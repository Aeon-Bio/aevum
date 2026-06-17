"""IN-C7 / HX3: the SOFTWARE half of the two-layer observer<->OT-2 interlock.

Proves the two software obligations:
- the observer enable INTENT tracks the lease (held => intended; released/expired/terminal/
  wrong-kind => withheld), and
- a pipetting lease is refused while the observer lease is active AND, after release, until a
  fresh parked + Z-retracted limit is reported.

The hardware enable line and the physical limit switch are B; these tests cover only the
software intent/handoff, never a claim that motors are de-energized.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from aevum_ot2.core.models import BridgeLeaseKind, BridgeLock
from aevum_ot2.core.observer_interlock import (
    DEFAULT_MAX_PARK_AGE,
    ObserverParkReport,
    observer_enable_intent,
    pipetting_lease_admission,
)

ROBOT = "http://ot2.local:31950"
NOW = datetime(2026, 6, 16, 12, 0, 0)


def _observer_lock(*, state: str = "active", expires_in_min: float = 5.0) -> BridgeLock:
    return BridgeLock(
        robot_url=ROBOT,
        session_id="obs-sess",
        owner_id="observer",
        lease_started_at=NOW,
        lease_expires_at=NOW + timedelta(minutes=expires_in_min),
        state=state,
        lease_kind=BridgeLeaseKind.OBSERVER_SCAN,
    )


def _pipetting_lock() -> BridgeLock:
    return BridgeLock(
        robot_url=ROBOT,
        session_id="ot2-sess",
        owner_id="pipettor",
        lease_started_at=NOW,
        lease_expires_at=NOW + timedelta(minutes=5),
        state="active_no_motion",
    )


def _park(
    *, parked: bool = True, z_retracted: bool = True, age_s: float = 5.0
) -> ObserverParkReport:
    return ObserverParkReport(
        parked=parked,
        z_retracted=z_retracted,
        reported_at=NOW - timedelta(seconds=age_s),
        source="observer_mcu_limit",
    )


# --- enable intent ------------------------------------------------------------------------


def test_enable_intended_only_while_observer_lease_held() -> None:
    state = observer_enable_intent(_observer_lock(), NOW)
    assert state.enable_intended is True
    assert state.reasons == ()


@pytest.mark.parametrize("lock_state", ["closed", "failed", "released"])
def test_enable_intent_drops_on_terminal_lease(lock_state: str) -> None:
    state = observer_enable_intent(_observer_lock(state=lock_state), NOW)
    assert state.enable_intended is False
    assert "observer_lease_not_held" in state.reasons


def test_enable_intent_drops_on_expiry() -> None:
    state = observer_enable_intent(_observer_lock(expires_in_min=-1.0), NOW)
    assert state.enable_intended is False
    assert "observer_lease_not_held" in state.reasons


def test_enable_intent_rejects_a_pipetting_lease() -> None:
    # a pipetting lease must never assert observer enable intent
    state = observer_enable_intent(_pipetting_lock(), NOW)
    assert state.enable_intended is False
    assert "not_an_observer_lease" in state.reasons


# --- pipetting admission handoff ----------------------------------------------------------


def test_pipetting_refused_while_observer_lease_active() -> None:
    admission = pipetting_lease_admission(
        observer_lock=_observer_lock(), park_report=_park(), now=NOW
    )
    assert admission.admitted is False
    assert "observer_lease_active" in admission.blockers


def test_pipetting_refused_after_release_until_park_confirmed() -> None:
    # software lease released, but no hardware parked report yet => still refused
    admission = pipetting_lease_admission(
        observer_lock=_observer_lock(state="released"), park_report=None, now=NOW
    )
    assert admission.admitted is False
    assert admission.blockers == ("observer_park_unconfirmed",)


def test_pipetting_refused_if_not_parked_or_not_retracted() -> None:
    not_parked = pipetting_lease_admission(
        observer_lock=_observer_lock(state="released"),
        park_report=_park(parked=False),
        now=NOW,
    )
    assert not_parked.admitted is False
    assert "observer_not_parked" in not_parked.blockers

    not_retracted = pipetting_lease_admission(
        observer_lock=_observer_lock(state="released"),
        park_report=_park(z_retracted=False),
        now=NOW,
    )
    assert not_retracted.admitted is False
    assert "observer_z_not_retracted" in not_retracted.blockers


def test_pipetting_refused_if_park_report_stale() -> None:
    stale_age = DEFAULT_MAX_PARK_AGE.total_seconds() + 1.0
    admission = pipetting_lease_admission(
        observer_lock=_observer_lock(state="released"),
        park_report=_park(age_s=stale_age),
        now=NOW,
    )
    assert admission.admitted is False
    assert "observer_park_report_stale" in admission.blockers


def test_pipetting_refused_if_park_report_in_future() -> None:
    # clock-sanity: a forward-dated report cannot satisfy freshness
    admission = pipetting_lease_admission(
        observer_lock=_observer_lock(state="released"),
        park_report=_park(age_s=-30.0),
        now=NOW,
    )
    assert admission.admitted is False
    assert "observer_park_report_in_future" in admission.blockers


def test_pipetting_admitted_after_release_with_fresh_parked_report() -> None:
    admission = pipetting_lease_admission(
        observer_lock=_observer_lock(state="released"),
        park_report=_park(),
        now=NOW,
    )
    assert admission.admitted is True
    assert admission.blockers == ()


def test_admission_with_no_observer_lock_still_requires_a_park_report() -> None:
    # fail-closed: even with no observer lock on record, a pipetting lease needs proof the
    # head is parked (a booted observer reports parked+retracted), then it admits.
    unconfirmed = pipetting_lease_admission(
        observer_lock=None, park_report=None, now=NOW
    )
    assert unconfirmed.admitted is False
    assert "observer_park_unconfirmed" in unconfirmed.blockers

    confirmed = pipetting_lease_admission(observer_lock=None, park_report=_park(), now=NOW)
    assert confirmed.admitted is True
