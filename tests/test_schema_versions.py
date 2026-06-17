from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.evidence import (
    append_evidence_event,
    commit_evidence_transaction,
    load_committed_evidence_claims,
    load_evidence_index,
    scan_evidence_transactions,
)
from aevum_ot2.core.models import (
    BridgeSession,
    EvidenceClaim,
    EvidenceEvent,
    EvidenceHandle,
    EvidenceIndex,
    EvidencePacket,
    EvidenceQuality,
    EvidenceSourceKind,
    GateName,
    GateResult,
    OffsetAuthorityState,
    OffsetRecord,
    OffsetRegistry,
    load_gate_result,
)
from aevum_ot2.core.plans import PlanFragment, load_plan_fragment
from aevum_ot2.core.records import (
    TARGET_CLASS_EVIDENCE_METHOD,
    FixtureQcMeasurement,
    FixtureQcRecord,
    LegacyImageEvidenceRecord,
    TargetClassResult,
    TargetClassVerificationRecord,
    load_fixture_qc_record,
    load_legacy_image_evidence_record,
    load_target_class_record,
    target_class_verified_claim_id,
    target_class_verified_claim_type,
    validate_legacy_image_evidence_record,
)
from aevum_ot2.core.registry import load_offset_registry
from aevum_ot2.core.schema import SchemaVersionError
from aevum_ot2.core.sessions import list_sessions, read_session, write_session

TARGET_EVIDENCE_PATH = Path(__file__).parent / "fixtures" / "target_evidence.json"


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def _fixture_qc_record() -> FixtureQcRecord:
    return FixtureQcRecord(
        fixture_load_name="aevum_p300_poc_fixture",
        fixture_params_sha256="a" * 64,
        labware_definition_sha256="b" * 64,
        measurements=[
            FixtureQcMeasurement(
                name="x_bound",
                measured_mm=127.76,
                nominal_mm=127.76,
                tolerance_mm=1.0,
                passed=True,
            )
        ],
    )


def _target_record() -> TargetClassVerificationRecord:
    return TargetClassVerificationRecord(
        target_class="center_high_z",
        fixture_load_name="aevum_p300_poc_fixture",
        fixture_params_sha256="a" * 64,
        labware_definition_sha256="b" * 64,
        robot_serial="OT2TEST0001",
        robot_server_version="9.0.0",
        slot="1",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        tiprack_load_name="opentrons_96_tiprack_300ul",
        offset_registry_record="not-yet-registered",
        result=TargetClassResult.BLOCKED,
    )


def _verified_target_record() -> TargetClassVerificationRecord:
    record = _target_record().model_copy(update={"result": TargetClassResult.PASSED})
    handle = EvidenceHandle(
        evidence_id="target-evidence:center_high_z",
        source_kind=EvidenceSourceKind.VISION_ANALYSIS,
        path=str(TARGET_EVIDENCE_PATH),
        checksum_sha256=_sha256_file(TARGET_EVIDENCE_PATH),
        session_id="session-1",
        quality=EvidenceQuality.USABLE,
    )
    claim = EvidenceClaim(
        claim_id=target_class_verified_claim_id("center_high_z", handle.evidence_id),
        claim_type=target_class_verified_claim_type("center_high_z"),
        value=True,
        session_id="session-1",
        fixture_load_name=record.fixture_load_name,
        fixture_params_sha256=record.fixture_params_sha256,
        labware_definition_sha256=record.labware_definition_sha256,
        method=TARGET_CLASS_EVIDENCE_METHOD,
        quality=EvidenceQuality.USABLE,
        evidence=[handle],
    )
    return record.model_copy(update={"evidence": [handle], "claims": [claim]})


def _legacy_image_record(image_path: Path) -> LegacyImageEvidenceRecord:
    return LegacyImageEvidenceRecord(
        legacy_record_id="legacy-1",
        purpose="fixture_presence",
        fixture_load_name="aevum_p300_poc_fixture",
        fixture_params_sha256="a" * 64,
        labware_definition_sha256="b" * 64,
        image_path=str(image_path),
        human_note="fixture observed",
    )


