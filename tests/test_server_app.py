from __future__ import annotations

import json
from datetime import datetime, timedelta
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from aevum_cad.labware import build_labware_definition
from aevum_cad.params import load_params
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.models import (
    BridgeSession,
    EndpointResult,
    EvidenceClaim,
    EvidenceHandle,
    EvidenceQuality,
    EvidenceSourceKind,
    NoMotionSessionInitReport,
    OffsetRegistry,
    RobotStatus,
)
from aevum_ot2.core.motion_commissioning import MotionApprovalArmResult
from aevum_ot2.core.pose import (
    POSE_EVIDENCE_METHOD,
    POSE_UPRIGHT_CLAIM,
    FixtureOrientation,
    FixturePose,
    fixture_pose_from_labware_definition,
    pose_orientation_claim_type,
)
from aevum_ot2.core.safety import (
    BoundaryTargetHandling,
    FixtureSafetyProfile,
    MeasuredFixtureBounds,
)
from aevum_ot2.core.sessions import write_session
from aevum_ot2.core.validation import PlanValidationResult
from aevum_ot2.server.app import (
    MAX_JSON_NESTING_DEPTH,
    MAX_REQUEST_BODY_BYTES,
    create_handler,
    create_server,
)


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


def _request_json(url: str, body: dict[str, object] | None = None) -> dict[str, object]:
    request = Request(url)
    if body is not None:
        request.data = json.dumps(body).encode("utf-8")
        request.add_header("Content-Type", "application/json")
        request.method = "POST"
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


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


def _fixture_pose() -> FixturePose:
    return fixture_pose_from_labware_definition(
        current_fixture_identity(),
        slot="5",
        orientation=FixtureOrientation.ROT180,
        canonical_labware_definition=build_labware_definition(load_params()),
    )


def _pose_claims(pose: FixturePose) -> list[EvidenceClaim]:
    identity = current_fixture_identity()
    return [
        EvidenceClaim(
            claim_id="pose-orientation-1",
            claim_type=pose_orientation_claim_type(
                orientation=pose.orientation,
                slot=pose.slot,
                fixture_definition_sha256=identity.labware_definition_sha256,
            ),
            value=True,
            fixture_load_name=identity.load_name,
            fixture_params_sha256=identity.params_sha256,
            labware_definition_sha256=identity.labware_definition_sha256,
            pose_digest_sha256=pose.pose_digest_sha256,
            method=POSE_EVIDENCE_METHOD,
            quality=EvidenceQuality.USABLE,
            session_id="session-1",
            evidence=[
                EvidenceHandle(
                    evidence_id="pose-orientation-evidence-1",
                    source_kind=EvidenceSourceKind.FIXTURE_POSE_ORIENTATION,
                    path="data/measurements/sessions/session-1/fixture_pose_evidence.json",
                    checksum_sha256="1" * 64,
                    session_id="session-1",
                    quality=EvidenceQuality.USABLE,
                )
            ],
        ),
        EvidenceClaim(
            claim_id="fixture-upright-1",
            claim_type=POSE_UPRIGHT_CLAIM,
            value=True,
            fixture_load_name=identity.load_name,
            fixture_params_sha256=identity.params_sha256,
            labware_definition_sha256=identity.labware_definition_sha256,
            pose_digest_sha256=pose.pose_digest_sha256,
            method=POSE_EVIDENCE_METHOD,
            quality=EvidenceQuality.USABLE,
            session_id="session-1",
            evidence=[
                EvidenceHandle(
                    evidence_id="fixture-upright-evidence-1",
                    source_kind=EvidenceSourceKind.FIXTURE_UPRIGHT,
                    path="data/measurements/sessions/session-1/fixture_pose_evidence.json",
                    checksum_sha256="2" * 64,
                    session_id="session-1",
                    quality=EvidenceQuality.USABLE,
                )
            ],
        ),
    ]


