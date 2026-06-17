# First Fixture QC Acceptance

## Purpose

The bridge should not treat generated CAD as sufficient evidence that a printed
fixture is safe. Physical measurements from the printed part feed the runtime
safety envelope.

## Nominal First Fixture

Generated nominal bounds:

```text
registered SBS base footprint: 127.76 x 85.48 mm
base STL: 127.76 x 85.48 x 67.70 mm
plate cap installed: 70.00 x 70.00 x 25.30 mm
mat cassette installed: 70.00 x 70.00 x 3.00 mm
assembly top: 91.00 mm
```

Critical geometry:

```text
guide_hole_diameter_default: 4.0 mm
cassette_guide_hole_rows: A=3.0 / B=3.5 / C=4.0 / D=4.5 mm
mock_well_upper_diameter: 6.80 mm
mock_well_lower_diameter: 6.21 mm
mock_well_area_equivalent_bottom_diameter: 6.18 mm
mock_well_diagram_internal_depth: 11.93 mm
mock_well_cell_plane_depth_from_plate_top: 12.40 mm
mock_plate_bottom_z: 65.70 mm
mock_plate_top_z: 80.0 mm
mat_plane_z: 88.0 mm
printed_cassette_top_z: 91.0 mm
fixture_top_z: 91.0 mm
target_offset_x: +1.5 mm
exposed_qc_hole_coupon_x: 80.0 mm
exposed_qc_hole_coupon_y: 18.0 / 25.0 / 32.0 / 39.0 mm
exposed_qc_hole_coupon_diameters: 3.0 / 3.5 / 4.0 / 4.5 mm
reg_1: x = 82.0 mm, y = 8.0 mm, exposed after assembly
reg_2: x = 119.76 mm, y = 77.48 mm, exposed after assembly
integrated labels: coarse cut labels on base, plate cap, and mat cassette
axis arrows: +X and +Y cut into base top near origin corner
```

## Provisional Acceptance Gates

These thresholds are intentionally conservative placeholders for the first
printed interaction mule. Tighten them after the first measured run.

| Check | Initial Gate | Runtime Effect |
| --- | --- | --- |
| X bound | within +/- 1.0 mm of nominal | outside gate blocks registration |
| Y bound | within +/- 1.0 mm of nominal | outside gate blocks registration |
| Z bound | no higher than nominal + 1.0 mm | higher value blocks low-Z motion |
| Camera capture | image captured and indexed | failure blocks autonomous gates |
| Fixture image | fixture visible in expected deck region | failure blocks registration |
| Vision scaffold | `evidence_ok: true`, `motion_gate: false` until detector calibration | failure blocks registration |
| Base seating | no visible rocking in selected deck slot | rocking blocks registration |
| Base flatness | no repeatable corner gap on flat reference surface | corner gap blocks low-Z motion |
| Brim cleanup | slicer brim fully removed before OT-2 deck placement | unremoved brim blocks registration |
| Guide holes | all planned target holes visibly open | blocked target class is unavailable |
| Support debris | no debris in guide/access geometry | debris blocks registration |
| Mock wells | no visible deformation at tested wells | deformed target class unavailable |
| Warping/lift | no lifted corner that changes deck seating | lift blocks registration |
| Text labels | coarse integrated labels only | missing/illegible labels do not authorize or block robot motion |

## Runtime Envelope Rule

The bridge should store measured bounds in the session and use the more
conservative value when measured dimensions differ from CAD. Missing measurements
block low-Z motion.

Camera-based QC should produce image handles and confidence values. If confidence
is below threshold during commissioning, human labels can be recorded as training
or calibration evidence, but autonomous promotion requires a machine gate.

For target-class verification:

- `center_high_z` does not authorize low-Z motion.
- `center_low_z_dry` authorizes only center-column low-Z dry targets that were
  observed.
- `offset_x_1p0_low_z_dry`, `offset_x_1p5_low_z_dry`, and
  `offset_x_2p0_low_z_dry` are separate target classes.
- Wet operations require separate wet verification after dry success.
- The full target-class checklist lives in
  `docs/protocols/target_class_verification.md`.
