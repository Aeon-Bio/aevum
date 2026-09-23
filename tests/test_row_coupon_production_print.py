from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import cadquery as cq
import pytest

import aevum_cad.row_coupon.artifacts as artifact_module
from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon import (
    ROW_COUPON_DISCRETE_UNSPLITTABLE_INSTALLED_PARTS,
    ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS,
    build_row_coupon_final_print_pieces,
    build_row_coupon_physical_artifacts,
    realize_row_coupon_final_print_pieces,
    row_coupon_physical_artifact_print_policies,
)
from aevum_cad.row_coupon.final_print_pieces import _piece_diagnostics
from aevum_cad.row_coupon_first_print import expected_production_artifacts

PARAMS = ROOT / "cad" / "one_row_coupon.params.json"


def _fits_selected_bed(target_x: float, target_y: float, bed_x: float, bed_y: float) -> bool:
    return (
        target_x <= bed_x
        and target_y <= bed_y
        or target_x <= bed_y
        and target_y <= bed_x
    )


def _bounds(shape: cq.Shape) -> tuple[float, ...]:
    bb = shape.BoundingBox()
    return (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)


def _assert_bounds_close(actual: cq.Shape, expected: cq.Shape, abs_tol: float = 0.05) -> None:
    assert _bounds(actual) == pytest.approx(_bounds(expected), abs=abs_tol)


def _geometry_signature(model: cq.Workplane) -> tuple[float | int, ...]:
    value = model.val()
    center = value.Center()
    return (
        round(float(value.Volume()), 6),
        *(round(bound, 6) for bound in _bounds(value)),
        round(float(center.x), 6),
        round(float(center.y), 6),
        round(float(center.z), 6),
        len(value.Solids()),
        len(value.Faces()),
        len(value.Edges()),
        len(value.Vertices()),
    )


@pytest.fixture(scope="module")
def default_realization():
    params = load_params(PARAMS)
    realization = realize_row_coupon_final_print_pieces(params)
    realization.require_printable()
    return realization


def test_default_final_print_piece_plan_is_rigid_canonical_queue(
    default_realization,
    tmp_path: Path,
    artifact_authority: dict[str, int],
) -> None:
    params = load_params(PARAMS)
    policies = row_coupon_physical_artifact_print_policies(
        params,
        bed_x_mm=250.0,
        bed_y_mm=210.0,
        fits_rectangular_bed=_fits_selected_bed,
    )
    realization = default_realization
    plan = realization.plan
    pieces = realization.pieces

    # Body and piece are different categories now: an artifact that fits the bed
    # releases one piece, an allowlisted structural artifact releases two.  The
    # literal totals this replaces (19/8/8 and 19/16) went stale when the latch
    # station pattern changed from 9 to 12, because the wedge-lock artifact count
    # is derived from the layout.  Tie the plan to the policy table instead: that
    # is the relation the split scheme must preserve, and it survives the next
    # layout change.
    policy_counts = Counter(policy.policy for policy in policies)
    assert set(policy_counts) == {
        "bed_fit_identity",
        "structural_split_allowed",
        "nonprinted_or_flexible",
    }
    assert policy_counts["structural_split_allowed"] == len(
        ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS
    )
    assert Counter(row["action"] for row in plan) == {
        "identity": policy_counts["bed_fit_identity"],
        "structural_split": 2 * policy_counts["structural_split_allowed"],
    }
    assert len(plan) == len(pieces) == (
        policy_counts["bed_fit_identity"] + 2 * policy_counts["structural_split_allowed"]
    )
    # Everything above is derived from the same realization the plan came from,
    # so it restates the constructor's loop.  These four totals come from the
    # external registry and are the only assertions here that a silent change in
    # artifact cardinality actually trips.
    assert policy_counts["bed_fit_identity"] + policy_counts["structural_split_allowed"] == (
        artifact_authority["rigid_sources"]
    )
    assert policy_counts["nonprinted_or_flexible"] == artifact_authority["compliant_sources"]
    assert policy_counts["structural_split_allowed"] == (
        artifact_authority["rigid_print_pieces"] - artifact_authority["rigid_sources"]
    )
    assert len(pieces) == artifact_authority["rigid_print_pieces"]
    # ... and the released-artifact total, cross-checked against the production
    # package, which derives its own list by a different route.
    # NB: len(expected_production_artifacts) is len(plan) + n(nonprinted) by
    # construction, so this pair only checks the package agrees with the plan.
    # The registry total is what makes it a real count check.
    assert len(pieces) + policy_counts["nonprinted_or_flexible"] == len(
        expected_production_artifacts(params, tmp_path)
    )
    assert len(pieces) + policy_counts["nonprinted_or_flexible"] == (
        artifact_authority["release_bodies"]
    )

    names = [row["name"] for row in plan]
    assert names == list(pieces)
    assert len(names) == len(set(names))
    assert all(row["diagnostics"] == () for row in plan)
    assert all(row["fits_selected_bed"] is True for row in plan)
    assert all(row["selected_bed_x_mm"] == 250.0 for row in plan)
    assert all(row["selected_bed_y_mm"] == 210.0 for row in plan)
    assert all(
        row["provenance"] == f"canonical physical artifact: {row['source_artifact']}"
        for row in plan
    )

    for name, piece in pieces.items():
        value = piece.val()
        assert len(value.Solids()) == 1, name
        assert value.Volume() > 0.0, name

    split_sources = {row["source_artifact"] for row in plan if row["action"] == "structural_split"}
    assert split_sources == {
        "plate_support_frame",
        "lower_harness_cover",
        "wet_chamber_frame",
        "lid_manifold_shell",
        "lid_harness_cover_lid_cover_left_gas_bus",
        "lid_harness_cover_lid_cover_right_gas_bus",
        "lid_harness_cover_lid_shell_right_sht41_bus",
        "lid_cover",
    }
    assert all(
        sum(1 for row in plan if row["source_artifact"] == source) == 2
        for source in split_sources
    )
    assert not {
        policy.name
        for policy in policies
        if policy.policy == "nonprinted_or_flexible"
    } & set(names)


