"""First-print bed-fit geometry, split-plan, and y-split-artifact audits, extracted verbatim.

This module owns the bed-fit geometry predicates (``_part_fits_rectangular_bed`` /
``_minimum_y_segments_for_bed``) and the bed-fit -> split-plan -> y-split-artifact audit chain.
The slicer-setup audits, ``_target_lookup`` and ``first_print_slicer_queue_artifacts`` it calls
still live on the package facade (extracted in later cycles); importing them at module top would
form a partially-initialized-module cycle (the facade imports this module during its own load,
before those names exist). They are therefore late-bound into this module's globals by the facade
at the end of its own load via ``_bind_facade_deferred`` -- see ``__init__.py``. The function
bodies below stay byte-identical.
"""

from __future__ import annotations

import configparser
import csv
import math
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Any

from aevum_cad.row_coupon import (
    build_row_coupon_production_y_split_parts,
    row_coupon_production_y_split_plan,
)

from .common import _parse_bool_cell
from .package import audit_first_print_package
from .models import (
    FirstPrintQCTarget,
    FirstPrintSlicerBedFitAudit,
    FirstPrintSlicerBedFitIssue,
    FirstPrintSlicerBedFitOversize,
    FirstPrintBedFitSplitPlanRow,
    FirstPrintBedFitSplitPlanIssue,
    FirstPrintBedFitSplitPlanAudit,
    FirstPrintYSplitArtifactRow,
    FirstPrintYSplitArtifactIssue,
    FirstPrintYSplitArtifactAudit,
)

# Facade-owned helpers the bodies below reference as plain globals (slicer-setup audits +
# _target_lookup + slicer-queue artifacts, not yet extracted this cycle). Late-bound by the facade
# via ``_bind_facade_deferred`` after they are defined. Declared ``None`` so LOAD_GLOBAL resolves.
_FACADE_DEFERRED = (
    "audit_first_print_slicer_setup",
    "_first_print_selected_slicer_setup_row",
    "_target_lookup",
    "first_print_slicer_queue_artifacts",
)

audit_first_print_slicer_setup = None  # bound by facade _bind_facade_deferred
_first_print_selected_slicer_setup_row = None  # bound by facade _bind_facade_deferred
_target_lookup = None  # bound by facade _bind_facade_deferred
first_print_slicer_queue_artifacts = None  # bound by facade _bind_facade_deferred


def _bind_facade_deferred(facade) -> None:
    """Late-bind facade-owned slicer-setup/queue helpers into this module's globals."""
    module_globals = globals()
    for name in _FACADE_DEFERRED:
        module_globals[name] = getattr(facade, name)


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
