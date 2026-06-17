from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from aevum_ot2.core.artifacts import DEFAULT_LABWARE, current_fixture_identity, load_json
from aevum_ot2.core.client import Ot2Client
from aevum_ot2.core.evidence import append_evidence_event
from aevum_ot2.core.lock import DEFAULT_STATE_DB, TERMINAL_LOCK_STATES, read_lock
from aevum_ot2.core.models import (
    EndpointResult,
    EvidenceEvent,
    MaintenanceCommandKeyReport,
    MaintenanceLabwareDefinitionReport,
    MaintenanceRunLifecycleReport,
)


def run_no_motion_maintenance_lifecycle_spike(
    robot_url: str,
    *,
    state_db_path: str | Path = DEFAULT_STATE_DB,
    timeout_seconds: float = 10.0,
) -> MaintenanceRunLifecycleReport:
    """Create and delete a maintenance run without enqueueing robot commands."""

    client = Ot2Client(robot_url, timeout_seconds=timeout_seconds)
    status = client.status()
    protocol_runs = client.get_json("/runs")
    report = MaintenanceRunLifecycleReport(
        robot_url=client.robot_url.rstrip("/"),
        status=status,
        protocol_runs=protocol_runs,
        notes=[
            "No maintenance-run commands are enqueued by this spike.",
            "Creating a maintenance run may clear an existing maintenance run on "
            "robot-server 9.0.0.",
        ],
    )

    if not _endpoint_ok(status.health):
        report.notes.append("Aborted before creating a maintenance run because /health failed.")
        return _record_report(report)
    if not _endpoint_ok(protocol_runs):
        report.notes.append("Aborted before creating a maintenance run because /runs failed.")
        return _record_report(report)
    if lock_blocker := _active_bridge_lock_blocker(report.robot_url, state_db_path):
        report.notes.append(lock_blocker)
        return _record_report(report)
    if _has_protocol_runs(protocol_runs):
        report.notes.append(
            "Aborted before creating a maintenance run because protocol runs were present."
        )
        return _record_report(report)

    report.create_result = client.post_json("/maintenance_runs")
    report.created_run_id = _extract_body_id(report.create_result)
    if not _endpoint_ok(report.create_result) or report.created_run_id is None:
        report.notes.append("Maintenance run creation failed or did not return a run ID.")
        return _record_report(report)

    run_path = f"/maintenance_runs/{report.created_run_id}"
    report.get_result = client.get_json(run_path)
    report.commands_result = client.get_json(f"{run_path}/commands")
    report.delete_result = client.delete_json(run_path)
    report.post_delete_get_result = client.get_json(run_path)

    if report.post_delete_get_result.status_code == 404:
        report.notes.append("Post-delete GET returned 404 as expected.")
    else:
        report.notes.append(
            "Post-delete GET did not return 404; inspect robot state before further work."
        )

    return _record_report(report)


