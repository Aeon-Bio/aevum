"""Cross-module FIRST_PRINT_* constants (extracted, behavior-preserving)."""

from __future__ import annotations


FIRST_PRINT_REQUIRED_VALIDATION_CHECKS = (
    "deck_slot_footprint_check",
    "deck_frame_keepout_check",
    "deck_pod_seating_repeatability_check",
    "adjacent_deck_slot_keepout_check",
    "pipette_puncture_swept_path_check",
    "pipette_toolhead_swept_body_check",
    "sensor_installation_path_check",
    "gas_pcb_flow_cell_check",
    "sensor_connector_service_clearance_check",
    "sensor_service_cable_envelope_check",
    "electrical_connector_mating_state_check",
    "operating_service_dress_check",
    "row_tiling_service_clearance_check",
    "side_gas_tube_envelope_check",
    "dry_bay_envelope_check",
    "dry_bay_boundary_check",
    "headspace_barrier_check",
    "headspace_volume_check",
    "wet_dry_failure_path_check",
    "side_gas_leak_witness_check",
    "sample_relief_leak_witness_check",
    "gasket_tab_leak_witness_check",
    "dry_bay_ingress_audit_check",
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
    "consumable_metrology_gauge",
    "printability_support_cleanup_check",
    "well_cell_plane_check",
    "ir_thermopile_fov_spot_check",
    "thermal_condensation_proxy_check",
)
FIRST_PRINT_OPTIONAL_VALIDATION_TOOLS: tuple[str, ...] = ()
FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM = 1.0
FIRST_PRINT_PHYSICAL_GATES = (
    "Gate 1 Print QC",
    "Gate 2 Dry Assembly Fit",
    "Gate 3 OT-2 Placement And No-Motion Clearance",
    "Gate 4 Passive Leak And Wet/Dry Witness",
    "Gate 5 Consumable And Puncture Link",
    "Gate 6 Sensor And Thermal Link",
)
FIRST_PRINT_ACTIVE_QUEUE_MODE_FIELD = "Active print queue mode"
FIRST_PRINT_ACTIVE_QUEUE_MODE_MONOLITHIC = "monolithic"
FIRST_PRINT_ACTIVE_QUEUE_MODE_SPLIT_Y = "split_y"
FIRST_PRINT_ACTIVE_QUEUE_MODE_VALUES = (
    FIRST_PRINT_ACTIVE_QUEUE_MODE_MONOLITHIC,
    FIRST_PRINT_ACTIVE_QUEUE_MODE_SPLIT_Y,
)
FIRST_PRINT_PREFLIGHT_LINK_FIELDS = (
    "Params file",
    "Print/procurement manifest",
    "Slicer queue",
    "Slicer setup worksheet",
    "Sliced output worksheet",
    "Gate 1 QC worksheet",
    "Gate 2 dry assembly worksheet",
    "Gate 3 placement worksheet",
    "Gate 4 wet/dry witness worksheet",
    "Gate 5 consumable/puncture worksheet",
    "Gate 6 sensor/thermal worksheet",
    "Install inventory worksheet",
    "Service state review worksheet",
)
FIRST_PRINT_SPLIT_PREFLIGHT_LINK_FIELDS = (
    "Split slicer queue",
    "Split sliced output worksheet",
    "Split Gate 1 QC worksheet",
)
FIRST_PRINT_PREFLIGHT_REQUIRED_SESSION_FIELDS = (
    FIRST_PRINT_ACTIVE_QUEUE_MODE_FIELD,
    "Printer / material / profile",
)
