from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from aevum_ot2.core.camera import capture_picture
from aevum_ot2.core.client import Ot2Client
from aevum_ot2.core.context import SessionContext, build_session_context
from aevum_ot2.core.dispatch_preparation import (
    build_motion_dispatch_preparation_for_approval,
)
from aevum_ot2.core.evidence_primitives import EVIDENCE_TRANSACTIONS_DIRNAME
from aevum_ot2.core.execution import (
    PlanExecutionResult,
    blocked_execution_result,
    failed_step_result,
    motion_not_implemented_result,
    not_implemented_step_result,
    skipped_empty_plan_result,
    succeeded_step_result,
)
from aevum_ot2.core.lock import read_lock
from aevum_ot2.core.models import (
    BridgeSession,
    EndpointResult,
    EvidenceClaim,
    NoMotionSessionCloseReport,
    NoMotionSessionInitReport,
    OffsetRegistry,
)
from aevum_ot2.core.motion_approval import MOTION_APPROVAL_MAX_TTL, MotionApproval
from aevum_ot2.core.motion_backend import dispatch_prepared_motion_command
from aevum_ot2.core.motion_commissioning import (
    MotionApprovalArmResult,
    arm_motion_commissioning,
    consume_motion_approval,
    read_motion_approval_record,
)
from aevum_ot2.core.plans import (
    PlanFragment,
    PlanStep,
    canonicalize_plan_fragment,
    step_requires_motion,
)
from aevum_ot2.core.pose import FixturePose
from aevum_ot2.core.readiness import ReadinessResult, evaluate_registration_readiness
from aevum_ot2.core.records import (
    TargetClassVerificationRecord,
    load_target_class_record,
)
from aevum_ot2.core.recovery import (
    NoMotionRecoveryDisposition,
    NoMotionRecoveryReport,
    recover_no_motion_session,
)
from aevum_ot2.core.revalidation import ExecuteRevalidationResult, revalidate_motion_execution
from aevum_ot2.core.safety import FixtureSafetyProfile
from aevum_ot2.core.sessions import (
    DEFAULT_SESSION_DB,
    close_no_motion_session,
    initialize_no_motion_session,
    list_sessions,
    read_session,
)
from aevum_ot2.core.validation import PlanValidationResult, validate_plan_fragment

MOTION_BACKEND_TIMEOUT_SECONDS = 70.0


class BridgeServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class BridgeServiceHealth(BaseModel):
    ok: bool = True
    service: str = "aevum-ot2-daemon"
    state_db_path: str
    motion_enabled: bool = False
    motion_backend_enabled: bool = False
    supported_operations: list[str] = Field(
        default_factory=lambda: [
            "health",
            "list_sessions",
            "get_session_context",
            "validate_plan",
            "execute_next",
            "arm_motion_approval",
            "start_no_motion_session",
            "close_no_motion_session",
            "recover_no_motion_session",
        ]
    )


