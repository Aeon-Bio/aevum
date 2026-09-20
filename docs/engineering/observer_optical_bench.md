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
`observer_sweep_extra_y = 12.2` — chosen so the bay just barely wraps a guessed
front-end swept body (~0.1–0.2 mm of slack). The front-end itself is a placeholder
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
| Front-element ceiling | **z = −8 mm** (`carriage_top_clearance_z = 8`) | top of any optical hardware sits at/below this |
| Objective keepout | **Ø32 mm** (`objective_keepout_diameter`) | front barrel must fit inside |
| Cell plane standoff | **≈ 9.73 mm** above z = −8 | 8 mm air + 0.6 mm plate window + ~1.0 mm + 0.17 mm coverslip |
| Well bottom imageable circle | **Ø6.21 mm** (`lower_well_diameter`) | per-well field to cover |
| Coverslip | **#1.5H, 0.170 mm** (`coverslip_thickness_z`) | standard objective correction thickness |
| Well pitch | **9.0 mm** X and Y | 96 wells/plate, 384 wells/row |
| Well-center span | **99.0 mm X × 334.5 mm Y** | the full scan the production observer must reach |

The plate is CellVis P96-1.5H-N. Cells live on the **top** surface of the 0.17 mm
coverslip and are imaged from below through that glass — standard inverted
geometry, and the coverslip thickness most objectives are corrected for.

## Build-out trajectory: how the bay gets filled

The bench is Stage 0 of a staged physical build-out. Each stage is a real build
inside (or representing) the bay envelope, produces Gate 6 evidence, and converts
a validation-only envelope into an installed part plus a measured parameter.

