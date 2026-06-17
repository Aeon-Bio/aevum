from __future__ import annotations

import math
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from aevum_ot2.core.evidence_primitives import _stable_json_sha256
from aevum_ot2.core.gates import (
    FIXTURE_DIMENSIONS_CLAIM,
    fixture_qc_claims_from_legacy_record,
    fixture_qc_gate_from_claims,
)
from aevum_ot2.core.models import (
    BridgeSession,
    BridgeSessionState,
    EvidenceClaim,
    FixtureIdentity,
    GateName,
    GateResult,
)
from aevum_ot2.core.records import FixtureQcMeasurement, FixtureQcRecord
from aevum_ot2.core.recovery import NoMotionRecoveryDisposition
from aevum_ot2.core.schema import load_versioned_json_model
from aevum_ot2.core.targets import TargetPolicy, target_policies

DEFAULT_HIGH_Z_CLEARANCE_MM = 20.0
DEFAULT_MAX_REGISTRATION_JOG_MM = 0.5


class MeasuredFixtureBounds(BaseModel):
    x_mm: float
    y_mm: float
    z_mm: float


class SafetyForbiddenZone(BaseModel):
    zone_id: str
    source: Literal["target_policy", "cad_params_placeholder"]
    description: str
    target_classes: list[str] = Field(default_factory=list)


class BoundaryTargetHandling(BaseModel):
    boundary_target_classes: list[str] = Field(default_factory=list)
    default_allowed: bool = False
    requires_inner_target_margin: bool = True
    reason: str = (
        "Boundary targets require inner target-class margin before motion planning."
    )


class FixtureSafetyProfile(BaseModel):
    schema_version: int = 1
    fixture_load_name: str
    fixture_params_sha256: str
    labware_definition_sha256: str
    pose_digest_sha256: str = ""
    params_path: str
    labware_path: str
    dimensions_source: Literal["measured_fixture_qc"] = "measured_fixture_qc"
    nominal_dimensions_mm: dict[str, float]
    labware_dimensions_mm: dict[str, float]
    measured_bounds_mm: MeasuredFixtureBounds
    conservative_bounds_mm: MeasuredFixtureBounds
    conservative_high_z_mm: float
    dry_z_floor_mm: float
    wet_z_floor_mm: float
    max_registration_jog_mm: float
    forbidden_zones: list[SafetyForbiddenZone] = Field(default_factory=list)
    boundary_handling: BoundaryTargetHandling
    target_policy_digest_sha256: str
    source_claim_ids: list[str] = Field(default_factory=list)
    source_claim_types: list[str] = Field(default_factory=list)
    safety_profile_sha256: str = ""


class SafetyProfileBuildResult(BaseModel):
    schema_version: int = 1
    passed: bool
    profile: FixtureSafetyProfile | None = None
    blockers: list[str] = Field(default_factory=list)
    missing_claims: list[str] = Field(default_factory=list)
    blocked_gates: list[GateName] = Field(default_factory=list)


