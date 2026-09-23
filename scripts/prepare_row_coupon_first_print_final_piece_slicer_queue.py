from __future__ import annotations

import argparse
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import prepare_first_print_final_piece_slicer_queue


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
        help="Directory to receive final-piece first-print STL files.",
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
        "--overwrite",
        action="store_true",
        help="Replace existing queued STL files and queue manifest.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    queue_dir = Path(args.queue_dir)
    items = prepare_first_print_final_piece_slicer_queue(
        params=params,
        out_dir=args.out_dir,
        piece_dir=args.piece_dir,
        queue_dir=queue_dir,
        slicer_setup_path=args.slicer_setup,
        overwrite=args.overwrite,
    )

    print(f"final-piece slicer queue: {queue_dir}")
    print(f"queued_printed_stls: {len(items)}")
    print(f"queue_manifest: {queue_dir / 'SLICER_QUEUE_MANIFEST.md'}")


if __name__ == "__main__":
    main()
