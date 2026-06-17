from __future__ import annotations

import argparse
from collections import defaultdict

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import audit_first_print_package


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
    args = parser.parse_args()

    params = load_params(args.params)
    audit = audit_first_print_package(params, args.out_dir)

    print(f"first-print package: {audit.name}")
    print(f"output directory: {audit.out_dir}")
    print(
        "assembly_step: "
        f"{'ok' if audit.assembly_step_exists else 'missing'} {audit.assembly_step}"
    )

    by_category: dict[str, list[str]] = defaultdict(list)
    for artifact in audit.production_artifacts:
        by_category[artifact.category].append(artifact.name)
    for category in sorted(by_category):
        print(f"{category}: {len(by_category[category])}")

    print(f"required_validation: {len(audit.validation_artifacts)}")
    print(f"optional_validation: {len(audit.optional_validation_artifacts)}")

    missing = audit.missing_paths
    if missing:
        print("missing required artifacts:")
        for path in missing:
            print(f"- {path}")
        raise SystemExit(1)

    print("ready: true")


if __name__ == "__main__":
    main()
