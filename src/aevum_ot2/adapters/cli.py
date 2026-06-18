from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, cast

import typer

from aevum_ot2.core.abort_recover import ot2_abort_or_recover
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.camera import capture_picture
from aevum_ot2.core.client import fetch_robot_status
from aevum_ot2.core.context import build_session_context
from aevum_ot2.core.discovery import DEFAULT_ROBOT_SERVICE_NAME, ROBOT_URL_ENV, resolve_robot
from aevum_ot2.core.evidence import (
    DEFAULT_EVIDENCE_TRANSACTION_ROOT,
    POSE_ORIENTATION_CLAIM_PREFIX,
    POSE_UPRIGHT_CLAIM,
    load_committed_evidence_claims,
)
from aevum_ot2.core.maintenance import (
    run_no_motion_comment_key_spike,
    run_no_motion_labware_definition_spike,
    run_no_motion_maintenance_lifecycle_spike,
)
from aevum_ot2.core.models import (
    BridgeSession,
    EvidenceClaim,
    EvidenceQuality,
    FixtureIdentity,
    VisionAnalysisResult,
)
from aevum_ot2.core.motion_approval import load_motion_approval
from aevum_ot2.core.plans import load_plan_fragment
from aevum_ot2.core.pose import FixtureOrientation, FixturePose, load_fixture_pose
from aevum_ot2.core.pose_evidence import (
    build_fixture_pose_evidence_artifact,
    commit_fixture_pose_evidence_artifact,
    write_fixture_pose_evidence_artifact,
)
from aevum_ot2.core.readiness import evaluate_registration_readiness
from aevum_ot2.core.records import (
    load_fixture_qc_record,
    load_target_class_record,
    scaffold_fixture_qc_record,
    scaffold_legacy_image_evidence_record,
    target_class_authority,
    validate_legacy_image_evidence_record,
    write_fixture_qc_record,
    write_legacy_image_evidence_record,
    write_target_class_record,
    write_target_class_scaffold,
)
from aevum_ot2.core.recovery import recover_no_motion_session
from aevum_ot2.core.registry import load_offset_registry
from aevum_ot2.core.safety import (
    build_fixture_safety_profile,
    load_fixture_safety_profile,
    write_fixture_safety_profile,
)
from aevum_ot2.core.sessions import (
    close_no_motion_session,
    initialize_no_motion_session,
    list_sessions,
    read_session,
)
from aevum_ot2.core.spike import run_read_only_api_spike
from aevum_ot2.core.target_evidence import (
    build_target_class_evidence_artifact,
    commit_target_class_claims,
    derive_target_class_claims,
    promoted_target_class_record,
    target_class_evidence_packets_from_artifact,
    write_target_class_evidence_artifact,
)
from aevum_ot2.core.vision import VisionPurpose, analyze_camera_image
from aevum_ot2.server.app import serve
from aevum_ot2.server.service import BridgeService

app = typer.Typer(help="Aevum OT-2 bridge utilities. Read-only by default.")
DEFAULT_LABWARE_OPTION = Path("outputs/labware/aevum_p300_poc_fixture.json")
DEFAULT_TARGET_SCAFFOLD_DIR = Path("data/measurements/target_classes")
DEFAULT_FIXTURE_QC_RECORD = Path("data/measurements/fixture_qc.json")
DEFAULT_LEGACY_IMAGE_EVIDENCE_DIR = Path("data/measurements/legacy_image_evidence")


@app.command("resolve")
def resolve(
    robot: str | None = typer.Option(
        None,
        envvar=ROBOT_URL_ENV,
        help="Robot server URL. If omitted, resolve the mDNS service name.",
    ),
    service_name: str = typer.Option(
        DEFAULT_ROBOT_SERVICE_NAME,
        help="mDNS service instance name to resolve when --robot is omitted.",
    ),
    timeout: float = typer.Option(5.0, help="mDNS discovery timeout in seconds."),
) -> None:
    result = resolve_robot(robot, service_name=service_name, timeout_seconds=timeout)
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2))


@app.command("status")
def status(
    robot: str | None = typer.Option(
        None,
        envvar=ROBOT_URL_ENV,
        help="Robot server URL. If omitted, resolve the mDNS service name.",
    ),
    service_name: str = typer.Option(
        DEFAULT_ROBOT_SERVICE_NAME,
        help="mDNS service instance name to resolve when --robot is omitted.",
    ),
    discovery_timeout: float = typer.Option(5.0, help="mDNS discovery timeout in seconds."),
    timeout: float = typer.Option(5.0, help="HTTP timeout in seconds."),
) -> None:
    discovery = resolve_robot(robot, service_name=service_name, timeout_seconds=discovery_timeout)
    result = fetch_robot_status(discovery.robot_url, timeout_seconds=timeout)
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2))


@app.command("fixture-check")
def fixture_check() -> None:
    identity = current_fixture_identity()
    typer.echo(json.dumps(identity.model_dump(mode="json"), indent=2))
    if not identity.dimensions_match:
        raise typer.Exit(code=1)


