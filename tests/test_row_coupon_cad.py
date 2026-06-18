from __future__ import annotations

import math
from collections import Counter
from copy import deepcopy
from pathlib import Path

import cadquery as cq
import pytest

import aevum_cad.row_coupon as row_coupon_module
from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon import (
    ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS,
    ROW_COUPON_SERVICE_MODES,
    build_adjacent_deck_slot_keepout_check,
    build_adjacent_slot_service_collision_review,
    build_assembly_debris_review,
    build_assembly_state_witness_check,
    build_consumable_metrology_gauge,
    build_cots_gas_service_tubes,
    build_deck_frame_keepout_check,
    build_deck_module_unseated_review,
    build_deck_pod_seating_repeatability_check,
    build_deck_pods,
    build_deck_pose_repeatability_review,
    build_deck_slot_footprint_check,
    build_dry_bay_boundary_check,
    build_dry_bay_envelope_check,
    build_dry_bay_ingress_audit_check,
    build_dry_bay_obstruction_review,
    build_electrical_connector_mating_state_check,
    build_fail_closed_prerun_inspection_check,
    build_flow_test_adapters,
    build_gas_pcb_flow_cell_check,
    build_gas_pcb_interface_gaskets,
    build_gas_sensor_pcbs,
    build_gasket_compression_gap_gauge,
    build_gasket_squeeze_out_of_range_review,
    build_gasket_tab_leak_witness_check,
    build_headspace_barrier_check,
    build_headspace_sht41_microcarriers,
    build_headspace_volume_check,
    build_ir_thermopile_face_gaskets,
    build_ir_thermopile_fov_spot_check,
    build_ir_thermopiles,
    build_latch_mechanism_demo_parts,
    build_latch_retention_span_check,
    build_latch_unseated_witnesses,
    build_lid_cover,
    build_lid_harness_cover,
    build_lid_manifold_shell,
    build_lid_sensor_harness,
    build_lid_sensor_service_cable_pigtails,
    build_lid_sensor_service_connectors,
    build_lower_gasket,
    build_lower_harness_cover,
    build_lower_sensor_harness,
    build_lower_sensor_service_cable_pigtail,
    build_lower_sensor_service_connector,
    build_material_cleaning_witness_coupon,
    build_microplates,
    build_misdressed_service_bundle_review,
    build_missing_gas_pcb_cartridge_witnesses,
    build_missing_local_sensor_witnesses,
    build_missing_microplate_witnesses,
    build_missing_perimeter_gasket_witnesses,
    build_missing_septum_mat_witnesses,
    build_missing_service_lead_witnesses,
    build_observer_carriage_envelope_check,
    build_observer_fiducial_focus_target_check,
    build_observer_front_end_swept_body_check,
    build_observer_infinity_port_datum_check,
    build_observer_kinematic_split_check,
    build_observer_optical_stability_check,
    build_observer_service_raceway_envelope_check,
    build_operating_service_dress_check,
    build_pipette_puncture_swept_path_check,
    build_pipette_toolhead_swept_body_check,
    build_plate_support_frame,
    build_printability_support_cleanup_check,
    build_printed_gas_pcb_keeper_doors,
    build_printed_sample_relief_cap,
    build_printed_wedge_locks,
    build_row_coupon_installed_parts,
    build_row_coupon_production_y_split_parts,
    build_row_coupon_service_parts,
    build_row_coupon_validation_parts,
    build_row_tiling_service_clearance_check,
    build_sample_relief_leak_witness_check,
    build_sensor_connector_service_clearance_check,
    build_sensor_installation_path_check,
    build_sensor_service_cable_envelope_check,
    build_septum_mat_inserts,
    build_side_gas_leak_witness_check,
    build_side_gas_tube_envelope_check,
    build_thermal_condensation_proxy_check,
    build_unmated_sensor_service_connectors_review,
    build_unseated_gas_pcb_cartridges_review,
    build_unseated_side_gas_tubes_review,
    build_unseated_wedge_locks_review,
    build_upper_gasket,
    build_well_cell_plane_check,
    build_wet_chamber_frame,
    build_wet_dry_failure_path_check,
    export_row_coupon,
    export_row_coupon_production_y_split_parts,
    export_row_coupon_validation_tools,
    row_coupon_layout,
    row_coupon_part_manifest,
    row_coupon_production_y_split_plan,
)

PARAMS = ROOT / "cad" / "one_row_coupon.params.json"


def _rectangles_overlap(
    ax: float,
    ay: float,
    aw: float,
    ah: float,
    bx: float,
    by: float,
    bw: float,
    bh: float,
) -> bool:
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def _rectangle_overlaps_circle(
    *,
    rect_x: float,
    rect_y: float,
    rect_w: float,
    rect_h: float,
    circle_x: float,
    circle_y: float,
    radius: float,
) -> bool:
    closest_x = min(max(circle_x, rect_x), rect_x + rect_w)
    closest_y = min(max(circle_y, rect_y), rect_y + rect_h)
    return (closest_x - circle_x) ** 2 + (closest_y - circle_y) ** 2 <= radius**2


def _septum_access_window_for_tile_for_test(
    tile: dict[str, float | int],
    params: dict,
) -> tuple[float, float, float, float]:
    grid = params["well_grid"]
    mat = params["septum_mat"]
    access = params["pipette_access"]
    min_x = tile["x"] + grid["first_well_center_x"]
    max_x = min_x + (grid["columns"] - 1) * grid["pitch_x"]
    min_y = tile["y"] + grid["first_well_center_y"]
    max_y = min_y + (grid["rows"] - 1) * grid["pitch_y"]
    margin = mat["round_plug_diameter"] / 2 + access["septum_window_clearance_xy"]
    return min_x - margin, min_y - margin, max_x - min_x + 2 * margin, max_y - min_y + 2 * margin


def test_row_coupon_layout_has_four_ot2_column_positions() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    plate = params["plate"]
    row = params["row"]
    dry_bay = params["dry_bay"]
    deck = params["deck_interface"]
    observer = params["observer_robotics"]

    assert len(layout["tile_origins"]) == 4
    assert layout["row_axis"] == "y"
    assert layout["tile_pitch_y"] == params["deck_interface"]["slot_pitch_y"]
    assert layout["length_x"] == (
        row["end_margin_x"] * 2 + plate["length_x"]
    )
    assert layout["width_y"] == (
        row["side_margin_y"] * 2
        + 4 * plate["width_y"]
        + 3 * row["inter_tile_gap_y"]
    )
    assert layout["dry_bay_envelope"]["width_y"] > 4 * dry_bay["aperture_width_y"]
    assert layout["dry_bay_envelope"]["top_z"] == 0.0
    assert layout["deck_plane_z"] == -(
        deck["standoff_height_z"] + deck["slot_shoe_thickness_z"]
    )
    assert (
        layout["observer_carriage_envelope_check"]["z"]
        + layout["observer_carriage_envelope_check"]["height_z"]
        <= -observer["carriage_top_clearance_z"]
    )
    assert layout["observer_service_raceway_envelope_check"]["x"] > (
        layout["dry_bay_envelope"]["x"] + layout["dry_bay_envelope"]["length_x"]
    )
    swept = layout["observer_front_end_swept_body_check"]
    assert swept["x"] >= layout["dry_bay_envelope"]["x"]
    assert swept["y"] >= layout["dry_bay_envelope"]["y"]
    assert (
        swept["x"] + swept["length_x"]
        <= layout["dry_bay_envelope"]["x"] + layout["dry_bay_envelope"]["length_x"]
    )
    assert (
        swept["y"] + swept["width_y"]
        <= layout["dry_bay_envelope"]["y"] + layout["dry_bay_envelope"]["width_y"]
    )
    assert swept["z"] >= layout["dry_bay_envelope"]["bottom_z"]
    assert swept["z"] + swept["height_z"] <= layout["dry_bay_envelope"]["top_z"]
    assert layout["wet_chamber_skirt"]["x"] == 0.0
    assert layout["wet_chamber_skirt"]["y"] == 0.0
    assert layout["wet_chamber_skirt"]["length_x"] == layout["length_x"]
    assert layout["wet_chamber_skirt"]["width_y"] == layout["width_y"]
    assert len(layout["deck_engagement_feet"]) == 4 * len(layout["tile_origins"])
    assert len(layout["plate_locator_rails"]) == 4 * len(layout["tile_origins"])
    assert len(layout["latch_post_positions"]) == len(layout["wedge_lock_rectangles"])
    assert layout["pipette_puncture_swept_path"]["well_count"] == (
        row["plate_count"] * params["well_grid"]["columns"] * params["well_grid"]["rows"]
    )


def test_deck_feet_stay_outside_observer_sweep() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    deck = params["deck_interface"]
    dry = layout["dry_bay_envelope"]

    for tile in layout["tile_origins"]:
        slot_x = tile["x"] + (
            params["plate"]["length_x"] - deck["slot_opening_length_x"]
        ) / 2
        slot_y = tile["y"] + (
            params["plate"]["width_y"] - deck["slot_opening_width_y"]
        ) / 2
        tile_feet = [
            foot
            for foot in layout["deck_engagement_feet"]
            if foot["tile_index"] == tile["index"]
        ]
        assert len(tile_feet) == 4
        for foot in tile_feet:
            assert slot_x <= foot["x"]
            assert foot["x"] + foot["length_x"] <= slot_x + deck["slot_opening_length_x"]
            assert slot_y <= foot["y"]
            assert foot["y"] + foot["width_y"] <= slot_y + deck["slot_opening_width_y"]
            assert not _rectangles_overlap(
                foot["x"],
                foot["y"],
                foot["length_x"],
                foot["width_y"],
                dry["x"],
                dry["y"],
                dry["length_x"],
                dry["width_y"],
            )


def test_deck_pod_seating_repeatability_check_requires_gate3_evidence() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    spec = layout["deck_pod_seating_repeatability_check"]
    slot_spec = layout["deck_slot_footprint_check"]
    frame_spec = layout["deck_frame_keepout_check"]
    rect = spec["body_rects"][0]
    slot_check = build_deck_slot_footprint_check(
        params,
        assembly_position=True,
    ).val()
    frame_check = build_deck_frame_keepout_check(
        params,
        assembly_position=True,
    ).val()
    check = build_deck_pod_seating_repeatability_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()

    assert "deck_slot_footprint_check" in validation
    assert "deck_slot_footprint_check" not in installed
    assert "deck_frame_keepout_check" in validation
    assert "deck_frame_keepout_check" not in installed
    assert slot_spec["evidence_gate"] == "Gate 3 OT-2 placement"
    assert slot_spec["validation"] == "required_gate3_deck_slot_footprint_evidence"
    assert slot_spec["failure_rule"] == (
        "slot_mismatch_or_unmeasured_deck_engagement_blocks_ot2_placement_pass"
    )
    assert slot_spec["cad_value"] == "4 slots / 130.00 x 359.50 x 0.80 mm"
    assert slot_spec["slot_count"] == len(layout["tile_origins"])
    assert slot_spec["requires_physical_evidence"] is True
    assert "normal_ot2_deck_slot_engagement" in slot_spec[
        "physical_claims_blocked"
    ]
    assert len(slot_spec["body_rects"]) == len(layout["tile_origins"])
    assert frame_spec["evidence_gate"] == "Gate 3 OT-2 placement"
    assert frame_spec["validation"] == "required_gate3_deck_frame_keepout_evidence"
    assert frame_spec["failure_rule"] == (
        "deck_frame_contact_or_unmeasured_frame_keepout_blocks_ot2_placement_pass"
    )
    assert frame_spec["cad_value"] == "148.60 x 377.25 x 2.50 mm / 4 slot cutouts"
    assert frame_spec["slot_cutout_count"] == len(layout["tile_origins"])
    assert frame_spec["requires_physical_evidence"] is True
    assert "normal_ot2_deck_frame_clearance" in frame_spec[
        "physical_claims_blocked"
    ]
    assert frame_spec["frame_rect"]["length_x"] == layout["length_x"]
    assert len(frame_spec["slot_cut_rects"]) == len(layout["tile_origins"])
    assert "deck_pod_seating_repeatability_check" in validation
    assert "deck_pod_seating_repeatability_check" not in installed
    assert spec["validation"] == (
        "cad_proxy_deck_pod_repeatability_physical_evidence_required"
    )
    assert spec["failure_rule"] == (
        "rocking_yaw_wear_or_frame_contact_blocks_ot2_operation_until_gate3_evidence"
    )
    assert spec["evidence_gate"] == "Gate 3 OT-2 placement"
    assert spec["checkpoint_count"] == 5
    assert spec["cad_value"] == "16 feet / 16 keys / 4 slots / 5 cycles"
    assert spec["deck_foot_count"] == len(layout["deck_engagement_feet"])
    assert spec["pod_frame_key_count"] == len(layout["deck_pod_frame_keys"])
    assert spec["deck_slot_count"] == len(layout["tile_origins"])
    assert spec["seat_release_cycles"] == 5
    assert spec["requires_physical_evidence"] is True
    assert spec["all_checkpoints_block_ot2_operation"] is True
    assert "normal_ot2_deck_seating" in spec["physical_claims_blocked"]
    assert {
        "deck_frame_contact_unverified",
        "deck_pod_repeat_seating_unproven",
        "dry_bay_debris_after_pod_cycle_unchecked",
        "pod_frame_key_or_shoe_wear_unchecked",
        "rocking_or_yaw_unmeasured",
    } == set(spec["blockers"])
    assert {
        "deck_engagement_feet",
        "deck_pod_frame_keys",
        "dry_bay_envelope",
    } == set(spec["source_layout_checks"])
    assert {
        "deck_frame_keepout_check",
        "deck_slot_footprint_check",
        "dry_bay_ingress_audit_check",
    } == set(spec["source_validation_checks"])
    assert spec["slot_shoe_clearance_xy"] == params["deck_interface"][
        "slot_shoe_clearance_xy"
    ]
    assert spec["foot_slot_clearance_xy"] == params["deck_interface"][
        "foot_slot_clearance_xy"
    ]
    assert spec["pod_frame_key_clearance_xy"] == params["production_assembly"][
        "pod_frame_key_clearance_xy"
    ]
    assert spec["dry_bay_protected_footprint"]["length_x"] == layout[
        "dry_bay_envelope"
    ]["length_x"]
    assert round(slot_check.BoundingBox().zmin, 2) == round(
        layout["deck_plane_z"] - params["deck_interface"][
            "deck_slot_footprint_check_thickness_z"
        ],
        2,
    )
    assert round(frame_check.BoundingBox().xlen, 2) == round(layout["length_x"], 2)
    assert round(frame_check.BoundingBox().ylen, 2) == round(layout["width_y"], 2)
    assert len(check.Solids()) == 1
    assert rect["x"] > layout["length_x"]
    assert round(check_bb.xlen, 2) == rect["length_x"]
    assert round(check_bb.ylen, 2) == rect["width_y"]
    assert round(check_bb.zmax, 2) == rect["height_z"]


def test_deck_module_unseated_is_opt_in_gate3_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    unseated_state = build_row_coupon_service_parts(params, mode="deck_module_unseated")
    installed_part_names = set(installed)
    lift_z = params["production_assembly"].get("deck_module_unseated_lift_z", 12.0)

    assert "deck_module_unseated" in ROW_COUPON_SERVICE_MODES
    assert "deck_module_unseated_review" not in installed
    assert "deck_module_unseated_review" not in validation
    assert installed_part_names.issubset(unseated_state)
    assert set(unseated_state) - installed_part_names == {"deck_module_unseated_review"}

    installed_deck_bb = installed["deck_pods"].val().BoundingBox()
    unseated_deck_bb = unseated_state["deck_pods"].val().BoundingBox()
    installed_frame_bb = installed["plate_support_frame"].val().BoundingBox()
    unseated_frame_bb = unseated_state["plate_support_frame"].val().BoundingBox()
    assert round(unseated_deck_bb.zmin - installed_deck_bb.zmin, 2) == round(lift_z, 2)
    assert round(unseated_frame_bb.zmin - installed_frame_bb.zmin, 2) == round(
        lift_z,
        2,
    )

    review = unseated_state["deck_module_unseated_review"].val()
    direct_review = build_deck_module_unseated_review(
        params,
        assembly_position=True,
    ).val()
    assert review.Volume() > 0
    assert round(review.BoundingBox().zmax, 2) == round(
        direct_review.BoundingBox().zmax,
        2,
    )

    review_rects = layout["deck_module_unseated_review"]
    assert len(review_rects) == len(layout["deck_engagement_feet"])
    feet_by_xy = {
        (foot["tile_index"], foot["x"], foot["y"]): foot
        for foot in layout["deck_engagement_feet"]
    }
    for rect in review_rects:
        foot = feet_by_xy[(rect["tile_index"], rect["x"], rect["y"])]
        assert rect["review_state"] == "deck_module_unseated"
        assert rect["retained_part"] == "deck_pods"
        assert rect["witness_kind"] == "deck_engagement_foot_seating_footprint"
        assert rect["x"] == foot["x"]
        assert rect["y"] == foot["y"]
        assert rect["length_x"] == foot["length_x"]
        assert rect["width_y"] == foot["width_y"]
        assert rect["unseated_offset_z"] == lift_z


def test_deck_pose_repeatability_unproven_is_opt_in_gate3_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    reviewed = build_row_coupon_service_parts(
        params,
        mode="deck_pose_repeatability_unproven",
    )
    installed_part_names = set(installed)
    rects = layout["deck_pose_repeatability_review"]
    check = layout["deck_pod_seating_repeatability_check"]
    review = reviewed["deck_pose_repeatability_review"].val()
    direct_review = build_deck_pose_repeatability_review(
        params,
        assembly_position=True,
    ).val()
    deck_checkpoint = next(
        checkpoint
        for checkpoint in layout["fail_closed_prerun_inspection_check"]["checkpoints"]
        if checkpoint["name"] == "deck_module_seated"
    )

    assert "deck_pose_repeatability_unproven" in ROW_COUPON_SERVICE_MODES
    assert "deck_pose_repeatability_review" not in installed
    assert "deck_pose_repeatability_review" not in validation
    assert installed_part_names.issubset(reviewed)
    assert set(reviewed) - installed_part_names == {"deck_pose_repeatability_review"}
    assert review.Volume() > 0
    assert round(review.BoundingBox().zmax, 2) == round(
        direct_review.BoundingBox().zmax,
        2,
    )

    assert len(rects) == 2 * len(layout["deck_engagement_feet"])
    assert {rect["review_state"] for rect in rects} == {
        "deck_pose_repeatability_unproven"
    }
    assert {rect["retained_part"] for rect in rects} == {"deck_pods"}
    assert {rect["witness_kind"] for rect in rects} == {
        "repeat_seat_cycle_unproven_footprint",
        "rocking_or_yaw_unmeasured_sweep",
    }
    assert {rect["blocked_fail_closed_state"] for rect in rects} == {
        "deck_pod_repeat_seating_unproven",
        "rocking_or_yaw_unmeasured",
    }
    assert {
        "deck_pod_repeat_seating_unproven",
        "rocking_or_yaw_unmeasured",
    } == set(rects[0]["blocked_fail_closed_states"])
    assert {
        "deck_slot_footprint_check",
        "deck_frame_keepout_check",
        "deck_pod_seating_repeatability_check",
    } == set(rects[0]["source_validation_checks"])
    assert {rect["seat_release_cycles_required"] for rect in rects} == {
        check["seat_release_cycles"]
    }
    assert "deck_pose_repeatability_unproven" in deck_checkpoint["blocks"]

    feet_by_tile = {
        (foot["tile_index"], foot["x"], foot["y"]): foot
        for foot in layout["deck_engagement_feet"]
    }
    for rect in rects:
        if rect["witness_kind"] == "repeat_seat_cycle_unproven_footprint":
            matching_feet = [
                foot
                for foot in feet_by_tile.values()
                if rect["tile_index"] == foot["tile_index"]
                and rect["x"] <= foot["x"]
                and rect["y"] <= foot["y"]
                and rect["x"] + rect["length_x"] >= foot["x"] + foot["length_x"]
                and rect["y"] + rect["width_y"] >= foot["y"] + foot["width_y"]
            ]
        else:
            matching_feet = [
                foot
                for foot in feet_by_tile.values()
                if rect["tile_index"] == foot["tile_index"]
                and rect["x"] <= foot["x"]
                and rect["x"] + rect["length_x"] >= foot["x"] + foot["length_x"]
                and _rectangles_overlap(
                    rect["x"],
                    rect["y"],
                    rect["length_x"],
                    rect["width_y"],
                    foot["x"],
                    foot["y"],
                    foot["length_x"],
                    foot["width_y"],
                )
            ]
        assert matching_feet


def test_row_coupon_stack_height_is_explicit() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    port_boss_height_z = max(
        float(port["boss_height_z"]) for port in layout["lid_port_positions"]
    )
    expected = (
        params["base"]["thickness_z"]
        + params["plate_support"]["land_height_z"]
        + params["plate"]["height_z"]
        + params["seal_interface"]["compressed_gasket_height_z"]
        + params["lid_manifold"]["thickness_z"]
        + port_boss_height_z
    )
    expected = max(
        expected,
        layout["latch_post_head_top_z"],
        layout["port_cap_top_z"],
        *(float(service["top_z"]) for service in layout["side_gas_service_interfaces"]),
    )
    expected = max(
        expected,
        *(
            mount["z"] + mount["height_z"]
            for mount in (
                layout["gas_sensor_pcb_mounts"]
                + layout["headspace_sht41_mounts"]
                + layout["ir_sensor_mounts"]
            )
        ),
    )

    assert math.isclose(layout["assembly_top_z"], expected)
    assert layout["assembly_envelope_z"] == (
        expected
        + params["deck_interface"]["standoff_height_z"]
        + params["deck_interface"]["slot_shoe_thickness_z"]
    )


def test_legacy_compound_builders_are_not_public_production_api() -> None:
    assert not hasattr(row_coupon_module, "build_row_coupon_base")
    assert not hasattr(row_coupon_module, "build_lid_manifold")


def test_observer_validation_api_uses_exported_check_names() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)

    assert not hasattr(row_coupon_module, "build_observer_module_swept_body_check")
    assert not hasattr(row_coupon_module, "build_observer_carriage_envelope")
    assert not hasattr(row_coupon_module, "build_observer_service_raceway_envelope")
    assert "observer_front_end_swept_body_check" in layout
    assert "observer_carriage_envelope_check" in layout
    assert "observer_service_raceway_envelope_check" in layout
    assert "observer_module_swept_body" not in layout
    assert "observer_carriage_envelope" not in layout
    assert "observer_service_raceway_envelope" not in layout


def test_installed_parts_match_production_assembly_tree() -> None:
    params = load_params(PARAMS)
    parts = build_row_coupon_installed_parts(params)

    assert list(parts) == [
        "deck_pods",
        "plate_support_frame",
        "ir_thermopiles",
        "ir_thermopile_face_gaskets",
        "lower_sensor_harness",
        "lower_harness_cover",
        "lower_sensor_service_connector",
        "printed_lower_sensor_connector_shroud",
        "lower_sensor_service_cable_pigtail",
        "lower_gasket",
        "wet_chamber_frame",
        "cots_microplates",
        "cots_septum_mats",
        "upper_gasket",
        "lid_manifold_shell",
        "headspace_sht41_microcarriers",
        "lid_sensor_harness",
        "lid_harness_cover",
        "lid_sensor_service_connectors",
        "printed_lid_sensor_connector_shrouds",
        "lid_sensor_service_cable_pigtails",
        "lid_cover",
        "cots_gas_service_tubes",
        "gas_pcb_interface_gaskets",
        "printed_gas_pcb_keeper_doors",
        "gas_sensor_pcbs",
        "printed_sample_relief_cap",
        "printed_wedge_locks",
    ]
    assert "base" not in parts
    assert "lid_manifold" not in parts


def test_part_manifest_covers_all_visible_operating_and_review_geometry() -> None:
    params = load_params(PARAMS)
    manifest = row_coupon_part_manifest()
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)

    assert manifest["policy"]["assembly_rule"] == (
        "print_native_screwless_no_glue_where_possible"
    )
    assert manifest["policy"]["material_authority_decision_date"] == "2026-06-04"
    assert manifest["policy"]["material_authority_decision"] == (
        "first_print_row_coupon_print_native_no_hidden_authority"
    )
    assert manifest["policy"]["supersedes_material_strategy"] == (
        "2026-05-06_printed_architecture_with_authority_inserts_for_this_coupon"
    )
    allowed_sources = set(manifest["policy"]["allowed_installed_fabrication_sources"])
    allowed_nonprinted_sources = set(
        manifest["policy"]["allowed_nonprinted_installed_sources"]
    )
    allowed_exposures = set(manifest["policy"]["allowed_exposure_classes"])
    allowed_dispositions = set(manifest["policy"]["allowed_service_dispositions"])
    forbidden_authority_terms = set(
        manifest["policy"]["forbidden_retention_authority_terms"]
    )
    assert list(manifest["installed"]) == list(installed)
    assert set(manifest["validation"]) == set(validation)
    assert set(manifest["service_modes"]) | set(manifest["review_modes"]) == set(
        ROW_COUPON_SERVICE_MODES
    )

    for name, entry in manifest["installed"].items():
        assert name in installed
        assert entry["role"]
        assert entry["fabrication_source"]
        assert entry["fabrication_source"] in allowed_sources
        assert entry["visibility"] in {
            "installed_operating",
            "installed_internal_electronics",
        }
        assert "glue" in entry["retention"]
        assert "screw" not in entry["retention"] or "no_screws" in entry["retention"]
        assert not any(
            term in entry["retention"] for term in forbidden_authority_terms
        )
        assert entry["exposure_class"] in allowed_exposures
        assert entry["service_disposition"] in allowed_dispositions
        assert "Gate " in entry["material_evidence_gate"] or entry[
            "material_evidence_gate"
        ].startswith("install inventory")
        if entry["fabrication_source"] != "printed_polymer":
            assert entry["fabrication_source"] in allowed_nonprinted_sources

    assert manifest["installed"]["lid_manifold_shell"]["exposure_class"] == (
        "wet_headspace_boundary"
    )
    assert manifest["installed"]["cots_microplates"]["service_disposition"] == (
        "disposable_cots_consumable"
    )
    assert manifest["installed"]["lower_sensor_harness"]["exposure_class"] == (
        "dry_electrical_service"
    )

    for name, entry in manifest["validation"].items():
        assert name in validation
        assert name not in installed
        assert entry["fabrication_source"] == "validation_only_geometry"
        assert entry["visibility"] == "validation_overlay"
        assert entry["retention"] == "not_installed_in_production_tree"

    installed_names = set(installed)
    for mode, entry in manifest["review_modes"].items():
        state = build_row_coupon_service_parts(params, mode=mode)
        removed = set(entry["removed_parts"])
        review_parts = set(entry["review_parts"])
        assert entry["role"]
        assert installed_names - set(state) == removed
        assert set(state) - installed_names == review_parts
        assert review_parts.isdisjoint(manifest["installed"])
        assert review_parts.isdisjoint(manifest["validation"])


def test_sample_relief_cap_manifest_matches_lip_and_seat_seal() -> None:
    params = load_params(PARAMS)
    manifest = row_coupon_part_manifest()
    layout = row_coupon_layout(params)
    cap_entry = manifest["installed"]["printed_sample_relief_cap"]
    port = layout["lid_port_positions"][0]

    assert cap_entry["role"] == "normally installed sample/relief port closure"
    assert cap_entry["fabrication_source"] == "printed_polymer"
    assert cap_entry["retention"] == "printed_annular_lip_in_lid_seat_no_screws_no_glue"
    assert "friction" not in cap_entry["retention"]
    assert port["cap_seal_lip_role"] == (
        "integrated_compliant_lip_on_sample_relief_boss_top"
    )
    assert port["cap_seal_lip_seat_depth_z"] > 0


def test_export_names_match_production_assembly_tree(monkeypatch, tmp_path) -> None:
    params = load_params(PARAMS)
    exported: list[str] = []

    def fake_export(_model: cq.Workplane, path: str) -> None:
        output = Path(path)
        output.touch()
        exported.append(output.name)

    def fake_assembly_export(_assembly: cq.Assembly, path: str) -> None:
        output = Path(path)
        output.touch()
        exported.append(output.name)

    monkeypatch.setattr(cq.exporters, "export", fake_export)
    monkeypatch.setattr(cq.Assembly, "export", fake_assembly_export)

    paths = export_row_coupon(params, tmp_path)

    assert list(paths) == [
        "deck_pods_stl",
        "deck_pods_step",
        "plate_support_frame_stl",
        "plate_support_frame_step",
        "ir_thermopiles_stl",
        "ir_thermopiles_step",
        "ir_thermopile_face_gaskets_stl",
        "ir_thermopile_face_gaskets_step",
        "lower_sensor_harness_stl",
        "lower_sensor_harness_step",
        "lower_harness_cover_stl",
        "lower_harness_cover_step",
        "lower_sensor_service_connector_stl",
        "lower_sensor_service_connector_step",
        "printed_lower_sensor_connector_shroud_stl",
        "printed_lower_sensor_connector_shroud_step",
        "lower_sensor_service_cable_pigtail_stl",
        "lower_sensor_service_cable_pigtail_step",
        "lower_gasket_stl",
        "lower_gasket_step",
        "wet_chamber_frame_stl",
        "wet_chamber_frame_step",
        "cots_microplates_stl",
        "cots_microplates_step",
        "cots_septum_mats_stl",
        "cots_septum_mats_step",
        "upper_gasket_stl",
        "upper_gasket_step",
        "lid_manifold_shell_stl",
        "lid_manifold_shell_step",
        "headspace_sht41_microcarriers_stl",
        "headspace_sht41_microcarriers_step",
        "lid_sensor_harness_stl",
        "lid_sensor_harness_step",
        "lid_harness_cover_stl",
        "lid_harness_cover_step",
        "lid_sensor_service_connectors_stl",
        "lid_sensor_service_connectors_step",
        "printed_lid_sensor_connector_shrouds_stl",
        "printed_lid_sensor_connector_shrouds_step",
        "lid_sensor_service_cable_pigtails_stl",
        "lid_sensor_service_cable_pigtails_step",
        "lid_cover_stl",
        "lid_cover_step",
        "cots_gas_service_tubes_stl",
        "cots_gas_service_tubes_step",
        "gas_pcb_interface_gaskets_stl",
        "gas_pcb_interface_gaskets_step",
        "printed_gas_pcb_keeper_doors_stl",
        "printed_gas_pcb_keeper_doors_step",
        "gas_sensor_pcbs_stl",
        "gas_sensor_pcbs_step",
        "printed_sample_relief_cap_stl",
        "printed_sample_relief_cap_step",
        "printed_wedge_locks_stl",
        "printed_wedge_locks_step",
        "assembly_step",
    ]
    assert len(exported) == 57
    assert all(path.exists() for path in paths.values())
    assert not (tmp_path / f"{params['name']}_base.step").exists()
    assert not (tmp_path / f"{params['name']}_lid_manifold.step").exists()
    assert not any("witness" in name or "review" in name or "missing" in name for name in exported)


