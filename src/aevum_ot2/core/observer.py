"""Observer scan authority: the ``observer_scan`` bridge lease, observer Evidence minting,
and the durable evidence output path.

IN-C4 / HX1. The observer is a *client* of the single-writer OT-2 bridge daemon
(`docs/knowledge/agent_ot2_bridge.md`). It does not run its own motion controller; it
requests a ``kind="observer_scan"`` motion lease that is mutually exclusive with the
pipetting lease (whichever subsystem asks second is refused — proven in tests), and it
emits one immutable ``ObserverScanEvidence`` packet per captured frame. Minting is
fail-closed: no observer evidence exists without a valid observer lease.

IN-C5 / HX2. ``observer_scan_evidence_to_packet`` + ``persist_observer_scan_evidence`` map
the bridge-native observer frames into the durable ``EvidencePacket``/transaction store, and
``module_evidence_to_packet`` + ``persist_module_evidence`` do the same for the generic SMIS
``ModuleEvidence`` (Raman/impedance/etc.) via the ``SensorModuleEvidenceLike`` structural
Protocol — neither core package imports the other. Together they complete the "evidence
output path" the hypergraph requires before any acquisition. Frames are committed as packets
with NO claims — an acquisition record never authorizes motion by itself (the
evidence_model.md design rule).

Authority kept deliberately separate — do NOT merge any of these into one boolean:

- **Lease (software/motion) authority** — this module + ``lock.py``: may the observer hold
  motion authority right now? Mutual exclusion is structural (one non-terminal lock per
  ``robot_url``), so the OT-2 pipetting lease and an observer scan lease cannot coexist.
- **Registration authority** — ``aevum_smis.registration`` / HX2 / IN-C5+C6: is the
  fiducial transform accepted? Carried here only as ``pose_digest_sha256`` *provenance*; a
  frame minted with an empty digest is NOT a claim that registration passed.
- **Hardware enable-line interlock** — HX3 / IN-C7: a physical backstop layered on top of
  the lease (lease released -> enable drops). The software lease does not assert it.
- **Source-enable / condensation** — ``aevum_smis.safety`` / ``aevum_smis.condensation``:
  separate fail-closed gates upstream of acquisition. This module gates only the lease.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol, runtime_checkable

from aevum_ot2.core.evidence import (
    DEFAULT_EVIDENCE_INDEX,
    DEFAULT_EVIDENCE_TRANSACTION_ROOT,
    EvidenceTransactionCommitResult,
    commit_evidence_transaction,
)
from aevum_ot2.core.lock import (
    DEFAULT_STATE_DB,
    LockAcquireResult,
    acquire_lock,
    lease_is_held,
)
from aevum_ot2.core.models import (
    BridgeLeaseKind,
    BridgeLock,
    EvidencePacket,
    EvidenceQuality,
    EvidenceSourceKind,
    ObserverScanEvidence,
)

OBSERVER_SCAN_LEASE_KIND = BridgeLeaseKind.OBSERVER_SCAN
OBSERVER_SCAN_OPERATION = "observer_scan"


@runtime_checkable
class SensorModuleEvidenceLike(Protocol):
    """Structural shape of a SMIS ``ModuleEvidence`` frame the bridge can persist (IN-C5).

    Mirrors ``aevum_smis.driver.ModuleEvidence`` WITHOUT importing it — the same decoupling
    the SMIS side uses in reverse (``MotionLease`` is a Protocol so SMIS never imports the
    bridge). The bridge is the consumer of SMIS evidence, so it owns the structural contract
    it accepts; neither core package depends on the other. This is the conservative resolution
    of the IN-C5 "where the cross-package mapping lives" fork: a structural seam, no import.
    """

    module_serial: str
    manifest_sha256: str
    modality: str
    well_id: str
    payload_kind: str
    payload_ref: str
    lease_owner: str
    session_id: str
    command_id: str
    calibration_ref: str
    captured_at: datetime


class ObserverLeaseError(RuntimeError):
    """Raised when observer evidence is requested without a valid ``observer_scan`` lease."""


def acquire_observer_scan_lease(
    *,
    robot_url: str,
    session_id: str,
    owner_id: str,
    now: datetime,
    lease_minutes: float = 5.0,
    state: str = "active",
    path: str | Path = DEFAULT_STATE_DB,
) -> LockAcquireResult:
    """Request the mutually-exclusive ``observer_scan`` lease from the single-writer bridge.

    Reuses ``acquire_lock`` wholesale: the bridge keeps one non-terminal lock per
    ``robot_url``, so a held pipetting lease (or another observer scan lease) refuses this
    request (``acquired=False``). On refusal, ``result.lock`` is the *holder* — read
    ``result.lock.lease_kind`` to report which subsystem is busy (the ``robot_busy``
    reason). This never grants motion by itself; the hardware enable-line interlock
    (IN-C7) and registration (IN-C5/C6) remain separate gates on top of it.
    """
    lock = BridgeLock(
        robot_url=robot_url,
        session_id=session_id,
        owner_id=owner_id,
        lease_started_at=now,
        lease_expires_at=now + timedelta(minutes=lease_minutes),
        state=state,
        lease_kind=BridgeLeaseKind.OBSERVER_SCAN,
    )
    return acquire_lock(lock, path)


def mint_observer_scan_evidence(
    lease: BridgeLock,
    *,
    evidence_id: str,
    well_id: str,
    focus_z_mm: float,
    focus_metric: float,
    illumination_mode: str,
    now: datetime,
    run_id: str = "",
    pose_digest_sha256: str = "",
    artifact_path: str = "",
    checksum_sha256: str = "",
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS,
    captured_at: datetime | None = None,
) -> ObserverScanEvidence:
    """Mint one observer frame's evidence — fail-closed against the observer lease.

    Refuses with ``ObserverLeaseError`` when the lease is:

    - the **wrong kind** (e.g. a pipetting lease cannot mint observer frames), or
    - **terminal** (closed/failed/released), or
    - **expired** (``lease_expires_at <= now``).

    This is the "no observer acquisition without a valid lease" rule and nothing more: it
    does not assert registration, source-enable, or condensation — those are separate gates
    that run upstream of acquisition. The returned packet binds the frame to the lease
    identity and carries ``pose_digest_sha256`` as registration provenance only.
    """
    if lease.lease_kind != BridgeLeaseKind.OBSERVER_SCAN:
        raise ObserverLeaseError(
            "observer evidence requires an observer_scan lease; "
            f"well {well_id!r} got lease_kind={lease.lease_kind!r}"
        )
    if not lease_is_held(lease, now):
        raise ObserverLeaseError(
            f"observer_scan lease is terminal or expired; cannot mint frame for well {well_id!r}"
        )
    return ObserverScanEvidence(
        evidence_id=evidence_id,
        well_id=well_id,
        focus_z_mm=focus_z_mm,
        focus_metric=focus_metric,
        illumination_mode=illumination_mode,
        captured_at=captured_at if captured_at is not None else now,
        session_id=lease.session_id,
        owner_id=lease.owner_id,
        lease_kind=lease.lease_kind,
        run_id=run_id,
        pose_digest_sha256=pose_digest_sha256,
        artifact_path=artifact_path,
        checksum_sha256=checksum_sha256,
        quality=quality,
    )


def observer_scan_evidence_to_packet(evidence: ObserverScanEvidence) -> EvidencePacket:
    """Map one observer frame into the bridge's durable ``EvidencePacket`` shape (IN-C5).

    Lossless on provenance: the lease binding (owner/kind), the modality numbers, the
    illumination mode, and the fiducial-transform ``pose_digest_sha256`` all survive into the
    durable packet. Per the evidence_model.md design rule, the packet is an indexed,
    checksummed *acquisition record* — NOT a motion authorization. ``OBSERVER_FRAME`` is not
    a pose source kind, so the transaction store does not force an on-disk artifact file:
    a frame whose ``payload_ref`` is a remote GigE capture handle still persists honestly.
    """
    return EvidencePacket(
        evidence_id=evidence.evidence_id,
        source_kind=EvidenceSourceKind.OBSERVER_FRAME,
        created_at=evidence.captured_at,
        session_id=evidence.session_id,
        pose_digest_sha256=evidence.pose_digest_sha256,
        operation=OBSERVER_SCAN_OPERATION,
        command_id=evidence.run_id,
        artifact_path=evidence.artifact_path,
        checksum_sha256=evidence.checksum_sha256,
        provenance={
            "lease_owner": evidence.owner_id,
            "lease_kind": str(evidence.lease_kind),
            "illumination_mode": evidence.illumination_mode,
        },
        payload={
            "well_id": evidence.well_id,
            "focus_z_mm": evidence.focus_z_mm,
            "focus_metric": evidence.focus_metric,
            "illumination_mode": evidence.illumination_mode,
        },
        quality=evidence.quality,
    )


def persist_observer_scan_evidence(
    frames: list[ObserverScanEvidence],
    *,
    index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    root: str | Path = DEFAULT_EVIDENCE_TRANSACTION_ROOT,
    transaction_id: str | None = None,
) -> EvidenceTransactionCommitResult:
    """Durably commit observer frames as one indexed, checksummed evidence transaction (IN-C5).

    Defense in depth: although ``mint_observer_scan_evidence`` already enforces the lease,
    a hand-built ``ObserverScanEvidence`` could carry a non-observer ``lease_kind``; this
    refuses to persist it (``ObserverLeaseError``) so a forged provenance cannot reach the
    durable store. The frames must share one session — the transaction store rejects mixed
    sessions, so a batch spanning two sessions fails closed rather than blurring authority.

    Commits packets only and NO claims: an acquisition record never authorizes motion on its
    own (the evidence_model.md rule), so ``load_committed_evidence_claims`` stays empty until
    a separate gate derives a claim from these packets.
    """
    if not frames:
        raise ValueError("at least one observer frame is required to persist")
    for frame in frames:
        if frame.lease_kind != BridgeLeaseKind.OBSERVER_SCAN:
            raise ObserverLeaseError(
                "refusing to persist a frame not bound to an observer_scan lease; "
                f"frame {frame.evidence_id!r} carries lease_kind={frame.lease_kind!r}"
            )
    packets = [observer_scan_evidence_to_packet(frame) for frame in frames]
    return commit_evidence_transaction(
        packets=packets,
        claims=[],
        index_path=index_path,
        root=root,
        transaction_id=transaction_id,
    )


def _module_evidence_id(evidence: SensorModuleEvidenceLike) -> str:
    """Deterministic id for a SMIS frame (module + modality + well + capture instant)."""
    return (
        f"{evidence.module_serial}:{evidence.modality}:"
        f"{evidence.well_id}:{evidence.captured_at.isoformat()}"
    )


def module_evidence_to_packet(
    evidence: SensorModuleEvidenceLike, *, evidence_id: str | None = None
) -> EvidencePacket:
    """Map a generic SMIS ``ModuleEvidence`` frame into the durable ``EvidencePacket`` (IN-C5).

    The same store and rule as the observer path: ``OBSERVER_FRAME`` source kind (the SMIS
    sensor stage is the observer reframed as a swappable-head carrier), packets only, no
    claims, no motion authority. The modality (brightfield / raman / impedance / ...) rides in
    ``operation`` and ``provenance`` so one query surfaces every modality's acquisitions. The
    DS28E07 ``calibration_ref`` is carried as provenance — its source-enable meaning is a
    separate gate (``aevum_smis.safety``), not re-derived here.
    """
    return EvidencePacket(
        evidence_id=evidence_id or _module_evidence_id(evidence),
        source_kind=EvidenceSourceKind.OBSERVER_FRAME,
        created_at=evidence.captured_at,
        session_id=evidence.session_id,
        operation=evidence.modality,
        command_id=evidence.command_id,
        artifact_path=evidence.payload_ref,
        provenance={
            "module_serial": evidence.module_serial,
            "manifest_sha256": evidence.manifest_sha256,
            "modality": evidence.modality,
            "payload_kind": evidence.payload_kind,
            "lease_owner": evidence.lease_owner,
            "calibration_ref": evidence.calibration_ref,
        },
        payload={
            "well_id": evidence.well_id,
            "modality": evidence.modality,
            "payload_kind": evidence.payload_kind,
        },
    )


def persist_module_evidence(
    frames: list[SensorModuleEvidenceLike],
    *,
    index_path: str | Path = DEFAULT_EVIDENCE_INDEX,
    root: str | Path = DEFAULT_EVIDENCE_TRANSACTION_ROOT,
    transaction_id: str | None = None,
) -> EvidenceTransactionCommitResult:
    """Durably commit SMIS module frames (IN-C5) — the generic counterpart of the observer path.

    Fail-closed: a frame with no ``lease_owner`` did not come from a lease-gated ``run_scan``
    and is refused (defense in depth, mirroring the observer path's lease-kind guard). The
    frames must share one session; the transaction store rejects mixed sessions. Packets only,
    NO claims — a bare acquisition record never authorizes motion.
    """
    if not frames:
        raise ValueError("at least one module frame is required to persist")
    for frame in frames:
        if not frame.lease_owner:
            raise ObserverLeaseError(
                "refusing to persist a module frame with no lease owner "
                f"(well {frame.well_id!r}); it did not come from a lease-gated scan"
            )
    packets = [module_evidence_to_packet(frame) for frame in frames]
    return commit_evidence_transaction(
        packets=packets,
        claims=[],
        index_path=index_path,
        root=root,
        transaction_id=transaction_id,
    )
