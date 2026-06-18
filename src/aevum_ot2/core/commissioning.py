from __future__ import annotations

import sqlite3
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from aevum_ot2.core.context import SessionContext
from aevum_ot2.core.execution import PlanExecutionResult
from aevum_ot2.core.motion_commissioning import (
    MISSING_APPROVAL_REASON,
    MotionApprovalArmResult,
)
from aevum_ot2.core.plans import PlanFragment
from aevum_ot2.core.safety import FixtureSafetyProfile
from aevum_ot2.core.validation import PlanValidationResult
from aevum_ot2.server.service import BridgeService, BridgeServiceError

# Operability layer over the existing motion-capable BridgeService. This module
# orchestrates the bridge core's already-fail-closed transitions; it MUST NOT
# create motion authority. It never mints a MotionApproval, never sets
# motion_allowed, and never calls consume/dispatch directly. The bridge core
# stays the sole authority for every gate -- this layer only sequences calls,
# surfaces blockers, and refuses to proceed unless the operator explicitly
# confirms each transition.

CommissioningPhase = Literal[
    "preflight",
    "arm",
    "execute",
]

CommissioningStepStatus = Literal[
    "ok",
    "blocked",
    "would_arm",
    "would_execute",
    "armed",
    "executed",
    "error",
]


class CommissioningStep(BaseModel):
    """One observable transition in the commissioning sequence."""

    model_config = ConfigDict(extra="forbid")

    name: str
    phase: CommissioningPhase
    status: CommissioningStepStatus
    detail: str = ""
    blockers: list[str] = Field(default_factory=list)


