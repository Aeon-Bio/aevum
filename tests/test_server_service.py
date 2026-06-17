from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

import aevum_ot2.server.service as service_module
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.models import BridgeSession, CameraCaptureResult
from aevum_ot2.core.plans import PlanFragment, PlanStep
from aevum_ot2.core.sessions import write_session
from aevum_ot2.server.service import BridgeService, BridgeServiceError


def _session(session_id: str = "session-1", state: str = "ready_no_motion") -> BridgeSession:
    identity = current_fixture_identity()
    now = datetime.now()
    return BridgeSession(
        session_id=session_id,
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


def test_bridge_service_health_and_session_context(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    service = BridgeService(state_db_path=db_path)

    health = service.health()
    context = service.get_session_context(session.session_id)

    assert health.ok is True
    assert health.motion_enabled is False
    assert context.session_id == session.session_id
    assert context.motion_allowed is False
    assert any(block.operation == "home" for block in context.blocked_ops)


def test_bridge_service_backend_flag_requires_motion_flag(tmp_path) -> None:
    with pytest.raises(ValueError, match="motion_backend_enabled requires motion_enabled"):
        BridgeService(
            state_db_path=tmp_path / "state.sqlite3",
            motion_backend_enabled=True,
        )


def test_bridge_service_lists_sessions_by_state(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    write_session(_session("ready"), db_path)
    write_session(_session("closed", state="closed"), db_path)
    service = BridgeService(state_db_path=db_path)

    sessions = service.list_sessions(state="ready_no_motion")

    assert [session.session_id for session in sessions] == ["ready"]


def test_bridge_service_validate_plan_uses_core_validation(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    service = BridgeService(state_db_path=db_path)

    result = service.validate_plan(
        session.session_id,
        PlanFragment(
            session_id=session.session_id,
            steps=[PlanStep(step_id="home", operation="home")],
        ),
    )

    assert result.allowed is False
    assert result.motion_allowed is False
    assert "registration readiness has not been evaluated" in " ".join(result.reasons)


def test_bridge_service_execute_next_returns_context(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    service = BridgeService(state_db_path=db_path)

    result = service.execute_next(
        session.session_id,
        PlanFragment(
            session_id=session.session_id,
            steps=[PlanStep(step_id="inspect", operation="inspect_context")],
        ),
    )

    assert result.executed is True
    assert result.motion_commands_sent is False
    assert result.steps[0].status == "succeeded"
    assert result.steps[0].payload["context"]["session_id"] == session.session_id


def test_bridge_service_execute_next_blocks_motion_without_backend(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    service = BridgeService(state_db_path=db_path)

    result = service.execute_next(
        session.session_id,
        PlanFragment(
            session_id=session.session_id,
            steps=[PlanStep(step_id="home", operation="home")],
        ),
    )

    assert result.executed is False
    assert result.motion_commands_sent is False
    assert result.steps[0].status == "blocked"
    assert "motion-capable bridge daemon" in " ".join(result.validation.reasons)


def test_bridge_service_execute_next_captures_observation(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    service = BridgeService(state_db_path=db_path)

    def fake_capture_picture(
        robot_url: str,
        *,
        output_dir: str,
        filename: str | None,
        timeout_seconds: float,
        record_evidence: bool,
        evidence_index_path: str,
        session_id: str | None,
    ) -> CameraCaptureResult:
        assert robot_url == session.robot_url
        assert output_dir == "data/measurements/images"
        assert filename == "fixture.jpg"
        assert timeout_seconds == 3.0
        assert record_evidence is True
        assert evidence_index_path == session.evidence_index_path
        assert session_id == session.session_id
        return CameraCaptureResult(
            robot_url=robot_url,
            captured_at=datetime.now(),
            endpoint="/camera/picture",
            image_path=str(tmp_path / "images" / "fixture.jpg"),
            image_checksum_sha256="0" * 64,
            content_type="image/jpg",
            bytes_written=128,
        )

    monkeypatch.setattr(service_module, "capture_picture", fake_capture_picture)

    result = service.execute_next(
        session.session_id,
        PlanFragment(
            session_id=session.session_id,
            steps=[
                PlanStep(
                    step_id="observe",
                    operation="capture_observation",
                    parameters={
                        "filename": "fixture.jpg",
                        "timeout_seconds": 3,
                    },
                )
            ],
        ),
    )

    assert result.executed is True
    assert result.motion_commands_sent is False
    assert result.steps[0].operation == "capture_evidence"
    assert result.steps[0].payload["capture"]["bytes_written"] == 128


def test_bridge_service_execute_next_reparses_mutated_plan_objects(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    service = BridgeService(state_db_path=db_path)
    plan = PlanFragment(
        session_id=session.session_id,
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
        service.execute_next(session.session_id, plan)


def test_bridge_service_raises_typed_error_for_missing_session(tmp_path) -> None:
    service = BridgeService(state_db_path=tmp_path / "state.sqlite3")

    try:
        service.get_session("missing")
    except BridgeServiceError as exc:
        assert exc.status_code == 404
        assert exc.code == "session_not_found"
    else:
        raise AssertionError("expected BridgeServiceError")


def test_bridge_service_start_session_passes_orientation(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_initialize_no_motion_session(robot_url: str, **kwargs: object) -> object:
        captured["robot_url"] = robot_url
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        service_module,
        "initialize_no_motion_session",
        fake_initialize_no_motion_session,
    )

    service = BridgeService(state_db_path=tmp_path / "state.sqlite3")
    service.start_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        slot="5",
        orientation="rot180",
    )

    assert captured["robot_url"] == "http://ot2.local:31950"
    assert captured["orientation"] == "rot180"
