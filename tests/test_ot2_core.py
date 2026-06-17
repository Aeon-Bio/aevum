from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw
from pydantic import ValidationError

import aevum_ot2.core.maintenance as maintenance_module
import aevum_ot2.core.sessions as sessions_module
from aevum_ot2.core.artifacts import current_fixture_identity, sha256_file
from aevum_ot2.core.camera import DEFAULT_IMAGE_DIR
from aevum_ot2.core.client import Ot2Client
from aevum_ot2.core.command_journal import list_command_journal_entries
from aevum_ot2.core.discovery import ROBOT_URL_ENV, normalize_robot_url, resolve_robot
from aevum_ot2.core.evidence import append_evidence_event, load_evidence_index
from aevum_ot2.core.lock import acquire_lock, read_lock, write_lock
from aevum_ot2.core.maintenance import (
    _comment_command_body,
    _extract_body_id,
    _extract_body_status,
    _extract_command_result_field,
    _extract_definition_uri,
    _has_protocol_runs,
    _load_labware_command_body,
    run_no_motion_maintenance_lifecycle_spike,
)
from aevum_ot2.core.models import (
    BridgeLock,
    BridgeSession,
    EndpointResult,
    EvidenceEvent,
    RobotStatus,
)
from aevum_ot2.core.pose import load_fixture_pose
from aevum_ot2.core.sessions import (
    _compact_load_labware_result,
    close_no_motion_session,
    initialize_no_motion_session,
    list_sessions,
    read_session,
    write_session,
)
from aevum_ot2.core.vision import analyze_camera_image


def test_current_fixture_identity_matches_generated_labware() -> None:
    identity = current_fixture_identity()

    assert identity.load_name == "aevum_p300_poc_fixture"
    assert identity.dimensions_match is True
    assert len(identity.params_sha256) == 64
    assert len(identity.labware_definition_sha256) == 64


def test_sha256_file_is_stable_for_params() -> None:
    identity = current_fixture_identity()

    assert sha256_file(identity.params_path) == identity.params_sha256


def test_evidence_index_appends_event(tmp_path) -> None:
    path = tmp_path / "evidence.json"
    event = EvidenceEvent(event_type="test", summary="test event")

    append_evidence_event(event, path)
    index = load_evidence_index(path)

    assert len(index.events) == 1
    assert index.events[0].event_type == "test"


