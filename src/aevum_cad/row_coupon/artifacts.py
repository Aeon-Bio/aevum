from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

import cadquery as cq

from .layout import row_coupon_layout
from .manifest import row_coupon_part_manifest
from .parts._geom_base import (
    _boxes_from_rectangles,
    _harness_z_shift,
    _rounded_box,
)
from .parts._shared_tile import _deck_slot_opening_for_tile
from .parts.gas_pcb import _keeper_door_body
from .parts.harness import (
    _build_printed_sensor_connector_shrouds,
    _harness_cover_from_rectangles,
    _shroud_grip_rib_kwargs,
    build_lower_harness_cover,
    build_printed_lower_sensor_connector_shroud,
)
from .parts.latches import _build_wedge_lock_body, _wedge_lock_rectangles
from .parts.sample_relief import build_printed_sample_relief_cap
from .parts.sealing import (
    _cut_rectangular_gas_interface_window,
    build_lower_gasket,
    build_upper_gasket,
)
from .parts.structural import (
    _add_deck_engagement_feet,
    _add_pod_frame_keys,
    build_lid_cover,
    build_lid_manifold_shell,
    build_plate_support_frame,
    build_wet_chamber_frame,
)


class RowCouponPhysicalArtifactSpec(NamedTuple):
    name: str
    installed_part: str


class RowCouponPhysicalArtifactPrintPolicy(NamedTuple):
    name: str
    installed_part: str
    policy: str
    target_x_mm: float
    target_y_mm: float
    target_z_mm: float
    reason: str


ROW_COUPON_PHYSICAL_ARTIFACT_PRINT_POLICIES = frozenset(
    {
        "bed_fit_identity",
        "structural_split_allowed",
        "canonical_redesign_required",
        "nonprinted_or_flexible",
        "discrete_unsplittable",
    }
)

ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS = frozenset(
    {
        "plate_support_frame",
        "lower_harness_cover",
        "wet_chamber_frame",
        "lid_manifold_shell",
        "lid_harness_cover_lid_cover_left_gas_bus",
        "lid_harness_cover_lid_cover_right_gas_bus",
        "lid_harness_cover_lid_shell_right_sht41_bus",
        "lid_cover",
    }
)

ROW_COUPON_DISCRETE_UNSPLITTABLE_INSTALLED_PARTS = frozenset(
    {
        "deck_pods",
        "printed_lower_sensor_connector_shroud",
        "printed_lid_sensor_connector_shrouds",
        "printed_gas_pcb_keeper_doors",
        "printed_sample_relief_cap",
        "printed_wedge_locks",
    }
)


def _tile_key(prefix: str, tile: dict[str, Any]) -> str:
    index = tile["index"] if "index" in tile else tile["tile_index"]
    return f"{prefix}_tile_{int(index)}"


def _mount_key(prefix: str, mount: dict[str, Any]) -> str:
    return f"{prefix}_{mount['name']}"


def _connector_key(prefix: str, connector: dict[str, Any]) -> str:
    return f"{prefix}_{connector['name']}"


def _wedge_lock_key(index: int, lock_rect: dict[str, Any]) -> str:
    return (
        f"printed_wedge_lock_station_{index:02d}_"
        f"{lock_rect['slide_axis']}_{lock_rect['insert_from']}"
    )