def build_fixture_safety_profile(
    fixture_identity: FixtureIdentity,
    *,
    session: BridgeSession | None = None,
    fixture_qc_record: FixtureQcRecord | None = None,
    fixture_qc_claims: list[EvidenceClaim] | None = None,
    fixture_pose: object | None = None,
    pose_claims: list[EvidenceClaim] | None = None,
    policies: list[TargetPolicy] | None = None,
    high_z_clearance_mm: float = DEFAULT_HIGH_Z_CLEARANCE_MM,
    max_registration_jog_mm: float = DEFAULT_MAX_REGISTRATION_JOG_MM,
) -> SafetyProfileBuildResult:
    active_policies = policies if policies is not None else target_policies()
    blockers: list[str] = []
    missing_claims: list[str] = []

    if fixture_qc_record is None:
        blockers.append("fixture QC record with measured bounds is required")
    else:
        blockers.extend(_fixture_identity_blockers(fixture_identity, fixture_qc_record))
    pose_digest_sha256 = ""
    if (
        fixture_qc_record is not None
        and fixture_qc_record.pose_digest_sha256
        and fixture_pose is None
    ):
        missing_claims.append("fixture_pose")
    if fixture_pose is not None:
        from aevum_ot2.core.pose import FixturePose, pose_match_gate

        pose = FixturePose.model_validate(fixture_pose)
        if session is not None:
            blockers.extend(_session_fixture_identity_blockers(fixture_identity, session))
        if session is None and any(claim.session_id for claim in pose_claims or []):
            blockers.append("bridge session is required for session-scoped pose claims")
        pose_gate = pose_match_gate(
            pose,
            expected_pose_digest_sha256=(
                fixture_qc_record.pose_digest_sha256
                if fixture_qc_record is not None
                else pose.pose_digest_sha256
            ),
            expected_session_id=session.session_id if session is not None else None,
            expected_robot_url=session.robot_url if session is not None else None,
            expected_fixture_params_sha256=fixture_identity.params_sha256,
            expected_evidence_index_path=(
                session.evidence_index_path if session is not None else None
            ),
            expected_claim_not_before=session.updated_at if session is not None else None,
            claim_expires_at=session.lease_expires_at if session is not None else None,
            claim_valid_at=datetime.now(),
            claims=pose_claims or [],
        )
        blockers.extend(pose_gate.blockers)
        missing_claims.extend(pose_gate.missing_claims)
        pose_digest_sha256 = pose.pose_digest_sha256
    blockers.extend(
        _safety_parameter_blockers(
            high_z_clearance_mm=high_z_clearance_mm,
            max_registration_jog_mm=max_registration_jog_mm,
        )
    )

    claims = fixture_qc_claims
    if claims is None and fixture_qc_record is not None:
        claims = fixture_qc_claims_from_legacy_record(fixture_qc_record)
    if not claims:
        missing_claims.append(FIXTURE_DIMENSIONS_CLAIM)
        blockers.append("fixture QC claims are required for safety profile construction")
    else:
        blockers.extend(_claim_scope_blockers(fixture_identity, claims))
        blockers.extend(_duplicate_claim_blockers(claims))
        gate = fixture_qc_gate_from_claims(claims)
        blockers.extend(gate.blockers)
        missing_claims.extend(gate.missing_claims)

    measured_bounds: MeasuredFixtureBounds | None = None
    if fixture_qc_record is not None:
        measured_bounds, measurement_blockers = _measured_bounds(fixture_qc_record)
        blockers.extend(measurement_blockers)

    blockers = _dedupe(blockers)
    missing_claims = _dedupe(missing_claims)
    if blockers or missing_claims or measured_bounds is None:
        return SafetyProfileBuildResult(
            passed=False,
            blockers=blockers,
            missing_claims=missing_claims,
            blocked_gates=_motion_gates_blocked_by_safety_profile(),
        )

    conservative_bounds = _conservative_bounds(
        fixture_identity.nominal_dimensions_mm,
        measured_bounds,
    )
    boundary_targets = [
        policy.target_class for policy in active_policies if policy.boundary
    ]
    target_policy_digest = _target_policy_digest(active_policies)
    profile = FixtureSafetyProfile(
        fixture_load_name=fixture_identity.load_name,
        fixture_params_sha256=fixture_identity.params_sha256,
        labware_definition_sha256=fixture_identity.labware_definition_sha256,
        pose_digest_sha256=pose_digest_sha256,
        params_path=fixture_identity.params_path,
        labware_path=fixture_identity.labware_path,
        nominal_dimensions_mm=dict(fixture_identity.nominal_dimensions_mm),
        labware_dimensions_mm=dict(fixture_identity.labware_dimensions_mm),
        measured_bounds_mm=measured_bounds,
        conservative_bounds_mm=conservative_bounds,
        conservative_high_z_mm=conservative_bounds.z_mm + high_z_clearance_mm,
        dry_z_floor_mm=conservative_bounds.z_mm,
        wet_z_floor_mm=conservative_bounds.z_mm,
        max_registration_jog_mm=max_registration_jog_mm,
        forbidden_zones=[
            SafetyForbiddenZone(
                zone_id="boundary_targets_without_inner_margin",
                source="target_policy",
                description=(
                    "Boundary target classes are blocked until inner target "
                    "classes prove margin for the same safety profile."
                ),
                target_classes=boundary_targets,
            )
        ],
        boundary_handling=BoundaryTargetHandling(
            boundary_target_classes=boundary_targets,
        ),
        target_policy_digest_sha256=target_policy_digest,
        source_claim_ids=[claim.claim_id for claim in claims],
        source_claim_types=[claim.claim_type for claim in claims],
    )
    profile.safety_profile_sha256 = _safety_profile_digest(profile)
    return SafetyProfileBuildResult(passed=True, profile=profile)


