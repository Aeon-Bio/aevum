from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    audit_first_print_bed_fit_split_plan,
)


def _default_worksheet_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_bed_fit_split_plan.csv"


def _default_slicer_setup_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_slicer_setup.csv"


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
        "--slicer-setup",
        default=_default_slicer_setup_path(),
        help="Selected slicer setup worksheet CSV path.",
    )
    parser.add_argument(
        "--worksheet",
        default=_default_worksheet_path(),
        help="Bed-fit split-plan worksheet CSV path to audit.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero unless every split-plan row is marked pass.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    audit = audit_first_print_bed_fit_split_plan(
        params=params,
        out_dir=args.out_dir,
        slicer_setup_path=args.slicer_setup,
        worksheet_path=args.worksheet,
    )

    print(f"bed_fit_split_plan: {audit.worksheet_path}")
    print(f"worksheet_valid: {'true' if audit.worksheet_valid else 'false'}")
    print(f"split_plan_ready: {'true' if audit.split_plan_ready else 'false'}")
    print(f"expected_rows: {audit.expected_row_count}")
    print(f"actual_rows: {audit.actual_row_count}")
    print(f"split_required_parts: {len(audit.split_required_parts)}")
    for part in audit.split_required_parts:
        print(f"split_required_part: {part}")
    print(f"missing_parts: {len(audit.missing_parts)}")
    print(f"extra_parts: {len(audit.extra_parts)}")
    print(f"duplicate_parts: {len(audit.duplicate_parts)}")
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.part} | {issue.field} | {issue.message}")

    if not audit.worksheet_valid:
        raise SystemExit(1)
    if args.require_ready and not audit.split_plan_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
