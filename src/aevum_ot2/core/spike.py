from __future__ import annotations

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.client import Ot2Client
from aevum_ot2.core.evidence import append_evidence_event
from aevum_ot2.core.models import ApiSpikeReport, EndpointResult, EvidenceEvent


def run_read_only_api_spike(robot_url: str, *, timeout_seconds: float = 5.0) -> ApiSpikeReport:
    client = Ot2Client(robot_url, timeout_seconds=timeout_seconds)
    status = client.status(include_openapi=True)
    identity = current_fixture_identity()

    notes: list[str] = []
    if status.openapi is not None and status.openapi.ok:
        notes.append("OpenAPI document was reachable.")
        openapi_text = status.openapi.text or ""
        openapi_json = status.openapi.data if isinstance(status.openapi.data, dict) else {}
        searchable = str(openapi_json) + openapi_text
        has_camera_capture = "capture_image" in searchable or "captureImage" in searchable
        if has_camera_capture:
            notes.append("OpenAPI content mentions a camera capture command.")
        else:
            notes.append(
                "OpenAPI content did not mention camera capture; "
                "protocol-run path may be required."
            )
        status.openapi = _compact_openapi_result(status.openapi, has_camera_capture)
    else:
        notes.append("OpenAPI document was not reachable.")

    if not identity.dimensions_match:
        notes.append("Generated labware dimensions do not match fixture parameters.")

    report = ApiSpikeReport(
        robot_url=robot_url,
        artifact_identity=identity,
        status=status,
        notes=notes,
    )
    append_evidence_event(
        EvidenceEvent(
            event_type="ot2_api_spike_read_only",
            summary=f"Read-only OT-2 API spike for {robot_url}",
            payload=report.model_dump(mode="json"),
        )
    )
    return report


def _compact_openapi_result(result: EndpointResult, has_camera_capture: bool) -> EndpointResult:
    if not isinstance(result.data, dict):
        return result

    paths = result.data.get("paths", {})
    components = result.data.get("components", {})
    result.data = {
        "openapi": result.data.get("openapi"),
        "info": result.data.get("info"),
        "path_count": len(paths) if isinstance(paths, dict) else None,
        "component_schema_count": len(components.get("schemas", {}))
        if isinstance(components, dict)
        else None,
        "has_camera_capture": has_camera_capture,
    }
    result.text = None
    return result
