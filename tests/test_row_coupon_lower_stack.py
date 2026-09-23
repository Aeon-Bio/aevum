from __future__ import annotations

import copy
from pathlib import Path

import pytest

from aevum_cad.params import load_params
from aevum_cad.row_coupon import (
    _deck_engagement_foot_rectangles,
    _pod_frame_key_rectangles,
    build_deck_pods,
    build_ir_thermopiles,
    build_lower_gasket,
    build_lower_harness_cover,
    build_lower_sensor_harness,
    build_lower_sensor_service_connector,
    build_microplates,
    build_plate_support_frame,
    build_printed_lower_sensor_connector_shroud,
    row_coupon_layout,
)
from aevum_cad.row_coupon.parts.harness import (
    _lower_cover_hook_rectangles,
    _lower_cover_trunk,
    _lower_shroud_mount_rectangles,
)

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
EPSILON_MM3 = 1e-6

# A1 measurements that caused this node.  These are evidence, not acceptance
# tolerances: B1 must drive each forbidden installed overlap to zero.
BLOCKER_BASELINE_MM3 = {
    "deck_pods::lower_sensor_service_connector": 0.876404731,
    "deck_pods::printed_lower_sensor_connector_shroud": 11.599168475,
    "lower_harness_cover::lower_sensor_service_connector": 5.94312,
    "lower_harness_cover::printed_lower_sensor_connector_shroud": 3.848,
    "lower_gasket_service_tabs::plate_support_frame": 26.4,
}


@pytest.fixture(scope="module")
def params() -> dict:
    return load_params(PARAMS)


@pytest.fixture(scope="module")
def lower_stack(params: dict) -> dict:
    return {
        "deck_pods": build_deck_pods(params),
        "plate_support_frame": build_plate_support_frame(params),
        "microplates": build_microplates(params, assembly_position=True),
        "ir_thermopiles": build_ir_thermopiles(params, assembly_position=True),
        "lower_gasket": build_lower_gasket(params, assembly_position=True),
        "lower_harness_cover": build_lower_harness_cover(params, assembly_position=True),
        "lower_sensor_harness": build_lower_sensor_harness(params, assembly_position=True),
        "lower_sensor_service_connector": build_lower_sensor_service_connector(
            params, assembly_position=True
        ),
        "printed_lower_sensor_connector_shroud": (
            build_printed_lower_sensor_connector_shroud(params, assembly_position=True)
        ),
    }


def _intersection_mm3(left, right) -> float:
    return left.val().intersect(right.val()).Volume()


def test_measured_lower_stack_blockers_are_removed(lower_stack: dict) -> None:
    assert all(volume > EPSILON_MM3 for volume in BLOCKER_BASELINE_MM3.values())
    forbidden_pairs = (
        ("deck_pods", "plate_support_frame"),
        ("deck_pods", "lower_sensor_service_connector"),
        ("deck_pods", "printed_lower_sensor_connector_shroud"),
        ("lower_harness_cover", "lower_sensor_service_connector"),
        ("lower_harness_cover", "printed_lower_sensor_connector_shroud"),
        ("lower_harness_cover", "plate_support_frame"),
        ("printed_lower_sensor_connector_shroud", "plate_support_frame"),
        ("lower_gasket", "plate_support_frame"),
        ("ir_thermopiles", "plate_support_frame"),
    )
    for left, right in forbidden_pairs:
        assert _intersection_mm3(lower_stack[left], lower_stack[right]) <= EPSILON_MM3


def test_only_rear_service_foot_and_derived_key_move(params: dict) -> None:
    layout = row_coupon_layout(params)
    baseline = copy.deepcopy(params)
    baseline["deck_interface"]["lower_service_foot_inset_x"] = 0.0
    before_feet = _deck_engagement_foot_rectangles(
        tile_origins=layout["tile_origins"], params=baseline
    )
    after_feet = _deck_engagement_foot_rectangles(
        tile_origins=layout["tile_origins"], params=params
    )
    before_keys = _pod_frame_key_rectangles(
        tile_origins=layout["tile_origins"], params=baseline
    )
    after_keys = _pod_frame_key_rectangles(
        tile_origins=layout["tile_origins"], params=params
    )

    changed_feet = [
        (a, b) for a, b in zip(before_feet, after_feet, strict=True) if a != b
    ]
    changed_keys = [
        (a, b) for a, b in zip(before_keys, after_keys, strict=True) if a != b
    ]
    assert len(after_feet) == len(after_keys) == 16
    assert len(changed_feet) == len(changed_keys) == 1
    for before, after in (*changed_feet, *changed_keys):
        assert after["tile_index"] == params["row"]["plate_count"]
        assert after["x"] - before["x"] == pytest.approx(
            params["deck_interface"]["lower_service_foot_inset_x"]
        )
        assert after["y"] == before["y"]


