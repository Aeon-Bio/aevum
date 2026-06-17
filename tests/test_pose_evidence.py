from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from aevum_cad.labware import build_labware_definition
from aevum_cad.params import load_params
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.evidence import (
    append_evidence_event,
    commit_evidence_transaction,
    load_committed_evidence_claims,
)
from aevum_ot2.core.models import (
    BridgeSession,
    CameraCaptureResult,
    EvidenceClaim,
    EvidenceEvent,
    EvidencePacket,
    EvidenceQuality,
    EvidenceSourceKind,
)
from aevum_ot2.core.pose import (
    POSE_UPRIGHT_CLAIM,
    FixtureOrientation,
    fixture_pose_from_labware_definition,
    pose_match_gate,
    pose_orientation_claim_type,
)
from aevum_ot2.core.pose_evidence import (
    build_fixture_pose_evidence_artifact,
    commit_fixture_pose_claims,
    commit_fixture_pose_evidence_artifact,
    derive_fixture_pose_claims,
    fixture_pose_evidence_packet,
    fixture_pose_evidence_packets_from_artifact,
    load_fixture_pose_evidence_artifact,
    write_fixture_pose_evidence_artifact,
)


def _session() -> BridgeSession:
    identity = current_fixture_identity()
    now = datetime.now()
    pose = _pose()
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
        slot="5",
        fixture_identity=identity,
        fixture_orientation="rot180",
        fixture_pose_digest_sha256=pose.pose_digest_sha256,
        fixture_pose_path="data/measurements/sessions/session-1/fixture_pose.json",
        definition_uri="aevum/aevum_p300_poc_fixture_rot180/1",
        loaded_labware_id="fixture-1",
        evidence_index_path="data/measurements/sessions/session-1/evidence_index.json",
    )


def _pose():
    return fixture_pose_from_labware_definition(
        current_fixture_identity(),
        slot="5",
        orientation=FixtureOrientation.ROT180,
        canonical_labware_definition=build_labware_definition(load_params()),
    )


def _artifact(tmp_path: Path, name: str) -> tuple[Path, str]:
    path = tmp_path / name
    path.write_text(f"{name}\n")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _bind_session_evidence(session: BridgeSession, tmp_path: Path) -> BridgeSession:
    session.evidence_index_path = str(
        tmp_path / "sessions" / session.session_id / "evidence_index.json"
    )
    return session


def _camera_capture(
    session: BridgeSession,
    tmp_path: Path,
    name: str,
    *,
    captured_at: datetime | None = None,
) -> tuple[Path, CameraCaptureResult]:
    _bind_session_evidence(session, tmp_path)
    path, checksum = _artifact(tmp_path, name)
    capture = CameraCaptureResult(
        robot_url=session.robot_url,
        captured_at=captured_at or datetime.now(),
        endpoint="/camera/picture",
        image_path=str(path),
        image_checksum_sha256=checksum,
        content_type="image/jpg",
        bytes_written=path.stat().st_size,
    )
    append_evidence_event(
        EvidenceEvent(
            event_type="ot2_camera_picture",
            session_id=session.session_id,
            summary="captured test camera image",
            payload=capture.model_dump(mode="json"),
        ),
        path=session.evidence_index_path,
    )
    return path, capture


def _packets(session: BridgeSession, tmp_path: Path):
    pose = _pose()
    image_path, camera_capture = _camera_capture(session, tmp_path, "slot5.jpg")
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
    return fixture_pose_evidence_packets_from_artifact(
        pose,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )


def _raw_packets(session: BridgeSession, tmp_path: Path):
    pose = _pose()
    orientation_path, orientation_checksum = _artifact(tmp_path, "pose-orientation.txt")
    upright_path, upright_checksum = _artifact(tmp_path, "fixture-upright.txt")
    return [
        fixture_pose_evidence_packet(
            pose,
            session=session,
            evidence_id="pose-orientation-evidence-1",
            source_kind=EvidenceSourceKind.FIXTURE_POSE_ORIENTATION,
            artifact_path=orientation_path,
            checksum_sha256=orientation_checksum,
            quality=EvidenceQuality.USABLE,
            payload={
                "orientation": "rot180",
                "slot": "5",
                "value": True,
                "image_path": str(orientation_path),
                "image_checksum_sha256": orientation_checksum,
            },
        ),
        fixture_pose_evidence_packet(
            pose,
            session=session,
            evidence_id="fixture-upright-evidence-1",
            source_kind=EvidenceSourceKind.FIXTURE_UPRIGHT,
            artifact_path=upright_path,
            checksum_sha256=upright_checksum,
            quality=EvidenceQuality.USABLE,
            payload={
                "fixture_upright": True,
                "slot": "5",
                "image_path": str(upright_path),
                "image_checksum_sha256": upright_checksum,
            },
        ),
    ]


