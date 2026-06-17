from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

import pytest

from aevum_cad.labware import build_labware_definition
from aevum_cad.params import load_params
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.evidence import append_evidence_event
from aevum_ot2.core.models import (
    CameraCaptureResult,
    EvidenceEvent,
    EvidenceQuality,
    GateName,
)
from aevum_ot2.core.pose import (
    WELL_IDENTITY_POLICY,
    FixtureOrientation,
    Point3D,
    canonical_to_installed,
    fixture_pose_from_labware_definition,
    load_fixture_pose,
    oriented_labware_definition,
    pose_digest_payload,
    pose_match_gate,
    write_fixture_pose,
)
from aevum_ot2.core.pose_evidence import (
    build_fixture_pose_evidence_artifact,
    derive_fixture_pose_claims,
    fixture_pose_evidence_packets_from_artifact,
    write_fixture_pose_evidence_artifact,
)


def _canonical_definition() -> dict[str, object]:
    return build_labware_definition(load_params())


def _rot180_pose():
    return fixture_pose_from_labware_definition(
        current_fixture_identity(),
        slot="5",
        orientation=FixtureOrientation.ROT180,
        canonical_labware_definition=_canonical_definition(),
    )


def _sha256_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pose_claims(tmp_path):
    identity = current_fixture_identity()
    pose = _rot180_pose()
    session = _claim_session(identity, pose)
    session.evidence_index_path = str(tmp_path / "sessions/session-1/evidence_index.json")
    image_path = tmp_path / "slot5.jpg"
    image_path.write_text("slot 5 image\n")
    image_checksum = _sha256_file(image_path)
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
    packets = fixture_pose_evidence_packets_from_artifact(
        pose,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )
    return derive_fixture_pose_claims(pose, packets, session=session)


def _claim_session(identity, pose):
    from aevum_ot2.core.models import BridgeSession

    now = datetime.now()
    return BridgeSession(
        session_id="session-1",
        kind="registration",
        owner_id="agent-1",
        robot_url="http://ot2.local:31950",
        state="ready_no_motion",
        created_at=now,
        updated_at=now,
        lease_expires_at=now + timedelta(minutes=10),
        maintenance_run_id="maintenance-run-1",
        slot=pose.slot,
        fixture_identity=identity,
        fixture_orientation=pose.orientation.value,
        fixture_pose_digest_sha256=pose.pose_digest_sha256,
        fixture_pose_path="data/measurements/sessions/session-1/fixture_pose.json",
        definition_uri="aevum/aevum_p300_poc_fixture_rot180/1",
        loaded_labware_id="fixture-1",
        evidence_index_path="data/measurements/sessions/session-1/evidence_index.json",
    )


def _authority_window(tmp_path=None) -> dict[str, object]:
    now = datetime.now()
    window: dict[str, object] = {
        "expected_session_id": "session-1",
        "expected_robot_url": "http://ot2.local:31950",
        "expected_claim_not_before": now - timedelta(minutes=5),
        "claim_expires_at": now + timedelta(minutes=5),
        "claim_valid_at": now,
    }
    if tmp_path is not None:
        window["expected_evidence_index_path"] = str(
            tmp_path / "sessions/session-1/evidence_index.json"
        )
    return window


def test_rot180_transform_maps_a1_by_fixture_dimensions() -> None:
    definition = _canonical_definition()
    a1 = definition["wells"]["A1"]
    pose = _rot180_pose()

    transformed = canonical_to_installed(
        Point3D(x=a1["x"], y=a1["y"], z=a1["z"]),
        pose,
    )

    assert transformed.x == 102.76
    assert transformed.y == 60.48
    assert transformed.z == 67.6
    assert transformed.frame == "installed"


def test_direction_suffixed_access_targets_keep_canonical_frame_semantics() -> None:
    definition = _canonical_definition()
    a1 = definition["wells"]["A1"]
    pose = _rot180_pose()

    port = canonical_to_installed(
        Point3D(x=a1["x"] + 1.5, y=a1["y"], z=a1["z"]),
        pose,
    )

    assert port.x == 101.26
    assert port.y == 60.48


def test_installed_labware_points_cannot_be_transformed_again() -> None:
    oriented = oriented_labware_definition(
        _canonical_definition(),
        orientation=FixtureOrientation.ROT180,
    )
    a1 = oriented["wells"]["A1"]

    with pytest.raises(ValueError, match="canonical-frame"):
        canonical_to_installed(
            Point3D(x=a1["x"], y=a1["y"], z=a1["z"], frame="installed"),
            _rot180_pose(),
        )


def test_oriented_labware_preserves_well_names_with_distinct_identity() -> None:
    definition = _canonical_definition()
    oriented = oriented_labware_definition(
        definition,
        orientation=FixtureOrientation.ROT180,
    )

    assert oriented["parameters"]["loadName"] == "aevum_p300_poc_fixture_rot180"
    assert oriented["wells"]["A1"]["x"] == 102.76
    assert oriented["wells"]["A1"]["y"] == 60.48
    assert "A1" in oriented["groups"][0]["wells"]


