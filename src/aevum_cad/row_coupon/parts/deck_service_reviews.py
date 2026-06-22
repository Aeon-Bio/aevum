from __future__ import annotations
from typing import Any
import cadquery as cq
from ..layout import (row_coupon_layout)
from ._geom_base import (_boxes_from_rectangles, _perimeter_rails, _rectangles_bounding_extents)
from ._shared_tile import (_deck_slot_opening_for_tile, _septum_access_window_for_tile)


def _adjacent_deck_slot_keepout_check(
    adjacent_keepouts: list[dict[str, Any]],
    *,
    params: dict[str, Any],
) -> dict[str, Any]:
    x_len, y_len, z_len = _rectangles_bounding_extents(adjacent_keepouts)
    deck = params["deck_interface"]
    return {
        "name": "adjacent_deck_slot_keepout_check",
        "role": "neighbor_ot2_slot_overhead_keepout_validation_body",
        "validation": "required_gate3_adjacent_slot_keepout_evidence",
        "failure_rule": (
            "adjacent_slot_interference_or_unmeasured_neighbor_keepout_blocks_ot2_placement_pass"
        ),
        "evidence_gate": "Gate 3 OT-2 placement",
        "cad_value": (
            f"{len(adjacent_keepouts)} neighbor keepouts / "
            f"{x_len:.2f} x {y_len:.2f} x {z_len:.2f} mm"
        ),
        "keepout_count": len(adjacent_keepouts),
        "adjacent_slot_columns": int(deck.get("adjacent_slot_keepout_columns", 0)),
        "required_side_service_vertical_clearance_z": round(
            float(deck.get("side_service_vertical_clearance_z", 0.0)),
            3,
        ),
        "source_layout_checks": ["side_gas_service_interfaces"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "normal_ot2_operation_in_adjacent_deck_slots",
            "side_service_clearance_with_neighbor_modules",
            "row_tiling_with_connected_services",
        ],
        "body_rects": adjacent_keepouts,
    }


def _adjacent_deck_slot_keepout_rectangles(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    deck_plane_z: float,
) -> list[dict[str, Any]]:
    deck = params["deck_interface"]
    columns = int(deck.get("adjacent_slot_keepout_columns", 0))
    height = deck.get("adjacent_slot_service_keepout_height_z", 0.0)
    if columns <= 0 or height <= 0:
        return []

    row_axis = layout["row_axis"]
    rects: list[dict[str, Any]] = []
    for tile in layout["tile_origins"]:
        slot_x, slot_y, slot_len, slot_wid = _deck_slot_opening_for_tile(tile, params)
        if row_axis == "y":
            directions = [("left", -1.0), ("right", 1.0)]
            for side, direction in directions:
                for column in range(1, columns + 1):
                    rects.append(
                        {
                            "name": f"tile_{tile['index']}_{side}_adjacent_slot_{column}",
                            "tile_index": tile["index"],
                            "side": side,
                            "column_offset": int(direction * column),
                            "x": round(slot_x + direction * deck["slot_pitch_x"] * column, 3),
                            "y": round(slot_y, 3),
                            "z": round(deck_plane_z, 3),
                            "length_x": round(slot_len, 3),
                            "width_y": round(slot_wid, 3),
                            "height_z": round(height, 3),
                        }
                    )
        else:
            directions = [("front", -1.0), ("rear", 1.0)]
            for side, direction in directions:
                for column in range(1, columns + 1):
                    rects.append(
                        {
                            "name": f"tile_{tile['index']}_{side}_adjacent_slot_{column}",
                            "tile_index": tile["index"],
                            "side": side,
                            "column_offset": int(direction * column),
                            "x": round(slot_x, 3),
                            "y": round(slot_y + direction * deck["slot_pitch_y"] * column, 3),
                            "z": round(deck_plane_z, 3),
                            "length_x": round(slot_len, 3),
                            "width_y": round(slot_wid, 3),
                            "height_z": round(height, 3),
                        }
                    )
    return rects


