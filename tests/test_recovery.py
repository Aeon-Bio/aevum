from __future__ import annotations

from datetime import datetime, timedelta

import aevum_ot2.core.recovery as recovery_module
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.command_journal import (
    new_command_journal_entry,
    read_command_journal_entry,
    write_command_journal_entry,
)
from aevum_ot2.core.lock import read_lock, write_lock
from aevum_ot2.core.models import BridgeLock, BridgeSession, EndpointResult
from aevum_ot2.core.plans import PlanStep
from aevum_ot2.core.recovery import recover_no_motion_session
from aevum_ot2.core.sessions import read_session, write_session


def _session(state: str = "close_failed") -> BridgeSession:
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
        evidence_index_path="data/measurements/ot2_evidence_index.json",
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


def _seed_state(tmp_path, session: BridgeSession) -> object:
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


def test_recovery_marks_closed_when_maintenance_run_is_already_absent(
    tmp_path,
    monkeypatch,
) -> None:
    session = _session()
    db_path = _seed_state(tmp_path, session)
    _disable_evidence(monkeypatch)

    class MissingRunClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url
            self.timeout_seconds = timeout_seconds

        def get_json(self, path: str) -> EndpointResult:
            return EndpointResult(path=path, ok=False, status_code=404)

    monkeypatch.setattr(recovery_module, "Ot2Client", MissingRunClient)

    report = recover_no_motion_session(session.session_id, state_db_path=db_path)

    assert report.reconciled is True
    assert report.disposition == "recovered_closed"
    assert report.session_after is not None
    assert report.session_after.state == "closed"
    loaded = read_session(session.session_id, db_path)
    lock = read_lock(session.robot_url, db_path)
    assert loaded is not None and loaded.state == "closed"
    assert lock is not None and lock.state == "closed" and lock.active_run_id is None


def test_recovery_deletes_known_no_motion_maintenance_run(tmp_path, monkeypatch) -> None:
    session = _session()
    db_path = _seed_state(tmp_path, session)
    _disable_evidence(monkeypatch)

    class NoMotionRunClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url
            self.timeout_seconds = timeout_seconds
            self.deleted = False

        def get_json(self, path: str) -> EndpointResult:
            if path.startswith("/maintenance_runs/run-1/commands"):
                return EndpointResult(
                    path=path,
                    ok=True,
                    data={
                        "data": [{"commandType": "loadLabware"}],
                        "meta": {"totalLength": 1},
                    },
                )
            if self.deleted:
                return EndpointResult(path=path, ok=False, status_code=404)
            if path == "/maintenance_runs/run-1":
                return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})
            return EndpointResult(path=path, ok=False, status_code=404)

        def delete_json(self, path: str) -> EndpointResult:
            self.deleted = True
            return EndpointResult(path=path, ok=True, status_code=200, data={})

    monkeypatch.setattr(recovery_module, "Ot2Client", NoMotionRunClient)

    report = recover_no_motion_session(session.session_id, state_db_path=db_path)

    assert report.reconciled is True
    assert report.disposition == "recovered_closed"
    assert report.command_types == ["loadLabware"]
    assert report.session_after is not None
    assert report.session_after.state == "closed"


def test_recovery_deletes_known_home_commissioning_run(tmp_path, monkeypatch) -> None:
    session = _session(state="recovery_required")
    session.last_command_type = "home"
    session.last_command_status = "succeeded"
    db_path = _seed_state(tmp_path, session)
    _disable_evidence(monkeypatch)

    class HomedRunClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url
            self.timeout_seconds = timeout_seconds
            self.deleted = False

        def get_json(self, path: str) -> EndpointResult:
            if path.startswith("/maintenance_runs/run-1/commands"):
                return EndpointResult(
                    path=path,
                    ok=True,
                    data={
                        "data": [
                            {"commandType": "loadLabware"},
                            {"commandType": "home"},
                        ],
                        "meta": {"totalLength": 2},
                    },
                )
            if self.deleted:
                return EndpointResult(path=path, ok=False, status_code=404)
            if path == "/maintenance_runs/run-1":
                return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})
            return EndpointResult(path=path, ok=False, status_code=404)

        def delete_json(self, path: str) -> EndpointResult:
            self.deleted = True
            return EndpointResult(path=path, ok=True, status_code=200, data={})

    monkeypatch.setattr(recovery_module, "Ot2Client", HomedRunClient)

    report = recover_no_motion_session(session.session_id, state_db_path=db_path)

    assert report.reconciled is True
    assert report.disposition == "recovered_closed"
    assert report.command_types == ["loadLabware", "home"]
    assert report.unsafe_command_types == []
    assert report.session_after is not None
    assert report.session_after.state == "closed"


