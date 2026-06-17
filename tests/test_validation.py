from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.models import (
    BridgeSession,
    EvidenceClaim,
    EvidenceHandle,
    EvidenceQuality,
    EvidenceSourceKind,
    OffsetAuthorityState,
    OffsetRecord,
    OffsetRegistry,
)
from aevum_ot2.core.motion_approval import (
    MotionApproval,
    build_motion_approval,
    expected_motion_approval_id,
    motion_approval_blockers,
    plan_fragment_digest,
)
from aevum_ot2.core.plans import PlanFragment, PlanStep
from aevum_ot2.core.readiness import ReadinessResult
from aevum_ot2.core.records import (
    TARGET_CLASS_EVIDENCE_METHOD,
    TargetClassResult,
    TargetClassVerificationRecord,
    scaffold_fixture_qc_record,
    target_class_authority,
    target_class_verified_claim_id,
    target_class_verified_claim_type,
)
from aevum_ot2.core.recovery import NoMotionRecoveryDisposition
from aevum_ot2.core.registry import offset_record_id
from aevum_ot2.core.safety import (
    FixtureSafetyProfile,
    _safety_profile_digest,
    build_fixture_safety_profile,
)
from aevum_ot2.core.validation import validate_plan_fragment

TARGET_EVIDENCE_PATH = Path(__file__).parent / "fixtures" / "target_evidence.json"


def _session(state: str = "ready_no_motion") -> BridgeSession:
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
        state=state,
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


def _readiness(ready: bool = True) -> ReadinessResult:
    return ReadinessResult(
        session_id="session-1",
        registration_ready=ready,
        reasons=[] if ready else ["missing target-class records"],
    )


