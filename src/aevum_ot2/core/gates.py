from __future__ import annotations

from pathlib import Path

from aevum_ot2.core.evidence_primitives import _sha256_file
from aevum_ot2.core.models import (
    EvidenceClaim,
    EvidenceHandle,
    EvidenceQuality,
    EvidenceSourceKind,
    GateName,
    GateResult,
)
from aevum_ot2.core.records import (
    REQUIRED_QC_MEASUREMENTS,
    FixtureQcRecord,
    RecordHandle,
    fixture_qc_record_handle,
)

FIXTURE_DIMENSIONS_CLAIM = "fixture_dimensions_within_tolerance"

FIXTURE_QC_LEGACY_CLAIMS: dict[str, tuple[str, EvidenceSourceKind]] = {
    "camera_capture_indexed": ("camera_capture_indexed", EvidenceSourceKind.CAMERA_CAPTURE),
    "fixture_visible": ("fixture_visible_in_slot", EvidenceSourceKind.VISION_ANALYSIS),
    "vision_evidence_ok": ("vision_evidence_usable", EvidenceSourceKind.VISION_ANALYSIS),
    "base_seated": ("fixture_base_seated", EvidenceSourceKind.INSPECTION_NOTE),
    "guide_holes_open": ("guide_holes_open", EvidenceSourceKind.INSPECTION_NOTE),
    "support_debris_absent": ("support_debris_absent", EvidenceSourceKind.INSPECTION_NOTE),
    "mock_wells_undeformed": ("mock_wells_undeformed", EvidenceSourceKind.INSPECTION_NOTE),
    "no_warping_lift": ("no_warping_lift", EvidenceSourceKind.INSPECTION_NOTE),
}

FIXTURE_QC_REQUIRED_CLAIMS = (
    FIXTURE_DIMENSIONS_CLAIM,
    "camera_capture_indexed",
    "fixture_visible_in_slot",
    "vision_evidence_usable",
    "fixture_base_seated",
    "guide_holes_open",
    "support_debris_absent",
    "mock_wells_undeformed",
    "no_warping_lift",
)
FIXTURE_QC_ACCEPTED_QUALITIES = {EvidenceQuality.USABLE, EvidenceQuality.LEGACY}


def fixture_qc_claims_from_legacy_record(
    record: FixtureQcRecord,
    *,
    record_handle: RecordHandle | None = None,
) -> list[EvidenceClaim]:
    """Adapt the current FixtureQcRecord shape into source-agnostic claims."""

    handle = record_handle or fixture_qc_record_handle(record, "")
    return [
        _dimension_claim(record, handle),
        *[
            _boolean_claim(
                record,
                handle,
                field_name=field_name,
                claim_type=claim_type,
                source_kind=source_kind,
            )
            for field_name, (claim_type, source_kind) in FIXTURE_QC_LEGACY_CLAIMS.items()
        ],
    ]


def fixture_qc_gate_from_claims(claims: list[EvidenceClaim]) -> GateResult:
    claim_by_type = {claim.claim_type: claim for claim in claims}
    blockers: list[str] = []
    missing_claims: list[str] = []
    evidence: list[EvidenceHandle] = []
    claim_ids: list[str] = []

    for claim_type in FIXTURE_QC_REQUIRED_CLAIMS:
        claim = claim_by_type.get(claim_type)
        if claim is None:
            missing_claims.append(claim_type)
            continue
        claim_ids.append(claim.claim_id)
        evidence.extend(claim.evidence)
        if claim.quality not in FIXTURE_QC_ACCEPTED_QUALITIES or claim.value is not True:
            blockers.append(f"claim {claim_type} is not an accepted true claim")
        blockers.extend(claim.reasons)

    return GateResult(
        gate_name=GateName.FIXTURE_QC,
        passed=not blockers and not missing_claims,
        motion_allowed=False,
        blockers=_dedupe(blockers),
        missing_claims=missing_claims,
        claim_ids=claim_ids,
        evidence=_dedupe_evidence(evidence),
    )


def fixture_qc_gate_from_legacy_record(
    record: FixtureQcRecord,
    *,
    record_handle: RecordHandle | None = None,
) -> GateResult:
    return fixture_qc_gate_from_claims(
        fixture_qc_claims_from_legacy_record(record, record_handle=record_handle)
    )


