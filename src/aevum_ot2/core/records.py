from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field

from aevum_ot2.core.evidence import load_committed_evidence_claims
from aevum_ot2.core.evidence_primitives import (
    _safe_path_segment,
    _sha256_file,
    _transaction_root_for_index,
)
from aevum_ot2.core.models import (
    BridgeSession,
    EvidenceClaim,
    EvidenceHandle,
    EvidenceQuality,
    FixtureIdentity,
    VisionAnalysisResult,
)
from aevum_ot2.core.schema import (
    load_json_object,
    parse_versioned_json_model,
    require_schema_version,
    require_schema_versioned_items,
)


class ValidationResult(BaseModel):
    passed: bool
    reasons: list[str] = Field(default_factory=list)


class RecordHandle(BaseModel):
    record_type: Literal[
        "fixture_qc",
        "target_class_verification",
        "legacy_image_evidence",
    ]
    path: str
    record_id: str


ObservationPurpose = Literal["deck_baseline", "fixture_presence", "high_z_target", "recovery"]
ObservationLabelValue = str | int | float | bool


class TargetClassResult(StrEnum):
    BLOCKED = "blocked"
    PASSED = "passed"
    FAILED = "failed"


class HighZMotionResult(StrEnum):
    """Outcome of a high-Z motion evidence record — a DISTINCT type from TargetClassResult.

    The string values coincide today, but the type must differ so a future consumer's
    ``record.result == TargetClassResult.PASSED`` filter cannot silently sweep up post-motion
    records it was never meant to authorize (the evidence_model.md rule: facts are
    distinguishable by kind, and the type checker should reject the category error).
    """

    BLOCKED = "blocked"
    PASSED = "passed"
    FAILED = "failed"


class TargetClass(BaseModel):
    name: str
    geometry: str
    requires: list[str] = Field(default_factory=list)
    wet: bool = False
    mat_patch: bool = False
    boundary: bool = False


TARGET_CLASSES: tuple[TargetClass, ...] = (
    TargetClass(name="center_high_z", geometry="column 1 center high clearance"),
    TargetClass(
        name="center_low_z_dry",
        geometry="column 1 center low dry approach",
        requires=["center_high_z"],
    ),
    TargetClass(name="offset_x_1p0_high_z", geometry="column 2 +1.0 mm X high clearance"),
    TargetClass(
        name="offset_x_1p0_low_z_dry",
        geometry="column 2 +1.0 mm X low dry approach",
        requires=["offset_x_1p0_high_z"],
    ),
    TargetClass(name="offset_x_1p5_high_z", geometry="column 3 +1.5 mm X high clearance"),
    TargetClass(
        name="offset_x_1p5_low_z_dry",
        geometry="column 3 +1.5 mm X low dry approach",
        requires=["offset_x_1p5_high_z"],
    ),
    TargetClass(
        name="offset_x_2p0_high_z",
        geometry="column 4 +2.0 mm X high clearance",
        boundary=True,
    ),
    TargetClass(
        name="offset_x_2p0_low_z_dry",
        geometry="column 4 +2.0 mm X low dry approach",
        requires=["offset_x_2p0_high_z"],
        boundary=True,
    ),
    TargetClass(
        name="center_wet",
        geometry="column 1 center dye/water dispense",
        requires=["center_low_z_dry"],
        wet=True,
    ),
    TargetClass(
        name="offset_x_1p0_wet",
        geometry="column 2 +1.0 mm X dye/water dispense",
        requires=["offset_x_1p0_low_z_dry"],
        wet=True,
    ),
    TargetClass(
        name="offset_x_1p5_wet",
        geometry="column 3 +1.5 mm X dye/water dispense",
        requires=["offset_x_1p5_low_z_dry"],
        wet=True,
    ),
    TargetClass(
        name="offset_x_2p0_wet",
        geometry="column 4 +2.0 mm X dye/water dispense",
        requires=["offset_x_2p0_low_z_dry"],
        wet=True,
        boundary=True,
    ),
    TargetClass(
        name="mat_patch_offset_x_1p5_low_z_dry",
        geometry="mat patch aligned to +1.5 mm X low dry approach",
        requires=["offset_x_1p5_low_z_dry"],
        mat_patch=True,
    ),
    TargetClass(
        name="mat_patch_offset_x_1p5_wet",
        geometry="mat patch aligned to +1.5 mm X dye/water dispense",
        requires=["mat_patch_offset_x_1p5_low_z_dry", "offset_x_1p5_wet"],
        wet=True,
        mat_patch=True,
    ),
)

TARGET_CLASS_BY_NAME = {target_class.name: target_class for target_class in TARGET_CLASSES}
REQUIRED_QC_MEASUREMENTS = {"x_bound", "y_bound", "z_bound"}
TARGET_CLASS_VERIFIED_CLAIM_PREFIX = "target_class_verified"
TARGET_CLASS_EVIDENCE_METHOD = "target_class_evidence_packet_v1"
HIGH_Z_MOTION_COMPLETED_CLAIM_PREFIX = "high_z_motion_completed"
HIGH_Z_MOTION_EVIDENCE_METHOD = "high_z_motion_evidence_packet_v1"