def run_no_motion_comment_key_spike(
    robot_url: str,
    *,
    command_key: str | None = None,
    state_db_path: str | Path = DEFAULT_STATE_DB,
    timeout_seconds: float = 10.0,
) -> MaintenanceCommandKeyReport:
    """Probe maintenance-run command key behavior with comment commands only."""

    client = Ot2Client(robot_url, timeout_seconds=timeout_seconds)
    status = client.status()
    protocol_runs = client.get_json("/runs")
    key = command_key or f"aevum-comment-key-{datetime.now():%Y%m%d-%H%M%S}"
    report = MaintenanceCommandKeyReport(
        robot_url=client.robot_url.rstrip("/"),
        status=status,
        protocol_runs=protocol_runs,
        command_key=key,
        notes=[
            "Only comment commands are enqueued by this spike.",
            "No motion, homing, pipetting, labware, or hardware-control command is sent.",
        ],
    )

    if not _endpoint_ok(status.health):
        report.notes.append("Aborted before creating a maintenance run because /health failed.")
        return _record_key_report(report)
    if not _endpoint_ok(protocol_runs):
        report.notes.append("Aborted before creating a maintenance run because /runs failed.")
        return _record_key_report(report)
    if lock_blocker := _active_bridge_lock_blocker(report.robot_url, state_db_path):
        report.notes.append(lock_blocker)
        return _record_key_report(report)
    if _has_protocol_runs(protocol_runs):
        report.notes.append(
            "Aborted before creating a maintenance run because protocol runs were present."
        )
        return _record_key_report(report)

    report.create_result = client.post_json("/maintenance_runs")
    report.created_run_id = _extract_body_id(report.create_result)
    if not _endpoint_ok(report.create_result) or report.created_run_id is None:
        report.notes.append("Maintenance run creation failed or did not return a run ID.")
        return _record_key_report(report)

    run_path = f"/maintenance_runs/{report.created_run_id}"
    first_body = _comment_command_body(
        key=key,
        message="Aevum no-motion command-key spike: first comment.",
    )
    report.first_command_result = client.post_json(
        f"{run_path}/commands?waitUntilComplete=true&timeout=5000",
        first_body,
    )
    report.first_command_id = _extract_body_id(report.first_command_result)
    report.first_command_status = _extract_body_status(report.first_command_result)

    if report.first_command_id is not None:
        report.first_command_detail_result = client.get_json(
            f"{run_path}/commands/{report.first_command_id}"
        )
    report.commands_after_first_result = client.get_json(f"{run_path}/commands?pageLength=20")

    duplicate_body = _comment_command_body(
        key=key,
        message="Aevum no-motion command-key spike: duplicate-key comment.",
    )
    report.duplicate_key_result = client.post_json(
        f"{run_path}/commands?waitUntilComplete=true&timeout=5000",
        duplicate_body,
    )
    report.duplicate_command_id = _extract_body_id(report.duplicate_key_result)
    report.duplicate_command_status = _extract_body_status(report.duplicate_key_result)
    report.commands_after_duplicate_result = client.get_json(f"{run_path}/commands?pageLength=20")

    if report.duplicate_key_result.ok:
        report.notes.append(
            "Duplicate command key was accepted; treat keys as correlation labels, not "
            "idempotency guards."
        )
    else:
        report.notes.append(
            "Duplicate command key was rejected; inspect status/error before relying on "
            "key uniqueness."
        )

    report.delete_result = client.delete_json(run_path)
    report.post_delete_get_result = client.get_json(run_path)
    if report.post_delete_get_result.status_code == 404:
        report.notes.append("Post-delete GET returned 404 as expected.")

    return _record_key_report(report)


def run_no_motion_labware_definition_spike(
    robot_url: str,
    *,
    slot: str = "1",
    labware_path: str = str(DEFAULT_LABWARE),
    state_db_path: str | Path = DEFAULT_STATE_DB,
    timeout_seconds: float = 10.0,
) -> MaintenanceLabwareDefinitionReport:
    """Probe custom labware reference/upload behavior without sending motion commands."""

    client = Ot2Client(robot_url, timeout_seconds=timeout_seconds)
    status = client.status()
    protocol_runs = client.get_json("/runs")
    identity = current_fixture_identity(labware_path=labware_path)
    labware_definition = load_json(labware_path)
    load_key = f"aevum-load-labware-{datetime.now():%Y%m%d-%H%M%S}"
    report = MaintenanceLabwareDefinitionReport(
        robot_url=client.robot_url.rstrip("/"),
        status=status,
        protocol_runs=protocol_runs,
        artifact_identity=identity,
        slot=slot,
        load_key=load_key,
        notes=[
            "Only loadLabware and labware-definition upload commands/endpoints are used.",
            "No motion, homing, pipetting, or module command is sent.",
        ],
    )

    if not _endpoint_ok(status.health):
        report.notes.append("Aborted before creating a maintenance run because /health failed.")
        return _record_labware_report(report)
    if not _endpoint_ok(protocol_runs):
        report.notes.append("Aborted before creating a maintenance run because /runs failed.")
        return _record_labware_report(report)
    if lock_blocker := _active_bridge_lock_blocker(report.robot_url, state_db_path):
        report.notes.append(lock_blocker)
        return _record_labware_report(report)
    if _has_protocol_runs(protocol_runs):
        report.notes.append(
            "Aborted before creating a maintenance run because protocol runs were present."
        )
        return _record_labware_report(report)
    if not identity.dimensions_match:
        report.notes.append("Aborted because generated labware dimensions do not match params.")
        return _record_labware_report(report)

    _probe_load_by_reference_before_upload(client, report)
    _probe_upload_then_load(client, report, labware_definition)
    return _record_labware_report(report)


