from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from aevum_ot2.core.evidence import (
    EVIDENCE_TRANSACTION_EVENT,
    EvidenceTransactionArtifact,
    EvidenceTransactionManifest,
    append_evidence_event,
    append_session_evidence_event,
    commit_evidence_transaction,
    evidence_index_path_for_session,
    load_committed_evidence_claims,
    load_evidence_index,
    scan_evidence_transactions,
)
from aevum_ot2.core.models import (
    EvidenceClaim,
    EvidenceEvent,
    EvidenceHandle,
    EvidencePacket,
    EvidenceQuality,
    EvidenceSourceKind,
)


def test_append_evidence_event_serializes_concurrent_writers(tmp_path: Path) -> None:
    index_path = tmp_path / "evidence_index.json"

    def append_event(event_id: int) -> None:
        append_evidence_event(
            EvidenceEvent(
                event_type="test_concurrent_append",
                session_id="session-1",
                summary=f"event {event_id}",
                payload={"event_id": event_id},
            ),
            path=index_path,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(append_event, range(32)))

    index = load_evidence_index(index_path)

    assert len(index.events) == 32
    assert sorted(event.payload["event_id"] for event in index.events) == list(range(32))


def test_append_session_evidence_event_uses_session_scoped_index(
    tmp_path: Path,
) -> None:
    event = EvidenceEvent(
        event_type="test_session_append",
        summary="session scoped event",
    )

    index = append_session_evidence_event(event, session_id="session/1", root=tmp_path)

    index_path = evidence_index_path_for_session("session/1", root=tmp_path)
    loaded = load_evidence_index(index_path)
    assert index_path == tmp_path / "session_1" / "evidence_index.json"
    assert index.events[0].session_id == "session/1"
    assert loaded.events[0].session_id == "session/1"


def test_append_session_evidence_event_rejects_cross_session_event(
    tmp_path: Path,
) -> None:
    event = EvidenceEvent(
        event_type="test_session_append",
        session_id="session-1",
        summary="session scoped event",
    )

    with pytest.raises(ValueError):
        append_session_evidence_event(event, session_id="session-2", root=tmp_path)


def _packet(evidence_id: str = "packet-1") -> EvidencePacket:
    return EvidencePacket(
        evidence_id=evidence_id,
        source_kind=EvidenceSourceKind.PHYSICAL_MEASUREMENT,
        session_id="session-1",
        operation="fixture_qc",
        quality=EvidenceQuality.USABLE,
        payload={"value": 1},
    )


def _claim(claim_id: str = "claim-1", *, evidence_id: str = "packet-1") -> EvidenceClaim:
    return EvidenceClaim(
        claim_id=claim_id,
        claim_type="fixture_dimensions_within_tolerance",
        value=True,
        session_id="session-1",
        method="unit_test",
        quality=EvidenceQuality.USABLE,
        evidence=[
            EvidenceHandle(
                evidence_id=evidence_id,
                source_kind=EvidenceSourceKind.PHYSICAL_MEASUREMENT,
                quality=EvidenceQuality.USABLE,
            )
        ],
    )