def test_final_print_pieces_preserve_or_reconstruct_source_geometry(
    default_realization,
) -> None:
    params = load_params(PARAMS)
    realization = default_realization
    plan = realization.plan
    pieces = realization.pieces
    sources = build_row_coupon_physical_artifacts(params)

    rows_by_source: dict[str, list[dict]] = defaultdict(list)
    for row in plan:
        rows_by_source[row["source_artifact"]].append(row)

    for source, rows in rows_by_source.items():
        source_value = sources[source].val()
        if len(rows) == 1:
            piece_value = pieces[rows[0]["name"]].val()
            _assert_bounds_close(piece_value, source_value)
            assert piece_value.Volume() == pytest.approx(source_value.Volume(), rel=0.001)
            continue

        rebuilt = pieces[rows[0]["name"]]
        for row in rows[1:]:
            rebuilt = rebuilt.union(pieces[row["name"]])
        rebuilt_value = rebuilt.val()
        seam = rows[0]["seam"]
        pair_overlap = pieces[rows[0]["name"]].intersect(
            pieces[rows[1]["name"]]
        ).val().Volume()
        source_overlap = source_value.intersect(rebuilt_value).Volume()
        source_missing = source_value.Volume() - source_overlap
        source_excess = rebuilt_value.Volume() - source_overlap
        assert pair_overlap == pytest.approx(
            seam["pair_interference_volume_mm3"], abs=1e-4
        )
        assert pair_overlap == pytest.approx(0.0, abs=1e-4)
        assert source_missing == pytest.approx(
            seam["source_missing_volume_mm3"], abs=0.01
        )
        assert source_excess == pytest.approx(
            seam["source_excess_volume_mm3"], abs=0.01
        )
        assert source_missing <= seam["pocket_removed_volume_mm3"] + 0.01
        assert source_excess <= (
            seam["boss_added_volume_mm3"]
            + seam["witness_added_volume_mm3"]
            + 0.01
        )
        source_bounds = _bounds(source_value)
        rebuilt_bounds = _bounds(rebuilt_value)
        assert rebuilt_bounds[:5] == pytest.approx(source_bounds[:5], abs=0.05)
        assert rebuilt_bounds[5] == pytest.approx(
            source_bounds[5] + seam["witness_protrusion_mm"],
            abs=0.05,
        )
        assert rebuilt_value.Volume() - source_value.Volume() == pytest.approx(
            seam["reconstruction_volume_delta_mm3"],
            abs=0.01,
        )


