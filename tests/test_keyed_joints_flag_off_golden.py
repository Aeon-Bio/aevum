"""G4 golden gate: with keyed_joints_enabled OFF (default), the CAD geometry must stay
byte-identical to the frozen baseline. This codifies the flag-off behavior-preservation
contract that the D1-D9 keyed-assembly features were verified against interactively, so a
future change cannot silently alter the default geometry. The baseline JSON is regenerated
ONLY on a reviewed, intentional diff.

Also asserts the master flag is actually wired (flag-ON changes geometry) so the gate
cannot pass by the feature being dead.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from aevum_cad.params import ROOT, load_params
import aevum_cad.row_coupon as m

GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "flag_off_geometry_baseline.json").read_text()
)


def _params():
    return load_params(ROOT / "cad" / "one_row_coupon.params.json")


def _sig(workplane):
    bb = workplane.val().BoundingBox()
    return [round(bb.xlen, 4), round(bb.ylen, 4), round(bb.zlen, 4), len(workplane.solids().vals())]


def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def test_flag_off_builder_signatures_match_golden():
    p = _params()
    assert not p.get("production_assembly", {}).get("keyed_joints_enabled", False), (
        "keyed_joints_enabled must default OFF in the shipped params"
    )
    mismatches = {}
    for name, expected in GOLDEN["builder_sigs"].items():
        got = _sig(getattr(m, name)(p))
        if got != expected:
            mismatches[name] = {"expected": expected, "got": got}
    assert not mismatches, f"flag-off geometry drifted from golden: {mismatches}"


def test_flag_off_y_split_matches_golden():
    p = _params()
    parts = m.build_row_coupon_production_y_split_parts(p)
    got = {k: [round(v.val().BoundingBox().ymax, 3), len(v.solids().vals())] for k, v in parts.items()}
    assert got == GOLDEN["y_split"], "flag-off y-split geometry drifted from golden"


def test_flag_off_layout_and_manifest_hashes_match_golden():
    p = _params()
    assert _hash(m.row_coupon_layout(p)) == GOLDEN["layout_hash"], "layout dict drifted"
    assert _hash(m.row_coupon_part_manifest()) == GOLDEN["manifest_hash"], "manifest drifted"


def test_keyed_flag_is_actually_wired():
    """Guard against the gate passing because the feature is dead: flag-ON must produce at
    least one keyed seam (some split part's lower segment protrudes past the flat split
    plane). Robust to WHICH parts attach a key — a bbox-centre key falls back to a butt
    seam on hollow frame/shell sections (only solid-seam parts key today; per-wall
    placement is deferred, G5a), so this asserts existence, not a specific part."""
    seam = 188.625  # split_y for the shipped one-row params
    p_on = copy.deepcopy(_params())
    p_on["production_assembly"]["keyed_joints_enabled"] = True
    on = m.build_row_coupon_production_y_split_parts(p_on)
    keyed = [
        k for k, v in on.items()
        if k.endswith("y01_of_02") and v.val().BoundingBox().ymax > seam + 0.5
    ]
    assert keyed, "keyed_joints_enabled produced no keyed seam — flag is not wired / feature inert"
