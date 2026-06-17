from __future__ import annotations

from aevum_smis import (
    ENTRY_POINT_GROUP,
    FROZEN_HEAD_BUS,
    SMIS_VERSION,
    HeadBusGroup,
    HeadBusSpec,
    ModuleManifest,
    SafetyClass,
    check_smis_version,
    validate_module_compatibility,
)


def _manifest(**overrides) -> ModuleManifest:
    base = dict(
        sku="obs-brightfield-4x",
        module_serial="SN-0001",
        hw_rev="A",
        smis_version=SMIS_VERSION,
        safety_class=SafetyClass.led,
        driver="aevum_modules.brightfield",
        mass_g=350.0,
        front_end_length_x_mm=21.0,
        front_end_width_y_mm=13.0,
        front_end_height_z_mm=28.0,
        focus_stroke_z_mm=12.0,
        barrel_diameter_mm=20.0,
    )
    base.update(overrides)
    return ModuleManifest(**base)


def _head_bus(**overrides) -> HeadBusSpec:
    data = FROZEN_HEAD_BUS.model_dump()
    data.update(overrides)
    return HeadBusSpec(**data)


def test_current_module_version_is_compatible() -> None:
    check = validate_module_compatibility(_manifest())
    assert check.compatible is True
    assert check.blockers == ()
    assert check.module_version == "0.1"
    assert check.platform_version == "0.1"
    assert check.head_bus_version == "0.1"
    assert check.driver_entry_point_group == ENTRY_POINT_GROUP
    assert check.same_major is True
    assert check.module_minor_supported is True
    assert check.head_bus_valid is True


def test_same_major_older_minor_is_accepted_by_semver_gate() -> None:
    ok, blockers, module, platform = check_smis_version("0.0", platform_version="0.1")
    assert ok is True
    assert blockers == ()
    assert str(module) == "0.0"
    assert str(platform) == "0.1"


def test_future_minor_fails_closed() -> None:
    check = validate_module_compatibility(_manifest(smis_version="0.2"))
    assert check.compatible is False
    assert check.same_major is True
    assert check.module_minor_supported is False
    assert "module_smis_minor_newer_than_platform" in check.blockers


def test_major_mismatch_fails_closed() -> None:
    check = validate_module_compatibility(_manifest(smis_version="1.0"))
    assert check.compatible is False
    assert check.same_major is False
    assert check.module_minor_supported is False
    assert "module_smis_major_incompatible" in check.blockers


def test_malformed_versions_fail_closed() -> None:
    check = validate_module_compatibility(_manifest(smis_version="0.1.0"))
    assert check.compatible is False
    assert "module_smis_version_malformed" in check.blockers

    ok, blockers, module, platform = check_smis_version("0.1", platform_version="dev")
    assert ok is False
    assert module is not None
    assert platform is None
    assert "platform_smis_version_malformed" in blockers


def test_head_bus_version_mismatch_fails_closed() -> None:
    check = validate_module_compatibility(
        _manifest(),
        head_bus=_head_bus(smis_version="0.2"),
    )
    assert check.compatible is False
    assert check.head_bus_version == "0.2"
    assert "head_bus_smis_version_mismatch" in check.blockers


def test_head_bus_structural_drift_fails_closed() -> None:
    lines = tuple(
        line for line in FROZEN_HEAD_BUS.lines if line.group != HeadBusGroup.one_wire
    )
    check = validate_module_compatibility(_manifest(), head_bus=_head_bus(lines=lines))
    assert check.compatible is False
    assert check.head_bus_valid is False
    assert "head_bus_missing_or_extra_signal_group" in check.blockers


def test_driver_entry_point_group_drift_fails_closed() -> None:
    check = validate_module_compatibility(
        _manifest(),
        driver_entry_point_group="aevum_modules_v2",
    )
    assert check.compatible is False
    assert "driver_entry_point_group_mismatch" in check.blockers
