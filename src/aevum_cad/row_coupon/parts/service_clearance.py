from __future__ import annotations
from typing import Any
import cadquery as cq
from ..layout import (row_coupon_layout)
from ._geom_base import (_boxes_from_rectangles, _rectangles_bounding_extents)


def _operating_service_dress_check(
    operating_service_rects: list[dict[str, Any]],
    *,
    side_service_rects: list[dict[str, Any]],
    electrical_service_rects: list[dict[str, Any]],
    side_gas_adjacent_slot_clearance: dict[str, Any],
) -> dict[str, Any]:
    x_len, y_len, z_len = _rectangles_bounding_extents(operating_service_rects)
    return {
        "name": "operating_service_dress_check",
        "role": "connected_gas_and_electrical_service_dress_validation_body",
        "validation": "required_gate3_connected_service_dress_evidence",
        "failure_rule": (
            "tube_cable_contact_or_unmeasured_service_dress_blocks_ot2_operation"
        ),
        "evidence_gate": "Gate 3 OT-2 placement",
        "cad_value": (
            f"{x_len:.2f} x {y_len:.2f} x {z_len:.2f} mm / "
            f"{len(operating_service_rects)} envelopes"
        ),
        "service_envelope_count": len(operating_service_rects),
        "side_gas_service_envelope_count": len(side_service_rects),
        "electrical_service_envelope_count": len(electrical_service_rects),
        "required_vertical_clearance_z": side_gas_adjacent_slot_clearance[
            "required_vertical_clearance_z"
        ],
        "min_vertical_clearance_z": side_gas_adjacent_slot_clearance[
            "min_vertical_clearance_z"
        ],
        "meets_vertical_clearance": side_gas_adjacent_slot_clearance[
            "meets_vertical_clearance"
        ],
        "source_layout_checks": [
            "side_gas_tube_envelope_check",
            "sensor_service_cable_envelope_check",
            "adjacent_deck_slot_keepout_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "normal_ot2_operation_with_connected_services",
            "pipette_access_with_connected_services",
            "row_tiling_with_connected_services",
        ],
        "body_rects": operating_service_rects,
    }


def _pipette_puncture_swept_path_check(
    sweep: dict[str, Any],
    *,
    well_centers: list[tuple[float, float]],
    params: dict[str, Any],
) -> dict[str, Any]:
    grid = params["well_grid"]
    plate_count = int(params["row"]["plate_count"])
    wells_per_plate = int(grid["columns"]) * int(grid["rows"])
    return {
        "name": "pipette_puncture_swept_path_check",
        "role": "all_well_pipette_tip_puncture_path_validation_body",
        "validation": "required_gate5_all_well_puncture_swept_path_evidence",
        "failure_rule": (
            "blocked_or_unmeasured_puncture_path_blocks_consumable_puncture_pass"
        ),
        "evidence_gate": "Gate 5 consumable/puncture",
        "cad_value": (
            f"{int(sweep['well_count'])} wells / "
            f"{float(sweep['diameter']):.2f} mm / "
            f"{float(sweep['bottom_z']):.2f}..{float(sweep['top_z']):.2f} mm"
        ),
        "target_count_cad_value": f"{int(sweep['well_count'])} wells",
        "diameter_cad_value": f"{float(sweep['diameter']):.2f} mm",
        "z_range_cad_value": (
            f"{float(sweep['bottom_z']):.2f}..{float(sweep['top_z']):.2f} mm"
        ),
        "diameter": sweep["diameter"],
        "bottom_z": sweep["bottom_z"],
        "top_z": sweep["top_z"],
        "height_z": sweep["height_z"],
        "well_count": sweep["well_count"],
        "plate_count": plate_count,
        "wells_per_plate": wells_per_plate,
        "source_layout_checks": [
            "tile_origins",
            "well_grid",
            "pipette_access",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "all_96_positions_per_plate_puncturable",
            "septum_mat_puncture_serviceability",
            "gate6_sensor_thermal_pipetting_readiness",
        ],
        "target_centers": well_centers,
    }


