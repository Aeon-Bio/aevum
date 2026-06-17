from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, model_validator

from aevum_ot2.core.evidence_primitives import _is_timezone_aware, _stable_json_sha256
from aevum_ot2.core.models import BridgeLock, BridgeSession, BridgeSessionState
from aevum_ot2.core.plans import (
    MOTION_OPERATIONS,
    PlanFragment,
    PlanOperation,
    PlanStep,
    canonicalize_plan_fragment,
    step_requires_motion,
)
from aevum_ot2.core.safety import FixtureSafetyProfile, safety_profile_integrity_blockers
from aevum_ot2.core.schema import (
    SchemaVersionError,
    load_json_object,
    parse_versioned_json_model,
)

MOTION_APPROVAL_SCHEMA_VERSION = 1
MOTION_APPROVAL_METHOD = "motion_commissioning_approval_v1"
MOTION_APPROVAL_SESSION_STATE = BridgeSessionState.MOTION_COMMISSIONING_ARMED
MOTION_APPROVAL_LOCK_STATE = "motion_commissioning_armed"
MOTION_APPROVAL_MAX_TTL = timedelta(minutes=5)


class MotionApproval(BaseModel):
    schema_version: int = MOTION_APPROVAL_SCHEMA_VERSION
    approval_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    session_id: str
    robot_serial: str
    robot_server_version: str
    max_protocol_api_version: str
    fixture_load_name: str
    fixture_params_sha256: str
    labware_definition_sha256: str
    pose_digest_sha256: str
    safety_profile_sha256: str
    plan_digest_sha256: str
    step_id: str
    operation: PlanOperation
    target_class: str = ""
    approved_by: str
    method: str = MOTION_APPROVAL_METHOD
    required_session_state: BridgeSessionState = MOTION_APPROVAL_SESSION_STATE
    required_lock_state: str = MOTION_APPROVAL_LOCK_STATE
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_approval(self) -> MotionApproval:
        if self.schema_version != MOTION_APPROVAL_SCHEMA_VERSION:
            raise ValueError("unsupported motion approval schema version")
        required = {
            "approval_id": self.approval_id,
            "session_id": self.session_id,
            "robot_serial": self.robot_serial,
            "robot_server_version": self.robot_server_version,
            "max_protocol_api_version": self.max_protocol_api_version,
            "fixture_load_name": self.fixture_load_name,
            "fixture_params_sha256": self.fixture_params_sha256,
            "labware_definition_sha256": self.labware_definition_sha256,
            "pose_digest_sha256": self.pose_digest_sha256,
            "safety_profile_sha256": self.safety_profile_sha256,
            "plan_digest_sha256": self.plan_digest_sha256,
            "step_id": self.step_id,
            "approved_by": self.approved_by,
            "method": self.method,
            "required_lock_state": self.required_lock_state,
        }
        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            raise ValueError("missing motion approval fields: " + ", ".join(missing))
        if self.method != MOTION_APPROVAL_METHOD:
            raise ValueError(f"motion approval method must be {MOTION_APPROVAL_METHOD}")
        if self.required_session_state != MOTION_APPROVAL_SESSION_STATE:
            raise ValueError(
                "motion approval required_session_state must be "
                f"{MOTION_APPROVAL_SESSION_STATE}"
            )
        if self.required_lock_state != MOTION_APPROVAL_LOCK_STATE:
            raise ValueError(
                f"motion approval required_lock_state must be {MOTION_APPROVAL_LOCK_STATE}"
            )
        if self.operation not in MOTION_OPERATIONS:
            raise ValueError("motion approval operation must require motion")
        if self.expires_at <= self.created_at:
            raise ValueError("motion approval must expire after it is created")
        if self.expires_at - self.created_at > MOTION_APPROVAL_MAX_TTL:
            raise ValueError(
                "motion approval TTL exceeds "
                f"{int(MOTION_APPROVAL_MAX_TTL.total_seconds())} seconds"
            )
        if _is_timezone_aware(self.created_at) or _is_timezone_aware(self.expires_at):
            raise ValueError("motion approval timestamps must be timezone-naive")
        _require_sha256(self.fixture_params_sha256, "fixture_params_sha256")
        _require_sha256(self.labware_definition_sha256, "labware_definition_sha256")
        _require_sha256(self.pose_digest_sha256, "pose_digest_sha256")
        _require_sha256(self.safety_profile_sha256, "safety_profile_sha256")
        _require_sha256(self.plan_digest_sha256, "plan_digest_sha256")
        return self