def test_final_print_realization_is_deterministic(default_realization) -> None:
    params = load_params(PARAMS)
    repeated = realize_row_coupon_final_print_pieces(params)
    repeated.require_printable()

    assert repeated.plan == default_realization.plan
    assert tuple(repeated.pieces) == tuple(default_realization.pieces)
    assert {
        name: _geometry_signature(model)
        for name, model in repeated.pieces.items()
    } == {
        name: _geometry_signature(model)
        for name, model in default_realization.pieces.items()
    }


def test_selected_bed_fit_uses_raw_geometry_before_display_rounding(
    monkeypatch,
) -> None:
    exact = cq.Workplane("XY").box(100.0, 210.0, 1.0, centered=(False, False, False))
    oversize = cq.Workplane("XY").box(
        100.0,
        210.004,
        1.0,
        centered=(False, False, False),
    )

    assert _piece_diagnostics(
        name="exact",
        model=exact,
        bed_x_mm=210.0,
        bed_y_mm=100.0,
    ) == ()
    assert "piece does not fit selected bed" in _piece_diagnostics(
        name="oversize",
        model=oversize,
        bed_x_mm=210.0,
        bed_y_mm=100.0,
    )[0]

    spec = artifact_module.RowCouponPhysicalArtifactSpec("boundary", "deck_pods")
    monkeypatch.setattr(
        artifact_module,
        "row_coupon_physical_artifact_specs",
        lambda _params: (spec,),
    )
    monkeypatch.setattr(
        artifact_module,
        "row_coupon_physical_artifact_manifest",
        lambda _params: {
            "boundary": {
                "fabrication_source": "printed_polymer",
                "installed_part": "deck_pods",
            }
        },
    )
    monkeypatch.setattr(
        artifact_module,
        "build_row_coupon_physical_artifacts",
        lambda _params: {"boundary": oversize},
    )
    fit_inputs = []

    def _capture_fit(target_x, target_y, bed_x, bed_y):
        fit_inputs.append((target_x, target_y, bed_x, bed_y))
        return _fits_selected_bed(target_x, target_y, bed_x, bed_y)

    policy = artifact_module.row_coupon_physical_artifact_print_policies(
        {},
        bed_x_mm=210.0,
        bed_y_mm=100.0,
        fits_rectangular_bed=_capture_fit,
    )[0]
    assert fit_inputs == [(100.0, pytest.approx(210.004), 210.0, 100.0)]
    assert policy.target_y_mm == 210.0  # display-only rounding
    assert policy.policy == "discrete_unsplittable"


def test_every_discrete_artifact_is_whole_when_fit_and_blocked_when_oversized(
    default_realization,
) -> None:
    params = load_params(PARAMS)
    sources = build_row_coupon_physical_artifacts(params)
    tiny = realize_row_coupon_final_print_pieces(params, bed_x_mm=30.0, bed_y_mm=30.0)
    tiny_policies = row_coupon_physical_artifact_print_policies(
        params,
        bed_x_mm=30.0,
        bed_y_mm=30.0,
        fits_rectangular_bed=_fits_selected_bed,
    )
    tiny_rows = {row["source_artifact"]: row for row in tiny.plan}
    default_rows = {row["source_artifact"]: row for row in default_realization.plan}
    discrete = [
        policy
        for policy in tiny_policies
        if policy.installed_part in ROW_COUPON_DISCRETE_UNSPLITTABLE_INSTALLED_PARTS
    ]
    assert {policy.installed_part for policy in discrete} == set(
        ROW_COUPON_DISCRETE_UNSPLITTABLE_INSTALLED_PARTS
    )

    for policy in discrete:
        default_row = default_rows[policy.name]
        default_piece = default_realization.pieces[policy.name]
        assert default_row["action"] == "identity"
        assert _geometry_signature(default_piece) == _geometry_signature(
            sources[policy.name]
        )

        tiny_row = tiny_rows[policy.name]
        if policy.policy == "bed_fit_identity":
            assert tiny_row["action"] == "identity"
            assert policy.name in tiny.pieces
            assert _geometry_signature(tiny.pieces[policy.name]) == _geometry_signature(
                sources[policy.name]
            )
        else:
            assert policy.policy == "discrete_unsplittable"
            assert tiny_row["action"] == "blocked"
            assert policy.name not in tiny.pieces
            assert "discrete/removable printed artifact must stay whole" in tiny_row[
                "diagnostics"
            ]

    with pytest.raises(
        ValueError,
        match="final print-piece blocked for .*discrete/removable printed artifact must stay whole",
    ):
        build_row_coupon_final_print_pieces(params, bed_x_mm=30.0, bed_y_mm=30.0)
