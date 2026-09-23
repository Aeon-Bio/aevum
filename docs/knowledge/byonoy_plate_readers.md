# Byonoy Plate Readers (Adjacent Prior Art)

## Purpose

Byonoy ships the closest commercial object to a piece of Aevum: a solid-state,
96-channel, no-moving-parts plate reader that lives *on the deck* of a liquid
handler and is sold as an Opentrons module. This page records what that product
actually is, which of our open forks it touches, and — the load-bearing part —
which of our claims it **narrows**, because an adjacent product that already
works is the cheapest possible falsifier of a platform thesis.

It is written to the same honesty discipline as the rest of the knowledge base:
it is **external prior art, not evidence**. No Byonoy hardware is in hand, every
number below is a vendor-published or vendor-documented specification retrieved
2026-09-20, and every comparison to our envelope is spec-against-spec. Nothing
here is Gate-6 evidence and nothing here retires an Aevum gate.

## Stance

Byonoy is **not** a COTS-authority exception in the family of `power_section.md`
and `sensor_pcb.md`: no Byonoy part is proposed for the row module or the dry
bay. It enters this knowledge base in the role `hardware_systems_lessons.md`
reserves for adjacent instrument families — a built machine whose architecture
tells us which of our design choices are forced and which are ours.

The one-sentence read: **Byonoy proves that when a measurement does not need an
objective, the correct architecture is a static parallel detector array, not a
scanning head — and that is precisely why Aevum's moving observer must justify
itself on the modalities that *do* need an objective.**

## What the product is

| | Absorbance 96 | Absorbance 96 Automate | Luminescence 96 |
|---|---|---|---|
| Footprint (W × L × H) | 9.6 × 15.4 × 5.5 cm | 9.6 × 15.5 × 5.7 cm | ~9.8 × 14 cm |
| Mass | 900 g | 435 g upper + 355 g lower | 900 g |
| Source | up to 4 LEDs | up to 6 LEDs, 400–1000 nm | — (emission assay) |
| Detector | 96 photodiodes | 96 photodiodes | 96 silicon photomultipliers |
| Read time | down to 3 s | down to 5 s | down to 3 s |
| Range | 0.0–4.0 OD | 0.0–4.0 OD | 8 decades, 100 fmol ATP/well |
| Power / link | USB 5 V, 2.5 W | USB-C, SiLA2 + vendor driver | USB 5 V, 2.5 W |
| Moving parts | none | none | shutter only |

The Opentrons Flex Absorbance Plate Reader Module GEN1 is this reader in
Opentrons packaging: 96 separate detection units, 450/562/600/650 nm, 0–4.0 OD
at 0.001 resolution, endpoint and kinetic, sold through the Opentrons automation
marketplace under the Byonoy partnership.

Three mechanism facts matter more than the spec table:

1. **One source and one detector per well, fired in parallel.** There is no
   monochromator, no filter wheel, no stage, no scan. A whole plate is one
   simultaneous 96-channel measurement, which is where "3 seconds" and "no
   routine maintenance" both come from.
2. **The Automate is a two-part machine the gripper operates.** The lower part is
   the detection chamber that occupies one SBS position; the upper hull carries
   the LEDs and is lifted off to a parking position by the same gripper that
   moves plates. The plate is read *between* the two halves — LEDs above,
   photodiodes below, sample in the middle. It is a transmission instrument, and
   the optical path is vertical and short.
3. **Opentrons documents the module as calibration-free**, requiring only the
   Flex gripper and deck slots A3–D3. Registration is *constructive*: the plate
   drops into a nest whose 96 channels are fixed relative to that nest, so there
   is nothing to calibrate.

## What it settles for us

### Parallel-by-construction is the correct architecture — for their measurement

A single-number-per-well absorbance reading needs no spatial resolution, so the
objective, the focus axis, the fiducial spine, the dock repeatability budget, and
the settle-time budget are all *pure cost* for that measurement. Byonoy deletes
them and gets 3 seconds and zero calibration. Our entire registration apparatus
(`coordinate_system.md`, the 16-fiducial world frame, the ≤ 5 µm dock target in
`sensor_module_interface.md`) is the price of motion, and motion is only worth
paying for when the measurement carries spatial information.

This is not an argument against the observer. It is an argument that the
observer's justification has to be *per-cell, spatially resolved, in-context
live-cell data* — QPI dry mass, fluorescence morphology, motility — and never
"we can also read a plate." The moment a roadmap item's deliverable is one number
per well, a static array beats us on every axis we care about.

