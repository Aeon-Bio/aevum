from __future__ import annotations
from typing import Any
import cadquery as cq
from ..layout import (row_coupon_layout)
from ._geom_base import (_boxes_from_rectangles, _harness_z_shift, _perimeter_rails)


def _add_dry_bay_aperture_thresholds(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    for threshold in layout["wet_dry_failure_paths"]["dry_bay_aperture_thresholds"]:
        model = model.union(
            _perimeter_rails(
                x0=float(threshold["x"]),
                y0=float(threshold["y"]),
                length=float(threshold["length_x"]),
                width=float(threshold["width_y"]),
                rail_width=float(threshold["rail_width"]),
                height=float(threshold["height_z"]),
                z0=float(threshold["z"]),
            )
        )
    return model


def _cut_dry_bay(
    model: cq.Workplane,
    *,
    x0: float,
    y0: float,
    plate_len: float,
    plate_wid: float,
    base_h: float,
    land_h: float,
    bay: dict[str, Any],
) -> cq.Workplane:
    aperture_x = x0 + (plate_len - bay["aperture_length_x"]) / 2
    aperture_y = y0 + (plate_wid - bay["aperture_width_y"]) / 2
    aperture_center_x = aperture_x + bay["aperture_length_x"] / 2
    aperture_center_y = aperture_y + bay["aperture_width_y"] / 2

    model = model.cut(
        cq.Workplane("XY")
        .box(
            bay["aperture_length_x"],
            bay["aperture_width_y"],
            base_h + land_h + 0.4,
            centered=(False, False, False),
        )
        .translate((aperture_x, aperture_y, -0.2))
    )
    model = model.cut(
        cq.Workplane("XY")
        .box(
            bay["aperture_length_x"] + bay["bottom_recess_extra"],
            bay["aperture_width_y"] + bay["bottom_recess_extra"],
            bay["bottom_recess_depth"] + 0.02,
            centered=(True, True, False),
        )
        .translate((aperture_center_x, aperture_center_y, -0.01))
    )
    model = model.cut(
        cq.Workplane("XY")
        .circle(bay["objective_keepout_diameter"] / 2)
        .extrude(bay["bottom_recess_depth"] + 0.02)
        .translate((aperture_center_x, aperture_center_y, -0.01))
    )
    model = model.cut(
        cq.Workplane("XY")
        .box(
            bay["crosshair_length"],
            bay["crosshair_width"],
            bay["bottom_recess_depth"] + 0.02,
            centered=(True, True, False),
        )
        .translate((aperture_center_x, aperture_center_y, -0.01))
    )
    return model.cut(
        cq.Workplane("XY")
        .box(
            bay["crosshair_width"],
            bay["crosshair_length"],
            bay["bottom_recess_depth"] + 0.02,
            centered=(True, True, False),
        )
        .translate((aperture_center_x, aperture_center_y, -0.01))
    )


def _cut_wet_dry_witness_gutters(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    for gutter in layout["wet_dry_failure_paths"]["wet_dry_witness_gutters"]:
        depth = float(gutter["depth_z"])
        model = model.cut(
            cq.Workplane("XY")
            .box(
                float(gutter["length_x"]),
                float(gutter["width_y"]),
                depth + 0.05,
                centered=(False, False, False),
            )
            .translate((float(gutter["x"]), float(gutter["y"]), float(gutter["z"])))
        )
    return model


def _dry_bay_aperture_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, float | int]]:
    plate = params["plate"]
    bay = params["dry_bay"]
    apertures: list[dict[str, float | int]] = []
    for tile in tile_origins:
        aperture_x = tile["x"] + (plate["length_x"] - bay["aperture_length_x"]) / 2
        aperture_y = tile["y"] + (plate["width_y"] - bay["aperture_width_y"]) / 2
        apertures.append(
            {
                "tile_index": tile.get("index", 0),
                "x": round(aperture_x, 3),
                "y": round(aperture_y, 3),
                "length_x": bay["aperture_length_x"],
                "width_y": bay["aperture_width_y"],
                "tile_x": round(tile["x"], 3),
                "tile_y": round(tile["y"], 3),
                "tile_length_x": plate["length_x"],
                "tile_width_y": plate["width_y"],
            }
        )
    return apertures


