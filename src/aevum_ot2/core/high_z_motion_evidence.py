from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, model_validator

from aevum_ot2.core.command_journal import (
    CommandJournalEntry,
    CommandReconciliationResult,
)
from aevum_ot2.core.evidence import (
    EvidenceTransactionCommitResult,
    commit_evidence_transaction,
    load_evidence_index,
)
from aevum_ot2.core.evidence_primitives import (
    _datetime_payload,
    _is_timezone_aware,
    _safe_path_segment,
    _same_path,
    _sha256_file,
    _transaction_root_for_index,
)
from aevum_ot2.core.models import (
    BridgeSession,
    BridgeSessionState,
    CameraCaptureResult,
    EvidenceClaim,
    EvidenceHandle,
    EvidencePacket,
    EvidenceQuality,
    EvidenceSourceKind,
    VisionAnalysisResult,
)
from aevum_ot2.core.records import (
    HIGH_Z_MOTION_EVIDENCE_METHOD,
    TARGET_CLASS_BY_NAME,
    HighZMotionRecord,
    HighZMotionResult,
    high_z_motion_completed_claim_id,
    high_z_motion_completed_claim_type,
)
from aevum_ot2.core.schema import (
    SchemaVersionError,
    load_json_object,
    parse_versioned_json_model,
)

HIGH_Z_MOTION_EVIDENCE_ARTIFACT_VERSION = 1
HIGH_Z_MOTION_SOURCE_KINDS = {EvidenceSourceKind.HIGH_Z_LANDING}
HIGH_Z_MOTION_SESSION_STATES = {
    BridgeSessionState.MOTION_COMMISSIONING_ARMED,
    BridgeSessionState.HIGH_Z_READY,
}

# The contract surface. `build_high_z_motion_evidence_artifact` is the ONLY safe producer —
# it binds command provenance and enforces post-motion ordering. The two low-level seams
# `high_z_motion_evidence_packet` and `derive_high_z_motion_claims` accept caller-built
# payloads and therefore BYPASS that binding; they exist for the commit path and tests and
# are intentionally NOT part of the public contract. A consumer (OT-1) must enter via
# `build_*` / `commit_*`, never hand-build a packet.
__all__ = [
    "HIGH_Z_MOTION_EVIDENCE_ARTIFACT_VERSION",
    "HIGH_Z_MOTION_SOURCE_KINDS",
    "HIGH_Z_MOTION_SESSION_STATES",
    "HighZMotionEvidenceArtifact",
    "build_high_z_motion_evidence_artifact",
    "write_high_z_motion_evidence_artifact",
    "load_high_z_motion_evidence_artifact",
    "high_z_motion_evidence_artifact_scope_reasons",
    "high_z_motion_evidence_packets_from_artifact",
    "commit_high_z_motion_claims",
    "commit_high_z_motion_evidence_artifact",
    "promoted_high_z_motion_record",
]


