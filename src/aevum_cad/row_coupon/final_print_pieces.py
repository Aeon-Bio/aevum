from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import cadquery as cq

from .artifacts import (
    build_row_coupon_physical_artifacts,
    row_coupon_physical_artifact_manifest,
    row_coupon_physical_artifact_print_policies,
)
from .layout import row_coupon_layout

DEFAULT_FIRST_PRINT_BED_X_MM = 250.0
DEFAULT_FIRST_PRINT_BED_Y_MM = 210.0


@dataclass(frozen=True)
class RowCouponFinalPrintRealization:
    """One authoritative realization of the final print plan and its exact bodies."""

    plan: tuple[dict[str, Any], ...]
    pieces: Mapping[str, cq.Workplane]
    assembly_position: bool

    def require_printable(self) -> None:
        for row in self.plan:
            diagnostics = tuple(row.get("diagnostics", ()))
            if diagnostics:
                raise ValueError(
                    f"final print-piece blocked for {row['source_artifact']}: {diagnostics[0]}"
                )


def _workplane_volume(model: cq.Workplane) -> float:
    return sum(float(value.Volume()) for value in model.vals())


def _reconstruction_metrics(
    source: cq.Workplane,
    lower: cq.Workplane,
    upper: cq.Workplane,
) -> dict[str, float]:
    rebuilt = lower.union(upper)
    source_volume = _workplane_volume(source)
    rebuilt_volume = _workplane_volume(rebuilt)
    source_rebuilt_overlap = _workplane_volume(source.intersect(rebuilt))
    pair_overlap = _workplane_volume(lower.intersect(upper))
    return {
        "pair_interference_volume_mm3": round(pair_overlap, 6),
        "source_missing_volume_mm3": round(max(0.0, source_volume - source_rebuilt_overlap), 6),
        "source_excess_volume_mm3": round(max(0.0, rebuilt_volume - source_rebuilt_overlap), 6),
        "reconstruction_volume_delta_mm3": round(rebuilt_volume - source_volume, 6),
    }


def _enforce_reconstruction_limits(
    source: cq.Workplane,
    metrics: Mapping[str, float],
    interface: Mapping[str, Any],
) -> None:
    """Apply limits that are independent of whatever feature was constructed.

    A feature must not be able to justify its own loss budget.  Canonical
    interfaces therefore carry absolute and relative caps; adversarially large
    pockets fail even when their bookkeeping is internally consistent.
    """

    source_volume = _workplane_volume(source)
    max_missing = min(
        float(interface.get("max_missing_volume_mm3", 25.0)),
        source_volume * float(interface.get("max_missing_fraction", 0.01)),
    )
    max_excess = float(interface.get("max_excess_volume_mm3", 1e-4))
    if metrics["source_missing_volume_mm3"] > max_missing + 1e-4:
        raise ValueError(
            "split reconstruction exceeds independent missing-material limit: "
            f"{metrics['source_missing_volume_mm3']} > {max_missing:.6f} mm^3"
        )
    if metrics["source_excess_volume_mm3"] > max_excess + 1e-4:
        raise ValueError(
            "split reconstruction exceeds independent source-excess limit: "
            f"{metrics['source_excess_volume_mm3']} > {max_excess:.6f} mm^3"
        )


def _validate_functional_exclusion_contract(interface: Mapping[str, Any]) -> tuple[str, ...]:
    declared = tuple(str(value) for value in interface.get("functional_exclusions", ()))
    expected = tuple(str(value) for value in interface.get("expected_functional_exclusions", ()))
    if expected and declared != expected:
        raise ValueError(
            "functional exclusion contract does not match the canonical allowlist: "
            f"declared={declared!r} expected={expected!r}"
        )
    if interface.get("canonical_source_artifact") and not expected:
        raise ValueError("canonical split source is missing an exclusion allowlist")
    return declared


def _butt_fallback_proof(
    source: cq.Workplane,
    lower: cq.Workplane,
    upper: cq.Workplane,
    *,
    clearance_mm: float,
    reason: str,
) -> dict[str, Any]:
    metrics = _reconstruction_metrics(source, lower, upper)
    tolerance = 1e-4
    if any(abs(value) > tolerance for value in metrics.values()):
        raise ValueError(f"plain-butt fallback failed exact reconstruction proof: {metrics}")
    return {
        "mating_feature_kind": "plain_butt_fallback",
        "realized_key_count": 0,
        "fit_class_clearance_mm": clearance_mm,
        "fit_clearance_x_mm": 0.0,
        "fit_clearance_y_mm": 0.0,
        "fit_clearance_z_mm": 0.0,
        "boss_added_volume_mm3": 0.0,
        "pocket_removed_volume_mm3": 0.0,
        "witness_added_volume_mm3": 0.0,
        "witness_protrusion_mm": 0.0,
        "retention_authority": (
            "surrounding installed capture only; no seam-local key or fastener; "
            "Gate 2 dry-fit evidence required"
        ),
        **metrics,
        "fallback_reason": reason,
    }


