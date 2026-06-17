"""SMIS v0.1 compatibility policy.

SMIS versions gate frozen platform contracts: mechanical envelope, HEAD-BUS,
driver ABI, manifest schema, and source safety. A module may only dock when the
platform can interpret the contracts it declares. Unknown future contracts fail
closed rather than being treated as compatible by accident.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from aevum_smis.driver import ENTRY_POINT_GROUP
from aevum_smis.head_bus import FROZEN_HEAD_BUS, HeadBusSpec, validate_head_bus_spec
from aevum_smis.manifest import SMIS_VERSION, ModuleManifest


class SmisVersion(BaseModel):
    """Parsed SMIS semantic version.

    SMIS currently uses ``major.minor``. Patch/build identifiers are intentionally
    rejected until a concrete migration policy needs them.
    """

    model_config = ConfigDict(frozen=True)

    major: int
    minor: int

    @classmethod
    def parse(cls, value: str) -> SmisVersion:
        parts = value.split(".")
        if len(parts) != 2 or not all(part.isdecimal() for part in parts):
            raise ValueError("SMIS version must be major.minor")
        major, minor = (int(part) for part in parts)
        return cls(major=major, minor=minor)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


class CompatibilityCheck(BaseModel):
    """Result of checking a module against the platform's frozen SMIS contracts."""

    model_config = ConfigDict(frozen=True)

    compatible: bool
    blockers: tuple[str, ...]
    module_version: str
    platform_version: str
    head_bus_version: str
    driver_entry_point_group: str
    same_major: bool
    module_minor_supported: bool
    head_bus_valid: bool


def check_smis_version(
    module_version: str,
    *,
    platform_version: str = SMIS_VERSION,
) -> tuple[bool, tuple[str, ...], SmisVersion | None, SmisVersion | None]:
    """Fail-closed SMIS semver gate.

    Same major is required. A module minor newer than the platform is rejected
    because it may depend on additive contracts the platform has not learned yet.
    Older/current minors are accepted by this gate; schema/envelope/HEAD-BUS gates
    still run separately.
    """

    blockers: list[str] = []
    try:
        module = SmisVersion.parse(module_version)
    except ValueError:
        blockers.append("module_smis_version_malformed")
        module = None
    try:
        platform = SmisVersion.parse(platform_version)
    except ValueError:
        blockers.append("platform_smis_version_malformed")
        platform = None

    if module is None or platform is None:
        return False, tuple(blockers), module, platform

    if module.major != platform.major:
        blockers.append("module_smis_major_incompatible")
    if module.major == platform.major and module.minor > platform.minor:
        blockers.append("module_smis_minor_newer_than_platform")

    return not blockers, tuple(blockers), module, platform


def validate_module_compatibility(
    manifest: ModuleManifest,
    *,
    head_bus: HeadBusSpec = FROZEN_HEAD_BUS,
    platform_version: str = SMIS_VERSION,
    driver_entry_point_group: str = ENTRY_POINT_GROUP,
) -> CompatibilityCheck:
    """Check the SMIS compatibility envelope before loading a driver or energizing."""

    version_ok, version_blockers, module, platform = check_smis_version(
        manifest.smis_version,
        platform_version=platform_version,
    )
    head_bus_check = validate_head_bus_spec(head_bus)
    blockers = list(version_blockers)
    if head_bus.smis_version != platform_version:
        blockers.append("head_bus_smis_version_mismatch")
    blockers.extend(head_bus_check.blockers)
    if driver_entry_point_group != ENTRY_POINT_GROUP:
        blockers.append("driver_entry_point_group_mismatch")

    same_major = bool(
        module is not None
        and platform is not None
        and module.major == platform.major
    )
    minor_supported = bool(
        module is not None
        and platform is not None
        and module.major == platform.major
        and module.minor <= platform.minor
    )

    return CompatibilityCheck(
        compatible=version_ok
        and not blockers
        and head_bus_check.valid
        and driver_entry_point_group == ENTRY_POINT_GROUP,
        blockers=tuple(blockers),
        module_version=manifest.smis_version,
        platform_version=platform_version,
        head_bus_version=head_bus.smis_version,
        driver_entry_point_group=driver_entry_point_group,
        same_major=same_major,
        module_minor_supported=minor_supported,
        head_bus_valid=head_bus_check.valid,
    )