def test_validation_tool_export_is_separate_from_production_tree(monkeypatch, tmp_path) -> None:
    params = load_params(PARAMS)
    exported: list[str] = []

    def fake_export(_model: cq.Workplane, path: str) -> None:
        output = Path(path)
        output.touch()
        exported.append(output.name)

    monkeypatch.setattr(cq.exporters, "export", fake_export)

    paths = export_row_coupon_validation_tools(params, tmp_path)

    assert list(paths) == [
        "consumable_metrology_gauge_stl",
        "consumable_metrology_gauge_step",
        "deck_slot_footprint_check_stl",
        "deck_slot_footprint_check_step",
        "deck_frame_keepout_check_stl",
        "deck_frame_keepout_check_step",
        "deck_pod_seating_repeatability_check_stl",
        "deck_pod_seating_repeatability_check_step",
        "dry_bay_envelope_check_stl",
        "dry_bay_envelope_check_step",
        "dry_bay_boundary_check_stl",
        "dry_bay_boundary_check_step",
        "headspace_barrier_check_stl",
        "headspace_barrier_check_step",
        "headspace_volume_check_stl",
        "headspace_volume_check_step",
        "well_cell_plane_check_stl",
        "well_cell_plane_check_step",
        "ir_thermopile_fov_spot_check_stl",
        "ir_thermopile_fov_spot_check_step",
        "thermal_condensation_proxy_check_stl",
        "thermal_condensation_proxy_check_step",
        "pipette_puncture_swept_path_check_stl",
        "pipette_puncture_swept_path_check_step",
        "pipette_toolhead_swept_body_check_stl",
        "pipette_toolhead_swept_body_check_step",
        "observer_front_end_swept_body_check_stl",
        "observer_front_end_swept_body_check_step",
        "observer_infinity_port_datum_check_stl",
        "observer_infinity_port_datum_check_step",
        "observer_carriage_envelope_check_stl",
        "observer_carriage_envelope_check_step",
        "observer_service_raceway_envelope_check_stl",
        "observer_service_raceway_envelope_check_step",
        "observer_fiducial_focus_target_check_stl",
        "observer_fiducial_focus_target_check_step",
        "observer_optical_stability_check_stl",
        "observer_optical_stability_check_step",
        "observer_kinematic_split_check_stl",
        "observer_kinematic_split_check_step",
        "assembly_state_witness_check_stl",
        "assembly_state_witness_check_step",
        "gasket_compression_gap_gauge_stl",
        "gasket_compression_gap_gauge_step",
        "latch_retention_span_check_stl",
        "latch_retention_span_check_step",
        "fail_closed_prerun_inspection_check_stl",
        "fail_closed_prerun_inspection_check_step",
        "printability_support_cleanup_check_stl",
        "printability_support_cleanup_check_step",
        "material_cleaning_witness_coupon_stl",
        "material_cleaning_witness_coupon_step",
        "wet_dry_failure_path_check_stl",
        "wet_dry_failure_path_check_step",
        "sensor_installation_path_check_stl",
        "sensor_installation_path_check_step",
        "sensor_connector_service_clearance_check_stl",
        "sensor_connector_service_clearance_check_step",
        "sensor_service_cable_envelope_check_stl",
        "sensor_service_cable_envelope_check_step",
        "electrical_connector_mating_state_check_stl",
        "electrical_connector_mating_state_check_step",
        "operating_service_dress_check_stl",
        "operating_service_dress_check_step",
        "row_tiling_service_clearance_check_stl",
        "row_tiling_service_clearance_check_step",
        "gas_pcb_flow_cell_check_stl",
        "gas_pcb_flow_cell_check_step",
        "side_gas_tube_envelope_check_stl",
        "side_gas_tube_envelope_check_step",
        "side_gas_leak_witness_check_stl",
        "side_gas_leak_witness_check_step",
        "sample_relief_leak_witness_check_stl",
        "sample_relief_leak_witness_check_step",
        "gasket_tab_leak_witness_check_stl",
        "gasket_tab_leak_witness_check_step",
        "dry_bay_ingress_audit_check_stl",
        "dry_bay_ingress_audit_check_step",
        "adjacent_deck_slot_keepout_check_stl",
        "adjacent_deck_slot_keepout_check_step",
        "latch_demo_lower_catch_stl",
        "latch_demo_lower_catch_step",
        "latch_demo_compressed_gasket_stl",
        "latch_demo_compressed_gasket_step",
        "latch_demo_upper_receiver_stl",
        "latch_demo_upper_receiver_step",
        "latch_demo_sliding_wedge_stl",
        "latch_demo_sliding_wedge_step",
    ]
    assert exported == [
        f"{params['name']}_validation_consumable_metrology_gauge.stl",
        f"{params['name']}_validation_consumable_metrology_gauge.step",
        f"{params['name']}_validation_deck_slot_footprint_check.stl",
        f"{params['name']}_validation_deck_slot_footprint_check.step",
        f"{params['name']}_validation_deck_frame_keepout_check.stl",
        f"{params['name']}_validation_deck_frame_keepout_check.step",
        f"{params['name']}_validation_deck_pod_seating_repeatability_check.stl",
        f"{params['name']}_validation_deck_pod_seating_repeatability_check.step",
        f"{params['name']}_validation_dry_bay_envelope_check.stl",
        f"{params['name']}_validation_dry_bay_envelope_check.step",
        f"{params['name']}_validation_dry_bay_boundary_check.stl",
        f"{params['name']}_validation_dry_bay_boundary_check.step",
        f"{params['name']}_validation_headspace_barrier_check.stl",
        f"{params['name']}_validation_headspace_barrier_check.step",
        f"{params['name']}_validation_headspace_volume_check.stl",
        f"{params['name']}_validation_headspace_volume_check.step",
        f"{params['name']}_validation_well_cell_plane_check.stl",
        f"{params['name']}_validation_well_cell_plane_check.step",
        f"{params['name']}_validation_ir_thermopile_fov_spot_check.stl",
        f"{params['name']}_validation_ir_thermopile_fov_spot_check.step",
        f"{params['name']}_validation_thermal_condensation_proxy_check.stl",
        f"{params['name']}_validation_thermal_condensation_proxy_check.step",
        f"{params['name']}_validation_pipette_puncture_swept_path_check.stl",
        f"{params['name']}_validation_pipette_puncture_swept_path_check.step",
        f"{params['name']}_validation_pipette_toolhead_swept_body_check.stl",
        f"{params['name']}_validation_pipette_toolhead_swept_body_check.step",
        f"{params['name']}_validation_observer_front_end_swept_body_check.stl",
        f"{params['name']}_validation_observer_front_end_swept_body_check.step",
        f"{params['name']}_validation_observer_infinity_port_datum_check.stl",
        f"{params['name']}_validation_observer_infinity_port_datum_check.step",
        f"{params['name']}_validation_observer_carriage_envelope_check.stl",
        f"{params['name']}_validation_observer_carriage_envelope_check.step",
        f"{params['name']}_validation_observer_service_raceway_envelope_check.stl",
        f"{params['name']}_validation_observer_service_raceway_envelope_check.step",
        f"{params['name']}_validation_observer_fiducial_focus_target_check.stl",
        f"{params['name']}_validation_observer_fiducial_focus_target_check.step",
        f"{params['name']}_validation_observer_optical_stability_check.stl",
        f"{params['name']}_validation_observer_optical_stability_check.step",
        f"{params['name']}_validation_observer_kinematic_split_check.stl",
        f"{params['name']}_validation_observer_kinematic_split_check.step",
        f"{params['name']}_validation_assembly_state_witness_check.stl",
        f"{params['name']}_validation_assembly_state_witness_check.step",
        f"{params['name']}_validation_gasket_compression_gap_gauge.stl",
        f"{params['name']}_validation_gasket_compression_gap_gauge.step",
        f"{params['name']}_validation_latch_retention_span_check.stl",
        f"{params['name']}_validation_latch_retention_span_check.step",
        f"{params['name']}_validation_fail_closed_prerun_inspection_check.stl",
        f"{params['name']}_validation_fail_closed_prerun_inspection_check.step",
        f"{params['name']}_validation_printability_support_cleanup_check.stl",
        f"{params['name']}_validation_printability_support_cleanup_check.step",
        f"{params['name']}_validation_material_cleaning_witness_coupon.stl",
        f"{params['name']}_validation_material_cleaning_witness_coupon.step",
        f"{params['name']}_validation_wet_dry_failure_path_check.stl",
        f"{params['name']}_validation_wet_dry_failure_path_check.step",
        f"{params['name']}_validation_sensor_installation_path_check.stl",
        f"{params['name']}_validation_sensor_installation_path_check.step",
        f"{params['name']}_validation_sensor_connector_service_clearance_check.stl",
        f"{params['name']}_validation_sensor_connector_service_clearance_check.step",
        f"{params['name']}_validation_sensor_service_cable_envelope_check.stl",
        f"{params['name']}_validation_sensor_service_cable_envelope_check.step",
        f"{params['name']}_validation_electrical_connector_mating_state_check.stl",
        f"{params['name']}_validation_electrical_connector_mating_state_check.step",
        f"{params['name']}_validation_operating_service_dress_check.stl",
        f"{params['name']}_validation_operating_service_dress_check.step",
        f"{params['name']}_validation_row_tiling_service_clearance_check.stl",
        f"{params['name']}_validation_row_tiling_service_clearance_check.step",
        f"{params['name']}_validation_gas_pcb_flow_cell_check.stl",
        f"{params['name']}_validation_gas_pcb_flow_cell_check.step",
        f"{params['name']}_validation_side_gas_tube_envelope_check.stl",
        f"{params['name']}_validation_side_gas_tube_envelope_check.step",
        f"{params['name']}_validation_side_gas_leak_witness_check.stl",
        f"{params['name']}_validation_side_gas_leak_witness_check.step",
        f"{params['name']}_validation_sample_relief_leak_witness_check.stl",
        f"{params['name']}_validation_sample_relief_leak_witness_check.step",
        f"{params['name']}_validation_gasket_tab_leak_witness_check.stl",
        f"{params['name']}_validation_gasket_tab_leak_witness_check.step",
        f"{params['name']}_validation_dry_bay_ingress_audit_check.stl",
        f"{params['name']}_validation_dry_bay_ingress_audit_check.step",
        f"{params['name']}_validation_adjacent_deck_slot_keepout_check.stl",
        f"{params['name']}_validation_adjacent_deck_slot_keepout_check.step",
        f"{params['name']}_validation_latch_demo_lower_catch.stl",
        f"{params['name']}_validation_latch_demo_lower_catch.step",
        f"{params['name']}_validation_latch_demo_compressed_gasket.stl",
        f"{params['name']}_validation_latch_demo_compressed_gasket.step",
        f"{params['name']}_validation_latch_demo_upper_receiver.stl",
        f"{params['name']}_validation_latch_demo_upper_receiver.step",
        f"{params['name']}_validation_latch_demo_sliding_wedge.stl",
        f"{params['name']}_validation_latch_demo_sliding_wedge.step",
    ]
    assert all(path.exists() for path in paths.values())


def test_production_base_split_preserves_support_and_deck_interfaces() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    deck_pods_bb = build_deck_pods(params).val().BoundingBox()
    support_frame_bb = build_plate_support_frame(params).val().BoundingBox()
    key_h = params["production_assembly"]["pod_frame_key_height_z"]
    locator_h = params["plate_support"]["lateral_locator_wall_height_z"]
    lower_stack_zmin = min(deck_pods_bb.zmin, support_frame_bb.zmin)
    lower_stack_zmax = max(deck_pods_bb.zmax, support_frame_bb.zmax)

    assert round(deck_pods_bb.zmin, 2) == round(layout["deck_plane_z"], 2)
    assert round(deck_pods_bb.zmax, 2) == key_h
    assert round(support_frame_bb.zmin, 2) == 0.0
    assert round(support_frame_bb.zmax, 2) == round(
        layout["plate_bottom_z"] + locator_h,
        2,
    )
    assert round(lower_stack_zmin, 2) == round(layout["deck_plane_z"], 2)
    assert round(lower_stack_zmax, 2) == round(
        layout["plate_bottom_z"] + locator_h,
        2,
    )
    intersection_volume = sum(
        shape.Volume()
        for shape in build_deck_pods(params).intersect(
            build_plate_support_frame(params)
        ).vals()
    )
    assert intersection_volume == 0.0


def test_production_y_split_plan_tracks_first_print_oversized_parts() -> None:
    params = load_params(PARAMS)
    plan = row_coupon_production_y_split_plan(params)
    layout = row_coupon_layout(params)
    expected_split_y = (
        layout["tile_origins"][1]["y"]
        + params["plate"]["width_y"]
        + layout["tile_origins"][2]["y"]
    ) / 2

    assert len(plan) == len(ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS) * 2
    assert {row["source_part"] for row in plan} == set(
        ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS
    )
    assert {row["interface_zone"] for row in plan} == {"between_plate_2_and_3"}
    assert {row["segment_count"] for row in plan} == {2}
    assert {row["y_max"] for row in plan if row["segment_index"] == 1} == {
        round(expected_split_y, 3)
    }
    assert {row["y_min"] for row in plan if row["segment_index"] == 2} == {
        round(expected_split_y, 3)
    }
    assert all("without screws or glue" in row["retention"] for row in plan)
    assert all("Gate 4 dye evidence" in row["sealing"] for row in plan)


def test_production_y_split_parts_fit_selected_mk4_bed_envelope() -> None:
    params = load_params(PARAMS)
    split_parts = build_row_coupon_production_y_split_parts(params)

    assert set(split_parts) == {
        f"{part}_y{segment:02d}_of_02"
        for part in ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS
        for segment in (1, 2)
    }
    for name, part in split_parts.items():
        bb = part.val().BoundingBox()
        assert bb.xlen > 0, name
        assert bb.ylen > 0, name
        assert bb.zlen > 0, name
        assert bb.xlen <= 250.0, name
        assert bb.ylen <= 210.0, name


def test_export_y_split_parts_uses_dedicated_first_print_names(
    monkeypatch,
    tmp_path,
) -> None:
    params = load_params(PARAMS)
    exported: list[str] = []

    def fake_export(_model: cq.Workplane, path: str) -> None:
        output = Path(path)
        output.touch()
        exported.append(output.name)

    monkeypatch.setattr(cq.exporters, "export", fake_export)

    paths = export_row_coupon_production_y_split_parts(params, tmp_path)

    assert len(paths) == len(ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS) * 4
    assert "deck_pods_y01_of_02_stl" in paths
    assert "deck_pods_y02_of_02_step" in paths
    assert (
        f"{params['name']}_plate_support_frame_y01_of_02.stl"
        in exported
    )
    assert f"{params['name']}_lid_cover_y02_of_02.step" in exported
    assert "assembly_step" not in paths


def test_support_frame_has_no_generic_top_datum_pockets_in_lower_seal_land() -> None:
    params = load_params(PARAMS)
    source = (ROOT / "src" / "aevum_cad" / "row_coupon.py").read_text()

    assert "fiducials" not in params
    assert "insert_pockets" not in params
    assert "_cut_fiducials" not in source
    assert "_cut_insert_pockets" not in source
    assert "insert_pockets" not in source
    assert params["dry_bay"]["observer_fiducial_depth"] > 0
    assert "_cut_observer_fiducials" in source


def test_manifest_roles_do_not_describe_visible_geometry_as_placeholders() -> None:
    manifest = row_coupon_part_manifest()
    forbidden = ("placeholder", "stub", "abstract")

    entries = [
        *manifest["installed"].items(),
        *manifest["validation"].items(),
    ]
    for name, entry in entries:
        visible_text = " ".join([name, *[str(value) for value in entry.values()]])
        assert not any(term in visible_text.lower() for term in forbidden)


def test_microplates_sit_on_integral_support_frame_lands() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    locator_h = params["plate_support"]["lateral_locator_wall_height_z"]
    support_frame_bb = build_plate_support_frame(params).val().BoundingBox()
    microplate_bb = build_microplates(params, assembly_position=True).val().BoundingBox()

    assert round(support_frame_bb.zmax, 2) == round(
        layout["plate_bottom_z"] + locator_h,
        2,
    )
    assert round(microplate_bb.zmin, 2) == round(layout["plate_bottom_z"], 2)
    assert round(microplate_bb.zmax, 2) == round(layout["plate_top_z"], 2)
    intersection_volume = sum(
        shape.Volume()
        for shape in build_plate_support_frame(params)
        .intersect(build_microplates(params, assembly_position=True))
        .vals()
    )
    assert intersection_volume == 0.0


def test_microplates_include_published_cellvis_well_openings() -> None:
    params = load_params(PARAMS)
    solid_deck_params = deepcopy(params)
    solid_deck_params["plate"]["upper_well_diameter"] = 0.0
    plate = params["plate"]
    grid = params["well_grid"]
    mat = params["septum_mat"]
    microplates = build_microplates(params, assembly_position=True).val()
    solid_deck_microplates = build_microplates(
        solid_deck_params,
        assembly_position=True,
    ).val()
    microplate_bb = microplates.BoundingBox()
    septum = build_septum_mat_inserts(params, assembly_position=True)

    assert plate["profile_source"].startswith("CellVis P96-1.5H-N published profile")
    assert plate["upper_well_diameter"] == 6.8
    assert plate["lower_well_diameter"] == 6.21
    assert plate["well_bottom_area_equivalent_diameter"] == 6.18
    assert plate["well_top_recess_depth_z"] == 0.47
    assert plate["upper_well_diameter"] > mat["round_plug_diameter"]
    assert grid["columns"] * grid["rows"] == 96
    assert microplates.Volume() < solid_deck_microplates.Volume()
    assert round(microplate_bb.zmax, 2) == round(row_coupon_layout(params)["plate_top_z"], 2)

    intersection_volume = sum(
        shape.Volume()
        for shape in build_microplates(params, assembly_position=True)
        .intersect(septum)
        .vals()
    )
    assert intersection_volume == 0.0


def test_well_cell_plane_check_marks_published_biology_target_plane() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    plate = params["plate"]
    grid = params["well_grid"]
    spec = layout["well_cell_plane_check"]
    validation = build_row_coupon_validation_parts(params)
    check = build_well_cell_plane_check(params, assembly_position=True).val()
    check_bb = check.BoundingBox()
    expected_count = params["row"]["plate_count"] * grid["columns"] * grid["rows"]
    thickness = plate["cell_plane_check_thickness_z"]
    expected_volume = (
        expected_count
        * math.pi
        * (plate["well_bottom_area_equivalent_diameter"] / 2) ** 2
        * thickness
    )

    assert "well_cell_plane_check" in validation
    assert "well_cell_plane_check" not in build_row_coupon_installed_parts(params)
    assert spec["evidence_gate"] == "Gate 6 sensor/thermal"
    assert spec["cad_value"] == "384 wells / 6.18 mm / z=11.80 mm"
    assert spec["failure_rule"] == (
        "unverified_cell_plane_reference_blocks_thermal_or_biology_claims"
    )
    assert spec["requires_physical_evidence"] is True
    assert "cell_temperature_claims" in spec["physical_claims_blocked"]
    assert len(spec["body_targets"]) == expected_count
    assert len(check.Solids()) == expected_count
    assert check.Volume() == pytest.approx(expected_volume, rel=0.01)
    assert round(check_bb.zlen, 2) == thickness
    assert round(check_bb.zmin, 2) == round(
        layout["plate_top_z"] - plate["plate_top_to_cell_plane_depth_z"] - thickness / 2,
        2,
    )
    assert round(check_bb.zmax, 2) == round(
        layout["plate_top_z"] - plate["plate_top_to_cell_plane_depth_z"] + thickness / 2,
        2,
    )
    assert check_bb.zmin > layout["plate_bottom_z"]
    assert check_bb.zmax < layout["plate_top_z"]


def test_ir_thermopile_fov_spot_check_marks_plate_margin_proxy() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    plate = params["plate"]
    grid = params["well_grid"]
    thickness = params["sensor_harness"]["ir_fov_spot_check_thickness_z"]
    mounts = layout["ir_sensor_mounts"]
    spec = layout["ir_thermopile_fov_spot_check"]
    validation = build_row_coupon_validation_parts(params)
    check = build_ir_thermopile_fov_spot_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()

    assert "ir_thermopile_fov_spot_check" in validation
    assert "ir_thermopile_fov_spot_check" not in build_row_coupon_installed_parts(params)
    assert spec["evidence_gate"] == "Gate 6 sensor/thermal"
    assert spec["cad_value"] == "4 spots / 1.08 mm at plate margin / 12.00 deg FOV"
    assert spec["spot_cad_value"] == "1.08 mm at plate margin, 12.00 deg FOV"
    assert spec["failure_rule"] == (
        "unverified_ir_plate_margin_proxy_blocks_cell_temperature_claims"
    )
    assert spec["requires_physical_evidence"] is True
    assert "ir_cell_temperature_claims" in spec["physical_claims_blocked"]
    assert len(spec["body_targets"]) == len(mounts)
    assert len(check.Solids()) == len(mounts)
    expected_volume = sum(
        math.pi * (float(mount["fov_spot_diameter"]) / 2) ** 2 * thickness
        for mount in mounts
    )
    assert check.Volume() == pytest.approx(expected_volume, rel=0.01)
    assert round(check_bb.zlen, 3) == round(thickness, 3)
    assert round(check_bb.zmin, 3) == round(layout["plate_bottom_z"] - thickness / 2, 3)
    assert round(check_bb.zmax, 3) == round(layout["plate_bottom_z"] + thickness / 2, 3)

    cell_radius = plate["well_bottom_area_equivalent_diameter"] / 2
    for mount in mounts:
        spot_radius = float(mount["fov_spot_diameter"]) / 2
        well_grid_rect = mount["well_grid_rect"]
        tile = layout["tile_origins"][mount["tile_index"] - 1]
        assert tile["x"] <= mount["center_x"] - spot_radius
        assert mount["center_x"] + spot_radius <= well_grid_rect["x"]
        assert tile["y"] <= mount["center_y"] - spot_radius
        assert mount["center_y"] + spot_radius <= tile["y"] + params["plate"]["width_y"]
        for column in range(grid["columns"]):
            for row in range(grid["rows"]):
                well_x = tile["x"] + grid["first_well_center_x"] + column * grid["pitch_x"]
                well_y = tile["y"] + grid["first_well_center_y"] + row * grid["pitch_y"]
                center_distance = math.hypot(
                    float(mount["center_x"]) - well_x,
                    float(mount["center_y"]) - well_y,
                )
                assert center_distance > spot_radius + cell_radius


def test_thermal_condensation_proxy_check_maps_gate6_proxy_points() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    plate = params["plate"]
    grid = params["well_grid"]
    production = params["production_assembly"]
    targets = layout["thermal_condensation_proxy_targets"]
    spec = layout["thermal_condensation_proxy_check"]
    validation = build_row_coupon_validation_parts(params)
    check = build_thermal_condensation_proxy_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()
    target_counts = Counter(target["kind"] for target in targets)

    assert "thermal_condensation_proxy_check" in validation
    assert "thermal_condensation_proxy_check" not in build_row_coupon_installed_parts(
        params
    )
    assert spec["evidence_gate"] == "Gate 6 sensor/thermal"
    assert spec["cad_value"] == (
        "4 center refs / 4 IR proxies / 4 SHT41 points / 4 condensation pockets"
    )
    assert spec["failure_rule"] == (
        "unverified_thermal_proxy_or_condensation_path_blocks_sensor_thermal_pass"
    )
    assert spec["requires_physical_evidence"] is True
    assert "powered_sensor_thermal_readiness" in spec["physical_claims_blocked"]
    assert spec["body_targets"] == targets
    assert target_counts == {
        "cell_plane_center_reference": params["row"]["plate_count"],
        "ir_plate_margin_proxy_spot": params["row"]["plate_count"],
        "sht41_headspace_aperture_drip_ring": params["row"]["plate_count"],
        "condensation_pocket_low_point": 4,
    }
    assert len(layout["condensation_pocket_rects"]) == 4
    assert len(check.Solids()) == len(targets)

    expected_volume = 0.0
    for target in targets:
        if target["shape"] == "disk":
            expected_volume += (
                math.pi
                * (float(target["diameter"]) / 2) ** 2
                * float(target["height_z"])
            )
        else:
            expected_volume += (
                float(target["length_x"])
                * float(target["width_y"])
                * float(target["height_z"])
            )
    assert check.Volume() == pytest.approx(expected_volume, rel=0.01)
    assert round(check_bb.zmin, 3) == min(round(float(t["z"]), 3) for t in targets)
    assert round(check_bb.zmax, 3) == max(
        round(float(t["z"]) + float(t["height_z"]), 3) for t in targets
    )

    ir_mounts_by_tile = {
        mount["tile_index"]: mount for mount in layout["ir_sensor_mounts"]
    }
    sht_mounts_by_tile = {
        mount["tile_index"]: mount for mount in layout["headspace_sht41_mounts"]
    }
    targets_by_name = {target["name"]: target for target in targets}
    cell_thickness = plate["cell_plane_check_thickness_z"]
    cell_plane_z = layout["plate_top_z"] - plate["plate_top_to_cell_plane_depth_z"]
    ir_thickness = params["sensor_harness"]["ir_fov_spot_check_thickness_z"]
    for tile in layout["tile_origins"]:
        tile_index = tile["index"]
        center = targets_by_name[f"thermal_cell_plane_center_tile_{tile_index}"]
        assert center["x"] == pytest.approx(
            tile["x"]
            + grid["first_well_center_x"]
            + (grid["columns"] - 1) * grid["pitch_x"] / 2
        )
        assert center["y"] == pytest.approx(
            tile["y"]
            + grid["first_well_center_y"]
            + (grid["rows"] - 1) * grid["pitch_y"] / 2
        )
        assert center["z"] == pytest.approx(cell_plane_z - cell_thickness / 2)
        assert center["diameter"] == plate["well_bottom_area_equivalent_diameter"]

        ir_target = targets_by_name[f"thermal_ir_proxy_spot_tile_{tile_index}"]
        ir_mount = ir_mounts_by_tile[tile_index]
        assert ir_target["x"] == ir_mount["center_x"]
        assert ir_target["y"] == ir_mount["center_y"]
        assert ir_target["z"] == pytest.approx(
            layout["plate_bottom_z"] - ir_thickness / 2
        )
        assert ir_target["diameter"] == ir_mount["fov_spot_diameter"]

        sht_target = targets_by_name[f"thermal_sht41_headspace_point_tile_{tile_index}"]
        sht_mount = sht_mounts_by_tile[tile_index]
        ring = sht_mount["drip_break_ring"]
        assert sht_target["x"] == sht_mount["aperture_x"]
        assert sht_target["y"] == sht_mount["aperture_y"]
        assert sht_target["z"] == ring["z"]
        assert sht_target["diameter"] == ring["outer_diameter"]
        assert sht_target["aperture_diameter"] == sht_mount["aperture_diameter"]

    pocket_targets = {
        target["name"]: target
        for target in targets
        if target["kind"] == "condensation_pocket_low_point"
    }
    for pocket in layout["condensation_pocket_rects"]:
        pocket_target = pocket_targets[pocket["name"]]
        assert pocket_target["x"] == pocket["x"]
        assert pocket_target["y"] == pocket["y"]
        assert pocket_target["z"] == pytest.approx(layout["base_top_z"] + 0.05)
        assert pocket_target["center_x"] == pocket["center_x"]
        assert pocket_target["center_y"] == pocket["center_y"]
        assert pocket_target["length_x"] == production["condensation_pocket_length_x"]
        assert pocket_target["width_y"] == production["condensation_pocket_width_y"]
        assert pocket_target["nominal_depth_z"] == production[
            "condensation_pocket_depth_z"
        ]


def test_plate_locator_rails_capture_edges_without_trapping_vertical_loading() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    plate = params["plate"]
    support = params["plate_support"]
    wall_h = support["lateral_locator_wall_height_z"]
    clearance = support["lateral_locator_clearance_xy"]

    for tile in layout["tile_origins"]:
        rails = [
            rail
            for rail in layout["plate_locator_rails"]
            if rail["tile_index"] == tile["index"]
        ]
        assert len(rails) == 4
        plate_x = tile["x"]
        plate_y = tile["y"]
        for rail in rails:
            assert round(float(rail["z"]), 2) == round(layout["plate_bottom_z"], 2)
            assert round(float(rail["height_z"]), 2) == wall_h
            assert not _rectangles_overlap(
                float(rail["x"]),
                float(rail["y"]),
                float(rail["length_x"]),
                float(rail["width_y"]),
                plate_x,
                plate_y,
                plate["length_x"],
                plate["width_y"],
            )
            assert float(rail["x"]) >= 0.0
            assert float(rail["y"]) >= 0.0
            assert float(rail["x"]) + float(rail["length_x"]) <= layout["length_x"]
            assert float(rail["y"]) + float(rail["width_y"]) <= layout["width_y"]

        capture_x0 = min(float(rail["x"]) for rail in rails)
        capture_y0 = min(float(rail["y"]) for rail in rails)
        capture_x1 = max(float(rail["x"]) + float(rail["length_x"]) for rail in rails)
        capture_y1 = max(float(rail["y"]) + float(rail["width_y"]) for rail in rails)
        assert capture_x0 < plate_x - clearance
        assert capture_y0 < plate_y - clearance
        assert capture_x1 > plate_x + plate["length_x"] + clearance
        assert capture_y1 > plate_y + plate["width_y"] + clearance


def test_wet_chamber_frame_encloses_microplates_without_trapping_insertion() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    frame_bb = build_wet_chamber_frame(params, assembly_position=True).val().BoundingBox()
    microplate_bb = build_microplates(params, assembly_position=True).val().BoundingBox()

    assert round(frame_bb.zmin, 2) == round(layout["base_top_z"], 2)
    assert round(frame_bb.zmax, 2) == round(layout["latch_post_head_top_z"], 2)
    assert round(microplate_bb.zmax, 2) == round(layout["gasket_bottom_z"], 2)
    assert round(frame_bb.xmin, 2) == 0.0
    assert round(frame_bb.ymin, 2) == 0.0
    assert round(frame_bb.xlen, 2) == round(layout["length_x"], 2)
    assert round(frame_bb.ylen, 2) == round(layout["width_y"], 2)
    assert frame_bb.xmin < microplate_bb.xmin
    assert frame_bb.xmax > microplate_bb.xmax
    assert frame_bb.ymin < microplate_bb.ymin
    assert frame_bb.ymax > microplate_bb.ymax


