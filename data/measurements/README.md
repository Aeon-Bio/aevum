# Measurements

Use this folder for measured data from real parts and robot tests.

Create one file per measurement session, for example:

```text
2026-05-02_p300_tip_measurements.md
2026-05-02_cole_parmer_mat_measurements.md
2026-05-02_first_fixture_ot2_run.md
2026-06-02_one_row_coupon_first_print.md
```

Templates live under `templates/`. For the production-operating row coupon, use:

```bash
uv run python scripts/scaffold_row_coupon_first_print_record.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md
```

The scaffold starts from `templates/one_row_coupon_first_print_readiness.md`,
fills CAD package identity and Gate 1 CAD target bounds, and leaves physical
gates as `not_tested`.

Generate the first-print package handoff manifest before slicing:

```bash
uv run python scripts/write_row_coupon_first_print_package_manifest.py --overwrite
```

The manifest must keep procurement distinct from printing: COTS consumables are
real installed parts, service tubing is real tubing or measured replacement, and
electronics/sensor dimensional blanks are dry-fit references only until real
parts close Gate 6 and operating acceptance.

Then prepare the printed-STL-only slicer queue:

```bash
uv run python scripts/prepare_row_coupon_first_print_slicer_queue.py --overwrite
```

Audit that queue before slicing:

```bash
uv run python scripts/audit_row_coupon_first_print_slicer_queue.py
```

Generate the slicer setup worksheet and select exactly one setup row before
preflight:

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

The selector marks the matching row `selected=yes`, marks it `result=pass`,
marks other rows unselected, and writes the matching setup summary into
`Printer / material / profile`. Use `--setup-summary` or add printer/material/
print-profile filters if a slicer name is not unique.

Generate and audit the selected-bed split-plan worksheet before deciding between
a larger printer and split production CAD:

```bash
uv run python scripts/write_row_coupon_first_print_bed_fit_split_plan.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_bed_fit_split_plan.csv

uv run python scripts/audit_row_coupon_first_print_bed_fit_split_plan.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_bed_fit_split_plan.csv
```

If generated production Y-split CAD exists, audit the split STEP/STL files
before any split queue replacement:

```bash
uv run python scripts/audit_row_coupon_first_print_y_split_artifacts.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --require-ready
```

This only proves selected-bed fit and file presence for the split artifacts.
The active slicer queue remains the authority for preflight until it is
intentionally replaced with split artifacts and re-audited.

After the split-artifact audit is ready, prepare and audit the alternate split
slicer queue:

```bash
uv run python scripts/prepare_row_coupon_first_print_y_split_slicer_queue.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv \
  --overwrite

uv run python scripts/audit_row_coupon_first_print_y_split_slicer_queue.py \
  --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv
```

Then generate and audit the split sliced-output worksheet from that alternate
queue:

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

The split queue and split sliced-output worksheet are evidence for an explicit
queue replacement path. They do not change preflight until the active record
links and checks intentionally refer to the split queue. After batch slicing,
the split sliced-output audit must report `sliced_outputs_ready: true` before
strict preflight can authorize print start.

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

Generate the blank Gate 1 QC worksheet before printing:

```bash
uv run python scripts/write_row_coupon_first_print_gate1_qc_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate1_qc.csv
```

The worksheet is a target-and-entry form only. It does not mark Gate 1 passed
until physical measurements and evidence paths are entered.

Audit the worksheet before and after measurement entry:

```bash
uv run python scripts/audit_row_coupon_first_print_gate1_qc_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate1_qc.csv
```

Every passing Gate 1 row requires measured X/Y/Z values within tolerance and an
`evidence_path` that resolves to an existing nonempty file; blank pre-print rows
remain valid but not ready.

The blank pre-print worksheet should report `worksheet_valid: true` and
`gate1_pass_ready: false`.

Generate the blank Gate 2 dry assembly worksheet before dry assembly:

```bash
uv run python scripts/write_row_coupon_first_print_gate2_dry_assembly_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv
```

Audit the worksheet before and after dry-fit evidence is entered:

```bash
uv run python scripts/audit_row_coupon_first_print_gate2_dry_assembly_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv
```

The blank worksheet should report `worksheet_valid: true` and
`gate2_pass_ready: false`. It becomes pass-ready only after the printed dry
assembly, consumables, services, and sensor packages/blanks have measured or
photo evidence for every CAD dry-assembly target.

Generate the blank Gate 3 OT-2 placement worksheet before deck placement:

```bash
uv run python scripts/write_row_coupon_first_print_gate3_placement_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv
```

Audit the worksheet before and after physical placement evidence is entered:

```bash
uv run python scripts/audit_row_coupon_first_print_gate3_placement_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv
```

The blank worksheet should report `worksheet_valid: true` and
`gate3_pass_ready: false`. It becomes pass-ready only after the printed,
dressed assembly is seated on the OT-2 deck and each CAD placement target has
measured/photo evidence. The Gate 3 targets distinguish the 384 tip puncture
locations from the larger conservative two-pipette OT-2 toolhead swept body; do
not replace that envelope or mark placement passed without measured toolhead
clearance evidence.

Generate the blank Gate 4 wet/dry witness worksheet before wet testing:

```bash
uv run python scripts/write_row_coupon_first_print_gate4_wet_dry_witness_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv
```

Audit the worksheet before and after dye or condensate evidence is entered:

```bash
uv run python scripts/audit_row_coupon_first_print_gate4_wet_dry_witness_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv
```

The blank worksheet should report `worksheet_valid: true` and
`gate4_pass_ready: false`. It becomes pass-ready only after wet collectors,
inboard dams, aperture thresholds, witness gutters, and the protected dry bay
have measured or photo evidence.