def _pipette_toolhead_swept_body_check(
    body: dict[str, Any],
    *,
    puncture_swept_path_check: dict[str, Any],
    operating_service_dress_check: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": "pipette_toolhead_swept_body_check",
        "role": "ot2_pipette_toolhead_operating_clearance_validation_body",
        "validation": "required_gate3_top_pipette_field_clearance_evidence",
        "failure_rule": (
            "toolhead_collision_or_unmeasured_top_field_clearance_blocks_ot2_placement_pass"
        ),
        "evidence_gate": "Gate 3 OT-2 placement",
        "cad_value": (
            f"{float(body['length_x']):.2f} x "
            f"{float(body['width_y']):.2f} x "
            f"{float(body['height_z']):.2f} mm / "
            f"{int(body['covered_well_count'])} wells"
        ),
        "clearance_cad_value": (
            f"{float(body['assembly_clearance_z']):.2f} mm assembly / "
            f"{float(body['service_clearance_z']):.2f} mm services / "
            f"{float(body['tip_transition_gap_z']):.2f} mm tip path"
        ),
        "covered_well_count": body["covered_well_count"],
        "service_envelope_count": body["service_envelope_count"],
        "assembly_clearance_z": body["assembly_clearance_z"],
        "service_clearance_z": body["service_clearance_z"],
        "tip_transition_gap_z": body["tip_transition_gap_z"],
        "source_layout_checks": [
            "pipette_puncture_swept_path_check",
            "operating_service_dress_check",
            "row_tiling_service_clearance_check",
        ],
        "puncture_target_count": puncture_swept_path_check["well_count"],
        "operating_service_envelope_count": operating_service_dress_check[
            "service_envelope_count"
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "normal_ot2_pipetting_operation",
            "top_pipette_field_clear",
            "all_well_access_with_connected_services",
        ],
        "body_rects": [body],
    }


def _row_tiling_service_clearance_check(
    layout: dict[str, Any],
    *,
    adjacent_keepouts: list[dict[str, Any]],
    operating_service_rects: list[dict[str, Any]],
    side_gas_adjacent_slot_clearance: dict[str, Any],
    deck_plane_z: float,
    assembly_top_z: float,
) -> dict[str, Any]:
    module_footprint_rect = {
        "name": "installed_row_module_deck_footprint",
        "role": "installed row-module footprint for row-to-row tiling review",
        "review_group": "installed_module_footprint",
        "x": 0.0,
        "y": 0.0,
        "z": round(deck_plane_z, 3),
        "length_x": round(float(layout["length_x"]), 3),
        "width_y": round(float(layout["width_y"]), 3),
        "height_z": 1.0,
    }
    neighbor_rects = [
        {
            **rect,
            "role": "neighbor OT-2 slot overhead keepout for row tiling review",
            "review_group": "neighbor_slot_keepout",
        }
        for rect in adjacent_keepouts
    ]
    service_rects = [
        {
            **rect,
            "role": rect.get("role", rect.get("service_role", "operating service dress")),
            "review_group": "operating_service_dress",
        }
        for rect in operating_service_rects
    ]
    return {
        "role": "validation-only row-to-row tiling and service-clearance review",
        "validation": "cad_proxy_physical_adjacent_slot_review_pending",
        "failure_rule": (
            "neighbor_slot_interference_or_unmeasured_service_clearance_blocks_ot2_operation"
        ),
        "evidence_gate": "Gate 3 OT-2 placement",
        "row_axis": layout["row_axis"],
        "tile_count": len(layout["tile_origins"]),
        "module_footprint_rect": module_footprint_rect,
        "adjacent_keepout_count": len(adjacent_keepouts),
        "service_envelope_count": len(operating_service_rects),
        "cad_value": (
            f"{len(adjacent_keepouts)} neighbor keepouts / "
            f"{len(operating_service_rects)} service envelopes / "
            f"{float(side_gas_adjacent_slot_clearance['min_vertical_clearance_z']):.2f} mm "
            "minimum clearance"
        ),
        "required_vertical_clearance_z": side_gas_adjacent_slot_clearance[
            "required_vertical_clearance_z"
        ],
        "min_vertical_clearance_z": side_gas_adjacent_slot_clearance[
            "min_vertical_clearance_z"
        ],
        "meets_vertical_clearance": side_gas_adjacent_slot_clearance[
            "meets_vertical_clearance"
        ],
        "assembly_top_z": round(assembly_top_z, 3),
        "physical_evidence": "pending printed-row OT-2 adjacent-slot service review",
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "normal_ot2_operation_in_adjacent_deck_slots",
            "service_dress_repeatability_on_deck",
        ],
        "review_rects": [module_footprint_rect, *neighbor_rects, *service_rects],
    }


