from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import cadquery as cq
import pytest

from aevum_cad.params import load_params
from aevum_cad.row_coupon import (
    _latch_mechanical_screens,
    _printed_wedge_lock_models,
    _wedge_lock_rectangles,
    build_lid_cover,
    build_lid_latch_coupon_pair,
    build_lid_manifold_shell,
    build_lid_tongue_groove_coupon_pair,
    build_lower_gasket,
    build_upper_gasket,
    build_wet_chamber_frame,
    row_coupon_layout,
)
from aevum_cad.row_coupon.final_print_pieces import (
    _final_print_piece_segments,
    _keyed_split_pair,
    _split_y_from_tile_origins,
)

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
EPSILON_MM3 = 1e-4


def _volume(shape: cq.Shape) -> float:
    return float(shape.Volume())


def _intersection(left: cq.Workplane, right: cq.Workplane) -> float:
    return _volume(left.val().intersect(right.val()))


@pytest.fixture(scope="module")
def params() -> dict:
    return load_params(PARAMS)


@pytest.fixture(scope="module")
def installed(params: dict) -> dict[str, cq.Workplane]:
    return {
        "cover": build_lid_cover(params, assembly_position=True),
        "shell": build_lid_manifold_shell(params, assembly_position=True),
        "wet": build_wet_chamber_frame(params, assembly_position=True),
        "upper": build_upper_gasket(params, assembly_position=True),
        "lower": build_lower_gasket(params, assembly_position=True),
    }


def test_lid_fit_has_declared_clearance_and_paired_coupon(
    params: dict,
    installed: dict[str, cq.Workplane],
) -> None:
    production = params["production_assembly"]
    assert production["lid_cover_tongue_clearance_xy"] == pytest.approx(0.25)
    assert production["lid_cover_tongue_clearance_z"] == pytest.approx(0.20)
    assert _intersection(installed["cover"], installed["shell"]) <= EPSILON_MM3

    assembled = build_lid_tongue_groove_coupon_pair(
        params,
        assembly_position=True,
    )
    bedded = build_lid_tongue_groove_coupon_pair(params)
    assert set(assembled) == {
        "lid_tongue_shell_coupon",
        "lid_groove_cover_coupon",
    }
    assert _intersection(*assembled.values()) <= EPSILON_MM3
    for body in bedded.values():
        assert len(body.val().Solids()) == 1
        assert body.val().BoundingBox().zmin == pytest.approx(0.0, abs=1e-6)


def test_all_twelve_wedges_clear_hard_geometry_and_classify_snap_lip(
    params: dict,
    installed: dict[str, cq.Workplane],
) -> None:
    layout = row_coupon_layout(params)
    rects = _wedge_lock_rectangles(layout, params)
    models = list(_printed_wedge_lock_models(params, assembly_position=True).values())
    assert len(rects) == len(models) == 12

    no_lip_params = deepcopy(params)
    no_lip_params["production_assembly"].update(
        {
            "wedge_receiver_lip_width_y": 0.0,
            "wedge_receiver_lip_height_z": 0.0,
        }
    )
    rigid_receiver = build_lid_cover(no_lip_params, assembly_position=True)
    for rect, model in zip(rects, models, strict=True):
        assert len(model.val().Solids()) == 1
        assert _intersection(model, installed["cover"]) <= EPSILON_MM3
        assert _intersection(model, installed["shell"]) <= EPSILON_MM3
        assert _intersection(model, installed["wet"]) <= EPSILON_MM3

        direction = -1.0 if rect["insert_from"] == "min" else 1.0
        travel = float(rect["length_x"])
        for offset in (0.0, travel / 2, travel + 1.0):
            moved = cq.Workplane(
                obj=model.val().moved(
                    cq.Location(cq.Vector(direction * offset, 0.0, 0.0))
                )
            )
            assert _intersection(moved, rigid_receiver) <= EPSILON_MM3
            assert _intersection(moved, installed["wet"]) <= EPSILON_MM3

    # The retained production sweep deliberately deflects the release lip; the
    # paired coupon is the physical gate for that compliant, cyclic interaction.
    latch_coupon = build_lid_latch_coupon_pair(params, assembly_position=True)
    assert _intersection(*latch_coupon.values()) <= EPSILON_MM3
    for body in build_lid_latch_coupon_pair(params).values():
        assert len(body.val().Solids()) == 1
        assert body.val().BoundingBox().zmin == pytest.approx(0.0, abs=1e-6)


def test_both_gasket_bands_remain_clear_of_wet_frame(
    installed: dict[str, cq.Workplane],
) -> None:
    assert _intersection(installed["lower"], installed["wet"]) <= EPSILON_MM3
    assert _intersection(installed["upper"], installed["wet"]) <= EPSILON_MM3
    assert _intersection(installed["upper"], installed["shell"]) <= EPSILON_MM3


