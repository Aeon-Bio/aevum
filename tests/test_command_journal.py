from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import aevum_ot2.core.command_journal as command_journal_module
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.command_journal import (
    apply_and_persist_command_reconciliation_to_session,
    apply_command_reconciliation_to_session,
    dispatch_journaled_command,
    list_command_journal_entries,
    new_command_journal_entry,
    prepare_command_dispatch,
    read_command_journal_entry,
    reconcile_command_history,
    write_command_journal_entry,
)
from aevum_ot2.core.maintenance import _load_labware_command_body
from aevum_ot2.core.models import BridgeSession, BridgeSessionState, EndpointResult
from aevum_ot2.core.plans import PlanStep


def _session() -> BridgeSession:
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
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        pipette_model="p300_single_v2.1",
        pipette_id="pipette-1",
        pipette_tip_length_mm=51.7,
        state=BridgeSessionState.READY_NO_MOTION,
        created_at=now,
        updated_at=now,
        lease_expires_at=now + timedelta(minutes=10),
        maintenance_run_id="maintenance-run-1",
        slot="1",
        fixture_identity=identity,
        definition_uri="aevum/aevum_p300_poc_fixture/1",
        loaded_labware_id="fixture-1",
        last_command_id="command-1",
        last_command_status="succeeded",
        evidence_index_path="data/measurements/ot2_evidence_index.json",
    )


def _step() -> PlanStep:
    return PlanStep(
        step_id="home",
        operation="home",
    )


def _command_body(key: str = "key-1", labware_id: str = "fixture-1") -> dict[str, object]:
    return _load_labware_command_body(
        key=key,
        slot="1",
        load_name="aevum_p300_poc_fixture",
        namespace="aevum",
        version=1,
        labware_id=labware_id,
        display_name="Aevum fixture",
    )


def _command(
    *,
    command_id: str = "command-2",
    key: str = "key-1",
    status: str = "succeeded",
    labware_id: str = "fixture-1",
) -> dict[str, object]:
    data = _command_body(key=key, labware_id=labware_id)["data"]
    assert isinstance(data, dict)
    return {
        "id": command_id,
        "key": key,
        "commandType": data["commandType"],
        "params": data["params"],
        "status": status,
        "createdAt": "2026-05-05T00:00:00",
    }


def _history(*commands: dict[str, object], ok: bool = True) -> EndpointResult:
    return EndpointResult(
        path="/maintenance_runs/run-1/commands",
        ok=ok,
        data={"data": list(commands), "meta": {"totalLength": len(commands)}},
    )


class FakeTransport:
    def __init__(
        self,
        *,
        post_result: EndpointResult | None = None,
        history_result: EndpointResult | None = None,
    ) -> None:
        self.post_result = post_result or EndpointResult(
            path="/maintenance_runs/run-1/commands",
            ok=True,
            data={"data": _command()},
        )
        self.history_result = history_result or _history(_command())
        self.posts: list[tuple[str, dict[str, object]]] = []

    def post_json(
        self,
        path: str,
        body: dict[str, object] | list[object] | None = None,
    ) -> EndpointResult:
        assert isinstance(body, dict)
        self.posts.append((path, body))
        return self.post_result

    def get_json(self, path: str) -> EndpointResult:
        return self.history_result


def test_command_journal_persists_pre_dispatch_entry(tmp_path: Path) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
        journal_id="journal-1",
    )

    result = prepare_command_dispatch(entry, tmp_path / "state.sqlite3")

    assert result.persisted is True
    loaded = read_command_journal_entry("journal-1", tmp_path / "state.sqlite3")
    assert loaded is not None
    assert loaded.state == "prepared"
    assert loaded.command_type == "loadLabware"
    assert list_command_journal_entries("session-1", tmp_path / "state.sqlite3") == [
        loaded
    ]


def test_command_journal_unavailable_blocks_dispatch(tmp_path: Path) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )

    result = prepare_command_dispatch(entry, tmp_path)

    assert result.persisted is False
    assert result.entry is None
    assert "command journal unavailable" in result.blocker