def _plan(*steps: PlanStep, session_id: str = "session-1") -> PlanFragment:
    return PlanFragment(session_id=session_id, steps=list(steps))


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
    record = scaffold_fixture_qc_record(
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
    result = build_fixture_safety_profile(session.fixture_identity, fixture_qc_record=record)
    assert result.profile is not None
    return result.profile


def _pose_scoped_session(
    *,
    state: str = "ready_no_motion",
    motion_allowed: bool = False,
) -> BridgeSession:
    return _session(state).model_copy(
        update={
            "fixture_orientation": "rot180",
            "fixture_pose_digest_sha256": "a" * 64,
            "fixture_pose_path": "data/measurements/sessions/session-1/fixture_pose.json",
            "motion_allowed": motion_allowed,
        }
    )


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


def test_prepare_registration_plan_requires_readiness() -> None:
    result = validate_plan_fragment(
        _plan(PlanStep(step_id="prep", operation="prepare_registration_plan")),
        _session(),
        readiness=_readiness(),
    )

    assert result.allowed is True
    assert result.motion_allowed is False
    assert result.steps[0].allowed is True


def test_motion_step_is_blocked_without_daemon() -> None:
    result = validate_plan_fragment(
        _plan(PlanStep(step_id="home", operation="home")),
        _session(),
        readiness=_readiness(),
    )

    assert result.allowed is False
    assert result.motion_allowed is False
    assert "motion-capable bridge daemon" in " ".join(result.reasons)


def test_home_step_can_validate_with_home_clearance_when_daemon_enabled() -> None:
    session = _session()
    profile = _safety_profile(session)

    result = validate_plan_fragment(
        _plan(PlanStep(step_id="home", operation="home")),
        session,
        readiness=_readiness(),
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert result.motion_allowed is False
    assert result.steps[0].allowed is True
    assert "motion approval is required" in " ".join(result.reasons)


def test_motion_approval_is_required_for_motion_allowed() -> None:
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    plan = _plan(PlanStep(step_id="home", operation="home"))
    approval = build_motion_approval(
        plan,
        session=session,
        safety_profile=profile,
        step_id="home",
        approved_by="unit-test",
    )

    without_approval = validate_plan_fragment(
        plan,
        session,
        readiness=_readiness(),
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
        daemon_motion_enabled=True,
    )

    assert without_approval.allowed is False
    assert without_approval.motion_allowed is False
    assert "fixture_pose" in " ".join(without_approval.reasons)
    assert (
        motion_approval_blockers(
            approval,
            plan=plan,
            session=session,
            safety_profile=profile,
        )
        == []
    )


def test_motion_approval_rejects_plan_drift() -> None:
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    approved_plan = _plan(PlanStep(step_id="home", operation="home"))
    drifted_plan = _plan(
        PlanStep(
            step_id="high-z",
            operation="move_high_z",
            target_class="center_high_z",
        )
    )
    approval = build_motion_approval(
        approved_plan,
        session=session,
        safety_profile=profile,
        step_id="home",
        approved_by="unit-test",
    )

    result = validate_plan_fragment(
        drifted_plan,
        session,
        readiness=_readiness(),
        target_records=[_verified_target_record(session, "center_high_z")],
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
        daemon_motion_enabled=True,
        motion_approval=approval,
    )

    assert result.allowed is False
    assert result.motion_allowed is False
    assert "plan digest does not match" in " ".join(result.reasons)


def test_motion_approval_rejects_forged_id() -> None:
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    plan = _plan(PlanStep(step_id="home", operation="home"))
    approval = build_motion_approval(
        plan,
        session=session,
        safety_profile=profile,
        step_id="home",
        approved_by="unit-test",
    )
    forged = approval.model_copy(update={"approval_id": "motion_approval:forged"})
    restamped = approval.model_copy(update={"robot_serial": "OT2OTHER0001"})

    assert approval.approval_id == expected_motion_approval_id(approval)
    assert ":scope-" in approval.approval_id
    assert "motion approval ID does not match scoped fields" in motion_approval_blockers(
        forged,
        plan=plan,
        session=session,
        safety_profile=profile,
    )
    assert "motion approval ID does not match scoped fields" in motion_approval_blockers(
        restamped,
        plan=plan,
        session=session,
        safety_profile=profile,
    )


def test_motion_approval_rejects_long_ttl() -> None:
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)

    with pytest.raises(ValidationError):
        build_motion_approval(
            _plan(PlanStep(step_id="home", operation="home")),
            session=session,
            safety_profile=profile,
            step_id="home",
            approved_by="unit-test",
            expires_in=timedelta(minutes=10),
        )


def test_motion_approval_plan_digest_ignores_notes() -> None:
    assert plan_fragment_digest(
        _plan(PlanStep(step_id="home", operation="home", notes="operator note"))
    ) == plan_fragment_digest(_plan(PlanStep(step_id="home", operation="home")))


def test_motion_approval_rejects_mutable_required_state() -> None:
    session = _pose_scoped_session(
        state="motion_commissioning_armed",
        motion_allowed=True,
    )
    profile = _pose_scoped_profile(session)
    approval = build_motion_approval(
        _plan(PlanStep(step_id="home", operation="home")),
        session=session,
        safety_profile=profile,
        step_id="home",
        approved_by="unit-test",
    )
    data = approval.model_dump(mode="json")
    data["required_lock_state"] = "active_motion"

    with pytest.raises(ValidationError):
        MotionApproval.model_validate(data)


def test_home_step_blocks_unresolved_recovery_even_with_safety_profile() -> None:
    session = _session()
    profile = _safety_profile(session)

    result = validate_plan_fragment(
        _plan(PlanStep(step_id="home", operation="home")),
        session,
        readiness=_readiness(),
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.UNRESOLVED_RECOVERY,
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert "unresolved_recovery" in " ".join(result.reasons)


def test_move_high_z_requires_home_clearance_not_registration_alone() -> None:
    center_high_z = _target_record("center_high_z")

    result = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="high-z",
                operation="move_high_z",
                target_class="center_high_z",
            )
        ),
        _session(),
        readiness=_readiness(),
        target_records=[center_high_z],
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert [gate.gate_name for gate in result.steps[0].gate_results] == [
        "target_class_authority",
        "first_high_z",
    ]
    assert result.steps[0].gate_results[-1].claim_ids == []
    assert "home_clearance_gate_passed" in " ".join(result.reasons)


def test_move_high_z_blocks_blocked_first_pass_target_even_after_home_clearance() -> None:
    session = _session()
    profile = _safety_profile(session)
    center_high_z = _target_record("center_high_z")

    result = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="high-z",
                operation="move_high_z",
                target_class="center_high_z",
            )
        ),
        session,
        readiness=_readiness(),
        target_records=[center_high_z],
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
        daemon_motion_enabled=True,
    )

    reason_text = " ".join(result.reasons)
    assert result.allowed is False
    assert result.motion_allowed is False
    assert "passed_target:center_high_z" in reason_text
    assert "target_class_verified:center_high_z" in reason_text


def test_move_high_z_can_validate_for_first_pass_target_after_home_clearance() -> None:
    session = _session()
    profile = _safety_profile(session)
    center_high_z = _verified_target_record(session, "center_high_z")

    result = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="high-z",
                operation="move_high_z",
                target_class="center_high_z",
            )
        ),
        session,
        readiness=_readiness(),
        target_records=[center_high_z],
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert result.motion_allowed is False
    assert result.steps[0].allowed is True
    assert "motion approval is required" in " ".join(result.reasons)
    assert [gate.gate_name for gate in result.steps[0].gate_results] == [
        "target_class_authority",
        "first_high_z",
    ]


