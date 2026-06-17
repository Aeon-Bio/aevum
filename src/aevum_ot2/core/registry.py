from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from aevum_cad.params import ROOT
from aevum_ot2.core.evidence_primitives import _stable_json_sha256
from aevum_ot2.core.models import (
    BridgeSession,
    GateName,
    GateResult,
    OffsetAuthorityState,
    OffsetRecord,
    OffsetRegistry,
)
from aevum_ot2.core.records import TargetClassVerificationRecord
from aevum_ot2.core.safety import FixtureSafetyProfile, safety_profile_integrity_blockers
from aevum_ot2.core.schema import (
    load_json_object,
    require_schema_version,
    require_schema_versioned_items,
)
from aevum_ot2.core.targets import TargetPolicy, target_policy_for

DEFAULT_OFFSET_REGISTRY = ROOT / "data" / "measurements" / "ot2_offset_registry.json"
PROMOTED_OFFSET_AUTHORITY_CLAIM = "promoted_offset_authority"


def load_offset_registry(path: str | Path = DEFAULT_OFFSET_REGISTRY) -> OffsetRegistry:
    registry_path = Path(path)
    if not registry_path.exists():
        return OffsetRegistry()

    data = load_json_object(registry_path, schema_name="OffsetRegistry")
    require_schema_version(data, schema_name="OffsetRegistry", path=registry_path)
    require_schema_versioned_items(
        data.get("records"),
        schema_name="OffsetRecord",
        path=registry_path,
    )
    return OffsetRegistry.model_validate(data)


def append_offset_record(
    record: OffsetRecord,
    path: str | Path = DEFAULT_OFFSET_REGISTRY,
) -> OffsetRegistry:
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry = load_offset_registry(registry_path)
    registry.records.append(_record_with_id(record))
    _atomic_write_json(registry_path, registry.model_dump(mode="json"))
    return registry


def offset_record_id(record: OffsetRecord) -> str:
    if record.offset_record_id:
        return record.offset_record_id
    payload = {
        "robot_serial": record.robot_serial,
        "robot_server_version": record.robot_server_version,
        "opentrons_api_version": record.opentrons_api_version,
        "fixture_load_name": record.fixture_load_name,
        "fixture_definition_uri": record.fixture_definition_uri,
        "fixture_params_sha256": record.fixture_params_sha256,
        "labware_definition_sha256": record.labware_definition_sha256,
        "pose_digest_sha256": record.pose_digest_sha256,
        "slot": record.slot,
        "pipette_name": record.pipette_name,
        "pipette_mount": record.pipette_mount,
        "tiprack_load_name": record.tiprack_load_name,
        "verification_targets": sorted(record.verification_targets),
        "safety_profile_sha256": record.safety_profile_sha256,
        "target_policy_digest_sha256": record.target_policy_digest_sha256,
    }
    return "offset:" + _stable_json_sha256(payload)[:24]


def offset_match_gate(
    *,
    registry: OffsetRegistry | None,
    session: BridgeSession,
    target_record: TargetClassVerificationRecord,
    safety_profile: FixtureSafetyProfile | None,
    target_policy: TargetPolicy | None = None,
    fixture_pose: object | None = None,
) -> GateResult:
    blockers: list[str] = []
    missing_claims: list[str] = []
    claim_ids: list[str] = []

    _target_policy_or_blocker(target_record.target_class, target_policy, blockers)
    blockers.extend(_target_record_scope_blockers(target_record, session))
    if session.fixture_pose_digest_sha256 and fixture_pose is None:
        missing_claims.append("fixture_pose")
    if fixture_pose is not None:
        from aevum_ot2.core.pose import FixturePose, pose_match_gate

        pose = FixturePose.model_validate(fixture_pose)
        pose_gate = pose_match_gate(
            pose,
            expected_pose_digest_sha256=target_record.pose_digest_sha256,
            expected_session_id=session.session_id,
            expected_robot_url=session.robot_url,
            expected_fixture_params_sha256=session.fixture_identity.params_sha256,
            expected_evidence_index_path=session.evidence_index_path,
            expected_claim_not_before=session.updated_at,
            claim_expires_at=session.lease_expires_at,
            claim_valid_at=datetime.now(),
            claims=target_record.claims,
        )
        missing_claims.extend(pose_gate.missing_claims)
        blockers.extend(pose_gate.blockers)
        claim_ids.extend(pose_gate.claim_ids)
    if registry is None:
        missing_claims.append("offset_registry")
    if safety_profile is None:
        missing_claims.append("fixture_safety_profile_valid")
    else:
        if not safety_profile.safety_profile_sha256:
            missing_claims.append("safety_profile_sha256")
        if not safety_profile.target_policy_digest_sha256:
            missing_claims.append("target_policy_digest_sha256")

    offset_reference = target_record.offset_registry_record.strip()
    if not offset_reference or offset_reference == "not-yet-registered":
        missing_claims.append(PROMOTED_OFFSET_AUTHORITY_CLAIM)

    record = None
    if registry is not None and offset_reference and offset_reference != "not-yet-registered":
        matching_records = _matching_offset_records(registry, offset_reference)
        if not matching_records:
            blockers.append(f"offset registry record not found: {offset_reference}")
        else:
            record = matching_records[0]
        if len(matching_records) > 1:
            blockers.append(f"duplicate offset registry record reference: {offset_reference}")

    if record is not None:
        claim_ids.append(offset_record_id(record))
        blockers.extend(
            _offset_scope_blockers(
                record,
                session=session,
                target_record=target_record,
                safety_profile=safety_profile,
            )
        )

    return GateResult(
        gate_name=GateName.OFFSET_AUTHORITY,
        passed=not blockers and not missing_claims,
        motion_allowed=False,
        blockers=_dedupe(blockers),
        missing_claims=_dedupe(missing_claims),
        claim_ids=_dedupe(claim_ids),
    )


