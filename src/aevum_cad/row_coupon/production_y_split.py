from __future__ import annotations
from pathlib import Path
from typing import Any
import cadquery as cq
from .layout import (row_coupon_layout)


def _clip_workplane_to_y_range(
    model: cq.Workplane,
    *,
    y_min: float,
    y_max: float,
) -> cq.Workplane:
    bbox = model.val().BoundingBox()
    pad = 1.0
    mask = (
        cq.Workplane("XY")
        .box(
            float(bbox.xlen) + 2 * pad,
            y_max - y_min,
            float(bbox.zlen) + 2 * pad,
            centered=(False, False, False),
        )
        .translate(
            (
                float(bbox.xmin) - pad,
                y_min,
                float(bbox.zmin) - pad,
            )
        )
    )
    return model.intersect(mask)


def _production_y_split_parts(params: dict[str, Any]) -> tuple[str, ...]:
    from aevum_cad.row_coupon import (ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS)
    production = params.get("production_assembly", {})
    configured = production.get("first_print_y_split_parts")
    if configured is None:
        return ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS
    return tuple(str(part) for part in configured)


def _production_y_split_segments(params: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    layout = row_coupon_layout(params)
    if layout["row_axis"] != "y":
        raise ValueError("production Y splits require a row configured on the Y axis")
    production = params.get("production_assembly", {})
    segment_count = int(production.get("first_print_y_split_segment_count", 2))
    if segment_count != 2:
        raise ValueError("production Y split currently supports exactly two segments")
    tile_origins = sorted(layout["tile_origins"], key=lambda tile: float(tile["y"]))
    if len(tile_origins) < 2:
        raise ValueError("production Y split requires at least two plate tiles")
    split_after = len(tile_origins) // 2
    lower_tile = tile_origins[split_after - 1]
    upper_tile = tile_origins[split_after]
    split_y = round(
        (
            float(lower_tile["y"])
            + float(params["plate"]["width_y"])
            + float(upper_tile["y"])
        )
        / 2,
        3,
    )
    return (
        {
            "segment_index": 1,
            "segment_count": segment_count,
            "suffix": "y01_of_02",
            "y_min": 0.0,
            "y_max": split_y,
            "interface_zone": f"between_plate_{lower_tile['index']}_and_{upper_tile['index']}",
            "interface_role": "lower segment terminates at inter-plate service gap",
            "retention": (
                "existing deck keys, tongue/groove, snap covers, and wedge locks "
                "must retain this split segment without screws or glue"
            ),
        },
        {
            "segment_index": 2,
            "segment_count": segment_count,
            "suffix": "y02_of_02",
            "y_min": split_y,
            "y_max": float(layout["width_y"]),
            "interface_zone": f"between_plate_{lower_tile['index']}_and_{upper_tile['index']}",
            "interface_role": "upper segment starts at inter-plate service gap",
            "retention": (
                "existing deck keys, tongue/groove, snap covers, and wedge locks "
                "must retain this split segment without screws or glue"
            ),
        },
    )


def build_row_coupon_production_y_split_parts(
    params: dict[str, Any],
) -> dict[str, cq.Workplane]:
    from aevum_cad.row_coupon import (_row_coupon_export_models)
    models = _row_coupon_export_models(params)
    split_parts: dict[str, cq.Workplane] = {}
    for row in row_coupon_production_y_split_plan(params):
        source_part = str(row["source_part"])
        if source_part not in models:
            raise ValueError(f"unknown production Y split source part: {source_part}")
        split_parts[str(row["name"])] = _clip_workplane_to_y_range(
            models[source_part],
            y_min=float(row["y_min"]),
            y_max=float(row["y_max"]),
        )
    return split_parts


def export_row_coupon_production_y_split_parts(
    params: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    for name, model in build_row_coupon_production_y_split_parts(params).items():
        stl_path = out / f"{params['name']}_{name}.stl"
        step_path = out / f"{params['name']}_{name}.step"
        cq.exporters.export(model, str(stl_path))
        cq.exporters.export(model, str(step_path))
        paths[f"{name}_stl"] = stl_path
        paths[f"{name}_step"] = step_path
    return paths


def row_coupon_production_y_split_plan(
    params: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Return first-print production split rows for oversized printed bodies."""

    rows: list[dict[str, Any]] = []
    for part in _production_y_split_parts(params):
        for segment in _production_y_split_segments(params):
            rows.append(
                {
                    "name": f"{part}_{segment['suffix']}",
                    "source_part": part,
                    "segment_index": segment["segment_index"],
                    "segment_count": segment["segment_count"],
                    "y_min": segment["y_min"],
                    "y_max": segment["y_max"],
                    "interface_zone": segment["interface_zone"],
                    "interface_role": segment["interface_role"],
                    "retention": segment["retention"],
                    "sealing": (
                        "split lies in the inter-plate service gap; wet-frame, "
                        "lid-shell, and lid-cover split segments require Gate 4 "
                        "dye evidence before wet operation"
                    ),
                    "serviceability": (
                        "plate, septum, sensor, gas-PCB, gas-tube, and latch service "
                        "checks remain required on the assembled split stack"
                    ),
                    "required_evidence": (
                        "Gate 1 dimensions, Gate 2 dry assembly, Gate 4 wet/dry "
                        "witness, and selected-slicer bed-fit evidence before this "
                        "split artifact replaces the monolithic queue part"
                    ),
                }
            )
    return tuple(rows)
