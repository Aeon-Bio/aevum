from __future__ import annotations

import argparse
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon.assembly_coupons import (
    export_row_coupon_assembly_coupon_package,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export profile-scoped Aevum row-coupon assembly test coupons."
    )
    parser.add_argument(
        "params",
        nargs="?",
        type=Path,
        default=ROOT / "cad" / "one_row_coupon.params.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "outputs" / "cad" / "assembly_coupons",
    )
    parser.add_argument(
        "--profile",
        type=Path,
        required=True,
        help="Exact exported slicer profile used for the coupon run; its SHA-256 is recorded.",
    )
    args = parser.parse_args()
    paths = export_row_coupon_assembly_coupon_package(
        load_params(args.params), args.output, profile_path=args.profile
    )
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
