# One-Row Coupon First-Print Readiness

Protocol:
`docs/protocols/one_row_coupon_first_print_readiness.md`

This record is for a real printed one-row coupon. Do not mark a gate passed from
CAD alone. Use `not_tested`, `pass`, `revise`, `defer`, or `block` for each gate.

## Session Identity

| Field | Value |
|---|---|
| Date |  |
| Operator |  |
| Printer / material / profile |  |
| Active print queue mode |  |
| Params file | `cad/one_row_coupon.params.json` |
| Params SHA256 |  |
| CAD source commit / worktree note |  |
| Generated output timestamp |  |
| Print/procurement manifest |  |
| Slicer queue |  |
| Split slicer queue |  |
| Slicer setup worksheet |  |
| Bed-fit split plan |  |
| Sliced output worksheet |  |
| Split sliced output worksheet |  |
| Split print batch traveler |  |
| Split Gate 1 QC worksheet |  |
| Gate 1 QC worksheet |  |
| Gate 2 dry assembly worksheet |  |
| Gate 3 placement worksheet |  |
| Gate 4 wet/dry witness worksheet |  |
| Gate 5 consumable/puncture worksheet |  |
| Gate 6 sensor/thermal worksheet |  |
| Install inventory worksheet |  |
| Service state review worksheet |  |
| CQ viewer mode inspected |  |
| OT-2 robot / slot if used |  |
| Consumable lot numbers |  |
| Sensor package or blank identifiers |  |
| Measurement images folder |  |

## Gate Summary

| Gate | Result | Evidence path / note |
|---|---|---|
| Gate 0 CAD Artifact Identity | not_tested |  |
| Gate 1 Print QC | not_tested |  |
| Gate 2 Dry Assembly Fit | not_tested |  |
| Gate 3 OT-2 Placement And No-Motion Clearance | not_tested |  |
| Gate 4 Passive Leak And Wet/Dry Witness | not_tested |  |
| Gate 5 Consumable And Puncture Link | not_tested |  |
| Gate 6 Sensor And Thermal Link | not_tested |  |

## Gate 0 CAD Artifact Identity