@app.command("api-spike-readonly")
def api_spike_readonly(
    robot: str | None = typer.Option(
        None,
        envvar=ROBOT_URL_ENV,
        help="Robot server URL. If omitted, resolve the mDNS service name.",
    ),
    service_name: str = typer.Option(
        DEFAULT_ROBOT_SERVICE_NAME,
        help="mDNS service instance name to resolve when --robot is omitted.",
    ),
    discovery_timeout: float = typer.Option(5.0, help="mDNS discovery timeout in seconds."),
    timeout: float = typer.Option(5.0, help="HTTP timeout in seconds."),
) -> None:
    discovery = resolve_robot(robot, service_name=service_name, timeout_seconds=discovery_timeout)
    report = run_read_only_api_spike(discovery.robot_url, timeout_seconds=timeout)
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))


@app.command("camera-capture")
def camera_capture(
    robot: str | None = typer.Option(
        None,
        envvar=ROBOT_URL_ENV,
        help="Robot server URL. If omitted, resolve the mDNS service name.",
    ),
    service_name: str = typer.Option(
        DEFAULT_ROBOT_SERVICE_NAME,
        help="mDNS service instance name to resolve when --robot is omitted.",
    ),
    discovery_timeout: float = typer.Option(5.0, help="mDNS discovery timeout in seconds."),
    filename: str | None = typer.Option(None, help="Optional JPG filename."),
    timeout: float = typer.Option(20.0, help="HTTP timeout in seconds."),
    session_id: str | None = typer.Option(
        None,
        help="Optional session ID; records the capture into that session evidence index.",
    ),
    output: Annotated[
        Path | None,
        typer.Option(help="Optional JSON output path for the capture result."),
    ] = None,
) -> None:
    session = _read_optional_session(session_id)
    robot_url = _session_robot_url_or_discovery(
        session,
        robot=robot,
        service_name=service_name,
        discovery_timeout=discovery_timeout,
    )
    result = capture_picture(
        robot_url,
        filename=filename,
        timeout_seconds=timeout,
        evidence_index_path=(
            session.evidence_index_path
            if session is not None
            else "data/measurements/ot2_evidence_index.json"
        ),
        session_id=session.session_id if session is not None else None,
    )
    if output is not None:
        _write_model_json(output, result)
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2))


@app.command("maintenance-spike-nomotion")
def maintenance_spike_nomotion(
    robot: str | None = typer.Option(
        None,
        envvar=ROBOT_URL_ENV,
        help="Robot server URL. If omitted, resolve the mDNS service name.",
    ),
    service_name: str = typer.Option(
        DEFAULT_ROBOT_SERVICE_NAME,
        help="mDNS service instance name to resolve when --robot is omitted.",
    ),
    discovery_timeout: float = typer.Option(5.0, help="mDNS discovery timeout in seconds."),
    timeout: float = typer.Option(10.0, help="HTTP timeout in seconds."),
) -> None:
    discovery = resolve_robot(robot, service_name=service_name, timeout_seconds=discovery_timeout)
    report = run_no_motion_maintenance_lifecycle_spike(
        discovery.robot_url,
        timeout_seconds=timeout,
    )
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))


@app.command("maintenance-comment-key-spike")
def maintenance_comment_key_spike(
    robot: str | None = typer.Option(
        None,
        envvar=ROBOT_URL_ENV,
        help="Robot server URL. If omitted, resolve the mDNS service name.",
    ),
    service_name: str = typer.Option(
        DEFAULT_ROBOT_SERVICE_NAME,
        help="mDNS service instance name to resolve when --robot is omitted.",
    ),
    discovery_timeout: float = typer.Option(5.0, help="mDNS discovery timeout in seconds."),
    timeout: float = typer.Option(10.0, help="HTTP timeout in seconds."),
    command_key: str | None = typer.Option(None, help="Optional command key to probe."),
) -> None:
    discovery = resolve_robot(robot, service_name=service_name, timeout_seconds=discovery_timeout)
    report = run_no_motion_comment_key_spike(
        discovery.robot_url,
        command_key=command_key,
        timeout_seconds=timeout,
    )
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))


@app.command("maintenance-labware-spike")
def maintenance_labware_spike(
    robot: str | None = typer.Option(
        None,
        envvar=ROBOT_URL_ENV,
        help="Robot server URL. If omitted, resolve the mDNS service name.",
    ),
    service_name: str = typer.Option(
        DEFAULT_ROBOT_SERVICE_NAME,
        help="mDNS service instance name to resolve when --robot is omitted.",
    ),
    discovery_timeout: float = typer.Option(5.0, help="mDNS discovery timeout in seconds."),
    timeout: float = typer.Option(10.0, help="HTTP timeout in seconds."),
    slot: str = typer.Option("1", help="Deck slot to use for the non-motion loadLabware probe."),
    labware_path: Annotated[
        Path,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Generated custom labware JSON.",
        ),
    ] = DEFAULT_LABWARE_OPTION,
) -> None:
    discovery = resolve_robot(robot, service_name=service_name, timeout_seconds=discovery_timeout)
    report = run_no_motion_labware_definition_spike(
        discovery.robot_url,
        slot=slot,
        labware_path=str(labware_path),
        timeout_seconds=timeout,
    )
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))


