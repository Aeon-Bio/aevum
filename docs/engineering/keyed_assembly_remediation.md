# Keyed assembly (D1–D9) — review findings & remediation plan

The CAD assembly-decomposition (`production_assembly.keyed_joints_enabled`, default **false**)
is gated so the **flag-off default geometry is byte-identical** to the pre-keyed design
(CI-enforced by `tests/test_keyed_joints_flag_off_golden.py`). Two adversarial review cycles
(F7, and the follow-up on the remediation itself) found the **flag-on** geometry is a
first-pass scaffold. This doc is the durable, tracked plan — not the tmpdir hypergraph.

## Done (committed)
- **G4** golden gate: flag-off byte-identity pinned to `tests/golden/flag_off_geometry_baseline.json`
  + a robust "flag is wired" existence check (`test_keyed_joints_flag_off_golden.py`).
- **G1** D4 dovetail real mate: shared Z datum, X+Z clearance, protruding witness, thin-part
  butt fallback, and an attach-check so a bbox-centre key in a hollow section falls back to a
  butt seam instead of floating. Mate proven on attaching parts (`tests/test_keyed_split_interface.py`).
- **G2/G3** verification honesty: D9 swept-removal tautology and D5 seal-lap claims corrected.
- **G6** loop-closing fixes (this pass): repaired the broken wiring test; removed the stale D1
  `_two_module_joint_metadata` "the lap bridges / not a flat butt" claim; added the honest
  per-part-realization caveat to the D8 descriptor audit; bounded the witness Z-protrusion in
  the mate test; moved this plan into the repo.

## Done (cont.)
- **G5a** wall-aware key placement: scatter candidate keys across the seam X-span, keep those whose
  boss overlaps seam material (deduped by spacing). Result: the structural backbone (`plate_support_frame`,
  the datum frame) carries MULTIPLE keys (was 1); thin-walled frames/shells/discrete parts (wet_chamber_frame,
  covers, keeper doors) correctly butt — they are too thin for a robust oversized dovetail and are retained
  by their own snap/wedge mechanisms while riding the keyed backbone (a coherent "key the backbone, retain the
  rest" strategy, per the print-native intent). Mate + multi-key density tested.

## Deferred design — needs physical iteration. **Do NOT ship flag-on for wet use until G5c.**
| ID | Item | Exit criterion |
|---|---|---|
| **G5a+** | Per-wall *sized* keys on thin perimeter walls (if a printed test shows the backbone-only joint is insufficient). | Wall-width-aware key sizing so a 2–4mm wall hosts a fitted (non-overhanging) key. |
| **G5b** | D4 Z-shear interlock (key slides out +Z). | Add only if a physical Z-lift test on a printed pair shows the existing wedge/deck retention is insufficient; requires frozen print orientation. |
| **G5c** | Real seal-across-split (lap applied DURING the split, one half overlapping, seated OUTSIDE the elastomer pocket). **BLOCKS wet use.** | Dye + pressure/vacuum decay evidence on a printed keyed pair. |
| **G5d** | Real swept-solid verification (boolean interference for removal / trapped-plate / per-part key realization) replacing descriptor/coincident-seam proxies. | Checks build the solids and boolean-intersect; a butted part reports butt, not keyed. |
| **G5e** | D6 four-corner lid keys over-constrain (lid rocks). | 3-2-1 / kinematic location; flatness/registration unaffected by warp. |
| **G5f** | Freeze FDM process + print orientation before fit-class clearances; size sub-nozzle witness/detent features above one road/layer; adopt per-feature commits. | Process card committed; feature dims ≥ nozzle/layer; future features land one-per-commit. |

## Standing constraints (all keyed features)
No-hidden-authority (printed dovetail/hook/wedge only — no metal pins/screws/inserts);
plate-as-consumable keepout (nothing lands on/grips the CellVis plate); COTS crossed as connectors.

## Status: CODE-COMPLETE; physical validation pending
Tractable code work is done: G4 (golden gate), G1+G5a (keyed joint — multi-keyed backbone, real
mate), G2/G3/G6 (honesty + loop-closing fixes), G5e (D6 kinematic). Real solid-inspection
verification lives in the test suite (mate clearance, multi-key density, reassembly, flag-off
golden). The keyed witness is 0.5mm (printable).

The ONLY remaining work is NOT code — it is hardware:
- **G5c (BLOCKS wet use):** real during-split overlapping seal lap + DYE/PRESSURE evidence on a printed pair.
- **G5b:** add a D4 Z-shear interlock ONLY if a printed Z-lift test shows backbone retention is insufficient.
- **G5d (disassembly):** swept-removal serviceability proof requires a printed pair, not CAD.
- **G5a+ (conditional):** wall-width-sized keys on thin perimeter walls only if backbone-only keying tests insufficient.
- **G5f:** freeze FDM process/orientation before fit-clearances; the pre-existing default wedge-detent
  sub-nozzle sizing is a separate fix (changes shipping geometry, out of this remediation's scope).

Net: the flag-on keyed assembly is geometrically as sound as it can be without a printer; flag-off
ships unchanged and CI-gated. The next step is a physical print of one keyed module pair.
