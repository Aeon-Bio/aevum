from __future__ import annotations

import ast
import inspect
from datetime import datetime, timedelta

import aevum_ot2.core.abort_recover as abort_recover_module
import aevum_ot2.core.recovery as recovery_module
from aevum_ot2.core.abort_recover import (
    AbortOrRecoverReport,
    RequiredRecoveryAction,
    ot2_abort_or_recover,
)
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.command_journal import (
    new_command_journal_entry,
    write_command_journal_entry,
)
from aevum_ot2.core.lock import write_lock
from aevum_ot2.core.models import BridgeLock, BridgeSession, EndpointResult, EvidenceEvent
from aevum_ot2.core.plans import PlanStep
from aevum_ot2.core.sessions import write_session


def _session(state: str = "recovery_required", *, evidence_index_path: str) -> BridgeSession:
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
        maintenance_run_id="run-1",
        slot="1",
        fixture_identity=identity,
        definition_uri="aevum/aevum_p300_poc_fixture/1",
        loaded_labware_id="fixture-1",
        last_command_id="command-1",
        last_command_key="command-key-1",
        evidence_index_path=evidence_index_path,
    )


def _lock(session: BridgeSession) -> BridgeLock:
    now = datetime.now()
    return BridgeLock(
        robot_url=session.robot_url,
        session_id=session.session_id,
        owner_id=session.owner_id,
        lease_started_at=now,
        lease_expires_at=now + timedelta(minutes=10),
        active_run_id=session.maintenance_run_id,
        last_command_id=session.last_command_id,
        state="recovery_required",
    )


def _seed_state(tmp_path, session: BridgeSession):
    db_path = tmp_path / "state.sqlite3"
    write_session(session, db_path)
    write_lock(_lock(session), db_path)
    return db_path


def _move_to_well_body(key: str = "move-key") -> dict[str, object]:
    return {
        "data": {
            "commandType": "moveToWell",
            "key": key,
            "params": {
                "pipetteId": "pipette-1",
                "labwareId": "fixture-1",
                "wellName": "A1",
                "wellLocation": {
                    "origin": "top",
                    "offset": {"x": 0.0, "y": 0.0, "z": 15.0},
                },
                "minimumZHeight": 111.0,
                "forceDirect": False,
                "speed": 20.0,
            },
        }
    }


def _move_to_well_command(key: str = "move-key") -> dict[str, object]:
    body = _move_to_well_body(key)
    data = body["data"]
    assert isinstance(data, dict)
    params = data["params"]
    assert isinstance(params, dict)
    well_location = dict(params["wellLocation"])
    assert isinstance(well_location, dict)
    well_location["volumeOffset"] = 0.0
    normalized_params = dict(params)
    normalized_params["wellLocation"] = well_location
    return {
        "id": "move-command-1",
        "key": key,
        "commandType": "moveToWell",
        "status": "succeeded",
        "params": normalized_params,
    }


def _disable_evidence(monkeypatch) -> None:
    monkeypatch.setattr(recovery_module, "append_evidence_event", lambda event, **kwargs: None)


def test_abort_recover_projects_recovered_closed_with_no_action(tmp_path, monkeypatch) -> None:
    evidence_index = tmp_path / "evidence_index.json"
    session = _session(state="close_failed", evidence_index_path=str(evidence_index))
    db_path = _seed_state(tmp_path, session)
    _disable_evidence(monkeypatch)

    class MissingRunClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url
            self.timeout_seconds = timeout_seconds

        def get_json(self, path: str) -> EndpointResult:
            return EndpointResult(path=path, ok=False, status_code=404)

    monkeypatch.setattr(recovery_module, "Ot2Client", MissingRunClient)

    report = ot2_abort_or_recover(session.session_id, state_db_path=db_path)

    assert isinstance(report, AbortOrRecoverReport)
    assert report.disposition == "recovered_closed"
    assert report.recovery_state == "closed"
    assert report.required_action == RequiredRecoveryAction.NONE
    assert report.motion_allowed is False
    assert report.owning_session_id == "session-1"
    assert report.last_command_key == "command-key-1"
    assert report.last_command_id == "command-1"
    assert report.latest_recovery_image_handle is None
    assert report.recovery_report.disposition == "recovered_closed"


