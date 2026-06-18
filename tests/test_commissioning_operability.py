from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.commissioning import (
    CommissioningReport,
    run_commissioning_preflight,
    run_commissioning_sequence,
)
from aevum_ot2.core.execution import PlanExecutionResult
from aevum_ot2.core.models import BridgeSession, GateName, GateResult
from aevum_ot2.core.motion_approval import MotionApproval, build_motion_approval
from aevum_ot2.core.motion_commissioning import (
    MISSING_APPROVAL_REASON,
    MotionApprovalArmResult,
    MotionApprovalRecord,
)
from aevum_ot2.core.plans import PlanFragment, PlanStep
from aevum_ot2.core.records import scaffold_fixture_qc_record
from aevum_ot2.core.safety import (
    FixtureSafetyProfile,
    _safety_profile_digest,
    build_fixture_safety_profile,
)
from aevum_ot2.core.sessions import write_session
from aevum_ot2.core.validation import PlanValidationResult, StepValidationResult
from aevum_ot2.server.service import BridgeService, BridgeServiceError


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
        state=state,
        created_at=now,
        updated_at=now,
        lease_expires_at=now + timedelta(minutes=10),
        maintenance_run_id="maintenance-run-1",
        slot="1",
        fixture_identity=identity,
        fixture_orientation="canonical",
        fixture_pose_digest_sha256="a" * 64,
        fixture_pose_path="data/measurements/sessions/session-1/fixture_pose.json",
        definition_uri="aevum/aevum_p300_poc_fixture/1",
        loaded_labware_id="fixture-1",
        last_command_id="command-1",
        last_command_key="load-key-1",
        last_command_status="succeeded",
        evidence_index_path="data/measurements/ot2_evidence_index.json",
    )


def _home_plan(session: BridgeSession) -> PlanFragment:
    return PlanFragment(
        session_id=session.session_id,
        steps=[PlanStep(step_id="home", operation="home")],
    )


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


def _missing_approval_validation(session: BridgeSession) -> PlanValidationResult:
    return PlanValidationResult(
        session_id=session.session_id,
        allowed=False,
        motion_allowed=False,
        reasons=[MISSING_APPROVAL_REASON],
        steps=[
            StepValidationResult(
                step_id="home",
                operation="home",
                allowed=False,
                requires_motion=True,
                reasons=["motion approval is required for motion execution"],
            )
        ],
    )


def _armed_result(
    session: BridgeSession,
    approval: MotionApproval,
) -> MotionApprovalArmResult:
    return MotionApprovalArmResult(
        session_id=session.session_id,
        armed=True,
        approval=approval,
        record=MotionApprovalRecord(approval=approval, robot_url=session.robot_url),
        validation=_missing_approval_validation(session),
    )


