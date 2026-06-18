"""OT-4 follow-up: per-well access geometry primitive (checksum-anchored)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aevum_ot2.core.artifacts import DEFAULT_LABWARE, sha256_file
from aevum_ot2.core.well_geometry import (
    WellAccessGeometry,
    descent_endpoint_within_bounds,
    load_well_access_geometry,
    well_access_geometry,
)

SHA = sha256_file(DEFAULT_LABWARE)


def test_a1_well_access_bounds_match_the_canonical_fixture() -> None:
    geo = load_well_access_geometry(
        labware_path=DEFAULT_LABWARE, expected_sha256=SHA, well_name="A1"
    )
    assert geo.well_bottom_deck_z_mm == pytest.approx(67.6)  # well z
    assert geo.well_top_deck_z_mm == pytest.approx(80.0)  # z + depth = 67.6 + 12.4
    assert geo.depth_mm == pytest.approx(12.4)


def test_loader_fails_closed_on_checksum_mismatch() -> None:
    # The integrity gate: a tampered/swapped definition is refused before any number is trusted.
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_well_access_geometry(
            labware_path=DEFAULT_LABWARE, expected_sha256="0" * 64, well_name="A1"
        )


def test_loader_requires_a_checksum() -> None:
    with pytest.raises(ValueError, match="checksum is required"):
        load_well_access_geometry(labware_path=DEFAULT_LABWARE, expected_sha256="", well_name="A1")


def test_loader_fails_closed_on_unknown_well() -> None:
    with pytest.raises(ValueError, match="no well"):
        load_well_access_geometry(
            labware_path=DEFAULT_LABWARE, expected_sha256=SHA, well_name="Z99"
        )


def test_loader_fails_closed_on_missing_file() -> None:
    # _sha256_file opens in binary, so a missing path raises FileNotFoundError (an OSError),
    # which the dispatch-path caller catches alongside ValueError -- never a silent pass.
    with pytest.raises(OSError):
        load_well_access_geometry(
            labware_path="/no/such/labware.json", expected_sha256=SHA, well_name="A1"
        )


def test_well_access_geometry_rejects_malformed_well() -> None:
    with pytest.raises(ValueError, match="missing numeric"):
        well_access_geometry({"wells": {"A1": {"z": 1.0}}}, "A1")  # no depth
    with pytest.raises(ValueError, match="negative depth"):
        well_access_geometry({"wells": {"A1": {"z": 1.0, "depth": -1.0}}}, "A1")


def test_descent_endpoint_within_bounds() -> None:
    geo = WellAccessGeometry(
        well_name="A1", well_top_deck_z_mm=80.0, well_bottom_deck_z_mm=67.6, depth_mm=12.4
    )
    assert descent_endpoint_within_bounds(geo, 80.0) is True  # at the rim
    assert descent_endpoint_within_bounds(geo, 67.6) is True  # at the floor
    assert descent_endpoint_within_bounds(geo, 73.0) is True  # inside the well
    assert descent_endpoint_within_bounds(geo, 80.1) is False  # above the rim (not descended)
    assert descent_endpoint_within_bounds(geo, 67.5) is False  # through the physical floor


def test_well_access_geometry_model_forbids_extra() -> None:
    with pytest.raises(ValidationError):
        WellAccessGeometry(
            well_name="A1",
            well_top_deck_z_mm=80.0,
            well_bottom_deck_z_mm=67.6,
            depth_mm=12.4,
            liquid_line_z_mm=72.0,  # extra='forbid' -- a dry floor is NOT a geometry field
        )
