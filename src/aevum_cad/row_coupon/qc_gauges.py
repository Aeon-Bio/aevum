from __future__ import annotations
from typing import Any
import cadquery as cq
from .layout import (row_coupon_layout)
from .manifest import (row_coupon_part_manifest)
from .parts._geom_base import (_boxes_from_rectangles, _rounded_box)
from .parts._shared_tile import (_well_centers_for_tile)


def _add_gasket_tab_leak_witness_features(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
    owner_part: str,
    z_shift: float = 0.0,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    for witness in layout["gasket_tab_leak_witnesses"]:
        if witness["owner_part"] != owner_part:
            continue
        gutter = dict(witness["gutter_rect"])
        gutter["z"] = float(gutter["z"]) + z_shift
        model = model.cut(_boxes_from_rectangles([gutter]))

        threshold = dict(witness["threshold_rect"])
        threshold["z"] = float(threshold["z"]) + z_shift
        model = model.union(_boxes_from_rectangles([threshold]))
    return model


def _consumable_metrology_gauge(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
) -> dict[str, Any]:
    plate = params["plate"]
    mat = params["septum_mat"]
    metrology = params.get("consumable_metrology", {})
    border = float(metrology.get("gauge_border_xy", 8.0))
    base_h = float(metrology.get("gauge_base_thickness_z", 3.0))
    radius = float(metrology.get("gauge_corner_radius", 1.5))
    x0 = float(layout["length_x"]) + float(metrology.get("viewer_offset_x", 18.0))
    y0 = 0.0
    z0 = 0.0
    length = float(plate["length_x"]) + 2 * border
    width = float(plate["width_y"]) + 2 * border
    top_z = z0 + base_h
    plate_clearance = float(metrology.get("plate_go_clearance_xy", 0.35))
    mat_clearance = float(metrology.get("mat_go_clearance_xy", 0.25))
    plate_pocket_depth = float(metrology.get("plate_pocket_depth_z", 0.8))
    mat_pocket_depth = float(metrology.get("mat_pocket_depth_z", 0.6))
    plug_clearance = float(metrology.get("plug_pocket_clearance_diameter", 0.35))
    plug_depth = float(metrology.get("plug_pocket_depth_z", 2.2))
    plug_diameter = float(mat["round_plug_diameter"]) + plug_clearance
    plug_centers = [
        {"x": round(x, 3), "y": round(y, 3)}
        for x, y in _well_centers_for_tile({"x": x0 + border, "y": y0 + border}, params)
    ]
    base_rect = {
        "name": "consumable_metrology_gauge_base",
        "x": round(x0, 3),
        "y": round(y0, 3),
        "z": round(z0, 3),
        "length_x": round(length, 3),
        "width_y": round(width, 3),
        "height_z": round(base_h, 3),
        "corner_radius": round(radius, 3),
    }
    plate_pocket_rect = {
        "name": "consumable_metrology_plate_go_pocket",
        "x": round(x0 + border - plate_clearance, 3),
        "y": round(y0 + border - plate_clearance, 3),
        "z": round(top_z - plate_pocket_depth, 3),
        "length_x": round(float(plate["length_x"]) + 2 * plate_clearance, 3),
        "width_y": round(float(plate["width_y"]) + 2 * plate_clearance, 3),
        "height_z": round(plate_pocket_depth, 3),
        "clearance_xy": round(plate_clearance, 3),
    }
    mat_pocket_rect = {
        "name": "consumable_metrology_septum_mat_go_pocket",
        "x": round(x0 + border - mat_clearance, 3),
        "y": round(y0 + border - mat_clearance, 3),
        "z": round(top_z - mat_pocket_depth, 3),
        "length_x": round(float(plate["length_x"]) + 2 * mat_clearance, 3),
        "width_y": round(float(plate["width_y"]) + 2 * mat_clearance, 3),
        "height_z": round(mat_pocket_depth, 3),
        "clearance_xy": round(mat_clearance, 3),
    }
    return {
        "name": "consumable_metrology_gauge",
        "role": "validation-only COTS plate, septum mat, and plug go/no-go gauge",
        "validation": "required_gate1_consumable_fit_metrology_evidence",
        "failure_rule": "unmeasured_plate_mat_or_plug_fit_blocks_gate1_pass",
        "evidence_gate": "Gate 1 Print QC",
        "cad_value": (
            f"{length:.2f} x {width:.2f} x {base_h:.2f} mm / "
            f"{len(plug_centers)} plug pockets"
        ),
        "x": round(x0, 3),
        "y": round(y0, 3),
        "z": round(z0, 3),
        "length_x": round(length, 3),
        "width_y": round(width, 3),
        "height_z": round(base_h, 3),
        "border_xy": round(border, 3),
        "corner_radius": round(radius, 3),
        "plate_pocket_depth_z": round(plate_pocket_depth, 3),
        "mat_pocket_depth_z": round(mat_pocket_depth, 3),
        "plug_pocket_depth_z": round(plug_depth, 3),
        "plug_pocket_diameter": round(plug_diameter, 3),
        "plug_pocket_count": len(plug_centers),
        "source_layout_checks": [
            "consumable_metrology",
            "plate",
            "septum_mat",
            "well_grid",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "cots_microplate_go_fit",
            "septum_mat_go_fit",
            "round_plug_alignment_fit",
            "gate1_print_qc_consumable_go_no_go",
        ],
        "base_rect": base_rect,
        "body_rects": [base_rect],
        "plate_pocket_rect": plate_pocket_rect,
        "mat_pocket_rect": mat_pocket_rect,
        "plug_pocket_centers": plug_centers,
    }


def _fail_closed_prerun_inspection_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_budget: dict[str, Any],
    gasket_gap_gauge: dict[str, Any],
    sensor_mount_summary: dict[str, Any],
    deck_engagement_feet: list[dict[str, Any]],
    service_lead_witnesses: list[dict[str, Any]],
    unseated_gas_pcb_cartridges_review: list[dict[str, Any]],
    unseated_side_gas_tubes_review: list[dict[str, Any]],
    unmated_connector_review_rects: list[dict[str, Any]],
) -> dict[str, Any]:
    from aevum_cad.row_coupon import (ROW_COUPON_SERVICE_MODES)
    metrology = params.get("consumable_metrology", {})
    check_params = params.get("fail_closed_prerun_inspection", {})
    tab_len = float(check_params.get("tab_length_x", 42.0))
    tab_wid = float(check_params.get("tab_width_y", 7.0))
    tab_h = float(check_params.get("tab_height_z", 0.9))
    tab_gap = float(check_params.get("tab_gap_y", 2.0))
    marker_len = float(check_params.get("marker_length_x", 4.0))
    marker_wid = float(check_params.get("marker_width_y", 3.0))
    marker_h = float(check_params.get("marker_height_z", 0.45))
    base_margin = float(check_params.get("base_margin_xy", 2.0))
    x0 = (
        float(layout["length_x"])
        + float(metrology.get("viewer_offset_x", 18.0))
        + float(check_params.get("viewer_offset_x", 100.0))
    )

    checkpoint_specs = [
        {
            "name": "deck_module_seated",
            "blocks": [
                "deck_module_unseated",
                "deck_pose_repeatability_unproven",
                "deck_pod_repeat_seating_unproven",
                "rocking_or_yaw_unmeasured",
            ],
            "source_validation_checks": [
                "deck_slot_footprint_check",
                "deck_frame_keepout_check",
                "deck_pod_seating_repeatability_check",
            ],
            "inspection_method": "visual_camera_manual_seat_check",
            "evidence_gate": "Gate 3 OT-2 placement",
            "cad_value": (
                f"{len(deck_engagement_feet)} feet / "
                f"{len(layout['tile_origins'])} slots"
            ),
        },
        {
            "name": "operating_stack_present",
            "blocks": [
                "microplates_missing",
                "septum_mats_missing",
                "perimeter_gaskets_missing",
            ],
            "source_validation_checks": ["assembly_state_witness_check"],
            "inspection_method": "visual_camera",
            "evidence_gate": "Gate 2 dry assembly",
            "cad_value": (
                f"{len(layout['tile_origins'])} plates / "
                f"{len(layout['tile_origins'])} mats / 2 gaskets"
            ),
        },
        {
            "name": "sample_relief_cap_seated",
            "blocks": [
                "sample_relief_cap_missing",
                "sample_relief_cap_unseated",
            ],
            "source_validation_checks": ["assembly_state_witness_check"],
            "inspection_method": "visual_camera",
            "evidence_gate": "Gate 2 dry assembly",
            "cad_value": "installed cap lip seated",
        },
        {
            "name": "wedge_locks_latched",
            "blocks": ["latches_unseated"],
            "source_validation_checks": [
                "assembly_state_witness_check",
                "gasket_compression_gap_gauge",
            ],
            "inspection_method": "visual_manual_cycle",
            "evidence_gate": "Gate 2 dry assembly",
            "cad_value": f"{len(layout['compression_stop_positions'])} stop positions",
        },
        {
            "name": "gasket_compression_in_range",
            "blocks": [
                "perimeter_gaskets_missing",
                "latches_unseated",
                "gasket_squeeze_out_of_range",
            ],
            "source_validation_checks": ["gasket_compression_gap_gauge"],
            "inspection_method": "caliper_gap_gauge",
            "evidence_gate": "Gate 2 dry assembly",
            "cad_value": (
                f"{float(compression_budget['gasket_squeeze_min_z']):.2f}.."
                f"{float(compression_budget['gasket_squeeze_max_z']):.2f} mm"
            ),
        },
        {
            "name": "gas_pcb_cartridges_sealed",
            "blocks": ["gas_pcbs_missing", "gas_pcb_cartridges_unseated"],
            "source_validation_checks": [
                "assembly_state_witness_check",
                "gas_pcb_flow_cell_check",
            ],
            "inspection_method": "visual_camera",
            "evidence_gate": "Gate 2 dry assembly",
            "cad_value": (
                f"{int(sensor_mount_summary['gas_sensor_pcb_count'])} gas PCBs / "
                f"{len(unseated_gas_pcb_cartridges_review)} compression seats"
            ),
        },
        {
            "name": "local_sensors_installed",
            "blocks": ["local_sensors_missing"],
            "source_validation_checks": [
                "assembly_state_witness_check",
                "sensor_installation_path_check",
                "ir_thermopile_fov_spot_check",
                "thermal_condensation_proxy_check",
            ],
            "inspection_method": "visual_camera_plus_sensor_inventory",
            "evidence_gate": "Gate 6 sensor/thermal",
            "cad_value": (
                f"{int(sensor_mount_summary['headspace_sht41_count'])} SHT41 / "
                f"{int(sensor_mount_summary['ir_thermopile_count'])} IR"
            ),
        },
        {
            "name": "service_leads_connected",
            "blocks": [
                "service_leads_missing",
                "side_gas_tubes_unseated",
                "electrical_connectors_unmated",
            ],
            "source_validation_checks": [
                "assembly_state_witness_check",
                "electrical_connector_mating_state_check",
            ],
            "inspection_method": "visual_camera",
            "evidence_gate": "Gate 2 dry assembly",
            "cad_value": (
                f"{len(service_lead_witnesses)} lead witnesses / "
                f"{len(unseated_side_gas_tubes_review)} gas tube seats / "
                f"{len(unmated_connector_review_rects)} connector states"
            ),
        },
        {
            "name": "services_dressed_clear",
            "blocks": [
                "tube_or_cable_over_pipette_field",
                "service_dress_over_pipette_field",
                "service_dress_adjacent_slot_collision",
                "adjacent_slot_service_collision",
            ],
            "source_validation_checks": [
                "operating_service_dress_check",
                "row_tiling_service_clearance_check",
                "pipette_toolhead_swept_body_check",
            ],
            "inspection_method": "visual_camera",
            "evidence_gate": "Gate 3 OT-2 placement",
            "cad_value": "service dress outside pipette field",
        },
        {
            "name": "dry_bay_clear_and_witness_paths_visible",
            "blocks": [
                "dry_bay_obstructed",
                "dry_bay_blocked",
                "wet_witness_path_hidden",
                "assembly_debris_present",
            ],
            "source_validation_checks": [
                "dry_bay_ingress_audit_check",
                "wet_dry_failure_path_check",
            ],
            "inspection_method": "visual_camera",
            "evidence_gate": "Gate 2 dry assembly",
            "cad_value": "dry bay open and witness paths visible",
        },
    ]

    base_rect = {
        "name": "fail_closed_prerun_inspection_base",
        "x": round(x0, 3),
        "y": 0.0,
        "z": 0.0,
        "length_x": round(tab_len + 2 * base_margin, 3),
        "width_y": round(
            len(checkpoint_specs) * tab_wid
            + max(0, len(checkpoint_specs) - 1) * tab_gap
            + 2 * base_margin,
            3,
        ),
        "height_z": 0.45,
    }
    checkpoints: list[dict[str, Any]] = []
    body_rects = [base_rect]
    for index, spec in enumerate(checkpoint_specs, start=1):
        y = base_margin + (index - 1) * (tab_wid + tab_gap)
        tab_rect = {
            "name": f"fail_closed_prerun_checkpoint_{index:02d}_{spec['name']}",
            "x": round(x0 + base_margin, 3),
            "y": round(y, 3),
            "z": base_rect["height_z"],
            "length_x": round(tab_len, 3),
            "width_y": round(tab_wid, 3),
            "height_z": round(tab_h, 3),
        }
        marker_rects = [
            {
                "name": f"fail_closed_prerun_checkpoint_{index:02d}_index_marker",
                "x": round(x0 + base_margin + 2.0, 3),
                "y": round(y + tab_wid - marker_wid - 1.0, 3),
                "z": round(base_rect["height_z"] + tab_h, 3),
                "length_x": round(marker_len + (index - 1) * 0.65, 3),
                "width_y": round(marker_wid, 3),
                "height_z": round(marker_h, 3),
            }
        ]
        checkpoints.append(
            {
                **spec,
                "index": index,
                "blocks_ot2_run": True,
                "tab_rect": tab_rect,
                "index_marker_rects": marker_rects,
            }
        )
    source_validation_checks = sorted(
        {
            source
            for checkpoint in checkpoints
            for source in checkpoint["source_validation_checks"]
        }
    )
    blockers = sorted(
        {
            block
            for checkpoint in checkpoints
            for block in checkpoint["blocks"]
        }
    )
    blocker_review_mode_aliases = {
        "deck_pod_repeat_seating_unproven": ["deck_pose_repeatability_unproven"],
        "rocking_or_yaw_unmeasured": ["deck_pose_repeatability_unproven"],
        "tube_or_cable_over_pipette_field": ["service_dress_over_pipette_field"],
        "adjacent_slot_service_collision": [
            "service_dress_adjacent_slot_collision"
        ],
        "dry_bay_blocked": ["dry_bay_obstructed"],
        "wet_witness_path_hidden": ["dry_bay_obstructed"],
    }
    blocker_service_review_modes: dict[str, list[str]] = {}
    uncovered_blockers: list[str] = []
    for block in blockers:
        review_modes: list[str] = []
        if block in ROW_COUPON_SERVICE_MODES:
            review_modes.append(block)
        review_modes.extend(blocker_review_mode_aliases.get(block, []))
        deduped_review_modes = sorted(dict.fromkeys(review_modes))
        blocker_service_review_modes[block] = deduped_review_modes
        if not deduped_review_modes:
            uncovered_blockers.append(block)
    for checkpoint in checkpoints:
        checkpoint["service_review_modes"] = sorted(
            {
                mode
                for block in checkpoint["blocks"]
                for mode in blocker_service_review_modes[block]
            }
        )
        checkpoint["uncovered_blockers"] = [
            block
            for block in checkpoint["blocks"]
            if not blocker_service_review_modes[block]
        ]

    return {
        "name": "fail_closed_prerun_inspection_check",
        "role": "validation-only fail-closed pre-run inspection checklist",
        "validation": "cad_proxy_operator_evidence_required_before_ot2_run",
        "evidence_gate": "Gate 2 dry assembly",
        "failure_rule": "any_blocker_not_passed_prevents_ot2_operation",
        "cad_value": (
            f"{len(checkpoints)} checkpoints / "
            "any_blocker_not_passed_prevents_ot2_operation"
        ),
        "fail_closed_rule": "any_blocker_not_passed_prevents_ot2_operation",
        "checkpoint_count": len(checkpoints),
        "all_checkpoints_block_ot2_run": True,
        "gasket_gap_gauge_blade_count": gasket_gap_gauge["blade_count"],
        "source_validation_checks": source_validation_checks,
        "blockers": blockers,
        "blocker_service_review_modes": blocker_service_review_modes,
        "all_blockers_have_service_review_mode": not uncovered_blockers,
        "uncovered_blockers": uncovered_blockers,
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "normal_ot2_operation",
            "wet_tests_after_dry_assembly",
            "powered_sensor_operation",
            "pipette_motion_with_connected_services",
        ],
        "base_rect": base_rect,
        "checkpoints": checkpoints,
        "body_rects": body_rects,
    }


