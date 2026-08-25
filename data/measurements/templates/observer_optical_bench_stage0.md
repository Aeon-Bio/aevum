# Observer Optical Bench Stage 0

Protocol:
`docs/protocols/observer_optical_bench_stage0.md`

## Session Identity

| Field | Value |
|---|---|
| Date |  |
| Operator |  |
| Bench build identifier |  |
| Objective (4x / 10x) |  |
| Camera |  |
| Plate identifier |  |
| Media / cells |  |
| Measurement images folder |  |

## Pre-Run Checks

| Check | Result | Evidence / notes |
|---|---|---|
| Head, cradle, and source share one breadboard datum | not_tested |  |
| Plate seated skirt-only, nothing under any well | not_tested |  |
| Plate leveled to < 0.1 deg, settled ~15 min, posts not hand-held | not_tested |  |
| Illumination arm mounted, source 30-80 mm above plate top | not_tested |  |
| Tube-lens-to-sensor spacing set to 50 mm | not_tested |  |
| Objective parfocal class recorded (4x WD ~22 mm / 10x WD ~8 mm) | not_tested |  |

## Phase A - Dry, No Plate (USAF in air)

| Measurement | Value / observation | Result | Notes |
|---|---|---|---|
| Smallest resolved USAF 1951 group / element |  | not_tested | pass = ~Group 7 Element 1 at 4x / NA 0.10 |
| Raw working distance (front element to target), calipers |  | not_tested |  |
| Rig alignment verdict |  | not_tested | fail here = misalignment, not the plate |

## Phase B - Dry Through Real Plate, No Cells (5-well tilt map)

| Well position | Focus-Z | WD_real (front element to coverslip) | Resolved feature (50 um grid) | Focus delta vs center (tilt) | Result | Notes |
|---|---|---|---|---|---|---|
| Center |  |  |  | (datum) | not_tested |  |
| Corner +X +Y |  |  |  |  | not_tested |  |
| Corner -X +Y |  |  |  |  | not_tested |  |
| Corner +X -Y |  |  |  |  | not_tested |  |
| Corner -X -Y |  |  |  |  | not_tested |  |

## Phase C - Wet, No Cells (warm media through wet boundary)

| Measurement | Value / observation | Result | Notes |
|---|---|---|---|
| Focus survives air -> 0.17 mm glass -> warm media (yes/no) |  | not_tested | 37 C media, bay at ambient |
| Condensation haze onset on plate underside (yes/no) |  | not_tested |  |
| Time-to-onset |  | not_tested |  |
| Contrast drop at onset |  | not_tested |  |
| T_underside |  | not_tested |  |
| DewPoint |  | not_tested |  |
| Margin (T_underside - DewPoint) |  | not_tested |  |

## Phase D - Live Cells (illumination fork)

| Illumination mode | Michelson contrast C | Count A | Count B | Agreement (+/-10%) | Confluence | Result | Notes |
|---|---|---|---|---|---|---|---|
| Transmitted (from above) |  |  |  |  |  | not_tested | HIGH cost - competes with sealed lid manifold |
| Oblique (from below, off-axis) |  |  |  |  |  | not_tested | LOW cost - module-side, preferred win |
| Epi / reflected (from below, through objective) |  |  |  |  |  | not_tested | LOW cost - future fluorescence path |

## The Three Gating Numbers

| Gate | Measured value / observation | Result | Notes |
|---|---|---|---|
| (a) Focus + WD_real >= ~8.8 mm (element at/below z = -8) |  | not_tested | 4x passes hugely; 10x (~8 mm) marginal/fail - record explicitly |
| (b) Contrast: grid C >= 0.15 AND two counts agree +/-10% (>= 1 mode) |  | not_tested | 0.08-0.15 marginal (computational only); < 0.08 = change illumination |
| (c) Field flatness: dZ_field <= DOF AND dZ_tilt <= DOF across 5 wells |  | not_tested | 4x DOF +/-55 um; dZ_tilt > DOF -> per-well autofocus |

## CAD-Feed Measurements

| Bench measurement | Measured value | Param mapping | Result | Notes |
|---|---|---|---|---|
| Front-end length `FE_x` |  | `front_end_length_x` (21.0) = measured + 1 mm margin | not_tested |  |
| Front-end width `FE_y` |  | `front_end_width_y` (13.0) = measured + 1 mm margin | not_tested |  |
| Front-end vertical extent `FE_z` (objective parfocal + fold mirror) |  | `front_end_height_z` (28.0) = measured | not_tested |  |
| Per-axis overhang past well aperture, X |  | `observer_sweep_extra_x` (16.1) - retire fudge | not_tested | headline deliverable |
| Per-axis overhang past well aperture, Y |  | `observer_sweep_extra_y` (12.2) - retire fudge | not_tested | headline deliverable |
| Scan-axis footprint incl. horizontal camera arm |  | dry-bay XY rectangle (swept body) | not_tested | tube lens + camera count against XY, not Z |
| WD_real |  | consistency check on `carriage_top_clearance_z` (8.0) | not_tested | if element forced above z = -8, 8 mm clearance invalid |
| dZ_tilt vs focus stroke |  | `front_end_focus_stroke_z` (12.0) | not_tested | confirm dZ_tilt + DOF margin <= 12.0 |
| Z-closure: 8 + FE_z + focus_stroke <= 62 |  | `carriage_height_z` (62) | not_tested | element <= z = -8 AND barrel Ø <= 32 |
| Front barrel diameter vs keepout |  | `objective_keepout_diameter` (32) | not_tested | barrel Ø <= 32 |

## Decision

Decision: `pass | revise | defer | block`

Rationale:

## CAD Changes Authorized By Evidence

| Evidence | Authorized CAD change |
|---|---|
|  |  |

## Open Failures Or Blockers

| Failure | Stage 0 gate / Gate 6 target | Next action |
|---|---|---|
|  |  |  |
