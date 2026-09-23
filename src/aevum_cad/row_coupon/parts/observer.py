from __future__ import annotations
from typing import Any
import cadquery as cq
from ..layout import (row_coupon_layout)
from ._geom_base import (_bodies_from_shape_targets, _boxes_from_rectangles, _harness_z_shift, _rectangles_overlap_xy)


def _cut_observer_fiducials(
    model: cq.Workplane,
    *,
    x0: float,
    y0: float,
    plate_len: float,
    plate_wid: float,
    bay: dict[str, Any],
) -> cq.Workplane:
    diameter = bay["observer_fiducial_diameter"]
    depth = bay["observer_fiducial_depth"]
    offset = bay["observer_fiducial_offset"]
    aperture_x = x0 + (plate_len - bay["aperture_length_x"]) / 2
    aperture_y = y0 + (plate_wid - bay["aperture_width_y"]) / 2
    x_values = [
        aperture_x - offset,
        aperture_x + bay["aperture_length_x"] + offset,
    ]
    y_values = [
        aperture_y - offset,
        aperture_y + bay["aperture_width_y"] + offset,
    ]

    for x in x_values:
        for y in y_values:
            model = model.cut(
                cq.Workplane("XY")
                .circle(diameter / 2)
                .extrude(depth + 0.05)
                .translate((x, y, -0.01))
            )
    return model


def _dry_bay_containment(
    rect: dict[str, Any],
    dry_bay_envelope: dict[str, Any],
) -> tuple[dict[str, float], bool]:
    """Two-sided dry-bay containment of a reserved-volume rect on X/Y/Z.

    Single source for "does this observer body fit the dry bay" -- used by the
    front-end swept body and the static carriage box. overflow = how far the rect
    overhangs either side of the bay on each axis; fits = no axis overhangs beyond
    the fit tolerance. The dry bay names Z as bottom_z/top_z, not z/height_z.
    """
    from aevum_cad.row_coupon import (_TRAVERSE_FIT_TOLERANCE_MM)
    db_x0 = float(dry_bay_envelope["x"])
    db_x1 = db_x0 + float(dry_bay_envelope["length_x"])
    db_y0 = float(dry_bay_envelope["y"])
    db_y1 = db_y0 + float(dry_bay_envelope["width_y"])
    db_z0 = float(dry_bay_envelope["bottom_z"])
    db_z1 = float(dry_bay_envelope["top_z"])
    bx0 = float(rect["x"])
    bx1 = bx0 + float(rect["length_x"])
    by0 = float(rect["y"])
    by1 = by0 + float(rect["width_y"])
    bz0 = float(rect["z"])
    bz1 = bz0 + float(rect["height_z"])
    overflow = {
        "x": max(0.0, db_x0 - bx0) + max(0.0, bx1 - db_x1),
        "y": max(0.0, db_y0 - by0) + max(0.0, by1 - db_y1),
        "z": max(0.0, db_z0 - bz0) + max(0.0, bz1 - db_z1),
    }
    fits = all(o <= _TRAVERSE_FIT_TOLERANCE_MM for o in overflow.values())
    return {k: round(v, 3) for k, v in overflow.items()}, fits


def _observer_body_rect(rect: dict[str, Any], *, name: str, role: str) -> dict[str, Any]:
    return {
        "name": name,
        "role": role,
        "x": rect["x"],
        "y": rect["y"],
        "z": rect["z"],
        "length_x": rect["length_x"],
        "width_y": rect["width_y"],
        "height_z": rect["height_z"],
    }


def _observer_box_cad_value(rect: dict[str, Any]) -> str:
    return (
        f"{float(rect['length_x']):.2f} x "
        f"{float(rect['width_y']):.2f} x "
        f"{float(rect['height_z']):.2f} mm"
    )


