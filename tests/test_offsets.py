from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.models import (
    BridgeSession,
    GateName,
    OffsetAuthorityState,
    OffsetRecord,
    OffsetRegistry,
)
from aevum_ot2.core.records import (
    TargetClassResult,
    TargetClassVerificationRecord,
    scaffold_fixture_qc_record,
)
from aevum_ot2.core.registry import (
    PROMOTED_OFFSET_AUTHORITY_CLAIM,
    append_offset_record,
    offset_match_gate,
    offset_record_id,
)
from aevum_ot2.core.safety import FixtureSafetyProfile, build_fixture_safety_profile


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


def _target_record(
    session: BridgeSession,
    target_class: str,
    *,
    offset_registry_record: str,
) -> TargetClassVerificationRecord:
    identity = session.fixture_identity
    return TargetClassVerificationRecord(
        target_class=target_class,
        fixture_load_name=identity.load_name,
        fixture_params_sha256=identity.params_sha256,
        labware_definition_sha256=identity.labware_definition_sha256,
        robot_serial=session.robot_serial or "",
        robot_server_version=session.robot_server_version or "",
        slot=session.slot,
        pipette_name="p300_single_gen2",
        pipette_mount="left",
        tiprack_load_name="opentrons_96_tiprack_300ul",
        offset_registry_record=offset_registry_record,
        result=TargetClassResult.BLOCKED,
    )


def _offset_record(
    session: BridgeSession,
    profile: FixtureSafetyProfile,
    target_class: str,
    *,
    authority_state: OffsetAuthorityState = OffsetAuthorityState.PROMOTED,
) -> OffsetRecord:
    identity = session.fixture_identity
    return OffsetRecord(
        offset_record_id="offset-1",
        authority_state=authority_state,
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


def test_promoted_offset_authority_gate_passes_for_exact_scope_match() -> None:
    session = _session()
    profile = _safety_profile(session)
    record = _offset_record(session, profile, "offset_x_1p5_low_z_dry")
    target_record = _target_record(
        session,
        "offset_x_1p5_low_z_dry",
        offset_registry_record=offset_record_id(record),
    )

    gate = offset_match_gate(
        registry=OffsetRegistry(records=[record]),
        session=session,
        target_record=target_record,
        safety_profile=profile,
    )

    assert gate.gate_name == GateName.OFFSET_AUTHORITY
    assert gate.passed is True
    assert gate.motion_allowed is False
    assert gate.claim_ids == ["offset-1"]


def test_proposed_offset_cannot_satisfy_promoted_authority() -> None:
    session = _session()
    profile = _safety_profile(session)
    record = _offset_record(
        session,
        profile,
        "offset_x_1p5_low_z_dry",
        authority_state=OffsetAuthorityState.PROPOSED,
    )
    target_record = _target_record(
        session,
        "offset_x_1p5_low_z_dry",
        offset_registry_record=offset_record_id(record),
    )

    gate = offset_match_gate(
        registry=OffsetRegistry(records=[record]),
        session=session,
        target_record=target_record,
        safety_profile=profile,
    )

    assert gate.passed is False
    assert "not promoted" in " ".join(gate.blockers)


def test_missing_offset_reference_reports_missing_promoted_authority() -> None:
    session = _session()
    profile = _safety_profile(session)
    target_record = _target_record(
        session,
        "offset_x_1p5_low_z_dry",
        offset_registry_record="not-yet-registered",
    )

    gate = offset_match_gate(
        registry=OffsetRegistry(),
        session=session,
        target_record=target_record,
        safety_profile=profile,
    )

    assert gate.passed is False
    assert PROMOTED_OFFSET_AUTHORITY_CLAIM in gate.missing_claims


def test_target_record_scope_mismatch_blocks_offset_authority() -> None:
    session = _session()
    profile = _safety_profile(session)
    record = _offset_record(session, profile, "offset_x_1p5_low_z_dry")
    target_record = _target_record(
        session,
        "offset_x_1p5_low_z_dry",
        offset_registry_record=offset_record_id(record),
    ).model_copy(update={"robot_serial": "OTHER"})

    gate = offset_match_gate(
        registry=OffsetRegistry(records=[record]),
        session=session,
        target_record=target_record,
        safety_profile=profile,
    )

    assert gate.passed is False
    assert "target record robot serial" in " ".join(gate.blockers)


def test_duplicate_offset_record_references_fail_closed() -> None:
    session = _session()
    profile = _safety_profile(session)
    record = _offset_record(session, profile, "offset_x_1p5_low_z_dry")
    target_record = _target_record(
        session,
        "offset_x_1p5_low_z_dry",
        offset_registry_record=offset_record_id(record),
    )

    gate = offset_match_gate(
        registry=OffsetRegistry(records=[record, record.model_copy()]),
        session=session,
        target_record=target_record,
        safety_profile=profile,
    )

    assert gate.passed is False
    assert "duplicate offset registry record reference" in " ".join(gate.blockers)


def test_empty_safety_profile_checksum_blocks_offset_authority() -> None:
    session = _session()
    profile = _safety_profile(session)
    record = _offset_record(session, profile, "offset_x_1p5_low_z_dry")
    target_record = _target_record(
        session,
        "offset_x_1p5_low_z_dry",
        offset_registry_record=offset_record_id(record),
    )
    stale_profile = profile.model_copy(update={"safety_profile_sha256": ""})

    gate = offset_match_gate(
        registry=OffsetRegistry(records=[record]),
        session=session,
        target_record=target_record,
        safety_profile=stale_profile,
    )

    assert gate.passed is False
    assert "safety_profile_sha256" in gate.missing_claims


@pytest.mark.parametrize(
    ("update", "expected"),
    [
        ({"robot_serial": "OTHER"}, "robot serial"),
        ({"slot": "2"}, "slot"),
        ({"pipette_mount": "right"}, "pipette mount"),
        ({"fixture_params_sha256": "0" * 64}, "params checksum"),
        ({"safety_profile_sha256": "0" * 64}, "safety profile checksum"),
        ({"target_policy_digest_sha256": "0" * 64}, "target policy digest"),
        ({"verification_targets": ["center_low_z_dry"]}, "target class"),
    ],
)
def test_offset_scope_mismatches_block_authority(
    update: dict[str, object],
    expected: str,
) -> None:
    session = _session()
    profile = _safety_profile(session)
    record = _offset_record(session, profile, "offset_x_1p5_low_z_dry").model_copy(
        update=update
    )
    target_record = _target_record(
        session,
        "offset_x_1p5_low_z_dry",
        offset_registry_record=offset_record_id(record),
    )

    gate = offset_match_gate(
        registry=OffsetRegistry(records=[record]),
        session=session,
        target_record=target_record,
        safety_profile=profile,
    )

    assert gate.passed is False
    assert expected in " ".join(gate.blockers)


def test_append_offset_record_assigns_stable_id(tmp_path) -> None:
    session = _session()
    profile = _safety_profile(session)
    record = _offset_record(session, profile, "offset_x_1p5_low_z_dry").model_copy(
        update={"offset_record_id": ""}
    )

    registry = append_offset_record(record, tmp_path / "offset_registry.json")

    assert len(registry.records) == 1
    assert registry.records[0].offset_record_id == offset_record_id(record)
