from __future__ import annotations
from typing import Any
import cadquery as cq
from ..layout import (row_coupon_layout)
from ._geom_base import (_axis_cylinder, _axis_cylinder_envelope_rect, _axis_tube, _boxes_from_rectangles, _perimeter_rails, _rectangles_overlap_xy)


def _add_gas_sensor_pcb_sockets(
    cover: cq.Workplane,
    *,
    params: dict[str, Any],
    assembly_position: bool,
) -> cq.Workplane:
    from aevum_cad.row_coupon import (_cut_rectangular_gas_interface_window)
    layout = row_coupon_layout(params)
    mounts = params.get("sensor_mounts", {})
    wall = mounts.get("gas_pcb_socket_wall_thickness", 1.2)
    lip_h = mounts.get("gas_pcb_socket_lip_height_z", 1.2)
    lip_w = mounts.get("gas_pcb_socket_lip_width_xy", 1.5)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]

    for mount in layout["gas_sensor_pcb_mounts"]:
        x = float(mount["x"])
        y = float(mount["y"])
        z = float(mount["z"]) + z_shift
        length_x = float(mount["length_x"])
        width_y = float(mount["width_y"])
        height_z = float(mount["height_z"])
        shelf_z = z
        cover = cover.union(
            cq.Workplane("XY")
            .box(length_x + 2 * wall, width_y + 2 * wall, lip_h, centered=(False, False, False))
            .translate((x - wall, y - wall, shelf_z))
        )
        cover = cover.union(
            _perimeter_rails(
                x0=x - wall,
                y0=y - wall,
                length=length_x + 2 * wall,
                width=width_y + 2 * wall,
                rail_width=wall,
                height=height_z,
                z0=z,
            )
        )
        interface = mount["gas_interface"]
        cover = cover.union(
            _boxes_from_rectangles([interface["seal_land_rect"]], z_shift=z_shift)
        )
        cover = cover.union(
            _boxes_from_rectangles(interface["compression_pad_rects"], z_shift=z_shift)
        )
        if length_x <= width_y:
            rail_len_x = length_x + 2 * wall
            cover = cover.union(
                cq.Workplane("XY")
                .box(rail_len_x, lip_w, lip_h, centered=(False, False, False))
                .translate((x - wall, y + width_y - lip_w / 2, z + height_z - lip_h))
            )
        else:
            rail_len_y = width_y + 2 * wall
            cover = cover.union(
                cq.Workplane("XY")
                .box(lip_w, rail_len_y, lip_h, centered=(False, False, False))
                .translate((x + length_x - lip_w / 2, y - wall, z + height_z - lip_h))
            )
        cover = _cut_rectangular_gas_interface_window(
            cover,
            interface["flow_cell_rect"],
            z_shift=z_shift,
        )
        cover = _cut_vertical_mount_aperture(cover, mount, z=z)
        cable = mount["cable_exit_rect"]
        cover = cover.cut(
            cq.Workplane("XY")
            .box(
                float(cable["length_x"]),
                float(cable["width_y"]),
                float(cable["depth_z"]) + 0.1,
                centered=(False, False, False),
            )
            .translate(
                (
                    float(cable["x"]),
                    float(cable["y"]),
                    float(cable["z"]) + z_shift - 0.05,
                )
            )
        )
    return cover


