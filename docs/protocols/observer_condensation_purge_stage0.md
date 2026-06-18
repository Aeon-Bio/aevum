# Observer Condensation Purge & Lip-Heat — Stage 0 Validation

## Purpose

This protocol closes the wet-boundary evidence loop that `observer_optical_bench.md`
Phase C and `observer_contrast_fork_ws2812.md` both defer: whether a production purge
flow and a plate-lip heat setpoint can hold the imaged plate underside above the
headspace dew point by the reserved margin, through a real imaging dwell, with warm
37 °C media driving the thermal gradient. It MEASURES the two numbers the software
condensation gate reserves but cannot yet evidence — the purge flow rate
(`purge_flow_ml_min`) and the lip-heat command (`lip_heat_pwm`) that keep
`T_underside(MLX90614) > DewPoint(SHT41) + target_margin_c`. It converts the
placeholder setpoints reserved (and explicitly NOT yet evidenced) in
`src/aevum_smis/condensation.py` into bench-measured flow/heat values.

It does not prove the optical claim, the illumination fork, or any moving-system
property. It says nothing about resolution, field flatness, the 62 mm Z-fit, the
moving carriage, or full-row traversal — those remain owned by
`observer_optical_bench.md` (Phases A–D) and the motion stages. Gate 6 stays blocked
until the physical gantry is built. This protocol produces exactly the purge/lip-heat
operating point and the measured dwell margin that justify retiring the reserved
setpoints — nothing more.

State this plainly, in the house cadence: the CAD envelopes and this prose are NOT
physical evidence; only the measured purge flow, lip-heat command, and dwell margin
recorded against a dated run are. The software gate
(`evaluate_condensation_control`) is falsifiable today — it has negative tests and
fails closed — but the flow rate and lip-heat setpoint that satisfy it are NOT yet
evidence. This bench supplies that evidence.

## Authority

The purge/lip-heat actuator is a **monitored, fail-closed enable** that an
operator or host drives. This protocol grants **no implicit permission** to purge,
heat, or acquire. A protocol, an adapter, or a software scaffold MUST NOT create
motion or actuation authority; running this procedure authorizes nothing on its own.
Each purge step and each heat step is an operator action against a gate the software
only reports.

Acquisition stays **BLOCKED** whenever `evaluate_condensation_control` raises any of
its three blockers, regardless of how good the contrast looks:

1. `headspace_rh_at_condensation_limit` — `sht41_relative_humidity_pct >=
   max_safe_relative_humidity_pct` (default 98 %): the headspace is saturated and a
   margin reading is untrustworthy.
2. `plate_underside_below_dew_point` — the margin `mlx90614_underside_temp_c −
   DewPoint < 0`: the glass is already condensing.
3. `condensation_margin_below_target` — `0 ≤ margin < target_margin_c` (default
   2.0 °C): above dew point but inside the reserved guard band.

When all three clear, the gate returns `acquisition_allowed = True` and an `action`
of `hold` (margin ≥ 2.5 °C) or `increase_purge` (2.0 °C ≤ margin < 2.5 °C). The
`increase_purge_and_lip_heat` action exists in the enum but is **unreachable under
the default policy** — it would require margin < `lip_heat_warning_margin_c` (1.0 °C),
which always trips the `condensation_margin_below_target` blocker first, so it surfaces
only under a non-default override. The `increase_purge` warning action is advice to
the operator, not a grant: the operator drives the purge/heat, the software only states
whether the measured telemetry has cleared the blockers.

## Measurement Record

Create the run record under:

```text
data/measurements/YYYY-MM-DD_observer_condensation_purge_stage0.md
```

Use `data/measurements/templates/observer_condensation_purge_stage0.md` as the
starting record. Keep every row `not_tested` until each has measured SHT41/MLX90614
telemetry, a logged purge flow, and a logged lip-heat command — the software gate
running green on simulated or hand-entered telemetry is NOT closure; only sensor
readings from the warm-media dwell are.

Record at minimum:

| Item | Tool | Pass condition |
|---|---|---|
| Headspace air T + RH | SHT41 (sensor PCB, gas-path position) | `sht41_air_temp_c`, `sht41_relative_humidity_pct` logged through dwell |
| Plate underside T | MLX90614 (row-module IR, non-contact) | `mlx90614_underside_temp_c` logged through dwell |
| Dew point | `dew_point_celsius(air_T, RH)` on logged telemetry | computed per sample, not estimated |
| Condensation margin | arithmetic: `underside − DewPoint` | `margin ≥ target_margin_c` held for the full imaging dwell |
| Production purge flow | mass-flow meter / rotameter on the purge line | `purge_flow_ml_min` that sustains the margin recorded, not assumed |
| Lip-heat command | logged PWM / measured lip surface T | `lip_heat_pwm` that sustains the margin recorded, with no media boil/drift |
| Gate verdict per sample | `evaluate_condensation_control(telemetry, policy)` | `acquisition_allowed = True`, `blockers = ()` for the whole dwell |
| Haze onset / recovery | timed visual + raw-frame contrast | underside stays haze-free; if haze appears, time-to-onset and recovery flow logged |

## Setup

Build the bench per `observer_optical_bench.md` (the single source for the optical
train, the cradle, and the Taobao terms) and wire the sensor PCB and row-module IR
per `docs/engineering/sensor_pcb.md`. Do not re-list parts here.

1. Seat the CellVis P96-1.5H-N plate skirt-only in the leveled cradle, observation
   window open from below — nothing adhered, fastened, or labeled on the plate. All
   plate-side sensing is non-contact: the MLX90614 reads the underside from the
   row-module side, the SHT41 reads the headspace from its gas-path position.
2. Confirm Stage-0 Phase C focus survives the wet stack first. A condensation result
   on a rig that has not focused through warm media is uninterpretable; do not run
   this protocol on an unfocused bench.
3. Plumb the purge line to the imaged-well headspace through the mass-flow meter so
   `purge_flow_ml_min` is measured at the manifold, not read off a supply gauge.
   Wire the lip-heat element so `lip_heat_pwm` and the lip surface temperature are
   both logged. Confirm both are wired as a fail-closed enable the operator drives —
   default OFF, no autonomous actuation.
4. Bring `evaluate_condensation_control` online against the live SHT41/MLX90614
   stream so each phase reads its verdict from measured telemetry. The default
   `CondensationPolicy` (`target_margin_c` 2.0, `purge_warning_margin_c` 2.5,
   `lip_heat_warning_margin_c` 1.0, `max_safe_relative_humidity_pct` 98.0) is the
   starting policy; record any Stage-0 tuning override explicitly.
5. Pipette **warm (37 °C) media** into the imaged well with the dry bay at ambient,
   to force the real thermal gradient — the same warm-media condition Phase C and the
   contrast fork run under.

Run the four phases **in this exact order; each is a gate — do not proceed if the
prior fails.** The ordering isolates cause: a blocked acquisition tells you whether
the headspace is saturated (A), the glass is at/below dew point (B), the purge alone
is insufficient (C), or the dwell cannot be held without lip heat (D). Never debug
all four at once. Each phase reads its verdict from `evaluate_condensation_control`,
not from the eye.

## Phase A — Baseline, No Purge, No Heat

1. With warm media in the well and purge/heat OFF (`purge_flow_ml_min = 0`,
   `lip_heat_pwm = 0`), log SHT41 air T + RH and MLX90614 underside T for ≥2 min.
2. Compute `dew_point_celsius` and the margin per sample; run
   `evaluate_condensation_control` on each.
3. **Pass:** the baseline is characterized — the (expected) blocker is named
   explicitly. With no purge the headspace typically saturates toward
   `headspace_rh_at_condensation_limit` or the margin falls into
   `condensation_margin_below_target` / `plate_underside_below_dew_point`. Record
   which blocker fires and the margin trajectory; this is the worst-case the purge
   must overcome, not a failure of the rig.

## Phase B — Purge Sweep, No Lip Heat

1. With heat still OFF, step `purge_flow_ml_min` upward across the candidate range
   (operator-driven, fail-closed), holding each step ≥2 min.