class BridgeService:
    """Workflow-level daemon service API over the bridge core."""

    def __init__(
        self,
        *,
        state_db_path: str | Path = DEFAULT_SESSION_DB,
        motion_enabled: bool = False,
        motion_backend_enabled: bool = False,
    ) -> None:
        if motion_backend_enabled and not motion_enabled:
            raise ValueError("motion_backend_enabled requires motion_enabled")
        self.state_db_path = Path(state_db_path)
        self.motion_enabled = motion_enabled
        self.motion_backend_enabled = motion_backend_enabled

    def health(self) -> BridgeServiceHealth:
        return BridgeServiceHealth(
            state_db_path=str(self.state_db_path),
            motion_enabled=self.motion_enabled,
            motion_backend_enabled=self.motion_backend_enabled,
        )

    def list_sessions(
        self,
        *,
        robot_url: str | None = None,
        state: str | None = None,
    ) -> list[BridgeSession]:
        return list_sessions(self.state_db_path, robot_url=robot_url, state=state)

    def get_session(self, session_id: str) -> BridgeSession:
        session = read_session(session_id, self.state_db_path)
        if session is None:
            raise BridgeServiceError(404, "session_not_found", f"session not found: {session_id}")
        return session

    def get_session_context(
        self,
        session_id: str,
        *,
        fixture_qc_record: str | Path | None = None,
        target_class_records: list[str | Path] | None = None,
    ) -> SessionContext:
        session = self.get_session(session_id)
        readiness = self._evaluate_readiness_if_requested(
            session,
            fixture_qc_record=fixture_qc_record,
            target_class_records=target_class_records or [],
        )
        return build_session_context(session, readiness=readiness)

    def validate_plan(
        self,
        session_id: str,
        plan: PlanFragment,
        *,
        fixture_qc_record: str | Path | None = None,
        target_class_records: list[str | Path] | None = None,
        offset_registry: OffsetRegistry | None = None,
        safety_profile: FixtureSafetyProfile | None = None,
        fixture_pose: FixturePose | None = None,
        pose_claims: list[EvidenceClaim] | None = None,
        recovery_disposition: NoMotionRecoveryDisposition | str | None = None,
        motion_approval: MotionApproval | None = None,
    ) -> PlanValidationResult:
        plan = canonicalize_plan_fragment(plan)
        session = self.get_session(session_id)
        readiness = self._evaluate_readiness_if_requested(
            session,
            fixture_qc_record=fixture_qc_record,
            target_class_records=target_class_records or [],
        )
        target_records = self._load_target_records(target_class_records or [])
        validation = validate_plan_fragment(
            plan,
            session,
            readiness=readiness,
            target_records=target_records,
            offset_registry=offset_registry,
            safety_profile=safety_profile,
            fixture_pose=fixture_pose,
            pose_claims=pose_claims,
            recovery_disposition=recovery_disposition,
            daemon_motion_enabled=self.motion_enabled,
            motion_approval=motion_approval,
        )
        if motion_approval is None:
            return validation
        return _validation_with_motion_approval_record(
            validation,
            motion_approval=motion_approval,
            state_db_path=self.state_db_path,
        )

    def execute_next(
        self,
        session_id: str,
        plan: PlanFragment,
        *,
        fixture_qc_record: str | Path | None = None,
        target_class_records: list[str | Path] | None = None,
        offset_registry: OffsetRegistry | None = None,
        safety_profile: FixtureSafetyProfile | None = None,
        fixture_pose: FixturePose | None = None,
        pose_claims: list[EvidenceClaim] | None = None,
        recovery_disposition: NoMotionRecoveryDisposition | str | None = None,
        motion_approval: MotionApproval | None = None,
    ) -> PlanExecutionResult:
        plan = canonicalize_plan_fragment(plan)
        session = self.get_session(session_id)
        validation = self.validate_plan(
            session_id,
            plan,
            fixture_qc_record=fixture_qc_record,
            target_class_records=target_class_records,
            offset_registry=offset_registry,
            safety_profile=safety_profile,
            fixture_pose=fixture_pose,
            pose_claims=pose_claims,
            recovery_disposition=recovery_disposition,
            motion_approval=motion_approval,
        )
        if not plan.steps:
            return skipped_empty_plan_result(plan, validation)
        if not validation.allowed:
            return blocked_execution_result(plan, validation)

        session = self.get_session(session_id)
        step = plan.steps[0]
        if step_requires_motion(step):
            live_status = self._live_robot_status(session)
            revalidation = revalidate_motion_execution(
                session=session,
                plan=plan,
                validation=validation,
                step=step,
                lock=read_lock(session.robot_url, self.state_db_path),
                robot_status=live_status,
                motion_approval=motion_approval,
                safety_profile=safety_profile,
            )
            if not revalidation.passed:
                return blocked_execution_result(
                    plan,
                    _validation_with_execute_revalidation(
                        validation,
                        step_id=step.step_id,
                        revalidation=revalidation,
                    ),
                )
            if motion_approval is None:
                return blocked_execution_result(
                    plan,
                    _validation_with_execute_revalidation(
                        validation,
                        step_id=step.step_id,
                        revalidation=ExecuteRevalidationResult(
                            passed=False,
                            missing_claims=["motion_approval"],
                        ),
                    ),
                )
            record_blockers = _motion_approval_record_blockers(
                motion_approval,
                state_db_path=self.state_db_path,
            )
            if record_blockers:
                return blocked_execution_result(
                    plan,
                    _validation_with_execute_revalidation(
                        validation,
                        step_id=step.step_id,
                        revalidation=ExecuteRevalidationResult(
                            passed=False,
                            blockers=[
                                f"motion_approval: {blocker}"
                                for blocker in record_blockers
                            ],
                        ),
                    ),
                )
            run_result, command_history_result = self._live_motion_dispatch_readbacks(
                session
            )
            dispatch_preparation = build_motion_dispatch_preparation_for_approval(
                approval=motion_approval,
                session=session,
                plan=plan,
                safety_profile=safety_profile,
                run_result=run_result,
                command_history_result=command_history_result,
            )
            if (
                not dispatch_preparation.prepared
                or dispatch_preparation.preparation is None
            ):
                return blocked_execution_result(
                    plan,
                    _validation_with_execute_revalidation(
                        validation,
                        step_id=step.step_id,
                        revalidation=ExecuteRevalidationResult(
                            passed=False,
                            blockers=[
                                f"motion_dispatch_preparation: {blocker}"
                                for blocker in dispatch_preparation.blockers
                            ],
                        ),
                    ),
                )
            consumption = consume_motion_approval(
                approval=motion_approval,
                plan=plan,
                safety_profile=safety_profile,
                dispatch_preparation=dispatch_preparation.preparation,
                path=self.state_db_path,
            )
            if not consumption.consumed:
                return blocked_execution_result(
                    plan,
                    _validation_with_execute_revalidation(
                        validation,
                        step_id=step.step_id,
                        revalidation=ExecuteRevalidationResult(
                            passed=False,
                            blockers=[
                                f"motion_approval_consumption: {blocker}"
                                for blocker in consumption.blockers
                            ],
                        ),
                    ),
                )
            payload: dict[str, Any] = {}
            reservation_id = ""
            if consumption.dispatch_reservation is not None:
                reservation_id = consumption.dispatch_reservation.reservation_id
                payload["dispatch_reservation"] = (
                    consumption.dispatch_reservation.model_dump(mode="json")
                )
            if consumption.dispatch_journal_entry is not None:
                payload["command_journal_entry"] = (
                    consumption.dispatch_journal_entry.model_dump(mode="json")
                )
                payload["dispatch_preparation"] = (
                    dispatch_preparation.preparation.model_dump(
                        mode="json",
                        exclude={"command_body"},
                    )
                )
            if self.motion_backend_enabled:
                if consumption.dispatch_reservation is None:
                    return _motion_backend_failed_result(
                        plan,
                        validation,
                        step,
                        payload=payload,
                        blockers=["motion backend missing dispatch reservation"],
                        motion_commands_sent=False,
                    )
                backend = dispatch_prepared_motion_command(
                    transport=self._live_motion_transport(session),
                    reservation=consumption.dispatch_reservation,
                    preparation=dispatch_preparation.preparation,
                    session=session,
                    plan=plan,
                    safety_profile=safety_profile,
                    state_db_path=self.state_db_path,
                )
                payload["motion_backend"] = backend.model_dump(
                    mode="json",
                    exclude={"preparation": {"command_body"}},
                )
                if backend.dispatched and backend.session_updated:
                    return succeeded_step_result(
                        plan,
                        validation,
                        step,
                        detail="dispatched and reconciled prepared motion command",
                        payload=payload,
                    ).model_copy(update={"motion_commands_sent": True})
                return _motion_backend_failed_result(
                    plan,
                    validation,
                    step,
                    payload=payload,
                    blockers=backend.blockers
                    or ["motion backend dispatch did not complete"],
                    motion_commands_sent=backend.motion_commands_sent,
                )

            notes = [
                (
                    "Motion dispatch was reserved and journal-prepared, but the "
                    "physical backend is disabled."
                ),
                "No robot command was sent.",
            ]
            post_consumption_validation = _validation_with_motion_approval_blockers(
                validation,
                blockers=[
                    "motion_approval: consumed by pre-dispatch reservation"
                    + (f" {reservation_id}" if reservation_id else "")
                ],
            )
            return motion_not_implemented_result(
                plan,
                post_consumption_validation,
                step,
                payload=payload,
                notes=notes,
            )

        result = self._execute_no_motion_step(session, plan, validation, step)
        if len(plan.steps) > 1:
            result.notes.append("Executed only the first approved step.")
        return result

    def start_no_motion_session(
        self,
        robot_url: str,
        *,
        owner_id: str,
        kind: str = "registration",
        slot: str = "1",
        orientation: str = "canonical",
        pipette_mount: str = "left",
        labware_path: str | None = None,
        lease_minutes: int = 15,
        timeout_seconds: float = 10.0,
    ) -> NoMotionSessionInitReport:
        kwargs: dict[str, Any] = {
            "owner_id": owner_id,
            "kind": kind,
            "slot": slot,
            "orientation": orientation,
            "pipette_mount": pipette_mount,
            "lease_minutes": lease_minutes,
            "timeout_seconds": timeout_seconds,
            "state_db_path": self.state_db_path,
        }
        if labware_path is not None:
            kwargs["labware_path"] = labware_path
        return initialize_no_motion_session(robot_url, **kwargs)

    def arm_motion_approval(
        self,
        session_id: str,
        plan: PlanFragment,
        *,
        approved_by: str,
        fixture_qc_record: str | Path | None = None,
        target_class_records: list[str | Path] | None = None,
        offset_registry: OffsetRegistry | None = None,
        safety_profile: FixtureSafetyProfile | None = None,
        fixture_pose: FixturePose | None = None,
        pose_claims: list[EvidenceClaim] | None = None,
        recovery_disposition: NoMotionRecoveryDisposition | str | None = None,
        expires_in_seconds: int = 300,
    ) -> MotionApprovalArmResult:
        plan = canonicalize_plan_fragment(plan)
        validation = self.validate_plan(
            session_id,
            plan,
            fixture_qc_record=fixture_qc_record,
            target_class_records=target_class_records,
            offset_registry=offset_registry,
            safety_profile=safety_profile,
            fixture_pose=fixture_pose,
            pose_claims=pose_claims,
            recovery_disposition=recovery_disposition,
        )
        blockers: list[str] = []
        if not self.motion_enabled:
            blockers.append("motion approval arm requires a motion-capable daemon")
        if expires_in_seconds <= 0:
            blockers.append("expires_in_seconds must be positive")
        max_seconds = int(MOTION_APPROVAL_MAX_TTL.total_seconds())
        if expires_in_seconds > max_seconds:
            blockers.append(f"expires_in_seconds must be <= {max_seconds}")
        if blockers:
            return MotionApprovalArmResult(
                session_id=session_id,
                validation=validation,
                blockers=blockers,
            )
        return arm_motion_commissioning(
            session_id=session_id,
            plan=plan,
            validation=validation,
            safety_profile=safety_profile,
            approved_by=approved_by,
            path=self.state_db_path,
            expires_in=timedelta(seconds=expires_in_seconds),
        )

    def close_no_motion_session(
        self,
        session_id: str,
        *,
        timeout_seconds: float = 10.0,
    ) -> NoMotionSessionCloseReport:
        return close_no_motion_session(
            session_id,
            timeout_seconds=timeout_seconds,
            state_db_path=self.state_db_path,
        )

    def recover_no_motion_session(
        self,
        session_id: str,
        *,
        timeout_seconds: float = 10.0,
    ) -> NoMotionRecoveryReport:
        return recover_no_motion_session(
            session_id,
            timeout_seconds=timeout_seconds,
            state_db_path=self.state_db_path,
        )

    def _execute_no_motion_step(
        self,
        session: BridgeSession,
        plan: PlanFragment,
        validation: PlanValidationResult,
        step: PlanStep,
    ) -> PlanExecutionResult:
        if step.operation == "inspect_context":
            context = self.get_session_context(session.session_id)
            return succeeded_step_result(
                plan,
                validation,
                step,
                detail="returned compact session context",
                payload={"context": context.model_dump(mode="json")},
            )
        if step.operation == "prepare_registration_plan":
            return succeeded_step_result(
                plan,
                validation,
                step,
                detail="prepared registration plan handoff without sending motion",
                payload={
                    "prepared": True,
                    "first_motion_operation": "home",
                    "motion_commands_sent": False,
                },
            )
        if step.operation == "capture_evidence":
            try:
                capture = capture_picture(
                    session.robot_url,
                    output_dir="data/measurements/images",
                    filename=_step_string(step, "filename"),
                    timeout_seconds=_step_float(step, "timeout_seconds") or 20.0,
                    record_evidence=True,
                    evidence_index_path=session.evidence_index_path,
                    session_id=session.session_id,
                )
            except (RuntimeError, ValueError) as exc:
                return failed_step_result(
                    plan,
                    validation,
                    step,
                    detail=f"camera evidence capture failed: {exc}",
                )
            return succeeded_step_result(
                plan,
                validation,
                step,
                detail="captured no-motion camera evidence",
                payload={"capture": capture.model_dump(mode="json")},
            )
        if step.operation == "close_session":
            report = self.close_no_motion_session(
                session.session_id,
                timeout_seconds=_step_float(step, "timeout_seconds") or 10.0,
            )
            return succeeded_step_result(
                plan,
                validation,
                step,
                detail="closed no-motion session",
                payload={"close_report": report.model_dump(mode="json")},
            )
        return not_implemented_step_result(
            plan,
            validation,
            step,
            detail=f"no-motion execution is not implemented for {step.operation}",
        )

    def _evaluate_readiness_if_requested(
        self,
        session: BridgeSession,
        *,
        fixture_qc_record: str | Path | None,
        target_class_records: list[str | Path],
    ) -> ReadinessResult | None:
        if fixture_qc_record is None:
            return None
        return evaluate_registration_readiness(
            session,
            fixture_qc_record=fixture_qc_record,
            target_class_records=target_class_records,
            evidence_transaction_root=self.state_db_path.parent / EVIDENCE_TRANSACTIONS_DIRNAME,
        )

    def _load_target_records(
        self,
        target_class_records: list[str | Path],
    ) -> list[TargetClassVerificationRecord]:
        records: list[TargetClassVerificationRecord] = []
        for path in target_class_records:
            try:
                records.append(load_target_class_record(path))
            except OSError as exc:
                raise BridgeServiceError(
                    400,
                    "target_record_unreadable",
                    f"target-class record could not be read: {path}: {exc}",
                ) from exc
        return records

    def _live_robot_status(self, session: BridgeSession):
        return Ot2Client(session.robot_url).status()

    def _live_motion_dispatch_readbacks(
        self,
        session: BridgeSession,
    ) -> tuple[EndpointResult, EndpointResult]:
        client = self._live_motion_transport(session)
        run_id = session.maintenance_run_id or ""
        run_path = f"/maintenance_runs/{run_id}"
        return (
            client.get_json(run_path),
            client.get_json(f"{run_path}/commands?pageLength=1000"),
        )

    def _live_motion_transport(self, session: BridgeSession):
        return Ot2Client(session.robot_url, timeout_seconds=MOTION_BACKEND_TIMEOUT_SECONDS)


