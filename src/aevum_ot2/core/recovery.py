from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from aevum_ot2.core.client import Ot2Client
from aevum_ot2.core.command_journal import (
    CommandJournalEntry,
    list_command_journal_entries,
    reconcile_command_history,
    write_command_journal_entry,
)
from aevum_ot2.core.evidence import append_evidence_event
from aevum_ot2.core.lock import DEFAULT_STATE_DB, read_lock, write_lock
from aevum_ot2.core.models import (
    BridgeLock,
    BridgeSession,
    BridgeSessionState,
    EndpointResult,
    EvidenceEvent,
)
from aevum_ot2.core.sessions import read_session, write_session

RECOVERABLE_SETUP_COMMAND_TYPES = {"comment", "loadLabware", "loadPipette", "home"}
RECOVERABLE_JOURNALED_MOTION_COMMAND_TYPES = {"moveToWell"}
COMMAND_SUCCESS_STATUSES = {"succeeded", "completed"}


class NoMotionRecoveryDisposition(StrEnum):
    NOT_STARTED = "not_started"
    NO_LOCAL_SESSION = "no_local_session"
    RECOVERED_ACTIVE = "recovered_active"
    RECOVERED_CLOSED = "recovered_closed"
    UNRESOLVED_RECOVERY = "unresolved_recovery"
    SUPERVISED_OVERRIDE_CLOSED = "supervised_override_closed"


class NoMotionRecoveryReport(BaseModel):
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    disposition: NoMotionRecoveryDisposition = NoMotionRecoveryDisposition.NOT_STARTED
    session_before: BridgeSession | None = None
    run_get_result: EndpointResult | None = None
    commands_result: EndpointResult | None = None
    command_types: list[str] = Field(default_factory=list)
    unsafe_command_types: list[str] = Field(default_factory=list)
    delete_result: EndpointResult | None = None
    post_delete_get_result: EndpointResult | None = None
    session_after: BridgeSession | None = None
    lock: BridgeLock | None = None
    reconciled: bool = False
    motion_commands_detected: bool = False
    notes: list[str] = Field(default_factory=list)


def recover_no_motion_session(
    session_id: str,
    *,
    timeout_seconds: float = 10.0,
    state_db_path: str | Path = DEFAULT_STATE_DB,
) -> NoMotionRecoveryReport:
    """Reconcile a local no-motion session with its exact maintenance run ID."""

    session = read_session(session_id, state_db_path)
    report = NoMotionRecoveryReport(
        session_id=session_id,
        session_before=session.model_copy(deep=True) if session else None,
        notes=["Recovery reconciles only known no-motion maintenance runs."],
    )
    if session is None:
        report.disposition = NoMotionRecoveryDisposition.NO_LOCAL_SESSION
        report.notes.append("No local session record found.")
        return _record_recovery(report)

    lock = read_lock(session.robot_url, state_db_path)
    if lock is not None and lock.session_id == session.session_id:
        report.lock = lock.model_copy(deep=True)

    if session.maintenance_run_id is None:
        report.notes.append("No maintenance run ID recorded; marking local session closed.")
        return _mark_recovered_closed(report, session, lock, state_db_path)

    client = Ot2Client(session.robot_url, timeout_seconds=timeout_seconds)
    run_path = f"/maintenance_runs/{session.maintenance_run_id}"
    report.run_get_result = client.get_json(run_path)
    if report.run_get_result.status_code == 404:
        report.notes.append("Maintenance run is already absent on the robot.")
        return _mark_recovered_closed(report, session, lock, state_db_path)
    if not report.run_get_result.ok:
        report.notes.append("Could not read maintenance run; recovery remains required.")
        return _mark_recovery_required(report, session, lock, state_db_path)

    report.commands_result = client.get_json(f"{run_path}/commands?pageLength=1000")
    if not report.commands_result.ok:
        report.notes.append("Could not read maintenance run commands; recovery remains required.")
        return _mark_recovery_required(report, session, lock, state_db_path)
    if not _commands_result_complete(report.commands_result):
        report.notes.append("Command history is incomplete; recovery remains required.")
        return _mark_recovery_required(report, session, lock, state_db_path)

    report.command_types = _extract_command_types(report.commands_result)
    report.unsafe_command_types = sorted(
        command_type
        for command_type in set(report.command_types)
        if command_type not in RECOVERABLE_SETUP_COMMAND_TYPES
    )
    if report.unsafe_command_types:
        report.motion_commands_detected = True
        reconciled_motion = _reconcile_known_journaled_motion(
            report,
            session,
            state_db_path,
        )
        if reconciled_motion is not None:
            report.notes.append(
                "Known journaled motion command reconciled; maintenance run remains active."
            )
            return _mark_recovered_active(
                report,
                session,
                lock,
                reconciled_motion,
                state_db_path,
            )
        report.notes.append("Unexpected command types were present; manual recovery required.")
        return _mark_recovery_required(report, session, lock, state_db_path)

    report.delete_result = client.delete_json(run_path)
    if report.delete_result.status_code == 404:
        report.notes.append("Maintenance run disappeared before delete; marking recovered.")
        return _mark_recovered_closed(report, session, lock, state_db_path)
    if not report.delete_result.ok:
        report.notes.append("Maintenance run delete failed; recovery remains required.")
        return _mark_recovery_required(report, session, lock, state_db_path)

    report.post_delete_get_result = client.get_json(run_path)
    if report.post_delete_get_result.status_code != 404:
        report.notes.append(
            "Post-delete lookup did not confirm removal; recovery remains required."
        )
        return _mark_recovery_required(report, session, lock, state_db_path)

    report.notes.append("Maintenance run deletion confirmed with post-delete 404.")
    return _mark_recovered_closed(report, session, lock, state_db_path)


