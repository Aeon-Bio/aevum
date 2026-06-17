from __future__ import annotations

import pytest
from pydantic import ValidationError

from aevum_smis import (
    FROZEN_HEAD_BUS,
    REQUIRED_HEAD_BUS_GROUPS,
    HeadBusGroup,
    HeadBusLine,
    HeadBusSpec,
    validate_head_bus_spec,
)


def _spec(**overrides) -> HeadBusSpec:
    data = FROZEN_HEAD_BUS.model_dump()
    data.update(overrides)
    return HeadBusSpec(**data)


def test_frozen_head_bus_contract_is_valid() -> None:
    check = validate_head_bus_spec(FROZEN_HEAD_BUS)
    assert check.valid is True
    assert check.blockers == ()
    assert check.required_groups_present is True
    assert check.unique_line_ids is True
    assert check.no_hot_mate is True
    assert check.eeprom_address_is_reserved is True
    assert check.interlocks_fail_closed is True
    assert check.shield_single_point is True
    assert check.line_count_total == 19


def test_head_bus_groups_match_the_v0_1_prose_table() -> None:
    assert {line.group for line in FROZEN_HEAD_BUS.lines} == set(REQUIRED_HEAD_BUS_GROUPS)
    assert [line.group for line in FROZEN_HEAD_BUS.lines] == [
        HeadBusGroup.power_24v,
        HeadBusGroup.power_5v,
        HeadBusGroup.power_3v3,
        HeadBusGroup.i2c,
        HeadBusGroup.one_wire,
        HeadBusGroup.gige,
        HeadBusGroup.microwave_coax,
        HeadBusGroup.fiber_bulkhead,
        HeadBusGroup.interlock_laser,
        HeadBusGroup.interlock_mw,
        HeadBusGroup.alarm,
        HeadBusGroup.shield,
    ]


def test_head_bus_power_and_identity_constants_are_pinned() -> None:
    assert FROZEN_HEAD_BUS.smis_version == "0.1"
    assert FROZEN_HEAD_BUS.float_mount_tolerance_mm == 0.5
    assert FROZEN_HEAD_BUS.hot_mate_allowed is False
    assert FROZEN_HEAD_BUS.id_eeprom_i2c_address == 0x50
    assert FROZEN_HEAD_BUS.cal_vault_family == "DS28E07-class 1-Wire"

    by_group = {line.group: line for line in FROZEN_HEAD_BUS.lines}
    assert by_group[HeadBusGroup.power_24v].voltage_v == 24.0
    assert by_group[HeadBusGroup.power_5v].voltage_v == 5.0
    assert by_group[HeadBusGroup.power_3v3].voltage_v == 3.3
    assert by_group[HeadBusGroup.power_3v3].max_current_ma == 500.0
    assert by_group[HeadBusGroup.i2c].logic_level_v == 3.3
    assert by_group[HeadBusGroup.i2c].notes.startswith("ID EEPROM at 0x50")


def test_interlocks_are_active_low_make_last_break_first() -> None:
    by_group = {line.group: line for line in FROZEN_HEAD_BUS.lines}
    for group in (HeadBusGroup.interlock_laser, HeadBusGroup.interlock_mw):
        line = by_group[group]
        assert line.active_low is True
        assert line.make_last_break_first is True
        assert "hardware loop" in line.spec

    alarm = by_group[HeadBusGroup.alarm]
    assert alarm.active_low is True
    assert alarm.make_last_break_first is False


def test_optional_mw_and_fiber_paths_are_not_default_electrical_loads() -> None:
    by_group = {line.group: line for line in FROZEN_HEAD_BUS.lines}
    assert by_group[HeadBusGroup.microwave_coax].populated_by_default is False
    assert by_group[HeadBusGroup.fiber_bulkhead].populated_by_default is False
    assert "optical, not electrical" in by_group[HeadBusGroup.fiber_bulkhead].notes


def test_head_bus_digest_is_deterministic_and_content_sensitive() -> None:
    assert FROZEN_HEAD_BUS.spec_sha256() == _spec().spec_sha256()
    drifted = _spec(float_mount_tolerance_mm=0.6)
    assert FROZEN_HEAD_BUS.spec_sha256() != drifted.spec_sha256()


def test_duplicate_line_id_is_rejected_by_validation() -> None:
    lines = list(FROZEN_HEAD_BUS.lines)
    lines[1] = lines[1].model_copy(update={"line_id": lines[0].line_id})
    check = validate_head_bus_spec(_spec(lines=tuple(lines)))
    assert check.valid is False
    assert "head_bus_line_id_not_unique" in check.blockers


def test_missing_signal_group_is_rejected_by_validation() -> None:
    lines = tuple(
        line for line in FROZEN_HEAD_BUS.lines if line.group != HeadBusGroup.one_wire
    )
    check = validate_head_bus_spec(_spec(lines=lines))
    assert check.valid is False
    assert "head_bus_missing_or_extra_signal_group" in check.blockers


def test_hot_mate_or_wrong_eeprom_address_are_rejected() -> None:
    hot = validate_head_bus_spec(_spec(hot_mate_allowed=True))
    assert hot.valid is False
    assert "head_bus_hot_mate_allowed" in hot.blockers

    wrong_eeprom = validate_head_bus_spec(_spec(id_eeprom_i2c_address=0x51))
    assert wrong_eeprom.valid is False
    assert "head_bus_eeprom_address_not_0x50" in wrong_eeprom.blockers


def test_interlock_drift_is_rejected() -> None:
    lines = list(FROZEN_HEAD_BUS.lines)
    index = next(
        idx for idx, line in enumerate(lines) if line.group == HeadBusGroup.interlock_laser
    )
    lines[index] = lines[index].model_copy(update={"make_last_break_first": False})
    check = validate_head_bus_spec(_spec(lines=tuple(lines)))
    assert check.valid is False
    assert "head_bus_interlocks_not_fail_closed" in check.blockers


def test_second_shield_bond_is_rejected() -> None:
    check = validate_head_bus_spec(_spec(single_point_shield_bond=False))
    assert check.valid is False
    assert "head_bus_shield_not_single_point_bonded" in check.blockers


def test_head_bus_schema_rejects_unknown_fields_and_bad_values() -> None:
    with pytest.raises(ValidationError):
        HeadBusLine(  # type: ignore[call-arg]
            **{**FROZEN_HEAD_BUS.lines[0].model_dump(), "unexpected": "field"}
        )
    with pytest.raises(ValidationError):
        HeadBusLine(**{**FROZEN_HEAD_BUS.lines[0].model_dump(), "line_count": 0})
    with pytest.raises(ValidationError):
        HeadBusSpec(**{**FROZEN_HEAD_BUS.model_dump(), "id_eeprom_i2c_address": 0x80})
