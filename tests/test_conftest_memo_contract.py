"""Guard the test-suite memo in tests/conftest.py.

The memo makes the CAD suite tractable, but it introduces one serious failure
mode: if a deliberately-mutated params dict (a red / negative-control case) were
served a result built from DIFFERENT inputs, the control would silently compare a
cached object against itself and the test would become vacuous.

These tests exercise the memo's keying logic directly against a cheap stand-in,
so they run in milliseconds instead of rebuilding real B-rep geometry.
"""
from __future__ import annotations

import copy

import conftest


def _fresh_probe():
    calls = {"n": 0}

    class Mod:
        pass

    mod = Mod()

    def build(params, *, assembly_position: bool = False):
        calls["n"] += 1
        return {"n": calls["n"], "pos": assembly_position}

    mod.build = build
    conftest._CACHE.clear()
    conftest._memoise(mod, "build")
    return mod, calls


def test_memo_hits_on_equal_content_not_identity() -> None:
    mod, calls = _fresh_probe()
    a = {"deck": {"inset": 3.0}}
    b = copy.deepcopy(a)  # equal content, different object
    mod.build(a)
    mod.build(b)
    assert calls["n"] == 1, "memo must be content-keyed, not identity-keyed"


def test_mutated_params_never_reuse_a_cached_build() -> None:
    mod, calls = _fresh_probe()
    base = {"deck": {"inset": 3.0}}
    red = copy.deepcopy(base)
    red["deck"]["inset"] = 0.0  # the real negative-control pattern
    mod.build(base)
    mod.build(red)
    assert calls["n"] == 2, "a mutated red case was wrongly served from cache"


def test_kwargs_are_part_of_the_key() -> None:
    # Regression: bypassing the cache on any kwarg left the two most expensive
    # internal calls (`assembly_position=True`) uncached, costing ~70 s each.
    mod, calls = _fresh_probe()
    p = {"deck": {"inset": 3.0}}
    mod.build(p)
    mod.build(p, assembly_position=True)
    assert calls["n"] == 2, "distinct kwargs must not collide"
    mod.build(p, assembly_position=True)
    assert calls["n"] == 2, "repeated identical kwargs must hit the cache"


def test_returned_dict_is_a_copy_so_callers_cannot_poison_the_cache() -> None:
    mod, _ = _fresh_probe()
    p = {"deck": {"inset": 3.0}}
    first = mod.build(p)
    first["injected"] = True
    assert "injected" not in mod.build(p), "caller mutation leaked into the cache"


def test_non_primitive_arguments_bypass_the_cache() -> None:
    mod, calls = _fresh_probe()
    p = {"deck": {"inset": 3.0}}
    mod.build(p, assembly_position=object())  # unkeyable
    mod.build(p, assembly_position=object())
    assert calls["n"] == 2, "unkeyable arguments must bypass, never collide"
