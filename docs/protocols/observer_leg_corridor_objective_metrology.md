# Observer Leg-Corridor & Objective-Barrel Metrology — Stage 0

## Purpose

This protocol closes the OC-A15 evidence loop: whether a real objective barrel
actually threads the clear corridor between the OT-2 deck standoff legs while the head
sweeps the four-plate column. The CAD found that the binding scan-axis constraint is
**not** the Ø32 objective keepout — it is the ~120.4 mm clear gap between the four 80 mm
structural standoff legs at the slot corners (which span the head's Z sweep), co-located
with the milled dry-bay wall (the bay hi-wall is actually ~0.1 mm tighter than the legs).
A head footprint wider than ~21 mm strikes that wall (strike onset ≈ 21.2 mm in the CAD
model; a Ø25 barrel overflows by ~3.6 mm). This
procedure converts the placeholder corridor (120.4 mm) and the placeholder barrel
(Ø25) into caliper-measured numbers, and decides whether a sourced slim objective fits.

See `decision_log.md` (the 2026-06-14 OC-A15 analysis-update entry) for the full
derivation, and `observer_optical_bench.md` for the optical-train selection this barrel
belongs to.

It does **not** prove imaging, focus, or motion — those are the Stage-0 optical bench
(`observer_optical_bench_stage0.md`) and Stage 1–4 motion properties. This protocol
proves one geometric fact: **a specific objective threads a measured corridor.** CAD
corridor geometry is not physical evidence; only the measured numbers here are.

## Measurement Record

Create the run record under:

```text
data/measurements/YYYY-MM-DD_observer_leg_corridor_objective_metrology.md
```

Use `data/measurements/templates/observer_leg_corridor_objective_metrology.md` as the
starting record.

Record at minimum:

| Item | Tool | Pass condition |
|---|---|---|
| (a) Standoff-leg scan corridor `W_corr` | calipers on the real OT-2 deck / printed standoff legs | clear inner-face gap measured (placeholder 120.4 mm); record both ends and the narrowest |
| (b) Objective widest diameter `Ø_obj` | calipers on the candidate objective (widest knurl, NOT the thread shoulder) | `Ø_obj` measured at the widest point along the full parfocal length |
| (c) Camera-arm scan-axis intrusion `arm_x` | calipers on the assembled head | post-fold tube/camera does NOT add to the scan-axis footprint (coaxial-fold or offboard); `arm_x ≈ 0` |
| (d) Effective scan footprint `FE_scan` | calipers (bounding box on the scan axis) | `FE_scan = max(Ø_obj, head body on scan axis, arm_x)` measured |
| (e) Corridor fit | arithmetic | `well_window_x + FE_scan ≤ W_corr` with explicit residual (the CAD strike line is footprint ≤ ~21.2 mm; record the real residual) |
| (f) Y wet-gutter wall `Y_avail` | calipers | clear dry-Y between the wet-witness/gasket gutters (placeholder 357.5 mm); the swept-Y `well_span_y + FE_scan` must fit |
| (g) Standoff-leg Z span | calipers | confirm the legs span the head's Z sweep (z −48..−8) — i.e. the corridor is a real 3-D wall, not a 2-D coincidence (placeholder legs z −80..0) |

## Setup

1. Obtain a real OT-2 deck (or the printed deck-engagement standoff legs from the row
   module). The four legs that matter are the ones at the **inner** corners of the
   imaged slot column — their inner faces define the scan corridor `W_corr`. The CAD
   places their inner faces at X = 13.6 / 134.0 (a 120.4 mm gap); measure the real
   parts, not the model.
2. Obtain the candidate objective(s). The optical selection is an infinity-corrected
   4× plan-achromat, RMS thread, NA ~0.10, 0.17-corrected (see
   `observer_optical_bench.md`). The RMS thread floors the barrel near Ø20.3; the
   question is whether a **slim** 4× (widest knurl ≤ ~21 mm) is sourceable. Buy 2–3
   candidates spanning the slim end of the range.

## Procedure

### (a) Measure the scan corridor

1. With the deck on a flat reference, caliper the clear horizontal gap between the
   inner faces of the two legs that straddle the optical window, at the Z height the
   head will occupy (mid-bay, ~z = −28). Measure at **both** plate ends of the column
   and at the mid-column slot — record the **narrowest** as `W_corr` (the binding wall).
2. Confirm (item g) the legs are continuous structure through the head's Z sweep
   (z −48..−8), not a shoe at the bottom. If a leg necks down or is interrupted in
   that band, the corridor there is wider — record the true minimum.

### (b)–(d) Measure the objective + head footprint

1. Caliper each candidate objective's **widest** outer diameter along its full length
   (the knurl/grip ring is usually widest, not the thread). Record `Ø_obj`.
2. On the assembled head (objective + fold + tube + camera), caliper the bounding box
   on the **scan axis** (`FE_scan`) and confirm the post-fold camera arm does not
   protrude on that axis (`arm_x ≈ 0`); if it does, the head is over-budget regardless
   of the barrel — re-route the arm coaxial/offboard (the `scan_axis_footprint_excludes_camera_arm`
   contract).

### (e)–(f) Decide the fit

1. Compute `well_window_x + FE_scan` and compare to `W_corr`. The CAD reports the live
   residual as `observer_carriage_envelope_check.carriage_traverse.scan_corridor_margin_mm`
   (placeholder 0.12 mm). A negative residual means the head strikes the legs — reject
   that objective or relocate the legs (see Outcomes).
2. Compute `well_span_y + FE_scan` and compare to `Y_avail` (the wet/dry-gutter-bounded
   dry-Y, placeholder 357.5 mm). This is the traverse-axis check; it has more slack
   (~10 mm placeholder) but is still real.

## Outcomes / Decision Tree

- **`Ø_obj` and `FE_scan` thread `W_corr` with positive residual → PASS.** Update
  `cad/one_row_coupon.params.json` `observer_robotics.front_end_barrel_diameter` and the
  `front_end_*` footprints to the measured values; the placeholder provenance note is
  retired for these fields. The dry-bay fit is then physically grounded, not assumed.
- **No sourceable objective threads `W_corr` → relocate the standoff legs.** The legs
  sit in the optical scan corridor by placement, not necessity. Move the deck-engagement
  seating to end-only / outboard of the optical window so the corridor widens to the
  full slot. This is a structural redesign of `_deck_engagement_foot_rectangles` and
  requires a **Stage-0 seating-repeatability re-validation** (the legs are the kinematic
  datum to the OT-2 deck; moving them must not lose plate-registration repeatability).
- **`W_corr` measures materially different from 120.4 mm → re-baseline the CAD.** The
  placeholder leg positions drive the entire OC-A15 conclusion; the measured corridor is
  the source of truth.

## What this gates

Passing this protocol retires the OC-A15 geometric uncertainty (`decision_log.md`) and
the `front_end_barrel_within_head_footprint` / `scan_corridor_margin_mm` diagnostics in
the CAD. It is **upstream of every SMIS modality head**: the same corridor binds every
swappable head, so the SMIS envelope's scan-footprint limit
(`SmisEnvelope.scan_corridor_footprint_max_mm`) must be set from the measured `W_corr`, not the
looser Ø32 objective keepout — see `sensor_module_interface.md`. It does not retire
Gate 6 imaging, focus, or motion evidence.
