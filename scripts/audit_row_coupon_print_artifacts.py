from __future__ import annotations

import argparse
import json

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon.print_audit import audit_row_coupon_print_artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "params",
        nargs="?",
        default=ROOT / "cad" / "one_row_coupon.params.json",
        help="Path to a one-row coupon params JSON file.",
    )
    args = parser.parse_args()
    print(json.dumps(audit_row_coupon_print_artifacts(load_params(args.params)), indent=2))


if __name__ == "__main__":
    main()
