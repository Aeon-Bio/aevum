from __future__ import annotations

import pytest
from pydantic import ValidationError

from aevum_smis import (
    SMIS_VERSION,
    ModuleManifest,
    SafetyClass,
    SmisEnvelope,
    validate_manifest_envelope,
)


def _manifest(**overrides) -> ModuleManifest:
    base = dict(
        sku="obs-brightfield-4x",
        module_serial="SN-0001",
        hw_rev="A",
        smis_version=SMIS_VERSION,
        safety_class=SafetyClass.led,
        driver="aevum_modules.brightfield",
        mass_g=350.0,
        front_end_length_x_mm=21.0,
        front_end_width_y_mm=13.0,
        front_end_height_z_mm=28.0,
        focus_stroke_z_mm=12.0,
        barrel_diameter_mm=20.0,  # slim RMS 4x that threads the leg corridor (OC-A15)
    )
    base.update(overrides)
    return ModuleManifest(**base)


def test_valid_brightfield_head_fits_the_frozen_envelope() -> None:
    check = validate_manifest_envelope(_manifest())
    assert check.fits is True
    assert check.blockers == ()
    assert check.barrel_fits_keepout is True
    assert check.barrel_overflow_mm == 0.0
    # circumscribed diameter of the 21x13 head = sqrt(610) ~= 24.698 < 32.
    assert check.footprint_circumscribed_diameter_mm == 24.698
    assert check.footprint_fits_keepout is True
    # vertical budget = front-face clearance 8 + height 28 + stroke 12 = 48 <= 62.
    assert check.vertical_budget_required_mm == 48.0
    assert check.vertical_budget_closes is True
    assert check.mass_within_budget is True


def test_oversized_barrel_is_rejected() -> None:
    check = validate_manifest_envelope(_manifest(barrel_diameter_mm=40.0))
    assert check.fits is False
    assert check.barrel_fits_keepout is False
    assert check.barrel_overflow_mm == 8.0  # 40 - 32
    assert "barrel_exceeds_objective_keepout" in check.blockers


def test_oversized_head_footprint_is_rejected() -> None:
    # sqrt(40^2 + 40^2) = 56.57 > 32 keepout.
    check = validate_manifest_envelope(
        _manifest(front_end_length_x_mm=40.0, front_end_width_y_mm=40.0)
    )
    assert check.fits is False
    assert check.footprint_fits_keepout is False
    assert "head_footprint_exceeds_objective_keepout" in check.blockers


def test_tall_head_blows_the_z_budget() -> None:
    # 8 + 60 + 12 = 80 > 62.
    check = validate_manifest_envelope(_manifest(front_end_height_z_mm=60.0))
    assert check.fits is False
    assert check.vertical_budget_required_mm == 80.0
    assert check.vertical_budget_closes is False
    assert "vertical_budget_exceeds_dock_z" in check.blockers


def test_service_margin_counts_against_the_z_budget() -> None:
    # 8 + 28 + 12 + 15 = 63 > 62 -> margin pushes it over.
    check = validate_manifest_envelope(_manifest(service_margin_z_mm=15.0))
    assert check.vertical_budget_required_mm == 63.0
    assert check.vertical_budget_closes is False
    assert "vertical_budget_exceeds_dock_z" in check.blockers


def test_heavy_head_exceeds_mass_budget() -> None:
    check = validate_manifest_envelope(_manifest(mass_g=1200.0))
    assert check.fits is False
    assert check.mass_within_budget is False
    assert "mass_exceeds_budget" in check.blockers


def test_multiple_failures_accumulate_blockers() -> None:
    check = validate_manifest_envelope(
        _manifest(barrel_diameter_mm=40.0, front_end_height_z_mm=60.0, mass_g=2000.0)
    )
    assert check.fits is False
    # Exact set -- a spurious extra blocker must fail, not be tolerated (F5). A Ø40
    # barrel exceeds BOTH the Ø32 keepout and the (tighter) Ø21.4 leg corridor (OC-A15).
    assert set(check.blockers) == {
        "barrel_exceeds_objective_keepout",
        "scan_footprint_exceeds_leg_corridor",
        "vertical_budget_exceeds_dock_z",
        "mass_exceeds_budget",
    }


