# Observer Leg-Corridor & Objective-Barrel Metrology — Stage 0

## Purpose

This protocol closes the OC-A15 evidence loop: whether a real objective barrel
actually threads the clear corridor between the OT-2 deck standoff legs while the head
sweeps the four-plate column. The CAD found that the binding scan-axis constraint is
**not** the Ø32 objective keepout — it is the clear gap between the four 80 mm
structural standoff legs at the slot corners, which span the head's Z sweep.

> **Corrected 2026-09-21.** This protocol previously quoted a 120.4 mm corridor with
> leg faces at X = 13.6 / 134.0 and a ~21.2 mm strike onset, and said the bay hi-wall
> was ~0.1 mm tighter than the legs. All of that was stale. Re-derived from the live
> `cad/one_row_coupon.params.json` + `_deck_engagement_foot_rectangles`:
>
> | | stale | **live** |
> |---|---:|---:|
> | corridor width | 120.4 | **117.4 mm** |
> | leg inner faces (X) | 13.6 / 134.0 | **17.10 / 134.50** |
> | head-footprint strike onset | 21.4 | **15.56 mm** |
>
> Two independent errors compounded. (1) `lower_service_foot_inset_x` (3.0) walks one
> tile-4 foot inboard, narrowing the corridor by 3.0 mm. (2) The old figure assumed the
> well array sits centred in the corridor and took the budget as
> `corridor − 99.0 mm well span`; it does not — live slack is **7.78 mm near** and
> **10.62 mm far**. The objective is on-axis, so the NEAR leg binds and the budget is
> `2 × 7.78 = 15.56`. At 21.2 the head fails **both** walls (corridor −2.82, bay −0.08),
> so that value never cleared anything. Confirmed by sweeping the live
> `carriage_traverse` check: `clears_traverse` flips between 15.56 and 15.60.
>
> **Consequence to carry into the measurement:** an RMS thread floors the barrel near
> Ø20.32, so at 15.56 mm **no RMS-threaded objective threads the corridor at all** —
> including the Ø20 reference 4×. Restoring `lower_service_foot_inset_x` to 0.0 by
> re-routing the service shroud gives a 120.4 mm corridor and a 21.24 mm budget, at
> which Ø20.32 clears by +0.46 mm. Measure with that in mind: the question is no longer
> only "is a slim 4× sourceable" but "does the service lane have to move".