def test_rot180_rejects_unhandled_coordinate_bearing_labware_fields() -> None:
    definition = _canonical_definition()
    definition["metadata"]["cameraPose"] = {"x": 1, "y": 2, "z": 3}

    with pytest.raises(ValueError, match="unsupported coordinate-bearing"):
        oriented_labware_definition(definition, orientation=FixtureOrientation.ROT180)


def test_rot180_rejects_nonzero_corner_offset() -> None:
    definition = _canonical_definition()
    definition["cornerOffsetFromSlot"]["x"] = 1

    with pytest.raises(ValueError, match="zero cornerOffsetFromSlot"):
        oriented_labware_definition(definition, orientation=FixtureOrientation.ROT180)


def test_canonical_pose_uses_nonempty_canonical_labware_identity_fields() -> None:
    identity = current_fixture_identity()
    pose = fixture_pose_from_labware_definition(
        identity,
        slot="1",
        orientation=FixtureOrientation.CANONICAL,
        canonical_labware_definition=_canonical_definition(),
    )

    assert pose.oriented_labware_load_name == identity.load_name
    assert len(pose.oriented_labware_definition_sha256) == 64
    assert len(pose.pose_digest_sha256) == 64


def test_pose_digest_has_stable_keys_and_changes_with_pose_inputs() -> None:
    identity = current_fixture_identity()
    pose = _rot180_pose()
    same = _rot180_pose()
    different_slot = fixture_pose_from_labware_definition(
        identity,
        slot="1",
        orientation=FixtureOrientation.ROT180,
        canonical_labware_definition=_canonical_definition(),
    )
    canonical = fixture_pose_from_labware_definition(
        identity,
        slot="5",
        orientation=FixtureOrientation.CANONICAL,
        canonical_labware_definition=_canonical_definition(),
    )

    assert pose.pose_digest_sha256 == same.pose_digest_sha256
    assert pose.pose_digest_sha256 != different_slot.pose_digest_sha256
    assert pose.pose_digest_sha256 != canonical.pose_digest_sha256
    payload = pose_digest_payload(pose)
    assert "transform_matrix_canonical_to_installed_mm" in payload
    assert "transform_canonical_to_installed_mm" not in payload
    assert payload["well_identity_policy"] == WELL_IDENTITY_POLICY


def test_pose_match_gate_requires_nonempty_digest_and_evidence_claims(tmp_path) -> None:
    pose = _rot180_pose()

    missing_claims_gate = pose_match_gate(pose)
    passing_gate = pose_match_gate(
        pose,
        claims=_pose_claims(tmp_path),
        **_authority_window(tmp_path),
    )
    empty_digest_gate = pose_match_gate(pose.model_copy(update={"pose_digest_sha256": ""}))

    assert missing_claims_gate.gate_name == GateName.POSE_MATCH
    assert missing_claims_gate.passed is False
    assert any("fixture_pose_orientation" in claim for claim in missing_claims_gate.missing_claims)
    assert passing_gate.passed is True
    assert passing_gate.motion_allowed is False
    assert empty_digest_gate.passed is False
    assert "pose_digest_sha256" in empty_digest_gate.missing_claims


def test_pose_match_gate_rejects_free_floating_claims(tmp_path) -> None:
    pose = _rot180_pose()
    claims = [claim.model_copy(update={"evidence": []}) for claim in _pose_claims(tmp_path)]

    gate = pose_match_gate(pose, claims=claims, **_authority_window(tmp_path))

    assert gate.passed is False
    assert any("evidence handle" in blocker for blocker in gate.blockers)


def test_pose_match_gate_rejects_unsupported_claim_method(tmp_path) -> None:
    pose = _rot180_pose()
    claims = [
        claim.model_copy(update={"method": "manual_assertion"})
        for claim in _pose_claims(tmp_path)
    ]

    gate = pose_match_gate(pose, claims=claims, **_authority_window(tmp_path))

    assert gate.passed is False
    assert any("unsupported method" in blocker for blocker in gate.blockers)


def test_pose_match_gate_rejects_digest_scope_mismatch(tmp_path) -> None:
    pose = _rot180_pose()
    gate = pose_match_gate(
        pose,
        expected_pose_digest_sha256="0" * 64,
        claims=_pose_claims(tmp_path),
        **_authority_window(tmp_path),
    )

    assert gate.passed is False
    assert "pose digest does not match expected scope" in gate.blockers


def test_fixture_orientation_v1_rejects_enum_widening() -> None:
    with pytest.raises(ValueError):
        FixtureOrientation("rot90")


def test_fixture_pose_round_trips_as_durable_json(tmp_path) -> None:
    pose = _rot180_pose()
    path = write_fixture_pose(pose, tmp_path / "fixture_pose.json")

    loaded = load_fixture_pose(path)

    assert loaded == pose
    assert loaded.pose_digest_sha256 == pose.pose_digest_sha256
