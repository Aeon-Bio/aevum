from __future__ import annotations

import argparse

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    audit_first_print_final_piece_gate3_placement_readiness,
    first_print_record_table_value,
)


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
        help="CAD output directory containing generated production STL/STEP files.",
    )
    parser.add_argument(
        "--piece-dir",
        default=ROOT / "outputs" / "cad" / "final_print_pieces",
        help="Directory containing generated canonical final-piece STL/STEP files.",
    )
    parser.add_argument(
        "--queue-dir",
        default=ROOT / "outputs" / "cad" / "first_print_final_piece_slicer_queue",
        help="Final-piece first-print slicer queue directory.",
    )
    parser.add_argument(
        "--slicer-setup",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_slicer_setup.csv",
        help="Selected slicer setup worksheet.",
    )
    parser.add_argument(
        "--gate1-qc",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_final_piece_gate1_qc.csv",
        help="Final Gate 1 QC worksheet.",
    )
    parser.add_argument(
        "--print-batch-traveler",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_final_piece_print_batch_traveler.csv",
        help="Final print batch traveler worksheet.",
    )
    parser.add_argument(
        "--sliced-outputs",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_final_piece_sliced_outputs.csv",
        help="Ready final-piece sliced-output worksheet.",
    )
    parser.add_argument(
        "--gate2-dry-assembly",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_gate2_dry_assembly.csv",
        help="Gate 2 dry assembly worksheet.",
    )
    parser.add_argument(
        "--install-inventory",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_install_inventory.csv",
        help="Install inventory worksheet.",
    )
    parser.add_argument(
        "--service-state-review",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_service_state_review.csv",
        help="Service-state review worksheet.",
    )
    parser.add_argument(
        "--gate3-placement",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_gate3_placement.csv",
        help="Gate 3 OT-2 placement worksheet.",
    )
    parser.add_argument(
        "--record",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_first_print.md",
        help="Measurement record to read selected setup from, if present.",
    )
    parser.add_argument(
        "--require-placement-ready",
        action="store_true",
        help="Exit nonzero unless Gate 3 placement and upstream dry assembly are ready.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    expected_setup = first_print_record_table_value(
        args.record,
        "Printer / material / profile",
    )
    audit = audit_first_print_final_piece_gate3_placement_readiness(
        params=params,
        out_dir=args.out_dir,
        piece_dir=args.piece_dir,
        queue_dir=args.queue_dir,
        slicer_setup_path=args.slicer_setup,
        gate1_qc_path=args.gate1_qc,
        print_batch_traveler_path=args.print_batch_traveler,
        sliced_output_path=args.sliced_outputs,
        gate2_dry_assembly_path=args.gate2_dry_assembly,
        install_inventory_path=args.install_inventory,
        service_state_review_path=args.service_state_review,
        gate3_placement_path=args.gate3_placement,
        expected_setup_summary=expected_setup,
    )

    print(f"gate3_placement_worksheet: {audit.gate3_placement_worksheet_path}")
    print(
        "gate2_dry_assembly_worksheet: "
        f"{audit.gate2_dry_assembly_worksheet_path}"
    )
    print(f"split_gate1_qc_worksheet: {audit.gate1_qc_worksheet_path}")
    print(f"split_print_batch_traveler: {audit.print_batch_traveler_path}")
    print(f"install_inventory: {audit.install_inventory_path}")
    print(f"placement_ready: {'true' if audit.placement_ready else 'false'}")
    print(
        "gate3_placement_worksheet_valid: "
        f"{'true' if audit.gate3_placement_worksheet_valid else 'false'}"
    )
    print(
        "gate3_placement_pass_ready: "
        f"{'true' if audit.gate3_placement_pass_ready else 'false'}"
    )
    print(f"gate3_pass_rows: {audit.gate3_pass_row_count}")
    print(
        "gate2_dry_assembly_ready: "
        f"{'true' if audit.gate2_dry_assembly_ready else 'false'}"
    )
    print(
        "gate2_dry_assembly_worksheet_valid: "
        f"{'true' if audit.gate2_dry_assembly_worksheet_valid else 'false'}"
    )
    print(
        "gate2_dry_assembly_pass_ready: "
        f"{'true' if audit.gate2_dry_assembly_pass_ready else 'false'}"
    )
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.target} | {issue.field} | {issue.message}")

    if audit.issues:
        raise SystemExit(1)
    if args.require_placement_ready and not audit.placement_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