def _observer_carriage_envelope_check(
    rect: dict[str, Any],
    *,
    dry_bay_envelope: dict[str, Any],
    carriage_traverse: dict[str, Any],
) -> dict[str, Any]:
    body_rect = _observer_body_rect(
        rect,
        name="observer_carriage_reserved_volume",
        role="dry observer carriage reserved volume",
    )
    # Gate the STATIC carriage box's own dry-bay containment -- same class as the
    # front-end-body gate. Without this an oversized carriage box overflows the bay
    # while only the swept-truck traverse is checked. The box is parked at the row
    # end, so at live params it fits; this catches a bad reserved dimension.
    box_overflow, box_fits_dry_bay = _dry_bay_containment(rect, dry_bay_envelope)
    return {
        **rect,
        "name": "observer_carriage_envelope_check",
        "role": "dry_observer_carriage_reserved_volume_validation_body",
        "validation": "required_gate6_observer_carriage_envelope_evidence",
        "failure_rule": (
            "carriage_intrusion_or_unmeasured_reserved_volume_blocks_observer_readiness"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": _observer_box_cad_value(rect),
        "carriage_traverse": carriage_traverse,
        "traverse_fits_dry_bay": carriage_traverse["fits_dry_bay"],
        "carriage_box_fits_dry_bay": box_fits_dry_bay,
        "carriage_box_overflow_mm": box_overflow,
        "dry_bay_bounds_mm": {
            "x": round(float(dry_bay_envelope["length_x"]), 2),
            "y": round(float(dry_bay_envelope["width_y"]), 2),
            "z": round(
                float(dry_bay_envelope["top_z"])
                - float(dry_bay_envelope["bottom_z"]),
                2,
            ),
        },
        "source_layout_checks": [
            "dry_bay_envelope_check",
            "observer_front_end_swept_body_check",
            "observer_kinematic_split_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "observer_carriage_clearance",
            "observer_carriage_traverse_clearance",
            "observer_kinematic_split",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": [body_rect],
    }


def _observer_carriage_traverse(
    *,
    row_axis: str,
    well_xs: list[float],
    well_ys: list[float],
    gantry_truck_traverse_extent: float,
    front_end_length_x: float,
    front_end_width_y: float,
    front_end_scan_axis_footprint: float,
    swept_z: float,
    swept_height_z: float,
    dry_bay_envelope: dict[str, Any],
    deck_feet: list[dict[str, Any]],
    adjacent_keepouts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Sweep the continuously-traversing observer structure across the whole row.

    The head that images every well must traverse the full row. Modeled today
    only as a static carriage box at the plate-1 end, it had no swept-volume
    check while every other observer body did. This computes the swept extent on
    BOTH axes so the geometry is surfaced as data rather than hidden.

    Traverse axis -- the resolution of the 44.6 mm overflow the earlier model
    flagged: the gantry beam that traverses the row must be THIN on the traverse
    axis (`gantry_truck_traverse_extent`, ~13 mm), not the 58 mm `carriage_width_y`
    the reserved carriage box allotted. Everything that rides the row in the
    traverse direction -- beam, head, rails -- has to fit inside that ~13 mm; the
    58 mm cross-section was an over-reservation. At 13 mm it clears the 347.9 mm
    dry-bay Y by ~0.4 mm; a truck wider than ~13.4 mm overflows again.

    Scan axis -- where the earlier Y fix RELOCATED its burden, surfaced here so it
    is not hidden: the head scans the columns, so the scan-axis swept extent is
    the well span (99 mm) plus the head's scan-axis footprint
    (`front_end_scan_axis_footprint`). After the 99 mm well span the dry-bay X
    leaves only ~0.2 mm of budget -- barely the bare objective barrel. The
    placeholder value (21 mm) is the objective alone and EXCLUDES the post-fold
    camera arm (tube lens + sensor). There is NO room to route that arm along X
    (the prior "place the bulk along the ~120 mm beam X-length" claim was wrong:
    the residual after the well span is ~0.2 mm, not 120 mm) -- the camera must be
    folded coaxially over the objective or taken offboard. If a measured
    scan-axis footprint exceeds the objective by more than ~0.2 mm, this reports
    an X overflow and the traverse blocks again, now on X.

    This proves only that the thin-truck TOPOLOGY fits geometrically, and only
    against PLACEHOLDER head footprints (21/13 mm, camera arm excluded) -- the
    real footprints, the achievable beam width, and the camera-routing strategy
    are Stage-0/Stage-3 caliper work. Whether a ~13 mm beam can physically carry
    the head and traverse 334.5 mm repeatably inside the bench's hold-still spec
    stays Gate-6 blocked. Reports a swept bounding box plus per-keepout intrusion
    (deck feet, adjacent OT-2 slots) using the same overlap machinery the
    front-end body uses.
    """
    from aevum_cad.row_coupon import (_RAZOR_THIN_MARGIN_WARN_MM, _TRAVERSE_FIT_TOLERANCE_MM)
    truck = float(gantry_truck_traverse_extent)
    # Scan-axis span = the head footprint along the scan axis. It must be at least
    # the bare body extent on that axis (the camera arm only adds, never subtracts):
    # tying it to the body length closes a decoupling bug where an oversized body
    # (`front_end_length_x`) overflows the bay while the traverse, reading only the
    # smaller scan-footprint param, still reports "fits".
    if row_axis == "y":
        scan = max(float(front_end_scan_axis_footprint), float(front_end_length_x))
        span_x = scan  # scan axis (X): head footprint incl. camera arm, >= body X
        span_y = max(truck, float(front_end_width_y))  # traverse axis (Y)
    else:
        scan = max(float(front_end_scan_axis_footprint), float(front_end_width_y))
        span_x = max(truck, float(front_end_length_x))  # traverse axis (X)
        span_y = scan  # scan axis (Y): head footprint incl. camera arm, >= body Y
    # Compute the fit decision from UNROUNDED extents so a sub-micron overflow
    # cannot be absorbed by display rounding before the subtraction; round only
    # for the reported rect/overflow fields.
    raw_length_x = max(well_xs) - min(well_xs) + span_x
    raw_width_y = max(well_ys) - min(well_ys) + span_y
    swept_x = round(min(well_xs) - span_x / 2, 3)
    swept_y = round(min(well_ys) - span_y / 2, 3)
    swept_length_x = round(raw_length_x, 3)
    swept_width_y = round(raw_width_y, 3)
    # The traverse overflow is 2D (X/Y) and swept-length-based (extent vs bay span),
    # NOT absolute placement: Z containment and absolute-placement containment of the
    # head are owned by the front-end-body check (`_dry_bay_containment`), which the
    # OC-A2 scan-span tie keeps consistent with this. Do not assume the two agree in
    # the sub-mm margin band -- they answer different questions by design.
    raw_overflow_x = max(0.0, raw_length_x - float(dry_bay_envelope["length_x"]))
    raw_overflow_y = max(0.0, raw_width_y - float(dry_bay_envelope["width_y"]))
    swept_rect = {
        "x": swept_x,
        "y": swept_y,
        "length_x": swept_length_x,
        "width_y": swept_width_y,
    }
    foot_hits = sum(
        1 for foot in deck_feet if _rectangles_overlap_xy(swept_rect, foot)
    )
    adjacent_hits = sum(
        1
        for keepout in adjacent_keepouts
        if _rectangles_overlap_xy(swept_rect, keepout)
    )
    # Decide fit on the unrounded overflow with an explicit tolerance; round only
    # for display so a sub-micron overflow can never silently read as a fit.
    fits_dry_bay = (
        raw_overflow_x <= _TRAVERSE_FIT_TOLERANCE_MM
        and raw_overflow_y <= _TRAVERSE_FIT_TOLERANCE_MM
    )
    clears_traverse = fits_dry_bay and foot_hits == 0 and adjacent_hits == 0
    # Both axes' fit margins -- surfaced because both are razor-thin: the traverse
    # turns on the truck staying thin (~0.4 mm), the scan axis on the head's
    # footprint staying near the bare objective (~0.2 mm, no room for the camera arm).
    traverse_margin = (
        float(dry_bay_envelope["width_y"]) - raw_width_y
        if row_axis == "y"
        else float(dry_bay_envelope["length_x"]) - raw_length_x
    )
    scan_margin = (
        float(dry_bay_envelope["length_x"]) - raw_length_x
        if row_axis == "y"
        else float(dry_bay_envelope["width_y"]) - raw_width_y
    )
    # OC-A15 (comment corrected against live geometry): the binding SCAN-axis wall is
    # whichever is tightest of (a) the standoff-leg corridor -- the clear gap between the
    # 80 mm deck-engagement legs that straddle the scan axis -- and (b) the milled dry-bay
    # wall. Both span the head's Z sweep, so a footprint wider than the tighter wall
    # strikes it.
    #
    # The two are NOT nearly co-located, and the legs are NOT symmetric about the well
    # array. `lower_service_foot_inset_x` (3.0) walks one tile-4 foot inboard, so the live
    # corridor is X 17.10..134.50 = 117.4 mm while the well centres run 24.88..123.88.
    # Near slack is 7.78 mm, far slack 10.62 mm: the NEAR (low-X) leg binds, and the head
    # budget is 2 x 7.78 = 15.56 mm, not (corridor - 99.0 mm span). An earlier version of
    # this comment claimed legs at 13.6/134.0 with the bay hi-wall ~0.1 mm inside them;
    # that described geometry the model no longer has.
    #
    # We surface the corridor, the per-wall bay clearance, and the binding minimum of the
    # two; the razor-thin flag tracks the binding wall, not just the corridor.
    scan_lo, scan_hi = (
        (swept_x, swept_x + swept_length_x)
        if row_axis == "y"
        else (swept_y, swept_y + swept_width_y)
    )
    scan_mid = (scan_lo + scan_hi) / 2.0

    def _foot_near(f: dict[str, Any]) -> float:
        return float(f["x"]) if row_axis == "y" else float(f["y"])

    def _foot_far(f: dict[str, Any]) -> float:
        return (
            float(f["x"]) + float(f["length_x"])
            if row_axis == "y"
            else float(f["y"]) + float(f["width_y"])
        )

    # A foot whose BODY spans the scan centerline blocks the head outright (robustness
    # guard -- never triggers for the live symmetric corner-leg layout, but a centered
    # structural rib must not read as a one-sided wall).
    straddling = [f for f in deck_feet if _foot_near(f) < scan_mid < _foot_far(f)]
    left_legs = [_foot_far(f) for f in deck_feet if _foot_far(f) <= scan_mid]
    right_legs = [_foot_near(f) for f in deck_feet if _foot_near(f) >= scan_mid]
    if straddling:
        scan_corridor_width = 0.0
        scan_corridor_margin = round(min(scan_lo - scan_mid, scan_mid - scan_hi), 3)
    elif left_legs and right_legs:
        corridor_lo, corridor_hi = max(left_legs), min(right_legs)
        scan_corridor_width = round(corridor_hi - corridor_lo, 3)
        scan_corridor_margin = round(min(scan_lo - corridor_lo, corridor_hi - scan_hi), 3)
    else:
        # No deck legs in scope (synthetic call): corridor unknown.
        scan_corridor_width = None
        scan_corridor_margin = None

    # Per-wall dry-bay scan clearance (min of the two walls), the OTHER real wall.
    # .get for x/y so synthetic unit calls (which pass only length_x/width_y) still work.
    if row_axis == "y":
        bay_origin = float(dry_bay_envelope.get("x", 0.0))
        bay_scan_lo, bay_scan_hi = bay_origin, bay_origin + float(dry_bay_envelope["length_x"])
    else:
        bay_origin = float(dry_bay_envelope.get("y", 0.0))
        bay_scan_lo, bay_scan_hi = bay_origin, bay_origin + float(dry_bay_envelope["width_y"])
    scan_bay_per_wall_margin = round(min(scan_lo - bay_scan_lo, bay_scan_hi - scan_hi), 3)
    # Binding scan margin = the tightest of the leg corridor and the per-wall bay wall.
    binding_candidates = [scan_bay_per_wall_margin]
    if scan_corridor_margin is not None:
        binding_candidates.append(scan_corridor_margin)
    effective_scan_margin = min(binding_candidates)
    # The traverse sweeps the MOVING HEAD's Z extent (the front-end swept body,
    # ~40 mm), NOT the static carriage box's 62 mm -- the head, not the parked carrier,
    # is what rides the row. Z containment / absolute placement is owned by the
    # front-end-body check (`_dry_bay_containment`); this is surfaced for consistency.
    z_within_dry_bay = (
        swept_z >= float(dry_bay_envelope["bottom_z"]) - _TRAVERSE_FIT_TOLERANCE_MM
        and swept_z + swept_height_z
        <= float(dry_bay_envelope["top_z"]) + _TRAVERSE_FIT_TOLERANCE_MM
    )
    return {
        "traverse_axis": row_axis,
        "x": swept_x,
        "y": swept_y,
        "z": round(float(swept_z), 3),
        "length_x": swept_length_x,
        "width_y": swept_width_y,
        "height_z": round(float(swept_height_z), 3),
        "z_within_dry_bay": z_within_dry_bay,
        "traverse_structure": "thin_gantry_truck",
        "gantry_truck_traverse_extent_mm": round(truck, 3),
        "traverse_axis_fit_margin_mm": round(traverse_margin, 3),
        # OC-A12: a positive-but-tiny margin still fits, but a sub-mm param drift would
        # tip it into overflow -- surface the razor-thinness so it can't erode silently.
        "traverse_margin_is_razor_thin": (
            0.0 <= traverse_margin <= _RAZOR_THIN_MARGIN_WARN_MM
        ),
        "scan_axis_footprint_mm": round(float(front_end_scan_axis_footprint), 3),
        "scan_axis_extent_mm": round(scan, 3),
        "scan_axis_fit_margin_mm": round(scan_margin, 3),
        # OC-A15: surface BOTH real scan walls (leg corridor + per-wall bay) and the
        # binding minimum. The bay hi-wall is actually the tightest here (~0.02 mm),
        # marginally inside the leg corridor (~0.12 mm); the razor-thin flag tracks the
        # binding minimum, not just the corridor.
        "scan_corridor_width_mm": scan_corridor_width,
        "scan_corridor_margin_mm": scan_corridor_margin,
        "scan_bay_per_wall_margin_mm": scan_bay_per_wall_margin,
        "scan_binding_margin_mm": round(effective_scan_margin, 3),
        "scan_margin_is_razor_thin": (
            0.0 <= effective_scan_margin <= _RAZOR_THIN_MARGIN_WARN_MM
        ),
        "razor_thin_margin_warn_threshold_mm": _RAZOR_THIN_MARGIN_WARN_MM,
        "scan_axis_footprint_excludes_camera_arm": True,
        "scan_axis_extent_is_head_inclusive": True,
        "dry_bay_overflow_x_mm": round(raw_overflow_x, 3),
        "dry_bay_overflow_y_mm": round(raw_overflow_y, 3),
        "fits_dry_bay": fits_dry_bay,
        "deck_foot_collision_count": foot_hits,
        "hits_deck_feet": foot_hits > 0,
        "adjacent_slot_collision_count": adjacent_hits,
        "enters_adjacent_slot": adjacent_hits > 0,
        "clears_traverse": clears_traverse,
    }


def _observer_fiducial_focus_target_check(
    observer_fiducial_focus_targets: list[dict[str, Any]],
    *,
    aperture_count: int,
    dry_bay_envelope: dict[str, Any],
) -> dict[str, Any]:
    from aevum_cad.row_coupon import (_TRAVERSE_FIT_TOLERANCE_MM, _target_kind_counts)
    counts = _target_kind_counts(observer_fiducial_focus_targets, "target_kind")
    # OC-A6: the check used to be count-only. Make it falsifiable on two invariants:
    # (1) MULTIPLICITY -- every aperture (plate position) carries exactly its pattern:
    # 4 corner fiducial disks + one each of the four focus/keepout marks; a missing or
    # duplicated mark breaks the per-aperture multiple. (2) CONTAINMENT -- every target
    # sits inside the dry-bay envelope, so a registration mark can't fall outside the
    # imageable volume.
    fiducials_per_aperture = 4
    _per_aperture_singletons = (
        "bottom_recess_focus_target",
        "objective_keepout_disk",
        "horizontal_focus_crosshair",
        "vertical_focus_crosshair",
    )
    fiducial_multiplicity_ok = (
        aperture_count > 0
        and counts.get("observer_fiducial_disk", 0)
        == aperture_count * fiducials_per_aperture
        and all(counts.get(k, 0) == aperture_count for k in _per_aperture_singletons)
    )
    tol = _TRAVERSE_FIT_TOLERANCE_MM
    db_x0 = float(dry_bay_envelope["x"])
    db_x1 = db_x0 + float(dry_bay_envelope["length_x"])
    db_y0 = float(dry_bay_envelope["y"])
    db_y1 = db_y0 + float(dry_bay_envelope["width_y"])
    db_z0 = float(dry_bay_envelope["bottom_z"])
    db_z1 = float(dry_bay_envelope["top_z"])

    def _within(t: dict[str, Any]) -> bool:
        # Targets are a mix: disk marks carry {center x, y, diameter}; rect marks carry
        # {corner x, y, length_x, width_y}. Containment must account for the disk RADIUS
        # (a Ø32 keepout disk centered near a bay edge overhangs ~16 mm) and the Z band
        # (a target with z outside the bay depth is not imageable), not treat marks as
        # zero-extent points.
        if "diameter" in t:
            r = float(t["diameter"]) / 2.0
            x_lo, x_hi = float(t["x"]) - r, float(t["x"]) + r
            y_lo, y_hi = float(t["y"]) - r, float(t["y"]) + r
        else:
            x_lo = float(t["x"])
            x_hi = x_lo + float(t.get("length_x", 0.0))
            y_lo = float(t["y"])
            y_hi = y_lo + float(t.get("width_y", 0.0))
        tz = float(t.get("z", 0.0))
        return (
            x_lo >= db_x0 - tol
            and x_hi <= db_x1 + tol
            and y_lo >= db_y0 - tol
            and y_hi <= db_y1 + tol
            and db_z0 - tol <= tz <= db_z1 + tol
        )

    all_targets_within_dry_bay = all(
        _within(t) for t in observer_fiducial_focus_targets
    )
    fiducial_geometry_blockers: list[str] = []
    if not fiducial_multiplicity_ok:
        fiducial_geometry_blockers.append("fiducial_pattern_multiplicity_mismatch")
    if not all_targets_within_dry_bay:
        fiducial_geometry_blockers.append("fiducial_target_outside_dry_bay")
    return {
        "name": "observer_fiducial_focus_target_check",
        "role": "observer_fiducial_focus_pattern_validation_body",
        "validation": "required_gate6_observer_fiducial_focus_evidence",
        "failure_rule": (
            "unverified_fiducial_visibility_or_focus_targets_block_observer_readiness"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{aperture_count} apertures / {len(observer_fiducial_focus_targets)} "
            f"targets / {counts.get('observer_fiducial_disk', 0)} fiducials"
        ),
        "aperture_count": aperture_count,
        "target_count": len(observer_fiducial_focus_targets),
        "target_kind_counts": counts,
        "fiducials_per_aperture": fiducials_per_aperture,
        "fiducial_multiplicity_ok": fiducial_multiplicity_ok,
        "all_targets_within_dry_bay": all_targets_within_dry_bay,
        "fiducial_geometry_blockers": sorted(fiducial_geometry_blockers),
        "fiducial_geometry_clears": not fiducial_geometry_blockers,
        "source_layout_checks": ["observer_fiducial_focus_targets"],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "observer_focus_repeatability",
            "observer_fiducial_visibility",
            "usable_imaging_quality",
        ],
        "body_targets": observer_fiducial_focus_targets,
    }


def _observer_fiducial_focus_target_rectangles(
    *,
    apertures: list[dict[str, float | int]],
    params: dict[str, Any],
) -> list[dict[str, float | int | str]]:
    bay = params["dry_bay"]
    recess_extra = float(bay["bottom_recess_extra"])
    recess_depth = float(bay["bottom_recess_depth"])
    objective_d = float(bay["objective_keepout_diameter"])
    crosshair_len = float(bay["crosshair_length"])
    crosshair_w = float(bay["crosshair_width"])
    fiducial_d = float(bay["observer_fiducial_diameter"])
    fiducial_offset = float(bay["observer_fiducial_offset"])

    targets: list[dict[str, float | int | str]] = []
    for aperture in apertures:
        aperture_x = float(aperture["x"])
        aperture_y = float(aperture["y"])
        aperture_len = float(aperture["length_x"])
        aperture_wid = float(aperture["width_y"])
        center_x = aperture_x + aperture_len / 2
        center_y = aperture_y + aperture_wid / 2
        tile_index = int(aperture["tile_index"])

        targets.extend(
            [
                {
                    "tile_index": tile_index,
                    "target_kind": "bottom_recess_focus_target",
                    "x": round(center_x - (aperture_len + recess_extra) / 2, 3),
                    "y": round(center_y - (aperture_wid + recess_extra) / 2, 3),
                    "z": 0.0,
                    "length_x": round(aperture_len + recess_extra, 3),
                    "width_y": round(aperture_wid + recess_extra, 3),
                    "height_z": round(recess_depth, 3),
                },
                {
                    "tile_index": tile_index,
                    "target_kind": "objective_keepout_disk",
                    "x": round(center_x, 3),
                    "y": round(center_y, 3),
                    "z": 0.0,
                    "diameter": round(objective_d, 3),
                    "height_z": round(recess_depth, 3),
                },
                {
                    "tile_index": tile_index,
                    "target_kind": "horizontal_focus_crosshair",
                    "x": round(center_x - crosshair_len / 2, 3),
                    "y": round(center_y - crosshair_w / 2, 3),
                    "z": 0.0,
                    "length_x": round(crosshair_len, 3),
                    "width_y": round(crosshair_w, 3),
                    "height_z": round(recess_depth, 3),
                },
                {
                    "tile_index": tile_index,
                    "target_kind": "vertical_focus_crosshair",
                    "x": round(center_x - crosshair_w / 2, 3),
                    "y": round(center_y - crosshair_len / 2, 3),
                    "z": 0.0,
                    "length_x": round(crosshair_w, 3),
                    "width_y": round(crosshair_len, 3),
                    "height_z": round(recess_depth, 3),
                },
            ]
        )
        for x in (
            aperture_x - fiducial_offset,
            aperture_x + aperture_len + fiducial_offset,
        ):
            for y in (
                aperture_y - fiducial_offset,
                aperture_y + aperture_wid + fiducial_offset,
            ):
                targets.append(
                    {
                        "tile_index": tile_index,
                        "target_kind": "observer_fiducial_disk",
                        "x": round(x, 3),
                        "y": round(y, 3),
                        "z": 0.0,
                        "diameter": round(fiducial_d, 3),
                        "height_z": round(recess_depth, 3),
                    }
                )
    return targets


def _observer_front_end_swept_body_check(
    rect: dict[str, Any],
    *,
    dry_bay_envelope: dict[str, Any],
    covered_well_count: int,
    front_end_length_x: float,
    front_end_width_y: float,
    front_end_height_z: float,
    front_end_focus_stroke_z: float,
    front_end_top_clearance_z: float,
    front_end_service_margin_z: float,
    front_end_barrel_diameter: float,
    scan_corridor_footprint_max: float,
    objective_keepout_diameter: float,
    carriage_height_z: float,
) -> dict[str, Any]:
    from aevum_cad.row_coupon import (_TRAVERSE_FIT_TOLERANCE_MM)
    body_rect = _observer_body_rect(
        rect,
        name="observer_front_end_swept_body",
        role="compact dry observer front-end swept volume",
    )
    # Falsifiable closure checks against independent params (not the well-derived
    # swept body, which is tautological by construction). The head body + its
    # focus travel + plate standoff + service margin must fit the carriage
    # vertical envelope. The footprint value is the CIRCUMSCRIBED diameter of the
    # rectangular head cross-section (a conservative upper bound), not a measured
    # round-barrel diameter -- it stands in for the doc's "barrel Ø <= keepout"
    # gate until Stage 0 measures the real barrel. When the real (possibly larger)
    # head bbox lands, split this into barrel-Ø-vs-keepout and head-bbox-vs-dry-bay.
    footprint_circumscribed_diameter = round(
        (front_end_length_x ** 2 + front_end_width_y ** 2) ** 0.5,
        3,
    )
    vertical_budget_required = round(
        front_end_top_clearance_z
        + front_end_height_z
        + front_end_focus_stroke_z
        + front_end_service_margin_z,
        3,
    )
    # Gate the swept body's own containment in the dry bay. Previously this was
    # enforced only by a layout-level test; encoding it on the check makes it a
    # first-class blocker, so an oversized front-end body (e.g. a larger measured
    # `front_end_length_x`) reports an overflow here instead of silently passing.
    body_overflow, body_fits_dry_bay = _dry_bay_containment(rect, dry_bay_envelope)
    return {
        **rect,
        "name": "observer_front_end_swept_body_check",
        "role": "compact_dry_observer_front_end_swept_volume_validation_body",
        "validation": "required_gate6_observer_front_end_swept_body_evidence",
        "failure_rule": (
            "front_end_collision_or_unmeasured_sweep_blocks_observer_readiness"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": _observer_box_cad_value(rect),
        "covered_well_count": covered_well_count,
        "front_end_footprint_circumscribed_diameter_mm": (
            footprint_circumscribed_diameter
        ),
        "objective_keepout_diameter_mm": round(float(objective_keepout_diameter), 3),
        "front_end_fits_objective_keepout": (
            footprint_circumscribed_diameter <= float(objective_keepout_diameter)
        ),
        # OC-A9: split the conflated check. The circumscribed diameter above is a
        # CONSERVATIVE bound on the whole head cross-section (incl. the camera arm);
        # the real per-well keepout is about the round objective BARREL, an
        # independent measured param. The barrel is the authoritative keepout gate;
        # the head bounding box is gated against the dry bay by front_end_body_fits_dry_bay.
        "front_end_barrel_diameter_mm": round(float(front_end_barrel_diameter), 3),
        "front_end_barrel_fits_keepout": (
            float(front_end_barrel_diameter) <= float(objective_keepout_diameter)
        ),
        # OC-A15 (diagnostic, surfaced not gated): a round barrel cannot fit a head
        # narrower than its diameter, and the plate-level traverse sweep is set by the
        # WIDER of (head footprint, barrel). With the current placeholders the Ø25
        # barrel exceeds the 13 mm head width -> this is FALSE, flagging that the
        # razor-thin traverse margin (built on the 13 mm footprint) does not account
        # for a realistic objective barrel. Resolution is measurement-gated (Stage-0)
        # / a design decision; see decision_log.md. Surfaced, not in the fit chain, so
        # it does not autonomously overturn the dry-bay "fits" conclusion.
        "front_end_barrel_within_head_footprint": (
            float(front_end_barrel_diameter)
            <= min(float(front_end_length_x), float(front_end_width_y))
            + _TRAVERSE_FIT_TOLERANCE_MM
        ),
        # OC-A15 (diagnostic, surfaced not gated): does the DECLARED barrel thread the
        # scan-axis corridor? The traverse fit chain reads the placeholder scan footprint
        # (not the barrel), so it ships green; this mirrors the SMIS dock gate
        # (scan_corridor_footprint_max) on the SAME number so CAD and SMIS cannot silently
        # disagree about a real Ø-barrel head. Currently FALSE (Ø25 > 21.2).
        "scan_corridor_footprint_max_mm": round(float(scan_corridor_footprint_max), 3),
        "barrel_threads_scan_corridor": (
            float(front_end_barrel_diameter)
            <= float(scan_corridor_footprint_max) + _TRAVERSE_FIT_TOLERANCE_MM
        ),
        "vertical_budget_required_mm": vertical_budget_required,
        "carriage_height_budget_mm": round(float(carriage_height_z), 3),
        "front_end_vertical_budget_closes": (
            vertical_budget_required <= float(carriage_height_z)
        ),
        "front_end_body_fits_dry_bay": body_fits_dry_bay,
        "front_end_body_overflow_mm": body_overflow,
        "dry_bay_bounds_mm": {
            "x": round(float(dry_bay_envelope["length_x"]), 2),
            "y": round(float(dry_bay_envelope["width_y"]), 2),
            "z": round(
                float(dry_bay_envelope["top_z"])
                - float(dry_bay_envelope["bottom_z"]),
                2,
            ),
        },
        "source_layout_checks": [
            "dry_bay_envelope_check",
            "observer_fiducial_focus_target_check",
            "observer_kinematic_split_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "observer_front_end_clearance",
            "all_well_observer_access",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": [body_rect],
    }


def _observer_infinity_port_datum_check(
    front_end_check: dict[str, Any],
    *,
    pd0_offset_from_objective_shoulder_z: float,
    clear_aperture_diameter: float,
    cage_standard_mm: float,
    rms_thread_present: bool,
    c_mount_present: bool,
    tube_lens_to_sensor_mm: float,
    objective_keepout_diameter: float,
) -> dict[str, Any]:
    """SM-2.1: make the SMIS infinity-port optical datum falsifiable in CAD."""

    top_z = float(front_end_check["z"]) + float(front_end_check["height_z"])
    pd0_z = round(top_z - float(pd0_offset_from_objective_shoulder_z), 3)
    datum_thickness = 0.5
    rect = {
        "x": front_end_check["x"],
        "y": front_end_check["y"],
        "z": pd0_z - datum_thickness / 2.0,
        "length_x": front_end_check["length_x"],
        "width_y": front_end_check["width_y"],
        "height_z": datum_thickness,
    }
    body_rect = _observer_body_rect(
        rect,
        name="observer_infinity_port_pd0_datum",
        role="SMIS infinity-port PD-0 swept datum plane",
    )
    pd0_within_front_end_z = float(front_end_check["z"]) <= pd0_z <= top_z
    clear_aperture_fits_keepout = (
        float(clear_aperture_diameter) <= float(objective_keepout_diameter)
    )
    clear_aperture_fits_cage = float(clear_aperture_diameter) <= float(cage_standard_mm)
    tube_lens_spacing_frozen = float(tube_lens_to_sensor_mm) == 50.0
    optical_standard_complete = bool(rms_thread_present and c_mount_present)

    blockers: list[str] = []
    if not pd0_within_front_end_z:
        blockers.append("pd0_datum_outside_front_end_z")
    if not clear_aperture_fits_keepout:
        blockers.append("infinity_port_aperture_exceeds_objective_keepout")
    if not clear_aperture_fits_cage:
        blockers.append("infinity_port_aperture_exceeds_cage_standard")
    if not optical_standard_complete:
        blockers.append("infinity_port_missing_rms_or_c_mount")
    if not tube_lens_spacing_frozen:
        blockers.append("tube_lens_to_sensor_spacing_drift")

    return {
        **rect,
        "name": "observer_infinity_port_datum_check",
        "role": "SMIS_infinity_port_PD0_datum_validation_body",
        "validation": "required_gate6_observer_infinity_port_datum_evidence",
        "failure_rule": (
            "missing_or_unmeasured_infinity_port_datum_blocks_SMIS_level1_swap"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": _observer_box_cad_value(rect),
        "pd0_offset_from_objective_shoulder_z_mm": round(
            float(pd0_offset_from_objective_shoulder_z),
            3,
        ),
        "pd0_z_mm": pd0_z,
        "pd0_within_front_end_z": pd0_within_front_end_z,
        "clear_aperture_diameter_mm": round(float(clear_aperture_diameter), 3),
        "objective_keepout_diameter_mm": round(float(objective_keepout_diameter), 3),
        "clear_aperture_fits_keepout": clear_aperture_fits_keepout,
        "cage_standard_mm": round(float(cage_standard_mm), 3),
        "clear_aperture_fits_cage_standard": clear_aperture_fits_cage,
        "rms_thread_present": bool(rms_thread_present),
        "c_mount_present": bool(c_mount_present),
        "optical_standard_complete": optical_standard_complete,
        "tube_lens_to_sensor_mm": round(float(tube_lens_to_sensor_mm), 3),
        "tube_lens_to_sensor_spacing_frozen": tube_lens_spacing_frozen,
        "infinity_port_geometry_clears": not blockers,
        "infinity_port_geometry_blockers": sorted(blockers),
        "source_layout_checks": [
            "observer_front_end_swept_body_check",
            "observer_optical_stability_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "SMIS_level1_backend_swap",
            "parfocal_infinity_port_registration",
            "fluorescence_dichroic_backend_install",
        ],
        "body_rects": [body_rect],
    }


def _observer_kinematic_split_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    observer_front_end_swept_body_check: dict[str, Any],
    observer_carriage_envelope_check: dict[str, Any],
    observer_service_raceway_envelope_check: dict[str, Any],
    dry_bay_envelope: dict[str, Any],
    observer_fiducial_focus_targets: list[dict[str, float | int | str]],
) -> dict[str, Any]:
    metrology = params.get("consumable_metrology", {})
    check_params = params.get("observer_kinematic_split_check", {})
    slab_len = float(check_params.get("length_x", 58.0))
    slab_wid = float(check_params.get("width_y", 78.0))
    slab_h = float(check_params.get("height_z", 0.45))
    x0 = (
        float(layout["length_x"])
        + float(metrology.get("viewer_offset_x", 18.0))
        + float(check_params.get("viewer_offset_x", 214.0))
    )
    y0 = (float(layout["width_y"]) - slab_wid) / 2

    source_validation_checks = [
        "observer_front_end_swept_body_check",
        "observer_carriage_envelope_check",
        "observer_service_raceway_envelope_check",
        "observer_fiducial_focus_target_check",
        "dry_bay_envelope_check",
    ]
    checkpoints = [
        {
            "name": "front_end_decoupled_from_carriage",
            "blocks": ["single_large_objective_centered_carriage_unacceptable"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_carriage_envelope_check",
            ],
            "inspection_method": "observer_split_layout_review",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "focus_axis_reaches_all_plate_positions",
            "blocks": ["focus_axis_travel_or_recovery_unproven"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_fiducial_focus_target_check",
            ],
            "inspection_method": "all_tile_focus_travel_check",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "carriage_stays_out_of_objective_centered_sweep",
            "blocks": ["carriage_treated_as_objective_centered_body"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_carriage_envelope_check",
            ],
            "inspection_method": "dry_bay_carriage_offset_review",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "service_loop_recovers_inside_raceway",
            "blocks": ["observer_service_loop_recovery_unproven"],
            "source_validation_checks": [
                "observer_service_raceway_envelope_check",
                "dry_bay_envelope_check",
            ],
            "inspection_method": "five_cycle_service_loop_recovery",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "install_remove_preserves_dry_bay_clearance",
            "blocks": ["observer_install_remove_snag_or_debris_unchecked"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_service_raceway_envelope_check",
                "dry_bay_envelope_check",
            ],
            "inspection_method": "post_cycle_dry_bay_clearance_inspection",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
    ]
    blocker_set = {
        block
        for checkpoint in checkpoints
        for block in checkpoint["blocks"]
    }
    carriage_traverse = observer_carriage_envelope_check.get("carriage_traverse", {})
    # Fail closed: absent traverse evidence must not silently read as a clear
    # path for a Gate-6 blocker.
    carriage_traverse_fits = bool(carriage_traverse.get("fits_dry_bay", False))
    carriage_traverse_clears = bool(carriage_traverse.get("clears_traverse", False))
    if not carriage_traverse_fits:
        # The carriage swept across the full row overflows the reserved dry-bay
        # envelope; until the gantry is physically built and shown to traverse,
        # this blocks Gate 6.
        blocker_set.add("carriage_traverse_exceeds_dry_bay")
    if carriage_traverse.get("hits_deck_feet", False):
        blocker_set.add("carriage_traverse_hits_deck_feet")
    if carriage_traverse.get("enters_adjacent_slot", False):
        blocker_set.add("carriage_traverse_enters_adjacent_slot")
    blockers = sorted(blocker_set)
    return {
        "name": "observer_kinematic_split_check",
        "role": "validation-only observer kinematic split evidence checklist",
        "validation": "required_gate6_observer_kinematic_split_evidence",
        "failure_rule": (
            "unproven_front_end_carriage_or_service_split_blocks_observer_readiness"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{len(checkpoints)} checks / 3 split envelopes / "
            f"{len(observer_fiducial_focus_targets)} targets"
        ),
        "checkpoint_count": len(checkpoints),
        "source_validation_checks": source_validation_checks,
        "blockers": blockers,
        "carriage_traverse_fits_dry_bay": carriage_traverse_fits,
        "carriage_traverse_clears": carriage_traverse_clears,
        "carriage_traverse_overflow_mm": {
            "x": round(float(carriage_traverse.get("dry_bay_overflow_x_mm", 0.0)), 2),
            "y": round(float(carriage_traverse.get("dry_bay_overflow_y_mm", 0.0)), 2),
        },
        "carriage_traverse_collisions": {
            "deck_feet": int(carriage_traverse.get("deck_foot_collision_count", 0)),
            "adjacent_slots": int(
                carriage_traverse.get("adjacent_slot_collision_count", 0)
            ),
        },
        "front_end_bounds_mm": {
            "x": round(float(observer_front_end_swept_body_check["length_x"]), 2),
            "y": round(float(observer_front_end_swept_body_check["width_y"]), 2),
            "z": round(float(observer_front_end_swept_body_check["height_z"]), 2),
        },
        "carriage_bounds_mm": {
            "x": round(float(observer_carriage_envelope_check["length_x"]), 2),
            "y": round(float(observer_carriage_envelope_check["width_y"]), 2),
            "z": round(float(observer_carriage_envelope_check["height_z"]), 2),
        },
        "raceway_bounds_mm": {
            "x": round(float(observer_service_raceway_envelope_check["length_x"]), 2),
            "y": round(float(observer_service_raceway_envelope_check["width_y"]), 2),
            "z": round(float(observer_service_raceway_envelope_check["height_z"]), 2),
        },
        "dry_bay_bounds_mm": {
            "x": round(float(dry_bay_envelope["length_x"]), 2),
            "y": round(float(dry_bay_envelope["width_y"]), 2),
            "z": round(
                float(dry_bay_envelope["top_z"])
                - float(dry_bay_envelope["bottom_z"]),
                2,
            ),
        },
        "requires_physical_evidence": True,
        "all_checkpoints_block_gate6_pass": True,
        "physical_claims_blocked": [
            "observer_kinematic_split",
            "objective_centered_access",
            "focus_axis_recovery",
            "service_loop_recovery",
            "observer_install_remove_clearance",
        ],
        "body_rects": [
            {
                "name": "observer_kinematic_split_evidence_slab",
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": 0.0,
                "length_x": round(slab_len, 3),
                "width_y": round(slab_wid, 3),
                "height_z": round(slab_h, 3),
            }
        ],
    }


def _observer_optical_stability_check(
    layout: dict[str, Any],
    *,
    params: dict[str, Any],
    dry_bay_apertures: list[dict[str, float | int]],
    observer_fiducial_focus_target_check: dict[str, Any],
    thermal_condensation_proxy_check: dict[str, Any],
    dry_bay_ingress_audit_rects: list[dict[str, Any]],
    wet_dry_failure_paths: dict[str, list[dict[str, float | int | str]]],
) -> dict[str, Any]:
    metrology = params.get("consumable_metrology", {})
    check_params = params.get("observer_optical_stability_check", {})
    slab_len = float(check_params.get("length_x", 56.0))
    slab_wid = float(check_params.get("width_y", 72.0))
    slab_h = float(check_params.get("height_z", 0.45))
    x0 = (
        float(layout["length_x"])
        + float(metrology.get("viewer_offset_x", 18.0))
        + float(check_params.get("viewer_offset_x", 132.0))
    )
    y0 = (float(layout["width_y"]) - slab_wid) / 2

    target_kind_counts = observer_fiducial_focus_target_check["target_kind_counts"]
    proxy_kind_counts = thermal_condensation_proxy_check["proxy_kind_counts"]

    checkpoints = [
        {
            "name": "stray_light_blank_frame",
            "blocks": ["stray_light_background_unmeasured"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "dry_bay_ingress_audit_check",
            ],
            "inspection_method": "blank_frame_capture",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "baffle_reflection_screen",
            "blocks": ["baffle_reflection_screen_missing"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_carriage_envelope_check",
            ],
            "inspection_method": "dark_and_illuminated_field_photo",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "fiducial_visibility",
            "blocks": ["fiducial_visibility_unproven"],
            "source_validation_checks": ["observer_fiducial_focus_target_check"],
            "inspection_method": "fiducial_target_image_set",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "focus_repeatability",
            "blocks": ["focus_repeatability_unmeasured"],
            "source_validation_checks": ["observer_fiducial_focus_target_check"],
            "inspection_method": "repeat_focus_series",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "vibration_stability",
            "blocks": ["vibration_motion_blur_unmeasured"],
            "source_validation_checks": [
                "observer_front_end_swept_body_check",
                "observer_carriage_envelope_check",
            ],
            "inspection_method": "service_motion_image_series",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "thermal_drift",
            "blocks": ["thermal_drift_unmeasured"],
            "source_validation_checks": ["thermal_condensation_proxy_check"],
            "inspection_method": "warm_humid_focus_drift_log",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "signal_quality_baseline",
            "blocks": ["signal_quality_baseline_missing"],
            "source_validation_checks": [
                "observer_fiducial_focus_target_check",
                "thermal_condensation_proxy_check",
            ],
            "inspection_method": "baseline_noise_and_contrast_capture",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
        {
            "name": "wet_boundary_optical_contamination",
            "blocks": ["wet_boundary_optical_contamination_unchecked"],
            "source_validation_checks": [
                "wet_dry_failure_path_check",
                "dry_bay_ingress_audit_check",
            ],
            "inspection_method": "post_warm_humid_dry_bay_inspection",
            "evidence_gate": "Gate 6 sensor/thermal",
        },
    ]
    source_validation_checks = sorted(
        {
            source
            for checkpoint in checkpoints
            for source in checkpoint["source_validation_checks"]
        }
    )
    blockers = sorted(
        {
            block
            for checkpoint in checkpoints
            for block in checkpoint["blocks"]
        }
    )

    return {
        "name": "observer_optical_stability_check",
        "role": "measured_observer_optical_performance_evidence_blocker",
        "validation": "cad_proxy_measured_observer_performance_required",
        "failure_rule": (
            "any_unproven_optical_checkpoint_blocks_observer_performance_claim"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": (
            f"{len(checkpoints)} checks / {len(dry_bay_apertures)} apertures / "
            f"{observer_fiducial_focus_target_check['target_count']} targets"
        ),
        "aperture_count": len(dry_bay_apertures),
        "fiducial_focus_target_count": observer_fiducial_focus_target_check[
            "target_count"
        ],
        "target_kind_counts": target_kind_counts,
        "thermal_proxy_count": thermal_condensation_proxy_check["target_count"],
        "thermal_proxy_kind_counts": proxy_kind_counts,
        "dry_bay_ingress_audit_rect_count": len(dry_bay_ingress_audit_rects),
        "wet_dry_witness_gutter_count": len(
            wet_dry_failure_paths["wet_dry_witness_gutters"]
        ),
        "checkpoints": checkpoints,
        "checkpoint_count": len(checkpoints),
        "blockers": blockers,
        "source_validation_checks": source_validation_checks,
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "usable_imaging_quality",
            "raman_signal_quality",
            "biophotonics_signal_quality",
            "focus_repeatability",
            "vibration_stability",
        ],
        "body_rects": [
            {
                "name": "observer_optical_stability_evidence_slab",
                "x": round(x0, 3),
                "y": round(y0, 3),
                "z": 0.0,
                "length_x": round(slab_len, 3),
                "width_y": round(slab_wid, 3),
                "height_z": round(slab_h, 3),
            }
        ],
    }


def _observer_service_raceway_envelope_check(
    rect: dict[str, Any],
    *,
    dry_bay_envelope: dict[str, Any],
    service_bend_radius: float,
) -> dict[str, Any]:
    from aevum_cad.row_coupon import (_TRAVERSE_FIT_TOLERANCE_MM)
    body_rect = _observer_body_rect(
        rect,
        name="observer_service_raceway_envelope",
        role="dry observer service loop raceway volume",
    )
    # OC-A3: falsifiable raceway asserts (the check had none). The raceway is a
    # service volume that must (a) sit OUTSIDE the optical sweep -- no XY overlap with
    # the dry-bay envelope, or a flexing cable would foul the moving optics; (b) fit
    # the bay depth in Z; (c) reserve enough Z for the cable-chain loop, whose height
    # is ~2x the bend radius (an R10 chain loops to ~20 mm; the raceway reserves 24 mm).
    raceway_clears_dry_bay_sweep = not _rectangles_overlap_xy(rect, dry_bay_envelope)
    raceway_z_within_bay_depth = (
        float(rect["z"]) >= float(dry_bay_envelope["bottom_z"]) - _TRAVERSE_FIT_TOLERANCE_MM
        and float(rect["z"]) + float(rect["height_z"])
        <= float(dry_bay_envelope["top_z"]) + _TRAVERSE_FIT_TOLERANCE_MM
    )
    loop_height = 2.0 * float(service_bend_radius)
    r10_loop_margin = round(float(rect["height_z"]) - loop_height, 3)
    r10_loop_fits_raceway_z = loop_height <= float(rect["height_z"]) + _TRAVERSE_FIT_TOLERANCE_MM
    raceway_blockers: list[str] = []
    if not raceway_clears_dry_bay_sweep:
        raceway_blockers.append("raceway_intrudes_optical_sweep")
    if not raceway_z_within_bay_depth:
        raceway_blockers.append("raceway_exceeds_bay_depth")
    if not r10_loop_fits_raceway_z:
        raceway_blockers.append("cable_loop_exceeds_raceway_z")
    return {
        **rect,
        "name": "observer_service_raceway_envelope_check",
        "role": "dry_observer_service_loop_raceway_validation_body",
        "validation": "required_gate6_observer_service_raceway_evidence",
        "failure_rule": (
            "service_loop_snag_or_unmeasured_raceway_blocks_observer_readiness"
        ),
        "evidence_gate": "Gate 6 sensor/thermal",
        "cad_value": _observer_box_cad_value(rect),
        "raceway_clears_dry_bay_sweep": raceway_clears_dry_bay_sweep,
        "raceway_z_within_bay_depth": raceway_z_within_bay_depth,
        "r10_loop_height_margin_mm": r10_loop_margin,
        "r10_loop_fits_raceway_z": r10_loop_fits_raceway_z,
        "raceway_geometry_blockers": sorted(raceway_blockers),
        "raceway_geometry_clears": not raceway_blockers,
        "dry_bay_bounds_mm": {
            "x": round(float(dry_bay_envelope["length_x"]), 2),
            "y": round(float(dry_bay_envelope["width_y"]), 2),
            "z": round(
                float(dry_bay_envelope["top_z"])
                - float(dry_bay_envelope["bottom_z"]),
                2,
            ),
        },
        "source_layout_checks": [
            "dry_bay_envelope_check",
            "observer_carriage_envelope_check",
            "observer_kinematic_split_check",
        ],
        "requires_physical_evidence": True,
        "physical_claims_blocked": [
            "observer_service_loop_recovery",
            "dry_bay_clearance_with_observer_services",
            "powered_sensor_thermal_readiness",
        ],
        "body_rects": [body_rect],
    }


def build_observer_carriage_envelope_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["observer_carriage_envelope_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -float(rects[0]["z"])
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_fiducial_focus_target_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    targets = layout["observer_fiducial_focus_target_check"]["body_targets"]
    z_shift = _harness_z_shift(targets, assembly_position=assembly_position)
    return _bodies_from_shape_targets(targets, z_shift=z_shift)


def build_observer_front_end_swept_body_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["observer_front_end_swept_body_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -float(rects[0]["z"])
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_infinity_port_datum_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["observer_infinity_port_datum_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -float(rects[0]["z"])
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_kinematic_split_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["observer_kinematic_split_check"]
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("observer kinematic split check requires rectangles")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_optical_stability_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    spec = layout["observer_optical_stability_check"]
    rects = spec["body_rects"]
    if not rects:
        raise ValueError("observer optical stability check requires rectangles")
    z_shift = 0.0 if assembly_position else -min(float(rect["z"]) for rect in rects)
    return _boxes_from_rectangles(rects, z_shift=z_shift)


def build_observer_service_raceway_envelope_check(
    params: dict[str, Any],
    *,
    assembly_position: bool = False,
) -> cq.Workplane:
    layout = row_coupon_layout(params)
    rects = layout["observer_service_raceway_envelope_check"]["body_rects"]
    z_shift = 0.0 if assembly_position else -float(rects[0]["z"])
    return _boxes_from_rectangles(rects, z_shift=z_shift)