def row_coupon_physical_artifact_specs(
    params: dict[str, Any],
) -> tuple[RowCouponPhysicalArtifactSpec, ...]:
    layout = row_coupon_layout(params)
    specs: list[RowCouponPhysicalArtifactSpec] = []

    specs.extend(
        RowCouponPhysicalArtifactSpec(_tile_key("deck_pod", tile), "deck_pods")
        for tile in layout["tile_origins"]
    )
    specs.append(RowCouponPhysicalArtifactSpec("plate_support_frame", "plate_support_frame"))
    specs.extend(
        RowCouponPhysicalArtifactSpec(
            _tile_key("ir_thermopile_face_gasket", mount),
            "ir_thermopile_face_gaskets",
        )
        for mount in layout["ir_sensor_mounts"]
    )
    specs.extend(
        [
            RowCouponPhysicalArtifactSpec("lower_harness_cover", "lower_harness_cover"),
            RowCouponPhysicalArtifactSpec(
                "printed_lower_sensor_connector_shroud",
                "printed_lower_sensor_connector_shroud",
            ),
            RowCouponPhysicalArtifactSpec("lower_gasket", "lower_gasket"),
            RowCouponPhysicalArtifactSpec("wet_chamber_frame", "wet_chamber_frame"),
            RowCouponPhysicalArtifactSpec("upper_gasket", "upper_gasket"),
            RowCouponPhysicalArtifactSpec("lid_manifold_shell", "lid_manifold_shell"),
        ]
    )
    specs.extend(
        RowCouponPhysicalArtifactSpec(
            f"lid_harness_cover_{trunk['name']}",
            "lid_harness_cover",
        )
        for trunk in layout["lid_sensor_harness_trunks"]
    )
    specs.extend(
        RowCouponPhysicalArtifactSpec(
            _connector_key("printed_lid_sensor_connector_shroud", connector),
            "printed_lid_sensor_connector_shrouds",
        )
        for connector in layout["lid_service_connector_envelopes"]
    )
    specs.append(RowCouponPhysicalArtifactSpec("lid_cover", "lid_cover"))
    specs.extend(
        RowCouponPhysicalArtifactSpec(
            _mount_key("gas_pcb_interface_gasket", mount),
            "gas_pcb_interface_gaskets",
        )
        for mount in layout["gas_sensor_pcb_mounts"]
    )
    specs.extend(
        RowCouponPhysicalArtifactSpec(
            _mount_key("printed_gas_pcb_keeper_door", mount),
            "printed_gas_pcb_keeper_doors",
        )
        for mount in layout["gas_sensor_pcb_mounts"]
    )
    specs.append(
        RowCouponPhysicalArtifactSpec(
            "printed_sample_relief_cap",
            "printed_sample_relief_cap",
        )
    )
    specs.extend(
        RowCouponPhysicalArtifactSpec(_wedge_lock_key(index, lock_rect), "printed_wedge_locks")
        for index, lock_rect in enumerate(_wedge_lock_rectangles(layout, params), start=1)
    )
    return tuple(specs)


def row_coupon_physical_artifact_manifest(params: dict[str, Any]) -> dict[str, dict[str, str]]:
    installed = row_coupon_part_manifest()["installed"]
    return {
        spec.name: {**installed[spec.installed_part], "installed_part": spec.installed_part}
        for spec in row_coupon_physical_artifact_specs(params)
    }


def row_coupon_physical_artifact_print_policies(
    params: dict[str, Any],
    *,
    bed_x_mm: float,
    bed_y_mm: float,
    fits_rectangular_bed: Callable[
        [float, float, float, float],
        bool,
    ],
) -> tuple[RowCouponPhysicalArtifactPrintPolicy, ...]:
    manifest = row_coupon_physical_artifact_manifest(params)
    models = build_row_coupon_physical_artifacts(params)
    policies: list[RowCouponPhysicalArtifactPrintPolicy] = []
    for spec in row_coupon_physical_artifact_specs(params):
        entry = manifest[spec.name]
        bb = models[spec.name].val().BoundingBox()
        raw_target_x = float(bb.xlen)
        raw_target_y = float(bb.ylen)
        target_x = round(raw_target_x, 2)
        target_y = round(raw_target_y, 2)
        target_z = round(float(bb.zlen), 2)
        fabrication_source = entry["fabrication_source"]
        if fabrication_source != "printed_polymer":
            policy = "nonprinted_or_flexible"
            reason = f"{fabrication_source} is not a printed queue source"
        elif spec.name in ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS:
            policy = "structural_split_allowed"
            reason = (
                "canonical two-piece structural artifact with printed seam authority; "
                "release identity is independent of incidental bed fit"
            )
        elif fits_rectangular_bed(raw_target_x, raw_target_y, bed_x_mm, bed_y_mm):
            policy = "bed_fit_identity"
            reason = "canonical artifact fits the selected usable bed unchanged"
        elif spec.installed_part in ROW_COUPON_DISCRETE_UNSPLITTABLE_INSTALLED_PARTS:
            policy = "discrete_unsplittable"
            reason = "discrete/removable printed artifact must stay whole"
        else:
            policy = "canonical_redesign_required"
            reason = "oversized printed artifact needs a canonical redesign before printing"
        policies.append(
            RowCouponPhysicalArtifactPrintPolicy(
                name=spec.name,
                installed_part=spec.installed_part,
                policy=policy,
                target_x_mm=target_x,
                target_y_mm=target_y,
                target_z_mm=target_z,
                reason=reason,
            )
        )
    return tuple(policies)