def _dry_bay_boundary_check(
    dry_bay_envelope: dict[str, Any],
    *,
    params: dict[str, Any],
    row_axis: str,
) -> dict[str, Any]:
    bay = params["dry_bay"]
    rail_w = float(bay["boundary_rail_width_y"])
    rail_h = float(bay["boundary_rail_height_z"])
    rail_clearance = float(bay["boundary_rail_clearance_y"])
    ref_x = float(dry_bay_envelope["x"])
    ref_y = float(dry_bay_envelope["y"])
    ref_len = float(dry_bay_envelope["length_x"])
    ref_wid = float(dry_bay_envelope["width_y"])
    if row_axis == "x":
        body_rects = [
            {
                "name": "dry_bay_front_boundary_clearance_rail",
                "x": round(ref_x, 3),
                "y": round(ref_y - rail_clearance - rail_w, 3),
                "z": round(-rail_h, 3),
                "length_x": round(ref_len, 3),
                "width_y": round(rail_w, 3),
                "height_z": round(rail_h, 3),
            },
            {
                "name": "dry_bay_rear_boundary_clearance_rail",
                "x": round(ref_x, 3),
                "y": round(ref_y + ref_wid + rail_clearance, 3),
                "z": round(-rail_h, 3),
                "length_x": round(ref_len, 3),
                "width_y": round(rail_w, 3),
                "height_z": round(rail_h, 3),
            },
        ]
        boundary_length_x = ref_len
        boundary_width_y = ref_wid + 2 * (rail_clearance + rail_w)
    else:
        body_rects = [
            {
                "name": "dry_bay_left_boundary_clearance_rail",
                "x": round(ref_x - rail_clearance - rail_w, 3),
                "y": round(ref_y, 3),
                "z": round(-rail_h, 3),
                "length_x": round(rail_w, 3),
                "width_y": round(ref_wid, 3),
                "height_z": round(rail_h, 3),
            },
            {
                "name": "dry_bay_right_boundary_clearance_rail",
                "x": round(ref_x + ref_len + rail_clearance, 3),
                "y": round(ref_y, 3),
                "z": round(-rail_h, 3),
                "length_x": round(rail_w, 3),
                "width_y": round(ref_wid, 3),
                "height_z": round(rail_h, 3),
            },
        ]
        boundary_length_x = ref_len + 2 * (rail_clearance + rail_w)
        boundary_width_y = ref_wid
    return {
        "name": "dry_bay_boundary_check",
        "role": "dry_bay_boundary_rail_clearance_validation_body",
        "validation": "required_gate4_dry_bay_boundary_clearance_evidence",
        "failure_rule": (
            "boundary_rail_interference_or_debris_bridge_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{boundary_length_x:.2f} x {boundary_width_y:.2f} x "
            f"{rail_h:.2f} mm, {rail_w:.2f} mm rails"
        ),
        "length_x": round(boundary_length_x, 3),
        "width_y": round(boundary_width_y, 3),
        "height_z": round(rail_h, 3),
        "rail_width": round(rail_w, 3),
        "source_layout_checks": ["dry_bay_envelope"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "dry_bay_boundary_clearance",
            "observer_service_loop_clearance",
            "wet_operation_without_boundary_debris_bridge",
        ],
        "body_rects": body_rects,
    }


