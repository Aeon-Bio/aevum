from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT
from aevum_cad.row_coupon_first_print import (
    first_print_install_inventory_rows,
    write_first_print_install_inventory,
)


def _default_output_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_install_inventory.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=_default_output_path(),
        help="Install inventory worksheet CSV path to create.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing install inventory worksheet.",
    )
    args = parser.parse_args()

    output = write_first_print_install_inventory(
        output_path=args.output,
        overwrite=args.overwrite,
    )
    rows = first_print_install_inventory_rows()

    print(f"install_inventory: {output}")
    print(f"rows: {len(rows)}")
    print("default_result: not_tested")


if __name__ == "__main__":
    main()
