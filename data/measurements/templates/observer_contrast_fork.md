# Observer Label-Free Contrast Fork (WS2812 Matrix)

Protocol:
`docs/protocols/observer_contrast_fork_ws2812.md`

## Session Identity

| Field | Value |
|---|---|
| Date |  |
| Operator |  |
| Second counting operator |  |
| Optical head identifier (4× build) |  |
| WS2812 matrix / arm identifier |  |
| Plate identifier (CellVis P96-1.5H-N) |  |
| Cell line / passage |  |
| Media + temperature at addition |  |
| Stage-0 Phases A–C record (focus pre-req) |  |
| Measurement images folder |  |

## Pre-Run Checks

| Check | Result | Evidence / notes |
|---|---|---|
| Phases A–C passed (dry, dry-through-plate, wet focus) | not_tested | reference `observer_optical_bench.md` run record |
| 4× head focused on cell plane in at least one mode | not_tested |  |
| Raw-frame capture (no auto-gain, no post) confirmed | not_tested |  |
| Rig settled ≥15 min, posts not hand-held | not_tested |  |
| Warm 37 °C media in imaged wells | not_tested |  |

## Illumination Mode Sweep

| Mode | Well | Grid-line C | Cell-edge C | Result | Evidence / notes |
|---|---|---|---|---|---|
| Brightfield (center pixels) | corner | | | not_tested |  |
| Brightfield (center pixels) | center | | | not_tested |  |
| Oblique (~33.2° quadrant) | corner | | | not_tested |  |
| Oblique (~33.2° quadrant) | center | | | not_tested |  |
| Darkfield (ring) | corner | | | not_tested |  |
| Darkfield (ring) | center | | | not_tested |  |
| Epi / reflected | corner | | | not_tested |  |
| Epi / reflected | center | | | not_tested |  |
| Transmitted-from-above (panel) | corner | | | not_tested |  |
| Transmitted-from-above (panel) | center | | | not_tested |  |

## Cell Counting

| Mode | Count A | Count B | % disagreement | Result (±10 %) | Notes |
|---|---|---|---|---|---|
| Best module-side mode | | | | not_tested |  |
| Any other mode with C ≥ 0.15 | | | | not_tested |  |

## Condensation Interaction

| Mode | Haze onset (yes/no) | Time-to-onset | Contrast drop | Result | Notes |
|---|---|---|---|---|---|
| Passing / candidate mode | | | | not_tested |  |

## Decision

Decision: `module-side win | top-window commit | escalate | defer`

Rationale:

## decision_log Entry Authorized By Evidence

| Outcome | decision_log.md entry to record |
|---|---|
| Oblique/epi `C ≥ 0.15` + counts ±10 % | contrast fork closed module-side; adopt oblique source; lid stays sealed |
| Only transmitted-above passes | commit lid optical window; re-cost gas/septum manifold; rescope `observation_module.md`, `sensor_module_interface.md` |
| Nothing passes / oblique marginal unrecovered | escalate to phase optics / different sensor (global-shutter IMX273 if jitter) |

## Open Failures Or Blockers

| Failure | Mode | Next action |
|---|---|---|
|  |  |  |
