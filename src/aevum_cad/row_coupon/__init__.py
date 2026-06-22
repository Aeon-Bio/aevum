from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import cadquery as cq
from .parts._geom_base import (
    _rounded_box,
    _perimeter_rails,
    _rectangle_intersects_circle,
    _axis_cylinder_envelope_rect,
    _rectangles_overlap_xy,
    _rectangles_bounding_extents,
    _harness_z_shift,
    _boxes_from_rectangles,
    _bodies_from_shape_targets,
    _axis_cylinder,
    _axis_tube,
)
from .parts._shared_tile import (
    _well_centers_for_tile,
    _septum_access_window_for_tile,
    _deck_slot_opening_for_tile,
    _lid_port_positions,
    _lid_port_spec,
)
from .layout import (
    row_coupon_layout,
    _compression_stop_positions,
    _compression_stop_positions_for_layout,
    _slot_centers,
)
from .manifest import row_coupon_part_manifest, _part_manifest_entry
from .parts.structural import (
    _add_deck_engagement_feet,
    _add_deck_slot_shoes,
    _add_latch_tension_posts,
    _add_lid_port_interface,
    _add_plate_lateral_locator_rails,
    _add_plate_support_lands,
    _add_pod_frame_keys,
    _add_wet_chamber_service_dividers,
    _condensation_pocket_rectangles_for_layout,
    _cut_condensation_pockets,
    _cut_deck_key_notch,
    _cut_locator_relief,
    _cut_plate_observation_recess,
    _cut_pod_frame_key_pockets,
    _cut_septum_lift_notch,
    _cut_septum_slit_reliefs,
    _cut_wet_chamber_divider_windows,
    _deck_engagement_foot_rectangles,
    _latch_post_positions_for_locks,
    _plate_lateral_locator_rectangles,
    _pod_frame_key_rectangles,
    _septum_access_window_length,
    _shared_chamber_bounds,
    _thermal_condensation_proxy_targets_for_layout,
    _well_grid_rectangle_for_tile,
    build_deck_pods,
    build_lid_cover,
    build_lid_manifold_shell,
    build_microplates,
    build_plate_support_frame,
    build_septum_mat_inserts,
    build_wet_chamber_frame,
    build_wet_chamber_skirt,
)
from .parts.sealing import (
    _add_gasket_service_tabs,
    _add_lid_cover_tongue,
    _cut_gasket_capture_groove,
    _cut_lid_cover_tongue_groove,
    _cut_rectangular_gas_interface_window,
    _gasket_compression_gap_gauge_for_layout,
    _gasket_squeeze_out_of_range_review_rectangles,
    _lid_cover_tongue_ring,
    build_gas_pcb_interface_gaskets,
    build_gasket_compression_gap_gauge,
    build_gasket_squeeze_out_of_range_review,
    build_ir_thermopile_face_gaskets,
    build_lid_gasket,
    build_lower_gasket,
    build_upper_gasket,
)
from .parts.latches import (
    _add_wedge_receiver_rails,
    _add_wedge_release_detent_and_witness_features,
    _assembly_state_witness_check,
    _build_wedge_lock_body,
    _cut_latch_post_slot,
    _latch_mechanical_screens,
    _latch_retention_span_check,
    _latch_station_asymmetry_screen,
    _production_latch_slide_length,
    _wedge_lock_overlaps_lid_port,
    _wedge_lock_rectangles,
    _wedge_lock_rectangles_for_layout,
    _wedge_profile_points,
    build_assembly_state_witness_check,
    build_latch_mechanism_demo_parts,
    build_latch_retention_span_check,
    build_latch_unseated_witnesses,
    build_printed_wedge_locks,
    build_unseated_wedge_locks_review,
)
from .parts.gas_pcb import (
    _add_gas_sensor_pcb_sockets,
    _add_side_gas_service_features,
    _cots_gas_service_tubes,
    _cut_vertical_mount_aperture,
    _gas_pcb_flow_cell_check_for_layout,
    _gas_pcb_sampling_interface,
    _gas_sensor_pcb_mounts_for_layout,
    _sensor_chip_marker_for_mount,
    _side_gas_adjacent_slot_clearance,
    _side_gas_leak_witness_check,
    _side_gas_service_interfaces,
    _side_gas_tube_envelope_check,
    _side_gas_tube_envelopes,
    _unseated_side_gas_tube_review_specs,
    build_cots_gas_service_tubes,
    build_gas_pcb_flow_cell_check,
    build_gas_sensor_pcbs,
    build_printed_gas_pcb_keeper_doors,
    build_side_gas_leak_witness_check,
    build_side_gas_tube_envelope_check,
    build_unseated_gas_pcb_cartridges_review,
)
from .parts.headspace_sensors import (
    _add_headspace_sht41_sockets,
    _add_ir_aperture_drip_collars,
    _add_ir_sensor_retention_lips,
    _cut_ir_sensor_pockets_and_apertures,
    _headspace_barrier_check,
    _headspace_sht41_mounts_for_layout,
    _headspace_volume_check,
    _ir_sensor_mounts_for_layout,
    _ir_thermopile_fov_spot_check,
    _target_kind_counts,
    _thermal_condensation_proxy_check,
    _well_cell_plane_check,
    build_headspace_barrier_check,
    build_headspace_sht41_microcarriers,
    build_headspace_volume_check,
    build_ir_thermopile_fov_spot_check,
    build_ir_thermopiles,
    build_thermal_condensation_proxy_check,
    build_well_cell_plane_check,
)
from .parts.harness import (
    _add_harness_snap_tabs,
    _build_printed_sensor_connector_shrouds,
    _build_sensor_service_connector_models,
    _cut_lid_sensor_harness_channels,
    _cut_lower_sensor_harness_channels,
    _electrical_connector_mating_state_check,
    _electrical_service_part_names,
    _harness_cover_from_rectangles,
    _installed_sensor_rect,
    _lid_sensor_harness_for_layout,
    _lower_ir_harness_for_layout,
    _review_rect,
    _sensor_connector_service_clearance_check,
    _sensor_harness_for_layout,
    _sensor_installation_for_layout,
    _sensor_installation_path_rectangles,
    _sensor_prototype_test_gates,
    _sensor_service_cable_envelope_check,
    _sensor_service_connector_spec,
    _service_connector_dimensions,
    _unmated_sensor_service_connector_review_rectangles,
    build_electrical_connector_mating_state_check,
    build_lid_harness_cover,
    build_lid_sensor_harness,
    build_lid_sensor_service_cable_pigtails,
    build_lid_sensor_service_connectors,
    build_lower_harness_cover,
    build_lower_sensor_harness,
    build_lower_sensor_service_cable_pigtail,
    build_lower_sensor_service_connector,
    build_printed_lid_sensor_connector_shrouds,
    build_printed_lower_sensor_connector_shroud,
    build_sensor_connector_service_clearance_check,
    build_sensor_installation_path_check,
    build_sensor_service_cable_envelope_check,
    build_unmated_sensor_service_connectors_review,
)
from .parts.sample_relief import (
    _add_sample_relief_cap_review_flag,
    _add_sample_relief_leak_witness_features,
    _build_port_cap_body,
    _port_service_review_state_metadata,
    _sample_relief_leak_witness_check,
    _sample_relief_leak_witnesses_for_layout,
    build_flow_test_adapters,
    build_missing_sample_relief_cap_witness,
    build_printed_sample_relief_cap,
    build_sample_relief_leak_witness_check,
    build_unseated_sample_relief_cap_review,
)
from .parts.observer import (
    _cut_observer_fiducials,
    _dry_bay_containment,
    _observer_body_rect,
    _observer_box_cad_value,
    _observer_carriage_envelope_check,
    _observer_carriage_traverse,
    _observer_fiducial_focus_target_check,
    _observer_fiducial_focus_target_rectangles,
    _observer_front_end_swept_body_check,
    _observer_infinity_port_datum_check,
    _observer_kinematic_split_check,
    _observer_optical_stability_check,
    _observer_service_raceway_envelope_check,
    build_observer_carriage_envelope_check,
    build_observer_fiducial_focus_target_check,
    build_observer_front_end_swept_body_check,
    build_observer_infinity_port_datum_check,
    build_observer_kinematic_split_check,
    build_observer_optical_stability_check,
    build_observer_service_raceway_envelope_check,
)
from .parts.dry_bay import (
    _add_dry_bay_aperture_thresholds,
    _cut_dry_bay,
    _cut_wet_dry_witness_gutters,
    _dry_bay_aperture_rectangles,
    _dry_bay_boundary_check,
    _dry_bay_envelope_check,
    _dry_bay_ingress_audit_check,
    _dry_bay_ingress_audit_rectangles,
    _dry_bay_obstruction_review_rectangles,
    _wet_dry_failure_path_check,
    _wet_dry_failure_path_geometry,
    build_dry_bay_boundary_check,
    build_dry_bay_envelope_check,
    build_dry_bay_ingress_audit_check,
    build_dry_bay_obstruction_review,
    build_wet_dry_failure_path_check,
)
from .parts.deck_service_reviews import (
    _adjacent_deck_slot_keepout_check,
    _adjacent_deck_slot_keepout_rectangles,
    _adjacent_slot_service_collision_review_rectangles,
    _assembly_debris_review_rectangles,
    _deck_frame_keepout_check,
    _deck_module_unseated_review_rectangles,
    _deck_pod_seating_repeatability_check,
    _deck_pose_repeatability_review_rectangles,
    _deck_slot_footprint_check,
    _deck_slot_footprint_rectangles,
    _misdressed_service_bundle_review_rectangles,
    build_adjacent_deck_slot_keepout_check,
    build_adjacent_slot_service_collision_review,
    build_assembly_debris_review,
    build_deck_frame_keepout_check,
    build_deck_module_unseated_review,
    build_deck_pod_seating_repeatability_check,
    build_deck_pose_repeatability_review,
    build_deck_slot_footprint_check,
    build_misdressed_service_bundle_review,
)
from .parts.service_clearance import (
    _operating_service_dress_check,
    _pipette_puncture_swept_path_check,
    _pipette_toolhead_swept_body_check,
    _row_tiling_service_clearance_check,
    build_operating_service_dress_check,
    build_pipette_puncture_swept_path_check,
    build_pipette_toolhead_swept_body_check,
    build_row_tiling_service_clearance_check,
)
from .parts.witness_review_rects import (
    _missing_gas_pcb_cartridge_witness_rectangles,
    _missing_local_sensor_witness_rectangles,
    _missing_microplate_witness_rectangles,
    _missing_perimeter_gasket_witness_rectangles,
    _missing_septum_mat_witness_rectangles,
    _missing_service_lead_witness_rectangles,
    _unseated_gas_pcb_cartridge_review_rectangles,
    build_missing_gas_pcb_cartridge_witnesses,
    build_missing_local_sensor_witnesses,
    build_missing_microplate_witnesses,
    build_missing_perimeter_gasket_witnesses,
    build_missing_septum_mat_witnesses,
    build_missing_service_lead_witnesses,
    build_unseated_side_gas_tubes_review,
)

