from __future__ import annotations

import pytest
from pydantic import ValidationError

from aevum_ot2.core.plans import (
    CaptureEvidenceParameters,
    PlanFragment,
    PlanStep,
    allowed_parameter_keys,
    canonicalize_plan_fragment,
    operation_category,
    parse_plan_fragment,
    parse_step_parameters,
)


def test_capture_observation_legacy_name_maps_to_capture_evidence() -> None:
    step = PlanStep(
        step_id="observe",
        operation="capture_observation",
        parameters={"filename": "fixture.jpg", "timeout_seconds": 3},
    )

    assert step.operation == "capture_evidence"
    assert step.model_dump(mode="json")["operation"] == "capture_evidence"
    assert isinstance(parse_step_parameters(step), CaptureEvidenceParameters)


def test_plan_fragment_parser_uses_same_operation_shim() -> None:
    plan = parse_plan_fragment(
        {
            "schema_version": 1,
            "session_id": "session-1",
            "steps": [{"step_id": "observe", "operation": "capture_observation"}],
        }
    )

    assert plan.steps[0].operation == "capture_evidence"


def test_operation_categories_and_parameter_keys_are_explicit() -> None:
    assert operation_category("inspect_context") == "context"
    assert operation_category("capture_evidence") == "evidence"
    assert operation_category("prepare_registration_plan") == "gate"
    assert operation_category("close_session") == "session"
    assert operation_category("move_high_z") == "motion"
    assert allowed_parameter_keys("capture_evidence") == {"filename", "timeout_seconds"}
    assert allowed_parameter_keys("move_low_z") == set()


@pytest.mark.parametrize(
    ("operation", "parameters"),
    [
        ("home", {"x": 1, "y": 2, "z": 3}),
        ("move_high_z", {"coordinates": {"x": 1, "y": 2, "z": 3}}),
        ("move_low_z", {"offset_mm": {"x": 0.1, "y": 0.0, "z": -1.0}}),
        ("liquid_handling", {"command": {"commandType": "aspirate"}}),
        ("capture_evidence", {"endpoint": "/commands"}),
        ("inspect_context", {"python": "import opentrons"}),
    ],
)
def test_plan_parameters_cannot_smuggle_coordinates_http_or_python(
    operation: str,
    parameters: dict[str, object],
) -> None:
    with pytest.raises(ValidationError, match="unsupported parameters"):
        PlanStep(step_id="bad", operation=operation, parameters=parameters)


def test_capture_evidence_rejects_paths_and_bad_timeouts() -> None:
    with pytest.raises(ValidationError, match="basename"):
        PlanStep(
            step_id="bad-filename",
            operation="capture_evidence",
            parameters={"filename": "../fixture.jpg"},
        )
    with pytest.raises(ValidationError, match="positive number"):
        PlanStep(
            step_id="bad-timeout",
            operation="capture_evidence",
            parameters={"timeout_seconds": True},
        )


def test_record_evidence_payload_is_typed() -> None:
    step = PlanStep(
        step_id="record",
        operation="record_evidence",
        parameters={
            "evidence_id": "image-1",
            "source_kind": "camera_capture",
            "path": "data/measurements/images/fixture.jpg",
            "checksum_sha256": "A" * 64,
            "quality": "usable",
        },
    )

    assert step.parameters["checksum_sha256"] == "a" * 64


def test_record_evidence_rejects_path_escape_before_operation_is_unblocked() -> None:
    with pytest.raises(ValidationError, match="relative artifact path"):
        PlanStep(
            step_id="record",
            operation="record_evidence",
            parameters={
                "evidence_id": "image-1",
                "source_kind": "camera_capture",
                "path": "../fixture.jpg",
                "checksum_sha256": "a" * 64,
            },
        )


def test_canonicalize_plan_fragment_rejects_mutated_model_payloads() -> None:
    plan = PlanFragment(
        session_id="session-1",
        steps=[
            PlanStep(
                step_id="observe",
                operation="capture_evidence",
                parameters={"filename": "fixture.jpg"},
            )
        ],
    )
    plan.steps[0].parameters["filename"] = "../fixture.jpg"

    with pytest.raises(ValidationError, match="basename"):
        canonicalize_plan_fragment(plan)


def test_ignored_target_classes_and_extra_step_fields_fail_closed() -> None:
    with pytest.raises(ValidationError, match="does not accept target_class"):
        PlanStep(step_id="inspect", operation="inspect_context", target_class="center_high_z")
    with pytest.raises(ValidationError):
        PlanStep(step_id="home", operation="home", coordinates={"x": 1})
