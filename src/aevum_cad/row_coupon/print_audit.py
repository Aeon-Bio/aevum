from __future__ import annotations

from collections import Counter
from typing import Any

from .artifacts import (
    ROW_COUPON_DISCRETE_UNSPLITTABLE_INSTALLED_PARTS,
    ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS,
    row_coupon_physical_artifact_print_policies,
)
from .final_print_pieces import realize_row_coupon_final_print_pieces


def _fits_bed(x: float, y: float, bed_x: float, bed_y: float) -> bool:
    return (x <= bed_x and y <= bed_y) or (x <= bed_y and y <= bed_x)


def audit_row_coupon_print_artifacts(params: dict[str, Any]) -> dict[str, Any]:
    """Build and fail closed over the canonical physical print contract."""

    realization = realize_row_coupon_final_print_pieces(params)
    realization.require_printable()
    policies = row_coupon_physical_artifact_print_policies(
        params,
        bed_x_mm=250.0,
        bed_y_mm=210.0,
        fits_rectangular_bed=_fits_bed,
    )
    names = [str(row["name"]) for row in realization.plan]
    if names != list(realization.pieces) or len(names) != len(set(names)):
        raise ValueError("final print plan and realized piece keys diverge")

    rows_by_source: dict[str, list[dict[str, Any]]] = {}
    for row in realization.plan:
        rows_by_source.setdefault(str(row["source_artifact"]), []).append(row)
        name = str(row["name"])
        value = realization.pieces[name].val()
        if len(value.Solids()) != 1 or value.Volume() <= 0.0:
            raise ValueError(f"{name}: expected one positive connected solid")
        bb = value.BoundingBox()
        if not _fits_bed(float(bb.xlen), float(bb.ylen), 250.0, 210.0):
            raise ValueError(f"{name}: raw geometry does not fit the selected bed")
        expected = f"canonical physical artifact: {row['source_artifact']}"
        if row["provenance"] != expected:
            raise ValueError(f"{name}: invalid source provenance")

    installed_by_source = {policy.name: policy.installed_part for policy in policies}
    for source, rows in rows_by_source.items():
        installed_part = installed_by_source[source]
        if installed_part in ROW_COUPON_DISCRETE_UNSPLITTABLE_INSTALLED_PARTS:
            if len(rows) != 1 or rows[0]["action"] != "identity":
                raise ValueError(f"{source}: discrete/removable artifact was split")
        elif len(rows) > 1:
            if source not in ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS:
                raise ValueError(f"{source}: structural split is not allowlisted")
            if len(rows) != 2 or any(row["action"] != "structural_split" for row in rows):
                raise ValueError(f"{source}: invalid structural split cardinality")

    policy_counts = Counter(policy.policy for policy in policies)
    action_counts = Counter(str(row["action"]) for row in realization.plan)
    # These totals are NOT constants.  Several artifact families are sized by the
    # plate layout (one wedge lock per latch station, one face gasket per IR
    # mount, ...), so pinning literal counts here made a legitimate layout change
    # -- the latch-station pattern going from 9 stations to 12 -- read as a print
    # contract failure.  What must hold, and what actually fails closed, is the
    # relation between the two independently derived tables: only these three
    # policies may occur at the production bed (a `discrete_unsplittable` policy
    # means a removable artifact no longer fits and must not be silently split),
    # every bed-fitting printed artifact yields exactly one identity piece, every
    # allowlisted structural source yields exactly two split pieces, and no
    # non-printed artifact reaches the print queue at all.
    if set(policy_counts) - {
        "bed_fit_identity",
        "structural_split_allowed",
        "nonprinted_or_flexible",
    }:
        raise ValueError(f"unexpected artifact policy kinds: {dict(policy_counts)}")
    if set(action_counts) - {"identity", "structural_split"}:
        raise ValueError(f"unexpected final-piece action kinds: {dict(action_counts)}")
    if action_counts["identity"] != policy_counts["bed_fit_identity"]:
        raise ValueError(
            "identity pieces do not match bed-fitting printed artifacts: "
            f"{action_counts['identity']} != {policy_counts['bed_fit_identity']}"
        )
    if action_counts["structural_split"] != 2 * policy_counts["structural_split_allowed"]:
        raise ValueError(
            "structural split pieces are not two per allowlisted source: "
            f"{action_counts['structural_split']} != "
            f"{2 * policy_counts['structural_split_allowed']}"
        )
    nonprinted = {
        policy.name for policy in policies if policy.policy == "nonprinted_or_flexible"
    }
    if nonprinted & set(rows_by_source):
        raise ValueError(
            "non-printed artifact reached the print queue: "
            f"{sorted(nonprinted & set(rows_by_source))}"
        )
    if len(policies) != len(rows_by_source) + len(nonprinted):
        raise ValueError(
            "printed artifacts and print-plan sources diverge: "
            f"{len(policies)} policies, {len(rows_by_source)} planned sources, "
            f"{len(nonprinted)} non-printed"
        )

    return {
        "physical_artifacts": len(realization.pieces)
        + policy_counts["nonprinted_or_flexible"],
        "rigid_print_pieces": len(realization.pieces),
        "whole_rigid_pieces": action_counts["identity"],
        "structural_piece_bodies": action_counts["structural_split"],
        "structural_sources": policy_counts["structural_split_allowed"],
        "flexible_or_compressible": policy_counts["nonprinted_or_flexible"],
        "piece_names": names,
    }
