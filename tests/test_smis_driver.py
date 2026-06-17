from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest

from aevum_smis import (
    DriverRegistry,
    HealthReport,
    LeaseError,
    ModuleDriver,
    ModuleEvidence,
    ModuleManifest,
    RegistrationResult,
    SafetyClass,
    WellTarget,
    lease_is_valid,
    run_scan,
)
from aevum_smis.driver import TERMINAL_LEASE_STATES

_NOW = datetime(2026, 6, 14, 12, 0, 0)


def _clock():
    return _NOW


@dataclass
class _Lease:
    """A duck-typed lease with the same surface as the bridge's BridgeLock."""

    session_id: str = "sess-1"
    owner_id: str = "observer"
    state: str = "active"
    lease_expires_at: datetime = _NOW + timedelta(minutes=5)


class _FakePlatform:
    def find_fiducials(self) -> int:
        return 1


def _manifest(modality: str, driver: str) -> ModuleManifest:
    return ModuleManifest(
        sku=f"obs-{modality}",
        module_serial=f"SN-{modality}",
        hw_rev="A",
        smis_version="0.1",
        safety_class=SafetyClass.led,
        driver=driver,
        mass_g=350.0,
        front_end_length_x_mm=21.0,
        front_end_width_y_mm=13.0,
        front_end_height_z_mm=28.0,
        focus_stroke_z_mm=12.0,
        barrel_diameter_mm=20.0,  # slim RMS 4x that threads the leg corridor (OC-A15)
    )


class _BaseDriver:
    """Reference driver; subclasses only differ in the payload they return."""

    modality = "base"
    payload_kind = "blob"

    def __init__(self, manifest: ModuleManifest) -> None:
        self.manifest = manifest
        self.configured: dict[str, object] = {}

    def on_dock(self, platform) -> RegistrationResult:
        return RegistrationResult(tier="A", ok=True, fiducials_used=platform.find_fiducials())

    def configure(self, params: dict[str, object]) -> None:
        self.configured = dict(params)

    def acquire(self, well: WellTarget, lease) -> ModuleEvidence:
        return ModuleEvidence(
            module_serial=self.manifest.module_serial,
            manifest_sha256=self.manifest.manifest_sha256(),
            modality=self.modality,
            well_id=well.well_id,
            payload_kind=self.payload_kind,
            payload_ref=f"data/{self.modality}/{well.well_id}",
            lease_owner=lease.owner_id,
            session_id=lease.session_id,
            captured_at=_NOW,
        )

    def health(self) -> HealthReport:
        return HealthReport(ok=True)

    def on_undock(self) -> None:
        return None


class _BrightfieldDriver(_BaseDriver):
    modality = "brightfield"
    payload_kind = "image_stack"


class _RamanDriver(_BaseDriver):
    modality = "raman"
    payload_kind = "spectrum"


def _wells() -> list[WellTarget]:
    return [
        WellTarget(well_id="A1", x_mm=14.38, y_mm=11.24),
        WellTarget(well_id="A2", x_mm=23.38, y_mm=11.24),
    ]


def test_reference_driver_has_the_module_driver_member_names() -> None:
    # runtime_checkable isinstance verifies member NAMES are present, not method
    # signatures -- signature conformance is a static-typing (mypy) concern.
    driver = _BrightfieldDriver(_manifest("brightfield", "aevum_modules.brightfield"))
    assert isinstance(driver, ModuleDriver)


def test_on_dock_receives_the_platform_context() -> None:
    driver = _BrightfieldDriver(_manifest("brightfield", "aevum_modules.brightfield"))
    result = driver.on_dock(_FakePlatform())
    assert result.tier == "A"
    assert result.fiducials_used == 1  # came from the platform handle


