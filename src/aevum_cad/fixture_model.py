from __future__ import annotations

from pathlib import Path
from typing import Any

import cadquery as cq

from aevum_cad.params import well_center


def _rounded_box(length: float, width: float, height: float, radius: float) -> cq.Workplane:
    part = cq.Workplane("XY").box(length, width, height, centered=(False, False, False))
    if radius > 0:
        part = part.edges("|Z").fillet(radius)
    return part


def _fixture_layout(params: dict[str, Any]) -> dict[str, float]:
    stack = params["raised_stack"]
    wells = params["mock_wells"]
    mat = params["mat_plane"]
    base = params["base"]
    layout_params = params.get("layout", {})

    plate_top_z = stack["height_to_mock_plate_top"]
    mat_z = plate_top_z + mat["height_above_mock_plate_top"]
    plate_bottom_z = plate_top_z - wells["plate_height_z"]
    well_bottom_z = plate_bottom_z + wells["bottom_height"] + wells["coverslip_thickness"]
    well_depth = plate_top_z - well_bottom_z

    field_min_x = wells["a1_center_x"] - wells["pitch"] / 2
    field_min_y = wells["a1_center_y"] - wells["pitch"] / 2
    field_len_x = (wells["columns"] - 1) * wells["pitch"] + wells["pitch"]
    field_len_y = (wells["rows"] - 1) * wells["pitch"] + wells["pitch"]
    tower_margin = layout_params.get("tower_margin", 10.0)
    tower_x = field_min_x - tower_margin
    tower_y = field_min_y - tower_margin
    tower_len = field_len_x + 2 * tower_margin
    tower_wid = field_len_y + 2 * tower_margin

    if mat.get("use_plate_footprint", False):
        rail_outer_len = wells["plate_length_x"]
        rail_outer_wid = wells["plate_width_y"]
        rail_x = (base["length_x"] - rail_outer_len) / 2
        rail_y = (base["width_y"] - rail_outer_wid) / 2
    else:
        rail_margin = layout_params.get("rail_margin", 7.0)
        rail_outer_len = tower_len + 2 * rail_margin
        rail_outer_wid = tower_wid + 2 * rail_margin
        rail_x = tower_x - rail_margin
        rail_y = tower_y - rail_margin

    return {
        "plate_top_z": plate_top_z,
        "mat_z": mat_z,
        "plate_bottom_z": plate_bottom_z,
        "well_bottom_z": well_bottom_z,
        "well_depth": well_depth,
        "field_min_x": field_min_x,
        "field_min_y": field_min_y,
        "field_len_x": field_len_x,
        "field_len_y": field_len_y,
        "tower_x": tower_x,
        "tower_y": tower_y,
        "tower_len": tower_len,
        "tower_wid": tower_wid,
        "rail_outer_len": rail_outer_len,
        "rail_outer_wid": rail_outer_wid,
        "rail_x": rail_x,
        "rail_y": rail_y,
    }


def _cassette_post_positions(
    rail_x: float,
    rail_y: float,
    rail_outer_len: float,
    rail_outer_wid: float,
    support_post_width: float,
) -> list[tuple[float, float]]:
    return [
        (rail_x, rail_y),
        (rail_x + rail_outer_len - support_post_width, rail_y),
        (rail_x, rail_y + rail_outer_wid - support_post_width),
        (
            rail_x + rail_outer_len - support_post_width,
            rail_y + rail_outer_wid - support_post_width,
        ),
    ]


def _cassette_extra_support_positions(
    params: dict[str, Any],
    layout: dict[str, float],
) -> list[tuple[float, float]]:
    mat = params.get("mat_plane", {})
    if mat.get("cassette_extra_supports") != "mid_edges":
        return []

    support_w = mat.get("support_post_width", 6.0)
    rail_x = layout["rail_x"]
    rail_y = layout["rail_y"]
    rail_outer_len = layout["rail_outer_len"]
    rail_outer_wid = layout["rail_outer_wid"]
    return [
        (rail_x + rail_outer_len / 2 - support_w / 2, rail_y),
        (rail_x + rail_outer_len / 2 - support_w / 2, rail_y + rail_outer_wid - support_w),
        (rail_x, rail_y + rail_outer_wid / 2 - support_w / 2),
        (rail_x + rail_outer_len - support_w, rail_y + rail_outer_wid / 2 - support_w / 2),
    ]


def _plate_cap_bounds(
    params: dict[str, Any],
    layout: dict[str, float],
) -> tuple[float, float, float, float]:
    base = params["base"]
    wells = params["mock_wells"]
    incubator = params.get("incubator", {})
    plate_lip = incubator.get("emulated_plate_lip", 0)
    plate_cap = params.get("plate_cap", {})
    if plate_cap.get("use_plate_footprint", False):
        cap_x = (base["length_x"] - wells["plate_length_x"]) / 2
        cap_y = (base["width_y"] - wells["plate_width_y"]) / 2
        cap_max_x = cap_x + wells["plate_length_x"]
        cap_max_y = cap_y + wells["plate_width_y"]
    else:
        cap_x = layout["tower_x"] - plate_lip
        cap_y = layout["tower_y"] - plate_lip
        cap_max_x = cap_x + layout["tower_len"] + 2 * plate_lip
        cap_max_y = cap_y + layout["tower_wid"] + 2 * plate_lip

    mat = params.get("mat_plane", {})
    if (
        plate_cap.get("carries_mat_cassette_posts", False)
        and mat.get("guide_style") == "separate_cassette"
    ):
        cap_x = min(cap_x, layout["rail_x"])
        cap_y = min(cap_y, layout["rail_y"])
        cap_max_x = max(cap_max_x, layout["rail_x"] + layout["rail_outer_len"])
        cap_max_y = max(cap_max_y, layout["rail_y"] + layout["rail_outer_wid"])

    return (cap_x, cap_y, cap_max_x - cap_x, cap_max_y - cap_y)