class HighZMotionEvidenceArtifact(BaseModel):
    schema_version: int = HIGH_Z_MOTION_EVIDENCE_ARTIFACT_VERSION
    artifact_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    session_id: str
    robot_serial: str = ""
    robot_server_version: str = ""
    fixture_load_name: str
    fixture_params_sha256: str
    labware_definition_sha256: str
    pose_digest_sha256: str = ""
    slot: str
    target_class: str
    commanded_high_z_mm: float
    command_id: str = ""
    command_key: str
    command_type: str
    command_operation: str = "move_high_z"
    command_status: str = ""
    command_history_reconciled: bool = False
    matched_command_is_latest: bool = False
    command_completed_at: datetime | None = None
    image_path: str
    image_checksum_sha256: str
    image_captured_at: datetime | None = None
    image_capture_robot_url: str = ""
    image_capture_endpoint: str = ""
    image_capture_checksum_sha256: str = ""
    vision_result_path: str = ""
    vision_result_checksum_sha256: str = ""
    inspection_note: str
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_artifact(self) -> HighZMotionEvidenceArtifact:
        if self.schema_version != HIGH_Z_MOTION_EVIDENCE_ARTIFACT_VERSION:
            raise ValueError("unsupported high-Z motion evidence artifact schema version")
        if not self.artifact_id.strip():
            raise ValueError("high-Z motion evidence artifact_id is required")
        if not self.session_id.strip():
            raise ValueError("high-Z motion evidence session_id is required")
        if self.target_class not in TARGET_CLASS_BY_NAME:
            raise ValueError(f"unknown target class: {self.target_class}")
        if _is_timezone_aware(self.created_at):
            raise ValueError("high-Z motion evidence created_at must be timezone-naive")
        if self.image_captured_at is not None and _is_timezone_aware(
            self.image_captured_at
        ):
            raise ValueError("high-Z motion evidence image_captured_at must be timezone-naive")
        if self.command_completed_at is not None and _is_timezone_aware(
            self.command_completed_at
        ):
            raise ValueError(
                "high-Z motion evidence command_completed_at must be timezone-naive"
            )
        if not math.isfinite(self.commanded_high_z_mm) or self.commanded_high_z_mm <= 0:
            raise ValueError("high-Z motion evidence commanded_high_z_mm must be finite and > 0")
        if not self.image_path.strip() or not self.image_checksum_sha256.strip():
            raise ValueError("high-Z motion evidence image path and checksum are required")
        if (
            self.image_capture_checksum_sha256
            and self.image_capture_checksum_sha256 != self.image_checksum_sha256
        ):
            raise ValueError("high-Z motion evidence image capture checksum mismatch")
        has_vision_path = bool(self.vision_result_path.strip())
        has_vision_checksum = bool(self.vision_result_checksum_sha256.strip())
        if has_vision_path != has_vision_checksum:
            raise ValueError(
                "high-Z motion evidence vision path and checksum must be provided together"
            )
        if self.quality == EvidenceQuality.USABLE:
            if not self.inspection_note.strip():
                raise ValueError("usable high-Z motion evidence requires an inspection note")
            if self.image_captured_at is None:
                raise ValueError("usable high-Z motion evidence requires image_captured_at")
            if not self.image_capture_robot_url.strip():
                raise ValueError("usable high-Z motion evidence requires image_capture_robot_url")
            if not self.image_capture_endpoint.strip():
                raise ValueError("usable high-Z motion evidence requires image_capture_endpoint")
            if not self.image_capture_checksum_sha256.strip():
                raise ValueError(
                    "usable high-Z motion evidence requires image_capture_checksum_sha256"
                )
            if not self.command_id.strip():
                raise ValueError("usable high-Z motion evidence requires command_id")
            if self.command_status != "succeeded":
                raise ValueError(
                    "usable high-Z motion evidence requires command_status succeeded"
                )
            if self.command_history_reconciled is not True:
                raise ValueError(
                    "usable high-Z motion evidence requires command_history_reconciled"
                )
            if self.matched_command_is_latest is not True:
                raise ValueError(
                    "usable high-Z motion evidence requires matched_command_is_latest"
                )
            if self.command_completed_at is None:
                raise ValueError(
                    "usable high-Z motion evidence requires command_completed_at"
                )
            if self.image_captured_at is not None and (
                self.image_captured_at < self.command_completed_at
            ):
                raise ValueError(
                    "usable high-Z motion evidence image_captured_at must be at or after "
                    "command_completed_at (the frame must be post-motion)"
                )
        return self