def _clip_workplane_to_y_range(
    model: cq.Workplane,
    *,
    y_min: float,
    y_max: float,
) -> cq.Workplane:
    bbox = model.val().BoundingBox()
    pad = 1.0
    mask = (
        cq.Workplane("XY")
        .box(
            float(bbox.xlen) + 2 * pad,
            y_max - y_min,
            float(bbox.zlen) + 2 * pad,
            centered=(False, False, False),
        )
        .translate(
            (
                float(bbox.xmin) - pad,
                y_min,
                float(bbox.zmin) - pad,
            )
        )
    )
    return model.intersect(mask)


def _keyed_split_pair(
    model: cq.Workplane,
    *,
    source_y_min: float,
    source_y_max: float,
    split_y: float,
    interface: dict[str, Any],
) -> tuple[cq.Workplane, cq.Workplane, dict[str, Any]]:
    functional_exclusions = _validate_functional_exclusion_contract(interface)
    lower_base = _clip_workplane_to_y_range(
        model,
        y_min=source_y_min,
        y_max=split_y,
    )
    upper_base = _clip_workplane_to_y_range(
        model,
        y_min=split_y,
        y_max=source_y_max,
    )

    src_bb = model.val().BoundingBox()
    src_zmin = float(src_bb.zmin)
    src_zlen = float(src_bb.zlen)
    src_zmax = float(src_bb.zmax)
    src_xmin = float(src_bb.xmin)
    src_xlen = float(src_bb.xlen)
    clr = float(interface.get("fit_class_clearance_mm", 0.2))
    half_span = float(interface.get("key_half_span_y", 3.0))
    narrow_x = float(interface.get("key_narrow_x", 6.0))
    wide_x = float(interface.get("key_wide_x", 10.0))
    key_depth = float(interface.get("key_depth_mm", 4.0))
    min_wall = float(interface.get("key_min_wall_mm", 0.8))
    n_cand = int(interface.get("key_candidate_count", 9))
    min_overlap = float(interface.get("key_min_overlap_frac", 0.3))
    fallback_reason = "source is too thin for the configured keyed interface"
    if src_zlen < key_depth + 2 * min_wall:
        return (
            lower_base,
            upper_base,
            _butt_fallback_proof(
                model,
                lower_base,
                upper_base,
                clearance_mm=clr,
                reason=fallback_reason,
            ),
        )
    configured_z_from_min = interface.get("key_z_from_source_min_mm")
    z0 = (
        src_zmin + float(configured_z_from_min)
        if configured_z_from_min is not None
        else src_zmin + (src_zlen - key_depth) / 2.0
    )
    if z0 < src_zmin or z0 + key_depth > src_zmax:
        return (
            lower_base,
            upper_base,
            _butt_fallback_proof(
                model,
                lower_base,
                upper_base,
                clearance_mm=clr,
                reason="configured key Z range lies outside the source envelope",
            ),
        )

    def _dovetail(
        xc: float,
        nx: float,
        wx: float,
        depth: float,
        z_base: float,
        y_half_span: float = half_span,
    ) -> cq.Workplane:
        pts = [
            (xc - nx / 2, split_y - y_half_span),
            (xc + nx / 2, split_y - y_half_span),
            (xc + wx / 2, split_y + y_half_span),
            (xc - wx / 2, split_y + y_half_span),
        ]
        return cq.Workplane("XY").polyline(pts).close().extrude(depth).translate((0, 0, z_base))

    boss_ref_vol = float(_dovetail(0.0, narrow_x, wide_x, key_depth, z0).val().Volume())
    spacing = wide_x + 2.0
    placements: list[float] = []
    keyed_lower = lower_base
    pocketed_upper = upper_base
    configured_positions = interface.get("key_x_positions_mm")
    candidate_positions = (
        tuple(float(value) for value in configured_positions)
        if configured_positions is not None
        else tuple(src_xmin + (i + 0.5) / n_cand * src_xlen for i in range(n_cand))
    )
    for xc in candidate_positions:
        if any(abs(xc - px) < spacing for px in placements):
            continue
        # The tongue is existing source material transferred across the seam,
        # never a bounding-box boss invented inside a functional void.
        boss = model.intersect(_dovetail(xc, narrow_x, wide_x, key_depth, z0))
        overlap = lower_base.intersect(boss).val()
        if overlap.Solids() and float(overlap.Volume()) >= min_overlap * boss_ref_vol:
            lower_candidate = keyed_lower.union(boss)
            lower_value = lower_candidate.val()
            pocket = _dovetail(
                xc,
                narrow_x + 2 * clr,
                wide_x + 2 * clr,
                key_depth + 2 * clr,
                z0 - clr,
                half_span + clr,
            )
            boss_outside_pocket = _workplane_volume(boss.cut(pocket))
            if boss_outside_pocket > 1e-4:
                continue
            upper_candidate = pocketed_upper.cut(pocket)
            upper_value = upper_candidate.val()
            if (
                len(lower_value.Solids()) != 1
                or float(lower_value.Volume()) <= 0.0
                or len(upper_value.Solids()) != 1
                or float(upper_value.Volume()) <= 0.0
            ):
                continue
            placements.append(xc)
            keyed_lower = lower_candidate
            pocketed_upper = upper_candidate
    if not placements:
        return (
            lower_base,
            upper_base,
            _butt_fallback_proof(
                model,
                lower_base,
                upper_base,
                clearance_mm=clr,
                reason="no connected seam material accepted a keyed candidate",
            ),
        )

    boss_added = float(keyed_lower.val().Volume()) - float(lower_base.val().Volume())
    pocket_removed = float(upper_base.val().Volume()) - float(pocketed_upper.val().Volume())
    if pocket_removed <= boss_added:
        return (
            lower_base,
            upper_base,
            _butt_fallback_proof(
                model,
                lower_base,
                upper_base,
                clearance_mm=clr,
                reason="realized pocket did not preserve positive fit clearance",
            ),
        )

    metrics = _reconstruction_metrics(model, keyed_lower, pocketed_upper)
    tolerance = 1e-4
    if metrics["pair_interference_volume_mm3"] > tolerance:
        raise ValueError(
            "keyed split pair failed collision-free mating proof: "
            f"{metrics['pair_interference_volume_mm3']} mm^3 interference"
        )
    _enforce_reconstruction_limits(model, metrics, interface)
    return (
        keyed_lower,
        pocketed_upper,
        {
            "mating_feature_kind": str(
                interface.get("mating_feature_kind", "printed_dovetail_key_and_pocket")
            ),
            "realized_key_count": len(placements),
            "fit_class_clearance_mm": clr,
            "fit_clearance_x_mm": clr,
            "fit_clearance_y_mm": clr,
            "fit_clearance_z_mm": clr,
            "boss_added_volume_mm3": round(boss_added, 6),
            "pocket_removed_volume_mm3": round(pocket_removed, 6),
            "witness_added_volume_mm3": 0.0,
            "witness_protrusion_mm": 0.0,
            "geometric_split_y_mm": split_y,
            "functional_exclusions": functional_exclusions,
            "functional_exclusions_enforced_by": "source_intersection_and_canonical_allowlist",
            "max_missing_fraction": float(interface.get("max_missing_fraction", 0.01)),
            "max_missing_volume_mm3": float(
                interface.get("max_missing_volume_mm3", 25.0)
            ),
            "max_excess_volume_mm3": float(interface.get("max_excess_volume_mm3", 1e-4)),
            "retention_authority": (
                "printed dovetail keys plus surrounding installed capture; "
                "Gate 2 dry-fit evidence required"
            ),
            **metrics,
            "fallback_reason": None,
        },
    )