def test_lid_sources_realize_keyed_split_without_renaming(params: dict) -> None:
    layout = row_coupon_layout(params)
    nominal_split_y = _split_y_from_tile_origins(layout["tile_origins"], params)
    segments = _final_print_piece_segments(params)
    interface = params["production_assembly"]["final_piece_interface"]
    expected_suffixes = [segment["suffix"] for segment in segments]

    for source_name, source in (
        ("lid_cover", build_lid_cover(params)),
        ("lid_manifold_shell", build_lid_manifold_shell(params)),
    ):
        source_interface = dict(interface)
        source_interface.update(interface["source_overrides"][source_name])
        source_interface.pop("source_overrides")
        source_interface["canonical_source_artifact"] = source_name
        split_y = float(source_interface.get("split_y_mm", nominal_split_y))
        lower, upper, proof = _keyed_split_pair(
            source,
            source_y_min=0.0,
            source_y_max=float(layout["width_y"]),
            split_y=split_y,
            interface=source_interface,
        )
        assert proof["mating_feature_kind"] == "printed_dovetail_key_and_pocket"
        assert proof["realized_key_count"] > 0
        assert proof["pair_interference_volume_mm3"] <= EPSILON_MM3
        assert len(lower.val().Solids()) == len(upper.val().Solids()) == 1
        assert [f"{source_name}_{suffix}" for suffix in expected_suffixes] == [
            f"{source_name}_piece_01_of_02_y_000p000_to_188p625",
            f"{source_name}_piece_02_of_02_y_188p625_to_377p250",
        ]


def test_realized_split_lid_and_shell_remain_clear_when_installed(params: dict) -> None:
    layout = row_coupon_layout(params)
    nominal_split_y = _split_y_from_tile_origins(layout["tile_origins"], params)
    interface = params["production_assembly"]["final_piece_interface"]
    realized: dict[str, cq.Workplane] = {}

    for source_name, source in (
        ("lid_cover", build_lid_cover(params, assembly_position=True)),
        (
            "lid_manifold_shell",
            build_lid_manifold_shell(params, assembly_position=True),
        ),
    ):
        source_interface = dict(interface)
        source_interface.update(interface["source_overrides"][source_name])
        source_interface.pop("source_overrides")
        source_interface["canonical_source_artifact"] = source_name
        split_y = float(source_interface.get("split_y_mm", nominal_split_y))
        lower, upper, _ = _keyed_split_pair(
            source,
            source_y_min=0.0,
            source_y_max=float(layout["width_y"]),
            split_y=split_y,
            interface=source_interface,
        )
        realized[source_name] = cq.Workplane(
            obj=cq.Compound.makeCompound([lower.val(), upper.val()])
        )

    assert _intersection(realized["lid_cover"], realized["lid_manifold_shell"]) <= (
        EPSILON_MM3
    )


def test_split_and_port_bypass_latches_restore_safe_symmetric_span(
    params: dict,
) -> None:
    layout = row_coupon_layout(params)
    rects = _wedge_lock_rectangles(layout, params)
    screen = _latch_mechanical_screens(
        layout,
        params=params,
        compression_stop_positions=layout["compression_stop_positions"],
        wedge_lock_rectangles=rects,
    )["station_asymmetry"]
    center_y = layout["width_y"] / 2
    split_y = params["production_assembly"]["final_piece_interface"][
        "source_overrides"
    ]["lid_cover"]["split_y_mm"]
    bypass = params["production_assembly"]["latch_center_station_bypass_offset_y"]
    positions = {(lock["post_x"], lock["post_y"]) for lock in rects}

    assert len(layout["compression_stop_positions"]) == 12
    assert len(rects) == 12
    assert all((x, center_y) not in positions for x in (7.1, 141.5))
    assert {
        (7.1, center_y - bypass),
        (7.1, center_y + bypass),
        (141.5, center_y - bypass),
        (141.5, center_y + bypass),
    } <= positions
    assert all(
        lock["y"] + lock["width_y"] < split_y or lock["y"] > split_y
        for lock in rects
    )
    assert min(
        min(
            abs(split_y - lock["y"]),
            abs(split_y - (lock["y"] + lock["width_y"])),
        )
        for lock in rects
    ) >= 8.0
    assert screen["omitted_station_count"] == 0
    assert screen["has_omitted_station_warning"] is False
    assert screen["max_active_station_span_mm"] == pytest.approx(77.125)
    assert screen["allowed_max_active_span_mm"] == pytest.approx(100.0)
    assert screen["exceeds_allowed_span"] is False
