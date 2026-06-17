"""SMIS HEAD-BUS v0.1 machine-checkable pinout contract.

The HEAD-BUS is the frozen electrical boundary at the swappable-head dock. This
module turns the prose table in ``docs/engineering/sensor_module_interface.md``
into a small typed schema so hardware records and module manifests can be checked
against one canonical bus contract.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class HeadBusGroup(StrEnum):
    power_24v = "power_24v"
    power_5v = "power_5v"
    power_3v3 = "power_3v3"
    i2c = "i2c"
    one_wire = "one_wire"
    gige = "gige"
    microwave_coax = "microwave_coax"
    fiber_bulkhead = "fiber_bulkhead"
    interlock_laser = "interlock_laser"
    interlock_mw = "interlock_mw"
    alarm = "alarm"
    shield = "shield"


class HeadBusLine(BaseModel):
    """One frozen signal group on the HEAD-BUS connector carrier."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    group: HeadBusGroup
    line_id: str = Field(min_length=1)
    line_count: int | None = Field(default=None, gt=0)
    connector: str = Field(min_length=1)
    spec: str = Field(min_length=1)
    notes: str = Field(min_length=1)
    voltage_v: float | None = Field(default=None, gt=0.0)
    logic_level_v: float | None = Field(default=None, gt=0.0)
    max_current_ma: float | None = Field(default=None, gt=0.0)
    active_low: bool = False
    make_last_break_first: bool = False
    populated_by_default: bool = True


