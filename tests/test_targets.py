from __future__ import annotations

from aevum_ot2.core.records import (
    TARGET_CLASS_BY_NAME,
    TARGET_CLASSES,
    target_class_names,
)
from aevum_ot2.core.targets import (
    TargetRequiredClaim,
    TargetZTier,
    matching_high_z_target,
    target_policies,
    target_policy_for,
    target_policy_names,
    validate_target_policy_table,
)


def test_target_policy_table_covers_every_declared_target_class() -> None:
    assert set(target_policy_names()) == set(target_class_names())
    assert validate_target_policy_table() == []


def test_target_policy_preserves_legacy_target_class_flags() -> None:
    for target_class in TARGET_CLASSES:
        policy = target_policy_for(target_class.name)

        assert policy.wet == target_class.wet
        assert policy.mat_patch == target_class.mat_patch
        assert policy.boundary == target_class.boundary
        assert set(target_class.requires) <= set(policy.required_predecessors)


def test_only_center_high_z_is_first_pass_eligible() -> None:
    first_pass_targets = [
        policy.target_class for policy in target_policies() if policy.first_pass_allowed
    ]

    assert first_pass_targets == ["center_high_z"]
    assert all(
        not policy.first_pass_allowed for policy in target_policies() if policy.boundary
    )


def test_low_z_targets_require_matching_high_z_predecessor_not_center_evidence() -> None:
    assert matching_high_z_target("offset_x_1p0_low_z_dry") == "offset_x_1p0_high_z"
    assert matching_high_z_target("offset_x_1p5_low_z_dry") == "offset_x_1p5_high_z"
    assert matching_high_z_target("offset_x_2p0_low_z_dry") == "offset_x_2p0_high_z"
    assert matching_high_z_target("center_low_z_dry") == "center_high_z"

    offset_low_z = target_policy_for("offset_x_1p5_low_z_dry")
    assert "center_high_z" not in offset_low_z.required_predecessors


def test_mat_patch_wet_requires_mat_patch_dry_and_no_mat_wet() -> None:
    policy = target_policy_for("mat_patch_offset_x_1p5_wet")

    assert policy.z_tier == TargetZTier.WET
    assert policy.mat_patch is True
    assert set(policy.required_predecessors) == {
        "mat_patch_offset_x_1p5_low_z_dry",
        "offset_x_1p5_wet",
    }


def test_boundary_targets_are_excluded_from_first_pass_and_marked_by_geometry() -> None:
    boundary_targets = [
        policy for policy in target_policies() if policy.geometry_id.endswith("_boundary")
    ]

    assert {policy.target_class for policy in boundary_targets} == {
        "offset_x_2p0_high_z",
        "offset_x_2p0_low_z_dry",
        "offset_x_2p0_wet",
    }
    assert all(policy.boundary for policy in boundary_targets)
    assert all(not policy.first_pass_allowed for policy in boundary_targets)


def test_low_z_and_wet_policies_require_future_offset_authority_claims() -> None:
    for policy in target_policies():
        if policy.z_tier in {TargetZTier.LOW_Z_DRY, TargetZTier.WET}:
            assert TargetRequiredClaim.PROMOTED_OFFSET_AUTHORITY in policy.required_claims
            assert TargetRequiredClaim.FIXTURE_SAFETY_PROFILE_VALID in policy.required_claims
        if policy.z_tier == TargetZTier.WET:
            assert TargetRequiredClaim.WET_WORKFLOW_READY in policy.required_claims


def test_target_policy_names_stay_in_sync_with_legacy_lookup() -> None:
    assert set(target_policy_names()) == set(TARGET_CLASS_BY_NAME)


def test_target_required_claim_values_remain_stable_strings() -> None:
    policy = target_policy_for("offset_x_1p5_low_z_dry")

    assert [claim.value for claim in policy.required_claims] == [
        "fixture_qc_gate_passed",
        "registration_gate_passed",
        "home_clearance_gate_passed",
        "fixture_safety_profile_valid",
        "promoted_offset_authority",
    ]