def test_lid_leaves_septum_well_field_open_to_pipette_axis() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    lid_shell = build_lid_manifold_shell(params)
    lid_cover = build_lid_cover(params).translate(
        (0, 0, params["lid_manifold"]["thickness_z"])
    )
    grid = params["well_grid"]
    probe_height = params["lid_manifold"]["thickness_z"] + params["lid_manifold"]["duct_height_z"]
    representative_grid_points = [
        (0, 0),
        (grid["columns"] - 1, 0),
        (grid["columns"] // 2, grid["rows"] // 2),
        (0, grid["rows"] - 1),
        (grid["columns"] - 1, grid["rows"] - 1),
    ]

    for tile in [layout["tile_origins"][0], layout["tile_origins"][-1]]:
        for col_idx, row_idx in representative_grid_points:
            x = tile["x"] + grid["first_well_center_x"] + col_idx * grid["pitch_x"]
            y = tile["y"] + grid["first_well_center_y"] + row_idx * grid["pitch_y"]
            probe = (
                cq.Workplane("XY")
                .circle(1.0)
                .extrude(probe_height + 0.4)
                .translate((x, y, -0.2))
            )
            intersection_volume = sum(
                shape.Volume()
                for part in (lid_shell, lid_cover)
                for shape in part.intersect(probe).vals()
            )
            assert intersection_volume == 0.0


def test_lid_compression_stops_follow_row_axis() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    row = params["row"]
    seal = params["seal_interface"]
    half_stop = seal["compression_stop_size"] / 2
    positions = layout["compression_stop_positions"]

    expected_y_values = {
        round(row["side_margin_y"] / 2, 3),
        round(layout["width_y"] - row["side_margin_y"] / 2, 3),
    }
    expected_y_values.update(
        round(tile["y"] - row["inter_tile_gap_y"] / 2, 3)
        for tile in layout["tile_origins"][1:]
    )
    expected_x_values = {
        round(row["end_margin_x"] / 2, 3),
        round(layout["length_x"] - row["end_margin_x"] / 2, 3),
    }

    assert layout["row_axis"] == "y"
    assert len(positions) == len(expected_x_values) * len(expected_y_values)
    assert len(positions) == len(set(positions))
    assert {x for x, _ in positions} == expected_x_values
    assert {y for _, y in positions} == expected_y_values
    for x, y in positions:
        assert half_stop < x < layout["length_x"] - half_stop
        assert half_stop < y < layout["width_y"] - half_stop


def test_printed_wedge_locks_clear_lid_service_ports() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    clearance = production["wedge_lock_port_clearance_xy"]
    receiver_cross = (
        production["wedge_receiver_clearance_x"]
        + production["wedge_receiver_rail_width_x"]
        + clearance
    )
    receiver_slide = production["wedge_receiver_length_extra_y"] / 2 + clearance

    assert len(layout["wedge_lock_rectangles"]) < len(layout["compression_stop_positions"])
    assert len(build_printed_wedge_locks(params).val().Solids()) == len(
        layout["wedge_lock_rectangles"]
    )

    for lock in layout["wedge_lock_rectangles"]:
        if lock["slide_axis"] == "x":
            rect_x = float(lock["x"]) - receiver_slide
            rect_y = float(lock["y"]) - receiver_cross
            rect_w = float(lock["length_x"]) + 2 * receiver_slide
            rect_h = float(lock["width_y"]) + 2 * receiver_cross
        else:
            rect_x = float(lock["x"]) - receiver_cross
            rect_y = float(lock["y"]) - receiver_slide
            rect_w = float(lock["length_x"]) + 2 * receiver_cross
            rect_h = float(lock["width_y"]) + 2 * receiver_slide
        for port in layout["lid_port_positions"]:
            assert not _rectangle_overlaps_circle(
                rect_x=rect_x,
                rect_y=rect_y,
                rect_w=rect_w,
                rect_h=rect_h,
                circle_x=float(port["x"]),
                circle_y=float(port["y"]),
                radius=float(port["boss_diameter"]) / 2 + clearance,
            )


def test_printed_latch_posts_are_integrated_wet_frame_tension_features() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    skirt = params["wet_chamber_skirt"]
    lane_span = (
        skirt["wall_thickness"]
        + skirt["service_lane_width"]
        + skirt["plenum_divider_thickness"]
    )
    frame_bb = build_wet_chamber_frame(params, assembly_position=True).val().BoundingBox()

    assert round(frame_bb.zmax, 2) == round(layout["latch_post_head_top_z"], 2)
    for lock, post in zip(
        layout["wedge_lock_rectangles"],
        layout["latch_post_positions"],
        strict=True,
    ):
        assert lock["slide_axis"] == "x"
        assert post["slide_axis"] == "x"
        assert float(lock["x"]) <= float(lock["post_x"]) <= (
            float(lock["x"]) + float(lock["length_x"])
        )
        assert float(lock["y"]) <= float(lock["post_y"]) <= (
            float(lock["y"]) + float(lock["width_y"])
        )
        assert float(post["x"]) <= lane_span or float(post["x"]) >= (
            layout["length_x"] - lane_span
        )
        assert production["latch_post_pedestal_width_y"] < params["row"][
            "inter_tile_gap_y"
        ]


def test_latch_stations_encode_bearing_capture_release_and_stop_geometry() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    slot_w = (
        production["latch_post_diameter"]
        + 2 * production["wedge_lock_post_slot_clearance_xy"]
    )
    bearing_len = production["wedge_lock_bearing_flat_length_x"]
    lip_len = production["wedge_receiver_lip_length_x"]
    release_len = production["wedge_release_tab_length_x"]
    witness_len = production["wedge_witness_mark_length_x"]
    detent_len = production["wedge_detent_bump_length_x"]
    head_len = production["latch_post_head_length_x"]

    for lock in layout["wedge_lock_rectangles"]:
        assert lock["slide_axis"] == "x"
        post_x = float(lock["post_x"])
        cap_x0 = post_x - head_len / 2
        cap_x1 = post_x + head_len / 2
        bearing_x0 = float(lock["bearing_flat_x"])
        bearing_x1 = bearing_x0 + float(lock["bearing_flat_length_x"])
        capture_x0 = float(lock["capture_lip_x"])
        capture_x1 = capture_x0 + float(lock["capture_lip_length_x"])
        release_x0 = float(lock["release_tab_x"])
        witness_x0 = float(lock["witness_mark_x"])
        detent_x0 = float(lock["detent_x"])
        stop_x0 = float(lock["travel_stop_x"])
        stop_x1 = stop_x0 + float(lock["travel_stop_length_x"])
        lock_x0 = float(lock["x"])
        lock_x1 = lock_x0 + float(lock["length_x"])

        assert float(lock["bearing_flat_length_x"]) == bearing_len
        assert float(lock["capture_lip_length_x"]) == lip_len
        assert cap_x0 <= bearing_x0
        assert bearing_x1 <= cap_x1

        if lock["insert_from"] == "min":
            assert post_x + slot_w / 2 < bearing_x0
            assert capture_x0 == lock_x0
            assert detent_x0 >= capture_x0
            assert detent_x0 + detent_len <= capture_x1
            assert release_x0 >= capture_x1
            assert release_x0 + release_len < bearing_x0
            assert release_x0 <= witness_x0
            assert witness_x0 + witness_len <= release_x0 + release_len
            assert stop_x0 >= lock_x1
        else:
            assert bearing_x1 < post_x - slot_w / 2
            assert capture_x1 == lock_x1
            assert detent_x0 >= capture_x0
            assert detent_x0 + detent_len <= capture_x1
            assert release_x0 + release_len <= capture_x0
            assert release_x0 > bearing_x1
            assert release_x0 <= witness_x0
            assert witness_x0 + witness_len <= release_x0 + release_len
            assert stop_x1 <= lock_x0


def test_latch_detail_features_change_their_owning_parts() -> None:
    params = load_params(PARAMS)
    plain_params = deepcopy(params)
    plain_params["production_assembly"]["wedge_receiver_lip_height_z"] = 0.0
    plain_params["production_assembly"]["wedge_travel_stop_height_z"] = 0.0
    plain_params["production_assembly"]["wedge_release_tab_height_z"] = 0.0
    plain_params["production_assembly"]["wedge_detent_bump_height_z"] = 0.0
    plain_params["production_assembly"]["latch_post_root_gusset_height_z"] = 0.0

    assert build_lid_cover(params).val().Volume() > (
        build_lid_cover(plain_params).val().Volume()
    )
    assert build_printed_wedge_locks(params).val().Volume() > (
        build_printed_wedge_locks(plain_params).val().Volume()
    )
    assert build_wet_chamber_frame(params).val().Volume() > (
        build_wet_chamber_frame(plain_params).val().Volume()
    )


def test_latch_mechanics_register_names_first_print_assumptions() -> None:
    params = load_params(PARAMS)
    mechanics = params["latch_mechanics"]

    assert mechanics["material_label"]
    assert mechanics["print_process_label"]
    assert mechanics["layer_height_mm"] > 0
    assert mechanics["latch_tolerance_allowance_z"] > 0
    assert mechanics["gasket_squeeze_min_z"] > 0
    assert mechanics["gasket_squeeze_min_z"] < mechanics["gasket_squeeze_target_z"]
    assert mechanics["gasket_squeeze_target_z"] <= mechanics["gasket_squeeze_max_z"]
    assert mechanics["friction_coefficient_min"] > 0
    assert mechanics["self_lock_min_margin_deg"] > 0
    assert mechanics["insertion_force_min_n"] > 0
    assert mechanics["insertion_force_min_n"] < mechanics["insertion_force_max_n"]
    assert mechanics["release_force_min_n"] > 0
    assert mechanics["release_force_min_n"] < mechanics["release_force_max_n"]
    assert mechanics["expected_clamp_force_per_latch_n"] > 0
    assert mechanics["allowable_wet_polymer_stress_mpa"] > 0
    assert mechanics["stress_safety_factor_min"] > 1.0


def test_latch_compression_budget_uses_production_geometry() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    mechanics = params["latch_mechanics"]
    demo = params["latch_mechanism_demo"]
    budget = layout["latch_compression_budget"]

    expected_rise = production["wedge_lock_height_z"] - production[
        "wedge_lock_low_height_z"
    ]
    expected_run = (
        production["wedge_lock_width_x"]
        - production["wedge_lock_lead_in_length_x"]
        - production["wedge_lock_bearing_flat_length_x"]
    )

    assert budget["source"] == "production_assembly"
    assert budget["ramp_rise_mm"] == round(expected_rise, 3)
    assert budget["ramp_run_mm"] == round(expected_run, 3)
    assert budget["ramp_rise_mm"] != (
        demo["wedge_high_height_z"] - demo["wedge_low_height_z"]
    )
    assert budget["wedge_length_mm"] == production["wedge_lock_width_x"]
    assert budget["wedge_length_mm"] != demo["wedge_length_x"]
    assert budget["available_squeeze_z"] == round(
        expected_rise - mechanics["latch_tolerance_allowance_z"],
        3,
    )
    assert budget["passes_budget"] is True
    assert budget["bounded_squeeze_z"] > 0
    assert budget["bounded_squeeze_z"] >= mechanics["gasket_squeeze_min_z"]
    assert budget["bounded_squeeze_z"] <= mechanics["gasket_squeeze_max_z"]
    assert budget["bounded_squeeze_z"] <= budget["hard_stop_limit_z"]


def test_gasket_compression_gap_gauge_encodes_latch_squeeze_budget() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    budget = layout["latch_compression_budget"]
    gauge_spec = layout["gasket_compression_gap_gauge"]
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    gauge = build_gasket_compression_gap_gauge(
        params,
        assembly_position=True,
    ).val()
    gauge_bb = gauge.BoundingBox()

    assert "gasket_compression_gap_gauge" in validation
    assert "gasket_compression_gap_gauge" not in installed
    assert gauge_spec["source"] == "latch_compression_budget"
    assert gauge_spec["role"] == "dry_assembly_gasket_squeeze_gap_reference"
    assert gauge_spec["evidence_gate"] == "Gate 2 dry assembly"
    assert gauge_spec["failure_rule"] == (
        "gasket_squeeze_out_of_range_blocks_dry_assembly_pass"
    )
    assert gauge_spec["cad_value"] == (
        "0.55 mm target / 0.20..0.80 mm allowed"
    )
    assert gauge_spec["requires_physical_evidence"] is True
    assert "gasket_compression_in_range" in gauge_spec["physical_claims_blocked"]
    assert gauge_spec["blade_count"] == 3
    assert len(gauge_spec["body_rects"]) == gauge_spec["blade_count"]
    assert [blade["role"] for blade in gauge_spec["blades"]] == [
        "minimum_gasket_squeeze_reference",
        "target_gasket_squeeze_reference",
        "maximum_gasket_squeeze_reference",
    ]
    assert [blade["thickness_z"] for blade in gauge_spec["blades"]] == [
        budget["gasket_squeeze_min_z"],
        budget["gasket_squeeze_target_z"],
        budget["gasket_squeeze_max_z"],
    ]
    assert [blade["length_x"] for blade in gauge_spec["blades"]] == sorted(
        blade["length_x"] for blade in gauge_spec["blades"]
    )
    assert len(gauge.Solids()) == gauge_spec["blade_count"]
    assert sorted(round(solid.BoundingBox().zlen, 2) for solid in gauge.Solids()) == [
        budget["gasket_squeeze_min_z"],
        budget["gasket_squeeze_target_z"],
        budget["gasket_squeeze_max_z"],
    ]
    assert round(gauge_bb.xmin, 2) > round(layout["length_x"], 2)
    assert round(gauge_bb.zmax, 2) == budget["gasket_squeeze_max_z"]


def test_gasket_squeeze_out_of_range_is_opt_in_gate2_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    budget = layout["latch_compression_budget"]
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    reviewed = build_row_coupon_service_parts(
        params,
        mode="gasket_squeeze_out_of_range",
    )
    installed_names = set(installed)
    rects = layout["gasket_squeeze_out_of_range_review"]
    review = reviewed["gasket_squeeze_out_of_range_review"].val()
    direct_review = build_gasket_squeeze_out_of_range_review(
        params,
        assembly_position=True,
    ).val()
    review_bb = review.BoundingBox()
    direct_bb = direct_review.BoundingBox()
    expected_xmin = min(float(rect["x"]) for rect in rects)
    expected_ymin = min(float(rect["y"]) for rect in rects)
    expected_zmin = min(float(rect["z"]) for rect in rects)
    expected_xmax = max(float(rect["x"]) + float(rect["length_x"]) for rect in rects)
    expected_ymax = max(float(rect["y"]) + float(rect["width_y"]) for rect in rects)
    expected_zmax = max(float(rect["z"]) + float(rect["height_z"]) for rect in rects)

    assert "gasket_squeeze_out_of_range" in ROW_COUPON_SERVICE_MODES
    assert "gasket_squeeze_out_of_range_review" not in installed
    assert "gasket_squeeze_out_of_range_review" not in validation
    assert installed_names.issubset(reviewed)
    assert set(reviewed) - installed_names == {"gasket_squeeze_out_of_range_review"}
    assert len(rects) == 2 * len(layout["compression_stop_positions"])
    assert len(review.Solids()) == len(rects)
    assert round(review_bb.xmin, 2) == round(direct_bb.xmin, 2)
    assert round(review_bb.ymin, 2) == round(direct_bb.ymin, 2)
    assert round(review_bb.zmin, 2) == round(direct_bb.zmin, 2)
    assert round(review_bb.xmax, 2) == round(direct_bb.xmax, 2)
    assert round(review_bb.ymax, 2) == round(direct_bb.ymax, 2)
    assert round(review_bb.zmax, 2) == round(direct_bb.zmax, 2)
    assert round(review_bb.xmin, 2) == round(expected_xmin, 2)
    assert round(review_bb.ymin, 2) == round(expected_ymin, 2)
    assert round(review_bb.zmin, 2) == round(expected_zmin, 2)
    assert round(review_bb.xmax, 2) == round(expected_xmax, 2)
    assert round(review_bb.ymax, 2) == round(expected_ymax, 2)
    assert round(review_bb.zmax, 2) == round(expected_zmax, 2)

    by_kind = {rect["review_kind"] for rect in rects}
    assert by_kind == {
        "gasket_overcompressed_below_min_gap",
        "gasket_undercompressed_above_max_gap",
    }
    assert {rect["review_state"] for rect in rects} == {"gasket_squeeze_out_of_range"}
    assert {rect["owner_part"] for rect in rects} == {
        "gasket_squeeze_out_of_range_review"
    }
    assert {rect["blocked_fail_closed_state"] for rect in rects} == {
        "gasket_squeeze_out_of_range"
    }
    assert {rect["retained_part"] for rect in rects} == {
        "lower_gasket_and_upper_gasket"
    }
    assert {rect["allowed_min_squeeze_z"] for rect in rects} == {
        budget["gasket_squeeze_min_z"]
    }
    assert {rect["allowed_max_squeeze_z"] for rect in rects} == {
        budget["gasket_squeeze_max_z"]
    }
    assert {
        "gasket_compression_gap_gauge",
        "latch_retention_span_check",
        "assembly_state_witness_check",
    } == set(rects[0]["source_validation_checks"])
    overcrush = [
        rect for rect in rects if rect["review_kind"] == "gasket_overcompressed_below_min_gap"
    ]
    undersqueeze = [
        rect
        for rect in rects
        if rect["review_kind"] == "gasket_undercompressed_above_max_gap"
    ]
    assert len(overcrush) == len(undersqueeze) == len(layout["compression_stop_positions"])
    assert all(rect["height_z"] < budget["gasket_squeeze_min_z"] for rect in overcrush)
    assert all(rect["height_z"] > budget["gasket_squeeze_max_z"] for rect in undersqueeze)


def test_fail_closed_prerun_inspection_check_encodes_blocking_states() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    spec = layout["fail_closed_prerun_inspection_check"]
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    check = build_fail_closed_prerun_inspection_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()
    rects = spec["body_rects"]
    blocker_states = {
        state
        for checkpoint in spec["checkpoints"]
        for state in checkpoint["blocks"]
    }
    source_checks = {
        source
        for checkpoint in spec["checkpoints"]
        for source in checkpoint["source_validation_checks"]
    }
    expected_xmin = min(float(rect["x"]) for rect in rects)
    expected_ymin = min(float(rect["y"]) for rect in rects)
    expected_zmin = min(float(rect["z"]) for rect in rects)
    expected_xmax = max(float(rect["x"]) + float(rect["length_x"]) for rect in rects)
    expected_ymax = max(float(rect["y"]) + float(rect["width_y"]) for rect in rects)
    expected_zmax = max(float(rect["z"]) + float(rect["height_z"]) for rect in rects)

    assert "fail_closed_prerun_inspection_check" in validation
    assert "fail_closed_prerun_inspection_check" not in installed
    assert spec["validation"] == "cad_proxy_operator_evidence_required_before_ot2_run"
    assert spec["evidence_gate"] == "Gate 2 dry assembly"
    assert spec["failure_rule"] == "any_blocker_not_passed_prevents_ot2_operation"
    assert spec["cad_value"] == (
        "10 checkpoints / any_blocker_not_passed_prevents_ot2_operation"
    )
    assert spec["fail_closed_rule"] == "any_blocker_not_passed_prevents_ot2_operation"
    assert spec["checkpoint_count"] == 10
    assert spec["all_blockers_have_service_review_mode"] is True
    assert spec["uncovered_blockers"] == []
    assert spec["all_checkpoints_block_ot2_run"] is True
    assert spec["requires_physical_evidence"] is True
    assert "normal_ot2_operation" in spec["physical_claims_blocked"]
    assert spec["gasket_gap_gauge_blade_count"] == 3
    assert "assembly_state_witness_check" in spec["source_validation_checks"]
    assert all(checkpoint["blocks_ot2_run"] for checkpoint in spec["checkpoints"])
    assert {checkpoint["index"] for checkpoint in spec["checkpoints"]} == set(range(1, 11))
    assert "deck_module_unseated" in blocker_states
    assert "sample_relief_cap_unseated" in blocker_states
    assert "gas_pcb_cartridges_unseated" in blocker_states
    assert "local_sensors_missing" in blocker_states
    assert "side_gas_tubes_unseated" in blocker_states
    assert "electrical_connectors_unmated" in blocker_states
    assert "service_dress_over_pipette_field" in blocker_states
    assert "service_dress_adjacent_slot_collision" in blocker_states
    assert "dry_bay_obstructed" in blocker_states
    assert "gasket_squeeze_out_of_range" in blocker_states
    assert "tube_or_cable_over_pipette_field" in blocker_states
    assert "wet_witness_path_hidden" in blocker_states
    assert spec["blocker_service_review_modes"][
        "deck_pod_repeat_seating_unproven"
    ] == ["deck_pose_repeatability_unproven"]
    assert spec["blocker_service_review_modes"]["rocking_or_yaw_unmeasured"] == [
        "deck_pose_repeatability_unproven"
    ]
    assert spec["blocker_service_review_modes"][
        "tube_or_cable_over_pipette_field"
    ] == ["service_dress_over_pipette_field"]
    assert spec["blocker_service_review_modes"]["adjacent_slot_service_collision"] == [
        "service_dress_adjacent_slot_collision"
    ]
    assert spec["blocker_service_review_modes"]["dry_bay_blocked"] == [
        "dry_bay_obstructed"
    ]
    assert spec["blocker_service_review_modes"]["wet_witness_path_hidden"] == [
        "dry_bay_obstructed"
    ]
    assert spec["blocker_service_review_modes"]["assembly_debris_present"] == [
        "assembly_debris_present"
    ]
    assert all(
        spec["blocker_service_review_modes"][block]
        for checkpoint in spec["checkpoints"]
        for block in checkpoint["blocks"]
    )
    assert all(
        checkpoint["service_review_modes"] and not checkpoint["uncovered_blockers"]
        for checkpoint in spec["checkpoints"]
    )
    assert {
        "assembly_state_witness_check",
        "deck_slot_footprint_check",
        "deck_frame_keepout_check",
        "deck_pod_seating_repeatability_check",
        "gasket_compression_gap_gauge",
        "sensor_installation_path_check",
        "ir_thermopile_fov_spot_check",
        "thermal_condensation_proxy_check",
        "electrical_connector_mating_state_check",
        "operating_service_dress_check",
        "row_tiling_service_clearance_check",
        "dry_bay_ingress_audit_check",
    }.issubset(source_checks)
    assert len(rects) == 1
    assert all("tab_rect" in checkpoint for checkpoint in spec["checkpoints"])
    assert all("index_marker_rects" in checkpoint for checkpoint in spec["checkpoints"])
    assert check.Volume() > 0
    assert round(check_bb.xmin, 2) == round(expected_xmin, 2)
    assert round(check_bb.ymin, 2) == round(expected_ymin, 2)
    assert round(check_bb.zmin, 2) == round(expected_zmin, 2)
    assert round(check_bb.xmax, 2) == round(expected_xmax, 2)
    assert round(check_bb.ymax, 2) == round(expected_ymax, 2)
    assert round(check_bb.zmax, 2) == round(expected_zmax, 2)


def test_material_cleaning_witness_coupon_tracks_cleaning_pending_surfaces() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    manifest = row_coupon_part_manifest()
    installed_manifest = manifest["installed"]
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    coupons = layout["material_cleaning_witness_coupons"]
    spec = layout["material_cleaning_witness_coupon"]
    body = build_material_cleaning_witness_coupon(
        params,
        assembly_position=True,
    ).val()
    body_bb = body.BoundingBox()
    standalone_bb = build_material_cleaning_witness_coupon(params).val().BoundingBox()
    cleaning_dispositions = {
        "printed_reusable_cleaning_pending",
        "replaceable_elastomer_or_tpu_cleaning_pending",
    }
    expected_groups: dict[tuple[str, str], list[str]] = {}
    for part_name, entry in installed_manifest.items():
        disposition = entry["service_disposition"]
        if disposition in cleaning_dispositions:
            expected_groups.setdefault(
                (entry["exposure_class"], disposition),
                [],
            ).append(part_name)

    assert "material_cleaning_witness_coupon" in validation
    assert "material_cleaning_witness_coupon" not in installed
    assert {
        (coupon["exposure_class"], coupon["service_disposition"])
        for coupon in coupons
    } == set(expected_groups)
    assert len(coupons) == len(expected_groups)
    assert body_bb.xmin > layout["length_x"]
    assert spec["evidence_gate"] == "Gate 1 Print QC"
    assert spec["validation"] == "required_gate1_same_material_cleaning_witness_evidence"
    assert spec["requires_physical_evidence"] is True
    assert spec["coupon_count"] == len(coupons)
    assert spec["body_rect_count"] == sum(
        3 + len(coupon["index_rects"]) for coupon in coupons
    )
    assert spec["cad_value"] == (
        "10 coupons / 16 represented parts / 38.00 x 127.00 x 1.55 mm"
    )
    assert round(body_bb.xmin, 2) == round(spec["x"], 2)
    assert round(body_bb.ymin, 2) == round(spec["y"], 2)
    assert round(body_bb.zmin, 2) == round(spec["z"], 2)
    assert round(body_bb.xlen, 2) == round(spec["length_x"], 2)
    assert round(body_bb.ylen, 2) == round(spec["width_y"], 2)
    assert round(body_bb.zlen, 2) == round(spec["height_z"], 2)
    assert round(standalone_bb.xmin, 2) == 0.0
    assert round(standalone_bb.ymin, 2) == 0.0

    represented_parts = {
        part
        for coupon in coupons
        for part in coupon["representative_parts"]
    }
    assert set(spec["representative_parts"]) == represented_parts
    assert represented_parts == {
        part
        for parts in expected_groups.values()
        for part in parts
    }
    assert "cots_microplates" not in represented_parts
    assert "cots_septum_mats" not in represented_parts
    assert "gas_sensor_pcbs" not in represented_parts
    assert "lower_sensor_harness" not in represented_parts

    expected_volume = 0.0
    for coupon in coupons:
        assert coupon["service_disposition"] in cleaning_dispositions
        assert coupon["representative_part_count"] == len(
            expected_groups[
                (coupon["exposure_class"], coupon["service_disposition"])
            ]
        )
        assert set(coupon["fabrication_sources"]) <= {
            "printed_polymer",
            "compressible_elastomer_or_printed_tpu",
        }
        assert len(coupon["index_rects"]) == coupon["index_code"]
        assert coupon["validation"].startswith("coupon_requires_same_material")
        for rect in (
            coupon["base_rect"],
            coupon["scrub_rect"],
            coupon["soak_rect"],
            *coupon["index_rects"],
        ):
            expected_volume += (
                float(rect["length_x"])
                * float(rect["width_y"])
                * float(rect["height_z"])
            )

    assert body.Volume() == pytest.approx(expected_volume, rel=0.01)


def test_latch_ramp_self_lock_screen_is_explicit_and_flags_thin_margin() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    mechanics = params["latch_mechanics"]
    demo = params["latch_mechanism_demo"]
    screen = layout["latch_ramp_self_lock"]

    rise = production["wedge_lock_height_z"] - production["wedge_lock_low_height_z"]
    run = (
        production["wedge_lock_width_x"]
        - production["wedge_lock_lead_in_length_x"]
        - production["wedge_lock_bearing_flat_length_x"]
    )
    expected_angle = math.degrees(math.atan2(rise, run))
    expected_friction_angle = math.degrees(math.atan(mechanics["friction_coefficient_min"]))
    demo_angle = math.degrees(
        math.atan2(
            demo["wedge_high_height_z"] - demo["wedge_low_height_z"],
            demo["wedge_length_x"],
        )
    )

    assert screen["source"] == "production_assembly"
    assert math.isclose(screen["ramp_angle_deg"], round(expected_angle, 3))
    assert screen["ramp_angle_deg"] != round(demo_angle, 3)
    assert math.isclose(screen["friction_angle_deg"], round(expected_friction_angle, 3))
    assert screen["passes_self_lock"] is True
    assert screen["self_lock_margin_deg"] > 0
    assert screen["meets_min_margin"] is False
    assert screen["backdrive_risk_flag"] is True
    assert screen["retention_status"] == "detent_or_physical_test_required"


def test_latch_post_stress_screen_has_positive_margin() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    mechanics = params["latch_mechanics"]
    screen = layout["latch_post_stress_screen"]

    expected_area = math.pi * (production["latch_post_diameter"] / 2) ** 2
    expected_stress = mechanics["expected_clamp_force_per_latch_n"] / expected_area

    assert screen["source"] == "production_assembly"
    assert math.isclose(screen["shaft_area_mm2"], round(expected_area, 3))
    assert math.isclose(screen["shaft_stress_mpa"], round(expected_stress, 3))
    assert screen["shaft_safety_factor"] >= mechanics["stress_safety_factor_min"]
    assert screen["cap_bearing_area_mm2"] >= mechanics["min_cap_bearing_area_mm2"]
    assert screen["root_pad_area_mm2"] >= mechanics["min_root_pad_area_mm2"]
    assert screen["passes_stress_screen"] is True


def test_latch_station_asymmetry_is_visible_when_port_omits_station() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    asymmetry = layout["latch_station_asymmetry"]

    assert asymmetry["expected_station_count"] == len(layout["compression_stop_positions"])
    assert asymmetry["active_station_count"] == len(layout["wedge_lock_rectangles"])
    assert asymmetry["omitted_station_count"] == 1
    assert asymmetry["has_omitted_station_warning"] is True
    assert asymmetry["omitted_stop_positions"] == [
        {"x": 142.6, "y": 188.625, "reason": "port_or_adapter_keepout"}
    ]
    assert asymmetry["max_active_station_span_mm"] > (
        params["latch_mechanics"]["max_active_latch_span_y"]
    )
    assert asymmetry["exceeds_allowed_span"] is True


def test_latch_retention_span_check_requires_dry_cycle_evidence() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    spec = layout["latch_retention_span_check"]
    rect = spec["body_rects"][0]
    check = build_latch_retention_span_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()

    assert "latch_retention_span_check" in validation
    assert "latch_retention_span_check" not in installed
    assert spec["validation"] == (
        "cad_proxy_latch_retention_span_physical_evidence_required"
    )
    assert spec["failure_rule"] == (
        "thin_self_lock_or_excess_span_blocks_wet_tests_until_gate2_evidence"
    )
    assert spec["evidence_gate"] == "Gate 2 dry assembly"
    assert spec["checkpoint_count"] == 4
    assert spec["cad_value"] == "0.32 deg margin / 181.00 mm span / 1 omitted"
    assert spec["wedge_lock_count"] == len(layout["wedge_lock_rectangles"])
    assert spec["self_lock_margin_deg"] == layout["latch_ramp_self_lock"][
        "self_lock_margin_deg"
    ]
    assert spec["backdrive_risk_flag"] is True
    assert spec["retention_status"] == "detent_or_physical_test_required"
    assert spec["omitted_station_count"] == 1
    assert spec["exceeds_allowed_span"] is True
    assert spec["requires_physical_evidence"] is True
    assert spec["all_checkpoints_block_wet_tests"] is True
    assert {
        "thin_self_lock_margin_unverified",
        "omitted_station_span_bow_unmeasured",
        "post_or_cap_bearing_damage_unchecked",
        "gasket_squeeze_after_latch_cycle_unmeasured",
    } == set(spec["blockers"])
    assert {
        "latch_ramp_self_lock",
        "latch_station_asymmetry",
        "latch_post_stress_screen",
        "latch_compression_budget",
    } == set(spec["source_layout_checks"])
    assert spec["source_validation_checks"] == ["gasket_compression_gap_gauge"]
    assert len(check.Solids()) == 1
    assert rect["x"] > layout["length_x"]
    assert round(check_bb.xlen, 2) == rect["length_x"]
    assert round(check_bb.ylen, 2) == rect["width_y"]
    assert round(check_bb.zmax, 2) == rect["height_z"]


def test_lid_ports_and_side_gas_services_are_role_typed_production_interfaces() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    ports = layout["lid_port_positions"]
    side_services = layout["side_gas_service_interfaces"]

    assert [port["role"] for port in ports] == ["sample_relief"]
    assert [port["name"] for port in ports] == ["sample_relief"]
    assert all("role_marker_count" not in port for port in ports)
    assert not any(
        key.startswith("port_role_marker")
        for key in params["production_assembly"]
    )
    for port in ports:
        assert port["cap_plug_diameter"] == round(
            port["hole_diameter"]
            - production["port_cap_plug_clearance_diameter"],
            3,
        )
        assert port["cap_flange_diameter"] == round(
            port["boss_diameter"] + 2 * production["port_cap_flange_overhang_xy"],
            3,
        )
        expected_lip_inner = round(
            port["hole_diameter"] + production["port_cap_plug_clearance_diameter"],
            3,
        )
        expected_lip_outer = round(
            min(
                expected_lip_inner + 2 * production["port_cap_seal_lip_width_xy"],
                port["boss_diameter"],
            ),
            3,
        )
        expected_lip_seat_depth = round(
            production["port_cap_seal_lip_height_z"]
            - production["port_cap_seal_lip_nominal_compression_z"],
            3,
        )
        assert port["cap_seal_lip_inner_diameter"] == expected_lip_inner
        assert port["cap_seal_lip_outer_diameter"] == expected_lip_outer
        assert port["cap_seal_lip_outer_diameter"] <= port["boss_diameter"]
        assert port["cap_seal_lip_height_z"] == production["port_cap_seal_lip_height_z"]
        assert port["cap_seal_lip_seat_depth_z"] == expected_lip_seat_depth
        assert port["cap_seal_lip_nominal_compression_z"] == (
            production["port_cap_seal_lip_nominal_compression_z"]
        )
        assert port["cap_seal_lip_nominal_compression_z"] < port["cap_seal_lip_height_z"]
        assert port["cap_seal_lip_role"] == (
            "integrated_compliant_lip_on_sample_relief_boss_top"
        )
    assert [service["role"] for service in side_services] == ["supply", "return"]
    assert [service["service_role"] for service in side_services] == [
        "production_operating_gas_supply",
        "production_operating_gas_return",
    ]
    assert {service["side"] for service in side_services} == {"left", "right"}
    assert all(service["owner_part"] == "lid_cover" for service in side_services)
    assert all(service["duct_opening"]["axis"] == "x" for service in side_services)
    assert all(
        service["validation"] == "side_connected_supply_return_no_top_gas_caps"
        for service in side_services
    )
    assert all(
        service["tube_min_bend_radius"] == params["gas_service"]["tube_bend_radius"]
        for service in side_services
    )
    assert layout["port_service_review_states"] == {
        "sample_relief_cap_missing": {
            "owner": "printed_sample_relief_cap",
            "removed_parts": ["printed_sample_relief_cap"],
            "review_parts": ["missing_sample_relief_cap_witness"],
            "meaning": (
                "The sample/relief cap is absent; witness ring marks the uncapped "
                "service port."
            ),
        },
        "sample_relief_cap_unseated": {
            "owner": "printed_sample_relief_cap",
            "removed_parts": ["printed_sample_relief_cap"],
            "review_parts": ["unseated_sample_relief_cap_review"],
            "meaning": "The sample/relief cap is shown lifted from its seated plug position.",
        },
    }


def test_sample_relief_cap_is_default_sealing_part() -> None:
    params = load_params(PARAMS)
    no_lip_params = deepcopy(params)
    no_lip_params["production_assembly"]["port_cap_seal_lip_width_xy"] = 0.0
    no_lip_params["production_assembly"]["port_cap_seal_lip_height_z"] = 0.0
    no_lip_params["production_assembly"]["port_cap_seal_lip_nominal_compression_z"] = 0.0
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    caps = build_printed_sample_relief_cap(params, assembly_position=True).val()
    no_lip_caps = build_printed_sample_relief_cap(
        no_lip_params,
        assembly_position=True,
    ).val()
    caps_bb = caps.BoundingBox()

    assert "printed_sample_relief_cap" in installed
    assert "printed_sample_relief_cap" not in validation
    assert "printed_port_caps" not in installed
    assert not hasattr(row_coupon_module, "build_printed_port_caps")
    assert len(caps.Solids()) == 1
    assert len(layout["lid_port_positions"]) == 1
    assert round(caps_bb.zmax, 2) == round(layout["port_cap_top_z"], 2)
    assert round(caps_bb.zmax, 2) < round(layout["assembly_top_z"], 2)
    assert caps.Volume() > no_lip_caps.Volume()
    assert build_lid_cover(params, assembly_position=True).val().Volume() < (
        build_lid_cover(no_lip_params, assembly_position=True).val().Volume()
    )


def test_sample_relief_cap_leak_witness_routes_outboard_without_blocking_access() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    witness_check = build_sample_relief_leak_witness_check(
        params,
        assembly_position=True,
    ).val()
    dry = layout["dry_bay_envelope"]
    spec = layout["sample_relief_leak_witness_check"]
    witness = layout["sample_relief_leak_witnesses"][0]
    shelf = witness["shelf_rect"]
    gutter = witness["gutter_rect"]
    threshold = witness["threshold_rect"]
    port = layout["lid_port_positions"][0]
    boss_r = port["boss_diameter"] / 2
    cap_flange_bottom_z = layout["lid_top_z"] + port["boss_height_z"]

    assert "sample_relief_leak_witness_check" not in installed
    assert "sample_relief_leak_witness_check" in validation
    assert len(layout["sample_relief_leak_witnesses"]) == 1
    assert spec["evidence_gate"] == "Gate 4 wet/dry witness"
    assert spec["cad_value"] == "2 wet collectors / 1 inboard dams"
    assert spec["failure_rule"] == (
        "sample_relief_leak_without_visible_witness_or_dam_blocks_wet_dry_pass"
    )
    assert spec["requires_physical_evidence"] is True
    assert "dry_bay_protection_from_top_cap_leaks" in spec["physical_claims_blocked"]
    assert spec["body_rects"] == [shelf, gutter, threshold]
    assert witness["owner_part"] == "lid_cover"
    assert witness["port_name"] == "sample_relief"
    assert witness["leak_management"] == (
        "outboard_visible_witness_gutter_with_inboard_dam"
    )
    assert witness["leak_flow_direction"] == "+X_to_visible_outer_edge"
    assert witness["route_axis"] == "x"
    assert witness["visible_edge"] == "right"
    assert shelf["x"] + shelf["length_x"] == round(layout["length_x"], 3)
    assert gutter["x"] + gutter["length_x"] == round(layout["length_x"], 3)
    assert gutter["height_z"] == params["production_assembly"][
        "sample_relief_witness_gutter_depth_z"
    ]
    assert threshold["height_z"] == params["production_assembly"][
        "sample_relief_witness_threshold_height_z"
    ]
    assert round(threshold["x"] + threshold["length_x"], 3) <= round(
        port["x"] - boss_r,
        3,
    )
    assert threshold["z"] == round(shelf["z"] + shelf["height_z"], 3)
    assert gutter["z"] == round(shelf["z"] + shelf["height_z"] - gutter["height_z"], 3)
    assert round(threshold["z"] + threshold["height_z"], 3) < round(
        cap_flange_bottom_z,
        3,
    )
    assert round(shelf["z"] + shelf["height_z"], 3) < round(cap_flange_bottom_z, 3)
    assert round(witness_check.BoundingBox().zmax, 2) == round(
        threshold["z"] + threshold["height_z"],
        2,
    )

    for rect in (shelf, gutter):
        assert not _rectangles_overlap(
            rect["x"],
            rect["y"],
            rect["length_x"],
            rect["width_y"],
            dry["x"],
            dry["y"],
            dry["length_x"],
            dry["width_y"],
        )
    for rect in (shelf, gutter, threshold):
        for tile in layout["tile_origins"]:
            x, y, length, width = _septum_access_window_for_tile_for_test(tile, params)
            assert not _rectangles_overlap(
                rect["x"],
                rect["y"],
                rect["length_x"],
                rect["width_y"],
                x,
                y,
                length,
                width,
            )


def test_side_gas_services_feed_sensor_cells_without_using_top_pipette_field() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    services = layout["side_gas_service_interfaces"]
    services_by_role = {service["role"]: service for service in services}
    tube_check = build_side_gas_tube_envelope_check(
        params,
        assembly_position=True,
    ).val()
    installed_tube_model = build_cots_gas_service_tubes(
        params,
        assembly_position=True,
    ).val()
    leak_check = build_side_gas_leak_witness_check(
        params,
        assembly_position=True,
    ).val()
    adjacent_check = build_adjacent_deck_slot_keepout_check(
        params,
        assembly_position=True,
    ).val()
    lid_bb = build_lid_cover(params, assembly_position=True).val().BoundingBox()
    adjacent_bb = adjacent_check.BoundingBox()
    dry = layout["dry_bay_envelope"]
    adjacent_keepouts = layout["adjacent_deck_slot_keepouts"]
    adjacent_spec = layout["adjacent_deck_slot_keepout_check"]
    adjacent_clearance = layout["side_gas_adjacent_slot_clearance"]
    gas_tubes = layout["cots_gas_service_tubes"]
    tube_spec = layout["side_gas_tube_envelope_check"]
    leak_spec = layout["side_gas_leak_witness_check"]
    gas = params["gas_service"]

    assert [service["role"] for service in services] == ["supply", "return"]
    assert gas["tube_inner_diameter"] <= gas["fitting_outer_diameter"]
    assert gas["barb_flange_diameter"] > gas["fitting_outer_diameter"]
    assert gas["barb_flange_diameter"] < gas["tube_outer_diameter"]
    assert gas["tube_outer_diameter"] <= gas["tube_envelope_diameter"]
    assert "cots_gas_service_tubes" in installed
    assert "cots_gas_service_tubes" not in validation
    tube_outer_radius = gas["tube_outer_diameter"] / 2
    tube_inner_radius = gas["tube_inner_diameter"] / 2
    solid_tube_volume = sum(
        math.pi * tube_outer_radius**2 * float(tube["length"])
        for tube in gas_tubes
    )
    hollow_tube_volume = sum(
        math.pi
        * (tube_outer_radius**2 - tube_inner_radius**2)
        * float(tube["length"])
        for tube in gas_tubes
    )
    assert installed_tube_model.Volume() > 0
    assert installed_tube_model.Volume() < solid_tube_volume
    assert installed_tube_model.Volume() == pytest.approx(hollow_tube_volume, rel=0.03)
    assert len(gas_tubes) == len(services)
    assert "side_gas_tube_envelope_check" not in installed
    assert "side_gas_tube_envelope_check" in validation
    assert "side_gas_leak_witness_check" not in installed
    assert "side_gas_leak_witness_check" in validation
    assert "adjacent_deck_slot_keepout_check" not in installed
    assert "adjacent_deck_slot_keepout_check" in validation
    assert adjacent_spec["evidence_gate"] == "Gate 3 OT-2 placement"
    assert adjacent_spec["validation"] == "required_gate3_adjacent_slot_keepout_evidence"
    assert adjacent_spec["failure_rule"] == (
        "adjacent_slot_interference_or_unmeasured_neighbor_keepout_blocks_ot2_placement_pass"
    )
    assert (
        adjacent_spec["cad_value"]
        == "8 neighbor keepouts / 395.00 x 359.50 x 110.00 mm"
    )
    assert adjacent_spec["requires_physical_evidence"] is True
    assert "normal_ot2_operation_in_adjacent_deck_slots" in adjacent_spec[
        "physical_claims_blocked"
    ]
    assert adjacent_spec["body_rects"] == adjacent_keepouts
    assert tube_spec["evidence_gate"] == "Gate 2 dry assembly"
    assert tube_spec["cad_value"] == "2 tubes / 36.00 mm envelope / 18.00 mm bend radius"
    assert tube_spec["failure_rule"] == (
        "kink_pull_off_or_unmeasured_tube_bend_blocks_dry_assembly_pass"
    )
    assert tube_spec["requires_physical_evidence"] is True
    assert "operating_gas_supply_connected" in tube_spec["physical_claims_blocked"]
    assert tube_spec["body_rects"] == layout["side_gas_tube_envelopes"]
    assert leak_spec["evidence_gate"] == "Gate 4 wet/dry witness"
    assert leak_spec["cad_value"] == "4 wet collectors / 2 inboard dams"
    assert leak_spec["failure_rule"] == (
        "side_gas_leak_without_visible_collector_or_inboard_dam_blocks_wet_dry_pass"
    )
    assert leak_spec["requires_physical_evidence"] is True
    assert "wet_operation_with_connected_side_gas" in leak_spec["physical_claims_blocked"]
    assert len(tube_check.Solids()) == len(services)
    assert len(leak_check.Solids()) == 3 * len(services)
    assert len(adjacent_check.Solids()) == (
        params["row"]["plate_count"]
        * 2
        * params["deck_interface"]["adjacent_slot_keepout_columns"]
    )
    assert round(lid_bb.xmin, 2) < 0.0
    assert round(lid_bb.xmax, 2) > round(layout["length_x"], 2)
    assert round(adjacent_bb.zmin, 2) == round(layout["deck_plane_z"], 2)
    assert round(adjacent_bb.zlen, 2) == params["deck_interface"][
        "adjacent_slot_service_keepout_height_z"
    ]
    assert adjacent_clearance["interpretation"] == (
        "side_services_use_reserved_adjacent_slot_overhead"
    )
    assert adjacent_clearance["xy_overlap_count"] > 0
    assert adjacent_clearance["meets_vertical_clearance"] is True
    assert adjacent_clearance["min_vertical_clearance_z"] >= params["deck_interface"][
        "side_service_vertical_clearance_z"
    ]
    assert {keepout["side"] for keepout in adjacent_keepouts} == {"left", "right"}

    for service in services:
        block = service["block_rect"]
        tube = service["tube_envelope_rect"]
        installed_tube = service["installed_tube"]
        tube_body = installed_tube["body_rect"]
        fitting = service["printed_fitting"]
        barb = service["printed_barb_retention_bead"]
        retention = service["tube_retention"]
        gutters = service["leak_witness_gutter_rects"]
        thresholds = service["leak_witness_threshold_rects"]
        assert installed_tube in gas_tubes
        assert installed_tube["owner_part"] == "cots_gas_service_tubes"
        assert installed_tube["service_role"] == (
            f"installed_operating_gas_{service['role']}_tube"
        )
        assert installed_tube["diameter"] == params["gas_service"]["tube_outer_diameter"]
        assert installed_tube["inner_diameter"] == gas["tube_inner_diameter"]
        assert installed_tube["flow_bore_diameter"] == gas["tube_inner_diameter"]
        assert installed_tube["geometry"] == "hollow_tube_wall"
        assert installed_tube["tube_retention"] == retention
        assert retention["retention"] == (
            "printed_barb_retention_bead_and_strain_relief_no_glue"
        )
        assert retention["validation"] == "print_native_tube_capture_no_glue_or_clamp"
        assert retention["tube_inner_diameter"] == gas["tube_inner_diameter"]
        assert retention["tube_outer_diameter"] == gas["tube_outer_diameter"]
        assert retention["stem_diameter"] == gas["fitting_outer_diameter"]
        assert retention["barb_peak_diameter"] == gas["barb_flange_diameter"]
        assert retention["barb_interference_diameter"] > 0
        assert retention["barb_radial_shoulder"] > 0
        assert fitting["diameter"] == gas["fitting_outer_diameter"]
        assert barb["diameter"] == gas["barb_flange_diameter"]
        assert barb["diameter"] > fitting["diameter"]
        assert barb["diameter"] < installed_tube["diameter"]
        assert barb["role"] == "tube_pulloff_resistance_without_glue"
        assert "printed_barb_retention_bead_envelope" in {
            rect["name"] for rect in service["external_service_rects"]
        }
        assert "printed_barb_flange_envelope" not in {
            rect["name"] for rect in service["external_service_rects"]
        }
        assert tube_body["x"] >= tube["x"]
        assert tube_body["y"] >= tube["y"]
        assert tube_body["z"] >= tube["z"]
        assert tube_body["x"] + tube_body["length_x"] <= tube["x"] + tube["length_x"]
        assert tube_body["y"] + tube_body["width_y"] <= tube["y"] + tube["width_y"]
        assert tube_body["z"] + tube_body["height_z"] <= tube["z"] + tube["height_z"]
        assert service["duct_z"] == round(
            layout["lid_top_z"] + params["lid_manifold"]["duct_height_z"] / 2,
            3,
        )
        assert service["leak_management"] == (
            "outboard_visible_witness_gutters_with_inboard_dam"
        )
        assert service["duct_opening"]["diameter"] == params["gas_service"][
            "duct_opening_diameter"
        ]
        assert len(gutters) == 2
        assert len(thresholds) == 1
        assert thresholds[0]["height_z"] == params["gas_service"][
            "leak_witness_threshold_height_z"
        ]
        assert thresholds[0]["z"] == round(block["z"] + block["height_z"], 3)
        if service["role"] == "supply":
            assert service["leak_flow_direction"] == "-X_to_visible_outer_edge"
            assert all(gutter["x"] == 0.0 for gutter in gutters)
            assert thresholds[0]["x"] >= gutters[0]["x"] + gutters[0]["length_x"]
        else:
            assert service["leak_flow_direction"] == "+X_to_visible_outer_edge"
            assert all(
                gutter["x"] + gutter["length_x"] == round(layout["length_x"], 3)
                for gutter in gutters
            )
            assert thresholds[0]["x"] + thresholds[0]["length_x"] <= gutters[0]["x"]
        for gutter in gutters:
            assert gutter["height_z"] == params["gas_service"]["leak_witness_gutter_depth_z"]
            assert gutter["z"] == round(block["z"] + block["height_z"] - gutter["height_z"], 3)
            assert not _rectangles_overlap(
                gutter["x"],
                gutter["y"],
                gutter["length_x"],
                gutter["width_y"],
                dry["x"],
                dry["y"],
                dry["length_x"],
                dry["width_y"],
            )
        for tile in layout["tile_origins"]:
            x, y, length, width = _septum_access_window_for_tile_for_test(tile, params)
            assert not _rectangles_overlap(
                block["x"],
                block["y"],
                block["length_x"],
                block["width_y"],
                x,
                y,
                length,
                width,
            )
            assert not _rectangles_overlap(
                tube["x"],
                tube["y"],
                tube["length_x"],
                tube["width_y"],
                x,
                y,
                length,
                width,
            )

        for rect in service["external_service_rects"]:
            for keepout in adjacent_keepouts:
                if not _rectangles_overlap(
                    rect["x"],
                    rect["y"],
                    rect["length_x"],
                    rect["width_y"],
                    keepout["x"],
                    keepout["y"],
                    keepout["length_x"],
                    keepout["width_y"],
                ):
                    continue
                clearance = rect["z"] - (keepout["z"] + keepout["height_z"])
                assert clearance >= params["deck_interface"][
                    "side_service_vertical_clearance_z"
                ]

    for mount in layout["gas_sensor_pcb_mounts"]:
        service = services_by_role[mount["role"]]
        assert mount["aperture_x"] == service["duct_x"]
        assert mount["aperture_y"] == service["duct_y"]
        assert mount["gas_interface"]["validation"] == (
            "aperture_registered_low_dead_volume_no_open_top_sampling"
        )


def test_first_build_sensor_roles_are_physical_screwless_mounts() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    parts = build_row_coupon_installed_parts(params)
    mounts = params["sensor_mounts"]
    lid = params["lid_manifold"]
    headspace_top_z = (
        layout["plate_top_z"]
        + params["seal_interface"]["compressed_gasket_height_z"]
        + params["seal_interface"]["headspace_recess_depth_z"]
    )

    assert layout["sensor_mount_summary"] == {
        "gas_sensor_pcb_count": 2,
        "headspace_sht41_count": 4,
        "ir_thermopile_count": 4,
        "row_module_retention": "screwless_printed_features",
    }
    assert {
        "gas_sensor_pcbs",
        "gas_pcb_interface_gaskets",
        "printed_gas_pcb_keeper_doors",
        "headspace_sht41_microcarriers",
        "ir_thermopiles",
        "ir_thermopile_face_gaskets",
    }.issubset(parts)
    assert build_gas_sensor_pcbs(params, assembly_position=True).val().Volume() > 0
    assert build_gas_pcb_interface_gaskets(params, assembly_position=True).val().Volume() > 0
    assert len(build_gas_pcb_flow_cell_check(params, assembly_position=True).val().Solids()) == 2
    assert layout["gas_pcb_flow_cell_check"]["validation"] == (
        "required_gate6_aperture_registered_flow_cell_evidence"
    )
    assert layout["gas_pcb_flow_cell_check"]["failure_rule"] == (
        "missing_flow_cell_or_gasket_registration_evidence_blocks_sensor_thermal_pass"
    )
    assert layout["gas_pcb_flow_cell_check"]["evidence_gate"] == (
        "Gate 6 sensor/thermal"
    )
    assert layout["gas_pcb_flow_cell_check"]["cad_value"] == (
        "2.00 mm aperture / 12.80 mm3 cell"
    )
    assert layout["gas_pcb_flow_cell_check"]["cartridge_count"] == 2
    assert layout["gas_pcb_flow_cell_check"]["flow_cell_count"] == 2
    assert layout["gas_pcb_flow_cell_check"]["aperture_count"] == 2
    assert layout["gas_pcb_flow_cell_check"]["requires_physical_evidence"] is True
    assert len(layout["gas_pcb_flow_cell_check"]["flow_cell_rects"]) == 2
    assert build_printed_gas_pcb_keeper_doors(
        params,
        assembly_position=True,
    ).val().Volume() > 0
    assert build_headspace_sht41_microcarriers(params, assembly_position=True).val().Volume() > 0
    assert len(build_ir_thermopiles(params, assembly_position=True).val().Solids()) == 4
    assert len(
        build_ir_thermopile_face_gaskets(params, assembly_position=True).val().Solids()
    ) == 4
    assert layout["sensor_installation_summary"] == {
        "install_step_count": 10,
        "test_gate_count": params["sensor_installation"]["test_gate_count"],
        "retention_policy": "printed_reversible_no_screws_no_glue",
        "service_modes": "bench_test_then_sensor_install_then_dry_then_wet_then_bsl1",
    }

    for mount in layout["gas_sensor_pcb_mounts"]:
        assert mount["owner_part"] == "lid_cover"
        assert mount["retention"] == "screwless_printed_keeper"
        assert mount["orientation"] == "vertical_side_cartridge"
        assert mount["socket_enclosure"] == "full_height_printed_dry_side_cassette"
        assert mount["wet_boundary"] == "dry_side_gas_duct_aperture_only"
        assert mount["headspace_intrusion"] is False
        assert mount["height_z"] == mounts["gas_pcb_envelope_width"]
        assert mount["length_x"] == mounts["gas_pcb_envelope_thickness"]
        assert mount["aperture_diameter"] == mounts["gas_pcb_aperture_diameter"]
        assert mount["z"] >= headspace_top_z
        assert layout["lid_top_z"] <= mount["aperture_z"] <= layout["lid_top_z"] + lid[
            "duct_height_z"
        ]
        interface = mount["gas_interface"]
        assert interface["type"] == "sealed_dry_side_duct_sampling_cell"
        assert interface["validation"] == "aperture_registered_low_dead_volume_no_open_top_sampling"
        assert interface["dead_volume_mm3"] <= 20.0
        assert interface["nominal_compression_x"] > 0
        assert interface["nominal_compression_x"] < interface["nominal_gasket_thickness_x"]
        flow = interface["flow_cell_rect"]
        gasket = interface["gasket_rect"]
        gasket_window = interface["gasket_window_rect"]
        land = interface["seal_land_rect"]
        assert flow["z"] >= layout["lid_top_z"]
        assert flow["z"] + flow["height_z"] <= layout["lid_top_z"] + lid["duct_height_z"]
        assert gasket["height_z"] <= lid["duct_height_z"]
        assert gasket_window["height_z"] == flow["height_z"]
        assert gasket_window["width_y"] == flow["width_y"]
        assert land["height_z"] <= lid["duct_height_z"]
        assert len(interface["compression_pad_rects"]) == 2
        assert mount["cable_exit_rect"]["depth_z"] == mounts["cable_channel_depth_z"]
        assert mount["cable_exit_rect"]["length_x"] > 0
        for tile in layout["tile_origins"]:
            x, y, length, width = _septum_access_window_for_tile_for_test(tile, params)
            assert not _rectangles_overlap(
                mount["x"],
                mount["y"],
                mount["length_x"],
                mount["width_y"],
                x,
                y,
                length,
                width,
            )
            assert not _rectangles_overlap(
                mount["cable_exit_rect"]["x"],
                mount["cable_exit_rect"]["y"],
                mount["cable_exit_rect"]["length_x"],
                mount["cable_exit_rect"]["width_y"],
                x,
                y,
                length,
                width,
            )

    for mount in layout["headspace_sht41_mounts"]:
        assert mount["owner_part"] == "lid_manifold_shell"
        assert mount["retention"] == "screwless_printed_microcarrier_keeper"
        assert mount["orientation"] == "side_loaded_service_cassette"
        assert mount["service_direction"] == "-X_install_+X_remove"
        assert mount["socket_enclosure"] == "protected_side_loaded_lid_shell_tunnel"
        assert mount["wet_boundary"] == "controlled_membrane_aperture_only"
        assert mount["condensate_protection"] == (
            "drip_break_ring_and_service_side_harness_isolation"
        )
        assert mount["length_x"] == mounts["sht41_carrier_length_x"]
        assert mount["width_y"] == mounts["sht41_carrier_width_y"]
        assert mount["height_z"] == mounts["sht41_carrier_height_z"]
        outer = mount["protected_cassette_outer_rect"]
        pocket = mount["protected_pocket_cut_rect"]
        keeper = mount["anti_lift_keeper_rect"]
        back_stop = mount["back_stop_rect"]
        key = mount["registration_key_rect"]
        notch = mount["registration_notch_rect"]
        relief = mount["service_finger_relief_rect"]
        ring = mount["drip_break_ring"]
        assert pocket["x"] <= mount["x"]
        assert pocket["y"] <= mount["y"]
        assert mount["x"] + mount["length_x"] <= pocket["x"] + pocket["length_x"]
        assert mount["y"] + mount["width_y"] <= pocket["y"] + pocket["width_y"]
        assert pocket["x"] + pocket["length_x"] > layout["length_x"]
        assert outer["x"] < pocket["x"]
        assert outer["y"] < pocket["y"]
        assert outer["x"] + outer["length_x"] == layout["length_x"]
        assert outer["y"] + outer["width_y"] > pocket["y"] + pocket["width_y"]
        assert outer["z"] == layout["lid_bottom_z"]
        assert mount["socket_floor_thickness_z"] > 0
        assert keeper["z"] == round(pocket["z"] + pocket["height_z"], 3)
        assert keeper["height_z"] == mounts["sht41_pocket_roof_thickness_z"]
        assert back_stop["x"] == outer["x"]
        assert back_stop["length_x"] == mounts["sht41_socket_wall_thickness"]
        assert len(mount["side_stop_rects"]) == 2
        for stop in mount["side_stop_rects"]:
            assert stop["width_y"] == mounts["sht41_socket_wall_thickness"]
            assert stop["height_z"] == pocket["height_z"]
        assert key == notch
        assert key["height_z"] == mounts["sht41_registration_key_height_z"]
        assert relief["x"] + relief["length_x"] == layout["length_x"]
        assert relief["width_y"] == mounts["sht41_service_finger_relief_width_y"]
        assert ring["inner_diameter"] == mount["aperture_diameter"]
        assert ring["outer_diameter"] == mounts["sht41_drip_break_outer_diameter"]
        assert ring["outer_diameter"] > ring["inner_diameter"]
        assert ring["z"] + ring["height_z"] == layout["lid_bottom_z"]
        assert mount["x"] > (
            layout["observer_front_end_swept_body_check"]["x"]
            + layout["observer_front_end_swept_body_check"]["length_x"]
        )
        assert mount["cable_exit_rect"]["length_x"] > 0
        tile = layout["tile_origins"][mount["tile_index"] - 1]
        x, y, length, width = _septum_access_window_for_tile_for_test(tile, params)
        assert not _rectangles_overlap(
            mount["x"],
            mount["y"],
            mount["length_x"],
            mount["width_y"],
            x,
            y,
            length,
            width,
        )
        assert not _rectangles_overlap(
            outer["x"],
            outer["y"],
            outer["length_x"],
            outer["width_y"],
            x,
            y,
            length,
            width,
        )
        assert not _rectangle_overlaps_circle(
            rect_x=x,
            rect_y=y,
            rect_w=length,
            rect_h=width,
            circle_x=ring["x"],
            circle_y=ring["y"],
            radius=ring["outer_diameter"] / 2,
        )
        assert not _rectangles_overlap(
            mount["cable_exit_rect"]["x"],
            mount["cable_exit_rect"]["y"],
            mount["cable_exit_rect"]["length_x"],
            mount["cable_exit_rect"]["width_y"],
            x,
            y,
            length,
            width,
        )

    for mount in layout["ir_sensor_mounts"]:
        assert mount["owner_part"] == "plate_support_frame"
        assert mount["retention"] == "screwless_printed_lip"
        assert mount["wet_boundary"] == (
            "drip_collared_aperture_with_dry_side_face_gasket"
        )
        assert mount["condensate_protection"] == (
            "top_drip_collar_and_compressed_face_gasket"
        )
        gasket = mount["face_gasket"]
        collar = mount["drip_collar"]
        assert gasket["retention"] == "captured_between_to39_face_and_printed_pocket_lip"
        assert gasket["wet_boundary"] == "dry_side_aperture_face_seal"
        assert gasket["outer_diameter"] == mounts["ir_face_gasket_outer_diameter"]
        assert gasket["inner_diameter"] == mounts["ir_face_gasket_inner_diameter"]
        assert gasket["height_z"] == mounts["ir_face_gasket_thickness_z"]
        assert gasket["nominal_compression_z"] == mounts[
            "ir_face_gasket_nominal_compression_z"
        ]
        assert 0 < gasket["nominal_compression_z"] < gasket["height_z"]
        assert gasket["inner_diameter"] > mount["aperture_diameter"]
        assert gasket["outer_diameter"] <= mount["length_x"]
        assert collar["owner_part"] == "plate_support_frame"
        assert collar["leak_management"] == (
            "raised_collar_keeps_wetting_out_of_ir_aperture"
        )
        assert collar["inner_diameter"] == mount["aperture_diameter"]
        assert collar["outer_diameter"] == mounts["ir_aperture_drip_collar_outer_diameter"]
        assert collar["height_z"] == mounts["ir_aperture_drip_collar_height_z"]
        assert collar["outer_diameter"] > collar["inner_diameter"]
        assert collar["z"] == layout["base_top_z"]
        assert collar["z"] + collar["height_z"] < layout["plate_bottom_z"]
        tile = layout["tile_origins"][mount["tile_index"] - 1]
        assert tile["x"] <= mount["x"]
        assert mount["x"] + mount["length_x"] <= tile["x"] + params["plate"]["length_x"]
        assert tile["y"] <= mount["y"]
        assert mount["y"] + mount["width_y"] <= tile["y"] + params["plate"]["width_y"]
        well_grid = mount["well_grid_rect"]
        assert mount["center_x"] + mount["fov_spot_diameter"] / 2 <= well_grid["x"]
        assert mount["cable_exit_rect"]["length_x"] > 0
        dry_aperture = next(
            aperture
            for aperture in layout["dry_bay_apertures"]
            if aperture["tile_index"] == mount["tile_index"]
        )
        assert not _rectangle_overlaps_circle(
            rect_x=dry_aperture["x"],
            rect_y=dry_aperture["y"],
            rect_w=dry_aperture["length_x"],
            rect_h=dry_aperture["width_y"],
            circle_x=mount["aperture_x"],
            circle_y=mount["aperture_y"],
            radius=mount["aperture_diameter"] / 2,
        )
        assert not _rectangle_overlaps_circle(
            rect_x=dry_aperture["x"],
            rect_y=dry_aperture["y"],
            rect_w=dry_aperture["length_x"],
            rect_h=dry_aperture["width_y"],
            circle_x=collar["x"],
            circle_y=collar["y"],
            radius=collar["outer_diameter"] / 2,
        )
        assert not _rectangles_overlap(
            mount["cable_exit_rect"]["x"],
            mount["cable_exit_rect"]["y"],
            mount["cable_exit_rect"]["length_x"],
            mount["cable_exit_rect"]["width_y"],
            dry_aperture["x"],
            dry_aperture["y"],
            dry_aperture["length_x"],
            dry_aperture["width_y"],
        )
        spot_r = mount["fov_spot_diameter"] / 2
        assert tile["x"] <= mount["center_x"] - spot_r
        assert mount["center_x"] + spot_r <= well_grid["x"]
        assert tile["y"] <= mount["center_y"] - spot_r
        assert mount["center_y"] + spot_r <= tile["y"] + params["plate"]["width_y"]
        assert mount["fov_angle_degrees"] == params["sensor_harness"]["ir_fov_angle_degrees"]


def test_sensor_harness_routes_are_physical_service_domains() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    harness = params["sensor_harness"]
    parts = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)

    assert layout["sensor_harness_summary"] == {
        "lower_ir_route_count": 4,
        "lid_sensor_route_count": 6,
        "service_connector_count": 3,
        "external_service_cable_envelope_count": 3,
        "installed_service_cable_pigtail_count": 3,
        "service_connector_family": harness["service_connector_family"],
        "retention": "printed_snap_covers_and_strain_relief",
        "lower_domain": "dry_plate_support_side",
        "lid_domain": "removable_lid_sensor_side",
    }
    assert {
        "lower_sensor_harness",
        "lower_harness_cover",
        "lid_sensor_harness",
        "lid_harness_cover",
        "lower_sensor_service_connector",
        "printed_lower_sensor_connector_shroud",
        "lower_sensor_service_cable_pigtail",
        "lid_sensor_service_connectors",
        "printed_lid_sensor_connector_shrouds",
        "lid_sensor_service_cable_pigtails",
    }.issubset(parts)
    assert build_lower_sensor_harness(params, assembly_position=True).val().Volume() > 0
    assert build_lid_sensor_harness(params, assembly_position=True).val().Volume() > 0
    assert build_lower_harness_cover(params, assembly_position=True).val().Volume() > 0
    assert build_lid_harness_cover(params, assembly_position=True).val().Volume() > 0
    assert build_lower_sensor_service_connector(params, assembly_position=True).val().Volume() > 0
    assert build_lid_sensor_service_connectors(params, assembly_position=True).val().Volume() > 0
    assert build_lower_sensor_service_cable_pigtail(
        params,
        assembly_position=True,
    ).val().Volume() > 0
    assert build_lid_sensor_service_cable_pigtails(
        params,
        assembly_position=True,
    ).val().Volume() > 0
    for part in [
        build_lower_sensor_harness(params, assembly_position=True),
        build_lower_harness_cover(params, assembly_position=True),
        build_lid_sensor_harness(params, assembly_position=True),
        build_lid_harness_cover(params, assembly_position=True),
        build_lower_sensor_service_connector(params, assembly_position=True),
        build_lid_sensor_service_connectors(params, assembly_position=True),
    ]:
        bb = part.val().BoundingBox()
        assert bb.xmin >= 0
        assert bb.ymin >= 0
        assert round(bb.xmax, 2) <= round(layout["length_x"], 2)
        assert round(bb.ymax, 2) <= round(layout["width_y"], 2)

    lower_trunk = layout["lower_ir_harness_trunk"]
    dry = layout["dry_bay_envelope"]
    assert lower_trunk["x"] + lower_trunk["length_x"] < dry["x"]
    assert lower_trunk["retention"] == "printed_snap_cover"
    assert layout["lower_ir_connector_envelope"]["z"] < 0
    assert not _rectangles_overlap(
        layout["lower_ir_connector_envelope"]["x"],
        layout["lower_ir_connector_envelope"]["y"],
        layout["lower_ir_connector_envelope"]["length_x"],
        layout["lower_ir_connector_envelope"]["width_y"],
        dry["x"],
        dry["y"],
        dry["length_x"],
        dry["width_y"],
    )

    for route in layout["lower_ir_harness_routes"]:
        branch = route["branch_rect"]
        relief = route["strain_relief_rect"]
        assert route["domain"] == "lower_dry_harness"
        assert route["branch_length_to_trunk"] >= harness["min_bend_radius"]
        assert branch["height_z"] <= harness["channel_depth_z"]
        assert relief["depth_z"] == harness["strain_relief_depth_z"]
        assert branch["x"] + branch["length_x"] < dry["x"]
        for aperture in layout["dry_bay_apertures"]:
            assert not _rectangles_overlap(
                branch["x"],
                branch["y"],
                branch["length_x"],
                branch["width_y"],
                aperture["x"],
                aperture["y"],
                aperture["length_x"],
                aperture["width_y"],
            )
        for foot in layout["deck_engagement_feet"]:
            assert not _rectangles_overlap(
                branch["x"],
                branch["y"],
                branch["length_x"],
                branch["width_y"],
                foot["x"],
                foot["y"],
                foot["length_x"],
                foot["width_y"],
            )

    lid_trunks = {trunk["name"]: trunk for trunk in layout["lid_sensor_harness_trunks"]}
    assert set(lid_trunks) == {
        "lid_cover_left_gas_bus",
        "lid_cover_right_gas_bus",
        "lid_shell_right_sht41_bus",
    }
    assert lid_trunks["lid_shell_right_sht41_bus"]["owner_part"] == "lid_manifold_shell"
    assert lid_trunks["lid_cover_left_gas_bus"]["owner_part"] == "lid_cover"
    assert lid_trunks["lid_cover_right_gas_bus"]["owner_part"] == "lid_cover"

    for trunk in lid_trunks.values():
        assert trunk["retention"] == "printed_snap_cover"
        assert 0 <= trunk["x"]
        assert trunk["x"] + trunk["length_x"] <= layout["length_x"]
        for tile in layout["tile_origins"]:
            x, y, length, width = _septum_access_window_for_tile_for_test(tile, params)
            assert not _rectangles_overlap(
                trunk["x"],
                trunk["y"],
                trunk["length_x"],
                trunk["width_y"],
                x,
                y,
                length,
                width,
            )

    gas_routes = [
        route
        for route in layout["lid_sensor_harness_routes"]
        if route["owner_part"] == "lid_cover"
    ]
    sht41_routes = [
        route
        for route in layout["lid_sensor_harness_routes"]
        if route["owner_part"] == "lid_manifold_shell"
    ]
    assert len(gas_routes) == 2
    assert len(sht41_routes) == 4
    for route in gas_routes:
        assert route["branch_length_to_trunk"] >= harness["min_bend_radius"]
        assert route["strain_relief_rect"]["depth_z"] == harness["strain_relief_depth_z"]
    for route in sht41_routes:
        assert route["inline_trunk"] is True
        assert route["trunk_name"] == "lid_shell_right_sht41_bus"
        assert route["strain_relief_rect"]["depth_z"] == harness["strain_relief_depth_z"]

    assert {conn["disconnect"] for conn in layout["sensor_service_connector_envelopes"]} == {
        "lower_dry_row_end",
        "removable_lid_left_gas",
        "removable_lid_right_sensor_bus",
    }
    service_clearance_rects = [
        connector["service_clearance_rect"]
        for connector in layout["sensor_service_connector_envelopes"]
    ]
    connector_check = layout["sensor_connector_service_clearance_check"]
    cable_envelope_check = layout["sensor_service_cable_envelope_check"]
    assert connector_check["evidence_gate"] == "Gate 6 sensor/thermal"
    assert connector_check["cad_value"] == "145.60 x 12.00 x 43.30 mm"
    assert connector_check["failure_rule"] == (
        "blocked_connector_clearance_or_unmeasured_mating_space_blocks_sensor_thermal_pass"
    )
    assert connector_check["requires_physical_evidence"] is True
    assert "mated_sensor_service_connectors" in connector_check[
        "physical_claims_blocked"
    ]
    assert connector_check["body_rects"] == service_clearance_rects
    assert cable_envelope_check["evidence_gate"] == "Gate 6 sensor/thermal"
    assert cable_envelope_check["cad_value"] == "6.00 x 30.00 x 5.10 mm"
    assert (
        cable_envelope_check["bend_cad_value"]
        == "12.00 mm bend radius / 18.00 mm straight"
    )
    assert cable_envelope_check["failure_rule"] == (
        "kinked_snagging_or_unmeasured_sensor_cable_dress_blocks_sensor_thermal_pass"
    )
    assert cable_envelope_check["requires_physical_evidence"] is True
    assert "connected_sensor_service_cable_dress" in cable_envelope_check[
        "physical_claims_blocked"
    ]
    assert cable_envelope_check["body_rects"] == layout["sensor_service_cable_envelopes"]
    lower_connector = layout["lower_ir_connector_envelope"]
    assert lower_connector["owner_part"] == "plate_support_frame"
    assert lower_connector["connector_family"] == harness["service_connector_family"]
    assert lower_connector["circuits"] == harness["service_connector_circuits"]
    assert lower_connector["mating_direction"] == "+Y"
    assert lower_connector["service_clearance_rect"]["width_y"] == harness[
        "service_connector_service_clearance_y"
    ]
    for connector in layout["lid_service_connector_envelopes"]:
        assert connector["owner_part"] == "lid_cover"
        assert connector["z"] == layout["lid_top_z"]
        assert connector["connector_family"] == harness["service_connector_family"]
        assert connector["printed_shroud"]["open_side"] == "+Y"
    clearance = build_sensor_connector_service_clearance_check(
        params,
        assembly_position=True,
    ).val()
    cable_check = build_sensor_service_cable_envelope_check(
        params,
        assembly_position=True,
    ).val()
    assert len(clearance.Solids()) == len(layout["sensor_service_connector_envelopes"])
    assert clearance.BoundingBox().ymax > layout["width_y"]
    assert "sensor_connector_service_clearance_check" not in parts
    assert "sensor_connector_service_clearance_check" in validation
    assert "sensor_service_cable_envelope_check" not in parts
    assert "sensor_service_cable_envelope_check" in validation
    assert len(cable_check.Solids()) == len(layout["sensor_service_connector_envelopes"])
    assert len(layout["sensor_service_cable_envelopes"]) == len(
        layout["sensor_service_connector_envelopes"]
    )
    assert len(layout["sensor_service_cable_pigtails"]) == len(
        layout["sensor_service_connector_envelopes"]
    )
    connectors_by_name = {
        connector["name"]: connector
        for connector in layout["sensor_service_connector_envelopes"]
    }
    pigtails_by_connector = {
        pigtail["connector_name"]: pigtail
        for pigtail in layout["sensor_service_cable_pigtails"]
    }
    for envelope in layout["sensor_service_cable_envelopes"]:
        connector = connectors_by_name[envelope["connector_name"]]
        pigtail = pigtails_by_connector[envelope["connector_name"]]
        assert envelope["route_axis"] == "+Y"
        assert envelope["service_role"] == "external_electrical_service_cable_envelope"
        assert envelope["validation"] == "row_end_cable_egress_not_printed_part"
        assert pigtail["route_axis"] == "+Y"
        assert pigtail["service_role"] == "installed_electrical_service_cable_pigtail"
        assert pigtail["validation"] == "installed_cable_body_bend_envelope_checked_separately"
        assert pigtail["material_intent"] == "COTS flexible cable assembly"
        assert pigtail["x"] >= envelope["x"]
        assert pigtail["y"] == envelope["y"]
        assert pigtail["z"] >= envelope["z"]
        assert pigtail["x"] + pigtail["length_x"] <= envelope["x"] + envelope["length_x"]
        assert pigtail["y"] + pigtail["width_y"] <= envelope["y"] + envelope["width_y"]
        assert pigtail["z"] + pigtail["height_z"] <= envelope["z"] + envelope["height_z"]
        assert envelope["y"] == connector["service_clearance_rect"]["y"]
        assert envelope["y"] + envelope["width_y"] > layout["width_y"]
        assert envelope["x"] >= 0.0
        assert envelope["x"] + envelope["length_x"] <= layout["length_x"]
        assert envelope["width_y"] == (
            harness["service_cable_bend_radius_y"]
            + harness["service_cable_straight_length_y"]
        )
        assert envelope["min_bend_radius_y"] == harness["service_cable_bend_radius_y"]
        assert envelope["straight_service_length_y"] == harness[
            "service_cable_straight_length_y"
        ]
        assert not _rectangles_overlap(
            envelope["x"],
            envelope["y"],
            envelope["length_x"],
            envelope["width_y"],
            dry["x"],
            dry["y"],
            dry["length_x"],
            dry["width_y"],
        )
        for tile in layout["tile_origins"]:
            x, y, length, width = _septum_access_window_for_tile_for_test(tile, params)
            assert not _rectangles_overlap(
                envelope["x"],
                envelope["y"],
                envelope["length_x"],
                envelope["width_y"],
                x,
                y,
                length,
                width,
            )


