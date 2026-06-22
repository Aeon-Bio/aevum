from __future__ import annotations
from typing import Any
import cadquery as cq
import math
from ..layout import (row_coupon_layout)
from ._geom_base import (_bodies_from_shape_targets, _boxes_from_rectangles, _harness_z_shift)
from ._shared_tile import (_well_centers_for_tile)


def _add_headspace_sht41_sockets(
    shell: cq.Workplane,
    *,
    params: dict[str, Any],
    assembly_position: bool,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_bottom_z"]

    for mount in layout["headspace_sht41_mounts"]:
        shell = shell.union(
            _boxes_from_rectangles(
                [mount["protected_cassette_outer_rect"]],
                z_shift=z_shift,
            )
        )
        pocket = mount["protected_pocket_cut_rect"]
        shell = shell.cut(
            cq.Workplane("XY")
            .box(
                float(pocket["length_x"]) + 0.2,
                float(pocket["width_y"]),
                float(pocket["height_z"]),
                centered=(False, False, False),
            )
            .translate(
                (
                    float(pocket["x"]),
                    float(pocket["y"]),
                    float(pocket["z"]) + z_shift,
                )
            )
        )
        shell = shell.union(
            _boxes_from_rectangles(
                [mount["registration_key_rect"]],
                z_shift=z_shift,
            )
        )
        ring = mount["drip_break_ring"]
        ring_body = (
            cq.Workplane("XY")
            .circle(float(ring["outer_diameter"]) / 2)
            .extrude(float(ring["height_z"]))
            .translate((float(ring["x"]), float(ring["y"]), float(ring["z"]) + z_shift))
        )
        ring_cut = (
            cq.Workplane("XY")
            .circle(float(ring["inner_diameter"]) / 2)
            .extrude(float(ring["height_z"]) + 0.2)
            .translate((float(ring["x"]), float(ring["y"]), float(ring["z"]) + z_shift - 0.1))
        )
        shell = shell.union(ring_body.cut(ring_cut))
        shell = shell.cut(
            cq.Workplane("XY")
            .circle(float(mount["aperture_diameter"]) / 2)
            .extrude(
                float(mount["drip_break_ring"]["height_z"])
                + float(mount["protected_cassette_outer_rect"]["height_z"])
                + 0.4
            )
            .translate(
                (
                    float(mount["aperture_x"]),
                    float(mount["aperture_y"]),
                    float(mount["drip_break_ring"]["z"]) + z_shift - 0.2,
                )
            )
        )
        cable = mount["cable_exit_rect"]
        shell = shell.cut(
            cq.Workplane("XY")
            .box(
                float(cable["length_x"]),
                float(cable["width_y"]),
                float(mount["height_z"]) + 0.2,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(cable["x"]),
                    float(cable["y"]),
                    float(cable["z"]) + z_shift - 0.1,
                )
            )
        )
    return shell