def _plate_locator_positions(
    params: dict[str, Any],
    layout: dict[str, float],
) -> list[tuple[float, float]]:
    plate_cap = params.get("plate_cap", {})
    support_w = plate_cap.get("support_post_width", 8.0)
    cap_x, cap_y, cap_len, cap_wid = _plate_cap_bounds(params, layout)
    return [
        (cap_x + support_w / 2, cap_y + support_w / 2),
        (cap_x + cap_len - support_w / 2, cap_y + support_w / 2),
        (cap_x + support_w / 2, cap_y + cap_wid - support_w / 2),
        (cap_x + cap_len - support_w / 2, cap_y + cap_wid - support_w / 2),
    ]


def _plate_extra_support_positions(
    params: dict[str, Any],
    layout: dict[str, float],
) -> list[tuple[float, float]]:
    plate_cap = params.get("plate_cap", {})
    if plate_cap.get("extra_supports") != "mid_edges":
        return []

    support_w = plate_cap.get("support_post_width", 8.0)
    cap_x, cap_y, cap_len, cap_wid = _plate_cap_bounds(params, layout)
    return [
        (cap_x + cap_len / 2, cap_y + support_w / 2),
        (cap_x + cap_len / 2, cap_y + cap_wid - support_w / 2),
        (cap_x + support_w / 2, cap_y + cap_wid / 2),
        (cap_x + cap_len - support_w / 2, cap_y + cap_wid / 2),
    ]


def _plate_locator_size(plate_cap: dict[str, Any], index: int) -> tuple[float, float]:
    pin_w = plate_cap.get("locator_pin_width", 3.5)
    key_extra_x = plate_cap.get("locator_key_extra_x", 2.0)
    if index == 0:
        return pin_w + key_extra_x, pin_w
    return pin_w, pin_w


def _locator_size(mat: dict[str, Any], index: int) -> tuple[float, float]:
    pin_w = mat.get("cassette_locator_pin_width", 3.5)
    key_extra_x = mat.get("cassette_locator_key_extra_x", 2.0)
    if index == 0:
        return pin_w + key_extra_x, pin_w
    return pin_w, pin_w


def _guide_hole_diameter(mat: dict[str, Any], row: int) -> float:
    diameters = mat.get("guide_hole_diameter_by_row")
    if diameters:
        return diameters[row % len(diameters)]
    return mat["guide_hole_diameter"]


def _well_cut(params: dict[str, Any], row: int, col: int, z: float, depth: float) -> cq.Workplane:
    wells = params["mock_wells"]
    x, y = well_center(params, row, col)
    lower_diameter = wells.get("lower_diameter_mm", wells["diameter"])
    upper_diameter = wells.get("upper_diameter_mm", wells["diameter"])
    if lower_diameter != upper_diameter:
        return cq.Workplane("XY").add(
            cq.Solid.makeCone(
                lower_diameter / 2,
                upper_diameter / 2,
                depth + 0.05,
                pnt=(x, y, z),
                dir=(0, 0, 1),
            )
        )
    return cq.Workplane("XY").circle(wells["diameter"] / 2).extrude(depth).translate((x, y, z))


def _pipette_offset_for_well(params: dict[str, Any], column: int) -> dict[str, float]:
    strategy = params.get("pipette_offset_strategy", {})
    if strategy.get("test_offsets_by_column", True):
        return params["pipette_offsets"][column % len(params["pipette_offsets"])]
    return {
        "x": strategy.get("target_offset_x", 0.0),
        "y": strategy.get("target_offset_y", 0.0),
    }


def _label_config(params: dict[str, Any]) -> dict[str, Any]:
    return params.get("integrated_labels", {})


def _label_font(params: dict[str, Any], key: str, default: float) -> float:
    cfg = _label_config(params)
    return cfg.get(key, cfg.get("font_size", default))


def _label_depth(params: dict[str, Any]) -> float:
    return _label_config(params).get("cut_depth", 0.45)


def _integrated_labels_enabled(params: dict[str, Any]) -> bool:
    return _label_config(params).get("enabled", False)


def _open_support_positions(
    layout: dict[str, float],
    bay: dict[str, Any],
) -> list[tuple[float, float]]:
    post_w = bay.get("support_post_width", 4.0)
    margin = bay.get("support_post_margin", 4.0)
    field_center_x = layout["field_min_x"] + layout["field_len_x"] / 2
    field_center_y = layout["field_min_y"] + layout["field_len_y"] / 2
    keepout_r = bay.get("objective_keepout_diameter", 28.0) / 2 + bay.get(
        "objective_keepout_clearance", 2.0
    )

    xs = [
        layout["tower_x"] + margin + post_w / 2,
        layout["field_min_x"],
        layout["field_min_x"] + layout["field_len_x"] / 4,
        field_center_x,
        layout["field_min_x"] + 3 * layout["field_len_x"] / 4,
        layout["field_min_x"] + layout["field_len_x"],
        layout["tower_x"] + layout["tower_len"] - margin - post_w / 2,
    ]
    ys = [
        layout["tower_y"] + margin + post_w / 2,
        layout["field_min_y"],
        layout["field_min_y"] + layout["field_len_y"] / 4,
        field_center_y,
        layout["field_min_y"] + 3 * layout["field_len_y"] / 4,
        layout["field_min_y"] + layout["field_len_y"],
        layout["tower_y"] + layout["tower_wid"] - margin - post_w / 2,
    ]

    positions: list[tuple[float, float]] = []
    seen: set[tuple[float, float]] = set()
    for x in xs:
        for y in ys:
            dx = x - field_center_x
            dy = y - field_center_y
            if (dx * dx + dy * dy) ** 0.5 < keepout_r:
                continue
            key = (round(x, 3), round(y, 3))
            if key in seen:
                continue
            seen.add(key)
            positions.append((x, y))
    return positions


