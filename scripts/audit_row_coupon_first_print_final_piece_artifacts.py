from __future__ import annotations

import argparse

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import audit_first_print_final_piece_artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--params",
        default=ROOT / "cad" / "one_row_coupon.params.json",
        help="Path to the one-row coupon params JSON file.",
    )
    parser.add_argument(
        "--out-dir",
        default=ROOT / "outputs" / "cad",
        help="CAD output directory containing generated monolithic STL/STEP files.",
    )
    parser.add_argument(
        "--piece-dir",
        default=ROOT / "outputs" / "cad" / "final_print_pieces",
        help="Directory containing generated canonical final-piece STL/STEP files.",
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
        "--require-ready",
        action="store_true",
        help="Exit nonzero unless every final-piece artifact exists and fits the selected bed.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    audit = audit_first_print_final_piece_artifacts(
        params=params,
        out_dir=args.out_dir,
        piece_dir=args.piece_dir,
        slicer_setup_path=args.slicer_setup,
    )

    print(f"piece_dir: {audit.piece_dir}")
    print(f"selected_setup: {audit.selected_setup_summary}")
    print(f"selected_bed_x_mm: {audit.bed_x_mm:.2f}")
    print(f"selected_bed_y_mm: {audit.bed_y_mm:.2f}")
    print(f"final_piece_artifacts_ready: {str(audit.final_piece_artifacts_ready).lower()}")
    print(f"expected_rows: {audit.expected_row_count}")
    print(f"actual_rows: {len(audit.rows)}")
    print(f"split_source_parts: {len(audit.split_source_parts)}")
    for part in audit.split_source_parts:
        print(f"split_source_part: {part}")
    print(f"covered_oversized_parts: {len(audit.covered_oversized_parts)}")
    for part in audit.covered_oversized_parts:
        print(f"covered_oversized_part: {part}")
    print(f"missing_oversized_parts: {len(audit.missing_oversized_parts)}")
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.split_part} | {issue.field} | {issue.message}")

    if args.require_ready and not audit.final_piece_artifacts_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
