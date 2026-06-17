from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, model_validator

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
    TARGET_CLASS_BY_NAME,
    TARGET_CLASS_EVIDENCE_METHOD,
    TargetClassResult,
    TargetClassVerificationRecord,
    target_class_verified_claim_id,
    target_class_verified_claim_type,
)
from aevum_ot2.core.schema import (
    SchemaVersionError,
    load_json_object,
    parse_versioned_json_model,
)

TARGET_CLASS_EVIDENCE_ARTIFACT_VERSION = 1
TARGET_EVIDENCE_SOURCE_KINDS = {
    EvidenceSourceKind.INSPECTION_NOTE,
    EvidenceSourceKind.VISION_ANALYSIS,
}
TARGET_EVIDENCE_SESSION_STATES = {
    BridgeSessionState.READY_NO_MOTION,
    BridgeSessionState.MOTION_COMMISSIONING_ARMED,
    BridgeSessionState.HIGH_Z_READY,
}


class TargetClassEvidenceArtifact(BaseModel):
    schema_version: int = TARGET_CLASS_EVIDENCE_ARTIFACT_VERSION
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
    def _validate_artifact(self) -> TargetClassEvidenceArtifact:
        if self.schema_version != TARGET_CLASS_EVIDENCE_ARTIFACT_VERSION:
            raise ValueError("unsupported target-class evidence artifact schema version")
        if not self.artifact_id.strip():
            raise ValueError("target-class evidence artifact_id is required")
        if not self.session_id.strip():
            raise ValueError("target-class evidence session_id is required")
        if self.target_class not in TARGET_CLASS_BY_NAME:
            raise ValueError(f"unknown target class: {self.target_class}")
        if _is_timezone_aware(self.created_at):
            raise ValueError("target-class evidence created_at must be timezone-naive")
        if self.image_captured_at is not None and _is_timezone_aware(
            self.image_captured_at
        ):
            raise ValueError("target-class evidence image_captured_at must be timezone-naive")
        if not self.image_path.strip() or not self.image_checksum_sha256.strip():
            raise ValueError("target-class evidence image path and checksum are required")
        if (
            self.image_capture_checksum_sha256
            and self.image_capture_checksum_sha256 != self.image_checksum_sha256
        ):
            raise ValueError("target-class evidence image capture checksum mismatch")
        has_vision_path = bool(self.vision_result_path.strip())
        has_vision_checksum = bool(self.vision_result_checksum_sha256.strip())
        if has_vision_path != has_vision_checksum:
            raise ValueError(
                "target-class evidence vision path and checksum must be provided together"
            )
        if self.quality == EvidenceQuality.USABLE:
            if not self.inspection_note.strip():
                raise ValueError("usable target-class evidence requires an inspection note")
            if self.image_captured_at is None:
                raise ValueError("usable target-class evidence requires image_captured_at")
            if not self.image_capture_robot_url.strip():
                raise ValueError("usable target-class evidence requires image_capture_robot_url")
            if not self.image_capture_endpoint.strip():
                raise ValueError("usable target-class evidence requires image_capture_endpoint")
            if not self.image_capture_checksum_sha256.strip():
                raise ValueError(
                    "usable target-class evidence requires image_capture_checksum_sha256"
                )
        return self