def _top_label_cut(
    text: str,
    x: float,
    y: float,
    top_z: float,
    font_size: float,
    depth: float,
    *,
    halign: str = "center",
    valign: str = "center",
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .text(
            text,
            font_size,
            depth + 0.05,
            combine=False,
            halign=halign,
            valign=valign,
        )
        .translate((x, y, top_z - depth))
    )


def _front_label_cut(
    text: str,
    x: float,
    face_y: float,
    z: float,
    font_size: float,
    depth: float,
    *,
    halign: str = "center",
    valign: str = "center",
    rotate_180: bool = False,
) -> cq.Workplane:
    # Text starts inside the front face and extrudes toward -Y so the glyphs
    # read upright from the OT-2 front while still cutting into the part.
    label = cq.Workplane("XY").text(
        text,
        font_size,
        depth + 0.05,
        combine=False,
        halign=halign,
        valign=valign,
    )
    if rotate_180:
        # The plate cap is installed inverted onto the posts, so its side label
        # needs the opposite in-plane orientation from base-side text.
        label = label.rotate((0, 0, 0), (0, 0, 1), 180)

    return label.rotate((0, 0, 0), (1, 0, 0), 90).translate((x, face_y + depth, z))


def _arrow_cut_x(
    x: float,
    y: float,
    top_z: float,
    length: float,
    width: float,
    depth: float,
) -> cq.Workplane:
    shaft_len = length * 0.62
    arrow = (
        cq.Workplane("XY")
        .box(shaft_len, width, depth + 0.05, centered=(False, True, False))
        .translate((x, y, top_z - depth))
    )
    head = (
        cq.Workplane("XY")
        .polyline(
            [
                (x + shaft_len, y - width * 1.4),
                (x + length, y),
                (x + shaft_len, y + width * 1.4),
            ]
        )
        .close()
        .extrude(depth + 0.05)
        .translate((0, 0, top_z - depth))
    )
    return arrow.union(head)


def _arrow_cut_y(
    x: float,
    y: float,
    top_z: float,
    length: float,
    width: float,
    depth: float,
) -> cq.Workplane:
    shaft_len = length * 0.62
    arrow = (
        cq.Workplane("XY")
        .box(width, shaft_len, depth + 0.05, centered=(True, False, False))
        .translate((x, y, top_z - depth))
    )
    head = (
        cq.Workplane("XY")
        .polyline(
            [
                (x - width * 1.4, y + shaft_len),
                (x, y + length),
                (x + width * 1.4, y + shaft_len),
            ]
        )
        .close()
        .extrude(depth + 0.05)
        .translate((0, 0, top_z - depth))
    )
    return arrow.union(head)


