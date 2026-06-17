from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

import aevum_ot2.server.service as service_module
from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.command_journal import (
    list_command_journal_entries,
    read_command_journal_entry,
)
from aevum_ot2.core.context import build_session_context
from aevum_ot2.core.dispatch_preparation import (
    FIRST_LOW_Z_DRY_SPEED_MM_PER_S,
    FIRST_LOW_Z_DRY_TOP_OFFSET_MM,
    _command_body_for_operation,
    _move_low_z_command_body,
    build_motion_dispatch_preparation_for_approval,
    build_motion_dispatch_preparation_for_reservation,
)
from aevum_ot2.core.dispatch_reservation import (
    MotionDispatchReservation,
    read_motion_dispatch_reservation,
    read_motion_dispatch_reservation_for_approval,
)
from aevum_ot2.core.lock import read_lock, write_lock
from aevum_ot2.core.models import (
    BridgeLock,
    BridgeSession,
    BridgeSessionState,
    EndpointResult,
    EvidenceClaim,
    EvidenceHandle,
    EvidenceQuality,
    EvidenceSourceKind,
    GateName,
    GateResult,
    OffsetAuthorityState,
    OffsetRecord,
    OffsetRegistry,
    RobotStatus,
)
from aevum_ot2.core.motion_approval import (
    MotionApproval,
    build_motion_approval,
    plan_fragment_digest,
)
from aevum_ot2.core.motion_commissioning import (
    MISSING_APPROVAL_REASON,
    arm_motion_commissioning,
    consume_motion_approval,
    list_motion_approval_records,
    read_motion_approval_record,
)
from aevum_ot2.core.plans import PlanFragment, PlanStep
from aevum_ot2.core.readiness import ReadinessResult, evaluate_registration_readiness
from aevum_ot2.core.records import (
    TARGET_CLASS_EVIDENCE_METHOD,
    TargetClassResult,
    TargetClassVerificationRecord,
    scaffold_fixture_qc_record,
    scaffold_target_class_records,
    target_class_names,
    target_class_verified_claim_id,
    target_class_verified_claim_type,
    write_fixture_qc_record,
    write_target_class_record,
)
from aevum_ot2.core.recovery import NoMotionRecoveryDisposition
from aevum_ot2.core.registry import offset_record_id
from aevum_ot2.core.safety import (
    FixtureSafetyProfile,
    _safety_profile_digest,
    build_fixture_safety_profile,
)
from aevum_ot2.core.sessions import read_session, write_session
from aevum_ot2.core.validation import (
    PlanValidationResult,
    StepValidationResult,
    validate_plan_fragment,
)
from aevum_ot2.server.service import BridgeService

TARGET_EVIDENCE_PATH = Path(__file__).parent / "fixtures" / "target_evidence.json"


def _session(
    session_id: str = "session-1",
    state: str = "ready_no_motion",
) -> BridgeSession:
    identity = current_fixture_identity()
    now = datetime.now()
    return BridgeSession(
        session_id=session_id,
        kind="registration",
        owner_id="agent-1",
        robot_url="http://ot2.local:31950",
        robot_serial="OT2TEST0001",
        robot_server_version="9.0.0",
        max_protocol_api_version="2.28",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        pipette_model="p300_single_v2.1",
        pipette_id="pipette-1",
        pipette_tip_length_mm=51.7,
        state=state,
        created_at=now,
        updated_at=now,
        lease_expires_at=now + timedelta(minutes=10),
        maintenance_run_id="maintenance-run-1",
        slot="1",
        fixture_identity=identity,
        definition_uri="aevum/aevum_p300_poc_fixture/1",
        loaded_labware_id="fixture-1",
        last_command_id="command-1",
        last_command_key="load-key-1",
        last_command_status="succeeded",
        evidence_index_path="data/measurements/ot2_evidence_index.json",
    )


def _pose_scoped_session(
    *,
    state: str = "ready_no_motion",
    motion_allowed: bool = False,
) -> BridgeSession:
    return _session(state=state).model_copy(
        update={
            "fixture_orientation": "rot180",
            "fixture_pose_digest_sha256": "a" * 64,
            "fixture_pose_path": "data/measurements/sessions/session-1/fixture_pose.json",
            "motion_allowed": motion_allowed,
        }
    )


def _readiness(ready: bool = True) -> ReadinessResult:
    return ReadinessResult(
        session_id="session-1",
        registration_ready=ready,
        reasons=[] if ready else ["missing target-class records"],
    )


def _live_status(
    session: BridgeSession,
    *,
    pipette_name: str = "p300_single_gen2",
    api_version: str = "9.0.0",
) -> RobotStatus:
    return RobotStatus(
        robot_url=session.robot_url,
        checked_at=datetime.now(),
        health=EndpointResult(
            path="/health",
            ok=True,
            data={
                "robot_serial": session.robot_serial,
                "api_version": api_version,
                "maximum_protocol_api_version": [2, 28],
            },
        ),
        pipettes=EndpointResult(
            path="/pipettes",
            ok=True,
            data={
                "left": {
                    "name": pipette_name,
                    "model": session.pipette_model,
                    "id": session.pipette_id,
                    "tip_length": session.pipette_tip_length_mm,
                },
                "right": {},
            },
        ),
    )


def _patch_live_status(monkeypatch: pytest.MonkeyPatch, status: RobotStatus) -> None:
    class FakeClient:
        def __init__(self, robot_url: str, **_kwargs: object) -> None:
            self.robot_url = robot_url

        def status(self) -> RobotStatus:
            return status

    monkeypatch.setattr(service_module, "Ot2Client", FakeClient)


def _run_readback(
    session: BridgeSession,
    *,
    status: str = "idle",
    current: bool = True,
    offset_id: str | None = None,
    offset_vector: dict[str, float] | None = None,
) -> EndpointResult:
    labware: dict[str, object] = {
        "id": session.loaded_labware_id,
        "loadName": "aevum_p300_poc_fixture",
        "definitionUri": session.definition_uri,
        "location": {"slotName": session.slot},
    }
    labware_offsets: list[dict[str, object]] = []
    if offset_id is not None:
        labware["offsetId"] = offset_id
        labware_offsets.append(
            {
                "id": offset_id,
                "definitionUri": session.definition_uri,
                "location": {"slotName": session.slot},
                "vector": offset_vector or {"x": 0.0, "y": 0.0, "z": 0.0},
            }
        )
    return EndpointResult(
        path=f"/maintenance_runs/{session.maintenance_run_id}",
        ok=True,
        data={
            "data": {
                "id": session.maintenance_run_id,
                "status": status,
                "current": current,
                "errors": [],
                "pipettes": [],
                "modules": [],
                "labware": [labware],
                "liquids": [],
                "liquidClasses": [],
                "labwareOffsets": labware_offsets,
            }
        },
    )


def _command_history_readback(
    session: BridgeSession,
    *commands: dict[str, object],
) -> EndpointResult:
    history = list(commands) or [
        {
            "id": session.last_command_id,
            "key": session.last_command_key,
            "commandType": "loadLabware",
            "status": session.last_command_status,
            "params": {},
            "createdAt": "2026-05-06T00:00:00",
        }
    ]
    return EndpointResult(
        path=f"/maintenance_runs/{session.maintenance_run_id}/commands?pageLength=1000",
        ok=True,
        data={"data": history, "meta": {"totalLength": len(history)}},
    )


def _patch_dispatch_readbacks(
    monkeypatch: pytest.MonkeyPatch,
    service: BridgeService,
    session: BridgeSession,
    *,
    run_result: EndpointResult | None = None,
    command_history_result: EndpointResult | None = None,
) -> None:
    monkeypatch.setattr(
        service,
        "_live_motion_dispatch_readbacks",
        lambda _session: (
            run_result or _run_readback(session),
            command_history_result or _command_history_readback(session),
        ),
    )