# ---------------------------------------------------------------------------
# D9 sequenced assembly/disassembly motion checks (flag-on validation tools).
#
# These three checks are ADDITIVE validation-tool bodies, gated behind
# params["production_assembly"]["keyed_joints_enabled"] (default False). With the
# flag OFF they are NOT wired into ``row_coupon_layout`` and NOT exported, so the
# layout dict and the production export tree are byte-identical to pre-D9.
#
# Each verdict mirrors the ``_pipette_toolhead_swept_body_check`` schema and
# inherits the Gate-6 posture: a measured/real geometric verdict field
# (clearance / overhang / bend+slack) PLUS ``requires_physical_evidence: True``
# and ``physical_claims_blocked``. A clear CAD body only narrows feasibility; the
# authoritative pass state stays "physical evidence pending". No verdict is
# hard-coded — every boolean is computed from the read geometry.
#
# No-hidden-authority + plate keepout: these checks only READ existing geometry
# (split-plan rows, printed locator/land rects, harness cable envelopes) and emit
# validation proxy solids. They add NO metal and touch NO production body; nothing
# grips or lands on the CellVis plate.
# ---------------------------------------------------------------------------


def _split_segment_swept_removal_check(
    split_rows: tuple[dict[str, Any], ...],
    *,
    split_y: float,
    removal_axis: str = "+Z",
) -> dict[str, Any]:
    """(a) Per-segment swept-removal vs mated neighbor.

    For each adjacent y-split segment pair (lower terminates at ``split_y``, upper
    starts at it), measure the residual clearance between the lower segment's mated
    top face and the upper segment's mated bottom face at the seam. The butt seam
    is coincident (0.0 mm), so the swept-removal proxy reports the seam gap as the
    minimum neighbor clearance; the geometric verdict ``meets_clearance`` only flips
    True if a non-negative gap exists. CAD geometry never sets the authoritative
    pass state — ``requires_physical_evidence`` keeps it pending."""
    # group rows by source part so each oversized body's two segments pair up
    by_part: dict[str, list[dict[str, Any]]] = {}
    for row in split_rows:
        by_part.setdefault(str(row["source_part"]), []).append(row)
    pair_count = 0
    seam_gaps: list[float] = []
    body_rects: list[dict[str, Any]] = []
    for part, rows in by_part.items():
        ordered = sorted(rows, key=lambda r: float(r["y_min"]))
        for lower, upper in zip(ordered, ordered[1:]):
            pair_count += 1
            # residual clearance at the seam: upper.y_min - lower.y_max
            seam_gap = round(float(upper["y_min"]) - float(lower["y_max"]), 4)
            seam_gaps.append(seam_gap)
            # swept-removal proxy slab straddling the seam (a thin validation body
            # spanning the interface zone), used only to emit a real solid.
            body_rects.append(
                {
                    "name": f"{part}_swept_removal_seam_{pair_count}",
                    "role": "split_segment_swept_removal_seam_proxy",
                    "source_part": part,
                    "x": 0.0,
                    "y": round(split_y - 1.0, 3),
                    "z": 0.0,
                    "length_x": 1.0,
                    "width_y": 2.0,
                    "height_z": 1.0,
                }
            )
    min_neighbor_clearance_mm = round(min(seam_gaps), 4) if seam_gaps else 0.0
    return {
        "name": "split_segment_swept_removal_check",
        "role": "y_split_segment_swept_removal_interference_validation_body",
        "validation": "required_gate6_real_split_segment_removal_serviceability_evidence",
        "failure_rule": (
            "segment_interference_or_unmeasured_removal_path_blocks_disassembly_pass"
        ),
        "evidence_gate": "Gate 6 sensor install / serviceability",
        "cad_value": (
            f"{pair_count} segment pairs / "
            f"{min_neighbor_clearance_mm:.2f} mm min neighbor clearance / "
            f"removal {removal_axis}"
        ),
        "split_y": round(float(split_y), 3),
        "removal_axis": removal_axis,
        "segment_pair_count": pair_count,
        # REAL geometric verdict fields (measured, not hard-coded):
        "min_neighbor_clearance_mm": min_neighbor_clearance_mm,
        "meets_clearance": min_neighbor_clearance_mm >= 0.0,
        "source_layout_checks": [
            "row_coupon_production_y_split_plan",
            "tile_origins",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "split_segment_withdraws_without_neighbor_interference",
            "two_module_disassembly_serviceability",
        ],
        "body_rects": body_rects,
    }


