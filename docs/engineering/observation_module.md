# Observation Module (Moving In-Bay Scanner, Stages 1-4)

## Purpose

The observation module is the **moving** realization of the observer subsystem:
the 3-axis micro-scanner that lives as a drop-in cartridge in the 80 mm dry
observation bay, carries the optical head documented in
`observer_optical_bench.md`, and indexes it under all 384 wells of the row module
to image cells from below through glass. Where the optical bench is Stage 0 — one
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
| Deck-foot inset / width | **8 mm X-inset, 7 mm Y** (`foot_inset_x`, `foot_width_y`) | feet at the X-perimeter; central ~120 mm bay clear |
| Service raceway | **8 mm Y x 24 mm Z**, R10 bend (`service_raceway_*`) | the only place flexing cable may live |
| Cell-plane standoff | **~9.73 mm** above z = -8 | 8 mm air + 0.6 mm window + media + 0.17 mm coverslip |
| DOF (from bench) | **±55 µm @ 4x / ±4 µm @ 10x** | focus tolerance per magnification |
| Hold-still spec (from bench) | **±27 µm @ 4x / ±4 µm @ 10x** | the vibration acceptance threshold the motion design inherits |

The cell plane sits ~9.73 mm above the z = -8 head ceiling; the 4x objective's
~22 mm working distance leaves the front element well below the ceiling with margin.
The hold-still spec is the bench's own conservative number (half the 4x DOF) handed
to the motion designer as the acceptance threshold for every moving stage.

## 2. How it moves — resolved kinematics

### Three axes, and why not two or four

| Axis | Carries | Stroke | Actuator | Transmission | Guide |
|---|---|---|---|---|---|
| **Y (row, long)** | X-stage + head; motor **parked at one end** | 334.5 mm | NEMA17 closed-loop | **steel-core GT2 belt** (a 335 mm leadscrew whips) | **stainless HGH15 / MGN12 rail** |
| **X (scan)** | head | ~110 mm | NEMA14 closed-loop | GT2-6 belt | MGN9 / MGN12 |
| **Z (focus)** | objective + fold parfocal block only | 12 mm | **voice-coil (VCM)** | direct / flexure | flexure or MGN9 |

**X must be a real mechanical scan, not optics.** At 4x the FOV is 5.6 x 4.2 mm
against a Ø6.21 mm well on a 9 mm pitch; covering 12 columns optically would need
12 parallel heads (absurd cost, unpackable in 100 mm) or a scan optic that destroys
the collimated infinity space the fold mirror lives in. So X is a mechanical axis on
the head. **Z is the only demanding axis** (10x DOF is ±4 µm); **no fourth axis
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

This is the make-or-break, and it resolves in CAD before any hardware. The current
swept-volume check `_observer_carriage_traverse` (`src/aevum_cad/row_coupon.py`,
line 9816) sweeps the **full 58 mm `carriage_width_y`** along the 334.5 mm Y row:

```
334.5 (well span) + 58 (carriage_width_y) = 392.5 mm  vs  347.9 mm dry-bay Y envelope
-> 44.6 mm overflow (22.3 mm past each row end)
```

This is the source of the `carriage_traverse_exceeds_dry_bay` Gate-6 blocker added
this session (line 13803). The check is correct as a conservative blocker, but the
58 mm is the body's cross-section **at one Y-station** — it is not a width that must
physically exist continuously along all 334.5 mm of travel. The code even flags this
at line 9854 (`span_y = float(carriage_width_y)`): picking the wrong dimension makes
the scan axis report the overflow.

**The fix: sweep the ~13 mm truck, not the 58 mm box.** Re-split the kinematics so
the *physically continuous* Y structure is thin. The Y mover is a flat transverse
truck thin on the traverse axis (~13 mm) carrying the X-stage and head; the 58 mm
carriage cross-section was an over-reservation. With only the thin truck traversing,
the swept Y collapses:

```
334.5 (well span) + 13 (truck width) = 347.5 mm  <  347.9 mm  -> fits with ~0.4 mm margin
```

This is implemented: `_observer_carriage_traverse` now sweeps a
`gantry_truck_traverse_extent` (13 mm) param on the traverse axis instead of
`carriage_width_y = 58`, which clears the `carriage_traverse_exceeds_dry_bay`
blocker. **This is geometric evidence only** — the topology *can* fit; whether a
~13 mm beam holds still and traverses 334.5 mm repeatably is Stage-3 physical work,
still Gate-6 blocked.

**But the Y fix relocated its burden onto the X scan axis — and a do→review cycle
caught it.** The head scans X across the 99 mm column span, so the scan-axis swept
extent is `99 + head-X-footprint`. The dry-bay X is 120.2 mm, so after the well
span only **~0.2 mm of X budget remains — barely the bare objective barrel.** The
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

The **reject** here is the two-gantry split (two 167 mm beams, two heads). It is a
*different, more expensive* fix (~2x the ¥1,885 optical core) that buys throughput,
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
   ~0.6 µm/px moving even 2 µm during a 10 ms exposure smears ~3 px.
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
   3-frame Brenner/Tenengrad bracket at **±40 µm** (inside the ±55 µm 4x DOF) picks
   the sharpest. The bracket catches local sag and debris without a full sweep.

At 4x, ±55 µm DOF makes the map alone nearly sufficient; the bracket is cheap
insurance. **Reject** pure per-well contrast sweep (doubles scan time, noisy on a
low-contrast target) and **reject** a laser/reflective focus sensor (the 0.17 mm
coverslip presents two reflecting surfaces 0.17 mm apart → wrong-surface lock, and
it competes for the objective keepout — not worth it at 4x). The **10x drill-down**
(±4 µm DOF, step ≤2 µm, full sweep) is a sparse per-well escalation on QC-flagged
wells only — the one place the VCM's precision earns its keep.

### FOV / tiling

At 4x, FOV is **5.6 x 4.2 mm vs Ø6.21 mm well** → **one centered frame** captures
the central ~4.2 mm band where confluence and morphology are read. You lose a thin
crescent at the well's left/right edges, which is meniscus-distorted anyway. No
z-stack at 4x (DOF swallows field tilt). Escalate to a **2x2 mosaic** (~4 frames,
full well including edges, phase-correlation stitch on the host) only on QC failure.

### Throughput for 384 wells

| Mode | Per-well | 384-well row |
|---|---|---|
| **Default: 4x, 1 frame, map-AF + bracket** | ~0.9 s | **~6-10 min** |
| 4x, full contrast-AF every well | ~2.5 s | ~16 min |
| 4x, 2x2 mosaic | ~3.0 s | ~19 min |
| Two-gantry split (reserve) | — | halve the above |

The honest production number is **~6-10 min single-head** — comfortably inside any
live-cell time-lapse cadence (15 min-1 hr). **Throughput is not the binding
constraint; focus reliability and label-free contrast are.** Phototoxicity is
near-zero (oblique label-free, ~0.1 % LED duty, no fluorescence excitation) — the
genuine advantage of this architecture. All cycle times above are estimates pending
Stage-2 settle measurement.

### Carried optics

Unchanged from the bench (`observer_optical_bench.md`): 4x infinity plan-achromat
RMS objective (NA 0.10, WD ~22 mm, 0.17-corrected) → 45deg first-surface fold →
f50 achromatic doublet → mono CMOS, 10x as the parfocal drill-down swap. Route the
horizontal post-fold axis **along X**, which keeps the heavy camera off the Y-truck
and only the ~60 mm objective + fold column in the 62 mm Z envelope. Keep ~25-40 mm
of collimated infinity space reserved for a future dichroic — build nothing, block
nothing; that is the reserved Raman/fluorescence budget.

## 4. Illumination on the move + condensation

### Illumination rides the head

