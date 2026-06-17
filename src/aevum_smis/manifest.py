"""SMIS module manifest schema + falsifiable envelope re-check.

A SMIS head ships a ``module.json`` manifest (mirrored on its I2C ``0x50``
ID-EEPROM, see ``docs/engineering/sensor_module_interface.md``). On dock the
platform re-runs the same falsifiable envelope arithmetic the observer CAD makes
test-failable -- barrel diameter vs the objective keepout, the head footprint vs
the keepout, the vertical Z-budget closure, and the mass budget -- so a manifest
claiming an envelope it does not fit is rejected at dock rather than discovered by
a crash.

The frozen ``SmisEnvelope`` numbers mirror the observer dry-bay params in
``cad/one_row_coupon.params.json`` (``carriage_height_z``,
``carriage_top_clearance_z``, ``objective_keepout_diameter``, the front-end swept
body). A CAD assert cross-checking the two against drift is a separate cycle
(OC-A10); here they are the platform-side source of truth for SMIS v0.1.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

SMIS_VERSION = "0.1"


class SmisEnvelope(BaseModel):
    """The frozen SMIS v0.1 dock/dry-bay envelope a module must fit.

    Mirrors ``cad/one_row_coupon.params.json`` observer_robotics + dry_bay.
    Frozen: a change is a SMIS-major bump that re-validates every head.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    z_budget_mm: float = 62.0  # carriage_height_z, usable Z below the dock plane
    # The vertical-budget clearance term: the live CAD mirrors this with
    # front_end_top_clearance_z (falling back to carriage_top_clearance_z); both are
    # 8.0 today but are distinct param keys, so the cross-check assert (OC-A10) tracks
    # them against drift.
    front_face_clearance_mm: float = 8.0
    objective_keepout_diameter_mm: float = 32.0
    # OC-A15: the BINDING scan-axis footprint limit is the tightest of the standoff-leg
    # corridor and the milled dry-bay wall (nearly co-located: the bay hi-wall is ~0.1 mm
    # inside the leg corridor), NOT the looser Ø32 objective keepout. Every modality head
    # must thread it, so a head that clears the keepout but exceeds it (e.g. a Ø25 barrel)
    # still strikes. 21.2 mm is the last footprint clearing EVERY wall in the CAD model
    # (clears_traverse flips ~21.21 mm; a 21 mm head has ~0.02 mm binding / ~0.12 mm
    # corridor margin). Placeholder; Stage-0-gated by
    # observer_leg_corridor_objective_metrology.md.
    scan_corridor_footprint_max_mm: float = 21.2
    swept_body_length_x_mm: float = 120.0
    swept_body_width_y_mm: float = 347.5
    swept_body_height_z_mm: float = 40.0
    mass_budget_g: float = 900.0


FROZEN_ENVELOPE = SmisEnvelope()


class SafetyClass(StrEnum):
    """Module source-energy class; gates source-enable at the dock."""

    passive = "passive"  # no active source (brightfield, phase)
    led = "led"  # incoherent LED illumination only
    laser_class_1 = "laser_class_1"
    laser_class_3b = "laser_class_3b"
    laser_class_4 = "laser_class_4"
    microwave = "microwave"  # NV ODMR drive


class ModuleManifest(BaseModel):
    """A SMIS head's ``module.json`` / EEPROM identity + declared geometry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Identity (mirrors the I2C 0x50 ID-EEPROM).
    sku: str = Field(min_length=1)
    module_serial: str = Field(min_length=1)
    hw_rev: str = Field(min_length=1)
    # Required, NOT defaulted to the platform's SMIS_VERSION: an incoming head must
    # declare its own version honestly so the semver compatibility gate can fail
    # closed on incompatible heads.
    smis_version: str = Field(min_length=1)
    safety_class: SafetyClass
    driver: str = Field(min_length=1)  # entry point: aevum_modules.<modality>

    # Registration (where this head's optical axis sits relative to the dock plane).
    axis_offset_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    parfocal_z_mm: float = 0.0
    requires_post_dock_autofocus: bool = False

    # Mass / centre of gravity -- gate the scan-speed profile.
    mass_g: float = Field(gt=0.0)
    cg_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Declared envelope geometry the platform re-checks against the frozen contract.
    front_end_length_x_mm: float = Field(gt=0.0)
    front_end_width_y_mm: float = Field(gt=0.0)
    front_end_height_z_mm: float = Field(gt=0.0)
    focus_stroke_z_mm: float = Field(ge=0.0)
    service_margin_z_mm: float = Field(default=0.0, ge=0.0)
    barrel_diameter_mm: float = Field(gt=0.0)

    def manifest_sha256(self) -> str:
        """Digest over the canonical manifest content (the EEPROM stores this)."""
        payload = json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def from_json(cls, text: str) -> ModuleManifest:
        return cls.model_validate_json(text)


class EnvelopeCheck(BaseModel):
    """Result of re-checking a manifest's declared geometry vs the frozen envelope."""

    model_config = ConfigDict(frozen=True)

    fits: bool
    blockers: tuple[str, ...]
    barrel_fits_keepout: bool
    barrel_overflow_mm: float
    footprint_circumscribed_diameter_mm: float
    footprint_fits_keepout: bool
    scan_footprint_mm: float
    scan_footprint_fits_corridor: bool
    vertical_budget_required_mm: float
    vertical_budget_closes: bool
    mass_within_budget: bool