class FixtureQcMeasurement(BaseModel):
    schema_version: int = 1
    name: str
    measured_mm: float | None = None
    nominal_mm: float | None = None
    tolerance_mm: float | None = None
    passed: bool
    notes: str = ""


class FixtureQcRecord(BaseModel):
    schema_version: int = 1
    fixture_load_name: str
    fixture_params_sha256: str
    labware_definition_sha256: str
    pose_digest_sha256: str = ""
    measurements: list[FixtureQcMeasurement] = Field(default_factory=list)
    camera_capture_indexed: bool = False
    fixture_visible: bool = False
    vision_evidence_ok: bool = False
    base_seated: bool = False
    guide_holes_open: bool = False
    support_debris_absent: bool = False
    mock_wells_undeformed: bool = False
    no_warping_lift: bool = False


class LegacyImageEvidenceRecord(BaseModel):
    schema_version: int = 1
    legacy_record_id: str = Field(
        default="",
        validation_alias=AliasChoices("legacy_record_id", "observation_id"),
    )
    created_at: datetime = Field(default_factory=datetime.now)
    purpose: ObservationPurpose
    session_id: str = ""
    fixture_load_name: str
    fixture_params_sha256: str
    labware_definition_sha256: str
    robot_serial: str = ""
    robot_server_version: str = ""
    slot: str = ""
    target_class: str = ""
    image_path: str
    vision_result_path: str = ""
    evidence_index_path: str = ""
    vision_evidence_ok: bool = False
    motion_gate: bool = False
    human_note: str = Field(
        default="",
        validation_alias=AliasChoices("human_note", "human_observation"),
    )
    labels: dict[str, ObservationLabelValue] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


def scaffold_fixture_qc_record(
    fixture_identity: FixtureIdentity,
    *,
    pose_digest_sha256: str = "",
    x_bound_mm: float | None = None,
    y_bound_mm: float | None = None,
    z_bound_mm: float | None = None,
    tolerance_mm: float = 1.0,
    camera_capture_indexed: bool = False,
    fixture_visible: bool = False,
    vision_evidence_ok: bool = False,
    base_seated: bool = False,
    guide_holes_open: bool = False,
    support_debris_absent: bool = False,
    mock_wells_undeformed: bool = False,
    no_warping_lift: bool = False,
) -> FixtureQcRecord:
    nominal = fixture_identity.nominal_dimensions_mm
    return FixtureQcRecord(
        fixture_load_name=fixture_identity.load_name,
        fixture_params_sha256=fixture_identity.params_sha256,
        labware_definition_sha256=fixture_identity.labware_definition_sha256,
        pose_digest_sha256=pose_digest_sha256,
        measurements=[
            _bound_measurement(
                name="x_bound",
                measured_mm=x_bound_mm,
                nominal_mm=nominal["x"],
                tolerance_mm=tolerance_mm,
                mode="within",
            ),
            _bound_measurement(
                name="y_bound",
                measured_mm=y_bound_mm,
                nominal_mm=nominal["y"],
                tolerance_mm=tolerance_mm,
                mode="within",
            ),
            _bound_measurement(
                name="z_bound",
                measured_mm=z_bound_mm,
                nominal_mm=nominal["z"],
                tolerance_mm=tolerance_mm,
                mode="max",
            ),
        ],
        camera_capture_indexed=camera_capture_indexed,
        fixture_visible=fixture_visible,
        vision_evidence_ok=vision_evidence_ok,
        base_seated=base_seated,
        guide_holes_open=guide_holes_open,
        support_debris_absent=support_debris_absent,
        mock_wells_undeformed=mock_wells_undeformed,
        no_warping_lift=no_warping_lift,
    )


def scaffold_legacy_image_evidence_record(
    fixture_identity: FixtureIdentity,
    *,
    purpose: ObservationPurpose,
    image_path: str | Path,
    session: BridgeSession | None = None,
    target_class: str = "",
    vision_result: VisionAnalysisResult | None = None,
    vision_result_path: str | Path | None = None,
    human_observation: str = "",
    labels: dict[str, ObservationLabelValue] | None = None,
    notes: list[str] | None = None,
) -> LegacyImageEvidenceRecord:
    record = LegacyImageEvidenceRecord(
        legacy_record_id="",
        purpose=purpose,
        session_id=session.session_id if session is not None else "",
        fixture_load_name=fixture_identity.load_name,
        fixture_params_sha256=fixture_identity.params_sha256,
        labware_definition_sha256=fixture_identity.labware_definition_sha256,
        robot_serial=session.robot_serial or "" if session is not None else "",
        robot_server_version=session.robot_server_version or "" if session is not None else "",
        slot=session.slot if session is not None else "",
        target_class=target_class,
        image_path=str(Path(image_path)),
        vision_result_path="" if vision_result_path is None else str(Path(vision_result_path)),
        evidence_index_path=session.evidence_index_path if session is not None else "",
        vision_evidence_ok=vision_result.evidence_ok if vision_result is not None else False,
        motion_gate=vision_result.motion_gate if vision_result is not None else False,
        human_note=human_observation,
        labels=labels or {},
        notes=notes or [],
    )
    record.legacy_record_id = _legacy_image_evidence_record_id(record)
    return record


