"""SMIS head-swap registration policy.

Registration is a distinct authority from docking. A module can fit the dock,
pass the manifest envelope, and still be unusable until the platform has enough
post-dock evidence to bind the module's optical axis back to the plate-support
fiducial world frame.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from aevum_smis.driver import RegistrationResult
from aevum_smis.manifest import ModuleManifest


class RegistrationTier(StrEnum):
    tier_a = "A"  # trust coupling + one fiducial touch-up
    tier_b = "B"  # re-fiducial + autofocus map
    tier_c = "C"  # full re-calibration


class RegistrationRitual(BaseModel):
    """Required post-dock ritual for a module in a given swap context."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tier: RegistrationTier
    min_fiducials: int
    requires_autofocus_map: bool
    requires_full_calibration: bool
    uses_declared_axis_offset: bool


class RegistrationCheck(BaseModel):
    """Validation result for a driver's ``on_dock`` registration output."""

    model_config = ConfigDict(frozen=True)

    accepted: bool
    blockers: tuple[str, ...]
    required_tier: RegistrationTier
    reported_tier: str
    fiducials_used: int
    min_fiducials: int
    requires_autofocus_map: bool
    requires_full_calibration: bool


TIER_RANK: dict[RegistrationTier, int] = {
    RegistrationTier.tier_a: 1,
    RegistrationTier.tier_b: 2,
    RegistrationTier.tier_c: 3,
}

# A 2D rigid transform (carriage frame -> plate-support datum) needs >=3 non-collinear
# fiducials to recover; the tier ritual's `min_fiducials` is a separate, possibly smaller
# minimum (Tier A trusts coupling with one touch-up and does NOT independently recover).
MIN_POSE_FIT_FIDUCIALS = 3

# The full sha256 pose digest length. A short/garbage digest must not pass as agreement.
POSE_DIGEST_LENGTH = 64

# Conservative placeholder for the rigid-fit residual gate. The real bound is Stage-0 /
# Stage-3 metrology (kinematic-seating variation is ~+/-50-100 um per observation_module.md);
# this default fails closed but MUST be replaced by a measured tolerance before it gates a
# real acquisition. Callers should pass an explicit, evidence-backed tolerance.
DEFAULT_POSE_RESIDUAL_TOLERANCE_UM = 50.0


