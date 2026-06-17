from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    first_print_gate6_sensor_thermal_worksheet_rows,
    write_first_print_gate6_sensor_thermal_worksheet,
)


def _default_output_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_gate6_sensor_thermal.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "params",
        nargs="?",
        default=ROOT / "cad" / "one_row_coupon.params.json",
        help="Path to a one-row coupon params JSON file.",
    )
    parser.add_argument(
        "--output",
        default=_default_output_path(),
        help="Gate 6 sensor/thermal worksheet CSV path to create.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing Gate 6 sensor/thermal worksheet.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    output = write_first_print_gate6_sensor_thermal_worksheet(
        params=params,
        output_path=args.output,
        overwrite=args.overwrite,
    )
    rows = first_print_gate6_sensor_thermal_worksheet_rows(params)

    print(f"gate6_sensor_thermal_worksheet: {output}")
    print(f"rows: {len(rows)}")
    print("default_result: not_tested")


if __name__ == "__main__":
    main()