def _planar_finger_split_pair(
    model: cq.Workplane,
    *,
    source_y_min: float,
    source_y_max: float,
    split_y: float,
    interface: dict[str, Any],
) -> tuple[cq.Workplane, cq.Workplane, dict[str, Any]]:
    """Partition thin covers with full-thickness, source-local XY fingers."""

    functional_exclusions = _validate_functional_exclusion_contract(interface)
    lower_base = _clip_workplane_to_y_range(model, y_min=source_y_min, y_max=split_y)
    upper_base = _clip_workplane_to_y_range(model, y_min=split_y, y_max=source_y_max)
    bb = model.val().BoundingBox()
    clr = float(interface.get("fit_class_clearance_mm", 0.15))
    finger_length = float(interface.get("finger_length_y_mm", 4.0))
    finger_width = float(interface.get("finger_width_x_mm", 3.0))
    centers = tuple(float(value) for value in interface.get("finger_x_positions_mm", ()))
    if not centers:
        centers = (float(bb.xmin) + float(bb.xlen) / 2.0,)
    if clr <= 0 or finger_length <= 2 * clr or finger_width <= 2 * clr:
        raise ValueError("planar finger dimensions must exceed twice the fit clearance")

    pad_z = 0.5

    def _box(xc: float, *, expanded: bool) -> cq.Workplane:
        grow = clr if expanded else 0.0
        return (
            cq.Workplane("XY")
            .box(
                finger_width + 2 * grow,
                finger_length + grow,
                float(bb.zlen) + 2 * pad_z,
                centered=(False, False, False),
            )
            .translate(
                (
                    xc - finger_width / 2.0 - grow,
                    split_y - (grow if expanded else 0.0),
                    float(bb.zmin) - pad_z,
                )
            )
        )

    lower = lower_base
    upper = upper_base
    realized = 0
    for xc in centers:
        tongue = model.intersect(_box(xc, expanded=False))
        tongue_volume = _workplane_volume(tongue)
        if tongue_volume <= 1e-4:
            continue
        lower_candidate = lower.union(tongue)
        upper_candidate = upper.cut(model.intersect(_box(xc, expanded=True)))
        if len(lower_candidate.val().Solids()) != 1 or len(upper_candidate.val().Solids()) != 1:
            continue
        lower, upper = lower_candidate, upper_candidate
        realized += 1
    if not realized:
        raise ValueError("no connected source-local planar finger could be realized")

    metrics = _reconstruction_metrics(model, lower, upper)
    if metrics["pair_interference_volume_mm3"] > 1e-4:
        raise ValueError("planar finger pair has positive-volume interference")
    _enforce_reconstruction_limits(model, metrics, interface)
    removed = float(upper_base.val().Volume()) - float(upper.val().Volume())
    added = float(lower.val().Volume()) - float(lower_base.val().Volume())
    return (
        lower,
        upper,
        {
            "mating_feature_kind": str(
                interface.get("mating_feature_kind", "printed_full_thickness_planar_finger")
            ),
            "realized_key_count": realized,
            "fit_class_clearance_mm": clr,
            "fit_clearance_x_mm": clr,
            "fit_clearance_y_mm": clr,
            "fit_clearance_z_mm": 0.0,
            "boss_added_volume_mm3": round(added, 6),
            "pocket_removed_volume_mm3": round(removed, 6),
            "witness_added_volume_mm3": 0.0,
            "witness_protrusion_mm": 0.0,
            "finger_length_y_mm": finger_length,
            "finger_width_x_mm": finger_width,
            "geometric_split_y_mm": split_y,
            "functional_exclusions": functional_exclusions,
            "functional_exclusions_enforced_by": "source_intersection_and_canonical_allowlist",
            "max_missing_fraction": float(interface.get("max_missing_fraction", 0.01)),
            "max_missing_volume_mm3": float(
                interface.get("max_missing_volume_mm3", 25.0)
            ),
            "max_excess_volume_mm3": float(interface.get("max_excess_volume_mm3", 1e-4)),
            "retention_authority": (
                "full-thickness planar fingers plus surrounding installed capture; "
                "Gate 2 dry-fit evidence required"
            ),
            **metrics,
            "fallback_reason": None,
        },
    )


