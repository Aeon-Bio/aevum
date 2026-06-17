from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    FIRST_PRINT_SERVICE_STATE_REVIEW_RESULT_VALUES,
    audit_first_print_service_state_review,
)


def _default_worksheet_path() -> Path:
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
        "--worksheet",
        default=_default_worksheet_path(),
        help="Service-state review worksheet CSV path to audit.",
    )
    parser.add_argument(
        "--require-service-state-review-ready",
        action="store_true",
        help="Exit nonzero unless every service-state review row is pass-ready.",
    )
    args = parser.parse_args()

    load_params(args.params)
    audit = audit_first_print_service_state_review(worksheet_path=args.worksheet)

    print(f"service_state_review_worksheet: {audit.worksheet_path}")
    print(f"worksheet_valid: {'true' if audit.worksheet_valid else 'false'}")
    print(
        "service_state_review_ready: "
        f"{'true' if audit.service_state_review_ready else 'false'}"
    )
    print(f"expected_rows: {audit.expected_row_count}")
    print(f"actual_rows: {audit.actual_row_count}")
    for result in sorted(FIRST_PRINT_SERVICE_STATE_REVIEW_RESULT_VALUES):
        print(f"{result}_rows: {audit.result_counts.get(result, 0)}")
    print(f"missing_modes: {len(audit.missing_modes)}")
    print(f"extra_modes: {len(audit.extra_modes)}")
    print(f"duplicate_modes: {len(audit.duplicate_modes)}")
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.mode} | {issue.field} | {issue.message}")

    if not audit.worksheet_valid:
        raise SystemExit(1)
    if args.require_service_state_review_ready and not audit.service_state_review_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
