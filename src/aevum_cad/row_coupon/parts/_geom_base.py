from __future__ import annotations

from typing import Any

import cadquery as cq


def _integral_feature_fusion_overlap_z(params: dict[str, Any]) -> float:
    return max(
        0.0,
        float(
            params.get("production_assembly", {}).get(
                "integral_feature_fusion_overlap_z",
                0.10,
            )
        ),
    )


def _fused_z_box(
    *,
    length: float,
    width: float,
    height: float,
    x: float,
    y: float,
    z: float,
    overlap_z: float,
    into: str,
) -> cq.Workplane:
    if into not in {"down", "up"}:
        raise ValueError("fused z box must overlap 'down' or 'up'")
    if overlap_z < 0:
        raise ValueError("fused z box overlap must be non-negative")
    fused_z = z - overlap_z if into == "down" else z
    return (
        cq.Workplane("XY")
        .box(length, width, height + overlap_z, centered=(False, False, False))
        .translate((x, y, fused_z))
    )


def _rounded_box(length: float, width: float, height: float, radius: float) -> cq.Workplane:
    part = cq.Workplane("XY").box(length, width, height, centered=(False, False, False))
    if radius > 0:
        part = part.edges("|Z").fillet(radius)
    return part


def _perimeter_rails(
    *,
    x0: float,
    y0: float,
    length: float,
    width: float,
    rail_width: float,
    height: float,
    z0: float,
) -> cq.Workplane:
    rails: cq.Workplane | None = None
    segments = [
        (x0, y0, length, rail_width),
        (x0, y0 + width - rail_width, length, rail_width),
        (x0, y0 + rail_width, rail_width, width - 2 * rail_width),
        (x0 + length - rail_width, y0 + rail_width, rail_width, width - 2 * rail_width),
    ]
    for x, y, segment_len, segment_wid in segments:
        part = (
            cq.Workplane("XY")
            .box(segment_len, segment_wid, height, centered=(False, False, False))
            .translate((x, y, z0))
        )
        rails = part if rails is None else rails.union(part)
    if rails is None:
        raise ValueError("perimeter rails require at least one segment")
    return rails


def _rectangle_intersects_circle(
    rect: dict[str, float],
    circle_x: float,
    circle_y: float,
    radius: float,
) -> bool:
    closest_x = min(max(circle_x, rect["x"]), rect["x"] + rect["length_x"])
    closest_y = min(max(circle_y, rect["y"]), rect["y"] + rect["width_y"])
    return (closest_x - circle_x) ** 2 + (closest_y - circle_y) ** 2 <= radius**2


def _axis_cylinder_envelope_rect(
    *,
    axis: str,
    x: float,
    y: float,
    z: float,
    length: float,
    diameter: float,
) -> dict[str, float]:
    if axis == "x":
        return {
            "x": round(x, 3),
            "y": round(y - diameter / 2, 3),
            "z": round(z - diameter / 2, 3),
            "length_x": round(length, 3),
            "width_y": round(diameter, 3),
            "height_z": round(diameter, 3),
        }
    if axis == "y":
        return {
            "x": round(x - diameter / 2, 3),
            "y": round(y, 3),
            "z": round(z - diameter / 2, 3),
            "length_x": round(diameter, 3),
            "width_y": round(length, 3),
            "height_z": round(diameter, 3),
        }
    raise ValueError("axis envelope must use axis 'x' or 'y'")


def _rectangles_overlap_xy(
    first: dict[str, Any],
    second: dict[str, Any],
) -> bool:
    return (
        float(first["x"]) < float(second["x"]) + float(second["length_x"])
        and float(second["x"]) < float(first["x"]) + float(first["length_x"])
        and float(first["y"]) < float(second["y"]) + float(second["width_y"])
        and float(second["y"]) < float(first["y"]) + float(first["width_y"])
    )


