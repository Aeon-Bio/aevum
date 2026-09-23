from __future__ import annotations

from typing import Any

import cadquery as cq

from ..layout import row_coupon_layout
from ._geom_base import _boxes_from_rectangles, _harness_z_shift, _rectangles_bounding_extents


def _add_harness_snap_tabs(
    model: cq.Workplane,
    trunk: dict[str, Any],
    *,
    params: dict[str, Any],
    underside: bool,
    z_shift: float = 0.0,
) -> cq.Workplane:
    harness = params["sensor_harness"]
    pitch = harness["snap_tab_pitch_y"]
    tab_len = harness["snap_tab_length_y"]
    tab_w = harness["snap_tab_width_x"]
    cover_h = harness["cover_height_z"]
    layout = row_coupon_layout(params)
    y = float(trunk["y"]) + pitch / 2
    y_end = float(trunk["y"]) + float(trunk["width_y"]) - tab_len
    if underside:
        z = float(trunk["z"]) + z_shift - cover_h
    else:
        z = float(trunk["z"]) + z_shift + float(trunk["height_z"])
    while y <= y_end:
        x_candidates = [
            float(trunk["x"]) - tab_w,
            float(trunk["x"]) + float(trunk["length_x"]),
        ]
        for x in x_candidates:
            if x < 0 or x + tab_w > float(layout["length_x"]):
                continue
            model = model.union(
                cq.Workplane("XY")
                .box(tab_w, tab_len, cover_h, centered=(False, False, False))
                .translate((x, y, z))
            )
        y += pitch
    return model


def _lower_cover_trunk(params: dict[str, Any]) -> dict[str, Any]:
    """Return the lower cover trunk stopped before the connector tool lane."""

    layout = row_coupon_layout(params)
    trunk = dict(layout["lower_ir_harness_trunk"])
    connector = layout["lower_ir_connector_envelope"]
    shroud = connector["printed_shroud"]
    harness = params["sensor_harness"]
    key_y = float(shroud["y"]) - float(connector["key_rib_rect"]["width_y"])
    clearance = float(harness["lower_connector_cover_clearance_y"])
    cover_overlap = float(harness["cover_overlap_xy"])
    trunk["width_y"] = round(
        min(float(shroud["y"]), key_y)
        - clearance
        - cover_overlap
        - float(trunk["y"]),
        3,
    )
    return trunk


def _lower_cover_hook_rectangles(params: dict[str, Any]) -> list[dict[str, float]]:
    harness = params["sensor_harness"]
    trunk = _lower_cover_trunk(params)
    pitch = float(harness["snap_tab_pitch_y"])
    tab_len = float(harness["snap_tab_length_y"])
    hook_w = float(harness["lower_cover_hook_width_x"])
    hook_len = float(harness["lower_cover_hook_length_y"])
    hook_h = float(harness["lower_cover_hook_height_z"])
    embed = float(harness["lower_cover_hook_embed_z"])
    x = float(trunk["x"]) + float(trunk["length_x"]) + float(harness["snap_tab_width_x"]) - hook_w
    y = float(trunk["y"]) + pitch / 2
    y_end = float(trunk["y"]) + float(trunk["width_y"]) - tab_len
    rects: list[dict[str, float]] = []
    while y <= y_end:
        rects.append(
            {
                "x": x,
                "y": y + (tab_len - hook_len) / 2,
                "z": float(trunk["z"]) - embed,
                "length_x": hook_w,
                "width_y": hook_len,
                "height_z": hook_h,
            }
        )
        y += pitch
    return rects


def _lower_shroud_mount_rectangles(params: dict[str, Any]) -> list[dict[str, float]]:
    harness = params["sensor_harness"]
    connector = row_coupon_layout(params)["lower_ir_connector_envelope"]
    shroud = connector["printed_shroud"]
    board = connector["board_rect"]
    lug_l = float(harness["lower_shroud_mount_lug_length_x"])
    lug_w = float(harness["lower_shroud_mount_lug_width_y"])
    lug_h = float(harness["lower_shroud_mount_lug_height_z"])
    embed = float(harness["lower_shroud_mount_lug_embed_z"])
    top = (
        float(board["z"])
        + float(board["height_z"])
        + float(shroud["height_z"])
    )
    span = float(shroud["length_x"])
    return [
        {
            "x": float(shroud["x"]) + span * fraction - lug_l / 2,
            "y": float(shroud["y"]),
            "z": top - embed,
            "length_x": lug_l,
            "width_y": lug_w,
            "height_z": lug_h,
        }
        for fraction in (0.55, 0.8)
    ]


def _cut_rect_receptacles(
    model: cq.Workplane,
    rects: list[dict[str, float]],
    *,
    clearance_xy: float,
    clearance_z: float,
) -> cq.Workplane:
    for rect in rects:
        model = model.cut(
            cq.Workplane("XY")
            .box(
                rect["length_x"] + 2 * clearance_xy,
                rect["width_y"] + 2 * clearance_xy,
                rect["height_z"] + clearance_z,
                centered=(False, False, False),
            )
            .translate(
                (
                    rect["x"] - clearance_xy,
                    rect["y"] - clearance_xy,
                    rect["z"],
                )
            )
        )
    return model


def _cut_lower_cover_hook_receptacles(
    model: cq.Workplane, *, params: dict[str, Any]
) -> cq.Workplane:
    harness = params["sensor_harness"]
    return _cut_rect_receptacles(
        model,
        _lower_cover_hook_rectangles(params),
        clearance_xy=float(harness["lower_cover_hook_clearance_xy"]),
        clearance_z=float(harness["lower_cover_hook_clearance_z"]),
    )


def _cut_lower_shroud_mount_receptacles(
    model: cq.Workplane, *, params: dict[str, Any]
) -> cq.Workplane:
    harness = params["sensor_harness"]
    model = _cut_rect_receptacles(
        model,
        _lower_shroud_mount_rectangles(params),
        clearance_xy=float(harness["lower_shroud_mount_clearance_xy"]),
        clearance_z=float(harness["lower_shroud_mount_clearance_z"]),
    )
    # The lower support also needs the complete above-datum shroud insertion
    # envelope.  Cutting the U-profile piecemeal left its side rails embedded
    # in the frame when the guard height changed.
    connector = row_coupon_layout(params)["lower_ir_connector_envelope"]
    shroud = connector["printed_shroud"]
    key = connector["key_rib_rect"]
    board = connector["board_rect"]
    clearance = float(harness["lower_shroud_mount_clearance_xy"])
    key_y = float(shroud["y"]) - float(key["width_y"])
    insertion_rect = {
        "x": float(shroud["x"]),
        "y": min(float(shroud["y"]), key_y),
        "z": 0.0,
        "length_x": float(shroud["length_x"]),
        "width_y": (
            float(shroud["y"])
            + float(shroud["width_y"])
            - min(float(shroud["y"]), key_y)
        ),
        "height_z": max(
            0.0,
            float(board["z"])
            + float(board["height_z"])
            + float(shroud["height_z"]),
        ),
    }
    return _cut_rect_receptacles(
        model,
        [insertion_rect],
        clearance_xy=clearance,
        clearance_z=float(harness["lower_shroud_mount_clearance_z"]),
    )


