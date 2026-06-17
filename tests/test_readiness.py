from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from pathlib import Path

from aevum_cad.labware import build_labware_definition
from aevum_cad.params import load_params
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.evidence import append_evidence_event
from aevum_ot2.core.models import (
    BridgeSession,
    CameraCaptureResult,
    EvidenceEvent,
    EvidenceQuality,
    EvidenceSourceKind,
)
from aevum_ot2.core.pose import (
    FixtureOrientation,
    fixture_pose_from_labware_definition,
    write_fixture_pose,
)
from aevum_ot2.core.pose_evidence import (
    build_fixture_pose_evidence_artifact,
    commit_fixture_pose_evidence_artifact,
    derive_fixture_pose_claims,
    fixture_pose_evidence_packet,
    write_fixture_pose_evidence_artifact,
)
from aevum_ot2.core.readiness import evaluate_registration_readiness
from aevum_ot2.core.records import (
    FixtureQcMeasurement,
    FixtureQcRecord,
    TargetClassResult,
    TargetClassVerificationRecord,
    target_class_names,
    write_fixture_qc_record,
    write_target_class_record,
)


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


def _pose():
    return fixture_pose_from_labware_definition(
        current_fixture_identity(),
        slot="5",
        orientation=FixtureOrientation.ROT180,
        canonical_labware_definition=build_labware_definition(load_params()),
    )


def _pose_session(tmp_path: Path) -> BridgeSession:
    session = _session()
    pose = _pose()
    pose_path = tmp_path / "sessions/session-1/fixture_pose.json"
    write_fixture_pose(pose, pose_path)
    return session.model_copy(
        update={
            "slot": "5",
            "fixture_orientation": "rot180",
            "fixture_pose_digest_sha256": pose.pose_digest_sha256,
            "fixture_pose_path": str(pose_path),
            "definition_uri": "aevum/aevum_p300_poc_fixture_rot180/1",
            "evidence_index_path": str(
                tmp_path / "sessions/session-1/evidence_index.json"
            ),
        }
    )


def _fixture_qc_record(session: BridgeSession) -> FixtureQcRecord:
    identity = session.fixture_identity
    return FixtureQcRecord(
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        pose_digest_sha256=session.fixture_pose_digest_sha256,
        measurements=[
            FixtureQcMeasurement(
                name="x_bound",
                measured_mm=127.76,
                nominal_mm=127.76,
                tolerance_mm=1.0,
                passed=True,
            ),
            FixtureQcMeasurement(
                name="y_bound",
                measured_mm=85.48,
                nominal_mm=85.48,
                tolerance_mm=1.0,
                passed=True,
            ),
            FixtureQcMeasurement(
                name="z_bound",
                measured_mm=91.0,
                nominal_mm=91.0,
                tolerance_mm=1.0,
                passed=True,
            ),
        ],
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )


def _target_record(session: BridgeSession, target_class: str) -> TargetClassVerificationRecord:
    identity = session.fixture_identity
    return TargetClassVerificationRecord(
        target_class=target_class,
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        robot_serial=session.robot_serial or "OT2TEST0001",
        robot_server_version=session.robot_server_version or "9.0.0",
        slot=session.slot,
        pose_digest_sha256=session.fixture_pose_digest_sha256,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        tiprack_load_name="opentrons_96_tiprack_300ul",
        offset_registry_record="not-yet-registered",
        result=TargetClassResult.BLOCKED,
    )


def _write_records(tmp_path: Path, session: BridgeSession) -> tuple[Path, list[Path]]:
    qc_path = tmp_path / "fixture_qc.json"
    write_fixture_qc_record(_fixture_qc_record(session), qc_path)
    target_paths = []
    for target_class in target_class_names():
        target_path = tmp_path / f"{target_class}.json"
        write_target_class_record(_target_record(session, target_class), target_path)
        target_paths.append(target_path)
    return qc_path, target_paths


