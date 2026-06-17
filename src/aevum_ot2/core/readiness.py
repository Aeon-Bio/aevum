from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from aevum_ot2.core.evidence import (
    DEFAULT_EVIDENCE_TRANSACTION_ROOT,
    load_committed_evidence_claims,
)
from aevum_ot2.core.gates import (
    fixture_qc_gate_from_legacy_record,
    registration_gate_result,
)
from aevum_ot2.core.models import (
    BridgeSession,
    BridgeSessionState,
    EvidenceClaim,
    GateResult,
)
from aevum_ot2.core.pose import FixturePose, load_fixture_pose, pose_match_gate
from aevum_ot2.core.records import (
    TARGET_CLASS_BY_NAME,
    RecordHandle,
    TargetClassResult,
    fixture_qc_record_handle,
    load_fixture_qc_record,
    load_target_class_record,
    target_class_names,
    target_class_record_handle,
    validate_fixture_qc_record,
)
from aevum_ot2.core.schema import SchemaVersionError


class ReadinessResult(BaseModel):
    session_id: str
    registration_ready: bool
    low_z_ready: bool = False
    motion_allowed: bool = False
    reasons: list[str] = Field(default_factory=list)
    gate_result: GateResult | None = None
    pose_gate: GateResult | None = None
    fixture_qc_record: RecordHandle | None = None
    target_class_records: list[RecordHandle] = Field(default_factory=list)


def evaluate_registration_readiness(
    session: BridgeSession,
    *,
    fixture_qc_record: RecordHandle | str | Path,
    target_class_records: list[RecordHandle | str | Path],
    fixture_pose: FixturePose | str | Path | None = None,
    pose_claims: list[EvidenceClaim] | None = None,
    evidence_transaction_root: str | Path = DEFAULT_EVIDENCE_TRANSACTION_ROOT,
) -> ReadinessResult:
    """Join Lane A session state with Lane B records without authorizing motion."""

    reasons: list[str] = []
    checked_at = datetime.now()
    qc_handle = _coerce_fixture_qc_handle(fixture_qc_record, reasons)
    target_handles = [
        _coerce_target_class_handle(record, reasons) for record in target_class_records
    ]
    target_handles = [handle for handle in target_handles if handle is not None]

    _check_session(session, reasons, checked_at=checked_at)
    pose_gate = _session_pose_gate(
        session,
        fixture_pose=fixture_pose,
        pose_claims=pose_claims,
        evidence_transaction_root=evidence_transaction_root,
        checked_at=checked_at,
        reasons=reasons,
    )

    qc_record = None
    fixture_qc_gate = None
    if qc_handle is not None:
        try:
            qc_record = load_fixture_qc_record(qc_handle.path)
        except OSError as exc:
            reasons.append(f"fixture QC record could not be read: {exc}")
        else:
            qc_result = validate_fixture_qc_record(qc_record, readiness="registration")
            reasons.extend(qc_result.reasons)
            fixture_qc_gate = fixture_qc_gate_from_legacy_record(
                qc_record,
                record_handle=qc_handle,
            )
            _check_fixture_identity(
                label="fixture QC record",
                fixture_load_name=qc_record.fixture_load_name,
                fixture_params_sha256=qc_record.fixture_params_sha256,
                labware_definition_sha256=qc_record.labware_definition_sha256,
                session=session,
                reasons=reasons,
            )
            _check_pose_digest_scope(
                label="fixture QC record",
                pose_digest_sha256=qc_record.pose_digest_sha256,
                session=session,
                reasons=reasons,
            )

    target_records = []
    for handle in target_handles:
        try:
            target_record = load_target_class_record(handle.path)
        except OSError as exc:
            reasons.append(f"target-class record could not be read: {handle.path}: {exc}")
            continue
        target_records.append(target_record)
        _check_fixture_identity(
            label=f"target-class record {target_record.target_class}",
            fixture_load_name=target_record.fixture_load_name,
            fixture_params_sha256=target_record.fixture_params_sha256,
            labware_definition_sha256=target_record.labware_definition_sha256,
            session=session,
            reasons=reasons,
        )
        if target_record.slot != session.slot:
            reasons.append(
                f"target-class record {target_record.target_class} slot {target_record.slot} "
                f"does not match session slot {session.slot}"
            )
        if session.robot_serial and target_record.robot_serial != session.robot_serial:
            reasons.append(
                f"target-class record {target_record.target_class} robot "
                f"{target_record.robot_serial} does not match session robot {session.robot_serial}"
            )
        if (
            session.robot_server_version
            and target_record.robot_server_version != session.robot_server_version
        ):
            reasons.append(
                f"target-class record {target_record.target_class} robot-server "
                f"{target_record.robot_server_version} does not match session "
                f"{session.robot_server_version}"
            )
        if session.pipette_name and target_record.pipette_name != session.pipette_name:
            reasons.append(
                f"target-class record {target_record.target_class} pipette "
                f"{target_record.pipette_name} does not match session pipette "
                f"{session.pipette_name}"
            )
        if session.pipette_mount and target_record.pipette_mount != session.pipette_mount:
            reasons.append(
                f"target-class record {target_record.target_class} pipette mount "
                f"{target_record.pipette_mount} does not match session pipette mount "
                f"{session.pipette_mount}"
            )
        if target_record.target_class not in TARGET_CLASS_BY_NAME:
            reasons.append(f"unknown target class: {target_record.target_class}")
        if target_record.result == TargetClassResult.FAILED:
            reasons.append(f"target class {target_record.target_class} is failed")
        _check_pose_digest_scope(
            label=f"target-class record {target_record.target_class}",
            pose_digest_sha256=target_record.pose_digest_sha256,
            session=session,
            reasons=reasons,
        )

    observed_target_classes = {record.target_class for record in target_records}
    missing_target_classes = sorted(set(target_class_names()) - observed_target_classes)
    if missing_target_classes:
        reasons.append("missing target-class records: " + ", ".join(missing_target_classes))
    gate_result = registration_gate_result(
        blockers=reasons,
        fixture_qc_gate=fixture_qc_gate,
        pose_gate=pose_gate,
        missing_target_classes=missing_target_classes,
    )

    return ReadinessResult(
        session_id=session.session_id,
        registration_ready=not reasons,
        low_z_ready=False,
        motion_allowed=False,
        reasons=reasons,
        gate_result=gate_result,
        pose_gate=pose_gate,
        fixture_qc_record=qc_handle,
        target_class_records=target_handles,
    )


