from __future__ import annotations

from pydantic import BaseModel, Field

from aevum_ot2.core.models import (
    BridgeSession,
    BridgeSessionState,
    EvidenceClaim,
    GateName,
    GateResult,
    OffsetRegistry,
)
from aevum_ot2.core.motion_approval import MotionApproval, motion_approval_blockers
from aevum_ot2.core.plans import (
    FORMALLY_CLOSED_OPERATIONS,
    PlanFragment,
    PlanOperation,
    PlanStep,
    canonicalize_plan_fragment,
    step_requires_motion,
)
from aevum_ot2.core.readiness import ReadinessResult
from aevum_ot2.core.records import (
    TARGET_CLASS_BY_NAME,
    TargetClassResult,
    TargetClassVerificationRecord,
    target_class_authority,
)
from aevum_ot2.core.recovery import NoMotionRecoveryDisposition
from aevum_ot2.core.registry import offset_match_gate
from aevum_ot2.core.safety import FixtureSafetyProfile, home_clearance_gate
from aevum_ot2.core.targets import matching_high_z_target, target_policy_for


class StepValidationResult(BaseModel):
    step_id: str
    operation: PlanOperation
    allowed: bool
    requires_motion: bool
    reasons: list[str] = Field(default_factory=list)
    gate_results: list[GateResult] = Field(default_factory=list)


class PlanValidationResult(BaseModel):
    session_id: str
    allowed: bool
    motion_allowed: bool = False
    motion_approval_id: str = ""
    reasons: list[str] = Field(default_factory=list)
    steps: list[StepValidationResult] = Field(default_factory=list)


def validate_plan_fragment(
    plan: PlanFragment,
    session: BridgeSession,
    *,
    readiness: ReadinessResult | None = None,
    target_records: list[TargetClassVerificationRecord] | None = None,
    offset_registry: OffsetRegistry | None = None,
    safety_profile: FixtureSafetyProfile | None = None,
    fixture_pose: object | None = None,
    pose_claims: list[EvidenceClaim] | None = None,
    recovery_disposition: NoMotionRecoveryDisposition | str | None = None,
    daemon_motion_enabled: bool = False,
    motion_approval: MotionApproval | None = None,
) -> PlanValidationResult:
    """Validate a plan fragment against local state without contacting the robot."""

    plan = canonicalize_plan_fragment(plan)
    reasons: list[str] = []
    if plan.session_id != session.session_id:
        reasons.append(
            f"plan session {plan.session_id} does not match session {session.session_id}"
        )
    if not plan.steps:
        reasons.append("plan has no steps")
    duplicate_step_ids = _duplicate_step_ids(plan.steps)
    if duplicate_step_ids:
        reasons.append("duplicate step IDs: " + ", ".join(duplicate_step_ids))

    duplicate_target_classes = _duplicate_target_classes(target_records or [])
    if duplicate_target_classes:
        reasons.append(
            "duplicate target-class records: " + ", ".join(duplicate_target_classes)
        )

    target_record_by_class = {
        record.target_class: record for record in target_records or []
    }
    step_results = [
        _validate_step(
            step,
            session,
            readiness=readiness,
            target_record_by_class=target_record_by_class,
            offset_registry=offset_registry,
            safety_profile=safety_profile,
            fixture_pose=fixture_pose,
            pose_claims=pose_claims,
            recovery_disposition=recovery_disposition,
            daemon_motion_enabled=daemon_motion_enabled,
        )
        for step in plan.steps
    ]
    for step_result in step_results:
        reasons.extend(
            f"{step_result.step_id}: {reason}" for reason in step_result.reasons
        )
    motion_approval_reasons = _motion_approval_reasons(
        plan,
        session,
        safety_profile=safety_profile,
        motion_approval=motion_approval,
        daemon_motion_enabled=daemon_motion_enabled,
    )
    reasons.extend(f"motion_approval: {reason}" for reason in motion_approval_reasons)
    motion_allowed = (
        daemon_motion_enabled
        and motion_approval is not None
        and not motion_approval_reasons
        and not reasons
        and any(step.requires_motion for step in step_results)
    )

    return PlanValidationResult(
        session_id=session.session_id,
        allowed=not reasons,
        motion_allowed=motion_allowed,
        motion_approval_id=motion_approval.approval_id if motion_approval is not None else "",
        reasons=reasons,
        steps=step_results,
    )


