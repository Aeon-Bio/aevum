# Swappable Sensor Module Interface (SMIS v0.1)

## Purpose

The observer bench (`observer_optical_bench.md`) proves one thing: an inverted
optical head can image cells in a CellVis well from underneath, inside the 80 mm
dry bay, through the real wet boundary. This page asserts the next, larger claim:
**the stage built to carry that head is the actual instrument, and the imaging
modality is a swappable part.** Once the bay holds a fiducial-registered 3-axis
scanner (`observation_module.md`), a head-side Pi, an offboard PSU/compute over the GX16 umbilical
(`power_section.md`), and the single-writer motion lease of the OT-2 bridge
(`agent_ot2_bridge.md`), nothing about that carrier is specific to brightfield.
A dichroic, a beamsplitter, a fiber pickoff, a Raman probe, or a non-optical
impedance head can all ride the same dock if — and only if — there is a frozen
contract for them to ride.

This document is that contract, in three parts: the **interface spec (SMIS
v0.1)**, the **modality catalog** it is designed to host, and the **scaling
roadmap** that takes it from one solo-built head to a platform with partner-built
heads.

It must be read with the same honesty discipline the rest of this knowledge base
uses. **SMIS is a v0.1 contract to design against, not a built subsystem.** It
sits in exactly the state the dry bay was in when the observer bench doc was
written: correctly reserved, deliberately scoped, and carrying **zero installed
parts**. Every dimension, pinout, and ABI signature below is a *specification*,
not a measurement; every imaging or motion claim it makes is **Gate-6 unproven**
until a physical dock is printed and a head is docked. The bench is Stage 0 of
filling the bay with one head; SMIS is the contract for filling it with the
*second* head, and it is honest to say that second head does not yet exist. This
is reserved-and-deferred, like the bay itself.

## Stance

SMIS is a COTS-authority exception in the same family as the power section, the
sensor PCB, and the observer bench. The print-native row coupon
(`one_row_coupon.md`) is a strict no-metal, no-glue mechanical proof; SMIS
deliberately brings commercial optical, electrical, and computing authority into
the dry bay at three named boundaries. Those boundaries are the whole point of the
spec:

- the **dock plane** (mechanical authority hands off to the gantry),
- the **infinity port** (optical authority hands off to the shared objective
  train), and
- the **HEAD-BUS connector** (electrical authority hands off to the offboard PSU,
  a superset of the GX16 umbilical from `power_section.md`).

Above those three planes the platform owns a **frozen** contract. Below them a
module owns a **free** design the platform trusts only after a digest check, an
interlock check, and a registration check — the same fail-closed evidence
discipline the OT-2 bridge already runs. The authority boundary that governs
everything is still the dry-bay envelope: a SMIS head may not intrude on the
sealed wet chamber, touch the CellVis plate (the plate-as-consumable rule from
`materials_strategy.md` holds — all sensing is non-contact from below or a
sibling consumable), or consume the deck-foot keepouts the row coupon validates.

The thesis in one sentence: **the stage is the sensor-agnostic instrument, and
modalities are plug-in heads above two frozen planes** — and the discipline that
keeps this from being vaporware is that the spec is allowed to be only as wide as
two real paid heads demand (see the trap at the end).

## The one number that organizes the catalog

The observer bench picked a **4× plan-achromat, NA 0.10** as the primary
objective. That choice propagates into every modality SMIS can host.

**Corrected 2026-09-21.** This section previously called the NA-0.10 collection
number "a single physical fact" of the platform. It is not — it is a property of
the *objective currently fitted*, and the correction that removed a phantom 0.6 mm
plate window changed what the geometry *admits*. Those are two different numbers
and the catalog below must not conflate them:

| | NA | collection (∝ NA²/4) | Abbe @ 550 nm |
|---|---:|---:|---:|
| **(a) FITTED TODAY** — 4× plan-achromat | 0.10 | ~~0.25 %~~ | 2.750 µm |
| **(b) ADMISSIBLE** — aberration ceiling set by residual cover-correction error at 0.17 mm of #1.5H | ~~**~0.55**~~ | ~~**7.56 %**~~ | ~~**0.500 µm**~~ |

**Corrected again 2026-09-23 — the table above is superseded on every column.**
Three independent errors compounded in it. They do not all push the same way, and
the honest summary is that the *absolute* numbers were wrong in both directions
while the *conclusion* — that photons are the binding constraint — was wrong
outright:

1. **The collection model was the wrong form.** `NA²/4` is a small-angle,
   *air-side* approximation. The emitter is not in air.
2. **The aberration ceiling was set against a residual cover-correction error**
   rather than against the Maréchal criterion applied to the full uncorrected
   0.17 mm coverslip.
3. **The mechanical wall the 2026-09-21 revision put in its place was an
   artifact** of checking the traverse against well columns the aperture never
   admitted.

### (1) Collection fraction — the correct, media-side form

The emitter sits in aqueous media at **n = 1.335**. An objective of numerical
aperture NA subtends a half-angle θ = asin(NA / n) *in that medium*, and the
fraction of an isotropic 4π emission it collects is the solid-angle cap fraction

```
η = ( 1 − cos( asin( NA / n_media ) ) ) / 2      n_media = 1.335
```

not `NA²/4`, and not the air-side version of the same cap formula either. At
NA 0.10 the old form **overstates** collection by ~1.8× (0.25 % claimed against
0.140 % real). Every photon argument in the catalog below is re-derived against η.

| NA | η collected (of 4π) | vs the fitted NA 0.10 | Abbe λ/2NA @ 550 nm | DOF λ/NA² @ 550 nm |
|---:|---:|---:|---:|---:|
| **0.10** — fitted today | **0.140 %** | 1.0× | 2750 nm | 55.0 µm |
| **0.363** — Maréchal cap, no collar | **1.884 %** | 13.4× | 758 nm | 4.17 µm |
| **0.45** — ELWD + correction collar | **2.926 %** | **20.8×** | 611 nm | 2.72 µm |
| **0.60** — ELWD + correction collar | **5.334 %** | **38.0×** | 458 nm | 1.53 µm |
| 0.95 — dry high-NA | 14.871 % | 106× | 289 nm | 0.61 µm |
| 1.20 — water immersion | 28.090 % | 200× | 229 nm | 0.38 µm |
| **1.335** — hard ceiling (NA = n_media) | **50.0 %** | 356× | 206 nm | — |

NA 0.95 and above are shown for scale only — § *The thermal wall* excludes them,
and § *(3) Oil is unrealizable* caps the column at 1.335 regardless. DOF uses the
dry (air-side) form λ/NA² and every figure in the column is a **total** depth, not
a half-range: 55.0 µm at 4×/NA 0.10 means ±27 µm about focus. This document
previously wrote that same quantity as "±55 µm", which double-counted it;
`observer_optical_bench.md`, § *Optical configuration*, row "Depth of field, NA 0.10"
corrected it on 2026-09-23 and this table now follows that convention throughout. Multiply by n_media = 1.335 for the
corresponding depth measured inside the specimen.

### (2) The aberration cap, and what lifts it

The uncorrected 0.17 mm coverslip is the aberration limit, not the
cover-correction *residual*. Slab spherical aberration scales as NA⁴, so the
Maréchal quarter-wave budget through 0.17 mm of n = 1.5185 glass caps an
uncorrected objective at

| λ | Maréchal NA cap |
|---:|---:|
| 405 nm | 0.336 |
| 550 nm | **0.363** |
| 785 nm | 0.397 |

(The three are mutually consistent: wavefront error ∝ NA⁴/λ, and
(0.397/0.363)⁴ = 1.43 ≈ 785/550.) This **supersedes** the old row (b) figure of
NA ~0.55, and it also supersedes the NA 0.640 "quarter-wave ceiling at 25 µm
residual" figure quoted in catalog row #6.

**A correction collar removes the cap entirely** — that is what a collar is for.
The distinction that matters for sourcing is therefore not high-NA vs low-NA but
*zero-cover design vs collar*:

- **Long-WD catalog objectives are zero-coverslip designs.** A Mitutoyo M Plan
  Apo 20×/0.42 WD 20 used through 0.17 mm of glass runs **1.79× over** the
  Maréchal budget ((0.42/0.363)⁴ = 1.79). Long WD does not buy cover correction.
- **At the short working distances the bay actually offers, the ELWD
  correction-collar class applies** — e.g. Nikon CFI S Plan Fluor ELWD 20×/0.45
  (WD 6.9–8.2 mm, collar 0–2 mm) and 40×/0.60 (WD 2.8–3.6 mm). These are
  designed to be dialled onto a coverslip thickness.

### (3) Oil is unrealizable on live cells — the ladder ends at water

NA = n·sinθ, and the light originates *in the media*, n = 1.335. The acceptance
angle in the sample medium cannot exceed 90°, so no matter what the barrel says,
the effective NA is capped at **n_media = 1.335**. A nominal **1.40 NA oil**
objective imaging live cells in aqueous media is an NA 1.335 objective with an
index-mismatch aberration penalty on top. **Oil buys nothing over water for this
sample.** The realizable ladder ends at **water, NA 1.20–1.27** — and § *The
thermal wall* then excludes even that. Record this before anyone specifies a
1.4 NA part.

### The mechanical wall was an artifact — 15.56 mm → 51.56 mm

The 2026-09-21 revision named a **15.56 mm** scan-corridor head budget and a
**WD ≥ 19.90 mm** floor, and concluded that "no RMS-threaded objective threads
this corridor at all." Both figures were arithmetically correct and both were
answering the wrong question. Re-measured 2026-09-23:

- **The corridor budget was computed against a 99 mm scan spanning all 12 well
  columns.** The per-tile through-aperture is **88 × 52 mm**
  (`dry_bay.aperture_length_x` / `aperture_width_y`) and has only ever admitted
  **8 columns**, span 63.0 mm. Against the columns the head can actually reach,
  the budget is `min(2·(42.88 − 17.10), 2·(134.50 − 105.88))` = **51.56 mm** — a
  **3.3× increase from parameterising the traverse check by reachable columns,
  with no CAD change.** An RMS barrel floors near Ø20.32 and now clears by
  2.5×. The three corridor levers (service-shroud re-route → 21.24 mm;
  post-to-rail reshape → 24.84 mm; outboard leg seating → 41.84 mm) are no
  longer required for any catalog head.
