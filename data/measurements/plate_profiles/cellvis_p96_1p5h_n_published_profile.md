# CellVis P96-1.5H-N Published Profile

Status: reference data
Plate: CellVis P96-1.5H-N

## Published Dimensions

| Item | Value mm |
|---|---:|
| Plate length X | 127.60 |
| Plate width Y | 85.75 |
| Plate height Z | 14.30 |
| Coverslip thickness | 0.170 |
| Coverslip thickness tolerance | 0.005 |
| Bottom height | 1.73 |
| Bottom height tolerance | 0.05 |
| Upper well diameter | 6.80 |
| Lower well diameter | 6.21 |
| Well bottom area equivalent diameter | 6.18 |
| Diagram internal depth | 11.93 |
| Plate top to cell plane depth | 12.40 |
| Well top recess depth | 0.47 |
| A1 center X | 14.38 |
| A1 center Y | 11.24 |
| Pitch | 9.00 |

## Not in this profile

`cad/one_row_coupon.params.json` sits under a `plate` block whose `profile_source`
points here, so anything in that block is read as published. Three values in it are
CAD-modelling choices, NOT published dimensions: `sidewall_thickness`,
`cell_plane_check_thickness_z`, and the observation-window rectangle
(`observation_window_length_x` / `observation_window_width_y`, 88.0 x 52.0 — provenance
not stated anywhere in the repo; it needs a caliper).

A fourth, `bottom_window_thickness_z` (0.6), was **removed on 2026-09-21**. It had been
extruded as an 88 x 52 mm glass slab across the observation window at the plate underside
and added to the optical standoff, but this profile closes exactly without it:

    bottom_height_z 1.73 + coverslip_thickness_z 0.17 = 1.90
    height_z 14.30 - plate_top_to_cell_plane_depth_z 12.40 = 1.90

A 0.6 mm window overshoots the published cell plane by exactly 0.60 mm. The plate's glass
is the #1.5H coverslip and nothing else; below it the observation window is open air. See
`docs/engineering/decision_log.md` (2026-09-21) and `docs/engineering/observer_optical_bench.md`.

## Use

This file is the published plate-profile source for the one-row coupon's COTS
microplate footprint, well-grid offsets, well opening diameters, and first-build
well-top geometry. Physical plate measurements should update or qualify these
values only when fit, seal, imaging, or pipette-access evidence contradicts the
published profile.
