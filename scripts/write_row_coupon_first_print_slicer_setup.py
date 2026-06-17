from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT
from aevum_cad.row_coupon_first_print import (
    discover_first_print_slicer_setup_rows,
    write_first_print_slicer_setup,
)


def _default_output_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_slicer_setup.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=_default_output_path(),
        help="Slicer setup worksheet CSV path to create.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing slicer setup worksheet.",
    )
    args = parser.parse_args()

    rows = discover_first_print_slicer_setup_rows()
    output = write_first_print_slicer_setup(
        output_path=args.output,
        rows=rows,
        overwrite=args.overwrite,
    )

    print(f"slicer_setup: {output}")
    print(f"rows: {len(rows)}")
    print("selected_rows: 0")


if __name__ == "__main__":
    main()
