# ruff: noqa: E402, F821, I001
"""Open this file in CQ-Editor to inspect the current P300 PoC fixture.

CQ-Editor provides ``show_object`` at runtime. Running this file from plain
Python is still useful as a smoke test; it will print model metadata instead of
opening a viewer.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aevum_cad.fixture_model import (  # noqa: E402
    build_fixture,
    build_fixture_assembly,
    build_mat_cassette,
    build_plate_cap,
)
from aevum_cad.params import load_params  # noqa: E402


DEFAULT_PARAMS = ROOT / "cad" / "p300_poc_fixture.params.json"


def _params_path(*values: str | Path | None) -> Path:
    for value in values:
        if value is None:
            continue
        candidate = Path(value)
        if candidate.suffix.lower() != ".json":
            continue
        if candidate.is_absolute():
            return candidate
        cwd_candidate = Path.cwd() / candidate
        if cwd_candidate.exists():
            return cwd_candidate
        return ROOT / candidate
    return DEFAULT_PARAMS


parser = argparse.ArgumentParser()
parser.add_argument(
    "params",
    nargs="?",
    default=None,
    help="Path to a fixture params JSON file.",
)
args, _unknown = parser.parse_known_args()

params = load_params(_params_path(args.params, *_unknown))
fixture = build_fixture(params)
plate_cap = build_plate_cap(params, assembly_position=True)
cassette = build_mat_cassette(params, assembly_position=True)
assembly = build_fixture_assembly(params)

try:
    show_object(  # type: ignore[name-defined] # noqa: F821
        fixture,
        name=f"{params['name']}_base",
        options={"alpha": 0.85, "color": (0.8, 0.82, 0.86)},
    )
    show_object(  # type: ignore[name-defined] # noqa: F821
        plate_cap,
        name=f"{params['name']}_plate_cap",
        options={"alpha": 0.75, "color": (0.35, 0.75, 0.45)},
    )
    show_object(  # type: ignore[name-defined] # noqa: F821
        cassette,
        name=f"{params['name']}_mat_cassette",
        options={"alpha": 0.65, "color": (0.25, 0.55, 0.95)},
    )
except NameError:
    print(params["name"])
    models = [
        ("base", fixture),
        ("plate cap installed", plate_cap),
        ("cassette installed", cassette),
        ("assembly", assembly),
    ]
    for label, model in models:
        if model is None:
            continue
        bb = model.val().BoundingBox()
        print(f"{label}: bounds x={bb.xlen:.2f} y={bb.ylen:.2f} z={bb.zlen:.2f} mm")
    print("Open this file in CQ-Editor to view it interactively.")