def test_duplicate_command_key_blocks_second_pre_dispatch(tmp_path: Path) -> None:
    first = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(key="key-1"),
    )
    second = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(key="key-1"),
    )

    assert prepare_command_dispatch(first, tmp_path / "state.sqlite3").persisted is True
    result = prepare_command_dispatch(second, tmp_path / "state.sqlite3")

    assert result.persisted is False
    assert "duplicate command key" in result.blocker


def test_same_journal_id_retry_after_post_is_blocked(tmp_path: Path) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
        journal_id="journal-1",
    )
    posted = entry.model_copy(update={"state": "posted"})
    write_command_journal_entry(posted, tmp_path / "state.sqlite3")

    result = prepare_command_dispatch(entry, tmp_path / "state.sqlite3")

    assert result.persisted is False
    assert "already passed pre-dispatch" in result.blocker


def test_dispatch_helper_does_not_post_when_journal_is_unavailable(tmp_path: Path) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )
    transport = FakeTransport()

    result = dispatch_journaled_command(
        transport=transport,
        entry=entry,
        command_path="/maintenance_runs/run-1/commands",
        command_body=_command_body(),
        journal_path=tmp_path,
        history_path="/maintenance_runs/run-1/commands",
    )

    assert result.journal_persisted is False
    assert result.posted is False
    assert transport.posts == []


def test_dispatch_helper_requires_matching_command_and_history_routes(
    tmp_path: Path,
) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )
    transport = FakeTransport()

    missing_history = dispatch_journaled_command(
        transport=transport,
        entry=entry,
        command_path="/maintenance_runs/run-1/commands",
        command_body=_command_body(),
        journal_path=tmp_path / "state.sqlite3",
    )
    wrong_command = dispatch_journaled_command(
        transport=transport,
        entry=entry,
        command_path="/maintenance_runs/run-2/commands",
        command_body=_command_body(),
        journal_path=tmp_path / "state.sqlite3",
        history_path="/maintenance_runs/run-1/commands",
    )
    wrong_history = dispatch_journaled_command(
        transport=transport,
        entry=entry,
        command_path="/maintenance_runs/run-1/commands",
        command_body=_command_body(),
        journal_path=tmp_path / "state.sqlite3",
        history_path="/maintenance_runs/run-2/commands",
    )

    assert missing_history.posted is False
    assert "history path is required" in " ".join(missing_history.blockers)
    assert wrong_command.posted is False
    assert "command path run" in " ".join(wrong_command.blockers)
    assert wrong_history.posted is False
    assert "history path run" in " ".join(wrong_history.blockers)
    assert transport.posts == []


def test_dispatch_helper_rejects_protocol_run_command_routes(
    tmp_path: Path,
) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )
    transport = FakeTransport()

    result = dispatch_journaled_command(
        transport=transport,
        entry=entry,
        command_path="/runs/run-1/commands",
        command_body=_command_body(),
        journal_path=tmp_path / "state.sqlite3",
        history_path="/runs/run-1/commands",
    )

    assert result.posted is False
    assert "command path run" in " ".join(result.blockers)
    assert transport.posts == []


def test_dispatch_helper_rejects_body_that_does_not_match_journal(
    tmp_path: Path,
) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(key="key-1"),
    )
    transport = FakeTransport()

    result = dispatch_journaled_command(
        transport=transport,
        entry=entry,
        command_path="/maintenance_runs/run-1/commands",
        command_body=_command_body(key="key-2"),
        journal_path=tmp_path / "state.sqlite3",
        history_path="/maintenance_runs/run-1/commands",
    )

    assert result.posted is False
    assert "does not match journal entry" in " ".join(result.blockers)
    assert transport.posts == []


def test_dispatch_helper_rejects_non_prepared_journal_entry(tmp_path: Path) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    ).model_copy(update={"state": "posted"})
    transport = FakeTransport()

    result = dispatch_journaled_command(
        transport=transport,
        entry=entry,
        command_path="/maintenance_runs/run-1/commands",
        command_body=_command_body(),
        journal_path=tmp_path / "state.sqlite3",
        history_path="/maintenance_runs/run-1/commands",
    )

    assert result.posted is False
    assert "not prepared" in " ".join(result.blockers)
    assert transport.posts == []


