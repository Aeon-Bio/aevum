from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    FIRST_PRINT_GATE6_SENSOR_THERMAL_RESULT_VALUES,
    audit_first_print_gate6_sensor_thermal_worksheet,
)


def _default_worksheet_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_gate6_sensor_thermal.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "params",
        nargs="?",
        default=ROOT / "cad" / "one_row_coupon.params.json",
        help="Path to a one-row coupon params JSON file.",
    )
    parser.add_argument(
        "--worksheet",
        default=_default_worksheet_path(),
        help="Gate 6 sensor/thermal worksheet CSV path to audit.",
    )
    parser.add_argument(
        "--require-gate6-pass",
        action="store_true",
        help="Exit nonzero unless every Gate 6 sensor/thermal row is pass-ready.",
    )
    args = parser.parse_args()

    params = load_params(args.params)
    audit = audit_first_print_gate6_sensor_thermal_worksheet(
        params=params,
        worksheet_path=args.worksheet,
    )

    print(f"gate6_sensor_thermal_worksheet: {audit.worksheet_path}")
    print(f"worksheet_valid: {'true' if audit.worksheet_valid else 'false'}")
    print(f"gate6_pass_ready: {'true' if audit.gate6_pass_ready else 'false'}")
    print(f"expected_rows: {audit.expected_row_count}")
    print(f"actual_rows: {audit.actual_row_count}")
    for result in sorted(FIRST_PRINT_GATE6_SENSOR_THERMAL_RESULT_VALUES):
        print(f"{result}_rows: {audit.result_counts.get(result, 0)}")
    print(f"missing_targets: {len(audit.missing_targets)}")
    print(f"extra_targets: {len(audit.extra_targets)}")
    print(f"duplicate_targets: {len(audit.duplicate_targets)}")
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.target} | {issue.field} | {issue.message}")

    if not audit.worksheet_valid:
        raise SystemExit(1)
    if args.require_gate6_pass and not audit.gate6_pass_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