def test_bridge_lock_round_trip(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    now = datetime.now()
    lock = BridgeLock(
        robot_url="http://ot2.local:31950",
        session_id="session-1",
        owner_id="agent-1",
        lease_started_at=now,
        lease_expires_at=now + timedelta(minutes=5),
    )

    write_lock(lock, db_path)
    loaded = read_lock(lock.robot_url, db_path)

    assert loaded is not None
    assert loaded.session_id == "session-1"
    assert loaded.owner_id == "agent-1"


def test_acquire_lock_allows_only_one_concurrent_owner(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    now = datetime.now()

    def attempt(number: int) -> object:
        return acquire_lock(
            BridgeLock(
                robot_url="http://ot2.local:31950",
                session_id=f"session-{number}",
                owner_id=f"agent-{number}",
                lease_started_at=now,
                lease_expires_at=now + timedelta(minutes=5),
                state="starting",
            ),
            db_path,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(attempt, range(16)))

    acquired = [result for result in results if result.acquired]
    loaded = read_lock("http://ot2.local:31950", db_path)

    assert len(acquired) == 1
    assert loaded is not None
    assert loaded.session_id == acquired[0].lock.session_id
    assert all(
        result.acquired or result.lock.session_id == acquired[0].lock.session_id
        for result in results
    )


def test_acquire_lock_blocks_expired_unreconciled_lock(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    now = datetime.now()
    write_lock(
        BridgeLock(
            robot_url="http://ot2.local:31950",
            session_id="old-session",
            owner_id="agent-old",
            lease_started_at=now - timedelta(hours=2),
            lease_expires_at=now - timedelta(hours=1),
            state="active_no_motion",
        ),
        db_path,
    )

    result = acquire_lock(
        BridgeLock(
            robot_url="http://ot2.local:31950",
            session_id="new-session",
            owner_id="agent-new",
            lease_started_at=now,
            lease_expires_at=now + timedelta(minutes=5),
            state="starting",
        ),
        db_path,
    )

    assert result.acquired is False
    assert result.lock.session_id == "old-session"
    assert read_lock("http://ot2.local:31950", db_path).session_id == "old-session"


def test_maintenance_spike_blocks_when_bridge_lock_active(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    now = datetime.now()
    posts: list[str] = []
    write_lock(
        BridgeLock(
            robot_url="http://ot2.local:31950",
            session_id="session-1",
            owner_id="agent-1",
            lease_started_at=now,
            lease_expires_at=now + timedelta(minutes=5),
            state="active_no_motion",
        ),
        db_path,
    )
    monkeypatch.setattr(
        maintenance_module,
        "append_evidence_event",
        lambda event, **kwargs: None,
    )

    class LockedBridgeClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url.rstrip("/") + "/"
            self.timeout_seconds = timeout_seconds

        def status(self) -> RobotStatus:
            return RobotStatus(
                robot_url=self.robot_url,
                checked_at=datetime.now(),
                health=EndpointResult(path="/health", ok=True),
            )

        def get_json(self, path: str) -> EndpointResult:
            if path == "/runs":
                return EndpointResult(path=path, ok=True, data={"data": []})
            raise AssertionError(f"unexpected GET {path}")

        def post_json(
            self,
            path: str,
            body: dict[str, object] | None = None,
        ) -> EndpointResult:
            posts.append(path)
            return EndpointResult(path=path, ok=True)

    monkeypatch.setattr(maintenance_module, "Ot2Client", LockedBridgeClient)

    report = run_no_motion_maintenance_lifecycle_spike(
        "http://ot2.local:31950",
        state_db_path=db_path,
    )

    assert posts == []
    assert report.create_result is None
    assert "bridge lock session-1 is active" in " ".join(report.notes)


def test_acquire_lock_replaces_terminal_lock(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    now = datetime.now()
    write_lock(
        BridgeLock(
            robot_url="http://ot2.local:31950",
            session_id="old-session",
            owner_id="agent-old",
            lease_started_at=now - timedelta(hours=2),
            lease_expires_at=now - timedelta(hours=1),
            state="closed",
        ),
        db_path,
    )

    result = acquire_lock(
        BridgeLock(
            robot_url="http://ot2.local:31950",
            session_id="new-session",
            owner_id="agent-new",
            lease_started_at=now,
            lease_expires_at=now + timedelta(minutes=5),
            state="starting",
        ),
        db_path,
    )

    assert result.acquired is True
    assert read_lock("http://ot2.local:31950", db_path).session_id == "new-session"


def _bridge_session(
    session_id: str = "session-1",
    *,
    state: str = "ready_no_motion",
    robot_url: str = "http://ot2.local:31950",
    maintenance_run_id: str | None = "run-1",
) -> BridgeSession:
    identity = current_fixture_identity()
    now = datetime.now()
    return BridgeSession(
        session_id=session_id,
        kind="registration",
        owner_id="agent-1",
        robot_url=robot_url,
        robot_serial="rough-morning",
        robot_server_version="9.0.0",
        max_protocol_api_version="2.28",
        state=state,
        created_at=now,
        updated_at=now,
        lease_expires_at=now + timedelta(minutes=5),
        maintenance_run_id=maintenance_run_id,
        slot="1",
        fixture_identity=identity,
        definition_uri="aevum/aevum_p300_poc_fixture/1",
        loaded_labware_id="fixture-1",
        evidence_index_path="data/measurements/ot2_evidence_index.json",
    )


def test_bridge_session_round_trip(tmp_path) -> None:
    session = _bridge_session()
    db_path = tmp_path / "state.sqlite3"
    write_session(session, db_path)
    loaded = read_session(session.session_id, db_path)

    assert loaded is not None
    assert loaded.session_id == "session-1"
    assert loaded.loaded_labware_id == "fixture-1"
    assert loaded.motion_allowed is False


def test_old_bridge_session_payload_loads_with_empty_pipette_defaults() -> None:
    data = _bridge_session().model_dump(mode="json")
    for field in [
        "pipette_name",
        "pipette_mount",
        "pipette_model",
        "pipette_id",
        "pipette_tip_length_mm",
    ]:
        data.pop(field, None)

    loaded = BridgeSession.model_validate(data)

    assert loaded.pipette_name == ""
    assert loaded.pipette_mount == ""
    assert loaded.pipette_model == ""
    assert loaded.pipette_id == ""
    assert loaded.pipette_tip_length_mm is None


def test_session_pipette_fields_extract_selected_mount() -> None:
    status = RobotStatus(
        robot_url="http://ot2.local:31950",
        checked_at=datetime.now(),
        health=EndpointResult(path="/health", ok=True),
        pipettes=EndpointResult(
            path="/pipettes",
            ok=True,
            data={
                "left": {
                    "name": "p300_single_gen2",
                    "model": "p300_single_v2.1",
                    "id": "pipette-1",
                    "tip_length": 51.7,
                },
                "right": {},
            },
        ),
    )

    fields = sessions_module._session_pipette_fields(status, "left")

    assert fields["pipette_mount"] == "left"
    assert fields["pipette_name"] == "p300_single_gen2"
    assert fields["pipette_model"] == "p300_single_v2.1"
    assert fields["pipette_id"] == "pipette-1"
    assert fields["pipette_tip_length_mm"] == 51.7


def test_bridge_session_rejects_invalid_pipette_mount() -> None:
    data = _bridge_session().model_dump(mode="json")
    data["pipette_mount"] = "deck"

    try:
        BridgeSession.model_validate(data)
    except ValidationError:
        pass
    else:
        raise AssertionError("expected invalid pipette mount to fail validation")


def test_list_sessions_filters_by_robot_and_state(tmp_path) -> None:
    db_path = tmp_path / "state.sqlite3"
    write_session(_bridge_session("old", state="closed"), db_path)
    write_session(_bridge_session("active", state="ready_no_motion"), db_path)
    write_session(
        _bridge_session("other", robot_url="http://other.local:31950"),
        db_path,
    )

    loaded = list_sessions(
        db_path,
        robot_url="http://ot2.local:31950",
        state="ready_no_motion",
    )

    assert [session.session_id for session in loaded] == ["active"]


def test_close_no_motion_session_keeps_lock_when_delete_fails(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "state.sqlite3"
    now = datetime.now()
    session = _bridge_session("session-1")
    lock = BridgeLock(
        robot_url=session.robot_url,
        session_id=session.session_id,
        owner_id=session.owner_id,
        lease_started_at=now,
        lease_expires_at=now + timedelta(minutes=5),
        active_run_id=session.maintenance_run_id,
        state="active_no_motion",
    )
    write_session(session, db_path)
    write_lock(lock, db_path)

    class FailingClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url
            self.timeout_seconds = timeout_seconds

        def delete_json(self, path: str) -> EndpointResult:
            return EndpointResult(path=path, ok=False, error="timeout")

    monkeypatch.setattr(sessions_module, "Ot2Client", FailingClient)

    report = close_no_motion_session(session.session_id, state_db_path=db_path)

    assert report.session_before is not None
    assert report.session_before.state == "ready_no_motion"
    assert report.session_after is not None
    assert report.session_after.state == "close_failed"
    assert report.lock is not None
    assert report.lock.state == "recovery_required"
    assert report.lock.active_run_id == "run-1"


def test_session_init_lock_conflict_does_not_create_maintenance_run(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    now = datetime.now()
    write_lock(
        BridgeLock(
            robot_url="http://ot2.local:31950",
            session_id="other-session",
            owner_id="other-agent",
            lease_started_at=now,
            lease_expires_at=now + timedelta(minutes=10),
            state="active_no_motion",
        ),
        db_path,
    )

    class LockConflictClient:
        post_called = False

        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url.rstrip("/") + "/"
            self.timeout_seconds = timeout_seconds

        def status(self) -> RobotStatus:
            return RobotStatus(
                robot_url=self.robot_url,
                checked_at=datetime.now(),
                health=EndpointResult(
                    path="/health",
                    ok=True,
                    data={
                        "robot_serial": "OT2TEST0001",
                        "api_version": "9.0.0",
                        "maximum_protocol_api_version": [2, 28],
                    },
                ),
            )

        def get_json(self, path: str) -> EndpointResult:
            assert path == "/runs"
            return EndpointResult(path=path, ok=True, data={"data": []})

        def post_json(self, path: str, body: object | None = None) -> EndpointResult:
            self.post_called = True
            raise AssertionError(f"post_json should not be called for {path}")

    monkeypatch.setattr(sessions_module, "Ot2Client", LockConflictClient)

    report = initialize_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        state_db_path=db_path,
    )

    lock = read_lock("http://ot2.local:31950", db_path)
    assert report.session is None
    assert report.lock is not None
    assert report.lock.session_id == "other-session"
    assert lock is not None and lock.session_id == "other-session"
    assert any("bridge lock" in note for note in report.notes)


def test_session_init_journals_load_labware_command(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "state.sqlite3"
    monkeypatch.setattr(sessions_module, "append_evidence_event", lambda event, **kwargs: None)

    class SuccessfulInitClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url.rstrip("/") + "/"
            self.timeout_seconds = timeout_seconds
            self.load_labware_command: dict[str, object] | None = None

        def status(self) -> RobotStatus:
            return RobotStatus(
                robot_url=self.robot_url,
                checked_at=datetime.now(),
                health=EndpointResult(
                    path="/health",
                    ok=True,
                    data={
                        "robot_serial": "OT2TEST0001",
                        "api_version": "9.0.0",
                        "maximum_protocol_api_version": [2, 28],
                    },
                ),
            )

        def get_json(self, path: str) -> EndpointResult:
            if path == "/runs":
                return EndpointResult(path=path, ok=True, data={"data": []})
            if path == "/maintenance_runs/run-1/commands?pageLength=1000":
                assert self.load_labware_command is not None
                return EndpointResult(
                    path=path,
                    ok=True,
                    data={
                        "data": [self.load_labware_command],
                        "meta": {"totalLength": 1},
                    },
                )
            if path == "/maintenance_runs/run-1":
                return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})
            return EndpointResult(path=path, ok=False, status_code=404)

        def post_json(
            self,
            path: str,
            body: dict[str, object] | None = None,
        ) -> EndpointResult:
            if path == "/maintenance_runs":
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={"data": {"id": "run-1"}},
                )
            if path == "/maintenance_runs/run-1/labware_definitions":
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={
                        "data": {
                            "definitionUri": "aevum/aevum_p300_poc_fixture/1",
                        }
                    },
                )
            if path == "/maintenance_runs/run-1/commands?waitUntilComplete=true&timeout=5000":
                assert body is not None
                data = body["data"]
                assert isinstance(data, dict)
                params = data["params"]
                assert isinstance(params, dict)
                self.load_labware_command = {
                    "id": "command-1",
                    "key": data["key"],
                    "commandType": "loadLabware",
                    "params": params,
                    "status": "succeeded",
                    "result": {"labwareId": params["labwareId"]},
                }
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={"data": self.load_labware_command},
                )
            raise AssertionError(f"unexpected POST {path}")

        def delete_json(self, path: str) -> EndpointResult:
            raise AssertionError(f"delete_json should not be called for {path}")

    monkeypatch.setattr(sessions_module, "Ot2Client", SuccessfulInitClient)

    report = initialize_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        state_db_path=db_path,
    )

    assert report.session is not None
    assert report.session.state == "ready_no_motion"
    assert report.session.last_command_key is not None
    entries = list_command_journal_entries(report.session.session_id, db_path)
    assert len(entries) == 1
    assert entries[0].command_key == report.session.last_command_key
    assert entries[0].command_type == "loadLabware"
    assert entries[0].state == "completed"


def test_session_init_rot180_uploads_oriented_labware_and_persists_pose(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    monkeypatch.setattr(sessions_module, "append_evidence_event", lambda event, **kwargs: None)

    class Rot180InitClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url.rstrip("/") + "/"
            self.timeout_seconds = timeout_seconds
            self.load_labware_command: dict[str, object] | None = None

        def status(self) -> RobotStatus:
            return RobotStatus(
                robot_url=self.robot_url,
                checked_at=datetime.now(),
                health=EndpointResult(
                    path="/health",
                    ok=True,
                    data={
                        "robot_serial": "OT2TEST0001",
                        "api_version": "9.0.0",
                        "maximum_protocol_api_version": [2, 28],
                    },
                ),
            )

        def get_json(self, path: str) -> EndpointResult:
            if path == "/runs":
                return EndpointResult(path=path, ok=True, data={"data": []})
            if path == "/maintenance_runs/run-1/commands?pageLength=1000":
                assert self.load_labware_command is not None
                return EndpointResult(
                    path=path,
                    ok=True,
                    data={
                        "data": [self.load_labware_command],
                        "meta": {"totalLength": 1},
                    },
                )
            if path == "/maintenance_runs/run-1":
                return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})
            return EndpointResult(path=path, ok=False, status_code=404)

        def post_json(
            self,
            path: str,
            body: dict[str, object] | None = None,
        ) -> EndpointResult:
            if path == "/maintenance_runs":
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={"data": {"id": "run-1"}},
                )
            if path == "/maintenance_runs/run-1/labware_definitions":
                assert body is not None
                definition = body["data"]
                assert isinstance(definition, dict)
                assert definition["parameters"]["loadName"] == (
                    "aevum_p300_poc_fixture_rot180"
                )
                assert definition["wells"]["A1"]["x"] == 102.76
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={
                        "data": {
                            "definitionUri": "aevum/aevum_p300_poc_fixture_rot180/1",
                        }
                    },
                )
            if path == "/maintenance_runs/run-1/commands?waitUntilComplete=true&timeout=5000":
                assert body is not None
                data = body["data"]
                assert isinstance(data, dict)
                params = data["params"]
                assert isinstance(params, dict)
                assert params["loadName"] == "aevum_p300_poc_fixture_rot180"
                assert params["location"]["slotName"] == "5"
                self.load_labware_command = {
                    "id": "command-1",
                    "key": data["key"],
                    "commandType": "loadLabware",
                    "params": params,
                    "status": "succeeded",
                    "result": {"labwareId": params["labwareId"]},
                }
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={"data": self.load_labware_command},
                )
            raise AssertionError(f"unexpected POST {path}")

        def delete_json(self, path: str) -> EndpointResult:
            raise AssertionError(f"delete_json should not be called for {path}")

    monkeypatch.setattr(sessions_module, "Ot2Client", Rot180InitClient)

    report = initialize_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        slot="5",
        orientation="rot180",
        state_db_path=db_path,
    )

    assert report.session is not None
    assert report.session.state == "ready_no_motion"
    assert report.session.fixture_orientation == "rot180"
    assert len(report.session.fixture_pose_digest_sha256) == 64
    assert report.session.fixture_pose_path
    assert tmp_path in Path(report.session.fixture_pose_path).parents
    assert tmp_path in Path(report.session.evidence_index_path).parents
    pose = load_fixture_pose(report.session.fixture_pose_path)
    assert pose.pose_digest_sha256 == report.session.fixture_pose_digest_sha256
    assert pose.oriented_labware_load_name == "aevum_p300_poc_fixture_rot180"
    assert report.session.definition_uri == "aevum/aevum_p300_poc_fixture_rot180/1"
    entries = list_command_journal_entries(report.session.session_id, db_path)
    assert entries[0].command_type == "loadLabware"


