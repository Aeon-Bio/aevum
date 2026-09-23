from __future__ import annotations

import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path

import pytest

from aevum_cad.params import load_params
from aevum_cad.row_coupon.artifacts import (
    row_coupon_physical_artifact_manifest,
    row_coupon_physical_artifact_specs,
)
from aevum_cad.row_coupon.assembly import (
    build_row_coupon_realized_installed_parts,
    measure_row_coupon_realized_installed_pair_intersections,
)
from aevum_cad.row_coupon.final_print_pieces import (
    group_row_coupon_final_print_pieces_by_installed_part,
    realize_row_coupon_final_print_pieces,
)
from aevum_cad.row_coupon.manifest import row_coupon_part_manifest

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
AUTHORITY = ROOT / "docs" / "assembly" / "artifact_authority.json"


@pytest.fixture(scope="module")
def params() -> dict:
    return load_params(PARAMS)


@pytest.fixture(scope="module")
def installed_realization(params: dict):
    return realize_row_coupon_final_print_pieces(params, assembly_position=True)


def test_all_final_release_bodies_retain_exact_installed_authority(
    params: dict,
    installed_realization,
) -> None:
    realization = installed_realization
    authority = json.loads(AUTHORITY.read_text())
    rigid_authority = {
        row["release_body_id"]: row["source_artifact_id"]
        for row in authority["release_bodies"]
        if row["body_class"] == "rigid_print_piece"
    }
    specs = {spec.name: spec for spec in row_coupon_physical_artifact_specs(params)}
    manifest = row_coupon_physical_artifact_manifest(params)
    plan_by_name = {row["name"]: row for row in realization.plan}

    assert realization.assembly_position is True
    assert set(plan_by_name) == set(realization.pieces) == set(rigid_authority)
    assert len(realization.plan) == len(realization.pieces) == len(rigid_authority)

    # Release BODY and source ARTIFACT are different categories: an artifact that
    # fits the bed releases one body, a structurally split one releases two.  The
    # literal action totals here (19/16) and source total (27) were pre-split
    # bookkeeping and went stale when the latch-station pattern changed from 9 to
    # 12 wedge locks.  artifact_authority.json is the independently maintained
    # release register, so deriving the fan-out from it is the real cross-check:
    # every release body traces to exactly one source artifact, and every source
    # appears either once (identity) or twice (structural split).
    bodies_per_source = Counter(rigid_authority.values())
    assert set(bodies_per_source.values()) == {1, 2}
    assert Counter(row["action"] for row in realization.plan) == {
        "identity": sum(1 for count in bodies_per_source.values() if count == 1),
        "structural_split": 2
        * sum(1 for count in bodies_per_source.values() if count == 2),
    }
    assert {row["source_artifact"] for row in realization.plan} == {
        source
        for source, entry in manifest.items()
        if entry["fabrication_source"] == "printed_polymer"
    }
    assert len({row["source_artifact"] for row in realization.plan}) == len(
        bodies_per_source
    )
    for release_body_id, source in rigid_authority.items():
        row = plan_by_name[release_body_id]
        assert row["source_artifact"] == source
        assert row["installed_part"] == specs[source].installed_part
        assert len(realization.pieces[release_body_id].val().Solids()) == 1


def test_realized_release_bodies_group_into_twelve_printed_families(
    params: dict,
) -> None:
    grouped = group_row_coupon_final_print_pieces_by_installed_part(
        params,
        assembly_position=True,
    )
    installed_manifest = row_coupon_part_manifest()["installed"]
    expected_printed = {
        name
        for name, entry in installed_manifest.items()
        if entry["fabrication_source"] == "printed_polymer"
    }
    assert len(grouped) == len(expected_printed) == 12
    assert set(grouped) == expected_printed
    assert all(model.val().Volume() > 0.0 for model in grouped.values())

    full = build_row_coupon_realized_installed_parts(params)
    assert list(full) == list(installed_manifest)
    assert len(full) == 28
    assert set(full) - set(grouped) == set(installed_manifest) - expected_printed
    for name in grouped:
        assert full[name].val().Volume() == pytest.approx(grouped[name].val().Volume())


def test_all_378_pairs_are_measured_on_realized_installed_geometry(
    params: dict,
) -> None:
    installed_names = sorted(row_coupon_part_manifest()["installed"])
    expected_keys = {
        "::".join((left, right))
        for left, right in combinations(installed_names, 2)
    }
    volumes = measure_row_coupon_realized_installed_pair_intersections(params)

    assert len(expected_keys) == len(volumes) == 378
    assert set(volumes) == expected_keys
    assert all(math.isfinite(volume) and volume >= 0.0 for volume in volumes.values())
    assert volumes["lid_cover::lid_manifold_shell"] == pytest.approx(0.0, abs=1e-4)
