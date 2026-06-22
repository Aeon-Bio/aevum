from __future__ import annotations
from typing import Any


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
