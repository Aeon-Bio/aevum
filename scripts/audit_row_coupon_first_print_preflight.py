from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import audit_first_print_preflight


def _default_record_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_first_print.md"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "params",
        nargs="?",
        default=ROOT / "cad" / "one_row_coupon.params.json",
        help="Path to a one-row coupon params JSON file.",
    )
    parser.add_argument(
        "--out-dir",
        default=ROOT / "outputs" / "cad",
        help="CAD output directory containing generated STL/STEP files.",
    )
    parser.add_argument(
        "--queue-dir",
        default=ROOT / "outputs" / "cad" / "first_print_slicer_queue",
        help="Printed-STL-only slicer queue directory.",
    )
    parser.add_argument(
        "--piece-dir",
        default=ROOT / "outputs" / "cad" / "final_print_pieces",
        help="Directory containing generated canonical final-piece STL/STEP files.",
    )
    parser.add_argument(
        "--record",
        default=_default_record_path(),
        help="First-print measurement record to audit.",
    )
    parser.add_argument(
        "--require-sliced-outputs-ready",
        action="store_true",
        help=(
            "Require actual sliced output files, hashes, and pass rows before "
            "accepting print start."
        ),
    )
    args = parser.parse_args()

    params = load_params(args.params)
    audit = audit_first_print_preflight(
        params=params,
        out_dir=args.out_dir,
        queue_dir=args.queue_dir,
        piece_dir=args.piece_dir,
        record_path=args.record,
        root=ROOT,
    )

    print(f"measurement_record: {audit.record_path}")
    print(f"active_queue_mode: {audit.active_queue_mode}")
    print(f"preprint_ready: {'true' if audit.preprint_ready else 'false'}")
    print(f"print_start_ready: {'true' if audit.print_start_ready else 'false'}")
    print(f"package_ready: {'true' if audit.package_ready else 'false'}")
    print(f"slicer_queue_ready: {'true' if audit.slicer_queue_ready else 'false'}")
    print(
        "params_hash_matches: "
        f"{'true' if audit.params_hash_matches else 'false'}"
    )
    print(f"expected_params_sha256: {audit.expected_params_sha256}")
    print(f"record_params_sha256: {audit.record_params_sha256}")
    print(
        "generated_output_timestamp_matches: "
        f"{'true' if audit.generated_output_timestamp_matches else 'false'}"
    )
    print(
        "cad_target_sections_match: "
        f"{'true' if audit.cad_target_sections_match else 'false'}"
    )
    print(
        "expected_generated_output_timestamp: "
        f"{audit.expected_generated_output_timestamp}"
    )
    print(
        "record_generated_output_timestamp: "
        f"{audit.record_generated_output_timestamp}"
    )
    print(f"slicer_setup_valid: {'true' if audit.slicer_setup_valid else 'false'}")
    print(
        "slicer_setup_selected: "
        f"{'true' if audit.slicer_setup_selected else 'false'}"
    )
    print(f"selected_slicer_setup: {audit.selected_slicer_setup}")
    print(
        "slicer_bed_fit_ready: "
        f"{'true' if audit.slicer_bed_fit_ready else 'false'}"
    )
    print(f"slicer_bed_x_mm: {audit.slicer_bed_x_mm:.2f}")
    print(f"slicer_bed_y_mm: {audit.slicer_bed_y_mm:.2f}")
    print(f"slicer_bed_oversized_parts: {len(audit.slicer_bed_oversized_parts)}")
    for part in audit.slicer_bed_oversized_parts:
        print(f"slicer_bed_oversized_part: {part}")
    print(
        "sliced_outputs_valid: "
        f"{'true' if audit.sliced_outputs_valid else 'false'}"
    )
    print(
        "sliced_outputs_ready: "
        f"{'true' if audit.sliced_outputs_ready else 'false'}"
    )
    print(
        "gate1_qc_worksheet_valid: "
        f"{'true' if audit.gate1_qc_worksheet_valid else 'false'}"
    )
    print(f"gate1_pass_ready: {'true' if audit.gate1_pass_ready else 'false'}")
    print(
        "gate2_dry_assembly_worksheet_valid: "
        f"{'true' if audit.gate2_dry_assembly_worksheet_valid else 'false'}"
    )
    print(
        "gate2_dry_assembly_pass_ready: "
        f"{'true' if audit.gate2_dry_assembly_pass_ready else 'false'}"
    )
    print(
        "gate3_placement_worksheet_valid: "
        f"{'true' if audit.gate3_placement_worksheet_valid else 'false'}"
    )
    print(
        "gate3_placement_pass_ready: "
        f"{'true' if audit.gate3_placement_pass_ready else 'false'}"
    )
    print(
        "gate4_wet_dry_witness_worksheet_valid: "
        f"{'true' if audit.gate4_wet_dry_witness_worksheet_valid else 'false'}"
    )
    print(
        "gate4_wet_dry_witness_pass_ready: "
        f"{'true' if audit.gate4_wet_dry_witness_pass_ready else 'false'}"
    )
    print(
        "gate5_consumable_puncture_worksheet_valid: "
        f"{'true' if audit.gate5_consumable_puncture_worksheet_valid else 'false'}"
    )
    print(
        "gate5_consumable_puncture_pass_ready: "
        f"{'true' if audit.gate5_consumable_puncture_pass_ready else 'false'}"
    )
    print(
        "gate6_sensor_thermal_worksheet_valid: "
        f"{'true' if audit.gate6_sensor_thermal_worksheet_valid else 'false'}"
    )
    print(
        "gate6_sensor_thermal_pass_ready: "
        f"{'true' if audit.gate6_sensor_thermal_pass_ready else 'false'}"
    )
    print(
        "install_inventory_valid: "
        f"{'true' if audit.install_inventory_valid else 'false'}"
    )
    print(
        "install_inventory_ready: "
        f"{'true' if audit.install_inventory_ready else 'false'}"
    )
    print(
        "service_state_review_valid: "
        f"{'true' if audit.service_state_review_valid else 'false'}"
    )
    print(
        "service_state_review_ready: "
        f"{'true' if audit.service_state_review_ready else 'false'}"
    )
    print(f"record_gate0_pass: {'true' if audit.record_gate0_pass else 'false'}")
    print(
        "required_session_fields_present: "
        f"{'true' if audit.required_session_fields_present else 'false'}"
    )
    print(f"missing_session_fields: {len(audit.missing_session_fields)}")
    for field in audit.missing_session_fields:
        print(f"missing_session_field: {field}")
    print(f"physical_gate_passes: {len(audit.physical_gate_passes)}")
    for gate in audit.physical_gate_passes:
        print(f"physical_gate_pass: {gate}")
    print(f"missing_record_links: {len(audit.missing_record_links)}")
    for field in audit.missing_record_links:
        print(f"missing_record_link: {field}")
    print(f"stale_cad_target_sections: {len(audit.stale_cad_target_sections)}")
    for section in audit.stale_cad_target_sections:
        print(f"stale_cad_target_section: {section}")
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.field} | {issue.message}")

    if args.require_sliced_outputs_ready:
        if not audit.print_start_ready:
            raise SystemExit(1)
    elif not audit.preprint_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
