from __future__ import annotations
from typing import Any
import cadquery as cq


def _row_coupon_export_models(params: dict[str, Any]) -> dict[str, cq.Workplane]:
    from aevum_cad.row_coupon import (build_cots_gas_service_tubes, build_deck_pods, build_gas_pcb_interface_gaskets, build_gas_sensor_pcbs, build_headspace_sht41_microcarriers, build_ir_thermopile_face_gaskets, build_ir_thermopiles, build_lid_cover, build_lid_harness_cover, build_lid_manifold_shell, build_lid_sensor_harness, build_lid_sensor_service_cable_pigtails, build_lid_sensor_service_connectors, build_lower_gasket, build_lower_harness_cover, build_lower_sensor_harness, build_lower_sensor_service_cable_pigtail, build_lower_sensor_service_connector, build_microplates, build_plate_support_frame, build_printed_gas_pcb_keeper_doors, build_printed_lid_sensor_connector_shrouds, build_printed_lower_sensor_connector_shroud, build_printed_sample_relief_cap, build_printed_wedge_locks, build_septum_mat_inserts, build_upper_gasket, build_wet_chamber_frame)
    return {
        "deck_pods": build_deck_pods(params),
        "plate_support_frame": build_plate_support_frame(params),
        "ir_thermopiles": build_ir_thermopiles(params),
        "ir_thermopile_face_gaskets": build_ir_thermopile_face_gaskets(params),
        "lower_sensor_harness": build_lower_sensor_harness(params),
        "lower_harness_cover": build_lower_harness_cover(params),
        "lower_sensor_service_connector": build_lower_sensor_service_connector(params),
        "printed_lower_sensor_connector_shroud": build_printed_lower_sensor_connector_shroud(
            params
        ),
        "lower_sensor_service_cable_pigtail": build_lower_sensor_service_cable_pigtail(
            params
        ),
        "lower_gasket": build_lower_gasket(params),
        "wet_chamber_frame": build_wet_chamber_frame(params),
        "cots_microplates": build_microplates(params),
        "cots_septum_mats": build_septum_mat_inserts(params),
        "upper_gasket": build_upper_gasket(params),
        "lid_manifold_shell": build_lid_manifold_shell(params),
        "headspace_sht41_microcarriers": build_headspace_sht41_microcarriers(params),
        "lid_sensor_harness": build_lid_sensor_harness(params),
        "lid_harness_cover": build_lid_harness_cover(params),
        "lid_sensor_service_connectors": build_lid_sensor_service_connectors(params),
        "printed_lid_sensor_connector_shrouds": build_printed_lid_sensor_connector_shrouds(
            params
        ),
        "lid_sensor_service_cable_pigtails": build_lid_sensor_service_cable_pigtails(
            params
        ),
        "lid_cover": build_lid_cover(params),
        "cots_gas_service_tubes": build_cots_gas_service_tubes(params),
        "gas_pcb_interface_gaskets": build_gas_pcb_interface_gaskets(params),
        "printed_gas_pcb_keeper_doors": build_printed_gas_pcb_keeper_doors(params),
        "gas_sensor_pcbs": build_gas_sensor_pcbs(params),
        "printed_sample_relief_cap": build_printed_sample_relief_cap(params),
        "printed_wedge_locks": build_printed_wedge_locks(params),
    }


def build_row_coupon_assembly(params: dict[str, Any]) -> cq.Workplane:
    parts = list(build_row_coupon_installed_parts(params).values())
    assembly = parts[0]
    for part in parts[1:]:
        assembly = assembly.union(part)
    return assembly


