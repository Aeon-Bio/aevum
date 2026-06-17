from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.evidence import (
    append_evidence_event,
    load_committed_evidence_claims,
)
from aevum_ot2.core.models import (
    BridgeSession,
    BridgeSessionState,
    CameraCaptureResult,
    EvidenceEvent,
    EvidenceQuality,
    EvidenceSourceKind,
    VisionAnalysisResult,
)
from aevum_ot2.core.records import (
    scaffold_target_class_record,
    target_class_authority,
    target_class_verified_claim_id,
    target_class_verified_claim_type,
)
from aevum_ot2.core.target_evidence import (
    build_target_class_evidence_artifact,
    commit_target_class_evidence_artifact,
    derive_target_class_claims,
    promoted_target_class_record,
    target_class_evidence_packet,
    target_class_evidence_packets_from_artifact,
    write_target_class_evidence_artifact,
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
        state="ready_no_motion",
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


def _target_record(session: BridgeSession):
    return scaffold_target_class_record(
        session,
        "center_high_z",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
    )


def _camera_capture(session: BridgeSession, tmp_path: Path) -> CameraCaptureResult:
    image = tmp_path / "center_high_z.jpg"
    image.write_bytes(b"target-class-camera-evidence")
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
            summary="captured target evidence",
            payload=capture.model_dump(mode="json"),
        ),
        path=session.evidence_index_path,
    )
    return capture


def test_target_class_evidence_commits_claim_and_promotes_record(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _target_record(session)
    capture = _camera_capture(session, tmp_path)
    artifact = build_target_class_evidence_artifact(
        record,
        session=session,
        artifact_id=f"{session.session_id}:target_class_evidence:center_high_z",
        image_path=capture.image_path,
        inspection_note="center high-Z target is visually clear and bounded",
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_target_class_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_target_evidence.json",
    )

    packets = target_class_evidence_packets_from_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )
    claims = derive_target_class_claims(record, packets, session=session)
    claim = claims[0]

    assert packets[0].source_kind == EvidenceSourceKind.INSPECTION_NOTE
    assert claim.value is True
    assert claim.quality == EvidenceQuality.USABLE
    assert claim.claim_type == target_class_verified_claim_type("center_high_z")
    assert claim.claim_id == target_class_verified_claim_id(
        "center_high_z",
        packets[0].evidence_id,
    )

    promoted = promoted_target_class_record(record, claims)
    uncommitted_authority = target_class_authority(promoted, session=session)
    assert uncommitted_authority.passed is False
    assert "not committed in session evidence" in " ".join(
        uncommitted_authority.blockers
    )

    commit = commit_target_class_evidence_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
        transaction_id="target-evidence-session-1-center-high-z",
    )
    authority = target_class_authority(promoted, session=session)
    committed_claims = load_committed_evidence_claims(
        index_path=session.evidence_index_path,
        root=tmp_path / "evidence_transactions",
    )

    assert commit.manifest.status == "committed"
    assert authority.passed is True
    assert committed_claims[0].claim_type == claim.claim_type


def test_valid_vision_result_promotes_packet_source_kind(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _target_record(session)
    capture = _camera_capture(session, tmp_path)
    vision_path = tmp_path / "center_high_z_vision.json"
    vision_path.write_text(
        VisionAnalysisResult(
            image_path=capture.image_path,
            analyzed_at=session.updated_at + timedelta(seconds=3),
            purpose="high_z_target",
            evidence_ok=True,
            motion_gate=False,
            summary="fixture target evidence is usable",
        ).model_dump_json()
    )
    artifact = build_target_class_evidence_artifact(
        record,
        session=session,
        artifact_id=f"{session.session_id}:target_class_evidence:center_high_z",
        image_path=capture.image_path,
        inspection_note="center high-Z target is visually clear and bounded",
        vision_result_path=vision_path,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_target_class_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_target_evidence.json",
    )

    packets = target_class_evidence_packets_from_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )

    assert packets[0].source_kind == EvidenceSourceKind.VISION_ANALYSIS


