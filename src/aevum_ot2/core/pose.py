from __future__ import annotations

import copy
import os
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from aevum_cad.params import ROOT
from aevum_ot2.core.evidence import load_evidence_index
from aevum_ot2.core.evidence_primitives import (
    _is_timezone_aware,
    _safe_path_segment,
    _same_path,
    _sha256_file,
    _stable_json_sha256,
)
from aevum_ot2.core.models import (
    EvidenceClaim,
    EvidenceHandle,
    EvidenceQuality,
    EvidenceSourceKind,
    FixtureIdentity,
    GateName,
    GateResult,
)
from aevum_ot2.core.schema import (
    SchemaVersionError,
    load_json_object,
    parse_versioned_json_model,
)

POSE_SCHEMA_VERSION = 1
WELL_IDENTITY_POLICY = "preserve_canonical_feature_names_v1"
POSE_UPRIGHT_CLAIM = "fixture_upright"
POSE_EVIDENCE_METHOD = "fixture_pose_evidence_packet_v1"
ORIENTED_LOAD_NAME_SUFFIX = "_rot180"
MATRIX_PRECISION_MM = 6
DEFAULT_FIXTURE_POSE_ROOT = ROOT / "data" / "measurements" / "sessions"

WellIdentityPolicy = Literal["preserve_canonical_feature_names_v1"]
TransformMatrix = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]


class FixtureOrientation(StrEnum):
    CANONICAL = "canonical"
    ROT180 = "rot180"


class Point3D(BaseModel):
    x: float
    y: float
    z: float
    frame: Literal["canonical", "installed"] = "canonical"


class FixturePose(BaseModel):
    schema_version: int = POSE_SCHEMA_VERSION
    slot: str
    orientation: FixtureOrientation
    fixture_load_name: str
    fixture_namespace: str
    fixture_version: int
    fixture_definition_sha256: str
    oriented_labware_load_name: str
    oriented_labware_namespace: str
    oriented_labware_version: int
    oriented_labware_definition_sha256: str
    transform_matrix_canonical_to_installed_mm: TransformMatrix
    well_identity_policy: WellIdentityPolicy = WELL_IDENTITY_POLICY
    evidence: list[EvidenceHandle] = Field(default_factory=list)
    pose_orientation_claim_id: str = ""
    fixture_upright_claim_id: str = ""
    pose_digest_sha256: str = ""


def fixture_pose_from_labware_definition(
    fixture_identity: FixtureIdentity,
    *,
    slot: str,
    orientation: FixtureOrientation | str,
    canonical_labware_definition: dict[str, Any],
    evidence: list[EvidenceHandle] | None = None,
    pose_orientation_claim_id: str = "",
    fixture_upright_claim_id: str = "",
) -> FixturePose:
    orientation_value = FixtureOrientation(orientation)
    oriented_definition = oriented_labware_definition(
        canonical_labware_definition,
        orientation=orientation_value,
    )
    oriented_identity = labware_definition_identity(oriented_definition)
    oriented_definition_sha256 = sha256_json(oriented_definition)
    pose = FixturePose(
        slot=slot,
        orientation=orientation_value,
        fixture_load_name=fixture_identity.load_name,
        fixture_namespace=fixture_identity.namespace,
        fixture_version=fixture_identity.version,
        fixture_definition_sha256=fixture_identity.labware_definition_sha256,
        oriented_labware_load_name=oriented_identity["load_name"],
        oriented_labware_namespace=oriented_identity["namespace"],
        oriented_labware_version=oriented_identity["version"],
        oriented_labware_definition_sha256=oriented_definition_sha256,
        transform_matrix_canonical_to_installed_mm=transform_matrix(
            fixture_identity,
            orientation=orientation_value,
        ),
        evidence=evidence or [],
        pose_orientation_claim_id=pose_orientation_claim_id,
        fixture_upright_claim_id=fixture_upright_claim_id,
    )
    return pose_with_digest(pose)


def fixture_pose_path_for_session(
    session_id: str,
    *,
    root: str | Path = DEFAULT_FIXTURE_POSE_ROOT,
) -> Path:
    return Path(root) / _safe_path_segment(session_id) / "fixture_pose.json"