class TargetClassVerificationRecord(BaseModel):
    schema_version: int = 1
    target_class: str
    fixture_load_name: str
    fixture_params_sha256: str
    labware_definition_sha256: str
    pose_digest_sha256: str = ""
    robot_serial: str
    robot_server_version: str
    slot: str
    pipette_name: str
    pipette_mount: str
    tiprack_load_name: str
    offset_registry_record: str
    run_id: str = ""
    maintenance_run_id: str = ""
    command_ids: list[str] = Field(default_factory=list)
    evidence: list[EvidenceHandle] = Field(default_factory=list)
    claims: list[EvidenceClaim] = Field(default_factory=list)
    legacy_camera_images: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("legacy_camera_images", "camera_images"),
        exclude=True,
    )
    legacy_vision_results: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("legacy_vision_results", "vision_results"),
        exclude=True,
    )
    legacy_commissioning_observation: str = Field(
        default="",
        validation_alias=AliasChoices(
            "legacy_commissioning_observation",
            "commissioning_observation",
        ),
        exclude=True,
    )
    result: TargetClassResult = TargetClassResult.BLOCKED
    predecessor_records: list[TargetClassVerificationRecord] = Field(default_factory=list)


class HighZMotionRecord(BaseModel):
    schema_version: int = 1
    target_class: str
    fixture_load_name: str
    fixture_params_sha256: str
    labware_definition_sha256: str
    pose_digest_sha256: str = ""
    robot_serial: str
    robot_server_version: str
    slot: str
    commanded_high_z_mm: float
    run_id: str = ""
    maintenance_run_id: str = ""
    command_id: str = ""
    evidence: list[EvidenceHandle] = Field(default_factory=list)
    claims: list[EvidenceClaim] = Field(default_factory=list)
    result: HighZMotionResult = HighZMotionResult.BLOCKED


class TargetClassAuthorityResult(BaseModel):
    passed: bool
    missing_claims: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    evidence: list[EvidenceHandle] = Field(default_factory=list)


def target_class_names() -> list[str]:
    return [target_class.name for target_class in TARGET_CLASSES]


def scaffold_target_class_record(
    session: BridgeSession,
    target_class: str,
    *,
    pipette_name: str,
    pipette_mount: str,
    tiprack_load_name: str = "opentrons_96_tiprack_300ul",
    offset_registry_record: str = "not-yet-registered",
) -> TargetClassVerificationRecord:
    identity = session.fixture_identity
    return TargetClassVerificationRecord(
        target_class=target_class,
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        pose_digest_sha256=session.fixture_pose_digest_sha256,
        robot_serial=session.robot_serial or "",
        robot_server_version=session.robot_server_version or "",
        slot=session.slot,
        pipette_name=pipette_name,
        pipette_mount=pipette_mount,
        tiprack_load_name=tiprack_load_name,
        offset_registry_record=offset_registry_record,
        maintenance_run_id=session.maintenance_run_id or "",
        result=TargetClassResult.BLOCKED,
    )


def scaffold_target_class_records(
    session: BridgeSession,
    *,
    pipette_name: str,
    pipette_mount: str,
    tiprack_load_name: str = "opentrons_96_tiprack_300ul",
    offset_registry_record: str = "not-yet-registered",
) -> list[TargetClassVerificationRecord]:
    return [
        scaffold_target_class_record(
            session,
            target_class_name,
            pipette_name=pipette_name,
            pipette_mount=pipette_mount,
            tiprack_load_name=tiprack_load_name,
            offset_registry_record=offset_registry_record,
        )
        for target_class_name in target_class_names()
    ]


def write_target_class_scaffold(
    session: BridgeSession,
    directory: str | Path,
    *,
    pipette_name: str,
    pipette_mount: str,
    tiprack_load_name: str = "opentrons_96_tiprack_300ul",
    offset_registry_record: str = "not-yet-registered",
) -> list[RecordHandle]:
    output_dir = Path(directory)
    records = scaffold_target_class_records(
        session,
        pipette_name=pipette_name,
        pipette_mount=pipette_mount,
        tiprack_load_name=tiprack_load_name,
        offset_registry_record=offset_registry_record,
    )
    return [
        write_target_class_record(record, output_dir / f"{record.target_class}.json")
        for record in records
    ]


def write_fixture_qc_record(record: FixtureQcRecord, path: str | Path) -> RecordHandle:
    record_path = Path(path)
    _atomic_write_model(record_path, record)
    return fixture_qc_record_handle(record, record_path)


def write_legacy_image_evidence_record(
    record: LegacyImageEvidenceRecord,
    path: str | Path,
) -> RecordHandle:
    record_path = Path(path)
    _atomic_write_model(record_path, record)
    return legacy_image_evidence_record_handle(record, record_path)


def fixture_qc_record_handle(record: FixtureQcRecord, path: str | Path) -> RecordHandle:
    return RecordHandle(
        record_type="fixture_qc",
        path=str(Path(path)),
        record_id=_fixture_qc_record_id(record),
    )


def legacy_image_evidence_record_handle(
    record: LegacyImageEvidenceRecord,
    path: str | Path,
) -> RecordHandle:
    return RecordHandle(
        record_type="legacy_image_evidence",
        path=str(Path(path)),
        record_id=record.legacy_record_id,
    )


