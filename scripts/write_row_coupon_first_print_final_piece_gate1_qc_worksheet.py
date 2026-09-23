from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    first_print_final_piece_gate1_qc_worksheet_rows,
    write_first_print_final_piece_gate1_qc_worksheet,
)


def _default_output_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_final_piece_gate1_qc.csv"


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
        "--output",
        default=_default_output_path(),
        help="Final Gate 1 QC worksheet CSV path to create.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing split Gate 1 QC worksheet.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    output = write_first_print_final_piece_gate1_qc_worksheet(
        params=params,
        out_dir=args.out_dir,
        piece_dir=args.piece_dir,
        queue_dir=args.queue_dir,
        slicer_setup_path=args.slicer_setup,
        output_path=args.output,
        overwrite=args.overwrite,
    )
    rows = first_print_final_piece_gate1_qc_worksheet_rows(
        params=params,
        out_dir=args.out_dir,
        piece_dir=args.piece_dir,
        queue_dir=args.queue_dir,
        slicer_setup_path=args.slicer_setup,
    )

    print(f"split_gate1_qc_worksheet: {output}")
    print(f"rows: {len(rows)}")
    print("default_result: not_tested")


if __name__ == "__main__":
    main()
