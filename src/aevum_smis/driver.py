"""SMIS module-driver ABI: ``acquire(well, lease) -> Evidence``, one orchestrator, N modalities.

Every modality head implements one driver interface (the Software section of
``docs/engineering/sensor_module_interface.md``). The orchestrator loop -- for each
well: ensure lease, drive the stage, ``acquire(well)``, write evidence -- never
changes per modality; a brightfield head returns an image stack, a Raman head a
spectrum, an impedance head a Z(f) sweep, all as the same immutable
``ModuleEvidence`` packet.

Coupling is deliberately structural: ``MotionLease`` is a Protocol the OT-2 bridge's
``BridgeLock`` already satisfies (session_id/owner_id/state/lease_expires_at), so this
package does not import the bridge. Mapping ``ModuleEvidence`` into the bridge's
durable ``EvidencePacket`` store is a later cross-package cycle (IN-C5); the contract is
frozen here.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from importlib import metadata
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from aevum_smis.manifest import ModuleManifest

ENTRY_POINT_GROUP = "aevum_modules"

# Mirror of ot2_harness.core.lock.TERMINAL_LOCK_STATES: the harness holds a lease unless
# its state is terminal, so SMIS must use the SAME predicate (terminal-exclusion), not a
# stricter "== active" literal that would wrongly reject a valid non-active, non-terminal
# state (e.g. a session mirrored as high_z_ready). Kept as a local copy so SMIS does not
# import the bridge; a drift test pins them equal.
TERMINAL_LEASE_STATES = frozenset({"closed", "failed", "released"})


@runtime_checkable
class MotionLease(Protocol):
    """The minimal lease surface ``acquire`` needs; the bridge's BridgeLock satisfies it."""

    session_id: str
    owner_id: str
    state: str
    lease_expires_at: datetime


def lease_is_valid(lease: MotionLease, *, now: datetime) -> bool:
    """A lease authorizes acquisition only while non-terminal and unexpired (fail-closed).

    Matches the bridge's own rule (held unless terminal), not a stricter == active.
    """
    return lease.state not in TERMINAL_LEASE_STATES and lease.lease_expires_at > now


@runtime_checkable
class PlatformCtx(Protocol):
    """Platform services a driver uses during ``on_dock`` for tiered registration.

    Minimal v0.1 surface (the frozen ABI passes this handle); fleshed out as the
    stage/fiducial services land.
    """

    def find_fiducials(self) -> int: ...


class LeaseError(RuntimeError):
    """Raised when acquisition is attempted without a valid motion lease."""


class WellTarget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    well_id: str = Field(min_length=1)
    x_mm: float
    y_mm: float


class RegistrationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tier: str  # "A" trust-coupling / "B" re-fiducial / "C" full re-cal
    ok: bool
    fiducials_used: int = 0
    residual_um: float | None = None


class HealthReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ok: bool
    detail: str = ""


class ModuleEvidence(BaseModel):
    """The immutable packet a driver returns from one well, for any modality.

    Carries the provenance the bridge's durable EvidencePacket will need at the IN-C5
    mapping (session/command ids, calibration ref), so freezing this contract does not
    force a later change to recover provenance.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    module_serial: str
    manifest_sha256: str
    modality: str
    well_id: str
    payload_kind: str  # e.g. image_stack / spectrum / impedance_sweep
    payload_ref: str  # path or handle to the captured artifact
    lease_owner: str
    session_id: str = ""
    command_id: str = ""
    calibration_ref: str = ""  # 1-Wire DS28E07 cal-vault digest (source-enable gate)
    captured_at: datetime = Field(default_factory=datetime.now)


@runtime_checkable
class ModuleDriver(Protocol):
    """The one ABI every modality head implements."""

    manifest: ModuleManifest

    def on_dock(self, platform: PlatformCtx) -> RegistrationResult: ...

    def configure(self, params: dict[str, object]) -> None: ...

    def acquire(self, well: WellTarget, lease: MotionLease) -> ModuleEvidence: ...

    def health(self) -> HealthReport: ...

    def on_undock(self) -> None: ...


def run_scan(
    driver: ModuleDriver,
    wells: list[WellTarget],
    lease: MotionLease,
    *,
    clock: Callable[[], datetime] = datetime.now,
) -> list[ModuleEvidence]:
    """The polymorphic orchestrator loop: lease-gated acquire over every well.

    Fail-closed for the acquisition's whole duration, not just its start: the lease is
    checked against the live ``clock`` BEFORE each acquire and AGAIN after it returns. If
    the lease lapses while a (possibly slow) acquire runs, the capture is discarded and
    the scan raises -- no evidence is retained without authority for its full duration.
    The loop body is identical for every modality -- this is the platform payoff.
    """
    evidence: list[ModuleEvidence] = []
    for well in wells:
        if not lease_is_valid(lease, now=clock()):
            raise LeaseError(
                f"motion lease not valid before acquiring well {well.well_id}"
            )
        captured = driver.acquire(well, lease)
        if not lease_is_valid(lease, now=clock()):
            raise LeaseError(
                f"motion lease lapsed during acquisition of well {well.well_id}; "
                "capture discarded"
            )
        evidence.append(captured)
    return evidence


class DriverRegistry:
    """Maps a modality name to a driver factory; the platform never hard-codes a modality."""

    def __init__(self) -> None:
        self._factories: dict[str, type[ModuleDriver]] = {}

    def register(self, name: str, factory: type[ModuleDriver]) -> None:
        if name in self._factories:
            raise ValueError(f"driver already registered: {name}")
        self._factories[name] = factory

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))

    def create(self, name: str, manifest: ModuleManifest) -> ModuleDriver:
        if name not in self._factories:
            raise KeyError(f"no driver registered for {name}")
        return self._factories[name](manifest)  # type: ignore[call-arg]

    def load_entry_points(
        self,
    ) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
        """Discover drivers published as ``aevum_modules.<modality>`` entry points.

        Returns ``(loaded, failures)``. A single malformed third-party plugin must not
        brick discovery of every head, so per-entry-point failures (bad import, not a
        class, duplicate) are isolated and reported as ``(name, error)`` pairs.
        """
        loaded: list[str] = []
        failures: list[tuple[str, str]] = []
        for ep in metadata.entry_points(group=ENTRY_POINT_GROUP):
            try:
                factory = ep.load()
                if not isinstance(factory, type):
                    raise TypeError(f"entry point {ep.name} is not a class")
                self.register(ep.name, factory)
                loaded.append(ep.name)
            except Exception as exc:  # noqa: BLE001 -- isolate one bad plugin
                failures.append((ep.name, str(exc)))
        return tuple(loaded), tuple(failures)
