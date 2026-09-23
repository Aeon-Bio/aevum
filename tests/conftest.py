"""Session-scoped memoisation of the deterministic CAD builders.

WHY THIS EXISTS
---------------
The row-coupon geometry is a pure function of one JSON parameter file, but the
suite rebuilt it from scratch in every test. Measured cost of a single build:

    load_params                           0.000 s
    row_coupon_layout                     0.002 s   <- free, never the problem
    build_row_coupon_validation_parts    14.0   s
    build_row_coupon_physical_artifacts  72.6   s
    build_row_coupon_installed_parts     78.5   s

Across tests/ those builders are called 45 / 8 / 36 times respectively, almost
always on the SAME unmodified parameter file. The full suite ran ~27 CPU-hours.

SAFETY BOUNDARY
---------------
Several tests deliberately mutate the params dict to build red / negative-control
cases (an oversized head, a zeroed service inset). Caching must never hand one of
those a result built from different inputs. So the key is a SHA-256 of the
canonical JSON of the params dict -- content, not identity. A mutated params dict
hashes differently and misses the cache, which is exactly the required behaviour.

Two further guards:
  * Any call with extra args/kwargs bypasses the cache entirely, so alternate call
    shapes can never collide with the default one.
  * Dict results are returned as a shallow copy, so a test that assigns into the
    returned mapping cannot corrupt the cached original. The CadQuery values are
    shared, which is safe because Workplane operations return new objects rather
    than mutating in place.

This is test-only. Production builders are untouched.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from typing import Any

import pytest

import aevum_cad.row_coupon.artifacts as _artifacts
import aevum_cad.row_coupon.assembly as _assembly
import aevum_cad.row_coupon.final_print_pieces as _fpp

_CACHE: dict[tuple[str, str], Any] = {}
_CACHE_MAX = 12  # bounded: a realisation holds every rigid body, and xdist runs N workers

# The two B-rep roots. Everything expensive funnels through these, so memoising
# here covers every public wrapper without patching each one. Measured cost of a
# single cold call:
#     _realize_row_coupon_final_print_pieces   ~145 s
#     build_row_coupon_physical_artifacts       ~73 s
# `row_coupon_final_print_piece_plan` returns only metadata but realises the full
# geometry to do it (deliberately -- final_print_pieces.py keeps plan and bodies
# together so metadata cannot drift from bodies). That is why the 142-test,
# zero-fixture, zero-cadquery-import test_row_coupon_first_print.py is the most
# expensive file in the suite: it looks like a contract file and is not.
# The two assembly roots below were measured as the most expensive builders in
# the suite by the profile at the top of this file, yet were not memoised: 40
# call sites for build_row_coupon_installed_parts and 47 for
# build_row_coupon_validation_parts, 83 of which are in test_row_coupon_cad.py
# alone. Both take `params` as their only argument, so they use the same
# content-hash keying and the same safety boundary as the roots above.
_ROOTS = (
    (_artifacts, "build_row_coupon_physical_artifacts"),
    (_fpp, "_realize_row_coupon_final_print_pieces"),
    (_assembly, "build_row_coupon_installed_parts"),
    (_assembly, "build_row_coupon_validation_parts"),
)


def _params_key(params: Any) -> str:
    return hashlib.sha256(
        json.dumps(params, sort_keys=True, default=str).encode()
    ).hexdigest()


def _memoise(module: Any, name: str) -> None:
    original = getattr(module, name, None)
    if original is None or getattr(original, "_aevum_memoised", False):
        return

    def wrapper(params, *args, **kwargs):
        # Extra arguments are part of the key when they are primitives -- the real
        # call sites pass `assembly_position=True` / `bed_x_mm=...`, and bypassing
        # on any kwarg left the two most expensive internal calls uncached.
        # Anything non-primitive cannot be keyed safely, so that call bypasses.
        extra = (*args, *sorted(kwargs.items()))
        if not all(
            isinstance(v, (str, int, float, bool, type(None)))
            for item in extra
            for v in (item if isinstance(item, tuple) else (item,))
        ):
            return original(params, *args, **kwargs)
        key = (name, _params_key(params), repr(extra))
        if key not in _CACHE:
            if len(_CACHE) >= _CACHE_MAX:
                _CACHE.pop(next(iter(_CACHE)))
            _CACHE[key] = original(params, *args, **kwargs)
        cached = _CACHE[key]
        return dict(cached) if isinstance(cached, dict) else cached

    wrapper._aevum_memoised = True  # type: ignore[attr-defined]
    wrapper.__name__ = original.__name__
    wrapper.__doc__ = original.__doc__

    # Rebind everywhere. Patching the defining module covers same-module callers;
    # the sweep below covers any module that did `from X import Y` before us.
    setattr(module, name, wrapper)
    for mod in list(sys.modules.values()):
        if mod is None or not getattr(mod, "__name__", "").startswith("aevum_"):
            continue
        if getattr(mod, name, None) is original:
            setattr(mod, name, wrapper)


for _module, _name in _ROOTS:
    _memoise(_module, _name)


# ---------------------------------------------------------------------------
# External artifact-count authority.
#
# docs/assembly/artifact_authority.json is a human-reviewed registry, separate
# from the CAD source tree, that records how many canonical sources exist and
# how they fan out into released bodies.  It is the ONLY genuinely independent
# check on those totals: every in-tree expression for them (layout lengths,
# policy Counters, len(plan), len(expected_production_artifacts)) is derived
# from the same generator as the thing under test, so comparing one to another
# restates the constructor's own loop and cannot fail.  Pin totals here.
#
#   canonical_sources 38 = rigid_sources 30 + compliant_sources 8
#   release_bodies    46 = rigid_print_pieces 38 + compliant_bodies 8
#   (8 of the 30 rigid sources exceed the bed and split in two: 30 - 8 + 16 = 38)
#
# Changing a count here requires editing the registry, which is a reviewed act.
_AUTHORITY_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "docs" / "assembly" / "artifact_authority.json"
)


@pytest.fixture(scope="session")
def artifact_authority() -> dict[str, int]:
    counts = json.loads(_AUTHORITY_PATH.read_text())["counts"]
    # Internal consistency of the registry itself, so a half-edited registry
    # cannot quietly become the new expectation.
    assert counts["canonical_sources"] == counts["rigid_sources"] + counts["compliant_sources"]
    assert counts["release_bodies"] == counts["rigid_print_pieces"] + counts["compliant_bodies"]
    assert counts["compliant_bodies"] == counts["compliant_sources"]
    return counts
