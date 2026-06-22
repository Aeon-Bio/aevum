"""Contract fence for the foundation layer (params/labware/fixture_model).

These three modules are NOT moved during the modularization: ``params.ROOT =
Path(__file__).resolve().parents[2]`` is depth-sensitive and imported by 58
files, so relocating the file would silently break ``ROOT`` (and
``DEFAULT_PARAMS`` derived from it) for the whole repo. This test pins the
import-time contract those modules owe their importers so any accidental move
or namespace regression fails fast (seconds), not in the slow geometry suite.

Additive regression armor only — it must not modify any assertion in
``tests/test_params_and_labware.py``.
"""

from __future__ import annotations

from pathlib import Path

import aevum_cad.params as params_module
from aevum_cad.fixture_model import (
    _fixture_layout,
    _plate_cap_bounds,
    build_fixture,
    build_fixture_assembly,
    build_mat_cassette,
    build_plate_cap,
    export_fixture,
)
from aevum_cad.labware import build_labware_definition, export_labware
from aevum_cad.params import (
    DEFAULT_PARAMS,
    ROOT,
    load_params,
    well_center,
    well_name,
)


def test_root_resolves_to_repo_root() -> None:
    # Path-independent proof: ROOT is the repo root iff it directly contains
    # pyproject.toml. This catches a silent parents[N] depth drift that a unit
    # test asserting only numeric geometry would miss.
    assert isinstance(ROOT, Path)
    assert ROOT.is_dir()
    assert (ROOT / "pyproject.toml").exists(), ROOT
    assert params_module.ROOT == ROOT


def test_default_params_resolves_under_root() -> None:
    assert DEFAULT_PARAMS == ROOT / "cad" / "p300_poc_fixture.params.json"
    assert DEFAULT_PARAMS.exists(), DEFAULT_PARAMS


def test_load_params_reads_default_and_cad_coupon() -> None:
    # The default serves the OT2 subsystem; the CAD suite loads one_row_coupon
    # explicitly. Both must load through the same loader.
    default_params = load_params()
    assert isinstance(default_params, dict)
    assert "mock_wells" in default_params

    coupon_path = ROOT / "cad" / "one_row_coupon.params.json"
    assert coupon_path.exists(), coupon_path
    coupon_params = load_params(coupon_path)
    assert isinstance(coupon_params, dict)


def test_public_callables_are_callable() -> None:
    for fn in (
        load_params,
        well_name,
        well_center,
        build_labware_definition,
        export_labware,
        build_fixture,
        build_plate_cap,
        build_mat_cassette,
        build_fixture_assembly,
        export_fixture,
    ):
        assert callable(fn), fn


def test_test_touched_private_helpers_stay_importable() -> None:
    # tests/test_params_and_labware.py imports these private names directly;
    # no __all__ may hide them.
    assert callable(_fixture_layout)
    assert callable(_plate_cap_bounds)


def test_well_name_and_center_behaviour() -> None:
    assert well_name(0, 0) == "A1"
    params = load_params()
    x_a1, y_a1 = well_center(params, 0, 0)
    x_a2, _y_a2 = well_center(params, 0, 1)
    assert x_a2 - x_a1 == params["mock_wells"]["pitch"]