def write_fixture_pose(pose: FixturePose, path: str | Path) -> Path:
    pose_path = Path(path)
    pose_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = pose_path.with_suffix(pose_path.suffix + ".tmp")
    tmp.write_text(pose.model_dump_json(indent=2) + "\n")
    os.replace(tmp, pose_path)
    return pose_path


def load_fixture_pose(path: str | Path) -> FixturePose:
    data = load_json_object(path, schema_name="FixturePose")
    return parse_versioned_json_model(
        data,
        FixturePose,
        schema_name="FixturePose",
        path=path,
    )


def pose_with_digest(pose: FixturePose) -> FixturePose:
    return pose.model_copy(update={"pose_digest_sha256": pose_digest_sha256(pose)})


def pose_digest_sha256(pose: FixturePose) -> str:
    return sha256_json(pose_digest_payload(pose))


def pose_digest_payload(pose: FixturePose) -> dict[str, Any]:
    return {
        "schema_version": pose.schema_version,
        "slot": pose.slot,
        "orientation": pose.orientation.value,
        "fixture_load_name": pose.fixture_load_name,
        "fixture_namespace": pose.fixture_namespace,
        "fixture_version": pose.fixture_version,
        "fixture_definition_sha256": pose.fixture_definition_sha256,
        "oriented_labware_load_name": pose.oriented_labware_load_name,
        "oriented_labware_namespace": pose.oriented_labware_namespace,
        "oriented_labware_version": pose.oriented_labware_version,
        "oriented_labware_definition_sha256": pose.oriented_labware_definition_sha256,
        "transform_matrix_canonical_to_installed_mm": canonicalize_matrix(
            pose.transform_matrix_canonical_to_installed_mm
        ),
        "well_identity_policy": pose.well_identity_policy,
    }


def transform_matrix(
    fixture_identity: FixtureIdentity,
    *,
    orientation: FixtureOrientation | str,
) -> TransformMatrix:
    orientation_value = FixtureOrientation(orientation)
    if orientation_value == FixtureOrientation.CANONICAL:
        return (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
        )
    if orientation_value == FixtureOrientation.ROT180:
        return (
            (-1.0, 0.0, 0.0, _dimension(fixture_identity, "x")),
            (0.0, -1.0, 0.0, _dimension(fixture_identity, "y")),
            (0.0, 0.0, 1.0, 0.0),
        )
    raise ValueError(f"unsupported fixture orientation: {orientation}")


def canonical_to_installed(point: Point3D, pose: FixturePose) -> Point3D:
    if point.frame != "canonical":
        raise ValueError("canonical_to_installed requires a canonical-frame point")
    matrix = pose.transform_matrix_canonical_to_installed_mm
    transformed = _apply_matrix(point, matrix)
    return transformed.model_copy(update={"frame": "installed"})


def installed_to_canonical(point: Point3D, pose: FixturePose) -> Point3D:
    if point.frame != "installed":
        raise ValueError("installed_to_canonical requires an installed-frame point")
    if pose.orientation == FixtureOrientation.CANONICAL:
        return point.model_copy(update={"frame": "canonical"})
    if pose.orientation == FixtureOrientation.ROT180:
        # In v1, rot180 is its own inverse. Any future orientation must add an
        # explicit inverse matrix before it can become motion-capable.
        transformed = _apply_matrix(point, pose.transform_matrix_canonical_to_installed_mm)
        return transformed.model_copy(update={"frame": "canonical"})
    raise ValueError(f"unsupported fixture orientation: {pose.orientation}")


def oriented_labware_definition(
    canonical_definition: dict[str, Any],
    *,
    orientation: FixtureOrientation | str,
) -> dict[str, Any]:
    orientation_value = FixtureOrientation(orientation)
    definition = copy.deepcopy(canonical_definition)
    if orientation_value == FixtureOrientation.CANONICAL:
        return definition

    _validate_rot180_supported_labware_definition(definition)
    dimensions = definition.get("dimensions", {})
    x_dimension = float(dimensions["xDimension"])
    y_dimension = float(dimensions["yDimension"])

    for well in definition.get("wells", {}).values():
        well["x"] = _round_mm(x_dimension - float(well["x"]))
        well["y"] = _round_mm(y_dimension - float(well["y"]))
        well["z"] = _round_mm(float(well["z"]))

    parameters = definition.setdefault("parameters", {})
    load_name = str(parameters["loadName"])
    if load_name.endswith(ORIENTED_LOAD_NAME_SUFFIX):
        raise ValueError("labware definition is already rot180-oriented")
    parameters["loadName"] = f"{load_name}{ORIENTED_LOAD_NAME_SUFFIX}"
    metadata = definition.setdefault("metadata", {})
    display_name = metadata.get("displayName")
    if isinstance(display_name, str) and "rot180" not in display_name:
        metadata["displayName"] = f"{display_name} rot180"
    tags = metadata.setdefault("tags", [])
    if isinstance(tags, list) and "rot180" not in tags:
        tags.append("rot180")

    return definition