def test_recovery_requires_manual_action_for_unexpected_command_type(
    tmp_path,
    monkeypatch,
) -> None:
    session = _session()
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
                        "data": [{"commandType": "moveToWell"}],
                        "meta": {"totalLength": 1},
                    },
                )
            return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})

    monkeypatch.setattr(recovery_module, "Ot2Client", UnsafeRunClient)

    report = recover_no_motion_session(session.session_id, state_db_path=db_path)

    assert report.reconciled is False
    assert report.disposition == "unresolved_recovery"
    assert report.motion_commands_detected is True
    assert report.unsafe_command_types == ["moveToWell"]
    assert report.session_after is not None
    assert report.session_after.state == "recovery_required"


def test_recovery_reconciles_known_journaled_move_to_well_without_deleting_run(
    tmp_path,
    monkeypatch,
) -> None:
    session = _session(state="recovery_required")
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

    class JournaledMotionClient:
        deleted = False

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
                            {
                                "id": "pipette-command-1",
                                "commandType": "loadPipette",
                            },
                            _move_to_well_command(),
                        ],
                        "meta": {"totalLength": 3},
                    },
                )
            return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})

        def delete_json(self, path: str) -> EndpointResult:
            self.deleted = True
            return EndpointResult(path=path, ok=True, data={})

    monkeypatch.setattr(recovery_module, "Ot2Client", JournaledMotionClient)

    report = recover_no_motion_session(session.session_id, state_db_path=db_path)

    assert report.reconciled is True
    assert report.disposition == "recovered_active"
    assert report.motion_commands_detected is True
    assert report.unsafe_command_types == ["moveToWell"]
    assert report.session_after is not None
    assert report.session_after.state == "ready_no_motion"
    assert report.session_after.last_command_id == "move-command-1"
    lock = read_lock(session.robot_url, db_path)
    assert lock is not None
    assert lock.state == "active_no_motion"
    assert lock.last_command_id == "move-command-1"
    journal = read_command_journal_entry("move-journal-1", db_path)
    assert journal is not None
    assert journal.state == "completed"
    assert journal.command_index == 2


def test_recovery_requires_manual_action_for_incomplete_command_history(
    tmp_path,
    monkeypatch,
) -> None:
    session = _session()
    db_path = _seed_state(tmp_path, session)
    _disable_evidence(monkeypatch)

    class IncompleteHistoryClient:
        def __init__(self, robot_url: str, *, timeout_seconds: float) -> None:
            self.robot_url = robot_url
            self.timeout_seconds = timeout_seconds

        def get_json(self, path: str) -> EndpointResult:
            if path.startswith("/maintenance_runs/run-1/commands"):
                return EndpointResult(
                    path=path,
                    ok=True,
                    data={"data": [{"commandType": "loadLabware"}]},
                )
            return EndpointResult(path=path, ok=True, data={"data": {"id": "run-1"}})

    monkeypatch.setattr(recovery_module, "Ot2Client", IncompleteHistoryClient)

    report = recover_no_motion_session(session.session_id, state_db_path=db_path)

    assert report.reconciled is False
    assert report.disposition == "unresolved_recovery"
    assert report.session_after is not None
    assert report.session_after.state == "recovery_required"
    assert any("Command history is incomplete" in note for note in report.notes)


def test_recovery_reports_missing_local_session_as_non_destructive_noop(
    tmp_path,
    monkeypatch,
) -> None:
    _disable_evidence(monkeypatch)

    report = recover_no_motion_session(
        "missing-session",
        state_db_path=tmp_path / "state.sqlite3",
    )

    assert report.reconciled is False
    assert report.disposition == "no_local_session"
    assert report.session_before is None
    assert report.session_after is None
    assert "No local session record found." in report.notes