def validate_manifest_envelope(
    manifest: ModuleManifest,
    envelope: SmisEnvelope = FROZEN_ENVELOPE,
) -> EnvelopeCheck:
    """Re-run the falsifiable envelope arithmetic the observer CAD makes test-failable.

    A module is accepted only if its round barrel and its head bounding box both
    fit the objective keepout, its vertical stack closes the Z budget, and its mass
    is within budget. Each failure adds a named blocker so the dock refuses an
    over-claiming head instead of crashing into the bay.
    """
    keepout = float(envelope.objective_keepout_diameter_mm)

    # Bare <= against 3-dp-rounded values, identical to the observer CAD's two
    # falsifiable checks (no fit tolerance there): a head exactly at budget passes,
    # 0.001 over fails.
    barrel_overflow = max(0.0, float(manifest.barrel_diameter_mm) - keepout)
    barrel_fits = float(manifest.barrel_diameter_mm) <= keepout

    # Circumscribed diameter of the rectangular head cross-section -- the
    # conservative bound the observer swept-body check uses (front_end_fits_objective_keepout).
    footprint_d = round(
        (manifest.front_end_length_x_mm ** 2 + manifest.front_end_width_y_mm ** 2)
        ** 0.5,
        3,
    )
    footprint_fits = footprint_d <= keepout

    # OC-A15: the scan-axis footprint (the wider of the round barrel and the head body on
    # the scan axis) must thread the standoff-leg corridor, a tighter wall than the
    # keepout. A head that clears the keepout but exceeds the corridor still strikes the
    # legs -- this rejects it at dock for every modality.
    corridor_max = float(envelope.scan_corridor_footprint_max_mm)
    scan_footprint = round(
        max(float(manifest.barrel_diameter_mm), float(manifest.front_end_length_x_mm)),
        3,
    )
    scan_footprint_fits = scan_footprint <= corridor_max

    vertical_required = round(
        float(envelope.front_face_clearance_mm)
        + float(manifest.front_end_height_z_mm)
        + float(manifest.focus_stroke_z_mm)
        + float(manifest.service_margin_z_mm),
        3,
    )
    vertical_closes = vertical_required <= float(envelope.z_budget_mm)

    mass_within = float(manifest.mass_g) <= float(envelope.mass_budget_g)

    blockers: list[str] = []
    if not barrel_fits:
        blockers.append("barrel_exceeds_objective_keepout")
    if not footprint_fits:
        blockers.append("head_footprint_exceeds_objective_keepout")
    if not scan_footprint_fits:
        blockers.append("scan_footprint_exceeds_leg_corridor")
    if not vertical_closes:
        blockers.append("vertical_budget_exceeds_dock_z")
    if not mass_within:
        blockers.append("mass_exceeds_budget")

    return EnvelopeCheck(
        fits=not blockers,
        blockers=tuple(blockers),
        barrel_fits_keepout=barrel_fits,
        barrel_overflow_mm=round(barrel_overflow, 3),
        footprint_circumscribed_diameter_mm=footprint_d,
        footprint_fits_keepout=footprint_fits,
        scan_footprint_mm=scan_footprint,
        scan_footprint_fits_corridor=scan_footprint_fits,
        vertical_budget_required_mm=vertical_required,
        vertical_budget_closes=vertical_closes,
        mass_within_budget=mass_within,
    )