Use the linked passive leak/wet-dry protocol and template for the physical
dye/condensate run:

```text
docs/protocols/row_coupon_passive_leak_wet_dry_validation.md
data/measurements/templates/row_coupon_passive_leak_wet_dry_validation.md
```

Generate the blank Gate 5 consumable/puncture worksheet before consumable
metrology or puncture testing:

```bash
uv run python scripts/write_row_coupon_first_print_gate5_consumable_puncture_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv
```

Audit the worksheet before and after plate/mat or puncture evidence is entered:

```bash
uv run python scripts/audit_row_coupon_first_print_gate5_consumable_puncture_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv
```

The blank worksheet should report `worksheet_valid: true` and
`gate5_pass_ready: false`. It becomes pass-ready only after real plate/mat
metrology, all-well puncture access, puncture-force, repeat-cycle, and
plate-shift evidence exists for every CAD/protocol target.

Generate the blank Gate 6 sensor/thermal worksheet before powered sensor or
thermal-proxy planning claims:

```bash
uv run python scripts/write_row_coupon_first_print_gate6_sensor_thermal_worksheet.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_gate6_sensor_thermal.csv
```

Audit the worksheet before and after sensor or thermal-plan evidence is entered:

```bash
uv run python scripts/audit_row_coupon_first_print_gate6_sensor_thermal_worksheet.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate6_sensor_thermal.csv
```

The blank worksheet should report `worksheet_valid: true` and
`gate6_pass_ready: false`. It becomes pass-ready only after sensor package or
blank installation, gas-PCB cartridge sealing, SHT41 carrier exposure, IR
gasket/FOV, harness continuity, cable dress, and thermal-proxy plan evidence
exists for every CAD/protocol target. The combined Gate 6 readiness audit still
blocks on dimensional electronics or sensor blanks; final sensor/thermal
readiness requires `real_sensor_inventory_ready: true`.

Every passing Gate 2-6 physical worksheet row requires a measured value or
observation plus an `evidence_path` that resolves to an existing nonempty file.
Blank pre-test rows remain valid but not ready.

Generate the nonprinted installed-item inventory before dry assembly:

```bash
uv run python scripts/write_row_coupon_first_print_install_inventory.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv
```

Audit that inventory before assembly:

```bash
uv run python scripts/audit_row_coupon_first_print_install_inventory.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv
```

The blank inventory should report `worksheet_valid: true` and
`install_inventory_ready: false`. It becomes ready only after COTS consumables,
tubing, electronics, cables, sensor packages, or dimensionally faithful blanks
are identified, keep their row-level `operating_requirement`, are installed in
an allowed form, and are backed by an `evidence_path` that resolves to an
existing nonempty file for the physical item or blank. Dimensional electronics
and sensor blanks support dry mechanical fit only; Gate 6 and
operating-prototype acceptance require those rows to be real parts.

Generate the service-state review worksheet before physical assembly. For the
first-print digital review, include generated plain-Python CadQuery bounds
evidence for every installed, service, and negative-review viewer mode:

```bash
uv run python scripts/write_row_coupon_first_print_service_state_review.py \
  --output data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv \
  --bounds-evidence-dir data/measurements/YYYY-MM-DD_one_row_coupon_service_state_bounds
```

Audit it with the ready requirement:

```bash
uv run python scripts/audit_row_coupon_first_print_service_state_review.py \
  --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv \
  --require-service-state-review-ready
```

The bounds-backed worksheet should report `worksheet_valid: true` and
`service_state_review_ready: true` only when every pass row references an
existing screenshot or bounds CSV, and every bounds CSV has matching mode
metadata, matching acceptance-gate ownership, positive part bounds, absent
expected-removed parts, and present negative-review witness parts. It does not
mark any physical Gate 1-6 row passed.

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

The preflight should report `preprint_ready: true` while Gates 1-6 remain
unpassed. It must not report ready until the live `Params SHA256` matches the
linked `Params file`, `Generated output timestamp` matches the current generated
CAD package, `Printer / material / profile` records the actual selected slicing
setup, and `service_state_review_ready: true` proves every installed, service,
and negative-review viewer mode has linked screenshot or generated bounds
evidence. The selected printer bed must also resolve from the profile source and
fit every queued printed STL in any XY rotation. If bed fit fails, the
split-plan worksheet records the minimum Y-axis segment count that would fit the
selected bed, but this is not print authorization. Do not slice until a larger
proven printer is selected or split production CAD/STLs exist with explicit
retention, service, sealing evidence, an audited split queue, and a matching
split sliced-output worksheet path.

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

The blank worksheet should report `worksheet_valid: true` and
`sliced_outputs_ready: false`. It becomes ready only when each queued printed
STL row has a selected setup summary, a sliced output path, a matching sliced
output hash, and `result=pass`. After slicing, rerun preflight with
`--require-sliced-outputs-ready` and require `print_start_ready: true` before
starting the print.

Minimum measurements needed:

- P300 tip model and length.
- Tip outer diameter near the nozzle and near mat-contact depth.
- Cole-Parmer mat thickness, plug geometry, and slit geometry.
- Actual plate dimensions once selected.
- Plate measurement backlog lives under `plate_profiles/`. Published labware
  dimensions remain in CAD params; measure only unknown geometry or fit issues.
- Maximum comfortable raised stack height.
- OT-2 camera capture path, image settings, and fixture/target evidence.
- Camera vision analysis records and motion-gate status.
- No-motion maintenance-run, command-key, and custom-labware definition probes.
- Collision notes.