| Stage | What gets built | Proves (Gate 6 evidence) | Envelope → part | Param pinned |
|---|---|---|---|---|
| **0 — Static focus cell** (this doc) | One optical head fixed under one well, real plate, real media, real illumination | Focus on cell plane through 0.17 mm glass + media; signal/contrast; real WD + head footprint; condensation behavior; field flatness | *(measurement)* | kills `observer_sweep_extra_x/y`; sets `front_end_*` |
| **1 — Focus (Z) axis** | The 12 mm focus actuator under the head | Repeatable autofocus on the cell plane | `focus_stroke` → real axis | `front_end_focus_stroke_z` |
| **2 — One-plate scan** | XY traverse over one plate (96 wells) | Repeatable focus across wells, field flatness across the plate, settle time; the real moving-head + carrier envelope | `front_end_swept_body` + carriage (one plate) → real gantry | front-end swept body, carriage footprint |
| **3 — Full-row scan** | Extend Y to 334.5 mm, all 4 plates / 384 wells | **The make-or-break:** does a 62 mm-tall carrier + gantry fit AND traverse the full bay without hitting deck feet, inside 80 mm | `observer_kinematic_split_check` → proven traverse | resolves the carriage-traversal gap |
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
**mono CMOS, Sony IMX178** (1/1.8", 2.4 µm pixels, 3088 × 2064). A **10× infinity
plan-achromat** (NA 0.25, WD ~8 mm) is the single parfocal upgrade. A
programmable **WS2812 16 × 16 LED matrix** above the plate resolves the
illumination fork.

| Quantity (4× primary, IMX178) | Value | Consequence |
|---|---|---|
| Effective magnification (f_tube 50 / f_ref 180) | ~1.1× | demagnified onto the small sensor |
| Sampling at cell plane | **~0.6–1.4 µm/px** | a 10–20 µm cell spans 10–30+ px — fully resolved |
| Optical (Abbe) resolution, NA 0.10 | **~3.4 µm** | confluence + gross morphology (not organelles) |
| FOV on IMX178 (8.92 mm diag) | **~5.6 × 4.2 mm** | captures ~90 % of the 6.21 mm well in one frame; full well = 2–4 tile stitch or drop f_tube to ~40 mm |
| Depth of field, NA 0.10 | **±55 µm** | swallows plate tilt/sag; forgiving focus |
| Working distance | **~22 mm** | front element sits well below the z = −8 ceiling with margin |
| Straight-down Z (objective parfocal ~45 + fold mirror ~15) | **~60 mm ≤ 62 mm** | **fits**, tube lens + camera routed horizontally |
| Front barrel diameter | **≤ 25 mm < 32 mm** | inside the objective keepout |

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

USD at ¥7.1. **Core 4× build ≈ ¥1,885 ≈ $266.** First-light de-risk subset ≈ $230.
Adding the 10× lands at ~$300.

| Part | Spec | Taobao term (中文) | ~¥ |
|---|---|---|---|
| **4× objective** (primary) | infinity plan-achromat, RMS, NA 0.10, WD ~22 mm, 0.17-corrected | `无限远物镜 4X 平场消色差 RMS` | 150 |
| **10× objective** (upgrade) | infinity plan-achromat, NA 0.25, WD ~8 mm, parfocal w/ 4× | `无限远物镜 10X 平场消色差` | 250 |
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

**Recommended first purchase (~$230):** 4×, tube lens, IMX179 board cam, RMS→C
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
   corner pusher (−X, −Y). Central cutout ≥ 90 × 54 mm so the full 88 × 52 mm
   observation window is open from below — **nothing under any well, skirt flange
   only.** Mount on two posts so the plate-bottom plane sits ~90–100 mm above the
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
  the optical prediction (4×/NA 0.10 → ~3.4 µm → USAF Group 7 Element 1 clearly).
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
  output.
- **Phase D — live cells.** Seed adherent cells; re-image the 5-well pattern under
  all three illumination modes (transmitted-above, oblique-below, epi). Record cell
  countability, confluence, morphology, and contrast per mode.

### The three gating numbers

| Gate | Metric | PASS threshold |
|---|---|---|
| **(a) Focus + real WD** | sharp focus through the wet stack AND WD_real (front element → cell plane) | **WD_real ≥ ~8.8 mm** so the front element sits at/below z = −8. 4× (~22 mm) passes hugely; **10× (~8 mm) is the marginal/fail case — record explicitly.** |
| **(b) Contrast** | Michelson `C = (I_max − I_min)/(I_max + I_min)` on a grid line / cell edge (raw frames) + cell-count agreement | **grid C ≥ 0.15 AND two manual counts agree ±10 %** in at least one illumination mode. 0.08–0.15 = marginal (computational only); < 0.08 = illumination must change. |
| **(c) Field flatness / tilt** | intra-well edge defocus `ΔZ_field` and well-to-well `ΔZ_tilt` vs DOF | **ΔZ_field ≤ DOF AND ΔZ_tilt ≤ DOF** (4× DOF ±55 µm → generous). ΔZ_tilt > DOF → per-well autofocus (confirm ≤ 12 mm stroke). ΔZ_field > DOF → field not flat, tile + refocus or drop mag. |

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
| Front-end half-extent overhanging the well aperture in X / Y | **`dry_bay.observer_sweep_extra_x` (16.1), `observer_sweep_extra_y` (12.2)** | **headline deliverable** — replace the hand-tuned fudge with the measured per-axis overhang |
| Vertical extent (objective parfocal + fold mirror) `FE_z` | `front_end_height_z` (28.0) | set = measured; closes budget iff `8 + FE_z + focus_stroke + margin ≤ 62` |
| `WD_real` | consistency check on `carriage_top_clearance_z` (8.0) | if WD_real forces the element above z = −8, the 8 mm clearance is invalid and the bay must deepen |
| `ΔZ_tilt` | `front_end_focus_stroke_z` (12.0) | confirm `ΔZ_tilt + DOF margin ≤ 12.0` |

**Z-closure go/no-go arithmetic:**

```
Required vertical = carriage_top_clearance_z (8)
                  + FE_z (objective parfocal + fold)
                  + focus_stroke (ΔZ_tilt)
                  + service margin
CLOSES iff Required vertical ≤ 62 mm (carriage_height_z), front element ≤ z = −8,
          barrel Ø ≤ 32 mm (objective_keepout_diameter).
```

Expected: FE_z ~60 mm straight-down closes with ~2 mm spare because the tube lens
and camera are routed horizontally. The bench must confirm ~60 with calipers, not
trust the estimate.

**Strengthen the swept-body test.** The current
`_observer_front_end_swept_body_check` (`src/aevum_cad/row_coupon.py`) builds the
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
the carriage across the row (body sweeps the long axis, head scans the short axis),
surfaces the **44.6 mm dry-bay Y overflow** as data, runs deck-foot / adjacent-slot
overlap (both 0 today — the overflow lands in unmodeled end-margin space), and adds
the `carriage_traverse_exceeds_dry_bay` Gate-6 blocker. This is geometric evidence,
not a proven motion plan; it stays Gate-6 blocked until the physical gantry is built.

## Decision tree

```
Phase A resolves to optical spec (dry, no plate)?
  NO  → rig misaligned; fix. NOT an architecture verdict.
  YES ↓
Q1 FOCUS through wet stack, WD_real ≥ ~8.8 mm (element ≤ z = −8)?
  NO at chosen mag / YES at lower mag → DROP MAG (4× is the safe default; 10× WD too short).
  NO at all mags                      → Z/GEOMETRY FAILS → DEEPEN BAY (eat the 80 mm Raman budget) or change optical class.
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
Q4 Z-CLOSURE: 8 + FE_z + focus_stroke + margin ≤ 62, element ≤ z = −8, barrel Ø ≤ 32?
  YES → COMPACT FRONT-END VIABLE → write measured front_end_* + observer_sweep_extra_x/y, retire 16.1/12.2, strengthen Gate 6.
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
mono, oblique-from-below illumination → focuses with ~22 mm WD margin, DOF ±55 µm
swallows plate tilt, straight-down ~60 mm closes the 62 mm budget, barrel Ø ≤ 25 <
32 keepout → compact moving front-end viable, sealed top preserved, the 16.1/12.2
fudge replaced by a measured overhang. The bench exists to confirm or break that
chain with calipers and real images.

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

## What Stage 0 does not prove (scope lock → Stages 1–4)

This static rig says **nothing** about the moving system. It deliberately omits
motion and the OT-2. It cannot tell you the moving carriage's settling time,
resonance, servo jitter, or motion-induced defocus — those are properties of the
motion system and its structural loop, tested on the actual stage in later stages.

The one number Stage 0 hands the motion designer is the **vibration spec**: the
moving carriage must be held still, at exposure, inside the measured depth of field
(≈ ±27 µm at 4×, ≈ ±4 µm at 10×). That becomes the acceptance threshold for
Stage 1's focus axis and Stage 2/3's scan.

The carriage-traversal gap — today the 62 mm-tall carriage is modeled only at the
plate-1 end of the row while the front-end must reach all four plates across
334.5 mm of Y — is **not** resolved by Stage 0. It is resolved physically at Stage 3,
where the real gantry either fits and traverses the full bay between the deck feet
within 80 mm, or forces a front-end/carriage decoupling redesign. Stage 0 exists to
make sure the optical head that gantry must carry is small enough and reaches focus
in the first place — so that Stage 3 is a motion problem, not also an optics
problem.
