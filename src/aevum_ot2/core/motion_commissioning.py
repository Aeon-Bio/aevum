from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from aevum_ot2.core.command_journal import (
    CommandJournalEntry,
    prepare_command_dispatch_in_transaction,
)
from aevum_ot2.core.dispatch_preparation import (
    MotionDispatchPreparation,
    motion_dispatch_preparation_blockers,
)
from aevum_ot2.core.dispatch_reservation import (
    MotionDispatchReservation,
    ensure_dispatch_reservation_table,
    reserve_motion_dispatch_for_consumed_approval,
)
from aevum_ot2.core.lock import DEFAULT_STATE_DB, initialize_state_db
from aevum_ot2.core.models import BridgeLock, BridgeSession, BridgeSessionState
from aevum_ot2.core.motion_approval import (
    MOTION_APPROVAL_LOCK_STATE,
    MOTION_APPROVAL_MAX_TTL,
    MotionApproval,
    build_motion_approval,
    motion_approval_blockers,
)
from aevum_ot2.core.plans import PlanFragment, canonicalize_plan_fragment, step_requires_motion
from aevum_ot2.core.safety import FixtureSafetyProfile
from aevum_ot2.core.schema import loads_json_object, parse_versioned_json_model
from aevum_ot2.core.sessions import initialize_session_db
from aevum_ot2.core.validation import PlanValidationResult

MotionApprovalRecordState = Literal["armed", "consumed", "revoked"]

MISSING_APPROVAL_REASON = "motion_approval: motion approval is required for motion execution"
ARMABLE_LOCK_STATE = "active_no_motion"
SQLITE_BUSY_TIMEOUT_MS = 5_000
MAX_SESSION_TRANSITION_NOTES = 50


class MotionApprovalRecord(BaseModel):
    schema_version: int = 1
    approval: MotionApproval
    robot_url: str
    state: MotionApprovalRecordState = "armed"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    consumed_at: datetime | None = None
    consumed_step_id: str = ""
    blockers: list[str] = Field(default_factory=list)


class MotionApprovalArmResult(BaseModel):
    session_id: str
    armed: bool = False
    approval: MotionApproval | None = None
    record: MotionApprovalRecord | None = None
    session: BridgeSession | None = None
    lock: BridgeLock | None = None
    validation: PlanValidationResult | None = None
    blockers: list[str] = Field(default_factory=list)


class MotionApprovalConsumeResult(BaseModel):
    approval_id: str
    consumed: bool = False
    record: MotionApprovalRecord | None = None
    session: BridgeSession | None = None
    lock: BridgeLock | None = None
    dispatch_reservation: MotionDispatchReservation | None = None
    dispatch_journal_entry: CommandJournalEntry | None = None
    blockers: list[str] = Field(default_factory=list)


