"""First-print install-inventory + service-state review worksheet families, extracted verbatim.

Crosses the package boundary into row_coupon service-parts geometry
(``build_row_coupon_service_parts_from_installed`` / ``ROW_COUPON_SERVICE_MODES`` /
``row_coupon_part_manifest``) via the ``aevum_cad.row_coupon`` facade. Borrows the worksheet
evidence-path helpers from ``common`` and ``artifact_category`` from ``package``. Function bodies +
the install/service constants stay byte-identical.
"""

from __future__ import annotations
from collections.abc import Mapping

import csv
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Any

from aevum_cad.row_coupon import (
    ROW_COUPON_SERVICE_MODES,
    build_row_coupon_installed_parts,
    build_row_coupon_service_parts_from_installed,
    row_coupon_part_manifest,
)

from .common import (
    _resolve_worksheet_evidence_path,
    _worksheet_evidence_file_error,
)
from .package import artifact_category
from .models import (
    FirstPrintInstallInventoryRow,
    FirstPrintInstallInventoryIssue,
    FirstPrintInstallInventoryAudit,
    FirstPrintServiceStateReviewRow,
    FirstPrintServiceStateReviewIssue,
    FirstPrintServiceStateReviewAudit,
    FirstPrintServiceStateBoundsEvidenceRow,
)


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
