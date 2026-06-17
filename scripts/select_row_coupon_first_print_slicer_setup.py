from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT
from aevum_cad.row_coupon_first_print import select_first_print_slicer_setup


def _default_worksheet_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_slicer_setup.csv"


def _default_record_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_first_print.md"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--worksheet",
        default=_default_worksheet_path(),
        help="Slicer setup worksheet CSV path to update.",
    )
    parser.add_argument(
        "--record",
        default=_default_record_path(),
        help="First-print measurement record to update.",
    )
    parser.add_argument(
        "--setup-summary",
        default="",
        help="Exact setup summary to select: slicer / printer / material / profile.",
    )
    parser.add_argument(
        "--slicer-name",
        default="",
        help="Slicer name to select when setup summary is not supplied.",
    )
    parser.add_argument(
        "--printer-profile",
        default="",
        help="Optional printer-profile filter used with --slicer-name.",
    )
    parser.add_argument(
        "--material-profile",
        default="",
        help="Optional material-profile filter used with --slicer-name.",
    )
    parser.add_argument(
        "--print-profile",
        default="",
        help="Optional print-profile filter used with --slicer-name.",
    )
    args = parser.parse_args()

    selection = select_first_print_slicer_setup(
        worksheet_path=args.worksheet,
        record_path=args.record,
        setup_summary=args.setup_summary,
        slicer_name=args.slicer_name,
        printer_profile=args.printer_profile,
        material_profile=args.material_profile,
        print_profile=args.print_profile,
    )

    print(f"slicer_setup: {selection.worksheet_path}")
    print(f"measurement_record: {selection.record_path}")
    print(f"selected_row_index: {selection.selected_row_index}")
    print(f"selected_setup: {selection.selected_setup_summary}")
    print(f"worksheet_valid: {'true' if selection.audit.worksheet_valid else 'false'}")
    print(f"setup_selected: {'true' if selection.audit.setup_selected else 'false'}")


if __name__ == "__main__":
    main()