class ObserverPoseCheck(BaseModel):
    """Cross-check that the observer-recovered installed pose agrees with the declared one.

    This is a DISTINCT authority from the Tier A/B/C ritual (`validate_registration_result`,
    which asks "did on_dock satisfy the required ritual") and from the bridge `observer_scan`
    lease, source-enable, and compatibility gates. It asks the coordinate question: is the
    declared canonical->installed transform still current (not stale), and does the observer's
    independent fiducial recovery agree with it within a measured residual tolerance?

    Pose digests are opaque sha256 strings here, so this package stays decoupled from the
    bridge's `FixturePose` (SMIS does not import the bridge).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    accepted: bool
    blockers: tuple[str, ...]
    independent_recovery_required: bool
    declared_pose_digest: str
    registered_pose_digest: str
    fiducials_used: int
    min_fit_fiducials: int
    recovered_residual_um: float | None
    residual_tolerance_um: float


def _pose_digest_blockers(digest: str, *, label: str) -> list[str]:
    if not digest:
        return [f"{label}_missing"]
    if len(digest) != POSE_DIGEST_LENGTH:
        return [f"{label}_malformed"]
    return []


def cross_check_observer_pose(
    registration: RegistrationCheck,
    *,
    declared_pose_digest: str,
    registered_pose_digest: str,
    recovered_residual_um: float | None = None,
    residual_tolerance_um: float = DEFAULT_POSE_RESIDUAL_TOLERANCE_UM,
) -> ObserverPoseCheck:
    """Fail closed unless the declared pose is current AND the recovery agrees with it.

    Blockers (each a separate, named reason — never collapsed into one boolean):

    - ``registration_not_accepted`` — the Tier A/B/C ritual itself failed; pose is moot.
    - ``declared_pose_digest_missing`` / ``_malformed`` — no current declared transform to
      bind to (empty/short digest cannot stand in for a pose).
    - ``observer_registration_digest_missing`` / ``_malformed`` — the recovery was not bound
      to a recorded pose.
    - ``observer_pose_stale`` — the declared pose digest changed since the observer registered
      against it (plate re-seated / re-declared); the registration is stale, reject.
    - ``observer_pose_fiducials_insufficient`` — fewer than 3 fiducials for a rigid fit
      (only when an independent recovery was required, i.e. Tier B/C).
    - ``observer_pose_residual_missing`` / ``observer_pose_residual_exceeds_tolerance`` — the
      fit residual is absent or worse than the (measured) tolerance.

    Tier A "trust coupling" uses the declared axis offset and does NOT independently recover a
    pose, so the fiducials-fit and residual checks are skipped for it; staleness and digest
    presence still apply to every tier.
    """
    independent_recovery_required = registration.required_tier in {
        RegistrationTier.tier_b,
        RegistrationTier.tier_c,
    }
    blockers: list[str] = []

    if not registration.accepted:
        blockers.append("registration_not_accepted")

    blockers.extend(_pose_digest_blockers(declared_pose_digest, label="declared_pose_digest"))
    blockers.extend(
        _pose_digest_blockers(registered_pose_digest, label="observer_registration_digest")
    )

    # Staleness: the declared pose must not have changed since the observer registered against
    # it. Only meaningful once both digests are well-formed.
    if (
        declared_pose_digest
        and registered_pose_digest
        and len(declared_pose_digest) == POSE_DIGEST_LENGTH
        and len(registered_pose_digest) == POSE_DIGEST_LENGTH
        and declared_pose_digest != registered_pose_digest
    ):
        blockers.append("observer_pose_stale")

    if independent_recovery_required:
        if registration.fiducials_used < MIN_POSE_FIT_FIDUCIALS:
            blockers.append("observer_pose_fiducials_insufficient")
        if recovered_residual_um is None:
            blockers.append("observer_pose_residual_missing")
        elif recovered_residual_um > residual_tolerance_um:
            blockers.append("observer_pose_residual_exceeds_tolerance")

    return ObserverPoseCheck(
        accepted=not blockers,
        blockers=tuple(blockers),
        independent_recovery_required=independent_recovery_required,
        declared_pose_digest=declared_pose_digest,
        registered_pose_digest=registered_pose_digest,
        fiducials_used=registration.fiducials_used,
        min_fit_fiducials=MIN_POSE_FIT_FIDUCIALS,
        recovered_residual_um=recovered_residual_um,
        residual_tolerance_um=residual_tolerance_um,
    )


def required_registration_ritual(
    manifest: ModuleManifest,
    *,
    first_install: bool = False,
    force_full_calibration: bool = False,
) -> RegistrationRitual:
    """Choose the minimum post-dock registration ritual for this head/context."""

    if first_install or force_full_calibration:
        return RegistrationRitual(
            tier=RegistrationTier.tier_c,
            min_fiducials=16,
            requires_autofocus_map=True,
            requires_full_calibration=True,
            uses_declared_axis_offset=False,
        )
    if manifest.requires_post_dock_autofocus:
        return RegistrationRitual(
            tier=RegistrationTier.tier_b,
            min_fiducials=3,
            requires_autofocus_map=True,
            requires_full_calibration=False,
            uses_declared_axis_offset=False,
        )
    return RegistrationRitual(
        tier=RegistrationTier.tier_a,
        min_fiducials=1,
        requires_autofocus_map=False,
        requires_full_calibration=False,
        uses_declared_axis_offset=True,
    )


def validate_registration_result(
    manifest: ModuleManifest,
    result: RegistrationResult,
    *,
    first_install: bool = False,
    force_full_calibration: bool = False,
) -> RegistrationCheck:
    """Fail closed unless ``on_dock`` satisfied the required Tier A/B/C ritual."""

    ritual = required_registration_ritual(
        manifest,
        first_install=first_install,
        force_full_calibration=force_full_calibration,
    )
    blockers: list[str] = []
    try:
        reported = RegistrationTier(result.tier)
    except ValueError:
        reported = None
        blockers.append("registration_tier_unknown")

    if not result.ok:
        blockers.append("registration_result_not_ok")
    if reported is not None and TIER_RANK[reported] < TIER_RANK[ritual.tier]:
        blockers.append("registration_tier_insufficient")
    if result.fiducials_used < ritual.min_fiducials:
        blockers.append("registration_fiducials_insufficient")

    return RegistrationCheck(
        accepted=not blockers,
        blockers=tuple(blockers),
        required_tier=ritual.tier,
        reported_tier=result.tier,
        fiducials_used=result.fiducials_used,
        min_fiducials=ritual.min_fiducials,
        requires_autofocus_map=ritual.requires_autofocus_map,
        requires_full_calibration=ritual.requires_full_calibration,
    )
