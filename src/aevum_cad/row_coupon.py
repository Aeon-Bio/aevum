from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import cadquery as cq

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


def _part_manifest_entry(
    *,
    role: str,
    fabrication_source: str,
    retention: str,
    visibility: str = "installed_operating",
) -> dict[str, str]:
    return {
        "role": role,
        "fabrication_source": fabrication_source,
        "retention": retention,
        "visibility": visibility,
    }


def row_coupon_part_manifest() -> dict[str, Any]:
    """Role/type manifest for visible row-coupon CAD parts and review geometry."""

    installed = {
        "deck_pods": _part_manifest_entry(
            role="OT-2 deck engagement, row standoff, and dry-bay Z envelope",
            fabrication_source="printed_polymer",
            retention="printed_deck_fit_no_glue",
        ),
        "plate_support_frame": _part_manifest_entry(
            role="plate datum, dry-bay apertures, lower sensor pockets, and lower seal land",
            fabrication_source="printed_polymer",
            retention="keyed_to_deck_pods_no_glue",
        ),
        "ir_thermopiles": _part_manifest_entry(
            role="plate-margin sample-plane temperature sensing",
            fabrication_source="cots_electronics",
            retention="printed_lip_no_screws_no_glue",
        ),
        "ir_thermopile_face_gaskets": _part_manifest_entry(
            role="dry-side seal around each IR thermopile aperture",
            fabrication_source="compressible_elastomer_or_printed_tpu",
            retention="captured_by_printed_lip_and_sensor_face_no_glue",
        ),
        "lower_sensor_harness": _part_manifest_entry(
            role="dry-side IR sensor wiring route inside covered lower channel",
            fabrication_source="electronics_assembly",
            retention="captured_under_printed_cover_no_glue",
        ),
        "lower_harness_cover": _part_manifest_entry(
            role="lower sensor harness protection and service retention",
            fabrication_source="printed_polymer",
            retention="printed_snap_cover_no_glue",
        ),
        "lower_sensor_service_connector": _part_manifest_entry(
            role="row-end lower sensor electrical service interface",
            fabrication_source="cots_electronics",
            retention="keyed_printed_shroud_no_glue",
        ),
        "printed_lower_sensor_connector_shroud": _part_manifest_entry(
            role="lower connector keying, strain relief, and service protection",
            fabrication_source="printed_polymer",
            retention="integral_printed_shroud_no_glue",
        ),
        "lower_sensor_service_cable_pigtail": _part_manifest_entry(
            role="installed lower sensor electrical service lead",
            fabrication_source="cots_cable_assembly",
            retention="connector_retained_service_lead_no_glue",
        ),
        "lower_gasket": _part_manifest_entry(
            role="lower wet-chamber perimeter seal between support frame and wet frame",
            fabrication_source="compressible_elastomer_or_printed_tpu",
            retention="captured_in_groove_and_compressed_no_glue",
        ),
        "wet_chamber_frame": _part_manifest_entry(
            role="shared wet headspace skirt, plate enclosure, and lower latch authority",
            fabrication_source="printed_polymer",
            retention="compressed_between_gaskets_by_printed_latches_no_glue",
        ),
        "cots_microplates": _part_manifest_entry(
            role="cell-culture consumable and well geometry for biology",
            fabrication_source="cots_consumable",
            retention="seated_in_printed_plate_lands_no_glue",
        ),
        "cots_septum_mats": _part_manifest_entry(
            role="replaceable pre-slit septum access and wet headspace closure",
            fabrication_source="cots_consumable",
            retention="seated_on_microplates_under_lid_stack_no_glue",
        ),
        "upper_gasket": _part_manifest_entry(
            role="upper wet-chamber perimeter seal between wet frame and lid shell",
            fabrication_source="compressible_elastomer_or_printed_tpu",
            retention="captured_in_groove_and_compressed_no_glue",
        ),
        "lid_manifold_shell": _part_manifest_entry(
            role="wet headspace roof, shared plenum relief, and headspace sensor sockets",
            fabrication_source="printed_polymer",
            retention="tongue_groove_to_lid_cover_and_latch_compression_no_glue",
        ),
        "headspace_sht41_microcarriers": _part_manifest_entry(
            role="per-plate wet-headspace humidity and temperature sensing",
            fabrication_source="electronics_microcarrier",
            retention="printed_microcarrier_keeper_no_screws_no_glue",
        ),
        "lid_sensor_harness": _part_manifest_entry(
            role="lid-side gas and headspace sensor wiring route under cover",
            fabrication_source="electronics_assembly",
            retention="captured_under_printed_cover_no_glue",
        ),
        "lid_harness_cover": _part_manifest_entry(
            role="lid sensor harness protection and service retention",
            fabrication_source="printed_polymer",
            retention="printed_snap_cover_no_glue",
        ),
        "lid_sensor_service_connectors": _part_manifest_entry(
            role="row-end lid sensor electrical service interfaces",
            fabrication_source="cots_electronics",
            retention="keyed_printed_shrouds_no_glue",
        ),
        "printed_lid_sensor_connector_shrouds": _part_manifest_entry(
            role="lid connector keying, strain relief, and service protection",
            fabrication_source="printed_polymer",
            retention="integral_printed_shrouds_no_glue",
        ),
        "lid_sensor_service_cable_pigtails": _part_manifest_entry(
            role="installed lid sensor electrical service leads",
            fabrication_source="cots_cable_assembly",
            retention="connector_retained_service_leads_no_glue",
        ),
        "lid_cover": _part_manifest_entry(
            role="side gas ducts, service fittings, leak routing, and latch receivers",
            fabrication_source="printed_polymer",
            retention="tongue_groove_and_printed_wedge_locks_no_glue",
        ),
        "cots_gas_service_tubes": _part_manifest_entry(
            role="installed side supply and return gas service tubing",
            fabrication_source="cots_flexible_tubing",
            retention="printed_barbed_fitting_and_strain_relief_no_glue",
        ),
        "gas_pcb_interface_gaskets": _part_manifest_entry(
            role="sealed low-dead-volume gas PCB duct sampling interface",
            fabrication_source="compressible_elastomer_or_printed_tpu",
            retention="compressed_by_printed_keeper_doors_no_glue",
        ),
        "printed_gas_pcb_keeper_doors": _part_manifest_entry(
            role="screwless gas sensor PCB cartridge retention and compression",
            fabrication_source="printed_polymer",
            retention="printed_keeper_door_no_screws_no_glue",
        ),
        "gas_sensor_pcbs": _part_manifest_entry(
            role="supply and return gas-state sensor electronics",
            fabrication_source="custom_or_cots_pcb_assembly",
            retention="printed_cartridge_keeper_no_screws_no_glue",
            visibility="installed_internal_electronics",
        ),
        "printed_sample_relief_cap": _part_manifest_entry(
            role="normally installed sample/relief port closure",
            fabrication_source="printed_polymer",
            retention="printed_annular_lip_in_lid_seat_no_screws_no_glue",
        ),
        "printed_wedge_locks": _part_manifest_entry(
            role="fastener-free lid/wet-frame/gasket compression locks",
            fabrication_source="printed_polymer",
            retention="removable_printed_wedges_no_screws_no_glue",
        ),
    }
    validation = {
        "consumable_metrology_gauge": "physical gauge for plate and septum mat fit",
        "printability_support_cleanup_check": (
            "print support cleanup and first-print feature integrity checklist"
        ),
        "deck_slot_footprint_check": "OT-2 slot opening footprint validation",
        "deck_frame_keepout_check": "OT-2 deck frame rib keepout validation",
        "deck_pod_seating_repeatability_check": (
            "deck pod seating, release, wear, and no-rock evidence blocker"
        ),
        "dry_bay_envelope_check": "reserved dry observer bay volume",
        "dry_bay_boundary_check": "dry bay side boundary rail clearance",
        "headspace_barrier_check": "shared wet chamber barrier perimeter",
        "headspace_volume_check": "shared wet headspace controlled volume",
        "well_cell_plane_check": "published CellVis cell-plane target disks",
        "ir_thermopile_fov_spot_check": "IR thermopile plate-margin FOV spots",
        "thermal_condensation_proxy_check": (
            "plate-center, IR, SHT41, and condensation pocket proxy map"
        ),
        "pipette_puncture_swept_path_check": "tip puncture path through every septum",
        "pipette_toolhead_swept_body_check": "larger OT-2 toolhead clearance envelope",
        "observer_front_end_swept_body_check": "compact dry observer front-end swept volume",
        "observer_infinity_port_datum_check": (
            "SMIS infinity-port PD-0 datum and optical standard validation"
        ),
        "observer_carriage_envelope_check": "dry observer carriage reserved volume",
        "observer_service_raceway_envelope_check": "dry observer service loop raceway volume",
        "observer_fiducial_focus_target_check": (
            "observer underside fiducial and focus target pattern"
        ),
        "observer_optical_stability_check": (
            "observer optical performance evidence blocker checklist"
        ),
        "observer_kinematic_split_check": (
            "observer front-end carriage and service-loop split checklist"
        ),
        "assembly_state_witness_check": (
            "missing or unseated operating-state witness footprints"
        ),
        "gasket_compression_gap_gauge": (
            "printable min/target/max gasket squeeze reference blades"
        ),
        "latch_retention_span_check": (
            "dry latch detent retention and omitted-station span evidence blocker"
        ),
        "fail_closed_prerun_inspection_check": (
            "pre-run blocker checklist tying negative states to inspection evidence"
        ),
        "material_cleaning_witness_coupon": (
            "same-material exposure and cleaning witness coupon set"
        ),
        "wet_dry_failure_path_check": "aperture-local wet/dry gutter routing",
        "sensor_connector_service_clearance_check": "connector service clearance",
        "sensor_installation_path_check": "sensor install and removal motion envelopes",
        "sensor_service_cable_envelope_check": "electrical cable bend and egress space",
        "electrical_connector_mating_state_check": (
            "mated and visibly unmated electrical connector state check"
        ),
        "operating_service_dress_check": (
            "combined normal-operation gas and electrical service dress envelope"
        ),
        "row_tiling_service_clearance_check": (
            "composite row footprint, neighbor-slot, and service-dress clearance review"
        ),
        "gas_pcb_flow_cell_check": "gas PCB low-dead-volume sampling cell",
        "side_gas_tube_envelope_check": "side gas tube bend and strain-relief space",
        "side_gas_leak_witness_check": "side gas gutter and inboard dam routing",
        "sample_relief_leak_witness_check": "sample/relief cap leak routing",
        "gasket_tab_leak_witness_check": "gasket tab root leak routing",
        "dry_bay_ingress_audit_check": "dry-bay ingress audit across external wet sources",
        "adjacent_deck_slot_keepout_check": "neighbor OT-2 slot overhead envelope",
    }
    review_modes = {
        "sample_relief_cap_missing": {
            "removed_parts": ["printed_sample_relief_cap"],
            "review_parts": ["missing_sample_relief_cap_witness"],
            "role": "missing sample/relief cap assembly-state review",
        },
        "sample_relief_cap_unseated": {
            "removed_parts": ["printed_sample_relief_cap"],
            "review_parts": ["unseated_sample_relief_cap_review"],
            "role": "mis-seated sample/relief cap assembly-state review",
        },
        "deck_module_unseated": {
            "removed_parts": [],
            "review_parts": ["deck_module_unseated_review"],
            "role": "unseated OT-2 deck module seating review",
        },
        "deck_pose_repeatability_unproven": {
            "removed_parts": [],
            "review_parts": ["deck_pose_repeatability_review"],
            "role": "repeat-seat and rocking/yaw deck pose review",
        },
        "service_dress_over_pipette_field": {
            "removed_parts": [
                "cots_gas_service_tubes",
                "lower_sensor_service_cable_pigtail",
                "lid_sensor_service_cable_pigtails",
            ],
            "review_parts": ["misdressed_service_bundle_review"],
            "role": "gas/electrical service bundle routed over pipette field review",
        },
        "service_dress_adjacent_slot_collision": {
            "removed_parts": [
                "cots_gas_service_tubes",
                "lower_sensor_service_cable_pigtail",
                "lid_sensor_service_cable_pigtails",
            ],
            "review_parts": ["adjacent_slot_service_collision_review"],
            "role": "gas/electrical service bundle intruding into adjacent OT-2 slot review",
        },
        "dry_bay_obstructed": {
            "removed_parts": [],
            "review_parts": ["dry_bay_obstruction_review"],
            "role": "dry bay obstruction and witness-path visibility review",
        },
        "assembly_debris_present": {
            "removed_parts": [],
            "review_parts": ["assembly_debris_review"],
            "role": "loose assembly debris in dry bay and witness-path review",
        },
        "gasket_squeeze_out_of_range": {
            "removed_parts": [],
            "review_parts": ["gasket_squeeze_out_of_range_review"],
            "role": "out-of-range gasket compression review",
        },
        "latches_unseated": {
            "removed_parts": ["printed_wedge_locks"],
            "review_parts": [
                "unseated_wedge_locks_review",
                "latch_unseated_witnesses",
            ],
            "role": "unseated latch and bearing-flat review",
        },
        "septum_mats_missing": {
            "removed_parts": ["cots_septum_mats"],
            "review_parts": ["missing_septum_mat_witnesses"],
            "role": "missing COTS septum mat assembly-state review",
        },
        "microplates_missing": {
            "removed_parts": ["cots_microplates", "cots_septum_mats"],
            "review_parts": ["missing_microplate_witnesses"],
            "role": "missing plate stack and dependent mat review",
        },
        "perimeter_gaskets_missing": {
            "removed_parts": ["lower_gasket", "upper_gasket"],
            "review_parts": ["missing_perimeter_gasket_witnesses"],
            "role": "missing compressed perimeter gasket review",
        },
        "gas_pcbs_missing": {
            "removed_parts": ["gas_sensor_pcbs", "gas_pcb_interface_gaskets"],
            "review_parts": ["missing_gas_pcb_cartridge_witnesses"],
            "role": "missing gas PCB cartridge and duct-seal review",
        },
        "gas_pcb_cartridges_unseated": {
            "removed_parts": ["gas_sensor_pcbs", "printed_gas_pcb_keeper_doors"],
            "review_parts": ["unseated_gas_pcb_cartridges_review"],
            "role": "unseated gas PCB cartridge and duct-seal compression review",
        },
        "local_sensors_missing": {
            "removed_parts": [
                "headspace_sht41_microcarriers",
                "ir_thermopiles",
                "ir_thermopile_face_gaskets",
            ],
            "review_parts": ["missing_local_sensor_witnesses"],
            "role": "missing local headspace and IR sensor module review",
        },
        "service_leads_missing": {
            "removed_parts": [
                "cots_gas_service_tubes",
                "lower_sensor_service_cable_pigtail",
                "lid_sensor_service_cable_pigtails",
            ],
            "review_parts": ["missing_service_lead_witnesses"],
            "role": "missing connected gas and electrical service lead review",
        },
        "side_gas_tubes_unseated": {
            "removed_parts": ["cots_gas_service_tubes"],
            "review_parts": ["unseated_side_gas_tubes_review"],
            "role": "unseated side gas tube barb and strain-relief review",
        },
        "electrical_connectors_unmated": {
            "removed_parts": [
                "lower_sensor_service_connector",
                "lid_sensor_service_connectors",
                "lower_sensor_service_cable_pigtail",
                "lid_sensor_service_cable_pigtails",
            ],
            "review_parts": ["unmated_sensor_service_connectors_review"],
            "role": "unmated electrical service connector review",
        },
    }
    service_modes = {
        "installed": "normal OT-2 operating assembly",
        "bench_sealed": (
            "bench-only sealed leak/setup review; not normal OT-2 operating authority"
        ),
        "sample_relief_flow_test": (
            "bench-only sample/relief flow-test adapter review; not installed operation"
        ),
        "exploded": "spaced service review of the full assembly tree",
        "lid_off": "lid-stack removal service review",
        "sensor_install": "sensor cartridge and microcarrier service review",
        "mats_exposed": "septum mat service access review",
        "wet_frame_off": "wet-chamber frame removal service review",
        "plates_removable": "plate and septum stack removal service review",
    }
    material_surface_policy = {
        "deck_pods": (
            "ot2_dry_exterior",
            "printed_reusable_cleaning_pending",
            "Gate 1 print QC",
        ),
        "plate_support_frame": (
            "dry_observer_side_with_wet_failure_witness",
            "printed_reusable_cleaning_pending",
            "Gate 1 print QC plus Gate 4 wet/dry witness",
        ),
        "ir_thermopiles": (
            "dry_sensor_package",
            "electronics_or_dimensional_blank_not_cleaned",
            "Gate 6 sensor/thermal",
        ),
        "ir_thermopile_face_gaskets": (
            "dry_sensor_seal",
            "replaceable_elastomer_or_tpu_cleaning_pending",
            "Gate 6 sensor/thermal",
        ),
        "lower_sensor_harness": (
            "dry_electrical_service",
            "electronics_or_dimensional_blank_not_cleaned",
            "install inventory plus Gate 6 sensor/thermal",
        ),
        "lower_harness_cover": (
            "dry_electrical_service",
            "printed_reusable_cleaning_pending",
            "Gate 2 dry assembly plus Gate 6 sensor/thermal",
        ),
        "lower_sensor_service_connector": (
            "dry_electrical_service",
            "electronics_or_dimensional_blank_not_cleaned",
            "Gate 6 sensor/thermal",
        ),
        "printed_lower_sensor_connector_shroud": (
            "dry_electrical_service",
            "printed_reusable_cleaning_pending",
            "Gate 2 dry assembly plus Gate 6 sensor/thermal",
        ),
        "lower_sensor_service_cable_pigtail": (
            "dry_electrical_service",
            "replaceable_cots_service_lead",
            "install inventory plus Gate 6 sensor/thermal",
        ),
        "lower_gasket": (
            "wet_headspace_boundary",
            "replaceable_elastomer_or_tpu_cleaning_pending",
            "Gate 4 wet/dry witness",
        ),
        "wet_chamber_frame": (
            "wet_headspace_boundary",
            "printed_reusable_cleaning_pending",
            "Gate 4 wet/dry witness",
        ),
        "cots_microplates": (
            "wet_consumable",
            "disposable_cots_consumable",
            "Gate 5 consumable/puncture",
        ),
        "cots_septum_mats": (
            "wet_consumable",
            "disposable_cots_consumable",
            "Gate 5 consumable/puncture",
        ),
        "upper_gasket": (
            "wet_headspace_boundary",
            "replaceable_elastomer_or_tpu_cleaning_pending",
            "Gate 4 wet/dry witness",
        ),
        "lid_manifold_shell": (
            "wet_headspace_boundary",
            "printed_reusable_cleaning_pending",
            "Gate 4 wet/dry witness plus Gate 6 sensor/thermal",
        ),
        "headspace_sht41_microcarriers": (
            "wet_headspace_sensor_package",
            "electronics_or_dimensional_blank_not_cleaned",
            "Gate 6 sensor/thermal",
        ),
        "lid_sensor_harness": (
            "dry_electrical_service",
            "electronics_or_dimensional_blank_not_cleaned",
            "install inventory plus Gate 6 sensor/thermal",
        ),
        "lid_harness_cover": (
            "dry_electrical_service",
            "printed_reusable_cleaning_pending",
            "Gate 2 dry assembly plus Gate 6 sensor/thermal",
        ),
        "lid_sensor_service_connectors": (
            "dry_electrical_service",
            "electronics_or_dimensional_blank_not_cleaned",
            "Gate 6 sensor/thermal",
        ),
        "printed_lid_sensor_connector_shrouds": (
            "dry_electrical_service",
            "printed_reusable_cleaning_pending",
            "Gate 2 dry assembly plus Gate 6 sensor/thermal",
        ),
        "lid_sensor_service_cable_pigtails": (
            "dry_electrical_service",
            "replaceable_cots_service_lead",
            "install inventory plus Gate 6 sensor/thermal",
        ),
        "lid_cover": (
            "wet_headspace_and_gas_path_boundary",
            "printed_reusable_cleaning_pending",
            "Gate 4 wet/dry witness plus Gate 6 sensor/thermal",
        ),
        "cots_gas_service_tubes": (
            "external_gas_service",
            "replaceable_cots_tubing",
            "install inventory plus Gate 3 placement",
        ),
        "gas_pcb_interface_gaskets": (
            "gas_sample_path",
            "replaceable_elastomer_or_tpu_cleaning_pending",
            "Gate 6 sensor/thermal",
        ),
        "printed_gas_pcb_keeper_doors": (
            "dry_sensor_retention",
            "printed_reusable_cleaning_pending",
            "Gate 2 dry assembly plus Gate 6 sensor/thermal",
        ),
        "gas_sensor_pcbs": (
            "gas_sample_path",
            "electronics_or_dimensional_blank_not_cleaned",
            "Gate 6 sensor/thermal",
        ),
        "printed_sample_relief_cap": (
            "wet_headspace_boundary",
            "printed_reusable_cleaning_pending",
            "Gate 4 wet/dry witness",
        ),
        "printed_wedge_locks": (
            "dry_mechanical_latch",
            "printed_reusable_cleaning_pending",
            "Gate 2 dry assembly",
        ),
    }
    if set(material_surface_policy) != set(installed):
        raise ValueError("material surface policy must cover every installed part")
    for name, (
        exposure_class,
        service_disposition,
        material_evidence_gate,
    ) in material_surface_policy.items():
        installed[name].update(
            {
                "exposure_class": exposure_class,
                "service_disposition": service_disposition,
                "material_evidence_gate": material_evidence_gate,
            }
        )
    return {
        "policy": {
            "assembly_rule": "print_native_screwless_no_glue_where_possible",
            "material_authority_decision_date": "2026-06-04",
            "material_authority_decision": (
                "first_print_row_coupon_print_native_no_hidden_authority"
            ),
            "supersedes_material_strategy": (
                "2026-05-06_printed_architecture_with_authority_inserts_for_this_coupon"
            ),
            "nonprinted_parts": "explicit_cots_consumable_electronics_gasket_or_service_exception",
            "material_surface_policy": (
                "classify_installed_parts_by_operating_exposure_and_disposition"
            ),
            "allowed_exposure_classes": (
                "ot2_dry_exterior",
                "dry_observer_side_with_wet_failure_witness",
                "dry_sensor_package",
                "dry_sensor_seal",
                "dry_electrical_service",
                "wet_headspace_boundary",
                "wet_consumable",
                "wet_headspace_sensor_package",
                "wet_headspace_and_gas_path_boundary",
                "external_gas_service",
                "gas_sample_path",
                "dry_sensor_retention",
                "dry_mechanical_latch",
            ),
            "allowed_service_dispositions": (
                "printed_reusable_cleaning_pending",
                "replaceable_elastomer_or_tpu_cleaning_pending",
                "electronics_or_dimensional_blank_not_cleaned",
                "replaceable_cots_service_lead",
                "disposable_cots_consumable",
                "replaceable_cots_tubing",
            ),
            "allowed_installed_fabrication_sources": (
                "printed_polymer",
                "compressible_elastomer_or_printed_tpu",
                "cots_consumable",
                "cots_electronics",
                "custom_or_cots_pcb_assembly",
                "electronics_assembly",
                "electronics_microcarrier",
                "cots_cable_assembly",
                "cots_flexible_tubing",
            ),
            "allowed_nonprinted_installed_sources": (
                "compressible_elastomer_or_printed_tpu",
                "cots_consumable",
                "cots_electronics",
                "custom_or_cots_pcb_assembly",
                "electronics_assembly",
                "electronics_microcarrier",
                "cots_cable_assembly",
                "cots_flexible_tubing",
            ),
            "forbidden_retention_authority_terms": (
                "metal_insert",
                "metal_fastener",
                "threaded_insert",
                "adhesive_bond",
                "glued",
                "solvent_weld",
                "thermal_stake",
                "permanent_weld",
                "hidden_bonded_authority",
                "spring",
            ),
        },
        "installed": installed,
        "validation": {
            name: {
                "role": role,
                "fabrication_source": "validation_only_geometry",
                "retention": "not_installed_in_production_tree",
                "visibility": "validation_overlay",
            }
            for name, role in validation.items()
        },
        "review_modes": review_modes,
        "service_modes": service_modes,
    }


def _rounded_box(length: float, width: float, height: float, radius: float) -> cq.Workplane:
    part = cq.Workplane("XY").box(length, width, height, centered=(False, False, False))
    if radius > 0:
        part = part.edges("|Z").fillet(radius)
    return part


def row_coupon_layout(params: dict[str, Any]) -> dict[str, Any]:
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

    return {
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


def build_deck_pods(params: dict[str, Any]) -> cq.Workplane:
    layout = row_coupon_layout(params)
    deck = params["deck_interface"]
    pods: cq.Workplane | None = None
    for tile in layout["tile_origins"]:
        x, y, _, _ = _deck_slot_opening_for_tile(tile, params)
        clearance = deck["slot_shoe_clearance_xy"]
        shoe = _rounded_box(
            deck["slot_opening_length_x"] - 2 * clearance,
            deck["slot_opening_width_y"] - 2 * clearance,
            deck["slot_shoe_thickness_z"],
            deck["slot_shoe_corner_radius"],
        ).translate((x + clearance, y + clearance, layout["deck_plane_z"]))
        pod = _add_deck_engagement_feet(shoe, tile=tile, params=params)
        pod = _add_pod_frame_keys(pod, tile=tile, params=params)
        pods = pod if pods is None else pods.union(pod)
    if pods is None:
        raise ValueError("row coupon requires at least one deck pod")
    return pods


def build_plate_support_frame(params: dict[str, Any]) -> cq.Workplane:
    layout = row_coupon_layout(params)
    base = params["base"]
    plate = params["plate"]
    support = params["plate_support"]
    bay = params["dry_bay"]
    length = layout["length_x"]
    width = layout["width_y"]
    base_h = base["thickness_z"]
    land_w = support["land_width"]
    land_h = support["land_height_z"]
    plate_len = plate["length_x"]
    plate_wid = plate["width_y"]

    model = _rounded_box(length, width, base_h, base["corner_radius"])

    for tile in layout["tile_origins"]:
        x0 = tile["x"]
        y0 = tile["y"]
        model = _add_plate_support_lands(
            model,
            x0=x0,
            y0=y0,
            plate_len=plate_len,
            plate_wid=plate_wid,
            land_w=land_w,
            land_h=land_h,
            z0=base_h,
        )
        model = _add_plate_lateral_locator_rails(
            model,
            tile=tile,
            params=params,
            z0=base_h + land_h,
        )
        model = _cut_dry_bay(
            model,
            x0=x0,
            y0=y0,
            plate_len=plate_len,
            plate_wid=plate_wid,
            base_h=base_h,
            land_h=land_h,
            bay=bay,
        )
        model = _cut_locator_relief(
            model,
            x0=x0,
            y0=y0,
            plate_len=plate_len,
            support=support,
            z=base_h + land_h - support["locator_relief_depth"],
        )
        model = _cut_observer_fiducials(
            model,
            x0=x0,
            y0=y0,
            plate_len=plate_len,
            plate_wid=plate_wid,
            bay=bay,
        )

    model = _cut_wet_dry_witness_gutters(model, params=params)
    model = _add_dry_bay_aperture_thresholds(model, params=params)
    model = _add_gasket_tab_leak_witness_features(
        model,
        params=params,
        owner_part="plate_support_frame",
    )
    model = _cut_pod_frame_key_pockets(model, params)
    model = _cut_ir_sensor_pockets_and_apertures(model, params=params)
    model = _add_ir_aperture_drip_collars(model, params=params)
    model = _cut_lower_sensor_harness_channels(model, params=params)
    model = _add_ir_sensor_retention_lips(model, params=params)
    model = _cut_gasket_capture_groove(
        model,
        params=params,
        z0=base_h,
        from_side="top",
    )
    return model


def build_microplates(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    plate = params["plate"]
    z0 = layout["plate_bottom_z"] if assembly_position else 0.0
    sidewall_w = plate["sidewall_thickness"]
    window_h = plate["bottom_window_thickness_z"]
    top_recess_h = plate.get("well_top_recess_depth_z", 0.0)
    well_opening_d = plate.get("upper_well_diameter", 0.0)

    microplates: cq.Workplane | None = None
    for tile in layout["tile_origins"]:
        part = _perimeter_rails(
            x0=tile["x"],
            y0=tile["y"],
            length=plate["length_x"],
            width=plate["width_y"],
            rail_width=sidewall_w,
            height=plate["height_z"],
            z0=z0,
        )
        window = (
            cq.Workplane("XY")
            .box(
                plate["observation_window_length_x"],
                plate["observation_window_width_y"],
                window_h,
                centered=(True, True, False),
            ).translate(
                (
                    tile["x"] + plate["length_x"] / 2,
                    tile["y"] + plate["width_y"] / 2,
                    z0,
                )
            )
        )
        part = part.union(window)
        if top_recess_h > 0:
            top_deck = (
                cq.Workplane("XY")
                .box(
                    plate["length_x"] - 2 * sidewall_w,
                    plate["width_y"] - 2 * sidewall_w,
                    top_recess_h,
                    centered=(False, False, False),
                )
                .translate(
                    (
                        tile["x"] + sidewall_w,
                        tile["y"] + sidewall_w,
                        z0 + plate["height_z"] - top_recess_h,
                    )
                )
            )
            if well_opening_d > 0:
                well_openings = (
                    cq.Workplane("XY")
                    .pushPoints(_well_centers_for_tile(tile, params))
                    .circle(well_opening_d / 2)
                    .extrude(top_recess_h + 0.2)
                    .translate((0, 0, z0 + plate["height_z"] - top_recess_h - 0.1))
                )
                top_deck = top_deck.cut(well_openings)
            part = part.union(top_deck)
        microplates = part if microplates is None else microplates.union(part)
    if microplates is None:
        raise ValueError("row coupon requires at least one microplate")
    return microplates


def build_septum_mat_inserts(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    plate = params["plate"]
    mat = params["septum_mat"]
    z0 = layout["plate_top_z"] if assembly_position else 0.0

    mats: cq.Workplane | None = None
    for tile in layout["tile_origins"]:
        sheet = _rounded_box(
            plate["length_x"],
            plate["width_y"],
            mat["sheet_thickness_z"],
            mat["sheet_corner_radius"],
        ).translate((tile["x"], tile["y"], z0))

        centers = _well_centers_for_tile(tile, params)
        plugs = (
            cq.Workplane("XY")
            .pushPoints(centers)
            .circle(mat["round_plug_diameter"] / 2)
            .extrude(mat["round_plug_depth_z"] + 0.1)
            .translate((0, 0, z0 - mat["round_plug_depth_z"]))
        )
        part = sheet.union(plugs)
        part = _cut_septum_slit_reliefs(part, centers, z0, mat)
        mats = part if mats is None else mats.union(part)
    if mats is None:
        raise ValueError("row coupon requires at least one septum mat insert")
    return mats


def build_missing_septum_mat_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["plate_top_z"]

    witnesses: cq.Workplane | None = None
    for witness in layout["missing_septum_mat_witnesses"]:
        frame = _perimeter_rails(
            x0=float(witness["x"]),
            y0=float(witness["y"]),
            length=float(witness["length_x"]),
            width=float(witness["width_y"]),
            rail_width=float(witness["rail_width"]),
            height=float(witness["height_z"]),
            z0=float(witness["z"]) + z_shift,
        )
        witnesses = frame if witnesses is None else witnesses.union(frame)
    if witnesses is None:
        raise ValueError("missing septum mat witnesses require at least one tile")
    return witnesses


def build_missing_microplate_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["plate_bottom_z"]

    witnesses: cq.Workplane | None = None
    for witness in layout["missing_microplate_witnesses"]:
        frame = _perimeter_rails(
            x0=float(witness["x"]),
            y0=float(witness["y"]),
            length=float(witness["length_x"]),
            width=float(witness["width_y"]),
            rail_width=float(witness["rail_width"]),
            height=float(witness["height_z"]),
            z0=float(witness["z"]) + z_shift,
        )
        witnesses = frame if witnesses is None else witnesses.union(frame)
    if witnesses is None:
        raise ValueError("missing microplate witnesses require at least one tile")
    return witnesses


def build_missing_perimeter_gasket_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    lower = build_lower_gasket(params, assembly_position=assembly_position)
    upper = build_upper_gasket(params, assembly_position=assembly_position)
    return lower.union(upper)


def build_missing_gas_pcb_cartridge_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]

    witnesses: cq.Workplane | None = None
    for witness in layout["missing_gas_pcb_cartridge_witnesses"]:
        if witness["witness_kind"] == "cartridge_top_footprint":
            part = _perimeter_rails(
                x0=float(witness["x"]),
                y0=float(witness["y"]),
                length=float(witness["length_x"]),
                width=float(witness["width_y"]),
                rail_width=float(witness["rail_width"]),
                height=float(witness["height_z"]),
                z0=float(witness["z"]) + z_shift,
            )
        else:
            part = (
                cq.Workplane("XY")
                .box(
                    float(witness["length_x"]),
                    float(witness["width_y"]),
                    float(witness["height_z"]),
                    centered=(False, False, False),
                )
                .translate(
                    (
                        float(witness["x"]),
                        float(witness["y"]),
                        float(witness["z"]) + z_shift,
                    )
                )
            )
        witnesses = part if witnesses is None else witnesses.union(part)
    if witnesses is None:
        raise ValueError("missing gas PCB witnesses require at least one cartridge")
    return witnesses


def build_missing_local_sensor_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    witness_rects = layout["missing_local_sensor_witnesses"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in witness_rects)

    witnesses: cq.Workplane | None = None
    for witness in witness_rects:
        if witness["witness_kind"] in {
            "headspace_sht41_carrier_footprint",
            "ir_thermopile_body_footprint",
        }:
            part = _perimeter_rails(
                x0=float(witness["x"]),
                y0=float(witness["y"]),
                length=float(witness["length_x"]),
                width=float(witness["width_y"]),
                rail_width=float(witness["rail_width"]),
                height=float(witness["height_z"]),
                z0=float(witness["z"]) + z_shift,
            )
        elif witness["witness_kind"] == "ir_face_gasket_seal":
            part = (
                cq.Workplane("XY")
                .circle(float(witness["outer_diameter"]) / 2)
                .circle(float(witness["inner_diameter"]) / 2)
                .extrude(float(witness["height_z"]))
                .translate(
                    (
                        float(witness["center_x"]),
                        float(witness["center_y"]),
                        float(witness["z"]) + z_shift,
                    )
                )
            )
        else:
            raise ValueError(f"unknown local sensor witness kind: {witness['witness_kind']}")
        witnesses = part if witnesses is None else witnesses.union(part)
    if witnesses is None:
        raise ValueError("missing local sensor witnesses require at least one sensor mount")
    return witnesses


def build_unseated_gas_pcb_cartridges_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    review_rects = layout["unseated_gas_pcb_cartridges_review"]
    mounts_by_name = {mount["name"]: mount for mount in layout["gas_sensor_pcb_mounts"]}
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]

    review: cq.Workplane | None = None
    for rect in review_rects:
        mount = mounts_by_name[rect["source_rect_name"]]
        z = float(rect["z"]) + z_shift
        pcb = (
            cq.Workplane("XY")
            .box(
                float(rect["length_x"]),
                float(rect["width_y"]),
                float(rect["height_z"]),
                centered=(False, False, False),
            )
            .translate((float(rect["x"]), float(rect["y"]), z))
        )
        pcb = _cut_vertical_mount_aperture(pcb, mount, z=z)
        pcb = pcb.union(_sensor_chip_marker_for_mount(mount, z=z))

        door_rect = dict(rect["keeper_door_rect"])
        tab_rect = dict(rect["keeper_tab_rect"])
        door_rect["z"] = float(door_rect["z"]) + z_shift
        tab_rect["z"] = float(tab_rect["z"]) + z_shift
        door = _boxes_from_rectangles([door_rect, tab_rect])
        body = pcb.union(door)
        review = body if review is None else review.union(body)
    if review is None:
        raise ValueError("unseated gas PCB cartridge review requires at least one mount")
    return review


def build_missing_service_lead_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    witness_rects = layout["missing_service_lead_witnesses"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in witness_rects)

    witnesses: cq.Workplane | None = None
    for witness in witness_rects:
        part = _perimeter_rails(
            x0=float(witness["x"]),
            y0=float(witness["y"]),
            length=float(witness["length_x"]),
            width=float(witness["width_y"]),
            rail_width=float(witness["rail_width"]),
            height=float(witness["height_z"]),
            z0=float(witness["z"]) + z_shift,
        )
        witnesses = part if witnesses is None else witnesses.union(part)
    if witnesses is None:
        raise ValueError("missing service lead witnesses require at least one service lead")
    return witnesses


def build_unseated_side_gas_tubes_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    review_specs = layout["unseated_side_gas_tubes_review"]
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]

    review: cq.Workplane | None = None
    for spec in review_specs:
        model = _axis_tube(
            axis=str(spec["axis"]),
            x=float(spec["x"]),
            y=float(spec["y"]),
            z=float(spec["z"]) + z_shift,
            length=float(spec["length"]),
            outer_diameter=float(spec["diameter"]),
            inner_diameter=float(spec["inner_diameter"]),
        )
        review = model if review is None else review.union(model)
    if review is None:
        raise ValueError("unseated side gas tube review requires at least one tube")
    return review


def build_unmated_sensor_service_connectors_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["unmated_sensor_service_connector_review_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_electrical_connector_mating_state_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["electrical_connector_mating_state_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_lid_gasket(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    rail_w = seal["gasket_rail_width"]
    rail_h = seal["compressed_gasket_height_z"]
    z0 = layout["gasket_bottom_z"] if assembly_position else 0.0
    bounds = _shared_chamber_bounds(layout, params)

    gasket = _perimeter_rails(
        x0=bounds["x"],
        y0=bounds["y"],
        length=bounds["length_x"],
        width=bounds["width_y"],
        rail_width=rail_w,
        height=rail_h,
        z0=z0,
    )
    return _add_gasket_service_tabs(gasket, params=params, z0=z0)


def build_upper_gasket(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    return build_lid_gasket(params, assembly_position=assembly_position)


def build_lower_gasket(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    rail_w = seal["gasket_rail_width"]
    rail_h = seal["compressed_gasket_height_z"]
    z0 = layout["base_top_z"] if assembly_position else 0.0
    bounds = _shared_chamber_bounds(layout, params)

    gasket = _perimeter_rails(
        x0=bounds["x"],
        y0=bounds["y"],
        length=bounds["length_x"],
        width=bounds["width_y"],
        rail_width=rail_w,
        height=rail_h,
        z0=z0,
    )
    return _add_gasket_service_tabs(gasket, params=params, z0=z0)


def build_wet_chamber_skirt(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    skirt = params["wet_chamber_skirt"]
    bounds = layout["wet_chamber_skirt"]
    z0 = bounds["bottom_z"] if assembly_position else 0.0

    model = _perimeter_rails(
        x0=bounds["x"],
        y0=bounds["y"],
        length=bounds["length_x"],
        width=bounds["width_y"],
        rail_width=skirt["wall_thickness"],
        height=bounds["height_z"],
        z0=z0,
    )
    radius = skirt.get("corner_radius", 0.0)
    if radius > 0:
        model = model.edges("|Z").fillet(radius)
    model = _cut_gasket_capture_groove(
        model,
        params=params,
        z0=z0,
        from_side="bottom",
    )
    model = _cut_gasket_capture_groove(
        model,
        params=params,
        z0=z0 + bounds["height_z"],
        from_side="top",
    )
    model = _cut_condensation_pockets(model, params=params, z0=z0)
    model = _add_wet_chamber_service_dividers(
        model,
        layout=layout,
        params=params,
        z0=z0,
        height=bounds["height_z"],
    )
    model = _add_latch_tension_posts(
        model,
        layout=layout,
        params=params,
        z0=z0,
        height=bounds["height_z"],
    )
    return model


def build_wet_chamber_frame(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    return build_wet_chamber_skirt(params, assembly_position=assembly_position)


def build_headspace_volume_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["headspace_volume_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_well_cell_plane_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    targets = layout["well_cell_plane_check"]["body_targets"]
    z_shift = _harness_z_shift(targets, assembly_position=assembly_position)
    return _bodies_from_shape_targets(targets, z_shift=z_shift)


def build_ir_thermopile_fov_spot_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    targets = layout["ir_thermopile_fov_spot_check"]["body_targets"]
    z_shift = _harness_z_shift(targets, assembly_position=assembly_position)
    return _bodies_from_shape_targets(targets, z_shift=z_shift)


def build_thermal_condensation_proxy_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    targets = layout["thermal_condensation_proxy_check"]["body_targets"]
    if not targets:
        raise ValueError("thermal/condensation proxy check requires at least one target")
    z_shift = 0.0 if assembly_position else -min(float(target["z"]) for target in targets)
    return _bodies_from_shape_targets(targets, z_shift=z_shift)


def build_headspace_barrier_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["headspace_barrier_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_dry_bay_envelope_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["dry_bay_envelope_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_dry_bay_boundary_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["dry_bay_boundary_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_wet_dry_failure_path_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["wet_dry_failure_path_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_dry_bay_obstruction_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["dry_bay_obstruction_review"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
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


def build_misdressed_service_bundle_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["misdressed_service_bundle_review"]
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


def build_adjacent_deck_slot_keepout_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["adjacent_deck_slot_keepout_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_carriage_envelope_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["observer_carriage_envelope_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -float(rects[0]["z"])
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_service_raceway_envelope_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["observer_service_raceway_envelope_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -float(rects[0]["z"])
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_front_end_swept_body_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["observer_front_end_swept_body_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -float(rects[0]["z"])
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_infinity_port_datum_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["observer_infinity_port_datum_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -float(rects[0]["z"])
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_fiducial_focus_target_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    targets = layout["observer_fiducial_focus_target_check"]["body_targets"]
    z_shift = _harness_z_shift(targets, assembly_position=assembly_position)
    return _bodies_from_shape_targets(targets, z_shift=z_shift)


def build_observer_optical_stability_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["observer_optical_stability_check"]
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("observer optical stability check requires rectangles")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_kinematic_split_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["observer_kinematic_split_check"]
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("observer kinematic split check requires rectangles")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_lid_manifold_shell(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    lid = params["lid_manifold"]
    plate = params["plate"]
    mat = params["septum_mat"]
    access = params["pipette_access"]
    z0 = layout["lid_bottom_z"] if assembly_position else 0.0

    model = _rounded_box(
        layout["length_x"],
        layout["width_y"],
        lid["thickness_z"],
        lid["corner_radius"],
    ).translate((0, 0, z0))

    chamber = _shared_chamber_bounds(layout, params)
    rail_w = seal["gasket_rail_width"]
    model = model.cut(
        cq.Workplane("XY")
        .box(
            chamber["length_x"] - 2 * rail_w,
            chamber["width_y"] - 2 * rail_w,
            seal["headspace_recess_depth_z"] + 0.2,
            centered=(False, False, False),
        )
        .translate((chamber["x"] + rail_w, chamber["y"] + rail_w, z0 - 0.1))
    )

    seat_clearance = mat.get("seat_clearance_xy", 0.0)
    seat_depth = mat.get("seat_pocket_depth_z", 0.0)
    if seat_depth > 0:
        for tile in layout["tile_origins"]:
            model = model.cut(
                cq.Workplane("XY")
                .box(
                    plate["length_x"] + 2 * seat_clearance,
                    plate["width_y"] + 2 * seat_clearance,
                    seat_depth + 0.2,
                    centered=(False, False, False),
                )
                .translate(
                    (
                        tile["x"] - seat_clearance,
                        tile["y"] - seat_clearance,
                        z0 - 0.1,
                    )
                )
            )

    if access.get("septum_window_enabled", False):
        for tile in layout["tile_origins"]:
            x, y, length, width = _septum_access_window_for_tile(tile, params)
            model = model.cut(
                cq.Workplane("XY")
                .box(
                    length,
                    width,
                    lid["thickness_z"] + lid["duct_height_z"] + 0.4,
                    centered=(False, False, False),
                )
                .translate((x, y, z0 - 0.2))
            )
            model = _cut_septum_lift_notch(
                model,
                access_x=x,
                access_y=y,
                params=params,
                z0=z0,
            )

    duct_h = lid["duct_height_z"]
    port_positions = _lid_port_positions(layout, params)
    for port in port_positions:
        model = model.cut(
            cq.Workplane("XY")
            .circle(float(port["hole_diameter"]) / 2)
            .extrude(lid["thickness_z"] + max(duct_h, float(port["boss_height_z"])) + 0.4)
            .translate((float(port["x"]), float(port["y"]), z0 - 0.2))
        )

    stop_h = seal["compression_stop_pad_height_z"]
    stop_hole_d = seal["compression_stop_clearance_hole_diameter"]
    for x, y in _compression_stop_positions(params):
        model = model.cut(
            cq.Workplane("XY")
            .circle(stop_hole_d / 2)
            .extrude(lid["thickness_z"] + stop_h + 0.4)
            .translate((x, y, z0 - 0.2))
        )

    model = _cut_gasket_capture_groove(
        model,
        params=params,
        z0=z0,
        from_side="bottom",
    )
    model = _add_gasket_tab_leak_witness_features(
        model,
        params=params,
        owner_part="lid_manifold_shell",
        z_shift=0.0 if assembly_position else -layout["lid_bottom_z"],
    )
    model = _cut_lid_cover_tongue_groove(model, params=params, z0=z0)

    for tile in layout["tile_origins"]:
        if layout["row_axis"] == "x":
            x_center = tile["x"] + plate["length_x"] / 2
            supply_y = tile["y"] + plate["width_y"] - lid["diffuser_offset_from_plate_edge_y"]
            return_y = tile["y"] + lid["diffuser_offset_from_plate_edge_y"]
            for slot_x in _slot_centers(
                x_center,
                lid["diffuser_slot_count_per_tile"],
                lid["diffuser_slot_length_x"],
            ):
                for slot_y in [supply_y, return_y]:
                    model = model.cut(
                        cq.Workplane("XY")
                        .box(
                            lid["diffuser_slot_length_x"],
                            lid["diffuser_slot_width_y"],
                            lid["thickness_z"] + duct_h + 0.4,
                            centered=(True, True, False),
                        )
                        .translate((slot_x, slot_y, z0 - 0.2))
                    )
        else:
            y_center = tile["y"] + plate["width_y"] / 2
            supply_x = tile["x"] + lid["diffuser_offset_from_plate_edge_x"]
            return_x = tile["x"] + plate["length_x"] - lid["diffuser_offset_from_plate_edge_x"]
            for slot_y in _slot_centers(
                y_center,
                lid["diffuser_slot_count_per_tile"],
                lid["diffuser_slot_length_x"],
            ):
                for slot_x in [supply_x, return_x]:
                    model = model.cut(
                        cq.Workplane("XY")
                        .box(
                            lid["diffuser_slot_width_y"],
                            lid["diffuser_slot_length_x"],
                            lid["thickness_z"] + duct_h + 0.4,
                            centered=(True, True, False),
                        )
                        .translate((slot_x, slot_y, z0 - 0.2))
                    )
        for target in access.get("targets", []):
            if not access.get("septum_window_enabled", False):
                model = model.cut(
                    cq.Workplane("XY")
                    .circle(access.get("hole_diameter", 4.2) / 2)
                    .extrude(lid["thickness_z"] + duct_h + 0.4)
                    .translate(
                        (
                            tile["x"] + target["local_x"] + target.get("offset_x", 0.0),
                            tile["y"] + target["local_y"] + target.get("offset_y", 0.0),
                            z0 - 0.2,
                        )
                        )
                    )
    model = _add_headspace_sht41_sockets(
        model,
        params=params,
        assembly_position=assembly_position,
    )
    model = _cut_lid_sensor_harness_channels(
        model,
        params=params,
        owner_part="lid_manifold_shell",
        assembly_position=assembly_position,
    )
    return model


def build_lid_cover(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    lid = params["lid_manifold"]
    row = params["row"]
    z0 = layout["lid_top_z"] if assembly_position else 0.0
    duct_h = lid["duct_height_z"]
    duct_w = lid["duct_width_y"]

    cover: cq.Workplane | None = None
    if layout["row_axis"] == "x":
        front_duct_y = row["side_margin_y"] - duct_w / 2
        rear_duct_y = layout["width_y"] - row["side_margin_y"] - duct_w / 2
        duct_length_x = layout["length_x"] - 2 * row["end_margin_x"]
        segments = [
            (row["end_margin_x"], front_duct_y, duct_length_x, duct_w),
            (row["end_margin_x"], rear_duct_y, duct_length_x, duct_w),
            (row["end_margin_x"], front_duct_y, duct_w, rear_duct_y - front_duct_y + duct_w),
            (
                layout["length_x"] - row["end_margin_x"] - duct_w,
                front_duct_y,
                duct_w,
                rear_duct_y - front_duct_y + duct_w,
            ),
        ]
    else:
        left_duct_x = row["end_margin_x"] - duct_w / 2
        right_duct_x = layout["length_x"] - row["end_margin_x"] - duct_w / 2
        duct_length_y = layout["width_y"] - 2 * row["side_margin_y"]
        segments = [
            (left_duct_x, row["side_margin_y"], duct_w, duct_length_y),
            (right_duct_x, row["side_margin_y"], duct_w, duct_length_y),
            (left_duct_x, row["side_margin_y"], right_duct_x - left_duct_x + duct_w, duct_w),
            (
                left_duct_x,
                layout["width_y"] - row["side_margin_y"] - duct_w,
                right_duct_x - left_duct_x + duct_w,
                duct_w,
            ),
        ]

    for x, y, length, width in segments:
        segment = (
            cq.Workplane("XY")
            .box(length, width, duct_h, centered=(False, False, False))
            .translate((x, y, z0))
        )
        cover = segment if cover is None else cover.union(segment)
    if cover is None:
        raise ValueError("lid cover requires at least one segment")

    cover = _add_lid_cover_tongue(cover, params=params, z0=z0)

    for port in _lid_port_positions(layout, params):
        cover = _add_lid_port_interface(cover, port, params=params, layout=layout, z0=z0)
        cover = cover.cut(
            cq.Workplane("XY")
            .circle(float(port["hole_diameter"]) / 2)
            .extrude(max(duct_h, float(port["boss_height_z"])) + 0.4)
            .translate((float(port["x"]), float(port["y"]), z0 - 0.2))
        )

    cover = _add_sample_relief_leak_witness_features(
        cover,
        params=params,
        assembly_position=assembly_position,
    )
    cover = _add_side_gas_service_features(
        cover,
        params=params,
        assembly_position=assembly_position,
    )

    stop_size = seal["compression_stop_size"]
    stop_h = seal["compression_stop_pad_height_z"]
    stop_hole_d = seal["compression_stop_clearance_hole_diameter"]
    for x, y in _compression_stop_positions(params):
        cover = cover.union(
            cq.Workplane("XY")
            .box(stop_size, stop_size, stop_h, centered=(True, True, False))
            .translate((x, y, z0))
        )
        cover = cover.cut(
            cq.Workplane("XY")
            .circle(stop_hole_d / 2)
            .extrude(max(duct_h, stop_h) + 0.4)
            .translate((x, y, z0 - 0.2))
        )
    cover = _add_wedge_receiver_rails(cover, params=params, z0=z0)
    cover = _add_gas_sensor_pcb_sockets(
        cover,
        params=params,
        assembly_position=assembly_position,
    )
    cover = _cut_lid_sensor_harness_channels(
        cover,
        params=params,
        owner_part="lid_cover",
        assembly_position=assembly_position,
    )
    return cover


def build_printed_wedge_locks(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    lid = params["lid_manifold"]
    z0 = layout["lid_top_z"] + lid["duct_height_z"] if assembly_position else 0.0

    locks: cq.Workplane | None = None
    for lock_rect in _wedge_lock_rectangles(layout, params):
        lock = _build_wedge_lock_body(lock_rect, params=params, z0=z0)
        locks = lock if locks is None else locks.union(lock)
    if locks is None:
        raise ValueError("printed wedge locks require compression stop positions")
    return locks


def build_unseated_wedge_locks_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    lid = params["lid_manifold"]
    production = params.get("production_assembly", {})
    z0 = layout["lid_top_z"] + lid["duct_height_z"] if assembly_position else 0.0
    offset = production.get("wedge_unseated_review_offset_x", 6.0)

    locks: cq.Workplane | None = None
    for lock_rect in _wedge_lock_rectangles(layout, params):
        dx = dy = 0.0
        direction = -1.0 if lock_rect["insert_from"] == "min" else 1.0
        if lock_rect["slide_axis"] == "x":
            dx = direction * offset
        else:
            dy = direction * offset
        lock = _build_wedge_lock_body(lock_rect, params=params, z0=z0).translate((dx, dy, 0))
        locks = lock if locks is None else locks.union(lock)
    if locks is None:
        raise ValueError("unseated wedge lock review requires compression stop positions")
    return locks


def build_latch_unseated_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    lid = params["lid_manifold"]
    z0 = (
        layout["lid_top_z"]
        + lid["duct_height_z"]
        + production.get("wedge_lock_height_z", 0.0)
        if assembly_position
        else production.get("wedge_lock_height_z", 0.0)
    )
    height = production.get("wedge_unseated_witness_height_z", 0.6)
    rects = [
        {
            "x": lock["bearing_flat_x"],
            "y": lock["bearing_flat_y"],
            "z": round(z0, 3),
            "length_x": lock["bearing_flat_length_x"],
            "width_y": lock["bearing_flat_width_y"],
            "height_z": round(height, 3),
        }
        for lock in _wedge_lock_rectangles(layout, params)
    ]
    return _boxes_from_rectangles(rects)


def build_assembly_state_witness_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    review_builders = {
        "missing_microplate_witnesses": build_missing_microplate_witnesses,
        "missing_septum_mat_witnesses": build_missing_septum_mat_witnesses,
        "missing_perimeter_gasket_witnesses": build_missing_perimeter_gasket_witnesses,
        "missing_gas_pcb_cartridge_witnesses": build_missing_gas_pcb_cartridge_witnesses,
        "unseated_gas_pcb_cartridges_review": (
            build_unseated_gas_pcb_cartridges_review
        ),
        "missing_local_sensor_witnesses": build_missing_local_sensor_witnesses,
        "missing_service_lead_witnesses": build_missing_service_lead_witnesses,
        "unseated_side_gas_tubes_review": build_unseated_side_gas_tubes_review,
        "missing_sample_relief_cap_witness": build_missing_sample_relief_cap_witness,
        "latch_unseated_witnesses": build_latch_unseated_witnesses,
    }
    witness_bodies = [
        review_builders[review_part](
            params,
            assembly_position=assembly_position,
        )
        for review_part in layout["assembly_state_witness_check"]["source_review_parts"]
    ]

    check = witness_bodies[0]
    for body in witness_bodies[1:]:
        check = check.union(body)
    return check


def build_printed_sample_relief_cap(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    ports = [
        port for port in _lid_port_positions(layout, params) if port["role"] == "sample_relief"
    ]
    if len(ports) != 1:
        raise ValueError("printed sample/relief cap requires exactly one sample/relief port")

    port = ports[0]
    plug_depth = production.get("port_cap_plug_depth_z", 0.0)
    plug_bottom_z = (
        layout["lid_top_z"] + float(port["boss_height_z"]) - plug_depth
        if assembly_position
        else 0.0
    )
    return _build_port_cap_body(
        x=float(port["x"]),
        y=float(port["y"]),
        plug_d=float(port["cap_plug_diameter"]),
        flange_d=float(port["cap_flange_diameter"]),
        plug_bottom_z=plug_bottom_z,
        plug_depth=plug_depth,
        flange_h=production.get("port_cap_flange_height_z", 0.0),
        seal_lip_inner_d=float(port["cap_seal_lip_inner_diameter"]),
        seal_lip_outer_d=float(port["cap_seal_lip_outer_diameter"]),
        seal_lip_h=float(port["cap_seal_lip_height_z"]),
        grip_len=production.get("port_cap_grip_length_xy", 0.0),
        grip_w=production.get("port_cap_grip_width_xy", 0.0),
        grip_h=production.get("port_cap_grip_height_z", 0.0),
        grip_overlap=production.get("port_cap_grip_attachment_overlap_xy", 0.0),
        layout=layout,
    )


def build_gas_sensor_pcbs(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    pcbs: cq.Workplane | None = None
    for mount in layout["gas_sensor_pcb_mounts"]:
        z = float(mount["z"]) if assembly_position else 0.0
        pcb = (
            cq.Workplane("XY")
            .box(
                float(mount["length_x"]),
                float(mount["width_y"]),
                float(mount["height_z"]),
                centered=(False, False, False),
            )
            .translate((float(mount["x"]), float(mount["y"]), z))
        )
        pcb = _cut_vertical_mount_aperture(pcb, mount, z=z)
        chip = _sensor_chip_marker_for_mount(mount, z=z)
        pcb = pcb.union(chip)
        pcbs = pcb if pcbs is None else pcbs.union(pcb)
    if pcbs is None:
        raise ValueError("gas sensor PCB model requires at least one mount")
    return pcbs


def build_printed_gas_pcb_keeper_doors(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    mounts = params.get("sensor_mounts", {})
    install = params.get("sensor_installation", {})
    wall = mounts.get("gas_pcb_socket_wall_thickness", 1.2)
    door_h = install.get("gas_pcb_keeper_door_height_z", 0.8)
    tab_len = install.get("gas_pcb_keeper_release_tab_length_y", 4.0)
    tab_w = install.get("gas_pcb_keeper_release_tab_width_x", 3.0)

    doors: cq.Workplane | None = None
    for mount in layout["gas_sensor_pcb_mounts"]:
        x = float(mount["x"])
        y = float(mount["y"])
        z = float(mount["z"]) if assembly_position else 0.0
        length_x = float(mount["length_x"])
        width_y = float(mount["width_y"])
        height_z = float(mount["height_z"])
        door_z = z + height_z - door_h
        door = (
            cq.Workplane("XY")
            .box(
                length_x + 2 * wall,
                width_y + 2 * wall,
                door_h,
                centered=(False, False, False),
            )
            .translate((x - wall, y - wall, door_z))
        )
        if length_x <= width_y:
            if mount["role"] == "supply":
                tab_x = max(0.0, x - wall - tab_w)
            else:
                tab_x = min(float(layout["length_x"]) - tab_w, x + length_x + wall)
            tab_y = float(mount["aperture_y"]) - tab_len / 2
            tab = (
                cq.Workplane("XY")
                .box(tab_w, tab_len, door_h, centered=(False, False, False))
                .translate((tab_x, tab_y, door_z))
            )
        else:
            if mount["role"] == "supply":
                tab_y = max(0.0, y - wall - tab_len)
            else:
                tab_y = min(float(layout["width_y"]) - tab_len, y + width_y + wall)
            tab_x = float(mount["aperture_x"]) - tab_w / 2
            tab = (
                cq.Workplane("XY")
                .box(tab_w, tab_len, door_h, centered=(False, False, False))
                .translate((tab_x, tab_y, door_z))
            )
        door = door.union(tab)
        doors = door if doors is None else doors.union(door)
    if doors is None:
        raise ValueError("gas PCB keeper doors require at least one mount")
    return doors


def build_gas_pcb_interface_gaskets(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    gaskets: cq.Workplane | None = None
    for mount in layout["gas_sensor_pcb_mounts"]:
        interface = mount["gas_interface"]
        gasket = _boxes_from_rectangles([interface["gasket_rect"]], z_shift=z_shift)
        gasket = _cut_rectangular_gas_interface_window(
            gasket,
            interface["gasket_window_rect"],
            z_shift=z_shift,
        )
        gaskets = gasket if gaskets is None else gaskets.union(gasket)
    if gaskets is None:
        raise ValueError("gas PCB interface gaskets require at least one mount")
    return gaskets


def build_headspace_sht41_microcarriers(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    carriers: cq.Workplane | None = None
    for mount in layout["headspace_sht41_mounts"]:
        z = float(mount["z"]) if assembly_position else 0.0
        carrier = (
            cq.Workplane("XY")
            .box(
                float(mount["length_x"]),
                float(mount["width_y"]),
                float(mount["height_z"]),
                centered=(False, False, False),
            )
            .translate((float(mount["x"]), float(mount["y"]), z))
        )
        aperture = (
            cq.Workplane("XY")
            .circle(float(mount["aperture_diameter"]) / 2)
            .extrude(float(mount["height_z"]) + 0.1)
            .translate((float(mount["aperture_x"]), float(mount["aperture_y"]), z - 0.05))
        )
        carrier = carrier.cut(aperture)
        notch = mount["registration_notch_rect"]
        carrier = carrier.cut(
            cq.Workplane("XY")
            .box(
                float(notch["length_x"]) + 0.05,
                float(notch["width_y"]) + 0.05,
                float(notch["height_z"]) + 0.05,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(notch["x"]) - 0.025,
                    float(notch["y"]) - 0.025,
                    float(notch["z"]) + (0.0 if assembly_position else -float(mount["z"])) - 0.025,
                )
            )
        )
        carriers = carrier if carriers is None else carriers.union(carrier)
    if carriers is None:
        raise ValueError("headspace SHT41 carrier model requires at least one mount")
    return carriers


def build_ir_thermopiles(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    mounts = params.get("sensor_mounts", {})
    lens_h = mounts.get("ir_lens_height_z", 0.35)
    sensors: cq.Workplane | None = None
    for mount in layout["ir_sensor_mounts"]:
        z = float(mount["z"]) if assembly_position else 0.0
        sensor = (
            cq.Workplane("XY")
            .circle(float(mount["length_x"]) / 2)
            .extrude(float(mount["height_z"]))
            .translate((float(mount["center_x"]), float(mount["center_y"]), z))
        )
        lens = (
            cq.Workplane("XY")
            .circle(float(mount["aperture_diameter"]) / 2)
            .extrude(lens_h)
            .translate(
                (
                    float(mount["center_x"]),
                    float(mount["center_y"]),
                    z + float(mount["height_z"]),
                )
            )
        )
        sensor = sensor.union(lens)
        sensors = sensor if sensors is None else sensors.union(sensor)
    if sensors is None:
        raise ValueError("IR thermopile model requires at least one mount")
    return sensors


def build_ir_thermopile_face_gaskets(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    gaskets: cq.Workplane | None = None
    for mount in layout["ir_sensor_mounts"]:
        gasket = mount["face_gasket"]
        z = float(gasket["z"]) if assembly_position else 0.0
        body = (
            cq.Workplane("XY")
            .circle(float(gasket["outer_diameter"]) / 2)
            .extrude(float(gasket["height_z"]))
            .translate((float(gasket["x"]), float(gasket["y"]), z))
        )
        aperture = (
            cq.Workplane("XY")
            .circle(float(gasket["inner_diameter"]) / 2)
            .extrude(float(gasket["height_z"]) + 0.2)
            .translate((float(gasket["x"]), float(gasket["y"]), z - 0.1))
        )
        gasket_body = body.cut(aperture)
        gaskets = gasket_body if gaskets is None else gaskets.union(gasket_body)
    if gaskets is None:
        raise ValueError("IR thermopile face gaskets require at least one mount")
    return gaskets


def build_lower_sensor_harness(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = [layout["lower_ir_harness_trunk"]]
    rects.extend(route["branch_rect"] for route in layout["lower_ir_harness_routes"])
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_lid_sensor_harness(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = [*layout["lid_sensor_harness_trunks"]]
    rects.extend(route["branch_rect"] for route in layout["lid_sensor_harness_routes"])
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_lower_harness_cover(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = [layout["lower_ir_harness_trunk"]]
    for route in layout["lower_ir_harness_routes"]:
        rects.append(route["branch_rect"])
        rects.append(route["strain_relief_rect"])
    z_shift = 0.0 if assembly_position else 0.0
    cover = _harness_cover_from_rectangles(rects, params=params, underside=True, z_shift=z_shift)
    cover = _add_harness_snap_tabs(
        cover,
        layout["lower_ir_harness_trunk"],
        params=params,
        underside=True,
        z_shift=z_shift,
    )
    return cover


def build_lid_harness_cover(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = [*layout["lid_sensor_harness_trunks"]]
    for route in layout["lid_sensor_harness_routes"]:
        rects.append(route["branch_rect"])
        rects.append(route["strain_relief_rect"])
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    cover = _harness_cover_from_rectangles(rects, params=params, underside=False, z_shift=z_shift)
    for trunk in layout["lid_sensor_harness_trunks"]:
        cover = _add_harness_snap_tabs(
            cover,
            trunk,
            params=params,
            underside=False,
            z_shift=z_shift,
        )
    return cover


def build_lower_sensor_service_connector(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    connector = layout["lower_ir_connector_envelope"]
    z_shift = _harness_z_shift([connector], assembly_position=assembly_position)
    return _build_sensor_service_connector_models([connector], z_shift=z_shift)


def build_lid_sensor_service_connectors(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    connectors = layout["lid_service_connector_envelopes"]
    z_shift = _harness_z_shift(connectors, assembly_position=assembly_position)
    return _build_sensor_service_connector_models(connectors, z_shift=z_shift)


def build_printed_lower_sensor_connector_shroud(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    connector = layout["lower_ir_connector_envelope"]
    z_shift = _harness_z_shift([connector], assembly_position=assembly_position)
    return _build_printed_sensor_connector_shrouds([connector], z_shift=z_shift)


def build_printed_lid_sensor_connector_shrouds(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    connectors = layout["lid_service_connector_envelopes"]
    z_shift = _harness_z_shift(connectors, assembly_position=assembly_position)
    return _build_printed_sensor_connector_shrouds(connectors, z_shift=z_shift)


def build_lower_sensor_service_cable_pigtail(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rect = layout["lower_ir_connector_envelope"]["installed_cable_pigtail_rect"]
    z_shift = _harness_z_shift([rect], assembly_position=assembly_position)
    return _boxes_from_rectangles([rect], z_shift=z_shift)


def build_lid_sensor_service_cable_pigtails(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = [
        connector["installed_cable_pigtail_rect"]
        for connector in layout["lid_service_connector_envelopes"]
    ]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_sensor_connector_service_clearance_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["sensor_connector_service_clearance_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_sensor_service_cable_envelope_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["sensor_service_cable_envelope_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
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


def build_unseated_sample_relief_cap_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    plug_depth = production.get("port_cap_plug_depth_z", 0.0)
    flange_h = production.get("port_cap_flange_height_z", 0.0)
    grip_h = production.get("port_cap_grip_height_z", 0.0)
    grip_len = production.get("port_cap_grip_length_xy", 0.0)
    grip_w = production.get("port_cap_grip_width_xy", 0.0)
    grip_overlap = production.get("port_cap_grip_attachment_overlap_xy", 0.0)
    unseated_lift = production.get("sample_relief_cap_unseated_lift_z", 0.0)
    port_positions = _lid_port_positions(layout, params)

    caps: cq.Workplane | None = None
    for port in port_positions:
        x = float(port["x"])
        y = float(port["y"])
        boss_h = float(port["boss_height_z"])
        plug_d = float(port["cap_plug_diameter"])
        flange_d = float(port["cap_flange_diameter"])
        plug_bottom_z = (
            layout["lid_top_z"] + boss_h - plug_depth + unseated_lift
            if assembly_position
            else 0.0
        )
        cap = _build_port_cap_body(
            x=x,
            y=y,
            plug_d=plug_d,
            flange_d=flange_d,
            plug_bottom_z=plug_bottom_z,
            plug_depth=plug_depth,
            flange_h=flange_h,
            seal_lip_inner_d=float(port["cap_seal_lip_inner_diameter"]),
            seal_lip_outer_d=float(port["cap_seal_lip_outer_diameter"]),
            seal_lip_h=float(port["cap_seal_lip_height_z"]),
            grip_len=grip_len,
            grip_w=grip_w,
            grip_h=grip_h,
            grip_overlap=grip_overlap,
            layout=layout,
        )
        caps = cap if caps is None else caps.union(cap)
    if caps is None:
        raise ValueError("sample/relief cap unseated review requires a lid port")
    return caps


def build_missing_sample_relief_cap_witness(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    ring_w = production.get("sample_relief_cap_missing_witness_ring_width_xy", 0.8)
    witness_h = production.get("sample_relief_cap_missing_witness_height_z", 0.6)
    flag_len = production.get("sample_relief_cap_missing_witness_flag_length_xy", 6.0)
    flag_w = production.get("sample_relief_cap_missing_witness_flag_width_xy", 1.4)

    witnesses: cq.Workplane | None = None
    for port in _lid_port_positions(layout, params):
        boss_h = float(port["boss_height_z"])
        inner_d = float(port["cap_flange_diameter"])
        height = witness_h
        z0 = layout["lid_top_z"] + boss_h if assembly_position else 0.0
        outer_d = inner_d + 2 * ring_w
        witness = (
            cq.Workplane("XY")
            .circle(outer_d / 2)
            .circle(inner_d / 2)
            .extrude(height)
            .translate((float(port["x"]), float(port["y"]), z0))
        )
        witness = _add_sample_relief_cap_review_flag(
            witness,
            port=port,
            layout=layout,
            z0=z0,
            length=flag_len,
            width=flag_w,
            height=height,
            radial_from_diameter=outer_d,
        )
        witnesses = witness if witnesses is None else witnesses.union(witness)
    if witnesses is None:
        raise ValueError("missing sample/relief cap witness requires a lid port")
    return witnesses


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


def build_flow_test_adapters(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    adapter_d = production.get("flow_probe_adapter_diameter", 7.0)
    adapter_h = production.get("flow_probe_adapter_height_z", 3.0)

    ports = [
        port for port in _lid_port_positions(layout, params) if port["role"] == "sample_relief"
    ]
    if len(ports) != 1:
        raise ValueError("flow test adapter requires exactly one sample/relief port")

    adapters: cq.Workplane | None = None
    for port in ports:
        z0 = layout["lid_top_z"] + float(port["boss_height_z"]) if assembly_position else 0.0
        adapter = (
            cq.Workplane("XY")
            .circle(adapter_d / 2)
            .extrude(adapter_h)
            .translate((float(port["x"]), float(port["y"]), z0))
        )
        adapters = adapter if adapters is None else adapters.union(adapter)
    if adapters is None:
        raise ValueError("flow test adapter requires a sample/relief port")
    return adapters


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


def build_gasket_compression_gap_gauge(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    gauge = layout["gasket_compression_gap_gauge"]
    rects = gauge["body_rects"]
    if not assembly_position:
        rects = [
            {
                **rect,
                "x": round(float(rect["x"]) - float(gauge["x"]), 3),
                "y": round(float(rect["y"]) - float(gauge["y"]), 3),
            }
            for rect in rects
        ]
    return _boxes_from_rectangles(rects)


def build_gasket_squeeze_out_of_range_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["gasket_squeeze_out_of_range_review"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


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


def build_latch_retention_span_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["latch_retention_span_check"]
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("latch retention/span check requires rectangles")
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


def build_sensor_installation_path_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["sensor_installation_path_check"]["body_rects"]
    if not rects:
        raise ValueError("sensor installation path check requires at least one sensor")
    z_shift = 0.0 if assembly_position else -min(
        float(rect["z"]) for rect in rects
    )
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_gas_pcb_flow_cell_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["gas_pcb_flow_cell_check"]["flow_cell_rects"]
    if not rects:
        raise ValueError("gas PCB flow-cell check requires at least one flow cell")
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_cots_gas_service_tubes(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    tubes: cq.Workplane | None = None
    for tube in layout["cots_gas_service_tubes"]:
        model = _axis_tube(
            axis=tube["axis"],
            x=float(tube["x"]),
            y=float(tube["y"]),
            z=float(tube["z"]) + z_shift,
            length=float(tube["length"]),
            outer_diameter=float(tube["diameter"]),
            inner_diameter=float(tube["inner_diameter"]),
        )
        tubes = model if tubes is None else tubes.union(model)
    if tubes is None:
        raise ValueError("gas service tubes require at least one tube")
    return tubes


def build_side_gas_tube_envelope_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["side_gas_tube_envelope_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_side_gas_leak_witness_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["side_gas_leak_witness_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_sample_relief_leak_witness_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["sample_relief_leak_witness_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
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


def build_dry_bay_ingress_audit_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["base_top_z"]
    return _boxes_from_rectangles(
        layout["dry_bay_ingress_audit_check"]["body_rects"],
        z_shift=z_shift,
    )


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


def build_latch_mechanism_demo_parts(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> dict[str, cq.Workplane]:
    layout = row_coupon_layout(params)
    demo = params.get("latch_mechanism_demo", {})
    length_x = demo.get("base_length_x", 38.0)
    width_y = demo.get("station_width_y", 42.0)
    lower_h = demo.get("lower_frame_height_z", 8.0)
    gasket_h = demo.get("gasket_height_z", 1.2)
    lid_h = demo.get("lid_receiver_height_z", 6.0)
    lid_gap_z = demo.get("lid_receiver_gap_z", 9.0)
    catch_h = demo.get("catch_lip_height_z", 3.0)
    catch_len = demo.get("catch_lip_length_x", 12.0)
    receiver_h = demo.get("receiver_lip_height_z", 3.0)
    receiver_len = demo.get("receiver_lip_length_x", 12.0)
    wedge_len = demo.get("wedge_length_x", 22.0)
    wedge_low = demo.get("wedge_low_height_z", 2.0)
    wedge_high = demo.get("wedge_high_height_z", 5.0)
    wedge_w = demo.get("wedge_width_y", 22.0)
    wedge_clearance = demo.get("wedge_clearance_z", 0.3)
    handle_w = demo.get("handle_width_y", 12.0)
    handle_h = demo.get("handle_height_z", 8.0)
    stop_w = demo.get("hard_stop_width_x", 2.0)
    witness_w = demo.get("witness_mark_width_x", 1.0)

    origin_x = 0.0
    origin_y = 0.0
    origin_z = 0.0
    if assembly_position:
        origin_x = layout["length_x"] + demo.get("viewer_offset_x", 18.0)
        origin_y = max(0.0, layout["width_y"] - demo.get("viewer_offset_y", 128.0))

    lower_frame = (
        _rounded_box(length_x, width_y, lower_h, 1.2)
        .translate((origin_x, origin_y, origin_z))
        .union(
            cq.Workplane("XY")
            .box(catch_len, width_y, catch_h, centered=(False, False, False))
            .translate((origin_x, origin_y, origin_z + lower_h))
        )
        .union(
            cq.Workplane("XY")
            .box(stop_w, width_y, catch_h + gasket_h, centered=(False, False, False))
            .translate((origin_x + length_x - stop_w, origin_y, origin_z + lower_h))
        )
    )

    gasket = (
        cq.Workplane("XY")
        .box(
            length_x - catch_len - stop_w,
            width_y,
            gasket_h,
            centered=(False, False, False),
        )
        .translate((origin_x + catch_len, origin_y, origin_z + lower_h))
    )

    lid_z = origin_z + lower_h + gasket_h + lid_gap_z
    upper_receiver = (
        _rounded_box(length_x, width_y, lid_h, 1.0)
        .translate((origin_x, origin_y, lid_z))
        .union(
            cq.Workplane("XY")
            .box(receiver_len, width_y, receiver_h, centered=(False, False, False))
            .translate((origin_x + length_x - receiver_len, origin_y, lid_z - receiver_h))
        )
    )

    wedge_x = origin_x + catch_len - 1.0
    wedge_y = origin_y + (width_y - wedge_w) / 2
    wedge_z = origin_z + lower_h + gasket_h + wedge_clearance
    sliding_wedge = (
        cq.Workplane("XZ")
        .polyline(
            [
                (0.0, 0.0),
                (wedge_len, 0.0),
                (wedge_len, wedge_high),
                (0.0, wedge_low),
            ]
        )
        .close()
        .extrude(wedge_w)
        .translate((wedge_x, wedge_y, wedge_z))
    )
    handle_x = wedge_x + wedge_len - stop_w
    sliding_wedge = sliding_wedge.union(
        cq.Workplane("XY")
        .box(stop_w, handle_w, handle_h, centered=(False, False, False))
        .translate(
            (
                handle_x,
                origin_y + (width_y - handle_w) / 2,
                wedge_z + wedge_high,
            )
        )
    )
    sliding_wedge = sliding_wedge.union(
        cq.Workplane("XY")
        .box(witness_w, handle_w, 0.6, centered=(False, False, False))
        .translate(
            (
                handle_x - witness_w,
                origin_y + (width_y - handle_w) / 2,
                wedge_z + wedge_high + handle_h,
            )
        )
    )

    return {
        "latch_demo_lower_catch": lower_frame,
        "latch_demo_compressed_gasket": gasket,
        "latch_demo_upper_receiver": upper_receiver,
        "latch_demo_sliding_wedge": sliding_wedge,
    }


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


def _perimeter_rails(
    *,
    x0: float,
    y0: float,
    length: float,
    width: float,
    rail_width: float,
    height: float,
    z0: float,
) -> cq.Workplane:
    rails: cq.Workplane | None = None
    segments = [
        (x0, y0, length, rail_width),
        (x0, y0 + width - rail_width, length, rail_width),
        (x0, y0 + rail_width, rail_width, width - 2 * rail_width),
        (x0 + length - rail_width, y0 + rail_width, rail_width, width - 2 * rail_width),
    ]
    for x, y, segment_len, segment_wid in segments:
        part = (
            cq.Workplane("XY")
            .box(segment_len, segment_wid, height, centered=(False, False, False))
            .translate((x, y, z0))
        )
        rails = part if rails is None else rails.union(part)
    if rails is None:
        raise ValueError("perimeter rails require at least one segment")
    return rails


def _missing_septum_mat_witness_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
    plate_top_z: float,
) -> list[dict[str, Any]]:
    plate = params["plate"]
    mat = params["septum_mat"]
    production = params.get("production_assembly", {})
    rail_w = production.get("missing_septum_mat_witness_frame_width_xy", 1.2)
    height = production.get("missing_septum_mat_witness_height_z", 0.7)
    z = plate_top_z + mat["sheet_thickness_z"]
    return [
        {
            "tile_index": tile["index"],
            "x": round(float(tile["x"]), 3),
            "y": round(float(tile["y"]), 3),
            "z": round(z, 3),
            "length_x": round(float(plate["length_x"]), 3),
            "width_y": round(float(plate["width_y"]), 3),
            "height_z": round(float(height), 3),
            "rail_width": round(float(rail_w), 3),
            "review_state": "septum_mats_missing",
            "removed_part": "cots_septum_mats",
            "meaning": "mat footprint witness at expected seated septum-mat top plane",
        }
        for tile in tile_origins
    ]


def _missing_microplate_witness_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
    plate_bottom_z: float,
) -> list[dict[str, Any]]:
    plate = params["plate"]
    production = params.get("production_assembly", {})
    rail_w = production.get("missing_microplate_witness_frame_width_xy", 1.2)
    height = production.get("missing_microplate_witness_height_z", 0.7)
    return [
        {
            "tile_index": tile["index"],
            "x": round(float(tile["x"]), 3),
            "y": round(float(tile["y"]), 3),
            "z": round(float(plate_bottom_z), 3),
            "length_x": round(float(plate["length_x"]), 3),
            "width_y": round(float(plate["width_y"]), 3),
            "height_z": round(float(height), 3),
            "rail_width": round(float(rail_w), 3),
            "review_state": "microplates_missing",
            "removed_part": "cots_microplates",
            "dependent_removed_part": "cots_septum_mats",
            "meaning": "microplate footprint witness at expected seated support datum",
        }
        for tile in tile_origins
    ]


def _missing_perimeter_gasket_witness_rectangles(
    *,
    skirt_bounds: dict[str, float],
    params: dict[str, Any],
    base_top_z: float,
    gasket_bottom_z: float,
) -> list[dict[str, Any]]:
    seal = params["seal_interface"]
    rail_w = seal["gasket_rail_width"]
    height = seal["compressed_gasket_height_z"]
    layers = (
        (
            "lower",
            "lower_gasket",
            base_top_z,
            "between_plate_support_frame_and_wet_chamber_frame",
        ),
        (
            "upper",
            "upper_gasket",
            gasket_bottom_z,
            "between_wet_chamber_frame_and_lid_manifold_shell",
        ),
    )
    return [
        {
            "layer": layer,
            "x": round(float(skirt_bounds["x"]), 3),
            "y": round(float(skirt_bounds["y"]), 3),
            "z": round(float(z), 3),
            "length_x": round(float(skirt_bounds["length_x"]), 3),
            "width_y": round(float(skirt_bounds["width_y"]), 3),
            "height_z": round(float(height), 3),
            "rail_width": round(float(rail_w), 3),
            "review_state": "perimeter_gaskets_missing",
            "removed_part": removed_part,
            "interface": interface,
            "meaning": "perimeter seal witness occupying the missing compressed gasket volume",
        }
        for layer, removed_part, z, interface in layers
    ]


def _missing_gas_pcb_cartridge_witness_rectangles(
    *,
    gas_sensor_pcb_mounts: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    rail_w = production.get("missing_gas_pcb_witness_frame_width_xy", 1.0)
    height = production.get("missing_gas_pcb_witness_height_z", 0.7)
    witnesses: list[dict[str, Any]] = []
    for mount in gas_sensor_pcb_mounts:
        witnesses.append(
            {
                "name": f"{mount['role']}_missing_gas_pcb_cartridge_footprint",
                "role": mount["role"],
                "witness_kind": "cartridge_top_footprint",
                "x": mount["x"],
                "y": mount["y"],
                "z": round(float(mount["z"]) + float(mount["height_z"]), 3),
                "length_x": mount["length_x"],
                "width_y": mount["width_y"],
                "height_z": round(float(height), 3),
                "rail_width": round(float(rail_w), 3),
                "review_state": "gas_pcbs_missing",
                "removed_part": "gas_sensor_pcbs",
                "dependent_removed_part": "gas_pcb_interface_gaskets",
                "meaning": "gas PCB cartridge top-footprint witness at expected seated socket",
            }
        )
        gasket_rect = mount["gas_interface"]["gasket_rect"]
        witnesses.append(
            {
                "name": f"{mount['role']}_missing_gas_pcb_interface_gasket",
                "role": mount["role"],
                "witness_kind": "duct_seal_gasket",
                "x": gasket_rect["x"],
                "y": gasket_rect["y"],
                "z": gasket_rect["z"],
                "length_x": gasket_rect["length_x"],
                "width_y": gasket_rect["width_y"],
                "height_z": gasket_rect["height_z"],
                "review_state": "gas_pcbs_missing",
                "removed_part": "gas_pcb_interface_gaskets",
                "dependent_removed_part": "gas_sensor_pcbs",
                "meaning": "missing duct-seal gasket witness at gas PCB sampling interface",
            }
        )
    return witnesses


def _missing_local_sensor_witness_rectangles(
    *,
    headspace_sht41_mounts: list[dict[str, Any]],
    ir_sensor_mounts: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    rail_w = production.get("missing_local_sensor_witness_frame_width_xy", 0.9)
    height = production.get("missing_local_sensor_witness_height_z", 0.7)
    witnesses: list[dict[str, Any]] = []

    for mount in headspace_sht41_mounts:
        witnesses.append(
            {
                "name": f"{mount['name']}_missing_headspace_sht41_carrier",
                "sensor_kind": "headspace_sht41_microcarrier",
                "tile_index": mount["tile_index"],
                "witness_kind": "headspace_sht41_carrier_footprint",
                "review_state": "local_sensors_missing",
                "removed_part": "headspace_sht41_microcarriers",
                "source_rect_name": mount["name"],
                "retention": mount["retention"],
                "x": mount["x"],
                "y": mount["y"],
                "z": round(float(mount["z"]) + float(mount["height_z"]), 3),
                "length_x": mount["length_x"],
                "width_y": mount["width_y"],
                "height_z": round(float(height), 3),
                "rail_width": round(float(rail_w), 3),
                "aperture_x": mount["aperture_x"],
                "aperture_y": mount["aperture_y"],
                "meaning": "missing SHT41 carrier footprint at wet-headspace socket",
            }
        )

    for mount in ir_sensor_mounts:
        witnesses.append(
            {
                "name": f"{mount['name']}_missing_ir_thermopile_body",
                "sensor_kind": "lower_ir_thermopile",
                "tile_index": mount["tile_index"],
                "witness_kind": "ir_thermopile_body_footprint",
                "review_state": "local_sensors_missing",
                "removed_part": "ir_thermopiles",
                "dependent_removed_part": "ir_thermopile_face_gaskets",
                "source_rect_name": mount["name"],
                "retention": mount["retention"],
                "x": mount["x"],
                "y": mount["y"],
                "z": round(float(mount["z"]) + float(mount["height_z"]), 3),
                "length_x": mount["length_x"],
                "width_y": mount["width_y"],
                "height_z": round(float(height), 3),
                "rail_width": round(float(rail_w), 3),
                "aperture_x": mount["aperture_x"],
                "aperture_y": mount["aperture_y"],
                "meaning": "missing lower IR thermopile footprint at dry-side pocket",
            }
        )
        gasket = mount["face_gasket"]
        outer_d = float(gasket["outer_diameter"])
        witnesses.append(
            {
                "name": f"{mount['name']}_missing_ir_face_gasket_seal",
                "sensor_kind": "lower_ir_face_gasket",
                "tile_index": mount["tile_index"],
                "witness_kind": "ir_face_gasket_seal",
                "review_state": "local_sensors_missing",
                "removed_part": "ir_thermopile_face_gaskets",
                "dependent_removed_part": "ir_thermopiles",
                "source_rect_name": mount["name"],
                "center_x": gasket["x"],
                "center_y": gasket["y"],
                "x": round(float(gasket["x"]) - outer_d / 2, 3),
                "y": round(float(gasket["y"]) - outer_d / 2, 3),
                "z": gasket["z"],
                "length_x": round(outer_d, 3),
                "width_y": round(outer_d, 3),
                "height_z": gasket["height_z"],
                "outer_diameter": gasket["outer_diameter"],
                "inner_diameter": gasket["inner_diameter"],
                "nominal_compression_z": gasket["nominal_compression_z"],
                "meaning": "missing IR dry-side face-gasket seal witness",
            }
        )
    return witnesses


def _unseated_gas_pcb_cartridge_review_rectangles(
    layout: dict[str, Any],
    *,
    gas_sensor_pcb_mounts: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    mounts = params.get("sensor_mounts", {})
    install = params.get("sensor_installation", {})
    lift_z = float(install.get("gas_pcb_service_lift_z", 18.0))
    wall = float(mounts.get("gas_pcb_socket_wall_thickness", 1.2))
    door_h = float(install.get("gas_pcb_keeper_door_height_z", 0.8))
    tab_len = float(install.get("gas_pcb_keeper_release_tab_length_y", 4.0))
    tab_w = float(install.get("gas_pcb_keeper_release_tab_width_x", 3.0))

    review_rects: list[dict[str, Any]] = []
    for mount in gas_sensor_pcb_mounts:
        x = float(mount["x"])
        y = float(mount["y"])
        z = float(mount["z"])
        length_x = float(mount["length_x"])
        width_y = float(mount["width_y"])
        height_z = float(mount["height_z"])
        lifted_z = z + lift_z
        door_z = lifted_z + height_z - door_h
        if length_x <= width_y:
            if mount["role"] == "supply":
                tab_x = max(0.0, x - wall - tab_w)
            else:
                tab_x = min(float(layout["length_x"]) - tab_w, x + length_x + wall)
            tab_y = float(mount["aperture_y"]) - tab_len / 2
        else:
            if mount["role"] == "supply":
                tab_y = max(0.0, y - wall - tab_len)
            else:
                tab_y = min(float(layout["width_y"]) - tab_len, y + width_y + wall)
            tab_x = float(mount["aperture_x"]) - tab_w / 2

        review_rects.append(
            {
                "name": f"{mount['role']}_unseated_gas_pcb_cartridge_review",
                "role": mount["role"],
                "owner_part": "unseated_gas_pcb_cartridges_review",
                "review_state": "gas_pcb_cartridges_unseated",
                "review_kind": "lifted_gas_pcb_cartridge",
                "removed_part": "gas_sensor_pcbs",
                "dependent_removed_part": "printed_gas_pcb_keeper_doors",
                "retained_part": "gas_pcb_interface_gaskets",
                "source_rect_name": mount["name"],
                "unseated_offset_z": round(lift_z, 3),
                "x": round(x, 3),
                "y": round(y, 3),
                "z": round(lifted_z, 3),
                "length_x": round(length_x, 3),
                "width_y": round(width_y, 3),
                "height_z": round(height_z, 3),
                "pcb_rect": {
                    "x": round(x, 3),
                    "y": round(y, 3),
                    "z": round(lifted_z, 3),
                    "length_x": round(length_x, 3),
                    "width_y": round(width_y, 3),
                    "height_z": round(height_z, 3),
                },
                "keeper_door_rect": {
                    "x": round(x - wall, 3),
                    "y": round(y - wall, 3),
                    "z": round(door_z, 3),
                    "length_x": round(length_x + 2 * wall, 3),
                    "width_y": round(width_y + 2 * wall, 3),
                    "height_z": round(door_h, 3),
                },
                "keeper_tab_rect": {
                    "x": round(tab_x, 3),
                    "y": round(tab_y, 3),
                    "z": round(door_z, 3),
                    "length_x": round(tab_w, 3),
                    "width_y": round(tab_len, 3),
                    "height_z": round(door_h, 3),
                },
                "meaning": (
                    "gas PCB cartridge is present but lifted off the compressed "
                    "duct sampling gasket"
                ),
            }
        )
    return review_rects


def _missing_service_lead_witness_rectangles(
    *,
    gas_service_tubes: list[dict[str, Any]],
    sensor_service_cable_pigtails: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    rail_w = production.get("missing_service_lead_witness_frame_width_xy", 0.9)
    height = production.get("missing_service_lead_witness_height_z", 0.7)
    span = production.get("missing_service_lead_witness_span_xy", 8.0)
    witnesses: list[dict[str, Any]] = []

    for tube in gas_service_tubes:
        body = tube["body_rect"]
        axis = tube["axis"]
        route = tube["route_axis"]
        if axis == "x":
            length_x = min(float(span), float(body["length_x"]))
            width_y = float(body["width_y"])
            x = float(body["x"])
            if route == "-X":
                x += float(body["length_x"]) - length_x
            y = float(body["y"])
        elif axis == "y":
            length_x = float(body["length_x"])
            width_y = min(float(span), float(body["width_y"]))
            x = float(body["x"])
            y = float(body["y"])
            if route == "-Y":
                y += float(body["width_y"]) - width_y
        else:
            raise ValueError("gas service lead witness requires x or y axis")
        witnesses.append(
            {
                "name": f"{tube['role']}_missing_gas_service_lead_handoff",
                "service_kind": "gas_tube",
                "role": tube["role"],
                "witness_kind": "gas_tube_handoff",
                "removed_part": "cots_gas_service_tubes",
                "review_state": "service_leads_missing",
                "x": round(x, 3),
                "y": round(y, 3),
                "z": round(float(body["z"]) + float(body["height_z"]), 3),
                "length_x": round(length_x, 3),
                "width_y": round(width_y, 3),
                "height_z": round(height, 3),
                "rail_width": round(rail_w, 3),
                "source_rect_name": tube["name"],
                "route_axis": route,
                "meaning": "missing COTS gas tube at printed side fitting handoff",
            }
        )

    for pigtail in sensor_service_cable_pigtails:
        connector_name = str(pigtail["connector_name"])
        removed_part = (
            "lower_sensor_service_cable_pigtail"
            if connector_name.startswith("lower_")
            else "lid_sensor_service_cable_pigtails"
        )
        width_y = min(float(span), float(pigtail["width_y"]))
        witnesses.append(
            {
                "name": f"{connector_name}_missing_electrical_service_lead_handoff",
                "service_kind": "electrical_cable",
                "role": connector_name,
                "witness_kind": "electrical_cable_handoff",
                "removed_part": removed_part,
                "review_state": "service_leads_missing",
                "x": round(float(pigtail["x"]), 3),
                "y": round(float(pigtail["y"]), 3),
                "z": round(float(pigtail["z"]) + float(pigtail["height_z"]), 3),
                "length_x": round(float(pigtail["length_x"]), 3),
                "width_y": round(width_y, 3),
                "height_z": round(height, 3),
                "rail_width": round(rail_w, 3),
                "source_rect_name": pigtail["name"],
                "route_axis": pigtail["route_axis"],
                "meaning": "missing COTS electrical cable pigtail at keyed connector handoff",
            }
        )
    return witnesses


def _electrical_service_part_names(connector_name: str) -> tuple[str, str]:
    if connector_name.startswith("lower_"):
        return "lower_sensor_service_connector", "lower_sensor_service_cable_pigtail"
    return "lid_sensor_service_connectors", "lid_sensor_service_cable_pigtails"


def _review_rect(
    source: dict[str, Any],
    *,
    connector: dict[str, Any],
    review_kind: str,
    y_offset: float = 0.0,
    height_z: float | None = None,
    z: float | None = None,
    name_suffix: str | None = None,
) -> dict[str, Any]:
    connector_part, pigtail_part = _electrical_service_part_names(
        str(connector["name"]),
    )
    return {
        "name": f"{connector['name']}_{name_suffix or review_kind}",
        "connector_name": connector["name"],
        "connector_family": connector["connector_family"],
        "review_state": "electrical_connectors_unmated",
        "review_kind": review_kind,
        "removed_connector_part": connector_part,
        "removed_pigtail_part": pigtail_part,
        "unmated_offset_y": round(y_offset, 3),
        "x": round(float(source["x"]), 3),
        "y": round(float(source["y"]) + y_offset, 3),
        "z": round(float(source["z"] if z is None else z), 3),
        "length_x": round(float(source["length_x"]), 3),
        "width_y": round(float(source["width_y"]), 3),
        "height_z": round(float(source["height_z"] if height_z is None else height_z), 3),
    }


def _unmated_sensor_service_connector_review_rectangles(
    *,
    connectors: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    witness_h = production.get("missing_service_lead_witness_height_z", 0.7)
    witness_w = min(
        production.get("missing_service_lead_witness_span_xy", 8.0),
        1.2,
    )
    rects: list[dict[str, Any]] = []

    for connector in connectors:
        service_clearance = connector["service_clearance_rect"]
        y_offset = max(
            float(connector["plug_rect"]["width_y"]) + witness_w,
            float(service_clearance["width_y"]) * 0.5,
        )
        y_offset = min(
            y_offset,
            max(
                float(service_clearance["width_y"])
                - float(connector["plug_rect"]["width_y"]),
                float(connector["plug_rect"]["width_y"]),
            ),
        )

        rects.append(
            _review_rect(
                connector["board_rect"],
                connector=connector,
                review_kind="stationary_service_board",
            )
        )
        rects.append(
            _review_rect(
                connector["header_rect"],
                connector=connector,
                review_kind="stationary_header",
            )
        )
        rects.append(
            _review_rect(
                connector["plug_rect"],
                connector=connector,
                review_kind="unmated_plug",
                y_offset=y_offset,
            )
        )
        rects.append(
            _review_rect(
                connector["latch_rect"],
                connector=connector,
                review_kind="unmated_latch",
                y_offset=y_offset,
            )
        )
        rects.append(
            _review_rect(
                connector["installed_cable_pigtail_rect"],
                connector=connector,
                review_kind="unmated_cable_pigtail",
                y_offset=y_offset,
            )
        )

        header = connector["header_rect"]
        witness_z = (
            max(
                float(connector["header_rect"]["z"]) + float(connector["header_rect"]["height_z"]),
                float(connector["plug_rect"]["z"]) + float(connector["plug_rect"]["height_z"]),
            )
            + 0.05
        )
        witness = {
            "x": header["x"],
            "y": round(float(connector["plug_rect"]["y"]), 3),
            "z": round(witness_z, 3),
            "length_x": header["length_x"],
            "width_y": round(witness_w, 3),
            "height_z": round(witness_h, 3),
        }
        rects.append(
            _review_rect(
                witness,
                connector=connector,
                review_kind="mating_gap_witness",
                height_z=witness_h,
            )
        )

    return rects


def _pod_frame_key_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, float | int]]:
    production = params.get("production_assembly", {})
    key_len = production.get("pod_frame_key_length_x", 3.2)
    key_wid = production.get("pod_frame_key_width_y", 5.2)
    keys: list[dict[str, float | int]] = []

    for foot in _deck_engagement_foot_rectangles(
        tile_origins=tile_origins,
        params=params,
    ):
        length = min(key_len, float(foot["length_x"]))
        width = min(key_wid, float(foot["width_y"]))
        keys.append(
            {
                "tile_index": foot["tile_index"],
                "x": round(float(foot["x"]) + (float(foot["length_x"]) - length) / 2, 3),
                "y": round(float(foot["y"]) + (float(foot["width_y"]) - width) / 2, 3),
                "length_x": round(length, 3),
                "width_y": round(width, 3),
            }
        )
    return keys


def _add_pod_frame_keys(
    model: cq.Workplane,
    *,
    tile: dict[str, Any],
    params: dict[str, Any],
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    key_h = production.get("pod_frame_key_height_z", 1.6)
    if key_h <= 0:
        return model

    for key in _pod_frame_key_rectangles(tile_origins=[tile], params=params):
        model = model.union(
            _rounded_box(
                float(key["length_x"]),
                float(key["width_y"]),
                key_h,
                min(float(key["length_x"]), float(key["width_y"])) / 6,
            ).translate((float(key["x"]), float(key["y"]), 0.0))
        )
    return model


def _cut_pod_frame_key_pockets(
    model: cq.Workplane,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    key_h = production.get("pod_frame_key_height_z", 1.6)
    clearance = production.get("pod_frame_key_clearance_xy", 0.25)
    pocket_extra_z = production.get("pod_frame_key_pocket_extra_z", 0.2)
    if key_h <= 0:
        return model

    for key in _pod_frame_key_rectangles(
        tile_origins=layout["tile_origins"],
        params=params,
    ):
        model = model.cut(
            cq.Workplane("XY")
            .box(
                float(key["length_x"]) + 2 * clearance,
                float(key["width_y"]) + 2 * clearance,
                key_h + pocket_extra_z + 0.1,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(key["x"]) - clearance,
                    float(key["y"]) - clearance,
                    -0.05,
                )
            )
        )
    return model


def _add_gasket_service_tabs(
    gasket: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    production = params.get("production_assembly", {})
    tab_len = production.get("gasket_service_tab_length_x", 0.0)
    tab_depth = production.get("gasket_service_tab_depth_y", 0.0)
    if tab_len <= 0 or tab_depth <= 0:
        return gasket

    rail_w = seal["gasket_rail_width"]
    rail_h = seal["compressed_gasket_height_z"]
    x0 = (layout["length_x"] - tab_len) / 2
    y_values = [
        rail_w,
        layout["width_y"] - rail_w - tab_depth,
    ]
    for y in y_values:
        gasket = gasket.union(
            cq.Workplane("XY")
            .box(tab_len, tab_depth, rail_h, centered=(False, False, False))
            .translate((x0, y, z0))
        )
    return gasket


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


def _cut_gasket_capture_groove(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
    from_side: str,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    production = params.get("production_assembly", {})
    depth = production.get("gasket_capture_depth_z", 0.0)
    clearance = production.get("gasket_capture_clearance_xy", 0.0)
    outer_land = min(
        production.get("gasket_capture_outer_land_xy", 0.8),
        seal["gasket_rail_width"] - 0.2,
    )
    if depth <= 0:
        return model
    if from_side not in {"top", "bottom"}:
        raise ValueError("gasket capture groove side must be top or bottom")

    groove_z = z0 - depth if from_side == "top" else z0 - 0.05
    cutter = _perimeter_rails(
        x0=outer_land,
        y0=outer_land,
        length=layout["length_x"] - 2 * outer_land,
        width=layout["width_y"] - 2 * outer_land,
        rail_width=seal["gasket_rail_width"] - outer_land + clearance,
        height=depth + 0.1,
        z0=groove_z,
    )
    return model.cut(cutter)


def _lid_cover_tongue_ring(
    *,
    params: dict[str, Any],
    z0: float,
    width_extra: float = 0.0,
) -> cq.Workplane | None:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    tongue_w = production.get("lid_cover_tongue_width", 0.0) + width_extra
    tongue_d = production.get("lid_cover_tongue_depth_z", 0.0)
    if tongue_w <= 0 or tongue_d <= 0:
        return None

    inset = params["wet_chamber_skirt"]["wall_thickness"] + 0.6 - width_extra / 2
    length = layout["length_x"] - 2 * inset
    width = layout["width_y"] - 2 * inset
    if length <= 2 * tongue_w or width <= 2 * tongue_w:
        return None
    return _perimeter_rails(
        x0=inset,
        y0=inset,
        length=length,
        width=width,
        rail_width=tongue_w,
        height=tongue_d,
        z0=z0,
    )


def _add_lid_cover_tongue(
    cover: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    tongue_d = production.get("lid_cover_tongue_depth_z", 0.0)
    ring = _lid_cover_tongue_ring(params=params, z0=z0 - tongue_d)
    if ring is None:
        return cover
    return cover.union(ring)


def _cut_lid_cover_tongue_groove(
    shell: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    tongue_d = production.get("lid_cover_tongue_depth_z", 0.0)
    clearance = production.get("lid_cover_tongue_clearance_xy", 0.0)
    if tongue_d <= 0:
        return shell

    groove = _lid_cover_tongue_ring(
        params=params,
        z0=z0 + params["lid_manifold"]["thickness_z"] - tongue_d - 0.05,
        width_extra=2 * clearance,
    )
    if groove is None:
        return shell
    return shell.cut(groove)


def _wedge_profile_points(
    lock_rect: dict[str, float | str],
    params: dict[str, Any],
) -> list[tuple[float, float]]:
    production = params.get("production_assembly", {})
    length = float(
        lock_rect["length_x"]
        if lock_rect["slide_axis"] == "x"
        else lock_rect["width_y"]
    )
    low_h = production.get("wedge_lock_low_height_z", 0.0)
    high_h = float(lock_rect["height_z"])
    lead_in = min(
        max(production.get("wedge_lock_lead_in_length_x", 0.0), 0.0),
        max(length / 3, 0.0),
    )
    bearing_flat = min(
        max(production.get("wedge_lock_bearing_flat_length_x", 0.0), 0.0),
        max(length - lead_in - 0.4, 0.0),
    )
    if lock_rect["insert_from"] == "min":
        flat_start = length - bearing_flat
        return [
            (0.0, 0.0),
            (length, 0.0),
            (length, high_h),
            (flat_start, high_h),
            (lead_in, low_h),
            (0.0, low_h),
        ]

    flat_end = bearing_flat
    lead_end = length - lead_in
    return [
        (0.0, 0.0),
        (length, 0.0),
        (length, low_h),
        (lead_end, low_h),
        (flat_end, high_h),
        (0.0, high_h),
    ]


def _build_wedge_lock_body(
    lock_rect: dict[str, float | str],
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    profile = _wedge_profile_points(lock_rect, params)
    if lock_rect["slide_axis"] == "x":
        lock = (
            cq.Workplane("XZ")
            .polyline(profile)
            .close()
            .extrude(-float(lock_rect["width_y"]))
            .translate((float(lock_rect["x"]), float(lock_rect["y"]), z0))
        )
    else:
        lock = (
            cq.Workplane("YZ")
            .polyline(profile)
            .close()
            .extrude(float(lock_rect["length_x"]))
            .translate((float(lock_rect["x"]), float(lock_rect["y"]), z0))
        )
    lock = _cut_latch_post_slot(lock, lock_rect, params=params, z0=z0)
    return _add_wedge_release_detent_and_witness_features(
        lock,
        lock_rect,
        params=params,
        z0=z0,
    )


def _production_latch_slide_length(params: dict[str, Any], *, row_axis: str) -> float:
    production = params.get("production_assembly", {})
    if row_axis == "y":
        return production.get("wedge_lock_width_x", 0.0)
    return production.get("wedge_lock_length_y", 0.0)


def _latch_mechanical_screens(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_stop_positions: list[tuple[float, float]],
    wedge_lock_rectangles: list[dict[str, float | str]],
) -> dict[str, dict[str, Any]]:
    production = params.get("production_assembly", {})
    mechanics = params.get("latch_mechanics", {})
    seal = params["seal_interface"]
    row_axis = layout["row_axis"]

    wedge_length = _production_latch_slide_length(params, row_axis=row_axis)
    lead_in = production.get("wedge_lock_lead_in_length_x", 0.0)
    bearing_flat = production.get("wedge_lock_bearing_flat_length_x", 0.0)
    wedge_low = production.get("wedge_lock_low_height_z", 0.0)
    wedge_high = production.get("wedge_lock_height_z", 0.0)
    ramp_rise = max(0.0, wedge_high - wedge_low)
    ramp_run = max(0.0, wedge_length - lead_in - bearing_flat)
    ramp_angle_deg = math.degrees(math.atan2(ramp_rise, ramp_run)) if ramp_run > 0 else 90.0

    tolerance_z = mechanics.get("latch_tolerance_allowance_z", 0.0)
    available_squeeze = max(0.0, ramp_rise - tolerance_z)
    squeeze_min = mechanics.get("gasket_squeeze_min_z", 0.0)
    squeeze_target = mechanics.get("gasket_squeeze_target_z", 0.0)
    squeeze_max = mechanics.get("gasket_squeeze_max_z", seal["compressed_gasket_height_z"])
    hard_stop_limit = min(squeeze_max, seal["compressed_gasket_height_z"])
    bounded_squeeze = min(available_squeeze, squeeze_target, hard_stop_limit)
    compression_budget = {
        "source": "production_assembly",
        "wedge_length_mm": round(wedge_length, 3),
        "ramp_rise_mm": round(ramp_rise, 3),
        "ramp_run_mm": round(ramp_run, 3),
        "tolerance_allowance_z": round(tolerance_z, 3),
        "available_squeeze_z": round(available_squeeze, 3),
        "gasket_squeeze_min_z": round(squeeze_min, 3),
        "gasket_squeeze_target_z": round(squeeze_target, 3),
        "gasket_squeeze_max_z": round(squeeze_max, 3),
        "hard_stop_limit_z": round(hard_stop_limit, 3),
        "bounded_squeeze_z": round(bounded_squeeze, 3),
        "min_squeeze_margin_z": round(bounded_squeeze - squeeze_min, 3),
        "target_squeeze_margin_z": round(available_squeeze - squeeze_target, 3),
        "overcompression_margin_z": round(squeeze_max - bounded_squeeze, 3),
        "passes_budget": (
            available_squeeze >= squeeze_target
            and squeeze_min <= bounded_squeeze <= squeeze_max
            and bounded_squeeze <= hard_stop_limit
        ),
    }

    mu_min = mechanics.get("friction_coefficient_min", 0.0)
    friction_angle_deg = math.degrees(math.atan(mu_min)) if mu_min > 0 else 0.0
    self_lock_margin_deg = friction_angle_deg - ramp_angle_deg
    min_margin_deg = mechanics.get("self_lock_min_margin_deg", 0.0)
    passes_self_lock = self_lock_margin_deg >= 0.0
    meets_margin = self_lock_margin_deg >= min_margin_deg
    ramp_self_lock = {
        "source": "production_assembly",
        "ramp_angle_deg": round(ramp_angle_deg, 3),
        "friction_coefficient_min": round(mu_min, 3),
        "friction_angle_deg": round(friction_angle_deg, 3),
        "self_lock_margin_deg": round(self_lock_margin_deg, 3),
        "self_lock_min_margin_deg": round(min_margin_deg, 3),
        "passes_self_lock": passes_self_lock,
        "meets_min_margin": meets_margin,
        "backdrive_risk_flag": not meets_margin,
        "retention_status": (
            "geometry_margin_ok" if meets_margin else "detent_or_physical_test_required"
        ),
    }

    post_d = production.get("latch_post_diameter", 0.0)
    clamp_force_n = mechanics.get("expected_clamp_force_per_latch_n", 0.0)
    allowable_mpa = mechanics.get("allowable_wet_polymer_stress_mpa", 0.0)
    shaft_area = math.pi * (post_d / 2) ** 2 if post_d > 0 else 0.0
    shaft_stress = clamp_force_n / shaft_area if shaft_area > 0 else float("inf")
    shaft_safety_factor = allowable_mpa / shaft_stress if shaft_stress > 0 else 0.0
    min_sf = mechanics.get("stress_safety_factor_min", 1.0)
    bearing_area = bearing_flat * production.get("wedge_lock_length_y", 0.0)
    root_area = (
        production.get("latch_post_root_gusset_length_x", 0.0)
        * production.get("latch_post_root_gusset_width_y", 0.0)
    )
    min_bearing_area = mechanics.get("min_cap_bearing_area_mm2", 0.0)
    min_root_area = mechanics.get("min_root_pad_area_mm2", 0.0)
    cap_bearing_stress = clamp_force_n / bearing_area if bearing_area > 0 else float("inf")
    root_bearing_stress = clamp_force_n / root_area if root_area > 0 else float("inf")
    post_stress_screen = {
        "source": "production_assembly",
        "expected_clamp_force_per_latch_n": round(clamp_force_n, 3),
        "post_diameter_mm": round(post_d, 3),
        "shaft_area_mm2": round(shaft_area, 3),
        "shaft_stress_mpa": round(shaft_stress, 3),
        "allowable_wet_polymer_stress_mpa": round(allowable_mpa, 3),
        "shaft_safety_factor": round(shaft_safety_factor, 3),
        "stress_safety_factor_min": round(min_sf, 3),
        "cap_bearing_area_mm2": round(bearing_area, 3),
        "cap_bearing_stress_mpa": round(cap_bearing_stress, 3),
        "min_cap_bearing_area_mm2": round(min_bearing_area, 3),
        "root_pad_area_mm2": round(root_area, 3),
        "root_bearing_stress_mpa": round(root_bearing_stress, 3),
        "min_root_pad_area_mm2": round(min_root_area, 3),
        "passes_stress_screen": (
            shaft_safety_factor >= min_sf
            and bearing_area >= min_bearing_area
            and root_area >= min_root_area
        ),
    }

    station_asymmetry = _latch_station_asymmetry_screen(
        layout,
        params=params,
        compression_stop_positions=compression_stop_positions,
        wedge_lock_rectangles=wedge_lock_rectangles,
    )
    return {
        "compression_budget": compression_budget,
        "ramp_self_lock": ramp_self_lock,
        "post_stress_screen": post_stress_screen,
        "station_asymmetry": station_asymmetry,
    }


def _assembly_state_witness_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_port_positions: list[dict[str, Any]],
    wedge_lock_rectangles: list[dict[str, Any]],
    missing_microplate_witnesses: list[dict[str, Any]],
    missing_septum_mat_witnesses: list[dict[str, Any]],
    missing_perimeter_gasket_witnesses: list[dict[str, Any]],
    missing_gas_pcb_cartridge_witnesses: list[dict[str, Any]],
    unseated_gas_pcb_cartridges_review: list[dict[str, Any]],
    missing_local_sensor_witnesses: list[dict[str, Any]],
    missing_service_lead_witnesses: list[dict[str, Any]],
    unseated_side_gas_tubes_review: list[dict[str, Any]],
    lid_top_z: float,
) -> dict[str, Any]:
    production = params.get("production_assembly", {})
    lid = params["lid_manifold"]
    sample_ports = [port for port in lid_port_positions if port["role"] == "sample_relief"]
    cap_ring_w = float(
        production.get("sample_relief_cap_missing_witness_ring_width_xy", 0.8)
    )
    cap_witness_h = float(
        production.get("sample_relief_cap_missing_witness_height_z", 0.6)
    )
    flag_len = float(
        production.get("sample_relief_cap_missing_witness_flag_length_xy", 6.0)
    )
    flag_w = float(
        production.get("sample_relief_cap_missing_witness_flag_width_xy", 1.4)
    )
    latch_witness_h = float(production.get("wedge_unseated_witness_height_z", 0.6))
    latch_z = (
        float(lid_top_z)
        + float(lid["duct_height_z"])
        + float(production.get("wedge_lock_height_z", 0.0))
    )
    latch_unseated_rects = [
        {
            "name": f"latch_unseated_witness_{index:02d}",
            "x": lock["bearing_flat_x"],
            "y": lock["bearing_flat_y"],
            "z": round(latch_z, 3),
            "length_x": lock["bearing_flat_length_x"],
            "width_y": lock["bearing_flat_width_y"],
            "height_z": round(latch_witness_h, 3),
            "review_state": "latches_unseated",
            "removed_part": "printed_wedge_locks",
        }
        for index, lock in enumerate(wedge_lock_rectangles, start=1)
    ]
    sample_relief_cap_witnesses: list[dict[str, Any]] = []
    sample_relief_flag_rects: list[dict[str, Any]] = []
    for port in sample_ports:
        inner_d = float(port["cap_flange_diameter"])
        outer_d = inner_d + 2 * cap_ring_w
        z0 = float(lid_top_z) + float(port["boss_height_z"])
        side = 1 if float(port["x"]) <= float(layout["length_x"]) / 2 else -1
        if side > 0:
            flag_x = float(port["x"]) + outer_d / 2 - 0.1
        else:
            flag_x = float(port["x"]) - outer_d / 2 - flag_len + 0.1
        flag_rect = {
            "name": f"{port['name']}_missing_cap_witness_flag",
            "x": round(flag_x, 3),
            "y": round(float(port["y"]) - flag_w / 2, 3),
            "z": round(z0, 3),
            "length_x": round(flag_len, 3),
            "width_y": round(flag_w, 3),
            "height_z": round(cap_witness_h, 3),
            "review_state": "sample_relief_cap_missing",
            "removed_part": "printed_sample_relief_cap",
        }
        sample_relief_flag_rects.append(flag_rect)
        sample_relief_cap_witnesses.append(
            {
                "name": f"{port['name']}_missing_cap_witness_ring",
                "port_name": port["name"],
                "review_state": "sample_relief_cap_missing",
                "removed_part": "printed_sample_relief_cap",
                "center_x": round(float(port["x"]), 3),
                "center_y": round(float(port["y"]), 3),
                "z": round(z0, 3),
                "inner_diameter": round(inner_d, 3),
                "outer_diameter": round(outer_d, 3),
                "height_z": round(cap_witness_h, 3),
                "flag_rect": flag_rect,
            }
        )

    body_rects = [
        *missing_microplate_witnesses,
        *missing_septum_mat_witnesses,
        *missing_perimeter_gasket_witnesses,
        *missing_gas_pcb_cartridge_witnesses,
        *(rect["pcb_rect"] for rect in unseated_gas_pcb_cartridges_review),
        *missing_local_sensor_witnesses,
        *missing_service_lead_witnesses,
        *(spec["body_rect"] for spec in unseated_side_gas_tubes_review),
        *latch_unseated_rects,
        *sample_relief_flag_rects,
    ]
    source_review_parts = [
        "missing_sample_relief_cap_witness",
        "latch_unseated_witnesses",
        "missing_septum_mat_witnesses",
        "missing_microplate_witnesses",
        "missing_perimeter_gasket_witnesses",
        "missing_gas_pcb_cartridge_witnesses",
        "unseated_gas_pcb_cartridges_review",
        "missing_local_sensor_witnesses",
        "missing_service_lead_witnesses",
        "unseated_side_gas_tubes_review",
    ]
    plate_count = len(missing_microplate_witnesses)
    local_sensor_count = sum(
        1
        for witness in missing_local_sensor_witnesses
        if witness["witness_kind"]
        in {"headspace_sht41_carrier_footprint", "ir_thermopile_body_footprint"}
    )
    return {
        "name": "assembly_state_witness_check",
        "role": "validation-only dry assembly negative-state witness composite",
        "validation": "required_gate2_dry_assembly_state_evidence",
        "failure_rule": (
            "missing_consumable_cap_service_or_latch_state_blocks_dry_assembly_pass"
        ),
        "evidence_gate": "Gate 2 dry assembly",
        "cad_value": (
            f"{plate_count} plates / {len(missing_septum_mat_witnesses)} mats / "
            f"{len(missing_perimeter_gasket_witnesses)} gaskets / "
            f"{len(missing_gas_pcb_cartridge_witnesses)} gas PCB / "
            f"{len(unseated_gas_pcb_cartridges_review)} unseated gas PCB / "
            f"{local_sensor_count} local sensors / "
            f"{len(missing_service_lead_witnesses)} service leads / "
            f"{len(unseated_side_gas_tubes_review)} unseated gas tubes / "
            f"{len(sample_relief_cap_witnesses)} cap / "
            f"{len(latch_unseated_rects)} latches"
        ),
        "stack_cad_value": (
            f"{plate_count} plates / {len(missing_septum_mat_witnesses)} mats / "
            f"{len(missing_perimeter_gasket_witnesses)} perimeter gaskets"
        ),
        "plate_count": plate_count,
        "septum_mat_count": len(missing_septum_mat_witnesses),
        "perimeter_gasket_count": len(missing_perimeter_gasket_witnesses),
        "gas_pcb_cartridge_count": len(missing_gas_pcb_cartridge_witnesses),
        "unseated_gas_pcb_cartridge_review_count": len(
            unseated_gas_pcb_cartridges_review
        ),
        "local_sensor_module_count": local_sensor_count,
        "local_sensor_witness_count": len(missing_local_sensor_witnesses),
        "service_lead_witness_count": len(missing_service_lead_witnesses),
        "unseated_side_gas_tube_review_count": len(unseated_side_gas_tubes_review),
        "sample_relief_cap_witness_count": len(sample_relief_cap_witnesses),
        "latch_unseated_witness_count": len(latch_unseated_rects),
        "source_review_parts": source_review_parts,
        "source_layout_checks": [
            "missing_microplate_witnesses",
            "missing_septum_mat_witnesses",
            "missing_perimeter_gasket_witnesses",
            "missing_gas_pcb_cartridge_witnesses",
            "unseated_gas_pcb_cartridges_review",
            "missing_local_sensor_witnesses",
            "missing_service_lead_witnesses",
            "unseated_side_gas_tubes_review",
            "wedge_lock_rectangles",
            "lid_port_positions",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "installed_dry_stack_complete",
            "sample_relief_cap_installed_and_seated",
            "latches_seated_before_wet_tests",
            "gas_pcb_cartridges_installed_for_dry_fit",
            "gas_pcb_cartridges_seated_to_duct_gaskets",
            "local_headspace_and_ir_sensors_installed",
            "service_leads_connected_for_operating_state",
            "side_gas_tubes_seated_on_barbs",
            "normal_ot2_operation",
        ],
        "body_rects": body_rects,
        "sample_relief_cap_witnesses": sample_relief_cap_witnesses,
        "latch_unseated_rects": latch_unseated_rects,
    }


def _gasket_compression_gap_gauge_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_budget: dict[str, Any],
) -> dict[str, Any]:
    mechanics = params.get("latch_mechanics", {})
    metrology = params.get("consumable_metrology", {})
    blade_len = float(mechanics.get("gasket_compression_gauge_blade_length_x", 26.0))
    blade_width = float(mechanics.get("gasket_compression_gauge_blade_width_y", 5.0))
    blade_gap = float(mechanics.get("gasket_compression_gauge_blade_gap_y", 2.0))
    length_step = float(mechanics.get("gasket_compression_gauge_length_step_x", 5.0))
    x0 = float(layout["length_x"]) + float(metrology.get("viewer_offset_x", 18.0))

    blade_sources = [
        (
            "minimum_squeeze_blade",
            "minimum_gasket_squeeze_reference",
            float(compression_budget["gasket_squeeze_min_z"]),
        ),
        (
            "target_squeeze_blade",
            "target_gasket_squeeze_reference",
            float(compression_budget["gasket_squeeze_target_z"]),
        ),
        (
            "maximum_squeeze_blade",
            "maximum_gasket_squeeze_reference",
            float(compression_budget["gasket_squeeze_max_z"]),
        ),
    ]
    blades = [
        {
            "name": name,
            "role": role,
            "x": 0.0,
            "y": round(index * (blade_width + blade_gap), 3),
            "z": 0.0,
            "length_x": round(blade_len + index * length_step, 3),
            "width_y": round(blade_width, 3),
            "thickness_z": round(thickness, 3),
        }
        for index, (name, role, thickness) in enumerate(blade_sources)
    ]
    total_width = blade_width * len(blades) + blade_gap * max(0, len(blades) - 1)
    body_rects = [
        {
            **blade,
            "x": round(x0 + float(blade["x"]), 3),
            "y": round(float(blade["y"]), 3),
            "height_z": blade["thickness_z"],
        }
        for blade in blades
    ]
    return {
        "name": "gasket_compression_gap_gauge",
        "role": "dry_assembly_gasket_squeeze_gap_reference",
        "source": "latch_compression_budget",
        "evidence_gate": "Gate 2 dry assembly",
        "failure_rule": "gasket_squeeze_out_of_range_blocks_dry_assembly_pass",
        "cad_value": (
            f"{float(compression_budget['gasket_squeeze_target_z']):.2f} mm target / "
            f"{float(compression_budget['gasket_squeeze_min_z']):.2f}.."
            f"{float(compression_budget['gasket_squeeze_max_z']):.2f} mm allowed"
        ),
        "x": round(x0, 3),
        "y": 0.0,
        "blade_count": len(blades),
        "blade_length_x": round(blade_len, 3),
        "blade_width_y": round(blade_width, 3),
        "blade_gap_y": round(blade_gap, 3),
        "length_step_x": round(length_step, 3),
        "total_width_y": round(total_width, 3),
        "min_squeeze_z": compression_budget["gasket_squeeze_min_z"],
        "target_squeeze_z": compression_budget["gasket_squeeze_target_z"],
        "max_squeeze_z": compression_budget["gasket_squeeze_max_z"],
        "bounded_squeeze_z": compression_budget["bounded_squeeze_z"],
        "blades": blades,
        "validation": "physical_gap_blades_require_printed_gate2_measurement",
        "source_layout_checks": ["latch_compression_budget"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "gasket_compression_in_range",
            "sealed_wet_headspace_perimeter",
            "latches_seated_before_wet_tests",
            "wet_operation_without_gasket_overcrush",
        ],
        "body_rects": body_rects,
    }


def _gasket_squeeze_out_of_range_review_rectangles(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_stop_positions: list[tuple[float, float]],
    compression_budget: dict[str, Any],
    base_top_z: float,
) -> list[dict[str, Any]]:
    seal = params["seal_interface"]
    mechanics = params.get("latch_mechanics", {})
    production = params.get("production_assembly", {})
    witness_size = min(
        float(production.get("gasket_squeeze_review_size_xy", 3.0)),
        float(seal["compression_stop_size"]) * 0.8,
    )
    witness_gap = float(production.get("gasket_squeeze_review_gap_xy", 0.8))
    overcrush_h = max(
        float(mechanics.get("gasket_squeeze_review_overcrush_height_z", 0.08)),
        float(compression_budget["gasket_squeeze_min_z"]) * 0.5,
    )
    undersqueeze_h = float(compression_budget["gasket_squeeze_max_z"]) + float(
        mechanics.get("gasket_squeeze_review_undersqueeze_extra_z", 0.35)
    )
    layout_len = float(layout["length_x"])
    layout_wid = float(layout["width_y"])

    def bounded_origin(center: float, size: float, *, positive: bool, limit: float) -> float:
        raw = center + witness_gap / 2 if positive else center - witness_gap / 2 - size
        return max(0.0, min(limit - size, raw))

    rects: list[dict[str, Any]] = []
    source_checks = [
        "gasket_compression_gap_gauge",
        "latch_retention_span_check",
        "assembly_state_witness_check",
    ]
    for index, (stop_x, stop_y) in enumerate(compression_stop_positions, start=1):
        base = {
            "review_state": "gasket_squeeze_out_of_range",
            "owner_part": "gasket_squeeze_out_of_range_review",
            "retained_part": "lower_gasket_and_upper_gasket",
            "blocked_fail_closed_state": "gasket_squeeze_out_of_range",
            "source_validation_checks": source_checks,
            "stop_index": index,
            "stop_x": round(float(stop_x), 3),
            "stop_y": round(float(stop_y), 3),
            "allowed_min_squeeze_z": compression_budget["gasket_squeeze_min_z"],
            "allowed_max_squeeze_z": compression_budget["gasket_squeeze_max_z"],
        }
        y0 = max(0.0, min(layout_wid - witness_size, float(stop_y) - witness_size / 2))
        rects.extend(
            [
                {
                    **base,
                    "name": f"compression_stop_{index:02d}_overcrush_review",
                    "review_kind": "gasket_overcompressed_below_min_gap",
                    "measured_squeeze_relation": "above_allowed_max_squeeze",
                    "x": round(
                        bounded_origin(
                            float(stop_x),
                            witness_size,
                            positive=False,
                            limit=layout_len,
                        ),
                        3,
                    ),
                    "y": round(y0, 3),
                    "z": round(float(base_top_z), 3),
                    "length_x": round(witness_size, 3),
                    "width_y": round(witness_size, 3),
                    "height_z": round(overcrush_h, 3),
                },
                {
                    **base,
                    "name": f"compression_stop_{index:02d}_undersqueeze_review",
                    "review_kind": "gasket_undercompressed_above_max_gap",
                    "measured_squeeze_relation": "below_allowed_min_squeeze",
                    "x": round(
                        bounded_origin(
                            float(stop_x),
                            witness_size,
                            positive=True,
                            limit=layout_len,
                        ),
                        3,
                    ),
                    "y": round(y0, 3),
                    "z": round(float(base_top_z), 3),
                    "length_x": round(witness_size, 3),
                    "width_y": round(witness_size, 3),
                    "height_z": round(undersqueeze_h, 3),
                },
            ]
        )
    return rects


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


def _latch_retention_span_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_budget: dict[str, Any],
    ramp_self_lock: dict[str, Any],
    post_stress_screen: dict[str, Any],
    station_asymmetry: dict[str, Any],
    wedge_lock_rectangles: list[dict[str, float | str]],
) -> dict[str, Any]:
    metrology = params.get("consumable_metrology", {})
    check_params = params.get("latch_retention_span_check", {})
    slab_len = float(check_params.get("length_x", 60.0))
    slab_wid = float(check_params.get("width_y", 62.0))
    slab_h = float(check_params.get("height_z", 0.45))
    x0 = (
        float(layout["length_x"])
        + float(metrology.get("viewer_offset_x", 18.0))
        + float(check_params.get("viewer_offset_x", 178.0))
    )
    y0 = (float(layout["width_y"]) - slab_wid) / 2

    checkpoints = [
        {
            "name": "detent_retention_cycle",
            "blocks": ["thin_self_lock_margin_unverified"],
            "source_layout_checks": ["latch_ramp_self_lock"],
            "inspection_method": "five_dry_latch_cycles_plus_tip_upset",
            "evidence_gate": "Gate 2 dry assembly",
        },
        {
            "name": "omitted_station_span_bow",
            "blocks": ["omitted_station_span_bow_unmeasured"],
            "source_layout_checks": ["latch_station_asymmetry"],
            "inspection_method": "straightedge_or_photo_near_omitted_station",
            "evidence_gate": "Gate 2 dry assembly",
        },
        {
            "name": "post_cap_bearing_after_cycle",
            "blocks": ["post_or_cap_bearing_damage_unchecked"],
            "source_layout_checks": ["latch_post_stress_screen"],
            "inspection_method": "post_cap_root_visual_after_dry_cycle",
            "evidence_gate": "Gate 2 dry assembly",
        },
        {
            "name": "gasket_squeeze_after_retention_cycle",
            "blocks": ["gasket_squeeze_after_latch_cycle_unmeasured"],
            "source_layout_checks": ["latch_compression_budget"],
            "source_validation_checks": ["gasket_compression_gap_gauge"],
            "inspection_method": "gap_gauge_or_caliper_after_dry_cycle",
            "evidence_gate": "Gate 2 dry assembly",
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
            for source in checkpoint["source_layout_checks"]
        }
    )
    source_validation_checks = sorted(
        {
            source
            for checkpoint in checkpoints
            for source in checkpoint.get("source_validation_checks", [])
        }
    )

    requires_physical_evidence = bool(
        ramp_self_lock["backdrive_risk_flag"]
        or station_asymmetry["exceeds_allowed_span"]
        or not post_stress_screen["passes_stress_screen"]
        or not compression_budget["passes_budget"]
    )
    return {
        "name": "latch_retention_span_check",
        "role": "dry_latch_retention_and_omitted_span_evidence_blocker",
        "validation": "cad_proxy_latch_retention_span_physical_evidence_required",
        "failure_rule": (
            "thin_self_lock_or_excess_span_blocks_wet_tests_until_gate2_evidence"
        ),
        "evidence_gate": "Gate 2 dry assembly",
        "cad_value": (
            f"{float(ramp_self_lock['self_lock_margin_deg']):.2f} deg margin / "
            f"{float(station_asymmetry['max_active_station_span_mm']):.2f} mm "
            f"span / {int(station_asymmetry['omitted_station_count'])} omitted"
        ),
        "checkpoint_count": len(checkpoints),
        "checkpoints": checkpoints,
        "blockers": blockers,
        "source_layout_checks": source_layout_checks,
        "source_validation_checks": source_validation_checks,
        "wedge_lock_count": len(wedge_lock_rectangles),
        "self_lock_margin_deg": ramp_self_lock["self_lock_margin_deg"],
        "self_lock_min_margin_deg": ramp_self_lock["self_lock_min_margin_deg"],
        "backdrive_risk_flag": ramp_self_lock["backdrive_risk_flag"],
        "retention_status": ramp_self_lock["retention_status"],
        "omitted_station_count": station_asymmetry["omitted_station_count"],
        "max_active_station_span_mm": station_asymmetry["max_active_station_span_mm"],
        "allowed_max_active_span_mm": station_asymmetry["allowed_max_active_span_mm"],
        "exceeds_allowed_span": station_asymmetry["exceeds_allowed_span"],
        "passes_post_stress_screen": post_stress_screen["passes_stress_screen"],
        "passes_compression_budget": compression_budget["passes_budget"],
        "requires_physical_evidence": requires_physical_evidence,
        "all_checkpoints_block_wet_tests": True,
        "body_rects": [
            {
                "name": "latch_retention_span_evidence_slab",
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": 0.0,
                "length_x": round(slab_len, 3),
                "width_y": round(slab_wid, 3),
                "height_z": round(slab_h, 3),
            }
        ],
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


def _latch_station_asymmetry_screen(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_stop_positions: list[tuple[float, float]],
    wedge_lock_rectangles: list[dict[str, float | str]],
) -> dict[str, Any]:
    mechanics = params.get("latch_mechanics", {})
    active_positions = {
        (round(float(lock["post_x"]), 3), round(float(lock["post_y"]), 3))
        for lock in wedge_lock_rectangles
    }
    expected_positions = {
        (round(float(x), 3), round(float(y), 3))
        for x, y in compression_stop_positions
    }
    omitted = sorted(expected_positions - active_positions)
    max_span = 0.0
    max_span_side: float | None = None
    if layout["row_axis"] == "y":
        sides = sorted({x for x, _y in expected_positions})
        for side_x in sides:
            ys = sorted(y for x, y in active_positions if x == side_x)
            for y0, y1 in zip(ys, ys[1:], strict=False):
                span = y1 - y0
                if span > max_span:
                    max_span = span
                    max_span_side = side_x
    else:
        sides = sorted({y for _x, y in expected_positions})
        for side_y in sides:
            xs = sorted(x for x, y in active_positions if y == side_y)
            for x0, x1 in zip(xs, xs[1:], strict=False):
                span = x1 - x0
                if span > max_span:
                    max_span = span
                    max_span_side = side_y

    allowed_span = mechanics.get("max_active_latch_span_y", 0.0)
    return {
        "expected_station_count": len(expected_positions),
        "active_station_count": len(active_positions),
        "omitted_station_count": len(omitted),
        "omitted_stop_positions": [
            {"x": x, "y": y, "reason": "port_or_adapter_keepout"} for x, y in omitted
        ],
        "has_omitted_station_warning": bool(omitted),
        "max_active_station_span_mm": round(max_span, 3),
        "max_active_station_span_side": round(max_span_side, 3)
        if max_span_side is not None
        else None,
        "allowed_max_active_span_mm": round(allowed_span, 3),
        "exceeds_allowed_span": bool(allowed_span > 0 and max_span > allowed_span),
    }


def _add_wedge_release_detent_and_witness_features(
    lock: cq.Workplane,
    lock_rect: dict[str, float | str],
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    low_h = production.get("wedge_lock_low_height_z", 0.0)
    tab_len = production.get("wedge_release_tab_length_x", 0.0)
    tab_w = production.get("wedge_release_tab_width_y", 0.0)
    tab_h = production.get("wedge_release_tab_height_z", 0.0)
    witness_len = production.get("wedge_witness_mark_length_x", 0.0)
    witness_h = production.get("wedge_witness_mark_height_z", 0.0)
    detent_len = production.get("wedge_detent_bump_length_x", 0.0)
    detent_w = production.get("wedge_detent_bump_width_y", 0.0)
    detent_h = production.get("wedge_detent_bump_height_z", 0.0)
    lip_len = production.get("wedge_receiver_lip_length_x", 0.0)
    if min(tab_len, tab_w, tab_h, detent_len, detent_w, detent_h) <= 0:
        return lock

    lock_x = float(lock_rect["x"])
    lock_y = float(lock_rect["y"])
    lock_l = float(lock_rect["length_x"])
    lock_w = float(lock_rect["width_y"])
    arm_margin = 0.2

    if lock_rect["slide_axis"] == "x":
        if lock_rect["insert_from"] == "min":
            tab_x = lock_x + lip_len + 0.1
            detent_x = lock_x + max((lip_len - detent_len) / 2, 0.0)
        else:
            tab_x = lock_x + lock_l - lip_len - tab_len - 0.1
            detent_x = lock_x + lock_l - lip_len + max((lip_len - detent_len) / 2, 0.0)
        y_values = [
            lock_y + arm_margin,
            lock_y + lock_w - arm_margin - tab_w,
        ]
        for tab_y in y_values:
            lock = lock.union(
                cq.Workplane("XY")
                .box(tab_len, tab_w, tab_h, centered=(False, False, False))
                .translate((tab_x, tab_y, z0 + low_h))
            )
            lock = lock.union(
                cq.Workplane("XY")
                .box(detent_len, detent_w, detent_h, centered=(False, False, False))
                .translate((detent_x, tab_y, z0 + low_h))
            )
            if witness_len > 0 and witness_h > 0:
                witness_x = tab_x + max((tab_len - witness_len) / 2, 0.0)
                lock = lock.union(
                    cq.Workplane("XY")
                    .box(witness_len, tab_w, witness_h, centered=(False, False, False))
                    .translate((witness_x, tab_y, z0 + low_h + tab_h))
                )
        return lock

    if lock_rect["insert_from"] == "min":
        tab_y = lock_y + lip_len + 0.1
        detent_y = lock_y + max((lip_len - detent_len) / 2, 0.0)
    else:
        tab_y = lock_y + lock_w - lip_len - tab_len - 0.1
        detent_y = lock_y + lock_w - lip_len + max((lip_len - detent_len) / 2, 0.0)
    x_values = [
        lock_x + arm_margin,
        lock_x + lock_l - arm_margin - tab_w,
    ]
    for tab_x in x_values:
        lock = lock.union(
            cq.Workplane("XY")
            .box(tab_w, tab_len, tab_h, centered=(False, False, False))
            .translate((tab_x, tab_y, z0 + low_h))
        )
        lock = lock.union(
            cq.Workplane("XY")
            .box(detent_w, detent_len, detent_h, centered=(False, False, False))
            .translate((tab_x, detent_y, z0 + low_h))
        )
        if witness_len > 0 and witness_h > 0:
            witness_y = tab_y + max((tab_len - witness_len) / 2, 0.0)
            lock = lock.union(
                cq.Workplane("XY")
                .box(tab_w, witness_len, witness_h, centered=(False, False, False))
                .translate((tab_x, witness_y, z0 + low_h + tab_h))
            )
    return lock


def _wedge_lock_rectangles(
    layout: dict[str, Any],
    params: dict[str, Any],
) -> list[dict[str, float | str]]:
    return _wedge_lock_rectangles_for_layout(layout, params)


def _wedge_lock_rectangles_for_layout(
    layout: dict[str, Any],
    params: dict[str, Any],
) -> list[dict[str, float | str]]:
    production = params.get("production_assembly", {})
    lock_w = production.get("wedge_lock_width_x", 6.0)
    lock_len = production.get("wedge_lock_length_y", 12.0)
    lock_h = production.get("wedge_lock_height_z", 3.0)
    bearing_flat = production.get("wedge_lock_bearing_flat_length_x", 0.0)
    receiver_lip_len = production.get("wedge_receiver_lip_length_x", 0.0)
    release_tab_len = production.get("wedge_release_tab_length_x", 0.0)
    witness_len = production.get("wedge_witness_mark_length_x", 0.0)
    detent_len = production.get("wedge_detent_bump_length_x", 0.0)
    stop_len = production.get("wedge_travel_stop_length_x", 0.0)
    stop_clearance = production.get("wedge_receiver_clearance_x", 0.0)
    port_positions = _lid_port_positions(layout, params)
    rectangles: list[dict[str, float | str]] = []
    for x, y in layout["compression_stop_positions"]:
        if layout["row_axis"] == "y":
            if x <= layout["length_x"] / 2:
                lock_x = 0.0
                insert_from = "min"
                bearing_x = lock_x + lock_w - bearing_flat
                capture_x = lock_x
                release_x = lock_x + receiver_lip_len + 0.1
                detent_x = lock_x + max((receiver_lip_len - detent_len) / 2, 0.0)
                stop_x = min(layout["length_x"] - stop_len, lock_x + lock_w + stop_clearance)
            else:
                lock_x = layout["length_x"] - lock_w
                insert_from = "max"
                bearing_x = lock_x
                capture_x = lock_x + lock_w - receiver_lip_len
                release_x = lock_x + lock_w - receiver_lip_len - release_tab_len - 0.1
                detent_x = lock_x + lock_w - receiver_lip_len + max(
                    (receiver_lip_len - detent_len) / 2,
                    0.0,
                )
                stop_x = max(0.0, lock_x - stop_clearance - stop_len)
            lock_y = min(max(y - lock_len / 2, 0.0), layout["width_y"] - lock_len)
            slide_axis = "x"
            bearing_y = lock_y
            capture_y = lock_y
            release_y = lock_y
            detent_y = lock_y
            witness_x = release_x + max((release_tab_len - witness_len) / 2, 0.0)
            witness_y = lock_y
            stop_y = lock_y
            stop_length_x = stop_len
            stop_width_y = lock_len
        else:
            lock_x = min(max(x - lock_w / 2, 0.0), layout["length_x"] - lock_w)
            if y <= layout["width_y"] / 2:
                lock_y = 0.0
                insert_from = "min"
                bearing_y = lock_y + lock_len - bearing_flat
                capture_y = lock_y
                release_y = lock_y + receiver_lip_len + 0.1
                detent_y = lock_y + max((receiver_lip_len - detent_len) / 2, 0.0)
                stop_y = min(layout["width_y"] - stop_len, lock_y + lock_len + stop_clearance)
            else:
                lock_y = layout["width_y"] - lock_len
                insert_from = "max"
                bearing_y = lock_y
                capture_y = lock_y + lock_len - receiver_lip_len
                release_y = lock_y + lock_len - receiver_lip_len - release_tab_len - 0.1
                detent_y = lock_y + lock_len - receiver_lip_len + max(
                    (receiver_lip_len - detent_len) / 2,
                    0.0,
                )
                stop_y = max(0.0, lock_y - stop_clearance - stop_len)
            slide_axis = "y"
            bearing_x = lock_x
            capture_x = lock_x
            release_x = lock_x
            detent_x = lock_x
            witness_x = lock_x
            witness_y = release_y + max((release_tab_len - witness_len) / 2, 0.0)
            stop_x = lock_x
            stop_length_x = lock_w
            stop_width_y = stop_len
        candidate = {
            "x": round(lock_x, 3),
            "y": round(lock_y, 3),
            "length_x": lock_w,
            "width_y": lock_len,
            "height_z": lock_h,
            "post_x": round(x, 3),
            "post_y": round(y, 3),
            "slide_axis": slide_axis,
            "insert_from": insert_from,
            "bearing_flat_x": round(bearing_x, 3),
            "bearing_flat_y": round(bearing_y, 3),
            "bearing_flat_length_x": round(
                bearing_flat if slide_axis == "x" else lock_w,
                3,
            ),
            "bearing_flat_width_y": round(
                lock_len if slide_axis == "x" else bearing_flat,
                3,
            ),
            "capture_lip_x": round(capture_x, 3),
            "capture_lip_y": round(capture_y, 3),
            "capture_lip_length_x": round(
                receiver_lip_len if slide_axis == "x" else lock_w,
                3,
            ),
            "capture_lip_width_y": round(
                lock_len if slide_axis == "x" else receiver_lip_len,
                3,
            ),
            "release_tab_x": round(release_x, 3),
            "release_tab_y": round(release_y, 3),
            "witness_mark_x": round(witness_x, 3),
            "witness_mark_y": round(witness_y, 3),
            "detent_x": round(detent_x, 3),
            "detent_y": round(detent_y, 3),
            "travel_stop_x": round(stop_x, 3),
            "travel_stop_y": round(stop_y, 3),
            "travel_stop_length_x": round(stop_length_x, 3),
            "travel_stop_width_y": round(stop_width_y, 3),
        }
        if _wedge_lock_overlaps_lid_port(candidate, port_positions, params):
            continue
        rectangles.append(candidate)
    return rectangles


def _wedge_lock_overlaps_lid_port(
    lock: dict[str, float | str],
    port_positions: list[dict[str, Any]],
    params: dict[str, Any],
) -> bool:
    production = params.get("production_assembly", {})
    port_clearance = production.get("wedge_lock_port_clearance_xy", 0.0)
    receiver_clearance = production.get("wedge_receiver_clearance_x", 0.0)
    receiver_w = production.get("wedge_receiver_rail_width_x", 0.0)
    length_extra = production.get("wedge_receiver_length_extra_y", 0.0)
    if lock["slide_axis"] == "x":
        env_x0 = min(float(lock["x"]), float(lock["travel_stop_x"]))
        env_x1 = max(
            float(lock["x"]) + float(lock["length_x"]),
            float(lock["travel_stop_x"]) + float(lock["travel_stop_length_x"]),
        )
        expanded = {
            "x": env_x0 - length_extra / 2 - port_clearance,
            "y": float(lock["y"]) - receiver_clearance - receiver_w - port_clearance,
            "length_x": env_x1 - env_x0 + length_extra + 2 * port_clearance,
            "width_y": float(lock["width_y"])
            + 2 * (receiver_clearance + receiver_w + port_clearance),
        }
    else:
        env_y0 = min(float(lock["y"]), float(lock["travel_stop_y"]))
        env_y1 = max(
            float(lock["y"]) + float(lock["width_y"]),
            float(lock["travel_stop_y"]) + float(lock["travel_stop_width_y"]),
        )
        expanded = {
            "x": float(lock["x"]) - receiver_clearance - receiver_w - port_clearance,
            "y": env_y0 - length_extra / 2 - port_clearance,
            "length_x": float(lock["length_x"])
            + 2 * (receiver_clearance + receiver_w + port_clearance),
            "width_y": env_y1 - env_y0 + length_extra + 2 * port_clearance,
        }
    for port in port_positions:
        if _rectangle_intersects_circle(
            expanded,
            float(port["x"]),
            float(port["y"]),
            float(port["boss_diameter"]) / 2 + port_clearance,
        ):
            return True
    return False


def _rectangle_intersects_circle(
    rect: dict[str, float],
    circle_x: float,
    circle_y: float,
    radius: float,
) -> bool:
    closest_x = min(max(circle_x, rect["x"]), rect["x"] + rect["length_x"])
    closest_y = min(max(circle_y, rect["y"]), rect["y"] + rect["width_y"])
    return (closest_x - circle_x) ** 2 + (closest_y - circle_y) ** 2 <= radius**2


def _cut_latch_post_slot(
    lock: cq.Workplane,
    lock_rect: dict[str, float | str],
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    post_d = production.get("latch_post_diameter", 0.0)
    if post_d <= 0:
        return lock

    slot_w = post_d + 2 * production.get("wedge_lock_post_slot_clearance_xy", 0.35)
    slot_h = float(lock_rect["height_z"]) + 0.6
    post_x = float(lock_rect["post_x"])
    post_y = float(lock_rect["post_y"])

    if lock_rect["slide_axis"] == "x":
        if lock_rect["insert_from"] == "min":
            slot_x = float(lock_rect["x"]) - 0.1
            slot_len = post_x - float(lock_rect["x"]) + slot_w / 2 + 0.1
        else:
            slot_x = post_x - slot_w / 2
            slot_len = (
                float(lock_rect["x"])
                + float(lock_rect["length_x"])
                - post_x
                + slot_w / 2
                + 0.1
            )
        cutter = (
            cq.Workplane("XY")
            .box(slot_len, slot_w, slot_h, centered=(False, False, False))
            .translate((slot_x, post_y - slot_w / 2, z0 - 0.2))
        )
        return lock.cut(cutter)

    if lock_rect["insert_from"] == "min":
        slot_y = float(lock_rect["y"]) - 0.1
        slot_len = post_y - float(lock_rect["y"]) + slot_w / 2 + 0.1
    else:
        slot_y = post_y - slot_w / 2
        slot_len = (
            float(lock_rect["y"])
            + float(lock_rect["width_y"])
            - post_y
            + slot_w / 2
            + 0.1
        )
    cutter = (
        cq.Workplane("XY")
        .box(slot_w, slot_len, slot_h, centered=(False, False, False))
        .translate((post_x - slot_w / 2, slot_y, z0 - 0.2))
    )
    return lock.cut(cutter)


def _add_wedge_receiver_rails(
    cover: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    lid = params["lid_manifold"]
    production = params.get("production_assembly", {})
    rail_w = production.get("wedge_receiver_rail_width_x", 1.2)
    rail_h = production.get("wedge_receiver_rail_height_z", 1.1)
    lip_w = production.get("wedge_receiver_lip_width_y", 0.0)
    lip_h = production.get("wedge_receiver_lip_height_z", 0.0)
    lip_len = production.get("wedge_receiver_lip_length_x", 0.0)
    stop_h = production.get("wedge_travel_stop_height_z", rail_h)
    clearance = production.get("wedge_receiver_clearance_x", 0.5)
    length_extra = production.get("wedge_receiver_length_extra_y", 2.0)
    if rail_w <= 0 or rail_h <= 0:
        return cover
    receiver_z = z0 + lid["duct_height_z"]

    for lock in _wedge_lock_rectangles(layout, params):
        if lock["slide_axis"] == "x":
            rail_x = max(0.0, float(lock["x"]) - length_extra / 2)
            rail_len = min(
                layout["length_x"] - rail_x,
                float(lock["length_x"]) + length_extra,
            )
            y_values = [
                max(0.0, float(lock["y"]) - clearance - rail_w),
                min(
                    layout["width_y"] - rail_w,
                    float(lock["y"]) + float(lock["width_y"]) + clearance,
                ),
            ]
            for rail_y in y_values:
                cover = cover.union(
                    cq.Workplane("XY")
                    .box(rail_len, rail_w, rail_h, centered=(False, False, False))
                    .translate((rail_x, rail_y, receiver_z))
                )
            if lip_w > 0 and lip_h > 0 and lip_len > 0:
                lip_x = float(lock["capture_lip_x"])
                lip_len_x = min(lip_len, layout["length_x"] - lip_x)
                lip_y_values = [
                    max(0.0, float(lock["y"]) - clearance),
                    min(
                        layout["width_y"] - lip_w,
                        float(lock["y"]) + float(lock["width_y"]) + clearance - lip_w,
                    ),
                ]
                for lip_y in lip_y_values:
                    cover = cover.union(
                        cq.Workplane("XY")
                        .box(lip_len_x, lip_w, lip_h, centered=(False, False, False))
                        .translate((lip_x, lip_y, receiver_z + rail_h))
                    )
            if stop_h > 0 and float(lock["travel_stop_length_x"]) > 0:
                stop_y = max(0.0, float(lock["y"]) - clearance - rail_w)
                stop_w = min(
                    layout["width_y"] - stop_y,
                    float(lock["width_y"]) + 2 * (clearance + rail_w),
                )
                cover = cover.union(
                    cq.Workplane("XY")
                    .box(
                        float(lock["travel_stop_length_x"]),
                        stop_w,
                        stop_h,
                        centered=(False, False, False),
                    )
                    .translate((float(lock["travel_stop_x"]), stop_y, receiver_z))
                )
        else:
            rail_y = max(0.0, float(lock["y"]) - length_extra / 2)
            rail_len = min(
                layout["width_y"] - rail_y,
                float(lock["width_y"]) + length_extra,
            )
            x_values = [
                max(0.0, float(lock["x"]) - clearance - rail_w),
                min(
                    layout["length_x"] - rail_w,
                    float(lock["x"]) + float(lock["length_x"]) + clearance,
                ),
            ]
            for rail_x in x_values:
                cover = cover.union(
                    cq.Workplane("XY")
                    .box(rail_w, rail_len, rail_h, centered=(False, False, False))
                    .translate((rail_x, rail_y, receiver_z))
                )
            if lip_w > 0 and lip_h > 0 and lip_len > 0:
                lip_y = float(lock["capture_lip_y"])
                lip_len_y = min(lip_len, layout["width_y"] - lip_y)
                lip_x_values = [
                    max(0.0, float(lock["x"]) - clearance),
                    min(
                        layout["length_x"] - lip_w,
                        float(lock["x"]) + float(lock["length_x"]) + clearance - lip_w,
                    ),
                ]
                for lip_x in lip_x_values:
                    cover = cover.union(
                        cq.Workplane("XY")
                        .box(lip_w, lip_len_y, lip_h, centered=(False, False, False))
                        .translate((lip_x, lip_y, receiver_z + rail_h))
                    )
            if stop_h > 0 and float(lock["travel_stop_width_y"]) > 0:
                stop_x = max(0.0, float(lock["x"]) - clearance - rail_w)
                stop_l = min(
                    layout["length_x"] - stop_x,
                    float(lock["length_x"]) + 2 * (clearance + rail_w),
                )
                cover = cover.union(
                    cq.Workplane("XY")
                    .box(
                        stop_l,
                        float(lock["travel_stop_width_y"]),
                        stop_h,
                        centered=(False, False, False),
                    )
                    .translate((stop_x, float(lock["travel_stop_y"]), receiver_z))
                )
    return cover


def _cut_condensation_pockets(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    pocket_rects = _condensation_pocket_rectangles_for_layout(
        layout,
        params=params,
        z0=z0,
    )
    if not pocket_rects:
        return model

    for pocket in pocket_rects:
        model = model.cut(
            cq.Workplane("XY")
            .box(
                float(pocket["length_x"]),
                float(pocket["width_y"]),
                float(pocket["height_z"]),
                centered=(True, False, False),
            )
            .translate(
                (
                    float(pocket["center_x"]),
                    float(pocket["y"]),
                    float(pocket["z"]),
                )
            )
        )
    return model


def _condensation_pocket_rectangles_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    z0: float,
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    pocket_len = float(production.get("condensation_pocket_length_x", 0.0))
    pocket_wid = float(production.get("condensation_pocket_width_y", 0.0))
    pocket_depth = float(production.get("condensation_pocket_depth_z", 0.0))
    if pocket_len <= 0 or pocket_wid <= 0 or pocket_depth <= 0:
        return []

    skirt = params["wet_chamber_skirt"]
    pocket_cut_z = z0 + 0.05
    lane_center_x_values = (
        float(skirt["wall_thickness"]) + float(skirt["service_lane_width"]) / 2,
        float(layout["length_x"])
        - float(skirt["wall_thickness"])
        - float(skirt["service_lane_width"]) / 2,
    )
    y_values = (
        float(skirt["wall_thickness"]) + pocket_wid,
        float(layout["width_y"]) - float(skirt["wall_thickness"]) - 2 * pocket_wid,
    )
    side_names = ("left_service_lane", "right_service_lane")
    edge_names = ("front_low_point", "rear_low_point")
    pockets: list[dict[str, Any]] = []
    for x_idx, center_x in enumerate(lane_center_x_values):
        for y_idx, y in enumerate(y_values):
            pockets.append(
                {
                    "name": (
                        f"condensation_pocket_{side_names[x_idx]}_"
                        f"{edge_names[y_idx]}"
                    ),
                    "kind": "condensation_pocket_low_point",
                    "shape": "rect",
                    "role": "wet_chamber_condensation_low_point_witness",
                    "x": round(center_x - pocket_len / 2, 3),
                    "y": round(y, 3),
                    "z": round(pocket_cut_z, 3),
                    "center_x": round(center_x, 3),
                    "center_y": round(y + pocket_wid / 2, 3),
                    "length_x": round(pocket_len, 3),
                    "width_y": round(pocket_wid, 3),
                    "height_z": round(pocket_depth + 0.05, 3),
                    "nominal_depth_z": round(pocket_depth, 3),
                }
            )
    return pockets


def _thermal_condensation_proxy_targets_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    plate_bottom_z: float,
    plate_top_z: float,
    ir_sensor_mounts: list[dict[str, Any]],
    headspace_sht41_mounts: list[dict[str, Any]],
    condensation_pocket_rects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plate = params["plate"]
    grid = params["well_grid"]
    harness = params.get("sensor_harness", {})
    cell_thickness = float(plate.get("cell_plane_check_thickness_z", 0.2))
    ir_thickness = float(harness.get("ir_fov_spot_check_thickness_z", 0.2))
    cell_plane_z = float(plate_top_z) - float(plate["plate_top_to_cell_plane_depth_z"])
    ir_mounts_by_tile = {
        int(mount["tile_index"]): mount
        for mount in ir_sensor_mounts
    }
    sht_mounts_by_tile = {
        int(mount["tile_index"]): mount
        for mount in headspace_sht41_mounts
    }

    targets: list[dict[str, Any]] = []
    for tile in layout["tile_origins"]:
        tile_index = int(tile["index"])
        center_x = (
            float(tile["x"])
            + float(grid["first_well_center_x"])
            + (int(grid["columns"]) - 1) * float(grid["pitch_x"]) / 2
        )
        center_y = (
            float(tile["y"])
            + float(grid["first_well_center_y"])
            + (int(grid["rows"]) - 1) * float(grid["pitch_y"]) / 2
        )
        targets.append(
            {
                "name": f"thermal_cell_plane_center_tile_{tile_index}",
                "kind": "cell_plane_center_reference",
                "shape": "disk",
                "role": "center_cell_plane_reference_for_edge_thermal_correlation",
                "tile_index": tile_index,
                "x": round(center_x, 3),
                "y": round(center_y, 3),
                "z": round(cell_plane_z - cell_thickness / 2, 3),
                "diameter": round(
                    float(plate["well_bottom_area_equivalent_diameter"]),
                    3,
                ),
                "height_z": round(cell_thickness, 3),
            }
        )

        ir_mount = ir_mounts_by_tile.get(tile_index)
        if ir_mount is not None:
            targets.append(
                {
                    "name": f"thermal_ir_proxy_spot_tile_{tile_index}",
                    "kind": "ir_plate_margin_proxy_spot",
                    "shape": "disk",
                    "role": "edge_plate_margin_ir_proxy_for_cell_plane_correlation",
                    "tile_index": tile_index,
                    "x": round(float(ir_mount["center_x"]), 3),
                    "y": round(float(ir_mount["center_y"]), 3),
                    "z": round(float(plate_bottom_z) - ir_thickness / 2, 3),
                    "diameter": round(float(ir_mount["fov_spot_diameter"]), 3),
                    "height_z": round(ir_thickness, 3),
                    "fov_angle_degrees": float(ir_mount["fov_angle_degrees"]),
                }
            )

        sht_mount = sht_mounts_by_tile.get(tile_index)
        if sht_mount is not None:
            ring = sht_mount["drip_break_ring"]
            targets.append(
                {
                    "name": f"thermal_sht41_headspace_point_tile_{tile_index}",
                    "kind": "sht41_headspace_aperture_drip_ring",
                    "shape": "disk",
                    "role": "local_headspace_temperature_humidity_point",
                    "tile_index": tile_index,
                    "x": round(float(sht_mount["aperture_x"]), 3),
                    "y": round(float(sht_mount["aperture_y"]), 3),
                    "z": round(float(ring["z"]), 3),
                    "diameter": round(float(ring["outer_diameter"]), 3),
                    "height_z": round(float(ring["height_z"]), 3),
                    "aperture_diameter": round(
                        float(sht_mount["aperture_diameter"]),
                        3,
                    ),
                }
            )

    for pocket in condensation_pocket_rects:
        targets.append(
            {
                **pocket,
                "role": "condensation_low_point_witness_for_gate6_review",
            }
        )
    return targets


def _add_wet_chamber_service_dividers(
    model: cq.Workplane,
    *,
    layout: dict[str, Any],
    params: dict[str, Any],
    z0: float,
    height: float,
) -> cq.Workplane:
    skirt = params["wet_chamber_skirt"]
    bounds = layout["wet_chamber_skirt"]
    wall_w = skirt["wall_thickness"]
    lane_w = skirt.get("service_lane_width", 0.0)
    divider_w = skirt.get("plenum_divider_thickness", 0.0)
    if lane_w <= 0 or divider_w <= 0:
        return model

    if layout["row_axis"] == "y":
        rail_y = bounds["y"] + wall_w
        rail_len = bounds["width_y"] - 2 * wall_w
        x_values = [
            bounds["x"] + wall_w + lane_w,
            bounds["x"] + bounds["length_x"] - wall_w - lane_w - divider_w,
        ]
        for x in x_values:
            model = model.union(
                cq.Workplane("XY")
                .box(divider_w, rail_len, height, centered=(False, False, False))
                .translate((x, rail_y, z0))
            )
        return _cut_wet_chamber_divider_windows(
            model,
            layout=layout,
            params=params,
            rail_positions=x_values,
            rail_axis="y",
            rail_thickness=divider_w,
            z0=z0,
            height=height,
        )

    rail_x = bounds["x"] + wall_w
    rail_len = bounds["length_x"] - 2 * wall_w
    y_values = [
        bounds["y"] + wall_w + lane_w,
        bounds["y"] + bounds["width_y"] - wall_w - lane_w - divider_w,
    ]
    for y in y_values:
        model = model.union(
            cq.Workplane("XY")
            .box(rail_len, divider_w, height, centered=(False, False, False))
            .translate((rail_x, y, z0))
        )
    return _cut_wet_chamber_divider_windows(
        model,
        layout=layout,
        params=params,
        rail_positions=y_values,
        rail_axis="x",
        rail_thickness=divider_w,
        z0=z0,
        height=height,
    )


def _cut_wet_chamber_divider_windows(
    model: cq.Workplane,
    *,
    layout: dict[str, Any],
    params: dict[str, Any],
    rail_positions: list[float],
    rail_axis: str,
    rail_thickness: float,
    z0: float,
    height: float,
) -> cq.Workplane:
    skirt = params["wet_chamber_skirt"]
    plate = params["plate"]
    window_len = skirt.get("diffuser_window_length", 0.0)
    window_h = skirt.get("diffuser_window_height_z", 0.0)
    top_ligament = skirt.get("diffuser_window_top_ligament_z", 0.0)
    if window_len <= 0 or window_h <= 0:
        return model

    window_z = z0 + max(0.0, height - top_ligament - window_h)
    cut_h = min(window_h, height) + 0.2
    for tile in layout["tile_origins"]:
        if rail_axis == "y":
            center = tile["y"] + plate["width_y"] / 2
            for x in rail_positions:
                model = model.cut(
                    cq.Workplane("XY")
                    .box(
                        rail_thickness + 0.4,
                        window_len,
                        cut_h,
                        centered=(False, False, False),
                    )
                    .translate((x - 0.2, center - window_len / 2, window_z))
                )
        else:
            center = tile["x"] + plate["length_x"] / 2
            for y in rail_positions:
                model = model.cut(
                    cq.Workplane("XY")
                    .box(
                        window_len,
                        rail_thickness + 0.4,
                        cut_h,
                        centered=(False, False, False),
                    )
                    .translate((center - window_len / 2, y - 0.2, window_z))
                )
    return model


def _latch_post_positions_for_locks(
    locks: list[dict[str, float | str]],
) -> list[dict[str, float | str]]:
    return [
        {
            "x": float(lock["post_x"]),
            "y": float(lock["post_y"]),
            "slide_axis": str(lock["slide_axis"]),
            "insert_from": str(lock["insert_from"]),
        }
        for lock in locks
    ]


def _add_latch_tension_posts(
    model: cq.Workplane,
    *,
    layout: dict[str, Any],
    params: dict[str, Any],
    z0: float,
    height: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    post_d = production.get("latch_post_diameter", 0.0)
    if post_d <= 0:
        return model

    lid = params["lid_manifold"]
    skirt = params["wet_chamber_skirt"]
    bounds = layout["wet_chamber_skirt"]
    head_len_x = production.get("latch_post_head_length_x", 8.5)
    head_w_y = production.get("latch_post_head_width_y", 10.0)
    head_h = production.get("latch_post_head_height_z", 1.0)
    pedestal_w = production.get("latch_post_pedestal_width_y", 3.4)
    root_len = production.get("latch_post_root_gusset_length_x", 0.0)
    root_w = production.get("latch_post_root_gusset_width_y", 0.0)
    root_h = min(production.get("latch_post_root_gusset_height_z", 0.0), height)
    wedge_h = production.get("wedge_lock_height_z", 3.0)
    frame_bottom_z = bounds["bottom_z"]
    wedge_bottom_z = layout["lid_top_z"] + lid["duct_height_z"]
    head_bottom_z = z0 + (wedge_bottom_z + wedge_h - frame_bottom_z)
    shaft_base_z = z0 + height - 0.2
    shaft_h = max(0.2, head_bottom_z - shaft_base_z + 0.05)
    lane_span = (
        skirt["wall_thickness"]
        + skirt.get("service_lane_width", 0.0)
        + skirt.get("plenum_divider_thickness", 0.0)
    )

    for post in layout["latch_post_positions"]:
        x = float(post["x"])
        y = float(post["y"])
        if post["slide_axis"] == "x":
            ped_len_x = max(lane_span, head_len_x)
            ped_y = min(
                max(bounds["y"], y - pedestal_w / 2),
                bounds["y"] + bounds["width_y"] - pedestal_w,
            )
            if post["insert_from"] == "min":
                ped_x = bounds["x"]
            else:
                ped_x = bounds["x"] + bounds["length_x"] - ped_len_x
            pedestal = (
                cq.Workplane("XY")
                .box(ped_len_x, pedestal_w, height, centered=(False, False, False))
                .translate((ped_x, ped_y, z0))
            )
            head = _rounded_box(
                head_len_x,
                head_w_y,
                head_h,
                min(head_len_x, head_w_y) / 8,
            ).translate((x - head_len_x / 2, y - head_w_y / 2, head_bottom_z))
            root_pad: cq.Workplane | None = None
            if root_len > 0 and root_w > 0 and root_h > 0:
                root_x = min(
                    max(bounds["x"], x - root_len / 2),
                    bounds["x"] + bounds["length_x"] - root_len,
                )
                root_y = min(
                    max(bounds["y"], y - root_w / 2),
                    bounds["y"] + bounds["width_y"] - root_w,
                )
                root_pad = (
                    cq.Workplane("XY")
                    .box(root_len, root_w, root_h, centered=(False, False, False))
                    .translate((root_x, root_y, z0 + height - root_h))
                )
        else:
            ped_len_y = max(lane_span, head_w_y)
            ped_x = min(
                max(bounds["x"], x - pedestal_w / 2),
                bounds["x"] + bounds["length_x"] - pedestal_w,
            )
            if post["insert_from"] == "min":
                ped_y = bounds["y"]
            else:
                ped_y = bounds["y"] + bounds["width_y"] - ped_len_y
            pedestal = (
                cq.Workplane("XY")
                .box(pedestal_w, ped_len_y, height, centered=(False, False, False))
                .translate((ped_x, ped_y, z0))
            )
            head = _rounded_box(
                head_w_y,
                head_len_x,
                head_h,
                min(head_len_x, head_w_y) / 8,
            ).translate((x - head_w_y / 2, y - head_len_x / 2, head_bottom_z))
            root_pad = None
            if root_len > 0 and root_w > 0 and root_h > 0:
                root_x = min(
                    max(bounds["x"], x - root_w / 2),
                    bounds["x"] + bounds["length_x"] - root_w,
                )
                root_y = min(
                    max(bounds["y"], y - root_len / 2),
                    bounds["y"] + bounds["width_y"] - root_len,
                )
                root_pad = (
                    cq.Workplane("XY")
                    .box(root_w, root_len, root_h, centered=(False, False, False))
                    .translate((root_x, root_y, z0 + height - root_h))
                )

        shaft = (
            cq.Workplane("XY")
            .circle(post_d / 2)
            .extrude(shaft_h)
            .translate((x, y, shaft_base_z))
        )
        model = model.union(pedestal)
        if root_pad is not None:
            model = model.union(root_pad)
        model = model.union(shaft).union(head)
    return model


def _shared_chamber_bounds(
    layout: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, float]:
    bounds = layout["wet_chamber_skirt"]
    return {
        "x": bounds["x"],
        "y": bounds["y"],
        "length_x": bounds["length_x"],
        "width_y": bounds["width_y"],
    }


def _build_port_cap_body(
    *,
    x: float,
    y: float,
    plug_d: float,
    flange_d: float,
    plug_bottom_z: float,
    plug_depth: float,
    flange_h: float,
    seal_lip_inner_d: float,
    seal_lip_outer_d: float,
    seal_lip_h: float,
    grip_len: float,
    grip_w: float,
    grip_h: float,
    grip_overlap: float,
    layout: dict[str, Any],
) -> cq.Workplane:
    flange_bottom_z = plug_bottom_z + plug_depth
    cap = (
        cq.Workplane("XY")
        .circle(plug_d / 2)
        .extrude(plug_depth)
        .translate((x, y, plug_bottom_z))
    )
    if flange_h > 0:
        cap = cap.union(
            cq.Workplane("XY")
            .circle(flange_d / 2)
            .extrude(flange_h)
            .translate((x, y, flange_bottom_z))
        )
    if min(seal_lip_inner_d, seal_lip_outer_d, seal_lip_h) > 0:
        if seal_lip_inner_d >= seal_lip_outer_d:
            raise ValueError("port cap seal lip inner diameter must be smaller than outer")
        seal_lip = (
            cq.Workplane("XY")
            .circle(seal_lip_outer_d / 2)
            .extrude(seal_lip_h)
            .translate((x, y, flange_bottom_z - seal_lip_h))
        )
        seal_lip = seal_lip.cut(
            cq.Workplane("XY")
            .circle(seal_lip_inner_d / 2)
            .extrude(seal_lip_h + 0.1)
            .translate((x, y, flange_bottom_z - seal_lip_h - 0.05))
        )
        cap = cap.union(seal_lip)
    if min(grip_len, grip_w, grip_h) > 0:
        side = 1 if x <= layout["length_x"] / 2 else -1
        if side > 0:
            grip_x = x + flange_d / 2 - grip_overlap
        else:
            grip_x = x - flange_d / 2 - grip_len + grip_overlap
        cap = cap.union(
            cq.Workplane("XY")
            .box(grip_len, grip_w, grip_h + grip_overlap, centered=(False, False, False))
            .translate(
                (
                    grip_x,
                    y - grip_w / 2,
                    flange_bottom_z + flange_h - grip_overlap,
                )
            )
        )
    return cap


def _add_sample_relief_cap_review_flag(
    witness: cq.Workplane,
    *,
    port: dict[str, Any],
    layout: dict[str, Any],
    z0: float,
    length: float,
    width: float,
    height: float,
    radial_from_diameter: float,
) -> cq.Workplane:
    x = float(port["x"])
    y = float(port["y"])
    side = 1 if x <= layout["length_x"] / 2 else -1
    if side > 0:
        flag_x = x + radial_from_diameter / 2 - 0.1
    else:
        flag_x = x - radial_from_diameter / 2 - length + 0.1
    return witness.union(
        cq.Workplane("XY")
        .box(length, width, height, centered=(False, False, False))
        .translate((flag_x, y - width / 2, z0))
    )


def _port_service_review_state_metadata() -> dict[str, dict[str, Any]]:
    return {
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


def _axis_cylinder_envelope_rect(
    *,
    axis: str,
    x: float,
    y: float,
    z: float,
    length: float,
    diameter: float,
) -> dict[str, float]:
    if axis == "x":
        return {
            "x": round(x, 3),
            "y": round(y - diameter / 2, 3),
            "z": round(z - diameter / 2, 3),
            "length_x": round(length, 3),
            "width_y": round(diameter, 3),
            "height_z": round(diameter, 3),
        }
    if axis == "y":
        return {
            "x": round(x - diameter / 2, 3),
            "y": round(y, 3),
            "z": round(z - diameter / 2, 3),
            "length_x": round(diameter, 3),
            "width_y": round(length, 3),
            "height_z": round(diameter, 3),
        }
    raise ValueError("axis envelope must use axis 'x' or 'y'")


def _rectangles_overlap_xy(
    first: dict[str, Any],
    second: dict[str, Any],
) -> bool:
    return (
        float(first["x"]) < float(second["x"]) + float(second["length_x"])
        and float(second["x"]) < float(first["x"]) + float(first["length_x"])
        and float(first["y"]) < float(second["y"]) + float(second["width_y"])
        and float(second["y"]) < float(first["y"]) + float(first["width_y"])
    )


def _rectangles_bounding_extents(
    rects: list[dict[str, Any]],
) -> tuple[float, float, float]:
    if not rects:
        return 0.0, 0.0, 0.0
    x_min = min(float(rect["x"]) for rect in rects)
    y_min = min(float(rect["y"]) for rect in rects)
    z_min = min(float(rect["z"]) for rect in rects)
    x_max = max(float(rect["x"]) + float(rect["length_x"]) for rect in rects)
    y_max = max(float(rect["y"]) + float(rect["width_y"]) for rect in rects)
    z_max = max(float(rect["z"]) + float(rect["height_z"]) for rect in rects)
    return x_max - x_min, y_max - y_min, z_max - z_min


def _side_gas_service_interfaces(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_top_z: float,
) -> list[dict[str, Any]]:
    gas = params.get("gas_service", {})
    row = params["row"]
    lid = params["lid_manifold"]
    duct_w = lid["duct_width_y"]
    duct_h = lid["duct_height_z"]
    block_w = gas.get("manifold_block_width_y", 18.0)
    block_h = gas.get("manifold_block_height_z", 5.0)
    stem_len = gas.get("fitting_stem_length_x", 7.0)
    fitting_d = gas.get("fitting_outer_diameter", 4.8)
    opening_d = gas.get("duct_opening_diameter", 2.4)
    flange_d = gas.get("barb_flange_diameter", 4.8)
    flange_w = gas.get("barb_flange_width_x", 1.2)
    relief_len = gas.get("strain_relief_slot_length_x", 6.0)
    relief_w = gas.get("strain_relief_slot_width_y", 7.0)
    relief_h = gas.get("strain_relief_height_z", 2.0)
    tube_d = gas.get("tube_envelope_diameter", 6.0)
    tube_id = gas.get("tube_inner_diameter", max(0.1, fitting_d - 0.1))
    tube_od = gas.get("tube_outer_diameter", min(tube_d, fitting_d))
    bend_r = gas.get("tube_bend_radius", 18.0)
    straight_len = gas.get("tube_straight_service_length", 18.0)
    center_offset = gas.get("service_center_offset_from_row_end_y", 50.0)
    witness_w = gas.get("leak_witness_gutter_width_xy", 1.0)
    witness_d = gas.get("leak_witness_gutter_depth_z", 0.35)
    witness_offset = gas.get("leak_witness_gutter_offset_xy", fitting_d / 2 + 1.4)
    threshold_w = gas.get("leak_witness_threshold_width_xy", 0.8)
    threshold_h = gas.get("leak_witness_threshold_height_z", 0.6)
    center_z = lid_top_z + duct_h / 2
    if fitting_d < tube_id:
        raise ValueError("side gas fitting stem must meet or exceed tube inner diameter")
    if flange_d <= fitting_d:
        raise ValueError("side gas barb retention bead must exceed fitting stem diameter")
    if flange_d >= tube_od:
        raise ValueError("side gas barb retention bead must fit inside tube outer diameter")
    if tube_od > tube_d:
        raise ValueError("side gas tube outer diameter must fit inside tube bend envelope")
    barb_retention = {
        "retention": "printed_barb_retention_bead_and_strain_relief_no_glue",
        "tube_inner_diameter": round(tube_id, 3),
        "tube_outer_diameter": round(tube_od, 3),
        "stem_diameter": round(fitting_d, 3),
        "barb_peak_diameter": round(flange_d, 3),
        "barb_width": round(flange_w, 3),
        "stem_interference_diameter": round(max(0.0, fitting_d - tube_id), 3),
        "barb_interference_diameter": round(flange_d - tube_id, 3),
        "barb_radial_shoulder": round((flange_d - fitting_d) / 2, 3),
        "validation": "print_native_tube_capture_no_glue_or_clamp",
    }

    if layout["row_axis"] == "y":
        block_depth = row["end_margin_x"] + duct_w / 2
        gutter_len = max(block_depth - threshold_w, 0.1)
        centers = {
            "supply": row["side_margin_y"] + center_offset,
            "return": float(layout["width_y"]) - row["side_margin_y"] - center_offset,
        }
        specs: list[dict[str, Any]] = []
        for role, center_y in centers.items():
            is_supply = role == "supply"
            side = "left" if is_supply else "right"
            if is_supply:
                duct_x = row["end_margin_x"]
                flange_start_x = -stem_len - flange_w / 2
                duct_opening_x = -0.2
                gutter_x = 0.0
                threshold_x = block_depth - threshold_w
                leak_flow_direction = "-X_to_visible_outer_edge"
            else:
                duct_x = float(layout["length_x"]) - row["end_margin_x"]
                flange_start_x = float(layout["length_x"]) + stem_len - flange_w / 2
                duct_opening_x = float(layout["length_x"]) - block_depth - 0.2
                gutter_x = float(layout["length_x"]) - gutter_len
                threshold_x = float(layout["length_x"]) - block_depth
                leak_flow_direction = "+X_to_visible_outer_edge"
            block_x = 0.0 if is_supply else float(layout["length_x"]) - block_depth
            tube_x = -straight_len - bend_r if is_supply else float(layout["length_x"])
            stem_start_x = -stem_len if is_supply else float(layout["length_x"])
            fitting_rect = _axis_cylinder_envelope_rect(
                axis="x",
                x=stem_start_x,
                y=center_y,
                z=center_z,
                length=stem_len,
                diameter=fitting_d,
            )
            flange_rect = _axis_cylinder_envelope_rect(
                axis="x",
                x=flange_start_x,
                y=center_y,
                z=center_z,
                length=flange_w,
                diameter=flange_d,
            )
            leak_gutters = [
                {
                    "x": round(gutter_x, 3),
                    "y": round(center_y - witness_offset - witness_w / 2, 3),
                    "z": round(lid_top_z + block_h - witness_d, 3),
                    "length_x": round(gutter_len, 3),
                    "width_y": round(witness_w, 3),
                    "height_z": round(witness_d, 3),
                },
                {
                    "x": round(gutter_x, 3),
                    "y": round(center_y + witness_offset - witness_w / 2, 3),
                    "z": round(lid_top_z + block_h - witness_d, 3),
                    "length_x": round(gutter_len, 3),
                    "width_y": round(witness_w, 3),
                    "height_z": round(witness_d, 3),
                },
            ]
            leak_thresholds = [
                {
                    "x": round(threshold_x, 3),
                    "y": round(center_y - block_w / 2, 3),
                    "z": round(lid_top_z + block_h, 3),
                    "length_x": round(threshold_w, 3),
                    "width_y": round(block_w, 3),
                    "height_z": round(threshold_h, 3),
                }
            ]
            strain_relief_rect = {
                "x": round(-relief_len if is_supply else float(layout["length_x"]), 3),
                "y": round(center_y - relief_w / 2, 3),
                "z": round(center_z - relief_h / 2, 3),
                "length_x": round(relief_len, 3),
                "width_y": round(relief_w, 3),
                "height_z": round(relief_h, 3),
            }
            tube_rect = {
                "x": round(tube_x, 3),
                "y": round(center_y - tube_d / 2, 3),
                "z": round(center_z - tube_d / 2, 3),
                "length_x": round(straight_len + bend_r, 3),
                "width_y": round(tube_d, 3),
                "height_z": round(tube_d, 3),
            }
            installed_tube = {
                "name": f"{role}_cots_gas_tube_pigtail",
                "role": role,
                "owner_part": "cots_gas_service_tubes",
                "service_role": f"installed_operating_gas_{role}_tube",
                "axis": "x",
                "route_axis": "-X" if is_supply else "+X",
                "x": round(tube_x, 3),
                "y": round(center_y, 3),
                "z": round(center_z, 3),
                "length": round(straight_len + bend_r, 3),
                "diameter": round(tube_od, 3),
                "inner_diameter": round(tube_id, 3),
                "flow_bore_diameter": round(tube_id, 3),
                "geometry": "hollow_tube_wall",
                "body_rect": _axis_cylinder_envelope_rect(
                    axis="x",
                    x=tube_x,
                    y=center_y,
                    z=center_z,
                    length=straight_len + bend_r,
                    diameter=tube_od,
                ),
                "envelope_rect": tube_rect,
                "tube_retention": barb_retention,
                "material_intent": "COTS flexible gas tubing",
                "validation": "installed_tube_body_bend_envelope_checked_separately",
            }
            external_service_rects = [
                {"name": "printed_fitting_envelope", **fitting_rect},
                {"name": "printed_barb_retention_bead_envelope", **flange_rect},
                {"name": "strain_relief_envelope", **strain_relief_rect},
                {"name": "tube_envelope", **tube_rect},
            ]
            specs.append(
                {
                    "name": f"{role}_side_gas_service",
                    "role": role,
                    "owner_part": "lid_cover",
                    "service_role": f"production_operating_gas_{role}",
                    "side": side,
                    "port_axis": "x",
                    "duct_x": round(duct_x, 3),
                    "duct_y": round(center_y, 3),
                    "duct_z": round(center_z, 3),
                    "top_z": round(lid_top_z + block_h + threshold_h, 3),
                    "block_rect": {
                        "x": round(block_x, 3),
                        "y": round(center_y - block_w / 2, 3),
                        "z": round(lid_top_z, 3),
                        "length_x": round(block_depth, 3),
                        "width_y": round(block_w, 3),
                        "height_z": round(block_h, 3),
                    },
                    "duct_opening": {
                        "axis": "x",
                        "x": round(duct_opening_x, 3),
                        "y": round(center_y, 3),
                        "z": round(center_z, 3),
                        "length": round(block_depth + 0.4, 3),
                        "diameter": round(opening_d, 3),
                    },
                    "printed_fitting": {
                        "axis": "x",
                        "x": round(stem_start_x, 3),
                        "y": round(center_y, 3),
                        "z": round(center_z, 3),
                        "length": round(stem_len, 3),
                        "diameter": round(fitting_d, 3),
                    },
                    "printed_barb_retention_bead": {
                        "axis": "x",
                        "x": round(flange_start_x, 3),
                        "y": round(center_y, 3),
                        "z": round(center_z, 3),
                        "length": round(flange_w, 3),
                        "diameter": round(flange_d, 3),
                        "role": "tube_pulloff_resistance_without_glue",
                    },
                    "tube_retention": barb_retention,
                    "strain_relief_rect": {
                        **strain_relief_rect,
                    },
                    "leak_management": "outboard_visible_witness_gutters_with_inboard_dam",
                    "leak_flow_direction": leak_flow_direction,
                    "leak_witness_gutter_rects": leak_gutters,
                    "leak_witness_threshold_rects": leak_thresholds,
                    "tube_envelope_rect": tube_rect,
                    "installed_tube": installed_tube,
                    "external_service_rects": external_service_rects,
                    "tube_min_bend_radius": round(bend_r, 3),
                    "validation": "side_connected_supply_return_no_top_gas_caps",
                }
            )
        return specs

    block_depth = row["side_margin_y"] + duct_w / 2
    gutter_len = max(block_depth - threshold_w, 0.1)
    centers_x = {
        "supply": row["end_margin_x"] + center_offset,
        "return": float(layout["length_x"]) - row["end_margin_x"] - center_offset,
    }
    specs = []
    for role, center_x in centers_x.items():
        is_supply = role == "supply"
        side = "rear" if is_supply else "front"
        if is_supply:
            duct_y = float(layout["width_y"]) - row["side_margin_y"]
            flange_start_y = float(layout["width_y"]) + stem_len - flange_w / 2
            duct_opening_y = float(layout["width_y"]) - block_depth - 0.2
            gutter_y = float(layout["width_y"]) - gutter_len
            threshold_y = float(layout["width_y"]) - block_depth
            leak_flow_direction = "+Y_to_visible_outer_edge"
        else:
            duct_y = row["side_margin_y"]
            flange_start_y = -stem_len - flange_w / 2
            duct_opening_y = -0.2
            gutter_y = 0.0
            threshold_y = block_depth - threshold_w
            leak_flow_direction = "-Y_to_visible_outer_edge"
        block_y = float(layout["width_y"]) - block_depth if is_supply else 0.0
        tube_y = float(layout["width_y"]) if is_supply else -straight_len - bend_r
        stem_start_y = float(layout["width_y"]) if is_supply else -stem_len
        fitting_rect = _axis_cylinder_envelope_rect(
            axis="y",
            x=center_x,
            y=stem_start_y,
            z=center_z,
            length=stem_len,
            diameter=fitting_d,
        )
        flange_rect = _axis_cylinder_envelope_rect(
            axis="y",
            x=center_x,
            y=flange_start_y,
            z=center_z,
            length=flange_w,
            diameter=flange_d,
        )
        leak_gutters = [
            {
                "x": round(center_x - witness_offset - witness_w / 2, 3),
                "y": round(gutter_y, 3),
                "z": round(lid_top_z + block_h - witness_d, 3),
                "length_x": round(witness_w, 3),
                "width_y": round(gutter_len, 3),
                "height_z": round(witness_d, 3),
            },
            {
                "x": round(center_x + witness_offset - witness_w / 2, 3),
                "y": round(gutter_y, 3),
                "z": round(lid_top_z + block_h - witness_d, 3),
                "length_x": round(witness_w, 3),
                "width_y": round(gutter_len, 3),
                "height_z": round(witness_d, 3),
            },
        ]
        leak_thresholds = [
            {
                "x": round(center_x - block_w / 2, 3),
                "y": round(threshold_y, 3),
                "z": round(lid_top_z + block_h, 3),
                "length_x": round(block_w, 3),
                "width_y": round(threshold_w, 3),
                "height_z": round(threshold_h, 3),
            }
        ]
        strain_relief_rect = {
            "x": round(center_x - relief_w / 2, 3),
            "y": round(float(layout["width_y"]) if is_supply else -relief_len, 3),
            "z": round(center_z - relief_h / 2, 3),
            "length_x": round(relief_w, 3),
            "width_y": round(relief_len, 3),
            "height_z": round(relief_h, 3),
        }
        tube_rect = {
            "x": round(center_x - tube_d / 2, 3),
            "y": round(tube_y, 3),
            "z": round(center_z - tube_d / 2, 3),
            "length_x": round(tube_d, 3),
            "width_y": round(straight_len + bend_r, 3),
            "height_z": round(tube_d, 3),
        }
        installed_tube = {
            "name": f"{role}_cots_gas_tube_pigtail",
            "role": role,
            "owner_part": "cots_gas_service_tubes",
            "service_role": f"installed_operating_gas_{role}_tube",
            "axis": "y",
            "route_axis": "+Y" if is_supply else "-Y",
            "x": round(center_x, 3),
            "y": round(tube_y, 3),
            "z": round(center_z, 3),
            "length": round(straight_len + bend_r, 3),
            "diameter": round(tube_od, 3),
            "inner_diameter": round(tube_id, 3),
            "flow_bore_diameter": round(tube_id, 3),
            "geometry": "hollow_tube_wall",
            "body_rect": _axis_cylinder_envelope_rect(
                axis="y",
                x=center_x,
                y=tube_y,
                z=center_z,
                length=straight_len + bend_r,
                diameter=tube_od,
            ),
            "envelope_rect": tube_rect,
            "tube_retention": barb_retention,
            "material_intent": "COTS flexible gas tubing",
            "validation": "installed_tube_body_bend_envelope_checked_separately",
        }
        external_service_rects = [
            {"name": "printed_fitting_envelope", **fitting_rect},
            {"name": "printed_barb_retention_bead_envelope", **flange_rect},
            {"name": "strain_relief_envelope", **strain_relief_rect},
            {"name": "tube_envelope", **tube_rect},
        ]
        specs.append(
            {
                "name": f"{role}_side_gas_service",
                "role": role,
                "owner_part": "lid_cover",
                "service_role": f"production_operating_gas_{role}",
                "side": side,
                "port_axis": "y",
                "duct_x": round(center_x, 3),
                "duct_y": round(duct_y, 3),
                "duct_z": round(center_z, 3),
                "top_z": round(lid_top_z + block_h + threshold_h, 3),
                "block_rect": {
                    "x": round(center_x - block_w / 2, 3),
                    "y": round(block_y, 3),
                    "z": round(lid_top_z, 3),
                    "length_x": round(block_w, 3),
                    "width_y": round(block_depth, 3),
                    "height_z": round(block_h, 3),
                },
                "duct_opening": {
                    "axis": "y",
                    "x": round(center_x, 3),
                    "y": round(duct_opening_y, 3),
                    "z": round(center_z, 3),
                    "length": round(block_depth + 0.4, 3),
                    "diameter": round(opening_d, 3),
                },
                "printed_fitting": {
                    "axis": "y",
                    "x": round(center_x, 3),
                    "y": round(stem_start_y, 3),
                    "z": round(center_z, 3),
                    "length": round(stem_len, 3),
                    "diameter": round(fitting_d, 3),
                },
                "printed_barb_retention_bead": {
                    "axis": "y",
                    "x": round(center_x, 3),
                    "y": round(flange_start_y, 3),
                    "z": round(center_z, 3),
                    "length": round(flange_w, 3),
                    "diameter": round(flange_d, 3),
                    "role": "tube_pulloff_resistance_without_glue",
                },
                "tube_retention": barb_retention,
                "strain_relief_rect": {
                    **strain_relief_rect,
                },
                "leak_management": "outboard_visible_witness_gutters_with_inboard_dam",
                "leak_flow_direction": leak_flow_direction,
                "leak_witness_gutter_rects": leak_gutters,
                "leak_witness_threshold_rects": leak_thresholds,
                "tube_envelope_rect": tube_rect,
                "installed_tube": installed_tube,
                "external_service_rects": external_service_rects,
                "tube_min_bend_radius": round(bend_r, 3),
                "validation": "side_connected_supply_return_no_top_gas_caps",
            }
        )
    return specs


def _side_gas_tube_envelopes(
    interfaces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "name": f"{interface['name']}_tube_bend_envelope",
            "role": interface["role"],
            **interface["tube_envelope_rect"],
            "min_bend_radius": interface["tube_min_bend_radius"],
        }
        for interface in interfaces
    ]


def _side_gas_tube_envelope_check(
    tube_envelopes: list[dict[str, Any]],
) -> dict[str, Any]:
    envelope_lengths = [
        max(float(rect["length_x"]), float(rect["width_y"])) for rect in tube_envelopes
    ]
    bend_radii = {round(float(rect["min_bend_radius"]), 3) for rect in tube_envelopes}
    max_envelope_length = max(envelope_lengths, default=0.0)
    min_bend_radius = min(bend_radii, default=0.0)
    return {
        "name": "side_gas_tube_envelope_check",
        "role": "side_gas_tube_bend_and_strain_relief_validation_body",
        "validation": "required_gate2_tube_bend_and_retention_evidence",
        "failure_rule": (
            "kink_pull_off_or_unmeasured_tube_bend_blocks_dry_assembly_pass"
        ),
        "evidence_gate": "Gate 2 dry assembly",
        "cad_value": (
            f"{len(tube_envelopes)} tubes / {max_envelope_length:.2f} mm envelope / "
            f"{min_bend_radius:.2f} mm bend radius"
        ),
        "tube_count": len(tube_envelopes),
        "max_envelope_length_mm": round(max_envelope_length, 3),
        "min_bend_radius": round(min_bend_radius, 3),
        "tube_roles": tuple(rect["role"] for rect in tube_envelopes),
        "source_layout_checks": ["side_gas_service_interfaces"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "operating_gas_supply_connected",
            "operating_gas_return_connected",
            "tube_pulloff_resistance_without_glue",
        ],
        "body_rects": tube_envelopes,
    }


def _side_gas_leak_witness_check(
    interfaces: list[dict[str, Any]],
) -> dict[str, Any]:
    wet_collectors = [
        rect
        for interface in interfaces
        for rect in interface["leak_witness_gutter_rects"]
    ]
    inboard_dams = [
        rect
        for interface in interfaces
        for rect in interface["leak_witness_threshold_rects"]
    ]
    body_rects = [*wet_collectors, *inboard_dams]
    return {
        "name": "side_gas_leak_witness_check",
        "role": "side_gas_wet_failure_witness_validation_body",
        "validation": "required_gate4_side_gas_wet_witness_evidence",
        "failure_rule": (
            "side_gas_leak_without_visible_collector_or_inboard_dam_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{len(wet_collectors)} wet collectors / {len(inboard_dams)} inboard dams"
        ),
        "wet_collector_count": len(wet_collectors),
        "inboard_dam_count": len(inboard_dams),
        "service_count": len(interfaces),
        "source_layout_checks": ["side_gas_service_interfaces"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "wet_operation_with_connected_side_gas",
            "dry_bay_protection_from_side_gas_leak",
        ],
        "body_rects": body_rects,
    }


def _cots_gas_service_tubes(
    interfaces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [interface["installed_tube"] for interface in interfaces]


def _unseated_side_gas_tube_review_specs(
    gas_service_tubes: list[dict[str, Any]],
    *,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    offset = float(production.get("side_gas_unseated_review_offset_xy", 8.0))
    if offset <= 0:
        raise ValueError("side gas unseated review offset must be positive")

    review_specs: list[dict[str, Any]] = []
    for tube in gas_service_tubes:
        axis = str(tube["axis"])
        route = str(tube["route_axis"])
        dx = dy = 0.0
        if axis == "x":
            dx = -offset if route == "-X" else offset
        elif axis == "y":
            dy = offset if route == "+Y" else -offset
        else:
            raise ValueError("side gas tube unseated review requires x or y axis")

        x = round(float(tube["x"]) + dx, 3)
        y = round(float(tube["y"]) + dy, 3)
        z = round(float(tube["z"]), 3)
        body_rect = _axis_cylinder_envelope_rect(
            axis=axis,
            x=x,
            y=y,
            z=z,
            length=float(tube["length"]),
            diameter=float(tube["diameter"]),
        )
        review_specs.append(
            {
                "name": f"{tube['role']}_unseated_side_gas_tube_review",
                "role": tube["role"],
                "owner_part": "unseated_side_gas_tubes_review",
                "review_state": "side_gas_tubes_unseated",
                "review_kind": "unseated_cots_gas_tube",
                "removed_part": "cots_gas_service_tubes",
                "source_rect_name": tube["name"],
                "axis": axis,
                "route_axis": route,
                "x": x,
                "y": y,
                "z": z,
                "length": tube["length"],
                "diameter": tube["diameter"],
                "inner_diameter": tube["inner_diameter"],
                "flow_bore_diameter": tube["flow_bore_diameter"],
                "unseated_offset_xy": round(offset, 3),
                "body_rect": body_rect,
                "meaning": "COTS gas tube is present but pulled off the printed barb",
            }
        )
    return review_specs


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


def _side_gas_adjacent_slot_clearance(
    interfaces: list[dict[str, Any]],
    adjacent_keepouts: list[dict[str, Any]],
    *,
    params: dict[str, Any],
) -> dict[str, Any]:
    required = params["deck_interface"].get("side_service_vertical_clearance_z", 0.0)
    overlaps: list[dict[str, Any]] = []
    min_clearance: float | None = None
    for interface in interfaces:
        for rect in interface["external_service_rects"]:
            for keepout in adjacent_keepouts:
                if not _rectangles_overlap_xy(rect, keepout):
                    continue
                clearance = float(rect["z"]) - (
                    float(keepout["z"]) + float(keepout["height_z"])
                )
                min_clearance = (
                    clearance
                    if min_clearance is None
                    else min(min_clearance, clearance)
                )
                overlaps.append(
                    {
                        "service": interface["role"],
                        "service_rect": rect["name"],
                        "adjacent_keepout": keepout["name"],
                        "vertical_clearance_z": round(clearance, 3),
                    }
                )
    min_value = float("inf") if min_clearance is None else min_clearance
    return {
        "required_vertical_clearance_z": round(required, 3),
        "min_vertical_clearance_z": round(min_value, 3) if overlaps else None,
        "xy_overlap_count": len(overlaps),
        "meets_vertical_clearance": bool(not overlaps or min_value >= required),
        "clearance_evidence": overlaps,
        "interpretation": "side_services_use_reserved_adjacent_slot_overhead",
    }


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


def _observer_box_cad_value(rect: dict[str, Any]) -> str:
    return (
        f"{float(rect['length_x']):.2f} x "
        f"{float(rect['width_y']):.2f} x "
        f"{float(rect['height_z']):.2f} mm"
    )


def _observer_body_rect(rect: dict[str, Any], *, name: str, role: str) -> dict[str, Any]:
    return {
        "name": name,
        "role": role,
        "x": rect["x"],
        "y": rect["y"],
        "z": rect["z"],
        "length_x": rect["length_x"],
        "width_y": rect["width_y"],
        "height_z": rect["height_z"],
    }


def _observer_front_end_swept_body_check(
    rect: dict[str, Any],
    *,
    dry_bay_envelope: dict[str, Any],
    covered_well_count: int,
    front_end_length_x: float,
    front_end_width_y: float,
    front_end_height_z: float,
    front_end_focus_stroke_z: float,
    front_end_top_clearance_z: float,
    front_end_service_margin_z: float,
    front_end_barrel_diameter: float,
    scan_corridor_footprint_max: float,
    objective_keepout_diameter: float,
    carriage_height_z: float,
) -> dict[str, Any]:
    body_rect = _observer_body_rect(
        rect,
        name="observer_front_end_swept_body",
        role="compact dry observer front-end swept volume",
    )
    # Falsifiable closure checks against independent params (not the well-derived
    # swept body, which is tautological by construction). The head body + its
    # focus travel + plate standoff + service margin must fit the carriage
    # vertical envelope. The footprint value is the CIRCUMSCRIBED diameter of the
    # rectangular head cross-section (a conservative upper bound), not a measured
    # round-barrel diameter -- it stands in for the doc's "barrel Ø <= keepout"
    # gate until Stage 0 measures the real barrel. When the real (possibly larger)
    # head bbox lands, split this into barrel-Ø-vs-keepout and head-bbox-vs-dry-bay.
    footprint_circumscribed_diameter = round(
        (front_end_length_x ** 2 + front_end_width_y ** 2) ** 0.5,
        3,
    )
    vertical_budget_required = round(
        front_end_top_clearance_z
        + front_end_height_z
        + front_end_focus_stroke_z
        + front_end_service_margin_z,
        3,
    )
    # Gate the swept body's own containment in the dry bay. Previously this was
    # enforced only by a layout-level test; encoding it on the check makes it a
    # first-class blocker, so an oversized front-end body (e.g. a larger measured
    # `front_end_length_x`) reports an overflow here instead of silently passing.
    body_overflow, body_fits_dry_bay = _dry_bay_containment(rect, dry_bay_envelope)
    return {
        **rect,
        "name": "observer_front_end_swept_body_check",
        "role": "compact_dry_observer_front_end_swept_volume_validation_body",
        "validation": "required_gate6_observer_front_end_swept_body_evidence",
        "failure_rule": (
            "front_end_collision_or_unmeasured_sweep_blocks_observer_readiness"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": _observer_box_cad_value(rect),
        "covered_well_count": covered_well_count,
        "front_end_footprint_circumscribed_diameter_mm": (
            footprint_circumscribed_diameter
        ),
        "objective_keepout_diameter_mm": round(float(objective_keepout_diameter), 3),
        "front_end_fits_objective_keepout": (
            footprint_circumscribed_diameter <= float(objective_keepout_diameter)
        ),
        # OC-A9: split the conflated check. The circumscribed diameter above is a
        # CONSERVATIVE bound on the whole head cross-section (incl. the camera arm);
        # the real per-well keepout is about the round objective BARREL, an
        # independent measured param. The barrel is the authoritative keepout gate;
        # the head bounding box is gated against the dry bay by front_end_body_fits_dry_bay.
        "front_end_barrel_diameter_mm": round(float(front_end_barrel_diameter), 3),
        "front_end_barrel_fits_keepout": (
            float(front_end_barrel_diameter) <= float(objective_keepout_diameter)
        ),
        # OC-A15 (diagnostic, surfaced not gated): a round barrel cannot fit a head
        # narrower than its diameter, and the plate-level traverse sweep is set by the
        # WIDER of (head footprint, barrel). With the current placeholders the Ø25
        # barrel exceeds the 13 mm head width -> this is FALSE, flagging that the
        # razor-thin traverse margin (built on the 13 mm footprint) does not account
        # for a realistic objective barrel. Resolution is measurement-gated (Stage-0)
        # / a design decision; see decision_log.md. Surfaced, not in the fit chain, so
        # it does not autonomously overturn the dry-bay "fits" conclusion.
        "front_end_barrel_within_head_footprint": (
            float(front_end_barrel_diameter)
            <= min(float(front_end_length_x), float(front_end_width_y))
            + _TRAVERSE_FIT_TOLERANCE_MM
        ),
        # OC-A15 (diagnostic, surfaced not gated): does the DECLARED barrel thread the
        # scan-axis corridor? The traverse fit chain reads the placeholder scan footprint
        # (not the barrel), so it ships green; this mirrors the SMIS dock gate
        # (scan_corridor_footprint_max) on the SAME number so CAD and SMIS cannot silently
        # disagree about a real Ø-barrel head. Currently FALSE (Ø25 > 21.2).
        "scan_corridor_footprint_max_mm": round(float(scan_corridor_footprint_max), 3),
        "barrel_threads_scan_corridor": (
            float(front_end_barrel_diameter)
            <= float(scan_corridor_footprint_max) + _TRAVERSE_FIT_TOLERANCE_MM
        ),
        "vertical_budget_required_mm": vertical_budget_required,
        "carriage_height_budget_mm": round(float(carriage_height_z), 3),
        "front_end_vertical_budget_closes": (
            vertical_budget_required <= float(carriage_height_z)
        ),
        "front_end_body_fits_dry_bay": body_fits_dry_bay,
        "front_end_body_overflow_mm": body_overflow,
        "dry_bay_bounds_mm": {
            "x": round(float(dry_bay_envelope["length_x"]), 2),
            "y": round(float(dry_bay_envelope["width_y"]), 2),
            "z": round(
                float(dry_bay_envelope["top_z"])
                - float(dry_bay_envelope["bottom_z"]),
                2,
            ),
        },
        "source_layout_checks": [
            "dry_bay_envelope_check",
            "observer_fiducial_focus_target_check",
            "observer_kinematic_split_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "observer_front_end_clearance",
            "all_well_observer_access",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": [body_rect],
    }


def _observer_infinity_port_datum_check(
    front_end_check: dict[str, Any],
    *,
    pd0_offset_from_objective_shoulder_z: float,
    clear_aperture_diameter: float,
    cage_standard_mm: float,
    rms_thread_present: bool,
    c_mount_present: bool,
    tube_lens_to_sensor_mm: float,
    objective_keepout_diameter: float,
) -> dict[str, Any]:
    """SM-2.1: make the SMIS infinity-port optical datum falsifiable in CAD."""

    top_z = float(front_end_check["z"]) + float(front_end_check["height_z"])
    pd0_z = round(top_z - float(pd0_offset_from_objective_shoulder_z), 3)
    datum_thickness = 0.5
    rect = {
        "x": front_end_check["x"],
        "y": front_end_check["y"],
        "z": pd0_z - datum_thickness / 2.0,
        "length_x": front_end_check["length_x"],
        "width_y": front_end_check["width_y"],
        "height_z": datum_thickness,
    }
    body_rect = _observer_body_rect(
        rect,
        name="observer_infinity_port_pd0_datum",
        role="SMIS infinity-port PD-0 swept datum plane",
    )
    pd0_within_front_end_z = float(front_end_check["z"]) <= pd0_z <= top_z
    clear_aperture_fits_keepout = (
        float(clear_aperture_diameter) <= float(objective_keepout_diameter)
    )
    clear_aperture_fits_cage = float(clear_aperture_diameter) <= float(cage_standard_mm)
    tube_lens_spacing_frozen = float(tube_lens_to_sensor_mm) == 50.0
    optical_standard_complete = bool(rms_thread_present and c_mount_present)

    blockers: list[str] = []
    if not pd0_within_front_end_z:
        blockers.append("pd0_datum_outside_front_end_z")
    if not clear_aperture_fits_keepout:
        blockers.append("infinity_port_aperture_exceeds_objective_keepout")
    if not clear_aperture_fits_cage:
        blockers.append("infinity_port_aperture_exceeds_cage_standard")
    if not optical_standard_complete:
        blockers.append("infinity_port_missing_rms_or_c_mount")
    if not tube_lens_spacing_frozen:
        blockers.append("tube_lens_to_sensor_spacing_drift")

    return {
        **rect,
        "name": "observer_infinity_port_datum_check",
        "role": "SMIS_infinity_port_PD0_datum_validation_body",
        "validation": "required_gate6_observer_infinity_port_datum_evidence",
        "failure_rule": (
            "missing_or_unmeasured_infinity_port_datum_blocks_SMIS_level1_swap"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": _observer_box_cad_value(rect),
        "pd0_offset_from_objective_shoulder_z_mm": round(
            float(pd0_offset_from_objective_shoulder_z),
            3,
        ),
        "pd0_z_mm": pd0_z,
        "pd0_within_front_end_z": pd0_within_front_end_z,
        "clear_aperture_diameter_mm": round(float(clear_aperture_diameter), 3),
        "objective_keepout_diameter_mm": round(float(objective_keepout_diameter), 3),
        "clear_aperture_fits_keepout": clear_aperture_fits_keepout,
        "cage_standard_mm": round(float(cage_standard_mm), 3),
        "clear_aperture_fits_cage_standard": clear_aperture_fits_cage,
        "rms_thread_present": bool(rms_thread_present),
        "c_mount_present": bool(c_mount_present),
        "optical_standard_complete": optical_standard_complete,
        "tube_lens_to_sensor_mm": round(float(tube_lens_to_sensor_mm), 3),
        "tube_lens_to_sensor_spacing_frozen": tube_lens_spacing_frozen,
        "infinity_port_geometry_clears": not blockers,
        "infinity_port_geometry_blockers": sorted(blockers),
        "source_layout_checks": [
            "observer_front_end_swept_body_check",
            "observer_optical_stability_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "SMIS_level1_backend_swap",
            "parfocal_infinity_port_registration",
            "fluorescence_dichroic_backend_install",
        ],
        "body_rects": [body_rect],
    }


_TRAVERSE_FIT_TOLERANCE_MM = 1.0e-6
# OC-A12: margins at or below this (but still positive) are flagged razor-thin so a
# sub-mm param drift consuming the budget is visible before it tips into overflow.
_RAZOR_THIN_MARGIN_WARN_MM = 0.5


def _dry_bay_containment(
    rect: dict[str, Any],
    dry_bay_envelope: dict[str, Any],
) -> tuple[dict[str, float], bool]:
    """Two-sided dry-bay containment of a reserved-volume rect on X/Y/Z.

    Single source for "does this observer body fit the dry bay" -- used by the
    front-end swept body and the static carriage box. overflow = how far the rect
    overhangs either side of the bay on each axis; fits = no axis overhangs beyond
    the fit tolerance. The dry bay names Z as bottom_z/top_z, not z/height_z.
    """
    db_x0 = float(dry_bay_envelope["x"])
    db_x1 = db_x0 + float(dry_bay_envelope["length_x"])
    db_y0 = float(dry_bay_envelope["y"])
    db_y1 = db_y0 + float(dry_bay_envelope["width_y"])
    db_z0 = float(dry_bay_envelope["bottom_z"])
    db_z1 = float(dry_bay_envelope["top_z"])
    bx0 = float(rect["x"])
    bx1 = bx0 + float(rect["length_x"])
    by0 = float(rect["y"])
    by1 = by0 + float(rect["width_y"])
    bz0 = float(rect["z"])
    bz1 = bz0 + float(rect["height_z"])
    overflow = {
        "x": max(0.0, db_x0 - bx0) + max(0.0, bx1 - db_x1),
        "y": max(0.0, db_y0 - by0) + max(0.0, by1 - db_y1),
        "z": max(0.0, db_z0 - bz0) + max(0.0, bz1 - db_z1),
    }
    fits = all(o <= _TRAVERSE_FIT_TOLERANCE_MM for o in overflow.values())
    return {k: round(v, 3) for k, v in overflow.items()}, fits


def _observer_carriage_traverse(
    *,
    row_axis: str,
    well_xs: list[float],
    well_ys: list[float],
    gantry_truck_traverse_extent: float,
    front_end_length_x: float,
    front_end_width_y: float,
    front_end_scan_axis_footprint: float,
    swept_z: float,
    swept_height_z: float,
    dry_bay_envelope: dict[str, Any],
    deck_feet: list[dict[str, Any]],
    adjacent_keepouts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Sweep the continuously-traversing observer structure across the whole row.

    The head that images every well must traverse the full row. Modeled today
    only as a static carriage box at the plate-1 end, it had no swept-volume
    check while every other observer body did. This computes the swept extent on
    BOTH axes so the geometry is surfaced as data rather than hidden.

    Traverse axis -- the resolution of the 44.6 mm overflow the earlier model
    flagged: the gantry beam that traverses the row must be THIN on the traverse
    axis (`gantry_truck_traverse_extent`, ~13 mm), not the 58 mm `carriage_width_y`
    the reserved carriage box allotted. Everything that rides the row in the
    traverse direction -- beam, head, rails -- has to fit inside that ~13 mm; the
    58 mm cross-section was an over-reservation. At 13 mm it clears the 347.9 mm
    dry-bay Y by ~0.4 mm; a truck wider than ~13.4 mm overflows again.

    Scan axis -- where the earlier Y fix RELOCATED its burden, surfaced here so it
    is not hidden: the head scans the columns, so the scan-axis swept extent is
    the well span (99 mm) plus the head's scan-axis footprint
    (`front_end_scan_axis_footprint`). After the 99 mm well span the dry-bay X
    leaves only ~0.2 mm of budget -- barely the bare objective barrel. The
    placeholder value (21 mm) is the objective alone and EXCLUDES the post-fold
    camera arm (tube lens + sensor). There is NO room to route that arm along X
    (the prior "place the bulk along the ~120 mm beam X-length" claim was wrong:
    the residual after the well span is ~0.2 mm, not 120 mm) -- the camera must be
    folded coaxially over the objective or taken offboard. If a measured
    scan-axis footprint exceeds the objective by more than ~0.2 mm, this reports
    an X overflow and the traverse blocks again, now on X.

    This proves only that the thin-truck TOPOLOGY fits geometrically, and only
    against PLACEHOLDER head footprints (21/13 mm, camera arm excluded) -- the
    real footprints, the achievable beam width, and the camera-routing strategy
    are Stage-0/Stage-3 caliper work. Whether a ~13 mm beam can physically carry
    the head and traverse 334.5 mm repeatably inside the bench's hold-still spec
    stays Gate-6 blocked. Reports a swept bounding box plus per-keepout intrusion
    (deck feet, adjacent OT-2 slots) using the same overlap machinery the
    front-end body uses.
    """
    truck = float(gantry_truck_traverse_extent)
    # Scan-axis span = the head footprint along the scan axis. It must be at least
    # the bare body extent on that axis (the camera arm only adds, never subtracts):
    # tying it to the body length closes a decoupling bug where an oversized body
    # (`front_end_length_x`) overflows the bay while the traverse, reading only the
    # smaller scan-footprint param, still reports "fits".
    if row_axis == "y":
        scan = max(float(front_end_scan_axis_footprint), float(front_end_length_x))
        span_x = scan  # scan axis (X): head footprint incl. camera arm, >= body X
        span_y = max(truck, float(front_end_width_y))  # traverse axis (Y)
    else:
        scan = max(float(front_end_scan_axis_footprint), float(front_end_width_y))
        span_x = max(truck, float(front_end_length_x))  # traverse axis (X)
        span_y = scan  # scan axis (Y): head footprint incl. camera arm, >= body Y
    # Compute the fit decision from UNROUNDED extents so a sub-micron overflow
    # cannot be absorbed by display rounding before the subtraction; round only
    # for the reported rect/overflow fields.
    raw_length_x = max(well_xs) - min(well_xs) + span_x
    raw_width_y = max(well_ys) - min(well_ys) + span_y
    swept_x = round(min(well_xs) - span_x / 2, 3)
    swept_y = round(min(well_ys) - span_y / 2, 3)
    swept_length_x = round(raw_length_x, 3)
    swept_width_y = round(raw_width_y, 3)
    # The traverse overflow is 2D (X/Y) and swept-length-based (extent vs bay span),
    # NOT absolute placement: Z containment and absolute-placement containment of the
    # head are owned by the front-end-body check (`_dry_bay_containment`), which the
    # OC-A2 scan-span tie keeps consistent with this. Do not assume the two agree in
    # the sub-mm margin band -- they answer different questions by design.
    raw_overflow_x = max(0.0, raw_length_x - float(dry_bay_envelope["length_x"]))
    raw_overflow_y = max(0.0, raw_width_y - float(dry_bay_envelope["width_y"]))
    swept_rect = {
        "x": swept_x,
        "y": swept_y,
        "length_x": swept_length_x,
        "width_y": swept_width_y,
    }
    foot_hits = sum(
        1 for foot in deck_feet if _rectangles_overlap_xy(swept_rect, foot)
    )
    adjacent_hits = sum(
        1
        for keepout in adjacent_keepouts
        if _rectangles_overlap_xy(swept_rect, keepout)
    )
    # Decide fit on the unrounded overflow with an explicit tolerance; round only
    # for display so a sub-micron overflow can never silently read as a fit.
    fits_dry_bay = (
        raw_overflow_x <= _TRAVERSE_FIT_TOLERANCE_MM
        and raw_overflow_y <= _TRAVERSE_FIT_TOLERANCE_MM
    )
    clears_traverse = fits_dry_bay and foot_hits == 0 and adjacent_hits == 0
    # Both axes' fit margins -- surfaced because both are razor-thin: the traverse
    # turns on the truck staying thin (~0.4 mm), the scan axis on the head's
    # footprint staying near the bare objective (~0.2 mm, no room for the camera arm).
    traverse_margin = (
        float(dry_bay_envelope["width_y"]) - raw_width_y
        if row_axis == "y"
        else float(dry_bay_envelope["length_x"]) - raw_length_x
    )
    scan_margin = (
        float(dry_bay_envelope["length_x"]) - raw_length_x
        if row_axis == "y"
        else float(dry_bay_envelope["width_y"]) - raw_width_y
    )
    # OC-A15: the binding SCAN-axis wall is whichever is tightest of (a) the standoff-leg
    # corridor -- the clear gap between the 80 mm deck-engagement legs that straddle the
    # scan axis -- and (b) the milled dry-bay wall. The two are nearly co-located here:
    # the bay (X 13.7..133.9) is milled just INSIDE the legs (13.6..134.0), so the bay
    # hi-wall is actually ~0.1 mm tighter than the leg wall. Both span the head's Z sweep,
    # so a footprint wider than the tighter wall strikes it. We surface the corridor, the
    # per-wall bay clearance, and the binding minimum of the two; the razor-thin flag
    # tracks the binding wall, not just the corridor (which under-reported the bay wall).
    scan_lo, scan_hi = (
        (swept_x, swept_x + swept_length_x)
        if row_axis == "y"
        else (swept_y, swept_y + swept_width_y)
    )
    scan_mid = (scan_lo + scan_hi) / 2.0

    def _foot_near(f: dict[str, Any]) -> float:
        return float(f["x"]) if row_axis == "y" else float(f["y"])

    def _foot_far(f: dict[str, Any]) -> float:
        return (
            float(f["x"]) + float(f["length_x"])
            if row_axis == "y"
            else float(f["y"]) + float(f["width_y"])
        )

    # A foot whose BODY spans the scan centerline blocks the head outright (robustness
    # guard -- never triggers for the live symmetric corner-leg layout, but a centered
    # structural rib must not read as a one-sided wall).
    straddling = [f for f in deck_feet if _foot_near(f) < scan_mid < _foot_far(f)]
    left_legs = [_foot_far(f) for f in deck_feet if _foot_far(f) <= scan_mid]
    right_legs = [_foot_near(f) for f in deck_feet if _foot_near(f) >= scan_mid]
    if straddling:
        scan_corridor_width = 0.0
        scan_corridor_margin = round(min(scan_lo - scan_mid, scan_mid - scan_hi), 3)
    elif left_legs and right_legs:
        corridor_lo, corridor_hi = max(left_legs), min(right_legs)
        scan_corridor_width = round(corridor_hi - corridor_lo, 3)
        scan_corridor_margin = round(min(scan_lo - corridor_lo, corridor_hi - scan_hi), 3)
    else:
        # No deck legs in scope (synthetic call): corridor unknown.
        scan_corridor_width = None
        scan_corridor_margin = None

    # Per-wall dry-bay scan clearance (min of the two walls), the OTHER real wall.
    # .get for x/y so synthetic unit calls (which pass only length_x/width_y) still work.
    if row_axis == "y":
        bay_origin = float(dry_bay_envelope.get("x", 0.0))
        bay_scan_lo, bay_scan_hi = bay_origin, bay_origin + float(dry_bay_envelope["length_x"])
    else:
        bay_origin = float(dry_bay_envelope.get("y", 0.0))
        bay_scan_lo, bay_scan_hi = bay_origin, bay_origin + float(dry_bay_envelope["width_y"])
    scan_bay_per_wall_margin = round(min(scan_lo - bay_scan_lo, bay_scan_hi - scan_hi), 3)
    # Binding scan margin = the tightest of the leg corridor and the per-wall bay wall.
    binding_candidates = [scan_bay_per_wall_margin]
    if scan_corridor_margin is not None:
        binding_candidates.append(scan_corridor_margin)
    effective_scan_margin = min(binding_candidates)
    # The traverse sweeps the MOVING HEAD's Z extent (the front-end swept body,
    # ~40 mm), NOT the static carriage box's 62 mm -- the head, not the parked carrier,
    # is what rides the row. Z containment / absolute placement is owned by the
    # front-end-body check (`_dry_bay_containment`); this is surfaced for consistency.
    z_within_dry_bay = (
        swept_z >= float(dry_bay_envelope["bottom_z"]) - _TRAVERSE_FIT_TOLERANCE_MM
        and swept_z + swept_height_z
        <= float(dry_bay_envelope["top_z"]) + _TRAVERSE_FIT_TOLERANCE_MM
    )
    return {
        "traverse_axis": row_axis,
        "x": swept_x,
        "y": swept_y,
        "z": round(float(swept_z), 3),
        "length_x": swept_length_x,
        "width_y": swept_width_y,
        "height_z": round(float(swept_height_z), 3),
        "z_within_dry_bay": z_within_dry_bay,
        "traverse_structure": "thin_gantry_truck",
        "gantry_truck_traverse_extent_mm": round(truck, 3),
        "traverse_axis_fit_margin_mm": round(traverse_margin, 3),
        # OC-A12: a positive-but-tiny margin still fits, but a sub-mm param drift would
        # tip it into overflow -- surface the razor-thinness so it can't erode silently.
        "traverse_margin_is_razor_thin": (
            0.0 <= traverse_margin <= _RAZOR_THIN_MARGIN_WARN_MM
        ),
        "scan_axis_footprint_mm": round(float(front_end_scan_axis_footprint), 3),
        "scan_axis_extent_mm": round(scan, 3),
        "scan_axis_fit_margin_mm": round(scan_margin, 3),
        # OC-A15: surface BOTH real scan walls (leg corridor + per-wall bay) and the
        # binding minimum. The bay hi-wall is actually the tightest here (~0.02 mm),
        # marginally inside the leg corridor (~0.12 mm); the razor-thin flag tracks the
        # binding minimum, not just the corridor.
        "scan_corridor_width_mm": scan_corridor_width,
        "scan_corridor_margin_mm": scan_corridor_margin,
        "scan_bay_per_wall_margin_mm": scan_bay_per_wall_margin,
        "scan_binding_margin_mm": round(effective_scan_margin, 3),
        "scan_margin_is_razor_thin": (
            0.0 <= effective_scan_margin <= _RAZOR_THIN_MARGIN_WARN_MM
        ),
        "razor_thin_margin_warn_threshold_mm": _RAZOR_THIN_MARGIN_WARN_MM,
        "scan_axis_footprint_excludes_camera_arm": True,
        "scan_axis_extent_is_head_inclusive": True,
        "dry_bay_overflow_x_mm": round(raw_overflow_x, 3),
        "dry_bay_overflow_y_mm": round(raw_overflow_y, 3),
        "fits_dry_bay": fits_dry_bay,
        "deck_foot_collision_count": foot_hits,
        "hits_deck_feet": foot_hits > 0,
        "adjacent_slot_collision_count": adjacent_hits,
        "enters_adjacent_slot": adjacent_hits > 0,
        "clears_traverse": clears_traverse,
    }


def _observer_carriage_envelope_check(
    rect: dict[str, Any],
    *,
    dry_bay_envelope: dict[str, Any],
    carriage_traverse: dict[str, Any],
) -> dict[str, Any]:
    body_rect = _observer_body_rect(
        rect,
        name="observer_carriage_reserved_volume",
        role="dry observer carriage reserved volume",
    )
    # Gate the STATIC carriage box's own dry-bay containment -- same class as the
    # front-end-body gate. Without this an oversized carriage box overflows the bay
    # while only the swept-truck traverse is checked. The box is parked at the row
    # end, so at live params it fits; this catches a bad reserved dimension.
    box_overflow, box_fits_dry_bay = _dry_bay_containment(rect, dry_bay_envelope)
    return {
        **rect,
        "name": "observer_carriage_envelope_check",
        "role": "dry_observer_carriage_reserved_volume_validation_body",
        "validation": "required_gate6_observer_carriage_envelope_evidence",
        "failure_rule": (
            "carriage_intrusion_or_unmeasured_reserved_volume_blocks_observer_readiness"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": _observer_box_cad_value(rect),
        "carriage_traverse": carriage_traverse,
        "traverse_fits_dry_bay": carriage_traverse["fits_dry_bay"],
        "carriage_box_fits_dry_bay": box_fits_dry_bay,
        "carriage_box_overflow_mm": box_overflow,
        "dry_bay_bounds_mm": {
            "x": round(float(dry_bay_envelope["length_x"]), 2),
            "y": round(float(dry_bay_envelope["width_y"]), 2),
            "z": round(
                float(dry_bay_envelope["top_z"])
                - float(dry_bay_envelope["bottom_z"]),
                2,
            ),
        },
        "source_layout_checks": [
            "dry_bay_envelope_check",
            "observer_front_end_swept_body_check",
            "observer_kinematic_split_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "observer_carriage_clearance",
            "observer_carriage_traverse_clearance",
            "observer_kinematic_split",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": [body_rect],
    }


def _observer_service_raceway_envelope_check(
    rect: dict[str, Any],
    *,
    dry_bay_envelope: dict[str, Any],
    service_bend_radius: float,
) -> dict[str, Any]:
    body_rect = _observer_body_rect(
        rect,
        name="observer_service_raceway_envelope",
        role="dry observer service loop raceway volume",
    )
    # OC-A3: falsifiable raceway asserts (the check had none). The raceway is a
    # service volume that must (a) sit OUTSIDE the optical sweep -- no XY overlap with
    # the dry-bay envelope, or a flexing cable would foul the moving optics; (b) fit
    # the bay depth in Z; (c) reserve enough Z for the cable-chain loop, whose height
    # is ~2x the bend radius (an R10 chain loops to ~20 mm; the raceway reserves 24 mm).
    raceway_clears_dry_bay_sweep = not _rectangles_overlap_xy(rect, dry_bay_envelope)
    raceway_z_within_bay_depth = (
        float(rect["z"]) >= float(dry_bay_envelope["bottom_z"]) - _TRAVERSE_FIT_TOLERANCE_MM
        and float(rect["z"]) + float(rect["height_z"])
        <= float(dry_bay_envelope["top_z"]) + _TRAVERSE_FIT_TOLERANCE_MM
    )
    loop_height = 2.0 * float(service_bend_radius)
    r10_loop_margin = round(float(rect["height_z"]) - loop_height, 3)
    r10_loop_fits_raceway_z = loop_height <= float(rect["height_z"]) + _TRAVERSE_FIT_TOLERANCE_MM
    raceway_blockers: list[str] = []
    if not raceway_clears_dry_bay_sweep:
        raceway_blockers.append("raceway_intrudes_optical_sweep")
    if not raceway_z_within_bay_depth:
        raceway_blockers.append("raceway_exceeds_bay_depth")
    if not r10_loop_fits_raceway_z:
        raceway_blockers.append("cable_loop_exceeds_raceway_z")
    return {
        **rect,
        "name": "observer_service_raceway_envelope_check",
        "role": "dry_observer_service_loop_raceway_validation_body",
        "validation": "required_gate6_observer_service_raceway_evidence",
        "failure_rule": (
            "service_loop_snag_or_unmeasured_raceway_blocks_observer_readiness"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": _observer_box_cad_value(rect),
        "raceway_clears_dry_bay_sweep": raceway_clears_dry_bay_sweep,
        "raceway_z_within_bay_depth": raceway_z_within_bay_depth,
        "r10_loop_height_margin_mm": r10_loop_margin,
        "r10_loop_fits_raceway_z": r10_loop_fits_raceway_z,
        "raceway_geometry_blockers": sorted(raceway_blockers),
        "raceway_geometry_clears": not raceway_blockers,
        "dry_bay_bounds_mm": {
            "x": round(float(dry_bay_envelope["length_x"]), 2),
            "y": round(float(dry_bay_envelope["width_y"]), 2),
            "z": round(
                float(dry_bay_envelope["top_z"])
                - float(dry_bay_envelope["bottom_z"]),
                2,
            ),
        },
        "source_layout_checks": [
            "dry_bay_envelope_check",
            "observer_carriage_envelope_check",
            "observer_kinematic_split_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "observer_service_loop_recovery",
            "dry_bay_clearance_with_observer_services",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": [body_rect],
    }


def _lid_port_positions(
    layout: dict[str, Any],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    row = params["row"]
    lid = params["lid_manifold"]
    duct_w = lid["duct_width_y"]
    port_positions: list[dict[str, Any]] = []
    if layout["row_axis"] == "x":
        rear_duct_y = layout["width_y"] - row["side_margin_y"] - duct_w / 2
        port_positions.append(
            _lid_port_spec(
                name="sample_relief",
                role="sample_relief",
                x=layout["length_x"] / 2,
                y=rear_duct_y + duct_w / 2,
                boss_d=lid.get("sample_port_boss_diameter", 10.0),
                hole_d=lid.get("sample_port_hole_diameter", 3.0),
                boss_h=lid.get("sample_port_boss_height_z", 5.0),
                params=params,
            )
        )
        return port_positions

    right_duct_x = layout["length_x"] - row["end_margin_x"] - duct_w / 2
    port_positions.append(
        _lid_port_spec(
            name="sample_relief",
            role="sample_relief",
            x=right_duct_x + duct_w / 2,
            y=layout["width_y"] / 2,
            boss_d=lid.get("sample_port_boss_diameter", 10.0),
            hole_d=lid.get("sample_port_hole_diameter", 3.0),
            boss_h=lid.get("sample_port_boss_height_z", 5.0),
            params=params,
        )
    )
    return port_positions


def _lid_port_spec(
    *,
    name: str,
    role: str,
    x: float,
    y: float,
    boss_d: float,
    hole_d: float,
    boss_h: float,
    params: dict[str, Any],
) -> dict[str, Any]:
    production = params.get("production_assembly", {})
    cap_clearance = production.get("port_cap_plug_clearance_diameter", 0.0)
    cap_overhang = production.get("port_cap_flange_overhang_xy", 0.0)
    lip_w = production.get("port_cap_seal_lip_width_xy", 0.0)
    lip_h = production.get("port_cap_seal_lip_height_z", 0.0)
    lip_compression = production.get("port_cap_seal_lip_nominal_compression_z", 0.0)
    lip_inner_d = hole_d + cap_clearance
    lip_outer_d = min(lip_inner_d + 2 * lip_w, boss_d)
    if lip_h > 0 and lip_compression >= lip_h:
        raise ValueError("port cap seal lip compression must be smaller than lip height")
    if lip_h > 0 and lip_w > 0 and lip_outer_d <= lip_inner_d:
        raise ValueError("port cap seal lip must fit inside the boss seal land")
    lip_seat_depth = max(lip_h - lip_compression, 0.0)
    return {
        "name": name,
        "role": role,
        "x": x,
        "y": y,
        "boss_diameter": boss_d,
        "hole_diameter": hole_d,
        "boss_height_z": boss_h,
        "cap_plug_diameter": max(hole_d - cap_clearance, 0.2),
        "cap_flange_diameter": boss_d + 2 * cap_overhang,
        "cap_seal_lip_inner_diameter": round(lip_inner_d, 3),
        "cap_seal_lip_outer_diameter": round(lip_outer_d, 3),
        "cap_seal_lip_height_z": round(lip_h, 3),
        "cap_seal_lip_seat_depth_z": round(lip_seat_depth, 3),
        "cap_seal_lip_nominal_compression_z": round(lip_compression, 3),
        "cap_seal_lip_role": "integrated_compliant_lip_on_sample_relief_boss_top",
    }


def _sample_relief_leak_witnesses_for_layout(
    layout: dict[str, Any],
    *,
    ports: list[dict[str, Any]],
    params: dict[str, Any],
    lid_top_z: float,
) -> list[dict[str, Any]]:
    lid = params["lid_manifold"]
    production = params.get("production_assembly", {})
    shelf_w = production.get("sample_relief_witness_shelf_width_y", 0.0)
    shelf_h = production.get("sample_relief_witness_shelf_height_z", 0.0)
    shelf_overlap = production.get("sample_relief_witness_shelf_overlap_xy", 0.0)
    gutter_w = production.get("sample_relief_witness_gutter_width_y", 0.0)
    gutter_d = production.get("sample_relief_witness_gutter_depth_z", 0.0)
    threshold_w = production.get("sample_relief_witness_threshold_width_x", 0.0)
    threshold_h = production.get("sample_relief_witness_threshold_height_z", 0.0)
    if min(shelf_w, shelf_h, gutter_w, gutter_d, threshold_w, threshold_h) <= 0:
        return []

    witnesses: list[dict[str, Any]] = []
    for port in ports:
        if port["role"] != "sample_relief":
            continue
        x = float(port["x"])
        y = float(port["y"])
        boss_r = float(port["boss_diameter"]) / 2
        edge_options = [
            ("x", -1, max(x - boss_r, 0.0), "left", "-X_to_visible_outer_edge"),
            (
                "x",
                1,
                max(float(layout["length_x"]) - (x + boss_r), 0.0),
                "right",
                "+X_to_visible_outer_edge",
            ),
            ("y", -1, max(y - boss_r, 0.0), "front", "-Y_to_visible_outer_edge"),
            (
                "y",
                1,
                max(float(layout["width_y"]) - (y + boss_r), 0.0),
                "rear",
                "+Y_to_visible_outer_edge",
            ),
        ]
        route_axis, route_sign, _distance, visible_edge, flow_direction = min(
            edge_options,
            key=lambda option: option[2],
        )
        axis_max = float(layout["length_x"] if route_axis == "x" else layout["width_y"])
        trans_max = float(layout["width_y"] if route_axis == "x" else layout["length_x"])
        axis_value = x if route_axis == "x" else y
        trans_value = y if route_axis == "x" else x
        shelf_trans_start = max(0.0, min(trans_value - shelf_w / 2, trans_max - shelf_w))
        gutter_trans_start = max(0.0, min(trans_value - gutter_w / 2, trans_max - gutter_w))
        if route_sign > 0:
            flow_start = max(0.0, min(axis_value + boss_r - shelf_overlap, axis_max))
            flow_len = max(axis_max - flow_start, 0.1)
            threshold_start = max(0.0, axis_value - boss_r - threshold_w)
        else:
            flow_start = 0.0
            flow_len = max(axis_value - boss_r + shelf_overlap, 0.1)
            threshold_start = min(axis_max - threshold_w, axis_value + boss_r)

        shelf_z = lid_top_z + lid["duct_height_z"]
        gutter_z = shelf_z + shelf_h - gutter_d
        threshold_z = shelf_z + shelf_h

        def route_rect(
            *,
            name: str,
            axis_start: float,
            trans_start: float,
            axis_length: float,
            trans_width: float,
            z: float,
            height_z: float,
            route_axis: str = route_axis,
        ) -> dict[str, Any]:
            if route_axis == "x":
                return {
                    "name": name,
                    "x": round(axis_start, 3),
                    "y": round(trans_start, 3),
                    "z": round(z, 3),
                    "length_x": round(axis_length, 3),
                    "width_y": round(trans_width, 3),
                    "height_z": round(height_z, 3),
                }
            return {
                "name": name,
                "x": round(trans_start, 3),
                "y": round(axis_start, 3),
                "z": round(z, 3),
                "length_x": round(trans_width, 3),
                "width_y": round(axis_length, 3),
                "height_z": round(height_z, 3),
            }

        shelf = route_rect(
            name=f"{port['name']}_outboard_witness_shelf",
            axis_start=flow_start,
            trans_start=shelf_trans_start,
            axis_length=flow_len,
            trans_width=shelf_w,
            z=shelf_z,
            height_z=shelf_h,
        )
        gutter = route_rect(
            name=f"{port['name']}_outboard_witness_gutter",
            axis_start=flow_start,
            trans_start=gutter_trans_start,
            axis_length=flow_len,
            trans_width=gutter_w,
            z=gutter_z,
            height_z=gutter_d,
        )
        threshold = route_rect(
            name=f"{port['name']}_inboard_witness_dam",
            axis_start=threshold_start,
            trans_start=shelf_trans_start,
            axis_length=threshold_w,
            trans_width=shelf_w,
            z=threshold_z,
            height_z=threshold_h,
        )
        witnesses.append(
            {
                "name": f"{port['name']}_cap_leak_witness",
                "owner_part": "lid_cover",
                "port_name": port["name"],
                "port_role": port["role"],
                "service_role": "production_sample_relief_cap_leak_witness",
                "leak_management": "outboard_visible_witness_gutter_with_inboard_dam",
                "leak_flow_direction": flow_direction,
                "route_axis": route_axis,
                "route_sign": route_sign,
                "visible_edge": visible_edge,
                "port_x": round(x, 3),
                "port_y": round(y, 3),
                "boss_diameter": round(float(port["boss_diameter"]), 3),
                "cap_flange_diameter": round(float(port["cap_flange_diameter"]), 3),
                "shelf_rect": shelf,
                "gutter_rect": gutter,
                "threshold_rect": threshold,
                "top_z": round(threshold_z + threshold_h, 3),
                "validation": "sample_relief_cap_routes_failures_to_visible_edge",
            }
        )
    return witnesses


def _gas_sensor_pcb_mounts_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_top_z: float,
) -> list[dict[str, Any]]:
    mounts = params.get("sensor_mounts", {})
    if not mounts:
        return []

    row = params["row"]
    lid = params["lid_manifold"]
    gas_len = mounts.get("gas_pcb_envelope_length", 30.0)
    gas_width = mounts.get("gas_pcb_envelope_width", 25.0)
    gas_thick = mounts.get("gas_pcb_envelope_thickness", 5.0)
    aperture_d = mounts.get("gas_pcb_aperture_diameter", 2.0)
    channel_w = mounts.get("cable_channel_width_xy", 1.2)
    channel_d = mounts.get("cable_channel_depth_z", 0.5)
    z0 = lid_top_z
    aperture_z = lid_top_z + lid["duct_height_z"] / 2
    side_gas_by_role = {
        interface["role"]: interface
        for interface in layout.get("side_gas_service_interfaces", [])
    }
    specs: list[dict[str, Any]] = []

    if layout["row_axis"] == "y":
        role_specs = [
            ("supply", row["end_margin_x"]),
            ("return", layout["length_x"] - row["end_margin_x"]),
        ]
        for role, duct_center_x in role_specs:
            gas_interface = side_gas_by_role[role]
            center_y = float(gas_interface["duct_y"])
            center_y = min(
                max(center_y, gas_len / 2),
                float(layout["width_y"]) - gas_len / 2,
            )
            x0 = duct_center_x - gas_thick / 2
            y0 = center_y - gas_len / 2
            cable_x = 0.0 if role == "supply" else x0 + gas_thick
            cable_len = x0 if role == "supply" else float(layout["length_x"]) - cable_x
            spec = {
                "name": f"{role}_gas_sensor_pcb",
                "role": role,
                "owner_part": "lid_cover",
                "retention": "screwless_printed_keeper",
                "orientation": "vertical_side_cartridge",
                "socket_enclosure": "full_height_printed_dry_side_cassette",
                "wet_boundary": "dry_side_gas_duct_aperture_only",
                "headspace_intrusion": False,
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": round(z0, 3),
                "length_x": round(gas_thick, 3),
                "width_y": round(gas_len, 3),
                "height_z": round(gas_width, 3),
                "aperture_x": round(duct_center_x, 3),
                "aperture_y": round(center_y, 3),
                "aperture_z": round(aperture_z, 3),
                "aperture_diameter": aperture_d,
                "cable_exit_rect": {
                    "x": round(cable_x, 3),
                    "y": round(center_y - channel_w / 2, 3),
                    "z": round(lid_top_z, 3),
                    "length_x": round(cable_len, 3),
                    "width_y": round(channel_w, 3),
                    "depth_z": round(channel_d, 3),
                },
            }
            spec["gas_interface"] = _gas_pcb_sampling_interface(spec, params=params)
            specs.append(spec)
        return specs

    role_specs = [
        ("supply", row["side_margin_y"]),
        ("return", layout["width_y"] - row["side_margin_y"]),
    ]
    for role, duct_center_y in role_specs:
        gas_interface = side_gas_by_role[role]
        center_x = float(gas_interface["duct_x"])
        center_x = min(
            max(center_x, gas_len / 2),
            float(layout["length_x"]) - gas_len / 2,
        )
        x0 = center_x - gas_len / 2
        y0 = duct_center_y - gas_thick / 2
        cable_y = 0.0 if role == "supply" else y0 + gas_thick
        cable_wid = y0 if role == "supply" else float(layout["width_y"]) - cable_y
        spec = {
            "name": f"{role}_gas_sensor_pcb",
            "role": role,
            "owner_part": "lid_cover",
            "retention": "screwless_printed_keeper",
            "orientation": "vertical_side_cartridge",
            "socket_enclosure": "full_height_printed_dry_side_cassette",
            "wet_boundary": "dry_side_gas_duct_aperture_only",
            "headspace_intrusion": False,
            "x": round(x0, 3),
            "y": round(y0, 3),
            "z": round(z0, 3),
            "length_x": round(gas_len, 3),
            "width_y": round(gas_thick, 3),
            "height_z": round(gas_width, 3),
            "aperture_x": round(center_x, 3),
            "aperture_y": round(duct_center_y, 3),
            "aperture_z": round(aperture_z, 3),
            "aperture_diameter": aperture_d,
            "cable_exit_rect": {
                "x": round(center_x - channel_w / 2, 3),
                "y": round(cable_y, 3),
                "z": round(lid_top_z, 3),
                "length_x": round(channel_w, 3),
                "width_y": round(cable_wid, 3),
                "depth_z": round(channel_d, 3),
            },
        }
        spec["gas_interface"] = _gas_pcb_sampling_interface(spec, params=params)
        specs.append(spec)
    return specs


def _gas_pcb_sampling_interface(
    mount: dict[str, Any],
    *,
    params: dict[str, Any],
) -> dict[str, Any]:
    mounts = params.get("sensor_mounts", {})
    flow_depth = mounts.get("gas_pcb_flow_cell_depth_x", 0.8)
    flow_len = mounts.get("gas_pcb_flow_cell_length_y", 8.0)
    flow_h = mounts.get("gas_pcb_flow_cell_height_z", 5.0)
    margin_y = mounts.get("gas_pcb_seal_land_margin_y", 2.0)
    margin_z = mounts.get("gas_pcb_seal_land_margin_z", 1.5)
    land_t = mounts.get("gas_pcb_seal_land_thickness_x", 0.8)
    gasket_t = mounts.get("gas_pcb_interface_gasket_thickness_x", 0.6)
    compression_x = mounts.get("gas_pcb_interface_gasket_compression_x", 0.2)
    pad_len_y = mounts.get("gas_pcb_compression_pad_length_y", 3.5)
    pad_h = mounts.get("gas_pcb_compression_pad_height_z", 1.0)
    seal_len = flow_len + 2 * margin_y
    seal_h = flow_h + 2 * margin_z
    aperture_y = float(mount["aperture_y"])
    aperture_z = float(mount["aperture_z"])
    length_x = float(mount["length_x"])
    width_y = float(mount["width_y"])

    if length_x <= width_y:
        face_x = float(mount["x"]) + length_x
        gasket_rect = {
            "x": round(face_x, 3),
            "y": round(aperture_y - seal_len / 2, 3),
            "z": round(aperture_z - seal_h / 2, 3),
            "length_x": round(gasket_t, 3),
            "width_y": round(seal_len, 3),
            "height_z": round(seal_h, 3),
        }
        seal_land_rect = {
            "x": round(face_x + gasket_t - compression_x, 3),
            "y": round(aperture_y - seal_len / 2, 3),
            "z": round(aperture_z - seal_h / 2, 3),
            "length_x": round(land_t, 3),
            "width_y": round(seal_len, 3),
            "height_z": round(seal_h, 3),
        }
        flow_cell_rect = {
            "x": round(face_x + gasket_t - compression_x, 3),
            "y": round(aperture_y - flow_len / 2, 3),
            "z": round(aperture_z - flow_h / 2, 3),
            "length_x": round(flow_depth + land_t, 3),
            "width_y": round(flow_len, 3),
            "height_z": round(flow_h, 3),
        }
        compression_pads = [
            {
                "x": seal_land_rect["x"],
                "y": round(aperture_y - seal_len / 2, 3),
                "z": round(aperture_z - seal_h / 2, 3),
                "length_x": round(land_t, 3),
                "width_y": round(pad_len_y, 3),
                "height_z": round(pad_h, 3),
            },
            {
                "x": seal_land_rect["x"],
                "y": round(aperture_y + seal_len / 2 - pad_len_y, 3),
                "z": round(aperture_z + seal_h / 2 - pad_h, 3),
                "length_x": round(land_t, 3),
                "width_y": round(pad_len_y, 3),
                "height_z": round(pad_h, 3),
            },
        ]
        face_axis = "+X"
    else:
        face_y = float(mount["y"]) + width_y
        gasket_rect = {
            "x": round(float(mount["aperture_x"]) - seal_len / 2, 3),
            "y": round(face_y, 3),
            "z": round(aperture_z - seal_h / 2, 3),
            "length_x": round(seal_len, 3),
            "width_y": round(gasket_t, 3),
            "height_z": round(seal_h, 3),
        }
        seal_land_rect = {
            "x": round(float(mount["aperture_x"]) - seal_len / 2, 3),
            "y": round(face_y + gasket_t - compression_x, 3),
            "z": round(aperture_z - seal_h / 2, 3),
            "length_x": round(seal_len, 3),
            "width_y": round(land_t, 3),
            "height_z": round(seal_h, 3),
        }
        flow_cell_rect = {
            "x": round(float(mount["aperture_x"]) - flow_len / 2, 3),
            "y": round(face_y + gasket_t - compression_x, 3),
            "z": round(aperture_z - flow_h / 2, 3),
            "length_x": round(flow_len, 3),
            "width_y": round(flow_depth + land_t, 3),
            "height_z": round(flow_h, 3),
        }
        compression_pads = [
            {
                "x": round(float(mount["aperture_x"]) - seal_len / 2, 3),
                "y": seal_land_rect["y"],
                "z": round(aperture_z - seal_h / 2, 3),
                "length_x": round(pad_len_y, 3),
                "width_y": round(land_t, 3),
                "height_z": round(pad_h, 3),
            },
            {
                "x": round(float(mount["aperture_x"]) + seal_len / 2 - pad_len_y, 3),
                "y": seal_land_rect["y"],
                "z": round(aperture_z + seal_h / 2 - pad_h, 3),
                "length_x": round(pad_len_y, 3),
                "width_y": round(land_t, 3),
                "height_z": round(pad_h, 3),
            },
        ]
        face_axis = "+Y"

    if face_axis == "+X":
        gasket_window_rect = {
            "x": gasket_rect["x"],
            "y": flow_cell_rect["y"],
            "z": flow_cell_rect["z"],
            "length_x": gasket_rect["length_x"],
            "width_y": flow_cell_rect["width_y"],
            "height_z": flow_cell_rect["height_z"],
        }
    else:
        gasket_window_rect = {
            "x": flow_cell_rect["x"],
            "y": gasket_rect["y"],
            "z": flow_cell_rect["z"],
            "length_x": flow_cell_rect["length_x"],
            "width_y": gasket_rect["width_y"],
            "height_z": flow_cell_rect["height_z"],
        }

    return {
        "type": "sealed_dry_side_duct_sampling_cell",
        "face_axis": face_axis,
        "gasket_material_intent": "compressible_elastomer_or_printed_tpu",
        "gasket_rect": gasket_rect,
        "gasket_window_rect": gasket_window_rect,
        "seal_land_rect": seal_land_rect,
        "flow_cell_rect": flow_cell_rect,
        "compression_pad_rects": compression_pads,
        "nominal_gasket_thickness_x": round(gasket_t, 3),
        "nominal_compression_x": round(compression_x, 3),
        "dead_volume_mm3": round(flow_depth * flow_len * flow_h, 3),
        "validation": "aperture_registered_low_dead_volume_no_open_top_sampling",
    }


def _gas_pcb_flow_cell_check_for_layout(
    gas_sensor_pcb_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    interfaces = [mount["gas_interface"] for mount in gas_sensor_pcb_mounts]
    flow_cell_rects = [interface["flow_cell_rect"] for interface in interfaces]
    aperture_diameters = {
        round(float(mount["aperture_diameter"]), 3) for mount in gas_sensor_pcb_mounts
    }
    dead_volumes = {
        round(float(interface["dead_volume_mm3"]), 3) for interface in interfaces
    }
    gasket_thicknesses = {
        round(float(interface["nominal_gasket_thickness_x"]), 3)
        for interface in interfaces
    }
    gasket_compressions = {
        round(float(interface["nominal_compression_x"]), 3)
        for interface in interfaces
    }
    aperture_d = next(iter(aperture_diameters)) if len(aperture_diameters) == 1 else 0.0
    dead_volume = next(iter(dead_volumes)) if len(dead_volumes) == 1 else 0.0

    return {
        "name": "gas_pcb_flow_cell_check",
        "role": "gas_pcb_duct_sampling_cell_validation_body",
        "validation": "required_gate6_aperture_registered_flow_cell_evidence",
        "failure_rule": (
            "missing_flow_cell_or_gasket_registration_evidence_blocks_sensor_thermal_pass"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": f"{aperture_d:.2f} mm aperture / {dead_volume:.2f} mm3 cell",
        "cartridge_count": len(gas_sensor_pcb_mounts),
        "flow_cell_count": len(flow_cell_rects),
        "aperture_count": len(gas_sensor_pcb_mounts),
        "aperture_diameter": aperture_d,
        "dead_volume_mm3": dead_volume,
        "nominal_gasket_thickness_x": (
            next(iter(gasket_thicknesses)) if len(gasket_thicknesses) == 1 else 0.0
        ),
        "nominal_compression_x": (
            next(iter(gasket_compressions)) if len(gasket_compressions) == 1 else 0.0
        ),
        "source_layout_checks": ["gas_sensor_pcb_mounts"],
        "requires_physical_evidence": True,
        "flow_cell_rects": flow_cell_rects,
    }


def _headspace_sht41_mounts_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_bottom_z: float,
) -> list[dict[str, Any]]:
    mounts = params.get("sensor_mounts", {})
    if not mounts:
        return []

    plate = params["plate"]
    carrier_len = mounts.get("sht41_carrier_length_x", 12.0)
    carrier_wid = mounts.get("sht41_carrier_width_y", 12.0)
    carrier_h = mounts.get("sht41_carrier_height_z", 4.0)
    inset_x = mounts.get("sht41_service_lane_inset_x", 9.0)
    z0 = lid_bottom_z + mounts.get("sht41_lid_recess_z", 0.4)
    aperture_d = mounts.get("sht41_headspace_aperture_diameter", 3.0)
    wall = mounts.get("sht41_socket_wall_thickness", 1.0)
    clearance_xy = mounts.get("sht41_carrier_clearance_xy", 0.25)
    clearance_z = mounts.get("sht41_carrier_clearance_z", 0.2)
    pocket_roof_h = mounts.get("sht41_pocket_roof_thickness_z", 0.8)
    key_len = mounts.get("sht41_registration_key_length_x", 2.0)
    key_w = mounts.get("sht41_registration_key_width_y", 0.8)
    key_h = mounts.get("sht41_registration_key_height_z", 0.5)
    relief_len = mounts.get("sht41_service_finger_relief_length_x", 5.0)
    relief_w = mounts.get("sht41_service_finger_relief_width_y", 4.0)
    drip_outer_d = mounts.get("sht41_drip_break_outer_diameter", aperture_d + 2.0)
    drip_h = mounts.get("sht41_drip_break_height_z", 0.35)
    channel_w = mounts.get("cable_channel_width_xy", 1.2)
    channel_d = mounts.get("cable_channel_depth_z", 0.5)
    x0 = float(layout["length_x"]) - inset_x - carrier_len / 2

    specs: list[dict[str, Any]] = []
    for tile in layout["tile_origins"]:
        center_y = tile["y"] + plate["width_y"] / 2
        y0 = center_y - carrier_wid / 2
        pocket_x = x0 - clearance_xy
        pocket_y = y0 - clearance_xy
        pocket_z = z0 - clearance_z / 2
        pocket_len = float(layout["length_x"]) - pocket_x + 0.2
        pocket_w = carrier_wid + 2 * clearance_xy
        pocket_h = carrier_h + clearance_z
        outer_x = x0 - wall - clearance_xy
        outer_y = y0 - wall - clearance_xy
        outer_w = carrier_wid + 2 * (wall + clearance_xy)
        outer_h = (z0 - lid_bottom_z) + pocket_h + pocket_roof_h
        service_edge_x = float(layout["length_x"])
        key = {
            "x": round(x0 + min(1.2, carrier_len / 4), 3),
            "y": round(y0 + carrier_wid - key_w, 3),
            "z": round(z0, 3),
            "length_x": round(key_len, 3),
            "width_y": round(key_w, 3),
            "height_z": round(key_h, 3),
        }
        specs.append(
            {
                "name": f"headspace_sht41_tile_{tile['index']}",
                "role": "plate_headspace_rh_t",
                "tile_index": tile["index"],
                "owner_part": "lid_manifold_shell",
                "retention": "screwless_printed_microcarrier_keeper",
                "orientation": "side_loaded_service_cassette",
                "service_direction": "-X_install_+X_remove",
                "socket_enclosure": "protected_side_loaded_lid_shell_tunnel",
                "wet_boundary": "controlled_membrane_aperture_only",
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": round(z0, 3),
                "length_x": round(carrier_len, 3),
                "width_y": round(carrier_wid, 3),
                "height_z": round(carrier_h, 3),
                "aperture_x": round(x0 + carrier_len / 2, 3),
                "aperture_y": round(center_y, 3),
                "aperture_z": round(z0, 3),
                "aperture_diameter": aperture_d,
                "condensate_protection": "drip_break_ring_and_service_side_harness_isolation",
                "protected_cassette_outer_rect": {
                    "x": round(outer_x, 3),
                    "y": round(outer_y, 3),
                    "z": round(lid_bottom_z, 3),
                    "length_x": round(service_edge_x - outer_x, 3),
                    "width_y": round(outer_w, 3),
                    "height_z": round(outer_h, 3),
                },
                "protected_pocket_cut_rect": {
                    "x": round(pocket_x, 3),
                    "y": round(pocket_y, 3),
                    "z": round(pocket_z, 3),
                    "length_x": round(pocket_len, 3),
                    "width_y": round(pocket_w, 3),
                    "height_z": round(pocket_h, 3),
                },
                "socket_floor_thickness_z": round(z0 - lid_bottom_z - clearance_z / 2, 3),
                "anti_lift_keeper_rect": {
                    "x": round(pocket_x, 3),
                    "y": round(pocket_y, 3),
                    "z": round(pocket_z + pocket_h, 3),
                    "length_x": round(pocket_len, 3),
                    "width_y": round(pocket_w, 3),
                    "height_z": round(pocket_roof_h, 3),
                },
                "back_stop_rect": {
                    "x": round(outer_x, 3),
                    "y": round(pocket_y, 3),
                    "z": round(pocket_z, 3),
                    "length_x": round(wall, 3),
                    "width_y": round(pocket_w, 3),
                    "height_z": round(pocket_h, 3),
                },
                "side_stop_rects": [
                    {
                        "x": round(pocket_x, 3),
                        "y": round(outer_y, 3),
                        "z": round(pocket_z, 3),
                        "length_x": round(pocket_len, 3),
                        "width_y": round(wall, 3),
                        "height_z": round(pocket_h, 3),
                    },
                    {
                        "x": round(pocket_x, 3),
                        "y": round(pocket_y + pocket_w, 3),
                        "z": round(pocket_z, 3),
                        "length_x": round(pocket_len, 3),
                        "width_y": round(wall, 3),
                        "height_z": round(pocket_h, 3),
                    },
                ],
                "registration_key_rect": key,
                "registration_notch_rect": key,
                "service_finger_relief_rect": {
                    "x": round(max(service_edge_x - relief_len, pocket_x), 3),
                    "y": round(center_y - relief_w / 2, 3),
                    "z": round(pocket_z, 3),
                    "length_x": round(min(relief_len, service_edge_x - pocket_x), 3),
                    "width_y": round(relief_w, 3),
                    "height_z": round(pocket_h, 3),
                },
                "drip_break_ring": {
                    "x": round(x0 + carrier_len / 2, 3),
                    "y": round(center_y, 3),
                    "z": round(lid_bottom_z - drip_h, 3),
                    "inner_diameter": round(aperture_d, 3),
                    "outer_diameter": round(drip_outer_d, 3),
                    "height_z": round(drip_h, 3),
                },
                "cable_exit_rect": {
                    "x": round(x0 + carrier_len, 3),
                    "y": round(center_y - channel_w / 2, 3),
                    "z": round(z0, 3),
                    "length_x": round(float(layout["length_x"]) - (x0 + carrier_len), 3),
                    "width_y": round(channel_w, 3),
                    "depth_z": round(channel_d, 3),
                },
            }
        )
    return specs


def _ir_sensor_mounts_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    base_top_z: float,
) -> list[dict[str, Any]]:
    mounts = params.get("sensor_mounts", {})
    if not mounts:
        return []

    plate = params["plate"]
    body_d = mounts.get("ir_body_diameter", 8.0)
    body_h = mounts.get("ir_body_height_z", 4.5)
    lens_h = mounts.get("ir_lens_height_z", 0.35)
    aperture_d = mounts.get("ir_aperture_diameter", 6.0)
    center_inset_x = mounts.get("ir_center_inset_x", 4.4)
    face_gasket_od = mounts.get("ir_face_gasket_outer_diameter", body_d)
    face_gasket_id = mounts.get("ir_face_gasket_inner_diameter", aperture_d + 0.4)
    face_gasket_h = mounts.get("ir_face_gasket_thickness_z", 0.45)
    face_gasket_compression_z = mounts.get("ir_face_gasket_nominal_compression_z", 0.12)
    drip_collar_od = mounts.get("ir_aperture_drip_collar_outer_diameter", aperture_d + 3.0)
    drip_collar_h = mounts.get("ir_aperture_drip_collar_height_z", 0.55)
    harness = params.get("sensor_harness", {})
    fov_angle_deg = harness.get("ir_fov_angle_degrees", 12.0)
    plate_bottom_z = base_top_z + params["plate_support"]["land_height_z"]
    sensor_to_plate_z = max(plate_bottom_z - (body_h + lens_h), 0.0)
    fov_spot_d = 2 * sensor_to_plate_z * math.tan(math.radians(fov_angle_deg) / 2)
    channel_w = mounts.get("cable_channel_width_xy", 1.2)
    channel_d = mounts.get("cable_channel_depth_z", 0.5)

    specs: list[dict[str, Any]] = []
    for tile in layout["tile_origins"]:
        center_x = tile["x"] + center_inset_x
        center_y = tile["y"] + plate["width_y"] / 2
        well_grid = _well_grid_rectangle_for_tile(tile, params)
        specs.append(
            {
                "name": f"ir_thermopile_tile_{tile['index']}",
                "role": "plate_margin_sample_plane_temperature",
                "tile_index": tile["index"],
                "owner_part": "plate_support_frame",
                "retention": "screwless_printed_lip",
                "wet_boundary": "drip_collared_aperture_with_dry_side_face_gasket",
                "condensate_protection": "top_drip_collar_and_compressed_face_gasket",
                "x": round(center_x - body_d / 2, 3),
                "y": round(center_y - body_d / 2, 3),
                "z": 0.0,
                "length_x": round(body_d, 3),
                "width_y": round(body_d, 3),
                "height_z": round(body_h, 3),
                "center_x": round(center_x, 3),
                "center_y": round(center_y, 3),
                "aperture_x": round(center_x, 3),
                "aperture_y": round(center_y, 3),
                "aperture_z": round(base_top_z, 3),
                "aperture_diameter": aperture_d,
                "fov_angle_degrees": round(fov_angle_deg, 3),
                "sensor_to_plate_z": round(sensor_to_plate_z, 3),
                "fov_spot_diameter": round(fov_spot_d, 3),
                "well_grid_rect": well_grid,
                "face_gasket": {
                    "x": round(center_x, 3),
                    "y": round(center_y, 3),
                    "z": round(max(body_h - face_gasket_h, 0.0), 3),
                    "outer_diameter": round(face_gasket_od, 3),
                    "inner_diameter": round(face_gasket_id, 3),
                    "height_z": round(face_gasket_h, 3),
                    "nominal_compression_z": round(face_gasket_compression_z, 3),
                    "retention": "captured_between_to39_face_and_printed_pocket_lip",
                    "wet_boundary": "dry_side_aperture_face_seal",
                },
                "drip_collar": {
                    "x": round(center_x, 3),
                    "y": round(center_y, 3),
                    "z": round(base_top_z, 3),
                    "inner_diameter": round(aperture_d, 3),
                    "outer_diameter": round(drip_collar_od, 3),
                    "height_z": round(drip_collar_h, 3),
                    "owner_part": "plate_support_frame",
                    "leak_management": "raised_collar_keeps_wetting_out_of_ir_aperture",
                },
                "cable_exit_rect": {
                    "x": 0.0,
                    "y": round(center_y - channel_w / 2, 3),
                    "z": 0.0,
                    "length_x": round(max(center_x - body_d / 2, 0.0), 3),
                    "width_y": round(channel_w, 3),
                    "depth_z": round(channel_d, 3),
                },
            }
        )
    return specs


def _sensor_harness_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_bottom_z: float,
    lid_top_z: float,
    base_top_z: float,
    plate_bottom_z: float,
    ir_sensor_mounts: list[dict[str, Any]],
    headspace_sht41_mounts: list[dict[str, Any]],
    gas_sensor_pcb_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    harness = params.get("sensor_harness", {})
    if not harness:
        return {
            "lower_ir_harness_routes": [],
            "lower_ir_harness_trunk": {},
            "lower_ir_connector_envelope": {},
            "lid_sensor_harness_routes": [],
            "lid_sensor_harness_trunks": [],
            "lid_service_connector_envelopes": [],
            "sensor_service_connector_envelopes": [],
            "sensor_service_cable_envelopes": [],
            "sensor_service_cable_pigtails": [],
            "sensor_harness_summary": {
                "lower_ir_route_count": 0,
                "lid_sensor_route_count": 0,
                "service_connector_count": 0,
                "external_service_cable_envelope_count": 0,
                "installed_service_cable_pigtail_count": 0,
                "retention": "not_modeled",
            },
        }

    lower = _lower_ir_harness_for_layout(
        layout,
        params=params,
        base_top_z=base_top_z,
        plate_bottom_z=plate_bottom_z,
        ir_sensor_mounts=ir_sensor_mounts,
    )
    lid = _lid_sensor_harness_for_layout(
        layout,
        params=params,
        lid_bottom_z=lid_bottom_z,
        lid_top_z=lid_top_z,
        headspace_sht41_mounts=headspace_sht41_mounts,
        gas_sensor_pcb_mounts=gas_sensor_pcb_mounts,
    )
    connectors = [lower["lower_ir_connector_envelope"], *lid["lid_service_connector_envelopes"]]
    cable_envelopes = [
        connector["external_cable_envelope_rect"]
        for connector in connectors
    ]
    cable_pigtails = [
        connector["installed_cable_pigtail_rect"]
        for connector in connectors
    ]
    return {
        **lower,
        **lid,
        "sensor_service_connector_envelopes": connectors,
        "sensor_service_cable_envelopes": cable_envelopes,
        "sensor_service_cable_pigtails": cable_pigtails,
        "sensor_harness_summary": {
            "lower_ir_route_count": len(lower["lower_ir_harness_routes"]),
            "lid_sensor_route_count": len(lid["lid_sensor_harness_routes"]),
            "service_connector_count": len(connectors),
            "external_service_cable_envelope_count": len(cable_envelopes),
            "installed_service_cable_pigtail_count": len(cable_pigtails),
            "service_connector_family": params["sensor_harness"].get(
                "service_connector_family",
                "unspecified",
            ),
            "retention": "printed_snap_covers_and_strain_relief",
            "lower_domain": "dry_plate_support_side",
            "lid_domain": "removable_lid_sensor_side",
        },
    }


def _sensor_connector_service_clearance_check(
    connectors: list[dict[str, Any]],
) -> dict[str, Any]:
    body_rects = [connector["service_clearance_rect"] for connector in connectors]
    x_len, y_len, z_len = _rectangles_bounding_extents(body_rects)
    connector_names = tuple(str(connector["name"]) for connector in connectors)
    return {
        "name": "sensor_connector_service_clearance_check",
        "role": "sensor_connector_mating_and_service_clearance_validation_body",
        "validation": "required_gate6_connector_service_clearance_evidence",
        "failure_rule": (
            "blocked_connector_clearance_or_unmeasured_mating_space_blocks_sensor_thermal_pass"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": f"{x_len:.2f} x {y_len:.2f} x {z_len:.2f} mm",
        "connector_count": len(connectors),
        "connector_names": connector_names,
        "source_layout_checks": ["sensor_service_connector_envelopes"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "mated_sensor_service_connectors",
            "serviceable_sensor_electrical_disconnects",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": body_rects,
    }


def _sensor_service_cable_envelope_check(
    cable_envelopes: list[dict[str, Any]],
) -> dict[str, Any]:
    first_envelope = cable_envelopes[0] if cable_envelopes else {}
    min_bend_radius_y = max(
        (float(envelope.get("min_bend_radius_y", 0.0)) for envelope in cable_envelopes),
        default=0.0,
    )
    straight_service_length_y = max(
        (
            float(envelope.get("straight_service_length_y", 0.0))
            for envelope in cable_envelopes
        ),
        default=0.0,
    )
    return {
        "name": "sensor_service_cable_envelope_check",
        "role": "sensor_service_cable_bend_and_egress_validation_body",
        "validation": "required_gate6_service_cable_bend_envelope_evidence",
        "failure_rule": (
            "kinked_snagging_or_unmeasured_sensor_cable_dress_blocks_sensor_thermal_pass"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{float(first_envelope.get('length_x', 0.0)):.2f} x "
            f"{float(first_envelope.get('width_y', 0.0)):.2f} x "
            f"{float(first_envelope.get('height_z', 0.0)):.2f} mm"
        ),
        "bend_cad_value": (
            f"{min_bend_radius_y:.2f} mm bend radius / "
            f"{straight_service_length_y:.2f} mm straight"
        ),
        "cable_envelope_count": len(cable_envelopes),
        "min_bend_radius_y": round(min_bend_radius_y, 3),
        "straight_service_length_y": round(straight_service_length_y, 3),
        "source_layout_checks": ["sensor_service_connector_envelopes"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "connected_sensor_service_cable_dress",
            "pipette_clearance_with_electrical_services",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": cable_envelopes,
    }


def _electrical_connector_mating_state_check(
    review_rects: list[dict[str, Any]],
    *,
    connectors: list[dict[str, Any]],
    cable_envelopes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "name": "electrical_connector_mating_state_check",
        "role": "mated_and_unmated_sensor_connector_state_validation_body",
        "validation": "required_gate6_connector_mating_state_evidence",
        "failure_rule": (
            "unmated_loose_or_unproven_connector_state_blocks_sensor_thermal_pass"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{len(connectors)} connectors / {len(cable_envelopes)} cable envelopes"
        ),
        "review_cad_value": (
            f"{len(connectors)} connectors / {len(review_rects)} "
            "mating-state review bodies"
        ),
        "connector_count": len(connectors),
        "cable_envelope_count": len(cable_envelopes),
        "review_body_count": len(review_rects),
        "source_layout_checks": [
            "sensor_connector_service_clearance_check",
            "sensor_service_cable_envelope_check",
            "unmated_sensor_service_connector_review_rects",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "mated_sensor_service_connectors",
            "continuous_sensor_electrical_service",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": review_rects,
    }


def _sensor_prototype_test_gates() -> list[dict[str, str]]:
    return [
        {
            "name": "incoming_module_electrical",
            "evidence": "bench I2C scan, current draw, sensor identity, and baseline reading",
        },
        {
            "name": "pocket_fit_and_retention",
            "evidence": "insertion/removal force, no rattle, no crushed package, release access",
        },
        {
            "name": "aperture_registration",
            "evidence": "gas, headspace, or IR aperture is visibly centered and unobstructed",
        },
        {
            "name": "installed_dry_electrical",
            "evidence": "assembled dry coupon bus scan plus connector wiggle/dropout check",
        },
        {
            "name": "environmental_step_response",
            "evidence": "humidity, temperature, CO2, and airflow step response without biology",
        },
        {
            "name": "wet_nonbiological_exposure",
            "evidence": "loaded plate/media proxy condensation, splash, drift, and leak check",
        },
        {
            "name": "bsl1_biology_commissioning",
            "evidence": "low-risk biology run correlating sensor traces with growth state",
        },
    ]


def _sensor_installation_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    gas_sensor_pcb_mounts: list[dict[str, Any]],
    headspace_sht41_mounts: list[dict[str, Any]],
    ir_sensor_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    install = params.get("sensor_installation", {})
    gas_lift_z = install.get("gas_pcb_service_lift_z", 18.0)
    sht41_offset_x = install.get("sht41_service_offset_x", 18.0)
    ir_drop_z = install.get("ir_service_drop_z", 14.0)
    steps: list[dict[str, Any]] = []

    for mount in gas_sensor_pcb_mounts:
        steps.append(
            {
                "name": f"{mount['name']}_install",
                "sensor_name": mount["name"],
                "module_kind": "gas_sensor_pcb_cartridge",
                "role": mount["role"],
                "owner_part": mount["owner_part"],
                "install_direction": "-Z into dry-side lid cassette",
                "service_direction": "+Z pull after releasing printed keeper door",
                "retention": "printed_keeper_door_no_screws_no_glue",
                "aperture_registration": "gas duct wall aperture to PCB sensor aperture",
                "service_vector": {"dx": 0.0, "dy": 0.0, "dz": round(gas_lift_z, 3)},
                "installed_rect": _installed_sensor_rect(mount),
            }
        )

    for mount in headspace_sht41_mounts:
        steps.append(
            {
                "name": f"{mount['name']}_install",
                "sensor_name": mount["name"],
                "module_kind": "headspace_sht41_microcarrier",
                "role": mount["role"],
                "owner_part": mount["owner_part"],
                "install_direction": "-X from lid service edge into protected pocket",
                "service_direction": "+X pull from lid service edge",
                "retention": "printed_microcarrier_keeper_no_screws_no_glue",
                "aperture_registration": "SHT41 membrane to local headspace aperture",
                "service_vector": {"dx": round(sht41_offset_x, 3), "dy": 0.0, "dz": 0.0},
                "installed_rect": _installed_sensor_rect(mount),
            }
        )

    for mount in ir_sensor_mounts:
        steps.append(
            {
                "name": f"{mount['name']}_install",
                "sensor_name": mount["name"],
                "module_kind": "lower_ir_thermopile",
                "role": mount["role"],
                "owner_part": mount["owner_part"],
                "install_direction": "+Z from underside into lower dry support pocket",
                "service_direction": "-Z pull from dry bay underside",
                "retention": "printed_lip_no_screws_no_glue",
                "aperture_registration": "IR lens to plate-margin aperture and FOV",
                "service_vector": {"dx": 0.0, "dy": 0.0, "dz": round(-ir_drop_z, 3)},
                "installed_rect": _installed_sensor_rect(mount),
            }
        )

    gates = _sensor_prototype_test_gates()
    path_width = install.get("install_path_width_xy", 1.4)
    path_height = install.get("install_path_height_z", path_width)
    path_rects = _sensor_installation_path_rectangles(
        steps,
        path_width=path_width,
        path_height=path_height,
    )
    module_kind_counts: dict[str, int] = {}
    for step in steps:
        kind = str(step["module_kind"])
        module_kind_counts[kind] = module_kind_counts.get(kind, 0) + 1

    return {
        "sensor_installation_steps": steps,
        "sensor_prototype_test_gates": gates,
        "sensor_installation_path_check": {
            "name": "sensor_installation_path_check",
            "role": "real_sensor_install_and_removal_motion_envelope_validation_body",
            "validation": "required_gate6_real_sensor_install_serviceability_evidence",
            "failure_rule": (
                "unproven_install_path_retention_or_aperture_registration_blocks_sensor_thermal_pass"
            ),
            "evidence_gate": "Gate 6 sensor/thermal",
            "cad_value": f"{len(steps)} steps / {len(gates)} gates",
            "install_step_count": len(steps),
            "test_gate_count": len(gates),
            "module_kind_counts": module_kind_counts,
            "path_width_xy": round(float(path_width), 3),
            "path_height_z": round(float(path_height), 3),
            "source_layout_checks": [
                "gas_pcb_flow_cell_check",
                "sensor_connector_service_clearance_check",
                "sensor_service_cable_envelope_check",
            ],
            "requires_physical_evidence": True,
            "requires_real_sensor_inventory": True,
            "physical_claims_blocked": [
                "gas_pcb_cartridges_sealed_to_sampling_cells",
                "local_headspace_sht41_sensors_installed",
                "local_ir_thermopiles_installed",
                "powered_sensor_thermal_readiness",
            ],
            "body_rects": path_rects,
        },
        "sensor_installation_summary": {
            "install_step_count": len(steps),
            "test_gate_count": len(gates),
            "retention_policy": "printed_reversible_no_screws_no_glue",
            "service_modes": "bench_test_then_sensor_install_then_dry_then_wet_then_bsl1",
        },
    }


def _sensor_installation_path_rectangles(
    steps: list[dict[str, Any]],
    *,
    path_width: float,
    path_height: float,
) -> list[dict[str, Any]]:
    rects: list[dict[str, Any]] = []
    for step in steps:
        installed = step["installed_rect"]
        vector = step["service_vector"]
        cx = float(installed["x"]) + float(installed["length_x"]) / 2
        cy = float(installed["y"]) + float(installed["width_y"]) / 2
        cz = float(installed["z"]) + float(installed["height_z"]) / 2
        dx = float(vector["dx"])
        dz = float(vector["dz"])
        if abs(dx) >= abs(dz):
            rects.append(
                {
                    "name": f"{step['name']}_path",
                    "sensor_name": step["sensor_name"],
                    "module_kind": step["module_kind"],
                    "x": round(min(cx, cx + dx) - path_width / 2, 3),
                    "y": round(cy - path_width / 2, 3),
                    "z": round(cz - path_height / 2, 3),
                    "length_x": round(abs(dx) + path_width, 3),
                    "width_y": round(path_width, 3),
                    "height_z": round(path_height, 3),
                }
            )
        else:
            rects.append(
                {
                    "name": f"{step['name']}_path",
                    "sensor_name": step["sensor_name"],
                    "module_kind": step["module_kind"],
                    "x": round(cx - path_width / 2, 3),
                    "y": round(cy - path_width / 2, 3),
                    "z": round(min(cz, cz + dz) - path_height / 2, 3),
                    "length_x": round(path_width, 3),
                    "width_y": round(path_width, 3),
                    "height_z": round(abs(dz) + path_height, 3),
                }
            )
    return rects


def _installed_sensor_rect(mount: dict[str, Any]) -> dict[str, float]:
    return {
        "x": round(float(mount["x"]), 3),
        "y": round(float(mount["y"]), 3),
        "z": round(float(mount["z"]), 3),
        "length_x": round(float(mount["length_x"]), 3),
        "width_y": round(float(mount["width_y"]), 3),
        "height_z": round(float(mount["height_z"]), 3),
    }


def _service_connector_dimensions(params: dict[str, Any]) -> dict[str, float | int | str]:
    harness = params["sensor_harness"]
    board_h = harness["service_connector_board_thickness_z"]
    header_h = harness["service_connector_header_height_z"]
    plug_h = harness["service_connector_plug_height_z"]
    latch_h = harness["service_connector_latch_height_z"]
    return {
        "family": harness["service_connector_family"],
        "source_url": harness["service_connector_source_url"],
        "circuits": int(harness["service_connector_circuits"]),
        "pitch": harness["service_connector_pitch"],
        "board_length_x": harness["service_connector_board_length_x"],
        "board_width_y": harness["service_connector_board_width_y"],
        "board_thickness_z": board_h,
        "header_length_x": harness["service_connector_header_length_x"],
        "header_width_y": harness["service_connector_header_width_y"],
        "header_height_z": header_h,
        "plug_length_y": harness["service_connector_plug_length_y"],
        "plug_height_z": plug_h,
        "latch_length_y": harness["service_connector_latch_length_y"],
        "latch_width_x": harness["service_connector_latch_width_x"],
        "latch_height_z": latch_h,
        "shroud_wall_xy": harness["service_connector_shroud_wall_xy"],
        "shroud_height_z": harness["service_connector_shroud_height_z"],
        "pin1_marker_diameter": harness["service_connector_pin1_marker_diameter"],
        "key_rib_width_x": harness["service_connector_key_rib_width_x"],
        "key_rib_length_y": harness["service_connector_key_rib_length_y"],
        "service_clearance_y": harness["service_connector_service_clearance_y"],
        "height_z": board_h + max(header_h, plug_h + latch_h),
    }


def _sensor_service_connector_spec(
    *,
    name: str,
    domain: str,
    owner_part: str,
    disconnect: str,
    x: float,
    y: float,
    z: float,
    params: dict[str, Any],
) -> dict[str, Any]:
    dims = _service_connector_dimensions(params)
    board_l = float(dims["board_length_x"])
    board_w = float(dims["board_width_y"])
    board_h = float(dims["board_thickness_z"])
    header_l = float(dims["header_length_x"])
    header_w = float(dims["header_width_y"])
    header_h = float(dims["header_height_z"])
    plug_l = float(dims["plug_length_y"])
    plug_h = float(dims["plug_height_z"])
    latch_l = float(dims["latch_length_y"])
    latch_w = float(dims["latch_width_x"])
    latch_h = float(dims["latch_height_z"])
    shroud_wall = float(dims["shroud_wall_xy"])
    shroud_h = float(dims["shroud_height_z"])
    harness = params["sensor_harness"]
    cable_w = harness.get("service_cable_envelope_width_x", board_l)
    cable_h = harness.get("service_cable_envelope_height_z", dims["height_z"])
    cable_bend = harness.get("service_cable_bend_radius_y", 0.0)
    cable_straight = harness.get("service_cable_straight_length_y", 0.0)
    cable_len = cable_bend + cable_straight
    pigtail_w = harness.get("service_cable_pigtail_width_x", min(cable_w, header_l))
    pigtail_h = harness.get("service_cable_pigtail_height_z", 1.2)
    pigtail_len = harness.get("service_cable_pigtail_length_y", cable_len)
    if cable_len > 0:
        pigtail_len = min(pigtail_len, cable_len)
    header_x = x + (board_l - header_l) / 2
    header_y = y + max((board_w - header_w - plug_l) / 2, 0.0)
    plug_y = header_y + header_w
    plug_w = min(plug_l, max(y + board_w - plug_y, plug_l))
    return {
        "name": name,
        "domain": domain,
        "owner_part": owner_part,
        "connector_family": dims["family"],
        "source_url": dims["source_url"],
        "circuits": dims["circuits"],
        "pitch": dims["pitch"],
        "x": round(x, 3),
        "y": round(y, 3),
        "z": round(z, 3),
        "length_x": round(board_l, 3),
        "width_y": round(board_w, 3),
        "height_z": round(float(dims["height_z"]), 3),
        "keyed": True,
        "disconnect": disconnect,
        "mating_direction": "+Y",
        "board_rect": {
            "x": round(x, 3),
            "y": round(y, 3),
            "z": round(z, 3),
            "length_x": round(board_l, 3),
            "width_y": round(board_w, 3),
            "height_z": round(board_h, 3),
        },
        "header_rect": {
            "x": round(header_x, 3),
            "y": round(header_y, 3),
            "z": round(z + board_h, 3),
            "length_x": round(header_l, 3),
            "width_y": round(header_w, 3),
            "height_z": round(header_h, 3),
        },
        "plug_rect": {
            "x": round(header_x, 3),
            "y": round(plug_y, 3),
            "z": round(z + board_h, 3),
            "length_x": round(header_l, 3),
            "width_y": round(plug_w, 3),
            "height_z": round(plug_h, 3),
        },
        "latch_rect": {
            "x": round(x + (board_l - latch_w) / 2, 3),
            "y": round(plug_y + max(plug_w - latch_l, 0.0), 3),
            "z": round(z + board_h + plug_h, 3),
            "length_x": round(latch_w, 3),
            "width_y": round(latch_l, 3),
            "height_z": round(latch_h, 3),
        },
        "pin1_marker": {
            "x": round(x + 1.0, 3),
            "y": round(y + 1.0, 3),
            "z": round(z + board_h, 3),
            "diameter": dims["pin1_marker_diameter"],
            "height_z": 0.25,
        },
        "key_rib_rect": {
            "x": round(header_x, 3),
            "y": round(y - shroud_wall, 3),
            "z": round(z, 3),
            "length_x": round(float(dims["key_rib_width_x"]), 3),
            "width_y": round(float(dims["key_rib_length_y"]), 3),
            "height_z": round(shroud_h, 3),
        },
        "printed_shroud": {
            "x": round(x - shroud_wall, 3),
            "y": round(y - shroud_wall, 3),
            "z": round(z, 3),
            "length_x": round(board_l + 2 * shroud_wall, 3),
            "width_y": round(board_w + shroud_wall, 3),
            "height_z": round(shroud_h, 3),
            "wall_xy": round(shroud_wall, 3),
            "open_side": "+Y",
        },
        "service_clearance_rect": {
            "x": round(x, 3),
            "y": round(y + board_w, 3),
            "z": round(z, 3),
            "length_x": round(board_l, 3),
            "width_y": round(float(dims["service_clearance_y"]), 3),
            "height_z": round(float(dims["height_z"]), 3),
        },
        "external_cable_envelope_rect": {
            "name": f"{name}_external_cable_bend_envelope",
            "domain": domain,
            "connector_name": name,
            "disconnect": disconnect,
            "route_axis": "+Y",
            "x": round(x + (board_l - cable_w) / 2, 3),
            "y": round(y + board_w, 3),
            "z": round(z, 3),
            "length_x": round(cable_w, 3),
            "width_y": round(cable_len, 3),
            "height_z": round(max(float(cable_h), float(dims["height_z"])), 3),
            "min_bend_radius_y": round(cable_bend, 3),
            "straight_service_length_y": round(cable_straight, 3),
            "service_role": "external_electrical_service_cable_envelope",
            "validation": "row_end_cable_egress_not_printed_part",
        },
        "installed_cable_pigtail_rect": {
            "name": f"{name}_cots_cable_pigtail",
            "domain": domain,
            "connector_name": name,
            "disconnect": disconnect,
            "route_axis": "+Y",
            "x": round(x + (board_l - pigtail_w) / 2, 3),
            "y": round(y + board_w, 3),
            "z": round(z + board_h, 3),
            "length_x": round(pigtail_w, 3),
            "width_y": round(pigtail_len, 3),
            "height_z": round(pigtail_h, 3),
            "service_role": "installed_electrical_service_cable_pigtail",
            "material_intent": "COTS flexible cable assembly",
            "validation": "installed_cable_body_bend_envelope_checked_separately",
        },
    }


def _lower_ir_harness_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    base_top_z: float,
    plate_bottom_z: float,
    ir_sensor_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    harness = params["sensor_harness"]
    wire_w = harness["wire_bundle_width_xy"]
    wire_h = harness["wire_bundle_height_z"]
    min_bend = harness["min_bend_radius"]
    trunk_x = harness["lower_trunk_x"]
    trunk_w = harness["lower_trunk_width_x"]
    conn_dims = _service_connector_dimensions(params)
    conn_wid = float(conn_dims["board_width_y"])
    conn_h = float(conn_dims["height_z"])
    edge_gap_y = harness.get("lid_connector_edge_gap_y", 2.0)
    conn_y = float(layout["width_y"]) - conn_wid - edge_gap_y
    centers_y = [float(mount["center_y"]) for mount in ir_sensor_mounts]
    trunk_y = max(params["row"]["side_margin_y"], min(centers_y) - min_bend)
    trunk_y2 = conn_y + conn_wid
    trunk = {
        "name": "lower_ir_dry_trunk",
        "domain": "lower_dry_harness",
        "owner_part": "plate_support_frame",
        "retention": "printed_snap_cover",
        "x": round(trunk_x, 3),
        "y": round(trunk_y, 3),
        "z": 0.0,
        "length_x": round(trunk_w, 3),
        "width_y": round(trunk_y2 - trunk_y, 3),
        "height_z": round(wire_h, 3),
        "channel_depth_z": harness["channel_depth_z"],
        "cover_height_z": harness["cover_height_z"],
        "min_bend_radius": min_bend,
        "base_top_z": round(base_top_z, 3),
        "plate_bottom_z": round(plate_bottom_z, 3),
    }
    routes: list[dict[str, Any]] = []
    branch_x = trunk_x + trunk_w
    for mount in ir_sensor_mounts:
        sensor_left_x = float(mount["x"])
        branch_len = max(sensor_left_x - branch_x, 0.0)
        center_y = float(mount["center_y"])
        relief_len = min(harness["strain_relief_length_x"], branch_len)
        routes.append(
            {
                "name": f"{mount['name']}_lower_dry_branch",
                "domain": "lower_dry_harness",
                "sensor_name": mount["name"],
                "tile_index": mount["tile_index"],
                "owner_part": "plate_support_frame",
                "retention": "printed_snap_cover_and_strain_relief",
                "branch_rect": {
                    "x": round(branch_x, 3),
                    "y": round(center_y - wire_w / 2, 3),
                    "z": 0.0,
                    "length_x": round(branch_len, 3),
                    "width_y": round(wire_w, 3),
                    "height_z": round(wire_h, 3),
                },
                "strain_relief_rect": {
                    "x": round(sensor_left_x - relief_len, 3),
                    "y": round(center_y - harness["strain_relief_width_y"] / 2, 3),
                    "z": 0.0,
                    "length_x": round(relief_len, 3),
                    "width_y": round(harness["strain_relief_width_y"], 3),
                    "height_z": round(wire_h, 3),
                    "depth_z": round(harness["strain_relief_depth_z"], 3),
                },
                "trunk_name": trunk["name"],
                "min_bend_radius": min_bend,
                "branch_length_to_trunk": round(branch_len, 3),
            }
        )
    connector = _sensor_service_connector_spec(
        name="lower_ir_service_connector",
        domain="lower_dry_harness",
        owner_part="plate_support_frame",
        disconnect="lower_dry_row_end",
        x=trunk_x,
        y=conn_y,
        z=-conn_h,
        params=params,
    )
    return {
        "lower_ir_harness_routes": routes,
        "lower_ir_harness_trunk": trunk,
        "lower_ir_connector_envelope": connector,
    }


def _lid_sensor_harness_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_bottom_z: float,
    lid_top_z: float,
    headspace_sht41_mounts: list[dict[str, Any]],
    gas_sensor_pcb_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    harness = params["sensor_harness"]
    wire_w = harness["wire_bundle_width_xy"]
    wire_h = harness["wire_bundle_height_z"]
    min_bend = harness["min_bend_radius"]
    conn_dims = _service_connector_dimensions(params)
    conn_len = float(conn_dims["board_length_x"])
    conn_wid = float(conn_dims["board_width_y"])
    edge_gap_y = harness["lid_connector_edge_gap_y"]
    conn_y = float(layout["width_y"]) - conn_wid - edge_gap_y
    left_x = harness["lid_left_trunk_x"]
    left_w = harness["lid_left_trunk_width_x"]
    right_x = harness["lid_right_trunk_x"]
    right_w = harness["lid_right_trunk_width_x"]

    gas_ys = [float(mount["aperture_y"]) for mount in gas_sensor_pcb_mounts]
    sht_ys = [float(mount["aperture_y"]) for mount in headspace_sht41_mounts]
    cover_trunk_y = max(params["row"]["side_margin_y"], min(gas_ys) - min_bend)
    shell_trunk_y = max(params["row"]["side_margin_y"], min(sht_ys) - min_bend)
    trunk_y2 = conn_y + conn_wid
    trunks = [
        {
            "name": "lid_cover_left_gas_bus",
            "domain": "lid_sensor_harness",
            "owner_part": "lid_cover",
            "retention": "printed_snap_cover",
            "x": round(left_x, 3),
            "y": round(cover_trunk_y, 3),
            "z": round(lid_top_z, 3),
            "length_x": round(left_w, 3),
            "width_y": round(trunk_y2 - cover_trunk_y, 3),
            "height_z": round(wire_h, 3),
            "channel_depth_z": harness["channel_depth_z"],
            "cover_height_z": harness["cover_height_z"],
            "min_bend_radius": min_bend,
        },
        {
            "name": "lid_cover_right_gas_bus",
            "domain": "lid_sensor_harness",
            "owner_part": "lid_cover",
            "retention": "printed_snap_cover",
            "x": round(right_x, 3),
            "y": round(cover_trunk_y, 3),
            "z": round(lid_top_z, 3),
            "length_x": round(right_w, 3),
            "width_y": round(trunk_y2 - cover_trunk_y, 3),
            "height_z": round(wire_h, 3),
            "channel_depth_z": harness["channel_depth_z"],
            "cover_height_z": harness["cover_height_z"],
            "min_bend_radius": min_bend,
        },
        {
            "name": "lid_shell_right_sht41_bus",
            "domain": "lid_sensor_harness",
            "owner_part": "lid_manifold_shell",
            "retention": "printed_snap_cover",
            "x": round(right_x, 3),
            "y": round(shell_trunk_y, 3),
            "z": round(lid_bottom_z + harness.get("wire_bundle_height_z", wire_h), 3),
            "length_x": round(right_w, 3),
            "width_y": round(trunk_y2 - shell_trunk_y, 3),
            "height_z": round(wire_h, 3),
            "channel_depth_z": harness["channel_depth_z"],
            "cover_height_z": harness["cover_height_z"],
            "min_bend_radius": min_bend,
        },
    ]
    trunk_by_name = {trunk["name"]: trunk for trunk in trunks}
    routes: list[dict[str, Any]] = []
    for mount in gas_sensor_pcb_mounts:
        if mount["role"] == "supply":
            trunk = trunk_by_name["lid_cover_left_gas_bus"]
            branch_x = float(trunk["x"]) + float(trunk["length_x"])
            branch_len = max(float(mount["x"]) - branch_x, 0.0)
        else:
            trunk = trunk_by_name["lid_cover_right_gas_bus"]
            branch_x = float(mount["x"]) + float(mount["length_x"])
            branch_len = max(float(trunk["x"]) - branch_x, 0.0)
        center_y = float(mount["aperture_y"])
        relief_len = min(harness["strain_relief_length_x"], branch_len)
        relief_x = (
            branch_x
            if mount["role"] == "return"
            else branch_x + branch_len - relief_len
        )
        routes.append(
            {
                "name": f"{mount['name']}_lid_cover_branch",
                "domain": "lid_sensor_harness",
                "sensor_name": mount["name"],
                "owner_part": "lid_cover",
                "retention": "printed_snap_cover_and_strain_relief",
                "branch_rect": {
                    "x": round(branch_x, 3),
                    "y": round(center_y - wire_w / 2, 3),
                    "z": round(float(mount["z"]), 3),
                    "length_x": round(branch_len, 3),
                    "width_y": round(wire_w, 3),
                    "height_z": round(wire_h, 3),
                },
                "strain_relief_rect": {
                    "x": round(relief_x, 3),
                    "y": round(center_y - harness["strain_relief_width_y"] / 2, 3),
                    "z": round(float(mount["z"]), 3),
                    "length_x": round(relief_len, 3),
                    "width_y": round(harness["strain_relief_width_y"], 3),
                    "height_z": round(wire_h, 3),
                    "depth_z": round(harness["strain_relief_depth_z"], 3),
                },
                "trunk_name": trunk["name"],
                "min_bend_radius": min_bend,
                "branch_length_to_trunk": round(branch_len, 3),
            }
        )
    shell_trunk = trunk_by_name["lid_shell_right_sht41_bus"]
    for mount in headspace_sht41_mounts:
        center_y = float(mount["aperture_y"])
        routes.append(
            {
                "name": f"{mount['name']}_inline_lid_shell_bus",
                "domain": "lid_sensor_harness",
                "sensor_name": mount["name"],
                "tile_index": mount["tile_index"],
                "owner_part": "lid_manifold_shell",
                "retention": "printed_snap_cover_and_strain_relief",
                "inline_trunk": True,
                "branch_rect": {
                    "x": round(float(shell_trunk["x"]), 3),
                    "y": round(center_y - wire_w / 2, 3),
                    "z": round(float(mount["z"]), 3),
                    "length_x": round(float(shell_trunk["length_x"]), 3),
                    "width_y": round(wire_w, 3),
                    "height_z": round(wire_h, 3),
                },
                "strain_relief_rect": {
                    "x": round(float(mount["x"]) + float(mount["length_x"]) - 1.0, 3),
                    "y": round(center_y - harness["strain_relief_width_y"] / 2, 3),
                    "z": round(float(mount["z"]), 3),
                    "length_x": 1.0,
                    "width_y": round(harness["strain_relief_width_y"], 3),
                    "height_z": round(wire_h, 3),
                    "depth_z": round(harness["strain_relief_depth_z"], 3),
                },
                "trunk_name": shell_trunk["name"],
                "min_bend_radius": min_bend,
                "branch_length_to_trunk": 0.0,
            }
        )

    left_connector = _sensor_service_connector_spec(
        name="lid_left_gas_service_connector",
        domain="lid_sensor_harness",
        owner_part="lid_cover",
        disconnect="removable_lid_left_gas",
        x=left_x,
        y=conn_y,
        z=lid_top_z,
        params=params,
    )
    right_connector = _sensor_service_connector_spec(
        name="lid_right_sensor_service_connector",
        domain="lid_sensor_harness",
        owner_part="lid_cover",
        disconnect="removable_lid_right_sensor_bus",
        x=float(layout["length_x"]) - conn_len - 1.0,
        y=conn_y,
        z=lid_top_z,
        params=params,
    )
    return {
        "lid_sensor_harness_routes": routes,
        "lid_sensor_harness_trunks": trunks,
        "lid_service_connector_envelopes": [left_connector, right_connector],
    }


def _harness_z_shift(
    rects: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    assembly_position: bool,
) -> float:
    if assembly_position:
        return 0.0
    return -min(float(rect["z"]) for rect in rects)


def _boxes_from_rectangles(
    rects: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    z_shift: float = 0.0,
    expand_xy: float = 0.0,
    height: float | None = None,
    z_override: float | None = None,
) -> cq.Workplane:
    model: cq.Workplane | None = None
    for rect in rects:
        rect_h = float(height if height is not None else rect["height_z"])
        z = float(z_override if z_override is not None else rect["z"]) + z_shift
        part = (
            cq.Workplane("XY")
            .box(
                float(rect["length_x"]) + 2 * expand_xy,
                float(rect["width_y"]) + 2 * expand_xy,
                rect_h,
                centered=(False, False, False),
            )
            .translate((float(rect["x"]) - expand_xy, float(rect["y"]) - expand_xy, z))
        )
        model = part if model is None else model.union(part)
    if model is None:
        raise ValueError("harness rectangle model requires at least one rectangle")
    return model


def _bodies_from_shape_targets(
    targets: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    z_shift: float = 0.0,
) -> cq.Workplane:
    model: cq.Workplane | None = None
    for target in targets:
        z = float(target["z"]) + z_shift
        if target.get("shape") == "disk" or "diameter" in target:
            body = (
                cq.Workplane("XY")
                .circle(float(target["diameter"]) / 2)
                .extrude(float(target["height_z"]))
                .translate((float(target["x"]), float(target["y"]), z))
            )
        else:
            body = (
                cq.Workplane("XY")
                .box(
                    float(target["length_x"]),
                    float(target["width_y"]),
                    float(target["height_z"]),
                    centered=(False, False, False),
                )
                .translate((float(target["x"]), float(target["y"]), z))
            )
        model = body if model is None else model.union(body)
    if model is None:
        raise ValueError("shape target model requires at least one target")
    return model


def _cut_rectangular_gas_interface_window(
    model: cq.Workplane,
    rect: dict[str, Any],
    *,
    z_shift: float = 0.0,
) -> cq.Workplane:
    return model.cut(
        cq.Workplane("XY")
        .box(
            float(rect["length_x"]) + 0.2,
            float(rect["width_y"]) + 0.2,
            float(rect["height_z"]) + 0.2,
            centered=(False, False, False),
        )
        .translate(
            (
                float(rect["x"]) - 0.1,
                float(rect["y"]) - 0.1,
                float(rect["z"]) + z_shift - 0.1,
            )
        )
    )


def _build_sensor_service_connector_models(
    connectors: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    z_shift: float = 0.0,
) -> cq.Workplane:
    model: cq.Workplane | None = None
    for connector in connectors:
        rects = [
            connector["board_rect"],
            connector["header_rect"],
            connector["plug_rect"],
            connector["latch_rect"],
        ]
        part = _boxes_from_rectangles(rects, z_shift=z_shift)
        marker = connector["pin1_marker"]
        part = part.union(
            cq.Workplane("XY")
            .circle(float(marker["diameter"]) / 2)
            .extrude(float(marker["height_z"]))
            .translate((float(marker["x"]), float(marker["y"]), float(marker["z"]) + z_shift))
        )
        header = connector["header_rect"]
        circuits = int(connector["circuits"])
        pitch = float(connector["pitch"])
        pin_span = pitch * (circuits - 1)
        first_x = float(header["x"]) + (float(header["length_x"]) - pin_span) / 2
        for idx in range(circuits):
            part = part.union(
                cq.Workplane("XY")
                .box(0.22, 0.8, 0.12, centered=(False, False, False))
                .translate(
                    (
                        first_x + idx * pitch - 0.11,
                        float(header["y"]) + 0.35,
                        float(header["z"]) + float(header["height_z"]) + z_shift,
                    )
                )
            )
        model = part if model is None else model.union(part)
    if model is None:
        raise ValueError("sensor service connector model requires at least one connector")
    return model


def _build_printed_sensor_connector_shrouds(
    connectors: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    z_shift: float = 0.0,
) -> cq.Workplane:
    model: cq.Workplane | None = None
    for connector in connectors:
        shroud = connector["printed_shroud"]
        wall = float(shroud["wall_xy"])
        x = float(shroud["x"])
        y = float(shroud["y"])
        z = float(shroud["z"]) + z_shift
        length = float(shroud["length_x"])
        width = float(shroud["width_y"])
        height = float(shroud["height_z"])
        rails = (
            cq.Workplane("XY")
            .box(wall, width, height, centered=(False, False, False))
            .translate((x, y, z))
            .union(
                cq.Workplane("XY")
                .box(wall, width, height, centered=(False, False, False))
                .translate((x + length - wall, y, z))
            )
            .union(
                cq.Workplane("XY")
                .box(length, wall, height, centered=(False, False, False))
                .translate((x, y, z))
            )
        )
        key = connector["key_rib_rect"]
        rails = rails.union(
            cq.Workplane("XY")
            .box(
                float(key["length_x"]),
                float(key["width_y"]),
                float(key["height_z"]),
                centered=(False, False, False),
            )
            .translate((float(key["x"]), float(key["y"]), float(key["z"]) + z_shift))
        )
        model = rails if model is None else model.union(rails)
    if model is None:
        raise ValueError("sensor connector shroud model requires at least one connector")
    return model


def _harness_cover_from_rectangles(
    rects: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    params: dict[str, Any],
    underside: bool,
    z_shift: float = 0.0,
) -> cq.Workplane:
    harness = params["sensor_harness"]
    cover_h = harness["cover_height_z"]
    overlap = harness["cover_overlap_xy"]
    cover: cq.Workplane | None = None
    for rect in rects:
        if underside:
            z = float(rect["z"]) + z_shift - cover_h
        else:
            z = float(rect["z"]) + z_shift + float(rect["height_z"])
        part = (
            cq.Workplane("XY")
            .box(
                float(rect["length_x"]) + 2 * overlap,
                float(rect["width_y"]) + 2 * overlap,
                cover_h,
                centered=(False, False, False),
            )
            .translate((float(rect["x"]) - overlap, float(rect["y"]) - overlap, z))
        )
        cover = part if cover is None else cover.union(part)
    if cover is None:
        raise ValueError("harness cover requires at least one rectangle")
    return cover


def _add_harness_snap_tabs(
    model: cq.Workplane,
    trunk: dict[str, Any],
    *,
    params: dict[str, Any],
    underside: bool,
    z_shift: float = 0.0,
) -> cq.Workplane:
    harness = params["sensor_harness"]
    pitch = harness["snap_tab_pitch_y"]
    tab_len = harness["snap_tab_length_y"]
    tab_w = harness["snap_tab_width_x"]
    cover_h = harness["cover_height_z"]
    layout = row_coupon_layout(params)
    y = float(trunk["y"]) + pitch / 2
    y_end = float(trunk["y"]) + float(trunk["width_y"]) - tab_len
    if underside:
        z = float(trunk["z"]) + z_shift - cover_h
    else:
        z = float(trunk["z"]) + z_shift + float(trunk["height_z"])
    while y <= y_end:
        x_candidates = [
            float(trunk["x"]) - tab_w,
            float(trunk["x"]) + float(trunk["length_x"]),
        ]
        for x in x_candidates:
            if x < 0 or x + tab_w > float(layout["length_x"]):
                continue
            model = model.union(
                cq.Workplane("XY")
                .box(tab_w, tab_len, cover_h, centered=(False, False, False))
                .translate((x, y, z))
            )
        y += pitch
    return model


def _cut_vertical_mount_aperture(
    model: cq.Workplane,
    mount: dict[str, Any],
    *,
    z: float,
) -> cq.Workplane:
    aperture_z = float(mount["aperture_z"]) - float(mount["z"]) + z
    radius = float(mount["aperture_diameter"]) / 2
    length_x = float(mount["length_x"])
    width_y = float(mount["width_y"])
    if length_x <= width_y:
        cutter = (
            cq.Workplane("YZ")
            .circle(radius)
            .extrude(length_x + 0.2)
            .translate((float(mount["x"]) - 0.1, float(mount["aperture_y"]), aperture_z))
        )
        return model.cut(cutter)
    cutter = (
        cq.Workplane("XZ")
        .circle(radius)
        .extrude(width_y + 0.2)
        .translate((float(mount["aperture_x"]), float(mount["y"]) - 0.1, aperture_z))
    )
    return model.cut(cutter)


def _sensor_chip_marker_for_mount(
    mount: dict[str, Any],
    *,
    z: float,
) -> cq.Workplane:
    aperture_z = float(mount["aperture_z"]) - float(mount["z"]) + z
    length_x = float(mount["length_x"])
    width_y = float(mount["width_y"])
    chip_w = 3.2
    chip_h = 3.2
    chip_t = 0.45
    if length_x <= width_y:
        return (
            cq.Workplane("XY")
            .box(chip_t, chip_w, chip_h, centered=(False, False, False))
            .translate(
                (
                    float(mount["x"]) + length_x + 0.02,
                    float(mount["aperture_y"]) - chip_w / 2,
                    aperture_z - chip_h / 2,
                )
            )
        )
    return (
        cq.Workplane("XY")
        .box(chip_w, chip_t, chip_h, centered=(False, False, False))
        .translate(
            (
                float(mount["aperture_x"]) - chip_w / 2,
                float(mount["y"]) + width_y + 0.02,
                aperture_z - chip_h / 2,
            )
        )
    )


def _add_gas_sensor_pcb_sockets(
    cover: cq.Workplane,
    *,
    params: dict[str, Any],
    assembly_position: bool,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    mounts = params.get("sensor_mounts", {})
    wall = mounts.get("gas_pcb_socket_wall_thickness", 1.2)
    lip_h = mounts.get("gas_pcb_socket_lip_height_z", 1.2)
    lip_w = mounts.get("gas_pcb_socket_lip_width_xy", 1.5)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]

    for mount in layout["gas_sensor_pcb_mounts"]:
        x = float(mount["x"])
        y = float(mount["y"])
        z = float(mount["z"]) + z_shift
        length_x = float(mount["length_x"])
        width_y = float(mount["width_y"])
        height_z = float(mount["height_z"])
        shelf_z = z
        cover = cover.union(
            cq.Workplane("XY")
            .box(length_x + 2 * wall, width_y + 2 * wall, lip_h, centered=(False, False, False))
            .translate((x - wall, y - wall, shelf_z))
        )
        cover = cover.union(
            _perimeter_rails(
                x0=x - wall,
                y0=y - wall,
                length=length_x + 2 * wall,
                width=width_y + 2 * wall,
                rail_width=wall,
                height=height_z,
                z0=z,
            )
        )
        interface = mount["gas_interface"]
        cover = cover.union(
            _boxes_from_rectangles([interface["seal_land_rect"]], z_shift=z_shift)
        )
        cover = cover.union(
            _boxes_from_rectangles(interface["compression_pad_rects"], z_shift=z_shift)
        )
        if length_x <= width_y:
            rail_len_x = length_x + 2 * wall
            cover = cover.union(
                cq.Workplane("XY")
                .box(rail_len_x, lip_w, lip_h, centered=(False, False, False))
                .translate((x - wall, y + width_y - lip_w / 2, z + height_z - lip_h))
            )
        else:
            rail_len_y = width_y + 2 * wall
            cover = cover.union(
                cq.Workplane("XY")
                .box(lip_w, rail_len_y, lip_h, centered=(False, False, False))
                .translate((x + length_x - lip_w / 2, y - wall, z + height_z - lip_h))
            )
        cover = _cut_rectangular_gas_interface_window(
            cover,
            interface["flow_cell_rect"],
            z_shift=z_shift,
        )
        cover = _cut_vertical_mount_aperture(cover, mount, z=z)
        cable = mount["cable_exit_rect"]
        cover = cover.cut(
            cq.Workplane("XY")
            .box(
                float(cable["length_x"]),
                float(cable["width_y"]),
                float(cable["depth_z"]) + 0.1,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(cable["x"]),
                    float(cable["y"]),
                    float(cable["z"]) + z_shift - 0.05,
                )
            )
        )
    return cover


def _add_headspace_sht41_sockets(
    shell: cq.Workplane,
    *,
    params: dict[str, Any],
    assembly_position: bool,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_bottom_z"]

    for mount in layout["headspace_sht41_mounts"]:
        shell = shell.union(
            _boxes_from_rectangles(
                [mount["protected_cassette_outer_rect"]],
                z_shift=z_shift,
            )
        )
        pocket = mount["protected_pocket_cut_rect"]
        shell = shell.cut(
            cq.Workplane("XY")
            .box(
                float(pocket["length_x"]) + 0.2,
                float(pocket["width_y"]),
                float(pocket["height_z"]),
                centered=(False, False, False),
            )
            .translate(
                (
                    float(pocket["x"]),
                    float(pocket["y"]),
                    float(pocket["z"]) + z_shift,
                )
            )
        )
        shell = shell.union(
            _boxes_from_rectangles(
                [mount["registration_key_rect"]],
                z_shift=z_shift,
            )
        )
        ring = mount["drip_break_ring"]
        ring_body = (
            cq.Workplane("XY")
            .circle(float(ring["outer_diameter"]) / 2)
            .extrude(float(ring["height_z"]))
            .translate((float(ring["x"]), float(ring["y"]), float(ring["z"]) + z_shift))
        )
        ring_cut = (
            cq.Workplane("XY")
            .circle(float(ring["inner_diameter"]) / 2)
            .extrude(float(ring["height_z"]) + 0.2)
            .translate((float(ring["x"]), float(ring["y"]), float(ring["z"]) + z_shift - 0.1))
        )
        shell = shell.union(ring_body.cut(ring_cut))
        shell = shell.cut(
            cq.Workplane("XY")
            .circle(float(mount["aperture_diameter"]) / 2)
            .extrude(
                float(mount["drip_break_ring"]["height_z"])
                + float(mount["protected_cassette_outer_rect"]["height_z"])
                + 0.4
            )
            .translate(
                (
                    float(mount["aperture_x"]),
                    float(mount["aperture_y"]),
                    float(mount["drip_break_ring"]["z"]) + z_shift - 0.2,
                )
            )
        )
        cable = mount["cable_exit_rect"]
        shell = shell.cut(
            cq.Workplane("XY")
            .box(
                float(cable["length_x"]),
                float(cable["width_y"]),
                float(mount["height_z"]) + 0.2,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(cable["x"]),
                    float(cable["y"]),
                    float(cable["z"]) + z_shift - 0.1,
                )
            )
        )
    return shell


def _cut_ir_sensor_pockets_and_apertures(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    mounts = params.get("sensor_mounts", {})
    clearance_d = mounts.get("ir_pocket_clearance_diameter", 0.4)
    base = params["base"]
    support = params["plate_support"]
    for mount in layout["ir_sensor_mounts"]:
        center_x = float(mount["center_x"])
        center_y = float(mount["center_y"])
        pocket_d = float(mount["length_x"]) + clearance_d
        model = model.cut(
            cq.Workplane("XY")
            .circle(pocket_d / 2)
            .extrude(float(mount["height_z"]) + 0.1)
            .translate((center_x, center_y, -0.05))
        )
        model = model.cut(
            cq.Workplane("XY")
            .circle(float(mount["aperture_diameter"]) / 2)
            .extrude(base["thickness_z"] + support["land_height_z"] + 0.4)
            .translate((center_x, center_y, -0.2))
        )
    return model


def _cut_lower_sensor_harness_channels(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    harness = params["sensor_harness"]
    channel_depth = harness["channel_depth_z"]
    channel_clearance = harness["channel_clearance_xy"]
    rects = [layout["lower_ir_harness_trunk"]]
    for route in layout["lower_ir_harness_routes"]:
        rects.append(route["branch_rect"])
        rects.append(route["strain_relief_rect"])
    for rect in rects:
        model = model.cut(
            cq.Workplane("XY")
            .box(
                float(rect["length_x"]) + 2 * channel_clearance,
                float(rect["width_y"]) + 2 * channel_clearance,
                channel_depth + 0.05,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(rect["x"]) - channel_clearance,
                    float(rect["y"]) - channel_clearance,
                    -0.01,
                )
            )
        )
    return model


def _cut_lid_sensor_harness_channels(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
    owner_part: str,
    assembly_position: bool,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    harness = params["sensor_harness"]
    channel_depth = harness["channel_depth_z"]
    channel_clearance = harness["channel_clearance_xy"]
    z_shift = 0.0
    if not assembly_position:
        if owner_part == "lid_manifold_shell":
            z_shift = -layout["lid_bottom_z"]
        else:
            z_shift = -layout["lid_top_z"]
    rects: list[dict[str, Any]] = [
        trunk
        for trunk in layout["lid_sensor_harness_trunks"]
        if trunk["owner_part"] == owner_part
    ]
    for route in layout["lid_sensor_harness_routes"]:
        if route["owner_part"] != owner_part:
            continue
        rects.append(route["branch_rect"])
        rects.append(route["strain_relief_rect"])
    for rect in rects:
        model = model.cut(
            cq.Workplane("XY")
            .box(
                float(rect["length_x"]) + 2 * channel_clearance,
                float(rect["width_y"]) + 2 * channel_clearance,
                channel_depth + 0.05,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(rect["x"]) - channel_clearance,
                    float(rect["y"]) - channel_clearance,
                    float(rect["z"]) + z_shift - 0.05,
                )
            )
        )
    return model


def _add_ir_sensor_retention_lips(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    mounts = params.get("sensor_mounts", {})
    lip_w = mounts.get("ir_retention_lip_width_xy", 1.0)
    lip_h = mounts.get("ir_retention_lip_height_z", 0.7)
    for mount in layout["ir_sensor_mounts"]:
        body_d = float(mount["length_x"])
        x0 = float(mount["center_x"]) - body_d / 2 - lip_w
        y_values = [
            float(mount["center_y"]) - body_d / 2 - lip_w,
            float(mount["center_y"]) + body_d / 2,
        ]
        for y0 in y_values:
            model = model.union(
                cq.Workplane("XY")
                .box(body_d + 2 * lip_w, lip_w, lip_h, centered=(False, False, False))
                .translate((x0, y0, 0.0))
            )
    return model


def _add_ir_aperture_drip_collars(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    for mount in layout["ir_sensor_mounts"]:
        collar = mount["drip_collar"]
        body = (
            cq.Workplane("XY")
            .circle(float(collar["outer_diameter"]) / 2)
            .extrude(float(collar["height_z"]))
            .translate((float(collar["x"]), float(collar["y"]), float(collar["z"])))
        )
        aperture = (
            cq.Workplane("XY")
            .circle(float(collar["inner_diameter"]) / 2)
            .extrude(float(collar["height_z"]) + 0.2)
            .translate((float(collar["x"]), float(collar["y"]), float(collar["z"]) - 0.1))
        )
        model = model.union(body.cut(aperture))
    return model


def _add_lid_port_interface(
    cover: cq.Workplane,
    port: dict[str, Any],
    *,
    params: dict[str, Any],
    layout: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    x = float(port["x"])
    y = float(port["y"])
    boss_d = float(port["boss_diameter"])
    boss_h = float(port["boss_height_z"])
    seal_land_w = production.get("port_seal_land_width_xy", 0.0)
    seal_land_h = production.get("port_seal_land_height_z", 0.0)

    if seal_land_w > 0 and seal_land_h > 0:
        cover = cover.union(
            cq.Workplane("XY")
            .circle(boss_d / 2 + seal_land_w)
            .extrude(seal_land_h)
            .translate((x, y, z0))
        )
    cover = cover.union(
        cq.Workplane("XY")
        .circle(boss_d / 2)
            .extrude(boss_h)
            .translate((x, y, z0))
    )
    lip_inner_d = float(port.get("cap_seal_lip_inner_diameter", 0.0))
    lip_outer_d = float(port.get("cap_seal_lip_outer_diameter", 0.0))
    lip_seat_depth = float(port.get("cap_seal_lip_seat_depth_z", 0.0))
    if min(lip_inner_d, lip_outer_d, lip_seat_depth) > 0:
        seal_seat = (
            cq.Workplane("XY")
            .circle(lip_outer_d / 2)
            .extrude(lip_seat_depth + 0.1)
            .translate((x, y, z0 + boss_h - lip_seat_depth - 0.05))
        )
        seal_seat = seal_seat.cut(
            cq.Workplane("XY")
            .circle(lip_inner_d / 2)
            .extrude(lip_seat_depth + 0.2)
            .translate((x, y, z0 + boss_h - lip_seat_depth - 0.1))
        )
        cover = cover.cut(seal_seat)
    return cover


def _axis_cylinder(
    *,
    axis: str,
    x: float,
    y: float,
    z: float,
    length: float,
    diameter: float,
) -> cq.Workplane:
    radius = diameter / 2
    if axis == "x":
        return cq.Workplane("YZ").circle(radius).extrude(length).translate((x, y, z))
    if axis == "y":
        return cq.Workplane("XZ").circle(radius).extrude(length).translate((x, y, z))
    raise ValueError("axis cylinder must use axis 'x' or 'y'")


def _axis_tube(
    *,
    axis: str,
    x: float,
    y: float,
    z: float,
    length: float,
    outer_diameter: float,
    inner_diameter: float,
) -> cq.Workplane:
    if inner_diameter <= 0:
        return _axis_cylinder(
            axis=axis,
            x=x,
            y=y,
            z=z,
            length=length,
            diameter=outer_diameter,
        )
    if inner_diameter >= outer_diameter:
        raise ValueError("axis tube inner diameter must be smaller than outer diameter")

    outer = _axis_cylinder(
        axis=axis,
        x=x,
        y=y,
        z=z,
        length=length,
        diameter=outer_diameter,
    )
    if axis == "x":
        inner = _axis_cylinder(
            axis=axis,
            x=x - 0.05,
            y=y,
            z=z,
            length=length + 0.1,
            diameter=inner_diameter,
        )
    elif axis == "y":
        inner = _axis_cylinder(
            axis=axis,
            x=x,
            y=y - 0.05,
            z=z,
            length=length + 0.1,
            diameter=inner_diameter,
        )
    else:
        raise ValueError("axis tube must use axis 'x' or 'y'")
    return outer.cut(inner)


def _add_sample_relief_leak_witness_features(
    cover: cq.Workplane,
    *,
    params: dict[str, Any],
    assembly_position: bool,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    for witness in layout["sample_relief_leak_witnesses"]:
        shelf = dict(witness["shelf_rect"])
        shelf["z"] = float(shelf["z"]) + z_shift
        cover = cover.union(_boxes_from_rectangles([shelf]))

        threshold = dict(witness["threshold_rect"])
        threshold["z"] = float(threshold["z"]) + z_shift
        cover = cover.union(_boxes_from_rectangles([threshold]))

        gutter = dict(witness["gutter_rect"])
        gutter["z"] = float(gutter["z"]) + z_shift
        cover = cover.cut(_boxes_from_rectangles([gutter]))
    return cover


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


def _add_side_gas_service_features(
    cover: cq.Workplane,
    *,
    params: dict[str, Any],
    assembly_position: bool,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    for interface in layout["side_gas_service_interfaces"]:
        block = dict(interface["block_rect"])
        block["z"] = float(block["z"]) + z_shift
        cover = cover.union(_boxes_from_rectangles([block]))

        for feature_name in ("printed_fitting", "printed_barb_retention_bead"):
            feature = interface[feature_name]
            cover = cover.union(
                _axis_cylinder(
                    axis=feature["axis"],
                    x=float(feature["x"]),
                    y=float(feature["y"]),
                    z=float(feature["z"]) + z_shift,
                    length=float(feature["length"]),
                    diameter=float(feature["diameter"]),
                )
            )

        relief = dict(interface["strain_relief_rect"])
        relief["z"] = float(relief["z"]) + z_shift
        cover = cover.union(_boxes_from_rectangles([relief]))

        threshold_rects = []
        for rect in interface["leak_witness_threshold_rects"]:
            threshold = dict(rect)
            threshold["z"] = float(threshold["z"]) + z_shift
            threshold_rects.append(threshold)
        cover = cover.union(_boxes_from_rectangles(threshold_rects))

        for rect in interface["leak_witness_gutter_rects"]:
            gutter = dict(rect)
            gutter["z"] = float(gutter["z"]) + z_shift
            cover = cover.cut(_boxes_from_rectangles([gutter]))

        opening = interface["duct_opening"]
        cover = cover.cut(
            _axis_cylinder(
                axis=opening["axis"],
                x=float(opening["x"]),
                y=float(opening["y"]),
                z=float(opening["z"]) + z_shift,
                length=float(opening["length"]),
                diameter=float(opening["diameter"]),
            )
        )
    return cover


def _well_centers_for_tile(
    tile: dict[str, Any],
    params: dict[str, Any],
) -> list[tuple[float, float]]:
    grid = params["well_grid"]
    centers: list[tuple[float, float]] = []
    for row_idx in range(grid["rows"]):
        for col_idx in range(grid["columns"]):
            centers.append(
                (
                    tile["x"] + grid["first_well_center_x"] + col_idx * grid["pitch_x"],
                    tile["y"] + grid["first_well_center_y"] + row_idx * grid["pitch_y"],
                )
            )
    return centers


def _well_grid_rectangle_for_tile(
    tile: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, float | int]:
    centers = _well_centers_for_tile(tile, params)
    xs = [point[0] for point in centers]
    ys = [point[1] for point in centers]
    return {
        "tile_index": tile.get("index", 0),
        "x": round(min(xs), 3),
        "y": round(min(ys), 3),
        "length_x": round(max(xs) - min(xs), 3),
        "width_y": round(max(ys) - min(ys), 3),
    }


def _septum_access_window_for_tile(
    tile: dict[str, Any],
    params: dict[str, Any],
) -> tuple[float, float, float, float]:
    mat = params["septum_mat"]
    access = params["pipette_access"]
    centers = _well_centers_for_tile(tile, params)
    xs = [point[0] for point in centers]
    ys = [point[1] for point in centers]
    radius = mat["round_plug_diameter"] / 2
    clearance = access["septum_window_clearance_xy"]
    x0 = min(xs) - radius - clearance
    x1 = max(xs) + radius + clearance
    y0 = min(ys) - radius - clearance
    y1 = max(ys) + radius + clearance
    return x0, y0, x1 - x0, y1 - y0


def _cut_septum_lift_notch(
    model: cq.Workplane,
    *,
    access_x: float,
    access_y: float,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    mat = params["septum_mat"]
    lid = params["lid_manifold"]
    notch_width = mat.get("lift_notch_width_x", 0.0)
    notch_depth = mat.get("lift_notch_depth_y", 0.0)
    if notch_width <= 0 or notch_depth <= 0:
        return model

    notch_x = access_x + (_septum_access_window_length(params) - notch_width) / 2
    notch_y = access_y - notch_depth
    return model.cut(
        cq.Workplane("XY")
        .box(
            notch_width,
            notch_depth + 0.1,
            lid["thickness_z"] + lid["duct_height_z"] + 0.4,
            centered=(False, False, False),
        )
        .translate((notch_x, notch_y, z0 - 0.2))
    )


def _septum_access_window_length(params: dict[str, Any]) -> float:
    mat = params["septum_mat"]
    access = params["pipette_access"]
    grid = params["well_grid"]
    radius = mat["round_plug_diameter"] / 2
    clearance = access["septum_window_clearance_xy"]
    return (grid["columns"] - 1) * grid["pitch_x"] + 2 * (radius + clearance)


def _cut_septum_slit_reliefs(
    model: cq.Workplane,
    centers: list[tuple[float, float]],
    z0: float,
    mat: dict[str, Any],
) -> cq.Workplane:
    slit_len = mat.get("slit_cut_length_x", 0.0)
    slit_wid = mat.get("slit_cut_width_y", 0.0)
    if slit_len <= 0 or slit_wid <= 0:
        return model

    cut_depth = mat["sheet_thickness_z"] + mat["round_plug_depth_z"] + 0.4
    slits = (
        cq.Workplane("XY")
        .pushPoints(centers)
        .rect(slit_len, slit_wid)
        .extrude(cut_depth)
        .translate((0, 0, z0 - mat["round_plug_depth_z"] - 0.2))
    )
    return model.cut(slits)


def _add_deck_slot_shoes(
    model: cq.Workplane,
    *,
    layout: dict[str, Any],
    params: dict[str, Any],
) -> cq.Workplane:
    deck = params["deck_interface"]
    thickness = deck["slot_shoe_thickness_z"]
    z0 = layout["deck_plane_z"]
    clearance = deck["slot_shoe_clearance_xy"]
    shoe_len = deck["slot_opening_length_x"] - 2 * clearance
    shoe_wid = deck["slot_opening_width_y"] - 2 * clearance
    for tile in layout["tile_origins"]:
        x, y, _, _ = _deck_slot_opening_for_tile(tile, params)
        shoe = _rounded_box(
            shoe_len,
            shoe_wid,
            thickness,
            deck["slot_shoe_corner_radius"],
        ).translate((x + clearance, y + clearance, z0))
        model = model.union(shoe)
    return model


def _deck_slot_opening_for_tile(
    tile: dict[str, Any],
    params: dict[str, Any],
) -> tuple[float, float, float, float]:
    deck = params["deck_interface"]
    plate = params["plate"]
    slot_len = deck["slot_opening_length_x"]
    slot_wid = deck["slot_opening_width_y"]
    x = tile["x"] + (plate["length_x"] - slot_len) / 2
    y = tile["y"] + (plate["width_y"] - slot_wid) / 2
    return x, y, slot_len, slot_wid


def _deck_engagement_foot_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, float | int]]:
    deck = params["deck_interface"]
    foot_len = deck["foot_length_x"]
    foot_wid = deck["foot_width_y"]
    clearance = deck.get("foot_slot_clearance_xy", deck["slot_shoe_clearance_xy"])
    feet: list[dict[str, float | int]] = []

    for tile in tile_origins:
        slot_x, slot_y, slot_len, slot_wid = _deck_slot_opening_for_tile(tile, params)
        x_values = [
            slot_x + clearance,
            slot_x + slot_len - clearance - foot_len,
        ]
        y_values = [
            slot_y + clearance,
            slot_y + slot_wid - clearance - foot_wid,
        ]
        for x in x_values:
            for y in y_values:
                feet.append(
                    {
                        "tile_index": tile["index"],
                        "x": round(x, 3),
                        "y": round(y, 3),
                        "length_x": foot_len,
                        "width_y": foot_wid,
                    }
                )
    return feet


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


def _dry_bay_obstruction_review_rectangles(
    *,
    dry_bay_envelope: dict[str, Any],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    dry_x = float(dry_bay_envelope["x"])
    dry_y = float(dry_bay_envelope["y"])
    dry_z0 = float(dry_bay_envelope["bottom_z"])
    dry_len = float(dry_bay_envelope["length_x"])
    dry_wid = float(dry_bay_envelope["width_y"])
    dry_h = float(dry_bay_envelope["top_z"]) - dry_z0
    margin = float(production.get("dry_bay_obstruction_review_margin_xy", 4.0))
    block_len = min(
        float(production.get("dry_bay_obstruction_review_length_x", 42.0)),
        max(dry_len - 2 * margin, 1.0),
    )
    block_wid = min(
        float(production.get("dry_bay_obstruction_review_width_y", 22.0)),
        max(dry_wid - 2 * margin, 1.0),
    )
    block_h = min(
        float(production.get("dry_bay_obstruction_review_height_z", 8.0)),
        max(dry_h - 1.0, 1.0),
    )
    top_gap = float(production.get("dry_bay_obstruction_review_top_gap_z", 1.0))
    cover_w = min(
        float(production.get("dry_bay_witness_cover_width_y", 4.0)),
        max(dry_wid / 4, 1.0),
    )
    cover_h = min(
        float(production.get("dry_bay_witness_cover_height_z", 2.5)),
        max(dry_h - 1.0, 1.0),
    )
    block_z = max(dry_z0, float(dry_bay_envelope["top_z"]) - top_gap - block_h)
    cover_z = max(dry_z0, float(dry_bay_envelope["top_z"]) - top_gap - cover_h)
    source_checks = [
        "dry_bay_ingress_audit_check",
        "wet_dry_failure_path_check",
        "dry_bay_envelope_check",
    ]
    base = {
        "review_state": "dry_bay_obstructed",
        "owner_part": "dry_bay_obstruction_review",
        "retained_part": "dry_bay_envelope",
        "source_validation_checks": source_checks,
    }
    return [
        {
            **base,
            "name": "dry_bay_foreign_object_obstruction_review",
            "review_kind": "foreign_object_inside_protected_dry_bay",
            "blocked_fail_closed_state": "dry_bay_blocked",
            "dry_bay_relation": "inside_protected_footprint",
            "x": round(dry_x + (dry_len - block_len) / 2, 3),
            "y": round(dry_y + (dry_wid - block_wid) / 2, 3),
            "z": round(block_z, 3),
            "length_x": round(block_len, 3),
            "width_y": round(block_wid, 3),
            "height_z": round(block_h, 3),
        },
        {
            **base,
            "name": "dry_bay_front_witness_path_cover_review",
            "review_kind": "wet_witness_path_visibility_cover",
            "blocked_fail_closed_state": "wet_witness_path_hidden",
            "dry_bay_relation": "front_margin_witness_path_hidden",
            "x": round(dry_x + margin, 3),
            "y": round(dry_y + margin, 3),
            "z": round(cover_z, 3),
            "length_x": round(max(dry_len - 2 * margin, 1.0), 3),
            "width_y": round(cover_w, 3),
            "height_z": round(cover_h, 3),
        },
        {
            **base,
            "name": "dry_bay_rear_witness_path_cover_review",
            "review_kind": "wet_witness_path_visibility_cover",
            "blocked_fail_closed_state": "wet_witness_path_hidden",
            "dry_bay_relation": "rear_margin_witness_path_hidden",
            "x": round(dry_x + margin, 3),
            "y": round(dry_y + dry_wid - margin - cover_w, 3),
            "z": round(cover_z, 3),
            "length_x": round(max(dry_len - 2 * margin, 1.0), 3),
            "width_y": round(cover_w, 3),
            "height_z": round(cover_h, 3),
        },
    ]


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


def _add_deck_engagement_feet(
    model: cq.Workplane,
    *,
    tile: dict[str, Any],
    params: dict[str, Any],
) -> cq.Workplane:
    deck = params["deck_interface"]
    foot_h = deck["standoff_height_z"]
    radius = deck["foot_corner_radius"]
    feet = _deck_engagement_foot_rectangles(tile_origins=[tile], params=params)

    for foot_rect in feet:
        foot = _rounded_box(
            foot_rect["length_x"],
            foot_rect["width_y"],
            foot_h,
            radius,
        ).translate((foot_rect["x"], foot_rect["y"], -foot_h))
        model = model.union(foot)

    front_left = min(feet, key=lambda foot: (foot["x"], foot["y"]))

    return _cut_deck_key_notch(
        model,
        x=front_left["x"] + front_left["length_x"] / 2,
        y=front_left["y"],
        z=-foot_h,
        deck=deck,
    )


def _cut_deck_key_notch(
    model: cq.Workplane,
    *,
    x: float,
    y: float,
    z: float,
    deck: dict[str, Any],
) -> cq.Workplane:
    return model.cut(
        cq.Workplane("XY")
        .box(
            deck["key_notch_width_x"],
            deck["key_notch_depth_y"] + 0.1,
            deck["key_notch_depth_z"],
            centered=(True, False, False),
        )
        .translate((x, y - 0.05, z - 0.05))
    )


def _plate_lateral_locator_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
    z0: float,
) -> list[dict[str, float | int]]:
    plate = params["plate"]
    support = params["plate_support"]
    wall_t = support.get("lateral_locator_wall_thickness", 0.0)
    wall_h = support.get("lateral_locator_wall_height_z", 0.0)
    clearance = support.get("lateral_locator_clearance_xy", 0.0)
    if wall_t <= 0 or wall_h <= 0:
        return []

    rails: list[dict[str, float | int]] = []
    for tile in tile_origins:
        x0 = tile["x"]
        y0 = tile["y"]
        rails.extend(
            [
                {
                    "tile_index": tile.get("index", 0),
                    "x": round(x0 - clearance - wall_t, 3),
                    "y": round(y0 - clearance, 3),
                    "z": round(z0, 3),
                    "length_x": wall_t,
                    "width_y": round(plate["width_y"] + 2 * clearance, 3),
                    "height_z": wall_h,
                },
                {
                    "tile_index": tile.get("index", 0),
                    "x": round(x0 + plate["length_x"] + clearance, 3),
                    "y": round(y0 - clearance, 3),
                    "z": round(z0, 3),
                    "length_x": wall_t,
                    "width_y": round(plate["width_y"] + 2 * clearance, 3),
                    "height_z": wall_h,
                },
                {
                    "tile_index": tile.get("index", 0),
                    "x": round(x0 - clearance - wall_t, 3),
                    "y": round(y0 - clearance - wall_t, 3),
                    "z": round(z0, 3),
                    "length_x": round(plate["length_x"] + 2 * clearance + 2 * wall_t, 3),
                    "width_y": wall_t,
                    "height_z": wall_h,
                },
                {
                    "tile_index": tile.get("index", 0),
                    "x": round(x0 - clearance - wall_t, 3),
                    "y": round(y0 + plate["width_y"] + clearance, 3),
                    "z": round(z0, 3),
                    "length_x": round(plate["length_x"] + 2 * clearance + 2 * wall_t, 3),
                    "width_y": wall_t,
                    "height_z": wall_h,
                },
            ]
        )
    return rails


def _add_plate_lateral_locator_rails(
    model: cq.Workplane,
    *,
    tile: dict[str, Any],
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    for rail in _plate_lateral_locator_rectangles(
        tile_origins=[tile],
        params=params,
        z0=z0,
    ):
        model = model.union(
            cq.Workplane("XY")
            .box(
                float(rail["length_x"]),
                float(rail["width_y"]),
                float(rail["height_z"]),
                centered=(False, False, False),
            )
            .translate((float(rail["x"]), float(rail["y"]), float(rail["z"])))
        )
    return model


def _add_plate_support_lands(
    model: cq.Workplane,
    *,
    x0: float,
    y0: float,
    plate_len: float,
    plate_wid: float,
    land_w: float,
    land_h: float,
    z0: float,
) -> cq.Workplane:
    lands = [
        (x0, y0, plate_len, land_w),
        (x0, y0 + plate_wid - land_w, plate_len, land_w),
        (x0, y0 + land_w, land_w, plate_wid - 2 * land_w),
        (x0 + plate_len - land_w, y0 + land_w, land_w, plate_wid - 2 * land_w),
    ]
    for x, y, length, width in lands:
        model = model.union(
            cq.Workplane("XY")
            .box(length, width, land_h, centered=(False, False, False))
            .translate((x, y, z0))
        )
    return model


def _dry_bay_aperture_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, float | int]]:
    plate = params["plate"]
    bay = params["dry_bay"]
    apertures: list[dict[str, float | int]] = []
    for tile in tile_origins:
        aperture_x = tile["x"] + (plate["length_x"] - bay["aperture_length_x"]) / 2
        aperture_y = tile["y"] + (plate["width_y"] - bay["aperture_width_y"]) / 2
        apertures.append(
            {
                "tile_index": tile.get("index", 0),
                "x": round(aperture_x, 3),
                "y": round(aperture_y, 3),
                "length_x": bay["aperture_length_x"],
                "width_y": bay["aperture_width_y"],
                "tile_x": round(tile["x"], 3),
                "tile_y": round(tile["y"], 3),
                "tile_length_x": plate["length_x"],
                "tile_width_y": plate["width_y"],
            }
        )
    return apertures


def _observer_fiducial_focus_target_rectangles(
    *,
    apertures: list[dict[str, float | int]],
    params: dict[str, Any],
) -> list[dict[str, float | int | str]]:
    bay = params["dry_bay"]
    recess_extra = float(bay["bottom_recess_extra"])
    recess_depth = float(bay["bottom_recess_depth"])
    objective_d = float(bay["objective_keepout_diameter"])
    crosshair_len = float(bay["crosshair_length"])
    crosshair_w = float(bay["crosshair_width"])
    fiducial_d = float(bay["observer_fiducial_diameter"])
    fiducial_offset = float(bay["observer_fiducial_offset"])

    targets: list[dict[str, float | int | str]] = []
    for aperture in apertures:
        aperture_x = float(aperture["x"])
        aperture_y = float(aperture["y"])
        aperture_len = float(aperture["length_x"])
        aperture_wid = float(aperture["width_y"])
        center_x = aperture_x + aperture_len / 2
        center_y = aperture_y + aperture_wid / 2
        tile_index = int(aperture["tile_index"])

        targets.extend(
            [
                {
                    "tile_index": tile_index,
                    "target_kind": "bottom_recess_focus_target",
                    "x": round(center_x - (aperture_len + recess_extra) / 2, 3),
                    "y": round(center_y - (aperture_wid + recess_extra) / 2, 3),
                    "z": 0.0,
                    "length_x": round(aperture_len + recess_extra, 3),
                    "width_y": round(aperture_wid + recess_extra, 3),
                    "height_z": round(recess_depth, 3),
                },
                {
                    "tile_index": tile_index,
                    "target_kind": "objective_keepout_disk",
                    "x": round(center_x, 3),
                    "y": round(center_y, 3),
                    "z": 0.0,
                    "diameter": round(objective_d, 3),
                    "height_z": round(recess_depth, 3),
                },
                {
                    "tile_index": tile_index,
                    "target_kind": "horizontal_focus_crosshair",
                    "x": round(center_x - crosshair_len / 2, 3),
                    "y": round(center_y - crosshair_w / 2, 3),
                    "z": 0.0,
                    "length_x": round(crosshair_len, 3),
                    "width_y": round(crosshair_w, 3),
                    "height_z": round(recess_depth, 3),
                },
                {
                    "tile_index": tile_index,
                    "target_kind": "vertical_focus_crosshair",
                    "x": round(center_x - crosshair_w / 2, 3),
                    "y": round(center_y - crosshair_len / 2, 3),
                    "z": 0.0,
                    "length_x": round(crosshair_w, 3),
                    "width_y": round(crosshair_len, 3),
                    "height_z": round(recess_depth, 3),
                },
            ]
        )
        for x in (
            aperture_x - fiducial_offset,
            aperture_x + aperture_len + fiducial_offset,
        ):
            for y in (
                aperture_y - fiducial_offset,
                aperture_y + aperture_wid + fiducial_offset,
            ):
                targets.append(
                    {
                        "tile_index": tile_index,
                        "target_kind": "observer_fiducial_disk",
                        "x": round(x, 3),
                        "y": round(y, 3),
                        "z": 0.0,
                        "diameter": round(fiducial_d, 3),
                        "height_z": round(recess_depth, 3),
                    }
                )
    return targets


def _target_kind_counts(
    targets: list[dict[str, Any]],
    key: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for target in targets:
        kind = str(target[key])
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def _well_cell_plane_check(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
    plate_top_z: float,
) -> dict[str, Any]:
    plate = params["plate"]
    grid = params["well_grid"]
    diameter = float(plate["well_bottom_area_equivalent_diameter"])
    thickness = float(plate.get("cell_plane_check_thickness_z", 0.2))
    z = float(plate_top_z) - float(plate["plate_top_to_cell_plane_depth_z"]) - thickness / 2
    body_targets: list[dict[str, Any]] = []
    for tile in tile_origins:
        for index, (x, y) in enumerate(_well_centers_for_tile(tile, params), start=1):
            body_targets.append(
                {
                    "name": f"well_cell_plane_tile_{tile['index']}_well_{index:02d}",
                    "shape": "disk",
                    "tile_index": tile["index"],
                    "well_index": index,
                    "x": round(x, 3),
                    "y": round(y, 3),
                    "z": round(z, 3),
                    "diameter": round(diameter, 3),
                    "height_z": round(thickness, 3),
                }
            )
    target_count = len(tile_origins) * int(grid["columns"]) * int(grid["rows"])
    return {
        "name": "well_cell_plane_check",
        "role": "published_cellvis_cell_plane_target_validation_body",
        "validation": "required_gate6_well_cell_plane_reference_evidence",
        "failure_rule": (
            "unverified_cell_plane_reference_blocks_thermal_or_biology_claims"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{target_count} wells / {diameter:.2f} mm / z={z:.2f} mm"
        ),
        "well_count": target_count,
        "diameter_cad_value": f"{diameter:.2f} mm",
        "z_cad_value": f"{z:.2f} mm",
        "source_layout_checks": ["tile_origins", "plate_top_z"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "cell_plane_reference_for_thermal_correlation",
            "biology_readiness",
            "cell_temperature_claims",
        ],
        "body_targets": body_targets,
    }


def _ir_thermopile_fov_spot_check(
    ir_sensor_mounts: list[dict[str, Any]],
    *,
    params: dict[str, Any],
    plate_bottom_z: float,
) -> dict[str, Any]:
    harness = params.get("sensor_harness", {})
    thickness = float(harness.get("ir_fov_spot_check_thickness_z", 0.2))
    z = float(plate_bottom_z) - thickness / 2
    body_targets = [
        {
            "name": f"{mount['name']}_fov_spot",
            "shape": "disk",
            "tile_index": mount["tile_index"],
            "x": mount["center_x"],
            "y": mount["center_y"],
            "z": round(z, 3),
            "diameter": mount["fov_spot_diameter"],
            "height_z": round(thickness, 3),
            "fov_angle_degrees": mount["fov_angle_degrees"],
        }
        for mount in ir_sensor_mounts
    ]
    spot_diameter = float(ir_sensor_mounts[0]["fov_spot_diameter"]) if ir_sensor_mounts else 0.0
    fov_angle = float(ir_sensor_mounts[0]["fov_angle_degrees"]) if ir_sensor_mounts else 0.0
    return {
        "name": "ir_thermopile_fov_spot_check",
        "role": "ir_thermopile_plate_margin_proxy_fov_validation_body",
        "validation": "required_gate6_ir_proxy_fov_spot_evidence",
        "failure_rule": (
            "unverified_ir_plate_margin_proxy_blocks_cell_temperature_claims"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{len(body_targets)} spots / {spot_diameter:.2f} mm at plate margin / "
            f"{fov_angle:.2f} deg FOV"
        ),
        "spot_cad_value": (
            f"{spot_diameter:.2f} mm at plate margin, {fov_angle:.2f} deg FOV"
        ),
        "spot_count": len(body_targets),
        "spot_diameter": round(spot_diameter, 3),
        "fov_angle_degrees": round(fov_angle, 3),
        "source_layout_checks": ["ir_sensor_mounts"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "ir_cell_temperature_claims",
            "edge_to_center_temperature_correlation",
            "biology_temperature_readiness",
        ],
        "body_targets": body_targets,
    }


def _thermal_condensation_proxy_check(
    thermal_condensation_proxy_targets: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = _target_kind_counts(thermal_condensation_proxy_targets, "kind")
    return {
        "name": "thermal_condensation_proxy_check",
        "role": "gate6_thermal_condensation_proxy_plan_validation_body",
        "validation": "required_gate6_thermal_condensation_proxy_evidence",
        "failure_rule": (
            "unverified_thermal_proxy_or_condensation_path_blocks_sensor_thermal_pass"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{counts.get('cell_plane_center_reference', 0)} center refs / "
            f"{counts.get('ir_plate_margin_proxy_spot', 0)} IR proxies / "
            f"{counts.get('sht41_headspace_aperture_drip_ring', 0)} SHT41 points / "
            f"{counts.get('condensation_pocket_low_point', 0)} condensation pockets"
        ),
        "target_count": len(thermal_condensation_proxy_targets),
        "proxy_kind_counts": counts,
        "source_layout_checks": ["thermal_condensation_proxy_targets"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "center_to_edge_thermal_correlation",
            "condensation_free_sensor_operation",
            "cell_temperature_claims",
            "powered_sensor_thermal_readiness",
        ],
        "body_targets": thermal_condensation_proxy_targets,
    }


def _observer_fiducial_focus_target_check(
    observer_fiducial_focus_targets: list[dict[str, Any]],
    *,
    aperture_count: int,
    dry_bay_envelope: dict[str, Any],
) -> dict[str, Any]:
    counts = _target_kind_counts(observer_fiducial_focus_targets, "target_kind")
    # OC-A6: the check used to be count-only. Make it falsifiable on two invariants:
    # (1) MULTIPLICITY -- every aperture (plate position) carries exactly its pattern:
    # 4 corner fiducial disks + one each of the four focus/keepout marks; a missing or
    # duplicated mark breaks the per-aperture multiple. (2) CONTAINMENT -- every target
    # sits inside the dry-bay envelope, so a registration mark can't fall outside the
    # imageable volume.
    fiducials_per_aperture = 4
    _per_aperture_singletons = (
        "bottom_recess_focus_target",
        "objective_keepout_disk",
        "horizontal_focus_crosshair",
        "vertical_focus_crosshair",
    )
    fiducial_multiplicity_ok = (
        aperture_count > 0
        and counts.get("observer_fiducial_disk", 0)
        == aperture_count * fiducials_per_aperture
        and all(counts.get(k, 0) == aperture_count for k in _per_aperture_singletons)
    )
    tol = _TRAVERSE_FIT_TOLERANCE_MM
    db_x0 = float(dry_bay_envelope["x"])
    db_x1 = db_x0 + float(dry_bay_envelope["length_x"])
    db_y0 = float(dry_bay_envelope["y"])
    db_y1 = db_y0 + float(dry_bay_envelope["width_y"])
    db_z0 = float(dry_bay_envelope["bottom_z"])
    db_z1 = float(dry_bay_envelope["top_z"])

    def _within(t: dict[str, Any]) -> bool:
        # Targets are a mix: disk marks carry {center x, y, diameter}; rect marks carry
        # {corner x, y, length_x, width_y}. Containment must account for the disk RADIUS
        # (a Ø32 keepout disk centered near a bay edge overhangs ~16 mm) and the Z band
        # (a target with z outside the bay depth is not imageable), not treat marks as
        # zero-extent points.
        if "diameter" in t:
            r = float(t["diameter"]) / 2.0
            x_lo, x_hi = float(t["x"]) - r, float(t["x"]) + r
            y_lo, y_hi = float(t["y"]) - r, float(t["y"]) + r
        else:
            x_lo = float(t["x"])
            x_hi = x_lo + float(t.get("length_x", 0.0))
            y_lo = float(t["y"])
            y_hi = y_lo + float(t.get("width_y", 0.0))
        tz = float(t.get("z", 0.0))
        return (
            x_lo >= db_x0 - tol
            and x_hi <= db_x1 + tol
            and y_lo >= db_y0 - tol
            and y_hi <= db_y1 + tol
            and db_z0 - tol <= tz <= db_z1 + tol
        )

    all_targets_within_dry_bay = all(
        _within(t) for t in observer_fiducial_focus_targets
    )
    fiducial_geometry_blockers: list[str] = []
    if not fiducial_multiplicity_ok:
        fiducial_geometry_blockers.append("fiducial_pattern_multiplicity_mismatch")
    if not all_targets_within_dry_bay:
        fiducial_geometry_blockers.append("fiducial_target_outside_dry_bay")
    return {
        "name": "observer_fiducial_focus_target_check",
        "role": "observer_fiducial_focus_pattern_validation_body",
        "validation": "required_gate6_observer_fiducial_focus_evidence",
        "failure_rule": (
            "unverified_fiducial_visibility_or_focus_targets_block_observer_readiness"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{aperture_count} apertures / {len(observer_fiducial_focus_targets)} "
            f"targets / {counts.get('observer_fiducial_disk', 0)} fiducials"
        ),
        "aperture_count": aperture_count,
        "target_count": len(observer_fiducial_focus_targets),
        "target_kind_counts": counts,
        "fiducials_per_aperture": fiducials_per_aperture,
        "fiducial_multiplicity_ok": fiducial_multiplicity_ok,
        "all_targets_within_dry_bay": all_targets_within_dry_bay,
        "fiducial_geometry_blockers": sorted(fiducial_geometry_blockers),
        "fiducial_geometry_clears": not fiducial_geometry_blockers,
        "source_layout_checks": ["observer_fiducial_focus_targets"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "observer_focus_repeatability",
            "observer_fiducial_visibility",
            "usable_imaging_quality",
        ],
        "body_targets": observer_fiducial_focus_targets,
    }


def _observer_optical_stability_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    dry_bay_apertures: list[dict[str, float | int]],
    observer_fiducial_focus_target_check: dict[str, Any],
    thermal_condensation_proxy_check: dict[str, Any],
    dry_bay_ingress_audit_rects: list[dict[str, Any]],
    wet_dry_failure_paths: dict[str, list[dict[str, float | int | str]]],
) -> dict[str, Any]:
    metrology = params.get("consumable_metrology", {})
    check_params = params.get("observer_optical_stability_check", {})
    slab_len = float(check_params.get("length_x", 56.0))
    slab_wid = float(check_params.get("width_y", 72.0))
    slab_h = float(check_params.get("height_z", 0.45))
    x0 = (
        float(layout["length_x"])
        + float(metrology.get("viewer_offset_x", 18.0))
        + float(check_params.get("viewer_offset_x", 132.0))
    )
    y0 = (float(layout["width_y"]) - slab_wid) / 2

    target_kind_counts = observer_fiducial_focus_target_check["target_kind_counts"]
    proxy_kind_counts = thermal_condensation_proxy_check["proxy_kind_counts"]

    checkpoints = [
        {
            "name": "stray_light_blank_frame",
            "blocks": ["stray_light_background_unmeasured"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "dry_bay_ingress_audit_check",
            ],
            "inspection_method": "blank_frame_capture",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "baffle_reflection_screen",
            "blocks": ["baffle_reflection_screen_missing"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_carriage_envelope_check",
            ],
            "inspection_method": "dark_and_illuminated_field_photo",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "fiducial_visibility",
            "blocks": ["fiducial_visibility_unproven"],
            "source_validation_checks": ["observer_fiducial_focus_target_check"],
            "inspection_method": "fiducial_target_image_set",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "focus_repeatability",
            "blocks": ["focus_repeatability_unmeasured"],
            "source_validation_checks": ["observer_fiducial_focus_target_check"],
            "inspection_method": "repeat_focus_series",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "vibration_stability",
            "blocks": ["vibration_motion_blur_unmeasured"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_carriage_envelope_check",
            ],
            "inspection_method": "service_motion_image_series",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "thermal_drift",
            "blocks": ["thermal_drift_unmeasured"],
            "source_validation_checks": ["thermal_condensation_proxy_check"],
            "inspection_method": "warm_humid_focus_drift_log",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "signal_quality_baseline",
            "blocks": ["signal_quality_baseline_missing"],
            "source_validation_checks": [
                "observer_fiducial_focus_target_check",
                "thermal_condensation_proxy_check",
            ],
            "inspection_method": "baseline_noise_and_contrast_capture",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "wet_boundary_optical_contamination",
            "blocks": ["wet_boundary_optical_contamination_unchecked"],
            "source_validation_checks": [
                "wet_dry_failure_path_check",
                "dry_bay_ingress_audit_check",
            ],
            "inspection_method": "post_warm_humid_dry_bay_inspection",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
    ]
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

    return {
        "name": "observer_optical_stability_check",
        "role": "measured_observer_optical_performance_evidence_blocker",
        "validation": "cad_proxy_measured_observer_performance_required",
        "failure_rule": (
            "any_unproven_optical_checkpoint_blocks_observer_performance_claim"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{len(checkpoints)} checks / {len(dry_bay_apertures)} apertures / "
            f"{observer_fiducial_focus_target_check['target_count']} targets"
        ),
        "aperture_count": len(dry_bay_apertures),
        "fiducial_focus_target_count": observer_fiducial_focus_target_check[
            "target_count"
        ],
        "target_kind_counts": target_kind_counts,
        "thermal_proxy_count": thermal_condensation_proxy_check["target_count"],
        "thermal_proxy_kind_counts": proxy_kind_counts,
        "dry_bay_ingress_audit_rect_count": len(dry_bay_ingress_audit_rects),
        "wet_dry_witness_gutter_count": len(
            wet_dry_failure_paths["wet_dry_witness_gutters"]
        ),
        "checkpoints": checkpoints,
        "checkpoint_count": len(checkpoints),
        "blockers": blockers,
        "source_validation_checks": source_validation_checks,
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "usable_imaging_quality",
            "raman_signal_quality",
            "biophotonics_signal_quality",
            "focus_repeatability",
            "vibration_stability",
        ],
        "body_rects": [
            {
                "name": "observer_optical_stability_evidence_slab",
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": 0.0,
                "length_x": round(slab_len, 3),
                "width_y": round(slab_wid, 3),
                "height_z": round(slab_h, 3),
            }
        ],
    }


def _observer_kinematic_split_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    observer_front_end_swept_body_check: dict[str, Any],
    observer_carriage_envelope_check: dict[str, Any],
    observer_service_raceway_envelope_check: dict[str, Any],
    dry_bay_envelope: dict[str, Any],
    observer_fiducial_focus_targets: list[dict[str, float | int | str]],
) -> dict[str, Any]:
    metrology = params.get("consumable_metrology", {})
    check_params = params.get("observer_kinematic_split_check", {})
    slab_len = float(check_params.get("length_x", 58.0))
    slab_wid = float(check_params.get("width_y", 78.0))
    slab_h = float(check_params.get("height_z", 0.45))
    x0 = (
        float(layout["length_x"])
        + float(metrology.get("viewer_offset_x", 18.0))
        + float(check_params.get("viewer_offset_x", 214.0))
    )
    y0 = (float(layout["width_y"]) - slab_wid) / 2

    source_validation_checks = [
        "observer_front_end_swept_body_check",
        "observer_carriage_envelope_check",
        "observer_service_raceway_envelope_check",
        "observer_fiducial_focus_target_check",
        "dry_bay_envelope_check",
    ]
    checkpoints = [
        {
            "name": "front_end_decoupled_from_carriage",
            "blocks": ["single_large_objective_centered_carriage_unacceptable"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_carriage_envelope_check",
            ],
            "inspection_method": "observer_split_layout_review",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "focus_axis_reaches_all_plate_positions",
            "blocks": ["focus_axis_travel_or_recovery_unproven"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_fiducial_focus_target_check",
            ],
            "inspection_method": "all_tile_focus_travel_check",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "carriage_stays_out_of_objective_centered_sweep",
            "blocks": ["carriage_treated_as_objective_centered_body"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_carriage_envelope_check",
            ],
            "inspection_method": "dry_bay_carriage_offset_review",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "service_loop_recovers_inside_raceway",
            "blocks": ["observer_service_loop_recovery_unproven"],
            "source_validation_checks": [
                "observer_service_raceway_envelope_check",
                "dry_bay_envelope_check",
            ],
            "inspection_method": "five_cycle_service_loop_recovery",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "install_remove_preserves_dry_bay_clearance",
            "blocks": ["observer_install_remove_snag_or_debris_unchecked"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_service_raceway_envelope_check",
                "dry_bay_envelope_check",
            ],
            "inspection_method": "post_cycle_dry_bay_clearance_inspection",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
    ]
    blocker_set = {
        block
        for checkpoint in checkpoints
        for block in checkpoint["blocks"]
    }
    carriage_traverse = observer_carriage_envelope_check.get("carriage_traverse", {})
    # Fail closed: absent traverse evidence must not silently read as a clear
    # path for a Gate-6 blocker.
    carriage_traverse_fits = bool(carriage_traverse.get("fits_dry_bay", False))
    carriage_traverse_clears = bool(carriage_traverse.get("clears_traverse", False))
    if not carriage_traverse_fits:
        # The carriage swept across the full row overflows the reserved dry-bay
        # envelope; until the gantry is physically built and shown to traverse,
        # this blocks Gate 6.
        blocker_set.add("carriage_traverse_exceeds_dry_bay")
    if carriage_traverse.get("hits_deck_feet", False):
        blocker_set.add("carriage_traverse_hits_deck_feet")
    if carriage_traverse.get("enters_adjacent_slot", False):
        blocker_set.add("carriage_traverse_enters_adjacent_slot")
    blockers = sorted(blocker_set)
    return {
        "name": "observer_kinematic_split_check",
        "role": "validation-only observer kinematic split evidence checklist",
        "validation": "required_gate6_observer_kinematic_split_evidence",
        "failure_rule": (
            "unproven_front_end_carriage_or_service_split_blocks_observer_readiness"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{len(checkpoints)} checks / 3 split envelopes / "
            f"{len(observer_fiducial_focus_targets)} targets"
        ),
        "checkpoint_count": len(checkpoints),
        "source_validation_checks": source_validation_checks,
        "blockers": blockers,
        "carriage_traverse_fits_dry_bay": carriage_traverse_fits,
        "carriage_traverse_clears": carriage_traverse_clears,
        "carriage_traverse_overflow_mm": {
            "x": round(float(carriage_traverse.get("dry_bay_overflow_x_mm", 0.0)), 2),
            "y": round(float(carriage_traverse.get("dry_bay_overflow_y_mm", 0.0)), 2),
        },
        "carriage_traverse_collisions": {
            "deck_feet": int(carriage_traverse.get("deck_foot_collision_count", 0)),
            "adjacent_slots": int(
                carriage_traverse.get("adjacent_slot_collision_count", 0)
            ),
        },
        "front_end_bounds_mm": {
            "x": round(float(observer_front_end_swept_body_check["length_x"]), 2),
            "y": round(float(observer_front_end_swept_body_check["width_y"]), 2),
            "z": round(float(observer_front_end_swept_body_check["height_z"]), 2),
        },
        "carriage_bounds_mm": {
            "x": round(float(observer_carriage_envelope_check["length_x"]), 2),
            "y": round(float(observer_carriage_envelope_check["width_y"]), 2),
            "z": round(float(observer_carriage_envelope_check["height_z"]), 2),
        },
        "raceway_bounds_mm": {
            "x": round(float(observer_service_raceway_envelope_check["length_x"]), 2),
            "y": round(float(observer_service_raceway_envelope_check["width_y"]), 2),
            "z": round(float(observer_service_raceway_envelope_check["height_z"]), 2),
        },
        "dry_bay_bounds_mm": {
            "x": round(float(dry_bay_envelope["length_x"]), 2),
            "y": round(float(dry_bay_envelope["width_y"]), 2),
            "z": round(
                float(dry_bay_envelope["top_z"])
                - float(dry_bay_envelope["bottom_z"]),
                2,
            ),
        },
        "requires_physical_evidence": True,
        "all_checkpoints_block_gate6_pass": True,
        "physical_claims_blocked": [
            "observer_kinematic_split",
            "objective_centered_access",
            "focus_axis_recovery",
            "service_loop_recovery",
            "observer_install_remove_clearance",
        ],
        "body_rects": [
            {
                "name": "observer_kinematic_split_evidence_slab",
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": 0.0,
                "length_x": round(slab_len, 3),
                "width_y": round(slab_wid, 3),
                "height_z": round(slab_h, 3),
            }
        ],
    }


def _headspace_barrier_check(
    wet_chamber_skirt: dict[str, Any],
    *,
    seal: dict[str, Any],
    plate_top_z: float,
) -> dict[str, Any]:
    x0 = float(wet_chamber_skirt["x"])
    y0 = float(wet_chamber_skirt["y"])
    length = float(wet_chamber_skirt["length_x"])
    width = float(wet_chamber_skirt["width_y"])
    rail_w = float(seal["chamber_wall_thickness"])
    height = float(seal["compressed_gasket_height_z"]) + float(
        seal["headspace_recess_depth_z"]
    )
    body_rects = [
        {
            "name": "headspace_barrier_front_rail",
            "x": round(x0, 3),
            "y": round(y0, 3),
            "z": round(plate_top_z, 3),
            "length_x": round(length, 3),
            "width_y": round(rail_w, 3),
            "height_z": round(height, 3),
        },
        {
            "name": "headspace_barrier_rear_rail",
            "x": round(x0, 3),
            "y": round(y0 + width - rail_w, 3),
            "z": round(plate_top_z, 3),
            "length_x": round(length, 3),
            "width_y": round(rail_w, 3),
            "height_z": round(height, 3),
        },
        {
            "name": "headspace_barrier_left_rail",
            "x": round(x0, 3),
            "y": round(y0 + rail_w, 3),
            "z": round(plate_top_z, 3),
            "length_x": round(rail_w, 3),
            "width_y": round(width - 2 * rail_w, 3),
            "height_z": round(height, 3),
        },
        {
            "name": "headspace_barrier_right_rail",
            "x": round(x0 + length - rail_w, 3),
            "y": round(y0 + rail_w, 3),
            "z": round(plate_top_z, 3),
            "length_x": round(rail_w, 3),
            "width_y": round(width - 2 * rail_w, 3),
            "height_z": round(height, 3),
        },
    ]
    return {
        "name": "headspace_barrier_check",
        "role": "shared_wet_headspace_barrier_perimeter_validation_body",
        "validation": "required_gate4_headspace_barrier_evidence",
        "failure_rule": "sealed_perimeter_leak_or_bypass_blocks_wet_dry_pass",
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{length:.2f} x {width:.2f} x {height:.2f} mm perimeter, "
            f"{rail_w:.2f} mm wall"
        ),
        "length_x": round(length, 3),
        "width_y": round(width, 3),
        "height_z": round(height, 3),
        "wall_width": round(rail_w, 3),
        "source_layout_checks": ["wet_chamber_skirt"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "sealed_wet_headspace_perimeter",
            "wet_operation_without_headspace_bypass",
            "wet_operation_without_external_leak",
        ],
        "body_rects": body_rects,
    }


def _headspace_volume_check(
    wet_chamber_skirt: dict[str, Any],
    *,
    seal: dict[str, Any],
    plate_top_z: float,
) -> dict[str, Any]:
    rail_w = float(seal["gasket_rail_width"])
    height = float(seal["compressed_gasket_height_z"]) + float(
        seal["headspace_recess_depth_z"]
    )
    length = float(wet_chamber_skirt["length_x"]) - 2 * rail_w
    width = float(wet_chamber_skirt["width_y"]) - 2 * rail_w
    body_rects = [
        {
            "name": "shared_wet_headspace_volume",
            "x": round(float(wet_chamber_skirt["x"]) + rail_w, 3),
            "y": round(float(wet_chamber_skirt["y"]) + rail_w, 3),
            "z": round(plate_top_z, 3),
            "length_x": round(length, 3),
            "width_y": round(width, 3),
            "height_z": round(height, 3),
        }
    ]
    return {
        "name": "headspace_volume_check",
        "role": "shared_wet_headspace_volume_validation_body",
        "validation": "required_gate4_shared_headspace_volume_evidence",
        "failure_rule": (
            "blocked_bridged_or_discontinuous_shared_headspace_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": f"{length:.2f} x {width:.2f} x {height:.2f} mm shared volume",
        "length_x": round(length, 3),
        "width_y": round(width, 3),
        "height_z": round(height, 3),
        "source_layout_checks": ["wet_chamber_skirt"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "shared_wet_headspace_continuity",
            "wet_operation_with_all_plates_in_one_headspace",
            "sealed_row_volume_without_blocked_bridges",
        ],
        "body_rects": body_rects,
    }


def _dry_bay_envelope_check(
    dry_bay_envelope: dict[str, Any],
) -> dict[str, Any]:
    height = float(dry_bay_envelope["top_z"]) - float(dry_bay_envelope["bottom_z"])
    body_rects = [
        {
            "name": "protected_dry_observer_bay_volume",
            "x": dry_bay_envelope["x"],
            "y": dry_bay_envelope["y"],
            "z": dry_bay_envelope["bottom_z"],
            "length_x": dry_bay_envelope["length_x"],
            "width_y": dry_bay_envelope["width_y"],
            "height_z": round(height, 3),
        }
    ]
    return {
        "name": "dry_bay_envelope_check",
        "role": "protected_dry_observer_bay_volume_validation_body",
        "validation": "required_gate4_dry_bay_protected_volume_evidence",
        "failure_rule": (
            "dye_condensate_debris_or_service_lead_inside_dry_bay_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{float(dry_bay_envelope['length_x']):.2f} x "
            f"{float(dry_bay_envelope['width_y']):.2f} x {height:.2f} mm"
        ),
        "length_x": dry_bay_envelope["length_x"],
        "width_y": dry_bay_envelope["width_y"],
        "height_z": round(height, 3),
        "source_layout_checks": ["dry_bay_envelope"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "dry_observer_bay_reserved",
            "wet_operation_without_dry_bay_ingress",
            "dry_observer_clearance_after_wet_exposure",
        ],
        "body_rects": body_rects,
    }


def _dry_bay_boundary_check(
    dry_bay_envelope: dict[str, Any],
    *,
    params: dict[str, Any],
    row_axis: str,
) -> dict[str, Any]:
    bay = params["dry_bay"]
    rail_w = float(bay["boundary_rail_width_y"])
    rail_h = float(bay["boundary_rail_height_z"])
    rail_clearance = float(bay["boundary_rail_clearance_y"])
    ref_x = float(dry_bay_envelope["x"])
    ref_y = float(dry_bay_envelope["y"])
    ref_len = float(dry_bay_envelope["length_x"])
    ref_wid = float(dry_bay_envelope["width_y"])
    if row_axis == "x":
        body_rects = [
            {
                "name": "dry_bay_front_boundary_clearance_rail",
                "x": round(ref_x, 3),
                "y": round(ref_y - rail_clearance - rail_w, 3),
                "z": round(-rail_h, 3),
                "length_x": round(ref_len, 3),
                "width_y": round(rail_w, 3),
                "height_z": round(rail_h, 3),
            },
            {
                "name": "dry_bay_rear_boundary_clearance_rail",
                "x": round(ref_x, 3),
                "y": round(ref_y + ref_wid + rail_clearance, 3),
                "z": round(-rail_h, 3),
                "length_x": round(ref_len, 3),
                "width_y": round(rail_w, 3),
                "height_z": round(rail_h, 3),
            },
        ]
        boundary_length_x = ref_len
        boundary_width_y = ref_wid + 2 * (rail_clearance + rail_w)
    else:
        body_rects = [
            {
                "name": "dry_bay_left_boundary_clearance_rail",
                "x": round(ref_x - rail_clearance - rail_w, 3),
                "y": round(ref_y, 3),
                "z": round(-rail_h, 3),
                "length_x": round(rail_w, 3),
                "width_y": round(ref_wid, 3),
                "height_z": round(rail_h, 3),
            },
            {
                "name": "dry_bay_right_boundary_clearance_rail",
                "x": round(ref_x + ref_len + rail_clearance, 3),
                "y": round(ref_y, 3),
                "z": round(-rail_h, 3),
                "length_x": round(rail_w, 3),
                "width_y": round(ref_wid, 3),
                "height_z": round(rail_h, 3),
            },
        ]
        boundary_length_x = ref_len + 2 * (rail_clearance + rail_w)
        boundary_width_y = ref_wid
    return {
        "name": "dry_bay_boundary_check",
        "role": "dry_bay_boundary_rail_clearance_validation_body",
        "validation": "required_gate4_dry_bay_boundary_clearance_evidence",
        "failure_rule": (
            "boundary_rail_interference_or_debris_bridge_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{boundary_length_x:.2f} x {boundary_width_y:.2f} x "
            f"{rail_h:.2f} mm, {rail_w:.2f} mm rails"
        ),
        "length_x": round(boundary_length_x, 3),
        "width_y": round(boundary_width_y, 3),
        "height_z": round(rail_h, 3),
        "rail_width": round(rail_w, 3),
        "source_layout_checks": ["dry_bay_envelope"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "dry_bay_boundary_clearance",
            "observer_service_loop_clearance",
            "wet_operation_without_boundary_debris_bridge",
        ],
        "body_rects": body_rects,
    }


def _wet_dry_failure_path_geometry(
    *,
    apertures: list[dict[str, float | int]],
    params: dict[str, Any],
    base_top_z: float,
) -> dict[str, list[dict[str, float | int | str]]]:
    production = params.get("production_assembly", {})
    threshold_w = production.get("dry_bay_threshold_width_xy", 0.0)
    threshold_h = production.get("dry_bay_threshold_height_z", 0.0)
    gutter_w = production.get("wet_dry_witness_gutter_width_xy", 0.0)
    gutter_d = production.get("wet_dry_witness_gutter_depth_z", 0.0)
    gutter_gap = production.get("wet_dry_witness_gutter_gap_xy", 0.0)

    thresholds: list[dict[str, float | int | str]] = []
    gutters: list[dict[str, float | int | str]] = []
    for aperture in apertures:
        aperture_x = float(aperture["x"])
        aperture_y = float(aperture["y"])
        aperture_len = float(aperture["length_x"])
        aperture_wid = float(aperture["width_y"])
        tile_x = float(aperture["tile_x"])
        tile_len = float(aperture["tile_length_x"])
        tile_xmax = tile_x + tile_len

        if threshold_w > 0 and threshold_h > 0:
            thresholds.append(
                {
                    "tile_index": aperture["tile_index"],
                    "x": round(aperture_x - threshold_w, 3),
                    "y": round(aperture_y - threshold_w, 3),
                    "length_x": round(aperture_len + 2 * threshold_w, 3),
                    "width_y": round(aperture_wid + 2 * threshold_w, 3),
                    "rail_width": round(threshold_w, 3),
                    "height_z": round(threshold_h, 3),
                    "z": round(base_top_z, 3),
                    "inner_x": aperture["x"],
                    "inner_y": aperture["y"],
                    "inner_length_x": aperture["length_x"],
                    "inner_width_y": aperture["width_y"],
                }
            )

        if gutter_w > 0 and gutter_d > 0:
            gutter_y = aperture_y - threshold_w
            gutter_width_y = aperture_wid + 2 * threshold_w
            candidates = [
                (
                    "min_x",
                    aperture_x - threshold_w - gutter_gap - gutter_w,
                ),
                (
                    "max_x",
                    aperture_x + aperture_len + threshold_w + gutter_gap,
                ),
            ]
            for side, gutter_x in candidates:
                if gutter_x < tile_x or gutter_x + gutter_w > tile_xmax:
                    continue
                gutters.append(
                    {
                        "tile_index": aperture["tile_index"],
                        "side": side,
                        "x": round(gutter_x, 3),
                        "y": round(gutter_y, 3),
                        "length_x": round(gutter_w, 3),
                        "width_y": round(gutter_width_y, 3),
                        "depth_z": round(gutter_d, 3),
                        "z": round(base_top_z - gutter_d, 3),
                    }
                )
    return {
        "dry_bay_aperture_thresholds": thresholds,
        "wet_dry_witness_gutters": gutters,
    }


def _wet_dry_failure_path_check(
    wet_dry_failure_paths: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    gutters = wet_dry_failure_paths["wet_dry_witness_gutters"]
    thresholds = wet_dry_failure_paths["dry_bay_aperture_thresholds"]
    body_rects = [
        {
            **gutter,
            "height_z": round(float(gutter["depth_z"]), 3),
        }
        for gutter in gutters
    ]
    gutter_depth = float(gutters[0]["depth_z"]) if gutters else 0.0
    return {
        "name": "wet_dry_failure_path_check",
        "role": "aperture_local_wet_dry_witness_gutter_validation_body",
        "validation": "required_gate4_aperture_wet_dry_failure_path_evidence",
        "failure_rule": (
            "aperture_leak_bridge_or_unmeasured_gutter_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{len(gutters)} gutters / {len(thresholds)} raised thresholds / "
            f"{gutter_depth:.2f} mm gutter depth"
        ),
        "gutter_cad_value": f"{len(gutters)} gutters, {gutter_depth:.2f} mm depth",
        "threshold_cad_value": f"{len(thresholds)} raised thresholds",
        "gutter_count": len(gutters),
        "threshold_count": len(thresholds),
        "gutter_depth_z": round(gutter_depth, 3),
        "source_layout_checks": ["wet_dry_failure_paths"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "dry_observer_bay_protected_from_aperture_leaks",
            "wet_operation_without_optics_ingress",
            "powered_sensor_thermal_readiness_after_wet_exposure",
        ],
        "body_rects": body_rects,
        "threshold_rects": thresholds,
    }


def _sample_relief_leak_witness_check(
    witnesses: list[dict[str, Any]],
) -> dict[str, Any]:
    wet_collectors = [
        rect
        for witness in witnesses
        for rect in (witness["shelf_rect"], witness["gutter_rect"])
    ]
    inboard_dams = [witness["threshold_rect"] for witness in witnesses]
    body_rects = [*wet_collectors, *inboard_dams]
    return {
        "name": "sample_relief_leak_witness_check",
        "role": "sample_relief_cap_wet_failure_witness_validation_body",
        "validation": "required_gate4_sample_relief_leak_witness_evidence",
        "failure_rule": (
            "sample_relief_leak_without_visible_witness_or_dam_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{len(wet_collectors)} wet collectors / {len(inboard_dams)} inboard dams"
        ),
        "wet_collector_count": len(wet_collectors),
        "inboard_dam_count": len(inboard_dams),
        "witness_count": len(witnesses),
        "source_layout_checks": ["sample_relief_leak_witnesses"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "sample_relief_cap_seat_does_not_bridge_to_dry_bay",
            "wet_operation_with_sample_relief_cap_installed",
            "dry_bay_protection_from_top_cap_leaks",
        ],
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


def _dry_bay_ingress_audit_rectangles(
    *,
    dry_bay_envelope: dict[str, Any],
    side_gas_service_interfaces: list[dict[str, Any]],
    sample_relief_leak_witnesses: list[dict[str, Any]],
    gasket_tab_leak_witnesses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    audit_rects: list[dict[str, Any]] = [
        {
            "name": "dry_bay_protected_footprint",
            "x": dry_bay_envelope["x"],
            "y": dry_bay_envelope["y"],
            "z": dry_bay_envelope["bottom_z"],
            "length_x": dry_bay_envelope["length_x"],
            "width_y": dry_bay_envelope["width_y"],
            "height_z": round(
                float(dry_bay_envelope["top_z"]) - float(dry_bay_envelope["bottom_z"]),
                3,
            ),
            "audit_role": "protected_dry_bay_footprint",
            "source_group": "dry_bay",
            "dry_bay_relation": "protected_volume_not_wet_source",
        }
    ]

    def add_rect(
        *,
        rect: dict[str, Any],
        name: str,
        source_group: str,
        audit_role: str,
        dry_bay_relation: str,
        source_role: str,
    ) -> None:
        audit_rects.append(
            {
                "name": name,
                "x": rect["x"],
                "y": rect["y"],
                "z": rect["z"],
                "length_x": rect["length_x"],
                "width_y": rect["width_y"],
                "height_z": rect["height_z"],
                "audit_role": audit_role,
                "source_group": source_group,
                "source_role": source_role,
                "dry_bay_relation": dry_bay_relation,
            }
        )

    for interface in side_gas_service_interfaces:
        role = interface["role"]
        for idx, rect in enumerate(interface["leak_witness_gutter_rects"], start=1):
            add_rect(
                rect=rect,
                name=f"{role}_side_gas_wet_collector_{idx}",
                source_group="side_gas_service",
                audit_role="wet_collection",
                dry_bay_relation="outside_protected_footprint",
                source_role=role,
            )
        for idx, rect in enumerate(interface["leak_witness_threshold_rects"], start=1):
            add_rect(
                rect=rect,
                name=f"{role}_side_gas_inboard_dam_{idx}",
                source_group="side_gas_service",
                audit_role="inboard_dam",
                dry_bay_relation="barrier_at_protected_margin",
                source_role=role,
            )

    for witness in sample_relief_leak_witnesses:
        add_rect(
            rect=witness["shelf_rect"],
            name=f"{witness['name']}_wet_shelf",
            source_group="sample_relief_cap",
            audit_role="wet_collection",
            dry_bay_relation="outside_protected_footprint",
            source_role=witness["port_role"],
        )
        add_rect(
            rect=witness["gutter_rect"],
            name=f"{witness['name']}_wet_gutter",
            source_group="sample_relief_cap",
            audit_role="wet_collection",
            dry_bay_relation="outside_protected_footprint",
            source_role=witness["port_role"],
        )
        add_rect(
            rect=witness["threshold_rect"],
            name=f"{witness['name']}_inboard_dam",
            source_group="sample_relief_cap",
            audit_role="inboard_dam",
            dry_bay_relation="barrier_at_protected_margin",
            source_role=witness["port_role"],
        )

    for witness in gasket_tab_leak_witnesses:
        source_role = f"{witness['layer']}_{witness['side']}"
        add_rect(
            rect=witness["gutter_rect"],
            name=f"{witness['name']}_wet_gutter",
            source_group="gasket_tab_root",
            audit_role="wet_collection",
            dry_bay_relation="outside_protected_footprint",
            source_role=source_role,
        )
        add_rect(
            rect=witness["threshold_rect"],
            name=f"{witness['name']}_inboard_dam",
            source_group="gasket_tab_root",
            audit_role="inboard_dam",
            dry_bay_relation="barrier_at_protected_margin",
            source_role=source_role,
        )

    return audit_rects


def _dry_bay_ingress_audit_check(
    audit_rects: list[dict[str, Any]],
) -> dict[str, Any]:
    protected_count = sum(
        1 for rect in audit_rects if rect["audit_role"] == "protected_dry_bay_footprint"
    )
    wet_collector_count = sum(
        1 for rect in audit_rects if rect["audit_role"] == "wet_collection"
    )
    inboard_dam_count = sum(1 for rect in audit_rects if rect["audit_role"] == "inboard_dam")
    source_groups = tuple(
        sorted(
            {
                str(rect["source_group"])
                for rect in audit_rects
                if rect["source_group"] != "dry_bay"
            }
        )
    )
    return {
        "name": "dry_bay_ingress_audit_check",
        "role": "dry_bay_external_wet_source_ingress_audit_validation_body",
        "validation": "required_gate4_dry_bay_ingress_audit_evidence",
        "failure_rule": (
            "wet_source_bridge_or_unprotected_dry_bay_path_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{wet_collector_count} wet collectors / {inboard_dam_count} inboard dams / "
            f"{protected_count} protected footprint"
        ),
        "wet_collector_count": wet_collector_count,
        "inboard_dam_count": inboard_dam_count,
        "protected_footprint_count": protected_count,
        "source_groups": source_groups,
        "source_layout_checks": [
            "side_gas_leak_witness_check",
            "sample_relief_leak_witness_check",
            "gasket_tab_leak_witness_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "wet_operation_without_dry_bay_ingress",
            "dry_observer_clearance_after_wet_exposure",
            "sensor_electronics_protected_from_external_wet_sources",
        ],
        "body_rects": audit_rects,
    }


def _add_dry_bay_aperture_thresholds(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    for threshold in layout["wet_dry_failure_paths"]["dry_bay_aperture_thresholds"]:
        model = model.union(
            _perimeter_rails(
                x0=float(threshold["x"]),
                y0=float(threshold["y"]),
                length=float(threshold["length_x"]),
                width=float(threshold["width_y"]),
                rail_width=float(threshold["rail_width"]),
                height=float(threshold["height_z"]),
                z0=float(threshold["z"]),
            )
        )
    return model


def _cut_wet_dry_witness_gutters(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    for gutter in layout["wet_dry_failure_paths"]["wet_dry_witness_gutters"]:
        depth = float(gutter["depth_z"])
        model = model.cut(
            cq.Workplane("XY")
            .box(
                float(gutter["length_x"]),
                float(gutter["width_y"]),
                depth + 0.05,
                centered=(False, False, False),
            )
            .translate((float(gutter["x"]), float(gutter["y"]), float(gutter["z"])))
        )
    return model


def _cut_dry_bay(
    model: cq.Workplane,
    *,
    x0: float,
    y0: float,
    plate_len: float,
    plate_wid: float,
    base_h: float,
    land_h: float,
    bay: dict[str, Any],
) -> cq.Workplane:
    aperture_x = x0 + (plate_len - bay["aperture_length_x"]) / 2
    aperture_y = y0 + (plate_wid - bay["aperture_width_y"]) / 2
    aperture_center_x = aperture_x + bay["aperture_length_x"] / 2
    aperture_center_y = aperture_y + bay["aperture_width_y"] / 2

    model = model.cut(
        cq.Workplane("XY")
        .box(
            bay["aperture_length_x"],
            bay["aperture_width_y"],
            base_h + land_h + 0.4,
            centered=(False, False, False),
        )
        .translate((aperture_x, aperture_y, -0.2))
    )
    model = model.cut(
        cq.Workplane("XY")
        .box(
            bay["aperture_length_x"] + bay["bottom_recess_extra"],
            bay["aperture_width_y"] + bay["bottom_recess_extra"],
            bay["bottom_recess_depth"] + 0.02,
            centered=(True, True, False),
        )
        .translate((aperture_center_x, aperture_center_y, -0.01))
    )
    model = model.cut(
        cq.Workplane("XY")
        .circle(bay["objective_keepout_diameter"] / 2)
        .extrude(bay["bottom_recess_depth"] + 0.02)
        .translate((aperture_center_x, aperture_center_y, -0.01))
    )
    model = model.cut(
        cq.Workplane("XY")
        .box(
            bay["crosshair_length"],
            bay["crosshair_width"],
            bay["bottom_recess_depth"] + 0.02,
            centered=(True, True, False),
        )
        .translate((aperture_center_x, aperture_center_y, -0.01))
    )
    return model.cut(
        cq.Workplane("XY")
        .box(
            bay["crosshair_width"],
            bay["crosshair_length"],
            bay["bottom_recess_depth"] + 0.02,
            centered=(True, True, False),
        )
        .translate((aperture_center_x, aperture_center_y, -0.01))
    )


def _cut_observer_fiducials(
    model: cq.Workplane,
    *,
    x0: float,
    y0: float,
    plate_len: float,
    plate_wid: float,
    bay: dict[str, Any],
) -> cq.Workplane:
    diameter = bay["observer_fiducial_diameter"]
    depth = bay["observer_fiducial_depth"]
    offset = bay["observer_fiducial_offset"]
    aperture_x = x0 + (plate_len - bay["aperture_length_x"]) / 2
    aperture_y = y0 + (plate_wid - bay["aperture_width_y"]) / 2
    x_values = [
        aperture_x - offset,
        aperture_x + bay["aperture_length_x"] + offset,
    ]
    y_values = [
        aperture_y - offset,
        aperture_y + bay["aperture_width_y"] + offset,
    ]

    for x in x_values:
        for y in y_values:
            model = model.cut(
                cq.Workplane("XY")
                .circle(diameter / 2)
                .extrude(depth + 0.05)
                .translate((x, y, -0.01))
            )
    return model


def _cut_locator_relief(
    model: cq.Workplane,
    *,
    x0: float,
    y0: float,
    plate_len: float,
    support: dict[str, Any],
    z: float,
) -> cq.Workplane:
    relief = support["locator_relief_width"]
    depth = support["locator_relief_depth"]
    for x in [x0 + relief, x0 + plate_len - relief]:
        model = model.cut(
            cq.Workplane("XY")
            .box(relief, relief, depth + 0.05, centered=(True, True, False))
            .translate((x, y0 + relief, z))
        )
    return model


def _cut_plate_observation_recess(
    part: cq.Workplane,
    x0: float,
    y0: float,
    plate: dict[str, Any],
    z: float,
) -> cq.Workplane:
    return part.cut(
        cq.Workplane("XY")
        .box(
            plate["observation_window_length_x"],
            plate["observation_window_width_y"],
            0.45,
            centered=(True, True, False),
        )
        .translate((x0 + plate["length_x"] / 2, y0 + plate["width_y"] / 2, z))
    )


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
