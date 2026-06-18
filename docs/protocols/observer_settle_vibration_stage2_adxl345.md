# Observer Settle-Time & Vibration — Stage 2 (ADXL345)

## Purpose

This protocol converts the observer module's most consequential motion *estimate*
into measured physical evidence: the **real first-mode frequency `f` and quality
factor `Q` of the structural focus loop, the post-move ring-down settle time to the
hold-still spec, and the OT-2 structure-borne idle vibration floor at the head.** It
is Stage 2 of the staged dry-bay build-out (`observation_module.md` §7) — the first
stage that has a moving carriage, so it is the first stage that *can* measure settle
at all. Everything upstream of it (`observer_optical_bench.md`, Stage 1 focus axis)
is static; settle, resonance, and OT-2 coupling are properties of the moving
structural loop and cannot be inferred from a static rig.

The hold-still acceptance threshold is inherited verbatim from the optical bench's
own measured depth of field (`observer_optical_bench.md` "What Stage 0 does not
prove"; `observation_module.md` "Verified bay geometry"): the moving carriage must
be held still, at exposure, inside **±27 µm at 4× and ±4 µm at 10×**. Those are the
two numbers this protocol gates against — not invented here, inherited from the
bench DOF.

**What this protocol proves:**

- the **real** first-mode `f` and `Q` of the all-aluminum focus loop, measured by
  ring-down, not estimated from a `~200 g head / cheap-belt-gantry → f ≈ 60 Hz,
  Q ≈ 30` arithmetic guess;
- the **measured** post-move settle time to ±27 µm (4×) and to ±4 µm (10×) after a
  representative 9 mm well-to-well step, with and without Klipper `input_shaper`;
- the **OT-2 structure-borne idle vibration floor** at the head — the displacement
  the head sees from a co-located, idle (powered, fans/electronics running) OT-2
  through the shared mechanical frame;
- whether the OT-2 *couples* during deck activity (a pipette puncture / gantry move)
  badly enough to violate the exposure-stillness spec.

**What this protocol explicitly does NOT prove (non-claims):**

- It says **nothing about imaging quality, resolution, or label-free contrast** —
  those are the optical bench's three gating numbers (`observer_optical_bench.md`),
  and the contrast fork (`observer_contrast_fork_ws2812.md`).
- It does **not prove focus or autofocus** — the Z axis and map-AF are Stage 1
  (`observation_module.md` §3); an ADXL345 measures structural motion, not optical
  defocus.
- It does **not close Gate 6** and authorizes **no** `cad/one_row_coupon.params.json`
  change. It is structural-vibration evidence, not a satisfied motion plan.
- It does **not prove the full-row 334.5 mm traverse** — that is Stage 3, the
  make-or-break geometry/stiffness proof of the 13 mm thin-truck over the whole row.
  Stage 2 measures settle on a **one-plate (≤99 mm X)** scan; the full-row beam may
  ring differently and must be re-measured at Stage 3.
- It does **not prove condensation rejection, drag-chain recovery, or thermal
  drift over a scan** — those are Stage-0 Phase C, Stage 4, and the thermal budget
  respectively.

The settle outcome is a **decision gate, not a bench curiosity**: per
`observation_module.md` §8, the measured ring-down decides **single thin-truck
gantry vs two-plate split** (open decision #1) and **strict OT-2 interlock vs
vibration-isolated concurrency** (open decision #3). A single 334.5 mm beam that
cannot hold ±27 µm even input-shaped forces the split; an OT-2 idle floor that is
not < 4 µm at the head kills concurrency and makes interlock mandatory. This
protocol produces the numbers those two decisions turn on.

> **CAD arithmetic is NOT physical evidence.** The `t ≈ (Q / πf)·ln(A0/A)` ms
> estimates in `observation_module.md` ("Settle forces stop-and-shoot": ~210 ms to
> ±27 µm at 4×, ~510 ms to ±4 µm at 10×) are an arithmetic placeholder built on a
> guessed `f ≈ 60 Hz, Q ≈ 30, A0 ≈ 100 µm`. They exist only to bound the scan-cycle
> table; they are not measurements and must not be cited as settle evidence. **Only
> the measured ring-down numbers recorded under this protocol are physical
> evidence.** The arithmetic and the measurement may disagree by a multiple — that
> disagreement is the entire reason to run this.

## Measurement Record

Create the run record under:

```text
data/measurements/YYYY-MM-DD_observer_settle_vibration_stage2_adxl345.md
```

Use `data/measurements/templates/observer_settle_vibration_stage2_adxl345.md` as
the starting record. Keep each phase `not_measured` until it has a captured
acceleration trace and a derived number with units. A settle time without the raw
ring-down trace behind it is not evidence.

Record at minimum:

| Item | Tool | Pass condition |
|---|---|---|
| (a) First-mode `f` | ADXL345 on the head, FFT of ring-down | dominant structural-loop peak (Hz); compare to the ~60 Hz estimate but do not assume it |
| (b) Quality factor `Q` | log-decrement on the ring-down envelope | `Q = π / ln(A_n / A_{n+1})` per cycle, or half-power bandwidth from the FFT |
| (c) Settle to ±27 µm (4×) | displacement (double-integrated / fit) vs time after a 9 mm step | `t_settle,4×` = time for envelope to fall below ±27 µm |
| (d) Settle to ±4 µm (10×) | same | `t_settle,10×` = time to fall below ±4 µm |
| (e) Input-shaped settle | same, with Klipper `input_shaper` on | `t_settle` with shaper ≤ unshaped; record the shaper type + freq |
| (f) OT-2 idle floor at head | ADXL345, OT-2 powered + idle, observer parked | RMS / peak displacement at the head over a quiet window |
| (g) OT-2 active coupling | ADXL345, during an OT-2 deck move / pipette puncture | peak head displacement during the disturbance |
| (h) Z-axis settle (objective + fold block) | ADXL345 on the Z block after a focus step | the low-mass Z loop settles faster than X/Y — confirm |

## Setup

This protocol assumes Stage 1 (`observation_module.md` §7) has produced a focus Z
axis and that a one-plate XY scan exists to drive representative 9 mm well-to-well
steps. Do not run settle measurement on a rig that cannot reproduce a real indexing
move — a hand-pushed step does not exercise the closed-loop stepper deceleration
profile that produces the real post-move sway.

1. **ADXL345 on the moving head, in the focus loop.** Bond a ¥20 ADXL345 to the
   front-end body **at the optical head**, as close as physically possible to the
   objective + fold block — the sensor must witness the *cell-plane structural loop*
   (objective → fold → Z-stage → X-beam → Y-truck → sub-frame → plate-support frame),
   not a slab elsewhere on the gantry. Mount rigidly (screw or cyanoacrylate to an
   aluminum face); no foam tape between the accelerometer and the loop it is
   measuring, or it filters out the very motion under test. Orient one axis along X
   (scan), one along Y (traverse), one along Z (focus) and record the orientation.
2. **All-aluminum focus loop — no PLA in the path.** Per `observation_module.md`
   ("Mounting into the bay"), the loop under test must be the production-intent
   all-aluminum loop (PLA CTE is ~3× aluminum → ~4 µm/°C drift that eats the whole
   10× budget). If the Stage-2 rig still has PLA in the structural loop, record that
   as a caveat — it changes both stiffness and thermal behavior and the numbers do
   not transfer to the aluminum production loop.
3. **Klipper host capture.** Drive the motion MCU from a Klipper host so the
   ADXL345 is read through Klipper's `ACCELEROMETER_QUERY` / `MEASURE_AXES_NOISE` /
   resonance-test path (the same `input_shaper` calibration flow). This gives raw
   acceleration traces and FFTs from the part the design already names for shaping
   (`observation_module.md`: "feeds Klipper `input_shaper` (free, halves residual)").
   Capture **raw traces**, not just Klipper's auto-recommended shaper — the trace is
   the evidence.
4. **OT-2 co-located for the coupling phase.** For phases (f)/(g), the observer rig
   must share the real mechanical frame with the OT-2 across the thin plate — the
   same shared-frame condition that motivates the strict-interlock stance
   (`observation_module.md` §5, driver #5). Mount the row module / observer cartridge
   on the deck as it would install, power the OT-2, and capture the head's ADXL345
   while the OT-2 is (f) idle and (g) executing a representative deck move / pipette
   puncture. A bench rig that is *not* co-located with the OT-2 can measure (a)–(e)
   but **cannot** measure (f)/(g); mark those `not_measured` in that case.
5. **Settle before capture.** Let the rig thermally settle after handling; do not
   hand-hold the structure during a capture (hand contact adds damping and mass that
   is not in the production loop).

## Procedure — phased, gated

Run the phases **in this exact order; each is a gate — do not proceed if the prior
fails to produce a clean trace.** Establish the noise floor and the natural mode
*before* asking about settle, and isolate the observer's own settle *before*
introducing the OT-2 — so that if the coupled number is bad you already know whether
it is the observer's structure (Phase 1–3) or the OT-2 coupling (Phase 4).

- **Phase 1 — noise floor (observer idle, OT-2 absent/off).** With the observer
  powered but not moving and motors at holding state, capture a quiet window. Record
  the ADXL345 RMS noise floor (`MEASURE_AXES_NOISE`). **Gate:** the floor must be
  well below the ±4 µm 10× spec, or the sensor/mount cannot resolve the settle
  target — fix the mount before proceeding.
- **Phase 2 — natural mode (`f`, `Q`).** Excite the parked head with a single tap /
  step impulse (or a Klipper resonance sweep) and capture the free ring-down. FFT
  for the dominant first-mode peak `f`; log-decrement the envelope for `Q`. **Gate:**
  a single dominant structural peak must be identifiable (record secondary modes).
  Compare to the `f ≈ 60 Hz, Q ≈ 30` estimate but report the measured values — the
  estimate is not the answer.
- **Phase 3 — post-move settle (the headline).** Command a representative **9 mm
  well-to-well step** on the X scan axis (the real indexing move) and capture the
  post-move ring-down. Derive the displacement envelope and read `t_settle,4×`
  (envelope < ±27 µm) and `t_settle,10×` (envelope < ±4 µm). Repeat **with Klipper
  `input_shaper` enabled** and record the shaped settle times and the shaper
  type/frequency. Also capture the **Z-axis** focus-step settle (item h) — the
  low-mass objective+fold block should settle fastest.
- **Phase 4 — OT-2 coupling (co-located).** With the OT-2 co-located on the shared
  frame: (f) capture the head's idle floor while the OT-2 is **powered and idle**;
  (g) capture the head during a representative OT-2 **deck move / pipette puncture**.
  Read peak head displacement for each. **Gate the concurrency question here:** if
  (f) the *idle* floor already exceeds ±4 µm at the head, concurrency is dead before
  any active disturbance is even considered.

## Gating Numbers (falsifiable)

| Gate | Metric | PASS threshold |
|---|---|---|
| **(1) Settle to 4× spec** | measured `t_settle,4×` after a 9 mm step (shaped) | settle to **±27 µm** inside the scan-cycle settle budget (`observation_module.md` §3 budgets ~0.20 s; the arithmetic estimate is ~210 ms — **the measured number is the truth**). PASS if a single thin-truck beam reaches ±27 µm in a time that keeps the per-well cycle inside the live-cell time-lapse cadence. |
| **(2) Settle to 10× spec** | measured `t_settle,10×` after a 9 mm step (shaped) | settle to **±4 µm** (the 10× DOF). Marginal/failing 10× settle is the documented escalation, not a hard stop — 4× remains the safe default (`observation_module.md` §8 decision #2). Record explicitly. |
| **(3) OT-2 idle floor** | measured RMS/peak head displacement, OT-2 powered + idle | **< ±4 µm at the head** for concurrency to be even possible. ≥ ±4 µm → concurrency is dead → strict time-sliced interlock is mandatory (`observation_module.md` driver #5, decision #3). |
| **(4) First-mode sanity** | measured `f`, `Q` | `f` and `Q` recorded with the ring-down trace behind them; gross disagreement with the ~60 Hz / Q≈30 estimate (e.g. `f` < ~25 Hz, a soft loop) is itself a finding that re-opens the stiffness/gantry choice. |

A single failing gate does not invalidate the others — each gate maps to a distinct
downstream decision (single-beam vs split; 4×-only vs 10×; interlock vs
concurrency). Record each independently.

## Decision Tree

Read the gantry/concurrency verdict from the measured settle numbers. Establish the
mode (Phase 2) and the observer's own settle (Phase 3) before reading the coupled
result (Phase 4).

```
Phase 1 noise floor << ±4 µm at the head?
  NO  → sensor/mount cannot resolve the target; re-mount the ADXL345 rigid + close
        to the loop. NOT a settle verdict.
  YES ↓
Q1 SINGLE-BEAM SETTLE: shaped t_settle,4× ≤ the scan-cycle settle budget at ±27 µm?
  YES → SINGLE THIN-TRUCK GANTRY VIABLE for 4× → keep the single-beam default
        (observation_module.md §8 decision #1).
  NO, even input-shaped → single 334.5 mm beam cannot hold still →
        ESCALATE TO TWO-PLATE SPLIT (two 167 mm beams, √2 stiffer, ~2× optics cost).
        This is the reserved stiffness escape, now triggered by data.
  ↓
Q2 10× SETTLE: shaped t_settle,10× reaches ±4 µm in budget?
  YES → 10× drill-down stays in the production path (commit the VCM precision).
  NO  → 10× settle too slow → 4×-ONLY is the safe path (±55 µm DOF is forgiving);
        keep 10× as a sparse QC-flagged escalation only, accepting longer dwell.
  ↓
Q3 OT-2 IDLE FLOOR: head idle-floor displacement < ±4 µm with the OT-2 powered+idle?
  YES, and active coupling (Phase 4g) is bounded under isolation →
        VIBRATION-ISOLATED CONCURRENCY is *possible* (pursue only if a real protocol
        timeline demands it AND sorbothane isolation supports it).
  NO  → idle floor ≥ ±4 µm → CONCURRENCY IS DEAD → STRICT TIME-SLICED INTERLOCK is
        mandatory (the safe default regardless). The two robots image one-at-a-time.
  ↓
Q4 FIRST-MODE: is measured f/Q grossly softer than the f≈60 Hz / Q≈30 estimate?
  YES → the structural loop is softer than designed → re-open stiffness (shorter
        beam, stiffer rail tier, head mass reduction) before trusting any cycle time.
  NO  → the arithmetic bound was reasonable; the measured settle still governs.
```

**Expected (not assumed) path:** a ~200 g head on a steel-core GT2 belt + preloaded
MGN/HGH rail, all-aluminum loop, with Klipper input-shaping halving the residual,
settles to ±27 µm fast enough for a single thin-truck beam at 4×, and the OT-2 idle
floor lands below ±4 µm so interlock (not concurrency) is the chosen default for
safety even where concurrency is technically possible. The protocol exists to
confirm or break that chain with measured ring-down — the move-settle-strobe trick
(`observation_module.md`: stop → settle → short LED flash) relaxes a stiffness
requirement into a timing requirement only if the measured settle time actually
fits the budget.

## Pass/Fail Boundary

The **single thin-truck gantry** is retained (split held in reserve) only if:

- shaped `t_settle,4×` reaches **±27 µm** within the scan-cycle settle budget on a
  single 334.5 mm-class beam, with the ring-down trace behind the number; and
- the measured first-mode `f`/`Q` is not grossly softer than the design estimate
  (no surprise sub-25 Hz loop mode swamping the budget).

The **two-plate split is triggered** when:

- even with Klipper `input_shaper` enabled, the single beam cannot reach ±27 µm
  inside the settle budget after a 9 mm step.

**Concurrency** with the OT-2 is permitted to be *considered* only if:

- the OT-2 **idle floor at the head is < ±4 µm** (Phase 4f), and the active-coupling
  disturbance (Phase 4g) is bounded under sorbothane isolation.

Otherwise **strict time-sliced interlock is mandatory** — and it remains the safe
default even when concurrency is technically possible.

**10×-in-path** is retained only if shaped `t_settle,10×` reaches **±4 µm** in
budget; otherwise 4×-only is the path and 10× is a sparse QC-flagged escalation.

Passing this protocol produces the measured `f`, `Q`, settle times, and OT-2 floor,
and authorizes the corresponding `decision_log.md` entries (single-beam-confirmed /
split-triggered; 4×-only / 10×-retained; interlock-mandatory / concurrency-possible).
It does **not** satisfy Gate 6, authorize the moving carriage as a closed motion
plan, prove the full-row 334.5 mm traverse (Stage 3), or authorize any
`cad/one_row_coupon.params.json` change. CAD arithmetic remains an estimate; only the
ring-down numbers recorded here are physical evidence.

## What this gates

Passing this protocol retires the **settle/vibration estimate** in
`observation_module.md` (§2 "Settle forces stop-and-shoot", §3 scan-cycle table)
and converts drivers **#3 (settle forcing stop-and-shoot)** and **#5 (OT-2
structure-borne vibration)** from arithmetic into measurement (§6 driver table). It
is the **decision gate** for two of the three top open decisions
(`observation_module.md` §8):

- **#1 — single thin-truck gantry vs two-plate split** turns on the measured
  single-beam settle to ±27 µm;
- **#3 — strict OT-2 interlock vs vibration-isolated concurrency** turns on the
  measured OT-2 idle floor at the head.

It does **not** retire the contrast/condensation killers (Stage 0,
`observer_contrast_fork_ws2812.md`, `observer_optical_bench.md`), the focus/AF axis
(Stage 1), the full-row traverse geometry (Stage 3, `observer_carriage_traverse`),
or any Gate-6 imaging evidence. **No motion or emission authority is created by this
protocol** — the ADXL345 only senses; the observer's authority to move remains
granted by the OT-2 bridge lease and hardware-gated by the enable line
(`observation_module.md` §5).

## Cross-references

- Settle physics, the `f ≈ 60 Hz / Q ≈ 30` arithmetic estimate, the move-settle-
  strobe trick, the driver table, and the top open decisions this protocol gates:
  `docs/engineering/observation_module.md` (§2 "Settle forces stop-and-shoot", §3,
  §6 drivers #3/#5, §7 Stage 2, §8 decisions #1/#3)
- The ±27 µm / ±4 µm hold-still vibration budget and the DOF it derives from
  (±55 µm @ 4× / ±4 µm @ 10×): `docs/engineering/observer_optical_bench.md`
  ("What Stage 0 does not prove")
- The verified bay geometry the moving loop is built against, and the all-aluminum
  focus-loop / 1.4 µm/°C thermal constraint: `docs/engineering/observation_module.md`
  ("Verified bay geometry", "Mounting into the bay")
- The shared-frame OT-2 interlock and the lease/enable-line authority boundary this
  protocol must not violate: `docs/engineering/observation_module.md` §5
- Stage 0 contrast and the optical gating numbers this protocol explicitly does NOT
  reprove: `docs/protocols/observer_contrast_fork_ws2812.md`,
  `docs/engineering/observer_optical_bench.md`
- Run record template: `data/measurements/templates/observer_settle_vibration_stage2_adxl345.md`
