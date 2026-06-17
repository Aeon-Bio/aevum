from __future__ import annotations

from aevum_cad.fixture_model import (
    _fixture_layout,
    _plate_cap_bounds,
    build_fixture,
    build_mat_cassette,
    build_plate_cap,
)
from aevum_cad.labware import build_labware_definition
from aevum_cad.params import load_params, well_center


def test_fixture_top_dimension_matches_params() -> None:
    params = load_params()
    definition = build_labware_definition(params)

    expected_top = (
        params["raised_stack"]["height_to_mock_plate_top"]
        + params["mat_plane"]["height_above_mock_plate_top"]
        + params["mat_plane"]["frame_thickness"]
    )

    assert definition["dimensions"]["zDimension"] == expected_top


def test_a1_center_matches_labware_definition() -> None:
    params = load_params()
    definition = build_labware_definition(params)
    x, y = well_center(params, 0, 0)

    assert definition["wells"]["A1"]["x"] == x
    assert definition["wells"]["A1"]["y"] == y


def test_4_by_4_well_field_is_generated() -> None:
    params = load_params()
    definition = build_labware_definition(params)

    assert len(definition["wells"]) == 16
    assert "A1" in definition["wells"]
    assert "D4" in definition["wells"]


def test_labware_volume_units_match_robot_schema() -> None:
    params = load_params()
    definition = build_labware_definition(params)

    assert definition["metadata"]["displayVolumeUnits"] == "\u00b5L"


def test_well_pitch_is_9mm() -> None:
    params = load_params()
    x_a1, y_a1 = well_center(params, 0, 0)
    x_a2, y_a2 = well_center(params, 0, 1)
    x_b1, y_b1 = well_center(params, 1, 0)

    assert x_a2 - x_a1 == 9.0
    assert y_a2 == y_a1
    assert x_b1 == x_a1
    assert y_b1 - y_a1 == 9.0


def test_readable_mock_well_depth_matches_plate_stack() -> None:
    params = load_params()
    wells = params["mock_wells"]

    expected_depth = wells["plate_height_z"] - wells["bottom_height"] - wells["coverslip_thickness"]

    assert wells["depth"] == round(expected_depth, 2)
    assert wells["plate_top_to_cell_plane_depth_mm"] == round(expected_depth, 2)


def test_cellvis_well_geometry_uses_dimension_diagram_values() -> None:
    params = load_params()
    wells = params["mock_wells"]
    definition = build_labware_definition(params)

    assert wells["plate_catalog_number"] == "P96-1.5H-N"
    assert wells["upper_diameter_mm"] == 6.8
    assert wells["lower_diameter_mm"] == 6.21
    assert wells["diameter"] == wells["upper_diameter_mm"]
    assert wells["area_equivalent_diameter_mm"] == 6.18
    assert wells["diagram_internal_depth_mm"] == 11.93
    assert wells["well_top_recess_depth_mm"] == round(
        wells["plate_top_to_cell_plane_depth_mm"] - wells["diagram_internal_depth_mm"],
        2,
    )
    assert definition["wells"]["A1"]["diameter"] == wells["upper_diameter_mm"]


def test_mat_target_is_round_cole_parmer_part() -> None:
    params = load_params()
    mat = params["mat_plane"]

    assert mat["mat_vendor"] == "Cole-Parmer"
    assert mat["mat_catalog_number"] == "EW-12920-06"
    assert mat["source_well_shape"] == "Round, deep"
    assert mat["source_pre_slit"] is True


def test_p300_first_guide_holes_are_not_tight_bushings() -> None:
    params = load_params()

    assert params["mat_plane"]["guide_hole_diameter"] == 4.0
    assert params["mat_plane"]["guide_hole_diameter_by_row"] == [3.0, 3.5, 4.0, 4.5]
    assert params["print_qc"]["guide_hole_test_diameters"] == [3.0, 3.5, 4.0, 4.5]


def test_target_port_offset_is_part_of_offset_sweep() -> None:
    params = load_params()
    strategy = params["pipette_offset_strategy"]
    offsets = {(item["name"], item["x"], item["y"]) for item in params["pipette_offsets"]}

    assert strategy["target_offset_name"] == "x_1p5"
    assert (
        strategy["target_offset_name"],
        strategy["target_offset_x"],
        strategy["target_offset_y"],
    ) in offsets


def test_fixture_exports_as_one_connected_solid() -> None:
    params = load_params()
    model = build_fixture(params).val()

    assert len(model.Solids()) == 1


def test_first_print_uses_separate_mat_cassette() -> None:
    params = load_params()

    assert params["mat_plane"]["guide_style"] == "separate_cassette"
    assert params["plate_cap"]["part_style"] == "separate_cap"
    assert params["plate_cap"]["carries_mat_cassette_posts"] is True
    assert params["base"]["adhesion_tabs_enabled"] is False