def test_lower_cover_and_shroud_have_clear_serviceable_retention(
    params: dict, lower_stack: dict
) -> None:
    harness = params["sensor_harness"]
    layout = row_coupon_layout(params)
    trunk = _lower_cover_trunk(params)
    hooks = _lower_cover_hook_rectangles(params)
    lugs = _lower_shroud_mount_rectangles(params)
    shroud = layout["lower_ir_connector_envelope"]["printed_shroud"]
    key = layout["lower_ir_connector_envelope"]["key_rib_rect"]
    first_obstruction_y = min(float(shroud["y"]), float(shroud["y"]) - float(key["width_y"]))
    cover_edge_y = (
        float(trunk["y"])
        + float(trunk["width_y"])
        + float(harness["cover_overlap_xy"])
    )

    assert hooks and len(lugs) == 2
    assert min(hook["length_x"] for hook in hooks) >= 0.8
    assert min(hook["width_y"] for hook in hooks) >= 0.8
    assert min(lug["length_x"] for lug in lugs) >= 0.8
    assert min(lug["width_y"] for lug in lugs) >= 0.8
    assert first_obstruction_y - cover_edge_y == pytest.approx(
        harness["lower_connector_cover_clearance_y"]
    )
    rear_frame_ligament = (
        float(layout["width_y"])
        - float(shroud["y"])
        - float(shroud["width_y"])
        - float(harness["lower_shroud_mount_clearance_xy"])
    )
    assert rear_frame_ligament >= 2 * float(shroud["wall_xy"])
    assert lower_stack["lower_harness_cover"].val().Volume() == pytest.approx(
        1177.2445, abs=1e-4
    )
    # Whole-frame volume is deliberately not a golden: other lower-interface
    # pockets may be added independently.  The zero-overlap checks above bind
    # the functional delta without making unrelated frame work brittle.
    assert lower_stack["plate_support_frame"].val().Volume() > 300_000.0


def test_canonical_lower_shroud_includes_mount_lugs_and_cable_entry(
    params: dict,
) -> None:
    from aevum_cad.row_coupon.artifacts import build_row_coupon_physical_artifacts
    from aevum_cad.row_coupon.parts.harness import (
        build_lower_sensor_harness,
        build_printed_lower_sensor_connector_shroud,
    )

    canonical = build_row_coupon_physical_artifacts(
        params,
        assembly_position=True,
    )["printed_lower_sensor_connector_shroud"]
    public = build_printed_lower_sensor_connector_shroud(
        params,
        assembly_position=True,
    )
    assert canonical.val().Volume() == pytest.approx(public.val().Volume(), abs=1e-6)
    assert len(canonical.val().Solids()) == 1
    assert canonical.intersect(
        build_lower_sensor_harness(params, assembly_position=True)
    ).val().Volume() <= EPSILON_MM3


def test_lower_shroud_removes_downward_without_crossing_fixed_parts(
    params: dict,
    lower_stack: dict,
) -> None:
    shroud_spec = row_coupon_layout(params)["lower_ir_connector_envelope"]["printed_shroud"]
    assert shroud_spec["install_axis"] == "+Z_from_below_to_datum"
    assert shroud_spec["removal_axis"] == "-Z_then_+Y_connector_unmate"

    fixed = (
        lower_stack["lower_sensor_harness"],
        lower_stack["lower_sensor_service_connector"],
        lower_stack["plate_support_frame"],
        lower_stack["deck_pods"],
    )
    shroud = lower_stack["printed_lower_sensor_connector_shroud"]
    for offset_z in (0.0, -0.2, -0.5, -1.0, -2.0, -5.0, -8.0):
        moved = shroud.translate((0.0, 0.0, offset_z))
        assert all(_intersection_mm3(moved, body) <= EPSILON_MM3 for body in fixed)


def test_datum_and_full_ir_body_removal_paths_are_clear(lower_stack: dict) -> None:
    frame = lower_stack["plate_support_frame"].val()
    deck = lower_stack["deck_pods"].val()
    service_paths = {
        "microplates": (0.0, 2.0, 5.0, 12.0),
        # The thermopiles are installed from the dry underside.
        "ir_thermopiles": (0.0, -2.0, -5.0, -12.0),
    }
    for name, offsets in service_paths.items():
        body = lower_stack[name].val()
        for offset_z in offsets:
            moved = body.copy().translate((0.0, 0.0, offset_z))
            assert moved.intersect(frame).Volume() <= EPSILON_MM3
            assert moved.intersect(deck).Volume() <= EPSILON_MM3

    for release_z in (0.0, -0.5, -1.0, -2.0, -5.0):
        released_pods = deck.copy().translate((0.0, 0.0, release_z))
        assert released_pods.intersect(frame).Volume() <= EPSILON_MM3


def test_lower_cable_path_keeps_required_bend_and_exposed_tool_lane(
    params: dict, lower_stack: dict
) -> None:
    harness = params["sensor_harness"]
    assert harness["service_cable_bend_radius_y"] >= harness["min_bend_radius"]
    assert _intersection_mm3(
        lower_stack["lower_sensor_harness"], lower_stack["lower_harness_cover"]
    ) <= EPSILON_MM3
    assert _intersection_mm3(
        lower_stack["lower_sensor_harness"],
        lower_stack["lower_sensor_service_connector"],
    ) <= EPSILON_MM3


def test_lower_print_sources_retain_flat_supported_orientation(lower_stack: dict) -> None:
    for name in ("lower_harness_cover", "printed_lower_sensor_connector_shroud"):
        solid = lower_stack[name].val()
        bbox = solid.BoundingBox()
        horizontal_faces = [
            face
            for face in solid.Faces()
            if abs(face.normalAt().z) >= 0.999 and face.Area() >= 1.0
        ]
        assert bbox.zlen >= 0.7
        assert horizontal_faces
