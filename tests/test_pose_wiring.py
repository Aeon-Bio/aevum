from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from aevum_cad.labware import build_labware_definition
from aevum_cad.params import load_params
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.evidence import append_evidence_event
from aevum_ot2.core.models import (
    BridgeSession,
    CameraCaptureResult,
    EvidenceClaim,
    EvidenceEvent,
    EvidenceQuality,
    OffsetAuthorityState,
    OffsetRecord,
    OffsetRegistry,
)
from aevum_ot2.core.pose import (
    POSE_UPRIGHT_CLAIM,
    FixtureOrientation,
    fixture_pose_from_labware_definition,
)
from aevum_ot2.core.pose_evidence import (
    build_fixture_pose_evidence_artifact,
    derive_fixture_pose_claims,
    fixture_pose_evidence_packets_from_artifact,
    write_fixture_pose_evidence_artifact,
)
from aevum_ot2.core.records import (
    TargetClassResult,
    TargetClassVerificationRecord,
    scaffold_fixture_qc_record,
    scaffold_target_class_record,
    target_class_authority,
    target_class_record_handle,
)
from aevum_ot2.core.registry import offset_match_gate
from aevum_ot2.core.safety import build_fixture_safety_profile, home_clearance_gate


def _pose(slot: str = "5", orientation: FixtureOrientation = FixtureOrientation.ROT180):
    return fixture_pose_from_labware_definition(
        current_fixture_identity(),
        slot=slot,
        orientation=orientation,
        canonical_labware_definition=build_labware_definition(load_params()),
    )


def _sha256_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _session(pose_digest_sha256: str = "") -> BridgeSession:
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
        slot="5",
        fixture_identity=identity,
        fixture_orientation="rot180" if pose_digest_sha256 else "",
        fixture_pose_digest_sha256=pose_digest_sha256,
        fixture_pose_path="data/measurements/sessions/session-1/fixture_pose.json"
        if pose_digest_sha256
        else "",
        definition_uri="aevum/aevum_p300_poc_fixture/1",
        loaded_labware_id="fixture-1",
        evidence_index_path="data/measurements/ot2_evidence_index.json",
    )


def _bind_session_evidence(session: BridgeSession, tmp_path) -> BridgeSession:
    session.evidence_index_path = str(
        tmp_path / "sessions" / session.session_id / "evidence_index.json"
    )
    return session


def _pose_claims(tmp_path, pose_digest_sha256: str, *, pose=None) -> list[EvidenceClaim]:
    active_pose = pose or _pose()
    image_path = tmp_path / f"{active_pose.orientation.value}_{active_pose.slot}.jpg"
    image_path.write_text("slot fixture image\n")
    session = _session(pose_digest_sha256)
    _bind_session_evidence(session, tmp_path)
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
        active_pose,
        session=session,
        artifact_id=f"fixture-pose-{active_pose.orientation.value}-{active_pose.slot}",
        image_path=image_path,
        observed_orientation=active_pose.orientation,
        fixture_upright=True,
        inspection_note="visible fiducials",
        camera_capture=camera_capture,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_fixture_pose_evidence_artifact(
        artifact,
        tmp_path / f"{artifact.artifact_id}.json",
    )
    packets = fixture_pose_evidence_packets_from_artifact(
        active_pose,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )
    return derive_fixture_pose_claims(active_pose, packets, session=session)


def test_target_scaffold_and_handle_include_pose_when_session_has_pose() -> None:
    pose = _pose()
    session = _session(pose.pose_digest_sha256)

    record = scaffold_target_class_record(
        session,
        "center_high_z",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
    )
    handle = target_class_record_handle(record, "target.json")

    assert record.pose_digest_sha256 == pose.pose_digest_sha256
    assert f"pose-{pose.pose_digest_sha256[:12]}" in handle.record_id


def test_target_authority_blocks_pose_less_record_when_pose_is_supplied() -> None:
    pose = _pose()
    session = _session(pose.pose_digest_sha256)
    record = TargetClassVerificationRecord(
        target_class="center_high_z",
        fixture_load_name=session.fixture_identity.load_name,
        fixture_params_sha256=session.fixture_identity.params_sha256,
        labware_definition_sha256=session.fixture_identity.labware_definition_sha256,
        robot_serial=session.robot_serial or "",
        robot_server_version=session.robot_server_version or "",
        slot=session.slot,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        tiprack_load_name="opentrons_96_tiprack_300ul",
        offset_registry_record="not-yet-registered",
        result=TargetClassResult.BLOCKED,
    )

    authority = target_class_authority(record, session=session, fixture_pose=pose)

    assert authority.passed is False
    assert "target record pose digest is missing" in authority.blockers
    assert "expected_pose_digest_sha256" in authority.missing_claims


