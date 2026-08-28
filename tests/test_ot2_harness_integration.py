from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from datetime import datetime, timedelta
from importlib import resources
from pathlib import Path

import pytest
from ot2_harness.core.artifacts import capture_fixture, captured_labware_definition
from ot2_harness.core.evidence import append_evidence_event
from ot2_harness.core.models import (
    BridgeSession,
    CameraCaptureResult,
    EvidenceClaim,
    EvidenceEvent,
    EvidenceHandle,
    EvidenceQuality,
    EvidenceSourceKind,
)
from ot2_harness.core.plans import PlanFragment, PlanStep
from ot2_harness.core.pose import FixtureOrientation, fixture_pose_from_labware_definition
from ot2_harness.core.pose_evidence import (
    build_fixture_pose_evidence_artifact,
    derive_fixture_pose_claims,
    fixture_pose_evidence_packets_from_artifact,
    write_fixture_pose_evidence_artifact,
)
from ot2_harness.core.readiness import ReadinessResult
from ot2_harness.core.records import (
    TARGET_CLASS_EVIDENCE_METHOD,
    TargetClassResult,
    scaffold_fixture_qc_record,
    scaffold_target_class_record,
    target_class_verified_claim_id,
    target_class_verified_claim_type,
)
from ot2_harness.core.recovery import NoMotionRecoveryDisposition
from ot2_harness.core.safety import build_fixture_safety_profile
from ot2_harness.core.validation import validate_plan_fragment

from aevum_cad.params import DEFAULT_PARAMS
from aevum_ot2_profile import (
    build_fixture_manifest,
    build_target_policy_bundle,
    build_workspace_paths,
    capture_aevum_profile_snapshot,
)

EXPECTED_LABWARE = "aevum_p300_poc_fixture.json"


def _output_dir(tmp_path: Path, name: str = "generated") -> Path:
    output = tmp_path / name
    output.mkdir()
    return output


def _params_copy(tmp_path: Path, *, load_name: str | None = None) -> Path:
    params = json.loads(DEFAULT_PARAMS.read_bytes())
    if load_name is not None:
        params["labware"]["load_name"] = load_name
    path = tmp_path / f"params-{len(list(tmp_path.glob('params-*')))}.json"
    path.write_text(json.dumps(params) + "\n")
    return path


def _write_active_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    bundle,
) -> Path:
    path = tmp_path / "target-policy-bundle.json"
    path.write_text(bundle.model_dump_json(indent=2) + "\n")
    monkeypatch.setenv("OT2_HARNESS_TARGET_POLICY_BUNDLE", str(path))
    return path


def _build_local_wheel(source: Path, wheel_dir: Path) -> Path:
    before = set(wheel_dir.glob("*.whl"))
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(wheel_dir), str(source)],
        cwd=wheel_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    created = set(wheel_dir.glob("*.whl")) - before
    assert len(created) == 1
    return created.pop()