def _artifact(tmp_path: Path, name: str) -> tuple[Path, str]:
    path = tmp_path / name
    path.write_text(f"{name}\n")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _commit_pose_claims(tmp_path: Path, session: BridgeSession) -> None:
    pose = _pose()
    session.evidence_index_path = str(
        tmp_path / "sessions" / session.session_id / "evidence_index.json"
    )
    image_path, image_checksum = _artifact(tmp_path, "slot5.jpg")
    camera_capture = CameraCaptureResult(
        robot_url=session.robot_url,
        captured_at=datetime.now(),
        endpoint="/camera/picture",
        image_path=str(image_path),
        image_checksum_sha256=image_checksum,
        content_type="image/jpg",
        bytes_written=image_path.stat().st_size,
    )
    append_evidence_event(
        EvidenceEvent(
            event_type="ot2_camera_picture",
            session_id=session.session_id,
            summary="captured test camera image",
            payload=camera_capture.model_dump(mode="json"),
        ),
        path=session.evidence_index_path,
    )
    vision_path, _vision_checksum = _artifact(tmp_path, "slot5.vision.json")
    artifact = build_fixture_pose_evidence_artifact(
        pose,
        session=session,
        artifact_id="fixture-pose-evidence-1",
        image_path=image_path,
        observed_orientation="rot180",
        fixture_upright=True,
        inspection_note="slot 5 fixture fiducials visible after 180-degree rotation",
        camera_capture=camera_capture,
        vision_result_path=vision_path,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_fixture_pose_evidence_artifact(
        artifact,
        tmp_path / "sessions/session-1/fixture_pose_evidence.json",
    )
    commit_fixture_pose_evidence_artifact(
        pose,
        artifact,
        session=session,
        artifact_path=artifact_path,
        root=tmp_path / "evidence_transactions",
        transaction_id="pose-claims-1",
    )


def test_registration_readiness_joins_session_and_record_paths(tmp_path) -> None:
    session = _session()
    qc_path, target_paths = _write_records(tmp_path, session)

    result = evaluate_registration_readiness(
        session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
    )

    assert result.registration_ready is True
    assert result.low_z_ready is False
    assert result.motion_allowed is False
    assert result.reasons == []
    assert result.gate_result is not None
    assert result.gate_result.passed is True
    assert result.gate_result.motion_allowed is False
    assert result.fixture_qc_record is not None
    assert len(result.target_class_records) == len(target_class_names())


def test_registration_readiness_fails_on_identity_mismatch(tmp_path) -> None:
    session = _session()
    qc_path, target_paths = _write_records(tmp_path, session)
    bad_record = _target_record(session, "center_high_z")
    bad_record.slot = "2"
    bad_record.robot_serial = "OTHERBOT"
    write_target_class_record(bad_record, target_paths[0])

    result = evaluate_registration_readiness(
        session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
    )

    reason_text = " ".join(result.reasons)
    assert result.registration_ready is False
    assert result.gate_result is not None
    assert result.gate_result.passed is False
    assert "slot 2 does not match session slot 1" in reason_text
    assert "OTHERBOT does not match session robot OT2TEST0001" in reason_text


def test_registration_readiness_requires_complete_target_scaffold(tmp_path) -> None:
    session = _session()
    qc_path, target_paths = _write_records(tmp_path, session)

    result = evaluate_registration_readiness(
        session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths[:-1],
    )

    assert result.registration_ready is False
    assert result.gate_result is not None
    assert result.gate_result.passed is False
    assert result.gate_result.missing_claims
    assert "missing target-class records" in " ".join(result.reasons)


def test_registration_readiness_requires_pose_claims_for_pose_scoped_session(
    tmp_path,
) -> None:
    session = _pose_session(tmp_path)
    qc_path, target_paths = _write_records(tmp_path, session)

    result = evaluate_registration_readiness(
        session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
        evidence_transaction_root=tmp_path / "evidence_transactions",
    )

    assert result.registration_ready is False
    assert result.pose_gate is not None
    assert result.pose_gate.passed is False
    assert "fixture_pose_orientation" in " ".join(result.pose_gate.missing_claims)
    assert "fixture_upright" in " ".join(result.pose_gate.missing_claims)


def test_registration_readiness_joins_committed_pose_claims(tmp_path) -> None:
    session = _pose_session(tmp_path)
    qc_path, target_paths = _write_records(tmp_path, session)
    _commit_pose_claims(tmp_path, session)

    result = evaluate_registration_readiness(
        session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
        evidence_transaction_root=tmp_path / "evidence_transactions",
    )

    assert result.registration_ready is True
    assert result.pose_gate is not None
    assert result.pose_gate.passed is True
    assert result.pose_gate.claim_ids
    assert result.gate_result is not None
    assert result.gate_result.passed is True


def test_registration_readiness_rejects_expired_pose_claim_authority(tmp_path) -> None:
    session = _pose_session(tmp_path)
    qc_path, target_paths = _write_records(tmp_path, session)
    _commit_pose_claims(tmp_path, session)
    expired_session = session.model_copy(
        update={"lease_expires_at": datetime.now() - timedelta(seconds=1)}
    )

    result = evaluate_registration_readiness(
        expired_session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
        evidence_transaction_root=tmp_path / "evidence_transactions",
    )

    reason_text = " ".join(result.reasons)
    assert result.registration_ready is False
    assert "session lease is expired" in reason_text
    assert "authority expired" in reason_text


def test_registration_readiness_rejects_pose_claims_before_session_update(
    tmp_path,
) -> None:
    session = _pose_session(tmp_path)
    qc_path, target_paths = _write_records(tmp_path, session)
    _commit_pose_claims(tmp_path, session)
    updated_session = session.model_copy(
        update={"updated_at": datetime.now() + timedelta(seconds=1)}
    )

    result = evaluate_registration_readiness(
        updated_session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
        evidence_transaction_root=tmp_path / "evidence_transactions",
    )

    assert result.registration_ready is False
    assert "predates active session authority" in " ".join(result.reasons)


def test_registration_readiness_ignores_cross_session_pose_claims(tmp_path) -> None:
    session = _pose_session(tmp_path)
    qc_path, target_paths = _write_records(tmp_path, session)
    other_session = session.model_copy(update={"session_id": "other-session"})
    pose = _pose()
    orientation_path, orientation_checksum = _artifact(tmp_path, "pose-orientation.txt")
    upright_path, upright_checksum = _artifact(tmp_path, "fixture-upright.txt")
    claims = derive_fixture_pose_claims(
        pose,
        [
            fixture_pose_evidence_packet(
                pose,
                session=other_session,
                evidence_id="pose-orientation-evidence-1",
                source_kind=EvidenceSourceKind.FIXTURE_POSE_ORIENTATION,
                artifact_path=orientation_path,
                checksum_sha256=orientation_checksum,
                quality=EvidenceQuality.USABLE,
                payload={"orientation": "rot180", "slot": "5", "value": True},
            ),
            fixture_pose_evidence_packet(
                pose,
                session=other_session,
                evidence_id="fixture-upright-evidence-1",
                source_kind=EvidenceSourceKind.FIXTURE_UPRIGHT,
                artifact_path=upright_path,
                checksum_sha256=upright_checksum,
                quality=EvidenceQuality.USABLE,
                payload={"fixture_upright": True, "slot": "5"},
            ),
        ],
        session=other_session,
    )

    result = evaluate_registration_readiness(
        session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
        pose_claims=claims,
        evidence_transaction_root=tmp_path / "evidence_transactions",
    )

    assert result.registration_ready is False
    assert "ignored 2 fixture pose claim(s) from another session" in result.reasons
    assert result.pose_gate is not None
    assert result.pose_gate.missing_claims


def test_registration_readiness_blocks_pose_digest_mismatch(tmp_path) -> None:
    session = _pose_session(tmp_path)
    qc_path, target_paths = _write_records(tmp_path, session)
    bad_record = _target_record(session, "center_high_z")
    bad_record.pose_digest_sha256 = "0" * 64
    write_target_class_record(bad_record, target_paths[0])
    _commit_pose_claims(tmp_path, session)

    result = evaluate_registration_readiness(
        session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
        evidence_transaction_root=tmp_path / "evidence_transactions",
    )

    assert result.registration_ready is False
    assert "pose digest does not match session pose" in " ".join(result.reasons)


def test_registration_readiness_fails_if_session_is_not_ready_no_motion(tmp_path) -> None:
    session = _session()
    session.state = "maintenance_run_created"
    qc_path, target_paths = _write_records(tmp_path, session)

    result = evaluate_registration_readiness(
        session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
    )

    assert result.registration_ready is False
    assert "not ready_no_motion" in " ".join(result.reasons)