def _offset_record() -> OffsetRecord:
    return OffsetRecord(
        offset_record_id="offset-1",
        authority_state=OffsetAuthorityState.PROMOTED,
        robot_serial="OT2TEST0001",
        robot_server_version="9.0.0",
        opentrons_api_version="2.28",
        fixture_load_name="aevum_p300_poc_fixture",
        fixture_definition_uri="aevum/aevum_p300_poc_fixture/1",
        fixture_params_sha256="a" * 64,
        labware_definition_sha256="b" * 64,
        slot="1",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        tiprack_load_name="opentrons_96_tiprack_300ul",
        offset_mm={"x": 0.0, "y": 0.0, "z": 0.0},
        evidence_file="data/measurements/offsets/offset-1.json",
    )


def _packet(evidence_id: str = "packet-1") -> EvidencePacket:
    return EvidencePacket(
        evidence_id=evidence_id,
        source_kind=EvidenceSourceKind.PHYSICAL_MEASUREMENT,
        session_id="session-1",
        operation="fixture_qc",
        quality=EvidenceQuality.USABLE,
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


def _session() -> BridgeSession:
    identity = current_fixture_identity()
    now = datetime.now()
    return BridgeSession(
        session_id="session-1",
        kind="registration",
        owner_id="agent-1",
        robot_url="http://ot2.local:31950",
        robot_serial="OT2TEST0001",
        robot_server_version="9.0.0",
        max_protocol_api_version="2.28",
        state="ready_no_motion",
        created_at=now,
        updated_at=now,
        lease_expires_at=now + timedelta(minutes=10),
        maintenance_run_id="maintenance-run-1",
        slot="1",
        fixture_identity=identity,
        definition_uri="aevum/aevum_p300_poc_fixture/1",
        loaded_labware_id="fixture-1",
        evidence_index_path="data/measurements/ot2_evidence_index.json",
    )


@pytest.mark.parametrize(
    ("name", "data_factory", "loader"),
    [
        (
            "FixtureQcRecord",
            lambda tmp_path: _fixture_qc_record().model_dump(mode="json"),
            load_fixture_qc_record,
        ),
        (
            "TargetClassVerificationRecord",
            lambda tmp_path: _target_record().model_dump(mode="json"),
            load_target_class_record,
        ),
        (
            "LegacyImageEvidenceRecord",
            lambda tmp_path: _legacy_image_record(
                _image_file(tmp_path)
            ).model_dump(mode="json"),
            load_legacy_image_evidence_record,
        ),
        (
            "EvidenceIndex",
            lambda tmp_path: EvidenceIndex().model_dump(mode="json"),
            load_evidence_index,
        ),
        (
            "OffsetRegistry",
            lambda tmp_path: OffsetRegistry(records=[_offset_record()]).model_dump(mode="json"),
            load_offset_registry,
        ),
        (
            "PlanFragment",
            lambda tmp_path: PlanFragment(session_id="session-1").model_dump(mode="json"),
            load_plan_fragment,
        ),
        (
            "GateResult",
            lambda tmp_path: GateResult(
                gate_name=GateName.FIXTURE_QC,
                passed=False,
            ).model_dump(mode="json"),
            load_gate_result,
        ),
    ],
)
def test_versioned_loaders_accept_v1_artifacts(
    tmp_path: Path,
    name: str,
    data_factory: Callable[[Path], dict[str, object]],
    loader: Callable[[Path], object],
) -> None:
    path = tmp_path / f"{name}.json"
    _write_json(path, data_factory(tmp_path))

    assert loader(path) is not None


@pytest.mark.parametrize(
    ("name", "data_factory", "loader"),
    [
        (
            "FixtureQcRecord",
            lambda tmp_path: _fixture_qc_record().model_dump(mode="json"),
            load_fixture_qc_record,
        ),
        (
            "TargetClassVerificationRecord",
            lambda tmp_path: _target_record().model_dump(mode="json"),
            load_target_class_record,
        ),
        (
            "LegacyImageEvidenceRecord",
            lambda tmp_path: _legacy_image_record(
                _image_file(tmp_path)
            ).model_dump(mode="json"),
            load_legacy_image_evidence_record,
        ),
        (
            "EvidenceIndex",
            lambda tmp_path: EvidenceIndex().model_dump(mode="json"),
            load_evidence_index,
        ),
        (
            "OffsetRegistry",
            lambda tmp_path: OffsetRegistry(records=[_offset_record()]).model_dump(mode="json"),
            load_offset_registry,
        ),
        (
            "PlanFragment",
            lambda tmp_path: PlanFragment(session_id="session-1").model_dump(mode="json"),
            load_plan_fragment,
        ),
        (
            "GateResult",
            lambda tmp_path: GateResult(
                gate_name=GateName.FIXTURE_QC,
                passed=False,
            ).model_dump(mode="json"),
            load_gate_result,
        ),
    ],
)
def test_versioned_loaders_reject_unknown_root_schema_versions(
    tmp_path: Path,
    name: str,
    data_factory: Callable[[Path], dict[str, object]],
    loader: Callable[[Path], object],
) -> None:
    path = tmp_path / f"{name}.json"
    data = data_factory(tmp_path)
    data["schema_version"] = 999
    _write_json(path, data)

    with pytest.raises(SchemaVersionError, match="unsupported schema_version"):
        loader(path)


def test_record_loaders_reject_unknown_nested_schema_versions(tmp_path: Path) -> None:
    fixture_path = tmp_path / "fixture_qc.json"
    fixture_data = _fixture_qc_record().model_dump(mode="json")
    fixture_data["measurements"][0]["schema_version"] = 999
    _write_json(fixture_path, fixture_data)

    registry_path = tmp_path / "offset_registry.json"
    registry_data = OffsetRegistry(records=[_offset_record()]).model_dump(mode="json")
    registry_data["records"][0]["schema_version"] = 999
    _write_json(registry_path, registry_data)

    gate_path = tmp_path / "gate.json"
    gate_data = GateResult(
        gate_name=GateName.FIXTURE_QC,
        passed=False,
        evidence=[
            EvidenceHandle(
                schema_version=999,
                evidence_id="handle-1",
                source_kind=EvidenceSourceKind.INSPECTION_NOTE,
            )
        ],
    ).model_dump(mode="json")
    _write_json(gate_path, gate_data)

    target_path = tmp_path / "target_class.json"
    target_data = _verified_target_record().model_dump(mode="json")
    target_data["claims"][0]["evidence"][0]["schema_version"] = 999
    _write_json(target_path, target_data)

    with pytest.raises(SchemaVersionError, match="FixtureQcMeasurement"):
        load_fixture_qc_record(fixture_path)
    with pytest.raises(SchemaVersionError, match="OffsetRecord"):
        load_offset_registry(registry_path)
    with pytest.raises(SchemaVersionError, match="EvidenceHandle"):
        load_gate_result(gate_path)
    with pytest.raises(SchemaVersionError, match="TargetClassVerificationRecord"):
        load_target_class_record(target_path)


def test_gate_significant_nested_records_must_carry_schema_versions(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "fixture_qc.json"
    fixture_data = _fixture_qc_record().model_dump(mode="json")
    fixture_data["measurements"][0].pop("schema_version")
    _write_json(fixture_path, fixture_data)

    registry_path = tmp_path / "offset_registry.json"
    registry_data = OffsetRegistry(records=[_offset_record()]).model_dump(mode="json")
    registry_data["records"][0].pop("schema_version")
    _write_json(registry_path, registry_data)

    gate_path = tmp_path / "gate.json"
    gate_data = GateResult(
        gate_name=GateName.FIXTURE_QC,
        passed=False,
        evidence=[
            EvidenceHandle(
                evidence_id="handle-1",
                source_kind=EvidenceSourceKind.INSPECTION_NOTE,
            )
        ],
    ).model_dump(mode="json")
    gate_data["evidence"][0].pop("schema_version")
    _write_json(gate_path, gate_data)

    target_path = tmp_path / "target_class.json"
    target_data = _verified_target_record().model_dump(mode="json")
    target_data["evidence"][0].pop("schema_version")
    _write_json(target_path, target_data)

    with pytest.raises(SchemaVersionError, match="FixtureQcMeasurement"):
        load_fixture_qc_record(fixture_path)
    with pytest.raises(SchemaVersionError, match="OffsetRecord"):
        load_offset_registry(registry_path)
    with pytest.raises(SchemaVersionError, match="EvidenceHandle"):
        load_gate_result(gate_path)
    with pytest.raises(SchemaVersionError, match="TargetClassVerificationRecord"):
        load_target_class_record(target_path)


def test_bridge_session_sqlite_payload_rejects_unknown_schema_versions(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    payload = session.model_dump(mode="json")
    payload["schema_version"] = 999
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE bridge_sessions SET payload_json = ? WHERE session_id = ?",
            (json.dumps(payload), session.session_id),
        )

    with pytest.raises(SchemaVersionError, match="BridgeSession"):
        read_session(session.session_id, db_path)
    with pytest.raises(SchemaVersionError, match="BridgeSession"):
        list_sessions(db_path)


def test_legacy_image_alias_load_records_telemetry_and_cannot_authorize_motion(
    tmp_path: Path,
) -> None:
    image_path = _image_file(tmp_path)
    record_path = tmp_path / "legacy_image_evidence.json"
    _write_json(
        record_path,
        {
            "schema_version": 1,
            "observation_id": "old-observation-id",
            "purpose": "fixture_presence",
            "fixture_load_name": "aevum_p300_poc_fixture",
            "fixture_params_sha256": "a" * 64,
            "labware_definition_sha256": "b" * 64,
            "image_path": str(image_path),
            "human_observation": "legacy note",
            "motion_gate": True,
        },
    )

    record = load_legacy_image_evidence_record(record_path)
    validation = validate_legacy_image_evidence_record(record)

    assert record.legacy_record_id == "old-observation-id"
    assert record.human_note == "legacy note"
    assert any("legacy image evidence aliases" in note for note in record.notes)
    assert validation.passed is False
    assert "must not authorize motion" in " ".join(validation.reasons)


def test_widened_offset_records_load_with_proposed_authority_defaults(
    tmp_path: Path,
) -> None:
    old_record = _offset_record().model_dump(mode="json")
    for additive_field in [
        "offset_record_id",
        "authority_state",
        "safety_profile_sha256",
        "target_policy_digest_sha256",
    ]:
        old_record.pop(additive_field)
    registry_path = tmp_path / "offset_registry.json"
    _write_json(
        registry_path,
        {
            "schema_version": 1,
            "records": [old_record],
        },
    )

    registry = load_offset_registry(registry_path)

    assert registry.records[0].authority_state == OffsetAuthorityState.PROPOSED
    assert registry.records[0].offset_record_id == ""
    assert registry.records[0].safety_profile_sha256 == ""
    assert registry.records[0].target_policy_digest_sha256 == ""


def test_transaction_artifact_unknown_schema_versions_fail_closed(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "evidence_index.json"
    root = tmp_path / "transactions"
    commit_evidence_transaction(
        packets=[_packet().model_copy(update={"schema_version": 999})],
        claims=[_claim()],
        index_path=index_path,
        root=root,
        transaction_id="txn-bad-packet",
    )
    commit_evidence_transaction(
        packets=[_packet("packet-2")],
        claims=[
            _claim("claim-2", evidence_id="packet-2").model_copy(
                update={"schema_version": 999}
            )
        ],
        index_path=index_path,
        root=root,
        transaction_id="txn-bad-claim",
    )

    claims = load_committed_evidence_claims(index_path=index_path, root=root)
    scan = scan_evidence_transactions(root=root, index_path=index_path)
    reasons = " ".join(finding.reason for finding in scan.findings)

    assert claims == []
    assert "EvidencePacket" in reasons
    assert "EvidenceClaim" in reasons
    assert "unsupported schema_version" in reasons


def test_transaction_claim_rejects_unknown_evidence_handle_schema(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "evidence_index.json"
    root = tmp_path / "transactions"
    claim = _claim().model_copy(
        update={
            "evidence": [
                EvidenceHandle(
                    schema_version=999,
                    evidence_id="packet-1",
                    source_kind=EvidenceSourceKind.INSPECTION_NOTE,
                    created_at=datetime.now(),
                )
            ]
        }
    )
    commit_evidence_transaction(
        packets=[_packet()],
        claims=[claim],
        index_path=index_path,
        root=root,
        transaction_id="txn-bad-handle",
    )

    claims = load_committed_evidence_claims(index_path=index_path, root=root)
    scan = scan_evidence_transactions(root=root, index_path=index_path)

    assert claims == []
    assert any("EvidenceHandle" in finding.reason for finding in scan.findings)


def test_transaction_manifest_must_match_active_index_and_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "transactions"
    source_index = tmp_path / "source_index.json"
    bad_index = tmp_path / "bad_index.json"
    committed = commit_evidence_transaction(
        packets=[_packet()],
        claims=[_claim()],
        index_path=source_index,
        root=root,
        transaction_id="txn-source",
    )
    append_evidence_event(
        EvidenceEvent(
            event_type="evidence_transaction_committed",
            summary="wrong index replay",
            payload={
                "transaction_id": committed.manifest.transaction_id,
                "manifest_path": committed.manifest_path,
                "manifest_checksum_sha256": committed.manifest_checksum_sha256,
            },
        ),
        path=bad_index,
    )

    wrong_index_claims = load_committed_evidence_claims(index_path=bad_index, root=root)
    wrong_root_claims = load_committed_evidence_claims(
        index_path=source_index,
        root=tmp_path / "other_transactions",
    )
    scan = scan_evidence_transactions(root=root, index_path=bad_index)
    root_scan = scan_evidence_transactions(
        root=tmp_path / "other_transactions",
        index_path=source_index,
    )

    assert wrong_index_claims == []
    assert wrong_root_claims == []
    assert any("index path does not match" in finding.reason for finding in scan.findings)
    assert any("escapes root" in finding.reason for finding in root_scan.findings)


def test_transaction_artifact_id_must_match_payload(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "evidence_index.json"
    root = tmp_path / "transactions"
    committed = commit_evidence_transaction(
        packets=[_packet()],
        claims=[_claim()],
        index_path=index_path,
        root=root,
        transaction_id="txn-artifact-id",
    )
    claim_path = Path(committed.manifest.claims[0].path)
    claim_data = json.loads(claim_path.read_text())
    claim_data["claim_id"] = "different-claim-id"
    _write_json(claim_path, claim_data)
    claim_checksum = _sha256(claim_path)
    Path(committed.manifest.claims[0].checksum_path).write_text(claim_checksum + "\n")

    manifest_path = Path(committed.manifest_path)
    manifest_data = json.loads(manifest_path.read_text())
    manifest_data["claims"][0]["checksum_sha256"] = claim_checksum
    _write_json(manifest_path, manifest_data)
    manifest_checksum = _sha256(manifest_path)

    index_data = load_evidence_index(index_path).model_dump(mode="json")
    index_data["events"][0]["payload"]["manifest_checksum_sha256"] = manifest_checksum
    _write_json(index_path, index_data)

    claims = load_committed_evidence_claims(index_path=index_path, root=root)
    scan = scan_evidence_transactions(root=root, index_path=index_path)

    assert claims == []
    assert any("artifact ID does not match payload" in finding.reason for finding in scan.findings)


def test_legacy_evidence_event_does_not_become_committed_claim(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "evidence_index.json"
    append_evidence_event(
        EvidenceEvent(
            event_type="legacy_promoted_offset_authority",
            summary="legacy payload should not authorize gates",
            payload={
                "schema_version": 1,
                "claim_id": "claim-legacy",
                "claim_type": "promoted_offset_authority",
                "value": True,
            },
        ),
        path=index_path,
    )

    assert load_committed_evidence_claims(index_path=index_path) == []


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _image_file(tmp_path: Path) -> Path:
    image_path = tmp_path / "fixture.jpg"
    image_path.write_bytes(b"jpeg-placeholder")
    return image_path