def test_daemon_http_health_context_and_validate_plan(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    server = create_server(port=0, state_db_path=db_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    try:
        health = _request_json(f"{base_url}/health")
        context = _request_json(f"{base_url}/sessions/{session.session_id}/context")
        validation = _request_json(
            f"{base_url}/sessions/{session.session_id}/validate-plan",
            {
                "plan": {
                    "schema_version": 1,
                    "session_id": session.session_id,
                    "steps": [{"step_id": "home", "operation": "home"}],
                }
            },
        )
        execution = _request_json(
            f"{base_url}/sessions/{session.session_id}/execute-next",
            {
                "plan": {
                    "schema_version": 1,
                    "session_id": session.session_id,
                    "steps": [
                        {"step_id": "inspect", "operation": "inspect_context"}
                    ],
                }
            },
        )

        assert health["ok"] is True
        assert "execute_next" in health["supported_operations"]
        assert context["session_id"] == session.session_id
        assert context["motion_allowed"] is False
        assert validation["allowed"] is False
        assert validation["motion_allowed"] is False
        assert execution["executed"] is True
        assert execution["motion_commands_sent"] is False
        assert execution["steps"][0]["status"] == "succeeded"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_http_returns_typed_error_for_missing_session(tmp_path) -> None:
    server = create_server(port=0, state_db_path=tmp_path / "state.sqlite3")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        try:
            _request_json(f"http://{host}:{port}/sessions/missing/context")
        except HTTPError as exc:
            data = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 404
            assert data["error"]["code"] == "session_not_found"
        else:
            raise AssertionError("expected HTTPError")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_http_rejects_multi_segment_session_id(tmp_path) -> None:
    server = create_server(port=0, state_db_path=tmp_path / "state.sqlite3")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        request = Request(f"http://{host}:{port}/sessions/a/b/motion-approval/arm")
        request.data = b"{}"
        request.add_header("Content-Type", "application/json")
        request.method = "POST"
        try:
            urlopen(request, timeout=5)
        except HTTPError as exc:
            data = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 400
            assert data["error"]["code"] == "bad_request"
            assert "session_id" in data["error"]["message"]
        else:
            raise AssertionError("expected HTTPError")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_http_start_session_carries_orientation() -> None:
    captured: dict[str, object] = {}

    class FakeService:
        def start_no_motion_session(self, robot_url: str, **kwargs: object) -> object:
            captured["robot_url"] = robot_url
            captured.update(kwargs)
            return NoMotionSessionInitReport(
                robot_url=robot_url,
                status=RobotStatus(
                    robot_url=robot_url,
                    checked_at=datetime.now(),
                    health=EndpointResult(path="/health", ok=True),
                ),
                protocol_runs=EndpointResult(path="/runs", ok=True),
            )

    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(FakeService()))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        _request_json(
            f"http://{host}:{port}/sessions/start-nomotion",
            {
                "robot_url": "http://ot2.local:31950",
                "owner_id": "agent-1",
                "slot": "5",
                "orientation": "rot180",
            },
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert captured["robot_url"] == "http://ot2.local:31950"
    assert captured["orientation"] == "rot180"


def test_daemon_http_rejects_bad_session_orientation_before_service() -> None:
    called = False

    class FakeService:
        def start_no_motion_session(self, robot_url: str, **kwargs: object) -> object:
            nonlocal called
            called = True
            raise AssertionError("service should not be called")

    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(FakeService()))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        with pytest.raises(HTTPError) as exc_info:
            _request_json(
                f"http://{host}:{port}/sessions/start-nomotion",
                {
                    "robot_url": "http://ot2.local:31950",
                    "owner_id": "agent-1",
                    "orientation": "rot90",
                },
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert exc_info.value.code == 400
    assert called is False


def test_daemon_http_rejects_raw_plan_payloads_at_shared_schema(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    server = create_server(port=0, state_db_path=db_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        try:
            _request_json(
                f"http://{host}:{port}/sessions/{session.session_id}/validate-plan",
                {
                    "plan": {
                        "schema_version": 1,
                        "session_id": session.session_id,
                        "steps": [
                            {
                                "step_id": "raw",
                                "operation": "move_high_z",
                                "parameters": {"coordinates": {"x": 1, "y": 2, "z": 3}},
                            }
                        ],
                    }
                },
            )
        except HTTPError as exc:
            data = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 400
            assert data["error"]["code"] == "bad_request"
            assert "unsupported parameters" in data["error"]["message"]
        else:
            raise AssertionError("expected HTTPError")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_http_plan_route_parses_safety_inputs() -> None:
    class FakeService:
        captured: dict[str, object]

        def validate_plan(self, session_id: str, plan: object, **kwargs: object):
            self.captured = {"session_id": session_id, "plan": plan, **kwargs}
            return PlanValidationResult(session_id=session_id, allowed=True)

    service = FakeService()
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(service))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    fixture_pose = _fixture_pose()
    try:
        response = _request_json(
            f"http://{host}:{port}/sessions/session-1/validate-plan",
            {
                "plan": {
                    "schema_version": 1,
                    "session_id": "session-1",
                    "steps": [{"step_id": "home", "operation": "home"}],
                },
                "offset_registry": OffsetRegistry().model_dump(mode="json"),
                "safety_profile": _safety_profile().model_dump(mode="json"),
                "fixture_pose": fixture_pose.model_dump(mode="json"),
                "recovery_disposition": "not_started",
            },
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response["allowed"] is True
    assert isinstance(service.captured["offset_registry"], OffsetRegistry)
    assert isinstance(service.captured["safety_profile"], FixtureSafetyProfile)
    assert isinstance(service.captured["fixture_pose"], FixturePose)
    assert service.captured["fixture_pose"].pose_digest_sha256 == (
        fixture_pose.pose_digest_sha256
    )
    assert service.captured["pose_claims"] == []
    assert service.captured["recovery_disposition"] == "not_started"


def test_daemon_http_arm_motion_approval_route_rejects_supplied_approval() -> None:
    class FakeService:
        def arm_motion_approval(self, session_id: str, plan: object, **kwargs: object):
            raise AssertionError("service should not be called")

    service = FakeService()
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(service))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        with pytest.raises(HTTPError) as exc_info:
            _request_json(
                f"http://{host}:{port}/sessions/session-1/motion-approval/arm",
                {
                    "plan": {
                        "schema_version": 1,
                        "session_id": "session-1",
                        "steps": [{"step_id": "home", "operation": "home"}],
                    },
                    "approved_by": "unit-test",
                    "motion_approval": {"approval_id": "caller-supplied"},
                },
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert exc_info.value.code == 400


def test_daemon_http_arm_motion_approval_route_rejects_huge_ttl() -> None:
    class FakeService:
        def arm_motion_approval(self, session_id: str, plan: object, **kwargs: object):
            raise AssertionError("service should not be called")

    service = FakeService()
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(service))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        with pytest.raises(HTTPError) as exc_info:
            _request_json(
                f"http://{host}:{port}/sessions/session-1/motion-approval/arm",
                {
                    "plan": {
                        "schema_version": 1,
                        "session_id": "session-1",
                        "steps": [{"step_id": "home", "operation": "home"}],
                    },
                    "approved_by": "unit-test",
                    "expires_in_seconds": 10**18,
                },
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert exc_info.value.code == 400


def test_daemon_http_arm_motion_approval_route_parses_inputs() -> None:
    class FakeService:
        captured: dict[str, object]

        def arm_motion_approval(self, session_id: str, plan: object, **kwargs: object):
            self.captured = {"session_id": session_id, "plan": plan, **kwargs}
            return MotionApprovalArmResult(session_id=session_id)

    service = FakeService()
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(service))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        response = _request_json(
            f"http://{host}:{port}/sessions/session-1/motion-approval/arm",
            {
                "plan": {
                    "schema_version": 1,
                    "session_id": "session-1",
                    "steps": [{"step_id": "home", "operation": "home"}],
                },
                "approved_by": "unit-test",
                "expires_in_seconds": 120,
                "safety_profile": _safety_profile().model_dump(mode="json"),
                "recovery_disposition": "not_started",
            },
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response["session_id"] == "session-1"
    assert service.captured["approved_by"] == "unit-test"
    assert service.captured["expires_in_seconds"] == 120
    assert isinstance(service.captured["safety_profile"], FixtureSafetyProfile)


def test_daemon_http_rejects_raw_pose_claims() -> None:
    class FakeService:
        def validate_plan(self, session_id: str, plan: object, **kwargs: object):
            return PlanValidationResult(session_id=session_id, allowed=True)

    service = FakeService()
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(service))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    fixture_pose = _fixture_pose()
    pose_claims = _pose_claims(fixture_pose)
    try:
        try:
            _request_json(
                f"http://{host}:{port}/sessions/session-1/validate-plan",
                {
                    "plan": {
                        "schema_version": 1,
                        "session_id": "session-1",
                        "steps": [{"step_id": "home", "operation": "home"}],
                    },
                    "fixture_pose": fixture_pose.model_dump(mode="json"),
                    "pose_claims": [
                        claim.model_dump(mode="json") for claim in pose_claims
                    ],
                },
            )
        except HTTPError as exc:
            data = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 400
            assert data["error"]["code"] == "bad_request"
            assert "raw pose_claims are not accepted" in data["error"]["message"]
        else:
            raise AssertionError("expected HTTPError")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_http_requires_explicit_plan_envelope(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    server = create_server(port=0, state_db_path=db_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        try:
            _request_json(
                f"http://{host}:{port}/sessions/{session.session_id}/validate-plan",
                {
                    "schema_version": 1,
                    "session_id": session.session_id,
                    "steps": [{"step_id": "inspect", "operation": "inspect_context"}],
                },
            )
        except HTTPError as exc:
            data = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 400
            assert data["error"]["code"] == "bad_request"
            assert "plan" in data["error"]["message"]
        else:
            raise AssertionError("expected HTTPError")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_http_rejects_record_path_traversal(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    server = create_server(port=0, state_db_path=db_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        try:
            _request_json(
                f"http://{host}:{port}/sessions/{session.session_id}/validate-plan",
                {
                    "plan": {
                        "schema_version": 1,
                        "session_id": session.session_id,
                        "steps": [{"step_id": "inspect", "operation": "inspect_context"}],
                    },
                    "target_class_records": ["../../etc/passwd"],
                },
            )
        except HTTPError as exc:
            data = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 400
            assert data["error"]["code"] == "bad_request"
            assert "traversal" in data["error"]["message"]
        else:
            raise AssertionError("expected HTTPError")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_http_context_rejects_record_path_traversal(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    server = create_server(port=0, state_db_path=db_path)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        try:
            _request_json(
                f"http://{host}:{port}/sessions/{session.session_id}/context"
                "?fixture_qc_record=../../etc/passwd"
            )
        except HTTPError as exc:
            data = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 400
            assert data["error"]["code"] == "bad_request"
            assert "traversal" in data["error"]["message"]
        else:
            raise AssertionError("expected HTTPError")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_http_rejects_oversized_request_bodies(tmp_path) -> None:
    server = create_server(port=0, state_db_path=tmp_path / "state.sqlite3")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        connection = HTTPConnection(host, port, timeout=5)
        try:
            connection.putrequest("POST", "/sessions/start-nomotion")
            connection.putheader("Content-Type", "application/json")
            connection.putheader("Content-Length", str(MAX_REQUEST_BODY_BYTES + 1))
            connection.endheaders()
            response = connection.getresponse()
            data = json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()
        assert response.status == 400
        assert data["error"]["code"] == "bad_request"
        assert "request body too large" in data["error"]["message"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_http_rejects_transfer_encoding(tmp_path) -> None:
    server = create_server(port=0, state_db_path=tmp_path / "state.sqlite3")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        connection = HTTPConnection(host, port, timeout=5)
        try:
            connection.putrequest("POST", "/sessions/start-nomotion")
            connection.putheader("Transfer-Encoding", "chunked")
            connection.endheaders()
            response = connection.getresponse()
            data = json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()
        assert response.status == 400
        assert data["error"]["code"] == "bad_request"
        assert "Transfer-Encoding is not supported" in data["error"]["message"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_http_rejects_excessive_json_nesting(tmp_path) -> None:
    server = create_server(port=0, state_db_path=tmp_path / "state.sqlite3")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        body = ("[" * (MAX_JSON_NESTING_DEPTH + 1)) + (
            "]" * (MAX_JSON_NESTING_DEPTH + 1)
        )
        request = Request(f"http://{host}:{port}/sessions/start-nomotion")
        request.data = body.encode("utf-8")
        request.add_header("Content-Type", "application/json")
        request.method = "POST"
        try:
            with urlopen(request, timeout=5):
                pass
        except HTTPError as exc:
            data = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 400
            assert data["error"]["code"] == "bad_request"
            assert "JSON nesting too deep" in data["error"]["message"]
        else:
            raise AssertionError("expected HTTPError")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_daemon_server_refuses_remote_bind_without_explicit_override(tmp_path) -> None:
    with pytest.raises(ValueError, match="non-loopback"):
        create_server(host="0.0.0.0", port=0, state_db_path=tmp_path / "state.sqlite3")


def test_daemon_server_refuses_remote_bind_with_motion_backend(tmp_path) -> None:
    with pytest.raises(ValueError, match="motion backend"):
        create_server(
            host="0.0.0.0",
            port=0,
            state_db_path=tmp_path / "state.sqlite3",
            motion_enabled=True,
            motion_backend_enabled=True,
            allow_remote=True,
        )


def test_daemon_server_requires_motion_backend_token(tmp_path) -> None:
    with pytest.raises(ValueError, match="local auth token"):
        create_server(
            port=0,
            state_db_path=tmp_path / "state.sqlite3",
            motion_enabled=True,
            motion_backend_enabled=True,
        )