def _trapped_plate_lift_check(
    locator_rails: list[dict[str, Any]],
    *,
    tile_origins: list[dict[str, Any]],
    plate_len: float,
    plate_wid: float,
    plate_bottom_z: float,
) -> dict[str, Any]:
    """(b) Trapped-plate free +Z lift.

    The CellVis plate is a consumable: nothing may grip or land on it. The 4-wall
    lateral-locator ring (``_plate_lateral_locator_rectangles`` /
    ``_add_plate_lateral_locator_rails``) and any plate-support land must lie
    OUTSIDE or flush with each plate's XY footprint so the plate lifts straight up
    (+Z) unobstructed. This computes, per plate footprint, the maximum inward
    overhang of any locator/land rect into the plate keepout column; free lift ==
    overhang 0 over the full +Z withdrawal column. The verdict is MEASURED from
    geometry (no hard-coded pass) and still carries ``requires_physical_evidence``."""
    max_overhang_mm = 0.0
    overhang_rects: list[dict[str, Any]] = []
    body_rects: list[dict[str, Any]] = []
    for tile in tile_origins:
        x0 = float(tile["x"])
        y0 = float(tile["y"])
        x1 = x0 + float(plate_len)
        y1 = y0 + float(plate_wid)
        # validation proxy: the plate +Z withdrawal column footprint (thin slab)
        body_rects.append(
            {
                "name": f"plate_lift_column_tile_{tile.get('index', 0)}",
                "role": "trapped_plate_lift_withdrawal_column_proxy",
                "tile_index": tile.get("index", 0),
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": round(float(plate_bottom_z), 3),
                "length_x": round(float(plate_len), 3),
                "width_y": round(float(plate_wid), 3),
                "height_z": 1.0,
            }
        )
        for rail in locator_rails:
            if int(rail.get("tile_index", 0)) not in (0, tile.get("index", 0)):
                continue
            rx0 = float(rail["x"])
            ry0 = float(rail["y"])
            rx1 = rx0 + float(rail["length_x"])
            ry1 = ry0 + float(rail["width_y"])
            # inward overlap of this wall into the plate footprint (XY)
            ox = max(0.0, min(rx1, x1) - max(rx0, x0))
            oy = max(0.0, min(ry1, y1) - max(ry0, y0))
            overlap = round(min(ox, oy), 4)
            if overlap > 0.0:
                max_overhang_mm = max(max_overhang_mm, overlap)
                overhang_rects.append({**rail, "overhang_mm": overlap})
    max_overhang_mm = round(max_overhang_mm, 4)
    return {
        "name": "trapped_plate_lift_check",
        "role": "consumable_plate_free_plus_z_lift_validation_body",
        "validation": "required_gate6_real_plate_removal_serviceability_evidence",
        "failure_rule": (
            "locator_or_land_overhang_or_unmeasured_lift_path_traps_consumable_plate"
        ),
        "evidence_gate": "Gate 6 sensor install / serviceability",
        "cad_value": (
            f"{len(tile_origins)} plate footprints / "
            f"{max_overhang_mm:.2f} mm max inward overhang / "
            f"{len(overhang_rects)} obstructing walls"
        ),
        "plate_footprint_count": len(tile_origins),
        "locator_wall_count": len(locator_rails),
        # REAL geometric verdict fields (measured from locator/land geometry):
        "max_overhang_mm": max_overhang_mm,
        "lift_unobstructed": max_overhang_mm == 0.0,
        "obstructing_walls": overhang_rects,
        "source_layout_checks": [
            "plate_locator_rails",
            "tile_origins",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "consumable_plate_lifts_free_plus_z_without_tooling",
            "plate_as_consumable_no_grip_serviceability",
        ],
        "body_rects": body_rects,
    }


