from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pytest

from aevum_cad.params import load_params
from aevum_cad.row_coupon import (
    row_coupon_final_print_piece_plan,
    row_coupon_part_manifest,
    row_coupon_physical_artifact_manifest,
    row_coupon_physical_artifact_specs,
)


ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
REGISTRY = ROOT / "docs" / "assembly" / "artifact_authority.json"

TOP_LEVEL_KEYS = {
    "schema_version",
    "registry_id",
    "identity_authority",
    "source_authorities",
    "counts",
    "known_defects",
    "canonical_sources",
    "release_bodies",
}
SOURCE_KEYS = {
    "source_artifact_id",
    "source_class",
    "installed_part",
    "role",
    "current_slice_material",
    "approved_operating_material",
    "material_status",
    "geometry_state",
    "mates",
    "evidence",
    "release_body_ids",
}
BODY_KEYS = {
    "release_body_id",
    "source_artifact_id",
    "body_class",
    "authority_inherited_from_source",
    "outputs",
}
EVIDENCE_KEYS = {"gate", "owner", "status", "required_gates"}
OUTPUT_KEYS = {"path", "sha256"}


@pytest.fixture(scope="module")
def live_authority() -> dict[str, Any]:
    params = load_params(PARAMS)
    specs = row_coupon_physical_artifact_specs(params)
    manifest = row_coupon_physical_artifact_manifest(params)
    final_plan = row_coupon_final_print_piece_plan(params)

    source_rows = {
        spec.name: {
            "installed_part": spec.installed_part,
            "role": manifest[spec.name]["role"],
            "source_class": (
                "rigid_source"
                if manifest[spec.name]["fabrication_source"] == "printed_polymer"
                else "compliant_source"
            ),
        }
        for spec in specs
    }
    body_rows = {
        str(row["name"]): {
            "source_artifact_id": str(row["source_artifact"]),
            "body_class": "rigid_print_piece",
        }
        for row in final_plan
    }
    for source_id, source in source_rows.items():
        if source["source_class"] == "compliant_source":
            body_rows[source_id] = {
                "source_artifact_id": source_id,
                "body_class": "compliant_body",
            }
    return {
        "sources": source_rows,
        "bodies": body_rows,
        "installed_parts": set(row_coupon_part_manifest()["installed"]),
    }