def _pose_gate(pose, claims, session: BridgeSession):
    return pose_match_gate(
        pose,
        claims=claims,
        expected_session_id=session.session_id,
        expected_robot_url=session.robot_url,
        expected_evidence_index_path=session.evidence_index_path,
        expected_claim_not_before=session.updated_at,
        claim_expires_at=session.lease_expires_at,
        claim_valid_at=datetime.now(),
    )


def test_derive_pose_claims_from_usable_pose_evidence_packets(tmp_path) -> None:
    pose = _pose()
    session = _session()
    claims = derive_fixture_pose_claims(pose, _packets(session, tmp_path), session=session)

    assert {claim.claim_type for claim in claims} == {
        pose_orientation_claim_type(
            orientation=pose.orientation,
            slot=pose.slot,
            fixture_definition_sha256=pose.fixture_definition_sha256,
        ),
        POSE_UPRIGHT_CLAIM,
    }
    assert all(claim.quality == EvidenceQuality.USABLE for claim in claims)
    assert all(claim.evidence for claim in claims)
    assert _pose_gate(pose, claims, session).passed is True


def test_session_scoped_pose_claims_require_authority_window(tmp_path) -> None:
    pose = _pose()
    session = _session()
    claims = derive_fixture_pose_claims(pose, _packets(session, tmp_path), session=session)

    gate = pose_match_gate(pose, claims=claims)

    assert gate.passed is False
    assert any("explicit session authority window" in blocker for blocker in gate.blockers)


def test_pose_claims_expire_with_session_authority_window(tmp_path) -> None:
    pose = _pose()
    session = _session()
    claims = derive_fixture_pose_claims(pose, _packets(session, tmp_path), session=session)

    stale_gate = pose_match_gate(
        pose,
        claims=claims,
        expected_session_id=session.session_id,
        expected_robot_url=session.robot_url,
        expected_evidence_index_path=session.evidence_index_path,
        expected_claim_not_before=datetime.now() + timedelta(seconds=1),
        claim_expires_at=session.lease_expires_at,
        claim_valid_at=datetime.now(),
    )
    expired_gate = pose_match_gate(
        pose,
        claims=claims,
        expected_session_id=session.session_id,
        expected_robot_url=session.robot_url,
        expected_evidence_index_path=session.evidence_index_path,
        expected_claim_not_before=session.updated_at,
        claim_expires_at=datetime.now() - timedelta(seconds=1),
        claim_valid_at=datetime.now(),
    )

    assert stale_gate.passed is False
    assert any("predates active session authority" in blocker for blocker in stale_gate.blockers)
    assert expired_gate.passed is False
    assert any("authority expired" in blocker for blocker in expired_gate.blockers)


def test_pose_match_gate_lets_fresh_pose_claims_supersede_stale_claims(
    tmp_path,
) -> None:
    pose = _pose()
    session = _session()
    claims = derive_fixture_pose_claims(pose, _packets(session, tmp_path), session=session)
    stale_claims = [
        claim.model_copy(
            update={
                "claim_id": f"{claim.claim_id}:stale",
                "created_at": session.updated_at - timedelta(seconds=1),
                "evidence": [
                    handle.model_copy(
                        update={"created_at": session.updated_at - timedelta(seconds=1)}
                    )
                    for handle in claim.evidence
                ],
            }
        )
        for claim in claims
    ]

    gate = _pose_gate(pose, stale_claims + claims, session)

    assert gate.passed is True
    assert not any("duplicate pose claims" in blocker for blocker in gate.blockers)
    assert set(gate.claim_ids) == {claim.claim_id for claim in claims}


