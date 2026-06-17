from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from aevum_ot2.core.command_journal import (
    CommandDispatchResult,
    CommandJournalEntry,
    CommandTransport,
    dispatch_journaled_command,
)
from aevum_ot2.core.dispatch_preparation import (
    MotionDispatchPreparation,
    build_motion_dispatch_preparation_for_reservation,
    motion_dispatch_preparation_blockers,
)
from aevum_ot2.core.dispatch_reservation import MotionDispatchReservation
from aevum_ot2.core.lock import (
    DEFAULT_STATE_DB,
    initialize_state_db,
    read_lock_in_transaction,
    write_lock_in_transaction,
)
from aevum_ot2.core.models import BridgeLock, BridgeSession, BridgeSessionState
from aevum_ot2.core.plans import PlanFragment, canonicalize_plan_fragment
from aevum_ot2.core.safety import FixtureSafetyProfile
from aevum_ot2.core.sessions import (
    initialize_session_db,
    read_session_in_transaction,
    write_session_in_transaction,
)


class MotionBackendDispatchResult(BaseModel):
    dispatched: bool = False
    motion_commands_sent: bool = False
    session_updated: bool = False
    preparation: MotionDispatchPreparation | None = None
    dispatch: CommandDispatchResult | None = None
    blockers: list[str] = Field(default_factory=list)


def dispatch_prepared_motion_command(
    *,
    transport: CommandTransport,
    reservation: MotionDispatchReservation,
    preparation: MotionDispatchPreparation,
    session: BridgeSession,
    plan: PlanFragment,
    safety_profile: FixtureSafetyProfile | None,
    state_db_path: str | Path = DEFAULT_STATE_DB,
) -> MotionBackendDispatchResult:
    plan = canonicalize_plan_fragment(plan)
    blockers = _pre_dispatch_blockers(
        reservation=reservation,
        preparation=preparation,
        session=session,
    )
    if blockers:
        session_updated, state_blockers = _persist_recovery_state(
            session=session,
            entry=preparation.command_journal_entry,
            reasons=blockers,
            state_db_path=state_db_path,
        )
        return MotionBackendDispatchResult(
            preparation=preparation,
            session_updated=session_updated,
            blockers=[*blockers, *state_blockers],
        )

    fresh_run = transport.get_json(f"/maintenance_runs/{preparation.run_id}")
    fresh_history = transport.get_json(preparation.history_path)
    fresh_result = build_motion_dispatch_preparation_for_reservation(
        reservation=reservation,
        session=session,
        plan=plan,
        safety_profile=safety_profile,
        run_result=fresh_run,
        command_history_result=fresh_history,
        now=preparation.prepared_at,
    )
    if not fresh_result.prepared or fresh_result.preparation is None:
        blockers = [
            f"fresh dispatch preparation: {blocker}"
            for blocker in fresh_result.blockers
        ]
        session_updated, state_blockers = _persist_recovery_state(
            session=session,
            entry=preparation.command_journal_entry,
            reasons=blockers,
            state_db_path=state_db_path,
        )
        return MotionBackendDispatchResult(
            preparation=preparation,
            session_updated=session_updated,
            blockers=[*blockers, *state_blockers],
        )
    fresh_blockers = _fresh_preparation_blockers(
        expected=preparation,
        fresh=fresh_result.preparation,
    )
    if fresh_blockers:
        session_updated, state_blockers = _persist_recovery_state(
            session=session,
            entry=preparation.command_journal_entry,
            reasons=fresh_blockers,
            state_db_path=state_db_path,
        )
        return MotionBackendDispatchResult(
            preparation=preparation,
            session_updated=session_updated,
            blockers=[*fresh_blockers, *state_blockers],
        )
    pre_post_blockers = _pre_post_scope_blockers(
        session=session,
        state_db_path=state_db_path,
    )
    if pre_post_blockers:
        session_updated, state_blockers = _persist_recovery_state(
            session=session,
            entry=preparation.command_journal_entry,
            reasons=pre_post_blockers,
            state_db_path=state_db_path,
        )
        return MotionBackendDispatchResult(
            preparation=preparation,
            session_updated=session_updated,
            blockers=[*pre_post_blockers, *state_blockers],
        )

    dispatch = dispatch_journaled_command(
        transport=transport,
        entry=preparation.command_journal_entry,
        command_path=preparation.command_path,
        command_body=preparation.command_body,
        journal_path=state_db_path,
        history_path=preparation.history_path,
    )
    state_update_blockers: list[str] = []
    session_updated = False
    if dispatch.posted:
        try:
            session_updated, state_update_blockers = _apply_post_dispatch_state(
                session=session,
                dispatch=dispatch,
                state_db_path=state_db_path,
            )
        except (OSError, sqlite3.Error) as exc:
            state_update_blockers = [
                f"motion backend state update failed after POST: {exc}"
            ]
    elif dispatch.blockers:
        session_updated, state_update_blockers = _persist_recovery_state(
            session=session,
            entry=preparation.command_journal_entry,
            reasons=dispatch.blockers,
            state_db_path=state_db_path,
        )
    return MotionBackendDispatchResult(
        dispatched=dispatch.posted and not state_update_blockers,
        motion_commands_sent=dispatch.posted,
        session_updated=session_updated,
        preparation=preparation,
        dispatch=dispatch,
        blockers=[*dispatch.blockers, *state_update_blockers],
    )