def _adjacent_slot_service_collision_review_rectangles(
    *,
    adjacent_keepouts: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    deck = params["deck_interface"]
    bundle_len = float(production.get("adjacent_slot_collision_bundle_length_x", 44.0))
    bundle_wid = float(production.get("adjacent_slot_collision_bundle_width_y", 6.0))
    bundle_h = float(production.get("adjacent_slot_collision_bundle_height_z", 4.0))
    inset = float(production.get("adjacent_slot_collision_inset_xy", 6.0))
    required_clearance = float(deck.get("side_service_vertical_clearance_z", 0.0))
    rects: list[dict[str, Any]] = []
    for keepout in adjacent_keepouts:
        keepout_len = float(keepout["length_x"])
        keepout_wid = float(keepout["width_y"])
        keepout_h = float(keepout["height_z"])
        length = min(bundle_len, max(keepout_len - 2 * inset, 1.0))
        width = min(bundle_wid, max(keepout_wid - 2 * inset, 1.0))
        height = min(bundle_h, max(keepout_h - 0.5, 0.5))
        z = float(keepout["z"]) + 0.5
        rects.append(
            {
                "name": f"{keepout['name']}_service_collision_review",
                "review_state": "service_dress_adjacent_slot_collision",
                "review_kind": "gas_electrical_service_bundle_intrudes_neighbor_slot",
                "owner_part": "adjacent_slot_service_collision_review",
                "retained_part": "gas_and_electrical_service_leads",
                "blocked_fail_closed_state": "adjacent_slot_service_collision",
                "source_keepout_name": keepout["name"],
                "source_validation_checks": [
                    "adjacent_deck_slot_keepout_check",
                    "row_tiling_service_clearance_check",
                    "operating_service_dress_check",
                ],
                "tile_index": int(keepout["tile_index"]),
                "side": keepout["side"],
                "column_offset": int(keepout["column_offset"]),
                "x": round(float(keepout["x"]) + (keepout_len - length) / 2, 3),
                "y": round(float(keepout["y"]) + (keepout_wid - width) / 2, 3),
                "z": round(z, 3),
                "length_x": round(length, 3),
                "width_y": round(width, 3),
                "height_z": round(height, 3),
                "collides_with_adjacent_slot_keepout": True,
                "required_vertical_clearance_z": round(required_clearance, 3),
                "vertical_clearance_z": round(
                    z - (float(keepout["z"]) + keepout_h),
                    3,
                ),
            }
        )
    return rects


def _assembly_debris_review_rectangles(
    *,
    dry_bay_envelope: dict[str, Any],
    wet_dry_failure_paths: dict[str, list[dict[str, Any]]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    dry_x = float(dry_bay_envelope["x"])
    dry_y = float(dry_bay_envelope["y"])
    dry_top_z = float(dry_bay_envelope["top_z"])
    dry_len = float(dry_bay_envelope["length_x"])
    dry_wid = float(dry_bay_envelope["width_y"])
    dry_h = dry_top_z - float(dry_bay_envelope["bottom_z"])
    chip_len = min(
        float(production.get("assembly_debris_review_chip_length_x", 8.0)),
        max(dry_len / 8.0, 1.0),
    )
    chip_wid = min(
        float(production.get("assembly_debris_review_chip_width_y", 3.0)),
        max(dry_wid / 18.0, 1.0),
    )
    chip_h = min(
        float(production.get("assembly_debris_review_chip_height_z", 0.8)),
        max(dry_h / 8.0, 0.4),
    )
    top_gap = float(production.get("assembly_debris_review_top_gap_z", 0.4))
    chip_z = round(dry_top_z - top_gap - chip_h, 3)
    source_checks = [
        "printability_support_cleanup_check",
        "assembly_state_witness_check",
        "dry_bay_ingress_audit_check",
        "wet_dry_failure_path_check",
    ]
    base = {
        "review_state": "assembly_debris_present",
        "owner_part": "assembly_debris_review",
        "retained_part": "plate_support_frame_wet_dry_witness_paths",
        "source_validation_checks": source_checks,
        "blocked_fail_closed_state": "assembly_debris_present",
        "evidence_gate": "Gate 2 dry assembly",
    }
    rects = [
        {
            **base,
            "name": "dry_bay_loose_assembly_debris_review",
            "review_kind": "loose_debris_inside_protected_dry_bay",
            "source_layout_check": "dry_bay_envelope",
            "dry_bay_relation": "inside_protected_footprint",
            "x": round(dry_x + dry_len * 0.52 - chip_len / 2.0, 3),
            "y": round(dry_y + dry_wid * 0.50 - chip_wid / 2.0, 3),
            "z": chip_z,
            "length_x": round(chip_len, 3),
            "width_y": round(chip_wid, 3),
            "height_z": round(chip_h, 3),
        }
    ]
    for threshold in wet_dry_failure_paths.get("dry_bay_aperture_thresholds", []):
        bridge_len = min(chip_len, max(float(threshold["inner_length_x"]) / 6.0, 1.0))
        bridge_wid = min(
            chip_wid,
            max(float(threshold["rail_width"]) * 1.6, 0.8),
        )
        rects.append(
            {
                **base,
                "name": (
                    f"tile_{threshold['tile_index']}_dry_bay_threshold_"
                    "assembly_debris_review"
                ),
                "tile_index": threshold["tile_index"],
                "review_kind": "support_debris_bridge_on_dry_bay_threshold",
                "source_layout_check": "wet_dry_failure_paths",
                "dry_bay_relation": "threshold_witness_path_debris_bridge",
                "x": round(
                    float(threshold["inner_x"])
                    + float(threshold["inner_length_x"]) / 2.0
                    - bridge_len / 2.0,
                    3,
                ),
                "y": round(float(threshold["y"]) + float(threshold["rail_width"]) / 2.0, 3),
                "z": chip_z,
                "length_x": round(bridge_len, 3),
                "width_y": round(bridge_wid, 3),
                "height_z": round(chip_h, 3),
            }
        )
    return rects


def _deck_frame_keepout_check(
    *,
    position_layout: dict[str, Any],
    params: dict[str, Any],
    deck_plane_z: float,
    slot_footprint_rects: list[dict[str, Any]],
) -> dict[str, Any]:
    deck = params["deck_interface"]
    height = float(deck["deck_frame_keepout_height_z"])
    frame_rect = {
        "name": "ot2_deck_frame_keepout_envelope",
        "x": 0.0,
        "y": 0.0,
        "z": round(deck_plane_z, 3),
        "length_x": round(float(position_layout["length_x"]), 3),
        "width_y": round(float(position_layout["width_y"]), 3),
        "height_z": round(height, 3),
    }
    slot_cut_rects = [
        {
            **rect,
            "name": f"{rect['name']}_frame_cutout",
            "z": round(deck_plane_z - 0.1, 3),
            "height_z": round(height + 0.2, 3),
        }
        for rect in slot_footprint_rects
    ]
    return {
        **frame_rect,
        "name": "deck_frame_keepout_check",
        "role": "ot2_deck_frame_rib_keepout_validation_body",
        "validation": "required_gate3_deck_frame_keepout_evidence",
        "failure_rule": (
            "deck_frame_contact_or_unmeasured_frame_keepout_blocks_ot2_placement_pass"
        ),
        "evidence_gate": "Gate 3 OT-2 placement",
        "cad_value": (
            f"{float(frame_rect['length_x']):.2f} x "
            f"{float(frame_rect['width_y']):.2f} x "
            f"{float(frame_rect['height_z']):.2f} mm / "
            f"{len(slot_cut_rects)} slot cutouts"
        ),
        "slot_cutout_count": len(slot_cut_rects),
        "source_layout_checks": ["deck_slot_footprint_check"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "normal_ot2_deck_frame_clearance",
            "repeatable_row_module_placement",
            "dry_bay_clearance_after_deck_cycles",
        ],
        "frame_rect": frame_rect,
        "slot_cut_rects": slot_cut_rects,
        "body_rects": [frame_rect],
    }


def _deck_module_unseated_review_rectangles(
    *,
    deck_engagement_feet: list[dict[str, Any]],
    deck_plane_z: float,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    deck = params["deck_interface"]
    production = params.get("production_assembly", {})
    lift_z = float(production.get("deck_module_unseated_lift_z", 12.0))
    rail_w = float(production.get("deck_module_unseated_witness_frame_width_xy", 0.7))
    witness_h = float(production.get("deck_module_unseated_witness_height_z", 0.6))
    foot_bottom_z = float(deck_plane_z) + float(deck["slot_shoe_thickness_z"])

    return [
        {
            "name": f"tile_{foot['tile_index']}_deck_foot_{index:02d}_unseated_witness",
            "tile_index": foot["tile_index"],
            "witness_kind": "deck_engagement_foot_seating_footprint",
            "review_state": "deck_module_unseated",
            "retained_part": "deck_pods",
            "source_layout_check": "deck_engagement_feet",
            "x": round(float(foot["x"]), 3),
            "y": round(float(foot["y"]), 3),
            "z": round(foot_bottom_z, 3),
            "length_x": round(float(foot["length_x"]), 3),
            "width_y": round(float(foot["width_y"]), 3),
            "height_z": round(witness_h, 3),
            "rail_width": round(rail_w, 3),
            "unseated_offset_z": round(lift_z, 3),
            "meaning": "deck engagement foot is lifted out of its OT-2 seating footprint",
        }
        for index, foot in enumerate(deck_engagement_feet, start=1)
    ]


def _deck_pod_seating_repeatability_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    deck_engagement_feet: list[dict[str, Any]],
    deck_pod_frame_keys: list[dict[str, Any]],
    dry_bay_envelope: dict[str, Any],
) -> dict[str, Any]:
    deck = params["deck_interface"]
    production = params.get("production_assembly", {})
    metrology = params.get("consumable_metrology", {})
    check_params = params.get("deck_pod_seating_repeatability_check", {})
    cycle_count = int(check_params.get("seat_release_cycles", 5))
    slab_len = float(check_params.get("length_x", 70.0))
    slab_wid = float(check_params.get("width_y", 58.0))
    slab_h = float(check_params.get("height_z", 0.5))
    x0 = (
        float(layout["length_x"])
        + float(metrology.get("viewer_offset_x", 18.0))
        + float(check_params.get("viewer_offset_x", 244.0))
    )
    y0 = (float(layout["width_y"]) - slab_wid) / 2
    slot_count = len(layout["tile_origins"])

    checkpoints = [
        {
            "name": "seat_release_repeatability",
            "blocks": ["deck_pod_repeat_seating_unproven"],
            "source_layout_checks": ["deck_engagement_feet"],
            "source_validation_checks": ["deck_slot_footprint_check"],
            "inspection_method": "five_ot2_deck_seat_release_cycles",
            "evidence_gate": "Gate 3 OT-2 placement",
        },
        {
            "name": "rock_yaw_after_service",
            "blocks": ["rocking_or_yaw_unmeasured"],
            "source_layout_checks": ["deck_engagement_feet"],
            "source_validation_checks": ["deck_slot_footprint_check"],
            "inspection_method": "manual_rock_yaw_photo_or_feeler_gauge",
            "evidence_gate": "Gate 3 OT-2 placement",
        },
        {
            "name": "shoe_and_key_wear_after_release",
            "blocks": ["pod_frame_key_or_shoe_wear_unchecked"],
            "source_layout_checks": ["deck_engagement_feet", "deck_pod_frame_keys"],
            "inspection_method": "visual_wear_check_after_cycles",
            "evidence_gate": "Gate 3 OT-2 placement",
        },
        {
            "name": "deck_frame_keepout_after_cycle",
            "blocks": ["deck_frame_contact_unverified"],
            "source_validation_checks": ["deck_frame_keepout_check"],
            "inspection_method": "frame_contact_visual_or_feeler_gauge",
            "evidence_gate": "Gate 3 OT-2 placement",
        },
        {
            "name": "dry_bay_debris_bridge_after_cycle",
            "blocks": ["dry_bay_debris_after_pod_cycle_unchecked"],
            "source_layout_checks": ["dry_bay_envelope"],
            "source_validation_checks": ["dry_bay_ingress_audit_check"],
            "inspection_method": "post_cycle_dry_bay_debris_inspection",
            "evidence_gate": "Gate 3 OT-2 placement",
        },
    ]
    blockers = sorted(
        {
            block
            for checkpoint in checkpoints
            for block in checkpoint["blocks"]
        }
    )
    source_layout_checks = sorted(
        {
            source
            for checkpoint in checkpoints
            for source in checkpoint.get("source_layout_checks", [])
        }
    )
    source_validation_checks = sorted(
        {
            source
            for checkpoint in checkpoints
            for source in checkpoint.get("source_validation_checks", [])
        }
    )

    return {
        "name": "deck_pod_seating_repeatability_check",
        "role": "deck_pod_seating_release_repeatability_evidence_blocker",
        "validation": (
            "cad_proxy_deck_pod_repeatability_physical_evidence_required"
        ),
        "failure_rule": (
            "rocking_yaw_wear_or_frame_contact_blocks_ot2_operation_until_gate3_evidence"
        ),
        "evidence_gate": "Gate 3 OT-2 placement",
        "cad_value": (
            f"{len(deck_engagement_feet)} feet / {len(deck_pod_frame_keys)} keys / "
            f"{slot_count} slots / {cycle_count} cycles"
        ),
        "checkpoint_count": len(checkpoints),
        "checkpoints": checkpoints,
        "blockers": blockers,
        "source_layout_checks": source_layout_checks,
        "source_validation_checks": source_validation_checks,
        "deck_slot_count": slot_count,
        "deck_foot_count": len(deck_engagement_feet),
        "pod_frame_key_count": len(deck_pod_frame_keys),
        "seat_release_cycles": cycle_count,
        "slot_opening_length_x": round(float(deck["slot_opening_length_x"]), 3),
        "slot_opening_width_y": round(float(deck["slot_opening_width_y"]), 3),
        "slot_shoe_clearance_xy": round(float(deck["slot_shoe_clearance_xy"]), 3),
        "foot_slot_clearance_xy": round(
            float(deck.get("foot_slot_clearance_xy", deck["slot_shoe_clearance_xy"])),
            3,
        ),
        "pod_frame_key_clearance_xy": round(
            float(production.get("pod_frame_key_clearance_xy", 0.0)),
            3,
        ),
        "dry_bay_protected_footprint": {
            "x": dry_bay_envelope["x"],
            "y": dry_bay_envelope["y"],
            "length_x": dry_bay_envelope["length_x"],
            "width_y": dry_bay_envelope["width_y"],
        },
        "requires_physical_evidence": True,
        "all_checkpoints_block_ot2_operation": True,
        "physical_claims_blocked": [
            "normal_ot2_deck_seating",
            "repeatable_row_module_placement",
            "dry_bay_clearance_after_deck_cycles",
        ],
        "body_rects": [
            {
                "name": "deck_pod_repeatability_evidence_slab",
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": 0.0,
                "length_x": round(slab_len, 3),
                "width_y": round(slab_wid, 3),
                "height_z": round(slab_h, 3),
            }
        ],
    }


def _deck_pose_repeatability_review_rectangles(
    *,
    deck_engagement_feet: list[dict[str, Any]],
    deck_pod_repeatability_check: dict[str, Any],
    deck_plane_z: float,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    deck = params["deck_interface"]
    production = params.get("production_assembly", {})
    witness_h = float(production.get("deck_pose_repeatability_witness_height_z", 1.0))
    clearance_xy = float(
        deck_pod_repeatability_check.get(
            "foot_slot_clearance_xy",
            deck.get("foot_slot_clearance_xy", deck["slot_shoe_clearance_xy"]),
        )
    )
    yaw_projection = max(
        clearance_xy * 2.0,
        float(production.get("deck_pose_repeatability_yaw_projection_xy", 1.2)),
    )
    foot_bottom_z = float(deck_plane_z) + float(deck["slot_shoe_thickness_z"])
    source_validation_checks = [
        "deck_slot_footprint_check",
        "deck_frame_keepout_check",
        "deck_pod_seating_repeatability_check",
    ]
    blocker_states = [
        "deck_pod_repeat_seating_unproven",
        "rocking_or_yaw_unmeasured",
    ]

    rects: list[dict[str, Any]] = []
    for index, foot in enumerate(deck_engagement_feet, start=1):
        x = float(foot["x"])
        y = float(foot["y"])
        length_x = float(foot["length_x"])
        width_y = float(foot["width_y"])
        rects.extend(
            [
                {
                    "name": (
                        f"tile_{foot['tile_index']}_deck_foot_{index:02d}_"
                        "repeat_seat_review"
                    ),
                    "tile_index": foot["tile_index"],
                    "witness_kind": "repeat_seat_cycle_unproven_footprint",
                    "review_state": "deck_pose_repeatability_unproven",
                    "retained_part": "deck_pods",
                    "source_layout_check": "deck_engagement_feet",
                    "source_validation_checks": source_validation_checks,
                    "blocked_fail_closed_state": "deck_pod_repeat_seating_unproven",
                    "blocked_fail_closed_states": blocker_states,
                    "seat_release_cycles_required": deck_pod_repeatability_check[
                        "seat_release_cycles"
                    ],
                    "foot_slot_clearance_xy": round(clearance_xy, 3),
                    "x": round(x - clearance_xy, 3),
                    "y": round(y - clearance_xy, 3),
                    "z": round(foot_bottom_z, 3),
                    "length_x": round(length_x + clearance_xy * 2.0, 3),
                    "width_y": round(width_y + clearance_xy * 2.0, 3),
                    "height_z": round(witness_h, 3),
                    "meaning": (
                        "deck engagement foot has not proven repeat seating "
                        "through the required seat/release cycles"
                    ),
                },
                {
                    "name": (
                        f"tile_{foot['tile_index']}_deck_foot_{index:02d}_"
                        "rock_yaw_review"
                    ),
                    "tile_index": foot["tile_index"],
                    "witness_kind": "rocking_or_yaw_unmeasured_sweep",
                    "review_state": "deck_pose_repeatability_unproven",
                    "retained_part": "deck_pods",
                    "source_layout_check": "deck_engagement_feet",
                    "source_validation_checks": source_validation_checks,
                    "blocked_fail_closed_state": "rocking_or_yaw_unmeasured",
                    "blocked_fail_closed_states": blocker_states,
                    "seat_release_cycles_required": deck_pod_repeatability_check[
                        "seat_release_cycles"
                    ],
                    "yaw_projection_xy": round(yaw_projection, 3),
                    "x": round(x - yaw_projection, 3),
                    "y": round(y + width_y / 2.0 - yaw_projection / 2.0, 3),
                    "z": round(foot_bottom_z + witness_h, 3),
                    "length_x": round(length_x + yaw_projection * 2.0, 3),
                    "width_y": round(yaw_projection, 3),
                    "height_z": round(witness_h, 3),
                    "meaning": (
                        "deck engagement foot rocking or yaw remains unmeasured "
                        "after service seating"
                    ),
                },
            ]
        )
    return rects


def _deck_slot_footprint_check(
    slot_rects: list[dict[str, Any]],
) -> dict[str, Any]:
    x_len, y_len, z_len = _rectangles_bounding_extents(slot_rects)
    return {
        "name": "deck_slot_footprint_check",
        "role": "ot2_slot_opening_footprint_validation_body",
        "validation": "required_gate3_deck_slot_footprint_evidence",
        "failure_rule": (
            "slot_mismatch_or_unmeasured_deck_engagement_blocks_ot2_placement_pass"
        ),
        "evidence_gate": "Gate 3 OT-2 placement",
        "cad_value": (
            f"{len(slot_rects)} slots / {x_len:.2f} x {y_len:.2f} x {z_len:.2f} mm"
        ),
        "slot_count": len(slot_rects),
        "slot_names": tuple(str(rect["name"]) for rect in slot_rects),
        "source_layout_checks": ["tile_origins", "deck_engagement_feet"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "normal_ot2_deck_slot_engagement",
            "repeatable_row_module_placement",
        ],
        "body_rects": slot_rects,
    }


def _deck_slot_footprint_rectangles(
    *,
    tile_origins: list[dict[str, float | int]],
    params: dict[str, Any],
    deck_plane_z: float,
) -> list[dict[str, Any]]:
    deck = params["deck_interface"]
    thickness = float(deck["deck_slot_footprint_check_thickness_z"])
    rects: list[dict[str, Any]] = []
    for tile in tile_origins:
        x, y, slot_len, slot_wid = _deck_slot_opening_for_tile(tile, params)
        rects.append(
            {
                "name": f"tile_{tile['index']}_deck_slot_footprint",
                "tile_index": tile["index"],
                "x": round(x, 3),
                "y": round(y, 3),
                "z": round(deck_plane_z - thickness, 3),
                "length_x": round(slot_len, 3),
                "width_y": round(slot_wid, 3),
                "height_z": round(thickness, 3),
            }
        )
    return rects


def _misdressed_service_bundle_review_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
    pipette_toolhead_swept_body: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    bundle_w = float(production.get("misdressed_service_bundle_width_y", 5.0))
    bundle_h = float(production.get("misdressed_service_bundle_height_z", 4.0))
    z_offset = float(production.get("misdressed_service_bundle_toolhead_overlap_z", 1.0))
    rects: list[dict[str, Any]] = []
    for tile in tile_origins:
        x, y, length, width = _septum_access_window_for_tile(tile, params)
        rects.append(
            {
                "name": (
                    f"tile_{tile['index']}_misdressed_service_bundle_"
                    "over_pipette_field"
                ),
                "review_state": "service_dress_over_pipette_field",
                "review_kind": "gas_electrical_service_bundle_crosses_top_access",
                "owner_part": "misdressed_service_bundle_review",
                "retained_part": "gas_and_electrical_service_leads",
                "source_validation_checks": [
                    "operating_service_dress_check",
                    "row_tiling_service_clearance_check",
                    "pipette_toolhead_swept_body_check",
                ],
                "tile_index": int(tile["index"]),
                "x": round(x, 3),
                "y": round(y + (width - bundle_w) / 2, 3),
                "z": round(float(pipette_toolhead_swept_body["z"]) + z_offset, 3),
                "length_x": round(length, 3),
                "width_y": round(bundle_w, 3),
                "height_z": round(bundle_h, 3),
                "overlaps_septum_access_window": True,
                "toolhead_overlap_z": round(z_offset, 3),
            }
        )
    return rects


def build_adjacent_deck_slot_keepout_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["adjacent_deck_slot_keepout_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_adjacent_slot_service_collision_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["adjacent_slot_service_collision_review"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_assembly_debris_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["assembly_debris_review"]
    if not rects:
        raise ValueError("assembly debris review requires debris witness rectangles")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_deck_frame_keepout_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["deck_frame_keepout_check"]
    frame_rect = spec["frame_rect"]
    slot_cut_rects = spec["slot_cut_rects"]
    z_shift = 0.0 if assembly_position else -float(frame_rect["z"])
    frame = (
        cq.Workplane("XY")
        .box(
            frame_rect["length_x"],
            frame_rect["width_y"],
            frame_rect["height_z"],
            centered=(False, False, False),
        )
        .translate((frame_rect["x"], frame_rect["y"], frame_rect["z"] + z_shift))
    )
    for slot in slot_cut_rects:
        frame = frame.cut(
            cq.Workplane("XY")
            .box(
                slot["length_x"],
                slot["width_y"],
                slot["height_z"],
                centered=(False, False, False),
            )
            .translate((slot["x"], slot["y"], slot["z"] + z_shift))
        )
    return frame


def build_deck_module_unseated_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["deck_module_unseated_review"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)

    review: cq.Workplane | None = None
    for rect in rects:
        part = _perimeter_rails(
            x0=float(rect["x"]),
            y0=float(rect["y"]),
            length=float(rect["length_x"]),
            width=float(rect["width_y"]),
            rail_width=float(rect["rail_width"]),
            height=float(rect["height_z"]),
            z0=float(rect["z"]) + z_shift,
        )
        review = part if review is None else review.union(part)
    if review is None:
        raise ValueError("deck module unseated review requires deck engagement feet")
    return review


def build_deck_pod_seating_repeatability_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["deck_pod_seating_repeatability_check"]
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("deck pod seating repeatability check requires rectangles")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_deck_pose_repeatability_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["deck_pose_repeatability_review"]
    if not rects:
        raise ValueError("deck pose repeatability review requires deck engagement feet")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_deck_slot_footprint_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["deck_slot_footprint_check"]["body_rects"]
    if not rects:
        raise ValueError("deck slot footprint checks require at least one slot")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_misdressed_service_bundle_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["misdressed_service_bundle_review"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)
