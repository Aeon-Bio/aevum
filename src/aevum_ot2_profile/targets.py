from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ot2_harness.core.targets import (
    TargetGeometry,
    TargetPolicy,
    TargetPolicyBundle,
    TargetRequiredClaim,
    TargetZTier,
)

from aevum_ot2_profile._params import AevumProfileSnapshot, capture_aevum_profile_snapshot

_BASE_CLAIMS = [
    TargetRequiredClaim.FIXTURE_QC_GATE_PASSED,
    TargetRequiredClaim.REGISTRATION_GATE_PASSED,
    TargetRequiredClaim.HOME_CLEARANCE_GATE_PASSED,
]
_LOW_Z_CLAIMS = [
    *_BASE_CLAIMS,
    TargetRequiredClaim.FIXTURE_SAFETY_PROFILE_VALID,
    TargetRequiredClaim.PROMOTED_OFFSET_AUTHORITY,
]
_WET_CLAIMS = [
    *_LOW_Z_CLAIMS,
    TargetRequiredClaim.DRY_TARGET_PASSED,
    TargetRequiredClaim.WET_WORKFLOW_READY,
]

_GEOMETRY_DESCRIPTIONS = {
    "column_1_center": "Column 1 centerline target for first-pass high-Z proof.",
    "column_2_offset_x_1p0": "Column 2 target offset 1.0 mm in fixture X.",
    "column_3_offset_x_1p5": "Column 3 target offset 1.5 mm in fixture X.",
    "column_4_offset_x_2p0_boundary": "Boundary column target offset 2.0 mm in fixture X.",
    "mat_patch_column_3_offset_x_1p5": "Mat-patch column 3 target offset 1.5 mm in fixture X.",
}


def build_target_policy_bundle(
    *,
    snapshot: AevumProfileSnapshot | None = None,
    params_path: str | Path | None = None,
) -> TargetPolicyBundle:
    """Build Aevum's immutable target authority bundle from one captured snapshot."""

    active = _active_snapshot(snapshot=snapshot, params_path=params_path)
    policies = tuple(_target_policies_from_snapshot(active))
    geometries = tuple(_target_geometries(policies))
    bundle = TargetPolicyBundle(
        fixture_load_name=active.load_name,
        fixture_params_sha256=active.params_sha256,
        labware_definition_sha256=active.labware_definition_sha256,
        consumer_source_sha256=active.params_sha256,
        policy_digest_sha256="0" * 64,
        geometries=geometries,
        policies=policies,
    )
    return bundle.model_copy(update={"policy_digest_sha256": bundle.canonical_digest()})


def build_target_policies(
    *,
    params_path: str | Path | None = None,
    snapshot: AevumProfileSnapshot | None = None,
) -> list[TargetPolicy]:
    """Build Aevum target policy from its tracked pipette-offset geometry."""

    return list(build_target_policy_bundle(snapshot=snapshot, params_path=params_path).policies)


def _active_snapshot(
    *,
    snapshot: AevumProfileSnapshot | None,
    params_path: str | Path | None,
) -> AevumProfileSnapshot:
    if snapshot is not None and params_path is not None:
        raise ValueError("provide either snapshot or params_path, not both")
    return snapshot if snapshot is not None else capture_aevum_profile_snapshot(params_path)


