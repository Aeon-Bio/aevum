from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pytest

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon.assembly_coupons import (
    ASSEMBLY_COUPON_FAMILY_IDS,
    MEASUREMENT_FIELDS,
    build_row_coupon_assembly_coupon_families,
    export_row_coupon_assembly_coupon_package,
    row_coupon_assembly_coupon_manifest,
)

PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
INTERFACES = ROOT / "docs" / "assembly" / "interface_matrix.json"
SEQUENCE = ROOT / "docs" / "assembly" / "sequence_and_split_matrix.json"


@pytest.fixture(scope="module")
def params() -> dict:
    return load_params(PARAMS)


@pytest.fixture(scope="module")
def manifest(params: dict) -> dict:
    return row_coupon_assembly_coupon_manifest(params)


@pytest.fixture(scope="module")
def coupon_models(params: dict) -> dict:
    return build_row_coupon_assembly_coupon_families(params)


def test_manifest_has_exact_eight_profile_scoped_families(manifest: dict) -> None:
    families = manifest["families"]
    assert tuple(family["family_id"] for family in families) == ASSEMBLY_COUPON_FAMILY_IDS
    assert len(families) == 8
    assert manifest["scope"] == {
        "printer_model": "Original Prusa MK4 Input Shaper 0.4 nozzle",
        "nozzle_diameter_mm": 0.4,
        "rigid_material": "Elegoo PLA",
        "rigid_profile": "0.15mm STRUCTURAL coupon profile",
        "transfer_rule": (
            "Results apply only to the recorded printer, nozzle, material product/lot, "
            "profile hash, orientation, and environmental conditioning."
        ),
    }
    policy = manifest["policy"]
    assert policy["coupon_results_are_final_artifact_acceptance"] is False
    assert policy["coupon_failure_blocks_represented_full_parts"] is True
    assert policy["coupon_pass_only_authorizes_next_full_part_gate"] is True
    assert policy["plain_seams_are_not_covered"] is True
    assert policy["unrecorded_profile_or_material_transfer_allowed"] is False
    assert all(family["coverage_mode"] == "screen_only_not_final_acceptance" for family in families)
    assert all(family["remaining_full_part_gate"] for family in families)


def test_ladders_are_physically_keyed_and_external_mates_are_explicit(
    manifest: dict,
) -> None:
    families = {family["family_id"]: family for family in manifest["families"]}
    for family_id in ASSEMBLY_COUPON_FAMILY_IDS[:-1]:
        stations = families[family_id]["stations"]
        assert [station["delta_mm"] for station in stations] == [-0.1, 0.0, 0.1]
        assert [station["physical_label_code"] for station in stations] == ["|", "||", "|||"]
        assert len({station["test_value_mm"] for station in stations}) == 3

    assert families["shroud_connector"]["required_external_mates"]
    assert families["gasket_land_compression"]["required_external_mates"]
    assert families["barb_tube"]["required_external_mates"]
    assert "build_lid_tongue_groove_coupon_pair" in families["lid_tongue_groove"]["builder_source"]
    assert "_keyed_split_pair" in families["structural_split_joint"]["builder_source"]
    assert "build_lid_latch_coupon_pair" in families["wedge_receiver"]["builder_source"]
    assert (
        "build_printability_support_cleanup_check" in families["support_cleanup"]["builder_source"]
    )
    assert "build_material_cleaning_witness_coupon" in families["support_cleanup"]["builder_source"]


