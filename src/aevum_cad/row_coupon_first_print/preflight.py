"""First-print preflight mega-orchestrator + worksheet writers + measurement-record scaffolder.

``audit_first_print_preflight`` is the fan-in apex (~25 audit calls). It imports those audits + gate
csv builders + manifest/snapshot/target markdown from the foundation/leaf/mid submodules directly
(NOT from the package facade, which would recurse at module load). It imports ZERO readiness symbols
-- the readiness -> preflight edge is one-directional. The record-table helpers it mutates live in
``common``. Function bodies stay byte-identical.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from .common import (
    file_sha256,
    _record_table_value,
    first_print_record_table_value,
    _record_gate_result,
    _markdown_path_value,
    _replace_record_table_value,
    _set_empty_table_value,
)
from .constants import (
    FIRST_PRINT_PHYSICAL_GATES,
    FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM,
    FIRST_PRINT_ACTIVE_QUEUE_MODE_FIELD,
    FIRST_PRINT_ACTIVE_QUEUE_MODE_MONOLITHIC,
    FIRST_PRINT_ACTIVE_QUEUE_MODE_SPLIT_Y,
    FIRST_PRINT_ACTIVE_QUEUE_MODE_VALUES,
    FIRST_PRINT_PREFLIGHT_LINK_FIELDS,
    FIRST_PRINT_SPLIT_PREFLIGHT_LINK_FIELDS,
    FIRST_PRINT_PREFLIGHT_REQUIRED_SESSION_FIELDS,
)
from .models import (
    FirstPrintPreflightIssue,
    FirstPrintPreflightAudit,
)
from .package import (
    audit_first_print_package,
    first_print_audit_snapshot_markdown,
    latest_required_artifact_timestamp,
)
from .cad_targets import (
    first_print_cad_target_sections_markdown,
    first_print_qc_target_bounds_markdown,
    first_print_dry_assembly_targets_markdown,
    first_print_ot2_placement_targets_markdown,
    first_print_wet_dry_witness_targets_markdown,
    first_print_consumable_puncture_targets_markdown,
    first_print_sensor_thermal_targets_markdown,
)
from .gates import (
    _audit_first_print_gate1_qc_worksheet_from_expected_rows,
    audit_first_print_gate1_qc_worksheet,
    audit_first_print_gate2_dry_assembly_worksheet,
    audit_first_print_gate3_placement_worksheet,
    audit_first_print_gate4_wet_dry_witness_worksheet,
    audit_first_print_gate5_consumable_puncture_worksheet,
    audit_first_print_gate6_sensor_thermal_worksheet,
    first_print_gate1_qc_worksheet_csv,
    first_print_y_split_gate1_qc_worksheet_csv,
    first_print_gate2_dry_assembly_worksheet_csv,
    first_print_gate3_placement_worksheet_csv,
    first_print_gate4_wet_dry_witness_worksheet_csv,
    first_print_gate5_consumable_puncture_worksheet_csv,
    first_print_gate6_sensor_thermal_worksheet_csv,
)
from .install_service import (
    audit_first_print_install_inventory,
    audit_first_print_service_state_review,
)
from .slicer_setup import audit_first_print_slicer_setup
from .bed_fit import (
    audit_first_print_slicer_bed_fit,
    audit_first_print_y_split_artifacts,
)
from .slicer_queue import (
    audit_first_print_slicer_queue,
    audit_first_print_slicer_queue_manifest,
    first_print_gate1_qc_rows_from_slicer_queue_manifest,
    first_print_package_manifest_markdown,
)
from .slicer import (
    audit_first_print_sliced_outputs,
    audit_first_print_y_split_sliced_outputs,
)


def _preflight_issue(
    issues: list[FirstPrintPreflightIssue],
    *,
    field: str,
    message: str,
) -> None:
    issues.append(FirstPrintPreflightIssue(field=field, message=message))










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
