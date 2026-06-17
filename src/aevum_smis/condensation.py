"""Observer condensation-control policy.

The observer images through the plate underside. Condensation is therefore an
acquisition blocker, not a comfort metric: if the MLX90614 underside temperature
does not stay above the SHT41 dew point by the reserved margin, the platform must
raise local purge/heat or refuse imaging.
"""

from __future__ import annotations

import math
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CondensationAction(StrEnum):
    hold = "hold"
    increase_purge = "increase_purge"
    increase_purge_and_lip_heat = "increase_purge_and_lip_heat"
    block_acquisition = "block_acquisition"


class CondensationTelemetry(BaseModel):
    """One local SHT41/MLX90614 sample for the imaged plate/window region."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    plate_id: str = Field(min_length=1)
    sht41_air_temp_c: float = Field(ge=-20.0, le=80.0)
    sht41_relative_humidity_pct: float = Field(ge=0.0, le=100.0)
    mlx90614_underside_temp_c: float = Field(ge=-20.0, le=80.0)
    purge_flow_ml_min: float = Field(default=0.0, ge=0.0)
    lip_heat_pwm: float = Field(default=0.0, ge=0.0, le=1.0)


class CondensationPolicy(BaseModel):
    """Reserved condensation gate; exact flow/heat setpoints remain bench-tuned."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target_margin_c: float = Field(default=2.0, gt=0.0)
    purge_warning_margin_c: float = Field(default=2.5, gt=0.0)
    lip_heat_warning_margin_c: float = Field(default=1.0, ge=0.0)
    max_safe_relative_humidity_pct: float = Field(default=98.0, gt=0.0, le=100.0)


class CondensationCheck(BaseModel):
    """Fail-closed decision for local observer condensation risk."""

    model_config = ConfigDict(frozen=True)

    acquisition_allowed: bool
    action: CondensationAction
    blockers: tuple[str, ...]
    plate_id: str
    dew_point_c: float
    underside_temp_c: float
    condensation_margin_c: float
    target_margin_c: float
    purge_flow_ml_min: float
    lip_heat_pwm: float


DEFAULT_CONDENSATION_POLICY = CondensationPolicy()


def dew_point_celsius(air_temp_c: float, relative_humidity_pct: float) -> float:
    """Compute dew point using the Magnus approximation over water."""

    if relative_humidity_pct <= 0.0:
        return float("-inf")
    a = 17.625
    b = 243.04
    gamma = math.log(relative_humidity_pct / 100.0) + (a * air_temp_c) / (b + air_temp_c)
    return (b * gamma) / (a - gamma)


def evaluate_condensation_control(
    telemetry: CondensationTelemetry,
    policy: CondensationPolicy = DEFAULT_CONDENSATION_POLICY,
) -> CondensationCheck:
    """Evaluate the SHT41/MLX90614 condensation gate before observer acquisition."""

    dew_point = dew_point_celsius(
        telemetry.sht41_air_temp_c,
        telemetry.sht41_relative_humidity_pct,
    )
    margin = telemetry.mlx90614_underside_temp_c - dew_point
    blockers: list[str] = []

    if telemetry.sht41_relative_humidity_pct >= policy.max_safe_relative_humidity_pct:
        blockers.append("headspace_rh_at_condensation_limit")
    if margin < 0.0:
        blockers.append("plate_underside_below_dew_point")
    elif margin < policy.target_margin_c:
        blockers.append("condensation_margin_below_target")

    if blockers:
        action = CondensationAction.block_acquisition
    elif margin < policy.lip_heat_warning_margin_c:
        action = CondensationAction.increase_purge_and_lip_heat
    elif margin < policy.purge_warning_margin_c:
        action = CondensationAction.increase_purge
    else:
        action = CondensationAction.hold

    return CondensationCheck(
        acquisition_allowed=not blockers,
        action=action,
        blockers=tuple(blockers),
        plate_id=telemetry.plate_id,
        dew_point_c=dew_point,
        underside_temp_c=telemetry.mlx90614_underside_temp_c,
        condensation_margin_c=margin,
        target_margin_c=policy.target_margin_c,
        purge_flow_ml_min=telemetry.purge_flow_ml_min,
        lip_heat_pwm=telemetry.lip_heat_pwm,
    )
