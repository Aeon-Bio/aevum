from __future__ import annotations

from collections import Counter

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon import row_coupon_final_print_piece_plan
from aevum_cad.row_coupon_first_print import (
    audit_first_print_package,
    audit_first_print_slicer_bed_fit,
    expected_production_artifacts,
    first_print_final_piece_gate1_qc_worksheet_rows,
    first_print_final_piece_sliced_output_rows,
    first_print_final_piece_slicer_queue_items,
    first_print_package_manifest_markdown,
    first_print_qc_targets,
    first_print_slicer_queue_artifacts,
)

PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
SLICER_SETUP = ROOT / "data" / "measurements" / "2026-06-02_one_row_coupon_slicer_setup.csv"


def test_package_and_qc_targets_are_final_piece_named(tmp_path) -> None:
    params = load_params(PARAMS)
    plan = row_coupon_final_print_piece_plan(params)
    plan_names = [row["name"] for row in plan]
    piece_dir = tmp_path / "final_print_pieces"
    audit = audit_first_print_package(params, tmp_path)
    production = expected_production_artifacts(params, tmp_path)
    qc_targets = first_print_qc_targets(params)

    assert audit.production_artifacts == production
    assert Counter(artifact.category for artifact in production) == {
        "printed": 38,
        "compressible_or_flexible": 8,
    }
    printed_names = [
        artifact.name for artifact in production if artifact.category == "printed"
    ]
    assert printed_names == plan_names
    assert all(
        artifact.stl_path.parent == piece_dir
        for artifact in production
        if artifact.category == "printed"
    )

    flexible_names = [
        artifact.name
        for artifact in production
        if artifact.category == "compressible_or_flexible"
    ]
    assert len(flexible_names) == 8
    assert not set(flexible_names) & set(plan_names)
    assert Counter(target.category for target in qc_targets) == {
        "printed": 38,
        "compressible_or_flexible": 8,
    }
    assert [target.name for target in qc_targets if target.category == "printed"] == plan_names


def test_slicer_queue_gate1_and_sliced_rows_derive_from_final_piece_plan(tmp_path) -> None:
    params = load_params(PARAMS)
    plan = row_coupon_final_print_piece_plan(params)
    plan_names = [row["name"] for row in plan]
    piece_dir = tmp_path / "final_print_pieces"
    queue_dir = tmp_path / "first_print_final_piece_slicer_queue"
    audit = audit_first_print_package(params, tmp_path)

    queue_artifacts = first_print_slicer_queue_artifacts(audit)
    assert [artifact.name for artifact in queue_artifacts] == plan_names
    assert all(artifact.category == "printed" for artifact in queue_artifacts)

    bed_audit = audit_first_print_slicer_bed_fit(
        params=params,
        out_dir=tmp_path,
        worksheet_path=SLICER_SETUP,
    )
    assert bed_audit.bed_x_mm == 250.0
    assert bed_audit.bed_y_mm == 210.0
    assert bed_audit.oversized_parts == ()

    queue_items = first_print_final_piece_slicer_queue_items(
        params=params,
        out_dir=tmp_path,
        piece_dir=piece_dir,
        queue_dir=queue_dir,
        slicer_setup_path=SLICER_SETUP,
    )
    gate1_rows = first_print_final_piece_gate1_qc_worksheet_rows(
        params=params,
        out_dir=tmp_path,
        piece_dir=piece_dir,
        queue_dir=queue_dir,
        slicer_setup_path=SLICER_SETUP,
    )
    sliced_rows = first_print_final_piece_sliced_output_rows(
        params=params,
        out_dir=tmp_path,
        piece_dir=piece_dir,
        queue_dir=queue_dir,
        slicer_setup_path=SLICER_SETUP,
    )

    assert [item.name for item in queue_items] == plan_names
    assert [row.part for row in gate1_rows] == plan_names
    assert [row.part for row in sliced_rows] == plan_names
    assert all(item.queue_stl_path.parent == queue_dir for item in queue_items)
    assert all(item.source_stl_path.parent == piece_dir for item in queue_items)


def test_package_manifest_reports_final_piece_printed_count(tmp_path) -> None:
    params = load_params(PARAMS)
    audit = audit_first_print_package(params, tmp_path)
    manifest = first_print_package_manifest_markdown(params, audit)

    assert "| Printed slicer parts | 38 |" in manifest
    assert "| Flexible/compressible parts | 8 |" in manifest
    assert "`plate_support_frame_piece_01_of_02_y_000p000_to_188p625`" in manifest
    assert "`plate_support_frame` |" not in manifest