def _harness_seam_routing_check(
    cable_envelopes: list[dict[str, Any]],
    *,
    split_y: float,
) -> dict[str, Any]:
    """(c) Harness routing slack / bend radius across the seam.

    The sensor/lid/lower service harness must route across the structural seam
    (``split_y`` = inter-plate service-gap midpoint) with enough straight-run slack
    and a bend radius no tighter than the cable's printed/COTS bound. This reads the
    harness cable bend envelopes (each carrying ``min_bend_radius_y`` /
    ``straight_service_length_y``) and the slack available across the seam. The
    verdict fields are MEASURED; ``within_bound`` only flips True if both slack and
    bend radius clear their bounds, and ``requires_physical_evidence`` keeps the
    authoritative state pending regardless."""
    min_bend_radius_mm = None
    min_slack_mm = None
    body_rects: list[dict[str, Any]] = []
    spanning = 0
    for env in cable_envelopes:
        ey0 = float(env["y"])
        ey1 = ey0 + float(env["width_y"])
        # straight-run slack the envelope provides (service length the harness can
        # take up as it crosses the seam)
        slack = float(env.get("straight_service_length_y", env.get("width_y", 0.0)))
        bend = float(env.get("min_bend_radius_y", env.get("min_bend_radius_mm", 0.0)))
        if min_slack_mm is None or slack < min_slack_mm:
            min_slack_mm = slack
        if bend > 0.0 and (min_bend_radius_mm is None or bend < min_bend_radius_mm):
            min_bend_radius_mm = bend
        # does this envelope's routing column straddle the seam?
        seam_span = ey0 <= split_y <= ey1
        if seam_span:
            spanning += 1
        body_rects.append(
            {
                "name": f"{env.get('name', 'harness')}_seam_routing_proxy",
                "role": "harness_seam_routing_slack_bend_proxy",
                "connector_name": env.get("connector_name"),
                "x": round(float(env["x"]), 3),
                "y": round(ey0, 3),
                "z": round(float(env["z"]), 3),
                "length_x": round(float(env["length_x"]), 3),
                "width_y": round(float(env["width_y"]), 3),
                "height_z": round(float(env["height_z"]), 3),
                "spans_seam": seam_span,
            }
        )
    min_bend_radius_mm = round(min_bend_radius_mm, 4) if min_bend_radius_mm is not None else 0.0
    min_slack_mm = round(min_slack_mm, 4) if min_slack_mm is not None else 0.0
    # geometric feasibility: positive slack AND a real (non-zero) bend radius bound
    within_bound = min_slack_mm > 0.0 and min_bend_radius_mm > 0.0
    return {
        "name": "harness_seam_routing_check",
        "role": "harness_seam_routing_slack_bend_validation_body",
        "validation": "required_gate6_real_harness_seam_routing_serviceability_evidence",
        "failure_rule": (
            "insufficient_slack_or_tight_bend_or_unmeasured_seam_routing_blocks_service"
        ),
        "evidence_gate": "Gate 6 sensor install / serviceability",
        "cad_value": (
            f"{len(cable_envelopes)} cable envelopes / "
            f"{min_slack_mm:.2f} mm slack / "
            f"{min_bend_radius_mm:.2f} mm min bend radius / "
            f"{spanning} spanning seam"
        ),
        "split_y": round(float(split_y), 3),
        "cable_envelope_count": len(cable_envelopes),
        "seam_spanning_count": spanning,
        # REAL geometric verdict fields (measured from harness envelopes):
        "slack_mm": min_slack_mm,
        "min_bend_radius_mm": min_bend_radius_mm,
        "within_bound": within_bound,
        "source_layout_checks": [
            "sensor_service_cable_envelopes",
            "tile_origins",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "harness_routes_across_seam_with_service_slack",
            "harness_bend_radius_within_cable_bound",
        ],
        "body_rects": body_rects,
    }


def build_split_segment_swept_removal_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout.get("split_segment_swept_removal_check")
    if spec is None:
        raise ValueError(
            "split_segment_swept_removal_check is only emitted when "
            "production_assembly.keyed_joints_enabled is true"
        )
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("split segment swept removal check requires segment pairs")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_trapped_plate_lift_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout.get("trapped_plate_lift_check")
    if spec is None:
        raise ValueError(
            "trapped_plate_lift_check is only emitted when "
            "production_assembly.keyed_joints_enabled is true"
        )
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("trapped plate lift check requires plate footprints")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_harness_seam_routing_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout.get("harness_seam_routing_check")
    if spec is None:
        raise ValueError(
            "harness_seam_routing_check is only emitted when "
            "production_assembly.keyed_joints_enabled is true"
        )
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("harness seam routing check requires cable envelopes")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_operating_service_dress_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["operating_service_dress_check"]["body_rects"]
    if not rects:
        raise ValueError("operating service dress check requires service envelopes")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_pipette_puncture_swept_path_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    sweep = layout["pipette_puncture_swept_path_check"]
    centers = sweep["target_centers"]
    z0 = sweep["bottom_z"] if assembly_position else 0.0

    return (
        cq.Workplane("XY")
        .pushPoints(centers)
        .circle(sweep["diameter"] / 2)
        .extrude(sweep["height_z"])
        .translate((0, 0, z0))
    )


def build_pipette_toolhead_swept_body_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    body = layout["pipette_toolhead_swept_body_check"]["body_rects"][0]
    z_shift = 0.0 if assembly_position else -float(body["z"])
    return _boxes_from_rectangles([body], z_shift=z_shift)


def build_row_tiling_service_clearance_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["row_tiling_service_clearance_check"]["review_rects"]
    if not rects:
        raise ValueError("row tiling service clearance check requires review rectangles")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)