def test_every_a1_interface_and_a3_split_or_service_path_is_fail_closed(
    manifest: dict,
) -> None:
    interface_matrix = json.loads(INTERFACES.read_text())
    sequence_matrix = json.loads(SEQUENCE.read_text())
    expected_interfaces = {row["interface_id"] for row in interface_matrix["interfaces"]}
    coverage = {row["interface_id"]: row for row in manifest["interface_coverage"]}
    assert set(coverage) == expected_interfaces
    assert all(
        row["mode"] in {"coupon_screen_plus_full_part_gate", "full_part_only"}
        and row["reason"]
        and row["evidence_owner"]
        for row in coverage.values()
    )
    assert all(
        row["coupon_family_id"] is None
        for row in coverage.values()
        if row["mode"] == "full_part_only"
    )

    split = {row["source_artifact_id"]: row for row in manifest["split_source_coverage"]}
    assert set(split) == {row["source_artifact_id"] for row in sequence_matrix["split_sources"]}
    assert all(row["coupon_family_id"] == "structural_split_joint" for row in split.values())
    assert all(row["remaining_gate"] for row in split.values())

    service = {row["path_id"]: row for row in manifest["service_path_coverage"]}
    assert set(service) == {row["path_id"] for row in sequence_matrix["service_paths"]}
    assert all(row["reason"] for row in service.values())
    assert service["gas_pcb_cartridge_vertical_service"]["mode"] == "full_part_only"
    assert service["sample_relief_cap_service"]["mode"] == "full_part_only"


def test_coupon_geometry_is_nonempty_and_split_coupon_has_no_plain_seam(
    coupon_models: dict,
) -> None:
    assert tuple(coupon_models) == ASSEMBLY_COUPON_FAMILY_IDS
    expected_counts = {
        "lid_tongue_groove": 6,
        "structural_split_joint": 6,
        "snap_keeper": 6,
        "wedge_receiver": 6,
        "shroud_connector": 3,
        "gasket_land_compression": 6,
        "barb_tube": 3,
        "support_cleanup": 2,
    }
    assert {family: len(models) for family, models in coupon_models.items()} == expected_counts
    for family_id, models in coupon_models.items():
        for name, model in models.items():
            value = model.val()
            assert value.Volume() > 0, (family_id, name)
            assert value.BoundingBox().xlen > 0, (family_id, name)
            assert value.BoundingBox().ylen > 0, (family_id, name)
            assert value.BoundingBox().zlen > 0, (family_id, name)
    assert all("plain" not in name for name in coupon_models["structural_split_joint"])


def test_export_writes_step_stl_3mf_manifest_and_measurement_form(
    params: dict, coupon_models: dict, tmp_path: Path
) -> None:
    profile = tmp_path / "coupon.ini"
    profile.write_text("layer_height = 0.15\nprinter_model = MK4IS\n")
    paths = export_row_coupon_assembly_coupon_package(
        params, tmp_path / "package", profile_path=profile
    )
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths.values())
    assert sum(key.endswith("_3mf") for key in paths) == 8

    exported_manifest = json.loads(paths["manifest"].read_text())
    assert exported_manifest["scope"]["profile_sha256"] != "UNSET_BLOCKS_PHYSICAL_TRANSFER"
    assert exported_manifest["policy"]["coupon_results_are_final_artifact_acceptance"] is False

    with paths["measurement_form"].open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert tuple(rows[0]) == MEASUREMENT_FIELDS
    assert len(rows) == 23
    assert {row["family_id"] for row in rows} == set(ASSEMBLY_COUPON_FAMILY_IDS)
    assert all(row["profile_name"] and row["material_product"] for row in rows)
    assert all(not row["coupon_result"] and not row["full_part_gate_result"] for row in rows)

    for family_id in ASSEMBLY_COUPON_FAMILY_IDS:
        project = paths[f"{family_id}_3mf"]
        with zipfile.ZipFile(project) as archive:
            assert "Metadata/aevum_coupon_scope.json" in archive.namelist()
            scope = json.loads(archive.read("Metadata/aevum_coupon_scope.json"))
            assert scope["family_id"] == family_id
            assert scope["final_artifact_acceptance"] is False
            model_xml = archive.read("3D/3dmodel.model")
            root = ElementTree.fromstring(model_xml)
            namespace = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
            assert root.findall("m:resources/m:object", namespace)
            assert len(root.findall("m:build/m:item", namespace)) == len(coupon_models[family_id])
