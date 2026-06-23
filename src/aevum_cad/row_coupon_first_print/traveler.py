"""First-print print-batch traveler family, extracted behavior-preserving.

Includes the two helpers (``_first_print_print_batch_traveler_row_dict`` /
``first_print_print_batch_traveler_csv``) that were physically interleaved into the slicer block in
the monolith. Imports the gate1 + sliced-output y-split audits it chains from ``gates`` / ``slicer``
(one-directional traveler -> slicer/gates edge). Function bodies stay byte-identical.
"""

from __future__ import annotations
from collections import Counter

import csv
from io import StringIO
from pathlib import Path
from typing import Any

from .common import (
    _csv_rows_from_path,
    _worksheet_evidence_file_error,
)
from .gates import audit_first_print_y_split_gate1_qc_worksheet
from .slicer import audit_first_print_y_split_sliced_outputs
from .models import (
    FirstPrintPrintBatchTravelerRow,
    FirstPrintPrintBatchTravelerIssue,
    FirstPrintPrintBatchTravelerAudit,
)


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
