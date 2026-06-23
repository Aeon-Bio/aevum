"""First-print dataclass models (extracted, behavior-preserving)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
    # --- D8 feature-aware seam fields (keyed_joints_enabled only) ---
    # All carry back-compat defaults so existing positional/keyword constructors
    # and the flag-OFF code path stay byte-identical (these stay at their defaults
    # when keyed_joints_enabled is false/absent).
    mating_feature_kind: str = ""
    interface_non_planar: bool = False
    y_fit_class_clearance_mm: float = 0.0
    anti_shear_key_present: bool = False
    witness_mark_present: bool = False
    requires_physical_evidence: bool = True


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
