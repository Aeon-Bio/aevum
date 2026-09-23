# Observation Module (Moving In-Bay Scanner, Stages 1-4)

## Purpose

The observation module is the **moving** realization of the observer subsystem:
the 3-axis micro-scanner that lives as a drop-in cartridge in the 80 mm dry
observation bay, carries the optical head documented in
`observer_optical_bench.md`, and indexes it under the wells of the row module
to image cells from below through glass — **128 of those 384, not all 384**,
through today's tile apertures (see "Aperture-limited well reach" below). Where the optical bench is Stage 0 — one
static head at one well, proving focus and contrast — this page is the design of
**how the head moves, how it images on the move, what breaks it, and the
prototyping path** that converts the bay's reserved-air envelopes into an
installed, traversing machine. It is the continuation of the same staged build-out:
Stage 0 makes the head small enough and proves it can focus; Stages 1-4 make it
move, settle, and reach every well without leaving the bay.

This document does not repeat the bench's optical BOM or its three gating numbers
(focus/WD, contrast, field flatness) — those are owned by
`observer_optical_bench.md` and are inputs here. It owns the **motion stack, the
imaging cycle, illumination-on-the-move, the wet-boundary control loop, the
control/OT-2 coordination, and the Stage-1-through-4 build sequence.**

## Stance

The observation module is the same COTS-authority exception as the optical bench,
the power section (`power_section.md`), and the sensor PCB (`sensor_pcb.md`): it
deliberately brings commercial motion, imaging, and compute authority into the dry
bay at a defined boundary. The authority boundary is a **dedicated observer GX16
umbilical**, parallel in kind to the power section's GX16-4/GX16-6: bulk power,
motor phases, illumination, logic, and the safety interlock cross it as copper;
camera data crosses a separate shielded data bulkhead (see §5). On the bay side of
the umbilical, the print-native, plate-as-consumable, non-contact discipline holds
— nothing the module adds may touch the CellVis plate, intrude on the wet chamber
above the plate-support plane, or consume the deck-foot keepouts the row coupon
already validates.

**This is a production-prototype design, and motion and on-the-move imaging are
Gate-6-deferred until built.** Everything below the kinematic resolution in §2 is
*reserved-and-deferred* design intent backed by geometry and arithmetic, not
physical evidence. The one claim this document is allowed to flip from blocked to
satisfied *today* is the carriage-Y-traverse geometry (§2), and only as
**CAD/geometry evidence** — re-parameterizing a swept-volume check, not proving a
motion plan. Settle time, resonance, OT-2 coupling, condensation rejection,
focus-on-the-move, and traverse repeatability are all **unproven** until the
physical Stages 2-4 measure them. They are scoped here with the numbers that *would*
constitute Gate-6 evidence, framed as targets, not results. The honesty rule from
the bench holds verbatim: CAD geometry is not physical evidence, and an arithmetic
fit is not a settled axis.

**Amended 2026-09-23.** Three further claims are now backed by swept-solid
measurement against the same model, and are admitted on the same terms — geometry
evidence, nothing more: the free probe column above each tile aperture and the
resulting retract-to-cross-tiles motion model (§2), the usable working-distance
range once the focus stroke is run upward from the traverse plane (§2), and the
**128-of-384** optically reachable well count that replaces this document's former
"all 384 wells" claim (below). The same pass also retired a number that was never
evidence at all: the illumination obliquity in §4 was written as 53deg beside a
parenthetical computing 33.2deg. It is 33.2deg. Nothing in this document's motion,
settle, condensation, or interlock claims has moved from blocked to satisfied.

