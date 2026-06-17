from __future__ import annotations

import argparse

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import audit_first_print_slicer_queue


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
        "--queue-dir",
        default=ROOT / "outputs" / "cad" / "first_print_slicer_queue",
        help="Directory containing queued printed production STL files.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    audit = audit_first_print_slicer_queue(
        params=params,
        out_dir=args.out_dir,
        queue_dir=args.queue_dir,
    )

    print(f"slicer queue: {audit.queue_dir}")
    print(f"queue_manifest: {'ok' if audit.manifest_exists else 'missing'} {audit.manifest_path}")
    print(f"expected_printed_stls: {len(audit.expected_stl_paths)}")
    print(f"actual_printed_stls: {len(audit.actual_stl_paths)}")
    print(f"package_missing_required_artifacts: {len(audit.package_missing_paths)}")
    print(f"missing_queue_stls: {len(audit.missing_stl_paths)}")
    print(f"extra_queue_files: {len(audit.extra_paths)}")
    print(f"hash_mismatches: {len(audit.hash_mismatches)}")

    if audit.ready:
        print("ready: true")
        return

    if audit.package_missing_paths:
        print("package missing required artifacts:")
        for path in audit.package_missing_paths:
            print(f"- {path}")
    if audit.missing_stl_paths:
        print("missing queued STL files:")
        for path in audit.missing_stl_paths:
            print(f"- {path}")
    if audit.extra_paths:
        print("extra queue files:")
        for path in audit.extra_paths:
            print(f"- {path}")
    if audit.hash_mismatches:
        print("hash mismatches:")
        for mismatch in audit.hash_mismatches:
            print(
                f"- {mismatch.path}: expected {mismatch.expected_sha256}, "
                f"actual {mismatch.actual_sha256}"
            )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