def build_row_coupon_installed_parts(params: dict[str, Any]) -> dict[str, cq.Workplane]:
    from aevum_cad.row_coupon import (build_cots_gas_service_tubes, build_deck_pods, build_gas_pcb_interface_gaskets, build_gas_sensor_pcbs, build_headspace_sht41_microcarriers, build_ir_thermopile_face_gaskets, build_ir_thermopiles, build_lid_cover, build_lid_harness_cover, build_lid_manifold_shell, build_lid_sensor_harness, build_lid_sensor_service_cable_pigtails, build_lid_sensor_service_connectors, build_lower_gasket, build_lower_harness_cover, build_lower_sensor_harness, build_lower_sensor_service_cable_pigtail, build_lower_sensor_service_connector, build_microplates, build_plate_support_frame, build_printed_gas_pcb_keeper_doors, build_printed_lid_sensor_connector_shrouds, build_printed_lower_sensor_connector_shroud, build_printed_sample_relief_cap, build_printed_wedge_locks, build_septum_mat_inserts, build_upper_gasket, build_wet_chamber_frame)
    return {
        "deck_pods": build_deck_pods(params),
        "plate_support_frame": build_plate_support_frame(params),
        "ir_thermopiles": build_ir_thermopiles(params, assembly_position=True),
        "ir_thermopile_face_gaskets": build_ir_thermopile_face_gaskets(
            params,
            assembly_position=True,
        ),
        "lower_sensor_harness": build_lower_sensor_harness(params, assembly_position=True),
        "lower_harness_cover": build_lower_harness_cover(params, assembly_position=True),
        "lower_sensor_service_connector": build_lower_sensor_service_connector(
            params,
            assembly_position=True,
        ),
        "printed_lower_sensor_connector_shroud": build_printed_lower_sensor_connector_shroud(
            params,
            assembly_position=True,
        ),
        "lower_sensor_service_cable_pigtail": build_lower_sensor_service_cable_pigtail(
            params,
            assembly_position=True,
        ),
        "lower_gasket": build_lower_gasket(params, assembly_position=True),
        "wet_chamber_frame": build_wet_chamber_frame(params, assembly_position=True),
        "cots_microplates": build_microplates(params, assembly_position=True),
        "cots_septum_mats": build_septum_mat_inserts(params, assembly_position=True),
        "upper_gasket": build_upper_gasket(params, assembly_position=True),
        "lid_manifold_shell": build_lid_manifold_shell(params, assembly_position=True),
        "headspace_sht41_microcarriers": build_headspace_sht41_microcarriers(
            params,
            assembly_position=True,
        ),
        "lid_sensor_harness": build_lid_sensor_harness(params, assembly_position=True),
        "lid_harness_cover": build_lid_harness_cover(params, assembly_position=True),
        "lid_sensor_service_connectors": build_lid_sensor_service_connectors(
            params,
            assembly_position=True,
        ),
        "printed_lid_sensor_connector_shrouds": build_printed_lid_sensor_connector_shrouds(
            params,
            assembly_position=True,
        ),
        "lid_sensor_service_cable_pigtails": build_lid_sensor_service_cable_pigtails(
            params,
            assembly_position=True,
        ),
        "lid_cover": build_lid_cover(params, assembly_position=True),
        "cots_gas_service_tubes": build_cots_gas_service_tubes(
            params,
            assembly_position=True,
        ),
        "gas_pcb_interface_gaskets": build_gas_pcb_interface_gaskets(
            params,
            assembly_position=True,
        ),
        "printed_gas_pcb_keeper_doors": build_printed_gas_pcb_keeper_doors(
            params,
            assembly_position=True,
        ),
        "gas_sensor_pcbs": build_gas_sensor_pcbs(params, assembly_position=True),
        "printed_sample_relief_cap": build_printed_sample_relief_cap(
            params,
            assembly_position=True,
        ),
        "printed_wedge_locks": build_printed_wedge_locks(params, assembly_position=True),
    }


def build_row_coupon_multipart_assembly(params: dict[str, Any]) -> cq.Assembly:
    assembly = cq.Assembly(name=params["name"])
    for name, part in build_row_coupon_installed_parts(params).items():
        assembly.add(part, name=name)
    return assembly


def build_row_coupon_service_parts(
    params: dict[str, Any],
    *,
    mode: str = "installed",
) -> dict[str, cq.Workplane]:
    return build_row_coupon_service_parts_from_installed(
        params,
        installed_parts=build_row_coupon_installed_parts(params),
        mode=mode,
    )


