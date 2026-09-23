from __future__ import annotations

import ast
import json
from pathlib import Path

from aevum_cad.row_coupon.artifacts import (
    ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS,
)

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs" / "assembly" / "sequence_and_split_matrix.json"
AUTHORITY_PATH = ROOT / "docs" / "assembly" / "artifact_authority.json"
ASSEMBLY_PATH = ROOT / "src" / "aevum_cad" / "row_coupon" / "assembly.py"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def _installed_part_names() -> list[str]:
    tree = ast.parse(ASSEMBLY_PATH.read_text())
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_row_coupon_installed_parts"
    )
    result = next(
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
    )
    return [
        key.value
        for key in result.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    ]


def test_matrix_covers_every_authoritative_source_and_release_body() -> None:
    matrix = _load(MATRIX_PATH)
    authority = _load(AUTHORITY_PATH)
    sources = authority["canonical_sources"]
    transitions = matrix["artifact_transitions"]

    expected_sources = {row["source_artifact_id"] for row in sources}
    actual_sources = [row["source_artifact_id"] for row in transitions]
    assert len(actual_sources) == len(set(actual_sources)) == 38
    assert set(actual_sources) == expected_sources

    release_bodies = [
        release_body_id
        for source in sources
        for release_body_id in source["release_body_ids"]
    ]
    mapped_release_bodies = [
        release_body_id
        for source in sources
        if source["source_artifact_id"] in set(actual_sources)
        for release_body_id in source["release_body_ids"]
    ]
    assert len(release_bodies) == len(set(release_bodies)) == 46
    assert set(mapped_release_bodies) == set(release_bodies)
    assert matrix["counts"]["release_bodies"] == len(release_bodies)

    install_states = {row["state_id"] for row in matrix["assembly_states"]}
    removal_states = {row["state_id"] for row in matrix["removal_states"]}
    for transition in transitions:
        assert transition["install_state_id"] in install_states
        assert transition["removal_state_id"] in removal_states
        assert transition["status"] != "accepted"
    assert matrix["acceptance_policy"]["permanent_artifacts"] == []


def test_enumerated_sequence_covers_installed_manifest_once_each_way() -> None:
    matrix = _load(MATRIX_PATH)
    expected = _installed_part_names()
    installed = [
        family
        for state in matrix["assembly_states"]
        for family in state["install_families"]
    ]
    removed = [
        family
        for state in matrix["removal_states"]
        for family in state["removes_families"]
    ]

    assert len(expected) == matrix["counts"]["installed_families"] == 28
    assert len(installed) == len(set(installed)) == len(expected)
    assert set(installed) == set(expected)
    assert len(removed) == len(set(removed)) == len(expected)
    assert set(removed) == set(expected)


def test_all_eight_split_sources_have_feature_and_load_evidence() -> None:
    matrix = _load(MATRIX_PATH)
    authority = _load(AUTHORITY_PATH)
    splits = matrix["split_sources"]
    expected = set(ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS)

    assert len(splits) == 8
    assert {row["source_artifact_id"] for row in splits} == expected
    assert matrix["counts"]["split_sources"] == len(splits)
    assert all(row["axis"] == "y" for row in splits)
    assert {row["split_y_mm"] for row in splits} == {188.625, 198.0}
    assert all(row["blocking"] is True for row in splits)

    authority_by_source = {
        row["source_artifact_id"]: row for row in authority["canonical_sources"]
    }
    for split in splits:
        assert len(authority_by_source[split["source_artifact_id"]]["release_body_ids"]) == 2
        intersections = split["feature_load_intersections"]
        assert len(intersections) >= 2
        assert any("load" in row["feature_class"] for row in intersections)
        assert all(row["evidence"] for row in intersections)

    feature_classes = " ".join(
        intersection["feature_class"]
        for split in splits
        for intersection in split["feature_load_intersections"]
    )
    for required_feature in (
        "datum",
        "seal",
        "sample_relief",
        "latch",
        "snap",
        "channel",
        "load",
    ):
        assert required_feature in feature_classes

    plain = [
        row for row in splits if row["mating_feature_kind"] == "plain_butt_fallback"
    ]
    assert not plain
    assert matrix["counts"]["plain_butt_blockers"] == 0
    assert all(row["seam_status"].startswith(("pending_", "modeled_")) for row in splits)
    butt_defect = next(
        defect
        for defect in authority["known_defects"]
        if defect["defect_id"] == "unretained_plain_butt_splits"
    )
    assert butt_defect["status"] == "digitally_corrected_physical_gate_pending"


def test_unsupported_service_paths_fail_closed_and_no_rework_is_an_acceptance_step() -> None:
    matrix = _load(MATRIX_PATH)
    service_paths = matrix["service_paths"]

    assert service_paths
    assert all(row["blocking"] is True for row in service_paths)
    assert all(row["status"].startswith("blocked_") for row in service_paths)
    assert all(row["missing_proof"] for row in service_paths)
    assert {
        "gas_pcb_cartridge_vertical_service",
        "sht41_carrier_side_service",
        "ir_thermopile_underside_service",
        "connector_shroud_and_pigtail_service",
        "harness_cover_install_and_release",
        "gas_tube_service",
        "sample_relief_cap_service",
        "microplate_and_septum_vertical_service",
        "wedge_lock_release",
    } == {row["path_id"] for row in service_paths}

    assert set(matrix["acceptance_policy"]["forbidden_acceptance_actions"]) == {
        "glue",
        "adhesive",
        "filing",
        "trimming",
        "unmodeled_hardware",
    }
    assert not any(
        forbidden in action
        for action in matrix["acceptance_policy"]["allowed_joining_actions"]
        for forbidden in matrix["acceptance_policy"]["forbidden_acceptance_actions"]
    )