def test_session_init_local_pose_persistence_failure_cleans_up_run(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    deletes: list[str] = []
    monkeypatch.setattr(sessions_module, "append_evidence_event", lambda event, **kwargs: None)

    def fail_write_fixture_pose(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(sessions_module, "write_fixture_pose", fail_write_fixture_pose)

    class PersistenceFailureClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url.rstrip("/") + "/"
            self.timeout_seconds = timeout_seconds

        def status(self) -> RobotStatus:
            return RobotStatus(
                robot_url=self.robot_url,
                checked_at=datetime.now(),
                health=EndpointResult(path="/health", ok=True),
            )

        def get_json(self, path: str) -> EndpointResult:
            if path == "/runs":
                return EndpointResult(path=path, ok=True, data={"data": []})
            raise AssertionError(f"unexpected GET {path}")

        def post_json(
            self,
            path: str,
            body: dict[str, object] | None = None,
        ) -> EndpointResult:
            assert path == "/maintenance_runs"
            return EndpointResult(
                path=path,
                ok=True,
                status_code=201,
                data={"data": {"id": "run-1"}},
            )

        def delete_json(self, path: str) -> EndpointResult:
            deletes.append(path)
            return EndpointResult(path=path, ok=False, status_code=404)

    monkeypatch.setattr(sessions_module, "Ot2Client", PersistenceFailureClient)

    report = initialize_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        state_db_path=db_path,
    )

    assert deletes == ["/maintenance_runs/run-1"]
    assert report.session is not None
    assert report.session.state == "failed"
    assert "Local session persistence failed" in report.session.notes[-1]
    assert report.lock is not None
    assert report.lock.state == "failed"
    assert report.lock.active_run_id is None


def test_session_init_cleanup_demotes_lock_when_session_write_fails(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    deletes: list[str] = []
    monkeypatch.setattr(sessions_module, "append_evidence_event", lambda event, **kwargs: None)

    def fail_write_session(*args: object, **kwargs: object) -> None:
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(sessions_module, "write_session", fail_write_session)

    class SessionWriteFailureClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url.rstrip("/") + "/"
            self.timeout_seconds = timeout_seconds

        def status(self) -> RobotStatus:
            return RobotStatus(
                robot_url=self.robot_url,
                checked_at=datetime.now(),
                health=EndpointResult(path="/health", ok=True),
            )

        def get_json(self, path: str) -> EndpointResult:
            if path == "/runs":
                return EndpointResult(path=path, ok=True, data={"data": []})
            raise AssertionError(f"unexpected GET {path}")

        def post_json(
            self,
            path: str,
            body: dict[str, object] | None = None,
        ) -> EndpointResult:
            assert path == "/maintenance_runs"
            return EndpointResult(
                path=path,
                ok=True,
                status_code=201,
                data={"data": {"id": "run-1"}},
            )

        def delete_json(self, path: str) -> EndpointResult:
            deletes.append(path)
            return EndpointResult(path=path, ok=False, status_code=404)

    monkeypatch.setattr(sessions_module, "Ot2Client", SessionWriteFailureClient)

    report = initialize_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        state_db_path=db_path,
    )

    assert deletes == ["/maintenance_runs/run-1"]
    assert report.session is not None
    assert report.session.state == "failed"
    assert report.lock is not None
    assert report.lock.state == "failed"
    assert report.lock.active_run_id is None
    assert read_lock("http://ot2.local:31950", db_path).state == "failed"
    assert any("session write failed during cleanup" in note for note in report.notes)


def test_session_init_rejects_bad_orientation_before_robot_calls(
    monkeypatch,
) -> None:
    monkeypatch.setattr(sessions_module, "append_evidence_event", lambda event, **kwargs: None)

    class NoNetworkClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("client should not be constructed")

    monkeypatch.setattr(sessions_module, "Ot2Client", NoNetworkClient)

    report = initialize_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        orientation="rot90",
    )

    assert report.session is None
    assert report.status.health.ok is False
    assert any("unsupported" in note for note in report.notes)