def _stepped_lap_split_pair(
    model: cq.Workplane,
    *,
    source_y_min: float,
    source_y_max: float,
    split_y: float,
    interface: dict[str, Any],
) -> tuple[cq.Workplane, cq.Workplane, dict[str, Any]]:
    """Create a shallow source-material lap for thin or sparse seam sections.

    The tongue is the source itself inside a declared Y/Z seam window.  The
    receiving half removes a slightly larger source-local window, so the joint
    never invents a tall boss from the source-wide bounding box.  This is the
    appropriate construction for sub-millimetre harness covers and sparse wet
    rails where a generic Z dovetail would be structurally dishonest.
    """

    functional_exclusions = _validate_functional_exclusion_contract(interface)
    lower_base = _clip_workplane_to_y_range(
        model,
        y_min=source_y_min,
        y_max=split_y,
    )
    upper_base = _clip_workplane_to_y_range(
        model,
        y_min=split_y,
        y_max=source_y_max,
    )
    src_bb = model.val().BoundingBox()
    clr = float(interface.get("fit_class_clearance_mm", 0.2))
    lap_length = float(interface.get("lap_length_y_mm", 4.0))
    lap_depth = float(interface.get("lap_depth_z_mm", 0.25))
    z0 = float(src_bb.zmin) + float(interface.get("lap_z_from_source_min_mm", 0.1))
    if lap_length <= clr or lap_depth <= clr:
        raise ValueError("stepped lap dimensions must exceed fit clearance")
    if z0 < float(src_bb.zmin) or z0 + lap_depth > float(src_bb.zmax):
        raise ValueError("stepped lap Z window lies outside the source envelope")

    pad_x = 1.0

    def _window(*, y0: float, y1: float, z_min: float, z_depth: float) -> cq.Workplane:
        return (
            cq.Workplane("XY")
            .box(
                float(src_bb.xlen) + 2 * pad_x,
                y1 - y0,
                z_depth,
                centered=(False, False, False),
            )
            .translate((float(src_bb.xmin) - pad_x, y0, z_min))
        )

    tongue = model.intersect(
        _window(
            y0=split_y,
            y1=split_y + lap_length,
            z_min=z0,
            z_depth=lap_depth,
        )
    )
    tongue_volume = _workplane_volume(tongue)
    if tongue_volume <= 1e-4:
        raise ValueError("stepped lap window contains no source-local seam material")

    pocket = model.intersect(
        _window(
            y0=split_y - clr,
            y1=split_y + lap_length + clr,
            z_min=z0 - clr,
            z_depth=lap_depth + 2 * clr,
        )
    )
    lapped_lower = lower_base.union(tongue)
    pocketed_upper = upper_base.cut(pocket)
    lower_value = lapped_lower.val()
    upper_value = pocketed_upper.val()
    if len(lower_value.Solids()) != 1 or len(upper_value.Solids()) != 1:
        raise ValueError("stepped lap did not preserve connected halves")

    tongue_added = float(lower_value.Volume()) - float(lower_base.val().Volume())
    pocket_removed = float(upper_base.val().Volume()) - float(upper_value.Volume())
    if tongue_added <= 1e-4 or pocket_removed <= tongue_added + 1e-4:
        raise ValueError("stepped lap did not realize positive source-local clearance")
    metrics = _reconstruction_metrics(model, lapped_lower, pocketed_upper)
    if metrics["pair_interference_volume_mm3"] > 1e-4:
        raise ValueError("stepped lap pair has positive-volume interference")
    _enforce_reconstruction_limits(model, metrics, interface)

    return (
        lapped_lower,
        pocketed_upper,
        {
            "mating_feature_kind": str(
                interface.get("mating_feature_kind", "printed_stepped_lap_and_pocket")
            ),
            "realized_key_count": len(tongue.val().Solids()),
            "fit_class_clearance_mm": clr,
            "fit_clearance_x_mm": 0.0,
            "fit_clearance_y_mm": clr,
            "fit_clearance_z_mm": clr,
            "boss_added_volume_mm3": round(tongue_added, 6),
            "pocket_removed_volume_mm3": round(pocket_removed, 6),
            "witness_added_volume_mm3": 0.0,
            "witness_protrusion_mm": 0.0,
            "lap_length_y_mm": lap_length,
            "lap_depth_z_mm": lap_depth,
            "geometric_split_y_mm": split_y,
            "functional_exclusions": functional_exclusions,
            "functional_exclusions_enforced_by": "source_intersection_and_canonical_allowlist",
            "max_missing_fraction": float(interface.get("max_missing_fraction", 0.01)),
            "max_missing_volume_mm3": float(
                interface.get("max_missing_volume_mm3", 25.0)
            ),
            "max_excess_volume_mm3": float(interface.get("max_excess_volume_mm3", 1e-4)),
            "retention_authority": (
                "printed stepped lap plus surrounding installed capture; "
                "Gate 2 dry-fit evidence required"
            ),
            **metrics,
            "fallback_reason": None,
        },
    )