def build_fixture(params: dict[str, Any]) -> cq.Workplane:
    base = params["base"]
    stack = params["raised_stack"]
    incubator = params.get("incubator", {})
    wells = params["mock_wells"]
    mat = params["mat_plane"]
    bay = params.get("inverted_bay", {})
    print_qc = params.get("print_qc", {})

    length = base["length_x"]
    width = base["width_y"]
    base_thickness = base["thickness_z"]
    layout = _fixture_layout(params)
    plate_top_z = layout["plate_top_z"]
    wall = stack["wall_thickness"]
    mat_z = layout["mat_z"]
    frame_thickness = mat["frame_thickness"]
    support_post_width = mat["support_post_width"]
    guide_plate_thickness = mat["guide_plate_thickness"]
    pocket_depth = mat["pocket_depth"]

    model = _rounded_box(length, width, base_thickness, base["corner_radius"])

    if base.get("adhesion_tabs_enabled", False):
        # Sacrificial mouse-ear tabs for PLA bed adhesion. These intentionally
        # sit outside the SBS footprint and must be trimmed before OT-2 use.
        tab_r = base["adhesion_tab_diameter"] / 2
        tab_h = base["adhesion_tab_thickness"]
        neck_w = base["adhesion_tab_neck_width"]
        tab_offset = base["adhesion_tab_offset"]
        tabs = [
            (0, 0, -tab_offset, -tab_offset, neck_w, neck_w),
            (length, 0, length + tab_offset, -tab_offset, neck_w, neck_w),
            (0, width, -tab_offset, width + tab_offset, neck_w, neck_w),
            (length, width, length + tab_offset, width + tab_offset, neck_w, neck_w),
        ]
        for base_x, base_y, tab_x, tab_y, neck_len_x, neck_len_y in tabs:
            model = model.union(
                cq.Workplane("XY").circle(tab_r).extrude(tab_h).translate((tab_x, tab_y, 0))
            )
            neck_x = min(base_x, tab_x)
            neck_y = min(base_y, tab_y)
            model = model.union(
                cq.Workplane("XY")
                .box(
                    abs(base_x - tab_x) + neck_len_x,
                    abs(base_y - tab_y) + neck_len_y,
                    tab_h,
                    centered=(False, False, False),
                )
                .translate((neck_x - neck_w / 2, neck_y - neck_w / 2, 0))
            )

    plate_bottom_z = layout["plate_bottom_z"]
    well_bottom_z = layout["well_bottom_z"]
    well_depth = layout["well_depth"]

    # Raised section under the 4x4 well field. Kept blocky for a fast, robust first print.
    field_min_x = layout["field_min_x"]
    field_min_y = layout["field_min_y"]
    field_len_x = layout["field_len_x"]
    field_len_y = layout["field_len_y"]
    tower_x = layout["tower_x"]
    tower_y = layout["tower_y"]
    tower_len = layout["tower_len"]
    tower_wid = layout["tower_wid"]
    tower_h = plate_bottom_z - base_thickness

    support_style = bay.get("support_style")
    separate_plate_cap = (
        support_style == "separate_plate_cap"
        or params.get("plate_cap", {}).get("part_style") == "separate_cap"
    )
    separate_upper_plate = separate_plate_cap
    open_bay_posts = support_style == "open_posts"
    if separate_plate_cap:
        plate_cap = params.get("plate_cap", {})
        post_w = plate_cap.get("support_post_width", 8.0)
        pin_h = plate_cap.get("locator_pin_height", 2.0)
        extra_positions = _plate_extra_support_positions(params, layout)
        for idx, (post_cx, post_cy) in enumerate(_plate_locator_positions(params, layout)):
            model = model.union(
                cq.Workplane("XY")
                .box(post_w, post_w, tower_h, centered=(True, True, False))
                .translate((post_cx, post_cy, base_thickness))
            )
            pin_x, pin_y = _plate_locator_size(plate_cap, idx)
            model = model.union(
                cq.Workplane("XY")
                .box(pin_x, pin_y, pin_h, centered=(True, True, False))
                .translate((post_cx, post_cy, plate_bottom_z))
            )
        for post_cx, post_cy in extra_positions:
            model = model.union(
                cq.Workplane("XY")
                .box(post_w, post_w, tower_h, centered=(True, True, False))
                .translate((post_cx, post_cy, base_thickness))
            )
    elif open_bay_posts:
        post_w = bay.get("support_post_width", 4.0)
        for post_cx, post_cy in _open_support_positions(layout, bay):
            model = model.union(
                cq.Workplane("XY")
                .box(post_w, post_w, tower_h, centered=(True, True, False))
                .translate((post_cx, post_cy, base_thickness))
            )
    else:
        model = model.union(
            cq.Workplane("XY")
            .box(tower_len, tower_wid, tower_h, centered=(False, False, False))
            .translate((tower_x, tower_y, base_thickness))
        )

    if incubator.get("enabled", False) and not separate_upper_plate:
        plate_lip = incubator.get("emulated_plate_lip", 0)
        if plate_lip > 0 and wells["plate_height_z"] > 0:
            # A visual/mechanical plate layer. This makes the mock culture plate
            # explicit instead of leaving it implied as the top of the bridge.
            model = model.union(
                cq.Workplane("XY")
                .box(
                    tower_len + 2 * plate_lip,
                    tower_wid + 2 * plate_lip,
                    wells["plate_height_z"],
                    centered=(False, False, False),
                )
                .translate((tower_x - plate_lip, tower_y - plate_lip, plate_bottom_z))
            )

    if bay.get("cavity_enabled", False) and not open_bay_posts:
        field_center_x = field_min_x + field_len_x / 2
        separator_thickness = incubator.get("wet_dry_separator_thickness", 3.0)
        cavity_top_z = well_bottom_z - separator_thickness
        cavity_x = field_center_x - bay["cavity_width_x"] / 2

        # Legacy tunnel-style dry-bay proxy. The current first PoC uses
        # open_posts instead, so this branch is retained only for comparison.
        model = model.cut(
            cq.Workplane("XY")
            .box(
                bay["cavity_width_x"],
                tower_wid + 0.4,
                max(cavity_top_z - base_thickness, 0.1),
                centered=(False, False, False),
            )
            .translate((cavity_x, tower_y - 0.2, base_thickness))
        )

    if incubator.get("enabled", False) and incubator.get("sidewall_enabled", False):
        headspace_h = mat_z - plate_top_z
        sidewall = (
            cq.Workplane("XY")
            .box(tower_len, tower_wid, headspace_h, centered=(False, False, False))
            .translate((tower_x, tower_y, plate_top_z))
        )
        sidewall = sidewall.cut(
            cq.Workplane("XY")
            .box(
                tower_len - 2 * wall,
                tower_wid - 2 * wall,
                headspace_h + 0.2,
                centered=(False, False, False),
            )
            .translate((tower_x + wall, tower_y + wall, plate_top_z - 0.1))
        )
        if incubator.get("headspace_window_enabled", False):
            window_len = incubator["headspace_window_length"]
            window_h = incubator["headspace_window_height"]
            window_z = plate_top_z + incubator["headspace_window_bottom_above_plate"]
            window_x = tower_x + tower_len / 2 - window_len / 2
            window_y = tower_y + tower_wid / 2 - window_len / 2
            # Front and rear windows.
            for cut_y in [tower_y - 0.1, tower_y + tower_wid - wall - 0.1]:
                sidewall = sidewall.cut(
                    cq.Workplane("XY")
                    .box(window_len, wall + 0.2, window_h, centered=(False, False, False))
                    .translate((window_x, cut_y, window_z))
                )
            # Left and right windows.
            for cut_x in [tower_x - 0.1, tower_x + tower_len - wall - 0.1]:
                sidewall = sidewall.cut(
                    cq.Workplane("XY")
                    .box(wall + 0.2, window_len, window_h, centered=(False, False, False))
                    .translate((cut_x, window_y, window_z))
                )
        model = model.union(sidewall)

    # Lid/mat collision-envelope support. In separate-cassette mode the mat
    # supports live on the removable mock plate cap, because the critical datum
    # is the slit-to-well relationship rather than the mat-to-base relationship.
    rail_outer_len = layout["rail_outer_len"]
    rail_outer_wid = layout["rail_outer_wid"]
    rail_x = layout["rail_x"]
    rail_y = layout["rail_y"]
    rail_h = frame_thickness
    rail_z = mat_z
    open_x = rail_x + wall
    open_y = rail_y + wall
    open_len = rail_outer_len - 2 * wall
    open_wid = rail_outer_wid - 2 * wall

    guide_style = mat.get("guide_style", "plate")
    post_positions = _cassette_post_positions(
        rail_x, rail_y, rail_outer_len, rail_outer_wid, support_post_width
    )
    if guide_style == "separate_cassette":
        pass
    else:
        rail = (
            cq.Workplane("XY")
            .box(rail_outer_len, rail_outer_wid, rail_h, centered=(False, False, False))
            .translate((rail_x, rail_y, rail_z))
        )
        rail = rail.cut(
            cq.Workplane("XY")
            .box(open_len, open_wid, rail_h + 0.2, centered=(False, False, False))
            .translate((open_x, open_y, rail_z - 0.1))
        )
        model = model.union(rail)

        # Vertical posts make the cassette-envelope rail printable and represent the
        # eventual stand-off structure that holds the mat plane above the wells. They
        # start at the base, not at the smaller raised well block, so the rail is
        # mechanically continuous in the first print.
        post_h = rail_z + rail_h - base_thickness
        for post_x, post_y in post_positions:
            model = model.union(
                cq.Workplane("XY")
                .box(
                    support_post_width,
                    support_post_width,
                    post_h,
                    centered=(False, False, False),
                )
                .translate((post_x, post_y, base_thickness))
            )

    # Guide/access geometry at the mat plane. In the current first-print path,
    # this lives in a separate flat cassette print.
    plate_overlap = 0.3
    x_min = field_min_x - mat["patch_margin"]
    y_min = field_min_y - mat["patch_margin"]
    if guide_style == "plate":
        guide_plate = (
            cq.Workplane("XY")
            .box(
                open_len + 2 * plate_overlap,
                open_wid + 2 * plate_overlap,
                guide_plate_thickness,
                centered=(False, False, False),
            )
            .translate((open_x - plate_overlap, open_y - plate_overlap, mat_z))
        )

        # Shallow top recess for laying/taping a Cole-Parmer mat patch onto the guide plate.
        guide_plate = guide_plate.cut(
            cq.Workplane("XY")
            .box(
                field_len_x + 2 * mat["patch_margin"],
                field_len_y + 2 * mat["patch_margin"],
                pocket_depth + 0.1,
                centered=(False, False, False),
            )
            .translate(
                (
                    x_min,
                    y_min,
                    mat_z + guide_plate_thickness - pocket_depth,
                )
            )
        )

        if mat.get("plug_witness_enabled", False):
            # Shallow circular witness marks approximate the round mat plug/slit
            # locations. They are inspection geometry, not real mat dimensions.
            for row in range(wells["rows"]):
                for col in range(wells["columns"]):
                    x, y = well_center(params, row, col)
                    offset = _pipette_offset_for_well(params, col)
                    guide_plate = guide_plate.cut(
                        cq.Workplane("XY")
                        .circle(mat["plug_witness_diameter"] / 2)
                        .extrude(mat["plug_witness_depth"] + 0.05)
                        .translate(
                            (
                                x + offset["x"],
                                y + offset["y"],
                                mat_z + guide_plate_thickness - pocket_depth,
                            )
                        )
                    )

        # One guide hole per well. Columns intentionally step through different offsets
        # so one print tests center, +1.0, +1.5, and +2.0 mm access behavior.
        for row in range(wells["rows"]):
            for col in range(wells["columns"]):
                x, y = well_center(params, row, col)
                offset = _pipette_offset_for_well(params, col)
                guide_plate = guide_plate.cut(
                    cq.Workplane("XY")
                    .circle(_guide_hole_diameter(mat, row) / 2)
                    .extrude(guide_plate_thickness + 0.4)
                    .translate((x + offset["x"], y + offset["y"], mat_z - 0.2))
                )

        model = model.union(guide_plate)
    elif guide_style == "suspended_scaffold":
        beam_w = mat.get("scaffold_beam_width", 1.6)
        picket_w = mat.get("scaffold_picket_width", 1.6)
        scaffold_h = guide_plate_thickness
        picket_bottom_z = plate_top_z - 0.3
        picket_h = mat_z + scaffold_h - picket_bottom_z

        scaffold: cq.Workplane | None = None

        def add_scaffold(part: cq.Workplane) -> None:
            nonlocal scaffold
            scaffold = part if scaffold is None else scaffold.union(part)

        row_beam_len = field_len_x
        row_beam_x = field_min_x
        for row in range(wells["rows"]):
            _, row_y = well_center(params, row, 0)
            add_scaffold(
                cq.Workplane("XY")
                .box(row_beam_len, beam_w, scaffold_h, centered=(False, False, False))
                .translate((row_beam_x, row_y - beam_w / 2, mat_z))
            )

        interstitial_xs = [
            field_min_x,
            *[
                wells["a1_center_x"] + (col + 0.5) * wells["pitch"]
                for col in range(wells["columns"] - 1)
            ],
            field_min_x + field_len_x,
        ]
        for row in range(wells["rows"]):
            _, row_y = well_center(params, row, 0)
            for post_x in interstitial_xs:
                add_scaffold(
                    cq.Workplane("XY")
                    .box(picket_w, picket_w, picket_h, centered=(False, False, False))
                    .translate((post_x - picket_w / 2, row_y - picket_w / 2, picket_bottom_z))
                )

        if scaffold is None:
            raise ValueError("suspended scaffold generated no parts")

        for row in range(wells["rows"]):
            for col in range(wells["columns"]):
                x, y = well_center(params, row, col)
                offset = _pipette_offset_for_well(params, col)
                cx = x + offset["x"]
                cy = y + offset["y"]
                scaffold = scaffold.cut(
                    cq.Workplane("XY")
                    .circle(_guide_hole_diameter(mat, row) / 2)
                    .extrude(scaffold_h + 0.4)
                    .translate((cx, cy, mat_z - 0.2))
                )

        model = model.union(scaffold)
    elif guide_style == "separate_cassette":
        pass
    else:
        raise ValueError(f"unknown mat_plane.guide_style: {guide_style}")

    if print_qc.get("enabled", False):
        qc_z = print_qc["surface_z"]
        for idx, diameter in enumerate(print_qc["guide_hole_test_diameters"]):
            model = model.cut(
                cq.Workplane("XY")
                .circle(diameter / 2)
                .extrude(qc_z)
                .translate(
                    (
                        print_qc["guide_hole_test_x"],
                        print_qc["guide_hole_test_y"] + idx * print_qc["guide_hole_test_spacing"],
                        0,
                    )
                )
            )

        step_x = print_qc["z_step_x"]
        for idx, height in enumerate(print_qc["z_step_heights"]):
            model = model.union(
                cq.Workplane("XY")
                .box(
                    print_qc["z_step_size"],
                    print_qc["z_step_size"],
                    height,
                    centered=(False, False, False),
                )
                .translate((step_x + idx * print_qc["z_step_size"], print_qc["z_step_y"], qc_z))
            )

        if guide_style == "plate":
            # Mat-patch corner marks on the top of the guide plate/recess. These are
            # shallow circular marks for aligning a cut Cole-Parmer mat patch.
            mark_r = print_qc["mat_patch_corner_mark_diameter"] / 2
            patch_min_x = field_min_x - mat["patch_margin"]
            patch_min_y = field_min_y - mat["patch_margin"]
            patch_max_x = field_min_x + field_len_x + mat["patch_margin"]
            patch_max_y = field_min_y + field_len_y + mat["patch_margin"]
            for mark_x, mark_y in [
                (patch_min_x, patch_min_y),
                (patch_max_x, patch_min_y),
                (patch_min_x, patch_max_y),
                (patch_max_x, patch_max_y),
            ]:
                model = model.cut(
                    cq.Workplane("XY")
                    .circle(mark_r)
                    .extrude(0.4)
                    .translate((mark_x, mark_y, mat_z + guide_plate_thickness - 0.4))
                )

    if not separate_upper_plate:
        # Mock wells.
        for row in range(wells["rows"]):
            for col in range(wells["columns"]):
                model = model.cut(_well_cut(params, row, col, well_bottom_z, well_depth))

    # Fiducials on the base top.
    for fid in params["fiducials"]:
        model = model.cut(
            cq.Workplane("XY")
            .circle(fid["diameter"] / 2)
            .extrude(fid["depth"])
            .translate((fid["x"], fid["y"], base_thickness - fid["depth"]))
        )

    if bay.get("enabled", False):
        field_center_x = field_min_x + field_len_x / 2
        field_center_y = field_min_y + field_len_y / 2
        aperture_x = field_center_x - bay["aperture_length_x"] / 2
        aperture_y = field_center_y - bay["aperture_width_y"] / 2

        # Bottom-side reference recess for the future inverted optics bay. It is
        # intentionally shallow so the fixture still behaves like a one-piece
        # deck article, but it gives a physical footprint for objective/bay
        # alignment planning after printing.
        model = model.cut(
            cq.Workplane("XY")
            .box(
                bay["aperture_length_x"],
                bay["aperture_width_y"],
                bay["aperture_recess_depth"],
                centered=(False, False, False),
            )
            .translate((aperture_x, aperture_y, -0.01))
        )

        model = model.cut(
            cq.Workplane("XY")
            .circle(bay["objective_keepout_diameter"] / 2)
            .extrude(bay["aperture_recess_depth"] + 0.02)
            .translate((field_center_x, field_center_y, -0.01))
        )
        model = model.cut(
            cq.Workplane("XY")
            .circle(bay["center_mark_diameter"] / 2)
            .extrude(base_thickness)
            .translate((field_center_x, field_center_y, 0))
        )
        model = model.cut(
            cq.Workplane("XY")
            .box(
                bay["crosshair_length"],
                bay["crosshair_width"],
                bay["aperture_recess_depth"] + 0.02,
                centered=(True, True, False),
            )
            .translate((field_center_x, field_center_y, -0.01))
        )
        model = model.cut(
            cq.Workplane("XY")
            .box(
                bay["crosshair_width"],
                bay["crosshair_length"],
                bay["aperture_recess_depth"] + 0.02,
                centered=(True, True, False),
            )
            .translate((field_center_x, field_center_y, -0.01))
        )

        for zone in bay["reference_zones"]:
            model = model.cut(
                cq.Workplane("XY")
                .circle(zone["diameter"] / 2)
                .extrude(zone["depth"])
                .translate((zone["x"], zone["y"], -0.01))
            )

    if _integrated_labels_enabled(params):
        cfg = _label_config(params)
        font = _label_font(params, "base_font_size", 4.2)
        axis_font = _label_font(params, "axis_font_size", 3.6)
        depth = _label_depth(params)
        model = model.cut(
            _front_label_cut(
                cfg.get("base_front_text", "FRONT SLOT 1"),
                length / 2,
                0.0,
                base_thickness / 2,
                font,
                depth,
            )
        )
        if cfg.get("axis_arrows_enabled", True):
            origin_x = cfg.get("axis_origin_x", 11.0)
            origin_y = cfg.get("axis_origin_y", 11.0)
            arrow_len = cfg.get("axis_arrow_length", 16.0)
            arrow_w = cfg.get("axis_arrow_width", 1.2)
            model = model.cut(
                _arrow_cut_x(origin_x, origin_y, base_thickness, arrow_len, arrow_w, depth)
            )
            model = model.cut(
                _top_label_cut(
                    "+X",
                    origin_x + arrow_len + 4.5,
                    origin_y,
                    base_thickness,
                    axis_font,
                    depth,
                )
            )
            model = model.cut(
                _arrow_cut_y(origin_x, origin_y, base_thickness, arrow_len, arrow_w, depth)
            )
            model = model.cut(
                _top_label_cut(
                    "+Y",
                    origin_x,
                    origin_y + arrow_len + 4.5,
                    base_thickness,
                    axis_font,
                    depth,
                )
            )

    return model


