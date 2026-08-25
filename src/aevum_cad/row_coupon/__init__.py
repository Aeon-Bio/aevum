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
    _deck_slot_datum,
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
    _add_lid_frame_keys,
    _cut_gasket_capture_groove,
    _cut_lid_cover_tongue_groove,
    _cut_lid_frame_key_pockets,
    _cut_rectangular_gas_interface_window,
    _gasket_compression_gap_gauge_for_layout,
    _gasket_squeeze_out_of_range_review_rectangles,
    _lid_cover_tongue_ring,
    _lid_frame_key_rectangles,
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
    _printed_wedge_lock_models,
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
    _keeper_door_body,
    _printed_gas_pcb_keeper_door_models,
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
    _harness_seam_routing_check,
    _operating_service_dress_check,
    _pipette_puncture_swept_path_check,
    _pipette_toolhead_swept_body_check,
    _row_tiling_service_clearance_check,
    _split_segment_swept_removal_check,
    _trapped_plate_lift_check,
    build_harness_seam_routing_check,
    build_operating_service_dress_check,
    build_pipette_puncture_swept_path_check,
    build_pipette_toolhead_swept_body_check,
    build_row_tiling_service_clearance_check,
    build_split_segment_swept_removal_check,
    build_trapped_plate_lift_check,
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
from .production_y_split import (
    _clip_workplane_to_y_range,
    _production_y_split_parts,
    _production_y_split_segments,
    _split_y_from_tile_origins,
    _two_module_joint_metadata,
    build_row_coupon_production_y_split_parts,
    export_row_coupon_production_y_split_parts,
    row_coupon_production_y_split_plan,
)
from .qc_gauges import (
    _add_gasket_tab_leak_witness_features,
    _consumable_metrology_gauge,
    _fail_closed_prerun_inspection_check,
    _gasket_tab_leak_witness_check,
    _gasket_tab_leak_witnesses_for_layout,
    _material_cleaning_witness_coupon,
    _material_cleaning_witness_coupons_for_policy,
    _printability_support_cleanup_check,
    build_consumable_metrology_gauge,
    build_fail_closed_prerun_inspection_check,
    build_gasket_tab_leak_witness_check,
    build_material_cleaning_witness_coupon,
    build_printability_support_cleanup_check,
)
from .assembly import (
    _row_coupon_export_models,
    build_row_coupon_assembly,
    build_row_coupon_installed_parts,
    build_row_coupon_multipart_assembly,
    build_row_coupon_service_parts,
    build_row_coupon_service_parts_from_installed,
    build_row_coupon_validation_parts,
    export_row_coupon,
    export_row_coupon_validation_tools,
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


























































































































































































































































































































































































_TRAVERSE_FIT_TOLERANCE_MM = 1.0e-6
# OC-A12: margins at or below this (but still positive) are flagged razor-thin so a
# sub-mm param drift consuming the budget is visible before it tips into overflow.
_RAZOR_THIN_MARGIN_WARN_MM = 0.5
