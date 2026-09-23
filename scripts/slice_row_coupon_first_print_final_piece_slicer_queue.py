from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import slice_first_print_final_piece_slicer_queue


def _default_output_path() -> Path:
    today = datetime.now().date().isoformat()
    return (
        ROOT
        / "data"
        / "measurements"
        / f"{today}_one_row_coupon_final_piece_sliced_outputs.csv"
    )


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
        "--sliced-dir",
        default=ROOT / "outputs" / "sliced" / "first_print_final_piece",
        help="Directory to receive sliced G-code files.",
    )
    parser.add_argument(
        "--output",
        default=_default_output_path(),
        help="Final-piece sliced-output worksheet CSV path to write with hashes.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing G-code files and sliced-output worksheet.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    rows = slice_first_print_final_piece_slicer_queue(
        params=params,
        out_dir=args.out_dir,
        piece_dir=args.piece_dir,
        queue_dir=args.queue_dir,
        slicer_setup_path=args.slicer_setup,
        sliced_dir=args.sliced_dir,
        output_path=args.output,
        overwrite=args.overwrite,
    )

    print(f"split_sliced_outputs: {args.output}")
    print(f"sliced_dir: {args.sliced_dir}")
    print(f"sliced_rows: {len(rows)}")
    print("result: pass")


if __name__ == "__main__":
    main()