def _step_string(step: PlanStep, key: str) -> str | None:
    value = step.parameters.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise BridgeServiceError(
            400,
            "bad_step_parameter",
            f"{step.step_id}.{key} must be a string",
        )
    return value


def _step_float(step: PlanStep, key: str) -> float | None:
    value = step.parameters.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise BridgeServiceError(
            400,
            "bad_step_parameter",
            f"{step.step_id}.{key} must be a number",
        )
    return float(value)


def _motion_backend_failed_result(
    plan: PlanFragment,
    validation: PlanValidationResult,
    step: PlanStep,
    *,
    payload: dict[str, Any],
    blockers: list[str],
    motion_commands_sent: bool,
) -> PlanExecutionResult:
    payload = {
        **payload,
        "motion_backend_blockers": blockers,
    }
    result = failed_step_result(
        plan,
        validation,
        step,
        detail="motion backend dispatch did not complete cleanly",
        payload=payload,
    )
    return result.model_copy(
        update={
            "motion_commands_sent": motion_commands_sent,
            "notes": [
                (
                    "A robot command POST was sent; recovery review is required."
                    if motion_commands_sent
                    else "No robot command was sent by the motion backend."
                )
            ],
        }
    )


def _validation_with_execute_revalidation(
    validation: PlanValidationResult,
    *,
    step_id: str,
    revalidation: ExecuteRevalidationResult,
) -> PlanValidationResult:
    revalidation_reasons = [
        *(f"missing execute-time input: {claim}" for claim in revalidation.missing_claims),
        *revalidation.blockers,
    ]
    prefixed_reasons = [f"{step_id}: {reason}" for reason in revalidation_reasons]
    steps = []
    for step in validation.steps:
        if step.step_id != step_id:
            steps.append(step)
            continue
        steps.append(
            step.model_copy(
                update={
                    "allowed": False,
                    "reasons": [*step.reasons, *revalidation_reasons],
                }
            )
        )
    return validation.model_copy(
        update={
            "allowed": False,
            "motion_allowed": False,
            "reasons": [*validation.reasons, *prefixed_reasons],
            "steps": steps,
        }
    )