def build_high_z_motion_evidence_artifact(
    record: HighZMotionRecord,
    *,
    session: BridgeSession,
    artifact_id: str,
    image_path: str | Path,
    inspection_note: str,
    command_entry: CommandJournalEntry,
    reconciliation: CommandReconciliationResult | None,
    camera_capture: CameraCaptureResult | None = None,
    vision_result_path: str | Path | None = None,
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS,
    notes: list[str] | None = None,
) -> HighZMotionEvidenceArtifact:
    if command_entry.operation != "move_high_z":
        raise ValueError("high-Z motion evidence command entry operation must be move_high_z")
    # The executed command MUST belong to the active session/robot/run — a foreign-session or
    # foreign-robot command entry can never stand in as proof THIS session's move completed.
    if command_entry.session_id != session.session_id:
        raise ValueError(
            "high-Z motion evidence command entry session does not match the active session"
        )
    if command_entry.robot_url.rstrip("/") != session.robot_url.rstrip("/"):
        raise ValueError(
            "high-Z motion evidence command entry robot URL does not match the active session"
        )
    if session.maintenance_run_id and command_entry.run_id != session.maintenance_run_id:
        raise ValueError(
            "high-Z motion evidence command entry run does not match the session maintenance run"
        )
    # The reconciliation must be bound to THIS command entry — a reconciliation that matched a
    # different (benign) command cannot be borrowed to assert this move reconciled.
    if reconciliation is not None and reconciliation.matched_command_id is not None:
        if (
            command_entry.command_id is None
            or reconciliation.matched_command_id != command_entry.command_id
        ):
            raise ValueError(
                "high-Z motion evidence reconciliation matched a different command than the "
                "command entry"
            )
        if (
            reconciliation.entry is not None
            and reconciliation.entry.command_key != command_entry.command_key
        ):
            raise ValueError(
                "high-Z motion evidence reconciliation entry does not match the command entry"
            )
        if (
            reconciliation.matched_status is not None
            and command_entry.command_status is not None
            and reconciliation.matched_status != command_entry.command_status
        ):
            raise ValueError(
                "high-Z motion evidence reconciliation status does not match the command entry"
            )
    image = Path(image_path)
    vision = Path(vision_result_path) if vision_result_path is not None else None
    image_checksum = _sha256_file(image)
    resolved_capture = camera_capture or _matching_session_camera_capture(
        session,
        image,
        image_checksum,
    )
    if resolved_capture is not None:
        blockers = _camera_capture_scope_reasons(
            resolved_capture,
            image_path=image,
            image_checksum_sha256=image_checksum,
        )
        if blockers:
            raise ValueError("; ".join(blockers))
    identity = session.fixture_identity
    command_history_reconciled = (
        reconciliation is not None
        and reconciliation.matched_command_id is not None
        and reconciliation.matched_status == "succeeded"
        and reconciliation.matched_command_is_latest
    )
    matched_command_is_latest = (
        reconciliation.matched_command_is_latest if reconciliation is not None else False
    )
    # The move's completion instant, READ from the passed journal entry (not synthesized here);
    # the frame must be captured at or after it for the artifact to be post-motion evidence. Note
    # the entry's own authenticity is the bridge's/consuming gate's concern — OT-6 binds what it
    # is handed, it does not cryptographically attest the move happened.
    command_completed_at = command_entry.reconciled_at or command_entry.posted_at
    artifact = HighZMotionEvidenceArtifact(
        artifact_id=artifact_id,
        session_id=session.session_id,
        robot_serial=session.robot_serial or "",
        robot_server_version=session.robot_server_version or "",
        fixture_load_name=record.fixture_load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=record.labware_definition_sha256,
        pose_digest_sha256=record.pose_digest_sha256,
        slot=record.slot,
        target_class=record.target_class,
        commanded_high_z_mm=record.commanded_high_z_mm,
        command_id=command_entry.command_id or "",
        command_key=command_entry.command_key,
        command_type=command_entry.command_type,
        command_operation="move_high_z",
        command_status=command_entry.command_status or "",
        command_history_reconciled=command_history_reconciled,
        matched_command_is_latest=matched_command_is_latest,
        command_completed_at=command_completed_at,
        image_path=str(image),
        image_checksum_sha256=image_checksum,
        image_captured_at=(
            resolved_capture.captured_at if resolved_capture is not None else None
        ),
        image_capture_robot_url=(
            resolved_capture.robot_url if resolved_capture is not None else ""
        ),
        image_capture_endpoint=(
            resolved_capture.endpoint if resolved_capture is not None else ""
        ),
        image_capture_checksum_sha256=(
            resolved_capture.image_checksum_sha256 if resolved_capture is not None else ""
        ),
        vision_result_path=str(vision) if vision is not None else "",
        vision_result_checksum_sha256=_sha256_file(vision) if vision is not None else "",
        inspection_note=inspection_note,
        quality=quality,
        notes=notes or [],
    )
    # A USABLE artifact must be genuinely scope-valid at build time, not merely well-formed:
    # require the post-move frame to be indexed in the session and within the capture-time
    # window (incl. the post-motion command-completion floor). This prevents a misleading
    # USABLE stamp on disk that derive/packets would only later demote.
    if artifact.quality == EvidenceQuality.USABLE:
        build_blockers = [
            *_artifact_camera_event_reasons(artifact, session=session),
            *_artifact_capture_time_reasons(artifact, session=session),
        ]
        if build_blockers:
            raise ValueError("; ".join(build_blockers))
    return artifact


