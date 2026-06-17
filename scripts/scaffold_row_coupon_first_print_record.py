from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    audit_first_print_package,
    scaffold_first_print_measurement_record,
)


def _default_output_path() -> Path:
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
        help="CAD output directory to audit.",
    )
    parser.add_argument(
        "--template",
        default=ROOT
        / "data"
        / "measurements"
        / "templates"
        / "one_row_coupon_first_print_readiness.md",
        help="Measurement template to copy and prefill.",
    )
    parser.add_argument(
        "--output",
        default=_default_output_path(),
        help="Measurement record path to create.",
    )
    parser.add_argument(
        "--cad-source-note",
        default="unrecorded-local-worktree",
        help="CAD source commit, branch, or worktree note to store in the record.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing measurement record.",
    )
    args = parser.parse_args()

    params_path = Path(args.params)
    params = load_params(params_path)
    output = scaffold_first_print_measurement_record(
        params=params,
        params_path=params_path,
        out_dir=args.out_dir,
        template_path=args.template,
        output_path=args.output,
        cad_source_note=args.cad_source_note,
        overwrite=args.overwrite,
    )
    audit = audit_first_print_package(params, args.out_dir)

    print(f"measurement record: {output}")
    print(f"gate0_audit_ready: {'true' if audit.ready else 'false'}")
    print(f"missing_required_artifacts: {len(audit.missing_paths)}")


if __name__ == "__main__":
    main()
