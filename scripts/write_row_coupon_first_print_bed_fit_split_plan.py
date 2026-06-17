from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    write_first_print_bed_fit_split_plan,
)


def _default_output_path() -> Path:
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
        "--output",
        default=_default_output_path(),
        help="Bed-fit split-plan worksheet CSV path to create.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing bed-fit split-plan worksheet.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    output = write_first_print_bed_fit_split_plan(
        params=params,
        out_dir=args.out_dir,
        slicer_setup_path=args.slicer_setup,
        output_path=args.output,
        overwrite=args.overwrite,
    )

    print(f"bed_fit_split_plan: {output}")
    print(f"slicer_setup: {args.slicer_setup}")


if __name__ == "__main__":
    main()
