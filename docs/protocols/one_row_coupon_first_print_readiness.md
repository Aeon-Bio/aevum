# One-Row Coupon First-Print Readiness

## Purpose

This protocol is the first physical proof gate for the production-operating
one-row coupon. It prevents the CAD from becoming an end in itself.

The current CAD is allowed to claim production intent only where a printed part,
COTS consumable, service lead, sensor package, or validation artifact can be
measured against that claim. Passing this protocol does not authorize OT-2
motion, wet biology, unattended incubation, or sensor calibration. It only
answers whether the next print is worth assembling and measuring.

## Scope

Use this protocol before adding another representational CAD layer unless that
layer directly supports one of these gates:

- OT-2 deck fit and neighbor-slot clearance;
- print-native, screwless, no-glue assembly and service;
- plate, septum mat, gasket, tube, cable, or sensor installability;
- wet/dry isolation, leak routing, or condensate inspection;
- physical measurement of optics, IR proxy temperature, gas response, or biology
  target access.

If a proposed CAD addition does not support one of those gates, defer or remove
it.

## Inputs

Record these before print or assembly:

```text
params: cad/one_row_coupon.params.json
cad source: src/aevum_cad/row_coupon.py
viewer: cad/view_one_row_coupon.py
assembly: outputs/cad/aevum_one_row_coupon_assembly.step
manifest source: row_coupon_part_manifest()
measurement record: data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md
```

Generated validation artifacts to inspect before printing:

```text
outputs/cad/aevum_one_row_coupon_validation_deck_slot_footprint_check.step
outputs/cad/aevum_one_row_coupon_validation_deck_frame_keepout_check.step
outputs/cad/aevum_one_row_coupon_validation_deck_pod_seating_repeatability_check.step
outputs/cad/aevum_one_row_coupon_validation_adjacent_deck_slot_keepout_check.step
outputs/cad/aevum_one_row_coupon_validation_pipette_toolhead_swept_body_check.step
outputs/cad/aevum_one_row_coupon_validation_sensor_installation_path_check.step
outputs/cad/aevum_one_row_coupon_validation_gas_pcb_flow_cell_check.step
outputs/cad/aevum_one_row_coupon_validation_sensor_service_cable_envelope_check.step
outputs/cad/aevum_one_row_coupon_validation_electrical_connector_mating_state_check.step
outputs/cad/aevum_one_row_coupon_validation_operating_service_dress_check.step
outputs/cad/aevum_one_row_coupon_validation_row_tiling_service_clearance_check.step
outputs/cad/aevum_one_row_coupon_validation_side_gas_tube_envelope_check.step
outputs/cad/aevum_one_row_coupon_validation_wet_dry_failure_path_check.step
outputs/cad/aevum_one_row_coupon_validation_side_gas_leak_witness_check.step
outputs/cad/aevum_one_row_coupon_validation_sample_relief_leak_witness_check.step
outputs/cad/aevum_one_row_coupon_validation_gasket_tab_leak_witness_check.step
outputs/cad/aevum_one_row_coupon_validation_dry_bay_ingress_audit_check.step
outputs/cad/aevum_one_row_coupon_validation_observer_fiducial_focus_target_check.step
outputs/cad/aevum_one_row_coupon_validation_observer_optical_stability_check.step
outputs/cad/aevum_one_row_coupon_validation_observer_kinematic_split_check.step
outputs/cad/aevum_one_row_coupon_validation_assembly_state_witness_check.step
outputs/cad/aevum_one_row_coupon_validation_gasket_compression_gap_gauge.step
outputs/cad/aevum_one_row_coupon_validation_latch_retention_span_check.step
outputs/cad/aevum_one_row_coupon_validation_fail_closed_prerun_inspection_check.step
outputs/cad/aevum_one_row_coupon_validation_printability_support_cleanup_check.step
outputs/cad/aevum_one_row_coupon_validation_material_cleaning_witness_coupon.step
outputs/cad/aevum_one_row_coupon_validation_consumable_metrology_gauge.step
outputs/cad/aevum_one_row_coupon_validation_well_cell_plane_check.step
outputs/cad/aevum_one_row_coupon_validation_ir_thermopile_fov_spot_check.step
outputs/cad/aevum_one_row_coupon_validation_thermal_condensation_proxy_check.step
```

Validation bodies are not production parts. Do not print them as installed
hardware unless a protocol explicitly calls them a gauge or demo coupon.

