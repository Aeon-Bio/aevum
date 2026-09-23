"""Final-piece joints must be connected, source-local, clear, and reconstructable."""
from __future__ import annotations

import pytest

import aevum_cad.row_coupon as m
from aevum_cad.params import ROOT, load_params

SEAM = 188.625


def _params():
    return load_params(ROOT / "cad" / "one_row_coupon.params.json")


@pytest.fixture(scope="module")
def realized_default():
    params = _params()
    realization = m.realize_row_coupon_final_print_pieces(params)
    realization.require_printable()
    return params, m._row_coupon_export_models(params), realization


def _piece_name(plan, source: str, piece_index: int) -> str:
    matches = [
        row["name"]
        for row in plan
        if row["source_artifact"] == source and row["piece_index"] == piece_index
    ]
    assert len(matches) == 1
    return matches[0]


def test_attached_key_has_real_mate_clearance_without_external_material(realized_default):
    _, source_models, realization = realized_default
    src = source_models["plate_support_frame"]  # has central seam material
    plan = realization.plan
    parts = realization.pieces
    lo = parts[_piece_name(plan, "plate_support_frame", 1)]
    up = parts[_piece_name(plan, "plate_support_frame", 2)]
    src_bb = src.val().BoundingBox()

    # (a) key actually attached (lower protrudes past the flat seam)
    assert lo.val().BoundingBox().ymax > SEAM + 0.1, "key did not attach on a solid-seam part"
    # (b) real fit: the upper pocket cavity is strictly larger than the lower boss
    butt_lo = m._clip_workplane_to_y_range(src, y_min=0.0, y_max=SEAM)
    butt_up = m._clip_workplane_to_y_range(src, y_min=SEAM, y_max=float(src_bb.ymax))
    boss_added = lo.val().Volume() - butt_lo.val().Volume()
    pocket_removed = butt_up.val().Volume() - up.val().Volume()
    assert pocket_removed > boss_added, (
        f"no fit clearance: pocket {pocket_removed:.2f} <= boss {boss_added:.2f} (interference)"
    )
    assert lo.intersect(up).val().Volume() == pytest.approx(0.0, abs=1e-4)
    seam = next(
        row["seam"]
        for row in plan
        if row["source_artifact"] == "plate_support_frame"
    )
    assert seam["fit_clearance_x_mm"] > 0.0
    assert seam["fit_clearance_y_mm"] > 0.0
    assert seam["fit_clearance_z_mm"] > 0.0
    # G5a: the structural backbone carries MULTIPLE keys (one per keyable wall), so the
    # added boss volume is well above a single key (~192 mm^3 at default dims).
    assert boss_added > 300.0, f"backbone should carry multiple G5a keys, got boss {boss_added:.0f}"
    # (c) the reconstructed pair stays inside the source envelope. Keys transfer
    # existing source material; they never invent a witness inside another interface.
    rb = lo.union(up).val().BoundingBox()
    assert rb.ymin >= src_bb.ymin - 0.01 and rb.ymax <= src_bb.ymax + 0.01
    assert rb.zmax <= src_bb.zmax + 0.01
    assert seam["source_excess_volume_mm3"] == pytest.approx(0.0, abs=1e-4)
    assert seam["witness_added_volume_mm3"] == 0.0


def test_wet_frame_uses_connected_source_local_labyrinth(realized_default):
    _, source_models, realization = realized_default
    plan = realization.plan
    parts = realization.pieces
    lo = parts[
        _piece_name(plan, "wet_chamber_frame", 1)
    ]
    seam = next(
        row["seam"]
        for row in plan
        if row["source_artifact"] == "wet_chamber_frame"
    )
    assert seam["mating_feature_kind"] == "printed_stepped_labyrinth_lap_and_pocket"
    assert lo.val().BoundingBox().ymax > seam["geometric_split_y_mm"]
    assert len(lo.val().Solids()) == 1
    up = parts[_piece_name(plan, "wet_chamber_frame", 2)]
    assert len(up.val().Solids()) == 1
    assert lo.intersect(up).val().Volume() == pytest.approx(0.0, abs=1e-4)
    assert seam["source_excess_volume_mm3"] == pytest.approx(0.0, abs=1e-4)
