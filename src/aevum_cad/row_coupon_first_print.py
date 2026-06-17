from __future__ import annotations

import configparser
import csv
import math
import subprocess
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from io import StringIO
from pathlib import Path
from shutil import copy2
from typing import Any

from aevum_cad.row_coupon import (
    ROW_COUPON_SERVICE_MODES,
    build_row_coupon_installed_parts,
    build_row_coupon_production_y_split_parts,
    build_row_coupon_service_parts,
    build_row_coupon_service_parts_from_installed,
    row_coupon_layout,
    row_coupon_part_manifest,
    row_coupon_production_y_split_plan,
)

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

FIRST_PRINT_GATE1_QC_FIELDNAMES = (
    "part",
    "source",
    "target_x_mm",
    "target_y_mm",
    "target_z_mm",
    "measured_x_mm",
    "measured_y_mm",
    "measured_z_mm",
    "evidence_path",
    "result",
    "notes",
)

FIRST_PRINT_GATE1_QC_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM = 1.0

FIRST_PRINT_GATE2_DRY_ASSEMBLY_FIELDNAMES = (
    "target",
    "cad_value",
    "physical_check",
    "measured_value",
    "evidence_path",
    "result",
    "notes",
)

FIRST_PRINT_GATE2_DRY_ASSEMBLY_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

FIRST_PRINT_GATE3_PLACEMENT_FIELDNAMES = (
    "target",
    "cad_value",
    "physical_check",
    "measured_value",
    "evidence_path",
    "result",
    "notes",
)

FIRST_PRINT_GATE3_PLACEMENT_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

FIRST_PRINT_GATE4_WET_DRY_WITNESS_FIELDNAMES = (
    "target",
    "cad_value",
    "physical_check",
    "measured_value",
    "evidence_path",
    "result",
    "notes",
)

FIRST_PRINT_GATE4_WET_DRY_WITNESS_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

FIRST_PRINT_GATE5_CONSUMABLE_PUNCTURE_FIELDNAMES = (
    "target",
    "cad_value",
    "physical_check",
    "measured_value",
    "evidence_path",
    "result",
    "notes",
)

FIRST_PRINT_GATE5_CONSUMABLE_PUNCTURE_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

FIRST_PRINT_GATE6_SENSOR_THERMAL_FIELDNAMES = (
    "target",
    "cad_value",
    "physical_check",
    "measured_value",
    "evidence_path",
    "result",
    "notes",
)

FIRST_PRINT_GATE6_SENSOR_THERMAL_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

FIRST_PRINT_PUNCTURE_PLATE_SHIFT_LIMIT_MM = 0.25

FIRST_PRINT_DRY_ASSEMBLY_SERVICE_CYCLES = 5

FIRST_PRINT_INSTALL_INVENTORY_FIELDNAMES = (
    "part",
    "source",
    "role",
    "acceptable_item",
    "operating_requirement",
    "item_identifier",
    "installed_as",
    "evidence_path",
    "result",
    "notes",
)

FIRST_PRINT_INSTALL_INVENTORY_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

FIRST_PRINT_INSTALL_INVENTORY_INSTALLED_AS_VALUES = frozenset(
    {"", "real_part", "dimensional_blank", "measured_replacement"}
)

FIRST_PRINT_INSTALL_INVENTORY_CATEGORIES = frozenset(
    {"cots_consumable", "electronics_or_dimensional_blank", "service_tubing"}
)

FIRST_PRINT_SERVICE_STATE_REVIEW_FIELDNAMES = (
    "mode",
    "mode_type",
    "review_scope",
    "acceptance_gate",
    "expected_removed_parts",
    "expected_review_parts",
    "screenshot_path",
    "result",
    "notes",
)

FIRST_PRINT_SERVICE_STATE_REVIEW_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

FIRST_PRINT_SERVICE_STATE_ACCEPTANCE_GATES = {
    "installed": "preflight digital service-state review",
    "bench_sealed": "preflight digital bench-only service-state review",
    "sample_relief_flow_test": "preflight digital bench-only service-state review",
    "exploded": "preflight digital service-state review",
    "lid_off": "Gate 2 dry assembly serviceability",
    "sensor_install": "Gate 6 sensor/thermal serviceability",
    "mats_exposed": "Gate 5 consumable/puncture serviceability",
    "wet_frame_off": "Gate 4 wet/dry witness serviceability",
    "plates_removable": "Gate 5 consumable/puncture serviceability",
    "sample_relief_cap_missing": "Gate 4 wet/dry witness fail-closed inspection",
    "sample_relief_cap_unseated": "Gate 4 wet/dry witness fail-closed inspection",
    "deck_module_unseated": "Gate 3 OT-2 placement fail-closed inspection",
    "deck_pose_repeatability_unproven": (
        "Gate 3 OT-2 placement fail-closed inspection"
    ),
    "latches_unseated": "Gate 2 dry assembly fail-closed inspection",
    "septum_mats_missing": "Gate 5 consumable/puncture fail-closed inspection",
    "microplates_missing": "Gate 5 consumable/puncture fail-closed inspection",
    "perimeter_gaskets_missing": "Gate 4 wet/dry witness fail-closed inspection",
    "gas_pcbs_missing": "Gate 6 sensor/thermal fail-closed inspection",
    "gas_pcb_cartridges_unseated": "Gate 6 sensor/thermal fail-closed inspection",
    "local_sensors_missing": "Gate 6 sensor/thermal fail-closed inspection",
    "service_leads_missing": "Gate 6 sensor/thermal fail-closed inspection",
    "side_gas_tubes_unseated": "Gate 2 dry assembly fail-closed inspection",
    "electrical_connectors_unmated": "Gate 6 sensor/thermal fail-closed inspection",
    "service_dress_over_pipette_field": "Gate 3 OT-2 placement fail-closed inspection",
    "service_dress_adjacent_slot_collision": "Gate 3 OT-2 placement fail-closed inspection",
    "dry_bay_obstructed": "Gate 4 wet/dry witness fail-closed inspection",
    "assembly_debris_present": "Gate 2 dry assembly fail-closed inspection",
    "gasket_squeeze_out_of_range": "Gate 2 dry assembly fail-closed inspection",
}

FIRST_PRINT_SERVICE_STATE_SERVICE_PART_EXPECTATIONS = {
    "sample_relief_flow_test": {
        "removed_parts": ("printed_sample_relief_cap",),
        "review_parts": ("sample_relief_flow_test_adapter",),
    },
}

FIRST_PRINT_SERVICE_STATE_BOUNDS_EVIDENCE_FIELDNAMES = (
    "mode",
    "mode_type",
    "review_scope",
    "acceptance_gate",
    "part",
    "x_min_mm",
    "x_max_mm",
    "x_len_mm",
    "y_min_mm",
    "y_max_mm",
    "y_len_mm",
    "z_min_mm",
    "z_max_mm",
    "z_len_mm",
    "expected_removed_parts_absent",
    "expected_review_parts_present",
    "result",
    "notes",
)

FIRST_PRINT_INSTALL_INVENTORY_ACCEPTABLE_ITEMS = {
    "ir_thermopiles": "TO-39 IR thermopile or measured package blank",
    "lower_sensor_harness": "lower IR sensor harness assembly or mechanical harness blank",
    "lower_sensor_service_connector": (
        "row-end lower sensor connector or dimensional connector blank"
    ),
    "lower_sensor_service_cable_pigtail": "installed lower sensor service cable pigtail",
    "cots_microplates": "CellVis P96-1.5H-N plate",
    "cots_septum_mats": "Cole-Parmer 1292006 round pre-slit silicone mat",
    "headspace_sht41_microcarriers": (
        "SHT41 headspace microcarrier or dimensional carrier blank"
    ),
    "lid_sensor_harness": "lid sensor harness assembly or mechanical harness blank",
    "lid_sensor_service_connectors": (
        "row-end lid sensor service connectors or dimensional connector blanks"
    ),
    "lid_sensor_service_cable_pigtails": "installed lid sensor service cable pigtails",
    "cots_gas_service_tubes": (
        "gas service tubing matching CAD ID/OD assumption or measured replacement"
    ),
    "gas_sensor_pcbs": "gas sensor PCB cartridge or dimensionally faithful cartridge blank",
}

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

FIRST_PRINT_SLICER_SETUP_FIELDNAMES = (
    "slicer_name",
    "executable_path",
    "version",
    "printer_profile",
    "material_profile",
    "print_profile",
    "profile_source",
    "selected",
    "result",
    "notes",
)

FIRST_PRINT_SLICER_SETUP_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

FIRST_PRINT_SLICER_SETUP_SELECTED_VALUES = frozenset({"", "yes", "no"})

FIRST_PRINT_SLICED_OUTPUT_FIELDNAMES = (
    "part",
    "queued_stl_path",
    "queued_stl_sha256",
    "sliced_output_path",
    "sliced_output_sha256",
    "selected_setup_summary",
    "result",
    "notes",
)

FIRST_PRINT_SLICED_OUTPUT_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

FIRST_PRINT_SLICED_OUTPUT_SUFFIXES = frozenset({".3mf", ".bgcode", ".gcode"})

FIRST_PRINT_PRINT_BATCH_TRAVELER_FIELDNAMES = (
    "print_order",
    "part",
    "source",
    "target_x_mm",
    "target_y_mm",
    "target_z_mm",
    "queued_stl_path",
    "queued_stl_sha256",
    "sliced_output_path",
    "sliced_output_sha256",
    "selected_setup_summary",
    "gate1_qc_result",
    "print_result",
    "print_evidence_path",
    "notes",
)

FIRST_PRINT_PRINT_BATCH_TRAVELER_PRINT_RESULT_VALUES = frozenset(
    {"not_printed", "printed", "failed", "reprint", "block"}
)

FIRST_PRINT_BED_FIT_SPLIT_PLAN_FIELDNAMES = (
    "part",
    "target_x_mm",
    "target_y_mm",
    "target_z_mm",
    "selected_bed_x_mm",
    "selected_bed_y_mm",
    "fits_as_exported",
    "minimum_y_segments",
    "max_segment_y_mm",
    "segment_fits_selected_bed",
    "required_decision",
    "result",
    "notes",
)

FIRST_PRINT_BED_FIT_SPLIT_PLAN_RESULT_VALUES = frozenset(
    {"not_tested", "pass", "revise", "defer", "block"}
)

DEFAULT_PRUSA_SLICER_PATH = Path(
    "/Applications/Original Prusa Drivers/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"
)
DEFAULT_BAMBU_STUDIO_PATH = Path(
    "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
)
DEFAULT_PRUSA_CONFIG_PATH = (
    Path.home() / "Library" / "Application Support" / "PrusaSlicer" / "PrusaSlicer.ini"
)
DEFAULT_BAMBU_CONFIG_PATH = (
    Path.home()
    / "Library"
    / "Application Support"
    / "BambuStudio"
    / "BambuStudio.conf"
)


@dataclass(frozen=True)
class FirstPrintArtifact:
    name: str
    category: str
    stl_path: Path
    step_path: Path
    stl_exists: bool
    step_exists: bool
    fabrication_source: str = ""
    role: str = ""

    @property
    def missing_paths(self) -> tuple[Path, ...]:
        paths: list[Path] = []
        if not self.stl_exists:
            paths.append(self.stl_path)
        if not self.step_exists:
            paths.append(self.step_path)
        return tuple(paths)


@dataclass(frozen=True)
class FirstPrintPackageAudit:
    name: str
    out_dir: Path
    assembly_step: Path
    assembly_step_exists: bool
    production_artifacts: tuple[FirstPrintArtifact, ...]
    validation_artifacts: tuple[FirstPrintArtifact, ...]
    optional_validation_artifacts: tuple[FirstPrintArtifact, ...]

    @property
    def missing_paths(self) -> tuple[Path, ...]:
        paths: list[Path] = []
        if not self.assembly_step_exists:
            paths.append(self.assembly_step)
        for artifact in (*self.production_artifacts, *self.validation_artifacts):
            paths.extend(artifact.missing_paths)
        return tuple(paths)

    @property
    def ready(self) -> bool:
        return not self.missing_paths


@dataclass(frozen=True)
class FirstPrintQCTarget:
    name: str
    category: str
    target_x_mm: float
    target_y_mm: float
    target_z_mm: float
    role: str


@dataclass(frozen=True)
class FirstPrintGate1QCWorksheetRow:
    part: str
    source: str
    target_x_mm: float
    target_y_mm: float
    target_z_mm: float
    measured_x_mm: str = ""
    measured_y_mm: str = ""
    measured_z_mm: str = ""
    evidence_path: str = ""
    result: str = "not_tested"
    notes: str = ""