def build_plate_cap(params: dict[str, Any], *, assembly_position: bool = False) -> cq.Workplane:
    """Build the removable mock CellVis plate cap.

    Print orientation has the cap bottom at z=0. Assembly orientation places
    the cap at the raised plate position.
    """

    wells = params["mock_wells"]
    mat = params["mat_plane"]
    plate_cap = params.get("plate_cap", {})
    layout = _fixture_layout(params)

    cap_x, cap_y, cap_len, cap_wid = _plate_cap_bounds(params, layout)
    thickness = wells["plate_height_z"]
    z0 = layout["plate_bottom_z"] if assembly_position else 0.0

    cap = (
        cq.Workplane("XY")
        .box(cap_len, cap_wid, thickness, centered=(False, False, False))
        .translate((cap_x, cap_y, z0))
    )

    locator_cutouts_enabled = plate_cap.get("locator_cutouts_enabled", True)
    if locator_cutouts_enabled:
        clearance = plate_cap.get("locator_pin_clearance", 0.35)
        for idx, (post_cx, post_cy) in enumerate(_plate_locator_positions(params, layout)):
            pin_x, pin_y = _plate_locator_size(plate_cap, idx)
            cap = cap.cut(
                cq.Workplane("XY")
                .box(
                    pin_x + clearance,
                    pin_y + clearance,
                    thickness + 0.4,
                    centered=(True, True, False),
                )
                .translate((post_cx, post_cy, z0 - 0.2))
            )

    well_floor_z = z0 + wells["bottom_height"] + wells["coverslip_thickness"]
    for row in range(wells["rows"]):
        for col in range(wells["columns"]):
            cap = cap.cut(_well_cut(params, row, col, well_floor_z, layout["well_depth"]))

    if (
        plate_cap.get("carries_mat_cassette_posts", False)
        and mat.get("guide_style") == "separate_cassette"
    ):
        support_post_width = mat["support_post_width"]
        post_h = mat["height_above_mock_plate_top"]
        pin_h = mat["frame_thickness"]
        cap_top_z = z0 + thickness
        post_positions = _cassette_post_positions(
            layout["rail_x"],
            layout["rail_y"],
            layout["rail_outer_len"],
            layout["rail_outer_wid"],
            support_post_width,
        )
        for idx, (post_x, post_y) in enumerate(post_positions):
            cap = cap.union(
                cq.Workplane("XY")
                .box(
                    support_post_width,
                    support_post_width,
                    post_h,
                    centered=(False, False, False),
                )
                .translate((post_x, post_y, cap_top_z))
            )
            pin_x, pin_y = _locator_size(mat, idx)
            cap = cap.union(
                cq.Workplane("XY")
                .box(pin_x, pin_y, pin_h, centered=(True, True, False))
                .translate(
                    (
                        post_x + support_post_width / 2,
                        post_y + support_post_width / 2,
                        cap_top_z + post_h,
                    )
                )
            )
        for post_x, post_y in _cassette_extra_support_positions(params, layout):
            cap = cap.union(
                cq.Workplane("XY")
                .box(
                    support_post_width,
                    support_post_width,
                    post_h,
                    centered=(False, False, False),
                )
                .translate((post_x, post_y, cap_top_z))
            )

    if _integrated_labels_enabled(params):
        cfg = _label_config(params)
        depth = _label_depth(params)
        side_font = _label_font(params, "plate_side_font_size", 4.2)
        top_font = _label_font(params, "plate_top_font_size", 3.8)
        cap = cap.cut(
            _front_label_cut(
                cfg.get("plate_front_text", "PLATE A1"),
                cap_x + cap_len / 2,
                cap_y,
                z0 + thickness / 2,
                side_font,
                depth,
                rotate_180=cfg.get("plate_front_inverted_for_install", True),
            )
        )

        a1_x, _a1_y = well_center(params, 0, 0)
        last_x, _last_y = well_center(params, wells["rows"] - 1, wells["columns"] - 1)
        field_min_y = layout["field_min_y"]
        field_max_y = layout["field_min_y"] + layout["field_len_y"]
        label_front_y = max(cap_y + 3.0, field_min_y - 3.0)
        label_back_y = min(cap_y + cap_wid - 3.0, field_max_y + 3.0)
        last_label = f"{chr(ord('A') + wells['rows'] - 1)}{wells['columns']}"
        cap = cap.cut(_top_label_cut("A1", a1_x, label_front_y, z0 + thickness, top_font, depth))
        cap = cap.cut(
            _top_label_cut(last_label, last_x, label_back_y, z0 + thickness, top_font, depth)
        )

    return cap


