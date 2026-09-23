from __future__ import annotations

from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon.artifacts import (
    ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS,
    row_coupon_physical_artifact_manifest,
)
from aevum_cad.row_coupon.print_audit import audit_row_coupon_print_artifacts
from aevum_cad.row_coupon_first_print import expected_production_artifacts


def test_integrated_print_artifact_audit_passes(
    tmp_path: Path,
    artifact_authority: dict[str, int],
) -> None:
    params = load_params(ROOT / "cad" / "one_row_coupon.params.json")
    summary = audit_row_coupon_print_artifacts(params)

    # Rigid BODY and print PIECE are no longer the same category: 8 of the 38
    # manifest bodies exceed the bed and each releases as 2 pieces, so the
    # released-artifact total is 38 - 8 + 16.  Pinning literal totals here went
    # stale the moment the latch-station pattern changed (9 -> 12 wedge locks),
    # so every count below is tied back to an independently derived source --
    # the artifact manifest, the structural-split allowlist, and the production
    # package's own artifact list -- instead of to a hand-typed number.
    manifest = row_coupon_physical_artifact_manifest(params)
    printed = {
        name
        for name, entry in manifest.items()
        if entry["fabrication_source"] == "printed_polymer"
    }

    assert summary["flexible_or_compressible"] == len(manifest) - len(printed)
    assert summary["structural_sources"] == len(ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS)
    assert ROW_COUPON_STRUCTURAL_SPLIT_ALLOWED_ARTIFACTS <= printed
    assert summary["whole_rigid_pieces"] == len(printed) - summary["structural_sources"]
    assert summary["structural_piece_bodies"] == 2 * summary["structural_sources"]
    assert summary["rigid_print_pieces"] == (
        summary["whole_rigid_pieces"] + summary["structural_piece_bodies"]
    )
    assert summary["physical_artifacts"] == (
        summary["rigid_print_pieces"] + summary["flexible_or_compressible"]
    )
    # Every assertion above is an arithmetic identity on summary's own fields or
    # on the manifest that produced them, so none of them can fail on a change
    # in artifact cardinality.  These four are pinned to the external registry,
    # which is the independent authority on the fan-out.
    assert len(manifest) == artifact_authority["canonical_sources"]
    assert len(printed) == artifact_authority["rigid_sources"]
    assert summary["rigid_print_pieces"] == artifact_authority["rigid_print_pieces"]
    assert summary["flexible_or_compressible"] == artifact_authority["compliant_sources"]
    assert summary["physical_artifacts"] == artifact_authority["release_bodies"]

    # The production package derives its artifact list from the same plan by a
    # different route, so it is the real cross-check on the body -> piece fan-out.
    production = expected_production_artifacts(params, tmp_path)
    assert summary["physical_artifacts"] == len(production)
    assert summary["piece_names"] == [
        artifact.name for artifact in production if artifact.category == "printed"
    ]
    assert len(summary["piece_names"]) == len(set(summary["piece_names"]))
    assert summary["rigid_print_pieces"] == len(summary["piece_names"])

    # Every piece traces back to exactly one manifest body, and every printed
    # manifest body is covered by at least one piece.
    covered = {name.split("_piece_")[0] for name in summary["piece_names"]}
    assert covered == printed
