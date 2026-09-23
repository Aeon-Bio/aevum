from __future__ import annotations

from pathlib import Path

import aevum_cad.row_coupon as row_coupon


def test_public_print_api_has_one_current_generation_surface() -> None:
    assert callable(row_coupon.realize_row_coupon_final_print_pieces)
    assert callable(row_coupon.row_coupon_final_print_piece_plan)
    assert callable(row_coupon.build_row_coupon_final_print_pieces)
    assert callable(row_coupon.export_row_coupon_final_print_pieces)

    removed = {
        "build_row_coupon_production_y_split_parts",
        "export_row_coupon_production_y_split_parts",
        "row_coupon_production_y_split_plan",
        "ROW_COUPON_PRODUCTION_Y_SPLIT_PARTS",
    }
    assert removed.isdisjoint(vars(row_coupon))


def test_cq_viewer_consumes_one_realization_and_labels_physical_groups() -> None:
    viewer = (
        Path(__file__).resolve().parents[1]
        / "cad"
        / "view_one_row_coupon_print_pieces.py"
    ).read_text()
    assert viewer.count("realize_row_coupon_final_print_pieces(params)") == 1
    assert "realization.pieces" in viewer
    assert "realization.plan" in viewer
    assert "PRINT_STRUCTURAL" in viewer
    assert "PRINT_WHOLE" in viewer
    assert "PRINT_SERVICE" in viewer
