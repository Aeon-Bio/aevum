from __future__ import annotations

from aevum_smis import (
    ModuleManifest,
    RegistrationResult,
    SafetyClass,
    compute_cal_response,
    derive_device_secret,
    detect_module,
    evaluate_source_enable,
    issue_challenge,
    validate_module_compatibility,
    validate_registration_result,
    verify_cal_vault,
)

_MASTER = b"aevum-factory-master-secret-v1"
_CHALLENGE = issue_challenge()


def _manifest(safety_class: SafetyClass = SafetyClass.led, **overrides) -> ModuleManifest:
    base = dict(
        sku="obs-head",
        module_serial="SN-0001",
        hw_rev="A",
        smis_version="0.1",
        safety_class=safety_class,
        driver="aevum_modules.head",
        mass_g=350.0,
        # Scan-axis footprint kept inside the CORRECTED 15.56 mm leg corridor (OC-A15)
        # so these tests exercise SAFETY logic rather than re-litigating the envelope.
        # Not physically realizable with an RMS thread (~Ø20.32 min) -- the real head's
        # corridor rejection is owned by tests/test_smis_manifest.py, in
        # test_reference_rms_4x_head_is_rejected_by_the_corrected_leg_corridor.
        front_end_length_x_mm=15.0,
        front_end_width_y_mm=13.0,
        front_end_height_z_mm=28.0,
        focus_stroke_z_mm=12.0,
        barrel_diameter_mm=15.0,
    )
    base.update(overrides)
    return ModuleManifest(**base)


def _genuine_response(manifest: ModuleManifest) -> str:
    return compute_cal_response(
        derive_device_secret(_MASTER, manifest.module_serial),
        challenge=_CHALLENGE,
        manifest_sha256=manifest.manifest_sha256(),
        serial=manifest.module_serial,
    )


def _detect(manifest, *, stored_digest=None, cal_response=None):
    return detect_module(
        manifest,
        stored_digest=stored_digest or manifest.manifest_sha256(),
        master_secret=_MASTER,
        challenge=_CHALLENGE,
        cal_response=cal_response if cal_response is not None else _genuine_response(manifest),
    )


def test_cal_vault_round_trip_and_counterfeit() -> None:
    m = _manifest()
    good = _genuine_response(m)
    assert verify_cal_vault(
        master_secret=_MASTER,
        serial=m.module_serial,
        manifest_sha256=m.manifest_sha256(),
        challenge=_CHALLENGE,
        response=good,
    )
    # A head that does not hold the master secret cannot forge a valid response.
    assert not verify_cal_vault(
        master_secret=_MASTER,
        serial=m.module_serial,
        manifest_sha256=m.manifest_sha256(),
        challenge=_CHALLENGE,
        response="deadbeef",
    )
    # The response is bound to the manifest digest: tamper the digest, the response fails.
    assert not verify_cal_vault(
        master_secret=_MASTER,
        serial=m.module_serial,
        manifest_sha256="0" * 64,
        challenge=_CHALLENGE,
        response=good,
    )


def test_genuine_head_detects_and_may_enable_source() -> None:
    m = _manifest(SafetyClass.laser_class_4)
    detect = _detect(m)
    assert detect.accepted is True
    assert detect.blockers == ()
    assert detect.digest_matches is True
    assert detect.cal_vault_valid is True
    enable = evaluate_source_enable(detect, interlock_closed=True)
    assert enable.allowed is True
    assert enable.blockers == ()


def test_tampered_manifest_digest_fails_detection() -> None:
    m = _manifest()
    detect = _detect(m, stored_digest="f" * 64)  # EEPROM digest != recomputed
    assert detect.accepted is False
    assert detect.digest_matches is False
    assert "manifest_digest_mismatch" in detect.blockers
    # A head rejected at detection can never enable its source.
    enable = evaluate_source_enable(detect, interlock_closed=True)
    assert enable.allowed is False
    assert "module_not_accepted_at_detection" in enable.blockers


def test_over_envelope_head_fails_detection() -> None:
    m = _manifest(barrel_diameter_mm=40.0)  # > Ø32 keepout
    detect = _detect(m)
    assert detect.accepted is False
    assert "manifest_envelope_does_not_fit" in detect.blockers


def test_counterfeit_class4_head_is_refused_source() -> None:
    # A head whose cal-vault does not validate (no master secret) still DETECTS if its
    # digest/envelope are fine -- but the source-enable gate refuses to energize a
    # Class-4 laser from it. This is the headline safety guarantee.
    m = _manifest(SafetyClass.laser_class_4)
    detect = _detect(m, cal_response="0" * 64)
    assert detect.accepted is True  # digest + envelope ok
    assert detect.cal_vault_valid is False
    enable = evaluate_source_enable(detect, interlock_closed=True)
    assert enable.allowed is False
    assert "uncertified_head_for_dangerous_source_class" in enable.blockers


def test_uncertified_passive_head_may_still_enable_its_source() -> None:
    # A passive/LED head needs no cal-vault to operate (it has no dangerous source);
    # an invalid cal-vault does not block its source-enable, only the interlock matters.
    # This is the residual: a head can declare led/passive without certification, but
    # those classes carry no dangerous source, so the exemption gains it nothing harmful.
    for safe in (SafetyClass.led, SafetyClass.passive):
        detect = _detect(_manifest(safe), cal_response="0" * 64)
        assert detect.cal_vault_valid is False
        assert evaluate_source_enable(detect, interlock_closed=True).allowed is True


