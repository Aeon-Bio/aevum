from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.models import (
    BridgeSession,
    EvidenceClaim,
    EvidenceHandle,
    EvidenceQuality,
    EvidenceSourceKind,
)
from aevum_ot2.core.records import (
    TARGET_CLASS_EVIDENCE_METHOD,
    TARGET_CLASSES,
    FixtureQcMeasurement,
    FixtureQcRecord,
    LegacyImageEvidenceRecord,
    RecordHandle,
    TargetClass,
    TargetClassResult,
    TargetClassVerificationRecord,
    load_fixture_qc_record,
    load_legacy_image_evidence_record,
    load_target_class_record,
    scaffold_fixture_qc_record,
    scaffold_legacy_image_evidence_record,
    scaffold_target_class_records,
    target_class_names,
    target_class_verified_claim_id,
    target_class_verified_claim_type,
    validate_fixture_qc_record,
    validate_legacy_image_evidence_record,
    validate_target_class_record,
    write_fixture_qc_record,
    write_legacy_image_evidence_record,
    write_target_class_record,
    write_target_class_scaffold,
)

EXPECTED_TARGET_CLASS_NAMES = {
    "center_high_z",
    "center_low_z_dry",
    "offset_x_1p0_high_z",
    "offset_x_1p0_low_z_dry",
    "offset_x_1p5_high_z",
    "offset_x_1p5_low_z_dry",
    "offset_x_2p0_high_z",
    "offset_x_2p0_low_z_dry",
    "center_wet",
    "offset_x_1p0_wet",
    "offset_x_1p5_wet",
    "offset_x_2p0_wet",
    "mat_patch_offset_x_1p5_low_z_dry",
    "mat_patch_offset_x_1p5_wet",
}
TARGET_EVIDENCE_PATH = Path(__file__).parent / "fixtures" / "target_evidence.json"


def _measurement(name: str, measured_mm: float, nominal_mm: float) -> FixtureQcMeasurement:
    return FixtureQcMeasurement(
        name=name,
        measured_mm=measured_mm,
        nominal_mm=nominal_mm,
        tolerance_mm=1.0,
        passed=True,
    )


def _nominal_fixture_qc(
    *,
    measurements: list[FixtureQcMeasurement] | None = None,
) -> FixtureQcRecord:
    return FixtureQcRecord(
        fixture_load_name="aevum_p300_poc_fixture",
        fixture_params_sha256="a" * 64,
        labware_definition_sha256="b" * 64,
        measurements=measurements
        if measurements is not None
        else [
            _measurement("x_bound", measured_mm=127.76, nominal_mm=127.76),
            _measurement("y_bound", measured_mm=85.48, nominal_mm=85.48),
            _measurement("z_bound", measured_mm=91.00, nominal_mm=91.00),
        ],
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )


def _target_record(
    target_class: str,
    *,
    predecessors: list[TargetClassVerificationRecord] | None = None,
    result: TargetClassResult = TargetClassResult.PASSED,
) -> TargetClassVerificationRecord:
    record = TargetClassVerificationRecord(
        target_class=target_class,
        fixture_load_name="aevum_p300_poc_fixture",
        fixture_params_sha256="a" * 64,
        labware_definition_sha256="b" * 64,
        robot_serial="OT2TEST0001",
        robot_server_version="8.0.0",
        slot="1",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        tiprack_load_name="opentrons_96_tiprack_300ul",
        offset_registry_record="offset-record-1",
        run_id="run-1",
        maintenance_run_id="maintenance-run-1",
        command_ids=["command-1"],
        result=result,
        predecessor_records=predecessors or [],
    )
    if result != TargetClassResult.PASSED:
        return record
    evidence = _target_evidence_handle(session_id="session-1", target_class=target_class)
    claim = _target_claim(
        session_id="session-1",
        target_class=target_class,
        handle=evidence,
        fixture_load_name=record.fixture_load_name,
        fixture_params_sha256=record.fixture_params_sha256,
        labware_definition_sha256=record.labware_definition_sha256,
    )
    return record.model_copy(update={"evidence": [evidence], "claims": [claim]})