def build_target_class_evidence_artifact(
    record: TargetClassVerificationRecord,
    *,
    session: BridgeSession,
    artifact_id: str,
    image_path: str | Path,
    inspection_note: str,
    camera_capture: CameraCaptureResult | None = None,
    vision_result_path: str | Path | None = None,
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS,
    notes: list[str] | None = None,
) -> TargetClassEvidenceArtifact:
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
    return TargetClassEvidenceArtifact(
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


def write_target_class_evidence_artifact(
    artifact: TargetClassEvidenceArtifact,
    path: str | Path,
) -> Path:
    artifact_path = Path(path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = artifact_path.with_suffix(artifact_path.suffix + ".tmp")
    tmp.write_text(artifact.model_dump_json(indent=2) + "\n")
    tmp.replace(artifact_path)
    return artifact_path


def load_target_class_evidence_artifact(
    path: str | Path,
) -> TargetClassEvidenceArtifact:
    data = load_json_object(path, schema_name="TargetClassEvidenceArtifact")
    return parse_versioned_json_model(
        data,
        TargetClassEvidenceArtifact,
        schema_name="TargetClassEvidenceArtifact",
        path=path,
    )


def target_class_evidence_artifact_scope_reasons(
    record: TargetClassVerificationRecord,
    *,
    session: BridgeSession,
    artifact_path: str | Path,
) -> list[str]:
    path = Path(artifact_path)
    try:
        artifact = load_target_class_evidence_artifact(path)
    except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
        return [f"target-class evidence artifact is invalid: {exc}"]
    return _artifact_scope_reasons(
        record,
        artifact,
        session=session,
        artifact_path=path,
    )


def target_class_evidence_packets_from_artifact(
    record: TargetClassVerificationRecord,
    artifact: TargetClassEvidenceArtifact,
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
        target_class_evidence_packet(
            record,
            session=session,
            evidence_id=f"{artifact.artifact_id}:target",
            source_kind=(
                EvidenceSourceKind.VISION_ANALYSIS
                if artifact.vision_result_path
                else EvidenceSourceKind.INSPECTION_NOTE
            ),
            artifact_path=path,
            checksum_sha256=checksum,
            quality=artifact.quality,
            payload={
                "target_class": artifact.target_class,
                "pose_digest_sha256": artifact.pose_digest_sha256,
                "slot": artifact.slot,
                "value": True,
                "image_path": artifact.image_path,
                "image_checksum_sha256": artifact.image_checksum_sha256,
                "image_captured_at": _datetime_payload(artifact.image_captured_at),
                "image_capture_robot_url": artifact.image_capture_robot_url,
                "image_capture_endpoint": artifact.image_capture_endpoint,
                "image_capture_checksum_sha256": artifact.image_capture_checksum_sha256,
                "vision_result_path": artifact.vision_result_path,
                "vision_result_checksum_sha256": artifact.vision_result_checksum_sha256,
            },
            notes=artifact.notes,
        )
    ]


def target_class_evidence_packet(
    record: TargetClassVerificationRecord,
    *,
    session: BridgeSession | None = None,
    evidence_id: str,
    source_kind: EvidenceSourceKind = EvidenceSourceKind.VISION_ANALYSIS,
    artifact_path: str | Path = "",
    checksum_sha256: str = "",
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS,
    payload: dict[str, object] | None = None,
    notes: list[str] | None = None,
) -> EvidencePacket:
    if source_kind not in TARGET_EVIDENCE_SOURCE_KINDS:
        raise ValueError(f"unsupported target-class evidence source: {source_kind}")
    active_payload: dict[str, object] = {
        "target_class": record.target_class,
        "pose_digest_sha256": record.pose_digest_sha256,
    }
    active_payload.update(payload or {})
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
        operation="target_class_verification",
        artifact_path=str(Path(artifact_path)) if artifact_path else "",
        checksum_sha256=checksum_sha256,
        payload=active_payload,
        quality=quality,
        notes=notes or [],
    )


def derive_target_class_claims(
    record: TargetClassVerificationRecord,
    evidence_packets: Iterable[EvidencePacket],
    *,
    session: BridgeSession | None = None,
    method: str = TARGET_CLASS_EVIDENCE_METHOD,
) -> list[EvidenceClaim]:
    packets = list(evidence_packets)
    target_packet = _first_target_packet(packets)
    if target_packet is None:
        return []
    reasons = _target_packet_reasons(record, target_packet, session)
    quality = target_packet.quality if not reasons else EvidenceQuality.FAILED
    return [
        EvidenceClaim(
            claim_id=target_class_verified_claim_id(
                record.target_class,
                target_packet.evidence_id,
            ),
            claim_type=target_class_verified_claim_type(record.target_class),
            value=not reasons,
            created_at=datetime.now(),
            session_id=(
                session.session_id if session is not None else target_packet.session_id
            ),
            fixture_load_name=record.fixture_load_name,
            fixture_params_sha256=record.fixture_params_sha256,
            labware_definition_sha256=record.labware_definition_sha256,
            pose_digest_sha256=record.pose_digest_sha256,
            method=method,
            quality=quality,
            evidence=[_evidence_handle(target_packet)],
            reasons=reasons,
        )
    ]


def commit_target_class_claims(
    record: TargetClassVerificationRecord,
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
    claims = derive_target_class_claims(record, evidence_packets, session=session)
    return commit_evidence_transaction(
        packets=evidence_packets,
        claims=claims,
        index_path=resolved_index_path,
        root=resolved_root,
        transaction_id=transaction_id,
        session_id=session.session_id,
    )


def commit_target_class_evidence_artifact(
    record: TargetClassVerificationRecord,
    artifact: TargetClassEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: str | Path,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    transaction_id: str | None = None,
) -> EvidenceTransactionCommitResult:
    return commit_target_class_claims(
        record,
        target_class_evidence_packets_from_artifact(
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


def promoted_target_class_record(
    record: TargetClassVerificationRecord,
    target_claims: list[EvidenceClaim],
    *,
    pose_claims: list[EvidenceClaim] | None = None,
) -> TargetClassVerificationRecord:
    claim_type = target_class_verified_claim_type(record.target_class)
    usable_target_claims = [
        claim
        for claim in target_claims
        if claim.claim_type == claim_type
        and claim.value is True
        and claim.quality == EvidenceQuality.USABLE
        and claim.method == TARGET_CLASS_EVIDENCE_METHOD
    ]
    if not usable_target_claims:
        raise ValueError(f"missing usable target-class claim: {claim_type}")
    claims = [*usable_target_claims, *(pose_claims or [])]
    evidence = _dedupe_evidence_handles(
        [handle for claim in claims for handle in claim.evidence]
    )
    return record.model_copy(
        update={
            "result": TargetClassResult.PASSED,
            "evidence": evidence,
            "claims": claims,
        }
    )


def _target_packet_reasons(
    record: TargetClassVerificationRecord,
    packet: EvidencePacket,
    session: BridgeSession | None,
) -> list[str]:
    reasons = _packet_scope_reasons(record, packet, session)
    if packet.payload.get("target_class") != record.target_class:
        reasons.append("target evidence target_class does not match target record")
    if packet.payload.get("value") is not True:
        reasons.append("target evidence did not assert a true observation")
    return reasons


def _packet_scope_reasons(
    record: TargetClassVerificationRecord,
    packet: EvidencePacket,
    session: BridgeSession | None,
) -> list[str]:
    reasons: list[str] = []
    if packet.quality != EvidenceQuality.USABLE:
        reasons.append(f"evidence packet is not usable: {packet.evidence_id}")
    elif not _usable_artifact_is_bound(packet):
        reasons.append("usable target evidence packet must bind an artifact path and checksum")
    elif session is None:
        reasons.append("usable target evidence packet requires an active session")
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
        reasons.append("evidence packet fixture does not match target record")
    if packet.fixture_params_sha256 != record.fixture_params_sha256:
        reasons.append("evidence packet fixture params checksum does not match target record")
    if packet.labware_definition_sha256 != record.labware_definition_sha256:
        reasons.append("evidence packet labware checksum does not match target record")
    if packet.pose_digest_sha256 != record.pose_digest_sha256:
        reasons.append("evidence packet pose digest does not match target record")
    if packet.payload.get("pose_digest_sha256") != record.pose_digest_sha256:
        reasons.append("evidence payload pose digest does not match target record")
    return reasons


def _packet_artifact_scope_reasons(
    record: TargetClassVerificationRecord,
    packet: EvidencePacket,
    *,
    session: BridgeSession,
) -> list[str]:
    try:
        artifact = load_target_class_evidence_artifact(packet.artifact_path)
    except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
        return [f"usable target evidence packet artifact is invalid: {exc}"]

    reasons = _artifact_scope_reasons(
        record,
        artifact,
        session=session,
        artifact_path=Path(packet.artifact_path),
    )
    if artifact.quality != packet.quality:
        reasons.append("target-class evidence artifact quality does not match packet")
    if packet.payload.get("target_class") != artifact.target_class:
        reasons.append("target-class evidence packet target does not match artifact")
    if packet.payload.get("image_path") != artifact.image_path:
        reasons.append("target-class evidence packet image path does not match artifact")
    if packet.payload.get("image_checksum_sha256") != artifact.image_checksum_sha256:
        reasons.append("target-class evidence packet image checksum does not match artifact")
    if packet.payload.get("image_captured_at") != _datetime_payload(
        artifact.image_captured_at
    ):
        reasons.append("target-class evidence packet image capture time does not match artifact")
    if packet.payload.get("image_capture_robot_url") != artifact.image_capture_robot_url:
        reasons.append("target-class evidence packet image capture robot does not match artifact")
    if packet.payload.get("image_capture_endpoint") != artifact.image_capture_endpoint:
        reasons.append(
            "target-class evidence packet image capture endpoint does not match artifact"
        )
    if (
        packet.payload.get("image_capture_checksum_sha256")
        != artifact.image_capture_checksum_sha256
    ):
        reasons.append(
            "target-class evidence packet image capture checksum does not match artifact"
        )
    if packet.payload.get("vision_result_path", "") != artifact.vision_result_path:
        reasons.append("target-class evidence packet vision path does not match artifact")
    if (
        packet.payload.get("vision_result_checksum_sha256", "")
        != artifact.vision_result_checksum_sha256
    ):
        reasons.append("target-class evidence packet vision checksum does not match artifact")
    return reasons


def _artifact_scope_reasons(
    record: TargetClassVerificationRecord,
    artifact: TargetClassEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: Path,
) -> list[str]:
    reasons: list[str] = []
    if not artifact_path.is_file():
        reasons.append(f"target-class evidence artifact is missing: {artifact_path}")
    else:
        try:
            loaded = load_target_class_evidence_artifact(artifact_path)
        except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
            reasons.append(f"target-class evidence artifact cannot be loaded: {exc}")
        else:
            if loaded.model_dump(mode="json") != artifact.model_dump(mode="json"):
                reasons.append("target-class evidence artifact does not match artifact path")

    identity = session.fixture_identity
    if session.state not in TARGET_EVIDENCE_SESSION_STATES:
        reasons.append(f"target-class evidence session state is {session.state}")
    if session.lease_expires_at <= datetime.now():
        reasons.append("target-class evidence session lease is expired")
    if artifact.session_id != session.session_id:
        reasons.append("target-class evidence session does not match active session")
    if artifact.robot_serial != (session.robot_serial or ""):
        reasons.append("target-class evidence robot does not match active session")
    if artifact.robot_server_version != (session.robot_server_version or ""):
        reasons.append("target-class evidence robot-server version does not match session")
    if artifact.image_capture_robot_url != session.robot_url.rstrip("/"):
        reasons.append("target-class evidence image capture robot URL does not match session")
    if artifact.fixture_load_name != record.fixture_load_name:
        reasons.append("target-class evidence fixture does not match target record")
    if artifact.fixture_params_sha256 != identity.params_sha256:
        reasons.append("target-class evidence fixture params checksum does not match session")
    if artifact.labware_definition_sha256 != record.labware_definition_sha256:
        reasons.append("target-class evidence labware checksum does not match target record")
    if artifact.pose_digest_sha256 != record.pose_digest_sha256:
        reasons.append("target-class evidence pose digest does not match target record")
    if artifact.slot != record.slot:
        reasons.append("target-class evidence slot does not match target record")
    if artifact.target_class != record.target_class:
        reasons.append("target-class evidence target does not match target record")
    reasons.extend(_artifact_capture_time_reasons(artifact, session=session))
    if artifact.quality == EvidenceQuality.USABLE:
        reasons.extend(_artifact_camera_event_reasons(artifact, session=session))
    reasons.extend(
        _file_checksum_reasons(
            path=artifact.image_path,
            checksum_sha256=artifact.image_checksum_sha256,
            label="target-class evidence image",
        )
    )
    if artifact.vision_result_path or artifact.vision_result_checksum_sha256:
        reasons.extend(
            _file_checksum_reasons(
                path=artifact.vision_result_path,
                checksum_sha256=artifact.vision_result_checksum_sha256,
                label="target-class evidence vision result",
            )
        )
        reasons.extend(_vision_result_scope_reasons(artifact))
    return reasons


def _vision_result_scope_reasons(
    artifact: TargetClassEvidenceArtifact,
) -> list[str]:
    path = Path(artifact.vision_result_path)
    try:
        result = VisionAnalysisResult.model_validate_json(path.read_text())
    except (ValidationError, OSError, ValueError) as exc:
        return [f"target-class evidence vision result is invalid: {exc}"]
    reasons: list[str] = []
    if result.purpose != "high_z_target":
        reasons.append("target-class evidence vision result purpose is not high_z_target")
    if result.evidence_ok is not True:
        reasons.append("target-class evidence vision result evidence_ok is not true")
    if not _same_path(result.image_path, artifact.image_path):
        reasons.append("target-class evidence vision result image does not match artifact")
    if result.analyzed_at > datetime.now():
        reasons.append("target-class evidence vision result is from the future")
    return reasons


def _artifact_capture_time_reasons(
    artifact: TargetClassEvidenceArtifact,
    *,
    session: BridgeSession,
) -> list[str]:
    if artifact.image_captured_at is None:
        return ["target-class evidence image capture time is required"]
    reasons: list[str] = []
    if artifact.image_captured_at < session.updated_at:
        reasons.append("target-class evidence image capture predates active session authority")
    if artifact.image_captured_at >= session.lease_expires_at:
        reasons.append("target-class evidence image capture is outside the session lease")
    if artifact.image_captured_at > datetime.now():
        reasons.append("target-class evidence image capture is from the future")
    return reasons


def _artifact_camera_event_reasons(
    artifact: TargetClassEvidenceArtifact,
    *,
    session: BridgeSession,
) -> list[str]:
    for capture in _session_camera_captures(session):
        if _capture_matches_artifact(capture, artifact):
            return []
    return ["target-class evidence image capture is not indexed in the active session"]


def _first_target_packet(packets: list[EvidencePacket]) -> EvidencePacket | None:
    matching = [
        packet for packet in packets if packet.source_kind in TARGET_EVIDENCE_SOURCE_KINDS
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
        reasons.append("camera capture image path does not match target-class image")
    if capture.image_checksum_sha256 != image_checksum_sha256:
        reasons.append("camera capture checksum does not match target-class image")
    try:
        if Path(capture.image_path).stat().st_size != capture.bytes_written:
            reasons.append("camera capture byte count does not match target-class image")
    except OSError:
        reasons.append("camera capture image is missing")
    return reasons


def _capture_matches_artifact(
    capture: CameraCaptureResult,
    artifact: TargetClassEvidenceArtifact,
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
        raise ValueError("target claim index path must be a session evidence_index.json")
    if index_path.resolve() != Path(session.evidence_index_path).resolve():
        raise ValueError("target claim index path must match the active session evidence index")
    expected_session_segment = _safe_path_segment(session.session_id)
    if index_path.parent.name != expected_session_segment:
        raise ValueError("target claim index path must be scoped to the session ID")


def _dedupe_evidence_handles(handles: list[EvidenceHandle]) -> list[EvidenceHandle]:
    deduped: list[EvidenceHandle] = []
    seen: set[str] = set()
    for handle in handles:
        if handle.evidence_id in seen:
            continue
        seen.add(handle.evidence_id)
        deduped.append(handle)
    return deduped