def _venv_python(tmp_path: Path) -> Path:
    venv = tmp_path / "wheel-smoke-venv"
    subprocess.run(
        ["uv", "venv", "--python", "3.11", "--seed", str(venv)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return venv / "bin/python"


def _install_wheels_into_venv(python: Path, artifacts: list[Path]) -> None:
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), *(str(path) for path in artifacts)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_default_manifest_captures_packaged_params_and_publishes_once(tmp_path: Path) -> None:
    output = _output_dir(tmp_path)
    manifest = build_fixture_manifest(output)
    snapshot = capture_fixture(manifest=manifest)
    identity = snapshot.identity
    packaged = resources.files("aevum_ot2_profile").joinpath(
        "p300_poc_fixture.params.json"
    )

    assert manifest.schema_version == 1
    assert manifest.design_artifact_path == Path(packaged)
    assert manifest.design_artifact_path.read_bytes() == DEFAULT_PARAMS.read_bytes()
    assert manifest.design_artifact_sha256 == hashlib.sha256(
        manifest.design_artifact_path.read_bytes()
    ).hexdigest()
    assert manifest.labware_sha256 == hashlib.sha256(manifest.labware_path.read_bytes()).hexdigest()
    assert identity.namespace == "aevum"
    assert identity.load_name == "aevum_p300_poc_fixture"
    assert identity.version == 1
    assert identity.nominal_dimensions_mm == {"x": 127.76, "y": 85.48, "z": 91.0}
    assert identity.labware_dimensions_mm == identity.nominal_dimensions_mm
    assert identity.dimensions_match is True
    entries = list(output.iterdir())
    assert entries == [output / EXPECTED_LABWARE]
    assert stat.S_ISREG(entries[0].lstat().st_mode)


def test_manifest_and_policy_bundle_share_one_snapshot_despite_path_replacement(
    tmp_path: Path,
) -> None:
    params_path = _params_copy(tmp_path)
    snapshot = capture_aevum_profile_snapshot(params_path)
    replacement_params = json.loads(params_path.read_bytes())
    replacement_params["base"]["length_x"] = 999.0
    params_path.write_text(json.dumps(replacement_params) + "\n")

    manifest = build_fixture_manifest(_output_dir(tmp_path), snapshot=snapshot)
    bundle = build_target_policy_bundle(snapshot=snapshot)

    assert manifest.design_artifact_sha256 == snapshot.params_sha256
    assert manifest.labware_sha256 == snapshot.labware_definition_sha256
    assert manifest.design_artifact_sha256 == bundle.fixture_params_sha256
    assert manifest.labware_sha256 == bundle.labware_definition_sha256
    assert bundle.consumer_source_sha256 == snapshot.params_sha256


def test_profile_snapshot_is_deeply_immutable() -> None:
    snapshot = capture_aevum_profile_snapshot()
    before = build_target_policy_bundle(snapshot=snapshot)

    with pytest.raises(TypeError):
        snapshot.params["pipette_offsets"] = ()  # type: ignore[index]
    with pytest.raises(TypeError):
        snapshot.params["base"]["length_x"] = 999.0  # type: ignore[index]
    with pytest.raises(TypeError):
        snapshot.params["pipette_offsets"][0]["x"] = 999.0  # type: ignore[index]
    with pytest.raises(AttributeError):
        snapshot.params["pipette_offsets"].append({"name": "forged", "x": 999.0})
    with pytest.raises(TypeError):
        snapshot.labware_definition["dimensions"]["xDimension"] = 999.0  # type: ignore[index]

    assert build_target_policy_bundle(snapshot=snapshot) == before


def test_dimension_validation_fails_before_any_publish(tmp_path: Path) -> None:
    params_path = _params_copy(tmp_path)
    params = json.loads(params_path.read_bytes())
    params["base"]["length_x"] = -1.0
    params_path.write_text(json.dumps(params) + "\n")
    output = _output_dir(tmp_path)

    with pytest.raises(ValueError, match="nominal x dimension"):
        build_fixture_manifest(output, params_path=params_path)

    assert list(output.iterdir()) == []


@pytest.mark.parametrize("source", ["params", "labware"])
def test_manifest_fails_closed_when_captured_source_changes(
    tmp_path: Path,
    source: str,
) -> None:
    params_path = _params_copy(tmp_path)
    manifest = build_fixture_manifest(_output_dir(tmp_path), params_path=params_path)
    if source == "params":
        params = json.loads(params_path.read_bytes())
        params["base"]["length_x"] = 127.77
        params_path.write_text(json.dumps(params) + "\n")
    else:
        manifest.labware_path.write_bytes(manifest.labware_path.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="checksum mismatch"):
        capture_fixture(manifest=manifest)


@pytest.mark.parametrize(
    "load_name",
    [
        "../outside",
        "..",
        ".",
        "/absolute",
        "C:\\absolute",
        "nested/name",
        "nested\\name",
        " leading",
        "trailing ",
        "trailing.",
        "CON",
        "",
    ],
)
def test_load_name_attacks_fail_before_any_write(tmp_path: Path, load_name: str) -> None:
    sentinel = tmp_path / "outside.json"
    sentinel.write_bytes(b"outside-sentinel")
    output = _output_dir(tmp_path)
    params_path = _params_copy(tmp_path, load_name=load_name)

    with pytest.raises(ValueError, match="portable filename segment"):
        build_fixture_manifest(output, params_path=params_path)

    assert sentinel.read_bytes() == b"outside-sentinel"
    assert list(output.iterdir()) == []


def test_output_root_symlink_is_rejected_without_touching_target(tmp_path: Path) -> None:
    physical = _output_dir(tmp_path, "physical")
    sentinel = physical / "sentinel"
    sentinel.write_bytes(b"unchanged")
    linked = tmp_path / "linked"
    linked.symlink_to(physical, target_is_directory=True)

    with pytest.raises(ValueError, match="not a symlink"):
        build_fixture_manifest(linked)

    assert sentinel.read_bytes() == b"unchanged"
    assert list(physical.iterdir()) == [sentinel]


@pytest.mark.parametrize("collision_kind", ["symlink", "regular"])
def test_existing_destination_is_never_clobbered(
    tmp_path: Path,
    collision_kind: str,
) -> None:
    output = _output_dir(tmp_path)
    outside = tmp_path / "outside-sentinel"
    outside.write_bytes(b"outside")
    destination = output / EXPECTED_LABWARE
    if collision_kind == "symlink":
        destination.symlink_to(outside)
    else:
        destination.write_bytes(b"pre-existing")

    with pytest.raises(FileExistsError, match="existing destination"):
        build_fixture_manifest(output)

    assert outside.read_bytes() == b"outside"
    if collision_kind == "symlink":
        assert destination.is_symlink()
    else:
        assert destination.read_bytes() == b"pre-existing"
    assert sorted(path.name for path in output.iterdir()) == [EXPECTED_LABWARE]


def test_competing_publisher_wins_without_being_clobbered(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = _output_dir(tmp_path)
    outside = tmp_path / "outside-sentinel"
    outside.write_bytes(b"outside")
    destination = output / EXPECTED_LABWARE
    real_link = os.link

    def competing_link(*args: object, **kwargs: object) -> None:
        destination.write_bytes(b"competing-publisher")
        real_link(*args, **kwargs)

    monkeypatch.setattr("aevum_ot2_profile.fixture.os.link", competing_link)
    with pytest.raises(FileExistsError, match="competing destination"):
        build_fixture_manifest(output)

    assert destination.read_bytes() == b"competing-publisher"
    assert outside.read_bytes() == b"outside"
    assert sorted(path.name for path in output.iterdir()) == [EXPECTED_LABWARE]


def test_parameter_path_replacement_during_snapshot_fails_before_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    params_path = _params_copy(tmp_path)
    replacement = _params_copy(tmp_path)
    replacement_params = json.loads(replacement.read_bytes())
    replacement_params["base"]["length_x"] = 999.0
    replacement.write_text(json.dumps(replacement_params) + "\n")
    output = _output_dir(tmp_path)
    outside = tmp_path / "outside-sentinel"
    outside.write_bytes(b"outside")
    real_read = os.read
    replaced = False

    def replacing_read(fd: int, size: int) -> bytes:
        nonlocal replaced
        chunk = real_read(fd, size)
        if chunk and not replaced:
            os.replace(replacement, params_path)
            replaced = True
        return chunk

    monkeypatch.setattr("aevum_ot2_profile._params.os.read", replacing_read)
    with pytest.raises(ValueError, match="changed while it was being captured"):
        build_fixture_manifest(output, params_path=params_path)

    assert outside.read_bytes() == b"outside"
    assert list(output.iterdir()) == []


def test_workspace_mapping_is_explicit_complete_and_side_effect_free(tmp_path: Path) -> None:
    workspace = tmp_path / "not-created"
    paths = build_workspace_paths(workspace)
    measurements = workspace / "data" / "measurements"
    expected = {
        "workspace": workspace,
        "state_db": measurements / "ot2_bridge_state.sqlite3",
        "evidence_index": measurements / "ot2_evidence_index.json",
        "evidence_transactions": measurements / "evidence_transactions",
        "sessions": measurements / "sessions",
        "poses": measurements / "sessions",
        "offset_registry": measurements / "ot2_offset_registry.json",
        "images": measurements / "images",
        "target_scaffolds": measurements / "target_classes",
        "fixture_qc": measurements / "fixture_qc.json",
        "safety_profiles": measurements / "safety_profiles",
        "legacy_evidence": measurements / "legacy_image_evidence",
    }

    assert paths.model_dump() == expected
    assert workspace.exists() is False
    with pytest.raises(TypeError):
        build_workspace_paths()  # type: ignore[call-arg]
    assert workspace.exists() is False


def _pose_scoped_safety_inputs(tmp_path: Path):
    profile = capture_aevum_profile_snapshot()
    manifest = build_fixture_manifest(_output_dir(tmp_path), snapshot=profile)
    snapshot = capture_fixture(manifest=manifest)
    session_id = "safety-session"
    sessions_root = tmp_path / "workspace" / "sessions"
    captured = snapshot.persist_labware(root=sessions_root, session_id=session_id)
    definition = captured_labware_definition(
        captured,
        expected_sha256=snapshot.identity.labware_definition_sha256,
        expected_session_id=session_id,
        trusted_sessions_root=sessions_root,
        original_source_path=manifest.labware_path,
    )
    pose = fixture_pose_from_labware_definition(
        snapshot.identity,
        slot="1",
        orientation=FixtureOrientation.CANONICAL,
        canonical_labware_definition=definition,
    )
    now = datetime.now() - timedelta(seconds=2)
    evidence_index = tmp_path / "workspace" / "evidence" / "index.json"
    session = BridgeSession(
        session_id=session_id,
        kind="registration",
        owner_id="aevum-integration",
        robot_url="http://ot2.local:31950",
        robot_serial="OT2TEST0001",
        robot_server_version="9.0.0",
        state="ready_no_motion",
        created_at=now,
        updated_at=now,
        lease_expires_at=now + timedelta(minutes=10),
        slot="1",
        fixture_identity=snapshot.identity,
        fixture_orientation=pose.orientation.value,
        fixture_pose_digest_sha256=pose.pose_digest_sha256,
        fixture_pose_path=str(sessions_root / session_id / "fixture_pose.json"),
        captured_labware=captured,
        evidence_index_path=str(evidence_index),
    )
    image = tmp_path / "fixture.jpg"
    image.write_bytes(b"fixture-image")
    camera = CameraCaptureResult(
        robot_url=session.robot_url,
        captured_at=datetime.now(),
        endpoint="/camera/picture",
        image_path=str(image),
        image_checksum_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
        content_type="image/jpeg",
        bytes_written=image.stat().st_size,
    )
    append_evidence_event(
        EvidenceEvent(
            event_type="ot2_camera_picture",
            session_id=session_id,
            summary="captured fixture pose",
            payload=camera.model_dump(mode="json"),
        ),
        path=evidence_index,
    )
    artifact = build_fixture_pose_evidence_artifact(
        pose,
        session=session,
        artifact_id="aevum-fixture-pose",
        image_path=image,
        observed_orientation=pose.orientation,
        fixture_upright=True,
        inspection_note="fixture seated and fiducials visible",
        camera_capture=camera,
        quality=EvidenceQuality.USABLE,
    )
    artifact_path = write_fixture_pose_evidence_artifact(
        artifact,
        tmp_path / "fixture-pose-evidence.json",
    )
    packets = fixture_pose_evidence_packets_from_artifact(
        pose,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )
    claims = derive_fixture_pose_claims(pose, packets, session=session)
    nominal = snapshot.identity.nominal_dimensions_mm
    qc = scaffold_fixture_qc_record(
        snapshot.identity,
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
    return snapshot, session, sessions_root, pose, claims, qc, profile


def _authoritative_target_record(
    tmp_path: Path,
    *,
    session: BridgeSession,
    pose,
    pose_claims: list[EvidenceClaim],
    target_class: str,
    result: TargetClassResult = TargetClassResult.PASSED,
    include_claim: bool = True,
):
    record = scaffold_target_class_record(
        session,
        target_class,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
    )
    evidence_path = tmp_path / f"{target_class}-evidence.json"
    evidence_path.write_text(json.dumps({"target_class": target_class}) + "\n")
    handle = EvidenceHandle(
        evidence_id=f"{target_class}-evidence",
        source_kind=EvidenceSourceKind.PHYSICAL_MEASUREMENT,
        path=str(evidence_path),
        checksum_sha256=hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        created_at=datetime.now(),
        session_id=session.session_id,
        quality=EvidenceQuality.USABLE,
    )
    claims = list(pose_claims)
    if include_claim:
        claims.append(
            EvidenceClaim(
                claim_id=target_class_verified_claim_id(target_class, handle.evidence_id),
                claim_type=target_class_verified_claim_type(target_class),
                value=True,
                session_id=session.session_id,
                fixture_load_name=session.fixture_identity.load_name,
                fixture_params_sha256=session.fixture_identity.params_sha256,
                labware_definition_sha256=(
                    session.fixture_identity.labware_definition_sha256
                ),
                pose_digest_sha256=pose.pose_digest_sha256,
                method=TARGET_CLASS_EVIDENCE_METHOD,
                quality=EvidenceQuality.USABLE,
                evidence=[handle],
            )
        )
    return record.model_copy(
        update={
            "result": result,
            "evidence": [handle],
            "claims": claims,
        }
    )


def test_pose_claims_qc_and_bundle_bind_positive_safety_profile(tmp_path: Path) -> None:
    snapshot, session, sessions_root, pose, claims, qc, profile = (
        _pose_scoped_safety_inputs(tmp_path)
    )
    bundle = build_target_policy_bundle(snapshot=profile)

    result = build_fixture_safety_profile(
        snapshot.identity,
        session=session,
        fixture_qc_record=qc,
        fixture_pose=pose,
        pose_claims=claims,
        policy_bundle=bundle,
        trusted_sessions_root=sessions_root,
    )

    assert result.passed is True
    assert result.profile is not None
    assert result.profile.session_id == session.session_id
    assert result.profile.pose_digest_sha256 == pose.pose_digest_sha256
    assert qc.pose_digest_sha256 == pose.pose_digest_sha256
    assert all(claim.session_id == session.session_id for claim in claims)
    assert all(claim.pose_digest_sha256 == pose.pose_digest_sha256 for claim in claims)
    assert result.profile.source_claim_ids
    assert result.profile.target_policy_bundle == bundle
    assert result.profile.target_policy_source_sha256 == snapshot.identity.params_sha256
    assert result.profile.target_policy_digest_sha256 == bundle.policy_digest_sha256
    assert result.profile.boundary_handling.default_allowed is False
    assert result.profile.boundary_handling.requires_inner_target_margin is True
    boundary = [policy for policy in bundle.policies if policy.boundary]
    assert boundary
    assert all(not policy.first_pass_allowed for policy in boundary)
    assert all(policy.required_predecessors for policy in boundary)


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("missing_bundle", "target policy bundle is invalid"),
        ("loose_policies", "loose target policy overrides"),
        ("source_checksum", "consumer source checksum"),
        ("fixture_checksum", "policy fixture design checksum mismatch"),
        ("policy_digest", "policy digest mismatch"),
        ("unknown_geometry", "unknown geometry"),
        ("duplicate_target", "duplicate target policy"),
    ],
)
def test_policy_bundle_contract_rejects_forgery_and_legacy_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    expected: str,
) -> None:
    snapshot, session, sessions_root, pose, claims, qc, profile = (
        _pose_scoped_safety_inputs(tmp_path)
    )
    bundle = build_target_policy_bundle(snapshot=profile)
    kwargs = {"policy_bundle": bundle}
    monkeypatch.delenv("OT2_HARNESS_TARGET_POLICY_BUNDLE", raising=False)
    if case == "missing_bundle":
        kwargs = {}
    elif case == "loose_policies":
        kwargs = {"policies": list(bundle.policies), "policy_bundle": bundle}
    elif case == "source_checksum":
        kwargs["policy_bundle"] = bundle.model_copy(
            update={"consumer_source_sha256": "0" * 64}
        )
    elif case == "fixture_checksum":
        kwargs["policy_bundle"] = bundle.model_copy(
            update={"fixture_params_sha256": "0" * 64}
        )
    elif case == "policy_digest":
        kwargs["policy_bundle"] = bundle.model_copy(
            update={"policy_digest_sha256": "0" * 64}
        )
    elif case == "unknown_geometry":
        policies = list(bundle.policies)
        policies[0] = policies[0].model_copy(update={"geometry_id": "unknown"})
        kwargs["policy_bundle"] = bundle.model_copy(update={"policies": tuple(policies)})
    elif case == "duplicate_target":
        kwargs["policy_bundle"] = bundle.model_copy(
            update={"policies": (*bundle.policies, bundle.policies[0])}
        )

    result = build_fixture_safety_profile(
        snapshot.identity,
        session=session,
        fixture_qc_record=qc,
        fixture_pose=pose,
        pose_claims=claims,
        trusted_sessions_root=sessions_root,
        **kwargs,
    )

    assert result.passed is False
    assert expected in " ".join(result.blockers)


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("absent_pose", "fixture_pose"),
        ("absent_claims", "fixture_pose_orientation"),
        ("mismatched_digest", "pose digest"),
        ("mismatched_fixture", "fixture params checksum"),
        ("stale_claims", "predates active session authority"),
        ("wrong_session", "session"),
    ],
)
def test_pose_scoped_safety_rejects_missing_or_cross_scoped_authority(
    tmp_path: Path,
    case: str,
    expected: str,
) -> None:
    snapshot, session, sessions_root, pose, claims, qc, profile = (
        _pose_scoped_safety_inputs(tmp_path)
    )
    identity = snapshot.identity
    active_pose = pose
    active_claims = claims
    active_qc = qc
    if case == "absent_pose":
        active_pose = None
    elif case == "absent_claims":
        active_claims = []
    elif case == "mismatched_digest":
        active_qc = qc.model_copy(update={"pose_digest_sha256": "f" * 64})
    elif case == "mismatched_fixture":
        identity = identity.model_copy(update={"params_sha256": "e" * 64})
    elif case == "stale_claims":
        stale = session.updated_at - timedelta(seconds=1)
        active_claims = [
            claim.model_copy(
                update={
                    "created_at": stale,
                    "evidence": [
                        handle.model_copy(update={"created_at": stale})
                        for handle in claim.evidence
                    ],
                }
            )
            for claim in claims
        ]
    elif case == "wrong_session":
        active_claims = [
            claim.model_copy(update={"session_id": "other-session"}) for claim in claims
        ]

    result = build_fixture_safety_profile(
        identity,
        session=session,
        fixture_qc_record=active_qc,
        fixture_pose=active_pose,
        pose_claims=active_claims,
        policy_bundle=build_target_policy_bundle(snapshot=profile),
        trusted_sessions_root=sessions_root,
    )

    assert result.passed is False
    assert result.profile is None
    assert expected in " ".join([*result.blockers, *result.missing_claims])