def _motion_approval_reasons(
    plan: PlanFragment,
    session: BridgeSession,
    *,
    safety_profile: FixtureSafetyProfile | None,
    motion_approval: MotionApproval | None,
    daemon_motion_enabled: bool,
) -> list[str]:
    motion_steps = [step for step in plan.steps if step_requires_motion(step)]
    if motion_approval is None:
        if motion_steps:
            return ["motion approval is required for motion execution"]
        return []
    reasons: list[str] = []
    if not daemon_motion_enabled:
        reasons.append("motion approval requires a motion-capable daemon")
    if len(motion_steps) != 1:
        reasons.append("motion approval requires exactly one motion step")
    step = motion_steps[0] if len(motion_steps) == 1 else None
    reasons.extend(
        motion_approval_blockers(
            motion_approval,
            plan=plan,
            session=session,
            safety_profile=safety_profile,
            step=step,
        )
    )
    return _dedupe(reasons)


def _duplicate_step_ids(steps: list[PlanStep]) -> list[str]:
    seen: set[str] = set()
    duplicate_ids: set[str] = set()
    for step in steps:
        if step.step_id in seen:
            duplicate_ids.add(step.step_id)
        seen.add(step.step_id)
    return sorted(duplicate_ids)


def _duplicate_target_classes(
    target_records: list[TargetClassVerificationRecord],
) -> list[str]:
    seen: set[str] = set()
    duplicate_classes: set[str] = set()
    for record in target_records:
        if record.target_class in seen:
            duplicate_classes.add(record.target_class)
        seen.add(record.target_class)
    return sorted(duplicate_classes)


def _validate_step(
    step: PlanStep,
    session: BridgeSession,
    *,
    readiness: ReadinessResult | None,
    target_record_by_class: dict[str, TargetClassVerificationRecord],
    offset_registry: OffsetRegistry | None,
    safety_profile: FixtureSafetyProfile | None,
    fixture_pose: object | None,
    pose_claims: list[EvidenceClaim] | None,
    recovery_disposition: NoMotionRecoveryDisposition | str | None,
    daemon_motion_enabled: bool,
) -> StepValidationResult:
    reasons: list[str] = []
    gate_results: list[GateResult] = []
    requires_motion = step_requires_motion(step)

    if step.operation == "inspect_context":
        return _step_result(step, requires_motion=False, reasons=reasons)

    allowed_session_states = {BridgeSessionState.READY_NO_MOTION}
    if requires_motion:
        allowed_session_states.add(BridgeSessionState.MOTION_COMMISSIONING_ARMED)
    if session.state not in allowed_session_states:
        reasons.append(
            "session state is "
            f"{session.state}, not one of {', '.join(sorted(allowed_session_states))}"
        )

    if step.operation == "close_session":
        return _step_result(step, requires_motion=False, reasons=reasons)

    if step.operation == "capture_evidence":
        return _step_result(step, requires_motion=False, reasons=reasons)

    if step.operation == "record_evidence":
        reasons.append("record_evidence plan execution is not implemented")
        return _step_result(step, requires_motion=False, reasons=reasons)

    if step.operation == "prepare_registration_plan":
        _require_registration_readiness(readiness, reasons)
        return _step_result(step, requires_motion=False, reasons=reasons)

    if requires_motion:
        _validate_motion_step(
            step,
            session=session,
            readiness=readiness,
            target_record_by_class=target_record_by_class,
            offset_registry=offset_registry,
            safety_profile=safety_profile,
            fixture_pose=fixture_pose,
            pose_claims=pose_claims,
            recovery_disposition=recovery_disposition,
            daemon_motion_enabled=daemon_motion_enabled,
            reasons=reasons,
            gate_results=gate_results,
        )

    return _step_result(
        step,
        requires_motion=requires_motion,
        reasons=reasons,
        gate_results=gate_results,
    )


