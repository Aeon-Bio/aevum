# SMIS Kinematic-Dock Lateral Re-Seat Repeatability — Stage B

## Purpose

This protocol closes the dock-repeatability evidence loop: whether the SMIS
kinematic dock, once docked, undocked, and redocked, **re-seats the head within
≤ 5 µm laterally** at the imaging plane. The dock is the mechanical contract
between the gantry Z-carriage and a swappable head — a quasi-kinematic 3-2-1 seat
(cone + vee + flat = 6 contacts = 6 DOF), magnet preload, and an anti-rotation
dowel (`docs/engineering/sensor_module_interface.md`, Mechanical dock section).
`src/aevum_smis/dock.py` (`validate_dock`) already gates the **geometry and
statics** of that contract — the canonical 3-2-1 multiset, the 5.0× magnet pull
margin against the 1 g-scan demand, the Ø32 keepout clearance, the dowel. What it
cannot gate, and deliberately does not, is the **physical re-seat scatter**: the
docstring and `decision_log.md` (2026-06-14 three-magnets entry) both record the
`≤ 5 µm` figure as a Stage-B physical measurement carried only as a *target, never
gated*. This procedure is that Stage-B measurement. It converts the
reserved-and-unproven claim into a falsifiable, gated number.

It proves **one physical fact: the coupling re-seats within ≤ 5 µm lateral over
repeated dock-undock-redock cycles.** It does **not** prove imaging quality, focus,
resolution, contrast, motion settling, servo jitter, carriage traverse, or full-row
scanning — those are the optical bench (`observer_optical_bench_stage0.md`) and the
Stage 1–4 motion properties of the actual gantry. It does **not** re-prove the
geometry or statics already gated in `src/aevum_smis/dock.py`
(`tests/test_smis_dock.py`): the 3-2-1 seat, the 3-magnet 5.0× margin, and the
keepout clearance are code-gated facts, not re-litigated here. CAD/spec geometry is
**not** physical evidence; the ball-on-cone/vee/flat layout, the magnet count, and
the dowel are the *device under test*, not its proof. Only the measured re-seat
scatter on a real imaged target is evidence.

## Authority

This protocol **measures and records; it creates no motion authority.** Nothing
here issues a move, energizes a source, or unblocks acquisition. An adapter,
translator, or scaffold MUST NOT create motion authority — and neither does a
measurement protocol.

The dock-repeatability **outcome feeds the existing fail-closed registration
gates; it does not become a gate.** A head whose measured re-seat scatter does
**not** clear ≤ 5 µm cannot trust the coupling to preserve its optical-axis
registration across a swap, so its manifest sets
`requires_post_dock_autofocus: true` (`src/aevum_smis/manifest.py`). That flag
escalates the post-dock registration ritual from Tier A (coupling trust + one
fiducial touch-up) to Tier B (re-fiducial with three fiducials + autofocus map) in
`required_registration_ritual` / `validate_registration_result`
(`src/aevum_smis/registration.py`; `decision_log.md`, 2026-06-15 head-swap
registration entry). The number does not flip a pass/fail in `validate_dock` — the
`≤ 5 µm` target is **never** a dock gate. It chooses how paranoid the registration
ritual must be. A head that re-seats tightly earns the cheap Tier-A ritual; a head
that scatters pays for it with the more expensive ritual, every dock.

## Measurement Record

Create the run record under:

```text
data/measurements/YYYY-MM-DD_observer_kinematic_dock_repeatability.md
```

Use `data/measurements/templates/observer_kinematic_dock_repeatability.md` as the
starting record. Keep every row `not_measured` until it has measured image
evidence — the printed-dock geometry and the magnet/dowel BOM are the device under
test, not closure.

Record at minimum:

| Item | Tool | Pass condition |
|---|---|---|
| (a) Per-cycle lateral re-seat offset `(Δx_i, Δy_i)` | USAF target image + sub-pixel registration | each of 20 redock frames registered against the seated reference; per-cycle radial offset `r_i = √(Δx_i² + Δy_i²)` recorded |
| (b) Scatter statistic `r_95` / `r_max` | arithmetic on the 20 cycles | **`r_95 ≤ 5 µm` (the target) AND `r_max` recorded** — the 95th-percentile radial re-seat offset is the headline number; the single worst cycle is recorded, never hidden |
| (c) Pixel-scale calibration `µm/px` | stage micrometer or known USAF pitch | the px→µm scale that converts (a) to microns is measured on *this* rig, not assumed from the objective spec |
| (d) Drift control | reference re-image without undock | a no-undock re-image bounds thermal/illumination/registration noise; `r_drift` must be ≪ the redock scatter or the redock number is uninterpretable |
| (e) Seat audit per cycle | visual + listen for the magnet seat | each cycle confirmed fully seated (cone + vee + flat contact, magnets pulled home, dowel engaged) — a partial seat is a void cycle, not a fail, and is re-run |
| Cycle count | tally | **≥ 20** complete dock-undock-redock cycles (fewer is not a distribution) |

## Setup

1. Print the dock per the SMIS dock spec geometry in `src/aevum_smis/dock.py`
   (`DockSpec` defaults): the **3 balls** (Ø6 grade-25 chrome) on the head plate
   and the matching **cone + vee + flat** seats on the bench cradle (the 3-2-1
   seat), the **3× N52 pot magnets** preload, and the **anti-rotation dowel**. The
   ball circle is Ø44 so the contact circle (~Ø38) clears the Ø32 objective
   keepout. **This geometry is the device under test, not evidence** — that it
   matches the spec is gated by `tests/test_smis_dock.py`, not by this protocol.
2. Mount the cradle half of the dock rigidly to the **optical-bench breadboard**
   (`observer_optical_bench_stage0.md`, Setup) so the dock and the imaging head
   share one mechanical ground. Let the rig settle ~15 min after handling; do not
   hold the posts during a cycle (hand heat is the µm-scale enemy).
3. Mount a **USAF 1951 resolution target** (or a high-contrast fiducial grid) on
   the head-plate half of the dock so it images through the bench optics. The
   target rides the head; the camera is fixed to the cradle ground. A lateral
   re-seat error appears as an in-plane image shift of the target between docks.
4. Bring the target into focus once, then **do not touch focus or XY for the rest
   of the run.** Any focus/XY adjustment between cycles destroys the re-seat
   measurement — the whole point is that the *dock alone* repositions.
5. Capture the **seated reference frame**: dock, confirm full seat (item (e)),
   image. This frame is the datum all 20 redock frames register against.

## Procedure

### (c) Calibrate the pixel scale first

1. Before any cycle, measure `µm/px` on this exact rig: image a stage micrometer or
   resolve a known USAF element pitch and compute microns per pixel. Sub-pixel
   registration in pixels is meaningless until this scale is pinned. Record it; it
   converts every (a) offset to microns.

### (d) Bound the drift floor

1. With the head docked and **not** undocked, re-image the target several times over
   the same wall-clock span the 20 cycles will take. Register each against the
   reference and record the radial spread `r_drift`. This is the thermal /
   illumination / registration-algorithm noise floor.
2. **`r_drift` must be ≪ the redock scatter** (rule of thumb: ≤ ~1 µm, well under
   the 5 µm target). If `r_drift` is comparable to the redock numbers, the rig — not
   the dock — sets the scatter and the redock result is uninterpretable. Fix the rig
   (settle longer, stabilize illumination, improve the registration target) before
   proceeding. A miss here is a rig problem, not a dock verdict.

### (a)–(b) Run the 20 dock-undock-redock cycles