def test_commit_evidence_transaction_writes_indexed_packets_claims_and_checksums(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "evidence_index.json"
    root = tmp_path / "transactions"

    result = commit_evidence_transaction(
        packets=[_packet()],
        claims=[_claim()],
        index_path=index_path,
        root=root,
        transaction_id="txn-1",
    )

    loaded_claims = load_committed_evidence_claims(index_path=index_path, root=root)
    assert result.manifest.status == "committed"
    assert Path(result.manifest.packets[0].path).exists()
    assert Path(result.manifest.packets[0].checksum_path).exists()
    assert Path(result.manifest.claims[0].path).exists()
    assert loaded_claims[0].claim_id == "claim-1"


def test_orphan_transaction_files_do_not_load_as_committed_claims(tmp_path: Path) -> None:
    index_path = tmp_path / "empty_index.json"
    commit_evidence_transaction(
        packets=[_packet()],
        claims=[_claim()],
        index_path=tmp_path / "other_index.json",
        root=tmp_path / "transactions",
        transaction_id="txn-orphan",
    )

    loaded_claims = load_committed_evidence_claims(
        index_path=index_path,
        root=tmp_path / "transactions",
    )
    scan = scan_evidence_transactions(
        root=tmp_path / "transactions",
        index_path=index_path,
    )

    assert loaded_claims == []
    assert any("not indexed" in finding.reason for finding in scan.findings)


def test_indexed_transaction_with_missing_packet_fails_closed(tmp_path: Path) -> None:
    index_path = tmp_path / "evidence_index.json"
    result = commit_evidence_transaction(
        packets=[_packet()],
        claims=[_claim()],
        index_path=index_path,
        root=tmp_path / "transactions",
        transaction_id="txn-missing-packet",
    )
    Path(result.manifest.packets[0].path).unlink()

    loaded_claims = load_committed_evidence_claims(
        index_path=index_path,
        root=tmp_path / "transactions",
    )
    scan = scan_evidence_transactions(
        root=tmp_path / "transactions",
        index_path=index_path,
    )

    assert loaded_claims == []
    assert any(finding.severity == "blocker" for finding in scan.findings)
    assert any("packet is missing" in finding.reason for finding in scan.findings)


def test_concurrent_evidence_transactions_preserve_all_claims(tmp_path: Path) -> None:
    index_path = tmp_path / "evidence_index.json"
    root = tmp_path / "transactions"

    def commit(transaction_number: int) -> None:
        commit_evidence_transaction(
            packets=[_packet(f"packet-{transaction_number}")],
            claims=[
                _claim(
                    f"claim-{transaction_number}",
                    evidence_id=f"packet-{transaction_number}",
                )
            ],
            index_path=index_path,
            root=root,
            transaction_id=f"txn-{transaction_number}",
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(commit, range(16)))

    loaded_claims = load_committed_evidence_claims(index_path=index_path, root=root)

    assert {claim.claim_id for claim in loaded_claims} == {
        f"claim-{number}" for number in range(16)
    }


def test_recovery_scan_reports_transaction_directory_without_manifest(
    tmp_path: Path,
) -> None:
    orphan_dir = tmp_path / "transactions" / "txn-partial"
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "packets").mkdir()
    (orphan_dir / "packets" / "packet.json").write_text("{}")

    scan = scan_evidence_transactions(
        root=tmp_path / "transactions",
        index_path=tmp_path / "evidence_index.json",
    )

    assert any("no manifest" in finding.reason for finding in scan.findings)


def test_recovery_scan_reports_index_entry_with_missing_manifest(tmp_path: Path) -> None:
    index_path = tmp_path / "evidence_index.json"
    append_evidence_event(
        EvidenceEvent(
            event_type=EVIDENCE_TRANSACTION_EVENT,
            summary="missing manifest",
            payload={
                "transaction_id": "txn-missing-manifest",
                "manifest_path": str(tmp_path / "missing" / "transaction.json"),
                "manifest_checksum_sha256": "0" * 64,
            },
        ),
        path=index_path,
    )

    scan = scan_evidence_transactions(
        root=tmp_path / "transactions",
        index_path=index_path,
    )

    assert any("manifest is missing" in finding.reason for finding in scan.findings)
    assert any(finding.severity == "blocker" for finding in scan.findings)


def test_index_entry_without_manifest_checksum_fails_closed(tmp_path: Path) -> None:
    committed = commit_evidence_transaction(
        packets=[_packet()],
        claims=[_claim()],
        index_path=tmp_path / "source_index.json",
        root=tmp_path / "transactions",
        transaction_id="txn-no-manifest-checksum",
    )
    index_path = tmp_path / "bad_index.json"
    append_evidence_event(
        EvidenceEvent(
            event_type=EVIDENCE_TRANSACTION_EVENT,
            summary="missing manifest checksum",
            payload={
                "transaction_id": committed.manifest.transaction_id,
                "manifest_path": committed.manifest_path,
            },
        ),
        path=index_path,
    )

    assert (
        load_committed_evidence_claims(
            index_path=index_path,
            root=tmp_path / "transactions",
        )
        == []
    )
    scan = scan_evidence_transactions(root=tmp_path / "transactions", index_path=index_path)
    assert any("missing manifest checksum" in finding.reason for finding in scan.findings)