PORT_REVIEW_SERVICE_MODES = (
    "sample_relief_cap_missing",
    "sample_relief_cap_unseated",
    "deck_module_unseated",
    "deck_pose_repeatability_unproven",
    "latches_unseated",
    "septum_mats_missing",
    "microplates_missing",
    "perimeter_gaskets_missing",
    "gas_pcbs_missing",
    "gas_pcb_cartridges_unseated",
    "local_sensors_missing",
    "service_leads_missing",
    "side_gas_tubes_unseated",
    "electrical_connectors_unmated",
    "service_dress_over_pipette_field",
    "service_dress_adjacent_slot_collision",
    "dry_bay_obstructed",
    "assembly_debris_present",
    "gasket_squeeze_out_of_range",
)
ROW_COUPON_SERVICE_MODES = (
    "installed",
    "bench_sealed",
    "sample_relief_flow_test",
    "exploded",
    "lid_off",
    "sensor_install",
    "mats_exposed",
    "wet_frame_off",
    "plates_removable",
    *PORT_REVIEW_SERVICE_MODES,
)

ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS = (
    "deck_pods",
    "plate_support_frame",
    "lower_harness_cover",
    "wet_chamber_frame",
    "lid_manifold_shell",
    "lid_harness_cover",
    "lid_cover",
    "printed_gas_pcb_keeper_doors",
    "printed_wedge_locks",
)


























































































































