1. For each cycle `i = 1..20`:
   a. **Undock:** release the magnet preload, lift the head clear of all three
      seats and the dowel. Fully separate — a partial lift does not exercise the
      re-seat.
   b. **Redock:** lower the head back onto the cone + vee + flat, let the magnets
      pull it home, confirm the dowel engages. **Audit the seat (item (e)):** all
      three contacts seated, magnets home, dowel engaged. A partial/false seat is a
      **void cycle** — discard and re-run it; it is not a fail.
   c. **Image:** capture one frame at the locked focus/XY.
   d. **Register:** sub-pixel-register the frame against the seated reference;
      record `(Δx_i, Δy_i)` in pixels, convert to microns via (c), and record the
      radial offset `r_i = √(Δx_i² + Δy_i²)`.
2. After 20 valid cycles, compute the scatter statistic: the **95th-percentile
   radial offset `r_95`** (headline) and the **worst single cycle `r_max`**
   (recorded explicitly, never hidden). Optionally record the per-axis std to see
   whether scatter is isotropic or biased along the vee/flat axis.

## Outcomes / Decision Tree

The measured `r_95` decides the **registration ritual** for this head class — not a
dock pass/fail.

- **`r_95 ≤ 5 µm` → the coupling re-seats within target.** The head class may keep
  `requires_post_dock_autofocus: false` in its manifest: the cheap Tier-A ritual
  (coupling trust + one fiducial touch-up) is justified for routine head swaps. The
  reserved-and-unproven `≤ 5 µm` claim in `src/aevum_smis/dock.py` /
  `sensor_module_interface.md` is now backed by physical evidence for this build.
- **5 µm < `r_95` (re-seat scatter exceeds target) → the coupling is not trusted to
  preserve registration.** Set `requires_post_dock_autofocus: true` for this head
  class. `required_registration_ritual` then raises the minimum ritual to **Tier B**
  (three fiducials + autofocus map) on every dock — the head pays the registration
  cost its loose re-seat demands. This is the designed feedback: the measurement
  feeds the gate; it does **not** loosen the `≤ 5 µm` figure or touch
  `validate_dock`.
- **`r_drift` not ≪ redock scatter → result void.** The rig sets the floor; the dock
  number is uninterpretable. Fix the rig and re-run; do **not** record a dock verdict
  from a drift-limited run.
- **Bimodal / outlier scatter (most cycles tight, a few large) → seat reliability
  problem, not a tolerance problem.** Audit for intermittent partial seats, debris on
  a ball/seat, or a dowel that occasionally fails to engage. The fix is mechanical
  (seat cleanliness, magnet alignment, dowel fit), not a registration-tier change.
  Re-run after the fix; a re-seat that *sometimes* fails is a worse failure mode than
  one that consistently scatters, because Tier B assumes a *consistent* registration
  burden.

## What this gates

Passing this protocol (`r_95 ≤ 5 µm`) supplies the physical evidence behind the
`repeatability_target_um = 5.0` figure that `src/aevum_smis/dock.py` carries as a
*target, never gated*, and justifies leaving `requires_post_dock_autofocus: false`
so the head earns the cheap Tier-A post-dock ritual
(`src/aevum_smis/registration.py`). Failing it does **not** block the dock — the
3-2-1 seat, the 3-magnet 5.0× margin, the keepout clearance, and the dowel remain
the only dock gates (`tests/test_smis_dock.py`) — it instead **escalates the
registration ritual** to Tier B by setting `requires_post_dock_autofocus: true`.
The measurement creates **no** motion authority; it informs the fail-closed
registration gate and nothing else.

It does **not** retire any imaging, focus, contrast, or motion evidence
(`observer_optical_bench_stage0.md`, Stage 1–4), and it does **not** re-prove the
dock geometry/statics, which are CAD/spec inputs to this test, not its output. No
manifest flag is changed and no CAD parameter is touched unless this run record
identifies the measured `r_95`, the measured `µm/px` scale, and the bounded
`r_drift` floor that justify it.
