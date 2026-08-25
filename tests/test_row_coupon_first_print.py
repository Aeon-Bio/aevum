from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

import pytest

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon import (
    ROW_COUPON_SERVICE_MODES,
    row_coupon_layout,
    row_coupon_part_manifest,
)
from aevum_cad.row_coupon_first_print import (
    FIRST_PRINT_OPTIONAL_VALIDATION_TOOLS,
    FIRST_PRINT_REQUIRED_VALIDATION_CHECKS,
    FirstPrintSlicerSetupRow,
    FirstPrintYSplitArtifactRow,
    _part_fits_rectangular_bed,
    artifact_category,
    audit_first_print_bed_fit_split_plan,
    audit_first_print_gate1_qc_worksheet,
    audit_first_print_gate2_dry_assembly_worksheet,
    audit_first_print_gate3_placement_worksheet,
    audit_first_print_gate4_wet_dry_witness_worksheet,
    audit_first_print_gate5_consumable_puncture_worksheet,
    audit_first_print_gate6_sensor_thermal_worksheet,
    audit_first_print_install_inventory,
    audit_first_print_package,
    audit_first_print_preflight,
    audit_first_print_service_state_review,
    audit_first_print_sliced_outputs,
    audit_first_print_slicer_bed_fit,
    audit_first_print_slicer_queue,
    audit_first_print_slicer_queue_manifest,
    audit_first_print_slicer_setup,
    audit_first_print_y_split_artifacts,
    audit_first_print_y_split_gate1_print_qc,
    audit_first_print_y_split_gate1_qc_worksheet,
    audit_first_print_y_split_gate2_dry_assembly_readiness,
    audit_first_print_y_split_gate3_placement_readiness,
    audit_first_print_y_split_gate4_wet_dry_witness_readiness,
    audit_first_print_y_split_gate5_consumable_puncture_readiness,
    audit_first_print_y_split_gate6_sensor_thermal_readiness,
    audit_first_print_y_split_operating_prototype_acceptance,
    audit_first_print_y_split_print_batch_traveler,
    audit_first_print_y_split_sliced_outputs,
    audit_first_print_y_split_slicer_queue,
    expected_optional_validation_artifacts,
    expected_production_artifacts,
    expected_validation_artifacts,
    file_sha256,
    first_print_audit_snapshot_markdown,
    first_print_bed_fit_split_plan_rows,
    first_print_cad_target_sections_markdown,
    first_print_consumable_puncture_targets_markdown,
    first_print_dry_assembly_targets_markdown,
    first_print_gate1_qc_worksheet_csv,
    first_print_gate1_qc_worksheet_rows,
    first_print_gate2_dry_assembly_targets,
    first_print_gate2_dry_assembly_worksheet_csv,
    first_print_gate2_dry_assembly_worksheet_rows,
    first_print_gate3_placement_targets,
    first_print_gate3_placement_worksheet_csv,
    first_print_gate3_placement_worksheet_rows,
    first_print_gate4_wet_dry_witness_targets,
    first_print_gate4_wet_dry_witness_worksheet_csv,
    first_print_gate4_wet_dry_witness_worksheet_rows,
    first_print_gate5_consumable_puncture_targets,
    first_print_gate5_consumable_puncture_worksheet_csv,
    first_print_gate5_consumable_puncture_worksheet_rows,
    first_print_gate6_sensor_thermal_targets,
    first_print_gate6_sensor_thermal_worksheet_csv,
    first_print_gate6_sensor_thermal_worksheet_rows,
    first_print_install_inventory_csv,
    first_print_install_inventory_rows,
    first_print_ot2_placement_targets_markdown,
    first_print_package_manifest_markdown,
    first_print_qc_target_bounds_markdown,
    first_print_qc_targets,
    first_print_sensor_thermal_targets_markdown,
    first_print_service_state_bounds_evidence_csv,
    first_print_service_state_bounds_evidence_rows,
    first_print_service_state_review_csv,
    first_print_service_state_review_rows,
    first_print_sliced_output_csv,
    first_print_sliced_output_rows,
    first_print_slicer_queue_artifacts,
    first_print_slicer_queue_manifest_markdown,
    first_print_slicer_setup_csv,
    first_print_wet_dry_witness_targets_markdown,
    first_print_y_split_artifact_rows,
    first_print_y_split_gate1_qc_worksheet_csv,
    first_print_y_split_gate1_qc_worksheet_rows,
    first_print_y_split_sliced_output_rows,
    prepare_first_print_slicer_queue,
    prepare_first_print_y_split_slicer_queue,
    scaffold_first_print_measurement_record,
    select_first_print_slicer_setup,
    slice_first_print_y_split_slicer_queue,
    write_first_print_bed_fit_split_plan,
    write_first_print_gate1_qc_worksheet,
    write_first_print_gate2_dry_assembly_worksheet,
    write_first_print_gate3_placement_worksheet,
    write_first_print_gate4_wet_dry_witness_worksheet,
    write_first_print_gate5_consumable_puncture_worksheet,
    write_first_print_gate6_sensor_thermal_worksheet,
    write_first_print_install_inventory,
    write_first_print_package_manifest,
    write_first_print_service_state_bounds_evidence,
    write_first_print_service_state_review,
    write_first_print_sliced_outputs,
    write_first_print_slicer_setup,
    write_first_print_y_split_gate1_qc_worksheet,
    write_first_print_y_split_print_batch_traveler,
    write_first_print_y_split_sliced_outputs,
)

PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
FIRST_PRINT_TEMPLATE = (
    ROOT / "data" / "measurements" / "templates" / "one_row_coupon_first_print_readiness.md"
)
PASSIVE_LEAK_PROTOCOL = (
    ROOT / "docs" / "protocols" / "row_coupon_passive_leak_wet_dry_validation.md"
)
PASSIVE_LEAK_TEMPLATE = (
    ROOT
    / "data"
    / "measurements"
    / "templates"
    / "row_coupon_passive_leak_wet_dry_validation.md"
)
TEST_SLICER_SETUP_SUMMARY = (
    "TestSlicer / test printer / test material / test print profile"
)


def _touch_required_artifacts(params: dict, out_dir: Path) -> None:
    audit = audit_first_print_package(params, out_dir)
    audit.assembly_step.parent.mkdir(parents=True, exist_ok=True)
    audit.assembly_step.touch()
    for artifact in (*audit.production_artifacts, *audit.validation_artifacts):
        artifact.stl_path.touch()
        artifact.step_path.touch()


def _worksheet_csv_from_rows(rows: list[dict[str, str]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=tuple(rows[0]),
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _write_evidence_file(root: Path, evidence_path: str) -> None:
    path = Path(evidence_path)
    if not path.is_absolute():
        path = root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"evidence\n")


def _write_ready_service_state_review_fixture(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "service_state_screens"
    evidence_dir.mkdir(exist_ok=True)
    evidence_paths: dict[str, str] = {}
    for row in first_print_service_state_review_rows():
        evidence_path = evidence_dir / f"{row.mode}.png"
        evidence_path.write_bytes(b"png")
        evidence_paths[row.mode] = f"service_state_screens/{row.mode}.png"
    write_first_print_service_state_review(
        output_path=tmp_path / "2026-06-02_one_row_coupon_service_state_review.csv",
        evidence_paths_by_mode=evidence_paths,
        overwrite=True,
    )


def _write_tiny_split_print_qc_fixture(
    tmp_path: Path,
    params: dict,
    *,
    ready: bool = False,
) -> dict[str, Path]:
    queue_dir = tmp_path / "tiny_split_queue"
    queue_dir.mkdir()
    stl_a = queue_dir / "part_a.stl"
    stl_b = queue_dir / "part_b.stl"
    stl_a.write_text("solid part a\n")
    stl_b.write_text("solid part b\n")
    (queue_dir / "SLICER_QUEUE_MANIFEST.md").write_text(
        "\n".join(
            (
                "# Test First-Print Slicer Queue",
                "",
                "| Part | Queued STL | SHA256 | Target X mm | Target Y mm | Target Z mm | Role |",
                "|---|---|---|---:|---:|---:|---|",
                f"| `part_a` | `{stl_a.name}` | `{file_sha256(stl_a)}` | "
                "10.00 | 20.00 | 3.00 | printed split segment |",
                f"| `part_b` | `{stl_b.name}` | `{file_sha256(stl_b)}` | "
                "11.00 | 21.00 | 4.00 | printed |",
            )
        )
    )
    gcode_a = tmp_path / "part_a.gcode"
    gcode_b = tmp_path / "part_b.gcode"
    gcode_a.write_text("gcode a\n")
    gcode_b.write_text("gcode b\n")
    sliced_outputs = tmp_path / "tiny_split_sliced_outputs.csv"
    sliced_outputs.write_text(
        _worksheet_csv_from_rows(
            [
                {
                    "part": "part_a",
                    "queued_stl_path": str(stl_a),
                    "queued_stl_sha256": file_sha256(stl_a),
                    "sliced_output_path": str(gcode_a),
                    "sliced_output_sha256": file_sha256(gcode_a),
                    "selected_setup_summary": TEST_SLICER_SETUP_SUMMARY,
                    "result": "pass",
                    "notes": "sliced with fake slicer",
                },
                {
                    "part": "part_b",
                    "queued_stl_path": str(stl_b),
                    "queued_stl_sha256": file_sha256(stl_b),
                    "sliced_output_path": str(gcode_b),
                    "sliced_output_sha256": file_sha256(gcode_b),
                    "selected_setup_summary": TEST_SLICER_SETUP_SUMMARY,
                    "result": "pass",
                    "notes": "sliced with fake slicer",
                },
            ]
        )
    )
    gate1_rows = [
        {
            "part": "part_a",
            "source": "printed_split",
            "target_x_mm": "10.00",
            "target_y_mm": "20.00",
            "target_z_mm": "3.00",
            "measured_x_mm": "",
            "measured_y_mm": "",
            "measured_z_mm": "",
            "evidence_path": "",
            "result": "not_tested",
            "notes": "",
        },
        {
            "part": "part_b",
            "source": "printed",
            "target_x_mm": "11.00",
            "target_y_mm": "21.00",
            "target_z_mm": "4.00",
            "measured_x_mm": "",
            "measured_y_mm": "",
            "measured_z_mm": "",
            "evidence_path": "",
            "result": "not_tested",
            "notes": "",
        },
    ]
    if ready:
        for row in gate1_rows:
            row["measured_x_mm"] = row["target_x_mm"]
            row["measured_y_mm"] = row["target_y_mm"]
            row["measured_z_mm"] = row["target_z_mm"]
            row["evidence_path"] = f"evidence/gate1/{row['part']}.jpg"
            _write_evidence_file(tmp_path, row["evidence_path"])
            row["result"] = "pass"
    gate1_qc = tmp_path / "tiny_split_gate1_qc.csv"
    gate1_qc.write_text(_worksheet_csv_from_rows(gate1_rows))
    traveler = tmp_path / "tiny_print_batch_traveler.csv"
    write_first_print_y_split_print_batch_traveler(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        sliced_output_path=sliced_outputs,
        gate1_qc_path=gate1_qc,
        output_path=traveler,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )
    if ready:
        traveler_rows = list(csv.DictReader(StringIO(traveler.read_text())))
        for row in traveler_rows:
            row["gate1_qc_result"] = "pass"
            row["print_result"] = "printed"
            row["print_evidence_path"] = f"evidence/print_batch/{row['part']}.jpg"
            _write_evidence_file(tmp_path, row["print_evidence_path"])
        traveler.write_text(_worksheet_csv_from_rows(traveler_rows))

    return {
        "queue_dir": queue_dir,
        "sliced_outputs": sliced_outputs,
        "gate1_qc": gate1_qc,
        "traveler": traveler,
    }


def _mark_tiny_split_print_qc_ready(fixture: dict[str, Path]) -> None:
    gate1_rows = list(csv.DictReader(StringIO(fixture["gate1_qc"].read_text())))
    for row in gate1_rows:
        row["measured_x_mm"] = row["target_x_mm"]
        row["measured_y_mm"] = row["target_y_mm"]
        row["measured_z_mm"] = row["target_z_mm"]
        row["evidence_path"] = f"evidence/gate1/{row['part']}.jpg"
        _write_evidence_file(fixture["gate1_qc"].parent, row["evidence_path"])
        row["result"] = "pass"
    fixture["gate1_qc"].write_text(_worksheet_csv_from_rows(gate1_rows))
    traveler_rows = list(csv.DictReader(StringIO(fixture["traveler"].read_text())))
    for row in traveler_rows:
        row["gate1_qc_result"] = "pass"
        row["print_result"] = "printed"
        row["print_evidence_path"] = f"evidence/print_batch/{row['part']}.jpg"
        _write_evidence_file(fixture["traveler"].parent, row["print_evidence_path"])
    fixture["traveler"].write_text(_worksheet_csv_from_rows(traveler_rows))


def _write_ready_install_inventory(path: Path) -> None:
    rows = list(csv.DictReader(StringIO(first_print_install_inventory_csv())))
    for row in rows:
        row["item_identifier"] = f"inventory-{row['part']}"
        row["evidence_path"] = f"evidence/install_inventory/{row['part']}.jpg"
        _write_evidence_file(path.parent, row["evidence_path"])
        row["result"] = "pass"
        if row["source"] == "cots_consumable":
            row["installed_as"] = "real_part"
        elif row["source"] == "service_tubing":
            row["installed_as"] = "measured_replacement"
        else:
            row["installed_as"] = "dimensional_blank"
            row["notes"] = "mechanical-only blank; no sensing authority"
    path.write_text(_worksheet_csv_from_rows(rows))


def _mark_install_inventory_real_sensors(path: Path) -> None:
    rows = list(csv.DictReader(StringIO(path.read_text())))
    for row in rows:
        if row["source"] != "electronics_or_dimensional_blank":
            continue
        row["installed_as"] = "real_part"
        row["notes"] = ""
    path.write_text(_worksheet_csv_from_rows(rows))


def _write_passed_target_worksheet(path: Path, worksheet_csv: str) -> None:
    rows = list(csv.DictReader(StringIO(worksheet_csv)))
    for row in rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(path.parent, row["evidence_path"])
        row["result"] = "pass"
    path.write_text(_worksheet_csv_from_rows(rows))


def _build_preflight_fixture(params: dict, tmp_path: Path) -> Path:
    params_path = tmp_path / "one_row_coupon.params.json"
    params_path.write_bytes(PARAMS.read_bytes())
    _touch_required_artifacts(params, tmp_path)
    write_first_print_package_manifest(
        params=params,
        out_dir=tmp_path,
        output_path=tmp_path / f"{params['name']}_first_print_package_manifest.md",
    )
    prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
    )
    record_path = tmp_path / "2026-06-02_one_row_coupon_first_print.md"
    scaffold_first_print_measurement_record(
        params=params,
        params_path=params_path,
        out_dir=tmp_path,
        template_path=FIRST_PRINT_TEMPLATE,
        output_path=record_path,
        date="2026-06-02",
        cad_source_note="test-worktree",
    )
    fake_slicer = tmp_path / "fake_slicer"
    fake_slicer.write_text("fake")
    profile_source = tmp_path / "fake_slicer_profile.ini"
    profile_source.write_text(
        "[printer:test printer]\n"
        "bed_shape = 0x0,500x0,500x500,0x500\n"
    )
    setup_row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(fake_slicer),
        version="TestSlicer 1.0",
        printer_profile="test printer",
        material_profile="test material",
        print_profile="test print profile",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
        notes="test setup",
    )
    write_first_print_slicer_setup(
        output_path=tmp_path / "2026-06-02_one_row_coupon_slicer_setup.csv",
        rows=(setup_row,),
    )
    write_first_print_sliced_outputs(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        output_path=tmp_path / "2026-06-02_one_row_coupon_sliced_outputs.csv",
    )
    write_first_print_gate1_qc_worksheet(
        params=params,
        output_path=tmp_path / "2026-06-02_one_row_coupon_gate1_qc.csv",
    )
    write_first_print_gate2_dry_assembly_worksheet(
        params=params,
        output_path=tmp_path / "2026-06-02_one_row_coupon_gate2_dry_assembly.csv",
    )
    write_first_print_gate3_placement_worksheet(
        params=params,
        output_path=tmp_path / "2026-06-02_one_row_coupon_gate3_placement.csv",
    )
    write_first_print_gate4_wet_dry_witness_worksheet(
        params=params,
        output_path=tmp_path / "2026-06-02_one_row_coupon_gate4_wet_dry_witness.csv",
    )
    write_first_print_gate5_consumable_puncture_worksheet(
        params=params,
        output_path=tmp_path / "2026-06-02_one_row_coupon_gate5_consumable_puncture.csv",
    )
    write_first_print_gate6_sensor_thermal_worksheet(
        params=params,
        output_path=tmp_path / "2026-06-02_one_row_coupon_gate6_sensor_thermal.csv",
    )
    write_first_print_install_inventory(
        output_path=tmp_path / "2026-06-02_one_row_coupon_install_inventory.csv",
    )
    _write_ready_service_state_review_fixture(tmp_path)
    record = record_path.read_text()
    record = record.replace(
        "| Gate 0 CAD Artifact Identity | not_tested |  |",
        "| Gate 0 CAD Artifact Identity | pass | test preflight evidence |",
        1,
    )
    record = record.replace(
        "| Printer / material / profile |  |",
        f"| Printer / material / profile | {setup_row.setup_summary} |",
        1,
    )
    record_path.write_text(record)
    return record_path


def _write_selected_small_bed_setup(tmp_path: Path) -> Path:
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text("[printer:small printer]\nbed_shape = 0x0,250x0,250x210,0x210\n")
    setup_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="small printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
    )
    setup_path.write_text(first_print_slicer_setup_csv((row,)))
    return setup_path


def _touch_y_split_artifacts(
    params: dict,
    tmp_path: Path,
    split_dir: Path,
    setup_path: Path,
) -> None:
    rows = first_print_y_split_artifact_rows(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        slicer_setup_path=setup_path,
    )
    for row in rows:
        row.stl_path.parent.mkdir(parents=True, exist_ok=True)
        row.stl_path.touch()
        row.step_path.touch()


def _write_ready_sliced_output_worksheet(params: dict, tmp_path: Path) -> Path:
    queue_dir = tmp_path / "first_print_slicer_queue"
    sliced_dir = tmp_path / "sliced"
    sliced_dir.mkdir()
    rows = list(
        csv.DictReader(
            StringIO(
                first_print_sliced_output_csv(
                    first_print_sliced_output_rows(
                        params=params,
                        out_dir=tmp_path,
                        queue_dir=queue_dir,
                        selected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
                    )
                )
            )
        )
    )
    for row in rows:
        output = sliced_dir / f"{row['part']}.gcode"
        output.write_text(f"sliced {row['part']}\n")
        row["sliced_output_path"] = str(output)
        row["sliced_output_sha256"] = file_sha256(output)
        row["result"] = "pass"
    worksheet = tmp_path / "2026-06-02_one_row_coupon_sliced_outputs.csv"
    worksheet.write_text(_worksheet_csv_from_rows(rows))
    return worksheet


def test_first_print_audit_tracks_manifest_and_required_validation_artifacts() -> None:
    params = load_params(PARAMS)
    manifest = row_coupon_part_manifest()
    production = expected_production_artifacts(params, ROOT / "outputs" / "cad")
    validation = expected_validation_artifacts(params, ROOT / "outputs" / "cad")
    optional = expected_optional_validation_artifacts(params, ROOT / "outputs" / "cad")

    assert [artifact.name for artifact in production] == list(manifest["installed"])
    assert [artifact.name for artifact in validation] == list(
        FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    )
    assert "deck_pod_seating_repeatability_check" in (
        FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    )
    assert "gas_pcb_flow_cell_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "pipette_puncture_swept_path_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "dry_bay_envelope_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "dry_bay_boundary_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "headspace_barrier_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "headspace_volume_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "wet_dry_failure_path_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "operating_service_dress_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "side_gas_tube_envelope_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "side_gas_leak_witness_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "sample_relief_leak_witness_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "gasket_tab_leak_witness_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "dry_bay_ingress_audit_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "adjacent_deck_slot_keepout_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "sensor_connector_service_clearance_check" in (
        FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    )
    assert "observer_front_end_swept_body_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "observer_carriage_envelope_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "observer_service_raceway_envelope_check" in (
        FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    )
    assert "observer_fiducial_focus_target_check" in (
        FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    )
    assert "observer_optical_stability_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "observer_kinematic_split_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "assembly_state_witness_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "gasket_compression_gap_gauge" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "latch_retention_span_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "fail_closed_prerun_inspection_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "material_cleaning_witness_coupon" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "consumable_metrology_gauge" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert (
        "printability_support_cleanup_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    )
    assert "row_tiling_service_clearance_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert "thermal_condensation_proxy_check" in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    assert [artifact.name for artifact in optional] == list(
        FIRST_PRINT_OPTIONAL_VALIDATION_TOOLS
    )
    assert FIRST_PRINT_OPTIONAL_VALIDATION_TOOLS == ()
    assert artifact_category("printed_polymer") == "printed"
    assert artifact_category("compressible_elastomer_or_printed_tpu") == (
        "compressible_or_flexible"
    )
    assert artifact_category("cots_consumable") == "cots_consumable"
    assert artifact_category("custom_or_cots_pcb_assembly") == (
        "electronics_or_dimensional_blank"
    )


def test_required_validation_checks_have_layout_physical_evidence_contract() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)

    missing = [
        name
        for name in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
        if not isinstance(layout.get(name), dict)
        or "evidence_gate" not in layout[name]
        or "requires_physical_evidence" not in layout[name]
    ]

    assert missing == []
    for name in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS:
        spec = layout[name]
        assert "Gate " in spec["evidence_gate"]
        assert spec["requires_physical_evidence"] is True
        assert spec["cad_value"]


def test_first_print_audit_passes_when_required_artifacts_exist(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)

    audit = audit_first_print_package(params, tmp_path)

    assert audit.ready
    assert audit.missing_paths == ()
    assert not any(
        path.name.endswith("validation_consumable_metrology_gauge.step")
        for path in audit.missing_paths
    )