def load_fixture_qc_record(path: str | Path) -> FixtureQcRecord:
    data = load_json_object(path, schema_name="FixtureQcRecord")
    require_schema_version(data, schema_name="FixtureQcRecord", path=path)
    require_schema_versioned_items(
        data.get("measurements"),
        schema_name="FixtureQcMeasurement",
        path=path,
    )
    return FixtureQcRecord.model_validate(data)


def load_legacy_image_evidence_record(path: str | Path) -> LegacyImageEvidenceRecord:
    data = load_json_object(path, schema_name="LegacyImageEvidenceRecord")
    record = parse_versioned_json_model(
        data,
        LegacyImageEvidenceRecord,
        schema_name="LegacyImageEvidenceRecord",
        path=path,
    )
    return _record_with_legacy_alias_telemetry(record, data)


def write_target_class_record(
    record: TargetClassVerificationRecord,
    path: str | Path,
) -> RecordHandle:
    record_path = Path(path)
    _atomic_write_model(record_path, record)
    return target_class_record_handle(record, record_path)


def target_class_record_handle(
    record: TargetClassVerificationRecord,
    path: str | Path,
) -> RecordHandle:
    return RecordHandle(
        record_type="target_class_verification",
        path=str(Path(path)),
        record_id=_target_class_record_id(record),
    )


def load_target_class_record(path: str | Path) -> TargetClassVerificationRecord:
    data = load_json_object(path, schema_name="TargetClassVerificationRecord")
    _require_target_class_record_schema(data, path=path)
    return TargetClassVerificationRecord.model_validate(data)


def target_class_verified_claim_type(target_class: str) -> str:
    return f"{TARGET_CLASS_VERIFIED_CLAIM_PREFIX}:{target_class}"


def target_class_verified_claim_id(target_class: str, evidence_id: str) -> str:
    return f"{target_class_verified_claim_type(target_class)}:evidence-{evidence_id}"


def high_z_motion_completed_claim_type(target_class: str) -> str:
    return f"{HIGH_Z_MOTION_COMPLETED_CLAIM_PREFIX}:{target_class}"


def high_z_motion_completed_claim_id(target_class: str, evidence_id: str) -> str:
    return f"{high_z_motion_completed_claim_type(target_class)}:evidence-{evidence_id}"


def target_class_authority(
    record: TargetClassVerificationRecord,
    *,
    session: BridgeSession,
    reference_record: TargetClassVerificationRecord | None = None,
    fixture_pose: object | None = None,
) -> TargetClassAuthorityResult:
    missing_claims: list[str] = []
    blockers: list[str] = []
    claim_ids: list[str] = []

    blockers.extend(_target_record_session_scope_blockers(record, session))
    if session.fixture_pose_digest_sha256 and fixture_pose is None:
        missing_claims.append("fixture_pose")
    if fixture_pose is not None:
        from aevum_ot2.core.pose import FixturePose, pose_match_gate

        pose = FixturePose.model_validate(fixture_pose)
        pose_gate = pose_match_gate(
            pose,
            expected_pose_digest_sha256=record.pose_digest_sha256,
            expected_session_id=session.session_id,
            expected_robot_url=session.robot_url,
            expected_fixture_params_sha256=session.fixture_identity.params_sha256,
            expected_evidence_index_path=session.evidence_index_path,
            expected_claim_not_before=session.updated_at,
            claim_expires_at=session.lease_expires_at,
            claim_valid_at=datetime.now(),
            claims=record.claims,
        )
        missing_claims.extend(pose_gate.missing_claims)
        blockers.extend(pose_gate.blockers)
        claim_ids.extend(pose_gate.claim_ids)
    if reference_record is not None:
        blockers.extend(_target_record_reference_scope_blockers(record, reference_record))
    if record.result != TargetClassResult.PASSED:
        missing_claims.append(f"passed_target:{record.target_class}")

    claim_type = target_class_verified_claim_type(record.target_class)
    claims = [claim for claim in record.claims if claim.claim_type == claim_type]
    if _has_legacy_target_evidence(record):
        blockers.append("legacy target evidence fields cannot authorize target class")
    if not claims:
        missing_claims.append(claim_type)
    if len(claims) > 1:
        blockers.append(f"duplicate target-class verified claims: {record.target_class}")

    evidence_by_id = {handle.evidence_id: handle for handle in record.evidence}
    if not evidence_by_id:
        missing_claims.append("target_class_evidence_handle")
    for handle in record.evidence:
        blockers.extend(_target_evidence_handle_blockers(handle, session=session))

    for claim in claims:
        claim_ids.append(claim.claim_id)
        blockers.extend(
            _target_claim_blockers(
                claim,
                record=record,
                session=session,
                evidence_by_id=evidence_by_id,
            )
        )

    return TargetClassAuthorityResult(
        passed=not blockers and not missing_claims,
        missing_claims=_dedupe(missing_claims),
        blockers=_dedupe(blockers),
        claim_ids=_dedupe(claim_ids),
        evidence=list(evidence_by_id.values()),
    )