def _validate_motion_step(
    step: PlanStep,
    *,
    session: BridgeSession,
    readiness: ReadinessResult | None,
    target_record_by_class: dict[str, TargetClassVerificationRecord],
    offset_registry: OffsetRegistry | None,
    safety_profile: FixtureSafetyProfile | None,
    fixture_pose: object | None,
    pose_claims: list[EvidenceClaim] | None,
    recovery_disposition: NoMotionRecoveryDisposition | str | None,
    daemon_motion_enabled: bool,
    reasons: list[str],
    gate_results: list[GateResult],
) -> None:
    if not daemon_motion_enabled:
        reasons.append("motion-capable bridge daemon is not implemented/enabled")
    _require_registration_readiness(readiness, reasons)

    if step.operation == "home":
        _require_home_clearance(
            session,
            safety_profile=safety_profile,
            fixture_pose=fixture_pose,
            pose_claims=pose_claims,
            recovery_disposition=recovery_disposition,
            allowed_session_states={
                BridgeSessionState.READY_NO_MOTION,
                BridgeSessionState.MOTION_COMMISSIONING_ARMED,
            },
            reasons=reasons,
            gate_results=gate_results,
        )
        return

    if step.operation in {"move_high_z", "move_low_z", "liquid_handling"}:
        if step.target_class is None:
            _append_missing_target_gate(step, "target_class", gate_results)
            reasons.append(f"{step.operation} requires a target class")
            return
        target_class = TARGET_CLASS_BY_NAME.get(step.target_class)
        if target_class is None:
            _append_missing_target_gate(step, f"target_class:{step.target_class}", gate_results)
            reasons.append(f"unknown target class: {step.target_class}")
            return
        target_record = target_record_by_class.get(step.target_class)
        if target_record is None:
            _append_missing_target_gate(step, f"target_record:{step.target_class}", gate_results)
            reasons.append(f"missing target-class record: {step.target_class}")
            return
        target_failed = target_record.result == TargetClassResult.FAILED
        if step.operation == "move_high_z":
            _require_first_high_z_gate(
                target_record,
                target_record_by_class,
                session=session,
                safety_profile=safety_profile,
                fixture_pose=fixture_pose,
                pose_claims=pose_claims,
                recovery_disposition=recovery_disposition,
                target_failed=target_failed,
                reasons=reasons,
                gate_results=gate_results,
            )
        if step.operation == "move_low_z":
            _require_low_z_dry_gate(
                target_record,
                target_record_by_class,
                session=session,
                registry=offset_registry,
                safety_profile=safety_profile,
                fixture_pose=fixture_pose,
                target_failed=target_failed,
                reasons=reasons,
                gate_results=gate_results,
            )
        if step.operation == "liquid_handling":
            _require_wet_gate(
                target_record,
                target_record_by_class,
                session=session,
                registry=offset_registry,
                safety_profile=safety_profile,
                fixture_pose=fixture_pose,
                target_failed=target_failed,
                reasons=reasons,
                gate_results=gate_results,
            )
        return

    if step.operation in FORMALLY_CLOSED_OPERATIONS:
        # Closed by design, not unimplemented: a labware offset is applied at run setup via
        # the offset registry / Opentrons /labwareOffsets API, not as a motion step (OT-2).
        reasons.append(
            f"{step.operation} is a closed operation: labware offsets are applied at run "
            "setup via the offset registry, not as a motion step"
        )
        return

    reasons.append(f"unsupported motion operation: {step.operation}")


def _require_registration_readiness(
    readiness: ReadinessResult | None,
    reasons: list[str],
) -> None:
    if readiness is None:
        reasons.append("registration readiness has not been evaluated")
    elif not readiness.registration_ready:
        reasons.append("registration readiness failed: " + "; ".join(readiness.reasons))


def _require_low_z_dry_gate(
    target_record: TargetClassVerificationRecord,
    target_record_by_class: dict[str, TargetClassVerificationRecord],
    *,
    session: BridgeSession,
    registry: OffsetRegistry | None,
    safety_profile: FixtureSafetyProfile | None,
    fixture_pose: object | None,
    target_failed: bool,
    reasons: list[str],
    gate_results: list[GateResult],
) -> None:
    blockers: list[str] = []
    missing_claims: list[str] = []
    predecessor_claim_ids: list[str] = []
    if target_failed:
        blockers.append(f"target class {target_record.target_class} is failed")
    matching_high_z = matching_high_z_target(target_record.target_class)
    if matching_high_z is None:
        missing_claims.append("matching_high_z_target")
    else:
        high_z_record = target_record_by_class.get(matching_high_z)
        if high_z_record is None:
            missing_claims.append(f"target_record:{matching_high_z}")
        else:
            authority = target_class_authority(
                high_z_record,
                session=session,
                reference_record=target_record,
                fixture_pose=fixture_pose,
            )
            missing_claims.extend(authority.missing_claims)
            blockers.extend(authority.blockers)
            predecessor_claim_ids.extend(authority.claim_ids)

    offset_gate = offset_match_gate(
        registry=registry,
        session=session,
        target_record=target_record,
        safety_profile=safety_profile,
        fixture_pose=fixture_pose,
    )
    gate_results.append(offset_gate)
    if not offset_gate.passed:
        missing_claims.append("promoted_offset_authority")
        missing_claims.extend(offset_gate.missing_claims)
        blockers.extend(offset_gate.blockers)

    gate = GateResult(
        gate_name=GateName.LOW_Z_DRY,
        passed=not blockers and not missing_claims,
        motion_allowed=False,
        blockers=_dedupe(blockers),
        missing_claims=_dedupe(missing_claims),
        claim_ids=(
            [*predecessor_claim_ids, *offset_gate.claim_ids]
            if not blockers and not missing_claims
            else []
        ),
    )
    gate_results.append(gate)
    if gate.passed:
        return
    for missing_claim in gate.missing_claims:
        reasons.append(f"missing low-Z input: {missing_claim}")
    reasons.extend(gate.blockers)