def _validate_rot180_supported_labware_definition(
    definition: dict[str, Any],
) -> None:
    for path, value in _walk_dicts(definition):
        keys = set(value)
        if keys & {"xDimension", "yDimension", "zDimension"}:
            if path == ("dimensions",):
                continue
            raise ValueError(
                "unsupported dimension-bearing labware field for rot180: "
                + ".".join(path)
            )
        if not keys & {"x", "y", "z"}:
            continue
        if len(path) == 2 and path[0] == "wells":
            continue
        if path == ("cornerOffsetFromSlot",):
            offsets = [float(value.get(axis, 0.0)) for axis in ("x", "y", "z")]
            if offsets == [0.0, 0.0, 0.0]:
                continue
            raise ValueError("rot180 requires zero cornerOffsetFromSlot")
        raise ValueError(
            "unsupported coordinate-bearing labware field for rot180: "
            + ".".join(path)
        )


def _walk_dicts(
    value: Any,
    path: tuple[str, ...] = (),
) -> list[tuple[tuple[str, ...], dict[str, Any]]]:
    if isinstance(value, dict):
        walked = [(path, value)]
        for key, child in value.items():
            walked.extend(_walk_dicts(child, (*path, str(key))))
        return walked
    if isinstance(value, list):
        walked: list[tuple[tuple[str, ...], dict[str, Any]]] = []
        for index, child in enumerate(value):
            walked.extend(_walk_dicts(child, (*path, str(index))))
        return walked
    return []


def labware_definition_identity(definition: dict[str, Any]) -> dict[str, Any]:
    return {
        "load_name": str(definition["parameters"]["loadName"]),
        "namespace": str(definition["namespace"]),
        "version": int(definition["version"]),
    }


def pose_orientation_claim_type(
    *,
    orientation: FixtureOrientation | str,
    slot: str,
    fixture_definition_sha256: str,
) -> str:
    orientation_value = FixtureOrientation(orientation)
    return (
        "fixture_pose_orientation:"
        f"{orientation_value.value}:slot-{slot}:{fixture_definition_sha256}"
    )