2. Per step, log telemetry and the gate verdict. Find the lowest `purge_flow_ml_min`
   at which `evaluate_condensation_control` clears all three blockers
   (`acquisition_allowed = True`) and the `action` settles at `hold` (margin ≥
   `purge_warning_margin_c`).
3. **Pass:** a purge-only flow exists that holds `margin ≥ target_margin_c` with no
   blocker for ≥2 min. Record it as the candidate production purge flow. If no
   purge-only flow clears the blockers — RH stays at the limit, or the underside
   stays at/below dew point — purge alone is insufficient; proceed to Phase C with
   that recorded.

## Phase C — Purge + Lip Heat To Margin

1. Hold the Phase B candidate purge flow. Step `lip_heat_pwm` upward (operator-driven)
   until the underside margin reaches `target_margin_c` with headroom to
   `purge_warning_margin_c`, watching that lip heat does not boil/drift the media or
   warp the wet boundary.
2. Per step, log telemetry, lip surface T, and the gate verdict.
3. **Pass:** a (purge flow, `lip_heat_pwm`) operating point exists where
   `evaluate_condensation_control` returns `acquisition_allowed = True`, `blockers =
   ()`, and `action = hold`, with the media stable. Record both setpoints. If the
   margin cannot be reached without disturbing the media, the wet boundary is the
   blocker — escalate, do not relax the policy.

## Phase D — Real Imaging Dwell

1. At the Phase C operating point, hold a real imaging dwell of the intended
   acquisition duration (≥ the longest planned exposure/scan window for the imaged
   well).
2. Log SHT41/MLX90614 telemetry and the `evaluate_condensation_control` verdict
   continuously for the full dwell. Watch the plate underside for haze; record any
   onset, the margin at onset, and the recovery flow/heat.
3. **Pass:** the margin stays `≥ target_margin_c` and the gate returns
   `acquisition_allowed = True` with `blockers = ()` for the **entire** dwell, with no
   condensation haze. A single sample crossing into any blocker fails the dwell — the
   operating point does not hold and the setpoints are not yet evidence.

## The Gating Numbers

These are the falsifiable thresholds the bench exists to clear. Record each
explicitly — including the marginal/fail cases. The thresholds are exactly the
defaults in `CondensationPolicy`; a Stage-0 override must be logged.

1. **Condensation margin.** `margin = mlx90614_underside_temp_c −
   dew_point_celsius(sht41_air_temp_c, sht41_relative_humidity_pct) ≥
   target_margin_c` (default **2.0 °C**) for the full dwell. `margin < 0` →
   `plate_underside_below_dew_point` (BLOCKED); `0 ≤ margin < 2.0` →
   `condensation_margin_below_target` (BLOCKED). Margin in **2.0–2.5 °C** is the only
   advisory band reachable under the default policy: the gate clears all blockers
   (`acquisition_allowed = True`) and advises `increase_purge` — record it, but it is
   still **not a pass for the dwell**, which requires `margin ≥ purge_warning_margin_c`
   (2.5 °C) so the `action` settles at `hold`. The `increase_purge_and_lip_heat`
   advisory (margin < `lip_heat_warning_margin_c` = 1.0 °C) is **unreachable under the
   defaults** — any margin below 1.0 °C trips `condensation_margin_below_target` first
   and BLOCKS — so it appears only under a non-default override where
   `lip_heat_warning_margin_c > target_margin_c`.
2. **Headspace RH ceiling.** `sht41_relative_humidity_pct < max_safe_relative_
   humidity_pct` (default **98 %**) for the full dwell. At or above 98 % the gate
   raises `headspace_rh_at_condensation_limit` and the margin reading is not trusted —
   acquisition is BLOCKED even if the computed margin looks adequate.
3. **Production purge flow + lip-heat command.** The measured `purge_flow_ml_min` and
   `lip_heat_pwm` at the Phase C/D operating point. These are the numbers that retire
   the reserved placeholders. Record them as a pair with the dwell duration they held;
   a margin held by an unrecorded flow is not evidence.

## Decision Tree

Read the verdict from `evaluate_condensation_control` on the **measured dwell
telemetry**, not from the eye:

```
Phase D dwell: blockers == () AND margin ≥ target_margin_c for the WHOLE dwell?
  YES → PURGE/LIP-HEAT OPERATING POINT EVIDENCED.
        Record (purge_flow_ml_min, lip_heat_pwm) as the production setpoints.
        Retire the reserved placeholders in src/aevum_smis/condensation.py.
        → decision_log.md: record "condensation purge/lip-heat operating point evidenced".
  NO ↓
Margin held purge-only in Phase B (no lip heat needed)?
  YES → record the purge-only flow as the operating point; lip heat stays reserve.
  NO ↓
Margin held only with lip heat (Phase C), media stayed stable?
  YES → record (purge, lip_heat_pwm) pair; flag lip-heat as required, not optional.
  NO ↓
RH pinned at the ceiling (headspace_rh_at_condensation_limit won't clear)?
  → headspace exchange/seal is the blocker, not the cooler.
    → escalate to observation_module.md defogging/headspace scope; do NOT relax the 98 % ceiling.
  NO ↓
Underside stays at/below dew point, or margin cannot reach target without
disturbing the media?
  → ESCALATE: the wet boundary / lip-heat authority is insufficient.
    → decision_log.md: record the escalation; the reserved setpoints stay reserved.
```

## Pass/Fail Boundary

The purge/lip-heat operating point is evidenced — and the reserved setpoints may be
retired — only if **all** of these hold across the full Phase D dwell:

- `evaluate_condensation_control` returns `acquisition_allowed = True` and
  `blockers = ()` for every logged sample of the dwell;
- the measured `margin (underside − dew point) ≥ target_margin_c` (2.0 °C default)
  for the whole dwell, with no sample entering `condensation_margin_below_target` or
  `plate_underside_below_dew_point`;
- `sht41_relative_humidity_pct` stays below `max_safe_relative_humidity_pct` (98 %),
  so `headspace_rh_at_condensation_limit` never fires;
- the holding `purge_flow_ml_min` and `lip_heat_pwm` are **measured and recorded** as
  a pair with the dwell duration — a margin held by an unlogged flow is not evidence;
- the plate underside stays haze-free, or any haze onset is bounded, recovered, and
  dispositioned.

The setpoints stay **reserved** (NOT evidenced) and acquisition stays BLOCKED if any
of these occur:

- any dwell sample raises any of the three blockers
  (`headspace_rh_at_condensation_limit`, `plate_underside_below_dew_point`,
  `condensation_margin_below_target`);
- the margin can only be held by relaxing `target_margin_c` or the 98 % RH ceiling
  below the policy defaults — relaxing the policy is not a pass;
- lip heat that reaches the margin boils, drifts, or warps the warm media / wet
  boundary;
- the holding `purge_flow_ml_min` or `lip_heat_pwm` is not recorded — CAD/prose and a
  green gate on hand-entered telemetry are not physical evidence.

Passing this protocol only supplies the measured purge-flow and lip-heat setpoints
that retire the reserved placeholders in `src/aevum_smis/condensation.py`, and
authorizes the corresponding `decision_log.md` entry. It does **not** satisfy Gate 6,
authorize the moving carriage, prove imaging quality, the illumination fork, or
field flatness, and it grants **no** standing permission to purge, heat, or acquire —
each remains an operator action against the fail-closed gate. No setpoint is retired
unless the dated run record identifies the measured evidence and the specific
placeholder it pins.

## What This Gates

- **Retires:** the placeholder purge/lip-heat setpoints reserved (NOT yet evidenced)
  behind `evaluate_condensation_control` and `dew_point_celsius` in
  `src/aevum_smis/condensation.py` — specifically the `purge_flow_ml_min` and
  `lip_heat_pwm` operating point a `hold` verdict implies.
- **Confirms (does not change):** the software gate's three blockers and the
  `CondensationPolicy` thresholds (`target_margin_c` 2.0, `max_safe_relative_
  humidity_pct` 98.0) are already falsifiable and fail-closed; this bench evidences
  the actuator setpoints that satisfy them, it does not move the gate.
- **Does not gate:** any optical, illumination, motion, or Gate 6 imaging-performance
  claim — those stay owned by `observer_optical_bench.md` and the motion stages, and
  remain blocked until the physical gantry exists.