def _deck_pod_models(
    params: dict[str, Any],
) -> dict[str, cq.Workplane]:
    layout = row_coupon_layout(params)
    deck = params["deck_interface"]
    models: dict[str, cq.Workplane] = {}
    for tile in layout["tile_origins"]:
        x, y, _, _ = _deck_slot_opening_for_tile(tile, params)
        clearance = deck["slot_shoe_clearance_xy"]
        shoe = _rounded_box(
            deck["slot_opening_length_x"] - 2 * clearance,
            deck["slot_opening_width_y"] - 2 * clearance,
            deck["slot_shoe_thickness_z"],
            deck["slot_shoe_corner_radius"],
        ).translate((x + clearance, y + clearance, layout["deck_plane_z"]))
        pod = _add_deck_engagement_feet(shoe, tile=tile, params=params)
        models[_tile_key("deck_pod", tile)] = _add_pod_frame_keys(pod, tile=tile, params=params)
    return models


def _ir_face_gasket_models(
    params: dict[str, Any],
    *,
    assembly_position: bool,
) -> dict[str, cq.Workplane]:
    layout = row_coupon_layout(params)
    models: dict[str, cq.Workplane] = {}
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
        models[_tile_key("ir_thermopile_face_gasket", mount)] = body.cut(aperture)
    return models


def _lid_harness_cover_models(
    params: dict[str, Any],
    *,
    assembly_position: bool,
) -> dict[str, cq.Workplane]:
    layout = row_coupon_layout(params)
    all_rects = [*layout["lid_sensor_harness_trunks"]]
    for route in layout["lid_sensor_harness_routes"]:
        all_rects.append(route["branch_rect"])
        all_rects.append(route["strain_relief_rect"])
    z_shift = _harness_z_shift(all_rects, assembly_position=assembly_position)

    # Service relief bodies are authored in installed coordinates and moved by
    # the same transform as the cover.  Building each part in its own print
    # coordinates here would destroy their relative Z datum.
    from .parts.gas_pcb import build_gas_sensor_pcbs
    from .parts.harness import (
        build_lid_sensor_service_connectors,
        build_printed_lid_sensor_connector_shrouds,
    )

    cover_side_reliefs = (
        build_gas_sensor_pcbs(params, assembly_position=True),
        build_lid_sensor_service_connectors(params, assembly_position=True),
        build_printed_lid_sensor_connector_shrouds(params, assembly_position=True),
    )
    relief_clearance = float(params["sensor_harness"]["channel_clearance_xy"])
    carrier_clearance = float(params["sensor_mounts"]["sht41_carrier_clearance_xy"])
    carrier_min_x = min(float(mount["x"]) for mount in layout["headspace_sht41_mounts"])
    underside_reliefs = (
        cq.Workplane("XY")
        .box(
            float(layout["length_x"]) - (carrier_min_x - carrier_clearance),
            float(layout["width_y"]),
            20.0,
            centered=(False, False, False),
        )
        .translate((carrier_min_x - carrier_clearance, 0.0, 20.0)),
    )

    models: dict[str, cq.Workplane] = {}
    for trunk in layout["lid_sensor_harness_trunks"]:
        rects = [trunk]
        for route in layout["lid_sensor_harness_routes"]:
            if route["trunk_name"] == trunk["name"]:
                rects.append(route["branch_rect"])
                rects.append(route["strain_relief_rect"])
        underside = trunk["owner_part"] == "lid_manifold_shell"
        cover = _harness_cover_from_rectangles(
            rects,
            params=params,
            underside=underside,
            z_shift=z_shift,
        )
        owner = (
            build_lid_manifold_shell(params, assembly_position=True)
            if underside
            else build_lid_cover(params, assembly_position=True)
        ).translate((0, 0, z_shift))
        # Canonical covers occupy only the routed channel void.  This prevents
        # exported service parts from containing owner material that would need
        # destructive cleanup at assembly.
        cover = _cut_with_axis_clearance(cover, owner, clearance=0.15)
        for relief in underside_reliefs if underside else cover_side_reliefs:
            cover = _cut_with_axis_clearance(
                cover,
                cq.Workplane(obj=relief.val().copy()).translate((0, 0, z_shift)),
                clearance=0.0 if underside else relief_clearance,
            )
        # Reassert the exact owner last.  OCCT can retain coincident slivers
        # when the translated clearance copies are fused into one compound;
        # the final exact cut is the installed no-interpenetration authority.
        exact_owner = (
            build_lid_manifold_shell(params, assembly_position=True)
            if underside
            else build_lid_cover(params, assembly_position=True)
        ).translate((0, 0, z_shift))
        cover = cover.cut(exact_owner)
        if not underside:
            # Cover-side routes cross the cover/shell tongue seam.  The shell
            # is a second rigid neighbor, not the route owner, and therefore
            # needs its own installed-datum service clearance.
            shell_neighbor = build_lid_manifold_shell(
                params,
                assembly_position=True,
            ).translate((0, 0, z_shift))
            cover = cover.cut(shell_neighbor)
        cover = _remove_named_lid_harness_fragments(
            cover,
            trunk_name=trunk["name"],
            assembly_position=assembly_position,
        )
        models[f"lid_harness_cover_{trunk['name']}"] = cover
    return models