def validate_fixture_qc_record(
    record: FixtureQcRecord,
    *,
    readiness: Literal["registration", "low_z"] = "registration",
) -> ValidationResult:
    reasons: list[str] = []
    measurement_by_name = {measurement.name: measurement for measurement in record.measurements}

    missing_measurements = sorted(REQUIRED_QC_MEASUREMENTS - measurement_by_name.keys())
    if missing_measurements:
        reasons.append(f"missing required QC measurements: {', '.join(missing_measurements)}")

    failed_measurements = [
        measurement.name for measurement in record.measurements if measurement.passed is False
    ]
    if failed_measurements:
        reasons.append(f"failed QC measurements: {', '.join(sorted(failed_measurements))}")

    gate_values = {
        "camera_capture_indexed": record.camera_capture_indexed,
        "fixture_visible": record.fixture_visible,
        "vision_evidence_ok": record.vision_evidence_ok,
        "base_seated": record.base_seated,
        "guide_holes_open": record.guide_holes_open,
        "support_debris_absent": record.support_debris_absent,
        "mock_wells_undeformed": record.mock_wells_undeformed,
        "no_warping_lift": record.no_warping_lift,
    }
    failed_gates = sorted(name for name, passed in gate_values.items() if not passed)
    if failed_gates:
        reasons.append(f"failed fixture QC gates: {', '.join(failed_gates)}")

    if readiness == "low_z":
        reasons.append("target-class verification is required before low-Z readiness")

    return ValidationResult(passed=not reasons, reasons=reasons)


def validate_legacy_image_evidence_record(
    record: LegacyImageEvidenceRecord,
) -> ValidationResult:
    reasons: list[str] = []
    if not record.image_path:
        reasons.append("image path is required")
    elif not Path(record.image_path).is_file():
        reasons.append("image path does not exist")
    if not record.vision_result_path and not record.human_note:
        reasons.append("vision result or human commissioning note is required")
    if record.vision_result_path:
        if not Path(record.vision_result_path).is_file():
            reasons.append("vision result path does not exist")
        if not record.vision_evidence_ok:
            reasons.append("vision evidence is not acceptable")
    if record.motion_gate:
        reasons.append("legacy image evidence records must not authorize motion")
    if record.purpose == "fixture_presence" and not record.fixture_load_name:
        reasons.append("fixture identity is required for fixture-presence observations")
    if record.purpose == "high_z_target" and not record.target_class:
        reasons.append("target class is required for high-Z target observations")
    return ValidationResult(passed=not reasons, reasons=reasons)


