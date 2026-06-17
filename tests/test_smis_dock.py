from __future__ import annotations

import pytest
from pydantic import ValidationError

from aevum_smis import DockSpec, SeatKind, validate_dock


def test_default_dock_passes_all_gates() -> None:
    check = validate_dock(DockSpec())
    assert check.fits is True
    assert check.blockers == ()
    # cone(3) + vee(2) + flat(1) = 6 DOF, the canonical 3-2-1 seat.
    assert check.constrained_dof == 6
    assert check.exactly_constrained is True
    assert check.is_canonical_three_two_one is True
    # 3 magnets x 3 kg = 9 kg over the 1 g-scan demand (0.9 kg x 2 = 1.8 kg) = 5.0x.
    assert check.total_magnet_pull_kg == 9.0
    assert check.separating_demand_kg == 1.8
    assert check.pull_margin == 5.0
    assert check.pull_margin_ok is True
    # Ø6 ball on a Ø44 circle contacts at Ø38, outside the Ø32 keepout.
    assert check.seats_clear_keepout is True
    assert check.has_anti_rotation is True
    assert check.repeatability_target_um == 5.0


def test_load_case_includes_scan_acceleration_not_static_weight_only() -> None:
    # The BLOCKER finding: the doc's 2-magnet config (6 kg) is only ~3.3x over the
    # 1 g-scan demand (1.8 kg), BELOW the 5x bar -- a static-weight-only reading
    # (6/0.9 = 6.67x) would falsely pass. The check models the real load case.
    two_magnets = validate_dock(DockSpec(magnet_count=2))  # 2 x 3 = 6 kg
    assert two_magnets.separating_demand_kg == 1.8
    assert two_magnets.pull_margin == 3.333
    assert two_magnets.pull_margin_ok is False
    assert "magnet_pull_margin_below_minimum" in two_magnets.blockers
    # With scan_accel_g=0 (static only) the same magnets read 6/0.9 = 6.667x -- this
    # is the optimistic reading the formula must NOT default to.
    static = validate_dock(DockSpec(magnet_count=2), scan_accel_g=0.0)
    assert static.pull_margin == 6.667


def test_under_constrained_seat_is_rejected() -> None:
    # cone + vee = 5 DOF: the head can still rock (one DOF free).
    check = validate_dock(DockSpec(seats=(SeatKind.cone, SeatKind.vee)))
    assert check.fits is False
    assert check.constrained_dof == 5
    assert check.is_canonical_three_two_one is False
    assert "seat_under_constrained" in check.blockers
    assert "seat_over_constrained" not in check.blockers  # label direction pinned


def test_over_constrained_seat_is_rejected() -> None:
    # cone + cone + flat = 7 DOF: over-constrained, the seat binds.
    check = validate_dock(DockSpec(seats=(SeatKind.cone, SeatKind.cone, SeatKind.flat)))
    assert check.fits is False
    assert check.constrained_dof == 7
    assert "seat_over_constrained" in check.blockers
    assert "seat_under_constrained" not in check.blockers  # label direction pinned


def test_non_canonical_six_dof_seat_is_rejected() -> None:
    # MAJOR finding: vee + vee + flat + flat sums to 6 DOF but is NOT the frozen
    # 3-2-1 seat. DOF==6 alone must not pass.
    check = validate_dock(
        DockSpec(seats=(SeatKind.vee, SeatKind.vee, SeatKind.flat, SeatKind.flat))
    )
    assert check.constrained_dof == 6
    assert check.exactly_constrained is True
    assert check.is_canonical_three_two_one is False
    assert check.fits is False
    assert "seat_not_canonical_three_two_one" in check.blockers


def test_weak_or_missing_magnets_fail_the_pull_margin() -> None:
    # 3 x 1.5 = 4.5 kg / 1.8 = 2.5x < 5x.
    weak = validate_dock(DockSpec(magnet_pull_kg_each=1.5))
    assert weak.pull_margin == 2.5
    assert "magnet_pull_margin_below_minimum" in weak.blockers
    # No magnets at all -> zero pull -> zero margin -> rejected.
    none = validate_dock(DockSpec(magnet_count=0))
    assert none.total_magnet_pull_kg == 0.0
    assert none.pull_margin == 0.0
    assert "magnet_pull_margin_below_minimum" in none.blockers


def test_pull_margin_boundary_with_head_mass() -> None:
    # Default 9 kg pull. At 900 g the demand is 1.8 kg -> exactly 5.0x (passes).
    at = validate_dock(DockSpec(), max_head_mass_g=900.0)
    assert at.pull_margin == 5.0
    assert at.pull_margin_ok is True
    # A heavier head raises the demand and fails: 1000 g -> demand 2.0 -> 4.5x.
    over = validate_dock(DockSpec(), max_head_mass_g=1000.0)
    assert over.separating_demand_kg == 2.0
    assert over.pull_margin == 4.5
    assert over.pull_margin_ok is False


def test_seat_circle_inside_keepout_is_rejected() -> None:
    # Ball contact circle (seat circle - Ø6 ball) below the Ø32 keepout -> intrudes.
    check = validate_dock(DockSpec(seat_circle_diameter_mm=34.0))  # contact 28 < 32
    assert check.fits is False
    assert check.seats_clear_keepout is False
    assert "seat_circle_intrudes_objective_keepout" in check.blockers
    # Exactly at the keepout after the ball radius: 38 - 6 = 32 >= 32 clears.
    at = validate_dock(DockSpec(seat_circle_diameter_mm=38.0))
    assert at.seats_clear_keepout is True


def test_missing_dowel_is_rejected() -> None:
    check = validate_dock(DockSpec(dowel_count=0))
    assert check.fits is False
    assert check.has_anti_rotation is False
    assert "missing_anti_rotation_dowel" in check.blockers


def test_multiple_dock_failures_accumulate_exact_blocker_set() -> None:
    check = validate_dock(
        DockSpec(
            seats=(SeatKind.cone, SeatKind.vee),  # 5 DOF, under-constrained
            magnet_count=1,  # 3 kg / 1.8 = 1.67x
            dowel_count=0,
        )
    )
    assert check.fits is False
    assert set(check.blockers) == {
        "seat_under_constrained",
        "magnet_pull_margin_below_minimum",
        "missing_anti_rotation_dowel",
    }


def test_non_positive_head_mass_raises() -> None:
    with pytest.raises(ValueError):
        validate_dock(DockSpec(), max_head_mass_g=0.0)


def test_dock_spec_rejects_unknown_fields_and_bad_values() -> None:
    with pytest.raises(ValidationError):
        DockSpec(unexpected=1)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        DockSpec(ball_diameter_mm=0.0)  # gt=0
    with pytest.raises(ValidationError):
        DockSpec(magnet_count=-1)  # ge=0
