from __future__ import annotations

from aevum_smis import (
    MIN_POSE_FIT_FIDUCIALS,
    ModuleManifest,
    RegistrationResult,
    RegistrationTier,
    SafetyClass,
    cross_check_observer_pose,
    required_registration_ritual,
    validate_registration_result,
)

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def _manifest(**overrides) -> ModuleManifest:
    base = dict(
        sku="obs-brightfield-4x",
        module_serial="SN-0001",
        hw_rev="A",
        smis_version="0.1",
        safety_class=SafetyClass.led,
        driver="aevum_modules.brightfield",
        mass_g=350.0,
        front_end_length_x_mm=21.0,
        front_end_width_y_mm=13.0,
        front_end_height_z_mm=28.0,
        focus_stroke_z_mm=12.0,
        barrel_diameter_mm=20.0,
    )
    base.update(overrides)
    return ModuleManifest(**base)


def test_tier_a_is_default_for_low_na_coupling_trust() -> None:
    ritual = required_registration_ritual(_manifest())
    assert ritual.tier == RegistrationTier.tier_a
    assert ritual.min_fiducials == 1
    assert ritual.uses_declared_axis_offset is True
    assert ritual.requires_autofocus_map is False

    check = validate_registration_result(
        _manifest(),
        RegistrationResult(tier="A", ok=True, fiducials_used=1),
    )
    assert check.accepted is True
    assert check.blockers == ()


def test_post_dock_autofocus_requires_tier_b_or_better() -> None:
    manifest = _manifest(requires_post_dock_autofocus=True)
    ritual = required_registration_ritual(manifest)
    assert ritual.tier == RegistrationTier.tier_b
    assert ritual.min_fiducials == 3
    assert ritual.requires_autofocus_map is True

    too_weak = validate_registration_result(
        manifest,
        RegistrationResult(tier="A", ok=True, fiducials_used=1),
    )
    assert too_weak.accepted is False
    assert too_weak.blockers == (
        "registration_tier_insufficient",
        "registration_fiducials_insufficient",
    )

    tier_b = validate_registration_result(
        manifest,
        RegistrationResult(tier="B", ok=True, fiducials_used=3),
    )
    assert tier_b.accepted is True


def test_first_install_requires_full_tier_c_registration() -> None:
    manifest = _manifest()
    ritual = required_registration_ritual(manifest, first_install=True)
    assert ritual.tier == RegistrationTier.tier_c
    assert ritual.min_fiducials == 16
    assert ritual.requires_full_calibration is True
    assert ritual.uses_declared_axis_offset is False

    insufficient = validate_registration_result(
        manifest,
        RegistrationResult(tier="B", ok=True, fiducials_used=3),
        first_install=True,
    )
    assert insufficient.accepted is False
    assert insufficient.blockers == (
        "registration_tier_insufficient",
        "registration_fiducials_insufficient",
    )

    full = validate_registration_result(
        manifest,
        RegistrationResult(tier="C", ok=True, fiducials_used=16),
        first_install=True,
    )
    assert full.accepted is True


def test_unknown_or_failed_registration_fails_closed() -> None:
    unknown = validate_registration_result(
        _manifest(),
        RegistrationResult(tier="D", ok=True, fiducials_used=16),
    )
    assert unknown.accepted is False
    assert unknown.blockers == ("registration_tier_unknown",)

    failed = validate_registration_result(
        _manifest(),
        RegistrationResult(tier="A", ok=False, fiducials_used=1),
    )
    assert failed.accepted is False
    assert failed.blockers == ("registration_result_not_ok",)


# --- IN-C6 / HX2: observer pose-digest cross-check ----------------------------------------


def _tier_b_check(*, fiducials_used: int = 3, ok: bool = True):
    manifest = _manifest(requires_post_dock_autofocus=True)
    return validate_registration_result(
        manifest, RegistrationResult(tier="B", ok=ok, fiducials_used=fiducials_used)
    )


def _tier_a_check():
    return validate_registration_result(
        _manifest(), RegistrationResult(tier="A", ok=True, fiducials_used=1)
    )