def _preparation_for_approval(
    approval: MotionApproval,
    session: BridgeSession,
    plan: PlanFragment,
    profile: FixtureSafetyProfile,
):
    result = build_motion_dispatch_preparation_for_approval(
        approval=approval,
        session=session,
        plan=plan,
        safety_profile=profile,
        run_result=_run_readback(session),
        command_history_result=_command_history_readback(session),
    )
    assert result.preparation is not None
    return result.preparation


def _write_active_lock(
    session: BridgeSession,
    db_path: Path,
    *,
    expires_in: timedelta = timedelta(minutes=10),
    state: str = "motion_commissioning_armed",
) -> None:
    now = datetime.now()
    write_lock(
        BridgeLock(
            robot_url=session.robot_url,
            session_id=session.session_id,
            owner_id=session.owner_id,
            lease_started_at=now,
            lease_expires_at=now + expires_in,
            active_run_id=session.maintenance_run_id,
            last_command_id=session.last_command_id,
            state=state,
        ),
        db_path,
    )


def _target_record(
    target_class: str,
    *,
    result: TargetClassResult = TargetClassResult.BLOCKED,
    offset_registry_record: str = "not-yet-registered",
) -> TargetClassVerificationRecord:
    identity = current_fixture_identity()
    return TargetClassVerificationRecord(
        target_class=target_class,
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        robot_serial="OT2TEST0001",
        robot_server_version="9.0.0",
        slot="1",
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        tiprack_load_name="opentrons_96_tiprack_300ul",
        offset_registry_record=offset_registry_record,
        result=result,
    )


def _verified_target_record(
    session: BridgeSession,
    target_class: str,
    *,
    offset_registry_record: str = "not-yet-registered",
) -> TargetClassVerificationRecord:
    record = _target_record(
        target_class,
        result=TargetClassResult.PASSED,
        offset_registry_record=offset_registry_record,
    )
    evidence = _target_evidence_handle(session, target_class)
    claim = _target_claim(session, target_class, evidence)
    return record.model_copy(update={"evidence": [evidence], "claims": [claim]})


def _target_evidence_handle(
    session: BridgeSession,
    target_class: str,
) -> EvidenceHandle:
    return EvidenceHandle(
        evidence_id=f"target-evidence:{target_class}",
        source_kind=EvidenceSourceKind.VISION_ANALYSIS,
        path=str(TARGET_EVIDENCE_PATH),
        checksum_sha256=_sha256_file(TARGET_EVIDENCE_PATH),
        session_id=session.session_id,
        quality=EvidenceQuality.USABLE,
    )


def _target_claim(
    session: BridgeSession,
    target_class: str,
    handle: EvidenceHandle,
) -> EvidenceClaim:
    identity = session.fixture_identity
    return EvidenceClaim(
        claim_id=target_class_verified_claim_id(target_class, handle.evidence_id),
        claim_type=target_class_verified_claim_type(target_class),
        value=True,
        session_id=session.session_id,
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        method=TARGET_CLASS_EVIDENCE_METHOD,
        quality=EvidenceQuality.USABLE,
        evidence=[handle],
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safety_profile(session: BridgeSession) -> FixtureSafetyProfile:
    nominal = session.fixture_identity.nominal_dimensions_mm
    qc_record = scaffold_fixture_qc_record(
        session.fixture_identity,
        x_bound_mm=nominal["x"],
        y_bound_mm=nominal["y"],
        z_bound_mm=nominal["z"],
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )
    result = build_fixture_safety_profile(
        session.fixture_identity,
        fixture_qc_record=qc_record,
    )
    assert result.profile is not None
    return result.profile


def _pose_scoped_profile(session: BridgeSession) -> FixtureSafetyProfile:
    profile = _safety_profile(session).model_copy(
        update={
            "pose_digest_sha256": session.fixture_pose_digest_sha256,
            "safety_profile_sha256": "",
        }
    )
    return profile.model_copy(
        update={"safety_profile_sha256": _safety_profile_digest(profile)}
    )


def _promoted_offset(
    session: BridgeSession,
    profile: FixtureSafetyProfile,
    target_class: str,
) -> OffsetRecord:
    identity = session.fixture_identity
    return OffsetRecord(
        offset_record_id="offset-1",
        authority_state=OffsetAuthorityState.PROMOTED,
        robot_serial=session.robot_serial or "",
        robot_server_version=session.robot_server_version,
        opentrons_api_version=session.max_protocol_api_version,
        fixture_load_name=identity.load_name,
        fixture_definition_uri=session.definition_uri or "",
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        slot=session.slot,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        tiprack_load_name="opentrons_96_tiprack_300ul",
        offset_mm={"x": 1.5, "y": 0.0, "z": 0.0},
        verification_targets=[target_class],
        evidence_file="data/measurements/offsets/offset-1.json",
        safety_profile_sha256=profile.safety_profile_sha256,
        target_policy_digest_sha256=profile.target_policy_digest_sha256,
    )


def _low_z_plan(
    session: BridgeSession,
    target_class: str = "offset_x_1p5_low_z_dry",
) -> PlanFragment:
    return PlanFragment(
        session_id=session.session_id,
        steps=[
            PlanStep(
                step_id="low-z",
                operation="move_low_z",
                target_class=target_class,
            )
        ],
    )


def _home_plan(session: BridgeSession) -> PlanFragment:
    return PlanFragment(
        session_id=session.session_id,
        steps=[PlanStep(step_id="home", operation="home")],
    )


def _high_z_plan(
    session: BridgeSession,
    target_class: str = "center_high_z",
) -> PlanFragment:
    return PlanFragment(
        session_id=session.session_id,
        steps=[
            PlanStep(
                step_id="high-z",
                operation="move_high_z",
                target_class=target_class,
            )
        ],
    )


def _home_approval(
    session: BridgeSession,
    profile: FixtureSafetyProfile,
) -> MotionApproval:
    return build_motion_approval(
        _home_plan(session),
        session=session,
        safety_profile=profile,
        step_id="home",
        approved_by="unit-test",
    )


def _approved_home_validation(session: BridgeSession, approval_id: str) -> PlanValidationResult:
    return PlanValidationResult(
        session_id=session.session_id,
        allowed=True,
        motion_allowed=True,
        motion_approval_id=approval_id,
        steps=[
            StepValidationResult(
                step_id="home",
                operation="home",
                allowed=True,
                requires_motion=True,
                gate_results=[GateResult(gate_name=GateName.HOME_CLEARANCE, passed=True)],
            )
        ],
    )


def _missing_motion_approval_validation(session: BridgeSession) -> PlanValidationResult:
    return PlanValidationResult(
        session_id=session.session_id,
        allowed=False,
        motion_allowed=False,
        reasons=[MISSING_APPROVAL_REASON],
        steps=[
            StepValidationResult(
                step_id="home",
                operation="home",
                allowed=True,
                requires_motion=True,
                gate_results=[GateResult(gate_name=GateName.HOME_CLEARANCE, passed=True)],
            )
        ],
    )


def _write_complete_registration_records(
    tmp_path: Path,
    session: BridgeSession,
    *,
    offset_registry_record: str = "not-yet-registered",
) -> tuple[Path, list[Path]]:
    nominal = session.fixture_identity.nominal_dimensions_mm
    qc_record = scaffold_fixture_qc_record(
        session.fixture_identity,
        x_bound_mm=nominal["x"],
        y_bound_mm=nominal["y"],
        z_bound_mm=nominal["z"],
        camera_capture_indexed=True,
        fixture_visible=True,
        vision_evidence_ok=True,
        base_seated=True,
        guide_holes_open=True,
        support_debris_absent=True,
        mock_wells_undeformed=True,
        no_warping_lift=True,
    )
    qc_path = tmp_path / "fixture_qc.json"
    write_fixture_qc_record(qc_record, qc_path)

    target_paths: list[Path] = []
    for record in scaffold_target_class_records(
        session,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
    ):
        if record.target_class == "offset_x_1p5_high_z":
            record = _verified_target_record(session, "offset_x_1p5_high_z")
        if record.target_class == "offset_x_1p5_low_z_dry":
            record.offset_registry_record = offset_registry_record
        target_path = tmp_path / f"{record.target_class}.json"
        write_target_class_record(record, target_path)
        target_paths.append(target_path)

    return qc_path, target_paths


def test_complete_registration_readiness_does_not_authorize_motion(
    tmp_path: Path,
) -> None:
    session = _session()
    qc_path, target_paths = _write_complete_registration_records(tmp_path, session)

    readiness = evaluate_registration_readiness(
        session,
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
    )
    context = build_session_context(session, readiness=readiness)

    assert readiness.registration_ready is True
    assert readiness.low_z_ready is False
    assert readiness.motion_allowed is False
    assert context.motion_allowed is False
    assert "prepare_registration_plan" in context.allowed_next_ops
    assert "move_low_z" not in context.allowed_next_ops


def test_motion_backend_boundary_blocks_without_motion_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    profile = _safety_profile(session)
    offset = _promoted_offset(session, profile, "offset_x_1p5_low_z_dry")
    write_session(session, db_path)
    _write_active_lock(session, db_path)
    _patch_live_status(monkeypatch, _live_status(session))
    qc_path, target_paths = _write_complete_registration_records(
        tmp_path,
        session,
        offset_registry_record=offset_record_id(offset),
    )
    service = BridgeService(state_db_path=db_path, motion_enabled=True)

    result = service.execute_next(
        session.session_id,
        _low_z_plan(session),
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
        offset_registry=OffsetRegistry(records=[offset]),
        safety_profile=profile,
    )

    assert result.validation.allowed is False
    assert result.validation.motion_allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert result.executed_step_id is None
    assert result.steps[0].status == "blocked"
    assert "motion approval is required" in " ".join(result.validation.reasons)


def test_home_boundary_blocks_without_motion_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    profile = _safety_profile(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path)
    _patch_live_status(monkeypatch, _live_status(session))
    qc_path, target_paths = _write_complete_registration_records(tmp_path, session)
    service = BridgeService(state_db_path=db_path, motion_enabled=True)

    result = service.execute_next(
        session.session_id,
        PlanFragment(
            session_id=session.session_id,
            steps=[PlanStep(step_id="home", operation="home")],
        ),
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )

    assert result.validation.allowed is False
    assert result.validation.motion_allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert result.executed_step_id is None
    assert result.steps[0].status == "blocked"
    assert "motion approval is required" in " ".join(result.validation.reasons)


def test_unpersisted_motion_approval_blocks_without_robot_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    plan = PlanFragment(
        session_id=session.session_id,
        steps=[PlanStep(step_id="home", operation="home")],
    )
    approval = build_motion_approval(
        plan,
        session=session,
        safety_profile=profile,
        step_id="home",
        approved_by="unit-test",
    )
    write_session(session, db_path)
    _write_active_lock(session, db_path, state=approval.required_lock_state)
    _patch_live_status(monkeypatch, _live_status(session))
    service = BridgeService(state_db_path=db_path, motion_enabled=True)

    def approved_validation(
        *_args: object,
        **_kwargs: object,
    ) -> PlanValidationResult:
        return PlanValidationResult(
            session_id=session.session_id,
            allowed=True,
            motion_allowed=True,
            motion_approval_id=approval.approval_id,
            steps=[
                StepValidationResult(
                    step_id="home",
                    operation="home",
                    allowed=True,
                    requires_motion=True,
                    gate_results=[
                        GateResult(gate_name=GateName.HOME_CLEARANCE, passed=True)
                    ],
                )
            ],
        )

    monkeypatch.setattr(service, "validate_plan", approved_validation)

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=approval,
    )

    assert result.validation.motion_allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert result.executed_step_id is None
    assert result.steps[0].status == "blocked"
    assert "motion approval record not found" in " ".join(result.validation.reasons)