def _endpoint_ok(result: EndpointResult | None) -> bool:
    return result is not None and result.ok


def _extract_body_id(result: EndpointResult | None) -> str | None:
    if result is None or not isinstance(result.data, dict):
        return None
    data = result.data.get("data")
    if not isinstance(data, dict):
        return None
    run_id = data.get("id")
    return run_id if isinstance(run_id, str) else None


def _extract_body_status(result: EndpointResult | None) -> str | None:
    if result is None or not isinstance(result.data, dict):
        return None
    data = result.data.get("data")
    if not isinstance(data, dict):
        return None
    status = data.get("status")
    return status if isinstance(status, str) else None


def _extract_command_result_field(result: EndpointResult | None, field: str) -> str | None:
    if result is None or not isinstance(result.data, dict):
        return None
    data = result.data.get("data")
    if not isinstance(data, dict):
        return None
    command_result = data.get("result")
    if not isinstance(command_result, dict):
        return None
    value = command_result.get(field)
    return value if isinstance(value, str) else None


def _extract_definition_uri(result: EndpointResult | None) -> str | None:
    if result is None or not isinstance(result.data, dict):
        return None
    data = result.data.get("data")
    if not isinstance(data, dict):
        return None
    direct_uri = data.get("definitionUri")
    if isinstance(direct_uri, str):
        return direct_uri
    definitions = data.get("labwareDefinitions")
    if isinstance(definitions, list) and definitions:
        latest = definitions[-1]
        if isinstance(latest, dict):
            uri = latest.get("definitionUri")
            return uri if isinstance(uri, str) else None
    return None


def _has_protocol_runs(result: EndpointResult) -> bool:
    data = result.data
    if not isinstance(data, dict):
        return True
    runs = data.get("data")
    return not isinstance(runs, list) or bool(runs)


def _active_bridge_lock_blocker(robot_url: str, state_db_path: str | Path) -> str | None:
    try:
        lock = read_lock(robot_url.rstrip("/"), state_db_path)
    except (OSError, sqlite3.Error) as exc:
        return (
            "Aborted before creating a maintenance run because bridge lock state "
            f"is unreadable: {exc}"
        )
    if lock is None or lock.state in TERMINAL_LOCK_STATES:
        return None
    return (
        "Aborted before creating a maintenance run because bridge lock "
        f"{lock.session_id} is active in state {lock.state}."
    )


def _record_report(report: MaintenanceRunLifecycleReport) -> MaintenanceRunLifecycleReport:
    append_evidence_event(
        EvidenceEvent(
            event_type="ot2_maintenance_run_lifecycle_no_motion",
            summary="No-motion maintenance-run lifecycle spike",
            payload=report.model_dump(mode="json"),
        )
    )
    return report


def _record_key_report(report: MaintenanceCommandKeyReport) -> MaintenanceCommandKeyReport:
    append_evidence_event(
        EvidenceEvent(
            event_type="ot2_maintenance_comment_key_no_motion",
            summary="No-motion maintenance-run comment key spike",
            payload=report.model_dump(mode="json"),
        )
    )
    return report


def _record_labware_report(
    report: MaintenanceLabwareDefinitionReport,
) -> MaintenanceLabwareDefinitionReport:
    append_evidence_event(
        EvidenceEvent(
            event_type="ot2_maintenance_labware_definition_no_motion",
            summary="No-motion maintenance-run custom labware definition spike",
            payload=report.model_dump(mode="json"),
        )
    )
    return report


def _comment_command_body(*, key: str, message: str) -> dict[str, Any]:
    return {
        "data": {
            "commandType": "comment",
            "key": key,
            "params": {"message": message},
        }
    }


def _load_labware_command_body(
    *,
    key: str,
    slot: str,
    load_name: str,
    namespace: str,
    version: int,
    labware_id: str,
    display_name: str,
) -> dict[str, Any]:
    return {
        "data": {
            "commandType": "loadLabware",
            "key": key,
            "params": {
                "location": {"slotName": slot},
                "loadName": load_name,
                "namespace": namespace,
                "version": version,
                "labwareId": labware_id,
                "displayName": display_name,
            },
        }
    }


