from __future__ import annotations
from typing import Any
from .parts._shared_tile import (_lid_port_positions, _well_centers_for_tile)


def _compression_stop_positions(params: dict[str, Any]) -> list[tuple[float, float]]:
    layout = row_coupon_layout(params)
    return _compression_stop_positions_for_layout(layout, params)


def _compression_stop_positions_for_layout(
    layout: dict[str, Any],
    params: dict[str, Any],
) -> list[tuple[float, float]]:
    row = params["row"]
    seal = params["seal_interface"]
    half_stop = seal["compression_stop_size"] / 2
    if layout["row_axis"] == "x":
        gap = row["inter_tile_gap_x"]
        x_values = [
            row["end_margin_x"] / 2,
            layout["length_x"] - row["end_margin_x"] / 2,
        ]
        x_values.extend(tile["x"] - gap / 2 for tile in layout["tile_origins"][1:])
        y_values = [
            row["side_margin_y"] / 2,
            layout["width_y"] - row["side_margin_y"] / 2,
        ]
    else:
        gap = row["inter_tile_gap_y"]
        x_values = [
            row["end_margin_x"] / 2,
            layout["length_x"] - row["end_margin_x"] / 2,
        ]
        y_values = [
            row["side_margin_y"] / 2,
            layout["width_y"] - row["side_margin_y"] / 2,
        ]
        y_values.extend(tile["y"] - gap / 2 for tile in layout["tile_origins"][1:])

    positions = {
        (round(x, 3), round(y, 3))
        for x in x_values
        for y in y_values
        if half_stop < x < layout["length_x"] - half_stop
        and half_stop < y < layout["width_y"] - half_stop
    }
    return sorted(positions)


def _slot_centers(center_x: float, count: int, slot_len: float) -> list[float]:
    if count <= 1:
        return [center_x]
    spacing = slot_len * 0.7
    start = center_x - spacing * (count - 1) / 2
    return [start + idx * spacing for idx in range(count)]