def _require_wet_gate(
    target_record: TargetClassVerificationRecord,
    target_record_by_class: dict[str, TargetClassVerificationRecord],
    *,
    session: BridgeSession,
    registry: OffsetRegistry | None,
    safety_profile: FixtureSafetyProfile | None,
    fixture_pose: object | None,
    target_failed: bool,
    reasons: list[str],
    gate_results: list[GateResult],
) -> None:
    blockers: list[str] = []
    missing_claims: list[str] = []
    predecessor_claim_ids: list[str] = []
    if target_failed:
        blockers.append(f"target class {target_record.target_class} is failed")
    try:
        policy = target_policy_for(target_record.target_class)
    except KeyError:
        blockers.append(f"unknown target policy: {target_record.target_class}")
    else:
        if not policy.wet:
            missing_claims.append("wet_target_policy")
        for predecessor in policy.required_predecessors:
            predecessor_record = target_record_by_class.get(predecessor)
            if predecessor_record is None:
                missing_claims.append(f"target_record:{predecessor}")
            else:
                authority = target_class_authority(
                    predecessor_record,
                    session=session,
                    reference_record=target_record,
                    fixture_pose=fixture_pose,
                )
                missing_claims.extend(authority.missing_claims)
                blockers.extend(authority.blockers)
                predecessor_claim_ids.extend(authority.claim_ids)

    offset_gate = offset_match_gate(
        registry=registry,
        session=session,
        target_record=target_record,
        safety_profile=safety_profile,
        fixture_pose=fixture_pose,
    )
    gate_results.append(offset_gate)
    if not offset_gate.passed:
        missing_claims.append("promoted_offset_authority")
        missing_claims.extend(offset_gate.missing_claims)
        blockers.extend(offset_gate.blockers)

    gate = GateResult(
        gate_name=GateName.WET,
        passed=not blockers and not missing_claims,
        motion_allowed=False,
        blockers=_dedupe(blockers),
        missing_claims=_dedupe(missing_claims),
        claim_ids=(
            [*predecessor_claim_ids, *offset_gate.claim_ids]
            if not blockers and not missing_claims
            else []
        ),
    )
    gate_results.append(gate)
    if gate.passed:
        return
    for missing_claim in gate.missing_claims:
        reasons.append(f"missing wet input: {missing_claim}")
    reasons.extend(gate.blockers)


def _require_home_clearance(
    session: BridgeSession,
    *,
    safety_profile: FixtureSafetyProfile | None,
    fixture_pose: object | None,
    pose_claims: list[EvidenceClaim] | None,
    recovery_disposition: NoMotionRecoveryDisposition | str | None,
    allowed_session_states: set[BridgeSessionState] | None = None,
    reasons: list[str],
    gate_results: list[GateResult],
) -> None:
    gate = home_clearance_gate(
        session=session,
        safety_profile=safety_profile,
        fixture_pose=fixture_pose,
        pose_claims=pose_claims,
        recovery_disposition=recovery_disposition,
        allowed_session_states=allowed_session_states,
    )
    gate_results.append(gate)
    if gate.passed:
        return
    for missing_claim in gate.missing_claims:
        reasons.append(f"missing home-clearance input: {missing_claim}")
    reasons.extend(gate.blockers)


