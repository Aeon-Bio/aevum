from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from aevum_ot2.core.models import (
    BridgeLock,
    BridgeSession,
    BridgeSessionState,
    GateName,
    RobotStatus,
)
from aevum_ot2.core.motion_approval import (
    MOTION_APPROVAL_LOCK_STATE,
    MotionApproval,
    motion_approval_blockers,
)
from aevum_ot2.core.plans import PlanFragment, PlanStep, step_requires_motion
from aevum_ot2.core.safety import FixtureSafetyProfile
from aevum_ot2.core.validation import PlanValidationResult, StepValidationResult

EXECUTION_LOCK_STATES = {MOTION_APPROVAL_LOCK_STATE}


class ExecuteRevalidationResult(BaseModel):
    passed: bool
    blockers: list[str] = Field(default_factory=list)
    missing_claims: list[str] = Field(default_factory=list)


def revalidate_motion_execution(
    *,
    session: BridgeSession,
    plan: PlanFragment,
    validation: PlanValidationResult,
    step: PlanStep,
    lock: BridgeLock | None,
    robot_status: RobotStatus | None,
    motion_approval: MotionApproval | None = None,
    safety_profile: FixtureSafetyProfile | None = None,
    now: datetime | None = None,
) -> ExecuteRevalidationResult:
    """Fail-closed execution-time checks that run after plan validation."""

    if not step_requires_motion(step):
        return ExecuteRevalidationResult(passed=True)

    blockers: list[str] = []
    missing_claims: list[str] = []
    checked_at = now or datetime.now()

    step_validation = _step_validation(validation, step)
    if not validation.allowed or not validation.motion_allowed:
        blockers.append("plan validation does not allow motion execution")
    if step_validation is None:
        missing_claims.append("step_validation")
    else:
        blockers.extend(_step_gate_blockers(step, step_validation))
    if motion_approval is None:
        missing_claims.append("motion_approval")
    else:
        blockers.extend(
            motion_approval_blockers(
                motion_approval,
                plan=plan,
                session=session,
                safety_profile=safety_profile,
                step=step,
                lock=lock,
                now=checked_at,
            )
        )

    if lock is None:
        missing_claims.append("bridge_lock")
    else:
        blockers.extend(_session_state_blockers(session, now=checked_at))
        blockers.extend(_lock_blockers(session, lock, now=checked_at))

    if robot_status is None:
        missing_claims.append("live_robot_status")
    else:
        blockers.extend(_robot_status_blockers(session, robot_status))
        blockers.extend(_live_pipette_blockers(session, robot_status))

    return ExecuteRevalidationResult(
        passed=not blockers and not missing_claims,
        blockers=_dedupe(blockers),
        missing_claims=_dedupe(missing_claims),
    )


def _step_validation(
    validation: PlanValidationResult,
    step: PlanStep,
) -> StepValidationResult | None:
    for step_validation in validation.steps:
        if step_validation.step_id == step.step_id:
            return step_validation
    return None


def _step_gate_blockers(
    step: PlanStep,
    step_validation: StepValidationResult,
) -> list[str]:
    blockers: list[str] = []
    if not step_validation.allowed:
        blockers.append("step validation does not allow motion execution")
    if not step_validation.gate_results:
        blockers.append("motion step has no gate result")
    gate_names = {gate.gate_name for gate in step_validation.gate_results}
    missing_gate_names = sorted(_required_motion_gate_names(step) - gate_names)
    for gate_name in missing_gate_names:
        blockers.append(f"motion step missing required gate result: {gate_name}")
    for gate in step_validation.gate_results:
        if not gate.passed:
            blockers.append(f"gate {gate.gate_name} did not pass")
        blockers.extend(gate.blockers)
    return blockers


def _required_motion_gate_names(step: PlanStep) -> set[GateName]:
    if step.operation == "home":
        return {GateName.HOME_CLEARANCE}
    if step.operation == "move_high_z":
        return {GateName.TARGET_CLASS_AUTHORITY, GateName.FIRST_HIGH_Z}
    if step.operation == "move_low_z":
        return {GateName.OFFSET_AUTHORITY, GateName.LOW_Z_DRY}
    if step.operation == "liquid_handling":
        return {GateName.OFFSET_AUTHORITY, GateName.WET}
    return set()


def _lock_blockers(
    session: BridgeSession,
    lock: BridgeLock,
    *,
    now: datetime,
) -> list[str]:
    blockers: list[str] = []
    if lock.session_id != session.session_id:
        blockers.append("bridge lock session does not match session")
    if lock.owner_id != session.owner_id:
        blockers.append("bridge lock owner does not match session")
    if lock.state not in EXECUTION_LOCK_STATES:
        blockers.append(f"bridge lock state {lock.state} cannot execute motion")
    if session.lease_expires_at <= now:
        blockers.append("session lease is expired")
    if lock.lease_expires_at <= now:
        blockers.append("bridge lock lease is expired")
    if not session.maintenance_run_id:
        blockers.append("session maintenance run ID is missing")
    elif lock.active_run_id != session.maintenance_run_id:
        blockers.append("bridge lock active run does not match session maintenance run")
    if not session.last_command_id:
        blockers.append("session last command ID is missing")
    elif lock.last_command_id != session.last_command_id:
        blockers.append("bridge lock last command does not match session")
    if session.last_command_status != "succeeded":
        blockers.append("session last command status is not succeeded")
    return blockers


