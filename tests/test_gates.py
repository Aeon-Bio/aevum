from __future__ import annotations

from aevum_ot2.core.artifacts import current_fixture_identity
from aevum_ot2.core.gates import (
    FIXTURE_DIMENSIONS_CLAIM,
    fixture_qc_claims_from_legacy_record,
    fixture_qc_gate_from_claims,
    fixture_qc_gate_from_legacy_record,
    registration_gate_result,
)
from aevum_ot2.core.models import EvidenceQuality, GateName
from aevum_ot2.core.records import (
    FixtureQcRecord,
    scaffold_fixture_qc_record,
    write_fixture_qc_record,
)


def _passing_fixture_qc_record() -> FixtureQcRecord:
    identity = current_fixture_identity()
    nominal = identity.nominal_dimensions_mm
    return scaffold_fixture_qc_record(
        identity,
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


def test_fixture_qc_legacy_record_derives_source_agnostic_claims(tmp_path) -> None:
    record = _passing_fixture_qc_record()
    handle = write_fixture_qc_record(record, tmp_path / "fixture_qc.json")

    claims = fixture_qc_claims_from_legacy_record(record, record_handle=handle)

    claim_by_type = {claim.claim_type: claim for claim in claims}
    assert claim_by_type[FIXTURE_DIMENSIONS_CLAIM].value is True
    assert claim_by_type["fixture_visible_in_slot"].quality == EvidenceQuality.LEGACY
    assert "adhesion_tabs_trimmed" not in claim_by_type
    assert all(claim.evidence for claim in claims)
    assert all(claim.evidence[0].checksum_sha256 for claim in claims)
    assert all(not hasattr(claim, "motion_allowed") for claim in claims)


def test_fixture_qc_gate_passes_without_authorizing_motion(tmp_path) -> None:
    record = _passing_fixture_qc_record()
    handle = write_fixture_qc_record(record, tmp_path / "fixture_qc.json")

    gate = fixture_qc_gate_from_legacy_record(record, record_handle=handle)

    assert gate.gate_name == GateName.FIXTURE_QC
    assert gate.passed is True
    assert gate.motion_allowed is False
    assert gate.blockers == []
    assert gate.missing_claims == []


def test_fixture_qc_gate_blocks_failed_legacy_claims(tmp_path) -> None:
    record = _passing_fixture_qc_record()
    record.guide_holes_open = False
    handle = write_fixture_qc_record(record, tmp_path / "fixture_qc.json")
    claims = fixture_qc_claims_from_legacy_record(record, record_handle=handle)

    gate = fixture_qc_gate_from_claims(claims)

    assert gate.passed is False
    assert gate.motion_allowed is False
    assert any("guide_holes_open" in blocker for blocker in gate.blockers)


def test_registration_gate_wraps_fixture_qc_claims_without_motion(tmp_path) -> None:
    record = _passing_fixture_qc_record()
    handle = write_fixture_qc_record(record, tmp_path / "fixture_qc.json")
    fixture_gate = fixture_qc_gate_from_legacy_record(record, record_handle=handle)

    gate = registration_gate_result(blockers=[], fixture_qc_gate=fixture_gate)

    assert gate.gate_name == GateName.REGISTRATION
    assert gate.passed is True
    assert gate.motion_allowed is False
    assert gate.claim_ids == fixture_gate.claim_ids
    assert gate.evidence