def _add_ir_aperture_drip_collars(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    for mount in layout["ir_sensor_mounts"]:
        collar = mount["drip_collar"]
        body = (
            cq.Workplane("XY")
            .circle(float(collar["outer_diameter"]) / 2)
            .extrude(float(collar["height_z"]))
            .translate((float(collar["x"]), float(collar["y"]), float(collar["z"])))
        )
        aperture = (
            cq.Workplane("XY")
            .circle(float(collar["inner_diameter"]) / 2)
            .extrude(float(collar["height_z"]) + 0.2)
            .translate((float(collar["x"]), float(collar["y"]), float(collar["z"]) - 0.1))
        )
        model = model.union(body.cut(aperture))
    return model


def _add_ir_sensor_retention_lips(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    mounts = params.get("sensor_mounts", {})
    lip_w = mounts.get("ir_retention_lip_width_xy", 1.0)
    lip_h = mounts.get("ir_retention_lip_height_z", 0.7)
    for mount in layout["ir_sensor_mounts"]:
        body_d = float(mount["length_x"])
        x0 = float(mount["center_x"]) - body_d / 2 - lip_w
        y_values = [
            float(mount["center_y"]) - body_d / 2 - lip_w,
            float(mount["center_y"]) + body_d / 2,
        ]
        for y0 in y_values:
            model = model.union(
                cq.Workplane("XY")
                .box(body_d + 2 * lip_w, lip_w, lip_h, centered=(False, False, False))
                .translate((x0, y0, 0.0))
            )
    return model


def _cut_ir_sensor_pockets_and_apertures(
    model: cq.Workplane,
    *,
    params: dict[str, Any],
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    mounts = params.get("sensor_mounts", {})
    clearance_d = mounts.get("ir_pocket_clearance_diameter", 0.4)
    base = params["base"]
    support = params["plate_support"]
    for mount in layout["ir_sensor_mounts"]:
        center_x = float(mount["center_x"])
        center_y = float(mount["center_y"])
        pocket_d = float(mount["length_x"]) + clearance_d
        model = model.cut(
            cq.Workplane("XY")
            .circle(pocket_d / 2)
            .extrude(float(mount["height_z"]) + 0.1)
            .translate((center_x, center_y, -0.05))
        )
        model = model.cut(
            cq.Workplane("XY")
            .circle(float(mount["aperture_diameter"]) / 2)
            .extrude(base["thickness_z"] + support["land_height_z"] + 0.4)
            .translate((center_x, center_y, -0.2))
        )
    return model


def _headspace_barrier_check(
    wet_chamber_skirt: dict[str, Any],
    *,
    seal: dict[str, Any],
    plate_top_z: float,
) -> dict[str, Any]:
    x0 = float(wet_chamber_skirt["x"])
    y0 = float(wet_chamber_skirt["y"])
    length = float(wet_chamber_skirt["length_x"])
    width = float(wet_chamber_skirt["width_y"])
    rail_w = float(seal["chamber_wall_thickness"])
    height = float(seal["compressed_gasket_height_z"]) + float(
        seal["headspace_recess_depth_z"]
    )
    body_rects = [
        {
            "name": "headspace_barrier_front_rail",
            "x": round(x0, 3),
            "y": round(y0, 3),
            "z": round(plate_top_z, 3),
            "length_x": round(length, 3),
            "width_y": round(rail_w, 3),
            "height_z": round(height, 3),
        },
        {
            "name": "headspace_barrier_rear_rail",
            "x": round(x0, 3),
            "y": round(y0 + width - rail_w, 3),
            "z": round(plate_top_z, 3),
            "length_x": round(length, 3),
            "width_y": round(rail_w, 3),
            "height_z": round(height, 3),
        },
        {
            "name": "headspace_barrier_left_rail",
            "x": round(x0, 3),
            "y": round(y0 + rail_w, 3),
            "z": round(plate_top_z, 3),
            "length_x": round(rail_w, 3),
            "width_y": round(width - 2 * rail_w, 3),
            "height_z": round(height, 3),
        },
        {
            "name": "headspace_barrier_right_rail",
            "x": round(x0 + length - rail_w, 3),
            "y": round(y0 + rail_w, 3),
            "z": round(plate_top_z, 3),
            "length_x": round(rail_w, 3),
            "width_y": round(width - 2 * rail_w, 3),
            "height_z": round(height, 3),
        },
    ]
    return {
        "name": "headspace_barrier_check",
        "role": "shared_wet_headspace_barrier_perimeter_validation_body",
        "validation": "required_gate4_headspace_barrier_evidence",
        "failure_rule": "sealed_perimeter_leak_or_bypass_blocks_wet_dry_pass",
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{length:.2f} x {width:.2f} x {height:.2f} mm perimeter, "
            f"{rail_w:.2f} mm wall"
        ),
        "length_x": round(length, 3),
        "width_y": round(width, 3),
        "height_z": round(height, 3),
        "wall_width": round(rail_w, 3),
        "source_layout_checks": ["wet_chamber_skirt"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "sealed_wet_headspace_perimeter",
            "wet_operation_without_headspace_bypass",
            "wet_operation_without_external_leak",
        ],
        "body_rects": body_rects,
    }


def _headspace_sht41_mounts_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_bottom_z: float,
) -> list[dict[str, Any]]:
    mounts = params.get("sensor_mounts", {})
    if not mounts:
        return []

    plate = params["plate"]
    carrier_len = mounts.get("sht41_carrier_length_x", 12.0)
    carrier_wid = mounts.get("sht41_carrier_width_y", 12.0)
    carrier_h = mounts.get("sht41_carrier_height_z", 4.0)
    inset_x = mounts.get("sht41_service_lane_inset_x", 9.0)
    z0 = lid_bottom_z + mounts.get("sht41_lid_recess_z", 0.4)
    aperture_d = mounts.get("sht41_headspace_aperture_diameter", 3.0)
    wall = mounts.get("sht41_socket_wall_thickness", 1.0)
    clearance_xy = mounts.get("sht41_carrier_clearance_xy", 0.25)
    clearance_z = mounts.get("sht41_carrier_clearance_z", 0.2)
    pocket_roof_h = mounts.get("sht41_pocket_roof_thickness_z", 0.8)
    key_len = mounts.get("sht41_registration_key_length_x", 2.0)
    key_w = mounts.get("sht41_registration_key_width_y", 0.8)
    key_h = mounts.get("sht41_registration_key_height_z", 0.5)
    relief_len = mounts.get("sht41_service_finger_relief_length_x", 5.0)
    relief_w = mounts.get("sht41_service_finger_relief_width_y", 4.0)
    drip_outer_d = mounts.get("sht41_drip_break_outer_diameter", aperture_d + 2.0)
    drip_h = mounts.get("sht41_drip_break_height_z", 0.35)
    channel_w = mounts.get("cable_channel_width_xy", 1.2)
    channel_d = mounts.get("cable_channel_depth_z", 0.5)
    x0 = float(layout["length_x"]) - inset_x - carrier_len / 2

    specs: list[dict[str, Any]] = []
    for tile in layout["tile_origins"]:
        center_y = tile["y"] + plate["width_y"] / 2
        y0 = center_y - carrier_wid / 2
        pocket_x = x0 - clearance_xy
        pocket_y = y0 - clearance_xy
        pocket_z = z0 - clearance_z / 2
        pocket_len = float(layout["length_x"]) - pocket_x + 0.2
        pocket_w = carrier_wid + 2 * clearance_xy
        pocket_h = carrier_h + clearance_z
        outer_x = x0 - wall - clearance_xy
        outer_y = y0 - wall - clearance_xy
        outer_w = carrier_wid + 2 * (wall + clearance_xy)
        outer_h = (z0 - lid_bottom_z) + pocket_h + pocket_roof_h
        service_edge_x = float(layout["length_x"])
        key = {
            "x": round(x0 + min(1.2, carrier_len / 4), 3),
            "y": round(y0 + carrier_wid - key_w, 3),
            "z": round(z0, 3),
            "length_x": round(key_len, 3),
            "width_y": round(key_w, 3),
            "height_z": round(key_h, 3),
        }
        specs.append(
            {
                "name": f"headspace_sht41_tile_{tile['index']}",
                "role": "plate_headspace_rh_t",
                "tile_index": tile["index"],
                "owner_part": "lid_manifold_shell",
                "retention": "screwless_printed_microcarrier_keeper",
                "orientation": "side_loaded_service_cassette",
                "service_direction": "-X_install_+X_remove",
                "socket_enclosure": "protected_side_loaded_lid_shell_tunnel",
                "wet_boundary": "controlled_membrane_aperture_only",
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": round(z0, 3),
                "length_x": round(carrier_len, 3),
                "width_y": round(carrier_wid, 3),
                "height_z": round(carrier_h, 3),
                "aperture_x": round(x0 + carrier_len / 2, 3),
                "aperture_y": round(center_y, 3),
                "aperture_z": round(z0, 3),
                "aperture_diameter": aperture_d,
                "condensate_protection": "drip_break_ring_and_service_side_harness_isolation",
                "protected_cassette_outer_rect": {
                    "x": round(outer_x, 3),
                    "y": round(outer_y, 3),
                    "z": round(lid_bottom_z, 3),
                    "length_x": round(service_edge_x - outer_x, 3),
                    "width_y": round(outer_w, 3),
                    "height_z": round(outer_h, 3),
                },
                "protected_pocket_cut_rect": {
                    "x": round(pocket_x, 3),
                    "y": round(pocket_y, 3),
                    "z": round(pocket_z, 3),
                    "length_x": round(pocket_len, 3),
                    "width_y": round(pocket_w, 3),
                    "height_z": round(pocket_h, 3),
                },
                "socket_floor_thickness_z": round(z0 - lid_bottom_z - clearance_z / 2, 3),
                "anti_lift_keeper_rect": {
                    "x": round(pocket_x, 3),
                    "y": round(pocket_y, 3),
                    "z": round(pocket_z + pocket_h, 3),
                    "length_x": round(pocket_len, 3),
                    "width_y": round(pocket_w, 3),
                    "height_z": round(pocket_roof_h, 3),
                },
                "back_stop_rect": {
                    "x": round(outer_x, 3),
                    "y": round(pocket_y, 3),
                    "z": round(pocket_z, 3),
                    "length_x": round(wall, 3),
                    "width_y": round(pocket_w, 3),
                    "height_z": round(pocket_h, 3),
                },
                "side_stop_rects": [
                    {
                        "x": round(pocket_x, 3),
                        "y": round(outer_y, 3),
                        "z": round(pocket_z, 3),
                        "length_x": round(pocket_len, 3),
                        "width_y": round(wall, 3),
                        "height_z": round(pocket_h, 3),
                    },
                    {
                        "x": round(pocket_x, 3),
                        "y": round(pocket_y + pocket_w, 3),
                        "z": round(pocket_z, 3),
                        "length_x": round(pocket_len, 3),
                        "width_y": round(wall, 3),
                        "height_z": round(pocket_h, 3),
                    },
                ],
                "registration_key_rect": key,
                "registration_notch_rect": key,
                "service_finger_relief_rect": {
                    "x": round(max(service_edge_x - relief_len, pocket_x), 3),
                    "y": round(center_y - relief_w / 2, 3),
                    "z": round(pocket_z, 3),
                    "length_x": round(min(relief_len, service_edge_x - pocket_x), 3),
                    "width_y": round(relief_w, 3),
                    "height_z": round(pocket_h, 3),
                },
                "drip_break_ring": {
                    "x": round(x0 + carrier_len / 2, 3),
                    "y": round(center_y, 3),
                    "z": round(lid_bottom_z - drip_h, 3),
                    "inner_diameter": round(aperture_d, 3),
                    "outer_diameter": round(drip_outer_d, 3),
                    "height_z": round(drip_h, 3),
                },
                "cable_exit_rect": {
                    "x": round(x0 + carrier_len, 3),
                    "y": round(center_y - channel_w / 2, 3),
                    "z": round(z0, 3),
                    "length_x": round(float(layout["length_x"]) - (x0 + carrier_len), 3),
                    "width_y": round(channel_w, 3),
                    "depth_z": round(channel_d, 3),
                },
            }
        )
    return specs


def _headspace_volume_check(
    wet_chamber_skirt: dict[str, Any],
    *,
    seal: dict[str, Any],
    plate_top_z: float,
) -> dict[str, Any]:
    rail_w = float(seal["gasket_rail_width"])
    height = float(seal["compressed_gasket_height_z"]) + float(
        seal["headspace_recess_depth_z"]
    )
    length = float(wet_chamber_skirt["length_x"]) - 2 * rail_w
    width = float(wet_chamber_skirt["width_y"]) - 2 * rail_w
    body_rects = [
        {
            "name": "shared_wet_headspace_volume",
            "x": round(float(wet_chamber_skirt["x"]) + rail_w, 3),
            "y": round(float(wet_chamber_skirt["y"]) + rail_w, 3),
            "z": round(plate_top_z, 3),
            "length_x": round(length, 3),
            "width_y": round(width, 3),
            "height_z": round(height, 3),
        }
    ]
    return {
        "name": "headspace_volume_check",
        "role": "shared_wet_headspace_volume_validation_body",
        "validation": "required_gate4_shared_headspace_volume_evidence",
        "failure_rule": (
            "blocked_bridged_or_discontinuous_shared_headspace_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": f"{length:.2f} x {width:.2f} x {height:.2f} mm shared volume",
        "length_x": round(length, 3),
        "width_y": round(width, 3),
        "height_z": round(height, 3),
        "source_layout_checks": ["wet_chamber_skirt"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "shared_wet_headspace_continuity",
            "wet_operation_with_all_plates_in_one_headspace",
            "sealed_row_volume_without_blocked_bridges",
        ],
        "body_rects": body_rects,
    }


def _ir_sensor_mounts_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    base_top_z: float,
) -> list[dict[str, Any]]:
    from aevum_cad.row_coupon import (_well_grid_rectangle_for_tile)
    mounts = params.get("sensor_mounts", {})
    if not mounts:
        return []

    plate = params["plate"]
    body_d = mounts.get("ir_body_diameter", 8.0)
    body_h = mounts.get("ir_body_height_z", 4.5)
    lens_h = mounts.get("ir_lens_height_z", 0.35)
    aperture_d = mounts.get("ir_aperture_diameter", 6.0)
    center_inset_x = mounts.get("ir_center_inset_x", 4.4)
    face_gasket_od = mounts.get("ir_face_gasket_outer_diameter", body_d)
    face_gasket_id = mounts.get("ir_face_gasket_inner_diameter", aperture_d + 0.4)
    face_gasket_h = mounts.get("ir_face_gasket_thickness_z", 0.45)
    face_gasket_compression_z = mounts.get("ir_face_gasket_nominal_compression_z", 0.12)
    drip_collar_od = mounts.get("ir_aperture_drip_collar_outer_diameter", aperture_d + 3.0)
    drip_collar_h = mounts.get("ir_aperture_drip_collar_height_z", 0.55)
    harness = params.get("sensor_harness", {})
    fov_angle_deg = harness.get("ir_fov_angle_degrees", 12.0)
    plate_bottom_z = base_top_z + params["plate_support"]["land_height_z"]
    sensor_to_plate_z = max(plate_bottom_z - (body_h + lens_h), 0.0)
    fov_spot_d = 2 * sensor_to_plate_z * math.tan(math.radians(fov_angle_deg) / 2)
    channel_w = mounts.get("cable_channel_width_xy", 1.2)
    channel_d = mounts.get("cable_channel_depth_z", 0.5)

    specs: list[dict[str, Any]] = []
    for tile in layout["tile_origins"]:
        center_x = tile["x"] + center_inset_x
        center_y = tile["y"] + plate["width_y"] / 2
        well_grid = _well_grid_rectangle_for_tile(tile, params)
        specs.append(
            {
                "name": f"ir_thermopile_tile_{tile['index']}",
                "role": "plate_margin_sample_plane_temperature",
                "tile_index": tile["index"],
                "owner_part": "plate_support_frame",
                "retention": "screwless_printed_lip",
                "wet_boundary": "drip_collared_aperture_with_dry_side_face_gasket",
                "condensate_protection": "top_drip_collar_and_compressed_face_gasket",
                "x": round(center_x - body_d / 2, 3),
                "y": round(center_y - body_d / 2, 3),
                "z": 0.0,
                "length_x": round(body_d, 3),
                "width_y": round(body_d, 3),
                "height_z": round(body_h, 3),
                "center_x": round(center_x, 3),
                "center_y": round(center_y, 3),
                "aperture_x": round(center_x, 3),
                "aperture_y": round(center_y, 3),
                "aperture_z": round(base_top_z, 3),
                "aperture_diameter": aperture_d,
                "fov_angle_degrees": round(fov_angle_deg, 3),
                "sensor_to_plate_z": round(sensor_to_plate_z, 3),
                "fov_spot_diameter": round(fov_spot_d, 3),
                "well_grid_rect": well_grid,
                "face_gasket": {
                    "x": round(center_x, 3),
                    "y": round(center_y, 3),
                    "z": round(max(body_h - face_gasket_h, 0.0), 3),
                    "outer_diameter": round(face_gasket_od, 3),
                    "inner_diameter": round(face_gasket_id, 3),
                    "height_z": round(face_gasket_h, 3),
                    "nominal_compression_z": round(face_gasket_compression_z, 3),
                    "retention": "captured_between_to39_face_and_printed_pocket_lip",
                    "wet_boundary": "dry_side_aperture_face_seal",
                },
                "drip_collar": {
                    "x": round(center_x, 3),
                    "y": round(center_y, 3),
                    "z": round(base_top_z, 3),
                    "inner_diameter": round(aperture_d, 3),
                    "outer_diameter": round(drip_collar_od, 3),
                    "height_z": round(drip_collar_h, 3),
                    "owner_part": "plate_support_frame",
                    "leak_management": "raised_collar_keeps_wetting_out_of_ir_aperture",
                },
                "cable_exit_rect": {
                    "x": 0.0,
                    "y": round(center_y - channel_w / 2, 3),
                    "z": 0.0,
                    "length_x": round(max(center_x - body_d / 2, 0.0), 3),
                    "width_y": round(channel_w, 3),
                    "depth_z": round(channel_d, 3),
                },
            }
        )
    return specs


def _ir_thermopile_fov_spot_check(
    ir_sensor_mounts: list[dict[str, Any]],
    *,
    params: dict[str, Any],
    plate_bottom_z: float,
) -> dict[str, Any]:
    harness = params.get("sensor_harness", {})
    thickness = float(harness.get("ir_fov_spot_check_thickness_z", 0.2))
    z = float(plate_bottom_z) - thickness / 2
    body_targets = [
        {
            "name": f"{mount['name']}_fov_spot",
            "shape": "disk",
            "tile_index": mount["tile_index"],
            "x": mount["center_x"],
            "y": mount["center_y"],
            "z": round(z, 3),
            "diameter": mount["fov_spot_diameter"],
            "height_z": round(thickness, 3),
            "fov_angle_degrees": mount["fov_angle_degrees"],
        }
        for mount in ir_sensor_mounts
    ]
    spot_diameter = float(ir_sensor_mounts[0]["fov_spot_diameter"]) if ir_sensor_mounts else 0.0
    fov_angle = float(ir_sensor_mounts[0]["fov_angle_degrees"]) if ir_sensor_mounts else 0.0
    return {
        "name": "ir_thermopile_fov_spot_check",
        "role": "ir_thermopile_plate_margin_proxy_fov_validation_body",
        "validation": "required_gate6_ir_proxy_fov_spot_evidence",
        "failure_rule": (
            "unverified_ir_plate_margin_proxy_blocks_cell_temperature_claims"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{len(body_targets)} spots / {spot_diameter:.2f} mm at plate margin / "
            f"{fov_angle:.2f} deg FOV"
        ),
        "spot_cad_value": (
            f"{spot_diameter:.2f} mm at plate margin, {fov_angle:.2f} deg FOV"
        ),
        "spot_count": len(body_targets),
        "spot_diameter": round(spot_diameter, 3),
        "fov_angle_degrees": round(fov_angle, 3),
        "source_layout_checks": ["ir_sensor_mounts"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "ir_cell_temperature_claims",
            "edge_to_center_temperature_correlation",
            "biology_temperature_readiness",
        ],
        "body_targets": body_targets,
    }


def _target_kind_counts(
    targets: list[dict[str, Any]],
    key: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for target in targets:
        kind = str(target[key])
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def _thermal_condensation_proxy_check(
    thermal_condensation_proxy_targets: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = _target_kind_counts(thermal_condensation_proxy_targets, "kind")
    return {
        "name": "thermal_condensation_proxy_check",
        "role": "gate6_thermal_condensation_proxy_plan_validation_body",
        "validation": "required_gate6_thermal_condensation_proxy_evidence",
        "failure_rule": (
            "unverified_thermal_proxy_or_condensation_path_blocks_sensor_thermal_pass"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{counts.get('cell_plane_center_reference', 0)} center refs / "
            f"{counts.get('ir_plate_margin_proxy_spot', 0)} IR proxies / "
            f"{counts.get('sht41_headspace_aperture_drip_ring', 0)} SHT41 points / "
            f"{counts.get('condensation_pocket_low_point', 0)} condensation pockets"
        ),
        "target_count": len(thermal_condensation_proxy_targets),
        "proxy_kind_counts": counts,
        "source_layout_checks": ["thermal_condensation_proxy_targets"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "center_to_edge_thermal_correlation",
            "condensation_free_sensor_operation",
            "cell_temperature_claims",
            "powered_sensor_thermal_readiness",
        ],
        "body_targets": thermal_condensation_proxy_targets,
    }


def _well_cell_plane_check(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
    plate_top_z: float,
) -> dict[str, Any]:
    plate = params["plate"]
    grid = params["well_grid"]
    diameter = float(plate["well_bottom_area_equivalent_diameter"])
    thickness = float(plate.get("cell_plane_check_thickness_z", 0.2))
    z = float(plate_top_z) - float(plate["plate_top_to_cell_plane_depth_z"]) - thickness / 2
    body_targets: list[dict[str, Any]] = []
    for tile in tile_origins:
        for index, (x, y) in enumerate(_well_centers_for_tile(tile, params), start=1):
            body_targets.append(
                {
                    "name": f"well_cell_plane_tile_{tile['index']}_well_{index:02d}",
                    "shape": "disk",
                    "tile_index": tile["index"],
                    "well_index": index,
                    "x": round(x, 3),
                    "y": round(y, 3),
                    "z": round(z, 3),
                    "diameter": round(diameter, 3),
                    "height_z": round(thickness, 3),
                }
            )
    target_count = len(tile_origins) * int(grid["columns"]) * int(grid["rows"])
    return {
        "name": "well_cell_plane_check",
        "role": "published_cellvis_cell_plane_target_validation_body",
        "validation": "required_gate6_well_cell_plane_reference_evidence",
        "failure_rule": (
            "unverified_cell_plane_reference_blocks_thermal_or_biology_claims"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{target_count} wells / {diameter:.2f} mm / z={z:.2f} mm"
        ),
        "well_count": target_count,
        "diameter_cad_value": f"{diameter:.2f} mm",
        "z_cad_value": f"{z:.2f} mm",
        "source_layout_checks": ["tile_origins", "plate_top_z"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "cell_plane_reference_for_thermal_correlation",
            "biology_readiness",
            "cell_temperature_claims",
        ],
        "body_targets": body_targets,
    }


def build_headspace_barrier_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["headspace_barrier_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_headspace_sht41_microcarriers(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    carriers: cq.Workplane | None = None
    for mount in layout["headspace_sht41_mounts"]:
        z = float(mount["z"]) if assembly_position else 0.0
        carrier = (
            cq.Workplane("XY")
            .box(
                float(mount["length_x"]),
                float(mount["width_y"]),
                float(mount["height_z"]),
                centered=(False, False, False),
            )
            .translate((float(mount["x"]), float(mount["y"]), z))
        )
        aperture = (
            cq.Workplane("XY")
            .circle(float(mount["aperture_diameter"]) / 2)
            .extrude(float(mount["height_z"]) + 0.1)
            .translate((float(mount["aperture_x"]), float(mount["aperture_y"]), z - 0.05))
        )
        carrier = carrier.cut(aperture)
        notch = mount["registration_notch_rect"]
        carrier = carrier.cut(
            cq.Workplane("XY")
            .box(
                float(notch["length_x"]) + 0.05,
                float(notch["width_y"]) + 0.05,
                float(notch["height_z"]) + 0.05,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(notch["x"]) - 0.025,
                    float(notch["y"]) - 0.025,
                    float(notch["z"]) + (0.0 if assembly_position else -float(mount["z"])) - 0.025,
                )
            )
        )
        carriers = carrier if carriers is None else carriers.union(carrier)
    if carriers is None:
        raise ValueError("headspace SHT41 carrier model requires at least one mount")
    return carriers


def build_headspace_volume_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["headspace_volume_check"]["body_rects"]
    z_shift = _harness_z_shift(rects, assembly_position=assembly_position)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_ir_thermopile_fov_spot_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    targets = layout["ir_thermopile_fov_spot_check"]["body_targets"]
    z_shift = _harness_z_shift(targets, assembly_position=assembly_position)
    return _bodies_from_shape_targets(targets, z_shift=z_shift)


def build_ir_thermopiles(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    mounts = params.get("sensor_mounts", {})
    lens_h = mounts.get("ir_lens_height_z", 0.35)
    sensors: cq.Workplane | None = None
    for mount in layout["ir_sensor_mounts"]:
        z = float(mount["z"]) if assembly_position else 0.0
        sensor = (
            cq.Workplane("XY")
            .circle(float(mount["length_x"]) / 2)
            .extrude(float(mount["height_z"]))
            .translate((float(mount["center_x"]), float(mount["center_y"]), z))
        )
        lens = (
            cq.Workplane("XY")
            .circle(float(mount["aperture_diameter"]) / 2)
            .extrude(lens_h)
            .translate(
                (
                    float(mount["center_x"]),
                    float(mount["center_y"]),
                    z + float(mount["height_z"]),
                )
            )
        )
        sensor = sensor.union(lens)
        sensors = sensor if sensors is None else sensors.union(sensor)
    if sensors is None:
        raise ValueError("IR thermopile model requires at least one mount")
    return sensors


def build_thermal_condensation_proxy_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    targets = layout["thermal_condensation_proxy_check"]["body_targets"]
    if not targets:
        raise ValueError("thermal/condensation proxy check requires at least one target")
    z_shift = 0.0 if assembly_position else -min(float(target["z"]) for target in targets)
    return _bodies_from_shape_targets(targets, z_shift=z_shift)


def build_well_cell_plane_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    targets = layout["well_cell_plane_check"]["body_targets"]
    z_shift = _harness_z_shift(targets, assembly_position=assembly_position)
    return _bodies_from_shape_targets(targets, z_shift=z_shift)