def build_motion_approval(
    plan: PlanFragment,
    *,
    session: BridgeSession,
    safety_profile: FixtureSafetyProfile,
    step_id: str,
    approved_by: str,
    created_at: datetime | None = None,
    expires_in: timedelta = timedelta(minutes=5),
    notes: list[str] | None = None,
) -> MotionApproval:
    created = created_at or datetime.now()
    step = _step_by_id(plan, step_id)
    if step is None:
        raise ValueError(f"motion approval step not found: {step_id}")
    if not step_requires_motion(step):
        raise ValueError(f"motion approval step does not require motion: {step_id}")
    identity = session.fixture_identity
    expires_at = created + expires_in
    plan_digest_sha256 = plan_fragment_digest(plan)
    robot_serial = session.robot_serial or ""
    robot_server_version = session.robot_server_version or ""
    max_protocol_api_version = session.max_protocol_api_version or ""
    target_class = step.target_class or ""
    scope_digest_sha256 = motion_approval_scope_digest(
        schema_version=MOTION_APPROVAL_SCHEMA_VERSION,
        created_at=created,
        expires_at=expires_at,
        session_id=session.session_id,
        robot_serial=robot_serial,
        robot_server_version=robot_server_version,
        max_protocol_api_version=max_protocol_api_version,
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        pose_digest_sha256=session.fixture_pose_digest_sha256,
        safety_profile_sha256=safety_profile.safety_profile_sha256,
        plan_digest_sha256=plan_digest_sha256,
        step_id=step.step_id,
        operation=step.operation,
        target_class=target_class,
        approved_by=approved_by,
        method=MOTION_APPROVAL_METHOD,
        required_session_state=MOTION_APPROVAL_SESSION_STATE,
        required_lock_state=MOTION_APPROVAL_LOCK_STATE,
    )
    return MotionApproval(
        approval_id=motion_approval_id(
            session_id=session.session_id,
            step_id=step.step_id,
            scope_digest_sha256=scope_digest_sha256,
            created_at=created,
        ),
        created_at=created,
        expires_at=expires_at,
        session_id=session.session_id,
        robot_serial=robot_serial,
        robot_server_version=robot_server_version,
        max_protocol_api_version=max_protocol_api_version,
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        pose_digest_sha256=session.fixture_pose_digest_sha256,
        safety_profile_sha256=safety_profile.safety_profile_sha256,
        plan_digest_sha256=plan_digest_sha256,
        step_id=step.step_id,
        operation=step.operation,
        target_class=target_class,
        approved_by=approved_by,
        notes=notes or [],
    )