def test_session_init_cleanup_delete_failure_requires_recovery(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    monkeypatch.setattr(sessions_module, "append_evidence_event", lambda event, **kwargs: None)

    class UnreconciledInitClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url.rstrip("/") + "/"
            self.timeout_seconds = timeout_seconds

        def status(self) -> RobotStatus:
            return RobotStatus(
                robot_url=self.robot_url,
                checked_at=datetime.now(),
                health=EndpointResult(path="/health", ok=True),
            )

        def get_json(self, path: str) -> EndpointResult:
            if path == "/runs":
                return EndpointResult(path=path, ok=True, data={"data": []})
            if path == "/maintenance_runs/run-1/commands?pageLength=1000":
                return EndpointResult(path=path, ok=False, error="timeout")
            return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})

        def post_json(
            self,
            path: str,
            body: dict[str, object] | None = None,
        ) -> EndpointResult:
            if path == "/maintenance_runs":
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={"data": {"id": "run-1"}},
                )
            if path == "/maintenance_runs/run-1/labware_definitions":
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={
                        "data": {
                            "definitionUri": "aevum/aevum_p300_poc_fixture/1",
                        }
                    },
                )
            if path == "/maintenance_runs/run-1/commands?waitUntilComplete=true&timeout=5000":
                assert body is not None
                data = body["data"]
                assert isinstance(data, dict)
                params = data["params"]
                assert isinstance(params, dict)
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={
                        "data": {
                            "id": "command-1",
                            "key": data["key"],
                            "commandType": "loadLabware",
                            "params": params,
                            "status": "succeeded",
                            "result": {"labwareId": params["labwareId"]},
                        }
                    },
                )
            raise AssertionError(f"unexpected POST {path}")

        def delete_json(self, path: str) -> EndpointResult:
            return EndpointResult(path=path, ok=False, status_code=500, error="stuck")

    monkeypatch.setattr(sessions_module, "Ot2Client", UnreconciledInitClient)

    report = initialize_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        state_db_path=db_path,
    )

    assert report.session is not None
    assert report.session.state == "recovery_required"
    assert report.lock is not None
    assert report.lock.state == "recovery_required"
    assert report.lock.active_run_id == "run-1"
    assert report.cleanup_delete_result is not None
    assert report.cleanup_delete_result.ok is False