- **WD ≥ 19.90 mm is the *traverse-plane* standoff, not the focus standoff.**
  Running the existing `focus_stroke_z` = 12.0 upward from the traverse plane
  puts the head nose at z = +4.00 and the working distance at **7.90 mm**. The
  vertical budget is 8 + 28 + 12 = 48 against `observer_sweep_depth_z` = 80, so
  32 mm of slack remains. Independently measured: probe cylinders up to **Ø25 mm
  rise unobstructed from z = 0 to z = 11.71** at every tile aperture centre — the
  column is clear to within 0.02 mm of the glass outer surface (0.19 mm below the
  cell plane). The short-WD ELWD
  correction-collar class is admissible; the long-WD zero-cover class is not the
  only option and is in fact the aberrated one.
- **The cost is a retract cycle, not a per-well one.** Between tiles the
  `plate_support_frame` (z 0–11.20) blocks at z = 0.05, so the nose must retract
  to cross a tile boundary: **3 retract cycles per row of 4 tiles, not one per
  well.** Within a tile's aperture the nose stays raised.

### The thermal wall — the constraint that actually binds now

A close objective is a heat sink into the well, and this platform exists to build
causal models of perturbation response. Steady-state model, 37 °C bath against a
25 °C bay:

| Head | WD | cells reach | ΔT |
|---|---:|---:|---:|
| water 60×/1.20 | 0.31 mm | 29.50 °C | **7.50 K** — fails |
| dry 40×/0.95 | 0.18 mm | 35.04 °C | **1.96 K** — fails |
| dry 40×/0.60 | 3.0 mm | 36.77 °C | **0.23 K** — passes a 0.3 K budget |
| dry 20×/0.45 | 7.5 mm | 36.85 °C | **0.15 K** — passes |

**Every head closer than ~3 mm fails, dry included.** This is the reason the
realizable ladder stops at NA 0.60 even though the optics and the corridor would
now carry NA 0.95 and water 1.20. It is not a comfort argument: an uncorrected
objective-induced ΔT is an **unlogged thermal perturbation correlated with which
wells are revisited and how often**, which is precisely the confound that
destroys the causal models the platform is being built to produce.

