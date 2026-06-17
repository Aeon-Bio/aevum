from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from aevum_ot2.core.records import TARGET_CLASS_BY_NAME, target_class_names


class TargetZTier(StrEnum):
    HIGH_Z = "high_z"
    LOW_Z_DRY = "low_z_dry"
    WET = "wet"


class TargetRequiredClaim(StrEnum):
    FIXTURE_QC_GATE_PASSED = "fixture_qc_gate_passed"
    REGISTRATION_GATE_PASSED = "registration_gate_passed"
    HOME_CLEARANCE_GATE_PASSED = "home_clearance_gate_passed"
    FIXTURE_SAFETY_PROFILE_VALID = "fixture_safety_profile_valid"
    PROMOTED_OFFSET_AUTHORITY = "promoted_offset_authority"
    DRY_TARGET_PASSED = "dry_target_passed"
    WET_WORKFLOW_READY = "wet_workflow_ready"


class TargetGeometry(BaseModel):
    geometry_id: str
    column_index: int | None = None
    column_offset_x_mm: float | None = None
    description: str
    mat_patch: bool = False
    boundary: bool = False


class TargetPolicy(BaseModel):
    target_class: str
    geometry_id: str
    column_index: int | None = None
    column_offset_x_mm: float | None = None
    z_tier: TargetZTier
    wet: bool = False
    mat_patch: bool = False
    boundary: bool = False
    first_pass_allowed: bool = False
    required_predecessors: list[str] = Field(default_factory=list)
    required_claims: list[TargetRequiredClaim] = Field(default_factory=list)


BASE_REGISTRATION_CLAIMS = (
    TargetRequiredClaim.FIXTURE_QC_GATE_PASSED,
    TargetRequiredClaim.REGISTRATION_GATE_PASSED,
    TargetRequiredClaim.HOME_CLEARANCE_GATE_PASSED,
)
LOW_Z_CLAIMS = (
    *BASE_REGISTRATION_CLAIMS,
    TargetRequiredClaim.FIXTURE_SAFETY_PROFILE_VALID,
    TargetRequiredClaim.PROMOTED_OFFSET_AUTHORITY,
)
WET_CLAIMS = (
    *LOW_Z_CLAIMS,
    TargetRequiredClaim.DRY_TARGET_PASSED,
    TargetRequiredClaim.WET_WORKFLOW_READY,
)


TARGET_GEOMETRIES: tuple[TargetGeometry, ...] = (
    TargetGeometry(
        geometry_id="column_1_center",
        column_index=1,
        column_offset_x_mm=0.0,
        description="column 1 center target geometry",
    ),
    TargetGeometry(
        geometry_id="column_2_offset_x_1p0",
        column_index=2,
        column_offset_x_mm=1.0,
        description="column 2 +1.0 mm X target geometry",
    ),
    TargetGeometry(
        geometry_id="column_3_offset_x_1p5",
        column_index=3,
        column_offset_x_mm=1.5,
        description="column 3 +1.5 mm X target geometry",
    ),
    TargetGeometry(
        geometry_id="column_4_offset_x_2p0_boundary",
        column_index=4,
        column_offset_x_mm=2.0,
        description="column 4 +2.0 mm X boundary target geometry",
        boundary=True,
    ),
    TargetGeometry(
        geometry_id="mat_patch_column_3_offset_x_1p5",
        column_index=3,
        column_offset_x_mm=1.5,
        description="mat patch aligned to column 3 +1.5 mm X target geometry",
        mat_patch=True,
    ),
)
TARGET_GEOMETRY_BY_ID = {geometry.geometry_id: geometry for geometry in TARGET_GEOMETRIES}


