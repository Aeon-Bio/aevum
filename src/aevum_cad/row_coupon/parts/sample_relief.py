from __future__ import annotations
from typing import Any
import cadquery as cq
from ..layout import (row_coupon_layout)
from ._geom_base import (_boxes_from_rectangles)
from ._shared_tile import (_lid_port_positions)


def _add_sample_relief_cap_review_flag(
    witness: cq.Workplane,
    *,
    port: dict[str, Any],
    layout: dict[str, Any],
    z0: float,
    length: float,
    width: float,
    height: float,
    radial_from_diameter: float,
) -> cq.Workplane:
    x = float(port["x"])
    y = float(port["y"])
    side = 1 if x <= layout["length_x"] / 2 else -1
    if side > 0:
        flag_x = x + radial_from_diameter / 2 - 0.1
    else:
        flag_x = x - radial_from_diameter / 2 - length + 0.1
    return witness.union(
        cq.Workplane("XY")
        .box(length, width, height, centered=(False, False, False))
        .translate((flag_x, y - width / 2, z0))
    )


def _add_sample_relief_leak_witness_features(
    cover: cq.Workplane,
    *,
    params: dict[str, Any],
    assembly_position: bool,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    for witness in layout["sample_relief_leak_witnesses"]:
        shelf = dict(witness["shelf_rect"])
        shelf["z"] = float(shelf["z"]) + z_shift
        cover = cover.union(_boxes_from_rectangles([shelf]))

        threshold = dict(witness["threshold_rect"])
        threshold["z"] = float(threshold["z"]) + z_shift
        cover = cover.union(_boxes_from_rectangles([threshold]))

        gutter = dict(witness["gutter_rect"])
        gutter["z"] = float(gutter["z"]) + z_shift
        cover = cover.cut(_boxes_from_rectangles([gutter]))
    return cover


def _build_port_cap_body(
    *,
    x: float,
    y: float,
    plug_d: float,
    flange_d: float,
    plug_bottom_z: float,
    plug_depth: float,
    flange_h: float,
    seal_lip_inner_d: float,
    seal_lip_outer_d: float,
    seal_lip_h: float,
    grip_len: float,
    grip_w: float,
    grip_h: float,
    grip_overlap: float,
    layout: dict[str, Any],
) -> cq.Workplane:
    flange_bottom_z = plug_bottom_z + plug_depth
    cap = (
        cq.Workplane("XY")
        .circle(plug_d / 2)
        .extrude(plug_depth)
        .translate((x, y, plug_bottom_z))
    )
    if flange_h > 0:
        cap = cap.union(
            cq.Workplane("XY")
            .circle(flange_d / 2)
            .extrude(flange_h)
            .translate((x, y, flange_bottom_z))
        )
    if min(seal_lip_inner_d, seal_lip_outer_d, seal_lip_h) > 0:
        if seal_lip_inner_d >= seal_lip_outer_d:
            raise ValueError("port cap seal lip inner diameter must be smaller than outer")
        seal_lip = (
            cq.Workplane("XY")
            .circle(seal_lip_outer_d / 2)
            .extrude(seal_lip_h)
            .translate((x, y, flange_bottom_z - seal_lip_h))
        )
        seal_lip = seal_lip.cut(
            cq.Workplane("XY")
            .circle(seal_lip_inner_d / 2)
            .extrude(seal_lip_h + 0.1)
            .translate((x, y, flange_bottom_z - seal_lip_h - 0.05))
        )
        cap = cap.union(seal_lip)
    if min(grip_len, grip_w, grip_h) > 0:
        side = 1 if x <= layout["length_x"] / 2 else -1
        if side > 0:
            grip_x = x + flange_d / 2 - grip_overlap
        else:
            grip_x = x - flange_d / 2 - grip_len + grip_overlap
        cap = cap.union(
            cq.Workplane("XY")
            .box(grip_len, grip_w, grip_h + grip_overlap, centered=(False, False, False))
            .translate(
                (
                    grip_x,
                    y - grip_w / 2,
                    flange_bottom_z + flange_h - grip_overlap,
                )
            )
        )
    return cap


def _port_service_review_state_metadata() -> dict[str, dict[str, Any]]:
    return {
        "sample_relief_cap_missing": {
            "owner": "printed_sample_relief_cap",
            "removed_parts": ["printed_sample_relief_cap"],
            "review_parts": ["missing_sample_relief_cap_witness"],
            "meaning": (
                "The sample/relief cap is absent; witness ring marks the uncapped "
                "service port."
            ),
        },
        "sample_relief_cap_unseated": {
            "owner": "printed_sample_relief_cap",
            "removed_parts": ["printed_sample_relief_cap"],
            "review_parts": ["unseated_sample_relief_cap_review"],
            "meaning": "The sample/relief cap is shown lifted from its seated plug position.",
        },
    }


def _sample_relief_leak_witness_check(
    witnesses: list[dict[str, Any]],
) -> dict[str, Any]:
    wet_collectors = [
        rect
        for witness in witnesses
        for rect in (witness["shelf_rect"], witness["gutter_rect"])
    ]
    inboard_dams = [witness["threshold_rect"] for witness in witnesses]
    body_rects = [*wet_collectors, *inboard_dams]
    return {
        "name": "sample_relief_leak_witness_check",
        "role": "sample_relief_cap_wet_failure_witness_validation_body",
        "validation": "required_gate4_sample_relief_leak_witness_evidence",
        "failure_rule": (
            "sample_relief_leak_without_visible_witness_or_dam_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{len(wet_collectors)} wet collectors / {len(inboard_dams)} inboard dams"
        ),
        "wet_collector_count": len(wet_collectors),
        "inboard_dam_count": len(inboard_dams),
        "witness_count": len(witnesses),
        "source_layout_checks": ["sample_relief_leak_witnesses"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "sample_relief_cap_seat_does_not_bridge_to_dry_bay",
            "wet_operation_with_sample_relief_cap_installed",
            "dry_bay_protection_from_top_cap_leaks",
        ],
        "body_rects": body_rects,
    }


def _sample_relief_leak_witnesses_for_layout(
    layout: dict[str, Any],
    *,
    ports: list[dict[str, Any]],
    params: dict[str, Any],
    lid_top_z: float,
) -> list[dict[str, Any]]:
    lid = params["lid_manifold"]
    production = params.get("production_assembly", {})
    shelf_w = production.get("sample_relief_witness_shelf_width_y", 0.0)
    shelf_h = production.get("sample_relief_witness_shelf_height_z", 0.0)
    shelf_overlap = production.get("sample_relief_witness_shelf_overlap_xy", 0.0)
    gutter_w = production.get("sample_relief_witness_gutter_width_y", 0.0)
    gutter_d = production.get("sample_relief_witness_gutter_depth_z", 0.0)
    threshold_w = production.get("sample_relief_witness_threshold_width_x", 0.0)
    threshold_h = production.get("sample_relief_witness_threshold_height_z", 0.0)
    if min(shelf_w, shelf_h, gutter_w, gutter_d, threshold_w, threshold_h) <= 0:
        return []

    witnesses: list[dict[str, Any]] = []
    for port in ports:
        if port["role"] != "sample_relief":
            continue
        x = float(port["x"])
        y = float(port["y"])
        boss_r = float(port["boss_diameter"]) / 2
        edge_options = [
            ("x", -1, max(x - boss_r, 0.0), "left", "-X_to_visible_outer_edge"),
            (
                "x",
                1,
                max(float(layout["length_x"]) - (x + boss_r), 0.0),
                "right",
                "+X_to_visible_outer_edge",
            ),
            ("y", -1, max(y - boss_r, 0.0), "front", "-Y_to_visible_outer_edge"),
            (
                "y",
                1,
                max(float(layout["width_y"]) - (y + boss_r), 0.0),
                "rear",
                "+Y_to_visible_outer_edge",
            ),
        ]
        route_axis, route_sign, _distance, visible_edge, flow_direction = min(
            edge_options,
            key=lambda option: option[2],
        )
        axis_max = float(layout["length_x"] if route_axis == "x" else layout["width_y"])
        trans_max = float(layout["width_y"] if route_axis == "x" else layout["length_x"])
        axis_value = x if route_axis == "x" else y
        trans_value = y if route_axis == "x" else x
        shelf_trans_start = max(0.0, min(trans_value - shelf_w / 2, trans_max - shelf_w))
        gutter_trans_start = max(0.0, min(trans_value - gutter_w / 2, trans_max - gutter_w))
        if route_sign > 0:
            flow_start = max(0.0, min(axis_value + boss_r - shelf_overlap, axis_max))
            flow_len = max(axis_max - flow_start, 0.1)
            threshold_start = max(0.0, axis_value - boss_r - threshold_w)
        else:
            flow_start = 0.0
            flow_len = max(axis_value - boss_r + shelf_overlap, 0.1)
            threshold_start = min(axis_max - threshold_w, axis_value + boss_r)

        shelf_z = lid_top_z + lid["duct_height_z"]
        gutter_z = shelf_z + shelf_h - gutter_d
        threshold_z = shelf_z + shelf_h

        def route_rect(
            *,
            name: str,
            axis_start: float,
            trans_start: float,
            axis_length: float,
            trans_width: float,
            z: float,
            height_z: float,
            route_axis: str = route_axis,
        ) -> dict[str, Any]:
            if route_axis == "x":
                return {
                    "name": name,
                    "x": round(axis_start, 3),
                    "y": round(trans_start, 3),
                    "z": round(z, 3),
                    "length_x": round(axis_length, 3),
                    "width_y": round(trans_width, 3),
                    "height_z": round(height_z, 3),
                }
            return {
                "name": name,
                "x": round(trans_start, 3),
                "y": round(axis_start, 3),
                "z": round(z, 3),
                "length_x": round(trans_width, 3),
                "width_y": round(axis_length, 3),
                "height_z": round(height_z, 3),
            }

        shelf = route_rect(
            name=f"{port['name']}_outboard_witness_shelf",
            axis_start=flow_start,
            trans_start=shelf_trans_start,
            axis_length=flow_len,
            trans_width=shelf_w,
            z=shelf_z,
            height_z=shelf_h,
        )
        gutter = route_rect(
            name=f"{port['name']}_outboard_witness_gutter",
            axis_start=flow_start,
            trans_start=gutter_trans_start,
            axis_length=flow_len,
            trans_width=gutter_w,
            z=gutter_z,
            height_z=gutter_d,
        )
        threshold = route_rect(
            name=f"{port['name']}_inboard_witness_dam",
            axis_start=threshold_start,
            trans_start=shelf_trans_start,
            axis_length=threshold_w,
            trans_width=shelf_w,
            z=threshold_z,
            height_z=threshold_h,
        )
        witnesses.append(
            {
                "name": f"{port['name']}_cap_leak_witness",
                "owner_part": "lid_cover",
                "port_name": port["name"],
                "port_role": port["role"],
                "service_role": "production_sample_relief_cap_leak_witness",
                "leak_management": "outboard_visible_witness_gutter_with_inboard_dam",
                "leak_flow_direction": flow_direction,
                "route_axis": route_axis,
                "route_sign": route_sign,
                "visible_edge": visible_edge,
                "port_x": round(x, 3),
                "port_y": round(y, 3),
                "boss_diameter": round(float(port["boss_diameter"]), 3),
                "cap_flange_diameter": round(float(port["cap_flange_diameter"]), 3),
                "shelf_rect": shelf,
                "gutter_rect": gutter,
                "threshold_rect": threshold,
                "top_z": round(threshold_z + threshold_h, 3),
                "validation": "sample_relief_cap_routes_failures_to_visible_edge",
            }
        )
    return witnesses


def build_flow_test_adapters(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    adapter_d = production.get("flow_probe_adapter_diameter", 7.0)
    adapter_h = production.get("flow_probe_adapter_height_z", 3.0)

    ports = [
        port for port in _lid_port_positions(layout, params) if port["role"] == "sample_relief"
    ]
    if len(ports) != 1:
        raise ValueError("flow test adapter requires exactly one sample/relief port")

    adapters: cq.Workplane | None = None
    for port in ports:
        z0 = layout["lid_top_z"] + float(port["boss_height_z"]) if assembly_position else 0.0
        adapter = (
            cq.Workplane("XY")
            .circle(adapter_d / 2)
            .extrude(adapter_h)
            .translate((float(port["x"]), float(port["y"]), z0))
        )
        adapters = adapter if adapters is None else adapters.union(adapter)
    if adapters is None:
        raise ValueError("flow test adapter requires a sample/relief port")
    return adapters


def build_missing_sample_relief_cap_witness(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    ring_w = production.get("sample_relief_cap_missing_witness_ring_width_xy", 0.8)
    witness_h = production.get("sample_relief_cap_missing_witness_height_z", 0.6)
    flag_len = production.get("sample_relief_cap_missing_witness_flag_length_xy", 6.0)
    flag_w = production.get("sample_relief_cap_missing_witness_flag_width_xy", 1.4)

    witnesses: cq.Workplane | None = None
    for port in _lid_port_positions(layout, params):
        boss_h = float(port["boss_height_z"])
        inner_d = float(port["cap_flange_diameter"])
        height = witness_h
        z0 = layout["lid_top_z"] + boss_h if assembly_position else 0.0
        outer_d = inner_d + 2 * ring_w
        witness = (
            cq.Workplane("XY")
            .circle(outer_d / 2)
            .circle(inner_d / 2)
            .extrude(height)
            .translate((float(port["x"]), float(port["y"]), z0))
        )
        witness = _add_sample_relief_cap_review_flag(
            witness,
            port=port,
            layout=layout,
            z0=z0,
            length=flag_len,
            width=flag_w,
            height=height,
            radial_from_diameter=outer_d,
        )
        witnesses = witness if witnesses is None else witnesses.union(witness)
    if witnesses is None:
        raise ValueError("missing sample/relief cap witness requires a lid port")
    return witnesses


def build_printed_sample_relief_cap(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    ports = [
        port for port in _lid_port_positions(layout, params) if port["role"] == "sample_relief"
    ]
    if len(ports) != 1:
        raise ValueError("printed sample/relief cap requires exactly one sample/relief port")

    port = ports[0]
    plug_depth = production.get("port_cap_plug_depth_z", 0.0)
    plug_bottom_z = (
        layout["lid_top_z"] + float(port["boss_height_z"]) - plug_depth
        if assembly_position
        else 0.0
    )
    return _build_port_cap_body(
        x=float(port["x"]),
        y=float(port["y"]),
        plug_d=float(port["cap_plug_diameter"]),
        flange_d=float(port["cap_flange_diameter"]),
        plug_bottom_z=plug_bottom_z,
        plug_depth=plug_depth,
        flange_h=production.get("port_cap_flange_height_z", 0.0),
        seal_lip_inner_d=float(port["cap_seal_lip_inner_diameter"]),
        seal_lip_outer_d=float(port["cap_seal_lip_outer_diameter"]),
        seal_lip_h=float(port["cap_seal_lip_height_z"]),
        grip_len=production.get("port_cap_grip_length_xy", 0.0),
        grip_w=production.get("port_cap_grip_width_xy", 0.0),
        grip_h=production.get("port_cap_grip_height_z", 0.0),
        grip_overlap=production.get("port_cap_grip_attachment_overlap_xy", 0.0),
        layout=layout,
    )


def build_sample_relief_leak_witness_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["sample_relief_leak_witness_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_unseated_sample_relief_cap_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    plug_depth = production.get("port_cap_plug_depth_z", 0.0)
    flange_h = production.get("port_cap_flange_height_z", 0.0)
    grip_h = production.get("port_cap_grip_height_z", 0.0)
    grip_len = production.get("port_cap_grip_length_xy", 0.0)
    grip_w = production.get("port_cap_grip_width_xy", 0.0)
    grip_overlap = production.get("port_cap_grip_attachment_overlap_xy", 0.0)
    unseated_lift = production.get("sample_relief_cap_unseated_lift_z", 0.0)
    port_positions = _lid_port_positions(layout, params)

    caps: cq.Workplane | None = None
    for port in port_positions:
        x = float(port["x"])
        y = float(port["y"])
        boss_h = float(port["boss_height_z"])
        plug_d = float(port["cap_plug_diameter"])
        flange_d = float(port["cap_flange_diameter"])
        plug_bottom_z = (
            layout["lid_top_z"] + boss_h - plug_depth + unseated_lift
            if assembly_position
            else 0.0
        )
        cap = _build_port_cap_body(
            x=x,
            y=y,
            plug_d=plug_d,
            flange_d=flange_d,
            plug_bottom_z=plug_bottom_z,
            plug_depth=plug_depth,
            flange_h=flange_h,
            seal_lip_inner_d=float(port["cap_seal_lip_inner_diameter"]),
            seal_lip_outer_d=float(port["cap_seal_lip_outer_diameter"]),
            seal_lip_h=float(port["cap_seal_lip_height_z"]),
            grip_len=grip_len,
            grip_w=grip_w,
            grip_h=grip_h,
            grip_overlap=grip_overlap,
            layout=layout,
        )
        caps = cap if caps is None else caps.union(cap)
    if caps is None:
        raise ValueError("sample/relief cap unseated review requires a lid port")
    return caps