class CommissioningReport(BaseModel):
    """Fail-closed summary of a commissioning preflight or sequence.

    ``armed``/``executed`` stay ``False`` on any blocker. The report emits the
    transitions that *would* run in a dry-run without arming anything.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    session_id: str
    motion_enabled: bool
    confirm_arm: bool = False
    confirm_execute: bool = False
    dry_run: bool = True
    health_ok: bool = False
    state_db_ok: bool = False
    plan_blocked_by_missing_approval_only: bool = False
    armed: bool = False
    executed: bool = False
    motion_commands_sent: bool = False
    approval_id: str = ""
    blockers: list[str] = Field(default_factory=list)
    steps: list[CommissioningStep] = Field(default_factory=list)
    context: SessionContext | None = None
    validation: PlanValidationResult | None = None
    arm_result: MotionApprovalArmResult | None = None
    execution: PlanExecutionResult | None = None

    @property
    def ok(self) -> bool:
        return not self.blockers


def run_commissioning_preflight(
    service: BridgeService,
    session_id: str,
    plan: PlanFragment,
    *,
    safety_profile: FixtureSafetyProfile | None = None,
    fixture_qc_record: str | None = None,
    target_class_records: list[str] | None = None,
    confirm_arm: bool = False,
    confirm_execute: bool = False,
) -> CommissioningReport:
    """Read-only commissioning preflight over an existing BridgeService.

    Runs, in order: (a) a health/state-db reachability check, (b) a session
    context fetch, and (c) a motion-disabled plan validation. It confirms the
    plan is blocked ONLY by the missing-approval reason; any other blocker is
    surfaced. Nothing is armed and no motion is dispatched -- this never calls
    ``arm_motion_approval`` or ``execute_next``.
    """

    report = CommissioningReport(
        session_id=session_id,
        motion_enabled=service.motion_enabled,
        confirm_arm=confirm_arm,
        confirm_execute=confirm_execute,
        dry_run=True,
    )

    if not _check_health(service, report):
        return report
    if not _check_session_context(
        service,
        session_id,
        report,
        fixture_qc_record=fixture_qc_record,
        target_class_records=target_class_records,
    ):
        return report
    _check_plan_blocked_by_missing_approval(
        service,
        session_id,
        plan,
        report,
        safety_profile=safety_profile,
        fixture_qc_record=fixture_qc_record,
        target_class_records=target_class_records,
    )
    return report


def run_commissioning_sequence(
    service: BridgeService,
    session_id: str,
    plan: PlanFragment,
    *,
    approved_by: str,
    safety_profile: FixtureSafetyProfile | None = None,
    fixture_qc_record: str | None = None,
    target_class_records: list[str] | None = None,
    confirm_arm: bool = False,
    motion_enabled: bool = False,
    confirm_execute: bool = False,
    expires_in_seconds: int = 300,
) -> CommissioningReport:
    """Fail-closed commissioning sequence over an existing BridgeService.

    The DEFAULT is a dry-run: with ``confirm_arm`` unset (or ``motion_enabled``
    unset) this reports the transition that *would* arm and emits nothing -- it
    never invokes ``arm_motion_approval``. Only when the caller passes both
    ``confirm_arm=True`` AND ``motion_enabled=True`` do we ask the bridge to
    arm. A further explicit ``confirm_execute=True`` is required before we ask
    the bridge to ``execute_next`` with the minted approval. Every transition is
    fail-closed: ``armed``/``executed`` stay ``False`` on any blocker.
    """

    report = run_commissioning_preflight(
        service,
        session_id,
        plan,
        safety_profile=safety_profile,
        fixture_qc_record=fixture_qc_record,
        target_class_records=target_class_records,
        confirm_arm=confirm_arm,
        confirm_execute=confirm_execute,
    )
    if report.blockers:
        return report

    if not _arm_gate_open(report, confirm_arm=confirm_arm, motion_enabled=motion_enabled):
        return report

    if not _arm(
        service,
        session_id,
        plan,
        report,
        approved_by=approved_by,
        safety_profile=safety_profile,
        fixture_qc_record=fixture_qc_record,
        target_class_records=target_class_records,
        expires_in_seconds=expires_in_seconds,
    ):
        return report

    if not _execute_gate_open(report, confirm_execute=confirm_execute):
        return report

    _execute(
        service,
        session_id,
        plan,
        report,
        safety_profile=safety_profile,
        fixture_qc_record=fixture_qc_record,
        target_class_records=target_class_records,
    )
    return report


def _check_health(service: BridgeService, report: CommissioningReport) -> bool:
    try:
        health = service.health()
        sessions = service.list_sessions()
    except (BridgeServiceError, sqlite3.Error, OSError, ValueError) as exc:
        report.state_db_ok = False
        report.blockers.append(f"state-db check failed: {exc}")
        report.steps.append(
            CommissioningStep(
                name="health_state_db",
                phase="preflight",
                status="error",
                detail="health or state-db probe raised",
                blockers=[str(exc)],
            )
        )
        return False
    report.health_ok = health.ok
    report.state_db_ok = True
    if not health.ok:
        report.blockers.append("bridge service health is not ok")
        report.steps.append(
            CommissioningStep(
                name="health_state_db",
                phase="preflight",
                status="blocked",
                detail="health reported not ok",
                blockers=["bridge service health is not ok"],
            )
        )
        return False
    report.steps.append(
        CommissioningStep(
            name="health_state_db",
            phase="preflight",
            status="ok",
            detail=f"state db reachable; {len(sessions)} session(s) listed",
        )
    )
    return True


def _check_session_context(
    service: BridgeService,
    session_id: str,
    report: CommissioningReport,
    *,
    fixture_qc_record: str | None,
    target_class_records: list[str] | None,
) -> bool:
    try:
        context = service.get_session_context(
            session_id,
            fixture_qc_record=fixture_qc_record,
            target_class_records=list(target_class_records or []),
        )
    except (BridgeServiceError, sqlite3.Error, OSError, ValueError) as exc:
        report.blockers.append(f"session context fetch failed: {exc}")
        report.steps.append(
            CommissioningStep(
                name="session_context",
                phase="preflight",
                status="error",
                detail="get_session_context raised",
                blockers=[str(exc)],
            )
        )
        return False
    report.context = context
    report.steps.append(
        CommissioningStep(
            name="session_context",
            phase="preflight",
            status="ok",
            detail=f"session state {context.state}; motion_allowed={context.motion_allowed}",
        )
    )
    return True


def _check_plan_blocked_by_missing_approval(
    service: BridgeService,
    session_id: str,
    plan: PlanFragment,
    report: CommissioningReport,
    *,
    safety_profile: FixtureSafetyProfile | None,
    fixture_qc_record: str | None,
    target_class_records: list[str] | None,
) -> bool:
    try:
        # Validate with motion disabled and NO approval supplied. This layer
        # never mints an approval; the only acceptable blocker is the bridge's
        # own missing-approval reason. Anything else is surfaced unmodified.
        validation = service.validate_plan(
            session_id,
            plan,
            fixture_qc_record=fixture_qc_record,
            target_class_records=list(target_class_records or []),
            safety_profile=safety_profile,
        )
    except (BridgeServiceError, sqlite3.Error, OSError, ValueError) as exc:
        report.blockers.append(f"plan validation failed: {exc}")
        report.steps.append(
            CommissioningStep(
                name="validate_plan",
                phase="preflight",
                status="error",
                detail="validate_plan raised",
                blockers=[str(exc)],
            )
        )
        return False
    report.validation = validation

    if validation.motion_allowed or validation.allowed:
        # A motion-disabled, approval-free validation must NOT allow motion.
        blocker = "plan validation unexpectedly allows execution before arming"
        report.blockers.append(blocker)
        report.steps.append(
            CommissioningStep(
                name="validate_plan",
                phase="preflight",
                status="blocked",
                detail="validation allowed without an approval",
                blockers=[blocker],
            )
        )
        return False

    other_reasons = [
        reason for reason in validation.reasons if reason != MISSING_APPROVAL_REASON
    ]
    if MISSING_APPROVAL_REASON not in validation.reasons:
        report.blockers.append(
            "plan is not blocked by the missing-approval reason; "
            "this layer only arms plans the bridge blocks solely on approval"
        )
    report.blockers.extend(f"plan blocker (not missing-approval): {r}" for r in other_reasons)

    if report.blockers:
        report.steps.append(
            CommissioningStep(
                name="validate_plan",
                phase="preflight",
                status="blocked",
                detail="plan blocked by reasons other than missing approval",
                blockers=list(report.blockers),
            )
        )
        return False

    report.plan_blocked_by_missing_approval_only = True
    report.steps.append(
        CommissioningStep(
            name="validate_plan",
            phase="preflight",
            status="ok",
            detail="plan is blocked ONLY by the missing motion approval",
        )
    )
    return True


def _arm_gate_open(
    report: CommissioningReport,
    *,
    confirm_arm: bool,
    motion_enabled: bool,
) -> bool:
    if confirm_arm and motion_enabled:
        report.dry_run = False
        return True

    # DEFAULT dry-run path: report what would arm and emit nothing. We do NOT
    # call arm_motion_approval here.
    detail_bits = []
    if not confirm_arm:
        detail_bits.append("confirm_arm not set")
    if not motion_enabled:
        detail_bits.append("motion_enabled not set")
    report.dry_run = True
    report.steps.append(
        CommissioningStep(
            name="arm_motion_approval",
            phase="arm",
            status="would_arm",
            detail="would arm motion approval (" + ", ".join(detail_bits) + ")",
        )
    )
    return False


def _arm(
    service: BridgeService,
    session_id: str,
    plan: PlanFragment,
    report: CommissioningReport,
    *,
    approved_by: str,
    safety_profile: FixtureSafetyProfile | None,
    fixture_qc_record: str | None,
    target_class_records: list[str] | None,
    expires_in_seconds: int,
) -> bool:
    try:
        arm_result = service.arm_motion_approval(
            session_id,
            plan,
            approved_by=approved_by,
            fixture_qc_record=fixture_qc_record,
            target_class_records=list(target_class_records or []),
            safety_profile=safety_profile,
            expires_in_seconds=expires_in_seconds,
        )
    except (BridgeServiceError, sqlite3.Error, OSError, ValueError) as exc:
        report.blockers.append(f"arm failed: {exc}")
        report.steps.append(
            CommissioningStep(
                name="arm_motion_approval",
                phase="arm",
                status="error",
                detail="arm_motion_approval raised",
                blockers=[str(exc)],
            )
        )
        return False

    report.arm_result = arm_result
    if not arm_result.armed or arm_result.approval is None:
        report.blockers.extend(arm_result.blockers)
        report.steps.append(
            CommissioningStep(
                name="arm_motion_approval",
                phase="arm",
                status="blocked",
                detail="bridge refused to arm motion approval",
                blockers=list(arm_result.blockers),
            )
        )
        return False

    report.armed = True
    report.approval_id = arm_result.approval.approval_id
    report.steps.append(
        CommissioningStep(
            name="arm_motion_approval",
            phase="arm",
            status="armed",
            detail=f"bridge armed motion approval {arm_result.approval.approval_id}",
        )
    )
    return True


def _execute_gate_open(report: CommissioningReport, *, confirm_execute: bool) -> bool:
    if confirm_execute:
        return True
    report.steps.append(
        CommissioningStep(
            name="execute_next",
            phase="execute",
            status="would_execute",
            detail="would execute the approved motion step (confirm_execute not set)",
        )
    )
    return False


def _execute(
    service: BridgeService,
    session_id: str,
    plan: PlanFragment,
    report: CommissioningReport,
    *,
    safety_profile: FixtureSafetyProfile | None,
    fixture_qc_record: str | None,
    target_class_records: list[str] | None,
) -> bool:
    approval = report.arm_result.approval if report.arm_result is not None else None
    if approval is None:
        # Defensive: never reach execute without a bridge-minted approval.
        report.blockers.append("cannot execute without an armed motion approval")
        report.steps.append(
            CommissioningStep(
                name="execute_next",
                phase="execute",
                status="error",
                detail="no armed approval present at execute",
                blockers=["cannot execute without an armed motion approval"],
            )
        )
        return False
    try:
        execution = service.execute_next(
            session_id,
            plan,
            fixture_qc_record=fixture_qc_record,
            target_class_records=list(target_class_records or []),
            safety_profile=safety_profile,
            motion_approval=approval,
        )
    except (BridgeServiceError, sqlite3.Error, OSError, ValueError) as exc:
        report.blockers.append(f"execute failed: {exc}")
        report.steps.append(
            CommissioningStep(
                name="execute_next",
                phase="execute",
                status="error",
                detail="execute_next raised",
                blockers=[str(exc)],
            )
        )
        return False

    report.execution = execution
    report.motion_commands_sent = execution.motion_commands_sent
    if not execution.executed:
        report.blockers.extend(execution.validation.reasons)
        report.steps.append(
            CommissioningStep(
                name="execute_next",
                phase="execute",
                status="blocked",
                detail="bridge did not execute the motion step",
                blockers=list(execution.validation.reasons),
            )
        )
        return False

    report.executed = True
    report.steps.append(
        CommissioningStep(
            name="execute_next",
            phase="execute",
            status="executed",
            detail=(
                "bridge executed the approved step; "
                f"motion_commands_sent={execution.motion_commands_sent}"
            ),
        )
    )
    return True
