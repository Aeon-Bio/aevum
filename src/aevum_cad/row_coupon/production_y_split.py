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


def _keyed_split_interface(
    model: cq.Workplane,
    *,
    y_min: float,
    y_max: float,
    split_y: float,
    interface: dict[str, Any],
) -> cq.Workplane:
    """D4 keyed split interface (flag-on only). Starts from the butt half, then adds a
    PRINTED dovetail anti-shear key straddling split_y (its slanted X walls are non-axis
    PLANE faces => non-flat seam) plus a witness pip on the lower half, and the
    clearance-inflated mating pocket on the upper half. Complementary by construction:
    both halves reference the same split_y, so the lower protrusion fits the upper pocket.
    No metal — all box/polyline/union/cut on the polymer body."""
    base = _clip_workplane_to_y_range(model, y_min=y_min, y_max=y_max)
    is_lower = abs(y_max - split_y) < 1e-6
    is_upper = abs(y_min - split_y) < 1e-6
    if not (is_lower or is_upper):
        return base

    bb = base.val().BoundingBox()
    x_center = (float(bb.xmin) + float(bb.xmax)) / 2.0
    zlen = float(bb.zlen)
    clr = float(interface.get("fit_class_clearance_mm", 0.2))
    half_span = float(interface.get("key_half_span_y", 3.0))
    narrow_x = float(interface.get("key_narrow_x", 6.0))
    wide_x = float(interface.get("key_wide_x", 10.0))
    # clamp the key depth to fit thin bodies (e.g. 0.8mm keeper doors)
    key_depth = min(float(interface.get("key_depth_mm", 4.0)), max(zlen - 0.4, 0.4))
    z0 = float(bb.zmin) + (zlen - key_depth) / 2.0

    def _dovetail(nx: float, wx: float) -> cq.Workplane:
        pts = [
            (x_center - nx / 2, split_y - half_span),
            (x_center + nx / 2, split_y - half_span),
            (x_center + wx / 2, split_y + half_span),
            (x_center - wx / 2, split_y + half_span),
        ]
        return (
            cq.Workplane("XY").polyline(pts).close().extrude(key_depth).translate((0, 0, z0))
        )

    if is_lower:
        w_w = float(interface.get("witness_width_mm", 1.0))
        w_l = float(interface.get("witness_len_mm", 2.0))
        w_h = float(interface.get("witness_height_mm", 0.5))
        witness = (
            cq.Workplane("XY")
            .box(w_w, w_l, w_h, centered=(True, False, False))
            .translate((x_center, split_y - w_l / 2, float(bb.zmax) - w_h))
        )
        return base.union(_dovetail(narrow_x, wide_x)).union(witness)
    # upper half: clearance-inflated mating pocket
    return base.cut(_dovetail(narrow_x + 2 * clr, wide_x + 2 * clr))


def _production_y_split_parts(params: dict[str, Any]) -> tuple[str, ...]:
    from aevum_cad.row_coupon import (ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS)
    production = params.get("production_assembly", {})
    configured = production.get("first_print_y_split_parts")
    if configured is None:
        return ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS
    return tuple(str(part) for part in configured)


def _split_y_from_tile_origins(
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
) -> float:
    """Single source of truth for the structural split_y (D1/D4/D5 share this datum).
    Pure function of the sorted plate tile origins + plate width — no layout call, so it
    can be consumed from inside ``row_coupon_layout`` without recursion."""
    ordered = sorted(tile_origins, key=lambda tile: float(tile["y"]))
    if len(ordered) < 2:
        raise ValueError("production Y split requires at least two plate tiles")
    split_after = len(ordered) // 2
    lower_tile = ordered[split_after - 1]
    upper_tile = ordered[split_after]
    return round(
        (
            float(lower_tile["y"])
            + float(params["plate"]["width_y"])
            + float(upper_tile["y"])
        )
        / 2,
        3,
    )