def test_base_stops_at_plate_cap_locator_height() -> None:
    params = load_params()
    model = build_fixture(params).val()
    bb = model.BoundingBox()

    expected_z = (
        params["raised_stack"]["height_to_mock_plate_top"]
        - params["mock_wells"]["plate_height_z"]
        + params["plate_cap"]["locator_pin_height"]
    )

    assert round(bb.zlen, 2) == round(expected_z, 2)


def test_base_qc_hole_coupon_stays_exposed_after_plate_cap_install() -> None:
    params = load_params()
    print_qc = params["print_qc"]
    cap_x, cap_y, cap_len, cap_wid = _plate_cap_bounds(params, _fixture_layout(params))
    cap_max_x = cap_x + cap_len
    cap_max_y = cap_y + cap_wid
    max_r = max(print_qc["guide_hole_test_diameters"]) / 2
    hole_x = print_qc["guide_hole_test_x"]

    for idx, _diameter in enumerate(print_qc["guide_hole_test_diameters"]):
        hole_y = print_qc["guide_hole_test_y"] + idx * print_qc["guide_hole_test_spacing"]
        outside_cap = (
            hole_x - max_r > cap_max_x
            or hole_x + max_r < cap_x
            or hole_y - max_r > cap_max_y
            or hole_y + max_r < cap_y
        )
        assert outside_cap


def test_base_fiducials_stay_exposed_after_plate_cap_install() -> None:
    params = load_params()
    cap_x, cap_y, cap_len, cap_wid = _plate_cap_bounds(params, _fixture_layout(params))
    cap_max_x = cap_x + cap_len
    cap_max_y = cap_y + cap_wid

    def outside_cap(x: float, y: float) -> bool:
        return x > cap_max_x or x < cap_x or y > cap_max_y or y < cap_y

    for fid in params["fiducials"]:
        assert outside_cap(fid["x"], fid["y"])


def test_first_physical_fixture_uses_integrated_coarse_labels() -> None:
    params = load_params()
    labels = params["integrated_labels"]
    base = build_fixture(params).val().BoundingBox()
    plate_cap = build_plate_cap(params).val().BoundingBox()
    cassette = build_mat_cassette(params).val().BoundingBox()

    assert "labels" not in params
    assert labels["enabled"] is True
    assert labels["cut_depth"] >= 0.4
    assert labels["base_front_text"] == "FRONT SLOT 1"
    assert labels["plate_front_text"] == "PLATE A1"
    assert labels["plate_front_inverted_for_install"] is True
    assert "cassette_back_text" not in labels
    assert "cassette_font_size" not in labels
    assert labels["axis_arrows_enabled"] is True
    assert labels["axis_origin_x"] == 11.0
    assert labels["axis_origin_y"] == 11.0
    assert round(base.zlen, 2) == 67.7
    assert round(plate_cap.zlen, 2) == 25.3
    assert round(cassette.zlen, 2) == 3.0


def test_plate_cap_exports_as_one_connected_solid() -> None:
    params = load_params()
    model = build_plate_cap(params).val()

    assert len(model.Solids()) == 1


def test_plate_cap_carries_mat_cassette_envelope() -> None:
    params = load_params()
    model = build_plate_cap(params).val()
    bb = model.BoundingBox()

    expected_z = (
        params["mock_wells"]["plate_height_z"]
        + params["mat_plane"]["height_above_mock_plate_top"]
        + params["mat_plane"]["frame_thickness"]
    )

    assert round(bb.zlen, 2) == round(expected_z, 2)


def test_mat_cassette_exports_as_one_connected_solid() -> None:
    params = load_params()
    model = build_mat_cassette(params).val()

    assert len(model.Solids()) == 1


def test_deprecated_microtext_params_are_removed() -> None:
    params = load_params()
    mat = params["mat_plane"]
    deprecated_mat_keys = {
        "offset_labels_enabled",
        "offset_label_y",
        "offset_label_font_size",
        "offset_label_height",
        "diameter_labels_enabled",
        "diameter_label_font_size",
        "diameter_label_height",
    }

    assert "labels" not in params
    assert deprecated_mat_keys.isdisjoint(mat)


def test_base_fixture_geometric_evidence_features_are_enabled() -> None:
    params = load_params()

    assert params["print_qc"]["enabled"] is True
    assert params["inverted_bay"]["enabled"] is True
    assert len(params["fiducials"]) == 2


def test_inverted_bay_uses_separate_plate_cap() -> None:
    params = load_params()
    bay = params["inverted_bay"]

    assert bay["support_style"] == "separate_plate_cap"
    assert params["plate_cap"]["support_post_width"] > 0
    assert params["plate_cap"]["locator_pin_clearance"] > 0
