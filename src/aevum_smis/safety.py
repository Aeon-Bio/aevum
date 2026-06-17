"""SMIS module detection + fail-closed source-enable gate (the safety spine).

On dock the platform reads the head's ``module.json`` (mirrored on the I2C ``0x50``
ID-EEPROM) and its 1-Wire DS28E07 cal-vault, then decides two things
(``docs/engineering/sensor_module_interface.md``, Electrical/Software sections):

1. ``detect_module`` -- is this a valid, genuine head? The stored EEPROM digest must
   match the recomputed manifest digest (anti-tamper), the declared envelope must fit
   the frozen contract, and the cal-vault challenge-response must verify (anti-counterfeit).
2. ``evaluate_source_enable`` -- may we energize its source? Fail-closed: no source
   unless the head is accepted, the hardware interlock loop is closed, and -- for a
   dangerous source class (Class-3B/4 laser, microwave) -- the cal-vault validates, so
   an uncertified head can never drive a Class-4 laser on our stage.

The cal-vault is modeled faithfully to the DS28E07: the factory provisions each head's
device secret as ``HMAC(master_secret, serial)``; the head answers a platform challenge
with ``HMAC(device_secret, challenge || manifest_sha256 || serial)``. A counterfeit head
without the manufacturing master secret cannot produce a valid response.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from pydantic import BaseModel, ConfigDict

from aevum_smis.manifest import (
    EnvelopeCheck,
    ModuleManifest,
    SafetyClass,
    SmisEnvelope,
    validate_manifest_envelope,
)

# Allowlist of demonstrably-safe source classes that may be energized WITHOUT a valid
# cal-vault (they carry no dangerous source). Everything else -- every laser class
# (including class_1, whose products routinely enclose a class-3B/4 emitter), microwave,
# and any class added in future -- REQUIRES cal-vault certification by default. This is
# deliberately a safe-allowlist, not a danger-denylist: a new enum value defaults to
# fail-closed (must be certified), and a counterfeit cannot dodge the gate by self-
# declaring a benign class, since only these two get the exemption.
CAL_VAULT_EXEMPT_CLASSES = frozenset({SafetyClass.passive, SafetyClass.led})


def issue_challenge() -> str:
    """A fresh CSPRNG nonce for one dock's cal-vault challenge.

    The platform MUST issue a fresh challenge per dock and never reuse one; a constant
    challenge lets a one-time bus capture of a genuine response replay forever.
    """
    return secrets.token_hex(16)


def _mac_message(challenge: str, manifest_sha256: str, serial: str) -> bytes:
    """Unambiguous, length-prefixed encoding so field boundaries cannot be confused."""
    parts = (challenge, manifest_sha256, serial)
    return b"".join(f"{len(p)}:".encode() + p.encode("utf-8") for p in parts)


def derive_device_secret(master_secret: bytes, serial: str) -> bytes:
    """Per-head factory secret provisioned into the DS28E07."""
    return hmac.new(master_secret, serial.encode("utf-8"), hashlib.sha256).digest()


def compute_cal_response(
    device_secret: bytes, *, challenge: str, manifest_sha256: str, serial: str
) -> str:
    """The response a genuine head's cal-vault returns to a fresh challenge."""
    message = _mac_message(challenge, manifest_sha256, serial)
    return hmac.new(device_secret, message, hashlib.sha256).hexdigest()


def verify_cal_vault(
    *,
    master_secret: bytes,
    serial: str,
    manifest_sha256: str,
    challenge: str,
    response: str,
) -> bool:
    """Constant-time verify the head's challenge-response against the master secret.

    The ``challenge`` MUST be a fresh per-dock nonce (see ``issue_challenge``); this
    function verifies a response but does not enforce nonce freshness -- that is the
    platform's obligation. A non-str response fails closed rather than raising.
    """
    if not isinstance(response, str):
        return False
    expected = compute_cal_response(
        derive_device_secret(master_secret, serial),
        challenge=challenge,
        manifest_sha256=manifest_sha256,
        serial=serial,
    )
    return hmac.compare_digest(expected, response)


class DetectResult(BaseModel):
    """Outcome of dock-time detection.

    ``accepted`` means "structurally valid head I can talk to" (digest matches, envelope
    fits) -- it is NOT "genuine". Genuineness is ``cal_vault_valid``. Downstream code that
    grants capability (motion, lease, source) must gate on ``cal_vault_valid`` for any
    non-exempt class, never on ``accepted`` alone.
    """

    model_config = ConfigDict(frozen=True)

    accepted: bool
    blockers: tuple[str, ...]
    digest_matches: bool
    envelope: EnvelopeCheck
    cal_vault_valid: bool
    safety_class: SafetyClass


class SourceEnableDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    allowed: bool
    blockers: tuple[str, ...]


def detect_module(
    manifest: ModuleManifest,
    *,
    stored_digest: str,
    master_secret: bytes,
    challenge: str,
    cal_response: str,
    envelope: SmisEnvelope | None = None,
) -> DetectResult:
    """Validate a head at dock: digest, envelope fit, and cal-vault.

    ``accepted`` requires the EEPROM digest to match (the manifest was not tampered) and
    the declared envelope to fit. The cal-vault result is always computed (the
    source-enable gate consumes it) but does not by itself block *detection* -- a genuine
    passive head with no cal-vault still docks; it only gates energizing a source.
    """
    env = (
        validate_manifest_envelope(manifest, envelope)
        if envelope is not None
        else validate_manifest_envelope(manifest)
    )
    digest_matches = hmac.compare_digest(manifest.manifest_sha256(), stored_digest)
    cal_valid = verify_cal_vault(
        master_secret=master_secret,
        serial=manifest.module_serial,
        manifest_sha256=manifest.manifest_sha256(),
        challenge=challenge,
        response=cal_response,
    )

    blockers: list[str] = []
    if not digest_matches:
        blockers.append("manifest_digest_mismatch")
    if not env.fits:
        blockers.append("manifest_envelope_does_not_fit")

    return DetectResult(
        accepted=not blockers,
        blockers=tuple(blockers),
        digest_matches=digest_matches,
        envelope=env,
        cal_vault_valid=cal_valid,
        safety_class=manifest.safety_class,
    )


def evaluate_source_enable(
    detect: DetectResult,
    *,
    interlock_closed: bool,
) -> SourceEnableDecision:
    """Fail-closed source-enable gate.

    A source is energized only if the head was accepted at detection, the hardware
    interlock loop is closed, and -- for a dangerous source class -- the cal-vault
    validates. Software can additionally refuse but can never override the hardware
    interlock to enable; this gate is the software half.
    """
    blockers: list[str] = []
    if not detect.accepted:
        blockers.append("module_not_accepted_at_detection")
    if not interlock_closed:
        blockers.append("hardware_interlock_open")
    # Require cal-vault for every class EXCEPT the safe allowlist -- so an unknown/future
    # class and a counterfeit declaring a non-exempt class both fail closed.
    if (
        detect.safety_class not in CAL_VAULT_EXEMPT_CLASSES
        and not detect.cal_vault_valid
    ):
        blockers.append("uncertified_head_for_dangerous_source_class")

    return SourceEnableDecision(allowed=not blockers, blockers=tuple(blockers))