### On-deck detection is a real product category, and the OT-2 is not served

The wedge in `sensor_module_interface.md` — "a lab running live-cell assays on an
OT-2 with no on-deck imaging, walking plates to an $80–250k imager" — gets
external support here, and also a sharpening. The Opentrons module is **Flex-only
and requires the Flex gripper**: Opentrons' own documentation names the gripper
as a requirement for moving both the labware and the reader's lid. The OT-2 has
no gripper. So on an OT-2 deck the standalone Absorbance 96 is a bench
instrument a human loads — the plate leaves its datum, leaves the headspace, and
leaves the incubated context, which is exactly the break the wedge names.

Consequence for how we phrase the moat: **"on-deck detection" is taken; "on-deck
detection on the OT-2 install base, registered, below-deck, without the plate
ever leaving the incubated context" is not.** Wording is a C-class call (see
C-SM2), but the claim "nobody puts detection on the deck" is now false and should
not appear in any pitch or doc.

### Absorbance is NA-insensitive, so our catalog row #3 survives — for a new reason

Catalog row #3 (multispectral/polarization) lists absorbance as a **free rider**
on the #1/#2 hardware, < $100, TRL 7-8. That verdict holds, but the recorded
rationale ("reuses #1/#2 hardware") undersells the real one: absorbance is a
**ratio** measurement, I/I₀, so the ~0.140 % collection penalty that
dominates the rest of the catalog largely cancels — the same argument the UCNP
row (#4) already makes for ratiometric thermometry. The NA-0.10 objective is not
a handicap for absorbance; it is a handicap for the *throughput* of absorbance,
which is a different complaint.

The honest framing of what we would ship is therefore **not** "a plate reader":
it is per-well spectrophotometry of an *imaged field*, serial, one well at a
time, on cells that are simultaneously being imaged and are still in their
incubated, registered, liquid-handled context. That is a different product from a
3-second plate read, and the docs should say so rather than implying we get plate
reading for free.

### The catalog was missing luminescence, and it is the one modality that *wants* no objective

Luminescence 96 (96 SiPMs, 100 fmol ATP/well, 8 decades) is the interesting
entry, because bioluminescent reporters — luciferase viability, reporter assays,
circadian and pathway readouts — are a first-class *live-cell kinetic* modality,
which is our stated territory, and the catalog in `sensor_module_interface.md`
had **no row for it**. It does now: row **#13, luminescence (SiPM, non-imaging)**,
added 2026-09-21 as the first real Level-3 candidate — reserved, not scheduled.

The physics is unusually favorable to the SMIS Level-3 (non-imaging) tier. A
luminescent sample emits without excitation; the limit is photons collected.
Through the 4× NA-0.10 objective we collect **~0.140 % of 4π**. A large-area SiPM sat
directly under the well with a light guide collects one to two orders of
magnitude more, and needs no objective, no focus, no registration finer than
"which well am I under". **Luminescence is the modality where deleting the
objective makes the measurement better, not worse** — the exact inverse of the
rest of the catalog, and therefore the cleanest possible test case for the
Level-3 tier the spec already reserves but has never exercised.


> **Corrected 2026-09-23 — collection fraction.** Both figures above previously read
> **~0.25 %**, computed from the small-angle *air-side* form `NA²/4`. The emitter is not in
> air: it sits in aqueous culture medium, so the collected solid-angle fraction is
> `η = (1 − cos(asin(NA / n_media))) / 2` with `n_media = 1.335`, which gives **0.140 %** at
> NA 0.10 — the old figure was **1.8× high**. Neither argument on this page weakens; both
> strengthen slightly. The absorbance ratio argument is unaffected (the penalty cancels in
> I/I₀ whatever its size), and the SiPM comparison gains, since the objective path it is
> being measured against collects less than was claimed.
>
> **But the "one to two orders of magnitude" gap above does not survive intact, for a second
> reason.** `sensor_module_interface.md` re-verdicted catalog row #13 on the same date: the
> comparison is no longer against the NA 0.10 path at all, because the geometry now admits
> **NA 0.60 at 5.334 %**, i.e. **38.0×** better collection. Against *that* path the SiPM's
> residual margin is `100 / 38.0` ≈ **2.6×** at the optimistic end of its own original claim
> and a **net loss** at the pessimistic (10×) end — and the imaging path keeps spatial
> information the SiPM structurally cannot produce. The row stays, on different grounds
> (one number per well with no focus requirement is the right shape for long kinetic runs,
> it is the only candidate exercising Level-3, and it needs no objective near the well to
> heat it). **Read the re-verdict, not the bound above:**
> `sensor_module_interface.md`, catalog row **#13, Luminescence (SiPM, non-imaging)**.
>
> Owner of the corrected collection form: `observer_optical_bench.md`, § *What NA actually
> buys*; the full ladder is tabulated in `sensor_module_interface.md`,
> § *(1) Collection fraction — the correct, media-side form*.


Byonoy's own design also tells us the two hard parts before we spend anything: a
**shutter** for background/dark-count control and a **phosphorescence-cancelling
filter** — i.e. plate-plastic afterglow and well-to-well optical crosstalk are
the real engineering, not the detector.

## What it does not settle — the dry-bay geometry conflict

A tempting bad idea is "put a 96-channel photodiode floor under each tile." The
frozen envelope forbids it, and the reason is worth recording so it is not
re-proposed:

- Byonoy's detectors sit **close-coupled** under the plate bottom, one collimated
  channel per well. Crosstalk rejection comes from that short, baffled standoff.
- Our contract mandates the opposite: the head's front face never crosses
  z = −8 (`carriage_top_clearance_z`), and the bay is a **swept traverse
  corridor** — 334.5 mm of clear Y travel inside 80 mm, with a Ø32 mm objective
  keepout. A static detector plane under a tile consumes the corridor and the
  aperture the moving head needs.
- A row is four plates / 384 wells, so parallel coverage is four units, not one.

So: **absorbance on Aevum is serial through the shared objective, by
construction.** A 384-well absorbance sweep at ~1 s/well is ~6 minutes; Byonoy
does a 96-well plate in 3. We lose that comparison and should stop making it. We
win a comparison Byonoy cannot enter at all: the same wells, read again every
twenty minutes for three days, without the plate ever moving, while a pipette
works the row and the headspace stays at setpoint.

If a parallel absorbance plane is ever genuinely wanted, the architecturally
honest home is a **tile-integrated static plane or a sibling consumable** (the
place `sensor_module_interface.md` already puts ECIS), never a head on the
gantry, and it must not intrude on the bay.

## The fork it actually touches: C-OB2 (illumination)

This is the concrete, actionable link. `observer_optical_bench.md` leaves the
illumination fork open, with a documented branch structure:

- oblique-from-below or epi passes the WS2812 contrast test → lid stays sealed
  and opaque (the cheap win);
- only transmitted-from-above passes → commit a **lid optical window** and re-cost
  the gas manifold.

Byonoy adds a coupling that fork does not currently name: **transmission
absorbance needs the same window as transmitted-from-above brightfield.** LEDs
above, sample between, detector below — there is no version of a transmission
absorbance measurement that survives an opaque lid. And the lid is not the only
obstruction: the row stack puts a **pre-slit silicone sealing mat** over the
wells, which is opaque, so a lid window alone is insufficient; the mat plane is
in the optical path too.

That makes the fork's two branches carry more than they appear to:

- **Sealed-opaque branch (cheap win):** we are also choosing to give up
  transmission absorbance and OD600-class readouts for the life of that lid
  design. Row #3's absorbance half quietly becomes epi/reflectance-only.
- **Window branch (expensive):** absorbance and OD600 arrive as riders on a
  window we already paid for — which materially improves that branch's return
  and should be part of the re-cost, alongside a per-well window/mat solution.

Neither branch is chosen here. The point is that C-OB2 is a **bigger decision
than the contrast test alone implies**, and the cheap branch has a cost nobody
had written down.

## The bridge / evidence relation

A reader of this class integrates as an **evidence source with no motion
authority** — it has no moving parts and no deck motion — which is the clean case
for `agent_ot2_bridge.md`: it would never take the motion lease, only return an
`Evidence` packet. Byonoy's open API and SiLA2 support make that mechanically
easy.

What makes it *not* a drop-in for us is the plate transfer. On the Flex the
gripper moves the plate and the reader's lid; on an OT-2 a human does, and a
human plate transfer breaks the target-class and unattended-autonomy rules
(`target_class_verification.md`, `readiness_contract.md`) and invalidates the
plate's registration — the plate leaves its datum and comes back to a pose
nothing has verified. Any future use of a COTS reader alongside Aevum must
therefore treat every transfer as a re-registration event, not as a read.

The inverse lesson is the useful one: **"does not require calibration" is an
architectural property, not a quality claim.** They earn it by never moving. We
cannot earn it, so our equivalent guarantee has to be the fiducial spine plus the
dock-repeatability gate — which is exactly why SM-B1.4 (print the dock, measure
≤ 5 µm over 20 cycles) is still the single highest-leverage unspent experiment in
the backlog.

## What this changes in the plan

**Nothing on the critical path.** The row-coupon gate chain, the 80 mm bay
budget, the frozen SMIS planes, and the near-term ordering (QPI → fluorescence)
are untouched. The SMIS trap section applies with full force: do not widen the
spec for an absorbance head nobody has bought.

Deltas, tagged with the `remaining_work.md` addressability scheme. The two
pointer-sized ones are **applied with this page**; the catalog row itself is left
to a normal do→review cycle rather than edited into a FROZEN-adjacent spec here:

- **A, applied** — the C-OB2 fork statement in `observer_optical_bench.md` now
  carries the absorbance/OD600 rider and the opaque-mat obstruction.
- **A, applied** — the catalog in `sensor_module_interface.md` now points here
  for the provenance of rows #3 and #13.
- **A, applied** — the catalog now carries row **#13, luminescence (SiPM,
  non-imaging)** as the first real Level-3 candidate, appended rather than
  rank-inserted so the document's existing #N references do not silently break;
  row #3's verdict is restated as ratiometric-survives-NA; and the bounded-claims
  section gains the luminescence limit (no spatial information, and three
  environmental failure modes — bay stray light, SiPM dark counts at the 37 °C
  setpoint, plate/mat afterglow). Reserved, not scheduled: it does not gate the
  wedge.