A **small-pitch addressable LED ring** (WS2812B-2020 / SK6812, ~16-24 px, **Ø26 OD
inside the Ø32 keepout** — the load-bearing fit number) bonded to the front-end body
at **r ≈ 13 mm**, firing one to two azimuthal quadrants at **~53deg from vertical**
(geometry: `atan(13 / 9.73) = 53.2deg`) for oblique phase-gradient / pseudo-DIC
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

**Inter-well stray light → a matte-black single-well snorkel** (carbon-PETG, OD
≤Ø31 inside the keepout, top aperture Ø6.5-7 mm framing exactly one well, lip
~1.5 mm off the plate, **never touching** — the no-contact consumable rule). At
9 mm pitch the gap between Ø6.21 mm well bottoms is only ~2.8 mm, so oblique light
at 53deg splashes into neighbors without containment. The snorkel does triple duty:
optical isolation, camera baffle, and purge plenum (below). The lip-to-plate gap is
the leak path for both light and gas and is the hard no-contact tradeoff number —
**measured at Stage-0 Phase C/D, not guessed**, then fed back into the
`front_end_*` swept-body params.

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

**Two-layer safety, defense in depth:**

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

**Scheduling:** a time-lapse scheduler (e.g. hourly) on the host *proposes* a scan
window; the bridge *grants* it only when the OT-2 is idle/homed. Late or deferred
scans are logged as evidence — a missed time-lapse point is auditable, never a silent
gap. Each captured frame is an Evidence packet (`docs/knowledge/evidence_model.md`):
well ID, focus-Z, focus metric, illumination mode, timestamp, lease/run ID, and the
fiducial-transform checksum, written under `data/measurements/observer/`.

### Registration

On the plate-support frame (not the plate — the plate is a no-contact consumable),
the 16 Ø2 mm fiducials are at known CAD coordinates. The head images them, centroids
the circles sub-pixel (a 2 mm fiducial spans ~1400-3300 px at the bench sampling), and
fits a 2D rigid transform from carriage frame → plate-support datum over ≥3
non-collinear fiducials. All 384 well centers then come analytically from the 9 mm
pitch and `A1_center` — **note A1 is offset at x = 14.38, y = 11.24, not at the bay
origin** (`first_well_center_*`), which is load-bearing for the map. Re-run the
fiducial fit **every plate load** (seconds) so the transform tracks kinematic-seating
variation (~±50-100 µm, smaller than the FOV margin). The fiducials are the shared
coordinate bridge between the two robots: the observer independently recovers the
installed pose and cross-checks the declared canonical→installed transform rather
than re-transforming target coordinates.

## 6. What to consider — drivers ranked by likelihood of breaking the module