class HeadBusSpec(BaseModel):
    """Frozen SMIS v0.1 HEAD-BUS schema.

    A change to this object is an SMIS-major electrical-interface change unless it
    is strictly additive under the future semver policy.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    smis_version: str = Field(min_length=1)
    connector_family: str = Field(min_length=1)
    float_mount_tolerance_mm: float = Field(ge=0.0)
    hot_mate_allowed: bool
    id_eeprom_i2c_address: int = Field(ge=0, le=0x7F)
    cal_vault_family: str = Field(min_length=1)
    single_point_shield_bond: bool
    lines: tuple[HeadBusLine, ...]

    def spec_sha256(self) -> str:
        payload = json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


FROZEN_HEAD_BUS = HeadBusSpec(
    smis_version="0.1",
    connector_family="blind-mate float carrier, mixed signal + M12/SMP/fiber bulkheads",
    float_mount_tolerance_mm=0.5,
    hot_mate_allowed=False,
    id_eeprom_i2c_address=0x50,
    cal_vault_family="DS28E07-class 1-Wire",
    single_point_shield_bond=True,
    lines=(
        HeadBusLine(
            group=HeadBusGroup.power_24v,
            line_id="+24V_GND",
            line_count=2,
            connector="blind-mate power contacts",
            spec="24 V from HRP-150-24, fused at head branch",
            voltage_v=24.0,
            notes="motion/heater-class loads only",
        ),
        HeadBusLine(
            group=HeadBusGroup.power_5v,
            line_id="+5V_GND",
            line_count=2,
            connector="blind-mate power contacts",
            spec="5 V from DDR-15G-5 isolated rail",
            voltage_v=5.0,
            notes="head Pi and LED-ring driver",
        ),
        HeadBusLine(
            group=HeadBusGroup.power_3v3,
            line_id="+3V3_GND",
            line_count=2,
            connector="blind-mate low-power contacts",
            spec="3.3 V sensor/logic rail, <= 500 mA",
            voltage_v=3.3,
            max_current_ma=500.0,
            notes="matches GX16-6 logic level",
        ),
        HeadBusLine(
            group=HeadBusGroup.i2c,
            line_id="I2C_SDA_SCL",
            line_count=2,
            connector="blind-mate signal contacts",
            spec="3.3 V I2C",
            logic_level_v=3.3,
            notes="ID EEPROM at 0x50 plus low-rate module sensors behind per-head mux",
        ),
        HeadBusLine(
            group=HeadBusGroup.one_wire,
            line_id="ONE_WIRE_CAL",
            line_count=1,
            connector="blind-mate signal contact",
            spec="DS28E07-class 1-Wire",
            logic_level_v=3.3,
            notes="redundant ID and per-module calibration vault",
        ),
        HeadBusLine(
            group=HeadBusGroup.gige,
            line_id="GIGE_M12_X_CODED",
            line_count=4,
            connector="M12 X-coded bulkhead",
            spec="1000BASE-T",
            notes="head-Pi capture lane; frozen high-speed path",
        ),
        HeadBusLine(
            group=HeadBusGroup.microwave_coax,
            line_id="MW_COAX",
            line_count=None,
            connector="SMP/SMA coax bulkhead",
            spec="DC-6 GHz",
            notes="NV magnetometry/thermometry only; capped otherwise",
            populated_by_default=False,
        ),
        HeadBusLine(
            group=HeadBusGroup.fiber_bulkhead,
            line_id="FIBER_BULKHEAD",
            line_count=None,
            connector="FC/SMA905 float-carrier bulkhead",
            spec="optical fiber handoff",
            notes="spectroscopy offboard signal; optical, not electrical",
            populated_by_default=False,
        ),
        HeadBusLine(
            group=HeadBusGroup.interlock_laser,
            line_id="INTERLOCK_LASER",
            line_count=1,
            connector="make-last/break-first safety contact",
            spec="active-low hardware loop",
            notes="breaks laser-enable if head undocked or lid open",
            active_low=True,
            make_last_break_first=True,
        ),
        HeadBusLine(
            group=HeadBusGroup.interlock_mw,
            line_id="INTERLOCK_MW",
            line_count=1,
            connector="make-last/break-first safety contact",
            spec="active-low hardware loop",
            notes="breaks microwave amplifier enable",
            active_low=True,
            make_last_break_first=True,
        ),
        HeadBusLine(
            group=HeadBusGroup.alarm,
            line_id="ALARM_N",
            line_count=1,
            connector="blind-mate signal contact",
            spec="open-drain active-low",
            notes="inherits GX16-6 pin 5 alarm semantics",
            active_low=True,
        ),
        HeadBusLine(
            group=HeadBusGroup.shield,
            line_id="SHIELD_CHASSIS",
            line_count=1,
            connector="360 degree backshell",
            spec="single-point chassis shield",
            notes="bonded at sensor-cluster star; no second earth bond",
        ),
    ),
)


class HeadBusCheck(BaseModel):
    """Validation result for a HEAD-BUS spec."""

    model_config = ConfigDict(frozen=True)

    valid: bool
    blockers: tuple[str, ...]
    line_count_total: int
    required_groups_present: bool
    unique_line_ids: bool
    no_hot_mate: bool
    eeprom_address_is_reserved: bool
    interlocks_fail_closed: bool
    shield_single_point: bool


REQUIRED_HEAD_BUS_GROUPS: tuple[HeadBusGroup, ...] = tuple(HeadBusGroup)


def validate_head_bus_spec(spec: HeadBusSpec = FROZEN_HEAD_BUS) -> HeadBusCheck:
    """Check the frozen electrical contract for drift and fail-open omissions."""

    groups = [line.group for line in spec.lines]
    line_ids = [line.line_id for line in spec.lines]
    required_present = set(groups) == set(REQUIRED_HEAD_BUS_GROUPS)
    unique_ids = len(line_ids) == len(set(line_ids))
    no_hot_mate = spec.hot_mate_allowed is False
    eeprom_ok = spec.id_eeprom_i2c_address == 0x50
    interlock_lines = [
        line
        for line in spec.lines
        if line.group in {HeadBusGroup.interlock_laser, HeadBusGroup.interlock_mw}
    ]
    interlocks_fail_closed = (
        len(interlock_lines) == 2
        and all(line.active_low and line.make_last_break_first for line in interlock_lines)
    )
    shield_single_point = spec.single_point_shield_bond and any(
        line.group == HeadBusGroup.shield for line in spec.lines
    )

    blockers: list[str] = []
    if not required_present:
        blockers.append("head_bus_missing_or_extra_signal_group")
    if not unique_ids:
        blockers.append("head_bus_line_id_not_unique")
    if not no_hot_mate:
        blockers.append("head_bus_hot_mate_allowed")
    if not eeprom_ok:
        blockers.append("head_bus_eeprom_address_not_0x50")
    if not interlocks_fail_closed:
        blockers.append("head_bus_interlocks_not_fail_closed")
    if not shield_single_point:
        blockers.append("head_bus_shield_not_single_point_bonded")

    total = sum(line.line_count or 1 for line in spec.lines)
    return HeadBusCheck(
        valid=not blockers,
        blockers=tuple(blockers),
        line_count_total=total,
        required_groups_present=required_present,
        unique_line_ids=unique_ids,
        no_hot_mate=no_hot_mate,
        eeprom_address_is_reserved=eeprom_ok,
        interlocks_fail_closed=interlocks_fail_closed,
        shield_single_point=shield_single_point,
    )