@app.command("session-init-nomotion")
def session_init_nomotion(
    robot: str | None = typer.Option(
        None,
        envvar=ROBOT_URL_ENV,
        help="Robot server URL. If omitted, resolve the mDNS service name.",
    ),
    service_name: str = typer.Option(
        DEFAULT_ROBOT_SERVICE_NAME,
        help="mDNS service instance name to resolve when --robot is omitted.",
    ),
    discovery_timeout: float = typer.Option(5.0, help="mDNS discovery timeout in seconds."),
    timeout: float = typer.Option(10.0, help="HTTP timeout in seconds."),
    owner: str = typer.Option("codex", help="Owner ID for the bridge lease."),
    kind: str = typer.Option("registration", help="Session kind."),
    lease_minutes: int = typer.Option(15, help="Lease duration in minutes."),
    slot: str = typer.Option("1", help="Deck slot to load the fixture into."),
    orientation: str = typer.Option(
        "canonical",
        help="Operator-proposed fixture orientation: canonical or rot180.",
    ),
    labware_path: Annotated[
        Path,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Generated custom labware JSON.",
        ),
    ] = DEFAULT_LABWARE_OPTION,
) -> None:
    discovery = resolve_robot(robot, service_name=service_name, timeout_seconds=discovery_timeout)
    report = initialize_no_motion_session(
        discovery.robot_url,
        owner_id=owner,
        kind=kind,
        slot=slot,
        orientation=orientation,
        labware_path=str(labware_path),
        lease_minutes=lease_minutes,
        timeout_seconds=timeout,
    )
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))


@app.command("session-show")
def session_show(session_id: str = typer.Argument(..., help="Local bridge session ID.")) -> None:
    session = read_session(session_id)
    if session is None:
        raise typer.BadParameter(f"session not found: {session_id}")
    typer.echo(json.dumps(session.model_dump(mode="json"), indent=2))


@app.command("session-list")
def session_list(
    robot: str | None = typer.Option(None, help="Filter by robot URL."),
    state: str | None = typer.Option(None, help="Filter by local session state."),
) -> None:
    sessions = list_sessions(robot_url=robot, state=state)
    typer.echo(json.dumps([session.model_dump(mode="json") for session in sessions], indent=2))


@app.command("readiness-check")
def readiness_check(
    session_id: str = typer.Argument(..., help="Local bridge session ID."),
    fixture_qc_record: Annotated[
        Path,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Fixture QC JSON record.",
        ),
    ] = ...,
    target_class_record: Annotated[
        list[Path] | None,
        typer.Option(
            "--target-class-record",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Target-class verification JSON record. Pass once per record.",
        ),
    ] = None,
    target_class_dir: Annotated[
        Path | None,
        typer.Option(
            "--target-class-dir",
            exists=True,
            file_okay=False,
            readable=True,
            help="Directory containing target-class verification JSON records.",
        ),
    ] = None,
) -> None:
    session = read_session(session_id)
    if session is None:
        raise typer.BadParameter(f"session not found: {session_id}")

    target_class_records = _target_class_record_paths(
        target_class_record,
        target_class_dir,
    )
    result = evaluate_registration_readiness(
        session,
        fixture_qc_record=fixture_qc_record,
        target_class_records=target_class_records,
    )
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2))
    if not result.registration_ready:
        raise typer.Exit(code=1)


@app.command("fixture-qc-scaffold")
def fixture_qc_scaffold(
    output: Annotated[
        Path,
        typer.Option(help="Fixture QC JSON record path."),
    ] = DEFAULT_FIXTURE_QC_RECORD,
    session_id: str | None = typer.Option(
        None,
        help="Optional session ID; binds fixture identity and pose digest to the session.",
    ),
    pose_digest_sha256: str = typer.Option(
        "",
        help="Optional explicit fixture pose digest for offline scaffolding.",
    ),
    x_bound_mm: float | None = typer.Option(None, help="Measured fixture X bound in mm."),
    y_bound_mm: float | None = typer.Option(None, help="Measured fixture Y bound in mm."),
    z_bound_mm: float | None = typer.Option(None, help="Measured fixture Z bound in mm."),
    tolerance_mm: float = typer.Option(1.0, help="Measurement tolerance in mm."),
    camera_capture_indexed: bool = typer.Option(False, help="Camera capture is indexed."),
    fixture_visible: bool = typer.Option(False, help="Fixture is visible in camera evidence."),
    vision_evidence_ok: bool = typer.Option(False, help="Vision evidence quality passed."),
    base_seated: bool = typer.Option(False, help="Fixture base is seated in the deck slot."),
    guide_holes_open: bool = typer.Option(False, help="Guide holes are visibly open."),
    support_debris_absent: bool = typer.Option(False, help="Support debris is absent."),
    mock_wells_undeformed: bool = typer.Option(False, help="Mock wells are undeformed."),
    warping_lift_absent: bool = typer.Option(
        False,
        "--warping-lift-absent/--warping-lift-present",
        help="No visible warping/lift.",
    ),
) -> None:
    identity, resolved_pose_digest = _fixture_qc_scope(
        session_id=session_id,
        pose_digest_sha256=pose_digest_sha256,
    )
    record = scaffold_fixture_qc_record(
        identity,
        pose_digest_sha256=resolved_pose_digest,
        x_bound_mm=x_bound_mm,
        y_bound_mm=y_bound_mm,
        z_bound_mm=z_bound_mm,
        tolerance_mm=tolerance_mm,
        camera_capture_indexed=camera_capture_indexed,
        fixture_visible=fixture_visible,
        vision_evidence_ok=vision_evidence_ok,
        base_seated=base_seated,
        guide_holes_open=guide_holes_open,
        support_debris_absent=support_debris_absent,
        mock_wells_undeformed=mock_wells_undeformed,
        no_warping_lift=warping_lift_absent,
    )
    handle = write_fixture_qc_record(record, output)
    typer.echo(
        json.dumps(
            {
                "handle": handle.model_dump(mode="json"),
                "record": record.model_dump(mode="json"),
            },
            indent=2,
        )
    )