def _gasket_tab_leak_witness_check(
    witnesses: list[dict[str, Any]],
) -> dict[str, Any]:
    wet_collectors = [witness["gutter_rect"] for witness in witnesses]
    inboard_dams = [witness["threshold_rect"] for witness in witnesses]
    body_rects = [*wet_collectors, *inboard_dams]
    return {
        "name": "gasket_tab_leak_witness_check",
        "role": "gasket_tab_root_wet_failure_witness_validation_body",
        "validation": "required_gate4_gasket_tab_leak_witness_evidence",
        "failure_rule": (
            "gasket_tab_root_leak_without_margin_witness_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{len(wet_collectors)} wet collectors / {len(inboard_dams)} inboard dams"
        ),
        "wet_collector_count": len(wet_collectors),
        "inboard_dam_count": len(inboard_dams),
        "witness_count": len(witnesses),
        "source_layout_checks": ["gasket_tab_leak_witnesses"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "gasket_service_tab_roots_do_not_bridge_to_dry_bay",
            "wet_operation_with_serviceable_gasket_tabs",
            "dry_bay_protection_from_gasket_margin_leaks",
        ],
        "body_rects": body_rects,
    }


def _gasket_tab_leak_witnesses_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    base_top_z: float,
    lid_bottom_z: float,
) -> list[dict[str, Any]]:
    seal = params["seal_interface"]
    production = params.get("production_assembly", {})
    tab_len = production.get("gasket_service_tab_length_x", 0.0)
    tab_depth = production.get("gasket_service_tab_depth_y", 0.0)
    margin_x = production.get("gasket_tab_witness_margin_x", 0.0)
    gap_y = production.get("gasket_tab_witness_gap_y", 0.0)
    gutter_w = production.get("gasket_tab_witness_gutter_width_y", 0.0)
    gutter_d = production.get("gasket_tab_witness_gutter_depth_z", 0.0)
    dam_w = production.get("gasket_tab_witness_dam_width_y", 0.0)
    dam_h = production.get("gasket_tab_witness_dam_height_z", 0.0)
    if min(tab_len, tab_depth, gutter_w, gutter_d, dam_w, dam_h) <= 0:
        return []

    rail_w = seal["gasket_rail_width"]
    rail_h = seal["compressed_gasket_height_z"]
    tab_x = (float(layout["length_x"]) - tab_len) / 2
    witness_x = max(0.0, tab_x - margin_x)
    witness_len = min(float(layout["length_x"]) - witness_x, tab_len + 2 * margin_x)
    side_specs = [
        {
            "side": "front",
            "tab_y": rail_w,
            "gutter_y": rail_w + tab_depth + gap_y,
            "dam_y": rail_w + tab_depth + gap_y + gutter_w + gap_y,
            "protected_direction": "+Y_toward_plate_row_and_dry_bay",
            "service_margin": "front",
        },
        {
            "side": "rear",
            "tab_y": float(layout["width_y"]) - rail_w - tab_depth,
            "gutter_y": float(layout["width_y"]) - rail_w - tab_depth - gap_y - gutter_w,
            "dam_y": float(layout["width_y"])
            - rail_w
            - tab_depth
            - gap_y
            - gutter_w
            - gap_y
            - dam_w,
            "protected_direction": "-Y_toward_plate_row_and_dry_bay",
            "service_margin": "rear",
        },
    ]
    layer_specs = [
        {
            "layer": "lower",
            "owner_part": "plate_support_frame",
            "gasket_z": base_top_z,
            "surface_z": base_top_z,
            "dam_z": base_top_z,
            "gutter_z": base_top_z - gutter_d,
            "dam_orientation": "up_from_lower_support_surface",
        },
        {
            "layer": "upper",
            "owner_part": "lid_manifold_shell",
            "gasket_z": lid_bottom_z - rail_h,
            "surface_z": lid_bottom_z,
            "dam_z": lid_bottom_z - dam_h,
            "gutter_z": lid_bottom_z - gutter_d,
            "dam_orientation": "down_from_lid_shell_underside",
        },
    ]
    witnesses: list[dict[str, Any]] = []
    for layer in layer_specs:
        for side in side_specs:
            tab_rect = {
                "name": f"{layer['layer']}_{side['side']}_gasket_service_tab",
                "x": round(tab_x, 3),
                "y": round(float(side["tab_y"]), 3),
                "z": round(float(layer["gasket_z"]), 3),
                "length_x": round(tab_len, 3),
                "width_y": round(tab_depth, 3),
                "height_z": round(rail_h, 3),
            }
            gutter_rect = {
                "name": f"{layer['layer']}_{side['side']}_tab_root_witness_gutter",
                "x": round(witness_x, 3),
                "y": round(float(side["gutter_y"]), 3),
                "z": round(float(layer["gutter_z"]), 3),
                "length_x": round(witness_len, 3),
                "width_y": round(gutter_w, 3),
                "height_z": round(gutter_d, 3),
            }
            dam_rect = {
                "name": f"{layer['layer']}_{side['side']}_tab_root_inboard_dam",
                "x": round(witness_x, 3),
                "y": round(float(side["dam_y"]), 3),
                "z": round(float(layer["dam_z"]), 3),
                "length_x": round(witness_len, 3),
                "width_y": round(dam_w, 3),
                "height_z": round(dam_h, 3),
            }
            witnesses.append(
                {
                    "name": f"{layer['layer']}_{side['side']}_gasket_tab_leak_witness",
                    "layer": layer["layer"],
                    "side": side["side"],
                    "owner_part": layer["owner_part"],
                    "service_role": "gasket_service_tab_root_witness",
                    "leak_management": "tab_root_margin_gutter_with_inboard_dam",
                    "protected_direction": side["protected_direction"],
                    "service_margin": side["service_margin"],
                    "dam_orientation": layer["dam_orientation"],
                    "tab_rect": tab_rect,
                    "gutter_rect": gutter_rect,
                    "threshold_rect": dam_rect,
                    "validation": "service_tab_root_witness_margin_not_leak_rate_proof",
                }
            )
    return witnesses


