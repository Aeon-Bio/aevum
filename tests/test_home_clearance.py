from __future__ import annotations

from datetime import datetime, timedelta

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.models import BridgeSession, BridgeSessionState, GateName
from aevum_ot2.core.records import scaffold_fixture_qc_record
from aevum_ot2.core.recovery import NoMotionRecoveryDisposition
from aevum_ot2.core.safety import (
    FixtureSafetyProfile,
    build_fixture_safety_profile,
    home_clearance_gate,
)


def _session(state: BridgeSessionState | str = BridgeSessionState.READY_NO_MOTION) -> BridgeSession:
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
    result = build_fixture_safety_profile(
        session.fixture_identity,
        fixture_qc_record=record,
    )
    assert result.profile is not None
    return result.profile


def test_home_clearance_gate_passes_with_safety_profile_without_authorizing_motion() -> None:
    session = _session()
    profile = _safety_profile(session)

    gate = home_clearance_gate(
        session=session,
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )

    assert gate.gate_name == GateName.HOME_CLEARANCE
    assert gate.passed is True
    assert gate.motion_allowed is False
    assert gate.claim_ids == [profile.safety_profile_sha256]


def test_home_clearance_gate_requires_safety_profile() -> None:
    gate = home_clearance_gate(
        session=_session(),
        safety_profile=None,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )

    assert gate.passed is False
    assert "fixture_safety_profile_valid" in gate.missing_claims


def test_home_clearance_gate_blocks_recovery_required_session() -> None:
    session = _session(BridgeSessionState.RECOVERY_REQUIRED)
    profile = _safety_profile(session)

    gate = home_clearance_gate(
        session=session,
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )

    assert gate.passed is False
    assert "recovery_required" in " ".join(gate.blockers)


def test_home_clearance_gate_blocks_unresolved_recovery_disposition() -> None:
    session = _session()
    profile = _safety_profile(session)

    gate = home_clearance_gate(
        session=session,
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.UNRESOLVED_RECOVERY,
    )

    assert gate.passed is False
    assert "unresolved_recovery" in " ".join(gate.blockers)


def test_home_clearance_gate_requires_explicit_recovery_disposition() -> None:
    session = _session()
    profile = _safety_profile(session)

    gate = home_clearance_gate(session=session, safety_profile=profile)

    assert gate.passed is False
    assert "recovery_disposition" in gate.missing_claims


def test_home_clearance_gate_rejects_unknown_recovery_disposition() -> None:
    session = _session()
    profile = _safety_profile(session)

    gate = home_clearance_gate(
        session=session,
        safety_profile=profile,
        recovery_disposition="UNRESOLVED_RECOVERY",
    )

    assert gate.passed is False
    assert "unknown recovery disposition" in " ".join(gate.blockers)


def test_home_clearance_gate_blocks_no_local_session_recovery_disposition() -> None:
    session = _session()
    profile = _safety_profile(session)

    gate = home_clearance_gate(
        session=session,
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NO_LOCAL_SESSION,
    )

    assert gate.passed is False
    assert "no_local_session" in " ".join(gate.blockers)


def test_home_clearance_gate_blocks_empty_safety_profile_checksum() -> None:
    session = _session()
    profile = _safety_profile(session).model_copy(update={"safety_profile_sha256": ""})

    gate = home_clearance_gate(
        session=session,
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )

    assert gate.passed is False
    assert "safety_profile_sha256" in gate.missing_claims


def test_home_clearance_gate_blocks_tampered_safety_profile_digest() -> None:
    session = _session()
    profile = _safety_profile(session).model_copy(update={"conservative_high_z_mm": 999.0})

    gate = home_clearance_gate(
        session=session,
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )

    assert gate.passed is False
    assert "checksum does not match" in " ".join(gate.blockers)


def test_home_clearance_gate_blocks_non_ready_session_states() -> None:
    blocked_states = [
        BridgeSessionState.MAINTENANCE_RUN_CREATED,
        BridgeSessionState.CLOSE_FAILED,
        BridgeSessionState.CLOSED,
        BridgeSessionState.FAILED,
        BridgeSessionState.HIGH_Z_READY,
        BridgeSessionState.DRY_READY,
        BridgeSessionState.WET_READY,
    ]
    for state in blocked_states:
        session = _session(state)
        profile = _safety_profile(session)

        gate = home_clearance_gate(
            session=session,
            safety_profile=profile,
            recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
        )

        assert gate.passed is False
        assert state.value in " ".join(gate.blockers)


def test_home_clearance_gate_allows_armed_motion_commissioning_session() -> None:
    session = _session(BridgeSessionState.MOTION_COMMISSIONING_ARMED)
    profile = _safety_profile(session)

    gate = home_clearance_gate(
        session=session,
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )

    assert gate.passed is True


def test_home_clearance_gate_blocks_stale_safety_profile_scope() -> None:
    session = _session()
    profile = _safety_profile(session).model_copy(update={"fixture_params_sha256": "0" * 64})

    gate = home_clearance_gate(
        session=session,
        safety_profile=profile,
        recovery_disposition=NoMotionRecoveryDisposition.NOT_STARTED,
    )

    assert gate.passed is False
    assert "params checksum" in " ".join(gate.blockers)