def test_boundary_high_z_is_not_a_first_pass_and_requires_inner_predecessor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot, session, sessions_root, pose, claims, qc, profile = (
        _pose_scoped_safety_inputs(tmp_path)
    )
    bundle = build_target_policy_bundle(snapshot=profile)
    _write_active_bundle(tmp_path, monkeypatch, bundle)
    safety = build_fixture_safety_profile(
        snapshot.identity,
        session=session,
        fixture_qc_record=qc,
        fixture_pose=pose,
        pose_claims=claims,
        policy_bundle=bundle,
        trusted_sessions_root=sessions_root,
    ).profile
    assert safety is not None
    boundary_record = scaffold_target_class_record(
        session,
        "offset_x_2p0_high_z",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
    )
    result = validate_plan_fragment(
        PlanFragment(
            session_id=session.session_id,
            steps=[
                PlanStep(
                    step_id="boundary-first-pass",
                    operation="move_high_z",
                    target_class="offset_x_2p0_high_z",
                )
            ],
        ),
        session,
        readiness=ReadinessResult(
            session_id=session.session_id,
            registration_ready=True,
        ),
        target_records=[boundary_record],
        safety_profile=safety,
        fixture_pose=pose,
        pose_claims=claims,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
        daemon_motion_enabled=True,
        trusted_sessions_root=sessions_root,
    )

    reasons = " ".join(result.reasons)
    assert result.allowed is False
    assert "target_record:offset_x_1p5_low_z_dry" in reasons
    assert safety.boundary_handling.requires_inner_target_margin is True


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("present_failed", "passed_target:offset_x_1p5_low_z_dry"),
        ("claimless", "target_class_verified:offset_x_1p5_low_z_dry"),
        ("stale", "predates active session authority"),
        ("wrong_session", "session does not match"),
        ("wrong_scope", "fixture params checksum"),
    ],
)
def test_boundary_predecessor_authority_rejects_distinct_invalid_states(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    expected: str,
) -> None:
    snapshot, session, sessions_root, pose, claims, qc, profile = (
        _pose_scoped_safety_inputs(tmp_path)
    )
    bundle = build_target_policy_bundle(snapshot=profile)
    _write_active_bundle(tmp_path, monkeypatch, bundle)
    safety = build_fixture_safety_profile(
        snapshot.identity,
        session=session,
        fixture_qc_record=qc,
        fixture_pose=pose,
        pose_claims=claims,
        policy_bundle=bundle,
        trusted_sessions_root=sessions_root,
    ).profile
    assert safety is not None
    predecessor = _authoritative_target_record(
        tmp_path,
        session=session,
        pose=pose,
        pose_claims=claims,
        target_class="offset_x_1p5_low_z_dry",
    )
    if case == "present_failed":
        predecessor = predecessor.model_copy(update={"result": TargetClassResult.FAILED})
    elif case == "claimless":
        predecessor = _authoritative_target_record(
            tmp_path,
            session=session,
            pose=pose,
            pose_claims=claims,
            target_class="offset_x_1p5_low_z_dry",
            include_claim=False,
        )
    elif case == "stale":
        stale = session.updated_at - timedelta(seconds=1)
        predecessor = predecessor.model_copy(
            update={
                "claims": [
                    claim.model_copy(
                        update={
                            "created_at": stale,
                            "evidence": [
                                handle.model_copy(update={"created_at": stale})
                                for handle in claim.evidence
                            ],
                        }
                    )
                    for claim in predecessor.claims
                ]
            }
        )
    elif case == "wrong_session":
        predecessor = predecessor.model_copy(
            update={
                "claims": [
                    claim.model_copy(update={"session_id": "other-session"})
                    for claim in predecessor.claims
                ],
                "evidence": [
                    handle.model_copy(update={"session_id": "other-session"})
                    for handle in predecessor.evidence
                ],
            }
        )
    elif case == "wrong_scope":
        predecessor = predecessor.model_copy(update={"fixture_params_sha256": "e" * 64})

    boundary_record = scaffold_target_class_record(
        session,
        "offset_x_2p0_high_z",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
    )
    result = validate_plan_fragment(
        PlanFragment(
            session_id=session.session_id,
            steps=[
                PlanStep(
                    step_id=f"boundary-{case}",
                    operation="move_high_z",
                    target_class="offset_x_2p0_high_z",
                )
            ],
        ),
        session,
        readiness=ReadinessResult(
            session_id=session.session_id,
            registration_ready=True,
        ),
        target_records=[boundary_record, predecessor],
        safety_profile=safety,
        fixture_pose=pose,
        pose_claims=claims,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
        daemon_motion_enabled=True,
        trusted_sessions_root=sessions_root,
    )

    assert result.allowed is False
    assert expected in " ".join(result.reasons)