def write_fixture_safety_profile(
    profile: FixtureSafetyProfile,
    path: str | Path,
) -> Path:
    profile_path = Path(path)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = profile_path.with_suffix(profile_path.suffix + ".tmp")
    tmp.write_text(profile.model_dump_json(indent=2) + "\n")
    os.replace(tmp, profile_path)
    return profile_path


def load_fixture_safety_profile(path: str | Path) -> FixtureSafetyProfile:
    return load_versioned_json_model(
        path,
        FixtureSafetyProfile,
        schema_name="FixtureSafetyProfile",
    )


def _session_fixture_identity_blockers(
    fixture_identity: FixtureIdentity,
    session: BridgeSession,
) -> list[str]:
    identity = session.fixture_identity
    blockers: list[str] = []
    if fixture_identity.load_name != identity.load_name:
        blockers.append("fixture identity does not match session fixture")
    if fixture_identity.params_sha256 != identity.params_sha256:
        blockers.append("fixture params checksum does not match session fixture")
    if fixture_identity.labware_definition_sha256 != identity.labware_definition_sha256:
        blockers.append("fixture labware checksum does not match session fixture")
    return blockers


def home_clearance_gate(
    *,
    session: BridgeSession,
    safety_profile: FixtureSafetyProfile | None,
    fixture_pose: object | None = None,
    pose_claims: list[EvidenceClaim] | None = None,
    recovery_disposition: NoMotionRecoveryDisposition | str | None = None,
    allowed_session_states: set[BridgeSessionState] | None = None,
) -> GateResult:
    blockers: list[str] = []
    missing_claims: list[str] = []
    claim_ids: list[str] = []

    if safety_profile is None:
        missing_claims.append("fixture_safety_profile_valid")
    else:
        if not safety_profile.safety_profile_sha256:
            missing_claims.append("safety_profile_sha256")
        else:
            claim_ids.append(safety_profile.safety_profile_sha256)
        blockers.extend(safety_profile_integrity_blockers(safety_profile))
        blockers.extend(_safety_profile_session_blockers(session, safety_profile))

    if session.fixture_pose_digest_sha256 and fixture_pose is None:
        missing_claims.append("fixture_pose")
    if fixture_pose is not None:
        from aevum_ot2.core.pose import FixturePose, pose_match_gate

        pose = FixturePose.model_validate(fixture_pose)
        expected_pose_digest = (
            safety_profile.pose_digest_sha256
            if safety_profile is not None
            else session.fixture_pose_digest_sha256
        )
        pose_gate = pose_match_gate(
            pose,
            expected_pose_digest_sha256=expected_pose_digest,
            expected_session_id=session.session_id,
            expected_robot_url=session.robot_url,
            expected_fixture_params_sha256=session.fixture_identity.params_sha256,
            expected_evidence_index_path=session.evidence_index_path,
            expected_claim_not_before=session.updated_at,
            claim_expires_at=session.lease_expires_at,
            claim_valid_at=datetime.now(),
            claims=pose_claims or [],
        )
        blockers.extend(pose_gate.blockers)
        missing_claims.extend(pose_gate.missing_claims)
        claim_ids.extend(pose_gate.claim_ids)

    allowed_states = allowed_session_states or {
        BridgeSessionState.READY_NO_MOTION,
        BridgeSessionState.MOTION_COMMISSIONING_ARMED,
    }
    if session.state not in allowed_states:
        blockers.append(f"session state {session.state} cannot pass home clearance")

    recovery_value, recovery_blockers = _recovery_disposition_value(recovery_disposition)
    blockers.extend(recovery_blockers)
    if recovery_value is None:
        missing_claims.append("recovery_disposition")
    elif recovery_value in {
        NoMotionRecoveryDisposition.NO_LOCAL_SESSION.value,
        NoMotionRecoveryDisposition.UNRESOLVED_RECOVERY.value,
    }:
        blockers.append(f"recovery disposition blocks home clearance: {recovery_value}")

    return GateResult(
        gate_name=GateName.HOME_CLEARANCE,
        passed=not blockers and not missing_claims,
        motion_allowed=False,
        blockers=_dedupe(blockers),
        missing_claims=_dedupe(missing_claims),
        claim_ids=_dedupe(claim_ids),
    )


