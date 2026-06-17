from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PARAMS = ROOT / "cad" / "p300_poc_fixture.params.json"


def load_params(path: str | Path = DEFAULT_PARAMS) -> dict[str, Any]:
    with Path(path).open() as f:
        return json.load(f)


def well_name(row: int, column: int) -> str:
    return f"{chr(ord('A') + row)}{column + 1}"


def well_center(params: dict[str, Any], row: int, column: int) -> tuple[float, float]:
    wells = params["mock_wells"]
    x = wells["a1_center_x"] + column * wells["pitch"]
    y = wells["a1_center_y"] + row * wells["pitch"]
    return x, y