A second review round in the same pass retired four more figures that had gone stale
rather than wrong-at-birth, each superseded in place with the reason stated where the
number lived: the ground-truth table's "WD >= 19.90 mm floor" (it is the *parked*
standoff; 7.90 mm at full stroke — §2), the "±55 µm @ 4x" depth of field (55.0 µm
total — half-depth ±27.5 — per the bench's row "Depth of field, NA 0.10"), the
"5.6 x 4.2 mm" 4x field and the "~0.6 µm/px" sampling (6.67 x 4.46 mm and 2.16 µm/px
at M_eff 1.11x, per the bench's rows "Effective magnification", "Sampling at cell
plane" and "FOV at cell plane"), and the dead
`src/aevum_cad/row_coupon.py` citations left behind when that module became a
package. None of these changes a verdict; two of them narrow a margin, and both say
so where they sit.

**Citation convention, adopted 2026-09-23.** Every one of the line-number citations
written into this file during that pass had already gone stale by the end of it,
because `observer_optical_bench.md` was being revised concurrently and its line
numbers moved twice within the hour. Per `decision_log.md`, "Sites in that file are
therefore anchored here by heading and quoted text, which are stable, rather than by
line", citations into that file are now written as **section heading + the quoted row
or clause**, with the live line number given only as a parenthetical convenience. A
reader who finds the parenthetical stale should search the quoted text.

The frozen observer umbilical pinout is now machine-checkable in
`src/aevum_smis/observer_umbilical.py`: GX16-4 owns 24 V and 5 V, GX16-6 owns I2C,
3.3 V, alarm, and the active-low observer enable loop, and GigE is explicitly on
the M12 X-coded bulkhead. The same check reconciles this boundary against HEAD-BUS
so the swappable-head dock remains a superset of the offboard observer authority
boundary.

## Architecture in one paragraph

A **3-axis Cartesian micro-scanner** drops into the bay as a cartridge. A compact
optical head (4x infinity objective + 45deg fold + f50 tube lens + mono CMOS +
head-mounted oblique LED ring, all from the bench) traverses **Y** — the long
334.5 mm row axis — on a **flat low-profile truck**; scans **X** — the 99 mm plate
width — on a short on-truck stage; and focuses **Z** over a 12 mm stroke on a fast
fine actuator under the objective only. The gantry sub-frame is kinematically hung
from the **plate-support frame** (the frame carrying the 16 Ø2 mm fiducials and 32
focus targets), so registration is a rigid-body offset off the fiducials, not a
stack-up across the 80 mm standoffs. The heavy, hot bulk — stepper drivers,
orchestration host, PSU — lives **outside the bay** across the umbilical; only a
bare CSI sensor and a head Pi ride the truck, and the camera link crosses the wall
as **Gigabit Ethernet, never raw USB3 over the moving cable**. Illumination rides
the head (co-registered for free); the sealed wet chamber stays sealed and its
fogging is managed by a non-contact dry-gas snorkel closed-loop on the SHT41 and
MLX90614 telemetry the device already has.

## Verified bay geometry the module is designed against

Ground truth from `cad/one_row_coupon.params.json` (`observer_robotics`,
`dry_bay`, `deck_interface`, `well_grid`):

| Quantity | Value | Source / meaning |
|---|---|---|
| Usable optical Z envelope | **62 mm** (`carriage_height_z`), z = -8 to -70 | the head + its Z stack must fit here |
| Front-element ceiling | **z = -8 mm** (`carriage_top_clearance_z`) | top of any optical hardware at/below this |
| Objective keepout | **Ø32 mm** (`objective_keepout_diameter`) | barrel **and** head-mounted LED ring must fit inside |
| Focus stroke reserved | **12 mm** (`front_end_focus_stroke_z`) | the Z axis budget |
| Placeholder head footprint | **21 x 13 x 28 mm** (`front_end_*`) | to be replaced by Stage-0 caliper metrology |
| Carriage body (reserved box) | **100 x 58 x 62 mm** (`carriage_*`) | the source of the Y-overflow artifact — see §2 |
| Well-center span | **99.0 mm X x 334.5 mm Y** | the full scan the module must reach |
| Well pitch | **9.0 mm** X and Y | 12 cols x 8 rows/plate, 384 wells/row |
| Well A1 center (offset) | **x = 14.38, y = 11.24** (`first_well_center_*`) | **A1 is not at bay origin** — load-bearing for registration |
| Deck-foot inset / width | **8 mm X-inset, 7 mm Y** (`foot_inset_x`, `foot_width_y`) | feet at the X-perimeter; central **117.4 mm** clear (X 17.10..134.50). `lower_service_foot_inset_x` 3.0 walks one tile-4 foot inboard and sets the near wall |
| Service raceway | **8 mm Y x 24 mm Z**, R10 bend (`service_raceway_*`) | the only place flexing cable may live |
| Cell-plane standoff | **19.90 mm** parked / **7.90 mm** at full `focus_stroke_z` | 8.0 ceiling gap + 8.0 base + 2.0 support land + 1.73 open window + 0.17 coverslip; only 0.17 mm is glass. The **traverse-plane standoff, not a WD floor** — see §2, "the reserved 12 mm focus stroke is real headroom". |
| DOF (from bench) | **±27.5 µm @ 4x (55.0 µm total) / ±4.4 µm @ 10x (8.8 µm total)** | focus tolerance per magnification; λ/NA² at NA 0.10 and NA 0.25 (550/0.01 = 55.0 µm; 550/0.0625 = 8.8 µm; halves are exactly 27.5 and 4.4). Total-vs-half convention owned and reconciled by `observer_optical_bench.md`, § "Optical configuration", row "Depth of field, NA 0.10", which states the total and writes the half **rounded** to ±27 |
| Hold-still spec (from bench) | **±27 µm @ 4x / ±4 µm @ 10x** | the vibration acceptance threshold the motion design inherits — a deliberate round-**down** from the ±27.5 / ±4.4 half-depths above, not a second reading of them |

The cell plane sits 19.90 mm above the z = -8 head ceiling, so 19.90 mm is the
standoff the head sees **when parked at the traverse plane**. It is not a
working-distance floor: running the reserved `focus_stroke_z` = 12.0 upward puts the
nose at z = +4.00 and the working distance at **7.90 mm** (§2, "the reserved 12 mm
focus stroke is real headroom"; the parked/risen table in `observer_optical_bench.md`;
`sensor_module_interface.md`, "WD >= 19.90 mm is the *traverse-plane* standoff, not
the focus standoff"). The 4x objective's ~22 mm WD clears the **parked** standoff by
only 2.1 mm -- not "with margin", and measurement-gated until a real WD is
caliper-verified.

**Corrected 2026-09-23.** The table row and this paragraph previously read
"Sets a WD >= 19.90 mm floor" / "19.90 mm is the working-distance FLOOR for any
objective here". That was wrong and it contradicted §2 of this same document as well
as both sister documents; it was found by cross-reading the ground-truth table
against the risen-nose measurement. The parked/risen pair supersedes the floor
framing.

The hold-still spec is the bench's own number: **±27 µm, a deliberate round-down
from the 4x half-depth of ±27.5 µm** (half of a 55.0 µm total DOF), handed to the
motion designer as the acceptance threshold for every moving stage. The 10x figure
is the same round-down of ±4.4 µm. **Corrected 2026-09-23 (twice):** it was first
described as "half the 4x DOF", a rationale that rested on the retired "±55 µm"
half-range reading of the same quantity — `observer_optical_bench.md`, § "Optical
configuration", row "Depth of field, NA 0.10" states that the old
"±55 µm" double-counted. It was then described as "equal to the 4x half-depth",
which is arithmetically false: 55.0 / 2 = 27.5, not 27. The spec number itself does
not move — only the reason given for it. **±27 and ±4 remain the acceptance
thresholds** everywhere in this document; they are simply 0.5 µm and 0.4 µm tighter
than the DOF halves, which is the safe direction.

### Aperture-limited well reach — 128 of 384 (measured 2026-09-23)

Superseding the "all 384 wells" framing this document used in its Purpose and in the
§3 throughput table: **the head cannot see every well from below.** The tile
through-aperture is smaller than the well array it is supposed to expose.

| Quantity | Value | Source |
|---|---|---|
| Per-tile through-aperture | **88.0 x 52.0 mm** | `dry_bay.aperture_length_x` / `aperture_width_y` |
| Aperture a skirt-flange-only cradle would need | **105.21 x 69.21 mm** at `lower_well_diameter` 6.21, **105.80 x 69.80 mm** at `upper_well_diameter` 6.80 | `observer_optical_bench.md`, § "Reachable wells, and the 'nothing under any well' contradiction", bracket table under that heading, which owns the requirement and brackets it by ruling well diameter; the session's 105.4 x 69.4 sits inside that bracket |
| Deficit | **17.21-17.80 mm on both axes** | 105.21 - 88.0 = 17.21 and 105.80 - 88.0 = 17.80; identical on Y (69.21 - 52.0, 69.80 - 52.0) |
| Optical cone at the aperture plane, WD 19.90 | **9.27 mm** dia -> **4.64 mm** edge inset | measured 2026-09-23 |
| Optically reachable wells | **128 of 384** | 8 of 12 columns (span 63.0 mm) x 4 of 8 rows, per tile |

Three things follow, and they are the ones that matter to the motion plan:

1. **240 is the wrong number and so is 384.** A count of well *centres* inside the
   88 x 52 aperture gives 240, but a centre inside the aperture is not a well that
   can be imaged: the optical cone (long WD) or the physical nose (short WD) needs
   clearance too. Both ends of the working-distance range land on the same answer —
   at WD 19.90 the cone is 9.27 mm at the aperture plane (4.64 mm inset), and at a
   short WD a nose of OD 8-20 mm gives a 4-10 mm inset. **128 either way.**
2. **The fix is CAD, not optics.** Enlarging the tile aperture to ~110 x 74 mm gives
   384 of 384 *and* satisfies the skirt-flange-only cradle spec. That is a
   `cad/one_row_coupon.params.json` change and is **not** made in this pass; it is
   recorded as a recommendation against `dry_bay.aperture_length_x` /
   `aperture_width_y`.
3. **`covered_well_count` reports 384 and is wrong.** It counts the grid, not the
   reachable set. Recorded as a recommendation; not edited here.

Until the aperture changes, every per-row throughput and coverage number in this
document describes a **128-well** pass dressed up as a 384-well one. The cycle times
themselves are unaffected; the well count multiplying them is not.

## 2. How it moves — resolved kinematics

### Three axes, and why not two or four

| Axis | Carries | Stroke | Actuator | Transmission | Guide |
|---|---|---|---|---|---|
| **Y (row, long)** | X-stage + head; motor **parked at one end** | 334.5 mm | NEMA17 closed-loop | **steel-core GT2 belt** (a 335 mm leadscrew whips) | **stainless HGH15 / MGN12 rail** |
| **X (scan)** | head | ~110 mm | NEMA14 closed-loop | GT2-6 belt | MGN9 / MGN12 |
| **Z (focus)** | objective + fold parfocal block only | 12 mm | **voice-coil (VCM)** | direct / flexure | flexure or MGN9 |

**X must be a real mechanical scan, not optics.** At 4x the FOV is 6.67 x 4.46 mm
(corrected 2026-09-23; 7.41 x 4.95 mm IMX178 active area / M_eff 1.11 —
`observer_optical_bench.md`, § "Optical configuration", row "FOV at cell plane")
against a Ø6.21 mm well
on a 9 mm pitch. The
correction does **not** weaken this argument: 6.67 mm of field is still less than the
9 mm column pitch, so no single head sees two columns. Covering 12 columns optically
would need
12 parallel heads (absurd cost, unpackable in 100 mm) or a scan optic that destroys
the collimated infinity space the fold mirror lives in. So X is a mechanical axis on
the head. **Z is the only demanding axis** (10x DOF is ±4.4 µm, spec ±4); **no fourth axis
earns its keep** — plate tilt is swallowed by the 4x DOF, and per-well focus is the
Z axis with a precomputed map, not a separate mechanism.

**Decisive picks inside the stack:**
- **Z is a voice-coil, not a leadscrew.** Backlash is fatal to the ±4 µm 10x
  requirement and the autofocus inner loop wants sub-µm, no-backlash, fast settle.
  The leadscrew's one virtue (non-backdriving, holds focus at zero current) is real
  but solved by closed-loop hold on a VCM. At 4x a leadscrew would be fine;
  speccing the VCM now (~¥30-80, `音圈电机 VCM`) keeps 10x alive without a redesign.
- **Closed-loop steppers everywhere on X/Y** (`闭环步进电机 带编码器`, ~¥90),
  TMC2209 drivers (`TMC2209 步进驱动`). Lost steps under an opaque deck = lost
  registration with no recovery; non-negotiable.
- **Reject V-wheels** (10-20 µm compliance creeps straight into the focus loop) and
  **reject cross-roller** (overkill cost). Preloaded MGN/HGH is the right tier.

### The 44.6 mm carriage-Y-overflow is a CAD artifact, not a physical wall

This is the make-or-break, and it resolved in CAD before any hardware. **As the
section title says, this is history: the live check no longer produces an overflow
on either axis.** The *superseded* form of the swept-volume check
`_observer_carriage_traverse` (`src/aevum_cad/row_coupon/parts/observer.py:151`,
invoked from `src/aevum_cad/row_coupon/layout.py:914`) swept the **full 58 mm
`carriage_width_y`** along the 334.5 mm Y row:

```
334.5 (well span) + 58 (carriage_width_y) = 392.5 mm  vs  347.9 mm dry-bay Y envelope
-> 44.6 mm overflow (22.3 mm past each row end)
```

This is the source of the `carriage_traverse_exceeds_dry_bay` Gate-6 blocker
(raised at `src/aevum_cad/row_coupon/parts/observer.py:888`). The check is correct as
a conservative blocker, but the 58 mm is the body's cross-section **at one
Y-station** — it is not a width that must physically exist continuously along all
334.5 mm of travel. The choice of dimension is explicit in the code at
`parts/observer.py:213`, where the traverse-axis span is picked: it read
`carriage_width_y` before the fix and reads
`max(gantry_truck_traverse_extent, front_end_width_y)` after it. Picking the wrong
dimension there makes the scan axis report the overflow.

*(Path and line numbers corrected 2026-09-23: this section previously cited
`src/aevum_cad/row_coupon.py` with four-digit line numbers, which did not survive the
module becoming a package. Same correction as `observer_optical_bench.md` applied in
this pass.)*

**The fix: sweep the ~13 mm truck, not the 58 mm box.** Re-split the kinematics so
the *physically continuous* Y structure is thin. The Y mover is a flat transverse
truck thin on the traverse axis (~13 mm) carrying the X-stage and head; the 58 mm
carriage cross-section was an over-reservation. With only the thin truck traversing,
the swept Y collapses:

```
334.5 (well span) + 13 (truck width) = 347.5 mm  <  357.5 mm dry-bay Y
                                     -> fits with 10.0 mm margin
```

*(Margin corrected 2026-09-23. This read "< 347.9 mm -> fits with ~0.4 mm margin",
which was the bay-Y as it stood before `observer_sweep_extra_y` went 12.2 -> 17.0 on
2026-06-14. The live envelope is **357.5 mm** (`dry_bay_envelope.width_y`), so the
live `traverse_axis_fit_margin_mm` is **10.0**, not 0.4 -- the fit is comfortable, not
razor-thin. The 392.5 vs 347.9 = 44.6 mm figures above are the pre-resize fat-body
arithmetic and are kept as the record of what was wrong, not as live numbers.)*

This is implemented: `_observer_carriage_traverse` now sweeps a
`gantry_truck_traverse_extent` (13 mm) param on the traverse axis instead of
`carriage_width_y = 58`, which clears the `carriage_traverse_exceeds_dry_bay`
blocker. **This is geometric evidence only** — the topology *can* fit; whether a
~13 mm beam holds still and traverses 334.5 mm repeatably is Stage-3 physical work,
still Gate-6 blocked.

**But the Y fix relocated its burden onto the X scan axis — and a do→review cycle
caught it.** The head scans X across the 99 mm column span, so the scan-axis swept
extent is `99 + head-X-footprint`. The dry-bay X is 120.2 mm, so after the well
span only **~0.2 mm of X budget remains against the dry-bay wall — and against the
LEG corridor the budget is already negative.** Corrected 2026-09-21: the binding scan
wall is the standoff-leg corridor, not the bay. At the 21 mm placeholder footprint the
head strikes the near leg by **2.72 mm** (`scan_corridor_margin_mm = -2.72`,
`clears_traverse = False`); the bay per-wall margin of +0.02 mm is the LOOSER of the two.
So "both axes fit" no longer holds, and the camera-routing problem below — though real —
is no longer the binding constraint. The
earlier claim that the camera arm could be "routed along the ~120 mm beam X-length"
was geometrically wrong: the residual after the 99 mm well span is ~0.2 mm, not
120 mm. **The post-fold camera arm cannot ride along X.** It must be folded
coaxially over the objective (compact head) or the sensor taken offboard. The check
now carries an explicit `front_end_scan_axis_footprint` param (placeholder 21 mm =
bare objective, camera arm **excluded**) and surfaces `scan_axis_fit_margin_mm` ≈
0.2 plus a `scan_axis_footprint_excludes_camera_arm` flag; if a measured scan-axis
footprint exceeds the objective by more than ~0.2 mm, the X overflow re-blocks the
traverse. So the honest state is: both axes fit **only against the bare-objective
placeholder**; the camera-routing strategy (coaxial fold or offboard sensor) is the
new binding constraint, gated and Stage-0-measurement-dependent. If Stage-0 head
metrology is larger than 21/13 mm, the margins shrink or overflow — the squeeze to
watch on both axes.

**Superseded 2026-09-23.** The ~0.2 mm residual and the 2.72 mm corridor strike are
both computed against a **99 mm** scan over all 12 well columns. The 88 mm aperture
admits **8** columns, span **63.0 mm** (see "Aperture-limited well reach" above), so
against the set the head can actually image:

```
dry-bay X:  120.2 - 63.0 (reachable span) - 21 (placeholder head) = 36.2 mm residual
                                                        (~18.1 mm per wall, not 0.02)
leg corridor: min( 2 x (42.88 - 17.10), 2 x (134.50 - 105.88) )
            = min( 51.56, 57.24 ) = 51.56 mm budget
            vs a 21 mm head -> +15.28 mm per wall, not -2.72
```

So neither wall binds at the placeholder footprint, and **X no longer forces the
camera-routing decision.** Coaxial folding over the objective, or an offboard sensor,
may still be the right choice on mass, thermal, and cable grounds — but the sentence
"the post-fold camera arm cannot ride along X" rested entirely on the 99 mm span and
does not survive it. The original text above is left in place rather than rewritten,
because the `scan_axis_fit_margin_mm` ≈ 0.2 figure it describes is what the check
*currently computes*; the check is parameterised on the nominal 12-column grid. The
honest caveat travels with the gain: it is bought by conceding that a third of the
plate is unreachable, and enlarging the aperture to ~110 x 74 mm restores the 99 mm
span and takes this margin back with it (open decision #5). See
`decision_log.md`, "2026-09-23 — the 15.56 mm head budget is an artifact of scanning
wells the aperture never admitted", and `observer_optical_bench.md`, § "The 15.56 mm
corridor is an artifact of scanning wells the head cannot reach".

The **reject** here is the two-gantry split (two 167 mm beams, two heads). It is a
*different, more expensive* fix (~2x the ¥1,940 optical core) that buys throughput,
not envelope — the thin truck already solves the geometry. Keep the split **in
reserve** only as a stiffness escape if Stage-2 settle measurement shows a single
334.5 mm beam cannot hold ±27 µm even input-shaped (see §3).

### Settle forces stop-and-shoot

The genuine disagreement in the design synthesis was whether one thin 334.5 mm beam
can hold still. The physically-derived estimate governs: a ~200 g head on a cheap
belt gantry has a first structural-loop mode near f ≈ 60 Hz, Q ≈ 30. Ring-down from
a ~100 µm post-move sway after a 9 mm step:

```
t ~= (Q / pi*f) * ln(A0 / A)
  to +/-27 um (4x): ln(100/27) = 1.3  -> ~210 ms
  to +/-4  um (10x): ln(100/4) = 3.2  -> ~510 ms
```

Consequences, decisively:

1. **Stop-and-shoot is forced.** No continuous/on-the-fly scan — a 4x cell at
   ~2.16 µm/px (`observer_optical_bench.md`, § "Optical configuration", row
   "Sampling at cell plane")
   moving even 2 µm during a 10 ms
   exposure smears ~1 px (2 / 2.16). **Corrected 2026-09-23** — the retired
   "~0.6 µm/px → ~3 px" was the *nameplate* 4x sampling (2.4/4), not this train's
   M_eff 1.11x. The conclusion holds on the new number but **the margin is thinner
   and should not be read as overdetermined:** smear scales linearly with residual
   velocity, so the ~5x-worse settle contemplated in driver #3 puts it back at ~5 px,
   and a 10x drill-down (2.4/2.78 = 0.86 µm/px at M_eff 2.78x) smears ~2.3 px on the
   same 2 µm of motion.
2. **Move-settle-strobe** converts residual µm-motion into sub-µm blur: stop →
   settle → fire a short LED flash for the exposure (the head's addressable ring is
   strobe-capable at ~0.1 % duty). This is the highest-leverage motion trick — it
   relaxes a stiffness requirement into a timing requirement.
3. **Minimize Z moving mass:** only objective + fold ride the Z block; tube lens,
   camera, and Pi stay fixed on the truck. Z settle → tens of grams → fast.
4. A **¥20 ADXL345** on the head measures f and Q, feeds Klipper `input_shaper`
   (free, halves residual), and tells you whether the OT-2 couples (§5). This is the
   second-highest-leverage purchase after the LED matrix.

All of the above are **targets and arithmetic**; the real f, Q, and settle time are
Stage-2 physical evidence, not yet measured.

### Vertical motion model — retract to cross tiles, not to cross wells

Until this session the Z axis was described only as a 12 mm focus stroke and the
head was implicitly assumed to traverse at one plane. A swept-probe check against
the solid model measured the actual free column above the apertures:

- A probe cylinder of up to **Ø25 mm** rises unobstructed from **z = 0 to
  z = 11.71** at **every** tile-aperture centre. The column is clear to within
  **0.02 mm of the glass outer surface** (z = 11.73) — equivalently 0.19 mm below
  the cell plane (z = 11.90). *(Corrected 2026-09-23: 0.19 mm is the gap to the cell
  plane, not to the glass.)*
- **Between** tiles the `plate_support_frame` (z = 0 .. 11.20) blocks at
  **z = 0.05**. Crossing from one tile to the next requires a full retract below
  z = 0.

Two consequences, both of which change the scan cycle in §3:

1. **Retract cycles are per tile, not per well.** A row is 4 tiles, so one row pass
   costs **3 retract/raise cycles**, not 384. Inside a tile's aperture the nose
   stays raised for all of that tile's wells, so the ~0.20 s move + ~0.20 s settle
   budget for an intra-tile 9 mm step is unchanged. Only the 3 tile crossings pay
   the full down-across-up penalty.
2. **The reserved 12 mm focus stroke is real headroom, not a fixed working
   distance.** Run *upward* from the traverse plane
   (z = -8.00 = `carriage_top_clearance_z`), a full
   `front_end_focus_stroke_z = 12.0` stroke puts the nose at **z = +4.00**, i.e.
   **WD 7.90 mm** to the cell plane rather than the 19.90 mm the traverse plane
   imposes. The vertical budget 8 + 28 + 12 = 48 mm sits against
   `observer_sweep_depth_z = 80` with **32 mm of slack**. The long working distance
   is therefore a property of *where the head parks*, not a wall the bay imposes —
   which is what keeps the short-WD, higher-NA objectives in
   `sensor_module_interface.md` on the table at all.

Both are **CAD/geometry evidence** (a swept solid), not a proven motion plan. The
raise, the retract, and the settle after each are Stage-3 physical work and remain
Gate-6 blocked.

### Safety requirement — hardware Z-gate on XY motor enable

**Requirement: XY motor enable must be hardware-gated off whenever the nose is
above z = 0.**

With the nose raised into a tile aperture the head is inside the plate's footprint.
At the short-WD end of the objective ladder — a 40x/NA 0.60 ELWD-class head,
WD 2.8-3.6 mm — the front element sits only **2.6-3.4 mm below the glass**
(WD minus the 0.17 mm coverslip), under a **consumable** plate whose seating varies
plate to plate and which the no-contact rule forbids the module from ever touching.
A commanded-position check in firmware is not sufficient protection for that gap: a
lost step, a stale focus-map value, or a homing fault all produce an XY move with
the nose still up.

The gate must therefore be physical, in the same class as the §5 TMC2209 enable
interlock: a Z limit/position signal (one switch, or one comparator on the Z
encoder) that drops the X and Y driver enable lines whenever the nose is above
z = 0, independent of software state. The converse is already implied by the §5
"head parked + Z-retracted" limit the bridge requires before granting a pipetting
lease; this makes the same signal a precondition for the observer's *own* XY moves.
Cost is one part. The failure it prevents is a head dragged sideways into the
underside of a live plate — which destroys the experiment, not just the hardware.

### Mounting into the bay

A drop-in cartridge, kinematically (3-2-1: cone/groove/flat) mounted to the
**plate-support frame** — the same frame carrying the 16 Ø2 mm fiducials and 32
focus targets — so registration is a rigid-body offset, not a stack-up across the
80 mm standoffs, and re-registration after a head swap is a fiducial re-find, not a
recalibration. The structural loop that must hold ±27 µm (objective → fold →
Z-stage → X-beam → Y-truck → sub-frame → plate-support frame → plate) is kept short
and all-aluminum: **no PLA in the focus loop** (PLA CTE is ~3x aluminum →
~4 µm/°C drift, eating the whole 10x budget; aluminum's ~60 mm loop gives
~1.4 µm/°C). The observer GX16 umbilical is the only disconnect for service.

## 3. How it images

### Scan cycle — stop-and-shoot

| Step | Action | Time (4x) |
|---|---|---|
| Move | index to next well center (≤9 mm) | ~0.20 s |
| Settle | ring-down below ±27 µm | ~0.20 s |
| Autofocus | drive Z to focus-map value; verify with 3-frame ±40 µm bracket | 0.15-0.30 s |
| Strobe + expose | fire oblique LED quadrant; single mono frame | ~0.10 s |
| Readout | CSI → head Pi, overlapped with next move | (hidden) |
| **Per well** | | **~0.7-1.0 s** |
| *Tile crossing* | retract below z = 0, cross, raise (see §2) | *3x per row, not per well* |

The tile-crossing row is the motion model measured this session: the nose stays
raised for every well inside a tile's aperture and only retracts to cross between
tiles, so a 4-tile row pays the down-across-up penalty **3 times**, not 384. Its
duration is unmeasured — it is a Z stroke plus a settle, and both are Stage-1/2
evidence.

### Autofocus — precomputed focus map + per-well bracket

The plate is one rigid #1.5H glass sheet seated kinematically; its focus surface is
a tilted plane plus mild sag, fully described by `z_focus(x,y) = a*x + b*y + c`
(plus an optional quadratic sag term).

1. **Build the map once per plate seating** from ~9 points per plate (4 corners + 4
   edge-mids + center) using the 32 focus targets — a full contrast sweep (range
   ±400 µm, step ~20 µm) at each, least-squares fit. ~36 s for the 4-plate row,
   once. This is the bench's Phase-B "5 wells: corners + center" calibration
   promoted into runtime.
2. **Per well: predictive jump + narrow verify.** Drive Z to the map value, then a
   3-frame Brenner/Tenengrad bracket at **±40 µm** (wider than the ±27.5 µm 4x
   half-depth, so the outer two frames straddle the 55.0 µm DOF rather than sitting
   inside it — which is what makes the peak findable) picks
   the sharpest. The bracket catches local sag and debris without a full sweep.

At 4x, a 55.0 µm total DOF (±27.5 µm) makes the map alone nearly sufficient; the
bracket is cheap
insurance. **Reject** pure per-well contrast sweep (doubles scan time, noisy on a
low-contrast target) and **reject** a laser/reflective focus sensor (the 0.17 mm
coverslip presents two reflecting surfaces 0.17 mm apart → wrong-surface lock, and
it competes for the objective keepout — not worth it at 4x). The **10x drill-down**
(±4.4 µm DOF, step ≤2 µm, full sweep) is a sparse per-well escalation on QC-flagged
wells only — the one place the VCM's precision earns its keep.

### Focus — DOF by NA, structural drift, and what actually forces a refocus

Everything above is argued at 4x / NA 0.10, where a 55.0 µm total (±27.5 µm) depth of
field makes a
precomputed map nearly sufficient. Depth of field falls as **1/NA²**, and the
objective ladder opened up by `sensor_module_interface.md` moves fast:

| NA | DOF = λ/NA² @ 550 nm, dry | Lateral resolution λ/2NA @ 550 nm |
|---|---|---|
| **0.10** (today's 4x) | **55.0 µm** | 2750 nm |
| **0.363** (Maréchal cap through an uncorrected 0.17 mm coverslip) | **4.17 µm** | 758 nm |
| **0.45** (20x ELWD, correction collar) | **2.72 µm** | 611 nm |
| **0.60** (40x ELWD, correction collar) | **1.53 µm** | 458 nm |

(The 55.0 µm at NA 0.10 is the same physical quantity this document's ground-truth
table now writes as "±27.5 µm @ 4x (55.0 µm total)". The convention is settled, not
open: `observer_optical_bench.md`, § "Optical configuration", row "Depth of
field, NA 0.10",
ruled on it in this same pass — 55.0 µm is the full depth, ±27.5 µm the half-range
(the bench writes it rounded to ±27), and the former "±55 µm" double-counted. This
document's earlier deferral of the reconciliation "to the owner" is retired; the
owner has answered.)

**Structural drift over the 80 mm standoff legs**, per 1 K excursion. CTE values
are material-class typicals (estimates); the product is exact arithmetic on them:

| Leg material | CTE (ppm/K, typical — estimate) | Drift over 80 mm |
|---|---|---|
| ABS | 90 | **7.20 µm/K** |
| PLA | 70 | **5.60 µm/K** |
| PETG | 60 | **4.80 µm/K** |
| Aluminium | 23 | **1.84 µm/K** |
| Steel | 12 | **0.96 µm/K** |
| Invar | 1.2 | **0.10 µm/K** |

Read naively this says "make the legs metal": at NA 0.60 the 1.53 µm DOF is spent
by a **0.27 K** excursion on PLA legs (1.53 / 5.60). But aluminium only buys 0.83 K
(1.53 / 1.84) and even invar buys 15 K — and none of it addresses the thing that
actually moves between one well and the next.

**The finding: plate-to-plate topography and seating — not temporal drift — is what
forces a refocus.** The coverslip's own figure and the kinematic seating of the
plate are hundreds-of-µm class; §5 already budgets **±50-100 µm** of seating
variation per plate load, and the plate is a *consumable* whose glass flatness we
neither specify nor control. Against a 1.53 µm DOF, that is two orders of magnitude
of unmodelled surface. **At NA ≥ 0.45 you must refocus at every well visit
regardless of how stable the structure is.**

The consequence is architectural, not material:

- The per-well bracket described above stops being "cheap insurance" layered on a
  focus map and becomes the **primary** mechanism; the plane fit `z_focus(x,y)`
  degrades from an answer to a **seed** for the search.
- The all-aluminium focus loop (§2, driver #7) is still right, but it is now a
  second-order argument. It buys slow-drift immunity, not per-well correctness.
- **Recommended architecture (not built): through-objective dual-surface IR
  autofocus** on the two coverslip surfaces, built **first as an open-loop drift
  gauge** — log the measured focus offset for every well of a full row, for several
  plate seatings, *before* any loop is closed. That order is deliberate: an
  open-loop gauge is evidence about the real plate; a closed loop is a mechanism
  that hides it.
- This **re-verdicts, and does not delete,** the reject of "a laser/reflective focus
  sensor" above. That reject was argued at 4x/NA 0.10 and its premise — the map
  alone nearly suffices — holds there. Its stated failure mode (two reflecting
  surfaces 0.17 mm apart → wrong-surface lock) is precisely the *signal* a
  dual-surface scheme uses rather than the fault it avoids. **The reject stands at
  4x. It does not survive the move to NA ≥ 0.45.**

None of this is measured. The DOF and CTE arithmetic is arithmetic; the claim that
topography dominates drift is an inference from the ±50-100 µm seating budget and
the consumable-plate constraint, and the open-loop gauge above is exactly the
experiment that would falsify it.

### FOV / tiling

At 4x, FOV is **6.67 x 4.46 mm vs Ø6.21 mm well** (corrected 2026-09-23;
7.41 x 4.95 mm active / M_eff 1.11 — `observer_optical_bench.md`, § "Optical
configuration", row "FOV at cell plane"). **The lost
axis is Y, not X.** One centred frame covers the full Ø6.21 mm well in X with
0.23 mm to spare each side, and clips it in Y: 4.46 mm of field against 6.21 mm of
well leaves a ~0.88 mm crescent off each Y edge. Those crescents are the
meniscus-distorted rim, so a single frame remains the right default read for
confluence and morphology — but per that same row ("the full 6.21 mm well fits in one
frame in X and needs 2 tiles in Y") the **full well
needs 2 tiles in Y**, and this document no longer claims one frame covers the well.
The superseded 5.6 x 4.2 mm figure put the crescent on the left/right edges, which
inverted the axis. No z-stack at 4x (the 55.0 µm DOF swallows field tilt). Escalate
to a **2-tile Y pair** for whole-well coverage, or to the **2x2 mosaic** costed in
the throughput table (~4 frames, phase-correlation stitch on the host) when X margin
is wanted as well — both on QC failure only.

### Throughput for 384 wells

| Mode | Per-well | 384-well row |
|---|---|---|
| **Default: 4x, 1 frame, map-AF + bracket** | ~0.9 s | **~6-10 min** |
| 4x, full contrast-AF every well | ~2.5 s | ~16 min |
| 4x, 2x2 mosaic | ~3.0 s | ~19 min |
| Two-gantry split (reserve) | — | halve the above |

**Well-count caveat:** every "384-well row" figure in the table above multiplies a
per-well cycle time by the *grid*, not by the reachable set. Against the 128
optically reachable wells measured this session (see "Aperture-limited well reach"),
the same cycle times give **~2-3.5 min** for a default pass — a smaller number that
describes **one third of the plate**. The table is left as written because the
cycle times are what it is really about; the multiplier is wrong until the tile
aperture is enlarged.

The honest production number is **~6-10 min single-head** — comfortably inside any
live-cell time-lapse cadence (15 min-1 hr). **Throughput is not the binding
constraint; focus reliability and label-free contrast are.** Phototoxicity is
near-zero (oblique label-free, ~0.1 % LED duty, no fluorescence excitation) — the
genuine advantage of this architecture. All cycle times above are estimates pending
Stage-2 settle measurement.

**This verdict is scoped to the 4x, one-frame-per-well default.** It does not survive
the move to NA ≥ 0.45. Exhaustive tiling at NA 0.60 runs **~82-101 tiles per well**
(the band is the two tube-lens conventions: M_eff 10.0x at Nikon f_ref 200, 11.11x at
Olympus f_ref 180), which over the **128** optically reachable wells is ~10,500-12,900
tiles, **~1.2-1.4 h** at 0.4 s/tile and **~133-164 GB** per pass at 12.7 MB/frame —
see `observer_optical_bench.md`, § "What NA actually buys", the "Tiling: the
throughput term nobody has costed" paragraph, and `sensor_module_interface.md`,
§ "The intervention ledger (CANDIDATE — recorded, not decided)", the paragraph
"A second candidate from the same session: `fields_per_well` as an explicit
Evidence sampling parameter". Both conclude the same way: neither the time nor the storage fits an
hourly cadence. **At any high-NA head throughput becomes binding**, and the
resolution is not a faster stage — it is making **"N random fields per well"** a
declared, logged Evidence sampling parameter. Enlarging the tile aperture makes this
worse, not better, because it triples the well count.

### Carried optics

Unchanged from the bench (`observer_optical_bench.md`): 4x infinity plan-achromat
RMS objective (NA 0.10, WD ~22 mm, 0.17-corrected) → 45deg first-surface fold →
f50 achromatic doublet → mono CMOS, 10x as the parfocal drill-down swap. Route the
horizontal post-fold axis **along X**, which keeps the heavy camera off the Y-truck
and only the ~60 mm objective + fold column in the 62 mm Z envelope.
*(Flagged 2026-09-23: this "route along X" instruction contradicts the X-residual
finding in §2, which concluded "the post-fold camera arm cannot ride along X". Both
are now in question — see the supersession note in §2, since the 63.0 mm reachable
span leaves ~36 mm of dry-bay X, not ~0.2 mm. Camera routing is an **open decision**,
not a settled instruction, and neither sentence should be built against until a
Stage-0 head footprint is measured.)* Keep ~25-40 mm
of collimated infinity space reserved for a future dichroic — build nothing, block
nothing; that is the reserved Raman/fluorescence budget.

## 4. Illumination on the move + condensation

### Illumination rides the head

A **small-pitch addressable LED ring** (WS2812B-2020 / SK6812, ~16-24 px, **Ø26 OD
inside the Ø32 keepout** — the load-bearing fit number) bonded to the front-end body
at **r ≈ 13 mm**, firing one to two azimuthal quadrants at **33.2deg from vertical**
(geometry: `atan(13 / 19.90) = 33.2deg`) for oblique phase-gradient / pseudo-DIC
contrast that makes unstained cells countable (target Michelson C ≥ 0.15). Mounting
the source on the head makes illumination **co-registered for free** and per-well
uniformity **constant by construction** — a fixed bay-floor array would force an
emitter-to-well calibration per well across the row, a second alignment problem on
top of motion. The emitters sit at the z = -8 plane and point inward and up, so they
clear the Ø≤25 mm barrel (firing outside it onto the well) and never threaten the
plate. Firmware hardwires the bench-winning azimuthal pattern and keeps **2-axis
DPC** (opposed quadrants, 2-4 frames/well, budgeted into dwell) and **darkfield**
(full ring) available from the same part. This is the moving-system realization of
the bench's WS2812 illumination fork — the bench proves which mode passes through
the media column; the head hardwires the winner.

**Corrected 2026-09-23: the obliquity is 33.2deg, not 53deg.** This paragraph
previously read "~53deg from vertical" immediately beside a parenthetical that
computed 33.2deg from the same geometry, and the 53 was the number the stray-light
and Stage-0 statements downstream inherited. The geometry governs: an emitter at
**r = 13 mm** on the z = -8 plane, firing at a cell plane **19.90 mm** above it,
subtends `atan(13 / 19.90)` = **33.2deg**. The ray budget closes end to end —
19.73 mm of air at `tan(33.2) = 0.654` walks 12.90 mm laterally, and the 0.17 mm
coverslip (refracting to `asin(sin 33.2 / 1.5185)` = 21.1deg inside the glass) adds
0.07 mm, for 12.96 mm ≈ the 13 mm ring radius. No geometry in this design produces
53deg. 33.2deg supersedes it everywhere below and in §7.

**Inter-well stray light → a matte-black single-well snorkel** (carbon-PETG, OD
≤Ø31 inside the keepout, top aperture Ø6.5-7 mm framing exactly one well, lip
~1.5 mm off the plate, **never touching** — the no-contact consumable rule). At
9 mm pitch the gap between Ø6.21 mm well bottoms is only ~2.79 mm, so oblique light
splashes into neighbors without containment. **The 33.2deg correction shrinks this
splash but does not retire it:** the beam walks `tan(33.2) = 0.654` mm laterally per
mm of rise, so across the 1.73 mm open window between the support land and the
coverslip it moves **1.13 mm** against that 2.79 mm gap. The superseded 53deg figure
implied `tan(53) = 1.327` mm/mm — **2.30 mm** over the same window, which would have
walked the beam essentially into the neighbouring well. The snorkel is still
required; it simply has roughly **2x** the containment margin the 53deg number
credited it with. The snorkel does triple duty: optical isolation, camera baffle,
and purge plenum (below). The lip-to-plate gap is
the leak path for both light and gas and is the hard no-contact tradeoff number —
**measured at Stage-0 Phase C/D, not guessed**, then fed back into the
`front_end_*` swept-body params.

### High-NA illumination is an open question — the r = 13 mm ring is shadowed at a short-WD nose plane

The 33.2deg geometry is a consequence of the **long** 19.90 mm standoff. It does
not survive raising the head into a tile aperture. If the nose is driven up to a
40x-class working distance (WD 2.8-3.6 mm, front element 2.6-3.4 mm below the
glass), the same r = 13 mm ring would have to fire at
`atan(13 / 3.0)` = **77.0deg** from vertical — a ray nearly parallel to the
coverslip. Two things break at that angle:

- **Occlusion.** The ring sits at r = 13 mm, barely outside a Ø25 mm barrel
  (r = 12.5 mm). A 77deg ray runs 13 mm laterally while rising only 3 mm, so any
  flare of the objective nose stands in the beam. The emitter is firing into its
  own barrel shoulder for most of its azimuth.
- **Fresnel loss at the glass.** At 77deg incidence into n = 1.5185 the unpolarized
  reflectance is **~30 %** (Rs = 0.457, Rp = 0.147), against **4.5 %** at the
  33.2deg long-WD geometry and 4.2 % at normal incidence. Most of what is not
  occluded never enters the glass.

So the head-mounted oblique ring is a **long-WD solution**, and this document should
not be read as having solved illumination for the higher-NA heads that the short-WD
motion model above makes geometrically possible. **No replacement is specified.**
The candidates — none evaluated, none costed — are a through-objective epi path
(which would spend the 25-40 mm of collimated infinity space §3 reserves for a
dichroic), a ring relocated off the head onto the tile-aperture rim (fixed, so it
reintroduces the per-well uniformity calibration the head-mounted ring exists to
avoid), or accepting brightfield-only at high NA. Recorded as open decision #4 in
§8.

### Condensation — the genuinely hard interface, non-contact and closed-loop

Imaging up from a cooler dry bay into a 37°C / ~95 %RH chamber fogs the
plate-window underside when the bay dew point exceeds the glass temperature. The
underside is squarely in the optical path; fog = scatter = contrast and focus death.
The two levers are lowering the dry-bay dew point and raising the window-underside
temperature; use both, **locally**, and **without touching the plate**.

**Strategy: local dry-gas purge up the snorkel + an optional warmed snorkel lip,
closed-loop on telemetry that already exists.** Feed dry gas (RH < 20 %,
`4mm 特氟龙管` + sintered laminarizer, a few hundred mL/min laminar — not a jet,
which would chill the glass and add vibration) up the snorkel to sweep only the
imaged well's underside. Layer in a low-power resistive lip heater (PTC or nichrome,
or routed LED waste heat) to nudge the local underside a few °C warm if purge alone
is marginal. **Reject whole-bay 37°C matching** — it cooks the bay electronics and
fights the power section's deliberate heat offload.

The elegant part: **no new sensors are needed.** The per-plate **SHT41** (x4,
`sensor_pcb.md`) gives dew point; the **MLX90614** IR thermopiles give non-contact
plate-underside temperature (both already on the TCA9548A I2C bus). Control law:
hold `T_underside (MLX90614) > DewPoint(SHT41) + 2°C`; raise purge flow or lip heat
as the margin closes. Condensation becomes a monitored, actively-rejected state, not
a surprise. **Tune the exact flow and ΔT at Stage-0 Phase C with warm 37°C media** —
that yields the production setpoints. The purge flow rate and the fog-free margin are
**unproven until that bench measurement**; the control structure is reserved, the
numbers are not yet evidence.

The reserved control structure is encoded in `src/aevum_smis/condensation.py`.
It computes dew point from the local SHT41 sample, compares it to the MLX90614
underside temperature, blocks acquisition below the reserved +2°C margin, and
returns explicit purge/heat actions as the margin closes. The software gate is
therefore falsifiable today while the final flow and lip-heat setpoints remain
Stage-0 Phase C evidence, not guessed constants.

## 5. Control + OT-2 coordination

### Compute and driver location — dumb head, smart host

Klipper-style split. **Head-side (rides the truck):** a bare **MIPI CSI camera
sensor** + a **Raspberry Pi 5 / CM4** (CSI capture, JPEG encode, autofocus inner
loop, buffering — the only computer in the bay) + one ESP32-S3/RP2040 motion MCU +
2x TMC2209 (X, Z) on small heatsinks + the addressable LED ring + the MLX90614.
**Offboard (across the GX16):** the Y stepper + driver (parked at the row end), the
orchestration host, and the PSU (add a 24 V motor rail to the existing 5 V Pi rail).
Strobe the LED and duty-cycle motors <5 % (closed-loop encoders hold position with
holding current disabled) to keep average bay dissipation <2 W, inside the
1.4 µm/°C focus-drift budget.

### Camera interface — CSI → head Pi → Gigabit Ethernet, never USB3 over flex

This is the call against the moving-cable reality. **Do not run raw USB3 over a
334.5 mm drag-chain** — a 5 Gb/s differential link is the documented field-failure
mode (bend fatigue, heater-PWM EMI on the umbilical, connector fretting). Instead the
high-rate MIPI CSI link is a ~10 cm rigid FPC **on the truck, never in the chain**;
only **5 V power + Gigabit Ethernet + an E-stop pair** cross the moving cable and the
wall. Ethernet is differential-robust in continuous flex; keeping CSI on the head
keeps the autofocus loop sub-frame-latency (no per-well network round-trip).
**Connector honesty: GX16 is not USB3-rated.** Power, motor phases, LED, and logic
cross the GX16; data crosses a **separate shielded bulkhead** (M12 X-coded GigE) —
two connectors at the wall, split by noise class.

**BOM consequence:** the bench's IMX178 is USB3 (fine for static Stage 0). For the
moving build, source a **mono CSI sensor** (IMX178 CSI if available, else
`IMX296 MIPI 黑白`-class). Global-shutter IMX273 is the named escape only if
Stage-2/3 settle testing shows residual jitter corrupting rolling-shutter frames.

### Cable carrier

A **side-mounted micro energy chain** (R10, inner ~10x10, `微型拖链`) bending in the
vertical Y-Z plane inside the reserved 8 x 24 mm raceway, thin dimension facing the
8 mm Y constraint. A **printed raceway lid** mechanically forbids the loop from
leaving the bottom 24 mm — the wet/dry separation witness and the single most
important serviceability part. The moving end terminates at the **truck** (which
stays installed); the head is a kinematic drop-in with a **blind-mate
pogo/board-to-board connector** so head swaps never touch the chain. **Watch item:**
an R10 micro-chain loop height is ~24 mm with ~0 mm margin — buy one segment and
caliper the real loop height *with cable in it* before freezing the lid; thinning the
bundle (head-local compute removes the data flex) drops it to inner 7x7 if needed.

### OT-2 interlock — strict mutual exclusion, observer as a bridge-daemon client

**Reject simultaneous operation.** The OT-2 and the observer share one mechanical
frame across a thin plate: an OT-2 pipette puncture induces deck sway that violates
the ±27 µm exposure-stillness spec, and two independent motion controllers with no
shared collision model violate the single-writer invariant. The observer is a
**client of the existing OT-2 bridge daemon** (`docs/knowledge/agent_ot2_bridge.md`),
requesting a `kind: "observer_scan"` lease that is mutually exclusive with the
pipetting lease. This reuses the proven SQLite lock/lease/fail-closed-recovery/
evidence stack wholesale; whichever subsystem asks second gets `robot_busy`. The
observer's MCU and Pi *execute* motion, but **authority to move is granted by the
bridge** — one brain, two bodies, hardware-enforced one-at-a-time. Building an
independent observer controller with a peer handshake would create a second writer,
exactly what the architecture forbids.

**Three-layer safety, defense in depth:**

1. **Software lease (cooperative):** the SQLite motion lease extended to cover
   observer sessions; renewed before every move; expiry → `needs_recovery`, never
   auto-handoff.
2. **Physical E-stop interlock (the backstop a software lock legally cannot
   provide):** the observer's TMC2209 enable pins are hardware-gated by a signal the
   bridge asserts only while the observer lease is held — lease released → enable
   line drops → motors disabled at the driver regardless of software state. Inversely,
   the bridge will not grant a pipetting lease until the observer reports a hardware
   **"head parked + Z-retracted"** limit. A master E-stop in this loop cuts the
   observer 24 V rail. The GX16 carries this safety loop; the physical disconnect is
   the ultimate authority boundary — the same philosophy as the power section's
   umbilical disconnect.
3. **Hardware Z-gate on XY enable (added 2026-09-23, observer-internal):** the same
   Z-retract signal also gates the observer's *own* X and Y driver enables, so no XY
   move is possible with the nose above z = 0 — see §2, "Safety requirement". Layers
   1 and 2 protect the OT-2 from the observer; this layer protects the **consumable
   plate** from the observer, which nothing else in the stack was watching.

**Scheduling:** a time-lapse scheduler (e.g. hourly) on the host *proposes* a scan
window; the bridge *grants* it only when the OT-2 is idle/homed. Late or deferred
scans are logged as evidence — a missed time-lapse point is auditable, never a silent
gap. Each captured frame is an Evidence packet (`docs/knowledge/evidence_model.md`):
well ID, focus-Z, focus metric, illumination mode, timestamp, lease/run ID, and the
fiducial-transform checksum, written under `data/measurements/observer/`.

### Registration

On the plate-support frame (not the plate — the plate is a no-contact consumable),
the 16 Ø2 mm fiducials are at known CAD coordinates. The head images them, centroids
the circles sub-pixel (a 2 mm fiducial spans ~930 px at the bench's 2.16 µm/px, and
~2,300 px on the 10x drill-down; *corrected 2026-09-23 — the "~1400-3300 px" this
read reproduced only from the retired "~0.6-1.4 µm/px" sampling*), and
fits a 2D rigid transform from carriage frame → plate-support datum over ≥3
non-collinear fiducials. All 384 well centers then come analytically from the 9 mm
pitch and `A1_center` — **note A1 is offset at x = 14.38, y = 11.24, not at the bay
origin** (`first_well_center_*`), which is load-bearing for the map. Re-run the
fiducial fit **every plate load** (seconds) so the transform tracks kinematic-seating
variation (~±50-100 µm — smaller than the 0.23 mm per-side X field margin over the
Ø6.21 mm well, and small against the 4.46 mm Y read band it recentres). The
fiducials are the shared
coordinate bridge between the two robots: the observer independently recovers the
installed pose and cross-checks the declared canonical→installed transform rather
than re-transforming target coordinates.

## 6. What to consider — drivers ranked by likelihood of breaking the module

| # | Driver | Key number | Why it breaks the module | Cheap retire |
|---|---|---|---|---|
| **1** | **Label-free contrast through media** (upstream of everything) | Michelson **≥0.15** | If oblique-from-below fails, the sealed top is in question → an optical window in the wet lid → re-cost the whole gas manifold. Cascades into illumination. | ¥40 WS2812 matrix, Stage-0 Phase D. **Settle this before building any motion.** |
| **2** | **Carriage Y-traverse overflow** (CAD blocker retired 2026-09-21; Stage-3 physical proof still open) | **retired — 0.0 mm today** (the **44.6 mm** headline was 392.5 vs a pre-2026-06-14 bay-Y of 347.9; live bay-Y is **357.5**, so the fat-body figure would now read 35.0 mm) | No motion plan exists until the topology changes | Done in CAD: `_observer_carriage_traverse` sweeps the **13 mm truck**, not the 58 mm body → `fits_dry_bay = True`, overflow 0.0 on both axes, **10.0 mm** of traverse-axis margin. What still blocks `clears_traverse` is the deck feet (1 collision) and the corridor (−2.72 mm), not the bay. |
| **3** | **Settle forcing stop-and-shoot** | **~210 ms** (4x) / **~510 ms** (10x) ring-down | Sets the whole throughput envelope; 5x worse collapses biology-interval compatibility | ¥20 ADXL345 on the head → measure f, Q → free Klipper input-shaping; sorbothane head shim. Stage 2. |
| **4** | **Condensation on plate underside** | `T_underside > DewPoint + 2°C` | Fog = scatter = contrast and focus death; the genuinely hard interface | Dry-gas snorkel purge + lip heat, closed-loop on existing SHT41/MLX90614. Stage-0 Phase C, warm media. |
| **5** | **OT-2 structure-borne vibration** | idle-floor must be **<4 µm** at head | If the robot cannot be isolated, concurrency is dead and interlock is mandatory; possibly cannot image during any deck activity | ADXL345 log OT-2-move vs idle; sorbothane pucks under standoffs; default to time-sliced interlock. |
| **6** | **Z focus backlash / 10x viability** | **<±4 µm** @ 10x | Stepper-leadscrew backlash makes 10x AF oscillate | Voice-coil fine-Z (¥30-80); bench-measure refind repeatability. 4x is safe regardless. |
| **7** | **Thermal focus drift** | **1.4 µm/°C** (60 mm Al loop); 4 µm/°C if PLA | Slow defocus over a scan | All-aluminum loop (no PLA), duty-cycle motors <5 %, per-well AF absorbs slow drift, SHT41 logs bay T. |
| **8** | **USB3 over moving cable** (avoided by design) | 5 Gb/s x thousands of flex cycles | Dropped frames mid-scan if the naive path is taken | CSI → Pi → GigE; only power + Ethernet cross the chain. Design-resolved. |
| **9** | **Plate-seating + registration** | land within **±0.2 mm** to keep the whole well in the X field (revised 2026-09-23: the corrected 6.67 mm X field leaves **0.23 mm** per side over a Ø6.21 mm well, not the ±0.5 mm this row claimed; ±0.5 mm only keeps the *read band* on the well) | Lowest mechanical risk — any homed gantry beats this 5x | Fiducial-correct off the 16 Ø2 mm targets every plate load (A1 offset 14.38, 11.24); vision over mechanical precision. |
| **10** | **Humid-bay corrosion / cable fatigue** | ~8,700 scans/yr, >5M flex cycles | Months-scale field death: rusted rails, dried lube, cracked chain | Stainless/chrome rails, continuous-flex cable, dry-film lube, 1-week 2000-cycle soak. |
| **11** | **Aperture-limited well reach** (appended 2026-09-23) | **128 of 384** reachable; aperture deficit **17.21-17.80 mm both axes** | Two thirds of every plate is unimageable from below; no motion plan recovers it | Enlarge the tile aperture to ~110 x 74 mm in `cad/one_row_coupon.params.json` — **CAD-testable, zero hardware**, recommended not applied in this pass. |
| **12** | **High-NA illumination** (appended 2026-09-23) | r = 13 mm ring needs **77.0deg** at a 3 mm WD; **~30 %** Fresnel loss | The head-mounted oblique ring is a long-WD solution and does not port to any NA ≥ 0.45 head | Nothing cheap is known. Open decision #4; the Stage-0 WS2812 fork measures only the long-WD case. |

Rows 11 and 12 are **appended, not inserted** — the 1-10 ranking above predates them
and is deliberately not re-sorted, because other sections of this document cite these
drivers by number. On likelihood of breaking the module, #11 belongs near the top.

## 7. Build sequence — mapped onto Stages 1-4

Each stage is a real build (or, for Stage 0, a static rig) that produces Gate-6
evidence and converts a reserved envelope into an installed, measured part. Stage 0
is the optical bench, owned by `observer_optical_bench.md`; it retires the two
upstream killers (contrast, condensation) before any motion exists.

| Stage | What it proves (Gate-6 evidence) | Highest-leverage step |
|---|---|---|
| **0 — static bench** (`observer_optical_bench.md`) | Drivers #1 (contrast) and #4 (condensation): oblique-from-below at 33.2deg clears Michelson ≥0.15 through real media; purge + lip holds fog-free for a dwell | Buy the ¥40 WS2812 matrix and run the contrast fork |
| **1 — focus Z axis** | Driver #6: the voice-coil Z hits ±4 µm (10x) repeatably; map-AF + bracket works on the rigid plate | Build the VCM focus axis + the autofocus inner loop on the head Pi |
| **2 — one-plate XY scan** | Drivers #3, #5, #7: **measure real settle f/Q with the ADXL345**, OT-2 coupling, thermal drift; decides single-head vs two-gantry split | Mount the ¥20 ADXL345 and measure ring-down — turns vibration/settle/thermal from guesses into an input-shaper config |
| **3 — full-row scan** | Driver #2: physically proves the **13 mm-truck traverse** fits and holds still over 334.5 mm. The make-or-break | Build the thin-truck Y gantry; validate the re-parameterized CAD traverse against hardware |
| **4 — service / vibration / thermal** | Drivers #5, #10: 5-cycle cartridge install/remove, drag-chain recovery, 1-week soak | Soak test + kinematic-mount re-registration |

**The single highest-leverage next physical step:** buy the **¥40 WS2812 LED matrix**
and run the Stage-0 oblique-from-below contrast test. It costs almost nothing, it is
upstream of every other decision, and a failure there changes the entire architecture
(it forces an optical window in the sealed wet lid). The **¥20 ADXL345** is the
second buy — together they convert the two biggest unknowns (contrast, settle/
vibration) from arguments into measurements, and ensure Stage 3 is a motion problem,
not also an optics, condensation, or vibration problem.

## 8. Top open decisions

1. **Single thin-truck gantry vs two-plate split.** One 334.5 mm beam with
   input-shaping (~¥1,940 optics, ~6-10 min/row) **or** two 167 mm beams (~2x
   optics ≈ +¥1,900, ~3-5 min/row, √2 stiffer). **Decision gate:** the Stage-2
   ADXL345 settle measurement — if a single beam cannot hold ±27 µm even
   input-shaped, split. Default to single until the data forces the split; throughput
   does not force it, only stiffness would.

2. **Keep 10x in the production path, or 4x-only.** Commit the voice-coil + ±2 µm AF
   + frequent thermal re-cal to keep the 10x drill-down **or** drop to 4x-only (the
   55.0 µm total (±27.5 µm) DOF makes everything forgiving — map-AF alone nearly
   suffices, no VCM
   precision needed). **Decision gate:** does the assay actually need 10x morphology,
   or does 4x confluence/count carry the biology? This sets whether focus is a hard
   problem or a solved one.

3. **OT-2 strict interlock vs vibration-isolated concurrency.** Hard time-sliced
   interlock (observer scans only when the OT-2 is parked — simplest, safest, costs
   nothing) **or** sorbothane-isolate the standoffs and attempt concurrent operation
   (faster end-to-end if a protocol needs imaging during long pipetting). **Decision
   gate:** the Stage-2 ADXL345 log of OT-2-move-vs-idle deck floor — if the idle floor
   is not <4 µm at the head, concurrency is dead regardless and interlock is mandatory.
   Default to interlock; pursue concurrency only if a real protocol timeline demands it
   **and** the isolation data supports it.

4. **How a high-NA head is illuminated — unsolved (opened 2026-09-23).** The
   head-mounted r = 13 mm oblique ring works at the 19.90 mm standoff (33.2deg) and
   is shadowed at a 3 mm working distance (77.0deg, ~30 % Fresnel loss) — see §4.
   Through-objective epi (spends the reserved infinity space) **or** a fixed ring on
   the tile-aperture rim (reintroduces per-well uniformity calibration) **or**
   brightfield-only at high NA. **Decision gate:** this cannot be gated on Stage-0,
   because the Stage-0 bench measures the long-WD geometry only. It needs its own
   short-WD contrast measurement, and that measurement does not currently exist in
   any stage plan. Default is "unsolved", not "the ring, but higher".

5. **Whether to enlarge the tile aperture.** Today's 88 x 52 mm aperture reaches
   **128 of 384** wells; ~110 x 74 mm reaches 384 of 384 and also satisfies the
   skirt-flange-only cradle spec that `observer_optical_bench.md` asserts in three
   places. **Decision gate:** whether the plate support retains adequate stiffness
   and the deck-foot keepouts survive a 17.21-17.80 mm-per-axis aperture growth — a
   row-coupon CAD question, not an observer question. Recorded here as a
   recommendation against `cad/one_row_coupon.params.json`
   (`dry_bay.aperture_length_x`, `dry_bay.aperture_width_y`); **not applied in this
   pass.**

## Cross-references

- Stage 0, the static optical bench, optics BOM, Z-budget, and the ±27 µm/±4 µm
  vibration spec: `observer_optical_bench.md`
- The swappable-sensor platform (SMIS) that turns this moving stage into a carrier
  for plug-in modality heads — Raman, fluorescence, quantum thermometry:
  `sensor_module_interface.md`
- Row coupon CAD — dry bay, envelopes, deck interface, well grid, fiducials:
  `one_row_coupon.md`, `cad/one_row_coupon.params.json` (`observer_robotics`,
  `dry_bay`, `deck_interface`, `well_grid`; A1 offset `first_well_center_x = 14.38`,
  `first_well_center_y = 11.24`)
- The carriage-traverse swept-volume check and the `carriage_traverse_exceeds_dry_bay`
  Gate-6 blocker: `src/aevum_cad/row_coupon/parts/observer.py:151`
  (`_observer_carriage_traverse`); call site `src/aevum_cad/row_coupon/layout.py:914`;
  traverse-axis span choice at `parts/observer.py:213`; blocker raised at
  `parts/observer.py:888` (path corrected 2026-09-23 after the module became a
  package; the former four-digit line numbers are deleted rather than re-guessed)
- AC→DC power stack and the GX16 umbilical authority-boundary pattern this module
  replicates: `power_section.md`
- Custom CO2/RH/T board (STC31/SHT41) and the per-plate SHT41 telemetry the
  condensation loop consumes: `sensor_pcb.md`
- Single-writer OT-2 bridge daemon the observer is a lease client of:
  `docs/knowledge/agent_ot2_bridge.md`
- Evidence packet model the acquire() ABI returns into:
  `docs/knowledge/evidence_model.md`
- The objective ladder (NA, working distance, correction collars) that the
  short-WD motion model in §2 makes reachable: `sensor_module_interface.md`
- Tile through-aperture params behind the 128-of-384 reach limit:
  `cad/one_row_coupon.params.json` (`dry_bay.aperture_length_x` 88.0,
  `dry_bay.aperture_width_y` 52.0) — enlargement recommended, not applied
- Dated decisions: `decision_log.md`