@dataclass(frozen=True)
class FirstPrintGate1QCWorksheetIssue:
    part: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate1QCWorksheetAudit:
    worksheet_path: Path
    tolerance_mm: float
    expected_row_count: int
    actual_row_count: int
    result_counts: dict[str, int]
    missing_parts: tuple[str, ...]
    extra_parts: tuple[str, ...]
    duplicate_parts: tuple[str, ...]
    issues: tuple[FirstPrintGate1QCWorksheetIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_parts
            or self.extra_parts
            or self.duplicate_parts
            or self.issues
        )

    @property
    def gate1_pass_ready(self) -> bool:
        return (
            self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
            and self.result_counts.get("pass", 0) == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintGate2DryAssemblyTarget:
    target: str
    cad_value: str
    physical_check: str


@dataclass(frozen=True)
class FirstPrintGate2DryAssemblyWorksheetRow:
    target: str
    cad_value: str
    physical_check: str
    measured_value: str = ""
    evidence_path: str = ""
    result: str = "not_tested"
    notes: str = ""


@dataclass(frozen=True)
class FirstPrintGate2DryAssemblyWorksheetIssue:
    target: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate2DryAssemblyWorksheetAudit:
    worksheet_path: Path
    expected_row_count: int
    actual_row_count: int
    result_counts: dict[str, int]
    missing_targets: tuple[str, ...]
    extra_targets: tuple[str, ...]
    duplicate_targets: tuple[str, ...]
    issues: tuple[FirstPrintGate2DryAssemblyWorksheetIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_targets
            or self.extra_targets
            or self.duplicate_targets
            or self.issues
        )

    @property
    def gate2_pass_ready(self) -> bool:
        return (
            self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
            and self.result_counts.get("pass", 0) == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintGate3PlacementTarget:
    target: str
    cad_value: str
    physical_check: str


@dataclass(frozen=True)
class FirstPrintGate3PlacementWorksheetRow:
    target: str
    cad_value: str
    physical_check: str
    measured_value: str = ""
    evidence_path: str = ""
    result: str = "not_tested"
    notes: str = ""


@dataclass(frozen=True)
class FirstPrintGate3PlacementWorksheetIssue:
    target: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate3PlacementWorksheetAudit:
    worksheet_path: Path
    expected_row_count: int
    actual_row_count: int
    result_counts: dict[str, int]
    missing_targets: tuple[str, ...]
    extra_targets: tuple[str, ...]
    duplicate_targets: tuple[str, ...]
    issues: tuple[FirstPrintGate3PlacementWorksheetIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_targets
            or self.extra_targets
            or self.duplicate_targets
            or self.issues
        )

    @property
    def gate3_pass_ready(self) -> bool:
        return (
            self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
            and self.result_counts.get("pass", 0) == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintGate4WetDryWitnessTarget:
    target: str
    cad_value: str
    physical_check: str


@dataclass(frozen=True)
class FirstPrintGate4WetDryWitnessWorksheetRow:
    target: str
    cad_value: str
    physical_check: str
    measured_value: str = ""
    evidence_path: str = ""
    result: str = "not_tested"
    notes: str = ""


@dataclass(frozen=True)
class FirstPrintGate4WetDryWitnessWorksheetIssue:
    target: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate4WetDryWitnessWorksheetAudit:
    worksheet_path: Path
    expected_row_count: int
    actual_row_count: int
    result_counts: dict[str, int]
    missing_targets: tuple[str, ...]
    extra_targets: tuple[str, ...]
    duplicate_targets: tuple[str, ...]
    issues: tuple[FirstPrintGate4WetDryWitnessWorksheetIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_targets
            or self.extra_targets
            or self.duplicate_targets
            or self.issues
        )

    @property
    def gate4_pass_ready(self) -> bool:
        return (
            self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
            and self.result_counts.get("pass", 0) == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintGate5ConsumablePunctureTarget:
    target: str
    cad_value: str
    physical_check: str


@dataclass(frozen=True)
class FirstPrintGate5ConsumablePunctureWorksheetRow:
    target: str
    cad_value: str
    physical_check: str
    measured_value: str = ""
    evidence_path: str = ""
    result: str = "not_tested"
    notes: str = ""


@dataclass(frozen=True)
class FirstPrintGate5ConsumablePunctureWorksheetIssue:
    target: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate5ConsumablePunctureWorksheetAudit:
    worksheet_path: Path
    expected_row_count: int
    actual_row_count: int
    result_counts: dict[str, int]
    missing_targets: tuple[str, ...]
    extra_targets: tuple[str, ...]
    duplicate_targets: tuple[str, ...]
    issues: tuple[FirstPrintGate5ConsumablePunctureWorksheetIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_targets
            or self.extra_targets
            or self.duplicate_targets
            or self.issues
        )

    @property
    def gate5_pass_ready(self) -> bool:
        return (
            self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
            and self.result_counts.get("pass", 0) == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintGate6SensorThermalTarget:
    target: str
    cad_value: str
    physical_check: str


@dataclass(frozen=True)
class FirstPrintGate6SensorThermalWorksheetRow:
    target: str
    cad_value: str
    physical_check: str
    measured_value: str = ""
    evidence_path: str = ""
    result: str = "not_tested"
    notes: str = ""


@dataclass(frozen=True)
class FirstPrintGate6SensorThermalWorksheetIssue:
    target: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate6SensorThermalWorksheetAudit:
    worksheet_path: Path
    expected_row_count: int
    actual_row_count: int
    result_counts: dict[str, int]
    missing_targets: tuple[str, ...]
    extra_targets: tuple[str, ...]
    duplicate_targets: tuple[str, ...]
    issues: tuple[FirstPrintGate6SensorThermalWorksheetIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_targets
            or self.extra_targets
            or self.duplicate_targets
            or self.issues
        )

    @property
    def gate6_pass_ready(self) -> bool:
        return (
            self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
            and self.result_counts.get("pass", 0) == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintInstallInventoryRow:
    part: str
    source: str
    role: str
    acceptable_item: str
    operating_requirement: str
    item_identifier: str = ""
    installed_as: str = ""
    evidence_path: str = ""
    result: str = "not_tested"
    notes: str = ""


@dataclass(frozen=True)
class FirstPrintInstallInventoryIssue:
    part: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintInstallInventoryAudit:
    worksheet_path: Path
    expected_row_count: int
    actual_row_count: int
    result_counts: dict[str, int]
    missing_parts: tuple[str, ...]
    extra_parts: tuple[str, ...]
    duplicate_parts: tuple[str, ...]
    sensor_inventory_blank_parts: tuple[str, ...]
    issues: tuple[FirstPrintInstallInventoryIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_parts
            or self.extra_parts
            or self.duplicate_parts
            or self.issues
        )

    @property
    def install_inventory_ready(self) -> bool:
        return (
            self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
            and self.result_counts.get("pass", 0) == self.expected_row_count
        )

    @property
    def real_sensor_inventory_ready(self) -> bool:
        return self.install_inventory_ready and not self.sensor_inventory_blank_parts


@dataclass(frozen=True)
class FirstPrintServiceStateReviewRow:
    mode: str
    mode_type: str
    review_scope: str
    acceptance_gate: str
    expected_removed_parts: str = ""
    expected_review_parts: str = ""
    screenshot_path: str = ""
    result: str = "not_tested"
    notes: str = ""


@dataclass(frozen=True)
class FirstPrintServiceStateBoundsEvidenceRow:
    mode: str
    mode_type: str
    review_scope: str
    acceptance_gate: str
    part: str
    x_min_mm: float
    x_max_mm: float
    x_len_mm: float
    y_min_mm: float
    y_max_mm: float
    y_len_mm: float
    z_min_mm: float
    z_max_mm: float
    z_len_mm: float
    expected_removed_parts_absent: str
    expected_review_parts_present: str
    result: str = "pass"
    notes: str = "plain-Python CadQuery bounds; physical gates unchanged"


@dataclass(frozen=True)
class FirstPrintServiceStateReviewIssue:
    mode: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintServiceStateReviewAudit:
    worksheet_path: Path
    expected_row_count: int
    actual_row_count: int
    result_counts: dict[str, int]
    missing_modes: tuple[str, ...]
    extra_modes: tuple[str, ...]
    duplicate_modes: tuple[str, ...]
    issues: tuple[FirstPrintServiceStateReviewIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_modes
            or self.extra_modes
            or self.duplicate_modes
            or self.issues
        )

    @property
    def service_state_review_ready(self) -> bool:
        return (
            self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
            and self.result_counts.get("pass", 0) == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintSlicerSetupRow:
    slicer_name: str
    executable_path: str
    version: str
    printer_profile: str
    material_profile: str
    print_profile: str
    profile_source: str
    selected: str = ""
    result: str = "not_tested"
    notes: str = ""

    @property
    def setup_summary(self) -> str:
        return (
            f"{self.slicer_name} / {self.printer_profile} / "
            f"{self.material_profile} / {self.print_profile}"
        )


@dataclass(frozen=True)
class FirstPrintSlicerSetupIssue:
    slicer_name: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintSlicerSetupAudit:
    worksheet_path: Path
    row_count: int
    selected_row_count: int
    selected_setup_summary: str
    issues: tuple[FirstPrintSlicerSetupIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not self.issues

    @property
    def setup_selected(self) -> bool:
        return self.worksheet_valid and self.selected_row_count == 1


@dataclass(frozen=True)
class FirstPrintSlicerBedFitIssue:
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintSlicerBedFitOversize:
    part: str
    target_x_mm: float
    target_y_mm: float
    bed_x_mm: float
    bed_y_mm: float


@dataclass(frozen=True)
class FirstPrintSlicerBedFitAudit:
    selected_setup_summary: str
    printer_profile: str
    bed_shape_source: str
    bed_x_mm: float
    bed_y_mm: float
    oversized_parts: tuple[FirstPrintSlicerBedFitOversize, ...]
    issues: tuple[FirstPrintSlicerBedFitIssue, ...]

    @property
    def bed_resolved(self) -> bool:
        return self.bed_x_mm > 0 and self.bed_y_mm > 0

    @property
    def bed_fit_ready(self) -> bool:
        return self.bed_resolved and not self.oversized_parts and not self.issues


@dataclass(frozen=True)
class FirstPrintSlicerSetupSelection:
    worksheet_path: Path
    record_path: Path
    selected_row_index: int
    selected_setup_summary: str
    audit: FirstPrintSlicerSetupAudit


@dataclass(frozen=True)
class FirstPrintSlicerQueueItem:
    name: str
    source_stl_path: Path
    queue_stl_path: Path
    sha256: str
    target_x_mm: float
    target_y_mm: float
    target_z_mm: float
    role: str


@dataclass(frozen=True)
class FirstPrintSlicerQueueHashMismatch:
    path: Path
    expected_sha256: str
    actual_sha256: str


@dataclass(frozen=True)
class FirstPrintSlicerQueueAudit:
    queue_dir: Path
    manifest_path: Path
    manifest_exists: bool
    expected_stl_paths: tuple[Path, ...]
    actual_stl_paths: tuple[Path, ...]
    missing_stl_paths: tuple[Path, ...]
    extra_paths: tuple[Path, ...]
    hash_mismatches: tuple[FirstPrintSlicerQueueHashMismatch, ...]
    package_missing_paths: tuple[Path, ...]
    source_issues: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return not (
            self.package_missing_paths
            or self.source_issues
            or not self.manifest_exists
            or self.missing_stl_paths
            or self.extra_paths
            or self.hash_mismatches
        )


@dataclass(frozen=True)
class FirstPrintSlicedOutputRow:
    part: str
    queued_stl_path: str
    queued_stl_sha256: str
    sliced_output_path: str = ""
    sliced_output_sha256: str = ""
    selected_setup_summary: str = ""
    result: str = "not_tested"
    notes: str = ""


@dataclass(frozen=True)
class FirstPrintSlicedOutputIssue:
    part: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintSlicedOutputAudit:
    worksheet_path: Path
    expected_row_count: int
    actual_row_count: int
    result_counts: dict[str, int]
    missing_parts: tuple[str, ...]
    extra_parts: tuple[str, ...]
    duplicate_parts: tuple[str, ...]
    queue_ready: bool
    issues: tuple[FirstPrintSlicedOutputIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_parts
            or self.extra_parts
            or self.duplicate_parts
            or self.issues
        )

    @property
    def sliced_outputs_ready(self) -> bool:
        return (
            self.queue_ready
            and self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
            and self.result_counts.get("pass", 0) == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintPrintBatchTravelerRow:
    print_order: int
    part: str
    source: str
    target_x_mm: str
    target_y_mm: str
    target_z_mm: str
    queued_stl_path: str
    queued_stl_sha256: str
    sliced_output_path: str
    sliced_output_sha256: str
    selected_setup_summary: str
    gate1_qc_result: str
    print_result: str = "not_printed"
    print_evidence_path: str = ""
    notes: str = "print pending; collect Gate 1 dimensions after print"


@dataclass(frozen=True)
class FirstPrintPrintBatchTravelerIssue:
    part: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintPrintBatchTravelerAudit:
    worksheet_path: Path
    expected_row_count: int
    actual_row_count: int
    print_result_counts: dict[str, int]
    missing_parts: tuple[str, ...]
    extra_parts: tuple[str, ...]
    duplicate_parts: tuple[str, ...]
    sliced_outputs_ready: bool
    gate1_qc_worksheet_valid: bool
    issues: tuple[FirstPrintPrintBatchTravelerIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_parts
            or self.extra_parts
            or self.duplicate_parts
            or self.issues
        )

    @property
    def handoff_ready(self) -> bool:
        return (
            self.sliced_outputs_ready
            and self.gate1_qc_worksheet_valid
            and self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintGate1PrintQCIssue:
    part: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate1PrintQCAudit:
    gate1_qc_worksheet_path: Path
    print_batch_traveler_path: Path
    expected_row_count: int
    printed_row_count: int
    unprinted_parts: tuple[str, ...]
    gate1_qc_worksheet_valid: bool
    gate1_pass_ready: bool
    print_batch_handoff_ready: bool
    issues: tuple[FirstPrintGate1PrintQCIssue, ...]

    @property
    def print_qc_ready(self) -> bool:
        return (
            self.gate1_qc_worksheet_valid
            and self.gate1_pass_ready
            and self.print_batch_handoff_ready
            and not self.unprinted_parts
            and not self.issues
            and self.printed_row_count == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintGate2DryAssemblyReadinessIssue:
    target: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate2DryAssemblyReadinessAudit:
    gate2_dry_assembly_worksheet_path: Path
    gate1_qc_worksheet_path: Path
    print_batch_traveler_path: Path
    install_inventory_path: Path
    service_state_review_path: Path
    gate2_dry_assembly_worksheet_valid: bool
    gate2_dry_assembly_pass_ready: bool
    gate2_pass_row_count: int
    gate1_print_qc_ready: bool
    install_inventory_valid: bool
    install_inventory_ready: bool
    service_state_review_valid: bool
    service_state_review_ready: bool
    issues: tuple[FirstPrintGate2DryAssemblyReadinessIssue, ...]

    @property
    def dry_assembly_ready(self) -> bool:
        return (
            self.gate2_dry_assembly_worksheet_valid
            and self.gate2_dry_assembly_pass_ready
            and self.gate1_print_qc_ready
            and self.install_inventory_valid
            and self.install_inventory_ready
            and self.service_state_review_valid
            and self.service_state_review_ready
            and not self.issues
        )


@dataclass(frozen=True)
class FirstPrintGate3PlacementReadinessIssue:
    target: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate3PlacementReadinessAudit:
    gate3_placement_worksheet_path: Path
    gate2_dry_assembly_worksheet_path: Path
    gate1_qc_worksheet_path: Path
    print_batch_traveler_path: Path
    install_inventory_path: Path
    gate3_placement_worksheet_valid: bool
    gate3_placement_pass_ready: bool
    gate3_pass_row_count: int
    gate2_dry_assembly_ready: bool
    gate2_dry_assembly_worksheet_valid: bool
    gate2_dry_assembly_pass_ready: bool
    gate2_pass_row_count: int
    gate1_print_qc_ready: bool
    install_inventory_ready: bool
    service_state_review_ready: bool
    issues: tuple[FirstPrintGate3PlacementReadinessIssue, ...]

    @property
    def placement_ready(self) -> bool:
        return (
            self.gate3_placement_worksheet_valid
            and self.gate3_placement_pass_ready
            and self.gate2_dry_assembly_ready
            and not self.issues
        )


@dataclass(frozen=True)
class FirstPrintGate4WetDryWitnessReadinessIssue:
    target: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate4WetDryWitnessReadinessAudit:
    gate4_wet_dry_witness_worksheet_path: Path
    gate3_placement_worksheet_path: Path
    gate2_dry_assembly_worksheet_path: Path
    gate1_qc_worksheet_path: Path
    print_batch_traveler_path: Path
    install_inventory_path: Path
    gate4_wet_dry_witness_worksheet_valid: bool
    gate4_wet_dry_witness_pass_ready: bool
    gate4_pass_row_count: int
    gate3_placement_ready: bool
    gate3_placement_worksheet_valid: bool
    gate3_placement_pass_ready: bool
    gate3_pass_row_count: int
    gate2_dry_assembly_ready: bool
    gate2_pass_row_count: int
    gate1_print_qc_ready: bool
    install_inventory_ready: bool
    service_state_review_ready: bool
    issues: tuple[FirstPrintGate4WetDryWitnessReadinessIssue, ...]

    @property
    def wet_dry_witness_ready(self) -> bool:
        return (
            self.gate4_wet_dry_witness_worksheet_valid
            and self.gate4_wet_dry_witness_pass_ready
            and self.gate3_placement_ready
            and not self.issues
        )


@dataclass(frozen=True)
class FirstPrintGate5ConsumablePunctureReadinessIssue:
    target: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate5ConsumablePunctureReadinessAudit:
    gate5_consumable_puncture_worksheet_path: Path
    gate4_wet_dry_witness_worksheet_path: Path
    gate3_placement_worksheet_path: Path
    gate2_dry_assembly_worksheet_path: Path
    gate1_qc_worksheet_path: Path
    print_batch_traveler_path: Path
    install_inventory_path: Path
    gate5_consumable_puncture_worksheet_valid: bool
    gate5_consumable_puncture_pass_ready: bool
    gate5_pass_row_count: int
    gate4_wet_dry_witness_ready: bool
    gate4_wet_dry_witness_worksheet_valid: bool
    gate4_wet_dry_witness_pass_ready: bool
    gate4_pass_row_count: int
    gate3_placement_ready: bool
    gate3_pass_row_count: int
    gate2_dry_assembly_ready: bool
    gate2_pass_row_count: int
    gate1_print_qc_ready: bool
    install_inventory_ready: bool
    service_state_review_ready: bool
    issues: tuple[FirstPrintGate5ConsumablePunctureReadinessIssue, ...]

    @property
    def consumable_puncture_ready(self) -> bool:
        return (
            self.gate5_consumable_puncture_worksheet_valid
            and self.gate5_consumable_puncture_pass_ready
            and self.gate4_wet_dry_witness_ready
            and not self.issues
        )


@dataclass(frozen=True)
class FirstPrintGate6SensorThermalReadinessIssue:
    target: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintGate6SensorThermalReadinessAudit:
    gate6_sensor_thermal_worksheet_path: Path
    gate5_consumable_puncture_worksheet_path: Path
    gate4_wet_dry_witness_worksheet_path: Path
    gate3_placement_worksheet_path: Path
    gate2_dry_assembly_worksheet_path: Path
    gate1_qc_worksheet_path: Path
    print_batch_traveler_path: Path
    install_inventory_path: Path
    gate6_sensor_thermal_worksheet_valid: bool
    gate6_sensor_thermal_pass_ready: bool
    gate6_pass_row_count: int
    gate5_consumable_puncture_ready: bool
    gate5_consumable_puncture_worksheet_valid: bool
    gate5_consumable_puncture_pass_ready: bool
    gate5_pass_row_count: int
    gate4_wet_dry_witness_ready: bool
    gate4_pass_row_count: int
    gate3_placement_ready: bool
    gate3_pass_row_count: int
    gate2_dry_assembly_ready: bool
    gate2_pass_row_count: int
    gate1_print_qc_ready: bool
    install_inventory_ready: bool
    service_state_review_ready: bool
    real_sensor_inventory_ready: bool
    sensor_inventory_blank_parts: tuple[str, ...]
    issues: tuple[FirstPrintGate6SensorThermalReadinessIssue, ...]

    @property
    def sensor_thermal_ready(self) -> bool:
        return (
            self.gate6_sensor_thermal_worksheet_valid
            and self.gate6_sensor_thermal_pass_ready
            and self.gate5_consumable_puncture_ready
            and self.real_sensor_inventory_ready
            and not self.issues
        )


@dataclass(frozen=True)
class FirstPrintOperatingPrototypeAcceptanceIssue:
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintOperatingPrototypeAcceptanceAudit:
    record_path: Path
    preflight_artifacts_ready: bool
    print_start_ready: bool
    service_state_review_ready: bool
    install_inventory_ready: bool
    gate1_print_qc_ready: bool
    gate2_dry_assembly_ready: bool
    gate2_pass_row_count: int
    gate3_placement_ready: bool
    gate3_pass_row_count: int
    gate4_wet_dry_witness_ready: bool
    gate4_pass_row_count: int
    gate5_consumable_puncture_ready: bool
    gate5_pass_row_count: int
    sensor_thermal_ready: bool
    real_sensor_inventory_ready: bool
    sensor_inventory_blank_parts: tuple[str, ...]
    gate6_sensor_thermal_worksheet_valid: bool
    gate6_sensor_thermal_pass_ready: bool
    gate6_pass_row_count: int
    physical_gate_passes: tuple[str, ...]
    issues: tuple[FirstPrintOperatingPrototypeAcceptanceIssue, ...]

    @property
    def operating_prototype_ready(self) -> bool:
        return (
            self.preflight_artifacts_ready
            and self.print_start_ready
            and self.sensor_thermal_ready
            and not self.issues
        )

    @property
    def next_evidence_actions(self) -> tuple[str, ...]:
        if self.operating_prototype_ready:
            return ()
        if not self.preflight_artifacts_ready:
            return ("close_preflight_artifacts",)
        if not self.print_start_ready:
            return ("close_print_start_handoff",)
        blockers: list[str] = []
        if not self.service_state_review_ready:
            blockers.append("complete_service_state_review")
        if not self.install_inventory_ready:
            blockers.append("complete_install_inventory")
        if not self.gate1_print_qc_ready:
            blockers.append("close_split_gate1_print_qc")
        if blockers:
            return tuple(blockers)
        if not self.gate2_dry_assembly_ready:
            return ("close_gate2_dry_assembly",)
        if not self.gate3_placement_ready:
            return ("close_gate3_ot2_placement",)
        if not self.gate4_wet_dry_witness_ready:
            return ("close_gate4_wet_dry_witness",)
        if not self.gate5_consumable_puncture_ready:
            return ("close_gate5_consumable_puncture",)
        if not self.real_sensor_inventory_ready:
            blockers.append("install_real_sensor_inventory")
        if not self.gate6_sensor_thermal_pass_ready:
            blockers.append("close_gate6_sensor_thermal")
        if blockers:
            return tuple(blockers)
        if not self.sensor_thermal_ready:
            return ("close_sensor_thermal_readiness",)
        return ("resolve_operating_acceptance_issues",)

@dataclass(frozen=True)
class FirstPrintBedFitSplitPlanRow:
    part: str
    target_x_mm: float
    target_y_mm: float
    target_z_mm: float
    selected_bed_x_mm: float
    selected_bed_y_mm: float
    fits_as_exported: bool
    minimum_y_segments: int
    max_segment_y_mm: float
    segment_fits_selected_bed: bool
    required_decision: str
    result: str = "not_tested"
    notes: str = ""


@dataclass(frozen=True)
class FirstPrintBedFitSplitPlanIssue:
    part: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintBedFitSplitPlanAudit:
    worksheet_path: Path
    expected_row_count: int
    actual_row_count: int
    result_counts: dict[str, int]
    missing_parts: tuple[str, ...]
    extra_parts: tuple[str, ...]
    duplicate_parts: tuple[str, ...]
    split_required_parts: tuple[str, ...]
    issues: tuple[FirstPrintBedFitSplitPlanIssue, ...]

    @property
    def worksheet_valid(self) -> bool:
        return not (
            self.missing_parts
            or self.extra_parts
            or self.duplicate_parts
            or self.issues
        )

    @property
    def split_plan_ready(self) -> bool:
        return (
            self.worksheet_valid
            and self.actual_row_count == self.expected_row_count
            and self.result_counts.get("pass", 0) == self.expected_row_count
        )


@dataclass(frozen=True)
class FirstPrintYSplitArtifactRow:
    split_part: str
    source_part: str
    segment_index: int
    segment_count: int
    target_x_mm: float
    target_y_mm: float
    target_z_mm: float
    selected_bed_x_mm: float
    selected_bed_y_mm: float
    fits_selected_bed: bool
    stl_path: Path
    step_path: Path
    stl_exists: bool
    step_exists: bool
    interface_zone: str
    required_evidence: str


@dataclass(frozen=True)
class FirstPrintYSplitArtifactIssue:
    split_part: str
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintYSplitArtifactAudit:
    split_dir: Path
    selected_setup_summary: str
    bed_x_mm: float
    bed_y_mm: float
    expected_row_count: int
    rows: tuple[FirstPrintYSplitArtifactRow, ...]
    split_source_parts: tuple[str, ...]
    covered_oversized_parts: tuple[str, ...]
    missing_oversized_parts: tuple[str, ...]
    issues: tuple[FirstPrintYSplitArtifactIssue, ...]

    @property
    def split_artifacts_ready(self) -> bool:
        return (
            self.bed_x_mm > 0
            and self.bed_y_mm > 0
            and not self.missing_oversized_parts
            and not self.issues
            and len(self.rows) == self.expected_row_count
            and all(
                row.stl_exists and row.step_exists and row.fits_selected_bed
                for row in self.rows
            )
        )


@dataclass(frozen=True)
class FirstPrintPreflightIssue:
    field: str
    message: str


@dataclass(frozen=True)
class FirstPrintPreflightAudit:
    record_path: Path
    active_queue_mode: str
    package_ready: bool
    slicer_queue_ready: bool
    params_hash_matches: bool
    generated_output_timestamp_matches: bool
    cad_target_sections_match: bool
    expected_params_sha256: str
    record_params_sha256: str
    expected_generated_output_timestamp: str
    record_generated_output_timestamp: str
    slicer_setup_valid: bool
    slicer_setup_selected: bool
    selected_slicer_setup: str
    slicer_bed_fit_ready: bool
    slicer_bed_x_mm: float
    slicer_bed_y_mm: float
    slicer_bed_oversized_parts: tuple[str, ...]
    sliced_outputs_valid: bool
    sliced_outputs_ready: bool
    gate1_qc_worksheet_valid: bool
    gate1_pass_ready: bool
    gate2_dry_assembly_worksheet_valid: bool
    gate2_dry_assembly_pass_ready: bool
    gate3_placement_worksheet_valid: bool
    gate3_placement_pass_ready: bool
    gate4_wet_dry_witness_worksheet_valid: bool
    gate4_wet_dry_witness_pass_ready: bool
    gate5_consumable_puncture_worksheet_valid: bool
    gate5_consumable_puncture_pass_ready: bool
    gate6_sensor_thermal_worksheet_valid: bool
    gate6_sensor_thermal_pass_ready: bool
    install_inventory_valid: bool
    install_inventory_ready: bool
    service_state_review_valid: bool
    service_state_review_ready: bool
    record_gate0_pass: bool
    required_session_fields_present: bool
    missing_session_fields: tuple[str, ...]
    physical_gate_passes: tuple[str, ...]
    missing_record_links: tuple[str, ...]
    stale_cad_target_sections: tuple[str, ...]
    issues: tuple[FirstPrintPreflightIssue, ...]

    @property
    def preprint_ready(self) -> bool:
        return (
            self.package_ready
            and self.slicer_queue_ready
            and self.params_hash_matches
            and self.generated_output_timestamp_matches
            and self.cad_target_sections_match
            and self.slicer_setup_valid
            and self.slicer_setup_selected
            and self.slicer_bed_fit_ready
            and self.sliced_outputs_valid
            and self.gate1_qc_worksheet_valid
            and self.gate2_dry_assembly_worksheet_valid
            and self.gate3_placement_worksheet_valid
            and self.gate4_wet_dry_witness_worksheet_valid
            and self.gate5_consumable_puncture_worksheet_valid
            and self.gate6_sensor_thermal_worksheet_valid
            and self.install_inventory_valid
            and self.service_state_review_valid
            and self.service_state_review_ready
            and self.record_gate0_pass
            and self.required_session_fields_present
            and not self.physical_gate_passes
            and not self.missing_record_links
            and not self.issues
        )

    @property
    def print_start_ready(self) -> bool:
        return self.preprint_ready and self.sliced_outputs_ready


def artifact_category(fabrication_source: str) -> str:
    if fabrication_source == "printed_polymer":
        return "printed"
    if fabrication_source == "compressible_elastomer_or_printed_tpu":
        return "compressible_or_flexible"
    if fabrication_source == "cots_consumable":
        return "cots_consumable"
    if fabrication_source == "cots_flexible_tubing":
        return "service_tubing"
    if fabrication_source in {
        "cots_electronics",
        "custom_or_cots_pcb_assembly",
        "electronics_assembly",
        "electronics_microcarrier",
        "cots_cable_assembly",
    }:
        return "electronics_or_dimensional_blank"
    if fabrication_source == "validation_only_geometry":
        return "validation"
    return "other"


def expected_production_artifacts(
    params: dict[str, Any],
    out_dir: str | Path,
) -> tuple[FirstPrintArtifact, ...]:
    out = Path(out_dir)
    prefix = params["name"]
    manifest = row_coupon_part_manifest()
    artifacts: list[FirstPrintArtifact] = []
    for name, entry in manifest["installed"].items():
        stl_path = out / f"{prefix}_{name}.stl"
        step_path = out / f"{prefix}_{name}.step"
        fabrication_source = entry["fabrication_source"]
        artifacts.append(
            FirstPrintArtifact(
                name=name,
                category=artifact_category(fabrication_source),
                stl_path=stl_path,
                step_path=step_path,
                stl_exists=stl_path.exists(),
                step_exists=step_path.exists(),
                fabrication_source=fabrication_source,
                role=entry["role"],
            )
        )
    return tuple(artifacts)


def _validation_artifact(
    *,
    name: str,
    prefix: str,
    out: Path,
    role: str,
    optional: bool = False,
) -> FirstPrintArtifact:
    stl_path = out / f"{prefix}_validation_{name}.stl"
    step_path = out / f"{prefix}_validation_{name}.step"
    return FirstPrintArtifact(
        name=name,
        category="optional_validation" if optional else "validation",
        stl_path=stl_path,
        step_path=step_path,
        stl_exists=stl_path.exists(),
        step_exists=step_path.exists(),
        fabrication_source="validation_only_geometry",
        role=role,
    )


def expected_validation_artifacts(
    params: dict[str, Any],
    out_dir: str | Path,
) -> tuple[FirstPrintArtifact, ...]:
    out = Path(out_dir)
    prefix = params["name"]
    validation_manifest = row_coupon_part_manifest()["validation"]
    return tuple(
        _validation_artifact(
            name=name,
            prefix=prefix,
            out=out,
            role=validation_manifest[name]["role"],
        )
        for name in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    )


def expected_optional_validation_artifacts(
    params: dict[str, Any],
    out_dir: str | Path,
) -> tuple[FirstPrintArtifact, ...]:
    out = Path(out_dir)
    prefix = params["name"]
    validation_manifest = row_coupon_part_manifest()["validation"]
    return tuple(
        _validation_artifact(
            name=name,
            prefix=prefix,
            out=out,
            role=validation_manifest[name]["role"],
            optional=True,
        )
        for name in FIRST_PRINT_OPTIONAL_VALIDATION_TOOLS
    )


def audit_first_print_package(
    params: dict[str, Any],
    out_dir: str | Path,
) -> FirstPrintPackageAudit:
    out = Path(out_dir)
    assembly_step = out / f"{params['name']}_assembly.step"
    return FirstPrintPackageAudit(
        name=params["name"],
        out_dir=out,
        assembly_step=assembly_step,
        assembly_step_exists=assembly_step.exists(),
        production_artifacts=expected_production_artifacts(params, out),
        validation_artifacts=expected_validation_artifacts(params, out),
        optional_validation_artifacts=expected_optional_validation_artifacts(params, out),
    )


def file_sha256(path: str | Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def first_print_artifact_category_counts(
    audit: FirstPrintPackageAudit,
) -> dict[str, int]:
    counts = Counter(artifact.category for artifact in audit.production_artifacts)
    return dict(sorted(counts.items()))


def _required_artifact_paths(audit: FirstPrintPackageAudit) -> tuple[Path, ...]:
    paths = [audit.assembly_step]
    for artifact in (*audit.production_artifacts, *audit.validation_artifacts):
        paths.extend((artifact.stl_path, artifact.step_path))
    return tuple(paths)


def latest_required_artifact_timestamp(audit: FirstPrintPackageAudit) -> str:
    mtimes = [
        path.stat().st_mtime
        for path in _required_artifact_paths(audit)
        if path.exists()
    ]
    if not mtimes:
        return ""
    timestamp = datetime.fromtimestamp(max(mtimes), tz=UTC)
    return timestamp.isoformat(timespec="seconds").replace("+00:00", "Z")


def first_print_audit_snapshot_markdown(audit: FirstPrintPackageAudit) -> str:
    lines = [
        "## Gate 0 Audit Snapshot",
        "",
        "This snapshot only verifies CAD output package presence. It does not mark any",
        "physical readiness gate as passed.",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Package | `{audit.name}` |",
        f"| Output directory | `{audit.out_dir}` |",
        f"| Assembly STEP | {'present' if audit.assembly_step_exists else 'missing'} |",
        f"| Required production artifacts | {len(audit.production_artifacts)} |",
        f"| Required validation artifacts | {len(audit.validation_artifacts)} |",
        f"| Optional validation artifacts | {len(audit.optional_validation_artifacts)} |",
        f"| Audit ready | {'true' if audit.ready else 'false'} |",
        "",
        "| Production artifact category | Count |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {category} | {count} |"
        for category, count in first_print_artifact_category_counts(audit).items()
    )

    missing = audit.missing_paths
    if missing:
        lines.extend(
            [
                "",
                "| Missing required artifact |",
                "|---|",
            ]
        )
        lines.extend(f"| `{path}` |" for path in missing)
    else:
        lines.extend(["", "Missing required artifacts: none"])

    return "\n".join(lines)


def first_print_qc_targets(params: dict[str, Any]) -> tuple[FirstPrintQCTarget, ...]:
    manifest = row_coupon_part_manifest()["installed"]
    parts = build_row_coupon_service_parts(params, mode="installed")
    targets: list[FirstPrintQCTarget] = []
    for name, entry in manifest.items():
        category = artifact_category(entry["fabrication_source"])
        if category not in {"printed", "compressible_or_flexible"}:
            continue
        bb = parts[name].val().BoundingBox()
        targets.append(
            FirstPrintQCTarget(
                name=name,
                category=category,
                target_x_mm=round(bb.xlen, 2),
                target_y_mm=round(bb.ylen, 2),
                target_z_mm=round(bb.zlen, 2),
                role=entry["role"],
            )
        )
    return tuple(targets)


def first_print_qc_target_bounds_markdown(params: dict[str, Any]) -> str:
    lines = [
        "## Gate 1 CAD Target Bounds",
        "",
        "These are CAD target bounds for first-print caliper comparison. They do",
        "not mark Gate 1 passed, and compressible/flexible parts remain nominal",
        "uncompressed CAD bodies until real stock or printed TPU is measured.",
        "",
        "| Part | Source | Target X mm | Target Y mm | Target Z mm | Role |",
        "|---|---|---:|---:|---:|---|",
    ]
    for target in first_print_qc_targets(params):
        lines.append(
            "| "
            f"`{target.name}` | {target.category} | "
            f"{target.target_x_mm:.2f} | {target.target_y_mm:.2f} | "
            f"{target.target_z_mm:.2f} | {target.role} |"
        )
    return "\n".join(lines)


def first_print_gate3_placement_targets(
    params: dict[str, Any],
) -> tuple[FirstPrintGate3PlacementTarget, ...]:
    layout = row_coupon_layout(params)
    clearance = layout["side_gas_adjacent_slot_clearance"]
    dry_bay = layout["dry_bay_envelope"]
    puncture_check = layout["pipette_puncture_swept_path_check"]
    toolhead_check = layout["pipette_toolhead_swept_body_check"]
    service_dress_check = layout["operating_service_dress_check"]
    row_tiling = layout["row_tiling_service_clearance_check"]
    deck_pod_repeatability = layout["deck_pod_seating_repeatability_check"]
    deck_frame_keepout = layout["deck_frame_keepout_check"]
    assembly_envelope_z = float(layout["assembly_envelope_z"])
    tolerance = FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM
    return (
        FirstPrintGate3PlacementTarget(
            target="Assembly deck-to-top envelope",
            cad_value=f"{assembly_envelope_z:.2f} mm",
            physical_check=(
                f"measured high point <= {assembly_envelope_z + tolerance:.2f} mm"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Assembly footprint X",
            cad_value=f"{float(deck_frame_keepout['length_x']):.2f} mm",
            physical_check="seated module stays inside intended deck-frame width",
        ),
        FirstPrintGate3PlacementTarget(
            target="Assembly footprint Y",
            cad_value=f"{float(deck_frame_keepout['width_y']):.2f} mm",
            physical_check="four-plate row stays inside intended deck-frame length",
        ),
        FirstPrintGate3PlacementTarget(
            target="Deck pod seating repeatability",
            cad_value=deck_pod_repeatability["cad_value"],
            physical_check=(
                "five seat/release cycles prove no rocking, yaw, wear, "
                "frame contact, or dry-bay debris"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Adjacent-slot service clearance",
            cad_value=f"{float(clearance['min_vertical_clearance_z']):.2f} mm",
            physical_check=(
                "dressed tube/cable route does not touch adjacent-slot keepout"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Required adjacent-slot clearance",
            cad_value=f"{float(clearance['required_vertical_clearance_z']):.2f} mm",
            physical_check=(
                "measured service dress remains above the keepout by at least "
                "this margin"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Operating service dress envelope",
            cad_value=str(service_dress_check["cad_value"]),
            physical_check=(
                "dressed gas and electrical services stay inside exported "
                "validation body"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Row tiling/service clearance check",
            cad_value=str(row_tiling["cad_value"]),
            physical_check=(
                "inspect printed row with adjacent OT-2 slot/service dress before "
                "operating deck use"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="OT-2 toolhead swept body envelope",
            cad_value=str(toolhead_check["cad_value"]),
            physical_check=(
                "measured OT-2 toolhead body clears exported validation body "
                "at every puncture target"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="OT-2 toolhead lower clearance",
            cad_value=str(toolhead_check["clearance_cad_value"]),
            physical_check=(
                "do not replace conservative CAD envelope without measured "
                "two-pipette OT-2 toolhead evidence"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Pipette puncture targets",
            cad_value=str(puncture_check["target_count_cad_value"]),
            physical_check=(
                "no cap, latch, tube, cable, or connector over any septum target"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Dry-bay protected footprint",
            cad_value=(
                f"{float(dry_bay['length_x']):.2f} x "
                f"{float(dry_bay['width_y']):.2f} mm"
            ),
            physical_check=(
                "no service lead, wet witness path, or debris bridge enters "
                "this footprint"
            ),
        ),
    )


def first_print_ot2_placement_targets_markdown(params: dict[str, Any]) -> str:
    targets = first_print_gate3_placement_targets(params)
    lines = [
        "## Gate 3 CAD Placement Targets",
        "",
        "These are CAD targets for OT-2 placement/no-motion inspection. They do",
        "not mark Gate 3 passed; use them to compare the printed assembly and",
        "dressed services against the current CAD envelope.",
        "",
        "| Target | CAD value | Physical check |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| {target.target} | {target.cad_value} | {target.physical_check} |"
        for target in targets
    )
    return "\n".join(lines)


def first_print_gate2_dry_assembly_targets(
    params: dict[str, Any],
) -> tuple[FirstPrintGate2DryAssemblyTarget, ...]:
    layout = row_coupon_layout(params)
    plate = params["plate"]
    mat = params["septum_mat"]
    latch_ramp = layout["latch_ramp_self_lock"]
    latch_asymmetry = layout["latch_station_asymmetry"]
    wedge_locks = layout["wedge_lock_rectangles"]
    assembly_state = layout["assembly_state_witness_check"]
    gasket_gap_gauge = layout["gasket_compression_gap_gauge"]
    latch_retention = layout["latch_retention_span_check"]
    side_tube_check = layout["side_gas_tube_envelope_check"]
    sensor_summary = layout["sensor_mount_summary"]
    harness = layout["sensor_harness_summary"]
    cable_envelope = layout["sensor_service_cable_envelopes"][0]
    dry_bay = layout["dry_bay_envelope"]
    plate_locator_rails = layout["plate_locator_rails"]
    fail_closed = layout["fail_closed_prerun_inspection_check"]
    return (
        FirstPrintGate2DryAssemblyTarget(
            target="Installed dry stack",
            cad_value=str(assembly_state["stack_cad_value"]),
            physical_check=(
                "dry stack follows production order with no liquid or powered electronics"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Plate/mat service cycles",
            cad_value=f"{FIRST_PRINT_DRY_ASSEMBLY_SERVICE_CYCLES} cycles each",
            physical_check="plates and mats insert, swap, reseat, and remain captured",
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Plate support datum",
            cad_value=(
                f"z={float(layout['plate_bottom_z']):.2f}.."
                f"{float(layout['plate_top_z']):.2f} mm"
            ),
            physical_check=(
                "plate is supported without scraping or contacting optical bottom"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Plate locator rails",
            cad_value=(
                f"{len(plate_locator_rails)} rails / "
                f"{float(plate_locator_rails[0]['height_z']):.2f} mm high"
            ),
            physical_check=(
                "real plate lot loads without filing, rocking, or sidewall crush"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Consumable nominal envelope",
            cad_value=(
                f"{float(plate['length_x']):.2f} x {float(plate['width_y']):.2f} "
                "mm plate / "
                f"{float(mat['sheet_thickness_z']) + float(mat['round_plug_depth_z']):.2f} "
                "mm mat stack"
            ),
            physical_check=(
                "mat seats on plate without lifting plate from locator rails"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Latch gasket squeeze budget",
            cad_value=str(gasket_gap_gauge["cad_value"]),
            physical_check=(
                "latches close stack without plate bow, gasket overcrush, screws, or glue"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Wedge lock stations",
            cad_value=(
                f"{len(wedge_locks)} locks / "
                f"{float(wedge_locks[0]['length_x']):.2f} mm travel body"
            ),
            physical_check=(
                "every printed wedge inserts, detents, releases, and survives cycling"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Latch asymmetry watch",
            cad_value=(
                f"{int(latch_asymmetry['omitted_station_count'])} omitted / "
                f"{float(latch_asymmetry['max_active_station_span_mm']):.2f} mm "
                "max span"
            ),
            physical_check=(
                "inspect wet-frame/lid bow near omitted station before wet tests"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Latch self-lock margin",
            cad_value=(
                f"{float(latch_ramp['self_lock_margin_deg']):.2f} deg / "
                f"{latch_ramp['retention_status']}"
            ),
            physical_check=(
                "detent must hold through dry service cycling before liquid exposure"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Latch retention/span evidence",
            cad_value=str(latch_retention["cad_value"]),
            physical_check=(
                "dry-cycle detent hold, omitted-station bow, post bearing, and "
                "gasket squeeze evidence required before wet tests"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Fail-closed pre-run inspection",
            cad_value=str(fail_closed["cad_value"]),
            physical_check=(
                "any failed blocker row prevents OT-2 operation until corrected"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Side gas service dry fit",
            cad_value=str(side_tube_check["cad_value"]),
            physical_check=(
                "supply and return tubes seat on printed barbs without glue or clamps"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Electrical service dry fit",
            cad_value=(
                f"{int(harness['installed_service_cable_pigtail_count'])} pigtails / "
                f"{float(cable_envelope['min_bend_radius_y']):.2f} mm bend radius"
            ),
            physical_check=(
                "pigtails dress into +Y service exits without pinching covers"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Sensor package dry fit",
            cad_value=(
                f"{int(sensor_summary['gas_sensor_pcb_count'])} gas PCB / "
                f"{int(sensor_summary['headspace_sht41_count'])} SHT41 / "
                f"{int(sensor_summary['ir_thermopile_count'])} IR"
            ),
            physical_check=(
                "real packages or dimensional blanks install and remove without trimming"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Dry-bay open volume",
            cad_value=(
                f"{float(dry_bay['length_x']):.2f} x "
                f"{float(dry_bay['width_y']):.2f} x "
                f"{float(dry_bay['top_z']) - float(dry_bay['bottom_z']):.2f} mm"
            ),
            physical_check=(
                "dry observer bay remains open, unblocked, and free of assembly debris"
            ),
        ),
    )


def first_print_dry_assembly_targets_markdown(params: dict[str, Any]) -> str:
    targets = first_print_gate2_dry_assembly_targets(params)
    lines = [
        "## Gate 2 CAD Dry Assembly Targets",
        "",
        "These are CAD targets for dry production assembly service checks. They",
        "do not mark Gate 2 passed; use them to catch fit, latch, service-dress,",
        "and omitted-latch-span failures before OT-2 placement, wet testing, or",
        "powered sensors.",
        "",
        "| Target | CAD/service value | Physical check |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| {target.target} | {target.cad_value} | {target.physical_check} |"
        for target in targets
    )
    return "\n".join(lines)


def first_print_gate4_wet_dry_witness_targets(
    params: dict[str, Any],
) -> tuple[FirstPrintGate4WetDryWitnessTarget, ...]:
    layout = row_coupon_layout(params)
    headspace_barrier = layout["headspace_barrier_check"]
    headspace_volume = layout["headspace_volume_check"]
    dry_bay_envelope = layout["dry_bay_envelope_check"]
    dry_bay_boundary = layout["dry_bay_boundary_check"]
    dry_bay_ingress = layout["dry_bay_ingress_audit_check"]
    side_gas_leak = layout["side_gas_leak_witness_check"]
    sample_relief_leak = layout["sample_relief_leak_witness_check"]
    gasket_tab_leak = layout["gasket_tab_leak_witness_check"]
    wet_dry_failure_path = layout["wet_dry_failure_path_check"]
    return (
        FirstPrintGate4WetDryWitnessTarget(
            target="Headspace barrier perimeter",
            cad_value=str(headspace_barrier["cad_value"]),
            physical_check=(
                "required barrier body traces sealed gasket perimeter with no dye bypass"
            ),
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Shared wet headspace volume",
            cad_value=str(headspace_volume["cad_value"]),
            physical_check=(
                "required volume body remains continuous and free of blocked bridges"
            ),
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Dry-bay protected volume",
            cad_value=str(dry_bay_envelope["cad_value"]),
            physical_check=(
                "required dry-bay envelope body admits no dye, condensate, debris, or service lead"
            ),
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Dry-bay ingress audit",
            cad_value=str(dry_bay_ingress["cad_value"]),
            physical_check=(
                "exported audit body shows no wet collector, dam, or debris bridge "
                "into protected footprint"
            ),
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Dry-bay boundary rail clearance",
            cad_value=str(dry_bay_boundary["cad_value"]),
            physical_check=(
                "required boundary body leaves side rails clear and unbridged"
            ),
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Side-gas service witness set",
            cad_value=str(side_gas_leak["cad_value"]),
            physical_check="side fitting dye routes to visible outboard collectors",
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Sample/relief cap witness set",
            cad_value=str(sample_relief_leak["cad_value"]),
            physical_check="cap-seat dye routes to visible edge witness",
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Gasket-tab root witness set",
            cad_value=str(gasket_tab_leak["cad_value"]),
            physical_check="lower/upper front/rear tab roots stay outside dry bay",
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Dry-bay aperture thresholds",
            cad_value=str(wet_dry_failure_path["threshold_cad_value"]),
            physical_check="raised collars remain unbridged by dye or support debris",
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Aperture-adjacent witness gutters",
            cad_value=str(wet_dry_failure_path["gutter_cad_value"]),
            physical_check=(
                "aperture-side dye stays in witness gutters and out of optics bay"
            ),
        ),
    )


def first_print_wet_dry_witness_targets_markdown(params: dict[str, Any]) -> str:
    targets = first_print_gate4_wet_dry_witness_targets(params)
    lines = [
        "## Gate 4 CAD Wet/Dry Witness Targets",
        "",
        "These are CAD targets for passive dye and condensate inspection. They do",
        "not mark Gate 4 passed; use them to compare visible wet paths against",
        "the current dry-bay ingress audit geometry.",
        "",
        "| Target | CAD value | Physical check |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| {target.target} | {target.cad_value} | {target.physical_check} |"
        for target in targets
    )
    return "\n".join(lines)


def first_print_gate5_consumable_puncture_targets(
    params: dict[str, Any],
) -> tuple[FirstPrintGate5ConsumablePunctureTarget, ...]:
    layout = row_coupon_layout(params)
    plate = params["plate"]
    mat = params["septum_mat"]
    grid = params["well_grid"]
    access = params["pipette_access"]
    metrology = params["consumable_metrology"]
    puncture_check = layout["pipette_puncture_swept_path_check"]
    plate_count = int(params["row"]["plate_count"])
    wells_per_plate = int(grid["columns"]) * int(grid["rows"])
    locator_rail_count = len(layout["plate_locator_rails"])
    locator_height = params["plate_support"]["lateral_locator_wall_height_z"]
    mat_stack_height = float(mat["sheet_thickness_z"]) + float(mat["round_plug_depth_z"])
    gauge_x = float(plate["length_x"]) + 2 * float(metrology["gauge_border_xy"])
    gauge_y = float(plate["width_y"]) + 2 * float(metrology["gauge_border_xy"])
    gauge_z = float(metrology["gauge_base_thickness_z"])
    return (
        FirstPrintGate5ConsumablePunctureTarget(
            target="Installed consumable set",
            cad_value=f"{plate_count} plates / {plate_count} septum mats",
            physical_check="real CellVis plates and Cole-Parmer mats required for pass",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Consumable metrology gauge",
            cad_value=f"{gauge_x:.2f} x {gauge_y:.2f} x {gauge_z:.2f} mm",
            physical_check=(
                "required gauge checks plate/mat lot fit before puncture claims"
            ),
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Plate CAD footprint",
            cad_value=(
                f"{float(plate['length_x']):.2f} x {float(plate['width_y']):.2f} x "
                f"{float(plate['height_z']):.2f} mm"
            ),
            physical_check="measure real plate lot; revise only if fit check fails",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Plate support datum",
            cad_value=f"z={float(layout['plate_bottom_z']):.2f} mm",
            physical_check="plate underside support contacts avoid optical bottom",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Locator rail count/height",
            cad_value=f"{locator_rail_count} rails / {float(locator_height):.2f} mm",
            physical_check="rails constrain lateral shift without pinching plate",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Mat CAD thickness stack",
            cad_value=f"{mat_stack_height:.2f} mm",
            physical_check=(
                "sheet plus plug depth placeholder; replace with measured mat data"
            ),
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Mat plug CAD diameter/depth",
            cad_value=(
                f"{float(mat['round_plug_diameter']):.2f} mm / "
                f"{float(mat['round_plug_depth_z']):.2f} mm"
            ),
            physical_check="plug fits wells without bottoming, bunching, or lifting plate",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Mat slit CAD relief",
            cad_value=(
                f"{float(mat['slit_cut_length_x']):.2f} x "
                f"{float(mat['slit_cut_width_y']):.2f} mm"
            ),
            physical_check="tip admits through slit without tearing or persistent opening",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Puncture target count",
            cad_value=str(puncture_check["target_count_cad_value"]),
            physical_check=(
                f"required swept-path validation body covers all "
                f"{wells_per_plate} positions per plate"
            ),
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Puncture swept diameter",
            cad_value=str(puncture_check["diameter_cad_value"]),
            physical_check="tip plus radial clearance through septum target",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Puncture Z range",
            cad_value=str(puncture_check["z_range_cad_value"]),
            physical_check=(
                f"{float(access['puncture_depth_below_mat_top_z']):.2f} mm below mat top"
            ),
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Puncture force limit",
            cad_value=f"{float(access['puncture_force_limit_n']):.2f} N",
            physical_check="revise if intended tip/mat combination exceeds this force",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Repeat puncture minimum",
            cad_value=f"{int(access['repeat_puncture_cycles_min'])} cycles",
            physical_check="same representative well reseals without unacceptable wear",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Plate lateral shift limit",
            cad_value=f"<={FIRST_PRINT_PUNCTURE_PLATE_SHIFT_LIMIT_MM:.2f} mm",
            physical_check="compare plate/mat datum positions before and after puncture",
        ),
    )


def first_print_consumable_puncture_targets_markdown(params: dict[str, Any]) -> str:
    targets = first_print_gate5_consumable_puncture_targets(params)
    lines = [
        "## Gate 5 CAD Consumable/Puncture Targets",
        "",
        "These are CAD and protocol targets for consumable metrology and first",
        "puncture testing. They do not mark Gate 5 passed; the Cole-Parmer mat",
        "dimensions remain measurement-gated until real caliper and wet-exposure",
        "data replace the current CAD assumptions.",
        "",
        "| Target | CAD/protocol value | Physical check |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| {target.target} | {target.cad_value} | {target.physical_check} |"
        for target in targets
    )
    return "\n".join(lines)


def first_print_gate6_sensor_thermal_targets(
    params: dict[str, Any],
) -> tuple[FirstPrintGate6SensorThermalTarget, ...]:
    layout = row_coupon_layout(params)
    install_check = layout["sensor_installation_path_check"]
    harness = layout["sensor_harness_summary"]
    gas_mounts = layout["gas_sensor_pcb_mounts"]
    sht_mounts = layout["headspace_sht41_mounts"]
    ir_mounts = layout["ir_sensor_mounts"]
    ir_fov_spot = layout["ir_thermopile_fov_spot_check"]
    thermal_proxy = layout["thermal_condensation_proxy_check"]
    gas_mount = gas_mounts[0]
    gas_flow_cell = layout["gas_pcb_flow_cell_check"]
    gas_interface = gas_mount["gas_interface"]
    sht_mount = sht_mounts[0]
    ir_mount = ir_mounts[0]
    face_gasket = ir_mount["face_gasket"]
    connector_clearance_check = layout["sensor_connector_service_clearance_check"]
    cable_envelope_check = layout["sensor_service_cable_envelope_check"]
    mating_state_check = layout["electrical_connector_mating_state_check"]
    observer_front_end = layout["observer_front_end_swept_body_check"]
    observer_carriage = layout["observer_carriage_envelope_check"]
    observer_service_raceway = layout["observer_service_raceway_envelope_check"]
    observer_optical_stability = layout["observer_optical_stability_check"]
    observer_kinematic_split = layout["observer_kinematic_split_check"]

    return (
        FirstPrintGate6SensorThermalTarget(
            target="Sensor install workflow",
            cad_value=str(install_check["cad_value"]),
            physical_check=(
                "install/remove follows printed reversible no-screws/no-glue policy"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Gas PCB cartridges",
            cad_value=(
                f"{len(gas_mounts)} cartridges, "
                f"{float(gas_mount['length_x']):.2f} x "
                f"{float(gas_mount['width_y']):.2f} x "
                f"{float(gas_mount['height_z']):.2f} mm"
            ),
            physical_check=(
                "supply/return cartridges seat in dry-side duct sampling cassettes"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Gas PCB aperture/dead volume",
            cad_value=gas_flow_cell["cad_value"],
            physical_check=(
                "aperture aligns to required duct sampling cell validation body, "
                "not open top headspace"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Gas PCB gasket",
            cad_value=(
                f"{float(gas_interface['nominal_gasket_thickness_x']):.2f} mm "
                "gasket / "
                f"{float(gas_interface['nominal_compression_x']):.2f} mm "
                "compression"
            ),
            physical_check="interface gasket visibly seats without crushing sensor package",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Headspace SHT41 carriers",
            cad_value=(
                f"{len(sht_mounts)} carriers, "
                f"{float(sht_mount['length_x']):.2f} x "
                f"{float(sht_mount['width_y']):.2f} x "
                f"{float(sht_mount['height_z']):.2f} mm"
            ),
            physical_check="one membrane aperture exposed per plate-local headspace",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Headspace SHT41 aperture",
            cad_value=(
                f"{float(sht_mount['aperture_diameter']):.2f} mm aperture / "
                f"{float(sht_mount['drip_break_ring']['outer_diameter']):.2f} mm "
                "drip ring OD"
            ),
            physical_check=(
                "membrane is exposed while pooling is kept off carrier electronics"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="IR thermopile pockets",
            cad_value=(
                f"{len(ir_mounts)} pockets, "
                f"{float(ir_mount['length_x']):.2f} x "
                f"{float(ir_mount['width_y']):.2f} x "
                f"{float(ir_mount['height_z']):.2f} mm"
            ),
            physical_check="plate-margin thermopiles seat with lens unobstructed",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="IR aperture/gasket",
            cad_value=(
                f"{float(ir_mount['aperture_diameter']):.2f} mm aperture / "
                f"{float(face_gasket['height_z']):.2f} mm gasket / "
                f"{float(face_gasket['nominal_compression_z']):.2f} mm "
                "compression"
            ),
            physical_check="face gasket centered and dry-side aperture face sealed",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="IR proxy FOV spot",
            cad_value=str(ir_fov_spot["spot_cad_value"]),
            physical_check=(
                "proxy only; edge-to-center plan required before cell-temperature claims"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Harness route count",
            cad_value=(
                f"{int(harness['lower_ir_route_count'])} lower / "
                f"{int(harness['lid_sensor_route_count'])} lid routes"
            ),
            physical_check="covered routes keep wires out of wet chamber and pipette field",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Service connectors/cables",
            cad_value=str(mating_state_check["cad_value"]),
            physical_check="continuity survives five install/remove service cycles",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Sensor connector service clearance",
            cad_value=str(connector_clearance_check["cad_value"]),
            physical_check=(
                "required connector clearance body stays open through mating "
                "and cable service"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Service cable envelope",
            cad_value=str(cable_envelope_check["cad_value"]),
            physical_check="row-end cable dress stays in modeled +Y envelope",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Service cable bend envelope",
            cad_value=str(cable_envelope_check["bend_cad_value"]),
            physical_check="external cable dress does not kink or pull connector shrouds",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Observer front-end swept volume",
            cad_value=str(observer_front_end["cad_value"]),
            physical_check=(
                "required front-end swept body clears apertures and focus travel"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Observer carriage reserved volume",
            cad_value=str(observer_carriage["cad_value"]),
            physical_check=(
                "required carriage envelope stays outside wet stack and pipette field"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Observer service raceway envelope",
            cad_value=str(observer_service_raceway["cad_value"]),
            physical_check=(
                "required service raceway body keeps observer loop out of wet chamber"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Observer optical stability evidence",
            cad_value=str(observer_optical_stability["cad_value"]),
            physical_check=(
                "do not claim observer imaging/Raman quality until every optical "
                "checkpoint has evidence"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Observer kinematic split evidence",
            cad_value=str(observer_kinematic_split["cad_value"]),
            physical_check=(
                "front-end, carriage, focus travel, and service loop split must "
                "be evidenced before observer readiness claims"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Thermal proxy plan",
            cad_value=str(thermal_proxy["cad_value"]),
            physical_check=(
                "center-to-edge correlation and condensation pocket inspection plan "
                "required before cell-temperature claims"
            ),
        ),
    )


def first_print_sensor_thermal_targets_markdown(params: dict[str, Any]) -> str:
    targets = first_print_gate6_sensor_thermal_targets(params)
    lines = [
        "## Gate 6 CAD Sensor/Thermal Targets",
        "",
        "These are CAD targets for sensor installation and first thermal-proxy",
        "planning. They do not mark Gate 6 passed and do not prove gas response,",
        "RH response, CO2 control, IR calibration, or biology readiness.",
        "",
        "| Target | CAD/protocol value | Physical check |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| {target.target} | {target.cad_value} | {target.physical_check} |"
        for target in targets
    )
    return "\n".join(lines)


def first_print_cad_target_sections_markdown(
    params: dict[str, Any],
) -> dict[str, str]:
    return {
        "Gate 1 CAD Target Bounds": first_print_qc_target_bounds_markdown(params),
        "Gate 2 CAD Dry Assembly Targets": first_print_dry_assembly_targets_markdown(
            params
        ),
        "Gate 3 CAD Placement Targets": first_print_ot2_placement_targets_markdown(
            params
        ),
        "Gate 4 CAD Wet/Dry Witness Targets": (
            first_print_wet_dry_witness_targets_markdown(params)
        ),
        "Gate 5 CAD Consumable/Puncture Targets": (
            first_print_consumable_puncture_targets_markdown(params)
        ),
        "Gate 6 CAD Sensor/Thermal Targets": (
            first_print_sensor_thermal_targets_markdown(params)
        ),
    }


def first_print_gate1_qc_worksheet_rows(
    params: dict[str, Any],
) -> tuple[FirstPrintGate1QCWorksheetRow, ...]:
    return tuple(
        FirstPrintGate1QCWorksheetRow(
            part=target.name,
            source=target.category,
            target_x_mm=target.target_x_mm,
            target_y_mm=target.target_y_mm,
            target_z_mm=target.target_z_mm,
        )
        for target in first_print_qc_targets(params)
    )


def _first_print_gate1_qc_worksheet_csv_from_rows(
    rows: tuple[FirstPrintGate1QCWorksheetRow, ...],
) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_GATE1_QC_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "part": row.part,
                "source": row.source,
                "target_x_mm": f"{row.target_x_mm:.2f}",
                "target_y_mm": f"{row.target_y_mm:.2f}",
                "target_z_mm": f"{row.target_z_mm:.2f}",
                "measured_x_mm": row.measured_x_mm,
                "measured_y_mm": row.measured_y_mm,
                "measured_z_mm": row.measured_z_mm,
                "evidence_path": row.evidence_path,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def first_print_gate1_qc_worksheet_csv(params: dict[str, Any]) -> str:
    return _first_print_gate1_qc_worksheet_csv_from_rows(
        first_print_gate1_qc_worksheet_rows(params)
    )


def first_print_y_split_gate1_qc_worksheet_rows(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
) -> tuple[FirstPrintGate1QCWorksheetRow, ...]:
    manifest_rows = first_print_gate1_qc_rows_from_slicer_queue_manifest(queue_dir)
    if manifest_rows:
        return manifest_rows

    split_path = Path(split_dir)
    rows: list[FirstPrintGate1QCWorksheetRow] = []
    for item in first_print_y_split_slicer_queue_items(
        params=params,
        out_dir=out_dir,
        split_dir=split_path,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
    ):
        source = "printed_split" if item.source_stl_path.parent == split_path else "printed"
        rows.append(
            FirstPrintGate1QCWorksheetRow(
                part=item.name,
                source=source,
                target_x_mm=item.target_x_mm,
                target_y_mm=item.target_y_mm,
                target_z_mm=item.target_z_mm,
            )
        )
    return tuple(rows)


def first_print_y_split_gate1_qc_worksheet_csv(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
) -> str:
    return _first_print_gate1_qc_worksheet_csv_from_rows(
        first_print_y_split_gate1_qc_worksheet_rows(
            params=params,
            out_dir=out_dir,
            split_dir=split_dir,
            queue_dir=queue_dir,
            slicer_setup_path=slicer_setup_path,
        )
    )


def _parse_gate1_float(value: str) -> float | None:
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _gate1_issue(
    issues: list[FirstPrintGate1QCWorksheetIssue],
    *,
    part: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate1QCWorksheetIssue(part=part, field=field, message=message)
    )


def _gate1_measurement_fields_filled(row: dict[str, str]) -> tuple[str, ...]:
    fields = ("measured_x_mm", "measured_y_mm", "measured_z_mm")
    return tuple(field for field in fields if row.get(field, "").strip())


def _resolve_worksheet_evidence_path(
    *,
    worksheet_path: Path,
    evidence_path: str,
) -> Path:
    path = Path(evidence_path)
    if path.is_absolute() or path.exists():
        return path
    return worksheet_path.parent / path


def _worksheet_evidence_file_error(
    *,
    worksheet_path: Path,
    evidence_path: str,
    evidence_label: str = "evidence",
) -> str:
    evidence_file = _resolve_worksheet_evidence_path(
        worksheet_path=worksheet_path,
        evidence_path=evidence_path,
    )
    if not evidence_file.exists():
        return f"{evidence_label} path does not exist"
    if not evidence_file.is_file():
        return f"{evidence_label} path is not a file"
    if evidence_file.stat().st_size <= 0:
        return f"{evidence_label} file is empty"
    return ""


def audit_first_print_gate1_qc_worksheet(
    *,
    params: dict[str, Any],
    worksheet_path: str | Path,
    tolerance_mm: float = FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM,
) -> FirstPrintGate1QCWorksheetAudit:
    return _audit_first_print_gate1_qc_worksheet_from_expected_rows(
        worksheet_path=Path(worksheet_path),
        expected_rows=first_print_gate1_qc_worksheet_rows(params),
        tolerance_mm=tolerance_mm,
    )


def audit_first_print_y_split_gate1_qc_worksheet(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    worksheet_path: str | Path,
    tolerance_mm: float = FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM,
) -> FirstPrintGate1QCWorksheetAudit:
    return _audit_first_print_gate1_qc_worksheet_from_expected_rows(
        worksheet_path=Path(worksheet_path),
        expected_rows=first_print_y_split_gate1_qc_worksheet_rows(
            params=params,
            out_dir=out_dir,
            split_dir=split_dir,
            queue_dir=queue_dir,
            slicer_setup_path=slicer_setup_path,
        ),
        tolerance_mm=tolerance_mm,
    )


def _audit_first_print_gate1_qc_worksheet_from_expected_rows(
    *,
    worksheet_path: Path,
    expected_rows: tuple[FirstPrintGate1QCWorksheetRow, ...],
    tolerance_mm: float,
) -> FirstPrintGate1QCWorksheetAudit:
    path = Path(worksheet_path)
    expected_by_part = {row.part: row for row in expected_rows}
    issues: list[FirstPrintGate1QCWorksheetIssue] = []
    if not path.exists():
        _gate1_issue(
            issues,
            part="worksheet",
            field="path",
            message="worksheet file does not exist",
        )
        return FirstPrintGate1QCWorksheetAudit(
            worksheet_path=path,
            tolerance_mm=tolerance_mm,
            expected_row_count=len(expected_by_part),
            actual_row_count=0,
            result_counts={},
            missing_parts=tuple(expected_by_part),
            extra_parts=(),
            duplicate_parts=(),
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_GATE1_QC_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_GATE1_QC_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _gate1_issue(
            issues,
            part="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _gate1_issue(
            issues,
            part="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    result_counts = Counter(row.get("result", "").strip() for row in rows)
    part_counts = Counter(row.get("part", "").strip() for row in rows)
    actual_parts = {part for part in part_counts if part}
    expected_parts = set(expected_by_part)
    missing_parts = tuple(
        part for part in expected_by_part if part not in actual_parts
    )
    extra_parts = tuple(sorted(part for part in actual_parts if part not in expected_parts))
    duplicate_parts = tuple(
        sorted(part for part, count in part_counts.items() if part and count > 1)
    )

    for part in missing_parts:
        _gate1_issue(
            issues,
            part=part,
            field="part",
            message="expected worksheet row is missing",
        )
    for part in extra_parts:
        _gate1_issue(
            issues,
            part=part,
            field="part",
            message="worksheet row is not an expected production QC target",
        )
    for part in duplicate_parts:
        _gate1_issue(
            issues,
            part=part,
            field="part",
            message="duplicate worksheet row",
        )

    for index, row in enumerate(rows, start=2):
        if None in row:
            _gate1_issue(
                issues,
                part=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        part = row.get("part", "").strip()
        if not part:
            _gate1_issue(
                issues,
                part=f"line {index}",
                field="part",
                message="part is blank",
            )
            continue
        expected = expected_by_part.get(part)
        if expected is None:
            continue

        source = row.get("source", "").strip()
        if source != expected.source:
            _gate1_issue(
                issues,
                part=part,
                field="source",
                message=f"expected {expected.source}, found {source or 'blank'}",
            )

        for field, target_value in (
            ("target_x_mm", expected.target_x_mm),
            ("target_y_mm", expected.target_y_mm),
            ("target_z_mm", expected.target_z_mm),
        ):
            observed = _parse_gate1_float(row.get(field, ""))
            if observed is None:
                _gate1_issue(
                    issues,
                    part=part,
                    field=field,
                    message="target value is blank or nonnumeric",
                )
            elif abs(observed - target_value) > 0.005:
                _gate1_issue(
                    issues,
                    part=part,
                    field=field,
                    message=f"expected {target_value:.2f}, found {observed:.2f}",
                )

        result = row.get("result", "").strip()
        if result not in FIRST_PRINT_GATE1_QC_RESULT_VALUES:
            _gate1_issue(
                issues,
                part=part,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
            continue

        filled_measurements = _gate1_measurement_fields_filled(row)
        evidence_path = row.get("evidence_path", "").strip()
        if result == "not_tested" and (filled_measurements or evidence_path):
            _gate1_issue(
                issues,
                part=part,
                field="result",
                message="not_tested row must not contain measured values or evidence",
            )
        if filled_measurements and len(filled_measurements) != 3:
            _gate1_issue(
                issues,
                part=part,
                field="measured_*_mm",
                message="measurement vector is partially filled",
            )
        if result != "pass":
            continue

        if len(filled_measurements) != 3:
            _gate1_issue(
                issues,
                part=part,
                field="measured_*_mm",
                message="pass row requires measured X/Y/Z values",
            )
            continue

        if not evidence_path:
            _gate1_issue(
                issues,
                part=part,
                field="evidence_path",
                message="pass row requires physical print-QC evidence",
            )
        else:
            evidence_error = _worksheet_evidence_file_error(
                worksheet_path=path,
                evidence_path=evidence_path,
            )
            if evidence_error:
                _gate1_issue(
                    issues,
                    part=part,
                    field="evidence_path",
                    message=evidence_error,
                )

        for field, target_value in (
            ("measured_x_mm", expected.target_x_mm),
            ("measured_y_mm", expected.target_y_mm),
            ("measured_z_mm", expected.target_z_mm),
        ):
            measured = _parse_gate1_float(row.get(field, ""))
            if measured is None:
                _gate1_issue(
                    issues,
                    part=part,
                    field=field,
                    message="measured value is nonnumeric",
                )
            elif abs(measured - target_value) > tolerance_mm:
                _gate1_issue(
                    issues,
                    part=part,
                    field=field,
                    message=(
                        f"pass exceeds +/- {tolerance_mm:.2f} mm tolerance: "
                        f"target {target_value:.2f}, measured {measured:.2f}"
                    ),
                )

    return FirstPrintGate1QCWorksheetAudit(
        worksheet_path=path,
        tolerance_mm=tolerance_mm,
        expected_row_count=len(expected_by_part),
        actual_row_count=len(rows),
        result_counts=dict(result_counts),
        missing_parts=missing_parts,
        extra_parts=extra_parts,
        duplicate_parts=duplicate_parts,
        issues=tuple(issues),
    )


def first_print_gate2_dry_assembly_worksheet_rows(
    params: dict[str, Any],
) -> tuple[FirstPrintGate2DryAssemblyWorksheetRow, ...]:
    return tuple(
        FirstPrintGate2DryAssemblyWorksheetRow(
            target=target.target,
            cad_value=target.cad_value,
            physical_check=target.physical_check,
        )
        for target in first_print_gate2_dry_assembly_targets(params)
    )


def first_print_gate2_dry_assembly_worksheet_csv(params: dict[str, Any]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_GATE2_DRY_ASSEMBLY_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in first_print_gate2_dry_assembly_worksheet_rows(params):
        writer.writerow(
            {
                "target": row.target,
                "cad_value": row.cad_value,
                "physical_check": row.physical_check,
                "measured_value": row.measured_value,
                "evidence_path": row.evidence_path,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def _gate2_dry_assembly_issue(
    issues: list[FirstPrintGate2DryAssemblyWorksheetIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate2DryAssemblyWorksheetIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_gate2_dry_assembly_worksheet(
    *,
    params: dict[str, Any],
    worksheet_path: str | Path,
) -> FirstPrintGate2DryAssemblyWorksheetAudit:
    path = Path(worksheet_path)
    expected_rows = {
        row.target: row
        for row in first_print_gate2_dry_assembly_worksheet_rows(params)
    }
    issues: list[FirstPrintGate2DryAssemblyWorksheetIssue] = []
    if not path.exists():
        _gate2_dry_assembly_issue(
            issues,
            target="worksheet",
            field="path",
            message="Gate 2 dry assembly worksheet file does not exist",
        )
        return FirstPrintGate2DryAssemblyWorksheetAudit(
            worksheet_path=path,
            expected_row_count=len(expected_rows),
            actual_row_count=0,
            result_counts={},
            missing_targets=tuple(expected_rows),
            extra_targets=(),
            duplicate_targets=(),
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_GATE2_DRY_ASSEMBLY_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_GATE2_DRY_ASSEMBLY_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _gate2_dry_assembly_issue(
            issues,
            target="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _gate2_dry_assembly_issue(
            issues,
            target="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    result_counts = Counter(row.get("result", "").strip() for row in rows)
    target_counts = Counter(row.get("target", "").strip() for row in rows)
    actual_targets = {target for target in target_counts if target}
    expected_targets = set(expected_rows)
    missing_targets = tuple(
        target for target in expected_rows if target not in actual_targets
    )
    extra_targets = tuple(
        sorted(target for target in actual_targets if target not in expected_targets)
    )
    duplicate_targets = tuple(
        sorted(
            target
            for target, count in target_counts.items()
            if target and count > 1
        )
    )

    for target in missing_targets:
        _gate2_dry_assembly_issue(
            issues,
            target=target,
            field="target",
            message="expected dry assembly worksheet row is missing",
        )
    for target in extra_targets:
        _gate2_dry_assembly_issue(
            issues,
            target=target,
            field="target",
            message="worksheet row is not an expected Gate 2 dry assembly target",
        )
    for target in duplicate_targets:
        _gate2_dry_assembly_issue(
            issues,
            target=target,
            field="target",
            message="duplicate worksheet row",
        )

    for index, row in enumerate(rows, start=2):
        if None in row:
            _gate2_dry_assembly_issue(
                issues,
                target=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        target = row.get("target", "").strip()
        if not target:
            _gate2_dry_assembly_issue(
                issues,
                target=f"line {index}",
                field="target",
                message="target is blank",
            )
            continue
        expected = expected_rows.get(target)
        if expected is None:
            continue

        for field, expected_value in (
            ("cad_value", expected.cad_value),
            ("physical_check", expected.physical_check),
        ):
            observed = row.get(field, "").strip()
            if observed != expected_value:
                _gate2_dry_assembly_issue(
                    issues,
                    target=target,
                    field=field,
                    message=f"expected {expected_value}, found {observed or 'blank'}",
                )

        result = row.get("result", "").strip()
        if result not in FIRST_PRINT_GATE2_DRY_ASSEMBLY_RESULT_VALUES:
            _gate2_dry_assembly_issue(
                issues,
                target=target,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
            continue

        measured_value = row.get("measured_value", "").strip()
        evidence_path = row.get("evidence_path", "").strip()
        if result == "not_tested" and (measured_value or evidence_path):
            _gate2_dry_assembly_issue(
                issues,
                target=target,
                field="result",
                message="not_tested row must not contain measured evidence",
            )
        if result != "pass":
            continue

        if not measured_value:
            _gate2_dry_assembly_issue(
                issues,
                target=target,
                field="measured_value",
                message="pass row requires a measured value or observation",
            )
        if not evidence_path:
            _gate2_dry_assembly_issue(
                issues,
                target=target,
                field="evidence_path",
                message="pass row requires a photo, log, or measurement evidence path",
            )
        else:
            evidence_error = _worksheet_evidence_file_error(
                worksheet_path=path,
                evidence_path=evidence_path,
            )
            if evidence_error:
                _gate2_dry_assembly_issue(
                    issues,
                    target=target,
                    field="evidence_path",
                    message=evidence_error,
                )

    return FirstPrintGate2DryAssemblyWorksheetAudit(
        worksheet_path=path,
        expected_row_count=len(expected_rows),
        actual_row_count=len(rows),
        result_counts=dict(result_counts),
        missing_targets=missing_targets,
        extra_targets=extra_targets,
        duplicate_targets=duplicate_targets,
        issues=tuple(issues),
    )


def first_print_gate3_placement_worksheet_rows(
    params: dict[str, Any],
) -> tuple[FirstPrintGate3PlacementWorksheetRow, ...]:
    return tuple(
        FirstPrintGate3PlacementWorksheetRow(
            target=target.target,
            cad_value=target.cad_value,
            physical_check=target.physical_check,
        )
        for target in first_print_gate3_placement_targets(params)
    )


def first_print_gate3_placement_worksheet_csv(params: dict[str, Any]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_GATE3_PLACEMENT_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in first_print_gate3_placement_worksheet_rows(params):
        writer.writerow(
            {
                "target": row.target,
                "cad_value": row.cad_value,
                "physical_check": row.physical_check,
                "measured_value": row.measured_value,
                "evidence_path": row.evidence_path,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def _gate3_placement_issue(
    issues: list[FirstPrintGate3PlacementWorksheetIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate3PlacementWorksheetIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_gate3_placement_worksheet(
    *,
    params: dict[str, Any],
    worksheet_path: str | Path,
) -> FirstPrintGate3PlacementWorksheetAudit:
    path = Path(worksheet_path)
    expected_rows = {
        row.target: row for row in first_print_gate3_placement_worksheet_rows(params)
    }
    issues: list[FirstPrintGate3PlacementWorksheetIssue] = []
    if not path.exists():
        _gate3_placement_issue(
            issues,
            target="worksheet",
            field="path",
            message="Gate 3 placement worksheet file does not exist",
        )
        return FirstPrintGate3PlacementWorksheetAudit(
            worksheet_path=path,
            expected_row_count=len(expected_rows),
            actual_row_count=0,
            result_counts={},
            missing_targets=tuple(expected_rows),
            extra_targets=(),
            duplicate_targets=(),
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_GATE3_PLACEMENT_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_GATE3_PLACEMENT_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _gate3_placement_issue(
            issues,
            target="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _gate3_placement_issue(
            issues,
            target="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    result_counts = Counter(row.get("result", "").strip() for row in rows)
    target_counts = Counter(row.get("target", "").strip() for row in rows)
    actual_targets = {target for target in target_counts if target}
    expected_targets = set(expected_rows)
    missing_targets = tuple(
        target for target in expected_rows if target not in actual_targets
    )
    extra_targets = tuple(
        sorted(target for target in actual_targets if target not in expected_targets)
    )
    duplicate_targets = tuple(
        sorted(
            target
            for target, count in target_counts.items()
            if target and count > 1
        )
    )

    for target in missing_targets:
        _gate3_placement_issue(
            issues,
            target=target,
            field="target",
            message="expected placement worksheet row is missing",
        )
    for target in extra_targets:
        _gate3_placement_issue(
            issues,
            target=target,
            field="target",
            message="worksheet row is not an expected Gate 3 placement target",
        )
    for target in duplicate_targets:
        _gate3_placement_issue(
            issues,
            target=target,
            field="target",
            message="duplicate worksheet row",
        )

    for index, row in enumerate(rows, start=2):
        if None in row:
            _gate3_placement_issue(
                issues,
                target=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        target = row.get("target", "").strip()
        if not target:
            _gate3_placement_issue(
                issues,
                target=f"line {index}",
                field="target",
                message="target is blank",
            )
            continue
        expected = expected_rows.get(target)
        if expected is None:
            continue

        for field, expected_value in (
            ("cad_value", expected.cad_value),
            ("physical_check", expected.physical_check),
        ):
            observed = row.get(field, "").strip()
            if observed != expected_value:
                _gate3_placement_issue(
                    issues,
                    target=target,
                    field=field,
                    message=f"expected {expected_value}, found {observed or 'blank'}",
                )

        result = row.get("result", "").strip()
        if result not in FIRST_PRINT_GATE3_PLACEMENT_RESULT_VALUES:
            _gate3_placement_issue(
                issues,
                target=target,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
            continue

        measured_value = row.get("measured_value", "").strip()
        evidence_path = row.get("evidence_path", "").strip()
        if result == "not_tested" and (measured_value or evidence_path):
            _gate3_placement_issue(
                issues,
                target=target,
                field="result",
                message="not_tested row must not contain measured evidence",
            )
        if result != "pass":
            continue

        if not measured_value:
            _gate3_placement_issue(
                issues,
                target=target,
                field="measured_value",
                message="pass row requires a measured value or observation",
            )
        if not evidence_path:
            _gate3_placement_issue(
                issues,
                target=target,
                field="evidence_path",
                message="pass row requires a photo, log, or measurement evidence path",
            )
        else:
            evidence_error = _worksheet_evidence_file_error(
                worksheet_path=path,
                evidence_path=evidence_path,
            )
            if evidence_error:
                _gate3_placement_issue(
                    issues,
                    target=target,
                    field="evidence_path",
                    message=evidence_error,
                )

    return FirstPrintGate3PlacementWorksheetAudit(
        worksheet_path=path,
        expected_row_count=len(expected_rows),
        actual_row_count=len(rows),
        result_counts=dict(result_counts),
        missing_targets=missing_targets,
        extra_targets=extra_targets,
        duplicate_targets=duplicate_targets,
        issues=tuple(issues),
    )


def first_print_gate4_wet_dry_witness_worksheet_rows(
    params: dict[str, Any],
) -> tuple[FirstPrintGate4WetDryWitnessWorksheetRow, ...]:
    return tuple(
        FirstPrintGate4WetDryWitnessWorksheetRow(
            target=target.target,
            cad_value=target.cad_value,
            physical_check=target.physical_check,
        )
        for target in first_print_gate4_wet_dry_witness_targets(params)
    )


def first_print_gate4_wet_dry_witness_worksheet_csv(params: dict[str, Any]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_GATE4_WET_DRY_WITNESS_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in first_print_gate4_wet_dry_witness_worksheet_rows(params):
        writer.writerow(
            {
                "target": row.target,
                "cad_value": row.cad_value,
                "physical_check": row.physical_check,
                "measured_value": row.measured_value,
                "evidence_path": row.evidence_path,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def _gate4_wet_dry_witness_issue(
    issues: list[FirstPrintGate4WetDryWitnessWorksheetIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate4WetDryWitnessWorksheetIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_gate4_wet_dry_witness_worksheet(
    *,
    params: dict[str, Any],
    worksheet_path: str | Path,
) -> FirstPrintGate4WetDryWitnessWorksheetAudit:
    path = Path(worksheet_path)
    expected_rows = {
        row.target: row
        for row in first_print_gate4_wet_dry_witness_worksheet_rows(params)
    }
    issues: list[FirstPrintGate4WetDryWitnessWorksheetIssue] = []
    if not path.exists():
        _gate4_wet_dry_witness_issue(
            issues,
            target="worksheet",
            field="path",
            message="Gate 4 wet/dry witness worksheet file does not exist",
        )
        return FirstPrintGate4WetDryWitnessWorksheetAudit(
            worksheet_path=path,
            expected_row_count=len(expected_rows),
            actual_row_count=0,
            result_counts={},
            missing_targets=tuple(expected_rows),
            extra_targets=(),
            duplicate_targets=(),
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_GATE4_WET_DRY_WITNESS_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_GATE4_WET_DRY_WITNESS_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _gate4_wet_dry_witness_issue(
            issues,
            target="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _gate4_wet_dry_witness_issue(
            issues,
            target="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    result_counts = Counter(row.get("result", "").strip() for row in rows)
    target_counts = Counter(row.get("target", "").strip() for row in rows)
    actual_targets = {target for target in target_counts if target}
    expected_targets = set(expected_rows)
    missing_targets = tuple(
        target for target in expected_rows if target not in actual_targets
    )
    extra_targets = tuple(
        sorted(target for target in actual_targets if target not in expected_targets)
    )
    duplicate_targets = tuple(
        sorted(
            target
            for target, count in target_counts.items()
            if target and count > 1
        )
    )

    for target in missing_targets:
        _gate4_wet_dry_witness_issue(
            issues,
            target=target,
            field="target",
            message="expected wet/dry worksheet row is missing",
        )
    for target in extra_targets:
        _gate4_wet_dry_witness_issue(
            issues,
            target=target,
            field="target",
            message="worksheet row is not an expected Gate 4 wet/dry target",
        )
    for target in duplicate_targets:
        _gate4_wet_dry_witness_issue(
            issues,
            target=target,
            field="target",
            message="duplicate worksheet row",
        )

    for index, row in enumerate(rows, start=2):
        if None in row:
            _gate4_wet_dry_witness_issue(
                issues,
                target=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        target = row.get("target", "").strip()
        if not target:
            _gate4_wet_dry_witness_issue(
                issues,
                target=f"line {index}",
                field="target",
                message="target is blank",
            )
            continue
        expected = expected_rows.get(target)
        if expected is None:
            continue

        for field, expected_value in (
            ("cad_value", expected.cad_value),
            ("physical_check", expected.physical_check),
        ):
            observed = row.get(field, "").strip()
            if observed != expected_value:
                _gate4_wet_dry_witness_issue(
                    issues,
                    target=target,
                    field=field,
                    message=f"expected {expected_value}, found {observed or 'blank'}",
                )

        result = row.get("result", "").strip()
        if result not in FIRST_PRINT_GATE4_WET_DRY_WITNESS_RESULT_VALUES:
            _gate4_wet_dry_witness_issue(
                issues,
                target=target,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
            continue

        measured_value = row.get("measured_value", "").strip()
        evidence_path = row.get("evidence_path", "").strip()
        if result == "not_tested" and (measured_value or evidence_path):
            _gate4_wet_dry_witness_issue(
                issues,
                target=target,
                field="result",
                message="not_tested row must not contain measured evidence",
            )
        if result != "pass":
            continue

        if not measured_value:
            _gate4_wet_dry_witness_issue(
                issues,
                target=target,
                field="measured_value",
                message="pass row requires a measured value or observation",
            )
        if not evidence_path:
            _gate4_wet_dry_witness_issue(
                issues,
                target=target,
                field="evidence_path",
                message="pass row requires a photo, log, or measurement evidence path",
            )
        else:
            evidence_error = _worksheet_evidence_file_error(
                worksheet_path=path,
                evidence_path=evidence_path,
            )
            if evidence_error:
                _gate4_wet_dry_witness_issue(
                    issues,
                    target=target,
                    field="evidence_path",
                    message=evidence_error,
                )

    return FirstPrintGate4WetDryWitnessWorksheetAudit(
        worksheet_path=path,
        expected_row_count=len(expected_rows),
        actual_row_count=len(rows),
        result_counts=dict(result_counts),
        missing_targets=missing_targets,
        extra_targets=extra_targets,
        duplicate_targets=duplicate_targets,
        issues=tuple(issues),
    )


def first_print_gate5_consumable_puncture_worksheet_rows(
    params: dict[str, Any],
) -> tuple[FirstPrintGate5ConsumablePunctureWorksheetRow, ...]:
    return tuple(
        FirstPrintGate5ConsumablePunctureWorksheetRow(
            target=target.target,
            cad_value=target.cad_value,
            physical_check=target.physical_check,
        )
        for target in first_print_gate5_consumable_puncture_targets(params)
    )


def first_print_gate5_consumable_puncture_worksheet_csv(
    params: dict[str, Any],
) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_GATE5_CONSUMABLE_PUNCTURE_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in first_print_gate5_consumable_puncture_worksheet_rows(params):
        writer.writerow(
            {
                "target": row.target,
                "cad_value": row.cad_value,
                "physical_check": row.physical_check,
                "measured_value": row.measured_value,
                "evidence_path": row.evidence_path,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def _gate5_consumable_puncture_issue(
    issues: list[FirstPrintGate5ConsumablePunctureWorksheetIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate5ConsumablePunctureWorksheetIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_gate5_consumable_puncture_worksheet(
    *,
    params: dict[str, Any],
    worksheet_path: str | Path,
) -> FirstPrintGate5ConsumablePunctureWorksheetAudit:
    path = Path(worksheet_path)
    expected_rows = {
        row.target: row
        for row in first_print_gate5_consumable_puncture_worksheet_rows(params)
    }
    issues: list[FirstPrintGate5ConsumablePunctureWorksheetIssue] = []
    if not path.exists():
        _gate5_consumable_puncture_issue(
            issues,
            target="worksheet",
            field="path",
            message="Gate 5 consumable/puncture worksheet file does not exist",
        )
        return FirstPrintGate5ConsumablePunctureWorksheetAudit(
            worksheet_path=path,
            expected_row_count=len(expected_rows),
            actual_row_count=0,
            result_counts={},
            missing_targets=tuple(expected_rows),
            extra_targets=(),
            duplicate_targets=(),
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_GATE5_CONSUMABLE_PUNCTURE_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_GATE5_CONSUMABLE_PUNCTURE_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _gate5_consumable_puncture_issue(
            issues,
            target="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _gate5_consumable_puncture_issue(
            issues,
            target="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    result_counts = Counter(row.get("result", "").strip() for row in rows)
    target_counts = Counter(row.get("target", "").strip() for row in rows)
    actual_targets = {target for target in target_counts if target}
    expected_targets = set(expected_rows)
    missing_targets = tuple(
        target for target in expected_rows if target not in actual_targets
    )
    extra_targets = tuple(
        sorted(target for target in actual_targets if target not in expected_targets)
    )
    duplicate_targets = tuple(
        sorted(
            target
            for target, count in target_counts.items()
            if target and count > 1
        )
    )

    for target in missing_targets:
        _gate5_consumable_puncture_issue(
            issues,
            target=target,
            field="target",
            message="expected consumable/puncture worksheet row is missing",
        )
    for target in extra_targets:
        _gate5_consumable_puncture_issue(
            issues,
            target=target,
            field="target",
            message="worksheet row is not an expected Gate 5 consumable target",
        )
    for target in duplicate_targets:
        _gate5_consumable_puncture_issue(
            issues,
            target=target,
            field="target",
            message="duplicate worksheet row",
        )

    for index, row in enumerate(rows, start=2):
        if None in row:
            _gate5_consumable_puncture_issue(
                issues,
                target=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        target = row.get("target", "").strip()
        if not target:
            _gate5_consumable_puncture_issue(
                issues,
                target=f"line {index}",
                field="target",
                message="target is blank",
            )
            continue
        expected = expected_rows.get(target)
        if expected is None:
            continue

        for field, expected_value in (
            ("cad_value", expected.cad_value),
            ("physical_check", expected.physical_check),
        ):
            observed = row.get(field, "").strip()
            if observed != expected_value:
                _gate5_consumable_puncture_issue(
                    issues,
                    target=target,
                    field=field,
                    message=f"expected {expected_value}, found {observed or 'blank'}",
                )

        result = row.get("result", "").strip()
        if result not in FIRST_PRINT_GATE5_CONSUMABLE_PUNCTURE_RESULT_VALUES:
            _gate5_consumable_puncture_issue(
                issues,
                target=target,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
            continue

        measured_value = row.get("measured_value", "").strip()
        evidence_path = row.get("evidence_path", "").strip()
        if result == "not_tested" and (measured_value or evidence_path):
            _gate5_consumable_puncture_issue(
                issues,
                target=target,
                field="result",
                message="not_tested row must not contain measured evidence",
            )
        if result != "pass":
            continue

        if not measured_value:
            _gate5_consumable_puncture_issue(
                issues,
                target=target,
                field="measured_value",
                message="pass row requires a measured value or observation",
            )
        if not evidence_path:
            _gate5_consumable_puncture_issue(
                issues,
                target=target,
                field="evidence_path",
                message="pass row requires a photo, log, or measurement evidence path",
            )
        else:
            evidence_error = _worksheet_evidence_file_error(
                worksheet_path=path,
                evidence_path=evidence_path,
            )
            if evidence_error:
                _gate5_consumable_puncture_issue(
                    issues,
                    target=target,
                    field="evidence_path",
                    message=evidence_error,
                )

    return FirstPrintGate5ConsumablePunctureWorksheetAudit(
        worksheet_path=path,
        expected_row_count=len(expected_rows),
        actual_row_count=len(rows),
        result_counts=dict(result_counts),
        missing_targets=missing_targets,
        extra_targets=extra_targets,
        duplicate_targets=duplicate_targets,
        issues=tuple(issues),
    )


def first_print_gate6_sensor_thermal_worksheet_rows(
    params: dict[str, Any],
) -> tuple[FirstPrintGate6SensorThermalWorksheetRow, ...]:
    return tuple(
        FirstPrintGate6SensorThermalWorksheetRow(
            target=target.target,
            cad_value=target.cad_value,
            physical_check=target.physical_check,
        )
        for target in first_print_gate6_sensor_thermal_targets(params)
    )


def first_print_gate6_sensor_thermal_worksheet_csv(
    params: dict[str, Any],
) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_GATE6_SENSOR_THERMAL_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in first_print_gate6_sensor_thermal_worksheet_rows(params):
        writer.writerow(
            {
                "target": row.target,
                "cad_value": row.cad_value,
                "physical_check": row.physical_check,
                "measured_value": row.measured_value,
                "evidence_path": row.evidence_path,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def _gate6_sensor_thermal_issue(
    issues: list[FirstPrintGate6SensorThermalWorksheetIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate6SensorThermalWorksheetIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_gate6_sensor_thermal_worksheet(
    *,
    params: dict[str, Any],
    worksheet_path: str | Path,
) -> FirstPrintGate6SensorThermalWorksheetAudit:
    path = Path(worksheet_path)
    expected_rows = {
        row.target: row for row in first_print_gate6_sensor_thermal_worksheet_rows(params)
    }
    issues: list[FirstPrintGate6SensorThermalWorksheetIssue] = []
    if not path.exists():
        _gate6_sensor_thermal_issue(
            issues,
            target="worksheet",
            field="path",
            message="Gate 6 sensor/thermal worksheet file does not exist",
        )
        return FirstPrintGate6SensorThermalWorksheetAudit(
            worksheet_path=path,
            expected_row_count=len(expected_rows),
            actual_row_count=0,
            result_counts={},
            missing_targets=tuple(expected_rows),
            extra_targets=(),
            duplicate_targets=(),
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_GATE6_SENSOR_THERMAL_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_GATE6_SENSOR_THERMAL_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _gate6_sensor_thermal_issue(
            issues,
            target="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _gate6_sensor_thermal_issue(
            issues,
            target="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    result_counts = Counter(row.get("result", "").strip() for row in rows)
    target_counts = Counter(row.get("target", "").strip() for row in rows)
    actual_targets = {target for target in target_counts if target}
    expected_targets = set(expected_rows)
    missing_targets = tuple(
        target for target in expected_rows if target not in actual_targets
    )
    extra_targets = tuple(
        sorted(target for target in actual_targets if target not in expected_targets)
    )
    duplicate_targets = tuple(
        sorted(
            target
            for target, count in target_counts.items()
            if target and count > 1
        )
    )

    for target in missing_targets:
        _gate6_sensor_thermal_issue(
            issues,
            target=target,
            field="target",
            message="expected sensor/thermal worksheet row is missing",
        )
    for target in extra_targets:
        _gate6_sensor_thermal_issue(
            issues,
            target=target,
            field="target",
            message="worksheet row is not an expected Gate 6 sensor/thermal target",
        )
    for target in duplicate_targets:
        _gate6_sensor_thermal_issue(
            issues,
            target=target,
            field="target",
            message="duplicate worksheet row",
        )

    for index, row in enumerate(rows, start=2):
        if None in row:
            _gate6_sensor_thermal_issue(
                issues,
                target=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        target = row.get("target", "").strip()
        if not target:
            _gate6_sensor_thermal_issue(
                issues,
                target=f"line {index}",
                field="target",
                message="target is blank",
            )
            continue
        expected = expected_rows.get(target)
        if expected is None:
            continue

        for field, expected_value in (
            ("cad_value", expected.cad_value),
            ("physical_check", expected.physical_check),
        ):
            observed = row.get(field, "").strip()
            if observed != expected_value:
                _gate6_sensor_thermal_issue(
                    issues,
                    target=target,
                    field=field,
                    message=f"expected {expected_value}, found {observed or 'blank'}",
                )

        result = row.get("result", "").strip()
        if result not in FIRST_PRINT_GATE6_SENSOR_THERMAL_RESULT_VALUES:
            _gate6_sensor_thermal_issue(
                issues,
                target=target,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
            continue

        measured_value = row.get("measured_value", "").strip()
        evidence_path = row.get("evidence_path", "").strip()
        if result == "not_tested" and (measured_value or evidence_path):
            _gate6_sensor_thermal_issue(
                issues,
                target=target,
                field="result",
                message="not_tested row must not contain measured evidence",
            )
        if result != "pass":
            continue

        if not measured_value:
            _gate6_sensor_thermal_issue(
                issues,
                target=target,
                field="measured_value",
                message="pass row requires a measured value or observation",
            )
        if not evidence_path:
            _gate6_sensor_thermal_issue(
                issues,
                target=target,
                field="evidence_path",
                message="pass row requires a photo, log, or measurement evidence path",
            )
        else:
            evidence_error = _worksheet_evidence_file_error(
                worksheet_path=path,
                evidence_path=evidence_path,
            )
            if evidence_error:
                _gate6_sensor_thermal_issue(
                    issues,
                    target=target,
                    field="evidence_path",
                    message=evidence_error,
                )

    return FirstPrintGate6SensorThermalWorksheetAudit(
        worksheet_path=path,
        expected_row_count=len(expected_rows),
        actual_row_count=len(rows),
        result_counts=dict(result_counts),
        missing_targets=missing_targets,
        extra_targets=extra_targets,
        duplicate_targets=duplicate_targets,
        issues=tuple(issues),
    )


def first_print_install_inventory_rows() -> tuple[FirstPrintInstallInventoryRow, ...]:
    manifest = row_coupon_part_manifest()["installed"]
    rows: list[FirstPrintInstallInventoryRow] = []
    for name, entry in manifest.items():
        source = artifact_category(entry["fabrication_source"])
        if source not in FIRST_PRINT_INSTALL_INVENTORY_CATEGORIES:
            continue
        rows.append(
            FirstPrintInstallInventoryRow(
                part=name,
                source=source,
                role=entry["role"],
                acceptable_item=FIRST_PRINT_INSTALL_INVENTORY_ACCEPTABLE_ITEMS[name],
                operating_requirement=(
                    _install_inventory_operating_requirement_for_source(source)
                ),
            )
        )
    return tuple(rows)


def first_print_install_inventory_csv() -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_INSTALL_INVENTORY_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in first_print_install_inventory_rows():
        writer.writerow(
            {
                "part": row.part,
                "source": row.source,
                "role": row.role,
                "acceptable_item": row.acceptable_item,
                "operating_requirement": row.operating_requirement,
                "item_identifier": row.item_identifier,
                "installed_as": row.installed_as,
                "evidence_path": row.evidence_path,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def write_first_print_install_inventory(
    *,
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(first_print_install_inventory_csv())
    return output


def _install_inventory_issue(
    issues: list[FirstPrintInstallInventoryIssue],
    *,
    part: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintInstallInventoryIssue(part=part, field=field, message=message)
    )


def _allowed_installed_as_for_source(source: str) -> frozenset[str]:
    if source == "cots_consumable":
        return frozenset({"real_part"})
    if source == "service_tubing":
        return frozenset({"real_part", "measured_replacement"})
    if source == "electronics_or_dimensional_blank":
        return frozenset({"real_part", "dimensional_blank"})
    return frozenset()


def _install_inventory_operating_requirement_for_source(source: str) -> str:
    if source == "cots_consumable":
        return "real_part required; dimensional blank not accepted"
    if source == "service_tubing":
        return "real_part or measured_replacement required with physical evidence"
    if source == "electronics_or_dimensional_blank":
        return (
            "dimensional_blank is dry-fit only through Gate 5; "
            "real_part required for Gate 6 and operating acceptance"
        )
    return "explicit operating install decision required"


def audit_first_print_install_inventory(
    *,
    worksheet_path: str | Path,
) -> FirstPrintInstallInventoryAudit:
    path = Path(worksheet_path)
    expected_rows = {row.part: row for row in first_print_install_inventory_rows()}
    issues: list[FirstPrintInstallInventoryIssue] = []
    if not path.exists():
        _install_inventory_issue(
            issues,
            part="worksheet",
            field="path",
            message="install inventory file does not exist",
        )
        return FirstPrintInstallInventoryAudit(
            worksheet_path=path,
            expected_row_count=len(expected_rows),
            actual_row_count=0,
            result_counts={},
            missing_parts=tuple(expected_rows),
            extra_parts=(),
            duplicate_parts=(),
            sensor_inventory_blank_parts=(),
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_INSTALL_INVENTORY_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_INSTALL_INVENTORY_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _install_inventory_issue(
            issues,
            part="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _install_inventory_issue(
            issues,
            part="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    result_counts = Counter(row.get("result", "").strip() for row in rows)
    part_counts = Counter(row.get("part", "").strip() for row in rows)
    actual_parts = {part for part in part_counts if part}
    expected_parts = set(expected_rows)
    missing_parts = tuple(part for part in expected_rows if part not in actual_parts)
    extra_parts = tuple(sorted(part for part in actual_parts if part not in expected_parts))
    duplicate_parts = tuple(
        sorted(part for part, count in part_counts.items() if part and count > 1)
    )
    sensor_inventory_blank_parts: list[str] = []

    for part in missing_parts:
        _install_inventory_issue(
            issues,
            part=part,
            field="part",
            message="expected install inventory row is missing",
        )
    for part in extra_parts:
        _install_inventory_issue(
            issues,
            part=part,
            field="part",
            message="install inventory row is not an expected nonprinted item",
        )
    for part in duplicate_parts:
        _install_inventory_issue(
            issues,
            part=part,
            field="part",
            message="duplicate install inventory row",
        )

    for index, row in enumerate(rows, start=2):
        if None in row:
            _install_inventory_issue(
                issues,
                part=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        part = row.get("part", "").strip()
        if not part:
            _install_inventory_issue(
                issues,
                part=f"line {index}",
                field="part",
                message="part is blank",
            )
            continue
        expected = expected_rows.get(part)
        if expected is None:
            continue

        for field, expected_value in (
            ("source", expected.source),
            ("role", expected.role),
            ("acceptable_item", expected.acceptable_item),
            ("operating_requirement", expected.operating_requirement),
        ):
            observed = row.get(field, "").strip()
            if observed != expected_value:
                _install_inventory_issue(
                    issues,
                    part=part,
                    field=field,
                    message=f"expected {expected_value}, found {observed or 'blank'}",
                )

        result = row.get("result", "").strip()
        if result not in FIRST_PRINT_INSTALL_INVENTORY_RESULT_VALUES:
            _install_inventory_issue(
                issues,
                part=part,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
            continue

        installed_as = row.get("installed_as", "").strip()
        if installed_as not in FIRST_PRINT_INSTALL_INVENTORY_INSTALLED_AS_VALUES:
            _install_inventory_issue(
                issues,
                part=part,
                field="installed_as",
                message=f"invalid installed_as {installed_as}",
            )
            continue

        if result != "pass":
            continue

        item_identifier = row.get("item_identifier", "").strip()
        if not item_identifier:
            _install_inventory_issue(
                issues,
                part=part,
                field="item_identifier",
                message="pass row requires a lot, serial, source, or blank identifier",
            )

        evidence_path = row.get("evidence_path", "").strip()
        if not evidence_path:
            _install_inventory_issue(
                issues,
                part=part,
                field="evidence_path",
                message=(
                    "pass row requires a physical evidence path for the "
                    "installed item or dimensional blank"
                ),
            )
        else:
            evidence_error = _worksheet_evidence_file_error(
                worksheet_path=path,
                evidence_path=evidence_path,
            )
            if evidence_error:
                _install_inventory_issue(
                    issues,
                    part=part,
                    field="evidence_path",
                    message=evidence_error,
                )

        allowed_installed_as = _allowed_installed_as_for_source(expected.source)
        if installed_as not in allowed_installed_as:
            allowed = ", ".join(sorted(allowed_installed_as))
            _install_inventory_issue(
                issues,
                part=part,
                field="installed_as",
                message=f"expected one of {allowed}, found {installed_as or 'blank'}",
            )

        if (
            expected.source == "electronics_or_dimensional_blank"
            and installed_as != "real_part"
        ):
            sensor_inventory_blank_parts.append(part)

        if installed_as == "dimensional_blank" and not row.get("notes", "").strip():
            _install_inventory_issue(
                issues,
                part=part,
                field="notes",
                message="dimensional blank pass requires mechanical-only note",
            )

    return FirstPrintInstallInventoryAudit(
        worksheet_path=path,
        expected_row_count=len(expected_rows),
        actual_row_count=len(rows),
        result_counts=dict(result_counts),
        missing_parts=missing_parts,
        extra_parts=extra_parts,
        duplicate_parts=duplicate_parts,
        sensor_inventory_blank_parts=tuple(sensor_inventory_blank_parts),
        issues=tuple(issues),
    )


def first_print_service_state_review_rows() -> tuple[FirstPrintServiceStateReviewRow, ...]:
    manifest = row_coupon_part_manifest()
    service_modes = manifest["service_modes"]
    review_modes = manifest["review_modes"]
    if set(FIRST_PRINT_SERVICE_STATE_ACCEPTANCE_GATES) != set(ROW_COUPON_SERVICE_MODES):
        raise ValueError("service-state acceptance gates must cover every viewer mode")
    rows: list[FirstPrintServiceStateReviewRow] = []
    for mode in ROW_COUPON_SERVICE_MODES:
        acceptance_gate = FIRST_PRINT_SERVICE_STATE_ACCEPTANCE_GATES[mode]
        if mode in service_modes:
            expectations = FIRST_PRINT_SERVICE_STATE_SERVICE_PART_EXPECTATIONS.get(
                mode,
                {},
            )
            rows.append(
                FirstPrintServiceStateReviewRow(
                    mode=mode,
                    mode_type="installed" if mode == "installed" else "service",
                    review_scope=service_modes[mode],
                    acceptance_gate=acceptance_gate,
                    expected_removed_parts=", ".join(
                        expectations.get("removed_parts", ())
                    ),
                    expected_review_parts=", ".join(
                        expectations.get("review_parts", ())
                    ),
                )
            )
            continue
        review = review_modes[mode]
        rows.append(
            FirstPrintServiceStateReviewRow(
                mode=mode,
                mode_type="negative_review",
                review_scope=review["role"],
                acceptance_gate=acceptance_gate,
                expected_removed_parts=", ".join(review["removed_parts"]),
                expected_review_parts=", ".join(review["review_parts"]),
            )
        )
    return tuple(rows)


def _service_state_parts_from_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _service_state_bounds_evidence_path(output_dir: str | Path, mode: str) -> Path:
    return Path(output_dir) / f"{mode}_plain_python_bounds.csv"


def first_print_service_state_bounds_evidence_rows(
    params: dict[str, Any],
    *,
    mode: str,
    installed_parts: dict[str, Any] | None = None,
) -> tuple[FirstPrintServiceStateBoundsEvidenceRow, ...]:
    expected_rows = {row.mode: row for row in first_print_service_state_review_rows()}
    expected = expected_rows[mode]
    base_parts = installed_parts or build_row_coupon_installed_parts(params)
    parts = build_row_coupon_service_parts_from_installed(
        params,
        installed_parts=base_parts,
        mode=mode,
    )
    part_names = set(parts)
    removed_parts = set(_service_state_parts_from_csv(expected.expected_removed_parts))
    review_parts = set(_service_state_parts_from_csv(expected.expected_review_parts))
    removed_parts_absent = (
        "not_applicable" if not removed_parts else str(not (removed_parts & part_names)).lower()
    )
    review_parts_present = (
        "not_applicable" if not review_parts else str(review_parts <= part_names).lower()
    )
    mode_checks_pass = removed_parts_absent != "false" and review_parts_present != "false"

    rows: list[FirstPrintServiceStateBoundsEvidenceRow] = []
    for part_name in sorted(parts):
        bb = parts[part_name].val().BoundingBox()
        positive_bounds = bb.xlen > 0 and bb.ylen > 0 and bb.zlen > 0
        rows.append(
            FirstPrintServiceStateBoundsEvidenceRow(
                mode=expected.mode,
                mode_type=expected.mode_type,
                review_scope=expected.review_scope,
                acceptance_gate=expected.acceptance_gate,
                part=part_name,
                x_min_mm=round(float(bb.xmin), 2),
                x_max_mm=round(float(bb.xmax), 2),
                x_len_mm=round(float(bb.xlen), 2),
                y_min_mm=round(float(bb.ymin), 2),
                y_max_mm=round(float(bb.ymax), 2),
                y_len_mm=round(float(bb.ylen), 2),
                z_min_mm=round(float(bb.zmin), 2),
                z_max_mm=round(float(bb.zmax), 2),
                z_len_mm=round(float(bb.zlen), 2),
                expected_removed_parts_absent=removed_parts_absent,
                expected_review_parts_present=review_parts_present,
                result="pass" if mode_checks_pass and positive_bounds else "block",
            )
        )
    return tuple(rows)


def first_print_service_state_bounds_evidence_csv(
    params: dict[str, Any],
    *,
    mode: str,
    installed_parts: dict[str, Any] | None = None,
) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_SERVICE_STATE_BOUNDS_EVIDENCE_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in first_print_service_state_bounds_evidence_rows(
        params,
        mode=mode,
        installed_parts=installed_parts,
    ):
        writer.writerow(
            {
                "mode": row.mode,
                "mode_type": row.mode_type,
                "review_scope": row.review_scope,
                "acceptance_gate": row.acceptance_gate,
                "part": row.part,
                "x_min_mm": f"{row.x_min_mm:.2f}",
                "x_max_mm": f"{row.x_max_mm:.2f}",
                "x_len_mm": f"{row.x_len_mm:.2f}",
                "y_min_mm": f"{row.y_min_mm:.2f}",
                "y_max_mm": f"{row.y_max_mm:.2f}",
                "y_len_mm": f"{row.y_len_mm:.2f}",
                "z_min_mm": f"{row.z_min_mm:.2f}",
                "z_max_mm": f"{row.z_max_mm:.2f}",
                "z_len_mm": f"{row.z_len_mm:.2f}",
                "expected_removed_parts_absent": row.expected_removed_parts_absent,
                "expected_review_parts_present": row.expected_review_parts_present,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def write_first_print_service_state_bounds_evidence(
    params: dict[str, Any],
    *,
    output_dir: str | Path,
    overwrite: bool = False,
) -> dict[str, Path]:
    output = Path(output_dir)
    paths = {
        mode: _service_state_bounds_evidence_path(output, mode)
        for mode in ROW_COUPON_SERVICE_MODES
    }
    if not overwrite:
        existing_paths = tuple(path for path in paths.values() if path.exists())
        if existing_paths:
            raise FileExistsError(existing_paths[0])

    output.mkdir(parents=True, exist_ok=True)
    installed_parts = build_row_coupon_installed_parts(params)
    for mode, path in paths.items():
        path.write_text(
            first_print_service_state_bounds_evidence_csv(
                params,
                mode=mode,
                installed_parts=installed_parts,
            )
        )
    return paths


def first_print_service_state_review_csv(
    *,
    evidence_paths_by_mode: Mapping[str, str | Path] | None = None,
) -> str:
    evidence_paths = evidence_paths_by_mode or {}
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_SERVICE_STATE_REVIEW_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in first_print_service_state_review_rows():
        evidence_path = evidence_paths.get(row.mode)
        result = "pass" if evidence_path else row.result
        notes = (
            "plain-Python bounds evidence; physical Gate 1-6 rows unchanged"
            if evidence_path
            else row.notes
        )
        writer.writerow(
            {
                "mode": row.mode,
                "mode_type": row.mode_type,
                "review_scope": row.review_scope,
                "acceptance_gate": row.acceptance_gate,
                "expected_removed_parts": row.expected_removed_parts,
                "expected_review_parts": row.expected_review_parts,
                "screenshot_path": str(evidence_path or row.screenshot_path),
                "result": result,
                "notes": notes,
            }
        )
    return output.getvalue()


def write_first_print_service_state_review(
    *,
    output_path: str | Path,
    overwrite: bool = False,
    evidence_paths_by_mode: Mapping[str, str | Path] | None = None,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        first_print_service_state_review_csv(
            evidence_paths_by_mode=evidence_paths_by_mode,
        )
    )
    return output


def _service_state_review_issue(
    issues: list[FirstPrintServiceStateReviewIssue],
    *,
    mode: str,
    field: str,
    message: str,
) -> None:
    issues.append(FirstPrintServiceStateReviewIssue(mode=mode, field=field, message=message))


def _resolve_service_state_evidence_path(
    *,
    worksheet_path: Path,
    evidence_path: str,
) -> Path:
    return _resolve_worksheet_evidence_path(
        worksheet_path=worksheet_path,
        evidence_path=evidence_path,
    )


def _audit_service_state_bounds_evidence(
    issues: list[FirstPrintServiceStateReviewIssue],
    *,
    mode: str,
    expected: FirstPrintServiceStateReviewRow,
    evidence_path: Path,
) -> None:
    reader = csv.DictReader(StringIO(evidence_path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_SERVICE_STATE_BOUNDS_EVIDENCE_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_SERVICE_STATE_BOUNDS_EVIDENCE_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _service_state_review_issue(
            issues,
            mode=mode,
            field="screenshot_path",
            message=f"bounds evidence missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _service_state_review_issue(
            issues,
            mode=mode,
            field="screenshot_path",
            message=f"bounds evidence extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    if not rows:
        _service_state_review_issue(
            issues,
            mode=mode,
            field="screenshot_path",
            message="bounds evidence has no part rows",
        )
        return

    parts = Counter(row.get("part", "").strip() for row in rows)
    duplicate_parts = tuple(
        sorted(part for part, count in parts.items() if part and count > 1)
    )
    if duplicate_parts:
        _service_state_review_issue(
            issues,
            mode=mode,
            field="screenshot_path",
            message=f"bounds evidence duplicate parts: {', '.join(duplicate_parts)}",
        )

    removed_parts = set(_service_state_parts_from_csv(expected.expected_removed_parts))
    review_parts = set(_service_state_parts_from_csv(expected.expected_review_parts))
    observed_parts = {part for part in parts if part}
    if removed_parts & observed_parts:
        _service_state_review_issue(
            issues,
            mode=mode,
            field="screenshot_path",
            message=(
                "bounds evidence still includes expected removed parts: "
                + ", ".join(sorted(removed_parts & observed_parts))
            ),
        )
    missing_review_parts = review_parts - observed_parts
    if missing_review_parts:
        _service_state_review_issue(
            issues,
            mode=mode,
            field="screenshot_path",
            message=(
                "bounds evidence is missing expected review parts: "
                + ", ".join(sorted(missing_review_parts))
            ),
        )

    for index, row in enumerate(rows, start=2):
        if None in row:
            _service_state_review_issue(
                issues,
                mode=mode,
                field="screenshot_path",
                message=f"bounds evidence line {index} has more values than headers",
            )
        if row.get("mode", "").strip() != mode:
            _service_state_review_issue(
                issues,
                mode=mode,
                field="screenshot_path",
                message=f"bounds evidence line {index} has stale mode",
            )
        for field, expected_value in (
            ("mode_type", expected.mode_type),
            ("review_scope", expected.review_scope),
            ("acceptance_gate", expected.acceptance_gate),
        ):
            observed = row.get(field, "").strip()
            if observed != expected_value:
                _service_state_review_issue(
                    issues,
                    mode=mode,
                    field="screenshot_path",
                    message=(
                        f"bounds evidence line {index} {field} expected "
                        f"{expected_value or 'blank'}, found {observed or 'blank'}"
                    ),
                )
        if not row.get("part", "").strip():
            _service_state_review_issue(
                issues,
                mode=mode,
                field="screenshot_path",
                message=f"bounds evidence line {index} part is blank",
            )
        for field in (
            "x_len_mm",
            "y_len_mm",
            "z_len_mm",
        ):
            try:
                value = float(row.get(field, ""))
            except ValueError:
                value = 0.0
            if value <= 0:
                _service_state_review_issue(
                    issues,
                    mode=mode,
                    field="screenshot_path",
                    message=f"bounds evidence line {index} has nonpositive {field}",
                )
        if row.get("result", "").strip() != "pass":
            _service_state_review_issue(
                issues,
                mode=mode,
                field="screenshot_path",
                message=f"bounds evidence line {index} result is not pass",
            )


def audit_first_print_service_state_review(
    *,
    worksheet_path: str | Path,
) -> FirstPrintServiceStateReviewAudit:
    path = Path(worksheet_path)
    expected_rows = {row.mode: row for row in first_print_service_state_review_rows()}
    issues: list[FirstPrintServiceStateReviewIssue] = []
    if not path.exists():
        _service_state_review_issue(
            issues,
            mode="worksheet",
            field="path",
            message="service state review worksheet file does not exist",
        )
        return FirstPrintServiceStateReviewAudit(
            worksheet_path=path,
            expected_row_count=len(expected_rows),
            actual_row_count=0,
            result_counts={},
            missing_modes=tuple(expected_rows),
            extra_modes=(),
            duplicate_modes=(),
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_SERVICE_STATE_REVIEW_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_SERVICE_STATE_REVIEW_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _service_state_review_issue(
            issues,
            mode="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _service_state_review_issue(
            issues,
            mode="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    result_counts = Counter(row.get("result", "").strip() for row in rows)
    mode_counts = Counter(row.get("mode", "").strip() for row in rows)
    actual_modes = {mode for mode in mode_counts if mode}
    expected_modes = set(expected_rows)
    missing_modes = tuple(mode for mode in expected_rows if mode not in actual_modes)
    extra_modes = tuple(sorted(mode for mode in actual_modes if mode not in expected_modes))
    duplicate_modes = tuple(
        sorted(mode for mode, count in mode_counts.items() if mode and count > 1)
    )

    for mode in missing_modes:
        _service_state_review_issue(
            issues,
            mode=mode,
            field="mode",
            message="expected service-state review row is missing",
        )
    for mode in extra_modes:
        _service_state_review_issue(
            issues,
            mode=mode,
            field="mode",
            message="service-state review row is not an expected viewer mode",
        )
    for mode in duplicate_modes:
        _service_state_review_issue(
            issues,
            mode=mode,
            field="mode",
            message="duplicate service-state review row",
        )

    for index, row in enumerate(rows, start=2):
        if None in row:
            _service_state_review_issue(
                issues,
                mode=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        mode = row.get("mode", "").strip()
        if not mode:
            _service_state_review_issue(
                issues,
                mode=f"line {index}",
                field="mode",
                message="mode is blank",
            )
            continue
        expected = expected_rows.get(mode)
        if expected is None:
            continue

        for field, expected_value in (
            ("mode_type", expected.mode_type),
            ("review_scope", expected.review_scope),
            ("acceptance_gate", expected.acceptance_gate),
            ("expected_removed_parts", expected.expected_removed_parts),
            ("expected_review_parts", expected.expected_review_parts),
        ):
            observed = row.get(field, "").strip()
            if observed != expected_value:
                _service_state_review_issue(
                    issues,
                    mode=mode,
                    field=field,
                    message=f"expected {expected_value or 'blank'}, found {observed or 'blank'}",
                )

        result = row.get("result", "").strip()
        if result not in FIRST_PRINT_SERVICE_STATE_REVIEW_RESULT_VALUES:
            _service_state_review_issue(
                issues,
                mode=mode,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
            continue

        screenshot_path = row.get("screenshot_path", "").strip()
        if result == "not_tested" and screenshot_path:
            _service_state_review_issue(
                issues,
                mode=mode,
                field="result",
                message="not_tested row must not contain screenshot evidence",
            )
        if result == "pass" and not screenshot_path:
            _service_state_review_issue(
                issues,
                mode=mode,
                field="screenshot_path",
                message="pass row requires a screenshot or plain-Python bounds evidence path",
            )
        if result == "pass" and screenshot_path:
            evidence_path = _resolve_service_state_evidence_path(
                worksheet_path=path,
                evidence_path=screenshot_path,
            )
            if not evidence_path.exists():
                _service_state_review_issue(
                    issues,
                    mode=mode,
                    field="screenshot_path",
                    message="evidence path does not exist",
                )
            elif evidence_path.suffix.lower() == ".csv":
                _audit_service_state_bounds_evidence(
                    issues,
                    mode=mode,
                    expected=expected,
                    evidence_path=evidence_path,
                )
            elif evidence_path.stat().st_size <= 0:
                _service_state_review_issue(
                    issues,
                    mode=mode,
                    field="screenshot_path",
                    message="screenshot evidence file is empty",
                )

    return FirstPrintServiceStateReviewAudit(
        worksheet_path=path,
        expected_row_count=len(expected_rows),
        actual_row_count=len(rows),
        result_counts=dict(result_counts),
        missing_modes=missing_modes,
        extra_modes=extra_modes,
        duplicate_modes=duplicate_modes,
        issues=tuple(issues),
    )


def _slicer_version(executable_path: Path, token: str) -> str:
    if not executable_path.exists():
        return ""
    commands = ((str(executable_path), "--help"), (str(executable_path), "--version"))
    for command in commands:
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        output = "\n".join((result.stdout, result.stderr))
        for line in output.splitlines():
            text = line.strip()
            if token in text:
                return text.rstrip(":")
    return "unknown"


def _prusa_active_presets(config_path: Path) -> dict[str, str]:
    if not config_path.exists():
        return {}
    values: dict[str, str] = {}
    in_presets = False
    for raw_line in config_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_presets = line == "[presets]"
            continue
        if not in_presets or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        values[key] = value
    return {
        "printer_profile": values.get("printer", ""),
        "material_profile": values.get("filament", ""),
        "print_profile": values.get("print", ""),
    }


def discover_first_print_slicer_setup_rows(
    *,
    prusa_slicer_path: str | Path = DEFAULT_PRUSA_SLICER_PATH,
    prusa_config_path: str | Path = DEFAULT_PRUSA_CONFIG_PATH,
    bambu_studio_path: str | Path = DEFAULT_BAMBU_STUDIO_PATH,
    bambu_config_path: str | Path = DEFAULT_BAMBU_CONFIG_PATH,
) -> tuple[FirstPrintSlicerSetupRow, ...]:
    prusa_path = Path(prusa_slicer_path)
    prusa_config = Path(prusa_config_path)
    bambu_path = Path(bambu_studio_path)
    bambu_config = Path(bambu_config_path)
    rows: list[FirstPrintSlicerSetupRow] = []
    if prusa_path.exists():
        presets = _prusa_active_presets(prusa_config)
        rows.append(
            FirstPrintSlicerSetupRow(
                slicer_name="PrusaSlicer",
                executable_path=str(prusa_path),
                version=_slicer_version(prusa_path, "PrusaSlicer-"),
                printer_profile=presets.get("printer_profile", ""),
                material_profile=presets.get("material_profile", ""),
                print_profile=presets.get("print_profile", ""),
                profile_source=str(prusa_config) if prusa_config.exists() else "",
                notes="active presets discovered from PrusaSlicer.ini",
            )
        )
    if bambu_path.exists():
        rows.append(
            FirstPrintSlicerSetupRow(
                slicer_name="BambuStudio",
                executable_path=str(bambu_path),
                version=_slicer_version(bambu_path, "BambuStudio-"),
                printer_profile="",
                material_profile="",
                print_profile="",
                profile_source=str(bambu_config) if bambu_config.exists() else "",
                notes="CLI discovered; select machine, process, and filament JSONs",
            )
        )
    return tuple(rows)


def first_print_slicer_setup_csv(
    rows: tuple[FirstPrintSlicerSetupRow, ...],
) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_SLICER_SETUP_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "slicer_name": row.slicer_name,
                "executable_path": row.executable_path,
                "version": row.version,
                "printer_profile": row.printer_profile,
                "material_profile": row.material_profile,
                "print_profile": row.print_profile,
                "profile_source": row.profile_source,
                "selected": row.selected,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def write_first_print_slicer_setup(
    *,
    output_path: str | Path,
    rows: tuple[FirstPrintSlicerSetupRow, ...] | None = None,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    setup_rows = rows if rows is not None else discover_first_print_slicer_setup_rows()
    output.write_text(first_print_slicer_setup_csv(tuple(setup_rows)))
    return output


def _slicer_setup_rows_from_csv(path: Path) -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    if fieldnames != FIRST_PRINT_SLICER_SETUP_FIELDNAMES:
        expected = ", ".join(FIRST_PRINT_SLICER_SETUP_FIELDNAMES)
        found = ", ".join(fieldnames)
        raise ValueError(f"expected slicer setup columns {expected}; found {found}")
    return list(reader)


def _slicer_setup_csv_from_dict_rows(rows: list[dict[str, str]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_SLICER_SETUP_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                field: row.get(field, "")
                for field in FIRST_PRINT_SLICER_SETUP_FIELDNAMES
            }
        )
    return output.getvalue()


def _slicer_setup_issue(
    issues: list[FirstPrintSlicerSetupIssue],
    *,
    slicer_name: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintSlicerSetupIssue(
            slicer_name=slicer_name,
            field=field,
            message=message,
        )
    )


def _slicer_setup_row_summary(row: dict[str, str]) -> str:
    return (
        f"{row.get('slicer_name', '').strip()} / "
        f"{row.get('printer_profile', '').strip()} / "
        f"{row.get('material_profile', '').strip()} / "
        f"{row.get('print_profile', '').strip()}"
    )


def _slicer_setup_row_matches(
    row: dict[str, str],
    *,
    setup_summary: str,
    slicer_name: str,
    printer_profile: str,
    material_profile: str,
    print_profile: str,
) -> bool:
    if setup_summary:
        return _slicer_setup_row_summary(row) == setup_summary
    if not slicer_name:
        raise ValueError("provide setup_summary or slicer_name")
    if row.get("slicer_name", "").strip() != slicer_name:
        return False
    filters = (
        ("printer_profile", printer_profile),
        ("material_profile", material_profile),
        ("print_profile", print_profile),
    )
    return all(
        not expected or row.get(field, "").strip() == expected
        for field, expected in filters
    )


def _validate_selectable_slicer_setup_row(row: dict[str, str]) -> None:
    slicer_name = row.get("slicer_name", "").strip() or "selected row"
    executable = Path(row.get("executable_path", "").strip())
    if not executable.exists():
        raise ValueError(f"{slicer_name} executable path does not exist: {executable}")
    for field in ("printer_profile", "material_profile", "print_profile"):
        if not row.get(field, "").strip():
            raise ValueError(f"{slicer_name} cannot be selected without {field}")
    source = row.get("profile_source", "").strip()
    if source and not Path(source).exists():
        raise ValueError(f"{slicer_name} profile source does not exist: {source}")


def _replace_record_table_value(record_text: str, field: str, value: str) -> str:
    if "\n" in value or "|" in value:
        raise ValueError(f"{field} value cannot contain newline or pipe characters")
    lines = record_text.splitlines()
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] == field:
            lines[index] = f"| {field} | {value} |"
            return "\n".join(lines) + ("\n" if record_text.endswith("\n") else "")
    raise ValueError(f"record field not found: {field}")


def select_first_print_slicer_setup(
    *,
    worksheet_path: str | Path,
    record_path: str | Path,
    setup_summary: str = "",
    slicer_name: str = "",
    printer_profile: str = "",
    material_profile: str = "",
    print_profile: str = "",
) -> FirstPrintSlicerSetupSelection:
    worksheet = Path(worksheet_path)
    record = Path(record_path)
    if not worksheet.exists():
        raise FileNotFoundError(worksheet)
    if not record.exists():
        raise FileNotFoundError(record)

    rows = _slicer_setup_rows_from_csv(worksheet)
    matches = [
        index
        for index, row in enumerate(rows)
        if _slicer_setup_row_matches(
            row,
            setup_summary=setup_summary,
            slicer_name=slicer_name,
            printer_profile=printer_profile,
            material_profile=material_profile,
            print_profile=print_profile,
        )
    ]
    if not matches:
        selector = setup_summary or slicer_name
        raise ValueError(f"no slicer setup row matched {selector}")
    if len(matches) > 1:
        selector = setup_summary or slicer_name
        raise ValueError(f"multiple slicer setup rows matched {selector}")

    selected_index = matches[0]
    _validate_selectable_slicer_setup_row(rows[selected_index])
    selected_summary = _slicer_setup_row_summary(rows[selected_index])

    record_text = record.read_text()
    updated_record = _replace_record_table_value(
        record_text,
        "Printer / material / profile",
        selected_summary,
    )

    updated_rows = [dict(row) for row in rows]
    for index, row in enumerate(updated_rows):
        row["selected"] = "yes" if index == selected_index else "no"
        if index == selected_index:
            row["result"] = "pass"
    worksheet.write_text(_slicer_setup_csv_from_dict_rows(updated_rows))
    audit = audit_first_print_slicer_setup(worksheet_path=worksheet)
    if not audit.setup_selected or audit.selected_setup_summary != selected_summary:
        raise RuntimeError("selected slicer setup did not audit cleanly")

    record.write_text(updated_record)
    return FirstPrintSlicerSetupSelection(
        worksheet_path=worksheet,
        record_path=record,
        selected_row_index=selected_index,
        selected_setup_summary=selected_summary,
        audit=audit,
    )


def audit_first_print_slicer_setup(
    *,
    worksheet_path: str | Path,
) -> FirstPrintSlicerSetupAudit:
    path = Path(worksheet_path)
    issues: list[FirstPrintSlicerSetupIssue] = []
    if not path.exists():
        _slicer_setup_issue(
            issues,
            slicer_name="worksheet",
            field="path",
            message="slicer setup worksheet does not exist",
        )
        return FirstPrintSlicerSetupAudit(
            worksheet_path=path,
            row_count=0,
            selected_row_count=0,
            selected_setup_summary="",
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(path.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_SLICER_SETUP_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_SLICER_SETUP_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _slicer_setup_issue(
            issues,
            slicer_name="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _slicer_setup_issue(
            issues,
            slicer_name="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    selected_rows: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=2):
        if None in row:
            _slicer_setup_issue(
                issues,
                slicer_name=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        slicer_name = row.get("slicer_name", "").strip() or f"line {index}"
        selected = row.get("selected", "").strip()
        result = row.get("result", "").strip()
        executable = Path(row.get("executable_path", "").strip())
        if not executable.exists():
            _slicer_setup_issue(
                issues,
                slicer_name=slicer_name,
                field="executable_path",
                message=f"executable path does not exist: {executable}",
            )
        if selected not in FIRST_PRINT_SLICER_SETUP_SELECTED_VALUES:
            _slicer_setup_issue(
                issues,
                slicer_name=slicer_name,
                field="selected",
                message=f"invalid selected value {selected or 'blank'}",
            )
        if result not in FIRST_PRINT_SLICER_SETUP_RESULT_VALUES:
            _slicer_setup_issue(
                issues,
                slicer_name=slicer_name,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
        if selected == "yes":
            selected_rows.append(row)
            if result != "pass":
                _slicer_setup_issue(
                    issues,
                    slicer_name=slicer_name,
                    field="result",
                    message="selected setup row must be marked pass",
                )
            for field in ("printer_profile", "material_profile", "print_profile"):
                if not row.get(field, "").strip():
                    _slicer_setup_issue(
                        issues,
                        slicer_name=slicer_name,
                        field=field,
                        message="selected setup requires this profile field",
                    )
            source = row.get("profile_source", "").strip()
            if source and not Path(source).exists():
                _slicer_setup_issue(
                    issues,
                    slicer_name=slicer_name,
                    field="profile_source",
                    message=f"profile source does not exist: {source}",
                )

    selected_summary = (
        _slicer_setup_row_summary(selected_rows[0]) if len(selected_rows) == 1 else ""
    )
    if len(selected_rows) > 1:
        _slicer_setup_issue(
            issues,
            slicer_name="worksheet",
            field="selected",
            message="exactly one setup row may be selected",
        )

    return FirstPrintSlicerSetupAudit(
        worksheet_path=path,
        row_count=len(rows),
        selected_row_count=len(selected_rows),
        selected_setup_summary=selected_summary,
        issues=tuple(issues),
    )


def _first_print_selected_slicer_setup_row(
    worksheet_path: str | Path,
) -> dict[str, str] | None:
    path = Path(worksheet_path)
    if not path.exists():
        return None
    try:
        rows = _slicer_setup_rows_from_csv(path)
    except ValueError:
        return None
    selected_rows = [
        row
        for row in rows
        if row.get("selected", "").strip() == "yes"
        and row.get("result", "").strip() == "pass"
    ]
    return selected_rows[0] if len(selected_rows) == 1 else None


def _slicer_profile_source_candidates(profile_source: str) -> tuple[Path, ...]:
    source = Path(profile_source).expanduser()
    candidates = [source]
    if source.name == "PrusaSlicer.ini":
        candidates.extend(
            (
                source.parent / "vendor" / "PrusaResearch.ini",
                source.parent / "cache" / "vendor" / "PrusaResearch.ini",
            )
        )
    seen: set[Path] = set()
    existing: list[Path] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            existing.append(candidate)
    return tuple(existing)


def _printer_profile_bed_shape(
    *,
    printer_profile: str,
    profile_source: str,
) -> tuple[str, str]:
    candidates = _slicer_profile_source_candidates(profile_source)
    if not candidates:
        return "", ""

    parser = configparser.RawConfigParser(strict=False)
    parser.optionxform = str
    read_candidates: list[Path] = []
    for candidate in candidates:
        try:
            if parser.read(candidate):
                read_candidates.append(candidate)
        except configparser.Error:
            continue
    if not read_candidates:
        return "", "; ".join(str(path) for path in candidates)

    def inherited_value(section: str, key: str, seen: set[str]) -> str:
        if section in seen or not parser.has_section(section):
            return ""
        seen.add(section)
        value = parser.get(section, key, fallback="").strip()
        if value:
            return value
        inherits = parser.get(section, "inherits", fallback="")
        for parent in inherits.split(";"):
            parent = parent.strip().strip('"')
            if not parent:
                continue
            inherited = inherited_value(f"printer:{parent}", key, seen)
            if inherited:
                return inherited
        return ""

    bed_shape = inherited_value(f"printer:{printer_profile}", "bed_shape", set())
    return bed_shape, "; ".join(str(path) for path in read_candidates)


def _bed_shape_xy_mm(bed_shape: str) -> tuple[float, float]:
    points: list[tuple[float, float]] = []
    for point in bed_shape.split(","):
        if "x" not in point:
            continue
        x_text, y_text = point.split("x", 1)
        points.append((float(x_text), float(y_text)))
    if not points:
        return 0.0, 0.0
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2)


def _part_fits_rectangular_bed(
    *,
    target_x_mm: float,
    target_y_mm: float,
    bed_x_mm: float,
    bed_y_mm: float,
) -> bool:
    if (
        target_x_mm <= bed_x_mm
        and target_y_mm <= bed_y_mm
        or target_x_mm <= bed_y_mm
        and target_y_mm <= bed_x_mm
    ):
        return True

    def allowed_intervals(limit: float, axis_a: float, axis_b: float) -> list[tuple[float, float]]:
        theta_min = 0.0
        theta_max = math.pi / 2
        radius = math.hypot(axis_a, axis_b)
        if limit >= radius:
            return [(theta_min, theta_max)]
        if limit <= 0:
            return []
        ratio = max(-1.0, min(1.0, limit / radius))
        center = math.atan2(axis_b, axis_a)
        half_width = math.acos(ratio)
        disallowed_min = center - half_width
        disallowed_max = center + half_width
        intervals: list[tuple[float, float]] = []
        if disallowed_min > theta_min:
            intervals.append((theta_min, min(disallowed_min, theta_max)))
        if disallowed_max < theta_max:
            intervals.append((max(disallowed_max, theta_min), theta_max))
        return [(start, end) for start, end in intervals if end - start >= 1e-9]

    width_intervals = allowed_intervals(bed_x_mm, target_x_mm, target_y_mm)
    height_intervals = allowed_intervals(bed_y_mm, target_y_mm, target_x_mm)
    return any(
        min(width_end, height_end) - max(width_start, height_start) >= -1e-9
        for width_start, width_end in width_intervals
        for height_start, height_end in height_intervals
    )


def _minimum_y_segments_for_bed(
    *,
    target_x_mm: float,
    target_y_mm: float,
    bed_x_mm: float,
    bed_y_mm: float,
    max_segments: int = 8,
) -> int:
    for segments in range(1, max_segments + 1):
        if _part_fits_rectangular_bed(
            target_x_mm=target_x_mm,
            target_y_mm=target_y_mm / segments,
            bed_x_mm=bed_x_mm,
            bed_y_mm=bed_y_mm,
        ):
            return segments
    return 0


def audit_first_print_slicer_bed_fit(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    worksheet_path: str | Path,
) -> FirstPrintSlicerBedFitAudit:
    setup_audit = audit_first_print_slicer_setup(worksheet_path=worksheet_path)
    selected_row = _first_print_selected_slicer_setup_row(worksheet_path)
    issues: list[FirstPrintSlicerBedFitIssue] = []
    if not setup_audit.setup_selected or selected_row is None:
        issues.append(
            FirstPrintSlicerBedFitIssue(
                field="Slicer setup worksheet",
                message="exactly one passing slicer setup row must be selected",
            )
        )
        return FirstPrintSlicerBedFitAudit(
            selected_setup_summary=setup_audit.selected_setup_summary,
            printer_profile="",
            bed_shape_source="",
            bed_x_mm=0.0,
            bed_y_mm=0.0,
            oversized_parts=(),
            issues=tuple(issues),
        )

    printer_profile = selected_row.get("printer_profile", "").strip()
    profile_source = selected_row.get("profile_source", "").strip()
    bed_shape, bed_shape_source = _printer_profile_bed_shape(
        printer_profile=printer_profile,
        profile_source=profile_source,
    )
    try:
        bed_x_mm, bed_y_mm = _bed_shape_xy_mm(bed_shape)
    except ValueError:
        bed_x_mm, bed_y_mm = 0.0, 0.0
        issues.append(
            FirstPrintSlicerBedFitIssue(
                field="bed_shape",
                message=f"could not parse selected printer bed shape: {bed_shape}",
            )
        )
    if bed_x_mm <= 0 or bed_y_mm <= 0:
        issues.append(
            FirstPrintSlicerBedFitIssue(
                field="bed_shape",
                message="selected printer bed shape could not be resolved",
            )
        )

    package_audit = audit_first_print_package(params, out_dir)
    targets = _target_lookup(params)
    oversized: list[FirstPrintSlicerBedFitOversize] = []
    if bed_x_mm > 0 and bed_y_mm > 0:
        for artifact in first_print_slicer_queue_artifacts(package_audit):
            target = targets[artifact.name]
            if not _part_fits_rectangular_bed(
                target_x_mm=target.target_x_mm,
                target_y_mm=target.target_y_mm,
                bed_x_mm=bed_x_mm,
                bed_y_mm=bed_y_mm,
            ):
                oversized.append(
                    FirstPrintSlicerBedFitOversize(
                        part=artifact.name,
                        target_x_mm=target.target_x_mm,
                        target_y_mm=target.target_y_mm,
                        bed_x_mm=bed_x_mm,
                        bed_y_mm=bed_y_mm,
                    )
                )
    for item in oversized:
        issues.append(
            FirstPrintSlicerBedFitIssue(
                field="bed_fit",
                message=(
                    f"{item.part} target {item.target_x_mm:.2f} x "
                    f"{item.target_y_mm:.2f} mm does not fit selected bed "
                    f"{item.bed_x_mm:.2f} x {item.bed_y_mm:.2f} mm"
                ),
            )
        )

    return FirstPrintSlicerBedFitAudit(
        selected_setup_summary=setup_audit.selected_setup_summary,
        printer_profile=printer_profile,
        bed_shape_source=bed_shape_source,
        bed_x_mm=bed_x_mm,
        bed_y_mm=bed_y_mm,
        oversized_parts=tuple(oversized),
        issues=tuple(issues),
    )


def first_print_bed_fit_split_plan_rows(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    worksheet_path: str | Path,
) -> tuple[FirstPrintBedFitSplitPlanRow, ...]:
    package_audit = audit_first_print_package(params, out_dir)
    bed_audit = audit_first_print_slicer_bed_fit(
        params=params,
        out_dir=out_dir,
        worksheet_path=worksheet_path,
    )
    targets = _target_lookup(params)
    rows: list[FirstPrintBedFitSplitPlanRow] = []
    for artifact in first_print_slicer_queue_artifacts(package_audit):
        target = targets[artifact.name]
        fits_as_exported = bed_audit.bed_resolved and _part_fits_rectangular_bed(
            target_x_mm=target.target_x_mm,
            target_y_mm=target.target_y_mm,
            bed_x_mm=bed_audit.bed_x_mm,
            bed_y_mm=bed_audit.bed_y_mm,
        )
        minimum_segments = (
            _minimum_y_segments_for_bed(
                target_x_mm=target.target_x_mm,
                target_y_mm=target.target_y_mm,
                bed_x_mm=bed_audit.bed_x_mm,
                bed_y_mm=bed_audit.bed_y_mm,
            )
            if bed_audit.bed_resolved
            else 0
        )
        max_segment_y = (
            round(target.target_y_mm / minimum_segments, 2)
            if minimum_segments
            else 0.0
        )
        segment_fits = minimum_segments > 0
        if fits_as_exported:
            decision = "none"
        elif segment_fits:
            decision = (
                f"split_y_{minimum_segments}_segments_with_print_native_"
                "retention_sealing_service_evidence"
            )
        else:
            decision = "larger_printer_or_cad_redesign_required"
        rows.append(
            FirstPrintBedFitSplitPlanRow(
                part=artifact.name,
                target_x_mm=target.target_x_mm,
                target_y_mm=target.target_y_mm,
                target_z_mm=target.target_z_mm,
                selected_bed_x_mm=bed_audit.bed_x_mm,
                selected_bed_y_mm=bed_audit.bed_y_mm,
                fits_as_exported=fits_as_exported,
                minimum_y_segments=minimum_segments,
                max_segment_y_mm=max_segment_y,
                segment_fits_selected_bed=segment_fits,
                required_decision=decision,
            )
        )
    return tuple(rows)


def first_print_bed_fit_split_plan_csv(
    rows: tuple[FirstPrintBedFitSplitPlanRow, ...],
) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_BED_FIT_SPLIT_PLAN_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "part": row.part,
                "target_x_mm": f"{row.target_x_mm:.2f}",
                "target_y_mm": f"{row.target_y_mm:.2f}",
                "target_z_mm": f"{row.target_z_mm:.2f}",
                "selected_bed_x_mm": f"{row.selected_bed_x_mm:.2f}",
                "selected_bed_y_mm": f"{row.selected_bed_y_mm:.2f}",
                "fits_as_exported": "yes" if row.fits_as_exported else "no",
                "minimum_y_segments": str(row.minimum_y_segments),
                "max_segment_y_mm": f"{row.max_segment_y_mm:.2f}",
                "segment_fits_selected_bed": (
                    "yes" if row.segment_fits_selected_bed else "no"
                ),
                "required_decision": row.required_decision,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def write_first_print_bed_fit_split_plan(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    slicer_setup_path: str | Path,
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = first_print_bed_fit_split_plan_rows(
        params=params,
        out_dir=out_dir,
        worksheet_path=slicer_setup_path,
    )
    output.write_text(first_print_bed_fit_split_plan_csv(rows))
    return output


def _split_plan_issue(
    issues: list[FirstPrintBedFitSplitPlanIssue],
    *,
    part: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintBedFitSplitPlanIssue(
            part=part,
            field=field,
            message=message,
        )
    )


def _parse_bool_cell(value: str) -> bool | None:
    cleaned = value.strip()
    if cleaned == "yes":
        return True
    if cleaned == "no":
        return False
    return None


def audit_first_print_bed_fit_split_plan(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    slicer_setup_path: str | Path,
    worksheet_path: str | Path,
) -> FirstPrintBedFitSplitPlanAudit:
    worksheet = Path(worksheet_path)
    expected_rows = first_print_bed_fit_split_plan_rows(
        params=params,
        out_dir=out_dir,
        worksheet_path=slicer_setup_path,
    )
    expected_by_part = {row.part: row for row in expected_rows}
    issues: list[FirstPrintBedFitSplitPlanIssue] = []
    if not worksheet.exists():
        _split_plan_issue(
            issues,
            part="worksheet",
            field="path",
            message="bed-fit split-plan worksheet does not exist",
        )
        return FirstPrintBedFitSplitPlanAudit(
            worksheet_path=worksheet,
            expected_row_count=len(expected_rows),
            actual_row_count=0,
            result_counts={},
            missing_parts=tuple(expected_by_part),
            extra_parts=(),
            duplicate_parts=(),
            split_required_parts=(),
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(worksheet.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_BED_FIT_SPLIT_PLAN_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_BED_FIT_SPLIT_PLAN_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _split_plan_issue(
            issues,
            part="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _split_plan_issue(
            issues,
            part="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    counts = Counter(row.get("part", "").strip() for row in rows)
    actual_parts = set(counts) - {""}
    missing_parts = tuple(part for part in expected_by_part if part not in actual_parts)
    extra_parts = tuple(part for part in actual_parts if part not in expected_by_part)
    duplicate_parts = tuple(part for part, count in counts.items() if part and count > 1)
    result_counts = Counter(row.get("result", "").strip() for row in rows)
    split_required: list[str] = []

    for index, row in enumerate(rows, start=2):
        if None in row:
            _split_plan_issue(
                issues,
                part=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        part = row.get("part", "").strip()
        expected = expected_by_part.get(part)
        if not part:
            _split_plan_issue(
                issues,
                part=f"line {index}",
                field="part",
                message="part is blank",
            )
            continue
        if expected is None:
            continue
        numeric_fields = (
            ("target_x_mm", expected.target_x_mm),
            ("target_y_mm", expected.target_y_mm),
            ("target_z_mm", expected.target_z_mm),
            ("selected_bed_x_mm", expected.selected_bed_x_mm),
            ("selected_bed_y_mm", expected.selected_bed_y_mm),
            ("max_segment_y_mm", expected.max_segment_y_mm),
        )
        for field, expected_value in numeric_fields:
            try:
                actual = float(row.get(field, "").strip())
            except ValueError:
                _split_plan_issue(
                    issues,
                    part=part,
                    field=field,
                    message="expected numeric value",
                )
                continue
            if round(actual, 2) != round(expected_value, 2):
                _split_plan_issue(
                    issues,
                    part=part,
                    field=field,
                    message=f"expected {expected_value:.2f}",
                )
        try:
            actual_segments = int(row.get("minimum_y_segments", "").strip())
        except ValueError:
            actual_segments = -1
            _split_plan_issue(
                issues,
                part=part,
                field="minimum_y_segments",
                message="expected integer value",
            )
        if actual_segments != expected.minimum_y_segments:
            _split_plan_issue(
                issues,
                part=part,
                field="minimum_y_segments",
                message=f"expected {expected.minimum_y_segments}",
            )
        bool_fields = (
            ("fits_as_exported", expected.fits_as_exported),
            ("segment_fits_selected_bed", expected.segment_fits_selected_bed),
        )
        for field, expected_value in bool_fields:
            actual = _parse_bool_cell(row.get(field, ""))
            if actual is None:
                _split_plan_issue(
                    issues,
                    part=part,
                    field=field,
                    message="expected yes or no",
                )
            elif actual != expected_value:
                _split_plan_issue(
                    issues,
                    part=part,
                    field=field,
                    message=f"expected {'yes' if expected_value else 'no'}",
                )
        decision = row.get("required_decision", "").strip()
        if decision != expected.required_decision:
            _split_plan_issue(
                issues,
                part=part,
                field="required_decision",
                message=f"expected {expected.required_decision}",
            )
        result = row.get("result", "").strip()
        if result not in FIRST_PRINT_BED_FIT_SPLIT_PLAN_RESULT_VALUES:
            _split_plan_issue(
                issues,
                part=part,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
        if not expected.fits_as_exported:
            split_required.append(part)

    return FirstPrintBedFitSplitPlanAudit(
        worksheet_path=worksheet,
        expected_row_count=len(expected_rows),
        actual_row_count=len(rows),
        result_counts=dict(result_counts),
        missing_parts=missing_parts,
        extra_parts=extra_parts,
        duplicate_parts=duplicate_parts,
        split_required_parts=tuple(split_required),
        issues=tuple(issues),
    )


def first_print_y_split_artifact_rows(
    *,
    params: dict[str, Any],
    split_dir: str | Path,
    slicer_setup_path: str | Path,
    out_dir: str | Path,
) -> tuple[FirstPrintYSplitArtifactRow, ...]:
    bed_audit = audit_first_print_slicer_bed_fit(
        params=params,
        out_dir=out_dir,
        worksheet_path=slicer_setup_path,
    )
    split_path = Path(split_dir)
    split_plan = {
        str(row["name"]): row for row in row_coupon_production_y_split_plan(params)
    }
    split_parts = build_row_coupon_production_y_split_parts(params)
    rows: list[FirstPrintYSplitArtifactRow] = []
    for split_part, model in split_parts.items():
        plan_row = split_plan[split_part]
        bb = model.val().BoundingBox()
        target_x = round(float(bb.xlen), 2)
        target_y = round(float(bb.ylen), 2)
        target_z = round(float(bb.zlen), 2)
        stl_path = split_path / f"{params['name']}_{split_part}.stl"
        step_path = split_path / f"{params['name']}_{split_part}.step"
        fits_selected_bed = bed_audit.bed_resolved and _part_fits_rectangular_bed(
            target_x_mm=target_x,
            target_y_mm=target_y,
            bed_x_mm=bed_audit.bed_x_mm,
            bed_y_mm=bed_audit.bed_y_mm,
        )
        rows.append(
            FirstPrintYSplitArtifactRow(
                split_part=split_part,
                source_part=str(plan_row["source_part"]),
                segment_index=int(plan_row["segment_index"]),
                segment_count=int(plan_row["segment_count"]),
                target_x_mm=target_x,
                target_y_mm=target_y,
                target_z_mm=target_z,
                selected_bed_x_mm=bed_audit.bed_x_mm,
                selected_bed_y_mm=bed_audit.bed_y_mm,
                fits_selected_bed=fits_selected_bed,
                stl_path=stl_path,
                step_path=step_path,
                stl_exists=stl_path.exists(),
                step_exists=step_path.exists(),
                interface_zone=str(plan_row["interface_zone"]),
                required_evidence=str(plan_row["required_evidence"])
                if "required_evidence" in plan_row
                else (
                    "Gate 1 dimensions, Gate 2 dry assembly, Gate 4 wet/dry "
                    "witness, and selected-slicer bed-fit evidence"
                ),
            )
        )
    return tuple(rows)


def _y_split_artifact_issue(
    issues: list[FirstPrintYSplitArtifactIssue],
    *,
    split_part: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintYSplitArtifactIssue(
            split_part=split_part,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_artifacts(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    slicer_setup_path: str | Path,
) -> FirstPrintYSplitArtifactAudit:
    bed_audit = audit_first_print_slicer_bed_fit(
        params=params,
        out_dir=out_dir,
        worksheet_path=slicer_setup_path,
    )
    rows = first_print_y_split_artifact_rows(
        params=params,
        split_dir=split_dir,
        slicer_setup_path=slicer_setup_path,
        out_dir=out_dir,
    )
    issues: list[FirstPrintYSplitArtifactIssue] = []
    if not bed_audit.bed_resolved:
        _y_split_artifact_issue(
            issues,
            split_part="selected_bed",
            field="bed_shape",
            message="selected printer bed shape could not be resolved",
        )

    split_sources = tuple(dict.fromkeys(row.source_part for row in rows))
    oversized_sources = tuple(item.part for item in bed_audit.oversized_parts)
    missing_oversized = tuple(
        part for part in oversized_sources if part not in split_sources
    )
    for part in missing_oversized:
        _y_split_artifact_issue(
            issues,
            split_part=part,
            field="source_part",
            message="oversized selected-bed source part has no production split artifact",
        )

    for row in rows:
        if row.target_x_mm <= 0 or row.target_y_mm <= 0 or row.target_z_mm <= 0:
            _y_split_artifact_issue(
                issues,
                split_part=row.split_part,
                field="target_*_mm",
                message="split artifact has a nonpositive CAD bound",
            )
        if not row.fits_selected_bed:
            _y_split_artifact_issue(
                issues,
                split_part=row.split_part,
                field="fits_selected_bed",
                message=(
                    f"split target {row.target_x_mm:.2f} x {row.target_y_mm:.2f} "
                    f"does not fit selected bed {row.selected_bed_x_mm:.2f} x "
                    f"{row.selected_bed_y_mm:.2f}"
                ),
            )
        if not row.stl_exists:
            _y_split_artifact_issue(
                issues,
                split_part=row.split_part,
                field="stl_path",
                message=f"split STL does not exist: {row.stl_path}",
            )
        if not row.step_exists:
            _y_split_artifact_issue(
                issues,
                split_part=row.split_part,
                field="step_path",
                message=f"split STEP does not exist: {row.step_path}",
            )

    covered_oversized = tuple(part for part in oversized_sources if part in split_sources)
    return FirstPrintYSplitArtifactAudit(
        split_dir=Path(split_dir),
        selected_setup_summary=bed_audit.selected_setup_summary,
        bed_x_mm=bed_audit.bed_x_mm,
        bed_y_mm=bed_audit.bed_y_mm,
        expected_row_count=len(row_coupon_production_y_split_plan(params)),
        rows=rows,
        split_source_parts=split_sources,
        covered_oversized_parts=covered_oversized,
        missing_oversized_parts=missing_oversized,
        issues=tuple(issues),
    )


def _target_lookup(params: dict[str, Any]) -> dict[str, FirstPrintQCTarget]:
    return {target.name: target for target in first_print_qc_targets(params)}


def _artifact_presence(artifact: FirstPrintArtifact) -> str:
    if artifact.stl_exists and artifact.step_exists:
        return "stl+step"
    if artifact.stl_exists:
        return "stl-only"
    if artifact.step_exists:
        return "step-only"
    return "missing"


def _artifact_path(path: Path) -> str:
    return f"`{path}`"


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _nonprinted_model_use_and_install_requirement(
    artifact: FirstPrintArtifact,
) -> tuple[str, str]:
    if artifact.category == "cots_consumable":
        return (
            "dimensional reference only",
            "install real COTS consumable; dimensional blank not accepted",
        )
    if artifact.category == "service_tubing":
        return (
            "route and bend reference",
            "install real tubing or measured replacement with evidence",
        )
    if artifact.category == "electronics_or_dimensional_blank":
        return (
            "dry-fit blank or real package reference",
            "dimensional blank supports Gates 2-5 only; real part required "
            "for Gate 6 and operating acceptance",
        )
    return ("reference only", "explicit install decision required")


def first_print_package_manifest_markdown(
    params: dict[str, Any],
    audit: FirstPrintPackageAudit,
) -> str:
    manifest = row_coupon_part_manifest()
    policy = manifest["policy"]
    forbidden_authority = ", ".join(
        f"`{term}`" for term in policy["forbidden_retention_authority_terms"]
    )
    targets = _target_lookup(params)
    printed = [
        artifact
        for artifact in audit.production_artifacts
        if artifact.category == "printed"
    ]
    flexible = [
        artifact
        for artifact in audit.production_artifacts
        if artifact.category == "compressible_or_flexible"
    ]
    nonprinted = [
        artifact
        for artifact in audit.production_artifacts
        if artifact.category
        in {"cots_consumable", "electronics_or_dimensional_blank", "service_tubing"}
    ]

    lines = [
        f"# {audit.name} First-Print Package Manifest",
        "",
        "This is a print/procurement handoff for the production-operating one-row",
        "coupon. It separates slicer-ready printed parts from flexible seal parts,",
        "COTS/electronics/service items, and validation-only bodies.",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| CAD package audit ready | {'true' if audit.ready else 'false'} |",
        f"| Assembly STEP | {_artifact_path(audit.assembly_step)} |",
        f"| Printed slicer parts | {len(printed)} |",
        f"| Flexible/compressible parts | {len(flexible)} |",
        f"| COTS/electronics/service items | {len(nonprinted)} |",
        f"| Required validation bodies | {len(audit.validation_artifacts)} |",
        f"| Optional validation bodies | {len(audit.optional_validation_artifacts)} |",
        f"| Assembly policy | `{policy['assembly_rule']}` |",
        "| Material authority decision | "
        f"`{policy['material_authority_decision_date']} "
        f"{policy['material_authority_decision']}` |",
        f"| Supersedes older insert strategy | `{policy['supersedes_material_strategy']}` |",
        f"| Nonprinted exception policy | `{policy['nonprinted_parts']}` |",
        f"| Forbidden retention authority | {forbidden_authority} |",
        "",
        "## Operating Readiness Scope",
        "",
        "Package readiness only verifies CAD output presence and handoff scope.",
        "It does not mark any physical gate or operating acceptance row as passed.",
        "",
        "| Evidence set | Generated scope | Acceptance rule |",
        "|---|---:|---|",
        "| Service-state review | "
        f"{len(first_print_service_state_review_rows())} viewer modes | "
        "every installed, service, bench-only, and fail-closed review mode must "
        "pass before preflight closes |",
        f"| Gate 1 Print QC | {len(first_print_gate1_qc_worksheet_rows(params))} rows | "
        "every printed or flexible part row requires measurements and evidence |",
        "| Gate 2 Dry Assembly Fit | "
        f"{len(first_print_gate2_dry_assembly_worksheet_rows(params))} rows | "
        "requires Gate 1 print QC, install inventory, service-state review, and "
        "all dry-assembly target evidence |",
        "| Gate 3 OT-2 Placement And No-Motion Clearance | "
        f"{len(first_print_gate3_placement_worksheet_rows(params))} rows | "
        "requires Gate 2 readiness plus deck placement and no-motion clearance "
        "evidence |",
        "| Gate 4 Passive Leak And Wet/Dry Witness | "
        f"{len(first_print_gate4_wet_dry_witness_worksheet_rows(params))} rows | "
        "requires Gate 3 readiness plus wet/dry boundary and witness evidence |",
        "| Gate 5 Consumable And Puncture Link | "
        f"{len(first_print_gate5_consumable_puncture_worksheet_rows(params))} rows | "
        "requires Gate 4 readiness plus real consumables and puncture evidence |",
        "| Gate 6 Sensor And Thermal Link | "
        f"{len(first_print_gate6_sensor_thermal_worksheet_rows(params))} rows | "
        "requires Gate 5 readiness, real sensor inventory, powered sensor "
        "evidence, and thermal-proxy evidence |",
        f"| Install inventory | {len(first_print_install_inventory_rows())} rows | "
        "COTS consumables, service tubing, electronics, and sensor items must "
        "match their operating requirements; dimensional blanks cannot support "
        "Gate 6 or operating acceptance |",
        f"| Operating prototype acceptance | {len(FIRST_PRINT_PHYSICAL_GATES)} gates | "
        "requires preflight artifacts, print-start readiness, service-state "
        "review, the full physical gate chain, and real sensor inventory |",
        "",
        "## Slicer Queue: Printed Polymer Parts",
        "",
        "Print these production STLs. Do not add metal, glue, or hidden bonded",
        "authority to make them pass Gate 1.",
        "",
        "| Part | STL | STEP | Target X mm | Target Y mm | Target Z mm | Presence | Role |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for artifact in printed:
        target = targets[artifact.name]
        lines.append(
            "| "
            f"`{artifact.name}` | {_artifact_path(artifact.stl_path)} | "
            f"{_artifact_path(artifact.step_path)} | {target.target_x_mm:.2f} | "
            f"{target.target_y_mm:.2f} | {target.target_z_mm:.2f} | "
            f"{_artifact_presence(artifact)} | {artifact.role} |"
        )

    lines.extend(
        [
            "",
            "## Flexible Or Compressible Parts",
            "",
            "Make or procure these as compliant seal parts. Their CAD bounds are nominal",
            "uncompressed targets until real stock or printed TPU is measured.",
            "",
            "| Part | STL | STEP | Target X mm | Target Y mm | Target Z mm | Presence | Role |",
            "|---|---|---|---:|---:|---:|---|---|",
        ]
    )
    for artifact in flexible:
        target = targets[artifact.name]
        lines.append(
            "| "
            f"`{artifact.name}` | {_artifact_path(artifact.stl_path)} | "
            f"{_artifact_path(artifact.step_path)} | {target.target_x_mm:.2f} | "
            f"{target.target_y_mm:.2f} | {target.target_z_mm:.2f} | "
            f"{_artifact_presence(artifact)} | {artifact.role} |"
        )

    lines.extend(
        [
            "",
            "## Procure Or Install: Do Not Print As Production Parts",
            "",
            "| Part | Category | STL/STEP model use | Operating install requirement | "
            "Presence | Role |",
            "|---|---|---|---|---|---|",
        ]
    )
    for artifact in nonprinted:
        model_use, install_requirement = _nonprinted_model_use_and_install_requirement(
            artifact
        )
        lines.append(
            "| "
            f"`{artifact.name}` | {artifact.category} | {model_use} | "
            f"{install_requirement} | {_artifact_presence(artifact)} | {artifact.role} |"
        )

    lines.extend(
        [
            "",
            "## Operating Material And Exposure Policy",
            "",
            "This classifies installed operating surfaces for first-print handling.",
            "It does not mark BSL1 material, cleaning, leachable, or biological",
            "compatibility evidence as passed.",
            "",
            "| Part | Exposure class | Service disposition | Evidence gate |",
            "|---|---|---|---|",
        ]
    )
    for artifact in audit.production_artifacts:
        entry = manifest["installed"][artifact.name]
        lines.append(
            "| "
            f"`{artifact.name}` | {entry['exposure_class']} | "
            f"{entry['service_disposition']} | {entry['material_evidence_gate']} |"
        )

    lines.extend(
        [
            "",
            "## Validation Bodies: Do Not Install As Production Parts",
            "",
            "| Body | Required | STL | STEP | Presence | Role |",
            "|---|---|---|---|---|---|",
        ]
    )
    for artifact in audit.validation_artifacts:
        lines.append(
            "| "
            f"`{artifact.name}` | yes | {_artifact_path(artifact.stl_path)} | "
            f"{_artifact_path(artifact.step_path)} | {_artifact_presence(artifact)} | "
            f"{artifact.role} |"
        )
    for artifact in audit.optional_validation_artifacts:
        lines.append(
            "| "
            f"`{artifact.name}` | optional | {_artifact_path(artifact.stl_path)} | "
            f"{_artifact_path(artifact.step_path)} | {_artifact_presence(artifact)} | "
            f"{artifact.role} |"
        )

    if audit.missing_paths:
        lines.extend(["", "## Missing Required Files", "", "| Path |", "|---|"])
        lines.extend(f"| {_artifact_path(path)} |" for path in audit.missing_paths)
    else:
        lines.extend(["", "Missing required files: none"])

    return "\n".join(lines)


def first_print_slicer_queue_artifacts(
    audit: FirstPrintPackageAudit,
) -> tuple[FirstPrintArtifact, ...]:
    return tuple(
        artifact
        for artifact in audit.production_artifacts
        if artifact.category == "printed"
    )


def first_print_slicer_queue_manifest_markdown(
    *,
    params: dict[str, Any],
    items: tuple[FirstPrintSlicerQueueItem, ...],
    queue_dir: str | Path,
) -> str:
    lines = [
        f"# {params['name']} First-Print Slicer Queue",
        "",
        "This directory contains only printed production STL files for the",
        "one-row coupon first print. Do not add COTS consumables, electronics,",
        "service tubing, flexible seal bodies, or validation bodies to this queue.",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Queue directory | `{Path(queue_dir)}` |",
        f"| Printed slicer queue files | {len(items)} |",
        "",
        "| Part | Queued STL | SHA256 | Target X mm | Target Y mm | Target Z mm | Role |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for item in items:
        lines.append(
            "| "
            f"`{item.name}` | {_artifact_path(item.queue_stl_path)} | "
            f"`{item.sha256}` | {item.target_x_mm:.2f} | "
            f"{item.target_y_mm:.2f} | {item.target_z_mm:.2f} | {item.role} |"
        )
    return "\n".join(lines)


def _markdown_table_cells(line: str) -> tuple[str, ...]:
    if not line.startswith("|"):
        return ()
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def first_print_slicer_queue_manifest_items(
    queue_dir: str | Path,
) -> tuple[FirstPrintSlicerQueueItem, ...]:
    queue = Path(queue_dir)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    if not manifest.exists():
        return ()
    items: list[FirstPrintSlicerQueueItem] = []
    for line in manifest.read_text().splitlines():
        cells = _markdown_table_cells(line)
        if len(cells) < 7 or not cells[1].strip("`").endswith(".stl"):
            continue
        queue_stl = queue / Path(cells[1].strip("`")).name
        try:
            target_x = float(cells[3])
            target_y = float(cells[4])
            target_z = float(cells[5])
        except ValueError:
            continue
        items.append(
            FirstPrintSlicerQueueItem(
                name=cells[0].strip("`"),
                source_stl_path=queue_stl,
                queue_stl_path=queue_stl,
                sha256=cells[2].strip("`"),
                target_x_mm=target_x,
                target_y_mm=target_y,
                target_z_mm=target_z,
                role=cells[6],
            )
        )
    return tuple(items)


def audit_first_print_slicer_queue_manifest(
    queue_dir: str | Path,
) -> FirstPrintSlicerQueueAudit:
    queue = Path(queue_dir)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    items = first_print_slicer_queue_manifest_items(queue)
    expected_stl_paths = tuple(item.queue_stl_path for item in items)
    expected_path_set = set(expected_stl_paths)
    actual_paths = tuple(sorted(path for path in queue.iterdir())) if queue.exists() else ()
    actual_file_paths = tuple(path for path in actual_paths if path.is_file())
    actual_stl_paths = tuple(path for path in actual_file_paths if path.suffix.lower() == ".stl")
    allowed_paths = {*expected_path_set, manifest}
    extra_paths = tuple(path for path in actual_file_paths if path not in allowed_paths)
    missing_stl_paths = tuple(path for path in expected_stl_paths if not path.exists())
    mismatches: list[FirstPrintSlicerQueueHashMismatch] = []
    for item in items:
        if not item.queue_stl_path.exists():
            continue
        actual_sha = file_sha256(item.queue_stl_path)
        if actual_sha != item.sha256:
            mismatches.append(
                FirstPrintSlicerQueueHashMismatch(
                    path=item.queue_stl_path,
                    expected_sha256=item.sha256,
                    actual_sha256=actual_sha,
                )
            )
    source_issues = () if items else ("slicer queue manifest has no STL rows",)
    return FirstPrintSlicerQueueAudit(
        queue_dir=queue,
        manifest_path=manifest,
        manifest_exists=manifest.exists(),
        expected_stl_paths=expected_stl_paths,
        actual_stl_paths=actual_stl_paths,
        missing_stl_paths=missing_stl_paths,
        extra_paths=extra_paths,
        hash_mismatches=tuple(mismatches),
        package_missing_paths=(),
        source_issues=source_issues,
    )


def first_print_sliced_output_rows_from_slicer_queue_manifest(
    *,
    queue_dir: str | Path,
    selected_setup_summary: str = "",
) -> tuple[FirstPrintSlicedOutputRow, ...]:
    rows: list[FirstPrintSlicedOutputRow] = []
    for item in first_print_slicer_queue_manifest_items(queue_dir):
        rows.append(
            FirstPrintSlicedOutputRow(
                part=item.name,
                queued_stl_path=str(item.queue_stl_path),
                queued_stl_sha256=(
                    file_sha256(item.queue_stl_path)
                    if item.queue_stl_path.exists()
                    else item.sha256
                ),
                selected_setup_summary=selected_setup_summary,
            )
        )
    return tuple(rows)


def first_print_gate1_qc_rows_from_slicer_queue_manifest(
    queue_dir: str | Path,
) -> tuple[FirstPrintGate1QCWorksheetRow, ...]:
    rows: list[FirstPrintGate1QCWorksheetRow] = []
    for item in first_print_slicer_queue_manifest_items(queue_dir):
        source = "printed_split" if "split segment" in item.role else "printed"
        rows.append(
            FirstPrintGate1QCWorksheetRow(
                part=item.name,
                source=source,
                target_x_mm=item.target_x_mm,
                target_y_mm=item.target_y_mm,
                target_z_mm=item.target_z_mm,
            )
        )
    return tuple(rows)


def prepare_first_print_slicer_queue(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    queue_dir: str | Path,
    overwrite: bool = False,
) -> tuple[FirstPrintSlicerQueueItem, ...]:
    audit = audit_first_print_package(params, out_dir)
    if audit.missing_paths:
        raise FileNotFoundError(audit.missing_paths[0])

    queue = Path(queue_dir)
    queue.mkdir(parents=True, exist_ok=True)
    targets = _target_lookup(params)
    printed_artifacts = first_print_slicer_queue_artifacts(audit)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    if manifest.exists() and not overwrite:
        raise FileExistsError(manifest)
    for artifact in printed_artifacts:
        destination = queue / artifact.stl_path.name
        if destination.exists() and not overwrite:
            raise FileExistsError(destination)

    items: list[FirstPrintSlicerQueueItem] = []
    for artifact in printed_artifacts:
        target = targets[artifact.name]
        destination = queue / artifact.stl_path.name
        copy2(artifact.stl_path, destination)
        items.append(
            FirstPrintSlicerQueueItem(
                name=artifact.name,
                source_stl_path=artifact.stl_path,
                queue_stl_path=destination,
                sha256=file_sha256(destination),
                target_x_mm=target.target_x_mm,
                target_y_mm=target.target_y_mm,
                target_z_mm=target.target_z_mm,
                role=artifact.role,
            )
        )

    manifest.write_text(
        first_print_slicer_queue_manifest_markdown(
            params=params,
            items=tuple(items),
            queue_dir=queue,
        )
    )
    return tuple(items)


def first_print_y_split_slicer_queue_items(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
) -> tuple[FirstPrintSlicerQueueItem, ...]:
    package_audit = audit_first_print_package(params, out_dir)
    split_audit = audit_first_print_y_split_artifacts(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        slicer_setup_path=slicer_setup_path,
    )
    targets = _target_lookup(params)
    split_rows_by_source: dict[str, list[FirstPrintYSplitArtifactRow]] = {}
    for row in split_audit.rows:
        split_rows_by_source.setdefault(row.source_part, []).append(row)

    queue = Path(queue_dir)
    items: list[FirstPrintSlicerQueueItem] = []
    for artifact in first_print_slicer_queue_artifacts(package_audit):
        split_rows = sorted(
            split_rows_by_source.get(artifact.name, ()),
            key=lambda row: row.segment_index,
        )
        if split_rows:
            for row in split_rows:
                items.append(
                    FirstPrintSlicerQueueItem(
                        name=row.split_part,
                        source_stl_path=row.stl_path,
                        queue_stl_path=queue / row.stl_path.name,
                        sha256=file_sha256(row.stl_path) if row.stl_exists else "",
                        target_x_mm=row.target_x_mm,
                        target_y_mm=row.target_y_mm,
                        target_z_mm=row.target_z_mm,
                        role=(
                            f"{artifact.role}; split segment "
                            f"{row.segment_index}/{row.segment_count} at "
                            f"{row.interface_zone}"
                        ),
                    )
                )
            continue
        target = targets[artifact.name]
        items.append(
            FirstPrintSlicerQueueItem(
                name=artifact.name,
                source_stl_path=artifact.stl_path,
                queue_stl_path=queue / artifact.stl_path.name,
                sha256=file_sha256(artifact.stl_path) if artifact.stl_exists else "",
                target_x_mm=target.target_x_mm,
                target_y_mm=target.target_y_mm,
                target_z_mm=target.target_z_mm,
                role=artifact.role,
            )
        )
    return tuple(items)


def prepare_first_print_y_split_slicer_queue(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    overwrite: bool = False,
) -> tuple[FirstPrintSlicerQueueItem, ...]:
    split_audit = audit_first_print_y_split_artifacts(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        slicer_setup_path=slicer_setup_path,
    )
    if not split_audit.split_artifacts_ready:
        detail = split_audit.issues[0].message if split_audit.issues else "not ready"
        raise ValueError(f"split artifacts are not ready: {detail}")

    queue = Path(queue_dir)
    queue.mkdir(parents=True, exist_ok=True)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    if manifest.exists() and not overwrite:
        raise FileExistsError(manifest)

    items = first_print_y_split_slicer_queue_items(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue,
        slicer_setup_path=slicer_setup_path,
    )
    for item in items:
        if item.queue_stl_path.exists() and not overwrite:
            raise FileExistsError(item.queue_stl_path)

    copied: list[FirstPrintSlicerQueueItem] = []
    for item in items:
        copy2(item.source_stl_path, item.queue_stl_path)
        copied.append(
            FirstPrintSlicerQueueItem(
                name=item.name,
                source_stl_path=item.source_stl_path,
                queue_stl_path=item.queue_stl_path,
                sha256=file_sha256(item.queue_stl_path),
                target_x_mm=item.target_x_mm,
                target_y_mm=item.target_y_mm,
                target_z_mm=item.target_z_mm,
                role=item.role,
            )
        )

    manifest.write_text(
        first_print_slicer_queue_manifest_markdown(
            params=params,
            items=tuple(copied),
            queue_dir=queue,
        )
    )
    return tuple(copied)


def audit_first_print_slicer_queue(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    queue_dir: str | Path,
) -> FirstPrintSlicerQueueAudit:
    package_audit = audit_first_print_package(params, out_dir)
    queue = Path(queue_dir)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    printed_artifacts = first_print_slicer_queue_artifacts(package_audit)
    expected_stl_paths = tuple(queue / artifact.stl_path.name for artifact in printed_artifacts)
    expected_path_set = set(expected_stl_paths)

    actual_paths = tuple(sorted(path for path in queue.iterdir())) if queue.exists() else ()
    actual_file_paths = tuple(path for path in actual_paths if path.is_file())
    actual_stl_paths = tuple(path for path in actual_file_paths if path.suffix.lower() == ".stl")
    allowed_paths = {*expected_path_set, manifest}
    extra_paths = tuple(path for path in actual_file_paths if path not in allowed_paths)
    missing_stl_paths = tuple(path for path in expected_stl_paths if not path.exists())

    mismatches: list[FirstPrintSlicerQueueHashMismatch] = []
    for artifact in printed_artifacts:
        queue_path = queue / artifact.stl_path.name
        if not queue_path.exists() or not artifact.stl_path.exists():
            continue
        expected_sha = file_sha256(artifact.stl_path)
        actual_sha = file_sha256(queue_path)
        if expected_sha != actual_sha:
            mismatches.append(
                FirstPrintSlicerQueueHashMismatch(
                    path=queue_path,
                    expected_sha256=expected_sha,
                    actual_sha256=actual_sha,
                )
            )

    return FirstPrintSlicerQueueAudit(
        queue_dir=queue,
        manifest_path=manifest,
        manifest_exists=manifest.exists(),
        expected_stl_paths=expected_stl_paths,
        actual_stl_paths=actual_stl_paths,
        missing_stl_paths=missing_stl_paths,
        extra_paths=extra_paths,
        hash_mismatches=tuple(mismatches),
        package_missing_paths=package_audit.missing_paths,
    )


def audit_first_print_y_split_slicer_queue(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
) -> FirstPrintSlicerQueueAudit:
    split_audit = audit_first_print_y_split_artifacts(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        slicer_setup_path=slicer_setup_path,
    )
    package_audit = audit_first_print_package(params, out_dir)
    queue = Path(queue_dir)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    items = first_print_y_split_slicer_queue_items(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue,
        slicer_setup_path=slicer_setup_path,
    )
    expected_stl_paths = tuple(item.queue_stl_path for item in items)
    expected_path_set = set(expected_stl_paths)

    actual_paths = tuple(sorted(path for path in queue.iterdir())) if queue.exists() else ()
    actual_file_paths = tuple(path for path in actual_paths if path.is_file())
    actual_stl_paths = tuple(path for path in actual_file_paths if path.suffix.lower() == ".stl")
    allowed_paths = {*expected_path_set, manifest}
    extra_paths = tuple(path for path in actual_file_paths if path not in allowed_paths)
    missing_stl_paths = tuple(path for path in expected_stl_paths if not path.exists())

    mismatches: list[FirstPrintSlicerQueueHashMismatch] = []
    missing_source_paths: list[Path] = []
    for item in items:
        if not item.source_stl_path.exists():
            missing_source_paths.append(item.source_stl_path)
            continue
        if not item.queue_stl_path.exists():
            continue
        expected_sha = file_sha256(item.source_stl_path)
        actual_sha = file_sha256(item.queue_stl_path)
        if expected_sha != actual_sha:
            mismatches.append(
                FirstPrintSlicerQueueHashMismatch(
                    path=item.queue_stl_path,
                    expected_sha256=expected_sha,
                    actual_sha256=actual_sha,
                )
            )

    source_issues = tuple(
        f"{issue.split_part} | {issue.field} | {issue.message}"
        for issue in split_audit.issues
    )
    return FirstPrintSlicerQueueAudit(
        queue_dir=queue,
        manifest_path=manifest,
        manifest_exists=manifest.exists(),
        expected_stl_paths=expected_stl_paths,
        actual_stl_paths=actual_stl_paths,
        missing_stl_paths=missing_stl_paths,
        extra_paths=extra_paths,
        hash_mismatches=tuple(mismatches),
        package_missing_paths=(
            *package_audit.missing_paths,
            *tuple(missing_source_paths),
        ),
        source_issues=source_issues,
    )


def first_print_sliced_output_rows(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    queue_dir: str | Path,
    selected_setup_summary: str = "",
) -> tuple[FirstPrintSlicedOutputRow, ...]:
    package_audit = audit_first_print_package(params, out_dir)
    queue = Path(queue_dir)
    rows: list[FirstPrintSlicedOutputRow] = []
    for artifact in first_print_slicer_queue_artifacts(package_audit):
        queued_stl = queue / artifact.stl_path.name
        rows.append(
            FirstPrintSlicedOutputRow(
                part=artifact.name,
                queued_stl_path=str(queued_stl),
                queued_stl_sha256=file_sha256(queued_stl) if queued_stl.exists() else "",
                selected_setup_summary=selected_setup_summary,
            )
        )
    return tuple(rows)


def first_print_y_split_sliced_output_rows(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    selected_setup_summary: str = "",
) -> tuple[FirstPrintSlicedOutputRow, ...]:
    manifest_rows = first_print_sliced_output_rows_from_slicer_queue_manifest(
        queue_dir=queue_dir,
        selected_setup_summary=selected_setup_summary,
    )
    if manifest_rows:
        return manifest_rows

    rows: list[FirstPrintSlicedOutputRow] = []
    for item in first_print_y_split_slicer_queue_items(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
    ):
        rows.append(
            FirstPrintSlicedOutputRow(
                part=item.name,
                queued_stl_path=str(item.queue_stl_path),
                queued_stl_sha256=(
                    file_sha256(item.queue_stl_path)
                    if item.queue_stl_path.exists()
                    else ""
                ),
                selected_setup_summary=selected_setup_summary,
            )
        )
    return tuple(rows)


def first_print_sliced_output_csv(
    rows: tuple[FirstPrintSlicedOutputRow, ...],
) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_SLICED_OUTPUT_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "part": row.part,
                "queued_stl_path": row.queued_stl_path,
                "queued_stl_sha256": row.queued_stl_sha256,
                "sliced_output_path": row.sliced_output_path,
                "sliced_output_sha256": row.sliced_output_sha256,
                "selected_setup_summary": row.selected_setup_summary,
                "result": row.result,
                "notes": row.notes,
            }
        )
    return output.getvalue()


def _first_print_print_batch_traveler_row_dict(
    row: FirstPrintPrintBatchTravelerRow,
) -> dict[str, str]:
    return {
        "print_order": str(row.print_order),
        "part": row.part,
        "source": row.source,
        "target_x_mm": row.target_x_mm,
        "target_y_mm": row.target_y_mm,
        "target_z_mm": row.target_z_mm,
        "queued_stl_path": row.queued_stl_path,
        "queued_stl_sha256": row.queued_stl_sha256,
        "sliced_output_path": row.sliced_output_path,
        "sliced_output_sha256": row.sliced_output_sha256,
        "selected_setup_summary": row.selected_setup_summary,
        "gate1_qc_result": row.gate1_qc_result,
        "print_result": row.print_result,
        "print_evidence_path": row.print_evidence_path,
        "notes": row.notes,
    }


def first_print_print_batch_traveler_csv(
    rows: tuple[FirstPrintPrintBatchTravelerRow, ...],
) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=FIRST_PRINT_PRINT_BATCH_TRAVELER_FIELDNAMES,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(_first_print_print_batch_traveler_row_dict(row))
    return output.getvalue()


def write_first_print_sliced_outputs(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    queue_dir: str | Path,
    output_path: str | Path,
    selected_setup_summary: str = "",
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = first_print_sliced_output_rows(
        params=params,
        out_dir=out_dir,
        queue_dir=queue_dir,
        selected_setup_summary=selected_setup_summary,
    )
    output.write_text(first_print_sliced_output_csv(rows))
    return output


def write_first_print_y_split_sliced_outputs(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    output_path: str | Path,
    selected_setup_summary: str = "",
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = first_print_y_split_sliced_output_rows(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        selected_setup_summary=selected_setup_summary,
    )
    output.write_text(first_print_sliced_output_csv(rows))
    return output


def _selected_first_print_slicer_setup_or_raise(
    slicer_setup_path: str | Path,
) -> dict[str, str]:
    setup = Path(slicer_setup_path)
    audit = audit_first_print_slicer_setup(worksheet_path=setup)
    if not audit.setup_selected:
        raise ValueError("selected slicer setup worksheet is not ready")
    row = _first_print_selected_slicer_setup_row(setup)
    if row is None:
        raise ValueError("selected slicer setup row could not be resolved")
    _validate_selectable_slicer_setup_row(row)
    return row


def _prusa_slicer_datadir(profile_source: str) -> Path | None:
    source = Path(profile_source).expanduser()
    if source.name == "PrusaSlicer.ini":
        return source.parent
    return source.parent if source.exists() else None


def _run_prusa_slicer_gcode_export(
    *,
    setup_row: dict[str, str],
    input_stl: Path,
    output_gcode: Path,
) -> None:
    slicer_name = setup_row.get("slicer_name", "").strip()
    if slicer_name != "PrusaSlicer":
        raise ValueError(f"unsupported slicer for batch slicing: {slicer_name}")
    executable = Path(setup_row.get("executable_path", "").strip())
    datadir = _prusa_slicer_datadir(setup_row.get("profile_source", "").strip())
    command = [str(executable)]
    if datadir is not None:
        command.extend(("--datadir", str(datadir)))
    command.extend(
        (
            "--printer-profile",
            setup_row.get("printer_profile", "").strip(),
            "--print-profile",
            setup_row.get("print_profile", "").strip(),
            "--material-profile",
            setup_row.get("material_profile", "").strip(),
            "--export-gcode",
            "--output",
            str(output_gcode),
            str(input_stl),
        )
    )
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        tail = "\n".join(detail[-8:])
        raise RuntimeError(f"PrusaSlicer failed for {input_stl}:\n{tail}")
    if not output_gcode.exists():
        raise RuntimeError(f"PrusaSlicer did not create {output_gcode}")


def slice_first_print_y_split_slicer_queue(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    sliced_dir: str | Path,
    output_path: str | Path,
    overwrite: bool = False,
) -> tuple[FirstPrintSlicedOutputRow, ...]:
    setup_row = _selected_first_print_slicer_setup_or_raise(slicer_setup_path)
    selected_setup_summary = _slicer_setup_row_summary(setup_row)
    queue_audit = audit_first_print_slicer_queue_manifest(queue_dir)
    if not queue_audit.ready:
        raise ValueError("split slicer queue is not ready")

    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    gcode_dir = Path(sliced_dir)
    gcode_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    rows: list[FirstPrintSlicedOutputRow] = []
    for item in first_print_slicer_queue_manifest_items(queue_dir):
        gcode = gcode_dir / f"{params['name']}_{item.name}.gcode"
        if gcode.exists() and not overwrite:
            raise FileExistsError(gcode)
        _run_prusa_slicer_gcode_export(
            setup_row=setup_row,
            input_stl=item.queue_stl_path,
            output_gcode=gcode,
        )
        rows.append(
            FirstPrintSlicedOutputRow(
                part=item.name,
                queued_stl_path=str(item.queue_stl_path),
                queued_stl_sha256=file_sha256(item.queue_stl_path),
                sliced_output_path=str(gcode),
                sliced_output_sha256=file_sha256(gcode),
                selected_setup_summary=selected_setup_summary,
                result="pass",
                notes=f"sliced with {setup_row.get('slicer_name', '').strip()}",
            )
        )

    output.write_text(first_print_sliced_output_csv(tuple(rows)))
    return tuple(rows)


def _sliced_output_issue(
    issues: list[FirstPrintSlicedOutputIssue],
    *,
    part: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintSlicedOutputIssue(
            part=part,
            field=field,
            message=message,
        )
    )


def _path_from_csv_cell(value: str) -> Path:
    return Path(value.strip())


def _csv_rows_from_path(path: str | Path) -> tuple[dict[str, str], ...]:
    csv_path = Path(path)
    if not csv_path.exists():
        return ()
    return tuple(csv.DictReader(StringIO(csv_path.read_text())))


def audit_first_print_sliced_outputs(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    queue_dir: str | Path,
    worksheet_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintSlicedOutputAudit:
    worksheet = Path(worksheet_path)
    queue_audit = audit_first_print_slicer_queue(
        params=params,
        out_dir=out_dir,
        queue_dir=queue_dir,
    )
    expected_rows = first_print_sliced_output_rows(
        params=params,
        out_dir=out_dir,
        queue_dir=queue_dir,
    )
    return _audit_first_print_sliced_outputs_from_expected_rows(
        worksheet_path=worksheet,
        expected_rows=expected_rows,
        queue_ready=queue_audit.ready,
        expected_setup_summary=expected_setup_summary,
    )


def audit_first_print_y_split_sliced_outputs(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    worksheet_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintSlicedOutputAudit:
    worksheet = Path(worksheet_path)
    queue_audit = audit_first_print_slicer_queue_manifest(queue_dir)
    expected_rows = first_print_sliced_output_rows_from_slicer_queue_manifest(
        queue_dir=queue_dir,
    )
    return _audit_first_print_sliced_outputs_from_expected_rows(
        worksheet_path=worksheet,
        expected_rows=expected_rows,
        queue_ready=queue_audit.ready,
        expected_setup_summary=expected_setup_summary,
    )


def _audit_first_print_sliced_outputs_from_expected_rows(
    *,
    worksheet_path: Path,
    expected_rows: tuple[FirstPrintSlicedOutputRow, ...],
    queue_ready: bool,
    expected_setup_summary: str = "",
) -> FirstPrintSlicedOutputAudit:
    worksheet = Path(worksheet_path)
    expected_by_part = {row.part: row for row in expected_rows}
    issues: list[FirstPrintSlicedOutputIssue] = []
    if not worksheet.exists():
        _sliced_output_issue(
            issues,
            part="worksheet",
            field="path",
            message="sliced output worksheet does not exist",
        )
        return FirstPrintSlicedOutputAudit(
            worksheet_path=worksheet,
            expected_row_count=len(expected_rows),
            actual_row_count=0,
            result_counts={},
            missing_parts=tuple(expected_by_part),
            extra_parts=(),
            duplicate_parts=(),
            queue_ready=queue_ready,
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(worksheet.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_SLICED_OUTPUT_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_SLICED_OUTPUT_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _sliced_output_issue(
            issues,
            part="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _sliced_output_issue(
            issues,
            part="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    counts = Counter(row.get("part", "").strip() for row in rows)
    actual_parts = set(counts) - {""}
    missing_parts = tuple(part for part in expected_by_part if part not in actual_parts)
    extra_parts = tuple(part for part in actual_parts if part not in expected_by_part)
    duplicate_parts = tuple(part for part, count in counts.items() if part and count > 1)
    result_counts = Counter(row.get("result", "").strip() for row in rows)

    for index, row in enumerate(rows, start=2):
        if None in row:
            _sliced_output_issue(
                issues,
                part=f"line {index}",
                field="row",
                message="row has more values than header columns",
            )
        part = row.get("part", "").strip()
        expected = expected_by_part.get(part)
        if not part:
            _sliced_output_issue(
                issues,
                part=f"line {index}",
                field="part",
                message="part is blank",
            )
            continue
        if expected is None:
            continue
        queued_stl_path = row.get("queued_stl_path", "").strip()
        queued_stl_sha256 = row.get("queued_stl_sha256", "").strip()
        if queued_stl_path != expected.queued_stl_path:
            _sliced_output_issue(
                issues,
                part=part,
                field="queued_stl_path",
                message=f"expected {expected.queued_stl_path}, found {queued_stl_path}",
            )
        if queued_stl_sha256 != expected.queued_stl_sha256:
            _sliced_output_issue(
                issues,
                part=part,
                field="queued_stl_sha256",
                message="queued STL hash does not match current queue",
            )
        result = row.get("result", "").strip()
        if result not in FIRST_PRINT_SLICED_OUTPUT_RESULT_VALUES:
            _sliced_output_issue(
                issues,
                part=part,
                field="result",
                message=f"invalid result {result or 'blank'}",
            )
        if result != "pass":
            continue

        setup_summary = row.get("selected_setup_summary", "").strip()
        if not setup_summary:
            _sliced_output_issue(
                issues,
                part=part,
                field="selected_setup_summary",
                message="pass row requires selected setup summary",
            )
        if expected_setup_summary and setup_summary != expected_setup_summary:
            _sliced_output_issue(
                issues,
                part=part,
                field="selected_setup_summary",
                message=f"expected selected setup {expected_setup_summary}",
            )
        sliced_path_text = row.get("sliced_output_path", "").strip()
        if not sliced_path_text:
            _sliced_output_issue(
                issues,
                part=part,
                field="sliced_output_path",
                message="pass row requires sliced output path",
            )
            continue
        sliced_path = _path_from_csv_cell(sliced_path_text)
        if sliced_path.suffix.lower() not in FIRST_PRINT_SLICED_OUTPUT_SUFFIXES:
            allowed = ", ".join(sorted(FIRST_PRINT_SLICED_OUTPUT_SUFFIXES))
            _sliced_output_issue(
                issues,
                part=part,
                field="sliced_output_path",
                message=f"expected sliced output suffix in {allowed}",
            )
        if not sliced_path.exists():
            _sliced_output_issue(
                issues,
                part=part,
                field="sliced_output_path",
                message=f"sliced output does not exist: {sliced_path}",
            )
            continue
        expected_sha = file_sha256(sliced_path)
        actual_sha = row.get("sliced_output_sha256", "").strip()
        if not actual_sha:
            _sliced_output_issue(
                issues,
                part=part,
                field="sliced_output_sha256",
                message="pass row requires sliced output hash",
            )
        elif actual_sha != expected_sha:
            _sliced_output_issue(
                issues,
                part=part,
                field="sliced_output_sha256",
                message="sliced output hash does not match file",
            )

    return FirstPrintSlicedOutputAudit(
        worksheet_path=worksheet,
        expected_row_count=len(expected_rows),
        actual_row_count=len(rows),
        result_counts=dict(result_counts),
        missing_parts=missing_parts,
        extra_parts=extra_parts,
        duplicate_parts=duplicate_parts,
        queue_ready=queue_ready,
        issues=tuple(issues),
    )


def first_print_print_batch_traveler_rows(
    *,
    sliced_output_path: str | Path,
    gate1_qc_path: str | Path,
) -> tuple[FirstPrintPrintBatchTravelerRow, ...]:
    gate1_rows = _csv_rows_from_path(gate1_qc_path)
    gate1_by_part = {row.get("part", "").strip(): row for row in gate1_rows}
    rows: list[FirstPrintPrintBatchTravelerRow] = []
    for order, row in enumerate(_csv_rows_from_path(sliced_output_path), start=1):
        part = row.get("part", "").strip()
        gate1_row = gate1_by_part.get(part, {})
        rows.append(
            FirstPrintPrintBatchTravelerRow(
                print_order=order,
                part=part,
                source=gate1_row.get("source", "").strip(),
                target_x_mm=gate1_row.get("target_x_mm", "").strip(),
                target_y_mm=gate1_row.get("target_y_mm", "").strip(),
                target_z_mm=gate1_row.get("target_z_mm", "").strip(),
                queued_stl_path=row.get("queued_stl_path", "").strip(),
                queued_stl_sha256=row.get("queued_stl_sha256", "").strip(),
                sliced_output_path=row.get("sliced_output_path", "").strip(),
                sliced_output_sha256=row.get("sliced_output_sha256", "").strip(),
                selected_setup_summary=row.get("selected_setup_summary", "").strip(),
                gate1_qc_result=gate1_row.get("result", "").strip(),
            )
        )
    return tuple(rows)


def write_first_print_y_split_print_batch_traveler(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    sliced_output_path: str | Path,
    gate1_qc_path: str | Path,
    output_path: str | Path,
    expected_setup_summary: str = "",
    overwrite: bool = False,
) -> Path:
    sliced_audit = audit_first_print_y_split_sliced_outputs(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        worksheet_path=sliced_output_path,
        expected_setup_summary=expected_setup_summary,
    )
    if not sliced_audit.sliced_outputs_ready:
        raise ValueError("split sliced outputs are not print-ready")
    gate1_audit = audit_first_print_y_split_gate1_qc_worksheet(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        worksheet_path=gate1_qc_path,
    )
    if not gate1_audit.worksheet_valid:
        raise ValueError("split Gate 1 QC worksheet is not valid")

    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = first_print_print_batch_traveler_rows(
        sliced_output_path=sliced_output_path,
        gate1_qc_path=gate1_qc_path,
    )
    output.write_text(first_print_print_batch_traveler_csv(rows))
    return output


def _print_batch_traveler_issue(
    issues: list[FirstPrintPrintBatchTravelerIssue],
    *,
    part: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintPrintBatchTravelerIssue(
            part=part,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_print_batch_traveler(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    sliced_output_path: str | Path,
    gate1_qc_path: str | Path,
    worksheet_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintPrintBatchTravelerAudit:
    sliced_audit = audit_first_print_y_split_sliced_outputs(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        worksheet_path=sliced_output_path,
        expected_setup_summary=expected_setup_summary,
    )
    gate1_audit = audit_first_print_y_split_gate1_qc_worksheet(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        worksheet_path=gate1_qc_path,
    )
    expected_rows = first_print_print_batch_traveler_rows(
        sliced_output_path=sliced_output_path,
        gate1_qc_path=gate1_qc_path,
    )
    expected_by_part = {
        row.part: _first_print_print_batch_traveler_row_dict(row)
        for row in expected_rows
    }
    worksheet = Path(worksheet_path)
    issues: list[FirstPrintPrintBatchTravelerIssue] = []
    if not sliced_audit.sliced_outputs_ready:
        _print_batch_traveler_issue(
            issues,
            part="worksheet",
            field="Split sliced output worksheet",
            message="split sliced outputs are not print-ready",
        )
    if not gate1_audit.worksheet_valid:
        _print_batch_traveler_issue(
            issues,
            part="worksheet",
            field="Split Gate 1 QC worksheet",
            message="split Gate 1 QC worksheet is not valid",
        )
    if not worksheet.exists():
        _print_batch_traveler_issue(
            issues,
            part="worksheet",
            field="path",
            message="print batch traveler does not exist",
        )
        return FirstPrintPrintBatchTravelerAudit(
            worksheet_path=worksheet,
            expected_row_count=len(expected_rows),
            actual_row_count=0,
            print_result_counts={},
            missing_parts=tuple(expected_by_part),
            extra_parts=(),
            duplicate_parts=(),
            sliced_outputs_ready=sliced_audit.sliced_outputs_ready,
            gate1_qc_worksheet_valid=gate1_audit.worksheet_valid,
            issues=tuple(issues),
        )

    reader = csv.DictReader(StringIO(worksheet.read_text()))
    fieldnames = tuple(reader.fieldnames or ())
    expected_fields = set(FIRST_PRINT_PRINT_BATCH_TRAVELER_FIELDNAMES)
    missing_fields = tuple(
        field
        for field in FIRST_PRINT_PRINT_BATCH_TRAVELER_FIELDNAMES
        if field not in fieldnames
    )
    extra_fields = tuple(field for field in fieldnames if field not in expected_fields)
    if missing_fields:
        _print_batch_traveler_issue(
            issues,
            part="worksheet",
            field="header",
            message=f"missing columns: {', '.join(missing_fields)}",
        )
    if extra_fields:
        _print_batch_traveler_issue(
            issues,
            part="worksheet",
            field="header",
            message=f"extra columns: {', '.join(extra_fields)}",
        )

    rows = list(reader)
    counts = Counter(row.get("part", "").strip() for row in rows)
    actual_parts = set(counts) - {""}
    missing_parts = tuple(part for part in expected_by_part if part not in actual_parts)
    extra_parts = tuple(part for part in actual_parts if part not in expected_by_part)
    duplicate_parts = tuple(part for part, count in counts.items() if part and count > 1)
    print_result_counts = Counter(row.get("print_result", "").strip() for row in rows)
    order_counts = Counter(row.get("print_order", "").strip() for row in rows)

    for index, row in enumerate(rows, start=2):
        if None in row:
            _print_batch_traveler_issue(
                issues,
                part=f"line {index}",
                field="row",
                message="row has more cells than header fields",
            )
        part = row.get("part", "").strip()
        if not part:
            _print_batch_traveler_issue(
                issues,
                part=f"line {index}",
                field="part",
                message="part is required",
            )
            continue
        expected = expected_by_part.get(part)
        if expected is None:
            continue
        for field, expected_value in expected.items():
            if field in {"print_result", "print_evidence_path", "notes"}:
                continue
            actual_value = row.get(field, "").strip()
            if actual_value != expected_value:
                _print_batch_traveler_issue(
                    issues,
                    part=part,
                    field=field,
                    message=f"expected {expected_value}",
                )
        print_order = row.get("print_order", "").strip()
        if order_counts[print_order] > 1:
            _print_batch_traveler_issue(
                issues,
                part=part,
                field="print_order",
                message=f"duplicate print order {print_order}",
            )
        result = row.get("print_result", "").strip()
        if result not in FIRST_PRINT_PRINT_BATCH_TRAVELER_PRINT_RESULT_VALUES:
            allowed = ", ".join(sorted(FIRST_PRINT_PRINT_BATCH_TRAVELER_PRINT_RESULT_VALUES))
            _print_batch_traveler_issue(
                issues,
                part=part,
                field="print_result",
                message=f"expected one of {allowed}",
            )
            continue
        print_evidence_path = row.get("print_evidence_path", "").strip()
        if result == "not_printed" and print_evidence_path:
            _print_batch_traveler_issue(
                issues,
                part=part,
                field="print_evidence_path",
                message="not_printed row must not contain print evidence",
            )
        if result == "printed" and not print_evidence_path:
            _print_batch_traveler_issue(
                issues,
                part=part,
                field="print_evidence_path",
                message="printed row requires physical print evidence",
            )
        elif result == "printed":
            evidence_error = _worksheet_evidence_file_error(
                worksheet_path=worksheet,
                evidence_path=print_evidence_path,
                evidence_label="print evidence",
            )
            if evidence_error:
                _print_batch_traveler_issue(
                    issues,
                    part=part,
                    field="print_evidence_path",
                    message=evidence_error,
                )

    return FirstPrintPrintBatchTravelerAudit(
        worksheet_path=worksheet,
        expected_row_count=len(expected_rows),
        actual_row_count=len(rows),
        print_result_counts=dict(print_result_counts),
        missing_parts=missing_parts,
        extra_parts=extra_parts,
        duplicate_parts=duplicate_parts,
        sliced_outputs_ready=sliced_audit.sliced_outputs_ready,
        gate1_qc_worksheet_valid=gate1_audit.worksheet_valid,
        issues=tuple(issues),
    )


def _gate1_print_qc_issue(
    issues: list[FirstPrintGate1PrintQCIssue],
    *,
    part: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate1PrintQCIssue(
            part=part,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate1_print_qc(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate1PrintQCAudit:
    gate1_audit = audit_first_print_y_split_gate1_qc_worksheet(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        worksheet_path=gate1_qc_path,
    )
    traveler_audit = audit_first_print_y_split_print_batch_traveler(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        sliced_output_path=sliced_output_path,
        gate1_qc_path=gate1_qc_path,
        worksheet_path=print_batch_traveler_path,
        expected_setup_summary=expected_setup_summary,
    )
    traveler_rows = _csv_rows_from_path(print_batch_traveler_path)
    gate1_rows = _csv_rows_from_path(gate1_qc_path)
    traveler_by_part = {
        row.get("part", "").strip(): row for row in traveler_rows if row.get("part", "").strip()
    }
    expected_parts = tuple(row.get("part", "").strip() for row in gate1_rows)
    unprinted_parts = tuple(
        part
        for part in expected_parts
        if traveler_by_part.get(part, {}).get("print_result", "").strip() != "printed"
    )
    printed_row_count = sum(
        1
        for part in expected_parts
        if traveler_by_part.get(part, {}).get("print_result", "").strip() == "printed"
    )
    issues: list[FirstPrintGate1PrintQCIssue] = []
    for row in gate1_rows:
        part = row.get("part", "").strip()
        if row.get("result", "").strip() != "pass":
            continue
        traveler_result = traveler_by_part.get(part, {}).get("print_result", "").strip()
        if traveler_result != "printed":
            _gate1_print_qc_issue(
                issues,
                part=part,
                field="print_result",
                message=(
                    "Gate 1 pass row requires matching print batch traveler "
                    f"result printed, found {traveler_result or 'missing'}"
                ),
            )
            continue
        if not traveler_by_part.get(part, {}).get("print_evidence_path", "").strip():
            _gate1_print_qc_issue(
                issues,
                part=part,
                field="print_evidence_path",
                message="Gate 1 pass row requires print batch traveler evidence",
            )

    return FirstPrintGate1PrintQCAudit(
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        expected_row_count=gate1_audit.expected_row_count,
        printed_row_count=printed_row_count,
        unprinted_parts=unprinted_parts,
        gate1_qc_worksheet_valid=gate1_audit.worksheet_valid,
        gate1_pass_ready=gate1_audit.gate1_pass_ready,
        print_batch_handoff_ready=traveler_audit.handoff_ready,
        issues=tuple(issues),
    )


def _gate2_dry_assembly_readiness_issue(
    issues: list[FirstPrintGate2DryAssemblyReadinessIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate2DryAssemblyReadinessIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate2_dry_assembly_readiness(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate2DryAssemblyReadinessAudit:
    gate2_audit = audit_first_print_gate2_dry_assembly_worksheet(
        params=params,
        worksheet_path=gate2_dry_assembly_path,
    )
    gate1_print_qc_audit = audit_first_print_y_split_gate1_print_qc(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        expected_setup_summary=expected_setup_summary,
    )
    install_inventory_audit = audit_first_print_install_inventory(
        worksheet_path=install_inventory_path,
    )
    service_state_review_audit = audit_first_print_service_state_review(
        worksheet_path=service_state_review_path,
    )
    gate2_pass_targets = tuple(
        row.get("target", "").strip()
        for row in _csv_rows_from_path(gate2_dry_assembly_path)
        if row.get("target", "").strip()
        and row.get("result", "").strip() == "pass"
    )
    issues: list[FirstPrintGate2DryAssemblyReadinessIssue] = []
    if gate2_pass_targets and not gate1_print_qc_audit.print_qc_ready:
        _gate2_dry_assembly_readiness_issue(
            issues,
            target="Gate 2 dry assembly",
            field="Gate 1 print QC",
            message=(
                f"{len(gate2_pass_targets)} Gate 2 pass rows require "
                "split Gate 1 print-QC readiness"
            ),
        )
    if gate2_pass_targets and not install_inventory_audit.install_inventory_ready:
        _gate2_dry_assembly_readiness_issue(
            issues,
            target="Gate 2 dry assembly",
            field="Install inventory",
            message=(
                f"{len(gate2_pass_targets)} Gate 2 pass rows require "
                "ready installed-item inventory"
            ),
        )
    if gate2_pass_targets and not service_state_review_audit.service_state_review_ready:
        _gate2_dry_assembly_readiness_issue(
            issues,
            target="Gate 2 dry assembly",
            field="Service state review",
            message=(
                f"{len(gate2_pass_targets)} Gate 2 pass rows require "
                "ready installed/service/negative-review mode evidence"
            ),
        )

    return FirstPrintGate2DryAssemblyReadinessAudit(
        gate2_dry_assembly_worksheet_path=Path(gate2_dry_assembly_path),
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        install_inventory_path=Path(install_inventory_path),
        service_state_review_path=Path(service_state_review_path),
        gate2_dry_assembly_worksheet_valid=gate2_audit.worksheet_valid,
        gate2_dry_assembly_pass_ready=gate2_audit.gate2_pass_ready,
        gate2_pass_row_count=len(gate2_pass_targets),
        gate1_print_qc_ready=gate1_print_qc_audit.print_qc_ready,
        install_inventory_valid=install_inventory_audit.worksheet_valid,
        install_inventory_ready=install_inventory_audit.install_inventory_ready,
        service_state_review_valid=service_state_review_audit.worksheet_valid,
        service_state_review_ready=(
            service_state_review_audit.service_state_review_ready
        ),
        issues=tuple(issues),
    )


def _gate3_placement_readiness_issue(
    issues: list[FirstPrintGate3PlacementReadinessIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate3PlacementReadinessIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate3_placement_readiness(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    gate3_placement_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate3PlacementReadinessAudit:
    gate3_audit = audit_first_print_gate3_placement_worksheet(
        params=params,
        worksheet_path=gate3_placement_path,
    )
    gate2_readiness_audit = audit_first_print_y_split_gate2_dry_assembly_readiness(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        gate2_dry_assembly_path=gate2_dry_assembly_path,
        install_inventory_path=install_inventory_path,
        service_state_review_path=service_state_review_path,
        expected_setup_summary=expected_setup_summary,
    )
    gate3_pass_targets = tuple(
        row.get("target", "").strip()
        for row in _csv_rows_from_path(gate3_placement_path)
        if row.get("target", "").strip()
        and row.get("result", "").strip() == "pass"
    )
    issues: list[FirstPrintGate3PlacementReadinessIssue] = []
    if gate3_pass_targets and not gate2_readiness_audit.dry_assembly_ready:
        _gate3_placement_readiness_issue(
            issues,
            target="Gate 3 OT-2 placement",
            field="Gate 2 dry assembly",
            message=(
                f"{len(gate3_pass_targets)} Gate 3 pass rows require "
                "Gate 2 dry-assembly readiness"
            ),
        )

    return FirstPrintGate3PlacementReadinessAudit(
        gate3_placement_worksheet_path=Path(gate3_placement_path),
        gate2_dry_assembly_worksheet_path=Path(gate2_dry_assembly_path),
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        install_inventory_path=Path(install_inventory_path),
        gate3_placement_worksheet_valid=gate3_audit.worksheet_valid,
        gate3_placement_pass_ready=gate3_audit.gate3_pass_ready,
        gate3_pass_row_count=len(gate3_pass_targets),
        gate2_dry_assembly_ready=gate2_readiness_audit.dry_assembly_ready,
        gate2_dry_assembly_worksheet_valid=(
            gate2_readiness_audit.gate2_dry_assembly_worksheet_valid
        ),
        gate2_dry_assembly_pass_ready=(
            gate2_readiness_audit.gate2_dry_assembly_pass_ready
        ),
        gate2_pass_row_count=gate2_readiness_audit.gate2_pass_row_count,
        gate1_print_qc_ready=gate2_readiness_audit.gate1_print_qc_ready,
        install_inventory_ready=gate2_readiness_audit.install_inventory_ready,
        service_state_review_ready=gate2_readiness_audit.service_state_review_ready,
        issues=tuple(issues),
    )


def _gate4_wet_dry_witness_readiness_issue(
    issues: list[FirstPrintGate4WetDryWitnessReadinessIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate4WetDryWitnessReadinessIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate4_wet_dry_witness_readiness(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    gate3_placement_path: str | Path,
    gate4_wet_dry_witness_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate4WetDryWitnessReadinessAudit:
    gate4_audit = audit_first_print_gate4_wet_dry_witness_worksheet(
        params=params,
        worksheet_path=gate4_wet_dry_witness_path,
    )
    gate3_readiness_audit = audit_first_print_y_split_gate3_placement_readiness(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        gate2_dry_assembly_path=gate2_dry_assembly_path,
        install_inventory_path=install_inventory_path,
        service_state_review_path=service_state_review_path,
        gate3_placement_path=gate3_placement_path,
        expected_setup_summary=expected_setup_summary,
    )
    gate4_pass_targets = tuple(
        row.get("target", "").strip()
        for row in _csv_rows_from_path(gate4_wet_dry_witness_path)
        if row.get("target", "").strip()
        and row.get("result", "").strip() == "pass"
    )
    issues: list[FirstPrintGate4WetDryWitnessReadinessIssue] = []
    if gate4_pass_targets and not gate3_readiness_audit.placement_ready:
        _gate4_wet_dry_witness_readiness_issue(
            issues,
            target="Gate 4 wet/dry witness",
            field="Gate 3 placement",
            message=(
                f"{len(gate4_pass_targets)} Gate 4 pass rows require "
                "Gate 3 placement readiness"
            ),
        )

    return FirstPrintGate4WetDryWitnessReadinessAudit(
        gate4_wet_dry_witness_worksheet_path=Path(gate4_wet_dry_witness_path),
        gate3_placement_worksheet_path=Path(gate3_placement_path),
        gate2_dry_assembly_worksheet_path=Path(gate2_dry_assembly_path),
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        install_inventory_path=Path(install_inventory_path),
        gate4_wet_dry_witness_worksheet_valid=gate4_audit.worksheet_valid,
        gate4_wet_dry_witness_pass_ready=gate4_audit.gate4_pass_ready,
        gate4_pass_row_count=len(gate4_pass_targets),
        gate3_placement_ready=gate3_readiness_audit.placement_ready,
        gate3_placement_worksheet_valid=(
            gate3_readiness_audit.gate3_placement_worksheet_valid
        ),
        gate3_placement_pass_ready=(
            gate3_readiness_audit.gate3_placement_pass_ready
        ),
        gate3_pass_row_count=gate3_readiness_audit.gate3_pass_row_count,
        gate2_dry_assembly_ready=gate3_readiness_audit.gate2_dry_assembly_ready,
        gate2_pass_row_count=gate3_readiness_audit.gate2_pass_row_count,
        gate1_print_qc_ready=gate3_readiness_audit.gate1_print_qc_ready,
        install_inventory_ready=gate3_readiness_audit.install_inventory_ready,
        service_state_review_ready=gate3_readiness_audit.service_state_review_ready,
        issues=tuple(issues),
    )


def _gate5_consumable_puncture_readiness_issue(
    issues: list[FirstPrintGate5ConsumablePunctureReadinessIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate5ConsumablePunctureReadinessIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate5_consumable_puncture_readiness(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    gate3_placement_path: str | Path,
    gate4_wet_dry_witness_path: str | Path,
    gate5_consumable_puncture_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate5ConsumablePunctureReadinessAudit:
    gate5_audit = audit_first_print_gate5_consumable_puncture_worksheet(
        params=params,
        worksheet_path=gate5_consumable_puncture_path,
    )
    gate4_readiness_audit = audit_first_print_y_split_gate4_wet_dry_witness_readiness(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        gate2_dry_assembly_path=gate2_dry_assembly_path,
        install_inventory_path=install_inventory_path,
        service_state_review_path=service_state_review_path,
        gate3_placement_path=gate3_placement_path,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness_path,
        expected_setup_summary=expected_setup_summary,
    )
    gate5_pass_targets = tuple(
        row.get("target", "").strip()
        for row in _csv_rows_from_path(gate5_consumable_puncture_path)
        if row.get("target", "").strip()
        and row.get("result", "").strip() == "pass"
    )
    issues: list[FirstPrintGate5ConsumablePunctureReadinessIssue] = []
    if gate5_pass_targets and not gate4_readiness_audit.wet_dry_witness_ready:
        _gate5_consumable_puncture_readiness_issue(
            issues,
            target="Gate 5 consumable/puncture",
            field="Gate 4 wet/dry witness",
            message=(
                f"{len(gate5_pass_targets)} Gate 5 pass rows require "
                "Gate 4 wet/dry witness readiness"
            ),
        )

    return FirstPrintGate5ConsumablePunctureReadinessAudit(
        gate5_consumable_puncture_worksheet_path=Path(gate5_consumable_puncture_path),
        gate4_wet_dry_witness_worksheet_path=Path(gate4_wet_dry_witness_path),
        gate3_placement_worksheet_path=Path(gate3_placement_path),
        gate2_dry_assembly_worksheet_path=Path(gate2_dry_assembly_path),
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        install_inventory_path=Path(install_inventory_path),
        gate5_consumable_puncture_worksheet_valid=gate5_audit.worksheet_valid,
        gate5_consumable_puncture_pass_ready=gate5_audit.gate5_pass_ready,
        gate5_pass_row_count=len(gate5_pass_targets),
        gate4_wet_dry_witness_ready=(
            gate4_readiness_audit.wet_dry_witness_ready
        ),
        gate4_wet_dry_witness_worksheet_valid=(
            gate4_readiness_audit.gate4_wet_dry_witness_worksheet_valid
        ),
        gate4_wet_dry_witness_pass_ready=(
            gate4_readiness_audit.gate4_wet_dry_witness_pass_ready
        ),
        gate4_pass_row_count=gate4_readiness_audit.gate4_pass_row_count,
        gate3_placement_ready=gate4_readiness_audit.gate3_placement_ready,
        gate3_pass_row_count=gate4_readiness_audit.gate3_pass_row_count,
        gate2_dry_assembly_ready=gate4_readiness_audit.gate2_dry_assembly_ready,
        gate2_pass_row_count=gate4_readiness_audit.gate2_pass_row_count,
        gate1_print_qc_ready=gate4_readiness_audit.gate1_print_qc_ready,
        install_inventory_ready=gate4_readiness_audit.install_inventory_ready,
        service_state_review_ready=gate4_readiness_audit.service_state_review_ready,
        issues=tuple(issues),
    )


def _gate6_sensor_thermal_readiness_issue(
    issues: list[FirstPrintGate6SensorThermalReadinessIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate6SensorThermalReadinessIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate6_sensor_thermal_readiness(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    gate3_placement_path: str | Path,
    gate4_wet_dry_witness_path: str | Path,
    gate5_consumable_puncture_path: str | Path,
    gate6_sensor_thermal_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate6SensorThermalReadinessAudit:
    gate6_audit = audit_first_print_gate6_sensor_thermal_worksheet(
        params=params,
        worksheet_path=gate6_sensor_thermal_path,
    )
    gate5_readiness_audit = audit_first_print_y_split_gate5_consumable_puncture_readiness(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        gate2_dry_assembly_path=gate2_dry_assembly_path,
        install_inventory_path=install_inventory_path,
        service_state_review_path=service_state_review_path,
        gate3_placement_path=gate3_placement_path,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness_path,
        gate5_consumable_puncture_path=gate5_consumable_puncture_path,
        expected_setup_summary=expected_setup_summary,
    )
    install_inventory_audit = audit_first_print_install_inventory(
        worksheet_path=install_inventory_path,
    )
    gate6_pass_targets = tuple(
        row.get("target", "").strip()
        for row in _csv_rows_from_path(gate6_sensor_thermal_path)
        if row.get("target", "").strip()
        and row.get("result", "").strip() == "pass"
    )
    issues: list[FirstPrintGate6SensorThermalReadinessIssue] = []
    if gate6_pass_targets and not gate5_readiness_audit.consumable_puncture_ready:
        _gate6_sensor_thermal_readiness_issue(
            issues,
            target="Gate 6 sensor/thermal",
            field="Gate 5 consumable/puncture",
            message=(
                f"{len(gate6_pass_targets)} Gate 6 pass rows require "
                "Gate 5 consumable/puncture readiness"
            ),
        )
    if gate6_pass_targets and not install_inventory_audit.real_sensor_inventory_ready:
        blank_parts = ", ".join(install_inventory_audit.sensor_inventory_blank_parts)
        message = (
            f"{len(gate6_pass_targets)} Gate 6 pass rows require real sensor "
            "and electrical installed items"
        )
        if blank_parts:
            message += f"; dimensional blanks found for {blank_parts}"
        _gate6_sensor_thermal_readiness_issue(
            issues,
            target="Gate 6 sensor/thermal",
            field="Install inventory",
            message=message,
        )

    return FirstPrintGate6SensorThermalReadinessAudit(
        gate6_sensor_thermal_worksheet_path=Path(gate6_sensor_thermal_path),
        gate5_consumable_puncture_worksheet_path=Path(gate5_consumable_puncture_path),
        gate4_wet_dry_witness_worksheet_path=Path(gate4_wet_dry_witness_path),
        gate3_placement_worksheet_path=Path(gate3_placement_path),
        gate2_dry_assembly_worksheet_path=Path(gate2_dry_assembly_path),
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        install_inventory_path=Path(install_inventory_path),
        gate6_sensor_thermal_worksheet_valid=gate6_audit.worksheet_valid,
        gate6_sensor_thermal_pass_ready=gate6_audit.gate6_pass_ready,
        gate6_pass_row_count=len(gate6_pass_targets),
        gate5_consumable_puncture_ready=(
            gate5_readiness_audit.consumable_puncture_ready
        ),
        gate5_consumable_puncture_worksheet_valid=(
            gate5_readiness_audit.gate5_consumable_puncture_worksheet_valid
        ),
        gate5_consumable_puncture_pass_ready=(
            gate5_readiness_audit.gate5_consumable_puncture_pass_ready
        ),
        gate5_pass_row_count=gate5_readiness_audit.gate5_pass_row_count,
        gate4_wet_dry_witness_ready=(
            gate5_readiness_audit.gate4_wet_dry_witness_ready
        ),
        gate4_pass_row_count=gate5_readiness_audit.gate4_pass_row_count,
        gate3_placement_ready=gate5_readiness_audit.gate3_placement_ready,
        gate3_pass_row_count=gate5_readiness_audit.gate3_pass_row_count,
        gate2_dry_assembly_ready=gate5_readiness_audit.gate2_dry_assembly_ready,
        gate2_pass_row_count=gate5_readiness_audit.gate2_pass_row_count,
        gate1_print_qc_ready=gate5_readiness_audit.gate1_print_qc_ready,
        install_inventory_ready=gate5_readiness_audit.install_inventory_ready,
        service_state_review_ready=gate5_readiness_audit.service_state_review_ready,
        real_sensor_inventory_ready=install_inventory_audit.real_sensor_inventory_ready,
        sensor_inventory_blank_parts=install_inventory_audit.sensor_inventory_blank_parts,
        issues=tuple(issues),
    )


def _operating_prototype_acceptance_issue(
    issues: list[FirstPrintOperatingPrototypeAcceptanceIssue],
    *,
    field: str,
    message: str,
) -> None:
    issues.append(FirstPrintOperatingPrototypeAcceptanceIssue(field=field, message=message))


def audit_first_print_y_split_operating_prototype_acceptance(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    queue_dir: str | Path,
    split_dir: str | Path,
    split_queue_dir: str | Path,
    record_path: str | Path,
    root: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    gate3_placement_path: str | Path,
    gate4_wet_dry_witness_path: str | Path,
    gate5_consumable_puncture_path: str | Path,
    gate6_sensor_thermal_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintOperatingPrototypeAcceptanceAudit:
    preflight_audit = audit_first_print_preflight(
        params=params,
        out_dir=out_dir,
        queue_dir=queue_dir,
        split_dir=split_dir,
        record_path=record_path,
        root=root,
    )
    gate6_readiness_audit = audit_first_print_y_split_gate6_sensor_thermal_readiness(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=split_queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        gate2_dry_assembly_path=gate2_dry_assembly_path,
        install_inventory_path=install_inventory_path,
        service_state_review_path=service_state_review_path,
        gate3_placement_path=gate3_placement_path,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness_path,
        gate5_consumable_puncture_path=gate5_consumable_puncture_path,
        gate6_sensor_thermal_path=gate6_sensor_thermal_path,
        expected_setup_summary=expected_setup_summary,
    )
    blocking_preflight_issues = tuple(
        issue
        for issue in preflight_audit.issues
        if issue.field not in FIRST_PRINT_PHYSICAL_GATES
    )
    preflight_artifacts_ready = (
        preflight_audit.package_ready
        and preflight_audit.slicer_queue_ready
        and preflight_audit.params_hash_matches
        and preflight_audit.generated_output_timestamp_matches
        and preflight_audit.cad_target_sections_match
        and preflight_audit.slicer_setup_valid
        and preflight_audit.slicer_setup_selected
        and preflight_audit.slicer_bed_fit_ready
        and preflight_audit.sliced_outputs_valid
        and preflight_audit.gate1_qc_worksheet_valid
        and preflight_audit.gate2_dry_assembly_worksheet_valid
        and preflight_audit.gate3_placement_worksheet_valid
        and preflight_audit.gate4_wet_dry_witness_worksheet_valid
        and preflight_audit.gate5_consumable_puncture_worksheet_valid
        and preflight_audit.gate6_sensor_thermal_worksheet_valid
        and preflight_audit.install_inventory_valid
        and preflight_audit.service_state_review_valid
        and preflight_audit.service_state_review_ready
        and preflight_audit.record_gate0_pass
        and preflight_audit.required_session_fields_present
        and not preflight_audit.missing_record_links
        and not blocking_preflight_issues
    )
    issues: list[FirstPrintOperatingPrototypeAcceptanceIssue] = []
    for issue in blocking_preflight_issues:
        _operating_prototype_acceptance_issue(
            issues,
            field=issue.field,
            message=issue.message,
        )
    for issue in gate6_readiness_audit.issues:
        _operating_prototype_acceptance_issue(
            issues,
            field=issue.field,
            message=issue.message,
        )
    if preflight_audit.physical_gate_passes and not gate6_readiness_audit.sensor_thermal_ready:
        _operating_prototype_acceptance_issue(
            issues,
            field="Physical gate summary",
            message=(
                f"{len(preflight_audit.physical_gate_passes)} record pass rows "
                "require complete Gate 6 sensor/thermal readiness"
            ),
        )

    return FirstPrintOperatingPrototypeAcceptanceAudit(
        record_path=Path(record_path),
        preflight_artifacts_ready=preflight_artifacts_ready,
        print_start_ready=preflight_artifacts_ready and preflight_audit.sliced_outputs_ready,
        service_state_review_ready=preflight_audit.service_state_review_ready,
        install_inventory_ready=gate6_readiness_audit.install_inventory_ready,
        gate1_print_qc_ready=gate6_readiness_audit.gate1_print_qc_ready,
        gate2_dry_assembly_ready=gate6_readiness_audit.gate2_dry_assembly_ready,
        gate2_pass_row_count=gate6_readiness_audit.gate2_pass_row_count,
        gate3_placement_ready=gate6_readiness_audit.gate3_placement_ready,
        gate3_pass_row_count=gate6_readiness_audit.gate3_pass_row_count,
        gate4_wet_dry_witness_ready=(
            gate6_readiness_audit.gate4_wet_dry_witness_ready
        ),
        gate4_pass_row_count=gate6_readiness_audit.gate4_pass_row_count,
        gate5_consumable_puncture_ready=(
            gate6_readiness_audit.gate5_consumable_puncture_ready
        ),
        gate5_pass_row_count=gate6_readiness_audit.gate5_pass_row_count,
        sensor_thermal_ready=gate6_readiness_audit.sensor_thermal_ready,
        real_sensor_inventory_ready=(
            gate6_readiness_audit.real_sensor_inventory_ready
        ),
        sensor_inventory_blank_parts=(
            gate6_readiness_audit.sensor_inventory_blank_parts
        ),
        gate6_sensor_thermal_worksheet_valid=(
            gate6_readiness_audit.gate6_sensor_thermal_worksheet_valid
        ),
        gate6_sensor_thermal_pass_ready=(
            gate6_readiness_audit.gate6_sensor_thermal_pass_ready
        ),
        gate6_pass_row_count=gate6_readiness_audit.gate6_pass_row_count,
        physical_gate_passes=preflight_audit.physical_gate_passes,
        issues=tuple(issues),
    )


def _preflight_issue(
    issues: list[FirstPrintPreflightIssue],
    *,
    field: str,
    message: str,
) -> None:
    issues.append(FirstPrintPreflightIssue(field=field, message=message))


def _record_table_value(record_text: str, field: str) -> str:
    for line in record_text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] == field:
            return cells[1]
    return ""


def first_print_record_table_value(record_path: str | Path, field: str) -> str:
    record = Path(record_path)
    if not record.exists():
        return ""
    return _record_table_value(record.read_text(), field)


def _record_gate_result(record_text: str, gate: str) -> str:
    for line in record_text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] == gate:
            return cells[1]
    return ""


def _markdown_path_value(value: str, root: Path) -> Path:
    cleaned = value.strip().strip("`").strip()
    path = Path(cleaned)
    return path if path.is_absolute() else root / path


def audit_first_print_preflight(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    queue_dir: str | Path,
    record_path: str | Path,
    root: str | Path,
    split_dir: str | Path | None = None,
) -> FirstPrintPreflightAudit:
    record = Path(record_path)
    root_path = Path(root)
    out_path = Path(out_dir)
    split_dir_path = (
        Path(split_dir) if split_dir is not None else out_path / "first_print_y_split_parts"
    )
    issues: list[FirstPrintPreflightIssue] = []

    package_audit = audit_first_print_package(params, out_path)

    record_text = ""
    if record.exists():
        record_text = record.read_text()
    else:
        _preflight_issue(
            issues,
            field="Measurement record",
            message="record file does not exist",
        )

    linked_paths: dict[str, Path] = {}
    missing_record_links: list[str] = []
    missing_session_fields: list[str] = []
    expected_params_sha256 = ""
    record_params_sha256 = ""
    expected_generated_output_timestamp = latest_required_artifact_timestamp(
        package_audit
    )
    record_generated_output_timestamp = ""
    params_hash_matches = False
    generated_output_timestamp_matches = not package_audit.ready
    stale_cad_target_sections: tuple[str, ...] = ()
    cad_target_sections_match = False
    active_queue_mode = ""
    if record_text:
        stale_cad_target_sections = tuple(
            section_name
            for section_name, section_markdown in first_print_cad_target_sections_markdown(
                params
            ).items()
            if section_markdown not in record_text
        )
        cad_target_sections_match = not stale_cad_target_sections
        for section_name in stale_cad_target_sections:
            _preflight_issue(
                issues,
                field=section_name,
                message="generated CAD target section is missing or stale",
            )
        for field in FIRST_PRINT_PREFLIGHT_REQUIRED_SESSION_FIELDS:
            raw_value = _record_table_value(record_text, field)
            if not raw_value:
                missing_session_fields.append(field)
                _preflight_issue(
                    issues,
                    field=field,
                    message="required session field is blank or missing",
                )
        active_queue_mode = _record_table_value(
            record_text,
            FIRST_PRINT_ACTIVE_QUEUE_MODE_FIELD,
        )
        if active_queue_mode and active_queue_mode not in FIRST_PRINT_ACTIVE_QUEUE_MODE_VALUES:
            _preflight_issue(
                issues,
                field=FIRST_PRINT_ACTIVE_QUEUE_MODE_FIELD,
                message=(
                    "expected one of "
                    f"{', '.join(FIRST_PRINT_ACTIVE_QUEUE_MODE_VALUES)}"
                ),
            )
        for field in FIRST_PRINT_PREFLIGHT_LINK_FIELDS:
            raw_value = _record_table_value(record_text, field)
            if not raw_value:
                missing_record_links.append(field)
                _preflight_issue(
                    issues,
                    field=field,
                    message="record link is blank or missing",
                )
                continue
            linked_path = _markdown_path_value(raw_value, root_path)
            linked_paths[field] = linked_path
            if not linked_path.exists():
                missing_record_links.append(field)
                _preflight_issue(
                    issues,
                    field=field,
                    message=f"linked path does not exist: {linked_path}",
                )
        record_params_sha256 = _record_table_value(record_text, "Params SHA256")
        params_path = linked_paths.get("Params file")
        if not record_params_sha256:
            _preflight_issue(
                issues,
                field="Params SHA256",
                message="record params hash is blank or missing",
            )
        elif params_path and params_path.exists():
            expected_params_sha256 = file_sha256(params_path)
            params_hash_matches = record_params_sha256 == expected_params_sha256
            if not params_hash_matches:
                _preflight_issue(
                    issues,
                    field="Params SHA256",
                    message=(
                        "record params hash does not match params file: "
                        f"{expected_params_sha256}"
                    ),
                )

        if active_queue_mode == FIRST_PRINT_ACTIVE_QUEUE_MODE_SPLIT_Y:
            for field in FIRST_PRINT_SPLIT_PREFLIGHT_LINK_FIELDS:
                raw_value = _record_table_value(record_text, field)
                if not raw_value:
                    missing_record_links.append(field)
                    _preflight_issue(
                        issues,
                        field=field,
                        message="record link is blank or missing",
                    )
                    continue
                linked_path = _markdown_path_value(raw_value, root_path)
                linked_paths[field] = linked_path
                if not linked_path.exists():
                    missing_record_links.append(field)
                    _preflight_issue(
                        issues,
                        field=field,
                        message=f"linked path does not exist: {linked_path}",
                    )

        record_generated_output_timestamp = _record_table_value(
            record_text,
            "Generated output timestamp",
        )
        if package_audit.ready:
            generated_output_timestamp_matches = (
                record_generated_output_timestamp == expected_generated_output_timestamp
            )
            if not record_generated_output_timestamp:
                _preflight_issue(
                    issues,
                    field="Generated output timestamp",
                    message="record generated output timestamp is blank or missing",
                )
            elif not generated_output_timestamp_matches:
                _preflight_issue(
                    issues,
                    field="Generated output timestamp",
                    message=(
                        "record generated output timestamp does not match current "
                        f"package: {expected_generated_output_timestamp}"
                    ),
                )

    gate1_path = linked_paths.get(
        "Gate 1 QC worksheet",
        root_path / "missing_gate1_qc_worksheet.csv",
    )
    gate2_dry_assembly_path = linked_paths.get(
        "Gate 2 dry assembly worksheet",
        root_path / "missing_gate2_dry_assembly_worksheet.csv",
    )
    gate3_placement_path = linked_paths.get(
        "Gate 3 placement worksheet",
        root_path / "missing_gate3_placement_worksheet.csv",
    )
    gate4_wet_dry_witness_path = linked_paths.get(
        "Gate 4 wet/dry witness worksheet",
        root_path / "missing_gate4_wet_dry_witness_worksheet.csv",
    )
    gate5_consumable_puncture_path = linked_paths.get(
        "Gate 5 consumable/puncture worksheet",
        root_path / "missing_gate5_consumable_puncture_worksheet.csv",
    )
    gate6_sensor_thermal_path = linked_paths.get(
        "Gate 6 sensor/thermal worksheet",
        root_path / "missing_gate6_sensor_thermal_worksheet.csv",
    )
    slicer_setup_path = linked_paths.get(
        "Slicer setup worksheet",
        root_path / "missing_slicer_setup.csv",
    )
    sliced_outputs_path = linked_paths.get(
        "Sliced output worksheet",
        root_path / "missing_sliced_outputs.csv",
    )
    split_slicer_queue_path = linked_paths.get(
        "Split slicer queue",
        root_path / "missing_split_slicer_queue",
    )
    split_sliced_outputs_path = linked_paths.get(
        "Split sliced output worksheet",
        root_path / "missing_split_sliced_outputs.csv",
    )
    split_gate1_path = linked_paths.get(
        "Split Gate 1 QC worksheet",
        root_path / "missing_split_gate1_qc_worksheet.csv",
    )
    install_inventory_path = linked_paths.get(
        "Install inventory worksheet",
        root_path / "missing_install_inventory.csv",
    )
    service_state_review_path = linked_paths.get(
        "Service state review worksheet",
        root_path / "missing_service_state_review.csv",
    )
    slicer_setup_audit = audit_first_print_slicer_setup(
        worksheet_path=slicer_setup_path,
    )
    use_split_queue = active_queue_mode == FIRST_PRINT_ACTIVE_QUEUE_MODE_SPLIT_Y
    if use_split_queue:
        slicer_queue_audit = audit_first_print_slicer_queue_manifest(
            split_slicer_queue_path
        )
        split_artifact_audit = audit_first_print_y_split_artifacts(
            params=params,
            out_dir=out_path,
            split_dir=split_dir_path,
            slicer_setup_path=slicer_setup_path,
        )
        split_oversized_parts = tuple(
            row.split_part for row in split_artifact_audit.rows if not row.fits_selected_bed
        )
        slicer_bed_fit_ready = split_artifact_audit.split_artifacts_ready
        slicer_bed_x_mm = split_artifact_audit.bed_x_mm
        slicer_bed_y_mm = split_artifact_audit.bed_y_mm
        slicer_bed_oversized_parts = (
            *split_artifact_audit.missing_oversized_parts,
            *split_oversized_parts,
        )
        sliced_outputs_audit = audit_first_print_y_split_sliced_outputs(
            params=params,
            out_dir=out_path,
            split_dir=split_dir_path,
            queue_dir=split_slicer_queue_path,
            slicer_setup_path=slicer_setup_path,
            worksheet_path=split_sliced_outputs_path,
            expected_setup_summary=slicer_setup_audit.selected_setup_summary,
        )
        gate1_audit = _audit_first_print_gate1_qc_worksheet_from_expected_rows(
            worksheet_path=split_gate1_path,
            expected_rows=first_print_gate1_qc_rows_from_slicer_queue_manifest(
                split_slicer_queue_path
            ),
            tolerance_mm=FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM,
        )
    else:
        slicer_queue_audit = audit_first_print_slicer_queue(
            params=params,
            out_dir=out_path,
            queue_dir=queue_dir,
        )
        slicer_bed_fit_audit = audit_first_print_slicer_bed_fit(
            params=params,
            out_dir=out_path,
            worksheet_path=slicer_setup_path,
        )
        slicer_bed_fit_ready = slicer_bed_fit_audit.bed_fit_ready
        slicer_bed_x_mm = slicer_bed_fit_audit.bed_x_mm
        slicer_bed_y_mm = slicer_bed_fit_audit.bed_y_mm
        slicer_bed_oversized_parts = tuple(
            item.part for item in slicer_bed_fit_audit.oversized_parts
        )
        sliced_outputs_audit = audit_first_print_sliced_outputs(
            params=params,
            out_dir=out_path,
            queue_dir=queue_dir,
            worksheet_path=sliced_outputs_path,
            expected_setup_summary=slicer_setup_audit.selected_setup_summary,
        )
        gate1_audit = audit_first_print_gate1_qc_worksheet(
            params=params,
            worksheet_path=gate1_path,
        )
    gate2_dry_assembly_audit = audit_first_print_gate2_dry_assembly_worksheet(
        params=params,
        worksheet_path=gate2_dry_assembly_path,
    )
    gate3_placement_audit = audit_first_print_gate3_placement_worksheet(
        params=params,
        worksheet_path=gate3_placement_path,
    )
    gate4_wet_dry_witness_audit = audit_first_print_gate4_wet_dry_witness_worksheet(
        params=params,
        worksheet_path=gate4_wet_dry_witness_path,
    )
    gate5_consumable_puncture_audit = (
        audit_first_print_gate5_consumable_puncture_worksheet(
            params=params,
            worksheet_path=gate5_consumable_puncture_path,
        )
    )
    gate6_sensor_thermal_audit = audit_first_print_gate6_sensor_thermal_worksheet(
        params=params,
        worksheet_path=gate6_sensor_thermal_path,
    )
    install_inventory_audit = audit_first_print_install_inventory(
        worksheet_path=install_inventory_path,
    )
    service_state_review_audit = audit_first_print_service_state_review(
        worksheet_path=service_state_review_path,
    )

    record_gate0_pass = False
    physical_gate_passes: tuple[str, ...] = ()
    printer_material_profile = ""
    if record_text:
        printer_material_profile = _record_table_value(
            record_text,
            "Printer / material / profile",
        )
        gate0_result = _record_gate_result(record_text, "Gate 0 CAD Artifact Identity")
        record_gate0_pass = gate0_result == "pass"
        if not record_gate0_pass:
            _preflight_issue(
                issues,
                field="Gate 0 CAD Artifact Identity",
                message=f"expected pass, found {gate0_result or 'missing'}",
            )
        physical_gate_passes = tuple(
            gate
            for gate in FIRST_PRINT_PHYSICAL_GATES
            if _record_gate_result(record_text, gate) == "pass"
        )
        for gate in physical_gate_passes:
            _preflight_issue(
                issues,
                field=gate,
                message="physical gate is passed before preflight is closed",
            )
        if (
            slicer_setup_audit.selected_setup_summary
            and printer_material_profile != slicer_setup_audit.selected_setup_summary
        ):
            _preflight_issue(
                issues,
                field="Printer / material / profile",
                message=(
                    "record value must match selected slicer setup: "
                    f"{slicer_setup_audit.selected_setup_summary}"
                ),
            )

    if not package_audit.ready:
        _preflight_issue(
            issues,
            field="CAD package",
            message=f"{len(package_audit.missing_paths)} required paths missing",
        )
    if not slicer_queue_audit.ready:
        _preflight_issue(
            issues,
            field="Slicer queue",
            message="slicer queue audit is not ready",
        )
    if not slicer_setup_audit.worksheet_valid:
        _preflight_issue(
            issues,
            field="Slicer setup worksheet",
            message=f"{len(slicer_setup_audit.issues)} setup issues",
        )
    if not slicer_setup_audit.setup_selected:
        _preflight_issue(
            issues,
            field="Slicer setup worksheet",
            message="exactly one passing slicer setup row must be selected",
        )
    if not slicer_bed_fit_ready:
        _preflight_issue(
            issues,
            field="Slicer bed fit",
            message=(
                f"{len(slicer_bed_oversized_parts) or 1} bed-fit issues "
                f"for active queue mode {active_queue_mode or 'missing'}"
            ),
        )
    if not sliced_outputs_audit.worksheet_valid:
        _preflight_issue(
            issues,
            field="Sliced output worksheet",
            message=f"{len(sliced_outputs_audit.issues)} sliced-output issues",
        )
    if not gate1_audit.worksheet_valid:
        _preflight_issue(
            issues,
            field="Gate 1 QC worksheet",
            message=f"{len(gate1_audit.issues)} worksheet issues",
        )
    if not gate2_dry_assembly_audit.worksheet_valid:
        _preflight_issue(
            issues,
            field="Gate 2 dry assembly worksheet",
            message=f"{len(gate2_dry_assembly_audit.issues)} worksheet issues",
        )
    if not gate3_placement_audit.worksheet_valid:
        _preflight_issue(
            issues,
            field="Gate 3 placement worksheet",
            message=f"{len(gate3_placement_audit.issues)} worksheet issues",
        )
    if not gate4_wet_dry_witness_audit.worksheet_valid:
        _preflight_issue(
            issues,
            field="Gate 4 wet/dry witness worksheet",
            message=f"{len(gate4_wet_dry_witness_audit.issues)} worksheet issues",
        )
    if not gate5_consumable_puncture_audit.worksheet_valid:
        _preflight_issue(
            issues,
            field="Gate 5 consumable/puncture worksheet",
            message=f"{len(gate5_consumable_puncture_audit.issues)} worksheet issues",
        )
    if not gate6_sensor_thermal_audit.worksheet_valid:
        _preflight_issue(
            issues,
            field="Gate 6 sensor/thermal worksheet",
            message=f"{len(gate6_sensor_thermal_audit.issues)} worksheet issues",
        )
    if not install_inventory_audit.worksheet_valid:
        _preflight_issue(
            issues,
            field="Install inventory worksheet",
            message=f"{len(install_inventory_audit.issues)} inventory issues",
        )
    if not service_state_review_audit.worksheet_valid:
        _preflight_issue(
            issues,
            field="Service state review worksheet",
            message=f"{len(service_state_review_audit.issues)} service-state issues",
        )
    elif not service_state_review_audit.service_state_review_ready:
        _preflight_issue(
            issues,
            field="Service state review worksheet",
            message="service-state review must be pass-ready before preflight closes",
        )

    return FirstPrintPreflightAudit(
        record_path=record,
        active_queue_mode=active_queue_mode,
        package_ready=package_audit.ready,
        slicer_queue_ready=slicer_queue_audit.ready,
        params_hash_matches=params_hash_matches,
        generated_output_timestamp_matches=generated_output_timestamp_matches,
        cad_target_sections_match=cad_target_sections_match,
        expected_params_sha256=expected_params_sha256,
        record_params_sha256=record_params_sha256,
        expected_generated_output_timestamp=expected_generated_output_timestamp,
        record_generated_output_timestamp=record_generated_output_timestamp,
        slicer_setup_valid=slicer_setup_audit.worksheet_valid,
        slicer_setup_selected=slicer_setup_audit.setup_selected,
        selected_slicer_setup=slicer_setup_audit.selected_setup_summary,
        slicer_bed_fit_ready=slicer_bed_fit_ready,
        slicer_bed_x_mm=slicer_bed_x_mm,
        slicer_bed_y_mm=slicer_bed_y_mm,
        slicer_bed_oversized_parts=tuple(slicer_bed_oversized_parts),
        sliced_outputs_valid=sliced_outputs_audit.worksheet_valid,
        sliced_outputs_ready=sliced_outputs_audit.sliced_outputs_ready,
        gate1_qc_worksheet_valid=gate1_audit.worksheet_valid,
        gate1_pass_ready=gate1_audit.gate1_pass_ready,
        gate2_dry_assembly_worksheet_valid=gate2_dry_assembly_audit.worksheet_valid,
        gate2_dry_assembly_pass_ready=gate2_dry_assembly_audit.gate2_pass_ready,
        gate3_placement_worksheet_valid=gate3_placement_audit.worksheet_valid,
        gate3_placement_pass_ready=gate3_placement_audit.gate3_pass_ready,
        gate4_wet_dry_witness_worksheet_valid=(
            gate4_wet_dry_witness_audit.worksheet_valid
        ),
        gate4_wet_dry_witness_pass_ready=(
            gate4_wet_dry_witness_audit.gate4_pass_ready
        ),
        gate5_consumable_puncture_worksheet_valid=(
            gate5_consumable_puncture_audit.worksheet_valid
        ),
        gate5_consumable_puncture_pass_ready=(
            gate5_consumable_puncture_audit.gate5_pass_ready
        ),
        gate6_sensor_thermal_worksheet_valid=(
            gate6_sensor_thermal_audit.worksheet_valid
        ),
        gate6_sensor_thermal_pass_ready=(
            gate6_sensor_thermal_audit.gate6_pass_ready
        ),
        install_inventory_valid=install_inventory_audit.worksheet_valid,
        install_inventory_ready=install_inventory_audit.install_inventory_ready,
        service_state_review_valid=service_state_review_audit.worksheet_valid,
        service_state_review_ready=(
            service_state_review_audit.service_state_review_ready
        ),
        record_gate0_pass=record_gate0_pass,
        required_session_fields_present=not missing_session_fields,
        missing_session_fields=tuple(missing_session_fields),
        physical_gate_passes=physical_gate_passes,
        missing_record_links=tuple(missing_record_links),
        stale_cad_target_sections=stale_cad_target_sections,
        issues=tuple(issues),
    )


def write_first_print_package_manifest(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    audit = audit_first_print_package(params, out_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(first_print_package_manifest_markdown(params, audit))
    return output


def write_first_print_gate1_qc_worksheet(
    *,
    params: dict[str, Any],
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(first_print_gate1_qc_worksheet_csv(params))
    return output


def write_first_print_y_split_gate1_qc_worksheet(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        first_print_y_split_gate1_qc_worksheet_csv(
            params=params,
            out_dir=out_dir,
            split_dir=split_dir,
            queue_dir=queue_dir,
            slicer_setup_path=slicer_setup_path,
        )
    )
    return output


def write_first_print_gate2_dry_assembly_worksheet(
    *,
    params: dict[str, Any],
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(first_print_gate2_dry_assembly_worksheet_csv(params))
    return output


def write_first_print_gate3_placement_worksheet(
    *,
    params: dict[str, Any],
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(first_print_gate3_placement_worksheet_csv(params))
    return output


def write_first_print_gate4_wet_dry_witness_worksheet(
    *,
    params: dict[str, Any],
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(first_print_gate4_wet_dry_witness_worksheet_csv(params))
    return output


def write_first_print_gate5_consumable_puncture_worksheet(
    *,
    params: dict[str, Any],
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(first_print_gate5_consumable_puncture_worksheet_csv(params))
    return output


def write_first_print_gate6_sensor_thermal_worksheet(
    *,
    params: dict[str, Any],
    output_path: str | Path,
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(first_print_gate6_sensor_thermal_worksheet_csv(params))
    return output


def _set_empty_table_value(text: str, field: str, value: str) -> str:
    marker = f"| {field} |  |"
    replacement = f"| {field} | {value} |"
    if marker not in text:
        raise ValueError(f"template is missing an empty `{field}` table cell")
    return text.replace(marker, replacement, 1)


def scaffold_first_print_measurement_record(
    *,
    params: dict[str, Any],
    params_path: str | Path,
    out_dir: str | Path,
    template_path: str | Path,
    output_path: str | Path,
    date: str = "",
    cad_source_note: str = "unrecorded-local-worktree",
    overwrite: bool = False,
) -> Path:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(output)

    audit = audit_first_print_package(params, out_dir)
    template = Path(template_path).read_text()
    session_date = date or datetime.now().date().isoformat()
    generated_timestamp = latest_required_artifact_timestamp(audit)
    package_manifest_path = Path(out_dir) / f"{params['name']}_first_print_package_manifest.md"
    slicer_queue_path = Path(out_dir) / "first_print_slicer_queue"
    split_slicer_queue_path = Path(out_dir) / "first_print_y_split_slicer_queue"
    slicer_setup_path = output.with_name(f"{session_date}_one_row_coupon_slicer_setup.csv")
    bed_fit_split_plan_path = output.with_name(
        f"{session_date}_one_row_coupon_bed_fit_split_plan.csv"
    )
    sliced_outputs_path = output.with_name(
        f"{session_date}_one_row_coupon_sliced_outputs.csv"
    )
    split_sliced_outputs_path = output.with_name(
        f"{session_date}_one_row_coupon_y_split_sliced_outputs.csv"
    )
    split_print_batch_traveler_path = output.with_name(
        f"{session_date}_one_row_coupon_y_split_print_batch_traveler.csv"
    )
    split_gate1_qc_worksheet_path = output.with_name(
        f"{session_date}_one_row_coupon_y_split_gate1_qc.csv"
    )
    gate1_qc_worksheet_path = output.with_name(f"{session_date}_one_row_coupon_gate1_qc.csv")
    gate2_dry_assembly_worksheet_path = output.with_name(
        f"{session_date}_one_row_coupon_gate2_dry_assembly.csv"
    )
    gate3_placement_worksheet_path = output.with_name(
        f"{session_date}_one_row_coupon_gate3_placement.csv"
    )
    gate4_wet_dry_witness_worksheet_path = output.with_name(
        f"{session_date}_one_row_coupon_gate4_wet_dry_witness.csv"
    )
    gate5_consumable_puncture_worksheet_path = output.with_name(
        f"{session_date}_one_row_coupon_gate5_consumable_puncture.csv"
    )
    gate6_sensor_thermal_worksheet_path = output.with_name(
        f"{session_date}_one_row_coupon_gate6_sensor_thermal.csv"
    )
    install_inventory_path = output.with_name(
        f"{session_date}_one_row_coupon_install_inventory.csv"
    )
    service_state_review_path = output.with_name(
        f"{session_date}_one_row_coupon_service_state_review.csv"
    )

    record = template
    record = _set_empty_table_value(record, "Date", session_date)
    record = _replace_record_table_value(record, "Params file", f"`{Path(params_path)}`")
    record = _set_empty_table_value(record, "Params SHA256", file_sha256(params_path))
    record = _set_empty_table_value(
        record,
        "CAD source commit / worktree note",
        cad_source_note,
    )
    record = _set_empty_table_value(
        record,
        "Generated output timestamp",
        generated_timestamp or "missing-required-artifacts",
    )
    record = _set_empty_table_value(
        record,
        FIRST_PRINT_ACTIVE_QUEUE_MODE_FIELD,
        FIRST_PRINT_ACTIVE_QUEUE_MODE_MONOLITHIC,
    )
    record = _set_empty_table_value(
        record,
        "Print/procurement manifest",
        f"`{package_manifest_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Slicer queue",
        f"`{slicer_queue_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Split slicer queue",
        f"`{split_slicer_queue_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Slicer setup worksheet",
        f"`{slicer_setup_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Bed-fit split plan",
        f"`{bed_fit_split_plan_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Sliced output worksheet",
        f"`{sliced_outputs_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Split sliced output worksheet",
        f"`{split_sliced_outputs_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Split print batch traveler",
        f"`{split_print_batch_traveler_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Split Gate 1 QC worksheet",
        f"`{split_gate1_qc_worksheet_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Gate 1 QC worksheet",
        f"`{gate1_qc_worksheet_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Gate 2 dry assembly worksheet",
        f"`{gate2_dry_assembly_worksheet_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Gate 3 placement worksheet",
        f"`{gate3_placement_worksheet_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Gate 4 wet/dry witness worksheet",
        f"`{gate4_wet_dry_witness_worksheet_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Gate 5 consumable/puncture worksheet",
        f"`{gate5_consumable_puncture_worksheet_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Gate 6 sensor/thermal worksheet",
        f"`{gate6_sensor_thermal_worksheet_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Install inventory worksheet",
        f"`{install_inventory_path}`",
    )
    record = _set_empty_table_value(
        record,
        "Service state review worksheet",
        f"`{service_state_review_path}`",
    )

    snapshot = first_print_audit_snapshot_markdown(audit)
    record = record.replace(
        "## Gate 0 CAD Artifact Identity",
        f"{snapshot}\n\n## Gate 0 CAD Artifact Identity",
        1,
    )
    qc_targets = first_print_qc_target_bounds_markdown(params)
    record = record.replace(
        "## Gate 2 Dry Assembly Fit",
        f"{qc_targets}\n\n## Gate 2 Dry Assembly Fit",
        1,
    )
    dry_assembly_targets = first_print_dry_assembly_targets_markdown(params)
    record = record.replace(
        "## Gate 3 OT-2 Placement And No-Motion Clearance",
        (
            f"{dry_assembly_targets}\n\n"
            "## Gate 3 OT-2 Placement And No-Motion Clearance"
        ),
        1,
    )
    ot2_targets = first_print_ot2_placement_targets_markdown(params)
    record = record.replace(
        "## Gate 4 Passive Leak And Wet/Dry Witness",
        f"{ot2_targets}\n\n## Gate 4 Passive Leak And Wet/Dry Witness",
        1,
    )
    wet_dry_targets = first_print_wet_dry_witness_targets_markdown(params)
    record = record.replace(
        "## Gate 5 Consumable And Puncture Link",
        f"{wet_dry_targets}\n\n## Gate 5 Consumable And Puncture Link",
        1,
    )
    puncture_targets = first_print_consumable_puncture_targets_markdown(params)
    record = record.replace(
        "## Gate 6 Sensor And Thermal Link",
        f"{puncture_targets}\n\n## Gate 6 Sensor And Thermal Link",
        1,
    )
    sensor_targets = first_print_sensor_thermal_targets_markdown(params)
    record = record.replace(
        "## Decision",
        f"{sensor_targets}\n\n## Decision",
        1,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(record)
    return output
