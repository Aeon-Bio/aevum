"""Observer GX16 umbilical contract and HEAD-BUS reconciliation.

The observer umbilical is the offboard PSU/compute boundary for the row observer.
It is not the swappable-head dock itself; it is the upstream service boundary that
the SMIS HEAD-BUS must remain a superset of.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from aevum_smis.head_bus import FROZEN_HEAD_BUS, HeadBusGroup, HeadBusSpec


class ObserverUmbilicalConnector(StrEnum):
    gx16_4_power = "GX16-4 power"
    gx16_6_control = "GX16-6 control"
    m12_x_gige = "M12 X-coded GigE"
    shield_backshell = "shield backshell"


class ObserverUmbilicalSignal(StrEnum):
    power_24v = "power_24v"
    power_5v = "power_5v"
    power_3v3 = "power_3v3"
    i2c = "i2c"
    alarm = "alarm"
    observer_enable_interlock = "observer_enable_interlock"
    gige = "gige"
    shield = "shield"
    spare = "spare"


class ObserverUmbilicalLine(BaseModel):
    """One frozen line on the observer offboard umbilical."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    connector: ObserverUmbilicalConnector
    pin: str = Field(min_length=1)
    signal: ObserverUmbilicalSignal
    line_id: str = Field(min_length=1)
    spec: str = Field(min_length=1)
    maps_to_head_bus_group: HeadBusGroup | None = None
    voltage_v: float | None = Field(default=None, gt=0.0)
    logic_level_v: float | None = Field(default=None, gt=0.0)
    active_low: bool = False
    make_last_break_first: bool = False
    populated_by_default: bool = True