def _dry_bay_envelope_check(
    dry_bay_envelope: dict[str, Any],
) -> dict[str, Any]:
    height = float(dry_bay_envelope["top_z"]) - float(dry_bay_envelope["bottom_z"])
    body_rects = [
        {
            "name": "protected_dry_observer_bay_volume",
            "x": dry_bay_envelope["x"],
            "y": dry_bay_envelope["y"],
            "z": dry_bay_envelope["bottom_z"],
            "length_x": dry_bay_envelope["length_x"],
            "width_y": dry_bay_envelope["width_y"],
            "height_z": round(height, 3),
        }
    ]
    return {
        "name": "dry_bay_envelope_check",
        "role": "protected_dry_observer_bay_volume_validation_body",
        "validation": "required_gate4_dry_bay_protected_volume_evidence",
        "failure_rule": (
            "dye_condensate_debris_or_service_lead_inside_dry_bay_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{float(dry_bay_envelope['length_x']):.2f} x "
            f"{float(dry_bay_envelope['width_y']):.2f} x {height:.2f} mm"
        ),
        "length_x": dry_bay_envelope["length_x"],
        "width_y": dry_bay_envelope["width_y"],
        "height_z": round(height, 3),
        "source_layout_checks": ["dry_bay_envelope"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "dry_observer_bay_reserved",
            "wet_operation_without_dry_bay_ingress",
            "dry_observer_clearance_after_wet_exposure",
        ],
        "body_rects": body_rects,
    }


def _dry_bay_ingress_audit_check(
    audit_rects: list[dict[str, Any]],
) -> dict[str, Any]:
    protected_count = sum(
        1 for rect in audit_rects if rect["audit_role"] == "protected_dry_bay_footprint"
    )
    wet_collector_count = sum(
        1 for rect in audit_rects if rect["audit_role"] == "wet_collection"
    )
    inboard_dam_count = sum(1 for rect in audit_rects if rect["audit_role"] == "inboard_dam")
    source_groups = tuple(
        sorted(
            {
                str(rect["source_group"])
                for rect in audit_rects
                if rect["source_group"] != "dry_bay"
            }
        )
    )
    return {
        "name": "dry_bay_ingress_audit_check",
        "role": "dry_bay_external_wet_source_ingress_audit_validation_body",
        "validation": "required_gate4_dry_bay_ingress_audit_evidence",
        "failure_rule": (
            "wet_source_bridge_or_unprotected_dry_bay_path_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{wet_collector_count} wet collectors / {inboard_dam_count} inboard dams / "
            f"{protected_count} protected footprint"
        ),
        "wet_collector_count": wet_collector_count,
        "inboard_dam_count": inboard_dam_count,
        "protected_footprint_count": protected_count,
        "source_groups": source_groups,
        "source_layout_checks": [
            "side_gas_leak_witness_check",
            "sample_relief_leak_witness_check",
            "gasket_tab_leak_witness_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "wet_operation_without_dry_bay_ingress",
            "dry_observer_clearance_after_wet_exposure",
            "sensor_electronics_protected_from_external_wet_sources",
        ],
        "body_rects": audit_rects,
    }


