from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EndpointResult(BaseModel):
    path: str
    ok: bool
    status_code: int | None = None
    data: dict[str, Any] | list[Any] | None = None
    text: str | None = None
    error: str | None = None


class RobotStatus(BaseModel):
    robot_url: str
    checked_at: datetime
    health: EndpointResult
    pipettes: EndpointResult | None = None
    openapi: EndpointResult | None = None


class RobotDiscoveryResult(BaseModel):
    robot_url: str
    source: Literal["argument", "environment", "mdns"]
    service_name: str | None = None
    service_type: str | None = None
    server: str | None = None
    addresses: list[str] = Field(default_factory=list)
    port: int | None = None
    properties: dict[str, str] = Field(default_factory=dict)


class CameraCaptureResult(BaseModel):
    robot_url: str
    captured_at: datetime
    endpoint: str
    image_path: str
    image_checksum_sha256: str = ""
    content_type: str | None = None
    bytes_written: int


class ImageMetrics(BaseModel):
    width_px: int
    height_px: int
    mode: str
    mean_luma: float
    luma_stddev: float
    edge_mean: float


class VisionCheck(BaseModel):
    name: str
    passed: bool
    severity: Literal["info", "warning", "blocker"]
    details: str
    observed: float | int | str | bool | None = None
    threshold: float | int | str | bool | None = None


class VisionAnalysisResult(BaseModel):
    image_path: str
    analyzed_at: datetime
    purpose: Literal["deck_baseline", "fixture_presence", "high_z_target", "recovery"]
    metrics: ImageMetrics | None = None
    evidence_ok: bool
    motion_gate: bool
    checks: list[VisionCheck] = Field(default_factory=list)
    summary: str


class FixtureIdentity(BaseModel):
    load_name: str
    namespace: str
    version: int
    params_path: str
    labware_path: str
    params_sha256: str
    labware_definition_sha256: str
    nominal_dimensions_mm: dict[str, float]
    labware_dimensions_mm: dict[str, float]
    dimensions_match: bool


class EvidenceEvent(BaseModel):
    event_type: str
    created_at: datetime = Field(default_factory=datetime.now)
    session_id: str | None = None
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)


class EvidenceIndex(BaseModel):
    schema_version: int = 1
    events: list[EvidenceEvent] = Field(default_factory=list)


class EvidenceSourceKind(StrEnum):
    GENERATED_ARTIFACT = "generated_artifact"
    ROBOT_STATE = "robot_state"
    COMMAND_RESPONSE = "command_response"
    COMMAND_HISTORY = "command_history"
    CAMERA_CAPTURE = "camera_capture"
    VISION_ANALYSIS = "vision_analysis"
    PHYSICAL_MEASUREMENT = "physical_measurement"
    INSPECTION_NOTE = "inspection_note"
    OFFSET_MEASUREMENT = "offset_measurement"
    FIXTURE_POSE_ORIENTATION = "fixture_pose_orientation"
    FIXTURE_UPRIGHT = "fixture_upright"
    OBSERVER_FRAME = "observer_frame"
    HIGH_Z_LANDING = "high_z_landing"


class EvidenceQuality(StrEnum):
    USABLE = "usable"
    AMBIGUOUS = "ambiguous"
    FAILED = "failed"
    LEGACY = "legacy"


ClaimValue = bool | int | float | str


class EvidenceHandle(BaseModel):
    schema_version: int = 1
    evidence_id: str
    source_kind: EvidenceSourceKind
    path: str = ""
    checksum_sha256: str = ""
    created_at: datetime | None = None
    session_id: str = ""
    quality: EvidenceQuality = EvidenceQuality.LEGACY


class EvidencePacket(BaseModel):
    schema_version: int = 1
    evidence_id: str
    source_kind: EvidenceSourceKind
    created_at: datetime = Field(default_factory=datetime.now)
    session_id: str = ""
    robot_serial: str = ""
    robot_server_version: str = ""
    fixture_load_name: str = ""
    fixture_params_sha256: str = ""
    labware_definition_sha256: str = ""
    pose_digest_sha256: str = ""
    operation: str = ""
    command_id: str = ""
    artifact_path: str = ""
    checksum_sha256: str = ""
    provenance: dict[str, str] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS
    notes: list[str] = Field(default_factory=list)