def test_pose_match_gate_lets_fresh_claims_supersede_stale_artifact_claims(
    tmp_path,
) -> None:
    pose = _pose()
    session = _session()
    claims = derive_fixture_pose_claims(pose, _packets(session, tmp_path), session=session)
    stale_at = session.updated_at - timedelta(seconds=1)
    stale_artifact_path = tmp_path / "fixture_pose_evidence_stale_artifact.json"
    artifact_data = json.loads(Path(claims[0].evidence[0].path).read_text())
    artifact_data["created_at"] = stale_at.isoformat()
    artifact_data["image_captured_at"] = stale_at.isoformat()
    stale_artifact_path.write_text(json.dumps(artifact_data, indent=2) + "\n")
    stale_artifact_checksum = hashlib.sha256(stale_artifact_path.read_bytes()).hexdigest()
    stale_claims = [
        claim.model_copy(
            update={
                "claim_id": f"{claim.claim_id}:stale-artifact",
                "evidence": [
                    handle.model_copy(
                        update={
                            "path": str(stale_artifact_path),
                            "checksum_sha256": stale_artifact_checksum,
                        }
                    )
                    for handle in claim.evidence
                ],
            }
        )
        for claim in claims
    ]

    gate = _pose_gate(pose, stale_claims + claims, session)

    assert gate.passed is True
    assert not any("duplicate pose claims" in blocker for blocker in gate.blockers)
    assert set(gate.claim_ids) == {claim.claim_id for claim in claims}


def test_pose_match_gate_still_rejects_duplicate_current_pose_claims(
    tmp_path,
) -> None:
    pose = _pose()
    session = _session()
    claims = derive_fixture_pose_claims(pose, _packets(session, tmp_path), session=session)
    duplicate_current_claim = claims[0].model_copy(
        update={"claim_id": f"{claims[0].claim_id}:duplicate"}
    )

    gate = _pose_gate(pose, [duplicate_current_claim, *claims], session)

    assert gate.passed is False
    assert any("duplicate pose claims" in blocker for blocker in gate.blockers)


def test_pose_match_gate_fails_closed_for_mixed_timezone_duplicate_claims(
    tmp_path,
) -> None:
    pose = _pose()
    session = _session()
    claims = derive_fixture_pose_claims(pose, _packets(session, tmp_path), session=session)
    timezone_aware_claim = claims[0].model_copy(
        update={
            "claim_id": f"{claims[0].claim_id}:timezone-aware",
            "created_at": datetime.now(UTC),
        }
    )

    gate = _pose_gate(pose, [timezone_aware_claim, *claims], session)

    assert gate.passed is False
    assert any("duplicate pose claims" in blocker for blocker in gate.blockers)


def test_pose_claim_freshness_requires_claim_handle_and_artifact_timestamps(
    tmp_path,
) -> None:
    pose = _pose()
    session = _session()
    claims = derive_fixture_pose_claims(pose, _packets(session, tmp_path), session=session)
    missing_claim_created_at = [
        EvidenceClaim.model_validate(
            {
                key: value
                for key, value in claims[0].model_dump(mode="json").items()
                if key != "created_at"
            }
        ),
        claims[1],
    ]
    missing_handle_created_at = [
        claims[0].model_copy(
            update={
                "evidence": [
                    claims[0].evidence[0].model_copy(update={"created_at": None})
                ]
            }
        ),
        claims[1],
    ]
    artifact_path = Path(claims[0].evidence[0].path)
    artifact_data = json.loads(artifact_path.read_text())
    artifact_data.pop("created_at")
    artifact_path.write_text(json.dumps(artifact_data, indent=2) + "\n")
    artifact_checksum = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    missing_artifact_created_at = [
        claim.model_copy(
            update={
                "evidence": [
                    claim.evidence[0].model_copy(update={"checksum_sha256": artifact_checksum})
                ]
            }
        )
        for claim in claims
    ]

    claim_gate = pose_match_gate(
        pose,
        claims=missing_claim_created_at,
        expected_session_id=session.session_id,
        expected_robot_url=session.robot_url,
        expected_evidence_index_path=session.evidence_index_path,
        expected_claim_not_before=session.updated_at,
        claim_expires_at=session.lease_expires_at,
        claim_valid_at=datetime.now(),
    )
    handle_gate = pose_match_gate(
        pose,
        claims=missing_handle_created_at,
        expected_session_id=session.session_id,
        expected_robot_url=session.robot_url,
        expected_evidence_index_path=session.evidence_index_path,
        expected_claim_not_before=session.updated_at,
        claim_expires_at=session.lease_expires_at,
        claim_valid_at=datetime.now(),
    )
    artifact_gate = pose_match_gate(
        pose,
        claims=missing_artifact_created_at,
        expected_session_id=session.session_id,
        expected_robot_url=session.robot_url,
        expected_evidence_index_path=session.evidence_index_path,
        expected_claim_not_before=session.updated_at,
        claim_expires_at=session.lease_expires_at,
        claim_valid_at=datetime.now(),
    )

    assert "created_at is missing" in " ".join(claim_gate.blockers)
    assert "evidence created_at is missing" in " ".join(handle_gate.blockers)
    assert "artifact created_at is missing" in " ".join(artifact_gate.blockers)