def test_tier_b_recovery_agreeing_with_declared_pose_is_accepted() -> None:
    pose = cross_check_observer_pose(
        _tier_b_check(),
        declared_pose_digest=DIGEST_A,
        registered_pose_digest=DIGEST_A,
        recovered_residual_um=20.0,
        residual_tolerance_um=50.0,
    )
    assert pose.accepted is True
    assert pose.blockers == ()
    assert pose.independent_recovery_required is True


def test_stale_declared_pose_is_rejected() -> None:
    # the declared pose digest changed since the observer registered against it
    pose = cross_check_observer_pose(
        _tier_b_check(),
        declared_pose_digest=DIGEST_B,
        registered_pose_digest=DIGEST_A,
        recovered_residual_um=10.0,
    )
    assert pose.accepted is False
    assert "observer_pose_stale" in pose.blockers


def test_residual_over_tolerance_is_rejected() -> None:
    pose = cross_check_observer_pose(
        _tier_b_check(),
        declared_pose_digest=DIGEST_A,
        registered_pose_digest=DIGEST_A,
        recovered_residual_um=80.0,
        residual_tolerance_um=50.0,
    )
    assert pose.accepted is False
    assert "observer_pose_residual_exceeds_tolerance" in pose.blockers


def test_missing_residual_when_recovery_required_is_rejected() -> None:
    pose = cross_check_observer_pose(
        _tier_b_check(),
        declared_pose_digest=DIGEST_A,
        registered_pose_digest=DIGEST_A,
        recovered_residual_um=None,
    )
    assert pose.accepted is False
    assert "observer_pose_residual_missing" in pose.blockers


def test_too_few_fiducials_for_a_rigid_fit_is_rejected() -> None:
    # 2 fiducials cannot recover a 2D rigid transform even if the tier check were lenient
    pose = cross_check_observer_pose(
        _tier_b_check(fiducials_used=2),
        declared_pose_digest=DIGEST_A,
        registered_pose_digest=DIGEST_A,
        recovered_residual_um=10.0,
    )
    assert pose.accepted is False
    assert "observer_pose_fiducials_insufficient" in pose.blockers
    assert pose.min_fit_fiducials == MIN_POSE_FIT_FIDUCIALS


def test_missing_or_malformed_digests_fail_closed() -> None:
    missing = cross_check_observer_pose(
        _tier_b_check(),
        declared_pose_digest="",
        registered_pose_digest=DIGEST_A,
        recovered_residual_um=10.0,
    )
    assert missing.accepted is False
    assert "declared_pose_digest_missing" in missing.blockers
    # a missing declared digest must NOT also read as a (false) stale match
    assert "observer_pose_stale" not in missing.blockers

    malformed = cross_check_observer_pose(
        _tier_b_check(),
        declared_pose_digest="deadbeef",
        registered_pose_digest=DIGEST_A,
        recovered_residual_um=10.0,
    )
    assert malformed.accepted is False
    assert "declared_pose_digest_malformed" in malformed.blockers


def test_failed_registration_blocks_pose_acceptance() -> None:
    pose = cross_check_observer_pose(
        _tier_b_check(ok=False),
        declared_pose_digest=DIGEST_A,
        registered_pose_digest=DIGEST_A,
        recovered_residual_um=10.0,
    )
    assert pose.accepted is False
    assert "registration_not_accepted" in pose.blockers


def test_tier_a_trusts_coupling_and_skips_the_fit_checks() -> None:
    # Tier A uses the declared axis offset; there is no independent recovery to residual-gate,
    # so a missing residual / 1 fiducial does NOT block — but staleness still applies.
    pose = cross_check_observer_pose(
        _tier_a_check(),
        declared_pose_digest=DIGEST_A,
        registered_pose_digest=DIGEST_A,
        recovered_residual_um=None,
    )
    assert pose.independent_recovery_required is False
    assert pose.accepted is True
    assert pose.blockers == ()

    stale_tier_a = cross_check_observer_pose(
        _tier_a_check(),
        declared_pose_digest=DIGEST_B,
        registered_pose_digest=DIGEST_A,
        recovered_residual_um=None,
    )
    assert stale_tier_a.accepted is False
    assert stale_tier_a.blockers == ("observer_pose_stale",)