| Check | Result | Evidence |
|---|---|---|
| `uv run ruff check .` | not_tested |  |
| `uv run pytest tests/test_row_coupon_cad.py -q` | not_tested |  |
| `uv run python scripts/generate_row_coupon.py` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_package.py` | not_tested |  |
| `uv run python scripts/scaffold_row_coupon_first_print_record.py` | not_tested |  |
| `uv run python scripts/write_row_coupon_first_print_package_manifest.py --overwrite` | not_tested | manifest separates printed, flexible, COTS, service-tubing, electronics/sensor, and validation bodies; nonprinted rows must state operating install requirements and cannot imply blanks are final operating parts |
| `uv run python scripts/prepare_row_coupon_first_print_slicer_queue.py --overwrite` | not_tested |  |
| `uv run python scripts/write_row_coupon_first_print_slicer_setup.py --output data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_slicer_setup.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv` | not_tested |  |
| `uv run python scripts/select_row_coupon_first_print_slicer_setup.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md --slicer-name SLICER_NAME` | not_tested | selects one audited setup and updates Printer / material / profile |
| `uv run python scripts/write_row_coupon_first_print_bed_fit_split_plan.py --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv --output data/measurements/YYYY-MM-DD_one_row_coupon_bed_fit_split_plan.csv` | not_tested | generated selected-bed split decision worksheet from queued printed parts |
| `uv run python scripts/audit_row_coupon_first_print_bed_fit_split_plan.py --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_bed_fit_split_plan.csv` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_y_split_artifacts.py --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv --require-ready` | not_tested | proves generated split STEP/STL files exist and fit selected bed; does not replace the active slicer queue |
| `uv run python scripts/prepare_row_coupon_first_print_y_split_slicer_queue.py --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv --overwrite` | not_tested | creates alternate split-artifact slicer queue; does not replace active preflight queue unless record/preflight are intentionally changed |
| `uv run python scripts/audit_row_coupon_first_print_y_split_slicer_queue.py --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv` | not_tested |  |
| `uv run python scripts/write_row_coupon_first_print_y_split_sliced_outputs.py --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv --output data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | generated blank split sliced-output worksheet from alternate split queue |
| `uv run python scripts/slice_row_coupon_first_print_y_split_slicer_queue.py --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv --sliced-dir outputs/sliced/first_print_y_split --output data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --overwrite` | not_tested | slices split queue STLs and rewrites split sliced-output worksheet with G-code paths and hashes |
| `uv run python scripts/audit_row_coupon_first_print_y_split_sliced_outputs.py --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested |  |
| `uv run python scripts/write_row_coupon_first_print_y_split_gate1_qc_worksheet.py --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv --output data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv` | not_tested | generated blank split Gate 1 QC worksheet from alternate split queue target bounds |
| `uv run python scripts/audit_row_coupon_first_print_y_split_gate1_qc_worksheet.py --slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv` | not_tested | pass rows require measured X/Y/Z values and an evidence_path resolving to an existing nonempty file |
| `uv run python scripts/write_row_coupon_first_print_y_split_print_batch_traveler.py --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv --output data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | generated physical print traveler from ready split G-code rows and split Gate 1 QC targets |
| `uv run python scripts/audit_row_coupon_first_print_y_split_print_batch_traveler.py --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md --require-handoff-ready` | not_tested | printed rows require print_evidence_path resolving to an existing nonempty file |
| `uv run python scripts/audit_row_coupon_first_print_y_split_gate1_print_qc.py --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | combined post-print Gate 1 audit; requires evidenced Gate 1 rows and printed traveler rows with existing nonempty evidence files before Gate 1 pass can be accepted |
| `uv run python scripts/write_row_coupon_first_print_sliced_outputs.py --output data/measurements/YYYY-MM-DD_one_row_coupon_sliced_outputs.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | generated blank sliced-output worksheet from queued STLs |
| `uv run python scripts/audit_row_coupon_first_print_sliced_outputs.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_sliced_outputs.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested |  |
| `uv run python scripts/write_row_coupon_first_print_gate1_qc_worksheet.py --output data/measurements/YYYY-MM-DD_one_row_coupon_gate1_qc.csv` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_gate1_qc_worksheet.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate1_qc.csv` | not_tested | pass rows require measured X/Y/Z values and an evidence_path resolving to an existing nonempty file |
| `uv run python scripts/write_row_coupon_first_print_gate2_dry_assembly_worksheet.py --output data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_gate2_dry_assembly_worksheet.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv` | not_tested | pass rows require measured value and evidence_path resolving to an existing nonempty file |
| `uv run python scripts/write_row_coupon_first_print_gate3_placement_worksheet.py --output data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_gate3_placement_worksheet.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv` | not_tested | pass rows require measured value and evidence_path resolving to an existing nonempty file |
| `uv run python scripts/write_row_coupon_first_print_gate4_wet_dry_witness_worksheet.py --output data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_gate4_wet_dry_witness_worksheet.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv` | not_tested | pass rows require measured value and evidence_path resolving to an existing nonempty file |
| `uv run python scripts/write_row_coupon_first_print_gate5_consumable_puncture_worksheet.py --output data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_gate5_consumable_puncture_worksheet.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv` | not_tested | pass rows require measured value and evidence_path resolving to an existing nonempty file |
| `uv run python scripts/write_row_coupon_first_print_gate6_sensor_thermal_worksheet.py --output data/measurements/YYYY-MM-DD_one_row_coupon_gate6_sensor_thermal.csv` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_gate6_sensor_thermal_worksheet.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate6_sensor_thermal.csv` | not_tested | pass rows require measured value and evidence_path resolving to an existing nonempty file |
| `uv run python scripts/write_row_coupon_first_print_install_inventory.py --output data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_install_inventory.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv` | not_tested | pass rows require item identifier, matching operating_requirement, allowed installed_as, and evidence_path resolving to an existing nonempty file; dimensional electronics/sensor blanks prove dry mechanical fit only |
| `uv run python scripts/write_row_coupon_first_print_service_state_review.py --output data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv --bounds-evidence-dir data/measurements/YYYY-MM-DD_one_row_coupon_service_state_bounds` | not_tested | generates per-mode plain-Python CadQuery bounds evidence, records acceptance-gate ownership for each viewer mode, and marks viewer service/review rows pass; does not replace physical Gate 1-6 evidence |
| `uv run python scripts/audit_row_coupon_first_print_service_state_review.py --worksheet data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv --require-service-state-review-ready` | not_tested | verifies each pass row references an existing screenshot or generated bounds CSV with matching mode metadata, acceptance-gate ownership, and positive part bounds |
| `uv run python scripts/audit_row_coupon_first_print_y_split_gate2_dry_assembly_readiness.py --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --gate2-dry-assembly data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv --install-inventory data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | combined Gate 2 dry-assembly readiness audit; requires split Gate 1 print QC, installed-item inventory, and service-state review readiness before Gate 2 pass can be accepted |
| `uv run python scripts/audit_row_coupon_first_print_y_split_gate3_placement_readiness.py --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --gate2-dry-assembly data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv --install-inventory data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv --gate3-placement data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | combined Gate 3 placement readiness audit; requires Gate 2 dry assembly before OT-2 placement pass can be accepted |
| `uv run python scripts/audit_row_coupon_first_print_y_split_gate4_wet_dry_witness_readiness.py --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --gate2-dry-assembly data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv --install-inventory data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv --gate3-placement data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv --gate4-wet-dry-witness data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | combined Gate 4 wet/dry witness readiness audit; requires Gate 3 placement before wet/dry pass can be accepted |
| `uv run python scripts/audit_row_coupon_first_print_y_split_gate5_consumable_puncture_readiness.py --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --gate2-dry-assembly data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv --install-inventory data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv --gate3-placement data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv --gate4-wet-dry-witness data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv --gate5-consumable-puncture data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | combined Gate 5 consumable/puncture readiness audit; requires Gate 4 wet/dry witness before consumable/puncture pass can be accepted |
| `uv run python scripts/audit_row_coupon_first_print_y_split_gate6_sensor_thermal_readiness.py --gate1-qc data/measurements/YYYY-MM-DD_one_row_coupon_y_split_gate1_qc.csv --print-batch-traveler data/measurements/YYYY-MM-DD_one_row_coupon_y_split_print_batch_traveler.csv --sliced-outputs data/measurements/YYYY-MM-DD_one_row_coupon_y_split_sliced_outputs.csv --gate2-dry-assembly data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv --install-inventory data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv --gate3-placement data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv --gate4-wet-dry-witness data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv --gate5-consumable-puncture data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv --gate6-sensor-thermal data/measurements/YYYY-MM-DD_one_row_coupon_gate6_sensor_thermal.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | combined Gate 6 sensor/thermal readiness audit; requires Gate 5 consumable/puncture plus real sensor/electrical inventory before sensor/thermal pass can be accepted |
| `uv run python scripts/audit_row_coupon_first_print_y_split_operating_prototype_acceptance.py --service-state-review data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | top-level production-operating acceptance audit; requires service-state review readiness, print-start artifacts, real sensor/electrical inventory, and the complete Gate 1-6 physical evidence chain |
| `uv run python scripts/audit_row_coupon_first_print_slicer_queue.py` | not_tested |  |
| `uv run python scripts/audit_row_coupon_first_print_preflight.py --record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md` | not_tested | requires service_state_review_ready true before preprint_ready or print_start_ready can pass |
| `uv run python cad/view_one_row_coupon.py --show-validation-tools` | not_tested |  |
| Assembly STEP present | not_tested | `outputs/cad/aevum_one_row_coupon_assembly.step` |
| Validation STEP set present | not_tested |  |