def _cut_with_axis_clearance(
    model: cq.Workplane,
    cutter: cq.Workplane,
    *,
    clearance: float,
) -> cq.Workplane:
    """Cut a service body plus a bounded six-axis assembly clearance."""
    expanded = cq.Workplane(obj=cutter.val().copy())
    for delta in (
        (clearance, 0.0, 0.0),
        (-clearance, 0.0, 0.0),
        (0.0, clearance, 0.0),
        (0.0, -clearance, 0.0),
        (0.0, 0.0, clearance),
        (0.0, 0.0, -clearance),
    ):
        expanded = expanded.union(
            cq.Workplane(obj=cutter.val().copy()).translate(delta)
        )
    return model.cut(expanded)


def _remove_named_lid_harness_fragments(
    cover: cq.Workplane,
    *,
    trunk_name: str,
    assembly_position: bool,
) -> cq.Workplane:
    """Remove only the two exact, source-known owner-subtraction remnants."""
    # These exact XY/volume fingerprints are the disconnected remnants created
    # where the shell/service clearances clip a cover branch or end.  Rejecting
    # by fingerprint prevents a future unrelated small feature from silently
    # inheriting cleanup authority.
    known_fragments = {
        "lid_cover_left_gas_bus": ((3.5, 7.6, 49.9, 53.85), 2.12175),
        "lid_cover_right_gas_bus": (
            (145.3, 147.5, 375.25, 375.75),
            0.286,
        ),
    }
    expected = known_fragments.get(trunk_name)
    retained = []
    rejected = []
    before_volume = float(cover.val().Volume())
    for solid in cover.val().Solids():
        volume = float(solid.Volume())
        if volume >= 5.0:
            retained.append(solid)
            continue
        bb = solid.BoundingBox()
        observed = (
            float(bb.xmin),
            float(bb.xmax),
            float(bb.ymin),
            float(bb.ymax),
            float(bb.zmin),
            float(bb.zmax),
        )
        if (
            expected is None
            or any(
                abs(actual - target) > 0.06
                for actual, target in zip(observed[:4], expected[0], strict=True)
            )
            or abs((observed[5] - observed[4]) - 0.7) > 0.06
            or abs(volume - expected[1]) > 0.08
        ):
            raise ValueError(
                f"lid harness cover {trunk_name} has an unknown small solid: "
                f"volume={volume:.6f}, xyz_bounds={observed!r}"
            )
        rejected.append(solid)

    expected_count = 1 if expected is not None else 0
    if len(rejected) != expected_count:
        raise ValueError(
            f"lid harness cover {trunk_name} expected {expected_count} named "
            f"fragment rejection(s), observed {len(rejected)}"
        )
    if not retained:
        raise ValueError(f"lid harness cover {trunk_name} contains no retained body")

    rejected_volume = sum(float(solid.Volume()) for solid in rejected)
    result = cq.Workplane(obj=cq.Compound.makeCompound(retained))
    after_volume = float(result.val().Volume())
    if abs((before_volume - after_volume) - rejected_volume) > 1e-6:
        raise ValueError(
            f"lid harness cover {trunk_name} cleanup volume accounting failed: "
            f"before={before_volume:.6f}, after={after_volume:.6f}, "
            f"rejected={rejected_volume:.6f} mm^3"
        )
    return result


def _printed_lid_shroud_models(
    params: dict[str, Any],
    *,
    assembly_position: bool,
) -> dict[str, cq.Workplane]:
    layout = row_coupon_layout(params)
    connectors = layout["lid_service_connector_envelopes"]
    z_shift = _harness_z_shift(connectors, assembly_position=assembly_position)
    owner = build_lid_cover(params, assembly_position=assembly_position)
    return {
        _connector_key("printed_lid_sensor_connector_shroud", connector): (
            _build_printed_sensor_connector_shrouds(
                [connector],
                z_shift=z_shift,
                **_shroud_grip_rib_kwargs(params),
            ).cut(owner)
        )
        for connector in connectors
    }


