"""First-print slicer-profile discover/select/audit family, extracted behavior-preserving.

Shells out to the slicer binary (``subprocess``) and parses the Prusa config to discover candidate
setup rows, then selects + audits the operator's chosen row. ``_replace_record_table_value`` is the
only foundation helper it borrows (imported from ``common``). Extracted verbatim from the package
facade (SLICER_SETUP_* + DEFAULT_* consts + the 14 defs).
"""

from __future__ import annotations

import csv
import subprocess
from io import StringIO
from pathlib import Path
from typing import Any

from .common import _replace_record_table_value
from .models import (
    FirstPrintSlicerSetupRow,
    FirstPrintSlicerSetupIssue,
    FirstPrintSlicerSetupAudit,
    FirstPrintSlicerSetupSelection,
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