def _validation_with_motion_approval_record(
    validation: PlanValidationResult,
    *,
    motion_approval: MotionApproval,
    state_db_path: Path,
) -> PlanValidationResult:
    blockers = _motion_approval_record_blockers(
        motion_approval,
        state_db_path=state_db_path,
    )
    if not blockers:
        return validation
    return _validation_with_motion_approval_blockers(
        validation,
        blockers=[f"motion_approval: {blocker}" for blocker in blockers],
    )


def _motion_approval_record_blockers(
    motion_approval: MotionApproval,
    *,
    state_db_path: Path,
) -> list[str]:
    record = read_motion_approval_record(motion_approval.approval_id, state_db_path)
    blockers: list[str] = []
    if record is None:
        blockers.append("motion approval record not found")
    elif record.approval != motion_approval:
        blockers.append("motion approval does not match persisted record")
    elif record.state != "armed":
        blockers.append(f"motion approval is not armed: {record.state}")
    return blockers


def _validation_with_motion_approval_blockers(
    validation: PlanValidationResult,
    *,
    blockers: list[str],
) -> PlanValidationResult:
    steps = []
    for step in validation.steps:
        if not step.requires_motion:
            steps.append(step)
            continue
        steps.append(
            step.model_copy(
                update={
                    "allowed": False,
                    "reasons": [*step.reasons, *blockers],
                }
            )
        )
    return validation.model_copy(
        update={
            "allowed": False,
            "motion_allowed": False,
            "reasons": [*validation.reasons, *blockers],
            "steps": steps,
        }
    )