def _gas_pcb_interface_gasket_models(
    params: dict[str, Any],
    *,
    assembly_position: bool,
) -> dict[str, cq.Workplane]:
    layout = row_coupon_layout(params)
    z_shift = 0.0 if assembly_position else -layout["lid_top_z"]
    models: dict[str, cq.Workplane] = {}
    for mount in layout["gas_sensor_pcb_mounts"]:
        interface = mount["gas_interface"]
        gasket = _boxes_from_rectangles([interface["gasket_rect"]], z_shift=z_shift)
        models[_mount_key("gas_pcb_interface_gasket", mount)] = (
            _cut_rectangular_gas_interface_window(
                gasket,
                interface["gasket_window_rect"],
                z_shift=z_shift,
            )
        )
    return models


def _keeper_door_models(
    params: dict[str, Any],
    *,
    assembly_position: bool,
) -> dict[str, cq.Workplane]:
    layout = row_coupon_layout(params)
    return {
        _mount_key("printed_gas_pcb_keeper_door", mount): _keeper_door_body(
            mount,
            layout,
            params,
            assembly_position=assembly_position,
        )
        for mount in layout["gas_sensor_pcb_mounts"]
    }


def _wedge_lock_models(
    params: dict[str, Any],
    *,
    assembly_position: bool,
) -> dict[str, cq.Workplane]:
    layout = row_coupon_layout(params)
    lid = params["lid_manifold"]
    z0 = layout["lid_top_z"] + lid["duct_height_z"] if assembly_position else 0.0
    return {
        _wedge_lock_key(index, lock_rect): _build_wedge_lock_body(lock_rect, params=params, z0=z0)
        for index, lock_rect in enumerate(_wedge_lock_rectangles(layout, params), start=1)
    }


def build_row_coupon_physical_artifacts(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> dict[str, cq.Workplane]:
    models: dict[str, cq.Workplane] = {}
    models.update(_deck_pod_models(params))
    models["plate_support_frame"] = build_plate_support_frame(params)
    models.update(_ir_face_gasket_models(params, assembly_position=assembly_position))
    models["lower_harness_cover"] = build_lower_harness_cover(
        params,
        assembly_position=assembly_position,
    )
    models["printed_lower_sensor_connector_shroud"] = (
        build_printed_lower_sensor_connector_shroud(
            params,
            assembly_position=assembly_position,
        )
    )
    models["lower_gasket"] = build_lower_gasket(params, assembly_position=assembly_position)
    models["wet_chamber_frame"] = build_wet_chamber_frame(
        params,
        assembly_position=assembly_position,
    )
    models["upper_gasket"] = build_upper_gasket(params, assembly_position=assembly_position)
    models["lid_manifold_shell"] = build_lid_manifold_shell(
        params,
        assembly_position=assembly_position,
    )
    models.update(_lid_harness_cover_models(params, assembly_position=assembly_position))
    models.update(_printed_lid_shroud_models(params, assembly_position=assembly_position))
    models["lid_cover"] = build_lid_cover(params, assembly_position=assembly_position)
    models.update(_gas_pcb_interface_gasket_models(params, assembly_position=assembly_position))
    models.update(_keeper_door_models(params, assembly_position=assembly_position))
    models["printed_sample_relief_cap"] = build_printed_sample_relief_cap(
        params,
        assembly_position=assembly_position,
    )
    models.update(_wedge_lock_models(params, assembly_position=assembly_position))

    ordered_specs = row_coupon_physical_artifact_specs(params)
    if set(models) != {spec.name for spec in ordered_specs}:
        missing = sorted({spec.name for spec in ordered_specs} - set(models))
        extra = sorted(set(models) - {spec.name for spec in ordered_specs})
        raise ValueError(f"artifact model/spec mismatch: missing={missing}, extra={extra}")
    return {spec.name: models[spec.name] for spec in ordered_specs}


def group_row_coupon_physical_artifacts_by_installed_part(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> dict[str, cq.Workplane]:
    artifacts = build_row_coupon_physical_artifacts(
        params,
        assembly_position=assembly_position,
    )
    grouped_models: dict[str, list[cq.Workplane]] = {}
    for spec in row_coupon_physical_artifact_specs(params):
        grouped_models.setdefault(spec.installed_part, []).append(artifacts[spec.name])

    grouped: dict[str, cq.Workplane] = {}
    for installed_part, models in grouped_models.items():
        if len(models) == 1:
            grouped[installed_part] = models[0]
            continue
        solids = [solid for model in models for solid in model.val().Solids()]
        grouped[installed_part] = cq.Workplane(
            obj=cq.Compound.makeCompound(solids)
        )
    return grouped
