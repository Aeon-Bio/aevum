from __future__ import annotations

import json
from pathlib import Path

import pytest

from aevum_cad.params import load_params
from aevum_cad.row_coupon import (
    build_lid_manifold_shell,
    build_lower_gasket,
    build_plate_support_frame,
    build_upper_gasket,
    build_wet_chamber_frame,
    row_coupon_layout,
)

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
CONTRACT = ROOT / "docs" / "assembly" / "wet_seal_stack.json"
VOLUME_EPSILON_MM3 = 1e-6


def _volume(model) -> float:
    return float(model.val().Volume())


def test_gaskets_are_continuous_and_seated_in_opposed_capture_grooves() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    production = params["production_assembly"]
    seal = params["seal_interface"]
    contract = json.loads(CONTRACT.read_text())

    rail_height = float(seal["compressed_gasket_height_z"])
    outer_land = float(production["gasket_capture_outer_land_xy"])
    clearance = float(production["gasket_capture_clearance_xy"])
    expected_inset = outer_land + clearance / 2
    expected_rail_width = float(seal["gasket_rail_width"]) - outer_land

    lower = build_lower_gasket(params, assembly_position=True)
    upper = build_upper_gasket(params, assembly_position=True)
    lower_bb = lower.val().BoundingBox()
    upper_bb = upper.val().BoundingBox()

    assert len(lower.solids().vals()) == 1
    assert len(upper.solids().vals()) == 1
    assert lower_bb.zmin == pytest.approx(layout["base_top_z"] - rail_height / 2)
    assert lower_bb.zmax == pytest.approx(layout["base_top_z"] + rail_height / 2)
    assert upper_bb.zmin == pytest.approx(layout["gasket_bottom_z"])
    assert upper_bb.zmax == pytest.approx(layout["lid_bottom_z"])
    assert lower_bb.xmin == pytest.approx(expected_inset)
    assert lower_bb.xmax == pytest.approx(layout["length_x"] - expected_inset)
    assert lower_bb.ymin == pytest.approx(expected_inset)
    assert lower_bb.ymax == pytest.approx(layout["width_y"] - expected_inset)
    assert contract["nominal_geometry"]["gasket_perimeter_inset_mm"] == pytest.approx(
        expected_inset
    )
    assert contract["nominal_geometry"]["captured_gasket_rail_width_mm"] == pytest.approx(
        expected_rail_width
    )
    assert float(production["gasket_capture_depth_z"]) * 2 >= rail_height


def test_nominal_wet_stack_has_no_forbidden_rigid_gasket_intersection() -> None:
    params = load_params(PARAMS)
    lower = build_lower_gasket(params, assembly_position=True)
    upper = build_upper_gasket(params, assembly_position=True)
    support = build_plate_support_frame(params)
    wet_frame = build_wet_chamber_frame(params, assembly_position=True)
    shell = build_lid_manifold_shell(params, assembly_position=True)

    intersections = {
        "lower_gasket::plate_support_frame": _volume(lower.intersect(support)),
        "lower_gasket::wet_chamber_frame": _volume(lower.intersect(wet_frame)),
        "upper_gasket::wet_chamber_frame": _volume(upper.intersect(wet_frame)),
        "upper_gasket::lid_manifold_shell": _volume(upper.intersect(shell)),
    }
    assert intersections == pytest.approx(
        {name: 0.0 for name in intersections}, abs=VOLUME_EPSILON_MM3
    )


def test_drainage_witnesses_and_compression_screen_remain_fail_closed() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    contract = json.loads(CONTRACT.read_text())
    budget = layout["latch_compression_budget"]

    assert budget["passes_budget"] is True
    assert budget["gasket_squeeze_min_z"] <= budget["bounded_squeeze_z"]
    assert budget["bounded_squeeze_z"] <= budget["gasket_squeeze_max_z"]
    assert len(layout["condensation_pocket_rects"]) == 4
    assert len(layout["wet_dry_failure_paths"]["wet_dry_witness_gutters"]) == 8
    assert len(layout["gasket_tab_leak_witnesses"]) == 4

    authority = contract["material_and_physical_authority"]
    assert authority["pla_allowed_for_operating_gaskets"] is False
    assert authority["operating_gasket_material"] == "unresolved"
    assert authority["requires_d2_physical_evidence"] is True
    assert {
        "leak_tight",
        "pressure_tight",
        "compression_set_acceptable",
        "chemical_compatibility_acceptable",
        "cleaning_protocol_acceptable",
        "wet_operation_ready",
    } == set(authority["blocked_claims"])