def _two_module_joint_metadata(
    *,
    params: dict[str, Any],
    split_y: float,
    lower_tile: dict[str, Any],
    upper_tile: dict[str, Any],
) -> dict[str, Any]:
    """D1 2-module joint descriptor (flag-on only). Composition/metadata that ties the
    already-shipped D4 keyed seam (``_keyed_split_interface``: printed dovetail anti-shear
    key + witness pip + clearance pocket straddling ``split_y``) and the D5 captured seal
    (``_add_gasket_capture_split_lap``: printed labyrinth tongue lap bridging the gasket
    capture groove across ``split_y``) into ONE coherent 2-module joint at the inter-plate
    service gap. Pure metadata — emits NO geometry of its own, so the keyed/sealed features
    remain owned by D4/D5; this only names the intentional module boundary and asserts the
    retention is printed-feature-only (no metal pins/screws/inserts, plate untouched).

    ``split_y`` is CONSUMED from the split-policy owner (the same datum D4/D5 read), not
    re-derived, so the joint description always matches the geometry that lands at the seam."""
    production = params.get("production_assembly", {})
    interface = production.get("y_split_interface", {}) or {}
    return {
        "joint_id": f"two_module_joint_{lower_tile['index']}_{upper_tile['index']}",
        "split_y": split_y,
        "module_boundary": "inter-plate service gap (intentional 2-module split)",
        "keyed_seam": (
            "D4 printed dovetail anti-shear key with witness pip on the lower module and "
            "a clearance-inflated mating pocket on the upper module, straddling split_y"
        ),
        "key_half_span_y": float(interface.get("key_half_span_y", 3.0)),
        "captured_seal": (
            "D5 printed labyrinth tongue lap bridges the gasket capture groove across "
            "split_y, so the seal crossing is a tongue/groove lap, not a flat butt"
        ),
        "seal_lap_len_y": float(production.get("gasket_capture_split_lap_len_y", 8.0)),
        "retention_authority": (
            "joint is retained by printed dovetail key, wedge locks, and the tongue/groove "
            "seal lap only — no screws, glue, or metal inserts; nothing grips the plate"
        ),
    }


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
    split_y = _split_y_from_tile_origins(tile_origins, params)
    lower_segment: dict[str, Any] = {
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
    }
    upper_segment: dict[str, Any] = {
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
    }
    if bool(production.get("keyed_joints_enabled", False)):
        # D1 flag-on: tie the D4 keyed seam + D5 captured seal into one coherent
        # 2-module joint descriptor on each module. segment_count stays 2 (the joint
        # is the intentional module boundary, not a new bay subdivision). Pure metadata;
        # flag-off leaves the two segment dicts byte-identical to the pre-D1 tuple.
        joint = _two_module_joint_metadata(
            params=params,
            split_y=split_y,
            lower_tile=lower_tile,
            upper_tile=upper_tile,
        )
        lower_segment["joint"] = {**joint, "joint_role": "lower module of two_module_joint"}
        upper_segment["joint"] = {**joint, "joint_role": "upper module of two_module_joint"}
    return (lower_segment, upper_segment)


def build_row_coupon_production_y_split_parts(
    params: dict[str, Any],
) -> dict[str, cq.Workplane]:
    from aevum_cad.row_coupon import (_row_coupon_export_models)
    pa = params.get("production_assembly", {})
    # The Y-split operates on full-row FUSED bodies; suppress per-instance latch
    # packaging (D7) for the source build so the split plan's fused source-part names
    # (e.g. printed_gas_pcb_keeper_doors, printed_wedge_locks) always resolve.
    source_params = (
        {**params, "production_assembly": {**pa, "export_per_instance_latch_keys": False}}
        if pa.get("export_per_instance_latch_keys", False)
        else params
    )
    models = _row_coupon_export_models(source_params)
    production = params.get("production_assembly", {})
    keyed = bool(production.get("keyed_joints_enabled", False))
    interface = production.get("y_split_interface", {}) or {}
    split_y = float(_production_y_split_segments(params)[0]["y_max"]) if keyed else None
    split_parts: dict[str, cq.Workplane] = {}
    for row in row_coupon_production_y_split_plan(params):
        source_part = str(row["source_part"])
        if source_part not in models:
            raise ValueError(f"unknown production Y split source part: {source_part}")
        if keyed:
            split_parts[str(row["name"])] = _keyed_split_interface(
                models[source_part],
                y_min=float(row["y_min"]),
                y_max=float(row["y_max"]),
                split_y=split_y,
                interface=interface,
            )
        else:
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
            row: dict[str, Any] = {
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
            # D1 flag-on: carry the coherent 2-module joint descriptor onto the plan
            # row when the keyed seam + captured seal are present. Absent flag-off
            # (no "joint" key on the segment), the row is byte-identical to pre-D1.
            if "joint" in segment:
                row["joint"] = segment["joint"]
            rows.append(row)
    return tuple(rows)