def test_arm_motion_approval_persists_and_arms_session_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    service = BridgeService(state_db_path=db_path, motion_enabled=True)

    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: PlanValidationResult(
            session_id=session.session_id,
            allowed=False,
            motion_allowed=False,
            reasons=[MISSING_APPROVAL_REASON],
            steps=[
                StepValidationResult(
                    step_id="home",
                    operation="home",
                    allowed=True,
                    requires_motion=True,
                    gate_results=[GateResult(gate_name=GateName.HOME_CLEARANCE, passed=True)],
                )
            ],
        ),
    )

    result = service.arm_motion_approval(
        session.session_id,
        plan,
        approved_by="unit-test",
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )

    assert result.armed is True
    assert result.approval is not None
    persisted_session = read_session(session.session_id, db_path)
    persisted_lock = read_lock(session.robot_url, db_path)
    persisted_record = read_motion_approval_record(result.approval.approval_id, db_path)
    assert persisted_session is not None
    assert persisted_session.state == BridgeSessionState.MOTION_COMMISSIONING_ARMED
    assert persisted_session.motion_allowed is True
    assert persisted_session.updated_at == session.updated_at
    assert persisted_lock is not None
    assert persisted_lock.state == result.approval.required_lock_state
    assert persisted_record is not None
    assert persisted_record.state == "armed"
    assert persisted_record.approval == result.approval


def test_arm_motion_approval_rejects_ttl_over_cap_without_arming(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    service = BridgeService(state_db_path=db_path, motion_enabled=True)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: PlanValidationResult(
            session_id=session.session_id,
            allowed=False,
            motion_allowed=False,
            reasons=[MISSING_APPROVAL_REASON],
            steps=[
                StepValidationResult(
                    step_id="home",
                    operation="home",
                    allowed=True,
                    requires_motion=True,
                    gate_results=[GateResult(gate_name=GateName.HOME_CLEARANCE, passed=True)],
                )
            ],
        ),
    )

    result = service.arm_motion_approval(
        session.session_id,
        plan,
        approved_by="unit-test",
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
        expires_in_seconds=301,
    )

    persisted_session = read_session(session.session_id, db_path)
    persisted_lock = read_lock(session.robot_url, db_path)
    assert result.armed is False
    assert result.approval is None
    assert "expires_in_seconds must be <= 300" in " ".join(result.blockers)
    assert persisted_session is not None
    assert persisted_session.state == BridgeSessionState.READY_NO_MOTION
    assert persisted_session.motion_allowed is False
    assert persisted_lock is not None
    assert persisted_lock.state == "active_no_motion"


def test_arm_motion_approval_rejects_ttl_beyond_remaining_lease(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    now = datetime.now()
    session = _pose_scoped_session().model_copy(
        update={"lease_expires_at": now + timedelta(seconds=30)}
    )
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")

    result = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
        expires_in=timedelta(seconds=60),
        now=now,
    )

    persisted_session = read_session(session.session_id, db_path)
    persisted_lock = read_lock(session.robot_url, db_path)
    assert result.armed is False
    assert "remaining session lease" in " ".join(result.blockers)
    assert persisted_session is not None
    assert persisted_session.state == BridgeSessionState.READY_NO_MOTION
    assert persisted_lock is not None
    assert persisted_lock.state == "active_no_motion"


def test_expired_armed_approval_is_revoked_before_rearm(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    started_at = datetime.now()
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")

    first = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
        expires_in=timedelta(seconds=1),
        now=started_at,
    )
    second = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
        expires_in=timedelta(seconds=1),
        now=started_at + timedelta(seconds=2),
    )

    records = list_motion_approval_records(session.session_id, db_path)
    assert first.armed is True
    assert second.armed is True
    assert [record.state for record in records] == ["revoked", "armed"]
    assert records[0].approval.approval_id == first.approval.approval_id
    assert records[1].approval.approval_id == second.approval.approval_id