def test_operating_service_dress_check_combines_attached_gas_and_electrical_services() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    rects = layout["operating_service_dress_envelopes"]
    spec = layout["operating_service_dress_check"]
    gas_rects = [
        rect
        for interface in layout["side_gas_service_interfaces"]
        for rect in interface["external_service_rects"]
    ]
    cable_rects = layout["sensor_service_cable_envelopes"]
    check = build_operating_service_dress_check(
        params,
        assembly_position=True,
    ).val()
    dry = layout["dry_bay_envelope"]
    adjacent_keepouts = layout["adjacent_deck_slot_keepouts"]
    expected_top_z = max(rect["z"] + rect["height_z"] for rect in rects)
    expected_xmin = min(rect["x"] for rect in rects)
    expected_ymin = min(rect["y"] for rect in rects)
    expected_zmin = min(rect["z"] for rect in rects)
    expected_xmax = max(rect["x"] + rect["length_x"] for rect in rects)
    expected_ymax = max(rect["y"] + rect["width_y"] for rect in rects)
    check_bb = check.BoundingBox()

    assert "operating_service_dress_check" not in installed
    assert "operating_service_dress_check" in validation
    assert spec["evidence_gate"] == "Gate 3 OT-2 placement"
    assert spec["cad_value"] == "220.60 x 348.75 x 43.30 mm / 11 envelopes"
    assert spec["failure_rule"] == (
        "tube_cable_contact_or_unmeasured_service_dress_blocks_ot2_operation"
    )
    assert spec["requires_physical_evidence"] is True
    assert "normal_ot2_operation_with_connected_services" in spec[
        "physical_claims_blocked"
    ]
    assert spec["body_rects"] == rects
    assert rects == [*gas_rects, *cable_rects]
    assert len(gas_rects) == 4 * len(layout["side_gas_service_interfaces"])
    assert len(cable_rects) == len(layout["sensor_service_connector_envelopes"])
    assert len(rects) == len({tuple(rect.items()) for rect in rects})
    assert len(check.Solids()) > 0
    assert round(check_bb.xmin, 2) == round(expected_xmin, 2)
    assert round(check_bb.ymin, 2) == round(expected_ymin, 2)
    assert round(check_bb.zmin, 2) == round(expected_zmin, 2)
    assert round(check_bb.xmax, 2) == round(expected_xmax, 2)
    assert round(check_bb.ymax, 2) == round(expected_ymax, 2)
    assert round(check_bb.zmax, 2) == round(expected_top_z, 2)
    assert layout["pipette_toolhead_swept_body"]["service_envelope_count"] == len(rects)

    gas_rect_names = {rect["name"] for rect in gas_rects}
    assert {
        "printed_fitting_envelope",
        "printed_barb_retention_bead_envelope",
        "strain_relief_envelope",
        "tube_envelope",
    }.issubset(gas_rect_names)
    assert all(
        rect["service_role"] == "external_electrical_service_cable_envelope"
        for rect in cable_rects
    )

    for rect in rects:
        assert not _rectangles_overlap(
            rect["x"],
            rect["y"],
            rect["length_x"],
            rect["width_y"],
            dry["x"],
            dry["y"],
            dry["length_x"],
            dry["width_y"],
        )
        for tile in layout["tile_origins"]:
            x, y, length, width = _septum_access_window_for_tile_for_test(tile, params)
            assert not _rectangles_overlap(
                rect["x"],
                rect["y"],
                rect["length_x"],
                rect["width_y"],
                x,
                y,
                length,
                width,
            )
        for keepout in adjacent_keepouts:
            if not _rectangles_overlap(
                rect["x"],
                rect["y"],
                rect["length_x"],
                rect["width_y"],
                keepout["x"],
                keepout["y"],
                keepout["length_x"],
                keepout["width_y"],
            ):
                continue
            clearance = rect["z"] - (keepout["z"] + keepout["height_z"])
            assert clearance >= params["deck_interface"]["side_service_vertical_clearance_z"]


