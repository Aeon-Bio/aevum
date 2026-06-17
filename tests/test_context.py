from __future__ import annotations

from datetime import datetime, timedelta

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.context import build_session_context
from aevum_ot2.core.models import BridgeSession, EndpointResult, RobotStatus
from aevum_ot2.core.readiness import ReadinessResult
from aevum_ot2.core.records import RecordHandle


def _session(state: str = "ready_no_motion") -> BridgeSession:
    identity = current_fixture_identity()
    now = datetime.now()
    return BridgeSession(
        session_id="session-1",
        kind="registration",
        owner_id="agent-1",
        robot_url="http://ot2.local:31950",
        robot_serial="OT2TEST0001",
        robot_server_version="9.0.0",
        max_protocol_api_version="2.28",
        state=state,
        created_at=now,
        updated_at=now,
        lease_expires_at=now + timedelta(minutes=10),
        maintenance_run_id="maintenance-run-1",
        slot="1",
        fixture_identity=identity,
        definition_uri="aevum/aevum_p300_poc_fixture/1",
        loaded_labware_id="fixture-1",
        evidence_index_path="data/measurements/ot2_evidence_index.json",
    )


def _status() -> RobotStatus:
    return RobotStatus(
        robot_url="http://ot2.local:31950",
        checked_at=datetime.now(),
        health=EndpointResult(path="/health", ok=True, data={}),
        pipettes=EndpointResult(
            path="/pipettes",
            ok=True,
            data={
                "left": {
                    "model": "p300_single_v2.1",
                    "name": "p300_single_gen2",
                    "tip_length": 0.0,
                    "id": "P3HSV212021022403",
                },
                "right": {
                    "model": "p20_single_v2.2",
                    "name": "p20_single_gen2",
                    "tip_length": 0.0,
                    "id": "P20SV222021050621",
                },
            },
        ),
    )


def _readiness() -> ReadinessResult:
    qc_handle = RecordHandle(
        record_type="fixture_qc",
        path="data/measurements/fixture_qc.json",
        record_id="fixture-qc-1",
    )
    target_handle = RecordHandle(
        record_type="target_class_verification",
        path="data/measurements/target_classes/center_high_z.json",
        record_id="center_high_z:OT2TEST0001:slot-1:p300_single_gen2:left",
    )
    return ReadinessResult(
        session_id="session-1",
        registration_ready=True,
        fixture_qc_record=qc_handle,
        target_class_records=[target_handle],
    )


def test_build_session_context_includes_compact_session_state() -> None:
    context = build_session_context(
        _session(),
        readiness=_readiness(),
        robot_status=_status(),
    )

    assert context.session_id == "session-1"
    assert context.robot.robot_serial == "OT2TEST0001"
    assert [pipette.name for pipette in context.robot.pipettes] == [
        "p300_single_gen2",
        "p20_single_gen2",
    ]
    assert context.fixture.load_name == "aevum_p300_poc_fixture"
    assert context.readiness is not None
    assert context.readiness.registration_ready is True
    assert len(context.record_handles) == 2
    assert "capture_evidence" in context.allowed_next_ops
    assert "capture_observation" not in context.allowed_next_ops
    assert "run_readiness_check" not in context.allowed_next_ops
    assert "prepare_registration_plan" in context.allowed_next_ops
    assert context.motion_allowed is False
    assert any(block.operation == "move_low_z" for block in context.blocked_ops)
    assert any(block.operation == "record_evidence" for block in context.blocked_ops)


def test_build_session_context_reads_nested_live_pipette_data() -> None:
    status = _status().model_copy(
        update={
            "pipettes": EndpointResult(
                path="/pipettes",
                ok=True,
                data={"data": _status().pipettes.data},
            )
        }
    )

    context = build_session_context(_session(), robot_status=status)

    assert [pipette.name for pipette in context.robot.pipettes] == [
        "p300_single_gen2",
        "p20_single_gen2",
    ]


def test_context_blocks_plan_preparation_without_readiness() -> None:
    context = build_session_context(_session())

    assert "prepare_registration_plan" not in context.allowed_next_ops
    assert any(
        block.operation == "prepare_registration_plan"
        and "readiness has not been evaluated" in block.reason
        for block in context.blocked_ops
    )


def test_context_blocks_plan_preparation_for_non_ready_session() -> None:
    context = build_session_context(_session(state="closed"), readiness=_readiness())

    assert context.allowed_next_ops == ["inspect_context"]
    assert "prepare_registration_plan" not in context.allowed_next_ops
    assert any(
        block.operation == "prepare_registration_plan"
        and "not ready_no_motion" in block.reason
        for block in context.blocked_ops
    )