def _fixture_qc_scope(
    *,
    session_id: str | None,
    pose_digest_sha256: str,
) -> tuple[FixtureIdentity, str]:
    explicit_pose_digest = pose_digest_sha256.strip()
    if explicit_pose_digest and len(explicit_pose_digest) != 64:
        raise typer.BadParameter("pose digest must be a 64-character sha256")
    if session_id is None:
        return current_fixture_identity(), explicit_pose_digest

    session = read_session(session_id)
    if session is None:
        raise typer.BadParameter(f"session not found: {session_id}")
    if not session.fixture_pose_digest_sha256:
        raise typer.BadParameter(f"session has no fixture pose digest: {session_id}")
    if (
        explicit_pose_digest
        and explicit_pose_digest != session.fixture_pose_digest_sha256
    ):
        raise typer.BadParameter("pose digest does not match session fixture pose digest")
    return session.fixture_identity, session.fixture_pose_digest_sha256


@app.command("target-scaffold")
def target_scaffold(
    session_id: str = typer.Argument(..., help="Local bridge session ID."),
    output_dir: Annotated[
        Path,
        typer.Option(
            help="Directory where target-class JSON scaffold records are written.",
        ),
    ] = DEFAULT_TARGET_SCAFFOLD_DIR,
    pipette_name: str = typer.Option("p300_single_gen2", help="Recorded pipette name."),
    pipette_mount: str = typer.Option("left", help="Recorded pipette mount."),
    tiprack_load_name: str = typer.Option(
        "opentrons_96_tiprack_300ul",
        help="Recorded tiprack load name.",
    ),
    offset_registry_record: str = typer.Option(
        "not-yet-registered",
        help="Offset registry record reference.",
    ),
) -> None:
    session = read_session(session_id)
    if session is None:
        raise typer.BadParameter(f"session not found: {session_id}")

    handles = write_target_class_scaffold(
        session,
        output_dir,
        pipette_name=pipette_name,
        pipette_mount=pipette_mount,
        tiprack_load_name=tiprack_load_name,
        offset_registry_record=offset_registry_record,
    )
    typer.echo(json.dumps([handle.model_dump(mode="json") for handle in handles], indent=2))


@app.command("session-context")
def session_context(
    session_id: str = typer.Argument(..., help="Local bridge session ID."),
    fixture_qc_record: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Optional fixture QC JSON record for local readiness context.",
        ),
    ] = None,
    target_class_record: Annotated[
        list[Path] | None,
        typer.Option(
            "--target-class-record",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Target-class verification JSON record. Pass once per record.",
        ),
    ] = None,
    target_class_dir: Annotated[
        Path | None,
        typer.Option(
            "--target-class-dir",
            exists=True,
            file_okay=False,
            readable=True,
            help="Directory containing target-class verification JSON records.",
        ),
    ] = None,
) -> None:
    session = read_session(session_id)
    if session is None:
        raise typer.BadParameter(f"session not found: {session_id}")

    readiness = None
    if fixture_qc_record is not None:
        readiness = evaluate_registration_readiness(
            session,
            fixture_qc_record=fixture_qc_record,
            target_class_records=_target_class_record_paths(
                target_class_record,
                target_class_dir,
            ),
        )

    context = build_session_context(session, readiness=readiness)
    typer.echo(json.dumps(context.model_dump(mode="json"), indent=2))


@app.command("safety-profile-build")
def safety_profile_build(
    session_id: str = typer.Argument(..., help="Local bridge session ID."),
    fixture_qc_record: Annotated[
        Path,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Pose-scoped fixture QC JSON record with measured bounds.",
        ),
    ] = ...,
    output: Annotated[
        Path | None,
        typer.Option(help="Fixture safety profile JSON output path."),
    ] = None,
    high_z_clearance_mm: float = typer.Option(
        20.0,
        help="Conservative high-Z clearance above the conservative fixture bound.",
    ),
    max_registration_jog_mm: float = typer.Option(
        0.5,
        help="Maximum registration jog distance allowed by the safety profile.",
    ),
) -> None:
    session = read_session(session_id)
    if session is None:
        raise typer.BadParameter(f"session not found: {session_id}")
    qc_record = load_fixture_qc_record(fixture_qc_record)
    pose, pose_claims = _session_pose_and_claims(session)
    result = build_fixture_safety_profile(
        session.fixture_identity,
        session=session,
        fixture_qc_record=qc_record,
        fixture_pose=pose,
        pose_claims=pose_claims,
        high_z_clearance_mm=high_z_clearance_mm,
        max_registration_jog_mm=max_registration_jog_mm,
    )
    profile_path = None
    if result.profile is not None:
        profile_path = output or _default_safety_profile_output(session)
        write_fixture_safety_profile(result.profile, profile_path)
    typer.echo(
        json.dumps(
            {
                "profile_path": str(profile_path) if profile_path is not None else None,
                "result": result.model_dump(mode="json"),
            },
            indent=2,
        )
    )
    if not result.passed:
        raise typer.Exit(code=1)