## Print Package

Generate the print/procurement handoff manifest before slicing:

```bash
uv run python scripts/write_row_coupon_first_print_package_manifest.py --overwrite
```

The package manifest must not treat nonprinted reference geometry as a final
operating substitute. Its procurement table should state that COTS consumables
are real installed parts, service tubing is real tubing or measured
replacement, and electronics/sensor dimensional blanks support dry-fit gates
only until real parts close Gate 6 and operating acceptance.

Generate the slicer queue from that package:

```bash
uv run python scripts/prepare_row_coupon_first_print_slicer_queue.py --overwrite
```

Audit the slicer queue before slicing:

```bash
uv run python scripts/audit_row_coupon_first_print_slicer_queue.py
```

Generate the slicer setup worksheet, audit it, then select exactly one real
setup row. The selector writes the matching setup summary into
`Printer / material / profile`:

```bash
uv run python scripts/write_row_coupon_first_print_slicer_setup.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv

uv run python scripts/audit_row_coupon_first_print_slicer_setup.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv

uv run python scripts/select_row_coupon_first_print_slicer_setup.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md \
  --slicer-name SLICER_NAME
```

Generate and audit the selected-bed split-plan worksheet. This is a decision
worksheet, not print authorization:

```bash
uv run python scripts/write_row_coupon_first_print_bed_fit_split_plan.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_bed_fit_split_plan.csv

uv run python scripts/audit_row_coupon_first_print_bed_fit_split_plan.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_bed_fit_split_plan.csv
```

If the CAD has generated production Y-split parts for the oversized bodies,
audit those files against the selected setup before considering any queue
replacement:

```bash
uv run python scripts/audit_row_coupon_first_print_y_split_artifacts.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --require-ready
```

This proves split STEP/STL presence and selected-bed fit only. It does not
replace Gate 1-6 physical evidence, and it does not authorize slicing.

Prepare and audit the alternate split-artifact slicer queue only after the
split-artifact audit is ready:

```bash
uv run python scripts/prepare_row_coupon_first_print_y_split_slicer_queue.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --overwrite

uv run python scripts/audit_row_coupon_first_print_y_split_slicer_queue.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv
```

Generate and audit a split sliced-output worksheet from that alternate queue:

```bash
uv run python scripts/write_row_coupon_first_print_y_split_sliced_outputs.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md

uv run python scripts/slice_row_coupon_first_print_y_split_slicer_queue.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --sliced-dir outputs/sliced/first_print_y_split \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --overwrite

uv run python scripts/audit_row_coupon_first_print_y_split_sliced_outputs.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md
```

The split queue and split sliced-output worksheet are alternate evidence until
the active measurement-record queue and preflight checks intentionally point to
that artifact set. Blank split sliced-output rows can audit valid, but they are
not print-ready. After batch slicing, the split sliced-output audit must report
`sliced_outputs_ready: true` before strict preflight can authorize print start.

Generate and audit the matching split Gate 1 QC worksheet before using the
split queue for physical inspection:

```bash
uv run python scripts/write_row_coupon_first_print_y_split_gate1_qc_worksheet.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv

uv run python scripts/audit_row_coupon_first_print_y_split_gate1_qc_worksheet.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv
```

Generate and audit the split print batch traveler before handing files to the
printer:

```bash
uv run python scripts/write_row_coupon_first_print_y_split_print_batch_traveler.py \
  --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md

uv run python scripts/audit_row_coupon_first_print_y_split_print_batch_traveler.py \
  --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md \
  --require-handoff-ready
```

The traveler is a physical print handoff. It must match the current split
sliced-output hashes and split Gate 1 QC worksheet, but it does not mark Gate 1
passed; rows begin as `not_printed` until the physical print is run. Rows
changed to `printed` require a `print_evidence_path` that resolves to an
existing nonempty file for the completed batch or part.

After the print batch and Gate 1 measurements are entered, run the combined
print-QC audit. Do not use the split Gate 1 worksheet alone to claim physical
print QC; every passing Gate 1 row must have a matching traveler row marked
`printed`, a traveler `print_evidence_path`, and a Gate 1 `evidence_path`.
Those evidence paths must resolve to existing nonempty files.

```bash
uv run python scripts/audit_row_coupon_first_print_y_split_gate1_print_qc.py \
  --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv \
  --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv \
  --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md \
  --require-print-qc-ready
```

