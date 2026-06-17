from __future__ import annotations

import argparse

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    audit_first_print_y_split_print_batch_traveler,
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
        "--split-dir",
        default=ROOT / "outputs" / "cad" / "first_print_y_split_parts",
        help="Directory containing generated production Y-split STL/STEP files.",
    )
    parser.add_argument(
        "--queue-dir",
        default=ROOT / "outputs" / "cad" / "first_print_y_split_slicer_queue",
        help="Split first-print slicer queue directory.",
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
        "--sliced-outputs",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_y_split_sliced_outputs.csv",
        help="Ready split sliced-output worksheet.",
    )
    parser.add_argument(
        "--gate1-qc",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_y_split_gate1_qc.csv",
        help="Split Gate 1 QC worksheet.",
    )
    parser.add_argument(
        "--worksheet",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_y_split_print_batch_traveler.csv",
        help="Split print batch traveler CSV path to audit.",
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
        "--require-handoff-ready",
        action="store_true",
        help="Exit nonzero unless the traveler is ready for physical print handoff.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    expected_setup = first_print_record_table_value(
        args.record,
        "Printer / material / profile",
    )
    audit = audit_first_print_y_split_print_batch_traveler(
        params=params,
        out_dir=args.out_dir,
        split_dir=args.split_dir,
        queue_dir=args.queue_dir,
        slicer_setup_path=args.slicer_setup,
        sliced_output_path=args.sliced_outputs,
        gate1_qc_path=args.gate1_qc,
        worksheet_path=args.worksheet,
        expected_setup_summary=expected_setup,
    )

    print(f"split_print_batch_traveler: {audit.worksheet_path}")
    print(f"worksheet_valid: {'true' if audit.worksheet_valid else 'false'}")
    print(f"handoff_ready: {'true' if audit.handoff_ready else 'false'}")
    print(f"sliced_outputs_ready: {'true' if audit.sliced_outputs_ready else 'false'}")
    print(
        "gate1_qc_worksheet_valid: "
        f"{'true' if audit.gate1_qc_worksheet_valid else 'false'}"
    )
    print(f"expected_rows: {audit.expected_row_count}")
    print(f"actual_rows: {audit.actual_row_count}")
    print(f"missing_parts: {len(audit.missing_parts)}")
    print(f"extra_parts: {len(audit.extra_parts)}")
    print(f"duplicate_parts: {len(audit.duplicate_parts)}")
    print(f"print_result_counts: {audit.print_result_counts}")
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.part} | {issue.field} | {issue.message}")

    if not audit.worksheet_valid:
        raise SystemExit(1)
    if args.require_handoff_ready and not audit.handoff_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