def test_tampered_manifest_checksum_fails_closed(tmp_path: Path) -> None:
    index_path = tmp_path / "evidence_index.json"
    committed = commit_evidence_transaction(
        packets=[_packet()],
        claims=[_claim()],
        index_path=index_path,
        root=tmp_path / "transactions",
        transaction_id="txn-tampered-manifest",
    )
    Path(committed.manifest_path).write_text(
        Path(committed.manifest_path).read_text().replace("committed", "prepared", 1)
    )

    assert (
        load_committed_evidence_claims(
            index_path=index_path,
            root=tmp_path / "transactions",
        )
        == []
    )
    scan = scan_evidence_transactions(root=tmp_path / "transactions", index_path=index_path)
    assert any("manifest checksum mismatch" in finding.reason for finding in scan.findings)


def test_tampered_claim_file_fails_closed(tmp_path: Path) -> None:
    index_path = tmp_path / "evidence_index.json"
    committed = commit_evidence_transaction(
        packets=[_packet()],
        claims=[_claim()],
        index_path=index_path,
        root=tmp_path / "transactions",
        transaction_id="txn-tampered-claim",
    )
    Path(committed.manifest.claims[0].path).write_text("{\"claim_id\":\"tampered\"}\n")

    assert (
        load_committed_evidence_claims(
            index_path=index_path,
            root=tmp_path / "transactions",
        )
        == []
    )
    scan = scan_evidence_transactions(root=tmp_path / "transactions", index_path=index_path)
    assert any("claim checksum mismatch" in finding.reason for finding in scan.findings)


def test_manifest_artifact_path_escape_fails_closed(tmp_path: Path) -> None:
    index_path = tmp_path / "evidence_index.json"
    transaction_dir = tmp_path / "transactions" / "txn-escape"
    transaction_dir.mkdir(parents=True)
    outside_claim = tmp_path / "outside_claim.json"
    outside_claim.write_text(_claim().model_dump_json())
    outside_checksum = tmp_path / "outside_claim.json.sha256"
    outside_checksum.write_text(_sha256(outside_claim) + "\n")
    manifest = EvidenceTransactionManifest(
        transaction_id="txn-escape",
        status="committed",
        index_path=str(index_path),
        claims=[
            EvidenceTransactionArtifact(
                artifact_type="claim",
                artifact_id="claim-1",
                path=str(outside_claim),
                checksum_path=str(outside_checksum),
                checksum_sha256=_sha256(outside_claim),
            )
        ],
    )
    manifest_path = transaction_dir / "transaction.json"
    manifest_path.write_text(manifest.model_dump_json())
    append_evidence_event(
        EvidenceEvent(
            event_type=EVIDENCE_TRANSACTION_EVENT,
            summary="escaped artifact path",
            payload={
                "transaction_id": "txn-escape",
                "manifest_path": str(manifest_path),
                "manifest_checksum_sha256": _sha256(manifest_path),
            },
        ),
        path=index_path,
    )

    assert (
        load_committed_evidence_claims(
            index_path=index_path,
            root=tmp_path / "transactions",
        )
        == []
    )
    scan = scan_evidence_transactions(root=tmp_path / "transactions", index_path=index_path)
    assert any("escapes transaction" in finding.reason for finding in scan.findings)


def test_evidence_transaction_rejects_mixed_session_ids(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="mix session IDs"):
        commit_evidence_transaction(
            packets=[_packet()],
            claims=[_claim().model_copy(update={"session_id": "other-session"})],
            index_path=tmp_path / "evidence_index.json",
            root=tmp_path / "transactions",
            transaction_id="txn-mixed-session",
        )


def test_evidence_transaction_rejects_claim_without_packet_handle(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no evidence handles"):
        commit_evidence_transaction(
            packets=[_packet()],
            claims=[_claim().model_copy(update={"evidence": []})],
            index_path=tmp_path / "evidence_index.json",
            root=tmp_path / "transactions",
            transaction_id="txn-no-claim-evidence",
        )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
