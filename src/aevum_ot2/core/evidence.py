from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback for local dev.
    fcntl = None

from pydantic import BaseModel, Field, ValidationError

from aevum_cad.params import ROOT
from aevum_ot2.core.evidence_primitives import (
    EVIDENCE_TRANSACTIONS_DIRNAME,
    _safe_path_segment,
    _same_path,
    _sha256_file,
)
from aevum_ot2.core.models import (
    EvidenceClaim,
    EvidenceEvent,
    EvidenceIndex,
    EvidencePacket,
    EvidenceQuality,
    EvidenceSourceKind,
)
from aevum_ot2.core.schema import (
    SchemaVersionError,
    load_json_object,
    load_versioned_json_model,
    require_schema_version,
    require_schema_versioned_items,
)

DEFAULT_EVIDENCE_INDEX = ROOT / "data" / "measurements" / "ot2_evidence_index.json"
DEFAULT_SESSION_EVIDENCE_ROOT = ROOT / "data" / "measurements" / "sessions"
DEFAULT_EVIDENCE_TRANSACTION_ROOT = ROOT / "data" / "measurements" / EVIDENCE_TRANSACTIONS_DIRNAME
EVIDENCE_TRANSACTION_EVENT = "evidence_transaction_committed"
POSE_EVIDENCE_METHOD = "fixture_pose_evidence_packet_v1"
POSE_UPRIGHT_CLAIM = "fixture_upright"
POSE_ORIENTATION_CLAIM_PREFIX = "fixture_pose_orientation:"


class EvidenceTransactionArtifact(BaseModel):
    artifact_type: Literal["packet", "claim"]
    artifact_id: str
    path: str
    checksum_path: str
    checksum_sha256: str


class EvidenceTransactionManifest(BaseModel):
    schema_version: int = 1
    transaction_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    committed_at: datetime | None = None
    status: Literal["prepared", "committed"] = "prepared"
    session_id: str = ""
    index_path: str
    packets: list[EvidenceTransactionArtifact] = Field(default_factory=list)
    claims: list[EvidenceTransactionArtifact] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class EvidenceTransactionCommitResult(BaseModel):
    manifest: EvidenceTransactionManifest
    manifest_path: str
    manifest_checksum_sha256: str
    index: EvidenceIndex


class EvidenceTransactionScanFinding(BaseModel):
    transaction_id: str
    severity: Literal["info", "warning", "blocker"]
    reason: str
    manifest_path: str = ""


class EvidenceTransactionScan(BaseModel):
    root: str
    index_path: str
    findings: list[EvidenceTransactionScanFinding] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(finding.severity != "blocker" for finding in self.findings)


def load_evidence_index(path: str | Path = DEFAULT_EVIDENCE_INDEX) -> EvidenceIndex:
    index_path = Path(path)
    if not index_path.exists():
        return EvidenceIndex()

    return load_versioned_json_model(
        index_path,
        EvidenceIndex,
        schema_name="EvidenceIndex",
    )