def test_first_print_audit_fails_when_required_artifact_is_missing(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    missing = tmp_path / f"{params['name']}_validation_well_cell_plane_check.step"
    missing.unlink()

    audit = audit_first_print_package(params, tmp_path)

    assert not audit.ready
    assert missing in audit.missing_paths


def test_first_print_audit_snapshot_lists_missing_paths(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    audit = audit_first_print_package(params, tmp_path)

    snapshot = first_print_audit_snapshot_markdown(audit)

    assert "| Audit ready | false |" in snapshot
    assert "| Missing required artifact |" in snapshot
    assert f"`{audit.assembly_step}`" in snapshot


def test_scaffold_first_print_record_prefills_identity_not_physical_gates(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    params_path = tmp_path / "one_row_coupon.params.json"
    params_path.write_bytes(PARAMS.read_bytes())
    _touch_required_artifacts(params, tmp_path)
    output_path = tmp_path / "record.md"

    scaffold_first_print_measurement_record(
        params=params,
        params_path=params_path,
        out_dir=tmp_path,
        template_path=FIRST_PRINT_TEMPLATE,
        output_path=output_path,
        date="2026-06-02",
        cad_source_note="test-worktree",
    )

    record = output_path.read_text()
    generated_timestamp_line = next(
        line
        for line in record.splitlines()
        if line.startswith("| Generated output timestamp |")
    )
    assert "| Date | 2026-06-02 |" in record
    assert "| Active print queue mode | monolithic |" in record
    assert f"| Params file | `{params_path}` |" in record
    assert f"| Params SHA256 | {file_sha256(params_path)} |" in record
    assert "| CAD source commit / worktree note | test-worktree |" in record
    manifest_path = tmp_path / "aevum_one_row_coupon_first_print_package_manifest.md"
    assert f"| Print/procurement manifest | `{manifest_path}` |" in record
    assert f"| Slicer queue | `{tmp_path / 'first_print_slicer_queue'}` |" in record
    split_queue = tmp_path / "first_print_y_split_slicer_queue"
    assert f"| Split slicer queue | `{split_queue}` |" in record
    setup = tmp_path / "2026-06-02_one_row_coupon_slicer_setup.csv"
    assert f"| Slicer setup worksheet | `{setup}` |" in record
    split_plan = tmp_path / "2026-06-02_one_row_coupon_bed_fit_split_plan.csv"
    assert f"| Bed-fit split plan | `{split_plan}` |" in record
    sliced_outputs = tmp_path / "2026-06-02_one_row_coupon_sliced_outputs.csv"
    assert f"| Sliced output worksheet | `{sliced_outputs}` |" in record
    split_sliced_outputs = (
        tmp_path / "2026-06-02_one_row_coupon_y_split_sliced_outputs.csv"
    )
    assert f"| Split sliced output worksheet | `{split_sliced_outputs}` |" in record
    split_traveler = (
        tmp_path / "2026-06-02_one_row_coupon_y_split_print_batch_traveler.csv"
    )
    assert f"| Split print batch traveler | `{split_traveler}` |" in record
    split_qc_worksheet = tmp_path / "2026-06-02_one_row_coupon_y_split_gate1_qc.csv"
    assert f"| Split Gate 1 QC worksheet | `{split_qc_worksheet}` |" in record
    qc_worksheet = tmp_path / "2026-06-02_one_row_coupon_gate1_qc.csv"
    assert f"| Gate 1 QC worksheet | `{qc_worksheet}` |" in record
    gate2_worksheet = tmp_path / "2026-06-02_one_row_coupon_gate2_dry_assembly.csv"
    assert f"| Gate 2 dry assembly worksheet | `{gate2_worksheet}` |" in record
    gate3_worksheet = tmp_path / "2026-06-02_one_row_coupon_gate3_placement.csv"
    assert f"| Gate 3 placement worksheet | `{gate3_worksheet}` |" in record
    gate4_worksheet = tmp_path / "2026-06-02_one_row_coupon_gate4_wet_dry_witness.csv"
    assert f"| Gate 4 wet/dry witness worksheet | `{gate4_worksheet}` |" in record
    gate5_worksheet = tmp_path / "2026-06-02_one_row_coupon_gate5_consumable_puncture.csv"
    assert f"| Gate 5 consumable/puncture worksheet | `{gate5_worksheet}` |" in record
    gate6_worksheet = tmp_path / "2026-06-02_one_row_coupon_gate6_sensor_thermal.csv"
    assert f"| Gate 6 sensor/thermal worksheet | `{gate6_worksheet}` |" in record
    inventory = tmp_path / "2026-06-02_one_row_coupon_install_inventory.csv"
    assert f"| Install inventory worksheet | `{inventory}` |" in record
    service_state_review = tmp_path / "2026-06-02_one_row_coupon_service_state_review.csv"
    assert f"| Service state review worksheet | `{service_state_review}` |" in record
    assert generated_timestamp_line.endswith("Z |")
    assert "## Gate 0 Audit Snapshot" in record
    assert "| Audit ready | true |" in record
    assert "Missing required artifacts: none" in record
    assert "## Gate 1 CAD Target Bounds" in record
    assert "| `deck_pods` | printed | 128.00 | 357.50 | 84.10 |" in record
    assert "| `lower_gasket` | compressible_or_flexible |" in record
    assert "## Gate 2 CAD Dry Assembly Targets" in record
    assert "| Installed dry stack | 4 plates / 4 mats / 2 perimeter gaskets |" in record
    assert "| Latch asymmetry watch | 1 omitted / 181.00 mm max span |" in record
    assert "| Sensor package dry fit | 2 gas PCB / 4 SHT41 / 4 IR |" in record
    assert "| Fail-closed pre-run inspection | 10 checkpoints /" in record
    assert "## Gate 3 CAD Placement Targets" in record
    assert "| Assembly deck-to-top envelope | 140.60 mm |" in record
    assert (
        "| Deck pod seating repeatability | 16 feet / 16 keys / "
        "4 slots / 5 cycles |" in record
    )
    assert "| Adjacent-slot service clearance | 4.10 mm |" in record
    assert (
            "| Operating service dress envelope | 220.60 x 348.75 x 43.30 mm / "
        "11 envelopes |"
    ) in record
    assert (
        "| Row tiling/service clearance check | 8 neighbor keepouts / "
        "11 service envelopes / 4.10 mm minimum clearance |"
    ) in record
    assert (
        "| OT-2 toolhead swept body envelope | 250.00 x 445.50 x 45.00 mm / "
        "384 wells |"
    ) in record
    assert (
        "| OT-2 toolhead lower clearance | 8.00 mm assembly / 27.90 mm "
        "services / 2.00 mm tip path |"
    ) in record
    assert "| Pipette puncture targets | 384 wells |" in record
    assert "## Gate 4 CAD Wet/Dry Witness Targets" in record
    assert "| Dry-bay protected volume | 120.20 x 357.50 x 80.00 mm |" in record
    assert (
        "| Dry-bay ingress audit | 10 wet collectors / 7 inboard dams / "
        "1 protected footprint |" in record
    )
    assert "| Side-gas service witness set | 4 wet collectors / 2 inboard dams |" in record
    assert "| Aperture-adjacent witness gutters | 8 gutters, 0.45 mm depth |" in record
    assert "## Gate 5 CAD Consumable/Puncture Targets" in record
    assert "| Installed consumable set | 4 plates / 4 septum mats |" in record
    assert "| Puncture target count | 384 wells |" in record
    assert "| Plate lateral shift limit | <=0.25 mm |" in record
    assert "## Gate 6 CAD Sensor/Thermal Targets" in record
    assert "| Sensor install workflow | 10 steps / 7 gates |" in record
    assert "| Gas PCB cartridges | 2 cartridges, 5.00 x 30.00 x 25.00 mm |" in record
    assert "| IR proxy FOV spot | 1.08 mm at plate margin, 12.00 deg FOV |" in record
    assert "| Gate 0 CAD Artifact Identity | not_tested |" in record
    assert "| Gate 1 Print QC | not_tested |" in record
    assert "| Gate 6 Sensor And Thermal Link | not_tested |" in record


def test_scaffold_first_print_record_refuses_overwrite(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    params_path = tmp_path / "one_row_coupon.params.json"
    params_path.write_bytes(PARAMS.read_bytes())
    output_path = tmp_path / "record.md"
    output_path.write_text("existing")

    with pytest.raises(FileExistsError):
        scaffold_first_print_measurement_record(
            params=params,
            params_path=params_path,
            out_dir=tmp_path,
            template_path=FIRST_PRINT_TEMPLATE,
            output_path=output_path,
        )


def test_first_print_template_tracks_gate0_protocol_commands() -> None:
    template = FIRST_PRINT_TEMPLATE.read_text()

    assert "`uv run python scripts/audit_row_coupon_first_print_package.py`" in template
    assert "`uv run python scripts/scaffold_row_coupon_first_print_record.py`" in template
    assert (
        "`uv run python scripts/write_row_coupon_first_print_package_manifest.py --overwrite`"
        in template
    )
    assert (
        "`uv run python scripts/prepare_row_coupon_first_print_slicer_queue.py --overwrite`"
        in template
    )
    assert (
        "`uv run python scripts/write_row_coupon_first_print_slicer_setup.py "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_slicer_setup.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv`"
        in template
    )
    assert (
        "`uv run python scripts/select_row_coupon_first_print_slicer_setup.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv "
        "--record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md "
        "--slicer-name SLICER_NAME`"
        in template
    )
    assert (
        "`uv run python scripts/write_row_coupon_first_print_bed_fit_split_plan.py "
        "--slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_bed_fit_split_plan.csv`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_bed_fit_split_plan.py "
        "--slicer-setup data/measurements/YYYY-MM-DD_one_row_coupon_slicer_setup.csv "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_bed_fit_split_plan.csv`"
        in template
    )
    assert (
        "`uv run python scripts/write_row_coupon_first_print_sliced_outputs.py "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_sliced_outputs.csv "
        "--record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_sliced_outputs.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_sliced_outputs.csv "
        "--record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md`"
        in template
    )
    assert (
        "`uv run python scripts/write_row_coupon_first_print_gate1_qc_worksheet.py "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_gate1_qc.csv`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_gate1_qc_worksheet.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate1_qc.csv`"
        in template
    )
    assert (
        "`uv run python scripts/write_row_coupon_first_print_gate2_dry_assembly_worksheet.py "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_gate2_dry_assembly_worksheet.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate2_dry_assembly.csv`"
        in template
    )
    assert (
        "`uv run python scripts/write_row_coupon_first_print_gate3_placement_worksheet.py "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_gate3_placement_worksheet.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate3_placement.csv`"
        in template
    )
    assert (
        "`uv run python scripts/write_row_coupon_first_print_gate4_wet_dry_witness_worksheet.py "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_gate4_wet_dry_witness_worksheet.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate4_wet_dry_witness.csv`"
        in template
    )
    assert (
        "`uv run python "
        "scripts/write_row_coupon_first_print_gate5_consumable_puncture_worksheet.py "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv`"
        in template
    )
    assert (
        "`uv run python "
        "scripts/audit_row_coupon_first_print_gate5_consumable_puncture_worksheet.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate5_consumable_puncture.csv`"
        in template
    )
    assert (
        "`uv run python scripts/write_row_coupon_first_print_gate6_sensor_thermal_worksheet.py "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_gate6_sensor_thermal.csv`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_gate6_sensor_thermal_worksheet.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_gate6_sensor_thermal.csv`"
        in template
    )
    assert (
        "`uv run python scripts/write_row_coupon_first_print_install_inventory.py "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_install_inventory.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_install_inventory.csv`"
        in template
    )
    assert (
        "`uv run python scripts/write_row_coupon_first_print_service_state_review.py "
        "--output data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv "
        "--bounds-evidence-dir "
        "data/measurements/YYYY-MM-DD_one_row_coupon_service_state_bounds`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_service_state_review.py "
        "--worksheet data/measurements/YYYY-MM-DD_one_row_coupon_service_state_review.csv "
        "--require-service-state-review-ready`"
        in template
    )
    assert (
        "`uv run python scripts/audit_row_coupon_first_print_preflight.py "
        "--record data/measurements/YYYY-MM-DD_one_row_coupon_first_print.md`"
        in template
    )
    assert "`uv run python scripts/audit_row_coupon_first_print_slicer_queue.py`" in template


def test_passive_leak_protocol_links_from_first_print_gate4_records() -> None:
    protocol = PASSIVE_LEAK_PROTOCOL.read_text()
    template = FIRST_PRINT_TEMPLATE.read_text()
    live_record = (
        ROOT
        / "data"
        / "measurements"
        / "2026-06-02_one_row_coupon_first_print.md"
    ).read_text()
    readiness = (ROOT / "docs" / "protocols" / "one_row_coupon_first_print_readiness.md")
    knowledge = (ROOT / "docs" / "knowledge" / "README.md")

    link = "docs/protocols/row_coupon_passive_leak_wet_dry_validation.md"
    assert "# Row Coupon Passive Leak And Wet/Dry Validation" in protocol
    assert "Gate 4 remains blocked" in protocol
    assert link in template
    assert link in live_record
    assert link in readiness.read_text()
    assert "row_coupon_passive_leak_wet_dry_validation.md" in knowledge.read_text()


def test_passive_leak_template_tracks_gate4_witness_targets() -> None:
    template = PASSIVE_LEAK_TEMPLATE.read_text()

    for target in (
        "Dry-bay protected volume",
        "Dry-bay ingress audit",
        "Side-gas service witness set",
        "Sample/relief cap witness set",
        "Gasket-tab root witness set",
        "Dry-bay aperture thresholds",
        "Aperture-adjacent witness gutters",
    ):
        assert f"| {target} |  |  | not_tested |  |" in template
    for inspection in (
        "Side gas fitting exterior - supply",
        "Sample/relief cap seat",
        "Optical apertures and thresholds",
        "Connector shrouds",
    ):
        assert inspection in template


def test_first_print_qc_targets_track_printed_and_flexible_manifest_parts() -> None:
    params = load_params(PARAMS)
    manifest = row_coupon_part_manifest()["installed"]
    expected_names = [
        name
        for name, entry in manifest.items()
        if artifact_category(entry["fabrication_source"])
        in {"printed", "compressible_or_flexible"}
    ]

    targets = first_print_qc_targets(params)
    target_markdown = first_print_qc_target_bounds_markdown(params)

    assert [target.name for target in targets] == expected_names
    assert all(target.target_x_mm > 0 for target in targets)
    assert all(target.target_y_mm > 0 for target in targets)
    assert all(target.target_z_mm > 0 for target in targets)
    assert not any(target.name == "cots_microplates" for target in targets)
    assert "do\nnot mark Gate 1 passed" in target_markdown


def test_first_print_ot2_placement_targets_markdown_uses_layout_values() -> None:
    params = load_params(PARAMS)
    targets = first_print_gate3_placement_targets(params)
    target_markdown = first_print_ot2_placement_targets_markdown(params)

    assert [target.target for target in targets] == [
        "Assembly deck-to-top envelope",
        "Assembly footprint X",
        "Assembly footprint Y",
        "Deck pod seating repeatability",
        "Adjacent-slot service clearance",
        "Required adjacent-slot clearance",
        "Operating service dress envelope",
        "Row tiling/service clearance check",
        "OT-2 toolhead swept body envelope",
        "OT-2 toolhead lower clearance",
        "Pipette puncture targets",
        "Dry-bay protected footprint",
    ]
    assert "## Gate 3 CAD Placement Targets" in target_markdown
    assert "| Assembly deck-to-top envelope | 140.60 mm |" in target_markdown
    assert "measured high point <= 141.60 mm" in target_markdown
    assert "| Assembly footprint X | 148.60 mm |" in target_markdown
    assert "| Assembly footprint Y | 377.25 mm |" in target_markdown
    assert (
        "| Deck pod seating repeatability | 16 feet / 16 keys / "
        "4 slots / 5 cycles |" in target_markdown
    )
    assert "five seat/release cycles prove no rocking" in target_markdown
    assert "| Adjacent-slot service clearance | 4.10 mm |" in target_markdown
    assert "| Required adjacent-slot clearance | 2.00 mm |" in target_markdown
    assert (
        "| Operating service dress envelope | 220.60 x 348.75 x 43.30 mm / "
        "11 envelopes |"
    ) in target_markdown
    assert (
        "| Row tiling/service clearance check | 8 neighbor keepouts / "
        "11 service envelopes / 4.10 mm minimum clearance |"
    ) in target_markdown
    assert (
        "| OT-2 toolhead swept body envelope | 250.00 x 445.50 x 45.00 mm / "
        "384 wells |"
    ) in target_markdown
    assert (
        "| OT-2 toolhead lower clearance | 8.00 mm assembly / 27.90 mm "
        "services / 2.00 mm tip path |"
    ) in target_markdown
    assert "without measured two-pipette OT-2 toolhead evidence" in target_markdown
    assert "| Pipette puncture targets | 384 wells |" in target_markdown
    assert "| Dry-bay protected footprint | 120.20 x 357.50 mm |" in target_markdown


def test_first_print_gate3_placement_worksheet_csv_has_blank_evidence() -> None:
    params = load_params(PARAMS)
    worksheet = first_print_gate3_placement_worksheet_csv(params)
    rows = list(csv.DictReader(StringIO(worksheet)))

    assert len(rows) == 12
    assert rows[0]["target"] == "Assembly deck-to-top envelope"
    assert rows[0]["cad_value"] == "140.60 mm"
    assert rows[0]["physical_check"] == "measured high point <= 141.60 mm"
    assert rows[3]["target"] == "Deck pod seating repeatability"
    assert rows[3]["cad_value"] == "16 feet / 16 keys / 4 slots / 5 cycles"
    assert rows[6]["target"] == "Operating service dress envelope"
    assert rows[6]["cad_value"] == "220.60 x 348.75 x 43.30 mm / 11 envelopes"
    assert rows[7]["target"] == "Row tiling/service clearance check"
    assert (
        rows[7]["cad_value"]
        == "8 neighbor keepouts / 11 service envelopes / 4.10 mm minimum clearance"
    )
    assert rows[8]["target"] == "OT-2 toolhead swept body envelope"
    assert rows[8]["cad_value"] == "250.00 x 445.50 x 45.00 mm / 384 wells"
    assert rows[9]["target"] == "OT-2 toolhead lower clearance"
    assert (
        rows[9]["cad_value"]
        == "8.00 mm assembly / 27.90 mm services / 2.00 mm tip path"
    )
    assert all(row["measured_value"] == "" for row in rows)
    assert all(row["evidence_path"] == "" for row in rows)
    assert all(row["result"] == "not_tested" for row in rows)


def test_write_first_print_gate3_placement_worksheet_refuses_overwrite(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    output_path = tmp_path / "gate3_placement.csv"
    output_path.write_text("existing")

    with pytest.raises(FileExistsError):
        write_first_print_gate3_placement_worksheet(
            params=params,
            output_path=output_path,
        )


def test_first_print_gate3_placement_worksheet_rows_match_target_count() -> None:
    params = load_params(PARAMS)

    rows = first_print_gate3_placement_worksheet_rows(params)

    assert len(rows) == len(first_print_gate3_placement_targets(params))
    assert rows[0].result == "not_tested"
    assert rows[3].target == "Deck pod seating repeatability"
    assert rows[6].target == "Operating service dress envelope"
    assert rows[7].target == "Row tiling/service clearance check"
    assert rows[8].target == "OT-2 toolhead swept body envelope"
    assert rows[9].target == "OT-2 toolhead lower clearance"


def test_audit_first_print_gate3_placement_accepts_blank_preplacement_sheet(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    worksheet_path = tmp_path / "gate3_placement.csv"
    worksheet_path.write_text(first_print_gate3_placement_worksheet_csv(params))

    audit = audit_first_print_gate3_placement_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert not audit.gate3_pass_ready
    assert audit.expected_row_count == 12
    assert audit.actual_row_count == 12
    assert audit.result_counts["not_tested"] == 12
    assert audit.issues == ()


def test_audit_first_print_gate3_placement_passes_evidenced_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(csv.DictReader(StringIO(first_print_gate3_placement_worksheet_csv(params))))
    for row in rows:
        row["measured_value"] = f"measured {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    worksheet_path = tmp_path / "gate3_placement.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate3_placement_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert audit.gate3_pass_ready
    assert audit.result_counts["pass"] == 12


def test_audit_first_print_gate3_placement_rejects_stale_cad_value(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(csv.DictReader(StringIO(first_print_gate3_placement_worksheet_csv(params))))
    rows[6]["cad_value"] = "stale service dress"
    worksheet_path = tmp_path / "gate3_placement.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate3_placement_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate3_pass_ready
    assert any(
        issue.target == "Operating service dress envelope"
        and issue.field == "cad_value"
        for issue in audit.issues
    )


def test_audit_first_print_gate3_placement_rejects_false_pass_claim(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(csv.DictReader(StringIO(first_print_gate3_placement_worksheet_csv(params))))
    rows[0]["result"] = "pass"
    worksheet_path = tmp_path / "gate3_placement.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate3_placement_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate3_pass_ready
    assert any(issue.field == "measured_value" for issue in audit.issues)
    assert any(issue.field == "evidence_path" for issue in audit.issues)


def test_first_print_dry_assembly_targets_markdown_uses_layout_values() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    targets = first_print_gate2_dry_assembly_targets(params)
    target_markdown = first_print_dry_assembly_targets_markdown(params)
    targets_by_name = {target.target: target for target in targets}

    assert [target.target for target in targets] == [
        "Installed dry stack",
        "Plate/mat service cycles",
        "Plate support datum",
        "Plate locator rails",
        "Consumable nominal envelope",
        "Latch gasket squeeze budget",
        "Wedge lock stations",
        "Latch asymmetry watch",
        "Latch self-lock margin",
        "Latch retention/span evidence",
        "Fail-closed pre-run inspection",
        "Side gas service dry fit",
        "Electrical service dry fit",
        "Sensor package dry fit",
        "Dry-bay open volume",
    ]
    assert "## Gate 2 CAD Dry Assembly Targets" in target_markdown
    assert (
        "| Installed dry stack | 4 plates / 4 mats / 2 perimeter gaskets |"
        in target_markdown
    )
    assert "| Plate/mat service cycles | 5 cycles each |" in target_markdown
    assert "| Plate support datum | z=10.00..24.30 mm |" in target_markdown
    assert "| Plate locator rails | 16 rails / 1.20 mm high |" in target_markdown
    assert (
        "| Consumable nominal envelope | 127.60 x 85.75 mm plate / "
        "4.50 mm mat stack |" in target_markdown
    )
    assert (
        "| Latch gasket squeeze budget | 0.55 mm target / 0.20..0.80 mm allowed |"
        in target_markdown
    )
    assert "| Wedge lock stations | 9 locks / 9.00 mm travel body |" in target_markdown
    assert (
        "| Latch asymmetry watch | 1 omitted / 181.00 mm max span |"
        in target_markdown
    )
    assert (
        "| Latch self-lock margin | 0.32 deg / detent_or_physical_test_required |"
        in target_markdown
    )
    assert (
        "| Latch retention/span evidence | 0.32 deg margin / 181.00 mm span / "
        "1 omitted |" in target_markdown
    )
    assert (
        "| Fail-closed pre-run inspection | 10 checkpoints / "
        "any_blocker_not_passed_prevents_ot2_operation |" in target_markdown
    )
    assert (
        "| Side gas service dry fit | 2 tubes / 36.00 mm envelope / "
        "18.00 mm bend radius |" in target_markdown
    )
    assert (
        "| Electrical service dry fit | 3 pigtails / 12.00 mm bend radius |"
        in target_markdown
    )
    assert "| Sensor package dry fit | 2 gas PCB / 4 SHT41 / 4 IR |" in target_markdown
    assert "| Dry-bay open volume | 120.20 x 357.50 x 80.00 mm |" in target_markdown
    assert "do not mark Gate 2 passed" in target_markdown
    assert targets_by_name["Installed dry stack"].cad_value == str(
        layout["assembly_state_witness_check"]["stack_cad_value"]
    )
    assert targets_by_name["Latch gasket squeeze budget"].cad_value == str(
        layout["gasket_compression_gap_gauge"]["cad_value"]
    )
    assert targets_by_name["Fail-closed pre-run inspection"].cad_value == str(
        layout["fail_closed_prerun_inspection_check"]["cad_value"]
    )


def test_first_print_gate2_dry_assembly_worksheet_csv_has_blank_evidence() -> None:
    params = load_params(PARAMS)
    worksheet = first_print_gate2_dry_assembly_worksheet_csv(params)
    rows = list(csv.DictReader(StringIO(worksheet)))

    assert len(rows) == 15
    assert rows[0]["target"] == "Installed dry stack"
    assert rows[0]["cad_value"] == "4 plates / 4 mats / 2 perimeter gaskets"
    assert rows[9]["target"] == "Latch retention/span evidence"
    assert rows[9]["cad_value"] == "0.32 deg margin / 181.00 mm span / 1 omitted"
    assert rows[10]["target"] == "Fail-closed pre-run inspection"
    assert (
        rows[10]["cad_value"]
        == "10 checkpoints / any_blocker_not_passed_prevents_ot2_operation"
    )
    assert rows[11]["target"] == "Side gas service dry fit"
    assert rows[11]["cad_value"] == "2 tubes / 36.00 mm envelope / 18.00 mm bend radius"
    assert rows[14]["target"] == "Dry-bay open volume"
    assert rows[14]["cad_value"] == "120.20 x 357.50 x 80.00 mm"
    assert all(row["measured_value"] == "" for row in rows)
    assert all(row["evidence_path"] == "" for row in rows)
    assert all(row["result"] == "not_tested" for row in rows)


def test_write_first_print_gate2_dry_assembly_worksheet_refuses_overwrite(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    output_path = tmp_path / "gate2_dry_assembly.csv"
    output_path.write_text("existing")

    with pytest.raises(FileExistsError):
        write_first_print_gate2_dry_assembly_worksheet(
            params=params,
            output_path=output_path,
        )


def test_first_print_gate2_dry_assembly_worksheet_rows_match_target_count() -> None:
    params = load_params(PARAMS)

    rows = first_print_gate2_dry_assembly_worksheet_rows(params)

    assert len(rows) == len(first_print_gate2_dry_assembly_targets(params))
    assert rows[0].result == "not_tested"
    assert rows[9].target == "Latch retention/span evidence"
    assert rows[10].target == "Fail-closed pre-run inspection"


def test_audit_first_print_gate2_dry_assembly_accepts_blank_dry_fit_sheet(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    worksheet_path = tmp_path / "gate2_dry_assembly.csv"
    worksheet_path.write_text(first_print_gate2_dry_assembly_worksheet_csv(params))

    audit = audit_first_print_gate2_dry_assembly_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert not audit.gate2_pass_ready
    assert audit.expected_row_count == 15
    assert audit.actual_row_count == 15
    assert audit.result_counts["not_tested"] == 15
    assert audit.issues == ()


def test_audit_first_print_gate2_dry_assembly_passes_evidenced_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(StringIO(first_print_gate2_dry_assembly_worksheet_csv(params)))
    )
    for row in rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    worksheet_path = tmp_path / "gate2_dry_assembly.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate2_dry_assembly_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert audit.gate2_pass_ready
    assert audit.result_counts["pass"] == 15


def test_audit_first_print_gate2_dry_assembly_rejects_missing_evidence_file(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(StringIO(first_print_gate2_dry_assembly_worksheet_csv(params)))
    )
    for row in rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        row["result"] = "pass"
    worksheet_path = tmp_path / "gate2_dry_assembly.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate2_dry_assembly_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate2_pass_ready
    assert any(
        issue.field == "evidence_path"
        and issue.message == "evidence path does not exist"
        for issue in audit.issues
    )


def test_audit_first_print_gate2_dry_assembly_rejects_stale_cad_value(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(StringIO(first_print_gate2_dry_assembly_worksheet_csv(params)))
    )
    side_gas_row = next(row for row in rows if row["target"] == "Side gas service dry fit")
    side_gas_row["cad_value"] = "stale dry fit"
    worksheet_path = tmp_path / "gate2_dry_assembly.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate2_dry_assembly_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate2_pass_ready
    assert any(
        issue.target == "Side gas service dry fit" and issue.field == "cad_value"
        for issue in audit.issues
    )


def test_audit_first_print_gate2_dry_assembly_rejects_false_pass_claim(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(StringIO(first_print_gate2_dry_assembly_worksheet_csv(params)))
    )
    rows[0]["result"] = "pass"
    worksheet_path = tmp_path / "gate2_dry_assembly.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate2_dry_assembly_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate2_pass_ready
    assert any(issue.field == "measured_value" for issue in audit.issues)
    assert any(issue.field == "evidence_path" for issue in audit.issues)


def test_first_print_wet_dry_witness_targets_markdown_uses_layout_values() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    targets = first_print_gate4_wet_dry_witness_targets(params)
    target_markdown = first_print_wet_dry_witness_targets_markdown(params)
    targets_by_name = {target.target: target for target in targets}

    assert [target.target for target in targets] == [
        "Headspace barrier perimeter",
        "Shared wet headspace volume",
        "Dry-bay protected volume",
        "Dry-bay ingress audit",
        "Dry-bay boundary rail clearance",
        "Side-gas service witness set",
        "Sample/relief cap witness set",
        "Gasket-tab root witness set",
        "Dry-bay aperture thresholds",
        "Aperture-adjacent witness gutters",
    ]
    assert "## Gate 4 CAD Wet/Dry Witness Targets" in target_markdown
    assert (
        "| Headspace barrier perimeter | "
        "148.60 x 377.25 x 5.80 mm perimeter, 2.00 mm wall |"
        in target_markdown
    )
    assert (
        "| Shared wet headspace volume | "
        "138.60 x 367.25 x 5.80 mm shared volume |"
        in target_markdown
    )
    assert "| Dry-bay protected volume | 120.20 x 357.50 x 80.00 mm |" in target_markdown
    assert (
        "| Dry-bay ingress audit | 10 wet collectors / 7 inboard dams / "
        "1 protected footprint |" in target_markdown
    )
    assert (
        "| Dry-bay boundary rail clearance | "
        "132.20 x 357.50 x 3.00 mm, 4.00 mm rails |"
        in target_markdown
    )
    assert "| Side-gas service witness set | 4 wet collectors / 2 inboard dams |" in target_markdown
    assert (
        "| Sample/relief cap witness set | 2 wet collectors / 1 inboard dams |"
        in target_markdown
    )
    assert "| Gasket-tab root witness set | 4 wet collectors / 4 inboard dams |" in target_markdown
    assert "| Dry-bay aperture thresholds | 4 raised thresholds |" in target_markdown
    assert "| Aperture-adjacent witness gutters | 8 gutters, 0.45 mm depth |" in target_markdown
    assert targets_by_name["Headspace barrier perimeter"].cad_value == str(
        layout["headspace_barrier_check"]["cad_value"]
    )
    assert targets_by_name["Shared wet headspace volume"].cad_value == str(
        layout["headspace_volume_check"]["cad_value"]
    )
    assert targets_by_name["Dry-bay protected volume"].cad_value == str(
        layout["dry_bay_envelope_check"]["cad_value"]
    )
    assert targets_by_name["Dry-bay boundary rail clearance"].cad_value == str(
        layout["dry_bay_boundary_check"]["cad_value"]
    )
    assert targets_by_name["Sample/relief cap witness set"].cad_value == str(
        layout["sample_relief_leak_witness_check"]["cad_value"]
    )
    assert targets_by_name["Gasket-tab root witness set"].cad_value == str(
        layout["gasket_tab_leak_witness_check"]["cad_value"]
    )
    assert targets_by_name["Dry-bay aperture thresholds"].cad_value == str(
        layout["wet_dry_failure_path_check"]["threshold_cad_value"]
    )
    assert targets_by_name["Aperture-adjacent witness gutters"].cad_value == str(
        layout["wet_dry_failure_path_check"]["gutter_cad_value"]
    )


def test_first_print_gate4_wet_dry_witness_worksheet_csv_has_blank_evidence() -> None:
    params = load_params(PARAMS)
    worksheet = first_print_gate4_wet_dry_witness_worksheet_csv(params)
    rows = list(csv.DictReader(StringIO(worksheet)))

    assert len(rows) == 10
    assert rows[0]["target"] == "Headspace barrier perimeter"
    assert rows[0]["cad_value"] == (
        "148.60 x 377.25 x 5.80 mm perimeter, 2.00 mm wall"
    )
    assert rows[1]["target"] == "Shared wet headspace volume"
    assert rows[1]["cad_value"] == "138.60 x 367.25 x 5.80 mm shared volume"
    assert rows[2]["target"] == "Dry-bay protected volume"
    assert rows[2]["cad_value"] == "120.20 x 357.50 x 80.00 mm"
    assert rows[3]["target"] == "Dry-bay ingress audit"
    assert rows[3]["cad_value"] == (
        "10 wet collectors / 7 inboard dams / 1 protected footprint"
    )
    assert rows[4]["target"] == "Dry-bay boundary rail clearance"
    assert rows[4]["cad_value"] == "132.20 x 357.50 x 3.00 mm, 4.00 mm rails"
    assert rows[5]["target"] == "Side-gas service witness set"
    assert rows[5]["cad_value"] == "4 wet collectors / 2 inboard dams"
    assert rows[9]["target"] == "Aperture-adjacent witness gutters"
    assert rows[9]["cad_value"] == "8 gutters, 0.45 mm depth"
    assert all(row["measured_value"] == "" for row in rows)
    assert all(row["evidence_path"] == "" for row in rows)
    assert all(row["result"] == "not_tested" for row in rows)


def test_write_first_print_gate4_wet_dry_witness_worksheet_refuses_overwrite(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    output_path = tmp_path / "gate4_wet_dry_witness.csv"
    output_path.write_text("existing")

    with pytest.raises(FileExistsError):
        write_first_print_gate4_wet_dry_witness_worksheet(
            params=params,
            output_path=output_path,
        )


def test_first_print_gate4_wet_dry_witness_worksheet_rows_match_target_count() -> None:
    params = load_params(PARAMS)

    rows = first_print_gate4_wet_dry_witness_worksheet_rows(params)

    assert len(rows) == len(first_print_gate4_wet_dry_witness_targets(params))
    assert rows[0].result == "not_tested"
    assert rows[9].target == "Aperture-adjacent witness gutters"


def test_audit_first_print_gate4_wet_dry_witness_accepts_blank_witness_sheet(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    worksheet_path = tmp_path / "gate4_wet_dry_witness.csv"
    worksheet_path.write_text(first_print_gate4_wet_dry_witness_worksheet_csv(params))

    audit = audit_first_print_gate4_wet_dry_witness_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert not audit.gate4_pass_ready
    assert audit.expected_row_count == 10
    assert audit.actual_row_count == 10
    assert audit.result_counts["not_tested"] == 10
    assert audit.issues == ()


def test_audit_first_print_gate4_wet_dry_witness_passes_evidenced_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(StringIO(first_print_gate4_wet_dry_witness_worksheet_csv(params)))
    )
    for row in rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    worksheet_path = tmp_path / "gate4_wet_dry_witness.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate4_wet_dry_witness_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert audit.gate4_pass_ready
    assert audit.result_counts["pass"] == 10


def test_audit_first_print_gate4_wet_dry_witness_rejects_stale_cad_value(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(StringIO(first_print_gate4_wet_dry_witness_worksheet_csv(params)))
    )
    rows[5]["cad_value"] = "stale witness set"
    worksheet_path = tmp_path / "gate4_wet_dry_witness.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate4_wet_dry_witness_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate4_pass_ready
    assert any(
        issue.target == "Side-gas service witness set"
        and issue.field == "cad_value"
        for issue in audit.issues
    )


def test_audit_first_print_gate4_wet_dry_witness_rejects_false_pass_claim(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(StringIO(first_print_gate4_wet_dry_witness_worksheet_csv(params)))
    )
    rows[0]["result"] = "pass"
    worksheet_path = tmp_path / "gate4_wet_dry_witness.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate4_wet_dry_witness_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate4_pass_ready
    assert any(issue.field == "measured_value" for issue in audit.issues)
    assert any(issue.field == "evidence_path" for issue in audit.issues)


def test_first_print_consumable_puncture_targets_markdown_uses_layout_values() -> None:
    params = load_params(PARAMS)
    targets = first_print_gate5_consumable_puncture_targets(params)
    target_markdown = first_print_consumable_puncture_targets_markdown(params)

    assert [target.target for target in targets] == [
        "Installed consumable set",
        "Consumable metrology gauge",
        "Plate CAD footprint",
        "Plate support datum",
        "Locator rail count/height",
        "Mat CAD thickness stack",
        "Mat plug CAD diameter/depth",
        "Mat slit CAD relief",
        "Puncture target count",
        "Puncture swept diameter",
        "Puncture Z range",
        "Puncture force limit",
        "Repeat puncture minimum",
        "Plate lateral shift limit",
    ]
    assert "## Gate 5 CAD Consumable/Puncture Targets" in target_markdown
    assert "| Installed consumable set | 4 plates / 4 septum mats |" in target_markdown
    assert (
        "| Consumable metrology gauge | 143.60 x 101.75 x 3.00 mm |"
        in target_markdown
    )
    assert "required gauge checks plate/mat lot fit" in target_markdown
    assert "| Plate CAD footprint | 127.60 x 85.75 x 14.30 mm |" in target_markdown
    assert "| Plate support datum | z=10.00 mm |" in target_markdown
    assert "| Locator rail count/height | 16 rails / 1.20 mm |" in target_markdown
    assert "| Mat CAD thickness stack | 4.50 mm |" in target_markdown
    assert "| Mat plug CAD diameter/depth | 6.00 mm / 3.50 mm |" in target_markdown
    assert "| Mat slit CAD relief | 2.00 x 0.35 mm |" in target_markdown
    assert "| Puncture target count | 384 wells |" in target_markdown
    assert "required swept-path validation body covers all 96 positions per plate" in (
        target_markdown
    )
    assert "| Puncture swept diameter | 2.50 mm |" in target_markdown
    assert "| Puncture Z range | 22.80..64.10 mm |" in target_markdown
    assert "| Puncture force limit | 8.00 N |" in target_markdown
    assert "| Repeat puncture minimum | 20 cycles |" in target_markdown
    assert "| Plate lateral shift limit | <=0.25 mm |" in target_markdown


def test_first_print_gate5_consumable_puncture_worksheet_csv_has_blank_evidence() -> None:
    params = load_params(PARAMS)
    worksheet = first_print_gate5_consumable_puncture_worksheet_csv(params)
    rows = list(csv.DictReader(StringIO(worksheet)))

    assert len(rows) == 14
    assert rows[0]["target"] == "Installed consumable set"
    assert rows[0]["cad_value"] == "4 plates / 4 septum mats"
    assert rows[1]["target"] == "Consumable metrology gauge"
    assert rows[1]["cad_value"] == "143.60 x 101.75 x 3.00 mm"
    assert rows[8]["target"] == "Puncture target count"
    assert rows[8]["cad_value"] == "384 wells"
    assert rows[9]["target"] == "Puncture swept diameter"
    assert rows[9]["cad_value"] == "2.50 mm"
    assert rows[10]["target"] == "Puncture Z range"
    assert rows[10]["cad_value"] == "22.80..64.10 mm"
    assert rows[11]["target"] == "Puncture force limit"
    assert rows[11]["cad_value"] == "8.00 N"
    assert rows[13]["target"] == "Plate lateral shift limit"
    assert rows[13]["cad_value"] == "<=0.25 mm"
    assert all(row["measured_value"] == "" for row in rows)
    assert all(row["evidence_path"] == "" for row in rows)
    assert all(row["result"] == "not_tested" for row in rows)


def test_write_first_print_gate5_consumable_puncture_worksheet_refuses_overwrite(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    output_path = tmp_path / "gate5_consumable_puncture.csv"
    output_path.write_text("existing")

    with pytest.raises(FileExistsError):
        write_first_print_gate5_consumable_puncture_worksheet(
            params=params,
            output_path=output_path,
        )


def test_first_print_gate5_consumable_puncture_worksheet_rows_match_target_count() -> None:
    params = load_params(PARAMS)

    rows = first_print_gate5_consumable_puncture_worksheet_rows(params)

    assert len(rows) == len(first_print_gate5_consumable_puncture_targets(params))
    assert rows[0].result == "not_tested"
    assert rows[1].target == "Consumable metrology gauge"
    assert rows[8].target == "Puncture target count"


def test_audit_first_print_gate5_consumable_puncture_accepts_blank_sheet(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    worksheet_path = tmp_path / "gate5_consumable_puncture.csv"
    worksheet_path.write_text(first_print_gate5_consumable_puncture_worksheet_csv(params))

    audit = audit_first_print_gate5_consumable_puncture_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert not audit.gate5_pass_ready
    assert audit.expected_row_count == 14
    assert audit.actual_row_count == 14
    assert audit.result_counts["not_tested"] == 14
    assert audit.issues == ()


def test_audit_first_print_gate5_consumable_puncture_passes_evidenced_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(
            StringIO(first_print_gate5_consumable_puncture_worksheet_csv(params))
        )
    )
    for row in rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    worksheet_path = tmp_path / "gate5_consumable_puncture.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate5_consumable_puncture_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert audit.gate5_pass_ready
    assert audit.result_counts["pass"] == 14


def test_audit_first_print_gate5_consumable_puncture_rejects_stale_cad_value(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(
            StringIO(first_print_gate5_consumable_puncture_worksheet_csv(params))
        )
    )
    puncture_row = next(row for row in rows if row["target"] == "Puncture target count")
    puncture_row["cad_value"] = "stale puncture count"
    worksheet_path = tmp_path / "gate5_consumable_puncture.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate5_consumable_puncture_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate5_pass_ready
    assert any(
        issue.target == "Puncture target count" and issue.field == "cad_value"
        for issue in audit.issues
    )


def test_audit_first_print_gate5_consumable_puncture_rejects_false_pass_claim(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(
            StringIO(first_print_gate5_consumable_puncture_worksheet_csv(params))
        )
    )
    rows[0]["result"] = "pass"
    worksheet_path = tmp_path / "gate5_consumable_puncture.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate5_consumable_puncture_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate5_pass_ready
    assert any(issue.field == "measured_value" for issue in audit.issues)
    assert any(issue.field == "evidence_path" for issue in audit.issues)


def test_first_print_sensor_thermal_targets_markdown_uses_layout_values() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    targets = first_print_gate6_sensor_thermal_targets(params)
    target_markdown = first_print_sensor_thermal_targets_markdown(params)
    targets_by_name = {target.target: target for target in targets}

    assert [target.target for target in targets] == [
        "Sensor install workflow",
        "Gas PCB cartridges",
        "Gas PCB aperture/dead volume",
        "Gas PCB gasket",
        "Headspace SHT41 carriers",
        "Headspace SHT41 aperture",
        "IR thermopile pockets",
        "IR aperture/gasket",
        "IR proxy FOV spot",
        "Harness route count",
        "Service connectors/cables",
        "Sensor connector service clearance",
        "Service cable envelope",
        "Service cable bend envelope",
        "Observer front-end swept volume",
        "Observer carriage reserved volume",
        "Observer service raceway envelope",
        "Observer optical stability evidence",
        "Observer kinematic split evidence",
        "Thermal proxy plan",
    ]
    assert "## Gate 6 CAD Sensor/Thermal Targets" in target_markdown
    assert "| Sensor install workflow | 10 steps / 7 gates |" in target_markdown
    assert "| Gas PCB cartridges | 2 cartridges, 5.00 x 30.00 x 25.00 mm |" in target_markdown
    assert (
        "| Gas PCB aperture/dead volume | 2.00 mm aperture / 12.80 mm3 cell |"
        in target_markdown
    )
    assert "required duct sampling cell validation body" in target_markdown
    assert (
        "| Gas PCB gasket | 0.60 mm gasket / 0.20 mm compression |"
        in target_markdown
    )
    assert (
        "| Headspace SHT41 carriers | 4 carriers, 12.00 x 12.00 x 4.00 mm |"
        in target_markdown
    )
    assert (
        "| Headspace SHT41 aperture | 3.00 mm aperture / 5.20 mm drip ring OD |"
        in target_markdown
    )
    assert (
        "| IR thermopile pockets | 4 pockets, 8.00 x 8.00 x 4.50 mm |"
        in target_markdown
    )
    assert (
        "| IR aperture/gasket | 6.00 mm aperture / 0.45 mm gasket / "
        "0.12 mm compression |" in target_markdown
    )
    assert (
        "| IR proxy FOV spot | 1.08 mm at plate margin, 12.00 deg FOV |"
        in target_markdown
    )
    assert "| Harness route count | 4 lower / 6 lid routes |" in target_markdown
    assert (
        "| Service connectors/cables | 3 connectors / 3 cable envelopes |"
        in target_markdown
    )
    assert (
        "| Sensor connector service clearance | "
        f"{layout['sensor_connector_service_clearance_check']['cad_value']} |"
        in target_markdown
    )
    assert "| Service cable envelope | 6.00 x 30.00 x 5.10 mm |" in target_markdown
    assert (
        "| Service cable bend envelope | 12.00 mm bend radius / 18.00 mm "
        "straight |" in target_markdown
    )
    assert (
        "| Observer front-end swept volume | 120.00 x 347.50 x 40.00 mm |"
        in target_markdown
    )
    assert (
        "| Observer carriage reserved volume | 100.00 x 58.00 x 62.00 mm |"
        in target_markdown
    )
    assert (
        "| Observer service raceway envelope | 8.00 x 357.50 x 24.00 mm |"
        in target_markdown
    )
    assert (
        "| Observer optical stability evidence | 8 checks / 4 apertures / "
        "32 targets |" in target_markdown
    )
    assert (
        "| Observer kinematic split evidence | 5 checks / 3 split envelopes / "
        "32 targets |" in target_markdown
    )
    assert (
        "| Thermal proxy plan | 4 center refs / 4 IR proxies / 4 SHT41 points / "
        "4 condensation pockets |" in target_markdown
    )
    assert "do not mark Gate 6 passed" in target_markdown
    assert "do not prove gas response" in target_markdown
    assert targets_by_name["IR proxy FOV spot"].cad_value == str(
        layout["ir_thermopile_fov_spot_check"]["spot_cad_value"]
    )
    assert targets_by_name["Observer optical stability evidence"].cad_value == str(
        layout["observer_optical_stability_check"]["cad_value"]
    )
    assert targets_by_name["Observer kinematic split evidence"].cad_value == str(
        layout["observer_kinematic_split_check"]["cad_value"]
    )
    assert targets_by_name["Thermal proxy plan"].cad_value == str(
        layout["thermal_condensation_proxy_check"]["cad_value"]
    )


def test_first_print_gate6_sensor_thermal_worksheet_csv_has_blank_evidence() -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    worksheet = first_print_gate6_sensor_thermal_worksheet_csv(params)
    rows = list(csv.DictReader(StringIO(worksheet)))

    assert len(rows) == 20
    assert rows[0]["target"] == "Sensor install workflow"
    assert rows[0]["cad_value"] == "10 steps / 7 gates"
    assert rows[1]["target"] == "Gas PCB cartridges"
    assert rows[1]["cad_value"] == "2 cartridges, 5.00 x 30.00 x 25.00 mm"
    assert rows[3]["target"] == "Gas PCB gasket"
    assert rows[3]["cad_value"] == "0.60 mm gasket / 0.20 mm compression"
    assert rows[10]["target"] == "Service connectors/cables"
    assert rows[10]["cad_value"] == "3 connectors / 3 cable envelopes"
    assert rows[11]["target"] == "Sensor connector service clearance"
    assert rows[11]["cad_value"] == str(
        layout["sensor_connector_service_clearance_check"]["cad_value"]
    )
    assert rows[12]["target"] == "Service cable envelope"
    assert rows[12]["cad_value"] == "6.00 x 30.00 x 5.10 mm"
    assert rows[13]["target"] == "Service cable bend envelope"
    assert rows[13]["cad_value"] == "12.00 mm bend radius / 18.00 mm straight"
    assert rows[14]["target"] == "Observer front-end swept volume"
    assert rows[14]["cad_value"] == "120.00 x 347.50 x 40.00 mm"
    assert rows[15]["target"] == "Observer carriage reserved volume"
    assert rows[15]["cad_value"] == "100.00 x 58.00 x 62.00 mm"
    assert rows[16]["target"] == "Observer service raceway envelope"
    assert rows[16]["cad_value"] == "8.00 x 357.50 x 24.00 mm"
    assert rows[17]["target"] == "Observer optical stability evidence"
    assert rows[17]["cad_value"] == "8 checks / 4 apertures / 32 targets"
    assert rows[18]["target"] == "Observer kinematic split evidence"
    assert rows[18]["cad_value"] == "5 checks / 3 split envelopes / 32 targets"
    assert rows[19]["target"] == "Thermal proxy plan"
    assert rows[19]["cad_value"] == (
        "4 center refs / 4 IR proxies / 4 SHT41 points / 4 condensation pockets"
    )
    assert all(row["measured_value"] == "" for row in rows)
    assert all(row["evidence_path"] == "" for row in rows)
    assert all(row["result"] == "not_tested" for row in rows)


def test_write_first_print_gate6_sensor_thermal_worksheet_refuses_overwrite(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    output_path = tmp_path / "gate6_sensor_thermal.csv"
    output_path.write_text("existing")

    with pytest.raises(FileExistsError):
        write_first_print_gate6_sensor_thermal_worksheet(
            params=params,
            output_path=output_path,
        )


def test_first_print_gate6_sensor_thermal_worksheet_rows_match_target_count() -> None:
    params = load_params(PARAMS)

    rows = first_print_gate6_sensor_thermal_worksheet_rows(params)

    assert len(rows) == len(first_print_gate6_sensor_thermal_targets(params))
    assert rows[0].result == "not_tested"
    assert rows[3].target == "Gas PCB gasket"


def test_audit_first_print_gate6_sensor_thermal_accepts_blank_sheet(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    worksheet_path = tmp_path / "gate6_sensor_thermal.csv"
    worksheet_path.write_text(first_print_gate6_sensor_thermal_worksheet_csv(params))

    audit = audit_first_print_gate6_sensor_thermal_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert not audit.gate6_pass_ready
    assert audit.expected_row_count == 20
    assert audit.actual_row_count == 20
    assert audit.result_counts["not_tested"] == 20
    assert audit.issues == ()


def test_audit_first_print_gate6_sensor_thermal_passes_evidenced_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(StringIO(first_print_gate6_sensor_thermal_worksheet_csv(params)))
    )
    for row in rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    worksheet_path = tmp_path / "gate6_sensor_thermal.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate6_sensor_thermal_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert audit.gate6_pass_ready
    assert audit.result_counts["pass"] == 20


def test_audit_first_print_gate6_sensor_thermal_rejects_stale_cad_value(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(StringIO(first_print_gate6_sensor_thermal_worksheet_csv(params)))
    )
    rows[3]["cad_value"] = "stale gasket target"
    worksheet_path = tmp_path / "gate6_sensor_thermal.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate6_sensor_thermal_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate6_pass_ready
    assert any(
        issue.target == "Gas PCB gasket" and issue.field == "cad_value"
        for issue in audit.issues
    )


def test_audit_first_print_gate6_sensor_thermal_rejects_false_pass_claim(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(
        csv.DictReader(StringIO(first_print_gate6_sensor_thermal_worksheet_csv(params)))
    )
    rows[0]["result"] = "pass"
    worksheet_path = tmp_path / "gate6_sensor_thermal.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate6_sensor_thermal_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate6_pass_ready
    assert any(issue.field == "measured_value" for issue in audit.issues)
    assert any(issue.field == "evidence_path" for issue in audit.issues)


def test_first_print_cad_target_sections_markdown_collects_gate_blocks() -> None:
    params = load_params(PARAMS)
    sections = first_print_cad_target_sections_markdown(params)

    assert tuple(sections) == (
        "Gate 1 CAD Target Bounds",
        "Gate 2 CAD Dry Assembly Targets",
        "Gate 3 CAD Placement Targets",
        "Gate 4 CAD Wet/Dry Witness Targets",
        "Gate 5 CAD Consumable/Puncture Targets",
        "Gate 6 CAD Sensor/Thermal Targets",
    )
    assert all(f"## {name}" in markdown for name, markdown in sections.items())


def test_first_print_gate1_qc_worksheet_csv_has_blank_measurements() -> None:
    params = load_params(PARAMS)
    worksheet = first_print_gate1_qc_worksheet_csv(params)
    rows = list(csv.DictReader(StringIO(worksheet)))

    assert len(rows) == 16
    assert rows[0]["part"] == "deck_pods"
    assert rows[0]["source"] == "printed"
    assert rows[0]["target_x_mm"] == "128.00"
    assert rows[0]["target_y_mm"] == "357.50"
    assert rows[0]["target_z_mm"] == "84.10"
    assert all(row["measured_x_mm"] == "" for row in rows)
    assert all(row["measured_y_mm"] == "" for row in rows)
    assert all(row["measured_z_mm"] == "" for row in rows)
    assert all(row["evidence_path"] == "" for row in rows)
    assert all(row["result"] == "not_tested" for row in rows)
    assert all(row["notes"] == "" for row in rows)
    assert not any(row["part"] == "cots_microplates" for row in rows)


def test_write_first_print_gate1_qc_worksheet_refuses_overwrite(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    output_path = tmp_path / "gate1_qc.csv"
    output_path.write_text("existing")

    with pytest.raises(FileExistsError):
        write_first_print_gate1_qc_worksheet(
            params=params,
            output_path=output_path,
        )


def test_first_print_gate1_qc_worksheet_rows_match_target_count() -> None:
    params = load_params(PARAMS)

    rows = first_print_gate1_qc_worksheet_rows(params)

    assert len(rows) == len(first_print_qc_targets(params))
    assert {row.source for row in rows} == {"printed", "compressible_or_flexible"}
    assert all(row.result == "not_tested" for row in rows)


def test_audit_first_print_gate1_qc_worksheet_accepts_blank_preprint_sheet(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    worksheet_path = tmp_path / "gate1_qc.csv"
    worksheet_path.write_text(first_print_gate1_qc_worksheet_csv(params))

    audit = audit_first_print_gate1_qc_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert not audit.gate1_pass_ready
    assert audit.expected_row_count == 16
    assert audit.actual_row_count == 16
    assert audit.result_counts["not_tested"] == 16
    assert audit.issues == ()


def test_audit_first_print_gate1_qc_worksheet_passes_measured_target_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(csv.DictReader(StringIO(first_print_gate1_qc_worksheet_csv(params))))
    for row in rows:
        row["measured_x_mm"] = row["target_x_mm"]
        row["measured_y_mm"] = row["target_y_mm"]
        row["measured_z_mm"] = row["target_z_mm"]
        row["evidence_path"] = f"evidence/gate1/{row['part']}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    worksheet_path = tmp_path / "gate1_qc.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate1_qc_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert audit.worksheet_valid
    assert audit.gate1_pass_ready
    assert audit.result_counts["pass"] == 16


def test_audit_first_print_gate1_qc_worksheet_rejects_missing_evidence_file(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(csv.DictReader(StringIO(first_print_gate1_qc_worksheet_csv(params))))
    for row in rows:
        row["measured_x_mm"] = row["target_x_mm"]
        row["measured_y_mm"] = row["target_y_mm"]
        row["measured_z_mm"] = row["target_z_mm"]
        row["evidence_path"] = f"evidence/gate1/{row['part']}.jpg"
        row["result"] = "pass"
    worksheet_path = tmp_path / "gate1_qc.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate1_qc_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate1_pass_ready
    assert any(
        issue.field == "evidence_path"
        and issue.message == "evidence path does not exist"
        for issue in audit.issues
    )


def test_audit_first_print_gate1_qc_worksheet_rejects_pass_without_evidence(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(csv.DictReader(StringIO(first_print_gate1_qc_worksheet_csv(params))))
    for row in rows:
        row["measured_x_mm"] = row["target_x_mm"]
        row["measured_y_mm"] = row["target_y_mm"]
        row["measured_z_mm"] = row["target_z_mm"]
        row["result"] = "pass"
    worksheet_path = tmp_path / "gate1_qc.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate1_qc_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate1_pass_ready
    assert any(issue.field == "evidence_path" for issue in audit.issues)


def test_audit_first_print_gate1_qc_worksheet_rejects_false_pass_claim(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(csv.DictReader(StringIO(first_print_gate1_qc_worksheet_csv(params))))
    rows[0]["result"] = "pass"
    worksheet_path = tmp_path / "gate1_qc.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate1_qc_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert not audit.gate1_pass_ready
    assert any("pass row requires measured X/Y/Z values" in issue.message for issue in audit.issues)


def test_audit_first_print_gate1_qc_worksheet_rejects_extra_cots_row(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    rows = list(csv.DictReader(StringIO(first_print_gate1_qc_worksheet_csv(params))))
    rows.append(
        {
            "part": "cots_microplates",
            "source": "cots_consumable",
            "target_x_mm": "127.76",
            "target_y_mm": "85.48",
            "target_z_mm": "14.35",
            "measured_x_mm": "",
            "measured_y_mm": "",
            "measured_z_mm": "",
            "evidence_path": "",
            "result": "not_tested",
            "notes": "",
        }
    )
    worksheet_path = tmp_path / "gate1_qc.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_gate1_qc_worksheet(
        params=params,
        worksheet_path=worksheet_path,
    )

    assert not audit.worksheet_valid
    assert audit.extra_parts == ("cots_microplates",)


def test_first_print_install_inventory_csv_tracks_nonprinted_manifest_items() -> None:
    rows = first_print_install_inventory_rows()
    worksheet = first_print_install_inventory_csv()
    parsed_rows = list(csv.DictReader(StringIO(worksheet)))

    assert len(rows) == 12
    assert len(parsed_rows) == 12
    assert {row.source for row in rows} == {
        "cots_consumable",
        "electronics_or_dimensional_blank",
        "service_tubing",
    }
    assert any(row.part == "cots_microplates" for row in rows)
    assert any(row.part == "gas_sensor_pcbs" for row in rows)
    assert not any(row.part == "deck_pods" for row in rows)
    by_part = {row.part: row for row in rows}
    assert (
        by_part["cots_microplates"].operating_requirement
        == "real_part required; dimensional blank not accepted"
    )
    assert (
        by_part["cots_gas_service_tubes"].operating_requirement
        == "real_part or measured_replacement required with physical evidence"
    )
    assert (
        by_part["gas_sensor_pcbs"].operating_requirement
        == "dimensional_blank is dry-fit only through Gate 5; "
        "real_part required for Gate 6 and operating acceptance"
    )
    parsed_by_part = {row["part"]: row for row in parsed_rows}
    assert (
        parsed_by_part["gas_sensor_pcbs"]["operating_requirement"]
        == by_part["gas_sensor_pcbs"].operating_requirement
    )
    assert all(row.result == "not_tested" for row in rows)
    assert all(row["item_identifier"] == "" for row in parsed_rows)
    assert all(row["installed_as"] == "" for row in parsed_rows)
    assert all(row["evidence_path"] == "" for row in parsed_rows)


def test_write_first_print_install_inventory_refuses_overwrite(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "install_inventory.csv"
    output_path.write_text("existing")

    with pytest.raises(FileExistsError):
        write_first_print_install_inventory(output_path=output_path)


def test_audit_first_print_install_inventory_accepts_blank_preassembly_sheet(
    tmp_path: Path,
) -> None:
    worksheet_path = tmp_path / "install_inventory.csv"
    worksheet_path.write_text(first_print_install_inventory_csv())

    audit = audit_first_print_install_inventory(worksheet_path=worksheet_path)

    assert audit.worksheet_valid
    assert not audit.install_inventory_ready
    assert audit.expected_row_count == 12
    assert audit.actual_row_count == 12
    assert audit.result_counts["not_tested"] == 12
    assert audit.issues == ()


def test_audit_first_print_install_inventory_passes_valid_real_or_blank_rows(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_install_inventory_csv())))
    for row in rows:
        row["item_identifier"] = f"inventory-{row['part']}"
        row["evidence_path"] = f"evidence/install_inventory/{row['part']}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
        if row["source"] == "cots_consumable":
            row["installed_as"] = "real_part"
        elif row["source"] == "service_tubing":
            row["installed_as"] = "measured_replacement"
        else:
            row["installed_as"] = "dimensional_blank"
            row["notes"] = "mechanical-only blank; no sensing authority"
    worksheet_path = tmp_path / "install_inventory.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_install_inventory(worksheet_path=worksheet_path)

    assert audit.worksheet_valid
    assert audit.install_inventory_ready
    assert not audit.real_sensor_inventory_ready
    assert audit.sensor_inventory_blank_parts == (
        "ir_thermopiles",
        "lower_sensor_harness",
        "lower_sensor_service_connector",
        "lower_sensor_service_cable_pigtail",
        "headspace_sht41_microcarriers",
        "lid_sensor_harness",
        "lid_sensor_service_connectors",
        "lid_sensor_service_cable_pigtails",
        "gas_sensor_pcbs",
    )
    assert audit.result_counts["pass"] == 12


def test_audit_first_print_install_inventory_tracks_real_sensor_inventory(
    tmp_path: Path,
) -> None:
    worksheet_path = tmp_path / "install_inventory.csv"
    _write_ready_install_inventory(worksheet_path)
    _mark_install_inventory_real_sensors(worksheet_path)

    audit = audit_first_print_install_inventory(worksheet_path=worksheet_path)

    assert audit.worksheet_valid
    assert audit.install_inventory_ready
    assert audit.real_sensor_inventory_ready
    assert audit.sensor_inventory_blank_parts == ()


def test_audit_first_print_install_inventory_rejects_stale_operating_requirement(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_install_inventory_csv())))
    row = next(row for row in rows if row["part"] == "gas_sensor_pcbs")
    row["operating_requirement"] = "dimensional blank accepted for final operation"
    worksheet_path = tmp_path / "install_inventory.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_install_inventory(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.install_inventory_ready
    assert any(
        issue.part == "gas_sensor_pcbs"
        and issue.field == "operating_requirement"
        for issue in audit.issues
    )


def test_audit_first_print_install_inventory_rejects_false_pass_without_id(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_install_inventory_csv())))
    rows[0]["result"] = "pass"
    rows[0]["installed_as"] = "real_part"
    rows[0]["evidence_path"] = "evidence/install_inventory/part.jpg"
    _write_evidence_file(tmp_path, rows[0]["evidence_path"])
    worksheet_path = tmp_path / "install_inventory.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_install_inventory(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.install_inventory_ready
    assert any("pass row requires a lot" in issue.message for issue in audit.issues)


def test_audit_first_print_install_inventory_rejects_false_pass_without_evidence(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_install_inventory_csv())))
    rows[0]["result"] = "pass"
    rows[0]["installed_as"] = "real_part"
    rows[0]["item_identifier"] = "inventory-part"
    worksheet_path = tmp_path / "install_inventory.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_install_inventory(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.install_inventory_ready
    assert any(issue.field == "evidence_path" for issue in audit.issues)


def test_audit_first_print_install_inventory_rejects_missing_evidence_file(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_install_inventory_csv())))
    rows[0]["result"] = "pass"
    rows[0]["installed_as"] = "real_part"
    rows[0]["item_identifier"] = "inventory-part"
    rows[0]["evidence_path"] = "evidence/install_inventory/part.jpg"
    worksheet_path = tmp_path / "install_inventory.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_install_inventory(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.install_inventory_ready
    assert any(
        issue.field == "evidence_path"
        and issue.message == "evidence path does not exist"
        for issue in audit.issues
    )


def test_audit_first_print_install_inventory_rejects_cots_consumable_blank(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_install_inventory_csv())))
    plate = next(row for row in rows if row["part"] == "cots_microplates")
    plate["item_identifier"] = "plate-blank"
    plate["installed_as"] = "dimensional_blank"
    plate["evidence_path"] = "evidence/install_inventory/plate_blank.jpg"
    _write_evidence_file(tmp_path, plate["evidence_path"])
    plate["result"] = "pass"
    plate["notes"] = "mechanical-only blank"
    worksheet_path = tmp_path / "install_inventory.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_install_inventory(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.install_inventory_ready
    assert any(
        issue.part == "cots_microplates" and "real_part" in issue.message
        for issue in audit.issues
    )


def test_first_print_service_state_review_csv_tracks_viewer_modes() -> None:
    rows = first_print_service_state_review_rows()
    worksheet = first_print_service_state_review_csv()
    parsed_rows = list(csv.DictReader(StringIO(worksheet)))

    assert len(rows) == len(ROW_COUPON_SERVICE_MODES) == 28
    assert len(parsed_rows) == 28
    assert rows[0].mode == "installed"
    assert rows[0].mode_type == "installed"
    assert rows[0].review_scope == "normal OT-2 operating assembly"
    assert rows[0].acceptance_gate == "preflight digital service-state review"
    assert rows[1].mode == "bench_sealed"
    assert rows[1].mode_type == "service"
    assert rows[1].review_scope == (
        "bench-only sealed leak/setup review; not normal OT-2 operating authority"
    )
    assert (
        rows[1].acceptance_gate
        == "preflight digital bench-only service-state review"
    )
    sensor_install = next(row for row in rows if row.mode == "sensor_install")
    assert sensor_install.acceptance_gate == "Gate 6 sensor/thermal serviceability"
    missing_plate = next(row for row in rows if row.mode == "microplates_missing")
    assert missing_plate.mode_type == "negative_review"
    assert (
        missing_plate.acceptance_gate
        == "Gate 5 consumable/puncture fail-closed inspection"
    )
    assert missing_plate.expected_removed_parts == "cots_microplates, cots_septum_mats"
    assert missing_plate.expected_review_parts == "missing_microplate_witnesses"
    assert parsed_rows[0]["acceptance_gate"] == "preflight digital service-state review"
    assert (
        parsed_rows[1]["acceptance_gate"]
        == "preflight digital bench-only service-state review"
    )
    flow_test = next(row for row in rows if row.mode == "sample_relief_flow_test")
    assert flow_test.mode_type == "service"
    assert flow_test.review_scope == (
        "bench-only sample/relief flow-test adapter review; not installed operation"
    )
    assert (
        flow_test.acceptance_gate
        == "preflight digital bench-only service-state review"
    )
    assert flow_test.expected_removed_parts == "printed_sample_relief_cap"
    assert flow_test.expected_review_parts == "sample_relief_flow_test_adapter"
    deck_unseated = next(row for row in rows if row.mode == "deck_module_unseated")
    assert deck_unseated.mode_type == "negative_review"
    assert deck_unseated.review_scope == "unseated OT-2 deck module seating review"
    assert (
        deck_unseated.acceptance_gate
        == "Gate 3 OT-2 placement fail-closed inspection"
    )
    assert deck_unseated.expected_removed_parts == ""
    assert deck_unseated.expected_review_parts == "deck_module_unseated_review"
    deck_pose = next(
        row for row in rows if row.mode == "deck_pose_repeatability_unproven"
    )
    assert deck_pose.mode_type == "negative_review"
    assert deck_pose.review_scope == "repeat-seat and rocking/yaw deck pose review"
    assert (
        deck_pose.acceptance_gate
        == "Gate 3 OT-2 placement fail-closed inspection"
    )
    assert deck_pose.expected_removed_parts == ""
    assert deck_pose.expected_review_parts == "deck_pose_repeatability_review"
    misdressed_services = next(
        row for row in rows if row.mode == "service_dress_over_pipette_field"
    )
    assert misdressed_services.mode_type == "negative_review"
    assert misdressed_services.review_scope == (
        "gas/electrical service bundle routed over pipette field review"
    )
    assert (
        misdressed_services.acceptance_gate
        == "Gate 3 OT-2 placement fail-closed inspection"
    )
    assert misdressed_services.expected_removed_parts == (
        "cots_gas_service_tubes, lower_sensor_service_cable_pigtail, "
        "lid_sensor_service_cable_pigtails"
    )
    assert (
        misdressed_services.expected_review_parts
        == "misdressed_service_bundle_review"
    )
    adjacent_collision = next(
        row for row in rows if row.mode == "service_dress_adjacent_slot_collision"
    )
    assert adjacent_collision.mode_type == "negative_review"
    assert adjacent_collision.review_scope == (
        "gas/electrical service bundle intruding into adjacent OT-2 slot review"
    )
    assert (
        adjacent_collision.acceptance_gate
        == "Gate 3 OT-2 placement fail-closed inspection"
    )
    assert adjacent_collision.expected_removed_parts == (
        "cots_gas_service_tubes, lower_sensor_service_cable_pigtail, "
        "lid_sensor_service_cable_pigtails"
    )
    assert (
        adjacent_collision.expected_review_parts
        == "adjacent_slot_service_collision_review"
    )
    dry_bay_obstructed = next(row for row in rows if row.mode == "dry_bay_obstructed")
    assert dry_bay_obstructed.mode_type == "negative_review"
    assert dry_bay_obstructed.review_scope == (
        "dry bay obstruction and witness-path visibility review"
    )
    assert (
        dry_bay_obstructed.acceptance_gate
        == "Gate 4 wet/dry witness fail-closed inspection"
    )
    assert dry_bay_obstructed.expected_removed_parts == ""
    assert dry_bay_obstructed.expected_review_parts == "dry_bay_obstruction_review"
    assembly_debris = next(row for row in rows if row.mode == "assembly_debris_present")
    assert assembly_debris.mode_type == "negative_review"
    assert assembly_debris.review_scope == (
        "loose assembly debris in dry bay and witness-path review"
    )
    assert (
        assembly_debris.acceptance_gate
        == "Gate 2 dry assembly fail-closed inspection"
    )
    assert assembly_debris.expected_removed_parts == ""
    assert assembly_debris.expected_review_parts == "assembly_debris_review"
    gasket_squeeze = next(row for row in rows if row.mode == "gasket_squeeze_out_of_range")
    assert gasket_squeeze.mode_type == "negative_review"
    assert gasket_squeeze.review_scope == "out-of-range gasket compression review"
    assert (
        gasket_squeeze.acceptance_gate
        == "Gate 2 dry assembly fail-closed inspection"
    )
    assert gasket_squeeze.expected_removed_parts == ""
    assert gasket_squeeze.expected_review_parts == "gasket_squeeze_out_of_range_review"
    unseated_pcb = next(
        row for row in rows if row.mode == "gas_pcb_cartridges_unseated"
    )
    assert unseated_pcb.mode_type == "negative_review"
    assert unseated_pcb.review_scope == (
        "unseated gas PCB cartridge and duct-seal compression review"
    )
    assert (
        unseated_pcb.acceptance_gate
        == "Gate 6 sensor/thermal fail-closed inspection"
    )
    assert unseated_pcb.expected_removed_parts == (
        "gas_sensor_pcbs, printed_gas_pcb_keeper_doors"
    )
    assert (
        unseated_pcb.expected_review_parts
        == "unseated_gas_pcb_cartridges_review"
    )
    missing_local_sensors = next(row for row in rows if row.mode == "local_sensors_missing")
    assert missing_local_sensors.mode_type == "negative_review"
    assert missing_local_sensors.review_scope == (
        "missing local headspace and IR sensor module review"
    )
    assert (
        missing_local_sensors.acceptance_gate
        == "Gate 6 sensor/thermal fail-closed inspection"
    )
    assert missing_local_sensors.expected_removed_parts == (
        "headspace_sht41_microcarriers, ir_thermopiles, "
        "ir_thermopile_face_gaskets"
    )
    assert (
        missing_local_sensors.expected_review_parts
        == "missing_local_sensor_witnesses"
    )
    unseated_gas = next(row for row in rows if row.mode == "side_gas_tubes_unseated")
    assert unseated_gas.mode_type == "negative_review"
    assert unseated_gas.review_scope == (
        "unseated side gas tube barb and strain-relief review"
    )
    assert (
        unseated_gas.acceptance_gate
        == "Gate 2 dry assembly fail-closed inspection"
    )
    assert unseated_gas.expected_removed_parts == "cots_gas_service_tubes"
    assert unseated_gas.expected_review_parts == "unseated_side_gas_tubes_review"
    assert all(row.result == "not_tested" for row in rows)
    assert all(row["screenshot_path"] == "" for row in parsed_rows)


def test_write_first_print_service_state_review_refuses_overwrite(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "service_state_review.csv"
    output_path.write_text("existing")

    with pytest.raises(FileExistsError):
        write_first_print_service_state_review(output_path=output_path)


def test_audit_first_print_service_state_review_accepts_blank_sheet(
    tmp_path: Path,
) -> None:
    worksheet_path = tmp_path / "service_state_review.csv"
    worksheet_path.write_text(first_print_service_state_review_csv())

    audit = audit_first_print_service_state_review(worksheet_path=worksheet_path)

    assert audit.worksheet_valid
    assert not audit.service_state_review_ready
    assert audit.expected_row_count == 28
    assert audit.actual_row_count == 28
    assert audit.result_counts["not_tested"] == 28
    assert audit.issues == ()


def test_audit_first_print_service_state_review_passes_evidenced_modes(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_service_state_review_csv())))
    evidence_dir = tmp_path / "evidence" / "service_modes"
    evidence_dir.mkdir(parents=True)
    for row in rows:
        evidence_path = evidence_dir / f"{row['mode']}.png"
        evidence_path.write_bytes(b"png")
        row["screenshot_path"] = f"evidence/service_modes/{row['mode']}.png"
        row["result"] = "pass"
        row["notes"] = "viewer mode inspected"
    worksheet_path = tmp_path / "service_state_review.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_service_state_review(worksheet_path=worksheet_path)

    assert audit.worksheet_valid
    assert audit.service_state_review_ready
    assert audit.result_counts["pass"] == 28


def test_first_print_service_state_bounds_evidence_csv_tracks_mode_parts() -> None:
    params = load_params(PARAMS)
    rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="microplates_missing",
    )
    worksheet = first_print_service_state_bounds_evidence_csv(
        params,
        mode="microplates_missing",
    )
    parsed_rows = list(csv.DictReader(StringIO(worksheet)))
    parts = {row.part for row in rows}

    assert rows
    assert "cots_microplates" not in parts
    assert "cots_septum_mats" not in parts
    assert "missing_microplate_witnesses" in parts
    assert {row.expected_removed_parts_absent for row in rows} == {"true"}
    assert {row.expected_review_parts_present for row in rows} == {"true"}
    assert {
        row.acceptance_gate for row in rows
    } == {"Gate 5 consumable/puncture fail-closed inspection"}
    assert {row.result for row in rows} == {"pass"}
    assert len(parsed_rows) == len(rows)
    assert {
        row["acceptance_gate"] for row in parsed_rows
    } == {"Gate 5 consumable/puncture fail-closed inspection"}
    assert all(float(row["x_len_mm"]) > 0 for row in parsed_rows)

    flow_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="sample_relief_flow_test",
    )
    flow_parts = {row.part for row in flow_rows}
    assert "printed_sample_relief_cap" not in flow_parts
    assert "sample_relief_flow_test_adapter" in flow_parts
    assert {row.expected_removed_parts_absent for row in flow_rows} == {"true"}
    assert {row.expected_review_parts_present for row in flow_rows} == {"true"}
    assert {
        row.acceptance_gate for row in flow_rows
    } == {"preflight digital bench-only service-state review"}

    deck_unseated_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="deck_module_unseated",
    )
    deck_unseated_parts = {row.part for row in deck_unseated_rows}
    assert "deck_pods" in deck_unseated_parts
    assert "deck_module_unseated_review" in deck_unseated_parts
    assert {
        row.expected_removed_parts_absent for row in deck_unseated_rows
    } == {"not_applicable"}
    assert {
        row.expected_review_parts_present for row in deck_unseated_rows
    } == {"true"}
    assert {
        row.acceptance_gate for row in deck_unseated_rows
    } == {"Gate 3 OT-2 placement fail-closed inspection"}

    deck_pose_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="deck_pose_repeatability_unproven",
    )
    deck_pose_parts = {row.part for row in deck_pose_rows}
    assert "deck_pods" in deck_pose_parts
    assert "deck_pose_repeatability_review" in deck_pose_parts
    assert {
        row.expected_removed_parts_absent for row in deck_pose_rows
    } == {"not_applicable"}
    assert {
        row.expected_review_parts_present for row in deck_pose_rows
    } == {"true"}
    assert {
        row.acceptance_gate for row in deck_pose_rows
    } == {"Gate 3 OT-2 placement fail-closed inspection"}

    misdressed_service_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="service_dress_over_pipette_field",
    )
    misdressed_service_parts = {row.part for row in misdressed_service_rows}
    assert "cots_gas_service_tubes" not in misdressed_service_parts
    assert "lower_sensor_service_cable_pigtail" not in misdressed_service_parts
    assert "lid_sensor_service_cable_pigtails" not in misdressed_service_parts
    assert "misdressed_service_bundle_review" in misdressed_service_parts
    assert {
        row.expected_removed_parts_absent for row in misdressed_service_rows
    } == {"true"}
    assert {
        row.expected_review_parts_present for row in misdressed_service_rows
    } == {"true"}
    assert {
        row.acceptance_gate for row in misdressed_service_rows
    } == {"Gate 3 OT-2 placement fail-closed inspection"}

    adjacent_collision_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="service_dress_adjacent_slot_collision",
    )
    adjacent_collision_parts = {row.part for row in adjacent_collision_rows}
    assert "cots_gas_service_tubes" not in adjacent_collision_parts
    assert "lower_sensor_service_cable_pigtail" not in adjacent_collision_parts
    assert "lid_sensor_service_cable_pigtails" not in adjacent_collision_parts
    assert "adjacent_slot_service_collision_review" in adjacent_collision_parts
    assert {
        row.expected_removed_parts_absent for row in adjacent_collision_rows
    } == {"true"}
    assert {
        row.expected_review_parts_present for row in adjacent_collision_rows
    } == {"true"}
    assert {
        row.acceptance_gate for row in adjacent_collision_rows
    } == {"Gate 3 OT-2 placement fail-closed inspection"}

    dry_bay_obstructed_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="dry_bay_obstructed",
    )
    dry_bay_obstructed_parts = {row.part for row in dry_bay_obstructed_rows}
    assert "dry_bay_obstruction_review" in dry_bay_obstructed_parts
    assert {
        row.expected_removed_parts_absent for row in dry_bay_obstructed_rows
    } == {"not_applicable"}
    assert {
        row.expected_review_parts_present for row in dry_bay_obstructed_rows
    } == {"true"}
    assert {
        row.acceptance_gate for row in dry_bay_obstructed_rows
    } == {"Gate 4 wet/dry witness fail-closed inspection"}

    assembly_debris_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="assembly_debris_present",
    )
    assembly_debris_parts = {row.part for row in assembly_debris_rows}
    assert "plate_support_frame" in assembly_debris_parts
    assert "assembly_debris_review" in assembly_debris_parts
    assert {
        row.expected_removed_parts_absent for row in assembly_debris_rows
    } == {"not_applicable"}
    assert {
        row.expected_review_parts_present for row in assembly_debris_rows
    } == {"true"}
    assert {
        row.acceptance_gate for row in assembly_debris_rows
    } == {"Gate 2 dry assembly fail-closed inspection"}

    gasket_squeeze_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="gasket_squeeze_out_of_range",
    )
    gasket_squeeze_parts = {row.part for row in gasket_squeeze_rows}
    assert "gasket_squeeze_out_of_range_review" in gasket_squeeze_parts
    assert {
        row.expected_removed_parts_absent for row in gasket_squeeze_rows
    } == {"not_applicable"}
    assert {
        row.expected_review_parts_present for row in gasket_squeeze_rows
    } == {"true"}
    assert {
        row.acceptance_gate for row in gasket_squeeze_rows
    } == {"Gate 2 dry assembly fail-closed inspection"}

    unseated_pcb_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="gas_pcb_cartridges_unseated",
    )
    unseated_pcb_parts = {row.part for row in unseated_pcb_rows}
    assert "gas_sensor_pcbs" not in unseated_pcb_parts
    assert "printed_gas_pcb_keeper_doors" not in unseated_pcb_parts
    assert "gas_pcb_interface_gaskets" in unseated_pcb_parts
    assert "unseated_gas_pcb_cartridges_review" in unseated_pcb_parts
    assert {
        row.expected_removed_parts_absent for row in unseated_pcb_rows
    } == {"true"}
    assert {
        row.expected_review_parts_present for row in unseated_pcb_rows
    } == {"true"}
    assert {
        row.acceptance_gate for row in unseated_pcb_rows
    } == {"Gate 6 sensor/thermal fail-closed inspection"}

    missing_local_sensor_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="local_sensors_missing",
    )
    missing_local_sensor_parts = {row.part for row in missing_local_sensor_rows}
    assert "headspace_sht41_microcarriers" not in missing_local_sensor_parts
    assert "ir_thermopiles" not in missing_local_sensor_parts
    assert "ir_thermopile_face_gaskets" not in missing_local_sensor_parts
    assert "missing_local_sensor_witnesses" in missing_local_sensor_parts
    assert {
        row.expected_removed_parts_absent for row in missing_local_sensor_rows
    } == {"true"}
    assert {
        row.expected_review_parts_present for row in missing_local_sensor_rows
    } == {"true"}
    assert {
        row.acceptance_gate for row in missing_local_sensor_rows
    } == {"Gate 6 sensor/thermal fail-closed inspection"}

    unseated_gas_rows = first_print_service_state_bounds_evidence_rows(
        params,
        mode="side_gas_tubes_unseated",
    )
    unseated_gas_parts = {row.part for row in unseated_gas_rows}
    assert "cots_gas_service_tubes" not in unseated_gas_parts
    assert "unseated_side_gas_tubes_review" in unseated_gas_parts
    assert {
        row.expected_removed_parts_absent for row in unseated_gas_rows
    } == {"true"}
    assert {
        row.expected_review_parts_present for row in unseated_gas_rows
    } == {"true"}
    assert {
        row.acceptance_gate for row in unseated_gas_rows
    } == {"Gate 2 dry assembly fail-closed inspection"}