- **C** — wedge wording (C-SM2): stop claiming on-deck detection; claim
  registered below-deck live-cell imaging on the OT-2 install base.
- **C** — whether to buy a standalone reader as *benchmarking* gear (an
  independent OD ground truth for validating tile optics). Price is
  quote-only; this is a budget call, not an architecture call.
- **B** — nothing new. No Byonoy-derived measurement is proposed.

## What this page does not prove

- **No hardware, no measurement.** Every Byonoy number is vendor-published and
  retrieved on one date; no unit has been sourced, opened, or benchmarked. Treat
  all of it as claim, not evidence.
- **It does not resolve C-OB2.** It adds a cost to one branch. The WS2812
  contrast test still decides the fork.
- **It does not authorize a luminescence head.** It argues the catalog has a gap
  and that the gap is Level-3-shaped. Building it competes with the wedge and
  loses under the current ordering.
- **It makes no competitive forecast.** Byonoy ships absorbance and luminescence
  and no fluorescence product was found as of this writing; whether that changes
  is a market question this repo has no evidence about.

## Cross-references

- Modality catalog, the Level-1/2/3 tiers, the wedge, and the trap:
  `../engineering/sensor_module_interface.md`
- Illumination fork C-OB2, the NA/collection arithmetic, dry-bay envelope:
  `../engineering/observer_optical_bench.md`