The split queue, split sliced-output worksheet, and split Gate 1 QC worksheet
must refer to the same split artifact set before they can replace the active
monolithic queue path.

To make that replacement active, set `Active print queue mode` in the measurement
record to `split_y` and rerun preflight. Preflight then treats `Split slicer
queue`, `Split sliced output worksheet`, and `Split Gate 1 QC worksheet` as the
authoritative print path while leaving print start blocked until sliced files and
hashes are entered.

Generate the blank Gate 1 QC worksheet for physical inspection:

```bash
uv run python scripts/write_row_coupon_first_print_gate1_qc_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate1_qc.csv
```

Audit the worksheet before and after measurement entry:

```bash
uv run python scripts/audit_row_coupon_first_print_gate1_qc_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate1_qc.csv
```

Every passing Gate 1 row requires measured X/Y/Z values within tolerance and an
`evidence_path` that resolves to an existing nonempty file; blank pre-print rows
remain valid but not ready.

Generate and audit the blank Gate 2 dry assembly worksheet before physical dry
assembly:

```bash
uv run python scripts/write_row_coupon_first_print_gate2_dry_assembly_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv

uv run python scripts/audit_row_coupon_first_print_gate2_dry_assembly_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv
```

Generate and audit the blank Gate 3 OT-2 placement worksheet before physical
deck placement:

```bash
uv run python scripts/write_row_coupon_first_print_gate3_placement_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv

uv run python scripts/audit_row_coupon_first_print_gate3_placement_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv
```

The worksheet includes both 384 tip puncture targets and the larger
conservative two-pipette OT-2 toolhead swept-body envelope. Keep the toolhead
rows `not_tested` until measured lower-body and service-dress clearance evidence
exists.

Generate and audit the blank Gate 4 wet/dry witness worksheet before leak or
condensate testing:

```bash
uv run python scripts/write_row_coupon_first_print_gate4_wet_dry_witness_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv

uv run python scripts/audit_row_coupon_first_print_gate4_wet_dry_witness_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv
```

Generate and audit the blank Gate 5 consumable/puncture worksheet before
consumable metrology or puncture testing:

```bash
uv run python scripts/write_row_coupon_first_print_gate5_consumable_puncture_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv

uv run python scripts/audit_row_coupon_first_print_gate5_consumable_puncture_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv
```

Generate and audit the blank Gate 6 sensor/thermal worksheet before powered
sensor or thermal-proxy planning claims:

```bash
uv run python scripts/write_row_coupon_first_print_gate6_sensor_thermal_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate6_sensor_thermal.csv

uv run python scripts/audit_row_coupon_first_print_gate6_sensor_thermal_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate6_sensor_thermal.csv
```

Every passing Gate 2-6 physical worksheet row requires a measured value or
observation plus an `evidence_path` that resolves to an existing nonempty file.
Blank pre-test rows remain valid but not ready.

Generate and audit the nonprinted installed-item inventory before dry assembly:

```bash
uv run python scripts/write_row_coupon_first_print_install_inventory.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv

uv run python scripts/audit_row_coupon_first_print_install_inventory.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv
```

The blank inventory should report `worksheet_valid: true` and
`install_inventory_ready: false`. It becomes ready only after each pass row
identifies the installed item or dimensional blank, preserves the row-level
`operating_requirement`, uses an allowed `installed_as` value for its source,
and names an `evidence_path` that resolves to an existing nonempty physical
proof file. Dimensional electronics or sensor blanks prove only mechanical
dry-assembly envelope; the stricter
`real_sensor_inventory_ready` claim stays false until every electronics,
electrical-service, IR, gas-sensor, and headspace-sensor inventory row is
installed as `real_part`.

Generate and audit the service-state review worksheet before physical assembly.
The default writer can create a blank tracking sheet, but the first-print digital
review should include generated plain-Python CadQuery bounds evidence for every
installed, service, and negative-review mode:

```bash
uv run python scripts/write_row_coupon_first_print_service_state_review.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv \
  --bounds-evidence-dir data/measurements/YYYY-MM-DD_one_row_coupon_service_state_bounds

uv run python scripts/audit_row_coupon_first_print_service_state_review.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv \
  --require-service-state-review-ready
```

