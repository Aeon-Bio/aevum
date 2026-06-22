from __future__ import annotations
from typing import Any
import cadquery as cq
from ..layout import (_compression_stop_positions, _slot_centers, row_coupon_layout)
from ._geom_base import (_perimeter_rails, _rounded_box)
from ._shared_tile import (_deck_slot_opening_for_tile, _lid_port_positions, _septum_access_window_for_tile, _well_centers_for_tile)


def _add_deck_engagement_feet(
    model: cq.Workplane,
    *,
    tile: dict[str, Any],
    params: dict[str, Any],
) -> cq.Workplane:
    deck = params["deck_interface"]
    foot_h = deck["standoff_height_z"]
    radius = deck["foot_corner_radius"]
    feet = _deck_engagement_foot_rectangles(tile_origins=[tile], params=params)

    for foot_rect in feet:
        foot = _rounded_box(
            foot_rect["length_x"],
            foot_rect["width_y"],
            foot_h,
            radius,
        ).translate((foot_rect["x"], foot_rect["y"], -foot_h))
        model = model.union(foot)

    front_left = min(feet, key=lambda foot: (foot["x"], foot["y"]))

    return _cut_deck_key_notch(
        model,
        x=front_left["x"] + front_left["length_x"] / 2,
        y=front_left["y"],
        z=-foot_h,
        deck=deck,
    )


def _add_deck_slot_shoes(
    model: cq.Workplane,
    *,
    layout: dict[str, Any],
    params: dict[str, Any],
) -> cq.Workplane:
    deck = params["deck_interface"]
    thickness = deck["slot_shoe_thickness_z"]
    z0 = layout["deck_plane_z"]
    clearance = deck["slot_shoe_clearance_xy"]
    shoe_len = deck["slot_opening_length_x"] - 2 * clearance
    shoe_wid = deck["slot_opening_width_y"] - 2 * clearance
    for tile in layout["tile_origins"]:
        x, y, _, _ = _deck_slot_opening_for_tile(tile, params)
        shoe = _rounded_box(
            shoe_len,
            shoe_wid,
            thickness,
            deck["slot_shoe_corner_radius"],
        ).translate((x + clearance, y + clearance, z0))
        model = model.union(shoe)
    return model


