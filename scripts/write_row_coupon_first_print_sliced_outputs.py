from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    first_print_record_table_value,
    write_first_print_sliced_outputs,
)


def _default_output_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_sliced_outputs.csv"


def _default_record_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_first_print.md"


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
        "--queue-dir",
        default=ROOT / "outputs" / "cad" / "first_print_slicer_queue",
        help="Printed-STL-only slicer queue directory.",
    )
    parser.add_argument(
        "--output",
        default=_default_output_path(),
        help="Sliced-output worksheet CSV path to create.",
    )
    parser.add_argument(
        "--record",
        default=_default_record_path(),
        help="Measurement record to read selected setup from, if present.",
    )
    parser.add_argument(
        "--selected-setup-summary",
        default="",
        help="Selected slicer setup summary to prefill.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing sliced-output worksheet.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    selected_setup_summary = args.selected_setup_summary or first_print_record_table_value(
        args.record,
        "Printer / material / profile",
    )
    output = write_first_print_sliced_outputs(
        params=params,
        out_dir=args.out_dir,
        queue_dir=args.queue_dir,
        output_path=args.output,
        selected_setup_summary=selected_setup_summary,
        overwrite=args.overwrite,
    )

    print(f"sliced_outputs: {output}")
    print(f"selected_setup_summary: {selected_setup_summary}")


if __name__ == "__main__":
    main()
