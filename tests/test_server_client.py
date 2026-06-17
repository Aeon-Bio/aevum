from __future__ import annotations

from datetime import datetime, timedelta
from threading import Thread

from aevum_cad.labware import build_labware_definition
from aevum_cad.params import load_params
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.models import BridgeSession, EvidenceClaim, EvidenceQuality, OffsetRegistry
from aevum_ot2.core.motion_commissioning import MotionApprovalArmResult
from aevum_ot2.core.plans import PlanFragment, PlanStep
from aevum_ot2.core.pose import (
    POSE_UPRIGHT_CLAIM,
    FixtureOrientation,
    fixture_pose_from_labware_definition,
)
from aevum_ot2.core.safety import (
    BoundaryTargetHandling,
    FixtureSafetyProfile,
    MeasuredFixtureBounds,
)
from aevum_ot2.core.sessions import write_session
from aevum_ot2.core.validation import PlanValidationResult
from aevum_ot2.server.app import create_server
from aevum_ot2.server.client import DaemonClient, DaemonClientError


def _session(session_id: str = "session-1") -> BridgeSession:
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
        state="ready_no_motion",
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


def _safety_profile() -> FixtureSafetyProfile:
    identity = current_fixture_identity()
    bounds = MeasuredFixtureBounds(x_mm=127.76, y_mm=85.48, z_mm=20.0)
    return FixtureSafetyProfile(
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        params_path=identity.params_path,
        labware_path=identity.labware_path,
        nominal_dimensions_mm=identity.nominal_dimensions_mm,
        labware_dimensions_mm=identity.labware_dimensions_mm,
        measured_bounds_mm=bounds,
        conservative_bounds_mm=bounds,
        conservative_high_z_mm=20.0,
        dry_z_floor_mm=0.0,
        wet_z_floor_mm=0.0,
        max_registration_jog_mm=0.5,
        boundary_handling=BoundaryTargetHandling(),
        target_policy_digest_sha256="0" * 64,
        safety_profile_sha256="1" * 64,
    )


def _fixture_pose():
    return fixture_pose_from_labware_definition(
        current_fixture_identity(),
        slot="5",
        orientation=FixtureOrientation.ROT180,
        canonical_labware_definition=build_labware_definition(load_params()),
    )


def test_daemon_client_round_trips_local_workflow(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    server = create_server(port=0, state_db_path=db_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    client = DaemonClient(f"http://{host}:{port}")
    try:
        health = client.health()
        sessions = client.list_sessions(state="ready_no_motion")
        context = client.get_session_context(session.session_id)
        validation = client.validate_plan(
            session.session_id,
            PlanFragment(
                session_id=session.session_id,
                steps=[PlanStep(step_id="home", operation="home")],
            ),
        )
        execution = client.execute_next(
            session.session_id,
            PlanFragment(
                session_id=session.session_id,
                steps=[PlanStep(step_id="inspect", operation="inspect_context")],
            ),
        )

        assert health.ok is True
        assert [item.session_id for item in sessions] == [session.session_id]
        assert context.session_id == session.session_id
        assert validation.allowed is False
        assert execution.executed is True
        assert execution.motion_commands_sent is False
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_client_raises_typed_errors(tmp_path) -> None:
    server = create_server(port=0, state_db_path=tmp_path / "state.sqlite3")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    client = DaemonClient(f"http://{host}:{port}")
    try:
        try:
            client.get_session_context("missing")
        except DaemonClientError as exc:
            assert exc.status_code == 404
            assert exc.code == "session_not_found"
        else:
            raise AssertionError("expected DaemonClientError")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_client_plan_body_carries_route_parity_inputs(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post_model(
        self: DaemonClient,
        path: str,
        body: dict[str, object],
        model_type: type[PlanValidationResult],
    ) -> PlanValidationResult:
        captured["path"] = path
        captured["body"] = body
        captured["model_type"] = model_type
        return PlanValidationResult(session_id="session-1", allowed=True)

    monkeypatch.setattr(DaemonClient, "_post_model", fake_post_model)

    client = DaemonClient()
    result = client.validate_plan(
        "session-1",
        PlanFragment(
            session_id="session-1",
            steps=[PlanStep(step_id="home", operation="home")],
        ),
        offset_registry=OffsetRegistry(),
        safety_profile=_safety_profile(),
        fixture_pose=_fixture_pose(),
        pose_claims=[
            EvidenceClaim(
                claim_id="fixture-upright-1",
                claim_type=POSE_UPRIGHT_CLAIM,
                value=True,
                method="test",
                quality=EvidenceQuality.USABLE,
                pose_digest_sha256=_fixture_pose().pose_digest_sha256,
            )
        ],
        recovery_disposition="not_started",
    )

    body = captured["body"]
    assert result.allowed is True
    assert captured["path"] == "sessions/session-1/validate-plan"
    assert isinstance(body, dict)
    assert "offset_registry" in body
    assert "safety_profile" in body
    assert "fixture_pose" in body
    assert "pose_claims" in body
    assert body["recovery_disposition"] == "not_started"


def test_daemon_client_arm_motion_approval_body_mints_server_side(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post_model(
        self: DaemonClient,
        path: str,
        body: dict[str, object],
        model_type: type[MotionApprovalArmResult],
    ) -> MotionApprovalArmResult:
        captured["path"] = path
        captured["body"] = body
        captured["model_type"] = model_type
        return MotionApprovalArmResult(
            session_id="session-1",
            armed=False,
            blockers=["blocked by test"],
        )

    monkeypatch.setattr(DaemonClient, "_post_model", fake_post_model)

    client = DaemonClient()
    result = client.arm_motion_approval(
        "session-1",
        PlanFragment(
            session_id="session-1",
            steps=[PlanStep(step_id="home", operation="home")],
        ),
        approved_by="agent-1",
        offset_registry=OffsetRegistry(),
        safety_profile=_safety_profile(),
        fixture_pose=_fixture_pose(),
        pose_claims=[
            EvidenceClaim(
                claim_id="fixture-upright-1",
                claim_type=POSE_UPRIGHT_CLAIM,
                value=True,
                method="test",
                quality=EvidenceQuality.USABLE,
                pose_digest_sha256=_fixture_pose().pose_digest_sha256,
            )
        ],
        recovery_disposition="not_started",
        expires_in_seconds=120,
    )

    body = captured["body"]
    assert result.armed is False
    assert captured["path"] == "sessions/session-1/motion-approval/arm"
    assert captured["model_type"] is MotionApprovalArmResult
    assert isinstance(body, dict)
    assert body["approved_by"] == "agent-1"
    assert body["expires_in_seconds"] == 120
    assert "motion_approval" not in body
    assert "offset_registry" in body
    assert "safety_profile" in body
    assert "fixture_pose" in body
    assert "pose_claims" in body
    assert body["recovery_disposition"] == "not_started"


def test_daemon_client_start_session_body_carries_orientation(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post_model(
        self: DaemonClient,
        path: str,
        body: dict[str, object],
        model_type: object,
    ) -> object:
        captured["path"] = path
        captured["body"] = body
        return object()

    monkeypatch.setattr(DaemonClient, "_post_model", fake_post_model)

    client = DaemonClient()
    client.start_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        slot="5",
        orientation="rot180",
    )

    assert captured["path"] == "sessions/start-nomotion"
    assert captured["body"]["orientation"] == "rot180"
