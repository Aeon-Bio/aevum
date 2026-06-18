#!/usr/bin/env python3
"""Operator entry point for OT-2 motion commissioning.

This is a fail-closed OPERABILITY wrapper over the existing motion-capable
BridgeService. It creates NO motion authority of its own: it only sequences
``BridgeService`` calls and surfaces the bridge core's blockers.

DEFAULT BEHAVIOUR IS A DRY RUN. With no ``--confirm-arm`` (and/or no
``--motion-enabled``) the tool reports the transitions that *would* run and
arms nothing. Arming requires BOTH ``--confirm-arm`` AND ``--motion-enabled``;
executing the approved step requires a further explicit ``--confirm-execute``.

Examples
--------
Dry run preflight only (default, never arms)::

    python scripts/ot2_motion_commissioning.py SESSION_ID plan.json \\
        --safety-profile profile.json

Arm a bridge-minted approval (no motion dispatched yet)::

    python scripts/ot2_motion_commissioning.py SESSION_ID plan.json \\
        --safety-profile profile.json --motion-enabled --confirm-arm \\
        --approved-by alice

Arm and execute the approved step::

    python scripts/ot2_motion_commissioning.py SESSION_ID plan.json \\
        --safety-profile profile.json --motion-enabled --confirm-arm \\
        --confirm-execute --approved-by alice
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aevum_ot2.core.commissioning import (
    CommissioningReport,
    run_commissioning_preflight,
    run_commissioning_sequence,
)
from aevum_ot2.core.plans import load_plan_fragment
from aevum_ot2.core.safety import load_fixture_safety_profile
from aevum_ot2.server.service import BridgeService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail-closed OT-2 motion-commissioning operability wrapper. "
        "Dry-run by default; arms nothing without --confirm-arm AND --motion-enabled.",
    )
    parser.add_argument("session_id", help="Local bridge session ID.")
    parser.add_argument(
        "plan",
        type=Path,
        help="Plan JSON file with the single motion step to commission.",
    )
    parser.add_argument(
        "--state-db",
        type=Path,
        default=None,
        help="Bridge state DB path. Defaults to the bridge default.",
    )
    parser.add_argument(
        "--safety-profile",
        type=Path,
        default=None,
        help="Fixture safety profile JSON for motion-boundary validation.",
    )
    parser.add_argument(
        "--fixture-qc-record",
        type=Path,
        default=None,
        help="Fixture QC JSON record for readiness context.",
    )
    parser.add_argument(
        "--target-class-record",
        type=Path,
        action="append",
        default=None,
        help="Target-class verification JSON record. Pass once per record.",
    )
    parser.add_argument(
        "--approved-by",
        default="",
        help="Operator identity recorded on the bridge-minted motion approval.",
    )
    parser.add_argument(
        "--expires-in-seconds",
        type=int,
        default=300,
        help="Requested motion-approval TTL in seconds (bridge bounds the maximum).",
    )
    parser.add_argument(
        "--motion-enabled",
        action="store_true",
        help="Run the BridgeService with motion validation enabled. "
        "Required (with --confirm-arm) before anything can arm.",
    )
    parser.add_argument(
        "--confirm-arm",
        action="store_true",
        help="Explicitly confirm arming. Without this the tool stays a dry run.",
    )
    parser.add_argument(
        "--confirm-execute",
        action="store_true",
        help="Explicitly confirm executing the approved step after a successful arm.",
    )
    return parser


def _build_service(args: argparse.Namespace) -> BridgeService:
    if args.state_db is not None:
        return BridgeService(
            state_db_path=args.state_db,
            motion_enabled=args.motion_enabled,
        )
    return BridgeService(motion_enabled=args.motion_enabled)


def _run(args: argparse.Namespace) -> CommissioningReport:
    service = _build_service(args)
    plan = load_plan_fragment(args.plan)
    safety_profile = (
        load_fixture_safety_profile(args.safety_profile)
        if args.safety_profile is not None
        else None
    )
    target_class_records = (
        [str(path) for path in args.target_class_record]
        if args.target_class_record
        else None
    )
    fixture_qc_record = (
        str(args.fixture_qc_record) if args.fixture_qc_record is not None else None
    )

    # When the operator has not confirmed arming we never call the sequence's
    # arm path; a pure preflight keeps the run strictly read-only.
    if not args.confirm_arm:
        return run_commissioning_preflight(
            service,
            args.session_id,
            plan,
            safety_profile=safety_profile,
            fixture_qc_record=fixture_qc_record,
            target_class_records=target_class_records,
            confirm_arm=args.confirm_arm,
            confirm_execute=args.confirm_execute,
        )

    return run_commissioning_sequence(
        service,
        args.session_id,
        plan,
        approved_by=args.approved_by,
        safety_profile=safety_profile,
        fixture_qc_record=fixture_qc_record,
        target_class_records=target_class_records,
        confirm_arm=args.confirm_arm,
        motion_enabled=args.motion_enabled,
        confirm_execute=args.confirm_execute,
        expires_in_seconds=args.expires_in_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = _run(args)
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    # Fail-closed exit code: any blocker is a non-zero exit so operators and
    # CI gates treat an unarmed/unexecuted run as a stop.
    return 0 if not report.blockers else 1


if __name__ == "__main__":
    sys.exit(main())