def test_service_dress_over_pipette_field_is_opt_in_gate3_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    misdressed = build_row_coupon_service_parts(
        params,
        mode="service_dress_over_pipette_field",
    )
    installed_names = set(installed)
    removed_parts = {
        "cots_gas_service_tubes",
        "lower_sensor_service_cable_pigtail",
        "lid_sensor_service_cable_pigtails",
    }
    rects = layout["misdressed_service_bundle_review"]
    toolhead = layout["pipette_toolhead_swept_body"]
    review = misdressed["misdressed_service_bundle_review"].val()
    direct_review = build_misdressed_service_bundle_review(
        params,
        assembly_position=True,
    ).val()
    review_bb = review.BoundingBox()
    direct_bb = direct_review.BoundingBox()
    expected_xmin = min(float(rect["x"]) for rect in rects)
    expected_ymin = min(float(rect["y"]) for rect in rects)
    expected_zmin = min(float(rect["z"]) for rect in rects)
    expected_xmax = max(float(rect["x"]) + float(rect["length_x"]) for rect in rects)
    expected_ymax = max(float(rect["y"]) + float(rect["width_y"]) for rect in rects)
    expected_zmax = max(float(rect["z"]) + float(rect["height_z"]) for rect in rects)

    assert "service_dress_over_pipette_field" in ROW_COUPON_SERVICE_MODES
    assert "misdressed_service_bundle_review" not in installed
    assert "misdressed_service_bundle_review" not in validation
    assert removed_parts < installed_names
    assert removed_parts.isdisjoint(misdressed)
    assert set(misdressed) - installed_names == {"misdressed_service_bundle_review"}
    assert "lower_sensor_service_connector" in misdressed
    assert "lid_sensor_service_connectors" in misdressed
    assert len(rects) == len(layout["tile_origins"])
    assert len(review.Solids()) == len(rects)
    assert round(review_bb.xmin, 2) == round(direct_bb.xmin, 2)
    assert round(review_bb.ymin, 2) == round(direct_bb.ymin, 2)
    assert round(review_bb.zmin, 2) == round(direct_bb.zmin, 2)
    assert round(review_bb.xmax, 2) == round(direct_bb.xmax, 2)
    assert round(review_bb.ymax, 2) == round(direct_bb.ymax, 2)
    assert round(review_bb.zmax, 2) == round(direct_bb.zmax, 2)
    assert round(review_bb.xmin, 2) == round(expected_xmin, 2)
    assert round(review_bb.ymin, 2) == round(expected_ymin, 2)
    assert round(review_bb.zmin, 2) == round(expected_zmin, 2)
    assert round(review_bb.xmax, 2) == round(expected_xmax, 2)
    assert round(review_bb.ymax, 2) == round(expected_ymax, 2)
    assert round(review_bb.zmax, 2) == round(expected_zmax, 2)

    tiles_by_index = {tile["index"]: tile for tile in layout["tile_origins"]}
    for rect in rects:
        tile = tiles_by_index[rect["tile_index"]]
        x, y, length, width = _septum_access_window_for_tile_for_test(tile, params)
        assert rect["review_state"] == "service_dress_over_pipette_field"
        assert rect["owner_part"] == "misdressed_service_bundle_review"
        assert rect["retained_part"] == "gas_and_electrical_service_leads"
        assert rect["overlaps_septum_access_window"] is True
        assert _rectangles_overlap(
            rect["x"],
            rect["y"],
            rect["length_x"],
            rect["width_y"],
            x,
            y,
            length,
            width,
        )
        assert rect["z"] >= toolhead["z"]
        assert rect["z"] + rect["height_z"] <= toolhead["z"] + toolhead["height_z"]
        assert {
            "operating_service_dress_check",
            "row_tiling_service_clearance_check",
            "pipette_toolhead_swept_body_check",
        } == set(rect["source_validation_checks"])


def test_service_dress_adjacent_slot_collision_is_opt_in_gate3_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    collided = build_row_coupon_service_parts(
        params,
        mode="service_dress_adjacent_slot_collision",
    )
    installed_names = set(installed)
    removed_parts = {
        "cots_gas_service_tubes",
        "lower_sensor_service_cable_pigtail",
        "lid_sensor_service_cable_pigtails",
    }
    rects = layout["adjacent_slot_service_collision_review"]
    keepouts_by_name = {
        keepout["name"]: keepout for keepout in layout["adjacent_deck_slot_keepouts"]
    }
    review = collided["adjacent_slot_service_collision_review"].val()
    direct_review = build_adjacent_slot_service_collision_review(
        params,
        assembly_position=True,
    ).val()
    review_bb = review.BoundingBox()
    direct_bb = direct_review.BoundingBox()
    expected_xmin = min(float(rect["x"]) for rect in rects)
    expected_ymin = min(float(rect["y"]) for rect in rects)
    expected_zmin = min(float(rect["z"]) for rect in rects)
    expected_xmax = max(float(rect["x"]) + float(rect["length_x"]) for rect in rects)
    expected_ymax = max(float(rect["y"]) + float(rect["width_y"]) for rect in rects)
    expected_zmax = max(float(rect["z"]) + float(rect["height_z"]) for rect in rects)

    assert "service_dress_adjacent_slot_collision" in ROW_COUPON_SERVICE_MODES
    assert "adjacent_slot_service_collision_review" not in installed
    assert "adjacent_slot_service_collision_review" not in validation
    assert removed_parts < installed_names
    assert removed_parts.isdisjoint(collided)
    assert set(collided) - installed_names == {"adjacent_slot_service_collision_review"}
    assert "lower_sensor_service_connector" in collided
    assert "lid_sensor_service_connectors" in collided
    assert len(rects) == len(layout["adjacent_deck_slot_keepouts"])
    assert len(rects) > 0
    assert len(review.Solids()) > 0
    assert round(review_bb.xmin, 2) == round(direct_bb.xmin, 2)
    assert round(review_bb.ymin, 2) == round(direct_bb.ymin, 2)
    assert round(review_bb.zmin, 2) == round(direct_bb.zmin, 2)
    assert round(review_bb.xmax, 2) == round(direct_bb.xmax, 2)
    assert round(review_bb.ymax, 2) == round(direct_bb.ymax, 2)
    assert round(review_bb.zmax, 2) == round(direct_bb.zmax, 2)
    assert round(review_bb.xmin, 2) == round(expected_xmin, 2)
    assert round(review_bb.ymin, 2) == round(expected_ymin, 2)
    assert round(review_bb.zmin, 2) == round(expected_zmin, 2)
    assert round(review_bb.xmax, 2) == round(expected_xmax, 2)
    assert round(review_bb.ymax, 2) == round(expected_ymax, 2)
    assert round(review_bb.zmax, 2) == round(expected_zmax, 2)

    for rect in rects:
        keepout = keepouts_by_name[rect["source_keepout_name"]]
        assert rect["review_state"] == "service_dress_adjacent_slot_collision"
        assert rect["owner_part"] == "adjacent_slot_service_collision_review"
        assert rect["blocked_fail_closed_state"] == "adjacent_slot_service_collision"
        assert rect["collides_with_adjacent_slot_keepout"] is True
        assert rect["vertical_clearance_z"] < 0
        assert rect["x"] >= keepout["x"]
        assert rect["y"] >= keepout["y"]
        assert rect["z"] >= keepout["z"]
        assert rect["x"] + rect["length_x"] <= keepout["x"] + keepout["length_x"]
        assert rect["y"] + rect["width_y"] <= keepout["y"] + keepout["width_y"]
        assert rect["z"] + rect["height_z"] <= keepout["z"] + keepout["height_z"]
        assert _rectangles_overlap(
            rect["x"],
            rect["y"],
            rect["length_x"],
            rect["width_y"],
            keepout["x"],
            keepout["y"],
            keepout["length_x"],
            keepout["width_y"],
        )
        assert {
            "adjacent_deck_slot_keepout_check",
            "row_tiling_service_clearance_check",
            "operating_service_dress_check",
        } == set(rect["source_validation_checks"])


def test_row_tiling_service_clearance_check_combines_neighbors_and_services() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    row_tiling = layout["row_tiling_service_clearance_check"]
    rects = row_tiling["review_rects"]
    module_rect = row_tiling["module_footprint_rect"]
    adjacent_keepouts = layout["adjacent_deck_slot_keepouts"]
    service_rects = layout["operating_service_dress_envelopes"]
    clearance = layout["side_gas_adjacent_slot_clearance"]
    check = build_row_tiling_service_clearance_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()
    expected_xmin = min(float(rect["x"]) for rect in rects)
    expected_ymin = min(float(rect["y"]) for rect in rects)
    expected_zmin = min(float(rect["z"]) for rect in rects)
    expected_xmax = max(float(rect["x"]) + float(rect["length_x"]) for rect in rects)
    expected_ymax = max(float(rect["y"]) + float(rect["width_y"]) for rect in rects)
    expected_zmax = max(float(rect["z"]) + float(rect["height_z"]) for rect in rects)

    assert "row_tiling_service_clearance_check" not in installed
    assert "row_tiling_service_clearance_check" in validation
    assert row_tiling["validation"] == "cad_proxy_physical_adjacent_slot_review_pending"
    assert row_tiling["failure_rule"] == (
        "neighbor_slot_interference_or_unmeasured_service_clearance_blocks_ot2_operation"
    )
    assert row_tiling["evidence_gate"] == "Gate 3 OT-2 placement"
    assert row_tiling["cad_value"] == (
        "8 neighbor keepouts / 11 service envelopes / 4.10 mm minimum clearance"
    )
    assert row_tiling["requires_physical_evidence"] is True
    assert "normal_ot2_operation_in_adjacent_deck_slots" in row_tiling[
        "physical_claims_blocked"
    ]
    assert row_tiling["tile_count"] == len(layout["tile_origins"])
    assert row_tiling["adjacent_keepout_count"] == len(adjacent_keepouts)
    assert row_tiling["service_envelope_count"] == len(service_rects)
    assert row_tiling["required_vertical_clearance_z"] == clearance[
        "required_vertical_clearance_z"
    ]
    assert row_tiling["min_vertical_clearance_z"] == clearance[
        "min_vertical_clearance_z"
    ]
    assert row_tiling["meets_vertical_clearance"] is True
    assert module_rect == rects[0]
    assert module_rect["x"] == 0.0
    assert module_rect["y"] == 0.0
    assert module_rect["z"] == layout["deck_plane_z"]
    assert module_rect["length_x"] == layout["length_x"]
    assert module_rect["width_y"] == layout["width_y"]
    assert len(rects) == 1 + len(adjacent_keepouts) + len(service_rects)
    assert {rect["review_group"] for rect in rects} == {
        "installed_module_footprint",
        "neighbor_slot_keepout",
        "operating_service_dress",
    }
    assert len(check.Solids()) > 0
    assert round(check_bb.xmin, 2) == round(expected_xmin, 2)
    assert round(check_bb.ymin, 2) == round(expected_ymin, 2)
    assert round(check_bb.zmin, 2) == round(expected_zmin, 2)
    assert round(check_bb.xmax, 2) == round(expected_xmax, 2)
    assert round(check_bb.ymax, 2) == round(expected_ymax, 2)
    assert round(check_bb.zmax, 2) == round(expected_zmax, 2)


def test_sensor_installation_workflow_is_modeled_for_production_prototype() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    steps = layout["sensor_installation_steps"]
    gates = layout["sensor_prototype_test_gates"]
    spec = layout["sensor_installation_path_check"]
    check = build_sensor_installation_path_check(params, assembly_position=True).val()
    check_bb = check.BoundingBox()
    rects = spec["body_rects"]
    expected_xmin = min(float(rect["x"]) for rect in rects)
    expected_ymin = min(float(rect["y"]) for rect in rects)
    expected_zmin = min(float(rect["z"]) for rect in rects)
    expected_xmax = max(float(rect["x"]) + float(rect["length_x"]) for rect in rects)
    expected_ymax = max(float(rect["y"]) + float(rect["width_y"]) for rect in rects)
    expected_zmax = max(float(rect["z"]) + float(rect["height_z"]) for rect in rects)

    assert len(steps) == (
        len(layout["gas_sensor_pcb_mounts"])
        + len(layout["headspace_sht41_mounts"])
        + len(layout["ir_sensor_mounts"])
    )
    assert len(gates) == params["sensor_installation"]["test_gate_count"]
    assert {gate["name"] for gate in gates} == {
        "incoming_module_electrical",
        "pocket_fit_and_retention",
        "aperture_registration",
        "installed_dry_electrical",
        "environmental_step_response",
        "wet_nonbiological_exposure",
        "bsl1_biology_commissioning",
    }
    assert len(check.Solids()) == len(steps)
    assert spec["validation"] == "required_gate6_real_sensor_install_serviceability_evidence"
    assert spec["failure_rule"] == (
        "unproven_install_path_retention_or_aperture_registration_blocks_sensor_thermal_pass"
    )
    assert spec["evidence_gate"] == "Gate 6 sensor/thermal"
    assert spec["cad_value"] == "10 steps / 7 gates"
    assert spec["install_step_count"] == len(steps)
    assert spec["test_gate_count"] == len(gates)
    assert spec["module_kind_counts"] == {
        "gas_sensor_pcb_cartridge": 2,
        "headspace_sht41_microcarrier": 4,
        "lower_ir_thermopile": 4,
    }
    assert spec["requires_physical_evidence"] is True
    assert spec["requires_real_sensor_inventory"] is True
    assert "local_headspace_sht41_sensors_installed" in spec["physical_claims_blocked"]
    assert "local_ir_thermopiles_installed" in spec["physical_claims_blocked"]
    assert len(rects) == len(steps)
    assert round(check_bb.xmin, 2) == round(expected_xmin, 2)
    assert round(check_bb.ymin, 2) == round(expected_ymin, 2)
    assert round(check_bb.zmin, 2) == round(expected_zmin, 2)
    assert round(check_bb.xmax, 2) == round(expected_xmax, 2)
    assert round(check_bb.ymax, 2) == round(expected_ymax, 2)
    assert round(check_bb.zmax, 2) == round(expected_zmax, 2)

    by_kind: dict[str, list[dict]] = {}
    for step in steps:
        by_kind.setdefault(step["module_kind"], []).append(step)
        assert "no_screws_no_glue" in step["retention"]
        assert step["installed_rect"]["length_x"] > 0
        assert step["installed_rect"]["width_y"] > 0
        assert step["installed_rect"]["height_z"] > 0
        assert any(abs(float(step["service_vector"][axis])) > 0 for axis in ("dx", "dy", "dz"))

    assert len(by_kind["gas_sensor_pcb_cartridge"]) == 2
    assert len(by_kind["headspace_sht41_microcarrier"]) == 4
    assert len(by_kind["lower_ir_thermopile"]) == 4
    for step in by_kind["gas_sensor_pcb_cartridge"]:
        assert step["install_direction"].startswith("-Z")
        assert step["service_vector"]["dz"] == params["sensor_installation"][
            "gas_pcb_service_lift_z"
        ]
        assert step["aperture_registration"] == "gas duct wall aperture to PCB sensor aperture"
    for step in by_kind["headspace_sht41_microcarrier"]:
        assert step["install_direction"].startswith("-X")
        assert step["service_vector"]["dx"] == params["sensor_installation"][
            "sht41_service_offset_x"
        ]
    for step in by_kind["lower_ir_thermopile"]:
        assert step["install_direction"].startswith("+Z")
        assert step["service_vector"]["dz"] == -params["sensor_installation"]["ir_service_drop_z"]


def test_gas_pcbs_missing_is_opt_in_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    missing_state = build_row_coupon_service_parts(params, mode="gas_pcbs_missing")
    installed_part_names = set(installed)
    witnesses = missing_state["missing_gas_pcb_cartridge_witnesses"].val()
    witness_bb = witnesses.BoundingBox()
    pcb_bb = installed["gas_sensor_pcbs"].val().BoundingBox()

    assert "gas_pcbs_missing" in ROW_COUPON_SERVICE_MODES
    assert "gas_sensor_pcbs" in installed
    assert "gas_pcb_interface_gaskets" in installed
    assert "printed_gas_pcb_keeper_doors" in installed
    assert "gas_sensor_pcbs" not in missing_state
    assert "gas_pcb_interface_gaskets" not in missing_state
    assert "printed_gas_pcb_keeper_doors" in missing_state
    assert "missing_gas_pcb_cartridge_witnesses" not in installed
    assert "missing_gas_pcb_cartridge_witnesses" not in validation
    assert installed_part_names - set(missing_state) == {
        "gas_sensor_pcbs",
        "gas_pcb_interface_gaskets",
    }
    assert set(missing_state) - installed_part_names == {
        "missing_gas_pcb_cartridge_witnesses"
    }
    assert witnesses.Volume() > 0
    assert round(witness_bb.xmin, 2) <= round(pcb_bb.xmin, 2)
    assert round(witness_bb.xmax, 2) >= round(pcb_bb.xmax, 2)
    assert round(witness_bb.ymin, 2) <= round(pcb_bb.ymin, 2)
    assert round(witness_bb.ymax, 2) >= round(pcb_bb.ymax, 2)

    witness_rects = layout["missing_gas_pcb_cartridge_witnesses"]
    by_kind: dict[str, list[dict]] = {}
    for witness in witness_rects:
        by_kind.setdefault(witness["witness_kind"], []).append(witness)
        assert witness["review_state"] == "gas_pcbs_missing"
        assert witness["role"] in {"supply", "return"}
    assert len(by_kind["cartridge_top_footprint"]) == len(layout["gas_sensor_pcb_mounts"])
    assert len(by_kind["duct_seal_gasket"]) == len(layout["gas_sensor_pcb_mounts"])

    mounts_by_role = {mount["role"]: mount for mount in layout["gas_sensor_pcb_mounts"]}
    for witness in by_kind["cartridge_top_footprint"]:
        mount = mounts_by_role[witness["role"]]
        assert witness["removed_part"] == "gas_sensor_pcbs"
        assert witness["dependent_removed_part"] == "gas_pcb_interface_gaskets"
        assert witness["x"] == mount["x"]
        assert witness["y"] == mount["y"]
        assert witness["z"] == round(mount["z"] + mount["height_z"], 3)
        assert witness["length_x"] == mount["length_x"]
        assert witness["width_y"] == mount["width_y"]
        assert witness["height_z"] == production["missing_gas_pcb_witness_height_z"]
        assert witness["rail_width"] == production["missing_gas_pcb_witness_frame_width_xy"]

    for witness in by_kind["duct_seal_gasket"]:
        gasket = mounts_by_role[witness["role"]]["gas_interface"]["gasket_rect"]
        assert witness["removed_part"] == "gas_pcb_interface_gaskets"
        assert witness["dependent_removed_part"] == "gas_sensor_pcbs"
        assert witness["x"] == gasket["x"]
        assert witness["y"] == gasket["y"]
        assert witness["z"] == gasket["z"]
        assert witness["length_x"] == gasket["length_x"]
        assert witness["width_y"] == gasket["width_y"]
        assert witness["height_z"] == gasket["height_z"]

    direct_witnesses = build_missing_gas_pcb_cartridge_witnesses(
        params,
        assembly_position=True,
    ).val()
    assert round(direct_witnesses.BoundingBox().zmax, 2) == round(witness_bb.zmax, 2)


def test_gas_pcb_cartridges_unseated_is_distinct_from_missing_pcbs() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    missing_state = build_row_coupon_service_parts(params, mode="gas_pcbs_missing")
    unseated_state = build_row_coupon_service_parts(
        params,
        mode="gas_pcb_cartridges_unseated",
    )
    review = unseated_state["unseated_gas_pcb_cartridges_review"].val()
    direct_review = build_unseated_gas_pcb_cartridges_review(
        params,
        assembly_position=True,
    ).val()
    review_rects = layout["unseated_gas_pcb_cartridges_review"]
    mounts_by_name = {mount["name"]: mount for mount in layout["gas_sensor_pcb_mounts"]}

    assert "gas_pcb_cartridges_unseated" in ROW_COUPON_SERVICE_MODES
    assert {"gas_sensor_pcbs", "gas_pcb_interface_gaskets"}.issubset(installed)
    assert "printed_gas_pcb_keeper_doors" in installed
    assert "gas_sensor_pcbs" not in missing_state
    assert "gas_pcb_interface_gaskets" not in missing_state
    assert "gas_sensor_pcbs" not in unseated_state
    assert "printed_gas_pcb_keeper_doors" not in unseated_state
    assert "gas_pcb_interface_gaskets" in unseated_state
    assert "unseated_gas_pcb_cartridges_review" in unseated_state
    assert "unseated_gas_pcb_cartridges_review" not in installed
    assert "unseated_gas_pcb_cartridges_review" not in validation
    assert review.Volume() == pytest.approx(direct_review.Volume())
    assert review.Volume() > installed["gas_sensor_pcbs"].val().Volume()
    assert len(review_rects) == len(layout["gas_sensor_pcb_mounts"]) == 2

    for rect in review_rects:
        mount = mounts_by_name[rect["source_rect_name"]]
        gasket = mount["gas_interface"]["gasket_rect"]
        assert rect["review_state"] == "gas_pcb_cartridges_unseated"
        assert rect["removed_part"] == "gas_sensor_pcbs"
        assert rect["dependent_removed_part"] == "printed_gas_pcb_keeper_doors"
        assert rect["retained_part"] == "gas_pcb_interface_gaskets"
        assert rect["owner_part"] == "unseated_gas_pcb_cartridges_review"
        assert rect["meaning"] == (
            "gas PCB cartridge is present but lifted off the compressed "
            "duct sampling gasket"
        )
        assert rect["unseated_offset_z"] == params["sensor_installation"][
            "gas_pcb_service_lift_z"
        ]
        assert rect["x"] == mount["x"]
        assert rect["y"] == mount["y"]
        assert rect["z"] == round(
            mount["z"] + params["sensor_installation"]["gas_pcb_service_lift_z"],
            3,
        )
        assert rect["pcb_rect"]["length_x"] == mount["length_x"]
        assert rect["pcb_rect"]["width_y"] == mount["width_y"]
        assert rect["keeper_door_rect"]["z"] > rect["pcb_rect"]["z"]
        assert rect["keeper_tab_rect"]["z"] == rect["keeper_door_rect"]["z"]
        assert gasket["z"] < rect["pcb_rect"]["z"]


def test_local_sensors_missing_is_opt_in_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    missing_state = build_row_coupon_service_parts(params, mode="local_sensors_missing")
    installed_part_names = set(installed)
    removed_parts = {
        "headspace_sht41_microcarriers",
        "ir_thermopiles",
        "ir_thermopile_face_gaskets",
    }
    kept_support_parts = {
        "lid_sensor_harness",
        "lower_sensor_harness",
        "lid_harness_cover",
        "lower_harness_cover",
        "lid_sensor_service_connectors",
        "lower_sensor_service_connector",
    }

    assert "local_sensors_missing" in ROW_COUPON_SERVICE_MODES
    assert removed_parts.issubset(installed)
    assert removed_parts.isdisjoint(missing_state)
    assert kept_support_parts.issubset(missing_state)
    assert "missing_local_sensor_witnesses" not in installed
    assert "missing_local_sensor_witnesses" not in validation
    assert installed_part_names - set(missing_state) == removed_parts
    assert set(missing_state) - installed_part_names == {"missing_local_sensor_witnesses"}

    witness = missing_state["missing_local_sensor_witnesses"].val()
    direct_witness = build_missing_local_sensor_witnesses(
        params,
        assembly_position=True,
    ).val()
    assert witness.Volume() > 0
    assert round(witness.BoundingBox().zmax, 2) == round(
        direct_witness.BoundingBox().zmax,
        2,
    )

    witness_rects = layout["missing_local_sensor_witnesses"]
    by_kind: dict[str, list[dict]] = {}
    for rect in witness_rects:
        by_kind.setdefault(rect["witness_kind"], []).append(rect)
        assert rect["review_state"] == "local_sensors_missing"
        assert rect["tile_index"] in {
            mount["tile_index"] for mount in layout["headspace_sht41_mounts"]
        }
    assert len(by_kind["headspace_sht41_carrier_footprint"]) == len(
        layout["headspace_sht41_mounts"]
    )
    assert len(by_kind["ir_thermopile_body_footprint"]) == len(
        layout["ir_sensor_mounts"]
    )
    assert len(by_kind["ir_face_gasket_seal"]) == len(layout["ir_sensor_mounts"])

    sht_mounts = {mount["name"]: mount for mount in layout["headspace_sht41_mounts"]}
    ir_mounts = {mount["name"]: mount for mount in layout["ir_sensor_mounts"]}
    for rect in by_kind["headspace_sht41_carrier_footprint"]:
        mount = sht_mounts[rect["source_rect_name"]]
        assert rect["sensor_kind"] == "headspace_sht41_microcarrier"
        assert rect["removed_part"] == "headspace_sht41_microcarriers"
        assert rect["x"] == mount["x"]
        assert rect["y"] == mount["y"]
        assert rect["z"] == round(mount["z"] + mount["height_z"], 3)
        assert rect["length_x"] == mount["length_x"]
        assert rect["width_y"] == mount["width_y"]
        assert rect["height_z"] == production.get(
            "missing_local_sensor_witness_height_z",
            0.7,
        )
        assert rect["rail_width"] == production.get(
            "missing_local_sensor_witness_frame_width_xy",
            0.9,
        )

    for rect in by_kind["ir_thermopile_body_footprint"]:
        mount = ir_mounts[rect["source_rect_name"]]
        assert rect["sensor_kind"] == "lower_ir_thermopile"
        assert rect["removed_part"] == "ir_thermopiles"
        assert rect["dependent_removed_part"] == "ir_thermopile_face_gaskets"
        assert rect["x"] == mount["x"]
        assert rect["y"] == mount["y"]
        assert rect["z"] == round(mount["z"] + mount["height_z"], 3)
        assert rect["length_x"] == mount["length_x"]
        assert rect["width_y"] == mount["width_y"]

    for rect in by_kind["ir_face_gasket_seal"]:
        gasket = ir_mounts[rect["source_rect_name"]]["face_gasket"]
        assert rect["sensor_kind"] == "lower_ir_face_gasket"
        assert rect["removed_part"] == "ir_thermopile_face_gaskets"
        assert rect["dependent_removed_part"] == "ir_thermopiles"
        assert rect["center_x"] == gasket["x"]
        assert rect["center_y"] == gasket["y"]
        assert rect["z"] == gasket["z"]
        assert rect["outer_diameter"] == gasket["outer_diameter"]
        assert rect["inner_diameter"] == gasket["inner_diameter"]


def test_service_leads_missing_is_opt_in_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    missing_state = build_row_coupon_service_parts(params, mode="service_leads_missing")
    installed_part_names = set(installed)
    removed_parts = {
        "cots_gas_service_tubes",
        "lower_sensor_service_cable_pigtail",
        "lid_sensor_service_cable_pigtails",
    }
    kept_printed_interfaces = {
        "lid_cover",
        "lower_sensor_service_connector",
        "printed_lower_sensor_connector_shroud",
        "lid_sensor_service_connectors",
        "printed_lid_sensor_connector_shrouds",
    }

    assert "service_leads_missing" in ROW_COUPON_SERVICE_MODES
    assert removed_parts.issubset(installed)
    assert removed_parts.isdisjoint(missing_state)
    assert kept_printed_interfaces.issubset(missing_state)
    assert "missing_service_lead_witnesses" not in installed
    assert "missing_service_lead_witnesses" not in validation
    assert installed_part_names - set(missing_state) == removed_parts
    assert set(missing_state) - installed_part_names == {"missing_service_lead_witnesses"}

    witness = missing_state["missing_service_lead_witnesses"].val()
    direct_witness = build_missing_service_lead_witnesses(
        params,
        assembly_position=True,
    ).val()
    assert witness.Volume() > 0
    assert round(witness.BoundingBox().zmax, 2) == round(
        direct_witness.BoundingBox().zmax,
        2,
    )

    witness_rects = layout["missing_service_lead_witnesses"]
    by_kind: dict[str, list[dict]] = {}
    for rect in witness_rects:
        by_kind.setdefault(rect["witness_kind"], []).append(rect)
        assert rect["review_state"] == "service_leads_missing"
        assert rect["height_z"] == production["missing_service_lead_witness_height_z"]
        assert rect["rail_width"] == production[
            "missing_service_lead_witness_frame_width_xy"
        ]
    assert len(by_kind["gas_tube_handoff"]) == len(layout["cots_gas_service_tubes"])
    assert len(by_kind["electrical_cable_handoff"]) == len(
        layout["sensor_service_cable_pigtails"]
    )

    tubes_by_name = {tube["name"]: tube for tube in layout["cots_gas_service_tubes"]}
    pigtails_by_name = {
        pigtail["name"]: pigtail for pigtail in layout["sensor_service_cable_pigtails"]
    }
    span = production["missing_service_lead_witness_span_xy"]
    for rect in by_kind["gas_tube_handoff"]:
        tube = tubes_by_name[rect["source_rect_name"]]
        body = tube["body_rect"]
        assert rect["removed_part"] == "cots_gas_service_tubes"
        assert rect["role"] == tube["role"]
        assert rect["z"] == round(body["z"] + body["height_z"], 3)
        if tube["axis"] == "x":
            expected_length = min(span, body["length_x"])
            expected_x = body["x"]
            if tube["route_axis"] == "-X":
                expected_x = body["x"] + body["length_x"] - expected_length
            assert rect["x"] == round(expected_x, 3)
            assert rect["y"] == body["y"]
            assert rect["length_x"] == round(expected_length, 3)
            assert rect["width_y"] == body["width_y"]
        else:
            expected_width = min(span, body["width_y"])
            expected_y = body["y"]
            if tube["route_axis"] == "-Y":
                expected_y = body["y"] + body["width_y"] - expected_width
            assert rect["x"] == body["x"]
            assert rect["y"] == round(expected_y, 3)
            assert rect["length_x"] == body["length_x"]
            assert rect["width_y"] == round(expected_width, 3)

    for rect in by_kind["electrical_cable_handoff"]:
        pigtail = pigtails_by_name[rect["source_rect_name"]]
        expected_removed_part = (
            "lower_sensor_service_cable_pigtail"
            if pigtail["connector_name"].startswith("lower_")
            else "lid_sensor_service_cable_pigtails"
        )
        assert rect["removed_part"] == expected_removed_part
        assert rect["role"] == pigtail["connector_name"]
        assert rect["x"] == pigtail["x"]
        assert rect["y"] == pigtail["y"]
        assert rect["z"] == round(pigtail["z"] + pigtail["height_z"], 3)
        assert rect["length_x"] == pigtail["length_x"]
        assert rect["width_y"] == round(min(span, pigtail["width_y"]), 3)
        assert rect["route_axis"] == pigtail["route_axis"]


def test_side_gas_tubes_unseated_is_distinct_from_missing_service_leads() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    unseated_state = build_row_coupon_service_parts(
        params,
        mode="side_gas_tubes_unseated",
    )
    missing_state = build_row_coupon_service_parts(params, mode="service_leads_missing")
    installed_tubes = build_cots_gas_service_tubes(
        params,
        assembly_position=True,
    ).val()
    direct_review = build_unseated_side_gas_tubes_review(
        params,
        assembly_position=True,
    ).val()
    review_specs = layout["unseated_side_gas_tubes_review"]
    tubes_by_name = {tube["name"]: tube for tube in layout["cots_gas_service_tubes"]}

    assert "side_gas_tubes_unseated" in ROW_COUPON_SERVICE_MODES
    assert "cots_gas_service_tubes" in installed
    assert "cots_gas_service_tubes" not in unseated_state
    assert "cots_gas_service_tubes" not in missing_state
    assert "unseated_side_gas_tubes_review" in unseated_state
    assert "unseated_side_gas_tubes_review" not in installed
    assert "unseated_side_gas_tubes_review" not in validation
    assert "missing_service_lead_witnesses" not in unseated_state
    assert "lower_sensor_service_cable_pigtail" in unseated_state
    assert "lid_sensor_service_cable_pigtails" in unseated_state
    assert unseated_state["unseated_side_gas_tubes_review"].val().Volume() == (
        pytest.approx(direct_review.Volume())
    )
    assert direct_review.Volume() == pytest.approx(installed_tubes.Volume())
    assert len(review_specs) == len(layout["cots_gas_service_tubes"]) == 2

    for spec in review_specs:
        tube = tubes_by_name[spec["source_rect_name"]]
        assert spec["review_state"] == "side_gas_tubes_unseated"
        assert spec["removed_part"] == "cots_gas_service_tubes"
        assert spec["owner_part"] == "unseated_side_gas_tubes_review"
        assert spec["meaning"] == (
            "COTS gas tube is present but pulled off the printed barb"
        )
        assert spec["diameter"] == tube["diameter"]
        assert spec["inner_diameter"] == tube["inner_diameter"]
        assert spec["flow_bore_diameter"] == tube["flow_bore_diameter"]
        assert spec["unseated_offset_xy"] == params["production_assembly"].get(
            "side_gas_unseated_review_offset_xy",
            8.0,
        )
        assert spec["body_rect"]["z"] == tube["body_rect"]["z"]
        if spec["axis"] == "x":
            expected_dx = (
                -spec["unseated_offset_xy"]
                if tube["route_axis"] == "-X"
                else spec["unseated_offset_xy"]
            )
            assert spec["x"] == round(tube["x"] + expected_dx, 3)
            assert spec["y"] == tube["y"]
            assert spec["body_rect"]["x"] == round(
                tube["body_rect"]["x"] + expected_dx,
                3,
            )
            assert spec["body_rect"]["y"] == tube["body_rect"]["y"]
        else:
            expected_dy = (
                spec["unseated_offset_xy"]
                if tube["route_axis"] == "+Y"
                else -spec["unseated_offset_xy"]
            )
            assert spec["y"] == round(tube["y"] + expected_dy, 3)
            assert spec["x"] == tube["x"]
            assert spec["body_rect"]["y"] == round(
                tube["body_rect"]["y"] + expected_dy,
                3,
            )
            assert spec["body_rect"]["x"] == tube["body_rect"]["x"]


