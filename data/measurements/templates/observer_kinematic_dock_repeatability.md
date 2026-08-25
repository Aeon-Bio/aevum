# SMIS Kinematic-Dock Lateral Re-Seat Repeatability — Run Record

- **Date:**
- **Operator:**
- **Dock build identifier:** (printed cradle / head-plate revision)
- **Balls:** (Ø6 grade-25 chrome ×3 — DUT, gated by tests/test_smis_dock.py)
- **Seats:** (cone + vee + flat — the 3-2-1 seat, DUT)
- **Magnets:** (3× N52 pot — DUT)
- **Dowel:** (anti-rotation ×1 — DUT)
- **Bench / camera / objective:** (shared optical-bench ground)
- **USAF target / fiducial:**
- **Measurement images folder:**
- **Protocol:** `docs/protocols/observer_kinematic_dock_repeatability.md`

> SPEC values (device under test, NOT evidence): repeatability target = 5.0 µm
> (`DockSpec.repeatability_target_um`); seat = canonical 3-2-1 (cone+vee+flat); preload
> = 3× N52 (~9 kg) → 5.0× over the 1 g-scan demand; ball circle Ø44 → contact ~Ø38
> clears the Ø32 keepout; 1 anti-rotation dowel. These are GATED in
> `tests/test_smis_dock.py` / `src/aevum_smis/dock.py`, NOT proven here. This protocol
> proves ONLY the measured lateral re-seat scatter on a real imaged target.

## Session Identity / Pre-Run Checks

| Check | Result | Evidence / notes |
|---|---|---|
| Dock cradle + imaging head share one breadboard datum | not_measured |  |
| Target rides the head half; camera fixed to cradle ground | not_measured |  |
| Focus + XY brought in once, then LOCKED for the whole run | not_measured |  |
| Rig settled ~15 min, posts not hand-held during cycles | not_measured |  |
| Seated reference frame captured (full-seat audited) | not_measured |  |

## (c) Pixel-Scale Calibration (measure FIRST)

| Measurement | Value | Tool | Result | Notes |
|---|---|---|---|---|
| Pixel scale `µm/px` |  | stage micrometer / known USAF pitch | not_measured | measured on THIS rig, not assumed from objective spec |

## (d) Drift Floor (no-undock re-image)

| Measurement | Value | Result | Notes |
|---|---|---|---|
| No-undock re-image count |  | not_measured | re-image across the same wall-clock span as 20 cycles |
| Drift radial spread `r_drift` (µm) |  | not_measured | must be ≪ redock scatter (≤ ~1 µm); else result VOID |
| `r_drift` ≪ redock scatter? | yes / no | not_measured | no → fix the rig before cycling, do not record a dock verdict |

## (a) Per-Cycle Lateral Re-Seat Offsets (20 cycles)

| Cycle | Seat audited full? (e) | Δx (µm) | Δy (µm) | Radial `r_i` (µm) | Void? | Notes |
|---|---|---|---|---|---|---|
| ref |  | 0 (datum) | 0 (datum) | 0 | — | seated reference frame |
| 1 | not_measured |  |  |  |  |  |
| 2 | not_measured |  |  |  |  |  |
| 3 | not_measured |  |  |  |  |  |
| 4 | not_measured |  |  |  |  |  |
| 5 | not_measured |  |  |  |  |  |
| 6 | not_measured |  |  |  |  |  |
| 7 | not_measured |  |  |  |  |  |
| 8 | not_measured |  |  |  |  |  |
| 9 | not_measured |  |  |  |  |  |
| 10 | not_measured |  |  |  |  |  |
| 11 | not_measured |  |  |  |  |  |
| 12 | not_measured |  |  |  |  |  |
| 13 | not_measured |  |  |  |  |  |
| 14 | not_measured |  |  |  |  |  |
| 15 | not_measured |  |  |  |  |  |
| 16 | not_measured |  |  |  |  |  |
| 17 | not_measured |  |  |  |  |  |
| 18 | not_measured |  |  |  |  |  |
| 19 | not_measured |  |  |  |  |  |
| 20 | not_measured |  |  |  |  |  |

> Void cycles (partial/false seat) are discarded and re-run, NOT counted as a fail.
> Need ≥ 20 VALID cycles for a distribution.

## (b) Scatter Statistic — Headline

| Statistic | Value (µm) | Result | Notes |
|---|---|---|---|
| Valid cycle count (≥ 20) |  | not_measured | fewer than 20 is not a distribution |
| **95th-percentile radial `r_95`** |  | not_measured | **HEADLINE — target ≤ 5.0 µm** |
| Worst single cycle `r_max` |  | not_measured | recorded explicitly, never hidden |
| Per-axis std (Δx / Δy) |  | not_measured | isotropic vs biased along vee/flat axis |

## Decision

Decision: `pass | escalate | revise | void`

- [ ] PASS — `r_95 ≤ 5 µm`: keep `requires_post_dock_autofocus: false`; head earns the
  cheap Tier-A post-dock ritual. The reserved ≤ 5 µm claim is now backed by evidence.
- [ ] ESCALATE — `r_95 > 5 µm`: set `requires_post_dock_autofocus: true`; the
  registration ritual rises to Tier B (3 fiducials + autofocus map) on every dock. The
  dock itself is NOT blocked.
- [ ] VOID — `r_drift` not ≪ redock scatter: rig-limited, uninterpretable; fix the rig
  and re-run.
- [ ] REVISE — bimodal/outlier scatter: intermittent-seat mechanical problem (debris,
  magnet alignment, dowel fit); fix mechanically and re-run.

**Chosen action / manifest flag:** `requires_post_dock_autofocus` = ______

## What this does NOT touch

> This measurement creates NO motion authority. It does NOT change `validate_dock`,
> does NOT loosen the 5 µm figure, and does NOT re-prove the 3-2-1 seat / 3-magnet 5.0×
> margin / keepout clearance (those stay gated in tests/test_smis_dock.py). Its only
> output is the `requires_post_dock_autofocus` flag feeding the registration ritual.

## Notes