def test_session_init_ambiguous_reconciliation_remains_recovery_after_cleanup(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    monkeypatch.setattr(sessions_module, "append_evidence_event", lambda event, **kwargs: None)

    class ConfirmedCleanupClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url.rstrip("/") + "/"
            self.timeout_seconds = timeout_seconds
            self.deleted = False

        def status(self) -> RobotStatus:
            return RobotStatus(
                robot_url=self.robot_url,
                checked_at=datetime.now(),
                health=EndpointResult(path="/health", ok=True),
            )

        def get_json(self, path: str) -> EndpointResult:
            if path == "/runs":
                return EndpointResult(path=path, ok=True, data={"data": []})
            if path == "/maintenance_runs/run-1/commands?pageLength=1000":
                return EndpointResult(path=path, ok=False, error="timeout")
            if path == "/maintenance_runs/run-1" and self.deleted:
                return EndpointResult(path=path, ok=False, status_code=404)
            return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})

        def post_json(
            self,
            path: str,
            body: dict[str, object] | None = None,
        ) -> EndpointResult:
            if path == "/maintenance_runs":
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={"data": {"id": "run-1"}},
                )
            if path == "/maintenance_runs/run-1/labware_definitions":
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={
                        "data": {
                            "definitionUri": "aevum/aevum_p300_poc_fixture/1",
                        }
                    },
                )
            if path == "/maintenance_runs/run-1/commands?waitUntilComplete=true&timeout=5000":
                assert body is not None
                data = body["data"]
                assert isinstance(data, dict)
                params = data["params"]
                assert isinstance(params, dict)
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={
                        "data": {
                            "id": "command-1",
                            "key": data["key"],
                            "commandType": "loadLabware",
                            "params": params,
                            "status": "succeeded",
                            "result": {"labwareId": params["labwareId"]},
                        }
                    },
                )
            raise AssertionError(f"unexpected POST {path}")

        def delete_json(self, path: str) -> EndpointResult:
            self.deleted = True
            return EndpointResult(path=path, ok=True, status_code=200)

    monkeypatch.setattr(sessions_module, "Ot2Client", ConfirmedCleanupClient)

    report = initialize_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        state_db_path=db_path,
    )

    assert report.session is not None
    assert report.session.state == "recovery_required"
    assert report.lock is not None
    assert report.lock.state == "recovery_required"
    assert report.lock.active_run_id is None
    assert report.cleanup_confirm_result is not None
    assert report.cleanup_confirm_result.status_code == 404


