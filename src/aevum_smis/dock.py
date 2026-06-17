"""SMIS kinematic dock spec + falsifiable dock-envelope re-check.

The dock is the mechanical contract between the gantry Z-carriage and a swappable
head (``docs/engineering/sensor_module_interface.md``, Mechanical dock section).
This module turns the doc's prose -- a quasi-kinematic 3-2-1 seat (cone + vee +
flat = 6 contacts = exactly 6 DOF), magnet preload with ">5x margin over a 900 g
head", an anti-rotation dowel, and a <=5 um repeatability target -- into a
falsifiable check, mirroring the manifest envelope re-check in ``manifest.py``.

It checks geometry/statics, not motion: the <=5 um repeatability is a Stage-B
physical measurement (see ``docs/protocols/observer_kinematic_dock_repeatability.md``
when authored), carried here only as the recorded target the build must meet.
"""

from __future__ import annotations

from collections import Counter
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from aevum_smis.manifest import FROZEN_ENVELOPE, SmisEnvelope

DEFAULT_REQUIRED_PULL_MARGIN = 5.0
DEFAULT_MAX_HEAD_MASS_G = 900.0
# Worst-case scan acceleration (in g) that adds to the head's static weight as an
# axial separating demand on the magnets. The doc's margin is "over a 900 g head at
# 1 g scan accel", so the demand is the static weight PLUS the 1 g inertial reaction
# (~2x weight), not static weight alone.
DEFAULT_SCAN_ACCEL_G = 1.0


class SeatKind(StrEnum):
    """A kinematic seat and the number of translational DOF it removes."""

    cone = "cone"  # removes 3 DOF
    vee = "vee"  # removes 2 DOF
    flat = "flat"  # removes 1 DOF


_SEAT_DOF = {SeatKind.cone: 3, SeatKind.vee: 2, SeatKind.flat: 1}


class DockSpec(BaseModel):
    """The platform dock's mechanical parameterization."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    seats: tuple[SeatKind, ...] = (SeatKind.cone, SeatKind.vee, SeatKind.flat)
    ball_diameter_mm: float = Field(default=6.0, gt=0.0)  # grade-25 chrome
    # The doc's "2x N52 pot magnets ~3-4 kg each" gives ~6-8 kg, which is only ~3.3x
    # over the 1 g-scan demand (1.8 kg-f) -- below the 5x bar. The review surfaced
    # this; the dock spec moves to 3 magnets (9 kg -> 5.0x). See decision_log.md.
    magnet_count: int = Field(default=3, ge=0)
    magnet_pull_kg_each: float = Field(default=3.0, ge=0.0)  # N52 pot, conservative
    dowel_count: int = Field(default=1, ge=0)  # anti-rotation
    seat_circle_diameter_mm: float = Field(default=44.0, gt=0.0)  # ball circle clears the keepout
    repeatability_target_um: float = Field(default=5.0, gt=0.0)


class DockCheck(BaseModel):
    """Result of re-checking a dock spec against the frozen envelope + a head mass."""

    model_config = ConfigDict(frozen=True)

    fits: bool
    blockers: tuple[str, ...]
    constrained_dof: int
    exactly_constrained: bool
    is_canonical_three_two_one: bool
    total_magnet_pull_kg: float
    separating_demand_kg: float
    pull_margin: float
    pull_margin_ok: bool
    seats_clear_keepout: bool
    has_anti_rotation: bool
    repeatability_target_um: float


_CANONICAL_321 = Counter([SeatKind.cone, SeatKind.vee, SeatKind.flat])


def validate_dock(
    dock: DockSpec,
    *,
    envelope: SmisEnvelope = FROZEN_ENVELOPE,
    max_head_mass_g: float = DEFAULT_MAX_HEAD_MASS_G,
    scan_accel_g: float = DEFAULT_SCAN_ACCEL_G,
    required_pull_margin: float = DEFAULT_REQUIRED_PULL_MARGIN,
) -> DockCheck:
    """Falsifiable dock check: canonical 3-2-1 seat, magnet margin, keepout clearance.

    - Seat: must be exactly the frozen 3-2-1 -- one cone (3 DOF) + one vee (2) + one
      flat (1) = 6 contacts, 6 DOF. DOF==6 alone is necessary but NOT sufficient (two
      vees + two flats also sum to 6 yet is not the doc's seat), so the canonical
      multiset is the real gate; the DOF count is reported for diagnostics.
    - Magnet margin: the separating demand is the head's static weight PLUS its 1 g
      scan-acceleration inertial reaction (~2x weight at scan_accel_g=1), NOT static
      weight alone. Total magnet preload must exceed that demand by >= the required
      margin. (The doc's 2-magnet figure only reaches ~3.3x against this demand,
      which is why the default spec uses 3 magnets.)
    - Keepout clearance: the ball *contact* circle (seat circle minus a ball radius)
      must sit outside the Ø32 objective keepout, so the balls never encroach on the
      optical path.
    - Anti-rotation: at least one dowel.

    The <=5 um repeatability is a Stage-B physical measurement, recorded here as the
    target only -- it is never gated. The 62 mm Z-budget closure lives in
    ``validate_manifest_envelope`` (the head's vertical stack), not here.
    """
    if max_head_mass_g <= 0:
        raise ValueError("max_head_mass_g must be > 0")

    constrained_dof = sum(_SEAT_DOF[s] for s in dock.seats)
    exactly_constrained = constrained_dof == 6
    is_canonical_321 = Counter(dock.seats) == _CANONICAL_321

    total_pull = round(dock.magnet_count * dock.magnet_pull_kg_each, 3)
    head_mass_kg = max_head_mass_g / 1000.0
    # Static weight + inertial reaction at scan acceleration, in kg-force.
    demand_kg = round(head_mass_kg * (1.0 + scan_accel_g), 3)
    pull_margin = round(total_pull / demand_kg, 3) if demand_kg > 0 else 0.0
    pull_margin_ok = pull_margin >= required_pull_margin

    # Ball contact circle: the seat circle minus one ball diameter (a Ø6 ball on a
    # Ø44 circle contacts at ~Ø38, still outside the Ø32 keepout).
    ball_contact_diameter = dock.seat_circle_diameter_mm - dock.ball_diameter_mm
    seats_clear_keepout = (
        ball_contact_diameter >= float(envelope.objective_keepout_diameter_mm)
    )
    has_anti_rotation = dock.dowel_count >= 1

    blockers: list[str] = []
    if not is_canonical_321:
        if constrained_dof < 6:
            blockers.append("seat_under_constrained")
        elif constrained_dof > 6:
            blockers.append("seat_over_constrained")
        else:
            blockers.append("seat_not_canonical_three_two_one")
    if not pull_margin_ok:
        blockers.append("magnet_pull_margin_below_minimum")
    if not seats_clear_keepout:
        blockers.append("seat_circle_intrudes_objective_keepout")
    if not has_anti_rotation:
        blockers.append("missing_anti_rotation_dowel")

    return DockCheck(
        fits=not blockers,
        blockers=tuple(blockers),
        constrained_dof=constrained_dof,
        exactly_constrained=exactly_constrained,
        is_canonical_three_two_one=is_canonical_321,
        total_magnet_pull_kg=total_pull,
        separating_demand_kg=demand_kg,
        pull_margin=pull_margin,
        pull_margin_ok=pull_margin_ok,
        seats_clear_keepout=seats_clear_keepout,
        has_anti_rotation=has_anti_rotation,
        repeatability_target_um=dock.repeatability_target_um,
    )
