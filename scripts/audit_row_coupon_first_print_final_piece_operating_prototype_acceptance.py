from __future__ import annotations

import argparse

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon_first_print import (
    audit_first_print_final_piece_operating_prototype_acceptance,
    first_print_record_table_value,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "params",
        nargs="?",
        default=ROOT / "cad" / "one_row_coupon.params.json",
        help="Path to a one-row coupon params JSON file.",
    )
    parser.add_argument(
        "--out-dir",
        default=ROOT / "outputs" / "cad",
        help="CAD output directory containing generated production STL/STEP files.",
    )
    parser.add_argument(
        "--queue-dir",
        default=ROOT / "outputs" / "cad" / "first_print_slicer_queue",
        help="Monolithic first-print slicer queue directory for preflight fallback.",
    )
    parser.add_argument(
        "--piece-dir",
        default=ROOT / "outputs" / "cad" / "final_print_pieces",
        help="Directory containing generated canonical final-piece STL/STEP files.",
    )
    parser.add_argument(
        "--piece-queue-dir",
        default=ROOT / "outputs" / "cad" / "first_print_final_piece_slicer_queue",
        help="Final-piece first-print slicer queue directory.",
    )
    parser.add_argument(
        "--slicer-setup",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_slicer_setup.csv",
        help="Selected slicer setup worksheet.",
    )
    parser.add_argument(
        "--gate1-qc",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_final_piece_gate1_qc.csv",
        help="Final Gate 1 QC worksheet.",
    )
    parser.add_argument(
        "--print-batch-traveler",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_final_piece_print_batch_traveler.csv",
        help="Final print batch traveler worksheet.",
    )
    parser.add_argument(
        "--sliced-outputs",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_final_piece_sliced_outputs.csv",
        help="Ready final-piece sliced-output worksheet.",
    )
    parser.add_argument(
        "--gate2-dry-assembly",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_gate2_dry_assembly.csv",
        help="Gate 2 dry assembly worksheet.",
    )
    parser.add_argument(
        "--install-inventory",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_install_inventory.csv",
        help="Install inventory worksheet.",
    )
    parser.add_argument(
        "--service-state-review",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_service_state_review.csv",
        help="Service-state review worksheet.",
    )
    parser.add_argument(
        "--gate3-placement",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_gate3_placement.csv",
        help="Gate 3 OT-2 placement worksheet.",
    )
    parser.add_argument(
        "--gate4-wet-dry-witness",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_gate4_wet_dry_witness.csv",
        help="Gate 4 wet/dry witness worksheet.",
    )
    parser.add_argument(
        "--gate5-consumable-puncture",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_gate5_consumable_puncture.csv",
        help="Gate 5 consumable/puncture worksheet.",
    )
    parser.add_argument(
        "--gate6-sensor-thermal",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_gate6_sensor_thermal.csv",
        help="Gate 6 sensor/thermal worksheet.",
    )
    parser.add_argument(
        "--record",
        default=ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_first_print.md",
        help="Measurement record to audit.",
    )
    parser.add_argument(
        "--require-operating-prototype-ready",
        action="store_true",
        help=(
            "Exit nonzero unless print-start artifacts and the full Gate 1-6 "
            "physical evidence chain are ready."
        ),
    )
    args = parser.parse_args()

    params = load_params(args.params)
    expected_setup = first_print_record_table_value(
        args.record,
        "Printer / material / profile",
    )
    audit = audit_first_print_final_piece_operating_prototype_acceptance(
        params=params,
        out_dir=args.out_dir,
        queue_dir=args.queue_dir,
        piece_dir=args.piece_dir,
        piece_queue_dir=args.piece_queue_dir,
        record_path=args.record,
        root=ROOT,
        slicer_setup_path=args.slicer_setup,
        gate1_qc_path=args.gate1_qc,
        print_batch_traveler_path=args.print_batch_traveler,
        sliced_output_path=args.sliced_outputs,
        gate2_dry_assembly_path=args.gate2_dry_assembly,
        install_inventory_path=args.install_inventory,
        service_state_review_path=args.service_state_review,
        gate3_placement_path=args.gate3_placement,
        gate4_wet_dry_witness_path=args.gate4_wet_dry_witness,
        gate5_consumable_puncture_path=args.gate5_consumable_puncture,
        gate6_sensor_thermal_path=args.gate6_sensor_thermal,
        expected_setup_summary=expected_setup,
    )

    print(f"measurement_record: {audit.record_path}")
    print(
        "operating_prototype_ready: "
        f"{'true' if audit.operating_prototype_ready else 'false'}"
    )
    print(
        "preflight_artifacts_ready: "
        f"{'true' if audit.preflight_artifacts_ready else 'false'}"
    )
    print(f"print_start_ready: {'true' if audit.print_start_ready else 'false'}")
    print(
        "service_state_review_ready: "
        f"{'true' if audit.service_state_review_ready else 'false'}"
    )
    print(
        "install_inventory_ready: "
        f"{'true' if audit.install_inventory_ready else 'false'}"
    )
    print(
        "gate1_print_qc_ready: "
        f"{'true' if audit.gate1_print_qc_ready else 'false'}"
    )
    print(
        "gate2_dry_assembly_ready: "
        f"{'true' if audit.gate2_dry_assembly_ready else 'false'}"
    )
    print(f"gate2_pass_rows: {audit.gate2_pass_row_count}")
    print(
        "gate3_placement_ready: "
        f"{'true' if audit.gate3_placement_ready else 'false'}"
    )
    print(f"gate3_pass_rows: {audit.gate3_pass_row_count}")
    print(
        "gate4_wet_dry_witness_ready: "
        f"{'true' if audit.gate4_wet_dry_witness_ready else 'false'}"
    )
    print(f"gate4_pass_rows: {audit.gate4_pass_row_count}")
    print(
        "gate5_consumable_puncture_ready: "
        f"{'true' if audit.gate5_consumable_puncture_ready else 'false'}"
    )
    print(f"gate5_pass_rows: {audit.gate5_pass_row_count}")
    print(
        "sensor_thermal_ready: "
        f"{'true' if audit.sensor_thermal_ready else 'false'}"
    )
    print(
        "real_sensor_inventory_ready: "
        f"{'true' if audit.real_sensor_inventory_ready else 'false'}"
    )
    print(f"sensor_inventory_blank_parts: {len(audit.sensor_inventory_blank_parts)}")
    for part in audit.sensor_inventory_blank_parts:
        print(f"sensor_inventory_blank_part: {part}")
    print(
        "gate6_sensor_thermal_worksheet_valid: "
        f"{'true' if audit.gate6_sensor_thermal_worksheet_valid else 'false'}"
    )
    print(
        "gate6_sensor_thermal_pass_ready: "
        f"{'true' if audit.gate6_sensor_thermal_pass_ready else 'false'}"
    )
    print(f"gate6_pass_rows: {audit.gate6_pass_row_count}")
    print(f"physical_gate_passes: {len(audit.physical_gate_passes)}")
    for gate in audit.physical_gate_passes:
        print(f"physical_gate_pass: {gate}")
    print(f"next_evidence_actions: {len(audit.next_evidence_actions)}")
    for action in audit.next_evidence_actions:
        print(f"next_evidence_action: {action}")
    print(f"issues: {len(audit.issues)}")
    for issue in audit.issues:
        print(f"issue: {issue.field} | {issue.message}")

    if audit.issues:
        raise SystemExit(1)
    if (
        args.require_operating_prototype_ready
        and not audit.operating_prototype_ready
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