def _atomic_write_model(path: Path, model: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(model.model_dump_json(indent=2) + "\n")
    os.replace(tmp, path)


def _record_with_legacy_alias_telemetry(
    record: LegacyImageEvidenceRecord,
    data: Mapping[str, Any],
) -> LegacyImageEvidenceRecord:
    aliases = [
        alias
        for alias, canonical in {
            "observation_id": "legacy_record_id",
            "human_observation": "human_note",
        }.items()
        if alias in data and canonical not in data
    ]
    if not aliases:
        return record
    note = "loaded through legacy image evidence aliases: " + ", ".join(sorted(aliases))
    if note in record.notes:
        return record
    return record.model_copy(update={"notes": [*record.notes, note]})


def _require_target_class_record_schema(
    data: Mapping[str, Any],
    *,
    path: str | Path,
    schema_name: str = "TargetClassVerificationRecord",
) -> None:
    require_schema_version(data, schema_name=schema_name, path=path)
    require_schema_versioned_items(
        data.get("evidence"),
        schema_name=f"{schema_name}.EvidenceHandle",
        path=path,
    )
    claims = data.get("claims")
    require_schema_versioned_items(
        claims,
        schema_name=f"{schema_name}.EvidenceClaim",
        path=path,
    )
    if isinstance(claims, list):
        for index, claim in enumerate(claims):
            if not isinstance(claim, Mapping):
                continue
            require_schema_versioned_items(
                claim.get("evidence"),
                schema_name=f"{schema_name}.claims[{index}].EvidenceHandle",
                path=path,
            )
    predecessors = data.get("predecessor_records")
    if not isinstance(predecessors, list):
        return
    for index, predecessor in enumerate(predecessors):
        if not isinstance(predecessor, Mapping):
            continue
        _require_target_class_record_schema(
            predecessor,
            path=path,
            schema_name=f"{schema_name}.predecessor_records[{index}]",
        )


def _bound_measurement(
    *,
    name: str,
    measured_mm: float | None,
    nominal_mm: float,
    tolerance_mm: float,
    mode: Literal["within", "max"],
) -> FixtureQcMeasurement:
    passed = False
    if measured_mm is not None:
        if mode == "within":
            passed = abs(measured_mm - nominal_mm) <= tolerance_mm
        else:
            passed = measured_mm <= nominal_mm + tolerance_mm
    return FixtureQcMeasurement(
        name=name,
        measured_mm=measured_mm,
        nominal_mm=nominal_mm,
        tolerance_mm=tolerance_mm,
        passed=passed,
    )


def _fixture_qc_record_id(record: FixtureQcRecord) -> str:
    base = (
        f"{record.fixture_load_name}:"
        f"{record.fixture_params_sha256[:12]}:"
        f"{record.labware_definition_sha256[:12]}"
    )
    if record.pose_digest_sha256:
        return f"{base}:pose-{record.pose_digest_sha256[:12]}"
    return base


def _target_class_record_id(record: TargetClassVerificationRecord) -> str:
    base = (
        f"{record.target_class}:"
        f"{record.robot_serial}:"
        f"slot-{record.slot}:"
    )
    if record.pose_digest_sha256:
        base = f"{base}pose-{record.pose_digest_sha256[:12]}:"
    return f"{base}{record.pipette_name}:{record.pipette_mount}"


def _legacy_image_evidence_record_id(record: LegacyImageEvidenceRecord) -> str:
    digest = hashlib.sha256(
        "|".join(
            [
                record.session_id,
                record.purpose,
                record.target_class,
                record.fixture_load_name,
                record.fixture_params_sha256,
                record.labware_definition_sha256,
                record.image_path,
                record.vision_result_path,
                record.human_note,
                json.dumps(record.labels, sort_keys=True),
            ]
        ).encode("utf-8")
    ).hexdigest()[:12]
    session_part = record.session_id or "no-session"
    return f"legacy_image_evidence:{record.purpose}:{session_part}:{digest}"


def validate_target_class_record(record: TargetClassVerificationRecord) -> ValidationResult:
    reasons = _target_record_validation_reasons(record, ancestors=set())
    return ValidationResult(passed=not reasons, reasons=reasons)


def _target_record_validation_reasons(
    record: TargetClassVerificationRecord,
    *,
    ancestors: set[str],
) -> list[str]:
    reasons: list[str] = []
    target_class = TARGET_CLASS_BY_NAME.get(record.target_class)
    if target_class is None:
        return [f"unknown target class: {record.target_class}"]

    if record.target_class in ancestors:
        return [f"circular predecessor target class: {record.target_class}"]

    if record.result != TargetClassResult.PASSED:
        reasons.append(f"target class result is {record.result.value}, not passed")

    predecessor_by_class = {
        predecessor.target_class: predecessor for predecessor in record.predecessor_records
    }
    missing_predecessors = [
        required for required in target_class.requires if required not in predecessor_by_class
    ]
    if missing_predecessors:
        reasons.append(
            "missing authoritative predecessor target classes: "
            + ", ".join(missing_predecessors)
        )
    next_ancestors = {*ancestors, record.target_class}
    for required in target_class.requires:
        predecessor = predecessor_by_class.get(required)
        if predecessor is None:
            continue
        predecessor_reasons = _target_record_validation_reasons(
            predecessor,
            ancestors=next_ancestors,
        )
        if predecessor_reasons:
            reasons.append(
                f"predecessor target class {required} is not authoritative: "
                + "; ".join(predecessor_reasons)
            )

    reasons.extend(_target_record_claim_reasons(record))

    return _dedupe(reasons)


def _target_record_claim_reasons(record: TargetClassVerificationRecord) -> list[str]:
    reasons: list[str] = []
    claim_type = target_class_verified_claim_type(record.target_class)
    claims = [claim for claim in record.claims if claim.claim_type == claim_type]
    if _has_legacy_target_evidence(record):
        reasons.append("legacy target evidence fields are compatibility-only")
    if not claims:
        reasons.append(f"missing target-class verified claim: {claim_type}")
        return reasons
    if len(claims) > 1:
        reasons.append(f"duplicate target-class verified claims: {record.target_class}")
    evidence_by_id = {handle.evidence_id: handle for handle in record.evidence}
    if not evidence_by_id:
        reasons.append("target-class evidence handles are required")
    for handle in record.evidence:
        reasons.extend(_target_evidence_handle_reasons(handle))
    for claim in claims:
        if claim.value is not True:
            reasons.append(f"target-class claim {claim.claim_id} is not true")
        if claim.quality != EvidenceQuality.USABLE:
            reasons.append(f"target-class claim {claim.claim_id} is not usable")
        if claim.method != TARGET_CLASS_EVIDENCE_METHOD:
            reasons.append(
                f"target-class claim {claim.claim_id} method is not "
                f"{TARGET_CLASS_EVIDENCE_METHOD}"
            )
        if claim.fixture_load_name != record.fixture_load_name:
            reasons.append(f"target-class claim {claim.claim_id} fixture does not match")
        if claim.fixture_params_sha256 != record.fixture_params_sha256:
            reasons.append(
                f"target-class claim {claim.claim_id} params checksum does not match"
            )
        if claim.labware_definition_sha256 != record.labware_definition_sha256:
            reasons.append(
                f"target-class claim {claim.claim_id} labware checksum does not match"
            )
        if not claim.evidence:
            reasons.append(f"target-class claim {claim.claim_id} has no evidence")
        if len(claim.evidence) != 1:
            reasons.append(f"target-class claim {claim.claim_id} must cite one evidence handle")
        for handle in claim.evidence:
            expected_claim_id = target_class_verified_claim_id(
                record.target_class,
                handle.evidence_id,
            )
            if claim.claim_id != expected_claim_id:
                reasons.append(
                    f"target-class claim {claim.claim_id} does not match expected "
                    f"claim ID {expected_claim_id}"
                )
            if handle.evidence_id not in evidence_by_id:
                reasons.append(
                    f"target-class claim {claim.claim_id} references external evidence "
                    f"{handle.evidence_id}"
                )
                continue
            reasons.extend(
                _target_claim_handle_match_reasons(
                    handle,
                    evidence_by_id[handle.evidence_id],
                    claim_id=claim.claim_id,
                )
            )
    return _dedupe(reasons)


def _target_claim_blockers(
    claim: EvidenceClaim,
    *,
    record: TargetClassVerificationRecord,
    session: BridgeSession,
    evidence_by_id: dict[str, EvidenceHandle],
) -> list[str]:
    blockers: list[str] = []
    if claim.value is not True:
        blockers.append(f"target-class claim {claim.claim_id} is not true")
    if claim.quality != EvidenceQuality.USABLE:
        blockers.append(f"target-class claim {claim.claim_id} is not usable")
    if claim.method != TARGET_CLASS_EVIDENCE_METHOD:
        blockers.append(
            f"target-class claim {claim.claim_id} method is not "
            f"{TARGET_CLASS_EVIDENCE_METHOD}"
        )
    else:
        blockers.extend(_committed_target_claim_blockers(claim, session=session))
    if claim.session_id != session.session_id:
        blockers.append(f"target-class claim {claim.claim_id} session does not match")
    if claim.fixture_load_name != session.fixture_identity.load_name:
        blockers.append(f"target-class claim {claim.claim_id} fixture does not match")
    if claim.fixture_params_sha256 != session.fixture_identity.params_sha256:
        blockers.append(f"target-class claim {claim.claim_id} params checksum does not match")
    if claim.labware_definition_sha256 != session.fixture_identity.labware_definition_sha256:
        blockers.append(f"target-class claim {claim.claim_id} labware checksum does not match")
    if not claim.evidence:
        blockers.append(f"target-class claim {claim.claim_id} has no evidence")
    if len(claim.evidence) != 1:
        blockers.append(f"target-class claim {claim.claim_id} must cite one evidence handle")
    for handle in claim.evidence:
        expected_claim_id = target_class_verified_claim_id(record.target_class, handle.evidence_id)
        if claim.claim_id != expected_claim_id:
            blockers.append(
                f"target-class claim {claim.claim_id} does not match expected "
                f"claim ID {expected_claim_id}"
            )
        record_handle = evidence_by_id.get(handle.evidence_id)
        if record_handle is None:
            blockers.append(
                f"target-class claim {claim.claim_id} references external evidence "
                f"{handle.evidence_id}"
            )
            continue
        blockers.extend(
            _target_claim_handle_match_reasons(
                handle,
                record_handle,
                claim_id=claim.claim_id,
            )
        )
        blockers.extend(_target_evidence_handle_blockers(record_handle, session=session))
        if claim.method == TARGET_CLASS_EVIDENCE_METHOD:
            blockers.extend(
                _target_evidence_artifact_blockers(
                    record_handle,
                    record=record,
                    session=session,
                )
            )
    return blockers


def _target_claim_handle_match_reasons(
    claim_handle: EvidenceHandle,
    record_handle: EvidenceHandle,
    *,
    claim_id: str,
) -> list[str]:
    reasons: list[str] = []
    comparisons = {
        "source kind": claim_handle.source_kind == record_handle.source_kind,
        "path": claim_handle.path == record_handle.path,
        "checksum": claim_handle.checksum_sha256 == record_handle.checksum_sha256,
        "session": claim_handle.session_id == record_handle.session_id,
        "quality": claim_handle.quality == record_handle.quality,
    }
    for label, passed in comparisons.items():
        if not passed:
            reasons.append(
                f"target-class claim {claim_id} evidence {claim_handle.evidence_id} "
                f"{label} does not match record evidence"
            )
    return reasons


def _committed_target_claim_blockers(
    claim: EvidenceClaim,
    *,
    session: BridgeSession,
) -> list[str]:
    if not _requires_committed_session_claim(session):
        return []
    try:
        committed_claims = load_committed_evidence_claims(
            index_path=session.evidence_index_path,
            root=_transaction_root_for_index(Path(session.evidence_index_path)),
        )
    except (OSError, ValueError) as exc:
        return [f"target-class claim transaction store could not be read: {exc}"]
    matching_claims = [
        committed for committed in committed_claims if committed.claim_id == claim.claim_id
    ]
    if not matching_claims:
        return [f"target-class claim {claim.claim_id} is not committed in session evidence"]
    if not any(_claims_authority_equivalent(committed, claim) for committed in matching_claims):
        return [f"target-class claim {claim.claim_id} does not match committed session claim"]
    return []


def _claims_authority_equivalent(
    committed: EvidenceClaim,
    record_claim: EvidenceClaim,
) -> bool:
    return (
        committed.claim_id == record_claim.claim_id
        and committed.claim_type == record_claim.claim_type
        and committed.value == record_claim.value
        and committed.session_id == record_claim.session_id
        and committed.fixture_load_name == record_claim.fixture_load_name
        and committed.fixture_params_sha256 == record_claim.fixture_params_sha256
        and committed.labware_definition_sha256 == record_claim.labware_definition_sha256
        and committed.pose_digest_sha256 == record_claim.pose_digest_sha256
        and committed.method == record_claim.method
        and committed.quality == record_claim.quality
        and _evidence_handles_authority_equivalent(
            committed.evidence,
            record_claim.evidence,
        )
    )


def _evidence_handles_authority_equivalent(
    committed: list[EvidenceHandle],
    record_handles: list[EvidenceHandle],
) -> bool:
    if len(committed) != len(record_handles):
        return False
    committed_by_id = {handle.evidence_id: handle for handle in committed}
    record_by_id = {handle.evidence_id: handle for handle in record_handles}
    if set(committed_by_id) != set(record_by_id):
        return False
    return all(
        _evidence_handle_authority_equivalent(committed_by_id[evidence_id], record_handle)
        for evidence_id, record_handle in record_by_id.items()
    )


def _evidence_handle_authority_equivalent(
    committed: EvidenceHandle,
    record_handle: EvidenceHandle,
) -> bool:
    return (
        committed.evidence_id == record_handle.evidence_id
        and committed.source_kind == record_handle.source_kind
        and committed.path == record_handle.path
        and committed.checksum_sha256 == record_handle.checksum_sha256
        and committed.session_id == record_handle.session_id
        and committed.quality == record_handle.quality
    )


def _requires_committed_session_claim(session: BridgeSession) -> bool:
    if not session.evidence_index_path:
        return False
    index_path = Path(session.evidence_index_path)
    return index_path.name == "evidence_index.json" and (
        index_path.parent.name == _safe_path_segment(session.session_id)
    )


def _target_evidence_artifact_blockers(
    handle: EvidenceHandle,
    *,
    record: TargetClassVerificationRecord,
    session: BridgeSession,
) -> list[str]:
    if not _requires_committed_session_claim(session):
        return []
    try:
        from aevum_ot2.core.target_evidence import (
            target_class_evidence_artifact_scope_reasons,
        )
    except ImportError as exc:  # pragma: no cover - import wiring failure.
        return [f"target-class evidence artifact validator unavailable: {exc}"]
    return target_class_evidence_artifact_scope_reasons(
        record,
        session=session,
        artifact_path=handle.path,
    )


def _target_evidence_handle_blockers(
    handle: EvidenceHandle,
    *,
    session: BridgeSession,
) -> list[str]:
    blockers = _target_evidence_handle_reasons(handle)
    if handle.session_id != session.session_id:
        blockers.append(f"target evidence handle {handle.evidence_id} session does not match")
    return blockers


def _target_evidence_handle_reasons(handle: EvidenceHandle) -> list[str]:
    reasons: list[str] = []
    if handle.quality != EvidenceQuality.USABLE:
        reasons.append(f"target evidence handle {handle.evidence_id} is not usable")
    if not handle.path:
        reasons.append(f"target evidence handle {handle.evidence_id} has no path")
    if not handle.checksum_sha256:
        reasons.append(f"target evidence handle {handle.evidence_id} has no checksum")
    if handle.path and handle.checksum_sha256:
        path = Path(handle.path)
        if not path.is_file():
            reasons.append(f"target evidence handle {handle.evidence_id} path does not exist")
        elif _sha256_file(path) != handle.checksum_sha256:
            reasons.append(f"target evidence handle {handle.evidence_id} checksum mismatch")
    return reasons


def _target_record_session_scope_blockers(
    record: TargetClassVerificationRecord,
    session: BridgeSession,
) -> list[str]:
    blockers: list[str] = []
    if record.robot_serial != (session.robot_serial or ""):
        blockers.append("target record robot serial does not match session")
    if record.robot_server_version != (session.robot_server_version or ""):
        blockers.append("target record robot server version does not match session")
    if record.slot != session.slot:
        blockers.append("target record slot does not match session")
    if record.fixture_load_name != session.fixture_identity.load_name:
        blockers.append("target record fixture load name does not match session")
    if record.fixture_params_sha256 != session.fixture_identity.params_sha256:
        blockers.append("target record fixture params checksum does not match session")
    if record.labware_definition_sha256 != session.fixture_identity.labware_definition_sha256:
        blockers.append("target record labware checksum does not match session")
    if session.fixture_pose_digest_sha256:
        if not record.pose_digest_sha256:
            blockers.append("target record pose digest is missing")
        elif record.pose_digest_sha256 != session.fixture_pose_digest_sha256:
            blockers.append("target record pose digest does not match session")
    return blockers


def _target_record_reference_scope_blockers(
    record: TargetClassVerificationRecord,
    reference_record: TargetClassVerificationRecord,
) -> list[str]:
    blockers: list[str] = []
    if record.pipette_name != reference_record.pipette_name:
        blockers.append("predecessor target pipette name does not match target record")
    if record.pipette_mount != reference_record.pipette_mount:
        blockers.append("predecessor target pipette mount does not match target record")
    if record.tiprack_load_name != reference_record.tiprack_load_name:
        blockers.append("predecessor target tiprack does not match target record")
    return blockers


def _has_legacy_target_evidence(record: TargetClassVerificationRecord) -> bool:
    return bool(
        record.legacy_camera_images
        or record.legacy_vision_results
        or record.legacy_commissioning_observation
    )


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