def _require_first_high_z_gate(
    target_record: TargetClassVerificationRecord,
    target_record_by_class: dict[str, TargetClassVerificationRecord],
    *,
    session: BridgeSession,
    safety_profile: FixtureSafetyProfile | None,
    fixture_pose: object | None,
    pose_claims: list[EvidenceClaim] | None,
    recovery_disposition: NoMotionRecoveryDisposition | str | None,
    target_failed: bool,
    reasons: list[str],
    gate_results: list[GateResult],
) -> None:
    blockers: list[str] = []
    missing_claims: list[str] = []
    predecessor_claim_ids: list[str] = []
    if target_failed:
        blockers.append(f"target class {target_record.target_class} is failed")
    target_authority_gate = _target_authority_gate(
        target_record,
        session=session,
        fixture_pose=fixture_pose,
    )
    gate_results.append(target_authority_gate)
    if not target_authority_gate.passed:
        missing_claims.extend(target_authority_gate.missing_claims)
        blockers.extend(target_authority_gate.blockers)
    home_gate = home_clearance_gate(
        session=session,
        safety_profile=safety_profile,
        fixture_pose=fixture_pose,
        pose_claims=pose_claims,
        recovery_disposition=recovery_disposition,
    )
    if not home_gate.passed:
        missing_claims.append("home_clearance_gate_passed")
        blockers.extend(home_gate.blockers)
        missing_claims.extend(home_gate.missing_claims)

    try:
        policy = target_policy_for(target_record.target_class)
    except KeyError:
        blockers.append(f"unknown target policy: {target_record.target_class}")
    else:
        if not policy.first_pass_allowed:
            for predecessor in policy.required_predecessors:
                predecessor_record = target_record_by_class.get(predecessor)
                if predecessor_record is None:
                    missing_claims.append(f"target_record:{predecessor}")
                else:
                    authority = target_class_authority(
                        predecessor_record,
                        session=session,
                        reference_record=target_record,
                        fixture_pose=fixture_pose,
                    )
                    missing_claims.extend(authority.missing_claims)
                    blockers.extend(authority.blockers)
                    predecessor_claim_ids.extend(authority.claim_ids)

    gate = GateResult(
        gate_name=GateName.FIRST_HIGH_Z,
        passed=not blockers and not missing_claims,
        motion_allowed=False,
        blockers=_dedupe(blockers),
        missing_claims=_dedupe(missing_claims),
        claim_ids=(
            [*target_authority_gate.claim_ids, *predecessor_claim_ids, *home_gate.claim_ids]
            if not blockers and not missing_claims
            else []
        ),
    )
    gate_results.append(gate)
    if gate.passed:
        return
    for missing_claim in gate.missing_claims:
        reasons.append(f"missing first-high-Z input: {missing_claim}")
    reasons.extend(gate.blockers)


def _target_authority_gate(
    target_record: TargetClassVerificationRecord,
    *,
    session: BridgeSession,
    fixture_pose: object | None,
) -> GateResult:
    authority = target_class_authority(
        target_record,
        session=session,
        fixture_pose=fixture_pose,
    )
    return GateResult(
        gate_name=GateName.TARGET_CLASS_AUTHORITY,
        passed=authority.passed,
        motion_allowed=False,
        blockers=authority.blockers,
        missing_claims=authority.missing_claims,
        claim_ids=authority.claim_ids if authority.passed else [],
        evidence=authority.evidence,
    )


def _append_missing_target_gate(
    step: PlanStep,
    missing_claim: str,
    gate_results: list[GateResult],
) -> None:
    gate_name = _motion_gate_name_for_step(step)
    if gate_name is None:
        return
    gate_results.append(
        GateResult(
            gate_name=gate_name,
            passed=False,
            motion_allowed=False,
            missing_claims=[missing_claim],
        )
    )


def _motion_gate_name_for_step(step: PlanStep) -> GateName | None:
    if step.operation == "move_high_z":
        return GateName.FIRST_HIGH_Z
    if step.operation == "move_low_z":
        return GateName.LOW_Z_DRY
    if step.operation == "liquid_handling":
        return GateName.WET
    return None


def _step_result(
    step: PlanStep,
    *,
    requires_motion: bool,
    reasons: list[str],
    gate_results: list[GateResult] | None = None,
) -> StepValidationResult:
    return StepValidationResult(
        step_id=step.step_id,
        operation=step.operation,
        allowed=not reasons,
        requires_motion=requires_motion,
        reasons=reasons,
        gate_results=gate_results or [],
    )


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