The generated-bounds worksheet should report `worksheet_valid: true` and
`service_state_review_ready: true` only when every pass row references an
existing screenshot or bounds CSV, and every bounds CSV has matching mode
metadata, positive part bounds, absent expected-removed parts, and present
negative-review witness parts. Each row also names the physical acceptance gate
that owns the installed/service/negative-state claim. This is a digital review
surface; it does not mark any physical gate passed.

Before accepting Gate 2 dry assembly, run the combined readiness audit. Do not
use the Gate 2 dry assembly worksheet alone to claim assembly readiness; every
Gate 2 pass row depends on split Gate 1 print-QC readiness, ready installed
nonprinted items, and ready installed/service/negative-review mode evidence.

```bash
uv run python scripts/audit_row_coupon_first_print_y_split_gate2_dry_assembly_readiness.py \
  --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv \
  --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv \
  --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --gate2-dry-assembly data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv \
  --install-inventory data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv \
  --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md \
  --require-dry-assembly-ready
```

Before accepting Gate 3 OT-2 placement, run the combined placement-readiness
audit. Do not use the Gate 3 placement worksheet alone to claim OT-2 placement;
every Gate 3 pass row depends on Gate 2 dry-assembly readiness.

```bash
uv run python scripts/audit_row_coupon_first_print_y_split_gate3_placement_readiness.py \
  --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv \
  --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv \
  --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --gate2-dry-assembly data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv \
  --install-inventory data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv \
  --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv \
  --gate3-placement data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md \
  --require-placement-ready
```

Before accepting Gate 4 wet/dry witness evidence, run the combined
wet/dry-readiness audit. Do not use the Gate 4 worksheet alone to claim
production wet/dry isolation; every Gate 4 pass row depends on Gate 3 placement
readiness.

```bash
uv run python scripts/audit_row_coupon_first_print_y_split_gate4_wet_dry_witness_readiness.py \
  --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv \
  --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv \
  --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --gate2-dry-assembly data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv \
  --install-inventory data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv \
  --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv \
  --gate3-placement data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv \
  --gate4-wet-dry-witness data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md \
  --require-wet-dry-witness-ready
```

Before accepting Gate 5 consumable/puncture evidence, run the combined
consumable-readiness audit. Do not use the Gate 5 worksheet alone to claim
production puncture access or consumable compatibility; every Gate 5 pass row
depends on Gate 4 wet/dry witness readiness.

```bash
uv run python scripts/audit_row_coupon_first_print_y_split_gate5_consumable_puncture_readiness.py \
  --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv \
  --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv \
  --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --gate2-dry-assembly data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv \
  --install-inventory data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv \
  --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv \
  --gate3-placement data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv \
  --gate4-wet-dry-witness data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv \
  --gate5-consumable-puncture data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md \
  --require-consumable-puncture-ready
```

Before accepting Gate 6 sensor/thermal evidence, run the combined
sensor-readiness audit. Do not use the Gate 6 worksheet alone to claim sensor
installation, gas response, harness continuity, cable dress, or thermal-proxy
readiness; every Gate 6 pass row depends on Gate 5 consumable/puncture
readiness and a real sensor/electrical install inventory with no dimensional
electronics or sensor blanks.

```bash
uv run python scripts/audit_row_coupon_first_print_y_split_gate6_sensor_thermal_readiness.py \
  --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv \
  --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv \
  --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv \
  --gate2-dry-assembly data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv \
  --install-inventory data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv \
  --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv \
  --gate3-placement data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv \
  --gate4-wet-dry-witness data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv \
  --gate5-consumable-puncture data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv \
  --gate6-sensor-thermal data/measurements/YYYY-MM-DD_one_row_coupon_gate6_sensor_thermal.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md \
  --require-sensor-thermal-ready
```

Before accepting the one-row coupon as a production-operating prototype, run
the top-level operating-prototype acceptance audit. This is the final evidence
surface; it requires print-start artifacts plus the complete split Gate 1-6
physical evidence chain, a real sensor/electrical install inventory, and
`operating_prototype_ready: true`.

```bash
uv run python scripts/audit_row_coupon_first_print_y_split_operating_prototype_acceptance.py \
  --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md \
  --require-operating-prototype-ready
```

Run the cross-artifact preflight audit before slicing or printing:

```bash
uv run python scripts/audit_row_coupon_first_print_preflight.py \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md
```

After preflight passes and the queued STLs are sliced, generate or update the
sliced-output worksheet and audit it before starting the print:

```bash
uv run python scripts/write_row_coupon_first_print_sliced_outputs.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_sliced_outputs.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md

uv run python scripts/audit_row_coupon_first_print_sliced_outputs.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_sliced_outputs.csv \
  --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md
```

Use the `Slicer Queue: Printed Polymer Parts` section as the production print
queue. Do not print COTS consumables, electronics, service tubing, or validation
bodies as production parts.

Print or procure only the minimum parts needed to exercise the real assembly
tree:

```text
printed:
  deck_pods
  plate_support_frame
  wet_chamber_frame
  lid_manifold_shell
  lid_cover
  lower_harness_cover
  lid_harness_cover
  printed_lower_sensor_connector_shroud
  printed_lid_sensor_connector_shrouds
  printed_gas_pcb_keeper_doors
  printed_sample_relief_cap
  printed_wedge_locks

compressible / flexible:
  lower_gasket
  upper_gasket
  gas_pcb_interface_gaskets
  ir_thermopile_face_gaskets

COTS / electronics / service:
  CellVis P96-1.5H-N plates
  Cole-Parmer 1292006 round pre-slit silicone mats
  gas service tubing matching the CAD first-build ID/OD assumption or measured replacement
  gas sensor PCBs or dimensionally faithful cartridge blanks
  SHT41 headspace microcarriers or dimensionally faithful carriers
  TO-39 IR thermopiles or measured package blanks
  row-end electrical service cable pigtails
```

If a real sensor is unavailable, a blank may prove only mechanical envelope and
service path. It does not prove sensing, sealing around a real package, thermal
response, or electrical durability.

The install inventory covers every nonprinted installed artifact in the CAD
tree. COTS consumables must be real parts to pass inventory; tubing may be a
measured replacement; electronics and sensor packages may use dimensionally
faithful blanks only with explicit mechanical-only notes. Those blanks are
accepted for dry mechanical gates only; Gate 6 and operating-prototype
acceptance require `real_sensor_inventory_ready: true`.

The preflight audit is a pre-print claim only. Before slicing, it must report
`preprint_ready: true`, `print_start_ready: false`, `gate1_pass_ready: false`,
`gate2_dry_assembly_pass_ready: false`, `gate3_placement_pass_ready: false`,
`gate4_wet_dry_witness_pass_ready: false`,
`gate5_consumable_puncture_pass_ready: false`,
`gate6_sensor_thermal_pass_ready: false`, `install_inventory_ready: false`,
`service_state_review_ready: true`, and zero physical gate passes before the
first print begins. `preprint_ready` is allowed to become true only after the
linked `Params file` hash matches the live `Params SHA256`, the generated output
timestamp matches the current generated CAD package, every generated Gate 1-6
CAD target section in the record matches the current params/layout, the linked
sliced-output worksheet, Gate 2 dry assembly worksheet, Gate 3 placement
worksheet, Gate 4 wet/dry witness worksheet, Gate 5 consumable/puncture
worksheet, and Gate 6 sensor/thermal worksheet are valid even if not yet ready,
the service-state review worksheet is ready with linked screenshot or generated
bounds evidence for every mode, and the `Printer / material / profile` session
field matches the selected passing row in the slicer setup worksheet. The
selected printer bed must also resolve from the recorded profile source and fit
every queued printed STL in any XY rotation.
If bed fit fails, the split-plan worksheet records the minimum Y-axis segment
count that would fit the selected bed. The Y-split artifact audit can prove
that generated split STEP/STL files exist and fit the selected bed, but preflight
still blocks while the active slicer queue contains the monolithic oversized
STLs. A split queue, split sliced-output worksheet, and split Gate 1 QC worksheet
can become the active preflight path only when `Active print queue mode` is set
to `split_y`; print-start still requires sliced-output hashes while downstream
physical gates remain false until measured evidence is entered.

The sliced-output worksheet is a post-preflight, pre-print claim. It must report
`worksheet_valid: true`, `sliced_outputs_ready: true`, and
`print_start_ready: true` before print start. Blank rows can be valid, but they
are not print-ready. After slicing, rerun the preflight with
`--require-sliced-outputs-ready` so the first print cannot start from a valid
but unsliced queue.

## Gate 0: CAD Artifact Identity

Pass only if:

- `uv run ruff check .` passes;
- `uv run pytest tests/test_row_coupon_cad.py -q` passes from the same worktree;
- `uv run python scripts/generate_row_coupon.py` regenerates the output package;
- `uv run python scripts/audit_row_coupon_first_print_package.py` passes against
  the generated output package;