def pose_match_gate(
    pose: FixturePose | None,
    *,
    expected_pose_digest_sha256: str | None = None,
    expected_session_id: str | None = None,
    expected_robot_url: str | None = None,
    expected_fixture_params_sha256: str | None = None,
    expected_evidence_index_path: str | Path | None = None,
    expected_claim_not_before: datetime | None = None,
    claim_expires_at: datetime | None = None,
    claim_valid_at: datetime | None = None,
    claims: list[EvidenceClaim] | None = None,
    require_claims: bool = True,
) -> GateResult:
    blockers: list[str] = []
    missing_claims: list[str] = []
    claim_ids: list[str] = []
    evidence: list[EvidenceHandle] = []

    if pose is None:
        return GateResult(
            gate_name=GateName.POSE_MATCH,
            passed=False,
            motion_allowed=False,
            missing_claims=["fixture_pose"],
        )

    if pose.schema_version != POSE_SCHEMA_VERSION:
        blockers.append(f"unsupported fixture pose schema version: {pose.schema_version}")
    if pose.orientation not in {FixtureOrientation.CANONICAL, FixtureOrientation.ROT180}:
        blockers.append(f"unsupported fixture orientation: {pose.orientation}")
    if not pose.pose_digest_sha256:
        missing_claims.append("pose_digest_sha256")
    elif pose.pose_digest_sha256 != pose_digest_sha256(pose):
        blockers.append("pose digest does not match pose contents")
    if expected_pose_digest_sha256 is not None:
        if not expected_pose_digest_sha256:
            missing_claims.append("expected_pose_digest_sha256")
        elif expected_pose_digest_sha256 != pose.pose_digest_sha256:
            blockers.append("pose digest does not match expected scope")

    if not pose.oriented_labware_load_name:
        missing_claims.append("oriented_labware_load_name")
    if not pose.oriented_labware_definition_sha256:
        missing_claims.append("oriented_labware_definition_sha256")
    if pose.well_identity_policy != WELL_IDENTITY_POLICY:
        blockers.append("unsupported well identity policy")
    if pose.orientation == FixtureOrientation.ROT180:
        canonical_name = pose.fixture_load_name
        if pose.oriented_labware_load_name == canonical_name:
            blockers.append("rot180 oriented labware load name must be distinct")

    if require_claims:
        claim_results = _pose_claim_results(
            pose,
            claims or [],
            expected_session_id=expected_session_id,
            expected_robot_url=expected_robot_url,
            expected_fixture_params_sha256=expected_fixture_params_sha256,
            expected_evidence_index_path=expected_evidence_index_path,
            expected_claim_not_before=expected_claim_not_before,
            claim_expires_at=claim_expires_at,
            claim_valid_at=claim_valid_at,
        )
        blockers.extend(claim_results["blockers"])
        missing_claims.extend(claim_results["missing_claims"])
        claim_ids.extend(claim_results["claim_ids"])
        evidence.extend(claim_results["evidence"])

    evidence.extend(pose.evidence)
    return GateResult(
        gate_name=GateName.POSE_MATCH,
        passed=not blockers and not missing_claims,
        motion_allowed=False,
        blockers=_dedupe(blockers),
        missing_claims=_dedupe(missing_claims),
        claim_ids=_dedupe(claim_ids),
        evidence=_dedupe_evidence(evidence),
    )


def sha256_json(payload: object) -> str:
    # Domain canonicalization first, then the shared stable-JSON digest — byte-identical to
    # the former inline json.dumps(sort_keys, compact) so the pose digest is unchanged.
    return _stable_json_sha256(_canonicalize(payload))


def canonicalize_matrix(matrix: TransformMatrix) -> list[list[float]]:
    return [[_round_mm(value) for value in row] for row in matrix]


