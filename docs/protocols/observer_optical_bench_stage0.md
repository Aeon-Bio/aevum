# Observer Optical Bench — Stage 0 Static Validation

## Purpose

This protocol closes the first physical evidence loop for the observer: whether a
static, single-station inverted optical head can focus on cells on the top of the
0.17 mm coverslip, from at least 8 mm below the plate bottom, through the real wet
boundary — and at what working distance and head footprint. It converts the dry
bay's reserved-air placeholders into caliper-measured geometry and exercises the
illumination fork, condensation behavior, and field flatness on the same rig. See
`observer_optical_bench.md` for the full Stage-0 rationale, the optical-train
selection, the BOM, and the decision tree this procedure executes.

It does not prove moving-system imaging. This static rig says nothing about the
moving carriage's settling time, resonance, servo jitter, motion-induced defocus,
or full-row traversal — those are Stage 1–4 properties of the motion system, tested
on the actual stage. It does not prove Gate 6 imaging performance: passing Stage 0
only retires the optical and geometric uncertainty so Stage 3 is a motion problem,
not also an optics problem. Gate 6 stays blocked until the physical gantry is built.
CAD envelope geometry is not physical evidence; only the measured numbers from this
bench are.

## Measurement Record

Create the run record under:

```text
data/measurements/YYYY-MM-DD_observer_optical_bench_stage0.md
```

Use `data/measurements/templates/observer_optical_bench_stage0.md` as the starting
record. Keep every observer Gate 6 row `not_tested` until each has measured image
or caliper evidence — CAD-side checks (`observer_front_end_swept_body_check`,
`observer_carriage_envelope_check`) are geometric scaffolding, not closure.

Record at minimum:

| Item | Tool | Pass condition |
|---|---|---|
| (a) Focus + real WD | image + calipers | sharp focus through the wet stack AND `WD_real` (front element → cell plane) ≥ ~8.8 mm so the front element sits at/below z = −8 |
| (b) Contrast + count agreement | raw-frame Michelson + two manual counts | grid/edge `C ≥ 0.15` AND two independent cell counts agree ±10 % in at least one illumination mode |
| (c) Field flatness / tilt | per-well focus-Z calipers | `ΔZ_field ≤ DOF` AND `ΔZ_tilt ≤ DOF` across the 5-well pattern |
| Condensation behavior | warm-media wet run + photo | underside haze onset recorded; `T_underside > DewPoint + 2 °C` held during imaging |
| Real working distance `WD_real` | calipers | front-element-to-coverslip distance measured, not estimated |
| Head footprint `FE_x × FE_y × FE_z` | calipers (bounding box) | vertical extent (objective parfocal + fold mirror) and swept XY extent measured |
| Z-closure | arithmetic on measured `FE_z` | `8 + FE_z + focus_stroke + margin ≤ 62`, front element ≤ z = −8, barrel Ø ≤ 32 |

## Setup

Build the bench per the BOM and assembly steps in `observer_optical_bench.md` — do
not re-list parts here; the bench doc is the single source for the optical train,
the Taobao terms, and the first-purchase subset.

1. Lay the 300×300 breadboard on damping feet / a heavy slab so the cradle and head
   share one mechanical ground. Let it settle ~15 min after handling; do not hold
   the posts during imaging (hand heat is the µm-scale enemy on a static bench).
2. Mount the plate cradle skirt-only, central cutout open from below so the full
   observation window is clear — nothing under any well, flange only. Level to
   <0.1° with the set-screw feet and a bubble level. The cradle's plate-bottom datum
   **is** the bay's plate-support plane (`sensor_module_interface.md`).
3. Assemble the optical head straight first (objective → RMS→C → extension tubes →
   f = 50 mm tube lens → camera), tube-lens-to-sensor = 50 mm. Clamp on the manual
   XYZ stage below the cradle, pointing up. Z = focus, XY = well-centering and tiling.
4. Mount the WS2812 16×16 matrix on the illumination cross-arm above the plate with
   the frosted diffuser between it and the plate; keep the panel and ring light as
   baselines. The bench is the bay at one well; the head's vertical envelope below
   the plate datum is the front-end swept body's straight-down portion
   (`observation_module.md`).
5. Default to non-contact and skirt-only registration: nothing is adhered, fastened,
   or labeled on the CellVis plate.

Run the four phases **in this exact order; each is a gate — do not proceed if the
prior fails.** The dry → wet → live ordering isolates cause: if live imaging fails
you already know whether it is the optical train (A), the glass/geometry (B), the
wet path/condensation (C), or genuinely the biology/illumination (D). Never debug
all four at once.

## Phase A — Dry, No Plate

1. Image a USAF 1951 resolution target in air, no plate in the cradle.
2. Record the smallest resolved group/element and the raw working distance by
   calipers.
3. **Pass:** resolve to the optical prediction (4×/NA 0.10 → ~3.4 µm → USAF Group 7
   Element 1 clearly). A miss here is rig misalignment — fix the rig; do not blame
   the plate. This is not an architecture verdict.

## Phase B — Dry Through The Real Plate, No Cells

1. Install a CellVis P96-1.5H-N plate in the cradle. Rest a hemocytometer grid
   (50 µm pitch) on the coverslip top in the imaged well.
2. Image **5 wells: the four extreme corners + center.**
3. Per well, record: focus-Z, real front-element-to-coverslip `WD_real`, resolved
   feature, and the corner-vs-center focus delta `ΔZ_tilt` (= plate tilt).
4. **Pass:** the grid resolves through the real 0.17 mm glass at every well, and the
   measured `WD_real` and per-well focus-Z are captured for the gating numbers below.

