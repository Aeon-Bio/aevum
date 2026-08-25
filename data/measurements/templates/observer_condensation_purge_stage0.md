# Observer Condensation Purge & Lip-Heat — Stage 0

Protocol:
`docs/protocols/observer_condensation_purge_stage0.md`

> Reserved setpoints (source of comparison, NOT evidence): the production
> `purge_flow_ml_min` and `lip_heat_pwm` that satisfy `evaluate_condensation_control`
> are reserved but NOT yet evidenced in `src/aevum_smis/condensation.py`. Policy
> defaults: `target_margin_c` 2.0, `purge_warning_margin_c` 2.5,
> `lip_heat_warning_margin_c` 1.0, `max_safe_relative_humidity_pct` 98.0. A green gate
> on hand-entered telemetry is NOT closure; only the warm-media dwell readings are.
> The purge/lip-heat actuator is a monitored fail-closed enable the operator drives;
> this record grants no permission to purge, heat, or acquire.

## Session Identity

| Field | Value |
|---|---|
| Date |  |
| Operator |  |
| Bench build identifier |  |
| SHT41 sensor-PCB position identifier |  |
| MLX90614 (row-module IR) identifier |  |
| Purge line + mass-flow meter identifier |  |
| Lip-heat element identifier |  |
| Plate identifier (CellVis P96-1.5H-N) |  |
| Media + temperature at addition |  |
| Stage-0 Phase C focus record (wet-focus pre-req) |  |
| Measurement images / telemetry log folder |  |

## Pre-Run Checks

| Check | Result | Evidence / notes |
|---|---|---|
| Phase C wet-focus passed (focus survives warm-media stack) | not_tested | reference `observer_optical_bench.md` run record |
| Plate seated skirt-only, nothing adhered / labeled on plate | not_tested |  |
| MLX90614 reads underside non-contact, SHT41 reads headspace | not_tested |  |
| Purge metered at manifold (not supply gauge) | not_tested |  |
| Purge + lip-heat wired fail-closed, default OFF, operator-driven | not_tested |  |
| `evaluate_condensation_control` online against live telemetry | not_tested |  |
| Policy in use (defaults or Stage-0 override) recorded | not_tested | target_margin_c / max_safe_relative_humidity_pct |
| Warm 37 C media in imaged well, dry bay at ambient | not_tested |  |

## Phase A - Baseline, No Purge, No Heat

| Measurement | Value / observation | Result | Notes |
|---|---|---|---|
| `sht41_air_temp_c` |  | not_tested | purge OFF, heat OFF |
| `sht41_relative_humidity_pct` |  | not_tested |  |
| `mlx90614_underside_temp_c` |  | not_tested |  |
| DewPoint = `dew_point_celsius(air_T, RH)` |  | not_tested |  |
| Margin (underside - DewPoint) |  | not_tested |  |
| Gate blocker(s) fired |  | not_tested | expected: rh_at_limit / below_dew_point / margin_below_target |
| Worst-case margin trajectory characterized |  | not_tested | baseline the purge must overcome |

## Phase B - Purge Sweep, No Lip Heat

| `purge_flow_ml_min` | Air T | RH | Underside T | DewPoint | Margin | `action` | `blockers` | Result | Notes |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  | not_tested | step >= 2 min |
|  |  |  |  |  |  |  |  | not_tested |  |
|  |  |  |  |  |  |  |  | not_tested |  |
|  |  |  |  |  |  |  |  | not_tested |  |
| **Lowest flow with blockers == () and action = hold** |  |  |  |  |  | hold | () | not_tested | candidate purge-only flow |

## Phase C - Purge + Lip Heat To Margin

| `lip_heat_pwm` | Purge flow held | Lip surface T | Underside T | Margin | `action` | `blockers` | Media stable? | Result | Notes |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  | not_tested | step >= 2 min |
|  |  |  |  |  |  |  |  | not_tested |  |
|  |  |  |  |  |  |  |  | not_tested |  |
| **Operating point: blockers == (), action = hold, media stable** |  |  |  |  | hold | () |  | not_tested | record (purge, lip_heat_pwm) pair |

## Phase D - Real Imaging Dwell

| Measurement | Value / observation | Result | Notes |
|---|---|---|---|
| Dwell duration (>= longest planned exposure/scan) |  | not_tested |  |
| Held `purge_flow_ml_min` |  | not_tested | operating-point flow |
| Held `lip_heat_pwm` |  | not_tested | operating-point heat command |
| Min margin over dwell |  | not_tested | must stay >= target_margin_c |
| Max RH over dwell |  | not_tested | must stay < max_safe_relative_humidity_pct |
| `acquisition_allowed` for whole dwell (yes/no) |  | not_tested | single blocker sample fails the dwell |
| `blockers` raised at any sample |  | not_tested | () = pass |
| Underside haze onset (yes/no) |  | not_tested |  |
| Haze time-to-onset / margin at onset / recovery |  | not_tested |  |

## The Gating Numbers

| Gate | Measured value / observation | Result | Notes |
|---|---|---|---|
| (1) Margin >= `target_margin_c` (2.0 C) for whole dwell |  | not_tested | <0 = below_dew_point (BLOCKED); 0-2.0 = margin_below_target (BLOCKED); 2.0-2.5 = increase_purge advisory; >=2.5 = hold |
| (2) RH < `max_safe_relative_humidity_pct` (98 %) for whole dwell |  | not_tested | >= 98 % = headspace_rh_at_condensation_limit, BLOCKED |
| (3) Production `purge_flow_ml_min` + `lip_heat_pwm` (pair) |  | not_tested | the numbers that retire the reserved placeholders |

## Decision

Decision: `evidenced (retire setpoints) | purge-only | lip-heat-required | escalate | defer | block`

Rationale:

## decision_log Entry Authorized By Evidence

| Outcome | decision_log.md entry to record |
|---|---|
| Dwell holds, blockers == () throughout | condensation purge/lip-heat operating point evidenced; retire reserved setpoints in `src/aevum_smis/condensation.py` |
| Margin held purge-only (no lip heat) | record purge-only flow as operating point; lip heat stays reserve |
| Margin held only with lip heat, media stable | record (purge, lip_heat_pwm) pair; lip heat required, not optional |
| RH pinned at ceiling | escalate headspace/defogging to `observation_module.md`; do NOT relax 98 % ceiling |
| Underside at/below dew point or margin unreachable without disturbing media | escalate wet-boundary / lip-heat authority; setpoints stay reserved |

## Open Failures Or Blockers

| Failure | Blocker / gate | Next action |
|---|---|---|
|  |  |  |