def _session_state_blockers(
    session: BridgeSession,
    *,
    now: datetime,
) -> list[str]:
    blockers: list[str] = []
    if session.state != BridgeSessionState.MOTION_COMMISSIONING_ARMED:
        blockers.append(
            f"session state is {session.state}, not motion_commissioning_armed"
        )
    if not session.motion_allowed:
        blockers.append("session is not motion-armed")
    if session.lease_expires_at <= now:
        blockers.append("session lease is expired")
    return blockers


def _robot_status_blockers(
    session: BridgeSession,
    robot_status: RobotStatus,
) -> list[str]:
    blockers: list[str] = []
    if not robot_status.health.ok:
        blockers.append("live robot health check failed")
        return blockers

    health = robot_status.health.data if isinstance(robot_status.health.data, dict) else {}
    live_serial = _string_or_none(health.get("robot_serial"))
    if not session.robot_serial:
        blockers.append("session robot serial is missing")
    elif live_serial is None:
        blockers.append("live robot serial is missing")
    elif live_serial != session.robot_serial:
        blockers.append("live robot serial does not match session")
    live_server_version = _string_or_none(health.get("api_version"))
    if not session.robot_server_version:
        blockers.append("session robot server version is missing")
    elif live_server_version is None:
        blockers.append("live robot server version is missing")
    elif live_server_version != session.robot_server_version:
        blockers.append("live robot server version does not match session")
    live_protocol_api = _max_protocol_api_version(health)
    if not session.max_protocol_api_version:
        blockers.append("session max protocol API version is missing")
    elif live_protocol_api is None:
        blockers.append("live max protocol API version is missing")
    elif live_protocol_api != session.max_protocol_api_version:
        blockers.append("live max protocol API version does not match session")
    return blockers


def _live_pipette_blockers(
    session: BridgeSession,
    robot_status: RobotStatus,
) -> list[str]:
    blockers: list[str] = []
    blockers.extend(_session_pipette_identity_blockers(session))
    if blockers:
        return blockers
    if robot_status.pipettes is None or not robot_status.pipettes.ok:
        blockers.append("live pipette status check failed")
        return blockers

    pipette = _pipette_data_for_mount(robot_status, session.pipette_mount)
    if pipette is None:
        blockers.append("live pipette mount is empty")
        return blockers

    live_name = _string_or_none(
        pipette.get("name"),
        pipette.get("pipetteName"),
        pipette.get("displayName"),
    )
    if live_name is None:
        blockers.append("live pipette name is missing")
    elif live_name != session.pipette_name:
        blockers.append("live pipette name does not match session")
    live_model = _string_or_none(pipette.get("model"))
    if live_model is None:
        blockers.append("live pipette model is missing")
    elif live_model != session.pipette_model:
        blockers.append("live pipette model does not match session")
    live_id = _string_or_none(
        pipette.get("id"),
        pipette.get("pipetteId"),
        pipette.get("pipette_id"),
    )
    if live_id is None:
        blockers.append("live pipette ID is missing")
    elif live_id != session.pipette_id:
        blockers.append("live pipette ID does not match session")
    live_tip_length = _float_or_none(
        pipette.get("tip_length"),
        pipette.get("tipLength"),
        pipette.get("tipLengthMm"),
    )
    if live_tip_length is None:
        blockers.append("live pipette tip length is missing")
    elif live_tip_length != session.pipette_tip_length_mm:
        blockers.append("live pipette tip length does not match session")
    return blockers


def _session_pipette_identity_blockers(session: BridgeSession) -> list[str]:
    blockers: list[str] = []
    if not session.pipette_mount:
        blockers.append("session pipette mount is missing")
    elif session.pipette_mount not in {"left", "right"}:
        blockers.append("session pipette mount is invalid")
    if not session.pipette_name:
        blockers.append("session pipette name is missing")
    if not session.pipette_model:
        blockers.append("session pipette model is missing")
    if not session.pipette_id:
        blockers.append("session pipette ID is missing")
    if session.pipette_tip_length_mm is None:
        blockers.append("session pipette tip length is missing")
    return blockers


def _pipette_data_for_mount(
    robot_status: RobotStatus,
    mount: str,
) -> dict[str, object] | None:
    if robot_status.pipettes is None or not isinstance(robot_status.pipettes.data, dict):
        return None
    data = robot_status.pipettes.data.get("data")
    by_mount = data if isinstance(data, dict) else robot_status.pipettes.data
    pipette = by_mount.get(mount)
    return pipette if isinstance(pipette, dict) and pipette else None


def _max_protocol_api_version(health: dict[str, object]) -> str | None:
    value = health.get("maximum_protocol_api_version")
    if (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(part, int) and not isinstance(part, bool) for part in value)
    ):
        return f"{value[0]}.{value[1]}"
    if isinstance(value, str):
        return value
    return None


def _string_or_none(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str):
            return value
    return None


def _float_or_none(*values: object) -> float | None:
    for value in values:
        if isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            return float(value)
    return None


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
