from __future__ import annotations

import copy
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "assembly" / "printability_ledger.json"
AUTHORITY = ROOT / "docs" / "assembly" / "artifact_authority.json"
PACKAGE = ROOT / "outputs" / "sliced" / "mk4_elegoo_pla"
DISPOSITION_RANK = {
    "print-now-test-article": 0,
    "coupon-first": 1,
    "hold": 2,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _project_body_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(
            archive.read("Metadata/Slic3r_PE_model.config")
        )
    return [
        next(
            metadata.attrib["value"]
            for metadata in obj.findall("metadata")
            if metadata.attrib.get("key") == "name"
        )
        for obj in root.findall("object")
    ]


def _project_settings(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        text = archive.read("Metadata/Slic3r_PE.config").decode()
    settings: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("; ") and " = " in line:
            key, value = line[2:].split(" = ", 1)
            settings[key] = value
    return settings


def _validate_ledger(ledger: dict[str, Any], *, verify_artifacts: bool) -> None:
    authority = json.loads(AUTHORITY.read_text())
    rigid = {
        body["release_body_id"]: body
        for body in authority["release_bodies"]
        if body["body_class"] == "rigid_print_piece"
    }
    sources = {
        source["source_artifact_id"]: source
        for source in authority["canonical_sources"]
    }

    assert ledger["schema_version"] == 2
    assert ledger["authority"]["manufacturing_evidence_only"] is True
    assert ledger["authority"]["prototype_acceptance_granted"] is False
    assert "plate position alone" in ledger["authority"]["body_identity"]
    assert ledger["supersession"]["status"] == "supersedes_prior_eight_plate_package"
    assert ledger["decoder_evidence"]["plaintext_outputs_retained"] is False
    assert len(ledger["decoder_evidence"]["decoder_executable_sha256"]) == 64
    assert set(ledger["policy"]["disposition_order"]) == set(DISPOSITION_RANK)
    assert ledger["policy"]["assembly_authorization"] == "Always false in this ledger."

    bodies = ledger["bodies"]
    plates = ledger["plates"]
    body_ids = [body["release_body_id"] for body in bodies]
    assert len(body_ids) == len(set(body_ids)) == 38
    assert set(body_ids) == set(rigid)
    assert len(plates) == 12
    assert sum(plate["decoded_body_count"] for plate in plates) == 38

    bodies_by_id = {body["release_body_id"]: body for body in bodies}
    seen_on_plates: list[str] = []
    for plate in plates:
        body_dispositions = [
            bodies_by_id[body_id]["disposition"] for body_id in plate["body_ids"]
        ]
        assert plate["body_dispositions"] == body_dispositions
        assert plate["decoded_body_count"] == len(plate["body_ids"])
        assert plate["mixed_body_plate"] is (len(plate["body_ids"]) > 1)
        assert plate["plate_disposition"] == max(
            body_dispositions, key=DISPOSITION_RANK.__getitem__
        )
        assert plate["strictest_body_policy_applied"] is True
        assert plate["whole_plate_print_authorized"] is False
        seen_on_plates.extend(plate["body_ids"])

        three_mf = ROOT / plate["artifacts"]["3mf"]["path"]
        bgcode = ROOT / plate["artifacts"]["bgcode"]["path"]
        profile = ROOT / plate["artifacts"]["profile_snapshot"]["path"]
        assert three_mf.is_file() and bgcode.is_file() and profile.is_file()
        assert _project_body_names(three_mf) == plate["body_ids"]
        assert bgcode.read_bytes()[:4] == b"GCDE"
        assert len(plate["artifacts"]["decoded_gcode_sha256"]) == 64
        if verify_artifacts:
            assert _sha256(three_mf) == plate["artifacts"]["3mf"]["sha256"]
            assert _sha256(bgcode) == plate["artifacts"]["bgcode"]["sha256"]
            assert _sha256(profile) == plate["artifacts"]["profile_snapshot"]["sha256"]

        settings = _project_settings(three_mf)
        expected = plate["slice_settings"]
        assert float(settings["layer_height"]) == expected["layer_height_mm"]
        assert int(settings["perimeters"]) == expected["perimeters"] == 3
        assert float(settings["fill_density"].rstrip("%")) == expected[
            "fill_density_percent"
        ]
        assert float(settings["brim_width"]) == expected["brim_width_mm"]
        support_enabled = plate["profile"] != "fine_service"
        assert settings["support_material"] == ("1" if support_enabled else "0")
        assert expected["support_material"] is support_enabled
        assert float(settings["max_print_speed"]) == expected[
            "max_print_speed_mm_s"
        ]

    assert Counter(seen_on_plates) == Counter({body_id: 1 for body_id in rigid})

    print_now_pods = plates[8]
    assert print_now_pods["failure_domain"] == "print_now_deck_pod_test_articles_only"
    assert set(print_now_pods["body_ids"]) == {"deck_pod_tile_2", "deck_pod_tile_4"}
    assert set(print_now_pods["body_dispositions"]) == {"print-now-test-article"}
    fine = plates[9]
    assert fine["failure_domain"] == "fine_harness_and_service_only"
    assert len(fine["body_ids"]) == 23
    assert fine["decoded_support_type_markers"] == 0
    relief = plates[10]
    assert relief["failure_domain"] == "held_relief_cap_support_review_only"
    assert relief["body_ids"] == ["printed_sample_relief_cap"]
    assert relief["decoded_support_type_markers"] > 0
    shrouds = plates[11]
    assert shrouds["failure_domain"] == (
        "coupon_first_lid_shrouds_support_review_only"
    )
    assert len(shrouds["body_ids"]) == 2
    assert set(shrouds["body_dispositions"]) == {"coupon-first"}
    assert shrouds["decoded_support_type_markers"] > 0

    for body in bodies:
        body_id = body["release_body_id"]
        expected = rigid[body_id]
        source = sources[body["source_artifact_id"]]
        assert body["source_artifact_id"] == expected["source_artifact_id"]
        assert body["identity_evidence"]["3mf_object_name"] == body_id
        m486_name = body["identity_evidence"]["bgcode_m486_name"]
        if body["identity_evidence"]["m486_name_match"] == "exact":
            assert m486_name == body_id
        else:
            assert body["identity_evidence"]["m486_name_match"] == "truncated_prefix"
            assert m486_name.endswith("...")
            assert body_id.startswith(m486_name[:-3])

        assert body["orientation"]["placed_z_min_mm"] == pytest.approx(0.0)
        assert body["first_layer_contact"]["status"] == (
            "direct_model_extrusion_at_first_layer"
        )
        assert body["first_layer_contact"]["first_model_layer_extrusion_mm"] > 0
        assert body["minimum_printed_feature"]["status"] == (
            "unresolved_width_proxy_only"
        )
        assert body["body_collisions"]["plate_xy_bbox_intersection"] is False
        assert body["artifact_completeness"]["complete"] is True
        assert body["artifact_completeness"]["positive_extrusion_present"] is True
        assert body["artifact_completeness"]["decoded_total_positive_extrusion_mm"] > 0
        assert body["artifact_completeness"]["canonical_stl_sha256"] == expected[
            "outputs"
        ]["stl"]["sha256"]
        assert body["artifact_completeness"]["canonical_step_sha256"] == expected[
            "outputs"
        ]["step"]["sha256"]
        assert body["geometry_likely_to_print"] is True
        assert body["assembly_authorized"] is False
        assert body["disposition"] in DISPOSITION_RANK
        assert body["disposition_reason"]

        supports = body["supports"]
        if supports["present"]:
            assert supports["support_extrusion_mm"] > 0
            assert supports["critical_surface_contact_status"].startswith("unresolved_")
            assert supports["cleanup_allowance"] == "none_documented"
            assert supports["blocker"] is True
            assert body["disposition"] != "print-now-test-article"
        else:
            assert supports["support_extrusion_mm"] == 0
            assert supports["blocker"] is False

        if source["geometry_state"].startswith("blocked_"):
            assert body["disposition"] == "hold"
        if source["installed_part"] == "printed_wedge_locks":
            assert source["material_status"] == "blocked_pla_not_operating_approved"
            assert body["disposition"] == "coupon-first"

    dispositions = Counter(body["disposition"] for body in bodies)
    assert dispositions == {
        "print-now-test-article": 2,
        "coupon-first": 17,
        "hold": 19,
    }
    assert ledger["counts"] == {
        "plates": 12,
        "rigid_bodies": 38,
        "decoded_bodies": 38,
        "print-now-test-article": 2,
        "coupon-first": 17,
        "hold": 19,
        "whole_plates_authorized": 0,
    }


def test_printability_ledger_matches_current_projects_and_toolpaths() -> None:
    ledger = json.loads(LEDGER.read_text())
    _validate_ledger(ledger, verify_artifacts=True)
    manifest = json.loads((PACKAGE / "package_manifest.json").read_text())
    snapshot = PACKAGE / "printability_ledger_snapshot.json"
    assert json.loads(snapshot.read_text()) == ledger
    assert _sha256(snapshot) == manifest["printability_ledger_snapshot"]["sha256"]
    decoded_report = ROOT / ledger["decoder_evidence"]["decoded_report"]
    assert _sha256(decoded_report) == ledger["decoder_evidence"][
        "decoded_report_sha256"
    ]


def test_printability_ledger_fails_closed_on_support_or_plate_downgrade() -> None:
    ledger = json.loads(LEDGER.read_text())

    supported = copy.deepcopy(ledger)
    supported_body = next(body for body in supported["bodies"] if body["supports"]["present"])
    supported_body["disposition"] = "print-now-test-article"
    with pytest.raises(AssertionError):
        _validate_ledger(supported, verify_artifacts=False)

    mixed = copy.deepcopy(ledger)
    mixed["plates"][2]["plate_disposition"] = "coupon-first"
    with pytest.raises(AssertionError):
        _validate_ledger(mixed, verify_artifacts=False)
