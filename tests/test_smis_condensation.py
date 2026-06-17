from __future__ import annotations

import pytest
from pydantic import ValidationError

from aevum_smis import (
    CondensationAction,
    CondensationPolicy,
    CondensationTelemetry,
    dew_point_celsius,
    evaluate_condensation_control,
)


def _telemetry(**overrides) -> CondensationTelemetry:
    base = dict(
        plate_id="plate-a",
        sht41_air_temp_c=37.0,
        sht41_relative_humidity_pct=95.0,
        mlx90614_underside_temp_c=39.0,
        purge_flow_ml_min=200.0,
        lip_heat_pwm=0.0,
    )
    base.update(overrides)
    return CondensationTelemetry(**base)


def test_dew_point_matches_warm_humid_stage0_case() -> None:
    assert dew_point_celsius(37.0, 95.0) == pytest.approx(36.1, abs=0.1)


def test_condensation_gate_allows_acquisition_when_margin_exceeds_two_celsius() -> None:
    check = evaluate_condensation_control(_telemetry(mlx90614_underside_temp_c=39.0))
    assert check.acquisition_allowed is True
    assert check.action == CondensationAction.hold
    assert check.blockers == ()
    assert check.condensation_margin_c == pytest.approx(2.9, abs=0.1)
    assert check.target_margin_c == 2.0


def test_condensation_gate_warns_to_raise_purge_before_margin_is_spent() -> None:
    check = evaluate_condensation_control(_telemetry(mlx90614_underside_temp_c=38.5))
    assert check.acquisition_allowed is True
    assert check.action == CondensationAction.increase_purge
    assert check.blockers == ()


def test_condensation_gate_blocks_when_margin_below_reserved_target() -> None:
    check = evaluate_condensation_control(_telemetry(mlx90614_underside_temp_c=37.0))
    assert check.acquisition_allowed is False
    assert check.action == CondensationAction.block_acquisition
    assert check.blockers == ("condensation_margin_below_target",)


def test_condensation_gate_blocks_when_glass_is_below_dew_point() -> None:
    check = evaluate_condensation_control(_telemetry(mlx90614_underside_temp_c=35.0))
    assert check.acquisition_allowed is False
    assert check.blockers == ("plate_underside_below_dew_point",)


def test_condensation_gate_blocks_saturated_headspace_even_if_margin_looks_ok() -> None:
    check = evaluate_condensation_control(
        _telemetry(sht41_relative_humidity_pct=99.0, mlx90614_underside_temp_c=42.0)
    )
    assert check.acquisition_allowed is False
    assert check.blockers == ("headspace_rh_at_condensation_limit",)


def test_policy_thresholds_are_configurable_for_stage0_tuning() -> None:
    policy = CondensationPolicy(target_margin_c=3.0, purge_warning_margin_c=4.0)
    check = evaluate_condensation_control(
        _telemetry(mlx90614_underside_temp_c=39.0),
        policy=policy,
    )
    assert check.acquisition_allowed is False
    assert check.blockers == ("condensation_margin_below_target",)
    assert check.target_margin_c == 3.0


def test_condensation_schema_rejects_impossible_telemetry() -> None:
    with pytest.raises(ValidationError):
        CondensationTelemetry(
            plate_id="",
            sht41_air_temp_c=37.0,
            sht41_relative_humidity_pct=95.0,
            mlx90614_underside_temp_c=39.0,
        )
    with pytest.raises(ValidationError):
        _telemetry(sht41_relative_humidity_pct=101.0)
    with pytest.raises(ValidationError):
        _telemetry(lip_heat_pwm=1.1)
