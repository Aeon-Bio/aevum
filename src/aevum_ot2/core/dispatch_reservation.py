from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aevum_ot2.core.lock import DEFAULT_STATE_DB
from aevum_ot2.core.models import BridgeSession
from aevum_ot2.core.motion_approval import MotionApproval, plan_fragment_digest
from aevum_ot2.core.plans import PlanFragment, PlanOperation, canonicalize_plan_fragment
from aevum_ot2.core.safety import FixtureSafetyProfile
from aevum_ot2.core.schema import loads_json_object, parse_versioned_json_model

MotionDispatchReservationState = Literal["reserved_pre_dispatch"]


class MotionDispatchReservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    reservation_id: str
    approval_id: str
    session_id: str
    owner_id: str
    robot_url: str
    run_id: str
    step_id: str
    operation: PlanOperation
    plan_digest_sha256: str
    safety_profile_sha256: str
    state: MotionDispatchReservationState = "reserved_pre_dispatch"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    command_journal_id: str = ""
    robot_command_posted: bool = False
    blockers: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_pre_dispatch_reservation(self) -> MotionDispatchReservation:
        if self.schema_version != 1:
            raise ValueError("unsupported motion dispatch reservation schema version")
        if self.state != "reserved_pre_dispatch":
            raise ValueError("motion dispatch reservation must remain reserved_pre_dispatch")
        if self.robot_command_posted:
            raise ValueError("pre-dispatch reservation cannot report a robot command post")
        return self


class MotionDispatchReservationResult(BaseModel):
    reserved: bool = False
    reservation: MotionDispatchReservation | None = None
    blockers: list[str] = Field(default_factory=list)


def initialize_dispatch_reservation_db(path: str | Path = DEFAULT_STATE_DB) -> Path:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as connection:
        ensure_dispatch_reservation_table(connection)
        connection.commit()
    return db_path


def ensure_dispatch_reservation_table(connection: sqlite3.Connection) -> None:
    _migrate_legacy_no_backend_reservation_table(connection)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS motion_dispatch_reservations (
            reservation_id TEXT PRIMARY KEY,
            approval_id TEXT NOT NULL UNIQUE,
            session_id TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state = 'reserved_pre_dispatch'),
            created_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_motion_dispatch_reservations_session
        ON motion_dispatch_reservations(session_id, created_at)
        """
    )


def _migrate_legacy_no_backend_reservation_table(
    connection: sqlite3.Connection,
) -> None:
    row = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'motion_dispatch_reservations'
        """
    ).fetchone()
    if row is None or "reserved_no_backend" not in str(row[0]):
        return
    connection.execute(
        "ALTER TABLE motion_dispatch_reservations RENAME TO motion_dispatch_reservations_legacy"
    )
    connection.execute(
        """
        CREATE TABLE motion_dispatch_reservations (
            reservation_id TEXT PRIMARY KEY,
            approval_id TEXT NOT NULL UNIQUE,
            session_id TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state = 'reserved_pre_dispatch'),
            created_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    rows = connection.execute(
        """
        SELECT reservation_id, approval_id, session_id, created_at, payload_json
        FROM motion_dispatch_reservations_legacy
        """
    ).fetchall()
    for row in rows:
        payload = json.loads(str(row[4]))
        if isinstance(payload, dict) and payload.get("state") == "reserved_no_backend":
            payload["state"] = "reserved_pre_dispatch"
        connection.execute(
            """
            INSERT INTO motion_dispatch_reservations (
                reservation_id, approval_id, session_id, state, created_at, payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row[0],
                row[1],
                row[2],
                "reserved_pre_dispatch",
                row[3],
                json.dumps(payload, sort_keys=True, separators=(",", ":")),
            ),
        )
    connection.execute("DROP TABLE motion_dispatch_reservations_legacy")


def reserve_motion_dispatch_for_consumed_approval(
    connection: sqlite3.Connection,
    *,
    approval: MotionApproval,
    approval_record_state: str,
    session: BridgeSession,
    plan: PlanFragment,
    safety_profile: FixtureSafetyProfile | None,
    command_journal_id: str = "",
    now: datetime | None = None,
) -> MotionDispatchReservationResult:
    checked_at = now or datetime.now()
    plan = canonicalize_plan_fragment(plan)
    blockers = _reservation_blockers(
        approval=approval,
        approval_record_state=approval_record_state,
        session=session,
        plan=plan,
        safety_profile=safety_profile,
    )
    if blockers:
        return MotionDispatchReservationResult(blockers=blockers)
    reservation = _build_reservation(
        approval=approval,
        session=session,
        command_journal_id=command_journal_id,
        created_at=checked_at,
    )
    ensure_dispatch_reservation_table(connection)
    try:
        _insert_reservation_row(connection, reservation)
    except sqlite3.IntegrityError:
        return MotionDispatchReservationResult(
            blockers=["motion dispatch reservation already exists for approval"]
        )
    return MotionDispatchReservationResult(reserved=True, reservation=reservation)


def read_motion_dispatch_reservation(
    reservation_id: str,
    path: str | Path = DEFAULT_STATE_DB,
) -> MotionDispatchReservation | None:
    db_path = initialize_dispatch_reservation_db(path)
    with closing(sqlite3.connect(db_path)) as connection:
        row = connection.execute(
            """
            SELECT reservation_id, approval_id, session_id, state, created_at, payload_json
            FROM motion_dispatch_reservations
            WHERE reservation_id = ?
            """,
            (reservation_id,),
        ).fetchone()
    if row is None:
        return None
    return _load_reservation_row(
        row,
        source=f"{db_path}:motion_dispatch_reservations.payload_json",
    )


