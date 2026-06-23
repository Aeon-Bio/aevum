from __future__ import annotations
from typing import Any
import cadquery as cq
import math
from ..layout import (row_coupon_layout)
from ._geom_base import (_boxes_from_rectangles, _rectangle_intersects_circle, _rounded_box)
from ._shared_tile import (_lid_port_positions)


def _add_wedge_receiver_rails(
    cover: cq.Workplane,
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    lid = params["lid_manifold"]
    production = params.get("production_assembly", {})
    rail_w = production.get("wedge_receiver_rail_width_x", 1.2)
    rail_h = production.get("wedge_receiver_rail_height_z", 1.1)
    lip_w = production.get("wedge_receiver_lip_width_y", 0.0)
    lip_h = production.get("wedge_receiver_lip_height_z", 0.0)
    lip_len = production.get("wedge_receiver_lip_length_x", 0.0)
    stop_h = production.get("wedge_travel_stop_height_z", rail_h)
    clearance = production.get("wedge_receiver_clearance_x", 0.5)
    length_extra = production.get("wedge_receiver_length_extra_y", 2.0)
    if rail_w <= 0 or rail_h <= 0:
        return cover
    receiver_z = z0 + lid["duct_height_z"]

    for lock in _wedge_lock_rectangles(layout, params):
        if lock["slide_axis"] == "x":
            rail_x = max(0.0, float(lock["x"]) - length_extra / 2)
            rail_len = min(
                layout["length_x"] - rail_x,
                float(lock["length_x"]) + length_extra,
            )
            y_values = [
                max(0.0, float(lock["y"]) - clearance - rail_w),
                min(
                    layout["width_y"] - rail_w,
                    float(lock["y"]) + float(lock["width_y"]) + clearance,
                ),
            ]
            for rail_y in y_values:
                cover = cover.union(
                    cq.Workplane("XY")
                    .box(rail_len, rail_w, rail_h, centered=(False, False, False))
                    .translate((rail_x, rail_y, receiver_z))
                )
            if lip_w > 0 and lip_h > 0 and lip_len > 0:
                lip_x = float(lock["capture_lip_x"])
                lip_len_x = min(lip_len, layout["length_x"] - lip_x)
                lip_y_values = [
                    max(0.0, float(lock["y"]) - clearance),
                    min(
                        layout["width_y"] - lip_w,
                        float(lock["y"]) + float(lock["width_y"]) + clearance - lip_w,
                    ),
                ]
                for lip_y in lip_y_values:
                    cover = cover.union(
                        cq.Workplane("XY")
                        .box(lip_len_x, lip_w, lip_h, centered=(False, False, False))
                        .translate((lip_x, lip_y, receiver_z + rail_h))
                    )
            if stop_h > 0 and float(lock["travel_stop_length_x"]) > 0:
                stop_y = max(0.0, float(lock["y"]) - clearance - rail_w)
                stop_w = min(
                    layout["width_y"] - stop_y,
                    float(lock["width_y"]) + 2 * (clearance + rail_w),
                )
                cover = cover.union(
                    cq.Workplane("XY")
                    .box(
                        float(lock["travel_stop_length_x"]),
                        stop_w,
                        stop_h,
                        centered=(False, False, False),
                    )
                    .translate((float(lock["travel_stop_x"]), stop_y, receiver_z))
                )
        else:
            rail_y = max(0.0, float(lock["y"]) - length_extra / 2)
            rail_len = min(
                layout["width_y"] - rail_y,
                float(lock["width_y"]) + length_extra,
            )
            x_values = [
                max(0.0, float(lock["x"]) - clearance - rail_w),
                min(
                    layout["length_x"] - rail_w,
                    float(lock["x"]) + float(lock["length_x"]) + clearance,
                ),
            ]
            for rail_x in x_values:
                cover = cover.union(
                    cq.Workplane("XY")
                    .box(rail_w, rail_len, rail_h, centered=(False, False, False))
                    .translate((rail_x, rail_y, receiver_z))
                )
            if lip_w > 0 and lip_h > 0 and lip_len > 0:
                lip_y = float(lock["capture_lip_y"])
                lip_len_y = min(lip_len, layout["width_y"] - lip_y)
                lip_x_values = [
                    max(0.0, float(lock["x"]) - clearance),
                    min(
                        layout["length_x"] - lip_w,
                        float(lock["x"]) + float(lock["length_x"]) + clearance - lip_w,
                    ),
                ]
                for lip_x in lip_x_values:
                    cover = cover.union(
                        cq.Workplane("XY")
                        .box(lip_w, lip_len_y, lip_h, centered=(False, False, False))
                        .translate((lip_x, lip_y, receiver_z + rail_h))
                    )
            if stop_h > 0 and float(lock["travel_stop_width_y"]) > 0:
                stop_x = max(0.0, float(lock["x"]) - clearance - rail_w)
                stop_l = min(
                    layout["length_x"] - stop_x,
                    float(lock["length_x"]) + 2 * (clearance + rail_w),
                )
                cover = cover.union(
                    cq.Workplane("XY")
                    .box(
                        stop_l,
                        float(lock["travel_stop_width_y"]),
                        stop_h,
                        centered=(False, False, False),
                    )
                    .translate((stop_x, float(lock["travel_stop_y"]), receiver_z))
                )
    return cover


def _add_wedge_release_detent_and_witness_features(
    lock: cq.Workplane,
    lock_rect: dict[str, float | str],
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    low_h = production.get("wedge_lock_low_height_z", 0.0)
    tab_len = production.get("wedge_release_tab_length_x", 0.0)
    tab_w = production.get("wedge_release_tab_width_y", 0.0)
    tab_h = production.get("wedge_release_tab_height_z", 0.0)
    witness_len = production.get("wedge_witness_mark_length_x", 0.0)
    witness_h = production.get("wedge_witness_mark_height_z", 0.0)
    detent_len = production.get("wedge_detent_bump_length_x", 0.0)
    detent_w = production.get("wedge_detent_bump_width_y", 0.0)
    detent_h = production.get("wedge_detent_bump_height_z", 0.0)
    lip_len = production.get("wedge_receiver_lip_length_x", 0.0)
    if min(tab_len, tab_w, tab_h, detent_len, detent_w, detent_h) <= 0:
        return lock

    lock_x = float(lock_rect["x"])
    lock_y = float(lock_rect["y"])
    lock_l = float(lock_rect["length_x"])
    lock_w = float(lock_rect["width_y"])
    arm_margin = 0.2

    if lock_rect["slide_axis"] == "x":
        if lock_rect["insert_from"] == "min":
            tab_x = lock_x + lip_len + 0.1
            detent_x = lock_x + max((lip_len - detent_len) / 2, 0.0)
        else:
            tab_x = lock_x + lock_l - lip_len - tab_len - 0.1
            detent_x = lock_x + lock_l - lip_len + max((lip_len - detent_len) / 2, 0.0)
        y_values = [
            lock_y + arm_margin,
            lock_y + lock_w - arm_margin - tab_w,
        ]
        for tab_y in y_values:
            lock = lock.union(
                cq.Workplane("XY")
                .box(tab_len, tab_w, tab_h, centered=(False, False, False))
                .translate((tab_x, tab_y, z0 + low_h))
            )
            lock = lock.union(
                cq.Workplane("XY")
                .box(detent_len, detent_w, detent_h, centered=(False, False, False))
                .translate((detent_x, tab_y, z0 + low_h))
            )
            if witness_len > 0 and witness_h > 0:
                witness_x = tab_x + max((tab_len - witness_len) / 2, 0.0)
                lock = lock.union(
                    cq.Workplane("XY")
                    .box(witness_len, tab_w, witness_h, centered=(False, False, False))
                    .translate((witness_x, tab_y, z0 + low_h + tab_h))
                )
        return lock

    if lock_rect["insert_from"] == "min":
        tab_y = lock_y + lip_len + 0.1
        detent_y = lock_y + max((lip_len - detent_len) / 2, 0.0)
    else:
        tab_y = lock_y + lock_w - lip_len - tab_len - 0.1
        detent_y = lock_y + lock_w - lip_len + max((lip_len - detent_len) / 2, 0.0)
    x_values = [
        lock_x + arm_margin,
        lock_x + lock_l - arm_margin - tab_w,
    ]
    for tab_x in x_values:
        lock = lock.union(
            cq.Workplane("XY")
            .box(tab_w, tab_len, tab_h, centered=(False, False, False))
            .translate((tab_x, tab_y, z0 + low_h))
        )
        lock = lock.union(
            cq.Workplane("XY")
            .box(detent_w, detent_len, detent_h, centered=(False, False, False))
            .translate((tab_x, detent_y, z0 + low_h))
        )
        if witness_len > 0 and witness_h > 0:
            witness_y = tab_y + max((tab_len - witness_len) / 2, 0.0)
            lock = lock.union(
                cq.Workplane("XY")
                .box(tab_w, witness_len, witness_h, centered=(False, False, False))
                .translate((tab_x, witness_y, z0 + low_h + tab_h))
            )
    return lock


def _assembly_state_witness_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_port_positions: list[dict[str, Any]],
    wedge_lock_rectangles: list[dict[str, Any]],
    missing_microplate_witnesses: list[dict[str, Any]],
    missing_septum_mat_witnesses: list[dict[str, Any]],
    missing_perimeter_gasket_witnesses: list[dict[str, Any]],
    missing_gas_pcb_cartridge_witnesses: list[dict[str, Any]],
    unseated_gas_pcb_cartridges_review: list[dict[str, Any]],
    missing_local_sensor_witnesses: list[dict[str, Any]],
    missing_service_lead_witnesses: list[dict[str, Any]],
    unseated_side_gas_tubes_review: list[dict[str, Any]],
    lid_top_z: float,
) -> dict[str, Any]:
    production = params.get("production_assembly", {})
    lid = params["lid_manifold"]
    sample_ports = [port for port in lid_port_positions if port["role"] == "sample_relief"]
    cap_ring_w = float(
        production.get("sample_relief_cap_missing_witness_ring_width_xy", 0.8)
    )
    cap_witness_h = float(
        production.get("sample_relief_cap_missing_witness_height_z", 0.6)
    )
    flag_len = float(
        production.get("sample_relief_cap_missing_witness_flag_length_xy", 6.0)
    )
    flag_w = float(
        production.get("sample_relief_cap_missing_witness_flag_width_xy", 1.4)
    )
    latch_witness_h = float(production.get("wedge_unseated_witness_height_z", 0.6))
    latch_z = (
        float(lid_top_z)
        + float(lid["duct_height_z"])
        + float(production.get("wedge_lock_height_z", 0.0))
    )
    latch_unseated_rects = [
        {
            "name": f"latch_unseated_witness_{index:02d}",
            "x": lock["bearing_flat_x"],
            "y": lock["bearing_flat_y"],
            "z": round(latch_z, 3),
            "length_x": lock["bearing_flat_length_x"],
            "width_y": lock["bearing_flat_width_y"],
            "height_z": round(latch_witness_h, 3),
            "review_state": "latches_unseated",
            "removed_part": "printed_wedge_locks",
        }
        for index, lock in enumerate(wedge_lock_rectangles, start=1)
    ]
    sample_relief_cap_witnesses: list[dict[str, Any]] = []
    sample_relief_flag_rects: list[dict[str, Any]] = []
    for port in sample_ports:
        inner_d = float(port["cap_flange_diameter"])
        outer_d = inner_d + 2 * cap_ring_w
        z0 = float(lid_top_z) + float(port["boss_height_z"])
        side = 1 if float(port["x"]) <= float(layout["length_x"]) / 2 else -1
        if side > 0:
            flag_x = float(port["x"]) + outer_d / 2 - 0.1
        else:
            flag_x = float(port["x"]) - outer_d / 2 - flag_len + 0.1
        flag_rect = {
            "name": f"{port['name']}_missing_cap_witness_flag",
            "x": round(flag_x, 3),
            "y": round(float(port["y"]) - flag_w / 2, 3),
            "z": round(z0, 3),
            "length_x": round(flag_len, 3),
            "width_y": round(flag_w, 3),
            "height_z": round(cap_witness_h, 3),
            "review_state": "sample_relief_cap_missing",
            "removed_part": "printed_sample_relief_cap",
        }
        sample_relief_flag_rects.append(flag_rect)
        sample_relief_cap_witnesses.append(
            {
                "name": f"{port['name']}_missing_cap_witness_ring",
                "port_name": port["name"],
                "review_state": "sample_relief_cap_missing",
                "removed_part": "printed_sample_relief_cap",
                "center_x": round(float(port["x"]), 3),
                "center_y": round(float(port["y"]), 3),
                "z": round(z0, 3),
                "inner_diameter": round(inner_d, 3),
                "outer_diameter": round(outer_d, 3),
                "height_z": round(cap_witness_h, 3),
                "flag_rect": flag_rect,
            }
        )

    body_rects = [
        *missing_microplate_witnesses,
        *missing_septum_mat_witnesses,
        *missing_perimeter_gasket_witnesses,
        *missing_gas_pcb_cartridge_witnesses,
        *(rect["pcb_rect"] for rect in unseated_gas_pcb_cartridges_review),
        *missing_local_sensor_witnesses,
        *missing_service_lead_witnesses,
        *(spec["body_rect"] for spec in unseated_side_gas_tubes_review),
        *latch_unseated_rects,
        *sample_relief_flag_rects,
    ]
    source_review_parts = [
        "missing_sample_relief_cap_witness",
        "latch_unseated_witnesses",
        "missing_septum_mat_witnesses",
        "missing_microplate_witnesses",
        "missing_perimeter_gasket_witnesses",
        "missing_gas_pcb_cartridge_witnesses",
        "unseated_gas_pcb_cartridges_review",
        "missing_local_sensor_witnesses",
        "missing_service_lead_witnesses",
        "unseated_side_gas_tubes_review",
    ]
    plate_count = len(missing_microplate_witnesses)
    local_sensor_count = sum(
        1
        for witness in missing_local_sensor_witnesses
        if witness["witness_kind"]
        in {"headspace_sht41_carrier_footprint", "ir_thermopile_body_footprint"}
    )
    return {
        "name": "assembly_state_witness_check",
        "role": "validation-only dry assembly negative-state witness composite",
        "validation": "required_gate2_dry_assembly_state_evidence",
        "failure_rule": (
            "missing_consumable_cap_service_or_latch_state_blocks_dry_assembly_pass"
        ),
        "evidence_gate": "Gate 2 dry assembly",
        "cad_value": (
            f"{plate_count} plates / {len(missing_septum_mat_witnesses)} mats / "
            f"{len(missing_perimeter_gasket_witnesses)} gaskets / "
            f"{len(missing_gas_pcb_cartridge_witnesses)} gas PCB / "
            f"{len(unseated_gas_pcb_cartridges_review)} unseated gas PCB / "
            f"{local_sensor_count} local sensors / "
            f"{len(missing_service_lead_witnesses)} service leads / "
            f"{len(unseated_side_gas_tubes_review)} unseated gas tubes / "
            f"{len(sample_relief_cap_witnesses)} cap / "
            f"{len(latch_unseated_rects)} latches"
        ),
        "stack_cad_value": (
            f"{plate_count} plates / {len(missing_septum_mat_witnesses)} mats / "
            f"{len(missing_perimeter_gasket_witnesses)} perimeter gaskets"
        ),
        "plate_count": plate_count,
        "septum_mat_count": len(missing_septum_mat_witnesses),
        "perimeter_gasket_count": len(missing_perimeter_gasket_witnesses),
        "gas_pcb_cartridge_count": len(missing_gas_pcb_cartridge_witnesses),
        "unseated_gas_pcb_cartridge_review_count": len(
            unseated_gas_pcb_cartridges_review
        ),
        "local_sensor_module_count": local_sensor_count,
        "local_sensor_witness_count": len(missing_local_sensor_witnesses),
        "service_lead_witness_count": len(missing_service_lead_witnesses),
        "unseated_side_gas_tube_review_count": len(unseated_side_gas_tubes_review),
        "sample_relief_cap_witness_count": len(sample_relief_cap_witnesses),
        "latch_unseated_witness_count": len(latch_unseated_rects),
        "source_review_parts": source_review_parts,
        "source_layout_checks": [
            "missing_microplate_witnesses",
            "missing_septum_mat_witnesses",
            "missing_perimeter_gasket_witnesses",
            "missing_gas_pcb_cartridge_witnesses",
            "unseated_gas_pcb_cartridges_review",
            "missing_local_sensor_witnesses",
            "missing_service_lead_witnesses",
            "unseated_side_gas_tubes_review",
            "wedge_lock_rectangles",
            "lid_port_positions",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "installed_dry_stack_complete",
            "sample_relief_cap_installed_and_seated",
            "latches_seated_before_wet_tests",
            "gas_pcb_cartridges_installed_for_dry_fit",
            "gas_pcb_cartridges_seated_to_duct_gaskets",
            "local_headspace_and_ir_sensors_installed",
            "service_leads_connected_for_operating_state",
            "side_gas_tubes_seated_on_barbs",
            "normal_ot2_operation",
        ],
        "body_rects": body_rects,
        "sample_relief_cap_witnesses": sample_relief_cap_witnesses,
        "latch_unseated_rects": latch_unseated_rects,
    }


def _build_wedge_lock_body(
    lock_rect: dict[str, float | str],
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    profile = _wedge_profile_points(lock_rect, params)
    if lock_rect["slide_axis"] == "x":
        lock = (
            cq.Workplane("XZ")
            .polyline(profile)
            .close()
            .extrude(-float(lock_rect["width_y"]))
            .translate((float(lock_rect["x"]), float(lock_rect["y"]), z0))
        )
    else:
        lock = (
            cq.Workplane("YZ")
            .polyline(profile)
            .close()
            .extrude(float(lock_rect["length_x"]))
            .translate((float(lock_rect["x"]), float(lock_rect["y"]), z0))
        )
    lock = _cut_latch_post_slot(lock, lock_rect, params=params, z0=z0)
    return _add_wedge_release_detent_and_witness_features(
        lock,
        lock_rect,
        params=params,
        z0=z0,
    )


def _cut_latch_post_slot(
    lock: cq.Workplane,
    lock_rect: dict[str, float | str],
    *,
    params: dict[str, Any],
    z0: float,
) -> cq.Workplane:
    production = params.get("production_assembly", {})
    post_d = production.get("latch_post_diameter", 0.0)
    if post_d <= 0:
        return lock

    slot_w = post_d + 2 * production.get("wedge_lock_post_slot_clearance_xy", 0.35)
    slot_h = float(lock_rect["height_z"]) + 0.6
    post_x = float(lock_rect["post_x"])
    post_y = float(lock_rect["post_y"])

    if lock_rect["slide_axis"] == "x":
        if lock_rect["insert_from"] == "min":
            slot_x = float(lock_rect["x"]) - 0.1
            slot_len = post_x - float(lock_rect["x"]) + slot_w / 2 + 0.1
        else:
            slot_x = post_x - slot_w / 2
            slot_len = (
                float(lock_rect["x"])
                + float(lock_rect["length_x"])
                - post_x
                + slot_w / 2
                + 0.1
            )
        cutter = (
            cq.Workplane("XY")
            .box(slot_len, slot_w, slot_h, centered=(False, False, False))
            .translate((slot_x, post_y - slot_w / 2, z0 - 0.2))
        )
        return lock.cut(cutter)

    if lock_rect["insert_from"] == "min":
        slot_y = float(lock_rect["y"]) - 0.1
        slot_len = post_y - float(lock_rect["y"]) + slot_w / 2 + 0.1
    else:
        slot_y = post_y - slot_w / 2
        slot_len = (
            float(lock_rect["y"])
            + float(lock_rect["width_y"])
            - post_y
            + slot_w / 2
            + 0.1
        )
    cutter = (
        cq.Workplane("XY")
        .box(slot_w, slot_len, slot_h, centered=(False, False, False))
        .translate((post_x - slot_w / 2, slot_y, z0 - 0.2))
    )
    return lock.cut(cutter)


def _latch_mechanical_screens(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_stop_positions: list[tuple[float, float]],
    wedge_lock_rectangles: list[dict[str, float | str]],
) -> dict[str, dict[str, Any]]:
    production = params.get("production_assembly", {})
    mechanics = params.get("latch_mechanics", {})
    seal = params["seal_interface"]
    row_axis = layout["row_axis"]

    wedge_length = _production_latch_slide_length(params, row_axis=row_axis)
    lead_in = production.get("wedge_lock_lead_in_length_x", 0.0)
    bearing_flat = production.get("wedge_lock_bearing_flat_length_x", 0.0)
    wedge_low = production.get("wedge_lock_low_height_z", 0.0)
    wedge_high = production.get("wedge_lock_height_z", 0.0)
    ramp_rise = max(0.0, wedge_high - wedge_low)
    ramp_run = max(0.0, wedge_length - lead_in - bearing_flat)
    ramp_angle_deg = math.degrees(math.atan2(ramp_rise, ramp_run)) if ramp_run > 0 else 90.0

    tolerance_z = mechanics.get("latch_tolerance_allowance_z", 0.0)
    available_squeeze = max(0.0, ramp_rise - tolerance_z)
    squeeze_min = mechanics.get("gasket_squeeze_min_z", 0.0)
    squeeze_target = mechanics.get("gasket_squeeze_target_z", 0.0)
    squeeze_max = mechanics.get("gasket_squeeze_max_z", seal["compressed_gasket_height_z"])
    hard_stop_limit = min(squeeze_max, seal["compressed_gasket_height_z"])
    bounded_squeeze = min(available_squeeze, squeeze_target, hard_stop_limit)
    compression_budget = {
        "source": "production_assembly",
        "wedge_length_mm": round(wedge_length, 3),
        "ramp_rise_mm": round(ramp_rise, 3),
        "ramp_run_mm": round(ramp_run, 3),
        "tolerance_allowance_z": round(tolerance_z, 3),
        "available_squeeze_z": round(available_squeeze, 3),
        "gasket_squeeze_min_z": round(squeeze_min, 3),
        "gasket_squeeze_target_z": round(squeeze_target, 3),
        "gasket_squeeze_max_z": round(squeeze_max, 3),
        "hard_stop_limit_z": round(hard_stop_limit, 3),
        "bounded_squeeze_z": round(bounded_squeeze, 3),
        "min_squeeze_margin_z": round(bounded_squeeze - squeeze_min, 3),
        "target_squeeze_margin_z": round(available_squeeze - squeeze_target, 3),
        "overcompression_margin_z": round(squeeze_max - bounded_squeeze, 3),
        "passes_budget": (
            available_squeeze >= squeeze_target
            and squeeze_min <= bounded_squeeze <= squeeze_max
            and bounded_squeeze <= hard_stop_limit
        ),
    }

    mu_min = mechanics.get("friction_coefficient_min", 0.0)
    friction_angle_deg = math.degrees(math.atan(mu_min)) if mu_min > 0 else 0.0
    self_lock_margin_deg = friction_angle_deg - ramp_angle_deg
    min_margin_deg = mechanics.get("self_lock_min_margin_deg", 0.0)
    passes_self_lock = self_lock_margin_deg >= 0.0
    meets_margin = self_lock_margin_deg >= min_margin_deg
    ramp_self_lock = {
        "source": "production_assembly",
        "ramp_angle_deg": round(ramp_angle_deg, 3),
        "friction_coefficient_min": round(mu_min, 3),
        "friction_angle_deg": round(friction_angle_deg, 3),
        "self_lock_margin_deg": round(self_lock_margin_deg, 3),
        "self_lock_min_margin_deg": round(min_margin_deg, 3),
        "passes_self_lock": passes_self_lock,
        "meets_min_margin": meets_margin,
        "backdrive_risk_flag": not meets_margin,
        "retention_status": (
            "geometry_margin_ok" if meets_margin else "detent_or_physical_test_required"
        ),
    }

    post_d = production.get("latch_post_diameter", 0.0)
    clamp_force_n = mechanics.get("expected_clamp_force_per_latch_n", 0.0)
    allowable_mpa = mechanics.get("allowable_wet_polymer_stress_mpa", 0.0)
    shaft_area = math.pi * (post_d / 2) ** 2 if post_d > 0 else 0.0
    shaft_stress = clamp_force_n / shaft_area if shaft_area > 0 else float("inf")
    shaft_safety_factor = allowable_mpa / shaft_stress if shaft_stress > 0 else 0.0
    min_sf = mechanics.get("stress_safety_factor_min", 1.0)
    bearing_area = bearing_flat * production.get("wedge_lock_length_y", 0.0)
    root_area = (
        production.get("latch_post_root_gusset_length_x", 0.0)
        * production.get("latch_post_root_gusset_width_y", 0.0)
    )
    min_bearing_area = mechanics.get("min_cap_bearing_area_mm2", 0.0)
    min_root_area = mechanics.get("min_root_pad_area_mm2", 0.0)
    cap_bearing_stress = clamp_force_n / bearing_area if bearing_area > 0 else float("inf")
    root_bearing_stress = clamp_force_n / root_area if root_area > 0 else float("inf")
    post_stress_screen = {
        "source": "production_assembly",
        "expected_clamp_force_per_latch_n": round(clamp_force_n, 3),
        "post_diameter_mm": round(post_d, 3),
        "shaft_area_mm2": round(shaft_area, 3),
        "shaft_stress_mpa": round(shaft_stress, 3),
        "allowable_wet_polymer_stress_mpa": round(allowable_mpa, 3),
        "shaft_safety_factor": round(shaft_safety_factor, 3),
        "stress_safety_factor_min": round(min_sf, 3),
        "cap_bearing_area_mm2": round(bearing_area, 3),
        "cap_bearing_stress_mpa": round(cap_bearing_stress, 3),
        "min_cap_bearing_area_mm2": round(min_bearing_area, 3),
        "root_pad_area_mm2": round(root_area, 3),
        "root_bearing_stress_mpa": round(root_bearing_stress, 3),
        "min_root_pad_area_mm2": round(min_root_area, 3),
        "passes_stress_screen": (
            shaft_safety_factor >= min_sf
            and bearing_area >= min_bearing_area
            and root_area >= min_root_area
        ),
    }

    station_asymmetry = _latch_station_asymmetry_screen(
        layout,
        params=params,
        compression_stop_positions=compression_stop_positions,
        wedge_lock_rectangles=wedge_lock_rectangles,
    )
    return {
        "compression_budget": compression_budget,
        "ramp_self_lock": ramp_self_lock,
        "post_stress_screen": post_stress_screen,
        "station_asymmetry": station_asymmetry,
    }


def _latch_retention_span_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_budget: dict[str, Any],
    ramp_self_lock: dict[str, Any],
    post_stress_screen: dict[str, Any],
    station_asymmetry: dict[str, Any],
    wedge_lock_rectangles: list[dict[str, float | str]],
) -> dict[str, Any]:
    metrology = params.get("consumable_metrology", {})
    check_params = params.get("latch_retention_span_check", {})
    slab_len = float(check_params.get("length_x", 60.0))
    slab_wid = float(check_params.get("width_y", 62.0))
    slab_h = float(check_params.get("height_z", 0.45))
    x0 = (
        float(layout["length_x"])
        + float(metrology.get("viewer_offset_x", 18.0))
        + float(check_params.get("viewer_offset_x", 178.0))
    )
    y0 = (float(layout["width_y"]) - slab_wid) / 2

    checkpoints = [
        {
            "name": "detent_retention_cycle",
            "blocks": ["thin_self_lock_margin_unverified"],
            "source_layout_checks": ["latch_ramp_self_lock"],
            "inspection_method": "five_dry_latch_cycles_plus_tip_upset",
            "evidence_gate": "Gate 2 dry assembly",
        },
        {
            "name": "omitted_station_span_bow",
            "blocks": ["omitted_station_span_bow_unmeasured"],
            "source_layout_checks": ["latch_station_asymmetry"],
            "inspection_method": "straightedge_or_photo_near_omitted_station",
            "evidence_gate": "Gate 2 dry assembly",
        },
        {
            "name": "post_cap_bearing_after_cycle",
            "blocks": ["post_or_cap_bearing_damage_unchecked"],
            "source_layout_checks": ["latch_post_stress_screen"],
            "inspection_method": "post_cap_root_visual_after_dry_cycle",
            "evidence_gate": "Gate 2 dry assembly",
        },
        {
            "name": "gasket_squeeze_after_retention_cycle",
            "blocks": ["gasket_squeeze_after_latch_cycle_unmeasured"],
            "source_layout_checks": ["latch_compression_budget"],
            "source_validation_checks": ["gasket_compression_gap_gauge"],
            "inspection_method": "gap_gauge_or_caliper_after_dry_cycle",
            "evidence_gate": "Gate 2 dry assembly",
        },
    ]
    blockers = sorted(
        {
            block
            for checkpoint in checkpoints
            for block in checkpoint["blocks"]
        }
    )
    source_layout_checks = sorted(
        {
            source
            for checkpoint in checkpoints
            for source in checkpoint["source_layout_checks"]
        }
    )
    source_validation_checks = sorted(
        {
            source
            for checkpoint in checkpoints
            for source in checkpoint.get("source_validation_checks", [])
        }
    )

    requires_physical_evidence = bool(
        ramp_self_lock["backdrive_risk_flag"]
        or station_asymmetry["exceeds_allowed_span"]
        or not post_stress_screen["passes_stress_screen"]
        or not compression_budget["passes_budget"]
    )
    return {
        "name": "latch_retention_span_check",
        "role": "dry_latch_retention_and_omitted_span_evidence_blocker",
        "validation": "cad_proxy_latch_retention_span_physical_evidence_required",
        "failure_rule": (
            "thin_self_lock_or_excess_span_blocks_wet_tests_until_gate2_evidence"
        ),
        "evidence_gate": "Gate 2 dry assembly",
        "cad_value": (
            f"{float(ramp_self_lock['self_lock_margin_deg']):.2f} deg margin / "
            f"{float(station_asymmetry['max_active_station_span_mm']):.2f} mm "
            f"span / {int(station_asymmetry['omitted_station_count'])} omitted"
        ),
        "checkpoint_count": len(checkpoints),
        "checkpoints": checkpoints,
        "blockers": blockers,
        "source_layout_checks": source_layout_checks,
        "source_validation_checks": source_validation_checks,
        "wedge_lock_count": len(wedge_lock_rectangles),
        "self_lock_margin_deg": ramp_self_lock["self_lock_margin_deg"],
        "self_lock_min_margin_deg": ramp_self_lock["self_lock_min_margin_deg"],
        "backdrive_risk_flag": ramp_self_lock["backdrive_risk_flag"],
        "retention_status": ramp_self_lock["retention_status"],
        "omitted_station_count": station_asymmetry["omitted_station_count"],
        "max_active_station_span_mm": station_asymmetry["max_active_station_span_mm"],
        "allowed_max_active_span_mm": station_asymmetry["allowed_max_active_span_mm"],
        "exceeds_allowed_span": station_asymmetry["exceeds_allowed_span"],
        "passes_post_stress_screen": post_stress_screen["passes_stress_screen"],
        "passes_compression_budget": compression_budget["passes_budget"],
        "requires_physical_evidence": requires_physical_evidence,
        "all_checkpoints_block_wet_tests": True,
        "body_rects": [
            {
                "name": "latch_retention_span_evidence_slab",
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": 0.0,
                "length_x": round(slab_len, 3),
                "width_y": round(slab_wid, 3),
                "height_z": round(slab_h, 3),
            }
        ],
    }


def _latch_station_asymmetry_screen(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    compression_stop_positions: list[tuple[float, float]],
    wedge_lock_rectangles: list[dict[str, float | str]],
) -> dict[str, Any]:
    mechanics = params.get("latch_mechanics", {})
    active_positions = {
        (round(float(lock["post_x"]), 3), round(float(lock["post_y"]), 3))
        for lock in wedge_lock_rectangles
    }
    expected_positions = {
        (round(float(x), 3), round(float(y), 3))
        for x, y in compression_stop_positions
    }
    omitted = sorted(expected_positions - active_positions)
    max_span = 0.0
    max_span_side: float | None = None
    if layout["row_axis"] == "y":
        sides = sorted({x for x, _y in expected_positions})
        for side_x in sides:
            ys = sorted(y for x, y in active_positions if x == side_x)
            for y0, y1 in zip(ys, ys[1:], strict=False):
                span = y1 - y0
                if span > max_span:
                    max_span = span
                    max_span_side = side_x
    else:
        sides = sorted({y for _x, y in expected_positions})
        for side_y in sides:
            xs = sorted(x for x, y in active_positions if y == side_y)
            for x0, x1 in zip(xs, xs[1:], strict=False):
                span = x1 - x0
                if span > max_span:
                    max_span = span
                    max_span_side = side_y

    allowed_span = mechanics.get("max_active_latch_span_y", 0.0)
    return {
        "expected_station_count": len(expected_positions),
        "active_station_count": len(active_positions),
        "omitted_station_count": len(omitted),
        "omitted_stop_positions": [
            {"x": x, "y": y, "reason": "port_or_adapter_keepout"} for x, y in omitted
        ],
        "has_omitted_station_warning": bool(omitted),
        "max_active_station_span_mm": round(max_span, 3),
        "max_active_station_span_side": round(max_span_side, 3)
        if max_span_side is not None
        else None,
        "allowed_max_active_span_mm": round(allowed_span, 3),
        "exceeds_allowed_span": bool(allowed_span > 0 and max_span > allowed_span),
    }


def _production_latch_slide_length(params: dict[str, Any], *, row_axis: str) -> float:
    production = params.get("production_assembly", {})
    if row_axis == "y":
        return production.get("wedge_lock_width_x", 0.0)
    return production.get("wedge_lock_length_y", 0.0)


def _wedge_lock_overlaps_lid_port(
    lock: dict[str, float | str],
    port_positions: list[dict[str, Any]],
    params: dict[str, Any],
) -> bool:
    production = params.get("production_assembly", {})
    port_clearance = production.get("wedge_lock_port_clearance_xy", 0.0)
    receiver_clearance = production.get("wedge_receiver_clearance_x", 0.0)
    receiver_w = production.get("wedge_receiver_rail_width_x", 0.0)
    length_extra = production.get("wedge_receiver_length_extra_y", 0.0)
    if lock["slide_axis"] == "x":
        env_x0 = min(float(lock["x"]), float(lock["travel_stop_x"]))
        env_x1 = max(
            float(lock["x"]) + float(lock["length_x"]),
            float(lock["travel_stop_x"]) + float(lock["travel_stop_length_x"]),
        )
        expanded = {
            "x": env_x0 - length_extra / 2 - port_clearance,
            "y": float(lock["y"]) - receiver_clearance - receiver_w - port_clearance,
            "length_x": env_x1 - env_x0 + length_extra + 2 * port_clearance,
            "width_y": float(lock["width_y"])
            + 2 * (receiver_clearance + receiver_w + port_clearance),
        }
    else:
        env_y0 = min(float(lock["y"]), float(lock["travel_stop_y"]))
        env_y1 = max(
            float(lock["y"]) + float(lock["width_y"]),
            float(lock["travel_stop_y"]) + float(lock["travel_stop_width_y"]),
        )
        expanded = {
            "x": float(lock["x"]) - receiver_clearance - receiver_w - port_clearance,
            "y": env_y0 - length_extra / 2 - port_clearance,
            "length_x": float(lock["length_x"])
            + 2 * (receiver_clearance + receiver_w + port_clearance),
            "width_y": env_y1 - env_y0 + length_extra + 2 * port_clearance,
        }
    for port in port_positions:
        if _rectangle_intersects_circle(
            expanded,
            float(port["x"]),
            float(port["y"]),
            float(port["boss_diameter"]) / 2 + port_clearance,
        ):
            return True
    return False


def _wedge_lock_rectangles(
    layout: dict[str, Any],
    params: dict[str, Any],
) -> list[dict[str, float | str]]:
    return _wedge_lock_rectangles_for_layout(layout, params)


def _wedge_lock_rectangles_for_layout(
    layout: dict[str, Any],
    params: dict[str, Any],
) -> list[dict[str, float | str]]:
    production = params.get("production_assembly", {})
    lock_w = production.get("wedge_lock_width_x", 6.0)
    lock_len = production.get("wedge_lock_length_y", 12.0)
    lock_h = production.get("wedge_lock_height_z", 3.0)
    bearing_flat = production.get("wedge_lock_bearing_flat_length_x", 0.0)
    receiver_lip_len = production.get("wedge_receiver_lip_length_x", 0.0)
    release_tab_len = production.get("wedge_release_tab_length_x", 0.0)
    witness_len = production.get("wedge_witness_mark_length_x", 0.0)
    detent_len = production.get("wedge_detent_bump_length_x", 0.0)
    stop_len = production.get("wedge_travel_stop_length_x", 0.0)
    stop_clearance = production.get("wedge_receiver_clearance_x", 0.0)
    port_positions = _lid_port_positions(layout, params)
    rectangles: list[dict[str, float | str]] = []
    for x, y in layout["compression_stop_positions"]:
        if layout["row_axis"] == "y":
            if x <= layout["length_x"] / 2:
                lock_x = 0.0
                insert_from = "min"
                bearing_x = lock_x + lock_w - bearing_flat
                capture_x = lock_x
                release_x = lock_x + receiver_lip_len + 0.1
                detent_x = lock_x + max((receiver_lip_len - detent_len) / 2, 0.0)
                stop_x = min(layout["length_x"] - stop_len, lock_x + lock_w + stop_clearance)
            else:
                lock_x = layout["length_x"] - lock_w
                insert_from = "max"
                bearing_x = lock_x
                capture_x = lock_x + lock_w - receiver_lip_len
                release_x = lock_x + lock_w - receiver_lip_len - release_tab_len - 0.1
                detent_x = lock_x + lock_w - receiver_lip_len + max(
                    (receiver_lip_len - detent_len) / 2,
                    0.0,
                )
                stop_x = max(0.0, lock_x - stop_clearance - stop_len)
            lock_y = min(max(y - lock_len / 2, 0.0), layout["width_y"] - lock_len)
            slide_axis = "x"
            bearing_y = lock_y
            capture_y = lock_y
            release_y = lock_y
            detent_y = lock_y
            witness_x = release_x + max((release_tab_len - witness_len) / 2, 0.0)
            witness_y = lock_y
            stop_y = lock_y
            stop_length_x = stop_len
            stop_width_y = lock_len
        else:
            lock_x = min(max(x - lock_w / 2, 0.0), layout["length_x"] - lock_w)
            if y <= layout["width_y"] / 2:
                lock_y = 0.0
                insert_from = "min"
                bearing_y = lock_y + lock_len - bearing_flat
                capture_y = lock_y
                release_y = lock_y + receiver_lip_len + 0.1
                detent_y = lock_y + max((receiver_lip_len - detent_len) / 2, 0.0)
                stop_y = min(layout["width_y"] - stop_len, lock_y + lock_len + stop_clearance)
            else:
                lock_y = layout["width_y"] - lock_len
                insert_from = "max"
                bearing_y = lock_y
                capture_y = lock_y + lock_len - receiver_lip_len
                release_y = lock_y + lock_len - receiver_lip_len - release_tab_len - 0.1
                detent_y = lock_y + lock_len - receiver_lip_len + max(
                    (receiver_lip_len - detent_len) / 2,
                    0.0,
                )
                stop_y = max(0.0, lock_y - stop_clearance - stop_len)
            slide_axis = "y"
            bearing_x = lock_x
            capture_x = lock_x
            release_x = lock_x
            detent_x = lock_x
            witness_x = lock_x
            witness_y = release_y + max((release_tab_len - witness_len) / 2, 0.0)
            stop_x = lock_x
            stop_length_x = lock_w
            stop_width_y = stop_len
        candidate = {
            "x": round(lock_x, 3),
            "y": round(lock_y, 3),
            "length_x": lock_w,
            "width_y": lock_len,
            "height_z": lock_h,
            "post_x": round(x, 3),
            "post_y": round(y, 3),
            "slide_axis": slide_axis,
            "insert_from": insert_from,
            "bearing_flat_x": round(bearing_x, 3),
            "bearing_flat_y": round(bearing_y, 3),
            "bearing_flat_length_x": round(
                bearing_flat if slide_axis == "x" else lock_w,
                3,
            ),
            "bearing_flat_width_y": round(
                lock_len if slide_axis == "x" else bearing_flat,
                3,
            ),
            "capture_lip_x": round(capture_x, 3),
            "capture_lip_y": round(capture_y, 3),
            "capture_lip_length_x": round(
                receiver_lip_len if slide_axis == "x" else lock_w,
                3,
            ),
            "capture_lip_width_y": round(
                lock_len if slide_axis == "x" else receiver_lip_len,
                3,
            ),
            "release_tab_x": round(release_x, 3),
            "release_tab_y": round(release_y, 3),
            "witness_mark_x": round(witness_x, 3),
            "witness_mark_y": round(witness_y, 3),
            "detent_x": round(detent_x, 3),
            "detent_y": round(detent_y, 3),
            "travel_stop_x": round(stop_x, 3),
            "travel_stop_y": round(stop_y, 3),
            "travel_stop_length_x": round(stop_length_x, 3),
            "travel_stop_width_y": round(stop_width_y, 3),
        }
        if _wedge_lock_overlaps_lid_port(candidate, port_positions, params):
            continue
        rectangles.append(candidate)
    return rectangles


def _wedge_profile_points(
    lock_rect: dict[str, float | str],
    params: dict[str, Any],
) -> list[tuple[float, float]]:
    production = params.get("production_assembly", {})
    length = float(
        lock_rect["length_x"]
        if lock_rect["slide_axis"] == "x"
        else lock_rect["width_y"]
    )
    low_h = production.get("wedge_lock_low_height_z", 0.0)
    high_h = float(lock_rect["height_z"])
    lead_in = min(
        max(production.get("wedge_lock_lead_in_length_x", 0.0), 0.0),
        max(length / 3, 0.0),
    )
    bearing_flat = min(
        max(production.get("wedge_lock_bearing_flat_length_x", 0.0), 0.0),
        max(length - lead_in - 0.4, 0.0),
    )
    if lock_rect["insert_from"] == "min":
        flat_start = length - bearing_flat
        return [
            (0.0, 0.0),
            (length, 0.0),
            (length, high_h),
            (flat_start, high_h),
            (lead_in, low_h),
            (0.0, low_h),
        ]

    flat_end = bearing_flat
    lead_end = length - lead_in
    return [
        (0.0, 0.0),
        (length, 0.0),
        (length, low_h),
        (lead_end, low_h),
        (flat_end, high_h),
        (0.0, high_h),
    ]


def build_assembly_state_witness_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    from aevum_cad.row_coupon import (build_missing_gas_pcb_cartridge_witnesses, build_missing_local_sensor_witnesses, build_missing_microplate_witnesses, build_missing_perimeter_gasket_witnesses, build_missing_sample_relief_cap_witness, build_missing_septum_mat_witnesses, build_missing_service_lead_witnesses, build_unseated_gas_pcb_cartridges_review, build_unseated_side_gas_tubes_review)
    layout = row_coupon_layout(params)
    review_builders = {
        "missing_microplate_witnesses": build_missing_microplate_witnesses,
        "missing_septum_mat_witnesses": build_missing_septum_mat_witnesses,
        "missing_perimeter_gasket_witnesses": build_missing_perimeter_gasket_witnesses,
        "missing_gas_pcb_cartridge_witnesses": build_missing_gas_pcb_cartridge_witnesses,
        "unseated_gas_pcb_cartridges_review": (
            build_unseated_gas_pcb_cartridges_review
        ),
        "missing_local_sensor_witnesses": build_missing_local_sensor_witnesses,
        "missing_service_lead_witnesses": build_missing_service_lead_witnesses,
        "unseated_side_gas_tubes_review": build_unseated_side_gas_tubes_review,
        "missing_sample_relief_cap_witness": build_missing_sample_relief_cap_witness,
        "latch_unseated_witnesses": build_latch_unseated_witnesses,
    }
    witness_bodies = [
        review_builders[review_part](
            params,
            assembly_position=assembly_position,
        )
        for review_part in layout["assembly_state_witness_check"]["source_review_parts"]
    ]

    check = witness_bodies[0]
    for body in witness_bodies[1:]:
        check = check.union(body)
    return check


def build_latch_mechanism_demo_parts(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> dict[str, cq.Workplane]:
    layout = row_coupon_layout(params)
    demo = params.get("latch_mechanism_demo", {})
    length_x = demo.get("base_length_x", 38.0)
    width_y = demo.get("station_width_y", 42.0)
    lower_h = demo.get("lower_frame_height_z", 8.0)
    gasket_h = demo.get("gasket_height_z", 1.2)
    lid_h = demo.get("lid_receiver_height_z", 6.0)
    lid_gap_z = demo.get("lid_receiver_gap_z", 9.0)
    catch_h = demo.get("catch_lip_height_z", 3.0)
    catch_len = demo.get("catch_lip_length_x", 12.0)
    receiver_h = demo.get("receiver_lip_height_z", 3.0)
    receiver_len = demo.get("receiver_lip_length_x", 12.0)
    wedge_len = demo.get("wedge_length_x", 22.0)
    wedge_low = demo.get("wedge_low_height_z", 2.0)
    wedge_high = demo.get("wedge_high_height_z", 5.0)
    wedge_w = demo.get("wedge_width_y", 22.0)
    wedge_clearance = demo.get("wedge_clearance_z", 0.3)
    handle_w = demo.get("handle_width_y", 12.0)
    handle_h = demo.get("handle_height_z", 8.0)
    stop_w = demo.get("hard_stop_width_x", 2.0)
    witness_w = demo.get("witness_mark_width_x", 1.0)

    origin_x = 0.0
    origin_y = 0.0
    origin_z = 0.0
    if assembly_position:
        origin_x = layout["length_x"] + demo.get("viewer_offset_x", 18.0)
        origin_y = max(0.0, layout["width_y"] - demo.get("viewer_offset_y", 128.0))

    lower_frame = (
        _rounded_box(length_x, width_y, lower_h, 1.2)
        .translate((origin_x, origin_y, origin_z))
        .union(
            cq.Workplane("XY")
            .box(catch_len, width_y, catch_h, centered=(False, False, False))
            .translate((origin_x, origin_y, origin_z + lower_h))
        )
        .union(
            cq.Workplane("XY")
            .box(stop_w, width_y, catch_h + gasket_h, centered=(False, False, False))
            .translate((origin_x + length_x - stop_w, origin_y, origin_z + lower_h))
        )
    )

    gasket = (
        cq.Workplane("XY")
        .box(
            length_x - catch_len - stop_w,
            width_y,
            gasket_h,
            centered=(False, False, False),
        )
        .translate((origin_x + catch_len, origin_y, origin_z + lower_h))
    )

    lid_z = origin_z + lower_h + gasket_h + lid_gap_z
    upper_receiver = (
        _rounded_box(length_x, width_y, lid_h, 1.0)
        .translate((origin_x, origin_y, lid_z))
        .union(
            cq.Workplane("XY")
            .box(receiver_len, width_y, receiver_h, centered=(False, False, False))
            .translate((origin_x + length_x - receiver_len, origin_y, lid_z - receiver_h))
        )
    )

    wedge_x = origin_x + catch_len - 1.0
    wedge_y = origin_y + (width_y - wedge_w) / 2
    wedge_z = origin_z + lower_h + gasket_h + wedge_clearance
    sliding_wedge = (
        cq.Workplane("XZ")
        .polyline(
            [
                (0.0, 0.0),
                (wedge_len, 0.0),
                (wedge_len, wedge_high),
                (0.0, wedge_low),
            ]
        )
        .close()
        .extrude(wedge_w)
        .translate((wedge_x, wedge_y, wedge_z))
    )
    handle_x = wedge_x + wedge_len - stop_w
    sliding_wedge = sliding_wedge.union(
        cq.Workplane("XY")
        .box(stop_w, handle_w, handle_h, centered=(False, False, False))
        .translate(
            (
                handle_x,
                origin_y + (width_y - handle_w) / 2,
                wedge_z + wedge_high,
            )
        )
    )
    sliding_wedge = sliding_wedge.union(
        cq.Workplane("XY")
        .box(witness_w, handle_w, 0.6, centered=(False, False, False))
        .translate(
            (
                handle_x - witness_w,
                origin_y + (width_y - handle_w) / 2,
                wedge_z + wedge_high + handle_h,
            )
        )
    )

    return {
        "latch_demo_lower_catch": lower_frame,
        "latch_demo_compressed_gasket": gasket,
        "latch_demo_upper_receiver": upper_receiver,
        "latch_demo_sliding_wedge": sliding_wedge,
    }


def build_latch_retention_span_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["latch_retention_span_check"]
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("latch retention/span check requires rectangles")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_latch_unseated_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    production = params.get("production_assembly", {})
    lid = params["lid_manifold"]
    z0 = (
        layout["lid_top_z"]
        + lid["duct_height_z"]
        + production.get("wedge_lock_height_z", 0.0)
        if assembly_position
        else production.get("wedge_lock_height_z", 0.0)
    )
    height = production.get("wedge_unseated_witness_height_z", 0.6)
    rects = [
        {
            "x": lock["bearing_flat_x"],
            "y": lock["bearing_flat_y"],
            "z": round(z0, 3),
            "length_x": lock["bearing_flat_length_x"],
            "width_y": lock["bearing_flat_width_y"],
            "height_z": round(height, 3),
        }
        for lock in _wedge_lock_rectangles(layout, params)
    ]
    return _boxes_from_rectangles(rects)


def build_printed_wedge_locks(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    lid = params["lid_manifold"]
    z0 = layout["lid_top_z"] + lid["duct_height_z"] if assembly_position else 0.0

    locks: cq.Workplane | None = None
    for lock_rect in _wedge_lock_rectangles(layout, params):
        lock = _build_wedge_lock_body(lock_rect, params=params, z0=z0)
        locks = lock if locks is None else locks.union(lock)
    if locks is None:
        raise ValueError("printed wedge locks require compression stop positions")
    return locks


def _printed_wedge_lock_models(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> dict[str, cq.Workplane]:
    """Per-instance wedge-lock bodies (single solid each, no cross-instance union)."""

    layout = row_coupon_layout(params)
    lid = params["lid_manifold"]
    z0 = layout["lid_top_z"] + lid["duct_height_z"] if assembly_position else 0.0

    models: dict[str, cq.Workplane] = {}
    for i, lock_rect in enumerate(_wedge_lock_rectangles(layout, params)):
        models[f"printed_wedge_lock_{i}"] = _build_wedge_lock_body(
            lock_rect, params=params, z0=z0
        )
    return models


def build_unseated_wedge_locks_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    lid = params["lid_manifold"]
    production = params.get("production_assembly", {})
    z0 = layout["lid_top_z"] + lid["duct_height_z"] if assembly_position else 0.0
    offset = production.get("wedge_unseated_review_offset_x", 6.0)

    locks: cq.Workplane | None = None
    for lock_rect in _wedge_lock_rectangles(layout, params):
        dx = dy = 0.0
        direction = -1.0 if lock_rect["insert_from"] == "min" else 1.0
        if lock_rect["slide_axis"] == "x":
            dx = direction * offset
        else:
            dy = direction * offset
        lock = _build_wedge_lock_body(lock_rect, params=params, z0=z0).translate((dx, dy, 0))
        locks = lock if locks is None else locks.union(lock)
    if locks is None:
        raise ValueError("unseated wedge lock review requires compression stop positions")
    return locks
