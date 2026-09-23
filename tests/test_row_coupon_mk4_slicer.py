from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zipfile
from collections import Counter
from itertools import combinations
from pathlib import Path
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_row_coupon_mk4_elegoo_pla_projects.py"
PACKAGE = ROOT / "outputs" / "sliced" / "mk4_elegoo_pla"
AUTHORITY = ROOT / "docs" / "assembly" / "artifact_authority.json"
LEDGER = ROOT / "docs" / "assembly" / "printability_ledger.json"


def _module():
    spec = importlib.util.spec_from_file_location("aevum_mk4_projects", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _project_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("Metadata/Slic3r_PE_model.config"))
    return [
        next(
            node.attrib["value"]
            for node in obj.findall("metadata")
            if node.attrib.get("key") == "name"
        )
        for obj in root.findall("object")
    ]


def _profile_settings(path: Path) -> dict[str, str]:
    settings: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if " = " in line and not line.startswith(("#", ";")):
            key, value = line.split(" = ", 1)
            settings[key] = value
    return settings


def _rigid_authority() -> dict[str, dict]:
    authority = json.loads(AUTHORITY.read_text())
    return {
        row["release_body_id"]: row
        for row in authority["release_bodies"]
        if row["body_class"] == "rigid_print_piece"
    }


def _a2_dispositions() -> dict[str, str]:
    ledger = json.loads(LEDGER.read_text())
    return {row["release_body_id"]: row["disposition"] for row in ledger["bodies"]}


def test_plate_topology_is_twelve_and_isolates_incompatible_failure_domains() -> None:
    module = _module()
    body_ids = set(_rigid_authority())
    dispositions = _a2_dispositions()
    specs = module._plate_specs(body_ids, dispositions)

    assert len(specs) == 12
    assert Counter(name for plate in specs for name in plate.part_names) == Counter(
        {name: 1 for name in body_ids}
    )
    anchor_plates = specs[:8]
    print_now_pod_plate = specs[8]
    fine_plate = specs[9]
    relief_cap_plate = specs[10]
    lid_shroud_plate = specs[11]
    assert all(sum("_piece_" in name for name in plate.part_names) == 1 for plate in anchor_plates)
    assert fine_plate.profile == "fine_service"
    assert len(fine_plate.part_names) == 23
    assert all(
        name.startswith(("lower_harness_cover_", "lid_harness_cover_", "printed_"))
        for name in fine_plate.part_names
    )
    assert not any(name.startswith("deck_pod_") for name in fine_plate.part_names)
    assert "printed_sample_relief_cap" not in fine_plate.part_names
    assert relief_cap_plate.profile == "relief_cap_support_review"
    assert relief_cap_plate.part_names == ("printed_sample_relief_cap",)
    assert dispositions["printed_sample_relief_cap"] == "hold"
    assert lid_shroud_plate.profile == "coupon_support_review"
    assert len(lid_shroud_plate.part_names) == 2
    assert all(
        name.startswith("printed_lid_sensor_connector_shroud_")
        for name in lid_shroud_plate.part_names
    )
    assert all(
        dispositions[name] == "coupon-first" for name in lid_shroud_plate.part_names
    )
    assert set(print_now_pod_plate.part_names) == {"deck_pod_tile_2", "deck_pod_tile_4"}
    assert all(
        dispositions[name] == "print-now-test-article"
        for name in print_now_pod_plate.part_names
    )
    held_pods = {
        name
        for plate in anchor_plates
        for name in plate.part_names
        if name.startswith("deck_pod_")
    }
    assert held_pods == {"deck_pod_tile_1", "deck_pod_tile_3"}
    assert all(dispositions[name] == "hold" for name in held_pods)
    assert all(plate.profile == "structural" for plate in specs[:9])


