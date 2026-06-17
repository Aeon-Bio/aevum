"""OT-1: transaction-backed offset authority — evidence -> claim -> (gated) promoted offset.

This is the producer the offset gate was missing: `offset_match_gate` (registry.py) trusts an
``OffsetRecord`` in ``authority_state=PROMOTED`` as an INPUT to motion, but nothing ever set
PROMOTED. OT-1 builds that path: it records the attested offset measurement as a durable
committed evidence claim, and `promoted_offset_record` is the terminal trust boundary that may
flip a PROPOSED record to PROMOTED — but ONLY after a fail-closed join of four independent
facts.

SAFETY MODEL (builder decision: "pipeline only, PROMOTED blocked"):

- ``CALIBRATED_OFFSET_SOURCES`` is a safe-allowlist of offset sources trusted to PROMOTE. It is
  EMPTY today: high-Z vision is uncalibrated and OT-6's "post-motion" is only a timestamp, so
  there is no trustworthy machine source for the x/y/z delta yet. An operator-attested offset
  may be RECORDED as evidence, but it MUST NOT promote until a calibrated source is deliberately
  added here. So the full machinery is built, tested, and ready, yet promotion is currently
  unreachable by construction (mirrors the SMIS source-enable safe-allowlist).

- Promotion JOINS, never trusts one packet: (a) a scope-valid OFFSET_MEASUREMENT claim, (b) the
  prerequisite OT-6 ``high_z_motion_completed`` claim re-fetched from the COMMITTED store (never
  caller-supplied), (c) that move re-reconciled against the LIVE command journal NOW (catches a
  stalled motor that merely reported success at OT-6 build time), and (d) the calibration gate.
  Remove any one and promotion is blocked.

OT-1 is a PRODUCER. It never sets ``motion_allowed``, never mints/arms/consumes a
``MotionApproval`` (the sole motion-permission minter is ``motion_commissioning``), and never
emits an authorizing ``GateResult``. It stops at "committed claim (+ optionally a PROMOTED
record)". Motion authority still comes only from the separate arm/consume flow over the gate.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, model_validator

from aevum_ot2.core.command_journal import (
    DEFAULT_STATE_DB,
    CommandReconciliationResult,
    read_command_journal_entry,
    reconcile_command_history,
)
from aevum_ot2.core.evidence import (
    EvidenceTransactionCommitResult,
    commit_evidence_transaction,
    load_committed_evidence_claims,
)
from aevum_ot2.core.evidence_primitives import (
    _is_timezone_aware,
    _sha256_file,
    _transaction_root_for_index,
)
from aevum_ot2.core.models import (
    BridgeSession,
    EndpointResult,
    EvidenceClaim,
    EvidenceHandle,
    EvidencePacket,
    EvidenceQuality,
    EvidenceSourceKind,
    OffsetAuthorityState,
    OffsetRecord,
)
from aevum_ot2.core.records import (
    HIGH_Z_MOTION_EVIDENCE_METHOD,
    OFFSET_EVIDENCE_METHOD,
    TARGET_CLASS_BY_NAME,
    high_z_motion_completed_claim_id,
    high_z_motion_completed_claim_type,
    offset_measured_claim_id,
    offset_measured_claim_type,
)
from aevum_ot2.core.schema import (
    SchemaVersionError,
    load_json_object,
    parse_versioned_json_model,
)

OFFSET_EVIDENCE_ARTIFACT_VERSION = 1
OFFSET_MEASUREMENT_SOURCE_KINDS = {EvidenceSourceKind.OFFSET_MEASUREMENT}

# SAFE-ALLOWLIST of offset sources trusted to PROMOTE an OffsetRecord. EMPTY by design: no
# calibrated machine source for the offset vector exists yet, so promotion is currently
# unreachable. Adding a member here is a deliberate, reviewed act that turns the (already-built,
# already-tested) promotion machinery on for that source. "operator_attested_jog" is NOT here.
CALIBRATED_OFFSET_SOURCES: frozenset[str] = frozenset()

# Command-reconciliation states/statuses that prove the high-Z move actually completed LIVE.
_LIVE_RECONCILED_STATE = "completed"
_LIVE_SUCCESS_STATUSES = frozenset({"succeeded", "completed"})

__all__ = [
    "OFFSET_EVIDENCE_ARTIFACT_VERSION",
    "OFFSET_MEASUREMENT_SOURCE_KINDS",
    "CALIBRATED_OFFSET_SOURCES",
    "OffsetEvidenceArtifact",
    "build_offset_evidence_artifact",
    "write_offset_evidence_artifact",
    "load_offset_evidence_artifact",
    "offset_evidence_artifact_scope_reasons",
    "offset_evidence_packets_from_artifact",
    "commit_offset_claims",
    "commit_offset_evidence_artifact",
    "promoted_offset_record",
]


class OffsetEvidenceArtifact(BaseModel):
    schema_version: int = OFFSET_EVIDENCE_ARTIFACT_VERSION
    artifact_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    session_id: str
    # scope identity (mirrors the OffsetRecord scope offset_match_gate re-checks)
    robot_serial: str = ""
    robot_server_version: str = ""
    opentrons_api_version: str = ""
    fixture_load_name: str
    fixture_definition_uri: str = ""
    fixture_params_sha256: str
    labware_definition_sha256: str
    pose_digest_sha256: str = ""
    slot: str
    pipette_name: str = ""
    pipette_mount: str = ""
    tiprack_load_name: str = ""
    target_class: str
    safety_profile_sha256: str = ""
    target_policy_digest_sha256: str = ""
    # the measured/attested offset and its provenance
    offset_mm: dict[str, float]
    offset_source: str
    measurement_method: str = ""
    # OT-6 command binding — lets promotion re-read the LIVE journal (run_id alone won't do)
    high_z_journal_id: str = ""
    high_z_command_id: str = ""
    high_z_command_key: str = ""
    high_z_run_id: str = ""
    high_z_evidence_id: str = ""
    # optional post-motion frame pointer (not load-bearing while vision is uncalibrated)
    image_path: str = ""
    image_checksum_sha256: str = ""
    inspection_note: str = ""
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_artifact(self) -> OffsetEvidenceArtifact:
        if self.schema_version != OFFSET_EVIDENCE_ARTIFACT_VERSION:
            raise ValueError("unsupported offset evidence artifact schema version")
        if not self.artifact_id.strip():
            raise ValueError("offset evidence artifact_id is required")
        if not self.session_id.strip():
            raise ValueError("offset evidence session_id is required")
        if self.target_class not in TARGET_CLASS_BY_NAME:
            raise ValueError(f"unknown target class: {self.target_class}")
        if _is_timezone_aware(self.created_at):
            raise ValueError("offset evidence created_at must be timezone-naive")
        if set(self.offset_mm) != {"x", "y", "z"}:
            raise ValueError("offset evidence offset_mm must have exactly keys x, y, z")
        if not all(math.isfinite(v) for v in self.offset_mm.values()):
            raise ValueError("offset evidence offset_mm values must be finite")
        if self.image_path and self.image_checksum_sha256 == "":
            raise ValueError("offset evidence image path requires a checksum")
        if self.quality == EvidenceQuality.USABLE:
            if not self.inspection_note.strip():
                raise ValueError("usable offset evidence requires an inspection note")
            if not self.offset_source.strip():
                raise ValueError("usable offset evidence requires an offset_source")
            if not self.high_z_journal_id.strip():
                raise ValueError(
                    "usable offset evidence requires high_z_journal_id (to re-reconcile the move)"
                )
        return self


def build_offset_evidence_artifact(
    record: OffsetRecord,
    *,
    session: BridgeSession,
    artifact_id: str,
    offset_source: str,
    inspection_note: str,
    high_z_journal_id: str,
    high_z_command_id: str = "",
    high_z_command_key: str = "",
    high_z_run_id: str = "",
    high_z_evidence_id: str = "",
    measurement_method: str = "",
    image_path: str | Path | None = None,
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS,
    notes: list[str] | None = None,
) -> OffsetEvidenceArtifact:
    """Build the offset evidence artifact from a PROPOSED OffsetRecord (the offset/scope source).

    The offset vector and full scope are taken FROM the record (its required fields); this only
    re-attests them with provenance (offset_source + inspection_note) and binds the OT-6 command
    so promotion can re-reconcile it. The command binding is supplied by the caller; it is never
    synthesized here.
    """
    image = Path(image_path) if image_path is not None else None
    image_checksum = _sha256_file(image) if image is not None else ""
    return OffsetEvidenceArtifact(
        artifact_id=artifact_id,
        session_id=session.session_id,
        robot_serial=record.robot_serial,
        robot_server_version=record.robot_server_version or "",
        opentrons_api_version=record.opentrons_api_version or "",
        fixture_load_name=record.fixture_load_name,
        fixture_definition_uri=record.fixture_definition_uri,
        fixture_params_sha256=record.fixture_params_sha256,
        labware_definition_sha256=record.labware_definition_sha256,
        pose_digest_sha256=record.pose_digest_sha256,
        slot=record.slot,
        pipette_name=record.pipette_name,
        pipette_mount=record.pipette_mount,
        tiprack_load_name=record.tiprack_load_name,
        target_class=_record_target_class(record),
        safety_profile_sha256=record.safety_profile_sha256,
        target_policy_digest_sha256=record.target_policy_digest_sha256,
        offset_mm=dict(record.offset_mm),
        offset_source=offset_source,
        measurement_method=measurement_method,
        high_z_journal_id=high_z_journal_id,
        high_z_command_id=high_z_command_id,
        high_z_command_key=high_z_command_key,
        high_z_run_id=high_z_run_id,
        high_z_evidence_id=high_z_evidence_id,
        image_path=str(image) if image is not None else "",
        image_checksum_sha256=image_checksum,
        inspection_note=inspection_note,
        quality=quality,
        notes=notes or [],
    )


def write_offset_evidence_artifact(
    artifact: OffsetEvidenceArtifact,
    path: str | Path,
) -> Path:
    artifact_path = Path(path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = artifact_path.with_suffix(artifact_path.suffix + ".tmp")
    tmp.write_text(artifact.model_dump_json(indent=2) + "\n")
    tmp.replace(artifact_path)
    return artifact_path


def load_offset_evidence_artifact(path: str | Path) -> OffsetEvidenceArtifact:
    data = load_json_object(path, schema_name="OffsetEvidenceArtifact")
    return parse_versioned_json_model(
        data,
        OffsetEvidenceArtifact,
        schema_name="OffsetEvidenceArtifact",
        path=path,
    )


def offset_evidence_artifact_scope_reasons(
    record: OffsetRecord,
    *,
    session: BridgeSession,
    artifact_path: str | Path,
) -> list[str]:
    path = Path(artifact_path)
    try:
        artifact = load_offset_evidence_artifact(path)
    except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
        return [f"offset evidence artifact is invalid: {exc}"]
    return _artifact_scope_reasons(record, artifact, session=session, artifact_path=path)


# Denormalized artifact fields carried in the packet payload — ONE table drives BOTH the build
# and the verify so a forgotten field cannot silently stop being checked (fail-closed).
_OFFSET_PAYLOAD_FIELDS: tuple[
    tuple[str, Callable[[OffsetEvidenceArtifact], object]], ...
] = (
    ("target_class", lambda a: a.target_class),
    ("pose_digest_sha256", lambda a: a.pose_digest_sha256),
    ("slot", lambda a: a.slot),
    ("offset_mm", lambda a: a.offset_mm),
    ("offset_source", lambda a: a.offset_source),
    ("measurement_method", lambda a: a.measurement_method),
    ("high_z_journal_id", lambda a: a.high_z_journal_id),
    ("high_z_command_id", lambda a: a.high_z_command_id),
    ("high_z_command_key", lambda a: a.high_z_command_key),
    ("high_z_run_id", lambda a: a.high_z_run_id),
    ("high_z_evidence_id", lambda a: a.high_z_evidence_id),
    ("robot_serial", lambda a: a.robot_serial),
    ("robot_server_version", lambda a: a.robot_server_version),
    ("opentrons_api_version", lambda a: a.opentrons_api_version),
    ("fixture_load_name", lambda a: a.fixture_load_name),
    ("fixture_definition_uri", lambda a: a.fixture_definition_uri),
    ("fixture_params_sha256", lambda a: a.fixture_params_sha256),
    ("labware_definition_sha256", lambda a: a.labware_definition_sha256),
    ("pipette_name", lambda a: a.pipette_name),
    ("pipette_mount", lambda a: a.pipette_mount),
    ("tiprack_load_name", lambda a: a.tiprack_load_name),
    ("safety_profile_sha256", lambda a: a.safety_profile_sha256),
    ("target_policy_digest_sha256", lambda a: a.target_policy_digest_sha256),
    ("image_path", lambda a: a.image_path),
    ("image_checksum_sha256", lambda a: a.image_checksum_sha256),
)


def _artifact_payload(artifact: OffsetEvidenceArtifact) -> dict[str, object]:
    payload: dict[str, object] = {key: getter(artifact) for key, getter in _OFFSET_PAYLOAD_FIELDS}
    payload["value"] = True
    return payload


def offset_evidence_packets_from_artifact(
    record: OffsetRecord,
    artifact: OffsetEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: str | Path,
) -> list[EvidencePacket]:
    path = Path(artifact_path)
    blockers = _artifact_scope_reasons(record, artifact, session=session, artifact_path=path)
    if blockers:
        raise ValueError("; ".join(blockers))
    checksum = _sha256_file(path)
    return [
        offset_evidence_packet(
            record,
            session=session,
            evidence_id=f"{artifact.artifact_id}:offset",
            source_kind=EvidenceSourceKind.OFFSET_MEASUREMENT,
            artifact_path=path,
            checksum_sha256=checksum,
            quality=artifact.quality,
            payload=_artifact_payload(artifact),
            notes=artifact.notes,
        )
    ]


def offset_evidence_packet(
    record: OffsetRecord,
    *,
    session: BridgeSession | None = None,
    evidence_id: str,
    source_kind: EvidenceSourceKind = EvidenceSourceKind.OFFSET_MEASUREMENT,
    artifact_path: str | Path = "",
    checksum_sha256: str = "",
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS,
    payload: dict[str, object] | None = None,
    notes: list[str] | None = None,
) -> EvidencePacket:
    """LOW-LEVEL seam — accepts a caller-built payload and bypasses build-time provenance.

    Not part of the public contract; producers use ``offset_evidence_packets_from_artifact``.
    """
    if source_kind not in OFFSET_MEASUREMENT_SOURCE_KINDS:
        raise ValueError(f"unsupported offset evidence source: {source_kind}")
    target_class = _record_target_class(record)
    active_payload: dict[str, object] = {
        "target_class": target_class,
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
        operation="offset_measurement",
        artifact_path=str(Path(artifact_path)) if artifact_path else "",
        checksum_sha256=checksum_sha256,
        payload=active_payload,
        quality=quality,
        notes=notes or [],
    )


def derive_offset_claims(
    record: OffsetRecord,
    evidence_packets: Iterable[EvidencePacket],
    *,
    session: BridgeSession | None = None,
    method: str = OFFSET_EVIDENCE_METHOD,
) -> list[EvidenceClaim]:
    packets = list(evidence_packets)
    offset_packet = _first_offset_packet(packets)
    if offset_packet is None:
        return []
    target_class = _record_target_class(record)
    reasons = _offset_packet_reasons(record, offset_packet, session)
    quality = offset_packet.quality if not reasons else EvidenceQuality.FAILED
    return [
        EvidenceClaim(
            claim_id=offset_measured_claim_id(target_class, offset_packet.evidence_id),
            claim_type=offset_measured_claim_type(target_class),
            value=not reasons,
            created_at=datetime.now(),
            session_id=(
                session.session_id if session is not None else offset_packet.session_id
            ),
            fixture_load_name=record.fixture_load_name,
            fixture_params_sha256=record.fixture_params_sha256,
            labware_definition_sha256=record.labware_definition_sha256,
            pose_digest_sha256=record.pose_digest_sha256,
            method=method,
            quality=quality,
            evidence=[_evidence_handle(offset_packet)],
            reasons=reasons,
        )
    ]


def commit_offset_claims(
    record: OffsetRecord,
    evidence_packets: list[EvidencePacket],
    *,
    session: BridgeSession,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    transaction_id: str | None = None,
) -> EvidenceTransactionCommitResult:
    resolved_index_path = Path(index_path or session.evidence_index_path)
    _require_session_evidence_index(session, resolved_index_path)
    resolved_root = (
        Path(root) if root is not None else _transaction_root_for_index(resolved_index_path)
    )
    claims = derive_offset_claims(record, evidence_packets, session=session)
    return commit_evidence_transaction(
        packets=evidence_packets,
        claims=claims,
        index_path=resolved_index_path,
        root=resolved_root,
        transaction_id=transaction_id,
        session_id=session.session_id,
    )


def commit_offset_evidence_artifact(
    record: OffsetRecord,
    artifact: OffsetEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: str | Path,
    index_path: str | Path | None = None,
    root: str | Path | None = None,
    transaction_id: str | None = None,
) -> EvidenceTransactionCommitResult:
    return commit_offset_claims(
        record,
        offset_evidence_packets_from_artifact(
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


def promoted_offset_record(
    record: OffsetRecord,
    *,
    session: BridgeSession,
    command_history: EndpointResult | None = None,
    command_journal_path: str | Path = DEFAULT_STATE_DB,
    now: datetime | None = None,
) -> OffsetRecord:
    """THE SAFETY CORE. Flip a PROPOSED OffsetRecord to PROMOTED, or raise (fail closed).

    Authority is derived SOLELY from the committed evidence store + the live journal — NOTHING
    is trusted from the caller (a caller-supplied claim object is never consulted). Promotion
    requires ALL of (collected, not short-circuited, so the full blocker set is visible):

    - the scope-valid OFFSET_MEASUREMENT claim re-fetched from the COMMITTED store, whose bound
      artifact is checksum-verified against its committed handle and whose offset_mm matches the
      record (so neither a fabricated/uncommitted claim nor a post-commit tamper of the external
      offset file can promote an unattested vector);
    - the prerequisite OT-6 ``high_z_motion_completed`` claim re-fetched from the COMMITTED store;
    - that move re-reconciled against the LIVE command journal NOW;
    - an offset_source in the (currently empty) ``CALIBRATED_OFFSET_SOURCES`` allowlist.

    With the allowlist empty this always blocks — promotion is unreachable by design until a
    calibrated source is added. The record is returned PROMOTED only on zero blockers.
    """
    target_class = _record_target_class(record)
    blockers: list[str] = []
    blockers.extend(_committed_offset_blockers(record, session=session, target_class=target_class))
    blockers.extend(_committed_high_z_blockers(record, session=session, target_class=target_class))
    blockers.extend(
        _live_journal_blockers(
            record,
            command_history=command_history,
            command_journal_path=command_journal_path,
            now=now,
        )
    )
    if record.offset_source not in CALIBRATED_OFFSET_SOURCES:
        blockers.append("offset_source_not_calibrated")

    if blockers:
        raise ValueError("offset promotion blocked: " + "; ".join(_dedupe(blockers)))

    # Flip to PROMOTED. verification_targets is already the single attested class
    # (_record_target_class), and offset_record_id is a scope hash that excludes
    # authority_state, so the promoted record keeps the same id as the PROPOSED one (the
    # registry upsert relies on this). Full lineage lives in the committed transaction store;
    # the record itself stays slim (OffsetRecord has no EvidenceHandle list by design).
    return record.model_copy(update={"authority_state": OffsetAuthorityState.PROMOTED})


def _committed_offset_blockers(
    record: OffsetRecord,
    *,
    session: BridgeSession,
    target_class: str,
) -> list[str]:
    """Re-fetch the offset_measured claim from the COMMITTED store and bind it to the record.

    Symmetric with ``_committed_high_z_blockers``: never trusts a caller-supplied claim. The
    committed claim must be scope-valid + USABLE, its bound artifact's on-disk bytes must match
    the committed handle checksum (tamper-evident — the external file is mutable), and the
    attested offset_mm must equal the record's (no promoting an unattested vector).
    """
    try:
        index_path = Path(session.evidence_index_path)
        committed = load_committed_evidence_claims(
            index_path=index_path,
            root=_transaction_root_for_index(index_path),
        )
    except (OSError, ValueError, SchemaVersionError, ValidationError) as exc:
        return [f"could not load committed offset claim: {exc}"]
    expected_type = offset_measured_claim_type(target_class)
    for claim in committed:
        if claim.claim_type != expected_type:
            continue
        if claim.value is not True or claim.reasons:
            continue
        if claim.quality != EvidenceQuality.USABLE:
            continue
        if claim.method != OFFSET_EVIDENCE_METHOD:
            continue
        if len(claim.evidence) != 1:
            continue
        handle = claim.evidence[0]
        if handle.source_kind != EvidenceSourceKind.OFFSET_MEASUREMENT:
            continue
        if claim.claim_id != offset_measured_claim_id(target_class, handle.evidence_id):
            continue
        if claim.fixture_load_name != record.fixture_load_name:
            continue
        if claim.fixture_params_sha256 != record.fixture_params_sha256:
            continue
        if claim.labware_definition_sha256 != record.labware_definition_sha256:
            continue
        if claim.pose_digest_sha256 != record.pose_digest_sha256:
            continue
        # tamper-evidence: the external artifact must still hash to the committed handle value
        if not handle.path or not handle.checksum_sha256:
            continue
        artifact_path = Path(handle.path)
        if not artifact_path.is_file():
            continue
        if _sha256_file(artifact_path) != handle.checksum_sha256:
            continue
        try:
            artifact = load_offset_evidence_artifact(artifact_path)
        except (SchemaVersionError, ValidationError, OSError, ValueError):
            continue
        # value binding: the attested offset must equal the record's, for this target
        if artifact.offset_mm != dict(record.offset_mm):
            continue
        if artifact.target_class != target_class:
            continue
        return []
    return ["missing_committed_offset_measurement_claim"]


def _committed_high_z_blockers(
    record: OffsetRecord,
    *,
    session: BridgeSession,
    target_class: str,
) -> list[str]:
    """Re-fetch the OT-6 high_z_motion_completed claim from the COMMITTED store (not caller).

    The offset is only promotable if the move it depends on is itself a committed, scope-valid,
    USABLE high-Z completion claim for the same target class.
    """
    try:
        index_path = Path(session.evidence_index_path)
        committed = load_committed_evidence_claims(
            index_path=index_path,
            root=_transaction_root_for_index(index_path),
        )
    except (OSError, ValueError, SchemaVersionError, ValidationError) as exc:
        return [f"could not load committed high-Z claim: {exc}"]
    expected_type = high_z_motion_completed_claim_type(target_class)
    for claim in committed:
        if claim.claim_type != expected_type:
            continue
        if claim.value is not True or claim.reasons:
            continue
        if claim.quality != EvidenceQuality.USABLE:
            continue
        if claim.method != HIGH_Z_MOTION_EVIDENCE_METHOD:
            continue
        if len(claim.evidence) != 1:
            continue
        handle = claim.evidence[0]
        if handle.source_kind != EvidenceSourceKind.HIGH_Z_LANDING:
            continue
        if claim.claim_id != high_z_motion_completed_claim_id(target_class, handle.evidence_id):
            continue
        # scope-equivalent to the offset record
        if claim.fixture_load_name != record.fixture_load_name:
            continue
        if claim.fixture_params_sha256 != record.fixture_params_sha256:
            continue
        if claim.labware_definition_sha256 != record.labware_definition_sha256:
            continue
        if claim.pose_digest_sha256 != record.pose_digest_sha256:
            continue
        return []
    return ["missing_committed_high_z_motion_claim"]


def _live_journal_blockers(
    record: OffsetRecord,
    *,
    command_history: EndpointResult | None,
    command_journal_path: str | Path,
    now: datetime | None,
) -> list[str]:
    """Re-reconcile the high-Z move against the LIVE journal NOW (catches stalled-then-reported)."""
    if not record.high_z_journal_id.strip():
        return ["high_z_command_binding_missing"]
    entry = read_command_journal_entry(record.high_z_journal_id, path=command_journal_path)
    if entry is None:
        return ["high_z_command_journal_entry_missing"]
    result: CommandReconciliationResult = reconcile_command_history(
        entry, command_history, now=now
    )
    if (
        result.state == _LIVE_RECONCILED_STATE
        and result.matched_status in _LIVE_SUCCESS_STATUSES
        and result.matched_command_is_latest is True
        and result.recovery_required is False
    ):
        return []
    return ["high_z_command_not_reconciled_live"]


def _offset_packet_reasons(
    record: OffsetRecord,
    packet: EvidencePacket,
    session: BridgeSession | None,
) -> list[str]:
    reasons = _packet_scope_reasons(record, packet, session)
    target_class = _record_target_class(record)
    if packet.payload.get("target_class") != target_class:
        reasons.append("offset evidence target_class does not match offset record")
    if packet.payload.get("value") is not True:
        reasons.append("offset evidence did not assert a true observation")
    if packet.payload.get("offset_mm") != dict(record.offset_mm):
        reasons.append("offset evidence offset_mm does not match offset record")
    if not str(packet.payload.get("offset_source", "")).strip():
        reasons.append("offset evidence offset_source is missing")
    if not str(packet.payload.get("high_z_journal_id", "")).strip():
        reasons.append("offset evidence high_z_journal_id is missing")
    return reasons


def _packet_scope_reasons(
    record: OffsetRecord,
    packet: EvidencePacket,
    session: BridgeSession | None,
) -> list[str]:
    reasons: list[str] = []
    if packet.quality != EvidenceQuality.USABLE:
        reasons.append(f"evidence packet is not usable: {packet.evidence_id}")
    elif not _usable_artifact_is_bound(packet):
        reasons.append("usable offset evidence packet must bind an artifact path and checksum")
    elif session is None:
        reasons.append("usable offset evidence packet requires an active session")
    else:
        reasons.extend(_packet_artifact_scope_reasons(record, packet, session=session))
    if session is not None and packet.session_id != session.session_id:
        reasons.append("evidence packet session does not match active session")
    if packet.fixture_load_name != record.fixture_load_name:
        reasons.append("evidence packet fixture does not match offset record")
    if packet.fixture_params_sha256 != record.fixture_params_sha256:
        reasons.append("evidence packet fixture params checksum does not match offset record")
    if packet.labware_definition_sha256 != record.labware_definition_sha256:
        reasons.append("evidence packet labware checksum does not match offset record")
    if packet.pose_digest_sha256 != record.pose_digest_sha256:
        reasons.append("evidence packet pose digest does not match offset record")
    if packet.payload.get("pose_digest_sha256") != record.pose_digest_sha256:
        reasons.append("evidence payload pose digest does not match offset record")
    return reasons


def _packet_artifact_scope_reasons(
    record: OffsetRecord,
    packet: EvidencePacket,
    *,
    session: BridgeSession,
) -> list[str]:
    try:
        artifact = load_offset_evidence_artifact(packet.artifact_path)
    except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
        return [f"usable offset evidence packet artifact is invalid: {exc}"]
    reasons = _artifact_scope_reasons(
        record, artifact, session=session, artifact_path=Path(packet.artifact_path)
    )
    if artifact.quality != packet.quality:
        reasons.append("offset evidence artifact quality does not match packet")
    for key, getter in _OFFSET_PAYLOAD_FIELDS:
        if packet.payload.get(key) != getter(artifact):
            reasons.append(f"offset evidence packet field {key} does not match artifact")
    return reasons


def _artifact_scope_reasons(
    record: OffsetRecord,
    artifact: OffsetEvidenceArtifact,
    *,
    session: BridgeSession,
    artifact_path: Path,
) -> list[str]:
    reasons: list[str] = []
    if not artifact_path.is_file():
        reasons.append(f"offset evidence artifact is missing: {artifact_path}")
    else:
        try:
            loaded = load_offset_evidence_artifact(artifact_path)
        except (SchemaVersionError, ValidationError, OSError, ValueError) as exc:
            reasons.append(f"offset evidence artifact cannot be loaded: {exc}")
        else:
            if loaded.model_dump(mode="json") != artifact.model_dump(mode="json"):
                reasons.append("offset evidence artifact does not match artifact path")

    target_class = _record_target_class(record)
    if session.lease_expires_at <= datetime.now():
        reasons.append("offset evidence session lease is expired")
    if artifact.session_id != session.session_id:
        reasons.append("offset evidence session does not match active session")
    if artifact.fixture_load_name != record.fixture_load_name:
        reasons.append("offset evidence fixture does not match offset record")
    if artifact.fixture_params_sha256 != record.fixture_params_sha256:
        reasons.append("offset evidence fixture params checksum does not match offset record")
    if artifact.labware_definition_sha256 != record.labware_definition_sha256:
        reasons.append("offset evidence labware checksum does not match offset record")
    if artifact.pose_digest_sha256 != record.pose_digest_sha256:
        reasons.append("offset evidence pose digest does not match offset record")
    if artifact.slot != record.slot:
        reasons.append("offset evidence slot does not match offset record")
    if artifact.target_class != target_class:
        reasons.append("offset evidence target does not match offset record")
    if artifact.offset_mm != dict(record.offset_mm):
        reasons.append("offset evidence offset_mm does not match offset record")
    if artifact.image_path or artifact.image_checksum_sha256:
        reasons.extend(
            _file_checksum_reasons(
                path=artifact.image_path,
                checksum_sha256=artifact.image_checksum_sha256,
                label="offset evidence image",
            )
        )
    return reasons


def _record_target_class(record: OffsetRecord) -> str:
    # An offset record is valid for one target class at promote time; verification_targets is
    # the authoritative source. Require exactly one so the claim/scope binding is unambiguous.
    targets = list(record.verification_targets)
    if len(targets) != 1:
        raise ValueError(
            "offset record must declare exactly one verification target to attest/promote; "
            f"got {targets!r}"
        )
    return targets[0]


def _first_offset_packet(packets: list[EvidencePacket]) -> EvidencePacket | None:
    matching = [p for p in packets if p.source_kind in OFFSET_MEASUREMENT_SOURCE_KINDS]
    if not matching:
        return None
    return sorted(matching, key=lambda p: p.created_at, reverse=True)[0]


def _usable_artifact_is_bound(packet: EvidencePacket) -> bool:
    if not packet.artifact_path or not packet.checksum_sha256:
        return False
    path = Path(packet.artifact_path)
    if not path.is_file():
        return False
    return _sha256_file(path) == packet.checksum_sha256


def _file_checksum_reasons(*, path: str, checksum_sha256: str, label: str) -> list[str]:
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


def _require_session_evidence_index(session: BridgeSession, index_path: Path) -> None:
    if index_path.name != "evidence_index.json":
        raise ValueError("offset claim index path must be a session evidence_index.json")
    if index_path.resolve() != Path(session.evidence_index_path).resolve():
        raise ValueError("offset claim index path must match the active session evidence index")


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