## Gate 1 Print QC

The scaffold inserts CAD target bounds below this table. Treat them as caliper
targets only; they do not mark Gate 1 passed.

| Item | Measured value | Tool | Result | Notes |
|---|---:|---|---|---|
| Deck pods X/Y/Z bounds |  | calipers | not_tested |  |
| Plate support frame X/Y/Z bounds |  | calipers | not_tested |  |
| Wet chamber frame X/Y/Z bounds |  | calipers | not_tested |  |
| Lid manifold shell X/Y/Z bounds |  | calipers | not_tested |  |
| Lid cover X/Y/Z bounds |  | calipers | not_tested |  |
| Deck-pod shoe dimensions |  | calipers | not_tested | no filing |
| Deck-pod vertical interference |  | visual/feeler gauge | not_tested |  |
| Gasket land flatness |  | straightedge/feeler gauge | not_tested |  |
| Wedge lock slide fit |  | hand cycling | not_tested |  |
| Sample/relief cap lip |  | calipers/hand cycling | not_tested |  |
| Gas barb/stem print quality |  | visual/calipers | not_tested | bore open |
| Sensor pockets |  | visual/calipers | not_tested | package or blank inserts |
| Harness covers and shrouds |  | hand cycling | not_tested | no cable pinch |
| Dry-bay aperture thresholds/gutters |  | visual | not_tested | no support debris bridge |

## Gate 2 Dry Assembly Fit

The linked Gate 2 dry assembly worksheet is generated from the CAD dry
assembly targets below. Keep it `not_tested` until the printed assembly,
consumables, services, and sensor packages/blanks have measured or photo
evidence for each row.

| Check | Result | Evidence / notes |
|---|---|---|
| Plates load from intended service direction | not_tested |  |
| Plates supported without optical-bottom contact | not_tested |  |
| Septum mats insert, swap, and reseat without lifting plate | not_tested |  |
| Wedge locks close stack without bowing plate/mat | not_tested |  |
| Side gas tubes stay in modeled exits | not_tested |  |
| Electrical pigtails stay in modeled exits | not_tested |  |
| Gas PCB cartridges or blanks install/remove | not_tested |  |
| SHT41 carriers or blanks install/remove | not_tested |  |
| IR thermopiles or blanks install/remove | not_tested |  |
| Sample/relief cap installs/removes | not_tested |  |
| Dry bay remains visually open | not_tested |  |

Cycle count:

| Component | Required cycles | Completed cycles | Result |
|---|---:|---:|---|
| Plates | 5 |  | not_tested |
| Septum mats | 5 |  | not_tested |
| Gas PCB cartridges/blanks | 5 |  | not_tested |
| SHT41 carriers/blanks | 5 |  | not_tested |
| IR thermopiles/blanks | 5 |  | not_tested |
| Sample/relief cap | 5 |  | not_tested |
| Wedge locks | 5 |  | not_tested |

## Gate 3 OT-2 Placement And No-Motion Clearance

This gate is placement-only. It does not authorize OT-2 motion.
The linked Gate 3 placement worksheet is generated from the CAD placement
targets below. Keep it `not_tested` until the printed, dressed assembly is
seated on the OT-2 deck and every row has measured/photo evidence.

| Item | Tool | Result | Evidence / notes |
|---|---|---|---|
| Deck seating in target slot | visual/feeler gauge | not_tested |  |
| No OT-2 frame protrusion interference | visual/feeler gauge | not_tested |  |
| Adjacent-slot tube/cable dress | visual/photo | not_tested |  |
| Pipette top-field obstruction absent | visual/photo | not_tested |  |
| Camera visibility of assembly/fiducials | OT-2 or external camera | not_tested |  |
| Assembly high point | calipers | not_tested |  |

## Gate 4 Passive Leak And Wet/Dry Witness

The linked Gate 4 wet/dry witness worksheet is generated from the CAD wet/dry
witness targets below. Keep it `not_tested` until dye, condensate, debris, and
dry-bay ingress observations have measured or photo evidence for each row.

Linked protocol:
`docs/protocols/row_coupon_passive_leak_wet_dry_validation.md`

Use water with dye before electronics or biology.

| Wet source | Result | Evidence / notes |
|---|---|---|
| Side gas fitting exterior | not_tested |  |
| Sample/relief cap seat | not_tested |  |
| Gasket-tab roots | not_tested |  |
| Optical-aperture-adjacent wet surface | not_tested |  |
| Representative plate wells under septum mat | not_tested |  |
| Warm humid exposure | not_tested | duration:  |
| Dry bay inspection | not_tested |  |
| IR pocket inspection | not_tested |  |
| Gas PCB pocket inspection | not_tested |  |
| SHT41 pocket inspection | not_tested |  |
| Harness channel inspection | not_tested |  |
| Connector shroud inspection | not_tested |  |

## Gate 5 Consumable And Puncture Link

The linked Gate 5 consumable/puncture worksheet is generated from the CAD
consumable/puncture targets below. Keep it `not_tested` until real plate/mat
metrology, all-well puncture access, puncture-force, repeat-cycle, and
plate-shift evidence is recorded for each row.

Linked protocol:
`docs/protocols/row_coupon_consumable_puncture_validation.md`

| Item | Result | Evidence / notes |
|---|---|---|
| Mat sheet thickness measured | not_tested |  |
| Mat plug diameter/protrusion measured | not_tested |  |
| Mat slit length/opening behavior measured | not_tested |  |
| Plate underside support contacts inspected | not_tested |  |
| Plate lateral shift after puncture | not_tested |  |
| Dye dispense/aspirate through mat | not_tested |  |

## Gate 6 Sensor And Thermal Link

The linked Gate 6 sensor/thermal worksheet is generated from the CAD
sensor/thermal targets below. Keep it `not_tested` until sensor packages or
blanks, gas-PCB cartridge sealing, SHT41 carrier exposure, IR gasket/FOV,
harness continuity, cable dress, and thermal-proxy plan evidence is recorded
for each row. Dimensional blanks support mechanical fit only; the final
sensor/thermal readiness audit requires real installed electronics, electrical
services, IR packages, gas-sensor PCBs, and headspace sensor carriers.

This gate records readiness for powered tests. It does not prove sensor response,
CO2 control, RH control, IR calibration, or biology readiness.

| Item | Result | Evidence / notes |
|---|---|---|
| Gas PCB cartridge seating | not_tested | aperture aligned, gasket compressed |
| Headspace SHT41 carrier seating | not_tested | membrane aperture exposed |
| IR package seating | not_tested | gasket centered, lens unobstructed |
| Cable continuity during service cycling | not_tested |  |
| IR FOV spot acknowledged as plate-margin proxy | not_tested | not direct cell temperature |
| Edge-to-center thermal plan written | not_tested |  |

## Decision

Decision: `pass | revise | defer | block`

Rationale:

## CAD Changes Authorized By Evidence

| Evidence | Authorized CAD change |
|---|---|
|  |  |

## Features Explicitly Deferred To Avoid Overengineering

| Feature / idea | Reason deferred |
|---|---|
|  |  |

## Open Failures Or Blockers

| Failure | Gate | Owner | Next action |
|---|---|---|---|
|  |  |  |  |
