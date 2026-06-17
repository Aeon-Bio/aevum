from __future__ import annotations

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.gates import (
    FIXTURE_DIMENSIONS_CLAIM,
    fixture_qc_claims_from_legacy_record,
)
from aevum_ot2.core.models import GateName
from aevum_ot2.core.records import FixtureQcRecord, scaffold_fixture_qc_record
from aevum_ot2.core.safety import (
    build_fixture_safety_profile,
    load_fixture_safety_profile,
    write_fixture_safety_profile,
)
from aevum_ot2.core.targets import TargetPolicy, target_policies


def _passing_fixture_qc_record() -> FixtureQcRecord:
    identity = current_fixture_identity()
    nominal = identity.nominal_dimensions_mm
    return scaffold_fixture_qc_record(
        identity,
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


def test_fixture_safety_profile_requires_measured_qc_not_labware_identity_alone() -> None:
    identity = current_fixture_identity()

    result = build_fixture_safety_profile(identity)

    assert result.passed is False
    assert result.profile is None
    assert FIXTURE_DIMENSIONS_CLAIM in result.missing_claims
    assert result.blocked_gates == [
        GateName.LOW_Z_DRY,
        GateName.WET,
        GateName.HOME_CLEARANCE,
    ]


def test_fixture_safety_profile_captures_bounds_and_boundary_policy() -> None:
    identity = current_fixture_identity()
    record = _passing_fixture_qc_record()

    result = build_fixture_safety_profile(identity, fixture_qc_record=record)

    assert result.passed is True
    assert result.profile is not None
    profile = result.profile
    assert profile.dimensions_source == "measured_fixture_qc"
    assert profile.measured_bounds_mm.x_mm == identity.nominal_dimensions_mm["x"]
    assert profile.conservative_bounds_mm.z_mm == identity.nominal_dimensions_mm["z"]
    assert profile.conservative_high_z_mm > profile.conservative_bounds_mm.z_mm
    assert profile.dry_z_floor_mm == profile.conservative_bounds_mm.z_mm
    assert profile.wet_z_floor_mm == profile.conservative_bounds_mm.z_mm
    assert profile.max_registration_jog_mm == 0.5
    assert profile.boundary_handling.default_allowed is False
    assert profile.boundary_handling.requires_inner_target_margin is True
    assert set(profile.boundary_handling.boundary_target_classes) == {
        "offset_x_2p0_high_z",
        "offset_x_2p0_low_z_dry",
        "offset_x_2p0_wet",
    }
    assert len(profile.safety_profile_sha256) == 64


def test_fixture_safety_profile_round_trips_schema_v1(tmp_path) -> None:
    identity = current_fixture_identity()
    result = build_fixture_safety_profile(
        identity,
        fixture_qc_record=_passing_fixture_qc_record(),
    )
    assert result.profile is not None
    path = tmp_path / "fixture_safety_profile.json"

    written = write_fixture_safety_profile(result.profile, path)
    loaded = load_fixture_safety_profile(written)

    assert loaded == result.profile
    assert loaded.safety_profile_sha256 == result.profile.safety_profile_sha256


def test_missing_measured_qc_blocks_low_z_wet_and_home_inputs() -> None:
    identity = current_fixture_identity()
    record = _passing_fixture_qc_record()
    record.measurements = [
        measurement for measurement in record.measurements if measurement.name != "z_bound"
    ]

    result = build_fixture_safety_profile(identity, fixture_qc_record=record)

    assert result.passed is False
    assert result.profile is None
    assert set(result.blocked_gates) == {
        GateName.LOW_Z_DRY,
        GateName.WET,
        GateName.HOME_CLEARANCE,
    }
    assert any("z_bound" in blocker for blocker in result.blockers)


def test_generated_labware_dimensions_cannot_override_failed_qc_claims() -> None:
    identity = current_fixture_identity()
    record = _passing_fixture_qc_record()
    claims = fixture_qc_claims_from_legacy_record(record)
    for claim in claims:
        if claim.claim_type == FIXTURE_DIMENSIONS_CLAIM:
            claim.value = False
            claim.reasons = ["measurement source rejected"]

    result = build_fixture_safety_profile(
        identity,
        fixture_qc_record=record,
        fixture_qc_claims=claims,
    )

    assert result.passed is False
    assert result.profile is None
    assert "measurement source rejected" in result.blockers


def test_cross_fixture_qc_claims_cannot_support_current_safety_profile() -> None:
    identity = current_fixture_identity()
    record = _passing_fixture_qc_record()
    claims = fixture_qc_claims_from_legacy_record(record)
    claims[0].fixture_params_sha256 = "0" * 64

    result = build_fixture_safety_profile(
        identity,
        fixture_qc_record=record,
        fixture_qc_claims=claims,
    )

    assert result.passed is False
    assert result.profile is None
    assert any("params checksum" in blocker for blocker in result.blockers)


def test_duplicate_fixture_qc_claim_types_fail_closed() -> None:
    identity = current_fixture_identity()
    record = _passing_fixture_qc_record()
    claims = fixture_qc_claims_from_legacy_record(record)
    claims.append(claims[0].model_copy(update={"claim_id": "duplicate"}))

    result = build_fixture_safety_profile(
        identity,
        fixture_qc_record=record,
        fixture_qc_claims=claims,
    )

    assert result.passed is False
    assert result.profile is None
    assert f"duplicate fixture QC claim type: {claims[0].claim_type}" in result.blockers


def test_safety_profile_fails_closed_on_invalid_parameter_overrides() -> None:
    identity = current_fixture_identity()
    record = _passing_fixture_qc_record()

    result = build_fixture_safety_profile(
        identity,
        fixture_qc_record=record,
        high_z_clearance_mm=0,
        max_registration_jog_mm=-1,
    )

    assert result.passed is False
    assert result.profile is None
    assert "high-Z clearance must be finite and positive" in result.blockers
    assert "max registration jog must be finite and positive" in result.blockers


def test_safety_profile_checksum_changes_when_measured_bounds_change() -> None:
    identity = current_fixture_identity()
    record = _passing_fixture_qc_record()
    changed_record = _passing_fixture_qc_record()
    for measurement in changed_record.measurements:
        if measurement.name == "x_bound":
            measurement.measured_mm = (measurement.measured_mm or 0) + 0.25

    original = build_fixture_safety_profile(identity, fixture_qc_record=record)
    changed = build_fixture_safety_profile(identity, fixture_qc_record=changed_record)

    assert original.profile is not None
    assert changed.profile is not None
    assert original.profile.safety_profile_sha256 != changed.profile.safety_profile_sha256


def test_safety_profile_checksum_changes_when_target_policy_inputs_change() -> None:
    identity = current_fixture_identity()
    record = _passing_fixture_qc_record()
    policies = target_policies()
    changed_policies: list[TargetPolicy] = [
        policy.model_copy(
            update={"boundary": False}
        )
        if policy.target_class == "offset_x_2p0_high_z"
        else policy
        for policy in policies
    ]

    original = build_fixture_safety_profile(
        identity,
        fixture_qc_record=record,
        policies=policies,
    )
    changed = build_fixture_safety_profile(
        identity,
        fixture_qc_record=record,
        policies=changed_policies,
    )

    assert original.profile is not None
    assert changed.profile is not None
    assert original.profile.target_policy_digest_sha256 != (
        changed.profile.target_policy_digest_sha256
    )
    assert original.profile.safety_profile_sha256 != changed.profile.safety_profile_sha256
