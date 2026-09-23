from __future__ import annotations

import pytest

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon import realize_row_coupon_final_print_pieces


def test_every_structural_pair_is_connected_bed_fit_and_noninterfering() -> None:
    realization = realize_row_coupon_final_print_pieces(
        load_params(ROOT / "cad" / "one_row_coupon.params.json")
    )
    realization.require_printable()
    split_rows = [
        row for row in realization.plan if row["action"] == "structural_split"
    ]
    assert len(split_rows) == 16

    for row in split_rows:
        piece = realization.pieces[str(row["name"])]
        assert len(piece.val().Solids()) == 1
        assert row["fits_selected_bed"] is True
        assert row["seam"]["pair_interference_volume_mm3"] == pytest.approx(
            0.0, abs=1e-4
        )
        assert row["seam"]["mating_feature_kind"] != "plain_butt_fallback"
        assert row["seam"]["realized_key_count"] > 0
        assert any(
            authority in row["seam"]["retention_authority"]
            for authority in (
                "printed dovetail keys",
                "printed stepped lap",
                "full-thickness planar fingers",
            )
        )
