# Observer Label-Free Contrast Fork (WS2812 Matrix)

## Purpose

This protocol resolves the single most upstream observer decision: whether
**oblique-from-below illumination gives readable label-free contrast** on
unstained adherent cells through the deep aqueous media column, while keeping the
sealed wet lid intact — versus being forced to commit a **transmitted optical
window in the lid**, which re-costs the gas/septum manifold above the plate.

It is the focused illumination experiment broken out of the Stage-0 bench
(`observer_optical_bench.md`, Phase D) because it is the one experiment that
retires the illumination fork, and because everything downstream in
`observation_module.md` and `sensor_module_interface.md` inherits its verdict.
The WS2812 16×16 matrix is the highest-leverage purchase on the bench precisely
because it tests the whole fork — brightfield, oblique, darkfield — without
rebuilding the rig.

It validates whether a module-side source resolves contrast for the sealed top,
or whether the top window must be conceded. It does **not** prove imaging quality,
resolution to optical spec, the 62 mm Z-fit, field flatness, or any moving-system
claim — Gate 6 remains deferred, and the CAD geometry that brackets the front-end
is not physical evidence until the rest of Stage 0 measures it. This protocol
produces one architectural bit (sealed top survives, or it does not) plus the
Michelson and cell-count numbers that justify that bit.

## CAD Review Aids

The dry-bay observer envelopes are validation-only and contain zero installed
parts today. They bracket where the source and head live but are **not** evidence
of contrast:

```text
outputs/cad/aevum_one_row_coupon_validation_dry_bay_envelope_check.step
outputs/cad/aevum_one_row_coupon_validation_observer_front_end_swept_body_check.step
cad/view_one_row_coupon.py --show-observer
```

Inspect them only to confirm the source arm and head clear the plate-support
plane and the deck-foot keepouts. They are inspection references, not a result.

## Measurement Record

Create the run record under:

```text
data/measurements/YYYY-MM-DD_observer_contrast_fork.md
```

Use `data/measurements/templates/observer_contrast_fork.md` as the starting
record. Keep each illumination mode `not_tested` until it has a raw-frame
Michelson value and two independent manual cell counts.

Record at minimum:

| Item | Tool | Pass condition |
|---|---|---|
| Brightfield (center pixels) Michelson | IMX178 raw frames, line profile | `C = (Imax−Imin)/(Imax+Imin)` on a grid line or cell edge |
| Oblique (~53° quadrant) Michelson | IMX178 raw frames, line profile | grid/edge `C ≥ 0.15` for FOR-sealed-top win |
| Darkfield (ring) Michelson | IMX178 raw frames, line profile | grid/edge `C` recorded as marginal-recovery option |
| Epi / reflected Michelson | IMX178 raw frames, line profile | grid/edge `C` recorded; module-side fallback |
| Transmitted-from-above Michelson | diffused panel above, raw frames | grid/edge `C`; only this passing forces a lid window |
| Cell countability per mode | two independent manual counts | counts agree **±10 %** in the passing mode |
| Condensation interaction | timed visual / frame contrast | onset time and contrast drop on plate underside recorded per mode |

## Setup

This protocol assumes Stage-0 Phases A–C of `observer_optical_bench.md` have
already passed (dry resolution, dry-through-plate focus, wet focus survival). Do
not run the fork on a rig that has not focused through the wet stack — a contrast
failure on an unfocused rig is uninterpretable.

1. Build the optical head per `observer_optical_bench.md` Assembly: the **4×**
   infinity plan-achromat → f = 50 mm tube lens → mono IMX178, on the manual XYZ
   stage pointing up. Use the 4× head only — its ±55 µm DOF removes focus as a
   confound for the contrast question.
2. Mount the **WS2812 16×16 matrix** on the movable illumination arm above the
   plate, 30–80 mm above the plate top, on a right-angle clamp that slides in Z
   and swings off-axis in XY, with the frosted diffuser between matrix and plate.
   Keep the diffused LED panel and the LED ring available as baselines.
3. Hold the CellVis P96-1.5H-N plate level in the cradle, skirt-only, observation
   window open from below. Seed **adherent cells** in the imaged wells and
   pipette **warm (37 °C) media** so the contrast and condensation behavior are
   measured under the real thermal gradient, not at ambient.
4. Let the rig settle ~15 min after handling. Do not hold the posts. Confirm
   focus on the cell plane in at least one mode before recording any contrast.

## Illumination Mode Sweep

