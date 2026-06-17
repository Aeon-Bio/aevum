"""OT-3: physical-event / foreign-command invalidation primitive.

Proves detect_foreign_commands is a fail-closed whole-history scan, not a generic success
boolean: it flags ANY run-history command this bridge did not author — crucially including a
foreign command that executed BEFORE ours (the gap matched_command_is_latest cannot see) — and
fails closed on any history it cannot fully read. It withholds trust; it never grants motion.
"""

from __future__ import annotations

from aevum_ot2.core.command_journal import (
    MOTION_RELEVANT_COMMAND_TYPES,
    CommandJournalEntry,
    detect_foreign_commands,
)
from aevum_ot2.core.command_journal import (
    _stable_command_params_sha256 as _params_sha256,
)
from aevum_ot2.core.models import EndpointResult

RUN = "maintenance-run-1"
MOVE_PARAMS = {"labwareId": "fixture-1", "wellName": "A1"}


def _entry(
    *,
    key: str,
    command_type: str = "moveToWell",
    params: dict | None = None,
    run_id: str = RUN,
    command_id: str | None = None,
) -> CommandJournalEntry:
    params = MOVE_PARAMS if params is None else params
    return CommandJournalEntry(
        journal_id=f"journal-{key}",
        session_id="session-1",
        owner_id="agent-1",
        robot_url="http://ot2.local:31950",
        run_id=run_id,
        step_id="step",
        operation="move_high_z",
        command_key=key,
        command_type=command_type,
        command_body_sha256="body-sha-unused-by-matching",
        command_params_sha256=_params_sha256(command_type, params),
        command_id=command_id,
    )


def _cmd(
    *,
    id_: str,
    key: str,
    command_type: str = "moveToWell",
    params: dict | None = None,
    status: str = "succeeded",
) -> dict:
    params = MOVE_PARAMS if params is None else params
    return {
        "id": id_,
        "key": key,
        "commandType": command_type,
        "params": params,
        "status": status,
        "createdAt": "2026-06-17T00:00:00",
    }


def _history(
    commands: list[dict],
    *,
    run_id: str = RUN,
    total: int | None = None,
) -> EndpointResult:
    return EndpointResult(
        path=f"/maintenance_runs/{run_id}/commands",
        ok=True,
        data={
            "data": commands,
            "meta": {"totalLength": len(commands) if total is None else total},
        },
    )


# --- the clean path -----------------------------------------------------------------------


def test_history_fully_authored_is_not_invalidated() -> None:
    # Robot-assigned ids differ from our id-less prepared entries; matching is by
    # key+type+params, so a clean post-execution history is still fully ours.
    entries = [
        _entry(key="k1"),
        _entry(key="k2", params={"labwareId": "fixture-1", "wellName": "B1"}),
    ]
    history = _history(
        [
            _cmd(id_="robot-1", key="k1"),
            _cmd(id_="robot-2", key="k2", params={"labwareId": "fixture-1", "wellName": "B1"}),
        ]
    )
    verdict = detect_foreign_commands(authored_entries=entries, command_history=history, run_id=RUN)
    assert verdict.invalidated is False
    assert verdict.foreign_commands == []
    assert verdict.history_total_length == 2
    assert verdict.blockers == []


def test_empty_history_is_clean() -> None:
    verdict = detect_foreign_commands(
        authored_entries=[_entry(key="k1")], command_history=_history([]), run_id=RUN
    )
    assert verdict.invalidated is False
    assert verdict.history_total_length == 0


# --- the headline gap: a foreign command BEFORE ours ---------------------------------------


def test_foreign_command_before_ours_invalidates() -> None:
    # Our command is the LATEST (matched_command_is_latest would be True), yet a foreign
    # touchscreen jog ran first and moved the robot. is_latest cannot see this; OT-3 does.
    history = _history(
        [
            _cmd(id_="touchscreen-jog", key="not-ours", command_type="moveRelative"),
            _cmd(id_="robot-1", key="k1"),
        ]
    )
    verdict = detect_foreign_commands(
        authored_entries=[_entry(key="k1")], command_history=history, run_id=RUN
    )
    assert verdict.invalidated is True
    assert [f.index for f in verdict.foreign_commands] == [0]
    foreign = verdict.foreign_commands[0]
    assert foreign.command_id == "touchscreen-jog"
    assert foreign.reason == "unauthored_command_key"
    assert foreign.motion_relevant is True


