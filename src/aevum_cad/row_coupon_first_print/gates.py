"""First-print Gate 1-6 worksheet families (rows/csv/issue/audit), extracted behavior-preserving.

The per-gate FIELDNAMES/RESULT_VALUES tuples live here with their owning gate. The gate
``*_worksheet_rows`` functions derive their rows from ``cad_targets``/slicer-queue helpers that
still live on the package facade (``aevum_cad.row_coupon_first_print``). Importing those at module
top would form a partially-initialized-module cycle (the facade imports this module during its own
initialization, before those helpers are defined). They are therefore bound into this module's
globals by the facade at the end of its own load via ``_bind_facade_targets`` — see ``__init__.py``.
Until then the names below are ``None`` placeholders; they are populated before any gate row
function is callable through the package.
"""

from __future__ import annotations

import csv
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Any

from .common import (
    _worksheet_evidence_file_error,
)
from .constants import FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM
from .models import (
    FirstPrintGate1QCWorksheetAudit,
    FirstPrintGate1QCWorksheetIssue,
    FirstPrintGate1QCWorksheetRow,
    FirstPrintGate2DryAssemblyWorksheetAudit,
    FirstPrintGate2DryAssemblyWorksheetIssue,
    FirstPrintGate2DryAssemblyWorksheetRow,
    FirstPrintGate3PlacementWorksheetAudit,
    FirstPrintGate3PlacementWorksheetIssue,
    FirstPrintGate3PlacementWorksheetRow,
    FirstPrintGate4WetDryWitnessWorksheetAudit,
    FirstPrintGate4WetDryWitnessWorksheetIssue,
    FirstPrintGate4WetDryWitnessWorksheetRow,
    FirstPrintGate5ConsumablePunctureWorksheetAudit,
    FirstPrintGate5ConsumablePunctureWorksheetIssue,
    FirstPrintGate5ConsumablePunctureWorksheetRow,
    FirstPrintGate6SensorThermalWorksheetAudit,
    FirstPrintGate6SensorThermalWorksheetIssue,
    FirstPrintGate6SensorThermalWorksheetRow,
)

# Facade-owned helpers the gate ``*_worksheet_rows`` bodies reference as plain globals. They still
# live on the package facade (cad_targets + slicer-queue helpers, not extracted this cycle) and are
# late-bound into this namespace by ``_bind_facade_targets`` (called at the end of the facade
# ``__init__`` after those helpers are defined). Declared here as ``None`` placeholders so the
# function bodies stay byte-identical and ``LOAD_GLOBAL`` finds the name.
_FACADE_DEFERRED = (
    "first_print_qc_targets",
    "first_print_gate2_dry_assembly_targets",
    "first_print_gate3_placement_targets",
    "first_print_gate4_wet_dry_witness_targets",
    "first_print_gate5_consumable_puncture_targets",
    "first_print_gate6_sensor_thermal_targets",
    "first_print_gate1_qc_rows_from_slicer_queue_manifest",
    "first_print_final_piece_slicer_queue_items",
)

first_print_qc_targets = None  # bound by facade _bind_facade_targets
first_print_gate2_dry_assembly_targets = None  # bound by facade _bind_facade_targets
first_print_gate3_placement_targets = None  # bound by facade _bind_facade_targets
first_print_gate4_wet_dry_witness_targets = None  # bound by facade _bind_facade_targets
first_print_gate5_consumable_puncture_targets = None  # bound by facade _bind_facade_targets
first_print_gate6_sensor_thermal_targets = None  # bound by facade _bind_facade_targets
first_print_gate1_qc_rows_from_slicer_queue_manifest = None  # bound by facade _bind_facade_targets
first_print_final_piece_slicer_queue_items = None  # bound by facade _bind_facade_targets


def _bind_facade_targets(facade) -> None:
    """Late-bind facade-owned cad_targets/slicer helpers into this module's globals.

    Called once by the package facade at the end of its own load, after those helpers exist, to
    break the import cycle without touching the (byte-identical) gate function bodies.
    """
    module_globals = globals()
    for name in _FACADE_DEFERRED:
        module_globals[name] = getattr(facade, name)


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


def first_print_final_piece_gate1_qc_worksheet_rows(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    piece_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
) -> tuple[FirstPrintGate1QCWorksheetRow, ...]:
    manifest_rows = first_print_gate1_qc_rows_from_slicer_queue_manifest(queue_dir)
    if manifest_rows:
        return manifest_rows

    piece_path = Path(piece_dir)
    rows: list[FirstPrintGate1QCWorksheetRow] = []
    for item in first_print_final_piece_slicer_queue_items(
        params=params,
        out_dir=out_dir,
        piece_dir=piece_path,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
    ):
        # Must agree row-for-row with the manifest-derived branch above
        # (``first_print_gate1_qc_rows_from_slicer_queue_manifest``), because the
        # audit compares the operator's worksheet against whichever branch is
        # live: a worksheet written before the queue was prepared has to survive
        # the audit run after it.
        #
        # Under the y_split scheme the two branches agreed by accident -- only cut
        # segments lived in the split directory, so "does this STL come out of the
        # split dir" and "is this a cut piece" were the same question. Under the
        # final-piece scheme EVERY queued part is exported to ``piece_dir``,
        # including bodies that fit the bed whole, so the directory test labels
        # everything ``printed_final_piece`` while the manifest branch still
        # labels an unsplit body ``printed``. Ask the same question the manifest
        # branch asks -- the queue item's own role, which is the field that
        # round-trips through the manifest table.
        source = (
            "printed_final_piece" if "final print piece" in item.role else "printed"
        )
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


def first_print_final_piece_gate1_qc_worksheet_csv(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    piece_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
) -> str:
    return _first_print_gate1_qc_worksheet_csv_from_rows(
        first_print_final_piece_gate1_qc_worksheet_rows(
            params=params,
            out_dir=out_dir,
            piece_dir=piece_dir,
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


def audit_first_print_final_piece_gate1_qc_worksheet(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    piece_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    worksheet_path: str | Path,
    tolerance_mm: float = FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM,
) -> FirstPrintGate1QCWorksheetAudit:
    return _audit_first_print_gate1_qc_worksheet_from_expected_rows(
        worksheet_path=Path(worksheet_path),
        expected_rows=first_print_final_piece_gate1_qc_worksheet_rows(
            params=params,
            out_dir=out_dir,
            piece_dir=piece_dir,
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
