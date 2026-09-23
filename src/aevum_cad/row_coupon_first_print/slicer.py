"""First-print sliced-output rows/csv + real gcode-export (subprocess) + sliced audits, extracted.

Two-range cut from the package facade that SKIPS the interleaved print-batch-traveler helpers (those
land in ``traveler.py``). ``_run_prusa_slicer_gcode_export`` shells out to the real slicer binary.
All upstream deps (slicer_setup / slicer_queue / package / common / models) are imported at module
top; function bodies stay byte-identical.
"""

from __future__ import annotations
from .slicer_queue import audit_first_print_slicer_queue, audit_first_print_slicer_queue_manifest
from .slicer_setup import _slicer_setup_row_summary, _validate_selectable_slicer_setup_row

import csv
import subprocess
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Any

from .common import (
    file_sha256,
    _path_from_csv_cell,
)
from .package import audit_first_print_package
from .slicer_setup import (
    _first_print_selected_slicer_setup_row,
    audit_first_print_slicer_setup,
)
from .slicer_queue import (
    first_print_slicer_queue_artifacts,
    first_print_slicer_queue_manifest_items,
    first_print_sliced_output_rows_from_slicer_queue_manifest,
    first_print_final_piece_slicer_queue_items,
)
from .models import (
    FirstPrintSlicedOutputRow,
    FirstPrintSlicedOutputIssue,
    FirstPrintSlicedOutputAudit,
)


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


def first_print_final_piece_sliced_output_rows(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    piece_dir: str | Path,
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
    for item in first_print_final_piece_slicer_queue_items(
        params=params,
        out_dir=out_dir,
        piece_dir=piece_dir,
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


def write_first_print_final_piece_sliced_outputs(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    piece_dir: str | Path,
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
    rows = first_print_final_piece_sliced_output_rows(
        params=params,
        out_dir=out_dir,
        piece_dir=piece_dir,
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


def slice_first_print_final_piece_slicer_queue(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    piece_dir: str | Path,
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
        raise ValueError("final-piece slicer queue is not ready")

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


def audit_first_print_final_piece_sliced_outputs(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    piece_dir: str | Path,
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
