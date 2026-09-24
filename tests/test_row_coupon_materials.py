"""Every printed part has exactly one print material, and split pieces inherit it."""

from __future__ import annotations

import json

import pytest

from aevum_cad.params import ROOT
from aevum_cad.row_coupon.materials import (
    MATERIALS,
    PART_MATERIALS,
    material_of,
    release_body_materials,
)

REGISTRY = json.loads((ROOT / "docs" / "assembly" / "artifact_authority.json").read_text())


def test_every_printed_part_has_a_known_material():
    printed = {
        s["installed_part"]
        for s in REGISTRY["canonical_sources"]
        if s["source_class"] == "rigid_source"
    }
    assert set(PART_MATERIALS) == printed
    for part, (material, reason) in PART_MATERIALS.items():
        assert material in MATERIALS, part
        assert len(reason) > 20, part


def test_split_pieces_inherit_their_parts_material():
    by_body = release_body_materials(REGISTRY)
    assert len(by_body) == REGISTRY["counts"]["rigid_print_pieces"]
    part_of_source = {
        s["source_artifact_id"]: s["installed_part"] for s in REGISTRY["canonical_sources"]
    }
    for rb in REGISTRY["release_bodies"]:
        if rb["body_class"] == "rigid_print_piece":
            part = part_of_source[rb["source_artifact_id"]]
            assert by_body[rb["release_body_id"]] == PART_MATERIALS[part][0]


def test_datum_parts_are_asa_and_snapping_parts_are_petg():
    assert material_of("plate_support_frame") == "ASA"
    assert material_of("deck_pods") == "ASA"
    for part in ("printed_wedge_locks", "lower_harness_cover", "lid_harness_cover"):
        assert material_of(part) == "PETG"


def test_unknown_part_fails_loudly():
    with pytest.raises(KeyError, match="PART_MATERIALS"):
        material_of("not_a_part")


def test_every_material_names_its_h2s_preset():
    for spec in MATERIALS.values():
        assert spec["bambu_filament"]["h2s"].startswith("Generic ")
