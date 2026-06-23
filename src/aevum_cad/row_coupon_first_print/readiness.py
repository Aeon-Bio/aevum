"""First-print cumulative Gate 1-6 readiness chain + operating-prototype acceptance, extracted.

A strict inductive chain: each readiness step pulls its gate WORKSHEET audit (gates) + install /
service (install_service) + traveler (traveler) audits and the previous readiness step (same
module). ``audit_first_print_y_split_operating_prototype_acceptance`` additionally calls
``audit_first_print_preflight``; preflight is its sibling apex (extracted alongside this module) and
importing it at module top would form a partially-initialized-module cycle, so it is late-bound by
the facade via ``_bind_facade_deferred``. Function bodies stay byte-identical.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import _csv_rows_from_path
from .constants import FIRST_PRINT_PHYSICAL_GATES
from .gates import (
    audit_first_print_y_split_gate1_qc_worksheet,
    audit_first_print_gate2_dry_assembly_worksheet,
    audit_first_print_gate3_placement_worksheet,
    audit_first_print_gate4_wet_dry_witness_worksheet,
    audit_first_print_gate5_consumable_puncture_worksheet,
    audit_first_print_gate6_sensor_thermal_worksheet,
)
from .install_service import (
    audit_first_print_install_inventory,
    audit_first_print_service_state_review,
)
from .traveler import audit_first_print_y_split_print_batch_traveler
from .models import (
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
)

# ``audit_first_print_preflight`` (sibling preflight.py apex) is late-bound by the facade via
# ``_bind_facade_deferred`` to keep the readiness <-> preflight edge one-directional and acyclic.
_FACADE_DEFERRED = ("audit_first_print_preflight",)

audit_first_print_preflight = None  # bound by facade _bind_facade_deferred


def _bind_facade_deferred(facade) -> None:
    """Late-bind ``audit_first_print_preflight`` into this module's globals."""
    module_globals = globals()
    for name in _FACADE_DEFERRED:
        module_globals[name] = getattr(facade, name)