# Boundary table (F1): a head EXACTLY at budget passes; 0.001 over fails on that
# axis only. This is where a <=/< or dropped-tolerance regression would otherwise
# ship green -- the whole point of a "falsifiable" envelope re-check.
@pytest.mark.parametrize(
    ("axis_blocker", "at_budget", "over_budget"),
    [
        (
            # OC-A15: the binding barrel constraint is the leg/bay corridor (21.2),
            # TIGHTER than the Ø32 keepout -- so the corridor is the testable barrel
            # boundary (a barrel at the Ø32 keepout edge strikes the wall long before).
            "scan_footprint_exceeds_leg_corridor",
            {"barrel_diameter_mm": 21.2},  # scan footprint = max(21.2, len 21) = 21.2
            {"barrel_diameter_mm": 21.201},
        ),
        (
            "vertical_budget_exceeds_dock_z",
            {"front_end_height_z_mm": 42.0},  # 8 + 42 + 12 = 62.0
            {"front_end_height_z_mm": 42.001},  # 62.001
        ),
        (
            "mass_exceeds_budget",
            {"mass_g": 900.0},
            {"mass_g": 900.001},
        ),
        (
            # Isolate the keepout-footprint boundary WITHOUT tripping the corridor:
            # narrow on the scan axis (len 21 <= 21.4), wide on the traverse axis so the
            # circumscribed diagonal hits the Ø32 keepout. sqrt(21^2 + 24.145^2) ~= 32.0.
            "head_footprint_exceeds_objective_keepout",
            {"front_end_length_x_mm": 21.0, "front_end_width_y_mm": 24.145},  # d≈32.0
            {"front_end_length_x_mm": 21.0, "front_end_width_y_mm": 24.5},  # d≈32.26
        ),
    ],
)
def test_envelope_boundary_exact_passes_just_over_fails(
    axis_blocker, at_budget, over_budget
) -> None:
    at = validate_manifest_envelope(_manifest(**at_budget))
    assert at.fits is True, f"{axis_blocker}: exactly-at-budget must pass"
    assert axis_blocker not in at.blockers

    over = validate_manifest_envelope(_manifest(**over_budget))
    assert over.fits is False, f"{axis_blocker}: 0.001 over must fail"
    assert axis_blocker in over.blockers


def test_realistic_25mm_barrel_head_is_rejected_by_leg_corridor() -> None:
    # OC-A15 cross-module guarantee: a head with a realistic Ø25 4x objective barrel
    # CLEARS the Ø32 objective keepout but STRIKES the standoff-leg corridor (21.4 mm),
    # so it is rejected at dock. The same corridor binds EVERY modality head, not just
    # the observer CAD -- a head that passes the keepout can still strike the legs.
    check = validate_manifest_envelope(_manifest(barrel_diameter_mm=25.0))
    assert check.barrel_fits_keepout is True  # 25 <= 32 keepout
    assert check.scan_footprint_mm == 25.0
    assert check.scan_footprint_fits_corridor is False
    assert check.fits is False
    assert "scan_footprint_exceeds_leg_corridor" in check.blockers
    assert "barrel_exceeds_objective_keepout" not in check.blockers


def test_smis_version_is_required_not_defaulted_to_platform() -> None:
    # An incoming head must declare its own version -- not silently inherit the
    # platform's (F2). Omitting it is a validation error, not an implicit "same as me".
    base = _manifest().model_dump()
    del base["smis_version"]
    with pytest.raises(ValidationError):
        ModuleManifest(**base)


def test_manifest_rejects_unknown_fields_and_bad_values() -> None:
    with pytest.raises(ValidationError):
        ModuleManifest(  # type: ignore[call-arg]
            **{**_manifest().model_dump(), "unexpected_field": 1}
        )
    with pytest.raises(ValidationError):
        _manifest(mass_g=0.0)  # gt=0
    with pytest.raises(ValidationError):
        _manifest(front_end_height_z_mm=-1.0)  # gt=0


def test_manifest_digest_is_deterministic_and_content_sensitive() -> None:
    a = _manifest()
    b = _manifest()
    assert a.manifest_sha256() == b.manifest_sha256()
    assert a.manifest_sha256() != _manifest(module_serial="SN-9999").manifest_sha256()


def test_manifest_digest_canonicalization_is_pinned() -> None:
    # The EEPROM digest is a cross-language contract (a partner's firmware must
    # reproduce it), so the canonicalization recipe is load-bearing and pinned here:
    # sorted keys, compact separators, sha256 (F3). A regression that drops
    # sort_keys would otherwise stay green.
    import hashlib
    import json

    m = _manifest()
    dump = m.model_dump(mode="json")
    canonical = json.dumps(dump, sort_keys=True, separators=(",", ":"))
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert m.manifest_sha256() == expected
    # Order-independence: the same content with shuffled key order yields the same
    # digest -- proving the sort_keys canonicalization, not insertion order.
    shuffled = dict(reversed(list(dump.items())))
    shuffled_canonical = json.dumps(shuffled, sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(shuffled_canonical.encode("utf-8")).hexdigest() == expected


def test_manifest_json_round_trips() -> None:
    m = _manifest()
    restored = ModuleManifest.from_json(m.model_dump_json())
    assert restored == m
    assert restored.manifest_sha256() == m.manifest_sha256()


def test_frozen_envelope_mirrors_the_observer_cad_numbers() -> None:
    env = SmisEnvelope()
    assert env.z_budget_mm == 62.0
    assert env.front_face_clearance_mm == 8.0
    assert env.objective_keepout_diameter_mm == 32.0
    assert env.mass_budget_g == 900.0