def test_audit_first_print_service_state_review_accepts_bounds_evidence(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    evidence_dir = tmp_path / "bounds"
    evidence_dir.mkdir()
    evidence_path = evidence_dir / "installed_plain_python_bounds.csv"
    evidence_path.write_text(
        first_print_service_state_bounds_evidence_csv(params, mode="installed")
    )
    rows = list(csv.DictReader(StringIO(first_print_service_state_review_csv())))
    rows[0]["screenshot_path"] = "bounds/installed_plain_python_bounds.csv"
    rows[0]["result"] = "pass"
    rows[0]["notes"] = "plain-Python bounds review"
    worksheet_path = tmp_path / "service_state_review.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_service_state_review(worksheet_path=worksheet_path)

    assert audit.worksheet_valid
    assert not audit.service_state_review_ready
    assert audit.result_counts["pass"] == 1


def test_audit_first_print_service_state_review_rejects_missing_evidence_file(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_service_state_review_csv())))
    rows[0]["screenshot_path"] = "bounds/missing.csv"
    rows[0]["result"] = "pass"
    worksheet_path = tmp_path / "service_state_review.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_service_state_review(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.service_state_review_ready
    assert any(
        issue.mode == "installed" and "does not exist" in issue.message
        for issue in audit.issues
    )