def _add_latch_tension_posts(
    model: cq.Workplane,
    *,
    layout: dict[str, Any],
    params: dict[str, Any],
    z0: float,
    height: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    post_d = production.get("latch_post_diameter", 0.0)
    if post_d <= 0:
        return model

    lid = params["lid_manifold"]
    skirt = params["wet_chamber_skirt"]
    bounds = layout["wet_chamber_skirt"]
    head_len_x = production.get("latch_post_head_length_x", 8.5)
    head_w_y = production.get("latch_post_head_width_y", 10.0)
    head_h = production.get("latch_post_head_height_z", 1.0)
    pedestal_w = production.get("latch_post_pedestal_width_y", 3.4)
    root_len = production.get("latch_post_root_gusset_length_x", 0.0)
    root_w = production.get("latch_post_root_gusset_width_y", 0.0)
    root_h = min(production.get("latch_post_root_gusset_height_z", 0.0), height)
    wedge_h = production.get("wedge_lock_height_z", 3.0)
    frame_bottom_z = bounds["bottom_z"]
    wedge_bottom_z = layout["lid_top_z"] + lid["duct_height_z"]
    head_bottom_z = z0 + (wedge_bottom_z + wedge_h - frame_bottom_z)
    shaft_base_z = z0 + height - 0.2
    shaft_h = max(0.2, head_bottom_z - shaft_base_z + 0.05)
    lane_span = (
        skirt["wall_thickness"]
        + skirt.get("service_lane_width", 0.0)
        + skirt.get("plenum_divider_thickness", 0.0)
    )

    for post in layout["latch_post_positions"]:
        x = float(post["x"])
        y = float(post["y"])
        if post["slide_axis"] == "x":
            ped_len_x = max(lane_span, head_len_x)
            ped_y = min(
                max(bounds["y"], y - pedestal_w / 2),
                bounds["y"] + bounds["width_y"] - pedestal_w,
            )
            if post["insert_from"] == "min":
                ped_x = bounds["x"]
            else:
                ped_x = bounds["x"] + bounds["length_x"] - ped_len_x
            pedestal = (
                cq.Workplane("XY")
                .box(ped_len_x, pedestal_w, height, centered=(False, False, False))
                .translate((ped_x, ped_y, z0))
            )
            head = _rounded_box(
                head_len_x,
                head_w_y,
                head_h,
                min(head_len_x, head_w_y) / 8,
            ).translate((x - head_len_x / 2, y - head_w_y / 2, head_bottom_z))
            root_pad: cq.Workplane | None = None
            if root_len > 0 and root_w > 0 and root_h > 0:
                root_x = min(
                    max(bounds["x"], x - root_len / 2),
                    bounds["x"] + bounds["length_x"] - root_len,
                )
                root_y = min(
                    max(bounds["y"], y - root_w / 2),
                    bounds["y"] + bounds["width_y"] - root_w,
                )
                root_pad = (
                    cq.Workplane("XY")
                    .box(root_len, root_w, root_h, centered=(False, False, False))
                    .translate((root_x, root_y, z0 + height - root_h))
                )
        else:
            ped_len_y = max(lane_span, head_w_y)
            ped_x = min(
                max(bounds["x"], x - pedestal_w / 2),
                bounds["x"] + bounds["length_x"] - pedestal_w,
            )
            if post["insert_from"] == "min":
                ped_y = bounds["y"]
            else:
                ped_y = bounds["y"] + bounds["width_y"] - ped_len_y
            pedestal = (
                cq.Workplane("XY")
                .box(pedestal_w, ped_len_y, height, centered=(False, False, False))
                .translate((ped_x, ped_y, z0))
            )
            head = _rounded_box(
                head_w_y,
                head_len_x,
                head_h,
                min(head_len_x, head_w_y) / 8,
            ).translate((x - head_w_y / 2, y - head_len_x / 2, head_bottom_z))
            root_pad = None
            if root_len > 0 and root_w > 0 and root_h > 0:
                root_x = min(
                    max(bounds["x"], x - root_w / 2),
                    bounds["x"] + bounds["length_x"] - root_w,
                )
                root_y = min(
                    max(bounds["y"], y - root_len / 2),
                    bounds["y"] + bounds["width_y"] - root_len,
                )
                root_pad = (
                    cq.Workplane("XY")
                    .box(root_w, root_len, root_h, centered=(False, False, False))
                    .translate((root_x, root_y, z0 + height - root_h))
                )

        shaft = (
            cq.Workplane("XY")
            .circle(post_d / 2)
            .extrude(shaft_h)
            .translate((x, y, shaft_base_z))
        )
        model = model.union(pedestal)
        if root_pad is not None:
            model = model.union(root_pad)
        model = model.union(shaft).union(head)
    return model


def _add_lid_port_interface(
    cover: cq.Workplane,
    port: dict[str, Any],
    *,
    params: dict[str, Any],
    layout: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    x = float(port["x"])
    y = float(port["y"])
    boss_d = float(port["boss_diameter"])
    boss_h = float(port["boss_height_z"])
    seal_land_w = production.get("port_seal_land_width_xy", 0.0)
    seal_land_h = production.get("port_seal_land_height_z", 0.0)

    if seal_land_w > 0 and seal_land_h > 0:
        cover = cover.union(
            cq.Workplane("XY")
            .circle(boss_d / 2 + seal_land_w)
            .extrude(seal_land_h)
            .translate((x, y, z0))
        )
    cover = cover.union(
        cq.Workplane("XY")
        .circle(boss_d / 2)
            .extrude(boss_h)
            .translate((x, y, z0))
    )
    lip_inner_d = float(port.get("cap_seal_lip_inner_diameter", 0.0))
    lip_outer_d = float(port.get("cap_seal_lip_outer_diameter", 0.0))
    lip_seat_depth = float(port.get("cap_seal_lip_seat_depth_z", 0.0))
    if min(lip_inner_d, lip_outer_d, lip_seat_depth) > 0:
        seal_seat = (
            cq.Workplane("XY")
            .circle(lip_outer_d / 2)
            .extrude(lip_seat_depth + 0.1)
            .translate((x, y, z0 + boss_h - lip_seat_depth - 0.05))
        )
        seal_seat = seal_seat.cut(
            cq.Workplane("XY")
            .circle(lip_inner_d / 2)
            .extrude(lip_seat_depth + 0.2)
            .translate((x, y, z0 + boss_h - lip_seat_depth - 0.1))
        )
        cover = cover.cut(seal_seat)
    return cover


def _add_plate_lateral_locator_rails(
    model: cq.Workplane,
    *,
    tile: dict[str, Any],
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    for rail in _plate_lateral_locator_rectangles(
        tile_origins=[tile],
        params=params,
        z0=z0,
    ):
        model = model.union(
            cq.Workplane("XY")
            .box(
                float(rail["length_x"]),
                float(rail["width_y"]),
                float(rail["height_z"]),
                centered=(False, False, False),
            )
            .translate((float(rail["x"]), float(rail["y"]), float(rail["z"])))
        )
    return model


def _add_plate_support_lands(
    model: cq.Workplane,
    *,
    x0: float,
    y0: float,
    plate_len: float,
    plate_wid: float,
    land_w: float,
    land_h: float,
    z0: float,
) -> cq.Workplane:
    lands = [
        (x0, y0, plate_len, land_w),
        (x0, y0 + plate_wid - land_w, plate_len, land_w),
        (x0, y0 + land_w, land_w, plate_wid - 2 * land_w),
        (x0 + plate_len - land_w, y0 + land_w, land_w, plate_wid - 2 * land_w),
    ]
    for x, y, length, width in lands:
        model = model.union(
            cq.Workplane("XY")
            .box(length, width, land_h, centered=(False, False, False))
            .translate((x, y, z0))
        )
    return model


def _add_pod_frame_keys(
    model: cq.Workplane,
    *,
    tile: dict[str, Any],
    params: dict[str, Any],
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    key_h = production.get("pod_frame_key_height_z", 1.6)
    if key_h <= 0:
        return model

    for key in _pod_frame_key_rectangles(tile_origins=[tile], params=params):
        model = model.union(
            _rounded_box(
                float(key["length_x"]),
                float(key["width_y"]),
                key_h,
                min(float(key["length_x"]), float(key["width_y"])) / 6,
            ).translate((float(key["x"]), float(key["y"]), 0.0))
        )
    return model


def _add_wet_chamber_service_dividers(
    model: cq.Workplane,
    *,
    layout: dict[str, Any],
    params: dict[str, Any],
    z0: float,
    height: float,
) -> cq.Workplane:
    skirt = params["wet_chamber_skirt"]
    bounds = layout["wet_chamber_skirt"]
    wall_w = skirt["wall_thickness"]
    lane_w = skirt.get("service_lane_width", 0.0)
    divider_w = skirt.get("plenum_divider_thickness", 0.0)
    if lane_w <= 0 or divider_w <= 0:
        return model

    if layout["row_axis"] == "y":
        rail_y = bounds["y"] + wall_w
        rail_len = bounds["width_y"] - 2 * wall_w
        x_values = [
            bounds["x"] + wall_w + lane_w,
            bounds["x"] + bounds["length_x"] - wall_w - lane_w - divider_w,
        ]
        for x in x_values:
            model = model.union(
                cq.Workplane("XY")
                .box(divider_w, rail_len, height, centered=(False, False, False))
                .translate((x, rail_y, z0))
            )
        return _cut_wet_chamber_divider_windows(
            model,
            layout=layout,
            params=params,
            rail_positions=x_values,
            rail_axis="y",
            rail_thickness=divider_w,
            z0=z0,
            height=height,
        )

    rail_x = bounds["x"] + wall_w
    rail_len = bounds["length_x"] - 2 * wall_w
    y_values = [
        bounds["y"] + wall_w + lane_w,
        bounds["y"] + bounds["width_y"] - wall_w - lane_w - divider_w,
    ]
    for y in y_values:
        model = model.union(
            cq.Workplane("XY")
            .box(rail_len, divider_w, height, centered=(False, False, False))
            .translate((rail_x, y, z0))
        )
    return _cut_wet_chamber_divider_windows(
        model,
        layout=layout,
        params=params,
        rail_positions=y_values,
        rail_axis="x",
        rail_thickness=divider_w,
        z0=z0,
        height=height,
    )


def _condensation_pocket_rectangles_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    z0: float,
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    pocket_len = float(production.get("condensation_pocket_length_x", 0.0))
    pocket_wid = float(production.get("condensation_pocket_width_y", 0.0))
    pocket_depth = float(production.get("condensation_pocket_depth_z", 0.0))
    if pocket_len <= 0 or pocket_wid <= 0 or pocket_depth <= 0:
        return []

    skirt = params["wet_chamber_skirt"]
    pocket_cut_z = z0 + 0.05
    lane_center_x_values = (
        float(skirt["wall_thickness"]) + float(skirt["service_lane_width"]) / 2,
        float(layout["length_x"])
        - float(skirt["wall_thickness"])
        - float(skirt["service_lane_width"]) / 2,
    )
    y_values = (
        float(skirt["wall_thickness"]) + pocket_wid,
        float(layout["width_y"]) - float(skirt["wall_thickness"]) - 2 * pocket_wid,
    )
    side_names = ("left_service_lane", "right_service_lane")
    edge_names = ("front_low_point", "rear_low_point")
    pockets: list[dict[str, Any]] = []
    for x_idx, center_x in enumerate(lane_center_x_values):
        for y_idx, y in enumerate(y_values):
            pockets.append(
                {
                    "name": (
                        f"condensation_pocket_{side_names[x_idx]}_"
                        f"{edge_names[y_idx]}"
                    ),
                    "kind": "condensation_pocket_low_point",
                    "shape": "rect",
                    "role": "wet_chamber_condensation_low_point_witness",
                    "x": round(center_x - pocket_len / 2, 3),
                    "y": round(y, 3),
                    "z": round(pocket_cut_z, 3),
                    "center_x": round(center_x, 3),
                    "center_y": round(y + pocket_wid / 2, 3),
                    "length_x": round(pocket_len, 3),
                    "width_y": round(pocket_wid, 3),
                    "height_z": round(pocket_depth + 0.05, 3),
                    "nominal_depth_z": round(pocket_depth, 3),
                }
            )
    return pockets


def _cut_condensation_pockets(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    pocket_rects = _condensation_pocket_rectangles_for_layout(
        layout,
        params=params,
        z0=z0,
    )
    if not pocket_rects:
        return model

    for pocket in pocket_rects:
        model = model.cut(
            cq.Workplane("XY")
            .box(
                float(pocket["length_x"]),
                float(pocket["width_y"]),
                float(pocket["height_z"]),
                centered=(True, False, False),
            )
            .translate(
                (
                    float(pocket["center_x"]),
                    float(pocket["y"]),
                    float(pocket["z"]),
                )
            )
        )
    return model


def _cut_deck_key_notch(
    model: cq.Workplane,
    *,
    x: float,
    y: float,
    z: float,
    deck: dict[str, Any],
) -> cq.Workplane:
    return model.cut(
        cq.Workplane("XY")
        .box(
            deck["key_notch_width_x"],
            deck["key_notch_depth_y"] + 0.1,
            deck["key_notch_depth_z"],
            centered=(True, False, False),
        )
        .translate((x, y - 0.05, z - 0.05))
    )


def _cut_locator_relief(
    model: cq.Workplane,
    *,
    x0: float,
    y0: float,
    plate_len: float,
    support: dict[str, Any],
    z: float,
) -> cq.Workplane:
    relief = support["locator_relief_width"]
    depth = support["locator_relief_depth"]
    for x in [x0 + relief, x0 + plate_len - relief]:
        model = model.cut(
            cq.Workplane("XY")
            .box(relief, relief, depth + 0.05, centered=(True, True, False))
            .translate((x, y0 + relief, z))
        )
    return model


def _cut_plate_observation_recess(
    part: cq.Workplane,
    x0: float,
    y0: float,
    plate: dict[str, Any],
    z: float,
) -> cq.Workplane:
    return part.cut(
        cq.Workplane("XY")
        .box(
            plate["observation_window_length_x"],
            plate["observation_window_width_y"],
            0.45,
            centered=(True, True, False),
        )
        .translate((x0 + plate["length_x"] / 2, y0 + plate["width_y"] / 2, z))
    )


def _cut_pod_frame_key_pockets(
    model: cq.Workplane,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    key_h = production.get("pod_frame_key_height_z", 1.6)
    clearance = production.get("pod_frame_key_clearance_xy", 0.25)
    pocket_extra_z = production.get("pod_frame_key_pocket_extra_z", 0.2)
    if key_h <= 0:
        return model

    for key in _pod_frame_key_rectangles(
        tile_origins=layout["tile_origins"],
        params=params,
    ):
        model = model.cut(
            cq.Workplane("XY")
            .box(
                float(key["length_x"]) + 2 * clearance,
                float(key["width_y"]) + 2 * clearance,
                key_h + pocket_extra_z + 0.1,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(key["x"]) - clearance,
                    float(key["y"]) - clearance,
                    -0.05,
                )
            )
        )
    return model


def _cut_septum_lift_notch(
    model: cq.Workplane,
    *,
    access_x: float,
    access_y: float,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    mat = params["septum_mat"]
    lid = params["lid_manifold"]
    notch_width = mat.get("lift_notch_width_x", 0.0)
    notch_depth = mat.get("lift_notch_depth_y", 0.0)
    if notch_width <= 0 or notch_depth <= 0:
        return model

    notch_x = access_x + (_septum_access_window_length(params) - notch_width) / 2
    notch_y = access_y - notch_depth
    return model.cut(
        cq.Workplane("XY")
        .box(
            notch_width,
            notch_depth + 0.1,
            lid["thickness_z"] + lid["duct_height_z"] + 0.4,
            centered=(False, False, False),
        )
        .translate((notch_x, notch_y, z0 - 0.2))
    )


def _cut_septum_slit_reliefs(
    model: cq.Workplane,
    centers: list[tuple[float, float]],
    z0: float,
    mat: dict[str, Any],
) -> cq.Workplane:
    slit_len = mat.get("slit_cut_length_x", 0.0)
    slit_wid = mat.get("slit_cut_width_y", 0.0)
    if slit_len <= 0 or slit_wid <= 0:
        return model

    cut_depth = mat["sheet_thickness_z"] + mat["round_plug_depth_z"] + 0.4
    slits = (
        cq.Workplane("XY")
        .pushPoints(centers)
        .rect(slit_len, slit_wid)
        .extrude(cut_depth)
        .translate((0, 0, z0 - mat["round_plug_depth_z"] - 0.2))
    )
    return model.cut(slits)


def _cut_wet_chamber_divider_windows(
    model: cq.Workplane,
    *,
    layout: dict[str, Any],
    params: dict[str, Any],
    rail_positions: list[float],
    rail_axis: str,
    rail_thickness: float,
    z0: float,
    height: float,
) -> cq.Workplane:
    skirt = params["wet_chamber_skirt"]
    plate = params["plate"]
    window_len = skirt.get("diffuser_window_length", 0.0)
    window_h = skirt.get("diffuser_window_height_z", 0.0)
    top_ligament = skirt.get("diffuser_window_top_ligament_z", 0.0)
    if window_len <= 0 or window_h <= 0:
        return model

    window_z = z0 + max(0.0, height - top_ligament - window_h)
    cut_h = min(window_h, height) + 0.2
    for tile in layout["tile_origins"]:
        if rail_axis == "y":
            center = tile["y"] + plate["width_y"] / 2
            for x in rail_positions:
                model = model.cut(
                    cq.Workplane("XY")
                    .box(
                        rail_thickness + 0.4,
                        window_len,
                        cut_h,
                        centered=(False, False, False),
                    )
                    .translate((x - 0.2, center - window_len / 2, window_z))
                )
        else:
            center = tile["x"] + plate["length_x"] / 2
            for y in rail_positions:
                model = model.cut(
                    cq.Workplane("XY")
                    .box(
                        window_len,
                        rail_thickness + 0.4,
                        cut_h,
                        centered=(False, False, False),
                    )
                    .translate((center - window_len / 2, y - 0.2, window_z))
                )
    return model


def _deck_engagement_foot_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, float | int]]:
    deck = params["deck_interface"]
    foot_len = deck["foot_length_x"]
    foot_wid = deck["foot_width_y"]
    clearance = deck.get("foot_slot_clearance_xy", deck["slot_shoe_clearance_xy"])
    feet: list[dict[str, float | int]] = []

    for tile in tile_origins:
        slot_x, slot_y, slot_len, slot_wid = _deck_slot_opening_for_tile(tile, params)
        x_values = [
            slot_x + clearance,
            slot_x + slot_len - clearance - foot_len,
        ]
        y_values = [
            slot_y + clearance,
            slot_y + slot_wid - clearance - foot_wid,
        ]
        for x in x_values:
            for y in y_values:
                feet.append(
                    {
                        "tile_index": tile["index"],
                        "x": round(x, 3),
                        "y": round(y, 3),
                        "length_x": foot_len,
                        "width_y": foot_wid,
                    }
                )
    return feet


def _latch_post_positions_for_locks(
    locks: list[dict[str, float | str]],
) -> list[dict[str, float | str]]:
    return [
        {
            "x": float(lock["post_x"]),
            "y": float(lock["post_y"]),
            "slide_axis": str(lock["slide_axis"]),
            "insert_from": str(lock["insert_from"]),
        }
        for lock in locks
    ]


def _plate_lateral_locator_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
    z0: float,
) -> list[dict[str, float | int]]:
    plate = params["plate"]
    support = params["plate_support"]
    wall_t = support.get("lateral_locator_wall_thickness", 0.0)
    wall_h = support.get("lateral_locator_wall_height_z", 0.0)
    clearance = support.get("lateral_locator_clearance_xy", 0.0)
    if wall_t <= 0 or wall_h <= 0:
        return []

    rails: list[dict[str, float | int]] = []
    for tile in tile_origins:
        x0 = tile["x"]
        y0 = tile["y"]
        rails.extend(
            [
                {
                    "tile_index": tile.get("index", 0),
                    "x": round(x0 - clearance - wall_t, 3),
                    "y": round(y0 - clearance, 3),
                    "z": round(z0, 3),
                    "length_x": wall_t,
                    "width_y": round(plate["width_y"] + 2 * clearance, 3),
                    "height_z": wall_h,
                },
                {
                    "tile_index": tile.get("index", 0),
                    "x": round(x0 + plate["length_x"] + clearance, 3),
                    "y": round(y0 - clearance, 3),
                    "z": round(z0, 3),
                    "length_x": wall_t,
                    "width_y": round(plate["width_y"] + 2 * clearance, 3),
                    "height_z": wall_h,
                },
                {
                    "tile_index": tile.get("index", 0),
                    "x": round(x0 - clearance - wall_t, 3),
                    "y": round(y0 - clearance - wall_t, 3),
                    "z": round(z0, 3),
                    "length_x": round(plate["length_x"] + 2 * clearance + 2 * wall_t, 3),
                    "width_y": wall_t,
                    "height_z": wall_h,
                },
                {
                    "tile_index": tile.get("index", 0),
                    "x": round(x0 - clearance - wall_t, 3),
                    "y": round(y0 + plate["width_y"] + clearance, 3),
                    "z": round(z0, 3),
                    "length_x": round(plate["length_x"] + 2 * clearance + 2 * wall_t, 3),
                    "width_y": wall_t,
                    "height_z": wall_h,
                },
            ]
        )
    return rails


def _pod_frame_key_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, float | int]]:
    production = params.get("production_assembly", {})
    key_len = production.get("pod_frame_key_length_x", 3.2)
    key_wid = production.get("pod_frame_key_width_y", 5.2)
    keys: list[dict[str, float | int]] = []

    for foot in _deck_engagement_foot_rectangles(
        tile_origins=tile_origins,
        params=params,
    ):
        length = min(key_len, float(foot["length_x"]))
        width = min(key_wid, float(foot["width_y"]))
        keys.append(
            {
                "tile_index": foot["tile_index"],
                "x": round(float(foot["x"]) + (float(foot["length_x"]) - length) / 2, 3),
                "y": round(float(foot["y"]) + (float(foot["width_y"]) - width) / 2, 3),
                "length_x": round(length, 3),
                "width_y": round(width, 3),
            }
        )
    return keys


def _septum_access_window_length(params: dict[str, Any]) -> float:
    mat = params["septum_mat"]
    access = params["pipette_access"]
    grid = params["well_grid"]
    radius = mat["round_plug_diameter"] / 2
    clearance = access["septum_window_clearance_xy"]
    return (grid["columns"] - 1) * grid["pitch_x"] + 2 * (radius + clearance)


def _shared_chamber_bounds(
    layout: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, float]:
    bounds = layout["wet_chamber_skirt"]
    return {
        "x": bounds["x"],
        "y": bounds["y"],
        "length_x": bounds["length_x"],
        "width_y": bounds["width_y"],
    }


def _thermal_condensation_proxy_targets_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    plate_bottom_z: float,
    plate_top_z: float,
    ir_sensor_mounts: list[dict[str, Any]],
    headspace_sht41_mounts: list[dict[str, Any]],
    condensation_pocket_rects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plate = params["plate"]
    grid = params["well_grid"]
    harness = params.get("sensor_harness", {})
    cell_thickness = float(plate.get("cell_plane_check_thickness_z", 0.2))
    ir_thickness = float(harness.get("ir_fov_spot_check_thickness_z", 0.2))
    cell_plane_z = float(plate_top_z) - float(plate["plate_top_to_cell_plane_depth_z"])
    ir_mounts_by_tile = {
        int(mount["tile_index"]): mount
        for mount in ir_sensor_mounts
    }
    sht_mounts_by_tile = {
        int(mount["tile_index"]): mount
        for mount in headspace_sht41_mounts
    }

    targets: list[dict[str, Any]] = []
    for tile in layout["tile_origins"]:
        tile_index = int(tile["index"])
        center_x = (
            float(tile["x"])
            + float(grid["first_well_center_x"])
            + (int(grid["columns"]) - 1) * float(grid["pitch_x"]) / 2
        )
        center_y = (
            float(tile["y"])
            + float(grid["first_well_center_y"])
            + (int(grid["rows"]) - 1) * float(grid["pitch_y"]) / 2
        )
        targets.append(
            {
                "name": f"thermal_cell_plane_center_tile_{tile_index}",
                "kind": "cell_plane_center_reference",
                "shape": "disk",
                "role": "center_cell_plane_reference_for_edge_thermal_correlation",
                "tile_index": tile_index,
                "x": round(center_x, 3),
                "y": round(center_y, 3),
                "z": round(cell_plane_z - cell_thickness / 2, 3),
                "diameter": round(
                    float(plate["well_bottom_area_equivalent_diameter"]),
                    3,
                ),
                "height_z": round(cell_thickness, 3),
            }
        )

        ir_mount = ir_mounts_by_tile.get(tile_index)
        if ir_mount is not None:
            targets.append(
                {
                    "name": f"thermal_ir_proxy_spot_tile_{tile_index}",
                    "kind": "ir_plate_margin_proxy_spot",
                    "shape": "disk",
                    "role": "edge_plate_margin_ir_proxy_for_cell_plane_correlation",
                    "tile_index": tile_index,
                    "x": round(float(ir_mount["center_x"]), 3),
                    "y": round(float(ir_mount["center_y"]), 3),
                    "z": round(float(plate_bottom_z) - ir_thickness / 2, 3),
                    "diameter": round(float(ir_mount["fov_spot_diameter"]), 3),
                    "height_z": round(ir_thickness, 3),
                    "fov_angle_degrees": float(ir_mount["fov_angle_degrees"]),
                }
            )

        sht_mount = sht_mounts_by_tile.get(tile_index)
        if sht_mount is not None:
            ring = sht_mount["drip_break_ring"]
            targets.append(
                {
                    "name": f"thermal_sht41_headspace_point_tile_{tile_index}",
                    "kind": "sht41_headspace_aperture_drip_ring",
                    "shape": "disk",
                    "role": "local_headspace_temperature_humidity_point",
                    "tile_index": tile_index,
                    "x": round(float(sht_mount["aperture_x"]), 3),
                    "y": round(float(sht_mount["aperture_y"]), 3),
                    "z": round(float(ring["z"]), 3),
                    "diameter": round(float(ring["outer_diameter"]), 3),
                    "height_z": round(float(ring["height_z"]), 3),
                    "aperture_diameter": round(
                        float(sht_mount["aperture_diameter"]),
                        3,
                    ),
                }
            )

    for pocket in condensation_pocket_rects:
        targets.append(
            {
                **pocket,
                "role": "condensation_low_point_witness_for_gate6_review",
            }
        )
    return targets


def _well_grid_rectangle_for_tile(
    tile: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, float | int]:
    centers = _well_centers_for_tile(tile, params)
    xs = [point[0] for point in centers]
    ys = [point[1] for point in centers]
    return {
        "tile_index": tile.get("index", 0),
        "x": round(min(xs), 3),
        "y": round(min(ys), 3),
        "length_x": round(max(xs) - min(xs), 3),
        "width_y": round(max(ys) - min(ys), 3),
    }


def build_deck_pods(params: dict[str, Any]) -> cq.Workplane:
    layout = row_coupon_layout(params)
    deck = params["deck_interface"]
    pods: cq.Workplane | None = None
    for tile in layout["tile_origins"]:
        x, y, _, _ = _deck_slot_opening_for_tile(tile, params)
        clearance = deck["slot_shoe_clearance_xy"]
        shoe = _rounded_box(
            deck["slot_opening_length_x"] - 2 * clearance,
            deck["slot_opening_width_y"] - 2 * clearance,
            deck["slot_shoe_thickness_z"],
            deck["slot_shoe_corner_radius"],
        ).translate((x + clearance, y + clearance, layout["deck_plane_z"]))
        pod = _add_deck_engagement_feet(shoe, tile=tile, params=params)
        pod = _add_pod_frame_keys(pod, tile=tile, params=params)
        pods = pod if pods is None else pods.union(pod)
    if pods is None:
        raise ValueError("row coupon requires at least one deck pod")
    return pods


def build_lid_cover(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    from aevum_cad.row_coupon import (_add_gas_sensor_pcb_sockets, _add_lid_cover_tongue, _add_sample_relief_leak_witness_features, _add_side_gas_service_features, _add_wedge_receiver_rails, _cut_lid_sensor_harness_channels)
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    lid = params["lid_manifold"]
    row = params["row"]
    z0 = layout["lid_top_z"] if assembly_position else 0.0
    duct_h = lid["duct_height_z"]
    duct_w = lid["duct_width_y"]

    cover: cq.Workplane | None = None
    if layout["row_axis"] == "x":
        front_duct_y = row["side_margin_y"] - duct_w / 2
        rear_duct_y = layout["width_y"] - row["side_margin_y"] - duct_w / 2
        duct_length_x = layout["length_x"] - 2 * row["end_margin_x"]
        segments = [
            (row["end_margin_x"], front_duct_y, duct_length_x, duct_w),
            (row["end_margin_x"], rear_duct_y, duct_length_x, duct_w),
            (row["end_margin_x"], front_duct_y, duct_w, rear_duct_y - front_duct_y + duct_w),
            (
                layout["length_x"] - row["end_margin_x"] - duct_w,
                front_duct_y,
                duct_w,
                rear_duct_y - front_duct_y + duct_w,
            ),
        ]
    else:
        left_duct_x = row["end_margin_x"] - duct_w / 2
        right_duct_x = layout["length_x"] - row["end_margin_x"] - duct_w / 2
        duct_length_y = layout["width_y"] - 2 * row["side_margin_y"]
        segments = [
            (left_duct_x, row["side_margin_y"], duct_w, duct_length_y),
            (right_duct_x, row["side_margin_y"], duct_w, duct_length_y),
            (left_duct_x, row["side_margin_y"], right_duct_x - left_duct_x + duct_w, duct_w),
            (
                left_duct_x,
                layout["width_y"] - row["side_margin_y"] - duct_w,
                right_duct_x - left_duct_x + duct_w,
                duct_w,
            ),
        ]

    for x, y, length, width in segments:
        segment = (
            cq.Workplane("XY")
            .box(length, width, duct_h, centered=(False, False, False))
            .translate((x, y, z0))
        )
        cover = segment if cover is None else cover.union(segment)
    if cover is None:
        raise ValueError("lid cover requires at least one segment")

    cover = _add_lid_cover_tongue(cover, params=params, z0=z0)

    for port in _lid_port_positions(layout, params):
        cover = _add_lid_port_interface(cover, port, params=params, layout=layout, z0=z0)
        cover = cover.cut(
            cq.Workplane("XY")
            .circle(float(port["hole_diameter"]) / 2)
            .extrude(max(duct_h, float(port["boss_height_z"])) + 0.4)
            .translate((float(port["x"]), float(port["y"]), z0 - 0.2))
        )

    cover = _add_sample_relief_leak_witness_features(
        cover,
        params=params,
        assembly_position=assembly_position,
    )
    cover = _add_side_gas_service_features(
        cover,
        params=params,
        assembly_position=assembly_position,
    )

    stop_size = seal["compression_stop_size"]
    stop_h = seal["compression_stop_pad_height_z"]
    stop_hole_d = seal["compression_stop_clearance_hole_diameter"]
    for x, y in _compression_stop_positions(params):
        cover = cover.union(
            cq.Workplane("XY")
            .box(stop_size, stop_size, stop_h, centered=(True, True, False))
            .translate((x, y, z0))
        )
        cover = cover.cut(
            cq.Workplane("XY")
            .circle(stop_hole_d / 2)
            .extrude(max(duct_h, stop_h) + 0.4)
            .translate((x, y, z0 - 0.2))
        )
    cover = _add_wedge_receiver_rails(cover, params=params, z0=z0)
    cover = _add_gas_sensor_pcb_sockets(
        cover,
        params=params,
        assembly_position=assembly_position,
    )
    cover = _cut_lid_sensor_harness_channels(
        cover,
        params=params,
        owner_part="lid_cover",
        assembly_position=assembly_position,
    )
    return cover


def build_lid_manifold_shell(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    from aevum_cad.row_coupon import (_add_gasket_tab_leak_witness_features, _add_headspace_sht41_sockets, _cut_gasket_capture_groove, _cut_lid_cover_tongue_groove, _cut_lid_sensor_harness_channels)
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    lid = params["lid_manifold"]
    plate = params["plate"]
    mat = params["septum_mat"]
    access = params["pipette_access"]
    z0 = layout["lid_bottom_z"] if assembly_position else 0.0

    model = _rounded_box(
        layout["length_x"],
        layout["width_y"],
        lid["thickness_z"],
        lid["corner_radius"],
    ).translate((0, 0, z0))

    chamber = _shared_chamber_bounds(layout, params)
    rail_w = seal["gasket_rail_width"]
    model = model.cut(
        cq.Workplane("XY")
        .box(
            chamber["length_x"] - 2 * rail_w,
            chamber["width_y"] - 2 * rail_w,
            seal["headspace_recess_depth_z"] + 0.2,
            centered=(False, False, False),
        )
        .translate((chamber["x"] + rail_w, chamber["y"] + rail_w, z0 - 0.1))
    )

    seat_clearance = mat.get("seat_clearance_xy", 0.0)
    seat_depth = mat.get("seat_pocket_depth_z", 0.0)
    if seat_depth > 0:
        for tile in layout["tile_origins"]:
            model = model.cut(
                cq.Workplane("XY")
                .box(
                    plate["length_x"] + 2 * seat_clearance,
                    plate["width_y"] + 2 * seat_clearance,
                    seat_depth + 0.2,
                    centered=(False, False, False),
                )
                .translate(
                    (
                        tile["x"] - seat_clearance,
                        tile["y"] - seat_clearance,
                        z0 - 0.1,
                    )
                )
            )

    if access.get("septum_window_enabled", False):
        for tile in layout["tile_origins"]:
            x, y, length, width = _septum_access_window_for_tile(tile, params)
            model = model.cut(
                cq.Workplane("XY")
                .box(
                    length,
                    width,
                    lid["thickness_z"] + lid["duct_height_z"] + 0.4,
                    centered=(False, False, False),
                )
                .translate((x, y, z0 - 0.2))
            )
            model = _cut_septum_lift_notch(
                model,
                access_x=x,
                access_y=y,
                params=params,
                z0=z0,
            )

    duct_h = lid["duct_height_z"]
    port_positions = _lid_port_positions(layout, params)
    for port in port_positions:
        model = model.cut(
            cq.Workplane("XY")
            .circle(float(port["hole_diameter"]) / 2)
            .extrude(lid["thickness_z"] + max(duct_h, float(port["boss_height_z"])) + 0.4)
            .translate((float(port["x"]), float(port["y"]), z0 - 0.2))
        )

    stop_h = seal["compression_stop_pad_height_z"]
    stop_hole_d = seal["compression_stop_clearance_hole_diameter"]
    for x, y in _compression_stop_positions(params):
        model = model.cut(
            cq.Workplane("XY")
            .circle(stop_hole_d / 2)
            .extrude(lid["thickness_z"] + stop_h + 0.4)
            .translate((x, y, z0 - 0.2))
        )

    model = _cut_gasket_capture_groove(
        model,
        params=params,
        z0=z0,
        from_side="bottom",
    )
    model = _add_gasket_tab_leak_witness_features(
        model,
        params=params,
        owner_part="lid_manifold_shell",
        z_shift=0.0 if assembly_position else -layout["lid_bottom_z"],
    )
    model = _cut_lid_cover_tongue_groove(model, params=params, z0=z0)

    for tile in layout["tile_origins"]:
        if layout["row_axis"] == "x":
            x_center = tile["x"] + plate["length_x"] / 2
            supply_y = tile["y"] + plate["width_y"] - lid["diffuser_offset_from_plate_edge_y"]
            return_y = tile["y"] + lid["diffuser_offset_from_plate_edge_y"]
            for slot_x in _slot_centers(
                x_center,
                lid["diffuser_slot_count_per_tile"],
                lid["diffuser_slot_length_x"],
            ):
                for slot_y in [supply_y, return_y]:
                    model = model.cut(
                        cq.Workplane("XY")
                        .box(
                            lid["diffuser_slot_length_x"],
                            lid["diffuser_slot_width_y"],
                            lid["thickness_z"] + duct_h + 0.4,
                            centered=(True, True, False),
                        )
                        .translate((slot_x, slot_y, z0 - 0.2))
                    )
        else:
            y_center = tile["y"] + plate["width_y"] / 2
            supply_x = tile["x"] + lid["diffuser_offset_from_plate_edge_x"]
            return_x = tile["x"] + plate["length_x"] - lid["diffuser_offset_from_plate_edge_x"]
            for slot_y in _slot_centers(
                y_center,
                lid["diffuser_slot_count_per_tile"],
                lid["diffuser_slot_length_x"],
            ):
                for slot_x in [supply_x, return_x]:
                    model = model.cut(
                        cq.Workplane("XY")
                        .box(
                            lid["diffuser_slot_width_y"],
                            lid["diffuser_slot_length_x"],
                            lid["thickness_z"] + duct_h + 0.4,
                            centered=(True, True, False),
                        )
                        .translate((slot_x, slot_y, z0 - 0.2))
                    )
        for target in access.get("targets", []):
            if not access.get("septum_window_enabled", False):
                model = model.cut(
                    cq.Workplane("XY")
                    .circle(access.get("hole_diameter", 4.2) / 2)
                    .extrude(lid["thickness_z"] + duct_h + 0.4)
                    .translate(
                        (
                            tile["x"] + target["local_x"] + target.get("offset_x", 0.0),
                            tile["y"] + target["local_y"] + target.get("offset_y", 0.0),
                            z0 - 0.2,
                        )
                        )
                    )
    model = _add_headspace_sht41_sockets(
        model,
        params=params,
        assembly_position=assembly_position,
    )
    model = _cut_lid_sensor_harness_channels(
        model,
        params=params,
        owner_part="lid_manifold_shell",
        assembly_position=assembly_position,
    )
    return model


def build_microplates(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    plate = params["plate"]
    z0 = layout["plate_bottom_z"] if assembly_position else 0.0
    sidewall_w = plate["sidewall_thickness"]
    window_h = plate["bottom_window_thickness_z"]
    top_recess_h = plate.get("well_top_recess_depth_z", 0.0)
    well_opening_d = plate.get("upper_well_diameter", 0.0)

    microplates: cq.Workplane | None = None
    for tile in layout["tile_origins"]:
        part = _perimeter_rails(
            x0=tile["x"],
            y0=tile["y"],
            length=plate["length_x"],
            width=plate["width_y"],
            rail_width=sidewall_w,
            height=plate["height_z"],
            z0=z0,
        )
        window = (
            cq.Workplane("XY")
            .box(
                plate["observation_window_length_x"],
                plate["observation_window_width_y"],
                window_h,
                centered=(True, True, False),
            ).translate(
                (
                    tile["x"] + plate["length_x"] / 2,
                    tile["y"] + plate["width_y"] / 2,
                    z0,
                )
            )
        )
        part = part.union(window)
        if top_recess_h > 0:
            top_deck = (
                cq.Workplane("XY")
                .box(
                    plate["length_x"] - 2 * sidewall_w,
                    plate["width_y"] - 2 * sidewall_w,
                    top_recess_h,
                    centered=(False, False, False),
                )
                .translate(
                    (
                        tile["x"] + sidewall_w,
                        tile["y"] + sidewall_w,
                        z0 + plate["height_z"] - top_recess_h,
                    )
                )
            )
            if well_opening_d > 0:
                well_openings = (
                    cq.Workplane("XY")
                    .pushPoints(_well_centers_for_tile(tile, params))
                    .circle(well_opening_d / 2)
                    .extrude(top_recess_h + 0.2)
                    .translate((0, 0, z0 + plate["height_z"] - top_recess_h - 0.1))
                )
                top_deck = top_deck.cut(well_openings)
            part = part.union(top_deck)
        microplates = part if microplates is None else microplates.union(part)
    if microplates is None:
        raise ValueError("row coupon requires at least one microplate")
    return microplates


def build_plate_support_frame(params: dict[str, Any]) -> cq.Workplane:
    from aevum_cad.row_coupon import (_add_dry_bay_aperture_thresholds, _add_gasket_tab_leak_witness_features, _add_ir_aperture_drip_collars, _add_ir_sensor_retention_lips, _cut_dry_bay, _cut_gasket_capture_groove, _cut_ir_sensor_pockets_and_apertures, _cut_lower_sensor_harness_channels, _cut_observer_fiducials, _cut_wet_dry_witness_gutters)
    layout = row_coupon_layout(params)
    base = params["base"]
    plate = params["plate"]
    support = params["plate_support"]
    bay = params["dry_bay"]
    length = layout["length_x"]
    width = layout["width_y"]
    base_h = base["thickness_z"]
    land_w = support["land_width"]
    land_h = support["land_height_z"]
    plate_len = plate["length_x"]
    plate_wid = plate["width_y"]

    model = _rounded_box(length, width, base_h, base["corner_radius"])

    for tile in layout["tile_origins"]:
        x0 = tile["x"]
        y0 = tile["y"]
        model = _add_plate_support_lands(
            model,
            x0=x0,
            y0=y0,
            plate_len=plate_len,
            plate_wid=plate_wid,
            land_w=land_w,
            land_h=land_h,
            z0=base_h,
        )
        model = _add_plate_lateral_locator_rails(
            model,
            tile=tile,
            params=params,
            z0=base_h + land_h,
        )
        model = _cut_dry_bay(
            model,
            x0=x0,
            y0=y0,
            plate_len=plate_len,
            plate_wid=plate_wid,
            base_h=base_h,
            land_h=land_h,
            bay=bay,
        )
        model = _cut_locator_relief(
            model,
            x0=x0,
            y0=y0,
            plate_len=plate_len,
            support=support,
            z=base_h + land_h - support["locator_relief_depth"],
        )
        model = _cut_observer_fiducials(
            model,
            x0=x0,
            y0=y0,
            plate_len=plate_len,
            plate_wid=plate_wid,
            bay=bay,
        )

    model = _cut_wet_dry_witness_gutters(model, params=params)
    model = _add_dry_bay_aperture_thresholds(model, params=params)
    model = _add_gasket_tab_leak_witness_features(
        model,
        params=params,
        owner_part="plate_support_frame",
    )
    model = _cut_pod_frame_key_pockets(model, params)
    model = _cut_ir_sensor_pockets_and_apertures(model, params=params)
    model = _add_ir_aperture_drip_collars(model, params=params)
    model = _cut_lower_sensor_harness_channels(model, params=params)
    model = _add_ir_sensor_retention_lips(model, params=params)
    model = _cut_gasket_capture_groove(
        model,
        params=params,
        z0=base_h,
        from_side="top",
    )
    return model


def build_septum_mat_inserts(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    plate = params["plate"]
    mat = params["septum_mat"]
    z0 = layout["plate_top_z"] if assembly_position else 0.0

    mats: cq.Workplane | None = None
    for tile in layout["tile_origins"]:
        sheet = _rounded_box(
            plate["length_x"],
            plate["width_y"],
            mat["sheet_thickness_z"],
            mat["sheet_corner_radius"],
        ).translate((tile["x"], tile["y"], z0))

        centers = _well_centers_for_tile(tile, params)
        plugs = (
            cq.Workplane("XY")
            .pushPoints(centers)
            .circle(mat["round_plug_diameter"] / 2)
            .extrude(mat["round_plug_depth_z"] + 0.1)
            .translate((0, 0, z0 - mat["round_plug_depth_z"]))
        )
        part = sheet.union(plugs)
        part = _cut_septum_slit_reliefs(part, centers, z0, mat)
        mats = part if mats is None else mats.union(part)
    if mats is None:
        raise ValueError("row coupon requires at least one septum mat insert")
    return mats


def build_wet_chamber_frame(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    return build_wet_chamber_skirt(params, assembly_position=assembly_position)


def build_wet_chamber_skirt(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    from aevum_cad.row_coupon import (_cut_gasket_capture_groove)
    layout = row_coupon_layout(params)
    skirt = params["wet_chamber_skirt"]
    bounds = layout["wet_chamber_skirt"]
    z0 = bounds["bottom_z"] if assembly_position else 0.0

    model = _perimeter_rails(
        x0=bounds["x"],
        y0=bounds["y"],
        length=bounds["length_x"],
        width=bounds["width_y"],
        rail_width=skirt["wall_thickness"],
        height=bounds["height_z"],
        z0=z0,
    )
    radius = skirt.get("corner_radius", 0.0)
    if radius > 0:
        model = model.edges("|Z").fillet(radius)
    model = _cut_gasket_capture_groove(
        model,
        params=params,
        z0=z0,
        from_side="bottom",
    )
    model = _cut_gasket_capture_groove(
        model,
        params=params,
        z0=z0 + bounds["height_z"],
        from_side="top",
    )
    model = _cut_condensation_pockets(model, params=params, z0=z0)
    model = _add_wet_chamber_service_dividers(
        model,
        layout=layout,
        params=params,
        z0=z0,
        height=bounds["height_z"],
    )
    model = _add_latch_tension_posts(
        model,
        layout=layout,
        params=params,
        z0=z0,
        height=bounds["height_z"],
    )
    return model