class EvidenceClaim(BaseModel):
    schema_version: int = 1
    claim_id: str
    claim_type: str
    value: ClaimValue
    created_at: datetime = Field(default_factory=datetime.now)
    session_id: str = ""
    fixture_load_name: str = ""
    fixture_params_sha256: str = ""
    labware_definition_sha256: str = ""
    pose_digest_sha256: str = ""
    method: str
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS
    evidence: list[EvidenceHandle] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class BridgeLeaseKind(StrEnum):
    """The mutually-exclusive kinds of motion lease the single-writer bridge can hold.

    The bridge keeps exactly one non-terminal lock per ``robot_url`` (see
    ``aevum_ot2.core.lock``), so these kinds are mutually exclusive by construction:
    whichever subsystem asks second is refused. ``PIPETTING`` is the OT-2's existing lease
    (the default, so prior sessions are unchanged); ``OBSERVER_SCAN`` is the observer's
    (IN-C4 / HX1). Consumed by both ``ObserverScanEvidence`` (provenance) and ``BridgeLock``.
    """

    PIPETTING = "pipetting"
    OBSERVER_SCAN = "observer_scan"


class ObserverScanEvidence(BaseModel):
    """Immutable evidence packet for one observer scan frame (one well, one modality).

    Minted only against a valid ``observer_scan`` bridge lease — see
    ``aevum_ot2.core.observer.mint_observer_scan_evidence`` (IN-C4 / HX1). It is the
    observer counterpart to the SMIS-side ``ModuleEvidence``; mapping it into the bridge's
    durable ``EvidencePacket`` store is the IN-C5 cross-package cycle, so this contract is
    frozen here and emits an ``EvidenceHandle`` rather than authorizing motion itself.

    Authority boundaries kept distinct (do not collapse into one success boolean):

    - ``session_id``/``owner_id``/``lease_kind`` bind the frame to the *lease* that
      authorized it (software/motion authority).
    - ``pose_digest_sha256`` is the fiducial-transform checksum carried as *registration
      provenance*. It is NOT a registration gate — registration acceptance is a separate
      authority (HX2 / IN-C5/C6). An empty digest is allowed at this layer; the registration
      gate, not this schema, decides whether a frame may be acquired without one.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    evidence_id: str
    well_id: str
    focus_z_mm: float
    focus_metric: float
    illumination_mode: str
    captured_at: datetime = Field(default_factory=datetime.now)
    session_id: str
    owner_id: str
    lease_kind: str = BridgeLeaseKind.OBSERVER_SCAN
    run_id: str = ""
    pose_digest_sha256: str = ""
    artifact_path: str = ""
    checksum_sha256: str = ""
    quality: EvidenceQuality = EvidenceQuality.AMBIGUOUS

    @model_validator(mode="after")
    def _validate_pose_digest(self) -> ObserverScanEvidence:
        if self.pose_digest_sha256 and len(self.pose_digest_sha256) != 64:
            raise ValueError(
                "pose_digest_sha256 must be a 64-character sha256 when present"
            )
        return self

    def to_handle(self) -> EvidenceHandle:
        """Emit the compact handle gates/context consume, not the raw frame payload."""
        return EvidenceHandle(
            evidence_id=self.evidence_id,
            source_kind=EvidenceSourceKind.OBSERVER_FRAME,
            path=self.artifact_path,
            checksum_sha256=self.checksum_sha256,
            created_at=self.captured_at,
            session_id=self.session_id,
            quality=self.quality,
        )


class GateName(StrEnum):
    FIXTURE_QC = "fixture_qc"
    REGISTRATION = "registration"
    POSE_MATCH = "pose_match"
    TARGET_CLASS_AUTHORITY = "target_class_authority"
    FIRST_HIGH_Z = "first_high_z"
    OFFSET_AUTHORITY = "offset_authority"
    LOW_Z_DRY = "low_z_dry"
    WET = "wet"
    RECOVERY = "recovery"
    HOME_CLEARANCE = "home_clearance"


class GateResult(BaseModel):
    schema_version: int = 1
    gate_name: GateName
    passed: bool
    motion_allowed: bool = False
    blockers: list[str] = Field(default_factory=list)
    missing_claims: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    evidence: list[EvidenceHandle] = Field(default_factory=list)


class OffsetAuthorityState(StrEnum):
    PROPOSED = "proposed"
    PROMOTED = "promoted"


class OffsetRecord(BaseModel):
    schema_version: int = 1
    offset_record_id: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    authority_state: OffsetAuthorityState = OffsetAuthorityState.PROPOSED
    robot_serial: str
    robot_server_version: str | None = None
    opentrons_api_version: str | None = None
    fixture_load_name: str
    fixture_definition_uri: str
    fixture_params_sha256: str
    labware_definition_sha256: str
    pose_digest_sha256: str = ""
    slot: str
    pipette_name: str
    pipette_mount: str
    tiprack_load_name: str
    offset_mm: dict[Literal["x", "y", "z"], float]
    verification_targets: list[str] = Field(default_factory=list)
    camera_evidence: list[str] = Field(default_factory=list)
    evidence_file: str
    safety_profile_sha256: str = ""
    target_policy_digest_sha256: str = ""
    run_id: str | None = None


class OffsetRegistry(BaseModel):
    schema_version: int = 1
    records: list[OffsetRecord] = Field(default_factory=list)


class BridgeSessionKind(StrEnum):
    REGISTRATION = "registration"
    DRY_RUN = "dry_run"
    RECOVERY = "recovery"
    NO_MOTION_PROBE = "no_motion_probe"


class BridgeSessionState(StrEnum):
    MAINTENANCE_RUN_CREATED = "maintenance_run_created"
    READY_NO_MOTION = "ready_no_motion"
    CLOSE_FAILED = "close_failed"
    CLOSED = "closed"
    FAILED = "failed"
    RECOVERY_REQUIRED = "recovery_required"
    MOTION_COMMISSIONING_ARMED = "motion_commissioning_armed"
    HIGH_Z_READY = "high_z_ready"
    DRY_READY = "dry_ready"
    WET_READY = "wet_ready"


class BridgeLock(BaseModel):
    robot_url: str
    session_id: str
    owner_id: str
    lease_started_at: datetime
    lease_expires_at: datetime
    active_run_id: str | None = None
    last_command_id: str | None = None
    state: str = "active"
    # Which mutually-exclusive lease this lock represents. Defaults to PIPETTING so every
    # existing OT-2 session is unchanged; the observer requests OBSERVER_SCAN (IN-C4 / HX1).
    lease_kind: str = BridgeLeaseKind.PIPETTING


class BridgeSession(BaseModel):
    schema_version: int = 1
    session_id: str
    kind: BridgeSessionKind
    owner_id: str
    robot_url: str
    robot_serial: str | None = None
    robot_server_version: str | None = None
    max_protocol_api_version: str | None = None
    pipette_name: str = ""
    pipette_mount: Literal["", "left", "right"] = ""
    pipette_model: str = ""
    pipette_id: str = ""
    pipette_tip_length_mm: float | None = None
    state: BridgeSessionState
    created_at: datetime
    updated_at: datetime
    lease_expires_at: datetime
    maintenance_run_id: str | None = None
    slot: str
    fixture_identity: FixtureIdentity
    fixture_orientation: Literal["", "canonical", "rot180"] = ""
    fixture_pose_digest_sha256: str = ""
    fixture_pose_path: str = ""
    definition_uri: str | None = None
    loaded_labware_id: str | None = None
    last_command_id: str | None = None
    last_command_key: str | None = None
    last_command_type: str | None = None
    last_command_status: str | None = None
    evidence_index_path: str
    motion_allowed: bool = False
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_fixture_pose_metadata(self) -> BridgeSession:
        fields = [
            self.fixture_orientation,
            self.fixture_pose_digest_sha256,
            self.fixture_pose_path,
        ]
        if any(fields) and not all(fields):
            raise ValueError(
                "fixture pose metadata must include orientation, digest, and path together"
            )
        if self.fixture_pose_digest_sha256 and len(self.fixture_pose_digest_sha256) != 64:
            raise ValueError("fixture_pose_digest_sha256 must be a 64-character sha256")
        return self


class NoMotionSessionInitReport(BaseModel):
    robot_url: str
    created_at: datetime = Field(default_factory=datetime.now)
    session: BridgeSession | None = None
    lock: BridgeLock | None = None
    status: RobotStatus
    protocol_runs: EndpointResult
    create_result: EndpointResult | None = None
    upload_definition_result: EndpointResult | None = None
    load_labware_result: EndpointResult | None = None
    run_get_result: EndpointResult | None = None
    cleanup_delete_result: EndpointResult | None = None
    cleanup_confirm_result: EndpointResult | None = None
    motion_commands_sent: bool = False
    notes: list[str] = Field(default_factory=list)


class NoMotionSessionCloseReport(BaseModel):
    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    session_before: BridgeSession | None = None
    delete_result: EndpointResult | None = None
    post_delete_get_result: EndpointResult | None = None
    session_after: BridgeSession | None = None
    lock: BridgeLock | None = None
    motion_commands_sent: bool = False
    notes: list[str] = Field(default_factory=list)


class ApiSpikeReport(BaseModel):
    robot_url: str
    created_at: datetime = Field(default_factory=datetime.now)
    artifact_identity: FixtureIdentity
    status: RobotStatus
    notes: list[str] = Field(default_factory=list)


class MaintenanceRunLifecycleReport(BaseModel):
    robot_url: str
    created_at: datetime = Field(default_factory=datetime.now)
    status: RobotStatus
    protocol_runs: EndpointResult
    create_result: EndpointResult | None = None
    created_run_id: str | None = None
    get_result: EndpointResult | None = None
    commands_result: EndpointResult | None = None
    delete_result: EndpointResult | None = None
    post_delete_get_result: EndpointResult | None = None
    no_motion_commands_sent: bool = True
    notes: list[str] = Field(default_factory=list)


class MaintenanceCommandKeyReport(BaseModel):
    robot_url: str
    created_at: datetime = Field(default_factory=datetime.now)
    status: RobotStatus
    protocol_runs: EndpointResult
    create_result: EndpointResult | None = None
    created_run_id: str | None = None
    command_key: str
    first_command_result: EndpointResult | None = None
    first_command_id: str | None = None
    first_command_status: str | None = None
    first_command_detail_result: EndpointResult | None = None
    commands_after_first_result: EndpointResult | None = None
    duplicate_key_result: EndpointResult | None = None
    duplicate_command_id: str | None = None
    duplicate_command_status: str | None = None
    commands_after_duplicate_result: EndpointResult | None = None
    delete_result: EndpointResult | None = None
    post_delete_get_result: EndpointResult | None = None
    motion_commands_sent: bool = False
    notes: list[str] = Field(default_factory=list)


class MaintenanceLabwareDefinitionReport(BaseModel):
    robot_url: str
    created_at: datetime = Field(default_factory=datetime.now)
    status: RobotStatus
    protocol_runs: EndpointResult
    artifact_identity: FixtureIdentity
    slot: str
    load_key: str
    pre_upload_create_result: EndpointResult | None = None
    pre_upload_run_id: str | None = None
    pre_upload_load_result: EndpointResult | None = None
    pre_upload_command_id: str | None = None
    pre_upload_command_status: str | None = None
    pre_upload_delete_result: EndpointResult | None = None
    upload_create_result: EndpointResult | None = None
    upload_run_id: str | None = None
    upload_definition_result: EndpointResult | None = None
    definition_uri: str | None = None
    post_upload_load_result: EndpointResult | None = None
    post_upload_command_id: str | None = None
    post_upload_command_status: str | None = None
    loaded_labware_id: str | None = None
    upload_run_get_result: EndpointResult | None = None
    upload_run_commands_result: EndpointResult | None = None
    upload_delete_result: EndpointResult | None = None
    post_delete_get_result: EndpointResult | None = None
    motion_commands_sent: bool = False
    notes: list[str] = Field(default_factory=list)


def parse_gate_result(
    data: Mapping[str, Any],
    *,
    path: str | Path | None = None,
) -> GateResult:
    from aevum_ot2.core.schema import (
        parse_versioned_json_model,
        require_schema_versioned_items,
    )

    if isinstance(data, Mapping):
        require_schema_versioned_items(
            data.get("evidence"),
            schema_name="EvidenceHandle",
            path=path,
        )
    return parse_versioned_json_model(
        data,
        GateResult,
        schema_name="GateResult",
        path=path,
    )


def load_gate_result(path: str | Path) -> GateResult:
    from aevum_ot2.core.schema import load_json_object

    data = load_json_object(path, schema_name="GateResult")
    return parse_gate_result(data, path=path)
