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

from .constants import (  # noqa: F401
    FIRST_PRINT_REQUIRED_VALIDATION_CHECKS,
    FIRST_PRINT_OPTIONAL_VALIDATION_TOOLS,
    FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM,
    FIRST_PRINT_PHYSICAL_GATES,
    FIRST_PRINT_ACTIVE_QUEUE_MODE_FIELD,
    FIRST_PRINT_ACTIVE_QUEUE_MODE_MONOLITHIC,
    FIRST_PRINT_ACTIVE_QUEUE_MODE_SPLIT_Y,
    FIRST_PRINT_ACTIVE_QUEUE_MODE_VALUES,
    FIRST_PRINT_PREFLIGHT_LINK_FIELDS,
    FIRST_PRINT_SPLIT_PREFLIGHT_LINK_FIELDS,
    FIRST_PRINT_PREFLIGHT_REQUIRED_SESSION_FIELDS,
)
from .models import (  # noqa: F401
    FirstPrintArtifact,
    FirstPrintPackageAudit,
    FirstPrintQCTarget,
    FirstPrintGate1QCWorksheetRow,
    FirstPrintGate1QCWorksheetIssue,
    FirstPrintGate1QCWorksheetAudit,
    FirstPrintGate2DryAssemblyTarget,
    FirstPrintGate2DryAssemblyWorksheetRow,
    FirstPrintGate2DryAssemblyWorksheetIssue,
    FirstPrintGate2DryAssemblyWorksheetAudit,
    FirstPrintGate3PlacementTarget,
    FirstPrintGate3PlacementWorksheetRow,
    FirstPrintGate3PlacementWorksheetIssue,
    FirstPrintGate3PlacementWorksheetAudit,
    FirstPrintGate4WetDryWitnessTarget,
    FirstPrintGate4WetDryWitnessWorksheetRow,
    FirstPrintGate4WetDryWitnessWorksheetIssue,
    FirstPrintGate4WetDryWitnessWorksheetAudit,
    FirstPrintGate5ConsumablePunctureTarget,
    FirstPrintGate5ConsumablePunctureWorksheetRow,
    FirstPrintGate5ConsumablePunctureWorksheetIssue,
    FirstPrintGate5ConsumablePunctureWorksheetAudit,
    FirstPrintGate6SensorThermalTarget,
    FirstPrintGate6SensorThermalWorksheetRow,
    FirstPrintGate6SensorThermalWorksheetIssue,
    FirstPrintGate6SensorThermalWorksheetAudit,
    FirstPrintInstallInventoryRow,
    FirstPrintInstallInventoryIssue,
    FirstPrintInstallInventoryAudit,
    FirstPrintServiceStateReviewRow,
    FirstPrintServiceStateBoundsEvidenceRow,
    FirstPrintServiceStateReviewIssue,
    FirstPrintServiceStateReviewAudit,
    FirstPrintSlicerSetupRow,
    FirstPrintSlicerSetupIssue,
    FirstPrintSlicerSetupAudit,
    FirstPrintSlicerBedFitIssue,
    FirstPrintSlicerBedFitOversize,
    FirstPrintSlicerBedFitAudit,
    FirstPrintSlicerSetupSelection,
    FirstPrintSlicerQueueItem,
    FirstPrintSlicerQueueHashMismatch,
    FirstPrintSlicerQueueAudit,
    FirstPrintSlicedOutputRow,
    FirstPrintSlicedOutputIssue,
    FirstPrintSlicedOutputAudit,
    FirstPrintPrintBatchTravelerRow,
    FirstPrintPrintBatchTravelerIssue,
    FirstPrintPrintBatchTravelerAudit,
    FirstPrintGate1PrintQCIssue,
    FirstPrintGate1PrintQCAudit,
    FirstPrintGate2DryAssemblyReadinessIssue,
    FirstPrintGate2DryAssemblyReadinessAudit,
    FirstPrintGate3PlacementReadinessIssue,
    FirstPrintGate3PlacementReadinessAudit,
    FirstPrintGate4WetDryWitnessReadinessIssue,
    FirstPrintGate4WetDryWitnessReadinessAudit,
    FirstPrintGate5ConsumablePunctureReadinessIssue,
    FirstPrintGate5ConsumablePunctureReadinessAudit,
    FirstPrintGate6SensorThermalReadinessIssue,
    FirstPrintGate6SensorThermalReadinessAudit,
    FirstPrintOperatingPrototypeAcceptanceIssue,
    FirstPrintOperatingPrototypeAcceptanceAudit,
    FirstPrintBedFitSplitPlanRow,
    FirstPrintBedFitSplitPlanIssue,
    FirstPrintBedFitSplitPlanAudit,
    FirstPrintYSplitArtifactRow,
    FirstPrintYSplitArtifactIssue,
    FirstPrintYSplitArtifactAudit,
    FirstPrintPreflightIssue,
    FirstPrintPreflightAudit,
)
from .common import (  # noqa: F401
    file_sha256,
    _resolve_worksheet_evidence_path,
    _worksheet_evidence_file_error,
    _parse_bool_cell,
    _artifact_presence,
    _artifact_path,
    _bool_text,
    _markdown_table_cells,
    _path_from_csv_cell,
    _csv_rows_from_path,
    _replace_record_table_value,
    _record_table_value,
    first_print_record_table_value,
    _record_gate_result,
    _markdown_path_value,
    _set_empty_table_value,
)