def initialize_motion_approval_db(path: str | Path = DEFAULT_STATE_DB) -> Path:
    initialize_state_db(path)
    db_path = initialize_session_db(path)
    with closing(sqlite3.connect(db_path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS motion_approvals (
                approval_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                robot_url TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                consumed_at TEXT,
                payload_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_motion_approvals_session_state
            ON motion_approvals(session_id, state, created_at)
            """
        )
        _revoke_duplicate_armed_records_before_index(connection)
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_motion_approvals_one_armed_per_session
            ON motion_approvals(session_id)
            WHERE state = 'armed'
            """
        )
        ensure_dispatch_reservation_table(connection)
        connection.commit()
    return db_path


def read_motion_approval_record(
    approval_id: str,
    path: str | Path = DEFAULT_STATE_DB,
) -> MotionApprovalRecord | None:
    db_path = initialize_motion_approval_db(path)
    with closing(sqlite3.connect(db_path)) as connection:
        row = connection.execute(
            "SELECT payload_json FROM motion_approvals WHERE approval_id = ?",
            (approval_id,),
        ).fetchone()
    if row is None:
        return None
    return _load_motion_approval_record(
        row[0],
        source=f"{db_path}:motion_approvals.payload_json",
    )


def list_motion_approval_records(
    session_id: str,
    path: str | Path = DEFAULT_STATE_DB,
) -> list[MotionApprovalRecord]:
    db_path = initialize_motion_approval_db(path)
    with closing(sqlite3.connect(db_path)) as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM motion_approvals
            WHERE session_id = ?
            ORDER BY created_at
            """,
            (session_id,),
        ).fetchall()
    return [
        _load_motion_approval_record(
            row[0],
            source=f"{db_path}:motion_approvals.payload_json",
        )
        for row in rows
    ]


def arm_motion_commissioning(
    *,
    session_id: str,
    plan: PlanFragment,
    validation: PlanValidationResult,
    safety_profile: FixtureSafetyProfile | None,
    approved_by: str,
    path: str | Path = DEFAULT_STATE_DB,
    expires_in: timedelta = timedelta(minutes=5),
    now: datetime | None = None,
) -> MotionApprovalArmResult:
    plan = canonicalize_plan_fragment(plan)
    blockers = motion_approval_arm_preflight_blockers(
        plan=plan,
        validation=validation,
        safety_profile=safety_profile,
        approved_by=approved_by,
        expires_in=expires_in,
    )
    if blockers:
        return MotionApprovalArmResult(
            session_id=session_id,
            validation=validation,
            blockers=blockers,
        )
    profile = safety_profile
    if profile is None:
        raise AssertionError("motion approval preflight returned without a safety profile")

    db_path = initialize_motion_approval_db(path)
    with closing(_connect_transaction(db_path)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        checked_at = now or datetime.now()
        try:
            session = _read_session_row(connection, session_id)
            if session is None:
                connection.rollback()
                return MotionApprovalArmResult(
                    session_id=session_id,
                    validation=validation,
                    blockers=[f"session not found: {session_id}"],
                )
            lock = _read_lock_row(connection, session.robot_url)
            session, lock, cleanup_changed = _revoke_expired_armed_records(
                connection,
                session,
                lock,
                checked_at,
            )
            tx_blockers = _arm_transaction_blockers(
                session,
                lock,
                checked_at,
                expires_in,
            )
            if _active_approval_record(connection, session.session_id) is not None:
                tx_blockers.append("an armed motion approval already exists for session")

            armed_session = _armed_session(session, checked_at)
            armed_lock = _armed_lock(lock) if lock is not None else None
            approval = build_motion_approval(
                plan,
                session=armed_session,
                safety_profile=profile,
                step_id=plan.steps[0].step_id,
                approved_by=approved_by,
                created_at=checked_at,
                expires_in=expires_in,
            )
            tx_blockers.extend(
                motion_approval_blockers(
                    approval,
                    plan=plan,
                    session=armed_session,
                    safety_profile=profile,
                    step=plan.steps[0],
                    lock=armed_lock,
                    now=checked_at,
                )
            )
            if tx_blockers:
                if cleanup_changed:
                    connection.commit()
                else:
                    connection.rollback()
                return MotionApprovalArmResult(
                    session_id=session_id,
                    validation=validation,
                    session=session,
                    lock=lock,
                    blockers=_dedupe(tx_blockers),
                )

            record = MotionApprovalRecord(
                approval=approval,
                robot_url=armed_session.robot_url,
                state="armed",
                created_at=checked_at,
                updated_at=checked_at,
            )
            _write_session_row(connection, armed_session)
            _write_lock_row(connection, armed_lock)  # type: ignore[arg-type]
            try:
                _insert_motion_approval_record_row(connection, record)
            except sqlite3.IntegrityError:
                connection.rollback()
                return MotionApprovalArmResult(
                    session_id=session_id,
                    validation=validation,
                    session=session,
                    lock=lock,
                    blockers=[
                        "motion approval record could not be inserted without "
                        "violating approval uniqueness"
                    ],
                )
            connection.commit()
            return MotionApprovalArmResult(
                session_id=session_id,
                armed=True,
                approval=approval,
                record=record,
                session=armed_session,
                lock=armed_lock,
                validation=validation,
            )
        except Exception:
            connection.rollback()
            raise


def consume_motion_approval(
    *,
    approval: MotionApproval,
    plan: PlanFragment,
    safety_profile: FixtureSafetyProfile | None,
    dispatch_preparation: MotionDispatchPreparation | None = None,
    path: str | Path = DEFAULT_STATE_DB,
    now: datetime | None = None,
) -> MotionApprovalConsumeResult:
    plan = canonicalize_plan_fragment(plan)
    db_path = initialize_motion_approval_db(path)
    with closing(_connect_transaction(db_path)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        checked_at = now or datetime.now()
        try:
            record = _read_motion_approval_record_row(connection, approval.approval_id)
            if record is None:
                connection.rollback()
                return MotionApprovalConsumeResult(
                    approval_id=approval.approval_id,
                    blockers=["motion approval record not found"],
                )
            if record.approval != approval:
                connection.rollback()
                return MotionApprovalConsumeResult(
                    approval_id=approval.approval_id,
                    record=record,
                    blockers=["motion approval does not match persisted record"],
                )
            session = _read_session_row(connection, approval.session_id)
            lock = _read_lock_row(connection, session.robot_url) if session is not None else None
            if record.state == "armed" and record.approval.expires_at <= checked_at:
                revoked_record, disarmed_session, disarmed_lock = (
                    _revoke_record_and_disarm_if_scoped(
                        connection,
                        record,
                        session,
                        lock,
                        checked_at,
                        reason="motion approval expired before consumption",
                    )
                )
                connection.commit()
                return MotionApprovalConsumeResult(
                    approval_id=approval.approval_id,
                    record=revoked_record,
                    session=disarmed_session,
                    lock=disarmed_lock,
                    blockers=["motion approval is expired"],
                )
            blockers: list[str] = []
            if record.state != "armed":
                blockers.append(f"motion approval is not armed: {record.state}")
            if session is None:
                blockers.append("motion approval session not found")
            elif lock is None:
                blockers.append("bridge lock is missing")
            else:
                step = _plan_step(plan, approval.step_id)
                blockers.extend(
                    motion_approval_blockers(
                        approval,
                        plan=plan,
                        session=session,
                        safety_profile=safety_profile,
                        step=step,
                        lock=lock,
                        now=checked_at,
                    )
                )
            if blockers:
                connection.rollback()
                return MotionApprovalConsumeResult(
                    approval_id=approval.approval_id,
                    record=record,
                    session=session,
                    lock=lock,
                    blockers=_dedupe(blockers),
                )
            if dispatch_preparation is None:
                connection.rollback()
                return MotionApprovalConsumeResult(
                    approval_id=approval.approval_id,
                    record=record,
                    session=session,
                    lock=lock,
                    blockers=["motion dispatch preparation is required"],
                )

            consumed_record = record.model_copy(
                update={
                    "state": "consumed",
                    "updated_at": checked_at,
                    "consumed_at": checked_at,
                    "consumed_step_id": approval.step_id,
                }
            )
            disarmed_session = _disarmed_session(session, approval.approval_id, checked_at)  # type: ignore[arg-type]
            disarmed_lock = _disarmed_lock(lock)  # type: ignore[arg-type]
            reservation = reserve_motion_dispatch_for_consumed_approval(
                connection,
                approval=approval,
                approval_record_state=consumed_record.state,
                session=disarmed_session,
                plan=plan,
                safety_profile=safety_profile,
                command_journal_id=dispatch_preparation.command_journal_entry.journal_id,
                now=checked_at,
            )
            if not reservation.reserved or reservation.reservation is None:
                connection.rollback()
                return MotionApprovalConsumeResult(
                    approval_id=approval.approval_id,
                    record=record,
                    session=session,
                    lock=lock,
                    blockers=[
                        f"motion dispatch reservation: {blocker}"
                        for blocker in reservation.blockers
                    ],
                )
            preparation_blockers = motion_dispatch_preparation_blockers(
                dispatch_preparation,
                reservation=reservation.reservation,
                session=disarmed_session,
            )
            if preparation_blockers:
                connection.rollback()
                return MotionApprovalConsumeResult(
                    approval_id=approval.approval_id,
                    record=record,
                    session=session,
                    lock=lock,
                    blockers=[
                        f"motion dispatch preparation: {blocker}"
                        for blocker in preparation_blockers
                    ],
                )
            prepared = prepare_command_dispatch_in_transaction(
                dispatch_preparation.command_journal_entry,
                connection,
            )
            if not prepared.persisted or prepared.entry is None:
                connection.rollback()
                return MotionApprovalConsumeResult(
                    approval_id=approval.approval_id,
                    record=record,
                    session=session,
                    lock=lock,
                    blockers=[
                        "motion dispatch preparation: "
                        + (prepared.blocker or "command journal unavailable")
                    ],
                )
            dispatch_journal_entry = prepared.entry
            _update_motion_approval_record_row(
                connection,
                consumed_record,
                expected_state="armed",
            )
            _write_session_row(connection, disarmed_session)
            _write_lock_row(connection, disarmed_lock)
            connection.commit()
            return MotionApprovalConsumeResult(
                approval_id=approval.approval_id,
                consumed=True,
                record=consumed_record,
                session=disarmed_session,
                lock=disarmed_lock,
                dispatch_reservation=reservation.reservation,
                dispatch_journal_entry=dispatch_journal_entry,
            )
        except Exception:
            connection.rollback()
            raise


def motion_approval_arm_preflight_blockers(
    *,
    plan: PlanFragment,
    validation: PlanValidationResult,
    safety_profile: FixtureSafetyProfile | None,
    approved_by: str,
    expires_in: timedelta,
) -> list[str]:
    blockers: list[str] = []
    if not approved_by.strip():
        blockers.append("approved_by is required")
    if safety_profile is None:
        blockers.append("fixture safety profile is required")
    if expires_in <= timedelta(0):
        blockers.append("motion approval TTL must be positive")
    if expires_in > MOTION_APPROVAL_MAX_TTL:
        blockers.append(
            "motion approval TTL exceeds "
            f"{int(MOTION_APPROVAL_MAX_TTL.total_seconds())} seconds"
        )
    if len(plan.steps) != 1:
        blockers.append("motion approval arm requires exactly one plan step")
    elif not step_requires_motion(plan.steps[0]):
        blockers.append("motion approval arm requires a motion step")
    if validation.session_id != plan.session_id:
        blockers.append("plan validation session does not match plan")
    if validation.motion_allowed:
        blockers.append("plan validation unexpectedly allows motion before arming")
    if MISSING_APPROVAL_REASON not in validation.reasons:
        blockers.append("motion approval arm requires validation blocked by missing approval")
    unexpected_reasons = [
        reason for reason in validation.reasons if reason != MISSING_APPROVAL_REASON
    ]
    blockers.extend(
        f"plan validation blocker before arming: {reason}"
        for reason in unexpected_reasons
    )
    for step in validation.steps:
        if step.requires_motion and not step.allowed:
            blockers.extend(
                f"step validation blocker before arming: {reason}"
                for reason in step.reasons
            )
    return _dedupe(blockers)


def _arm_transaction_blockers(
    session: BridgeSession,
    lock: BridgeLock | None,
    now: datetime,
    expires_in: timedelta,
) -> list[str]:
    blockers: list[str] = []
    if session.state != BridgeSessionState.READY_NO_MOTION:
        blockers.append(f"session state is {session.state}, not ready_no_motion")
    if session.motion_allowed:
        blockers.append("ready_no_motion session unexpectedly allows motion")
    if session.lease_expires_at <= now:
        blockers.append("session lease is expired")
    elif now + expires_in > session.lease_expires_at:
        blockers.append("motion approval TTL exceeds remaining session lease")
    if not session.maintenance_run_id:
        blockers.append("session maintenance run ID is missing")
    if not session.definition_uri:
        blockers.append("session has no uploaded labware definition URI")
    if not session.loaded_labware_id:
        blockers.append("session has no loaded fixture labware ID")
    if not session.last_command_id:
        blockers.append("session last command ID is missing")
    if session.last_command_status != "succeeded":
        blockers.append("session last command status is not succeeded")
    if lock is None:
        blockers.append("bridge lock is missing")
        return blockers
    if lock.state != ARMABLE_LOCK_STATE:
        blockers.append(f"bridge lock state {lock.state} cannot arm motion")
    if lock.session_id != session.session_id:
        blockers.append("bridge lock session does not match session")
    if lock.owner_id != session.owner_id:
        blockers.append("bridge lock owner does not match session")
    if lock.lease_expires_at <= now:
        blockers.append("bridge lock lease is expired")
    elif now + expires_in > lock.lease_expires_at:
        blockers.append("motion approval TTL exceeds remaining bridge lock lease")
    if lock.active_run_id != session.maintenance_run_id:
        blockers.append("bridge lock active run does not match session maintenance run")
    if lock.last_command_id != session.last_command_id:
        blockers.append("bridge lock last command does not match session")
    return blockers


def _armed_session(session: BridgeSession, now: datetime) -> BridgeSession:
    return session.model_copy(
        update={
            "state": BridgeSessionState.MOTION_COMMISSIONING_ARMED,
            "motion_allowed": True,
            "notes": _append_session_note(
                session.notes,
                "Motion commissioning armed by local approval transaction.",
            ),
        }
    )


def _armed_lock(lock: BridgeLock | None) -> BridgeLock | None:
    if lock is None:
        return None
    return lock.model_copy(
        update={
            "state": MOTION_APPROVAL_LOCK_STATE,
        }
    )


def _disarmed_session(
    session: BridgeSession,
    approval_id: str,
    now: datetime,
) -> BridgeSession:
    return session.model_copy(
        update={
            "state": BridgeSessionState.READY_NO_MOTION,
            "motion_allowed": False,
            "notes": _append_session_note(
                session.notes,
                f"Motion approval consumed at no-motion backend boundary: {approval_id}.",
            ),
        }
    )


def _disarmed_lock(lock: BridgeLock) -> BridgeLock:
    return lock.model_copy(
        update={
            "state": ARMABLE_LOCK_STATE,
        }
    )


def _append_session_note(notes: list[str], note: str) -> list[str]:
    return [*notes, note][-MAX_SESSION_TRANSITION_NOTES:]


def _connect_transaction(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, isolation_level=None)
    connection.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    return connection


def _revoke_duplicate_armed_records_before_index(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        """
        SELECT session_id, payload_json
        FROM motion_approvals
        WHERE state = 'armed'
        ORDER BY session_id, created_at DESC
        """
    ).fetchall()
    records_by_session: dict[str, list[MotionApprovalRecord]] = {}
    for row in rows:
        session_id = str(row[0])
        records_by_session.setdefault(session_id, []).append(
            _load_motion_approval_record(
                row[1],
                source="motion_approvals.payload_json",
            )
        )
    now = datetime.now()
    for records in records_by_session.values():
        for record in records[1:]:
            revoked_record = record.model_copy(
                update={
                    "state": "revoked",
                    "updated_at": now,
                    "blockers": _dedupe(
                        [
                            *record.blockers,
                            "duplicate armed approval revoked before unique index",
                        ]
                    ),
                }
            )
            _update_motion_approval_record_row(
                connection,
                revoked_record,
                expected_state="armed",
            )


def _revoke_expired_armed_records(
    connection: sqlite3.Connection,
    session: BridgeSession,
    lock: BridgeLock | None,
    now: datetime,
) -> tuple[BridgeSession, BridgeLock | None, bool]:
    rows = connection.execute(
        """
        SELECT payload_json
        FROM motion_approvals
        WHERE session_id = ? AND state = 'armed'
        ORDER BY created_at
        """,
        (session.session_id,),
    ).fetchall()
    records = [
        _load_motion_approval_record(row[0], source="motion_approvals.payload_json")
        for row in rows
    ]
    expired_records = [
        record
        for record in records
        if _armed_record_should_revoke(record, session, lock, now)
    ]
    active_records = [record for record in records if record not in expired_records]
    updated_session = session
    updated_lock = lock
    cleanup_changed = False
    for record in expired_records:
        _, updated_session, updated_lock = _revoke_record_and_disarm_if_scoped(
            connection,
            record,
            updated_session,
            updated_lock,
            now,
            reason=_armed_record_revoke_reason(record, session, lock, now),
            allow_disarm=not active_records,
        )
        cleanup_changed = True
    return updated_session, updated_lock, cleanup_changed


def _armed_record_should_revoke(
    record: MotionApprovalRecord,
    session: BridgeSession,
    lock: BridgeLock | None,
    now: datetime,
) -> bool:
    return (
        record.approval.expires_at <= now
        or session.lease_expires_at <= now
        or (lock is not None and lock.lease_expires_at <= now)
    )


def _armed_record_revoke_reason(
    record: MotionApprovalRecord,
    session: BridgeSession,
    lock: BridgeLock | None,
    now: datetime,
) -> str:
    if record.approval.expires_at <= now:
        return "motion approval expired before re-arm"
    if session.lease_expires_at <= now:
        return "session lease expired before re-arm"
    if lock is not None and lock.lease_expires_at <= now:
        return "bridge lock lease expired before re-arm"
    return "armed approval revoked before re-arm"


def _revoke_record_and_disarm_if_scoped(
    connection: sqlite3.Connection,
    record: MotionApprovalRecord,
    session: BridgeSession | None,
    lock: BridgeLock | None,
    now: datetime,
    *,
    reason: str,
    allow_disarm: bool = True,
) -> tuple[MotionApprovalRecord, BridgeSession | None, BridgeLock | None]:
    revoked_record = record.model_copy(
        update={
            "state": "revoked",
            "updated_at": now,
            "blockers": _dedupe([*record.blockers, reason]),
        }
    )
    _update_motion_approval_record_row(
        connection,
        revoked_record,
        expected_state="armed",
    )
    if session is None:
        return revoked_record, session, lock
    if not allow_disarm or not _can_disarm_session_for_revoked_approval(record, session):
        return revoked_record, session, lock

    disarmed_session = _disarmed_session(
        session,
        record.approval.approval_id,
        now,
    )
    _write_session_row(connection, disarmed_session)
    disarmed_lock = lock
    if lock is not None and _can_disarm_lock_for_revoked_approval(
        record,
        disarmed_session,
        lock,
    ):
        disarmed_lock = _disarmed_lock(lock)
        _write_lock_row(connection, disarmed_lock)
    return revoked_record, disarmed_session, disarmed_lock


def _can_disarm_session_for_revoked_approval(
    record: MotionApprovalRecord,
    session: BridgeSession,
) -> bool:
    approval = record.approval
    return (
        session.session_id == approval.session_id
        and session.state == approval.required_session_state
    )


def _can_disarm_lock_for_revoked_approval(
    record: MotionApprovalRecord,
    session: BridgeSession,
    lock: BridgeLock | None,
) -> bool:
    if lock is None:
        return False
    approval = record.approval
    return (
        lock.state == approval.required_lock_state
        and lock.session_id == session.session_id
        and lock.owner_id == session.owner_id
        and lock.active_run_id == session.maintenance_run_id
    )


def _active_approval_record(
    connection: sqlite3.Connection,
    session_id: str,
) -> MotionApprovalRecord | None:
    row = connection.execute(
        """
        SELECT payload_json
        FROM motion_approvals
        WHERE session_id = ? AND state = 'armed'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()
    if row is None:
        return None
    return _load_motion_approval_record(
        row[0],
        source="motion_approvals.payload_json",
    )


def _read_session_row(
    connection: sqlite3.Connection,
    session_id: str,
) -> BridgeSession | None:
    row = connection.execute(
        "SELECT payload_json FROM bridge_sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        return None
    data = loads_json_object(row[0], schema_name="BridgeSession")
    return parse_versioned_json_model(data, BridgeSession, schema_name="BridgeSession")


def _write_session_row(connection: sqlite3.Connection, session: BridgeSession) -> None:
    connection.execute(
        """
        INSERT INTO bridge_sessions (
            session_id, robot_url, owner_id, state, maintenance_run_id,
            created_at, updated_at, payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            robot_url = excluded.robot_url,
            owner_id = excluded.owner_id,
            state = excluded.state,
            maintenance_run_id = excluded.maintenance_run_id,
            updated_at = excluded.updated_at,
            payload_json = excluded.payload_json
        """,
        (
            session.session_id,
            session.robot_url,
            session.owner_id,
            session.state,
            session.maintenance_run_id,
            session.created_at.isoformat(),
            session.updated_at.isoformat(),
            session.model_dump_json(),
        ),
    )


def _read_lock_row(
    connection: sqlite3.Connection,
    robot_url: str,
) -> BridgeLock | None:
    row = connection.execute(
        """
        SELECT robot_url, session_id, owner_id, lease_started_at, lease_expires_at,
               active_run_id, last_command_id, state
        FROM bridge_locks
        WHERE robot_url = ?
        """,
        (robot_url,),
    ).fetchone()
    if row is None:
        return None
    return BridgeLock(
        robot_url=str(row[0]),
        session_id=str(row[1]),
        owner_id=str(row[2]),
        lease_started_at=datetime.fromisoformat(str(row[3])),
        lease_expires_at=datetime.fromisoformat(str(row[4])),
        active_run_id=row[5] if isinstance(row[5], str) else None,
        last_command_id=row[6] if isinstance(row[6], str) else None,
        state=str(row[7]),
    )


def _write_lock_row(connection: sqlite3.Connection, lock: BridgeLock) -> None:
    connection.execute(
        """
        INSERT INTO bridge_locks (
            robot_url, session_id, owner_id, lease_started_at, lease_expires_at,
            active_run_id, last_command_id, state
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(robot_url) DO UPDATE SET
            session_id = excluded.session_id,
            owner_id = excluded.owner_id,
            lease_started_at = excluded.lease_started_at,
            lease_expires_at = excluded.lease_expires_at,
            active_run_id = excluded.active_run_id,
            last_command_id = excluded.last_command_id,
            state = excluded.state
        """,
        (
            lock.robot_url,
            lock.session_id,
            lock.owner_id,
            lock.lease_started_at.isoformat(),
            lock.lease_expires_at.isoformat(),
            lock.active_run_id,
            lock.last_command_id,
            lock.state,
        ),
    )


def _read_motion_approval_record_row(
    connection: sqlite3.Connection,
    approval_id: str,
) -> MotionApprovalRecord | None:
    row = connection.execute(
        "SELECT payload_json FROM motion_approvals WHERE approval_id = ?",
        (approval_id,),
    ).fetchone()
    if row is None:
        return None
    return _load_motion_approval_record(
        row[0],
        source="motion_approvals.payload_json",
    )


def _insert_motion_approval_record_row(
    connection: sqlite3.Connection,
    record: MotionApprovalRecord,
) -> None:
    approval = record.approval
    connection.execute(
        """
        INSERT INTO motion_approvals (
            approval_id, session_id, robot_url, state, created_at,
            updated_at, consumed_at, payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            approval.approval_id,
            approval.session_id,
            record.robot_url,
            record.state,
            record.created_at.isoformat(),
            record.updated_at.isoformat(),
            record.consumed_at.isoformat() if record.consumed_at is not None else None,
            record.model_dump_json(),
        ),
    )


def _update_motion_approval_record_row(
    connection: sqlite3.Connection,
    record: MotionApprovalRecord,
    *,
    expected_state: MotionApprovalRecordState,
) -> None:
    cursor = connection.execute(
        """
        UPDATE motion_approvals
        SET
            session_id = ?,
            robot_url = ?,
            state = ?,
            updated_at = ?,
            consumed_at = ?,
            payload_json = ?
        WHERE approval_id = ? AND state = ?
        """,
        (
            record.approval.session_id,
            record.robot_url,
            record.state,
            record.updated_at.isoformat(),
            record.consumed_at.isoformat() if record.consumed_at is not None else None,
            record.model_dump_json(),
            record.approval.approval_id,
            expected_state,
        ),
    )
    if cursor.rowcount != 1:
        raise sqlite3.IntegrityError(
            "motion approval record state changed before transition"
        )


def _load_motion_approval_record(payload_json: str, *, source: str) -> MotionApprovalRecord:
    data = loads_json_object(payload_json, schema_name="MotionApprovalRecord", path=source)
    return parse_versioned_json_model(
        data,
        MotionApprovalRecord,
        schema_name="MotionApprovalRecord",
        path=source,
    )


def _plan_step(plan: PlanFragment, step_id: str):
    for step in plan.steps:
        if step.step_id == step_id:
            return step
    return None


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