def _build_printed_sensor_connector_shrouds(
    connectors: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    z_shift: float = 0.0,
    emit_grip_rib: bool = False,
    grip_rib_width_y: float = 2.0,
    grip_rib_y_offset: float = 0.0,
) -> cq.Workplane:
    model: cq.Workplane | None = None
    for connector in connectors:
        shroud = connector["printed_shroud"]
        wall = float(shroud["wall_xy"])
        x = float(shroud["x"])
        y = float(shroud["y"])
        # The shroud is a removable guard, not a socket around the carrier PCB.
        # Start it above the PCB plane so the printed walls never consume the
        # COTS board volume during installation/removal.
        board = connector["board_rect"]
        z = float(board["z"]) + float(board["height_z"]) + z_shift
        length = float(shroud["length_x"])
        width = float(shroud["width_y"])
        height = float(shroud["height_z"])
        rails = (
            cq.Workplane("XY")
            .box(wall, width, height, centered=(False, False, False))
            .translate((x, y, z))
            .union(
                cq.Workplane("XY")
                .box(wall, width, height, centered=(False, False, False))
                .translate((x + length - wall, y, z))
            )
            .union(
                cq.Workplane("XY")
                .box(length, wall, height, centered=(False, False, False))
                .translate((x, y, z))
            )
        )
        key = connector["key_rib_rect"]
        # Put the tactile key on the outside of the closed (-Y) wall.  The old
        # placement projected through the connector body itself.
        key_y = y - float(key["width_y"]) + min(0.1, wall / 4)
        rails = rails.union(
            cq.Workplane("XY")
            .box(
                float(key["length_x"]),
                float(key["width_y"]),
                float(key["height_z"]),
                centered=(False, False, False),
            )
            .translate((float(key["x"]), key_y, z))
        )
        if emit_grip_rib:
            rails = rails.union(
                cq.Workplane("XY")
                .box(
                    float(key["length_x"]),
                    float(grip_rib_width_y),
                    float(key["height_z"]),
                    centered=(False, False, False),
                )
                .translate(
                    (
                        float(key["x"]),
                        key_y - float(grip_rib_y_offset),
                        z,
                    )
                )
            )
        model = rails if model is None else model.union(rails)
    if model is None:
        raise ValueError("sensor connector shroud model requires at least one connector")
    return model


def _cut_lower_shroud_harness_entry(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
    z_shift: float,
) -> cq.Workplane:
    """Open the lower shroud's closed wall for its fixed cable bundle.

    The connector unmates toward +Y while its harness approaches from -Y.
    Without this low notch, the already-wired harness passes through solid
    shroud wall material and the guard cannot be installed.
    """

    layout = row_coupon_layout(params)
    connector = layout["lower_ir_connector_envelope"]
    shroud = connector["printed_shroud"]
    key = connector["key_rib_rect"]
    trunk = layout["lower_ir_harness_trunk"]
    clearance = float(params["sensor_harness"]["channel_clearance_xy"])
    wall_y = float(shroud["y"])
    key_y = wall_y - float(key["width_y"]) + min(0.1, float(shroud["wall_xy"]) / 4)
    z0 = float(trunk["z"]) + z_shift
    notch = (
        cq.Workplane("XY")
        .box(
            float(trunk["length_x"]) + 2 * clearance,
            wall_y + float(shroud["wall_xy"]) - key_y + 2 * clearance,
            float(trunk["height_z"]) + 2 * clearance,
            centered=(False, False, False),
        )
        .translate(
            (
                float(trunk["x"]) - clearance,
                key_y - clearance,
                z0 - clearance,
            )
        )
    )
    return model.cut(notch)


def _build_sensor_service_connector_models(
    connectors: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    z_shift: float = 0.0,
) -> cq.Workplane:
    model: cq.Workplane | None = None
    for connector in connectors:
        rects = [
            connector["board_rect"],
            connector["header_rect"],
            connector["plug_rect"],
            connector["latch_rect"],
        ]
        part = _boxes_from_rectangles(rects, z_shift=z_shift)
        marker = connector["pin1_marker"]
        part = part.union(
            cq.Workplane("XY")
            .circle(float(marker["diameter"]) / 2)
            .extrude(float(marker["height_z"]))
            .translate((float(marker["x"]), float(marker["y"]), float(marker["z"]) + z_shift))
        )
        header = connector["header_rect"]
        circuits = int(connector["circuits"])
        pitch = float(connector["pitch"])
        pin_span = pitch * (circuits - 1)
        first_x = float(header["x"]) + (float(header["length_x"]) - pin_span) / 2
        for idx in range(circuits):
            part = part.union(
                cq.Workplane("XY")
                .box(0.22, 0.8, 0.12, centered=(False, False, False))
                .translate(
                    (
                        first_x + idx * pitch - 0.11,
                        float(header["y"]) + 0.35,
                        float(header["z"]) + float(header["height_z"]) + z_shift,
                    )
                )
            )
        model = part if model is None else model.union(part)
    if model is None:
        raise ValueError("sensor service connector model requires at least one connector")
    return model


def _cut_lid_sensor_harness_channels(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
    owner_part: str,
    assembly_position: bool,
    fabrication_origin_z: float | None = None,
    cut_through_top: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    harness = params["sensor_harness"]
    channel_depth = harness["channel_depth_z"]
    channel_clearance = harness["channel_clearance_xy"]
    z_shift = 0.0
    if not assembly_position and fabrication_origin_z is not None:
        z_shift = -fabrication_origin_z
    elif not assembly_position:
        if owner_part == "lid_manifold_shell":
            z_shift = -layout["lid_bottom_z"]
        else:
            z_shift = -layout["lid_top_z"]
    rects: list[dict[str, Any]] = [
        trunk
        for trunk in layout["lid_sensor_harness_trunks"]
        if trunk["owner_part"] == owner_part
    ]
    for route in layout["lid_sensor_harness_routes"]:
        if route["owner_part"] != owner_part:
            continue
        rects.append(route["branch_rect"])
        rects.append(route["strain_relief_rect"])
    for rect in rects:
        cutter_z = float(rect["z"]) + z_shift - 0.05
        cutter_height = channel_depth + 0.05
        if cut_through_top:
            cutter_height = max(
                cutter_height,
                float(model.val().BoundingBox().zmax) - cutter_z + 0.1,
            )
        model = model.cut(
            cq.Workplane("XY")
            .box(
                float(rect["length_x"]) + 2 * channel_clearance,
                float(rect["width_y"]) + 2 * channel_clearance,
                cutter_height,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(rect["x"]) - channel_clearance,
                    float(rect["y"]) - channel_clearance,
                    cutter_z,
                )
            )
        )
    return model


def _cut_lower_sensor_harness_channels(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    harness = params["sensor_harness"]
    channel_depth = harness["channel_depth_z"]
    channel_clearance = harness["channel_clearance_xy"]
    rects = [layout["lower_ir_harness_trunk"]]
    for route in layout["lower_ir_harness_routes"]:
        rects.append(route["branch_rect"])
        rects.append(route["strain_relief_rect"])
    for rect in rects:
        model = model.cut(
            cq.Workplane("XY")
            .box(
                float(rect["length_x"]) + 2 * channel_clearance,
                float(rect["width_y"]) + 2 * channel_clearance,
                channel_depth + 0.05,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(rect["x"]) - channel_clearance,
                    float(rect["y"]) - channel_clearance,
                    -0.01,
                )
            )
        )
    return model