def motion_approval_blockers(
    approval: MotionApproval,
    *,
    plan: PlanFragment,
    session: BridgeSession,
    safety_profile: FixtureSafetyProfile | None,
    step: PlanStep | None = None,
    lock: BridgeLock | None = None,
    now: datetime | None = None,
) -> list[str]:
    blockers: list[str] = []
    checked_at = now or datetime.now()
    canonical_plan = canonicalize_plan_fragment(plan)
    resolved_step = step or _step_by_id(canonical_plan, approval.step_id)
    if resolved_step is None:
        blockers.append(f"motion approval step is not in plan: {approval.step_id}")
    elif not step_requires_motion(resolved_step):
        blockers.append("motion approval step does not require motion")
    elif resolved_step.operation != approval.operation:
        blockers.append("motion approval operation does not match plan step")
    elif (resolved_step.target_class or "") != approval.target_class:
        blockers.append("motion approval target class does not match plan step")

    if approval.method != MOTION_APPROVAL_METHOD:
        blockers.append(f"motion approval method is not {MOTION_APPROVAL_METHOD}")
    if approval.required_session_state != MOTION_APPROVAL_SESSION_STATE:
        blockers.append(
            "motion approval required session state is not "
            f"{MOTION_APPROVAL_SESSION_STATE}"
        )
    if approval.required_lock_state != MOTION_APPROVAL_LOCK_STATE:
        blockers.append(
            f"motion approval required lock state is not {MOTION_APPROVAL_LOCK_STATE}"
        )
    if approval.approval_id != expected_motion_approval_id(approval):
        blockers.append("motion approval ID does not match scoped fields")
    if approval.created_at > checked_at:
        blockers.append("motion approval is from the future")
    if approval.expires_at <= checked_at:
        blockers.append("motion approval is expired")
    if approval.expires_at - approval.created_at > MOTION_APPROVAL_MAX_TTL:
        blockers.append("motion approval TTL exceeds maximum")
    if approval.plan_digest_sha256 != plan_fragment_digest(canonical_plan):
        blockers.append("motion approval plan digest does not match plan")
    blockers.extend(_session_scope_blockers(approval, session))
    if session.lease_expires_at <= checked_at:
        blockers.append("session lease is expired")
    blockers.extend(_safety_profile_scope_blockers(approval, safety_profile))
    if lock is not None:
        blockers.extend(_lock_scope_blockers(approval, session, lock))
        if lock.lease_expires_at <= checked_at:
            blockers.append("bridge lock lease is expired")
    return _dedupe(blockers)


def plan_fragment_digest(plan: PlanFragment) -> str:
    canonical = canonicalize_plan_fragment(plan)
    payload = _approval_plan_payload(canonical)
    return _stable_json_sha256(payload)


def motion_approval_id(
    *,
    session_id: str,
    step_id: str,
    scope_digest_sha256: str,
    created_at: datetime,
) -> str:
    # Uniqueness rides on the scope-digest segment (a hash over the RAW fields), NOT on the
    # _safe_segment label: two degenerate session/step ids that both sanitize to "empty" still
    # get distinct ids via distinct scope digests. So do NOT "fix" _safe_segment's non-raising
    # "empty" fallback into a raise — it is a label, and raising would break id generation for
    # currently-valid degenerate inputs.
    return (
        f"motion_approval:{_safe_segment(session_id)}:{_safe_segment(step_id)}:"
        f"scope-{scope_digest_sha256[:16]}:{created_at:%Y%m%d-%H%M%S-%f}"
    )


def expected_motion_approval_id(approval: MotionApproval) -> str:
    return motion_approval_id(
        session_id=approval.session_id,
        step_id=approval.step_id,
        scope_digest_sha256=motion_approval_scope_digest(
            schema_version=approval.schema_version,
            created_at=approval.created_at,
            expires_at=approval.expires_at,
            session_id=approval.session_id,
            robot_serial=approval.robot_serial,
            robot_server_version=approval.robot_server_version,
            max_protocol_api_version=approval.max_protocol_api_version,
            fixture_load_name=approval.fixture_load_name,
            fixture_params_sha256=approval.fixture_params_sha256,
            labware_definition_sha256=approval.labware_definition_sha256,
            pose_digest_sha256=approval.pose_digest_sha256,
            safety_profile_sha256=approval.safety_profile_sha256,
            plan_digest_sha256=approval.plan_digest_sha256,
            step_id=approval.step_id,
            operation=approval.operation,
            target_class=approval.target_class,
            approved_by=approval.approved_by,
            method=approval.method,
            required_session_state=approval.required_session_state,
            required_lock_state=approval.required_lock_state,
        ),
        created_at=approval.created_at,
    )


def motion_approval_scope_digest(**scope: Any) -> str:
    payload = {
        key: _json_scope_value(value)
        for key, value in sorted(scope.items())
        if key != "approval_id"
    }
    return _stable_json_sha256(payload)