- if selected-bed split artifacts are used, `uv run python
  scripts/audit_row_coupon_first_print_y_split_artifacts.py --require-ready`
  reports all split files present, selected-bed-fit, and covering every
  selected-bed oversized source part;
- if a split-artifact queue is prepared, the split queue audit reports all
  expected split/small printed STLs present with zero source, missing, extra,
  or hash issues;
- if a split sliced-output worksheet is prepared, its audit reports
  `worksheet_valid: true` against the split queue while still allowing
  `sliced_outputs_ready: false` before real sliced files exist;
- `uv run python scripts/scaffold_row_coupon_first_print_record.py` creates the
  measurement record with params checksum and Gate 0 audit snapshot;
- `uv run python cad/view_one_row_coupon.py --show-validation-tools` loads and
  lists the validation bodies;
- the measurement record stores params checksum, output artifact date, and any
  local worktree identifier available.

Failure blocks print authorization because the print would not correspond to the
verified CAD state.

## Gate 1: Print QC

The scaffolded measurement record includes CAD target bounds for printed and
compressible/flexible parts. Use those targets for caliper comparison, but do
not treat their presence as physical evidence.

The Gate 1 QC worksheet is a CSV entry surface generated from the same CAD
targets. Keep its measured fields blank and every row `not_tested` until the
printed or flexible part has been inspected.

The blank pre-print worksheet should audit as `worksheet_valid: true` and
`gate1_pass_ready: false`. Gate 1 is pass-ready only when every production
print/flexible target row is measured, within tolerance, marked `pass`, and
links to an existing nonempty evidence file.
For split-Y prints, the combined Gate 1 print-QC audit must also report
`print_qc_ready: true`; a measurement row cannot pass unless the matching print
batch traveler row is `printed` and links to an existing nonempty print evidence
file.

The required `printability_support_cleanup_check` validation body is the Gate 1
review map for post-print cleanup blockers: support scars on gasket lands,
support debris in wedge slide paths, blocked side-gas barbs, blocked sensor
pockets, bridged wet/dry gutters, or split-segment edge cleanup that removes an
authority feature. Any of those findings blocks Gate 1 pass.

Record:

| Item | Tool | Initial Gate |
|---|---|---|
| Overall X/Y/Z bounds for each printed part | calipers | within +/- 1.0 mm, or revise measured safety envelope |
| Deck-pod shoe dimensions | calipers | fit the modeled deck-slot footprint without filing |
| Deck-pod vertical interference | visual/feeler gauge | no contact with OT-2 frame protrusions outside intended pod surfaces |
| Gasket land flatness | straightedge/feeler gauge | no visible ridge, lift, or support scar on seal land |
| Wedge lock slide fit | hand cycling | inserts/removes without cracking, tools, screws, or glue |
| Sample/relief cap lip | calipers/hand cycling | seats and removes without tearing or permanent visible set |
| Gas barb/stem print quality | visual/calipers | bore open, barb not crushed, tube can seat without splitting print |
| IR/SHT/gas sensor pockets | visual/calipers | package or measured blank inserts without trimming |
| Harness covers and shrouds | hand cycling | snap/seat without adhesive and without pinching cable envelope |
| Dry-bay aperture thresholds/gutters | visual | no support debris bridging gutter to aperture |

Any trimming, glue, threaded hardware, or metal reinforcement used to pass this
gate must be recorded as a design failure, not as an accepted production method.

## Gate 2: Dry Assembly Fit

Assemble without liquid, powered electronics, or OT-2 motion:

1. Seat deck pods and plate support frame on a flat surface.
2. Install lower gasket, wet chamber frame, one CellVis plate per tile, and one
   Cole-Parmer mat per plate.
3. Install lid manifold shell, upper gasket, lid cover, sample/relief cap, and
   wedge locks.
4. Install side gas tubes, sensor cartridges/carriers/packages, cable pigtails,
   and harness covers.
5. Remove and reinstall plates, septum mats, gas PCB cartridges, SHT41 carriers,
   IR thermopiles, sample/relief cap, and wedge locks at least five cycles each.

The scaffold inserts Gate 2 CAD dry assembly targets after the dry-fit cycle
table. Treat them as service targets for stack order, plate/mat cycling, plate
support datum, locator rail fit, gasket squeeze budget, wedge-lock travel,
omitted latch-span inspection, side gas tube dress, electrical pigtail dress,
sensor blank/package installation, and dry-bay openness. They do not mark Gate
2 passed.