def build_row_coupon_service_parts_from_installed(
    params: dict[str, Any],
    *,
    installed_parts: dict[str, cq.Workplane],
    mode: str = "installed",
) -> dict[str, cq.Workplane]:
    from aevum_cad.row_coupon import (ROW_COUPON_SERVICE_MODES, build_adjacent_slot_service_collision_review, build_assembly_debris_review, build_deck_module_unseated_review, build_deck_pose_repeatability_review, build_dry_bay_obstruction_review, build_flow_test_adapters, build_gasket_squeeze_out_of_range_review, build_latch_unseated_witnesses, build_misdressed_service_bundle_review, build_missing_gas_pcb_cartridge_witnesses, build_missing_local_sensor_witnesses, build_missing_microplate_witnesses, build_missing_perimeter_gasket_witnesses, build_missing_sample_relief_cap_witness, build_missing_septum_mat_witnesses, build_missing_service_lead_witnesses, build_sensor_installation_path_check, build_unmated_sensor_service_connectors_review, build_unseated_gas_pcb_cartridges_review, build_unseated_sample_relief_cap_review, build_unseated_side_gas_tubes_review, build_unseated_wedge_locks_review)
    parts = dict(installed_parts)
    if mode in {"installed", "bench_sealed"}:
        return parts

    production = params.get("production_assembly", {})
    spacing_z = production.get("exploded_spacing_z", 10.0)
    spacing_y = production.get("exploded_spacing_y", 16.0)
    names = list(parts)

    if mode == "sample_relief_flow_test":
        parts.pop("printed_sample_relief_cap")
        parts["sample_relief_flow_test_adapter"] = build_flow_test_adapters(
            params,
            assembly_position=True,
        )
        return parts

    if mode == "exploded":
        midpoint = (len(names) - 1) / 2
        return {
            name: part.translate((0, (idx - midpoint) * spacing_y, idx * spacing_z))
            for idx, (name, part) in enumerate(parts.items())
        }

    lifted = dict(parts)
    lid_stack = {
        "upper_gasket",
        "lid_manifold_shell",
        "headspace_sht41_microcarriers",
        "lid_cover",
        "lid_sensor_harness",
        "lid_harness_cover",
        "lid_sensor_service_connectors",
        "printed_lid_sensor_connector_shrouds",
        "lid_sensor_service_cable_pigtails",
        "gas_sensor_pcbs",
        "gas_pcb_interface_gaskets",
        "printed_gas_pcb_keeper_doors",
        "printed_sample_relief_cap",
        "printed_wedge_locks",
        "cots_gas_service_tubes",
    }
    if mode == "sensor_install":
        install = params.get("sensor_installation", {})
        lifted["gas_sensor_pcbs"] = lifted["gas_sensor_pcbs"].translate(
            (0, 0, install.get("gas_pcb_service_lift_z", 18.0))
        )
        lifted["headspace_sht41_microcarriers"] = lifted[
            "headspace_sht41_microcarriers"
        ].translate((install.get("sht41_service_offset_x", 18.0), 0, 0))
        lifted["ir_thermopiles"] = lifted["ir_thermopiles"].translate(
            (0, 0, -install.get("ir_service_drop_z", 14.0))
        )
        lifted["ir_thermopile_face_gaskets"] = lifted[
            "ir_thermopile_face_gaskets"
        ].translate((0, 0, -install.get("ir_service_drop_z", 14.0)))
        lifted["sensor_installation_path_check"] = build_sensor_installation_path_check(
            params,
            assembly_position=True,
        )
        return lifted

    if mode in {"lid_off", "mats_exposed"}:
        for name in lid_stack:
            lifted[name] = lifted[name].translate((0, spacing_y * 2, spacing_z * 2))
        return lifted

    if mode == "wet_frame_off":
        for name in lid_stack | {"wet_chamber_frame"}:
            lifted[name] = lifted[name].translate((0, spacing_y * 2, spacing_z * 2))
        return lifted

    if mode == "plates_removable":
        for name in lid_stack | {"wet_chamber_frame"}:
            lifted[name] = lifted[name].translate((0, spacing_y * 2, spacing_z * 2))
        for name in {"cots_microplates", "cots_septum_mats"}:
            lifted[name] = lifted[name].translate((0, 0, spacing_z * 2))
        return lifted

    if mode == "sample_relief_cap_missing":
        lifted.pop("printed_sample_relief_cap")
        lifted["missing_sample_relief_cap_witness"] = build_missing_sample_relief_cap_witness(
            params,
            assembly_position=True,
        )
        return lifted

    if mode == "sample_relief_cap_unseated":
        lifted.pop("printed_sample_relief_cap")
        lifted["unseated_sample_relief_cap_review"] = build_unseated_sample_relief_cap_review(
            params,
            assembly_position=True,
        )
        return lifted

    if mode == "deck_module_unseated":
        lift_z = production.get("deck_module_unseated_lift_z", 12.0)
        for name in list(lifted):
            lifted[name] = lifted[name].translate((0, 0, lift_z))
        lifted["deck_module_unseated_review"] = build_deck_module_unseated_review(
            params,
            assembly_position=True,
        )
        return lifted

    if mode == "deck_pose_repeatability_unproven":
        lifted["deck_pose_repeatability_review"] = (
            build_deck_pose_repeatability_review(
                params,
                assembly_position=True,
            )
        )
        return lifted

    if mode == "latches_unseated":
        lifted.pop("printed_wedge_locks")
        lifted["unseated_wedge_locks_review"] = build_unseated_wedge_locks_review(
            params,
            assembly_position=True,
        )
        lifted["latch_unseated_witnesses"] = build_latch_unseated_witnesses(
            params,
            assembly_position=True,
        )
        return lifted

    if mode == "septum_mats_missing":
        lifted.pop("cots_septum_mats")
        lifted["missing_septum_mat_witnesses"] = build_missing_septum_mat_witnesses(
            params,
            assembly_position=True,
        )
        return lifted

    if mode == "microplates_missing":
        lifted.pop("cots_microplates")
        lifted.pop("cots_septum_mats")
        lifted["missing_microplate_witnesses"] = build_missing_microplate_witnesses(
            params,
            assembly_position=True,
        )
        return lifted

    if mode == "perimeter_gaskets_missing":
        lifted.pop("lower_gasket")
        lifted.pop("upper_gasket")
        lifted["missing_perimeter_gasket_witnesses"] = (
            build_missing_perimeter_gasket_witnesses(
                params,
                assembly_position=True,
            )
        )
        return lifted

    if mode == "gas_pcbs_missing":
        lifted.pop("gas_sensor_pcbs")
        lifted.pop("gas_pcb_interface_gaskets")
        lifted["missing_gas_pcb_cartridge_witnesses"] = (
            build_missing_gas_pcb_cartridge_witnesses(
                params,
                assembly_position=True,
            )
        )
        return lifted

    if mode == "gas_pcb_cartridges_unseated":
        lifted.pop("gas_sensor_pcbs")
        lifted.pop("printed_gas_pcb_keeper_doors")
        lifted["unseated_gas_pcb_cartridges_review"] = (
            build_unseated_gas_pcb_cartridges_review(
                params,
                assembly_position=True,
            )
        )
        return lifted

    if mode == "local_sensors_missing":
        lifted.pop("headspace_sht41_microcarriers")
        lifted.pop("ir_thermopiles")
        lifted.pop("ir_thermopile_face_gaskets")
        lifted["missing_local_sensor_witnesses"] = build_missing_local_sensor_witnesses(
            params,
            assembly_position=True,
        )
        return lifted

    if mode == "service_leads_missing":
        lifted.pop("cots_gas_service_tubes")
        lifted.pop("lower_sensor_service_cable_pigtail")
        lifted.pop("lid_sensor_service_cable_pigtails")
        lifted["missing_service_lead_witnesses"] = build_missing_service_lead_witnesses(
            params,
            assembly_position=True,
        )
        return lifted

    if mode == "side_gas_tubes_unseated":
        lifted.pop("cots_gas_service_tubes")
        lifted["unseated_side_gas_tubes_review"] = (
            build_unseated_side_gas_tubes_review(
                params,
                assembly_position=True,
            )
        )
        return lifted

    if mode == "electrical_connectors_unmated":
        lifted.pop("lower_sensor_service_connector")
        lifted.pop("lid_sensor_service_connectors")
        lifted.pop("lower_sensor_service_cable_pigtail")
        lifted.pop("lid_sensor_service_cable_pigtails")
        lifted["unmated_sensor_service_connectors_review"] = (
            build_unmated_sensor_service_connectors_review(
                params,
                assembly_position=True,
            )
        )
        return lifted

    if mode == "service_dress_over_pipette_field":
        lifted.pop("cots_gas_service_tubes")
        lifted.pop("lower_sensor_service_cable_pigtail")
        lifted.pop("lid_sensor_service_cable_pigtails")
        lifted["misdressed_service_bundle_review"] = (
            build_misdressed_service_bundle_review(
                params,
                assembly_position=True,
            )
        )
        return lifted

    if mode == "service_dress_adjacent_slot_collision":
        lifted.pop("cots_gas_service_tubes")
        lifted.pop("lower_sensor_service_cable_pigtail")
        lifted.pop("lid_sensor_service_cable_pigtails")
        lifted["adjacent_slot_service_collision_review"] = (
            build_adjacent_slot_service_collision_review(
                params,
                assembly_position=True,
            )
        )
        return lifted

    if mode == "dry_bay_obstructed":
        lifted["dry_bay_obstruction_review"] = build_dry_bay_obstruction_review(
            params,
            assembly_position=True,
        )
        return lifted

    if mode == "assembly_debris_present":
        lifted["assembly_debris_review"] = build_assembly_debris_review(
            params,
            assembly_position=True,
        )
        return lifted

    if mode == "gasket_squeeze_out_of_range":
        lifted["gasket_squeeze_out_of_range_review"] = (
            build_gasket_squeeze_out_of_range_review(
                params,
                assembly_position=True,
            )
        )
        return lifted

    raise ValueError(
        "row coupon service mode must be one of: " + ", ".join(ROW_COUPON_SERVICE_MODES)
    )


