# Observer Leg-Corridor & Objective-Barrel Metrology — Run Record

- **Date:**
- **Operator:**
- **Deck source:** (real OT-2 / printed standoff legs, revision)
- **Objective candidate(s):** (make / model / thread / mag / NA)
- **Protocol:** `docs/protocols/observer_leg_corridor_objective_metrology.md`

> CAD placeholders (source of comparison, NOT evidence): scan corridor `W_corr` = 120.4 mm
> (leg inner faces X 13.6 / 134.0); strike-onset footprint ≈ 21.2 mm; live corridor margin
> 0.12 mm but binding scan margin 0.02 mm (the bay hi-wall is co-located and tighter);
> Y wet/dry-gutter wall `Y_avail` = 357.5 mm; legs span
> z −80..0 (through the head sweep z −48..−8); barrel placeholder Ø25.

## Measurements

| Item | Symbol | Measured | Tool | Pass condition | Result |
|---|---|---|---|---|---|
| Scan corridor — end A | `W_corr_A` |  | calipers |  | not_measured |
| Scan corridor — end B | `W_corr_B` |  | calipers |  | not_measured |
| Scan corridor — mid-column | `W_corr_mid` |  | calipers |  | not_measured |
| **Narrowest corridor** | `W_corr` |  | calipers | binding wall | not_measured |
| Leg Z span vs head sweep | — |  | calipers | legs continuous through z −48..−8 | not_measured |
| Objective widest Ø | `Ø_obj` |  | calipers | widest knurl, full length | not_measured |
| Camera-arm scan intrusion | `arm_x` |  | calipers | ≈ 0 (coaxial/offboard) | not_measured |
| Effective scan footprint | `FE_scan` |  | calipers | max(Ø_obj, body, arm_x) | not_measured |
| Corridor fit residual | `W_corr − (well_window_x + FE_scan)` |  | arithmetic | > 0 | not_measured |
| Y wet-gutter wall | `Y_avail` |  | calipers | clear dry-Y between gutters | not_measured |
| Traverse-Y fit residual | `Y_avail − (well_span_y + FE_scan)` |  | arithmetic | > 0 | not_measured |

## Per-candidate objective table

| Candidate | Ø_obj | FE_scan | threads W_corr? | residual mm |
|---|---|---|---|---|
|  |  |  |  |  |

## Decision

- [ ] PASS — an objective threads the corridor; update `front_end_barrel_diameter` +
  `front_end_*` footprints in `cad/one_row_coupon.params.json` to measured values.
- [ ] RELOCATE LEGS — no sourceable objective fits; move the deck-engagement seating
  out of the optical corridor (+ Stage-0 seating-repeatability re-validation).
- [ ] RE-BASELINE — measured `W_corr` differs materially from 120.4 mm; update the CAD
  leg geometry.

**Chosen objective / action:**

**SMIS envelope update:** set `SmisEnvelope.scan_corridor_width_mm` from `W_corr` =
______ mm (binds every modality head, not just this one).

## Notes