def test_electrical_connectors_unmated_is_opt_in_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    unmated_state = build_row_coupon_service_parts(
        params,
        mode="electrical_connectors_unmated",
    )
    installed_part_names = set(installed)
    removed_parts = {
        "lower_sensor_service_connector",
        "lid_sensor_service_connectors",
        "lower_sensor_service_cable_pigtail",
        "lid_sensor_service_cable_pigtails",
    }
    kept_interfaces = {
        "lower_sensor_harness",
        "lower_harness_cover",
        "printed_lower_sensor_connector_shroud",
        "lid_sensor_harness",
        "lid_harness_cover",
        "printed_lid_sensor_connector_shrouds",
    }

    assert "electrical_connectors_unmated" in ROW_COUPON_SERVICE_MODES
    assert removed_parts.issubset(installed)
    assert removed_parts.isdisjoint(unmated_state)
    assert kept_interfaces.issubset(unmated_state)
    assert "unmated_sensor_service_connectors_review" not in installed
    assert "unmated_sensor_service_connectors_review" not in validation
    assert "electrical_connector_mating_state_check" in validation
    assert installed_part_names - set(unmated_state) == removed_parts
    assert set(unmated_state) - installed_part_names == {
        "unmated_sensor_service_connectors_review"
    }

    review = unmated_state["unmated_sensor_service_connectors_review"].val()
    direct_review = build_unmated_sensor_service_connectors_review(
        params,
        assembly_position=True,
    ).val()
    validation_check = build_electrical_connector_mating_state_check(
        params,
        assembly_position=True,
    ).val()
    assert review.Volume() > 0
    assert round(review.BoundingBox().zmax, 2) == round(
        direct_review.BoundingBox().zmax,
        2,
    )
    assert round(validation_check.BoundingBox().zmax, 2) == round(
        direct_review.BoundingBox().zmax,
        2,
    )

    rects = layout["unmated_sensor_service_connector_review_rects"]
    connectors = {
        connector["name"]: connector
        for connector in layout["sensor_service_connector_envelopes"]
    }
    connector_count = len(connectors)
    mating_state_check = layout["electrical_connector_mating_state_check"]
    assert mating_state_check["evidence_gate"] == "Gate 6 sensor/thermal"
    assert mating_state_check["cad_value"] == "3 connectors / 3 cable envelopes"
    assert mating_state_check["review_cad_value"] == (
        f"{connector_count} connectors / {len(rects)} mating-state review bodies"
    )
    assert mating_state_check["failure_rule"] == (
        "unmated_loose_or_unproven_connector_state_blocks_sensor_thermal_pass"
    )
    assert mating_state_check["requires_physical_evidence"] is True
    assert "continuous_sensor_electrical_service" in mating_state_check[
        "physical_claims_blocked"
    ]
    assert mating_state_check["body_rects"] == rects
    by_kind: dict[str, list[dict]] = {}
    for rect in rects:
        by_kind.setdefault(rect["review_kind"], []).append(rect)
        assert rect["review_state"] == "electrical_connectors_unmated"
        assert rect["connector_name"] in connectors
        assert rect["connector_family"] == params["sensor_harness"][
            "service_connector_family"
        ]
        assert rect["removed_connector_part"] in {
            "lower_sensor_service_connector",
            "lid_sensor_service_connectors",
        }
        assert rect["removed_pigtail_part"] in {
            "lower_sensor_service_cable_pigtail",
            "lid_sensor_service_cable_pigtails",
        }

    assert set(by_kind) == {
        "stationary_service_board",
        "stationary_header",
        "unmated_plug",
        "unmated_latch",
        "unmated_cable_pigtail",
        "mating_gap_witness",
    }
    assert all(len(kind_rects) == connector_count for kind_rects in by_kind.values())

    by_connector = {
        name: [rect for rect in rects if rect["connector_name"] == name]
        for name in connectors
    }
    for name, connector_rects in by_connector.items():
        connector = connectors[name]
        kinds = {rect["review_kind"]: rect for rect in connector_rects}
        y_offset = kinds["unmated_plug"]["unmated_offset_y"]
        assert y_offset > float(connector["plug_rect"]["width_y"])
        assert y_offset <= float(connector["service_clearance_rect"]["width_y"])
        assert kinds["stationary_service_board"]["y"] == connector["board_rect"]["y"]
        assert kinds["stationary_header"]["y"] == connector["header_rect"]["y"]
        assert kinds["unmated_plug"]["y"] == round(
            float(connector["plug_rect"]["y"]) + y_offset,
            3,
        )
        assert kinds["unmated_latch"]["y"] == round(
            float(connector["latch_rect"]["y"]) + y_offset,
            3,
        )
        assert kinds["unmated_cable_pigtail"]["y"] == round(
            float(connector["installed_cable_pigtail_rect"]["y"]) + y_offset,
            3,
        )
        assert kinds["mating_gap_witness"]["z"] > round(
            float(connector["plug_rect"]["z"]) + float(connector["plug_rect"]["height_z"]),
            3,
        )


def test_sample_relief_cap_negative_states_are_opt_in_review_modes() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    installed_part_names = set(installed)
    review_parts = {
        "sample_relief_cap_missing": "missing_sample_relief_cap_witness",
        "sample_relief_cap_unseated": "unseated_sample_relief_cap_review",
    }

    assert set(review_parts).issubset(ROW_COUPON_SERVICE_MODES)
    assert "adapter_missing" not in ROW_COUPON_SERVICE_MODES
    assert "port_caps_missing" not in ROW_COUPON_SERVICE_MODES
    assert "wrong_port_caps" not in ROW_COUPON_SERVICE_MODES
    for retired_mode in {"adapter_missing", "port_caps_missing", "wrong_port_caps"}:
        with pytest.raises(ValueError, match="row coupon service mode"):
            build_row_coupon_service_parts(params, mode=retired_mode)
    for mode, review_name in review_parts.items():
        state = build_row_coupon_service_parts(params, mode=mode)
        review = state[review_name].val()
        review_bb = review.BoundingBox()

        assert "printed_sample_relief_cap" in installed
        assert "printed_sample_relief_cap" not in state
        assert review_name not in installed
        assert review_name not in validation
        assert installed_part_names - set(state) == {"printed_sample_relief_cap"}
        assert set(state) - installed_part_names == {review_name}
        assert len(review.Solids()) == len(layout["lid_port_positions"])
        assert review.Volume() > 0
        assert round(review_bb.zmax, 2) > round(layout["lid_top_z"], 2)
        assert round(review_bb.zmax, 2) < round(layout["assembly_top_z"], 2)

    unseated = build_row_coupon_service_parts(params, mode="sample_relief_cap_unseated")[
        "unseated_sample_relief_cap_review"
    ].val()
    installed_caps = installed["printed_sample_relief_cap"].val()
    assert unseated.Volume() == pytest.approx(installed_caps.Volume(), rel=0.001)
    assert round(unseated.BoundingBox().zmin, 2) > round(
        installed_caps.BoundingBox().zmin,
        2,
    )


def test_latches_unseated_is_opt_in_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    unseated_state = build_row_coupon_service_parts(params, mode="latches_unseated")
    installed_locks = installed["printed_wedge_locks"].val()
    unseated_locks = unseated_state["unseated_wedge_locks_review"].val()
    witnesses = unseated_state["latch_unseated_witnesses"].val()
    installed_bb = installed_locks.BoundingBox()
    unseated_bb = unseated_locks.BoundingBox()
    witness_bb = witnesses.BoundingBox()

    assert "latches_unseated" in ROW_COUPON_SERVICE_MODES
    assert "printed_wedge_locks" in installed
    assert "printed_wedge_locks" not in unseated_state
    assert "unseated_wedge_locks_review" not in installed
    assert "latch_unseated_witnesses" not in installed
    assert "unseated_wedge_locks_review" not in validation
    assert "latch_unseated_witnesses" not in validation
    assert len(unseated_locks.Solids()) == len(layout["wedge_lock_rectangles"])
    assert len(witnesses.Solids()) == len(layout["wedge_lock_rectangles"])
    assert unseated_bb.xmin == round(
        installed_bb.xmin - production["wedge_unseated_review_offset_x"],
        2,
    )
    assert unseated_bb.xmax == round(
        installed_bb.xmax + production["wedge_unseated_review_offset_x"],
        2,
    )
    assert round(unseated_bb.zmin, 2) == round(installed_bb.zmin, 2)
    assert round(witness_bb.zmin, 2) == round(installed_bb.zmax, 2)
    assert round(witness_bb.zlen, 2) == production["wedge_unseated_witness_height_z"]

    direct_unseated = build_unseated_wedge_locks_review(
        params,
        assembly_position=True,
    ).val()
    direct_witnesses = build_latch_unseated_witnesses(
        params,
        assembly_position=True,
    ).val()
    assert round(direct_unseated.BoundingBox().xlen, 2) == round(unseated_bb.xlen, 2)
    assert round(direct_witnesses.BoundingBox().zlen, 2) == round(witness_bb.zlen, 2)


def test_septum_mats_missing_is_opt_in_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    missing_state = build_row_coupon_service_parts(params, mode="septum_mats_missing")
    installed_part_names = set(installed)
    witnesses = missing_state["missing_septum_mat_witnesses"].val()
    witness_bb = witnesses.BoundingBox()
    mat_bb = installed["cots_septum_mats"].val().BoundingBox()

    assert "septum_mats_missing" in ROW_COUPON_SERVICE_MODES
    assert "cots_septum_mats" in installed
    assert "cots_septum_mats" not in missing_state
    assert "missing_septum_mat_witnesses" not in installed
    assert "missing_septum_mat_witnesses" not in validation
    assert installed_part_names - set(missing_state) == {"cots_septum_mats"}
    assert set(missing_state) - installed_part_names == {"missing_septum_mat_witnesses"}
    assert len(layout["missing_septum_mat_witnesses"]) == params["row"]["plate_count"]
    assert witnesses.Volume() > 0
    assert round(witness_bb.xmin, 2) == round(mat_bb.xmin, 2)
    assert round(witness_bb.xmax, 2) == round(mat_bb.xmax, 2)
    assert round(witness_bb.ymin, 2) == round(mat_bb.ymin, 2)
    assert round(witness_bb.ymax, 2) == round(mat_bb.ymax, 2)
    assert round(witness_bb.zmin, 2) == round(
        layout["plate_top_z"] + params["septum_mat"]["sheet_thickness_z"],
        2,
    )
    assert round(witness_bb.zlen, 2) == production[
        "missing_septum_mat_witness_height_z"
    ]

    for witness, tile in zip(
        layout["missing_septum_mat_witnesses"],
        layout["tile_origins"],
        strict=True,
    ):
        assert witness["review_state"] == "septum_mats_missing"
        assert witness["removed_part"] == "cots_septum_mats"
        assert witness["tile_index"] == tile["index"]
        assert witness["x"] == tile["x"]
        assert witness["y"] == tile["y"]
        assert witness["length_x"] == params["plate"]["length_x"]
        assert witness["width_y"] == params["plate"]["width_y"]
        assert witness["rail_width"] == production[
            "missing_septum_mat_witness_frame_width_xy"
        ]

    direct_witnesses = build_missing_septum_mat_witnesses(
        params,
        assembly_position=True,
    ).val()
    assert round(direct_witnesses.BoundingBox().zlen, 2) == round(witness_bb.zlen, 2)


def test_microplates_missing_is_opt_in_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    missing_state = build_row_coupon_service_parts(params, mode="microplates_missing")
    installed_part_names = set(installed)
    witnesses = missing_state["missing_microplate_witnesses"].val()
    witness_bb = witnesses.BoundingBox()
    plate_bb = installed["cots_microplates"].val().BoundingBox()

    assert "microplates_missing" in ROW_COUPON_SERVICE_MODES
    assert "cots_microplates" in installed
    assert "cots_septum_mats" in installed
    assert "cots_microplates" not in missing_state
    assert "cots_septum_mats" not in missing_state
    assert "missing_microplate_witnesses" not in installed
    assert "missing_microplate_witnesses" not in validation
    assert installed_part_names - set(missing_state) == {
        "cots_microplates",
        "cots_septum_mats",
    }
    assert set(missing_state) - installed_part_names == {"missing_microplate_witnesses"}
    assert len(layout["missing_microplate_witnesses"]) == params["row"]["plate_count"]
    assert witnesses.Volume() > 0
    assert round(witness_bb.xmin, 2) == round(plate_bb.xmin, 2)
    assert round(witness_bb.xmax, 2) == round(plate_bb.xmax, 2)
    assert round(witness_bb.ymin, 2) == round(plate_bb.ymin, 2)
    assert round(witness_bb.ymax, 2) == round(plate_bb.ymax, 2)
    assert round(witness_bb.zmin, 2) == round(layout["plate_bottom_z"], 2)
    assert round(witness_bb.zlen, 2) == production[
        "missing_microplate_witness_height_z"
    ]

    for witness, tile in zip(
        layout["missing_microplate_witnesses"],
        layout["tile_origins"],
        strict=True,
    ):
        assert witness["review_state"] == "microplates_missing"
        assert witness["removed_part"] == "cots_microplates"
        assert witness["dependent_removed_part"] == "cots_septum_mats"
        assert witness["tile_index"] == tile["index"]
        assert witness["x"] == tile["x"]
        assert witness["y"] == tile["y"]
        assert witness["length_x"] == params["plate"]["length_x"]
        assert witness["width_y"] == params["plate"]["width_y"]
        assert witness["rail_width"] == production[
            "missing_microplate_witness_frame_width_xy"
        ]

    direct_witnesses = build_missing_microplate_witnesses(
        params,
        assembly_position=True,
    ).val()
    assert round(direct_witnesses.BoundingBox().zlen, 2) == round(witness_bb.zlen, 2)


def test_perimeter_gaskets_missing_is_opt_in_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    installed = build_row_coupon_service_parts(params, mode="installed")
    validation = build_row_coupon_validation_parts(params)
    missing_state = build_row_coupon_service_parts(params, mode="perimeter_gaskets_missing")
    installed_part_names = set(installed)
    witnesses = missing_state["missing_perimeter_gasket_witnesses"].val()
    witness_bb = witnesses.BoundingBox()
    gasket_pair = installed["lower_gasket"].union(installed["upper_gasket"]).val()
    gasket_bb = gasket_pair.BoundingBox()

    assert "perimeter_gaskets_missing" in ROW_COUPON_SERVICE_MODES
    assert "lower_gasket" in installed
    assert "upper_gasket" in installed
    assert "lower_gasket" not in missing_state
    assert "upper_gasket" not in missing_state
    assert "missing_perimeter_gasket_witnesses" not in installed
    assert "missing_perimeter_gasket_witnesses" not in validation
    assert installed_part_names - set(missing_state) == {"lower_gasket", "upper_gasket"}
    assert set(missing_state) - installed_part_names == {
        "missing_perimeter_gasket_witnesses"
    }
    assert witnesses.Volume() > 0
    assert round(witness_bb.xmin, 2) == round(gasket_bb.xmin, 2)
    assert round(witness_bb.xmax, 2) == round(gasket_bb.xmax, 2)
    assert round(witness_bb.ymin, 2) == round(gasket_bb.ymin, 2)
    assert round(witness_bb.ymax, 2) == round(gasket_bb.ymax, 2)
    assert round(witness_bb.zmin, 2) == round(gasket_bb.zmin, 2)
    assert round(witness_bb.zmax, 2) == round(gasket_bb.zmax, 2)

    assert len(layout["missing_perimeter_gasket_witnesses"]) == 2
    by_removed = {
        witness["removed_part"]: witness
        for witness in layout["missing_perimeter_gasket_witnesses"]
    }
    assert set(by_removed) == {"lower_gasket", "upper_gasket"}
    assert by_removed["lower_gasket"]["review_state"] == "perimeter_gaskets_missing"
    assert by_removed["upper_gasket"]["review_state"] == "perimeter_gaskets_missing"
    assert by_removed["lower_gasket"]["z"] == round(layout["base_top_z"], 3)
    assert by_removed["upper_gasket"]["z"] == round(layout["gasket_bottom_z"], 3)
    for witness in by_removed.values():
        assert witness["rail_width"] == seal["gasket_rail_width"]
        assert witness["height_z"] == seal["compressed_gasket_height_z"]

    direct_witnesses = build_missing_perimeter_gasket_witnesses(
        params,
        assembly_position=True,
    ).val()
    assert round(direct_witnesses.BoundingBox().zmax, 2) == round(witness_bb.zmax, 2)


def test_assembly_state_witness_check_exports_negative_state_witnesses() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    spec = layout["assembly_state_witness_check"]
    check = build_assembly_state_witness_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()
    source_witnesses = [
        (
            "sample_relief_cap_missing",
            "missing_sample_relief_cap_witness",
        ),
        ("latches_unseated", "latch_unseated_witnesses"),
        ("septum_mats_missing", "missing_septum_mat_witnesses"),
        ("microplates_missing", "missing_microplate_witnesses"),
        ("perimeter_gaskets_missing", "missing_perimeter_gasket_witnesses"),
        ("gas_pcbs_missing", "missing_gas_pcb_cartridge_witnesses"),
        ("gas_pcb_cartridges_unseated", "unseated_gas_pcb_cartridges_review"),
        ("local_sensors_missing", "missing_local_sensor_witnesses"),
        ("service_leads_missing", "missing_service_lead_witnesses"),
        ("side_gas_tubes_unseated", "unseated_side_gas_tubes_review"),
    ]

    assert "assembly_state_witness_check" in validation
    assert "assembly_state_witness_check" not in installed
    assert spec["evidence_gate"] == "Gate 2 dry assembly"
    assert spec["failure_rule"] == (
        "missing_consumable_cap_service_or_latch_state_blocks_dry_assembly_pass"
    )
    assert spec["cad_value"] == (
        "4 plates / 4 mats / 2 gaskets / 4 gas PCB / 2 unseated gas PCB / "
        "8 local sensors / 5 service leads / 2 unseated gas tubes / 1 cap / "
        "9 latches"
    )
    assert spec["stack_cad_value"] == "4 plates / 4 mats / 2 perimeter gaskets"
    assert spec["requires_physical_evidence"] is True
    assert "normal_ot2_operation" in spec["physical_claims_blocked"]
    assert spec["source_review_parts"] == [
        witness_name for _mode, witness_name in source_witnesses
    ]
    assert spec["plate_count"] == len(layout["missing_microplate_witnesses"])
    assert spec["septum_mat_count"] == len(layout["missing_septum_mat_witnesses"])
    assert spec["perimeter_gasket_count"] == len(
        layout["missing_perimeter_gasket_witnesses"]
    )
    assert spec["gas_pcb_cartridge_count"] == len(
        layout["missing_gas_pcb_cartridge_witnesses"]
    )
    assert spec["unseated_gas_pcb_cartridge_review_count"] == len(
        layout["unseated_gas_pcb_cartridges_review"]
    )
    assert spec["local_sensor_module_count"] == 8
    assert spec["local_sensor_witness_count"] == len(
        layout["missing_local_sensor_witnesses"]
    )
    assert spec["service_lead_witness_count"] == len(
        layout["missing_service_lead_witnesses"]
    )
    assert spec["unseated_side_gas_tube_review_count"] == len(
        layout["unseated_side_gas_tubes_review"]
    )
    assert spec["sample_relief_cap_witness_count"] == 1
    assert spec["latch_unseated_witness_count"] == len(layout["wedge_lock_rectangles"])
    for mode, witness_name in source_witnesses:
        state = build_row_coupon_service_parts(params, mode=mode)
        witness = state[witness_name].val()
        witness_bb = witness.BoundingBox()

        assert witness.Volume() > 0
        assert check_bb.xmin <= witness_bb.xmin
        assert check_bb.xmax >= witness_bb.xmax
        assert check_bb.ymin <= witness_bb.ymin
        assert check_bb.ymax >= witness_bb.ymax
        assert check_bb.zmin <= witness_bb.zmin
        assert check_bb.zmax >= witness_bb.zmax

    assert check.Volume() > max(
        build_row_coupon_service_parts(params, mode=mode)[witness_name].val().Volume()
        for mode, witness_name in source_witnesses
    )


def test_wet_dry_failure_paths_are_printed_into_support_frame() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    paths = layout["wet_dry_failure_paths"]
    apertures = layout["dry_bay_apertures"]
    thresholds = paths["dry_bay_aperture_thresholds"]
    gutters = paths["wet_dry_witness_gutters"]

    assert len(apertures) == params["row"]["plate_count"]
    assert len(thresholds) == len(apertures)
    assert len(gutters) == 2 * len(apertures)
    for threshold, aperture in zip(thresholds, apertures, strict=True):
        assert threshold["inner_x"] == aperture["x"]
        assert threshold["inner_y"] == aperture["y"]
        assert threshold["inner_length_x"] == aperture["length_x"]
        assert threshold["inner_width_y"] == aperture["width_y"]
        assert threshold["rail_width"] == production["dry_bay_threshold_width_xy"]
        assert threshold["height_z"] <= params["plate_support"]["land_height_z"]
        assert threshold["z"] == layout["base_top_z"]

    for gutter in gutters:
        assert gutter["depth_z"] == production["wet_dry_witness_gutter_depth_z"]
        assert gutter["z"] == round(layout["base_top_z"] - gutter["depth_z"], 3)
        for aperture in apertures:
            assert not _rectangles_overlap(
                gutter["x"],
                gutter["y"],
                gutter["length_x"],
                gutter["width_y"],
                aperture["x"],
                aperture["y"],
                aperture["length_x"],
                aperture["width_y"],
            )

    plain_params = deepcopy(params)
    plain_params["production_assembly"]["dry_bay_threshold_width_xy"] = 0.0
    plain_params["production_assembly"]["dry_bay_threshold_height_z"] = 0.0
    plain_params["production_assembly"]["wet_dry_witness_gutter_width_xy"] = 0.0
    plain_params["production_assembly"]["wet_dry_witness_gutter_depth_z"] = 0.0
    assert build_plate_support_frame(params).val().Volume() > (
        build_plate_support_frame(plain_params).val().Volume()
    )


def test_production_lid_split_and_printed_locks_are_explicit() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    shell_bb = build_lid_manifold_shell(params, assembly_position=True).val().BoundingBox()
    cover_bb = build_lid_cover(params, assembly_position=True).val().BoundingBox()
    caps_bb = build_printed_sample_relief_cap(
        params,
        assembly_position=True,
    ).val().BoundingBox()
    locks_bb = build_printed_wedge_locks(params, assembly_position=True).val().BoundingBox()
    tongue_d = params["production_assembly"]["lid_cover_tongue_depth_z"]
    upper_tab_dams = [
        witness["threshold_rect"]
        for witness in layout["gasket_tab_leak_witnesses"]
        if witness["layer"] == "upper"
    ]
    shell_bottom_z = min(float(dam["z"]) for dam in upper_tab_dams)

    assert round(shell_bb.zmin, 2) == round(shell_bottom_z, 2)
    assert round(shell_bb.zmin, 2) < round(layout["lid_bottom_z"], 2)
    assert round(shell_bb.zmax, 2) == round(layout["lid_top_z"], 2)
    assert round(cover_bb.zmin, 2) == round(layout["lid_top_z"] - tongue_d, 2)
    assert round(cover_bb.zmax, 2) == round(layout["assembly_top_z"], 2)
    assert round(caps_bb.zmax, 2) == round(layout["port_cap_top_z"], 2)
    assert round(caps_bb.zmax, 2) < round(layout["assembly_top_z"], 2)
    assert round(locks_bb.zmin, 2) == round(
        layout["lid_top_z"] + params["lid_manifold"]["duct_height_z"],
        2,
    )
    assert locks_bb.zmax <= cover_bb.zmax
    assert 0.0 <= round(locks_bb.xmin, 2)
    assert round(locks_bb.xmax, 2) <= round(layout["length_x"], 2)
    assert 0.0 <= round(locks_bb.ymin, 2)
    assert round(locks_bb.ymax, 2) <= round(layout["width_y"], 2)


def test_upper_and_lower_gaskets_are_separate_production_parts() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    lower_bb = build_lower_gasket(params, assembly_position=True).val().BoundingBox()
    upper_bb = build_upper_gasket(params, assembly_position=True).val().BoundingBox()
    lower_volume = build_lower_gasket(params, assembly_position=True).val().Volume()
    plain_params = deepcopy(params)
    plain_params["production_assembly"]["gasket_service_tab_length_x"] = 0.0
    plain_params["production_assembly"]["gasket_service_tab_depth_y"] = 0.0
    plain_volume = build_lower_gasket(plain_params, assembly_position=True).val().Volume()

    assert round(lower_bb.zmin, 2) == round(layout["base_top_z"], 2)
    assert round(lower_bb.zlen, 2) == params["seal_interface"]["compressed_gasket_height_z"]
    assert round(upper_bb.zmin, 2) == round(layout["gasket_bottom_z"], 2)
    assert round(upper_bb.zlen, 2) == params["seal_interface"]["compressed_gasket_height_z"]
    assert lower_volume > plain_volume


def test_gasket_service_tab_roots_have_margin_witnesses_not_dry_bay_paths() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    check = build_gasket_tab_leak_witness_check(params, assembly_position=True).val()
    dry = layout["dry_bay_envelope"]
    witnesses = layout["gasket_tab_leak_witnesses"]
    spec = layout["gasket_tab_leak_witness_check"]
    production = params["production_assembly"]

    assert "gasket_tab_leak_witness_check" not in installed
    assert "gasket_tab_leak_witness_check" in validation
    assert len(witnesses) == 4
    assert spec["evidence_gate"] == "Gate 4 wet/dry witness"
    assert spec["cad_value"] == "4 wet collectors / 4 inboard dams"
    assert spec["failure_rule"] == (
        "gasket_tab_root_leak_without_margin_witness_blocks_wet_dry_pass"
    )
    assert spec["requires_physical_evidence"] is True
    assert "dry_bay_protection_from_gasket_margin_leaks" in (
        spec["physical_claims_blocked"]
    )
    assert spec["wet_collector_count"] == len(witnesses)
    assert spec["inboard_dam_count"] == len(witnesses)
    assert len(spec["body_rects"]) == 2 * len(witnesses)
    assert len(check.Solids()) == 2 * len(witnesses)
    assert {(witness["layer"], witness["side"]) for witness in witnesses} == {
        ("lower", "front"),
        ("lower", "rear"),
        ("upper", "front"),
        ("upper", "rear"),
    }
    assert {witness["owner_part"] for witness in witnesses} == {
        "plate_support_frame",
        "lid_manifold_shell",
    }

    for witness in witnesses:
        tab = witness["tab_rect"]
        gutter = witness["gutter_rect"]
        dam = witness["threshold_rect"]
        assert witness["leak_management"] == "tab_root_margin_gutter_with_inboard_dam"
        assert witness["validation"] == "service_tab_root_witness_margin_not_leak_rate_proof"
        assert gutter["height_z"] == production["gasket_tab_witness_gutter_depth_z"]
        assert dam["height_z"] == production["gasket_tab_witness_dam_height_z"]
        assert gutter["length_x"] == dam["length_x"]
        assert gutter["x"] == dam["x"]
        assert tab["x"] >= gutter["x"]
        assert tab["x"] + tab["length_x"] <= gutter["x"] + gutter["length_x"]
        if witness["layer"] == "lower":
            assert witness["owner_part"] == "plate_support_frame"
            assert gutter["z"] == round(layout["base_top_z"] - gutter["height_z"], 3)
            assert dam["z"] == layout["base_top_z"]
        else:
            assert witness["owner_part"] == "lid_manifold_shell"
            assert gutter["z"] == round(layout["lid_bottom_z"] - gutter["height_z"], 3)
            assert dam["z"] == round(layout["lid_bottom_z"] - dam["height_z"], 3)
        if witness["side"] == "front":
            assert dam["y"] > gutter["y"] > tab["y"]
            assert dam["y"] + dam["width_y"] < dry["y"]
        else:
            assert dam["y"] < gutter["y"] < tab["y"]
            assert dam["y"] > dry["y"] + dry["width_y"]
        for rect in (tab, gutter, dam):
            assert not _rectangles_overlap(
                rect["x"],
                rect["y"],
                rect["length_x"],
                rect["width_y"],
                dry["x"],
                dry["y"],
                dry["length_x"],
                dry["width_y"],
            )
            for tile in layout["tile_origins"]:
                x, y, length, width = _septum_access_window_for_tile_for_test(tile, params)
                assert not _rectangles_overlap(
                    rect["x"],
                    rect["y"],
                    rect["length_x"],
                    rect["width_y"],
                    x,
                    y,
                    length,
                    width,
                )


def test_dry_bay_ingress_audit_collects_external_wet_sources() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    check = build_dry_bay_ingress_audit_check(params, assembly_position=True).val()
    dry = layout["dry_bay_envelope"]
    audit_rects = layout["dry_bay_ingress_audit_rects"]
    spec = layout["dry_bay_ingress_audit_check"]
    protected = [
        rect
        for rect in audit_rects
        if rect["audit_role"] == "protected_dry_bay_footprint"
    ]
    wet_collectors = [
        rect for rect in audit_rects if rect["audit_role"] == "wet_collection"
    ]
    inboard_dams = [rect for rect in audit_rects if rect["audit_role"] == "inboard_dam"]

    assert "dry_bay_ingress_audit_check" not in installed
    assert "dry_bay_ingress_audit_check" in validation
    assert spec["evidence_gate"] == "Gate 4 wet/dry witness"
    assert spec["cad_value"] == "10 wet collectors / 7 inboard dams / 1 protected footprint"
    assert spec["failure_rule"] == (
        "wet_source_bridge_or_unprotected_dry_bay_path_blocks_wet_dry_pass"
    )
    assert spec["requires_physical_evidence"] is True
    assert "wet_operation_without_dry_bay_ingress" in spec["physical_claims_blocked"]
    assert spec["body_rects"] == audit_rects
    assert check.Volume() > 0
    assert len(protected) == 1
    assert len(wet_collectors) == 10
    assert len(inboard_dams) == 7
    assert len(audit_rects) == 1 + len(wet_collectors) + len(inboard_dams)

    protected_rect = protected[0]
    assert protected_rect["x"] == dry["x"]
    assert protected_rect["y"] == dry["y"]
    assert protected_rect["z"] == dry["bottom_z"]
    assert protected_rect["length_x"] == dry["length_x"]
    assert protected_rect["width_y"] == dry["width_y"]
    assert protected_rect["height_z"] == round(dry["top_z"] - dry["bottom_z"], 3)
    assert protected_rect["dry_bay_relation"] == "protected_volume_not_wet_source"

    source_groups = {rect["source_group"] for rect in wet_collectors + inboard_dams}
    assert source_groups == {
        "side_gas_service",
        "sample_relief_cap",
        "gasket_tab_root",
    }
    assert {rect["source_group"] for rect in wet_collectors} == source_groups
    assert {rect["source_group"] for rect in inboard_dams} == source_groups

    for rect in wet_collectors:
        assert rect["dry_bay_relation"] == "outside_protected_footprint"
        assert not _rectangles_overlap(
            rect["x"],
            rect["y"],
            rect["length_x"],
            rect["width_y"],
            dry["x"],
            dry["y"],
            dry["length_x"],
            dry["width_y"],
        )

    for rect in inboard_dams:
        assert rect["dry_bay_relation"] == "barrier_at_protected_margin"
        assert rect["height_z"] > 0
        assert rect["length_x"] > 0
        assert rect["width_y"] > 0


def test_dry_bay_obstructed_is_opt_in_gate4_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    obstructed = build_row_coupon_service_parts(params, mode="dry_bay_obstructed")
    installed_names = set(installed)
    dry = layout["dry_bay_envelope"]
    rects = layout["dry_bay_obstruction_review"]
    review = obstructed["dry_bay_obstruction_review"].val()
    direct_review = build_dry_bay_obstruction_review(
        params,
        assembly_position=True,
    ).val()
    review_bb = review.BoundingBox()
    direct_bb = direct_review.BoundingBox()
    expected_xmin = min(float(rect["x"]) for rect in rects)
    expected_ymin = min(float(rect["y"]) for rect in rects)
    expected_zmin = min(float(rect["z"]) for rect in rects)
    expected_xmax = max(float(rect["x"]) + float(rect["length_x"]) for rect in rects)
    expected_ymax = max(float(rect["y"]) + float(rect["width_y"]) for rect in rects)
    expected_zmax = max(float(rect["z"]) + float(rect["height_z"]) for rect in rects)

    assert "dry_bay_obstructed" in ROW_COUPON_SERVICE_MODES
    assert "dry_bay_obstruction_review" not in installed
    assert "dry_bay_obstruction_review" not in validation
    assert installed_names.issubset(obstructed)
    assert set(obstructed) - installed_names == {"dry_bay_obstruction_review"}
    assert len(rects) == 3
    assert len(review.Solids()) == len(rects)
    assert round(review_bb.xmin, 2) == round(direct_bb.xmin, 2)
    assert round(review_bb.ymin, 2) == round(direct_bb.ymin, 2)
    assert round(review_bb.zmin, 2) == round(direct_bb.zmin, 2)
    assert round(review_bb.xmax, 2) == round(direct_bb.xmax, 2)
    assert round(review_bb.ymax, 2) == round(direct_bb.ymax, 2)
    assert round(review_bb.zmax, 2) == round(direct_bb.zmax, 2)
    assert round(review_bb.xmin, 2) == round(expected_xmin, 2)
    assert round(review_bb.ymin, 2) == round(expected_ymin, 2)
    assert round(review_bb.zmin, 2) == round(expected_zmin, 2)
    assert round(review_bb.xmax, 2) == round(expected_xmax, 2)
    assert round(review_bb.ymax, 2) == round(expected_ymax, 2)
    assert round(review_bb.zmax, 2) == round(expected_zmax, 2)

    blocked_states = {rect["blocked_fail_closed_state"] for rect in rects}
    assert blocked_states == {"dry_bay_blocked", "wet_witness_path_hidden"}
    assert {rect["review_state"] for rect in rects} == {"dry_bay_obstructed"}
    assert {rect["owner_part"] for rect in rects} == {"dry_bay_obstruction_review"}
    assert {rect["retained_part"] for rect in rects} == {"dry_bay_envelope"}
    for rect in rects:
        assert rect["x"] >= dry["x"]
        assert rect["y"] >= dry["y"]
        assert rect["z"] >= dry["bottom_z"]
        assert rect["x"] + rect["length_x"] <= dry["x"] + dry["length_x"]
        assert rect["y"] + rect["width_y"] <= dry["y"] + dry["width_y"]
        assert rect["z"] + rect["height_z"] <= dry["top_z"]
        assert {
            "dry_bay_ingress_audit_check",
            "wet_dry_failure_path_check",
            "dry_bay_envelope_check",
        } == set(rect["source_validation_checks"])


def test_assembly_debris_present_is_opt_in_gate2_review_mode() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    reviewed = build_row_coupon_service_parts(params, mode="assembly_debris_present")
    installed_names = set(installed)
    rects = layout["assembly_debris_review"]
    dry = layout["dry_bay_envelope"]
    review = reviewed["assembly_debris_review"].val()
    direct_review = build_assembly_debris_review(
        params,
        assembly_position=True,
    ).val()
    dry_checkpoint = next(
        checkpoint
        for checkpoint in layout["fail_closed_prerun_inspection_check"]["checkpoints"]
        if checkpoint["name"] == "dry_bay_clear_and_witness_paths_visible"
    )
    threshold_count = len(layout["wet_dry_failure_paths"]["dry_bay_aperture_thresholds"])

    assert "assembly_debris_present" in ROW_COUPON_SERVICE_MODES
    assert "assembly_debris_review" not in installed
    assert "assembly_debris_review" not in validation
    assert installed_names.issubset(reviewed)
    assert set(reviewed) - installed_names == {"assembly_debris_review"}
    assert len(rects) == threshold_count + 1
    assert len(review.Solids()) == len(rects)
    assert round(review.BoundingBox().zmax, 2) == round(
        direct_review.BoundingBox().zmax,
        2,
    )

    assert {rect["review_state"] for rect in rects} == {"assembly_debris_present"}
    assert {rect["owner_part"] for rect in rects} == {"assembly_debris_review"}
    assert {rect["blocked_fail_closed_state"] for rect in rects} == {
        "assembly_debris_present"
    }
    assert {
        "loose_debris_inside_protected_dry_bay",
        "support_debris_bridge_on_dry_bay_threshold",
    } == {rect["review_kind"] for rect in rects}
    assert {
        "printability_support_cleanup_check",
        "assembly_state_witness_check",
        "dry_bay_ingress_audit_check",
        "wet_dry_failure_path_check",
    } == set(rects[0]["source_validation_checks"])
    assert "assembly_debris_present" in dry_checkpoint["blocks"]

    for rect in rects:
        assert rect["x"] >= dry["x"]
        assert rect["y"] >= dry["y"]
        assert rect["z"] >= dry["bottom_z"]
        assert rect["x"] + rect["length_x"] <= dry["x"] + dry["length_x"]
        assert rect["y"] + rect["width_y"] <= dry["y"] + dry["width_y"]
        assert rect["z"] + rect["height_z"] <= dry["top_z"]