def test_low_z_step_requires_matching_high_z_evidence_even_with_daemon_flag() -> None:
    low_z = _target_record("offset_x_1p5_low_z_dry")

    result = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="low-z",
                operation="move_low_z",
                target_class="offset_x_1p5_low_z_dry",
            )
        ),
        _session(),
        readiness=_readiness(),
        target_records=[low_z],
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert "offset_x_1p5_high_z" in " ".join(result.reasons)


def test_low_z_step_can_validate_after_matching_high_z_evidence_when_daemon_enabled() -> None:
    session = _session()
    profile = _safety_profile(session)
    offset = _promoted_offset(session, profile, "offset_x_1p5_low_z_dry")
    low_z = _target_record(
        "offset_x_1p5_low_z_dry",
        offset_registry_record=offset_record_id(offset),
    )
    high_z = _verified_target_record(session, "offset_x_1p5_high_z")

    result = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="low-z",
                operation="move_low_z",
                target_class="offset_x_1p5_low_z_dry",
            )
        ),
        session,
        readiness=_readiness(),
        target_records=[low_z, high_z],
        offset_registry=OffsetRegistry(records=[offset]),
        safety_profile=profile,
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert result.steps[0].allowed is True
    assert "motion approval is required" in " ".join(result.reasons)
    assert result.motion_allowed is False
    assert [gate.gate_name for gate in result.steps[0].gate_results] == [
        "offset_authority",
        "low_z_dry",
    ]


def test_target_authority_rejects_legacy_fields_even_with_claim() -> None:
    session = _session()
    record = _verified_target_record(session, "offset_x_1p5_high_z").model_copy(
        update={"legacy_camera_images": ["legacy-camera-image"]}
    )

    authority = target_class_authority(record, session=session)

    assert authority.passed is False
    assert "legacy target evidence fields cannot authorize target class" in authority.blockers


def test_target_authority_rejects_unapproved_claim_method() -> None:
    session = _session()
    record = _verified_target_record(session, "offset_x_1p5_high_z")
    bad_claim = record.claims[0].model_copy(update={"method": "manual_flip_to_passed"})
    record = record.model_copy(update={"claims": [bad_claim]})

    authority = target_class_authority(record, session=session)

    assert authority.passed is False
    assert "target_class_evidence_packet_v1" in " ".join(authority.blockers)


def test_target_authority_rejects_nondeterministic_claim_id() -> None:
    session = _session()
    record = _verified_target_record(session, "offset_x_1p5_high_z")
    bad_claim = record.claims[0].model_copy(
        update={"claim_id": "target-claim:offset_x_1p5_high_z"}
    )
    record = record.model_copy(update={"claims": [bad_claim]})

    authority = target_class_authority(record, session=session)

    assert authority.passed is False
    assert "does not match expected claim ID" in " ".join(authority.blockers)


def test_target_authority_rejects_claim_handle_that_differs_from_record_handle() -> None:
    session = _session()
    record = _verified_target_record(session, "offset_x_1p5_high_z")
    bad_claim_handle = record.evidence[0].model_copy(
        update={"checksum_sha256": "0" * 64}
    )
    bad_claim = record.claims[0].model_copy(update={"evidence": [bad_claim_handle]})
    record = record.model_copy(update={"claims": [bad_claim]})

    authority = target_class_authority(record, session=session)

    assert authority.passed is False
    assert any(
        "checksum does not match record evidence" in blocker
        for blocker in authority.blockers
    )


def test_low_z_predecessor_requires_target_claim_not_legacy_fields() -> None:
    session = _session()
    profile = _safety_profile(session)
    offset = _promoted_offset(session, profile, "offset_x_1p5_low_z_dry")
    low_z = _target_record(
        "offset_x_1p5_low_z_dry",
        offset_registry_record=offset_record_id(offset),
    )
    legacy_high_z = _target_record(
        "offset_x_1p5_high_z",
        result=TargetClassResult.PASSED,
    ).model_copy(update={"legacy_camera_images": ["legacy-camera-image"]})

    result = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="low-z",
                operation="move_low_z",
                target_class="offset_x_1p5_low_z_dry",
            )
        ),
        session,
        readiness=_readiness(),
        target_records=[low_z, legacy_high_z],
        offset_registry=OffsetRegistry(records=[offset]),
        safety_profile=profile,
        daemon_motion_enabled=True,
    )

    reason_text = " ".join(result.reasons)
    assert result.allowed is False
    assert "target_class_verified:offset_x_1p5_high_z" in reason_text
    assert "legacy target evidence fields cannot authorize target class" in reason_text


def test_duplicate_target_class_records_block_plan_validation() -> None:
    session = _session()
    profile = _safety_profile(session)
    target = _target_record("center_high_z")

    result = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="high-z",
                operation="move_high_z",
                target_class="center_high_z",
            )
        ),
        session,
        readiness=_readiness(),
        target_records=[target, target.model_copy()],
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert "duplicate target-class records: center_high_z" in result.reasons