def safety_profile_integrity_blockers(profile: FixtureSafetyProfile) -> list[str]:
    blockers: list[str] = []
    if profile.schema_version != 1:
        blockers.append(f"unsupported safety profile schema version: {profile.schema_version}")
    if profile.safety_profile_sha256:
        expected = _safety_profile_digest(profile)
        if profile.safety_profile_sha256 != expected:
            blockers.append("safety profile checksum does not match profile contents")
    return blockers


def _fixture_identity_blockers(
    fixture_identity: FixtureIdentity,
    record: FixtureQcRecord,
) -> list[str]:
    blockers: list[str] = []
    if not fixture_identity.dimensions_match:
        blockers.append("fixture artifact identity has mismatched nominal/labware dimensions")
    if record.fixture_load_name != fixture_identity.load_name:
        blockers.append("fixture QC record load name does not match fixture identity")
    if record.fixture_params_sha256 != fixture_identity.params_sha256:
        blockers.append("fixture QC record params checksum does not match fixture identity")
    if record.labware_definition_sha256 != fixture_identity.labware_definition_sha256:
        blockers.append("fixture QC record labware checksum does not match fixture identity")
    return blockers


def _safety_profile_session_blockers(
    session: BridgeSession,
    profile: FixtureSafetyProfile,
) -> list[str]:
    blockers: list[str] = []
    if profile.fixture_load_name != session.fixture_identity.load_name:
        blockers.append("safety profile fixture load name does not match session")
    if profile.fixture_params_sha256 != session.fixture_identity.params_sha256:
        blockers.append("safety profile params checksum does not match session")
    if profile.labware_definition_sha256 != session.fixture_identity.labware_definition_sha256:
        blockers.append("safety profile labware checksum does not match session")
    if session.fixture_pose_digest_sha256:
        if not profile.pose_digest_sha256:
            blockers.append("safety profile pose digest is missing")
        elif profile.pose_digest_sha256 != session.fixture_pose_digest_sha256:
            blockers.append("safety profile pose digest does not match session")
    return blockers


def _recovery_disposition_value(
    recovery_disposition: NoMotionRecoveryDisposition | str | None,
) -> tuple[str | None, list[str]]:
    if recovery_disposition is None:
        return None, []
    if isinstance(recovery_disposition, NoMotionRecoveryDisposition):
        return recovery_disposition.value, []
    try:
        return NoMotionRecoveryDisposition(recovery_disposition).value, []
    except ValueError:
        return None, [f"unknown recovery disposition: {recovery_disposition}"]


