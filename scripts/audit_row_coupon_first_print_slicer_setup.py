from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT
from aevum_cad.row_coupon_first_print import audit_first_print_slicer_setup


def _default_worksheet_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_slicer_setup.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--worksheet",
        default=_default_worksheet_path(),
        help="Slicer setup worksheet CSV path to audit.",
    )
    parser.add_argument(
        "--require-selected",
        action="store_true",
        help="Exit nonzero unless exactly one setup row is selected and passing.",
    )
    args = parser.parse_args()

    audit = audit_first_print_slicer_setup(worksheet_path=args.worksheet)

    print(f"slicer_setup: {audit.worksheet_path}")
    print(f"worksheet_valid: {'true' if audit.worksheet_valid else 'false'}")
    print(f"setup_selected: {'true' if audit.setup_selected else 'false'}")
    print(f"row_count: {audit.row_count}")
    print(f"selected_rows: {audit.selected_row_count}")
    print(f"selected_setup: {audit.selected_setup_summary}")
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.slicer_name} | {issue.field} | {issue.message}")

    if not audit.worksheet_valid:
        raise SystemExit(1)
    if args.require_selected and not audit.setup_selected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