def _pose_claim_results(
    pose: FixturePose,
    claims: list[EvidenceClaim],
    *,
    expected_session_id: str | None = None,
    expected_robot_url: str | None = None,
    expected_fixture_params_sha256: str | None = None,
    expected_evidence_index_path: str | Path | None = None,
    expected_claim_not_before: datetime | None = None,
    claim_expires_at: datetime | None = None,
    claim_valid_at: datetime | None = None,
) -> dict[str, list[str] | list[EvidenceHandle]]:
    blockers: list[str] = []
    missing_claims: list[str] = []
    claim_ids: list[str] = []
    evidence: list[EvidenceHandle] = []
    valid_at = claim_valid_at or datetime.now()
    has_authority_window = (
        expected_session_id is not None
        and expected_robot_url is not None
        and expected_evidence_index_path is not None
        and expected_claim_not_before is not None
        and claim_expires_at is not None
        and claim_valid_at is not None
    )

    required_claims = {
        pose_orientation_claim_type(
            orientation=pose.orientation,
            slot=pose.slot,
            fixture_definition_sha256=pose.fixture_definition_sha256,
        ),
        POSE_UPRIGHT_CLAIM,
    }
    for claim_type in sorted(required_claims):
        matching_claims = sorted(
            [claim for claim in claims if claim.claim_type == claim_type],
            key=_claim_recency_sort_key,
            reverse=True,
        )
        candidate_claims = matching_claims
        if expected_claim_not_before is not None:
            current_claims = [
                claim
                for claim in matching_claims
                if not _claim_predates_authority(claim, expected_claim_not_before)
            ]
            if current_claims:
                candidate_claims = current_claims
        if len(candidate_claims) > 1:
            blockers.append(f"duplicate pose claims for {claim_type}")
        claim = candidate_claims[0] if candidate_claims else None
        if claim is None:
            missing_claims.append(claim_type)
            continue
        claim_ids.append(claim.claim_id)
        evidence.extend(claim.evidence)
        if _claim_is_session_scoped(claim) and not has_authority_window:
            blockers.append(
                f"pose claim {claim_type} requires an explicit session authority window"
            )
        if "created_at" not in claim.model_fields_set:
            blockers.append(f"pose claim {claim_type} created_at is missing")
        if claim_expires_at is not None and valid_at >= claim_expires_at:
            blockers.append(f"pose claim {claim_type} authority expired")
        claim_created_at = claim.created_at
        claim_created_at_is_usable = True
        if _is_timezone_aware(claim_created_at):
            blockers.append(f"pose claim {claim_type} created_at is timezone-aware")
            claim_created_at_is_usable = False
        if expected_claim_not_before is not None:
            if claim_created_at_is_usable and claim_created_at < expected_claim_not_before:
                blockers.append(
                    f"pose claim {claim_type} predates active session authority"
                )
            if claim_created_at_is_usable and claim_created_at > valid_at:
                blockers.append(f"pose claim {claim_type} is from the future")
        if claim.method != POSE_EVIDENCE_METHOD:
            blockers.append(f"pose claim {claim_type} has unsupported method")
        if claim.value is not True:
            blockers.append(f"pose claim {claim_type} is not true")
        if claim.quality != EvidenceQuality.USABLE:
            blockers.append(f"pose claim {claim_type} is not usable")
        if expected_session_id is not None and claim.session_id != expected_session_id:
            blockers.append(f"pose claim {claim_type} session does not match")
        if claim.fixture_load_name != pose.fixture_load_name:
            blockers.append(f"pose claim {claim_type} fixture does not match")
        if not claim.fixture_params_sha256:
            missing_claims.append(f"{claim_type}:fixture_params_sha256")
        elif (
            expected_fixture_params_sha256 is not None
            and claim.fixture_params_sha256 != expected_fixture_params_sha256
        ):
            blockers.append(f"pose claim {claim_type} fixture params checksum does not match")
        if claim.labware_definition_sha256 != pose.fixture_definition_sha256:
            blockers.append(f"pose claim {claim_type} labware checksum does not match")
        if not claim.pose_digest_sha256:
            missing_claims.append(f"{claim_type}:pose_digest_sha256")
        elif claim.pose_digest_sha256 != pose.pose_digest_sha256:
            blockers.append(f"pose claim {claim_type} pose digest does not match")
        blockers.extend(
            _pose_claim_evidence_blockers(
                claim,
                pose=pose,
                claim_type=claim_type,
                expected_source_kind=_expected_pose_claim_source_kind(claim_type),
                expected_session_id=expected_session_id,
                expected_robot_url=expected_robot_url,
                expected_fixture_params_sha256=expected_fixture_params_sha256,
                expected_evidence_index_path=expected_evidence_index_path,
                expected_claim_not_before=expected_claim_not_before,
                claim_valid_at=valid_at,
            )
        )
        blockers.extend(claim.reasons)

    return {
        "blockers": _dedupe(blockers),
        "missing_claims": _dedupe(missing_claims),
        "claim_ids": _dedupe(claim_ids),
        "evidence": _dedupe_evidence(evidence),
    }


def _claim_predates_authority(
    claim: EvidenceClaim,
    expected_claim_not_before: datetime,
) -> bool:
    if (
        "created_at" in claim.model_fields_set
        and _datetime_predates_authority(claim.created_at, expected_claim_not_before)
    ):
        return True
    for handle in claim.evidence:
        if (
            handle.created_at is not None
            and _datetime_predates_authority(
                handle.created_at,
                expected_claim_not_before,
            )
        ):
            return True
        if _artifact_predates_authority(handle, expected_claim_not_before):
            return True
    return False


def _claim_recency_sort_key(claim: EvidenceClaim) -> tuple[datetime, str]:
    return claim.created_at.replace(tzinfo=None), claim.claim_id


def _datetime_predates_authority(
    value: datetime,
    expected_claim_not_before: datetime,
) -> bool:
    if _is_timezone_aware(value):
        return False
    return value < expected_claim_not_before