@app.command("plan-validate")
def plan_validate(
    session_id: str = typer.Argument(..., help="Local bridge session ID."),
    plan_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True, help="Plan JSON file."),
    ] = ...,
    fixture_qc_record: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Fixture QC JSON record for readiness context.",
        ),
    ] = None,
    target_class_record: Annotated[
        list[Path] | None,
        typer.Option(
            "--target-class-record",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Target-class verification JSON record. Pass once per record.",
        ),
    ] = None,
    target_class_dir: Annotated[
        Path | None,
        typer.Option(
            "--target-class-dir",
            exists=True,
            file_okay=False,
            readable=True,
            help="Directory containing target-class verification JSON records.",
        ),
    ] = None,
    safety_profile: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Fixture safety profile JSON for motion-boundary validation.",
        ),
    ] = None,
    fixture_pose: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Fixture pose JSON. Defaults to the session pose when available.",
        ),
    ] = None,
    offset_registry: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Offset registry JSON for low-Z or wet validation.",
        ),
    ] = None,
    recovery_disposition: str | None = typer.Option(
        None,
        help="Recovery disposition for home-clearance validation, e.g. not_started.",
    ),
    motion_approval: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Motion approval JSON for dispatch-boundary validation.",
        ),
    ] = None,
    motion_enabled: bool = typer.Option(
        False,
        "--motion-enabled/--motion-disabled",
        help="Enable motion-boundary validation only; this command never dispatches robot motion.",
    ),
) -> None:
    session = read_session(session_id)
    if session is None:
        raise typer.BadParameter(f"session not found: {session_id}")
    plan = load_plan_fragment(plan_path)
    pose, pose_claims = _session_pose_and_claims(session, fixture_pose_path=fixture_pose)
    target_class_records = _target_class_record_paths(
        target_class_record,
        target_class_dir,
    )
    service = BridgeService(motion_enabled=motion_enabled)
    result = service.validate_plan(
        session_id,
        plan,
        fixture_qc_record=fixture_qc_record,
        target_class_records=target_class_records,
        offset_registry=(
            load_offset_registry(offset_registry) if offset_registry is not None else None
        ),
        safety_profile=(
            load_fixture_safety_profile(safety_profile)
            if safety_profile is not None
            else None
        ),
        fixture_pose=pose,
        pose_claims=pose_claims,
        recovery_disposition=recovery_disposition,
        motion_approval=(
            load_motion_approval(motion_approval) if motion_approval is not None else None
        ),
    )
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2))
    if not result.allowed:
        raise typer.Exit(code=1)


@app.command("session-close-nomotion")
def session_close_nomotion(
    session_id: str = typer.Argument(..., help="Local bridge session ID."),
    timeout: float = typer.Option(10.0, help="HTTP timeout in seconds."),
) -> None:
    report = close_no_motion_session(session_id, timeout_seconds=timeout)
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))


@app.command("session-recover-nomotion")
def session_recover_nomotion(
    session_id: str = typer.Argument(..., help="Local bridge session ID."),
    timeout: float = typer.Option(10.0, help="HTTP timeout in seconds."),
) -> None:
    report = recover_no_motion_session(session_id, timeout_seconds=timeout)
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))


@app.command("session-abort-or-recover")
def session_abort_or_recover(
    session_id: str = typer.Argument(..., help="Local bridge session ID."),
    timeout: float = typer.Option(10.0, help="HTTP timeout in seconds."),
) -> None:
    """Project recover_no_motion_session into the agent abort/recover contract (OT-10).

    A facade over the proven recovery state machine: it never creates motion authority
    (motion_allowed is always derived, never True out of this path).
    """
    report = ot2_abort_or_recover(session_id, timeout_seconds=timeout)
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))


@app.command("camera-analyze")
def camera_analyze(
    image_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    purpose: Annotated[str, typer.Option(help="Camera observation purpose.")] = "deck_baseline",
) -> None:
    result = analyze_camera_image(image_path, purpose=_parse_vision_purpose(purpose))
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2))


