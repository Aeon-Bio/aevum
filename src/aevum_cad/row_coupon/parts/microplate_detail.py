"""Display-grade microplate models for the Print Kit viewer's consumable switch.

``build_microplates`` (structural.py) stays the authority proxy that interference and
validation checks run against. The models here draw the same plates in more detail and
must agree with that proxy on footprint, height and cell plane
(tests/test_row_coupon_microplate_detail.py).

96-well: CellVis P96-1.5H-N, from the published profile
(data/measurements/plate_profiles/cellvis_p96_1p5h_n_published_profile.md). Published and
used here: footprint, height, A1 offset, 9.00 mm pitch, the tapered well (lower 6.21 ->
upper 6.80 mm diameter over the 11.93 mm internal depth), the 0.47 mm well-top recess, the
1.73 mm bottom height and the 0.17 mm #1.5H coverslip, whose top is the cell plane at 1.90
mm. Not published, so modelling choices: the 1.5 mm perimeter wall (``sidewall_thickness``,
shared with the proxy), a solid web between wells, and a coverslip spanning the whole plate
interior. Below the coverslip is open air inside the perimeter skirt.

384-well: no product profile is in the repo, so only what the ANSI/SLAS standards fix is
drawn, and the viewer shows it as a ghost marked "profile pending": the SLAS 1-2004
footprint (127.76 x 85.48 mm), the SLAS 2-2004 height (14.35 mm), and the SLAS 4-2004 well
positions (A1 at 12.13 / 8.99 mm, 4.5 mm pitch, 16 x 24), as rings on the plate top.
"""

from __future__ import annotations

import math
from typing import Any

import cadquery as cq
import numpy as np

from ..layout import row_coupon_layout
from ._geom_base import _perimeter_rails
from ._shared_tile import _well_centers_for_tile

SLAS_FOOTPRINT_X_MM = 127.76  # ANSI/SLAS 1-2004
SLAS_FOOTPRINT_Y_MM = 85.48  # ANSI/SLAS 1-2004
SLAS_HEIGHT_MM = 14.35  # ANSI/SLAS 2-2004
SLAS_384_A1_X_MM = 12.13  # ANSI/SLAS 4-2004
SLAS_384_A1_Y_MM = 8.99  # ANSI/SLAS 4-2004
SLAS_384_PITCH_MM = 4.5  # ANSI/SLAS 4-2004
SLAS_384_ROWS, SLAS_384_COLUMNS = 16, 24
SLAS_384_RING_DIAMETER_MM = 3.3  # marker only; the well size is product-specific


def cell_plane_height(params: dict[str, Any]) -> float:
    """Cell plane above the plate underside: bottom height plus coverslip."""
    plate = params["plate"]
    return float(plate["bottom_height_z"]) + float(plate["coverslip_thickness_z"])


def build_microplates_96_detailed(params: dict[str, Any]) -> cq.Workplane:
    """Every tile's CellVis P96-1.5H-N with individual tapered wells, in assembly position."""
    layout = row_coupon_layout(params)
    plate = params["plate"]
    z0 = float(layout["plate_bottom_z"])
    wall = float(plate["sidewall_thickness"])
    length, width, height = (
        float(plate["length_x"]),
        float(plate["width_y"]),
        float(plate["height_z"]),
    )
    cell_z = cell_plane_height(params)
    well_top_z = height - float(plate["well_top_recess_depth_z"])
    depth = well_top_z - cell_z
    if not math.isclose(depth, float(plate["diagram_internal_depth_z"]), abs_tol=1e-6):
        raise ValueError(
            f"published profile does not close: well top {well_top_z} - cell plane {cell_z} "
            f"= {depth}, internal depth is {plate['diagram_internal_depth_z']}"
        )
    r_low = float(plate["lower_well_diameter"]) / 2
    r_up = float(plate["upper_well_diameter"]) / 2

    plates: cq.Workplane | None = None
    for tile in layout["tile_origins"]:
        x0, y0 = float(tile["x"]), float(tile["y"])
        frame = _perimeter_rails(
            x0=x0, y0=y0, length=length, width=width, rail_width=wall, height=height, z0=z0
        )
        interior = (length - 2 * wall, width - 2 * wall)
        web = (
            cq.Workplane("XY")
            .box(*interior, depth, centered=False)
            .translate((x0 + wall, y0 + wall, z0 + cell_z))
        )
        bores = cq.Workplane("XY").add(
            cq.Compound.makeCompound(
                [
                    cq.Solid.makeCone(
                        r_low, r_up, depth, cq.Vector(x, y, z0 + cell_z), cq.Vector(0, 0, 1)
                    )
                    for x, y in _well_centers_for_tile(tile, params)
                ]
            )
        )
        coverslip = (
            cq.Workplane("XY")
            .box(*interior, float(plate["coverslip_thickness_z"]), centered=False)
            .translate((x0 + wall, y0 + wall, z0 + float(plate["bottom_height_z"])))
        )
        part = frame.union(web.cut(bores)).union(coverslip)
        plates = part if plates is None else plates.union(part)
    if plates is None:
        raise ValueError("row coupon requires at least one microplate")
    return plates


def slas_384_footprints(params: dict[str, Any]) -> cq.Workplane:
    """SLAS footprint boxes, centred on each tile's plate, for the 384-well placeholder."""
    layout = row_coupon_layout(params)
    plate = params["plate"]
    z0 = float(layout["plate_bottom_z"])
    boxes = None
    for tile in layout["tile_origins"]:
        cx = float(tile["x"]) + float(plate["length_x"]) / 2
        cy = float(tile["y"]) + float(plate["width_y"]) / 2
        box = (
            cq.Workplane("XY")
            .box(
                SLAS_FOOTPRINT_X_MM,
                SLAS_FOOTPRINT_Y_MM,
                SLAS_HEIGHT_MM,
                centered=(True, True, False),
            )
            .translate((cx, cy, z0))
        )
        boxes = box if boxes is None else boxes.union(box)
    return boxes


def slas_384_well_rings(params: dict[str, Any], segments: int = 20) -> np.ndarray:
    """Line segments (n, 2, 3) marking the SLAS 4-2004 384-well centres on each plate top."""
    layout = row_coupon_layout(params)
    plate = params["plate"]
    z = float(layout["plate_bottom_z"]) + SLAS_HEIGHT_MM
    r = SLAS_384_RING_DIAMETER_MM / 2
    t = np.linspace(0.0, 2 * np.pi, segments + 1)
    ring = np.stack([r * np.cos(t), r * np.sin(t)], axis=1)
    out = []
    for tile in layout["tile_origins"]:
        # SLAS offsets are from the footprint corner; the footprint is centred on the plate.
        ox = float(tile["x"]) + (float(plate["length_x"]) - SLAS_FOOTPRINT_X_MM) / 2
        oy = float(tile["y"]) + (float(plate["width_y"]) - SLAS_FOOTPRINT_Y_MM) / 2
        for row in range(SLAS_384_ROWS):
            for col in range(SLAS_384_COLUMNS):
                cx = ox + SLAS_384_A1_X_MM + col * SLAS_384_PITCH_MM
                cy = oy + SLAS_384_A1_Y_MM + row * SLAS_384_PITCH_MM
                pts = np.column_stack([ring[:, 0] + cx, ring[:, 1] + cy, np.full(len(ring), z)])
                out.extend(np.stack([pts[:-1], pts[1:]], axis=1))
    return np.asarray(out)