def _material_cleaning_witness_coupon(
    coupons: list[dict[str, Any]],
) -> dict[str, Any]:
    if not coupons:
        raise ValueError("material cleaning witness coupon requires coupons")
    body_rects: list[dict[str, Any]] = []
    for coupon in coupons:
        body_rects.append(coupon["base_rect"])
        body_rects.append(coupon["scrub_rect"])
        body_rects.append(coupon["soak_rect"])
        body_rects.extend(coupon["index_rects"])
    x_min = min(float(rect["x"]) for rect in body_rects)
    y_min = min(float(rect["y"]) for rect in body_rects)
    z_min = min(float(rect["z"]) for rect in body_rects)
    x_max = max(float(rect["x"]) + float(rect["length_x"]) for rect in body_rects)
    y_max = max(float(rect["y"]) + float(rect["width_y"]) for rect in body_rects)
    z_max = max(float(rect["z"]) + float(rect["height_z"]) for rect in body_rects)
    representative_parts = sorted(
        {
            part
            for coupon in coupons
            for part in coupon["representative_parts"]
        }
    )
    fabrication_sources = sorted(
        {
            source
            for coupon in coupons
            for source in coupon["fabrication_sources"]
        }
    )
    evidence_gates = sorted(
        {
            gate
            for coupon in coupons
            for gate in coupon["evidence_gates"]
        }
    )
    exposure_classes = sorted({str(coupon["exposure_class"]) for coupon in coupons})
    service_dispositions = sorted(
        {str(coupon["service_disposition"]) for coupon in coupons}
    )
    length = x_max - x_min
    width = y_max - y_min
    height = z_max - z_min
    return {
        "name": "material_cleaning_witness_coupon",
        "role": "validation-only same-material exposure and cleaning witness set",
        "validation": "required_gate1_same_material_cleaning_witness_evidence",
        "failure_rule": (
            "unverified_same_material_cleaning_or_exposure_blocks_gate1_pass"
        ),
        "evidence_gate": "Gate 1 Print QC",
        "cad_value": (
            f"{len(coupons)} coupons / {len(representative_parts)} represented parts / "
            f"{length:.2f} x {width:.2f} x {height:.2f} mm"
        ),
        "x": round(x_min, 3),
        "y": round(y_min, 3),
        "z": round(z_min, 3),
        "length_x": round(length, 3),
        "width_y": round(width, 3),
        "height_z": round(height, 3),
        "coupon_count": len(coupons),
        "body_rect_count": len(body_rects),
        "representative_part_count": len(representative_parts),
        "representative_parts": tuple(representative_parts),
        "fabrication_sources": tuple(fabrication_sources),
        "evidence_gates": tuple(evidence_gates),
        "exposure_classes": tuple(exposure_classes),
        "service_dispositions": tuple(service_dispositions),
        "source_layout_checks": [
            "material_cleaning_witness_coupons",
            "row_coupon_part_manifest",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "same_material_cleaning_compatibility",
            "wet_exposed_reusable_parts_cleaned_for_operation",
            "dry_service_parts_safe_after_cleaning",
            "normal_ot2_operation_after_cleaning",
        ],
        "coupons": coupons,
        "body_rects": body_rects,
    }