def test_every_non_exempt_class_requires_cal_vault_including_class_1() -> None:
    # The polarity fix: laser_class_1 (which can enclose a class-3B/4 emitter) and every
    # other non-exempt class require certification by default -- a counterfeit cannot
    # dodge the gate by declaring a "benign-looking" class.
    for dangerous in (
        SafetyClass.laser_class_1,
        SafetyClass.laser_class_3b,
        SafetyClass.laser_class_4,
        SafetyClass.microwave,
    ):
        detect = _detect(_manifest(dangerous), cal_response="0" * 64)
        assert detect.accepted is True
        enable = evaluate_source_enable(detect, interlock_closed=True)
        assert enable.allowed is False
        assert "uncertified_head_for_dangerous_source_class" in enable.blockers


def test_fresh_challenge_defeats_replay_across_docks() -> None:
    # A genuine response to dock-1's challenge must NOT verify against dock-2's fresh
    # challenge -- so a one-time bus capture cannot be replayed.
    m = _manifest()
    challenge_1 = issue_challenge()
    challenge_2 = issue_challenge()
    assert challenge_1 != challenge_2
    response_1 = compute_cal_response(
        derive_device_secret(_MASTER, m.module_serial),
        challenge=challenge_1,
        manifest_sha256=m.manifest_sha256(),
        serial=m.module_serial,
    )
    assert not verify_cal_vault(
        master_secret=_MASTER,
        serial=m.module_serial,
        manifest_sha256=m.manifest_sha256(),
        challenge=challenge_2,
        response=response_1,
    )


def test_mac_field_boundaries_are_unambiguous() -> None:
    # Length-prefixed encoding: shifting a delimiter between fields must change the MAC
    # (no "a|b","c" vs "a","b|c" collision).
    ds = derive_device_secret(_MASTER, "serial")
    a = compute_cal_response(ds, challenge="x|", manifest_sha256="y", serial="s")
    b = compute_cal_response(ds, challenge="x", manifest_sha256="|y", serial="s")
    assert a != b


def test_non_str_cal_response_fails_closed() -> None:
    m = _manifest()
    assert not verify_cal_vault(
        master_secret=_MASTER,
        serial=m.module_serial,
        manifest_sha256=m.manifest_sha256(),
        challenge=_CHALLENGE,
        response=b"bytes-not-str",  # type: ignore[arg-type]
    )


def test_open_interlock_blocks_every_source() -> None:
    m = _manifest(SafetyClass.led)
    detect = _detect(m)
    enable = evaluate_source_enable(detect, interlock_closed=False)
    assert enable.allowed is False
    assert "hardware_interlock_open" in enable.blockers


def test_multiple_source_enable_blockers_accumulate() -> None:
    m = _manifest(SafetyClass.laser_class_4)
    detect = _detect(m, stored_digest="f" * 64, cal_response="0" * 64)
    enable = evaluate_source_enable(detect, interlock_closed=False)
    assert enable.allowed is False
    assert set(enable.blockers) == {
        "module_not_accepted_at_detection",
        "hardware_interlock_open",
        "uncertified_head_for_dangerous_source_class",
    }


# --- IN-C8 / HX4: cal-vault is a SEPARATE authority from compatibility & registration ------
# HX4 requires the counterfeit/cal-vault check to be extended to the heads "without merging
# them with compatibility or registration." These prove the three authorities are computed by
# independent functions over independent inputs: a part can pass one and fail another, and
# genuineness never rides in on (or is masked by) version compatibility or pose registration.


def test_genuineness_is_independent_of_version_compatibility() -> None:
    # A GENUINE head (valid cal-vault, accepted at detection) on an INCOMPATIBLE major
    # version: the cal-vault still verifies (it is genuine), but compatibility refuses it.
    incompatible = _manifest(smis_version="1.0")  # major 1 vs platform major 0
    detect = _detect(incompatible)  # genuine response recomputed for this manifest
    compat = validate_module_compatibility(incompatible)
    assert detect.cal_vault_valid is True
    assert detect.accepted is True
    assert compat.compatible is False
    assert compat.blockers != ()

    # Converse: a perfectly COMPATIBLE manifest with a FORGED cal-vault stays counterfeit.
    compatible = _manifest()
    forged = _detect(compatible, cal_response="0" * 64)
    assert validate_module_compatibility(compatible).compatible is True
    assert forged.cal_vault_valid is False


def test_genuineness_is_independent_of_registration() -> None:
    # A genuine head (valid cal-vault) whose post-dock registration is insufficient: the
    # registration authority rejects it, but that says nothing about genuineness, and the
    # cal-vault says nothing about registration. Different functions, different inputs.
    m = _manifest(requires_post_dock_autofocus=True)  # needs Tier B / 3 fiducials
    detect = _detect(m)
    registration = validate_registration_result(
        m, RegistrationResult(tier="A", ok=True, fiducials_used=1)
    )
    assert detect.cal_vault_valid is True
    assert registration.accepted is False
    assert "registration_tier_insufficient" in registration.blockers


def test_source_enable_does_not_consume_compatibility_or_registration() -> None:
    # The headline "without merging": evaluate_source_enable's only inputs are the detection
    # result (which carries the cal-vault verdict) and the hardware interlock. A genuine,
    # interlock-closed, cal-valid head enables its source through ITS gate even when a
    # separate compatibility check on the same manifest fails -- because driver-load
    # (compatibility) and acquire (registration) are distinct upstream gates, not folded in.
    incompatible_but_genuine = _manifest(SafetyClass.laser_class_4, smis_version="1.0")
    detect = _detect(incompatible_but_genuine)
    assert validate_module_compatibility(incompatible_but_genuine).compatible is False
    enable = evaluate_source_enable(detect, interlock_closed=True)
    assert enable.allowed is True  # source-enable is its own authority over the cal-vault
    assert enable.blockers == ()
