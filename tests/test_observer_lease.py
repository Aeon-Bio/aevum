"""IN-C4 / HX1: the observer_scan bridge lease + observer Evidence schema.

Proves the three review obligations the hypergraph names for HX1:
1. mutual exclusion with the OT-2 (pipetting) lease/motion state,
2. fail-closed rejection of a missing / wrong-kind / stale lease at evidence minting,
3. evidence emits a usable handle whose provenance binds it to the lease.

Plus the back-compat migration of a pre-IN-C4 lock DB.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from aevum_ot2.core.evidence import (
    load_committed_evidence_claims,
    scan_evidence_transactions,
)
from aevum_ot2.core.lock import acquire_lock, lease_is_held, read_lock, write_lock
from aevum_ot2.core.models import (
    BridgeLeaseKind,
    BridgeLock,
    EvidencePacket,
    EvidenceQuality,
    EvidenceSourceKind,
    ObserverScanEvidence,
)
from aevum_ot2.core.observer import (
    ObserverLeaseError,
    SensorModuleEvidenceLike,
    acquire_observer_scan_lease,
    mint_observer_scan_evidence,
    module_evidence_to_packet,
    observer_scan_evidence_to_packet,
    persist_module_evidence,
    persist_observer_scan_evidence,
)

ROBOT = "http://ot2.local:31950"
NOW = datetime(2026, 6, 16, 12, 0, 0)
POSE_DIGEST = "a" * 64


def _pipetting_lock(*, state: str = "active_no_motion", expires_in_min: float = 5.0) -> BridgeLock:
    return BridgeLock(
        robot_url=ROBOT,
        session_id="ot2-sess",
        owner_id="pipettor",
        lease_started_at=NOW,
        lease_expires_at=NOW + timedelta(minutes=expires_in_min),
        state=state,
    )


def _observer_lock(*, state: str = "active", expires_in_min: float = 5.0) -> BridgeLock:
    return BridgeLock(
        robot_url=ROBOT,
        session_id="obs-sess",
        owner_id="observer",
        lease_started_at=NOW,
        lease_expires_at=NOW + timedelta(minutes=expires_in_min),
        state=state,
        lease_kind=BridgeLeaseKind.OBSERVER_SCAN,
    )


# --- lease kind + persistence -------------------------------------------------------------


def test_pipetting_lease_kind_is_the_default(tmp_path) -> None:
    db = tmp_path / "state.sqlite3"
    write_lock(_pipetting_lock(), db)
    loaded = read_lock(ROBOT, db)
    assert loaded is not None
    assert loaded.lease_kind == BridgeLeaseKind.PIPETTING == "pipetting"


def test_observer_scan_lease_round_trips_its_kind(tmp_path) -> None:
    db = tmp_path / "state.sqlite3"
    result = acquire_observer_scan_lease(
        robot_url=ROBOT, session_id="obs-sess", owner_id="observer", now=NOW, path=db
    )
    assert result.acquired is True
    loaded = read_lock(ROBOT, db)
    assert loaded is not None
    assert loaded.lease_kind == BridgeLeaseKind.OBSERVER_SCAN == "observer_scan"


# --- mutual exclusion (the HX1 core claim) ------------------------------------------------


def test_pipetting_lease_blocks_observer_scan(tmp_path) -> None:
    db = tmp_path / "state.sqlite3"
    write_lock(_pipetting_lock(), db)  # OT-2 holds the robot

    result = acquire_observer_scan_lease(
        robot_url=ROBOT, session_id="obs-sess", owner_id="observer", now=NOW, path=db
    )

    assert result.acquired is False
    # the refusal names the *holder* so the bridge can report robot_busy:<kind>
    assert result.lock.lease_kind == BridgeLeaseKind.PIPETTING
    assert result.lock.session_id == "ot2-sess"
    # the lock on disk is unchanged: the observer did not steal it
    assert read_lock(ROBOT, db).session_id == "ot2-sess"


def test_observer_scan_lease_blocks_pipetting(tmp_path) -> None:
    db = tmp_path / "state.sqlite3"
    assert acquire_observer_scan_lease(
        robot_url=ROBOT, session_id="obs-sess", owner_id="observer", now=NOW, path=db
    ).acquired is True

    # the OT-2 now asks (a default pipetting BridgeLock) -> refused, observer named
    result = acquire_lock(_pipetting_lock(state="starting"), db)

    assert result.acquired is False
    assert result.lock.lease_kind == BridgeLeaseKind.OBSERVER_SCAN
    assert result.lock.session_id == "obs-sess"


def test_second_observer_scan_lease_is_refused(tmp_path) -> None:
    db = tmp_path / "state.sqlite3"
    assert acquire_observer_scan_lease(
        robot_url=ROBOT, session_id="obs-A", owner_id="observer", now=NOW, path=db
    ).acquired is True

    result = acquire_observer_scan_lease(
        robot_url=ROBOT, session_id="obs-B", owner_id="observer", now=NOW, path=db
    )

    assert result.acquired is False
    assert result.lock.session_id == "obs-A"


def test_terminal_observer_lease_can_be_replaced(tmp_path) -> None:
    db = tmp_path / "state.sqlite3"
    write_lock(_observer_lock(state="released"), db)  # observer released its lease

    # OT-2 may now take the robot (a released lease is not held)
    result = acquire_lock(_pipetting_lock(state="starting"), db)

    assert result.acquired is True
    assert read_lock(ROBOT, db).lease_kind == BridgeLeaseKind.PIPETTING


# --- evidence minting: fail-closed against the lease --------------------------------------


def test_valid_observer_lease_mints_evidence_and_emits_handle(tmp_path) -> None:
    lease = _observer_lock()
    evidence = mint_observer_scan_evidence(
        lease,
        evidence_id="obs-frame-1",
        well_id="A1",
        focus_z_mm=12.34,
        focus_metric=0.91,
        illumination_mode="oblique_below_53deg",
        pose_digest_sha256=POSE_DIGEST,
        run_id="scan-run-1",
        artifact_path="data/measurements/observer/A1.tiff",
        checksum_sha256="c" * 64,
        quality=EvidenceQuality.USABLE,
        now=NOW,
    )

    # provenance binds the frame to the lease that authorized it
    assert evidence.session_id == "obs-sess"
    assert evidence.owner_id == "observer"
    assert evidence.lease_kind == BridgeLeaseKind.OBSERVER_SCAN
    assert evidence.pose_digest_sha256 == POSE_DIGEST

    handle = evidence.to_handle()
    assert handle.source_kind == EvidenceSourceKind.OBSERVER_FRAME
    assert handle.evidence_id == "obs-frame-1"
    assert handle.path == "data/measurements/observer/A1.tiff"
    assert handle.session_id == "obs-sess"
    assert handle.quality == EvidenceQuality.USABLE


def test_mint_rejects_a_pipetting_lease(tmp_path) -> None:
    with pytest.raises(ObserverLeaseError, match="observer_scan lease"):
        mint_observer_scan_evidence(
            _pipetting_lock(),
            evidence_id="x",
            well_id="A1",
            focus_z_mm=1.0,
            focus_metric=1.0,
            illumination_mode="oblique",
            now=NOW,
        )


def test_mint_rejects_an_expired_lease() -> None:
    expired = _observer_lock(expires_in_min=-1.0)
    assert lease_is_held(expired, NOW) is False
    with pytest.raises(ObserverLeaseError, match="terminal or expired"):
        mint_observer_scan_evidence(
            expired,
            evidence_id="x",
            well_id="A1",
            focus_z_mm=1.0,
            focus_metric=1.0,
            illumination_mode="oblique",
            now=NOW,
        )


@pytest.mark.parametrize("state", ["closed", "failed", "released"])
def test_mint_rejects_a_terminal_lease(state: str) -> None:
    terminal = _observer_lock(state=state)
    with pytest.raises(ObserverLeaseError, match="terminal or expired"):
        mint_observer_scan_evidence(
            terminal,
            evidence_id="x",
            well_id="A1",
            focus_z_mm=1.0,
            focus_metric=1.0,
            illumination_mode="oblique",
            now=NOW,
        )


def test_lease_exactly_at_expiry_is_not_held() -> None:
    # boundary: lease_expires_at == now is NOT valid (fail-closed, strict >)
    at_expiry = _observer_lock(expires_in_min=0.0)
    assert lease_is_held(at_expiry, NOW) is False
    with pytest.raises(ObserverLeaseError):
        mint_observer_scan_evidence(
            at_expiry,
            evidence_id="x",
            well_id="A1",
            focus_z_mm=1.0,
            focus_metric=1.0,
            illumination_mode="oblique",
            now=NOW,
        )


# --- registration provenance is carried, not gated ----------------------------------------


def test_evidence_allows_empty_pose_digest_but_validates_format() -> None:
    # An empty digest is allowed at the schema layer: the registration GATE (HX2), not this
    # evidence schema, decides whether a frame may be acquired without a pose. A malformed
    # (non-64-char) digest is rejected so a truncated/garbage checksum cannot masquerade.
    ok = mint_observer_scan_evidence(
        _observer_lock(),
        evidence_id="x",
        well_id="A1",
        focus_z_mm=1.0,
        focus_metric=1.0,
        illumination_mode="oblique",
        now=NOW,
    )
    assert ok.pose_digest_sha256 == ""

    with pytest.raises(ValueError, match="64-character sha256"):
        mint_observer_scan_evidence(
            _observer_lock(),
            evidence_id="x",
            well_id="A1",
            focus_z_mm=1.0,
            focus_metric=1.0,
            illumination_mode="oblique",
            pose_digest_sha256="deadbeef",
            now=NOW,
        )


# --- back-compat migration ----------------------------------------------------------------


def test_pre_inc4_lock_db_migrates_to_pipetting(tmp_path) -> None:
    db = tmp_path / "legacy.sqlite3"
    # build a bridge_locks table in the OLD shape (no lease_kind column) with a live row
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE bridge_locks (
                robot_url TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                lease_started_at TEXT NOT NULL,
                lease_expires_at TEXT NOT NULL,
                active_run_id TEXT,
                last_command_id TEXT,
                state TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO bridge_locks (robot_url, session_id, owner_id, lease_started_at, "
            "lease_expires_at, active_run_id, last_command_id, state) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ROBOT,
                "legacy-sess",
                "pipettor",
                NOW.isoformat(),
                (NOW + timedelta(minutes=5)).isoformat(),
                None,
                None,
                "active_no_motion",
            ),
        )

    loaded = read_lock(ROBOT, db)  # triggers the migration
    assert loaded is not None
    assert loaded.session_id == "legacy-sess"
    assert loaded.lease_kind == "pipetting"


# --- IN-C5: durable evidence output path --------------------------------------------------


def _frame(
    *,
    evidence_id: str = "obs-frame-1",
    well_id: str = "A1",
    session_id: str = "obs-sess",
) -> ObserverScanEvidence:
    lease = _observer_lock()
    lease = lease.model_copy(update={"session_id": session_id})
    return mint_observer_scan_evidence(
        lease,
        evidence_id=evidence_id,
        well_id=well_id,
        focus_z_mm=12.34,
        focus_metric=0.91,
        illumination_mode="oblique_below_53deg",
        pose_digest_sha256=POSE_DIGEST,
        run_id="scan-run-1",
        artifact_path="data/measurements/observer/A1.tiff",
        checksum_sha256="c" * 64,
        quality=EvidenceQuality.USABLE,
        now=NOW,
    )


def test_packet_mapping_preserves_provenance() -> None:
    packet = observer_scan_evidence_to_packet(_frame())
    assert packet.source_kind == EvidenceSourceKind.OBSERVER_FRAME
    assert packet.session_id == "obs-sess"
    assert packet.operation == "observer_scan"
    assert packet.command_id == "scan-run-1"
    assert packet.artifact_path == "data/measurements/observer/A1.tiff"
    assert packet.pose_digest_sha256 == POSE_DIGEST
    assert packet.provenance["lease_owner"] == "observer"
    assert packet.provenance["lease_kind"] == "observer_scan"
    assert packet.payload["well_id"] == "A1"
    assert packet.payload["focus_z_mm"] == 12.34
    assert packet.quality == EvidenceQuality.USABLE


def test_persist_commits_a_clean_indexed_transaction(tmp_path) -> None:
    index_path = tmp_path / "evidence_index.json"
    root = tmp_path / "transactions"
    result = persist_observer_scan_evidence(
        [_frame(evidence_id="obs-frame-1", well_id="A1")],
        index_path=index_path,
        root=root,
        transaction_id="txn-observer-1",
    )

    # the transaction is valid, indexed, and checksum-consistent (no blocker findings)
    scan = scan_evidence_transactions(root=root, index_path=index_path)
    assert [f for f in scan.findings if f.severity == "blocker"] == []
    assert len(result.manifest.packets) == 1
    assert result.manifest.packets[0].artifact_id == "obs-frame-1"

    # the durable packet round-trips with provenance intact
    persisted = EvidencePacket.model_validate(
        json.loads(Path(result.manifest.packets[0].path).read_text())
    )
    assert persisted.source_kind == EvidenceSourceKind.OBSERVER_FRAME
    assert persisted.session_id == "obs-sess"
    assert persisted.pose_digest_sha256 == POSE_DIGEST


def test_persisted_frame_yields_no_claims(tmp_path) -> None:
    # design rule: a bare acquisition record never authorizes motion; no claim is derived.
    index_path = tmp_path / "evidence_index.json"
    root = tmp_path / "transactions"
    persist_observer_scan_evidence(
        [_frame()], index_path=index_path, root=root, transaction_id="txn-no-claim"
    )
    assert load_committed_evidence_claims(index_path=index_path, root=root) == []


def test_persist_refuses_empty_batch(tmp_path) -> None:
    with pytest.raises(ValueError, match="at least one observer frame"):
        persist_observer_scan_evidence(
            [], index_path=tmp_path / "i.json", root=tmp_path / "t"
        )


def test_persist_refuses_a_forged_non_observer_lease_kind(tmp_path) -> None:
    # a hand-built frame claiming a pipetting lease must not reach the durable store
    forged = _frame().model_copy(update={"lease_kind": BridgeLeaseKind.PIPETTING})
    with pytest.raises(ObserverLeaseError, match="not bound to an observer_scan lease"):
        persist_observer_scan_evidence(
            [forged], index_path=tmp_path / "i.json", root=tmp_path / "t"
        )


def test_persist_refuses_mixed_sessions(tmp_path) -> None:
    a = _frame(evidence_id="frame-a", session_id="sess-A")
    b = _frame(evidence_id="frame-b", session_id="sess-B")
    with pytest.raises(ValueError, match="cannot mix session IDs"):
        persist_observer_scan_evidence(
            [a, b], index_path=tmp_path / "i.json", root=tmp_path / "t"
        )


# --- IN-C5 tail: generic SMIS ModuleEvidence -> durable store via the structural Protocol ---


def _module_evidence(
    *, well_id: str = "A1", lease_owner: str = "observer", session_id: str = "obs-sess"
):
    # the REAL aevum_smis type — proves the bridge's structural Protocol matches it without
    # either package importing the other.
    from aevum_smis import ModuleEvidence

    return ModuleEvidence(
        module_serial="SN-0001",
        manifest_sha256="d" * 64,
        modality="raman",
        well_id=well_id,
        payload_kind="spectrum",
        payload_ref=f"data/measurements/observer/{well_id}.spc",
        lease_owner=lease_owner,
        session_id=session_id,
        command_id="cmd-9",
        calibration_ref="ds28e07-digest",
        captured_at=NOW,
    )


def test_real_smis_module_evidence_satisfies_the_bridge_protocol() -> None:
    # the structural seam: the actual SMIS ModuleEvidence is a SensorModuleEvidenceLike
    assert isinstance(_module_evidence(), SensorModuleEvidenceLike)


def test_module_evidence_maps_with_modality_and_cal_provenance() -> None:
    packet = module_evidence_to_packet(_module_evidence())
    assert packet.source_kind == EvidenceSourceKind.OBSERVER_FRAME
    assert packet.operation == "raman"
    assert packet.session_id == "obs-sess"
    assert packet.artifact_path == "data/measurements/observer/A1.spc"
    assert packet.provenance["modality"] == "raman"
    assert packet.provenance["calibration_ref"] == "ds28e07-digest"
    assert packet.provenance["lease_owner"] == "observer"
    # deterministic id includes module/modality/well/capture instant
    assert packet.evidence_id == "SN-0001:raman:A1:" + NOW.isoformat()


def test_persist_module_evidence_commits_cleanly(tmp_path) -> None:
    index_path = tmp_path / "evidence_index.json"
    root = tmp_path / "transactions"
    result = persist_module_evidence(
        [_module_evidence()], index_path=index_path, root=root, transaction_id="txn-mod-1"
    )
    assert result.manifest.packets[0].artifact_id == "SN-0001:raman:A1:" + NOW.isoformat()
    scan = scan_evidence_transactions(root=root, index_path=index_path)
    assert [f for f in scan.findings if f.severity == "blocker"] == []
    # packets only, no motion authority
    assert load_committed_evidence_claims(index_path=index_path, root=root) == []


def test_persist_module_evidence_refuses_a_frame_with_no_lease_owner(tmp_path) -> None:
    orphan = _module_evidence(lease_owner="")
    with pytest.raises(ObserverLeaseError, match="no lease owner"):
        persist_module_evidence(
            [orphan], index_path=tmp_path / "i.json", root=tmp_path / "t"
        )