def append_evidence_event(
    event: EvidenceEvent,
    path: str | Path = DEFAULT_EVIDENCE_INDEX,
) -> EvidenceIndex:
    index_path = Path(path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with _locked_index(index_path):
        index = load_evidence_index(index_path)
        index.events.append(event)
        _atomic_write_json(index_path, index.model_dump(mode="json"))
        return index


def evidence_index_path_for_session(
    session_id: str,
    *,
    root: str | Path = DEFAULT_SESSION_EVIDENCE_ROOT,
) -> Path:
    return Path(root) / _safe_path_segment(session_id) / "evidence_index.json"


def append_session_evidence_event(
    event: EvidenceEvent,
    *,
    session_id: str | None = None,
    root: str | Path = DEFAULT_SESSION_EVIDENCE_ROOT,
) -> EvidenceIndex:
    resolved_session_id = session_id or event.session_id
    if not resolved_session_id:
        raise ValueError("session_id is required for session-scoped evidence")
    if event.session_id is not None and event.session_id != resolved_session_id:
        raise ValueError(
            f"event session {event.session_id} does not match target session "
            f"{resolved_session_id}"
        )
    if event.session_id is None:
        event = event.model_copy(update={"session_id": resolved_session_id})
    return append_evidence_event(
        event,
        path=evidence_index_path_for_session(resolved_session_id, root=root),
    )


def commit_evidence_transaction(
    *,
    packets: list[EvidencePacket],
    claims: list[EvidenceClaim],
    index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    root: str | Path = DEFAULT_EVIDENCE_TRANSACTION_ROOT,
    transaction_id: str | None = None,
    session_id: str = "",
) -> EvidenceTransactionCommitResult:
    if not packets:
        raise ValueError("at least one evidence packet is required")
    packet_blockers: list[str] = []
    for packet in packets:
        packet_blockers.extend(
            _packet_external_artifact_blockers(packet, index_path=index_path)
        )
    if packet_blockers:
        raise ValueError("; ".join(packet_blockers))
    claim_link_blockers = _claim_packet_link_blockers(
        claims,
        packet_ids={packet.evidence_id for packet in packets},
        packets_by_id={packet.evidence_id: packet for packet in packets},
    )
    if claim_link_blockers:
        raise ValueError("; ".join(claim_link_blockers))
    resolved_transaction_id = transaction_id or f"txn-{uuid4().hex}"
    transaction_dir = Path(root) / _safe_path_segment(resolved_transaction_id)
    transaction_dir.mkdir(parents=True, exist_ok=False)

    packet_artifacts = [
        _write_transaction_artifact(transaction_dir, "packet", packet.evidence_id, packet)
        for packet in packets
    ]
    claim_artifacts = [
        _write_transaction_artifact(transaction_dir, "claim", claim.claim_id, claim)
        for claim in claims
    ]
    manifest_path = transaction_dir / "transaction.json"
    manifest_session_id = _transaction_session_id(packets, claims, explicit_session_id=session_id)
    manifest = EvidenceTransactionManifest(
        transaction_id=resolved_transaction_id,
        committed_at=datetime.now(),
        status="committed",
        session_id=manifest_session_id,
        index_path=str(Path(index_path)),
        packets=packet_artifacts,
        claims=claim_artifacts,
    )
    _atomic_write_json(manifest_path, manifest.model_dump(mode="json"))
    manifest_checksum = _write_checksum_file(manifest_path)
    event = EvidenceEvent(
        event_type=EVIDENCE_TRANSACTION_EVENT,
        session_id=manifest.session_id,
        summary="Evidence transaction committed",
        payload={
            "transaction_id": manifest.transaction_id,
            "manifest_path": str(manifest_path),
            "manifest_checksum_sha256": manifest_checksum,
        },
    )
    index = append_evidence_event(event, path=index_path)
    return EvidenceTransactionCommitResult(
        manifest=manifest,
        manifest_path=str(manifest_path),
        manifest_checksum_sha256=manifest_checksum,
        index=index,
    )


def load_committed_evidence_claims(
    *,
    index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    root: str | Path = DEFAULT_EVIDENCE_TRANSACTION_ROOT,
) -> list[EvidenceClaim]:
    claims: list[EvidenceClaim] = []
    for manifest, blockers, manifest_path in _indexed_transaction_manifests(
        index_path,
        root=root,
    ):
        if blockers or manifest.status != "committed":
            continue
        if _manifest_artifact_blockers(manifest, manifest_path=manifest_path):
            continue
        for artifact in manifest.claims:
            try:
                claims.append(_load_evidence_claim_artifact(Path(artifact.path)))
            except (SchemaVersionError, ValidationError, OSError):
                continue
    return claims


def scan_evidence_transactions(
    *,
    root: str | Path = DEFAULT_EVIDENCE_TRANSACTION_ROOT,
    index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
) -> EvidenceTransactionScan:
    root_path = Path(root)
    findings: list[EvidenceTransactionScanFinding] = []
    indexed_manifest_results = list(_indexed_transaction_manifests(index_path, root=root_path))
    for manifest, blockers, _manifest_path in indexed_manifest_results:
        for blocker in blockers:
            findings.append(
                EvidenceTransactionScanFinding(
                    transaction_id=manifest.transaction_id,
                    severity="blocker",
                    reason=blocker,
                )
            )
    indexed_transactions = {
        manifest.transaction_id: manifest
        for manifest, blockers, _manifest_path in indexed_manifest_results
        if not blockers
    }
    indexed_paths = {Path(manifest_path) for manifest_path in _indexed_manifest_paths(index_path)}

    if root_path.exists():
        for child in sorted(path for path in root_path.iterdir() if path.is_dir()):
            manifest_path = child / "transaction.json"
            if not manifest_path.exists():
                findings.append(
                    EvidenceTransactionScanFinding(
                        transaction_id=child.name,
                        severity="warning",
                        reason="transaction directory has no manifest",
                    )
                )
                continue
            try:
                manifest = _load_transaction_manifest(manifest_path)
            except (SchemaVersionError, ValidationError) as exc:
                findings.append(
                    EvidenceTransactionScanFinding(
                        transaction_id=child.name,
                        severity="blocker",
                        reason=str(exc),
                        manifest_path=str(manifest_path),
                    )
                )
                continue
            blockers = _manifest_artifact_blockers(manifest, manifest_path=manifest_path)
            for blocker in blockers:
                findings.append(
                    EvidenceTransactionScanFinding(
                        transaction_id=manifest.transaction_id,
                        severity="blocker",
                        reason=blocker,
                        manifest_path=str(manifest_path),
                    )
                )
            if manifest.status != "committed":
                findings.append(
                    EvidenceTransactionScanFinding(
                        transaction_id=manifest.transaction_id,
                        severity="warning",
                        reason=f"transaction status is {manifest.status}",
                        manifest_path=str(manifest_path),
                    )
                )
            if manifest_path not in indexed_paths:
                findings.append(
                    EvidenceTransactionScanFinding(
                        transaction_id=manifest.transaction_id,
                        severity="warning",
                        reason="committed transaction manifest is not indexed",
                        manifest_path=str(manifest_path),
                    )
                )

    for manifest, _indexed_blockers, manifest_path in indexed_manifest_results:
        if manifest.transaction_id not in indexed_transactions:
            continue
        blockers = _manifest_artifact_blockers(manifest, manifest_path=manifest_path)
        for blocker in blockers:
            findings.append(
                EvidenceTransactionScanFinding(
                    transaction_id=manifest.transaction_id,
                    severity="blocker",
                    reason=blocker,
                    manifest_path=str(Path(manifest.packets[0].path).parent / "transaction.json")
                    if manifest.packets
                    else "",
                )
            )
    return EvidenceTransactionScan(
        root=str(root_path),
        index_path=str(Path(index_path)),
        findings=findings,
    )


@contextmanager
def _locked_index(path: Path) -> Iterator[None]:
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock_file:
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _atomic_write_json(path: Path, data: object) -> None:
    _durable_write_text(path, json.dumps(data, indent=2) + "\n")


def _write_transaction_artifact(
    transaction_dir: Path,
    artifact_type: Literal["packet", "claim"],
    artifact_id: str,
    model: EvidencePacket | EvidenceClaim,
) -> EvidenceTransactionArtifact:
    artifact_dir = transaction_dir / f"{artifact_type}s"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{_safe_path_segment(artifact_id)}.json"
    _atomic_write_json(path, model.model_dump(mode="json"))
    checksum = _write_checksum_file(path)
    return EvidenceTransactionArtifact(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        path=str(path),
        checksum_path=str(path.with_suffix(path.suffix + ".sha256")),
        checksum_sha256=checksum,
    )


def _write_checksum_file(path: Path) -> str:
    checksum = _sha256_file(path)
    checksum_path = path.with_suffix(path.suffix + ".sha256")
    _durable_write_text(checksum_path, checksum + "\n")
    return checksum


def _durable_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    _fsync_directory(path.parent)


def _fsync_directory(path: Path) -> None:
    open_flags = getattr(os, "O_DIRECTORY", 0) | os.O_RDONLY
    try:
        fd = os.open(path, open_flags)
    except OSError:  # pragma: no cover - platform fallback.
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _transaction_session_id(
    packets: list[EvidencePacket],
    claims: list[EvidenceClaim],
    *,
    explicit_session_id: str = "",
) -> str:
    session_ids = {explicit_session_id} if explicit_session_id else set()
    for packet in packets:
        if packet.session_id:
            session_ids.add(packet.session_id)
    for claim in claims:
        if claim.session_id:
            session_ids.add(claim.session_id)
    if len(session_ids) > 1:
        raise ValueError("evidence transaction cannot mix session IDs")
    return next(iter(session_ids), "")


def _load_transaction_manifest(path: Path) -> EvidenceTransactionManifest:
    return load_versioned_json_model(
        path,
        EvidenceTransactionManifest,
        schema_name="EvidenceTransactionManifest",
    )


def _load_evidence_packet_artifact(path: Path) -> EvidencePacket:
    return load_versioned_json_model(
        path,
        EvidencePacket,
        schema_name="EvidencePacket",
    )


def _load_evidence_claim_artifact(path: Path) -> EvidenceClaim:
    data = load_json_object(path, schema_name="EvidenceClaim")
    require_schema_version(data, schema_name="EvidenceClaim", path=path)
    require_schema_versioned_items(
        data.get("evidence"),
        schema_name="EvidenceHandle",
        path=path,
    )
    return EvidenceClaim.model_validate(data)


def _manifest_scope_blockers(
    manifest: EvidenceTransactionManifest,
    *,
    index_path: Path,
    manifest_path: Path,
) -> list[str]:
    blockers: list[str] = []
    if Path(manifest.index_path).resolve() != index_path.resolve():
        blockers.append("transaction manifest index path does not match active index")
    expected_transaction_id = manifest_path.parent.name
    if manifest.transaction_id != expected_transaction_id:
        blockers.append("transaction manifest ID does not match manifest directory")
    return blockers


def _indexed_transaction_manifests(
    index_path: str | Path,
    *,
    root: str | Path,
) -> Iterator[tuple[EvidenceTransactionManifest, list[str], Path | None]]:
    index = load_evidence_index(index_path)
    root_path = Path(root).resolve()
    for event in index.events:
        if event.event_type != EVIDENCE_TRANSACTION_EVENT:
            continue
        manifest_path = event.payload.get("manifest_path")
        expected_checksum = event.payload.get("manifest_checksum_sha256")
        blockers: list[str] = []
        if not isinstance(manifest_path, str):
            blockers.append("indexed transaction is missing manifest path")
            yield _empty_manifest(), blockers, None
            continue
        if not isinstance(expected_checksum, str):
            blockers.append("indexed transaction is missing manifest checksum")
            yield _empty_manifest(), blockers, None
            continue
        path = Path(manifest_path)
        if not path.exists():
            blockers.append(f"indexed transaction manifest is missing: {manifest_path}")
            yield _empty_manifest(), blockers, path
            continue
        if _sha256_file(path) != expected_checksum:
            blockers.append(f"indexed transaction manifest checksum mismatch: {manifest_path}")
            yield _empty_manifest(), blockers, path
            continue
        if not _path_is_under(path, root_path):
            blockers.append(f"indexed transaction manifest escapes root: {manifest_path}")
            transaction_id = event.payload.get("transaction_id")
            yield _empty_manifest(
                transaction_id if isinstance(transaction_id, str) else ""
            ), blockers, path
            continue
        try:
            manifest = _load_transaction_manifest(path)
        except (SchemaVersionError, ValidationError) as exc:
            blockers.append(str(exc))
            transaction_id = event.payload.get("transaction_id")
            yield _empty_manifest(
                transaction_id if isinstance(transaction_id, str) else ""
            ), blockers, path
            continue
        scope_blockers = _manifest_scope_blockers(
            manifest,
            index_path=Path(index_path),
            manifest_path=path,
        )
        if scope_blockers:
            blockers.extend(scope_blockers)
            yield manifest, blockers, path
            continue
        yield manifest, blockers, path


def _indexed_manifest_paths(index_path: str | Path) -> list[str]:
    index = load_evidence_index(index_path)
    paths: list[str] = []
    for event in index.events:
        if event.event_type != EVIDENCE_TRANSACTION_EVENT:
            continue
        manifest_path = event.payload.get("manifest_path")
        if isinstance(manifest_path, str):
            paths.append(manifest_path)
    return paths


def _manifest_artifact_blockers(
    manifest: EvidenceTransactionManifest,
    *,
    manifest_path: Path | None,
) -> list[str]:
    blockers: list[str] = []
    transaction_dir = manifest_path.parent.resolve() if manifest_path is not None else None
    for artifact in [*manifest.packets, *manifest.claims]:
        path = Path(artifact.path)
        checksum_path = Path(artifact.checksum_path)
        if transaction_dir is None:
            blockers.append("transaction manifest path is required for artifact validation")
            continue
        if not _path_is_under(path, transaction_dir):
            blockers.append(f"{artifact.artifact_type} path escapes transaction: {artifact.path}")
            continue
        if not _path_is_under(checksum_path, transaction_dir):
            blockers.append(
                f"{artifact.artifact_type} checksum path escapes transaction: "
                f"{artifact.checksum_path}"
            )
            continue
        if checksum_path != path.with_suffix(path.suffix + ".sha256"):
            blockers.append(f"{artifact.artifact_type} checksum path is not canonical")
            continue
        if not path.exists():
            blockers.append(f"{artifact.artifact_type} is missing: {artifact.path}")
            continue
        if not checksum_path.exists():
            blockers.append(f"{artifact.artifact_type} checksum is missing: {artifact.path}")
            continue
        expected_checksum = checksum_path.read_text().strip()
        actual_checksum = _sha256_file(path)
        if (
            expected_checksum != artifact.checksum_sha256
            or actual_checksum != artifact.checksum_sha256
        ):
            blockers.append(f"{artifact.artifact_type} checksum mismatch: {artifact.path}")
            continue
        blockers.extend(_artifact_schema_blockers(artifact, path, manifest=manifest))
    blockers.extend(
        _manifest_claim_link_blockers(
            manifest,
            packet_ids={artifact.artifact_id for artifact in manifest.packets},
        )
    )
    return _dedupe(blockers)


def _manifest_claim_link_blockers(
    manifest: EvidenceTransactionManifest,
    *,
    packet_ids: set[str],
) -> list[str]:
    blockers: list[str] = []
    packets_by_id: dict[str, EvidencePacket] = {}
    for artifact in manifest.packets:
        try:
            packet = _load_evidence_packet_artifact(Path(artifact.path))
        except (SchemaVersionError, ValidationError, OSError):
            continue
        packets_by_id[packet.evidence_id] = packet
    for artifact in manifest.claims:
        try:
            claim = _load_evidence_claim_artifact(Path(artifact.path))
        except (SchemaVersionError, ValidationError, OSError):
            continue
        blockers.extend(
            _claim_packet_link_blockers(
                [claim],
                packet_ids=packet_ids,
                packets_by_id=packets_by_id,
                claim_label=artifact.path,
            )
        )
    return blockers


def _claim_packet_link_blockers(
    claims: list[EvidenceClaim],
    *,
    packet_ids: set[str],
    packets_by_id: dict[str, EvidencePacket] | None = None,
    claim_label: str = "",
) -> list[str]:
    blockers: list[str] = []
    for claim in claims:
        label = claim_label or claim.claim_id
        if not claim.evidence:
            blockers.append(f"claim has no evidence handles: {label}")
            continue
        for handle in claim.evidence:
            if handle.evidence_id not in packet_ids:
                blockers.append(
                    f"claim evidence handle is not in transaction packets: {label}"
                )
                continue
            if packets_by_id is not None and handle.evidence_id in packets_by_id:
                blockers.extend(
                    _claim_packet_scope_blockers(
                        claim,
                        handle=handle,
                        packet=packets_by_id[handle.evidence_id],
                        label=label,
                    )
                )
    return blockers


def _claim_packet_scope_blockers(
    claim: EvidenceClaim,
    *,
    handle: object,
    packet: EvidencePacket,
    label: str,
) -> list[str]:
    if not _is_pose_claim(claim):
        return []
    return _pose_claim_packet_blockers(claim, handle=handle, packet=packet, label=label)


def _is_pose_claim(claim: EvidenceClaim) -> bool:
    return claim.claim_type == POSE_UPRIGHT_CLAIM or claim.claim_type.startswith(
        POSE_ORIENTATION_CLAIM_PREFIX
    )


def _pose_claim_packet_blockers(
    claim: EvidenceClaim,
    *,
    handle: object,
    packet: EvidencePacket,
    label: str,
) -> list[str]:
    blockers: list[str] = []
    if getattr(handle, "source_kind", None) != packet.source_kind:
        blockers.append(f"pose claim evidence handle source does not match packet: {label}")
    if getattr(handle, "path", "") != packet.artifact_path:
        blockers.append(f"pose claim evidence handle path does not match packet: {label}")
    if getattr(handle, "checksum_sha256", "") != packet.checksum_sha256:
        blockers.append(f"pose claim evidence handle checksum does not match packet: {label}")
    if getattr(handle, "quality", None) != packet.quality:
        blockers.append(f"pose claim evidence handle quality does not match packet: {label}")
    if claim.method != POSE_EVIDENCE_METHOD:
        blockers.append(f"pose claim method does not match packet derivation: {label}")
    if claim.quality != EvidenceQuality.USABLE or packet.quality != EvidenceQuality.USABLE:
        blockers.append(f"pose claim and packet must both be usable: {label}")
    if claim.session_id != packet.session_id:
        blockers.append(f"pose claim session does not match packet: {label}")
    if claim.fixture_load_name != packet.fixture_load_name:
        blockers.append(f"pose claim fixture does not match packet: {label}")
    if claim.fixture_params_sha256 != packet.fixture_params_sha256:
        blockers.append(f"pose claim fixture params checksum does not match packet: {label}")
    if claim.labware_definition_sha256 != packet.labware_definition_sha256:
        blockers.append(f"pose claim labware checksum does not match packet: {label}")
    if claim.pose_digest_sha256 != packet.pose_digest_sha256:
        blockers.append(f"pose claim pose digest does not match packet: {label}")
    if packet.payload.get("pose_digest_sha256") != claim.pose_digest_sha256:
        blockers.append(f"pose packet payload digest does not match claim: {label}")
    if claim.claim_type == POSE_UPRIGHT_CLAIM:
        if packet.source_kind != EvidenceSourceKind.FIXTURE_UPRIGHT:
            blockers.append(f"upright claim source does not match packet: {label}")
        upright_value = packet.payload.get(
            "fixture_upright",
            packet.payload.get("upright", packet.payload.get("value")),
        )
        if upright_value is not True:
            blockers.append(f"upright packet did not assert true value: {label}")
        return blockers

    if packet.source_kind != EvidenceSourceKind.FIXTURE_POSE_ORIENTATION:
        blockers.append(f"orientation claim source does not match packet: {label}")
    orientation = packet.payload.get("orientation")
    slot = packet.payload.get("slot")
    expected_claim_type = (
        f"{POSE_ORIENTATION_CLAIM_PREFIX}{orientation}:slot-{slot}:"
        f"{packet.labware_definition_sha256}"
    )
    if claim.claim_type != expected_claim_type:
        blockers.append(f"orientation claim type does not match packet payload: {label}")
    if packet.payload.get("value") is not True:
        blockers.append(f"orientation packet did not assert true value: {label}")
    return blockers


def _packet_external_artifact_blockers(
    packet: EvidencePacket,
    *,
    index_path: str | Path | None = None,
) -> list[str]:
    if packet.source_kind not in {
        EvidenceSourceKind.FIXTURE_POSE_ORIENTATION,
        EvidenceSourceKind.FIXTURE_UPRIGHT,
    }:
        return []
    if packet.quality != EvidenceQuality.USABLE:
        return []
    blockers = _external_file_checksum_blockers(
        path=packet.artifact_path,
        checksum_sha256=packet.checksum_sha256,
        label=f"external evidence artifact {packet.evidence_id}",
    )
    blockers.extend(_fixture_pose_artifact_payload_blockers(packet, index_path=index_path))
    blockers.extend(
        _payload_file_checksum_blockers(
            packet,
            path_key="image_path",
            checksum_key="image_checksum_sha256",
            label="fixture pose evidence image",
        )
    )
    if (
        packet.payload.get("vision_result_path")
        or packet.payload.get("vision_result_checksum_sha256")
    ):
        blockers.extend(
            _payload_file_checksum_blockers(
                packet,
                path_key="vision_result_path",
                checksum_key="vision_result_checksum_sha256",
                label="fixture pose evidence vision result",
            )
        )
    return blockers


def _fixture_pose_artifact_payload_blockers(
    packet: EvidencePacket,
    *,
    index_path: str | Path | None,
) -> list[str]:
    try:
        data = load_json_object(
            packet.artifact_path,
            schema_name="FixturePoseEvidenceArtifact",
        )
    except (OSError, ValueError, TypeError) as exc:
        return [f"fixture pose evidence artifact cannot be loaded: {exc}"]

    blockers: list[str] = []
    _require_artifact_field(data, "schema_version", 1, blockers)
    _require_artifact_field(data, "session_id", packet.session_id, blockers)
    _require_artifact_field(data, "robot_serial", packet.robot_serial, blockers)
    _require_artifact_field(
        data,
        "robot_server_version",
        packet.robot_server_version,
        blockers,
    )
    _require_artifact_field(data, "fixture_load_name", packet.fixture_load_name, blockers)
    _require_artifact_field(
        data,
        "fixture_params_sha256",
        packet.fixture_params_sha256,
        blockers,
    )
    _require_artifact_field(
        data,
        "labware_definition_sha256",
        packet.labware_definition_sha256,
        blockers,
    )
    _require_artifact_field(data, "pose_digest_sha256", packet.pose_digest_sha256, blockers)
    _require_artifact_field(data, "quality", packet.quality.value, blockers)
    if not str(data.get("inspection_note", "")).strip():
        blockers.append("fixture pose evidence artifact inspection note is required")
    _require_artifact_field(
        data,
        "image_path",
        packet.payload.get("image_path"),
        blockers,
    )
    _require_artifact_field(
        data,
        "image_checksum_sha256",
        packet.payload.get("image_checksum_sha256"),
        blockers,
    )
    _require_artifact_field(
        data,
        "image_captured_at",
        packet.payload.get("image_captured_at"),
        blockers,
    )
    _require_artifact_field(
        data,
        "image_capture_robot_url",
        packet.payload.get("image_capture_robot_url"),
        blockers,
    )
    _require_artifact_field(
        data,
        "image_capture_endpoint",
        packet.payload.get("image_capture_endpoint"),
        blockers,
    )
    _require_artifact_field(
        data,
        "image_capture_checksum_sha256",
        packet.payload.get("image_capture_checksum_sha256"),
        blockers,
    )
    if data.get("image_capture_checksum_sha256") != data.get("image_checksum_sha256"):
        blockers.append("fixture pose evidence artifact image capture checksum is stale")
    blockers.extend(
        _camera_capture_event_blockers(data, packet=packet, index_path=index_path)
    )
    _require_artifact_field(
        data,
        "vision_result_path",
        packet.payload.get("vision_result_path", ""),
        blockers,
    )
    _require_artifact_field(
        data,
        "vision_result_checksum_sha256",
        packet.payload.get("vision_result_checksum_sha256", ""),
        blockers,
    )
    if packet.source_kind == EvidenceSourceKind.FIXTURE_POSE_ORIENTATION:
        _require_artifact_field(
            data,
            "observed_orientation",
            packet.payload.get("orientation"),
            blockers,
        )
        _require_artifact_field(data, "slot", packet.payload.get("slot"), blockers)
        if packet.payload.get("value") is not True:
            blockers.append("fixture pose orientation packet did not assert true value")
    elif packet.source_kind == EvidenceSourceKind.FIXTURE_UPRIGHT:
        _require_artifact_field(
            data,
            "fixture_upright",
            packet.payload.get("fixture_upright"),
            blockers,
        )
        if packet.payload.get("fixture_upright") is not True:
            blockers.append("fixture upright packet did not assert true value")
    return blockers


def _require_artifact_field(
    data: dict[str, object],
    field: str,
    expected: object,
    blockers: list[str],
) -> None:
    if data.get(field) != expected:
        blockers.append(f"fixture pose evidence artifact {field} does not match packet")


def _camera_capture_event_blockers(
    data: dict[str, object],
    *,
    packet: EvidencePacket,
    index_path: str | Path | None,
) -> list[str]:
    if index_path is None:
        return ["fixture pose evidence camera capture index is required"]
    try:
        index = load_evidence_index(index_path)
    except (OSError, SchemaVersionError, ValidationError):
        return ["fixture pose evidence camera capture index cannot be loaded"]
    for event in index.events:
        if event.event_type != "ot2_camera_picture":
            continue
        if event.session_id != packet.session_id:
            continue
        payload = event.payload
        if (
            _same_path(payload.get("image_path"), data.get("image_path"))
            and payload.get("image_checksum_sha256") == data.get("image_checksum_sha256")
            and payload.get("captured_at") == data.get("image_captured_at")
            and payload.get("robot_url") == data.get("image_capture_robot_url")
            and payload.get("endpoint") == data.get("image_capture_endpoint")
        ):
            return []
    return ["fixture pose evidence camera capture is not indexed in the active session"]


def _payload_file_checksum_blockers(
    packet: EvidencePacket,
    *,
    path_key: str,
    checksum_key: str,
    label: str,
) -> list[str]:
    path = packet.payload.get(path_key)
    checksum = packet.payload.get(checksum_key)
    if not isinstance(path, str) or not isinstance(checksum, str):
        return [f"{label} path and checksum are required: {packet.evidence_id}"]
    return _external_file_checksum_blockers(
        path=path,
        checksum_sha256=checksum,
        label=f"{label} {packet.evidence_id}",
    )


def _external_file_checksum_blockers(
    *,
    path: str,
    checksum_sha256: str,
    label: str,
) -> list[str]:
    if not path or not checksum_sha256:
        return [f"{label} path and checksum are required"]
    external_path = Path(path)
    if not external_path.is_file():
        return [f"{label} is missing: {path}"]
    if _sha256_file(external_path) != checksum_sha256:
        return [f"{label} checksum mismatch: {path}"]
    return []


def _artifact_schema_blockers(
    artifact: EvidenceTransactionArtifact,
    path: Path,
    *,
    manifest: EvidenceTransactionManifest,
) -> list[str]:
    blockers: list[str] = []
    try:
        if artifact.artifact_type == "packet":
            model = _load_evidence_packet_artifact(path)
            artifact_id = model.evidence_id
            session_id = model.session_id
            blockers.extend(
                _packet_external_artifact_blockers(
                    model,
                    index_path=manifest.index_path,
                )
            )
        else:
            model = _load_evidence_claim_artifact(path)
            artifact_id = model.claim_id
            session_id = model.session_id
    except (SchemaVersionError, ValidationError, OSError) as exc:
        return [str(exc)]

    if artifact_id != artifact.artifact_id:
        blockers.append(
            f"{artifact.artifact_type} artifact ID does not match payload: {artifact.path}"
        )
    if manifest.session_id and session_id != manifest.session_id:
        blockers.append(
            f"{artifact.artifact_type} session ID does not match manifest: {artifact.path}"
        )
    if session_id and not manifest.session_id:
        blockers.append(
            f"{artifact.artifact_type} has session ID but manifest is unscoped: {artifact.path}"
        )
    return blockers


def _path_is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent)
    except ValueError:
        return False
    return True


def _empty_manifest(transaction_id: str = "") -> EvidenceTransactionManifest:
    return EvidenceTransactionManifest(transaction_id=transaction_id, index_path="")


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