def _atomic_write_json(path: Path, data: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, path)


def _record_with_id(record: OffsetRecord) -> OffsetRecord:
    if record.offset_record_id:
        return record
    return record.model_copy(update={"offset_record_id": offset_record_id(record)})


def _target_policy_or_blocker(
    target_class: str,
    target_policy: TargetPolicy | None,
    blockers: list[str],
) -> TargetPolicy | None:
    if target_policy is not None:
        if target_policy.target_class != target_class:
            blockers.append("target policy does not match target record")
        return target_policy
    try:
        return target_policy_for(target_class)
    except KeyError:
        blockers.append(f"unknown target policy: {target_class}")
        return None


def _matching_offset_records(
    registry: OffsetRegistry,
    offset_reference: str,
) -> list[OffsetRecord]:
    return [
        record
        for record in registry.records
        if offset_record_id(record) == offset_reference
    ]


def _target_record_scope_blockers(
    target_record: TargetClassVerificationRecord,
    session: BridgeSession,
) -> list[str]:
    blockers: list[str] = []
    if target_record.robot_serial != (session.robot_serial or ""):
        blockers.append("target record robot serial does not match session")
    if target_record.robot_server_version != (session.robot_server_version or ""):
        blockers.append("target record robot server version does not match session")
    if target_record.slot != session.slot:
        blockers.append("target record slot does not match session")
    if target_record.fixture_load_name != session.fixture_identity.load_name:
        blockers.append("target record fixture load name does not match session")
    if target_record.fixture_params_sha256 != session.fixture_identity.params_sha256:
        blockers.append("target record fixture params checksum does not match session")
    if (
        target_record.labware_definition_sha256
        != session.fixture_identity.labware_definition_sha256
    ):
        blockers.append("target record labware checksum does not match session")
    if session.fixture_pose_digest_sha256:
        if not target_record.pose_digest_sha256:
            blockers.append("target record pose digest is missing")
        elif target_record.pose_digest_sha256 != session.fixture_pose_digest_sha256:
            blockers.append("target record pose digest does not match session")
    return blockers


def _offset_scope_blockers(
    record: OffsetRecord,
    *,
    session: BridgeSession,
    target_record: TargetClassVerificationRecord,
    safety_profile: FixtureSafetyProfile | None,
) -> list[str]:
    blockers: list[str] = []
    if record.authority_state != OffsetAuthorityState.PROMOTED:
        blockers.append("offset registry record is not promoted")
    if record.robot_serial != (session.robot_serial or ""):
        blockers.append("offset robot serial does not match session")
    if record.robot_server_version != session.robot_server_version:
        blockers.append("offset robot server version does not match session")
    if record.opentrons_api_version != session.max_protocol_api_version:
        blockers.append("offset Opentrons API version does not match session")
    if record.fixture_load_name != session.fixture_identity.load_name:
        blockers.append("offset fixture load name does not match session")
    if record.fixture_definition_uri != (session.definition_uri or ""):
        blockers.append("offset fixture definition URI does not match session")
    if record.fixture_params_sha256 != session.fixture_identity.params_sha256:
        blockers.append("offset fixture params checksum does not match session")
    if record.labware_definition_sha256 != session.fixture_identity.labware_definition_sha256:
        blockers.append("offset labware checksum does not match session")
    if session.fixture_pose_digest_sha256:
        if not record.pose_digest_sha256:
            blockers.append("offset pose digest is missing")
        elif record.pose_digest_sha256 != session.fixture_pose_digest_sha256:
            blockers.append("offset pose digest does not match session")
    if record.slot != session.slot:
        blockers.append("offset slot does not match session")
    if record.pipette_name != target_record.pipette_name:
        blockers.append("offset pipette name does not match target record")
    if record.pipette_mount != target_record.pipette_mount:
        blockers.append("offset pipette mount does not match target record")
    if record.tiprack_load_name != target_record.tiprack_load_name:
        blockers.append("offset tiprack load name does not match target record")
    if target_record.target_class not in record.verification_targets:
        blockers.append("offset verification targets do not include target class")
    if safety_profile is not None:
        blockers.extend(safety_profile_integrity_blockers(safety_profile))
        if record.safety_profile_sha256 != safety_profile.safety_profile_sha256:
            blockers.append("offset safety profile checksum does not match")
        if record.target_policy_digest_sha256 != safety_profile.target_policy_digest_sha256:
            blockers.append("offset target policy digest does not match")
        if safety_profile.pose_digest_sha256:
            if not record.pose_digest_sha256:
                blockers.append("offset pose digest is missing")
            elif record.pose_digest_sha256 != safety_profile.pose_digest_sha256:
                blockers.append("offset pose digest does not match safety profile")
    return blockers


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