def build_mat_cassette(params: dict[str, Any], *, assembly_position: bool = False) -> cq.Workplane:
    """Build the removable printed mat-cassette emulator.

    Print orientation has the cassette bottom at z=0. Assembly orientation
    places the cassette at the real mat plane above the mock plate.
    """

    stack = params["raised_stack"]
    wells = params["mock_wells"]
    mat = params["mat_plane"]
    layout = _fixture_layout(params)

    wall = stack["wall_thickness"]
    support_post_width = mat["support_post_width"]
    thickness = mat["frame_thickness"]
    pocket_depth = mat["pocket_depth"]
    clearance = mat.get("cassette_locator_pin_clearance", 0.35)

    z0 = layout["mat_z"] if assembly_position else 0.0
    rail_x = layout["rail_x"]
    rail_y = layout["rail_y"]
    rail_outer_len = layout["rail_outer_len"]
    rail_outer_wid = layout["rail_outer_wid"]
    field_min_x = layout["field_min_x"]
    field_min_y = layout["field_min_y"]
    field_len_x = layout["field_len_x"]
    field_len_y = layout["field_len_y"]

    cassette = (
        cq.Workplane("XY")
        .box(rail_outer_len, rail_outer_wid, thickness, centered=(False, False, False))
        .translate((rail_x, rail_y, z0))
    )

    # Shallow top recess for taping or locating a cut Cole-Parmer mat patch.
    cassette = cassette.cut(
        cq.Workplane("XY")
        .box(
            field_len_x + 2 * mat["patch_margin"],
            field_len_y + 2 * mat["patch_margin"],
            min(pocket_depth, thickness - 0.4) + 0.1,
            centered=(False, False, False),
        )
        .translate(
            (
                field_min_x - mat["patch_margin"],
                field_min_y - mat["patch_margin"],
                z0 + thickness - min(pocket_depth, thickness - 0.4),
            )
        )
    )

    # Locator holes drop over the screwless pins printed on the spacer or plate
    # cap posts. The A1-side locator is intentionally elongated so orientation
    # is obvious.
    post_positions = _cassette_post_positions(
        rail_x, rail_y, rail_outer_len, rail_outer_wid, support_post_width
    )
    for idx, (post_x, post_y) in enumerate(post_positions):
        pin_x, pin_y = _locator_size(mat, idx)
        post_cx = post_x + support_post_width / 2
        post_cy = post_y + support_post_width / 2
        cassette = cassette.cut(
            cq.Workplane("XY")
            .box(
                pin_x + clearance,
                pin_y + clearance,
                thickness + 0.4,
                centered=(True, True, False),
            )
            .translate((post_cx, post_cy, z0 - 0.2))
        )

    # One guide hole per mock well. Columns intentionally step through offsets;
    # rows step through hole diameters so the cassette tests real entry paths.
    for row in range(wells["rows"]):
        for col in range(wells["columns"]):
            x, y = well_center(params, row, col)
            offset = _pipette_offset_for_well(params, col)
            cassette = cassette.cut(
                cq.Workplane("XY")
                .circle(_guide_hole_diameter(mat, row) / 2)
                .extrude(thickness + 0.4)
                .translate((x + offset["x"], y + offset["y"], z0 - 0.2))
            )

    # Mat-patch corner marks are cut into the pocket floor so they remain visible
    # after the cassette is printed flat.
    print_qc = params.get("print_qc", {})
    if print_qc.get("enabled", False):
        mark_r = print_qc["mat_patch_corner_mark_diameter"] / 2
        patch_min_x = field_min_x - mat["patch_margin"]
        patch_min_y = field_min_y - mat["patch_margin"]
        patch_max_x = field_min_x + field_len_x + mat["patch_margin"]
        patch_max_y = field_min_y + field_len_y + mat["patch_margin"]
        mark_depth = min(0.35, thickness / 2)
        mark_z = z0 + thickness - min(pocket_depth, thickness - 0.4) - mark_depth
        for mark_x, mark_y in [
            (patch_min_x, patch_min_y),
            (patch_max_x, patch_min_y),
            (patch_min_x, patch_max_y),
            (patch_max_x, patch_max_y),
        ]:
            cassette = cassette.cut(
                cq.Workplane("XY")
                .circle(mark_r)
                .extrude(mark_depth + 0.05)
                .translate((mark_x, mark_y, mark_z))
            )

    # A shallow perimeter relief makes the part read as a cassette frame instead
    # of a featureless tile while keeping a continuous central mat emulator.
    relief_depth = min(0.35, thickness / 3)
    open_x = rail_x + wall
    open_y = rail_y + wall
    open_len = rail_outer_len - 2 * wall
    open_wid = rail_outer_wid - 2 * wall
    cassette = cassette.cut(
        cq.Workplane("XY")
        .box(open_len, open_wid, relief_depth + 0.05, centered=(False, False, False))
        .translate((open_x, open_y, z0 + thickness - relief_depth))
    )

    return cassette


