from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from aevum_ot2.core.artifacts import DEFAULT_LABWARE, current_fixture_identity, load_json
from aevum_ot2.core.client import Ot2Client
from aevum_ot2.core.command_journal import (
    apply_and_persist_command_reconciliation_to_session,
    dispatch_journaled_command,
    new_command_journal_entry,
)
from aevum_ot2.core.evidence import (
    append_evidence_event,
    evidence_index_path_for_session,
)
from aevum_ot2.core.lock import (
    DEFAULT_STATE_DB,
    acquire_lock,
    lease_is_held,
    read_lock,
    write_lock,
)
from aevum_ot2.core.maintenance import (
    _endpoint_ok,
    _extract_body_id,
    _extract_body_status,
    _extract_command_result_field,
    _extract_definition_uri,
    _has_protocol_runs,
    _load_labware_command_body,
)
from aevum_ot2.core.models import (
    BridgeLock,
    BridgeSession,
    BridgeSessionKind,
    BridgeSessionState,
    EndpointResult,
    EvidenceEvent,
    NoMotionSessionCloseReport,
    NoMotionSessionInitReport,
    RobotStatus,
)
from aevum_ot2.core.plans import PlanStep
from aevum_ot2.core.pose import (
    FixtureOrientation,
    fixture_pose_from_labware_definition,
    fixture_pose_path_for_session,
    oriented_labware_definition,
    write_fixture_pose,
)
from aevum_ot2.core.schema import loads_json_object, parse_versioned_json_model

DEFAULT_SESSION_DB = DEFAULT_STATE_DB


def session_artifact_root_for_state_db(path: str | Path = DEFAULT_SESSION_DB) -> Path:
    return Path(path).parent / "sessions"