from .package import (  # noqa: F401  (facade re-export of extracted package catalog/audit)
    artifact_category,
    expected_production_artifacts,
    _validation_artifact,
    expected_validation_artifacts,
    expected_optional_validation_artifacts,
    audit_first_print_package,
    first_print_artifact_category_counts,
    _required_artifact_paths,
    latest_required_artifact_timestamp,
    first_print_audit_snapshot_markdown,
)


from .cad_targets import (  # noqa: F401  (facade re-export of extracted CAD/QC target tables)
    FIRST_PRINT_PUNCTURE_PLATE_SHIFT_LIMIT_MM,
    FIRST_PRINT_DRY_ASSEMBLY_SERVICE_CYCLES,
    first_print_qc_targets,
    first_print_qc_target_bounds_markdown,
    first_print_gate3_placement_targets,
    first_print_ot2_placement_targets_markdown,
    first_print_gate2_dry_assembly_targets,
    first_print_dry_assembly_targets_markdown,
    first_print_gate4_wet_dry_witness_targets,
    first_print_wet_dry_witness_targets_markdown,
    first_print_gate5_consumable_puncture_targets,
    first_print_consumable_puncture_targets_markdown,
    first_print_gate6_sensor_thermal_targets,
    first_print_sensor_thermal_targets_markdown,
    first_print_cad_target_sections_markdown,
)


from .gates import (  # noqa: F401  (facade re-export of extracted gate1-6 worksheet families)
    FIRST_PRINT_GATE1_QC_FIELDNAMES,
    FIRST_PRINT_GATE1_QC_RESULT_VALUES,
    FIRST_PRINT_GATE2_DRY_ASSEMBLY_FIELDNAMES,
    FIRST_PRINT_GATE2_DRY_ASSEMBLY_RESULT_VALUES,
    FIRST_PRINT_GATE3_PLACEMENT_FIELDNAMES,
    FIRST_PRINT_GATE3_PLACEMENT_RESULT_VALUES,
    FIRST_PRINT_GATE4_WET_DRY_WITNESS_FIELDNAMES,
    FIRST_PRINT_GATE4_WET_DRY_WITNESS_RESULT_VALUES,
    FIRST_PRINT_GATE5_CONSUMABLE_PUNCTURE_FIELDNAMES,
    FIRST_PRINT_GATE5_CONSUMABLE_PUNCTURE_RESULT_VALUES,
    FIRST_PRINT_GATE6_SENSOR_THERMAL_FIELDNAMES,
    FIRST_PRINT_GATE6_SENSOR_THERMAL_RESULT_VALUES,
    first_print_gate1_qc_worksheet_rows,
    _first_print_gate1_qc_worksheet_csv_from_rows,
    first_print_gate1_qc_worksheet_csv,
    first_print_y_split_gate1_qc_worksheet_rows,
    first_print_y_split_gate1_qc_worksheet_csv,
    _parse_gate1_float,
    _gate1_issue,
    _gate1_measurement_fields_filled,
    audit_first_print_gate1_qc_worksheet,
    audit_first_print_y_split_gate1_qc_worksheet,
    _audit_first_print_gate1_qc_worksheet_from_expected_rows,
    first_print_gate2_dry_assembly_worksheet_rows,
    first_print_gate2_dry_assembly_worksheet_csv,
    _gate2_dry_assembly_issue,
    audit_first_print_gate2_dry_assembly_worksheet,
    first_print_gate3_placement_worksheet_rows,
    first_print_gate3_placement_worksheet_csv,
    _gate3_placement_issue,
    audit_first_print_gate3_placement_worksheet,
    first_print_gate4_wet_dry_witness_worksheet_rows,
    first_print_gate4_wet_dry_witness_worksheet_csv,
    _gate4_wet_dry_witness_issue,
    audit_first_print_gate4_wet_dry_witness_worksheet,
    first_print_gate5_consumable_puncture_worksheet_rows,
    first_print_gate5_consumable_puncture_worksheet_csv,
    _gate5_consumable_puncture_issue,
    audit_first_print_gate5_consumable_puncture_worksheet,
    first_print_gate6_sensor_thermal_worksheet_rows,
    first_print_gate6_sensor_thermal_worksheet_csv,
    _gate6_sensor_thermal_issue,
    audit_first_print_gate6_sensor_thermal_worksheet,
)