def _artifact_predates_authority(
    handle: EvidenceHandle,
    expected_claim_not_before: datetime,
) -> bool:
    if not handle.path or not handle.checksum_sha256:
        return False
    path = Path(handle.path)
    if not path.is_file():
        return False
    try:
        if _sha256_file(path) != handle.checksum_sha256:
            return False
        data = load_json_object(path, schema_name="FixturePoseEvidenceArtifact")
    except (OSError, ValueError, TypeError):
        return False
    for field in ("created_at", "image_captured_at"):
        value = _artifact_datetime(data, field)
        if value is not None and value < expected_claim_not_before:
            return True
    return False


def _claim_is_session_scoped(claim: EvidenceClaim) -> bool:
    return bool(claim.session_id or any(handle.session_id for handle in claim.evidence))


def _expected_pose_claim_source_kind(claim_type: str) -> EvidenceSourceKind:
    if claim_type == POSE_UPRIGHT_CLAIM:
        return EvidenceSourceKind.FIXTURE_UPRIGHT
    return EvidenceSourceKind.FIXTURE_POSE_ORIENTATION


def _pose_claim_evidence_blockers(
    claim: EvidenceClaim,
    *,
    pose: FixturePose,
    claim_type: str,
    expected_source_kind: EvidenceSourceKind,
    expected_session_id: str | None,
    expected_robot_url: str | None,
    expected_fixture_params_sha256: str | None,
    expected_evidence_index_path: str | Path | None,
    expected_claim_not_before: datetime | None,
    claim_valid_at: datetime,
) -> list[str]:
    blockers: list[str] = []
    if len(claim.evidence) != 1:
        return [f"pose claim {claim_type} must have exactly one evidence handle"]
    handle = claim.evidence[0]
    if handle.source_kind != expected_source_kind:
        blockers.append(f"pose claim {claim_type} evidence source does not match")
    if handle.quality != EvidenceQuality.USABLE:
        blockers.append(f"pose claim {claim_type} evidence handle is not usable")
    if not handle.path:
        blockers.append(f"pose claim {claim_type} evidence handle path is missing")
    if not handle.checksum_sha256:
        blockers.append(f"pose claim {claim_type} evidence handle checksum is missing")
    if expected_session_id is not None and handle.session_id != expected_session_id:
        blockers.append(f"pose claim {claim_type} evidence session does not match")
    if handle.created_at is None:
        blockers.append(f"pose claim {claim_type} evidence created_at is missing")
    else:
        handle_created_at_is_usable = True
        if _is_timezone_aware(handle.created_at):
            blockers.append(f"pose claim {claim_type} evidence created_at is timezone-aware")
            handle_created_at_is_usable = False
        if (
            expected_claim_not_before is not None
            and handle_created_at_is_usable
            and handle.created_at < expected_claim_not_before
        ):
            blockers.append(f"pose claim {claim_type} evidence predates active session authority")
        if handle_created_at_is_usable and handle.created_at > claim_valid_at:
            blockers.append(f"pose claim {claim_type} evidence is from the future")
    if handle.path and handle.checksum_sha256:
        blockers.extend(
            _pose_claim_artifact_blockers(
                claim,
                pose=pose,
                claim_type=claim_type,
                handle=handle,
                expected_session_id=expected_session_id,
                expected_robot_url=expected_robot_url,
                expected_fixture_params_sha256=expected_fixture_params_sha256,
                expected_evidence_index_path=expected_evidence_index_path,
                expected_claim_not_before=expected_claim_not_before,
                claim_valid_at=claim_valid_at,
            )
        )
    return blockers


