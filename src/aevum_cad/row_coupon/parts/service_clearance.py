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