from .install_service import (  # noqa: F401  (facade re-export of extracted install/service families)
    FIRST_PRINT_INSTALL_INVENTORY_FIELDNAMES,
    FIRST_PRINT_INSTALL_INVENTORY_RESULT_VALUES,
    FIRST_PRINT_INSTALL_INVENTORY_INSTALLED_AS_VALUES,
    FIRST_PRINT_INSTALL_INVENTORY_CATEGORIES,
    FIRST_PRINT_INSTALL_INVENTORY_ACCEPTABLE_ITEMS,
    FIRST_PRINT_SERVICE_STATE_REVIEW_FIELDNAMES,
    FIRST_PRINT_SERVICE_STATE_REVIEW_RESULT_VALUES,
    FIRST_PRINT_SERVICE_STATE_ACCEPTANCE_GATES,
    FIRST_PRINT_SERVICE_STATE_SERVICE_PART_EXPECTATIONS,
    FIRST_PRINT_SERVICE_STATE_BOUNDS_EVIDENCE_FIELDNAMES,
    first_print_install_inventory_rows,
    first_print_install_inventory_csv,
    write_first_print_install_inventory,
    _install_inventory_issue,
    _allowed_installed_as_for_source,
    _install_inventory_operating_requirement_for_source,
    audit_first_print_install_inventory,
    first_print_service_state_review_rows,
    _service_state_parts_from_csv,
    _service_state_bounds_evidence_path,
    first_print_service_state_bounds_evidence_rows,
    first_print_service_state_bounds_evidence_csv,
    write_first_print_service_state_bounds_evidence,
    first_print_service_state_review_csv,
    write_first_print_service_state_review,
    _service_state_review_issue,
    _resolve_service_state_evidence_path,
    _audit_service_state_bounds_evidence,
    audit_first_print_service_state_review,
)


from .slicer_setup import (  # noqa: F401  (facade re-export of extracted slicer-setup family)
    FIRST_PRINT_SLICER_SETUP_FIELDNAMES,
    FIRST_PRINT_SLICER_SETUP_RESULT_VALUES,
    FIRST_PRINT_SLICER_SETUP_SELECTED_VALUES,
    DEFAULT_PRUSA_SLICER_PATH,
    DEFAULT_BAMBU_STUDIO_PATH,
    DEFAULT_PRUSA_CONFIG_PATH,
    DEFAULT_BAMBU_CONFIG_PATH,
    _slicer_version,
    _prusa_active_presets,
    discover_first_print_slicer_setup_rows,
    first_print_slicer_setup_csv,
    write_first_print_slicer_setup,
    _slicer_setup_rows_from_csv,
    _slicer_setup_csv_from_dict_rows,
    _slicer_setup_issue,
    _slicer_setup_row_summary,
    _slicer_setup_row_matches,
    _validate_selectable_slicer_setup_row,
    select_first_print_slicer_setup,
    audit_first_print_slicer_setup,
    _first_print_selected_slicer_setup_row,
)


from .bed_fit import (  # noqa: F401  (facade re-export of extracted bed-fit/split-plan/y-split audits)
    FIRST_PRINT_BED_FIT_SPLIT_PLAN_FIELDNAMES,
    FIRST_PRINT_BED_FIT_SPLIT_PLAN_RESULT_VALUES,
    _slicer_profile_source_candidates,
    _printer_profile_bed_shape,
    _bed_shape_xy_mm,
    _part_fits_rectangular_bed,
    _minimum_y_segments_for_bed,
    audit_first_print_slicer_bed_fit,
    first_print_bed_fit_split_plan_rows,
    first_print_bed_fit_split_plan_csv,
    write_first_print_bed_fit_split_plan,
    _split_plan_issue,
    audit_first_print_bed_fit_split_plan,
    first_print_y_split_artifact_rows,
    _y_split_artifact_issue,
    audit_first_print_y_split_artifacts,
)


from .slicer_queue import (  # noqa: F401  (facade re-export of extracted slicer-queue + manifest family)
    _target_lookup,
    _nonprinted_model_use_and_install_requirement,
    first_print_package_manifest_markdown,
    first_print_slicer_queue_artifacts,
    first_print_slicer_queue_manifest_markdown,
    first_print_slicer_queue_manifest_items,
    audit_first_print_slicer_queue_manifest,
    first_print_sliced_output_rows_from_slicer_queue_manifest,
    first_print_gate1_qc_rows_from_slicer_queue_manifest,
    prepare_first_print_slicer_queue,
    first_print_y_split_slicer_queue_items,
    prepare_first_print_y_split_slicer_queue,
    audit_first_print_slicer_queue,
    audit_first_print_y_split_slicer_queue,
)


