"""OT-1: transaction-backed offset authority — the safety core.

Proves the fail-closed JOIN in promoted_offset_record: a scope-valid offset claim + the
COMMITTED OT-6 high_z_motion_completed claim + a LIVE command-journal re-reconcile + the
(currently-empty) calibrated-source allowlist. With the allowlist empty, an operator-attested
offset can be RECORDED but never PROMOTED — and a monkeypatched allowlist proves the machinery
is correct and only gated.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from aevum_ot2.core import offset_evidence as oe
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.command_journal import (
    new_command_journal_entry,
    prepare_command_dispatch,
)
from aevum_ot2.core.evidence import commit_evidence_transaction, load_committed_evidence_claims
from aevum_ot2.core.evidence_primitives import _transaction_root_for_index
from aevum_ot2.core.models import (
    BridgeSession,
    EndpointResult,
    EvidenceClaim,
    EvidenceHandle,
    EvidencePacket,
    EvidenceQuality,
    EvidenceSourceKind,
    OffsetAuthorityState,
    OffsetRecord,
)
from aevum_ot2.core.plans import PlanStep
from aevum_ot2.core.records import (
    HIGH_Z_MOTION_EVIDENCE_METHOD,
    high_z_motion_completed_claim_id,
    high_z_motion_completed_claim_type,
    offset_measured_claim_type,
)
from aevum_ot2.core.registry import (
    load_offset_registry,
    offset_record_id,
    promote_offset_record_in_registry,
)

TARGET = "center_high_z"
NOW = datetime(2026, 6, 17, 12, 0, 0)


def _session(tmp_path: Path) -> BridgeSession:
    identity = current_fixture_identity()
    now = datetime.now() - timedelta(minutes=1)
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
        state="high_z_ready",
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
        evidence_index_path=str(tmp_path / "sessions/session-1/evidence_index.json"),
    )


def _proposed_record(session: BridgeSession, *, journal_id: str) -> OffsetRecord:
    identity = session.fixture_identity
    return OffsetRecord(
        robot_serial=session.robot_serial or "",
        robot_server_version=session.robot_server_version,
        opentrons_api_version=session.max_protocol_api_version,
        fixture_load_name=identity.load_name,
        fixture_definition_uri=session.definition_uri or "",
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        pose_digest_sha256=session.fixture_pose_digest_sha256,
        slot=session.slot,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        tiprack_load_name="opentrons_96_tiprack_300ul",
        offset_mm={"x": 0.12, "y": -0.34, "z": 0.0},
        verification_targets=[TARGET],
        evidence_file="data/measurements/offsets/proposed.json",
        offset_source="operator_attested_jog",
        high_z_journal_id=journal_id,
    )


def _commit_high_z_claim(session: BridgeSession) -> None:
    # Land a scope-valid, USABLE high_z_motion_completed claim in the session's committed store.
    identity = session.fixture_identity
    handle = EvidenceHandle(
        evidence_id="hz-frame",
        source_kind=EvidenceSourceKind.HIGH_Z_LANDING,
        quality=EvidenceQuality.USABLE,
    )
    packet = EvidencePacket(
        evidence_id="hz-frame",
        source_kind=EvidenceSourceKind.HIGH_Z_LANDING,
        session_id=session.session_id,
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        pose_digest_sha256=session.fixture_pose_digest_sha256,
        operation="move_high_z",
        quality=EvidenceQuality.USABLE,
        payload={"value": True},
    )
    claim = EvidenceClaim(
        claim_id=high_z_motion_completed_claim_id(TARGET, "hz-frame"),
        claim_type=high_z_motion_completed_claim_type(TARGET),
        value=True,
        session_id=session.session_id,
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        pose_digest_sha256=session.fixture_pose_digest_sha256,
        method=HIGH_Z_MOTION_EVIDENCE_METHOD,
        quality=EvidenceQuality.USABLE,
        evidence=[handle],
    )
    index_path = Path(session.evidence_index_path)
    commit_evidence_transaction(
        packets=[packet],
        claims=[claim],
        index_path=index_path,
        root=_transaction_root_for_index(index_path),
        transaction_id="txn-hz",
        session_id=session.session_id,
    )


def _persist_journal(session: BridgeSession, db_path: Path) -> tuple[str, EndpointResult]:
    run_id = session.maintenance_run_id or "maintenance-run-1"
    command_body = {
        "data": {
            "key": "hz-key",
            "commandType": "moveToWell",
            "params": {"labwareId": "fixture-1", "wellName": "A1"},
        }
    }
    entry = new_command_journal_entry(
        session=session,
        step=PlanStep(step_id="hz", operation="move_high_z"),
        run_id=run_id,
        command_body=command_body,
        journal_id="hz-journal-1",
    )
    assert prepare_command_dispatch(entry, db_path).persisted is True
    command = {
        "id": "hz-cmd-1",
        "key": "hz-key",
        "commandType": "moveToWell",
        "params": {"labwareId": "fixture-1", "wellName": "A1"},
        "status": "succeeded",
        "createdAt": "2026-06-17T00:00:00",
    }
    history = EndpointResult(
        path=f"/maintenance_runs/{run_id}/commands",
        ok=True,
        data={"data": [command], "meta": {"totalLength": 1}},
    )
    return "hz-journal-1", history


def _committed_offset_claims(
    session: BridgeSession, record: OffsetRecord, tmp_path: Path
) -> list[EvidenceClaim]:
    artifact = oe.build_offset_evidence_artifact(
        record,
        session=session,
        artifact_id="offset-artifact-1",
        offset_source=record.offset_source,
        inspection_note="operator jogged to well center; offset read off the deck",
        high_z_journal_id=record.high_z_journal_id,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = oe.write_offset_evidence_artifact(
        artifact, tmp_path / "sessions/session-1/offset_evidence.json"
    )
    packets = oe.offset_evidence_packets_from_artifact(
        record, artifact, session=session, artifact_path=artifact_path
    )
    # Commit the offset evidence into the session store (recording the attested offset), then
    # hand the COMMITTED offset claims to promote.
    oe.commit_offset_claims(record, packets, session=session, transaction_id="txn-offset")
    committed = load_committed_evidence_claims(
        index_path=Path(session.evidence_index_path),
        root=_transaction_root_for_index(Path(session.evidence_index_path)),
    )
    return [c for c in committed if c.claim_type == offset_measured_claim_type(TARGET)]


def _full_setup(tmp_path: Path):
    session = _session(tmp_path)
    db_path = tmp_path / "state.sqlite3"
    journal_id, history = _persist_journal(session, db_path)
    record = _proposed_record(session, journal_id=journal_id)
    _commit_high_z_claim(session)
    offset_claims = _committed_offset_claims(session, record, tmp_path)
    return session, record, offset_claims, history, db_path


# --- validator ----------------------------------------------------------------------------


def test_offset_mm_must_be_finite_with_xyz_keys(tmp_path: Path) -> None:
    session = _session(tmp_path)
    with pytest.raises(ValueError, match="finite"):
        oe.OffsetEvidenceArtifact(
            artifact_id="a", session_id=session.session_id,
            fixture_load_name="f", fixture_params_sha256="p", labware_definition_sha256="l",
            slot="1", target_class=TARGET,
            offset_mm={"x": float("inf"), "y": 0.0, "z": 0.0}, offset_source="x",
        )
    with pytest.raises(ValueError, match="keys x, y, z"):
        oe.OffsetEvidenceArtifact(
            artifact_id="a", session_id=session.session_id,
            fixture_load_name="f", fixture_params_sha256="p", labware_definition_sha256="l",
            slot="1", target_class=TARGET, offset_mm={"x": 0.0, "y": 0.0}, offset_source="x",
        )


def test_usable_requires_note_source_and_journal_binding(tmp_path: Path) -> None:
    session = _session(tmp_path)
    base = dict(
        artifact_id="a", session_id=session.session_id, fixture_load_name="f",
        fixture_params_sha256="p", labware_definition_sha256="l", slot="1",
        target_class=TARGET, offset_mm={"x": 0.0, "y": 0.0, "z": 0.0},
        quality=EvidenceQuality.USABLE,
    )
    with pytest.raises(ValueError, match="offset_source"):
        oe.OffsetEvidenceArtifact(
            **base, offset_source="", inspection_note="n", high_z_journal_id="j"
        )
    with pytest.raises(ValueError, match="inspection note"):
        oe.OffsetEvidenceArtifact(
            **base, offset_source="s", inspection_note="", high_z_journal_id="j"
        )
    with pytest.raises(ValueError, match="high_z_journal_id"):
        oe.OffsetEvidenceArtifact(
            **base, offset_source="s", inspection_note="n", high_z_journal_id=""
        )


# --- evidence records (commit works) ------------------------------------------------------


def test_offset_evidence_commits_and_claim_appears(tmp_path: Path) -> None:
    session, record, offset_claims, _history, _db = _full_setup(tmp_path)
    assert offset_claims[0].value is True
    assert offset_claims[0].quality == EvidenceQuality.USABLE
    committed = load_committed_evidence_claims(
        index_path=Path(session.evidence_index_path),
        root=_transaction_root_for_index(Path(session.evidence_index_path)),
    )
    assert any(c.claim_type == offset_measured_claim_type(TARGET) for c in committed)


# --- THE HEADLINE: promotion blocked by uncalibrated source -------------------------------


def test_promotion_blocked_by_uncalibrated_source(tmp_path: Path) -> None:
    session, record, offset_claims, history, db = _full_setup(tmp_path)
    # Everything else is valid (committed OT-6 claim, live journal reconciles, scope matches).
    assert oe.CALIBRATED_OFFSET_SOURCES == frozenset()  # empty by design
    with pytest.raises(ValueError, match="offset_source_not_calibrated"):
        oe.promoted_offset_record(
            record, session=session,
            command_history=history, command_journal_path=db, now=NOW,
        )


def test_machinery_promotes_when_source_is_calibrated(tmp_path: Path, monkeypatch) -> None:
    # Prove the pipeline is CORRECT and only gated: open the allowlist for the test source.
    session, record, offset_claims, history, db = _full_setup(tmp_path)
    monkeypatch.setattr(
        oe, "CALIBRATED_OFFSET_SOURCES", frozenset({"operator_attested_jog"})
    )
    promoted = oe.promoted_offset_record(
            record, session=session,
        command_history=history, command_journal_path=db, now=NOW,
    )
    assert promoted.authority_state == OffsetAuthorityState.PROMOTED
    assert TARGET in promoted.verification_targets
    # id is a scope hash (excludes authority_state) -> unchanged by promotion
    assert offset_record_id(promoted) == offset_record_id(record)


# --- fail-closed: each join member is load-bearing ----------------------------------------


def test_missing_committed_high_z_claim_blocks(tmp_path: Path, monkeypatch) -> None:
    # No committed OT-6 claim -> blocked even with a calibrated source.
    session = _session(tmp_path)
    db = tmp_path / "state.sqlite3"
    journal_id, history = _persist_journal(session, db)
    record = _proposed_record(session, journal_id=journal_id)
    # commits the offset evidence but NOT a high-Z claim (side effect: lands the offset claim)
    _committed_offset_claims(session, record, tmp_path)
    monkeypatch.setattr(oe, "CALIBRATED_OFFSET_SOURCES", frozenset({"operator_attested_jog"}))
    with pytest.raises(ValueError, match="missing_committed_high_z_motion_claim"):
        oe.promoted_offset_record(
            record, session=session,
            command_history=history, command_journal_path=db, now=NOW,
        )


def test_live_journal_entry_missing_blocks(tmp_path: Path, monkeypatch) -> None:
    session, record, offset_claims, history, db = _full_setup(tmp_path)
    monkeypatch.setattr(oe, "CALIBRATED_OFFSET_SOURCES", frozenset({"operator_attested_jog"}))
    # point at a journal id that was never persisted
    bad = record.model_copy(update={"high_z_journal_id": "no-such-journal"})
    with pytest.raises(ValueError, match="high_z_command_journal_entry_missing"):
        oe.promoted_offset_record(
            bad, session=session,
            command_history=history, command_journal_path=db, now=NOW,
        )


def test_no_live_history_blocks(tmp_path: Path, monkeypatch) -> None:
    session, record, offset_claims, _history, db = _full_setup(tmp_path)
    monkeypatch.setattr(oe, "CALIBRATED_OFFSET_SOURCES", frozenset({"operator_attested_jog"}))
    # command_history=None -> reconcile ambiguous -> fail closed (needs a live re-prove)
    with pytest.raises(ValueError, match="high_z_command_not_reconciled_live"):
        oe.promoted_offset_record(
            record, session=session,
            command_history=None, command_journal_path=db, now=NOW,
        )


def test_stale_command_not_latest_blocks(tmp_path: Path, monkeypatch) -> None:
    session, record, offset_claims, _history, db = _full_setup(tmp_path)
    monkeypatch.setattr(oe, "CALIBRATED_OFFSET_SOURCES", frozenset({"operator_attested_jog"}))
    run_id = session.maintenance_run_id
    # the high-Z command is NOT the latest (a later command follows) -> not reconciled live
    hz = {
        "id": "hz-cmd-1", "key": "hz-key", "commandType": "moveToWell",
        "params": {"labwareId": "fixture-1", "wellName": "A1"},
        "status": "succeeded", "createdAt": "2026-06-17T00:00:00",
    }
    later = {
        "id": "later", "key": "later-key", "commandType": "home",
        "params": {}, "status": "succeeded", "createdAt": "2026-06-17T00:01:00",
    }
    history = EndpointResult(
        path=f"/maintenance_runs/{run_id}/commands",
        ok=True,
        data={"data": [hz, later], "meta": {"totalLength": 2}},
    )
    with pytest.raises(ValueError, match="high_z_command_not_reconciled_live"):
        oe.promoted_offset_record(
            record, session=session,
            command_history=history, command_journal_path=db, now=NOW,
        )


def test_offset_scope_mismatch_demotes_claim_and_blocks(tmp_path: Path, monkeypatch) -> None:
    session, record, offset_claims, history, db = _full_setup(tmp_path)
    monkeypatch.setattr(oe, "CALIBRATED_OFFSET_SOURCES", frozenset({"operator_attested_jog"}))
    # promote against a record whose offset_mm differs from the committed claim's artifact
    mismatched = record.model_copy(update={"offset_mm": {"x": 9.9, "y": 9.9, "z": 9.9}})
    with pytest.raises(ValueError, match="missing_committed_offset_measurement_claim"):
        oe.promoted_offset_record(
            mismatched, session=session,
            command_history=history, command_journal_path=db, now=NOW,
        )


# --- registry upsert + authority isolation ------------------------------------------------


def test_registry_upsert_replaces_same_id_proposed(tmp_path: Path, monkeypatch) -> None:
    session, record, offset_claims, history, db = _full_setup(tmp_path)
    registry_path = tmp_path / "offset_registry.json"
    from aevum_ot2.core.registry import append_offset_record
    append_offset_record(record, registry_path)  # PROPOSED on disk
    monkeypatch.setattr(oe, "CALIBRATED_OFFSET_SOURCES", frozenset({"operator_attested_jog"}))
    promoted = oe.promoted_offset_record(
            record, session=session,
        command_history=history, command_journal_path=db, now=NOW,
    )
    registry = promote_offset_record_in_registry(promoted, registry_path)
    matching = [r for r in registry.records if offset_record_id(r) == offset_record_id(promoted)]
    assert len(matching) == 1  # upsert, not duplicate
    assert matching[0].authority_state == OffsetAuthorityState.PROMOTED


def test_blocked_promotion_leaves_registry_proposed(tmp_path: Path) -> None:
    session, record, offset_claims, history, db = _full_setup(tmp_path)
    registry_path = tmp_path / "offset_registry.json"
    from aevum_ot2.core.registry import append_offset_record
    append_offset_record(record, registry_path)
    # default (empty) allowlist -> promotion raises -> registry must stay PROPOSED
    with pytest.raises(ValueError, match="offset_source_not_calibrated"):
        oe.promoted_offset_record(
            record, session=session,
            command_history=history, command_journal_path=db, now=NOW,
        )
    registry = load_offset_registry(registry_path)
    assert all(r.authority_state == OffsetAuthorityState.PROPOSED for r in registry.records)


def test_module_grants_no_motion_authority() -> None:
    # Check real USAGE patterns, not docstring prose (which legitimately names what it must NOT do).
    src = Path("src/aevum_ot2/core/offset_evidence.py").read_text()
    assert "import motion_commissioning" not in src
    assert "from aevum_ot2.core.motion_commissioning" not in src
    assert "motion_allowed=True" not in src
    assert "MotionApproval(" not in src


# --- regression: the two safety-core holes the adversarial review found -------------------


def test_post_commit_offset_artifact_tamper_blocks(tmp_path: Path, monkeypatch) -> None:
    # A post-commit edit of the external offset_evidence.json (even with the record matched to
    # the tampered vector) must NOT promote: the committed handle checksum no longer matches.
    session, _record, _claims, history, db = _full_setup(tmp_path)
    monkeypatch.setattr(oe, "CALIBRATED_OFFSET_SOURCES", frozenset({"operator_attested_jog"}))
    artifact_path = tmp_path / "sessions/session-1/offset_evidence.json"
    artifact = oe.load_offset_evidence_artifact(artifact_path)
    tampered = artifact.model_copy(update={"offset_mm": {"x": 9.9, "y": 9.9, "z": 9.9}})
    oe.write_offset_evidence_artifact(tampered, artifact_path)  # overwrite committed file
    journal_id = artifact.high_z_journal_id
    bad = _proposed_record(session, journal_id=journal_id).model_copy(
        update={"offset_mm": {"x": 9.9, "y": 9.9, "z": 9.9}}
    )
    with pytest.raises(ValueError, match="missing_committed_offset_measurement_claim"):
        oe.promoted_offset_record(
            bad, session=session, command_history=history, command_journal_path=db, now=NOW
        )


def test_uncommitted_offset_claim_does_not_promote(tmp_path: Path, monkeypatch) -> None:
    # The offset claim is NOT trusted from a caller arg and is never committed here -> promote
    # finds no committed offset claim and blocks, even with a calibrated source and a valid high-Z.
    session = _session(tmp_path)
    db = tmp_path / "state.sqlite3"
    journal_id, history = _persist_journal(session, db)
    record = _proposed_record(session, journal_id=journal_id)
    _commit_high_z_claim(session)  # high-Z committed; offset evidence deliberately NOT committed
    monkeypatch.setattr(oe, "CALIBRATED_OFFSET_SOURCES", frozenset({"operator_attested_jog"}))
    with pytest.raises(ValueError, match="missing_committed_offset_measurement_claim"):
        oe.promoted_offset_record(
            record, session=session, command_history=history, command_journal_path=db, now=NOW
        )