- Traverse corridor, deck feet, objective keepout, fiducials:
  `../engineering/one_row_coupon.md`, `cad/one_row_coupon.params.json`
- Addressability tags (A/B/C) and the queue this page deliberately does not edit:
  `../engineering/remaining_work.md`
- Adjacent instrument families and authority separation:
  `hardware_systems_lessons.md`
- Plate-as-consumable / no-contact rule, COTS-authority-exception framing:
  `materials_strategy.md`
- Lease, evidence, and why a no-motion instrument is the easy integration case:
  `agent_ot2_bridge.md`, `evidence_model.md`
- Target-class and autonomy rules a manual plate transfer violates:
  `../protocols/target_class_verification.md`, `../engineering/readiness_contract.md`

## Sources (retrieved 2026-09-20)

- Byonoy, Absorbance 96 specifications: <https://byonoy.com/absorbance-96/specifications/>
- Byonoy, Absorbance 96 Automate: <https://byonoy.com/absorbance-automate/>
- Byonoy, Luminescence 96: <https://byonoy.com/luminescence-96/>
- Opentrons, Flex Absorbance Plate Reader module documentation:
  <https://docs.opentrons.com/flex/modules/absorbance-plate-reader/>
- Opentrons, Flex Absorbance Plate Reader Module GEN1 product page:
  <https://opentrons.com/products/opentrons-flex-absorbance-plate-reader-module-gen1>
- Opentrons, automation marketplace launch (Byonoy partnership):
  <https://opentrons.com/archives/news/opentrons-launches-automation-marketplace-to-expand-lab-robotics-accessibility-and-streamline-drug-discovery-and-microbiome-research>