Generate the linked Gate 2 dry assembly worksheet from those same targets and
keep rows `not_tested` until the printed dry assembly has measured values or
observations plus evidence paths. The blank worksheet may be valid for
preflight, but Gate 2 is not pass-ready until every row has evidence.

Pass only if:

- plates load from the intended service direction and are supported without
  contacting the optical bottom where the CAD assumes clearance;
- septum mats can be inserted, swapped, and reseated without lifting the plate;
- wedge locks create visible closure without bowing the plate stack;
- service leads remain in their modeled side/end exits and do not cross the top
  pipette field;
- sensor modules can be installed and removed without removing unrelated major
  parts;
- the dry bay remains visually open for the observer envelope.

## Gate 3: OT-2 Placement And No-Motion Clearance

This gate is placement-only unless the OT-2 bridge readiness workflow separately
authorizes motion.

The scaffold inserts Gate 3 CAD placement targets below the record table. Treat
them as measurement targets for deck-to-top height, assembly footprint, adjacent
slot service clearance, operating service-dress envelope, conservative OT-2
toolhead swept body, pipette target count, and dry-bay protected footprint; they
do not mark Gate 3 passed.
Generate the linked Gate 3 placement worksheet from those same targets and keep
it `not_tested` until the printed, dressed assembly is seated on the OT-2 deck.
Rows marked `pass` require measured evidence and a photo, log, or measurement
path.

Record:

| Item | Tool | Initial Gate |
|---|---|---|
| Deck seating in target slot | visual/feeler gauge | no rocking and no frame-protrusion interference |
| Adjacent-slot tube/cable dress | visual/photo | services remain inside the exported operating service-dress body and intended overhead or row-end route |
| Pipette top-field obstruction | visual/photo | no cap, latch, tube, cable, or connector over septum targets |
| Camera visibility of fiducials/assembly | OT-2 camera or external camera | evidence image stored |
| Assembly high point | calipers | no higher than CAD bound plus 1.0 mm |

If any tube or cable must be hand-held to pass, the service routing fails.

## Gate 4: Passive Leak And Wet/Dry Witness

Run `docs/protocols/row_coupon_passive_leak_wet_dry_validation.md` after
Gates 1-3 pass and before powered sensors or biology. The passive leak
protocol owns dye challenge, condensate challenge, dry-bay ingress inspection,
and wet/dry witness evidence paths.

Use water with dye before electronics or biology.

The scaffold inserts Gate 4 CAD wet/dry witness targets after the record table.
Treat them as countable inspection targets for the required headspace barrier
and shared-volume bodies, required dry-bay envelope and boundary bodies, side
gas witnesses, sample/relief witnesses, gasket-tab witnesses, aperture
thresholds, and aperture-adjacent gutters; they do not mark Gate 4 passed.

Generate the linked Gate 4 wet/dry witness worksheet from those same targets
and keep rows `not_tested` until the printed assembly has dye, condensate,
debris, headspace-continuity, dry-bay boundary clearance, or dry-bay ingress
observations plus evidence paths. The blank worksheet may be valid for
preflight, but Gate 4 is not pass-ready until every row has evidence.

1. Apply small droplets to side gas fitting exteriors, sample/relief cap seat,
   gasket-tab roots, and optical-aperture-adjacent wet surfaces.
2. Inspect whether dye follows the modeled witness gutters and dams.
3. Add shallow water to representative plate wells under installed septum mats.
4. Hold the assembled coupon in a warm humid environment long enough to show
   first condensation behavior.
5. Inspect dry bay, IR pockets, gas PCB pockets, SHT41 pockets, harness channels,
   and connector shrouds.

Pass only if visible wetting remains outside dry optics/electronics volumes or
is captured by a visible witness feature. Any invisible wet path into the dry
bay, sensor pocket, or harness channel blocks the design claim.

## Gate 5: Consumable And Puncture Link

Run `docs/protocols/row_coupon_consumable_puncture_validation.md` after Gates
1-4 pass. The puncture protocol owns measured mat dimensions, plate shift,
slit behavior, and first dye transfer through the mat.

The scaffold inserts Gate 5 CAD consumable/puncture targets after the record
table. Treat them as measurement targets for the required consumable metrology
gauge, required all-well puncture swept-path body, plate lot fit, placeholder
mat dimensions, puncture force, repeat-cycle, and plate-shift limits; they do
not mark Gate 5 passed.