def _mark_recovered_closed(
    report: NoMotionRecoveryReport,
    session: BridgeSession,
    lock: BridgeLock | None,
    state_db_path: str | Path,
) -> NoMotionRecoveryReport:
    now = datetime.now()
    session.state = BridgeSessionState.CLOSED
    session.motion_allowed = False
    session.updated_at = now
    session.notes.append("Recovery reconciled the no-motion session as closed.")
    write_session(session, state_db_path)
    report.session_after = session
    report.disposition = NoMotionRecoveryDisposition.RECOVERED_CLOSED

    if lock is not None and lock.session_id == session.session_id:
        lock.state = "closed"
        lock.active_run_id = None
        lock.last_command_id = session.last_command_id
        write_lock(lock, state_db_path)
        report.lock = lock

    report.reconciled = True
    return _record_recovery(report)


def _mark_recovered_active(
    report: NoMotionRecoveryReport,
    session: BridgeSession,
    lock: BridgeLock | None,
    entry: CommandJournalEntry,
    state_db_path: str | Path,
) -> NoMotionRecoveryReport:
    now = datetime.now()
    session = session.model_copy(
        update={
            "state": BridgeSessionState.READY_NO_MOTION,
            "motion_allowed": False,
            "last_command_id": entry.command_id,
            "last_command_key": entry.command_key,
            "last_command_type": entry.command_type,
            "last_command_status": entry.command_status,
            "updated_at": now,
            "notes": [
                *session.notes,
                f"Recovery reconciled journaled motion command: {entry.journal_id}.",
            ],
        }
    )
    write_session(session, state_db_path)
    report.session_after = session
    report.disposition = NoMotionRecoveryDisposition.RECOVERED_ACTIVE

    if lock is not None and lock.session_id == session.session_id:
        lock = lock.model_copy(
            update={
                "state": "active_no_motion",
                "active_run_id": session.maintenance_run_id,
                "last_command_id": entry.command_id,
            }
        )
        write_lock(lock, state_db_path)
        report.lock = lock

    report.reconciled = True
    return _record_recovery(report)


