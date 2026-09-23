from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    first_print_record_table_value,
    write_first_print_final_piece_print_batch_traveler,
)


def _default_output_path() -> Path:
    today = datetime.now().date().isoformat()
    return (
        ROOT
        / "data"
        / "measurements"
        / f"{today}_one_row_coupon_final_piece_print_batch_traveler.csv"
    )


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
        help="CAD output directory containing generated production STL/STEP files.",
    )
    parser.add_argument(
        "--piece-dir",
        default=ROOT / "outputs" / "cad" / "final_print_pieces",
        help="Directory containing generated canonical final-piece STL/STEP files.",
    )
    parser.add_argument(
        "--queue-dir",
        default=ROOT / "outputs" / "cad" / "first_print_final_piece_slicer_queue",
        help="Final-piece first-print slicer queue directory.",
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
        "--sliced-outputs",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_final_piece_sliced_outputs.csv",
        help="Ready final-piece sliced-output worksheet.",
    )
    parser.add_argument(
        "--gate1-qc",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_final_piece_gate1_qc.csv",
        help="Final Gate 1 QC worksheet.",
    )
    parser.add_argument(
        "--output",
        default=_default_output_path(),
        help="Final print batch traveler CSV path to create.",
    )
    parser.add_argument(
        "--record",
        default=_default_record_path(),
        help="Measurement record to read selected setup from, if present.",
    )
    parser.add_argument(
        "--selected-setup-summary",
        default="",
        help="Selected slicer setup summary to require.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing print batch traveler.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    expected_setup = args.selected_setup_summary or first_print_record_table_value(
        args.record,
        "Printer / material / profile",
    )
    output = write_first_print_final_piece_print_batch_traveler(
        params=params,
        out_dir=args.out_dir,
        piece_dir=args.piece_dir,
        queue_dir=args.queue_dir,
        slicer_setup_path=args.slicer_setup,
        sliced_output_path=args.sliced_outputs,
        gate1_qc_path=args.gate1_qc,
        output_path=args.output,
        expected_setup_summary=expected_setup,
        overwrite=args.overwrite,
    )

    print(f"split_print_batch_traveler: {output}")
    print(f"selected_setup_summary: {expected_setup}")
    print("result: pass")


if __name__ == "__main__":
    main()
