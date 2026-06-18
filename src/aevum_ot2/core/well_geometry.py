"""OT-4 follow-up: per-well vertical access geometry, checksum-anchored to the labware def.

The OT-4 review established that ``dry_z_floor_mm`` (the conservative collision-envelope TOP) is
the WRONG quantity for a per-well descent: the A1 well-top sits ~11 mm below it. This module
provides the RIGHT quantity -- the well's geometric access bounds in deck Z -- derived only from a
labware definition whose checksum matches the integrity anchor the safety profile already carries
(mirroring OT-1's committed-store re-fetch + checksum-verify: never trust a number whose source
file does not match its digest).

These are GEOMETRIC bounds (rim and floor), NOT a dry-descent floor. The safe dry depth -- the
liquid line somewhere within ``[well_bottom, well_top]`` -- is a measurement (B), so a low-Z descent
stays gated; this only makes the bound a real, checksummed object instead of a misused envelope top.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from aevum_ot2.core.evidence_primitives import _sha256_file


class WellAccessGeometry(BaseModel):
    """A single well's vertical access bounds in deck Z (mm)."""

    model_config = ConfigDict(extra="forbid")

    well_name: str
    # The rim: z + depth -- the highest interior point, where a descent enters the well.
    well_top_deck_z_mm: float
    # The floor: z -- the lowest physical point of the well.
    well_bottom_deck_z_mm: float
    depth_mm: float


def well_access_geometry(definition: dict[str, Any], well_name: str) -> WellAccessGeometry:
    """Derive a well's access bounds from an (already-trusted) labware definition.

    Fails closed (ValueError) on a missing well or non-numeric / negative geometry.
    """
    wells = definition.get("wells")
    if not isinstance(wells, dict) or well_name not in wells:
        raise ValueError(f"labware definition has no well {well_name!r}")
    well = wells[well_name]
    if not isinstance(well, dict):
        raise ValueError(f"well {well_name!r} is not an object")
    try:
        z = float(well["z"])
        depth = float(well["depth"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"well {well_name!r} is missing numeric z/depth: {exc}") from exc
    if depth < 0:
        raise ValueError(f"well {well_name!r} has negative depth {depth}")
    return WellAccessGeometry(
        well_name=well_name,
        well_top_deck_z_mm=z + depth,
        well_bottom_deck_z_mm=z,
        depth_mm=depth,
    )


def load_well_access_geometry(
    *,
    labware_path: str | Path,
    expected_sha256: str,
    well_name: str,
) -> WellAccessGeometry:
    """Re-read the labware definition from disk, VERIFY its checksum against the expected digest,
    then derive the per-well access bounds.

    Fails closed (ValueError / OSError) on a missing checksum, a missing/unreadable file, a
    checksum mismatch (a tampered or swapped definition), or malformed well geometry. The checksum
    gate is load-bearing: it is the only thing that lets a downstream gate trust the returned
    numbers, exactly as OT-1 re-verifies an external artifact before trusting its offset_mm.
    """
    if not expected_sha256:
        raise ValueError("a labware definition checksum is required to trust well geometry")
    path = Path(labware_path)
    actual = _sha256_file(path)
    if actual != expected_sha256:
        raise ValueError(
            f"labware definition checksum mismatch for {path}: "
            f"expected {expected_sha256}, got {actual}"
        )
    with path.open() as handle:
        definition = json.load(handle)
    return well_access_geometry(definition, well_name)


def descent_endpoint_within_bounds(
    geometry: WellAccessGeometry,
    endpoint_deck_z_mm: float,
) -> bool:
    """True iff a descent endpoint lies within ``[well_bottom, well_top]`` (inclusive).

    A NECESSARY geometric sanity bound (it catches an endpoint above the rim -- not actually
    descended -- or below the physical floor -- driven through the bottom), NOT a sufficient
    dry-safety check: the liquid line within the bounds is a separate measurement. The rim
    (``well_top``) is included: it is the conservative entry point a descent starts from, not a
    violation. Whoever grounds a real (sub-rim) endpoint owns choosing the safe dry depth within
    these bounds.
    """
    return geometry.well_bottom_deck_z_mm <= endpoint_deck_z_mm <= geometry.well_top_deck_z_mm