def test_dispatch_helper_posts_only_after_journal_persists(tmp_path: Path) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
        journal_id="journal-1",
    )
    transport = FakeTransport()

    result = dispatch_journaled_command(
        transport=transport,
        entry=entry,
        command_path="/maintenance_runs/run-1/commands",
        command_body=_command_body(),
        journal_path=tmp_path / "state.sqlite3",
        history_path="/maintenance_runs/run-1/commands",
    )

    assert result.journal_persisted is True
    assert result.posted is True
    assert transport.posts == [("/maintenance_runs/run-1/commands", _command_body())]
    loaded = read_command_journal_entry("journal-1", tmp_path / "state.sqlite3")
    assert loaded is not None
    assert loaded.state == "completed"


def test_dispatch_helper_reports_post_dispatch_journal_write_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
        journal_id="journal-1",
    )
    transport = FakeTransport()
    real_write = command_journal_module.write_command_journal_entry
    writes = 0

    def flaky_write(entry, path) -> None:
        nonlocal writes
        writes += 1
        if writes >= 2:
            raise OSError("disk unavailable")
        real_write(entry, path)

    monkeypatch.setattr(command_journal_module, "write_command_journal_entry", flaky_write)

    result = dispatch_journaled_command(
        transport=transport,
        entry=entry,
        command_path="/maintenance_runs/run-1/commands",
        command_body=_command_body(),
        journal_path=tmp_path / "state.sqlite3",
        history_path="/maintenance_runs/run-1/commands",
    )

    assert result.posted is True
    assert result.journal_persisted is False
    assert "after dispatch" in " ".join(result.blockers)
    loaded = read_command_journal_entry("journal-1", tmp_path / "state.sqlite3")
    assert loaded is not None
    assert loaded.state == "dispatching"


def test_command_response_without_journal_entry_requires_recovery() -> None:
    result = reconcile_command_history(None, _history(_command()))

    assert result.recovery_required is True
    assert result.state == "recovery_required"
    assert "no matching journal" in " ".join(result.blockers)


def test_timeout_or_unavailable_history_never_blind_retries() -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )

    result = reconcile_command_history(entry, None)
    recovered = apply_command_reconciliation_to_session(_session(), result)

    assert result.recovery_required is True
    assert result.entry is not None
    assert result.entry.state == "recovery_required"
    assert recovered.state == BridgeSessionState.RECOVERY_REQUIRED
    assert recovered.motion_allowed is False


def test_recovery_required_reconciliation_can_be_persisted_with_session(
    tmp_path: Path,
) -> None:
    session = _session()
    entry = new_command_journal_entry(
        session=session,
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )
    result = reconcile_command_history(entry, None)

    recovered = apply_and_persist_command_reconciliation_to_session(
        session,
        result,
        tmp_path / "state.sqlite3",
    )

    from aevum_ot2.core.sessions import read_session

    loaded = read_session(session.session_id, tmp_path / "state.sqlite3")
    assert loaded is not None
    assert recovered.state == BridgeSessionState.RECOVERY_REQUIRED
    assert loaded.state == BridgeSessionState.RECOVERY_REQUIRED


def test_duplicate_command_key_is_non_idempotent_even_when_successful() -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )

    result = reconcile_command_history(
        entry,
        _history(
            _command(command_id="command-2", key="key-1"),
            _command(command_id="command-3", key="key-1"),
        ),
    )

    assert result.recovery_required is True
    assert result.non_idempotent_duplicate_key is True
    assert "duplicate command key" in " ".join(result.blockers)


def test_command_history_mismatch_does_not_infer_success() -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(labware_id="fixture-1"),
    )

    result = reconcile_command_history(
        entry,
        _history(_command(command_id="command-2", labware_id="other-fixture")),
    )

    assert result.recovery_required is True
    assert result.state == "recovery_required"
    assert "exactly one matching command" in " ".join(result.blockers)


