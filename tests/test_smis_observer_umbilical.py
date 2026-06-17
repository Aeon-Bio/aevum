from __future__ import annotations

import pytest
from pydantic import ValidationError

from aevum_smis import (
    FROZEN_HEAD_BUS,
    FROZEN_OBSERVER_UMBILICAL,
    HeadBusGroup,
    ObserverUmbilicalConnector,
    ObserverUmbilicalLine,
    ObserverUmbilicalSignal,
    ObserverUmbilicalSpec,
    reconcile_observer_umbilical_with_head_bus,
)


def _umbilical(**overrides) -> ObserverUmbilicalSpec:
    data = FROZEN_OBSERVER_UMBILICAL.model_dump()
    data.update(overrides)
    return ObserverUmbilicalSpec(**data)


def test_frozen_observer_umbilical_reconciles_with_head_bus() -> None:
    check = reconcile_observer_umbilical_with_head_bus()
    assert check.valid is True
    assert check.blockers == ()
    assert check.observer_line_count == 12
    assert check.unique_observer_line_ids is True
    assert check.no_hot_mate is True
    assert check.shield_single_point is True
    assert check.active_low_interlock_present is True
    assert set(check.required_head_bus_groups) == {
        HeadBusGroup.power_24v,
        HeadBusGroup.power_5v,
        HeadBusGroup.power_3v3,
        HeadBusGroup.i2c,
        HeadBusGroup.alarm,
        HeadBusGroup.interlock_laser,
        HeadBusGroup.gige,
        HeadBusGroup.shield,
    }


def test_observer_umbilical_pinout_keeps_gige_off_gx16() -> None:
    by_id = {line.line_id: line for line in FROZEN_OBSERVER_UMBILICAL.lines}
    assert by_id["GIGE_M12_X_CODED"].connector == ObserverUmbilicalConnector.m12_x_gige
    assert "not GX16" in by_id["GIGE_M12_X_CODED"].spec

    gx16_signals = {
        line.signal
        for line in FROZEN_OBSERVER_UMBILICAL.lines
        if line.connector
        in {
            ObserverUmbilicalConnector.gx16_4_power,
            ObserverUmbilicalConnector.gx16_6_control,
        }
    }
    assert ObserverUmbilicalSignal.gige not in gx16_signals


def test_observer_umbilical_matches_power_section_gx16_rail_levels() -> None:
    by_id = {line.line_id: line for line in FROZEN_OBSERVER_UMBILICAL.lines}
    assert by_id["+24V"].connector == ObserverUmbilicalConnector.gx16_4_power
    assert by_id["+24V"].pin == "1"
    assert by_id["24V_GND"].pin == "2"
    assert by_id["+5V"].pin == "3"
    assert by_id["5V_GND"].pin == "4"
    assert by_id["I2C_SDA"].pin == "1"
    assert by_id["I2C_SCL"].pin == "2"
    assert by_id["+3V3"].pin == "3"
    assert by_id["3V3_GND"].pin == "4"
    assert by_id["+24V"].voltage_v == 24.0
    assert by_id["+5V"].voltage_v == 5.0
    assert by_id["+3V3"].voltage_v == 3.3
    assert by_id["I2C_SDA"].logic_level_v == 3.3
    assert by_id["I2C_SCL"].logic_level_v == 3.3


def test_duplicate_observer_line_id_is_rejected_by_reconciliation() -> None:
    lines = list(FROZEN_OBSERVER_UMBILICAL.lines)
    lines[1] = lines[1].model_copy(update={"line_id": lines[0].line_id})
    check = reconcile_observer_umbilical_with_head_bus(_umbilical(lines=tuple(lines)))
    assert check.valid is False
    assert "observer_umbilical_line_id_not_unique" in check.blockers


def test_head_bus_missing_required_umbilical_group_is_rejected() -> None:
    head_bus = FROZEN_HEAD_BUS.model_copy(
        update={
            "lines": tuple(
                line for line in FROZEN_HEAD_BUS.lines if line.group != HeadBusGroup.gige
            )
        }
    )
    check = reconcile_observer_umbilical_with_head_bus(head_bus=head_bus)
    assert check.valid is False
    assert "head_bus_not_superset_of_observer_umbilical" in check.blockers
    assert HeadBusGroup.gige not in check.covered_head_bus_groups


def test_hot_mate_shield_and_interlock_drift_fail_closed() -> None:
    hot = reconcile_observer_umbilical_with_head_bus(
        _umbilical(hot_mate_allowed=True)
    )
    assert hot.valid is False
    assert "observer_umbilical_or_head_bus_hot_mate_allowed" in hot.blockers

    shield = reconcile_observer_umbilical_with_head_bus(
        _umbilical(single_point_shield_bond=False)
    )
    assert shield.valid is False
    assert "observer_umbilical_shield_not_single_point_bonded" in shield.blockers

    lines = list(FROZEN_OBSERVER_UMBILICAL.lines)
    index = next(
        idx
        for idx, line in enumerate(lines)
        if line.signal == ObserverUmbilicalSignal.observer_enable_interlock
    )
    lines[index] = lines[index].model_copy(update={"make_last_break_first": False})
    interlock = reconcile_observer_umbilical_with_head_bus(
        _umbilical(lines=tuple(lines))
    )
    assert interlock.valid is False
    assert "observer_umbilical_interlock_not_fail_closed" in interlock.blockers


def test_observer_umbilical_schema_rejects_unknown_fields_and_bad_values() -> None:
    with pytest.raises(ValidationError):
        ObserverUmbilicalLine(  # type: ignore[call-arg]
            **{**FROZEN_OBSERVER_UMBILICAL.lines[0].model_dump(), "unexpected": "field"}
        )
    with pytest.raises(ValidationError):
        ObserverUmbilicalLine(
            **{**FROZEN_OBSERVER_UMBILICAL.lines[0].model_dump(), "pin": ""}
        )