def test_isolated_installed_aevum_wheel_resolves_pinned_harness(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parents[1]
    harness_repository = repository.parent / "ot2-harness"
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    aevum_wheel = _build_local_wheel(repository, wheels)
    python = _venv_python(tmp_path)
    _install_wheels_into_venv(python, [aevum_wheel])
    smoke = tmp_path / "smoke"
    smoke.mkdir()
    script = """
import json
import os
import sys
from importlib.metadata import distribution
from pathlib import Path

roots = [Path(os.environ[name]).resolve() for name in ('A1_REPOSITORY', 'A1_HARNESS')]
blocked = {path for root in roots for path in (root, root / 'src')}
assert all(Path(entry or '.').resolve() not in blocked for entry in sys.path)

from importlib import resources
import aevum_ot2_profile
import ot2_harness
from ot2_harness.core.artifacts import capture_fixture
from aevum_ot2_profile import (
    build_fixture_manifest,
    build_target_policy_bundle,
    build_workspace_paths,
)

assert all(
    not Path(module.__file__).resolve().is_relative_to(root)
    for module in (aevum_ot2_profile, ot2_harness)
    for root in blocked
)
direct_url = json.loads(distribution('ot2-harness').read_text('direct_url.json'))
assert direct_url['vcs_info']['commit_id'] == os.environ['EXPECTED_OT2_HARNESS_COMMIT']
resource = resources.files('aevum_ot2_profile').joinpath('p300_poc_fixture.params.json')
assert resource.is_file()
output = Path('generated')
output.mkdir()
manifest = build_fixture_manifest(output)
assert capture_fixture(manifest=manifest).identity.load_name == 'aevum_p300_poc_fixture'
bundle = build_target_policy_bundle()
assert bundle.consumer_source_sha256 == bundle.fixture_params_sha256
paths = build_workspace_paths(Path('aevum-workspace'))
expected_state = Path('aevum-workspace').resolve() / 'data/measurements/ot2_bridge_state.sqlite3'
assert paths.state_db == expected_state
"""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["A1_REPOSITORY"] = str(repository)
    environment["A1_HARNESS"] = str(harness_repository)
    environment["EXPECTED_OT2_HARNESS_COMMIT"] = (
        "663cf647d2bae516f955e2daf51ae2b3ae8abb0f"
    )
    subprocess.run(
        [str(python), "-I", "-c", script],
        cwd=smoke,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
