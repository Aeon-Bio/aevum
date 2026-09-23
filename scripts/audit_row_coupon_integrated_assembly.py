#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from aevum_cad.row_coupon.assembly_audit import audit_row_coupon_integrated_assembly


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the fail-closed Aevum integrated assembly audit"
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_row_coupon_integrated_assembly(args.root)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if report["overall_status"] == "GATE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
