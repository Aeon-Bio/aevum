# Observer Optical Bench (Dry-Bay Build-Out, Stage 0)

## Purpose

The observer is the inverted optical subsystem that must image cells in every
well of the row module from underneath, inside the 80 mm dry observation bay
between the OT-2 deck plane and the plate-support plane. This page documents the
**optical bench** — not as a throwaway benchtop rig, but as **Stage 0 of
physically building out the dry bay** toward a production prototype. The bench is
the observer subsystem at one well, built statically, whose job is to convert the
bay's reserved-air envelopes into measured, real geometry and then grow
axis-by-axis into the moving in-bay scanner.

This is the third production-prototype subsystem documented as a discrete unit,
after the power section (`power_section.md`) and the sensor PCB
(`sensor_pcb.md`). Where those two were already physical, the dry bay is the
least-built part of the whole machine: today it contains **zero installed
parts**. Everything observer-related is validation-only — `dry_bay_envelope_check`,
`observer_front_end_swept_body_check`, `observer_carriage_envelope_check`,
`observer_service_raceway_envelope_check`, `observer_kinematic_split_check`,
`observer_optical_stability_check`, `observer_fiducial_focus_target_check`. The
bay is correctly reserved and correctly gated to Gate 6, but it has never been
populated. This document is how it starts getting populated.

## Stance

The observer is a COTS-authority exception in the same family as the power
section and sensor PCB. The print-native row coupon is a strict no-metal,
no-glue mechanical proof; the observer deliberately brings commercial optical and
imaging authority — objectives, a CMOS sensor, a fold mirror, programmable
illumination, and later a motion stage — into the dry bay at a defined boundary.
The authority boundary is the **dry-bay envelope**: nothing the observer adds may
intrude on the wet chamber above the plate-support plane, touch the CellVis plate
(the plate-as-consumable rule holds — all imaging is non-contact from below), or
consume the deck-foot keepouts the row coupon already validates.