def test_liquid_handling_requires_wet_gate_with_dry_predecessor_and_offset() -> None:
    session = _session()
    profile = _safety_profile(session)
    offset = _promoted_offset(session, profile, "offset_x_1p5_wet")
    wet = _target_record(
        "offset_x_1p5_wet",
        offset_registry_record=offset_record_id(offset),
    )
    dry = _verified_target_record(session, "offset_x_1p5_low_z_dry")

    result = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="wet",
                operation="liquid_handling",
                target_class="offset_x_1p5_wet",
            )
        ),
        session,
        readiness=_readiness(),
        target_records=[wet, dry],
        offset_registry=OffsetRegistry(records=[offset]),
        safety_profile=profile,
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert result.steps[0].allowed is True
    assert "motion approval is required" in " ".join(result.reasons)
    assert [gate.gate_name for gate in result.steps[0].gate_results] == [
        "offset_authority",
        "wet",
    ]


def test_motion_step_without_target_class_still_emits_blocking_gate_result() -> None:
    cases = [
        ("move_high_z", "first_high_z"),
        ("move_low_z", "low_z_dry"),
        ("liquid_handling", "wet"),
    ]
    for operation, gate_name in cases:
        result = validate_plan_fragment(
            _plan(PlanStep(step_id=operation, operation=operation)),
            _session(),
            readiness=_readiness(),
            daemon_motion_enabled=True,
        )

        assert result.allowed is False
        assert result.steps[0].gate_results[0].gate_name == gate_name
        assert result.steps[0].gate_results[0].missing_claims == ["target_class"]


def test_unknown_and_missing_motion_targets_emit_blocking_gate_results() -> None:
    unknown = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="unknown",
                operation="move_high_z",
                target_class="missing_target",
            )
        ),
        _session(),
        readiness=_readiness(),
        daemon_motion_enabled=True,
    )
    missing_record = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="missing-record",
                operation="move_high_z",
                target_class="center_high_z",
            )
        ),
        _session(),
        readiness=_readiness(),
        daemon_motion_enabled=True,
    )

    assert unknown.steps[0].gate_results[0].missing_claims == [
        "target_class:missing_target"
    ]
    assert missing_record.steps[0].gate_results[0].missing_claims == [
        "target_record:center_high_z"
    ]


def test_failed_target_record_blocks_gate_result_without_claim_ids() -> None:
    session = _session()
    profile = _safety_profile(session)
    offset = _promoted_offset(session, profile, "offset_x_1p5_low_z_dry")
    low_z = _target_record(
        "offset_x_1p5_low_z_dry",
        result=TargetClassResult.FAILED,
        offset_registry_record=offset_record_id(offset),
    )
    high_z = _verified_target_record(session, "offset_x_1p5_high_z")

    result = validate_plan_fragment(
        _plan(
            PlanStep(
                step_id="low-z",
                operation="move_low_z",
                target_class="offset_x_1p5_low_z_dry",
            )
        ),
        session,
        readiness=_readiness(),
        target_records=[low_z, high_z],
        offset_registry=OffsetRegistry(records=[offset]),
        safety_profile=profile,
        daemon_motion_enabled=True,
    )

    low_z_gate = result.steps[0].gate_results[-1]
    assert result.allowed is False
    assert low_z_gate.gate_name == "low_z_dry"
    assert low_z_gate.passed is False
    assert low_z_gate.claim_ids == []
    assert "failed" in " ".join(low_z_gate.blockers)


def test_set_offset_is_formally_closed_fails_closed_even_with_daemon_enabled() -> None:
    # OT-2: set_offset is a CLOSED op (offsets are run-setup labware offsets, not motion
    # steps) -- rejected with an explicit closure reason, not a generic "unimplemented".
    result = validate_plan_fragment(
        _plan(PlanStep(step_id="offset", operation="set_offset")),
        _session(),
        readiness=_readiness(),
        daemon_motion_enabled=True,
    )

    assert result.allowed is False
    assert result.motion_allowed is False
    assert "set_offset is a closed operation" in " ".join(result.reasons)


def test_validation_fails_on_session_mismatch() -> None:
    result = validate_plan_fragment(
        _plan(PlanStep(step_id="inspect", operation="inspect_context"), session_id="other"),
        _session(),
        readiness=_readiness(),
    )

    assert result.allowed is False
    assert "does not match session" in " ".join(result.reasons)


def test_validate_plan_fragment_reparses_mutated_plan_objects() -> None:
    plan = _plan(
        PlanStep(
            step_id="observe",
            operation="capture_evidence",
            parameters={"filename": "fixture.jpg"},
        )
    )
    plan.steps[0].parameters["filename"] = "../fixture.jpg"

    with pytest.raises(ValidationError, match="basename"):
        validate_plan_fragment(plan, _session())