def test_foreign_command_after_ours_invalidates() -> None:
    history = _history(
        [
            _cmd(id_="robot-1", key="k1"),
            _cmd(id_="intruder", key="not-ours", command_type="aspirate", params={"flowRate": 1}),
        ]
    )
    verdict = detect_foreign_commands(
        authored_entries=[_entry(key="k1")], command_history=history, run_id=RUN
    )
    assert verdict.invalidated is True
    assert [f.index for f in verdict.foreign_commands] == [1]
    assert verdict.foreign_commands[0].reason == "unauthored_command_key"


# --- forged / replayed idempotency key (id/params divergence under our key) ----------------


def test_key_reuse_with_id_mismatch_is_foreign() -> None:
    # An entry whose id we already learned; a second history command reuses the key with a
    # different id -> a replay/forge, distinct from a wholly unknown key.
    entry = _entry(key="k1", command_id="robot-1")
    history = _history(
        [
            _cmd(id_="robot-1", key="k1"),  # the genuine, matched command
            _cmd(id_="forged", key="k1"),  # same key, different id
        ]
    )
    verdict = detect_foreign_commands(
        authored_entries=[entry], command_history=history, run_id=RUN
    )
    assert verdict.invalidated is True
    assert [f.index for f in verdict.foreign_commands] == [1]
    assert verdict.foreign_commands[0].reason == "authored_key_reuse_mismatch"


def test_params_divergence_under_authored_key_is_foreign() -> None:
    history = _history(
        [_cmd(id_="robot-1", key="k1", params={"labwareId": "fixture-1", "wellName": "H12"})]
    )
    verdict = detect_foreign_commands(
        authored_entries=[_entry(key="k1")], command_history=history, run_id=RUN
    )
    assert verdict.invalidated is True
    assert verdict.foreign_commands[0].reason == "authored_key_reuse_mismatch"


# --- run scoping --------------------------------------------------------------------------


def test_authored_entry_for_other_run_does_not_account_for_this_run() -> None:
    # Authored entries are filtered to run_id; an entry from another run cannot vouch for a
    # command in this run, so the command is foreign (fail-closed on cross-run vouching).
    entries = [_entry(key="k1", run_id="some-other-run")]
    history = _history([_cmd(id_="robot-1", key="k1")])
    verdict = detect_foreign_commands(authored_entries=entries, command_history=history, run_id=RUN)
    assert verdict.invalidated is True
    assert verdict.foreign_commands[0].reason == "unauthored_command_key"


# --- fail-closed on unreadable history ----------------------------------------------------


def test_history_none_fails_closed() -> None:
    verdict = detect_foreign_commands(authored_entries=[], command_history=None, run_id=RUN)
    assert verdict.invalidated is True
    assert verdict.blockers == ["command_history_unavailable"]
    assert verdict.foreign_commands == []


def test_history_not_ok_fails_closed() -> None:
    bad = EndpointResult(path=f"/maintenance_runs/{RUN}/commands", ok=False, data={"data": []})
    verdict = detect_foreign_commands(authored_entries=[], command_history=bad, run_id=RUN)
    assert verdict.invalidated is True
    assert verdict.blockers == ["command_history_unavailable"]


def test_history_malformed_fails_closed() -> None:
    malformed = EndpointResult(
        path=f"/maintenance_runs/{RUN}/commands", ok=True, data={"data": [123]}
    )
    verdict = detect_foreign_commands(authored_entries=[], command_history=malformed, run_id=RUN)
    assert verdict.invalidated is True
    assert verdict.blockers == ["command_history_malformed"]


def test_history_incomplete_fails_closed() -> None:
    incomplete = _history([_cmd(id_="robot-1", key="k1")], total=5)  # totalLength > present
    verdict = detect_foreign_commands(
        authored_entries=[_entry(key="k1")], command_history=incomplete, run_id=RUN
    )
    assert verdict.invalidated is True
    assert verdict.blockers == ["command_history_incomplete"]


def test_history_run_mismatch_fails_closed() -> None:
    other = _history([_cmd(id_="robot-1", key="k1")], run_id="a-different-run")
    verdict = detect_foreign_commands(
        authored_entries=[_entry(key="k1")], command_history=other, run_id=RUN
    )
    assert verdict.invalidated is True
    assert verdict.blockers == ["command_history_run_mismatch"]