def _safety_parameter_blockers(
    *,
    high_z_clearance_mm: float,
    max_registration_jog_mm: float,
) -> list[str]:
    blockers: list[str] = []
    if not math.isfinite(high_z_clearance_mm) or high_z_clearance_mm <= 0:
        blockers.append("high-Z clearance must be finite and positive")
    if not math.isfinite(max_registration_jog_mm) or max_registration_jog_mm <= 0:
        blockers.append("max registration jog must be finite and positive")
    return blockers


def _claim_scope_blockers(
    fixture_identity: FixtureIdentity,
    claims: list[EvidenceClaim],
) -> list[str]:
    blockers: list[str] = []
    for claim in claims:
        if claim.fixture_load_name != fixture_identity.load_name:
            blockers.append(f"claim {claim.claim_type} load name does not match fixture identity")
        if claim.fixture_params_sha256 != fixture_identity.params_sha256:
            blockers.append(
                f"claim {claim.claim_type} params checksum does not match fixture identity"
            )
        if claim.labware_definition_sha256 != fixture_identity.labware_definition_sha256:
            blockers.append(
                f"claim {claim.claim_type} labware checksum does not match fixture identity"
            )
    return blockers


def _duplicate_claim_blockers(claims: list[EvidenceClaim]) -> list[str]:
    blockers: list[str] = []
    seen: set[str] = set()
    duplicate_types: set[str] = set()
    for claim in claims:
        if claim.claim_type in seen:
            duplicate_types.add(claim.claim_type)
        seen.add(claim.claim_type)
    for claim_type in sorted(duplicate_types):
        blockers.append(f"duplicate fixture QC claim type: {claim_type}")
    return blockers


def _measured_bounds(
    record: FixtureQcRecord,
) -> tuple[MeasuredFixtureBounds | None, list[str]]:
    measurement_by_name = {measurement.name: measurement for measurement in record.measurements}
    blockers: list[str] = []
    values: dict[str, float] = {}
    for measurement_name, bound_key in (
        ("x_bound", "x_mm"),
        ("y_bound", "y_mm"),
        ("z_bound", "z_mm"),
    ):
        measurement = measurement_by_name.get(measurement_name)
        if measurement is None:
            blockers.append(f"missing measured fixture bound: {measurement_name}")
            continue
        blockers.extend(_measurement_blockers(measurement))
        if measurement.measured_mm is not None:
            values[bound_key] = measurement.measured_mm

    if blockers:
        return None, blockers
    return MeasuredFixtureBounds(**values), []


def _measurement_blockers(measurement: FixtureQcMeasurement) -> list[str]:
    blockers: list[str] = []
    if measurement.measured_mm is None:
        blockers.append(f"fixture QC measurement {measurement.name} has no measured value")
    if not measurement.passed:
        blockers.append(f"fixture QC measurement {measurement.name} did not pass")
    return blockers


def _conservative_bounds(
    nominal_dimensions_mm: dict[str, float],
    measured_bounds: MeasuredFixtureBounds,
) -> MeasuredFixtureBounds:
    return MeasuredFixtureBounds(
        x_mm=max(float(nominal_dimensions_mm["x"]), measured_bounds.x_mm),
        y_mm=max(float(nominal_dimensions_mm["y"]), measured_bounds.y_mm),
        z_mm=max(float(nominal_dimensions_mm["z"]), measured_bounds.z_mm),
    )


def _target_policy_digest(policies: list[TargetPolicy]) -> str:
    payload = [policy.model_dump(mode="json") for policy in policies]
    return _stable_json_sha256(payload)


def _safety_profile_digest(profile: FixtureSafetyProfile) -> str:
    payload = profile.model_dump(mode="json", exclude={"safety_profile_sha256"})
    return _stable_json_sha256(payload)


def _motion_gates_blocked_by_safety_profile() -> list[GateName]:
    return [GateName.LOW_Z_DRY, GateName.WET, GateName.HOME_CLEARANCE]


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
