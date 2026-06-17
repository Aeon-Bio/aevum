from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from aevum_ot2.core.plans import PlanFragment, PlanOperation, PlanStep, step_requires_motion
from aevum_ot2.core.validation import PlanValidationResult, StepValidationResult

StepExecutionStatus = Literal["succeeded", "blocked", "failed", "not_implemented", "skipped"]


class StepExecutionResult(BaseModel):
    step_id: str
    operation: PlanOperation
    status: StepExecutionStatus
    requires_motion: bool
    validation_allowed: bool
    detail: str
    payload: dict[str, Any] = Field(default_factory=dict)


class PlanExecutionResult(BaseModel):
    session_id: str
    plan_step_count: int
    executed_step_id: str | None = None
    executed: bool = False
    motion_commands_sent: bool = False
    validation: PlanValidationResult
    steps: list[StepExecutionResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def blocked_execution_result(
    plan: PlanFragment,
    validation: PlanValidationResult,
) -> PlanExecutionResult:
    return PlanExecutionResult(
        session_id=validation.session_id,
        plan_step_count=len(plan.steps),
        validation=validation,
        steps=[
            _step_result(
                step,
                _validation_for_step(validation, step),
                status="blocked",
                detail="plan validation blocked execution",
            )
            for step in plan.steps
        ],
        notes=["No operation executed because plan validation failed."],
    )


def skipped_empty_plan_result(
    plan: PlanFragment,
    validation: PlanValidationResult,
) -> PlanExecutionResult:
    return PlanExecutionResult(
        session_id=validation.session_id,
        plan_step_count=len(plan.steps),
        validation=validation,
        notes=["No operation executed because the plan has no steps."],
    )


def motion_not_implemented_result(
    plan: PlanFragment,
    validation: PlanValidationResult,
    step: PlanStep,
    *,
    payload: dict[str, Any] | None = None,
    notes: list[str] | None = None,
) -> PlanExecutionResult:
    step_validation = _validation_for_step(validation, step)
    return PlanExecutionResult(
        session_id=validation.session_id,
        plan_step_count=len(plan.steps),
        validation=validation,
        steps=[
            _step_result(
                step,
                step_validation,
                status="not_implemented",
                detail="motion execution backend is not implemented; no robot command was sent",
                payload=payload or {},
            )
        ],
        notes=notes or [
            "Motion remains unavailable in the current daemon execution boundary."
        ],
    )


def succeeded_step_result(
    plan: PlanFragment,
    validation: PlanValidationResult,
    step: PlanStep,
    *,
    detail: str,
    payload: dict[str, Any] | None = None,
) -> PlanExecutionResult:
    return PlanExecutionResult(
        session_id=validation.session_id,
        plan_step_count=len(plan.steps),
        executed_step_id=step.step_id,
        executed=True,
        validation=validation,
        steps=[
            _step_result(
                step,
                _validation_for_step(validation, step),
                status="succeeded",
                detail=detail,
                payload=payload or {},
            )
        ],
    )


def failed_step_result(
    plan: PlanFragment,
    validation: PlanValidationResult,
    step: PlanStep,
    *,
    detail: str,
    payload: dict[str, Any] | None = None,
) -> PlanExecutionResult:
    return PlanExecutionResult(
        session_id=validation.session_id,
        plan_step_count=len(plan.steps),
        validation=validation,
        steps=[
            _step_result(
                step,
                _validation_for_step(validation, step),
                status="failed",
                detail=detail,
                payload=payload or {},
            )
        ],
    )


def not_implemented_step_result(
    plan: PlanFragment,
    validation: PlanValidationResult,
    step: PlanStep,
    *,
    detail: str,
) -> PlanExecutionResult:
    return PlanExecutionResult(
        session_id=validation.session_id,
        plan_step_count=len(plan.steps),
        executed_step_id=step.step_id,
        validation=validation,
        steps=[
            _step_result(
                step,
                _validation_for_step(validation, step),
                status="not_implemented",
                detail=detail,
            )
        ],
    )


def _step_result(
    step: PlanStep,
    step_validation: StepValidationResult | None,
    *,
    status: StepExecutionStatus,
    detail: str,
    payload: dict[str, Any] | None = None,
) -> StepExecutionResult:
    return StepExecutionResult(
        step_id=step.step_id,
        operation=step.operation,
        status=status,
        requires_motion=step_requires_motion(step),
        validation_allowed=bool(step_validation and step_validation.allowed),
        detail=detail,
        payload=payload or {},
    )


def _validation_for_step(
    validation: PlanValidationResult,
    step: PlanStep,
) -> StepValidationResult | None:
    for step_validation in validation.steps:
        if step_validation.step_id == step.step_id:
            return step_validation
    return None