def _part_fits_selected_bed(
    target_x_mm: float,
    target_y_mm: float,
    bed_x_mm: float,
    bed_y_mm: float,
) -> bool:
    from aevum_cad.row_coupon_first_print.bed_fit import _part_fits_rectangular_bed

    return _part_fits_rectangular_bed(
        target_x_mm=target_x_mm,
        target_y_mm=target_y_mm,
        bed_x_mm=bed_x_mm,
        bed_y_mm=bed_y_mm,
    )


def _split_y_from_tile_origins(
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
) -> float:
    ordered = sorted(tile_origins, key=lambda tile: float(tile["y"]))
    if len(ordered) < 2:
        raise ValueError("final print-piece split requires at least two plate tiles")
    split_after = len(ordered) // 2
    lower_tile = ordered[split_after - 1]
    upper_tile = ordered[split_after]
    return round(
        (float(lower_tile["y"]) + float(params["plate"]["width_y"]) + float(upper_tile["y"])) / 2,
        3,
    )


def _two_module_joint_metadata(
    *,
    params: dict[str, Any],
    split_y: float,
    lower_tile: dict[str, Any],
    upper_tile: dict[str, Any],
) -> dict[str, Any]:
    production = params.get("production_assembly", {})
    interface = production.get("final_piece_interface", {}) or {}
    return {
        "joint_id": f"two_module_joint_{lower_tile['index']}_{upper_tile['index']}",
        "split_y": split_y,
        "module_boundary": "inter-plate service gap",
        "mating_feature_kind": str(
            interface.get("mating_feature_kind", "printed_dovetail_key_and_pocket")
        ),
        "key_half_span_y": float(interface.get("key_half_span_y", 3.0)),
        "retention_authority": (
            "printed dovetail key, wedge locks, and printed witness features only"
        ),
    }


