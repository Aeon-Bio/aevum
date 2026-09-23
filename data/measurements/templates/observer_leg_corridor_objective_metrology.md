# Observer Leg-Corridor & Objective-Barrel Metrology — Run Record

- **Date:**
- **Operator:**
- **Deck source:** (real OT-2 / printed standoff legs, revision)
- **Objective candidate(s):** (make / model / thread / mag / NA)
- **Protocol:** `docs/protocols/observer_leg_corridor_objective_metrology.md`

> CAD placeholders (source of comparison, NOT evidence), corrected 2026-09-21:
> scan corridor `W_corr` = **117.4 mm** (leg inner faces X **17.10 / 134.50**);
> head-footprint strike onset **15.56 mm**; live corridor margin **−2.72 mm** (it strikes),
> bay per-wall margin +0.02 mm — the two walls are ~2.74 mm apart and the LEGS bind, not
> the bay. Well centres run X 24.88..123.88, so the array is **not centred**: near slack
> 7.78, far slack 10.62. `deck_interface.lower_service_foot_inset_x` (3.0) walks one
> tile-4 foot inboard and sets the near wall; zeroing it restores 120.4 mm / 21.24 mm.
> Y wet/dry-gutter wall `Y_avail` = 357.5 mm; legs span z −80..0 (through the head sweep
> z −48..−8); barrel placeholder Ø25.
>
> Record the two slacks SEPARATELY. The old single-gap residual assumed a centred array
> and is refuted — see the protocol's correction banner.

## Measurements

| Item | Symbol | Measured | Tool | Pass condition | Result |
|---|---|---|---|---|---|
| Scan corridor — end A | `W_corr_A` |  | calipers |  | not_measured |
| Scan corridor — end B | `W_corr_B` |  | calipers |  | not_measured |
| Scan corridor — mid-column | `W_corr_mid` |  | calipers |  | not_measured |
| **Narrowest corridor** | `W_corr` |  | calipers | binding wall | not_measured |
| Near-leg inner face (low X) | `face_lo` |  | calipers | CAD 17.10 | not_measured |
| Far-leg inner face (high X) | `face_hi` |  | calipers | CAD 134.50 | not_measured |
| First / last well centre X | `well_x_min` / `well_x_max` |  | calipers | CAD 24.88 / 123.88 | not_measured |
| Leg Z span vs head sweep | — |  | calipers | legs continuous through z −48..−8 | not_measured |
| Objective widest Ø | `Ø_obj` |  | calipers | widest knurl, full length | not_measured |
| Camera-arm scan intrusion | `arm_x` |  | calipers | ≈ 0 (coaxial/offboard) | not_measured |
| Effective scan footprint | `FE_scan` |  | calipers | max(Ø_obj, body, arm_x) | not_measured |
| Near slack | `well_x_min − face_lo` |  | arithmetic | CAD 7.78 | not_measured |
| Far slack | `face_hi − well_x_max` |  | arithmetic | CAD 10.62 | not_measured |
| **Head budget** | `2 × min(near_slack, far_slack)` |  | arithmetic | CAD 15.56 | not_measured |
| Corridor fit residual | `budget − FE_scan` |  | arithmetic | > 0 | not_measured |
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
- [ ] RE-BASELINE — measured `W_corr` differs materially from 117.4 mm, or the measured
  slacks differ materially from 7.78 / 10.62; update the CAD leg geometry.
- [ ] RE-ROUTE SERVICE SHROUD — `lower_service_foot_inset_x` 3.0 → 0.0. This is the
  cheapest lever: it restores a 120.4 mm corridor and a 21.24 mm budget, at which a
  Ø20.32 RMS barrel clears by +0.46 mm. At 15.56 no RMS objective fits at all.
  **Corrected 2026-09-23:** 15.56 mm is the residual for scanning all 12 well
  columns, which the 88 x 52 mm aperture never admitted. Against the 8 reachable
  columns (63.0 mm span) the budget is **51.56 mm**, at which Ø20.32 clears by
  +31.24 mm with no geometry moved. Record both corridor walls regardless -- the
  wide aperture and the wide head are alternatives, not a package. See
  docs/protocols/observer_leg_corridor_objective_metrology.md, "Corrected again
  2026-09-23".

**Chosen objective / action:**

**SMIS envelope update:** set `SmisEnvelope.scan_corridor_footprint_max_mm` (NOT a
`scan_corridor_width_mm` field — that does not exist on the model) from the measured
**head budget** `2 × min(near_slack, far_slack)` = ______ mm, not from `W_corr` directly.
Binds every modality head, not just this one.

## Notes
