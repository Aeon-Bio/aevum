"""The display-grade plates must agree with the authority proxy and the published profile."""

from __future__ import annotations

import math

import pytest

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon.layout import row_coupon_layout
from aevum_cad.row_coupon.parts.microplate_detail import (
    SLAS_384_COLUMNS,
    SLAS_384_ROWS,
    build_microplates_96_detailed,
    cell_plane_height,
    slas_384_footprints,
    slas_384_well_rings,
)
from aevum_cad.row_coupon.parts.structural import build_microplates

PARAMS = load_params(ROOT / "cad" / "one_row_coupon.params.json")


@pytest.fixture(scope="module")
def detailed():
    return build_microplates_96_detailed(PARAMS)


def test_detailed_plate_matches_the_proxy_envelope(detailed):
    a = detailed.val().BoundingBox()
    b = build_microplates(PARAMS, assembly_position=True).val().BoundingBox()
    for axis in ("xmin", "ymin", "zmin", "xmax", "ymax", "zmax"):
        assert getattr(a, axis) == pytest.approx(getattr(b, axis), abs=1e-6), axis


def test_detailed_plate_has_every_published_well(detailed):
    tiles = len(row_coupon_layout(PARAMS)["tile_origins"])
    grid = PARAMS["well_grid"]
    assert detailed.val().isValid()
    assert len(detailed.solids().vals()) == tiles
    cones = [f for f in detailed.faces().vals() if f.geomType() == "CONE"]
    assert len(cones) == tiles * grid["rows"] * grid["columns"]


def test_well_floor_is_the_published_cell_plane(detailed):
    plate = PARAMS["plate"]
    z0 = row_coupon_layout(PARAMS)["plate_bottom_z"]
    assert cell_plane_height(PARAMS) == pytest.approx(
        plate["height_z"] - plate["plate_top_to_cell_plane_depth_z"]
    )
    cone = next(f for f in detailed.faces().vals() if f.geomType() == "CONE")
    bb = cone.BoundingBox()
    assert bb.zmin == pytest.approx(z0 + cell_plane_height(PARAMS), abs=1e-6)
    assert bb.zmax - bb.zmin == pytest.approx(plate["diagram_internal_depth_z"], abs=1e-6)
    assert bb.xlen == pytest.approx(plate["upper_well_diameter"], abs=1e-3)


def test_384_placeholder_follows_the_slas_grid():
    tiles = len(row_coupon_layout(PARAMS)["tile_origins"])
    rings = slas_384_well_rings(PARAMS, segments=20)
    assert rings.shape == (tiles * SLAS_384_ROWS * SLAS_384_COLUMNS * 20, 2, 3)
    boxes = slas_384_footprints(PARAMS).val().BoundingBox()
    assert boxes.zlen == pytest.approx(14.35)
    # every ring centre sits inside a footprint
    centres = rings.reshape(-1, 20, 2, 3)[:, :, 0, :2].mean(axis=1)
    assert centres[:, 0].min() > boxes.xmin and centres[:, 0].max() < boxes.xmax
    assert math.isclose(boxes.xlen, 127.76, abs_tol=1e-6)