def test_capture_grooves_and_lid_tongue_change_the_owning_parts() -> None:
    params = load_params(PARAMS)
    plain_params = deepcopy(params)
    plain_params["production_assembly"]["gasket_capture_depth_z"] = 0.0
    plain_params["production_assembly"]["condensation_pocket_depth_z"] = 0.0
    plain_params["production_assembly"]["lid_cover_tongue_depth_z"] = 0.0
    plain_params["production_assembly"]["wedge_receiver_rail_height_z"] = 0.0

    assert build_plate_support_frame(params).val().Volume() < (
        build_plate_support_frame(plain_params).val().Volume()
    )
    assert build_wet_chamber_frame(params).val().Volume() < (
        build_wet_chamber_frame(plain_params).val().Volume()
    )
    assert build_lid_manifold_shell(params).val().Volume() < (
        build_lid_manifold_shell(plain_params).val().Volume()
    )
    assert build_lid_cover(params).val().Volume() > (
        build_lid_cover(plain_params).val().Volume()
    )


def test_observer_front_end_swept_body_reaches_all_wells_without_hitting_feet() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    swept = layout["observer_front_end_swept_body_check"]
    carriage = layout["observer_carriage_envelope_check"]
    raceway = layout["observer_service_raceway_envelope_check"]
    swept_bb = build_observer_front_end_swept_body_check(
        params,
        assembly_position=True,
    ).val().BoundingBox()

    assert "observer_front_end_swept_body_check" not in installed
    assert "observer_front_end_swept_body_check" in validation
    assert "observer_carriage_envelope_check" not in installed
    assert "observer_carriage_envelope_check" in validation
    assert "observer_service_raceway_envelope_check" not in installed
    assert "observer_service_raceway_envelope_check" in validation
    assert swept["evidence_gate"] == "Gate 6 sensor/thermal"
    assert (
        swept["validation"]
        == "required_gate6_observer_front_end_swept_body_evidence"
    )
    assert swept["cad_value"] == "120.00 x 347.50 x 40.00 mm"
    assert swept["requires_physical_evidence"] is True
    assert "observer_front_end_clearance" in swept["physical_claims_blocked"]
    assert swept["body_rects"][0]["length_x"] == swept["length_x"]
    # Falsifiable closure asserts (the well-containment asserts above are
    # tautological by construction; these are not). The optical-head footprint
    # must fit the objective keepout circle, and head body + focus stroke +
    # plate standoff must fit the carriage vertical envelope.
    observer_robotics = params["observer_robotics"]
    expected_footprint_d = round(
        (
            observer_robotics["front_end_length_x"] ** 2
            + observer_robotics["front_end_width_y"] ** 2
        )
        ** 0.5,
        3,
    )
    assert (
        swept["front_end_footprint_circumscribed_diameter_mm"] == expected_footprint_d
    )
    assert swept["objective_keepout_diameter_mm"] == (
        params["dry_bay"]["objective_keepout_diameter"]
    )
    assert swept["front_end_fits_objective_keepout"] is True
    assert swept["front_end_footprint_circumscribed_diameter_mm"] <= (
        swept["objective_keepout_diameter_mm"]
    )
    assert swept["vertical_budget_required_mm"] == round(
        observer_robotics["front_end_top_clearance_z"]
        + observer_robotics["front_end_height_z"]
        + observer_robotics["front_end_focus_stroke_z"]
        + observer_robotics.get("front_end_service_margin_z", 0.0),
        3,
    )
    assert swept["carriage_height_budget_mm"] == observer_robotics["carriage_height_z"]
    assert swept["front_end_vertical_budget_closes"] is True
    assert swept["vertical_budget_required_mm"] <= swept["carriage_height_budget_mm"]
    # The swept body's own dry-bay containment is now gated on the check (not only
    # by the layout test below): the placeholder body fits with zero overflow.
    assert swept["front_end_body_fits_dry_bay"] is True
    assert swept["front_end_body_overflow_mm"] == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert carriage["evidence_gate"] == "Gate 6 sensor/thermal"
    assert (
        carriage["validation"]
        == "required_gate6_observer_carriage_envelope_evidence"
    )
    assert carriage["cad_value"] == "100.00 x 58.00 x 62.00 mm"
    assert carriage["requires_physical_evidence"] is True
    assert "observer_carriage_clearance" in carriage["physical_claims_blocked"]
    assert carriage["body_rects"][0]["height_z"] == carriage["height_z"]
    assert raceway["evidence_gate"] == "Gate 6 sensor/thermal"
    assert (
        raceway["validation"]
        == "required_gate6_observer_service_raceway_evidence"
    )
    assert raceway["cad_value"] == "8.00 x 357.50 x 24.00 mm"  # bay-Y resized to clear wet gutters
    assert raceway["requires_physical_evidence"] is True
    assert "observer_service_loop_recovery" in raceway["physical_claims_blocked"]
    assert raceway["body_rects"][0]["width_y"] == raceway["width_y"]
    assert round(swept_bb.xlen, 2) == round(swept["length_x"], 2)
    assert round(swept_bb.ylen, 2) == round(swept["width_y"], 2)
    for tile in layout["tile_origins"]:
        for x, y in [
            (
                tile["x"] + params["well_grid"]["first_well_center_x"],
                tile["y"] + params["well_grid"]["first_well_center_y"],
            ),
            (
                tile["x"]
                + params["well_grid"]["first_well_center_x"]
                + (params["well_grid"]["columns"] - 1) * params["well_grid"]["pitch_x"],
                tile["y"]
                + params["well_grid"]["first_well_center_y"]
                + (params["well_grid"]["rows"] - 1) * params["well_grid"]["pitch_y"],
            ),
        ]:
            assert swept["x"] < x < swept["x"] + swept["length_x"]
            assert swept["y"] < y < swept["y"] + swept["width_y"]

    for foot in layout["deck_engagement_feet"]:
        assert not _rectangles_overlap(
            float(foot["x"]),
            float(foot["y"]),
            float(foot["length_x"]),
            float(foot["width_y"]),
            swept["x"],
            swept["y"],
            swept["length_x"],
            swept["width_y"],
        )


def test_observer_infinity_port_datum_check_is_frozen_and_falsifiable_sm_2_1() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    swept = layout["observer_front_end_swept_body_check"]
    port = layout["observer_infinity_port_datum_check"]
    port_bb = build_observer_infinity_port_datum_check(
        params,
        assembly_position=True,
    ).val().BoundingBox()

    assert "observer_infinity_port_datum_check" not in installed
    assert "observer_infinity_port_datum_check" in validation
    assert port["evidence_gate"] == "Gate 6 sensor/thermal"
    assert port["validation"] == "required_gate6_observer_infinity_port_datum_evidence"
    assert port["cad_value"] == "120.00 x 347.50 x 0.50 mm"
    assert port["requires_physical_evidence"] is True
    assert "SMIS_level1_backend_swap" in port["physical_claims_blocked"]
    assert port["pd0_offset_from_objective_shoulder_z_mm"] == 28.0
    assert port["pd0_z_mm"] == -36.0
    assert swept["z"] <= port["pd0_z_mm"] <= swept["z"] + swept["height_z"]
    assert port["pd0_within_front_end_z"] is True
    assert port["clear_aperture_diameter_mm"] == 20.0
    assert port["objective_keepout_diameter_mm"] == 32.0
    assert port["clear_aperture_fits_keepout"] is True
    assert port["cage_standard_mm"] == 30.0
    assert port["clear_aperture_fits_cage_standard"] is True
    assert port["rms_thread_present"] is True
    assert port["c_mount_present"] is True
    assert port["optical_standard_complete"] is True
    assert port["tube_lens_to_sensor_mm"] == 50.0
    assert port["tube_lens_to_sensor_spacing_frozen"] is True
    assert port["infinity_port_geometry_clears"] is True
    assert port["infinity_port_geometry_blockers"] == []
    assert round(port_bb.xlen, 2) == round(port["length_x"], 2)
    assert round(port_bb.ylen, 2) == round(port["width_y"], 2)
    assert round(port_bb.zlen, 2) == round(port["height_z"], 2)

    wide_aperture = deepcopy(params)
    wide_aperture["observer_robotics"]["infinity_port_clear_aperture_diameter"] = 40.0
    failed = row_coupon_layout(wide_aperture)["observer_infinity_port_datum_check"]
    assert failed["clear_aperture_fits_keepout"] is False
    assert failed["clear_aperture_fits_cage_standard"] is False
    assert failed["infinity_port_geometry_clears"] is False
    assert failed["infinity_port_geometry_blockers"] == [
        "infinity_port_aperture_exceeds_cage_standard",
        "infinity_port_aperture_exceeds_objective_keepout",
    ]

    missing_standard = deepcopy(params)
    missing_standard["observer_robotics"]["infinity_port_c_mount_present"] = False
    missing_standard["observer_robotics"]["infinity_port_tube_lens_to_sensor_mm"] = 55.0
    failed_standard = row_coupon_layout(missing_standard)[
        "observer_infinity_port_datum_check"
    ]
    assert failed_standard["optical_standard_complete"] is False
    assert failed_standard["tube_lens_to_sensor_spacing_frozen"] is False
    assert failed_standard["infinity_port_geometry_blockers"] == [
        "infinity_port_missing_rms_or_c_mount",
        "tube_lens_to_sensor_spacing_drift",
    ]


def test_observer_carriage_traverse_thin_truck_fits_dry_bay() -> None:
    # Stage-3 resolution: the 44.6 mm overflow the earlier model flagged was an
    # artifact of sweeping the 58 mm carriage BODY along the row. The thing that
    # physically traverses continuously is a thin gantry truck
    # (`gantry_truck_traverse_extent`, ~13 mm); the 58 mm box is parked at the row
    # end. Sweeping the truck makes the topology fit -- with a razor-thin margin.
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    carriage = layout["observer_carriage_envelope_check"]
    kinematic = layout["observer_kinematic_split_check"]
    swept = layout["observer_front_end_swept_body_check"]
    dry_bay = layout["dry_bay_envelope"]
    observer_robotics = params["observer_robotics"]
    traverse = carriage["carriage_traverse"]

    # The truck traverses the long row axis (Y for this four-plate column).
    assert traverse["traverse_axis"] == params["row"]["axis"]
    assert traverse["traverse_axis"] == "y"
    assert traverse["traverse_structure"] == "thin_gantry_truck"

    # Traverse-axis (Y) extent now grows by the THIN truck, not the 58 mm body.
    truck = observer_robotics["gantry_truck_traverse_extent"]
    well_y_span = round(swept["width_y"] - observer_robotics["front_end_width_y"], 3)
    well_x_span = round(swept["length_x"] - observer_robotics["front_end_length_x"], 3)
    assert traverse["gantry_truck_traverse_extent_mm"] == truck
    assert traverse["width_y"] == round(
        well_y_span + max(truck, observer_robotics["front_end_width_y"]),
        3,
    )
    # Sweeping the truck (13) instead of the carriage body (58) is the fix.
    assert traverse["width_y"] < round(
        well_y_span + observer_robotics["carriage_width_y"], 3
    )
    # Scan-axis (X) extent stays head-inclusive (head reaches outer columns).
    assert traverse["scan_axis_extent_is_head_inclusive"] is True
    assert traverse["length_x"] == round(
        well_x_span + observer_robotics["front_end_length_x"], 3
    )

    # Both axes fit the dry bay -- but only with the PLACEHOLDER bare-objective
    # head footprint. Both margins are razor-thin and surfaced as data; the
    # relationship asserts pin them without a brittle upper bound (a benign relief
    # -- a measured head smaller than the placeholder -- must not false-FAIL).
    assert traverse["dry_bay_overflow_x_mm"] == 0.0
    assert traverse["dry_bay_overflow_y_mm"] == 0.0
    assert traverse["fits_dry_bay"] is True
    assert carriage["traverse_fits_dry_bay"] is True
    # OC-A5: the traverse sweeps the MOVING HEAD's Z (the 40 mm front-end swept body),
    # not the static 62 mm carriage box -- the head, not the parked carrier, rides the row.
    assert traverse["z"] == swept["z"]
    assert traverse["height_z"] == swept["height_z"]
    assert traverse["z"] != carriage["z"]  # not the carriage box's -70
    assert traverse["height_z"] == 40.0 and carriage["height_z"] == 62.0
    assert traverse["z_within_dry_bay"] is True
    assert traverse["traverse_axis_fit_margin_mm"] == round(
        dry_bay["width_y"] - traverse["width_y"], 3
    )
    assert traverse["traverse_axis_fit_margin_mm"] > 0.0

    # Scan axis (X): this is where the Y fix RELOCATED its burden. The margin is
    # ~0.2 mm and the footprint EXCLUDES the post-fold camera arm -- both surfaced
    # so the X packing problem is honest, not hidden.
    assert traverse["scan_axis_fit_margin_mm"] == round(
        dry_bay["length_x"] - traverse["length_x"], 3
    )
    assert traverse["scan_axis_fit_margin_mm"] > 0.0
    assert traverse["scan_axis_footprint_excludes_camera_arm"] is True
    assert traverse["scan_axis_footprint_mm"] == (
        observer_robotics["front_end_scan_axis_footprint"]
    )

    # No feet / adjacent-slot intrusion with the thin truck.
    assert traverse["deck_foot_collision_count"] == 0
    assert traverse["adjacent_slot_collision_count"] == 0
    assert traverse["clears_traverse"] is True

    # FALSIFIABILITY: the fit is dimension-sensitive, NOT true by construction.
    # Re-sweeping the old 58 mm carriage body re-creates the Y overflow + blocker.
    fat = row_coupon_module._observer_carriage_traverse(
        row_axis="y",
        well_xs=[0.0, well_x_span],
        well_ys=[0.0, well_y_span],
        gantry_truck_traverse_extent=observer_robotics["carriage_width_y"],  # 58
        front_end_length_x=observer_robotics["front_end_length_x"],
        front_end_width_y=observer_robotics["front_end_width_y"],
        front_end_scan_axis_footprint=observer_robotics[
            "front_end_scan_axis_footprint"
        ],
        swept_z=-48.0,
        swept_height_z=40.0,
        dry_bay_envelope=dry_bay,
        deck_feet=[],
        adjacent_keepouts=[],
    )
    assert fat["dry_bay_overflow_y_mm"] > 0.0
    assert fat["fits_dry_bay"] is False

    # FALSIFIABILITY (scan axis): a real camera arm on the scan axis re-overflows
    # X -- the relocated burden is gated, not assumed away.
    armed = row_coupon_module._observer_carriage_traverse(
        row_axis="y",
        well_xs=[0.0, well_x_span],
        well_ys=[0.0, well_y_span],
        gantry_truck_traverse_extent=observer_robotics["gantry_truck_traverse_extent"],
        front_end_length_x=observer_robotics["front_end_length_x"],
        front_end_width_y=observer_robotics["front_end_width_y"],
        front_end_scan_axis_footprint=50.0,  # objective + a real folded arm
        swept_z=-48.0,
        swept_height_z=40.0,
        dry_bay_envelope=dry_bay,
        deck_feet=[],
        adjacent_keepouts=[],
    )
    assert armed["dry_bay_overflow_x_mm"] > 0.0
    assert armed["fits_dry_bay"] is False

    # Gate 6 stays blocked on the remaining physical-evidence checkpoints; only
    # the geometry overflow blocker is cleared. (Geometry fits; motion unproven.)
    assert kinematic["carriage_traverse_fits_dry_bay"] is True
    assert kinematic["carriage_traverse_clears"] is True
    assert "carriage_traverse_exceeds_dry_bay" not in kinematic["blockers"]
    assert kinematic["carriage_traverse_overflow_mm"] == {"x": 0.0, "y": 0.0}
    assert kinematic["blockers"]  # still non-empty: physical evidence required
    assert kinematic["requires_physical_evidence"] is True
    assert "observer_carriage_traverse_clearance" in carriage["physical_claims_blocked"]


def test_observer_carriage_traverse_x_axis_branch_is_symmetric() -> None:
    # The row_axis == "x" branch is not exercised by the (axis="y") params file,
    # so unit-test it directly for symmetry: the thin TRUCK sweeps the X traverse
    # axis (inflated by gantry_truck_traverse_extent) while the HEAD scans Y
    # (inflated by front_end_width_y). A deliberately fat 40 mm truck makes X
    # overflow while Y fits -- proving the truck, not the head, drives the
    # traverse axis, the mirror image of the live axis="y" case.
    traverse = row_coupon_module._observer_carriage_traverse(
        row_axis="x",
        well_xs=[0.0, 100.0],
        well_ys=[0.0, 50.0],
        gantry_truck_traverse_extent=40.0,
        front_end_length_x=21.0,
        front_end_width_y=13.0,
        front_end_scan_axis_footprint=13.0,
        swept_z=-48.0,
        swept_height_z=40.0,
        dry_bay_envelope={"length_x": 120.0, "width_y": 347.9, "bottom_z": -80.0, "top_z": 0.0},
        deck_feet=[],
        adjacent_keepouts=[],
    )
    assert traverse["traverse_axis"] == "x"
    assert traverse["traverse_structure"] == "thin_gantry_truck"
    assert traverse["gantry_truck_traverse_extent_mm"] == 40.0
    # X (traverse): well-X span 100 + max(truck 40, front_end 21) = 140.
    assert traverse["length_x"] == 140.0
    # Y (scan, head scan-axis footprint): well-Y span 50 + scan footprint 13 = 63.
    assert traverse["width_y"] == 63.0
    assert traverse["scan_axis_footprint_mm"] == 13.0
    # X overflows the 120 mm bay by 20; Y fits inside 347.9.
    assert traverse["dry_bay_overflow_x_mm"] == 20.0
    assert traverse["dry_bay_overflow_y_mm"] == 0.0
    assert traverse["fits_dry_bay"] is False
    assert traverse["clears_traverse"] is False


def test_observer_carriage_traverse_head_wider_than_truck_dominates() -> None:
    # Lock the max(truck, head) traverse-axis semantics: when the head is WIDER
    # than the thin rail on the traverse axis, the head (not the rail) sets the
    # swept extent. With the live params truck and front_end_width_y tie at 13, so
    # the x-branch never exercises the head-dominates direction -- pin it here.
    traverse = row_coupon_module._observer_carriage_traverse(
        row_axis="y",
        well_xs=[0.0, 80.0],
        well_ys=[0.0, 300.0],
        gantry_truck_traverse_extent=13.0,
        front_end_length_x=21.0,
        front_end_width_y=20.0,  # head wider than the 13 mm rail
        front_end_scan_axis_footprint=21.0,
        swept_z=-48.0,
        swept_height_z=40.0,
        dry_bay_envelope={"length_x": 120.0, "width_y": 347.9, "bottom_z": -80.0, "top_z": 0.0},
        deck_feet=[],
        adjacent_keepouts=[],
    )
    # Traverse Y extent = well-Y span 300 + max(truck 13, head 20) = 320, not 313.
    assert traverse["width_y"] == 320.0
    assert traverse["gantry_truck_traverse_extent_mm"] == 13.0


def test_observer_cad_hardening_live_layout_clears_all_asserts() -> None:
    # OC-A3/A6/A7/A9/A11/A12 happy path: with the live params every hardened
    # observer-CAD assert clears.
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    swept = layout["observer_front_end_swept_body_check"]
    carriage = layout["observer_carriage_envelope_check"]
    raceway = layout["observer_service_raceway_envelope_check"]
    fiducial = layout["observer_fiducial_focus_target_check"]
    optical = layout["observer_optical_stability_check"]

    # OC-A9: the round objective BARREL (an explicit measured param) is the
    # authoritative keepout gate, split from the conservative head bbox circumscribed Ø.
    assert swept["front_end_barrel_diameter_mm"] == 25.0
    assert swept["front_end_barrel_fits_keepout"] is True
    assert swept["front_end_barrel_diameter_mm"] <= swept["objective_keepout_diameter_mm"]

    # OC-A7: the service margin is an explicit param (was a silent .get default).
    assert params["observer_robotics"]["front_end_service_margin_z"] == 0.0
    assert swept["front_end_vertical_budget_closes"] is True

    # OC-A3: the raceway clears the optical sweep, fits the bay depth, and reserves the
    # R10 cable-loop height (24 mm reserved vs 2*R=20 mm loop -> 4 mm margin).
    assert raceway["raceway_clears_dry_bay_sweep"] is True
    assert raceway["raceway_z_within_bay_depth"] is True
    assert raceway["r10_loop_height_margin_mm"] == 4.0
    assert raceway["raceway_geometry_clears"] is True

    # OC-A6: the fiducial pattern multiplicity (4 disks + 4 marks per aperture) and
    # within-bay containment are gated, not just counted.
    assert fiducial["fiducial_multiplicity_ok"] is True
    assert fiducial["all_targets_within_dry_bay"] is True
    assert fiducial["fiducial_geometry_clears"] is True

    # OC-A12 + OC-A15: after the bay-Y was resized to its wet/dry-bounded wall, the
    # TRAVERSE axis is comfortable (10 mm) and no longer razor-thin. The binding
    # constraint is the SCAN axis, where the standoff-leg corridor and the milled
    # dry-bay wall are nearly co-located: the bay hi-wall (0.02 mm) is actually ~0.1 mm
    # TIGHTER than the leg corridor (0.12 mm). The model surfaces both and the binding
    # minimum, and the razor-thin flag tracks the binding wall (0.02), not just the corridor.
    traverse = carriage["carriage_traverse"]
    assert traverse["traverse_margin_is_razor_thin"] is False  # wet/dry-bounded wall, 10 mm
    assert traverse["traverse_axis_fit_margin_mm"] == 10.0
    assert traverse["scan_corridor_width_mm"] == 120.4
    assert traverse["scan_corridor_margin_mm"] == 0.12  # leg wall
    assert traverse["scan_bay_per_wall_margin_mm"] == 0.02  # bay hi-wall, the tightest
    assert traverse["scan_binding_margin_mm"] == 0.02  # min of the two = the true wall
    assert traverse["scan_binding_margin_mm"] <= traverse["scan_corridor_margin_mm"]
    assert traverse["scan_margin_is_razor_thin"] is True  # vs the binding wall

    # OC-A11: geometry clears -> no geometry blocker on the optical-stability check.
    # (Reads carriage_traverse["clears_traverse"], which ANDs in deck-foot / adjacent-
    # slot collisions, NOT the bay-envelope-only fits_dry_bay.)
    assert optical["observer_geometry_clears"] is True
    assert "geometry_overflow_blocks_optical_stability" not in optical["blockers"]

    # OC-A15 (KNOWN, surfaced-not-gated): the hardening EXPOSED a real placeholder
    # inconsistency that needs Stage-0 measurement / a design decision (see decision_log.md).
    # Pinned False here so it stays visible and cannot silently flip:
    #   A15 -- a Ø25 objective barrel cannot fit the 13 mm head footprint the razor-thin
    #          traverse margin assumes (plate-level sweep should use the barrel Ø).
    assert swept["front_end_barrel_within_head_footprint"] is False
    # OC-A14 resolved: end_margin_x is 10.5 mm, enough for the raceway to remain outside
    # the boundary-rail lane after the coupon-length clamp.
    assert raceway["raceway_clears_boundary_rail"] is True
    # OC-A15: the CAD now surfaces the SAME barrel-vs-corridor verdict the SMIS dock gate
    # enforces, on the shared 21.2 mm constant -- so CAD and SMIS cannot silently disagree
    # about a real Ø25 head (both report it does NOT thread the corridor).
    assert swept["scan_corridor_footprint_max_mm"] == 21.2
    assert swept["barrel_threads_scan_corridor"] is False
    # All surfaced diagnostics, NOT in the hard fit chain, so the layout's geometry
    # verdict is unchanged until the design decision lands.


def test_observer_scan_corridor_strike_is_falsifiable_oc_a15() -> None:
    # The corridor STRIKE (negative-margin) path was unasserted -- drive a wide scan
    # footprint through the live layout and confirm the corridor margin goes negative,
    # the legs are struck, and clears_traverse goes False. A sign/branch inversion in the
    # left/right split or the max/min selection would otherwise ship green.
    params = load_params(PARAMS)
    over = deepcopy(params)
    over["observer_robotics"]["front_end_scan_axis_footprint"] = 26.0  # > corridor
    over["observer_robotics"]["front_end_length_x"] = 26.0
    traverse = row_coupon_layout(over)["observer_carriage_envelope_check"]["carriage_traverse"]
    assert traverse["scan_corridor_margin_mm"] < 0.0
    assert traverse["scan_binding_margin_mm"] < 0.0
    assert traverse["deck_foot_collision_count"] > 0
    assert traverse["clears_traverse"] is False


def test_observer_raceway_geometry_falsifiable_oc_a3() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    db = layout["dry_bay_envelope"]
    raw = layout["observer_service_raceway_envelope_check"]
    base = {k: raw[k] for k in ("x", "y", "z", "length_x", "width_y", "height_z")}

    # Intruding the optical sweep: move the raceway inside the dry-bay X -> blocker.
    intruding_rect = {**base, "x": float(db["x"]) + 1.0}
    intruding = row_coupon_module._observer_service_raceway_envelope_check(
        intruding_rect, dry_bay_envelope=db, service_bend_radius=10.0
    )
    assert intruding["raceway_clears_dry_bay_sweep"] is False
    assert "raceway_intrudes_optical_sweep" in intruding["raceway_geometry_blockers"]

    # A fat bend radius (R20 -> 40 mm loop) exceeds the 24 mm raceway Z -> blocker.
    tight = row_coupon_module._observer_service_raceway_envelope_check(
        base, dry_bay_envelope=db, service_bend_radius=20.0
    )
    assert tight["r10_loop_fits_raceway_z"] is False
    assert "cable_loop_exceeds_raceway_z" in tight["raceway_geometry_blockers"]

    # A raceway that drops below the bay floor exceeds the bay depth -> blocker (the
    # z_within_bay_depth False path, otherwise untested).
    deep = {**base, "z": float(db["bottom_z"]) - 10.0}
    sunk = row_coupon_module._observer_service_raceway_envelope_check(
        deep, dry_bay_envelope=db, service_bend_radius=10.0
    )
    assert sunk["raceway_z_within_bay_depth"] is False
    assert "raceway_exceeds_bay_depth" in sunk["raceway_geometry_blockers"]


def test_observer_fiducial_geometry_falsifiable_oc_a6() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    db = layout["dry_bay_envelope"]
    targets = layout["observer_fiducial_focus_target_check"]["body_targets"]

    # Drop one fiducial disk -> per-aperture multiplicity breaks.
    dropped = False
    missing_one = []
    for t in targets:
        if not dropped and t["target_kind"] == "observer_fiducial_disk":
            dropped = True
            continue
        missing_one.append(t)
    check = row_coupon_module._observer_fiducial_focus_target_check(
        missing_one, aperture_count=4, dry_bay_envelope=db
    )
    assert check["fiducial_multiplicity_ok"] is False
    assert "fiducial_pattern_multiplicity_mismatch" in check["fiducial_geometry_blockers"]

    # Shove one target outside the bay -> containment fails.
    outside = [dict(t) for t in targets]
    outside[0] = {**outside[0], "x": float(db["x"]) - 50.0}
    check2 = row_coupon_module._observer_fiducial_focus_target_check(
        outside, aperture_count=4, dry_bay_envelope=db
    )
    assert check2["all_targets_within_dry_bay"] is False
    assert "fiducial_target_outside_dry_bay" in check2["fiducial_geometry_blockers"]

    # A DISK target whose RADIUS overhangs the bay edge fails -- containment is
    # radius-aware, not point-only (move a keepout disk center to within < r of the edge).
    disk_idx = next(
        i for i, t in enumerate(targets) if "diameter" in t and t["diameter"] >= 30
    )
    radius_overhang = [dict(t) for t in targets]
    rt = radius_overhang[disk_idx]
    radius_overhang[disk_idx] = {**rt, "x": float(db["x"]) + float(rt["diameter"]) / 2.0 - 1.0}
    check3 = row_coupon_module._observer_fiducial_focus_target_check(
        radius_overhang, aperture_count=4, dry_bay_envelope=db
    )
    assert check3["all_targets_within_dry_bay"] is False

    # A target whose Z falls outside the bay depth fails -- containment gates Z too.
    bad_z = [dict(t) for t in targets]
    bad_z[0] = {**bad_z[0], "z": float(db["bottom_z"]) - 100.0}
    check4 = row_coupon_module._observer_fiducial_focus_target_check(
        bad_z, aperture_count=4, dry_bay_envelope=db
    )
    assert check4["all_targets_within_dry_bay"] is False


def test_observer_barrel_and_optical_geometry_propagation_falsifiable_oc_a9_a11() -> None:
    params = load_params(PARAMS)

    # OC-A9: an oversized barrel fails the keepout gate independently of the bbox.
    over_barrel = deepcopy(params)
    over_barrel["observer_robotics"]["front_end_barrel_diameter"] = 40.0  # > Ø32
    swept = row_coupon_layout(over_barrel)["observer_front_end_swept_body_check"]
    assert swept["front_end_barrel_fits_keepout"] is False

    # OC-A11: a geometry overflow (oversized front-end body) must propagate a hard
    # blocker into the optical-stability check -- it can no longer read as "only
    # physical evidence pending".
    over_body = deepcopy(params)
    over_body["observer_robotics"]["front_end_length_x"] = 160.0  # body overflows the bay
    over_layout = row_coupon_layout(over_body)
    optical = over_layout["observer_optical_stability_check"]
    assert optical["observer_geometry_clears"] is False
    assert "geometry_overflow_blocks_optical_stability" in optical["blockers"]


def test_observer_razor_thin_margin_flag_is_falsifiable_oc_a12() -> None:
    # A comfortable margin must NOT be flagged razor-thin (proves the flag is real, not
    # a constant True): a roomy bay leaves >0.5 mm on both axes.
    roomy = row_coupon_module._observer_carriage_traverse(
        row_axis="y",
        well_xs=[0.0, 80.0],
        well_ys=[0.0, 300.0],
        gantry_truck_traverse_extent=13.0,
        front_end_length_x=21.0,
        front_end_width_y=13.0,
        front_end_scan_axis_footprint=21.0,
        swept_z=-48.0,
        swept_height_z=40.0,
        dry_bay_envelope={"length_x": 200.0, "width_y": 400.0, "bottom_z": -80.0, "top_z": 0.0},
        deck_feet=[],
        adjacent_keepouts=[],
    )
    assert roomy["traverse_margin_is_razor_thin"] is False
    assert roomy["scan_margin_is_razor_thin"] is False


def test_observer_oversized_body_overflows_both_checks_no_decoupling() -> None:
    # OC-A1/OC-A2 guard: an oversized front-end BODY must not overflow the dry bay
    # while the traverse silently reports "fits". Bumping front_end_length_x past
    # the bay (scan footprint left at the placeholder) drives BOTH the swept-body
    # containment check and the traverse scan-axis fit to False -- the two params
    # are no longer decoupled.
    params = load_params(PARAMS)

    def layout_with(**overrides):
        cfg = deepcopy(params)
        cfg["observer_robotics"].update(overrides)
        return row_coupon_layout(cfg)

    # X case: oversized body length. The swept body overflows dry-bay X by exactly
    # 38.8 mm (two-sided), the check reports it (OC-A1), and the traverse scan span
    # is tied to the body length (max with the scan footprint) so it overflows too
    # (OC-A2) -- the two params are no longer decoupled. Exact values pinned so a
    # math regression can't slide by under a loose inequality.
    lx = layout_with(front_end_length_x=60.0)
    fe = lx["observer_front_end_swept_body_check"]
    traverse = lx["observer_carriage_envelope_check"]["carriage_traverse"]
    assert fe["front_end_body_fits_dry_bay"] is False
    assert fe["front_end_body_overflow_mm"]["x"] == 38.8
    assert traverse["length_x"] == 159.0  # well-X span 99 + max(scan 21, body 60)
    assert traverse["scan_axis_extent_mm"] == 60.0  # the body, not the placeholder
    assert traverse["fits_dry_bay"] is False

    # Y case: oversized body width drives both the FE-body Y and the traverse Y red.
    ly = layout_with(front_end_width_y=100.0)
    assert ly["observer_front_end_swept_body_check"]["front_end_body_overflow_mm"]["y"] == 77.0
    assert (
        ly["observer_carriage_envelope_check"]["carriage_traverse"]["fits_dry_bay"]
        is False
    )

    # Z case: oversized focus stroke overflows the FE-body Z (6.0 mm). Z containment
    # is owned solely by the FE-body check; the traverse is 2D (X/Y) by design and
    # correctly stays green -- this is documented, not a decoupling.
    lz = layout_with(front_end_focus_stroke_z=50.0)
    assert lz["observer_front_end_swept_body_check"]["front_end_body_overflow_mm"]["z"] == 6.0
    assert (
        lz["observer_carriage_envelope_check"]["carriage_traverse"]["fits_dry_bay"]
        is True
    )

    # Carriage STATIC box gate: an oversized reserved box overflows the bay and is
    # now caught (same bug class, previously ungated).
    lc = layout_with(carriage_length_x=300.0)
    cbox = lc["observer_carriage_envelope_check"]
    assert cbox["carriage_box_fits_dry_bay"] is False
    assert cbox["carriage_box_overflow_mm"]["x"] > 0.0

    # Live params remain a clean fit on every gate (no false positive).
    live = row_coupon_layout(params)
    live_fe = live["observer_front_end_swept_body_check"]
    live_c = live["observer_carriage_envelope_check"]
    assert live_fe["front_end_body_fits_dry_bay"] is True
    assert live_fe["front_end_body_overflow_mm"] == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert live_c["carriage_box_fits_dry_bay"] is True
    assert live_c["carriage_box_overflow_mm"] == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert live_c["carriage_traverse"]["fits_dry_bay"] is True
    assert live_c["carriage_traverse"]["scan_axis_footprint_mm"] == (
        params["observer_robotics"]["front_end_scan_axis_footprint"]
    )
    assert live_c["carriage_traverse"]["scan_axis_extent_mm"] == 21.0