def _approved_home_validation(approval: MotionApproval) -> PlanValidationResult:
    return PlanValidationResult(
        session_id=approval.session_id,
        allowed=True,
        motion_allowed=True,
        motion_approval_id=approval.approval_id,
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


def _service_with_session(tmp_path, *, motion_enabled: bool = False) -> tuple[
    BridgeService, BridgeSession
]:
    db_path = tmp_path / "state.sqlite3"
    session = _session()
    write_session(session, db_path)
    service = BridgeService(state_db_path=db_path, motion_enabled=motion_enabled)
    return service, session


def _spy_validate_missing_approval(
    service: BridgeService,
    session: BridgeSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service,
        "validate_plan",
        lambda *args, **kwargs: _missing_approval_validation(session),
    )


def test_preflight_clean_reports_blocked_by_missing_approval(
    tmp_path, monkeypatch
) -> None:
    service, session = _service_with_session(tmp_path)
    _spy_validate_missing_approval(service, session, monkeypatch)

    report = run_commissioning_preflight(
        service,
        session.session_id,
        _home_plan(session),
        safety_profile=_safety_profile(session),
    )

    assert isinstance(report, CommissioningReport)
    assert report.health_ok is True
    assert report.state_db_ok is True
    assert report.plan_blocked_by_missing_approval_only is True
    assert report.blockers == []
    assert report.armed is False
    assert report.executed is False
    assert report.dry_run is True
    names = [step.name for step in report.steps]
    assert names == ["health_state_db", "session_context", "validate_plan"]


def test_dry_run_default_never_arms(tmp_path, monkeypatch) -> None:
    service, session = _service_with_session(tmp_path)
    _spy_validate_missing_approval(service, session, monkeypatch)

    arm_calls: list[object] = []

    def spy_arm(*args: object, **kwargs: object) -> MotionApprovalArmResult:
        arm_calls.append((args, kwargs))
        raise AssertionError("arm_motion_approval must NOT be called in a dry run")

    monkeypatch.setattr(service, "arm_motion_approval", spy_arm)

    report = run_commissioning_sequence(
        service,
        session.session_id,
        _home_plan(session),
        approved_by="operator-1",
        safety_profile=_safety_profile(session),
        # Defaults: confirm_arm False, motion_enabled False -> dry run.
    )

    assert arm_calls == []
    assert report.armed is False
    assert report.executed is False
    assert report.dry_run is True
    arm_step = next(step for step in report.steps if step.phase == "arm")
    assert arm_step.status == "would_arm"
    assert report.blockers == []


def test_arm_refused_when_motion_disabled(tmp_path, monkeypatch) -> None:
    # confirm_arm=True but motion_enabled=False must still NOT arm.
    service, session = _service_with_session(tmp_path, motion_enabled=False)
    _spy_validate_missing_approval(service, session, monkeypatch)

    def spy_arm(*args: object, **kwargs: object) -> MotionApprovalArmResult:
        raise AssertionError("arm must not run while motion is disabled")

    monkeypatch.setattr(service, "arm_motion_approval", spy_arm)

    report = run_commissioning_sequence(
        service,
        session.session_id,
        _home_plan(session),
        approved_by="operator-1",
        safety_profile=_safety_profile(session),
        confirm_arm=True,
        motion_enabled=False,
    )

    assert report.armed is False
    assert report.executed is False
    assert report.dry_run is True
    arm_step = next(step for step in report.steps if step.phase == "arm")
    assert arm_step.status == "would_arm"
    assert "motion_enabled not set" in arm_step.detail


def test_preflight_surfaces_non_missing_approval_blockers(
    tmp_path, monkeypatch
) -> None:
    service, session = _service_with_session(tmp_path)
    blocked = PlanValidationResult(
        session_id=session.session_id,
        allowed=False,
        motion_allowed=False,
        reasons=[MISSING_APPROVAL_REASON, "home: home clearance gate failed"],
    )
    monkeypatch.setattr(service, "validate_plan", lambda *a, **k: blocked)

    report = run_commissioning_preflight(
        service,
        session.session_id,
        _home_plan(session),
        safety_profile=_safety_profile(session),
    )

    assert report.plan_blocked_by_missing_approval_only is False
    assert any("home clearance gate failed" in blocker for blocker in report.blockers)


def test_preflight_blocks_when_validation_unexpectedly_allows(
    tmp_path, monkeypatch
) -> None:
    # Fail-closed: a motion-disabled, approval-free validation that claims to
    # allow execution must be treated as a blocker, not a green light.
    service, session = _service_with_session(tmp_path)
    allowing = PlanValidationResult(
        session_id=session.session_id,
        allowed=True,
        motion_allowed=True,
    )
    monkeypatch.setattr(service, "validate_plan", lambda *a, **k: allowing)

    report = run_commissioning_preflight(
        service,
        session.session_id,
        _home_plan(session),
        safety_profile=_safety_profile(session),
    )

    assert report.plan_blocked_by_missing_approval_only is False
    assert report.blockers
    assert report.armed is False


def test_health_failure_fails_closed(tmp_path, monkeypatch) -> None:
    service, session = _service_with_session(tmp_path)

    def boom() -> object:
        raise BridgeServiceError(503, "state_db_busy", "db is busy")

    monkeypatch.setattr(service, "list_sessions", boom)

    report = run_commissioning_preflight(
        service,
        session.session_id,
        _home_plan(session),
        safety_profile=_safety_profile(session),
    )

    assert report.state_db_ok is False
    assert report.blockers
    assert report.steps[0].status == "error"
    assert report.context is None


def test_session_context_failure_fails_closed(tmp_path) -> None:
    service, session = _service_with_session(tmp_path)

    report = run_commissioning_preflight(
        service,
        "missing-session",
        PlanFragment(
            session_id="missing-session",
            steps=[PlanStep(step_id="home", operation="home")],
        ),
        safety_profile=_safety_profile(session),
    )

    assert report.health_ok is True
    assert report.context is None
    assert report.armed is False
    assert any("session context fetch failed" in blocker for blocker in report.blockers)


def test_arm_blocked_by_bridge_keeps_armed_false(tmp_path, monkeypatch) -> None:
    service, session = _service_with_session(tmp_path, motion_enabled=True)
    _spy_validate_missing_approval(service, session, monkeypatch)

    refused = MotionApprovalArmResult(
        session_id=session.session_id,
        validation=_missing_approval_validation(session),
        blockers=["session lease is expired"],
    )
    arm_calls: list[object] = []

    def spy_arm(*args: object, **kwargs: object) -> MotionApprovalArmResult:
        arm_calls.append(kwargs)
        return refused

    execute_calls: list[object] = []

    def spy_execute(*args: object, **kwargs: object) -> PlanExecutionResult:
        execute_calls.append(kwargs)
        raise AssertionError("execute must not run after a refused arm")

    monkeypatch.setattr(service, "arm_motion_approval", spy_arm)
    monkeypatch.setattr(service, "execute_next", spy_execute)

    report = run_commissioning_sequence(
        service,
        session.session_id,
        _home_plan(session),
        approved_by="operator-1",
        safety_profile=_safety_profile(session),
        confirm_arm=True,
        motion_enabled=True,
        confirm_execute=True,
    )

    assert len(arm_calls) == 1
    assert execute_calls == []
    assert report.armed is False
    assert report.executed is False
    assert "session lease is expired" in report.blockers


def test_arm_succeeds_then_execute_gate_blocks_without_confirm(
    tmp_path, monkeypatch
) -> None:
    # confirm_arm + motion_enabled but no confirm_execute: arm, then stop.
    service, session = _service_with_session(tmp_path, motion_enabled=True)
    _spy_validate_missing_approval(service, session, monkeypatch)
    profile = _pose_scoped_profile(session)
    approval = build_motion_approval(
        _home_plan(session),
        session=session,
        safety_profile=profile,
        step_id="home",
        approved_by="operator-1",
    )

    monkeypatch.setattr(
        service,
        "arm_motion_approval",
        lambda *a, **k: _armed_result(session, approval),
    )

    def spy_execute(*args: object, **kwargs: object) -> PlanExecutionResult:
        raise AssertionError("execute must not run without confirm_execute")

    monkeypatch.setattr(service, "execute_next", spy_execute)

    report = run_commissioning_sequence(
        service,
        session.session_id,
        _home_plan(session),
        approved_by="operator-1",
        safety_profile=profile,
        confirm_arm=True,
        motion_enabled=True,
        confirm_execute=False,
    )

    assert report.armed is True
    assert report.approval_id == approval.approval_id
    assert report.executed is False
    assert report.blockers == []
    execute_step = next(step for step in report.steps if step.phase == "execute")
    assert execute_step.status == "would_execute"


def test_execute_blocked_keeps_executed_false(tmp_path, monkeypatch) -> None:
    service, session = _service_with_session(tmp_path, motion_enabled=True)
    _spy_validate_missing_approval(service, session, monkeypatch)
    profile = _pose_scoped_profile(session)
    approval = build_motion_approval(
        _home_plan(session),
        session=session,
        safety_profile=profile,
        step_id="home",
        approved_by="operator-1",
    )
    monkeypatch.setattr(
        service,
        "arm_motion_approval",
        lambda *a, **k: _armed_result(session, approval),
    )

    blocked_execution = PlanExecutionResult(
        session_id=session.session_id,
        plan_step_count=1,
        executed=False,
        motion_commands_sent=False,
        validation=PlanValidationResult(
            session_id=session.session_id,
            allowed=False,
            motion_allowed=False,
            reasons=["motion approval is not armed: consumed"],
        ),
    )
    execute_calls: list[object] = []

    def spy_execute(*args: object, **kwargs: object) -> PlanExecutionResult:
        execute_calls.append(kwargs)
        return blocked_execution

    monkeypatch.setattr(service, "execute_next", spy_execute)

    report = run_commissioning_sequence(
        service,
        session.session_id,
        _home_plan(session),
        approved_by="operator-1",
        safety_profile=profile,
        confirm_arm=True,
        motion_enabled=True,
        confirm_execute=True,
    )

    assert len(execute_calls) == 1
    # The bridge-minted approval, not one created by this layer, is forwarded.
    assert execute_calls[0]["motion_approval"] is approval
    assert report.armed is True
    assert report.executed is False
    assert report.motion_commands_sent is False
    assert "motion approval is not armed: consumed" in report.blockers


def test_full_confirm_executes_via_bridge(tmp_path, monkeypatch) -> None:
    service, session = _service_with_session(tmp_path, motion_enabled=True)
    _spy_validate_missing_approval(service, session, monkeypatch)
    profile = _pose_scoped_profile(session)
    approval = build_motion_approval(
        _home_plan(session),
        session=session,
        safety_profile=profile,
        step_id="home",
        approved_by="operator-1",
    )
    monkeypatch.setattr(
        service,
        "arm_motion_approval",
        lambda *a, **k: _armed_result(session, approval),
    )

    executed = PlanExecutionResult(
        session_id=session.session_id,
        plan_step_count=1,
        executed_step_id="home",
        executed=True,
        motion_commands_sent=True,
        validation=_approved_home_validation(approval),
    )
    monkeypatch.setattr(service, "execute_next", lambda *a, **k: executed)

    report = run_commissioning_sequence(
        service,
        session.session_id,
        _home_plan(session),
        approved_by="operator-1",
        safety_profile=profile,
        confirm_arm=True,
        motion_enabled=True,
        confirm_execute=True,
    )

    assert report.armed is True
    assert report.executed is True
    assert report.motion_commands_sent is True
    assert report.blockers == []
    phases = [step.phase for step in report.steps]
    assert phases == ["preflight", "preflight", "preflight", "arm", "execute"]