@app.command("legacy-image-evidence-record")
def legacy_image_evidence_record(
    image_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    output: Annotated[
        Path | None,
        typer.Option(help="Legacy image-evidence JSON record path."),
    ] = None,
    session_id: str | None = typer.Option(
        None,
        help="Optional local bridge session ID to bind robot/fixture context.",
    ),
    purpose: Annotated[str, typer.Option(help="Camera evidence purpose.")] = "fixture_presence",
    target_class: str = typer.Option("", help="Target class for target image evidence."),
    human_observation: str = typer.Option("", help="Optional supervised commissioning note."),
    analyze: bool = typer.Option(
        False,
        "--analyze/--no-analyze",
        help="Run evidence-only image analysis before writing the record.",
    ),
    vision_result_path: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Existing vision-analysis JSON result to attach.",
        ),
    ] = None,
    vision_output: Annotated[
        Path | None,
        typer.Option(help="Vision-analysis JSON output path when --analyze is used."),
    ] = None,
) -> None:
    if analyze and vision_result_path is not None:
        raise typer.BadParameter("use either --analyze or --vision-result-path, not both")

    session = None
    if session_id is not None:
        session = read_session(session_id)
        if session is None:
            raise typer.BadParameter(f"session not found: {session_id}")

    parsed_purpose = _parse_vision_purpose(purpose)
    record_output = output or _default_legacy_image_evidence_output(
        image_path,
        parsed_purpose,
    )
    analysis = None
    attached_vision_path = vision_result_path
    if analyze:
        attached_vision_path = vision_output or _default_vision_output(record_output)
        analysis = analyze_camera_image(
            image_path,
            purpose=parsed_purpose,
            evidence_index_path=session.evidence_index_path if session is not None else None
            or "data/measurements/ot2_evidence_index.json",
        )
        _write_model_json(attached_vision_path, analysis)
    elif vision_result_path is not None:
        analysis = VisionAnalysisResult.model_validate_json(vision_result_path.read_text())
        if analysis.purpose != parsed_purpose:
            raise typer.BadParameter(
                f"vision result purpose {analysis.purpose} does not match {parsed_purpose}"
            )

    identity = session.fixture_identity if session is not None else current_fixture_identity()
    record = scaffold_legacy_image_evidence_record(
        identity,
        purpose=parsed_purpose,
        image_path=image_path,
        session=session,
        target_class=target_class,
        vision_result=analysis,
        vision_result_path=attached_vision_path,
        human_observation=human_observation,
    )
    handle = write_legacy_image_evidence_record(record, record_output)
    validation = validate_legacy_image_evidence_record(record)
    typer.echo(
        json.dumps(
            {
                "handle": handle.model_dump(mode="json"),
                "record": record.model_dump(mode="json"),
                "validation": validation.model_dump(mode="json"),
            },
            indent=2,
        )
    )


@app.command("pose-evidence-commit")
def pose_evidence_commit(
    session_id: Annotated[
        str,
        typer.Argument(help="Pose-scoped no-motion session ID."),
    ],
    image_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    observed_orientation: str = typer.Option(
        ...,
        help="Observed fixture orientation from the evidence: canonical or rot180.",
    ),
    fixture_upright: bool = typer.Option(
        False,
        "--fixture-upright/--fixture-not-upright",
        help="Inspection says the fixture is upright and seated in the expected Z sense.",
    ),
    inspection_note: str = typer.Option(
        "",
        help="Short inspection note linking the observation to visible/camera evidence.",
    ),
    vision_result_path: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Optional vision-analysis JSON tied to the image.",
        ),
    ] = None,
    quality: str = typer.Option(
        "ambiguous",
        help="Evidence quality: usable, ambiguous, or failed.",
    ),
    output: Annotated[
        Path | None,
        typer.Option(help="Fixture pose evidence artifact JSON output path."),
    ] = None,
    transaction_id: str | None = typer.Option(
        None,
        help="Optional evidence transaction ID.",
    ),
) -> None:
    session = read_session(session_id)
    if session is None:
        raise typer.BadParameter(f"session not found: {session_id}")
    if not session.fixture_pose_path:
        raise typer.BadParameter("session has no fixture pose path")
    pose = load_fixture_pose(session.fixture_pose_path)
    parsed_quality = _parse_evidence_quality(quality)
    artifact = build_fixture_pose_evidence_artifact(
        pose,
        session=session,
        artifact_id=f"{session.session_id}:fixture_pose_evidence:{datetime.now():%Y%m%d-%H%M%S}",
        image_path=image_path,
        observed_orientation=_parse_fixture_orientation(observed_orientation),
        fixture_upright=fixture_upright,
        inspection_note=inspection_note,
        vision_result_path=vision_result_path,
        quality=parsed_quality,
    )
    artifact_path = output or _default_pose_evidence_output(session)
    write_fixture_pose_evidence_artifact(artifact, artifact_path)
    commit = commit_fixture_pose_evidence_artifact(
        pose,
        artifact,
        session=session,
        artifact_path=artifact_path,
        transaction_id=transaction_id,
    )
    typer.echo(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                "artifact": artifact.model_dump(mode="json"),
                "transaction": commit.model_dump(mode="json"),
            },
            indent=2,
        )
    )