def _add_side_gas_service_features(
    cover: cq.Workplane,
    *,
    params: dict[str, Any],
    assembly_position: bool,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    for interface in layout["side_gas_service_interfaces"]:
        block = dict(interface["block_rect"])
        block["z"] = float(block["z"]) + z_shift
        cover = cover.union(_boxes_from_rectangles([block]))

        for feature_name in ("printed_fitting", "printed_barb_retention_bead"):
            feature = interface[feature_name]
            cover = cover.union(
                _axis_cylinder(
                    axis=feature["axis"],
                    x=float(feature["x"]),
                    y=float(feature["y"]),
                    z=float(feature["z"]) + z_shift,
                    length=float(feature["length"]),
                    diameter=float(feature["diameter"]),
                )
            )

        relief = dict(interface["strain_relief_rect"])
        relief["z"] = float(relief["z"]) + z_shift
        cover = cover.union(_boxes_from_rectangles([relief]))

        threshold_rects = []
        for rect in interface["leak_witness_threshold_rects"]:
            threshold = dict(rect)
            threshold["z"] = float(threshold["z"]) + z_shift
            threshold_rects.append(threshold)
        cover = cover.union(_boxes_from_rectangles(threshold_rects))

        for rect in interface["leak_witness_gutter_rects"]:
            gutter = dict(rect)
            gutter["z"] = float(gutter["z"]) + z_shift
            cover = cover.cut(_boxes_from_rectangles([gutter]))

        opening = interface["duct_opening"]
        cover = cover.cut(
            _axis_cylinder(
                axis=opening["axis"],
                x=float(opening["x"]),
                y=float(opening["y"]),
                z=float(opening["z"]) + z_shift,
                length=float(opening["length"]),
                diameter=float(opening["diameter"]),
            )
        )
    return cover


def _cots_gas_service_tubes(
    interfaces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [interface["installed_tube"] for interface in interfaces]


def _cut_vertical_mount_aperture(
    model: cq.Workplane,
    mount: dict[str, Any],
    *,
    z: float,
) -> cq.Workplane:
    aperture_z = float(mount["aperture_z"]) - float(mount["z"]) + z
    radius = float(mount["aperture_diameter"]) / 2
    length_x = float(mount["length_x"])
    width_y = float(mount["width_y"])
    if length_x <= width_y:
        cutter = (
            cq.Workplane("YZ")
            .circle(radius)
            .extrude(length_x + 0.2)
            .translate((float(mount["x"]) - 0.1, float(mount["aperture_y"]), aperture_z))
        )
        return model.cut(cutter)
    cutter = (
        cq.Workplane("XZ")
        .circle(radius)
        .extrude(width_y + 0.2)
        .translate((float(mount["aperture_x"]), float(mount["y"]) - 0.1, aperture_z))
    )
    return model.cut(cutter)


def _gas_pcb_flow_cell_check_for_layout(
    gas_sensor_pcb_mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    interfaces = [mount["gas_interface"] for mount in gas_sensor_pcb_mounts]
    flow_cell_rects = [interface["flow_cell_rect"] for interface in interfaces]
    aperture_diameters = {
        round(float(mount["aperture_diameter"]), 3) for mount in gas_sensor_pcb_mounts
    }
    dead_volumes = {
        round(float(interface["dead_volume_mm3"]), 3) for interface in interfaces
    }
    gasket_thicknesses = {
        round(float(interface["nominal_gasket_thickness_x"]), 3)
        for interface in interfaces
    }
    gasket_compressions = {
        round(float(interface["nominal_compression_x"]), 3)
        for interface in interfaces
    }
    aperture_d = next(iter(aperture_diameters)) if len(aperture_diameters) == 1 else 0.0
    dead_volume = next(iter(dead_volumes)) if len(dead_volumes) == 1 else 0.0

    return {
        "name": "gas_pcb_flow_cell_check",
        "role": "gas_pcb_duct_sampling_cell_validation_body",
        "validation": "required_gate6_aperture_registered_flow_cell_evidence",
        "failure_rule": (
            "missing_flow_cell_or_gasket_registration_evidence_blocks_sensor_thermal_pass"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": f"{aperture_d:.2f} mm aperture / {dead_volume:.2f} mm3 cell",
        "cartridge_count": len(gas_sensor_pcb_mounts),
        "flow_cell_count": len(flow_cell_rects),
        "aperture_count": len(gas_sensor_pcb_mounts),
        "aperture_diameter": aperture_d,
        "dead_volume_mm3": dead_volume,
        "nominal_gasket_thickness_x": (
            next(iter(gasket_thicknesses)) if len(gasket_thicknesses) == 1 else 0.0
        ),
        "nominal_compression_x": (
            next(iter(gasket_compressions)) if len(gasket_compressions) == 1 else 0.0
        ),
        "source_layout_checks": ["gas_sensor_pcb_mounts"],
        "requires_physical_evidence": True,
        "flow_cell_rects": flow_cell_rects,
    }


def _gas_pcb_sampling_interface(
    mount: dict[str, Any],
    *,
    params: dict[str, Any],
) -> dict[str, Any]:
    mounts = params.get("sensor_mounts", {})
    flow_depth = mounts.get("gas_pcb_flow_cell_depth_x", 0.8)
    flow_len = mounts.get("gas_pcb_flow_cell_length_y", 8.0)
    flow_h = mounts.get("gas_pcb_flow_cell_height_z", 5.0)
    margin_y = mounts.get("gas_pcb_seal_land_margin_y", 2.0)
    margin_z = mounts.get("gas_pcb_seal_land_margin_z", 1.5)
    land_t = mounts.get("gas_pcb_seal_land_thickness_x", 0.8)
    gasket_t = mounts.get("gas_pcb_interface_gasket_thickness_x", 0.6)
    compression_x = mounts.get("gas_pcb_interface_gasket_compression_x", 0.2)
    pad_len_y = mounts.get("gas_pcb_compression_pad_length_y", 3.5)
    pad_h = mounts.get("gas_pcb_compression_pad_height_z", 1.0)
    seal_len = flow_len + 2 * margin_y
    seal_h = flow_h + 2 * margin_z
    aperture_y = float(mount["aperture_y"])
    aperture_z = float(mount["aperture_z"])
    length_x = float(mount["length_x"])
    width_y = float(mount["width_y"])

    if length_x <= width_y:
        face_x = float(mount["x"]) + length_x
        gasket_rect = {
            "x": round(face_x, 3),
            "y": round(aperture_y - seal_len / 2, 3),
            "z": round(aperture_z - seal_h / 2, 3),
            "length_x": round(gasket_t, 3),
            "width_y": round(seal_len, 3),
            "height_z": round(seal_h, 3),
        }
        seal_land_rect = {
            "x": round(face_x + gasket_t - compression_x, 3),
            "y": round(aperture_y - seal_len / 2, 3),
            "z": round(aperture_z - seal_h / 2, 3),
            "length_x": round(land_t, 3),
            "width_y": round(seal_len, 3),
            "height_z": round(seal_h, 3),
        }
        flow_cell_rect = {
            "x": round(face_x + gasket_t - compression_x, 3),
            "y": round(aperture_y - flow_len / 2, 3),
            "z": round(aperture_z - flow_h / 2, 3),
            "length_x": round(flow_depth + land_t, 3),
            "width_y": round(flow_len, 3),
            "height_z": round(flow_h, 3),
        }
        compression_pads = [
            {
                "x": seal_land_rect["x"],
                "y": round(aperture_y - seal_len / 2, 3),
                "z": round(aperture_z - seal_h / 2, 3),
                "length_x": round(land_t, 3),
                "width_y": round(pad_len_y, 3),
                "height_z": round(pad_h, 3),
            },
            {
                "x": seal_land_rect["x"],
                "y": round(aperture_y + seal_len / 2 - pad_len_y, 3),
                "z": round(aperture_z + seal_h / 2 - pad_h, 3),
                "length_x": round(land_t, 3),
                "width_y": round(pad_len_y, 3),
                "height_z": round(pad_h, 3),
            },
        ]
        face_axis = "+X"
    else:
        face_y = float(mount["y"]) + width_y
        gasket_rect = {
            "x": round(float(mount["aperture_x"]) - seal_len / 2, 3),
            "y": round(face_y, 3),
            "z": round(aperture_z - seal_h / 2, 3),
            "length_x": round(seal_len, 3),
            "width_y": round(gasket_t, 3),
            "height_z": round(seal_h, 3),
        }
        seal_land_rect = {
            "x": round(float(mount["aperture_x"]) - seal_len / 2, 3),
            "y": round(face_y + gasket_t - compression_x, 3),
            "z": round(aperture_z - seal_h / 2, 3),
            "length_x": round(seal_len, 3),
            "width_y": round(land_t, 3),
            "height_z": round(seal_h, 3),
        }
        flow_cell_rect = {
            "x": round(float(mount["aperture_x"]) - flow_len / 2, 3),
            "y": round(face_y + gasket_t - compression_x, 3),
            "z": round(aperture_z - flow_h / 2, 3),
            "length_x": round(flow_len, 3),
            "width_y": round(flow_depth + land_t, 3),
            "height_z": round(flow_h, 3),
        }
        compression_pads = [
            {
                "x": round(float(mount["aperture_x"]) - seal_len / 2, 3),
                "y": seal_land_rect["y"],
                "z": round(aperture_z - seal_h / 2, 3),
                "length_x": round(pad_len_y, 3),
                "width_y": round(land_t, 3),
                "height_z": round(pad_h, 3),
            },
            {
                "x": round(float(mount["aperture_x"]) + seal_len / 2 - pad_len_y, 3),
                "y": seal_land_rect["y"],
                "z": round(aperture_z + seal_h / 2 - pad_h, 3),
                "length_x": round(pad_len_y, 3),
                "width_y": round(land_t, 3),
                "height_z": round(pad_h, 3),
            },
        ]
        face_axis = "+Y"

    if face_axis == "+X":
        gasket_window_rect = {
            "x": gasket_rect["x"],
            "y": flow_cell_rect["y"],
            "z": flow_cell_rect["z"],
            "length_x": gasket_rect["length_x"],
            "width_y": flow_cell_rect["width_y"],
            "height_z": flow_cell_rect["height_z"],
        }
    else:
        gasket_window_rect = {
            "x": flow_cell_rect["x"],
            "y": gasket_rect["y"],
            "z": flow_cell_rect["z"],
            "length_x": flow_cell_rect["length_x"],
            "width_y": gasket_rect["width_y"],
            "height_z": flow_cell_rect["height_z"],
        }

    return {
        "type": "sealed_dry_side_duct_sampling_cell",
        "face_axis": face_axis,
        "gasket_material_intent": "compressible_elastomer_or_printed_tpu",
        "gasket_rect": gasket_rect,
        "gasket_window_rect": gasket_window_rect,
        "seal_land_rect": seal_land_rect,
        "flow_cell_rect": flow_cell_rect,
        "compression_pad_rects": compression_pads,
        "nominal_gasket_thickness_x": round(gasket_t, 3),
        "nominal_compression_x": round(compression_x, 3),
        "dead_volume_mm3": round(flow_depth * flow_len * flow_h, 3),
        "validation": "aperture_registered_low_dead_volume_no_open_top_sampling",
    }


def _gas_sensor_pcb_mounts_for_layout(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_top_z: float,
) -> list[dict[str, Any]]:
    mounts = params.get("sensor_mounts", {})
    if not mounts:
        return []

    row = params["row"]
    lid = params["lid_manifold"]
    gas_len = mounts.get("gas_pcb_envelope_length", 30.0)
    gas_width = mounts.get("gas_pcb_envelope_width", 25.0)
    gas_thick = mounts.get("gas_pcb_envelope_thickness", 5.0)
    aperture_d = mounts.get("gas_pcb_aperture_diameter", 2.0)
    channel_w = mounts.get("cable_channel_width_xy", 1.2)
    channel_d = mounts.get("cable_channel_depth_z", 0.5)
    z0 = lid_top_z
    aperture_z = lid_top_z + lid["duct_height_z"] / 2
    side_gas_by_role = {
        interface["role"]: interface
        for interface in layout.get("side_gas_service_interfaces", [])
    }
    specs: list[dict[str, Any]] = []

    if layout["row_axis"] == "y":
        role_specs = [
            ("supply", row["end_margin_x"]),
            ("return", layout["length_x"] - row["end_margin_x"]),
        ]
        for role, duct_center_x in role_specs:
            gas_interface = side_gas_by_role[role]
            center_y = float(gas_interface["duct_y"])
            center_y = min(
                max(center_y, gas_len / 2),
                float(layout["width_y"]) - gas_len / 2,
            )
            x0 = duct_center_x - gas_thick / 2
            y0 = center_y - gas_len / 2
            cable_x = 0.0 if role == "supply" else x0 + gas_thick
            cable_len = x0 if role == "supply" else float(layout["length_x"]) - cable_x
            spec = {
                "name": f"{role}_gas_sensor_pcb",
                "role": role,
                "owner_part": "lid_cover",
                "retention": "screwless_printed_keeper",
                "orientation": "vertical_side_cartridge",
                "socket_enclosure": "full_height_printed_dry_side_cassette",
                "wet_boundary": "dry_side_gas_duct_aperture_only",
                "headspace_intrusion": False,
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": round(z0, 3),
                "length_x": round(gas_thick, 3),
                "width_y": round(gas_len, 3),
                "height_z": round(gas_width, 3),
                "aperture_x": round(duct_center_x, 3),
                "aperture_y": round(center_y, 3),
                "aperture_z": round(aperture_z, 3),
                "aperture_diameter": aperture_d,
                "cable_exit_rect": {
                    "x": round(cable_x, 3),
                    "y": round(center_y - channel_w / 2, 3),
                    "z": round(lid_top_z, 3),
                    "length_x": round(cable_len, 3),
                    "width_y": round(channel_w, 3),
                    "depth_z": round(channel_d, 3),
                },
            }
            spec["gas_interface"] = _gas_pcb_sampling_interface(spec, params=params)
            specs.append(spec)
        return specs

    role_specs = [
        ("supply", row["side_margin_y"]),
        ("return", layout["width_y"] - row["side_margin_y"]),
    ]
    for role, duct_center_y in role_specs:
        gas_interface = side_gas_by_role[role]
        center_x = float(gas_interface["duct_x"])
        center_x = min(
            max(center_x, gas_len / 2),
            float(layout["length_x"]) - gas_len / 2,
        )
        x0 = center_x - gas_len / 2
        y0 = duct_center_y - gas_thick / 2
        cable_y = 0.0 if role == "supply" else y0 + gas_thick
        cable_wid = y0 if role == "supply" else float(layout["width_y"]) - cable_y
        spec = {
            "name": f"{role}_gas_sensor_pcb",
            "role": role,
            "owner_part": "lid_cover",
            "retention": "screwless_printed_keeper",
            "orientation": "vertical_side_cartridge",
            "socket_enclosure": "full_height_printed_dry_side_cassette",
            "wet_boundary": "dry_side_gas_duct_aperture_only",
            "headspace_intrusion": False,
            "x": round(x0, 3),
            "y": round(y0, 3),
            "z": round(z0, 3),
            "length_x": round(gas_len, 3),
            "width_y": round(gas_thick, 3),
            "height_z": round(gas_width, 3),
            "aperture_x": round(center_x, 3),
            "aperture_y": round(duct_center_y, 3),
            "aperture_z": round(aperture_z, 3),
            "aperture_diameter": aperture_d,
            "cable_exit_rect": {
                "x": round(center_x - channel_w / 2, 3),
                "y": round(cable_y, 3),
                "z": round(lid_top_z, 3),
                "length_x": round(channel_w, 3),
                "width_y": round(cable_wid, 3),
                "depth_z": round(channel_d, 3),
            },
        }
        spec["gas_interface"] = _gas_pcb_sampling_interface(spec, params=params)
        specs.append(spec)
    return specs


def _sensor_chip_marker_for_mount(
    mount: dict[str, Any],
    *,
    z: float,
) -> cq.Workplane:
    aperture_z = float(mount["aperture_z"]) - float(mount["z"]) + z
    length_x = float(mount["length_x"])
    width_y = float(mount["width_y"])
    chip_w = 3.2
    chip_h = 3.2
    chip_t = 0.45
    if length_x <= width_y:
        return (
            cq.Workplane("XY")
            .box(chip_t, chip_w, chip_h, centered=(False, False, False))
            .translate(
                (
                    float(mount["x"]) + length_x + 0.02,
                    float(mount["aperture_y"]) - chip_w / 2,
                    aperture_z - chip_h / 2,
                )
            )
        )
    return (
        cq.Workplane("XY")
        .box(chip_w, chip_t, chip_h, centered=(False, False, False))
        .translate(
            (
                float(mount["aperture_x"]) - chip_w / 2,
                float(mount["y"]) + width_y + 0.02,
                aperture_z - chip_h / 2,
            )
        )
    )


def _side_gas_adjacent_slot_clearance(
    interfaces: list[dict[str, Any]],
    adjacent_keepouts: list[dict[str, Any]],
    *,
    params: dict[str, Any],
) -> dict[str, Any]:
    required = params["deck_interface"].get("side_service_vertical_clearance_z", 0.0)
    overlaps: list[dict[str, Any]] = []
    min_clearance: float | None = None
    for interface in interfaces:
        for rect in interface["external_service_rects"]:
            for keepout in adjacent_keepouts:
                if not _rectangles_overlap_xy(rect, keepout):
                    continue
                clearance = float(rect["z"]) - (
                    float(keepout["z"]) + float(keepout["height_z"])
                )
                min_clearance = (
                    clearance
                    if min_clearance is None
                    else min(min_clearance, clearance)
                )
                overlaps.append(
                    {
                        "service": interface["role"],
                        "service_rect": rect["name"],
                        "adjacent_keepout": keepout["name"],
                        "vertical_clearance_z": round(clearance, 3),
                    }
                )
    min_value = float("inf") if min_clearance is None else min_clearance
    return {
        "required_vertical_clearance_z": round(required, 3),
        "min_vertical_clearance_z": round(min_value, 3) if overlaps else None,
        "xy_overlap_count": len(overlaps),
        "meets_vertical_clearance": bool(not overlaps or min_value >= required),
        "clearance_evidence": overlaps,
        "interpretation": "side_services_use_reserved_adjacent_slot_overhead",
    }


def _side_gas_leak_witness_check(
    interfaces: list[dict[str, Any]],
) -> dict[str, Any]:
    wet_collectors = [
        rect
        for interface in interfaces
        for rect in interface["leak_witness_gutter_rects"]
    ]
    inboard_dams = [
        rect
        for interface in interfaces
        for rect in interface["leak_witness_threshold_rects"]
    ]
    body_rects = [*wet_collectors, *inboard_dams]
    return {
        "name": "side_gas_leak_witness_check",
        "role": "side_gas_wet_failure_witness_validation_body",
        "validation": "required_gate4_side_gas_wet_witness_evidence",
        "failure_rule": (
            "side_gas_leak_without_visible_collector_or_inboard_dam_blocks_wet_dry_pass"
        ),
        "evidence_gate": "Gate 4 wet/dry witness",
        "cad_value": (
            f"{len(wet_collectors)} wet collectors / {len(inboard_dams)} inboard dams"
        ),
        "wet_collector_count": len(wet_collectors),
        "inboard_dam_count": len(inboard_dams),
        "service_count": len(interfaces),
        "source_layout_checks": ["side_gas_service_interfaces"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "wet_operation_with_connected_side_gas",
            "dry_bay_protection_from_side_gas_leak",
        ],
        "body_rects": body_rects,
    }


def _side_gas_service_interfaces(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    lid_top_z: float,
) -> list[dict[str, Any]]:
    gas = params.get("gas_service", {})
    row = params["row"]
    lid = params["lid_manifold"]
    duct_w = lid["duct_width_y"]
    duct_h = lid["duct_height_z"]
    block_w = gas.get("manifold_block_width_y", 18.0)
    block_h = gas.get("manifold_block_height_z", 5.0)
    stem_len = gas.get("fitting_stem_length_x", 7.0)
    fitting_d = gas.get("fitting_outer_diameter", 4.8)
    opening_d = gas.get("duct_opening_diameter", 2.4)
    flange_d = gas.get("barb_flange_diameter", 4.8)
    flange_w = gas.get("barb_flange_width_x", 1.2)
    relief_len = gas.get("strain_relief_slot_length_x", 6.0)
    relief_w = gas.get("strain_relief_slot_width_y", 7.0)
    relief_h = gas.get("strain_relief_height_z", 2.0)
    tube_d = gas.get("tube_envelope_diameter", 6.0)
    tube_id = gas.get("tube_inner_diameter", max(0.1, fitting_d - 0.1))
    tube_od = gas.get("tube_outer_diameter", min(tube_d, fitting_d))
    bend_r = gas.get("tube_bend_radius", 18.0)
    straight_len = gas.get("tube_straight_service_length", 18.0)
    center_offset = gas.get("service_center_offset_from_row_end_y", 50.0)
    witness_w = gas.get("leak_witness_gutter_width_xy", 1.0)
    witness_d = gas.get("leak_witness_gutter_depth_z", 0.35)
    witness_offset = gas.get("leak_witness_gutter_offset_xy", fitting_d / 2 + 1.4)
    threshold_w = gas.get("leak_witness_threshold_width_xy", 0.8)
    threshold_h = gas.get("leak_witness_threshold_height_z", 0.6)
    center_z = lid_top_z + duct_h / 2
    if fitting_d < tube_id:
        raise ValueError("side gas fitting stem must meet or exceed tube inner diameter")
    if flange_d <= fitting_d:
        raise ValueError("side gas barb retention bead must exceed fitting stem diameter")
    if flange_d >= tube_od:
        raise ValueError("side gas barb retention bead must fit inside tube outer diameter")
    if tube_od > tube_d:
        raise ValueError("side gas tube outer diameter must fit inside tube bend envelope")
    barb_retention = {
        "retention": "printed_barb_retention_bead_and_strain_relief_no_glue",
        "tube_inner_diameter": round(tube_id, 3),
        "tube_outer_diameter": round(tube_od, 3),
        "stem_diameter": round(fitting_d, 3),
        "barb_peak_diameter": round(flange_d, 3),
        "barb_width": round(flange_w, 3),
        "stem_interference_diameter": round(max(0.0, fitting_d - tube_id), 3),
        "barb_interference_diameter": round(flange_d - tube_id, 3),
        "barb_radial_shoulder": round((flange_d - fitting_d) / 2, 3),
        "validation": "print_native_tube_capture_no_glue_or_clamp",
    }

    if layout["row_axis"] == "y":
        block_depth = row["end_margin_x"] + duct_w / 2
        gutter_len = max(block_depth - threshold_w, 0.1)
        centers = {
            "supply": row["side_margin_y"] + center_offset,
            "return": float(layout["width_y"]) - row["side_margin_y"] - center_offset,
        }
        specs: list[dict[str, Any]] = []
        for role, center_y in centers.items():
            is_supply = role == "supply"
            side = "left" if is_supply else "right"
            if is_supply:
                duct_x = row["end_margin_x"]
                flange_start_x = -stem_len - flange_w / 2
                duct_opening_x = -0.2
                gutter_x = 0.0
                threshold_x = block_depth - threshold_w
                leak_flow_direction = "-X_to_visible_outer_edge"
            else:
                duct_x = float(layout["length_x"]) - row["end_margin_x"]
                flange_start_x = float(layout["length_x"]) + stem_len - flange_w / 2
                duct_opening_x = float(layout["length_x"]) - block_depth - 0.2
                gutter_x = float(layout["length_x"]) - gutter_len
                threshold_x = float(layout["length_x"]) - block_depth
                leak_flow_direction = "+X_to_visible_outer_edge"
            block_x = 0.0 if is_supply else float(layout["length_x"]) - block_depth
            tube_x = -straight_len - bend_r if is_supply else float(layout["length_x"])
            stem_start_x = -stem_len if is_supply else float(layout["length_x"])
            fitting_rect = _axis_cylinder_envelope_rect(
                axis="x",
                x=stem_start_x,
                y=center_y,
                z=center_z,
                length=stem_len,
                diameter=fitting_d,
            )
            flange_rect = _axis_cylinder_envelope_rect(
                axis="x",
                x=flange_start_x,
                y=center_y,
                z=center_z,
                length=flange_w,
                diameter=flange_d,
            )
            leak_gutters = [
                {
                    "x": round(gutter_x, 3),
                    "y": round(center_y - witness_offset - witness_w / 2, 3),
                    "z": round(lid_top_z + block_h - witness_d, 3),
                    "length_x": round(gutter_len, 3),
                    "width_y": round(witness_w, 3),
                    "height_z": round(witness_d, 3),
                },
                {
                    "x": round(gutter_x, 3),
                    "y": round(center_y + witness_offset - witness_w / 2, 3),
                    "z": round(lid_top_z + block_h - witness_d, 3),
                    "length_x": round(gutter_len, 3),
                    "width_y": round(witness_w, 3),
                    "height_z": round(witness_d, 3),
                },
            ]
            leak_thresholds = [
                {
                    "x": round(threshold_x, 3),
                    "y": round(center_y - block_w / 2, 3),
                    "z": round(lid_top_z + block_h, 3),
                    "length_x": round(threshold_w, 3),
                    "width_y": round(block_w, 3),
                    "height_z": round(threshold_h, 3),
                }
            ]
            strain_relief_rect = {
                "x": round(-relief_len if is_supply else float(layout["length_x"]), 3),
                "y": round(center_y - relief_w / 2, 3),
                "z": round(center_z - relief_h / 2, 3),
                "length_x": round(relief_len, 3),
                "width_y": round(relief_w, 3),
                "height_z": round(relief_h, 3),
            }
            tube_rect = {
                "x": round(tube_x, 3),
                "y": round(center_y - tube_d / 2, 3),
                "z": round(center_z - tube_d / 2, 3),
                "length_x": round(straight_len + bend_r, 3),
                "width_y": round(tube_d, 3),
                "height_z": round(tube_d, 3),
            }
            installed_tube = {
                "name": f"{role}_cots_gas_tube_pigtail",
                "role": role,
                "owner_part": "cots_gas_service_tubes",
                "service_role": f"installed_operating_gas_{role}_tube",
                "axis": "x",
                "route_axis": "-X" if is_supply else "+X",
                "x": round(tube_x, 3),
                "y": round(center_y, 3),
                "z": round(center_z, 3),
                "length": round(straight_len + bend_r, 3),
                "diameter": round(tube_od, 3),
                "inner_diameter": round(tube_id, 3),
                "flow_bore_diameter": round(tube_id, 3),
                "geometry": "hollow_tube_wall",
                "body_rect": _axis_cylinder_envelope_rect(
                    axis="x",
                    x=tube_x,
                    y=center_y,
                    z=center_z,
                    length=straight_len + bend_r,
                    diameter=tube_od,
                ),
                "envelope_rect": tube_rect,
                "tube_retention": barb_retention,
                "material_intent": "COTS flexible gas tubing",
                "validation": "installed_tube_body_bend_envelope_checked_separately",
            }
            external_service_rects = [
                {"name": "printed_fitting_envelope", **fitting_rect},
                {"name": "printed_barb_retention_bead_envelope", **flange_rect},
                {"name": "strain_relief_envelope", **strain_relief_rect},
                {"name": "tube_envelope", **tube_rect},
            ]
            specs.append(
                {
                    "name": f"{role}_side_gas_service",
                    "role": role,
                    "owner_part": "lid_cover",
                    "service_role": f"production_operating_gas_{role}",
                    "side": side,
                    "port_axis": "x",
                    "duct_x": round(duct_x, 3),
                    "duct_y": round(center_y, 3),
                    "duct_z": round(center_z, 3),
                    "top_z": round(lid_top_z + block_h + threshold_h, 3),
                    "block_rect": {
                        "x": round(block_x, 3),
                        "y": round(center_y - block_w / 2, 3),
                        "z": round(lid_top_z, 3),
                        "length_x": round(block_depth, 3),
                        "width_y": round(block_w, 3),
                        "height_z": round(block_h, 3),
                    },
                    "duct_opening": {
                        "axis": "x",
                        "x": round(duct_opening_x, 3),
                        "y": round(center_y, 3),
                        "z": round(center_z, 3),
                        "length": round(block_depth + 0.4, 3),
                        "diameter": round(opening_d, 3),
                    },
                    "printed_fitting": {
                        "axis": "x",
                        "x": round(stem_start_x, 3),
                        "y": round(center_y, 3),
                        "z": round(center_z, 3),
                        "length": round(stem_len, 3),
                        "diameter": round(fitting_d, 3),
                    },
                    "printed_barb_retention_bead": {
                        "axis": "x",
                        "x": round(flange_start_x, 3),
                        "y": round(center_y, 3),
                        "z": round(center_z, 3),
                        "length": round(flange_w, 3),
                        "diameter": round(flange_d, 3),
                        "role": "tube_pulloff_resistance_without_glue",
                    },
                    "tube_retention": barb_retention,
                    "strain_relief_rect": {
                        **strain_relief_rect,
                    },
                    "leak_management": "outboard_visible_witness_gutters_with_inboard_dam",
                    "leak_flow_direction": leak_flow_direction,
                    "leak_witness_gutter_rects": leak_gutters,
                    "leak_witness_threshold_rects": leak_thresholds,
                    "tube_envelope_rect": tube_rect,
                    "installed_tube": installed_tube,
                    "external_service_rects": external_service_rects,
                    "tube_min_bend_radius": round(bend_r, 3),
                    "validation": "side_connected_supply_return_no_top_gas_caps",
                }
            )
        return specs

    block_depth = row["side_margin_y"] + duct_w / 2
    gutter_len = max(block_depth - threshold_w, 0.1)
    centers_x = {
        "supply": row["end_margin_x"] + center_offset,
        "return": float(layout["length_x"]) - row["end_margin_x"] - center_offset,
    }
    specs = []
    for role, center_x in centers_x.items():
        is_supply = role == "supply"
        side = "rear" if is_supply else "front"
        if is_supply:
            duct_y = float(layout["width_y"]) - row["side_margin_y"]
            flange_start_y = float(layout["width_y"]) + stem_len - flange_w / 2
            duct_opening_y = float(layout["width_y"]) - block_depth - 0.2
            gutter_y = float(layout["width_y"]) - gutter_len
            threshold_y = float(layout["width_y"]) - block_depth
            leak_flow_direction = "+Y_to_visible_outer_edge"
        else:
            duct_y = row["side_margin_y"]
            flange_start_y = -stem_len - flange_w / 2
            duct_opening_y = -0.2
            gutter_y = 0.0
            threshold_y = block_depth - threshold_w
            leak_flow_direction = "-Y_to_visible_outer_edge"
        block_y = float(layout["width_y"]) - block_depth if is_supply else 0.0
        tube_y = float(layout["width_y"]) if is_supply else -straight_len - bend_r
        stem_start_y = float(layout["width_y"]) if is_supply else -stem_len
        fitting_rect = _axis_cylinder_envelope_rect(
            axis="y",
            x=center_x,
            y=stem_start_y,
            z=center_z,
            length=stem_len,
            diameter=fitting_d,
        )
        flange_rect = _axis_cylinder_envelope_rect(
            axis="y",
            x=center_x,
            y=flange_start_y,
            z=center_z,
            length=flange_w,
            diameter=flange_d,
        )
        leak_gutters = [
            {
                "x": round(center_x - witness_offset - witness_w / 2, 3),
                "y": round(gutter_y, 3),
                "z": round(lid_top_z + block_h - witness_d, 3),
                "length_x": round(witness_w, 3),
                "width_y": round(gutter_len, 3),
                "height_z": round(witness_d, 3),
            },
            {
                "x": round(center_x + witness_offset - witness_w / 2, 3),
                "y": round(gutter_y, 3),
                "z": round(lid_top_z + block_h - witness_d, 3),
                "length_x": round(witness_w, 3),
                "width_y": round(gutter_len, 3),
                "height_z": round(witness_d, 3),
            },
        ]
        leak_thresholds = [
            {
                "x": round(center_x - block_w / 2, 3),
                "y": round(threshold_y, 3),
                "z": round(lid_top_z + block_h, 3),
                "length_x": round(block_w, 3),
                "width_y": round(threshold_w, 3),
                "height_z": round(threshold_h, 3),
            }
        ]
        strain_relief_rect = {
            "x": round(center_x - relief_w / 2, 3),
            "y": round(float(layout["width_y"]) if is_supply else -relief_len, 3),
            "z": round(center_z - relief_h / 2, 3),
            "length_x": round(relief_w, 3),
            "width_y": round(relief_len, 3),
            "height_z": round(relief_h, 3),
        }
        tube_rect = {
            "x": round(center_x - tube_d / 2, 3),
            "y": round(tube_y, 3),
            "z": round(center_z - tube_d / 2, 3),
            "length_x": round(tube_d, 3),
            "width_y": round(straight_len + bend_r, 3),
            "height_z": round(tube_d, 3),
        }
        installed_tube = {
            "name": f"{role}_cots_gas_tube_pigtail",
            "role": role,
            "owner_part": "cots_gas_service_tubes",
            "service_role": f"installed_operating_gas_{role}_tube",
            "axis": "y",
            "route_axis": "+Y" if is_supply else "-Y",
            "x": round(center_x, 3),
            "y": round(tube_y, 3),
            "z": round(center_z, 3),
            "length": round(straight_len + bend_r, 3),
            "diameter": round(tube_od, 3),
            "inner_diameter": round(tube_id, 3),
            "flow_bore_diameter": round(tube_id, 3),
            "geometry": "hollow_tube_wall",
            "body_rect": _axis_cylinder_envelope_rect(
                axis="y",
                x=center_x,
                y=tube_y,
                z=center_z,
                length=straight_len + bend_r,
                diameter=tube_od,
            ),
            "envelope_rect": tube_rect,
            "tube_retention": barb_retention,
            "material_intent": "COTS flexible gas tubing",
            "validation": "installed_tube_body_bend_envelope_checked_separately",
        }
        external_service_rects = [
            {"name": "printed_fitting_envelope", **fitting_rect},
            {"name": "printed_barb_retention_bead_envelope", **flange_rect},
            {"name": "strain_relief_envelope", **strain_relief_rect},
            {"name": "tube_envelope", **tube_rect},
        ]
        specs.append(
            {
                "name": f"{role}_side_gas_service",
                "role": role,
                "owner_part": "lid_cover",
                "service_role": f"production_operating_gas_{role}",
                "side": side,
                "port_axis": "y",
                "duct_x": round(center_x, 3),
                "duct_y": round(duct_y, 3),
                "duct_z": round(center_z, 3),
                "top_z": round(lid_top_z + block_h + threshold_h, 3),
                "block_rect": {
                    "x": round(center_x - block_w / 2, 3),
                    "y": round(block_y, 3),
                    "z": round(lid_top_z, 3),
                    "length_x": round(block_w, 3),
                    "width_y": round(block_depth, 3),
                    "height_z": round(block_h, 3),
                },
                "duct_opening": {
                    "axis": "y",
                    "x": round(center_x, 3),
                    "y": round(duct_opening_y, 3),
                    "z": round(center_z, 3),
                    "length": round(block_depth + 0.4, 3),
                    "diameter": round(opening_d, 3),
                },
                "printed_fitting": {
                    "axis": "y",
                    "x": round(center_x, 3),
                    "y": round(stem_start_y, 3),
                    "z": round(center_z, 3),
                    "length": round(stem_len, 3),
                    "diameter": round(fitting_d, 3),
                },
                "printed_barb_retention_bead": {
                    "axis": "y",
                    "x": round(center_x, 3),
                    "y": round(flange_start_y, 3),
                    "z": round(center_z, 3),
                    "length": round(flange_w, 3),
                    "diameter": round(flange_d, 3),
                    "role": "tube_pulloff_resistance_without_glue",
                },
                "tube_retention": barb_retention,
                "strain_relief_rect": {
                    **strain_relief_rect,
                },
                "leak_management": "outboard_visible_witness_gutters_with_inboard_dam",
                "leak_flow_direction": leak_flow_direction,
                "leak_witness_gutter_rects": leak_gutters,
                "leak_witness_threshold_rects": leak_thresholds,
                "tube_envelope_rect": tube_rect,
                "installed_tube": installed_tube,
                "external_service_rects": external_service_rects,
                "tube_min_bend_radius": round(bend_r, 3),
                "validation": "side_connected_supply_return_no_top_gas_caps",
            }
        )
    return specs


def _side_gas_tube_envelope_check(
    tube_envelopes: list[dict[str, Any]],
) -> dict[str, Any]:
    envelope_lengths = [
        max(float(rect["length_x"]), float(rect["width_y"])) for rect in tube_envelopes
    ]
    bend_radii = {round(float(rect["min_bend_radius"]), 3) for rect in tube_envelopes}
    max_envelope_length = max(envelope_lengths, default=0.0)
    min_bend_radius = min(bend_radii, default=0.0)
    return {
        "name": "side_gas_tube_envelope_check",
        "role": "side_gas_tube_bend_and_strain_relief_validation_body",
        "validation": "required_gate2_tube_bend_and_retention_evidence",
        "failure_rule": (
            "kink_pull_off_or_unmeasured_tube_bend_blocks_dry_assembly_pass"
        ),
        "evidence_gate": "Gate 2 dry assembly",
        "cad_value": (
            f"{len(tube_envelopes)} tubes / {max_envelope_length:.2f} mm envelope / "
            f"{min_bend_radius:.2f} mm bend radius"
        ),
        "tube_count": len(tube_envelopes),
        "max_envelope_length_mm": round(max_envelope_length, 3),
        "min_bend_radius": round(min_bend_radius, 3),
        "tube_roles": tuple(rect["role"] for rect in tube_envelopes),
        "source_layout_checks": ["side_gas_service_interfaces"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "operating_gas_supply_connected",
            "operating_gas_return_connected",
            "tube_pulloff_resistance_without_glue",
        ],
        "body_rects": tube_envelopes,
    }


def _side_gas_tube_envelopes(
    interfaces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "name": f"{interface['name']}_tube_bend_envelope",
            "role": interface["role"],
            **interface["tube_envelope_rect"],
            "min_bend_radius": interface["tube_min_bend_radius"],
        }
        for interface in interfaces
    ]


def _unseated_side_gas_tube_review_specs(
    gas_service_tubes: list[dict[str, Any]],
    *,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    offset = float(production.get("side_gas_unseated_review_offset_xy", 8.0))
    if offset <= 0:
        raise ValueError("side gas unseated review offset must be positive")

    review_specs: list[dict[str, Any]] = []
    for tube in gas_service_tubes:
        axis = str(tube["axis"])
        route = str(tube["route_axis"])
        dx = dy = 0.0
        if axis == "x":
            dx = -offset if route == "-X" else offset
        elif axis == "y":
            dy = offset if route == "+Y" else -offset
        else:
            raise ValueError("side gas tube unseated review requires x or y axis")

        x = round(float(tube["x"]) + dx, 3)
        y = round(float(tube["y"]) + dy, 3)
        z = round(float(tube["z"]), 3)
        body_rect = _axis_cylinder_envelope_rect(
            axis=axis,
            x=x,
            y=y,
            z=z,
            length=float(tube["length"]),
            diameter=float(tube["diameter"]),
        )
        review_specs.append(
            {
                "name": f"{tube['role']}_unseated_side_gas_tube_review",
                "role": tube["role"],
                "owner_part": "unseated_side_gas_tubes_review",
                "review_state": "side_gas_tubes_unseated",
                "review_kind": "unseated_cots_gas_tube",
                "removed_part": "cots_gas_service_tubes",
                "source_rect_name": tube["name"],
                "axis": axis,
                "route_axis": route,
                "x": x,
                "y": y,
                "z": z,
                "length": tube["length"],
                "diameter": tube["diameter"],
                "inner_diameter": tube["inner_diameter"],
                "flow_bore_diameter": tube["flow_bore_diameter"],
                "unseated_offset_xy": round(offset, 3),
                "body_rect": body_rect,
                "meaning": "COTS gas tube is present but pulled off the printed barb",
            }
        )
    return review_specs


def build_cots_gas_service_tubes(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    tubes: cq.Workplane | None = None
    for tube in layout["cots_gas_service_tubes"]:
        model = _axis_tube(
            axis=tube["axis"],
            x=float(tube["x"]),
            y=float(tube["y"]),
            z=float(tube["z"]) + z_shift,
            length=float(tube["length"]),
            outer_diameter=float(tube["diameter"]),
            inner_diameter=float(tube["inner_diameter"]),
        )
        tubes = model if tubes is None else tubes.union(model)
    if tubes is None:
        raise ValueError("gas service tubes require at least one tube")
    return tubes


def build_gas_pcb_flow_cell_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["gas_pcb_flow_cell_check"]["flow_cell_rects"]
    if not rects:
        raise ValueError("gas PCB flow-cell check requires at least one flow cell")
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_gas_sensor_pcbs(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    pcbs: cq.Workplane | None = None
    for mount in layout["gas_sensor_pcb_mounts"]:
        z = float(mount["z"]) if assembly_position else 0.0
        pcb = (
            cq.Workplane("XY")
            .box(
                float(mount["length_x"]),
                float(mount["width_y"]),
                float(mount["height_z"]),
                centered=(False, False, False),
            )
            .translate((float(mount["x"]), float(mount["y"]), z))
        )
        pcb = _cut_vertical_mount_aperture(pcb, mount, z=z)
        chip = _sensor_chip_marker_for_mount(mount, z=z)
        pcb = pcb.union(chip)
        pcbs = pcb if pcbs is None else pcbs.union(pcb)
    if pcbs is None:
        raise ValueError("gas sensor PCB model requires at least one mount")
    return pcbs


def _keeper_door_body(
    mount: dict[str, Any],
    layout: dict[str, Any],
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    """Single per-mount keeper door body (door box + release tab union)."""

    mounts = params.get("sensor_mounts", {})
    install = params.get("sensor_installation", {})
    wall = mounts.get("gas_pcb_socket_wall_thickness", 1.2)
    door_h = install.get("gas_pcb_keeper_door_height_z", 0.8)
    tab_len = install.get("gas_pcb_keeper_release_tab_length_y", 4.0)
    tab_w = install.get("gas_pcb_keeper_release_tab_width_x", 3.0)

    x = float(mount["x"])
    y = float(mount["y"])
    z = float(mount["z"]) if assembly_position else 0.0
    length_x = float(mount["length_x"])
    width_y = float(mount["width_y"])
    height_z = float(mount["height_z"])
    door_z = z + height_z - door_h
    door = (
        cq.Workplane("XY")
        .box(
            length_x + 2 * wall,
            width_y + 2 * wall,
            door_h,
            centered=(False, False, False),
        )
        .translate((x - wall, y - wall, door_z))
    )
    if length_x <= width_y:
        if mount["role"] == "supply":
            tab_x = max(0.0, x - wall - tab_w)
        else:
            tab_x = min(float(layout["length_x"]) - tab_w, x + length_x + wall)
        tab_y = float(mount["aperture_y"]) - tab_len / 2
        tab = (
            cq.Workplane("XY")
            .box(tab_w, tab_len, door_h, centered=(False, False, False))
            .translate((tab_x, tab_y, door_z))
        )
    else:
        if mount["role"] == "supply":
            tab_y = max(0.0, y - wall - tab_len)
        else:
            tab_y = min(float(layout["width_y"]) - tab_len, y + width_y + wall)
        tab_x = float(mount["aperture_x"]) - tab_w / 2
        tab = (
            cq.Workplane("XY")
            .box(tab_w, tab_len, door_h, centered=(False, False, False))
            .translate((tab_x, tab_y, door_z))
        )
    return door.union(tab)


def build_printed_gas_pcb_keeper_doors(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)

    doors: cq.Workplane | None = None
    for mount in layout["gas_sensor_pcb_mounts"]:
        door = _keeper_door_body(
            mount, layout, params, assembly_position=assembly_position
        )
        doors = door if doors is None else doors.union(door)
    if doors is None:
        raise ValueError("gas PCB keeper doors require at least one mount")
    return doors


def _printed_gas_pcb_keeper_door_models(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> dict[str, cq.Workplane]:
    """Per-instance keeper-door bodies (single solid each, no cross-instance union)."""

    layout = row_coupon_layout(params)
    models: dict[str, cq.Workplane] = {}
    for i, mount in enumerate(layout["gas_sensor_pcb_mounts"]):
        models[f"keeper_door_{i}"] = _keeper_door_body(
            mount, layout, params, assembly_position=assembly_position
        )
    return models


def build_side_gas_leak_witness_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["side_gas_leak_witness_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_side_gas_tube_envelope_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["side_gas_tube_envelope_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_unseated_gas_pcb_cartridges_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    review_rects = layout["unseated_gas_pcb_cartridges_review"]
    mounts_by_name = {mount["name"]: mount for mount in layout["gas_sensor_pcb_mounts"]}
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]

    review: cq.Workplane | None = None
    for rect in review_rects:
        mount = mounts_by_name[rect["source_rect_name"]]
        z = float(rect["z"]) + z_shift
        pcb = (
            cq.Workplane("XY")
            .box(
                float(rect["length_x"]),
                float(rect["width_y"]),
                float(rect["height_z"]),
                centered=(False, False, False),
            )
            .translate((float(rect["x"]), float(rect["y"]), z))
        )
        pcb = _cut_vertical_mount_aperture(pcb, mount, z=z)
        pcb = pcb.union(_sensor_chip_marker_for_mount(mount, z=z))

        door_rect = dict(rect["keeper_door_rect"])
        tab_rect = dict(rect["keeper_tab_rect"])
        door_rect["z"] = float(door_rect["z"]) + z_shift
        tab_rect["z"] = float(tab_rect["z"]) + z_shift
        door = _boxes_from_rectangles([door_rect, tab_rect])
        body = pcb.union(door)
        review = body if review is None else review.union(body)
    if review is None:
        raise ValueError("unseated gas PCB cartridge review requires at least one mount")
    return review