| # | Driver | Key number | Why it breaks the module | Cheap retire |
|---|---|---|---|---|
| **1** | **Label-free contrast through media** (upstream of everything) | Michelson **≥0.15** | If oblique-from-below fails, the sealed top is in question → an optical window in the wet lid → re-cost the whole gas manifold. Cascades into illumination. | ¥40 WS2812 matrix, Stage-0 Phase D. **Settle this before building any motion.** |
| **2** | **Carriage Y-traverse overflow** (Stage-3 blocker) | 392.5 vs 347.9 = **44.6 mm** | No motion plan exists until the topology changes | Re-parameterize `_observer_carriage_traverse` to sweep the **13 mm truck**, not the 58 mm body → fit with 0.4 mm. **CAD-testable today, zero hardware.** |
| **3** | **Settle forcing stop-and-shoot** | **~210 ms** (4x) / **~510 ms** (10x) ring-down | Sets the whole throughput envelope; 5x worse collapses biology-interval compatibility | ¥20 ADXL345 on the head → measure f, Q → free Klipper input-shaping; sorbothane head shim. Stage 2. |
| **4** | **Condensation on plate underside** | `T_underside > DewPoint + 2°C` | Fog = scatter = contrast and focus death; the genuinely hard interface | Dry-gas snorkel purge + lip heat, closed-loop on existing SHT41/MLX90614. Stage-0 Phase C, warm media. |
| **5** | **OT-2 structure-borne vibration** | idle-floor must be **<4 µm** at head | If the robot cannot be isolated, concurrency is dead and interlock is mandatory; possibly cannot image during any deck activity | ADXL345 log OT-2-move vs idle; sorbothane pucks under standoffs; default to time-sliced interlock. |
| **6** | **Z focus backlash / 10x viability** | **<±4 µm** @ 10x | Stepper-leadscrew backlash makes 10x AF oscillate | Voice-coil fine-Z (¥30-80); bench-measure refind repeatability. 4x is safe regardless. |
| **7** | **Thermal focus drift** | **1.4 µm/°C** (60 mm Al loop); 4 µm/°C if PLA | Slow defocus over a scan | All-aluminum loop (no PLA), duty-cycle motors <5 %, per-well AF absorbs slow drift, SHT41 logs bay T. |
| **8** | **USB3 over moving cable** (avoided by design) | 5 Gb/s x thousands of flex cycles | Dropped frames mid-scan if the naive path is taken | CSI → Pi → GigE; only power + Ethernet cross the chain. Design-resolved. |
| **9** | **Plate-seating + registration** | land within **±0.5 mm** to keep well in FOV | Lowest mechanical risk — any homed gantry beats this 5x | Fiducial-correct off the 16 Ø2 mm targets every plate load (A1 offset 14.38, 11.24); vision over mechanical precision. |
| **10** | **Humid-bay corrosion / cable fatigue** | ~8,700 scans/yr, >5M flex cycles | Months-scale field death: rusted rails, dried lube, cracked chain | Stainless/chrome rails, continuous-flex cable, dry-film lube, 1-week 2000-cycle soak. |

## 7. Build sequence — mapped onto Stages 1-4

Each stage is a real build (or, for Stage 0, a static rig) that produces Gate-6
evidence and converts a reserved envelope into an installed, measured part. Stage 0
is the optical bench, owned by `observer_optical_bench.md`; it retires the two
upstream killers (contrast, condensation) before any motion exists.

| Stage | What it proves (Gate-6 evidence) | Highest-leverage step |
|---|---|---|
| **0 — static bench** (`observer_optical_bench.md`) | Drivers #1 (contrast) and #4 (condensation): oblique-from-below at 53deg clears Michelson ≥0.15 through real media; purge + lip holds fog-free for a dwell | Buy the ¥40 WS2812 matrix and run the contrast fork |
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
   input-shaping (~¥1,885 optics, ~6-10 min/row) **or** two 167 mm beams (~2x
   optics ≈ +¥1,900, ~3-5 min/row, √2 stiffer). **Decision gate:** the Stage-2
   ADXL345 settle measurement — if a single beam cannot hold ±27 µm even
   input-shaped, split. Default to single until the data forces the split; throughput
   does not force it, only stiffness would.

2. **Keep 10x in the production path, or 4x-only.** Commit the voice-coil + ±2 µm AF
   + frequent thermal re-cal to keep the 10x drill-down **or** drop to 4x-only (the
   ±55 µm DOF makes everything forgiving — map-AF alone nearly suffices, no VCM
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
  Gate-6 blocker: `src/aevum_cad/row_coupon.py` (`_observer_carriage_traverse`,
  line 9816; `span_y` at line 9854; blocker at line 13803)
- AC→DC power stack and the GX16 umbilical authority-boundary pattern this module
  replicates: `power_section.md`
- Custom CO2/RH/T board (STC31/SHT41) and the per-plate SHT41 telemetry the
  condensation loop consumes: `sensor_pcb.md`
- Single-writer OT-2 bridge daemon the observer is a lease client of:
  `docs/knowledge/agent_ot2_bridge.md`
- Evidence packet model the acquire() ABI returns into:
  `docs/knowledge/evidence_model.md`
- Dated decisions: `decision_log.md`