def build_row_coupon_validation_parts(
    params: dict[str, Any],
) -> dict[str, cq.Workplane]:
    from aevum_cad.row_coupon import (build_adjacent_deck_slot_keepout_check, build_assembly_state_witness_check, build_consumable_metrology_gauge, build_deck_frame_keepout_check, build_deck_pod_seating_repeatability_check, build_deck_slot_footprint_check, build_dry_bay_boundary_check, build_dry_bay_envelope_check, build_dry_bay_ingress_audit_check, build_electrical_connector_mating_state_check, build_fail_closed_prerun_inspection_check, build_gas_pcb_flow_cell_check, build_gasket_compression_gap_gauge, build_gasket_tab_leak_witness_check, build_headspace_barrier_check, build_headspace_volume_check, build_ir_thermopile_fov_spot_check, build_latch_retention_span_check, build_material_cleaning_witness_coupon, build_observer_carriage_envelope_check, build_observer_fiducial_focus_target_check, build_observer_front_end_swept_body_check, build_observer_infinity_port_datum_check, build_observer_kinematic_split_check, build_observer_optical_stability_check, build_observer_service_raceway_envelope_check, build_operating_service_dress_check, build_pipette_puncture_swept_path_check, build_pipette_toolhead_swept_body_check, build_printability_support_cleanup_check, build_row_tiling_service_clearance_check, build_sample_relief_leak_witness_check, build_sensor_connector_service_clearance_check, build_sensor_installation_path_check, build_sensor_service_cable_envelope_check, build_side_gas_leak_witness_check, build_side_gas_tube_envelope_check, build_thermal_condensation_proxy_check, build_well_cell_plane_check, build_wet_dry_failure_path_check)
    return {
        "consumable_metrology_gauge": build_consumable_metrology_gauge(
            params,
            assembly_position=True,
        ),
        "deck_slot_footprint_check": build_deck_slot_footprint_check(
            params,
            assembly_position=True,
        ),
        "deck_frame_keepout_check": build_deck_frame_keepout_check(
            params,
            assembly_position=True,
        ),
        "deck_pod_seating_repeatability_check": (
            build_deck_pod_seating_repeatability_check(
                params,
                assembly_position=True,
            )
        ),
        "dry_bay_envelope_check": build_dry_bay_envelope_check(
            params,
            assembly_position=True,
        ),
        "dry_bay_boundary_check": build_dry_bay_boundary_check(
            params,
            assembly_position=True,
        ),
        "headspace_barrier_check": build_headspace_barrier_check(
            params,
            assembly_position=True,
        ),
        "headspace_volume_check": build_headspace_volume_check(
            params,
            assembly_position=True,
        ),
        "well_cell_plane_check": build_well_cell_plane_check(
            params,
            assembly_position=True,
        ),
        "ir_thermopile_fov_spot_check": build_ir_thermopile_fov_spot_check(
            params,
            assembly_position=True,
        ),
        "thermal_condensation_proxy_check": (
            build_thermal_condensation_proxy_check(
                params,
                assembly_position=True,
            )
        ),
        "pipette_puncture_swept_path_check": build_pipette_puncture_swept_path_check(
            params,
            assembly_position=True,
        ),
        "pipette_toolhead_swept_body_check": (
            build_pipette_toolhead_swept_body_check(
                params,
                assembly_position=True,
            )
        ),
        "observer_front_end_swept_body_check": build_observer_front_end_swept_body_check(
            params,
            assembly_position=True,
        ),
        "observer_infinity_port_datum_check": build_observer_infinity_port_datum_check(
            params,
            assembly_position=True,
        ),
        "observer_carriage_envelope_check": build_observer_carriage_envelope_check(
            params,
            assembly_position=True,
        ),
        "observer_service_raceway_envelope_check": (
            build_observer_service_raceway_envelope_check(
                params,
                assembly_position=True,
            )
        ),
        "observer_fiducial_focus_target_check": (
            build_observer_fiducial_focus_target_check(
                params,
                assembly_position=True,
            )
        ),
        "observer_optical_stability_check": build_observer_optical_stability_check(
            params,
            assembly_position=True,
        ),
        "observer_kinematic_split_check": build_observer_kinematic_split_check(
            params,
            assembly_position=True,
        ),
        "assembly_state_witness_check": build_assembly_state_witness_check(
            params,
            assembly_position=True,
        ),
        "gasket_compression_gap_gauge": build_gasket_compression_gap_gauge(
            params,
            assembly_position=True,
        ),
        "latch_retention_span_check": build_latch_retention_span_check(
            params,
            assembly_position=True,
        ),
        "fail_closed_prerun_inspection_check": (
            build_fail_closed_prerun_inspection_check(
                params,
                assembly_position=True,
            )
        ),
        "printability_support_cleanup_check": (
            build_printability_support_cleanup_check(
                params,
                assembly_position=True,
            )
        ),
        "material_cleaning_witness_coupon": (
            build_material_cleaning_witness_coupon(
                params,
                assembly_position=True,
            )
        ),
        "wet_dry_failure_path_check": build_wet_dry_failure_path_check(
            params,
            assembly_position=True,
        ),
        "sensor_connector_service_clearance_check": (
            build_sensor_connector_service_clearance_check(
                params,
                assembly_position=True,
            )
        ),
        "sensor_service_cable_envelope_check": (
            build_sensor_service_cable_envelope_check(
                params,
                assembly_position=True,
            )
        ),
        "electrical_connector_mating_state_check": (
            build_electrical_connector_mating_state_check(
                params,
                assembly_position=True,
            )
        ),
        "operating_service_dress_check": build_operating_service_dress_check(
            params,
            assembly_position=True,
        ),
        "row_tiling_service_clearance_check": (
            build_row_tiling_service_clearance_check(
                params,
                assembly_position=True,
            )
        ),
        "sensor_installation_path_check": build_sensor_installation_path_check(
            params,
            assembly_position=True,
        ),
        "gas_pcb_flow_cell_check": build_gas_pcb_flow_cell_check(
            params,
            assembly_position=True,
        ),
        "side_gas_tube_envelope_check": build_side_gas_tube_envelope_check(
            params,
            assembly_position=True,
        ),
        "side_gas_leak_witness_check": build_side_gas_leak_witness_check(
            params,
            assembly_position=True,
        ),
        "sample_relief_leak_witness_check": build_sample_relief_leak_witness_check(
            params,
            assembly_position=True,
        ),
        "gasket_tab_leak_witness_check": build_gasket_tab_leak_witness_check(
            params,
            assembly_position=True,
        ),
        "dry_bay_ingress_audit_check": build_dry_bay_ingress_audit_check(
            params,
            assembly_position=True,
        ),
        "adjacent_deck_slot_keepout_check": build_adjacent_deck_slot_keepout_check(
            params,
            assembly_position=True,
        ),
    }