def build_row_coupon_installed_parts(params: dict[str, Any]) -> dict[str, cq.Workplane]:
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


def build_row_coupon_service_parts_from_installed(
    params: dict[str, Any],
    *,
    installed_parts: dict[str, cq.Workplane],
    mode: str = "installed",
) -> dict[str, cq.Workplane]:
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


















def build_gasket_tab_leak_witness_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["gasket_tab_leak_witness_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -layout["base_top_z"]
    return _boxes_from_rectangles(rects, z_shift=z_shift)




def build_row_coupon_validation_parts(
    params: dict[str, Any],
) -> dict[str, cq.Workplane]:
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


def _row_coupon_export_models(params: dict[str, Any]) -> dict[str, cq.Workplane]:
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


def _production_y_split_parts(params: dict[str, Any]) -> tuple[str, ...]:
    production = params.get("production_assembly", {})
    configured = production.get("first_print_y_split_parts")
    if configured is None:
        return ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS
    return tuple(str(part) for part in configured)


def _production_y_split_segments(params: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    layout = row_coupon_layout(params)
    if layout["row_axis"] != "y":
        raise ValueError("production Y splits require a row configured on the Y axis")
    production = params.get("production_assembly", {})
    segment_count = int(production.get("first_print_y_split_segment_count", 2))
    if segment_count != 2:
        raise ValueError("production Y split currently supports exactly two segments")
    tile_origins = sorted(layout["tile_origins"], key=lambda tile: float(tile["y"]))
    if len(tile_origins) < 2:
        raise ValueError("production Y split requires at least two plate tiles")
    split_after = len(tile_origins) // 2
    lower_tile = tile_origins[split_after - 1]
    upper_tile = tile_origins[split_after]
    split_y = round(
        (
            float(lower_tile["y"])
            + float(params["plate"]["width_y"])
            + float(upper_tile["y"])
        )
        / 2,
        3,
    )
    return (
        {
            "segment_index": 1,
            "segment_count": segment_count,
            "suffix": "y01_of_02",
            "y_min": 0.0,
            "y_max": split_y,
            "interface_zone": f"between_plate_{lower_tile['index']}_and_{upper_tile['index']}",
            "interface_role": "lower segment terminates at inter-plate service gap",
            "retention": (
                "existing deck keys, tongue/groove, snap covers, and wedge locks "
                "must retain this split segment without screws or glue"
            ),
        },
        {
            "segment_index": 2,
            "segment_count": segment_count,
            "suffix": "y02_of_02",
            "y_min": split_y,
            "y_max": float(layout["width_y"]),
            "interface_zone": f"between_plate_{lower_tile['index']}_and_{upper_tile['index']}",
            "interface_role": "upper segment starts at inter-plate service gap",
            "retention": (
                "existing deck keys, tongue/groove, snap covers, and wedge locks "
                "must retain this split segment without screws or glue"
            ),
        },
    )


def row_coupon_production_y_split_plan(
    params: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Return first-print production split rows for oversized printed bodies."""

    rows: list[dict[str, Any]] = []
    for part in _production_y_split_parts(params):
        for segment in _production_y_split_segments(params):
            rows.append(
                {
                    "name": f"{part}_{segment['suffix']}",
                    "source_part": part,
                    "segment_index": segment["segment_index"],
                    "segment_count": segment["segment_count"],
                    "y_min": segment["y_min"],
                    "y_max": segment["y_max"],
                    "interface_zone": segment["interface_zone"],
                    "interface_role": segment["interface_role"],
                    "retention": segment["retention"],
                    "sealing": (
                        "split lies in the inter-plate service gap; wet-frame, "
                        "lid-shell, and lid-cover split segments require Gate 4 "
                        "dye evidence before wet operation"
                    ),
                    "serviceability": (
                        "plate, septum, sensor, gas-PCB, gas-tube, and latch service "
                        "checks remain required on the assembled split stack"
                    ),
                    "required_evidence": (
                        "Gate 1 dimensions, Gate 2 dry assembly, Gate 4 wet/dry "
                        "witness, and selected-slicer bed-fit evidence before this "
                        "split artifact replaces the monolithic queue part"
                    ),
                }
            )
    return tuple(rows)


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


def build_row_coupon_production_y_split_parts(
    params: dict[str, Any],
) -> dict[str, cq.Workplane]:
    models = _row_coupon_export_models(params)
    split_parts: dict[str, cq.Workplane] = {}
    for row in row_coupon_production_y_split_plan(params):
        source_part = str(row["source_part"])
        if source_part not in models:
            raise ValueError(f"unknown production Y split source part: {source_part}")
        split_parts[str(row["name"])] = _clip_workplane_to_y_range(
            models[source_part],
            y_min=float(row["y_min"]),
            y_max=float(row["y_max"]),
        )
    return split_parts




def build_row_coupon_assembly(params: dict[str, Any]) -> cq.Workplane:
    parts = list(build_row_coupon_installed_parts(params).values())
    assembly = parts[0]
    for part in parts[1:]:
        assembly = assembly.union(part)
    return assembly


def build_row_coupon_multipart_assembly(params: dict[str, Any]) -> cq.Assembly:
    assembly = cq.Assembly(name=params["name"])
    for name, part in build_row_coupon_installed_parts(params).items():
        assembly.add(part, name=name)
    return assembly


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


def export_row_coupon_production_y_split_parts(
    params: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    for name, model in build_row_coupon_production_y_split_parts(params).items():
        stl_path = out / f"{params['name']}_{name}.stl"
        step_path = out / f"{params['name']}_{name}.step"
        cq.exporters.export(model, str(stl_path))
        cq.exporters.export(model, str(step_path))
        paths[f"{name}_stl"] = stl_path
        paths[f"{name}_step"] = step_path
    return paths


def export_row_coupon_validation_tools(
    params: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, Path]:
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


















































































_TRAVERSE_FIT_TOLERANCE_MM = 1.0e-6
# OC-A12: margins at or below this (but still positive) are flagged razor-thin so a
# sub-mm param drift consuming the budget is visible before it tips into overflow.
_RAZOR_THIN_MARGIN_WARN_MM = 0.5




























































































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






