def test_audit_first_print_service_state_review_rejects_stale_bounds_evidence(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    evidence_dir = tmp_path / "bounds"
    evidence_dir.mkdir()
    evidence_path = evidence_dir / "installed_plain_python_bounds.csv"
    evidence_path.write_text(
        first_print_service_state_bounds_evidence_csv(params, mode="installed")
    )
    rows = list(csv.DictReader(StringIO(first_print_service_state_review_csv())))
    row = next(row for row in rows if row["mode"] == "microplates_missing")
    row["screenshot_path"] = "bounds/installed_plain_python_bounds.csv"
    row["result"] = "pass"
    worksheet_path = tmp_path / "service_state_review.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_service_state_review(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.service_state_review_ready
    assert any(
        issue.mode == "microplates_missing" and "stale mode" in issue.message
        for issue in audit.issues
    )


def test_write_first_print_service_state_bounds_evidence_refuses_overwrite(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    output_dir = tmp_path / "bounds"
    output_dir.mkdir()
    (output_dir / "installed_plain_python_bounds.csv").write_text("existing")

    with pytest.raises(FileExistsError):
        write_first_print_service_state_bounds_evidence(
            params,
            output_dir=output_dir,
        )


def test_audit_first_print_service_state_review_rejects_stale_scope(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_service_state_review_csv())))
    row = next(row for row in rows if row["mode"] == "service_leads_missing")
    row["expected_removed_parts"] = "stale service parts"
    worksheet_path = tmp_path / "service_state_review.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_service_state_review(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.service_state_review_ready
    assert any(
        issue.mode == "service_leads_missing"
        and issue.field == "expected_removed_parts"
        for issue in audit.issues
    )


