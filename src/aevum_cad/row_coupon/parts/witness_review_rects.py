from __future__ import annotations
from typing import Any
import cadquery as cq
from ..layout import (row_coupon_layout)
from ._geom_base import (_axis_tube, _perimeter_rails)


def _missing_gas_pcb_cartridge_witness_rectangles(
    *,
    gas_sensor_pcb_mounts: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    rail_w = production.get("missing_gas_pcb_witness_frame_width_xy", 1.0)
    height = production.get("missing_gas_pcb_witness_height_z", 0.7)
    witnesses: list[dict[str, Any]] = []
    for mount in gas_sensor_pcb_mounts:
        witnesses.append(
            {
                "name": f"{mount['role']}_missing_gas_pcb_cartridge_footprint",
                "role": mount["role"],
                "witness_kind": "cartridge_top_footprint",
                "x": mount["x"],
                "y": mount["y"],
                "z": round(float(mount["z"]) + float(mount["height_z"]), 3),
                "length_x": mount["length_x"],
                "width_y": mount["width_y"],
                "height_z": round(float(height), 3),
                "rail_width": round(float(rail_w), 3),
                "review_state": "gas_pcbs_missing",
                "removed_part": "gas_sensor_pcbs",
                "dependent_removed_part": "gas_pcb_interface_gaskets",
                "meaning": "gas PCB cartridge top-footprint witness at expected seated socket",
            }
        )
        gasket_rect = mount["gas_interface"]["gasket_rect"]
        witnesses.append(
            {
                "name": f"{mount['role']}_missing_gas_pcb_interface_gasket",
                "role": mount["role"],
                "witness_kind": "duct_seal_gasket",
                "x": gasket_rect["x"],
                "y": gasket_rect["y"],
                "z": gasket_rect["z"],
                "length_x": gasket_rect["length_x"],
                "width_y": gasket_rect["width_y"],
                "height_z": gasket_rect["height_z"],
                "review_state": "gas_pcbs_missing",
                "removed_part": "gas_pcb_interface_gaskets",
                "dependent_removed_part": "gas_sensor_pcbs",
                "meaning": "missing duct-seal gasket witness at gas PCB sampling interface",
            }
        )
    return witnesses


def _missing_local_sensor_witness_rectangles(
    *,
    headspace_sht41_mounts: list[dict[str, Any]],
    ir_sensor_mounts: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    rail_w = production.get("missing_local_sensor_witness_frame_width_xy", 0.9)
    height = production.get("missing_local_sensor_witness_height_z", 0.7)
    witnesses: list[dict[str, Any]] = []

    for mount in headspace_sht41_mounts:
        witnesses.append(
            {
                "name": f"{mount['name']}_missing_headspace_sht41_carrier",
                "sensor_kind": "headspace_sht41_microcarrier",
                "tile_index": mount["tile_index"],
                "witness_kind": "headspace_sht41_carrier_footprint",
                "review_state": "local_sensors_missing",
                "removed_part": "headspace_sht41_microcarriers",
                "source_rect_name": mount["name"],
                "retention": mount["retention"],
                "x": mount["x"],
                "y": mount["y"],
                "z": round(float(mount["z"]) + float(mount["height_z"]), 3),
                "length_x": mount["length_x"],
                "width_y": mount["width_y"],
                "height_z": round(float(height), 3),
                "rail_width": round(float(rail_w), 3),
                "aperture_x": mount["aperture_x"],
                "aperture_y": mount["aperture_y"],
                "meaning": "missing SHT41 carrier footprint at wet-headspace socket",
            }
        )

    for mount in ir_sensor_mounts:
        witnesses.append(
            {
                "name": f"{mount['name']}_missing_ir_thermopile_body",
                "sensor_kind": "lower_ir_thermopile",
                "tile_index": mount["tile_index"],
                "witness_kind": "ir_thermopile_body_footprint",
                "review_state": "local_sensors_missing",
                "removed_part": "ir_thermopiles",
                "dependent_removed_part": "ir_thermopile_face_gaskets",
                "source_rect_name": mount["name"],
                "retention": mount["retention"],
                "x": mount["x"],
                "y": mount["y"],
                "z": round(float(mount["z"]) + float(mount["height_z"]), 3),
                "length_x": mount["length_x"],
                "width_y": mount["width_y"],
                "height_z": round(float(height), 3),
                "rail_width": round(float(rail_w), 3),
                "aperture_x": mount["aperture_x"],
                "aperture_y": mount["aperture_y"],
                "meaning": "missing lower IR thermopile footprint at dry-side pocket",
            }
        )
        gasket = mount["face_gasket"]
        outer_d = float(gasket["outer_diameter"])
        witnesses.append(
            {
                "name": f"{mount['name']}_missing_ir_face_gasket_seal",
                "sensor_kind": "lower_ir_face_gasket",
                "tile_index": mount["tile_index"],
                "witness_kind": "ir_face_gasket_seal",
                "review_state": "local_sensors_missing",
                "removed_part": "ir_thermopile_face_gaskets",
                "dependent_removed_part": "ir_thermopiles",
                "source_rect_name": mount["name"],
                "center_x": gasket["x"],
                "center_y": gasket["y"],
                "x": round(float(gasket["x"]) - outer_d / 2, 3),
                "y": round(float(gasket["y"]) - outer_d / 2, 3),
                "z": gasket["z"],
                "length_x": round(outer_d, 3),
                "width_y": round(outer_d, 3),
                "height_z": gasket["height_z"],
                "outer_diameter": gasket["outer_diameter"],
                "inner_diameter": gasket["inner_diameter"],
                "nominal_compression_z": gasket["nominal_compression_z"],
                "meaning": "missing IR dry-side face-gasket seal witness",
            }
        )
    return witnesses


def _missing_microplate_witness_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
    plate_bottom_z: float,
) -> list[dict[str, Any]]:
    plate = params["plate"]
    production = params.get("production_assembly", {})
    rail_w = production.get("missing_microplate_witness_frame_width_xy", 1.2)
    height = production.get("missing_microplate_witness_height_z", 0.7)
    return [
        {
            "tile_index": tile["index"],
            "x": round(float(tile["x"]), 3),
            "y": round(float(tile["y"]), 3),
            "z": round(float(plate_bottom_z), 3),
            "length_x": round(float(plate["length_x"]), 3),
            "width_y": round(float(plate["width_y"]), 3),
            "height_z": round(float(height), 3),
            "rail_width": round(float(rail_w), 3),
            "review_state": "microplates_missing",
            "removed_part": "cots_microplates",
            "dependent_removed_part": "cots_septum_mats",
            "meaning": "microplate footprint witness at expected seated support datum",
        }
        for tile in tile_origins
    ]


def _missing_perimeter_gasket_witness_rectangles(
    *,
    skirt_bounds: dict[str, float],
    params: dict[str, Any],
    base_top_z: float,
    gasket_bottom_z: float,
) -> list[dict[str, Any]]:
    seal = params["seal_interface"]
    rail_w = seal["gasket_rail_width"]
    height = seal["compressed_gasket_height_z"]
    layers = (
        (
            "lower",
            "lower_gasket",
            base_top_z,
            "between_plate_support_frame_and_wet_chamber_frame",
        ),
        (
            "upper",
            "upper_gasket",
            gasket_bottom_z,
            "between_wet_chamber_frame_and_lid_manifold_shell",
        ),
    )
    return [
        {
            "layer": layer,
            "x": round(float(skirt_bounds["x"]), 3),
            "y": round(float(skirt_bounds["y"]), 3),
            "z": round(float(z), 3),
            "length_x": round(float(skirt_bounds["length_x"]), 3),
            "width_y": round(float(skirt_bounds["width_y"]), 3),
            "height_z": round(float(height), 3),
            "rail_width": round(float(rail_w), 3),
            "review_state": "perimeter_gaskets_missing",
            "removed_part": removed_part,
            "interface": interface,
            "meaning": "perimeter seal witness occupying the missing compressed gasket volume",
        }
        for layer, removed_part, z, interface in layers
    ]


def _missing_septum_mat_witness_rectangles(
    *,
    tile_origins: list[dict[str, Any]],
    params: dict[str, Any],
    plate_top_z: float,
) -> list[dict[str, Any]]:
    plate = params["plate"]
    mat = params["septum_mat"]
    production = params.get("production_assembly", {})
    rail_w = production.get("missing_septum_mat_witness_frame_width_xy", 1.2)
    height = production.get("missing_septum_mat_witness_height_z", 0.7)
    z = plate_top_z + mat["sheet_thickness_z"]
    return [
        {
            "tile_index": tile["index"],
            "x": round(float(tile["x"]), 3),
            "y": round(float(tile["y"]), 3),
            "z": round(z, 3),
            "length_x": round(float(plate["length_x"]), 3),
            "width_y": round(float(plate["width_y"]), 3),
            "height_z": round(float(height), 3),
            "rail_width": round(float(rail_w), 3),
            "review_state": "septum_mats_missing",
            "removed_part": "cots_septum_mats",
            "meaning": "mat footprint witness at expected seated septum-mat top plane",
        }
        for tile in tile_origins
    ]


def _missing_service_lead_witness_rectangles(
    *,
    gas_service_tubes: list[dict[str, Any]],
    sensor_service_cable_pigtails: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    production = params.get("production_assembly", {})
    rail_w = production.get("missing_service_lead_witness_frame_width_xy", 0.9)
    height = production.get("missing_service_lead_witness_height_z", 0.7)
    span = production.get("missing_service_lead_witness_span_xy", 8.0)
    witnesses: list[dict[str, Any]] = []

    for tube in gas_service_tubes:
        body = tube["body_rect"]
        axis = tube["axis"]
        route = tube["route_axis"]
        if axis == "x":
            length_x = min(float(span), float(body["length_x"]))
            width_y = float(body["width_y"])
            x = float(body["x"])
            if route == "-X":
                x += float(body["length_x"]) - length_x
            y = float(body["y"])
        elif axis == "y":
            length_x = float(body["length_x"])
            width_y = min(float(span), float(body["width_y"]))
            x = float(body["x"])
            y = float(body["y"])
            if route == "-Y":
                y += float(body["width_y"]) - width_y
        else:
            raise ValueError("gas service lead witness requires x or y axis")
        witnesses.append(
            {
                "name": f"{tube['role']}_missing_gas_service_lead_handoff",
                "service_kind": "gas_tube",
                "role": tube["role"],
                "witness_kind": "gas_tube_handoff",
                "removed_part": "cots_gas_service_tubes",
                "review_state": "service_leads_missing",
                "x": round(x, 3),
                "y": round(y, 3),
                "z": round(float(body["z"]) + float(body["height_z"]), 3),
                "length_x": round(length_x, 3),
                "width_y": round(width_y, 3),
                "height_z": round(height, 3),
                "rail_width": round(rail_w, 3),
                "source_rect_name": tube["name"],
                "route_axis": route,
                "meaning": "missing COTS gas tube at printed side fitting handoff",
            }
        )

    for pigtail in sensor_service_cable_pigtails:
        connector_name = str(pigtail["connector_name"])
        removed_part = (
            "lower_sensor_service_cable_pigtail"
            if connector_name.startswith("lower_")
            else "lid_sensor_service_cable_pigtails"
        )
        width_y = min(float(span), float(pigtail["width_y"]))
        witnesses.append(
            {
                "name": f"{connector_name}_missing_electrical_service_lead_handoff",
                "service_kind": "electrical_cable",
                "role": connector_name,
                "witness_kind": "electrical_cable_handoff",
                "removed_part": removed_part,
                "review_state": "service_leads_missing",
                "x": round(float(pigtail["x"]), 3),
                "y": round(float(pigtail["y"]), 3),
                "z": round(float(pigtail["z"]) + float(pigtail["height_z"]), 3),
                "length_x": round(float(pigtail["length_x"]), 3),
                "width_y": round(width_y, 3),
                "height_z": round(height, 3),
                "rail_width": round(rail_w, 3),
                "source_rect_name": pigtail["name"],
                "route_axis": pigtail["route_axis"],
                "meaning": "missing COTS electrical cable pigtail at keyed connector handoff",
            }
        )
    return witnesses


def _unseated_gas_pcb_cartridge_review_rectangles(
    layout: dict[str, Any],
    *,
    gas_sensor_pcb_mounts: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    mounts = params.get("sensor_mounts", {})
    install = params.get("sensor_installation", {})
    lift_z = float(install.get("gas_pcb_service_lift_z", 18.0))
    wall = float(mounts.get("gas_pcb_socket_wall_thickness", 1.2))
    door_h = float(install.get("gas_pcb_keeper_door_height_z", 0.8))
    tab_len = float(install.get("gas_pcb_keeper_release_tab_length_y", 4.0))
    tab_w = float(install.get("gas_pcb_keeper_release_tab_width_x", 3.0))

    review_rects: list[dict[str, Any]] = []
    for mount in gas_sensor_pcb_mounts:
        x = float(mount["x"])
        y = float(mount["y"])
        z = float(mount["z"])
        length_x = float(mount["length_x"])
        width_y = float(mount["width_y"])
        height_z = float(mount["height_z"])
        lifted_z = z + lift_z
        door_z = lifted_z + height_z - door_h
        if length_x <= width_y:
            if mount["role"] == "supply":
                tab_x = max(0.0, x - wall - tab_w)
            else:
                tab_x = min(float(layout["length_x"]) - tab_w, x + length_x + wall)
            tab_y = float(mount["aperture_y"]) - tab_len / 2
        else:
            if mount["role"] == "supply":
                tab_y = max(0.0, y - wall - tab_len)
            else:
                tab_y = min(float(layout["width_y"]) - tab_len, y + width_y + wall)
            tab_x = float(mount["aperture_x"]) - tab_w / 2

        review_rects.append(
            {
                "name": f"{mount['role']}_unseated_gas_pcb_cartridge_review",
                "role": mount["role"],
                "owner_part": "unseated_gas_pcb_cartridges_review",
                "review_state": "gas_pcb_cartridges_unseated",
                "review_kind": "lifted_gas_pcb_cartridge",
                "removed_part": "gas_sensor_pcbs",
                "dependent_removed_part": "printed_gas_pcb_keeper_doors",
                "retained_part": "gas_pcb_interface_gaskets",
                "source_rect_name": mount["name"],
                "unseated_offset_z": round(lift_z, 3),
                "x": round(x, 3),
                "y": round(y, 3),
                "z": round(lifted_z, 3),
                "length_x": round(length_x, 3),
                "width_y": round(width_y, 3),
                "height_z": round(height_z, 3),
                "pcb_rect": {
                    "x": round(x, 3),
                    "y": round(y, 3),
                    "z": round(lifted_z, 3),
                    "length_x": round(length_x, 3),
                    "width_y": round(width_y, 3),
                    "height_z": round(height_z, 3),
                },
                "keeper_door_rect": {
                    "x": round(x - wall, 3),
                    "y": round(y - wall, 3),
                    "z": round(door_z, 3),
                    "length_x": round(length_x + 2 * wall, 3),
                    "width_y": round(width_y + 2 * wall, 3),
                    "height_z": round(door_h, 3),
                },
                "keeper_tab_rect": {
                    "x": round(tab_x, 3),
                    "y": round(tab_y, 3),
                    "z": round(door_z, 3),
                    "length_x": round(tab_w, 3),
                    "width_y": round(tab_len, 3),
                    "height_z": round(door_h, 3),
                },
                "meaning": (
                    "gas PCB cartridge is present but lifted off the compressed "
                    "duct sampling gasket"
                ),
            }
        )
    return review_rects


def build_missing_gas_pcb_cartridge_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]

    witnesses: cq.Workplane | None = None
    for witness in layout["missing_gas_pcb_cartridge_witnesses"]:
        if witness["witness_kind"] == "cartridge_top_footprint":
            part = _perimeter_rails(
                x0=float(witness["x"]),
                y0=float(witness["y"]),
                length=float(witness["length_x"]),
                width=float(witness["width_y"]),
                rail_width=float(witness["rail_width"]),
                height=float(witness["height_z"]),
                z0=float(witness["z"]) + z_shift,
            )
        else:
            part = (
                cq.Workplane("XY")
                .box(
                    float(witness["length_x"]),
                    float(witness["width_y"]),
                    float(witness["height_z"]),
                    centered=(False, False, False),
                )
                .translate(
                    (
                        float(witness["x"]),
                        float(witness["y"]),
                        float(witness["z"]) + z_shift,
                    )
                )
            )
        witnesses = part if witnesses is None else witnesses.union(part)
    if witnesses is None:
        raise ValueError("missing gas PCB witnesses require at least one cartridge")
    return witnesses


def build_missing_local_sensor_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    witness_rects = layout["missing_local_sensor_witnesses"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in witness_rects)

    witnesses: cq.Workplane | None = None
    for witness in witness_rects:
        if witness["witness_kind"] in {
            "headspace_sht41_carrier_footprint",
            "ir_thermopile_body_footprint",
        }:
            part = _perimeter_rails(
                x0=float(witness["x"]),
                y0=float(witness["y"]),
                length=float(witness["length_x"]),
                width=float(witness["width_y"]),
                rail_width=float(witness["rail_width"]),
                height=float(witness["height_z"]),
                z0=float(witness["z"]) + z_shift,
            )
        elif witness["witness_kind"] == "ir_face_gasket_seal":
            part = (
                cq.Workplane("XY")
                .circle(float(witness["outer_diameter"]) / 2)
                .circle(float(witness["inner_diameter"]) / 2)
                .extrude(float(witness["height_z"]))
                .translate(
                    (
                        float(witness["center_x"]),
                        float(witness["center_y"]),
                        float(witness["z"]) + z_shift,
                    )
                )
            )
        else:
            raise ValueError(f"unknown local sensor witness kind: {witness['witness_kind']}")
        witnesses = part if witnesses is None else witnesses.union(part)
    if witnesses is None:
        raise ValueError("missing local sensor witnesses require at least one sensor mount")
    return witnesses


def build_missing_microplate_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["plate_bottom_z"]

    witnesses: cq.Workplane | None = None
    for witness in layout["missing_microplate_witnesses"]:
        frame = _perimeter_rails(
            x0=float(witness["x"]),
            y0=float(witness["y"]),
            length=float(witness["length_x"]),
            width=float(witness["width_y"]),
            rail_width=float(witness["rail_width"]),
            height=float(witness["height_z"]),
            z0=float(witness["z"]) + z_shift,
        )
        witnesses = frame if witnesses is None else witnesses.union(frame)
    if witnesses is None:
        raise ValueError("missing microplate witnesses require at least one tile")
    return witnesses


def build_missing_perimeter_gasket_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    from aevum_cad.row_coupon import (build_lower_gasket, build_upper_gasket)
    lower = build_lower_gasket(params, assembly_position=assembly_position)
    upper = build_upper_gasket(params, assembly_position=assembly_position)
    return lower.union(upper)


def build_missing_septum_mat_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["plate_top_z"]

    witnesses: cq.Workplane | None = None
    for witness in layout["missing_septum_mat_witnesses"]:
        frame = _perimeter_rails(
            x0=float(witness["x"]),
            y0=float(witness["y"]),
            length=float(witness["length_x"]),
            width=float(witness["width_y"]),
            rail_width=float(witness["rail_width"]),
            height=float(witness["height_z"]),
            z0=float(witness["z"]) + z_shift,
        )
        witnesses = frame if witnesses is None else witnesses.union(frame)
    if witnesses is None:
        raise ValueError("missing septum mat witnesses require at least one tile")
    return witnesses


def build_missing_service_lead_witnesses(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    witness_rects = layout["missing_service_lead_witnesses"]
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in witness_rects)

    witnesses: cq.Workplane | None = None
    for witness in witness_rects:
        part = _perimeter_rails(
            x0=float(witness["x"]),
            y0=float(witness["y"]),
            length=float(witness["length_x"]),
            width=float(witness["width_y"]),
            rail_width=float(witness["rail_width"]),
            height=float(witness["height_z"]),
            z0=float(witness["z"]) + z_shift,
        )
        witnesses = part if witnesses is None else witnesses.union(part)
    if witnesses is None:
        raise ValueError("missing service lead witnesses require at least one service lead")
    return witnesses


def build_unseated_side_gas_tubes_review(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    review_specs = layout["unseated_side_gas_tubes_review"]
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]

    review: cq.Workplane | None = None
    for spec in review_specs:
        model = _axis_tube(
            axis=str(spec["axis"]),
            x=float(spec["x"]),
            y=float(spec["y"]),
            z=float(spec["z"]) + z_shift,
            length=float(spec["length"]),
            outer_diameter=float(spec["diameter"]),
            inner_diameter=float(spec["inner_diameter"]),
        )
        review = model if review is None else review.union(model)
    if review is None:
        raise ValueError("unseated side gas tube review requires at least one tube")
    return review