def test_one_orchestrator_runs_two_modalities_unchanged() -> None:
    lease = _Lease()
    for cls, modality, kind in [
        (_BrightfieldDriver, "brightfield", "image_stack"),
        (_RamanDriver, "raman", "spectrum"),
    ]:
        driver = cls(_manifest(modality, f"aevum_modules.{modality}"))
        evidence = run_scan(driver, _wells(), lease, clock=_clock)
        assert [e.well_id for e in evidence] == ["A1", "A2"]
        assert {e.payload_kind for e in evidence} == {kind}
        for e in evidence:
            assert e.modality == modality
            assert e.module_serial == f"SN-{modality}"
            assert e.manifest_sha256 == driver.manifest.manifest_sha256()
            assert e.lease_owner == "observer"
            assert e.session_id == "sess-1"


def test_run_scan_is_fail_closed_on_an_invalid_lease() -> None:
    driver = _BrightfieldDriver(_manifest("brightfield", "aevum_modules.brightfield"))
    expired = _Lease(lease_expires_at=_NOW - timedelta(seconds=1))
    with pytest.raises(LeaseError):
        run_scan(driver, _wells(), expired, clock=_clock)
    released = _Lease(state="released")
    with pytest.raises(LeaseError):
        run_scan(driver, _wells(), released, clock=_clock)


def test_run_scan_discards_capture_if_lease_lapses_during_acquire() -> None:
    # The lease is valid at acquire START but expires before it returns; the capture
    # must be discarded (not retained without authority for its duration).
    driver = _BrightfieldDriver(_manifest("brightfield", "aevum_modules.brightfield"))
    lease = _Lease(lease_expires_at=_NOW + timedelta(seconds=1))
    times = iter([_NOW, _NOW + timedelta(seconds=5)])  # before: valid; after: expired

    def advancing_clock():
        return next(times)

    with pytest.raises(LeaseError, match="lapsed during acquisition"):
        run_scan(driver, _wells(), lease, clock=advancing_clock)


def test_lease_validity_matches_terminal_exclusion_not_active_literal() -> None:
    assert lease_is_valid(_Lease(), now=_NOW) is True
    # A non-active but NON-terminal state is still held (the bridge's rule), NOT rejected.
    assert lease_is_valid(_Lease(state="high_z_ready"), now=_NOW) is True
    # Terminal states are invalid.
    for terminal in ("closed", "failed", "released"):
        assert lease_is_valid(_Lease(state=terminal), now=_NOW) is False
    # Exactly expired is invalid (strict >).
    assert lease_is_valid(_Lease(lease_expires_at=_NOW), now=_NOW) is False


def test_terminal_lease_states_mirror_the_bridge() -> None:
    # Drift guard: SMIS's terminal set must equal the bridge's authoritative set.
    from aevum_ot2.core.lock import TERMINAL_LOCK_STATES

    assert TERMINAL_LEASE_STATES == set(TERMINAL_LOCK_STATES)


def test_registry_register_create_and_unknown() -> None:
    registry = DriverRegistry()
    registry.register("brightfield", _BrightfieldDriver)
    registry.register("raman", _RamanDriver)
    assert registry.names() == ("brightfield", "raman")
    created = registry.create("brightfield", _manifest("brightfield", "x"))
    assert isinstance(created, _BrightfieldDriver)
    with pytest.raises(KeyError):
        registry.create("nv", _manifest("nv", "x"))
    with pytest.raises(ValueError):
        registry.register("brightfield", _RamanDriver)  # duplicate


def test_bridge_lock_shaped_object_satisfies_motion_lease() -> None:
    from aevum_ot2.core.models import BridgeLock

    lock = BridgeLock(
        robot_url="http://robot.local",
        session_id="sess-1",
        owner_id="observer",
        lease_started_at=_NOW,
        lease_expires_at=_NOW + timedelta(minutes=5),
        state="active",
    )
    assert lease_is_valid(lock, now=_NOW) is True
    driver = _BrightfieldDriver(_manifest("brightfield", "aevum_modules.brightfield"))
    evidence = run_scan(driver, _wells(), lock, clock=_clock)
    assert evidence[0].lease_owner == "observer"
