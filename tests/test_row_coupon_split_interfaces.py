from __future__ import annotations

import cadquery as cq
import pytest

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon.artifacts import (
    ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS,
    _lid_harness_cover_models,
    _remove_named_lid_harness_fragments,
    build_row_coupon_physical_artifacts,
    row_coupon_physical_artifact_manifest,
)
from aevum_cad.row_coupon.final_print_pieces import (
    _keyed_split_pair,
    _stepped_lap_split_pair,
    realize_row_coupon_final_print_pieces,
)

LOWER_SUFFIX = "piece_01_of_02_y_000p000_to_188p625"
UPPER_SUFFIX = "piece_02_of_02_y_188p625_to_377p250"


@pytest.fixture(scope="module")
def params() -> dict:
    return load_params(ROOT / "cad" / "one_row_coupon.params.json")


@pytest.fixture(scope="module")
def realization(params: dict):
    return realize_row_coupon_final_print_pieces(params)


def test_release_contract_preserves_exact_eight_sources_and_sixteen_halves(
    realization,
    params: dict,
) -> None:
    sources = set(ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS)
    expected = {
        f"{source}_{suffix}" for source in sources for suffix in (LOWER_SUFFIX, UPPER_SUFFIX)
    }
    split_rows = [row for row in realization.plan if row["action"] == "structural_split"]

    assert len(sources) == 8
    assert len(split_rows) == 16
    assert {row["name"] for row in split_rows} == expected
    assert {row["source_artifact"] for row in split_rows} == sources
    assert {(row["piece_index"], row["piece_count"]) for row in split_rows} == {
        (1, 2),
        (2, 2),
    }
    assert len(realization.plan) == len(realization.pieces) == 38

    manifest = row_coupon_physical_artifact_manifest(params)
    flexible = [
        name for name, entry in manifest.items() if entry["fabrication_source"] != "printed_polymer"
    ]
    assert len(flexible) == 8
    assert len(realization.pieces) + len(flexible) == 46


def test_canonical_sources_and_realized_halves_are_connected(
    realization,
    params: dict,
) -> None:
    sources = build_row_coupon_physical_artifacts(params)
    for source in ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS:
        assert len(sources[source].val().Solids()) == 1, source

    for row in realization.plan:
        if row["action"] != "structural_split":
            continue
        assert len(realization.pieces[row["name"]].val().Solids()) == 1, row["name"]
        assert row["diagnostics"] == ()
        assert row["fits_selected_bed"] is True


def test_every_split_is_retained_clear_and_reconstructable(realization) -> None:
    first_rows = {
        row["source_artifact"]: row
        for row in realization.plan
        if row["action"] == "structural_split" and row["piece_index"] == 1
    }
    assert set(first_rows) == set(ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS)

    for source, row in first_rows.items():
        seam = row["seam"]
        assert seam["mating_feature_kind"] != "plain_butt_fallback", source
        assert seam["fallback_reason"] is None
        assert seam["realized_key_count"] > 0
        assert seam["fit_class_clearance_mm"] > 0
        assert seam["pair_interference_volume_mm3"] == pytest.approx(0.0, abs=1e-4)
        assert seam["source_excess_volume_mm3"] == pytest.approx(0.0, abs=1e-4)
        assert seam["source_missing_volume_mm3"] <= (seam["pocket_removed_volume_mm3"] + 1e-4)
        assert seam["source_excess_volume_mm3"] <= (
            seam["boss_added_volume_mm3"] + seam.get("witness_added_volume_mm3", 0.0) + 1e-4
        )
        assert seam["functional_exclusions"]
        assert seam["functional_exclusions_enforced_by"] == (
            "source_intersection_and_canonical_allowlist"
        )
        assert "Gate 2 dry-fit evidence required" in seam["retention_authority"]

        assert row["range_semantics"] == "stable_nominal_identity_only"
        assert row["nominal_id_range_max_mm"] == pytest.approx(188.625)
        assert row["geometric_y_max_mm"] >= seam["geometric_split_y_mm"]


def test_wet_and_lid_seams_are_relocated_away_from_nominal_latch_plane(
    realization,
) -> None:
    split_y = {
        row["source_artifact"]: row["seam"]["geometric_split_y_mm"]
        for row in realization.plan
        if row["action"] == "structural_split" and row["piece_index"] == 1
    }
    assert split_y["wet_chamber_frame"] == pytest.approx(198.0)
    assert split_y["lid_manifold_shell"] == pytest.approx(198.0)
    assert split_y["lid_cover"] == pytest.approx(198.0)
    assert split_y["plate_support_frame"] == pytest.approx(188.625)


def test_exclusion_allowlist_and_independent_loss_caps_fail_closed(params: dict) -> None:
    sources = build_row_coupon_physical_artifacts(params)
    base = dict(params["production_assembly"]["final_piece_interface"])
    overrides = base.pop("source_overrides")

    plate_interface = {**base, **overrides["plate_support_frame"]}
    plate_interface["canonical_source_artifact"] = "plate_support_frame"
    plate_interface["functional_exclusions"] = ["invented_safe_zone"]
    with pytest.raises(ValueError, match="canonical allowlist"):
        _keyed_split_pair(
            sources["plate_support_frame"],
            source_y_min=0.0,
            source_y_max=377.25,
            split_y=188.625,
            interface=plate_interface,
        )

    wet_interface = {**base, **overrides["wet_chamber_frame"]}
    wet_interface["canonical_source_artifact"] = "wet_chamber_frame"
    wet_interface["lap_length_y_mm"] = 100.0
    with pytest.raises(ValueError, match="missing-material limit"):
        _stepped_lap_split_pair(
            sources["wet_chamber_frame"],
            source_y_min=0.0,
            source_y_max=377.25,
            split_y=198.0,
            interface=wet_interface,
        )


def test_named_harness_fragment_cleanup_rejects_wrong_z() -> None:
    retained = cq.Workplane("XY").box(10.0, 10.0, 1.0)
    impostor = (
        cq.Workplane("XY")
        .box(0.5, 4.2, 0.7, centered=(False, False, False))
        .translate((8.0, 57.9, 100.0))
    )
    candidate = cq.Workplane(
        obj=cq.Compound.makeCompound([retained.val(), impostor.val()])
    )
    with pytest.raises(ValueError, match="unknown small solid"):
        _remove_named_lid_harness_fragments(
            candidate,
            trunk_name="lid_cover_left_gas_bus",
            assembly_position=False,
        )


def test_harness_fragment_contract_holds_in_print_and_installed_coordinates(
    params: dict,
) -> None:
    for assembly_position in (False, True):
        covers = _lid_harness_cover_models(
            params,
            assembly_position=assembly_position,
        )
        assert len(covers) == 3
        assert all(len(cover.val().Solids()) == 1 for cover in covers.values())
