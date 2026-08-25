# Observer Settle-Time & Vibration — Stage 2 (ADXL345) — Run Record

Protocol:
`docs/protocols/observer_settle_vibration_stage2_adxl345.md`

> CAD arithmetic is NOT evidence (source of comparison only): the
> `t ≈ (Q/πf)·ln(A0/A)` estimate gives ~210 ms to ±27 µm (4×) and ~510 ms to ±4 µm
> (10×) from a guessed `f ≈ 60 Hz, Q ≈ 30, A0 ≈ 100 µm`. Only the measured ring-down
> numbers below are physical evidence. Hold-still spec inherited from the bench DOF:
> **±27 µm @ 4× / ±4 µm @ 10×** (`observer_optical_bench.md`).

## Session Identity

| Field | Value |
|---|---|
| Date |  |
| Operator |  |
| Observer rig / Stage-2 build identifier |  |
| Structural focus loop (all-aluminum? PLA present?) |  |
| ADXL345 mount location (on head / near objective+fold) |  |
| ADXL345 axis orientation (X scan / Y traverse / Z focus) |  |
| Klipper host + firmware version |  |
| OT-2 co-located? (serial / deck slot) |  |
| Input-shaper type + frequency (if used) |  |
| Capture / trace files folder |  |

## Pre-Run Checks

| Check | Result | Evidence / notes |
|---|---|---|
| Stage 1 focus Z axis exists; one-plate XY scan can drive a real 9 mm step | not_measured |  |
| ADXL345 bonded rigidly to the head (no foam between sensor and loop) | not_measured |  |
| All-aluminum focus loop (no PLA in path), or PLA caveat recorded | not_measured |  |
| Raw acceleration traces captured (not just Klipper auto-shaper) | not_measured |  |
| Rig thermally settled, structure not hand-held during capture | not_measured |  |
| OT-2 co-located on shared frame (required for Phase 4) | not_measured |  |

## Phase 1 — Noise Floor (observer idle, OT-2 absent/off)

| Item | Symbol | Measured | Units | Gate | Result |
|---|---|---|---|---|---|
| ADXL345 RMS noise floor | — |  | µm (RMS) | << ±4 µm 10× spec | not_measured |

## Phase 2 — Natural Mode

| Item | Symbol | Measured | Units | Method | Result |
|---|---|---|---|---|---|
| First-mode frequency | `f` |  | Hz | FFT of free ring-down | not_measured |
| Quality factor | `Q` |  | — | log-decrement / half-power BW | not_measured |
| Secondary mode(s) | — |  | Hz | FFT | not_measured |

## Phase 3 — Post-Move Settle (9 mm well-to-well step)

| Item | Symbol | Unshaped | Shaped | Units | Gate | Result |
|---|---|---|---|---|---|---|
| Settle to 4× spec | `t_settle,4×` |  |  | ms | ≤ scan-cycle settle budget at ±27 µm | not_measured |
| Settle to 10× spec | `t_settle,10×` |  |  | ms | ≤ budget at ±4 µm | not_measured |
| Post-move sway amplitude `A0` | `A0` |  |  | µm | — | not_measured |
| Z-axis focus-step settle (objective+fold) | `t_settle,Z` |  |  | ms | settles faster than X/Y | not_measured |

## Phase 4 — OT-2 Coupling (co-located)

| Item | Symbol | Measured | Units | Gate | Result |
|---|---|---|---|---|---|
| OT-2 idle floor at head (powered + idle) | — |  | µm (RMS / peak) | < ±4 µm at head for concurrency | not_measured |
| OT-2 active coupling (deck move / pipette puncture) | — |  | µm (peak) | bounded under isolation | not_measured |

## Gating Numbers Roll-Up

| Gate | Threshold | Measured | Result |
|---|---|---|---|
| (1) Single-beam settle to ±27 µm (4×, shaped) | ≤ scan-cycle settle budget | | not_measured |
| (2) Settle to ±4 µm (10×, shaped) | in budget | | not_measured |
| (3) OT-2 idle floor at head | < ±4 µm | | not_measured |
| (4) First-mode f/Q sanity | not grossly softer than f≈60 Hz / Q≈30 | | not_measured |

## Decision

Gantry: `single thin-truck confirmed | two-plate split triggered | defer`

10× path: `10× retained | 4×-only | defer`

OT-2 mode: `interlock mandatory | concurrency possible | defer`

Rationale:

## decision_log Entry Authorized By Evidence

| Outcome | decision_log.md entry to record |
|---|---|
| Shaped `t_settle,4×` ≤ budget on a single beam | single thin-truck gantry confirmed at 4×; two-plate split held in reserve |
| Single beam cannot reach ±27 µm even shaped | two-plate split triggered by measured settle (stiffness escape) |
| Shaped `t_settle,10×` reaches ±4 µm in budget | 10× drill-down retained in production path (commit VCM precision) |
| 10× settle too slow | 4×-only production path; 10× sparse QC-flagged escalation only |
| OT-2 idle floor < ±4 µm at head + active coupling bounded | vibration-isolated concurrency possible (interlock still default) |
| OT-2 idle floor ≥ ±4 µm at head | concurrency dead; strict time-sliced OT-2 interlock mandatory |
| Measured f/Q grossly softer than estimate | re-open gantry stiffness (beam length / rail tier / head mass) |

## Open Failures Or Blockers

| Failure | Phase | Next action |
|---|---|---|
|  |  |  |

## Notes