@app.command("target-evidence-commit")
def target_evidence_commit(
    session_id: Annotated[
        str,
        typer.Argument(help="Pose-scoped no-motion or motion-commissioning session ID."),
    ],
    target_record_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Target-class verification JSON record to promote.",
        ),
    ],
    image_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    inspection_note: str = typer.Option(
        "",
        help="Short inspection note linking the observation to target evidence.",
    ),
    vision_result_path: Annotated[
        Path | None,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Optional vision-analysis JSON tied to the image.",
        ),
    ] = None,
    quality: str = typer.Option(
        "ambiguous",
        help="Evidence quality: usable, ambiguous, or failed.",
    ),
    output: Annotated[
        Path | None,
        typer.Option(help="Target-class evidence artifact JSON output path."),
    ] = None,
    record_output: Annotated[
        Path | None,
        typer.Option(help="Promoted target-class record output path. Defaults to input."),
    ] = None,
    transaction_id: str | None = typer.Option(
        None,
        help="Optional evidence transaction ID.",
    ),
) -> None:
    session = read_session(session_id)
    if session is None:
        raise typer.BadParameter(f"session not found: {session_id}")
    record = load_target_class_record(target_record_path)
    pose, pose_claims = _session_pose_and_claims(session)
    parsed_quality = _parse_evidence_quality(quality)
    artifact = build_target_class_evidence_artifact(
        record,
        session=session,
        artifact_id=(
            f"{session.session_id}:target_class_evidence:"
            f"{record.target_class}:{datetime.now():%Y%m%d-%H%M%S}"
        ),
        image_path=image_path,
        inspection_note=inspection_note,
        vision_result_path=vision_result_path,
        quality=parsed_quality,
    )
    artifact_path = output or _default_target_evidence_output(session, record.target_class)
    write_target_class_evidence_artifact(artifact, artifact_path)
    packets = target_class_evidence_packets_from_artifact(
        record,
        artifact,
        session=session,
        artifact_path=artifact_path,
    )
    target_claims = derive_target_class_claims(record, packets, session=session)
    promoted = promoted_target_class_record(
        record,
        target_claims,
        pose_claims=_pose_authority_claims(pose_claims),
    )
    commit = commit_target_class_claims(
        record,
        packets,
        session=session,
        transaction_id=transaction_id,
    )
    authority = target_class_authority(promoted, session=session, fixture_pose=pose)
    if not authority.passed:
        typer.echo(
            json.dumps(
                {
                    "artifact_path": str(artifact_path),
                    "artifact": artifact.model_dump(mode="json"),
                    "target_claims": [
                        claim.model_dump(mode="json") for claim in target_claims
                    ],
                    "authority": authority.model_dump(mode="json"),
                    "transaction": commit.model_dump(mode="json"),
                },
                indent=2,
            )
        )
        raise typer.Exit(code=1)

    promoted_record_path = record_output or target_record_path
    handle = write_target_class_record(promoted, promoted_record_path)
    typer.echo(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                "record_path": str(promoted_record_path),
                "handle": handle.model_dump(mode="json"),
                "artifact": artifact.model_dump(mode="json"),
                "target_claims": [
                    claim.model_dump(mode="json") for claim in target_claims
                ],
                "authority": authority.model_dump(mode="json"),
                "transaction": commit.model_dump(mode="json"),
            },
            indent=2,
        )
    )


@app.command("camera-observe")
def camera_observe(
    robot: str | None = typer.Option(
        None,
        envvar=ROBOT_URL_ENV,
        help="Robot server URL. If omitted, resolve the mDNS service name.",
    ),
    service_name: str = typer.Option(
        DEFAULT_ROBOT_SERVICE_NAME,
        help="mDNS service instance name to resolve when --robot is omitted.",
    ),
    discovery_timeout: float = typer.Option(5.0, help="mDNS discovery timeout in seconds."),
    filename: str | None = typer.Option(None, help="Optional JPG filename."),
    timeout: float = typer.Option(20.0, help="HTTP timeout in seconds."),
    purpose: Annotated[str, typer.Option(help="Camera observation purpose.")] = "deck_baseline",
    session_id: str | None = typer.Option(
        None,
        help="Optional session ID; records capture and analysis into that session evidence index.",
    ),
    output: Annotated[
        Path | None,
        typer.Option(help="Optional JSON output path for the capture and analysis result."),
    ] = None,
) -> None:
    session = _read_optional_session(session_id)
    robot_url = _session_robot_url_or_discovery(
        session,
        robot=robot,
        service_name=service_name,
        discovery_timeout=discovery_timeout,
    )
    evidence_index_path = (
        session.evidence_index_path
        if session is not None
        else "data/measurements/ot2_evidence_index.json"
    )
    capture = capture_picture(
        robot_url,
        filename=filename,
        timeout_seconds=timeout,
        evidence_index_path=evidence_index_path,
        session_id=session.session_id if session is not None else None,
    )
    analysis = analyze_camera_image(
        capture.image_path,
        purpose=_parse_vision_purpose(purpose),
        evidence_index_path=evidence_index_path,
    )
    payload = {
        "capture": capture.model_dump(mode="json"),
        "analysis": analysis.model_dump(mode="json"),
    }
    if output is not None:
        _write_json(output, payload)
    typer.echo(json.dumps(payload, indent=2))


def _read_optional_session(session_id: str | None) -> BridgeSession | None:
    if session_id is None:
        return None
    session = read_session(session_id)
    if session is None:
        raise typer.BadParameter(f"session not found: {session_id}")
    return session


def _session_pose_and_claims(
    session: BridgeSession,
    *,
    fixture_pose_path: Path | None = None,
) -> tuple[FixturePose | None, list[EvidenceClaim]]:
    pose = None
    pose_source = fixture_pose_path or (
        Path(session.fixture_pose_path) if session.fixture_pose_path else None
    )
    if pose_source is not None:
        pose = load_fixture_pose(pose_source)

    claims: list[EvidenceClaim] = []
    if session.evidence_index_path:
        claims = load_committed_evidence_claims(
            index_path=session.evidence_index_path,
            root=DEFAULT_EVIDENCE_TRANSACTION_ROOT,
        )
    return pose, claims


def _pose_authority_claims(claims: list[EvidenceClaim]) -> list[EvidenceClaim]:
    return [
        claim
        for claim in claims
        if claim.claim_type == POSE_UPRIGHT_CLAIM
        or claim.claim_type.startswith(POSE_ORIENTATION_CLAIM_PREFIX)
    ]