def write_high_z_motion_evidence_artifact(
    artifact: HighZMotionEvidenceArtifact,
    path: str | Path,
) -> Path:
    artifact_path = Path(path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = artifact_path.with_suffix(artifact_path.suffix + ".tmp")
    tmp.write_text(artifact.model_dump_json(indent=2) + "\n")
    tmp.replace(artifact_path)
    return artifact_path


def load_high_z_motion_evidence_artifact(
    path: str | Path,
) -> HighZMotionEvidenceArtifact:
    data = load_json_object(path, schema_name="HighZMotionEvidenceArtifact")
    return parse_versioned_json_model(
        data,
        HighZMotionEvidenceArtifact,
        schema_name="HighZMotionEvidenceArtifact",
        path=path,
    )


def high_z_motion_evidence_artifact_scope_reasons(
    record: HighZMotionRecord,
    *,
    session: BridgeSession,
    artifact_path: str | Path,
) -> list[str]:
    path = Path(artifact_path)
    try:
        artifact = load_high_z_motion_evidence_artifact(path)
    except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
        return [f"high-Z motion evidence artifact is invalid: {exc}"]
    return _artifact_scope_reasons(
        record,
        artifact,
        session=session,
        artifact_path=path,
    )


# The denormalized artifact fields carried in the packet payload, as ONE table that drives
# BOTH the build (payload construction) and the verify (_packet_artifact_scope_reasons). They
# must share this table: a field added to the build but forgotten in the verify is exactly the
# fail-OPEN drift this collapses — here a new entry is built and checked from the same row.
_PACKET_PAYLOAD_FIELDS: tuple[
    tuple[str, Callable[[HighZMotionEvidenceArtifact], object]], ...
] = (
    ("target_class", lambda a: a.target_class),
    ("pose_digest_sha256", lambda a: a.pose_digest_sha256),
    ("slot", lambda a: a.slot),
    ("commanded_high_z_mm", lambda a: a.commanded_high_z_mm),
    ("command_id", lambda a: a.command_id),
    ("command_key", lambda a: a.command_key),
    ("command_type", lambda a: a.command_type),
    ("command_operation", lambda a: a.command_operation),
    ("command_status", lambda a: a.command_status),
    ("command_history_reconciled", lambda a: a.command_history_reconciled),
    ("matched_command_is_latest", lambda a: a.matched_command_is_latest),
    ("command_completed_at", lambda a: _datetime_payload(a.command_completed_at)),
    ("image_path", lambda a: a.image_path),
    ("image_checksum_sha256", lambda a: a.image_checksum_sha256),
    ("image_captured_at", lambda a: _datetime_payload(a.image_captured_at)),
    ("image_capture_robot_url", lambda a: a.image_capture_robot_url),
    ("image_capture_endpoint", lambda a: a.image_capture_endpoint),
    ("image_capture_checksum_sha256", lambda a: a.image_capture_checksum_sha256),
    ("vision_result_path", lambda a: a.vision_result_path),
    ("vision_result_checksum_sha256", lambda a: a.vision_result_checksum_sha256),
)


def _artifact_payload(artifact: HighZMotionEvidenceArtifact) -> dict[str, object]:
    payload: dict[str, object] = {
        key: getter(artifact) for key, getter in _PACKET_PAYLOAD_FIELDS
    }
    payload["value"] = True
    return payload


def high_z_motion_evidence_packets_from_artifact(
    record: HighZMotionRecord,
    artifact: HighZMotionEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: str | Path,
) -> list[EvidencePacket]:
    path = Path(artifact_path)
    blockers = _artifact_scope_reasons(
        record,
        artifact,
        session=session,
        artifact_path=path,
    )
    if blockers:
        raise ValueError("; ".join(blockers))
    checksum = _sha256_file(path)
    return [
        high_z_motion_evidence_packet(
            record,
            session=session,
            evidence_id=f"{artifact.artifact_id}:high_z_motion",
            source_kind=EvidenceSourceKind.HIGH_Z_LANDING,
            artifact_path=path,
            checksum_sha256=checksum,
            quality=artifact.quality,
            payload=_artifact_payload(artifact),
            notes=artifact.notes,
        )
    ]


def high_z_motion_evidence_packet(
    record: HighZMotionRecord,
    *,
    session: BridgeSession | None = None,
    evidence_id: str,
    source_kind: EvidenceSourceKind = EvidenceSourceKind.HIGH_Z_LANDING,
    artifact_path: str | Path = "",
    checksum_sha256: str = "",
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS,
    payload: dict[str, object] | None = None,
    notes: list[str] | None = None,
) -> EvidencePacket:
    """LOW-LEVEL seam — accepts a caller-built payload and BYPASSES command-provenance binding.

    Not part of the public contract (`__all__`). Producers must go through
    ``high_z_motion_evidence_packets_from_artifact`` (which derives the payload from a
    provenance-bound artifact); a packet hand-built here whose payload lies is still
    demoted at derive time, but the safe entry point is the artifact path.
    """
    if source_kind not in HIGH_Z_MOTION_SOURCE_KINDS:
        raise ValueError(f"unsupported high-Z motion evidence source: {source_kind}")
    active_payload: dict[str, object] = {
        "target_class": record.target_class,
        "pose_digest_sha256": record.pose_digest_sha256,
    }
    active_payload.update(payload or {})
    command_id = active_payload.get("command_id")
    return EvidencePacket(
        evidence_id=evidence_id,
        source_kind=source_kind,
        session_id=session.session_id if session is not None else "",
        robot_serial=(session.robot_serial or "") if session is not None else "",
        robot_server_version=(
            (session.robot_server_version or "") if session is not None else ""
        ),
        fixture_load_name=record.fixture_load_name,
        fixture_params_sha256=record.fixture_params_sha256,
        labware_definition_sha256=record.labware_definition_sha256,
        pose_digest_sha256=record.pose_digest_sha256,
        operation="move_high_z",
        command_id=command_id if isinstance(command_id, str) else "",
        artifact_path=str(Path(artifact_path)) if artifact_path else "",
        checksum_sha256=checksum_sha256,
        payload=active_payload,
        quality=quality,
        notes=notes or [],
    )


def derive_high_z_motion_claims(
    record: HighZMotionRecord,
    evidence_packets: Iterable[EvidencePacket],
    *,
    session: BridgeSession | None = None,
    method: str = HIGH_Z_MOTION_EVIDENCE_METHOD,
) -> list[EvidenceClaim]:
    packets = list(evidence_packets)
    motion_packet = _first_high_z_motion_packet(packets)
    if motion_packet is None:
        return []
    reasons = _high_z_motion_packet_reasons(record, motion_packet, session)
    quality = motion_packet.quality if not reasons else EvidenceQuality.FAILED
    return [
        EvidenceClaim(
            claim_id=high_z_motion_completed_claim_id(
                record.target_class,
                motion_packet.evidence_id,
            ),
            claim_type=high_z_motion_completed_claim_type(record.target_class),
            value=not reasons,
            created_at=datetime.now(),
            session_id=(
                session.session_id if session is not None else motion_packet.session_id
            ),
            fixture_load_name=record.fixture_load_name,
            fixture_params_sha256=record.fixture_params_sha256,
            labware_definition_sha256=record.labware_definition_sha256,
            pose_digest_sha256=record.pose_digest_sha256,
            method=method,
            quality=quality,
            evidence=[_evidence_handle(motion_packet)],
            reasons=reasons,
        )
    ]


def commit_high_z_motion_claims(
    record: HighZMotionRecord,
    evidence_packets: list[EvidencePacket],
    *,
    session: BridgeSession,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    transaction_id: str | None = None,
) -> EvidenceTransactionCommitResult:
    resolved_index_path = Path(index_path or session.evidence_index_path)
    _require_session_evidence_index(session, resolved_index_path)
    resolved_root = Path(root) if root is not None else _transaction_root_for_index(
        resolved_index_path
    )
    claims = derive_high_z_motion_claims(record, evidence_packets, session=session)
    return commit_evidence_transaction(
        packets=evidence_packets,
        claims=claims,
        index_path=resolved_index_path,
        root=resolved_root,
        transaction_id=transaction_id,
        session_id=session.session_id,
    )


def commit_high_z_motion_evidence_artifact(
    record: HighZMotionRecord,
    artifact: HighZMotionEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: str | Path,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    transaction_id: str | None = None,
) -> EvidenceTransactionCommitResult:
    return commit_high_z_motion_claims(
        record,
        high_z_motion_evidence_packets_from_artifact(
            record,
            artifact,
            session=session,
            artifact_path=artifact_path,
        ),
        session=session,
        index_path=index_path,
        root=root,
        transaction_id=transaction_id,
    )


def promoted_high_z_motion_record(
    record: HighZMotionRecord,
    claims: list[EvidenceClaim],
) -> HighZMotionRecord:
    claim_type = high_z_motion_completed_claim_type(record.target_class)
    usable_claims = [
        claim
        for claim in claims
        if claim.claim_type == claim_type
        and claim.value is True
        # derive's invariant is value == (not reasons); reject a self-contradictory claim
        and not claim.reasons
        and claim.quality == EvidenceQuality.USABLE
        and claim.method == HIGH_Z_MOTION_EVIDENCE_METHOD
        and not _promote_claim_scope_blockers(record, claim)
    ]
    if not usable_claims:
        raise ValueError(f"missing usable high-Z motion claim: {claim_type}")
    evidence = _dedupe_evidence_handles(
        [handle for claim in usable_claims for handle in claim.evidence]
    )
    return record.model_copy(
        update={
            "result": HighZMotionResult.PASSED,
            "evidence": evidence,
            "claims": usable_claims,
        }
    )


def _promote_claim_scope_blockers(
    record: HighZMotionRecord,
    claim: EvidenceClaim,
) -> list[str]:
    """Re-validate a claim's scope against the record before promotion.

    ``promoted_high_z_motion_record`` is the TERMINAL trust boundary for OT-6 until a
    consuming high-Z gate exists (OT-1 / a follow-on gate). The target-class path can lean on
    its downstream ``target_class_authority`` gate; OT-6 has no analog yet, so promotion must
    re-check the claim's identity rather than trust a caller-supplied USABLE claim. This is
    not a motion gate and consults only the record + the claim (the committed-store and
    live-journal re-validation remain the consuming gate's responsibility).
    """
    blockers: list[str] = []
    if claim.fixture_load_name != record.fixture_load_name:
        blockers.append("claim fixture does not match motion record")
    if claim.fixture_params_sha256 != record.fixture_params_sha256:
        blockers.append("claim fixture params checksum does not match motion record")
    if claim.labware_definition_sha256 != record.labware_definition_sha256:
        blockers.append("claim labware checksum does not match motion record")
    if claim.pose_digest_sha256 != record.pose_digest_sha256:
        blockers.append("claim pose digest does not match motion record")
    if len(claim.evidence) != 1:
        blockers.append("claim must reference exactly one evidence handle")
        return blockers
    handle = claim.evidence[0]
    if handle.source_kind != EvidenceSourceKind.HIGH_Z_LANDING:
        blockers.append("claim evidence handle is not a high-Z landing source")
    if claim.claim_id != high_z_motion_completed_claim_id(
        record.target_class, handle.evidence_id
    ):
        blockers.append("claim id is not bound to its evidence handle")
    return blockers


def _high_z_motion_packet_reasons(
    record: HighZMotionRecord,
    packet: EvidencePacket,
    session: BridgeSession | None,
) -> list[str]:
    reasons = _packet_scope_reasons(record, packet, session)
    if packet.payload.get("target_class") != record.target_class:
        reasons.append("high-Z motion evidence target_class does not match motion record")
    if packet.payload.get("value") is not True:
        reasons.append("high-Z motion evidence did not assert a true observation")
    if packet.payload.get("command_status") != "succeeded":
        reasons.append("high-Z motion evidence command status is not succeeded")
    if packet.payload.get("command_history_reconciled") is not True:
        reasons.append("high-Z motion evidence command history is not reconciled")
    if packet.payload.get("matched_command_is_latest") is not True:
        reasons.append("high-Z motion evidence command is not the latest command")
    if not str(packet.payload.get("command_id", "")).strip():
        reasons.append("high-Z motion evidence command_id is missing")
    return reasons


def _packet_scope_reasons(
    record: HighZMotionRecord,
    packet: EvidencePacket,
    session: BridgeSession | None,
) -> list[str]:
    reasons: list[str] = []
    if packet.quality != EvidenceQuality.USABLE:
        reasons.append(f"evidence packet is not usable: {packet.evidence_id}")
    elif not _usable_artifact_is_bound(packet):
        reasons.append(
            "usable high-Z motion evidence packet must bind an artifact path and checksum"
        )
    elif session is None:
        reasons.append("usable high-Z motion evidence packet requires an active session")
    else:
        reasons.extend(_packet_artifact_scope_reasons(record, packet, session=session))
    if session is not None:
        if packet.session_id != session.session_id:
            reasons.append("evidence packet session does not match active session")
        if packet.robot_serial and packet.robot_serial != (session.robot_serial or ""):
            reasons.append("evidence packet robot does not match active session")
        if (
            packet.robot_server_version
            and packet.robot_server_version != (session.robot_server_version or "")
        ):
            reasons.append("evidence packet robot-server version does not match session")
    if packet.fixture_load_name != record.fixture_load_name:
        reasons.append("evidence packet fixture does not match motion record")
    if packet.fixture_params_sha256 != record.fixture_params_sha256:
        reasons.append("evidence packet fixture params checksum does not match motion record")
    if packet.labware_definition_sha256 != record.labware_definition_sha256:
        reasons.append("evidence packet labware checksum does not match motion record")
    if packet.pose_digest_sha256 != record.pose_digest_sha256:
        reasons.append("evidence packet pose digest does not match motion record")
    if packet.payload.get("pose_digest_sha256") != record.pose_digest_sha256:
        reasons.append("evidence payload pose digest does not match motion record")
    return reasons


def _packet_artifact_scope_reasons(
    record: HighZMotionRecord,
    packet: EvidencePacket,
    *,
    session: BridgeSession,
) -> list[str]:
    try:
        artifact = load_high_z_motion_evidence_artifact(packet.artifact_path)
    except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
        return [f"usable high-Z motion evidence packet artifact is invalid: {exc}"]

    reasons = _artifact_scope_reasons(
        record,
        artifact,
        session=session,
        artifact_path=Path(packet.artifact_path),
    )
    if artifact.quality != packet.quality:
        reasons.append("high-Z motion evidence artifact quality does not match packet")
    # Verify every denormalized payload field against the artifact from the SAME table that
    # built them — a forgotten field can no longer silently stop being checked (fail-closed).
    for key, getter in _PACKET_PAYLOAD_FIELDS:
        if packet.payload.get(key) != getter(artifact):
            reasons.append(f"high-Z motion evidence packet field {key} does not match artifact")
    # The packet's top-level command_id (not a payload field) must also match the artifact.
    if packet.command_id != artifact.command_id:
        reasons.append("high-Z motion evidence packet command provenance does not match artifact")
    return reasons


def _artifact_scope_reasons(
    record: HighZMotionRecord,
    artifact: HighZMotionEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: Path,
) -> list[str]:
    reasons: list[str] = []
    if not artifact_path.is_file():
        reasons.append(f"high-Z motion evidence artifact is missing: {artifact_path}")
    else:
        try:
            loaded = load_high_z_motion_evidence_artifact(artifact_path)
        except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
            reasons.append(f"high-Z motion evidence artifact cannot be loaded: {exc}")
        else:
            if loaded.model_dump(mode="json") != artifact.model_dump(mode="json"):
                reasons.append("high-Z motion evidence artifact does not match artifact path")

    identity = session.fixture_identity
    if session.state not in HIGH_Z_MOTION_SESSION_STATES:
        reasons.append(f"high-Z motion evidence session state is {session.state}")
    if session.lease_expires_at <= datetime.now():
        reasons.append("high-Z motion evidence session lease is expired")
    if artifact.session_id != session.session_id:
        reasons.append("high-Z motion evidence session does not match active session")
    if artifact.robot_serial != (session.robot_serial or ""):
        reasons.append("high-Z motion evidence robot does not match active session")
    if artifact.robot_server_version != (session.robot_server_version or ""):
        reasons.append("high-Z motion evidence robot-server version does not match session")
    if artifact.image_capture_robot_url != session.robot_url.rstrip("/"):
        reasons.append("high-Z motion evidence image capture robot URL does not match session")
    if artifact.fixture_load_name != record.fixture_load_name:
        reasons.append("high-Z motion evidence fixture does not match motion record")
    if artifact.fixture_params_sha256 != identity.params_sha256:
        reasons.append("high-Z motion evidence fixture params checksum does not match session")
    if artifact.labware_definition_sha256 != record.labware_definition_sha256:
        reasons.append("high-Z motion evidence labware checksum does not match motion record")
    if artifact.pose_digest_sha256 != record.pose_digest_sha256:
        reasons.append("high-Z motion evidence pose digest does not match motion record")
    if artifact.slot != record.slot:
        reasons.append("high-Z motion evidence slot does not match motion record")
    if artifact.target_class != record.target_class:
        reasons.append("high-Z motion evidence target does not match motion record")
    if artifact.commanded_high_z_mm != record.commanded_high_z_mm:
        reasons.append("high-Z motion evidence commanded high Z does not match motion record")
    if artifact.command_operation != "move_high_z":
        reasons.append("high-Z motion evidence command operation is not move_high_z")
    if record.command_id and artifact.command_id != record.command_id:
        reasons.append("high-Z motion evidence command ID does not match motion record")
    reasons.extend(_artifact_capture_time_reasons(artifact, session=session))
    if artifact.quality == EvidenceQuality.USABLE:
        reasons.extend(_artifact_camera_event_reasons(artifact, session=session))
        if artifact.command_status != "succeeded":
            reasons.append("usable high-Z motion evidence command status is not succeeded")
        if artifact.command_history_reconciled is not True:
            reasons.append("usable high-Z motion evidence command history is not reconciled")
        if artifact.matched_command_is_latest is not True:
            reasons.append("usable high-Z motion evidence command is not the latest command")
        if not artifact.command_id.strip():
            reasons.append("usable high-Z motion evidence command_id is missing")
    reasons.extend(
        _file_checksum_reasons(
            path=artifact.image_path,
            checksum_sha256=artifact.image_checksum_sha256,
            label="high-Z motion evidence image",
        )
    )
    if artifact.vision_result_path or artifact.vision_result_checksum_sha256:
        reasons.extend(
            _file_checksum_reasons(
                path=artifact.vision_result_path,
                checksum_sha256=artifact.vision_result_checksum_sha256,
                label="high-Z motion evidence vision result",
            )
        )
        reasons.extend(_vision_result_scope_reasons(artifact))
    return reasons


def _vision_result_scope_reasons(
    artifact: HighZMotionEvidenceArtifact,
) -> list[str]:
    path = Path(artifact.vision_result_path)
    try:
        result = VisionAnalysisResult.model_validate_json(path.read_text())
    except (ValidationError, OSError, ValueError) as exc:
        return [f"high-Z motion evidence vision result is invalid: {exc}"]
    reasons: list[str] = []
    if result.purpose != "high_z_target":
        reasons.append("high-Z motion evidence vision result purpose is not high_z_target")
    if result.evidence_ok is not True:
        reasons.append("high-Z motion evidence vision result evidence_ok is not true")
    if not _same_path(result.image_path, artifact.image_path):
        reasons.append("high-Z motion evidence vision result image does not match artifact")
    if result.analyzed_at > datetime.now():
        reasons.append("high-Z motion evidence vision result is from the future")
    return reasons


def _artifact_capture_time_reasons(
    artifact: HighZMotionEvidenceArtifact,
    *,
    session: BridgeSession,
) -> list[str]:
    if artifact.image_captured_at is None:
        return ["high-Z motion evidence image capture time is required"]
    reasons: list[str] = []
    if (
        artifact.command_completed_at is not None
        and artifact.image_captured_at < artifact.command_completed_at
    ):
        reasons.append(
            "high-Z motion evidence image capture predates the executed high-Z command "
            "(not post-motion)"
        )
    if artifact.image_captured_at < session.updated_at:
        reasons.append("high-Z motion evidence image capture predates active session authority")
    if artifact.image_captured_at >= session.lease_expires_at:
        reasons.append("high-Z motion evidence image capture is outside the session lease")
    if artifact.image_captured_at > datetime.now():
        reasons.append("high-Z motion evidence image capture is from the future")
    return reasons


def _artifact_camera_event_reasons(
    artifact: HighZMotionEvidenceArtifact,
    *,
    session: BridgeSession,
) -> list[str]:
    for capture in _session_camera_captures(session):
        if _capture_matches_artifact(capture, artifact):
            return []
    return ["high-Z motion evidence image capture is not indexed in the active session"]


def _first_high_z_motion_packet(packets: list[EvidencePacket]) -> EvidencePacket | None:
    matching = [
        packet for packet in packets if packet.source_kind in HIGH_Z_MOTION_SOURCE_KINDS
    ]
    if not matching:
        return None
    return sorted(matching, key=lambda packet: packet.created_at, reverse=True)[0]


def _matching_session_camera_capture(
    session: BridgeSession,
    image_path: Path,
    image_checksum_sha256: str,
) -> CameraCaptureResult | None:
    matching = [
        capture
        for capture in _session_camera_captures(session)
        if _capture_matches_image(
            capture,
            image_path=image_path,
            image_checksum_sha256=image_checksum_sha256,
        )
    ]
    if not matching:
        return None
    return sorted(matching, key=lambda capture: capture.captured_at, reverse=True)[0]


def _session_camera_captures(session: BridgeSession) -> list[CameraCaptureResult]:
    try:
        index = load_evidence_index(session.evidence_index_path)
    except (OSError, SchemaVersionError, ValueError, ValidationError):
        return []
    captures: list[CameraCaptureResult] = []
    for event in index.events:
        if event.event_type != "ot2_camera_picture":
            continue
        if event.session_id != session.session_id:
            continue
        try:
            captures.append(CameraCaptureResult.model_validate(event.payload))
        except ValidationError:
            continue
    return captures


def _camera_capture_scope_reasons(
    capture: CameraCaptureResult,
    *,
    image_path: Path,
    image_checksum_sha256: str,
) -> list[str]:
    reasons: list[str] = []
    if not _same_path(capture.image_path, image_path):
        reasons.append("camera capture image path does not match high-Z motion image")
    if capture.image_checksum_sha256 != image_checksum_sha256:
        reasons.append("camera capture checksum does not match high-Z motion image")
    try:
        if Path(capture.image_path).stat().st_size != capture.bytes_written:
            reasons.append("camera capture byte count does not match high-Z motion image")
    except OSError:
        reasons.append("camera capture image is missing")
    return reasons


def _capture_matches_artifact(
    capture: CameraCaptureResult,
    artifact: HighZMotionEvidenceArtifact,
) -> bool:
    return (
        _capture_matches_image(
            capture,
            image_path=Path(artifact.image_path),
            image_checksum_sha256=artifact.image_checksum_sha256,
        )
        and capture.captured_at == artifact.image_captured_at
        and capture.robot_url == artifact.image_capture_robot_url
        and capture.endpoint == artifact.image_capture_endpoint
        and capture.image_checksum_sha256 == artifact.image_capture_checksum_sha256
    )


def _capture_matches_image(
    capture: CameraCaptureResult,
    *,
    image_path: Path,
    image_checksum_sha256: str,
) -> bool:
    return (
        _same_path(capture.image_path, image_path)
        and bool(capture.image_checksum_sha256)
        and capture.image_checksum_sha256 == image_checksum_sha256
    )


def _usable_artifact_is_bound(packet: EvidencePacket) -> bool:
    if not packet.artifact_path or not packet.checksum_sha256:
        return False
    path = Path(packet.artifact_path)
    if not path.is_file():
        return False
    return _sha256_file(path) == packet.checksum_sha256


def _file_checksum_reasons(
    *,
    path: str,
    checksum_sha256: str,
    label: str,
) -> list[str]:
    if not path or not checksum_sha256:
        return [f"{label} path and checksum are required"]
    artifact_path = Path(path)
    if not artifact_path.is_file():
        return [f"{label} is missing: {path}"]
    if _sha256_file(artifact_path) != checksum_sha256:
        return [f"{label} checksum mismatch: {path}"]
    return []


def _evidence_handle(packet: EvidencePacket) -> EvidenceHandle:
    return EvidenceHandle(
        evidence_id=packet.evidence_id,
        source_kind=packet.source_kind,
        path=packet.artifact_path,
        checksum_sha256=packet.checksum_sha256,
        created_at=packet.created_at,
        session_id=packet.session_id,
        quality=packet.quality,
    )


def _require_session_evidence_index(
    session: BridgeSession,
    index_path: Path,
) -> None:
    if index_path.name != "evidence_index.json":
        raise ValueError("high-Z motion claim index path must be a session evidence_index.json")
    if index_path.resolve() != Path(session.evidence_index_path).resolve():
        raise ValueError(
            "high-Z motion claim index path must match the active session evidence index"
        )
    expected_session_segment = _safe_path_segment(session.session_id)
    if index_path.parent.name != expected_session_segment:
        raise ValueError("high-Z motion claim index path must be scoped to the session ID")


def _dedupe_evidence_handles(handles: list[EvidenceHandle]) -> list[EvidenceHandle]:
    deduped: list[EvidenceHandle] = []
    seen: set[str] = set()
    for handle in handles:
        if handle.evidence_id in seen:
            continue
        seen.add(handle.evidence_id)
        deduped.append(handle)
    return deduped
