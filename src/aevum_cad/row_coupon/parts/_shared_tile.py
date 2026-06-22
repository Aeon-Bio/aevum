from __future__ import annotations

from typing import Any


def _well_centers_for_tile(
    tile: dict[str, Any],
    params: dict[str, Any],
) -> list[tuple[float, float]]:
    grid = params["well_grid"]
    centers: list[tuple[float, float]] = []
    for row_idx in range(grid["rows"]):
        for col_idx in range(grid["columns"]):
            centers.append(
                (
                    tile["x"] + grid["first_well_center_x"] + col_idx * grid["pitch_x"],
                    tile["y"] + grid["first_well_center_y"] + row_idx * grid["pitch_y"],
                )
            )
    return centers
def _septum_access_window_for_tile(
    tile: dict[str, Any],
    params: dict[str, Any],
) -> tuple[float, float, float, float]:
    mat = params["septum_mat"]
    access = params["pipette_access"]
    centers = _well_centers_for_tile(tile, params)
    xs = [point[0] for point in centers]
    ys = [point[1] for point in centers]
    radius = mat["round_plug_diameter"] / 2
    clearance = access["septum_window_clearance_xy"]
    x0 = min(xs) - radius - clearance
    x1 = max(xs) + radius + clearance
    y0 = min(ys) - radius - clearance
    y1 = max(ys) + radius + clearance
    return x0, y0, x1 - x0, y1 - y0
def _deck_slot_opening_for_tile(
    tile: dict[str, Any],
    params: dict[str, Any],
) -> tuple[float, float, float, float]:
    deck = params["deck_interface"]
    plate = params["plate"]
    slot_len = deck["slot_opening_length_x"]
    slot_wid = deck["slot_opening_width_y"]
    x = tile["x"] + (plate["length_x"] - slot_len) / 2
    y = tile["y"] + (plate["width_y"] - slot_wid) / 2
    return x, y, slot_len, slot_wid
def _lid_port_spec(
    *,
    name: str,
    role: str,
    x: float,
    y: float,
    boss_d: float,
    hole_d: float,
    boss_h: float,
    params: dict[str, Any],
) -> dict[str, Any]:
    production = params.get("production_assembly", {})
    cap_clearance = production.get("port_cap_plug_clearance_diameter", 0.0)
    cap_overhang = production.get("port_cap_flange_overhang_xy", 0.0)
    lip_w = production.get("port_cap_seal_lip_width_xy", 0.0)
    lip_h = production.get("port_cap_seal_lip_height_z", 0.0)
    lip_compression = production.get("port_cap_seal_lip_nominal_compression_z", 0.0)
    lip_inner_d = hole_d + cap_clearance
    lip_outer_d = min(lip_inner_d + 2 * lip_w, boss_d)
    if lip_h > 0 and lip_compression >= lip_h:
        raise ValueError("port cap seal lip compression must be smaller than lip height")
    if lip_h > 0 and lip_w > 0 and lip_outer_d <= lip_inner_d:
        raise ValueError("port cap seal lip must fit inside the boss seal land")
    lip_seat_depth = max(lip_h - lip_compression, 0.0)
    return {
        "name": name,
        "role": role,
        "x": x,
        "y": y,
        "boss_diameter": boss_d,
        "hole_diameter": hole_d,
        "boss_height_z": boss_h,
        "cap_plug_diameter": max(hole_d - cap_clearance, 0.2),
        "cap_flange_diameter": boss_d + 2 * cap_overhang,
        "cap_seal_lip_inner_diameter": round(lip_inner_d, 3),
        "cap_seal_lip_outer_diameter": round(lip_outer_d, 3),
        "cap_seal_lip_height_z": round(lip_h, 3),
        "cap_seal_lip_seat_depth_z": round(lip_seat_depth, 3),
        "cap_seal_lip_nominal_compression_z": round(lip_compression, 3),
        "cap_seal_lip_role": "integrated_compliant_lip_on_sample_relief_boss_top",
    }
def _lid_port_positions(
    layout: dict[str, Any],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    row = params["row"]
    lid = params["lid_manifold"]
    duct_w = lid["duct_width_y"]
    port_positions: list[dict[str, Any]] = []
    if layout["row_axis"] == "x":
        rear_duct_y = layout["width_y"] - row["side_margin_y"] - duct_w / 2
        port_positions.append(
            _lid_port_spec(
                name="sample_relief",
                role="sample_relief",
                x=layout["length_x"] / 2,
                y=rear_duct_y + duct_w / 2,
                boss_d=lid.get("sample_port_boss_diameter", 10.0),
                hole_d=lid.get("sample_port_hole_diameter", 3.0),
                boss_h=lid.get("sample_port_boss_height_z", 5.0),
                params=params,
            )
        )
        return port_positions

    right_duct_x = layout["length_x"] - row["end_margin_x"] - duct_w / 2
    port_positions.append(
        _lid_port_spec(
            name="sample_relief",
            role="sample_relief",
            x=right_duct_x + duct_w / 2,
            y=layout["width_y"] / 2,
            boss_d=lid.get("sample_port_boss_diameter", 10.0),
            hole_d=lid.get("sample_port_hole_diameter", 3.0),
            boss_h=lid.get("sample_port_boss_height_z", 5.0),
            params=params,
        )
    )
    return port_positions