def test_target_authority_requires_pose_object_when_session_is_pose_scoped() -> None:
    pose = _pose()
    session = _session(pose.pose_digest_sha256)
    record = scaffold_target_class_record(
        session,
        "center_high_z",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
    )

    authority = target_class_authority(record, session=session)

    assert authority.passed is False
    assert "fixture_pose" in authority.missing_claims


def test_safety_profile_checksum_changes_by_pose_digest(tmp_path) -> None:
    identity = current_fixture_identity()
    canonical_pose = _pose(slot="5", orientation=FixtureOrientation.CANONICAL)
    rot180_pose = _pose(slot="5", orientation=FixtureOrientation.ROT180)
    nominal = identity.nominal_dimensions_mm
    canonical_qc = scaffold_fixture_qc_record(
        identity,
        pose_digest_sha256=canonical_pose.pose_digest_sha256,
        x_bound_mm=nominal["x"],
        y_bound_mm=nominal["y"],
        z_bound_mm=nominal["z"],
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )
    rot180_qc = canonical_qc.model_copy(
        update={"pose_digest_sha256": rot180_pose.pose_digest_sha256}
    )

    canonical_session = _bind_session_evidence(
        _session(canonical_pose.pose_digest_sha256),
        tmp_path,
    )
    rot180_session = _bind_session_evidence(
        _session(rot180_pose.pose_digest_sha256),
        tmp_path,
    )
    canonical = build_fixture_safety_profile(
        identity,
        session=canonical_session,
        fixture_qc_record=canonical_qc,
        fixture_pose=canonical_pose,
        pose_claims=_pose_claims(
            tmp_path,
            canonical_pose.pose_digest_sha256,
            pose=canonical_pose,
        ),
    )
    rot180 = build_fixture_safety_profile(
        identity,
        session=rot180_session,
        fixture_qc_record=rot180_qc,
        fixture_pose=rot180_pose,
        pose_claims=_pose_claims(
            tmp_path,
            rot180_pose.pose_digest_sha256,
            pose=rot180_pose,
        ),
    )

    assert canonical.profile is not None
    assert rot180.profile is not None
    assert canonical.profile.pose_digest_sha256 == canonical_pose.pose_digest_sha256
    assert rot180.profile.pose_digest_sha256 == rot180_pose.pose_digest_sha256
    assert canonical.profile.safety_profile_sha256 != rot180.profile.safety_profile_sha256


def test_safety_profile_requires_pose_claims_when_pose_is_supplied() -> None:
    pose = _pose()
    identity = current_fixture_identity()
    nominal = identity.nominal_dimensions_mm
    qc = scaffold_fixture_qc_record(
        identity,
        pose_digest_sha256=pose.pose_digest_sha256,
        x_bound_mm=nominal["x"],
        y_bound_mm=nominal["y"],
        z_bound_mm=nominal["z"],
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )

    result = build_fixture_safety_profile(
        identity,
        fixture_qc_record=qc,
        fixture_pose=pose,
    )

    assert result.passed is False
    assert any("fixture_pose_orientation" in claim for claim in result.missing_claims)
    assert POSE_UPRIGHT_CLAIM in result.missing_claims


def test_safety_profile_requires_session_for_session_scoped_pose_claims(tmp_path) -> None:
    pose = _pose()
    session = _bind_session_evidence(_session(pose.pose_digest_sha256), tmp_path)
    identity = current_fixture_identity()
    nominal = identity.nominal_dimensions_mm
    qc = scaffold_fixture_qc_record(
        identity,
        pose_digest_sha256=pose.pose_digest_sha256,
        x_bound_mm=nominal["x"],
        y_bound_mm=nominal["y"],
        z_bound_mm=nominal["z"],
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )

    result = build_fixture_safety_profile(
        identity,
        fixture_qc_record=qc,
        fixture_pose=pose,
        pose_claims=_pose_claims(tmp_path, pose.pose_digest_sha256),
    )
    scoped = build_fixture_safety_profile(
        identity,
        session=session,
        fixture_qc_record=qc,
        fixture_pose=pose,
        pose_claims=_pose_claims(tmp_path, pose.pose_digest_sha256),
    )

    assert result.passed is False
    assert "bridge session is required" in " ".join(result.blockers)
    assert scoped.passed is True