def write_motion_approval(approval: MotionApproval, path: str | Path) -> Path:
    approval_path = Path(path)
    approval_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = approval_path.with_suffix(approval_path.suffix + ".tmp")
    tmp.write_text(approval.model_dump_json(indent=2) + "\n")
    tmp.replace(approval_path)
    return approval_path


def load_motion_approval(path: str | Path) -> MotionApproval:
    data = load_json_object(path, schema_name="MotionApproval")
    return parse_versioned_json_model(
        data,
        MotionApproval,
        schema_name="MotionApproval",
        path=path,
    )


def motion_approval_load_blockers(path: str | Path) -> list[str]:
    try:
        load_motion_approval(path)
    except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
        return [f"motion approval is invalid: {exc}"]
    return []


def _session_scope_blockers(
    approval: MotionApproval,
    session: BridgeSession,
) -> list[str]:
    identity = session.fixture_identity
    blockers: list[str] = []
    if approval.session_id != session.session_id:
        blockers.append("motion approval session does not match session")
    if approval.robot_serial != (session.robot_serial or ""):
        blockers.append("motion approval robot serial does not match session")
    if approval.robot_server_version != (session.robot_server_version or ""):
        blockers.append("motion approval robot server version does not match session")
    if approval.max_protocol_api_version != (session.max_protocol_api_version or ""):
        blockers.append("motion approval protocol API version does not match session")
    if approval.fixture_load_name != identity.load_name:
        blockers.append("motion approval fixture does not match session")
    if approval.fixture_params_sha256 != identity.params_sha256:
        blockers.append("motion approval fixture params checksum does not match session")
    if approval.labware_definition_sha256 != identity.labware_definition_sha256:
        blockers.append("motion approval labware checksum does not match session")
    if approval.pose_digest_sha256 != session.fixture_pose_digest_sha256:
        blockers.append("motion approval pose digest does not match session")
    if session.state != approval.required_session_state:
        blockers.append(
            f"session state {session.state} does not match motion approval state "
            f"{approval.required_session_state}"
        )
    if not session.motion_allowed:
        blockers.append("session is not motion-armed")
    return blockers


def _safety_profile_scope_blockers(
    approval: MotionApproval,
    safety_profile: FixtureSafetyProfile | None,
) -> list[str]:
    if safety_profile is None:
        return ["motion approval requires a safety profile"]
    blockers = safety_profile_integrity_blockers(safety_profile)
    if approval.safety_profile_sha256 != safety_profile.safety_profile_sha256:
        blockers.append("motion approval safety profile checksum does not match")
    if approval.pose_digest_sha256 != safety_profile.pose_digest_sha256:
        blockers.append("motion approval pose digest does not match safety profile")
    return blockers


def _lock_scope_blockers(
    approval: MotionApproval,
    session: BridgeSession,
    lock: BridgeLock,
) -> list[str]:
    blockers: list[str] = []
    if lock.state != approval.required_lock_state:
        blockers.append(
            f"bridge lock state {lock.state} does not match motion approval lock state "
            f"{approval.required_lock_state}"
        )
    if lock.session_id != session.session_id:
        blockers.append("bridge lock session does not match motion approval session")
    if lock.owner_id != session.owner_id:
        blockers.append("bridge lock owner does not match session")
    return blockers


def _step_by_id(plan: PlanFragment, step_id: str) -> PlanStep | None:
    canonical = canonicalize_plan_fragment(plan)
    for step in canonical.steps:
        if step.step_id == step_id:
            return step
    return None


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or not all(char in _HEX_DIGITS for char in value):
        raise ValueError(f"{field_name} must be a 64-character sha256")


def _safe_segment(value: str) -> str:
    safe = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in value
    ).strip("_")
    return safe or "empty"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _approval_plan_payload(plan: PlanFragment) -> dict[str, Any]:
    return {
        "schema_version": plan.schema_version,
        "session_id": plan.session_id,
        "steps": [
            {
                "step_id": step.step_id,
                "operation": step.operation,
                "target_class": step.target_class or "",
                "parameters": step.parameters,
            }
            for step in plan.steps
        ],
    }


def _json_scope_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, BridgeSessionState):
        return value.value
    return value


_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