The bench exists because the bay's current numbers are honest placeholders, not
measurements. The dry-bay reference rectangle is inflated around the well aperture
by two hand-tuned fudge factors — `observer_sweep_extra_x = 16.1`,
`observer_sweep_extra_y = 17.0` — chosen so the bay just barely wraps a guessed
front-end swept body. *(Corrected 2026-09-23: the slack is **not** symmetric, and
this parenthetical previously claimed ~0.1–0.2 mm on both axes. X is razor-thin at
**0.2 mm** (`carriage_traverse.scan_axis_fit_margin_mm`); Y was resized 12.2 → 17.0
on 2026-06-14 to the wet/dry-bounded deck extent and now carries **10.0 mm**
(`traverse_axis_fit_margin_mm`) — see `decision_log.md`, § *OC-A15 — implementation
(2026-06-14, "make the model report the real wall")*, item 2 "CAD — bay-Y resized to
the wet/dry-bounded deck extent, X left alone".)* The front-end itself is a placeholder
box (`front_end_length_x = 21.0`, `width_y = 13.0`, `height_z = 28.0`,
`focus_stroke_z = 12.0`). The bench replaces every one of those numbers with a
caliper-measured value from a real optical head imaging a real plate through the
real wet boundary.

## The dry bay as it exists today

Verified ground truth from `cad/one_row_coupon.params.json` and the layout:

| Quantity | Value | Source / meaning |
|---|---|---|
| Dry-bay vertical budget | **80 mm** (`observer_sweep_depth_z`) | reserved as the Raman/biophotonics exploration budget |
| Usable optical envelope | **62 mm** (`carriage_height_z`), z = −70 to −8 | the head must fit here |
| Front-element ceiling, **parked** | **z = −8 mm** (`carriage_top_clearance_z = 8`) | where optical hardware sits while the head *traverses*. *Scoped 2026-09-23 — this row read "top of any optical hardware sits at/below this", full stop. It is the traverse plane, not a hard ceiling: the nose may rise into the aperture to z = +4.00 at full `focus_stroke_z`. See "Correction (2026-09-23): the aperture is climbable".* |
| Front-element ceiling, **risen** | **z = 11.71 mm** (measured clear column) | the real hard ceiling — probe cylinders to Ø25 mm rise unobstructed from z = 0 to z = 11.71 at every tile aperture centre, i.e. to 0.02 mm of the glass outer surface (0.19 mm below the cell plane) |
| Objective keepout | **Ø32 mm** (`objective_keepout_diameter`) | front barrel must fit inside |
| Per-tile through-aperture | **88 × 52 mm** (`dry_bay.aperture_length_x` / `aperture_width_y`) | the only optical path through the base; sets both what the head can see and what it can climb into |
| Cell plane standoff | **19.90 mm** above z = −8 | 8.0 head-ceiling gap + 8.0 `base.thickness_z` + 2.0 `plate_support.land_height_z` + 1.73 open window + 0.17 coverslip. All air but the coverslip. |
| Glass in the optical path | **0.17 mm — the coverslip, and nothing else** | corrected 2026-09-21; see "Correction: there is no 0.6 mm plate window" below |
| Well bottom imageable circle | **Ø6.21 mm** (`lower_well_diameter`) | per-well field to cover |
| Coverslip | **#1.5H, 0.170 mm** (`coverslip_thickness_z`) | standard objective correction thickness |
| Well pitch | **9.0 mm** X and Y | 96 wells/plate, 384 wells/row |
| Well-center span | **99.0 mm X × 334.5 mm Y** | the full scan the production observer must reach |

The plate is CellVis P96-1.5H-N. Cells live on the **top** surface of the 0.17 mm
coverslip and are imaged from below through that glass — standard inverted
geometry, and the coverslip thickness most objectives are corrected for.

### Correction: there is no 0.6 mm plate window

Until 2026-09-21 the standoff row above read `8 mm air + 0.6 mm plate window +
~1.0 mm + 0.17 mm coverslip`, and `cad/one_row_coupon.params.json` carried a
`plate.bottom_window_thickness_z = 0.6` that `build_microplates` extruded as an
88 × 52 mm slab across the observation window at the plate underside. **Both were
wrong, and they contradicted the two paragraphs above and the Stage-0 cradle spec
("the full 88 × 52 mm observation window is open from below — nothing under any
well, skirt flange only").**

> **Note added 2026-09-23.** The cradle spec quoted here is itself internally
> inconsistent: an 88 × 52 mm window is ~17 mm too small on both axes to leave
> nothing under any well of a 96-well plate. The *principle* stands and is not
> retracted; the *geometry* violates it. See "Reachable wells, and the 'nothing
> under any well' contradiction" below.

The published profile closes exactly without any second glass layer:

| | mm |
|---|---:|
| `bottom_height_z` | 1.73 |
| `coverslip_thickness_z` | 0.17 |
| sum | **1.90** |
| `height_z` − `plate_top_to_cell_plane_depth_z` = 14.30 − 12.40 | **1.90** |

Adding a 0.6 mm window overshoots the published cell plane by exactly 0.60 mm.
`bottom_window_thickness_z` never appeared in
`data/measurements/plate_profiles/cellvis_p96_1p5h_n_published_profile.md`; the
cycle log (RS39) shows it as the pre-existing placeholder for "the plate has some
bottom", left unreconciled when the published coverslip value was added beside it.

The parameter has been removed and `build_microplates` now places a
`coverslip_thickness_z` slab at `bottom_height_z` — glass where the glass is,
open air below it.

**Second correction, same day: the standoff is 19.90 mm, not 9.73 or 9.90.**
The original row decomposed the standoff as "8 mm air + …", treating
`carriage_top_clearance_z` as the whole air gap. It is not — it only places the
head's front-face ceiling at z = −8. The plate bottom is at z = **+10.0**,
because `base.thickness_z` (8.0) and `plate_support.land_height_z` (2.0) sit
between them; the optical path crosses both through the 88 × 52 mm aperture, so
they are air, but they are still 10 mm of standoff. Live layout confirms it two
ways: `plate_bottom_z` 10.0 + 1.73 + 0.17 = cell plane z **11.90**, and
`plate_top_z` 24.3 − `plate_top_to_cell_plane_depth_z` 12.4 = **11.90**. Against
a front-face ceiling of z = −8 that is **19.90 mm**, of which 0.17 mm is glass
and 19.73 mm is air.

**This sets the working-distance floor — at the parked height.** *(Scoped
2026-09-23: the sentence as originally written said "floor", full stop. It is the
floor only for a head that never leaves the traverse plane. See "Correction
(2026-09-23): the aperture is climbable" below — the floor at full focus stroke is
7.90 mm.)* An objective that must reach the cell plane from z = −8 needs
WD ≥ 19.90 mm, which excludes the entire short-WD catalogue and makes
long-working-distance objectives the only admissible class from the parked height.
It also doubles the front aperture each NA demands, since that goes as
2·WD·tan(asin(NA)):

| NA | front aperture at WD 19.90 | vs corridor budget |
|---:|---:|---|
| 0.10 | 4.00 mm | fits today (15.56) |
| 0.40 | 17.37 mm | needs the service inset removed (21.24) — and that is the BARE aperture, before any barrel |
| 0.50 | 22.98 mm | needs rails (25.84), bare |
| 0.55 | 26.21 mm | needs the 30.84 slot ceiling, bare |

*(The "vs corridor budget" column is measured against `scan_corridor_footprint_max`
= 15.56 mm. That budget is itself an artifact — see "The 15.56 mm corridor is an
artifact of scanning wells the head cannot reach" below, which raises it to
51.56 mm without touching the CAD.)*

The open design question this raises: the head ceiling sits 18 mm below the plate
bottom while the base carries an 88 × 52 mm aperture the head could rise into.
Recovering that travel is the single largest lever on admissible NA, and no
document has yet asked whether the front element may enter the aperture.
**Answered 2026-09-23 — it may, and it is already in the parameters.**

**Why this is load-bearing, not bookkeeping.** Spherical aberration from a
plane-parallel slab goes as `W_pv ≈ t(n²−1)/(8n³)·NA⁴`, so the admissible NA is
set by the *uncorrected* glass thickness. Believing 0.77 mm of glass (0.6 window +
0.17 coverslip) sat in the path capped the usable NA near **0.25** and made every
objective above a 10× look inadmissible. The real path is 0.17 mm of #1.5H — which
is exactly what the objectives are corrected for — so the ceiling is set by the
*residual* correction error, not by 0.6 mm of phantom glass. This is the
difference between "no subcellular domain is resolvable here" and "NA ≈ 0.55 is
reachable", and it was a parameter error, not a physical limit.

*(Arithmetic corrected 2026-09-23 — the 0.77 mm figure above read "near **0.26**",
which reproduces from no stated derivation. The same formula, at t = 0.77 mm,
n = 1.5185: 0.77 mm · (n²−1)/(8n³) = 35.90 µm, so the λ/4 budget this document uses
at "The aberration ceiling" below gives NA = (0.550/143.6)^¼ = **0.249** —
equivalently 0.363 × (0.17/0.77)^¼. It describes a retired belief, but it is quoted
as arithmetic and must reproduce from the stated formula. `decision_log.md:1664`
carries the same 0.26 and is flagged to its owner.)*

*(Refined 2026-09-23: the residual correction error is itself removable — the ceiling is
0.363 for an **uncorrected** objective and is lifted by a correction collar. See
"The aberration ceiling is a correction-collar question" below.)*

## Correction (2026-09-23): the aperture is climbable

The preceding section is correct about the *parked* geometry and wrong about the
conclusion it drew from it. The question it left open — "may the front element
enter the aperture?" — was answered this session by probing the solid model rather
than by reasoning about the parameter names.

**Measured.** Probe cylinders up to Ø25 mm rise unobstructed from z = 0 to
z = 11.71 at every tile aperture centre. The column above the aperture is clear to
**0.02 mm** of the glass outer surface (z = 11.73), i.e. to **0.19 mm** below the
cell plane (z = 11.90). *(Corrected 2026-09-23 — this read "0.19 mm of the glass
outer surface", which conflated the two: 11.73 − 11.71 = 0.02 is the gap to the
glass, and 11.90 − 11.71 = 0.19 is the gap to the cell plane.)* Nothing —
not the base, not the plate-support land, not the locator walls — occupies the
aperture column. The 88 × 52 mm through-aperture is a hole, and the head can climb
it.

**Consequence: the WD path is 19.90 → 7.90 mm, with no CAD change.** The existing
`focus_stroke_z = 12.0`, run *upward* from the traverse plane instead of downward,
puts the nose at z = −8 + 12.0 = **+4.00**, i.e. WD = 11.90 − 4.00 = **7.90 mm**.
The vertical budget this spends is `carriage_top_clearance_z` 8 +
`front_end_height_z` 28 + `focus_stroke_z` 12 = **48 mm** against
`observer_sweep_depth_z` = 80, leaving **32 mm of slack**. The travel already
exists in the parameter file; only the direction it is spent in was assumed.

| Standoff | Nose z | WD | Objective class that reaches |
|---|---:|---:|---|
| Parked (traverse plane) | −8.00 | **19.90 mm** | long-WD, zero-coverslip (Mitutoyo M Plan Apo class) |
| Risen, full `focus_stroke_z` | +4.00 | **7.90 mm** | ELWD correction-collar class (Nikon CFI S Plan Fluor ELWD 20×/0.45, WD 6.9–8.2 mm) |

**Cost: retract cycles, but per tile, not per well.** Between tiles the
`plate_support_frame` occupies z = 0 … 11.20 and blocks a risen nose at
z = 0.05. Crossing a tile boundary therefore requires a full retract to below
z = 0 and a re-raise: **3 retract/re-raise cycles per row of 4 tiles**. *Within* a
tile's aperture the nose stays raised for every well it can reach. This is a
throughput term of tens of cycles per pass, not thousands, and it is the price of
the 2.5× WD reduction.

**Safety follows directly.** At the ELWD 40×/0.60 end (WD 2.8–3.6 mm to the cell
plane at z = 11.90) the nose sits at z = 8.3 … 9.1 — **2.6–3.4 mm below the
coverslip, and 0.9–1.7 mm below the plate bottom at z = 10.0.** That is inside the
aperture, under a **consumable** plate an operator swaps by hand. Recommend a hardware
Z-gate that cuts XY motor enable whenever the nose is above z = 0 — interlock, not
firmware convention. *(Recommendation for the motion-control owner; no code
changed in this pass.)*

**What this supersedes.** Not the geometry above, which is right, but two verdicts
drawn from it: the 2026-09-21 withdrawal of the 10× objective ("the NA ladder above
0.10 has no documented member that physically reaches focus") and the claim that
long-WD is the *only* admissible class. Both hold at the parked height and neither
holds at full stroke. The withdrawn 10× is reinstated as a bench candidate on the
risen geometry — see the BOM note.

## The aberration ceiling is a correction-collar question, not a glass-thickness one

The section above derives the NA ceiling from `W_pv ≈ t(n²−1)/(8n³)·NA⁴`. Carrying
that through the Maréchal criterion (diffraction-limited while W_rms ≤ λ/14, i.e.
W_pv ≤ λ/4 for this aberration form) with t = 0.17 mm, n = 1.5185:

```
t(n²−1)/(8n³) = 170 µm × 1.3058 / 28.012 = 7.925 µm
so  W_pv = 7.925 · NA⁴  µm,  and  W_pv = λ/4  gives  NA = (λ/31.70)^¼
```

| λ | NA cap from 0.17 mm of **uncorrected** cover glass |
|---:|---:|
| 405 nm | **0.336** |
| 550 nm | **0.363** |
| 785 nm | **0.397** |

**This caps uncorrected objectives only.** A correction collar re-spaces the
objective's internal groups to cancel the slab's spherical aberration; with the
collar set to 0.17 mm the cap does not apply. That single fact reorganises the
catalogue:

- **Long-WD catalogue objectives are zero-coverslip designs.** Mitutoyo's M Plan
  Apo line is specified for imaging in air with no cover glass. The catalogue
  M Plan Apo 20×/0.42, WD 20 mm, reaches the cell plane from the *parked* standoff
  — and lands **1.79× over the Maréchal budget** through 0.17 mm of glass when it
  gets there. Reaching focus and being diffraction-limited at focus are two
  different acceptances, and this class passes the first and fails the second.
- **At WD ≈ 7.9 mm the ELWD correction-collar class applies.** Catalogue examples:
  Nikon CFI S Plan Fluor ELWD 20×/0.45, WD 6.9–8.2 mm, collar 0–2 mm; and
  40×/0.60, WD 2.8–3.6 mm, collar 0–2 mm. These are corrected *and* long enough for
  the risen standoff, which is exactly the combination the parked geometry could
  not offer.

*(Catalogue WD/NA/collar figures are vendor specifications, quoted not measured.
The Maréchal caps are derived from the formula above and are this repo's
arithmetic.)*

So the admissible-NA question decomposes into two independent gates, and the
document must stop conflating them:

1. **Reach** — does the nose get within WD of z = 11.90? Answered by the standoff,
   now 19.90 or 7.90 mm depending on stroke direction.
2. **Correction** — is the objective corrected for the 0.17 mm it is looking
   through? Answered by the collar, not by the geometry.

## What NA actually buys

Every number below is at λ = 550 nm, emitter in aqueous media (n = 1.335), sensor
IMX178 (2.4 µm pixels, 3088 × 2064, 7.41 × 4.95 mm active).

| NA | Collected fraction of 4π | Abbe λ/2NA | DOF λ/NA² | M for Nyquist |
|---:|---:|---:|---:|---:|
| 0.10 | 0.140 % | 2750 nm | 55.0 µm | 1.75× |
| 0.363 (Maréchal cap) | 1.884 % | 758 nm | 4.17 µm | 6.34× |
| 0.45 | 2.926 % | 611 nm | 2.72 µm | 7.86× |
| 0.60 | 5.334 % | 458 nm | 1.53 µm | 10.5× |
| 0.95 (dry ceiling) | 14.871 % | 289 nm | 0.61 µm | 16.6× |
| 1.20 (water) | 28.090 % | 229 nm | 0.38 µm | 21.0× |
| 1.335 (= n_media) | 50.0 % | 206 nm | — | — |

**Collection.** The collected fraction is `(1 − cos(asin(NA/n_media)))/2` with
n_media = 1.335, because the emitter sits in media, not in air. *(This supersedes
the `NA²/4` form. `sensor_module_interface.md` was corrected to the media-side cap
fraction on the same date — see its "(1) Collection fraction — the correct,
media-side form" section, which strikes the old table through at :73-77 and
re-derives η at :84-105. **Closed 2026-09-23:**
`docs/knowledge/byonoy_plate_readers.md` carried the same air-side form in two
places — "the NA²/4 ≈ 0.25 % collection penalty" and "we collect ~0.25 % of 4π" —
and both were corrected to **0.140 %** in the same pass, with a dated correction
block recording that neither argument on that page weakens. No file still quotes
the air-side form as live.)* Against the NA 0.10 path
the ladder buys **20.8× at NA 0.45, 38.0× at NA 0.60, 200× at NA 1.20**.

**The ladder ends at water, not at oil.** The cone half-angle is set by
`asin(NA/n_media)`, and asin is undefined above NA = n_media = 1.335. A nominal
1.40 NA oil objective imaging live cells in aqueous media is therefore effectively
NA 1.335 — the media index itself. The oil buys nothing over water for this sample,
because the sample is water. The realizable top of the ladder is a water-immersion 1.20–1.27.

**Sampling: the tube lens, not the objective, sets it.** See the next section. At
the current f_tube = 50 mm the M for Nyquist column is unreachable for every NA on
the ladder except by changing the tube lens.

*(DOF here is the air-side wave-optical form λ/NA². Multiply by n_media = 1.335
for the corresponding depth inside the specimen. The repo has quoted both; state
which one, always.)*

**Tiling: the throughput term nobody has costed.** At NA 0.60 on a nameplate 40×
Nikon ELWD (**M_eff 10.0×**, f_ref 200 — see the tube-lens section next) the
sampling is 2.4/10.0 = 0.24 µm/px and the field is 0.741 × 0.495 mm =
**0.367 mm²**. A Ø6.18 mm well (`well_bottom_area_equivalent_diameter`) is
30.0 mm² — **~82 tiles per well.**
Across the 128 optically reachable wells that is ~10,500 tiles per pass; at an
optimistic 0.4 s/tile, **~1.2 h per pass**. Enlarging the aperture to reach all
384 (below) triples it to ~31,400 tiles and **~3.5 h**. Neither fits an hourly
perturbation cadence. Storage follows from the same arithmetic: 3088 × 2064 at
16 bit is 12.7 MB per frame, so ~133 GB per pass at 128 wells and **~6.4 TB over
48 hourly passes**. *(Recomputed 2026-09-23 from M_eff 11.11× to 10.0×: this
paragraph inherited the Olympus divisor while naming a Nikon head. The old figures
were 0.216 µm/px, 0.298 mm², ~101 tiles/well, ~164 GB and ~7.9 TB — ~24 % high on
tile count and storage. `sensor_module_interface.md`, § *A second candidate from the
same session: `fields_per_well` as an explicit Evidence sampling parameter*, carries
the 11.11× per-well term at the **same 128-well basis as this paragraph** — a 1.23×
tube-lens-convention difference, not a disagreement about well count, and that file
states both conventions side by side. **Closed 2026-09-23:** `remaining_work.md`
(SM-4.5, and the Track-6 roll-up under "Recommended next 3 cycles") previously carried
the same arithmetic on a **192-well basis**; it was corrected in this same pass to the
128-well basis and states the 192-well figures as withdrawn. No file still carries
192.)* The resolution
is not a faster stage: it is making **N random fields per well** a first-class Evidence
sampling parameter, so that tile count is a chosen statistic rather than a
consequence of well area. *(Recommendation for the Evidence-contract owner; out of
scope for this file.)*

## The tube lens sets every magnification number in this document

This is a load-bearing premise that was previously buried in one table cell, and
every sampling, FOV and tile-count figure in this document silently depends on it.

**An infinity objective's nameplate magnification is only realised at the tube
focal length its maker assumes.** With f_tube = 50 mm in this bench against a
reference f_ref = 180 mm (Olympus-convention RMS parts, which is what the Taobao
4× is):

```
M_eff = nameplate × f_tube / f_ref = nameplate × 50 / 180 = nameplate / 3.6
```

For Nikon and Mitutoyo (f_ref = 200 mm) the divisor is 4, and the two cases must
be kept apart because they differ by 11 %:

| vendor convention | f_ref | divisor | nameplate 40× → | nameplate 4× → |
|---|---:|---:|---:|---:|
| Olympus (the RMS 4× fitted today) | 180 mm | 3.6 | **11.11×** | **1.11×** |
| Nikon / Mitutoyo | 200 mm | 4.0 | **10.0×** | **1.00×** |

*(Corrected 2026-09-23 — this paragraph previously read "the divisor is 4. So a
'40×' objective on this bench runs at M_eff 11.11×", which applies the Olympus
divisor to the Nikon/Mitutoyo sentence. 40/4 = 10.0.
`sensor_module_interface.md`, § *Optical — the infinity port (FROZEN)*, the bullet
"Sampling: the f = 50 mm tube lens is the throughput/resolution decoupler", already
stated the range correctly as "M_eff 10–11.11×".)*

**Which one this document assumes.** The 40×/0.60 head named above is the **Nikon
CFI S Plan Fluor ELWD**, f_ref 200 — so every tile, sampling and storage figure in
this file for that head is computed at **M_eff 10.0×**, not 11.11×. The 4× primary
fitted today is an Olympus-convention RMS part and runs at **1.11×**.

Two consequences the document must carry explicitly:

- **High NA costs almost nothing in throughput here, and buys almost nothing in
  resolution, unless the tube lens changes.** The short tube lens is what lets 4×
  see most of a well; it is also what guarantees the system is sampling-limited
  rather than diffraction-limited at every NA on the ladder.
- **The 50 mm tube lens is a design choice under review, not a constant.** Any
  future resolution claim must state f_tube alongside the nameplate, or it is not
  a claim about this instrument.

## The thermal gate: a close objective is a heat sink into the well

Climbing the aperture buys NA and creates a gate this document did not previously
have. The objective is a large, well-conducted metal mass at bay ambient, brought
to within millimetres of a 37 °C well. It sinks heat out of the sample.

Steady-state cell-plane temperature, 37 °C bath over 25 °C bay, for four candidate
heads:

| Head | WD | Cell-plane T | ΔT | vs 0.3 K budget |
|---|---:|---:|---:|---|
| water 60×/1.20 | 0.31 mm | 29.50 °C | **7.50 K** | fail |
| dry 40×/0.95 | 0.18 mm | 35.04 °C | **1.96 K** | fail |
| dry 40×/0.60 | 3.0 mm | 36.77 °C | **0.23 K** | **pass** |
| dry 20×/0.45 | 7.5 mm | 36.85 °C | **0.15 K** | **pass** |

**Every head closer than roughly 3 mm fails, dry included.** Both terms bind, and
the table says which is which. *Within* the dry column ΔT rises as the gap closes
(7.5 mm → 0.15 K, 3.0 mm → 0.23 K, 0.18 mm → 1.96 K), so proximity governs there.
*Across* media the medium sets the scale: the water head loses **7.50 K through a
0.31 mm couplant column** while the *closer* 0.18 mm air gap loses 1.96 K, because
the couplant conducts far better than air. Immersion is therefore the larger term —
and dry still does not make a close head safe, since the dry 40×/0.95 row misses the
0.3 K budget by 6.5× on proximity alone. That row, not the water row, is what
carries the conclusion. *(Clause corrected 2026-09-23 — it previously read "the
governing term is proximity, not medium", which the table directly above
contradicts: the farther water head is the hotter loss.)*

**Why 0.3 K is a gate and not a comfort target.** This platform exists to fit
causal models of perturbation response. A cooled well is an *unlogged thermal
perturbation whose magnitude is correlated with which wells get revisited and how
often* — exactly the structure that manufactures a spurious cause. A confounder
that tracks the sampling schedule is worse than a larger one that does not.

**Mitigation is a heated nose, not a heated bay.** A local 37 °C objective heater
removes the gradient at its source. Warming the whole dry bay to 37 °C does not:
IMX178 dark current roughly doubles per 6–7 K, which spends the long integrations
that the Raman and luminescence budgets in `sensor_module_interface.md` are
reserved for. Commercial confirmation that the local approach is the industry
answer: Opera Phenix Plus and Yokogawa CellVoyager CV8000 both run automated water
immersion from below through glass-bottom plates, and both condition/heat the
objective. *(Vendor architecture, quoted not measured.)*

> **Caveat, stated plainly.** The model above uses an **estimated**
> `G_obj-ambient = 50 mW/K` for the objective-to-bay conductance. The *ordering* of
> the four rows is robust to that estimate; the absolute ΔT is not. This is the
> **highest-value early measurement on the whole observer programme** — a
> thermocouple in a well and a dummy aluminium nose on the Stage-0 bench settles it
> for the price of an afternoon. It is added to the Stage-0 protocol's Phase C.

### Focus follows from the thermal and NA sections, not from structural stiffness

Raising the NA collapses the depth of field: λ/NA² gives **4.17 µm at the
Maréchal-capped 0.363, 2.72 µm at 0.45, 1.53 µm at 0.60** — against 55 µm at the
current NA 0.10. That changes what the focus system is for.

The instinct is to chase temporal drift, and the printed structure does drift: over
an 80 mm leg, PLA moves 5.60 µm/K, PETG 4.80, ABS 7.20, aluminium 1.84, steel 0.96,
invar 0.10. *(Per-material CTE budget is the structural owner's number; quoted here
only to size the comparison.)* But **the operative driver is plate-to-plate
topography and seating, not drift**: at a 1.53 µm depth of field you must refocus at
every well visit no matter how stable the structure is. A stiffer, lower-CTE leg
buys a slower *rate* of refocus error, not the elimination of refocus.

**Recommended architecture: through-objective dual-surface IR autofocus on the
coverslip** (reflections off the glass's two faces give an absolute, sample-
independent focus reference). **Build it FIRST as an open-loop drift gauge, before
any loop is closed.** An open-loop gauge is falsifiable — it produces a logged
error signal that can be compared against DOF — while a closed loop hides the
thing being measured inside its own correction.

## Reachable wells, and the "nothing under any well" contradiction

This document asserts in two places (and the Stage-0 protocol in a third) that the
observation window is "open from below — **nothing under any well, skirt flange
only**". **Measured 2026-09-23: the geometry does not satisfy that principle.**

**The arithmetic.** A 96-well plate's well centres span 99.0 mm in X
(11 × 9.0 pitch) and 63.0 mm in Y (7 × 9.0). To have nothing under any well, the
aperture must clear that span plus one well diameter:

| Ruling diameter | Required aperture | Actual (`dry_bay`) | Deficit, both axes |
|---|---|---|---:|
| `lower_well_diameter` 6.21 (clear glass bottom) | 105.21 × 69.21 | 88 × 52 | **17.21 mm** |
| `upper_well_diameter` 6.80 (moulded well OD) | 105.80 × 69.80 | 88 × 52 | **17.80 mm** |

The session measurement quotes 105.4 × 69.4 and a **17.4 mm** deficit on both
axes; the bracket above is the same finding under the two defensible well
diameters. *(Added 2026-09-23: 105.4 − 99.0 = 6.4 mm implies a ruling well diameter
of 6.4 mm, which matches no parameter in the repo, and `decision_log.md` has since
**withdrawn 6.4 mm and 17.4 mm** for that reason. They are retained here only as the
session's as-measured quote; the table above is the figure to cite.)* Either way the conclusion is identical and large: `plate_support_frame`
material sits under **well columns 1 and 12 and rows A and H**.

**The principle is not retracted.** "Nothing under any well" is the right rule —
it is what makes the plate a consumable that can be dropped in and imaged
anywhere. What is recorded here is that the **current geometry violates it**, by
~17 mm on both axes. One site in this file still states the clause aspirationally
rather than descriptively: the 2026-09-21 correction block above, which quotes the
original cradle spec verbatim and carries the "Note added 2026-09-23" that flags
it. The other site — Assembly step 2 below — **has been corrected**; its cutout is
now ≥ 107 × 71 mm.

**Optically reachable wells: 128 of 384, not 240 and not 384.** The 240 figure
that has circulated counts well *centres* falling inside the 88 × 52 aperture and
ignores that something has to pass through the hole — either the optical cone or
the physical nose.

- *Long WD (19.90 mm, parked).* The cell plane is 11.90 mm above the aperture's
  lower plane (z = 0). At the Maréchal-capped NA 0.363 the cone there is
  2 × 11.90 × tan(asin(0.363)) = **9.27 mm** wide, so a usable well centre must sit
  **4.64 mm** inside the aperture edge.
- *Short WD (7.90 mm, risen).* The cone shrinks, but a physical nose of OD
  8–20 mm now occupies the hole, giving an inset of 4–10 mm.

Both regimes land in the same inset band and therefore on the same answer: **8 of
12 columns and 4 of 8 rows per plate = 32 wells × 4 plates = 128 of 384.** The
identity of the two results is the useful part — the reachable count is a property
of the *aperture*, not of the optical choice, so no objective selection improves
it.

**The fix is one number.** Enlarging the per-tile aperture to approximately
**110 × 74 mm** simultaneously gives 384/384 reachable wells and satisfies the
"nothing under any well" principle. *(Recommendation only — `dry_bay.aperture_*`
is CAD geometry and is not changed in this documentation pass. It is a structural
change before it is an optical one: the frame has to survive losing ~22 mm of land
on each axis, which is a stiffness question for the row-module owner.)*

**The bench cradle follows the same arithmetic.** Assembly step 2 below used to
specify a "central cutout ≥ 90 × 54 mm so the full 88 × 52 mm observation window is
open from below — nothing under any well". Those two clauses contradict each other
for exactly the reason above: 90 × 54 clears the *aperture*, not the *wells*. The
bench cradle is a printed part with no structural constraint, so **it is corrected
there to ≥ 107 × 71 mm** — which honours the principle, and lets the bench measure
the outer wells the bay as ruled cannot reach. The paired protocol
(`../protocols/observer_optical_bench_stage0.md:62`) and the blank record sheet
(`../../data/measurements/templates/observer_optical_bench_stage0.md`, Pre-Run Checks
row "Plate seated skirt-only in a cradle whose central cutout is >= 107 x 71 mm")
carry the same number. The **bay** aperture is unchanged and still violates the principle.

## The 15.56 mm corridor is an artifact of scanning wells the head cannot reach

`observer_robotics.scan_corridor_footprint_max = 15.56` is the head-width budget
that currently rejects every interesting objective. It is not a physical limit.

**Where 15.56 comes from.** It is the residual after requiring the head to scan
**all 12 well columns** — a 99.0 mm sweep — inside the leg corridor (117.4 mm
clear, inner faces at X 17.10 and 134.50).

**Why that requirement is void.** The 88 mm aperture never admitted 12 columns. It
admits **8**, spanning 63.0 mm, at X 42.88 … 105.88. The traverse check is
enforcing clearance for a scan across wells the optics cannot see, because solid
base material is in the way.

**Budget against the reachable set:**

```
min( 2 × (42.88 − 17.10), 2 × (134.50 − 105.88) )
= min( 51.56, 57.24 ) = 51.56 mm
```

**15.56 → 51.56 mm, a 3.3× increase, from parameterising the traverse check by
reachable columns instead of nominal columns. No CAD change, no geometry moved.**
The array is not centred in the corridor, so the near (−X) wall binds; that is what
the `min` picks up. Note the coupling: if the aperture is enlarged to 110 × 74 to
recover all 384 wells, the reachable span returns to 99 mm and this budget returns
toward 15.56. **The wide aperture and the wide head are alternatives, not a
package** — that trade is the observer's central architectural choice and it
should be made deliberately, not inherited.

This matters because `src/aevum_cad/row_coupon/parts/observer.py:184-193`
currently states that the residual after
the well span is "~0.2 mm, not 120 mm — the camera must be folded coaxially over
the objective or taken offboard." That conclusion is downstream of the wrong span.
**Recommendation for the code owner: parameterise the traverse check by reachable
columns.** *(No code changed in this pass.)*

## Build-out trajectory: how the bay gets filled

The bench is Stage 0 of a staged physical build-out. Each stage is a real build
inside (or representing) the bay envelope, produces Gate 6 evidence, and converts
a validation-only envelope into an installed part plus a measured parameter.

| Stage | What gets built | Proves (Gate 6 evidence) | Envelope → part | Param pinned |
|---|---|---|---|---|
| **0 — Static focus cell** (this doc) | One optical head fixed under one well, real plate, real media, real illumination | Focus on cell plane through 0.17 mm glass + media; signal/contrast; real WD + head footprint; condensation behavior; field flatness | *(measurement)* | kills `observer_sweep_extra_x/y`; sets `front_end_*` |
| **1 — Focus (Z) axis** | The 12 mm focus actuator under the head | Repeatable autofocus on the cell plane | `focus_stroke` → real axis | `front_end_focus_stroke_z` |
| **2 — One-plate scan** | XY traverse over one plate (96 wells) | Repeatable focus across wells, field flatness across the plate, settle time; the real moving-head + carrier envelope | `front_end_swept_body` + carriage (one plate) → real gantry | front-end swept body, carriage footprint |
| **3 — Full-row scan** | Extend Y to 334.5 mm, all 4 plates / 384 wells — **but only 128 of those wells are optically reachable through the 88 × 52 aperture (measured 2026-09-23); see "Reachable wells"** | **The make-or-break:** does a 62 mm-tall carrier + gantry fit AND traverse the full bay without hitting deck feet, inside 80 mm | `observer_kinematic_split_check` → proven traverse | resolves the carriage-traversal gap |
| **4 — Service / stability / install** | Raceway as real cable chain; vibration; thermal; 5-cycle install-remove | `observer_optical_stability_check`, dry-bay ingress, service-loop recovery | raceway + stability → real parts | closes remaining Gate 6 |

Stage 0 is described in full below. Stages 1–4 are scoped at the end under "What
Stage 0 does not prove."

---

## Stage 0 — the optical bench

### What it physically is

A static, single-station inverted microscope built upside-down on an optical
breadboard: one CellVis P96-1.5H-N plate held level and skirt-only in a printed
cradle ~90 mm above the board, a complete COTS optical head on a manual XYZ stage
*below* it pointing up, and a movable programmable LED source on an arm above. No
motion, no OT-2. The cradle's plate-bottom datum **is** the bay's plate-support
plane; the head's vertical envelope below it **is** the front-end swept body's
straight-down portion; the stage's Z **is** the focus stroke; the stage's XY is
the future scan, exercised by hand. The bench is, literally, the bay at one well.

It answers one existential question — **can an inverted head focus on cells on the
top of the 0.17 mm coverslip, from at least 8 mm below the plate bottom, through
the real wet boundary, and at what working distance and head footprint** — and
produces the caliper numbers that retire the fudge factors. Illumination fork,
condensation, field flatness, and tiling count are first-class secondary outputs
of the same rig.

### Optical configuration (decisive, no options)

Infinity-corrected **4× plan-achromat RMS objective** (NA 0.10, WD ~22 mm,
0.17 mm cover-glass corrected) → ~40 mm collimated/infinity space holding **one
45° first-surface fold mirror** → **f = 50 mm achromatic doublet tube lens** →
**mono CMOS, Sony IMX178** (1/1.8", 2.4 µm pixels, 3088 × 2064).

> **Corrected 2026-09-21 — the 10× upgrade is withdrawn.** A 10× infinity
> plan-achromat (NA 0.25, **WD ~8 mm**) was listed here as "the single parfocal
> upgrade". It cannot reach the cell plane in the bay-as-ruled, where the standoff
> is **19.90 mm**. It remains usable on the static bench only if the cradle is built
> to the ~8 mm clearance (head inside the aperture) — which is a different geometry
> from the bay. The NA ladder above 0.10 therefore has **no documented member that
> physically reaches focus**; the objective spec is NA ≥ 0.40 at **WD > 19.90 mm**,
> which no RMS-threaded part satisfies at a barrel the 15.56 mm corridor admits.
>
> **Superseded 2026-09-23 — the 10× is reinstated as a candidate, and the "different
> geometry from the bay" clause is what was wrong.** Head-inside-the-aperture *is*
> the bay: probe cylinders to Ø25 rise clear from z = 0 to z = 11.71 at every tile
> aperture centre, and `focus_stroke_z = 12.0` run upward puts the nose at z = +4.00
> for **WD 7.90 mm**. A ~8 mm-WD objective reaches focus in the bay as parameterised
> today. The bench cradle should therefore be built to replicate **both** standoffs
> (see gate (a′)), not to choose between them. The two constraints that survive are
> the ones this note did not state: the **correction collar** (an uncorrected
> objective is capped at NA 0.363 whatever its WD) and the **thermal gate** (a nose
> closer than ~3 mm cools the well past 0.3 K). Both are below.

A programmable **WS2812 16 × 16 LED matrix** above the plate resolves the
illumination fork.

> **Corrected 2026-09-23 — the sampling row and the FOV row contradicted the
> magnification row in the same table.** The table read "~0.6–1.4 µm/px" and
> "~5.6 × 4.2 mm" beside an effective magnification of ~1.1×. Those three cannot all
> be true: 2.4 µm pixels at M 1.11× sample at 2.16 µm/px and cover the whole
> 7.41 × 4.95 mm sensor as 6.67 × 4.46 mm at the cell plane. The old sampling figure
> is roughly what a *nameplate* 4× would give (2.4/4 = 0.6 µm/px) — it was the
> nameplate number left in a table whose other rows had already been divided by 3.6.
> Corrected below, and the tube-lens premise that causes this is now stated
> explicitly in its own section above. **The consequence is not cosmetic: at
> 2.16 µm/px the system undersamples its own NA 0.10 optics by ~1.6×, so this bench
> is sampling-limited, not diffraction-limited.**

| Quantity (4× primary, IMX178) | Value | Derivation | Consequence |
|---|---|---|---|
| Effective magnification | **1.11×** | 4 × f_tube 50 / f_ref 180 | demagnified onto the small sensor |
| Sampling at cell plane | **2.16 µm/px** | 2.4 µm / 1.11 | a 10–20 µm cell spans 5–9 px — countable, not morphologically resolved |
| Optical resolution, NA 0.10 | **2.75 µm** Abbe (λ/2NA), **3.36 µm** Rayleigh (0.61λ/NA) | λ = 550 nm | confluence + gross morphology (not organelles). *The old "~3.4 µm" was the Rayleigh figure; both are quoted here because the NA tables elsewhere in this repo use Abbe — state the criterion.* |
| **Sampling vs optics** | **undersampled ~1.6×** | Nyquist needs 2.75/2 = 1.375 µm/px, i.e. M ≥ 1.75×; the bench has 1.11× | resolution here is set by the sensor, not the objective |
| FOV at cell plane | **6.67 × 4.46 mm** | 7.41 × 4.95 mm active / 1.11 | the full 6.21 mm well fits in one frame in X and needs 2 tiles in Y |
| Depth of field, NA 0.10 | **55 µm total (±27 µm)** | λ/NA² | swallows plate tilt/sag; forgiving focus. *The old "±55 µm" double-counted: 55 µm is the full depth. The ±27 µm quoted under "What Stage 0 does not prove" was the correct half-depth.* |
| Working distance | **~22 mm** | catalogue | reaches the cell plane from the **parked** standoff (19.90) with 2.1 mm spare; see the climbable-aperture correction for the risen case |
| Straight-down Z (objective parfocal ~45 + fold mirror ~15) | **~60 mm ≤ 62 mm** | estimate, caliper-gated | **fits**, tube lens + camera routed horizontally |
| Front barrel diameter | **≤ 25 mm < 32 mm** | catalogue vs `objective_keepout_diameter` | inside the objective keepout |

**Why this train and not the alternatives, one line each:**

- **Finite 160 mm DIN objective → sensor: disqualified by geometry.** A finite DIN
  objective has a ~195 mm object-to-image conjugate; it cannot be packaged in
  62 mm even Z-folded, and projected onto a bare sensor it images at the wrong
  conjugate (field curvature / chromatic aberration).
- **Infinity objective + short tube lens: the winner.** The collimated segment
  between objective and tube lens is the only aberration-free place to put the
  fold mirror — and later a dichroic or beamsplitter for the reserved Raman/
  fluorescence budget. The short 50 mm tube lens is the lever that demagnifies the
  well onto a small sensor so 4× sees nearly the whole well.
- **Telecentric/reversed CCTV macro: rejected** — too long (>110 mm), expensive,
  and not cover-glass corrected.
- **Integrated USB-microscope module: rejected** for production evidence — fixed
  plastic optics, no defined NA/WD, useless for replacing the CAD fudge factors.
  Acceptable only as a throwaway "does anything image at all" pre-check.
- **Mono over color sensor:** unstained cells carry no color; mono keeps full
  resolution (no demosaic) and full sensitivity for a photon-starved low-contrast
  target.

**Z-budget fit, quantified.** Unfolded, the path (objective ~45 + ~50 to tube lens
+ tube lens + sensor) is >110 mm and does **not** fit. Folded once, only the
objective barrel (~45 mm) and the fold mirror (~15 mm) stack vertically — ~60 mm,
inside the 62 mm envelope with ~2 mm spare — while the tube lens and camera lie
horizontally along the 100 mm carriage length and cost zero vertical budget. **One
fold is mandatory; one fold is sufficient.** This is the geometry the bench must
confirm with calipers, not trust as an estimate.

### Illumination — the architectural decision the bench forces

Unstained adherent cells are phase objects with near-zero amplitude contrast in
plain brightfield. The fork:

| Mode | How | Cost to Aevum | Label-free contrast |
|---|---|---|---|
| **Transmitted (from above)** | LED + diffuser above the plate, through the media column | **HIGH** — the top is the sealed wet chamber + gas/septum manifold; this commits an optical window competing with that manifold | Best, but plain brightfield still weak without phase tricks |
| **Epi / reflected (from below, through objective)** | Coaxial source + beamsplitter in the head | **LOW** — fully module-side; but glass-bottom + cells reflect weakly (~75 % double-pass loss) | Poor for brightfield; really the future fluorescence path |
| **Oblique (from below, off-axis)** | Off-axis LED below, into the well at an angle | **LOW** — module-side, no top window | Good — pseudo-phase-gradient contrast on transparent cells, cheaply |

A single **WS2812 16 × 16 LED matrix** tests the entire fork without rebuilding:
center pixels → brightfield, one quadrant → oblique, a ring → darkfield — and the
same array enables computational phase later. This ~¥40 part is the highest-leverage
purchase on the list.

**Production recommendation:** adopt **module-side oblique illumination** (LED
matrix or annular ring in the dry bay, off-axis around the objective). It respects
the sealed top, honors the non-contact rule, gives label-free contrast cheaply, and
keeps the epi/coaxial port and the 80 mm Raman budget free for the future
biophotonics path. Reserve transmitted-from-above as the fallback **only** if the
bench shows oblique-from-below is inadequate through the media column.

### Bill of materials

USD at ¥7.1. *(Recomputed 2026-09-23 — both headline totals were quoted without
saying which rows they included, and neither reproduced from the table.)*

- **Core 4× build = ¥1,940 ≈ $273.** Every non-parenthesised row below **except**
  the ¥250 10× upgrade — i.e. excluding the (250) IMX179 alt, the (120) beamsplitter
  and the uncosted ELWD candidate.
- **Recommended first purchase = ¥1,265 ≈ $178** (the subset named under the table).
- **Core + 10× = ¥2,190 ≈ $308.**

The superseded figures were ¥1,885 ≈ $266 core and ≈ $230 first purchase.

| Part | Spec | Taobao term (中文) | ~¥ |
|---|---|---|---|
| **4× objective** (primary) | infinity plan-achromat, RMS, NA 0.10, WD ~22 mm, 0.17-corrected | `无限远物镜 4X 平场消色差 RMS` | 150 |
| **10× objective** (upgrade) | NA 0.25, WD ~8 mm. ~~WITHDRAWN 2026-09-21~~ **REINSTATED 2026-09-23** — WD ~8 mm reaches the cell plane at the risen standoff (WD 7.90 mm at full `focus_stroke_z`), which is the bay geometry, not a bench-only one. Buy it to exercise gate (a′) at both standoffs. | `无限远物镜 10X 平场消色差` | 250 |
| **ELWD correction-collar objective** *(candidate, not costed)* | 20×/0.45, WD 6.9–8.2 mm, collar 0–2 mm — Nikon CFI S Plan Fluor ELWD class. The collar is what removes the NA 0.363 Maréchal cap, and this is the class the risen standoff opens. Catalogue spec only: no Taobao source identified, no price claimed. | — | — |
| **Tube lens** | achromatic doublet, f = 50 mm, Ø25, AR-coated | `消色差双胶合透镜 焦距50mm Φ25` | 60 |
| **Camera** (primary) | mono, Sony IMX178, 1/1.8", 2.4 µm px, C-mount USB3 | `IMX178 工业相机 黑白 C口 USB3` | 500 |
| Camera (cheap first-light alt) | color IMX179 8 MP USB board cam | `IMX179 USB摄像头模组` | (250) |
| RMS→C adapter | RMS male to C-mount | `RMS转C口 转接环` | 20 |
| C-mount extension/focus tubes | set, to set tube-lens→sensor = 50 mm | `C口延长筒 调焦筒` | 50 |
| **45° fold mirror** | 25 mm protected-aluminum **first-surface** | `第一表面反射镜 45度 25mm` | 40 |
| Right-angle mirror mount | kinematic (or print a 45° wedge) | `直角反射镜架 KCB1` | 80 |
| **Manual XYZ stage** | ≥10–15 mm travel/axis, ≤10 µm/div | `三维位移台 手动 微调 行程13mm` | 250 |
| **Z differential micrometer head** | ≤1 µm/div (for 10× focus) | `差动测微头 0.5um` | 120 |
| **Optical breadboard** | 300×300, M6 grid, ~12 mm Al | `光学面包板 300x300 M6` | 280 |
| Posts + clamps | Ø12–25 stainless, assorted | `光学支柱 Φ25 + 支杆夹` | 120 |
| **LED matrix** (programmable source) | WS2812 16×16, drive w/ any MCU | `WS2812 16x16 LED点阵` | 40 |
| Diffused LED panel | transmitted reference | `LED面光源 漫射` | 40 |
| LED ring | ring-oblique / darkfield | `环形光源 LED` | 50 |
| Frosted diffuser sheet | acrylic / drafting film | `漫射片 亚克力 磨砂` | 15 |
| Plate cradle | printed PETG or laser-cut acrylic | `亚克力 激光切割 定制` (or self-print) | 30 |
| USAF target | resolution test board | `USAF 1951 分辨率测试板` | 80 |
| Hemocytometer | 50 µm grid fiducial | `血球计数板` | 15 |
| (Future epi) beamsplitter | 50:50 cube for collimated space | `分光棱镜 50:50` | (120) |

**Recommended first purchase (¥1,265 ≈ $178):** 4×, tube lens, IMX179 board cam, RMS→C
adapter, extension tubes, XYZ stage, small breadboard, posts, LED matrix,
diffuser, cradle. Build straight, point up, prove the well images through real
media and see condensation. Then add the 10×, the mono IMX178, the fold
mirror/mount, and the ring light to finalize the 62 mm-fit and illumination-fork
answers.

### Assembly

1. **Breadboard + datum.** Lay the 300×300 board on sorbothane feet / a heavy
   slab. Everything bolts to this single board so the cradle and head share one
   mechanical ground and drift together. On a static bench the µm-scale enemy is
   thermal drift, not floor vibration — let it settle ~15 min after handling and
   don't hold the posts (hand heat = drift).
2. **Plate cradle.** Print/cut an open picture-frame the plate skirt drops into,
   registering on two adjacent fixed datum walls (+X, +Y) plus one sprung/foam
   corner pusher (−X, −Y). Central cutout **≥ 107 × 71 mm** — **corrected
   2026-09-23**: this step used to say "≥ 90 × 54 mm so the full 88 × 52 mm
   observation window is open from below", which does not achieve the **nothing
   under any well, skirt flange only** that the same sentence demands. The 96-well
   centres span 99.0 × 63.0 mm, so clearing every well needs that plus a well
   diameter (105.21 × 69.21 at `lower_well_diameter` 6.21). The printed cradle has
   no structural constraint, so cut it to the wells — and gain the outer wells the
   bay's 88 × 52 aperture cannot reach. Mount on two posts so the plate-bottom
   plane sits ~90–100 mm above the
   board (≥70 mm clear underneath). Level to <0.1° with three M4 set-screw feet and
   a phone bubble level.
3. **Optical head, built straight first (Phase A de-risk).** Assemble as one rigid
   C-mount column pointing **up**: objective → RMS→C adapter → C-mount extension
   tubes → f = 50 mm tube lens → camera. Set **tube-lens-to-sensor = 50 mm** with
   the extension rings (the one critical spacing; objective-to-tube-lens is
   forgiving infinity space). Clamp the column in a post holder on the XYZ stage —
   Z gives focus, XY gives well-centering and tiling.
4. **Fold (Phase B, to prove 62 mm).** Drop the 25 mm first-surface 45° mirror into
   the collimated segment in its mount so the beam turns vertical → horizontal. Now
   only the objective barrel + mirror stack vertically (~60 mm); the tube lens +
   camera lie horizontally.
5. **Illumination arm.** A second post beside the cradle carries a horizontal
   cross-arm holding the source 30–80 mm above the plate top, on a right-angle
   clamp so it slides in Z and swings off-axis in XY. Primary source: the WS2812
   matrix (center = brightfield, quadrant = oblique, ring = darkfield) with the
   frosted diffuser between it and the plate. Keep the panel and ring light as
   baselines.

### Measurement protocol

Run the phases **in this exact order; each is a gate — do not proceed if the prior
fails.** The dry → wet → live ordering isolates cause: if live imaging fails you
already know whether it is the optical train (A), the glass/geometry (B), the wet
path/condensation (C), or genuinely the biology/illumination (D). Never debug all
four at once.

- **Phase A — dry, no plate.** Image a USAF 1951 target in air. Record smallest
  resolved group/element and raw working distance by calipers. **Pass:** resolve to
  the optical prediction — but note the bench is **sampling-limited, not
  diffraction-limited**: the optics resolve 2.75 µm (Abbe) / 3.36 µm (Rayleigh) at
  4×/NA 0.10, while 2.16 µm/px sampling sets the practical floor near 4.3 µm
  (2 px). Expect **USAF Group 6 Element 6 – Group 7 Element 1**, and read a miss as
  rig misalignment, not as an optics verdict.
  Fail = rig misalignment; fix it, do not blame the plate.
- **Phase B — dry through the real plate, no cells.** Rest a hemocytometer grid
  (50 µm pitch) on the coverslip top in the imaged well. Image **5 wells: the four
  extreme corners + center.** Record per-well focus-Z, real front-element-to-
  coverslip WD, resolved feature, and the corner-vs-center focus delta (= plate
  tilt).
- **Phase C — wet, no cells.** Pipette **warm (37 °C) media** into the well with the
  dry bay at ambient, to force the real thermal gradient. Confirm focus survives
  air → 0.17 mm glass → media, and **watch for condensation haze on the plate
  underside** (yes/no, time-to-onset, contrast drop) — a required wet-boundary
  output. **Added 2026-09-23 — measure the nose-to-well ΔT here (gate (a″)):**
  thermocouple in the well, head parked vs at working distance, 37 °C media over
  ambient bay. This is the measurement that replaces the estimated
  `G_obj-ambient = 50 mW/K` and it costs one afternoon.
- **Phase D — live cells.** Seed adherent cells; re-image the 5-well pattern under
  all three illumination modes (transmitted-above, oblique-below, epi). Record cell
  countability, confluence, morphology, and contrast per mode.

### The gating numbers

*(Renamed 2026-09-23 — there were three; the re-ruled standoff adds (a′) which
was already here informally, and (a″) thermal, which is new.)*

| Gate | Metric | PASS threshold |
|---|---|---|
| **(a) Focus + real WD** | sharp focus through the wet stack AND WD_real (front element → cell plane) | **Corrected 2026-09-21 — the old ~8.8 mm threshold was derived from a 9.73 mm standoff that omitted `base.thickness_z` (8.0) and `plate_support.land_height_z` (2.0).** The bay-as-ruled puts the head ceiling at z = −8 and the cell plane at z = +11.90, so **WD_real ≥ 19.90 mm** *at the parked height*. 4× (~22 mm) clears by only **2.1 mm**, not "hugely". ~~10× (~8 mm) cannot reach focus at all.~~ **Amended 2026-09-23:** the aperture is climbable and `focus_stroke_z` runs upward, so the binding threshold is **WD_real ≥ 7.90 mm at full stroke** and the 10× passes. The 19.90 mm figure remains the threshold for an objective that must work from the parked plane (e.g. because a retract-to-traverse cycle per well is unaffordable). **Record the threshold you tested against.** |
| **(a′) Which standoff is being tested** | bench head-to-plate-bottom clearance vs the bay's ruled clearance | The bench's 8 mm is the head **inside the 88 × 52 mm aperture**; the parked bay geometry is 18 mm below the plate bottom because `carriage_top_clearance_z` fixes the front face at z = −8 while the plate bottom sits at z = +10. **Record which one you built — and preferably build both, because both are now legal.** ~~No document has decided this~~ **Decided 2026-09-23:** the front element may enter the aperture (probe cylinders to Ø25 clear from z = 0 to z = 11.71 at every tile aperture centre), so the standoff is **19.90 mm parked / 7.90 mm risen** and the NA ladder reopens. What replaces this as the open question is not geometry but the two gates below it: the correction collar and the thermal gate. |
| **(a″) Thermal — nose-to-well ΔT** | cell-plane temperature with the head at working distance vs with the head retracted | **ΔT ≤ 0.3 K.** A close objective sinks heat out of the well; the modelled ordering is water 60×/1.20 @ WD 0.31 → 7.50 K (fail), dry 40×/0.95 @ 0.18 → 1.96 K (fail), dry 40×/0.60 @ 3.0 → 0.23 K (pass), dry 20×/0.45 @ 7.5 → 0.15 K (pass). The model assumes an **estimated** `G_obj-ambient = 50 mW/K`; **the bench measurement replaces the estimate and is the highest-value early number on the programme.** Fail → local 37 °C nose heater, not a 37 °C bay. |
| **(b) Contrast** | Michelson `C = (I_max − I_min)/(I_max + I_min)` on a grid line / cell edge (raw frames) + cell-count agreement | **grid C ≥ 0.15 AND two manual counts agree ±10 %** in at least one illumination mode. 0.08–0.15 = marginal (computational only); < 0.08 = illumination must change. |
| **(c) Field flatness / tilt** | intra-well edge defocus `ΔZ_field` and well-to-well `ΔZ_tilt` vs DOF | **ΔZ_field ≤ DOF AND ΔZ_tilt ≤ DOF** (4×/NA 0.10 DOF = λ/NA² = **55 µm total, ±27 µm** → generous; the "±55 µm" this row used to quote double-counted). ΔZ_tilt > DOF → per-well autofocus (confirm ≤ 12 mm stroke). ΔZ_field > DOF → field not flat, tile + refocus or drop mag. **At the NA the risen standoff opens, DOF collapses — 2.72 µm at NA 0.45, 1.53 µm at NA 0.60 — and refocus at every well visit becomes mandatory regardless of how stable the structure is.** |

---

## How Stage 0 feeds the CAD

Bound the moving front-end with a caliper bounding box of the objective barrel Ø +
fold-mirror housing + the **vertical** extent of the head only. The tube lens and
camera are horizontal, so they do **not** count against the Z budget — but their
swept XY extent **does** count against the dry-bay XY rectangle. Then overwrite
these exact params in `cad/one_row_coupon.params.json`:

| Bench measurement | → Param | Mapping rule |
|---|---|---|
| Front-end XY bounding box `FE_x × FE_y` | `observer_robotics.front_end_length_x` (21.0), `front_end_width_y` (13.0) | set = measured + 1 mm assembly margin |
| Front-end half-extent overhanging the well aperture in X / Y | **`dry_bay.observer_sweep_extra_x` (16.1), `observer_sweep_extra_y` (17.0)** | **headline deliverable** — replace the hand-tuned fudge with the measured per-axis overhang |
| Vertical extent (objective parfocal + fold mirror) `FE_z` | `front_end_height_z` (28.0) | set = measured; closes budget iff `8 + FE_z + focus_stroke + margin ≤ 62` |
| `WD_real` | consistency check on `carriage_top_clearance_z` (8.0) | ~~if WD_real forces the element above z = −8, the 8 mm clearance is invalid and the bay must deepen~~ **Superseded 2026-09-23:** rising above z = −8 is legal — the aperture column is clear to z = 11.71 — so a WD_real between 7.90 and 19.90 mm does **not** invalidate the clearance or require deepening. It requires `focus_stroke_z` to be spent upward and costs 3 retract/re-raise cycles per row of 4 tiles. Only `WD_real < 7.90` forces a class change. |
| Nose-to-well ΔT at working distance | *(no param yet — gate (a″))* | replaces the estimated `G_obj-ambient = 50 mW/K`. ΔT > 0.3 K → the head needs a local 37 °C nose heater, which is a new part in the front-end bounding box and must be added to `front_end_*` before those are pinned |
| `ΔZ_tilt` | `front_end_focus_stroke_z` (12.0) | confirm `ΔZ_tilt + DOF margin ≤ 12.0` |

**Z-closure go/no-go arithmetic:**

```
Required vertical = carriage_top_clearance_z (8)
                  + FE_z (objective parfocal + fold)
                  + focus_stroke (ΔZ_tilt)
                  + service margin
CLOSES iff Required vertical ≤ 62 mm (carriage_height_z),
          nose within the measured clear column (z ≤ 11.71),
          barrel Ø ≤ 32 mm (objective_keepout_diameter).
```

*(Corrected 2026-09-23 — the closure condition read "front element ≤ z = −8". That
clause is void: "Correction (2026-09-23): the aperture is climbable" above measures
the column clear from z = 0 to z = 11.71 and legalises a nose at z = +4.00, and the
paired protocol dropped the same clause at
`../protocols/observer_optical_bench_stage0.md:51` and `:231`. Left in, Q4 below
would reject every risen-standoff head this document argues for. The ceiling that
replaces it is the **measured** one, z = 11.71, which is 0.02 mm below the glass
outer surface (0.19 mm below the cell plane).
Read this block together with the additive-sum caution immediately following: the
sum itself over-constrains, so a head that fails it has not yet been rejected on
geometry.)*

Expected: FE_z ~60 mm straight-down closes with ~2 mm spare because the tube lens
and camera are routed horizontally. The bench must confirm ~60 with calipers, not
trust the estimate.

> **Caution added 2026-09-23 — this additive sum over-constrains.** The same form
> is implemented at `src/aevum_smis/manifest.py:193-200`, where
> `vertical_required = front_face_clearance + front_end_height_z + focus_stroke_z +
> service_margin_z` is tested against the z budget. Summing all four assumes the
> head simultaneously occupies its parked clearance *and* its full focus stroke,
> which no pose does — the stroke moves the head through the clearance, it does not
> stack on top of it. On a 60 mm-parfocal objective the sum reads 8 + 57 + 18 = 83
> against a 62 mm budget and rejects the part, while the solid model says the column
> is clear (probe cylinders to Ø25 rise to z = 11.71). Against
> `observer_sweep_depth_z` = 80 the honest figure for the placeholder head is
> 8 + 28 + 12 = **48 mm, with 32 mm of slack**.
>
> **Recommendation (not applied — this is a docs-only pass):** replace the additive
> sum with a **swept-envelope** check that unions the head body over the stroke, and
> keep a **hard retract-plane assertion** alongside it (nose ≤ z = 0 whenever XY
> motion is enabled) so the relaxation does not silently permit a head that cannot
> traverse. The retract-plane assertion is what makes the swept check falsifiable;
> dropping the additive sum without it would be a real loss of safety.

**Strengthen the swept-body test.** The current
`_observer_front_end_swept_body_check`
(`src/aevum_cad/row_coupon/parts/observer.py:574`; path corrected 2026-09-23 after
the module became a package) builds the
swept body as `[min_well − L/2, max_well + L/2]` and the test
(`tests/test_row_coupon_cad.py`) asserts the wells fall inside it — which is true by
construction and cannot fail. After the bench: (1) overwrite `observer_sweep_extra_x/y`
and `front_end_*` with measured values; (2) the swept body becomes the measured
objective-barrel cylinder + measured horizontal camera-arm rectangle, not a
placeholder box; (3) add the two falsifiable asserts the current test lacks —
**front barrel Ø ≤ `objective_keepout_diameter` (32)** and
**`front_end_height_z + carriage_top_clearance_z + front_end_focus_stroke_z ≤
carriage_height_z` (62)**; (4) the Gate 6 swept-body check flips from
"required_physical_evidence / claims blocked" to satisfied, because the swept volume
is now caliper-backed. The test that should now be able to fail: "given a measured
40 × 40 mm head with a 25 mm working distance, does it still fit and clear?"

**Implementation status (2026-06-10).** The two falsifiable asserts above are now
implemented in `_observer_front_end_swept_body_check` against the *placeholder*
params (footprint Ø 24.70 ≤ 32; vertical budget 8+28+12 = 48 ≤ 62), so the closure
is guarded before the bench, not after — bumping `front_end_length_x` or
`front_end_height_z` now turns the test red. The footprint value is the
circumscribed diagonal of the head bbox (a conservative stand-in), to be split into
barrel-Ø-vs-keepout and head-bbox-vs-dry-bay once Stage 0 measures the real barrel.
The Stage-3 carriage gap is also scaffolded: `_observer_carriage_traverse` sweeps
the carriage across the row (body sweeps the long axis, head scans the short axis)
and runs deck-foot / adjacent-slot overlap, adding the
`carriage_traverse_exceeds_dry_bay` Gate-6 blocker. *(Updated 2026-09-23 to the
live output; this paragraph described the superseded fat-body result.)* The
thin-truck topology **resolves** the Y overflow: today
`dry_bay_overflow_x_mm = dry_bay_overflow_y_mm = 0.0` and `fits_dry_bay = True`,
with 10.0 mm of traverse-axis margin. The **44.6 mm** figure is the pre-thin-truck
58 mm-body result and is retired. What still blocks is not the bay envelope but the
feet and the corridor: `deck_foot_collision_count = 1` (`hits_deck_feet = True`) and
`scan_corridor_margin_mm = −2.72`, so `clears_traverse = False`. This is geometric evidence,
not a proven motion plan; it stays Gate-6 blocked until the physical gantry is built.

## Decision tree

```
Phase A resolves to optical spec (dry, no plate)?
  NO  → rig misaligned; fix. NOT an architecture verdict.
  YES ↓
Q1 FOCUS through wet stack — which standoff? (re-ruled 2026-09-23; the element MAY enter the 88x52 aperture)
  WD_real >= 19.90 mm  → PARKED-HEIGHT HEAD: scans a tile without retracting. Long-WD zero-coverslip class.
  7.90 <= WD_real < 19.90 → RISEN HEAD: legal, costs 3 retract/re-raise cycles per row of 4 tiles.
                            Requires focus_stroke_z run UPWARD from the traverse plane.
  WD_real < 7.90 mm    → does not reach even at full stroke → DROP MAG or change optical class.
  YES ↓
Q1b CORRECTION: is the objective corrected for the 0.17 mm coverslip (collar, or 0.17-design)?
  YES → no aberration cap.
  NO  → hard cap NA <= 0.363 @550 nm whatever the WD. Reaching focus is NOT the same acceptance.
  ↓
Q1c THERMAL: cell-plane dT with the nose at WD <= 0.3 K?
  YES → proceed.
  NO  → LOCAL 37C NOSE HEATER (not a 37C bay: IMX178 dark current ~doubles per 6-7 K).
        Heads closer than ~3 mm fail this, DRY INCLUDED.
  YES ↓
Q2 CONTRAST: some mode gives Michelson ≥ 0.15 + countable cells?
  oblique-from-below or epi passes   → fork resolves FOR sealed top (the cheap win — keep lid sealed).
  only transmitted-from-above passes → fork resolves AGAINST sealed top → commit lid optical window, re-cost manifold.
  nothing passes                     → escalate: phase optics / different sensor (global-shutter IMX273 if jitter).
  YES ↓
Q3 FIELD FLATNESS: ΔZ_field ≤ DOF AND ΔZ_tilt ≤ DOF across 5 wells?
  YES               → fixed-focus per tile (simplest production).
  ΔZ_tilt > DOF only → per-well autofocus; confirm ΔZ_tilt ≤ focus_stroke (12 mm).
  ΔZ_field > DOF     → field not flat → TILE + REFOCUS, or drop mag.
  ↓
Q4 Z-CLOSURE: 8 + FE_z + focus_stroke + margin ≤ 62, nose ≤ z = 11.71 (measured
   clear ceiling, NOT z = −8 — see the climbable-aperture correction), barrel Ø ≤ 32?
   (the additive sum over-constrains — see the caution above it)
  YES → COMPACT FRONT-END VIABLE → write measured front_end_* + observer_sweep_extra_x/y, retire 16.1/17.0, strengthen Gate 6.
  straight > 62 but folded fits → NEEDS FOLD (already assumed); keep straight-down ≤ ~54 mm, route tube + camera horizontal.
  even folded fails → Z BUDGET FAILS → deepen bay / lower mag / remote sensor via relay.
```

The Q2 branches carry more than contrast. A **transmission absorbance / OD600
readout needs the same clear vertical path as transmitted-from-above brightfield**
(source above, sample between, detector below), and the pre-slit silicone sealing
mat is opaque as well as the lid — so the "sealed top" branch also gives up
transmission absorbance for the life of that lid design, and the "optical window"
branch gains absorbance as a rider that belongs in its re-cost. See
`../knowledge/byonoy_plate_readers.md`.


**Expected happy path:** 4× infinity + f ≈ 50 mm tube + single 45° fold + IMX178
mono, oblique-from-below illumination → focuses at ~22 mm WD from the parked
height, DOF 55 µm (±27) swallows plate tilt, straight-down ~60 mm closes the 62 mm
budget, barrel Ø ≤ 25 < 32 keepout → compact moving front-end viable, sealed top
preserved, the 16.1/17.0 fudge replaced by a measured overhang. The bench exists to
confirm or break that chain with calipers and real images.

**What the happy path is not.** It is a *geometry* result, and after 2026-09-23 the
geometry is no longer the binding constraint. A 4×/NA 0.10 head at 2.16 µm/px
collects **0.140 % of 4π** and resolves 2.75 µm; it can count cells and score
confluence and it cannot do anything else. The three questions that now decide the
observer's ceiling are all downstream of the happy path: the **correction collar**
(NA 0.363 otherwise), the **thermal gate** (0.3 K), and the **tube lens** (M_eff =
nameplate/3.6 at f_ref 180, nameplate/4 at f_ref 200 — see "The tube lens sets every
magnification number in this document" — which makes every NA on the ladder
sampling-limited). Passing Stage 0 does not answer any of them.

## The one risk most likely to bite

**Label-free contrast on unstained cells through the media column — not focus, not
Z-fit.** Focus and the 62 mm geometry are nearly guaranteed by the 4×'s 22 mm WD
and the fold math; those are arithmetic. The genuinely uncertain thing is whether
oblique-from-below illumination gives readable phase-gradient contrast (Michelson
≥ 0.15, countable cells) through the deep aqueous media column without a transmitted
source above. If it does not, the cheap architectural win evaporates and Aevum must
commit an optical window in the sealed wet lid — directly competing with the
gas/septum manifold and re-costing the whole lid. This is why the WS2812 matrix is
the highest-leverage purchase: it is the single experiment that retires the
illumination fork. Test oblique-from-below first in Phase D; if it lands marginal
(0.08–0.15), characterize whether a darkfield ring or computational enhancement
recovers it before conceding the top window.

**Second entry, added 2026-09-23: the nose-to-well thermal gradient.** It is not a
close second to contrast — it is a different kind of risk. Contrast failing is a
visible, immediate failure that forces a redesign. A 2 K well-cooling gradient
correlated with the revisit schedule is an **invisible** failure: every image looks
fine, and the causal models the platform exists to build absorb the artifact as
biology. It is cheap to measure (gate (a″), one afternoon on this bench) and
expensive to discover late, which is the worst combination to leave untested.

## What Stage 0 does not prove (scope lock → Stages 1–4)

This static rig says **nothing** about the moving system. It deliberately omits
motion and the OT-2. It cannot tell you the moving carriage's settling time,
resonance, servo jitter, or motion-induced defocus — those are properties of the
motion system and its structural loop, tested on the actual stage in later stages.

The one number Stage 0 hands the motion designer is the **vibration spec**: the
moving carriage must be held still, at exposure, inside half the measured depth of
field — λ/NA² gives **55 µm total at 4×/NA 0.10** and **8.8 µm total at
10×/NA 0.25**, so the spec is **±27 µm** and **±4.4 µm**. That
becomes the acceptance threshold for Stage 1's focus axis and Stage 2/3's scan.
**On the reopened NA ladder it tightens by more than an order of magnitude:
±1.4 µm at NA 0.45, ±0.8 µm at NA 0.60.** A vibration spec written against the
4× number will not survive the objective this document now says is admissible.

The carriage-traversal gap — today the 62 mm-tall carriage is modeled only at the
plate-1 end of the row while the front-end must reach all four plates across
334.5 mm of Y — is **not** resolved by Stage 0. It is resolved physically at Stage 3,
where the real gantry either fits and traverses the full bay between the deck feet
within 80 mm, or forces a front-end/carriage decoupling redesign. Stage 0 exists to
make sure the optical head that gantry must carry is small enough and reaches focus
in the first place — so that Stage 3 is a motion problem, not also an optics
problem.