TARGET_POLICIES: tuple[TargetPolicy, ...] = (
    TargetPolicy(
        target_class="center_high_z",
        geometry_id="column_1_center",
        column_index=1,
        column_offset_x_mm=0.0,
        z_tier=TargetZTier.HIGH_Z,
        first_pass_allowed=True,
        required_claims=list(BASE_REGISTRATION_CLAIMS),
    ),
    TargetPolicy(
        target_class="center_low_z_dry",
        geometry_id="column_1_center",
        column_index=1,
        column_offset_x_mm=0.0,
        z_tier=TargetZTier.LOW_Z_DRY,
        required_predecessors=["center_high_z"],
        required_claims=list(LOW_Z_CLAIMS),
    ),
    TargetPolicy(
        target_class="offset_x_1p0_high_z",
        geometry_id="column_2_offset_x_1p0",
        column_index=2,
        column_offset_x_mm=1.0,
        z_tier=TargetZTier.HIGH_Z,
        required_predecessors=["center_low_z_dry"],
        required_claims=list(BASE_REGISTRATION_CLAIMS),
    ),
    TargetPolicy(
        target_class="offset_x_1p0_low_z_dry",
        geometry_id="column_2_offset_x_1p0",
        column_index=2,
        column_offset_x_mm=1.0,
        z_tier=TargetZTier.LOW_Z_DRY,
        required_predecessors=["offset_x_1p0_high_z"],
        required_claims=list(LOW_Z_CLAIMS),
    ),
    TargetPolicy(
        target_class="offset_x_1p5_high_z",
        geometry_id="column_3_offset_x_1p5",
        column_index=3,
        column_offset_x_mm=1.5,
        z_tier=TargetZTier.HIGH_Z,
        required_predecessors=["offset_x_1p0_low_z_dry"],
        required_claims=list(BASE_REGISTRATION_CLAIMS),
    ),
    TargetPolicy(
        target_class="offset_x_1p5_low_z_dry",
        geometry_id="column_3_offset_x_1p5",
        column_index=3,
        column_offset_x_mm=1.5,
        z_tier=TargetZTier.LOW_Z_DRY,
        required_predecessors=["offset_x_1p5_high_z"],
        required_claims=list(LOW_Z_CLAIMS),
    ),
    TargetPolicy(
        target_class="offset_x_2p0_high_z",
        geometry_id="column_4_offset_x_2p0_boundary",
        column_index=4,
        column_offset_x_mm=2.0,
        z_tier=TargetZTier.HIGH_Z,
        boundary=True,
        required_predecessors=["offset_x_1p5_low_z_dry"],
        required_claims=list(BASE_REGISTRATION_CLAIMS),
    ),
    TargetPolicy(
        target_class="offset_x_2p0_low_z_dry",
        geometry_id="column_4_offset_x_2p0_boundary",
        column_index=4,
        column_offset_x_mm=2.0,
        z_tier=TargetZTier.LOW_Z_DRY,
        boundary=True,
        required_predecessors=["offset_x_2p0_high_z"],
        required_claims=list(LOW_Z_CLAIMS),
    ),
    TargetPolicy(
        target_class="center_wet",
        geometry_id="column_1_center",
        column_index=1,
        column_offset_x_mm=0.0,
        z_tier=TargetZTier.WET,
        wet=True,
        required_predecessors=["center_low_z_dry"],
        required_claims=list(WET_CLAIMS),
    ),
    TargetPolicy(
        target_class="offset_x_1p0_wet",
        geometry_id="column_2_offset_x_1p0",
        column_index=2,
        column_offset_x_mm=1.0,
        z_tier=TargetZTier.WET,
        wet=True,
        required_predecessors=["offset_x_1p0_low_z_dry"],
        required_claims=list(WET_CLAIMS),
    ),
    TargetPolicy(
        target_class="offset_x_1p5_wet",
        geometry_id="column_3_offset_x_1p5",
        column_index=3,
        column_offset_x_mm=1.5,
        z_tier=TargetZTier.WET,
        wet=True,
        required_predecessors=["offset_x_1p5_low_z_dry"],
        required_claims=list(WET_CLAIMS),
    ),
    TargetPolicy(
        target_class="offset_x_2p0_wet",
        geometry_id="column_4_offset_x_2p0_boundary",
        column_index=4,
        column_offset_x_mm=2.0,
        z_tier=TargetZTier.WET,
        wet=True,
        boundary=True,
        required_predecessors=["offset_x_2p0_low_z_dry"],
        required_claims=list(WET_CLAIMS),
    ),
    TargetPolicy(
        target_class="mat_patch_offset_x_1p5_low_z_dry",
        geometry_id="mat_patch_column_3_offset_x_1p5",
        column_index=3,
        column_offset_x_mm=1.5,
        z_tier=TargetZTier.LOW_Z_DRY,
        mat_patch=True,
        required_predecessors=["offset_x_1p5_low_z_dry"],
        required_claims=list(LOW_Z_CLAIMS),
    ),
    TargetPolicy(
        target_class="mat_patch_offset_x_1p5_wet",
        geometry_id="mat_patch_column_3_offset_x_1p5",
        column_index=3,
        column_offset_x_mm=1.5,
        z_tier=TargetZTier.WET,
        wet=True,
        mat_patch=True,
        required_predecessors=[
            "mat_patch_offset_x_1p5_low_z_dry",
            "offset_x_1p5_wet",
        ],
        required_claims=list(WET_CLAIMS),
    ),
)
TARGET_POLICY_BY_NAME = {policy.target_class: policy for policy in TARGET_POLICIES}


