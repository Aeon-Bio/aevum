from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from aevum_ot2.core.schema import load_json_object, parse_versioned_json_model

PlanOperationCategory = Literal["context", "evidence", "gate", "session", "motion", "recovery"]

PlanOperation = Literal[
    "inspect_context",
    "capture_evidence",
    "record_evidence",
    "close_session",
    "prepare_registration_plan",
    "home",
    "move_high_z",
    "move_low_z",
    "liquid_handling",
    "set_offset",
]

EvidenceSourceKindValue = Literal[
    "generated_artifact",
    "robot_state",
    "command_response",
    "command_history",
    "camera_capture",
    "vision_analysis",
    "physical_measurement",
    "inspection_note",
    "offset_measurement",
]

EvidenceQualityValue = Literal["usable", "ambiguous", "failed", "legacy"]

PLAN_OPERATION_ALIASES: dict[str, PlanOperation] = {
    "capture_observation": "capture_evidence",
}

PLAN_OPERATION_CATEGORIES: dict[PlanOperation, PlanOperationCategory] = {
    "inspect_context": "context",
    "capture_evidence": "evidence",
    "record_evidence": "evidence",
    "close_session": "session",
    "prepare_registration_plan": "gate",
    "home": "motion",
    "move_high_z": "motion",
    "move_low_z": "motion",
    "liquid_handling": "motion",
    "set_offset": "motion",
}

MOTION_OPERATIONS = {
    "home",
    "move_high_z",
    "move_low_z",
    "liquid_handling",
    "set_offset",
}

TARGET_CLASS_OPERATIONS = {"move_high_z", "move_low_z", "liquid_handling"}

# Operations deliberately CLOSED (not merely unimplemented): they stay in the enum for
# completeness but have no validated path and are rejected fail-closed at every layer
# (context block, validation, dispatch, and the agent surface). `set_offset` is closed
# because a labware offset is an evidence-backed registry record applied at run SETUP via the
# Opentrons /labwareOffsets API -- and consumed by the OFFSET_AUTHORITY gate -- NOT a
# maintenance MOTION command, so there is no coherent command for a translator to emit.
# See decision_log.md (OT-2).
FORMALLY_CLOSED_OPERATIONS = frozenset({"set_offset"})


class _PlanParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyPlanParameters(_PlanParameters):
    pass


class CaptureEvidenceParameters(_PlanParameters):
    filename: str | None = None
    timeout_seconds: float | None = None

    @field_validator("filename", mode="before")
    @classmethod
    def _validate_filename(cls, value: object) -> str | None:
        filename = _optional_non_empty_string(value, "filename")
        if filename is None:
            return None
        if "/" in filename or "\\" in filename or filename in {".", ".."}:
            raise ValueError("filename must be a basename, not a path")
        return filename

    @field_validator("timeout_seconds", mode="before")
    @classmethod
    def _validate_timeout_seconds(cls, value: object) -> float | None:
        return _optional_positive_seconds(value, "timeout_seconds")


class RecordEvidenceParameters(_PlanParameters):
    evidence_id: str
    source_kind: EvidenceSourceKindValue
    path: str
    checksum_sha256: str
    quality: EvidenceQualityValue = "ambiguous"

    @field_validator("evidence_id", "path", mode="before")
    @classmethod
    def _validate_non_empty_string(cls, value: object, info: ValidationInfo) -> str:
        if info.field_name == "path":
            return _required_relative_artifact_path(value)
        return _required_non_empty_string(value, info.field_name)

    @field_validator("checksum_sha256", mode="before")
    @classmethod
    def _validate_checksum(cls, value: object) -> str:
        checksum = _required_non_empty_string(value, "checksum_sha256")
        if len(checksum) != 64 or not all(char in _HEX_DIGITS for char in checksum):
            raise ValueError("checksum_sha256 must be a 64-character hex digest")
        return checksum.lower()


class CloseSessionParameters(_PlanParameters):
    timeout_seconds: float | None = None

    @field_validator("timeout_seconds", mode="before")
    @classmethod
    def _validate_timeout_seconds(cls, value: object) -> float | None:
        return _optional_positive_seconds(value, "timeout_seconds")