def _electrical_connector_mating_state_check(
    review_rects: list[dict[str, Any]],
    *,
    connectors: list[dict[str, Any]],
    cable_envelopes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "name": "electrical_connector_mating_state_check",
        "role": "mated_and_unmated_sensor_connector_state_validation_body",
        "validation": "required_gate6_connector_mating_state_evidence",
        "failure_rule": (
            "unmated_loose_or_unproven_connector_state_blocks_sensor_thermal_pass"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{len(connectors)} connectors / {len(cable_envelopes)} cable envelopes"
        ),
        "review_cad_value": (
            f"{len(connectors)} connectors / {len(review_rects)} "
            "mating-state review bodies"
        ),
        "connector_count": len(connectors),
        "cable_envelope_count": len(cable_envelopes),
        "review_body_count": len(review_rects),
        "source_layout_checks": [
            "sensor_connector_service_clearance_check",
            "sensor_service_cable_envelope_check",
            "unmated_sensor_service_connector_review_rects",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "mated_sensor_service_connectors",
            "continuous_sensor_electrical_service",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": review_rects,
    }


def _electrical_service_part_names(connector_name: str) -> tuple[str, str]:
    if connector_name.startswith("lower_"):
        return "lower_sensor_service_connector", "lower_sensor_service_cable_pigtail"
    return "lid_sensor_service_connectors", "lid_sensor_service_cable_pigtails"


def _harness_cover_from_rectangles(
    rects: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    params: dict[str, Any],
    underside: bool,
    z_shift: float = 0.0,
) -> cq.Workplane:
    harness = params["sensor_harness"]
    cover_h = harness["cover_height_z"]
    overlap = harness["cover_overlap_xy"]
    cover: cq.Workplane | None = None
    for rect in rects:
        if underside:
            z = float(rect["z"]) + z_shift - cover_h
        else:
            z = float(rect["z"]) + z_shift + float(rect["height_z"])
        part = (
            cq.Workplane("XY")
            .box(
                float(rect["length_x"]) + 2 * overlap,
                float(rect["width_y"]) + 2 * overlap,
                cover_h,
                centered=(False, False, False),
            )
            .translate((float(rect["x"]) - overlap, float(rect["y"]) - overlap, z))
        )
        cover = part if cover is None else cover.union(part)
    if cover is None:
        raise ValueError("harness cover requires at least one rectangle")
    return cover


def _installed_sensor_rect(mount: dict[str, Any]) -> dict[str, float]:
    return {
        "x": round(float(mount["x"]), 3),
        "y": round(float(mount["y"]), 3),
        "z": round(float(mount["z"]), 3),
        "length_x": round(float(mount["length_x"]), 3),
        "width_y": round(float(mount["width_y"]), 3),
        "height_z": round(float(mount["height_z"]), 3),
    }


def _lid_sensor_harness_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_bottom_z: float,
    lid_top_z: float,
    headspace_sht41_mounts: list[dict[str, Any]],
    gas_sensor_pcb_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    harness = params["sensor_harness"]
    wire_w = harness["wire_bundle_width_xy"]
    wire_h = harness["wire_bundle_height_z"]
    min_bend = harness["min_bend_radius"]
    conn_dims = _service_connector_dimensions(params)
    conn_len = float(conn_dims["board_length_x"])
    conn_wid = float(conn_dims["board_width_y"])
    edge_gap_y = harness["lid_connector_edge_gap_y"]
    conn_y = float(layout["width_y"]) - conn_wid - edge_gap_y
    left_x = harness["lid_left_trunk_x"]
    left_w = harness["lid_left_trunk_width_x"]
    right_x = harness["lid_right_trunk_x"]
    right_w = harness["lid_right_trunk_width_x"]
    shell_right_x = harness.get("lid_shell_right_trunk_x", right_x)
    shell_bus_z = (
        lid_bottom_z
        + float(harness["cover_height_z"])
        + float(harness.get("lid_shell_cover_gasket_clearance_z", 0.1))
    )

    gas_ys = [float(mount["aperture_y"]) for mount in gas_sensor_pcb_mounts]
    sht_ys = [float(mount["aperture_y"]) for mount in headspace_sht41_mounts]
    cover_trunk_y = max(params["row"]["side_margin_y"], min(gas_ys) - min_bend)
    shell_trunk_y = max(params["row"]["side_margin_y"], min(sht_ys) - min_bend)
    trunk_y2 = conn_y + conn_wid
    trunks = [
        {
            "name": "lid_cover_left_gas_bus",
            "domain": "lid_sensor_harness",
            "owner_part": "lid_cover",
            "retention": "channel_clearance_cover_physical_retention_gate",
            "install_axis": "+Z",
            "removal_axis": "+Z",
            "critical_surface_printing": "channel_face_up_no_internal_support",
            "x": round(left_x, 3),
            "y": round(cover_trunk_y, 3),
            "z": round(lid_top_z, 3),
            "length_x": round(left_w, 3),
            "width_y": round(trunk_y2 - cover_trunk_y, 3),
            "height_z": round(wire_h, 3),
            "channel_depth_z": harness["channel_depth_z"],
            "cover_height_z": harness["cover_height_z"],
            "min_bend_radius": min_bend,
        },
        {
            "name": "lid_cover_right_gas_bus",
            "domain": "lid_sensor_harness",
            "owner_part": "lid_cover",
            "retention": "channel_clearance_cover_physical_retention_gate",
            "install_axis": "+Z",
            "removal_axis": "+Z",
            "critical_surface_printing": "channel_face_up_no_internal_support",
            "x": round(right_x, 3),
            "y": round(cover_trunk_y, 3),
            "z": round(lid_top_z, 3),
            "length_x": round(right_w, 3),
            "width_y": round(trunk_y2 - cover_trunk_y, 3),
            "height_z": round(wire_h, 3),
            "channel_depth_z": harness["channel_depth_z"],
            "cover_height_z": harness["cover_height_z"],
            "min_bend_radius": min_bend,
        },
        {
            "name": "lid_shell_right_sht41_bus",
            "domain": "lid_sensor_harness",
            "owner_part": "lid_manifold_shell",
            "retention": "channel_clearance_cover_physical_retention_gate",
            "install_axis": "-Z",
            "removal_axis": "-Z",
            "critical_surface_printing": "channel_face_up_no_internal_support",
            # The underside SHT41 bus must remain inside the upper perimeter
            # gasket's inner edge.  It is independently located from the
            # cover-side gas bus, which legitimately runs at the outer edge.
            "x": round(shell_right_x, 3),
            "y": round(shell_trunk_y, 3),
            "z": round(shell_bus_z, 3),
            "length_x": round(right_w, 3),
            "width_y": round(trunk_y2 - shell_trunk_y, 3),
            "height_z": round(wire_h, 3),
            "channel_depth_z": harness["channel_depth_z"],
            "cover_height_z": harness["cover_height_z"],
            "min_bend_radius": min_bend,
        },
    ]
    trunk_by_name = {trunk["name"]: trunk for trunk in trunks}
    routes: list[dict[str, Any]] = []
    for mount in gas_sensor_pcb_mounts:
        if mount["role"] == "supply":
            trunk = trunk_by_name["lid_cover_left_gas_bus"]
            branch_x = float(trunk["x"]) + float(trunk["length_x"])
            branch_len = max(float(mount["x"]) - branch_x, 0.0)
        else:
            trunk = trunk_by_name["lid_cover_right_gas_bus"]
            branch_x = float(mount["x"]) + float(mount["length_x"])
            branch_len = max(float(trunk["x"]) - branch_x, 0.0)
        # Cable egress is intentionally offset from the sealed gas aperture;
        # sharing the aperture centerline routes the wire through the gasket.
        center_y = float(mount.get("cable_center_y", mount["aperture_y"]))
        relief_len = min(harness["strain_relief_length_x"], branch_len)
        relief_x = (
            branch_x
            if mount["role"] == "return"
            else branch_x + branch_len - relief_len
        )
        routes.append(
            {
                "name": f"{mount['name']}_lid_cover_branch",
                "domain": "lid_sensor_harness",
                "sensor_name": mount["name"],
                "owner_part": "lid_cover",
                "retention": "printed_snap_cover_and_strain_relief",
                "branch_rect": {
                    "x": round(branch_x, 3),
                    "y": round(center_y - wire_w / 2, 3),
                    "z": round(float(mount["z"]), 3),
                    "length_x": round(branch_len, 3),
                    "width_y": round(wire_w, 3),
                    "height_z": round(wire_h, 3),
                },
                "strain_relief_rect": {
                    "x": round(relief_x, 3),
                    "y": round(center_y - harness["strain_relief_width_y"] / 2, 3),
                    "z": round(float(mount["z"]), 3),
                    "length_x": round(relief_len, 3),
                    "width_y": round(harness["strain_relief_width_y"], 3),
                    "height_z": round(wire_h, 3),
                    "depth_z": round(harness["strain_relief_depth_z"], 3),
                },
                "trunk_name": trunk["name"],
                "min_bend_radius": min_bend,
                "branch_length_to_trunk": round(branch_len, 3),
            }
        )
    shell_trunk = trunk_by_name["lid_shell_right_sht41_bus"]
    for mount in headspace_sht41_mounts:
        center_y = float(mount["aperture_y"])
        routes.append(
            {
                "name": f"{mount['name']}_inline_lid_shell_bus",
                "domain": "lid_sensor_harness",
                "sensor_name": mount["name"],
                "tile_index": mount["tile_index"],
                "owner_part": "lid_manifold_shell",
                "retention": "printed_snap_cover_and_strain_relief",
                "inline_trunk": True,
                "branch_rect": {
                    "x": round(float(shell_trunk["x"]), 3),
                    "y": round(center_y - wire_w / 2, 3),
                    "z": round(float(shell_trunk["z"]), 3),
                    "length_x": round(float(shell_trunk["length_x"]), 3),
                    "width_y": round(wire_w, 3),
                    "height_z": round(wire_h, 3),
                },
                "strain_relief_rect": {
                    "x": round(float(shell_trunk["x"]), 3),
                    "y": round(center_y - harness["strain_relief_width_y"] / 2, 3),
                    "z": round(float(shell_trunk["z"]), 3),
                    "length_x": round(float(shell_trunk["length_x"]), 3),
                    "width_y": round(harness["strain_relief_width_y"], 3),
                    "height_z": round(wire_h, 3),
                    "depth_z": round(harness["strain_relief_depth_z"], 3),
                },
                "trunk_name": shell_trunk["name"],
                "min_bend_radius": min_bend,
                "branch_length_to_trunk": 0.0,
            }
        )

    left_connector = _sensor_service_connector_spec(
        name="lid_left_gas_service_connector",
        domain="lid_sensor_harness",
        owner_part="lid_cover",
        disconnect="removable_lid_left_gas",
        x=left_x,
        y=conn_y,
        z=lid_top_z,
        params=params,
    )
    right_connector = _sensor_service_connector_spec(
        name="lid_right_sensor_service_connector",
        domain="lid_sensor_harness",
        owner_part="lid_cover",
        disconnect="removable_lid_right_sensor_bus",
        x=float(layout["length_x"]) - conn_len - 1.0,
        y=conn_y,
        z=lid_top_z,
        params=params,
    )
    return {
        "lid_sensor_harness_routes": routes,
        "lid_sensor_harness_trunks": trunks,
        "lid_service_connector_envelopes": [left_connector, right_connector],
    }


def _lower_ir_harness_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    base_top_z: float,
    plate_bottom_z: float,
    ir_sensor_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    harness = params["sensor_harness"]
    wire_w = harness["wire_bundle_width_xy"]
    wire_h = harness["wire_bundle_height_z"]
    min_bend = harness["min_bend_radius"]
    trunk_x = harness["lower_trunk_x"]
    trunk_w = harness["lower_trunk_width_x"]
    conn_dims = _service_connector_dimensions(params)
    conn_wid = float(conn_dims["board_width_y"])
    conn_h = float(conn_dims["height_z"])
    edge_gap_y = harness.get("lid_connector_edge_gap_y", 2.0)
    conn_y = float(layout["width_y"]) - conn_wid - edge_gap_y
    centers_y = [float(mount["center_y"]) for mount in ir_sensor_mounts]
    trunk_y = max(params["row"]["side_margin_y"], min(centers_y) - min_bend)
    trunk_y2 = conn_y + conn_wid
    trunk = {
        "name": "lower_ir_dry_trunk",
        "domain": "lower_dry_harness",
        "owner_part": "plate_support_frame",
        "retention": "printed_snap_cover",
        "x": round(trunk_x, 3),
        "y": round(trunk_y, 3),
        "z": 0.0,
        "length_x": round(trunk_w, 3),
        "width_y": round(trunk_y2 - trunk_y, 3),
        "height_z": round(wire_h, 3),
        "channel_depth_z": harness["channel_depth_z"],
        "cover_height_z": harness["cover_height_z"],
        "min_bend_radius": min_bend,
        "base_top_z": round(base_top_z, 3),
        "plate_bottom_z": round(plate_bottom_z, 3),
    }
    routes: list[dict[str, Any]] = []
    branch_x = trunk_x + trunk_w
    for mount in ir_sensor_mounts:
        sensor_left_x = float(mount["x"])
        branch_len = max(sensor_left_x - branch_x, 0.0)
        center_y = float(mount["center_y"])
        relief_len = min(harness["strain_relief_length_x"], branch_len)
        routes.append(
            {
                "name": f"{mount['name']}_lower_dry_branch",
                "domain": "lower_dry_harness",
                "sensor_name": mount["name"],
                "tile_index": mount["tile_index"],
                "owner_part": "plate_support_frame",
                "retention": "printed_snap_cover_and_strain_relief",
                "branch_rect": {
                    "x": round(branch_x, 3),
                    "y": round(center_y - wire_w / 2, 3),
                    "z": 0.0,
                    "length_x": round(branch_len, 3),
                    "width_y": round(wire_w, 3),
                    "height_z": round(wire_h, 3),
                },
                "strain_relief_rect": {
                    "x": round(sensor_left_x - relief_len, 3),
                    "y": round(center_y - harness["strain_relief_width_y"] / 2, 3),
                    "z": 0.0,
                    "length_x": round(relief_len, 3),
                    "width_y": round(harness["strain_relief_width_y"], 3),
                    "height_z": round(wire_h, 3),
                    "depth_z": round(harness["strain_relief_depth_z"], 3),
                },
                "trunk_name": trunk["name"],
                "min_bend_radius": min_bend,
                "branch_length_to_trunk": round(branch_len, 3),
            }
        )
    connector = _sensor_service_connector_spec(
        name="lower_ir_service_connector",
        domain="lower_dry_harness",
        owner_part="plate_support_frame",
        disconnect="lower_dry_row_end",
        x=trunk_x,
        y=conn_y,
        z=-conn_h,
        params=params,
    )
    connector["printed_shroud"]["install_axis"] = "+Z_from_below_to_datum"
    connector["printed_shroud"]["removal_axis"] = "-Z_then_+Y_connector_unmate"
    return {
        "lower_ir_harness_routes": routes,
        "lower_ir_harness_trunk": trunk,
        "lower_ir_connector_envelope": connector,
    }


def _review_rect(
    source: dict[str, Any],
    *,
    connector: dict[str, Any],
    review_kind: str,
    y_offset: float = 0.0,
    height_z: float | None = None,
    z: float | None = None,
    name_suffix: str | None = None,
) -> dict[str, Any]:
    connector_part, pigtail_part = _electrical_service_part_names(
        str(connector["name"]),
    )
    return {
        "name": f"{connector['name']}_{name_suffix or review_kind}",
        "connector_name": connector["name"],
        "connector_family": connector["connector_family"],
        "review_state": "electrical_connectors_unmated",
        "review_kind": review_kind,
        "removed_connector_part": connector_part,
        "removed_pigtail_part": pigtail_part,
        "unmated_offset_y": round(y_offset, 3),
        "x": round(float(source["x"]), 3),
        "y": round(float(source["y"]) + y_offset, 3),
        "z": round(float(source["z"] if z is None else z), 3),
        "length_x": round(float(source["length_x"]), 3),
        "width_y": round(float(source["width_y"]), 3),
        "height_z": round(float(source["height_z"] if height_z is None else height_z), 3),
    }


def _sensor_connector_service_clearance_check(
    connectors: list[dict[str, Any]],
) -> dict[str, Any]:
    body_rects = [connector["service_clearance_rect"] for connector in connectors]
    x_len, y_len, z_len = _rectangles_bounding_extents(body_rects)
    connector_names = tuple(str(connector["name"]) for connector in connectors)
    return {
        "name": "sensor_connector_service_clearance_check",
        "role": "sensor_connector_mating_and_service_clearance_validation_body",
        "validation": "required_gate6_connector_service_clearance_evidence",
        "failure_rule": (
            "blocked_connector_clearance_or_unmeasured_mating_space_blocks_sensor_thermal_pass"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": f"{x_len:.2f} x {y_len:.2f} x {z_len:.2f} mm",
        "connector_count": len(connectors),
        "connector_names": connector_names,
        "source_layout_checks": ["sensor_service_connector_envelopes"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "mated_sensor_service_connectors",
            "serviceable_sensor_electrical_disconnects",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": body_rects,
    }


def _sensor_harness_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_bottom_z: float,
    lid_top_z: float,
    base_top_z: float,
    plate_bottom_z: float,
    ir_sensor_mounts: list[dict[str, Any]],
    headspace_sht41_mounts: list[dict[str, Any]],
    gas_sensor_pcb_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    harness = params.get("sensor_harness", {})
    if not harness:
        return {
            "lower_ir_harness_routes": [],
            "lower_ir_harness_trunk": {},
            "lower_ir_connector_envelope": {},
            "lid_sensor_harness_routes": [],
            "lid_sensor_harness_trunks": [],
            "lid_service_connector_envelopes": [],
            "sensor_service_connector_envelopes": [],
            "sensor_service_cable_envelopes": [],
            "sensor_service_cable_pigtails": [],
            "sensor_harness_summary": {
                "lower_ir_route_count": 0,
                "lid_sensor_route_count": 0,
                "service_connector_count": 0,
                "external_service_cable_envelope_count": 0,
                "installed_service_cable_pigtail_count": 0,
                "retention": "not_modeled",
            },
        }

    lower = _lower_ir_harness_for_layout(
        layout,
        params=params,
        base_top_z=base_top_z,
        plate_bottom_z=plate_bottom_z,
        ir_sensor_mounts=ir_sensor_mounts,
    )
    lid = _lid_sensor_harness_for_layout(
        layout,
        params=params,
        lid_bottom_z=lid_bottom_z,
        lid_top_z=lid_top_z,
        headspace_sht41_mounts=headspace_sht41_mounts,
        gas_sensor_pcb_mounts=gas_sensor_pcb_mounts,
    )
    connectors = [lower["lower_ir_connector_envelope"], *lid["lid_service_connector_envelopes"]]
    cable_envelopes = [
        connector["external_cable_envelope_rect"]
        for connector in connectors
    ]
    cable_pigtails = [
        connector["installed_cable_pigtail_rect"]
        for connector in connectors
    ]
    return {
        **lower,
        **lid,
        "sensor_service_connector_envelopes": connectors,
        "sensor_service_cable_envelopes": cable_envelopes,
        "sensor_service_cable_pigtails": cable_pigtails,
        "sensor_harness_summary": {
            "lower_ir_route_count": len(lower["lower_ir_harness_routes"]),
            "lid_sensor_route_count": len(lid["lid_sensor_harness_routes"]),
            "service_connector_count": len(connectors),
            "external_service_cable_envelope_count": len(cable_envelopes),
            "installed_service_cable_pigtail_count": len(cable_pigtails),
            "service_connector_family": params["sensor_harness"].get(
                "service_connector_family",
                "unspecified",
            ),
            "retention": "printed_snap_covers_and_strain_relief",
            "lower_domain": "dry_plate_support_side",
            "lid_domain": "removable_lid_sensor_side",
        },
    }


def _sensor_installation_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    gas_sensor_pcb_mounts: list[dict[str, Any]],
    headspace_sht41_mounts: list[dict[str, Any]],
    ir_sensor_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    install = params.get("sensor_installation", {})
    gas_lift_z = install.get("gas_pcb_service_lift_z", 18.0)
    sht41_offset_x = install.get("sht41_service_offset_x", 18.0)
    ir_drop_z = install.get("ir_service_drop_z", 14.0)
    steps: list[dict[str, Any]] = []

    for mount in gas_sensor_pcb_mounts:
        steps.append(
            {
                "name": f"{mount['name']}_install",
                "sensor_name": mount["name"],
                "module_kind": "gas_sensor_pcb_cartridge",
                "role": mount["role"],
                "owner_part": mount["owner_part"],
                "install_direction": "-Z into dry-side lid cassette",
                "service_direction": "+Z pull after releasing printed keeper door",
                "retention": "printed_keeper_door_no_screws_no_glue",
                "aperture_registration": "gas duct wall aperture to PCB sensor aperture",
                "service_vector": {"dx": 0.0, "dy": 0.0, "dz": round(gas_lift_z, 3)},
                "installed_rect": _installed_sensor_rect(mount),
            }
        )

    for mount in headspace_sht41_mounts:
        steps.append(
            {
                "name": f"{mount['name']}_install",
                "sensor_name": mount["name"],
                "module_kind": "headspace_sht41_microcarrier",
                "role": mount["role"],
                "owner_part": mount["owner_part"],
                "install_direction": "-X from lid service edge into protected pocket",
                "service_direction": "+X pull from lid service edge",
                "retention": "printed_microcarrier_keeper_no_screws_no_glue",
                "aperture_registration": "SHT41 membrane to local headspace aperture",
                "service_vector": {"dx": round(sht41_offset_x, 3), "dy": 0.0, "dz": 0.0},
                "installed_rect": _installed_sensor_rect(mount),
            }
        )

    for mount in ir_sensor_mounts:
        steps.append(
            {
                "name": f"{mount['name']}_install",
                "sensor_name": mount["name"],
                "module_kind": "lower_ir_thermopile",
                "role": mount["role"],
                "owner_part": mount["owner_part"],
                "install_direction": "+Z from underside into lower dry support pocket",
                "service_direction": "-Z pull from dry bay underside",
                "retention": "printed_lip_no_screws_no_glue",
                "aperture_registration": "IR lens to plate-margin aperture and FOV",
                "service_vector": {"dx": 0.0, "dy": 0.0, "dz": round(-ir_drop_z, 3)},
                "installed_rect": _installed_sensor_rect(mount),
            }
        )

    gates = _sensor_prototype_test_gates()
    path_width = install.get("install_path_width_xy", 1.4)
    path_height = install.get("install_path_height_z", path_width)
    path_rects = _sensor_installation_path_rectangles(
        steps,
        path_width=path_width,
        path_height=path_height,
    )
    module_kind_counts: dict[str, int] = {}
    for step in steps:
        kind = str(step["module_kind"])
        module_kind_counts[kind] = module_kind_counts.get(kind, 0) + 1

    return {
        "sensor_installation_steps": steps,
        "sensor_prototype_test_gates": gates,
        "sensor_installation_path_check": {
            "name": "sensor_installation_path_check",
            "role": "real_sensor_install_and_removal_motion_envelope_validation_body",
            "validation": "required_gate6_real_sensor_install_serviceability_evidence",
            "failure_rule": (
                "unproven_install_path_retention_or_aperture_registration_blocks_sensor_thermal_pass"
            ),
            "evidence_gate": "Gate 6 sensor/thermal",
            "cad_value": f"{len(steps)} steps / {len(gates)} gates",
            "install_step_count": len(steps),
            "test_gate_count": len(gates),
            "module_kind_counts": module_kind_counts,
            "path_width_xy": round(float(path_width), 3),
            "path_height_z": round(float(path_height), 3),
            "source_layout_checks": [
                "gas_pcb_flow_cell_check",
                "sensor_connector_service_clearance_check",
                "sensor_service_cable_envelope_check",
            ],
            "requires_physical_evidence": True,
            "requires_real_sensor_inventory": True,
            "physical_claims_blocked": [
                "gas_pcb_cartridges_sealed_to_sampling_cells",
                "local_headspace_sht41_sensors_installed",
                "local_ir_thermopiles_installed",
                "powered_sensor_thermal_readiness",
            ],
            "body_rects": path_rects,
        },
        "sensor_installation_summary": {
            "install_step_count": len(steps),
            "test_gate_count": len(gates),
            "retention_policy": "printed_reversible_no_screws_no_glue",
            "service_modes": "bench_test_then_sensor_install_then_dry_then_wet_then_bsl1",
        },
    }


def _sensor_installation_path_rectangles(
    steps: list[dict[str, Any]],
    *,
    path_width: float,
    path_height: float,
) -> list[dict[str, Any]]:
    rects: list[dict[str, Any]] = []
    for step in steps:
        installed = step["installed_rect"]
        vector = step["service_vector"]
        cx = float(installed["x"]) + float(installed["length_x"]) / 2
        cy = float(installed["y"]) + float(installed["width_y"]) / 2
        cz = float(installed["z"]) + float(installed["height_z"]) / 2
        dx = float(vector["dx"])
        dz = float(vector["dz"])
        if abs(dx) >= abs(dz):
            rects.append(
                {
                    "name": f"{step['name']}_path",
                    "sensor_name": step["sensor_name"],
                    "module_kind": step["module_kind"],
                    "x": round(min(cx, cx + dx) - path_width / 2, 3),
                    "y": round(cy - path_width / 2, 3),
                    "z": round(cz - path_height / 2, 3),
                    "length_x": round(abs(dx) + path_width, 3),
                    "width_y": round(path_width, 3),
                    "height_z": round(path_height, 3),
                }
            )
        else:
            rects.append(
                {
                    "name": f"{step['name']}_path",
                    "sensor_name": step["sensor_name"],
                    "module_kind": step["module_kind"],
                    "x": round(cx - path_width / 2, 3),
                    "y": round(cy - path_width / 2, 3),
                    "z": round(min(cz, cz + dz) - path_height / 2, 3),
                    "length_x": round(path_width, 3),
                    "width_y": round(path_width, 3),
                    "height_z": round(abs(dz) + path_height, 3),
                }
            )
    return rects


def _sensor_prototype_test_gates() -> list[dict[str, str]]:
    return [
        {
            "name": "incoming_module_electrical",
            "evidence": "bench I2C scan, current draw, sensor identity, and baseline reading",
        },
        {
            "name": "pocket_fit_and_retention",
            "evidence": "insertion/removal force, no rattle, no crushed package, release access",
        },
        {
            "name": "aperture_registration",
            "evidence": "gas, headspace, or IR aperture is visibly centered and unobstructed",
        },
        {
            "name": "installed_dry_electrical",
            "evidence": "assembled dry coupon bus scan plus connector wiggle/dropout check",
        },
        {
            "name": "environmental_step_response",
            "evidence": "humidity, temperature, CO2, and airflow step response without biology",
        },
        {
            "name": "wet_nonbiological_exposure",
            "evidence": "loaded plate/media proxy condensation, splash, drift, and leak check",
        },
        {
            "name": "bsl1_biology_commissioning",
            "evidence": "low-risk biology run correlating sensor traces with growth state",
        },
    ]


def _sensor_service_cable_envelope_check(
    cable_envelopes: list[dict[str, Any]],
) -> dict[str, Any]:
    first_envelope = cable_envelopes[0] if cable_envelopes else {}
    min_bend_radius_y = max(
        (float(envelope.get("min_bend_radius_y", 0.0)) for envelope in cable_envelopes),
        default=0.0,
    )
    straight_service_length_y = max(
        (
            float(envelope.get("straight_service_length_y", 0.0))
            for envelope in cable_envelopes
        ),
        default=0.0,
    )
    return {
        "name": "sensor_service_cable_envelope_check",
        "role": "sensor_service_cable_bend_and_egress_validation_body",
        "validation": "required_gate6_service_cable_bend_envelope_evidence",
        "failure_rule": (
            "kinked_snagging_or_unmeasured_sensor_cable_dress_blocks_sensor_thermal_pass"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{float(first_envelope.get('length_x', 0.0)):.2f} x "
            f"{float(first_envelope.get('width_y', 0.0)):.2f} x "
            f"{float(first_envelope.get('height_z', 0.0)):.2f} mm"
        ),
        "bend_cad_value": (
            f"{min_bend_radius_y:.2f} mm bend radius / "
            f"{straight_service_length_y:.2f} mm straight"
        ),
        "cable_envelope_count": len(cable_envelopes),
        "min_bend_radius_y": round(min_bend_radius_y, 3),
        "straight_service_length_y": round(straight_service_length_y, 3),
        "source_layout_checks": ["sensor_service_connector_envelopes"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "connected_sensor_service_cable_dress",
            "pipette_clearance_with_electrical_services",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": cable_envelopes,
    }


def _sensor_service_connector_spec(
    *,
    name: str,
    domain: str,
    owner_part: str,
    disconnect: str,
    x: float,
    y: float,
    z: float,
    params: dict[str, Any],
) -> dict[str, Any]:
    dims = _service_connector_dimensions(params)
    board_l = float(dims["board_length_x"])
    board_w = float(dims["board_width_y"])
    board_h = float(dims["board_thickness_z"])
    header_l = float(dims["header_length_x"])
    header_w = float(dims["header_width_y"])
    header_h = float(dims["header_height_z"])
    plug_l = float(dims["plug_length_y"])
    plug_h = float(dims["plug_height_z"])
    latch_l = float(dims["latch_length_y"])
    latch_w = float(dims["latch_width_x"])
    latch_h = float(dims["latch_height_z"])
    shroud_wall = float(dims["shroud_wall_xy"])
    shroud_h = float(dims["shroud_height_z"])
    harness = params["sensor_harness"]
    cable_w = harness.get("service_cable_envelope_width_x", board_l)
    cable_h = harness.get("service_cable_envelope_height_z", dims["height_z"])
    cable_bend = harness.get("service_cable_bend_radius_y", 0.0)
    cable_straight = harness.get("service_cable_straight_length_y", 0.0)
    cable_len = cable_bend + cable_straight
    pigtail_w = harness.get("service_cable_pigtail_width_x", min(cable_w, header_l))
    pigtail_h = harness.get("service_cable_pigtail_height_z", 1.2)
    pigtail_len = harness.get("service_cable_pigtail_length_y", cable_len)
    if cable_len > 0:
        pigtail_len = min(pigtail_len, cable_len)
    header_x = x + (board_l - header_l) / 2
    header_y = y + max((board_w - header_w - plug_l) / 2, 0.0)
    plug_y = header_y + header_w
    plug_w = min(plug_l, max(y + board_w - plug_y, plug_l))
    return {
        "name": name,
        "domain": domain,
        "owner_part": owner_part,
        "connector_family": dims["family"],
        "source_url": dims["source_url"],
        "circuits": dims["circuits"],
        "pitch": dims["pitch"],
        "x": round(x, 3),
        "y": round(y, 3),
        "z": round(z, 3),
        "length_x": round(board_l, 3),
        "width_y": round(board_w, 3),
        "height_z": round(float(dims["height_z"]), 3),
        "keyed": True,
        "disconnect": disconnect,
        "mating_direction": "+Y",
        "board_rect": {
            "x": round(x, 3),
            "y": round(y, 3),
            "z": round(z, 3),
            "length_x": round(board_l, 3),
            "width_y": round(board_w, 3),
            "height_z": round(board_h, 3),
        },
        "header_rect": {
            "x": round(header_x, 3),
            "y": round(header_y, 3),
            "z": round(z + board_h, 3),
            "length_x": round(header_l, 3),
            "width_y": round(header_w, 3),
            "height_z": round(header_h, 3),
        },
        "plug_rect": {
            "x": round(header_x, 3),
            "y": round(plug_y, 3),
            "z": round(z + board_h, 3),
            "length_x": round(header_l, 3),
            "width_y": round(plug_w, 3),
            "height_z": round(plug_h, 3),
        },
        "latch_rect": {
            "x": round(x + (board_l - latch_w) / 2, 3),
            "y": round(plug_y + max(plug_w - latch_l, 0.0), 3),
            "z": round(z + board_h + plug_h, 3),
            "length_x": round(latch_w, 3),
            "width_y": round(latch_l, 3),
            "height_z": round(latch_h, 3),
        },
        "pin1_marker": {
            "x": round(x + 1.0, 3),
            "y": round(y + 1.0, 3),
            "z": round(z + board_h, 3),
            "diameter": dims["pin1_marker_diameter"],
            "height_z": 0.25,
        },
        "key_rib_rect": {
            "x": round(header_x, 3),
            "y": round(y - shroud_wall, 3),
            "z": round(z, 3),
            "length_x": round(float(dims["key_rib_width_x"]), 3),
            "width_y": round(float(dims["key_rib_length_y"]), 3),
            "height_z": round(shroud_h, 3),
        },
        "printed_shroud": {
            "x": round(x - shroud_wall, 3),
            "y": round(y - shroud_wall, 3),
            "z": round(z, 3),
            "length_x": round(board_l + 2 * shroud_wall, 3),
            "width_y": round(board_w + shroud_wall, 3),
            "height_z": round(shroud_h, 3),
            "wall_xy": round(shroud_wall, 3),
            "open_side": "+Y",
            "install_axis": "+Z",
            "removal_axis": "+Z_then_+Y_connector_unmate",
            "retention_target": "slip_fit_guard_above_carrier_board",
            "print_orientation": "open_side_up_no_internal_support",
            "physical_gate": "connector_fit_and_repeated_service_cycle",
        },
        "service_clearance_rect": {
            "x": round(x, 3),
            "y": round(y + board_w, 3),
            "z": round(z, 3),
            "length_x": round(board_l, 3),
            "width_y": round(float(dims["service_clearance_y"]), 3),
            "height_z": round(float(dims["height_z"]), 3),
        },
        "external_cable_envelope_rect": {
            "name": f"{name}_external_cable_bend_envelope",
            "domain": domain,
            "connector_name": name,
            "disconnect": disconnect,
            "route_axis": "+Y",
            "x": round(x + (board_l - cable_w) / 2, 3),
            "y": round(y + board_w, 3),
            "z": round(z, 3),
            "length_x": round(cable_w, 3),
            "width_y": round(cable_len, 3),
            "height_z": round(max(float(cable_h), float(dims["height_z"])), 3),
            "min_bend_radius_y": round(cable_bend, 3),
            "straight_service_length_y": round(cable_straight, 3),
            "service_role": "external_electrical_service_cable_envelope",
            "validation": "row_end_cable_egress_not_printed_part",
        },
        "installed_cable_pigtail_rect": {
            "name": f"{name}_cots_cable_pigtail",
            "domain": domain,
            "connector_name": name,
            "disconnect": disconnect,
            "route_axis": "+Y",
            "x": round(x + (board_l - pigtail_w) / 2, 3),
            "y": round(y + board_w, 3),
            "z": round(z + board_h, 3),
            "length_x": round(pigtail_w, 3),
            "width_y": round(pigtail_len, 3),
            "height_z": round(pigtail_h, 3),
            "service_role": "installed_electrical_service_cable_pigtail",
            "material_intent": "COTS flexible cable assembly",
            "validation": "installed_cable_body_bend_envelope_checked_separately",
        },
    }


def _service_connector_dimensions(params: dict[str, Any]) -> dict[str, float | int | str]:
    harness = params["sensor_harness"]
    board_h = harness["service_connector_board_thickness_z"]
    header_h = harness["service_connector_header_height_z"]
    plug_h = harness["service_connector_plug_height_z"]
    latch_h = harness["service_connector_latch_height_z"]
    return {
        "family": harness["service_connector_family"],
        "source_url": harness["service_connector_source_url"],
        "circuits": int(harness["service_connector_circuits"]),
        "pitch": harness["service_connector_pitch"],
        "board_length_x": harness["service_connector_board_length_x"],
        "board_width_y": harness["service_connector_board_width_y"],
        "board_thickness_z": board_h,
        "header_length_x": harness["service_connector_header_length_x"],
        "header_width_y": harness["service_connector_header_width_y"],
        "header_height_z": header_h,
        "plug_length_y": harness["service_connector_plug_length_y"],
        "plug_height_z": plug_h,
        "latch_length_y": harness["service_connector_latch_length_y"],
        "latch_width_x": harness["service_connector_latch_width_x"],
        "latch_height_z": latch_h,
        "shroud_wall_xy": harness["service_connector_shroud_wall_xy"],
        "shroud_height_z": harness["service_connector_shroud_height_z"],
        "pin1_marker_diameter": harness["service_connector_pin1_marker_diameter"],
        "key_rib_width_x": harness["service_connector_key_rib_width_x"],
        "key_rib_length_y": harness["service_connector_key_rib_length_y"],
        "service_clearance_y": harness["service_connector_service_clearance_y"],
        "height_z": board_h + max(header_h, plug_h + latch_h),
    }


def _unmated_sensor_service_connector_review_rectangles(
    *,
    connectors: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    witness_h = production.get("missing_service_lead_witness_height_z", 0.7)
    witness_w = min(
        production.get("missing_service_lead_witness_span_xy", 8.0),
        1.2,
    )
    rects: list[dict[str, Any]] = []

    for connector in connectors:
        service_clearance = connector["service_clearance_rect"]
        y_offset = max(
            float(connector["plug_rect"]["width_y"]) + witness_w,
            float(service_clearance["width_y"]) * 0.5,
        )
        y_offset = min(
            y_offset,
            max(
                float(service_clearance["width_y"])
                - float(connector["plug_rect"]["width_y"]),
                float(connector["plug_rect"]["width_y"]),
            ),
        )

        rects.append(
            _review_rect(
                connector["board_rect"],
                connector=connector,
                review_kind="stationary_service_board",
            )
        )
        rects.append(
            _review_rect(
                connector["header_rect"],
                connector=connector,
                review_kind="stationary_header",
            )
        )
        rects.append(
            _review_rect(
                connector["plug_rect"],
                connector=connector,
                review_kind="unmated_plug",
                y_offset=y_offset,
            )
        )
        rects.append(
            _review_rect(
                connector["latch_rect"],
                connector=connector,
                review_kind="unmated_latch",
                y_offset=y_offset,
            )
        )
        rects.append(
            _review_rect(
                connector["installed_cable_pigtail_rect"],
                connector=connector,
                review_kind="unmated_cable_pigtail",
                y_offset=y_offset,
            )
        )

        header = connector["header_rect"]
        witness_z = (
            max(
                float(connector["header_rect"]["z"]) + float(connector["header_rect"]["height_z"]),
                float(connector["plug_rect"]["z"]) + float(connector["plug_rect"]["height_z"]),
            )
            + 0.05
        )
        witness = {
            "x": header["x"],
            "y": round(float(connector["plug_rect"]["y"]), 3),
            "z": round(witness_z, 3),
            "length_x": header["length_x"],
            "width_y": round(witness_w, 3),
            "height_z": round(witness_h, 3),
        }
        rects.append(
            _review_rect(
                witness,
                connector=connector,
                review_kind="mating_gap_witness",
                height_z=witness_h,
            )
        )

    return rects


def build_electrical_connector_mating_state_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["electrical_connector_mating_state_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_lid_harness_cover(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    """The installed lid harness cover: the union of its canonical per-trunk bodies.

    This used to re-derive the cover here, cutting ONLY the route's owner part.
    That made it a second, weaker definition of the same object: the canonical
    bodies additionally cut the gas PCBs, the service connectors, the printed
    connector shrouds and -- for cover-side routes -- the manifold shell as a
    second rigid neighbour, then re-assert the exact owner to clear OCCT
    slivers.  The local version therefore released material that interpenetrated
    four rigid neighbours (267.008 mm^3, and a fourth solid where the canonical
    grouping releases three), and it drifted silently because nothing compared
    the two.

    Delegating to the grouping removes the duplicate definition rather than
    re-syncing it, so the two cannot diverge again.  The grouping is what
    ``build_row_coupon_installed_parts`` already consumes, which makes it the
    installed authority.
    """

    from ..artifacts import group_row_coupon_physical_artifacts_by_installed_part

    grouped = group_row_coupon_physical_artifacts_by_installed_part(
        params,
        assembly_position=assembly_position,
    )
    cover = grouped.get("lid_harness_cover")
    if cover is None:
        raise ValueError("lid harness cover requires at least one routed trunk")
    return cover


def build_lid_sensor_harness(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = [*layout["lid_sensor_harness_trunks"]]
    rects.extend(route["branch_rect"] for route in layout["lid_sensor_harness_routes"])
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_lid_sensor_service_cable_pigtails(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = [
        connector["installed_cable_pigtail_rect"]
        for connector in layout["lid_service_connector_envelopes"]
    ]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_lid_sensor_service_connectors(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    connectors = layout["lid_service_connector_envelopes"]
    z_shift = _harness_z_shift(connectors, assembly_position=assembly_position)
    return _build_sensor_service_connector_models(connectors, z_shift=z_shift)


def build_lower_harness_cover(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    trunk = _lower_cover_trunk(params)
    rects = [trunk]
    for route in layout["lower_ir_harness_routes"]:
        rects.append(route["branch_rect"])
        rects.append(route["strain_relief_rect"])
    z_shift = 0.0 if assembly_position else 0.0
    cover = _harness_cover_from_rectangles(rects, params=params, underside=True, z_shift=z_shift)
    cover = _add_harness_snap_tabs(
        cover,
        trunk,
        params=params,
        underside=True,
        z_shift=z_shift,
    )
    cover = cover.union(_boxes_from_rectangles(_lower_cover_hook_rectangles(params)))
    return cover


def build_lower_sensor_harness(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = [layout["lower_ir_harness_trunk"]]
    rects.extend(route["branch_rect"] for route in layout["lower_ir_harness_routes"])
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_lower_sensor_service_cable_pigtail(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rect = layout["lower_ir_connector_envelope"]["installed_cable_pigtail_rect"]
    z_shift = _harness_z_shift([rect], assembly_position=assembly_position)
    return _boxes_from_rectangles([rect], z_shift=z_shift)


def build_lower_sensor_service_connector(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    connector = layout["lower_ir_connector_envelope"]
    z_shift = _harness_z_shift([connector], assembly_position=assembly_position)
    return _build_sensor_service_connector_models([connector], z_shift=z_shift)


def build_printed_lid_sensor_connector_shrouds(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    connectors = layout["lid_service_connector_envelopes"]
    z_shift = _harness_z_shift(connectors, assembly_position=assembly_position)
    from .structural import build_lid_cover

    shrouds = _build_printed_sensor_connector_shrouds(
        connectors, z_shift=z_shift, **_shroud_grip_rib_kwargs(params)
    )
    return shrouds.cut(build_lid_cover(params, assembly_position=assembly_position))


def _shroud_grip_rib_kwargs(params: dict[str, Any]) -> dict[str, Any]:
    """Grip-rib kwargs for shroud builders."""

    shroud = params.get("printed_sensor_connector_shroud", {})
    return {
        "emit_grip_rib": True,
        "grip_rib_width_y": float(shroud.get("grip_rib_width_y", 2.0)),
        "grip_rib_y_offset": float(shroud.get("grip_rib_y_offset", 0.0)),
    }


def build_printed_lower_sensor_connector_shroud(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    connector = layout["lower_ir_connector_envelope"]
    z_shift = _harness_z_shift([connector], assembly_position=assembly_position)
    model = _build_printed_sensor_connector_shrouds(
        [connector], z_shift=z_shift, **_shroud_grip_rib_kwargs(params)
    )
    model = _cut_lower_shroud_harness_entry(model, params=params, z_shift=z_shift)
    return model.union(
        _boxes_from_rectangles(_lower_shroud_mount_rectangles(params), z_shift=z_shift)
    )


def build_sensor_connector_service_clearance_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["sensor_connector_service_clearance_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_sensor_installation_path_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["sensor_installation_path_check"]["body_rects"]
    if not rects:
        raise ValueError("sensor installation path check requires at least one sensor")
    z_shift = 0.0 if assembly_position else -min(
        float(rect["z"]) for rect in rects
    )
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_sensor_service_cable_envelope_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["sensor_service_cable_envelope_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_unmated_sensor_service_connectors_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["unmated_sensor_service_connector_review_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)