def test_attached_vision_result_must_be_schema_valid(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _target_record(session)
    capture = _camera_capture(session, tmp_path)
    vision_path = tmp_path / "invalid_vision.json"
    vision_path.write_text('{"not":"a vision result"}')
    artifact = build_target_class_evidence_artifact(
        record,
        session=session,
        artifact_id=f"{session.session_id}:target_class_evidence:center_high_z",
        image_path=capture.image_path,
        inspection_note="center high-Z target is visually clear and bounded",
        vision_result_path=vision_path,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_target_class_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_target_evidence.json",
    )

    with pytest.raises(ValueError, match="vision result is invalid"):
        target_class_evidence_packets_from_artifact(
            record,
            artifact,
            session=session,
            artifact_path=artifact_path,
        )


def test_attached_vision_result_must_match_target_image(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _target_record(session)
    capture = _camera_capture(session, tmp_path)
    other_image = tmp_path / "other.jpg"
    other_image.write_bytes(b"other image")
    vision_path = tmp_path / "wrong_image_vision.json"
    vision_path.write_text(
        VisionAnalysisResult(
            image_path=str(other_image),
            analyzed_at=session.updated_at + timedelta(seconds=3),
            purpose="high_z_target",
            evidence_ok=True,
            motion_gate=False,
            summary="fixture target evidence is usable",
        ).model_dump_json()
    )
    artifact = build_target_class_evidence_artifact(
        record,
        session=session,
        artifact_id=f"{session.session_id}:target_class_evidence:center_high_z",
        image_path=capture.image_path,
        inspection_note="center high-Z target is visually clear and bounded",
        vision_result_path=vision_path,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_target_class_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_target_evidence.json",
    )

    with pytest.raises(ValueError, match="vision result image does not match"):
        target_class_evidence_packets_from_artifact(
            record,
            artifact,
            session=session,
            artifact_path=artifact_path,
        )


def test_usable_target_class_evidence_requires_indexed_camera_capture(
    tmp_path: Path,
) -> None:
    session = _session(tmp_path)
    record = _target_record(session)
    image = tmp_path / "unindexed.jpg"
    image.write_bytes(b"unindexed target evidence")

    with pytest.raises(ValidationError, match="requires image_captured_at"):
        build_target_class_evidence_artifact(
            record,
            session=session,
            artifact_id=f"{session.session_id}:target_class_evidence:center_high_z",
            image_path=image,
            inspection_note="image was not captured through the session evidence index",
            quality=EvidenceQuality.USABLE,
        )


def test_target_class_evidence_rejects_closed_session_authority(
    tmp_path: Path,
) -> None:
    session = _session(tmp_path)
    record = _target_record(session)
    capture = _camera_capture(session, tmp_path)
    artifact = build_target_class_evidence_artifact(
        record,
        session=session,
        artifact_id=f"{session.session_id}:target_class_evidence:center_high_z",
        image_path=capture.image_path,
        inspection_note="center high-Z target is visually clear and bounded",
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_target_class_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/center_high_z_target_evidence.json",
    )
    closed_session = session.model_copy(update={"state": BridgeSessionState.CLOSED})

    with pytest.raises(ValueError, match="session state is closed"):
        target_class_evidence_packets_from_artifact(
            record,
            artifact,
            session=closed_session,
            artifact_path=artifact_path,
        )


def test_promoted_target_class_record_rejects_failed_target_claim(tmp_path: Path) -> None:
    session = _session(tmp_path)
    record = _target_record(session)
    packet = target_class_evidence_packet(
        record,
        session=session,
        evidence_id="ambiguous-target-evidence",
        quality=EvidenceQuality.AMBIGUOUS,
    )
    claims = derive_target_class_claims(
        record,
        [packet],
        session=session,
    )

    assert claims[0].value is False
    with pytest.raises(ValueError, match="missing usable target-class claim"):
        promoted_target_class_record(record, claims)