def build_fixture_assembly(params: dict[str, Any]) -> cq.Workplane:
    assembly = build_fixture(params)
    assembly = assembly.union(build_plate_cap(params, assembly_position=True))
    return assembly.union(build_mat_cassette(params, assembly_position=True))


def export_fixture(params: dict[str, Any], out_dir: str | Path) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    base_model = build_fixture(params)
    plate_cap_model = build_plate_cap(params)
    cassette_model = build_mat_cassette(params)
    assembly_model = build_fixture_assembly(params)

    base_stl = out / f"{params['name']}_base.stl"
    base_step = out / f"{params['name']}_base.step"
    plate_cap_stl = out / f"{params['name']}_plate_cap.stl"
    plate_cap_step = out / f"{params['name']}_plate_cap.step"
    cassette_stl = out / f"{params['name']}_mat_cassette.stl"
    cassette_step = out / f"{params['name']}_mat_cassette.step"
    assembly_step = out / f"{params['name']}_assembly.step"

    cq.exporters.export(base_model, str(base_stl))
    cq.exporters.export(base_model, str(base_step))
    cq.exporters.export(plate_cap_model, str(plate_cap_stl))
    cq.exporters.export(plate_cap_model, str(plate_cap_step))
    cq.exporters.export(cassette_model, str(cassette_stl))
    cq.exporters.export(cassette_model, str(cassette_step))
    cq.exporters.export(assembly_model, str(assembly_step))

    paths = {
        "base_stl": base_stl,
        "base_step": base_step,
        "cassette_stl": cassette_stl,
        "cassette_step": cassette_step,
        "assembly_step": assembly_step,
    }
    paths["plate_cap_stl"] = plate_cap_stl
    paths["plate_cap_step"] = plate_cap_step
    return paths