def _target_policies_from_snapshot(snapshot: AevumProfileSnapshot) -> list[TargetPolicy]:
    offsets = _fixture_offsets(snapshot.params)
    center = offsets["center"]
    x_1p0 = offsets["x_1p0"]
    x_1p5 = offsets["x_1p5"]
    x_2p0 = offsets["x_2p0"]

    return [
        _policy(
            "center_high_z",
            "column_1_center",
            1,
            center,
            TargetZTier.HIGH_Z,
            first_pass_allowed=True,
            claims=_BASE_CLAIMS,
        ),
        _policy(
            "center_low_z_dry",
            "column_1_center",
            1,
            center,
            TargetZTier.LOW_Z_DRY,
            predecessors=["center_high_z"],
            claims=_LOW_Z_CLAIMS,
        ),
        _policy(
            "offset_x_1p0_high_z",
            "column_2_offset_x_1p0",
            2,
            x_1p0,
            TargetZTier.HIGH_Z,
            predecessors=["center_low_z_dry"],
            claims=_BASE_CLAIMS,
        ),
        _policy(
            "offset_x_1p0_low_z_dry",
            "column_2_offset_x_1p0",
            2,
            x_1p0,
            TargetZTier.LOW_Z_DRY,
            predecessors=["offset_x_1p0_high_z"],
            claims=_LOW_Z_CLAIMS,
        ),
        _policy(
            "offset_x_1p5_high_z",
            "column_3_offset_x_1p5",
            3,
            x_1p5,
            TargetZTier.HIGH_Z,
            predecessors=["offset_x_1p0_low_z_dry"],
            claims=_BASE_CLAIMS,
        ),
        _policy(
            "offset_x_1p5_low_z_dry",
            "column_3_offset_x_1p5",
            3,
            x_1p5,
            TargetZTier.LOW_Z_DRY,
            predecessors=["offset_x_1p5_high_z"],
            claims=_LOW_Z_CLAIMS,
        ),
        _policy(
            "offset_x_2p0_high_z",
            "column_4_offset_x_2p0_boundary",
            4,
            x_2p0,
            TargetZTier.HIGH_Z,
            boundary=True,
            predecessors=["offset_x_1p5_low_z_dry"],
            claims=_BASE_CLAIMS,
        ),
        _policy(
            "offset_x_2p0_low_z_dry",
            "column_4_offset_x_2p0_boundary",
            4,
            x_2p0,
            TargetZTier.LOW_Z_DRY,
            boundary=True,
            predecessors=["offset_x_2p0_high_z"],
            claims=_LOW_Z_CLAIMS,
        ),
        _policy(
            "center_wet",
            "column_1_center",
            1,
            center,
            TargetZTier.WET,
            wet=True,
            predecessors=["center_low_z_dry"],
            claims=_WET_CLAIMS,
        ),
        _policy(
            "offset_x_1p0_wet",
            "column_2_offset_x_1p0",
            2,
            x_1p0,
            TargetZTier.WET,
            wet=True,
            predecessors=["offset_x_1p0_low_z_dry"],
            claims=_WET_CLAIMS,
        ),
        _policy(
            "offset_x_1p5_wet",
            "column_3_offset_x_1p5",
            3,
            x_1p5,
            TargetZTier.WET,
            wet=True,
            predecessors=["offset_x_1p5_low_z_dry"],
            claims=_WET_CLAIMS,
        ),
        _policy(
            "offset_x_2p0_wet",
            "column_4_offset_x_2p0_boundary",
            4,
            x_2p0,
            TargetZTier.WET,
            wet=True,
            boundary=True,
            predecessors=["offset_x_2p0_low_z_dry"],
            claims=_WET_CLAIMS,
        ),
        _policy(
            "mat_patch_offset_x_1p5_low_z_dry",
            "mat_patch_column_3_offset_x_1p5",
            3,
            x_1p5,
            TargetZTier.LOW_Z_DRY,
            mat_patch=True,
            predecessors=["offset_x_1p5_low_z_dry"],
            claims=_LOW_Z_CLAIMS,
        ),
        _policy(
            "mat_patch_offset_x_1p5_wet",
            "mat_patch_column_3_offset_x_1p5",
            3,
            x_1p5,
            TargetZTier.WET,
            wet=True,
            mat_patch=True,
            predecessors=[
                "mat_patch_offset_x_1p5_low_z_dry",
                "offset_x_1p5_wet",
            ],
            claims=_WET_CLAIMS,
        ),
    ]


def _target_geometries(policies: tuple[TargetPolicy, ...]) -> list[TargetGeometry]:
    geometries: list[TargetGeometry] = []
    seen: set[str] = set()
    for policy in policies:
        if policy.geometry_id in seen:
            continue
        seen.add(policy.geometry_id)
        geometries.append(
            TargetGeometry(
                geometry_id=policy.geometry_id,
                column_index=policy.column_index,
                column_offset_x_mm=policy.column_offset_x_mm,
                description=_GEOMETRY_DESCRIPTIONS[policy.geometry_id],
                mat_patch=policy.mat_patch,
                boundary=policy.boundary,
            )
        )
    return geometries


def _fixture_offsets(params: Mapping[str, Any]) -> dict[str, float]:
    raw_offsets = params.get("pipette_offsets")
    if not isinstance(raw_offsets, Sequence) or isinstance(raw_offsets, (str, bytes)):
        raise ValueError("pipette_offsets must be a sequence")
    offsets: dict[str, float] = {}
    for offset in raw_offsets:
        if not isinstance(offset, Mapping):
            raise ValueError("each pipette offset must be an object")
        name = offset.get("name")
        x = offset.get("x")
        y = offset.get("y")
        if (
            not isinstance(name, str)
            or type(x) not in (int, float)
            or type(y) not in (int, float)
            or float(y) != 0.0
        ):
            raise ValueError("Aevum target offsets require named numeric X and zero Y")
        x_mm = float(x)
        if not math.isfinite(x_mm):
            raise ValueError("Aevum target offsets require finite X values")
        offsets[name] = x_mm
    required = {"center", "x_1p0", "x_1p5", "x_2p0"}
    if offsets.keys() != required:
        raise ValueError("Aevum target offsets must be exactly center, x_1p0, x_1p5, x_2p0")
    return offsets


def _policy(
    target_class: str,
    geometry_id: str,
    column_index: int,
    column_offset_x_mm: float,
    z_tier: TargetZTier,
    *,
    wet: bool = False,
    mat_patch: bool = False,
    boundary: bool = False,
    first_pass_allowed: bool = False,
    predecessors: list[str] | None = None,
    claims: list[TargetRequiredClaim],
) -> TargetPolicy:
    return TargetPolicy(
        target_class=target_class,
        geometry_id=geometry_id,
        column_index=column_index,
        column_offset_x_mm=column_offset_x_mm,
        z_tier=z_tier,
        wet=wet,
        mat_patch=mat_patch,
        boundary=boundary,
        first_pass_allowed=first_pass_allowed,
        required_predecessors=tuple(predecessors or []),
        required_claims=tuple(claims),
    )
