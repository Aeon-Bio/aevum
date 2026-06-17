from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.command_journal import (
    CommandJournalEntry,
    CommandReconciliationResult,
)
from aevum_ot2.core.evidence import (
    append_evidence_event,
    load_committed_evidence_claims,
)
from aevum_ot2.core.high_z_motion_evidence import (
    HighZMotionEvidenceArtifact,
    build_high_z_motion_evidence_artifact,
    commit_high_z_motion_claims,
    commit_high_z_motion_evidence_artifact,
    derive_high_z_motion_claims,
    high_z_motion_evidence_packet,
    high_z_motion_evidence_packets_from_artifact,
    promoted_high_z_motion_record,
    write_high_z_motion_evidence_artifact,
)
from aevum_ot2.core.models import (
    BridgeSession,
    BridgeSessionState,
    CameraCaptureResult,
    EvidenceEvent,
    EvidenceQuality,
    EvidenceSourceKind,
    OffsetRegistry,
)
from aevum_ot2.core.records import (
    HighZMotionRecord,
    HighZMotionResult,
    high_z_motion_completed_claim_id,
    high_z_motion_completed_claim_type,
)


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


def _motion_record(session: BridgeSession) -> HighZMotionRecord:
    identity = session.fixture_identity
    return HighZMotionRecord(
        target_class="center_high_z",
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        pose_digest_sha256=session.fixture_pose_digest_sha256,
        robot_serial=session.robot_serial or "",
        robot_server_version=session.robot_server_version or "",
        slot=session.slot,
        commanded_high_z_mm=20.0,
        maintenance_run_id=session.maintenance_run_id or "",
        command_id="cmd-id-1",
        result=HighZMotionResult.BLOCKED,
    )


def _command_entry(
    *,
    operation: str = "move_high_z",
    command_id: str | None = "cmd-id-1",
    command_status: str | None = "succeeded",
    session_id: str = "session-1",
    robot_url: str = "http://ot2.local:31950",
    run_id: str = "maintenance-run-1",
    command_key: str = "command-key-high-z",
    reconciled_at: datetime | None = None,
) -> CommandJournalEntry:
    return CommandJournalEntry(
        journal_id="cmd-journal-1",
        session_id=session_id,
        owner_id="agent-1",
        robot_url=robot_url,
        run_id=run_id,
        step_id="step-high-z",
        operation=operation,
        command_key=command_key,
        command_type="moveToWell",
        command_body_sha256="c" * 64,
        command_params_sha256="d" * 64,
        state="completed",
        command_id=command_id,
        command_index=0,
        command_status=command_status,
        reconciled_at=reconciled_at,
    )


def _reconciliation(
    entry: CommandJournalEntry,
    *,
    matched_command_id: str | None = "cmd-id-1",
    matched_status: str | None = "succeeded",
    matched_command_is_latest: bool = True,
) -> CommandReconciliationResult:
    return CommandReconciliationResult(
        entry=entry,
        state="completed",
        matched_command_id=matched_command_id,
        matched_command_index=0,
        command_history_total_length=1,
        matched_command_is_latest=matched_command_is_latest,
        matched_status=matched_status,
        recovery_required=False,
    )


def _camera_capture(session: BridgeSession, tmp_path: Path) -> CameraCaptureResult:
    image = tmp_path / "center_high_z_landing.jpg"
    image.write_bytes(b"high-z-landing-camera-evidence")
    checksum = hashlib.sha256(image.read_bytes()).hexdigest()
    capture = CameraCaptureResult(
        robot_url=session.robot_url,
        captured_at=session.updated_at + timedelta(seconds=2),
        endpoint="/camera/picture",
        image_path=str(image),
        image_checksum_sha256=checksum,
        content_type="image/jpeg",
        bytes_written=image.stat().st_size,
    )
    append_evidence_event(
        EvidenceEvent(
            event_type="ot2_camera_picture",
            session_id=session.session_id,
            summary="captured high-Z landing evidence",
            payload=capture.model_dump(mode="json"),
        ),
        path=session.evidence_index_path,
    )
    return capture