def test_lease_expired_armed_approval_cleanup_commits_when_rearm_blocks(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    started_at = datetime.now()
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    first = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
        expires_in=timedelta(seconds=60),
        now=started_at,
    )
    armed_session = read_session(session.session_id, db_path)
    assert first.armed is True
    assert armed_session is not None
    write_session(
        armed_session.model_copy(
            update={"lease_expires_at": started_at - timedelta(seconds=1)}
        ),
        db_path,
    )

    second = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
        expires_in=timedelta(seconds=1),
        now=started_at + timedelta(seconds=1),
    )

    records = list_motion_approval_records(session.session_id, db_path)
    persisted_session = read_session(session.session_id, db_path)
    assert second.armed is False
    assert "session lease is expired" in " ".join(second.blockers)
    assert [record.state for record in records] == ["revoked"]
    assert persisted_session is not None
    assert persisted_session.state == BridgeSessionState.READY_NO_MOTION
    assert persisted_session.motion_allowed is False


def test_motion_approval_id_collision_does_not_overwrite_consumed_record(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    now = datetime.now()
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    first = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
        now=now,
    )
    assert first.approval is not None
    assert first.session is not None
    preparation = _preparation_for_approval(first.approval, first.session, plan, profile)
    consumed = consume_motion_approval(
        approval=first.approval,
        plan=plan,
        safety_profile=profile,
        dispatch_preparation=preparation,
        path=db_path,
        now=now,
    )
    second = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
        now=now,
    )

    records = list_motion_approval_records(session.session_id, db_path)
    assert consumed.consumed is True
    assert second.armed is False
    assert "approval uniqueness" in " ".join(second.blockers)
    assert len(records) == 1
    assert records[0].state == "consumed"


def test_service_validate_plan_blocks_unpersisted_motion_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    approval = _home_approval(session, profile)
    write_session(session, db_path)
    service = BridgeService(state_db_path=db_path, motion_enabled=True)
    monkeypatch.setattr(
        service_module,
        "validate_plan_fragment",
        lambda *_args, **_kwargs: _approved_home_validation(
            session,
            approval.approval_id,
        ),
    )

    result = service.validate_plan(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=approval,
    )

    assert result.allowed is False
    assert result.motion_allowed is False
    assert "motion approval record not found" in " ".join(result.reasons)


def test_consume_motion_approval_blocks_missing_lock_without_exception(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    arm = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
    )
    assert arm.approval is not None
    with sqlite3.connect(db_path) as connection:
        connection.execute("DELETE FROM bridge_locks WHERE robot_url = ?", (session.robot_url,))

    result = consume_motion_approval(
        approval=arm.approval,
        plan=plan,
        safety_profile=profile,
        path=db_path,
    )

    record = read_motion_approval_record(arm.approval.approval_id, db_path)
    assert result.consumed is False
    assert "bridge lock is missing" in " ".join(result.blockers)
    assert record is not None
    assert record.state == "armed"


def test_dispatch_reservation_conflict_rolls_back_approval_consumption(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    arm = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
    )
    assert arm.approval is not None
    assert arm.session is not None
    preparation = _preparation_for_approval(arm.approval, arm.session, plan, profile)
    conflict = MotionDispatchReservation(
        reservation_id="reservation-conflict",
        approval_id=arm.approval.approval_id,
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id="home",
        operation="home",
        plan_digest_sha256=arm.approval.plan_digest_sha256,
        safety_profile_sha256=arm.approval.safety_profile_sha256,
    )
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO motion_dispatch_reservations (
                reservation_id, approval_id, session_id, state, created_at, payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                conflict.reservation_id,
                conflict.approval_id,
                conflict.session_id,
                conflict.state,
                conflict.created_at.isoformat(),
                conflict.model_dump_json(),
            ),
        )

    result = consume_motion_approval(
        approval=arm.approval,
        plan=plan,
        safety_profile=profile,
        dispatch_preparation=preparation,
        path=db_path,
    )

    record = read_motion_approval_record(arm.approval.approval_id, db_path)
    persisted_session = read_session(session.session_id, db_path)
    assert result.consumed is False
    assert "motion dispatch reservation" in " ".join(result.blockers)
    assert record is not None
    assert record.state == "armed"
    assert persisted_session is not None
    assert persisted_session.state == BridgeSessionState.MOTION_COMMISSIONING_ARMED
    assert persisted_session.motion_allowed is True


def test_dispatch_reservation_rejects_backend_state() -> None:
    with pytest.raises(ValidationError):
        MotionDispatchReservation(
            reservation_id="reservation-1",
            approval_id="approval-1",
            session_id="session-1",
            owner_id="agent-1",
            robot_url="http://ot2.local:31950",
            run_id="run-1",
            step_id="home",
            operation="home",
            plan_digest_sha256="0" * 64,
            safety_profile_sha256="1" * 64,
            robot_command_posted=True,
        )


