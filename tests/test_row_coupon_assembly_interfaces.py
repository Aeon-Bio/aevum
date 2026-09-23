from __future__ import annotations

import copy
import json
from itertools import combinations
from pathlib import Path
from typing import Any

import pytest

from aevum_cad.params import load_params
from aevum_cad.row_coupon import (
    build_lid_cover,
    build_lid_manifold_shell,
    row_coupon_part_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
MATRIX = ROOT / "docs" / "assembly" / "interface_matrix.json"
ARTIFACT_AUTHORITY = ROOT / "docs" / "assembly" / "artifact_authority.json"

TOP_LEVEL_KEYS = {
    "schema_version",
    "matrix_id",
    "scope",
    "policy",
    "source_anchors",
    "current_geometry_summary",
    "geometry_observations",
    "interfaces",
    "explicit_exclusion_pair_keys",
}
INTERFACE_KEYS = {
    "interface_id",
    "pair_key",
    "parts",
    "interface_class",
    "intended_contact_type",
    "forbidden_intersection",
    "nominal_clearance_mm",
    "minimum_clearance_mm",
    "allowed_motion",
    "tolerance_basis",
    "inspection_method",
    "evidence_owner",
    "current_intersection_mm3",
    "current_geometry_status",
    "blocking_reason",
    "known_defect_id",
}
REQUIRED_CLASSES = {"seal", "latch", "sensor", "cable", "tube", "datum", "service"}
GEOMETRY_STATUSES = {
    "blocked",
    "classified_intentional_overlap",
    "no_positive_overlap",
}
EVIDENCE_OWNERS = {
    "gate_2_dry_assembly",
    "gate_3_ot2_placement",
    "gate_4_wet_dry_witness",
    "gate_6_sensor_thermal",
}


def _pair_key(left: str, right: str) -> str:
    return "::".join(sorted((left, right)))


def _expected_pair_keys(families: list[str]) -> set[str]:
    return {_pair_key(left, right) for left, right in combinations(families, 2)}


def _validate_static_matrix(matrix: dict[str, Any]) -> None:
    assert set(matrix) == TOP_LEVEL_KEYS
    assert matrix["schema_version"] == 1
    assert ARTIFACT_AUTHORITY.is_file()

    manifest_families = list(row_coupon_part_manifest()["installed"])
    scope = matrix["scope"]
    assert scope["installed_families"] == manifest_families
    assert scope["installed_family_count"] == len(manifest_families) == 28
    expected_pairs = _expected_pair_keys(manifest_families)
    assert scope["unordered_pair_count"] == len(expected_pairs) == 378
    epsilon = float(scope["volume_epsilon_mm3"])
    assert epsilon > 0.0
    assert scope["runtime_authority"] is False

    interfaces = matrix["interfaces"]
    interface_keys: list[str] = []
    for row in interfaces:
        assert set(row) == INTERFACE_KEYS
        pair_key = row["pair_key"]
        assert row["parts"] == sorted(row["parts"])
        assert len(row["parts"]) == 2
        assert row["parts"][0] != row["parts"][1]
        assert pair_key == _pair_key(*row["parts"])
        assert pair_key in expected_pairs
        assert row["interface_id"] == f"{pair_key}#{row['interface_class']}"
        assert row["interface_class"]
        assert row["intended_contact_type"]
        assert isinstance(row["forbidden_intersection"], bool)
        assert isinstance(row["nominal_clearance_mm"], (int, float))
        assert isinstance(row["minimum_clearance_mm"], (int, float))
        assert row["allowed_motion"]
        assert row["tolerance_basis"]
        assert row["inspection_method"]
        assert all(isinstance(method, str) and method for method in row["inspection_method"])
        assert row["evidence_owner"] in EVIDENCE_OWNERS
        assert row["current_intersection_mm3"] >= 0.0
        assert row["current_geometry_status"] in GEOMETRY_STATUSES
        assert row["current_geometry_status"] != "pass"
        if row["current_intersection_mm3"] > epsilon:
            if row["forbidden_intersection"]:
                assert row["current_geometry_status"] == "blocked"
                assert row["blocking_reason"]
            else:
                assert row["current_geometry_status"] == "classified_intentional_overlap"
                assert row["blocking_reason"] is None
        else:
            assert row["current_geometry_status"] == "no_positive_overlap"
            assert row["blocking_reason"] is None
        interface_keys.append(pair_key)

    assert len(interface_keys) == len(set(interface_keys))
    assert REQUIRED_CLASSES <= {row["interface_class"] for row in interfaces}

    exclusions = matrix["explicit_exclusion_pair_keys"]
    assert exclusions == sorted(exclusions)
    assert len(exclusions) == len(set(exclusions))
    assert set(exclusions) <= expected_pairs
    assert not set(exclusions).intersection(interface_keys)
    assert set(interface_keys).union(exclusions) == expected_pairs

    observed = matrix["geometry_observations"]["positive_intersections_mm3"]
    assert observed
    assert all(volume > epsilon for volume in observed.values())
    positive_rows = {
        row["pair_key"] for row in interfaces if float(row["current_intersection_mm3"]) > epsilon
    }
    assert set(observed) == positive_rows
    assert not set(observed).intersection(exclusions)
    rows_by_pair = {row["pair_key"]: row for row in interfaces}
    for pair_key, volume in observed.items():
        assert rows_by_pair[pair_key]["current_intersection_mm3"] == pytest.approx(
            volume, rel=1e-9, abs=1e-9
        )

    summary = matrix["current_geometry_summary"]
    blocked = [row for row in interfaces if row["current_geometry_status"] == "blocked"]
    intentional = [
        row
        for row in interfaces
        if row["current_geometry_status"] == "classified_intentional_overlap"
    ]
    assert summary["positive_intersection_pair_count"] == len(observed)
    assert summary["blocked_pair_count"] == len(blocked)
    assert summary["classified_intentional_overlap_pair_count"] == len(intentional)
    assert summary["assembly_acceptance"] == "blocked"


def test_installed_interface_matrix_is_complete_and_fail_closed() -> None:
    matrix = json.loads(MATRIX.read_text())
    _validate_static_matrix(matrix)


def test_static_validator_rejects_unclassified_or_falsely_passing_overlap() -> None:
    matrix = json.loads(MATRIX.read_text())
    epsilon = float(matrix["scope"]["volume_epsilon_mm3"])
    known_row = next(
        row
        for row in matrix["interfaces"]
        if float(row.get("current_intersection_mm3") or 0.0) > epsilon
    )
    known_pair = known_row["pair_key"]

    unclassified = copy.deepcopy(matrix)
    unclassified["interfaces"] = [
        row for row in unclassified["interfaces"] if row["pair_key"] != known_pair
    ]
    unclassified["explicit_exclusion_pair_keys"].append(known_pair)
    unclassified["explicit_exclusion_pair_keys"].sort()
    with pytest.raises(AssertionError):
        _validate_static_matrix(unclassified)

    falsely_passing = copy.deepcopy(matrix)
    target = next(row for row in falsely_passing["interfaces"] if row["pair_key"] == known_pair)
    target["current_geometry_status"] = "no_positive_overlap"
    with pytest.raises(AssertionError):
        _validate_static_matrix(falsely_passing)


def test_lid_cover_shell_collision_remains_eliminated() -> None:
    params = load_params(PARAMS)
    cover = build_lid_cover(params, assembly_position=True)
    shell = build_lid_manifold_shell(params, assembly_position=True)
    overlap = cover.intersect(shell).val()
    measured_volume = overlap.Volume()

    matrix = json.loads(MATRIX.read_text())
    row = next(
        row for row in matrix["interfaces"] if row["pair_key"] == "lid_cover::lid_manifold_shell"
    )
    authority = json.loads(ARTIFACT_AUTHORITY.read_text())
    known_defects = {defect["defect_id"]: defect["status"] for defect in authority["known_defects"]}

    assert measured_volume == pytest.approx(0.0, abs=1e-4)
    assert params["production_assembly"]["lid_cover_tongue_clearance_xy"] == 0.25
    assert row["current_intersection_mm3"] == pytest.approx(measured_volume, abs=1e-4)
    assert row["forbidden_intersection"] is True
    assert row["current_geometry_status"] == "no_positive_overlap"
    assert row["known_defect_id"] == "lid_cover_shell_installed_overlap"
    assert row["blocking_reason"] is None
    assert known_defects[row["known_defect_id"]] == "digitally_resolved_physical_gate_pending"
