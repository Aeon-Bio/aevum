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
    CameraCaptureResult,
    EvidenceClaim,
    EvidenceHandle,
    EvidencePacket,
    EvidenceQuality,
    EvidenceSourceKind,
)
from aevum_ot2.core.pose import (
    POSE_EVIDENCE_METHOD,
    POSE_UPRIGHT_CLAIM,
    FixtureOrientation,
    FixturePose,
    pose_orientation_claim_type,
)
from aevum_ot2.core.schema import (
    SchemaVersionError,
    load_json_object,
    parse_versioned_json_model,
)

FIXTURE_POSE_EVIDENCE_ARTIFACT_VERSION = 1


class FixturePoseEvidenceArtifact(BaseModel):
    schema_version: int = FIXTURE_POSE_EVIDENCE_ARTIFACT_VERSION
    artifact_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    session_id: str
    robot_serial: str = ""
    robot_server_version: str = ""
    fixture_load_name: str
    fixture_params_sha256: str
    labware_definition_sha256: str
    pose_digest_sha256: str
    slot: str
    observed_orientation: FixtureOrientation
    fixture_upright: bool
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
    def _validate_artifact(self) -> FixturePoseEvidenceArtifact:
        if self.schema_version != FIXTURE_POSE_EVIDENCE_ARTIFACT_VERSION:
            raise ValueError("unsupported fixture pose evidence artifact schema version")
        if not self.artifact_id.strip():
            raise ValueError("fixture pose evidence artifact_id is required")
        if not self.session_id.strip():
            raise ValueError("fixture pose evidence session_id is required")
        if _is_timezone_aware(self.created_at):
            raise ValueError("fixture pose evidence created_at must be timezone-naive")
        if self.image_captured_at is not None and _is_timezone_aware(
            self.image_captured_at
        ):
            raise ValueError("fixture pose evidence image_captured_at must be timezone-naive")
        if not self.image_path.strip() or not self.image_checksum_sha256.strip():
            raise ValueError("fixture pose evidence image path and checksum are required")
        if (
            self.image_capture_checksum_sha256
            and self.image_capture_checksum_sha256 != self.image_checksum_sha256
        ):
            raise ValueError("fixture pose evidence image capture checksum mismatch")
        has_vision_path = bool(self.vision_result_path.strip())
        has_vision_checksum = bool(self.vision_result_checksum_sha256.strip())
        if has_vision_path != has_vision_checksum:
            raise ValueError(
                "fixture pose evidence vision path and checksum must be provided together"
            )
        if self.quality == EvidenceQuality.USABLE:
            if not self.inspection_note.strip():
                raise ValueError("usable fixture pose evidence requires an inspection note")
            if self.image_captured_at is None:
                raise ValueError("usable fixture pose evidence requires image_captured_at")
            if not self.image_capture_robot_url.strip():
                raise ValueError(
                    "usable fixture pose evidence requires image_capture_robot_url"
                )
            if not self.image_capture_endpoint.strip():
                raise ValueError(
                    "usable fixture pose evidence requires image_capture_endpoint"
                )
            if not self.image_capture_checksum_sha256.strip():
                raise ValueError(
                    "usable fixture pose evidence requires image_capture_checksum_sha256"
                )
        return self