from .slicer import (  # noqa: F401  (facade re-export of extracted sliced-output + gcode-export family)
    FIRST_PRINT_SLICED_OUTPUT_FIELDNAMES,
    FIRST_PRINT_SLICED_OUTPUT_RESULT_VALUES,
    FIRST_PRINT_SLICED_OUTPUT_SUFFIXES,
    first_print_sliced_output_rows,
    first_print_y_split_sliced_output_rows,
    first_print_sliced_output_csv,
    write_first_print_sliced_outputs,
    write_first_print_y_split_sliced_outputs,
    _selected_first_print_slicer_setup_or_raise,
    _prusa_slicer_datadir,
    _run_prusa_slicer_gcode_export,
    slice_first_print_y_split_slicer_queue,
    _sliced_output_issue,
    audit_first_print_sliced_outputs,
    audit_first_print_y_split_sliced_outputs,
    _audit_first_print_sliced_outputs_from_expected_rows,
)


from .traveler import (  # noqa: F401  (facade re-export of extracted print-batch-traveler family)
    FIRST_PRINT_PRINT_BATCH_TRAVELER_FIELDNAMES,
    FIRST_PRINT_PRINT_BATCH_TRAVELER_PRINT_RESULT_VALUES,
    _first_print_print_batch_traveler_row_dict,
    first_print_print_batch_traveler_csv,
    first_print_print_batch_traveler_rows,
    write_first_print_y_split_print_batch_traveler,
    _print_batch_traveler_issue,
    audit_first_print_y_split_print_batch_traveler,
)


from .readiness import (  # noqa: F401  (facade re-export of extracted Gate 1-6 readiness chain)
    _gate1_print_qc_issue,
    audit_first_print_y_split_gate1_print_qc,
    _gate2_dry_assembly_readiness_issue,
    audit_first_print_y_split_gate2_dry_assembly_readiness,
    _gate3_placement_readiness_issue,
    audit_first_print_y_split_gate3_placement_readiness,
    _gate4_wet_dry_witness_readiness_issue,
    audit_first_print_y_split_gate4_wet_dry_witness_readiness,
    _gate5_consumable_puncture_readiness_issue,
    audit_first_print_y_split_gate5_consumable_puncture_readiness,
    _gate6_sensor_thermal_readiness_issue,
    audit_first_print_y_split_gate6_sensor_thermal_readiness,
    _operating_prototype_acceptance_issue,
    audit_first_print_y_split_operating_prototype_acceptance,
)


from .preflight import (  # noqa: F401  (facade re-export of extracted preflight + writers + scaffold)
    _preflight_issue,
    audit_first_print_preflight,
    write_first_print_package_manifest,
    write_first_print_gate1_qc_worksheet,
    write_first_print_y_split_gate1_qc_worksheet,
    write_first_print_gate2_dry_assembly_worksheet,
    write_first_print_gate3_placement_worksheet,
    write_first_print_gate4_wet_dry_witness_worksheet,
    write_first_print_gate5_consumable_puncture_worksheet,
    write_first_print_gate6_sensor_thermal_worksheet,
    scaffold_first_print_measurement_record,
)


# Late-bind facade-owned cad_targets / slicer-queue helpers into the extracted ``gates`` module.
# The gate ``*_worksheet_rows`` bodies reference these as plain globals; they cannot be imported at
# ``gates`` module-top without forming a partially-initialized-module cycle (this facade imports
# ``gates`` before these helpers are defined). Bind them here, after their definitions exist.
import sys as _sys  # noqa: E402

from . import gates as _gates  # noqa: E402

_gates._bind_facade_targets(_sys.modules[__name__])
del _gates

# Late-bind facade-owned slicer-setup / queue helpers into the extracted ``bed_fit`` module
# (same partially-initialized-module-cycle reason as ``gates`` above).
from . import bed_fit as _bed_fit  # noqa: E402

_bed_fit._bind_facade_deferred(_sys.modules[__name__])
del _bed_fit

# Late-bind facade-owned install/service row helpers into the extracted ``slicer_queue`` module
# (same partially-initialized-module-cycle reason as ``gates`` above).
from . import slicer_queue as _slicer_queue  # noqa: E402

_slicer_queue._bind_facade_deferred(_sys.modules[__name__])
del _slicer_queue

# Late-bind facade-owned ``audit_first_print_preflight`` into the extracted ``readiness`` module
# (same partially-initialized-module-cycle reason as ``gates`` above; readiness -> preflight edge).
from . import readiness as _readiness  # noqa: E402

_readiness._bind_facade_deferred(_sys.modules[__name__])
del _readiness, _sys