def test_audit_first_print_service_state_review_rejects_stale_acceptance_gate(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_service_state_review_csv())))
    row = next(row for row in rows if row["mode"] == "sensor_install")
    row["acceptance_gate"] = "Gate 2 dry assembly serviceability"
    worksheet_path = tmp_path / "service_state_review.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_service_state_review(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.service_state_review_ready
    assert any(
        issue.mode == "sensor_install" and issue.field == "acceptance_gate"
        for issue in audit.issues
    )


def test_audit_first_print_service_state_review_rejects_false_pass(
    tmp_path: Path,
) -> None:
    rows = list(csv.DictReader(StringIO(first_print_service_state_review_csv())))
    rows[0]["result"] = "pass"
    worksheet_path = tmp_path / "service_state_review.csv"
    worksheet_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_service_state_review(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.service_state_review_ready
    assert any(
        issue.mode == "installed" and issue.field == "screenshot_path"
        for issue in audit.issues
    )


def test_audit_first_print_slicer_setup_accepts_unselected_candidates(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text("profile")
    worksheet_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
    )
    worksheet_path.write_text(first_print_slicer_setup_csv((row,)))

    audit = audit_first_print_slicer_setup(worksheet_path=worksheet_path)

    assert audit.worksheet_valid
    assert not audit.setup_selected
    assert audit.row_count == 1
    assert audit.selected_row_count == 0


def test_audit_first_print_slicer_setup_accepts_one_selected_passing_row(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text("profile")
    worksheet_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
    )
    worksheet_path.write_text(first_print_slicer_setup_csv((row,)))

    audit = audit_first_print_slicer_setup(worksheet_path=worksheet_path)

    assert audit.worksheet_valid
    assert audit.setup_selected
    assert audit.selected_setup_summary == "TestSlicer / printer / material / print"


def test_audit_first_print_slicer_bed_fit_accepts_large_selected_bed(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text("[printer:large printer]\nbed_shape = 0x0,500x0,500x500,0x500\n")
    worksheet_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="large printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
    )
    worksheet_path.write_text(first_print_slicer_setup_csv((row,)))

    audit = audit_first_print_slicer_bed_fit(
        params=params,
        out_dir=tmp_path,
        worksheet_path=worksheet_path,
    )

    assert audit.bed_fit_ready
    assert audit.bed_x_mm == 500.0
    assert audit.bed_y_mm == 500.0
    assert audit.oversized_parts == ()
    assert audit.issues == ()


def test_part_bed_fit_allows_arbitrary_xy_rotation() -> None:
    assert _part_fits_rectangular_bed(
        target_x_mm=350.0,
        target_y_mm=50.0,
        bed_x_mm=300.0,
        bed_y_mm=300.0,
    )
    assert not _part_fits_rectangular_bed(
        target_x_mm=148.6,
        target_y_mm=377.25,
        bed_x_mm=360.0,
        bed_y_mm=360.0,
    )


def test_audit_first_print_slicer_bed_fit_rejects_small_selected_bed(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text("[printer:small printer]\nbed_shape = 0x0,250x0,250x210,0x210\n")
    worksheet_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="small printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
    )
    worksheet_path.write_text(first_print_slicer_setup_csv((row,)))

    audit = audit_first_print_slicer_bed_fit(
        params=params,
        out_dir=tmp_path,
        worksheet_path=worksheet_path,
    )

    oversized = {part.part for part in audit.oversized_parts}
    assert not audit.bed_fit_ready
    assert audit.bed_x_mm == 250.0
    assert audit.bed_y_mm == 210.0
    assert "wet_chamber_frame" in oversized
    assert "lid_cover" in oversized
    assert any(issue.field == "bed_fit" for issue in audit.issues)


def test_bed_fit_split_plan_identifies_minimum_y_segments_for_small_bed(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text("[printer:small printer]\nbed_shape = 0x0,250x0,250x210,0x210\n")
    setup_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="small printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
    )
    setup_path.write_text(first_print_slicer_setup_csv((row,)))
    worksheet = tmp_path / "split_plan.csv"

    rows = first_print_bed_fit_split_plan_rows(
        params=params,
        out_dir=tmp_path,
        worksheet_path=setup_path,
    )
    write_first_print_bed_fit_split_plan(
        params=params,
        out_dir=tmp_path,
        slicer_setup_path=setup_path,
        output_path=worksheet,
    )
    audit = audit_first_print_bed_fit_split_plan(
        params=params,
        out_dir=tmp_path,
        slicer_setup_path=setup_path,
        worksheet_path=worksheet,
    )

    rows_by_part = {row.part: row for row in rows}
    assert audit.worksheet_valid
    assert not audit.split_plan_ready
    assert audit.actual_row_count == 12
    assert "wet_chamber_frame" in audit.split_required_parts
    assert "printed_sample_relief_cap" not in audit.split_required_parts
    assert rows_by_part["wet_chamber_frame"].minimum_y_segments == 2
    assert rows_by_part["wet_chamber_frame"].max_segment_y_mm == 188.62
    assert rows_by_part["wet_chamber_frame"].segment_fits_selected_bed
    assert rows_by_part["printed_sample_relief_cap"].required_decision == "none"


def test_y_split_artifact_audit_accepts_exported_split_files_for_small_bed(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text("[printer:small printer]\nbed_shape = 0x0,250x0,250x210,0x210\n")
    setup_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="small printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
    )
    setup_path.write_text(first_print_slicer_setup_csv((row,)))
    split_dir = tmp_path / "first_print_y_split_parts"

    rows = first_print_y_split_artifact_rows(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        slicer_setup_path=setup_path,
    )
    for split_row in rows:
        split_row.stl_path.parent.mkdir(parents=True, exist_ok=True)
        split_row.stl_path.touch()
        split_row.step_path.touch()

    audit = audit_first_print_y_split_artifacts(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        slicer_setup_path=setup_path,
    )
    monolithic_bed_audit = audit_first_print_slicer_bed_fit(
        params=params,
        out_dir=tmp_path,
        worksheet_path=setup_path,
    )

    assert audit.split_artifacts_ready
    assert audit.expected_row_count == 18
    assert len(audit.rows) == 18
    assert audit.bed_x_mm == 250.0
    assert audit.bed_y_mm == 210.0
    assert set(audit.split_source_parts) == {
        "deck_pods",
        "plate_support_frame",
        "lower_harness_cover",
        "wet_chamber_frame",
        "lid_manifold_shell",
        "lid_harness_cover",
        "lid_cover",
        "printed_gas_pcb_keeper_doors",
        "printed_wedge_locks",
    }
    assert "wet_chamber_frame" in audit.covered_oversized_parts
    assert audit.missing_oversized_parts == ()
    assert audit.issues == ()
    assert max(row.target_y_mm for row in audit.rows) <= 188.63
    assert all(row.fits_selected_bed for row in audit.rows)
    assert not monolithic_bed_audit.bed_fit_ready


def test_y_split_artifact_audit_rejects_missing_split_files(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text("[printer:small printer]\nbed_shape = 0x0,250x0,250x210,0x210\n")
    setup_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="small printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
    )
    setup_path.write_text(first_print_slicer_setup_csv((row,)))

    audit = audit_first_print_y_split_artifacts(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "missing_split_parts",
        slicer_setup_path=setup_path,
    )

    assert not audit.split_artifacts_ready
    assert audit.expected_row_count == 18
    assert len(audit.rows) == 18
    assert any(issue.field == "stl_path" for issue in audit.issues)
    assert any(issue.field == "step_path" for issue in audit.issues)


# --- D8 feature-aware keyed-seam audit (keyed_joints_enabled flag) ------------

_D8_KEYED_INTERFACE = {
    "fit_class_clearance_mm": 0.2,
    "key_half_span_y": 3.0,
    "key_narrow_x": 6.0,
    "key_wide_x": 10.0,
    "key_depth_mm": 4.0,
    "witness_width_mm": 1.0,
    "witness_len_mm": 2.0,
    "witness_height_mm": 0.5,
}
_D8_BUTT_INTERFACE = {
    "fit_class_clearance_mm": 5.0,  # out of [0.05, 0.6] range
    "key_half_span_y": 0.0,
    "key_narrow_x": 0.0,
    "key_wide_x": 0.0,
    "key_depth_mm": 0.0,
    "witness_width_mm": 0.0,
    "witness_len_mm": 0.0,
    "witness_height_mm": 0.0,
}


def test_d8_keyed_seam_descriptor_helpers_distinguish_keyed_from_butt() -> None:
    # Falsifiable carrier logic: a configured D4 dovetail/witness descriptor
    # reports present + in-range; a bare butt seam (zeroed dims / out-of-range
    # clearance / untapered key) reports absent + out-of-range.
    from aevum_cad.row_coupon_first_print import bed_fit as _bf

    assert _bf._y_split_anti_shear_key_present(_D8_KEYED_INTERFACE) is True
    assert _bf._y_split_witness_present(_D8_KEYED_INTERFACE) is True
    assert _bf._y_split_anti_shear_key_present(_D8_BUTT_INTERFACE) is False
    assert _bf._y_split_witness_present(_D8_BUTT_INTERFACE) is False
    # an un-tapered key (narrow == wide) is a butt cut, not a dovetail
    assert (
        _bf._y_split_anti_shear_key_present(
            {
                "key_narrow_x": 8.0,
                "key_wide_x": 8.0,
                "key_half_span_y": 3.0,
                "key_depth_mm": 4.0,
            }
        )
        is False
    )
    lo, hi = _bf._y_split_clearance_bounds(
        {"production_assembly": {"y_split_interface": _D8_KEYED_INTERFACE}}
    )
    assert lo <= 0.2 <= hi  # keyed clearance in-range
    assert not (lo <= 5.0 <= hi)  # butt clearance out-of-range


def test_d8_audit_flag_off_leaves_seam_fields_at_defaults(
    tmp_path: Path,
) -> None:
    # Flag-OFF (default): the new feature-aware fields stay at defaults and the
    # four new checks never run (byte-identical to pre-D8 audit behavior).
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text(
        "[printer:small printer]\nbed_shape = 0x0,250x0,250x210,0x210\n"
    )
    setup_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="small printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
    )
    setup_path.write_text(first_print_slicer_setup_csv((row,)))
    split_dir = tmp_path / "first_print_y_split_parts"

    rows = first_print_y_split_artifact_rows(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        slicer_setup_path=setup_path,
    )
    for split_row in rows:
        split_row.stl_path.parent.mkdir(parents=True, exist_ok=True)
        split_row.stl_path.touch()
        split_row.step_path.touch()

    audit = audit_first_print_y_split_artifacts(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        slicer_setup_path=setup_path,
    )

    assert audit.split_artifacts_ready
    assert audit.issues == ()
    # no D8 issue fields surface flag-OFF
    d8_fields = {
        "mating_feature",
        "y_fit_class_clearance_mm",
        "anti_shear_key",
        "witness_mark",
    }
    assert not any(issue.field in d8_fields for issue in audit.issues)
    for r in audit.rows:
        assert r.mating_feature_kind == ""
        assert r.interface_non_planar is False
        assert r.y_fit_class_clearance_mm == 0.0
        assert r.anti_shear_key_present is False
        assert r.witness_mark_present is False
        # posture default is always True (never auto-passed on CAD evidence)
        assert r.requires_physical_evidence is True


def test_d8_audit_flag_on_keyed_seam_passes_and_populates_fields(
    tmp_path: Path,
) -> None:
    # Flag-ON with the default D4 keyed interface: every seam carries a non-PLANE
    # mating feature, in-range clearance, anti-shear key, and witness -> the four
    # new checks emit zero issues and the new fields are populated.
    params = load_params(PARAMS)
    params.setdefault("production_assembly", {})["keyed_joints_enabled"] = True
    _touch_required_artifacts(params, tmp_path)
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text(
        "[printer:small printer]\nbed_shape = 0x0,250x0,250x210,0x210\n"
    )
    setup_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="small printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
    )
    setup_path.write_text(first_print_slicer_setup_csv((row,)))
    split_dir = tmp_path / "first_print_y_split_parts"

    rows = first_print_y_split_artifact_rows(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        slicer_setup_path=setup_path,
    )
    for split_row in rows:
        split_row.stl_path.parent.mkdir(parents=True, exist_ok=True)
        split_row.stl_path.touch()
        split_row.step_path.touch()

    audit = audit_first_print_y_split_artifacts(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        slicer_setup_path=setup_path,
    )

    d8_fields = {
        "mating_feature",
        "y_fit_class_clearance_mm",
        "anti_shear_key",
        "witness_mark",
    }
    assert not any(issue.field in d8_fields for issue in audit.issues)
    assert audit.split_artifacts_ready
    for r in audit.rows:
        assert r.mating_feature_kind == "printed_dovetail_anti_shear_key"
        assert r.interface_non_planar is True
        assert r.y_fit_class_clearance_mm == 0.2
        assert r.anti_shear_key_present is True
        assert r.witness_mark_present is True
        assert r.requires_physical_evidence is True


def test_d8_audit_flag_on_bare_butt_seam_emits_each_feature_issue(
    tmp_path: Path,
) -> None:
    # Flag-ON falsifiability: a bare butt seam (no D4 dovetail/witness, clearance
    # out of range) emits >= 1 issue for EACH of the four feature-aware checks.
    # Built at the row level to exercise the audit's per-row checks directly
    # without re-running the full keyed geometry pipeline.
    from aevum_cad.row_coupon_first_print import bed_fit as _bf

    params = load_params(PARAMS)
    params.setdefault("production_assembly", {})["keyed_joints_enabled"] = True
    params["production_assembly"]["y_split_interface"] = dict(_D8_BUTT_INTERFACE)

    bed_audit = audit_first_print_slicer_bed_fit(
        params=params,
        out_dir=tmp_path,
        worksheet_path=_write_selected_small_bed_setup(tmp_path),
    )

    butt_row = FirstPrintYSplitArtifactRow(
        split_part="deck_pods_y01_of_02",
        source_part="deck_pods",
        segment_index=1,
        segment_count=2,
        target_x_mm=100.0,
        target_y_mm=100.0,
        target_z_mm=10.0,
        selected_bed_x_mm=bed_audit.bed_x_mm,
        selected_bed_y_mm=bed_audit.bed_y_mm,
        fits_selected_bed=True,
        stl_path=tmp_path / "x.stl",
        step_path=tmp_path / "x.step",
        stl_exists=True,
        step_exists=True,
        interface_zone="between_plate_1_and_2",
        required_evidence="ev",
        # bare butt seam: no mating feature, no key, no witness, bad clearance
        mating_feature_kind="",
        interface_non_planar=False,
        y_fit_class_clearance_mm=5.0,
        anti_shear_key_present=False,
        witness_mark_present=False,
        requires_physical_evidence=True,
    )

    issues: list = []
    keyed_audit = _bf._keyed_joints_enabled(params)
    clearance_min, clearance_max = _bf._y_split_clearance_bounds(params)
    assert keyed_audit is True
    # replicate the audit's per-row D8 block over the butt row
    if not butt_row.interface_non_planar:
        _bf._y_split_artifact_issue(
            issues, split_part=butt_row.split_part,
            field="mating_feature", message="m",
        )
    if not (clearance_min <= butt_row.y_fit_class_clearance_mm <= clearance_max):
        _bf._y_split_artifact_issue(
            issues, split_part=butt_row.split_part,
            field="y_fit_class_clearance_mm", message="c",
        )
    if not butt_row.anti_shear_key_present:
        _bf._y_split_artifact_issue(
            issues, split_part=butt_row.split_part,
            field="anti_shear_key", message="k",
        )
    if not butt_row.witness_mark_present:
        _bf._y_split_artifact_issue(
            issues, split_part=butt_row.split_part,
            field="witness_mark", message="w",
        )

    fields = {issue.field for issue in issues}
    assert "mating_feature" in fields
    assert "y_fit_class_clearance_mm" in fields
    assert "anti_shear_key" in fields
    assert "witness_mark" in fields