def test_published_package_binds_authority_cad_3mf_bgcode_profiles_and_minimality() -> None:
    manifest_path = PACKAGE / "package_manifest.json"
    assert manifest_path.is_file(), "C2 package has not been published"
    manifest = json.loads(manifest_path.read_text())
    authority = _rigid_authority()

    assert manifest["schema_version"] == 1
    assert manifest["authority"]["manufacturing_evidence_only"] is True
    assert manifest["authority"]["operator_release_granted"] is False
    assert manifest["counts"] == {
        "plates": 12,
        "rigid_bodies": 38,
        "large_anchor_bodies": 8,
        "zero_support_fine_harness_service_bodies": 23,
        "relief_cap_support_review_bodies": 1,
        "coupon_support_review_bodies": 2,
    }
    assert manifest["minimality"]["plate_lower_bound"] == 12
    assert manifest["minimality"][
        "independent_print_now_pod_failure_domain_lower_bound"
    ] == 1
    assert manifest["minimality"]["isolated_relief_cap_support_review_lower_bound"] == 1
    assert manifest["minimality"]["isolated_coupon_shroud_support_review_lower_bound"] == 1
    assert len(manifest["minimality"]["pairwise_anchor_rotation_check"]) == 28
    assert not any(
        row["can_share_usable_bed"]
        for row in manifest["minimality"]["pairwise_anchor_rotation_check"]
    )

    seen: list[str] = []
    for plate in manifest["plates"]:
        project = ROOT / plate["artifacts"]["3mf"]["path"]
        bgcode = ROOT / plate["artifacts"]["bgcode"]["path"]
        profile = ROOT / plate["artifacts"]["profile_snapshot"]["path"]
        assert _sha256(project) == plate["artifacts"]["3mf"]["sha256"]
        assert _sha256(bgcode) == plate["artifacts"]["bgcode"]["sha256"]
        assert _sha256(profile) == plate["artifacts"]["profile_snapshot"]["sha256"]
        assert bgcode.read_bytes()[:4] == b"GCDE"
        assert _project_names(project) == plate["body_ids"]
        assert plate["decoded_toolpath"]["decoded_body_count"] == len(plate["body_ids"])
        seen.extend(plate["body_ids"])
        margin = plate["bed_margin_mm"]
        for obj in plate["objects"]:
            body_id = obj["release_body_id"]
            assert obj["source_artifact_id"] == authority[body_id]["source_artifact_id"]
            assert obj["identity_chain"]["authority_release_body_id"] == body_id
            assert obj["identity_chain"]["3mf_object_name"] == body_id
            assert obj["identity_chain"]["m486_name_match"] in {
                "exact",
                "truncated_prefix",
            }
            assert obj["identity_chain"]["stl_sha256"] == authority[body_id]["outputs"][
                "stl"
            ]["sha256"]
            assert obj["identity_chain"]["step_sha256"] == authority[body_id]["outputs"][
                "step"
            ]["sha256"]
            assert obj["identity_chain"]["bgcode_sha256"] == _sha256(bgcode)
            decoded = obj["decoded_toolpath"]
            assert decoded["release_body_id"] == body_id
            assert decoded["object_ordinal"] == obj["object_ordinal"]
            assert decoded["decoded_total_positive_extrusion_mm"] > 0
            assert decoded["decoded_model_positive_extrusion_mm"] > 0
            assert decoded["first_model_layer_extrusion_mm"] > 0
            assert decoded["minimum_observed_model_extrusion_width_mm"] > 0
            orientation = obj["orientation"]
            assert orientation["rotation_x_deg"] == orientation["rotation_y_deg"] == 0
            assert orientation["rotation_z_deg"] in {0, 90}
            bounds = orientation["placed_bounds"]
            assert bounds["z_min_mm"] == pytest.approx(0.0, abs=1e-5)
            assert bounds["x_min_mm"] >= margin - 1e-5
            assert bounds["x_max_mm"] <= 250.0 - margin + 1e-5
            assert bounds["y_min_mm"] >= margin - 1e-5
            assert bounds["y_max_mm"] <= 210.0 - margin + 1e-5
        for first, second in combinations(plate["objects"], 2):
            a = first["orientation"]["placed_bounds"]
            b = second["orientation"]["placed_bounds"]
            x_gap = max(a["x_min_mm"] - b["x_max_mm"], b["x_min_mm"] - a["x_max_mm"])
            y_gap = max(a["y_min_mm"] - b["y_max_mm"], b["y_min_mm"] - a["y_max_mm"])
            assert max(x_gap, y_gap) >= plate["minimum_model_gap_mm"] - 1e-5

    assert Counter(seen) == Counter({body_id: 1 for body_id in authority})
    pod_plate = manifest["plates"][8]
    assert pod_plate["failure_domain"] == "print_now_deck_pod_test_articles_only"
    assert set(pod_plate["body_dispositions"]) == {"print-now-test-article"}
    assert pod_plate["decoded_toolpath"]["support_present"] is False
    fine = manifest["plates"][9]
    assert fine["failure_domain"] == "fine_harness_and_service_only"
    assert len(fine["body_ids"]) == 23
    assert fine["decoded_toolpath"]["support_present"] is False
    assert fine["decoded_toolpath"]["decoded_support_type_markers"] == 0
    fine_profile = _profile_settings(ROOT / fine["artifacts"]["profile_snapshot"]["path"])
    assert fine_profile["support_material"] == "0"
    assert float(fine_profile["brim_width"]) == 3.0
    assert float(fine_profile["layer_height"]) == 0.15
    relief = manifest["plates"][10]
    assert relief["failure_domain"] == "held_relief_cap_support_review_only"
    assert relief["body_ids"] == ["printed_sample_relief_cap"]
    assert relief["decoded_toolpath"]["support_present"] is True
    assert relief["decoded_toolpath"]["critical_surface_contact_status"] == (
        "physical_cleanup_mapping_pending"
    )
    shrouds = manifest["plates"][11]
    assert shrouds["failure_domain"] == (
        "coupon_first_lid_shrouds_support_review_only"
    )
    assert len(shrouds["body_ids"]) == 2
    assert set(shrouds["body_dispositions"]) == {"coupon-first"}
    assert shrouds["decoded_toolpath"]["support_present"] is True
