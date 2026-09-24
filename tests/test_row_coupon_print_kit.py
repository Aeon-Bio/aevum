"""Contracts the Print Kit viewer bundle relies on (scripts/build_row_coupon_print_kit.py)."""

from __future__ import annotations

import base64
import json

import cadquery as cq
import numpy as np
import pytest

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon.assembly import build_row_coupon_installed_parts
from aevum_cad.row_coupon.print_kit import (
    COTS_PART_CLASSES,
    PART_CLASSES,
    GltfWriter,
    Mesh,
    PlacedBody,
    classify_parts,
    install_states,
    load_part_options,
    plate_origin,
    release_body_to_installed_part,
    tessellate,
    verify_package,
)

REGISTRY = json.loads((ROOT / "docs" / "assembly" / "artifact_authority.json").read_text())
SEQUENCE = json.loads((ROOT / "docs" / "assembly" / "sequence_and_split_matrix.json").read_text())


@pytest.fixture(scope="module")
def installed_names() -> list[str]:
    return list(
        build_row_coupon_installed_parts(load_params(ROOT / "cad" / "one_row_coupon.params.json"))
    )


def test_every_installed_part_has_exactly_one_class_and_a_colour(installed_names):
    classes = classify_parts(installed_names, REGISTRY)
    assert set(classes) == set(installed_names)
    assert set(classes.values()) <= set(PART_CLASSES)
    rigid = {
        s["installed_part"]
        for s in REGISTRY["canonical_sources"]
        if s["source_class"] == "rigid_source"
    }
    assert {n for n, c in classes.items() if c == "printed"} == rigid
    options = load_part_options(ROOT / "cad" / "view_one_row_coupon.py")
    assert not set(installed_names) - set(options)


def test_classification_fails_closed(installed_names):
    with pytest.raises(ValueError, match="has no class"):
        classify_parts([*installed_names, "unregistered_widget"], REGISTRY)
    with pytest.raises(ValueError, match="no longer installs"):
        classify_parts([n for n in installed_names if n != next(iter(COTS_PART_CLASSES))], REGISTRY)


def test_every_installed_part_has_an_assembly_state(installed_names):
    states = install_states(SEQUENCE)
    assert not set(installed_names) - set(states)


def test_every_rigid_release_body_maps_to_an_installed_printed_part(installed_names):
    part_of = release_body_to_installed_part(REGISTRY)
    rigid_bodies = [
        rb for rb in REGISTRY["release_bodies"] if rb["body_class"] == "rigid_print_piece"
    ]
    assert len(part_of) == len(rigid_bodies) == REGISTRY["counts"]["rigid_print_pieces"]
    assert set(part_of.values()) <= set(installed_names)


def test_placement_rotates_ccw_then_lands_min_corner():
    box = tessellate(cq.Workplane("XY").box(40, 10, 5, centered=False), 0.1, 0.5)
    placed = box.transformed(90, (100.0, 20.0, 0.0))
    x0, y0, z0, x1, y1, z1 = placed.bbox
    assert (x0, y0, z0) == pytest.approx((100.0, 20.0, 0.0), abs=1e-9)
    assert (x1 - x0, y1 - y0, z1 - z0) == pytest.approx((10.0, 40.0, 5.0), abs=1e-9)
    # CCW: the box's +X end (x=40) swings to +Y, so the original origin corner ends at max x.
    corner = placed.positions[np.argmin(np.linalg.norm(box.positions, axis=1))]
    assert corner[:2] == pytest.approx((110.0, 20.0), abs=1e-9)


def test_plate_grid_wraps_every_four_beds():
    assert plate_origin(0, 250, 210) == (0.0, 0.0)
    assert plate_origin(3, 250, 210) == (3 * 290.0, 0.0)
    assert plate_origin(4, 250, 210) == (0.0, -250.0)


def test_stale_package_is_reported():
    body = PlacedBody("a", 0, 0, 0.0, 0.0, "hold", "sha-old", None, False)
    package = {"bodies": [body]}
    assert verify_package(package, {"a": "sha-old"}) == []
    assert verify_package(package, {"a": "sha-new"}) == ["a"]
    assert verify_package(package, {"a": "sha-old", "b": "x"})[0].startswith("body set differs")


def test_gltf_matches_the_viewer_reader():
    mesh = Mesh(
        np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], float),
        np.array([[0, 1, 2]]),
        np.array([[0, 0, 0], [1, 0, 0]], float),
        np.array([[0, 1]]),
    )
    w = GltfWriter("t")
    w.add("tri", mesh, (1.0, 0.5, 0.0, 0.4))
    doc = w.to_json()
    buf = base64.b64decode(doc["buffers"][0]["uri"].split(",", 1)[1])
    assert len(buf) == doc["buffers"][0]["byteLength"]
    prims = doc["meshes"][0]["primitives"]
    assert [p["mode"] for p in prims] == [4, 1]
    for p in prims:
        for acc in (doc["accessors"][p["attributes"]["POSITION"]], doc["accessors"][p["indices"]]):
            assert acc["componentType"] in (5126, 5125)
            view = doc["bufferViews"][acc["bufferView"]]
            assert view["byteOffset"] % 4 == 0 and view["byteOffset"] + view["byteLength"] <= len(
                buf
            )
    assert doc["materials"][0]["alphaMode"] == "BLEND"
