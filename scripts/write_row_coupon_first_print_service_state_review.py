from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    first_print_service_state_review_rows,
    write_first_print_service_state_bounds_evidence,
    write_first_print_service_state_review,
)


def _default_output_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_service_state_review.csv"


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
        help="Service-state review worksheet CSV path to create.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing service-state review worksheet.",
    )
    parser.add_argument(
        "--bounds-evidence-dir",
        default=None,
        help=(
            "Optional directory for generated plain-Python CadQuery bounds evidence. "
            "When supplied, worksheet rows are marked pass against those files."
        ),
    )
    args = parser.parse_args()

    params = load_params(args.params)
    evidence_paths = None
    if args.bounds_evidence_dir is not None:
        evidence_paths = write_first_print_service_state_bounds_evidence(
            params,
            output_dir=args.bounds_evidence_dir,
            overwrite=args.overwrite,
        )
    output = write_first_print_service_state_review(
        output_path=args.output,
        overwrite=args.overwrite,
        evidence_paths_by_mode=evidence_paths,
    )
    rows = first_print_service_state_review_rows()

    print(f"service_state_review_worksheet: {output}")
    print(f"rows: {len(rows)}")
    if evidence_paths is None:
        print("default_result: not_tested")
    else:
        print(f"bounds_evidence_dir: {args.bounds_evidence_dir}")
        print(f"bounds_evidence_files: {len(evidence_paths)}")
        print("default_result: pass")


if __name__ == "__main__":
    main()
