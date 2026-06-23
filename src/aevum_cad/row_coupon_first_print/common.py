"""Cross-cutting first-print audit helpers (extracted, behavior-preserving)."""

from __future__ import annotations
from .models import FirstPrintArtifact

import csv
from hashlib import sha256
from io import StringIO
from pathlib import Path


def file_sha256(path: str | Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()

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

def _parse_bool_cell(value: str) -> bool | None:
    cleaned = value.strip()
    if cleaned == "yes":
        return True
    if cleaned == "no":
        return False
    return None

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

def _markdown_table_cells(line: str) -> tuple[str, ...]:
    if not line.startswith("|"):
        return ()
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))

def _path_from_csv_cell(value: str) -> Path:
    return Path(value.strip())

def _csv_rows_from_path(path: str | Path) -> tuple[dict[str, str], ...]:
    csv_path = Path(path)
    if not csv_path.exists():
        return ()
    return tuple(csv.DictReader(StringIO(csv_path.read_text())))

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

def _set_empty_table_value(text: str, field: str, value: str) -> str:
    marker = f"| {field} |  |"
    replacement = f"| {field} | {value} |"
    if marker not in text:
        raise ValueError(f"template is missing an empty `{field}` table cell")
    return text.replace(marker, replacement, 1)