def test_session_init_cleanup_delete_requires_post_delete_absence(
    tmp_path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    monkeypatch.setattr(sessions_module, "append_evidence_event", lambda event, **kwargs: None)

    class UnconfirmedCleanupClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url.rstrip("/") + "/"
            self.timeout_seconds = timeout_seconds

        def status(self) -> RobotStatus:
            return RobotStatus(
                robot_url=self.robot_url,
                checked_at=datetime.now(),
                health=EndpointResult(path="/health", ok=True),
            )

        def get_json(self, path: str) -> EndpointResult:
            if path == "/runs":
                return EndpointResult(path=path, ok=True, data={"data": []})
            return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})

        def post_json(
            self,
            path: str,
            body: dict[str, object] | None = None,
        ) -> EndpointResult:
            if path == "/maintenance_runs":
                return EndpointResult(
                    path=path,
                    ok=True,
                    status_code=201,
                    data={"data": {"id": "run-1"}},
                )
            if path == "/maintenance_runs/run-1/labware_definitions":
                return EndpointResult(path=path, ok=False, status_code=500)
            raise AssertionError(f"unexpected POST {path}")

        def delete_json(self, path: str) -> EndpointResult:
            return EndpointResult(path=path, ok=True, status_code=200)

    monkeypatch.setattr(sessions_module, "Ot2Client", UnconfirmedCleanupClient)

    report = initialize_no_motion_session(
        "http://ot2.local:31950",
        owner_id="agent-1",
        state_db_path=db_path,
    )

    assert report.session is not None
    assert report.session.state == "recovery_required"
    assert report.lock is not None
    assert report.lock.state == "recovery_required"
    assert report.lock.active_run_id == "run-1"
    assert report.cleanup_confirm_result is not None
    assert report.cleanup_confirm_result.status_code != 404


