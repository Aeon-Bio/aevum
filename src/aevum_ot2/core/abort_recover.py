"""Agent-facing abort/recover facade over the proven no-motion recovery state machine.

This module is a thin PROJECTION over :func:`recover_no_motion_session` (the only
fail-closed DELETE path, allowlisted in :mod:`aevum_ot2.core.recovery`). It MUST NOT
own motion authority: every projected report derives ``motion_allowed`` from the
recovered session and can NEVER report ``True`` out of this path. The facade performs
pure composition plus read-only lookups (``read_session`` / ``read_lock`` / the session
evidence index) and never calls ``post_json`` / ``delete_json`` directly.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from aevum_ot2.core.evidence import load_evidence_index
from aevum_ot2.core.lock import DEFAULT_STATE_DB, read_lock
from aevum_ot2.core.models import BridgeLock, BridgeSession
from aevum_ot2.core.recovery import (
    NoMotionRecoveryDisposition,
    NoMotionRecoveryReport,
    recover_no_motion_session,
)
from aevum_ot2.core.sessions import read_session

RECOVERY_CAMERA_EVENT_TYPE = "ot2_camera_picture"
UNKNOWN_RECOVERY_STATE = "unknown"


class RequiredRecoveryAction(StrEnum):
    """The single fail-closed next action an agent must take after a recovery attempt."""

    NONE = "none"
    CAPTURE_CAMERA_EVIDENCE = "capture_camera_evidence"
    SUPERVISED_RECOVERY = "supervised_recovery"
    MANUAL_HARDWARE_ABORT = "manual_hardware_abort"


# Fail-closed projection: a disposition the state machine could not resolve, or one with
# no local session to reconcile, MUST escalate to a supervised path -- never NONE. Adding a
# disposition without an explicit entry here falls through to SUPERVISED_RECOVERY below.
_DISPOSITION_REQUIRED_ACTION: dict[NoMotionRecoveryDisposition, RequiredRecoveryAction] = {
    NoMotionRecoveryDisposition.RECOVERED_CLOSED: RequiredRecoveryAction.NONE,
    NoMotionRecoveryDisposition.RECOVERED_ACTIVE: RequiredRecoveryAction.CAPTURE_CAMERA_EVIDENCE,
    NoMotionRecoveryDisposition.SUPERVISED_OVERRIDE_CLOSED: RequiredRecoveryAction.NONE,
    NoMotionRecoveryDisposition.UNRESOLVED_RECOVERY: RequiredRecoveryAction.SUPERVISED_RECOVERY,
    NoMotionRecoveryDisposition.NO_LOCAL_SESSION: RequiredRecoveryAction.SUPERVISED_RECOVERY,
    NoMotionRecoveryDisposition.NOT_STARTED: RequiredRecoveryAction.MANUAL_HARDWARE_ABORT,
}


class AbortOrRecoverReport(BaseModel):
    """Agent contract projected from a :class:`NoMotionRecoveryReport`.

    ``motion_allowed`` is ALWAYS derived from the recovered session and is NEVER set to
    ``True`` out of this path; the recovery state machine always leaves
    ``session.motion_allowed`` ``False``, so this facade only ever surfaces a fail-closed
    motion gate. The embedded :class:`NoMotionRecoveryReport` is carried verbatim for audit.
    """

    model_config = ConfigDict(extra="forbid")

    recovery_state: str
    owning_session_id: str
    last_command_key: str | None = None
    last_command_id: str | None = None
    required_action: RequiredRecoveryAction
    latest_recovery_image_handle: str | None = None
    motion_allowed: bool = False
    disposition: NoMotionRecoveryDisposition
    recovery_report: NoMotionRecoveryReport
    notes: list[str] = Field(default_factory=list)


def ot2_abort_or_recover(
    session_id: str,
    *,
    timeout_seconds: float = 10.0,
    state_db_path: str | Path = DEFAULT_STATE_DB,
) -> AbortOrRecoverReport:
    """Run the proven recovery state machine and PROJECT it into the agent contract.

    This is pure composition: it delegates the only mutating, fail-closed work to
    :func:`recover_no_motion_session`, then performs read-only lookups (``read_session`` /
    ``read_lock`` / session evidence index) to assemble the agent-facing report. It MUST
    NOT call ``post_json`` / ``delete_json`` -- the recovery module owns the allowlisted
    DELETE.
    """

    report = recover_no_motion_session(
        session_id,
        timeout_seconds=timeout_seconds,
        state_db_path=state_db_path,
    )
    return _project_recovery_report(report, state_db_path=state_db_path)


def _project_recovery_report(
    report: NoMotionRecoveryReport,
    *,
    state_db_path: str | Path,
) -> AbortOrRecoverReport:
    session = report.session_after or report.session_before
    # Read-only reconciliation reads -- never re-mutates state the state machine owns.
    persisted = read_session(report.session_id, state_db_path)
    lock = _read_owning_lock(session, state_db_path)

    return AbortOrRecoverReport(
        recovery_state=_recovery_state(session, persisted, lock),
        owning_session_id=report.session_id,
        last_command_key=_last_command_key(session, persisted, lock),
        last_command_id=_last_command_id(session, persisted, lock),
        required_action=_required_action(report.disposition),
        latest_recovery_image_handle=_latest_recovery_image_handle(session),
        motion_allowed=_derive_motion_allowed(session, persisted),
        disposition=report.disposition,
        recovery_report=report,
        notes=list(report.notes),
    )


def _required_action(disposition: NoMotionRecoveryDisposition) -> RequiredRecoveryAction:
    # Fail-closed default: any disposition without an explicit mapping escalates to a
    # supervised path rather than silently reporting NONE.
    return _DISPOSITION_REQUIRED_ACTION.get(
        disposition,
        RequiredRecoveryAction.SUPERVISED_RECOVERY,
    )


def _derive_motion_allowed(
    session: BridgeSession | None,
    persisted: BridgeSession | None,
) -> bool:
    # ALWAYS derived, NEVER True out of this path. The recovery state machine leaves
    # session.motion_allowed False on every disposition; if either the in-report or the
    # persisted session somehow disagrees, fail closed.
    if session is not None and session.motion_allowed:
        return False
    if persisted is not None and persisted.motion_allowed:
        return False
    return False


def _read_owning_lock(
    session: BridgeSession | None,
    state_db_path: str | Path,
) -> BridgeLock | None:
    if session is None:
        return None
    lock = read_lock(session.robot_url, state_db_path)
    if lock is None or lock.session_id != session.session_id:
        return None
    return lock


def _recovery_state(
    session: BridgeSession | None,
    persisted: BridgeSession | None,
    lock: BridgeLock | None,
) -> str:
    if persisted is not None:
        return str(persisted.state)
    if session is not None:
        return str(session.state)
    if lock is not None:
        return lock.state
    return UNKNOWN_RECOVERY_STATE


def _last_command_key(
    session: BridgeSession | None,
    persisted: BridgeSession | None,
    lock: BridgeLock | None,
) -> str | None:
    for candidate in (persisted, session):
        if candidate is not None and candidate.last_command_key:
            return candidate.last_command_key
    return None


def _last_command_id(
    session: BridgeSession | None,
    persisted: BridgeSession | None,
    lock: BridgeLock | None,
) -> str | None:
    for candidate in (persisted, session):
        if candidate is not None and candidate.last_command_id:
            return candidate.last_command_id
    if lock is not None and lock.last_command_id:
        return lock.last_command_id
    return None


def _latest_recovery_image_handle(session: BridgeSession | None) -> str | None:
    """Read-only lookup of the most recent camera image path from the session index."""

    if session is None:
        return None
    index_path = Path(session.evidence_index_path)
    if not index_path.exists():
        return None
    index = load_evidence_index(index_path)
    latest: str | None = None
    for event in index.events:
        if event.event_type != RECOVERY_CAMERA_EVENT_TYPE:
            continue
        if event.session_id is not None and event.session_id != session.session_id:
            continue
        image_path = event.payload.get("image_path")
        if isinstance(image_path, str) and image_path:
            latest = image_path
    return latest
