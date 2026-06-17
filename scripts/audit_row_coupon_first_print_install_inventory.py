from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT
from aevum_cad.row_coupon_first_print import (
    FIRST_PRINT_INSTALL_INVENTORY_RESULT_VALUES,
    audit_first_print_install_inventory,
)


def _default_worksheet_path() -> Path:
    today = datetime.now().date().isoformat()
    return ROOT / "data" / "measurements" / f"{today}_one_row_coupon_install_inventory.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--worksheet",
        default=_default_worksheet_path(),
        help="Install inventory worksheet CSV path to audit.",
    )
    parser.add_argument(
        "--require-install-ready",
        action="store_true",
        help="Exit nonzero unless every nonprinted item row is pass-ready.",
    )
    args = parser.parse_args()

    audit = audit_first_print_install_inventory(worksheet_path=args.worksheet)

    print(f"install_inventory: {audit.worksheet_path}")
    print(f"worksheet_valid: {'true' if audit.worksheet_valid else 'false'}")
    print(
        "install_inventory_ready: "
        f"{'true' if audit.install_inventory_ready else 'false'}"
    )
    print(
        "real_sensor_inventory_ready: "
        f"{'true' if audit.real_sensor_inventory_ready else 'false'}"
    )
    print(f"expected_rows: {audit.expected_row_count}")
    print(f"actual_rows: {audit.actual_row_count}")
    for result in sorted(FIRST_PRINT_INSTALL_INVENTORY_RESULT_VALUES):
        print(f"{result}_rows: {audit.result_counts.get(result, 0)}")
    print(f"missing_parts: {len(audit.missing_parts)}")
    print(f"extra_parts: {len(audit.extra_parts)}")
    print(f"duplicate_parts: {len(audit.duplicate_parts)}")
    print(f"sensor_inventory_blank_parts: {len(audit.sensor_inventory_blank_parts)}")
    for part in audit.sensor_inventory_blank_parts:
        print(f"sensor_inventory_blank_part: {part}")
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.part} | {issue.field} | {issue.message}")

    if not audit.worksheet_valid:
        raise SystemExit(1)
    if args.require_install_ready and not audit.install_inventory_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