def _pose_claim_artifact_blockers(
    claim: EvidenceClaim,
    *,
    pose: FixturePose,
    claim_type: str,
    handle: EvidenceHandle,
    expected_session_id: str | None,
    expected_robot_url: str | None,
    expected_fixture_params_sha256: str | None,
    expected_evidence_index_path: str | Path | None,
    expected_claim_not_before: datetime | None,
    claim_valid_at: datetime,
) -> list[str]:
    path = Path(handle.path)
    if not path.is_file():
        return [f"pose claim {claim_type} evidence artifact is missing"]
    if _sha256_file(path) != handle.checksum_sha256:
        return [f"pose claim {claim_type} evidence artifact checksum does not match"]
    try:
        data = load_json_object(path, schema_name="FixturePoseEvidenceArtifact")
    except (OSError, ValueError, TypeError) as exc:
        return [f"pose claim {claim_type} evidence artifact is invalid: {exc}"]

    blockers: list[str] = []
    _require_artifact_value(data, "schema_version", 1, claim_type, blockers)
    artifact_created_at = _artifact_datetime(data, "created_at")
    if artifact_created_at is None:
        blockers.append(f"pose claim {claim_type} evidence artifact created_at is missing")
    else:
        if (
            expected_claim_not_before is not None
            and artifact_created_at < expected_claim_not_before
        ):
            blockers.append(
                f"pose claim {claim_type} evidence artifact predates active session authority"
            )
        if artifact_created_at > claim_valid_at:
            blockers.append(f"pose claim {claim_type} evidence artifact is from the future")
    image_captured_at = _artifact_datetime(data, "image_captured_at")
    if image_captured_at is None:
        blockers.append(
            f"pose claim {claim_type} evidence artifact image_captured_at is missing"
        )
    else:
        if (
            expected_claim_not_before is not None
            and image_captured_at < expected_claim_not_before
        ):
            blockers.append(
                f"pose claim {claim_type} evidence image capture predates active "
                "session authority"
            )
        if image_captured_at > claim_valid_at:
            blockers.append(f"pose claim {claim_type} evidence image capture is from the future")
        if not _is_timezone_aware(claim.created_at) and image_captured_at > claim.created_at:
            blockers.append(
                f"pose claim {claim_type} evidence image capture is after claim creation"
            )
    _require_artifact_value(data, "session_id", claim.session_id, claim_type, blockers)
    if expected_session_id is not None:
        _require_artifact_value(data, "session_id", expected_session_id, claim_type, blockers)
    _require_artifact_value(
        data,
        "fixture_load_name",
        pose.fixture_load_name,
        claim_type,
        blockers,
    )
    expected_params = expected_fixture_params_sha256 or claim.fixture_params_sha256
    _require_artifact_value(
        data,
        "fixture_params_sha256",
        expected_params,
        claim_type,
        blockers,
    )
    _require_artifact_value(
        data,
        "labware_definition_sha256",
        pose.fixture_definition_sha256,
        claim_type,
        blockers,
    )
    _require_artifact_value(
        data,
        "pose_digest_sha256",
        pose.pose_digest_sha256,
        claim_type,
        blockers,
    )
    _require_artifact_value(data, "slot", pose.slot, claim_type, blockers)
    _require_artifact_value(data, "quality", EvidenceQuality.USABLE.value, claim_type, blockers)
    if not str(data.get("inspection_note", "")).strip():
        blockers.append(f"pose claim {claim_type} evidence artifact inspection note is missing")
    if not str(data.get("image_capture_robot_url", "")).strip():
        blockers.append(
            f"pose claim {claim_type} evidence artifact image capture robot is missing"
        )
    if expected_robot_url is not None:
        _require_artifact_value(
            data,
            "image_capture_robot_url",
            expected_robot_url.rstrip("/"),
            claim_type,
            blockers,
        )
    if data.get("image_capture_endpoint") != "/camera/picture":
        blockers.append(
            f"pose claim {claim_type} evidence artifact image capture endpoint does not match"
        )
    if data.get("image_capture_checksum_sha256") != data.get("image_checksum_sha256"):
        blockers.append(
            f"pose claim {claim_type} evidence artifact image capture checksum does not match"
        )
    blockers.extend(
        _artifact_camera_event_blockers(
            data,
            claim_type=claim_type,
            expected_session_id=expected_session_id,
            expected_robot_url=expected_robot_url,
            expected_evidence_index_path=expected_evidence_index_path,
        )
    )
    blockers.extend(
        _artifact_file_blockers(
            data,
            path_field="image_path",
            checksum_field="image_checksum_sha256",
            claim_type=claim_type,
            label="image",
        )
    )
    if data.get("vision_result_path") or data.get("vision_result_checksum_sha256"):
        blockers.extend(
            _artifact_file_blockers(
                data,
                path_field="vision_result_path",
                checksum_field="vision_result_checksum_sha256",
                claim_type=claim_type,
                label="vision result",
            )
        )
    if claim_type == POSE_UPRIGHT_CLAIM:
        _require_artifact_value(data, "fixture_upright", True, claim_type, blockers)
    else:
        _require_artifact_value(
            data,
            "observed_orientation",
            pose.orientation.value,
            claim_type,
            blockers,
        )
    return blockers