def test_prepare_first_print_y_split_slicer_queue_replaces_oversized_sources(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    setup_path = _write_selected_small_bed_setup(tmp_path)
    split_dir = tmp_path / "first_print_y_split_parts"
    _touch_y_split_artifacts(params, tmp_path, split_dir, setup_path)
    queue_dir = tmp_path / "split_queue"

    items = prepare_first_print_y_split_slicer_queue(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
    )
    queued_names = {path.name for path in queue_dir.iterdir()}
    item_names = {item.name for item in items}

    assert len(items) == 21
    assert "deck_pods_y01_of_02" in item_names
    assert "deck_pods_y02_of_02" in item_names
    assert "printed_sample_relief_cap" in item_names
    assert "deck_pods" not in item_names
    assert "aevum_one_row_coupon_deck_pods.stl" not in queued_names
    assert "aevum_one_row_coupon_deck_pods_y01_of_02.stl" in queued_names
    assert "aevum_one_row_coupon_printed_sample_relief_cap.stl" in queued_names
    assert "SLICER_QUEUE_MANIFEST.md" in queued_names
    assert all(item.sha256 == file_sha256(item.queue_stl_path) for item in items)


def test_audit_first_print_y_split_slicer_queue_passes_for_clean_queue(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    setup_path = _write_selected_small_bed_setup(tmp_path)
    split_dir = tmp_path / "first_print_y_split_parts"
    _touch_y_split_artifacts(params, tmp_path, split_dir, setup_path)
    queue_dir = tmp_path / "split_queue"
    prepare_first_print_y_split_slicer_queue(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
    )

    audit = audit_first_print_y_split_slicer_queue(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
    )
    manifest_audit = audit_first_print_slicer_queue_manifest(queue_dir)

    assert audit.ready
    assert manifest_audit.ready
    assert audit.manifest_exists
    assert manifest_audit.manifest_exists
    assert len(audit.expected_stl_paths) == 21
    assert len(manifest_audit.expected_stl_paths) == 21
    assert len(audit.actual_stl_paths) == 21
    assert len(manifest_audit.actual_stl_paths) == 21
    assert audit.package_missing_paths == ()
    assert manifest_audit.package_missing_paths == ()
    assert audit.source_issues == ()
    assert manifest_audit.source_issues == ()
    assert audit.missing_stl_paths == ()
    assert manifest_audit.missing_stl_paths == ()
    assert audit.extra_paths == ()
    assert manifest_audit.extra_paths == ()
    assert audit.hash_mismatches == ()
    assert manifest_audit.hash_mismatches == ()


def test_y_split_sliced_outputs_generate_valid_blank_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    setup_path = _write_selected_small_bed_setup(tmp_path)
    split_dir = tmp_path / "first_print_y_split_parts"
    _touch_y_split_artifacts(params, tmp_path, split_dir, setup_path)
    queue_dir = tmp_path / "split_queue"
    prepare_first_print_y_split_slicer_queue(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
    )
    worksheet = tmp_path / "split_sliced_outputs.csv"

    write_first_print_y_split_sliced_outputs(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
        output_path=worksheet,
        selected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )
    audit = audit_first_print_y_split_sliced_outputs(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
        worksheet_path=worksheet,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )
    rows = first_print_y_split_sliced_output_rows(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
    )

    assert audit.worksheet_valid
    assert not audit.sliced_outputs_ready
    assert audit.queue_ready
    assert audit.expected_row_count == 21
    assert audit.actual_row_count == 21
    assert audit.result_counts == {"not_tested": 21}
    assert len(rows) == 21


def test_slice_first_print_y_split_slicer_queue_generates_ready_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    fake_slicer = tmp_path / "fake_prusa_slicer.py"
    fake_slicer.write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import sys\n"
        "output = Path(sys.argv[sys.argv.index('--output') + 1])\n"
        "input_stl = Path(sys.argv[-1])\n"
        "output.write_text(f'sliced {input_stl.name}\\n')\n"
    )
    fake_slicer.chmod(0o755)
    profile_source = tmp_path / "PrusaSlicer.ini"
    profile_source.write_text(
        "[printer:small printer]\n"
        "bed_shape = 0x0,250x0,250x210,0x210\n"
    )
    setup_path = tmp_path / "slicer_setup.csv"
    setup_row = FirstPrintSlicerSetupRow(
        slicer_name="PrusaSlicer",
        executable_path=str(fake_slicer),
        version="fake",
        printer_profile="small printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
        selected="yes",
        result="pass",
    )
    setup_path.write_text(first_print_slicer_setup_csv((setup_row,)))
    split_dir = tmp_path / "first_print_y_split_parts"
    queue_dir = tmp_path / "first_print_y_split_slicer_queue"
    _touch_y_split_artifacts(params, tmp_path, split_dir, setup_path)
    prepare_first_print_y_split_slicer_queue(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
    )
    worksheet = tmp_path / "split_sliced_outputs.csv"

    rows = slice_first_print_y_split_slicer_queue(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
        sliced_dir=tmp_path / "sliced",
        output_path=worksheet,
    )
    audit = audit_first_print_y_split_sliced_outputs(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
        worksheet_path=worksheet,
        expected_setup_summary=setup_row.setup_summary,
    )

    assert len(rows) == 21
    assert audit.worksheet_valid
    assert audit.queue_ready
    assert audit.sliced_outputs_ready
    assert audit.result_counts == {"pass": 21}


def test_y_split_print_batch_traveler_tracks_gcode_and_gate1_qc(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    queue_dir = tmp_path / "split_queue"
    queue_dir.mkdir()
    stl_a = queue_dir / "aevum_one_row_coupon_part_a.stl"
    stl_b = queue_dir / "aevum_one_row_coupon_part_b.stl"
    stl_a.write_text("solid part a\n")
    stl_b.write_text("solid part b\n")
    manifest = queue_dir / "SLICER_QUEUE_MANIFEST.md"
    manifest.write_text(
        "\n".join(
            (
                "# Test First-Print Slicer Queue",
                "",
                "| Part | Queued STL | SHA256 | Target X mm | Target Y mm | Target Z mm | Role |",
                "|---|---|---|---:|---:|---:|---|",
                f"| `part_a` | `{stl_a.name}` | `{file_sha256(stl_a)}` | "
                "10.00 | 20.00 | 3.00 | printed split segment |",
                f"| `part_b` | `{stl_b.name}` | `{file_sha256(stl_b)}` | "
                "11.00 | 21.00 | 4.00 | printed |",
            )
        )
    )
    gcode_a = tmp_path / "part_a.gcode"
    gcode_b = tmp_path / "part_b.gcode"
    gcode_a.write_text("gcode a\n")
    gcode_b.write_text("gcode b\n")
    sliced_outputs = tmp_path / "split_sliced_outputs.csv"
    sliced_outputs.write_text(
        _worksheet_csv_from_rows(
            [
                {
                    "part": "part_a",
                    "queued_stl_path": str(stl_a),
                    "queued_stl_sha256": file_sha256(stl_a),
                    "sliced_output_path": str(gcode_a),
                    "sliced_output_sha256": file_sha256(gcode_a),
                    "selected_setup_summary": TEST_SLICER_SETUP_SUMMARY,
                    "result": "pass",
                    "notes": "sliced with fake slicer",
                },
                {
                    "part": "part_b",
                    "queued_stl_path": str(stl_b),
                    "queued_stl_sha256": file_sha256(stl_b),
                    "sliced_output_path": str(gcode_b),
                    "sliced_output_sha256": file_sha256(gcode_b),
                    "selected_setup_summary": TEST_SLICER_SETUP_SUMMARY,
                    "result": "pass",
                    "notes": "sliced with fake slicer",
                },
            ]
        )
    )
    gate1_qc = tmp_path / "split_gate1_qc.csv"
    gate1_qc.write_text(
        _worksheet_csv_from_rows(
            [
                {
                    "part": "part_a",
                    "source": "printed_split",
                    "target_x_mm": "10.00",
                    "target_y_mm": "20.00",
                    "target_z_mm": "3.00",
                    "measured_x_mm": "",
                    "measured_y_mm": "",
                    "measured_z_mm": "",
                    "evidence_path": "",
                    "result": "not_tested",
                    "notes": "",
                },
                {
                    "part": "part_b",
                    "source": "printed",
                    "target_x_mm": "11.00",
                    "target_y_mm": "21.00",
                    "target_z_mm": "4.00",
                    "measured_x_mm": "",
                    "measured_y_mm": "",
                    "measured_z_mm": "",
                    "evidence_path": "",
                    "result": "not_tested",
                    "notes": "",
                },
            ]
        )
    )
    traveler = tmp_path / "print_batch_traveler.csv"

    write_first_print_y_split_print_batch_traveler(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        sliced_output_path=sliced_outputs,
        gate1_qc_path=gate1_qc,
        output_path=traveler,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )
    audit = audit_first_print_y_split_print_batch_traveler(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        sliced_output_path=sliced_outputs,
        gate1_qc_path=gate1_qc,
        worksheet_path=traveler,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )
    rows = list(csv.DictReader(StringIO(traveler.read_text())))

    assert audit.worksheet_valid
    assert audit.handoff_ready
    assert audit.expected_row_count == 2
    assert audit.actual_row_count == 2
    assert audit.print_result_counts == {"not_printed": 2}
    assert audit.issues == ()
    assert rows[0]["print_order"] == "1"
    assert rows[0]["part"] == "part_a"
    assert rows[0]["source"] == "printed_split"
    assert rows[0]["gate1_qc_result"] == "not_tested"
    assert rows[0]["print_result"] == "not_printed"
    assert rows[0]["print_evidence_path"] == ""

    print_qc_audit = audit_first_print_y_split_gate1_print_qc(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=gate1_qc,
        print_batch_traveler_path=traveler,
        sliced_output_path=sliced_outputs,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not print_qc_audit.print_qc_ready
    assert print_qc_audit.gate1_qc_worksheet_valid
    assert not print_qc_audit.gate1_pass_ready
    assert print_qc_audit.print_batch_handoff_ready
    assert print_qc_audit.unprinted_parts == ("part_a", "part_b")
    assert print_qc_audit.issues == ()

    gate1_rows = list(csv.DictReader(StringIO(gate1_qc.read_text())))
    for row in gate1_rows:
        row["measured_x_mm"] = row["target_x_mm"]
        row["measured_y_mm"] = row["target_y_mm"]
        row["measured_z_mm"] = row["target_z_mm"]
        row["evidence_path"] = f"evidence/gate1/{row['part']}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    gate1_qc.write_text(_worksheet_csv_from_rows(gate1_rows))
    rows = list(csv.DictReader(StringIO(traveler.read_text())))
    for row in rows:
        row["gate1_qc_result"] = "pass"
    traveler.write_text(_worksheet_csv_from_rows(rows))

    unprinted_pass_audit = audit_first_print_y_split_gate1_print_qc(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=gate1_qc,
        print_batch_traveler_path=traveler,
        sliced_output_path=sliced_outputs,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not unprinted_pass_audit.print_qc_ready
    assert unprinted_pass_audit.gate1_pass_ready
    assert unprinted_pass_audit.unprinted_parts == ("part_a", "part_b")
    assert {
        (issue.part, issue.field) for issue in unprinted_pass_audit.issues
    } == {("part_a", "print_result"), ("part_b", "print_result")}

    rows = list(csv.DictReader(StringIO(traveler.read_text())))
    for row in rows:
        row["print_result"] = "printed"
    traveler.write_text(_worksheet_csv_from_rows(rows))
    unevidenced_print_audit = audit_first_print_y_split_gate1_print_qc(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=gate1_qc,
        print_batch_traveler_path=traveler,
        sliced_output_path=sliced_outputs,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not unevidenced_print_audit.print_qc_ready
    assert not unevidenced_print_audit.print_batch_handoff_ready
    assert unevidenced_print_audit.printed_row_count == 2
    assert {
        (issue.part, issue.field) for issue in unevidenced_print_audit.issues
    } == {("part_a", "print_evidence_path"), ("part_b", "print_evidence_path")}

    rows = list(csv.DictReader(StringIO(traveler.read_text())))
    for row in rows:
        row["print_evidence_path"] = f"evidence/print_batch/{row['part']}.jpg"
    traveler.write_text(_worksheet_csv_from_rows(rows))
    missing_print_evidence_audit = audit_first_print_y_split_print_batch_traveler(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        sliced_output_path=sliced_outputs,
        gate1_qc_path=gate1_qc,
        worksheet_path=traveler,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not missing_print_evidence_audit.handoff_ready
    assert {
        (issue.part, issue.field, issue.message)
        for issue in missing_print_evidence_audit.issues
    } == {
        ("part_a", "print_evidence_path", "print evidence path does not exist"),
        ("part_b", "print_evidence_path", "print evidence path does not exist"),
    }

    for row in rows:
        _write_evidence_file(tmp_path, row["print_evidence_path"])
    traveler.write_text(_worksheet_csv_from_rows(rows))
    ready_print_qc_audit = audit_first_print_y_split_gate1_print_qc(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=gate1_qc,
        print_batch_traveler_path=traveler,
        sliced_output_path=sliced_outputs,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert ready_print_qc_audit.print_qc_ready
    assert ready_print_qc_audit.printed_row_count == 2
    assert ready_print_qc_audit.unprinted_parts == ()
    assert ready_print_qc_audit.issues == ()

    rows[0]["sliced_output_sha256"] = "stale"
    traveler.write_text(_worksheet_csv_from_rows(rows))
    stale_audit = audit_first_print_y_split_print_batch_traveler(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        sliced_output_path=sliced_outputs,
        gate1_qc_path=gate1_qc,
        worksheet_path=traveler,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not stale_audit.worksheet_valid
    assert any(issue.field == "sliced_output_sha256" for issue in stale_audit.issues)


def test_y_split_gate2_dry_assembly_readiness_requires_print_and_inventory(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    queue_dir = tmp_path / "split_queue"
    queue_dir.mkdir()
    stl_a = queue_dir / "part_a.stl"
    stl_b = queue_dir / "part_b.stl"
    stl_a.write_text("solid part a\n")
    stl_b.write_text("solid part b\n")
    (queue_dir / "SLICER_QUEUE_MANIFEST.md").write_text(
        "\n".join(
            (
                "# Test First-Print Slicer Queue",
                "",
                "| Part | Queued STL | SHA256 | Target X mm | Target Y mm | Target Z mm | Role |",
                "|---|---|---|---:|---:|---:|---|",
                f"| `part_a` | `{stl_a.name}` | `{file_sha256(stl_a)}` | "
                "10.00 | 20.00 | 3.00 | printed split segment |",
                f"| `part_b` | `{stl_b.name}` | `{file_sha256(stl_b)}` | "
                "11.00 | 21.00 | 4.00 | printed |",
            )
        )
    )
    gcode_a = tmp_path / "part_a.gcode"
    gcode_b = tmp_path / "part_b.gcode"
    gcode_a.write_text("gcode a\n")
    gcode_b.write_text("gcode b\n")
    sliced_outputs = tmp_path / "split_sliced_outputs.csv"
    sliced_outputs.write_text(
        _worksheet_csv_from_rows(
            [
                {
                    "part": "part_a",
                    "queued_stl_path": str(stl_a),
                    "queued_stl_sha256": file_sha256(stl_a),
                    "sliced_output_path": str(gcode_a),
                    "sliced_output_sha256": file_sha256(gcode_a),
                    "selected_setup_summary": TEST_SLICER_SETUP_SUMMARY,
                    "result": "pass",
                    "notes": "sliced with fake slicer",
                },
                {
                    "part": "part_b",
                    "queued_stl_path": str(stl_b),
                    "queued_stl_sha256": file_sha256(stl_b),
                    "sliced_output_path": str(gcode_b),
                    "sliced_output_sha256": file_sha256(gcode_b),
                    "selected_setup_summary": TEST_SLICER_SETUP_SUMMARY,
                    "result": "pass",
                    "notes": "sliced with fake slicer",
                },
            ]
        )
    )
    gate1_qc = tmp_path / "split_gate1_qc.csv"
    gate1_qc.write_text(
        _worksheet_csv_from_rows(
            [
                {
                    "part": "part_a",
                    "source": "printed_split",
                    "target_x_mm": "10.00",
                    "target_y_mm": "20.00",
                    "target_z_mm": "3.00",
                    "measured_x_mm": "",
                    "measured_y_mm": "",
                    "measured_z_mm": "",
                    "evidence_path": "",
                    "result": "not_tested",
                    "notes": "",
                },
                {
                    "part": "part_b",
                    "source": "printed",
                    "target_x_mm": "11.00",
                    "target_y_mm": "21.00",
                    "target_z_mm": "4.00",
                    "measured_x_mm": "",
                    "measured_y_mm": "",
                    "measured_z_mm": "",
                    "evidence_path": "",
                    "result": "not_tested",
                    "notes": "",
                },
            ]
        )
    )
    traveler = tmp_path / "print_batch_traveler.csv"
    write_first_print_y_split_print_batch_traveler(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        sliced_output_path=sliced_outputs,
        gate1_qc_path=gate1_qc,
        output_path=traveler,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )
    gate2_dry_assembly = tmp_path / "gate2_dry_assembly.csv"
    gate2_dry_assembly.write_text(first_print_gate2_dry_assembly_worksheet_csv(params))
    install_inventory = tmp_path / "install_inventory.csv"
    install_inventory.write_text(first_print_install_inventory_csv())
    _write_ready_service_state_review_fixture(tmp_path)
    service_state_review = (
        tmp_path / "2026-06-02_one_row_coupon_service_state_review.csv"
    )

    blank_audit = audit_first_print_y_split_gate2_dry_assembly_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=gate1_qc,
        print_batch_traveler_path=traveler,
        sliced_output_path=sliced_outputs,
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not blank_audit.dry_assembly_ready
    assert blank_audit.gate2_dry_assembly_worksheet_valid
    assert not blank_audit.gate2_dry_assembly_pass_ready
    assert blank_audit.gate2_pass_row_count == 0
    assert not blank_audit.gate1_print_qc_ready
    assert blank_audit.install_inventory_valid
    assert not blank_audit.install_inventory_ready
    assert blank_audit.service_state_review_valid
    assert blank_audit.service_state_review_ready
    assert blank_audit.issues == ()

    gate2_rows = list(
        csv.DictReader(StringIO(first_print_gate2_dry_assembly_worksheet_csv(params)))
    )
    for row in gate2_rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    gate2_dry_assembly.write_text(_worksheet_csv_from_rows(gate2_rows))

    false_pass_audit = audit_first_print_y_split_gate2_dry_assembly_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=gate1_qc,
        print_batch_traveler_path=traveler,
        sliced_output_path=sliced_outputs,
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not false_pass_audit.dry_assembly_ready
    assert false_pass_audit.gate2_dry_assembly_pass_ready
    assert false_pass_audit.gate2_pass_row_count == 15
    assert {
        issue.field for issue in false_pass_audit.issues
    } == {"Gate 1 print QC", "Install inventory"}

    write_first_print_service_state_review(
        output_path=service_state_review,
        overwrite=True,
    )
    unready_service_audit = audit_first_print_y_split_gate2_dry_assembly_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=gate1_qc,
        print_batch_traveler_path=traveler,
        sliced_output_path=sliced_outputs,
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not unready_service_audit.dry_assembly_ready
    assert unready_service_audit.service_state_review_valid
    assert not unready_service_audit.service_state_review_ready
    assert {
        issue.field for issue in unready_service_audit.issues
    } == {"Gate 1 print QC", "Install inventory", "Service state review"}
    _write_ready_service_state_review_fixture(tmp_path)

    gate1_rows = list(csv.DictReader(StringIO(gate1_qc.read_text())))
    for row in gate1_rows:
        row["measured_x_mm"] = row["target_x_mm"]
        row["measured_y_mm"] = row["target_y_mm"]
        row["measured_z_mm"] = row["target_z_mm"]
        row["evidence_path"] = f"evidence/gate1/{row['part']}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    gate1_qc.write_text(_worksheet_csv_from_rows(gate1_rows))
    traveler_rows = list(csv.DictReader(StringIO(traveler.read_text())))
    for row in traveler_rows:
        row["gate1_qc_result"] = "pass"
        row["print_result"] = "printed"
        row["print_evidence_path"] = f"evidence/print_batch/{row['part']}.jpg"
        _write_evidence_file(tmp_path, row["print_evidence_path"])
    traveler.write_text(_worksheet_csv_from_rows(traveler_rows))
    inventory_rows = list(csv.DictReader(StringIO(first_print_install_inventory_csv())))
    for row in inventory_rows:
        row["item_identifier"] = f"inventory-{row['part']}"
        row["evidence_path"] = f"evidence/install_inventory/{row['part']}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
        if row["source"] == "cots_consumable":
            row["installed_as"] = "real_part"
        elif row["source"] == "service_tubing":
            row["installed_as"] = "measured_replacement"
        else:
            row["installed_as"] = "dimensional_blank"
            row["notes"] = "mechanical-only blank; no sensing authority"
    install_inventory.write_text(_worksheet_csv_from_rows(inventory_rows))

    ready_audit = audit_first_print_y_split_gate2_dry_assembly_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=queue_dir,
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=gate1_qc,
        print_batch_traveler_path=traveler,
        sliced_output_path=sliced_outputs,
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert ready_audit.dry_assembly_ready
    assert ready_audit.gate1_print_qc_ready
    assert ready_audit.install_inventory_ready
    assert ready_audit.service_state_review_ready
    assert ready_audit.issues == ()


def test_y_split_gate3_placement_readiness_requires_gate2_dry_assembly(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    fixture = _write_tiny_split_print_qc_fixture(tmp_path, params)
    gate2_dry_assembly = tmp_path / "gate2_dry_assembly.csv"
    gate2_dry_assembly.write_text(first_print_gate2_dry_assembly_worksheet_csv(params))
    install_inventory = tmp_path / "install_inventory.csv"
    install_inventory.write_text(first_print_install_inventory_csv())
    _write_ready_service_state_review_fixture(tmp_path)
    service_state_review = (
        tmp_path / "2026-06-02_one_row_coupon_service_state_review.csv"
    )
    gate3_placement = tmp_path / "gate3_placement.csv"
    gate3_placement.write_text(first_print_gate3_placement_worksheet_csv(params))

    blank_audit = audit_first_print_y_split_gate3_placement_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not blank_audit.placement_ready
    assert blank_audit.gate3_placement_worksheet_valid
    assert not blank_audit.gate3_placement_pass_ready
    assert blank_audit.gate3_pass_row_count == 0
    assert not blank_audit.gate2_dry_assembly_ready
    assert blank_audit.issues == ()

    gate3_rows = list(
        csv.DictReader(StringIO(first_print_gate3_placement_worksheet_csv(params)))
    )
    for row in gate3_rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    gate3_placement.write_text(_worksheet_csv_from_rows(gate3_rows))

    false_pass_audit = audit_first_print_y_split_gate3_placement_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not false_pass_audit.placement_ready
    assert false_pass_audit.gate3_placement_pass_ready
    assert false_pass_audit.gate3_pass_row_count == 12
    assert {
        issue.field for issue in false_pass_audit.issues
    } == {"Gate 2 dry assembly"}

    gate1_rows = list(csv.DictReader(StringIO(fixture["gate1_qc"].read_text())))
    for row in gate1_rows:
        row["measured_x_mm"] = row["target_x_mm"]
        row["measured_y_mm"] = row["target_y_mm"]
        row["measured_z_mm"] = row["target_z_mm"]
        row["evidence_path"] = f"evidence/gate1/{row['part']}.jpg"
        _write_evidence_file(fixture["gate1_qc"].parent, row["evidence_path"])
        row["result"] = "pass"
    fixture["gate1_qc"].write_text(_worksheet_csv_from_rows(gate1_rows))
    traveler_rows = list(csv.DictReader(StringIO(fixture["traveler"].read_text())))
    for row in traveler_rows:
        row["gate1_qc_result"] = "pass"
        row["print_result"] = "printed"
        row["print_evidence_path"] = f"evidence/print_batch/{row['part']}.jpg"
        _write_evidence_file(fixture["traveler"].parent, row["print_evidence_path"])
    fixture["traveler"].write_text(_worksheet_csv_from_rows(traveler_rows))
    inventory_rows = list(csv.DictReader(StringIO(first_print_install_inventory_csv())))
    for row in inventory_rows:
        row["item_identifier"] = f"inventory-{row['part']}"
        row["evidence_path"] = f"evidence/install_inventory/{row['part']}.jpg"
        _write_evidence_file(fixture["traveler"].parent, row["evidence_path"])
        row["result"] = "pass"
        if row["source"] == "cots_consumable":
            row["installed_as"] = "real_part"
        elif row["source"] == "service_tubing":
            row["installed_as"] = "measured_replacement"
        else:
            row["installed_as"] = "dimensional_blank"
            row["notes"] = "mechanical-only blank; no sensing authority"
    install_inventory.write_text(_worksheet_csv_from_rows(inventory_rows))
    gate2_rows = list(
        csv.DictReader(StringIO(first_print_gate2_dry_assembly_worksheet_csv(params)))
    )
    for row in gate2_rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(gate2_dry_assembly.parent, row["evidence_path"])
        row["result"] = "pass"
    gate2_dry_assembly.write_text(_worksheet_csv_from_rows(gate2_rows))

    ready_audit = audit_first_print_y_split_gate3_placement_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert ready_audit.placement_ready
    assert ready_audit.gate2_dry_assembly_ready
    assert ready_audit.issues == ()


def test_y_split_gate4_wet_dry_witness_readiness_requires_gate3_placement(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    fixture = _write_tiny_split_print_qc_fixture(tmp_path, params)
    gate2_dry_assembly = tmp_path / "gate2_dry_assembly.csv"
    gate2_dry_assembly.write_text(first_print_gate2_dry_assembly_worksheet_csv(params))
    install_inventory = tmp_path / "install_inventory.csv"
    install_inventory.write_text(first_print_install_inventory_csv())
    _write_ready_service_state_review_fixture(tmp_path)
    service_state_review = (
        tmp_path / "2026-06-02_one_row_coupon_service_state_review.csv"
    )
    gate3_placement = tmp_path / "gate3_placement.csv"
    gate3_placement.write_text(first_print_gate3_placement_worksheet_csv(params))
    gate4_wet_dry_witness = tmp_path / "gate4_wet_dry_witness.csv"
    gate4_wet_dry_witness.write_text(
        first_print_gate4_wet_dry_witness_worksheet_csv(params)
    )

    blank_audit = audit_first_print_y_split_gate4_wet_dry_witness_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not blank_audit.wet_dry_witness_ready
    assert blank_audit.gate4_wet_dry_witness_worksheet_valid
    assert not blank_audit.gate4_wet_dry_witness_pass_ready
    assert blank_audit.gate4_pass_row_count == 0
    assert not blank_audit.gate3_placement_ready
    assert blank_audit.issues == ()

    gate4_rows = list(
        csv.DictReader(StringIO(first_print_gate4_wet_dry_witness_worksheet_csv(params)))
    )
    for row in gate4_rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    gate4_wet_dry_witness.write_text(_worksheet_csv_from_rows(gate4_rows))

    false_pass_audit = audit_first_print_y_split_gate4_wet_dry_witness_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not false_pass_audit.wet_dry_witness_ready
    assert false_pass_audit.gate4_wet_dry_witness_pass_ready
    assert false_pass_audit.gate4_pass_row_count == 10
    assert {
        issue.field for issue in false_pass_audit.issues
    } == {"Gate 3 placement"}

    gate1_rows = list(csv.DictReader(StringIO(fixture["gate1_qc"].read_text())))
    for row in gate1_rows:
        row["measured_x_mm"] = row["target_x_mm"]
        row["measured_y_mm"] = row["target_y_mm"]
        row["measured_z_mm"] = row["target_z_mm"]
        row["evidence_path"] = f"evidence/gate1/{row['part']}.jpg"
        _write_evidence_file(fixture["gate1_qc"].parent, row["evidence_path"])
        row["result"] = "pass"
    fixture["gate1_qc"].write_text(_worksheet_csv_from_rows(gate1_rows))
    traveler_rows = list(csv.DictReader(StringIO(fixture["traveler"].read_text())))
    for row in traveler_rows:
        row["gate1_qc_result"] = "pass"
        row["print_result"] = "printed"
        row["print_evidence_path"] = f"evidence/print_batch/{row['part']}.jpg"
        _write_evidence_file(fixture["traveler"].parent, row["print_evidence_path"])
    fixture["traveler"].write_text(_worksheet_csv_from_rows(traveler_rows))
    inventory_rows = list(csv.DictReader(StringIO(first_print_install_inventory_csv())))
    for row in inventory_rows:
        row["item_identifier"] = f"inventory-{row['part']}"
        row["evidence_path"] = f"evidence/install_inventory/{row['part']}.jpg"
        _write_evidence_file(fixture["traveler"].parent, row["evidence_path"])
        row["result"] = "pass"
        if row["source"] == "cots_consumable":
            row["installed_as"] = "real_part"
        elif row["source"] == "service_tubing":
            row["installed_as"] = "measured_replacement"
        else:
            row["installed_as"] = "dimensional_blank"
            row["notes"] = "mechanical-only blank; no sensing authority"
    install_inventory.write_text(_worksheet_csv_from_rows(inventory_rows))
    gate2_rows = list(
        csv.DictReader(StringIO(first_print_gate2_dry_assembly_worksheet_csv(params)))
    )
    for row in gate2_rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(gate2_dry_assembly.parent, row["evidence_path"])
        row["result"] = "pass"
    gate2_dry_assembly.write_text(_worksheet_csv_from_rows(gate2_rows))
    gate3_rows = list(
        csv.DictReader(StringIO(first_print_gate3_placement_worksheet_csv(params)))
    )
    for row in gate3_rows:
        row["measured_value"] = f"observed {row['target']}"
        row["evidence_path"] = f"evidence/{row['target'].lower().replace(' ', '_')}.jpg"
        _write_evidence_file(gate3_placement.parent, row["evidence_path"])
        row["result"] = "pass"
    gate3_placement.write_text(_worksheet_csv_from_rows(gate3_rows))

    ready_audit = audit_first_print_y_split_gate4_wet_dry_witness_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert ready_audit.wet_dry_witness_ready
    assert ready_audit.gate3_placement_ready
    assert ready_audit.issues == ()


def test_y_split_gate5_consumable_puncture_readiness_requires_gate4_wet_dry(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    fixture = _write_tiny_split_print_qc_fixture(tmp_path, params)
    gate2_dry_assembly = tmp_path / "gate2_dry_assembly.csv"
    gate2_dry_assembly.write_text(first_print_gate2_dry_assembly_worksheet_csv(params))
    install_inventory = tmp_path / "install_inventory.csv"
    install_inventory.write_text(first_print_install_inventory_csv())
    _write_ready_service_state_review_fixture(tmp_path)
    service_state_review = (
        tmp_path / "2026-06-02_one_row_coupon_service_state_review.csv"
    )
    gate3_placement = tmp_path / "gate3_placement.csv"
    gate3_placement.write_text(first_print_gate3_placement_worksheet_csv(params))
    gate4_wet_dry_witness = tmp_path / "gate4_wet_dry_witness.csv"
    gate4_wet_dry_witness.write_text(
        first_print_gate4_wet_dry_witness_worksheet_csv(params)
    )
    gate5_consumable_puncture = tmp_path / "gate5_consumable_puncture.csv"
    gate5_consumable_puncture.write_text(
        first_print_gate5_consumable_puncture_worksheet_csv(params)
    )

    blank_audit = audit_first_print_y_split_gate5_consumable_puncture_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        gate5_consumable_puncture_path=gate5_consumable_puncture,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not blank_audit.consumable_puncture_ready
    assert blank_audit.gate5_consumable_puncture_worksheet_valid
    assert not blank_audit.gate5_consumable_puncture_pass_ready
    assert blank_audit.gate5_pass_row_count == 0
    assert not blank_audit.gate4_wet_dry_witness_ready
    assert blank_audit.issues == ()

    _write_passed_target_worksheet(
        gate5_consumable_puncture,
        first_print_gate5_consumable_puncture_worksheet_csv(params),
    )
    false_pass_audit = audit_first_print_y_split_gate5_consumable_puncture_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        gate5_consumable_puncture_path=gate5_consumable_puncture,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not false_pass_audit.consumable_puncture_ready
    assert false_pass_audit.gate5_consumable_puncture_pass_ready
    assert false_pass_audit.gate5_pass_row_count == 14
    assert {
        issue.field for issue in false_pass_audit.issues
    } == {"Gate 4 wet/dry witness"}

    _mark_tiny_split_print_qc_ready(fixture)
    _write_ready_install_inventory(install_inventory)
    _write_passed_target_worksheet(
        gate2_dry_assembly,
        first_print_gate2_dry_assembly_worksheet_csv(params),
    )
    _write_passed_target_worksheet(
        gate3_placement,
        first_print_gate3_placement_worksheet_csv(params),
    )
    _write_passed_target_worksheet(
        gate4_wet_dry_witness,
        first_print_gate4_wet_dry_witness_worksheet_csv(params),
    )
    ready_audit = audit_first_print_y_split_gate5_consumable_puncture_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        gate5_consumable_puncture_path=gate5_consumable_puncture,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert ready_audit.consumable_puncture_ready
    assert ready_audit.gate4_wet_dry_witness_ready
    assert ready_audit.issues == ()


def test_y_split_gate6_sensor_thermal_readiness_requires_gate5_puncture(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    fixture = _write_tiny_split_print_qc_fixture(tmp_path, params)
    gate2_dry_assembly = tmp_path / "gate2_dry_assembly.csv"
    gate2_dry_assembly.write_text(first_print_gate2_dry_assembly_worksheet_csv(params))
    install_inventory = tmp_path / "install_inventory.csv"
    install_inventory.write_text(first_print_install_inventory_csv())
    _write_ready_service_state_review_fixture(tmp_path)
    service_state_review = (
        tmp_path / "2026-06-02_one_row_coupon_service_state_review.csv"
    )
    gate3_placement = tmp_path / "gate3_placement.csv"
    gate3_placement.write_text(first_print_gate3_placement_worksheet_csv(params))
    gate4_wet_dry_witness = tmp_path / "gate4_wet_dry_witness.csv"
    gate4_wet_dry_witness.write_text(
        first_print_gate4_wet_dry_witness_worksheet_csv(params)
    )
    gate5_consumable_puncture = tmp_path / "gate5_consumable_puncture.csv"
    gate5_consumable_puncture.write_text(
        first_print_gate5_consumable_puncture_worksheet_csv(params)
    )
    gate6_sensor_thermal = tmp_path / "gate6_sensor_thermal.csv"
    gate6_sensor_thermal.write_text(
        first_print_gate6_sensor_thermal_worksheet_csv(params)
    )

    blank_audit = audit_first_print_y_split_gate6_sensor_thermal_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        gate5_consumable_puncture_path=gate5_consumable_puncture,
        gate6_sensor_thermal_path=gate6_sensor_thermal,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not blank_audit.sensor_thermal_ready
    assert blank_audit.gate6_sensor_thermal_worksheet_valid
    assert not blank_audit.gate6_sensor_thermal_pass_ready
    assert blank_audit.gate6_pass_row_count == 0
    assert not blank_audit.gate5_consumable_puncture_ready
    assert blank_audit.gate5_pass_row_count == 0
    assert not blank_audit.gate4_wet_dry_witness_ready
    assert blank_audit.gate4_pass_row_count == 0
    assert not blank_audit.gate3_placement_ready
    assert blank_audit.gate3_pass_row_count == 0
    assert not blank_audit.gate2_dry_assembly_ready
    assert blank_audit.gate2_pass_row_count == 0
    assert not blank_audit.gate1_print_qc_ready
    assert not blank_audit.install_inventory_ready
    assert blank_audit.service_state_review_ready
    assert not blank_audit.real_sensor_inventory_ready
    assert blank_audit.sensor_inventory_blank_parts == ()
    assert blank_audit.issues == ()

    _write_passed_target_worksheet(
        gate6_sensor_thermal,
        first_print_gate6_sensor_thermal_worksheet_csv(params),
    )
    false_pass_audit = audit_first_print_y_split_gate6_sensor_thermal_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        gate5_consumable_puncture_path=gate5_consumable_puncture,
        gate6_sensor_thermal_path=gate6_sensor_thermal,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not false_pass_audit.sensor_thermal_ready
    assert false_pass_audit.gate6_sensor_thermal_pass_ready
    assert false_pass_audit.gate6_pass_row_count == 20
    assert not false_pass_audit.gate5_consumable_puncture_ready
    assert false_pass_audit.gate5_pass_row_count == 0
    assert not false_pass_audit.gate4_wet_dry_witness_ready
    assert false_pass_audit.gate4_pass_row_count == 0
    assert not false_pass_audit.gate3_placement_ready
    assert false_pass_audit.gate3_pass_row_count == 0
    assert not false_pass_audit.gate2_dry_assembly_ready
    assert false_pass_audit.gate2_pass_row_count == 0
    assert not false_pass_audit.gate1_print_qc_ready
    assert not false_pass_audit.install_inventory_ready
    assert not false_pass_audit.real_sensor_inventory_ready
    assert {
        issue.field for issue in false_pass_audit.issues
    } == {"Gate 5 consumable/puncture", "Install inventory"}

    _mark_tiny_split_print_qc_ready(fixture)
    _write_ready_install_inventory(install_inventory)
    _write_passed_target_worksheet(
        gate2_dry_assembly,
        first_print_gate2_dry_assembly_worksheet_csv(params),
    )
    _write_passed_target_worksheet(
        gate3_placement,
        first_print_gate3_placement_worksheet_csv(params),
    )
    _write_passed_target_worksheet(
        gate4_wet_dry_witness,
        first_print_gate4_wet_dry_witness_worksheet_csv(params),
    )
    _write_passed_target_worksheet(
        gate5_consumable_puncture,
        first_print_gate5_consumable_puncture_worksheet_csv(params),
    )
    blank_inventory_audit = audit_first_print_y_split_gate6_sensor_thermal_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        gate5_consumable_puncture_path=gate5_consumable_puncture,
        gate6_sensor_thermal_path=gate6_sensor_thermal,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not blank_inventory_audit.sensor_thermal_ready
    assert blank_inventory_audit.gate6_sensor_thermal_pass_ready
    assert blank_inventory_audit.gate5_consumable_puncture_ready
    assert blank_inventory_audit.gate5_pass_row_count == 14
    assert blank_inventory_audit.gate4_wet_dry_witness_ready
    assert blank_inventory_audit.gate4_pass_row_count == 10
    assert blank_inventory_audit.gate3_placement_ready
    assert blank_inventory_audit.gate3_pass_row_count == 12
    assert blank_inventory_audit.gate2_dry_assembly_ready
    assert blank_inventory_audit.gate2_pass_row_count == 15
    assert blank_inventory_audit.gate1_print_qc_ready
    assert blank_inventory_audit.install_inventory_ready
    assert not blank_inventory_audit.real_sensor_inventory_ready
    assert blank_inventory_audit.sensor_inventory_blank_parts
    assert {
        issue.field for issue in blank_inventory_audit.issues
    } == {"Install inventory"}

    _mark_install_inventory_real_sensors(install_inventory)
    ready_audit = audit_first_print_y_split_gate6_sensor_thermal_readiness(
        params=params,
        out_dir=tmp_path,
        split_dir=tmp_path / "unused_split_dir",
        queue_dir=fixture["queue_dir"],
        slicer_setup_path=tmp_path / "unused_setup.csv",
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        gate5_consumable_puncture_path=gate5_consumable_puncture,
        gate6_sensor_thermal_path=gate6_sensor_thermal,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert ready_audit.sensor_thermal_ready
    assert ready_audit.gate5_consumable_puncture_ready
    assert ready_audit.gate5_pass_row_count == 14
    assert ready_audit.gate4_wet_dry_witness_ready
    assert ready_audit.gate4_pass_row_count == 10
    assert ready_audit.gate3_placement_ready
    assert ready_audit.gate3_pass_row_count == 12
    assert ready_audit.gate2_dry_assembly_ready
    assert ready_audit.gate2_pass_row_count == 15
    assert ready_audit.gate1_print_qc_ready
    assert ready_audit.install_inventory_ready
    assert ready_audit.real_sensor_inventory_ready
    assert ready_audit.sensor_inventory_blank_parts == ()
    assert ready_audit.issues == ()


def test_y_split_operating_prototype_acceptance_requires_full_physical_chain(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    _write_ready_sliced_output_worksheet(params, tmp_path)
    fixture = _write_tiny_split_print_qc_fixture(tmp_path, params)
    setup_path = tmp_path / "2026-06-02_one_row_coupon_slicer_setup.csv"
    split_dir = tmp_path / "unused_split_dir"
    gate2_dry_assembly = tmp_path / "2026-06-02_one_row_coupon_gate2_dry_assembly.csv"
    gate3_placement = tmp_path / "2026-06-02_one_row_coupon_gate3_placement.csv"
    gate4_wet_dry_witness = (
        tmp_path / "2026-06-02_one_row_coupon_gate4_wet_dry_witness.csv"
    )
    gate5_consumable_puncture = (
        tmp_path / "2026-06-02_one_row_coupon_gate5_consumable_puncture.csv"
    )
    gate6_sensor_thermal = tmp_path / "2026-06-02_one_row_coupon_gate6_sensor_thermal.csv"
    install_inventory = tmp_path / "2026-06-02_one_row_coupon_install_inventory.csv"
    service_state_review = (
        tmp_path / "2026-06-02_one_row_coupon_service_state_review.csv"
    )

    blank_audit = audit_first_print_y_split_operating_prototype_acceptance(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        split_dir=split_dir,
        split_queue_dir=fixture["queue_dir"],
        record_path=record_path,
        root=tmp_path,
        slicer_setup_path=setup_path,
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        gate5_consumable_puncture_path=gate5_consumable_puncture,
        gate6_sensor_thermal_path=gate6_sensor_thermal,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not blank_audit.operating_prototype_ready
    assert blank_audit.preflight_artifacts_ready
    assert blank_audit.print_start_ready
    assert blank_audit.service_state_review_ready
    assert not blank_audit.install_inventory_ready
    assert not blank_audit.gate1_print_qc_ready
    assert not blank_audit.gate2_dry_assembly_ready
    assert blank_audit.gate2_pass_row_count == 0
    assert not blank_audit.gate3_placement_ready
    assert blank_audit.gate3_pass_row_count == 0
    assert not blank_audit.gate4_wet_dry_witness_ready
    assert blank_audit.gate4_pass_row_count == 0
    assert not blank_audit.gate5_consumable_puncture_ready
    assert blank_audit.gate5_pass_row_count == 0
    assert not blank_audit.sensor_thermal_ready
    assert not blank_audit.real_sensor_inventory_ready
    assert blank_audit.sensor_inventory_blank_parts == ()
    assert blank_audit.gate6_pass_row_count == 0
    assert blank_audit.next_evidence_actions == (
        "complete_install_inventory",
        "close_split_gate1_print_qc",
    )
    assert blank_audit.issues == ()

    _mark_tiny_split_print_qc_ready(fixture)
    _write_ready_install_inventory(install_inventory)
    _write_passed_target_worksheet(
        gate2_dry_assembly,
        first_print_gate2_dry_assembly_worksheet_csv(params),
    )
    _write_passed_target_worksheet(
        gate3_placement,
        first_print_gate3_placement_worksheet_csv(params),
    )
    _write_passed_target_worksheet(
        gate4_wet_dry_witness,
        first_print_gate4_wet_dry_witness_worksheet_csv(params),
    )
    _write_passed_target_worksheet(
        gate5_consumable_puncture,
        first_print_gate5_consumable_puncture_worksheet_csv(params),
    )
    _write_passed_target_worksheet(
        gate6_sensor_thermal,
        first_print_gate6_sensor_thermal_worksheet_csv(params),
    )
    blank_inventory_audit = audit_first_print_y_split_operating_prototype_acceptance(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        split_dir=split_dir,
        split_queue_dir=fixture["queue_dir"],
        record_path=record_path,
        root=tmp_path,
        slicer_setup_path=setup_path,
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        gate5_consumable_puncture_path=gate5_consumable_puncture,
        gate6_sensor_thermal_path=gate6_sensor_thermal,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not blank_inventory_audit.operating_prototype_ready
    assert blank_inventory_audit.preflight_artifacts_ready
    assert blank_inventory_audit.print_start_ready
    assert blank_inventory_audit.service_state_review_ready
    assert blank_inventory_audit.install_inventory_ready
    assert blank_inventory_audit.gate1_print_qc_ready
    assert blank_inventory_audit.gate2_dry_assembly_ready
    assert blank_inventory_audit.gate2_pass_row_count == 15
    assert blank_inventory_audit.gate3_placement_ready
    assert blank_inventory_audit.gate3_pass_row_count == 12
    assert blank_inventory_audit.gate4_wet_dry_witness_ready
    assert blank_inventory_audit.gate4_pass_row_count == 10
    assert blank_inventory_audit.gate5_consumable_puncture_ready
    assert blank_inventory_audit.gate5_pass_row_count == 14
    assert not blank_inventory_audit.sensor_thermal_ready
    assert not blank_inventory_audit.real_sensor_inventory_ready
    assert blank_inventory_audit.sensor_inventory_blank_parts
    assert blank_inventory_audit.gate6_pass_row_count == 20
    assert blank_inventory_audit.next_evidence_actions == (
        "install_real_sensor_inventory",
    )
    assert {
        issue.field for issue in blank_inventory_audit.issues
    } == {"Install inventory"}

    _mark_install_inventory_real_sensors(install_inventory)
    ready_audit = audit_first_print_y_split_operating_prototype_acceptance(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        split_dir=split_dir,
        split_queue_dir=fixture["queue_dir"],
        record_path=record_path,
        root=tmp_path,
        slicer_setup_path=setup_path,
        gate1_qc_path=fixture["gate1_qc"],
        print_batch_traveler_path=fixture["traveler"],
        sliced_output_path=fixture["sliced_outputs"],
        gate2_dry_assembly_path=gate2_dry_assembly,
        install_inventory_path=install_inventory,
        service_state_review_path=service_state_review,
        gate3_placement_path=gate3_placement,
        gate4_wet_dry_witness_path=gate4_wet_dry_witness,
        gate5_consumable_puncture_path=gate5_consumable_puncture,
        gate6_sensor_thermal_path=gate6_sensor_thermal,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert ready_audit.operating_prototype_ready
    assert ready_audit.service_state_review_ready
    assert ready_audit.install_inventory_ready
    assert ready_audit.gate1_print_qc_ready
    assert ready_audit.gate2_dry_assembly_ready
    assert ready_audit.gate2_pass_row_count == 15
    assert ready_audit.gate3_placement_ready
    assert ready_audit.gate3_pass_row_count == 12
    assert ready_audit.gate4_wet_dry_witness_ready
    assert ready_audit.gate4_pass_row_count == 10
    assert ready_audit.gate5_consumable_puncture_ready
    assert ready_audit.gate5_pass_row_count == 14
    assert ready_audit.sensor_thermal_ready
    assert ready_audit.real_sensor_inventory_ready
    assert ready_audit.sensor_inventory_blank_parts == ()
    assert ready_audit.gate6_pass_row_count == 20
    assert ready_audit.next_evidence_actions == ()
    assert ready_audit.issues == ()


def test_y_split_gate1_qc_rows_track_split_queue_items(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    setup_path = _write_selected_small_bed_setup(tmp_path)
    split_dir = tmp_path / "first_print_y_split_parts"
    _touch_y_split_artifacts(params, tmp_path, split_dir, setup_path)
    queue_dir = tmp_path / "split_queue"

    rows = first_print_y_split_gate1_qc_worksheet_rows(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
    )
    by_part = {row.part: row for row in rows}

    assert len(rows) == 21
    assert "deck_pods_y01_of_02" in by_part
    assert "deck_pods_y02_of_02" in by_part
    assert "printed_sample_relief_cap" in by_part
    assert "deck_pods" not in by_part
    assert by_part["deck_pods_y01_of_02"].source == "printed_split"
    assert by_part["deck_pods_y02_of_02"].source == "printed_split"
    assert by_part["printed_sample_relief_cap"].source == "printed"
    assert by_part["deck_pods_y01_of_02"].target_y_mm <= 210.0
    assert by_part["deck_pods_y01_of_02"].target_x_mm > 0
    assert by_part["deck_pods_y01_of_02"].target_z_mm > 0


def test_audit_first_print_y_split_gate1_qc_accepts_blank_preprint_sheet(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    setup_path = _write_selected_small_bed_setup(tmp_path)
    split_dir = tmp_path / "first_print_y_split_parts"
    _touch_y_split_artifacts(params, tmp_path, split_dir, setup_path)
    queue_dir = tmp_path / "split_queue"
    worksheet = tmp_path / "split_gate1_qc.csv"

    write_first_print_y_split_gate1_qc_worksheet(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
        output_path=worksheet,
    )
    audit = audit_first_print_y_split_gate1_qc_worksheet(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
        worksheet_path=worksheet,
    )

    assert audit.worksheet_valid
    assert not audit.gate1_pass_ready
    assert audit.expected_row_count == 21
    assert audit.actual_row_count == 21
    assert audit.result_counts == {"not_tested": 21}
    assert audit.missing_parts == ()
    assert audit.extra_parts == ()
    assert audit.duplicate_parts == ()
    assert audit.issues == ()


def test_audit_first_print_y_split_gate1_qc_passes_measured_target_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    setup_path = _write_selected_small_bed_setup(tmp_path)
    split_dir = tmp_path / "first_print_y_split_parts"
    _touch_y_split_artifacts(params, tmp_path, split_dir, setup_path)
    queue_dir = tmp_path / "split_queue"
    worksheet = tmp_path / "split_gate1_qc.csv"
    rows = list(
        csv.DictReader(
            StringIO(
                first_print_y_split_gate1_qc_worksheet_csv(
                    params=params,
                    out_dir=tmp_path,
                    split_dir=split_dir,
                    queue_dir=queue_dir,
                    slicer_setup_path=setup_path,
                )
            )
        )
    )
    for row in rows:
        row["measured_x_mm"] = row["target_x_mm"]
        row["measured_y_mm"] = row["target_y_mm"]
        row["measured_z_mm"] = row["target_z_mm"]
        row["evidence_path"] = f"evidence/gate1/{row['part']}.jpg"
        _write_evidence_file(tmp_path, row["evidence_path"])
        row["result"] = "pass"
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0])
    writer.writeheader()
    writer.writerows(rows)
    worksheet.write_text(output.getvalue())

    audit = audit_first_print_y_split_gate1_qc_worksheet(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
        worksheet_path=worksheet,
    )

    assert audit.worksheet_valid
    assert audit.gate1_pass_ready
    assert audit.expected_row_count == 21
    assert audit.result_counts == {"pass": 21}


def test_audit_first_print_slicer_setup_rejects_selected_incomplete_profile(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    worksheet_path = tmp_path / "slicer_setup.csv"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="printer",
        material_profile="",
        print_profile="print",
        profile_source="",
        selected="yes",
        result="pass",
    )
    worksheet_path.write_text(first_print_slicer_setup_csv((row,)))

    audit = audit_first_print_slicer_setup(worksheet_path=worksheet_path)

    assert not audit.worksheet_valid
    assert not audit.setup_selected
    assert any(issue.field == "material_profile" for issue in audit.issues)


def test_select_first_print_slicer_setup_updates_worksheet_and_record(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    other_executable = tmp_path / "other_slicer"
    other_executable.write_text("fake")
    profile_source = tmp_path / "profile.ini"
    profile_source.write_text("profile")
    worksheet_path = tmp_path / "slicer_setup.csv"
    record_path = tmp_path / "first_print.md"
    row = FirstPrintSlicerSetupRow(
        slicer_name="TestSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="printer",
        material_profile="material",
        print_profile="print",
        profile_source=str(profile_source),
    )
    other_row = FirstPrintSlicerSetupRow(
        slicer_name="OtherSlicer",
        executable_path=str(other_executable),
        version="1.0",
        printer_profile="other printer",
        material_profile="other material",
        print_profile="other print",
        profile_source=str(profile_source),
    )
    worksheet_path.write_text(first_print_slicer_setup_csv((row, other_row)))
    record_path.write_text(
        "\n".join(
            (
                "| Field | Value |",
                "|---|---|",
                "| Printer / material / profile |  |",
            )
        )
    )

    selection = select_first_print_slicer_setup(
        worksheet_path=worksheet_path,
        record_path=record_path,
        slicer_name="TestSlicer",
    )

    rows = list(csv.DictReader(StringIO(worksheet_path.read_text())))
    assert selection.selected_setup_summary == "TestSlicer / printer / material / print"
    assert rows[0]["selected"] == "yes"
    assert rows[0]["result"] == "pass"
    assert rows[1]["selected"] == "no"
    assert "| Printer / material / profile | TestSlicer / printer / material / print |" in (
        record_path.read_text()
    )


def test_select_first_print_slicer_setup_rejects_incomplete_candidate(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "slicer"
    executable.write_text("fake")
    worksheet_path = tmp_path / "slicer_setup.csv"
    record_path = tmp_path / "first_print.md"
    row = FirstPrintSlicerSetupRow(
        slicer_name="IncompleteSlicer",
        executable_path=str(executable),
        version="1.0",
        printer_profile="printer",
        material_profile="",
        print_profile="print",
        profile_source="",
    )
    worksheet_path.write_text(first_print_slicer_setup_csv((row,)))
    record_path.write_text("| Printer / material / profile |  |\n")

    with pytest.raises(ValueError, match="material_profile"):
        select_first_print_slicer_setup(
            worksheet_path=worksheet_path,
            record_path=record_path,
            slicer_name="IncompleteSlicer",
        )

    rows = list(csv.DictReader(StringIO(worksheet_path.read_text())))
    assert rows[0]["selected"] == ""
    assert rows[0]["result"] == "not_tested"
    assert record_path.read_text() == "| Printer / material / profile |  |\n"


def test_audit_first_print_preflight_passes_blank_preprint_artifacts(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert audit.preprint_ready
    assert not audit.print_start_ready
    assert audit.package_ready
    assert audit.slicer_queue_ready
    assert audit.params_hash_matches
    assert audit.record_params_sha256 == audit.expected_params_sha256
    assert audit.generated_output_timestamp_matches
    assert audit.cad_target_sections_match
    assert audit.stale_cad_target_sections == ()
    assert (
        audit.record_generated_output_timestamp
        == audit.expected_generated_output_timestamp
    )
    assert audit.slicer_setup_valid
    assert audit.slicer_setup_selected
    assert audit.selected_slicer_setup == TEST_SLICER_SETUP_SUMMARY
    assert audit.slicer_bed_fit_ready
    assert audit.slicer_bed_x_mm == 500.0
    assert audit.slicer_bed_y_mm == 500.0
    assert audit.slicer_bed_oversized_parts == ()
    assert audit.sliced_outputs_valid
    assert not audit.sliced_outputs_ready
    assert audit.gate1_qc_worksheet_valid
    assert not audit.gate1_pass_ready
    assert audit.gate2_dry_assembly_worksheet_valid
    assert not audit.gate2_dry_assembly_pass_ready
    assert audit.gate3_placement_worksheet_valid
    assert not audit.gate3_placement_pass_ready
    assert audit.gate4_wet_dry_witness_worksheet_valid
    assert not audit.gate4_wet_dry_witness_pass_ready
    assert audit.gate5_consumable_puncture_worksheet_valid
    assert not audit.gate5_consumable_puncture_pass_ready
    assert audit.gate6_sensor_thermal_worksheet_valid
    assert not audit.gate6_sensor_thermal_pass_ready
    assert audit.install_inventory_valid
    assert not audit.install_inventory_ready
    assert audit.service_state_review_valid
    assert audit.service_state_review_ready
    assert audit.record_gate0_pass
    assert audit.required_session_fields_present
    assert audit.missing_session_fields == ()
    assert audit.physical_gate_passes == ()
    assert audit.missing_record_links == ()
    assert audit.issues == ()


def test_audit_first_print_preflight_marks_print_start_ready_after_slicing(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    _write_ready_sliced_output_worksheet(params, tmp_path)

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert audit.preprint_ready
    assert audit.sliced_outputs_ready
    assert audit.service_state_review_ready
    assert audit.print_start_ready
    assert audit.issues == ()


def test_audit_first_print_preflight_rejects_small_selected_printer_bed(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    setup_path = tmp_path / "2026-06-02_one_row_coupon_slicer_setup.csv"
    small_profile = tmp_path / "small_bed_profile.ini"
    small_profile.write_text(
        "[printer:test printer]\n"
        "bed_shape = 0x0,250x0,250x210,0x210\n"
    )
    rows = list(csv.DictReader(StringIO(setup_path.read_text())))
    rows[0]["profile_source"] = str(small_profile)
    setup_path.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert not audit.slicer_bed_fit_ready
    assert audit.slicer_bed_x_mm == 250.0
    assert audit.slicer_bed_y_mm == 210.0
    assert "wet_chamber_frame" in audit.slicer_bed_oversized_parts
    assert any(issue.field == "Slicer bed fit" for issue in audit.issues)


def test_audit_first_print_preflight_uses_split_queue_mode_for_small_bed(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    setup_path = tmp_path / "2026-06-02_one_row_coupon_slicer_setup.csv"
    small_profile = tmp_path / "small_bed_profile.ini"
    small_profile.write_text(
        "[printer:small printer]\n"
        "bed_shape = 0x0,250x0,250x210,0x210\n"
    )
    rows = list(csv.DictReader(StringIO(setup_path.read_text())))
    rows[0]["printer_profile"] = "small printer"
    rows[0]["profile_source"] = str(small_profile)
    setup_path.write_text(_worksheet_csv_from_rows(rows))
    selected_summary = "TestSlicer / small printer / test material / test print profile"
    record = record_path.read_text()
    record = record.replace(
        "| Active print queue mode | monolithic |",
        "| Active print queue mode | split_y |",
        1,
    )
    record = record.replace(
        f"| Printer / material / profile | {TEST_SLICER_SETUP_SUMMARY} |",
        f"| Printer / material / profile | {selected_summary} |",
        1,
    )
    record_path.write_text(record)
    split_dir = tmp_path / "first_print_y_split_parts"
    queue_dir = tmp_path / "first_print_y_split_slicer_queue"
    _touch_y_split_artifacts(params, tmp_path, split_dir, setup_path)
    prepare_first_print_y_split_slicer_queue(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
    )
    write_first_print_y_split_sliced_outputs(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
        output_path=tmp_path / "2026-06-02_one_row_coupon_y_split_sliced_outputs.csv",
        selected_setup_summary=selected_summary,
    )
    write_first_print_y_split_gate1_qc_worksheet(
        params=params,
        out_dir=tmp_path,
        split_dir=split_dir,
        queue_dir=queue_dir,
        slicer_setup_path=setup_path,
        output_path=tmp_path / "2026-06-02_one_row_coupon_y_split_gate1_qc.csv",
    )

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        split_dir=split_dir,
        record_path=record_path,
        root=tmp_path,
    )

    assert audit.active_queue_mode == "split_y"
    assert audit.preprint_ready
    assert not audit.print_start_ready
    assert audit.slicer_queue_ready
    assert audit.slicer_bed_fit_ready
    assert audit.slicer_bed_x_mm == 250.0
    assert audit.slicer_bed_y_mm == 210.0
    assert audit.slicer_bed_oversized_parts == ()
    assert audit.sliced_outputs_valid
    assert not audit.sliced_outputs_ready
    assert audit.gate1_qc_worksheet_valid
    assert not audit.gate1_pass_ready
    assert audit.missing_record_links == ()
    assert audit.issues == ()


def test_audit_first_print_preflight_rejects_physical_gate_pass(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    record = record_path.read_text()
    record = record.replace(
        "| Gate 1 Print QC | not_tested |  |",
        "| Gate 1 Print QC | pass | unsupported physical claim |",
        1,
    )
    record_path.write_text(record)

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert audit.physical_gate_passes == ("Gate 1 Print QC",)
    assert any(issue.field == "Gate 1 Print QC" for issue in audit.issues)


def test_audit_first_print_preflight_rejects_blank_printer_profile(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    record = record_path.read_text()
    record = record.replace(
        f"| Printer / material / profile | {TEST_SLICER_SETUP_SUMMARY} |",
        "| Printer / material / profile |  |",
        1,
    )
    record_path.write_text(record)

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert not audit.required_session_fields_present
    assert audit.missing_session_fields == ("Printer / material / profile",)
    assert any(issue.field == "Printer / material / profile" for issue in audit.issues)


def test_audit_first_print_preflight_rejects_stale_params_hash(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    record = record_path.read_text()
    record = record.replace(
        f"| Params SHA256 | {file_sha256(tmp_path / 'one_row_coupon.params.json')} |",
        "| Params SHA256 | stale |",
        1,
    )
    record_path.write_text(record)

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert not audit.params_hash_matches
    assert audit.record_params_sha256 == "stale"
    assert audit.expected_params_sha256 == file_sha256(
        tmp_path / "one_row_coupon.params.json"
    )
    assert any(issue.field == "Params SHA256" for issue in audit.issues)


def test_audit_first_print_preflight_rejects_stale_generated_output_timestamp(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    record = record_path.read_text()
    old_timestamp = next(
        line.split("|")[2].strip()
        for line in record.splitlines()
        if line.startswith("| Generated output timestamp |")
    )
    record = record.replace(
        f"| Generated output timestamp | {old_timestamp} |",
        "| Generated output timestamp | 2000-01-01T00:00:00Z |",
        1,
    )
    record_path.write_text(record)

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert not audit.generated_output_timestamp_matches
    assert audit.record_generated_output_timestamp == "2000-01-01T00:00:00Z"
    assert audit.expected_generated_output_timestamp == old_timestamp
    assert any(issue.field == "Generated output timestamp" for issue in audit.issues)


def test_audit_first_print_preflight_rejects_stale_cad_target_section(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    record = record_path.read_text()
    record = record.replace(
        "| Latch asymmetry watch | 1 omitted / 181.00 mm max span |",
        "| Latch asymmetry watch | stale |",
        1,
    )
    record_path.write_text(record)

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert not audit.cad_target_sections_match
    assert audit.stale_cad_target_sections == ("Gate 2 CAD Dry Assembly Targets",)
    assert any(
        issue.field == "Gate 2 CAD Dry Assembly Targets"
        and "missing or stale" in issue.message
        for issue in audit.issues
    )


def test_audit_first_print_preflight_rejects_mismatched_selected_setup(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    record = record_path.read_text()
    record = record.replace(
        f"| Printer / material / profile | {TEST_SLICER_SETUP_SUMMARY} |",
        "| Printer / material / profile | different printer / material / profile |",
        1,
    )
    record_path.write_text(record)

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert audit.slicer_setup_selected
    assert any(
        issue.field == "Printer / material / profile"
        and "must match selected slicer setup" in issue.message
        for issue in audit.issues
    )


def test_audit_first_print_preflight_rejects_missing_linked_sliced_outputs(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    (tmp_path / "2026-06-02_one_row_coupon_sliced_outputs.csv").unlink()

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert not audit.sliced_outputs_valid
    assert audit.missing_record_links == ("Sliced output worksheet",)
    assert any(
        issue.field == "Sliced output worksheet" for issue in audit.issues
    )


def test_audit_first_print_preflight_rejects_missing_linked_inventory(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    (tmp_path / "2026-06-02_one_row_coupon_install_inventory.csv").unlink()

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert audit.missing_record_links == ("Install inventory worksheet",)
    assert not audit.install_inventory_valid


def test_audit_first_print_preflight_rejects_missing_service_state_review(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    (tmp_path / "2026-06-02_one_row_coupon_service_state_review.csv").unlink()

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert audit.missing_record_links == ("Service state review worksheet",)


def test_audit_first_print_preflight_rejects_unready_service_state_review(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    write_first_print_service_state_review(
        output_path=tmp_path / "2026-06-02_one_row_coupon_service_state_review.csv",
        overwrite=True,
    )

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert audit.service_state_review_valid
    assert not audit.service_state_review_ready
    assert any(
        issue.field == "Service state review worksheet"
        and "pass-ready" in issue.message
        for issue in audit.issues
    )


def test_audit_first_print_preflight_rejects_missing_linked_gate2_dry_assembly(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    (tmp_path / "2026-06-02_one_row_coupon_gate2_dry_assembly.csv").unlink()

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert audit.missing_record_links == ("Gate 2 dry assembly worksheet",)
    assert not audit.gate2_dry_assembly_worksheet_valid


def test_audit_first_print_preflight_rejects_missing_linked_gate3_placement(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    (tmp_path / "2026-06-02_one_row_coupon_gate3_placement.csv").unlink()

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert audit.missing_record_links == ("Gate 3 placement worksheet",)
    assert not audit.gate3_placement_worksheet_valid


def test_audit_first_print_preflight_rejects_missing_linked_gate4_wet_dry_witness(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    (tmp_path / "2026-06-02_one_row_coupon_gate4_wet_dry_witness.csv").unlink()

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert audit.missing_record_links == ("Gate 4 wet/dry witness worksheet",)
    assert not audit.gate4_wet_dry_witness_worksheet_valid


def test_audit_first_print_preflight_rejects_missing_linked_gate5_consumable_puncture(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    (tmp_path / "2026-06-02_one_row_coupon_gate5_consumable_puncture.csv").unlink()

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert audit.missing_record_links == ("Gate 5 consumable/puncture worksheet",)
    assert not audit.gate5_consumable_puncture_worksheet_valid


def test_audit_first_print_preflight_rejects_missing_linked_gate6_sensor_thermal(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    record_path = _build_preflight_fixture(params, tmp_path)
    (tmp_path / "2026-06-02_one_row_coupon_gate6_sensor_thermal.csv").unlink()

    audit = audit_first_print_preflight(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "first_print_slicer_queue",
        record_path=record_path,
        root=tmp_path,
    )

    assert not audit.preprint_ready
    assert audit.missing_record_links == ("Gate 6 sensor/thermal worksheet",)
    assert not audit.gate6_sensor_thermal_worksheet_valid


def test_first_print_package_manifest_separates_print_queue_from_procurement(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    audit = audit_first_print_package(params, tmp_path)

    manifest = first_print_package_manifest_markdown(params, audit)
    slicer_section = manifest.split("## Flexible Or Compressible Parts", 1)[0]

    assert "## Slicer Queue: Printed Polymer Parts" in manifest
    assert "| Printed slicer parts | 12 |" in manifest
    assert "| Flexible/compressible parts | 4 |" in manifest
    assert "| COTS/electronics/service items | 12 |" in manifest
    assert "| Required validation bodies | 39 |" in manifest
    assert "| Optional validation bodies | 0 |" in manifest
    assert (
        "| Assembly policy | `print_native_screwless_no_glue_where_possible` |"
        in manifest
    )
    assert (
        "| Material authority decision | "
        "`2026-06-04 first_print_row_coupon_print_native_no_hidden_authority` |"
        in manifest
    )
    assert (
        "| Supersedes older insert strategy | "
        "`2026-05-06_printed_architecture_with_authority_inserts_for_this_coupon` |"
        in manifest
    )
    assert (
        "| Nonprinted exception policy | "
        "`explicit_cots_consumable_electronics_gasket_or_service_exception` |"
        in manifest
    )
    assert "`metal_insert`, `metal_fastener`" in manifest
    assert "`hidden_bonded_authority`" in manifest
    assert "## Operating Readiness Scope" in manifest
    assert (
        "| Service-state review | 28 viewer modes | every installed, service, "
        "bench-only, and fail-closed review mode must pass before preflight closes |"
    ) in manifest
    assert (
        "| Gate 1 Print QC | 16 rows | every printed or flexible part row requires "
        "measurements and evidence |"
    ) in manifest
    assert (
        "| Gate 2 Dry Assembly Fit | 15 rows | requires Gate 1 print QC, install "
        "inventory, service-state review, and all dry-assembly target evidence |"
    ) in manifest
    assert (
        "| Gate 6 Sensor And Thermal Link | 20 rows | requires Gate 5 readiness, "
        "real sensor inventory, powered sensor evidence, and thermal-proxy evidence |"
    ) in manifest
    assert (
        "| Install inventory | 12 rows | COTS consumables, service tubing, "
        "electronics, and sensor items must match their operating requirements; "
        "dimensional blanks cannot support Gate 6 or operating acceptance |"
    ) in manifest
    assert (
        "| Operating prototype acceptance | 6 gates | requires preflight artifacts, "
        "print-start readiness, service-state review, the full physical gate chain, "
        "and real sensor inventory |"
    ) in manifest
    assert "`deck_pods`" in slicer_section
    assert "`cots_microplates`" not in slicer_section
    assert "`gas_sensor_pcbs`" not in slicer_section
    assert "## Procure Or Install: Do Not Print As Production Parts" in manifest
    assert (
        "`cots_microplates` | cots_consumable | dimensional reference only | "
        "install real COTS consumable; dimensional blank not accepted"
    ) in manifest
    assert (
        "`cots_gas_service_tubes` | service_tubing | route and bend reference | "
        "install real tubing or measured replacement with evidence"
    ) in manifest
    assert (
        "`gas_sensor_pcbs` | electronics_or_dimensional_blank | "
        "dry-fit blank or real package reference | dimensional blank supports Gates 2-5 only; "
        "real part required for Gate 6 and operating acceptance"
    ) in manifest
    assert "## Operating Material And Exposure Policy" in manifest
    assert (
        "`lid_manifold_shell` | wet_headspace_boundary | "
        "printed_reusable_cleaning_pending"
    ) in manifest
    assert (
        "`cots_microplates` | wet_consumable | disposable_cots_consumable"
        in manifest
    )
    assert (
        "`lower_sensor_harness` | dry_electrical_service | "
        "electronics_or_dimensional_blank_not_cleaned"
    ) in manifest
    assert "## Validation Bodies: Do Not Install As Production Parts" in manifest
    assert "`deck_slot_footprint_check` | yes" in manifest
    assert "`deck_pod_seating_repeatability_check` | yes" in manifest
    assert "`pipette_puncture_swept_path_check` | yes" in manifest
    assert "`dry_bay_envelope_check` | yes" in manifest
    assert "`dry_bay_boundary_check` | yes" in manifest
    assert "`headspace_barrier_check` | yes" in manifest
    assert "`headspace_volume_check` | yes" in manifest
    assert "`gas_pcb_flow_cell_check` | yes" in manifest
    assert "`sensor_connector_service_clearance_check` | yes" in manifest
    assert "`consumable_metrology_gauge` | yes" in manifest
    assert "`printability_support_cleanup_check` | yes" in manifest
    assert "`latch_retention_span_check` | yes" in manifest
    assert "`observer_front_end_swept_body_check` | yes" in manifest
    assert "`observer_carriage_envelope_check` | yes" in manifest
    assert "`observer_service_raceway_envelope_check` | yes" in manifest
    assert "`observer_optical_stability_check` | yes" in manifest
    assert "`observer_kinematic_split_check` | yes" in manifest
    assert "`material_cleaning_witness_coupon` | yes" in manifest
    assert "`fail_closed_prerun_inspection_check` | yes" in manifest
    assert "Missing required files: none" in manifest


def test_write_first_print_package_manifest_refuses_overwrite(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    output_path = tmp_path / "manifest.md"
    output_path.write_text("existing")

    with pytest.raises(FileExistsError):
        write_first_print_package_manifest(
            params=params,
            out_dir=tmp_path,
            output_path=output_path,
        )


def test_first_print_slicer_queue_artifacts_are_printed_only(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    audit = audit_first_print_package(params, tmp_path)

    artifacts = first_print_slicer_queue_artifacts(audit)

    assert len(artifacts) == 12
    assert all(artifact.category == "printed" for artifact in artifacts)
    assert not any(artifact.name == "cots_microplates" for artifact in artifacts)
    assert not any(artifact.name == "deck_slot_footprint_check" for artifact in artifacts)


def test_prepare_first_print_slicer_queue_copies_only_printed_stls(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    queue_dir = tmp_path / "queue"

    items = prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )
    queue_manifest = (queue_dir / "SLICER_QUEUE_MANIFEST.md").read_text()
    queued_names = {path.name for path in queue_dir.iterdir()}

    assert len(items) == 12
    assert "aevum_one_row_coupon_deck_pods.stl" in queued_names
    assert "aevum_one_row_coupon_cots_microplates.stl" not in queued_names
    assert "aevum_one_row_coupon_validation_deck_slot_footprint_check.stl" not in queued_names
    assert "SLICER_QUEUE_MANIFEST.md" in queued_names
    assert "| Printed slicer queue files | 12 |" in queue_manifest
    assert "`cots_microplates`" not in queue_manifest
    assert "`deck_slot_footprint_check`" not in queue_manifest
    assert all(item.sha256 == file_sha256(item.queue_stl_path) for item in items)


def test_audit_first_print_slicer_queue_passes_for_clean_queue(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    queue_dir = tmp_path / "queue"
    prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )

    audit = audit_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )

    assert audit.ready
    assert audit.manifest_exists
    assert len(audit.expected_stl_paths) == 12
    assert len(audit.actual_stl_paths) == 12
    assert audit.missing_stl_paths == ()
    assert audit.extra_paths == ()
    assert audit.hash_mismatches == ()


def test_audit_first_print_slicer_queue_fails_for_extra_file(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    queue_dir = tmp_path / "queue"
    prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )
    extra = queue_dir / "aevum_one_row_coupon_cots_microplates.stl"
    extra.write_text("not a production print")

    audit = audit_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )

    assert not audit.ready
    assert extra in audit.extra_paths


def test_audit_first_print_slicer_queue_fails_for_missing_file(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    queue_dir = tmp_path / "queue"
    prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )
    missing = queue_dir / "aevum_one_row_coupon_deck_pods.stl"
    missing.unlink()

    audit = audit_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )

    assert not audit.ready
    assert missing in audit.missing_stl_paths


def test_audit_first_print_slicer_queue_fails_for_hash_mismatch(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    queue_dir = tmp_path / "queue"
    prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )
    changed = queue_dir / "aevum_one_row_coupon_deck_pods.stl"
    changed.write_text("modified after queue creation")

    audit = audit_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )

    assert not audit.ready
    assert len(audit.hash_mismatches) == 1
    assert audit.hash_mismatches[0].path == changed


def test_prepare_first_print_slicer_queue_refuses_overwrite(tmp_path: Path) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    queue_dir = tmp_path / "queue"
    prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )

    with pytest.raises(FileExistsError):
        prepare_first_print_slicer_queue(
            params=params,
            out_dir=tmp_path,
            queue_dir=queue_dir,
        )


def test_first_print_slicer_queue_manifest_names_physical_handoff_only(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    items = prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=tmp_path / "queue",
    )

    manifest = first_print_slicer_queue_manifest_markdown(
        params=params,
        items=items,
        queue_dir=tmp_path / "queue",
    )

    assert "contains only printed production STL files" in manifest
    assert "Do not add COTS consumables" in manifest
    assert "| Printed slicer queue files | 12 |" in manifest


def test_write_first_print_sliced_outputs_generates_valid_blank_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    queue_dir = tmp_path / "queue"
    prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )
    worksheet = tmp_path / "sliced_outputs.csv"

    write_first_print_sliced_outputs(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
        output_path=worksheet,
    )
    audit = audit_first_print_sliced_outputs(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
        worksheet_path=worksheet,
    )

    assert audit.worksheet_valid
    assert not audit.sliced_outputs_ready
    assert audit.expected_row_count == 12
    assert audit.actual_row_count == 12
    assert audit.result_counts == {"not_tested": 12}


def test_audit_first_print_sliced_outputs_accepts_ready_rows(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    queue_dir = tmp_path / "queue"
    prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )
    sliced_dir = tmp_path / "sliced"
    sliced_dir.mkdir()
    rows = list(
        csv.DictReader(
            StringIO(
                first_print_sliced_output_csv(
                    first_print_sliced_output_rows(
                        params=params,
                        out_dir=tmp_path,
                        queue_dir=queue_dir,
                        selected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
                    )
                )
            )
        )
    )
    for row in rows:
        output = sliced_dir / f"{row['part']}.gcode"
        output.write_text(f"sliced {row['part']}\n")
        row["sliced_output_path"] = str(output)
        row["sliced_output_sha256"] = file_sha256(output)
        row["result"] = "pass"
    worksheet = tmp_path / "sliced_outputs.csv"
    worksheet.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_sliced_outputs(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
        worksheet_path=worksheet,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert audit.worksheet_valid
    assert audit.sliced_outputs_ready
    assert audit.result_counts == {"pass": 12}


def test_audit_first_print_sliced_outputs_rejects_stale_output_hash(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    queue_dir = tmp_path / "queue"
    prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )
    rows = list(
        csv.DictReader(
            StringIO(
                first_print_sliced_output_csv(
                    first_print_sliced_output_rows(
                        params=params,
                        out_dir=tmp_path,
                        queue_dir=queue_dir,
                        selected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
                    )
                )
            )
        )
    )
    output = tmp_path / "one_part.gcode"
    output.write_text("sliced\n")
    rows[0]["sliced_output_path"] = str(output)
    rows[0]["sliced_output_sha256"] = "stale"
    rows[0]["result"] = "pass"
    worksheet = tmp_path / "sliced_outputs.csv"
    worksheet.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_sliced_outputs(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
        worksheet_path=worksheet,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not audit.worksheet_valid
    assert not audit.sliced_outputs_ready
    assert any(issue.field == "sliced_output_sha256" for issue in audit.issues)


def test_audit_first_print_sliced_outputs_rejects_setup_mismatch(
    tmp_path: Path,
) -> None:
    params = load_params(PARAMS)
    _touch_required_artifacts(params, tmp_path)
    queue_dir = tmp_path / "queue"
    prepare_first_print_slicer_queue(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
    )
    rows = list(
        csv.DictReader(
            StringIO(
                first_print_sliced_output_csv(
                    first_print_sliced_output_rows(
                        params=params,
                        out_dir=tmp_path,
                        queue_dir=queue_dir,
                        selected_setup_summary="wrong setup",
                    )
                )
            )
        )
    )
    output = tmp_path / "one_part.gcode"
    output.write_text("sliced\n")
    rows[0]["sliced_output_path"] = str(output)
    rows[0]["sliced_output_sha256"] = file_sha256(output)
    rows[0]["result"] = "pass"
    worksheet = tmp_path / "sliced_outputs.csv"
    worksheet.write_text(_worksheet_csv_from_rows(rows))

    audit = audit_first_print_sliced_outputs(
        params=params,
        out_dir=tmp_path,
        queue_dir=queue_dir,
        worksheet_path=worksheet,
        expected_setup_summary=TEST_SLICER_SETUP_SUMMARY,
    )

    assert not audit.worksheet_valid
    assert not audit.sliced_outputs_ready
    assert any(issue.field == "selected_setup_summary" for issue in audit.issues)