def _usable_artifact(
    session: BridgeSession,
    record: HighZMotionRecord,
    tmp_path: Path,
    *,
    command_entry: CommandJournalEntry | None = None,
    reconciliation: CommandReconciliationResult | None = None,
):
    capture = _camera_capture(session, tmp_path)
    entry = command_entry or _command_entry(
        reconciled_at=session.updated_at + timedelta(seconds=1)
    )
    reconcile = reconciliation if reconciliation is not None else _reconciliation(entry)
    return build_high_z_motion_evidence_artifact(
        record,
        session=session,
        artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
        image_path=capture.image_path,
        inspection_note="high-Z move executed; nozzle cleared fixture at commanded Z",
        command_entry=entry,
        reconciliation=reconcile,
        quality=EvidenceQuality.USABLE,
    )


def test_high_z_motion_evidence_commits_claim_and_appears_committed(
    tmp_path: Path,
) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_motion_evidence.json",
    )

    packets = high_z_motion_evidence_packets_from_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )
    claims = derive_high_z_motion_claims(record, packets, session=session)
    claim = claims[0]

    assert packets[0].source_kind == EvidenceSourceKind.HIGH_Z_LANDING
    assert claim.value is True
    assert claim.quality == EvidenceQuality.USABLE
    assert len(claim.evidence) == 1
    assert claim.claim_type == high_z_motion_completed_claim_type("center_high_z")
    assert claim.claim_id == high_z_motion_completed_claim_id(
        "center_high_z",
        packets[0].evidence_id,
    )

    commit = commit_high_z_motion_evidence_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
        transaction_id="high-z-motion-session-1-center-high-z",
    )
    committed_claims = load_committed_evidence_claims(
        index_path=session.evidence_index_path,
        root=tmp_path / "evidence_transactions",
    )

    assert commit.manifest.status == "committed"
    assert committed_claims[0].claim_type == claim.claim_type
    assert committed_claims[0].value is True

    promoted = promoted_high_z_motion_record(record, claims)
    assert promoted.result == HighZMotionResult.PASSED
    assert len(promoted.evidence) == 1


def test_pose_mismatch_demotes_claim_to_failed(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_motion_evidence.json",
    )
    packets = high_z_motion_evidence_packets_from_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )

    mismatched_record = record.model_copy(update={"pose_digest_sha256": "f" * 64})
    claims = derive_high_z_motion_claims(mismatched_record, packets, session=session)

    assert claims[0].value is False
    assert claims[0].quality == EvidenceQuality.FAILED
    assert claims[0].reasons


def test_slot_mismatch_demotes_claim_to_failed(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_motion_evidence.json",
    )
    packets = high_z_motion_evidence_packets_from_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )

    mismatched_record = record.model_copy(update={"slot": "2"})
    claims = derive_high_z_motion_claims(mismatched_record, packets, session=session)

    assert claims[0].value is False
    assert claims[0].quality == EvidenceQuality.FAILED
    assert any("slot" in reason for reason in claims[0].reasons)


def test_fixture_mismatch_demotes_claim_to_failed(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_motion_evidence.json",
    )
    packets = high_z_motion_evidence_packets_from_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )

    mismatched_record = record.model_copy(update={"fixture_load_name": "other_fixture"})
    claims = derive_high_z_motion_claims(mismatched_record, packets, session=session)

    assert claims[0].value is False
    assert claims[0].quality == EvidenceQuality.FAILED
    assert any("fixture" in reason for reason in claims[0].reasons)