def test_ot2_client_normalizes_robot_url() -> None:
    client = Ot2Client("http://ot2.local:31950")

    assert client.robot_url == "http://ot2.local:31950/"


def test_normalize_robot_url_adds_http_scheme() -> None:
    assert normalize_robot_url("ot2.local:31950/") == "http://ot2.local:31950"


def test_resolve_robot_prefers_explicit_url(monkeypatch) -> None:
    monkeypatch.setenv(ROBOT_URL_ENV, "http://env.local:31950")

    result = resolve_robot("explicit.local:31950")

    assert result.robot_url == "http://explicit.local:31950"
    assert result.source == "argument"


def test_resolve_robot_uses_environment(monkeypatch) -> None:
    monkeypatch.setenv(ROBOT_URL_ENV, "env.local:31950")

    result = resolve_robot()

    assert result.robot_url == "http://env.local:31950"
    assert result.source == "environment"


def test_default_image_dir_is_under_measurements() -> None:
    assert DEFAULT_IMAGE_DIR.name == "images"
    assert DEFAULT_IMAGE_DIR.parent.name == "measurements"


def test_analyze_camera_image_records_evidence_quality(tmp_path) -> None:
    image_path = tmp_path / "deck.jpg"
    image = Image.new("RGB", (640, 480), color=(110, 110, 110))
    draw = ImageDraw.Draw(image)
    for x in range(0, 640, 80):
        draw.line((x, 0, x, 479), fill=(210, 210, 210), width=3)
    for y in range(0, 480, 80):
        draw.line((0, y, 639, y), fill=(40, 40, 40), width=3)
    image.save(image_path)

    result = analyze_camera_image(image_path, record_evidence=False)

    assert result.evidence_ok is True
    assert result.motion_gate is False
    assert result.metrics is not None
    assert result.metrics.width_px == 640
    assert result.metrics.height_px == 480
    assert any(check.name == "motion_authorization" for check in result.checks)