def row_coupon_layout(params: dict[str, Any]) -> dict[str, Any]:
    from aevum_cad.row_coupon import (
        _TRAVERSE_FIT_TOLERANCE_MM,
        _adjacent_deck_slot_keepout_check,
        _adjacent_deck_slot_keepout_rectangles,
        _adjacent_slot_service_collision_review_rectangles,
        _assembly_debris_review_rectangles,
        _assembly_state_witness_check,
        _condensation_pocket_rectangles_for_layout,
        _consumable_metrology_gauge,
        _cots_gas_service_tubes,
        _deck_engagement_foot_rectangles,
        _deck_frame_keepout_check,
        _deck_module_unseated_review_rectangles,
        _deck_pod_seating_repeatability_check,
        _deck_pose_repeatability_review_rectangles,
        _deck_slot_footprint_check,
        _deck_slot_footprint_rectangles,
        _dry_bay_aperture_rectangles,
        _dry_bay_boundary_check,
        _dry_bay_envelope_check,
        _dry_bay_ingress_audit_check,
        _dry_bay_ingress_audit_rectangles,
        _dry_bay_obstruction_review_rectangles,
        _electrical_connector_mating_state_check,
        _fail_closed_prerun_inspection_check,
        _gas_pcb_flow_cell_check_for_layout,
        _gas_sensor_pcb_mounts_for_layout,
        _gasket_compression_gap_gauge_for_layout,
        _gasket_squeeze_out_of_range_review_rectangles,
        _gasket_tab_leak_witness_check,
        _gasket_tab_leak_witnesses_for_layout,
        _harness_seam_routing_check,
        _headspace_barrier_check,
        _headspace_sht41_mounts_for_layout,
        _headspace_volume_check,
        _ir_sensor_mounts_for_layout,
        _ir_thermopile_fov_spot_check,
        _latch_mechanical_screens,
        _latch_post_positions_for_locks,
        _latch_retention_span_check,
        _material_cleaning_witness_coupon,
        _material_cleaning_witness_coupons_for_policy,
        _misdressed_service_bundle_review_rectangles,
        _missing_gas_pcb_cartridge_witness_rectangles,
        _missing_local_sensor_witness_rectangles,
        _missing_microplate_witness_rectangles,
        _missing_perimeter_gasket_witness_rectangles,
        _missing_septum_mat_witness_rectangles,
        _missing_service_lead_witness_rectangles,
        _observer_carriage_envelope_check,
        _observer_carriage_traverse,
        _observer_fiducial_focus_target_check,
        _observer_fiducial_focus_target_rectangles,
        _observer_front_end_swept_body_check,
        _observer_infinity_port_datum_check,
        _observer_kinematic_split_check,
        _observer_optical_stability_check,
        _observer_service_raceway_envelope_check,
        _operating_service_dress_check,
        _pipette_puncture_swept_path_check,
        _pipette_toolhead_swept_body_check,
        _plate_lateral_locator_rectangles,
        _pod_frame_key_rectangles,
        _port_service_review_state_metadata,
        _printability_support_cleanup_check,
        _row_tiling_service_clearance_check,
        _sample_relief_leak_witness_check,
        _sample_relief_leak_witnesses_for_layout,
        _sensor_connector_service_clearance_check,
        _sensor_harness_for_layout,
        _sensor_installation_for_layout,
        _sensor_service_cable_envelope_check,
        _side_gas_adjacent_slot_clearance,
        _side_gas_leak_witness_check,
        _side_gas_service_interfaces,
        _side_gas_tube_envelope_check,
        _side_gas_tube_envelopes,
        _split_segment_swept_removal_check,
        _thermal_condensation_proxy_check,
        _thermal_condensation_proxy_targets_for_layout,
        _trapped_plate_lift_check,
        _unmated_sensor_service_connector_review_rectangles,
        _unseated_gas_pcb_cartridge_review_rectangles,
        _unseated_side_gas_tube_review_specs,
        _wedge_lock_rectangles_for_layout,
        _well_cell_plane_check,
        _wet_dry_failure_path_check,
        _wet_dry_failure_path_geometry,
    )
    row = params["row"]
    plate = params["plate"]
    mat = params["septum_mat"]
    base = params["base"]
    support = params["plate_support"]
    bay = params["dry_bay"]
    deck = params["deck_interface"]
    observer = params["observer_robotics"]
    seal = params["seal_interface"]
    lid = params["lid_manifold"]
    access = params["pipette_access"]
    skirt = params["wet_chamber_skirt"]
    production = params.get("production_assembly", {})

    plate_count = row["plate_count"]
    plate_len = plate["length_x"]
    plate_wid = plate["width_y"]
    row_axis = row.get("axis", "x")
    if row_axis not in {"x", "y"}:
        raise ValueError("row axis must be 'x' or 'y'")
    gap = row.get("inter_tile_gap_y" if row_axis == "y" else "inter_tile_gap_x")
    if gap is None:
        raise ValueError("row gap is required for the configured row axis")
    end_margin = row["end_margin_x"]
    side_margin = row["side_margin_y"]
    if row_axis == "x":
        length = end_margin * 2 + plate_count * plate_len + (plate_count - 1) * gap
        width = side_margin * 2 + plate_wid
        tile_pitch_x = plate_len + gap
        tile_pitch_y = 0.0
        tile_origins = [
            {
                "index": idx + 1,
                "x": end_margin + idx * tile_pitch_x,
                "y": side_margin,
            }
            for idx in range(plate_count)
        ]
    else:
        length = end_margin * 2 + plate_len
        width = side_margin * 2 + plate_count * plate_wid + (plate_count - 1) * gap
        tile_pitch_x = 0.0
        tile_pitch_y = plate_wid + gap
        tile_origins = [
            {
                "index": idx + 1,
                "x": end_margin,
                "y": side_margin + idx * tile_pitch_y,
            }
            for idx in range(plate_count)
        ]

    aperture_x0 = min(
        tile["x"] + (plate_len - bay["aperture_length_x"]) / 2
        for tile in tile_origins
    )
    aperture_x1 = max(
        tile["x"] + (plate_len + bay["aperture_length_x"]) / 2
        for tile in tile_origins
    )
    aperture_y0 = min(
        tile["y"] + (plate_wid - bay["aperture_width_y"]) / 2
        for tile in tile_origins
    )
    aperture_y1 = max(
        tile["y"] + (plate_wid + bay["aperture_width_y"]) / 2
        for tile in tile_origins
    )
    dry_ref_x0 = max(0.0, aperture_x0 - bay["observer_sweep_extra_x"])
    dry_ref_x1 = min(length, aperture_x1 + bay["observer_sweep_extra_x"])
    dry_ref_y0 = max(0.0, aperture_y0 - bay["observer_sweep_extra_y"])
    dry_ref_y1 = min(width, aperture_y1 + bay["observer_sweep_extra_y"])
    dry_bay_envelope = {
        "x": round(dry_ref_x0, 3),
        "y": round(dry_ref_y0, 3),
        "length_x": round(dry_ref_x1 - dry_ref_x0, 3),
        "width_y": round(dry_ref_y1 - dry_ref_y0, 3),
        "bottom_z": -bay["observer_sweep_depth_z"],
        "top_z": 0.0,
    }
    if row_axis == "x":
        carriage_x = (
            tile_origins[0]["x"] + plate_len / 2 - observer["carriage_length_x"] / 2
        )
        carriage_y = (dry_ref_y0 + dry_ref_y1) / 2 - observer["carriage_width_y"] / 2
    else:
        carriage_x = (dry_ref_x0 + dry_ref_x1) / 2 - observer["carriage_length_x"] / 2
        carriage_y = (
            tile_origins[0]["y"] + plate_wid / 2 - observer["carriage_width_y"] / 2
        )
    carriage_z = -bay["observer_sweep_depth_z"] + (
        bay["observer_sweep_depth_z"]
        - observer["carriage_top_clearance_z"]
        - observer["carriage_height_z"]
    )
    if row_axis == "x":
        raceway_x = dry_ref_x0
        raceway_y = (
            dry_ref_y1
            + bay["boundary_rail_clearance_y"]
            + bay["boundary_rail_width_y"]
            + observer["service_raceway_clearance_y"]
        )
        raceway_length_x = dry_ref_x1 - dry_ref_x0
        raceway_width_y = observer["service_raceway_width_y"]
        raceway_y = min(width - raceway_width_y, raceway_y)
    else:
        raceway_x = (
            dry_ref_x1
            + bay["boundary_rail_clearance_y"]
            + bay["boundary_rail_width_y"]
            + observer["service_raceway_clearance_y"]
        )
        raceway_y = dry_ref_y0
        raceway_length_x = observer["service_raceway_width_y"]
        raceway_width_y = dry_ref_y1 - dry_ref_y0
        raceway_x = min(length - raceway_length_x, raceway_x)
    raceway_z = -bay["observer_sweep_depth_z"] + (
        bay["observer_sweep_depth_z"] - observer["service_raceway_height_z"]
    ) / 2

    base_top_z = base["thickness_z"]
    plate_bottom_z = base_top_z + support["land_height_z"]
    plate_top_z = plate_bottom_z + plate["height_z"]
    lid_bottom_z = plate_top_z + seal["compressed_gasket_height_z"]
    lid_top_z = lid_bottom_z + lid["thickness_z"]
    deck_plane_z = -(deck["standoff_height_z"] + deck["slot_shoe_thickness_z"])
    port_boss_top_z = lid_top_z + max(
        lid["port_boss_height_z"],
        lid.get("sample_port_boss_height_z", 0.0),
        lid.get("sensor_port_boss_height_z", 0.0),
    )
    port_top_z = lid_top_z + max(lid["duct_height_z"], port_boss_top_z - lid_top_z)
    port_cap_top_z = port_boss_top_z + production.get(
        "port_cap_flange_height_z",
        0.0,
    ) + production.get("port_cap_grip_height_z", 0.0)
    latch_post_head_top_z = (
        lid_top_z
        + lid["duct_height_z"]
        + production.get("wedge_lock_height_z", 0.0)
        + production.get("latch_post_head_height_z", 0.0)
    )
    if production.get("latch_post_diameter", 0.0) <= 0:
        latch_post_head_top_z = port_top_z
    assembly_top_z = max(port_top_z, port_cap_top_z, latch_post_head_top_z)
    headspace_check_top_z = lid_bottom_z + seal["headspace_recess_depth_z"]
    edge_inset = skirt.get("edge_inset_xy", 0.0)
    skirt_bounds = {
        "x": round(edge_inset, 3),
        "y": round(edge_inset, 3),
        "length_x": round(length - 2 * edge_inset, 3),
        "width_y": round(width - 2 * edge_inset, 3),
        "bottom_z": base_top_z,
        "top_z": plate_top_z,
        "height_z": round(plate_top_z - base_top_z, 3),
    }
    headspace_barrier_check = _headspace_barrier_check(
        skirt_bounds,
        seal=seal,
        plate_top_z=plate_top_z,
    )
    headspace_volume_check = _headspace_volume_check(
        skirt_bounds,
        seal=seal,
        plate_top_z=plate_top_z,
    )
    dry_bay_envelope_check = _dry_bay_envelope_check(dry_bay_envelope)
    dry_bay_boundary_check = _dry_bay_boundary_check(
        dry_bay_envelope,
        params=params,
        row_axis=row_axis,
    )
    deck_engagement_feet = _deck_engagement_foot_rectangles(
        tile_origins=tile_origins,
        params=params,
    )
    deck_module_unseated_review = _deck_module_unseated_review_rectangles(
        deck_engagement_feet=deck_engagement_feet,
        deck_plane_z=deck_plane_z,
        params=params,
    )
    deck_slot_footprint_rects = _deck_slot_footprint_rectangles(
        tile_origins=tile_origins,
        params=params,
        deck_plane_z=deck_plane_z,
    )
    deck_slot_footprint_check = _deck_slot_footprint_check(
        deck_slot_footprint_rects,
    )
    deck_frame_keepout_check = _deck_frame_keepout_check(
        position_layout={
            "length_x": round(length, 3),
            "width_y": round(width, 3),
            "tile_origins": tile_origins,
        },
        params=params,
        deck_plane_z=deck_plane_z,
        slot_footprint_rects=deck_slot_footprint_rects,
    )
    deck_pod_frame_keys = _pod_frame_key_rectangles(
        tile_origins=tile_origins,
        params=params,
    )
    compression_stop_positions = _compression_stop_positions_for_layout(
        {
            "row_axis": row_axis,
            "length_x": round(length, 3),
            "width_y": round(width, 3),
            "tile_origins": tile_origins,
        },
        params,
    )
    position_layout = {
        "row_axis": row_axis,
        "length_x": round(length, 3),
        "width_y": round(width, 3),
        "tile_origins": tile_origins,
        "compression_stop_positions": compression_stop_positions,
    }
    condensation_pocket_rects = _condensation_pocket_rectangles_for_layout(
        position_layout,
        params=params,
        z0=base_top_z,
    )
    lid_port_positions = _lid_port_positions(position_layout, params)
    sample_relief_leak_witnesses = _sample_relief_leak_witnesses_for_layout(
        position_layout,
        ports=lid_port_positions,
        params=params,
        lid_top_z=lid_top_z,
    )
    if sample_relief_leak_witnesses:
        assembly_top_z = max(
            assembly_top_z,
            max(float(witness["top_z"]) for witness in sample_relief_leak_witnesses),
        )
    if lid_port_positions:
        actual_port_boss_height_z = max(
            float(port["boss_height_z"]) for port in lid_port_positions
        )
        port_boss_top_z = lid_top_z + actual_port_boss_height_z
        port_top_z = lid_top_z + max(lid["duct_height_z"], actual_port_boss_height_z)
        port_cap_top_z = port_boss_top_z + production.get(
            "port_cap_flange_height_z",
            0.0,
        ) + production.get("port_cap_grip_height_z", 0.0)
        assembly_top_z = max(port_top_z, port_cap_top_z, latch_post_head_top_z)
    side_gas_service_interfaces = _side_gas_service_interfaces(
        position_layout,
        params=params,
        lid_top_z=lid_top_z,
    )
    if side_gas_service_interfaces:
        assembly_top_z = max(
            assembly_top_z,
            max(float(interface["top_z"]) for interface in side_gas_service_interfaces),
        )
    side_gas_tube_envelopes = _side_gas_tube_envelopes(side_gas_service_interfaces)
    side_gas_tube_envelope_check = _side_gas_tube_envelope_check(
        side_gas_tube_envelopes
    )
    side_gas_leak_witness_check = _side_gas_leak_witness_check(
        side_gas_service_interfaces
    )
    cots_gas_service_tubes = _cots_gas_service_tubes(side_gas_service_interfaces)
    unseated_side_gas_tubes_review = _unseated_side_gas_tube_review_specs(
        cots_gas_service_tubes,
        params=params,
    )
    adjacent_deck_slot_keepouts = _adjacent_deck_slot_keepout_rectangles(
        position_layout,
        params=params,
        deck_plane_z=deck_plane_z,
    )
    adjacent_deck_slot_keepout_check = _adjacent_deck_slot_keepout_check(
        adjacent_deck_slot_keepouts,
        params=params,
    )
    adjacent_slot_service_collision_review = (
        _adjacent_slot_service_collision_review_rectangles(
            adjacent_keepouts=adjacent_deck_slot_keepouts,
            params=params,
        )
    )
    side_gas_adjacent_slot_clearance = _side_gas_adjacent_slot_clearance(
        side_gas_service_interfaces,
        adjacent_deck_slot_keepouts,
        params=params,
    )
    dry_bay_apertures = _dry_bay_aperture_rectangles(
        tile_origins=tile_origins,
        params=params,
    )
    observer_fiducial_focus_targets = _observer_fiducial_focus_target_rectangles(
        apertures=dry_bay_apertures,
        params=params,
    )
    observer_fiducial_focus_target_check = _observer_fiducial_focus_target_check(
        observer_fiducial_focus_targets,
        aperture_count=len(dry_bay_apertures),
        dry_bay_envelope=dry_bay_envelope,
    )
    wet_dry_failure_paths = _wet_dry_failure_path_geometry(
        apertures=dry_bay_apertures,
        params=params,
        base_top_z=base_top_z,
    )
    gasket_tab_leak_witnesses = _gasket_tab_leak_witnesses_for_layout(
        position_layout,
        params=params,
        base_top_z=base_top_z,
        lid_bottom_z=lid_bottom_z,
    )
    wet_dry_failure_path_check = _wet_dry_failure_path_check(
        wet_dry_failure_paths
    )
    sample_relief_leak_witness_check = _sample_relief_leak_witness_check(
        sample_relief_leak_witnesses
    )
    gasket_tab_leak_witness_check = _gasket_tab_leak_witness_check(
        gasket_tab_leak_witnesses
    )
    dry_bay_ingress_audit_rects = _dry_bay_ingress_audit_rectangles(
        dry_bay_envelope=dry_bay_envelope,
        side_gas_service_interfaces=side_gas_service_interfaces,
        sample_relief_leak_witnesses=sample_relief_leak_witnesses,
        gasket_tab_leak_witnesses=gasket_tab_leak_witnesses,
    )
    dry_bay_ingress_audit_check = _dry_bay_ingress_audit_check(
        dry_bay_ingress_audit_rects
    )
    dry_bay_obstruction_review = _dry_bay_obstruction_review_rectangles(
        dry_bay_envelope=dry_bay_envelope,
        params=params,
    )
    assembly_debris_review = _assembly_debris_review_rectangles(
        dry_bay_envelope=dry_bay_envelope,
        wet_dry_failure_paths=wet_dry_failure_paths,
        params=params,
    )
    sensor_position_layout = {
        **position_layout,
        "lid_port_positions": lid_port_positions,
        "side_gas_service_interfaces": side_gas_service_interfaces,
    }
    gas_sensor_pcb_mounts = _gas_sensor_pcb_mounts_for_layout(
        sensor_position_layout,
        params=params,
        lid_top_z=lid_top_z,
    )
    gas_pcb_flow_cell_check = _gas_pcb_flow_cell_check_for_layout(
        gas_sensor_pcb_mounts,
    )
    unseated_gas_pcb_cartridges_review = (
        _unseated_gas_pcb_cartridge_review_rectangles(
            position_layout,
            gas_sensor_pcb_mounts=gas_sensor_pcb_mounts,
            params=params,
        )
    )
    missing_gas_pcb_cartridge_witnesses = _missing_gas_pcb_cartridge_witness_rectangles(
        gas_sensor_pcb_mounts=gas_sensor_pcb_mounts,
        params=params,
    )
    headspace_sht41_mounts = _headspace_sht41_mounts_for_layout(
        sensor_position_layout,
        params=params,
        lid_bottom_z=lid_bottom_z,
    )
    ir_sensor_mounts = _ir_sensor_mounts_for_layout(
        sensor_position_layout,
        params=params,
        base_top_z=base_top_z,
    )
    missing_local_sensor_witnesses = _missing_local_sensor_witness_rectangles(
        headspace_sht41_mounts=headspace_sht41_mounts,
        ir_sensor_mounts=ir_sensor_mounts,
        params=params,
    )
    ir_thermopile_fov_spot_check = _ir_thermopile_fov_spot_check(
        ir_sensor_mounts,
        params=params,
        plate_bottom_z=plate_bottom_z,
    )
    thermal_condensation_proxy_targets = (
        _thermal_condensation_proxy_targets_for_layout(
            position_layout,
            params=params,
            plate_bottom_z=plate_bottom_z,
            plate_top_z=plate_top_z,
            ir_sensor_mounts=ir_sensor_mounts,
            headspace_sht41_mounts=headspace_sht41_mounts,
            condensation_pocket_rects=condensation_pocket_rects,
        )
    )
    thermal_condensation_proxy_check = _thermal_condensation_proxy_check(
        thermal_condensation_proxy_targets
    )
    sensor_harness_layout = _sensor_harness_for_layout(
        sensor_position_layout,
        params=params,
        lid_bottom_z=lid_bottom_z,
        lid_top_z=lid_top_z,
        base_top_z=base_top_z,
        plate_bottom_z=plate_bottom_z,
        ir_sensor_mounts=ir_sensor_mounts,
        headspace_sht41_mounts=headspace_sht41_mounts,
        gas_sensor_pcb_mounts=gas_sensor_pcb_mounts,
    )
    missing_service_lead_witnesses = _missing_service_lead_witness_rectangles(
        gas_service_tubes=cots_gas_service_tubes,
        sensor_service_cable_pigtails=sensor_harness_layout.get(
            "sensor_service_cable_pigtails",
            [],
        ),
        params=params,
    )
    unmated_sensor_service_connector_review_rects = (
        _unmated_sensor_service_connector_review_rectangles(
            connectors=sensor_harness_layout.get(
                "sensor_service_connector_envelopes",
                [],
            ),
            params=params,
        )
    )
    sensor_connector_service_clearance_check = (
        _sensor_connector_service_clearance_check(
            sensor_harness_layout.get("sensor_service_connector_envelopes", [])
        )
    )
    sensor_service_cable_envelope_check = _sensor_service_cable_envelope_check(
        sensor_harness_layout.get("sensor_service_cable_envelopes", [])
    )
    electrical_connector_mating_state_check = _electrical_connector_mating_state_check(
        unmated_sensor_service_connector_review_rects,
        connectors=sensor_harness_layout.get("sensor_service_connector_envelopes", []),
        cable_envelopes=sensor_harness_layout.get("sensor_service_cable_envelopes", []),
    )
    sensor_installation_layout = _sensor_installation_for_layout(
        sensor_position_layout,
        params=params,
        gas_sensor_pcb_mounts=gas_sensor_pcb_mounts,
        headspace_sht41_mounts=headspace_sht41_mounts,
        ir_sensor_mounts=ir_sensor_mounts,
    )
    wedge_lock_rectangles = _wedge_lock_rectangles_for_layout(position_layout, params)
    latch_post_positions = _latch_post_positions_for_locks(wedge_lock_rectangles)
    latch_mechanics = _latch_mechanical_screens(
        position_layout,
        params=params,
        compression_stop_positions=compression_stop_positions,
        wedge_lock_rectangles=wedge_lock_rectangles,
    )
    gasket_compression_gap_gauge = _gasket_compression_gap_gauge_for_layout(
        position_layout,
        params=params,
        compression_budget=latch_mechanics["compression_budget"],
    )
    gasket_squeeze_out_of_range_review = (
        _gasket_squeeze_out_of_range_review_rectangles(
            position_layout,
            params=params,
            compression_stop_positions=compression_stop_positions,
            compression_budget=latch_mechanics["compression_budget"],
            base_top_z=base_top_z,
        )
    )
    latch_retention_span_check = _latch_retention_span_check(
        position_layout,
        params=params,
        compression_budget=latch_mechanics["compression_budget"],
        ramp_self_lock=latch_mechanics["ramp_self_lock"],
        post_stress_screen=latch_mechanics["post_stress_screen"],
        station_asymmetry=latch_mechanics["station_asymmetry"],
        wedge_lock_rectangles=wedge_lock_rectangles,
    )
    deck_pod_seating_repeatability_check = _deck_pod_seating_repeatability_check(
        position_layout,
        params=params,
        deck_engagement_feet=deck_engagement_feet,
        deck_pod_frame_keys=deck_pod_frame_keys,
        dry_bay_envelope=dry_bay_envelope,
    )
    deck_pose_repeatability_review = _deck_pose_repeatability_review_rectangles(
        deck_engagement_feet=deck_engagement_feet,
        deck_pod_repeatability_check=deck_pod_seating_repeatability_check,
        deck_plane_z=deck_plane_z,
        params=params,
    )
    observer_optical_stability_check = _observer_optical_stability_check(
        position_layout,
        params=params,
        dry_bay_apertures=dry_bay_apertures,
        observer_fiducial_focus_target_check=observer_fiducial_focus_target_check,
        thermal_condensation_proxy_check=thermal_condensation_proxy_check,
        dry_bay_ingress_audit_rects=dry_bay_ingress_audit_rects,
        wet_dry_failure_paths=wet_dry_failure_paths,
    )
    fail_closed_prerun_inspection_check = _fail_closed_prerun_inspection_check(
        position_layout,
        params=params,
        compression_budget=latch_mechanics["compression_budget"],
        gasket_gap_gauge=gasket_compression_gap_gauge,
        sensor_mount_summary={
            "gas_sensor_pcb_count": len(gas_sensor_pcb_mounts),
            "headspace_sht41_count": len(headspace_sht41_mounts),
            "ir_thermopile_count": len(ir_sensor_mounts),
        },
        deck_engagement_feet=deck_engagement_feet,
        service_lead_witnesses=missing_service_lead_witnesses,
        unseated_gas_pcb_cartridges_review=unseated_gas_pcb_cartridges_review,
        unseated_side_gas_tubes_review=unseated_side_gas_tubes_review,
        unmated_connector_review_rects=unmated_sensor_service_connector_review_rects,
    )
    printability_support_cleanup_check = _printability_support_cleanup_check(
        position_layout,
        params=params,
        side_gas_service_interfaces=side_gas_service_interfaces,
        wedge_lock_rectangles=wedge_lock_rectangles,
        wet_dry_failure_paths=wet_dry_failure_paths,
        dry_bay_ingress_audit_rects=dry_bay_ingress_audit_rects,
        gas_sensor_pcb_mounts=gas_sensor_pcb_mounts,
        headspace_sht41_mounts=headspace_sht41_mounts,
        ir_sensor_mounts=ir_sensor_mounts,
    )
    consumable_metrology_gauge = _consumable_metrology_gauge(
        position_layout,
        params=params,
    )
    material_cleaning_witness_coupons = _material_cleaning_witness_coupons_for_policy(
        position_layout,
        params=params,
    )
    material_cleaning_witness_coupon = _material_cleaning_witness_coupon(
        material_cleaning_witness_coupons,
    )
    plate_locator_rails = _plate_lateral_locator_rectangles(
        tile_origins=tile_origins,
        params=params,
        z0=plate_bottom_z,
    )
    missing_microplate_witnesses = _missing_microplate_witness_rectangles(
        tile_origins=tile_origins,
        params=params,
        plate_bottom_z=plate_bottom_z,
    )
    missing_septum_mat_witnesses = _missing_septum_mat_witness_rectangles(
        tile_origins=tile_origins,
        params=params,
        plate_top_z=plate_top_z,
    )
    missing_perimeter_gasket_witnesses = _missing_perimeter_gasket_witness_rectangles(
        skirt_bounds=skirt_bounds,
        params=params,
        base_top_z=base_top_z,
        gasket_bottom_z=plate_top_z,
    )
    assembly_state_witness_check = _assembly_state_witness_check(
        position_layout,
        params=params,
        lid_port_positions=lid_port_positions,
        wedge_lock_rectangles=wedge_lock_rectangles,
        missing_microplate_witnesses=missing_microplate_witnesses,
        missing_septum_mat_witnesses=missing_septum_mat_witnesses,
        missing_perimeter_gasket_witnesses=missing_perimeter_gasket_witnesses,
        missing_gas_pcb_cartridge_witnesses=missing_gas_pcb_cartridge_witnesses,
        unseated_gas_pcb_cartridges_review=unseated_gas_pcb_cartridges_review,
        missing_local_sensor_witnesses=missing_local_sensor_witnesses,
        missing_service_lead_witnesses=missing_service_lead_witnesses,
        unseated_side_gas_tubes_review=unseated_side_gas_tubes_review,
        lid_top_z=lid_top_z,
    )
    all_well_centers = [
        center
        for tile in tile_origins
        for center in _well_centers_for_tile(tile, params)
    ]
    well_cell_plane_check = _well_cell_plane_check(
        tile_origins=tile_origins,
        params=params,
        plate_top_z=plate_top_z,
    )
    well_xs = [center[0] for center in all_well_centers]
    well_ys = [center[1] for center in all_well_centers]
    # NOTE: if a front_end_* key is absent these fall back to carriage dims. The
    # height/focus fallbacks (to carriage_height_z / focus_stroke_z) would make
    # the swept-body vertical-budget closure partially self-reference its own
    # ceiling and re-weaken falsifiability, so the params file keeps all five
    # front_end_* keys present; the fallbacks are a safety net, not the live path.
    front_end_len = observer.get("front_end_length_x", observer["carriage_length_x"])
    front_end_wid = observer.get("front_end_width_y", observer["carriage_width_y"])
    front_end_h = observer.get("front_end_height_z", observer["carriage_height_z"])
    front_end_focus = observer.get("front_end_focus_stroke_z", observer["focus_stroke_z"])
    front_end_clearance = observer.get(
        "front_end_top_clearance_z",
        observer["carriage_top_clearance_z"],
    )
    front_end_swept_h = front_end_h + front_end_focus
    front_end_swept_top_z = -front_end_clearance
    front_end_swept_bottom_z = front_end_swept_top_z - front_end_swept_h
    tip_keepout_d = (
        access.get("tip_outer_diameter_at_septum", 1.8)
        + 2 * access.get("tip_radial_clearance_xy", 0.35)
    )
    puncture_bottom_z = (
        plate_top_z
        + mat["sheet_thickness_z"]
        - access.get("puncture_depth_below_mat_top_z", 2.5)
    )
    sensor_top_candidates = [
        float(mount["z"]) + float(mount["height_z"])
        for mount in (
            gas_sensor_pcb_mounts + headspace_sht41_mounts + ir_sensor_mounts
        )
    ]
    if sensor_top_candidates:
        assembly_top_z = max(assembly_top_z, max(sensor_top_candidates))
    puncture_top_z = assembly_top_z + access.get("approach_clearance_above_lid_z", 6.0)
    side_service_rects = [
        *[
            rect
            for interface in side_gas_service_interfaces
            for rect in interface.get("external_service_rects", [])
        ],
    ]
    electrical_service_rects = sensor_harness_layout.get(
        "sensor_service_cable_envelopes",
        [],
    )
    operating_service_rects = [*side_service_rects, *electrical_service_rects]
    operating_service_dress_check = _operating_service_dress_check(
        operating_service_rects,
        side_service_rects=side_service_rects,
        electrical_service_rects=electrical_service_rects,
        side_gas_adjacent_slot_clearance=side_gas_adjacent_slot_clearance,
    )
    row_tiling_service_clearance_check = _row_tiling_service_clearance_check(
        position_layout,
        adjacent_keepouts=adjacent_deck_slot_keepouts,
        operating_service_rects=operating_service_rects,
        side_gas_adjacent_slot_clearance=side_gas_adjacent_slot_clearance,
        deck_plane_z=deck_plane_z,
        assembly_top_z=assembly_top_z,
    )
    operating_service_top_z = max(
        (
            float(rect["z"]) + float(rect["height_z"])
            for rect in operating_service_rects
        ),
        default=assembly_top_z,
    )
    toolhead_len = access.get("ot2_toolhead_envelope_length_x", 135.0)
    toolhead_wid = access.get("ot2_toolhead_envelope_width_y", 95.0)
    toolhead_h = access.get("ot2_toolhead_envelope_height_z", 45.0)
    toolhead_overtravel_x = access.get("ot2_toolhead_envelope_overtravel_x", 8.0)
    toolhead_overtravel_y = access.get("ot2_toolhead_envelope_overtravel_y", 8.0)
    toolhead_assembly_clearance = access.get(
        "ot2_toolhead_bottom_clearance_above_assembly_z",
        8.0,
    )
    toolhead_service_clearance = access.get(
        "ot2_toolhead_service_clearance_z",
        2.0,
    )
    toolhead_bottom_z = max(
        assembly_top_z + toolhead_assembly_clearance,
        operating_service_top_z + toolhead_service_clearance,
        puncture_top_z + toolhead_service_clearance,
    )
    well_field_x0 = min(well_xs)
    well_field_x1 = max(well_xs)
    well_field_y0 = min(well_ys)
    well_field_y1 = max(well_ys)
    pipette_puncture_swept_path = {
        "diameter": round(tip_keepout_d, 3),
        "bottom_z": round(puncture_bottom_z, 3),
        "top_z": round(puncture_top_z, 3),
        "height_z": round(puncture_top_z - puncture_bottom_z, 3),
        "well_count": len(all_well_centers),
    }
    pipette_toolhead_swept_body = {
        "role": "ot2_pipette_toolhead_operating_clearance",
        "validation": "conservative_envelope_requires_physical_ot2_measurement",
        "x": round(well_field_x0 - toolhead_len / 2 - toolhead_overtravel_x, 3),
        "y": round(well_field_y0 - toolhead_wid / 2 - toolhead_overtravel_y, 3),
        "z": round(toolhead_bottom_z, 3),
        "length_x": round(
            (well_field_x1 - well_field_x0) + toolhead_len + 2 * toolhead_overtravel_x,
            3,
        ),
        "width_y": round(
            (well_field_y1 - well_field_y0) + toolhead_wid + 2 * toolhead_overtravel_y,
            3,
        ),
        "height_z": round(toolhead_h, 3),
        "covered_well_count": len(all_well_centers),
        "service_envelope_count": len(operating_service_rects),
        "assembly_clearance_z": round(toolhead_bottom_z - assembly_top_z, 3),
        "service_clearance_z": round(
            toolhead_bottom_z - operating_service_top_z,
            3,
        ),
        "tip_transition_gap_z": round(toolhead_bottom_z - puncture_top_z, 3),
        "operating_service_top_z": round(operating_service_top_z, 3),
    }
    misdressed_service_bundle_review = _misdressed_service_bundle_review_rectangles(
        tile_origins=tile_origins,
        params=params,
        pipette_toolhead_swept_body=pipette_toolhead_swept_body,
    )
    pipette_puncture_swept_path_check = _pipette_puncture_swept_path_check(
        pipette_puncture_swept_path,
        well_centers=all_well_centers,
        params=params,
    )
    pipette_toolhead_swept_body_check = _pipette_toolhead_swept_body_check(
        pipette_toolhead_swept_body,
        puncture_swept_path_check=pipette_puncture_swept_path_check,
        operating_service_dress_check=operating_service_dress_check,
    )
    observer_carriage_envelope_rect = {
        "x": round(carriage_x, 3),
        "y": round(carriage_y, 3),
        "z": round(carriage_z, 3),
        "length_x": observer["carriage_length_x"],
        "width_y": observer["carriage_width_y"],
        "height_z": observer["carriage_height_z"],
    }
    observer_service_raceway_envelope_rect = {
        "x": round(raceway_x, 3),
        "y": round(raceway_y, 3),
        "z": round(raceway_z, 3),
        "length_x": round(raceway_length_x, 3),
        "width_y": round(raceway_width_y, 3),
        "height_z": observer["service_raceway_height_z"],
    }
    observer_front_end_swept_body_rect = {
        "x": round(min(well_xs) - front_end_len / 2, 3),
        "y": round(min(well_ys) - front_end_wid / 2, 3),
        "z": round(front_end_swept_bottom_z, 3),
        "length_x": round(max(well_xs) - min(well_xs) + front_end_len, 3),
        "width_y": round(max(well_ys) - min(well_ys) + front_end_wid, 3),
        "height_z": round(front_end_swept_h, 3),
    }
    carriage_traverse = _observer_carriage_traverse(
        row_axis=row_axis,
        well_xs=well_xs,
        well_ys=well_ys,
        gantry_truck_traverse_extent=observer.get(
            "gantry_truck_traverse_extent",
            observer["carriage_width_y"],
        ),
        front_end_length_x=front_end_len,
        front_end_width_y=front_end_wid,
        front_end_scan_axis_footprint=observer.get(
            "front_end_scan_axis_footprint",
            front_end_len,
        ),
        swept_z=front_end_swept_bottom_z,
        swept_height_z=front_end_swept_h,
        dry_bay_envelope=dry_bay_envelope,
        deck_feet=deck_engagement_feet,
        adjacent_keepouts=adjacent_deck_slot_keepouts,
    )
    observer_carriage_envelope_check = _observer_carriage_envelope_check(
        observer_carriage_envelope_rect,
        dry_bay_envelope=dry_bay_envelope,
        carriage_traverse=carriage_traverse,
    )
    observer_service_raceway_envelope_check = _observer_service_raceway_envelope_check(
        observer_service_raceway_envelope_rect,
        dry_bay_envelope=dry_bay_envelope,
        service_bend_radius=observer["service_bend_radius"],
    )
    # OC-A14: the raceway X can be clamped by the coupon length. The live footprint now
    # carries enough X end margin for the raceway near edge to sit at/beyond the boundary
    # rail far edge. Keep this as a diagnostic so future footprint/raceway changes cannot
    # silently reintroduce the single-row clamp intrusion.
    if row_axis == "y":
        _rail_far_x = (
            dry_ref_x1
            + bay["boundary_rail_clearance_y"]
            + bay["boundary_rail_width_y"]
        )
        observer_service_raceway_envelope_check["raceway_clears_boundary_rail"] = bool(
            float(observer_service_raceway_envelope_check["x"])
            >= _rail_far_x - _TRAVERSE_FIT_TOLERANCE_MM
        )
    else:
        # row-axis "x" runs the raceway along Y; the rail relation differs and is not
        # assessed here (live layout is axis "y").
        observer_service_raceway_envelope_check["raceway_clears_boundary_rail"] = None
    observer_front_end_swept_body_check = _observer_front_end_swept_body_check(
        observer_front_end_swept_body_rect,
        dry_bay_envelope=dry_bay_envelope,
        covered_well_count=len(all_well_centers),
        front_end_length_x=front_end_len,
        front_end_width_y=front_end_wid,
        front_end_height_z=front_end_h,
        front_end_focus_stroke_z=front_end_focus,
        front_end_top_clearance_z=front_end_clearance,
        front_end_service_margin_z=observer.get("front_end_service_margin_z", 0.0),
        front_end_barrel_diameter=observer.get(
            "front_end_barrel_diameter",
            bay["objective_keepout_diameter"],
        ),
        scan_corridor_footprint_max=observer.get(
            "scan_corridor_footprint_max",
            observer["front_end_scan_axis_footprint"],
        ),
        objective_keepout_diameter=bay["objective_keepout_diameter"],
        carriage_height_z=observer["carriage_height_z"],
    )
    observer_infinity_port_datum_check = _observer_infinity_port_datum_check(
        observer_front_end_swept_body_check,
        pd0_offset_from_objective_shoulder_z=observer[
            "infinity_port_pd0_offset_from_objective_shoulder_z"
        ],
        clear_aperture_diameter=observer["infinity_port_clear_aperture_diameter"],
        cage_standard_mm=observer["infinity_port_cage_standard_mm"],
        rms_thread_present=observer["infinity_port_rms_thread_present"],
        c_mount_present=observer["infinity_port_c_mount_present"],
        tube_lens_to_sensor_mm=observer["infinity_port_tube_lens_to_sensor_mm"],
        objective_keepout_diameter=bay["objective_keepout_diameter"],
    )
    observer_kinematic_split_check = _observer_kinematic_split_check(
        position_layout,
        params=params,
        observer_front_end_swept_body_check=observer_front_end_swept_body_check,
        observer_carriage_envelope_check=observer_carriage_envelope_check,
        observer_service_raceway_envelope_check=(
            observer_service_raceway_envelope_check
        ),
        dry_bay_envelope=dry_bay_envelope,
        observer_fiducial_focus_targets=observer_fiducial_focus_targets,
    )

    # OC-A11: propagate geometry overflow into optical-stability readiness. The optical
    # checkpoints are physical (Gate 6), but if the geometry itself overflows the dry
    # bay the optical baseline is moot -- a geometry overflow must NOT read as "only
    # physical evidence pending". Surface the geometry verdict and add a hard blocker
    # when any clearance fails, so the optical-stability check is fail-closed on
    # geometry it previously ignored.
    observer_geometry_clears = bool(
        observer_front_end_swept_body_check["front_end_body_fits_dry_bay"]
        and observer_front_end_swept_body_check["front_end_vertical_budget_closes"]
        and observer_front_end_swept_body_check["front_end_barrel_fits_keepout"]
        and observer_carriage_envelope_check["carriage_box_fits_dry_bay"]
        # clears_traverse (NOT traverse_fits_dry_bay) so a head that fits the bay
        # envelope but strikes a deck foot or enters the adjacent OT-2 slot still
        # blocks optical stability -- the collision class the kinematic split detects.
        and observer_carriage_envelope_check["carriage_traverse"]["clears_traverse"]
        and observer_service_raceway_envelope_check["raceway_geometry_clears"]
        and observer_fiducial_focus_target_check["fiducial_geometry_clears"]
    )
    observer_optical_stability_check = {
        **observer_optical_stability_check,
        "observer_geometry_clears": observer_geometry_clears,
        "blockers": list(observer_optical_stability_check["blockers"])
        if observer_geometry_clears
        else sorted(
            [
                *observer_optical_stability_check["blockers"],
                "geometry_overflow_blocks_optical_stability",
            ]
        ),
    }

    # D9 sequenced assembly/disassembly motion checks (flag-on validation tools).
    # Gated behind production_assembly.keyed_joints_enabled (default False): when
    # OFF these keys are NOT added, so the layout dict stays byte-identical to
    # pre-D9 (the production export tree + first_print snapshots are zero-diff).
    # These checks only READ existing geometry and add NO production body, NO
    # metal, and NOTHING that grips/lands on the CellVis plate.
    d9_motion_checks: dict[str, Any] = {}
    if bool(production.get("keyed_joints_enabled", False)):
        # NOTE: derive the split segments INLINE from tile_origins — do NOT call
        # row_coupon_production_y_split_plan() here, since that re-enters
        # row_coupon_layout() and would recurse infinitely through this gated
        # branch. _split_y_from_tile_origins is a pure function of tile_origins +
        # plate width, so it is safe to call.
        from aevum_cad.row_coupon import (
            _production_y_split_parts,
            _split_y_from_tile_origins,
        )

        d9_split_y = _split_y_from_tile_origins(tile_origins, params)
        d9_split_rows = tuple(
            {
                "source_part": part,
                "y_min": y_min,
                "y_max": y_max,
            }
            for part in _production_y_split_parts(params)
            for (y_min, y_max) in (
                (0.0, d9_split_y),
                (d9_split_y, round(width, 3)),
            )
        )
        d9_motion_checks = {
            "split_segment_swept_removal_check": _split_segment_swept_removal_check(
                d9_split_rows,
                split_y=d9_split_y,
            ),
            "trapped_plate_lift_check": _trapped_plate_lift_check(
                plate_locator_rails,
                tile_origins=tile_origins,
                plate_len=plate_len,
                plate_wid=plate_wid,
                plate_bottom_z=plate_bottom_z,
            ),
            "harness_seam_routing_check": _harness_seam_routing_check(
                sensor_harness_layout.get("sensor_service_cable_envelopes", []),
                split_y=d9_split_y,
            ),
        }

    return {
        **d9_motion_checks,
        "row_axis": row_axis,
        "length_x": round(length, 3),
        "width_y": round(width, 3),
        "tile_pitch_x": round(tile_pitch_x, 3),
        "tile_pitch_y": round(tile_pitch_y, 3),
        "tile_origins": tile_origins,
        "dry_bay_envelope": dry_bay_envelope,
        "dry_bay_envelope_check": dry_bay_envelope_check,
        "dry_bay_boundary_check": dry_bay_boundary_check,
        "dry_bay_apertures": dry_bay_apertures,
        "observer_fiducial_focus_targets": observer_fiducial_focus_targets,
        "observer_fiducial_focus_target_check": (
            observer_fiducial_focus_target_check
        ),
        "wet_dry_failure_paths": wet_dry_failure_paths,
        "wet_dry_failure_path_check": wet_dry_failure_path_check,
        "condensation_pocket_rects": condensation_pocket_rects,
        "thermal_condensation_proxy_targets": thermal_condensation_proxy_targets,
        "thermal_condensation_proxy_check": thermal_condensation_proxy_check,
        "dry_bay_ingress_audit_rects": dry_bay_ingress_audit_rects,
        "observer_carriage_envelope_check": observer_carriage_envelope_check,
        "observer_service_raceway_envelope_check": (
            observer_service_raceway_envelope_check
        ),
        "observer_front_end_swept_body_check": observer_front_end_swept_body_check,
        "observer_infinity_port_datum_check": observer_infinity_port_datum_check,
        "deck_plane_z": deck_plane_z,
        "deck_slot_footprint_check": deck_slot_footprint_check,
        "deck_frame_keepout_check": deck_frame_keepout_check,
        "deck_engagement_feet": deck_engagement_feet,
        "deck_module_unseated_review": deck_module_unseated_review,
        "deck_pose_repeatability_review": deck_pose_repeatability_review,
        "deck_pod_frame_keys": deck_pod_frame_keys,
        "adjacent_deck_slot_keepouts": adjacent_deck_slot_keepouts,
        "adjacent_deck_slot_keepout_check": adjacent_deck_slot_keepout_check,
        "adjacent_slot_service_collision_review": (
            adjacent_slot_service_collision_review
        ),
        "side_gas_adjacent_slot_clearance": side_gas_adjacent_slot_clearance,
        "plate_locator_rails": plate_locator_rails,
        "missing_microplate_witnesses": missing_microplate_witnesses,
        "missing_septum_mat_witnesses": missing_septum_mat_witnesses,
        "missing_perimeter_gasket_witnesses": missing_perimeter_gasket_witnesses,
        "compression_stop_positions": compression_stop_positions,
        "lid_port_positions": [
            {
                "name": port["name"],
                "role": port["role"],
                "x": round(float(port["x"]), 3),
                "y": round(float(port["y"]), 3),
                "boss_diameter": float(port["boss_diameter"]),
                "hole_diameter": float(port["hole_diameter"]),
                "boss_height_z": float(port["boss_height_z"]),
                "cap_plug_diameter": round(float(port["cap_plug_diameter"]), 3),
                "cap_flange_diameter": round(float(port["cap_flange_diameter"]), 3),
                "cap_seal_lip_inner_diameter": round(
                    float(port["cap_seal_lip_inner_diameter"]),
                    3,
                ),
                "cap_seal_lip_outer_diameter": round(
                    float(port["cap_seal_lip_outer_diameter"]),
                    3,
                ),
                "cap_seal_lip_height_z": round(float(port["cap_seal_lip_height_z"]), 3),
                "cap_seal_lip_seat_depth_z": round(
                    float(port["cap_seal_lip_seat_depth_z"]),
                    3,
                ),
                "cap_seal_lip_nominal_compression_z": round(
                    float(port["cap_seal_lip_nominal_compression_z"]),
                    3,
                ),
                "cap_seal_lip_role": port["cap_seal_lip_role"],
            }
            for port in lid_port_positions
        ],
        "sample_relief_leak_witnesses": sample_relief_leak_witnesses,
        "sample_relief_leak_witness_check": sample_relief_leak_witness_check,
        "gasket_tab_leak_witnesses": gasket_tab_leak_witnesses,
        "gasket_tab_leak_witness_check": gasket_tab_leak_witness_check,
        "side_gas_service_interfaces": side_gas_service_interfaces,
        "side_gas_tube_envelopes": side_gas_tube_envelopes,
        "side_gas_tube_envelope_check": side_gas_tube_envelope_check,
        "side_gas_leak_witness_check": side_gas_leak_witness_check,
        "cots_gas_service_tubes": cots_gas_service_tubes,
        "unseated_side_gas_tubes_review": unseated_side_gas_tubes_review,
        "operating_service_dress_envelopes": operating_service_rects,
        "operating_service_dress_check": operating_service_dress_check,
        "misdressed_service_bundle_review": misdressed_service_bundle_review,
        "row_tiling_service_clearance_check": row_tiling_service_clearance_check,
        "dry_bay_ingress_audit_check": dry_bay_ingress_audit_check,
        "dry_bay_obstruction_review": dry_bay_obstruction_review,
        "assembly_debris_review": assembly_debris_review,
        "port_service_review_states": _port_service_review_state_metadata(),
        "gas_sensor_pcb_mounts": gas_sensor_pcb_mounts,
        "gas_pcb_flow_cell_check": gas_pcb_flow_cell_check,
        "missing_gas_pcb_cartridge_witnesses": missing_gas_pcb_cartridge_witnesses,
        "unseated_gas_pcb_cartridges_review": unseated_gas_pcb_cartridges_review,
        "missing_local_sensor_witnesses": missing_local_sensor_witnesses,
        "missing_service_lead_witnesses": missing_service_lead_witnesses,
        "unmated_sensor_service_connector_review_rects": (
            unmated_sensor_service_connector_review_rects
        ),
        "sensor_connector_service_clearance_check": (
            sensor_connector_service_clearance_check
        ),
        "sensor_service_cable_envelope_check": sensor_service_cable_envelope_check,
        "electrical_connector_mating_state_check": electrical_connector_mating_state_check,
        "headspace_sht41_mounts": headspace_sht41_mounts,
        "ir_sensor_mounts": ir_sensor_mounts,
        "ir_thermopile_fov_spot_check": ir_thermopile_fov_spot_check,
        **sensor_harness_layout,
        **sensor_installation_layout,
        "sensor_mount_summary": {
            "gas_sensor_pcb_count": len(gas_sensor_pcb_mounts),
            "headspace_sht41_count": len(headspace_sht41_mounts),
            "ir_thermopile_count": len(ir_sensor_mounts),
            "row_module_retention": "screwless_printed_features",
        },
        "wedge_lock_rectangles": wedge_lock_rectangles,
        "latch_post_positions": latch_post_positions,
        "latch_compression_budget": latch_mechanics["compression_budget"],
        "gasket_compression_gap_gauge": gasket_compression_gap_gauge,
        "gasket_squeeze_out_of_range_review": gasket_squeeze_out_of_range_review,
        "deck_pod_seating_repeatability_check": deck_pod_seating_repeatability_check,
        "latch_retention_span_check": latch_retention_span_check,
        "observer_optical_stability_check": observer_optical_stability_check,
        "observer_kinematic_split_check": observer_kinematic_split_check,
        "assembly_state_witness_check": assembly_state_witness_check,
        "fail_closed_prerun_inspection_check": fail_closed_prerun_inspection_check,
        "printability_support_cleanup_check": printability_support_cleanup_check,
        "consumable_metrology_gauge": consumable_metrology_gauge,
        "material_cleaning_witness_coupons": material_cleaning_witness_coupons,
        "material_cleaning_witness_coupon": material_cleaning_witness_coupon,
        "latch_ramp_self_lock": latch_mechanics["ramp_self_lock"],
        "latch_post_stress_screen": latch_mechanics["post_stress_screen"],
        "latch_station_asymmetry": latch_mechanics["station_asymmetry"],
        "base_top_z": base_top_z,
        "plate_bottom_z": plate_bottom_z,
        "plate_top_z": plate_top_z,
        "gasket_bottom_z": plate_top_z,
        "gasket_top_z": lid_bottom_z,
        "lid_bottom_z": lid_bottom_z,
        "lid_top_z": lid_top_z,
        "headspace_check_top_z": headspace_check_top_z,
        "wet_chamber_skirt": skirt_bounds,
        "headspace_barrier_check": headspace_barrier_check,
        "headspace_volume_check": headspace_volume_check,
        "well_cell_plane_check": well_cell_plane_check,
        "pipette_puncture_swept_path": pipette_puncture_swept_path,
        "pipette_puncture_swept_path_check": pipette_puncture_swept_path_check,
        "pipette_toolhead_swept_body": pipette_toolhead_swept_body,
        "pipette_toolhead_swept_body_check": pipette_toolhead_swept_body_check,
        "latch_post_head_top_z": round(latch_post_head_top_z, 3),
        "port_cap_top_z": round(port_cap_top_z, 3),
        "assembly_top_z": assembly_top_z,
        "assembly_envelope_z": (
            assembly_top_z
            + deck["standoff_height_z"]
            + deck["slot_shoe_thickness_z"]
        ),
    }