def _artifact_datetime(data: dict[str, object], field: str) -> datetime | None:
    value = data.get(field)
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if _is_timezone_aware(parsed):
        return None
    return parsed


def _artifact_camera_event_blockers(
    data: dict[str, object],
    *,
    claim_type: str,
    expected_session_id: str | None,
    expected_robot_url: str | None,
    expected_evidence_index_path: str | Path | None,
) -> list[str]:
    if expected_session_id is None:
        return []
    if expected_evidence_index_path is None:
        return [
            f"pose claim {claim_type} evidence artifact camera capture index is missing"
        ]
    try:
        index = load_evidence_index(expected_evidence_index_path)
    except (OSError, SchemaVersionError, ValueError):
        return [
            f"pose claim {claim_type} evidence artifact camera capture index is invalid"
        ]
    for event in index.events:
        if event.event_type != "ot2_camera_picture":
            continue
        if event.session_id != expected_session_id:
            continue
        payload = event.payload
        if (
            _same_path(payload.get("image_path"), data.get("image_path"))
            and payload.get("image_checksum_sha256") == data.get("image_checksum_sha256")
            and payload.get("captured_at") == data.get("image_captured_at")
            and payload.get("robot_url") == data.get("image_capture_robot_url")
            and (
                expected_robot_url is None
                or payload.get("robot_url") == expected_robot_url.rstrip("/")
            )
            and payload.get("endpoint") == data.get("image_capture_endpoint")
        ):
            return []
    return [
        f"pose claim {claim_type} evidence artifact camera capture is not indexed"
    ]


def _require_artifact_value(
    data: dict[str, object],
    field: str,
    expected: object,
    claim_type: str,
    blockers: list[str],
) -> None:
    if data.get(field) != expected:
        blockers.append(f"pose claim {claim_type} evidence artifact {field} does not match")


def _artifact_file_blockers(
    data: dict[str, object],
    *,
    path_field: str,
    checksum_field: str,
    claim_type: str,
    label: str,
) -> list[str]:
    path = data.get(path_field)
    checksum = data.get(checksum_field)
    if not isinstance(path, str) or not isinstance(checksum, str) or not path or not checksum:
        return [f"pose claim {claim_type} evidence artifact {label} path/checksum missing"]
    file_path = Path(path)
    if not file_path.is_file():
        return [f"pose claim {claim_type} evidence artifact {label} is missing"]
    if _sha256_file(file_path) != checksum:
        return [f"pose claim {claim_type} evidence artifact {label} checksum does not match"]
    return []


def _apply_matrix(point: Point3D, matrix: TransformMatrix) -> Point3D:
    x = matrix[0][0] * point.x + matrix[0][1] * point.y + matrix[0][2] * point.z + matrix[0][3]
    y = matrix[1][0] * point.x + matrix[1][1] * point.y + matrix[1][2] * point.z + matrix[1][3]
    z = matrix[2][0] * point.x + matrix[2][1] * point.y + matrix[2][2] * point.z + matrix[2][3]
    return Point3D(x=_round_mm(x), y=_round_mm(y), z=_round_mm(z))


def _dimension(fixture_identity: FixtureIdentity, key: Literal["x", "y", "z"]) -> float:
    dimensions = fixture_identity.labware_dimensions_mm
    return float(dimensions[key])


def _round_mm(value: float) -> float:
    rounded = round(float(value), MATRIX_PRECISION_MM)
    # Normalize negative zero so JSON digest payloads remain stable.
    return 0.0 if rounded == -0.0 else rounded


def _canonicalize(payload: object) -> object:
    if isinstance(payload, float):
        return _round_mm(payload)
    if isinstance(payload, dict):
        return {str(key): _canonicalize(value) for key, value in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [_canonicalize(value) for value in payload]
    if isinstance(payload, StrEnum):
        return payload.value
    return payload


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _dedupe_evidence(evidence: list[EvidenceHandle]) -> list[EvidenceHandle]:
    deduped: list[EvidenceHandle] = []
    seen: set[tuple[str, str, str]] = set()
    for handle in evidence:
        key = (handle.evidence_id, handle.source_kind.value, handle.path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(handle)
    return deduped
