"""Two-layer observer<->OT-2 interlock — the SOFTWARE half (IN-C7 / HX3).

`docs/engineering/observation_module.md` specifies defense in depth:

1. **Software lease (cooperative)** — the `observer_scan` lease (IN-C4, `observer.py`).
2. **Physical E-stop interlock (the backstop a software lock legally cannot provide)** — the
   observer's TMC2209 enable pins are hardware-gated by a signal the bridge asserts ONLY
   while the observer lease is held; lease released -> enable line drops -> motors disabled
   at the driver regardless of software. Inversely, the bridge will not grant a pipetting
   lease until the observer reports a hardware "head parked + Z-retracted" limit.

This module owns the SOFTWARE side of layer 2: the *enable intent* the bridge asserts to the
(hardware, B) enable line, and the *handoff precondition* the bridge enforces before granting
a pipetting lease. It does NOT — and a software module legally cannot — guarantee the motors
are de-energized; that is the hardware backstop. Keeping the two explicit is the point:

- `observer_enable_intent` returns intent, never the hardware enable state.
- `ObserverParkReport` is the SOFTWARE record of a HARDWARE limit readback (the GX16
  parked/Z-retracted signal). Absent / false / stale / future-dated => fail closed to "not
  safely parked", because a software lease releasing does not prove the head physically moved.

Authority kept separate from the lease itself (IN-C4), registration (IN-C6), source-enable,
and condensation: this is purely the motion-handoff interlock.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict

from aevum_ot2.core.lock import lease_is_held
from aevum_ot2.core.models import BridgeLeaseKind, BridgeLock

# How recently the observer must have reported parked + Z-retracted for the bridge to trust
# the head is still safe to pipette around. Conservative policy default; a real value is a
# function of how the observer reports its limit (continuous heartbeat vs. one-shot) and is
# refined with the Stage-4 interlock build. Fail-closed: an older report does not admit.
DEFAULT_MAX_PARK_AGE = timedelta(seconds=60)


class ObserverParkReport(BaseModel):
    """Software record of the observer's hardware "head parked + Z-retracted" limit.

    The actual limit is a GX16 signal (B); this is what the bridge consults to decide a safe
    handoff to pipetting. It is evidence of a hardware state, not the state itself.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    parked: bool
    z_retracted: bool
    reported_at: datetime
    source: str = ""  # e.g. "observer_mcu_limit"


class ObserverEnableState(BaseModel):
    """The SOFTWARE enable intent the bridge asserts to the (hardware, B) observer enable line.

    ``enable_intended`` is true ONLY while a valid ``observer_scan`` lease is held. This is
    not the motor enable state — the hardware backstop drops the line on lease release
    regardless of software. ``reasons`` names every cause the intent is withheld.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    enable_intended: bool
    reasons: tuple[str, ...]


class PipettingAdmission(BaseModel):
    """Whether the bridge may grant a pipetting lease given the observer handoff state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    admitted: bool
    blockers: tuple[str, ...]


def observer_enable_intent(observer_lock: BridgeLock, now: datetime) -> ObserverEnableState:
    """Derive the observer enable intent from the lease (fail-closed).

    Enable is intended only while a valid ``observer_scan`` lease is held; a wrong-kind,
    terminal, or expired lease withholds it. The bridge asserts this intent on the (hardware)
    enable line — but releasing the lease and dropping the line are the same event by design:
    no valid lease => no enable intent => the hardware backstop disables the motors.
    """
    reasons: list[str] = []
    if observer_lock.lease_kind != BridgeLeaseKind.OBSERVER_SCAN:
        reasons.append("not_an_observer_lease")
    if not lease_is_held(observer_lock, now):
        reasons.append("observer_lease_not_held")
    return ObserverEnableState(enable_intended=not reasons, reasons=tuple(reasons))


def pipetting_lease_admission(
    *,
    observer_lock: BridgeLock | None,
    park_report: ObserverParkReport | None,
    now: datetime,
    max_park_age: timedelta = DEFAULT_MAX_PARK_AGE,
) -> PipettingAdmission:
    """Refuse a pipetting lease until the observer has safely yielded the frame (fail-closed).

    Two-stage handoff:

    1. While an ``observer_scan`` lease is still held => ``observer_lease_active`` (this is the
       IN-C4 mutual exclusion seen from the OT-2 side; the lease layer also refuses it, this
       names *why* for the handoff caller).
    2. After release, until the observer reports a FRESH parked + Z-retracted limit => refuse.
       A released software lease does not prove the head physically parked, so the bridge
       requires the hardware limit readback before pipetting can move around the shared frame.

    Blockers (each separate, never one boolean): ``observer_lease_active``,
    ``observer_park_unconfirmed`` (no report), ``observer_not_parked``,
    ``observer_z_not_retracted``, ``observer_park_report_stale`` (older than ``max_park_age``),
    ``observer_park_report_in_future`` (clock-sanity guard against a forward-dated report).
    """
    blockers: list[str] = []

    if (
        observer_lock is not None
        and observer_lock.lease_kind == BridgeLeaseKind.OBSERVER_SCAN
        and lease_is_held(observer_lock, now)
    ):
        blockers.append("observer_lease_active")

    if park_report is None:
        blockers.append("observer_park_unconfirmed")
    else:
        if not park_report.parked:
            blockers.append("observer_not_parked")
        if not park_report.z_retracted:
            blockers.append("observer_z_not_retracted")
        if park_report.reported_at > now:
            blockers.append("observer_park_report_in_future")
        elif now - park_report.reported_at > max_park_age:
            blockers.append("observer_park_report_stale")

    return PipettingAdmission(admitted=not blockers, blockers=tuple(blockers))