> **Corrected again 2026-09-23 — 15.56 mm is a residual, not a wall.** Everything
> below still quotes 15.56 mm as the live head-footprint budget, and the
> consequences drawn from it (":32 no RMS-threaded objective threads the corridor
> at all", re-routing the service shroud as the only relief) are consequences of
> that reading. They are conditional, not facts about the legs.
>
> 15.56 mm is the residual after requiring the head to scan **all 12 well
> columns** — a 99.0 mm sweep — inside the 117.4 mm corridor. The 88 × 52 mm
> aperture never admitted 12 columns: it admits **8**, spanning 63.0 mm at
> X 42.88 … 105.88. Budgeted against the columns the optics can actually see:
>
> ```
> min( 2 × (42.88 − 17.10), 2 × (134.50 − 105.88) ) = min( 51.56, 57.24 ) = 51.56 mm
> ```
>
> **At 51.56 mm a Ø20.32 RMS thread clears by +31.24 mm, and the "no objective
> fits" consequence disappears without moving any geometry** — it is a
> parameterisation of the traverse check, not a re-route. See
> `../engineering/observer_optical_bench.md`, § *The 15.56 mm corridor is an
> artifact of scanning wells the head cannot reach*.
>
> The coupling is the thing to carry into the measurement: enlarging the aperture
> to ~110 × 74 mm to recover all 384 wells returns the reachable span to 99.0 mm
> and the budget toward 15.56 mm. **The wide aperture and the wide head are
> alternatives, not a package.** Measure both corridor walls and the real barrel
> so the trade can be made on numbers.
>
> The corridor geometry itself (117.4 mm clear, faces at X 17.10 / 134.50, near
> slack 7.78 / far 10.62) is unchanged and remains what this protocol measures.

This procedure converts the corridor and the placeholder barrel (Ø25) into
caliper-measured numbers, and decides whether a sourced slim objective fits.

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
| (a) Standoff-leg scan corridor `W_corr` | calipers on the real OT-2 deck / printed standoff legs | clear inner-face gap measured (CAD: 117.4 mm); record both ends and the narrowest, and record each end SEPARATELY — the corridor is not symmetric about the well array |
| (b) Objective widest diameter `Ø_obj` | calipers on the candidate objective (widest knurl, NOT the thread shoulder) | `Ø_obj` measured at the widest point along the full parfocal length |
| (c) Camera-arm scan-axis intrusion `arm_x` | calipers on the assembled head | post-fold tube/camera does NOT add to the scan-axis footprint (coaxial-fold or offboard); `arm_x ≈ 0` |
| (d) Effective scan footprint `FE_scan` | calipers (bounding box on the scan axis) | `FE_scan = max(Ø_obj, head body on scan axis, arm_x)` measured |
| (e) Corridor fit | arithmetic | per-side, NOT centred: `near_slack = x_first_well − x_near_leg_inner` and `far_slack = x_far_leg_inner − x_last_well`; budget `= 2 × min(near, far)` (CAD: 2 × 7.78 = **15.56 mm**). Record the real residual on each side |
| (f) Y wet-gutter wall `Y_avail` | calipers | clear dry-Y between the wet-witness/gasket gutters (placeholder 357.5 mm); the swept-Y `well_span_y + FE_scan` must fit |
| (g) Standoff-leg Z span | calipers | confirm the legs span the head's Z sweep (z −48..−8) — i.e. the corridor is a real 3-D wall, not a 2-D coincidence (placeholder legs z −80..0) |

## Setup

1. Obtain a real OT-2 deck (or the printed deck-engagement standoff legs from the row
   module). The four legs that matter are the ones at the **inner** corners of the
   imaged slot column — their inner faces define the scan corridor `W_corr`. The CAD
   places their inner faces at X = 17.10 / 134.50 (a 117.4 mm gap, asymmetric about the
   well array); measure the real parts, not the model. Note which foot is the inboard
   one — `lower_service_foot_inset_x` moves a single tile-4 foot, and that one foot sets
   the binding wall.
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

1. Compute `2 x min(near_slack, far_slack) - FE_scan`, per item (e). **Do not use the
   centred single-gap form `well_window_x + FE_scan` vs `W_corr`** — item (e) refutes it:
   the well array is not centred in the corridor (live slack 7.78 near / 10.62 far), so the
   near wall binds and the centred form understates the strike. The CAD reports the live
   residual as `observer_carriage_envelope_check.carriage_traverse.scan_corridor_margin_mm`,
   which is **-2.72 mm today** (it strikes) at the 21 mm bare-objective placeholder
   footprint. A negative residual means the head strikes the legs — reject that objective,
   relocate the legs, or budget against the reachable columns (see the 2026-09-23 correction
   at the head of this protocol, and Outcomes). *(Corrected 2026-09-23: this step read
   "placeholder 0.12 mm", which was neither the live value nor computed on item (e)'s form.)*
2. Compute `well_span_y + FE_scan` and compare to `Y_avail` (the wet/dry-gutter-bounded
   dry-Y, placeholder 357.5 mm). This is the traverse-axis check; it has more slack
   (~10 mm placeholder) but is still real.

## Outcomes / Decision Tree

- **`Ø_obj` and `FE_scan` thread `W_corr` with positive residual → PASS.** Update
  `cad/one_row_coupon.params.json` `observer_robotics.front_end_barrel_diameter` and the
  `front_end_*` footprints to the measured values; the placeholder provenance note is
  retired for these fields. The dry-bay fit is then physically grounded, not assumed.
- **No sourceable objective threads `W_corr` → relocate the standoff legs.** The legs
  sit in the optical scan corridor by placement, not necessity. This is a structural
  redesign of `_deck_engagement_foot_rectangles` and requires a **Stage-0
  seating-repeatability re-validation** (the legs are the kinematic datum to the OT-2
  deck; moving them must not lose plate-registration repeatability).

  Three variants, costed against the live model on 2026-09-21. Head budget is
  `2 x min(near_slack, far_slack)`; bearing area today is 4 posts x 3.8 x 7.0 =
  106.4 mm2 per slot.

  | variant | head budget | bearing area/slot | cost |
  |---|---:|---:|---|
  | today (3.8 posts, `lower_service_foot_inset_x` 3.0) | 15.56 mm | 106.4 | — |
  | re-route service shroud, inset 0.0 | **21.24** | 106.4 | shroud lane must move |
  | + reshape to 2.0 mm rails (narrow X, long Y) | **24.84** | 344.0 | line contact, see below |
  | + reshape to 1.5 mm rails | 25.84 | 258.0 | as above |
  | **absolute ceiling, legs still inside the 130.0 mm slot** | **30.84** | — | unreachable in practice |

  **Thinning beats relocating.** Reshaping the corner posts into two X-strip rails
  running the slot's Y length raises bearing area (2.0 mm rails give 344 mm2, 3.2x
  today) while widening the corridor, and converts four point posts into continuous
  webs — so it moves stiffness the right way. The cost is contact character, not load:
  posts tolerate a wavy deck-slot floor, a continuous rail bridges local high spots and
  can rock. If rocking shows up, segment each rail into ~3 pads of 15 mm (still 180 mm2,
  1.7x today) to keep discrete contact at the same 2.0 mm X width. Measure seating
  repeatability before and after — this is exactly what the Stage-0 re-validation is for.

  **End-only seating is possible but tight in Y, and it is NOT a free lunch.** Feet must
  land inside a machined slot opening (`deck_interface.description`: "shoes fit inside
  machined slot openings ... avoids aluminum deck-frame ribs"), and the head sweeps the
  full Y of every slot. That leaves only the Y bands between the slot edge and the first
  well row: slot 1 runs Y 8.875..96.875 while wells start at 21.240, so the band is
  `12.365 - head_Y/2`. At the live head traverse footprint (13.0 mm = max of
  `gantry_truck_traverse_extent` and `front_end_width_y`) that is **5.87 mm below /
  6.14 mm above** — too narrow for the current 7.0 mm `foot_width_y`, but workable for a
  foot rotated to 3.8 mm in Y and run long in X. It collapses fast: at head_Y 20 the band
  is 2.4 mm, at 26 it is negative. So end-only survives only while the head stays thin on
  the TRAVERSE axis, and any Y growth kills it. The structural price is the real one:
  support span goes from the 90.5 mm slot pitch to ~357 mm, so distributed sag scales
  ~`L^4` (**~243x**) and the first structural mode drops ~`1/L^2` (**~0.064x**, i.e. ~16x
  lower). Against a focus tolerance that tightens with NA (+-27.5 um at NA 0.10 but
  +-1.56 um at NA 0.42, i.e. 3.12 um total), that is the wrong direction. Static sag is mappable by autofocus;
  the mode drop and the settle time it implies are not.

  **Outboard seating needs a different parameter.** The assembly is 148.6 mm wide over a
  130.0 mm slot, so it already overhangs the deck frame by 9.30 mm per side and already
  overruns the 132.5 mm `slot_pitch_x` by 16.1 mm (`adjacent_slot_keepout_columns: 1` is
  spent either way). Putting legs on that overhang gives a **41.84 mm** budget with 3.8 mm
  feet — the only route to a Ø34 long-WD metrology barrel — but it means bearing on
  extruded frame instead of machined slot, which `deck_frame_keepout_height_z: 2.5`
  currently forbids by holding the module clear of the frame. That is a flatness and
  repeatability regression precisely where NA makes it least affordable. Hold it in
  reserve.
- **`W_corr` measures materially different from 117.4 mm → re-baseline the CAD.** The
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