PLAN_PARAMETER_MODELS: dict[PlanOperation, type[_PlanParameters]] = {
    "inspect_context": EmptyPlanParameters,
    "capture_evidence": CaptureEvidenceParameters,
    "record_evidence": RecordEvidenceParameters,
    "close_session": CloseSessionParameters,
    "prepare_registration_plan": EmptyPlanParameters,
    "home": EmptyPlanParameters,
    "move_high_z": EmptyPlanParameters,
    "move_low_z": EmptyPlanParameters,
    "liquid_handling": EmptyPlanParameters,
    "set_offset": EmptyPlanParameters,
}

_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
_MAX_TIMEOUT_SECONDS = 300.0


class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    operation: PlanOperation
    target_class: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""

    @model_validator(mode="before")
    @classmethod
    def _normalize_operation_aliases(cls, data: object) -> object:
        if not isinstance(data, Mapping):
            return data
        operation = data.get("operation")
        if not isinstance(operation, str):
            return data
        canonical = PLAN_OPERATION_ALIASES.get(operation)
        if canonical is None:
            return data
        normalized = dict(data)
        normalized["operation"] = canonical
        return normalized

    @field_validator("step_id", mode="before")
    @classmethod
    def _validate_step_id(cls, value: object) -> str:
        return _required_non_empty_string(value, "step_id")

    @field_validator("target_class", mode="before")
    @classmethod
    def _validate_target_class(cls, value: object) -> str | None:
        return _optional_non_empty_string(value, "target_class")

    @model_validator(mode="after")
    def _validate_step_payload(self) -> Self:
        unknown_parameters = sorted(set(self.parameters) - allowed_parameter_keys(self.operation))
        if unknown_parameters:
            raise ValueError(
                f"unsupported parameters for {self.operation}: "
                + ", ".join(unknown_parameters)
            )
        parameter_model = PLAN_PARAMETER_MODELS[self.operation].model_validate(self.parameters)
        self.parameters = parameter_model.model_dump(mode="json", exclude_none=True)

        if self.target_class is not None and self.operation not in TARGET_CLASS_OPERATIONS:
            raise ValueError(f"{self.operation} does not accept target_class")
        return self


class PlanFragment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    session_id: str
    steps: list[PlanStep] = Field(default_factory=list)


def parse_plan_fragment(
    data: Mapping[str, Any],
    *,
    path: str | Path | None = None,
) -> PlanFragment:
    return parse_versioned_json_model(
        data,
        PlanFragment,
        schema_name="PlanFragment",
        path=path,
    )


def load_plan_fragment(path: str | Path) -> PlanFragment:
    data = load_json_object(path, schema_name="PlanFragment")
    return parse_plan_fragment(data, path=path)


def canonicalize_plan_fragment(plan: PlanFragment) -> PlanFragment:
    return parse_plan_fragment(plan.model_dump(mode="json"))


def canonical_operation(operation: str) -> str:
    return PLAN_OPERATION_ALIASES.get(operation, operation)


def operation_category(operation: PlanOperation) -> PlanOperationCategory:
    return PLAN_OPERATION_CATEGORIES[operation]


def allowed_parameter_keys(operation: PlanOperation) -> set[str]:
    return set(PLAN_PARAMETER_MODELS[operation].model_fields)


def parse_step_parameters(step: PlanStep) -> _PlanParameters:
    return PLAN_PARAMETER_MODELS[step.operation].model_validate(step.parameters)


def step_requires_motion(step: PlanStep) -> bool:
    return step.operation in MOTION_OPERATIONS


def _required_non_empty_string(value: object, field_name: str | None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name or 'field'} must be a non-empty string")
    return value


def _optional_non_empty_string(value: object, field_name: str | None) -> str | None:
    if value is None:
        return None
    return _required_non_empty_string(value, field_name)


def _required_relative_artifact_path(value: object) -> str:
    path = _required_non_empty_string(value, "path")
    if "\\" in path or path.startswith("/"):
        raise ValueError("path must be a relative artifact path")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("path must be a relative artifact path")
    return path


def _optional_positive_seconds(value: object, field_name: str | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name or 'timeout'} must be a positive number")
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0 or seconds > _MAX_TIMEOUT_SECONDS:
        raise ValueError(
            f"{field_name or 'timeout'} must be greater than 0 and no more than "
            f"{_MAX_TIMEOUT_SECONDS:g}"
        )
    return seconds