def _material_cleaning_witness_coupons_for_policy(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    manifest = row_coupon_part_manifest()
    installed = manifest["installed"]
    cleaning_dispositions = {
        "printed_reusable_cleaning_pending",
        "replaceable_elastomer_or_tpu_cleaning_pending",
    }
    grouped: dict[tuple[str, str], list[str]] = {}
    for part_name, entry in installed.items():
        disposition = str(entry["service_disposition"])
        if disposition not in cleaning_dispositions:
            continue
        key = (str(entry["exposure_class"]), disposition)
        grouped.setdefault(key, []).append(part_name)

    coupon_params = params.get("material_witness_coupon", {})
    coupon_len = float(coupon_params.get("length_x", 38.0))
    coupon_wid = float(coupon_params.get("width_y", 10.0))
    coupon_h = float(coupon_params.get("height_z", 1.2))
    coupon_gap_y = float(coupon_params.get("gap_y", 3.0))
    scrub_len = float(coupon_params.get("scrub_strip_length_x", 14.0))
    scrub_wid = float(coupon_params.get("scrub_strip_width_y", 2.0))
    scrub_h = float(coupon_params.get("scrub_strip_height_z", 0.35))
    soak_len = float(coupon_params.get("soak_pad_length_x", 10.0))
    soak_wid = float(coupon_params.get("soak_pad_width_y", 5.0))
    soak_h = float(coupon_params.get("soak_pad_height_z", 0.25))
    index_pad = float(coupon_params.get("index_pad_xy", 1.0))
    index_gap = float(coupon_params.get("index_pad_gap_x", 0.55))
    x0 = (
        float(layout["length_x"])
        + float(params.get("consumable_metrology", {}).get("viewer_offset_x", 18.0))
        + float(coupon_params.get("viewer_offset_x", 55.0))
    )

    coupons: list[dict[str, Any]] = []
    for coupon_index, ((exposure_class, disposition), part_names) in enumerate(
        sorted(grouped.items()),
        start=1,
    ):
        y0 = (coupon_index - 1) * (coupon_wid + coupon_gap_y)
        base_rect = {
            "name": f"material_cleaning_coupon_{coupon_index:02d}_base",
            "x": round(x0, 3),
            "y": round(y0, 3),
            "z": 0.0,
            "length_x": round(coupon_len, 3),
            "width_y": round(coupon_wid, 3),
            "height_z": round(coupon_h, 3),
        }
        scrub_rect = {
            "name": f"material_cleaning_coupon_{coupon_index:02d}_scrub_strip",
            "x": round(x0 + 2.0, 3),
            "y": round(y0 + coupon_wid - scrub_wid - 2.0, 3),
            "z": round(coupon_h, 3),
            "length_x": round(scrub_len, 3),
            "width_y": round(scrub_wid, 3),
            "height_z": round(scrub_h, 3),
        }
        soak_rect = {
            "name": f"material_cleaning_coupon_{coupon_index:02d}_soak_pad",
            "x": round(x0 + coupon_len - soak_len - 2.0, 3),
            "y": round(y0 + 2.0, 3),
            "z": round(coupon_h, 3),
            "length_x": round(soak_len, 3),
            "width_y": round(soak_wid, 3),
            "height_z": round(soak_h, 3),
        }
        index_rects = [
            {
                "name": f"material_cleaning_coupon_{coupon_index:02d}_index_{pad_idx:02d}",
                "x": round(x0 + 2.0 + (pad_idx - 1) * (index_pad + index_gap), 3),
                "y": round(y0 + 2.0, 3),
                "z": round(coupon_h, 3),
                "length_x": round(index_pad, 3),
                "width_y": round(index_pad, 3),
                "height_z": round(soak_h, 3),
            }
            for pad_idx in range(1, coupon_index + 1)
        ]
        part_entries = [installed[name] for name in part_names]
        coupons.append(
            {
                "name": f"material_cleaning_witness_coupon_{coupon_index:02d}",
                "role": "same_material_cleaning_and_exposure_witness",
                "exposure_class": exposure_class,
                "service_disposition": disposition,
                "representative_parts": tuple(sorted(part_names)),
                "representative_part_count": len(part_names),
                "fabrication_sources": tuple(
                    sorted({str(entry["fabrication_source"]) for entry in part_entries})
                ),
                "evidence_gates": tuple(
                    sorted({str(entry["material_evidence_gate"]) for entry in part_entries})
                ),
                "base_rect": base_rect,
                "scrub_rect": scrub_rect,
                "soak_rect": soak_rect,
                "index_rects": tuple(index_rects),
                "index_code": coupon_index,
                "validation": (
                    "coupon_requires_same_material_cleaning_soak_scrub_and_bsl1_review"
                ),
            }
        )
    return coupons


def _printability_support_cleanup_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    side_gas_service_interfaces: list[dict[str, Any]],
    wedge_lock_rectangles: list[dict[str, Any]],
    wet_dry_failure_paths: dict[str, list[dict[str, Any]]],
    dry_bay_ingress_audit_rects: list[dict[str, Any]],
    gas_sensor_pcb_mounts: list[dict[str, Any]],
    headspace_sht41_mounts: list[dict[str, Any]],
    ir_sensor_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    from aevum_cad.row_coupon import (ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS)
    metrology = params.get("consumable_metrology", {})
    check_params = params.get("printability_support_cleanup_check", {})
    slab_len = float(check_params.get("length_x", 64.0))
    slab_wid = float(check_params.get("width_y", 80.0))
    slab_h = float(check_params.get("height_z", 0.45))
    tab_len = float(check_params.get("tab_length_x", 52.0))
    tab_wid = float(check_params.get("tab_width_y", 6.0))
    tab_h = float(check_params.get("tab_height_z", 0.75))
    tab_gap = float(check_params.get("tab_gap_y", 2.0))
    x0 = (
        float(layout["length_x"])
        + float(metrology.get("viewer_offset_x", 18.0))
        + float(check_params.get("viewer_offset_x", 330.0))
    )
    y0 = max((float(layout["width_y"]) - slab_wid) / 2, 0.0)
    printed_part_count = sum(
        1
        for entry in row_coupon_part_manifest()["installed"].values()
        if entry["fabrication_source"] == "printed_polymer"
    )
    sensor_pocket_count = (
        len(gas_sensor_pcb_mounts)
        + len(headspace_sht41_mounts)
        + len(ir_sensor_mounts)
    )
    gutter_count = len(wet_dry_failure_paths["wet_dry_witness_gutters"])
    dry_bay_audit_count = len(dry_bay_ingress_audit_rects)
    split_source_count = len(ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS)
    checkpoints = [
        {
            "name": "gasket_lands_support_scar_free",
            "blocks": ["gasket_land_support_scar_or_lift_unchecked"],
            "source_validation_checks": ["gasket_compression_gap_gauge"],
            "inspection_method": "straightedge_feeler_gauge_visual",
            "evidence_gate": "Gate 1 Print QC",
            "cad_value": "upper and lower gasket lands",
        },
        {
            "name": "wedge_slide_paths_free_of_support_debris",
            "blocks": ["wedge_slide_or_detent_support_debris_unchecked"],
            "source_layout_checks": ["wedge_lock_rectangles"],
            "source_validation_checks": ["latch_retention_span_check"],
            "inspection_method": "manual_slide_and_visual_cleanup_check",
            "evidence_gate": "Gate 1 Print QC",
            "cad_value": f"{len(wedge_lock_rectangles)} wedge lock bodies",
        },
        {
            "name": "side_gas_barbs_bores_open",
            "blocks": ["side_gas_barb_bore_or_stem_support_blockage_unchecked"],
            "source_layout_checks": ["side_gas_service_interfaces"],
            "source_validation_checks": ["side_gas_tube_envelope_check"],
            "inspection_method": "visual_bore_and_tube_seat_check",
            "evidence_gate": "Gate 1 Print QC",
            "cad_value": f"{len(side_gas_service_interfaces)} side gas interfaces",
        },
        {
            "name": "sensor_pockets_support_free",
            "blocks": ["sensor_pocket_support_debris_or_trim_unchecked"],
            "source_validation_checks": ["sensor_installation_path_check"],
            "inspection_method": "blank_insert_visual_fit_check",
            "evidence_gate": "Gate 1 Print QC",
            "cad_value": f"{sensor_pocket_count} sensor pockets",
        },
        {
            "name": "dry_bay_gutters_unbridged",
            "blocks": ["dry_bay_gutter_or_threshold_support_bridge_unchecked"],
            "source_validation_checks": [
                "wet_dry_failure_path_check",
                "dry_bay_ingress_audit_check",
            ],
            "inspection_method": "visual_witness_path_cleanup_check",
            "evidence_gate": "Gate 1 Print QC",
            "cad_value": f"{gutter_count} gutters / {dry_bay_audit_count} audit rects",
        },
        {
            "name": "split_segment_edges_do_not_remove_authority_features",
            "blocks": ["split_segment_cleanup_authority_feature_loss_unchecked"],
            "source_validation_checks": [
                "operating_service_dress_check",
                "row_tiling_service_clearance_check",
            ],
            "inspection_method": "split_segment_edge_visual_check",
            "evidence_gate": "Gate 1 Print QC",
            "cad_value": f"{split_source_count} split-source printed parts",
        },
    ]
    blockers = sorted(
        {
            block
            for checkpoint in checkpoints
            for block in checkpoint["blocks"]
        }
    )
    source_validation_checks = sorted(
        {
            source
            for checkpoint in checkpoints
            for source in checkpoint.get("source_validation_checks", [])
        }
    )
    source_layout_checks = sorted(
        {
            source
            for checkpoint in checkpoints
            for source in checkpoint.get("source_layout_checks", [])
        }
    )
    base_rect = {
        "name": "printability_support_cleanup_evidence_slab",
        "x": round(x0, 3),
        "y": round(y0, 3),
        "z": 0.0,
        "length_x": round(slab_len, 3),
        "width_y": round(slab_wid, 3),
        "height_z": round(slab_h, 3),
    }
    body_rects = [base_rect]
    for index, checkpoint in enumerate(checkpoints):
        tab_y = y0 + 2.0 + index * (tab_wid + tab_gap)
        body_rects.append(
            {
                "name": f"printability_support_cleanup_tab_{index + 1:02d}",
                "x": round(x0 + 2.0, 3),
                "y": round(tab_y, 3),
                "z": round(slab_h, 3),
                "length_x": round(tab_len, 3),
                "width_y": round(tab_wid, 3),
                "height_z": round(tab_h, 3),
            }
        )
        checkpoint["index"] = index + 1
        checkpoint["blocks_print_qc_pass"] = True

    return {
        "name": "printability_support_cleanup_check",
        "role": "validation-only first-print support cleanup evidence checklist",
        "validation": "required_gate1_printability_cleanup_evidence",
        "failure_rule": (
            "support_scar_debris_blockage_or_split_edge_feature_loss_blocks_gate1_pass"
        ),
        "evidence_gate": "Gate 1 Print QC",
        "cad_value": (
            f"{len(checkpoints)} checks / {printed_part_count} printed parts / "
            f"{len(side_gas_service_interfaces)} gas interfaces"
        ),
        "checkpoint_count": len(checkpoints),
        "printed_part_count": printed_part_count,
        "side_gas_interface_count": len(side_gas_service_interfaces),
        "sensor_pocket_count": sensor_pocket_count,
        "wet_dry_witness_gutter_count": gutter_count,
        "dry_bay_ingress_audit_rect_count": dry_bay_audit_count,
        "split_source_part_count": split_source_count,
        "checkpoints": checkpoints,
        "blockers": blockers,
        "source_layout_checks": source_layout_checks,
        "source_validation_checks": source_validation_checks,
        "requires_physical_evidence": True,
        "all_checkpoints_block_gate1_pass": True,
        "body_rects": body_rects,
    }


def build_consumable_metrology_gauge(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["consumable_metrology_gauge"]
    x_shift = 0.0 if assembly_position else -float(spec["x"])
    y_shift = 0.0 if assembly_position else -float(spec["y"])
    z_shift = 0.0 if assembly_position else -float(spec["z"])
    base = spec["base_rect"]
    x0 = float(base["x"]) + x_shift
    y0 = float(base["y"]) + y_shift
    z0 = float(base["z"]) + z_shift

    gauge = _rounded_box(
        float(base["length_x"]),
        float(base["width_y"]),
        float(base["height_z"]),
        float(spec["corner_radius"]),
    ).translate((x0, y0, z0))
    top_z = z0 + float(base["height_z"])

    plate_pocket = spec["plate_pocket_rect"]
    plate_pocket_depth = float(plate_pocket["height_z"])
    if plate_pocket_depth > 0:
        gauge = gauge.cut(
            cq.Workplane("XY")
            .box(
                float(plate_pocket["length_x"]),
                float(plate_pocket["width_y"]),
                plate_pocket_depth + 0.05,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(plate_pocket["x"]) + x_shift,
                    float(plate_pocket["y"]) + y_shift,
                    float(plate_pocket["z"]) + z_shift,
                )
            )
        )

    mat_pocket = spec["mat_pocket_rect"]
    mat_pocket_depth = float(mat_pocket["height_z"])
    if mat_pocket_depth > 0:
        gauge = gauge.cut(
            cq.Workplane("XY")
            .box(
                float(mat_pocket["length_x"]),
                float(mat_pocket["width_y"]),
                mat_pocket_depth + 0.05,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(mat_pocket["x"]) + x_shift,
                    float(mat_pocket["y"]) + y_shift,
                    float(mat_pocket["z"]) + z_shift,
                )
            )
        )

    plug_depth = float(spec["plug_pocket_depth_z"])
    if plug_depth > 0:
        centers = [
            (float(center["x"]) + x_shift, float(center["y"]) + y_shift)
            for center in spec["plug_pocket_centers"]
        ]
        plug_pockets = (
            cq.Workplane("XY")
            .pushPoints(centers)
            .circle(float(spec["plug_pocket_diameter"]) / 2)
            .extrude(plug_depth + 0.05)
            .translate((0, 0, top_z - plug_depth))
        )
        gauge = gauge.cut(plug_pockets)

    return gauge


def build_fail_closed_prerun_inspection_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["fail_closed_prerun_inspection_check"]
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("fail-closed pre-run inspection check requires rectangles")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_gasket_tab_leak_witness_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["gasket_tab_leak_witness_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -layout["base_top_z"]
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_material_cleaning_witness_coupon(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["material_cleaning_witness_coupon"]
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("material cleaning witness coupon requires coupons")
    x_shift = 0.0 if assembly_position else -float(spec["x"])
    y_shift = 0.0 if assembly_position else -float(spec["y"])
    z_shift = 0.0 if assembly_position else -float(spec["z"])
    shifted_rects = [
        {
            **rect,
            "x": round(float(rect["x"]) + x_shift, 3),
            "y": round(float(rect["y"]) + y_shift, 3),
        }
        for rect in rects
    ]
    return _boxes_from_rectangles(shifted_rects, z_shift=z_shift)


def build_printability_support_cleanup_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["printability_support_cleanup_check"]
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("printability support cleanup check requires rectangles")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)