def _probe_load_by_reference_before_upload(
    client: Ot2Client,
    report: MaintenanceLabwareDefinitionReport,
) -> None:
    report.pre_upload_create_result = client.post_json("/maintenance_runs")
    report.pre_upload_run_id = _extract_body_id(report.pre_upload_create_result)
    if not _endpoint_ok(report.pre_upload_create_result) or report.pre_upload_run_id is None:
        report.notes.append("Could not create pre-upload maintenance run.")
        return

    run_path = f"/maintenance_runs/{report.pre_upload_run_id}"
    report.pre_upload_load_result = client.post_json(
        f"{run_path}/commands?waitUntilComplete=true&timeout=5000",
        _load_labware_command_body(
            key=f"{report.load_key}-pre",
            slot=report.slot,
            load_name=report.artifact_identity.load_name,
            namespace=report.artifact_identity.namespace,
            version=report.artifact_identity.version,
            labware_id="aevum-fixture-pre-upload",
            display_name="Aevum fixture pre-upload probe",
        ),
    )
    report.pre_upload_command_id = _extract_body_id(report.pre_upload_load_result)
    report.pre_upload_command_status = _extract_body_status(report.pre_upload_load_result)
    if report.pre_upload_command_status == "succeeded":
        report.notes.append("Custom labware loaded by reference before run-local upload.")
    else:
        report.notes.append("Custom labware did not load by reference before run-local upload.")
    report.pre_upload_delete_result = client.delete_json(run_path)


def _probe_upload_then_load(
    client: Ot2Client,
    report: MaintenanceLabwareDefinitionReport,
    labware_definition: dict[str, Any],
) -> None:
    report.upload_create_result = client.post_json("/maintenance_runs")
    report.upload_run_id = _extract_body_id(report.upload_create_result)
    if not _endpoint_ok(report.upload_create_result) or report.upload_run_id is None:
        report.notes.append("Could not create upload maintenance run.")
        return

    run_path = f"/maintenance_runs/{report.upload_run_id}"
    report.upload_definition_result = client.post_json(
        f"{run_path}/labware_definitions",
        {"data": labware_definition},
    )
    report.definition_uri = _extract_definition_uri(report.upload_definition_result)
    report.post_upload_load_result = client.post_json(
        f"{run_path}/commands?waitUntilComplete=true&timeout=5000",
        _load_labware_command_body(
            key=f"{report.load_key}-post",
            slot=report.slot,
            load_name=report.artifact_identity.load_name,
            namespace=report.artifact_identity.namespace,
            version=report.artifact_identity.version,
            labware_id="aevum-fixture-post-upload",
            display_name="Aevum fixture post-upload probe",
        ),
    )
    report.post_upload_command_id = _extract_body_id(report.post_upload_load_result)
    report.post_upload_command_status = _extract_body_status(report.post_upload_load_result)
    report.loaded_labware_id = _extract_command_result_field(
        report.post_upload_load_result,
        "labwareId",
    )
    report.upload_run_get_result = client.get_json(run_path)
    report.upload_run_commands_result = client.get_json(f"{run_path}/commands?pageLength=20")

    if report.post_upload_command_status == "succeeded":
        report.notes.append("Custom labware loaded successfully after run-local definition upload.")
    else:
        report.notes.append("Custom labware did not load successfully after definition upload.")

    report.upload_delete_result = client.delete_json(run_path)
    report.post_delete_get_result = client.get_json(run_path)
    if report.post_delete_get_result.status_code == 404:
        report.notes.append("Post-delete GET returned 404 as expected.")


def summarize_command_collection(result: EndpointResult | None) -> dict[str, Any]:
    if result is None or not isinstance(result.data, dict):
        return {"ok": False, "totalLength": None}
    meta = result.data.get("meta")
    total_length = meta.get("totalLength") if isinstance(meta, dict) else None
    commands = result.data.get("data")
    return {
        "ok": result.ok,
        "totalLength": total_length,
        "command_count": len(commands) if isinstance(commands, list) else None,
    }