def test_abort_recover_projects_recovered_active_requires_camera_evidence(
    tmp_path,
    monkeypatch,
) -> None:
    evidence_index = tmp_path / "evidence_index.json"
    session = _session(state="recovery_required", evidence_index_path=str(evidence_index))
    session.pipette_name = "p300_single_gen2"
    session.pipette_mount = "left"
    session.pipette_id = "pipette-1"
    session.last_command_id = "pipette-command-1"
    session.last_command_type = "loadPipette"
    session.last_command_status = "succeeded"
    db_path = _seed_state(tmp_path, session)
    entry = new_command_journal_entry(
        session=session,
        step=PlanStep(
            step_id="center-high-z",
            operation="move_high_z",
            target_class="center_high_z",
        ),
        run_id="run-1",
        command_body=_move_to_well_body(),
        journal_id="move-journal-1",
    )
    write_command_journal_entry(entry, db_path)
    _disable_evidence(monkeypatch)

    # Seed a camera image into the session evidence index for the read-only handle lookup.
    image_path = tmp_path / "recovery.jpg"
    image_path.write_bytes(b"image-bytes")
    from aevum_ot2.core.evidence import append_evidence_event

    append_evidence_event(
        EvidenceEvent(
            event_type="ot2_camera_picture",
            session_id="session-1",
            summary="recovery image",
            payload={"image_path": str(image_path)},
        ),
        path=evidence_index,
    )

    class JournaledMotionClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url
            self.timeout_seconds = timeout_seconds

        def get_json(self, path: str) -> EndpointResult:
            if path.startswith("/maintenance_runs/run-1/commands"):
                return EndpointResult(
                    path=path,
                    ok=True,
                    data={
                        "data": [
                            {"id": "load-command-1", "commandType": "loadLabware"},
                            {"id": "pipette-command-1", "commandType": "loadPipette"},
                            _move_to_well_command(),
                        ],
                        "meta": {"totalLength": 3},
                    },
                )
            return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})

        def delete_json(self, path: str) -> EndpointResult:
            raise AssertionError("recovered-active path must not delete the run")

    monkeypatch.setattr(recovery_module, "Ot2Client", JournaledMotionClient)

    report = ot2_abort_or_recover(session.session_id, state_db_path=db_path)

    assert report.disposition == "recovered_active"
    assert report.recovery_state == "ready_no_motion"
    assert report.required_action == RequiredRecoveryAction.CAPTURE_CAMERA_EVIDENCE
    assert report.motion_allowed is False
    assert report.last_command_id == "move-command-1"
    assert report.latest_recovery_image_handle == str(image_path)


def test_abort_recover_projects_unresolved_with_motion_disallowed(tmp_path, monkeypatch) -> None:
    evidence_index = tmp_path / "evidence_index.json"
    session = _session(state="recovery_required", evidence_index_path=str(evidence_index))
    db_path = _seed_state(tmp_path, session)
    _disable_evidence(monkeypatch)

    class UnsafeRunClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url
            self.timeout_seconds = timeout_seconds

        def get_json(self, path: str) -> EndpointResult:
            if path.startswith("/maintenance_runs/run-1/commands"):
                return EndpointResult(
                    path=path,
                    ok=True,
                    data={
                        "data": [{"commandType": "aspirate"}],
                        "meta": {"totalLength": 1},
                    },
                )
            return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})

    monkeypatch.setattr(recovery_module, "Ot2Client", UnsafeRunClient)

    report = ot2_abort_or_recover(session.session_id, state_db_path=db_path)

    assert report.disposition == "unresolved_recovery"
    assert report.recovery_state == "recovery_required"
    assert report.required_action == RequiredRecoveryAction.SUPERVISED_RECOVERY
    assert report.motion_allowed is False


def test_abort_recover_no_local_session_escalates_to_supervised(tmp_path, monkeypatch) -> None:
    _disable_evidence(monkeypatch)

    report = ot2_abort_or_recover(
        "missing-session",
        state_db_path=tmp_path / "state.sqlite3",
    )

    assert report.disposition == "no_local_session"
    assert report.required_action == RequiredRecoveryAction.SUPERVISED_RECOVERY
    assert report.motion_allowed is False
    assert report.owning_session_id == "missing-session"
    assert report.latest_recovery_image_handle is None


def test_abort_recover_facade_never_calls_post_or_delete_json() -> None:
    """Boundary: the facade module must not itself reach the robot transport.

    The only allowlisted DELETE lives in aevum_ot2.core.recovery; the facade is a
    projection plus read-only lookups. Asserting on the source guards against a future
    edit smuggling motion authority into the agent-facing path.
    """

    # AST-based so prose explaining the boundary cannot false-positive AND a smuggled call
    # cannot hide behind tokenizer spacing: assert no Attribute call named post_json/
    # delete_json and no reference to Ot2Client anywhere in the facade module.
    tree = ast.parse(inspect.getsource(abort_recover_module))
    called = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "post_json" not in called
    assert "delete_json" not in called
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    imported = {
        alias.asname or alias.name.split(".")[-1]
        for n in ast.walk(tree)
        if isinstance(n, (ast.Import, ast.ImportFrom))
        for alias in n.names
    }
    assert "Ot2Client" not in names
    assert "Ot2Client" not in imported