def initialize_session_db(path: str | Path = DEFAULT_SESSION_DB) -> Path:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bridge_sessions (
                session_id TEXT PRIMARY KEY,
                robot_url TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                state TEXT NOT NULL,
                maintenance_run_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bridge_sessions_robot_url
            ON bridge_sessions(robot_url)
            """
        )
    return db_path


def write_session(session: BridgeSession, path: str | Path = DEFAULT_SESSION_DB) -> None:
    db_path = initialize_session_db(path)
    with sqlite3.connect(db_path) as connection:
        write_session_in_transaction(connection, session)


def write_session_in_transaction(
    connection: sqlite3.Connection,
    session: BridgeSession,
) -> None:
    connection.execute(
        """
        INSERT INTO bridge_sessions (
            session_id, robot_url, owner_id, state, maintenance_run_id,
            created_at, updated_at, payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            robot_url = excluded.robot_url,
            owner_id = excluded.owner_id,
            state = excluded.state,
            maintenance_run_id = excluded.maintenance_run_id,
            updated_at = excluded.updated_at,
            payload_json = excluded.payload_json
        """,
        (
            session.session_id,
            session.robot_url,
            session.owner_id,
            session.state,
            session.maintenance_run_id,
            session.created_at.isoformat(),
            session.updated_at.isoformat(),
            session.model_dump_json(),
        ),
    )


def read_session(
    session_id: str,
    path: str | Path = DEFAULT_SESSION_DB,
) -> BridgeSession | None:
    db_path = initialize_session_db(path)
    with sqlite3.connect(db_path) as connection:
        return read_session_in_transaction(connection, session_id)


def read_session_in_transaction(
    connection: sqlite3.Connection,
    session_id: str,
) -> BridgeSession | None:
    row = connection.execute(
        "SELECT payload_json FROM bridge_sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        return None
    return _load_session_payload(row[0], source="bridge_sessions.payload_json")


def list_sessions(
    path: str | Path = DEFAULT_SESSION_DB,
    *,
    robot_url: str | None = None,
    state: str | None = None,
) -> list[BridgeSession]:
    db_path = initialize_session_db(path)
    query = "SELECT payload_json FROM bridge_sessions"
    params: list[str] = []
    predicates: list[str] = []
    if robot_url is not None:
        predicates.append("robot_url = ?")
        params.append(robot_url.rstrip("/"))
    if state is not None:
        predicates.append("state = ?")
        params.append(state)
    if predicates:
        query += " WHERE " + " AND ".join(predicates)
    query += " ORDER BY created_at DESC"

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(query, params).fetchall()
    return [
        _load_session_payload(row[0], source=f"{db_path}:bridge_sessions.payload_json")
        for row in rows
    ]


def _load_session_payload(payload_json: str, *, source: str) -> BridgeSession:
    data = loads_json_object(payload_json, schema_name="BridgeSession", path=source)
    return parse_versioned_json_model(
        data,
        BridgeSession,
        schema_name="BridgeSession",
        path=source,
    )


def initialize_no_motion_session(
    robot_url: str,
    *,
    owner_id: str,
    kind: str = "registration",
    slot: str = "1",
    orientation: str = "canonical",
    pipette_mount: str = "left",
    labware_path: str = str(DEFAULT_LABWARE),
    lease_minutes: int = 15,
    timeout_seconds: float = 10.0,
    state_db_path: str | Path = DEFAULT_SESSION_DB,
) -> NoMotionSessionInitReport:
    """Create a persisted bridge session with labware loaded, but no motion allowed."""

    try:
        fixture_orientation = FixtureOrientation(orientation)
    except ValueError:
        return _record_session_init(
            _preflight_aborted_session_init_report(
                robot_url,
                f"Aborted because fixture orientation is unsupported: {orientation}",
            )
        )

    client = Ot2Client(robot_url, timeout_seconds=timeout_seconds)
    status = client.status()
    protocol_runs = client.get_json("/runs")
    report = NoMotionSessionInitReport(
        robot_url=client.robot_url.rstrip("/"),
        status=status,
        protocol_runs=protocol_runs,
        notes=[
            "Session init is no-motion: maintenance run, definition upload, and loadLabware only.",
            "motion_allowed remains false.",
        ],
    )

    if not _endpoint_ok(status.health):
        report.notes.append("Aborted before lock acquisition because /health failed.")
        return _record_session_init(report)
    if not _endpoint_ok(protocol_runs):
        report.notes.append("Aborted before lock acquisition because /runs failed.")
        return _record_session_init(report)
    if _has_protocol_runs(protocol_runs):
        report.notes.append("Aborted because protocol runs were present.")
        return _record_session_init(report)

    identity = current_fixture_identity(labware_path=labware_path)
    if not identity.dimensions_match:
        report.notes.append("Aborted because generated labware dimensions do not match params.")
        return _record_session_init(report)
    canonical_labware_definition = load_json(labware_path)

    now = datetime.now()
    session_id = f"reg-{now:%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
    fixture_pose = fixture_pose_from_labware_definition(
        identity,
        slot=slot,
        orientation=fixture_orientation,
        canonical_labware_definition=canonical_labware_definition,
    )
    session_artifact_root = session_artifact_root_for_state_db(state_db_path)
    pose_path = fixture_pose_path_for_session(session_id, root=session_artifact_root)
    lease_expires_at = now + timedelta(minutes=lease_minutes)
    lock = BridgeLock(
        robot_url=report.robot_url,
        session_id=session_id,
        owner_id=owner_id,
        lease_started_at=now,
        lease_expires_at=lease_expires_at,
        state="starting",
    )
    acquired = acquire_lock(lock, state_db_path)
    if not acquired.acquired:
        report.lock = acquired.lock
        report.notes.append(
            "Aborted because an active or unreconciled bridge lock already exists."
        )
        return _record_session_init(report)
    report.lock = lock

    report.create_result = client.post_json("/maintenance_runs")
    maintenance_run_id = _extract_body_id(report.create_result)
    if not _endpoint_ok(report.create_result) or maintenance_run_id is None:
        report.notes.append("Maintenance run creation failed.")
        lock.state = "failed"
        write_lock(lock, state_db_path)
        report.lock = lock
        return _record_session_init(report)

    session = BridgeSession(
        session_id=session_id,
        kind=_normalize_kind(kind),
        owner_id=owner_id,
        robot_url=report.robot_url,
        robot_serial=_health_string(status, "robot_serial"),
        robot_server_version=_health_string(status, "api_version"),
        max_protocol_api_version=_max_protocol_api_version(status),
        **_session_pipette_fields(status, pipette_mount),
        state=BridgeSessionState.MAINTENANCE_RUN_CREATED,
        created_at=now,
        updated_at=datetime.now(),
        lease_expires_at=lease_expires_at,
        maintenance_run_id=maintenance_run_id,
        slot=slot,
        fixture_identity=identity,
        fixture_orientation=fixture_pose.orientation.value,
        fixture_pose_digest_sha256=fixture_pose.pose_digest_sha256,
        fixture_pose_path=str(pose_path),
        evidence_index_path=str(
            evidence_index_path_for_session(session_id, root=session_artifact_root)
        ),
    )
    try:
        write_session(session, state_db_path)
        write_fixture_pose(fixture_pose, pose_path)
        lock.active_run_id = maintenance_run_id
        lock.state = "active_no_motion"
        write_lock(lock, state_db_path)
    except (OSError, sqlite3.Error) as exc:
        return _fail_session_init(
            client,
            report,
            session,
            lock,
            state_db_path,
            f"Local session persistence failed after maintenance run creation: {exc}",
        )

    labware_definition = oriented_labware_definition(
        canonical_labware_definition,
        orientation=fixture_pose.orientation,
    )
    run_path = f"/maintenance_runs/{maintenance_run_id}"
    report.upload_definition_result = client.post_json(
        f"{run_path}/labware_definitions",
        {"data": labware_definition},
    )
    definition_uri = _extract_definition_uri(report.upload_definition_result)
    if not _endpoint_ok(report.upload_definition_result) or definition_uri is None:
        return _fail_session_init(
            client,
            report,
            session,
            lock,
            state_db_path,
            "Labware definition upload failed.",
        )

    command_key = f"aevum-session-load-{now:%Y%m%d-%H%M%S}"
    labware_id = f"{session_id}-fixture"
    load_labware_body = _load_labware_command_body(
        key=command_key,
        slot=slot,
        load_name=fixture_pose.oriented_labware_load_name,
        namespace=fixture_pose.oriented_labware_namespace,
        version=fixture_pose.oriented_labware_version,
        labware_id=labware_id,
        display_name=f"Aevum fixture {session_id}",
    )
    load_dispatch = dispatch_journaled_command(
        transport=client,
        entry=new_command_journal_entry(
            session=session,
            step=PlanStep(
                step_id="session-load-labware",
                operation="prepare_registration_plan",
            ),
            run_id=maintenance_run_id,
            command_body=load_labware_body,
            journal_id=f"{session_id}:loadLabware",
        ),
        command_path=f"{run_path}/commands?waitUntilComplete=true&timeout=5000",
        command_body=load_labware_body,
        journal_path=state_db_path,
        history_path=f"{run_path}/commands?pageLength=1000",
    )
    if not load_dispatch.journal_persisted:
        return _fail_session_init(
            client,
            report,
            session,
            lock,
            state_db_path,
            (
                "Command journal could not persist loadLabware after dispatch."
                if load_dispatch.posted
                else "Command journal could not persist loadLabware before dispatch."
            ),
            recovery_required=load_dispatch.posted,
        )
    report.load_labware_result = _compact_load_labware_result(
        load_dispatch.post_result
        or EndpointResult(path=f"{run_path}/commands", ok=False, error="missing command result")
    )
    if load_dispatch.reconciliation is not None and load_dispatch.reconciliation.recovery_required:
        session = apply_and_persist_command_reconciliation_to_session(
            session,
            load_dispatch.reconciliation,
            state_db_path,
        )
        return _fail_session_init(
            client,
            report,
            session,
            lock,
            state_db_path,
            "loadLabware command reconciliation requires recovery.",
            recovery_required=True,
        )
    command_id = _extract_body_id(report.load_labware_result)
    command_status = _extract_body_status(report.load_labware_result)
    loaded_labware_id = _extract_command_result_field(report.load_labware_result, "labwareId")
    if command_status != "succeeded" or loaded_labware_id is None:
        return _fail_session_init(
            client,
            report,
            session,
            lock,
            state_db_path,
            "loadLabware did not succeed.",
        )

    report.run_get_result = client.get_json(run_path)
    session.definition_uri = definition_uri
    session.loaded_labware_id = loaded_labware_id
    session.last_command_id = command_id
    session.last_command_key = command_key
    session.last_command_type = "loadLabware"
    session.last_command_status = command_status
    session.state = BridgeSessionState.READY_NO_MOTION
    session.updated_at = datetime.now()
    session.notes.append("Custom labware uploaded and loaded; motion remains blocked.")
    session.notes.append(
        "Fixture pose is operator-proposed; pose-orientation and upright claims "
        "are required before motion."
    )
    write_session(session, state_db_path)

    lock.last_command_id = command_id
    lock.state = "active_no_motion"
    write_lock(lock, state_db_path)
    report.session = session
    report.lock = lock
    report.notes.append("No-motion session state persisted.")
    return _record_session_init(report)


def close_no_motion_session(
    session_id: str,
    *,
    timeout_seconds: float = 10.0,
    state_db_path: str | Path = DEFAULT_SESSION_DB,
) -> NoMotionSessionCloseReport:
    session = read_session(session_id, state_db_path)
    report = NoMotionSessionCloseReport(
        session_id=session_id,
        session_before=session.model_copy(deep=True) if session else None,
        notes=["Session close deletes the maintenance run if one is recorded."],
    )
    if session is None:
        report.notes.append("No local session record found.")
        return _record_session_close(report)

    client = Ot2Client(session.robot_url, timeout_seconds=timeout_seconds)
    close_confirmed = (
        session.maintenance_run_id is None
        or session.state == BridgeSessionState.CLOSED
    )
    if (
        session.maintenance_run_id is not None
        and session.state != BridgeSessionState.CLOSED
    ):
        run_path = f"/maintenance_runs/{session.maintenance_run_id}"
        report.delete_result = client.delete_json(run_path)
        if report.delete_result.status_code == 404:
            close_confirmed = True
            report.notes.append("Maintenance run was already absent on the robot.")
        elif _endpoint_ok(report.delete_result):
            report.post_delete_get_result = client.get_json(run_path)
            close_confirmed = report.post_delete_get_result.status_code == 404
            if close_confirmed:
                report.notes.append("Post-delete GET returned 404 as expected.")
            else:
                report.notes.append("Could not confirm maintenance run deletion.")
        else:
            report.notes.append("Maintenance run deletion failed; local lock requires recovery.")

    now = datetime.now()
    if not close_confirmed:
        session.state = BridgeSessionState.CLOSE_FAILED
        session.motion_allowed = False
        session.updated_at = now
        session.notes.append("Close failed; active maintenance run must be recovered.")
        write_session(session, state_db_path)
        report.session_after = session

        lock = read_lock(session.robot_url, state_db_path)
        if lock is not None and lock.session_id == session.session_id:
            lock.state = "recovery_required"
            lock.active_run_id = session.maintenance_run_id
            lock.last_command_id = session.last_command_id
            write_lock(lock, state_db_path)
            report.lock = lock
        return _record_session_close(report)

    session.state = BridgeSessionState.CLOSED
    session.motion_allowed = False
    session.updated_at = now
    session.notes.append("Session closed and motion remains blocked.")
    write_session(session, state_db_path)
    report.session_after = session

    lock = read_lock(session.robot_url, state_db_path)
    if lock is not None and lock.session_id == session.session_id:
        lock.state = "closed"
        lock.active_run_id = None
        lock.last_command_id = session.last_command_id
        write_lock(lock, state_db_path)
        report.lock = lock

    return _record_session_close(report)


def _lock_blocks_session(lock: BridgeLock, now: datetime) -> bool:
    # A lock blocks a new session exactly while it still holds its lease (non-terminal,
    # unexpired). Same predicate the observer evidence path uses, so "valid lease" is one
    # thing across the bridge regardless of lease kind.
    return lease_is_held(lock, now)


def _preflight_aborted_session_init_report(
    robot_url: str,
    note: str,
) -> NoMotionSessionInitReport:
    normalized_robot_url = robot_url.rstrip("/")
    return NoMotionSessionInitReport(
        robot_url=normalized_robot_url,
        status=RobotStatus(
            robot_url=normalized_robot_url,
            checked_at=datetime.now(),
            health=EndpointResult(
                path="/health",
                ok=False,
                error="not checked because local preflight validation failed",
            ),
        ),
        protocol_runs=EndpointResult(
            path="/runs",
            ok=False,
            error="not checked because local preflight validation failed",
        ),
        notes=[
            "Session init is no-motion: maintenance run, definition upload, and loadLabware only.",
            "motion_allowed remains false.",
            note,
        ],
    )


def _normalize_kind(kind: str) -> BridgeSessionKind:
    try:
        return BridgeSessionKind(kind)
    except ValueError:
        return BridgeSessionKind.REGISTRATION


def _health_string(status: object, key: str) -> str | None:
    if not hasattr(status, "health"):
        return None
    health = status.health
    data = health.data if isinstance(health.data, dict) else {}
    value = data.get(key)
    return value if isinstance(value, str) else None


def _max_protocol_api_version(status: object) -> str | None:
    if not hasattr(status, "health"):
        return None
    health = status.health
    data = health.data if isinstance(health.data, dict) else {}
    value = data.get("maximum_protocol_api_version")
    if isinstance(value, list) and len(value) == 2:
        return f"{value[0]}.{value[1]}"
    return None


def _session_pipette_fields(status: object, mount: str) -> dict[str, object]:
    pipette = _pipette_data_for_mount(status, mount)
    if pipette is None:
        return {
            "pipette_mount": mount,
        }
    return {
        "pipette_mount": mount,
        "pipette_name": _string_or_empty(
            pipette.get("name"),
            pipette.get("pipetteName"),
            pipette.get("displayName"),
        ),
        "pipette_model": _string_or_empty(pipette.get("model")),
        "pipette_id": _string_or_empty(
            pipette.get("id"),
            pipette.get("pipetteId"),
            pipette.get("pipette_id"),
        ),
        "pipette_tip_length_mm": _float_or_none(
            pipette.get("tip_length"),
            pipette.get("tipLength"),
            pipette.get("tipLengthMm"),
        ),
    }


def _pipette_data_for_mount(status: object, mount: str) -> dict[str, object] | None:
    if not hasattr(status, "pipettes"):
        return None
    pipettes = status.pipettes
    if pipettes is None or not isinstance(pipettes.data, dict):
        return None
    data = pipettes.data.get("data")
    by_mount = data if isinstance(data, dict) else pipettes.data
    pipette = by_mount.get(mount)
    return pipette if isinstance(pipette, dict) and pipette else None


def _string_or_empty(*values: object) -> str:
    for value in values:
        if isinstance(value, str):
            return value
    return ""


def _float_or_none(*values: object) -> float | None:
    for value in values:
        if isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            return float(value)
    return None


def _fail_session_init(
    client: Ot2Client,
    report: NoMotionSessionInitReport,
    session: BridgeSession,
    lock: BridgeLock,
    state_db_path: str | Path,
    note: str,
    *,
    recovery_required: bool = False,
) -> NoMotionSessionInitReport:
    report.notes.append(note)
    delete_confirmed = session.maintenance_run_id is None
    if session.maintenance_run_id is not None:
        run_path = f"/maintenance_runs/{session.maintenance_run_id}"
        report.cleanup_delete_result = client.delete_json(run_path)
        if report.cleanup_delete_result.status_code == 404:
            delete_confirmed = True
        elif _endpoint_ok(report.cleanup_delete_result):
            report.cleanup_confirm_result = client.get_json(run_path)
            delete_confirmed = report.cleanup_confirm_result.status_code == 404
        else:
            delete_confirmed = False
    unresolved = recovery_required or not delete_confirmed
    session.state = (
        BridgeSessionState.RECOVERY_REQUIRED if unresolved else BridgeSessionState.FAILED
    )
    session.updated_at = datetime.now()
    session.motion_allowed = False
    if not unresolved:
        session.notes.append(note)
    elif delete_confirmed:
        session.notes.append(f"{note} Manual recovery is required.")
    else:
        session.notes.append(
            f"{note} Cleanup delete failed or was unconfirmed; recovery is required."
        )
    if report.cleanup_confirm_result is not None and not delete_confirmed:
        session.notes.append("Cleanup delete response did not confirm maintenance run removal.")
    lock.state = "recovery_required" if unresolved else "failed"
    lock.active_run_id = None if delete_confirmed else session.maintenance_run_id
    report.session = session
    report.lock = lock
    persistence_errors: list[str] = []
    try:
        write_session(session, state_db_path)
    except (OSError, sqlite3.Error) as exc:
        persistence_errors.append(f"session write failed during cleanup: {exc}")
    try:
        write_lock(lock, state_db_path)
    except (OSError, sqlite3.Error) as exc:
        persistence_errors.append(f"lock write failed during cleanup: {exc}")
    for error in persistence_errors:
        report.notes.append(error)
        session.notes.append(error)
    if persistence_errors:
        report.notes.append("Cleanup persistence failed after robot cleanup attempt.")
    return _record_session_init(report)


def _compact_load_labware_result(result: EndpointResult) -> EndpointResult:
    compacted = result.model_copy(deep=True)
    if not isinstance(compacted.data, dict):
        return compacted
    data = compacted.data.get("data")
    if not isinstance(data, dict):
        return compacted
    command_result = data.get("result")
    if not isinstance(command_result, dict):
        return compacted
    definition = command_result.get("definition")
    if isinstance(definition, dict):
        wells = definition.get("wells")
        parameters = definition.get("parameters")
        command_result["definition"] = {
            "namespace": definition.get("namespace"),
            "version": definition.get("version"),
            "loadName": parameters.get("loadName") if isinstance(parameters, dict) else None,
            "dimensions": definition.get("dimensions"),
            "well_count": len(wells) if isinstance(wells, dict) else None,
        }
    return compacted


def _record_session_init(report: NoMotionSessionInitReport) -> NoMotionSessionInitReport:
    event = EvidenceEvent(
        event_type="ot2_no_motion_session_init",
        session_id=report.session.session_id if report.session else None,
        summary="No-motion bridge session initialization",
        payload=report.model_dump(mode="json"),
    )
    if report.session is not None:
        append_evidence_event(event, path=report.session.evidence_index_path)
    else:
        append_evidence_event(event)
    return report


def _record_session_close(report: NoMotionSessionCloseReport) -> NoMotionSessionCloseReport:
    session_id = report.session_after.session_id if report.session_after else report.session_id
    session = report.session_after or report.session_before
    event = EvidenceEvent(
        event_type="ot2_no_motion_session_close",
        session_id=session_id,
        summary="No-motion bridge session close",
        payload=report.model_dump(mode="json"),
    )
    if session is not None:
        append_evidence_event(event, path=session.evidence_index_path)
    else:
        append_evidence_event(event)
    return report