The mitigation is a **37 °C nose heater** (local), not a 37 °C bay (global) —
IMX178 dark current roughly doubles per 6–7 K, which would kill the long
integrations Raman (#6) and luminescence (#13) need. Objective conditioning is
also what the commercial precedents do: Opera Phenix Plus and Yokogawa
CellVoyager CV8000 both run automated **water immersion from below through
glass-bottom plates** and both condition/heat the objective.

> **Caveat, stated because it is load-bearing.** The table above uses an
> **estimated** objective-to-ambient conductance `G = 50 mW/K`. The *ordering* is
> robust, but not for the reason an earlier revision of this line gave. ΔT is set
> by **two** terms, not by 1/WD alone: within a given gap medium it rises as the
> gap closes, and the **medium sets the scale** — a water column conducts roughly
> 25× better than the same thickness of air (~0.6 against ~0.026 W/m·K near room
> temperature). That is why the table above is *not* monotone in WD: the 0.31 mm
> immersion head (7.50 K) is far worse than the 0.18 mm dry head (1.96 K) despite
> the **larger** standoff, because its gap is filled with water. Read as two terms
> the ordering does hold — the three dry heads are monotone in gap (1.96 K at
> 0.18 mm, 0.23 K at 3.0 mm, 0.15 K at 7.5 mm) and the one immersion head is worst
> on the medium term — and a common error in the estimated `G` rescales all four
> rows together, so it cannot reorder them; only a per-head error in the *gap*
> conductance could. The absolute ΔT is not robust either way. **This is the
> highest-value early measurement on the optical side of the project:** a
> thermocouple in a filled well with a dummy aluminium slug at each of the four
> working distances retires it in an afternoon. Until then, the 0.3 K budget is a design rule, not a result.
>
> **Water immersion is separately blocked on policy, not physics.**
> `../knowledge/materials_strategy.md` states that per-well sensing is "optical
> ... through the glass from the row module's dry bay or lid, not contact."
> Immersion fluid touching the plate underside would require an **explicit
> written amendment there plus a decision-log entry** — it is not an
> interpretation question, and SMIS does not get to decide it.

### What this does to the value gradient

The gradient still runs opposite to the difficulty gradient, but the difficulty
has moved again — twice in three days, which is itself worth recording:

| revision | what the catalog thought the binding wall was |
|---|---|
| original | **photons** — NA 0.10 is all we can host |
| 2026-09-21 | **corridor geometry** — 15.56 mm admits no RMS head |
| **2026-09-23** | **thermal** — NA ≤ 0.60 / WD ≥ 3 mm, from sample-temperature integrity |

The computational wedge (#1, #3, #4) is still the correct place to start, for the
third distinct reason in three revisions: it is cheap, it is differentiating, and
it does not park a heat sink under a living well. What changed is that the
**photon-hungry rows are no longer blocked** — NA 0.45–0.60 is reachable, at
20.8–38.0× the collection the catalog was written against.

The second governing fact is the observer bench's own finding: **the collimated
infinity space between the objective and the f=50 mm tube lens is the only
aberration-free place to insert an optic.** A plane-parallel element (dichroic,
notch, polarizer, beamsplitter, fiber pickoff) in collimated light adds zero
defocus and negligible aberration — a tilted plate just shifts the beam laterally
instead of adding spherical/coma. SMIS turns that ~25-40 mm slot into a *named,
dimensioned, mechanically standardized port* (§ Optical). The modularity slot is
not invented here; it is the same trick every infinity-corrected microscope uses.
SMIS only freezes its geometry.

These two facts split the catalog cleanly:

- **Back-end / front-end swap** — keep the objective and plate-side hardware,
  change only what lives in or after the infinity space. Registration survives
  trivially. The cheap, fast, high-value zone.
- **Whole-head swap** — change the objective itself (different NA/WD), re-register.
  A real engineering tax.
- **Fork** — needs electrodes or probes in contact with cells. Breaks the
  no-contact plate rule, so it is a *sibling consumable*, not a head.

## The modality catalog

Ranked by value-per-effort for a solo builder. "Share" = back-end/front-end swap
preserving the 4× objective and the fiducial registration; "Head-swap" = new
objective/probe plus re-registration; "Fork" = plate contact required → sibling
consumable, not a head; "Level-3" = non-imaging — no objective and no infinity
port, dock + bus + manifest only. Cost is added optics/source only (the shared
camera, objective, and stage are sunk). TRL-solo is the realistic
technology-readiness for *this* geometry built by one person, not the modality's
textbook maturity.

> **Read the catalog against this, 2026-09-23.** Every verdict below was written
> when the only hostable objective was **NA 0.10**, and that premise is
> load-bearing in rows **#2**, **#6** and **#13**. It no longer holds: the
> corridor correction (15.56 → 51.56 mm) and the focus-stroke standoff
> (WD 19.90 → 7.90 mm) admit the **ELWD correction-collar class at NA 0.45–0.60**,
> which collects **20.8× to 38.0×** the photons of the fitted 4×/NA0.10 head
> (§ *The one number*). The three affected rows are **re-verdicted in place
> below**, with what they used to say preserved. The NA ceiling is now set by
> the thermal wall (NA ≤ 0.60, WD ≥ ~3 mm), not by optics or geometry.
>
> Rows **#1, #3, #4, #5, #7–#12 were each re-checked against the new ladder and
> do not move** — see the note below the table. Nothing was deleted to tidy the
> catalog: an honest negative verdict that survives re-derivation is still a
> result.

Rows #1-#12 are rank-ordered. **#13 is appended, not ranked** — the numbering was
already load-bearing across this document and the roadmap when it was added, and
renumbering a catalog other sections cite by number is a silent reference break.
On value-per-effort #13 sits near #4/#5, below the two wedge heads.

| # | Modality | Measures | Share / swap / fork | Cost | TRL-solo | Verdict |
|---|---|---|---|---|---|---|
| 1 | **QPI / DPC / FPM** ⭐ | Label-free dry mass (pg/cell), morphology, confluency, motility | **Share** — LED matrix only | ~$20 | 7-8 | **Near-term win. The wedge. Build now.** Quantitative, differentiating, zero new optics. |
| 2 | **Epifluorescence 1-4 ch** ⭐ | Viability, GFP/RFP reporters, nuclei, IF, Ca²⁺ | **Share** — dichroic cube in infinity port | $300-800 | 8-9 | **Near-term win. The revenue modality. Re-verdicted 2026-09-23 — it got better.** It used to read "NA 0.10 limits it to *bright* labels; dim single-molecule needs a high-NA head", written when no high-NA head could be hosted. One can now: at NA 0.45/0.60 collection is **20.8×/38.0×** the NA-0.10 path, moving dim reporters, IF and low-amplitude Ca²⁺ from *excluded* to *a head we can dock*. Two caveats replace the old one: (i) the frozen **f = 50 mm tube lens undersamples** the gain — a 20×/0.45 runs at M_eff 5× → 0.48 µm/px against a 306 nm Nyquist pitch, 1.6× short, so **NA 0.45 buys photons now and resolution only if f_tube rises**; (ii) **NA ≥ 0.95 is excluded on thermal grounds, not optical** (§ *The thermal wall*). Single-molecule stays out. |
| 3 | **Multispectral + polarization** ⭐ | Absorbance/chromophore; birefringence (collagen, spindle, fibrosis) | **Share** — reuses #1/#2 hardware | <$100 | 7-8 | **Near-term win, as free variants.** Absorbance survives NA 0.10 because it is **ratiometric** (I/I₀), so the collection penalty largely cancels — the #4 argument, not a free-rider accident. What ships is *serial per-well spectrophotometry of an imaged field*, never a 3-second plate read (`../knowledge/byonoy_plate_readers.md`). Transmission absorbance also needs the lid-window branch of C-OB2. Ship with #1/#2, not as headline heads. Plastic-optic strain birefringence is the watch-out. |
| 4 | **UCNP / lanthanide ratiometric thermometry** ⭐ | Sample-plane / per-well T, 0.1-0.5 K, in living cells | **Share** — 980 nm pump + 525/545 split | <$550 | ~6 | **Near-term win. The real quantum-adjacent head.** Ratiometric ⇒ NA-insensitive; no microwave; a genuine upgrade over the MLX90614 thermopiles. |
| 5 | **Optical O₂ / pH chemical-spot** | Dissolved O₂, pH ratiometrically (Ru/porphyrin, fluorescein) | **Share** — same epi path as #4 | ~$200 | 7 | Near-term, no-contact compatible (spot lives in media/film, not on hardware). Metabolic readout. |
| 6 | **Raman 785 nm point-probe** 🎯 | Label-free molecular fingerprint (lipid/protein/NA, drug uptake) | **Share** pickoff; **wants own high-NA head**; spectrometer **offboard via fiber** | $10-23k | 4-5 pt / 2-3 map | **Frontier bet. The moat, and the reason the 80 mm bay exists.** Throughput-limited to sparse/targeted spot-checks — *not* a whole-plate raster. **Verdict re-derived twice. 2026-09-21: blocker moved from photons to geometry. 2026-09-23: the geometry was an artifact, and the last hard wall is thermal.** The 15.56 mm corridor budget was computed against a 99 mm scan over all 12 well columns; the 88 mm tile aperture only ever admitted 8 (span 63.0 mm), and against the reachable set the budget is **51.56 mm** — so both credible heads, **30.0 mm** (fiber-offboard pickoff) and **34.28 mm** (sealed high-NA cartridge), now fit with margin and **no corridor lever is needed**. Optics were already open, but for a corrected reason: the 785 nm uncorrected-coverslip Maréchal cap is **NA 0.397** (this **supersedes** the 0.640 "25 µm residual" figure this cell used to quote), a correction collar lifts it, Ø20 PD-0 passes every ladder pupil, HEAD-BUS already carries the fiber bulkhead and hardware laser interlock, and Z closes with ~14 mm spare. **What remains:** (i) **thermal** — a Level-2 Raman head parked closer than ~3 mm fails the 0.3 K sample budget, so the high-NA cartridge needs a 37 °C nose or a ≥ 3 mm standoff; (ii) **integration time** — still 1–30+ s/point even at the corrected NA-0.60 collection of 5.334 % (38.0× the figure the original estimate used, which is a real gain and still not a raster). Partner-built; must not gate the wedge. |
| 7 | **NV-diamond ODMR thermometry** 🎯 | mK-class T (D = 2.87 GHz, dD/dT = −74.2 kHz/K), window-bonded diamond | **Head-ish** — dichroic + MW; CPW printed on head-top window | ~$0.5-1.2k | 5 bench / 2-3 in-platform | **Frontier bet. The credible "quantum" headline** — as an mK *non-contact reference thermometer*. **NOT intracellular, NOT magnetometry** (see bounded claims). |
| 8 | SPAD / FLIM | Lifetime (ns) → NAD(P)H metabolism, FRET, pH/viscosity | **Share** — detector swap behind infinity port | $20-60k | 3-4 | Very high value, **sourcing-blocked**: no Taobao path to a SPAD array. Park until consumer-LiDAR SPADs commoditize. |
| 9 | ECIS / impedance / TEER | Barrier, adhesion, migration (label-free, kinetic) | **Fork** — electrodes contact cells | <$100 chip | 7 standalone / 3 integrated | Strong razor-blade *second consumable*, not a head. Shares gantry/registration/daemon, not the optics. |
| 10 | Electrochemical (O₂/pH/lactate/neurotransmitter) | Amperometric/potentiometric media analytes | **Fork** (prefer optical #5 for no-contact) | low | 7 / 3 | Use the optical route #5 instead where possible. |
| 11 | IR-thermography (microbolometer) | Coarse bay/lid thermal map | Head/lid-side only | ~$150 | 8 | Low. Glass is LWIR-opaque → cannot see the sample plane through the coverslip from below; lid/oblique only. |
| 12 | Photoacoustic | Optical-absorption contrast at depth | Head-swap | $5-23k | 4 | Niche. Acoustic couplant breaks the dry-bay/no-contact rule. |
| 13 | **Luminescence (SiPM, non-imaging)** | ATP/viability, luciferase reporters, pathway + circadian kinetics | **Level-3** — no objective; one large-area SiPM + light guide, scanned well-to-well by the stage that already exists | ~$150-300 | 6-7 | **Reserved, not promised. Re-verdicted 2026-09-23: the row stays, the tier argument does not.** It used to argue that deleting the objective buys "one to two orders of magnitude of solid angle over the 0.25 % NA-0.10 path". Both halves of that moved: 0.25 % was the wrong air-side `NA²/4` model (media-side: **0.140 %**), and the path the geometry now admits is **NA 0.60 at 5.334 %**, i.e. **38.0×** better. The SiPM's residual margin is therefore `100 / 38.0 ≈` **2.6×** at the optimistic end of its own original claim and a **net loss** at the pessimistic (10×) end — while the imaging path **keeps spatial information the SiPM structurally cannot produce** (it reports that the well lit up, never which cells did). **It stays anyway, on different grounds:** one number per well with no focus requirement is still the right *shape* for long kinetic ATP/circadian runs, it is the only candidate that exercises Level-3 at all, and it needs no objective to heat the well. One detector, not Byonoy's 96, because the stage scans. Failure modes are environmental, not optical (see bounded claims). Does not gate the wedge. |
| 14 | **Patterned photostimulation** — *CANDIDATE, not decided; an **actuator**, not a sensor* | Nothing. It *delivers* a spatially patterned optical dose (optogenetics, uncaging, targeted photodamage) to chosen sub-fields inside one well | **Share** — pattern injected at PD-0 in the collimated space, the same slot #2's dichroic uses | unscoped | unassessed | **Recorded as a candidate so the contract does not preclude it. Nothing here is planned, costed, or sourced.** Every other row in this catalog senses; this one perturbs, and that is the missing half of a causality platform. **Within-well randomisation puts treated and untreated cells in the same well** — same medium, same lid, same thermal history, same handling — which removes the well-level confounders that no amount of downstream sensing can subtract. It is also the row that forces the dose-ledger question (§ *The intervention ledger*): an actuator head needs its own `safety_class`, a hardware interlock, and a **logged dose per field** before it is allowed to fire once. No source, no pattern engine, no optical budget and no cost basis has been scoped — do not read this as a plan. |
| — | OCT / CARS-SRS / O-PTIR / light-sheet / SIM-STORM | 3D structure / fast Raman / IR-chem / sectioning / super-res | Whole new instrument or architecturally excluded | high | 1-3 | Platform-headroom slide only. Geometry or NA forbids on this stage. |

**Re-checked 2026-09-23 against the NA 0.45–0.60 ladder and unchanged.** Saying so
explicitly, because "the NA premise moved" is not a licence to re-litigate rows
whose reasoning never rested on it:

- **#3 (multispectral/polarization) and #4 (UCNP ratiometric thermometry) do not
  move, and the reason is structural, not lucky.** Both are **ratiometric** — they
  report I/I₀ or a 525/545 band ratio — so the collection efficiency η appears in
  numerator and denominator and largely cancels. Correcting η from 0.25 % to
  0.140 % therefore changes their SNR integration times, not their verdicts, and
  raising η by 38× is a convenience for them rather than an unblock. **#5 (optical
  O₂/pH chemical spot) rides the same argument** and likewise does not move.
- **#11 (IR thermography) and #12 (photoacoustic) do not move, and cannot.** They
  are blocked on hard physics that no NA buys past: glass is **LWIR-opaque**, so
  #11 cannot see the sample plane through the coverslip from below at any
  aperture; and #12 needs an **acoustic couplant**, which breaks the
  plate-as-consumable no-contact rule regardless of the optical path. These are
  not photon-budget verdicts and were never going to move.
- **#1 (QPI/FPM)** gains resolution with NA but was never photon-limited; it stays
  the wedge. **#8 (SPAD/FLIM)** is sourcing-blocked, not physics-blocked — an NA
  change does not conjure a Taobao SPAD. **#9/#10** are forks on contact grounds.
  **#7 (NV)** is bounded by the sensor-to-cell standoff, not by η (see bounded
  claims).

Rows #3 and #13 come from a review of the commercial solid-state parallel readers
(Byonoy / the Opentrons Flex absorbance module) in
`../knowledge/byonoy_plate_readers.md`: absorbance survives NA 0.10 because it is
ratiometric, what we would ship is serial per-well spectrophotometry of an imaged
field rather than plate reading, and luminescence — which that review found the
catalog was missing entirely — is the one modality that is *better* without an
objective. **That review stated the collection penalty as "NA²/4 ≈ 0.25 %", inherited from
the model this document has now corrected.** Its absorbance conclusion survives
unchanged (ratiometric), and its luminescence margin gains rather than loses,
because the objective path it is compared against collects less than was claimed.
**Closed 2026-09-23:** `../knowledge/byonoy_plate_readers.md` was corrected to the
media-side **0.140 %** in both places and carries a dated block recording it.

### The bounded claims (honesty, load-bearing)

Four entries in the catalog are routinely over-sold, and SMIS documents their
real limits so the project stops spending cycles on them:

- **NV is an mK *reference* thermometer, not intracellular thermometry and not
  cell magnetometry.** The defensible build is architecture (B): a thin NV-diamond
  membrane plus a printed coplanar-waveguide microwave antenna bonded to a
  head-top window ~8 mm below the plate. The diamond and its antenna travel with
  the head, off-plate, fully under module authority, and deliver mK-class
  *non-contact bath / sample-plane* temperature — a real upgrade over the
  thermopiles. It measures the window's temperature, ~8 mm from the cells, **not**
  intracellular temperature. Intracellular FND thermometry through the NA-0.10
  objective is TRL 2-3 and likely will not close without an NA ≥ 0.7 head.
- **NV magnetometry of cells is infeasible on this geometry — do not promise it.**
  The landmark single-neuron result needed the diamond ~10 µm from an *excised
  invertebrate giant axon* (mm-scale, enormous current) and still got SNR ≈ 1.2.
  Mammalian cells through 0.17 mm of coverslip + media with the sensor ~8 mm away
  put the signal **3-4 orders of magnitude below** the NV floor. This is not a
  sensitivity-tuning problem. The only legitimate use of the magnetometry channel
  here is rejecting stray-field artifacts in the mK thermometer (read both ODMR
  transitions to separate B from T).
- **Raman is throughput-limited to sparse spot-checks and wants its own head.**
  Spontaneous Raman cross-sections (~10⁻³⁰ cm²) × the collection fraction η
  (**0.140 %** at the fitted NA 0.10, **5.334 %** at the NA 0.60 the geometry now
  admits — corrected 2026-09-23 from a mis-stated 0.25 %) ×
  cellular autofluorescence make per-point integration realistically 1-30+ s. A
  hyperspectral map of one Ø6.21 mm well at 10 µm steps is ~300k points —
  physically impossible at screening throughput. Raman on this platform is a
  *targeted molecular spot-check*, it genuinely wants a dedicated higher-NA
  Level-2 head, and the heavy cooled spectrometer **rides offboard via fiber**,
  never on the head (see the offboard rule). It is the flagship R&D module,
  partner-built against a frozen spec, and must not gate the platform.
- **Luminescence is a photon-collection problem, and the objective is the
  problem.** The over-sell is "we get luminescence free on the imaging head":
  through the 4× NA-0.10 path a reporter-level bioluminescent signal is
  integration-bound — seconds to minutes per field, flux-dependent — because the
  objective throws away **99.86 %** of an emission that has no excitation to turn
  up (corrected 2026-09-23 from 99.75 %, which came from the air-side `NA²/4`
  model; the media-side collection at NA 0.10 is 0.140 %, not 0.25 %).
  The defensible build is **Level-3, non-imaging**: one large-area SiPM with a
  light guide directly under the well, one number per well, scanned by the stage
  (#13). What that buys is solid angle and no focus requirement; what it does
  **not** buy is spatial information — it reports that the well lit up, never
  which cells did. **The photon half of this argument is now weak.** At the
  NA 0.60 the corrected geometry admits, the objective throws away 94.67 %, not
  99.86 % — a 38.0× improvement that eats most of the SiPM's claimed one-to-two
  orders and leaves roughly 2.6× at best (row #13). The row survives on *shape*
  (one number per well, no focus, no heat sink over the cells, and Level-3 needs
  an exerciser), not on solid angle. Stating this rather than deleting it,
  because the original reasoning was published and someone will cite it. It is also the only catalog entry whose dominant failure modes
  are environmental rather than optical: stray light in the bay (the WS2812 ring
  and any deck-side leak must be dark during acquisition, which the bay is not
  built for today), SiPM dark-count rise at the 37 °C row setpoint, and
  plate/mat afterglow following any illuminated step. Those three, not the
  detector, are the build. Electrically it is an ordinary tenant of the existing
  bus — SiPM bias (~27-55 V, part-dependent) is a **module-side** boost from the
  HEAD-BUS +24 V rail, which the FREE column already allows — so appending #13
  forces no SMIS-major bump. An appended row owes the contract that check.
- **SPAD/FLIM is sourcing-blocked, not physics-blocked.** The optics are a clean
  detector swap behind the infinity port; the wall is that a SPAD array is
  $20-60k+ with no China/Taobao path. Park it; revisit when automotive-LiDAR SPAD
  supply commoditizes.

**Near-term wins (build now):** #1 QPI/FPM, #2 fluorescence, #4 UCNP thermometry,
with #3 and #5 as cheap riders. **Frontier bets:** #6 Raman and #7 NV-thermometry
arch-(B). **Reserved Level-3 candidate:** #13 luminescence — cheap and
physically favorable, but it spends the same solo build-hours as the wedge, so it
waits behind #1 and #2 and is not a third head. **Unscoped candidate:** #14
patterned photostimulation — recorded, not planned, and it changes the *kind* of
thing SMIS hosts (an actuator), which is a contract question before it is a
build question.

The 2026-09-23 re-derivation does not reorder this list. #2's position improves on
the merits — it is now a photon-rich modality rather than a bright-labels-only
one — but it was already #2 for wedge reasons, and #6 moving from "foreclosed" to
"thermally constrained" does not make a $10-23k partner-built spectrometer a
near-term solo build.

## SMIS v0.1 — the interface contract

Status: **DRAFT-FOR-FREEZE.** Authority class: COTS-authority exception. Authority
boundaries: the dock plane (mechanical), the infinity port (optical), the HEAD-BUS
connector (electrical). Above those three planes = FROZEN platform contract; below
them = FREE per-module design.

### FROZEN vs FREE at a glance

| Layer | FROZEN (platform owns) | FREE (module owns) |
|---|---|---|
| Mechanical | Dock plane DP-0, 3-2-1 kinematic seats + 3 magnets + dowel, bolt pattern, mass ≤ 900 g, envelope 120 × 347.5 × 40 mm, Ø32 barrel keepout, **scan-corridor footprint ≤ 15.56 mm**, 62 mm Z, front face ≤ z = −8, **WD ≥ 19.90 mm** | Internal optomech, where mass sits, fold count, source mounts |
| Optical | Infinity-port plane PD-0, Ø20 clear collimated aperture, 30 mm cage + RMS + C-mount triple standard, parfocal datum, tube-lens-to-sensor = 50 mm | Whatever drops into the infinity space; the objective itself if Level-2; nothing if Level-3 |
| Electrical | HEAD-BUS pinout (24 V / 5 V / 3.3 V / GigE / I2C / 1-Wire / MW-coax / 2× interlock / shield), blind-mate float connector, no hot-mate, ID-EEPROM at I2C `0x50` | Which rails it draws, what rides the data lane, MW power, laser class |
| Software | `module.json` manifest schema, the driver plugin ABI, `acquire(well, lease) -> Evidence`, the safety-class enum, the lease protocol | Driver internals, calibration model, per-modality params |
| Registration | 16 × Ø2 mm fiducials on the plate-support frame *are* the world frame; only the module→dock transform is re-established on a swap | The module's internal optical-axis offset (declared in manifest, verified on dock) |

> **Added 2026-09-21.** The Ø32 keepout is NOT the binding mechanical gate and never
> was. The binding gate is `scan_corridor_footprint_max_mm` = **15.56 mm**
> (`cad/one_row_coupon.params.json`, `src/aevum_smis/manifest.py`), which the SMIS
> code already enforces at dock. It currently **rejects every RMS-threaded head**,
> including this document's own Ø20 reference 4×, because an RMS thread floors near
> Ø20.32. The RMS freeze below is therefore frozen *and currently unsatisfiable in
> the bay*; it remains valid for the static Stage-0 bench, which has no corridor.
> A second frozen figure follows from the standoff correction the same day: the
> cell plane sits **19.90 mm** above the z = −8 front-face ceiling, so WD ≥ 19.90 mm
> is a hard admission criterion and excludes the entire short-WD catalogue.
>
> **Superseded 2026-09-23 — both of those figures answered the wrong question.**
> The 15.56 mm budget was computed against a 99 mm scan spanning all 12 well
> columns, but the 88 × 52 mm tile aperture only ever admitted 8 (span 63.0 mm);
> against the reachable columns the budget is **51.56 mm**, and an RMS barrel at
> Ø20.32 clears by 2.5×. And 19.90 mm is the **traverse-plane** standoff: running
> the existing `focus_stroke_z` = 12.0 upward puts the nose at z = +4.00 and the
> **working distance at 7.90 mm**, with 32 mm of `observer_sweep_depth_z` slack
> left. See § *The one number that organizes the catalog* for the derivations
> and measurements.
>
> **The FROZEN cell above is deliberately left as-is.** Changing
> `scan_corridor_footprint_max_mm` or the WD floor is a **SMIS-major** bump that
> re-validates every head, and it also requires a code change
> (`src/aevum_smis/manifest.py`) that this documentation pass is not authorised to
> make. The two recorded recommendations, neither applied:
>
> 1. **Parameterise the traverse check by *reachable* columns**, not by all 12, so
>    the corridor budget reads 51.56 mm. This is a check-scope fix, not a geometry
>    change — no CAD moves.
> 2. **`src/aevum_smis/manifest.py:193-200` computes `vertical_required` as an
>    additive sum** (`front_face_clearance + front_end_height_z + focus_stroke_z +
>    service_margin_z ≤ z_budget`). At 8 + 57 + 18 = 83 > 62 it rejects every
>    60 mm-parfocal objective on a column the solid model says is clear (Ø25 mm
>    probes rise unobstructed to z = 11.71). Recommend a **swept-envelope** check
>    in its place — while **keeping a hard retract-plane assertion**, because the
>    retract plane is what makes tile-to-tile traverse safe (3 retract cycles per
>    row of 4 tiles; the `plate_support_frame` blocks at z = 0.05 between tiles).

A change to anything in the FROZEN column is a **SMIS-major** bump and re-validates
every head. A change in the FREE column is a per-module bump. SMIS-minor is
additive-only. This is the same rule `coordinate_system.md` applies to pose
schema, and the same contract discipline `power_section.md` froze for the GX16
pinout.

### The three tiers

- **Level-1 — back-end swap.** Objective, fold, tube lens, and oblique LED ring
  stay; the module is a cage insert dropped into the infinity space (fluorescence
  dichroic cube, 50:50 beamsplitter for epi, fiber pickoff to an offboard
  spectrometer, polarizer/analyzer). Parfocal by construction, Tier-A
  registration. Cheapest and fastest; #1-#5 all live here.
- **Level-2 — whole-head swap.** The module brings its own objective (high-NA
  Raman head, long-WD head). The entire head undocks at the kinematic dock; the
  new head must still respect the envelope, mass, keepout, Z budget, and present
  the same HEAD-BUS. Tier-B/C registration.
- **Level-3 — non-imaging.** No objective, no infinity port: impedance probe,
  MW-resonator, NV quantum head, SiPM luminescence head (#13 — the first
  candidate that is *better* in this tier than above it, and the first the tier
  has to actually exercise). Uses only the dock + bus + manifest.

### Mechanical — the kinematic dock (FROZEN)

- **Dock plane DP-0:** a horizontal plane on the gantry Z-carriage; all module
  Z-offsets are declared downward from it. DP-0 is the single mechanical truth.
- **Envelope, inherited verbatim from the bench, not renegotiable:** swept body
  **120 × 347.5 × 40 mm**; **Ø32 mm** barrel keepout (= `objective_keepout_diameter`
  in `cad/one_row_coupon.params.json`); **62 mm** usable Z below DP-0
  (= `carriage_height_z`); front face **≥ 8 mm below the plate** (never crosses
  z = −8, = `carriage_top_clearance_z`).
- **Mass budget ≤ 900 g (target 600 g).** The Y-truck indexes 334.5 mm and focus-Z
  must settle inside the bench's vibration spec (≈ ±27 µm at 4×) at exposure;
  heavier heads lower the structural-loop resonance and lengthen settle. Mass and
  CG are manifest fields that gate the scan-speed profile.
- **Coupling — a quasi-kinematic 3-2-1 with magnetic preload.** A true Maxwell
  kinematic is fussy to print and a contamination trap in a wet-adjacent bay, so
  the decisive choice is **3 hardened-ball-on-cone/vee/flat contacts + 2 pull
  magnets + 1 anti-rotation dowel.** One cone (3 DOF), one vee (2 DOF), one flat
  (1 DOF) = 6 contacts, 6 DOF, exactly constrained. Three Ø6 mm grade-25
  chrome-steel balls (`钢珠 6mm`) press into the *module*; the cone/vee/flat seats
  are on the *gantry* and are the long-lived datum (precision on the shared part,
  not the swap-frequency module). Preload by **3× N52 pot magnets Ø10×5 mm**,
  ~3 kg each (`强力磁铁 沉孔 D10`) → ~9 kg pull. The margin is taken against the
  **1 g-scan separating demand** — the head's static weight *plus* its inertial
  reaction at 1 g (~2× the 900 g weight = 1.8 kg-f), not the static weight alone —
  giving 9 / 1.8 = **5.0×**. (The original 2-magnet figure read ~6.7× against static
  weight but only ~3.3× against this demand; the SM-1.2 dock-check review surfaced
  the load-case error and the spec moved to 3 magnets — see `decision_log.md`.) A
  single Ø3 dowel + lead-in chamfer makes the dock one-handed and blind; 2× M3
  captive thumbscrews are secondary retention if a magnet is heat-demagnetized.
- **Repeatability target: ≤ 5 µm lateral** (reserved-and-unproven until the bench
  measures it — see Top 3 moves). 5 µm is comfortably inside the 4× DOF (55 µm
  total, ±27 µm — `observer_optical_bench.md`, § *Optical configuration*, row
  "Depth of field, NA 0.10"), so 4× and low-NA heads trust
  the coupling. **At 10×/NA 0.25 the DOF is 8.8 µm
  total (±4.4 µm) and the coupling alone is not enough** — those heads declare
  `requires_post_dock_autofocus: true`.
  **Extended 2026-09-23 to the new ladder:** DOF = λ/NA² gives **4.17 µm total at
  NA 0.363, 2.72 µm at 0.45, 1.53 µm at 0.60** (half-ranges ±2.09 / ±1.36 /
  ±0.77 µm). Every head on the reachable ladder is therefore at or inside the
  5 µm dock target, so
  **`requires_post_dock_autofocus: true` is mandatory for all of them** — the
  10× carve-out is now the general case, not the exception.
- **Focus is not a drift problem, it is a seating problem — do not buy the wrong
  fix.** 80 mm printed legs expand 5.60 µm/K (PLA), 4.80 (PETG), 7.20 (ABS),
  against 1.84 (aluminium), 0.96 (steel), 0.10 (invar), so at NA 0.60's 1.53 µm DOF
  a fraction of a kelvin walks the structure out of focus and invar looks
  compelling. **It is the wrong lever.** The operative driver is **plate-to-plate
  topography and seating**, not temporal drift: at DOF 1.53 µm the head must
  **refocus at every well visit regardless of how stable the structure is.** Once
  per-visit refocus exists, structural drift is a second-order correction on a
  loop that already runs. Spending the budget on invar before the focus loop
  exists buys nothing.
  **Recommended architecture (not built, not decided):** through-objective
  **dual-surface IR autofocus on the coverslip** — built **first as an open-loop
  drift gauge**, logging the correction it *would* apply, before any loop is
  closed. An open-loop gauge is falsifiable and cannot crash a plate; a closed
  loop built first is neither.
- **Recommended hardware Z-gate (not applied — a code/firmware change).** At
  40×/NA0.60 the nose sits **2.6–3.4 mm below a consumable plate** that is
  positioned by hand. Recommend a **hardware gate that cuts XY motor enable
  whenever the nose is above z = 0**, series-wired into the existing interlock
  loop alongside the head-docked seat switch and bay-lid-closed contacts, so
  software can disable but never enable across it. This is the same fail-closed
  pattern the laser and MW loops already use, applied to the axis that can destroy
  the consumable and the objective in one move.
- **Swap never touches the wet stack.** The dock is *under* the deck; the plate is
  70+ mm *above*, on the opposite side of the deck plane. The swap runs with Z
  retracted to dock-park (z = −60) and Y at the service index off all four plates,
  approached from the reserved service-raceway side. Same frozen service order as
  the umbilical: de-energize → unplug → swap → re-plug → re-energize → detect →
  re-register.

### Optical — the infinity port (FROZEN)

- **Port datum plane PD-0:** the plane in the collimated space where a back-end
  mates, set **28 mm above the objective shoulder** (the infinity space is
  25-40 mm; 28 mm leaves room either side for a fold/dichroic). The row-coupon
  CAD now surfaces this as `observer_infinity_port_datum_check`, a Gate-6
  validation-only PD-0 datum slab that fails if PD-0 leaves the front-end Z
  envelope.
- **Clear aperture at PD-0: Ø20 mm** of unvignetted collimated beam. The
  4×/NA0.10 + f50 train fills only ~Ø8-10 mm; Ø20 gives headroom for higher-NA and
  off-axis fields. **Checked against the full NA 0.45–0.60 ladder 2026-09-23 and
  the Ø20 freeze holds with ≥ 2× margin.** The pupil an infinity objective
  projects is `D = 2 · f_obj · NA` with `f_obj = f_ref / M_nameplate`, so it
  depends on the objective's own focal length and **not** on our tube lens:

  | objective | f_ref | f_obj | NA | pupil D |
  |---|---:|---:|---:|---:|
  | 4× plan-achromat (fitted) | 180 | 45.0 | 0.10 | 9.00 mm |
  | Nikon CFI S Plan Fluor ELWD 20×/0.45 | 200 | 10.0 | 0.45 | 9.00 mm |
  | Nikon CFI S Plan Fluor ELWD 40×/0.60 | 200 | 5.0 | 0.60 | 6.00 mm |
  | Mitutoyo M Plan Apo 20×/0.42 WD20 | 200 | 10.0 | 0.42 | 8.40 mm |
  | water 60×/1.20 (scale only — thermally excluded) | 200 | 3.33 | 1.20 | 8.00 mm |

  High NA does **not** mean a big pupil, because high-NA objectives are short-focal.
  Ø20 is overfilled only when `NA / M_nameplate > 10 / f_ref` (0.056 at f180,
  0.050 at f200) — i.e. by a *low-magnification* high-NA objective, which the
  ladder does not contain.

  *(Superseded 2026-09-23. This bullet previously closed with a "session check at
  a delivered 4×" that took `f_obj = f_tube / M = 50 / 4 = 12.5 mm` and reported
  **9.07 mm** at NA 0.363 and **15.32 mm** at NA 0.613, "both inside Ø20". The
  form and the conclusion were both wrong, and they contradicted the same bullet's
  own rule two lines above. `f_obj` is a property of the **objective** —
  `f_ref / M_nameplate` — not of our tube lens; substituting f_tube understates
  the pupil by exactly `f_ref / f_tube` = 180/50 = **3.6×**. Recomputed under the
  stated rule, a 4× at f_ref 180 has f_obj 45.0 mm, so `D = 90 · NA`: NA 0.363 →
  **32.7 mm** and NA 0.613 → **55.2 mm**, both of which *overfill* Ø20, not fit
  inside it. The pairing was not a catalogue one either — no 4× on the ladder
  carries NA 0.363 or 0.613; those are the Maréchal cap and a scratch value, not
  objectives. None of this moves the freeze: the Ø20-holds conclusion is carried
  by the table above, where the real 20×/0.45 projects 9.00 mm and the real
  40×/0.60 projects 6.00 mm, and that is the defensible support for it. Found by
  checking the bullet against its own formula.)*
- **Sampling: the f = 50 mm tube lens is the throughput/resolution decoupler, and
  it undersamples.** Against `f_ref` the effective magnification is
  `M_eff = nameplate × 50 / f_ref` = nameplate/3.6 (Olympus, f180) or nameplate/4
  (Nikon, Mitutoyo, f200). A nameplate "40×" therefore runs at **M_eff 10–11.11×**,
  and the fitted 4× runs at **M_eff 1.11×**. On the IMX178's 2.4 µm pixels
  (active array 3088 × 2064 = 7.41 × 4.95 mm, the figure
  `observer_optical_bench.md`, § *What NA actually buys*, uses in its opening line
  "sensor IMX178 (2.4 µm pixels, 3088 × 2064, 7.41 × 4.95 mm active)"):

  | path | M_eff | sampling at sample | Nyquist needs | verdict |
  |---|---:|---:|---:|---|
  | 4×/0.10 fitted | 1.11× | 2.16 µm/px | 1375 nm | grossly undersampled |
  | 20×/0.45 ELWD | 5.0× | 0.48 µm/px | 306 nm | undersampled 1.6× |
  | 40×/0.60 ELWD | 10.0× | 0.24 µm/px | 229 nm | undersampled 1.05× |
  | any NA 0.363 path | — | needs ≤ 0.379 µm/px | — | needs **M ≥ 6.34×** |

  **Consequence, and it is a design rule, not a complaint:** a high-NA head on the
  frozen f50 train buys **photons** (η up 38×) at almost no throughput cost, and
  buys **resolution only if f_tube rises**. Do not justify a high-NA purchase on
  resolution while the tube lens is 50 mm. Raising f_tube is a **SMIS-major**
  change — `tube-lens-to-sensor = 50 mm` is frozen below.
- **Triple mechanical standard, all three present, frozen:** the **30 mm cage**
  system (4× Ø6 mm rods, structural), the **RMS thread** on the objective side
  (parfocal 4×/10×/20× swap), and **C-mount** on the detector side (inherited
  directly from the bench's IMX178 camera). They are orthogonal roles — cage
  carries load, RMS carries the objective, C-mount carries the detector — so
  freezing all three costs nothing and lets off-the-shelf adapters bolt to the
  port. **Tube-lens-to-sensor = 50 mm** is frozen for the shared imaging back-end
  (the one critical spacing the bench pinned); a re-imaging Level-1 back-end
  declares its own conjugate past PD-0. The same CAD check pins the Ø20 aperture,
  30 mm cage standard, RMS/C-mount presence, and 50 mm spacing so Level-1
  back-end swaps cannot silently drift the optical datum.
- **The offboard rule (mass + thermal escape hatch).** Heavy or bulky analyzers —
  Raman spectrometer, cooled detector, pulsed laser, high-sensitivity PMT — **never
  ride the head.** The head carries only a fiber pickoff/launch at PD-0; the
  analyzer lives offboard in the PSU/compute enclosure, coupled by a fiber routed
  down the service raceway alongside the GX16 umbilical. This is exactly how the
  80 mm bay budget is spent without breaking the 900 g ceiling.

### Electrical — the HEAD-BUS (FROZEN)

A single blind-mate connector at the dock, **float-mounted ±0.5 mm** so the
kinematic balls register position and the connector follows (it never fights the
datum). **No hot-mate:** rails are de-energized at the offboard PSU before any
dock/undock, enforced by a make-last/break-first short pin on the interlock loop —
undocking physically opens the laser and MW enable loops before any signal pin
parts. HEAD-BUS is a **superset of the GX16 contract** from `power_section.md`,
reusing its rail definitions, levels, and single-point-earth ground plan so one
offboard PSU serves both umbilicals.

| Signal group | Line(s) | Spec | Notes |
|---|---|---|---|
| +24 V / GND | 2 | from HRP-150-24, fused at head branch | motion/heater-class loads only |
| +5 V / GND | 2 | from DDR-15G-5, isolated | head-Pi, LED-ring driver |
| +3.3 V / GND | 2 | ≤ 500 mA, sensor/logic | matches GX16-6 level |
| I2C SDA/SCL | 2 | 3.3 V logic | ID-EEPROM + low-rate module sensors |
| 1-Wire | 1 | DS28E07-class | redundant ID + per-module cal vault |
| GigE data | 4 (M12 X-coded) | 1000BASE-T | head-Pi capture lane; the frozen high-speed path — reuse it, do not invent CSI-over-coax |
| MW coax | SMP/SMA | DC-6 GHz, **populated NV-only**, capped otherwise | NV magnetometry/thermometry |
| Fiber bulkhead | FC/SMA905 | on the float carrier | spectroscopy offboard signal (optical, not electrical) |
| INTERLOCK_LASER | 1 | active-low hardware loop | breaks laser-enable if head undocked or lid open |
| INTERLOCK_MW | 1 | active-low hardware loop | breaks MW-amp enable |
| ALARM | 1 | open-drain active-low | inherited from GX16-6 pin 5 semantics |
| SHIELD / chassis | 1 | 360° backshell | single-point bonded at the sensor-cluster star — **no second earth bond** (power-section rule) |

The frozen HEAD-BUS table is mirrored as a machine-checkable schema in
`src/aevum_smis/head_bus.py` (`FROZEN_HEAD_BUS`). The validator pins the required
signal groups, unique line IDs, no-hot-mate rule, EEPROM address `0x50`,
make-last/break-first active-low laser/MW interlocks, and single-point shield
bond so a hardware record cannot silently drift from this table.

The observer offboard umbilical is separately frozen in
`src/aevum_smis/observer_umbilical.py` (`FROZEN_OBSERVER_UMBILICAL`): GX16-4 carries
24 V and 5 V, GX16-6 carries I2C, 3.3 V, alarm, and the observer enable loop, and
GigE stays on the M12 X-coded bulkhead rather than GX16. The reconciliation check
proves HEAD-BUS remains a superset of those GX16/M12 authority classes before a
future dock or head revision can claim compatibility.

**Module auto-ID and the cal vault.** An **ID-EEPROM at fixed I2C `0x50`** holds
the module identity and manifest digest (`sku`, `module_serial`, `smis_version`,
`hw_rev`, `safety_class`, `axis_offset_mm`, `parfocal_z_mm`, `mass_g`, `cg_mm`,
`manifest_sha256`), read on dock by `platform.detect()`. A **1-Wire DS28E07**
serves as the calibration vault and anti-counterfeit token (factory cal blob plus
a crypto challenge) so the platform can **refuse to drive a Class-4 laser from an
uncertified head** — the connector-level expression of the Sensirion
genuine-parts discipline in `power_section.md`/`sensor_pcb.md`. The `0x50`
EEPROM never collides; any module-local I2C sensors sit behind a per-head
TCA9548A, the same pattern the dual STC31/SHT41 PCBs already use. The
laser/MW interlocks are **hardware** loops (series-wired through head-docked seat
switch, bay-lid-closed, OT-2 bridge E-stop) — software can additionally disable
but can never override the loop to enable.

### Software — the `acquire() -> Evidence` ABI (FROZEN)

A module is, to the orchestrator, a thing that produces evidence at a well under
the motion lease. It plugs directly into the OT-2 bridge core
(`agent_ot2_bridge.md`) and the immutable Evidence packet model
(`evidence_model.md`). Every modality implements one driver interface:

```python
class ModuleDriver(Protocol):
    manifest: Manifest
    def on_dock(self, platform: PlatformCtx) -> RegistrationResult: ...   # tier A/B/C
    def configure(self, params: dict) -> None: ...
    def acquire(self, well: WellTarget, lease: MotionLease) -> Evidence: ...  # the polymorphic call
    def health(self) -> HealthReport: ...
    def on_undock(self) -> None: ...                                      # source off, park, release
```

`acquire(well, lease) -> Evidence` is the single polymorphic call. A brightfield
head returns an image stack; a Raman head returns a spectrum at a point; an
impedance head returns a Z(f) sweep — **all return the same `Evidence` packet
type** the bridge already defines (immutable, handle-referenced, carrying
`manifest_sha256`, `module_serial`, well id, run/command ids, calibration ref).
The orchestrator's loop — *for each well in plan: ensure lease → drive stage →
`acquire(well)` → write evidence → gate* — never changes per modality. **One
orchestrator, N modalities** is the platform payoff. Drivers are entry-point
plugins (`aevum_modules.<modality>`) loaded by the manifest `driver` field on
dock; the platform never hard-codes a modality.

The manifest carries **falsifiable assertions** the platform re-checks against the
frozen keepout — `mechanical.envelope_ok` and `front_face_z_mm` are verified
against the same `8 + FE_z + stroke ≤ 62` and `barrel Ø ≤ 32` arithmetic the
observer bench made test-failable. A manifest that claims an envelope it does not
fit is rejected at dock, not discovered by a crash.

### The intervention ledger (CANDIDATE — recorded, not decided)

Two findings from 2026-09-23 point at the same missing field in the Evidence
contract, and both are recorded here as **candidates for `evidence_model.md`'s
owner to accept or reject** — SMIS does not get to extend the Evidence schema
unilaterally, and nothing below has been agreed.

- **Every optical pass is an unlogged treatment.** Fluorescence (#2) delivers an
  excitation dose. UCNP (#4) delivers 980 nm pump power. Raman (#6) delivers a
  785 nm laser onto cells. #14, if it is ever built, delivers dose *on purpose*.
  The platform currently records what it *measured* and not what it *did*, which
  means a cell's photo-history is reconstructable only by replaying the schedule.
- **The thermal effect is correlated with treatment.** A close objective pulls
  the sample plane down by ΔT (§ *The thermal wall*), and which wells get a long
  dwell is exactly which wells are interesting. That is a confound with the same
  index as the independent variable.

**The candidate:** a **photodose / thermal-dose / intervention ledger** as a
first-class part of the Evidence packet — per well visit, the source, wavelength,
power, exposure, cumulative dose, dwell time, and estimated sample-plane ΔT. It
is cheap (every number in it is already known to the driver at `acquire()` time)
and it converts an invisible confound into a regressor.

**A second candidate from the same session: `fields_per_well` as an explicit
Evidence sampling parameter.** Exhaustive tiling does not close. The arithmetic
below is derived on the **128 optically reachable wells** — this is the
reachable-set figure, not the 384-well grid figure (see the reachable-count
correction under § *The scaling roadmap*, and `observer_optical_bench.md`,
"Tiling: the throughput term nobody has costed", which computes the
identical quantity at f_ref 200; the 1.23× convention band is stated below):

| basis | tiles/pass | at 0.4 s/tile | at 12.7 MB/frame | × 48 hourly passes |
|---|---:|---:|---:|---:|
| **128 reachable wells, Nikon f_ref 200 / M_eff 10.0×** — today | **~10,500** | **~1.2 h** | **~133 GB** | **~6.4 TB** |
| 128 reachable wells, Olympus f_ref 180 / M_eff 11.11× — the other convention, 1.23× worse | ~12,900 | ~1.4 h | ~164 GB | ~7.9 TB |
| 384 wells at M_eff 10.0× — only if the aperture is enlarged to ~110 × 74 mm | ~31,400 | ~3.5 h | ~399 GB | ~19.1 TB |
| 384 wells at M_eff 11.11× — the same enlargement, band edge | ~38,800 | ~4.3 h | ~493 GB | ~23.7 TB |

The per-well term: at NA 0.60 on a nameplate 40× read at the **Nikon f_ref 200
convention, M_eff 10.0×** (2.4/10.0 = 0.24 µm/px), the IMX178's
3088 × 2064 / 7.41 × 4.95 mm array covers **0.741 × 0.495 mm = 0.367 mm²** at the
sample against a ~30.0 mm² well (Ø6.18 mm,
`well_bottom_area_equivalent_diameter`) → **~82 tiles/well**. The frame term is
3088 × 2064 at 16 bit = 12.7 MB.

**The costed head fixes the convention; the other convention is the band edge,
and the band should be read, not the point.** The ELWD head costed here is a
*Nikon* CFI S Plan Fluor 40×/0.60 and Nikon's f_ref is 200, so `M_eff = 40 × 50 /
200 = 10.0×` — that is the bolded row, and it is the same basis
`observer_optical_bench.md` uses for the same head. Read at the Olympus f_ref 180
convention (`40 × 50 / 180 = 11.11×`) the field shrinks to 0.667 × 0.446 mm =
0.298 mm² and the well needs ~101 tiles. The two conventions differ by 1.23× and
both fail the cadence the same way; name the f_ref whenever this number is quoted.

> **Superseded 2026-09-23.** An earlier revision of this paragraph costed the pass
> over "**192 wells**" — 19,200 tiles, ~2.1 h, ~246 GB/pass, 11.8 TB over 48
> passes. 192 has no derivation anywhere in the repo: it is neither the 384-well
> grid nor the 128 reachable wells this same document establishes under § *The
> scaling roadmap*, and it put a headline throughput/storage budget 1.5× away from
> `observer_optical_bench.md`'s figure for the same quantity, from the same
> session. It is withdrawn in favour of the table above. Found by a
> cross-file consistency check. `remaining_work.md` (SM-4.5 and the Track-6
> critical-path summary) inherited the 192-well version and was corrected in the same
> pass; both now carry the 128-well basis and state the 192-well figures as withdrawn.
>
> **Corrected again 2026-09-23, second pass — the headline row changed basis.**
> The table's bolded "today" row was the Olympus f_ref 180 / M_eff 11.11× basis
> (~12,900 tiles, ~1.4 h, ~164 GB, ~7.9 TB) while `observer_optical_bench.md`
> bolds ~10,500 / ~1.2 h / ~133 GB / ~6.4 TB for the *same quantity* and the
> *same named head*, a Nikon CFI S Plan Fluor ELWD 40×/0.60, at f_ref 200. That
> file does not treat the two as interchangeable: it records the 11.11× figures as
> an **error** for this head ("this paragraph inherited the Olympus divisor while
> naming a Nikon head … ~24 % high on tile count and storage") and states that
> every figure in it for that head is computed at M_eff 10.0×. Since both
> documents cost the same head, the bolded row here is now the f_ref 200 one and
> 11.11× is demoted to the explicit 1.23× band edge. The earlier wording that this
> file "must stay in step with" the bench doc has been replaced by naming the
> convention, which is the thing that actually has to match. Found by comparing
> the two files' bolded headlines.

Neither the time nor the storage is compatible with an hourly-cadence mission, and
no amount of NA fixes it — the 384-well rows are worse on both axes, so *enlarging
the aperture makes this problem larger, not smaller*. **"N random fields per
well" has to be a declared, logged sampling parameter rather than an implicit
consequence of how long the run was allowed to take** — declared, because the field count is a statistical
property of the evidence and belongs in the packet, not in an operator's memory.
Both candidates are unowned by this document; they are recorded so they are not
rediscovered.

**Tie to the lease and fail-closed.** `acquire()` runs only while the driver holds
a valid `MotionLease` from the bridge's single-writer lock; a module is just
another lease-respecting client, and an undock releases the lease. The bridge
reads `safety_class` and refuses source-enable unless the hardware interlock loop
is closed *and* the 1-Wire cal vault validates. Manifest-digest mismatch, missing
post-dock registration, evidence-write failure, or interlock-open → no motion, no
source. These are not new rules; they are the bridge's existing non-negotiables
applied to the module boundary.

### Registration survives the swap

Registration is anchored on the **16 × Ø2 mm fiducials on the plate-support
frame** (`observer_fiducial_diameter = 2.0` in `cad/one_row_coupon.params.json`).
That is the world frame and it does **not** move when a head swaps. A swap only
re-derives the **module→dock transform** — where this head's optical axis sits
relative to DP-0 — at one of three tiers declared in the manifest:

- **Tier A — trust the coupling** (default for 4× and low-NA): apply the declared
  `axis_offset_mm` / `parfocal_z_mm`, verify with one fiducial touch-up (~5 s).
- **Tier B — re-fiducial** (high-NA / Level-2): 3-fiducial affine solve + per-region
  autofocus map (~30-60 s). Required whenever `requires_post_dock_autofocus`.
- **Tier C — full re-cal** (non-parfocal Level-2, or first install of a SKU): full
  16-fiducial solve + focus map + the module's own ritual (dark frame, lamp
  warm-up), cached by `module_serial`.

**Added 2026-09-23 — the tiers cover the *swap*, not the *visit*.** All three
tiers above answer "where is this head's axis relative to DP-0 after a swap".
None of them answer "is this well in focus right now". At the DOF the reachable
ladder implies (2.72 µm at NA 0.45, 1.53 µm at NA 0.60), **per-well-visit refocus
is required independent of tier**, because plate topography and seating vary
well-to-well within a single plate. Tier A's "one fiducial touch-up (~5 s)" is a
registration check, not a focus policy, and must not be read as one.

This policy is encoded in `src/aevum_smis/registration.py`. Docking, manifest
compatibility, and registration are separate gates: a head may be mechanically
accepted and still fail closed for acquisition if `on_dock()` reports too weak a
tier, too few fiducials, an unknown tier, or `ok=false`.

### FROZEN vs FREE, one sentence

The dock plane, the Ø20 infinity port on cage+RMS+C-mount, the HEAD-BUS pinout,
the `module.json` schema, and the `acquire(well) -> Evidence` ABI are the immovable
platform contract; everything a head does below those planes — optics, source,
analyzer, calibration — is the module's free design, trusted only after digest +
interlock + registration check.

## The scaling roadmap

### Build sequence — each head validates exactly one interface layer

The discipline is *never build a modality to get the modality; build each
modality to validate the one interface layer whose failure would kill the
platform, in that order.* Each step ships a usable instrument on its own.

| Order | Head | Proves (the interface layer) | The hard part it retires |
|---|---|---|---|
| 0 | Oblique brightfield (the bench head) | Dock + fiducial registration + OT-2 lease | "Can I image the **reachable** wells from below, repeatably, with trustworthy coordinates?" |
| 1 | **QPI / FPM** (LED matrix) | Compute/registration spine, zero new optics | "Is the reconstruction pipeline robust across the **reachable** well set?" — and it is the wedge |
| 2 | **Fluorescence 1-ch** | **Infinity port + electrical auto-ID** | "Does a real dichroic drop in with zero registration penalty, and does the head self-announce?" — for ~$150, not after a Raman build |
| 3 | 2nd fluor head (multi-band) | **Hot-swap interchangeability, N=2 → FREEZE the spec** | "Two heads, one stage, swap without recal, config travels with the head?" Modularity is unproven until N=2 |
| 4 | Raman pickoff (partner-built) | 80 mm bay + **offboard fiber back-end bus** | "Is the bay a real systems budget or a fiction?" |
| 5 | NV-thermometry / non-optical | The abstraction survives a non-camera | "Does the platform host something that isn't a microscope?" |

> **"384 wells" was wrong and is corrected here, 2026-09-23.** The optically
> reachable count is **128 of 384**, not the **384** that `covered_well_count`
> reports and not the intermediate **240** that counts well *centres* falling
> inside the 88 × 52 mm tile aperture. `covered_well_count` is
> `len(all_well_centers)` (`src/aevum_cad/row_coupon/layout.py:865`, `:965`)
> and therefore returns the full grid, 384 — 240 was never a code output, only a
> figure that appeared while checking it (`decision_log.md`, § *2026-09-23 — the
> optically reachable well count is 128, not 384 and not 240*). Both
> intermediate counts ignore that the optical cone — or the physical nose — needs
> clearance at the aperture plane. At the long WD 19.90 the cone is
> 9.27 mm there (4.64 mm edge inset → 128/384); at short WD with a nose OD of
> 8–20 mm the inset is 4–10 mm → **also 128/384**. The two regimes give the
> identical answer, which is why this is a geometry fact and not a working-point
> choice. **Enlarging the aperture to ~110 × 74 mm gives 384/384 at the long-WD
> optical inset of 4.64 mm — and for any nose OD ≤ 11 mm.** The requirement is
> `99.0 + 2 × inset` by `63.0 + 2 × inset`, so a fatter nose needs more: up to
> ~119 × 83 mm at OD 20 mm. ~110 × 74 is the *long-WD optical* answer, not a
> nose-independent one. Enlarging it would
> simultaneously re-impose the 15.56 mm corridor budget, because a 12-column
> scan is exactly what that budget was computed against. Reach and head footprint
> are coupled; neither can be improved in isolation.
>
> This number is not SMIS's to fix (the aperture is `dry_bay.aperture_length_x` /
> `aperture_width_y` and `covered_well_count` is computed elsewhere), but the
> roadmap above was making a claim in terms of it, so the claim is corrected.

This order is forced, not arbitrary. Brightfield first because if registration off
the 16 fiducials does not survive a focus sweep and a Y-index across four plates,
nothing else matters. Fluorescence second and non-negotiable because it is the
*minimum* change that exercises the infinity port (insert a dichroic), the bus
(excitation power + auto-ID), and the software (a new acquire mode) — if the port
standard is wrong, fluorescence exposes it for ~$150 instead of after a Raman
build. A second fluorescence head before Raman because **modularity is unproven
until N=2**: that is the first time interchangeability *itself* is demonstrated.
Raman before NV because Raman is the first head that breaks "it's a camera on the
end" and validates the offboard fiber back-end. NV last because it abandons the
optical train's purpose entirely.

**The static bench de-risks every module.** A fixed off-gantry bench with
identical infinity-port geometry, objective, and dock face, on a breadboard with
one well or a calibration slide, validates each head's *physics* with motion
removed from the loop. Only a head that produces correct signal there earns a live
dock. This decouples "is the physics right" from "is the motion right" — the most
expensive coupling for a solo builder to debug — and it is the artifact handed to
a partner so they validate *their* physics without the motion stack.

### Solo → platform: the frozen published spec is the team you don't have

A solo founder cannot build five modalities serially in any reasonable time. The
only way one person becomes a platform is to make modalities into *independent,
parallelizable, delegable* tracks, and the thing that makes them independent is a
**frozen, published interface.** You personally build the stage, dock, bus,
registration loop, software abstraction, and the **first two heads** — you cannot
publish an interface you have never built against, and N=2 is the minimum that
reveals the true axis of variation and the maximum a solo founder should
generalize from. Then **freeze v1 additive-only** and parallelize: contract out
fabrication, PCBs, filters; **partner** Raman (a spectroscopist) and NV (a quantum
group), each building against the spec plus a static-bench unit, touching the
dock/port/bus but never the stage, shipping back a docking module. Documentation
plus the bench *are* the org; semver is how you do not break partners — a head
built against v1 docks forever, exactly as `power_section.md` froze its umbilical
pinout as a contract future row modules design against.

### Platform strategy

- **The wedge = automated below-deck live-cell fluorescence (+ brightfield/QPI)
  on the OT-2.** Not brightfield (commoditized), not Raman (small market, long
  sell), not NV (no buyer). Fluorescence is the largest "I'll pay today" market in
  cell biology, and it is the *same work* as the modularity proof (steps 1-3), so
  you never choose between de-risking the platform and shipping the product.
- **The desperate first customer:** a lab or small biotech running high-content
  **live-cell** assays on an OT-2 with no on-deck imaging — today they pull plates
  and walk them to an $80-250k imager, breaking the automated, incubated,
  liquid-handled context. They are desperate for registered, protocol-triggered
  fluorescence *that lives on the deck so cells never leave the workflow.*
- **Razor-and-blades:** razor = the stage (dock, registration, OT-2 integration —
  the install base); blades = certified heads + calibration + analysis software.
  You do not own the CellVis plate, so recurring revenue is heads + cal + software,
  and every later head is a low-friction upsell to a customer who already trusts
  the stage.
- **Open the dock, close the back-end.** *Publish* the mechanical dock, the
  infinity port (cage/RMS/C-mount are already open standards), the HEAD-BUS
  pinout, the manifest schema, and the `ModuleDriver` API — openness grows the
  catalog and makes your dock the standard. *Hold* the registration IP, the
  lease/arbitration daemon, the motion stack, and the cal-vault/safety-class
  certification — so only validated heads can drive lasers on your stage. Open
  enough to grow the catalog, closed enough that the stage and the best blades are
  yours.

### The top 3 moves now

1. **Print the dock and measure dock-undock-redock repeatability — ~¥50 and an
   afternoon.** 3 balls + cone/vee/flat + 3 magnets + dowel on the existing bench
   cradle; image the USAF target across 20 cycles. **Gate: ≤ 5 µm lateral, focus
   ≤ DOF.** This single experiment proves or kills the entire platform thesis. It
   is the SMIS equivalent of the WS2812 matrix — the highest-leverage purchase on
   the list, and it converts the dock's central reserved-and-unproven claim into
   physical Gate-6 evidence.
2. **Buy the ~$20 LED matrix and ship QPI/FPM as Module #0+#1.** Free
   physics-per-dollar; turns Aevum from "another well-plate camera" into a
   *measurement* platform (dry mass) and de-risks the compute/registration spine
   with zero new optics.
3. **Build the one fluorescence head and land one desperate live-cell OT-2
   customer** (revenue or signed LOI) before any third head. This is
   simultaneously the wedge product, the infinity-port test, and the auto-ID test.
   Freeze SMIS v1 from what these two head families actually needed — then, and
   only then, hand the frozen spec + a bench unit to a Raman partner.

### The trap

**Generalizing the interface against five imagined modalities instead of two paid
heads.** The solo-founder death is spending 18 months perfecting a
dock/bus/abstraction elegant enough to host Raman and NV — designing the bus for
the laser you have not built — and running out of money with a beautiful spec and
zero install base. The discipline: design the interface only as wide as two paid
heads (brightfield + fluorescence) demand, make it additive-only so Raman and NV
*extend* it later without breaking it, and let desperate customers — not the
catalog — pull the platform into being. **The interface is the moat, but the wedge
is the company.**

## What SMIS does not prove (scope lock)

Like the observer bench's "what Stage 0 does not prove," SMIS is explicit about
its own limits:

- **It is a contract, not a build.** Zero SMIS parts are installed. Every
  dimension, pinout, and ABI signature is a specification to design against, and
  every motion/imaging claim it implies is Gate-6 blocked until a physical dock is
  printed and a head is docked. The ≤ 5 µm repeatability number is a *target*, not
  a measurement (Top 3 move #1 exists to retire it).
- **It rides on the observer bench, not the other way around.** SMIS assumes the
  bench has already answered focus, contrast, the illumination fork, and the 62 mm
  Z-closure for *one* head. Those answers (and their caliper-measured `front_end_*`
  and `observer_sweep_extra_x/y` values) are inputs to the SMIS envelope; SMIS
  does not re-derive them.
- **It does not resolve the carriage-traversal gap.** Whether a 62 mm head
  traverses the full 334.5 mm row between the deck feet inside 80 mm is the
  observer bench's Stage-3 motion problem, unchanged by SMIS. SMIS only guarantees
  that *any* head it hosts respects the same envelope the gantry must carry.
- **The NA ladder is derived, the thermal wall is modelled, and the difference
  matters.** The collection fractions, Maréchal caps, Abbe limits, DOF values,
  pupil diameters, and sampling figures added 2026-09-23 are closed-form
  derivations from stated geometry — they are as good as their inputs and can be
  re-checked on paper. **The thermal table is not in that class.** It uses an
  **estimated** objective-to-ambient conductance of 50 mW/K; the *ordering* of the
  four heads is robust, the absolute ΔT is not, and the entire NA ≤ 0.60 ceiling
  rests on it. Treat "NA 0.60 passes a 0.3 K budget" as a design rule awaiting its
  measurement, not as a result. It is the highest-value early optical measurement
  on the list and it is not on the Top 3 above, because the Top 3 is about the
  dock.
- **The corrected corridor and standoff are not yet in the contract.** § *FROZEN
  vs FREE* still carries 15.56 mm and WD ≥ 19.90 mm, because changing them is a
  SMIS-major bump plus a code change (`src/aevum_smis/manifest.py:68`
`scan_corridor_footprint_max_mm`, mirrored at `cad/one_row_coupon.params.json`) that
  this pass did not make. **Until that happens the frozen table and the catalog
  disagree on purpose, and the frozen table is what the validator enforces.** A
  head sourced against 51.56 mm / WD 7.90 mm today will be rejected at dock by
  code that is still correct about the old question.
- **The catalog's frontier rows are reserved, not promised.** Raman, NV, SPAD,
  ECIS — and the appended Level-3 luminescence row #13 — are documented so the
  platform is designed not to *preclude* them, not asserted as deliverable on the
  current geometry. #13 is cheap and physically favorable, which is exactly why
  it needs saying: cheap is not the same as scheduled, and nothing about it has
  been built or measured. The bounded-claims section is
  load-bearing: NV is an mK reference, not intracellular and not magnetometry;
  Raman is sparse spot-checks wanting its own head; SPAD is sourcing-blocked.
- **Row #14 and the intervention ledger are candidates, and "recorded" is not
  "decided".** Patterned photostimulation would make SMIS host an **actuator**,
  which the FROZEN contract has no safety-class, dose-logging, or interlock story
  for; the photodose/thermal-dose ledger and `fields_per_well` belong to
  `evidence_model.md`, not to this document. They are written down so the contract
  is designed not to preclude them and so they are not rediscovered a third time.
  Neither has been scoped, costed, sourced, or agreed by the owner of the file it
  would change.

## Cross-references

- Stage 0 optical bench, envelope, optical train, infinity-space thesis,
  Z-closure asserts: `observer_optical_bench.md`
- The moving 3-axis stage SMIS heads dock to — kinematics, scan cycle, mass/Z
  envelope, the OT-2 lease, and the kinematic mount this dock extends:
  `observation_module.md`
- Dry bay, deck interface, well grid, fiducials, observer-reserved CAD params:
  `one_row_coupon.md` and `cad/one_row_coupon.params.json`
- GX16 frozen umbilical pinout, rail levels, single-point-earth ground plan,
  no-second-earth-bond rule, counterfeit-authentication discipline:
  `power_section.md`
- Custom-PCB COTS-authority-exception pattern, I2C addressing, TCA9548A, genuine
  Sensirion discipline: `sensor_pcb.md`
- World frame, pose-digest and schema-versioning precedent ("rot90 is a schema and
  gate migration"): `coordinate_system.md`
- Single-writer motion lease, evidence→claim→gate, fail-closed rules the software
  layer plugs into: `agent_ot2_bridge.md`
- The immutable Evidence packet the `acquire()` ABI returns into:
  `evidence_model.md`
- Plate-as-consumable / no-contact rule and the COTS-authority-exception framing:
  `materials_strategy.md`
- Low-turbulence headspace and per-plate sampling rationale: `architecture.md`
- Decision history: `decision_log.md`