def _gate1_print_qc_issue(
    issues: list[FirstPrintGate1PrintQCIssue],
    *,
    part: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate1PrintQCIssue(
            part=part,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate1_print_qc(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate1PrintQCAudit:
    gate1_audit = audit_first_print_y_split_gate1_qc_worksheet(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        worksheet_path=gate1_qc_path,
    )
    traveler_audit = audit_first_print_y_split_print_batch_traveler(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        sliced_output_path=sliced_output_path,
        gate1_qc_path=gate1_qc_path,
        worksheet_path=print_batch_traveler_path,
        expected_setup_summary=expected_setup_summary,
    )
    traveler_rows = _csv_rows_from_path(print_batch_traveler_path)
    gate1_rows = _csv_rows_from_path(gate1_qc_path)
    traveler_by_part = {
        row.get("part", "").strip(): row for row in traveler_rows if row.get("part", "").strip()
    }
    expected_parts = tuple(row.get("part", "").strip() for row in gate1_rows)
    unprinted_parts = tuple(
        part
        for part in expected_parts
        if traveler_by_part.get(part, {}).get("print_result", "").strip() != "printed"
    )
    printed_row_count = sum(
        1
        for part in expected_parts
        if traveler_by_part.get(part, {}).get("print_result", "").strip() == "printed"
    )
    issues: list[FirstPrintGate1PrintQCIssue] = []
    for row in gate1_rows:
        part = row.get("part", "").strip()
        if row.get("result", "").strip() != "pass":
            continue
        traveler_result = traveler_by_part.get(part, {}).get("print_result", "").strip()
        if traveler_result != "printed":
            _gate1_print_qc_issue(
                issues,
                part=part,
                field="print_result",
                message=(
                    "Gate 1 pass row requires matching print batch traveler "
                    f"result printed, found {traveler_result or 'missing'}"
                ),
            )
            continue
        if not traveler_by_part.get(part, {}).get("print_evidence_path", "").strip():
            _gate1_print_qc_issue(
                issues,
                part=part,
                field="print_evidence_path",
                message="Gate 1 pass row requires print batch traveler evidence",
            )

    return FirstPrintGate1PrintQCAudit(
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        expected_row_count=gate1_audit.expected_row_count,
        printed_row_count=printed_row_count,
        unprinted_parts=unprinted_parts,
        gate1_qc_worksheet_valid=gate1_audit.worksheet_valid,
        gate1_pass_ready=gate1_audit.gate1_pass_ready,
        print_batch_handoff_ready=traveler_audit.handoff_ready,
        issues=tuple(issues),
    )


def _gate2_dry_assembly_readiness_issue(
    issues: list[FirstPrintGate2DryAssemblyReadinessIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate2DryAssemblyReadinessIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate2_dry_assembly_readiness(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate2DryAssemblyReadinessAudit:
    gate2_audit = audit_first_print_gate2_dry_assembly_worksheet(
        params=params,
        worksheet_path=gate2_dry_assembly_path,
    )
    gate1_print_qc_audit = audit_first_print_y_split_gate1_print_qc(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        expected_setup_summary=expected_setup_summary,
    )
    install_inventory_audit = audit_first_print_install_inventory(
        worksheet_path=install_inventory_path,
    )
    service_state_review_audit = audit_first_print_service_state_review(
        worksheet_path=service_state_review_path,
    )
    gate2_pass_targets = tuple(
        row.get("target", "").strip()
        for row in _csv_rows_from_path(gate2_dry_assembly_path)
        if row.get("target", "").strip()
        and row.get("result", "").strip() == "pass"
    )
    issues: list[FirstPrintGate2DryAssemblyReadinessIssue] = []
    if gate2_pass_targets and not gate1_print_qc_audit.print_qc_ready:
        _gate2_dry_assembly_readiness_issue(
            issues,
            target="Gate 2 dry assembly",
            field="Gate 1 print QC",
            message=(
                f"{len(gate2_pass_targets)} Gate 2 pass rows require "
                "split Gate 1 print-QC readiness"
            ),
        )
    if gate2_pass_targets and not install_inventory_audit.install_inventory_ready:
        _gate2_dry_assembly_readiness_issue(
            issues,
            target="Gate 2 dry assembly",
            field="Install inventory",
            message=(
                f"{len(gate2_pass_targets)} Gate 2 pass rows require "
                "ready installed-item inventory"
            ),
        )
    if gate2_pass_targets and not service_state_review_audit.service_state_review_ready:
        _gate2_dry_assembly_readiness_issue(
            issues,
            target="Gate 2 dry assembly",
            field="Service state review",
            message=(
                f"{len(gate2_pass_targets)} Gate 2 pass rows require "
                "ready installed/service/negative-review mode evidence"
            ),
        )

    return FirstPrintGate2DryAssemblyReadinessAudit(
        gate2_dry_assembly_worksheet_path=Path(gate2_dry_assembly_path),
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        install_inventory_path=Path(install_inventory_path),
        service_state_review_path=Path(service_state_review_path),
        gate2_dry_assembly_worksheet_valid=gate2_audit.worksheet_valid,
        gate2_dry_assembly_pass_ready=gate2_audit.gate2_pass_ready,
        gate2_pass_row_count=len(gate2_pass_targets),
        gate1_print_qc_ready=gate1_print_qc_audit.print_qc_ready,
        install_inventory_valid=install_inventory_audit.worksheet_valid,
        install_inventory_ready=install_inventory_audit.install_inventory_ready,
        service_state_review_valid=service_state_review_audit.worksheet_valid,
        service_state_review_ready=(
            service_state_review_audit.service_state_review_ready
        ),
        issues=tuple(issues),
    )


def _gate3_placement_readiness_issue(
    issues: list[FirstPrintGate3PlacementReadinessIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate3PlacementReadinessIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate3_placement_readiness(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    gate3_placement_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate3PlacementReadinessAudit:
    gate3_audit = audit_first_print_gate3_placement_worksheet(
        params=params,
        worksheet_path=gate3_placement_path,
    )
    gate2_readiness_audit = audit_first_print_y_split_gate2_dry_assembly_readiness(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        gate2_dry_assembly_path=gate2_dry_assembly_path,
        install_inventory_path=install_inventory_path,
        service_state_review_path=service_state_review_path,
        expected_setup_summary=expected_setup_summary,
    )
    gate3_pass_targets = tuple(
        row.get("target", "").strip()
        for row in _csv_rows_from_path(gate3_placement_path)
        if row.get("target", "").strip()
        and row.get("result", "").strip() == "pass"
    )
    issues: list[FirstPrintGate3PlacementReadinessIssue] = []
    if gate3_pass_targets and not gate2_readiness_audit.dry_assembly_ready:
        _gate3_placement_readiness_issue(
            issues,
            target="Gate 3 OT-2 placement",
            field="Gate 2 dry assembly",
            message=(
                f"{len(gate3_pass_targets)} Gate 3 pass rows require "
                "Gate 2 dry-assembly readiness"
            ),
        )

    return FirstPrintGate3PlacementReadinessAudit(
        gate3_placement_worksheet_path=Path(gate3_placement_path),
        gate2_dry_assembly_worksheet_path=Path(gate2_dry_assembly_path),
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        install_inventory_path=Path(install_inventory_path),
        gate3_placement_worksheet_valid=gate3_audit.worksheet_valid,
        gate3_placement_pass_ready=gate3_audit.gate3_pass_ready,
        gate3_pass_row_count=len(gate3_pass_targets),
        gate2_dry_assembly_ready=gate2_readiness_audit.dry_assembly_ready,
        gate2_dry_assembly_worksheet_valid=(
            gate2_readiness_audit.gate2_dry_assembly_worksheet_valid
        ),
        gate2_dry_assembly_pass_ready=(
            gate2_readiness_audit.gate2_dry_assembly_pass_ready
        ),
        gate2_pass_row_count=gate2_readiness_audit.gate2_pass_row_count,
        gate1_print_qc_ready=gate2_readiness_audit.gate1_print_qc_ready,
        install_inventory_ready=gate2_readiness_audit.install_inventory_ready,
        service_state_review_ready=gate2_readiness_audit.service_state_review_ready,
        issues=tuple(issues),
    )


def _gate4_wet_dry_witness_readiness_issue(
    issues: list[FirstPrintGate4WetDryWitnessReadinessIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate4WetDryWitnessReadinessIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate4_wet_dry_witness_readiness(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    gate3_placement_path: str | Path,
    gate4_wet_dry_witness_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate4WetDryWitnessReadinessAudit:
    gate4_audit = audit_first_print_gate4_wet_dry_witness_worksheet(
        params=params,
        worksheet_path=gate4_wet_dry_witness_path,
    )
    gate3_readiness_audit = audit_first_print_y_split_gate3_placement_readiness(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        gate2_dry_assembly_path=gate2_dry_assembly_path,
        install_inventory_path=install_inventory_path,
        service_state_review_path=service_state_review_path,
        gate3_placement_path=gate3_placement_path,
        expected_setup_summary=expected_setup_summary,
    )
    gate4_pass_targets = tuple(
        row.get("target", "").strip()
        for row in _csv_rows_from_path(gate4_wet_dry_witness_path)
        if row.get("target", "").strip()
        and row.get("result", "").strip() == "pass"
    )
    issues: list[FirstPrintGate4WetDryWitnessReadinessIssue] = []
    if gate4_pass_targets and not gate3_readiness_audit.placement_ready:
        _gate4_wet_dry_witness_readiness_issue(
            issues,
            target="Gate 4 wet/dry witness",
            field="Gate 3 placement",
            message=(
                f"{len(gate4_pass_targets)} Gate 4 pass rows require "
                "Gate 3 placement readiness"
            ),
        )

    return FirstPrintGate4WetDryWitnessReadinessAudit(
        gate4_wet_dry_witness_worksheet_path=Path(gate4_wet_dry_witness_path),
        gate3_placement_worksheet_path=Path(gate3_placement_path),
        gate2_dry_assembly_worksheet_path=Path(gate2_dry_assembly_path),
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        install_inventory_path=Path(install_inventory_path),
        gate4_wet_dry_witness_worksheet_valid=gate4_audit.worksheet_valid,
        gate4_wet_dry_witness_pass_ready=gate4_audit.gate4_pass_ready,
        gate4_pass_row_count=len(gate4_pass_targets),
        gate3_placement_ready=gate3_readiness_audit.placement_ready,
        gate3_placement_worksheet_valid=(
            gate3_readiness_audit.gate3_placement_worksheet_valid
        ),
        gate3_placement_pass_ready=(
            gate3_readiness_audit.gate3_placement_pass_ready
        ),
        gate3_pass_row_count=gate3_readiness_audit.gate3_pass_row_count,
        gate2_dry_assembly_ready=gate3_readiness_audit.gate2_dry_assembly_ready,
        gate2_pass_row_count=gate3_readiness_audit.gate2_pass_row_count,
        gate1_print_qc_ready=gate3_readiness_audit.gate1_print_qc_ready,
        install_inventory_ready=gate3_readiness_audit.install_inventory_ready,
        service_state_review_ready=gate3_readiness_audit.service_state_review_ready,
        issues=tuple(issues),
    )


def _gate5_consumable_puncture_readiness_issue(
    issues: list[FirstPrintGate5ConsumablePunctureReadinessIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate5ConsumablePunctureReadinessIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate5_consumable_puncture_readiness(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    gate3_placement_path: str | Path,
    gate4_wet_dry_witness_path: str | Path,
    gate5_consumable_puncture_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate5ConsumablePunctureReadinessAudit:
    gate5_audit = audit_first_print_gate5_consumable_puncture_worksheet(
        params=params,
        worksheet_path=gate5_consumable_puncture_path,
    )
    gate4_readiness_audit = audit_first_print_y_split_gate4_wet_dry_witness_readiness(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        gate2_dry_assembly_path=gate2_dry_assembly_path,
        install_inventory_path=install_inventory_path,
        service_state_review_path=service_state_review_path,
        gate3_placement_path=gate3_placement_path,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness_path,
        expected_setup_summary=expected_setup_summary,
    )
    gate5_pass_targets = tuple(
        row.get("target", "").strip()
        for row in _csv_rows_from_path(gate5_consumable_puncture_path)
        if row.get("target", "").strip()
        and row.get("result", "").strip() == "pass"
    )
    issues: list[FirstPrintGate5ConsumablePunctureReadinessIssue] = []
    if gate5_pass_targets and not gate4_readiness_audit.wet_dry_witness_ready:
        _gate5_consumable_puncture_readiness_issue(
            issues,
            target="Gate 5 consumable/puncture",
            field="Gate 4 wet/dry witness",
            message=(
                f"{len(gate5_pass_targets)} Gate 5 pass rows require "
                "Gate 4 wet/dry witness readiness"
            ),
        )

    return FirstPrintGate5ConsumablePunctureReadinessAudit(
        gate5_consumable_puncture_worksheet_path=Path(gate5_consumable_puncture_path),
        gate4_wet_dry_witness_worksheet_path=Path(gate4_wet_dry_witness_path),
        gate3_placement_worksheet_path=Path(gate3_placement_path),
        gate2_dry_assembly_worksheet_path=Path(gate2_dry_assembly_path),
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        install_inventory_path=Path(install_inventory_path),
        gate5_consumable_puncture_worksheet_valid=gate5_audit.worksheet_valid,
        gate5_consumable_puncture_pass_ready=gate5_audit.gate5_pass_ready,
        gate5_pass_row_count=len(gate5_pass_targets),
        gate4_wet_dry_witness_ready=(
            gate4_readiness_audit.wet_dry_witness_ready
        ),
        gate4_wet_dry_witness_worksheet_valid=(
            gate4_readiness_audit.gate4_wet_dry_witness_worksheet_valid
        ),
        gate4_wet_dry_witness_pass_ready=(
            gate4_readiness_audit.gate4_wet_dry_witness_pass_ready
        ),
        gate4_pass_row_count=gate4_readiness_audit.gate4_pass_row_count,
        gate3_placement_ready=gate4_readiness_audit.gate3_placement_ready,
        gate3_pass_row_count=gate4_readiness_audit.gate3_pass_row_count,
        gate2_dry_assembly_ready=gate4_readiness_audit.gate2_dry_assembly_ready,
        gate2_pass_row_count=gate4_readiness_audit.gate2_pass_row_count,
        gate1_print_qc_ready=gate4_readiness_audit.gate1_print_qc_ready,
        install_inventory_ready=gate4_readiness_audit.install_inventory_ready,
        service_state_review_ready=gate4_readiness_audit.service_state_review_ready,
        issues=tuple(issues),
    )


def _gate6_sensor_thermal_readiness_issue(
    issues: list[FirstPrintGate6SensorThermalReadinessIssue],
    *,
    target: str,
    field: str,
    message: str,
) -> None:
    issues.append(
        FirstPrintGate6SensorThermalReadinessIssue(
            target=target,
            field=field,
            message=message,
        )
    )


def audit_first_print_y_split_gate6_sensor_thermal_readiness(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    split_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    gate3_placement_path: str | Path,
    gate4_wet_dry_witness_path: str | Path,
    gate5_consumable_puncture_path: str | Path,
    gate6_sensor_thermal_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintGate6SensorThermalReadinessAudit:
    gate6_audit = audit_first_print_gate6_sensor_thermal_worksheet(
        params=params,
        worksheet_path=gate6_sensor_thermal_path,
    )
    gate5_readiness_audit = audit_first_print_y_split_gate5_consumable_puncture_readiness(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        gate2_dry_assembly_path=gate2_dry_assembly_path,
        install_inventory_path=install_inventory_path,
        service_state_review_path=service_state_review_path,
        gate3_placement_path=gate3_placement_path,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness_path,
        gate5_consumable_puncture_path=gate5_consumable_puncture_path,
        expected_setup_summary=expected_setup_summary,
    )
    install_inventory_audit = audit_first_print_install_inventory(
        worksheet_path=install_inventory_path,
    )
    gate6_pass_targets = tuple(
        row.get("target", "").strip()
        for row in _csv_rows_from_path(gate6_sensor_thermal_path)
        if row.get("target", "").strip()
        and row.get("result", "").strip() == "pass"
    )
    issues: list[FirstPrintGate6SensorThermalReadinessIssue] = []
    if gate6_pass_targets and not gate5_readiness_audit.consumable_puncture_ready:
        _gate6_sensor_thermal_readiness_issue(
            issues,
            target="Gate 6 sensor/thermal",
            field="Gate 5 consumable/puncture",
            message=(
                f"{len(gate6_pass_targets)} Gate 6 pass rows require "
                "Gate 5 consumable/puncture readiness"
            ),
        )
    if gate6_pass_targets and not install_inventory_audit.real_sensor_inventory_ready:
        blank_parts = ", ".join(install_inventory_audit.sensor_inventory_blank_parts)
        message = (
            f"{len(gate6_pass_targets)} Gate 6 pass rows require real sensor "
            "and electrical installed items"
        )
        if blank_parts:
            message += f"; dimensional blanks found for {blank_parts}"
        _gate6_sensor_thermal_readiness_issue(
            issues,
            target="Gate 6 sensor/thermal",
            field="Install inventory",
            message=message,
        )

    return FirstPrintGate6SensorThermalReadinessAudit(
        gate6_sensor_thermal_worksheet_path=Path(gate6_sensor_thermal_path),
        gate5_consumable_puncture_worksheet_path=Path(gate5_consumable_puncture_path),
        gate4_wet_dry_witness_worksheet_path=Path(gate4_wet_dry_witness_path),
        gate3_placement_worksheet_path=Path(gate3_placement_path),
        gate2_dry_assembly_worksheet_path=Path(gate2_dry_assembly_path),
        gate1_qc_worksheet_path=Path(gate1_qc_path),
        print_batch_traveler_path=Path(print_batch_traveler_path),
        install_inventory_path=Path(install_inventory_path),
        gate6_sensor_thermal_worksheet_valid=gate6_audit.worksheet_valid,
        gate6_sensor_thermal_pass_ready=gate6_audit.gate6_pass_ready,
        gate6_pass_row_count=len(gate6_pass_targets),
        gate5_consumable_puncture_ready=(
            gate5_readiness_audit.consumable_puncture_ready
        ),
        gate5_consumable_puncture_worksheet_valid=(
            gate5_readiness_audit.gate5_consumable_puncture_worksheet_valid
        ),
        gate5_consumable_puncture_pass_ready=(
            gate5_readiness_audit.gate5_consumable_puncture_pass_ready
        ),
        gate5_pass_row_count=gate5_readiness_audit.gate5_pass_row_count,
        gate4_wet_dry_witness_ready=(
            gate5_readiness_audit.gate4_wet_dry_witness_ready
        ),
        gate4_pass_row_count=gate5_readiness_audit.gate4_pass_row_count,
        gate3_placement_ready=gate5_readiness_audit.gate3_placement_ready,
        gate3_pass_row_count=gate5_readiness_audit.gate3_pass_row_count,
        gate2_dry_assembly_ready=gate5_readiness_audit.gate2_dry_assembly_ready,
        gate2_pass_row_count=gate5_readiness_audit.gate2_pass_row_count,
        gate1_print_qc_ready=gate5_readiness_audit.gate1_print_qc_ready,
        install_inventory_ready=gate5_readiness_audit.install_inventory_ready,
        service_state_review_ready=gate5_readiness_audit.service_state_review_ready,
        real_sensor_inventory_ready=install_inventory_audit.real_sensor_inventory_ready,
        sensor_inventory_blank_parts=install_inventory_audit.sensor_inventory_blank_parts,
        issues=tuple(issues),
    )


def _operating_prototype_acceptance_issue(
    issues: list[FirstPrintOperatingPrototypeAcceptanceIssue],
    *,
    field: str,
    message: str,
) -> None:
    issues.append(FirstPrintOperatingPrototypeAcceptanceIssue(field=field, message=message))


def audit_first_print_y_split_operating_prototype_acceptance(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    queue_dir: str | Path,
    split_dir: str | Path,
    split_queue_dir: str | Path,
    record_path: str | Path,
    root: str | Path,
    slicer_setup_path: str | Path,
    gate1_qc_path: str | Path,
    print_batch_traveler_path: str | Path,
    sliced_output_path: str | Path,
    gate2_dry_assembly_path: str | Path,
    install_inventory_path: str | Path,
    service_state_review_path: str | Path,
    gate3_placement_path: str | Path,
    gate4_wet_dry_witness_path: str | Path,
    gate5_consumable_puncture_path: str | Path,
    gate6_sensor_thermal_path: str | Path,
    expected_setup_summary: str = "",
) -> FirstPrintOperatingPrototypeAcceptanceAudit:
    preflight_audit = audit_first_print_preflight(
        params=params,
        out_dir=out_dir,
        queue_dir=queue_dir,
        split_dir=split_dir,
        record_path=record_path,
        root=root,
    )
    gate6_readiness_audit = audit_first_print_y_split_gate6_sensor_thermal_readiness(
        params=params,
        out_dir=out_dir,
        split_dir=split_dir,
        queue_dir=split_queue_dir,
        slicer_setup_path=slicer_setup_path,
        gate1_qc_path=gate1_qc_path,
        print_batch_traveler_path=print_batch_traveler_path,
        sliced_output_path=sliced_output_path,
        gate2_dry_assembly_path=gate2_dry_assembly_path,
        install_inventory_path=install_inventory_path,
        service_state_review_path=service_state_review_path,
        gate3_placement_path=gate3_placement_path,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness_path,
        gate5_consumable_puncture_path=gate5_consumable_puncture_path,
        gate6_sensor_thermal_path=gate6_sensor_thermal_path,
        expected_setup_summary=expected_setup_summary,
    )
    blocking_preflight_issues = tuple(
        issue
        for issue in preflight_audit.issues
        if issue.field not in FIRST_PRINT_PHYSICAL_GATES
    )
    preflight_artifacts_ready = (
        preflight_audit.package_ready
        and preflight_audit.slicer_queue_ready
        and preflight_audit.params_hash_matches
        and preflight_audit.generated_output_timestamp_matches
        and preflight_audit.cad_target_sections_match
        and preflight_audit.slicer_setup_valid
        and preflight_audit.slicer_setup_selected
        and preflight_audit.slicer_bed_fit_ready
        and preflight_audit.sliced_outputs_valid
        and preflight_audit.gate1_qc_worksheet_valid
        and preflight_audit.gate2_dry_assembly_worksheet_valid
        and preflight_audit.gate3_placement_worksheet_valid
        and preflight_audit.gate4_wet_dry_witness_worksheet_valid
        and preflight_audit.gate5_consumable_puncture_worksheet_valid
        and preflight_audit.gate6_sensor_thermal_worksheet_valid
        and preflight_audit.install_inventory_valid
        and preflight_audit.service_state_review_valid
        and preflight_audit.service_state_review_ready
        and preflight_audit.record_gate0_pass
        and preflight_audit.required_session_fields_present
        and not preflight_audit.missing_record_links
        and not blocking_preflight_issues
    )
    issues: list[FirstPrintOperatingPrototypeAcceptanceIssue] = []
    for issue in blocking_preflight_issues:
        _operating_prototype_acceptance_issue(
            issues,
            field=issue.field,
            message=issue.message,
        )
    for issue in gate6_readiness_audit.issues:
        _operating_prototype_acceptance_issue(
            issues,
            field=issue.field,
            message=issue.message,
        )
    if preflight_audit.physical_gate_passes and not gate6_readiness_audit.sensor_thermal_ready:
        _operating_prototype_acceptance_issue(
            issues,
            field="Physical gate summary",
            message=(
                f"{len(preflight_audit.physical_gate_passes)} record pass rows "
                "require complete Gate 6 sensor/thermal readiness"
            ),
        )

    return FirstPrintOperatingPrototypeAcceptanceAudit(
        record_path=Path(record_path),
        preflight_artifacts_ready=preflight_artifacts_ready,
        print_start_ready=preflight_artifacts_ready and preflight_audit.sliced_outputs_ready,
        service_state_review_ready=preflight_audit.service_state_review_ready,
        install_inventory_ready=gate6_readiness_audit.install_inventory_ready,
        gate1_print_qc_ready=gate6_readiness_audit.gate1_print_qc_ready,
        gate2_dry_assembly_ready=gate6_readiness_audit.gate2_dry_assembly_ready,
        gate2_pass_row_count=gate6_readiness_audit.gate2_pass_row_count,
        gate3_placement_ready=gate6_readiness_audit.gate3_placement_ready,
        gate3_pass_row_count=gate6_readiness_audit.gate3_pass_row_count,
        gate4_wet_dry_witness_ready=(
            gate6_readiness_audit.gate4_wet_dry_witness_ready
        ),
        gate4_pass_row_count=gate6_readiness_audit.gate4_pass_row_count,
        gate5_consumable_puncture_ready=(
            gate6_readiness_audit.gate5_consumable_puncture_ready
        ),
        gate5_pass_row_count=gate6_readiness_audit.gate5_pass_row_count,
        sensor_thermal_ready=gate6_readiness_audit.sensor_thermal_ready,
        real_sensor_inventory_ready=(
            gate6_readiness_audit.real_sensor_inventory_ready
        ),
        sensor_inventory_blank_parts=(
            gate6_readiness_audit.sensor_inventory_blank_parts
        ),
        gate6_sensor_thermal_worksheet_valid=(
            gate6_readiness_audit.gate6_sensor_thermal_worksheet_valid
        ),
        gate6_sensor_thermal_pass_ready=(
            gate6_readiness_audit.gate6_sensor_thermal_pass_ready
        ),
        gate6_pass_row_count=gate6_readiness_audit.gate6_pass_row_count,
        physical_gate_passes=preflight_audit.physical_gate_passes,
        issues=tuple(issues),
    )
