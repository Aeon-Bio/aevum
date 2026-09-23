# Observer Optical Bench Stage 0

Protocol:
`docs/protocols/observer_optical_bench_stage0.md`

*Brought back in step with the protocol 2026-09-23. This sheet had not been touched
while the protocol was rewritten, so it was still asking for sign-off against
thresholds that had been retracted twice (the ~8.8 mm standoff, the "+/-55 um" DOF
double-count, and the "nothing under any well" clause the 88 x 52 mm aperture has
never met). Each corrected row says what it used to say.*

## Session Identity

| Field | Value |
|---|---|
| Date |  |
| Operator |  |
| Bench build identifier |  |
| Objective (4x / 10x / ELWD) |  |
| Correction collar fitted (y/n) and setting (mm) |  |
| Camera |  |
| Plate identifier |  |
| Media / cells |  |
| Measurement images folder |  |

## Pre-Run Checks

| Check | Result | Evidence / notes |
|---|---|---|
| Head, cradle, and source share one breadboard datum | not_tested |  |
| Plate seated skirt-only in a cradle whose central cutout is >= 107 x 71 mm, so nothing sits under any well | not_tested | corrected 2026-09-23 (was "nothing under any well" with no number). 96-well centres span 99.0 x 63.0 mm; clearing every well needs that plus a well diameter = 105.21 x 69.21 at `lower_well_diameter` 6.21. The BAY's own 88 x 52 mm aperture does NOT meet this - it is 17.21 mm short on both axes at `lower_well_diameter` 6.21 (17.80 mm at the seating-relevant `upper_well_diameter` 6.80), so frame material sits under columns 1/12 and rows A/H. The 17.4 mm figure this row previously carried implies a 6.4 mm ruling well diameter that matches no parameter and has been withdrawn in decision_log.md, 2026-09-23. The bench cradle is a printed part with no structural constraint, so cut it to the wells. |
| Plate leveled to < 0.1 deg, settled ~15 min, posts not hand-held | not_tested |  |
| Illumination arm mounted, source 30-80 mm above plate top | not_tested |  |
| Tube-lens-to-sensor spacing set to 50 mm | not_tested |  |
| Objective parfocal class recorded (4x WD ~22 mm / 10x WD ~8 mm) | not_tested |  |
| Standoff built: parked (nose at z = -8, WD 19.90) or risen (nose at z = +4.00, full focus_stroke_z upward, WD 7.90) | not_tested | added 2026-09-23 - both are legal bay geometry; probe cylinders to O25 mm rise unobstructed from z = 0 to z = 11.71 at every tile aperture centre |

## Phase A - Dry, No Plate (USAF in air)

| Measurement | Value / observation | Result | Notes |
|---|---|---|---|
| Smallest resolved USAF 1951 group / element |  | not_tested | pass = **Group 6 Element 6 - Group 7 Element 1** at 4x / NA 0.10. Corrected 2026-09-23 (was "~Group 7 Element 1", quoted without the sampling caveat): the bench is SAMPLING-limited, not diffraction-limited. At f_tube 50 vs f_ref 180 the 4x runs at M_eff 1.11x, so 2.4 um pixels sample at 2.16 um/px and the practical floor is ~4.3 um (2 px), against optics resolving 2.75 um (Abbe) / 3.36 um (Rayleigh). |
| Raw working distance (front element to target), calipers |  | not_tested |  |
| Rig alignment verdict |  | not_tested | fail here = misalignment, not the plate |

## Phase B - Dry Through Real Plate, No Cells (5-well tilt map)

*Correction-collar column added 2026-09-23: protocol step B3 now requires the
setting be recorded. An objective uncorrected for the 0.17 mm coverslip is capped
at NA <= 0.363 @ 550 nm (0.336 @ 405, 0.397 @ 785) by the Marechal criterion
whatever its working distance; the collar is what removes that cap, so its setting
is part of the result, not a rig detail. Write "none" if the objective has no collar.*

| Well position | Focus-Z | WD_real (front element to coverslip) | Collar setting (mm) | Resolved feature (50 um grid) | Focus delta vs center (tilt) | Result | Notes |
|---|---|---|---|---|---|---|---|
| Center |  |  |  |  | (datum) | not_tested |  |
| Corner +X +Y |  |  |  |  |  | not_tested |  |
| Corner -X +Y |  |  |  |  |  | not_tested |  |
| Corner +X -Y |  |  |  |  |  | not_tested |  |
| Corner -X -Y |  |  |  |  |  | not_tested |  |

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
| Cell-plane T, head RETRACTED (thermocouple in media, 37 C media over ambient bay) |  | not_tested | added 2026-09-23, protocol Phase C step 4 |
| Cell-plane T, head AT WORKING DISTANCE |  | not_tested | same thermocouple, same well, head advanced to WD |
| dT = retracted - at-WD |  | not_tested | **pass: dT <= 0.3 K.** Fail -> a LOCAL 37 C nose heater is required (not a 37 C bay: IMX178 dark current roughly doubles per 6-7 K, which spends the long integrations Raman and luminescence depend on) |
| Nose assembly recorded (aluminium mass, mount, WD at which dT was taken) |  | not_tested | G is a property of the assembly measured, not of "an objective" |

## Phase D - Live Cells (illumination fork)