def _pre_dispatch_blockers(
    *,
    reservation: MotionDispatchReservation,
    preparation: MotionDispatchPreparation,
    session: BridgeSession,
) -> list[str]:
    blockers = motion_dispatch_preparation_blockers(
        preparation,
        reservation=reservation,
        session=session,
    )
    if reservation.command_journal_id != preparation.command_journal_entry.journal_id:
        blockers.append("dispatch reservation journal ID does not match preparation")
    if preparation.robot_command_posted:
        blockers.append("dispatch preparation already reports a robot command post")
    return _dedupe(blockers)


def _fresh_preparation_blockers(
    *,
    expected: MotionDispatchPreparation,
    fresh: MotionDispatchPreparation,
) -> list[str]:
    blockers: list[str] = []
    if fresh.command_path != expected.command_path:
        blockers.append("fresh dispatch command path changed")
    if fresh.history_path != expected.history_path:
        blockers.append("fresh dispatch history path changed")
    if fresh.command_body != expected.command_body:
        blockers.append("fresh dispatch command body changed")
    if fresh.command_body_sha256 != expected.command_body_sha256:
        blockers.append("fresh dispatch command body checksum changed")
    if _journal_identity(fresh.command_journal_entry) != _journal_identity(
        expected.command_journal_entry
    ):
        blockers.append("fresh dispatch journal identity changed")
    if fresh.readback != expected.readback:
        blockers.append("fresh dispatch readback changed")
    return blockers


def _apply_post_dispatch_state(
    *,
    session: BridgeSession,
    dispatch: CommandDispatchResult,
    state_db_path: str | Path,
) -> tuple[bool, list[str]]:
    recovery_reasons = _post_dispatch_recovery_reasons(dispatch)
    entry = dispatch.entry
    if recovery_reasons:
        return _persist_recovery_state(
            session=session,
            entry=entry,
            reasons=recovery_reasons,
            state_db_path=state_db_path,
        )
    if not _completed_entry(entry):
        return _persist_recovery_state(
            session=session,
            entry=entry,
            reasons=["motion backend dispatch completed without command authority"],
            state_db_path=state_db_path,
        )
    return _persist_completed_state(
        session=session,
        entry=entry,
        state_db_path=state_db_path,
    )


def _post_dispatch_recovery_reasons(dispatch: CommandDispatchResult) -> list[str]:
    reasons: list[str] = []
    if not dispatch.journal_persisted:
        reasons.append("command journal was not durably reconciled after dispatch")
    if dispatch.post_result is None:
        reasons.append("motion command POST result is missing")
    elif not dispatch.post_result.ok:
        reasons.append("motion command POST failed")
    if dispatch.reconciliation is None:
        reasons.append("motion command reconciliation is missing")
    elif dispatch.reconciliation.recovery_required:
        reasons.extend(dispatch.reconciliation.blockers)
    elif dispatch.reconciliation.state != "completed":
        reasons.append(
            f"motion command reconciliation ended in {dispatch.reconciliation.state}"
        )
    elif not dispatch.reconciliation.matched_command_is_latest:
        reasons.append("motion command is not latest in command history")
    return _dedupe(reasons)


def _completed_entry(entry: CommandJournalEntry) -> bool:
    return (
        entry.state == "completed"
        and entry.command_id is not None
        and entry.command_status in {"succeeded", "completed"}
    )


def _persist_completed_state(
    *,
    session: BridgeSession,
    entry: CommandJournalEntry,
    state_db_path: str | Path,
) -> tuple[bool, list[str]]:
    def update_session(latest: BridgeSession) -> BridgeSession:
        return latest.model_copy(
            update={
                "state": BridgeSessionState.READY_NO_MOTION,
                "motion_allowed": False,
                "last_command_id": entry.command_id,
                "last_command_key": entry.command_key,
                "last_command_type": entry.command_type,
                "last_command_status": entry.command_status,
                "updated_at": datetime.now(),
                "notes": [
                    *latest.notes,
                    f"Motion command completed and reconciled: {entry.journal_id}.",
                ],
            }
        )

    def update_lock(lock: BridgeLock) -> BridgeLock:
        return lock.model_copy(
            update={
                "last_command_id": entry.command_id,
                "state": "active_no_motion",
            }
        )

    return _persist_session_lock_state(
        session=session,
        update_session=update_session,
        update_lock=update_lock,
        state_db_path=state_db_path,
    )