def export_row_coupon(params: dict[str, Any], out_dir: str | Path) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    models = _row_coupon_export_models(params)
    paths: dict[str, Path] = {}
    for name, model in models.items():
        stl_path = out / f"{params['name']}_{name}.stl"
        step_path = out / f"{params['name']}_{name}.step"
        cq.exporters.export(model, str(stl_path))
        cq.exporters.export(model, str(step_path))
        paths[f"{name}_stl"] = stl_path
        paths[f"{name}_step"] = step_path

    assembly_step = out / f"{params['name']}_assembly.step"
    build_row_coupon_multipart_assembly(params).export(str(assembly_step))
    paths["assembly_step"] = assembly_step
    return paths


def export_row_coupon_validation_tools(
    params: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, Path]:
    from aevum_cad.row_coupon import (build_adjacent_deck_slot_keepout_check, build_assembly_state_witness_check, build_consumable_metrology_gauge, build_deck_frame_keepout_check, build_deck_pod_seating_repeatability_check, build_deck_slot_footprint_check, build_dry_bay_boundary_check, build_dry_bay_envelope_check, build_dry_bay_ingress_audit_check, build_electrical_connector_mating_state_check, build_fail_closed_prerun_inspection_check, build_gas_pcb_flow_cell_check, build_gasket_compression_gap_gauge, build_gasket_tab_leak_witness_check, build_headspace_barrier_check, build_headspace_volume_check, build_ir_thermopile_fov_spot_check, build_latch_mechanism_demo_parts, build_latch_retention_span_check, build_material_cleaning_witness_coupon, build_observer_carriage_envelope_check, build_observer_fiducial_focus_target_check, build_observer_front_end_swept_body_check, build_observer_infinity_port_datum_check, build_observer_kinematic_split_check, build_observer_optical_stability_check, build_observer_service_raceway_envelope_check, build_operating_service_dress_check, build_pipette_puncture_swept_path_check, build_pipette_toolhead_swept_body_check, build_printability_support_cleanup_check, build_row_tiling_service_clearance_check, build_sample_relief_leak_witness_check, build_sensor_connector_service_clearance_check, build_sensor_installation_path_check, build_sensor_service_cable_envelope_check, build_side_gas_leak_witness_check, build_side_gas_tube_envelope_check, build_thermal_condensation_proxy_check, build_well_cell_plane_check, build_wet_dry_failure_path_check)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    models = {
        "consumable_metrology_gauge": build_consumable_metrology_gauge(params),
        "deck_slot_footprint_check": build_deck_slot_footprint_check(
            params,
            assembly_position=True,
        ),
        "deck_frame_keepout_check": build_deck_frame_keepout_check(
            params,
            assembly_position=True,
        ),
        "deck_pod_seating_repeatability_check": (
            build_deck_pod_seating_repeatability_check(
                params,
                assembly_position=True,
            )
        ),
        "dry_bay_envelope_check": build_dry_bay_envelope_check(
            params,
            assembly_position=True,
        ),
        "dry_bay_boundary_check": build_dry_bay_boundary_check(
            params,
            assembly_position=True,
        ),
        "headspace_barrier_check": build_headspace_barrier_check(
            params,
            assembly_position=True,
        ),
        "headspace_volume_check": build_headspace_volume_check(
            params,
            assembly_position=True,
        ),
        "well_cell_plane_check": build_well_cell_plane_check(
            params,
            assembly_position=True,
        ),
        "ir_thermopile_fov_spot_check": build_ir_thermopile_fov_spot_check(
            params,
            assembly_position=True,
        ),
        "thermal_condensation_proxy_check": (
            build_thermal_condensation_proxy_check(
                params,
                assembly_position=True,
            )
        ),
        "pipette_puncture_swept_path_check": build_pipette_puncture_swept_path_check(
            params,
            assembly_position=True,
        ),
        "pipette_toolhead_swept_body_check": (
            build_pipette_toolhead_swept_body_check(
                params,
                assembly_position=True,
            )
        ),
        "observer_front_end_swept_body_check": build_observer_front_end_swept_body_check(
            params,
            assembly_position=True,
        ),
        "observer_infinity_port_datum_check": build_observer_infinity_port_datum_check(
            params,
            assembly_position=True,
        ),
        "observer_carriage_envelope_check": build_observer_carriage_envelope_check(
            params,
            assembly_position=True,
        ),
        "observer_service_raceway_envelope_check": (
            build_observer_service_raceway_envelope_check(
                params,
                assembly_position=True,
            )
        ),
        "observer_fiducial_focus_target_check": (
            build_observer_fiducial_focus_target_check(
                params,
                assembly_position=True,
            )
        ),
        "observer_optical_stability_check": build_observer_optical_stability_check(
            params,
            assembly_position=True,
        ),
        "observer_kinematic_split_check": build_observer_kinematic_split_check(
            params,
            assembly_position=True,
        ),
        "assembly_state_witness_check": build_assembly_state_witness_check(
            params,
            assembly_position=True,
        ),
        "gasket_compression_gap_gauge": build_gasket_compression_gap_gauge(
            params,
            assembly_position=True,
        ),
        "latch_retention_span_check": build_latch_retention_span_check(
            params,
            assembly_position=True,
        ),
        "fail_closed_prerun_inspection_check": (
            build_fail_closed_prerun_inspection_check(
                params,
                assembly_position=True,
            )
        ),
        "printability_support_cleanup_check": (
            build_printability_support_cleanup_check(
                params,
                assembly_position=True,
            )
        ),
        "material_cleaning_witness_coupon": (
            build_material_cleaning_witness_coupon(
                params,
                assembly_position=True,
            )
        ),
        "wet_dry_failure_path_check": build_wet_dry_failure_path_check(
            params,
            assembly_position=True,
        ),
        "sensor_installation_path_check": build_sensor_installation_path_check(
            params,
            assembly_position=True,
        ),
        "sensor_connector_service_clearance_check": (
            build_sensor_connector_service_clearance_check(
                params,
                assembly_position=True,
            )
        ),
        "sensor_service_cable_envelope_check": build_sensor_service_cable_envelope_check(
            params,
            assembly_position=True,
        ),
        "electrical_connector_mating_state_check": (
            build_electrical_connector_mating_state_check(
                params,
                assembly_position=True,
            )
        ),
        "operating_service_dress_check": build_operating_service_dress_check(
            params,
            assembly_position=True,
        ),
        "row_tiling_service_clearance_check": (
            build_row_tiling_service_clearance_check(
                params,
                assembly_position=True,
            )
        ),
        "gas_pcb_flow_cell_check": build_gas_pcb_flow_cell_check(
            params,
            assembly_position=True,
        ),
        "side_gas_tube_envelope_check": build_side_gas_tube_envelope_check(
            params,
            assembly_position=True,
        ),
        "side_gas_leak_witness_check": build_side_gas_leak_witness_check(
            params,
            assembly_position=True,
        ),
        "sample_relief_leak_witness_check": build_sample_relief_leak_witness_check(
            params,
            assembly_position=True,
        ),
        "gasket_tab_leak_witness_check": build_gasket_tab_leak_witness_check(
            params,
            assembly_position=True,
        ),
        "dry_bay_ingress_audit_check": build_dry_bay_ingress_audit_check(
            params,
            assembly_position=True,
        ),
        "adjacent_deck_slot_keepout_check": build_adjacent_deck_slot_keepout_check(
            params,
            assembly_position=True,
        ),
    }
    models.update(build_latch_mechanism_demo_parts(params))
    paths: dict[str, Path] = {}
    for name, model in models.items():
        stl_path = out / f"{params['name']}_validation_{name}.stl"
        step_path = out / f"{params['name']}_validation_{name}.step"
        cq.exporters.export(model, str(stl_path))
        cq.exporters.export(model, str(step_path))
        paths[f"{name}_stl"] = stl_path
        paths[f"{name}_step"] = step_path
    return paths