def test_fixture_pose_evidence_rejects_stale_image_capture(tmp_path) -> None:
    pose = _pose()
    session = _session()
    image_path, camera_capture = _camera_capture(
        session,
        tmp_path,
        "slot5.jpg",
        captured_at=session.updated_at - timedelta(seconds=1),
    )
    artifact = build_fixture_pose_evidence_artifact(
        pose,
        session=session,
        artifact_id="fixture-pose-evidence-1",
        image_path=image_path,
        observed_orientation="rot180",
        fixture_upright=True,
        inspection_note="visible fiducials",
        camera_capture=camera_capture,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_fixture_pose_evidence_artifact(
        artifact,
        tmp_path / "fixture_pose_evidence.json",
    )

    try:
        fixture_pose_evidence_packets_from_artifact(
            pose,
            artifact,
            session=session,
            artifact_path=artifact_path,
        )
    except ValueError as exc:
        assert "image capture predates active session authority" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_fixture_pose_evidence_requires_indexed_camera_capture(tmp_path) -> None:
    pose = _pose()
    session = _session()
    _bind_session_evidence(session, tmp_path)
    image_path, checksum = _artifact(tmp_path, "slot5.jpg")
    camera_capture = CameraCaptureResult(
        robot_url=session.robot_url,
        captured_at=datetime.now(),
        endpoint="/camera/picture",
        image_path=str(image_path),
        image_checksum_sha256=checksum,
        content_type="image/jpg",
        bytes_written=image_path.stat().st_size,
    )
    artifact = build_fixture_pose_evidence_artifact(
        pose,
        session=session,
        artifact_id="fixture-pose-evidence-1",
        image_path=image_path,
        observed_orientation="rot180",
        fixture_upright=True,
        inspection_note="visible fiducials",
        camera_capture=camera_capture,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_fixture_pose_evidence_artifact(
        artifact,
        tmp_path / "fixture_pose_evidence.json",
    )

    try:
        fixture_pose_evidence_packets_from_artifact(
            pose,
            artifact,
            session=session,
            artifact_path=artifact_path,
        )
    except ValueError as exc:
        assert "image capture is not indexed" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_pose_gate_requires_indexed_camera_capture_for_direct_claims(tmp_path) -> None:
    pose = _pose()
    session = _session()
    claims = derive_fixture_pose_claims(pose, _packets(session, tmp_path), session=session)
    Path(session.evidence_index_path).write_text('{"schema_version": 1, "events": []}\n')

    gate = _pose_gate(pose, claims, session)

    assert gate.passed is False
    assert any("camera capture is not indexed" in blocker for blocker in gate.blockers)


def test_fixture_pose_evidence_rejects_unscoped_camera_capture_event(tmp_path) -> None:
    pose = _pose()
    session = _session()
    _bind_session_evidence(session, tmp_path)
    image_path, checksum = _artifact(tmp_path, "slot5.jpg")
    camera_capture = CameraCaptureResult(
        robot_url=session.robot_url,
        captured_at=datetime.now(),
        endpoint="/camera/picture",
        image_path=str(image_path),
        image_checksum_sha256=checksum,
        content_type="image/jpg",
        bytes_written=image_path.stat().st_size,
    )
    append_evidence_event(
        EvidenceEvent(
            event_type="ot2_camera_picture",
            summary="unscoped legacy camera image",
            payload=camera_capture.model_dump(mode="json"),
        ),
        path=session.evidence_index_path,
    )
    artifact = build_fixture_pose_evidence_artifact(
        pose,
        session=session,
        artifact_id="fixture-pose-evidence-1",
        image_path=image_path,
        observed_orientation="rot180",
        fixture_upright=True,
        inspection_note="visible fiducials",
        camera_capture=camera_capture,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_fixture_pose_evidence_artifact(
        artifact,
        tmp_path / "fixture_pose_evidence.json",
    )

    try:
        fixture_pose_evidence_packets_from_artifact(
            pose,
            artifact,
            session=session,
            artifact_path=artifact_path,
        )
    except ValueError as exc:
        assert "image capture is not indexed" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_fixture_pose_evidence_rejects_cross_robot_camera_capture(tmp_path) -> None:
    pose = _pose()
    session = _session()
    image_path, camera_capture = _camera_capture(session, tmp_path, "slot5.jpg")
    artifact = build_fixture_pose_evidence_artifact(
        pose,
        session=session,
        artifact_id="fixture-pose-evidence-1",
        image_path=image_path,
        observed_orientation="rot180",
        fixture_upright=True,
        inspection_note="visible fiducials",
        camera_capture=camera_capture.model_copy(update={"robot_url": "http://other-ot2"}),
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_fixture_pose_evidence_artifact(
        artifact,
        tmp_path / "fixture_pose_evidence.json",
    )

    try:
        fixture_pose_evidence_packets_from_artifact(
            pose,
            artifact,
            session=session,
            artifact_path=artifact_path,
        )
    except ValueError as exc:
        assert "image capture robot URL does not match session" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_pose_gate_blocks_timezone_aware_claim_and_handle_timestamps(tmp_path) -> None:
    pose = _pose()
    session = _session()
    claims = derive_fixture_pose_claims(pose, _packets(session, tmp_path), session=session)
    aware_claim = [
        claims[0].model_copy(update={"created_at": datetime.now(UTC)}),
        claims[1],
    ]
    aware_handle = [
        claims[0].model_copy(
            update={
                "evidence": [
                    claims[0].evidence[0].model_copy(
                        update={"created_at": datetime.now(UTC)}
                    )
                ]
            }
        ),
        claims[1],
    ]

    claim_gate = _pose_gate(pose, aware_claim, session)
    handle_gate = _pose_gate(pose, aware_handle, session)

    assert claim_gate.passed is False
    assert "created_at is timezone-aware" in " ".join(claim_gate.blockers)
    assert handle_gate.passed is False
    assert "evidence created_at is timezone-aware" in " ".join(handle_gate.blockers)


def test_pose_claim_derivation_fails_closed_on_mismatched_packet(tmp_path) -> None:
    pose = _pose()
    session = _session()
    path, checksum = _artifact(tmp_path, "pose-orientation.txt")
    packet = fixture_pose_evidence_packet(
        pose,
        session=session,
        evidence_id="pose-orientation-evidence-1",
        source_kind=EvidenceSourceKind.FIXTURE_POSE_ORIENTATION,
        artifact_path=path,
        checksum_sha256=checksum,
        quality=EvidenceQuality.USABLE,
        payload={"orientation": "canonical", "slot": "5", "value": True},
    )

    claims = derive_fixture_pose_claims(pose, [packet], session=session)
    gate = _pose_gate(pose, claims, session)

    assert claims[0].quality == EvidenceQuality.FAILED
    assert gate.passed is False
    assert "fixture_upright" in gate.missing_claims
    assert any("orientation evidence does not match" in blocker for blocker in gate.blockers)


def test_pose_claim_derivation_requires_artifact_for_usable_packet() -> None:
    pose = _pose()
    session = _session()
    packet = fixture_pose_evidence_packet(
        pose,
        session=session,
        evidence_id="pose-orientation-evidence-1",
        source_kind=EvidenceSourceKind.FIXTURE_POSE_ORIENTATION,
        quality=EvidenceQuality.USABLE,
        payload={"orientation": "rot180", "slot": "5", "value": True},
    )

    claims = derive_fixture_pose_claims(pose, [packet], session=session)
    gate = _pose_gate(pose, claims, session)

    assert claims[0].quality == EvidenceQuality.FAILED
    assert any("artifact path and checksum" in blocker for blocker in gate.blockers)


def test_pose_claim_derivation_requires_packet_pose_identity(tmp_path) -> None:
    pose = _pose()
    session = _session()
    path, checksum = _artifact(tmp_path, "pose-orientation.txt")
    packet = EvidencePacket(
        evidence_id="pose-orientation-evidence-1",
        source_kind=EvidenceSourceKind.FIXTURE_POSE_ORIENTATION,
        session_id=session.session_id,
        artifact_path=str(path),
        checksum_sha256=checksum,
        quality=EvidenceQuality.USABLE,
        payload={
            "pose_digest_sha256": pose.pose_digest_sha256,
            "orientation": "rot180",
            "slot": "5",
            "value": True,
        },
    )

    claims = derive_fixture_pose_claims(pose, [packet], session=session)
    gate = _pose_gate(pose, claims, session)

    assert claims[0].quality == EvidenceQuality.FAILED
    assert any("fixture does not match" in blocker for blocker in gate.blockers)
    assert any("labware checksum does not match" in blocker for blocker in gate.blockers)
    assert any("pose digest does not match" in blocker for blocker in gate.blockers)


def test_commit_fixture_pose_claims_writes_transaction_claims(tmp_path) -> None:
    session = _session().model_copy(
        update={
            "evidence_index_path": str(tmp_path / "sessions/session-1/evidence_index.json"),
        }
    )
    pose = _pose()
    result = commit_fixture_pose_claims(
        pose,
        _packets(session, tmp_path),
        session=session,
        index_path=session.evidence_index_path,
        root=tmp_path / "evidence_transactions",
        transaction_id="pose-claims-1",
    )

    loaded_claims = load_committed_evidence_claims(
        index_path=session.evidence_index_path,
        root=tmp_path / "evidence_transactions",
    )

    assert result.manifest.session_id == session.session_id
    assert {claim.claim_type for claim in loaded_claims} == {
        POSE_UPRIGHT_CLAIM,
        pose_orientation_claim_type(
            orientation=pose.orientation,
            slot=pose.slot,
            fixture_definition_sha256=pose.fixture_definition_sha256,
        ),
    }
    assert _pose_gate(pose, loaded_claims, session).passed is True


def test_commit_fixture_pose_claims_rejects_raw_non_artifact_pose_packets(
    tmp_path,
) -> None:
    session = _session().model_copy(
        update={
            "evidence_index_path": str(tmp_path / "sessions/session-1/evidence_index.json"),
        }
    )

    try:
        commit_fixture_pose_claims(
            _pose(),
            _raw_packets(session, tmp_path),
            session=session,
            index_path=session.evidence_index_path,
            root=tmp_path / "evidence_transactions",
            transaction_id="raw-pose-claims",
        )
    except ValueError as exc:
        assert "FixturePoseEvidenceArtifact" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_pose_claim_transaction_rejects_forged_claim_packet_link(tmp_path) -> None:
    session = _session().model_copy(
        update={
            "evidence_index_path": str(tmp_path / "sessions/session-1/evidence_index.json"),
        }
    )
    pose = _pose()
    packets = _packets(session, tmp_path)
    claims = derive_fixture_pose_claims(pose, packets, session=session)
    forged_claims = [
        claims[0].model_copy(
            update={
                "evidence": [
                    claims[0].evidence[0].model_copy(
                        update={"checksum_sha256": "0" * 64}
                    )
                ]
            }
        ),
        claims[1],
    ]

    try:
        commit_evidence_transaction(
            packets=packets,
            claims=forged_claims,
            index_path=session.evidence_index_path,
            root=tmp_path / "evidence_transactions",
            transaction_id="forged-pose-claims",
            session_id=session.session_id,
        )
    except ValueError as exc:
        assert "checksum does not match packet" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_commit_fixture_pose_claims_rejects_global_index_for_session(tmp_path) -> None:
    session = _session().model_copy(
        update={
            "evidence_index_path": str(tmp_path / "sessions/session-1/evidence_index.json"),
        }
    )

    try:
        commit_fixture_pose_claims(
            _pose(),
            _packets(session, tmp_path),
            session=session,
            index_path=tmp_path / "ot2_evidence_index.json",
        )
    except ValueError as exc:
        assert "session evidence_index" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_fixture_pose_evidence_artifact_commits_pose_claims(tmp_path) -> None:
    session = _session().model_copy(
        update={
            "evidence_index_path": str(tmp_path / "sessions/session-1/evidence_index.json"),
        }
    )
    pose = _pose()
    image_path, camera_capture = _camera_capture(session, tmp_path, "slot5.jpg")
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

    loaded = load_fixture_pose_evidence_artifact(artifact_path)
    packets = fixture_pose_evidence_packets_from_artifact(
        pose,
        loaded,
        session=session,
        artifact_path=artifact_path,
    )
    commit_fixture_pose_evidence_artifact(
        pose,
        loaded,
        session=session,
        artifact_path=artifact_path,
        root=tmp_path / "evidence_transactions",
        transaction_id="pose-evidence-1",
    )
    loaded_claims = load_committed_evidence_claims(
        index_path=session.evidence_index_path,
        root=tmp_path / "evidence_transactions",
    )

    claims = derive_fixture_pose_claims(pose, packets, session=session)
    assert loaded == artifact
    assert _pose_gate(pose, claims, session).passed is True
    assert _pose_gate(pose, loaded_claims, session).passed is True

    image_path.write_text("tampered image\n")
    assert (
        load_committed_evidence_claims(
            index_path=session.evidence_index_path,
            root=tmp_path / "evidence_transactions",
        )
        == []
    )


def test_usable_fixture_pose_evidence_artifact_requires_inspection_note(tmp_path) -> None:
    image_path, _checksum = _artifact(tmp_path, "slot5.jpg")

    try:
        build_fixture_pose_evidence_artifact(
            _pose(),
            session=_session(),
            artifact_id="fixture-pose-evidence-1",
            image_path=image_path,
            observed_orientation="rot180",
            fixture_upright=True,
            inspection_note="",
            quality=EvidenceQuality.USABLE,
        )
    except ValueError as exc:
        assert "inspection note" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_loaded_usable_fixture_pose_evidence_artifact_requires_inspection_note(
    tmp_path,
) -> None:
    session = _session()
    image_path, camera_capture = _camera_capture(session, tmp_path, "slot5.jpg")
    artifact = build_fixture_pose_evidence_artifact(
        _pose(),
        session=session,
        artifact_id="fixture-pose-evidence-1",
        image_path=image_path,
        observed_orientation="rot180",
        fixture_upright=True,
        inspection_note="visible fiducials",
        camera_capture=camera_capture,
        quality=EvidenceQuality.USABLE,
    )
    invalid = artifact.model_copy(update={"inspection_note": ""})
    artifact_path = tmp_path / "fixture_pose_evidence.json"
    artifact_path.write_text(invalid.model_dump_json(indent=2) + "\n")

    try:
        load_fixture_pose_evidence_artifact(artifact_path)
    except ValueError as exc:
        assert "inspection note" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_fixture_pose_evidence_artifact_cannot_be_restamped_to_session(
    tmp_path,
) -> None:
    session = _session()
    pose = _pose()
    image_path, camera_capture = _camera_capture(session, tmp_path, "slot5.jpg")
    artifact = build_fixture_pose_evidence_artifact(
        pose,
        session=session,
        artifact_id="fixture-pose-evidence-1",
        image_path=image_path,
        observed_orientation="rot180",
        fixture_upright=True,
        inspection_note="visible fiducials",
        camera_capture=camera_capture,
        quality=EvidenceQuality.USABLE,
    ).model_copy(update={"session_id": "stale-session"})
    artifact_path = tmp_path / "fixture_pose_evidence.json"
    artifact_path.write_text(artifact.model_dump_json(indent=2) + "\n")

    try:
        fixture_pose_evidence_packets_from_artifact(
            pose,
            artifact,
            session=session,
            artifact_path=artifact_path,
        )
    except ValueError as exc:
        assert "session does not match active session" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_fixture_pose_evidence_artifact_must_match_artifact_path(tmp_path) -> None:
    session = _session()
    pose = _pose()
    image_path, camera_capture = _camera_capture(session, tmp_path, "slot5.jpg")
    artifact = build_fixture_pose_evidence_artifact(
        pose,
        session=session,
        artifact_id="fixture-pose-evidence-1",
        image_path=image_path,
        observed_orientation="rot180",
        fixture_upright=True,
        inspection_note="visible fiducials",
        camera_capture=camera_capture,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_fixture_pose_evidence_artifact(
        artifact,
        tmp_path / "fixture_pose_evidence.json",
    )
    mutated = artifact.model_copy(update={"notes": ["not what is on disk"]})

    try:
        fixture_pose_evidence_packets_from_artifact(
            pose,
            mutated,
            session=session,
            artifact_path=artifact_path,
        )
    except ValueError as exc:
        assert "does not match artifact path" in str(exc)
    else:
        raise AssertionError("expected ValueError")