def test_command_history_reconciles_server_normalized_params_after_post() -> None:
    command_body = {
        "data": {
            "commandType": "moveToWell",
            "key": "key-1",
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
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=command_body,
    ).model_copy(update={"command_id": "command-2"})
    normalized = {
        "id": "command-2",
        "key": "key-1",
        "commandType": "moveToWell",
        "params": {
            "pipetteId": "pipette-1",
            "labwareId": "fixture-1",
            "wellName": "A1",
            "wellLocation": {
                "origin": "top",
                "offset": {"x": 0.0, "y": 0.0, "z": 15.0},
                "volumeOffset": 0.0,
            },
            "minimumZHeight": 111.0,
            "forceDirect": False,
            "speed": 20.0,
        },
        "status": "succeeded",
        "createdAt": "2026-05-05T00:00:00",
    }

    result = reconcile_command_history(entry, _history(normalized))

    assert result.recovery_required is False
    assert result.state == "completed"
    assert result.matched_command_id == "command-2"
    assert result.entry is not None
    assert result.entry.blockers == []


def test_command_history_with_command_id_still_rejects_wrong_params() -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(labware_id="fixture-1"),
    ).model_copy(update={"command_id": "command-2"})

    result = reconcile_command_history(
        entry,
        _history(_command(command_id="command-2", labware_id="other-fixture")),
    )

    assert result.recovery_required is True
    assert "exactly one matching command" in " ".join(result.blockers)


def test_substring_run_id_match_cannot_complete_journal_entry() -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )
    history = _history(_command(command_id="command-2"))
    history.path = "/maintenance_runs/run-12/commands"

    result = reconcile_command_history(entry, history)

    assert result.recovery_required is True
    assert "run does not match" in " ".join(result.blockers)


def test_running_command_history_is_not_terminal_success() -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )

    result = reconcile_command_history(
        entry,
        _history(_command(command_id="command-2", status="running")),
    )

    assert result.recovery_required is True
    assert result.state == "recovery_required"
    assert "ambiguous" in " ".join(result.blockers)


def test_incomplete_command_history_page_requires_recovery() -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )
    history = _history(_command(command_id="command-2"))
    assert isinstance(history.data, dict)
    history.data["meta"] = {"totalLength": 2}

    result = reconcile_command_history(entry, history)

    assert result.recovery_required is True
    assert "incomplete" in " ".join(result.blockers)


def test_command_history_without_total_length_requires_recovery() -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
    )
    history = _history(_command(command_id="command-2"))
    assert isinstance(history.data, dict)
    history.data.pop("meta")

    result = reconcile_command_history(entry, history)

    assert result.recovery_required is True
    assert "incomplete" in " ".join(result.blockers)


def test_wrong_run_history_cannot_complete_journal_entry() -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-2",
        command_body=_command_body(),
    )

    result = reconcile_command_history(entry, _history(_command(command_id="command-2")))

    assert result.recovery_required is True
    assert "run does not match" in " ".join(result.blockers)


def test_matching_command_history_completes_journal_entry(tmp_path: Path) -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(),
        journal_id="journal-1",
    )

    result = reconcile_command_history(entry, _history(_command(command_id="command-2")))
    assert result.recovery_required is False
    assert result.entry is not None
    assert result.entry.state == "completed"
    assert result.entry.command_id == "command-2"
    assert result.entry.command_index == 0

    write_command_journal_entry(result.entry, tmp_path / "state.sqlite3")
    loaded = read_command_journal_entry("journal-1", tmp_path / "state.sqlite3")
    assert loaded is not None
    assert loaded.state == "completed"


def test_matching_command_history_reports_when_match_is_not_latest() -> None:
    entry = new_command_journal_entry(
        session=_session(),
        step=_step(),
        run_id="run-1",
        command_body=_command_body(key="key-1"),
    )

    result = reconcile_command_history(
        entry,
        _history(
            _command(command_id="command-2", key="key-1"),
            _command(command_id="command-3", key="other-key"),
        ),
    )

    assert result.recovery_required is False
    assert result.state == "completed"
    assert result.matched_command_id == "command-2"
    assert result.matched_command_index == 0
    assert result.command_history_total_length == 2
    assert result.matched_command_is_latest is False