def read_motion_dispatch_reservation_for_approval(
    approval_id: str,
    path: str | Path = DEFAULT_STATE_DB,
) -> MotionDispatchReservation | None:
    db_path = initialize_dispatch_reservation_db(path)
    with closing(sqlite3.connect(db_path)) as connection:
        row = connection.execute(
            """
            SELECT reservation_id, approval_id, session_id, state, created_at, payload_json
            FROM motion_dispatch_reservations
            WHERE approval_id = ?
            """,
            (approval_id,),
        ).fetchone()
    if row is None:
        return None
    return _load_reservation_row(
        row,
        source=f"{db_path}:motion_dispatch_reservations.payload_json",
    )


def list_motion_dispatch_reservations(
    session_id: str,
    path: str | Path = DEFAULT_STATE_DB,
) -> list[MotionDispatchReservation]:
    db_path = initialize_dispatch_reservation_db(path)
    with closing(sqlite3.connect(db_path)) as connection:
        rows = connection.execute(
            """
            SELECT reservation_id, approval_id, session_id, state, created_at, payload_json
            FROM motion_dispatch_reservations
            WHERE session_id = ?
            ORDER BY created_at
            """,
            (session_id,),
        ).fetchall()
    return [
        _load_reservation_row(
            row,
            source=f"{db_path}:motion_dispatch_reservations.payload_json",
        )
        for row in rows
    ]


def _build_reservation(
    *,
    approval: MotionApproval,
    session: BridgeSession,
    command_journal_id: str,
    created_at: datetime,
) -> MotionDispatchReservation:
    return MotionDispatchReservation(
        reservation_id=_reservation_id(approval.approval_id),
        approval_id=approval.approval_id,
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id=approval.step_id,
        operation=approval.operation,
        plan_digest_sha256=approval.plan_digest_sha256,
        safety_profile_sha256=approval.safety_profile_sha256,
        created_at=created_at,
        updated_at=created_at,
        command_journal_id=command_journal_id,
    )


def motion_dispatch_reservation_id(approval_id: str) -> str:
    return _reservation_id(approval_id)


def _reservation_blockers(
    *,
    approval: MotionApproval,
    approval_record_state: str,
    session: BridgeSession,
    plan: PlanFragment,
    safety_profile: FixtureSafetyProfile | None,
) -> list[str]:
    blockers: list[str] = []
    if approval_record_state != "consumed":
        blockers.append("motion dispatch reservation requires a consumed approval record")
    if approval.session_id != session.session_id:
        blockers.append("motion dispatch approval session does not match session")
    if not session.maintenance_run_id:
        blockers.append("motion dispatch reservation requires a maintenance run ID")
    step = next((item for item in plan.steps if item.step_id == approval.step_id), None)
    if step is None:
        blockers.append("motion dispatch approval step is not in plan")
    elif step.operation != approval.operation:
        blockers.append("motion dispatch approval operation does not match plan")
    if approval.plan_digest_sha256 != plan_fragment_digest(plan):
        blockers.append("motion dispatch approval plan digest does not match plan")
    if safety_profile is None:
        blockers.append("motion dispatch reservation requires a safety profile")
    elif safety_profile.safety_profile_sha256 != approval.safety_profile_sha256:
        blockers.append("motion dispatch safety profile does not match approval")
    return _dedupe(blockers)


def _insert_reservation_row(
    connection: sqlite3.Connection,
    reservation: MotionDispatchReservation,
) -> None:
    connection.execute(
        """
        INSERT INTO motion_dispatch_reservations (
            reservation_id, approval_id, session_id, state, created_at, payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            reservation.reservation_id,
            reservation.approval_id,
            reservation.session_id,
            reservation.state,
            reservation.created_at.isoformat(),
            reservation.model_dump_json(),
        ),
    )


def _load_reservation_row(
    row: tuple[object, ...],
    *,
    source: str,
) -> MotionDispatchReservation:
    data = loads_json_object(
        str(row[5]),
        schema_name="MotionDispatchReservation",
        path=source,
    )
    reservation = parse_versioned_json_model(
        data,
        MotionDispatchReservation,
        schema_name="MotionDispatchReservation",
        path=source,
    )
    row_values = {
        "reservation_id": str(row[0]),
        "approval_id": str(row[1]),
        "session_id": str(row[2]),
        "state": str(row[3]),
        "created_at": str(row[4]),
    }
    payload_values = {
        "reservation_id": reservation.reservation_id,
        "approval_id": reservation.approval_id,
        "session_id": reservation.session_id,
        "state": reservation.state,
        "created_at": reservation.created_at.isoformat(),
    }
    mismatches = [
        key
        for key, row_value in row_values.items()
        if payload_values[key] != row_value
    ]
    if mismatches:
        raise ValueError(
            "motion dispatch reservation row/payload mismatch: "
            + ", ".join(mismatches)
        )
    return reservation


def _reservation_id(approval_id: str) -> str:
    digest = hashlib.sha256(approval_id.encode("utf-8")).hexdigest()
    return f"motion_dispatch_reservation:{digest[:24]}"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