def target_policies() -> list[TargetPolicy]:
    return list(TARGET_POLICIES)


def target_policy_names() -> list[str]:
    return [policy.target_class for policy in TARGET_POLICIES]


def target_policy_for(target_class: str) -> TargetPolicy:
    return TARGET_POLICY_BY_NAME[target_class]


def matching_high_z_target(target_class: str) -> str | None:
    policy = target_policy_for(target_class)
    if policy.z_tier != TargetZTier.LOW_Z_DRY:
        return None
    for predecessor in policy.required_predecessors:
        predecessor_policy = target_policy_for(predecessor)
        if (
            predecessor_policy.z_tier == TargetZTier.HIGH_Z
            and predecessor_policy.geometry_id == policy.geometry_id
        ):
            return predecessor
    return None


def validate_target_policy_table() -> list[str]:
    reasons: list[str] = []
    declared_names = set(target_class_names())
    policy_names = set(target_policy_names())

    missing_policies = sorted(declared_names - policy_names)
    extra_policies = sorted(policy_names - declared_names)
    if missing_policies:
        reasons.append("missing target policies: " + ", ".join(missing_policies))
    if extra_policies:
        reasons.append("target policies without target classes: " + ", ".join(extra_policies))

    for policy in TARGET_POLICIES:
        legacy_target = TARGET_CLASS_BY_NAME.get(policy.target_class)
        if legacy_target is not None:
            if legacy_target.wet != policy.wet:
                reasons.append(f"{policy.target_class} wet flag does not match TargetClass")
            if legacy_target.mat_patch != policy.mat_patch:
                reasons.append(
                    f"{policy.target_class} mat_patch flag does not match TargetClass"
                )
            if legacy_target.boundary != policy.boundary:
                reasons.append(
                    f"{policy.target_class} boundary flag does not match TargetClass"
                )
            missing_legacy_predecessors = sorted(
                set(legacy_target.requires) - set(policy.required_predecessors)
            )
            if missing_legacy_predecessors:
                reasons.append(
                    f"{policy.target_class} policy omits legacy predecessors: "
                    + ", ".join(missing_legacy_predecessors)
                )
        if policy.geometry_id not in TARGET_GEOMETRY_BY_ID:
            reasons.append(f"{policy.target_class} has unknown geometry {policy.geometry_id}")
        if policy.boundary and policy.first_pass_allowed:
            reasons.append(f"{policy.target_class} boundary target cannot be first pass")
        if policy.target_class in policy.required_predecessors:
            reasons.append(f"{policy.target_class} requires itself")
        for predecessor in policy.required_predecessors:
            if predecessor not in policy_names:
                reasons.append(
                    f"{policy.target_class} has unknown predecessor {predecessor}"
                )
        if (
            policy.z_tier == TargetZTier.LOW_Z_DRY
            and not policy.mat_patch
            and matching_high_z_target(policy.target_class) is None
        ):
            reasons.append(f"{policy.target_class} lacks matching high-Z predecessor")

    return reasons
