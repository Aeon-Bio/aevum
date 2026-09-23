from __future__ import annotations

import json
from functools import lru_cache

from aevum_cad.row_coupon.assembly_audit import audit_row_coupon_integrated_assembly


@lru_cache(maxsize=1)
def _report() -> dict:
    return audit_row_coupon_integrated_assembly()


def test_integrated_audit_is_machine_readable_and_fail_closed() -> None:
    report = _report()
    assert json.loads(json.dumps(report)) == report
    assert report["overall_status"] == "GATE_FAIL"
    assert report["assembly_authorized"] is False
    assert set(report["verdicts"]) == {"digital", "manufacturing", "coupon", "physical"}
    assert report["boundaries"] == {
        "digital_pass_is_physical_acceptance": False,
        "manufacturing_pass_is_assembly_acceptance": False,
        "coupon_pass_is_final_artifact_acceptance": False,
        "d2_human_physical_acceptance_required": True,
    }


def test_authority_and_retained_seam_proofs_are_exact() -> None:
    evidence = _report()["evidence"]["authority"]
    assert evidence["canonical_source_count"] == 38
    assert evidence["release_body_count"] == 46
    assert evidence["live_rigid_piece_count"] == 38
    assert evidence["live_release_body_count"] == 46
    assert evidence["release_artifact_hash_mismatch_count"] == 0
    assert evidence["seam_proof_count"] == 8


def test_live_geometry_matches_frozen_matrix_without_forbidden_pairs() -> None:
    evidence = _report()["evidence"]["interfaces_and_service"]
    assert evidence["installed_family_count"] == 28
    assert evidence["unordered_pair_count"] == 378
    assert evidence["interface_count"] == 64
    assert evidence["exclusion_count"] == 314
    assert evidence["static_positive_pair_count"] == 7
    assert evidence["live_positive_pair_count"] == 7
    assert evidence["static_live_change_count"] == 0
    assert evidence["collision_geometry_scope"] == "installed_release_bodies"
    assert evidence["unclassified_live_intersections_mm3"] == {}
    assert evidence["forbidden_live_intersections_mm3"] == {}
    codes = _report()["verdicts"]["digital"]["finding_codes"]
    assert "STATIC_LIVE_GEOMETRY_MISMATCH" not in codes
    assert "FORBIDDEN_LIVE_INTERSECTION" not in codes
    assert "UNCLASSIFIED_LIVE_INTERSECTION" not in codes


def test_service_coupon_cots_material_and_manufacturing_boundaries_are_explicit() -> None:
    report = _report()
    interface_evidence = report["evidence"]["interfaces_and_service"]
    coupon = report["evidence"]["coupons"]
    physical = report["evidence"]["physical"]
    manufacturing = report["evidence"]["manufacturing"]
    assert interface_evidence["split_source_count"] == 8
    assert interface_evidence["service_path_count"] == 9
    assert interface_evidence["blocked_service_path_count"] == 9
    assert (
        coupon["family_count"],
        coupon["interface_mapping_count"],
        coupon["split_mapping_count"],
        coupon["service_mapping_count"],
    ) == (8, 64, 8, 9)
    assert coupon["completed_passing_station_count"] == 0
    assert physical["operating_gasket_material"] == "unresolved"
    assert physical["exact_cots_class_count"] == 0
    assert report["expected_counts"]["plates"] == 12
    assert manufacturing["plate_count"] == 12
    assert manufacturing["rigid_body_count"] == 38
    assert manufacturing["artifact_error_count"] == 0
    assert report["verdicts"]["manufacturing"]["status"] == "gate_pass"
    assert report["verdicts"]["coupon"]["status"] == "gate_fail"
    assert report["verdicts"]["physical"]["status"] == "gate_fail"
    assert (
        "WEDGE_LOCK_OPERATING_MATERIAL_BLOCKED" in report["verdicts"]["physical"]["finding_codes"]
    )