def _persist_recovery_state(
    *,
    session: BridgeSession,
    entry: CommandJournalEntry,
    reasons: list[str],
    state_db_path: str | Path,
) -> tuple[bool, list[str]]:
    reason_text = "; ".join(_dedupe(reasons)) or "motion dispatch recovery required"

    def update_session(latest: BridgeSession) -> BridgeSession:
        command_was_observed = entry.command_id is not None
        return latest.model_copy(
            update={
                "state": BridgeSessionState.RECOVERY_REQUIRED,
                "motion_allowed": False,
                "last_command_id": entry.command_id or latest.last_command_id,
                "last_command_key": entry.command_key
                if command_was_observed
                else latest.last_command_key,
                "last_command_type": entry.command_type
                if command_was_observed
                else latest.last_command_type,
                "last_command_status": entry.command_status
                or latest.last_command_status,
                "updated_at": datetime.now(),
                "notes": [
                    *latest.notes,
                    f"Motion dispatch requires recovery: {reason_text}.",
                ],
            }
        )

    def update_lock(lock: BridgeLock) -> BridgeLock:
        return lock.model_copy(
            update={
                "last_command_id": entry.command_id or lock.last_command_id,
                "state": "recovery_required",
            }
        )

    updated, blockers = _persist_session_lock_state(
        session=session,
        update_session=update_session,
        update_lock=update_lock,
        state_db_path=state_db_path,
    )
    recovery_blockers = [
        f"motion dispatch recovery required: {reason}" for reason in reasons
    ]
    return updated, recovery_blockers + blockers


def _pre_post_scope_blockers(
    *,
    session: BridgeSession,
    state_db_path: str | Path,
) -> list[str]:
    db_path = initialize_session_db(state_db_path)
    initialize_state_db(db_path)
    now = datetime.now()
    with sqlite3.connect(db_path) as connection:
        latest = read_session_in_transaction(connection, session.session_id)
        lock = read_lock_in_transaction(connection, session.robot_url)
    blockers = _state_scope_blockers(expected=session, latest=latest, lock=lock)
    if latest is not None and latest.lease_expires_at <= now:
        blockers.append("session lease expired before motion command POST")
    if lock is not None and lock.lease_expires_at <= now:
        blockers.append("bridge lock lease expired before motion command POST")
    return _dedupe(blockers)


def _persist_session_lock_state(
    *,
    session: BridgeSession,
    update_session,
    update_lock,
    state_db_path: str | Path,
) -> tuple[bool, list[str]]:
    db_path = initialize_session_db(state_db_path)
    initialize_state_db(db_path)
    with sqlite3.connect(db_path, isolation_level=None) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            latest = read_session_in_transaction(connection, session.session_id)
            lock = read_lock_in_transaction(connection, session.robot_url)
            blockers = _state_scope_blockers(
                expected=session,
                latest=latest,
                lock=lock,
            )
            if blockers or latest is None or lock is None:
                connection.rollback()
                return False, blockers
            write_session_in_transaction(connection, update_session(latest))
            write_lock_in_transaction(connection, update_lock(lock))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return True, []


def _state_scope_blockers(
    *,
    expected: BridgeSession,
    latest: BridgeSession | None,
    lock: BridgeLock | None,
) -> list[str]:
    blockers: list[str] = []
    if latest is None:
        blockers.append("session disappeared before motion backend state update")
        return blockers
    if latest.session_id != expected.session_id:
        blockers.append("session ID changed before motion backend state update")
    if latest.owner_id != expected.owner_id:
        blockers.append("session owner changed before motion backend state update")
    if latest.robot_url != expected.robot_url:
        blockers.append("session robot URL changed before motion backend state update")
    if latest.maintenance_run_id != expected.maintenance_run_id:
        blockers.append("session run changed before motion backend state update")
    if latest.state != BridgeSessionState.READY_NO_MOTION:
        blockers.append("session state changed before motion backend state update")
    if latest.motion_allowed:
        blockers.append("session motion allowance changed before motion backend state update")
    if latest.last_command_id != expected.last_command_id:
        blockers.append("session last command ID changed before motion backend state update")
    if latest.last_command_key != expected.last_command_key:
        blockers.append("session last command key changed before motion backend state update")
    if latest.last_command_type != expected.last_command_type:
        blockers.append("session last command type changed before motion backend state update")
    if latest.last_command_status != expected.last_command_status:
        blockers.append("session last command status changed before motion backend state update")
    if lock is None:
        blockers.append("bridge lock disappeared before motion backend state update")
        return blockers
    if lock.session_id != expected.session_id:
        blockers.append("bridge lock session changed before motion backend state update")
    if lock.owner_id != expected.owner_id:
        blockers.append("bridge lock owner changed before motion backend state update")
    if lock.active_run_id != expected.maintenance_run_id:
        blockers.append("bridge lock run changed before motion backend state update")
    if lock.state != "active_no_motion":
        blockers.append("bridge lock state changed before motion backend state update")
    if lock.last_command_id != expected.last_command_id:
        blockers.append("bridge lock last command changed before motion backend state update")
    return blockers


def _journal_identity(entry: CommandJournalEntry) -> dict[str, object]:
    return entry.model_dump(
        mode="json",
        exclude={"prepared_at", "posted_at", "reconciled_at", "command_id", "command_index"},
    )


def _dedupe(items: list[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item and item not in deduped:
            deduped.append(item)
    return deduped