def _dry_bay_ingress_audit_rectangles(
    *,
    dry_bay_envelope: dict[str, Any],
    side_gas_service_interfaces: list[dict[str, Any]],
    sample_relief_leak_witnesses: list[dict[str, Any]],
    gasket_tab_leak_witnesses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    audit_rects: list[dict[str, Any]] = [
        {
            "name": "dry_bay_protected_footprint",
            "x": dry_bay_envelope["x"],
            "y": dry_bay_envelope["y"],
            "z": dry_bay_envelope["bottom_z"],
            "length_x": dry_bay_envelope["length_x"],
            "width_y": dry_bay_envelope["width_y"],
            "height_z": round(
                float(dry_bay_envelope["top_z"]) - float(dry_bay_envelope["bottom_z"]),
                3,
            ),
            "audit_role": "protected_dry_bay_footprint",
            "source_group": "dry_bay",
            "dry_bay_relation": "protected_volume_not_wet_source",
        }
    ]

    def add_rect(
        *,
        rect: dict[str, Any],
        name: str,
        source_group: str,
        audit_role: str,
        dry_bay_relation: str,
        source_role: str,
    ) -> None:
        audit_rects.append(
            {
                "name": name,
                "x": rect["x"],
                "y": rect["y"],
                "z": rect["z"],
                "length_x": rect["length_x"],
                "width_y": rect["width_y"],
                "height_z": rect["height_z"],
                "audit_role": audit_role,
                "source_group": source_group,
                "source_role": source_role,
                "dry_bay_relation": dry_bay_relation,
            }
        )

    for interface in side_gas_service_interfaces:
        role = interface["role"]
        for idx, rect in enumerate(interface["leak_witness_gutter_rects"], start=1):
            add_rect(
                rect=rect,
                name=f"{role}_side_gas_wet_collector_{idx}",
                source_group="side_gas_service",
                audit_role="wet_collection",
                dry_bay_relation="outside_protected_footprint",
                source_role=role,
            )
        for idx, rect in enumerate(interface["leak_witness_threshold_rects"], start=1):
            add_rect(
                rect=rect,
                name=f"{role}_side_gas_inboard_dam_{idx}",
                source_group="side_gas_service",
                audit_role="inboard_dam",
                dry_bay_relation="barrier_at_protected_margin",
                source_role=role,
            )

    for witness in sample_relief_leak_witnesses:
        add_rect(
            rect=witness["shelf_rect"],
            name=f"{witness['name']}_wet_shelf",
            source_group="sample_relief_cap",
            audit_role="wet_collection",
            dry_bay_relation="outside_protected_footprint",
            source_role=witness["port_role"],
        )
        add_rect(
            rect=witness["gutter_rect"],
            name=f"{witness['name']}_wet_gutter",
            source_group="sample_relief_cap",
            audit_role="wet_collection",
            dry_bay_relation="outside_protected_footprint",
            source_role=witness["port_role"],
        )
        add_rect(
            rect=witness["threshold_rect"],
            name=f"{witness['name']}_inboard_dam",
            source_group="sample_relief_cap",
            audit_role="inboard_dam",
            dry_bay_relation="barrier_at_protected_margin",
            source_role=witness["port_role"],
        )

    for witness in gasket_tab_leak_witnesses:
        source_role = f"{witness['layer']}_{witness['side']}"
        add_rect(
            rect=witness["gutter_rect"],
            name=f"{witness['name']}_wet_gutter",
            source_group="gasket_tab_root",
            audit_role="wet_collection",
            dry_bay_relation="outside_protected_footprint",
            source_role=source_role,
        )
        add_rect(
            rect=witness["threshold_rect"],
            name=f"{witness['name']}_inboard_dam",
            source_group="gasket_tab_root",
            audit_role="inboard_dam",
            dry_bay_relation="barrier_at_protected_margin",
            source_role=source_role,
        )

    return audit_rects


def _dry_bay_obstruction_review_rectangles(
    *,
    dry_bay_envelope: dict[str, Any],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    dry_x = float(dry_bay_envelope["x"])
    dry_y = float(dry_bay_envelope["y"])
    dry_z0 = float(dry_bay_envelope["bottom_z"])
    dry_len = float(dry_bay_envelope["length_x"])
    dry_wid = float(dry_bay_envelope["width_y"])
    dry_h = float(dry_bay_envelope["top_z"]) - dry_z0
    margin = float(production.get("dry_bay_obstruction_review_margin_xy", 4.0))
    block_len = min(
        float(production.get("dry_bay_obstruction_review_length_x", 42.0)),
        max(dry_len - 2 * margin, 1.0),
    )
    block_wid = min(
        float(production.get("dry_bay_obstruction_review_width_y", 22.0)),
        max(dry_wid - 2 * margin, 1.0),
    )
    block_h = min(
        float(production.get("dry_bay_obstruction_review_height_z", 8.0)),
        max(dry_h - 1.0, 1.0),
    )
    top_gap = float(production.get("dry_bay_obstruction_review_top_gap_z", 1.0))
    cover_w = min(
        float(production.get("dry_bay_witness_cover_width_y", 4.0)),
        max(dry_wid / 4, 1.0),
    )
    cover_h = min(
        float(production.get("dry_bay_witness_cover_height_z", 2.5)),
        max(dry_h - 1.0, 1.0),
    )
    block_z = max(dry_z0, float(dry_bay_envelope["top_z"]) - top_gap - block_h)
    cover_z = max(dry_z0, float(dry_bay_envelope["top_z"]) - top_gap - cover_h)
    source_checks = [
        "dry_bay_ingress_audit_check",
        "wet_dry_failure_path_check",
        "dry_bay_envelope_check",
    ]
    base = {
        "review_state": "dry_bay_obstructed",
        "owner_part": "dry_bay_obstruction_review",
        "retained_part": "dry_bay_envelope",
        "source_validation_checks": source_checks,
    }
    return [
        {
            **base,
            "name": "dry_bay_foreign_object_obstruction_review",
            "review_kind": "foreign_object_inside_protected_dry_bay",
            "blocked_fail_closed_state": "dry_bay_blocked",
            "dry_bay_relation": "inside_protected_footprint",
            "x": round(dry_x + (dry_len - block_len) / 2, 3),
            "y": round(dry_y + (dry_wid - block_wid) / 2, 3),
            "z": round(block_z, 3),
            "length_x": round(block_len, 3),
            "width_y": round(block_wid, 3),
            "height_z": round(block_h, 3),
        },
        {
            **base,
            "name": "dry_bay_front_witness_path_cover_review",
            "review_kind": "wet_witness_path_visibility_cover",
            "blocked_fail_closed_state": "wet_witness_path_hidden",
            "dry_bay_relation": "front_margin_witness_path_hidden",
            "x": round(dry_x + margin, 3),
            "y": round(dry_y + margin, 3),
            "z": round(cover_z, 3),
            "length_x": round(max(dry_len - 2 * margin, 1.0), 3),
            "width_y": round(cover_w, 3),
            "height_z": round(cover_h, 3),
        },
        {
            **base,
            "name": "dry_bay_rear_witness_path_cover_review",
            "review_kind": "wet_witness_path_visibility_cover",
            "blocked_fail_closed_state": "wet_witness_path_hidden",
            "dry_bay_relation": "rear_margin_witness_path_hidden",
            "x": round(dry_x + margin, 3),
            "y": round(dry_y + dry_wid - margin - cover_w, 3),
            "z": round(cover_z, 3),
            "length_x": round(max(dry_len - 2 * margin, 1.0), 3),
            "width_y": round(cover_w, 3),
            "height_z": round(cover_h, 3),
        },
    ]


def _wet_dry_failure_path_check(
    wet_dry_failure_paths: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    gutters = wet_dry_failure_paths["wet_dry_witness_gutters"]
    thresholds = wet_dry_failure_paths["dry_bay_aperture_thresholds"]
    body_rects = [
        {
            **gutter,
            "height_z": round(float(gutter["depth_z"]), 3),
        }
        for gutter in gutters
    ]
    gutter_depth = float(gutters[0]["depth_z"]) if gutters else 0.0
    return {
        "name": "wet_dry_failure_path_check",
        "role": "aperture_local_wet_dry_witness_gutter_validation_body",
        "validation": "required_gate4_aperture_wet_dry_failure_path_evidence",
        "failure_rule": (
            "aperture_leak_bridge_or_unmeasured_gutter_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{len(gutters)} gutters / {len(thresholds)} raised thresholds / "
            f"{gutter_depth:.2f} mm gutter depth"
        ),
        "gutter_cad_value": f"{len(gutters)} gutters, {gutter_depth:.2f} mm depth",
        "threshold_cad_value": f"{len(thresholds)} raised thresholds",
        "gutter_count": len(gutters),
        "threshold_count": len(thresholds),
        "gutter_depth_z": round(gutter_depth, 3),
        "source_layout_checks": ["wet_dry_failure_paths"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "dry_observer_bay_protected_from_aperture_leaks",
            "wet_operation_without_optics_ingress",
            "powered_sensor_thermal_readiness_after_wet_exposure",
        ],
        "body_rects": body_rects,
        "threshold_rects": thresholds,
    }


def _wet_dry_failure_path_geometry(
    *,
    apertures: list[dict[str, float | int]],
    params: dict[str, Any],
    base_top_z: float,
) -> dict[str, list[dict[str, float | int | str]]]:
    production = params.get("production_assembly", {})
    threshold_w = production.get("dry_bay_threshold_width_xy", 0.0)
    threshold_h = production.get("dry_bay_threshold_height_z", 0.0)
    gutter_w = production.get("wet_dry_witness_gutter_width_xy", 0.0)
    gutter_d = production.get("wet_dry_witness_gutter_depth_z", 0.0)
    gutter_gap = production.get("wet_dry_witness_gutter_gap_xy", 0.0)

    thresholds: list[dict[str, float | int | str]] = []
    gutters: list[dict[str, float | int | str]] = []
    for aperture in apertures:
        aperture_x = float(aperture["x"])
        aperture_y = float(aperture["y"])
        aperture_len = float(aperture["length_x"])
        aperture_wid = float(aperture["width_y"])
        tile_x = float(aperture["tile_x"])
        tile_len = float(aperture["tile_length_x"])
        tile_xmax = tile_x + tile_len

        if threshold_w > 0 and threshold_h > 0:
            thresholds.append(
                {
                    "tile_index": aperture["tile_index"],
                    "x": round(aperture_x - threshold_w, 3),
                    "y": round(aperture_y - threshold_w, 3),
                    "length_x": round(aperture_len + 2 * threshold_w, 3),
                    "width_y": round(aperture_wid + 2 * threshold_w, 3),
                    "rail_width": round(threshold_w, 3),
                    "height_z": round(threshold_h, 3),
                    "z": round(base_top_z, 3),
                    "inner_x": aperture["x"],
                    "inner_y": aperture["y"],
                    "inner_length_x": aperture["length_x"],
                    "inner_width_y": aperture["width_y"],
                }
            )

        if gutter_w > 0 and gutter_d > 0:
            gutter_y = aperture_y - threshold_w
            gutter_width_y = aperture_wid + 2 * threshold_w
            candidates = [
                (
                    "min_x",
                    aperture_x - threshold_w - gutter_gap - gutter_w,
                ),
                (
                    "max_x",
                    aperture_x + aperture_len + threshold_w + gutter_gap,
                ),
            ]
            for side, gutter_x in candidates:
                if gutter_x < tile_x or gutter_x + gutter_w > tile_xmax:
                    continue
                gutters.append(
                    {
                        "tile_index": aperture["tile_index"],
                        "side": side,
                        "x": round(gutter_x, 3),
                        "y": round(gutter_y, 3),
                        "length_x": round(gutter_w, 3),
                        "width_y": round(gutter_width_y, 3),
                        "depth_z": round(gutter_d, 3),
                        "z": round(base_top_z - gutter_d, 3),
                    }
                )
    return {
        "dry_bay_aperture_thresholds": thresholds,
        "wet_dry_witness_gutters": gutters,
    }


def build_dry_bay_boundary_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["dry_bay_boundary_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_dry_bay_envelope_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["dry_bay_envelope_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_dry_bay_ingress_audit_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["base_top_z"]
    return _boxes_from_rectangles(
        layout["dry_bay_ingress_audit_check"]["body_rects"],
        z_shift=z_shift,
    )


def build_dry_bay_obstruction_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["dry_bay_obstruction_review"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_wet_dry_failure_path_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["wet_dry_failure_path_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)
