from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aevum_cad.params import ROOT, load_params
from aevum_ot2.core.evidence_primitives import _sha256_file
from aevum_ot2.core.models import FixtureIdentity

DEFAULT_LABWARE = ROOT / "outputs" / "labware" / "aevum_p300_poc_fixture.json"


def sha256_file(path: str | Path) -> str:
    """Public file-SHA-256 (accepts str|Path); delegates to the canonical hasher."""
    return _sha256_file(Path(path))


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open() as f:
        return json.load(f)


def current_fixture_identity(
    *,
    params_path: str | Path | None = None,
    labware_path: str | Path = DEFAULT_LABWARE,
) -> FixtureIdentity:
    params_file = (
        Path(params_path)
        if params_path is not None
        else ROOT / "cad" / "p300_poc_fixture.params.json"
    )
    labware_file = Path(labware_path)
    params = load_params(params_file)
    labware = load_json(labware_file)

    nominal = {
        "x": float(params["base"]["length_x"]),
        "y": float(params["base"]["width_y"]),
        "z": float(
            params["raised_stack"]["height_to_mock_plate_top"]
            + params["mat_plane"]["height_above_mock_plate_top"]
            + params["mat_plane"]["frame_thickness"]
        ),
    }
    labware_dimensions = {
        "x": float(labware["dimensions"]["xDimension"]),
        "y": float(labware["dimensions"]["yDimension"]),
        "z": float(labware["dimensions"]["zDimension"]),
    }

    meta = params["labware"]
    return FixtureIdentity(
        load_name=meta["load_name"],
        namespace=meta["namespace"],
        version=int(meta["version"]),
        params_path=str(params_file),
        labware_path=str(labware_file),
        params_sha256=sha256_file(params_file),
        labware_definition_sha256=sha256_file(labware_file),
        nominal_dimensions_mm=nominal,
        labware_dimensions_mm=labware_dimensions,
        dimensions_match=nominal == labware_dimensions,
    )