def _rectangles_bounding_extents(
    rects: list[dict[str, Any]],
) -> tuple[float, float, float]:
    if not rects:
        return 0.0, 0.0, 0.0
    x_min = min(float(rect["x"]) for rect in rects)
    y_min = min(float(rect["y"]) for rect in rects)
    z_min = min(float(rect["z"]) for rect in rects)
    x_max = max(float(rect["x"]) + float(rect["length_x"]) for rect in rects)
    y_max = max(float(rect["y"]) + float(rect["width_y"]) for rect in rects)
    z_max = max(float(rect["z"]) + float(rect["height_z"]) for rect in rects)
    return x_max - x_min, y_max - y_min, z_max - z_min


def _harness_z_shift(
    rects: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    assembly_position: bool,
) -> float:
    if assembly_position:
        return 0.0
    return -min(float(rect["z"]) for rect in rects)


def _boxes_from_rectangles(
    rects: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    z_shift: float = 0.0,
    expand_xy: float = 0.0,
    height: float | None = None,
    z_override: float | None = None,
) -> cq.Workplane:
    model: cq.Workplane | None = None
    for rect in rects:
        rect_h = float(height if height is not None else rect["height_z"])
        z = float(z_override if z_override is not None else rect["z"]) + z_shift
        part = (
            cq.Workplane("XY")
            .box(
                float(rect["length_x"]) + 2 * expand_xy,
                float(rect["width_y"]) + 2 * expand_xy,
                rect_h,
                centered=(False, False, False),
            )
            .translate((float(rect["x"]) - expand_xy, float(rect["y"]) - expand_xy, z))
        )
        model = part if model is None else model.union(part)
    if model is None:
        raise ValueError("harness rectangle model requires at least one rectangle")
    return model


def _bodies_from_shape_targets(
    targets: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    z_shift: float = 0.0,
) -> cq.Workplane:
    model: cq.Workplane | None = None
    for target in targets:
        z = float(target["z"]) + z_shift
        if target.get("shape") == "disk" or "diameter" in target:
            body = (
                cq.Workplane("XY")
                .circle(float(target["diameter"]) / 2)
                .extrude(float(target["height_z"]))
                .translate((float(target["x"]), float(target["y"]), z))
            )
        else:
            body = (
                cq.Workplane("XY")
                .box(
                    float(target["length_x"]),
                    float(target["width_y"]),
                    float(target["height_z"]),
                    centered=(False, False, False),
                )
                .translate((float(target["x"]), float(target["y"]), z))
            )
        model = body if model is None else model.union(body)
    if model is None:
        raise ValueError("shape target model requires at least one target")
    return model


def _axis_cylinder(
    *,
    axis: str,
    x: float,
    y: float,
    z: float,
    length: float,
    diameter: float,
) -> cq.Workplane:
    radius = diameter / 2
    if axis == "x":
        return cq.Workplane("YZ").circle(radius).extrude(length).translate((x, y, z))
    if axis == "y":
        return cq.Workplane("XZ").circle(radius).extrude(length).translate((x, y, z))
    raise ValueError("axis cylinder must use axis 'x' or 'y'")


def _axis_tube(
    *,
    axis: str,
    x: float,
    y: float,
    z: float,
    length: float,
    outer_diameter: float,
    inner_diameter: float,
) -> cq.Workplane:
    if inner_diameter <= 0:
        return _axis_cylinder(
            axis=axis,
            x=x,
            y=y,
            z=z,
            length=length,
            diameter=outer_diameter,
        )
    if inner_diameter >= outer_diameter:
        raise ValueError("axis tube inner diameter must be smaller than outer diameter")

    outer = _axis_cylinder(
        axis=axis,
        x=x,
        y=y,
        z=z,
        length=length,
        diameter=outer_diameter,
    )
    if axis == "x":
        inner = _axis_cylinder(
            axis=axis,
            x=x - 0.05,
            y=y,
            z=z,
            length=length + 0.1,
            diameter=inner_diameter,
        )
    elif axis == "y":
        inner = _axis_cylinder(
            axis=axis,
            x=x,
            y=y - 0.05,
            z=z,
            length=length + 0.1,
            diameter=inner_diameter,
        )
    else:
        raise ValueError("axis tube must use axis 'x' or 'y'")
    return outer.cut(inner)