def test_fixture_presence_analysis_requires_calibrated_detector(tmp_path) -> None:
    image_path = tmp_path / "fixture.jpg"
    image = Image.new("RGB", (640, 480), color=(120, 120, 120))
    draw = ImageDraw.Draw(image)
    draw.rectangle((120, 120, 520, 360), outline=(20, 20, 20), width=5)
    image.save(image_path)

    result = analyze_camera_image(image_path, purpose="fixture_presence", record_evidence=False)

    assert result.evidence_ok is True
    assert result.motion_gate is False
    assert any(
        check.name == "validated_fixture_detector" and check.passed is False
        for check in result.checks
    )


def test_too_small_camera_image_fails_evidence_quality(tmp_path) -> None:
    image_path = tmp_path / "small.jpg"
    Image.new("RGB", (320, 240), color=(120, 120, 120)).save(image_path)

    result = analyze_camera_image(image_path, record_evidence=False)

    assert result.evidence_ok is False
    assert result.motion_gate is False
    assert any(check.name == "minimum_resolution" and not check.passed for check in result.checks)


def test_extract_maintenance_run_id_from_response() -> None:
    result = EndpointResult(
        path="/maintenance_runs",
        ok=True,
        status_code=201,
        data={"data": {"id": "run-123"}},
    )

    assert _extract_body_id(result) == "run-123"


def test_extract_command_status_from_response() -> None:
    result = EndpointResult(
        path="/maintenance_runs/run-1/commands",
        ok=True,
        status_code=201,
        data={"data": {"id": "command-1", "status": "succeeded"}},
    )

    assert _extract_body_status(result) == "succeeded"


def test_protocol_runs_guard_requires_empty_run_list() -> None:
    empty = EndpointResult(path="/runs", ok=True, data={"data": []})
    nonempty = EndpointResult(path="/runs", ok=True, data={"data": [{"id": "run-1"}]})

    assert _has_protocol_runs(empty) is False
    assert _has_protocol_runs(nonempty) is True


def test_comment_command_body_is_no_motion_command() -> None:
    body = _comment_command_body(key="key-1", message="hello")

    assert body["data"]["commandType"] == "comment"
    assert body["data"]["key"] == "key-1"
    assert body["data"]["params"]["message"] == "hello"


def test_load_labware_command_body_references_fixture() -> None:
    body = _load_labware_command_body(
        key="key-1",
        slot="1",
        load_name="aevum_p300_poc_fixture",
        namespace="aevum",
        version=1,
        labware_id="labware-1",
        display_name="fixture",
    )

    assert body["data"]["commandType"] == "loadLabware"
    assert body["data"]["params"]["location"] == {"slotName": "1"}
    assert body["data"]["params"]["loadName"] == "aevum_p300_poc_fixture"
    assert body["data"]["params"]["labwareId"] == "labware-1"


def test_extract_command_result_field() -> None:
    result = EndpointResult(
        path="/maintenance_runs/run-1/commands",
        ok=True,
        data={"data": {"result": {"labwareId": "labware-1"}}},
    )

    assert _extract_command_result_field(result, "labwareId") == "labware-1"


def test_extract_definition_uri_from_summary_response() -> None:
    result = EndpointResult(
        path="/maintenance_runs/run-1/labware_definitions",
        ok=True,
        data={"data": {"definitionUri": "aevum/aevum_p300_poc_fixture/1"}},
    )

    assert _extract_definition_uri(result) == "aevum/aevum_p300_poc_fixture/1"


def test_compact_load_labware_result_removes_full_definition() -> None:
    result = EndpointResult(
        path="/maintenance_runs/run-1/commands",
        ok=True,
        data={
            "data": {
                "result": {
                    "labwareId": "fixture-1",
                    "definition": {
                        "namespace": "aevum",
                        "version": 1,
                        "parameters": {"loadName": "aevum_p300_poc_fixture"},
                        "dimensions": {"xDimension": 1, "yDimension": 2, "zDimension": 3},
                        "wells": {"A1": {}, "A2": {}},
                    },
                }
            }
        },
    )

    compacted = _compact_load_labware_result(result)
    definition = compacted.data["data"]["result"]["definition"]  # type: ignore[index]

    assert definition["loadName"] == "aevum_p300_poc_fixture"
    assert definition["well_count"] == 2
    assert "wells" not in definition