def _coerce_fixture_qc_handle(
    value: RecordHandle | str | Path,
    reasons: list[str],
) -> RecordHandle | None:
    if isinstance(value, RecordHandle):
        if value.record_type != "fixture_qc":
            reasons.append(f"expected fixture_qc handle, got {value.record_type}")
            return None
        return value

    path = Path(value)
    try:
        record = load_fixture_qc_record(path)
    except OSError as exc:
        reasons.append(f"fixture QC record could not be read: {path}: {exc}")
        return None
    return fixture_qc_record_handle(record, path)


def _coerce_target_class_handle(
    value: RecordHandle | str | Path,
    reasons: list[str],
) -> RecordHandle | None:
    if isinstance(value, RecordHandle):
        if value.record_type != "target_class_verification":
            reasons.append(f"expected target_class_verification handle, got {value.record_type}")
            return None
        return value

    path = Path(value)
    try:
        record = load_target_class_record(path)
    except OSError as exc:
        reasons.append(f"target-class record could not be read: {path}: {exc}")
        return None
    return target_class_record_handle(record, path)


def _check_session(
    session: BridgeSession,
    reasons: list[str],
    *,
    checked_at: datetime,
) -> None:
    if session.state == BridgeSessionState.READY_NO_MOTION:
        if session.motion_allowed:
            reasons.append("ready_no_motion session unexpectedly allows motion")
    elif session.state == BridgeSessionState.MOTION_COMMISSIONING_ARMED:
        if not session.motion_allowed:
            reasons.append("motion_commissioning_armed session is not motion-armed")
    else:
        reasons.append(f"session state is {session.state}, not ready_no_motion")
    if session.lease_expires_at <= checked_at:
        reasons.append("session lease is expired")
    if session.maintenance_run_id is None:
        reasons.append("session has no maintenance run ID")
    if session.definition_uri is None:
        reasons.append("session has no uploaded labware definition URI")
    if session.loaded_labware_id is None:
        reasons.append("session has no loaded fixture labware ID")
    if not session.fixture_identity.dimensions_match:
        reasons.append("session fixture identity dimensions do not match generated labware")