# --- motion-relevance classification (informational, does not gate invalidated) -----------


def test_non_motion_foreign_still_invalidates_but_is_not_motion_relevant() -> None:
    history = _history(
        [_cmd(id_="x", key="not-ours", command_type="loadLabware", params={"namespace": "x"})]
    )
    verdict = detect_foreign_commands(authored_entries=[], command_history=history, run_id=RUN)
    assert verdict.invalidated is True  # any foreign command fails closed
    assert verdict.foreign_commands[0].motion_relevant is False
    assert verdict.motion_relevant_foreign == []


# --- 1:1 cardinality: a single authored entry cannot vouch for duplicate executions --------
# (regression for the adversarial-review blocker: `any(_matches_entry)` let one entry absorb
# unlimited matching history rows, so a replayed physical move read as invalidated=False.)


def test_duplicate_executions_of_our_key_invalidate() -> None:
    history = _history([_cmd(id_=f"robot-{i}", key="k1") for i in range(4)])
    verdict = detect_foreign_commands(
        authored_entries=[_entry(key="k1")], command_history=history, run_id=RUN
    )
    assert verdict.invalidated is True
    assert [f.index for f in verdict.foreign_commands] == [1, 2, 3]  # first row is ours
    assert {f.reason for f in verdict.foreign_commands} == {"non_idempotent_duplicate_key"}
    assert all(f.motion_relevant for f in verdict.foreign_commands)  # moveToWell re-ran


def test_duplicate_executions_under_id_bearing_entry_invalidate() -> None:
    # An entry whose id we already learned cannot vouch for three rows carrying that id.
    entry = _entry(key="k1", command_id="robot-1")
    history = _history([_cmd(id_="robot-1", key="k1") for _ in range(3)])
    verdict = detect_foreign_commands(
        authored_entries=[entry], command_history=history, run_id=RUN
    )
    assert verdict.invalidated is True
    assert [f.index for f in verdict.foreign_commands] == [1, 2]
    assert {f.reason for f in verdict.foreign_commands} == {"non_idempotent_duplicate_key"}


def test_failed_then_replayed_success_invalidates() -> None:
    # Our move FAILED; a replay under the same key SUCCEEDED -> the robot moved on the retry.
    # Status is not compared per-command (shared _matches_entry); the 1:1 pass is what catches it.
    history = _history(
        [
            _cmd(id_="robot-1", key="k1", status="failed"),
            _cmd(id_="robot-2", key="k1", status="succeeded"),
        ]
    )
    verdict = detect_foreign_commands(
        authored_entries=[_entry(key="k1")], command_history=history, run_id=RUN
    )
    assert verdict.invalidated is True
    assert [f.index for f in verdict.foreign_commands] == [1]
    assert verdict.foreign_commands[0].reason == "non_idempotent_duplicate_key"


def test_n_authored_vs_n_distinct_history_stays_clean() -> None:
    # The symmetric direction: equal counts of distinct-key commands must NOT over-flag.
    entries = [
        _entry(key=f"k{i}", params={"labwareId": "fixture-1", "wellName": f"A{i}"})
        for i in range(3)
    ]
    history = _history(
        [
            _cmd(
                id_=f"robot-{i}",
                key=f"k{i}",
                params={"labwareId": "fixture-1", "wellName": f"A{i}"},
            )
            for i in range(3)
        ]
    )
    verdict = detect_foreign_commands(authored_entries=entries, command_history=history, run_id=RUN)
    assert verdict.invalidated is False
    assert verdict.foreign_commands == []


def test_motion_relevant_foreign_filters_to_movers() -> None:
    history = _history(
        [
            _cmd(id_="r1", key="k1"),  # ours
            _cmd(id_="r2", key="load", command_type="loadPipette", params={"mount": "left"}),
            _cmd(id_="r3", key="jog", command_type="moveToCoordinates", params={"x": 1}),
        ]
    )
    verdict = detect_foreign_commands(
        authored_entries=[_entry(key="k1")], command_history=history, run_id=RUN
    )
    assert verdict.invalidated is True
    foreign_types = {f.command_type for f in verdict.foreign_commands}
    assert foreign_types == {"loadPipette", "moveToCoordinates"}
    assert [f.command_type for f in verdict.motion_relevant_foreign] == ["moveToCoordinates"]
    assert "moveToCoordinates" in MOTION_RELEVANT_COMMAND_TYPES