def _final_print_piece_segments(params: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    layout = row_coupon_layout(params)
    if layout["row_axis"] != "y":
        raise ValueError("final print-piece split requires a row configured on the Y axis")
    tile_origins = sorted(layout["tile_origins"], key=lambda tile: float(tile["y"]))
    if len(tile_origins) < 2:
        raise ValueError("final print-piece split requires at least two plate tiles")
    split_after = len(tile_origins) // 2
    lower_tile = tile_origins[split_after - 1]
    upper_tile = tile_origins[split_after]
    split_y = _split_y_from_tile_origins(tile_origins, params)
    segments: list[dict[str, Any]] = [
        {
            "piece_index": 1,
            "piece_count": 2,
            "suffix": f"piece_01_of_02_y_000p000_to_{split_y:.3f}".replace(
                ".",
                "p",
            ),
            "axis": "y",
            "range_min_mm": 0.0,
            "range_max_mm": split_y,
            "interface_zone": f"between_plate_{lower_tile['index']}_and_{upper_tile['index']}",
        },
        {
            "piece_index": 2,
            "piece_count": 2,
            "suffix": "piece_02_of_02_y_{:.3f}_to_{:.3f}".format(
                split_y,
                float(layout["width_y"]),
            ).replace(".", "p"),
            "axis": "y",
            "range_min_mm": split_y,
            "range_max_mm": float(layout["width_y"]),
            "interface_zone": f"between_plate_{lower_tile['index']}_and_{upper_tile['index']}",
        },
    ]
    joint = _two_module_joint_metadata(
        params=params,
        split_y=split_y,
        lower_tile=lower_tile,
        upper_tile=upper_tile,
    )
    segments[0]["seam"] = {**joint, "joint_role": "lower module"}
    segments[1]["seam"] = {**joint, "joint_role": "upper module"}
    return tuple(segments)


def _piece_diagnostics(
    *,
    name: str,
    model: cq.Workplane,
    bed_x_mm: float,
    bed_y_mm: float,
) -> tuple[str, ...]:
    value = model.val()
    solids = value.Solids()
    bb = value.BoundingBox()
    issues: list[str] = []
    if len(solids) != 1:
        issues.append(f"expected one connected solid, found {len(solids)}")
    if float(value.Volume()) <= 0.0:
        issues.append("piece volume is nonpositive")
    if float(bb.xlen) <= 0.0 or float(bb.ylen) <= 0.0 or float(bb.zlen) <= 0.0:
        issues.append("piece bounding box is nonpositive")
    if not _part_fits_selected_bed(
        float(bb.xlen),
        float(bb.ylen),
        bed_x_mm,
        bed_y_mm,
    ):
        issues.append(f"piece does not fit selected bed: {name}")
    return tuple(issues)


def _validated_installed_translation(
    *,
    source: str,
    fabrication_model: cq.Workplane,
    installed_model: cq.Workplane,
) -> tuple[float, float, float]:
    """Return the print-to-install placement without changing release geometry.

    The fabrication artifact is the shape authority.  Installed builders are
    used only for placement because owner-relative cuts can otherwise rebuild a
    materially different shape in assembly coordinates.
    """

    fabrication_value = fabrication_model.val()
    installed_value = installed_model.val()
    fabrication_bbox = fabrication_value.BoundingBox()
    installed_bbox = installed_value.BoundingBox()
    # Row-coupon fabrication artifacts retain global assembly X/Y and normalize
    # only Z.  Some legacy installed builders make owner-relative cuts that can
    # change their X/Y envelope; those shapes are deliberately not authority for
    # the final printed body.  Equal Z thickness is sufficient to recover the
    # placement while preserving the fabrication artifact byte-for-byte in X/Y.
    if abs(float(fabrication_bbox.zlen - installed_bbox.zlen)) > 1e-6:
        raise ValueError(
            f"physical artifact {source} has no unambiguous installed Z placement"
        )
    return (0.0, 0.0, float(installed_bbox.zmin - fabrication_bbox.zmin))


def _realize_row_coupon_final_print_pieces(
    params: dict[str, Any],
    *,
    bed_x_mm: float = DEFAULT_FIRST_PRINT_BED_X_MM,
    bed_y_mm: float = DEFAULT_FIRST_PRINT_BED_Y_MM,
    assembly_position: bool = False,
) -> tuple[tuple[dict[str, Any], ...], dict[str, cq.Workplane]]:
    source_params = params
    # Seam construction is authoritative in fabrication coordinates.  Splitting
    # an already installed source can move source-local seam/exclusion logic and
    # silently choose a different joint.  Validate and apply the source's rigid
    # installed transform only after the exact release bodies have been made.
    models = build_row_coupon_physical_artifacts(
        source_params,
        assembly_position=False,
    )
    installed_models = (
        build_row_coupon_physical_artifacts(source_params, assembly_position=True)
        if assembly_position
        else {}
    )
    installed_translations: dict[str, tuple[float, float, float]] = {}

    def output_model(source: str, model: cq.Workplane) -> cq.Workplane:
        if not assembly_position:
            return model
        if source not in installed_translations:
            installed_translations[source] = _validated_installed_translation(
                source=source,
                fabrication_model=models[source],
                installed_model=installed_models[source],
            )
        return model.translate(installed_translations[source])

    manifest = row_coupon_physical_artifact_manifest(source_params)

    policies = row_coupon_physical_artifact_print_policies(
        source_params,
        bed_x_mm=bed_x_mm,
        bed_y_mm=bed_y_mm,
        fits_rectangular_bed=_part_fits_selected_bed,
    )
    rows: list[dict[str, Any]] = []
    pieces: dict[str, cq.Workplane] = {}
    for policy in policies:
        if policy.policy == "nonprinted_or_flexible":
            continue

        source = policy.name
        model = models[source]
        entry = manifest[source]
        if policy.policy == "bed_fit_identity":
            piece_name = source
            piece_model = output_model(source, model)
            diagnostics = _piece_diagnostics(
                name=piece_name,
                model=piece_model,
                bed_x_mm=bed_x_mm,
                bed_y_mm=bed_y_mm,
            )
            row = {
                "name": piece_name,
                "source_artifact": source,
                "source_part": source,
                "installed_part": policy.installed_part,
                "piece_index": 1,
                "piece_count": 1,
                "axis": "identity",
                "range_min_mm": None,
                "range_max_mm": None,
                "policy": policy.policy,
                "action": "identity",
                "target_x_mm": policy.target_x_mm,
                "target_y_mm": policy.target_y_mm,
                "target_z_mm": policy.target_z_mm,
                "selected_bed_x_mm": bed_x_mm,
                "selected_bed_y_mm": bed_y_mm,
                "fits_selected_bed": not any("selected bed" in issue for issue in diagnostics),
                "provenance": f"canonical physical artifact: {source}",
                "role": entry["role"],
                "diagnostics": diagnostics,
            }
            rows.append(row)
            pieces[piece_name] = piece_model
            continue

        if policy.policy == "structural_split_allowed":
            production = params.get("production_assembly", {})
            base_interface = production.get("final_piece_interface", {}) or {}
            source_overrides = base_interface.get("source_overrides", {}) or {}
            interface = {
                **base_interface,
                **(source_overrides.get(source, {}) or {}),
                "canonical_source_artifact": source,
            }
            interface.pop("source_overrides", None)
            segments = _final_print_piece_segments(source_params)
            nominal_split_y = float(segments[0]["range_max_mm"])
            split_y = float(interface.get("split_y_mm", nominal_split_y))
            strategy = str(interface.get("joint_strategy", "keyed"))
            split_builder = {
                "keyed": _keyed_split_pair,
                "stepped_lap": _stepped_lap_split_pair,
                "planar_finger": _planar_finger_split_pair,
            }.get(strategy)
            if split_builder is None:
                raise ValueError(f"unsupported final-piece joint strategy: {strategy}")
            try:
                lower_piece, upper_piece, seam_proof = split_builder(
                    model,
                    source_y_min=float(segments[0]["range_min_mm"]),
                    source_y_max=float(segments[-1]["range_max_mm"]),
                    split_y=split_y,
                    interface=interface,
                )
            except ValueError as exc:
                raise ValueError(
                    f"final print-piece split failed for {source}: {exc}"
                ) from exc
            if seam_proof["mating_feature_kind"] == "plain_butt_fallback":
                raise ValueError(
                    f"canonical split source {source} has no seam-local retention: "
                    f"{seam_proof['fallback_reason']}"
                )
            piece_models = (
                output_model(source, lower_piece),
                output_model(source, upper_piece),
            )
            for segment in segments:
                piece_name = f"{source}_{segment['suffix']}"
                piece_model = piece_models[int(segment["piece_index"]) - 1]
                bb = piece_model.val().BoundingBox()
                diagnostics = _piece_diagnostics(
                    name=piece_name,
                    model=piece_model,
                    bed_x_mm=bed_x_mm,
                    bed_y_mm=bed_y_mm,
                )
                row = {
                    "name": piece_name,
                    "source_artifact": source,
                    "source_part": source,
                    "installed_part": policy.installed_part,
                    "piece_index": segment["piece_index"],
                    "piece_count": segment["piece_count"],
                    "axis": segment["axis"],
                    "range_semantics": "stable_nominal_identity_only",
                    "range_min_mm": segment["range_min_mm"],
                    "range_max_mm": segment["range_max_mm"],
                    "nominal_id_range_min_mm": segment["range_min_mm"],
                    "nominal_id_range_max_mm": segment["range_max_mm"],
                    "geometric_y_min_mm": round(float(bb.ymin), 6),
                    "geometric_y_max_mm": round(float(bb.ymax), 6),
                    "interface_zone": segment["interface_zone"],
                    "seam": {**segment.get("seam", {}), **seam_proof},
                    "policy": policy.policy,
                    "action": "structural_split",
                    "target_x_mm": round(float(bb.xlen), 2),
                    "target_y_mm": round(float(bb.ylen), 2),
                    "target_z_mm": round(float(bb.zlen), 2),
                    "selected_bed_x_mm": bed_x_mm,
                    "selected_bed_y_mm": bed_y_mm,
                    "fits_selected_bed": not any("selected bed" in issue for issue in diagnostics),
                    "provenance": f"canonical physical artifact: {source}",
                    "role": entry["role"],
                    "diagnostics": diagnostics,
                    "required_evidence": (
                        "Gate 1 dimensions, Gate 2 dry assembly, Gate 4 wet/dry "
                        "witness, and selected-slicer bed-fit evidence"
                    ),
                }
                rows.append(row)
                pieces[piece_name] = piece_model
            continue

        rows.append(
            {
                "name": source,
                "source_artifact": source,
                "source_part": source,
                "installed_part": policy.installed_part,
                "piece_index": 0,
                "piece_count": 0,
                "axis": "blocked",
                "range_min_mm": None,
                "range_max_mm": None,
                "policy": policy.policy,
                "action": "blocked",
                "target_x_mm": policy.target_x_mm,
                "target_y_mm": policy.target_y_mm,
                "target_z_mm": policy.target_z_mm,
                "selected_bed_x_mm": bed_x_mm,
                "selected_bed_y_mm": bed_y_mm,
                "fits_selected_bed": False,
                "provenance": f"canonical physical artifact: {source}",
                "role": entry["role"],
                "diagnostics": (policy.reason,),
            }
        )

    name_counts = Counter(str(row["name"]) for row in rows)
    duplicates = tuple(name for name, count in name_counts.items() if count > 1)
    if duplicates:
        raise ValueError("duplicate final print-piece names in generated plan")
    return tuple(rows), pieces


def realize_row_coupon_final_print_pieces(
    params: dict[str, Any],
    *,
    bed_x_mm: float = DEFAULT_FIRST_PRINT_BED_X_MM,
    bed_y_mm: float = DEFAULT_FIRST_PRINT_BED_Y_MM,
    assembly_position: bool = False,
) -> RowCouponFinalPrintRealization:
    """Realize plan and geometry together so metadata cannot drift from bodies.

    ``assembly_position=False`` is the fabrication-coordinate authority used by
    exports.  Set it to true when the exact final release bodies, including all
    retained split interfaces, must be audited in their installed coordinates.
    """

    plan, pieces = _realize_row_coupon_final_print_pieces(
        params,
        bed_x_mm=bed_x_mm,
        bed_y_mm=bed_y_mm,
        assembly_position=assembly_position,
    )
    return RowCouponFinalPrintRealization(
        plan=plan,
        pieces=MappingProxyType(pieces),
        assembly_position=assembly_position,
    )


def group_row_coupon_final_print_pieces_by_installed_part(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
    bed_x_mm: float = DEFAULT_FIRST_PRINT_BED_X_MM,
    bed_y_mm: float = DEFAULT_FIRST_PRINT_BED_Y_MM,
) -> dict[str, cq.Workplane]:
    """Group every exact rigid release body under its installed-family authority."""

    realization = realize_row_coupon_final_print_pieces(
        params,
        bed_x_mm=bed_x_mm,
        bed_y_mm=bed_y_mm,
        assembly_position=assembly_position,
    )
    realization.require_printable()
    rows_by_name = {str(row["name"]): row for row in realization.plan}
    if len(rows_by_name) != len(realization.plan) or set(rows_by_name) != set(
        realization.pieces
    ):
        raise ValueError("final release-body plan does not map one-to-one to geometry")

    manifest = row_coupon_physical_artifact_manifest(params)
    rigid_sources = {
        source
        for source, entry in manifest.items()
        if entry["fabrication_source"] == "printed_polymer"
    }
    realized_sources = {str(row["source_artifact"]) for row in realization.plan}
    if realized_sources != rigid_sources:
        raise ValueError(
            "final release-body source authority mismatch: "
            f"missing={sorted(rigid_sources - realized_sources)}, "
            f"extra={sorted(realized_sources - rigid_sources)}"
        )

    grouped_models: dict[str, list[cq.Workplane]] = {}
    for release_body_id, model in realization.pieces.items():
        row = rows_by_name[release_body_id]
        source = str(row["source_artifact"])
        installed_part = str(row["installed_part"])
        if installed_part != str(manifest[source]["installed_part"]):
            raise ValueError(
                f"installed-family authority mismatch for {release_body_id}: "
                f"{installed_part} != {manifest[source]['installed_part']}"
            )
        grouped_models.setdefault(installed_part, []).append(model)

    grouped: dict[str, cq.Workplane] = {}
    for installed_part, models in grouped_models.items():
        if len(models) == 1:
            grouped[installed_part] = models[0]
            continue
        solids = [solid for model in models for solid in model.val().Solids()]
        grouped[installed_part] = cq.Workplane(
            obj=cq.Compound.makeCompound(solids)
        )
    return grouped


def row_coupon_final_print_piece_plan(
    params: dict[str, Any],
    *,
    bed_x_mm: float = DEFAULT_FIRST_PRINT_BED_X_MM,
    bed_y_mm: float = DEFAULT_FIRST_PRINT_BED_Y_MM,
) -> tuple[dict[str, Any], ...]:
    realization = realize_row_coupon_final_print_pieces(
        params,
        bed_x_mm=bed_x_mm,
        bed_y_mm=bed_y_mm,
    )
    return realization.plan


def build_row_coupon_final_print_pieces(
    params: dict[str, Any],
    *,
    bed_x_mm: float = DEFAULT_FIRST_PRINT_BED_X_MM,
    bed_y_mm: float = DEFAULT_FIRST_PRINT_BED_Y_MM,
) -> dict[str, cq.Workplane]:
    realization = realize_row_coupon_final_print_pieces(
        params,
        bed_x_mm=bed_x_mm,
        bed_y_mm=bed_y_mm,
    )
    realization.require_printable()
    return dict(realization.pieces)


def export_row_coupon_final_print_pieces(
    params: dict[str, Any],
    out_dir: str | Path,
    *,
    bed_x_mm: float = DEFAULT_FIRST_PRINT_BED_X_MM,
    bed_y_mm: float = DEFAULT_FIRST_PRINT_BED_Y_MM,
) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    realization = realize_row_coupon_final_print_pieces(
        params,
        bed_x_mm=bed_x_mm,
        bed_y_mm=bed_y_mm,
    )
    realization.require_printable()
    paths: dict[str, Path] = {}
    for name, model in realization.pieces.items():
        stl_path = out / f"{params['name']}_{name}.stl"
        step_path = out / f"{params['name']}_{name}.step"
        cq.exporters.export(model, str(stl_path))
        cq.exporters.export(model, str(step_path))
        paths[f"{name}_stl"] = stl_path
        paths[f"{name}_step"] = step_path
    return paths
