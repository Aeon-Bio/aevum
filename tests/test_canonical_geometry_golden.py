"""Golden gate for the shipped canonical geometry and print-piece contract.

Regenerate the baseline only for a reviewed, intentional geometry change.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import aevum_cad.row_coupon as m
from aevum_cad.params import ROOT, load_params

GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "canonical_geometry_baseline.json").read_text()
)


def _params():
    return load_params(ROOT / "cad" / "one_row_coupon.params.json")


def _sig(workplane):
    bb = workplane.val().BoundingBox()
    return [round(bb.xlen, 4), round(bb.ylen, 4), round(bb.zlen, 4), len(workplane.solids().vals())]


def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def test_canonical_builder_signatures_match_golden():
    p = _params()
    mismatches = {}
    for name, expected in GOLDEN["builder_sigs"].items():
        got = _sig(getattr(m, name)(p))
        if got != expected:
            mismatches[name] = {"expected": expected, "got": got}
    assert not mismatches, f"canonical geometry drifted from golden: {mismatches}"


def test_final_piece_sources_are_canonical_artifacts():
    p = _params()
    canonical_artifacts = set(m.row_coupon_physical_artifact_manifest(p))
    plan = m.row_coupon_final_print_piece_plan(p)

    unknown_sources = sorted({row["source_part"] for row in plan} - canonical_artifacts)
    assert unknown_sources == []

    parts = m.build_row_coupon_final_print_pieces(p)
    assert set(parts) == {row["name"] for row in plan}


def test_canonical_layout_and_manifest_hashes_match_golden():
    p = _params()
    assert _hash(m.row_coupon_layout(p)) == GOLDEN["layout_hash"], "layout dict drifted"
    assert _hash(m.row_coupon_part_manifest()) == GOLDEN["manifest_hash"], "manifest drifted"