def _target_class_record_paths(
    records: list[Path] | None,
    directory: Path | None,
) -> list[Path]:
    paths = list(records or [])
    if directory is not None:
        directory_paths = sorted(path for path in directory.glob("*.json") if path.is_file())
        if not directory_paths:
            raise typer.BadParameter(
                f"target-class directory contains no JSON records: {directory}"
            )
        paths.extend(directory_paths)

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        key = path.resolve()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return deduped


def _session_robot_url_or_discovery(
    session: BridgeSession | None,
    *,
    robot: str | None,
    service_name: str,
    discovery_timeout: float,
) -> str:
    if session is not None and robot is None:
        return session.robot_url
    discovery = resolve_robot(
        robot,
        service_name=service_name,
        timeout_seconds=discovery_timeout,
    )
    if session is not None and discovery.robot_url.rstrip("/") != session.robot_url.rstrip("/"):
        raise typer.BadParameter("session camera capture robot must match session robot_url")
    return discovery.robot_url


def _parse_vision_purpose(value: str) -> VisionPurpose:
    normalized = value.replace("-", "_")
    allowed = {"deck_baseline", "fixture_presence", "high_z_target", "recovery"}
    if normalized not in allowed:
        raise typer.BadParameter(f"expected one of: {', '.join(sorted(allowed))}")
    return cast(VisionPurpose, normalized)


def _parse_fixture_orientation(value: str) -> FixtureOrientation:
    normalized = value.replace("-", "_")
    try:
        return FixtureOrientation(normalized)
    except ValueError as exc:
        raise typer.BadParameter("expected one of: canonical, rot180") from exc


def _parse_evidence_quality(value: str) -> EvidenceQuality:
    normalized = value.replace("-", "_")
    try:
        return EvidenceQuality(normalized)
    except ValueError as exc:
        raise typer.BadParameter("expected one of: usable, ambiguous, failed") from exc


def _default_vision_output(output: Path) -> Path:
    return output.with_name(f"{output.stem}_vision.json")


def _default_legacy_image_evidence_output(image_path: Path, purpose: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    image_stem = image_path.stem.replace(" ", "_")
    purpose_stem = purpose.replace("-", "_")
    return DEFAULT_LEGACY_IMAGE_EVIDENCE_DIR / f"{timestamp}_{purpose_stem}_{image_stem}.json"


def _default_pose_evidence_output(session: BridgeSession) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    pose_dir = Path(session.fixture_pose_path).parent
    return pose_dir / f"{timestamp}_fixture_pose_evidence.json"


def _default_target_evidence_output(session: BridgeSession, target_class: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if session.fixture_pose_path:
        root = Path(session.fixture_pose_path).parent
    else:
        root = Path("data/measurements/sessions") / session.session_id
    return root / f"{timestamp}_{target_class}_target_evidence.json"


def _default_safety_profile_output(session: BridgeSession) -> Path:
    if session.fixture_pose_path:
        return Path(session.fixture_pose_path).parent / "fixture_safety_profile.json"
    return Path("data/measurements/safety_profiles") / f"{session.session_id}.json"


def _write_model_json(path: Path, model: object) -> None:
    if not hasattr(model, "model_dump_json"):
        raise TypeError("expected pydantic model")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2) + "\n")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


@app.command("daemon-serve")
def daemon_serve(
    host: str = typer.Option("127.0.0.1", help="Local daemon bind host."),
    port: int = typer.Option(8765, help="Local daemon bind port."),
    motion_enabled: bool = typer.Option(
        False,
        help="Enable future motion validation paths. Keep false during no-motion commissioning.",
    ),
    motion_backend_enabled: bool = typer.Option(
        False,
        help=(
            "Enable physical motion command dispatch after approval and fresh readbacks. "
            "Requires --motion-enabled."
        ),
    ),
    motion_backend_token: str | None = typer.Option(
        None,
        help=(
            "Required local HTTP auth token when --motion-backend-enabled is set. "
            "Sent by clients as X-Aevum-Bridge-Token."
        ),
        envvar="AEVUM_OT2_MOTION_BACKEND_TOKEN",
    ),
    allow_remote: bool = typer.Option(
        False,
        help="Allow binding the unauthenticated daemon to a non-loopback host.",
    ),
) -> None:
    serve(
        host=host,
        port=port,
        motion_enabled=motion_enabled,
        motion_backend_enabled=motion_backend_enabled,
        motion_backend_token=motion_backend_token,
        allow_remote=allow_remote,
    )


@app.command("mcp-serve")
def mcp_serve(
    daemon_url: str = typer.Option(
        "http://127.0.0.1:8765",
        help="Local Aevum OT-2 daemon base URL the MCP tools route through.",
    ),
) -> None:
    """Serve the policy-enforcing MCP agent adapter (allow-listed tools only, OT-7).

    The MCP SDK is optional and is NOT an install requirement; build_mcp_server
    lazy-imports it and raises a clear ImportError if absent.
    """
    # Lazy import so importing the CLI never requires the optional MCP SDK.
    from aevum_ot2.adapters.mcp import build_mcp_server

    try:
        server = build_mcp_server(daemon_url=daemon_url)
    except ImportError as exc:
        raise typer.BadParameter(str(exc)) from exc
    server.run()