## Phase C — Wet, No Cells

1. Pipette **warm (37 °C) media** into the imaged well with the dry bay at ambient,
   to force the real thermal gradient. Confirm focus survives air → 0.17 mm glass →
   media.
2. **Watch for condensation haze on the plate underside** — record yes/no,
   time-to-onset, and any contrast drop. This is a required wet-boundary output, not
   optional.
3. Hold `T_underside > DewPoint + 2 °C` during the imaging window; if the underside
   reaches dew point the haze degrades contrast and the wet-path result is invalid.
4. **Pass:** focus is maintained through the full wet stack and condensation
   behavior is characterized (onset time and contrast effect logged), with the
   underside held above dew point + 2 °C while imaging.

## Phase D — Live Cells

1. Seed adherent cells; re-image the same 5-well pattern (corners + center).
2. Image under **all three illumination modes — transmitted-from-above,
   oblique-from-below, epi.** See `observer_contrast_fork_ws2812.md` for the WS2812
   pixel patterns per mode (center = brightfield, quadrant = oblique, ring =
   darkfield) and the drive/exposure detail.
3. Per mode, record cell countability, confluence, morphology, and the Michelson
   contrast on a cell edge.
4. **Pass:** at least one illumination mode gives countable cells meeting gating
   number (b). Test oblique-from-below first — it is the cheap architectural win that
   keeps the sealed top intact; only fall back toward a top window if oblique is
   inadequate through the media column.

## The Three Gating Numbers

These are the falsifiable thresholds the bench exists to clear. Record each
explicitly — including the marginal/fail cases.

1. **(a) Focus + real WD.** Sharp focus through the wet stack AND `WD_real`
   (front element → cell plane) **≥ ~8.8 mm** so the front element sits at/below
   z = −8. The 4× (~22 mm WD) passes hugely; the **10× (~8 mm WD) is the
   marginal/fail case — record it explicitly** rather than assuming.
2. **(b) Contrast + count agreement.** Michelson
   `C = (I_max − I_min)/(I_max + I_min)` on a grid line / cell edge in raw frames,
   plus cell-count agreement: **grid/edge `C ≥ 0.15` AND two manual counts agree
   ±10 %** in at least one illumination mode. 0.08–0.15 = marginal (computational
   enhancement only); < 0.08 = illumination must change.
3. **(c) Field flatness / tilt.** Intra-well edge defocus `ΔZ_field` and well-to-well
   `ΔZ_tilt` vs depth of field: **`ΔZ_field ≤ DOF` AND `ΔZ_tilt ≤ DOF`** across the
   5 wells (4× DOF ±55 µm → generous). `ΔZ_tilt > DOF` → per-well autofocus, confirm
   stroke ≤ 12 mm. `ΔZ_field > DOF` → field not flat, tile + refocus or drop
   magnification.

## Feeding The CAD

The measured numbers — not the placeholders — become the observer's CAD truth.
Overwrite these exact params in `cad/one_row_coupon.params.json` (mapping rules in
`observer_optical_bench.md`):

1. Measured front-end XY bounding box → `front_end_length_x` / `front_end_width_y`
   (= measured + 1 mm assembly margin); measured vertical extent (objective parfocal
   + fold mirror) → `front_end_height_z`.
2. **Headline deliverable:** the measured per-axis overhang of the head over the well
   aperture **replaces the hand-tuned fudge factors `observer_sweep_extra_x` (16.1)
   and `observer_sweep_extra_y` (12.2)**. The bench retires both numbers.
3. Measured scan-axis (swept XY) footprint of the horizontal tube-lens/camera arm
   becomes the swept-body rectangle against the dry-bay XY budget — the tube lens and
   camera cost zero vertical budget but do count in XY.
4. `WD_real` is a consistency check on `carriage_top_clearance_z` (8.0): if `WD_real`
   forces the element above z = −8, the 8 mm clearance is invalid and the bay must
   deepen. `ΔZ_tilt` confirms `front_end_focus_stroke_z` (12.0).
5. Z-closure arithmetic: `8 + FE_z + focus_stroke + margin ≤ 62`, front element
   ≤ z = −8, barrel Ø ≤ 32. Record the result and log the param overwrite and any
   authorized geometry change in `decision_log.md`.

## Pass/Fail Boundary

The observer claims and Gate 6 remain blocked if any of these occur:

- Phase A does not resolve to the optical spec (rig not trustworthy — every later
  number is suspect);
- focus cannot be reached through the real wet stack, or `WD_real < ~8.8 mm` at the
  chosen magnification (front element forced above z = −8);
- no illumination mode reaches Michelson `C ≥ 0.15` with two counts agreeing ±10 %
  (cells are not countable);
- `ΔZ_field > DOF` or `ΔZ_tilt > DOF` is left unresolved (field not flat / tilt not
  absorbed by focus stroke);
- condensation haze drives the plate underside to/below dew point during imaging, or
  condensation behavior is left uncharacterized;
- the measured head fails Z-closure (`8 + FE_z + focus_stroke + margin > 62`, element
  above z = −8, or barrel Ø > 32);
- the fudge factors `observer_sweep_extra_x/y` and `front_end_*` are not replaced by
  caliper-measured values — CAD geometry is not physical evidence.

Passing this protocol only supports the Stage-0 static-imaging claim and authorizes
the param overwrite that retires 16.1/12.2. It does not authorize moving-system
imaging, OT-2 motion, the full-row traversal claim, or any Gate 6 imaging-performance
verdict; those are resolved physically at Stages 1–4. No CAD change is authorized
unless the run record identifies the measured evidence and the specific parameter it
pins.
