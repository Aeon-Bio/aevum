# OT-2 Target-Class Verification

## Purpose

Target verification is scoped to a specific fixture, robot, deck slot, pipette
state, offset registry entry, and access geometry. A successful check at one
target does not authorize nearby targets or wet work.

Use this page to decide what an agent or bridge session may do next after the
first PoC print is installed.

## Target Classes

Initial target classes for `aevum_p300_poc_fixture`:

The current cassette has a second geometry dimension by row:

```text
row A: 3.0 mm guide holes
row B: 3.5 mm guide holes
row C: 4.0 mm guide holes
row D: 4.5 mm guide holes
```

Column target classes below describe offset families. Each evidence record
should also preserve the exact well row/diameter. Do not promote success at one
row diameter to another row diameter.

| Target class | Geometry | Meaning |
| --- | --- | --- |
| `center_high_z` | column 1, center, conservative Z above guide plane | Tip can reach the nominal center target region at high clearance. |
| `center_low_z_dry` | column 1, center, low dry approach | Tip can enter the center guide/well path without liquid. |
| `offset_x_1p0_high_z` | column 2, +1.0 mm X, high clearance | Tip can reach the +1.0 mm target region at high clearance. |
| `offset_x_1p0_low_z_dry` | column 2, +1.0 mm X, low dry approach | Tip can enter the +1.0 mm guide/well path without liquid. |
| `offset_x_1p5_high_z` | column 3, +1.5 mm X, high clearance | Tip can reach the candidate final offset region at high clearance. |
| `offset_x_1p5_low_z_dry` | column 3, +1.5 mm X, low dry approach | Tip can enter the candidate final offset path without liquid. |
| `offset_x_2p0_high_z` | column 4, +2.0 mm X, high clearance | Tip can reach the aggressive boundary offset region at high clearance. |
| `offset_x_2p0_low_z_dry` | column 4, +2.0 mm X, low dry approach | Boundary dry approach only; does not imply final design suitability. |
| `center_wet` | column 1, center, dye/water dispense | Low-volume liquid dispense works at the center target. |
| `offset_x_1p0_wet` | column 2, +1.0 mm X, dye/water dispense | Low-volume liquid dispense works at +1.0 mm X. |
| `offset_x_1p5_wet` | column 3, +1.5 mm X, dye/water dispense | Low-volume liquid dispense works at the candidate final offset. |
| `offset_x_2p0_wet` | column 4, +2.0 mm X, dye/water dispense | Boundary wet test only; excluded from first wet runs by default. |

Mat-patch tests are separate target classes because a real slit grid can align
to only one global offset at a time:

```text
mat_patch_offset_x_1p5_low_z_dry
mat_patch_offset_x_1p5_wet
```

Add other mat-patch classes only after the no-mat path is stable.

## Promotion Rules

Promotion must move in this order:

1. Fixture print QC passes.
2. Camera capture succeeds and is indexed.
3. Fixture-installed image is recorded with `purpose=fixture_presence`.
4. Robot, slot, fixture artifact checksums, and pipette state match the session.
5. Registration offset is recorded in the structured offset registry.
6. `center_high_z` is observed.
7. `center_low_z_dry` is observed.
8. Offset high-Z classes are observed before their matching low-Z dry classes.
9. Wet classes are attempted only after the matching dry class passes.
10. Mat-patch classes are attempted only after no-mat dry and wet classes pass.

Never promote:

- high-Z evidence to low-Z authorization,
- center evidence to offset authorization,
- dry evidence to wet authorization,
- no-mat evidence to mat-patch authorization,
- one robot, slot, fixture, pipette, or checksum combination to another.

## Evidence Required

Each target-class verification record should include durable evidence handles
and a derived claim. Raw image paths, vision-result paths, and free-text
commissioning observations can be preserved as legacy evidence records, but
they cannot authorize target promotion from the target-class record itself.

```json
{
  "schema_version": 1,
  "target_class": "offset_x_1p5_low_z_dry",
  "fixture_load_name": "aevum_p300_poc_fixture",
  "fixture_params_sha256": "",
  "labware_definition_sha256": "",
  "robot_serial": "",
  "robot_server_version": "",
  "slot": "1",
  "pipette_name": "p300_single_gen2",
  "pipette_mount": "left",
  "tiprack_load_name": "opentrons_96_tiprack_300ul",
  "offset_registry_record": "",
  "run_id": "",
  "maintenance_run_id": "",
  "command_ids": [],
  "evidence": [
    {
      "schema_version": 1,
      "evidence_id": "",
      "source_kind": "vision_analysis",
      "path": "",
      "checksum_sha256": "",
      "session_id": "",
      "quality": "usable"
    }
  ],
  "claims": [
    {
      "schema_version": 1,
      "claim_id": "",
      "claim_type": "target_class_verified:offset_x_1p5_low_z_dry",
      "value": true,
      "session_id": "",
      "fixture_load_name": "aevum_p300_poc_fixture",
      "fixture_params_sha256": "",
      "labware_definition_sha256": "",
      "method": "",
      "quality": "usable",
      "evidence": []
    }
  ],
  "result": "blocked|passed|failed",
  "predecessor_records": []
}
```

Camera evidence should include before/after images for safety-critical
transitions. During commissioning, human observations may label or interpret
images, but the bridge should still store those artifacts as evidence packets
and derive the target claim from handles rather than from raw target-record
fields.

## Blockers

Block target-class promotion if any of these are true:

- fixture QC measurements are missing or outside gate,
- base rocks or shifts in the deck slot,
- the planned guide hole or mock well is blocked or deformed,
- current pipette state differs from the recorded session state,
- evidence write or index update fails,
- target evidence path is missing or its checksum does not match the handle,
- camera capture fails when required,
- vision analysis returns `evidence_ok: false`,
- motion command history is ambiguous,
- command response, command history, and camera/commissioning evidence disagree,
- the target class depends on an unverified lower-risk class,
- `result` is manually set to `passed` without a matching
  `target_class_verified:<target_class>` claim and usable evidence handles.

`motion_gate: false` from the current vision scaffold is expected. It means the
image is evidence only. It does not by itself fail the commissioning record, but
it prevents autonomous promotion until calibrated fixture and target detectors
exist.

## Initial Checklist

Use this first after the PoC print passes physical QC:

```text
[ ] fixture_presence evidence recorded
[ ] center_high_z observed
[ ] center_low_z_dry observed
[ ] offset_x_1p0_high_z observed
[ ] offset_x_1p0_low_z_dry observed
[ ] offset_x_1p5_high_z observed
[ ] offset_x_1p5_low_z_dry observed
[ ] center_wet observed
[ ] offset_x_1p0_wet observed
[ ] offset_x_1p5_wet observed
[ ] mat_patch_offset_x_1p5_low_z_dry observed
[ ] mat_patch_offset_x_1p5_wet observed
```

Leave `offset_x_2p0_low_z_dry` and `offset_x_2p0_wet` out of the first pass
unless center, +1.0 mm, and +1.5 mm evidence show large margin.