Cycle the **same** WS2812 matrix through the three module-side modes without
moving the head, then add the two baselines. For each mode, image **one corner
well and one center well**, and compute Michelson contrast on a cell edge and on
a hemocytometer grid line from **raw frames** (no auto-gain, no post-processing).

1. **Brightfield** — illuminate the **center pixels** of the matrix through the
   diffuser. Capture corner + center well. Compute `C` on grid line and cell edge.
   Expect this to be weak: unstained cells are near-zero-amplitude phase objects.
2. **Oblique (~53°)** — illuminate **one quadrant** of the matrix so light enters
   the well off-axis. Capture corner + center well. Compute `C`. This is the
   pseudo-phase-gradient mode and the candidate production source.
3. **Darkfield** — illuminate a **ring** of pixels. Capture corner + center well.
   Compute `C`. This is the marginal-recovery option if oblique lands 0.08–0.15.
4. **Epi / reflected** — if the head carries a coaxial source/beamsplitter, image
   the same wells through the objective. Compute `C`. Module-side fallback.
5. **Transmitted-from-above** — swap to the diffused LED panel above the plate,
   through the full media column. Compute `C`. This is the expensive mode; record
   it last so its result is read against the module-side modes, not for it.

## Cell Counting

For each mode that reaches `C ≥ 0.15`, and for the best module-side mode
regardless:

1. Have two operators independently count cells in the **same** center-well frame
   without conferring.
2. Record both counts and the percent disagreement.
3. A mode is countable only when the two counts agree within **±10 %**. Contrast
   without countability is not a pass.

## Condensation Interaction

The warm-media wet boundary can fog the plate underside and erase contrast that
was real at t = 0.

1. From the moment warm media is added, watch the plate underside for
   condensation haze. Record yes/no, time-to-onset, and the contrast drop on the
   passing mode.
2. If condensation collapses an otherwise-passing mode, that mode is not a pass —
   note it as a wet-boundary failure, not an illumination failure, and flag it
   for `observation_module.md` defogging scope.

## Decision Tree

Read the verdict from the **best module-side mode first**, transmitted-from-above
last:

```
Oblique-from-below OR epi reaches C ≥ 0.15 AND counts agree ±10 %?
  YES → ILLUMINATION RESOLVES FOR THE SEALED TOP (the cheap win).
        Adopt module-side oblique as the production source.
        Lid stays sealed; gas/septum manifold untouched.
        → decision_log.md: record "contrast fork closed module-side".
  NO ↓
Only transmitted-from-above reaches C ≥ 0.15 + countable?
  YES → ILLUMINATION RESOLVES AGAINST THE SEALED TOP.
        Commit a lid optical window; re-cost the gas/septum manifold.
        → decision_log.md: record the top-window commitment + manifold re-cost.
        → flag observation_module.md and sensor_module_interface.md for rescope.
  NO ↓
Oblique lands marginal (0.08–0.15)?
  → Try darkfield ring and computational enhancement before conceding.
    Recover to ≥ 0.15 → treat as module-side win above.
    No recovery → escalate.
  NO ↓
Nothing passes in any mode?
  → ESCALATE: phase optics / different sensor
    (global-shutter IMX273 if jitter; phase-gradient or DIC-class front-end).
    → decision_log.md: record the optical-class escalation.
```

## Pass/Fail Boundary

The module-side (sealed-top) win is claimed only if **all** of these hold in the
same mode:

- a module-side mode (oblique-from-below or epi) reaches raw-frame
  `C ≥ 0.15` on a grid line or cell edge;
- two independent manual cell counts in that mode agree within ±10 %;
- the passing contrast survives warm-media condensation onset, or the
  condensation effect is bounded and dispositioned.

The fork resolves **against** the sealed top — forcing a lid optical window and a
gas-manifold re-cost — when:

- no module-side mode reaches `C ≥ 0.15` with countable cells, and
- transmitted-from-above is the only mode that passes.

Escalate to phase optics or a different sensor when:

- no mode passes, or oblique stays marginal (0.08–0.15) and neither a darkfield
  ring nor computational enhancement recovers it to ≥ 0.15.

Passing this protocol only closes the illumination fork and authorizes the
corresponding `decision_log.md` entry (module-side source, top-window commitment,
or optical-class escalation). It does **not** satisfy Gate 6, authorize the moving
carriage, prove resolution, Z-fit, or field flatness, or authorize any
`cad/one_row_coupon.params.json` change — those remain owned by the rest of
Stage 0 in `observer_optical_bench.md`. The CAD observer envelopes stay
validation-only until that physical evidence exists; geometry is not the proof
this protocol produces.