def _validate_registry(
    registry: dict[str, Any],
    live: dict[str, Any],
    *,
    verify_hashes: bool,
) -> None:
    assert set(registry) == TOP_LEVEL_KEYS
    assert registry["schema_version"] == 2
    assert "plate position" in registry["identity_authority"]["forbidden_inference"]

    sources = registry["canonical_sources"]
    bodies = registry["release_bodies"]
    source_ids = [row["source_artifact_id"] for row in sources]
    body_ids = [row["release_body_id"] for row in bodies]
    assert len(source_ids) == len(set(source_ids))
    assert len(body_ids) == len(set(body_ids))
    assert set(source_ids) == set(live["sources"])
    assert set(body_ids) == set(live["bodies"])

    source_classes = Counter(row["source_class"] for row in sources)
    body_classes = Counter(row["body_class"] for row in bodies)
    assert source_classes == {"rigid_source": 30, "compliant_source": 8}
    assert body_classes == {"rigid_print_piece": 38, "compliant_body": 8}
    assert registry["counts"] == {
        "canonical_sources": 38,
        "rigid_sources": 30,
        "compliant_sources": 8,
        "release_bodies": 46,
        "rigid_print_pieces": 38,
        "compliant_bodies": 8,
    }

    bodies_by_source: defaultdict[str, list[str]] = defaultdict(list)
    for body in bodies:
        assert set(body) == BODY_KEYS
        body_id = body["release_body_id"]
        expected = live["bodies"][body_id]
        assert body["source_artifact_id"] == expected["source_artifact_id"]
        assert body["body_class"] == expected["body_class"]
        assert body["authority_inherited_from_source"] == body["source_artifact_id"]
        assert set(body["outputs"]) == {"stl", "step"}
        bodies_by_source[body["source_artifact_id"]].append(body_id)
        for extension, output in body["outputs"].items():
            assert set(output) == OUTPUT_KEYS
            path = ROOT / output["path"]
            assert path.suffix == f".{extension}"
            assert path.is_file()
            assert body_id in path.stem
            if verify_hashes:
                assert hashlib.sha256(path.read_bytes()).hexdigest() == output["sha256"]

    for source in sources:
        assert set(source) == SOURCE_KEYS
        source_id = source["source_artifact_id"]
        expected = live["sources"][source_id]
        assert source["source_class"] == expected["source_class"]
        assert source["installed_part"] == expected["installed_part"]
        assert source["role"] == expected["role"]
        assert source["release_body_ids"] == bodies_by_source[source_id]
        assert source["mates"]
        assert all(
            mate in live["installed_parts"] or mate.startswith("external:")
            for mate in source["mates"]
        )
        assert set(source["evidence"]) == EVIDENCE_KEYS
        assert source["evidence"]["owner"] == "human_operator"
        assert source["evidence"]["status"] == "pending"
        assert source["evidence"]["gate"] in source["evidence"]["required_gates"]
        assert source["geometry_state"].startswith(
            ("pending_", "blocked_", "modeled_", "digitally_resolved_")
        )
        assert source["material_status"].startswith(("pending_", "blocked_"))
        assert source["current_slice_material"] != source["approved_operating_material"]
        assert source["approved_operating_material"] is None

        if source["source_class"] == "rigid_source":
            assert source["current_slice_material"] == "elegoo_pla"
        else:
            assert source["current_slice_material"] == "not_in_current_pla_slice_queue"
            assert source["material_status"] == "pending_compliant_material_specification"

        if source["installed_part"] == "printed_wedge_locks":
            assert source["current_slice_material"] == "elegoo_pla"
            assert source["approved_operating_material"] is None
            assert source["material_status"] == "blocked_pla_not_operating_approved"

    defect_statuses = {row["defect_id"]: row["status"] for row in registry["known_defects"]}
    assert defect_statuses == {
        "lid_cover_shell_installed_overlap": "digitally_resolved_physical_gate_pending",
        "lid_tongue_support_dependency": "blocked",
        "unretained_plain_butt_splits": "digitally_corrected_physical_gate_pending",
        "service_install_removal_clearance": "pending",
        "wedge_pla_operating_material": "blocked",
        "compliant_material_specification": "pending",
    }
    assert "pass" not in defect_statuses.values()


def test_artifact_authority_matches_both_live_namespaces_and_outputs(
    live_authority: dict[str, Any],
) -> None:
    registry = json.loads(REGISTRY.read_text())
    _validate_registry(registry, live_authority, verify_hashes=True)


def test_artifact_authority_fails_closed_on_unknown_duplicate_or_plate_identity(
    live_authority: dict[str, Any],
) -> None:
    registry = json.loads(REGISTRY.read_text())

    unknown = copy.deepcopy(registry)
    unknown["canonical_sources"][0]["source_artifact_id"] = "unknown_source"
    with pytest.raises(AssertionError):
        _validate_registry(unknown, live_authority, verify_hashes=False)

    duplicate = copy.deepcopy(registry)
    duplicate["release_bodies"][1]["release_body_id"] = duplicate["release_bodies"][0][
        "release_body_id"
    ]
    with pytest.raises(AssertionError):
        _validate_registry(duplicate, live_authority, verify_hashes=False)

    inferred_plate_identity = copy.deepcopy(registry)
    inferred_plate_identity["release_bodies"][0]["plate_id"] = "plate_05_object_02"
    with pytest.raises(AssertionError):
        _validate_registry(inferred_plate_identity, live_authority, verify_hashes=False)