def registration_gate_result(
    *,
    blockers: list[str],
    fixture_qc_gate: GateResult | None = None,
    pose_gate: GateResult | None = None,
    missing_target_classes: list[str] | None = None,
) -> GateResult:
    missing_claims = []
    claim_ids: list[str] = []
    evidence: list[EvidenceHandle] = []
    gate_blockers = list(blockers)

    if fixture_qc_gate is None:
        missing_claims.append("fixture_qc_gate")
    else:
        claim_ids.extend(fixture_qc_gate.claim_ids)
        evidence.extend(fixture_qc_gate.evidence)
        gate_blockers.extend(fixture_qc_gate.blockers)
        missing_claims.extend(fixture_qc_gate.missing_claims)

    if pose_gate is not None:
        claim_ids.extend(pose_gate.claim_ids)
        evidence.extend(pose_gate.evidence)
        gate_blockers.extend(pose_gate.blockers)
        missing_claims.extend(pose_gate.missing_claims)

    for target_class in missing_target_classes or []:
        missing_claims.append(f"target_class_record:{target_class}")

    return GateResult(
        gate_name=GateName.REGISTRATION,
        passed=not gate_blockers and not missing_claims,
        motion_allowed=False,
        blockers=_dedupe(gate_blockers),
        missing_claims=_dedupe(missing_claims),
        claim_ids=_dedupe(claim_ids),
        evidence=_dedupe_evidence(evidence),
    )


def _dimension_claim(record: FixtureQcRecord, handle: RecordHandle) -> EvidenceClaim:
    measurement_by_name = {
        measurement.name: measurement for measurement in record.measurements
    }
    missing_measurements = sorted(REQUIRED_QC_MEASUREMENTS - measurement_by_name.keys())
    failed_measurements = sorted(
        measurement.name for measurement in record.measurements if not measurement.passed
    )
    reasons = []
    if missing_measurements:
        reasons.append(
            "missing required QC measurements: " + ", ".join(missing_measurements)
        )
    if failed_measurements:
        reasons.append("failed QC measurements: " + ", ".join(failed_measurements))

    return EvidenceClaim(
        claim_id=_claim_id(record, FIXTURE_DIMENSIONS_CLAIM),
        claim_type=FIXTURE_DIMENSIONS_CLAIM,
        value=not reasons,
        fixture_load_name=record.fixture_load_name,
        fixture_params_sha256=record.fixture_params_sha256,
        labware_definition_sha256=record.labware_definition_sha256,
        method="legacy_fixture_qc_record_v1",
        quality=EvidenceQuality.LEGACY if not reasons else EvidenceQuality.FAILED,
        evidence=[_legacy_record_evidence(handle, EvidenceSourceKind.PHYSICAL_MEASUREMENT)],
        reasons=reasons,
    )


def _boolean_claim(
    record: FixtureQcRecord,
    handle: RecordHandle,
    *,
    field_name: str,
    claim_type: str,
    source_kind: EvidenceSourceKind,
) -> EvidenceClaim:
    value = bool(getattr(record, field_name))
    return EvidenceClaim(
        claim_id=_claim_id(record, claim_type),
        claim_type=claim_type,
        value=value,
        fixture_load_name=record.fixture_load_name,
        fixture_params_sha256=record.fixture_params_sha256,
        labware_definition_sha256=record.labware_definition_sha256,
        method="legacy_fixture_qc_record_v1",
        quality=EvidenceQuality.LEGACY if value else EvidenceQuality.FAILED,
        evidence=[_legacy_record_evidence(handle, source_kind)],
        reasons=[] if value else [f"fixture QC field {field_name} is false"],
    )


def _legacy_record_evidence(
    handle: RecordHandle,
    source_kind: EvidenceSourceKind,
) -> EvidenceHandle:
    return EvidenceHandle(
        evidence_id=f"legacy:{handle.record_type}:{handle.record_id}:{source_kind.value}",
        source_kind=source_kind,
        path=str(Path(handle.path)) if handle.path else "",
        checksum_sha256=_sha256_if_file(handle.path),
        quality=EvidenceQuality.LEGACY,
    )


def _claim_id(record: FixtureQcRecord, claim_type: str) -> str:
    return (
        f"fixture_qc:{record.fixture_load_name}:"
        f"{record.fixture_params_sha256[:12]}:"
        f"{record.labware_definition_sha256[:12]}:{claim_type}"
    )


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
        key = (handle.evidence_id, handle.source_kind, handle.path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(handle)
    return deduped


def _sha256_if_file(path: str) -> str:
    if not path:
        return ""
    candidate = Path(path)
    if not candidate.is_file():
        return ""
    return _sha256_file(candidate)
