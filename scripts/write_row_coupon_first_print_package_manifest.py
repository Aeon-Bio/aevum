from __future__ import annotations

import argparse
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    audit_first_print_package,
    write_first_print_package_manifest,
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
        help="CAD output directory containing generated STL/STEP files.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Package manifest path to create.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing package manifest.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    output = Path(args.output) if args.output else (
        ROOT / "outputs" / "cad" / f"{params['name']}_first_print_package_manifest.md"
    )
    manifest_path = write_first_print_package_manifest(
        params=params,
        out_dir=args.out_dir,
        output_path=output,
        overwrite=args.overwrite,
    )
    audit = audit_first_print_package(params, args.out_dir)
    printed_count = sum(
        1 for artifact in audit.production_artifacts if artifact.category == "printed"
    )

    print(f"package manifest: {manifest_path}")
    print(f"gate0_audit_ready: {'true' if audit.ready else 'false'}")
    print(f"printed_slicer_parts: {printed_count}")
    print(f"missing_required_artifacts: {len(audit.missing_paths)}")


if __name__ == "__main__":
    main()