def build_fixture_pose_evidence_artifact(
    pose: FixturePose,
    *,
    session: BridgeSession,
    artifact_id: str,
    image_path: str | Path,
    observed_orientation: FixtureOrientation | str,
    fixture_upright: bool,
    inspection_note: str,
    camera_capture: CameraCaptureResult | None = None,
    vision_result_path: str | Path | None = None,
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS,
    notes: list[str] | None = None,
) -> FixturePoseEvidenceArtifact:
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
    return FixturePoseEvidenceArtifact(
        artifact_id=artifact_id,
        session_id=session.session_id,
        robot_serial=session.robot_serial or "",
        robot_server_version=session.robot_server_version or "",
        fixture_load_name=pose.fixture_load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=pose.fixture_definition_sha256,
        pose_digest_sha256=pose.pose_digest_sha256,
        slot=pose.slot,
        observed_orientation=FixtureOrientation(observed_orientation),
        fixture_upright=fixture_upright,
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


def write_fixture_pose_evidence_artifact(
    artifact: FixturePoseEvidenceArtifact,
    path: str | Path,
) -> Path:
    artifact_path = Path(path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = artifact_path.with_suffix(artifact_path.suffix + ".tmp")
    tmp.write_text(artifact.model_dump_json(indent=2) + "\n")
    tmp.replace(artifact_path)
    return artifact_path


def load_fixture_pose_evidence_artifact(path: str | Path) -> FixturePoseEvidenceArtifact:
    data = load_json_object(path, schema_name="FixturePoseEvidenceArtifact")
    return parse_versioned_json_model(
        data,
        FixturePoseEvidenceArtifact,
        schema_name="FixturePoseEvidenceArtifact",
        path=path,
    )


def fixture_pose_evidence_packets_from_artifact(
    pose: FixturePose,
    artifact: FixturePoseEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: str | Path,
) -> list[EvidencePacket]:
    path = Path(artifact_path)
    blockers = _artifact_scope_reasons(
        pose,
        artifact,
        session=session,
        artifact_path=path,
    )
    if blockers:
        raise ValueError("; ".join(blockers))
    checksum = _sha256_file(path)
    return [
        fixture_pose_evidence_packet(
            pose,
            source_kind=EvidenceSourceKind.FIXTURE_POSE_ORIENTATION,
            session=session,
            evidence_id=f"{artifact.artifact_id}:orientation",
            artifact_path=path,
            checksum_sha256=checksum,
            quality=artifact.quality,
            payload={
                "pose_digest_sha256": artifact.pose_digest_sha256,
                "orientation": artifact.observed_orientation.value,
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
        ),
        fixture_pose_evidence_packet(
            pose,
            source_kind=EvidenceSourceKind.FIXTURE_UPRIGHT,
            session=session,
            evidence_id=f"{artifact.artifact_id}:upright",
            artifact_path=path,
            checksum_sha256=checksum,
            quality=artifact.quality,
            payload={
                "pose_digest_sha256": artifact.pose_digest_sha256,
                "fixture_upright": artifact.fixture_upright,
                "slot": artifact.slot,
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
        ),
    ]


def commit_fixture_pose_evidence_artifact(
    pose: FixturePose,
    artifact: FixturePoseEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: str | Path,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    transaction_id: str | None = None,
) -> EvidenceTransactionCommitResult:
    return commit_fixture_pose_claims(
        pose,
        fixture_pose_evidence_packets_from_artifact(
            pose,
            artifact,
            session=session,
            artifact_path=artifact_path,
        ),
        session=session,
        index_path=index_path,
        root=root,
        transaction_id=transaction_id,
    )


def fixture_pose_evidence_packet(
    pose: FixturePose,
    *,
    source_kind: EvidenceSourceKind,
    session: BridgeSession | None = None,
    evidence_id: str,
    artifact_path: str | Path = "",
    checksum_sha256: str = "",
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS,
    payload: dict[str, object] | None = None,
    notes: list[str] | None = None,
) -> EvidencePacket:
    if source_kind not in {
        EvidenceSourceKind.FIXTURE_POSE_ORIENTATION,
        EvidenceSourceKind.FIXTURE_UPRIGHT,
    }:
        raise ValueError(f"unsupported fixture pose evidence source: {source_kind}")
    active_payload = _default_pose_evidence_payload(pose, source_kind)
    active_payload.update(payload or {})
    identity = session.fixture_identity if session is not None else None
    return EvidencePacket(
        evidence_id=evidence_id,
        source_kind=source_kind,
        session_id=session.session_id if session is not None else "",
        robot_serial=(session.robot_serial or "") if session is not None else "",
        robot_server_version=(
            (session.robot_server_version or "") if session is not None else ""
        ),
        fixture_load_name=pose.fixture_load_name,
        fixture_params_sha256=identity.params_sha256 if identity is not None else "",
        labware_definition_sha256=pose.fixture_definition_sha256,
        pose_digest_sha256=pose.pose_digest_sha256,
        artifact_path=str(Path(artifact_path)) if artifact_path else "",
        checksum_sha256=checksum_sha256,
        payload=active_payload,
        quality=quality,
        notes=notes or [],
    )


def derive_fixture_pose_claims(
    pose: FixturePose,
    evidence_packets: Iterable[EvidencePacket],
    *,
    session: BridgeSession | None = None,
    method: str = POSE_EVIDENCE_METHOD,
) -> list[EvidenceClaim]:
    packets = list(evidence_packets)
    claims: list[EvidenceClaim] = []
    orientation_packet = _first_packet(
        packets,
        EvidenceSourceKind.FIXTURE_POSE_ORIENTATION,
    )
    upright_packet = _first_packet(packets, EvidenceSourceKind.FIXTURE_UPRIGHT)
    if orientation_packet is not None:
        claims.append(
            _claim_from_packet(
                pose,
                orientation_packet,
                session=session,
                claim_type=pose_orientation_claim_type(
                    orientation=pose.orientation,
                    slot=pose.slot,
                    fixture_definition_sha256=pose.fixture_definition_sha256,
                ),
                method=method,
                reasons=_orientation_packet_reasons(pose, orientation_packet, session),
            )
        )
    if upright_packet is not None:
        claims.append(
            _claim_from_packet(
                pose,
                upright_packet,
                session=session,
                claim_type=POSE_UPRIGHT_CLAIM,
                method=method,
                reasons=_upright_packet_reasons(pose, upright_packet, session),
            )
        )
    return claims


def commit_fixture_pose_claims(
    pose: FixturePose,
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
    claims = derive_fixture_pose_claims(pose, evidence_packets, session=session)
    return commit_evidence_transaction(
        packets=evidence_packets,
        claims=claims,
        index_path=resolved_index_path,
        root=resolved_root,
        transaction_id=transaction_id,
        session_id=session.session_id,
    )


def _default_pose_evidence_payload(
    pose: FixturePose,
    source_kind: EvidenceSourceKind,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "pose_digest_sha256": pose.pose_digest_sha256,
    }
    return payload


def _first_packet(
    packets: list[EvidencePacket],
    source_kind: EvidenceSourceKind,
) -> EvidencePacket | None:
    matching = [packet for packet in packets if packet.source_kind == source_kind]
    if not matching:
        return None
    return sorted(matching, key=lambda packet: packet.created_at, reverse=True)[0]


def _claim_from_packet(
    pose: FixturePose,
    packet: EvidencePacket,
    *,
    session: BridgeSession | None,
    claim_type: str,
    method: str,
    reasons: list[str],
) -> EvidenceClaim:
    quality = packet.quality if not reasons else EvidenceQuality.FAILED
    identity = session.fixture_identity if session is not None else None
    return EvidenceClaim(
        claim_id=_pose_claim_id(claim_type, pose.pose_digest_sha256, packet.evidence_id),
        claim_type=claim_type,
        value=not reasons,
        created_at=datetime.now(),
        session_id=session.session_id if session is not None else packet.session_id,
        fixture_load_name=pose.fixture_load_name,
        fixture_params_sha256=identity.params_sha256 if identity is not None else (
            packet.fixture_params_sha256
        ),
        labware_definition_sha256=pose.fixture_definition_sha256,
        pose_digest_sha256=pose.pose_digest_sha256,
        method=method,
        quality=quality,
        evidence=[_evidence_handle(packet)],
        reasons=reasons,
    )


def _orientation_packet_reasons(
    pose: FixturePose,
    packet: EvidencePacket,
    session: BridgeSession | None,
) -> list[str]:
    reasons = _packet_scope_reasons(pose, packet, session)
    if packet.payload.get("orientation") != pose.orientation.value:
        reasons.append("orientation evidence does not match fixture pose")
    if str(packet.payload.get("slot", "")) != pose.slot:
        reasons.append("orientation evidence slot does not match fixture pose")
    if packet.payload.get("value") is not True:
        reasons.append("orientation evidence did not assert a true observation")
    return reasons


def _upright_packet_reasons(
    pose: FixturePose,
    packet: EvidencePacket,
    session: BridgeSession | None,
) -> list[str]:
    reasons = _packet_scope_reasons(pose, packet, session)
    slot = packet.payload.get("slot")
    if slot is not None and str(slot) != pose.slot:
        reasons.append("upright evidence slot does not match fixture pose")
    upright_value = packet.payload.get(
        "fixture_upright",
        packet.payload.get("upright", packet.payload.get("value")),
    )
    if upright_value is not True:
        reasons.append("upright evidence did not assert a true observation")
    return reasons


def _packet_scope_reasons(
    pose: FixturePose,
    packet: EvidencePacket,
    session: BridgeSession | None,
) -> list[str]:
    reasons: list[str] = []
    if packet.quality != EvidenceQuality.USABLE:
        reasons.append(f"evidence packet is not usable: {packet.evidence_id}")
    elif not _usable_artifact_is_bound(packet):
        reasons.append("usable pose evidence packet must bind an artifact path and checksum")
    elif session is None:
        reasons.append("usable pose evidence packet requires an active session")
    else:
        reasons.extend(_packet_artifact_scope_reasons(pose, packet, session=session))
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
    if packet.fixture_load_name != pose.fixture_load_name:
        reasons.append("evidence packet fixture does not match fixture pose")
    if session is not None and (
        packet.fixture_params_sha256 != session.fixture_identity.params_sha256
    ):
        reasons.append("evidence packet fixture params checksum does not match session")
    if packet.labware_definition_sha256 != pose.fixture_definition_sha256:
        reasons.append("evidence packet labware checksum does not match fixture pose")
    if packet.pose_digest_sha256 != pose.pose_digest_sha256:
        reasons.append("evidence packet pose digest does not match fixture pose")
    if packet.payload.get("pose_digest_sha256") != pose.pose_digest_sha256:
        reasons.append("evidence payload pose digest does not match fixture pose")
    return reasons


def _packet_artifact_scope_reasons(
    pose: FixturePose,
    packet: EvidencePacket,
    *,
    session: BridgeSession,
) -> list[str]:
    try:
        artifact = load_fixture_pose_evidence_artifact(packet.artifact_path)
    except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
        return [f"usable pose evidence packet artifact is invalid: {exc}"]

    reasons = _artifact_scope_reasons(
        pose,
        artifact,
        session=session,
        artifact_path=Path(packet.artifact_path),
    )
    if artifact.quality != packet.quality:
        reasons.append("fixture pose evidence artifact quality does not match packet")
    if packet.payload.get("image_path") != artifact.image_path:
        reasons.append("fixture pose evidence packet image path does not match artifact")
    if packet.payload.get("image_checksum_sha256") != artifact.image_checksum_sha256:
        reasons.append("fixture pose evidence packet image checksum does not match artifact")
    if packet.payload.get("image_captured_at") != _datetime_payload(
        artifact.image_captured_at
    ):
        reasons.append("fixture pose evidence packet image capture time does not match artifact")
    if packet.payload.get("image_capture_robot_url") != artifact.image_capture_robot_url:
        reasons.append("fixture pose evidence packet image capture robot does not match artifact")
    if packet.payload.get("image_capture_endpoint") != artifact.image_capture_endpoint:
        reasons.append(
            "fixture pose evidence packet image capture endpoint does not match artifact"
        )
    if (
        packet.payload.get("image_capture_checksum_sha256")
        != artifact.image_capture_checksum_sha256
    ):
        reasons.append(
            "fixture pose evidence packet image capture checksum does not match artifact"
        )
    if packet.payload.get("vision_result_path", "") != artifact.vision_result_path:
        reasons.append("fixture pose evidence packet vision path does not match artifact")
    if (
        packet.payload.get("vision_result_checksum_sha256", "")
        != artifact.vision_result_checksum_sha256
    ):
        reasons.append("fixture pose evidence packet vision checksum does not match artifact")
    if packet.source_kind == EvidenceSourceKind.FIXTURE_POSE_ORIENTATION:
        if packet.payload.get("orientation") != artifact.observed_orientation.value:
            reasons.append("fixture pose evidence packet orientation does not match artifact")
        if packet.payload.get("slot") != artifact.slot:
            reasons.append("fixture pose evidence packet slot does not match artifact")
    if packet.source_kind == EvidenceSourceKind.FIXTURE_UPRIGHT:
        if packet.payload.get("fixture_upright") != artifact.fixture_upright:
            reasons.append("fixture pose evidence packet upright state does not match artifact")
    return reasons


def _artifact_scope_reasons(
    pose: FixturePose,
    artifact: FixturePoseEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: Path,
) -> list[str]:
    reasons: list[str] = []
    if not artifact_path.is_file():
        reasons.append(f"fixture pose evidence artifact is missing: {artifact_path}")
    else:
        try:
            loaded = load_fixture_pose_evidence_artifact(artifact_path)
        except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
            reasons.append(f"fixture pose evidence artifact cannot be loaded: {exc}")
        else:
            if loaded.model_dump(mode="json") != artifact.model_dump(mode="json"):
                reasons.append("fixture pose evidence artifact does not match artifact path")

    if artifact.session_id != session.session_id:
        reasons.append("fixture pose evidence session does not match active session")
    if artifact.robot_serial != (session.robot_serial or ""):
        reasons.append("fixture pose evidence robot does not match active session")
    if artifact.robot_server_version != (session.robot_server_version or ""):
        reasons.append("fixture pose evidence robot-server version does not match session")
    if artifact.image_capture_robot_url != session.robot_url.rstrip("/"):
        reasons.append("fixture pose evidence image capture robot URL does not match session")
    if artifact.fixture_load_name != pose.fixture_load_name:
        reasons.append("fixture pose evidence fixture does not match fixture pose")
    if artifact.fixture_params_sha256 != session.fixture_identity.params_sha256:
        reasons.append("fixture pose evidence fixture params checksum does not match session")
    if artifact.labware_definition_sha256 != pose.fixture_definition_sha256:
        reasons.append("fixture pose evidence labware checksum does not match fixture pose")
    if artifact.pose_digest_sha256 != pose.pose_digest_sha256:
        reasons.append("fixture pose evidence pose digest does not match fixture pose")
    if artifact.slot != pose.slot:
        reasons.append("fixture pose evidence slot does not match fixture pose")
    if artifact.observed_orientation != pose.orientation:
        reasons.append("fixture pose evidence orientation does not match fixture pose")
    reasons.extend(_artifact_capture_time_reasons(artifact, session=session))
    if artifact.quality == EvidenceQuality.USABLE:
        reasons.extend(_artifact_camera_event_reasons(artifact, session=session))
    reasons.extend(
        _file_checksum_reasons(
            path=artifact.image_path,
            checksum_sha256=artifact.image_checksum_sha256,
            label="fixture pose evidence image",
        )
    )
    if artifact.vision_result_path or artifact.vision_result_checksum_sha256:
        reasons.extend(
            _file_checksum_reasons(
                path=artifact.vision_result_path,
                checksum_sha256=artifact.vision_result_checksum_sha256,
                label="fixture pose evidence vision result",
            )
        )
    return reasons


def _artifact_capture_time_reasons(
    artifact: FixturePoseEvidenceArtifact,
    *,
    session: BridgeSession,
) -> list[str]:
    if artifact.image_captured_at is None:
        return ["fixture pose evidence image capture time is required"]
    reasons: list[str] = []
    if artifact.image_captured_at < session.updated_at:
        reasons.append("fixture pose evidence image capture predates active session authority")
    if artifact.image_captured_at >= session.lease_expires_at:
        reasons.append("fixture pose evidence image capture is outside the session lease")
    if artifact.image_captured_at > datetime.now():
        reasons.append("fixture pose evidence image capture is from the future")
    return reasons


def _artifact_camera_event_reasons(
    artifact: FixturePoseEvidenceArtifact,
    *,
    session: BridgeSession,
) -> list[str]:
    for capture in _session_camera_captures(session):
        if _capture_matches_artifact(capture, artifact):
            return []
    return ["fixture pose evidence image capture is not indexed in the active session"]


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
        reasons.append("camera capture image path does not match fixture pose image")
    if capture.image_checksum_sha256 != image_checksum_sha256:
        reasons.append("camera capture checksum does not match fixture pose image")
    try:
        if Path(capture.image_path).stat().st_size != capture.bytes_written:
            reasons.append("camera capture byte count does not match fixture pose image")
    except OSError:
        reasons.append("camera capture image is missing")
    return reasons


def _capture_matches_artifact(
    capture: CameraCaptureResult,
    artifact: FixturePoseEvidenceArtifact,
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


def _pose_claim_id(claim_type: str, pose_digest_sha256: str, evidence_id: str) -> str:
    return f"{claim_type}:pose-{pose_digest_sha256[:12]}:evidence-{evidence_id}"


def _require_session_evidence_index(
    session: BridgeSession,
    index_path: Path,
) -> None:
    if index_path.name != "evidence_index.json":
        raise ValueError("pose claim index path must be a session evidence_index.json")
    if index_path.resolve() != Path(session.evidence_index_path).resolve():
        raise ValueError("pose claim index path must match the active session evidence index")
    expected_session_segment = _safe_path_segment(session.session_id)
    if index_path.parent.name != expected_session_segment:
        raise ValueError("pose claim index path must be scoped to the session ID")
