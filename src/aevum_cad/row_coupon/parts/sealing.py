from __future__ import annotations
from typing import Any
import cadquery as cq
from ..layout import (row_coupon_layout)
from ._geom_base import (_boxes_from_rectangles, _perimeter_rails)


def _add_gasket_service_tabs(
    gasket: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    production = params.get("production_assembly", {})
    tab_len = production.get("gasket_service_tab_length_x", 0.0)
    tab_depth = production.get("gasket_service_tab_depth_y", 0.0)
    if tab_len <= 0 or tab_depth <= 0:
        return gasket

    rail_w = seal["gasket_rail_width"]
    rail_h = seal["compressed_gasket_height_z"]
    x0 = (layout["length_x"] - tab_len) / 2
    y_values = [
        rail_w,
        layout["width_y"] - rail_w - tab_depth,
    ]
    for y in y_values:
        gasket = gasket.union(
            cq.Workplane("XY")
            .box(tab_len, tab_depth, rail_h, centered=(False, False, False))
            .translate((x0, y, z0))
        )
    return gasket


def _add_lid_cover_tongue(
    cover: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    tongue_d = production.get("lid_cover_tongue_depth_z", 0.0)
    ring = _lid_cover_tongue_ring(params=params, z0=z0 - tongue_d)
    if ring is None:
        return cover
    return cover.union(ring)


def _cut_gasket_capture_groove(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
    from_side: str,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    production = params.get("production_assembly", {})
    depth = production.get("gasket_capture_depth_z", 0.0)
    clearance = production.get("gasket_capture_clearance_xy", 0.0)
    outer_land = min(
        production.get("gasket_capture_outer_land_xy", 0.8),
        seal["gasket_rail_width"] - 0.2,
    )
    if depth <= 0:
        return model
    if from_side not in {"top", "bottom"}:
        raise ValueError("gasket capture groove side must be top or bottom")

    groove_z = z0 - depth if from_side == "top" else z0 - 0.05
    cutter = _perimeter_rails(
        x0=outer_land,
        y0=outer_land,
        length=layout["length_x"] - 2 * outer_land,
        width=layout["width_y"] - 2 * outer_land,
        rail_width=seal["gasket_rail_width"] - outer_land + clearance,
        height=depth + 0.1,
        z0=groove_z,
    )
    return model.cut(cutter)


def _cut_lid_cover_tongue_groove(
    shell: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    tongue_d = production.get("lid_cover_tongue_depth_z", 0.0)
    clearance = production.get("lid_cover_tongue_clearance_xy", 0.0)
    if tongue_d <= 0:
        return shell

    groove = _lid_cover_tongue_ring(
        params=params,
        z0=z0 + params["lid_manifold"]["thickness_z"] - tongue_d - 0.05,
        width_extra=2 * clearance,
    )
    if groove is None:
        return shell
    return shell.cut(groove)


def _cut_rectangular_gas_interface_window(
    model: cq.Workplane,
    rect: dict[str, Any],
    *,
    z_shift: float = 0.0,
) -> cq.Workplane:
    return model.cut(
        cq.Workplane("XY")
        .box(
            float(rect["length_x"]) + 0.2,
            float(rect["width_y"]) + 0.2,
            float(rect["height_z"]) + 0.2,
            centered=(False, False, False),
        )
        .translate(
            (
                float(rect["x"]) - 0.1,
                float(rect["y"]) - 0.1,
                float(rect["z"]) + z_shift - 0.1,
            )
        )
    )


def _gasket_compression_gap_gauge_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_budget: dict[str, Any],
) -> dict[str, Any]:
    mechanics = params.get("latch_mechanics", {})
    metrology = params.get("consumable_metrology", {})
    blade_len = float(mechanics.get("gasket_compression_gauge_blade_length_x", 26.0))
    blade_width = float(mechanics.get("gasket_compression_gauge_blade_width_y", 5.0))
    blade_gap = float(mechanics.get("gasket_compression_gauge_blade_gap_y", 2.0))
    length_step = float(mechanics.get("gasket_compression_gauge_length_step_x", 5.0))
    x0 = float(layout["length_x"]) + float(metrology.get("viewer_offset_x", 18.0))

    blade_sources = [
        (
            "minimum_squeeze_blade",
            "minimum_gasket_squeeze_reference",
            float(compression_budget["gasket_squeeze_min_z"]),
        ),
        (
            "target_squeeze_blade",
            "target_gasket_squeeze_reference",
            float(compression_budget["gasket_squeeze_target_z"]),
        ),
        (
            "maximum_squeeze_blade",
            "maximum_gasket_squeeze_reference",
            float(compression_budget["gasket_squeeze_max_z"]),
        ),
    ]
    blades = [
        {
            "name": name,
            "role": role,
            "x": 0.0,
            "y": round(index * (blade_width + blade_gap), 3),
            "z": 0.0,
            "length_x": round(blade_len + index * length_step, 3),
            "width_y": round(blade_width, 3),
            "thickness_z": round(thickness, 3),
        }
        for index, (name, role, thickness) in enumerate(blade_sources)
    ]
    total_width = blade_width * len(blades) + blade_gap * max(0, len(blades) - 1)
    body_rects = [
        {
            **blade,
            "x": round(x0 + float(blade["x"]), 3),
            "y": round(float(blade["y"]), 3),
            "height_z": blade["thickness_z"],
        }
        for blade in blades
    ]
    return {
        "name": "gasket_compression_gap_gauge",
        "role": "dry_assembly_gasket_squeeze_gap_reference",
        "source": "latch_compression_budget",
        "evidence_gate": "Gate 2 dry assembly",
        "failure_rule": "gasket_squeeze_out_of_range_blocks_dry_assembly_pass",
        "cad_value": (
            f"{float(compression_budget['gasket_squeeze_target_z']):.2f} mm target / "
            f"{float(compression_budget['gasket_squeeze_min_z']):.2f}.."
            f"{float(compression_budget['gasket_squeeze_max_z']):.2f} mm allowed"
        ),
        "x": round(x0, 3),
        "y": 0.0,
        "blade_count": len(blades),
        "blade_length_x": round(blade_len, 3),
        "blade_width_y": round(blade_width, 3),
        "blade_gap_y": round(blade_gap, 3),
        "length_step_x": round(length_step, 3),
        "total_width_y": round(total_width, 3),
        "min_squeeze_z": compression_budget["gasket_squeeze_min_z"],
        "target_squeeze_z": compression_budget["gasket_squeeze_target_z"],
        "max_squeeze_z": compression_budget["gasket_squeeze_max_z"],
        "bounded_squeeze_z": compression_budget["bounded_squeeze_z"],
        "blades": blades,
        "validation": "physical_gap_blades_require_printed_gate2_measurement",
        "source_layout_checks": ["latch_compression_budget"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "gasket_compression_in_range",
            "sealed_wet_headspace_perimeter",
            "latches_seated_before_wet_tests",
            "wet_operation_without_gasket_overcrush",
        ],
        "body_rects": body_rects,
    }


def _gasket_squeeze_out_of_range_review_rectangles(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_stop_positions: list[tuple[float, float]],
    compression_budget: dict[str, Any],
    base_top_z: float,
) -> list[dict[str, Any]]:
    seal = params["seal_interface"]
    mechanics = params.get("latch_mechanics", {})
    production = params.get("production_assembly", {})
    witness_size = min(
        float(production.get("gasket_squeeze_review_size_xy", 3.0)),
        float(seal["compression_stop_size"]) * 0.8,
    )
    witness_gap = float(production.get("gasket_squeeze_review_gap_xy", 0.8))
    overcrush_h = max(
        float(mechanics.get("gasket_squeeze_review_overcrush_height_z", 0.08)),
        float(compression_budget["gasket_squeeze_min_z"]) * 0.5,
    )
    undersqueeze_h = float(compression_budget["gasket_squeeze_max_z"]) + float(
        mechanics.get("gasket_squeeze_review_undersqueeze_extra_z", 0.35)
    )
    layout_len = float(layout["length_x"])
    layout_wid = float(layout["width_y"])

    def bounded_origin(center: float, size: float, *, positive: bool, limit: float) -> float:
        raw = center + witness_gap / 2 if positive else center - witness_gap / 2 - size
        return max(0.0, min(limit - size, raw))

    rects: list[dict[str, Any]] = []
    source_checks = [
        "gasket_compression_gap_gauge",
        "latch_retention_span_check",
        "assembly_state_witness_check",
    ]
    for index, (stop_x, stop_y) in enumerate(compression_stop_positions, start=1):
        base = {
            "review_state": "gasket_squeeze_out_of_range",
            "owner_part": "gasket_squeeze_out_of_range_review",
            "retained_part": "lower_gasket_and_upper_gasket",
            "blocked_fail_closed_state": "gasket_squeeze_out_of_range",
            "source_validation_checks": source_checks,
            "stop_index": index,
            "stop_x": round(float(stop_x), 3),
            "stop_y": round(float(stop_y), 3),
            "allowed_min_squeeze_z": compression_budget["gasket_squeeze_min_z"],
            "allowed_max_squeeze_z": compression_budget["gasket_squeeze_max_z"],
        }
        y0 = max(0.0, min(layout_wid - witness_size, float(stop_y) - witness_size / 2))
        rects.extend(
            [
                {
                    **base,
                    "name": f"compression_stop_{index:02d}_overcrush_review",
                    "review_kind": "gasket_overcompressed_below_min_gap",
                    "measured_squeeze_relation": "above_allowed_max_squeeze",
                    "x": round(
                        bounded_origin(
                            float(stop_x),
                            witness_size,
                            positive=False,
                            limit=layout_len,
                        ),
                        3,
                    ),
                    "y": round(y0, 3),
                    "z": round(float(base_top_z), 3),
                    "length_x": round(witness_size, 3),
                    "width_y": round(witness_size, 3),
                    "height_z": round(overcrush_h, 3),
                },
                {
                    **base,
                    "name": f"compression_stop_{index:02d}_undersqueeze_review",
                    "review_kind": "gasket_undercompressed_above_max_gap",
                    "measured_squeeze_relation": "below_allowed_min_squeeze",
                    "x": round(
                        bounded_origin(
                            float(stop_x),
                            witness_size,
                            positive=True,
                            limit=layout_len,
                        ),
                        3,
                    ),
                    "y": round(y0, 3),
                    "z": round(float(base_top_z), 3),
                    "length_x": round(witness_size, 3),
                    "width_y": round(witness_size, 3),
                    "height_z": round(undersqueeze_h, 3),
                },
            ]
        )
    return rects


def _lid_cover_tongue_ring(
    *,
    params: dict[str, Any],
    z0: float,
    width_extra: float = 0.0,
) -> cq.Workplane | None:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    tongue_w = production.get("lid_cover_tongue_width", 0.0) + width_extra
    tongue_d = production.get("lid_cover_tongue_depth_z", 0.0)
    if tongue_w <= 0 or tongue_d <= 0:
        return None

    inset = params["wet_chamber_skirt"]["wall_thickness"] + 0.6 - width_extra / 2
    length = layout["length_x"] - 2 * inset
    width = layout["width_y"] - 2 * inset
    if length <= 2 * tongue_w or width <= 2 * tongue_w:
        return None
    return _perimeter_rails(
        x0=inset,
        y0=inset,
        length=length,
        width=width,
        rail_width=tongue_w,
        height=tongue_d,
        z0=z0,
    )


def build_gas_pcb_interface_gaskets(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    gaskets: cq.Workplane | None = None
    for mount in layout["gas_sensor_pcb_mounts"]:
        interface = mount["gas_interface"]
        gasket = _boxes_from_rectangles([interface["gasket_rect"]], z_shift=z_shift)
        gasket = _cut_rectangular_gas_interface_window(
            gasket,
            interface["gasket_window_rect"],
            z_shift=z_shift,
        )
        gaskets = gasket if gaskets is None else gaskets.union(gasket)
    if gaskets is None:
        raise ValueError("gas PCB interface gaskets require at least one mount")
    return gaskets


def build_gasket_compression_gap_gauge(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    gauge = layout["gasket_compression_gap_gauge"]
    rects = gauge["body_rects"]
    if not assembly_position:
        rects = [
            {
                **rect,
                "x": round(float(rect["x"]) - float(gauge["x"]), 3),
                "y": round(float(rect["y"]) - float(gauge["y"]), 3),
            }
            for rect in rects
        ]
    return _boxes_from_rectangles(rects)


def build_gasket_squeeze_out_of_range_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["gasket_squeeze_out_of_range_review"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_ir_thermopile_face_gaskets(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    gaskets: cq.Workplane | None = None
    for mount in layout["ir_sensor_mounts"]:
        gasket = mount["face_gasket"]
        z = float(gasket["z"]) if assembly_position else 0.0
        body = (
            cq.Workplane("XY")
            .circle(float(gasket["outer_diameter"]) / 2)
            .extrude(float(gasket["height_z"]))
            .translate((float(gasket["x"]), float(gasket["y"]), z))
        )
        aperture = (
            cq.Workplane("XY")
            .circle(float(gasket["inner_diameter"]) / 2)
            .extrude(float(gasket["height_z"]) + 0.2)
            .translate((float(gasket["x"]), float(gasket["y"]), z - 0.1))
        )
        gasket_body = body.cut(aperture)
        gaskets = gasket_body if gaskets is None else gaskets.union(gasket_body)
    if gaskets is None:
        raise ValueError("IR thermopile face gaskets require at least one mount")
    return gaskets


def build_lid_gasket(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    from aevum_cad.row_coupon import (_shared_chamber_bounds)
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    rail_w = seal["gasket_rail_width"]
    rail_h = seal["compressed_gasket_height_z"]
    z0 = layout["gasket_bottom_z"] if assembly_position else 0.0
    bounds = _shared_chamber_bounds(layout, params)

    gasket = _perimeter_rails(
        x0=bounds["x"],
        y0=bounds["y"],
        length=bounds["length_x"],
        width=bounds["width_y"],
        rail_width=rail_w,
        height=rail_h,
        z0=z0,
    )
    return _add_gasket_service_tabs(gasket, params=params, z0=z0)


def build_lower_gasket(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    from aevum_cad.row_coupon import (_shared_chamber_bounds)
    layout = row_coupon_layout(params)
    seal = params["seal_interface"]
    rail_w = seal["gasket_rail_width"]
    rail_h = seal["compressed_gasket_height_z"]
    z0 = layout["base_top_z"] if assembly_position else 0.0
    bounds = _shared_chamber_bounds(layout, params)

    gasket = _perimeter_rails(
        x0=bounds["x"],
        y0=bounds["y"],
        length=bounds["length_x"],
        width=bounds["width_y"],
        rail_width=rail_w,
        height=rail_h,
        z0=z0,
    )
    return _add_gasket_service_tabs(gasket, params=params, z0=z0)


def build_upper_gasket(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    return build_lid_gasket(params, assembly_position=assembly_position)