Generate the linked Gate 5 consumable/puncture worksheet from those same
targets and keep rows `not_tested` until required-gauge inspection, real
plate/mat metrology, all-well swept-path access, puncture-force, repeat-cycle,
and plate-shift evidence paths exist. Blank may be valid for preflight, but
Gate 5 is not pass-ready until every row has evidence.

Do not treat CAD septum access as proven until the puncture record passes.

## Gate 6: Sensor And Thermal Link

This gate only authorizes the next measurement plan, not final sensing claims.

The scaffold inserts Gate 6 CAD sensor/thermal targets after the record table.
Use those rows as mechanical installation targets for reversible sensor
workflow, gas-PCB cartridge sealing, SHT41 membrane exposure, IR aperture and
gasket seating, harness continuity, connector service clearance, service cable
bend relief, IR proxy FOV, required observer front-end/carriage/raceway
envelopes, observer kinematic split, and the edge-to-center thermal plan. They
do not mark Gate 6 passed and do not prove gas response, RH response, CO2
control, IR calibration, observer performance, or biology readiness.

Generate the linked Gate 6 sensor/thermal worksheet from those same targets and
keep rows `not_tested` until package installation, gas-PCB cartridge sealing,
SHT41 carrier exposure, IR gasket/FOV, harness continuity, connector service
clearance, cable dress, observer envelope, observer kinematic split, and
thermal-proxy plan evidence paths exist. Dimensionally faithful blanks may prove
only mechanical envelope through the dry assembly chain; Gate 6 readiness stays
false until the install inventory has real electronics, electrical-service, IR,
gas-sensor, and headspace-sensor rows with no dimensional blanks.

Record:

| Item | Tool | Initial Gate |
|---|---|---|
| Gas PCB cartridge seating | visual/calipers | aperture aligned, gasket compressed, keeper retained |
| Headspace SHT41 carrier seating | visual/calipers | membrane aperture exposed, PCB not wettable by pooling |
| IR package seating | visual/calipers | gasket centered, lens not obstructed, drip collar clear |
| Cable continuity during service cycling | multimeter/log | no dropout during five install/remove cycles |
| IR FOV spot vs cell-plane overlay | CAD + photo/measurement | protocol acknowledges margin proxy, not direct cell reading |
| Edge-to-center thermal plan | written setup | plate-margin IR reading will be correlated to cell-plane/reference sensors |

Final gas response, RH response, CO2 control, IR calibration, and biology
readiness remain blocked until separate powered tests pass.

## Decision Rules

Use these outcomes after the gate sequence:

```text
pass:
  physical evidence supports printing/assembling the current CAD as the next PoC

revise:
  measured failure changes a CAD-controlled interface, envelope, seal, service path,
  or printed retention feature

defer:
  a feature is not required for the next physical proof and should not gain more CAD
  fidelity now

block:
  a wet/dry, OT-2, printability, service, or safety failure prevents responsible
  robot, sensor, or biology work
```

The next CAD cycle should be driven by `revise` findings, not by visual
completeness.

## Measurement Record Skeleton

Create:

```text
data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md
```

Template:

```text
data/measurements/templates/one_row_coupon_first_print_readiness.md
```

Preferred command:

```bash
uv run python scripts/scaffold_row_coupon_first_print_record.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md
```

The scaffold only records CAD package identity and audit status. It leaves Gate
0-6 results as `not_tested` until physical evidence is entered.

Minimum sections if the template is not available:

```text
# One-Row Coupon First-Print Readiness

Date:
Operator:
Printer/material/profile:
Params file:
Params SHA256:
Generated output timestamp:
CQ viewer mode inspected:
Service state review worksheet:
OT-2 robot/slot if used:
Consumable lot numbers:
Sensor package or blank identifiers:

## Gate 0 CAD Artifact Identity

## Gate 1 Print QC

## Gate 2 Dry Assembly Fit

## Gate 3 OT-2 Placement And No-Motion Clearance

## Gate 4 Passive Leak And Wet/Dry Witness

## Gate 5 Consumable And Puncture Link

## Gate 6 Sensor And Thermal Link

## Decision

pass | revise | defer | block

## CAD Changes Authorized By Evidence

## Features Explicitly Deferred To Avoid Overengineering
```