def _mark_recovery_required(
    report: NoMotionRecoveryReport,
    session: BridgeSession,
    lock: BridgeLock | None,
    state_db_path: str | Path,
) -> NoMotionRecoveryReport:
    now = datetime.now()
    session.state = BridgeSessionState.RECOVERY_REQUIRED
    session.motion_allowed = False
    session.updated_at = now
    session.notes.append("No-motion recovery could not reconcile robot state.")
    write_session(session, state_db_path)
    report.session_after = session
    report.disposition = NoMotionRecoveryDisposition.UNRESOLVED_RECOVERY

    if lock is not None and lock.session_id == session.session_id:
        lock.state = "recovery_required"
        lock.active_run_id = session.maintenance_run_id
        lock.last_command_id = session.last_command_id
        write_lock(lock, state_db_path)
        report.lock = lock

    report.reconciled = False
    return _record_recovery(report)


def _reconcile_known_journaled_motion(
    report: NoMotionRecoveryReport,
    session: BridgeSession,
    state_db_path: str | Path,
) -> CommandJournalEntry | None:
    commands = _extract_commands(report.commands_result)
    unsafe_commands = [
        command
        for command in commands
        if _command_type(command) not in RECOVERABLE_SETUP_COMMAND_TYPES
    ]
    if len(unsafe_commands) != 1:
        report.notes.append(
            "Journaled motion recovery requires exactly one non-setup command."
        )
        return None
    command = unsafe_commands[0]
    command_type = _command_type(command)
    if command_type not in RECOVERABLE_JOURNALED_MOTION_COMMAND_TYPES:
        report.notes.append(f"Command type is not journal-recoverable: {command_type}.")
        return None
    if _command_status(command) not in COMMAND_SUCCESS_STATUSES:
        report.notes.append("Journaled motion command is not successful.")
        return None

    entries = [
        entry
        for entry in list_command_journal_entries(session.session_id, state_db_path)
        if entry.run_id == (session.maintenance_run_id or "")
        and entry.command_type == command_type
    ]
    matches: list[CommandJournalEntry] = []
    for entry in entries:
        reconciliation = reconcile_command_history(entry, report.commands_result)
        if (
            not reconciliation.recovery_required
            and reconciliation.entry is not None
            and reconciliation.state == "completed"
            and reconciliation.matched_command_is_latest
            and reconciliation.matched_command_id == _command_id(command)
        ):
            matches.append(reconciliation.entry)

    if len(matches) != 1:
        report.notes.append("Expected exactly one matching journaled motion command.")
        return None
    write_command_journal_entry(matches[0], state_db_path)
    return matches[0]


def _extract_commands(result: EndpointResult | None) -> list[dict[str, object]]:
    if result is None or not isinstance(result.data, dict):
        return []
    raw_commands = result.data.get("data")
    if not isinstance(raw_commands, list):
        return []
    return [command for command in raw_commands if isinstance(command, dict)]


def _extract_command_types(result: EndpointResult) -> list[str]:
    return [
        command_type
        for command in _extract_commands(result)
        if (command_type := _command_type(command))
    ]


def _command_id(command: dict[str, object]) -> str:
    command_id = command.get("id")
    return command_id if isinstance(command_id, str) else ""


def _command_type(command: dict[str, object]) -> str:
    command_type = command.get("commandType")
    return command_type if isinstance(command_type, str) else ""


def _command_status(command: dict[str, object]) -> str:
    status = command.get("status")
    return status if isinstance(status, str) else ""


def _commands_result_complete(result: EndpointResult) -> bool:
    data = result.data
    if not isinstance(data, dict):
        return False
    raw_commands = data.get("data")
    if not isinstance(raw_commands, list):
        return False
    meta = data.get("meta")
    if not isinstance(meta, dict):
        return False
    total_length = meta.get("totalLength")
    if isinstance(total_length, bool) or not isinstance(total_length, int):
        return False
    return total_length <= len(raw_commands)


def _record_recovery(report: NoMotionRecoveryReport) -> NoMotionRecoveryReport:
    session = report.session_after or report.session_before
    event = EvidenceEvent(
        event_type="ot2_no_motion_recovery",
        session_id=report.session_after.session_id if report.session_after else report.session_id,
        summary="No-motion bridge session recovery",
        payload=report.model_dump(mode="json"),
    )
    if session is not None:
        append_evidence_event(event, path=session.evidence_index_path)
    else:
        append_evidence_event(event)
    return report