def test_dispatch_reservation_row_payload_mismatch_fails_closed(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    arm = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
    )
    assert arm.approval is not None
    assert arm.session is not None
    preparation = _preparation_for_approval(arm.approval, arm.session, plan, profile)
    result = consume_motion_approval(
        approval=arm.approval,
        plan=plan,
        safety_profile=profile,
        dispatch_preparation=preparation,
        path=db_path,
    )
    assert result.dispatch_reservation is not None
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            UPDATE motion_dispatch_reservations
            SET session_id = ?
            WHERE reservation_id = ?
            """,
            ("other-session", result.dispatch_reservation.reservation_id),
        )

    with pytest.raises(ValueError, match="row/payload mismatch"):
        read_motion_dispatch_reservation(
            result.dispatch_reservation.reservation_id,
            db_path,
        )


def test_dispatch_preparation_builds_home_journal_candidate_from_readback(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    arm = arm_motion_commissioning(
        session_id=session.session_id,
        plan=plan,
        validation=_missing_motion_approval_validation(session),
        safety_profile=profile,
        approved_by="unit-test",
        path=db_path,
    )
    assert arm.approval is not None
    assert arm.session is not None
    preparation = _preparation_for_approval(arm.approval, arm.session, plan, profile)
    consumed = consume_motion_approval(
        approval=arm.approval,
        plan=plan,
        safety_profile=profile,
        dispatch_preparation=preparation,
        path=db_path,
    )
    assert consumed.dispatch_reservation is not None
    assert consumed.session is not None

    result = build_motion_dispatch_preparation_for_reservation(
        reservation=consumed.dispatch_reservation,
        session=consumed.session,
        plan=plan,
        safety_profile=profile,
        run_result=_run_readback(consumed.session),
        command_history_result=_command_history_readback(consumed.session),
    )

    assert result.prepared is True
    assert result.preparation is not None
    assert result.preparation.robot_command_posted is False
    assert result.preparation.command_body == {
        "data": {
            "commandType": "home",
            "key": result.preparation.command_journal_entry.command_key,
            "params": {},
        }
    }
    assert result.preparation.command_journal_entry.state == "prepared"
    assert result.preparation.command_journal_entry.command_id is None


def test_dispatch_preparation_builds_center_high_z_move_to_well_candidate() -> None:
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _high_z_plan(session)
    reservation = MotionDispatchReservation(
        reservation_id="reservation-high-z",
        approval_id="approval-high-z",
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id="high-z",
        operation="move_high_z",
        plan_digest_sha256=plan_fragment_digest(plan),
        safety_profile_sha256=profile.safety_profile_sha256,
    )

    result = build_motion_dispatch_preparation_for_reservation(
        reservation=reservation,
        session=session,
        plan=plan,
        safety_profile=profile,
        run_result=_run_readback(session),
        command_history_result=_command_history_readback(session),
    )

    assert result.prepared is True
    assert result.preparation is not None
    body = result.preparation.command_body["data"]
    assert body["commandType"] == "moveToWell"
    assert body["key"] == result.preparation.command_journal_entry.command_key
    assert body["params"] == {
        "pipetteId": session.pipette_id,
        "labwareId": session.loaded_labware_id,
        "wellName": "A1",
        "wellLocation": {
            "origin": "top",
            "offset": {"x": 0.0, "y": 0.0, "z": 15.0},
        },
        "minimumZHeight": profile.conservative_high_z_mm,
        "forceDirect": False,
        "speed": 20.0,
    }
    assert result.preparation.command_journal_entry.command_type == "moveToWell"


def test_dispatch_preparation_blocks_non_center_high_z_target() -> None:
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _high_z_plan(session, target_class="offset_x_1p0_high_z")
    reservation = MotionDispatchReservation(
        reservation_id="reservation-offset-high-z",
        approval_id="approval-offset-high-z",
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id="high-z",
        operation="move_high_z",
        plan_digest_sha256=plan_fragment_digest(plan),
        safety_profile_sha256=profile.safety_profile_sha256,
    )

    result = build_motion_dispatch_preparation_for_reservation(
        reservation=reservation,
        session=session,
        plan=plan,
        safety_profile=profile,
        run_result=_run_readback(session),
        command_history_result=_command_history_readback(session),
    )

    assert result.prepared is False
    assert "only implemented for center_high_z" in " ".join(result.blockers)


# --- OT-4: move_low_z dry-target translator -----------------------------------------------


def test_dispatch_preparation_blocks_low_z_descent_until_endpoint_grounded() -> None:
    # Headline: even a fully scope-valid center_low_z_dry step is REFUSED, because no per-well
    # dry-descent endpoint is grounded yet (minimumZHeight cannot bound a descent, and
    # dry_z_floor_mm is the collision-envelope top, not a descent floor). Mirrors OT-1's
    # promotion-blocked-behind-empty-allowlist headline.
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _low_z_plan(session, target_class="center_low_z_dry")
    reservation = MotionDispatchReservation(
        reservation_id="reservation-low-z",
        approval_id="approval-low-z",
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id="low-z",
        operation="move_low_z",
        plan_digest_sha256=plan_fragment_digest(plan),
        safety_profile_sha256=profile.safety_profile_sha256,
    )

    result = build_motion_dispatch_preparation_for_reservation(
        reservation=reservation,
        session=session,
        plan=plan,
        safety_profile=profile,
        run_result=_run_readback(session),
        command_history_result=_command_history_readback(session),
    )

    assert result.prepared is False
    assert "low_z_dry_descent_endpoint_not_grounded" in " ".join(result.blockers)


def test_move_low_z_emission_machinery_when_descent_grounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Machinery proof (mirrors OT-1's monkeypatched-allowlist test): with the grounding gate
    # forced open, the translator emits a structurally-correct moveToWell whose minimumZHeight
    # is the high-Z PARK (transit-arc clearance), NOT dry_z_floor_mm -- proving the corrected
    # semantics. The z-offset is the documented PROVISIONAL placeholder, not a verified depth.
    monkeypatch.setattr(
        "aevum_ot2.core.dispatch_preparation.LOW_Z_DRY_DESCENT_ENDPOINT_GROUNDED", True
    )
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    step = PlanStep(step_id="low-z", operation="move_low_z", target_class="center_low_z_dry")
    cmd, blockers = _move_low_z_command_body(
        reservation_id="r1", session=session, step=step, safety_profile=profile
    )
    assert blockers == []
    assert cmd is not None
    params = cmd["data"]["params"]
    assert cmd["data"]["commandType"] == "moveToWell"
    assert params["minimumZHeight"] == profile.conservative_high_z_mm  # transit arc, not floor
    assert params["minimumZHeight"] != profile.dry_z_floor_mm
    assert params["wellLocation"]["offset"]["z"] == FIRST_LOW_Z_DRY_TOP_OFFSET_MM
    assert params["speed"] == FIRST_LOW_Z_DRY_SPEED_MM_PER_S


def test_command_body_for_operation_formally_closes_set_offset() -> None:
    # OT-2: the translator refuses set_offset with an explicit closure reason (defense in
    # depth behind validation) -- there is no command to emit for a run-setup labware offset.
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    cmd, blockers = _command_body_for_operation(
        operation="set_offset",
        reservation_id="r1",
        session=session,
        step=PlanStep(step_id="offset", operation="set_offset"),
        safety_profile=profile,
    )
    assert cmd is None
    assert any("set_offset is a closed operation" in b for b in blockers)
    assert not any("not implemented for" in b for b in blockers)


def test_dispatch_preparation_blocks_non_center_low_z_dry_target() -> None:
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _low_z_plan(session, target_class="offset_x_1p5_low_z_dry")
    reservation = MotionDispatchReservation(
        reservation_id="reservation-offset-low-z",
        approval_id="approval-offset-low-z",
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id="low-z",
        operation="move_low_z",
        plan_digest_sha256=plan_fragment_digest(plan),
        safety_profile_sha256=profile.safety_profile_sha256,
    )

    result = build_motion_dispatch_preparation_for_reservation(
        reservation=reservation,
        session=session,
        plan=plan,
        safety_profile=profile,
        run_result=_run_readback(session),
        command_history_result=_command_history_readback(session),
    )

    assert result.prepared is False
    assert "only implemented for center_low_z_dry" in " ".join(result.blockers)


def test_move_low_z_translator_fails_closed_on_unsafe_or_missing_inputs() -> None:
    # Direct fail-closed checks on the translator's named blockers (the descent direction is
    # safety-critical, so each guard is pinned independently). The grounding gate fires on
    # every call here (it is closed by default), so each case asserts its own blocker is
    # present alongside it.
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    step = PlanStep(step_id="low-z", operation="move_low_z", target_class="center_low_z_dry")

    def body(*, sess=session, prof=profile, stp=step):
        return _move_low_z_command_body(
            reservation_id="r1", session=sess, step=stp, safety_profile=prof
        )

    # the descent-grounding gate is closed by default -> always refuses
    cmd, blockers = body()
    assert cmd is None and "low_z_dry_descent_endpoint_not_grounded" in blockers

    # missing safety profile
    cmd, blockers = body(prof=None)
    assert cmd is None and "move_low_z requires a safety profile" in blockers

    # high-Z park (the transit-arc clearance) not finite-positive
    cmd, blockers = body(prof=profile.model_copy(update={"conservative_high_z_mm": 0.0}))
    assert cmd is None
    assert "move_low_z safety-profile high-Z is not finite positive" in blockers

    # missing session pipette / labware
    cmd, blockers = body(sess=session.model_copy(update={"pipette_id": None}))
    assert cmd is None and "move_low_z requires session pipette ID" in blockers
    cmd, blockers = body(sess=session.model_copy(update={"loaded_labware_id": None}))
    assert cmd is None and "move_low_z requires loaded labware ID" in blockers

    # wrong target class
    cmd, blockers = body(
        stp=PlanStep(step_id="low-z", operation="move_low_z", target_class="center_high_z")
    )
    assert cmd is None and "only implemented for center_low_z_dry" in " ".join(blockers)


def test_dispatch_preparation_blocks_non_idle_run_readback() -> None:
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    reservation = MotionDispatchReservation(
        reservation_id="reservation-1",
        approval_id="approval-1",
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id="home",
        operation="home",
        plan_digest_sha256=plan_fragment_digest(_home_plan(session)),
        safety_profile_sha256=profile.safety_profile_sha256,
    )

    result = build_motion_dispatch_preparation_for_reservation(
        reservation=reservation,
        session=session,
        plan=_home_plan(session),
        safety_profile=profile,
        run_result=_run_readback(session, status="running"),
        command_history_result=_command_history_readback(session),
    )

    assert result.prepared is False
    assert "live maintenance run status is not idle" in " ".join(result.blockers)


def test_dispatch_preparation_recomputes_safety_profile_integrity() -> None:
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    tampered_profile = profile.model_copy(
        update={"max_registration_jog_mm": profile.max_registration_jog_mm + 1.0}
    )
    reservation = MotionDispatchReservation(
        reservation_id="reservation-1",
        approval_id="approval-1",
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id="home",
        operation="home",
        plan_digest_sha256=plan_fragment_digest(_home_plan(session)),
        safety_profile_sha256=profile.safety_profile_sha256,
    )

    result = build_motion_dispatch_preparation_for_reservation(
        reservation=reservation,
        session=session,
        plan=_home_plan(session),
        safety_profile=tampered_profile,
        run_result=_run_readback(session),
        command_history_result=_command_history_readback(session),
    )

    assert result.prepared is False
    assert "safety profile checksum does not match" in " ".join(result.blockers)


def test_dispatch_preparation_rejects_wrong_run_path_and_bad_offset() -> None:
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    reservation = MotionDispatchReservation(
        reservation_id="reservation-1",
        approval_id="approval-1",
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id="home",
        operation="home",
        plan_digest_sha256=plan_fragment_digest(_home_plan(session)),
        safety_profile_sha256=profile.safety_profile_sha256,
    )
    run_result = _run_readback(
        session,
        offset_id="offset-1",
        offset_vector={"x": float("nan"), "y": 0.0, "z": 0.0},
    )
    run_result.path = f"/runs/{session.maintenance_run_id}"

    result = build_motion_dispatch_preparation_for_reservation(
        reservation=reservation,
        session=session,
        plan=_home_plan(session),
        safety_profile=profile,
        run_result=run_result,
        command_history_result=_command_history_readback(session),
    )

    assert result.prepared is False
    blockers = " ".join(result.blockers)
    assert "live maintenance run path does not match session" in blockers
    assert "offset vector is incomplete" in blockers


def test_dispatch_preparation_requires_session_last_command_to_be_latest() -> None:
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    reservation = MotionDispatchReservation(
        reservation_id="reservation-1",
        approval_id="approval-1",
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id="home",
        operation="home",
        plan_digest_sha256=plan_fragment_digest(_home_plan(session)),
        safety_profile_sha256=profile.safety_profile_sha256,
    )

    result = build_motion_dispatch_preparation_for_reservation(
        reservation=reservation,
        session=session,
        plan=_home_plan(session),
        safety_profile=profile,
        run_result=_run_readback(session),
        command_history_result=_command_history_readback(
            session,
            {
                "id": session.last_command_id,
                "key": session.last_command_key,
                "commandType": "loadLabware",
                "status": session.last_command_status,
                "params": {},
                "createdAt": "2026-05-06T00:00:00",
            },
            {
                "id": "later-command",
                "key": "later-key",
                "commandType": "comment",
                "status": "succeeded",
                "params": {"message": "drift"},
                "createdAt": "2026-05-06T00:01:00",
            },
        ),
    )

    assert result.prepared is False
    assert "last command does not match session" in " ".join(result.blockers)


def test_dispatch_preparation_rejects_nonfinite_jog_bound() -> None:
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session).model_copy(
        update={"max_registration_jog_mm": float("inf")}
    )
    reservation = MotionDispatchReservation(
        reservation_id="reservation-1",
        approval_id="approval-1",
        session_id=session.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id="home",
        operation="home",
        plan_digest_sha256=plan_fragment_digest(_home_plan(session)),
        safety_profile_sha256=profile.safety_profile_sha256,
    )

    result = build_motion_dispatch_preparation_for_reservation(
        reservation=reservation,
        session=session,
        plan=_home_plan(session),
        safety_profile=profile,
        run_result=_run_readback(
            session,
            offset_id="offset-1",
            offset_vector={"x": 0.1, "y": 0.0, "z": 0.0},
        ),
        command_history_result=_command_history_readback(session),
    )

    assert result.prepared is False
    assert "jog bound is not finite positive" in " ".join(result.blockers)


def test_execute_next_preparation_failure_does_not_consume_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    service = BridgeService(state_db_path=db_path, motion_enabled=True)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: _missing_motion_approval_validation(session),
    )
    arm = service.arm_motion_approval(
        session.session_id,
        plan,
        approved_by="unit-test",
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )
    assert arm.approval is not None
    armed_session = read_session(session.session_id, db_path)
    assert armed_session is not None
    _patch_live_status(monkeypatch, _live_status(armed_session))
    _patch_dispatch_readbacks(
        monkeypatch,
        service,
        armed_session,
        run_result=_run_readback(armed_session, status="running"),
    )
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: _approved_home_validation(
            armed_session,
            arm.approval.approval_id,
        ),
    )

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=arm.approval,
    )

    record = read_motion_approval_record(arm.approval.approval_id, db_path)
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert result.steps[0].status == "blocked"
    assert "motion_dispatch_preparation" in " ".join(result.validation.reasons)
    assert record is not None
    assert record.state == "armed"
    assert read_motion_dispatch_reservation_for_approval(
        arm.approval.approval_id,
        db_path,
    ) is None
    assert list_command_journal_entries(session.session_id, db_path) == []


def test_execute_next_consumes_motion_approval_once_without_robot_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    service = BridgeService(state_db_path=db_path, motion_enabled=True)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: PlanValidationResult(
            session_id=session.session_id,
            allowed=False,
            motion_allowed=False,
            reasons=[MISSING_APPROVAL_REASON],
            steps=[
                StepValidationResult(
                    step_id="home",
                    operation="home",
                    allowed=True,
                    requires_motion=True,
                    gate_results=[GateResult(gate_name=GateName.HOME_CLEARANCE, passed=True)],
                )
            ],
        ),
    )
    arm = service.arm_motion_approval(
        session.session_id,
        plan,
        approved_by="unit-test",
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )
    assert arm.approval is not None
    armed_session = read_session(session.session_id, db_path)
    assert armed_session is not None
    _patch_live_status(monkeypatch, _live_status(armed_session))
    _patch_dispatch_readbacks(monkeypatch, service, armed_session)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: _approved_home_validation(
            armed_session,
            arm.approval.approval_id,
        ),
    )

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=arm.approval,
    )

    assert result.executed is False
    assert result.motion_commands_sent is False
    assert result.executed_step_id is None
    assert result.validation.allowed is False
    assert result.validation.motion_allowed is False
    assert "consumed by pre-dispatch reservation" in " ".join(
        result.validation.reasons
    )
    assert result.steps[0].status == "not_implemented"
    assert "dispatch_reservation" in result.steps[0].payload
    assert "command_journal_entry" in result.steps[0].payload
    assert "dispatch_preparation" in result.steps[0].payload
    assert "command_body" not in result.steps[0].payload["dispatch_preparation"]
    consumed_record = read_motion_approval_record(arm.approval.approval_id, db_path)
    assert consumed_record is not None
    assert consumed_record.state == "consumed"
    reservation = read_motion_dispatch_reservation_for_approval(
        arm.approval.approval_id,
        db_path,
    )
    assert reservation is not None
    assert reservation.state == "reserved_pre_dispatch"
    assert reservation.robot_command_posted is False
    assert reservation.step_id == "home"
    assert result.steps[0].payload["dispatch_reservation"]["reservation_id"] == (
        reservation.reservation_id
    )
    journal_id = result.steps[0].payload["command_journal_entry"]["journal_id"]
    assert reservation.command_journal_id == journal_id
    journal_entry = read_command_journal_entry(journal_id, db_path)
    assert journal_entry is not None
    assert journal_entry.state == "prepared"
    assert journal_entry.command_type == "home"
    assert journal_entry.posted_at is None
    assert journal_entry.command_id is None
    disarmed_session = read_session(session.session_id, db_path)
    disarmed_lock = read_lock(session.robot_url, db_path)
    assert disarmed_session is not None
    assert disarmed_session.state == BridgeSessionState.READY_NO_MOTION
    assert disarmed_session.motion_allowed is False
    assert disarmed_session.updated_at == session.updated_at
    assert disarmed_lock is not None
    assert disarmed_lock.state == "active_no_motion"

    replay = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=arm.approval,
    )
    assert replay.executed is False
    assert replay.motion_commands_sent is False
    assert "session state" in " ".join(replay.validation.reasons)


def test_execute_next_with_motion_backend_posts_prepared_home_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    service = BridgeService(
        state_db_path=db_path,
        motion_enabled=True,
        motion_backend_enabled=True,
    )
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: PlanValidationResult(
            session_id=session.session_id,
            allowed=False,
            motion_allowed=False,
            reasons=[MISSING_APPROVAL_REASON],
            steps=[
                StepValidationResult(
                    step_id="home",
                    operation="home",
                    allowed=True,
                    requires_motion=True,
                    gate_results=[GateResult(gate_name=GateName.HOME_CLEARANCE, passed=True)],
                )
            ],
        ),
    )
    arm = service.arm_motion_approval(
        session.session_id,
        plan,
        approved_by="unit-test",
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )
    assert arm.approval is not None
    armed_session = read_session(session.session_id, db_path)
    assert armed_session is not None
    run_path = f"/maintenance_runs/{armed_session.maintenance_run_id}"
    commands = _command_history_readback(armed_session).data["data"]  # type: ignore[index]
    assert isinstance(commands, list)
    posts: list[tuple[str, dict[str, object]]] = []

    class FakeClient:
        def __init__(self, robot_url: str, **_kwargs: object) -> None:
            self.robot_url = robot_url

        def status(self) -> RobotStatus:
            return _live_status(armed_session)

        def get_json(self, path: str) -> EndpointResult:
            if path == run_path:
                return _run_readback(armed_session)
            if path == f"{run_path}/commands?pageLength=1000":
                return EndpointResult(
                    path=path,
                    ok=True,
                    data={"data": list(commands), "meta": {"totalLength": len(commands)}},
                )
            return EndpointResult(path=path, ok=False, error="unexpected path")

        def post_json(
            self,
            path: str,
            body: dict[str, object] | list[object] | None = None,
        ) -> EndpointResult:
            assert isinstance(body, dict)
            data = body["data"]
            assert isinstance(data, dict)
            command = {
                "id": "command-home-1",
                "key": data["key"],
                "commandType": data["commandType"],
                "status": "succeeded",
                "params": data.get("params", {}),
                "createdAt": "2026-05-06T00:00:00",
            }
            posts.append((path, body))
            commands.append(command)
            return EndpointResult(
                path=path,
                ok=True,
                status_code=201,
                data={"data": command},
            )

    monkeypatch.setattr(service_module, "Ot2Client", FakeClient)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: _approved_home_validation(
            armed_session,
            arm.approval.approval_id,
        ),
    )

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=arm.approval,
    )

    assert result.executed is True
    assert result.motion_commands_sent is True
    assert result.executed_step_id == "home"
    assert len(posts) == 1
    assert posts[0][0] == f"{run_path}/commands?waitUntilComplete=true&timeout=60000"
    assert posts[0][1]["data"]["commandType"] == "home"  # type: ignore[index]
    backend_payload = result.steps[0].payload["motion_backend"]
    assert backend_payload["dispatched"] is True
    assert backend_payload["motion_commands_sent"] is True
    assert "command_body" not in backend_payload["preparation"]

    latest = read_session(session.session_id, db_path)
    latest_lock = read_lock(session.robot_url, db_path)
    assert latest is not None
    assert latest.state == BridgeSessionState.READY_NO_MOTION
    assert latest.motion_allowed is False
    assert latest.last_command_id == "command-home-1"
    assert latest.last_command_key == posts[0][1]["data"]["key"]  # type: ignore[index]
    assert latest.last_command_type == "home"
    assert latest.last_command_status == "succeeded"
    assert latest_lock is not None
    assert latest_lock.state == "active_no_motion"
    assert latest_lock.last_command_id == "command-home-1"

    reservation = read_motion_dispatch_reservation_for_approval(
        arm.approval.approval_id,
        db_path,
    )
    assert reservation is not None
    journal_entry = read_command_journal_entry(reservation.command_journal_id, db_path)
    assert journal_entry is not None
    assert journal_entry.state == "completed"
    assert journal_entry.command_id == "command-home-1"


def test_motion_backend_fresh_readback_drift_blocks_before_post(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session()
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    service = BridgeService(
        state_db_path=db_path,
        motion_enabled=True,
        motion_backend_enabled=True,
    )
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: PlanValidationResult(
            session_id=session.session_id,
            allowed=False,
            motion_allowed=False,
            reasons=[MISSING_APPROVAL_REASON],
            steps=[
                StepValidationResult(
                    step_id="home",
                    operation="home",
                    allowed=True,
                    requires_motion=True,
                    gate_results=[GateResult(gate_name=GateName.HOME_CLEARANCE, passed=True)],
                )
            ],
        ),
    )
    arm = service.arm_motion_approval(
        session.session_id,
        plan,
        approved_by="unit-test",
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )
    assert arm.approval is not None
    armed_session = read_session(session.session_id, db_path)
    assert armed_session is not None
    run_path = f"/maintenance_runs/{armed_session.maintenance_run_id}"
    initial_commands = _command_history_readback(armed_session).data["data"]  # type: ignore[index]
    assert isinstance(initial_commands, list)
    drifted_commands = [
        *initial_commands,
        {
            "id": "other-command",
            "key": "other-key",
            "commandType": "home",
            "status": "succeeded",
            "params": {},
            "createdAt": "2026-05-06T00:00:01",
        },
    ]
    history_gets = 0
    posts: list[tuple[str, dict[str, object]]] = []

    class FakeClient:
        def __init__(self, robot_url: str, **_kwargs: object) -> None:
            self.robot_url = robot_url

        def status(self) -> RobotStatus:
            return _live_status(armed_session)

        def get_json(self, path: str) -> EndpointResult:
            nonlocal history_gets
            if path == run_path:
                return _run_readback(armed_session)
            if path == f"{run_path}/commands?pageLength=1000":
                history_gets += 1
                commands = initial_commands if history_gets == 1 else drifted_commands
                return EndpointResult(
                    path=path,
                    ok=True,
                    data={"data": list(commands), "meta": {"totalLength": len(commands)}},
                )
            return EndpointResult(path=path, ok=False, error="unexpected path")

        def post_json(
            self,
            path: str,
            body: dict[str, object] | list[object] | None = None,
        ) -> EndpointResult:
            assert isinstance(body, dict)
            posts.append((path, body))
            return EndpointResult(path=path, ok=True, data={"data": {}})

    monkeypatch.setattr(service_module, "Ot2Client", FakeClient)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: _approved_home_validation(
            armed_session,
            arm.approval.approval_id,
        ),
    )

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=arm.approval,
    )

    assert result.executed is False
    assert result.motion_commands_sent is False
    assert posts == []
    assert "fresh dispatch preparation" in " ".join(
        result.steps[0].payload["motion_backend_blockers"]
    )
    assert "last command" in " ".join(result.steps[0].payload["motion_backend_blockers"])
    latest = read_session(session.session_id, db_path)
    latest_lock = read_lock(session.robot_url, db_path)
    assert latest is not None
    assert latest.state == BridgeSessionState.RECOVERY_REQUIRED
    assert latest.motion_allowed is False
    assert latest_lock is not None
    assert latest_lock.state == "recovery_required"


@pytest.mark.parametrize(
    ("status_kwargs", "expected"),
    [
        ({"pipette_name": "p20_single_gen2"}, "live pipette name does not match session"),
        ({"api_version": "9.1.0"}, "live robot server version does not match session"),
    ],
)
def test_execute_time_live_robot_drift_blocks_motion_without_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status_kwargs: dict[str, str],
    expected: str,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    approval = _home_approval(session, profile)
    write_session(session, db_path)
    _write_active_lock(session, db_path)
    _patch_live_status(monkeypatch, _live_status(session, **status_kwargs))
    service = BridgeService(state_db_path=db_path, motion_enabled=True)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: _approved_home_validation(
            session,
            approval.approval_id,
        ),
    )

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=approval,
    )

    assert result.validation.allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert expected in " ".join(result.validation.reasons)


def test_execute_time_stale_lock_blocks_motion_without_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    approval = _home_approval(session, profile)
    write_session(session, db_path)
    _write_active_lock(session, db_path, expires_in=timedelta(minutes=-1))
    _patch_live_status(monkeypatch, _live_status(session))
    service = BridgeService(state_db_path=db_path, motion_enabled=True)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: _approved_home_validation(
            session,
            approval.approval_id,
        ),
    )

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=approval,
    )

    assert result.validation.allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert "bridge lock lease is expired" in " ".join(result.validation.reasons)


def test_execute_time_expired_session_lease_blocks_motion_without_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session().model_copy(
        update={"lease_expires_at": datetime.now() - timedelta(minutes=1)}
    )
    profile = _safety_profile(session)
    write_session(session, db_path)
    _write_active_lock(session, db_path)
    _patch_live_status(monkeypatch, _live_status(session))
    qc_path, target_paths = _write_complete_registration_records(tmp_path, session)
    service = BridgeService(state_db_path=db_path, motion_enabled=True)

    result = service.execute_next(
        session.session_id,
        PlanFragment(
            session_id=session.session_id,
            steps=[PlanStep(step_id="home", operation="home")],
        ),
        fixture_qc_record=qc_path,
        target_class_records=target_paths,
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )

    assert result.validation.allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert "session lease is expired" in " ".join(result.validation.reasons)


def test_execute_time_incomplete_session_pipette_identity_blocks_motion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    ).model_copy(update={"pipette_id": ""})
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    approval = _home_approval(session, profile)
    write_session(session, db_path)
    _write_active_lock(session, db_path)
    _patch_live_status(monkeypatch, _live_status(session))
    service = BridgeService(state_db_path=db_path, motion_enabled=True)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: _approved_home_validation(
            session,
            approval.approval_id,
        ),
    )

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=approval,
    )

    assert result.validation.allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert "session pipette ID is missing" in " ".join(result.validation.reasons)


def test_execute_time_no_motion_lock_state_blocks_motion_without_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    approval = _home_approval(session, profile)
    write_session(session, db_path)
    _write_active_lock(session, db_path, state="active_no_motion")
    _patch_live_status(monkeypatch, _live_status(session))
    service = BridgeService(state_db_path=db_path, motion_enabled=True)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: _approved_home_validation(
            session,
            approval.approval_id,
        ),
    )

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=approval,
    )

    assert result.validation.allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert "bridge lock state active_no_motion" in " ".join(result.validation.reasons)


def test_execute_time_reloaded_non_ready_session_blocks_motion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    approval = _home_approval(session, profile)
    write_session(session, db_path)
    _write_active_lock(session, db_path)
    _patch_live_status(monkeypatch, _live_status(session))
    service = BridgeService(state_db_path=db_path, motion_enabled=True)

    def mutating_validate_plan(*args: object, **kwargs: object) -> PlanValidationResult:
        validation = _approved_home_validation(session, approval.approval_id)
        write_session(
            session.model_copy(update={"state": BridgeSessionState.CLOSED}),
            db_path,
        )
        return validation

    monkeypatch.setattr(service, "validate_plan", mutating_validate_plan)

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=approval,
    )

    assert result.validation.allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert "session state is closed" in " ".join(result.validation.reasons)


def test_execute_time_lock_owner_mismatch_blocks_motion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    plan = _home_plan(session)
    approval = _home_approval(session, profile)
    write_session(session, db_path)
    _write_active_lock(session.model_copy(update={"owner_id": "other-agent"}), db_path)
    _patch_live_status(monkeypatch, _live_status(session))
    service = BridgeService(state_db_path=db_path, motion_enabled=True)
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *_args, **_kwargs: _approved_home_validation(
            session,
            approval.approval_id,
        ),
    )

    result = service.execute_next(
        session.session_id,
        plan,
        safety_profile=profile,
        motion_approval=approval,
    )

    assert result.validation.allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert "bridge lock owner does not match session" in " ".join(
        result.validation.reasons
    )


def test_execute_time_missing_gate_result_blocks_motion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    _write_active_lock(session, db_path)
    _patch_live_status(monkeypatch, _live_status(session))
    service = BridgeService(state_db_path=db_path, motion_enabled=True)

    def validation_without_gates(*_args: object, **_kwargs: object) -> PlanValidationResult:
        return PlanValidationResult(
            session_id=session.session_id,
            allowed=True,
            motion_allowed=True,
            steps=[
                StepValidationResult(
                    step_id="home",
                    operation="home",
                    allowed=True,
                    requires_motion=True,
                )
            ],
        )

    monkeypatch.setattr(service, "validate_plan", validation_without_gates)

    result = service.execute_next(
        session.session_id,
        PlanFragment(
            session_id=session.session_id,
            steps=[PlanStep(step_id="home", operation="home")],
        ),
    )

    assert result.validation.allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert "motion step has no gate result" in " ".join(result.validation.reasons)


def test_execute_time_missing_required_gate_shape_blocks_motion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    _write_active_lock(session, db_path)
    _patch_live_status(monkeypatch, _live_status(session))
    service = BridgeService(state_db_path=db_path, motion_enabled=True)

    def validation_without_target_authority(
        *_args: object,
        **_kwargs: object,
    ) -> PlanValidationResult:
        return PlanValidationResult(
            session_id=session.session_id,
            allowed=True,
            motion_allowed=True,
            steps=[
                StepValidationResult(
                    step_id="high-z",
                    operation="move_high_z",
                    allowed=True,
                    requires_motion=True,
                    gate_results=[
                        GateResult(gate_name=GateName.FIRST_HIGH_Z, passed=True)
                    ],
                )
            ],
        )

    monkeypatch.setattr(service, "validate_plan", validation_without_target_authority)

    result = service.execute_next(
        session.session_id,
        PlanFragment(
            session_id=session.session_id,
            steps=[
                PlanStep(
                    step_id="high-z",
                    operation="move_high_z",
                    target_class="center_high_z",
                )
            ],
        ),
    )

    assert result.validation.allowed is False
    assert result.executed is False
    assert result.motion_commands_sent is False
    assert "motion step missing required gate result: target_class_authority" in " ".join(
        result.validation.reasons
    )


def test_unknown_plan_operation_fails_closed_at_model_boundary() -> None:
    with pytest.raises(ValidationError):
        PlanStep(step_id="raw-http", operation="post_robot_server_command")


def test_unknown_session_state_fails_closed_at_model_boundary() -> None:
    data = _session().model_dump(mode="json")
    data["state"] = "ready_nomotion"

    with pytest.raises(ValidationError):
        BridgeSession.model_validate(data)


def test_unknown_session_kind_fails_closed_at_model_boundary() -> None:
    data = _session().model_dump(mode="json")
    data["kind"] = "ad_hoc_motion"

    with pytest.raises(ValidationError):
        BridgeSession.model_validate(data)


def test_low_z_without_promoted_offset_registry_record_is_blocked() -> None:
    low_z = _target_record("offset_x_1p5_low_z_dry")
    high_z = _verified_target_record(_session(), "offset_x_1p5_high_z")

    result = validate_plan_fragment(
        _low_z_plan(_session()),
        _session(),
        readiness=_readiness(),
        target_records=[low_z, high_z],
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert result.motion_allowed is False
    assert "offset" in " ".join(result.reasons).lower()


def test_home_requires_explicit_home_clearance_gate() -> None:
    result = validate_plan_fragment(
        PlanFragment(
            session_id="session-1",
            steps=[PlanStep(step_id="home", operation="home")],
        ),
        _session(),
        readiness=_readiness(),
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert result.motion_allowed is False
    assert "home" in " ".join(result.reasons).lower()


def test_duplicate_step_ids_are_rejected_before_execution() -> None:
    result = validate_plan_fragment(
        PlanFragment(
            session_id="session-1",
            steps=[
                PlanStep(step_id="inspect", operation="inspect_context"),
                PlanStep(step_id="inspect", operation="capture_observation"),
            ],
        ),
        _session(),
    )

    assert result.allowed is False
    assert "duplicate" in " ".join(result.reasons).lower()


def test_registration_record_scaffold_remains_complete() -> None:
    session = _session()

    records = scaffold_target_class_records(
        session,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
    )

    assert {record.target_class for record in records} == set(target_class_names())
    assert all(record.result == TargetClassResult.BLOCKED for record in records)
    assert all(record.offset_registry_record == "not-yet-registered" for record in records)