def test_safety_profile_requires_pose_object_for_pose_scoped_qc_record() -> None:
    pose = _pose()
    identity = current_fixture_identity()
    nominal = identity.nominal_dimensions_mm
    qc = scaffold_fixture_qc_record(
        identity,
        pose_digest_sha256=pose.pose_digest_sha256,
        x_bound_mm=nominal["x"],
        y_bound_mm=nominal["y"],
        z_bound_mm=nominal["z"],
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )

    result = build_fixture_safety_profile(identity, fixture_qc_record=qc)

    assert result.passed is False
    assert result.profile is None
    assert "fixture_pose" in result.missing_claims


def test_home_clearance_requires_pose_object_when_session_is_pose_scoped() -> None:
    pose = _pose()
    session = _session(pose.pose_digest_sha256)

    gate = home_clearance_gate(
        session=session,
        safety_profile=None,
        recovery_disposition="recovered_closed",
    )

    assert gate.passed is False
    assert "fixture_pose" in gate.missing_claims


def test_offset_authority_blocks_cross_pose_scope_when_pose_is_supplied(tmp_path) -> None:
    pose = _pose()
    other_pose = _pose(slot="1", orientation=FixtureOrientation.ROT180)
    session = _bind_session_evidence(_session(pose.pose_digest_sha256), tmp_path)
    identity = session.fixture_identity
    nominal = identity.nominal_dimensions_mm
    qc = scaffold_fixture_qc_record(
        identity,
        pose_digest_sha256=pose.pose_digest_sha256,
        x_bound_mm=nominal["x"],
        y_bound_mm=nominal["y"],
        z_bound_mm=nominal["z"],
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )
    profile_result = build_fixture_safety_profile(
        identity,
        session=session,
        fixture_qc_record=qc,
        fixture_pose=pose,
        pose_claims=_pose_claims(tmp_path, pose.pose_digest_sha256),
    )
    assert profile_result.profile is not None
    target_record = scaffold_target_class_record(
        session,
        "offset_x_1p5_low_z_dry",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        offset_registry_record="offset-1",
    )
    target_record.claims = _pose_claims(tmp_path, pose.pose_digest_sha256)
    offset = OffsetRecord(
        offset_record_id="offset-1",
        authority_state=OffsetAuthorityState.PROMOTED,
        robot_serial=session.robot_serial or "",
        robot_server_version=session.robot_server_version,
        opentrons_api_version=session.max_protocol_api_version,
        fixture_load_name=identity.load_name,
        fixture_definition_uri=session.definition_uri or "",
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        pose_digest_sha256=other_pose.pose_digest_sha256,
        slot=session.slot,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        tiprack_load_name="opentrons_96_tiprack_300ul",
        offset_mm={"x": 1.5, "y": 0.0, "z": 0.0},
        verification_targets=["offset_x_1p5_low_z_dry"],
        evidence_file="data/measurements/offsets/offset-1.json",
        safety_profile_sha256=profile_result.profile.safety_profile_sha256,
        target_policy_digest_sha256=profile_result.profile.target_policy_digest_sha256,
    )

    gate = offset_match_gate(
        registry=OffsetRegistry(records=[offset]),
        session=session,
        target_record=target_record,
        safety_profile=profile_result.profile,
        fixture_pose=pose,
    )

    assert gate.passed is False
    assert "offset pose digest does not match session" in gate.blockers
    assert "offset pose digest does not match safety profile" in gate.blockers


def test_offset_authority_requires_pose_object_when_session_is_pose_scoped() -> None:
    pose = _pose()
    session = _session(pose.pose_digest_sha256)
    target_record = scaffold_target_class_record(
        session,
        "offset_x_1p5_low_z_dry",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        offset_registry_record="not-yet-registered",
    )

    gate = offset_match_gate(
        registry=OffsetRegistry(),
        session=session,
        target_record=target_record,
        safety_profile=None,
    )

    assert gate.passed is False
    assert "fixture_pose" in gate.missing_claims