def _target_evidence_handle(
    *,
    session_id: str,
    target_class: str,
) -> EvidenceHandle:
    return EvidenceHandle(
        evidence_id=f"target-evidence:{target_class}",
        source_kind=EvidenceSourceKind.VISION_ANALYSIS,
        path=str(TARGET_EVIDENCE_PATH),
        checksum_sha256=_sha256_file(TARGET_EVIDENCE_PATH),
        session_id=session_id,
        quality=EvidenceQuality.USABLE,
    )


def _target_claim(
    *,
    session_id: str,
    target_class: str,
    handle: EvidenceHandle,
    fixture_load_name: str,
    fixture_params_sha256: str,
    labware_definition_sha256: str,
) -> EvidenceClaim:
    return EvidenceClaim(
        claim_id=target_class_verified_claim_id(target_class, handle.evidence_id),
        claim_type=target_class_verified_claim_type(target_class),
        value=True,
        session_id=session_id,
        fixture_load_name=fixture_load_name,
        fixture_params_sha256=fixture_params_sha256,
        labware_definition_sha256=labware_definition_sha256,
        method=TARGET_CLASS_EVIDENCE_METHOD,
        quality=EvidenceQuality.USABLE,
        evidence=[handle],
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reason_text(result: object) -> str:
    return " ".join(str(reason).lower() for reason in result.reasons)


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


def test_expected_target_class_names_are_declared() -> None:
    assert set(target_class_names()) == EXPECTED_TARGET_CLASS_NAMES
    assert {target_class.name for target_class in TARGET_CLASSES} == EXPECTED_TARGET_CLASS_NAMES
    assert all(isinstance(target_class, TargetClass) for target_class in TARGET_CLASSES)


@pytest.mark.parametrize(
    "stale_name",
    ["center_low_z", "offset_x_1p0_low_z", "offset_x_1p5_low_z", "offset_x_2p0_low_z"],
)
def test_stale_low_z_names_are_absent(stale_name: str) -> None:
    assert stale_name not in target_class_names()


def test_wet_target_requires_matching_dry_predecessor() -> None:
    record = _target_record("center_wet", predecessors=[_target_record("center_high_z")])

    result = validate_target_class_record(record)

    assert result.passed is False
    assert "center_low_z_dry" in _reason_text(result)


def test_low_z_dry_target_requires_matching_high_z_predecessor() -> None:
    record = _target_record(
        "offset_x_1p5_low_z_dry",
        predecessors=[_target_record("center_high_z")],
    )

    result = validate_target_class_record(record)

    assert result.passed is False
    assert "offset_x_1p5_high_z" in _reason_text(result)


def test_fixture_qc_missing_measurements_fails_low_z_readiness() -> None:
    qc_record = _nominal_fixture_qc(
        measurements=[
            _measurement("x_bound", measured_mm=127.76, nominal_mm=127.76),
            _measurement("y_bound", measured_mm=85.48, nominal_mm=85.48),
        ]
    )

    result = validate_fixture_qc_record(qc_record, readiness="low_z")

    assert result.passed is False
    assert "z_bound" in _reason_text(result)


def test_nominal_fixture_qc_allows_registration_but_not_low_z_by_itself() -> None:
    qc_record = _nominal_fixture_qc()

    registration = validate_fixture_qc_record(qc_record, readiness="registration")
    low_z = validate_fixture_qc_record(qc_record, readiness="low_z")

    assert registration.passed is True
    assert registration.reasons == []
    assert low_z.passed is False
    assert "target" in _reason_text(low_z)


def test_fixture_qc_record_round_trips_with_handle(tmp_path) -> None:
    path = tmp_path / "fixture_qc.json"
    qc_record = _nominal_fixture_qc()

    handle = write_fixture_qc_record(qc_record, path)
    loaded = load_fixture_qc_record(path)

    assert isinstance(handle, RecordHandle)
    assert handle.record_type == "fixture_qc"
    assert handle.path == str(path)
    assert handle.record_id.startswith("aevum_p300_poc_fixture:")
    assert loaded == qc_record


def test_target_class_record_round_trips_with_handle(tmp_path) -> None:
    path = tmp_path / "target_class.json"
    record = _target_record("center_high_z")

    handle = write_target_class_record(record, path)
    loaded = load_target_class_record(path)

    assert handle.record_type == "target_class_verification"
    assert handle.path == str(path)
    assert handle.record_id == "center_high_z:OT2TEST0001:slot-1:p300_single_gen2:left"
    assert loaded == record


def test_target_class_legacy_evidence_aliases_are_non_authoritative() -> None:
    record = TargetClassVerificationRecord.model_validate(
        {
            "schema_version": 1,
            "target_class": "center_high_z",
            "fixture_load_name": "aevum_p300_poc_fixture",
            "fixture_params_sha256": "a" * 64,
            "labware_definition_sha256": "b" * 64,
            "robot_serial": "OT2TEST0001",
            "robot_server_version": "8.0.0",
            "slot": "1",
            "pipette_name": "p300_single_gen2",
            "pipette_mount": "left",
            "tiprack_load_name": "opentrons_96_tiprack_300ul",
            "offset_registry_record": "offset-record-1",
            "camera_images": ["legacy-camera-image"],
            "vision_results": ["legacy-vision-result"],
            "commissioning_observation": "legacy commissioning note",
            "result": "passed",
        }
    )

    result = validate_target_class_record(record)

    assert record.legacy_camera_images == ["legacy-camera-image"]
    assert result.passed is False
    assert "compatibility-only" in _reason_text(result)
    assert "target_class_verified:center_high_z" in _reason_text(result)


def test_target_class_validation_rejects_tampered_evidence_checksum() -> None:
    record = _target_record("center_high_z")
    tampered_handle = record.evidence[0].model_copy(
        update={"checksum_sha256": "0" * 64}
    )
    tampered_claim = record.claims[0].model_copy(update={"evidence": [tampered_handle]})
    record = record.model_copy(
        update={"evidence": [tampered_handle], "claims": [tampered_claim]}
    )

    result = validate_target_class_record(record)

    assert result.passed is False
    assert "checksum mismatch" in _reason_text(result)


def test_target_class_writer_drops_legacy_compatibility_fields(tmp_path) -> None:
    path = tmp_path / "target_class.json"
    record = _target_record("center_high_z").model_copy(
        update={
            "legacy_camera_images": ["legacy-camera-image"],
            "legacy_vision_results": ["legacy-vision-result"],
            "legacy_commissioning_observation": "legacy note",
        }
    )

    write_target_class_record(record, path)
    data = json.loads(path.read_text())

    assert "camera_images" not in data
    assert "vision_results" not in data
    assert "commissioning_observation" not in data
    assert "legacy_camera_images" not in data
    assert "legacy_vision_results" not in data
    assert "legacy_commissioning_observation" not in data


def test_fixture_qc_scaffold_passes_with_nominal_measurements_and_gates() -> None:
    identity = current_fixture_identity()

    record = scaffold_fixture_qc_record(
        identity,
        x_bound_mm=127.76,
        y_bound_mm=85.48,
        z_bound_mm=91.0,
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )
    result = validate_fixture_qc_record(record, readiness="registration")

    assert result.passed is True
    assert record.fixture_params_sha256 == identity.params_sha256
    assert record.measurements[0].passed is True


def test_fixture_qc_scaffold_blocks_missing_measurements_and_unchecked_gates() -> None:
    identity = current_fixture_identity()

    record = scaffold_fixture_qc_record(identity)
    result = validate_fixture_qc_record(record, readiness="registration")

    assert result.passed is False
    assert all(measurement.passed is False for measurement in record.measurements)
    assert "failed qc measurements" in _reason_text(result)
    assert "failed fixture qc gates" in _reason_text(result)


def test_fixture_qc_scaffold_blocks_high_z_bound() -> None:
    identity = current_fixture_identity()

    record = scaffold_fixture_qc_record(
        identity,
        x_bound_mm=127.76,
        y_bound_mm=85.48,
        z_bound_mm=92.5,
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )
    result = validate_fixture_qc_record(record, readiness="registration")

    assert result.passed is False
    assert record.measurements[2].name == "z_bound"
    assert record.measurements[2].passed is False


def test_legacy_image_evidence_record_round_trips_with_legacy_handle(tmp_path) -> None:
    identity = current_fixture_identity()
    image_path = tmp_path / "fixture.jpg"
    image_path.write_bytes(b"jpeg-placeholder")
    record = scaffold_legacy_image_evidence_record(
        identity,
        purpose="fixture_presence",
        image_path=image_path,
        human_observation="fixture appears seated",
    )

    handle = write_legacy_image_evidence_record(
        record,
        tmp_path / "legacy_image_evidence.json",
    )
    loaded = load_legacy_image_evidence_record(handle.path)
    validation = validate_legacy_image_evidence_record(loaded)

    assert handle.record_type == "legacy_image_evidence"
    assert handle.record_id.startswith("legacy_image_evidence:fixture_presence:")
    assert loaded == record
    assert loaded.human_note == "fixture appears seated"
    assert validation.passed is True


def test_legacy_image_evidence_record_loads_old_observation_keys(tmp_path) -> None:
    image_path = tmp_path / "fixture.jpg"
    image_path.write_bytes(b"jpeg-placeholder")
    record = LegacyImageEvidenceRecord.model_validate(
        {
            "schema_version": 1,
            "observation_id": "old-observation-id",
            "purpose": "fixture_presence",
            "fixture_load_name": "aevum_p300_poc_fixture",
            "fixture_params_sha256": "a" * 64,
            "labware_definition_sha256": "b" * 64,
            "image_path": str(image_path),
            "human_observation": "legacy note",
        }
    )

    assert record.legacy_record_id == "old-observation-id"
    assert record.human_note == "legacy note"
    assert validate_legacy_image_evidence_record(record).passed is True


def test_legacy_image_evidence_record_rejects_missing_image_path() -> None:
    record = LegacyImageEvidenceRecord.model_validate(
        {
            "schema_version": 1,
            "legacy_record_id": "legacy-record-id",
            "purpose": "fixture_presence",
            "fixture_load_name": "aevum_p300_poc_fixture",
            "fixture_params_sha256": "a" * 64,
            "labware_definition_sha256": "b" * 64,
            "image_path": "missing-fixture.jpg",
            "human_note": "legacy note",
        }
    )

    result = validate_legacy_image_evidence_record(record)

    assert result.passed is False
    assert "image path does not exist" in _reason_text(result)


def test_legacy_image_evidence_record_id_includes_supervised_note(tmp_path) -> None:
    identity = current_fixture_identity()
    image_path = tmp_path / "fixture.jpg"
    image_path.write_bytes(b"jpeg-placeholder")

    first = scaffold_legacy_image_evidence_record(
        identity,
        purpose="fixture_presence",
        image_path=image_path,
        human_observation="fixture seated",
    )
    second = scaffold_legacy_image_evidence_record(
        identity,
        purpose="fixture_presence",
        image_path=image_path,
        human_observation="fixture not seated",
    )

    assert first.legacy_record_id != second.legacy_record_id


def test_legacy_image_evidence_record_cannot_authorize_motion(tmp_path) -> None:
    identity = current_fixture_identity()
    record = scaffold_legacy_image_evidence_record(
        identity,
        purpose="fixture_presence",
        image_path=tmp_path / "fixture.jpg",
        human_observation="fixture appears seated",
    )
    record.motion_gate = True

    result = validate_legacy_image_evidence_record(record)

    assert result.passed is False
    assert "must not authorize motion" in _reason_text(result)


def test_target_class_scaffold_uses_session_identity() -> None:
    session = _session()

    records = scaffold_target_class_records(
        session,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
    )

    assert len(records) == len(TARGET_CLASSES)
    assert {record.target_class for record in records} == EXPECTED_TARGET_CLASS_NAMES
    assert all(record.result == TargetClassResult.BLOCKED for record in records)
    assert all(record.robot_serial == session.robot_serial for record in records)
    assert all(record.slot == session.slot for record in records)
    assert all(record.maintenance_run_id == session.maintenance_run_id for record in records)


def test_write_target_class_scaffold_writes_one_record_per_target(tmp_path) -> None:
    session = _session()

    handles = write_target_class_scaffold(
        session,
        tmp_path,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
    )

    assert len(handles) == len(TARGET_CLASSES)
    assert {handle.record_type for handle in handles} == {"target_class_verification"}
    assert (tmp_path / "center_high_z.json").exists()
