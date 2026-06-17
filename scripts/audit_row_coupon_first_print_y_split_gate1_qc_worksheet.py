from __future__ import annotations

import argparse

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM,
    FIRST_PRINT_GATE1_QC_RESULT_VALUES,
    audit_first_print_y_split_gate1_qc_worksheet,
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
        "--worksheet",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_y_split_gate1_qc.csv",
        help="Split Gate 1 QC worksheet CSV path to audit.",
    )
    parser.add_argument(
        "--tolerance-mm",
        type=float,
        default=FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM,
        help="Allowed absolute X/Y/Z deviation for rows marked pass.",
    )
    parser.add_argument(
        "--require-gate1-pass",
        action="store_true",
        help="Exit nonzero unless all rows are measured, within tolerance, and pass.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    audit = audit_first_print_y_split_gate1_qc_worksheet(
        params=params,
        out_dir=args.out_dir,
        split_dir=args.split_dir,
        queue_dir=args.queue_dir,
        slicer_setup_path=args.slicer_setup,
        worksheet_path=args.worksheet,
        tolerance_mm=args.tolerance_mm,
    )

    print(f"split_gate1_qc_worksheet: {audit.worksheet_path}")
    print(f"worksheet_valid: {'true' if audit.worksheet_valid else 'false'}")
    print(f"gate1_pass_ready: {'true' if audit.gate1_pass_ready else 'false'}")
    print(f"expected_rows: {audit.expected_row_count}")
    print(f"actual_rows: {audit.actual_row_count}")
    print(f"tolerance_mm: {audit.tolerance_mm:.2f}")
    for result in sorted(FIRST_PRINT_GATE1_QC_RESULT_VALUES):
        print(f"{result}_rows: {audit.result_counts.get(result, 0)}")
    print(f"missing_parts: {len(audit.missing_parts)}")
    print(f"extra_parts: {len(audit.extra_parts)}")
    print(f"duplicate_parts: {len(audit.duplicate_parts)}")
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.part} | {issue.field} | {issue.message}")

    if not audit.worksheet_valid:
        raise SystemExit(1)
    if args.require_gate1_pass and not audit.gate1_pass_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