| Illumination mode | Michelson contrast C | Count A | Count B | Agreement (+/-10%) | Confluence | Result | Notes |
|---|---|---|---|---|---|---|---|
| Transmitted (from above) |  |  |  |  |  | not_tested | HIGH cost - competes with sealed lid manifold |
| Oblique (from below, off-axis) |  |  |  |  |  | not_tested | LOW cost - module-side, preferred win |
| Epi / reflected (from below, through objective) |  |  |  |  |  | not_tested | LOW cost - future fluorescence path |

## The Gating Numbers

*Renamed and re-ruled 2026-09-23 to match the protocol: there were three, the
re-ruled standoff splits (a) and adds (a") thermal.*

| Gate | Measured value / observation | Result | Notes |
|---|---|---|---|
| (a) Focus + WD_real >= 19.90 mm parked OR >= 7.90 mm risen - record which standoff was built |  | not_tested | corrected 2026-09-23. Was "(a) Focus + WD_real >= ~8.8 mm (element at/below z = -8) ... 4x passes hugely; 10x (~8 mm) marginal/fail". That threshold is void twice over: the 8.8 mm figure came from a 9.73 mm standoff that omitted `base.thickness_z` (8.0) and `plate_support.land_height_z` (2.0), and the element may legally rise into the aperture. The 4x (~22 mm WD) clears the PARKED threshold by 2.1 mm - not "hugely". The 10x (~8 mm) fails parked and PASSES risen. |
| (a') Which standoff was built: parked (nose z = -8) / risen (nose z = +4.00) |  | not_tested | both are real bay geometry - the aperture column is measured clear from z = 0 to z = 11.71, i.e. to 0.02 mm of the glass outer surface (0.19 mm below the cell plane). Prefer building both. Crossing a tile boundary with the nose risen is blocked by `plate_support_frame` at z = 0.05: 3 retract/re-raise cycles per row of 4 tiles, a per-TILE cost, not per-well. |
| (a") Nose-to-well dT at working distance <= 0.3 K |  | not_tested | from the Phase C rows above. Replaces the ESTIMATED `G_obj-ambient = 50 mW/K` and is the single highest-value early measurement on the observer programme. Every head closer than ~3 mm is modelled to fail this, dry included. Budget is 0.3 K because a cooled well is an unlogged perturbation whose size tracks the revisit schedule. |
| (b) Contrast: grid C >= 0.15 AND two counts agree +/-10% (>= 1 mode) |  | not_tested | 0.08-0.15 marginal (computational only); < 0.08 = change illumination |
| (c) Field flatness: dZ_field <= DOF AND dZ_tilt <= DOF across 5 wells |  | not_tested | 4x / NA 0.10 DOF = 55 um total (+/-27 um) - corrected 2026-09-23, the old "+/-55 um" double-counted the full depth. dZ_tilt > DOF -> per-well autofocus (confirm stroke <= 12 mm). If a higher-NA head is fitted DOF collapses (2.72 um at NA 0.45, 1.53 um at NA 0.60) and refocus at every well visit is mandatory regardless of structural stability - the driver is plate-to-plate topography and seating, not temporal drift. |

## CAD-Feed Measurements

| Bench measurement | Measured value | Param mapping | Result | Notes |
|---|---|---|---|---|
| Front-end length `FE_x` |  | `front_end_length_x` (21.0) = measured + 1 mm margin | not_tested |  |
| Front-end width `FE_y` |  | `front_end_width_y` (13.0) = measured + 1 mm margin | not_tested |  |
| Front-end vertical extent `FE_z` (objective parfocal + fold mirror) |  | `front_end_height_z` (28.0) = measured | not_tested |  |
| Per-axis overhang past well aperture, X |  | `observer_sweep_extra_x` (16.1) - retire fudge | not_tested | headline deliverable |
| Per-axis overhang past well aperture, Y |  | `observer_sweep_extra_y` (17.0) - retire fudge | not_tested | headline deliverable. Corrected 2026-09-23: this row said 12.2, which was stale against `cad/one_row_coupon.params.json`. |
| Scan-axis footprint incl. horizontal camera arm |  | dry-bay XY rectangle (swept body) | not_tested | tube lens + camera count against XY, not Z |
| WD_real |  | consistency check on `carriage_top_clearance_z` (8.0) | not_tested | corrected 2026-09-23: an element above z = -8 does NOT invalidate the clearance or force the bay to deepen. A WD_real between 7.90 and 19.90 mm means `focus_stroke_z` is spent upward and the head retracts to cross tile boundaries. Only WD_real < 7.90 mm at full stroke forces a class change. |
| dZ_tilt vs focus stroke |  | `front_end_focus_stroke_z` (12.0) | not_tested | confirm dZ_tilt + DOF margin <= 12.0 |
| Z-closure: 8 + FE_z + focus_stroke <= 62 |  | `carriage_height_z` (62) | not_tested | corrected 2026-09-23: the closure conditions are vertical <= 62, nose within the MEASURED clear column (z <= 11.71) and barrel O <= 32. The "element <= z = -8" clause is dropped. Note the additive sum itself over-constrains (it charges the head for parked clearance and full stroke at once) - record the raw measurements and let `observer_optical_bench.md` adjudicate. |
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
