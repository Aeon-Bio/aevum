"""G1: D4 keyed split interface — flag-on geometry must form a REAL mate, not floating
cosmetic solids. Where the dovetail key attaches to seam material it must (a) have positive
fit clearance (pocket cavity strictly larger than the boss), (b) carry a witness that
protrudes above the body, and (c) reassemble within the source bbox. Where a bbox-centred
key would float in a hollow frame section, the seam must fall back to a plain butt (no
disconnected solid added). Robust per-wall key placement on hollow sections is deferred (G5).
"""
from __future__ import annotations

import copy

from aevum_cad.params import ROOT, load_params
import aevum_cad.row_coupon as m

SEAM = 188.625


def _keyed_params():
    p = copy.deepcopy(load_params(ROOT / "cad" / "one_row_coupon.params.json"))
    p["production_assembly"]["keyed_joints_enabled"] = True
    return p


def test_attached_key_has_real_mate_clearance_and_protruding_witness():
    p = _keyed_params()
    src = m._row_coupon_export_models(p)["plate_support_frame"]  # has central seam material
    parts = m.build_row_coupon_production_y_split_parts(p)
    lo = parts["plate_support_frame_y01_of_02"]
    up = parts["plate_support_frame_y02_of_02"]
    src_bb = src.val().BoundingBox()

    # (a) key actually attached (lower protrudes past the flat seam)
    assert lo.val().BoundingBox().ymax > SEAM + 0.1, "key did not attach on a solid-seam part"
    # (b) witness protrudes above the source top face
    assert lo.val().BoundingBox().zmax > src_bb.zmax + 0.01, "witness does not protrude"
    # (c) real fit: the upper pocket cavity is strictly larger than the lower boss
    butt_lo = m._clip_workplane_to_y_range(src, y_min=0.0, y_max=SEAM)
    butt_up = m._clip_workplane_to_y_range(src, y_min=SEAM, y_max=float(src_bb.ymax))
    boss_added = lo.val().Volume() - butt_lo.val().Volume()
    pocket_removed = butt_up.val().Volume() - up.val().Volume()
    assert pocket_removed > boss_added, (
        f"no fit clearance: pocket {pocket_removed:.2f} <= boss {boss_added:.2f} (interference)"
    )
    # G5a: the structural backbone carries MULTIPLE keys (one per keyable wall), so the
    # added boss volume is well above a single key (~192 mm^3 at default dims).
    assert boss_added > 300.0, f"backbone should carry multiple G5a keys, got boss {boss_added:.0f}"
    # (d) reassembles within the source bbox; Z only exceeds the source by the (bounded,
    # intentional) protruding witness height, not an unbounded envelope blowup
    rb = lo.union(up).val().BoundingBox()
    w_h = float(p["production_assembly"]["y_split_interface"].get("witness_height_mm", 0.5))
    assert rb.ymin >= src_bb.ymin - 0.01 and rb.ymax <= src_bb.ymax + 0.01
    assert rb.zmax <= src_bb.zmax + w_h + 0.01, "keyed part Z envelope grew beyond the witness height"


def test_thin_walled_part_falls_back_to_butt_not_floating_key():
    p = _keyed_params()
    parts = m.build_row_coupon_production_y_split_parts(p)
    lo = parts["wet_chamber_frame_y01_of_02"]  # thin perimeter walls at the seam
    # too thin for a robust oversized dovetail -> butt seam (retained globally / by the seal
    # + the keyed backbone it mounts to); no key protrusion, no floating disconnected boss
    assert abs(lo.val().BoundingBox().ymax - SEAM) < 1e-3, "thin-walled part should butt at the seam"
    assert len(lo.val().Solids()) == len(
        m._clip_workplane_to_y_range(
            m._row_coupon_export_models(p)["wet_chamber_frame"], y_min=0.0, y_max=SEAM
        ).val().Solids()
    ), "fallback added a disconnected solid"
