from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from aevum_ot2.core.models import BridgeSession, BridgeSessionState, RobotStatus
from aevum_ot2.core.readiness import ReadinessResult
from aevum_ot2.core.records import RecordHandle


class PipetteContext(BaseModel):
    mount: Literal["left", "right"]
    name: str | None = None
    model: str | None = None
    pipette_id: str | None = None
    tip_length: float | None = None


class RobotContext(BaseModel):
    robot_url: str
    robot_serial: str | None = None
    robot_server_version: str | None = None
    max_protocol_api_version: str | None = None
    pipettes: list[PipetteContext] = Field(default_factory=list)


class FixtureContext(BaseModel):
    load_name: str
    namespace: str
    version: int
    slot: str
    orientation: Literal["", "canonical", "rot180"] = ""
    pose_digest_sha256: str = ""
    pose_path: str = ""
    definition_uri: str | None = None
    loaded_labware_id: str | None = None
    params_sha256: str
    labware_definition_sha256: str
    dimensions_match: bool


class OperationBlock(BaseModel):
    operation: str
    reason: str
    severity: Literal["info", "warning", "blocker"] = "blocker"


class SessionContext(BaseModel):
    schema_version: int = 1
    session_id: str
    kind: str
    state: str
    owner_id: str
    lease_expires_at: str
    robot: RobotContext
    fixture: FixtureContext
    readiness: ReadinessResult | None = None
    record_handles: list[RecordHandle] = Field(default_factory=list)
    allowed_next_ops: list[str] = Field(default_factory=list)
    blocked_ops: list[OperationBlock] = Field(default_factory=list)
    evidence_index_path: str
    motion_allowed: bool = False
    notes: list[str] = Field(default_factory=list)


def build_session_context(
    session: BridgeSession,
    *,
    readiness: ReadinessResult | None = None,
    robot_status: RobotStatus | None = None,
    record_handles: list[RecordHandle] | None = None,
) -> SessionContext:
    """Build a compact local context pack for agents and operator/debug adapters."""

    handles = _dedupe_handles(_context_record_handles(readiness, record_handles or []))
    allowed_next_ops = _allowed_next_ops(session, readiness)
    blocked_ops = _blocked_ops(session, readiness)

    return SessionContext(
        session_id=session.session_id,
        kind=session.kind,
        state=session.state,
        owner_id=session.owner_id,
        lease_expires_at=session.lease_expires_at.isoformat(),
        robot=_robot_context(session, robot_status),
        fixture=_fixture_context(session),
        readiness=readiness,
        record_handles=handles,
        allowed_next_ops=allowed_next_ops,
        blocked_ops=blocked_ops,
        evidence_index_path=session.evidence_index_path,
        motion_allowed=False,
        notes=list(session.notes),
    )


def _robot_context(session: BridgeSession, robot_status: RobotStatus | None) -> RobotContext:
    live_pipettes = _pipette_contexts(robot_status)
    return RobotContext(
        robot_url=session.robot_url,
        robot_serial=session.robot_serial,
        robot_server_version=session.robot_server_version,
        max_protocol_api_version=session.max_protocol_api_version,
        pipettes=live_pipettes or _session_pipette_contexts(session),
    )


def _fixture_context(session: BridgeSession) -> FixtureContext:
    identity = session.fixture_identity
    return FixtureContext(
        load_name=identity.load_name,
        namespace=identity.namespace,
        version=identity.version,
        slot=session.slot,
        orientation=session.fixture_orientation,
        pose_digest_sha256=session.fixture_pose_digest_sha256,
        pose_path=session.fixture_pose_path,
        definition_uri=session.definition_uri,
        loaded_labware_id=session.loaded_labware_id,
        params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        dimensions_match=identity.dimensions_match,
    )


def _pipette_contexts(robot_status: RobotStatus | None) -> list[PipetteContext]:
    if robot_status is None or robot_status.pipettes is None:
        return []
    data = robot_status.pipettes.data
    if not isinstance(data, dict):
        return []
    nested = data.get("data")
    if isinstance(nested, dict):
        data = nested

    contexts: list[PipetteContext] = []
    for mount in ("left", "right"):
        pipette_data = data.get(mount)
        if not isinstance(pipette_data, dict) or not pipette_data:
            continue
        contexts.append(
            PipetteContext(
                mount=mount,
                name=_string_or_none(pipette_data.get("name")),
                model=_string_or_none(pipette_data.get("model")),
                pipette_id=_string_or_none(pipette_data.get("id")),
                tip_length=_float_or_none(pipette_data.get("tip_length")),
            )
        )
    return contexts


def _session_pipette_contexts(session: BridgeSession) -> list[PipetteContext]:
    if not session.pipette_mount:
        return []
    return [
        PipetteContext(
            mount="right" if session.pipette_mount == "right" else "left",
            name=session.pipette_name or None,
            model=session.pipette_model or None,
            pipette_id=session.pipette_id or None,
            tip_length=session.pipette_tip_length_mm,
        )
    ]


def _context_record_handles(
    readiness: ReadinessResult | None,
    extra_handles: list[RecordHandle],
) -> list[RecordHandle]:
    handles: list[RecordHandle] = []
    if readiness is not None:
        if readiness.fixture_qc_record is not None:
            handles.append(readiness.fixture_qc_record)
        handles.extend(readiness.target_class_records)
    handles.extend(extra_handles)
    return handles


def _dedupe_handles(handles: list[RecordHandle]) -> list[RecordHandle]:
    deduped: list[RecordHandle] = []
    seen: set[tuple[str, str, str]] = set()
    for handle in handles:
        key = (handle.record_type, handle.path, handle.record_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(handle)
    return deduped


def _allowed_next_ops(
    session: BridgeSession,
    readiness: ReadinessResult | None,
) -> list[str]:
    allowed = ["inspect_context"]
    if session.state != BridgeSessionState.CLOSED:
        allowed.append("close_session")
    if session.state == BridgeSessionState.READY_NO_MOTION:
        allowed.append("capture_evidence")
        if readiness is not None and readiness.registration_ready:
            allowed.append("prepare_registration_plan")
    return allowed


def _blocked_ops(
    session: BridgeSession,
    readiness: ReadinessResult | None,
) -> list[OperationBlock]:
    blocked = [
        OperationBlock(
            operation="record_evidence",
            reason="transaction-backed evidence record writes are not implemented",
        ),
        OperationBlock(
            operation="home",
            reason="motion-capable bridge daemon and plan validator are not implemented",
        ),
        OperationBlock(
            operation="move_high_z",
            reason="first motion requires an approved motion-commissioning session",
        ),
        OperationBlock(
            operation="move_low_z",
            reason="low-Z motion requires matching high-Z target evidence",
        ),
        OperationBlock(
            operation="liquid_handling",
            reason="wet workflows require completed dry target commissioning",
        ),
        OperationBlock(
            operation="set_offset",
            reason="offsets require bounded motion evidence and explicit registry writes",
        ),
    ]

    if session.state != BridgeSessionState.READY_NO_MOTION:
        blocked.append(
            OperationBlock(
                operation="prepare_registration_plan",
                reason=f"session state is {session.state}, not ready_no_motion",
            )
        )
    elif readiness is None:
        blocked.append(
            OperationBlock(
                operation="prepare_registration_plan",
                reason="readiness has not been evaluated against fixture and target records",
                severity="warning",
            )
        )
    elif not readiness.registration_ready:
        blocked.append(
            OperationBlock(
                operation="prepare_registration_plan",
                reason="registration readiness failed: " + "; ".join(readiness.reasons),
            )
        )
    return blocked


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None
