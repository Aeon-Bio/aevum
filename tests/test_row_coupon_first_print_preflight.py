from __future__ import annotations

from pathlib import Path

import pytest

from aevum_cad.params import load_params
from aevum_cad.row_coupon_first_print import bed_fit
from aevum_cad.row_coupon_first_print.models import (
    FirstPrintSlicerBedFitAudit,
    FirstPrintSlicerBedFitIssue,
)


ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "cad" / "one_row_coupon.params.json"


def _bed_audit(*, resolved: bool, message: str = "") -> FirstPrintSlicerBedFitAudit:
    return FirstPrintSlicerBedFitAudit(
        selected_setup_summary="test setup" if resolved else "",
        printer_profile="test printer" if resolved else "",
        bed_shape_source="test profile" if resolved else "",
        bed_x_mm=250.0 if resolved else 0.0,
        bed_y_mm=210.0 if resolved else 0.0,
        oversized_parts=(),
        issues=(
            ()
            if resolved
            else (
                FirstPrintSlicerBedFitIssue(
                    field="bed_shape",
                    message=message or "selected printer bed shape could not be resolved",
                ),
            )
        ),
    )


@pytest.mark.parametrize(
    "authority_problem",
    (
        "setup worksheet is absent",
        "selected setup record is stale",
        "selected profile bed_shape is malformed",
    ),
)
def test_unresolved_bed_authority_stops_before_piece_realization(
    monkeypatch: pytest.MonkeyPatch,
    authority_problem: str,
) -> None:
    params = load_params(PARAMS)
    monkeypatch.setattr(
        bed_fit,
        "audit_first_print_slicer_bed_fit",
        lambda **_: _bed_audit(resolved=False, message=authority_problem),
    )

    def forbidden_realization(*args: object, **kwargs: object) -> object:
        raise AssertionError("geometry realization crossed unresolved input authority")

    monkeypatch.setattr(
        bed_fit,
        "realize_row_coupon_final_print_pieces",
        forbidden_realization,
    )
    monkeypatch.setattr(
        bed_fit,
        "row_coupon_final_print_piece_plan",
        forbidden_realization,
    )

    rows = bed_fit.first_print_final_piece_artifact_rows(
        params=params,
        piece_dir="unused",
        slicer_setup_path="unresolved.csv",
        out_dir="unused",
    )
    audit = bed_fit.audit_first_print_final_piece_artifacts(
        params=params,
        piece_dir="unused",
        slicer_setup_path="unresolved.csv",
        out_dir="unused",
    )

    assert rows == ()
    assert not audit.final_piece_artifacts_ready
    assert audit.expected_row_count == 0
    assert [(issue.field, issue.message) for issue in audit.issues] == [
        ("bed_shape", "selected printer bed shape could not be resolved")
    ]


def test_resolved_bed_preserves_geometry_failure_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    params = load_params(PARAMS)
    monkeypatch.setattr(
        bed_fit,
        "audit_first_print_slicer_bed_fit",
        lambda **_: _bed_audit(resolved=True),
    )

    def broken_geometry(*args: object, **kwargs: object) -> object:
        raise ValueError("deliberate geometry failure")

    monkeypatch.setattr(
        bed_fit,
        "realize_row_coupon_final_print_pieces",
        broken_geometry,
    )

    with pytest.raises(ValueError, match="deliberate geometry failure"):
        bed_fit.first_print_final_piece_artifact_rows(
            params=params,
            piece_dir="unused",
            slicer_setup_path="valid.csv",
            out_dir="unused",
        )