def _session_pose_gate(
    session: BridgeSession,
    *,
    fixture_pose: FixturePose | str | Path | None,
    pose_claims: list[EvidenceClaim] | None,
    evidence_transaction_root: str | Path,
    checked_at: datetime,
    reasons: list[str],
) -> GateResult | None:
    if not session.fixture_pose_digest_sha256:
        return None

    pose = _load_session_pose(session, fixture_pose=fixture_pose, reasons=reasons)
    claims = _load_session_pose_claims(
        session,
        pose_claims=pose_claims,
        evidence_transaction_root=evidence_transaction_root,
        reasons=reasons,
    )
    gate = pose_match_gate(
        pose,
        expected_pose_digest_sha256=session.fixture_pose_digest_sha256,
        expected_session_id=session.session_id,
        expected_robot_url=session.robot_url,
        expected_fixture_params_sha256=session.fixture_identity.params_sha256,
        expected_evidence_index_path=session.evidence_index_path,
        expected_claim_not_before=session.updated_at,
        claim_expires_at=session.lease_expires_at,
        claim_valid_at=checked_at,
        claims=claims,
    )
    for blocker in gate.blockers:
        reasons.append(f"fixture pose blocker: {blocker}")
    for missing_claim in gate.missing_claims:
        reasons.append(f"missing fixture pose input: {missing_claim}")
    return gate


def _load_session_pose(
    session: BridgeSession,
    *,
    fixture_pose: FixturePose | str | Path | None,
    reasons: list[str],
) -> FixturePose | None:
    source = fixture_pose or session.fixture_pose_path
    if not source:
        reasons.append("session has pose digest but no fixture pose path")
        return None
    if isinstance(source, FixturePose):
        return source
    try:
        return load_fixture_pose(source)
    except (OSError, SchemaVersionError, ValidationError, ValueError) as exc:
        reasons.append(f"fixture pose could not be read: {source}: {exc}")
        return None


def _load_session_pose_claims(
    session: BridgeSession,
    *,
    pose_claims: list[EvidenceClaim] | None,
    evidence_transaction_root: str | Path,
    reasons: list[str],
) -> list[EvidenceClaim]:
    if pose_claims is not None:
        claims = pose_claims
    else:
        try:
            claims = load_committed_evidence_claims(
                index_path=session.evidence_index_path,
                root=evidence_transaction_root,
            )
        except (OSError, SchemaVersionError, ValidationError, ValueError) as exc:
            reasons.append(f"pose claims could not be read: {exc}")
            return []
    scoped_claims = [
        claim for claim in claims if claim.session_id == session.session_id
    ]
    dropped = len(claims) - len(scoped_claims)
    if dropped:
        reasons.append(f"ignored {dropped} fixture pose claim(s) from another session")
    return scoped_claims


def _check_pose_digest_scope(
    *,
    label: str,
    pose_digest_sha256: str,
    session: BridgeSession,
    reasons: list[str],
) -> None:
    if session.fixture_pose_digest_sha256:
        if not pose_digest_sha256:
            reasons.append(f"{label} has no pose digest for pose-scoped session")
        elif pose_digest_sha256 != session.fixture_pose_digest_sha256:
            reasons.append(f"{label} pose digest does not match session pose")
    elif pose_digest_sha256:
        reasons.append(f"{label} has pose digest but session is pose-unknown")


def _check_fixture_identity(
    *,
    label: str,
    fixture_load_name: str,
    fixture_params_sha256: str,
    labware_definition_sha256: str,
    session: BridgeSession,
    reasons: list[str],
) -> None:
    identity = session.fixture_identity
    if fixture_load_name != identity.load_name:
        reasons.append(
            f"{label} fixture {fixture_load_name} does not match session fixture "
            f"{identity.load_name}"
        )
    if fixture_params_sha256 != identity.params_sha256:
        reasons.append(f"{label} params checksum does not match session fixture")
    if labware_definition_sha256 != identity.labware_definition_sha256:
        reasons.append(f"{label} labware checksum does not match session fixture")