def test_observer_measured_40x40_head_at_25mm_wd_red_case_oc_a8() -> None:
    # OC-A8: the bench-doc "40x40 head @ 25mm WD" measured front-end footprint must
    # NOT slip through any observer geometry gate. The doc figure maps onto the
    # observer_robotics keys as: 40 mm in X (front_end_length_x), 40 mm in Y
    # (front_end_width_y), a 40 mm scan-axis sweep (front_end_scan_axis_footprint),
    # a Ø40 barrel (front_end_barrel_diameter), and a 25 mm working distance / top
    # clearance (front_end_top_clearance_z). Values below are EMPIRICALLY VERIFIED by
    # running row_coupon_layout, not copied from any plan.
    red = deepcopy(load_params(PARAMS))
    red["observer_robotics"]["front_end_length_x"] = 40.0  # doc "40 ... head" -> X
    red["observer_robotics"]["front_end_width_y"] = 40.0  # doc "40x40 head" -> Y
    red["observer_robotics"]["front_end_scan_axis_footprint"] = 40.0  # scan sweep
    red["observer_robotics"]["front_end_barrel_diameter"] = 40.0  # Ø40 objective barrel
    red["observer_robotics"]["front_end_top_clearance_z"] = 25.0  # 25 mm WD -> top clr
    layout = row_coupon_layout(red)

    fe = layout["observer_front_end_swept_body_check"]
    traverse = layout["observer_carriage_envelope_check"]["carriage_traverse"]
    optical = layout["observer_optical_stability_check"]

    # OC-A1: the swept body overflows the dry bay (X by 18.8 mm, Y by 17.0 mm).
    assert fe["front_end_body_fits_dry_bay"] is False
    assert fe["front_end_body_overflow_mm"] == {"x": 18.8, "y": 17.0, "z": 0.0}

    # OC-A2: the traverse scan span is driven by the 40 mm body, not the placeholder,
    # and the carriage no longer fits the bay.
    assert traverse["scan_axis_extent_mm"] == 40.0
    assert traverse["fits_dry_bay"] is False

    # OC-A5: the 25 mm working-distance budget no longer closes vertically.
    assert fe["front_end_vertical_budget_closes"] is False

    # Labeled-secondary cascade: the Ø40 barrel violates the objective keepout, the
    # 40 mm scan footprint drives the corridor margin negative, the traverse no longer
    # clears, and the geometry overflow propagates a hard blocker into the optical-
    # stability check (it can no longer read as "only physical evidence pending").
    assert fe["front_end_fits_objective_keepout"] is False
    assert traverse["scan_corridor_margin_mm"] < 0.0
    assert traverse["clears_traverse"] is False
    assert optical["observer_geometry_clears"] is False
    assert "geometry_overflow_blocks_optical_stability" in optical["blockers"]

    # Green-baseline guard: the unmodified live params clear every gate above, proving
    # the red asserts catch the oversized head rather than constant-failing.
    green = row_coupon_layout(load_params(PARAMS))
    green_fe = green["observer_front_end_swept_body_check"]
    green_tr = green["observer_carriage_envelope_check"]["carriage_traverse"]
    green_opt = green["observer_optical_stability_check"]
    assert green_fe["front_end_body_fits_dry_bay"] is True
    assert green_fe["front_end_body_overflow_mm"] == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert green_fe["front_end_vertical_budget_closes"] is True
    assert green_fe["front_end_fits_objective_keepout"] is True
    assert green_tr["scan_axis_extent_mm"] == 21.0
    assert green_tr["fits_dry_bay"] is True
    assert green_tr["scan_corridor_margin_mm"] >= 0.0
    assert green_tr["clears_traverse"] is True
    assert green_opt["observer_geometry_clears"] is True
    assert "geometry_overflow_blocks_optical_stability" not in green_opt["blockers"]


def test_observer_fiducial_focus_target_check_exports_local_pattern() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    targets = layout["observer_fiducial_focus_targets"]
    spec = layout["observer_fiducial_focus_target_check"]
    check = build_observer_fiducial_focus_target_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()

    assert "observer_fiducial_focus_target_check" in validation
    assert "observer_fiducial_focus_target_check" not in installed
    assert spec["evidence_gate"] == "Gate 6 sensor/thermal"
    assert spec["cad_value"] == "4 apertures / 32 targets / 16 fiducials"
    assert spec["failure_rule"] == (
        "unverified_fiducial_visibility_or_focus_targets_block_observer_readiness"
    )
    assert spec["requires_physical_evidence"] is True
    assert "observer_focus_repeatability" in spec["physical_claims_blocked"]
    assert spec["body_targets"] == targets
    assert len(targets) == params["row"]["plate_count"] * 8
    assert len(check.Solids()) == params["row"]["plate_count"] * 5
    assert {
        "bottom_recess_focus_target",
        "objective_keepout_disk",
        "horizontal_focus_crosshair",
        "vertical_focus_crosshair",
        "observer_fiducial_disk",
    } == {target["target_kind"] for target in targets}
    assert sum(
        1 for target in targets if target["target_kind"] == "observer_fiducial_disk"
    ) == params["row"]["plate_count"] * 4
    assert round(check_bb.zmin, 2) == 0.0
    assert round(check_bb.zmax, 2) == params["dry_bay"]["bottom_recess_depth"]
    for target in targets:
        assert target["tile_index"] in range(1, params["row"]["plate_count"] + 1)


def test_observer_optical_stability_check_requires_measured_evidence() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    spec = layout["observer_optical_stability_check"]
    rect = spec["body_rects"][0]
    check = build_observer_optical_stability_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()

    assert "observer_optical_stability_check" in validation
    assert "observer_optical_stability_check" not in installed
    assert spec["validation"] == "cad_proxy_measured_observer_performance_required"
    assert (
        spec["failure_rule"]
        == "any_unproven_optical_checkpoint_blocks_observer_performance_claim"
    )
    assert spec["evidence_gate"] == "Gate 6 sensor/thermal"
    assert spec["requires_physical_evidence"] is True
    assert spec["checkpoint_count"] == 8
    assert spec["aperture_count"] == len(layout["dry_bay_apertures"])
    assert spec["fiducial_focus_target_count"] == len(
        layout["observer_fiducial_focus_targets"]
    )
    assert spec["cad_value"] == "8 checks / 4 apertures / 32 targets"
    assert spec["target_kind_counts"]["observer_fiducial_disk"] == (
        params["row"]["plate_count"] * 4
    )
    assert spec["thermal_proxy_kind_counts"]["condensation_pocket_low_point"] == (
        params["row"]["plate_count"]
    )
    assert spec["wet_dry_witness_gutter_count"] > 0
    assert {
        "observer_fiducial_focus_target_check",
        "observer_front_end_swept_body_check",
        "observer_carriage_envelope_check",
        "thermal_condensation_proxy_check",
        "dry_bay_ingress_audit_check",
        "wet_dry_failure_path_check",
    }.issubset(spec["source_validation_checks"])
    assert {
        "stray_light_background_unmeasured",
        "focus_repeatability_unmeasured",
        "vibration_motion_blur_unmeasured",
        "thermal_drift_unmeasured",
        "signal_quality_baseline_missing",
        "wet_boundary_optical_contamination_unchecked",
    }.issubset(spec["blockers"])
    assert "raman_signal_quality" in spec["physical_claims_blocked"]
    assert len(check.Solids()) == 1
    assert rect["x"] > layout["length_x"]
    assert round(check_bb.xlen, 2) == rect["length_x"]
    assert round(check_bb.ylen, 2) == rect["width_y"]
    assert round(check_bb.zmax, 2) == rect["height_z"]


def test_observer_kinematic_split_check_blocks_gate6_claims() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    spec = layout["observer_kinematic_split_check"]
    check = build_observer_kinematic_split_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()

    assert "observer_kinematic_split_check" in validation
    assert "observer_kinematic_split_check" not in installed
    assert spec["validation"] == "required_gate6_observer_kinematic_split_evidence"
    assert spec["evidence_gate"] == "Gate 6 sensor/thermal"
    assert (
        spec["failure_rule"]
        == "unproven_front_end_carriage_or_service_split_blocks_observer_readiness"
    )
    assert spec["cad_value"] == "5 checks / 3 split envelopes / 32 targets"
    assert spec["checkpoint_count"] == 5
    assert spec["requires_physical_evidence"] is True
    assert spec["all_checkpoints_block_gate6_pass"] is True
    assert spec["front_end_bounds_mm"] == {"x": 120.0, "y": 347.5, "z": 40.0}
    assert spec["carriage_bounds_mm"] == {"x": 100.0, "y": 58.0, "z": 62.0}
    assert spec["raceway_bounds_mm"] == {"x": 8.0, "y": 357.5, "z": 24.0}
    assert {
        "observer_front_end_swept_body_check",
        "observer_carriage_envelope_check",
        "observer_service_raceway_envelope_check",
        "observer_fiducial_focus_target_check",
        "dry_bay_envelope_check",
    } == set(spec["source_validation_checks"])
    assert {
        "single_large_objective_centered_carriage_unacceptable",
        "focus_axis_travel_or_recovery_unproven",
        "observer_service_loop_recovery_unproven",
    }.issubset(spec["blockers"])
    assert "observer_kinematic_split" in spec["physical_claims_blocked"]
    assert len(check.Solids()) == 1
    assert round(check_bb.xlen, 2) == 58.00
    assert round(check_bb.ylen, 2) == 78.00
    assert round(check_bb.zlen, 2) == 0.45


def test_service_views_and_flow_adapters_are_explicit_review_geometry() -> None:
    params = load_params(PARAMS)
    manifest = row_coupon_part_manifest()
    installed = build_row_coupon_service_parts(params, mode="installed")
    bench_sealed = build_row_coupon_service_parts(params, mode="bench_sealed")
    sample_relief_flow_test = build_row_coupon_service_parts(
        params,
        mode="sample_relief_flow_test",
    )
    exploded = build_row_coupon_service_parts(params, mode="exploded")
    lid_off = build_row_coupon_service_parts(params, mode="lid_off")
    sensor_install = build_row_coupon_service_parts(params, mode="sensor_install")
    adapters = build_flow_test_adapters(params, assembly_position=True).val()

    assert list(installed) == list(build_row_coupon_installed_parts(params))
    assert list(bench_sealed) == list(installed)
    assert manifest["service_modes"]["installed"] == "normal OT-2 operating assembly"
    assert manifest["service_modes"]["bench_sealed"] == (
        "bench-only sealed leak/setup review; not normal OT-2 operating authority"
    )
    assert manifest["service_modes"]["sample_relief_flow_test"] == (
        "bench-only sample/relief flow-test adapter review; not installed operation"
    )
    assert "printed_sample_relief_cap" in installed
    assert "printed_sample_relief_cap" not in sample_relief_flow_test
    assert "sample_relief_flow_test_adapter" not in installed
    assert "sample_relief_flow_test_adapter" in sample_relief_flow_test
    assert sample_relief_flow_test["sample_relief_flow_test_adapter"].val().Volume() == (
        pytest.approx(adapters.Volume(), rel=0.001)
    )
    assert list(exploded) == list(installed)
    assert list(lid_off) == list(installed)
    assert "sensor_installation_path_check" in sensor_install
    assert exploded["printed_wedge_locks"].val().BoundingBox().zmin > (
        installed["printed_wedge_locks"].val().BoundingBox().zmin
    )
    assert lid_off["lid_cover"].val().BoundingBox().ymin > (
        installed["lid_cover"].val().BoundingBox().ymin
    )
    assert lid_off["printed_sample_relief_cap"].val().BoundingBox().ymin > (
        installed["printed_sample_relief_cap"].val().BoundingBox().ymin
    )
    assert sensor_install["gas_sensor_pcbs"].val().BoundingBox().zmin > (
        installed["gas_sensor_pcbs"].val().BoundingBox().zmin
    )
    assert sensor_install["headspace_sht41_microcarriers"].val().BoundingBox().xmin > (
        installed["headspace_sht41_microcarriers"].val().BoundingBox().xmin
    )
    assert sensor_install["ir_thermopiles"].val().BoundingBox().zmin < (
        installed["ir_thermopiles"].val().BoundingBox().zmin
    )
    assert sensor_install["ir_thermopile_face_gaskets"].val().BoundingBox().zmin < (
        installed["ir_thermopile_face_gaskets"].val().BoundingBox().zmin
    )
    assert len(adapters.Solids()) == 1


def test_consumable_metrology_gauge_is_physical_validation_tool() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    metrology = params["consumable_metrology"]
    plate = params["plate"]
    spec = layout["consumable_metrology_gauge"]
    gauge = build_consumable_metrology_gauge(
        params,
        assembly_position=True,
    ).val()
    gauge_bb = gauge.BoundingBox()
    standalone_bb = build_consumable_metrology_gauge(params).val().BoundingBox()

    assert len(gauge.Solids()) == 1
    assert round(gauge_bb.xmin, 2) > round(layout["length_x"], 2)
    assert round(gauge_bb.xlen, 2) == round(
        plate["length_x"] + 2 * metrology["gauge_border_xy"],
        2,
    )
    assert round(gauge_bb.ylen, 2) == round(
        plate["width_y"] + 2 * metrology["gauge_border_xy"],
        2,
    )
    assert round(gauge_bb.zlen, 2) == metrology["gauge_base_thickness_z"]
    assert spec["evidence_gate"] == "Gate 1 Print QC"
    assert spec["validation"] == "required_gate1_consumable_fit_metrology_evidence"
    assert spec["requires_physical_evidence"] is True
    assert spec["cad_value"] == "143.60 x 101.75 x 3.00 mm / 96 plug pockets"
    assert spec["plug_pocket_count"] == 96
    assert spec["source_layout_checks"] == [
        "consumable_metrology",
        "plate",
        "septum_mat",
        "well_grid",
    ]
    assert round(gauge_bb.xmin, 2) == round(spec["x"], 2)
    assert round(gauge_bb.ymin, 2) == round(spec["y"], 2)
    assert round(gauge_bb.zmin, 2) == round(spec["z"], 2)
    assert round(gauge_bb.xlen, 2) == round(spec["length_x"], 2)
    assert round(gauge_bb.ylen, 2) == round(spec["width_y"], 2)
    assert round(gauge_bb.zlen, 2) == round(spec["height_z"], 2)
    assert round(standalone_bb.xmin, 2) == 0.0
    assert round(standalone_bb.ymin, 2) == 0.0


def test_printability_support_cleanup_check_blocks_gate1_claims() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    check_spec = layout["printability_support_cleanup_check"]
    check = build_printability_support_cleanup_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()

    assert check_spec["validation"] == "required_gate1_printability_cleanup_evidence"
    assert check_spec["evidence_gate"] == "Gate 1 Print QC"
    assert check_spec["failure_rule"] == (
        "support_scar_debris_blockage_or_split_edge_feature_loss_blocks_gate1_pass"
    )
    assert check_spec["cad_value"] == "6 checks / 12 printed parts / 2 gas interfaces"
    assert check_spec["checkpoint_count"] == 6
    assert check_spec["printed_part_count"] == 12
    assert check_spec["side_gas_interface_count"] == 2
    assert check_spec["sensor_pocket_count"] == 10
    assert check_spec["wet_dry_witness_gutter_count"] == 8
    assert check_spec["split_source_part_count"] == len(
        ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS
    )
    assert check_spec["requires_physical_evidence"] is True
    assert check_spec["all_checkpoints_block_gate1_pass"] is True
    assert {
        "gasket_compression_gap_gauge",
        "latch_retention_span_check",
        "side_gas_tube_envelope_check",
        "sensor_installation_path_check",
        "wet_dry_failure_path_check",
        "dry_bay_ingress_audit_check",
    }.issubset(set(check_spec["source_validation_checks"]))
    assert any(
        checkpoint["name"] == "dry_bay_gutters_unbridged"
        for checkpoint in check_spec["checkpoints"]
    )
    assert round(check_bb.xlen, 2) == 64.00
    assert round(check_bb.ylen, 2) == 80.00
    assert round(check_bb.zlen, 2) == 1.20


def test_pipette_puncture_swept_path_covers_all_septum_targets() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    sweep = layout["pipette_puncture_swept_path"]
    spec = layout["pipette_puncture_swept_path_check"]
    check = build_pipette_puncture_swept_path_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()

    assert "pipette_puncture_swept_path_check" not in installed
    assert "pipette_puncture_swept_path_check" in validation
    assert spec["evidence_gate"] == "Gate 5 consumable/puncture"
    assert (
        spec["validation"]
        == "required_gate5_all_well_puncture_swept_path_evidence"
    )
    assert spec["failure_rule"] == (
        "blocked_or_unmeasured_puncture_path_blocks_consumable_puncture_pass"
    )
    assert spec["cad_value"] == "384 wells / 2.50 mm / 22.80..64.10 mm"
    assert spec["target_count_cad_value"] == "384 wells"
    assert spec["diameter_cad_value"] == "2.50 mm"
    assert spec["z_range_cad_value"] == "22.80..64.10 mm"
    assert spec["well_count"] == sweep["well_count"]
    assert spec["wells_per_plate"] == 96
    assert spec["requires_physical_evidence"] is True
    assert "all_96_positions_per_plate_puncturable" in spec[
        "physical_claims_blocked"
    ]
    assert len(spec["target_centers"]) == sweep["well_count"]
    assert len(check.Solids()) == sweep["well_count"]
    assert sweep["diameter"] > params["pipette_access"]["tip_outer_diameter_at_septum"]
    assert sweep["bottom_z"] < (
        layout["plate_top_z"] + params["septum_mat"]["sheet_thickness_z"]
    )
    assert sweep["top_z"] > layout["assembly_top_z"]
    assert round(check_bb.zmin, 2) == round(sweep["bottom_z"], 2)
    assert round(check_bb.zmax, 2) == round(sweep["top_z"], 2)


def test_pipette_toolhead_swept_body_clears_connected_services() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    access = params["pipette_access"]
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    body = layout["pipette_toolhead_swept_body"]
    spec = layout["pipette_toolhead_swept_body_check"]
    check = build_pipette_toolhead_swept_body_check(
        params,
        assembly_position=True,
    ).val()
    check_bb = check.BoundingBox()
    grid = params["well_grid"]

    service_rects = layout["operating_service_dress_envelopes"]
    service_top_z = max(rect["z"] + rect["height_z"] for rect in service_rects)

    assert "pipette_toolhead_swept_body_check" not in installed
    assert "pipette_toolhead_swept_body_check" in validation
    assert len(check.Solids()) == 1
    assert body["role"] == "ot2_pipette_toolhead_operating_clearance"
    assert body["validation"] == "conservative_envelope_requires_physical_ot2_measurement"
    assert spec["body_rects"] == [body]
    assert spec["evidence_gate"] == "Gate 3 OT-2 placement"
    assert (
        spec["validation"]
        == "required_gate3_top_pipette_field_clearance_evidence"
    )
    assert spec["failure_rule"] == (
        "toolhead_collision_or_unmeasured_top_field_clearance_blocks_ot2_placement_pass"
    )
    assert spec["cad_value"] == "250.00 x 445.50 x 45.00 mm / 384 wells"
    assert (
        spec["clearance_cad_value"]
        == "8.00 mm assembly / 27.90 mm services / 2.00 mm tip path"
    )
    assert spec["puncture_target_count"] == layout[
        "pipette_puncture_swept_path_check"
    ]["well_count"]
    assert spec["requires_physical_evidence"] is True
    assert "top_pipette_field_clear" in spec["physical_claims_blocked"]
    assert {
        "pipette_puncture_swept_path_check",
        "operating_service_dress_check",
        "row_tiling_service_clearance_check",
    } == set(spec["source_layout_checks"])
    assert body["covered_well_count"] == (
        params["row"]["plate_count"] * grid["columns"] * grid["rows"]
    )
    assert body["service_envelope_count"] == len(service_rects)
    assert body["height_z"] == access["ot2_toolhead_envelope_height_z"]
    assert body["assembly_clearance_z"] >= access[
        "ot2_toolhead_bottom_clearance_above_assembly_z"
    ]
    assert body["service_clearance_z"] >= access["ot2_toolhead_service_clearance_z"]
    assert body["tip_transition_gap_z"] >= access["ot2_toolhead_service_clearance_z"]
    assert body["z"] >= service_top_z + access["ot2_toolhead_service_clearance_z"]
    assert body["z"] > layout["assembly_top_z"]
    assert body["z"] > layout["pipette_puncture_swept_path"]["top_z"]
    assert round(check_bb.xmin, 2) == round(body["x"], 2)
    assert round(check_bb.ymin, 2) == round(body["y"], 2)
    assert round(check_bb.zmin, 2) == round(body["z"], 2)
    assert round(check_bb.xlen, 2) == round(body["length_x"], 2)
    assert round(check_bb.ylen, 2) == round(body["width_y"], 2)
    assert round(check_bb.zlen, 2) == round(body["height_z"], 2)

    for tile in layout["tile_origins"]:
        for col_idx in range(grid["columns"]):
            for row_idx in range(grid["rows"]):
                x = tile["x"] + grid["first_well_center_x"] + col_idx * grid["pitch_x"]
                y = tile["y"] + grid["first_well_center_y"] + row_idx * grid["pitch_y"]
                assert body["x"] <= x <= body["x"] + body["length_x"]
                assert body["y"] <= y <= body["y"] + body["width_y"]


def test_validation_parts_are_not_default_production_parts() -> None:
    params = load_params(PARAMS)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)

    assert set(validation) == {
        "consumable_metrology_gauge",
        "printability_support_cleanup_check",
        "deck_slot_footprint_check",
        "deck_frame_keepout_check",
        "deck_pod_seating_repeatability_check",
        "dry_bay_envelope_check",
        "dry_bay_boundary_check",
        "headspace_barrier_check",
        "headspace_volume_check",
        "well_cell_plane_check",
        "ir_thermopile_fov_spot_check",
        "thermal_condensation_proxy_check",
        "pipette_puncture_swept_path_check",
        "pipette_toolhead_swept_body_check",
        "observer_front_end_swept_body_check",
        "observer_carriage_envelope_check",
        "observer_service_raceway_envelope_check",
        "observer_fiducial_focus_target_check",
        "observer_optical_stability_check",
        "observer_kinematic_split_check",
        "assembly_state_witness_check",
        "gasket_compression_gap_gauge",
        "latch_retention_span_check",
        "fail_closed_prerun_inspection_check",
        "material_cleaning_witness_coupon",
        "wet_dry_failure_path_check",
        "sensor_connector_service_clearance_check",
        "sensor_installation_path_check",
        "sensor_service_cable_envelope_check",
        "electrical_connector_mating_state_check",
        "operating_service_dress_check",
        "row_tiling_service_clearance_check",
        "gas_pcb_flow_cell_check",
        "side_gas_tube_envelope_check",
        "side_gas_leak_witness_check",
        "sample_relief_leak_witness_check",
        "gasket_tab_leak_witness_check",
        "dry_bay_ingress_audit_check",
        "adjacent_deck_slot_keepout_check",
    }
    assert set(validation).isdisjoint(installed)


def test_wet_dry_failure_path_check_is_hidden_validation_geometry() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    installed = build_row_coupon_installed_parts(params)
    validation = build_row_coupon_validation_parts(params)
    check = build_wet_dry_failure_path_check(params, assembly_position=True).val()
    check_bb = check.BoundingBox()
    spec = layout["wet_dry_failure_path_check"]
    gutters = layout["wet_dry_failure_paths"]["wet_dry_witness_gutters"]
    thresholds = layout["wet_dry_failure_paths"]["dry_bay_aperture_thresholds"]

    assert "wet_dry_failure_path_check" in validation
    assert "wet_dry_failure_path_check" not in installed
    assert spec["evidence_gate"] == "Gate 4 wet/dry witness"
    assert spec["cad_value"] == "8 gutters / 4 raised thresholds / 0.45 mm gutter depth"
    assert spec["gutter_cad_value"] == "8 gutters, 0.45 mm depth"
    assert spec["threshold_cad_value"] == "4 raised thresholds"
    assert spec["failure_rule"] == (
        "aperture_leak_bridge_or_unmeasured_gutter_blocks_wet_dry_pass"
    )
    assert spec["requires_physical_evidence"] is True
    assert "wet_operation_without_optics_ingress" in spec["physical_claims_blocked"]
    assert spec["gutter_count"] == len(gutters)
    assert spec["threshold_count"] == len(thresholds)
    assert spec["threshold_rects"] == thresholds
    assert len(spec["body_rects"]) == len(gutters)
    assert all(rect["height_z"] == rect["depth_z"] for rect in spec["body_rects"])
    assert len(check.Solids()) == spec["gutter_count"]
    assert round(check_bb.zmax, 2) <= round(layout["base_top_z"], 2)
    assert round(check_bb.zmin, 2) == round(
        layout["base_top_z"] - params["production_assembly"]["wet_dry_witness_gutter_depth_z"],
        2,
    )


def test_latch_mechanism_demo_is_separate_printable_assembly() -> None:
    params = load_params(PARAMS)
    installed = build_row_coupon_installed_parts(params)
    demo = build_latch_mechanism_demo_parts(params, assembly_position=True)

    assert set(demo) == {
        "latch_demo_lower_catch",
        "latch_demo_compressed_gasket",
        "latch_demo_upper_receiver",
        "latch_demo_sliding_wedge",
    }
    assert set(demo).isdisjoint(installed)
    assert demo["latch_demo_sliding_wedge"].val().BoundingBox().xmax <= (
        demo["latch_demo_lower_catch"].val().BoundingBox().xmax
    )
    assert demo["latch_demo_sliding_wedge"].val().BoundingBox().zmin > (
        demo["latch_demo_lower_catch"].val().BoundingBox().zmin
    )
    assert demo["latch_demo_upper_receiver"].val().BoundingBox().zmin > (
        demo["latch_demo_sliding_wedge"].val().BoundingBox().zmin
    )


def test_headspace_volume_check_is_one_shared_row_volume() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    barrier = build_headspace_barrier_check(params).val()
    headspace = build_headspace_volume_check(params).val()
    barrier_bb = barrier.BoundingBox()
    headspace_bb = headspace.BoundingBox()
    barrier_spec = layout["headspace_barrier_check"]
    volume_spec = layout["headspace_volume_check"]

    assert barrier_spec["evidence_gate"] == "Gate 4 wet/dry witness"
    assert barrier_spec["cad_value"] == (
        "148.60 x 377.25 x 5.80 mm perimeter, 2.00 mm wall"
    )
    assert barrier_spec["failure_rule"] == (
        "sealed_perimeter_leak_or_bypass_blocks_wet_dry_pass"
    )
    assert barrier_spec["requires_physical_evidence"] is True
    assert "sealed_wet_headspace_perimeter" in barrier_spec["physical_claims_blocked"]
    assert len(barrier_spec["body_rects"]) == 4
    assert volume_spec["evidence_gate"] == "Gate 4 wet/dry witness"
    assert volume_spec["cad_value"] == "138.60 x 367.25 x 5.80 mm shared volume"
    assert volume_spec["failure_rule"] == (
        "blocked_bridged_or_discontinuous_shared_headspace_blocks_wet_dry_pass"
    )
    assert volume_spec["requires_physical_evidence"] is True
    assert "shared_wet_headspace_continuity" in volume_spec["physical_claims_blocked"]
    assert len(volume_spec["body_rects"]) == 1
    assert round(barrier_bb.zlen, 2) == round(barrier_spec["height_z"], 2)
    assert len(headspace.Solids()) == 1
    assert round(headspace_bb.xlen, 2) == round(
        layout["length_x"] - 2 * params["seal_interface"]["gasket_rail_width"],
        2,
    )
    assert round(headspace_bb.ylen, 2) == round(
        layout["width_y"] - 2 * params["seal_interface"]["gasket_rail_width"],
        2,
    )
    assert headspace_bb.ylen > params["plate"]["width_y"]


def test_septum_mats_are_serviceable_insert_bodies() -> None:
    params = load_params(PARAMS)
    plain_params = deepcopy(params)
    plain_params["septum_mat"]["slit_cut_length_x"] = 0.0
    plain_params["septum_mat"]["slit_cut_width_y"] = 0.0
    mats = build_septum_mat_inserts(params).val()
    plain_mats = build_septum_mat_inserts(plain_params).val()
    mat_bb = mats.BoundingBox()

    assert len(mats.Solids()) == params["row"]["plate_count"]
    assert "slit_cut_length_x" in params["septum_mat"]
    assert "slit_cut_width_y" in params["septum_mat"]
    assert "slit_mark_length_x" not in params["septum_mat"]
    assert "slit_mark_width_y" not in params["septum_mat"]
    assert round(mat_bb.xlen, 2) == params["plate"]["length_x"]
    assert round(mat_bb.ylen, 2) == round(
        4 * params["plate"]["width_y"] + 3 * params["row"]["inter_tile_gap_y"],
        2,
    )
    assert round(mat_bb.zlen, 2) == (
        params["septum_mat"]["sheet_thickness_z"]
        + params["septum_mat"]["round_plug_depth_z"]
    )
    assert mats.Volume() < plain_mats.Volume()


def test_row_coupon_components_have_expected_bounds() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)

    deck_pods_bb = build_deck_pods(params).val().BoundingBox()
    support_frame_bb = build_plate_support_frame(params).val().BoundingBox()
    gasket_bb = build_upper_gasket(params).val().BoundingBox()
    barrier_bb = build_headspace_barrier_check(params).val().BoundingBox()
    headspace_bb = build_headspace_volume_check(params).val().BoundingBox()
    dry_bay_bb = build_dry_bay_envelope_check(params).val().BoundingBox()
    dry_bay_boundary_bb = build_dry_bay_boundary_check(params).val().BoundingBox()
    deck_slots_bb = build_deck_slot_footprint_check(params).val().BoundingBox()
    deck_frame_bb = build_deck_frame_keepout_check(params).val().BoundingBox()
    carriage_bb = build_observer_carriage_envelope_check(params).val().BoundingBox()
    service_bb = build_observer_service_raceway_envelope_check(params).val().BoundingBox()
    lid_shell_bb = build_lid_manifold_shell(params).val().BoundingBox()
    lid_cover_bb = (
        build_lid_cover(params)
        .translate((0, 0, params["lid_manifold"]["thickness_z"]))
        .val()
        .BoundingBox()
    )
    plates_bb = build_microplates(params).val().BoundingBox()
    septum_bb = build_septum_mat_inserts(params).val().BoundingBox()
    frame_bb = build_wet_chamber_frame(params).val().BoundingBox()
    lower_stack_xmin = min(deck_pods_bb.xmin, support_frame_bb.xmin)
    lower_stack_xmax = max(deck_pods_bb.xmax, support_frame_bb.xmax)
    lower_stack_ymin = min(deck_pods_bb.ymin, support_frame_bb.ymin)
    lower_stack_ymax = max(deck_pods_bb.ymax, support_frame_bb.ymax)
    lower_stack_zmin = min(deck_pods_bb.zmin, support_frame_bb.zmin)
    lower_stack_zmax = max(deck_pods_bb.zmax, support_frame_bb.zmax)
    lid_stack_zmin = min(lid_shell_bb.zmin, lid_cover_bb.zmin)
    lid_stack_zmax = max(lid_shell_bb.zmax, lid_cover_bb.zmax)

    assert round(lower_stack_xmax - lower_stack_xmin, 2) == round(layout["length_x"], 2)
    assert round(lower_stack_ymax - lower_stack_ymin, 2) == round(layout["width_y"], 2)
    assert round(lower_stack_zmax - lower_stack_zmin, 2) == (
        params["base"]["thickness_z"] + params["plate_support"]["land_height_z"]
        + params["plate_support"]["lateral_locator_wall_height_z"]
        + params["deck_interface"]["standoff_height_z"]
        + params["deck_interface"]["slot_shoe_thickness_z"]
    )
    assert round(gasket_bb.zlen, 2) == params["seal_interface"]["compressed_gasket_height_z"]
    assert round(gasket_bb.xlen, 2) == round(layout["length_x"], 2)
    assert round(gasket_bb.ylen, 2) == round(layout["width_y"], 2)
    assert round(septum_bb.xlen, 2) == params["plate"]["length_x"]
    assert round(septum_bb.ylen, 2) == round(
        4 * params["plate"]["width_y"] + 3 * params["row"]["inter_tile_gap_y"],
        2,
    )
    assert round(septum_bb.zlen, 2) == (
        params["septum_mat"]["sheet_thickness_z"]
        + params["septum_mat"]["round_plug_depth_z"]
    )
    assert round(frame_bb.xlen, 2) == round(layout["length_x"], 2)
    assert round(frame_bb.ylen, 2) == round(layout["width_y"], 2)
    assert round(frame_bb.zlen, 2) == round(
        layout["latch_post_head_top_z"] - layout["base_top_z"],
        2,
    )
    assert round(barrier_bb.xlen, 2) == round(layout["length_x"], 2)
    assert round(barrier_bb.ylen, 2) == round(layout["width_y"], 2)
    assert round(barrier_bb.zlen, 2) == (
        params["seal_interface"]["compressed_gasket_height_z"]
        + params["seal_interface"]["headspace_recess_depth_z"]
    )
    assert round(headspace_bb.zlen, 2) == (
        params["seal_interface"]["compressed_gasket_height_z"]
        + params["seal_interface"]["headspace_recess_depth_z"]
    )
    assert round(dry_bay_bb.xlen, 2) == round(layout["dry_bay_envelope"]["length_x"], 2)
    assert round(dry_bay_bb.ylen, 2) == round(layout["dry_bay_envelope"]["width_y"], 2)
    assert round(dry_bay_bb.zlen, 2) == params["dry_bay"]["observer_sweep_depth_z"]
    assert round(dry_bay_boundary_bb.zlen, 2) == params["dry_bay"]["boundary_rail_height_z"]
    dry_bay_envelope_spec = layout["dry_bay_envelope_check"]
    dry_bay_boundary_spec = layout["dry_bay_boundary_check"]
    assert dry_bay_envelope_spec["evidence_gate"] == "Gate 4 wet/dry witness"
    assert dry_bay_envelope_spec["cad_value"] == "120.20 x 357.50 x 80.00 mm"
    assert dry_bay_envelope_spec["failure_rule"] == (
        "dye_condensate_debris_or_service_lead_inside_dry_bay_blocks_wet_dry_pass"
    )
    assert dry_bay_envelope_spec["requires_physical_evidence"] is True
    assert "wet_operation_without_dry_bay_ingress" in (
        dry_bay_envelope_spec["physical_claims_blocked"]
    )
    assert len(dry_bay_envelope_spec["body_rects"]) == 1
    assert dry_bay_boundary_spec["evidence_gate"] == "Gate 4 wet/dry witness"
    assert dry_bay_boundary_spec["cad_value"] == (
        "132.20 x 357.50 x 3.00 mm, 4.00 mm rails"
    )
    assert dry_bay_boundary_spec["failure_rule"] == (
        "boundary_rail_interference_or_debris_bridge_blocks_wet_dry_pass"
    )
    assert dry_bay_boundary_spec["requires_physical_evidence"] is True
    assert "dry_bay_boundary_clearance" in (
        dry_bay_boundary_spec["physical_claims_blocked"]
    )
    assert len(dry_bay_boundary_spec["body_rects"]) == 2
    assert round(carriage_bb.xlen, 2) == params["observer_robotics"]["carriage_length_x"]
    assert round(carriage_bb.ylen, 2) == params["observer_robotics"]["carriage_width_y"]
    assert round(carriage_bb.zlen, 2) == params["observer_robotics"]["carriage_height_z"]
    assert round(service_bb.xlen, 2) == params["observer_robotics"]["service_raceway_width_y"]
    assert round(service_bb.ylen, 2) == round(layout["dry_bay_envelope"]["width_y"], 2)
    assert round(service_bb.zlen, 2) == params["observer_robotics"]["service_raceway_height_z"]
    assert round(deck_slots_bb.xlen, 2) == params["deck_interface"]["slot_opening_length_x"]
    assert round(deck_slots_bb.ylen, 2) == round(
        params["deck_interface"]["slot_opening_width_y"]
        + 3 * params["deck_interface"]["slot_pitch_y"],
        2,
    )
    assert round(deck_frame_bb.xlen, 2) == round(layout["length_x"], 2)
    assert round(deck_frame_bb.ylen, 2) == round(layout["width_y"], 2)
    assert round(deck_frame_bb.zlen, 2) == params["deck_interface"][
        "deck_frame_keepout_height_z"
    ]
    assert round(lid_stack_zmax - lid_stack_zmin, 2) == (
        params["lid_manifold"]["thickness_z"]
        + params["sensor_mounts"]["gas_pcb_envelope_width"]
        + params["production_assembly"]["gasket_tab_witness_dam_height_z"]
    )
    assert round(plates_bb.zlen, 2) == params["plate"]["height_z"]


def test_row_coupon_params_live_in_cad_directory() -> None:
    assert Path(PARAMS).is_file()