class ObserverUmbilicalSpec(BaseModel):
    """Frozen observer offboard-boundary pinout."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    spec_version: str = Field(min_length=1)
    hot_mate_allowed: bool
    single_point_shield_bond: bool
    lines: tuple[ObserverUmbilicalLine, ...]


class UmbilicalHeadBusReconciliation(BaseModel):
    """Validation result proving HEAD-BUS covers the observer umbilical classes."""

    model_config = ConfigDict(frozen=True)

    valid: bool
    blockers: tuple[str, ...]
    required_head_bus_groups: tuple[HeadBusGroup, ...]
    covered_head_bus_groups: tuple[HeadBusGroup, ...]
    observer_line_count: int
    unique_observer_line_ids: bool
    no_hot_mate: bool
    shield_single_point: bool
    active_low_interlock_present: bool


FROZEN_OBSERVER_UMBILICAL = ObserverUmbilicalSpec(
    spec_version="0.1",
    hot_mate_allowed=False,
    single_point_shield_bond=True,
    lines=(
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.gx16_4_power,
            pin="1",
            signal=ObserverUmbilicalSignal.power_24v,
            line_id="+24V",
            spec="24 V observer motor/source rail from offboard PSU",
            maps_to_head_bus_group=HeadBusGroup.power_24v,
            voltage_v=24.0,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.gx16_4_power,
            pin="2",
            signal=ObserverUmbilicalSignal.power_24v,
            line_id="24V_GND",
            spec="24 V return",
            maps_to_head_bus_group=HeadBusGroup.power_24v,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.gx16_4_power,
            pin="3",
            signal=ObserverUmbilicalSignal.power_5v,
            line_id="+5V",
            spec="5 V isolated Pi/LED logic rail",
            maps_to_head_bus_group=HeadBusGroup.power_5v,
            voltage_v=5.0,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.gx16_4_power,
            pin="4",
            signal=ObserverUmbilicalSignal.power_5v,
            line_id="5V_GND",
            spec="5 V isolated return",
            maps_to_head_bus_group=HeadBusGroup.power_5v,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.gx16_6_control,
            pin="1",
            signal=ObserverUmbilicalSignal.i2c,
            line_id="I2C_SDA",
            spec="3.3 V I2C data",
            maps_to_head_bus_group=HeadBusGroup.i2c,
            logic_level_v=3.3,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.gx16_6_control,
            pin="2",
            signal=ObserverUmbilicalSignal.i2c,
            line_id="I2C_SCL",
            spec="3.3 V I2C clock",
            maps_to_head_bus_group=HeadBusGroup.i2c,
            logic_level_v=3.3,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.gx16_6_control,
            pin="3",
            signal=ObserverUmbilicalSignal.power_3v3,
            line_id="+3V3",
            spec="3.3 V low-current sensor/control rail",
            maps_to_head_bus_group=HeadBusGroup.power_3v3,
            voltage_v=3.3,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.gx16_6_control,
            pin="4",
            signal=ObserverUmbilicalSignal.power_3v3,
            line_id="3V3_GND",
            spec="3.3 V return, common with 5 V isolated return",
            maps_to_head_bus_group=HeadBusGroup.power_3v3,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.gx16_6_control,
            pin="5",
            signal=ObserverUmbilicalSignal.alarm,
            line_id="ALARM_N",
            spec="open-drain active-low safety alarm",
            maps_to_head_bus_group=HeadBusGroup.alarm,
            active_low=True,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.gx16_6_control,
            pin="6",
            signal=ObserverUmbilicalSignal.observer_enable_interlock,
            line_id="OBSERVER_ENABLE_N",
            spec="active-low observer enable loop, physically opened on service disconnect",
            maps_to_head_bus_group=HeadBusGroup.interlock_laser,
            active_low=True,
            make_last_break_first=True,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.m12_x_gige,
            pin="A-D",
            signal=ObserverUmbilicalSignal.gige,
            line_id="GIGE_M12_X_CODED",
            spec="1000BASE-T on separate shielded data bulkhead, not GX16",
            maps_to_head_bus_group=HeadBusGroup.gige,
        ),
        ObserverUmbilicalLine(
            connector=ObserverUmbilicalConnector.shield_backshell,
            pin="backshell",
            signal=ObserverUmbilicalSignal.shield,
            line_id="SHIELD_CHASSIS",
            spec="360 degree shield, bonded at one chassis star point",
            maps_to_head_bus_group=HeadBusGroup.shield,
        ),
    ),
)


def reconcile_observer_umbilical_with_head_bus(
    umbilical: ObserverUmbilicalSpec = FROZEN_OBSERVER_UMBILICAL,
    head_bus: HeadBusSpec = FROZEN_HEAD_BUS,
) -> UmbilicalHeadBusReconciliation:
    """Verify that HEAD-BUS remains a superset of the observer GX16 boundary."""

    line_ids = [line.line_id for line in umbilical.lines]
    required_groups = tuple(
        dict.fromkeys(
            line.maps_to_head_bus_group
            for line in umbilical.lines
            if line.maps_to_head_bus_group is not None
        )
    )
    head_bus_groups = {line.group for line in head_bus.lines}
    covered_groups = tuple(group for group in required_groups if group in head_bus_groups)
    unique_ids = len(line_ids) == len(set(line_ids))
    no_hot_mate = umbilical.hot_mate_allowed is False and head_bus.hot_mate_allowed is False
    shield_single_point = (
        umbilical.single_point_shield_bond and head_bus.single_point_shield_bond
    )
    active_low_interlock = any(
        line.signal == ObserverUmbilicalSignal.observer_enable_interlock
        and line.active_low
        and line.make_last_break_first
        for line in umbilical.lines
    )

    blockers: list[str] = []
    if not unique_ids:
        blockers.append("observer_umbilical_line_id_not_unique")
    if set(required_groups) - head_bus_groups:
        blockers.append("head_bus_not_superset_of_observer_umbilical")
    if not no_hot_mate:
        blockers.append("observer_umbilical_or_head_bus_hot_mate_allowed")
    if not shield_single_point:
        blockers.append("observer_umbilical_shield_not_single_point_bonded")
    if not active_low_interlock:
        blockers.append("observer_umbilical_interlock_not_fail_closed")

    return UmbilicalHeadBusReconciliation(
        valid=not blockers,
        blockers=tuple(blockers),
        required_head_bus_groups=required_groups,
        covered_head_bus_groups=covered_groups,
        observer_line_count=len(umbilical.lines),
        unique_observer_line_ids=unique_ids,
        no_hot_mate=no_hot_mate,
        shield_single_point=shield_single_point,
        active_low_interlock_present=active_low_interlock,
    )