def test_command_not_reconciled_blocks_usable_quality(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    entry = _command_entry()
    capture = _camera_capture(session, tmp_path)

    # No reconciliation result at all -> command_history_reconciled is False.
    ambiguous = build_high_z_motion_evidence_artifact(
        record,
        session=session,
        artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
        image_path=capture.image_path,
        inspection_note="high-Z move executed; nozzle cleared fixture",
        command_entry=entry,
        reconciliation=None,
        quality=EvidenceQuality.AMBIGUOUS,
    )
    assert ambiguous.command_history_reconciled is False

    with pytest.raises(ValidationError, match="requires command_history_reconciled"):
        build_high_z_motion_evidence_artifact(
            record,
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=capture.image_path,
            inspection_note="high-Z move executed; nozzle cleared fixture",
            command_entry=entry,
            reconciliation=None,
            quality=EvidenceQuality.USABLE,
        )

    # Reconciliation present but it matched no command in history -> not reconciled.
    # (A reconciliation whose matched_status disagreed with the entry would be a hard
    # inconsistency error; here matched_command_id is None, the genuine no-match case.)
    reconcile = _reconciliation(entry).model_copy(
        update={"matched_command_id": None, "matched_status": None}
    )
    not_reconciled = build_high_z_motion_evidence_artifact(
        record,
        session=session,
        artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
        image_path=capture.image_path,
        inspection_note="high-Z move executed; nozzle cleared fixture",
        command_entry=entry,
        reconciliation=reconcile,
        quality=EvidenceQuality.AMBIGUOUS,
    )
    assert not_reconciled.command_history_reconciled is False


def test_command_status_not_succeeded_blocks_usable(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    entry = _command_entry(command_status="failed")
    reconcile = _reconciliation(entry, matched_status="failed")
    capture = _camera_capture(session, tmp_path)

    with pytest.raises(ValidationError, match="command_status succeeded"):
        build_high_z_motion_evidence_artifact(
            record,
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=capture.image_path,
            inspection_note="high-Z move executed",
            command_entry=entry,
            reconciliation=reconcile,
            quality=EvidenceQuality.USABLE,
        )


def test_matched_command_not_latest_blocks_usable(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    entry = _command_entry()
    reconcile = _reconciliation(entry, matched_command_is_latest=False)
    capture = _camera_capture(session, tmp_path)

    # build_high_z_motion_evidence_artifact derives command_history_reconciled from
    # matched_command_is_latest, so a non-latest reconciliation also fails the
    # reconciled rule. Constructing the artifact directly isolates the latest-command
    # rule: reconciled True but matched_command_is_latest False must still block USABLE.
    image_checksum = hashlib.sha256(Path(capture.image_path).read_bytes()).hexdigest()
    with pytest.raises(ValidationError, match="matched_command_is_latest"):
        HighZMotionEvidenceArtifact(
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            session_id=session.session_id,
            robot_serial=session.robot_serial or "",
            robot_server_version=session.robot_server_version or "",
            fixture_load_name=record.fixture_load_name,
            fixture_params_sha256=record.fixture_params_sha256,
            labware_definition_sha256=record.labware_definition_sha256,
            slot=record.slot,
            target_class=record.target_class,
            commanded_high_z_mm=record.commanded_high_z_mm,
            command_id=entry.command_id or "",
            command_key=entry.command_key,
            command_type=entry.command_type,
            command_status="succeeded",
            command_history_reconciled=True,
            matched_command_is_latest=False,
            image_path=capture.image_path,
            image_checksum_sha256=image_checksum,
            image_captured_at=capture.captured_at,
            image_capture_robot_url=capture.robot_url,
            image_capture_endpoint=capture.endpoint,
            image_capture_checksum_sha256=capture.image_checksum_sha256,
            inspection_note="high-Z move executed",
            quality=EvidenceQuality.USABLE,
        )
    assert reconcile.matched_command_is_latest is False


def test_command_entry_operation_must_be_move_high_z(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    entry = _command_entry(operation="move_low_z")
    reconcile = _reconciliation(entry)
    capture = _camera_capture(session, tmp_path)

    with pytest.raises(ValueError, match="operation must be move_high_z"):
        build_high_z_motion_evidence_artifact(
            record,
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=capture.image_path,
            inspection_note="high-Z move executed",
            command_entry=entry,
            reconciliation=reconcile,
            quality=EvidenceQuality.AMBIGUOUS,
        )


def test_timezone_aware_created_at_is_rejected(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    capture = _camera_capture(session, tmp_path)
    image_checksum = hashlib.sha256(Path(capture.image_path).read_bytes()).hexdigest()

    with pytest.raises(ValidationError, match="created_at must be timezone-naive"):
        HighZMotionEvidenceArtifact(
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            created_at=datetime.now(UTC),
            session_id=session.session_id,
            fixture_load_name=record.fixture_load_name,
            fixture_params_sha256=record.fixture_params_sha256,
            labware_definition_sha256=record.labware_definition_sha256,
            slot=record.slot,
            target_class=record.target_class,
            commanded_high_z_mm=record.commanded_high_z_mm,
            command_key=_command_entry().command_key,
            command_type=_command_entry().command_type,
            image_path=capture.image_path,
            image_checksum_sha256=image_checksum,
            inspection_note="high-Z move executed",
        )


def test_non_positive_commanded_high_z_is_rejected(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    entry = _command_entry()
    reconcile = _reconciliation(entry)
    capture = _camera_capture(session, tmp_path)

    with pytest.raises(ValidationError, match="commanded_high_z_mm must be finite"):
        build_high_z_motion_evidence_artifact(
            record.model_copy(update={"commanded_high_z_mm": 0.0}),
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=capture.image_path,
            inspection_note="high-Z move executed",
            command_entry=entry,
            reconciliation=reconcile,
            quality=EvidenceQuality.AMBIGUOUS,
        )


def test_non_finite_commanded_high_z_is_rejected(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    entry = _command_entry()
    reconcile = _reconciliation(entry)
    capture = _camera_capture(session, tmp_path)

    with pytest.raises(ValidationError, match="commanded_high_z_mm must be finite"):
        build_high_z_motion_evidence_artifact(
            record.model_copy(update={"commanded_high_z_mm": float("inf")}),
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=capture.image_path,
            inspection_note="high-Z move executed",
            command_entry=entry,
            reconciliation=reconcile,
            quality=EvidenceQuality.AMBIGUOUS,
        )


def test_usable_evidence_requires_indexed_camera_capture(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    entry = _command_entry()
    reconcile = _reconciliation(entry)
    image = tmp_path / "unindexed.jpg"
    image.write_bytes(b"unindexed high-z landing evidence")

    with pytest.raises(ValidationError, match="requires image_captured_at"):
        build_high_z_motion_evidence_artifact(
            record,
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=image,
            inspection_note="image was not captured through the session evidence index",
            command_entry=entry,
            reconciliation=reconcile,
            quality=EvidenceQuality.USABLE,
        )


def test_image_checksum_tamper_is_a_blocker(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    capture = _camera_capture(session, tmp_path)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_motion_evidence.json",
    )
    Path(capture.image_path).write_bytes(b"tampered high-z image content")

    with pytest.raises(ValueError, match="image checksum mismatch"):
        high_z_motion_evidence_packets_from_artifact(
            record,
            artifact,
            session=session,
            artifact_path=artifact_path,
        )


def test_lease_expired_is_a_blocker(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_motion_evidence.json",
    )
    expired_session = session.model_copy(
        update={"lease_expires_at": datetime.now() - timedelta(seconds=1)}
    )

    with pytest.raises(ValueError, match="session lease is expired"):
        high_z_motion_evidence_packets_from_artifact(
            record,
            artifact,
            session=expired_session,
            artifact_path=artifact_path,
        )


def test_session_state_not_allowed_is_a_blocker(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_motion_evidence.json",
    )
    no_motion_session = session.model_copy(
        update={"state": BridgeSessionState.READY_NO_MOTION}
    )

    with pytest.raises(ValueError, match="session state is ready_no_motion"):
        high_z_motion_evidence_packets_from_artifact(
            record,
            artifact,
            session=no_motion_session,
            artifact_path=artifact_path,
        )


def test_packet_rejects_non_allowlist_source_kind(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)

    with pytest.raises(ValueError, match="unsupported high-Z motion evidence source"):
        high_z_motion_evidence_packet(
            record,
            session=session,
            evidence_id="bad-source",
            source_kind=EvidenceSourceKind.INSPECTION_NOTE,
            quality=EvidenceQuality.AMBIGUOUS,
        )


def test_target_packet_is_not_picked_up_as_high_z_motion(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    from aevum_ot2.core.models import EvidencePacket

    foreign_packet = EvidencePacket(
        evidence_id="vision-packet",
        source_kind=EvidenceSourceKind.VISION_ANALYSIS,
        session_id=session.session_id,
        operation="target_class_verification",
        quality=EvidenceQuality.USABLE,
    )
    claims = derive_high_z_motion_claims(record, [foreign_packet], session=session)
    assert claims == []


def test_ambiguous_default_does_not_promote(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    packet = high_z_motion_evidence_packet(
        record,
        session=session,
        evidence_id="ambiguous-high-z-evidence",
        quality=EvidenceQuality.AMBIGUOUS,
    )
    claims = derive_high_z_motion_claims(record, [packet], session=session)

    assert claims[0].value is False
    with pytest.raises(ValueError, match="missing usable high-Z motion claim"):
        promoted_high_z_motion_record(record, claims)


def test_commit_produces_no_gate_result_and_no_offset_side_effects(
    tmp_path: Path,
) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_motion_evidence.json",
    )
    offset_registry_path = tmp_path / "offset_registry.json"
    offset_registry_path.write_text(OffsetRegistry().model_dump_json(indent=2) + "\n")
    registry_before = offset_registry_path.read_text()

    commit = commit_high_z_motion_evidence_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
        transaction_id="high-z-motion-isolation",
    )

    transaction_root = tmp_path / "evidence_transactions"
    produced_files = [path.name for path in transaction_root.rglob("*")]
    assert commit.manifest.status == "committed"
    assert not any("gate" in name.lower() for name in produced_files)
    assert not any("offset" in name.lower() for name in produced_files)
    assert offset_registry_path.read_text() == registry_before


def test_require_session_evidence_index_rejects_non_session_path(
    tmp_path: Path,
) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_motion_evidence.json",
    )
    packets = high_z_motion_evidence_packets_from_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )

    with pytest.raises(ValueError, match="must be a session evidence_index.json"):
        commit_high_z_motion_claims(
            record,
            packets,
            session=session,
            index_path=tmp_path / "not_an_index.json",
        )


# --- hardening: command-provenance binding (adversarial review fixes) ----------------------


def test_reconciliation_matching_a_foreign_command_is_rejected(tmp_path: Path) -> None:
    # A reconciliation that matched a DIFFERENT command cannot be borrowed to assert this
    # move reconciled (the binding must be to command_entry.command_id).
    session = _session(tmp_path)
    record = _motion_record(session)
    entry = _command_entry(reconciled_at=session.updated_at + timedelta(seconds=1))
    capture = _camera_capture(session, tmp_path)
    foreign = _reconciliation(entry, matched_command_id="SOME-OTHER-COMMAND")

    with pytest.raises(ValueError, match="matched a different command"):
        build_high_z_motion_evidence_artifact(
            record,
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=capture.image_path,
            inspection_note="high-Z move executed",
            command_entry=entry,
            reconciliation=foreign,
            quality=EvidenceQuality.USABLE,
        )


def test_command_entry_from_a_foreign_session_is_rejected(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    capture = _camera_capture(session, tmp_path)
    foreign_entry = _command_entry(
        session_id="some-other-session",
        reconciled_at=session.updated_at + timedelta(seconds=1),
    )

    with pytest.raises(ValueError, match="command entry session does not match"):
        build_high_z_motion_evidence_artifact(
            record,
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=capture.image_path,
            inspection_note="high-Z move executed",
            command_entry=foreign_entry,
            reconciliation=_reconciliation(foreign_entry),
            quality=EvidenceQuality.USABLE,
        )


def test_command_entry_from_a_foreign_robot_is_rejected(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _motion_record(session)
    capture = _camera_capture(session, tmp_path)
    foreign_entry = _command_entry(
        robot_url="http://other-ot2.local:31950",
        reconciled_at=session.updated_at + timedelta(seconds=1),
    )

    with pytest.raises(ValueError, match="command entry robot URL does not match"):
        build_high_z_motion_evidence_artifact(
            record,
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=capture.image_path,
            inspection_note="high-Z move executed",
            command_entry=foreign_entry,
            reconciliation=_reconciliation(foreign_entry),
            quality=EvidenceQuality.USABLE,
        )


# --- hardening: post-motion ordering -------------------------------------------------------


def test_pre_move_frame_is_rejected_as_post_motion_evidence(tmp_path: Path) -> None:
    # A frame captured BEFORE the move command completed cannot be USABLE completion evidence,
    # even though it is after session.updated_at.
    session = _session(tmp_path)
    record = _motion_record(session)
    capture = _camera_capture(session, tmp_path)  # captured at session.updated_at + 2s
    # command completes AFTER the capture -> the frame is a pre-move (baseline) frame.
    entry = _command_entry(reconciled_at=capture.captured_at + timedelta(seconds=5))

    with pytest.raises(ValidationError, match="must be at or after command_completed_at"):
        build_high_z_motion_evidence_artifact(
            record,
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=capture.image_path,
            inspection_note="high-Z move executed",
            command_entry=entry,
            reconciliation=_reconciliation(entry),
            quality=EvidenceQuality.USABLE,
        )


def test_usable_requires_command_completed_at(tmp_path: Path) -> None:
    # No posted_at/reconciled_at on the entry -> no command completion time -> cannot be USABLE.
    session = _session(tmp_path)
    record = _motion_record(session)
    capture = _camera_capture(session, tmp_path)
    entry = _command_entry(reconciled_at=None)  # no completion timestamp

    with pytest.raises(ValidationError, match="requires command_completed_at"):
        build_high_z_motion_evidence_artifact(
            record,
            session=session,
            artifact_id=f"{session.session_id}:high_z_motion:center_high_z",
            image_path=capture.image_path,
            inspection_note="high-Z move executed",
            command_entry=entry,
            reconciliation=_reconciliation(entry),
            quality=EvidenceQuality.USABLE,
        )


# --- hardening: promote re-validates scope (terminal trust boundary) -----------------------


def test_promote_refuses_a_foreign_fixture_claim(tmp_path: Path) -> None:
    # A hand-built USABLE claim for a DIFFERENT fixture must not promote, even though its
    # claim_type/quality/method look right (there is no downstream high-Z gate yet).
    from aevum_ot2.core.models import EvidenceClaim, EvidenceHandle
    from aevum_ot2.core.records import HIGH_Z_MOTION_EVIDENCE_METHOD

    session = _session(tmp_path)
    record = _motion_record(session)
    handle = EvidenceHandle(
        evidence_id="forged-evidence",
        source_kind=EvidenceSourceKind.HIGH_Z_LANDING,
        quality=EvidenceQuality.USABLE,
    )
    forged = EvidenceClaim(
        claim_id=high_z_motion_completed_claim_id("center_high_z", "forged-evidence"),
        claim_type=high_z_motion_completed_claim_type("center_high_z"),
        value=True,
        fixture_load_name="totally_different_fixture",
        fixture_params_sha256="0" * 64,
        labware_definition_sha256=record.labware_definition_sha256,
        pose_digest_sha256=record.pose_digest_sha256,
        method=HIGH_Z_MOTION_EVIDENCE_METHOD,
        quality=EvidenceQuality.USABLE,
        evidence=[handle],
    )
    with pytest.raises(ValueError, match="missing usable high-Z motion claim"):
        promoted_high_z_motion_record(record, [forged])


def test_promote_refuses_a_claim_id_not_bound_to_its_handle(tmp_path: Path) -> None:
    from aevum_ot2.core.models import EvidenceClaim, EvidenceHandle
    from aevum_ot2.core.records import HIGH_Z_MOTION_EVIDENCE_METHOD

    session = _session(tmp_path)
    record = _motion_record(session)
    handle = EvidenceHandle(
        evidence_id="evidence-A",
        source_kind=EvidenceSourceKind.HIGH_Z_LANDING,
        quality=EvidenceQuality.USABLE,
    )
    mismatched = EvidenceClaim(
        claim_id="high_z_motion_completed:center_high_z:evidence-literally-anything",
        claim_type=high_z_motion_completed_claim_type("center_high_z"),
        value=True,
        fixture_load_name=record.fixture_load_name,
        fixture_params_sha256=record.fixture_params_sha256,
        labware_definition_sha256=record.labware_definition_sha256,
        pose_digest_sha256=record.pose_digest_sha256,
        method=HIGH_Z_MOTION_EVIDENCE_METHOD,
        quality=EvidenceQuality.USABLE,
        evidence=[handle],
    )
    with pytest.raises(ValueError, match="missing usable high-Z motion claim"):
        promoted_high_z_motion_record(record, [mismatched])


def test_promote_refuses_a_self_contradictory_claim(tmp_path: Path) -> None:
    # derive's invariant is value == (not reasons); a value=True claim that still carries
    # blocking reasons is malformed-by-contract and must not promote (it could never be
    # emitted by derive_high_z_motion_claims).
    from aevum_ot2.core.models import EvidenceClaim, EvidenceHandle
    from aevum_ot2.core.records import HIGH_Z_MOTION_EVIDENCE_METHOD

    session = _session(tmp_path)
    record = _motion_record(session)
    handle = EvidenceHandle(
        evidence_id="evidence-A",
        source_kind=EvidenceSourceKind.HIGH_Z_LANDING,
        quality=EvidenceQuality.USABLE,
    )
    contradictory = EvidenceClaim(
        claim_id=high_z_motion_completed_claim_id("center_high_z", "evidence-A"),
        claim_type=high_z_motion_completed_claim_type("center_high_z"),
        value=True,
        fixture_load_name=record.fixture_load_name,
        fixture_params_sha256=record.fixture_params_sha256,
        labware_definition_sha256=record.labware_definition_sha256,
        pose_digest_sha256=record.pose_digest_sha256,
        method=HIGH_Z_MOTION_EVIDENCE_METHOD,
        quality=EvidenceQuality.USABLE,
        evidence=[handle],
        reasons=["this command never reconciled", "image predates motion"],
    )
    with pytest.raises(ValueError, match="missing usable high-Z motion claim"):
        promoted_high_z_motion_record(record, [contradictory])


def test_genuine_committed_claim_promotes(tmp_path: Path) -> None:
    # the legitimate path still promotes after the scope re-validation
    session = _session(tmp_path)
    record = _motion_record(session)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact, tmp_path / "sessions/session-1/center_high_z_motion_evidence.json"
    )
    packets = high_z_motion_evidence_packets_from_artifact(
        record, artifact, session=session, artifact_path=artifact_path
    )
    claims = derive_high_z_motion_claims(record, packets, session=session)
    assert claims[0].value is True
    promoted = promoted_high_z_motion_record(record, claims)
    assert promoted.result == HighZMotionResult.PASSED
    assert promoted.claims == claims


# --- hardening: packet/claim-layer command demotion (not only the validator layer) ---------


def test_packet_with_unreconciled_command_demotes_claim(tmp_path: Path) -> None:
    # A packet whose payload says the command did not reconcile yields value=False / FAILED,
    # exercising the packet/claim scope layer (not just the artifact validator).
    session = _session(tmp_path)
    record = _motion_record(session)
    packet = high_z_motion_evidence_packet(
        record,
        session=session,
        evidence_id="hand-built-high-z",
        quality=EvidenceQuality.USABLE,
        payload={
            "value": True,
            "command_id": "cmd-id-1",
            "command_status": "succeeded",
            "command_history_reconciled": False,
            "matched_command_is_latest": True,
        },
    )
    claims = derive_high_z_motion_claims(record, [packet], session=session)
    assert claims[0].value is False
    assert claims[0].quality == EvidenceQuality.FAILED
    assert any("reconcil" in reason for reason in claims[0].reasons)


# --- hardening: declarative payload table closes the fail-open verification gap -------------


def test_every_payload_field_corruption_is_caught(tmp_path: Path) -> None:
    # Property test: take a valid packet derived from a real artifact, corrupt each payload
    # field in turn, and assert EVERY corruption demotes the claim to FAILED. This guards the
    # _PACKET_PAYLOAD_FIELDS table — if a field stops being verified, this test goes red.
    session = _session(tmp_path)
    record = _motion_record(session)
    artifact = _usable_artifact(session, record, tmp_path)
    artifact_path = write_high_z_motion_evidence_artifact(
        artifact, tmp_path / "sessions/session-1/center_high_z_motion_evidence.json"
    )
    base = high_z_motion_evidence_packets_from_artifact(
        record, artifact, session=session, artifact_path=artifact_path
    )[0]

    # sanity: the clean packet derives a usable, true claim
    clean = derive_high_z_motion_claims(record, [base], session=session)[0]
    assert clean.value is True
    assert clean.quality == EvidenceQuality.USABLE

    assert set(base.payload) - {"value"}, "expected denormalized payload fields to verify"
    for key, original in list(base.payload.items()):
        corrupted = base.model_copy(deep=True)
        corrupted.payload[key] = (not original) if isinstance(original, bool) else "CORRUPTED-VALUE"
        claim = derive_high_z_motion_claims(record, [corrupted], session=session)[0]
        assert claim.value is False, f"corrupting payload[{key!r}] was NOT caught"
        assert claim.quality == EvidenceQuality.FAILED, f"payload[{key!r}] corruption not FAILED"
        assert claim.reasons
