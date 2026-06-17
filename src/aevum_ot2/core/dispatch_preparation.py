from __future__ import annotations

import hashlib
import math
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aevum_ot2.core.command_journal import CommandJournalEntry, new_command_journal_entry
from aevum_ot2.core.dispatch_reservation import (
    MotionDispatchReservation,
    motion_dispatch_reservation_id,
)
from aevum_ot2.core.evidence_primitives import _stable_json_sha256
from aevum_ot2.core.models import BridgeSession, EndpointResult
from aevum_ot2.core.motion_approval import MotionApproval, plan_fragment_digest
from aevum_ot2.core.plans import (
    PlanFragment,
    PlanOperation,
    PlanStep,
    canonicalize_plan_fragment,
)
from aevum_ot2.core.safety import FixtureSafetyProfile, safety_profile_integrity_blockers

MotionDispatchPreparationState = Literal["prepared_no_post"]
FIRST_HIGH_Z_TARGET_CLASS = "center_high_z"
FIRST_HIGH_Z_WELL_NAME = "A1"
FIRST_HIGH_Z_TOP_OFFSET_MM = 15.0
FIRST_HIGH_Z_SPEED_MM_PER_S = 20.0
FIRST_LOW_Z_DRY_TARGET_CLASS = "center_low_z_dry"
FIRST_LOW_Z_DRY_WELL_NAME = "A1"
# PROVISIONAL placeholder endpoint, NOT a verified-safe descent target. A safe per-well dry
# descent endpoint requires validated well-access geometry and a per-well descent FLOOR that
# the safety model does not yet carry (`dry_z_floor_mm` is the collision-envelope top, a
# lateral-transit clearance, not a descent floor -- e.g. the canonical fixture's A1 well-top
# is ~11 mm BELOW it). Until that endpoint is grounded, low-Z descent emission is refused
# (see LOW_Z_DRY_DESCENT_ENDPOINT_GROUNDED); this constant feeds only the unreachable tail.
FIRST_LOW_Z_DRY_TOP_OFFSET_MM = 0.0
# Half the high-Z transit speed: the low move runs closer to the fixture.
FIRST_LOW_Z_DRY_SPEED_MM_PER_S = 10.0
# Safe-allowlist gate (mirrors OT-1's empty CALIBRATED_OFFSET_SOURCES). A low-Z DESCENT can
# only be emitted once a per-well dry-descent endpoint is grounded against a real descent
# floor. `minimumZHeight` cannot stand in for that floor: per the Opentrons MoveToWellParams
# schema it only raises the lateral-transit ARC apex (and is a no-op below the API's default
# safe-Z margin) -- it never clamps the final descent. While this is False the translator
# builds + validates everything else but refuses to command a descent, fail-closed.
LOW_Z_DRY_DESCENT_ENDPOINT_GROUNDED = False


class MotionDispatchReadbackSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_status: str
    run_current: bool
    loaded_labware_id: str
    loaded_labware_definition_uri: str
    loaded_labware_slot: str
    loaded_labware_offset_id: str | None = None
    labware_offset_vector_mm: dict[Literal["x", "y", "z"], float]
    command_history_total_length: int
    last_observed_command_id: str | None = None
    last_observed_command_key: str | None = None
    last_observed_command_type: str | None = None
    last_observed_command_status: str | None = None


class MotionDispatchPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    preparation_id: str
    reservation_id: str
    approval_id: str
    session_id: str
    owner_id: str
    robot_url: str
    run_id: str
    step_id: str
    operation: PlanOperation
    state: MotionDispatchPreparationState = "prepared_no_post"
    command_path: str
    history_path: str
    command_body: dict[str, Any]
    command_body_sha256: str
    command_journal_entry: CommandJournalEntry
    readback: MotionDispatchReadbackSummary
    prepared_at: datetime = Field(default_factory=datetime.now)
    robot_command_posted: bool = False
    blockers: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_preparation(self) -> MotionDispatchPreparation:
        if self.schema_version != 1:
            raise ValueError("unsupported motion dispatch preparation schema version")
        if self.state != "prepared_no_post":
            raise ValueError("motion dispatch preparation must remain prepared_no_post")
        if self.robot_command_posted:
            raise ValueError("dispatch preparation cannot report a robot command post")
        if self.command_journal_entry.state != "prepared":
            raise ValueError("dispatch preparation requires a prepared command journal entry")
        if self.command_journal_entry.posted_at is not None:
            raise ValueError("dispatch preparation journal entry must not be posted")
        if self.command_journal_entry.command_id is not None:
            raise ValueError("dispatch preparation journal entry must not have command ID")
        if self.command_journal_entry.session_id != self.session_id:
            raise ValueError("dispatch preparation journal session does not match")
        if self.command_journal_entry.run_id != self.run_id:
            raise ValueError("dispatch preparation journal run does not match")
        if self.command_journal_entry.step_id != self.step_id:
            raise ValueError("dispatch preparation journal step does not match")
        if self.command_journal_entry.operation != self.operation:
            raise ValueError("dispatch preparation journal operation does not match")
        if self.command_journal_entry.journal_id != _journal_id(self.reservation_id):
            raise ValueError("dispatch preparation journal ID is not reservation-derived")
        if self.command_journal_entry.command_key != _command_key(self.reservation_id):
            raise ValueError("dispatch preparation command key is not reservation-derived")
        if self.command_body_sha256 != _stable_json_sha256(self.command_body):
            raise ValueError("dispatch preparation command body checksum mismatch")
        if self.command_journal_entry.command_body_sha256 != self.command_body_sha256:
            raise ValueError("dispatch preparation journal body checksum mismatch")
        if _history_path_run_id(self.command_path) != self.run_id:
            raise ValueError("dispatch preparation command path run does not match")
        if _history_path_run_id(self.history_path) != self.run_id:
            raise ValueError("dispatch preparation history path run does not match")
        return self


class MotionDispatchPreparationResult(BaseModel):
    prepared: bool = False
    preparation: MotionDispatchPreparation | None = None
    blockers: list[str] = Field(default_factory=list)


def build_motion_dispatch_preparation_for_approval(
    *,
    approval: MotionApproval,
    session: BridgeSession,
    plan: PlanFragment,
    safety_profile: FixtureSafetyProfile | None,
    run_result: EndpointResult,
    command_history_result: EndpointResult,
    now: datetime | None = None,
) -> MotionDispatchPreparationResult:
    reservation_id = motion_dispatch_reservation_id(approval.approval_id)
    return _build_motion_dispatch_preparation(
        reservation_id=reservation_id,
        approval_id=approval.approval_id,
        session_id=approval.session_id,
        owner_id=session.owner_id,
        robot_url=session.robot_url,
        run_id=session.maintenance_run_id or "",
        step_id=approval.step_id,
        operation=approval.operation,
        plan_digest_sha256=approval.plan_digest_sha256,
        safety_profile_sha256=approval.safety_profile_sha256,
        session=session,
        plan=plan,
        safety_profile=safety_profile,
        run_result=run_result,
        command_history_result=command_history_result,
        now=now,
    )


def build_motion_dispatch_preparation_for_reservation(
    *,
    reservation: MotionDispatchReservation,
    session: BridgeSession,
    plan: PlanFragment,
    safety_profile: FixtureSafetyProfile | None,
    run_result: EndpointResult,
    command_history_result: EndpointResult,
    now: datetime | None = None,
) -> MotionDispatchPreparationResult:
    return _build_motion_dispatch_preparation(
        reservation_id=reservation.reservation_id,
        approval_id=reservation.approval_id,
        session_id=reservation.session_id,
        owner_id=reservation.owner_id,
        robot_url=reservation.robot_url,
        run_id=reservation.run_id,
        step_id=reservation.step_id,
        operation=reservation.operation,
        plan_digest_sha256=reservation.plan_digest_sha256,
        safety_profile_sha256=reservation.safety_profile_sha256,
        session=session,
        plan=plan,
        safety_profile=safety_profile,
        run_result=run_result,
        command_history_result=command_history_result,
        now=now,
    )


def motion_dispatch_preparation_blockers(
    preparation: MotionDispatchPreparation,
    *,
    reservation: MotionDispatchReservation,
    session: BridgeSession,
) -> list[str]:
    blockers: list[str] = []
    if preparation.reservation_id != reservation.reservation_id:
        blockers.append("dispatch preparation reservation does not match reservation")
    if preparation.approval_id != reservation.approval_id:
        blockers.append("dispatch preparation approval does not match reservation")
    if preparation.session_id != reservation.session_id:
        blockers.append("dispatch preparation session does not match reservation")
    if preparation.owner_id != reservation.owner_id:
        blockers.append("dispatch preparation owner does not match reservation")
    if preparation.robot_url != reservation.robot_url:
        blockers.append("dispatch preparation robot URL does not match reservation")
    if preparation.run_id != reservation.run_id:
        blockers.append("dispatch preparation run does not match reservation")
    if preparation.step_id != reservation.step_id:
        blockers.append("dispatch preparation step does not match reservation")
    if preparation.operation != reservation.operation:
        blockers.append("dispatch preparation operation does not match reservation")
    if preparation.session_id != session.session_id:
        blockers.append("dispatch preparation session does not match persisted session")
    if preparation.owner_id != session.owner_id:
        blockers.append("dispatch preparation owner does not match persisted session")
    if preparation.robot_url != session.robot_url:
        blockers.append("dispatch preparation robot URL does not match persisted session")
    if preparation.run_id != (session.maintenance_run_id or ""):
        blockers.append("dispatch preparation run does not match persisted session")
    if preparation.command_journal_entry.journal_id != _journal_id(reservation.reservation_id):
        blockers.append("dispatch preparation journal ID is not reservation-derived")
    if preparation.command_journal_entry.command_key != _command_key(reservation.reservation_id):
        blockers.append("dispatch preparation command key is not reservation-derived")
    return _dedupe(blockers)


def _build_motion_dispatch_preparation(
    *,
    reservation_id: str,
    approval_id: str,
    session_id: str,
    owner_id: str,
    robot_url: str,
    run_id: str,
    step_id: str,
    operation: PlanOperation,
    plan_digest_sha256: str,
    safety_profile_sha256: str,
    session: BridgeSession,
    plan: PlanFragment,
    safety_profile: FixtureSafetyProfile | None,
    run_result: EndpointResult,
    command_history_result: EndpointResult,
    now: datetime | None,
) -> MotionDispatchPreparationResult:
    plan = canonicalize_plan_fragment(plan)
    checked_at = now or datetime.now()
    blockers = _scope_blockers(
        session_id=session_id,
        owner_id=owner_id,
        robot_url=robot_url,
        run_id=run_id,
        step_id=step_id,
        operation=operation,
        plan_digest_sha256=plan_digest_sha256,
        safety_profile_sha256=safety_profile_sha256,
        session=session,
        plan=plan,
        safety_profile=safety_profile,
    )
    readback, readback_blockers = _readback_summary(
        session=session,
        run_id=run_id,
        command_key=_command_key(reservation_id),
        safety_profile=safety_profile,
        run_result=run_result,
        command_history_result=command_history_result,
    )
    blockers.extend(readback_blockers)
    step = next((item for item in plan.steps if item.step_id == step_id), None)
    command_body, command_blockers = _command_body_for_operation(
        operation=operation,
        reservation_id=reservation_id,
        session=session,
        step=step,
        safety_profile=safety_profile,
    )
    blockers.extend(command_blockers)
    blockers = _dedupe(blockers)
    if blockers or readback is None or command_body is None or step is None:
        return MotionDispatchPreparationResult(blockers=blockers)

    entry = new_command_journal_entry(
        session=session,
        step=step,
        run_id=run_id,
        command_body=command_body,
        journal_id=_journal_id(reservation_id),
        prepared_at=checked_at,
    )
    preparation = MotionDispatchPreparation(
        preparation_id=_preparation_id(reservation_id),
        reservation_id=reservation_id,
        approval_id=approval_id,
        session_id=session_id,
        owner_id=owner_id,
        robot_url=robot_url,
        run_id=run_id,
        step_id=step_id,
        operation=operation,
        command_path=_command_path(run_id),
        history_path=_history_path(run_id),
        command_body=command_body,
        command_body_sha256=_stable_json_sha256(command_body),
        command_journal_entry=entry,
        readback=readback,
        prepared_at=checked_at,
    )
    return MotionDispatchPreparationResult(prepared=True, preparation=preparation)


def _scope_blockers(
    *,
    session_id: str,
    owner_id: str,
    robot_url: str,
    run_id: str,
    step_id: str,
    operation: PlanOperation,
    plan_digest_sha256: str,
    safety_profile_sha256: str,
    session: BridgeSession,
    plan: PlanFragment,
    safety_profile: FixtureSafetyProfile | None,
) -> list[str]:
    blockers: list[str] = []
    if session_id != session.session_id:
        blockers.append("dispatch preparation session does not match session")
    if owner_id != session.owner_id:
        blockers.append("dispatch preparation owner does not match session")
    if robot_url != session.robot_url:
        blockers.append("dispatch preparation robot URL does not match session")
    if run_id != (session.maintenance_run_id or ""):
        blockers.append("dispatch preparation run does not match session")
    if not run_id:
        blockers.append("dispatch preparation requires a maintenance run ID")
    if plan.session_id != session.session_id:
        blockers.append("dispatch preparation plan session does not match session")
    step = next((item for item in plan.steps if item.step_id == step_id), None)
    if step is None:
        blockers.append("dispatch preparation step is not in plan")
    elif step.operation != operation:
        blockers.append("dispatch preparation operation does not match plan")
    if plan_digest_sha256 != plan_fragment_digest(plan):
        blockers.append("dispatch preparation plan digest does not match plan")
    if safety_profile is None:
        blockers.append("dispatch preparation requires a safety profile")
    elif safety_profile.safety_profile_sha256 != safety_profile_sha256:
        blockers.append("dispatch preparation safety profile does not match approval")
    elif integrity_blockers := safety_profile_integrity_blockers(safety_profile):
        blockers.extend(
            f"dispatch preparation safety profile: {blocker}"
            for blocker in integrity_blockers
        )
    if not session.loaded_labware_id:
        blockers.append("dispatch preparation requires loaded labware ID")
    if not session.definition_uri:
        blockers.append("dispatch preparation requires loaded labware definition URI")
    return blockers


def _readback_summary(
    *,
    session: BridgeSession,
    run_id: str,
    command_key: str,
    safety_profile: FixtureSafetyProfile | None,
    run_result: EndpointResult,
    command_history_result: EndpointResult,
) -> tuple[MotionDispatchReadbackSummary | None, list[str]]:
    blockers: list[str] = []
    run_data = _run_endpoint_data(run_result, blockers)
    history_data = _collection_endpoint_data(command_history_result, blockers)
    if _maintenance_run_path_run_id(run_result.path) != run_id:
        blockers.append("live maintenance run path does not match session")
    if _history_path_run_id(command_history_result.path) != run_id:
        blockers.append("live command history path does not match maintenance run")
    if run_data is None or history_data is None:
        return None, _dedupe(blockers)

    run_id_value = _string_or_none(run_data.get("id"))
    run_status = _string_or_none(run_data.get("status")) or ""
    run_current = run_data.get("current")
    if run_id_value != run_id:
        blockers.append("live maintenance run ID does not match session")
    if run_current is not True:
        blockers.append("live maintenance run is not current")
    if run_status != "idle":
        blockers.append(f"live maintenance run status is not idle: {run_status or 'missing'}")
    errors = run_data.get("errors")
    if not isinstance(errors, list):
        blockers.append("live maintenance run errors field is malformed")
    elif errors:
        blockers.append("live maintenance run contains errors")

    labware, labware_blockers = _loaded_labware(run_data, session)
    blockers.extend(labware_blockers)
    offset_vector, offset_blockers = _labware_offset_vector(
        run_data,
        labware,
        safety_profile=safety_profile,
    )
    blockers.extend(offset_blockers)
    commands, history_blockers = _command_history(history_data)
    blockers.extend(history_blockers)
    if any(_string_or_none(command.get("key")) == command_key for command in commands):
        blockers.append("live command history already contains dispatch command key")
    last_command = commands[-1] if commands else None
    if session.last_command_id and last_command is None:
        blockers.append("live command history is empty")
    elif session.last_command_id and _string_or_none(last_command.get("id")) != (
        session.last_command_id
    ):
        blockers.append("live command history last command does not match session")
    elif last_command is not None:
        if _string_or_none(last_command.get("key")) != session.last_command_key:
            blockers.append("live last command key does not match session")
        if _string_or_none(last_command.get("status")) != session.last_command_status:
            blockers.append("live last command status does not match session")
        expected_type = session.last_command_type or "loadLabware"
        if _string_or_none(last_command.get("commandType")) != expected_type:
            blockers.append("live last command type does not match session")

    blockers = _dedupe(blockers)
    if blockers or labware is None or offset_vector is None:
        return None, blockers
    return (
        MotionDispatchReadbackSummary(
            run_status=run_status,
            run_current=True,
            loaded_labware_id=session.loaded_labware_id or "",
            loaded_labware_definition_uri=session.definition_uri or "",
            loaded_labware_slot=session.slot,
            loaded_labware_offset_id=_string_or_none(labware.get("offsetId")),
            labware_offset_vector_mm=offset_vector,
            command_history_total_length=_history_total_length(history_data),
            last_observed_command_id=_string_or_none(last_command.get("id"))
            if last_command is not None
            else None,
            last_observed_command_key=_string_or_none(last_command.get("key"))
            if last_command is not None
            else None,
            last_observed_command_type=_string_or_none(last_command.get("commandType"))
            if last_command is not None
            else None,
            last_observed_command_status=_string_or_none(last_command.get("status"))
            if last_command is not None
            else None,
        ),
        [],
    )


def _run_endpoint_data(
    result: EndpointResult,
    blockers: list[str],
) -> dict[str, Any] | None:
    if not result.ok:
        blockers.append("live maintenance run readback failed")
        return None
    if not isinstance(result.data, dict):
        blockers.append("live maintenance run readback payload is malformed")
        return None
    data = result.data.get("data")
    if not isinstance(data, dict):
        blockers.append("live maintenance run readback data is malformed")
        return None
    return data


def _collection_endpoint_data(
    result: EndpointResult,
    blockers: list[str],
) -> dict[str, Any] | None:
    if not result.ok:
        blockers.append("live command history readback failed")
        return None
    if not isinstance(result.data, dict):
        blockers.append("live command history readback payload is malformed")
        return None
    return result.data


def _loaded_labware(
    run_data: dict[str, Any],
    session: BridgeSession,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    labware_items = run_data.get("labware")
    if not isinstance(labware_items, list):
        return None, ["live maintenance run labware field is malformed"]
    matches = [
        item
        for item in labware_items
        if isinstance(item, dict) and item.get("id") == session.loaded_labware_id
    ]
    if len(matches) != 1:
        return None, ["live maintenance run does not contain exactly one loaded fixture"]
    labware = matches[0]
    if _string_or_none(labware.get("definitionUri")) != session.definition_uri:
        blockers.append("live loaded fixture definition URI does not match session")
    location = labware.get("location")
    if not isinstance(location, dict):
        blockers.append("live loaded fixture location is malformed")
    elif _string_or_none(location.get("slotName")) != session.slot:
        blockers.append("live loaded fixture slot does not match session")
    return labware, blockers


def _labware_offset_vector(
    run_data: dict[str, Any],
    labware: dict[str, Any] | None,
    *,
    safety_profile: FixtureSafetyProfile | None,
) -> tuple[dict[Literal["x", "y", "z"], float] | None, list[str]]:
    if labware is None:
        return None, []
    blockers: list[str] = []
    offset_id = _string_or_none(labware.get("offsetId"))
    if offset_id is None:
        return {"x": 0.0, "y": 0.0, "z": 0.0}, []
    offsets = run_data.get("labwareOffsets")
    if not isinstance(offsets, list):
        return None, ["live maintenance run labware offsets field is malformed"]
    matches = [
        offset
        for offset in offsets
        if isinstance(offset, dict) and offset.get("id") == offset_id
    ]
    if len(matches) != 1:
        return None, ["live loaded fixture offset is not present in run offsets"]
    offset = matches[0]
    if offset.get("definitionUri") != labware.get("definitionUri"):
        blockers.append("live loaded fixture offset definition URI does not match labware")
    offset_location = offset.get("location")
    labware_location = labware.get("location")
    if not isinstance(offset_location, dict):
        blockers.append("live loaded fixture offset location is malformed")
    elif not isinstance(labware_location, dict):
        blockers.append("live loaded fixture labware location is malformed")
    elif offset_location.get("slotName") != labware_location.get("slotName"):
        blockers.append("live loaded fixture offset slot does not match labware")
    vector = offset.get("vector")
    if not isinstance(vector, dict):
        return None, [*blockers, "live loaded fixture offset vector is malformed"]
    parsed = _vector(vector)
    if parsed is None:
        return None, [*blockers, "live loaded fixture offset vector is incomplete"]
    if safety_profile is not None:
        max_jog = safety_profile.max_registration_jog_mm
        if not math.isfinite(max_jog) or max_jog <= 0:
            blockers.append("safety-profile jog bound is not finite positive")
        elif any(abs(value) > max_jog for value in parsed.values()):
            blockers.append("live loaded fixture offset exceeds safety-profile jog bound")
    if blockers:
        return None, blockers
    return parsed, []


def _command_history(
    history_data: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    data = history_data.get("data")
    if not isinstance(data, list):
        return [], ["live command history data is malformed"]
    commands: list[dict[str, Any]] = []
    for command in data:
        if not isinstance(command, dict):
            return [], ["live command history contains malformed command"]
        commands.append(command)
    meta = history_data.get("meta")
    if not isinstance(meta, dict):
        blockers.append("live command history metadata is malformed")
    else:
        total_length = meta.get("totalLength")
        if isinstance(total_length, bool) or not isinstance(total_length, int):
            blockers.append("live command history total length is malformed")
        elif total_length > len(commands):
            blockers.append("live command history page is incomplete")
    return commands, blockers


def _history_total_length(history_data: dict[str, Any]) -> int:
    meta = history_data.get("meta")
    if not isinstance(meta, dict):
        return 0
    total_length = meta.get("totalLength")
    if isinstance(total_length, bool) or not isinstance(total_length, int):
        return 0
    return total_length


def _command_body_for_operation(
    *,
    operation: PlanOperation,
    reservation_id: str,
    session: BridgeSession,
    step: PlanStep | None,
    safety_profile: FixtureSafetyProfile | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    if operation == "home":
        return (
            {
                "data": {
                    "commandType": "home",
                    "key": _command_key(reservation_id),
                    "params": {},
                }
            },
            [],
        )
    if operation == "move_high_z":
        return _move_high_z_command_body(
            reservation_id=reservation_id,
            session=session,
            step=step,
            safety_profile=safety_profile,
        )
    if operation == "move_low_z":
        return _move_low_z_command_body(
            reservation_id=reservation_id,
            session=session,
            step=step,
            safety_profile=safety_profile,
        )
    return None, [f"motion dispatch preparation is not implemented for {operation}"]


def _move_high_z_command_body(
    *,
    reservation_id: str,
    session: BridgeSession,
    step: PlanStep | None,
    safety_profile: FixtureSafetyProfile | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    target_class = getattr(step, "target_class", None)
    if target_class != FIRST_HIGH_Z_TARGET_CLASS:
        blockers.append(
            "motion dispatch preparation is only implemented for "
            f"{FIRST_HIGH_Z_TARGET_CLASS}"
        )
    if safety_profile is None:
        blockers.append("move_high_z requires a safety profile")
    elif (
        not math.isfinite(safety_profile.conservative_high_z_mm)
        or safety_profile.conservative_high_z_mm <= 0
    ):
        blockers.append("move_high_z safety-profile high-Z is not finite positive")
    if not session.loaded_labware_id:
        blockers.append("move_high_z requires loaded labware ID")
    if not session.pipette_id:
        blockers.append("move_high_z requires session pipette ID")
    if blockers:
        return None, blockers

    assert safety_profile is not None
    return (
        {
            "data": {
                "commandType": "moveToWell",
                "key": _command_key(reservation_id),
                "params": {
                    "pipetteId": session.pipette_id,
                    "labwareId": session.loaded_labware_id,
                    "wellName": FIRST_HIGH_Z_WELL_NAME,
                    "wellLocation": {
                        "origin": "top",
                        "offset": {
                            "x": 0.0,
                            "y": 0.0,
                            "z": FIRST_HIGH_Z_TOP_OFFSET_MM,
                        },
                    },
                    "minimumZHeight": safety_profile.conservative_high_z_mm,
                    "forceDirect": False,
                    "speed": FIRST_HIGH_Z_SPEED_MM_PER_S,
                },
            }
        },
        [],
    )


def _move_low_z_command_body(
    *,
    reservation_id: str,
    session: BridgeSession,
    step: PlanStep | None,
    safety_profile: FixtureSafetyProfile | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Translate an approved first low-Z dry step into a moveToWell command (OT-4).

    The low-Z move is the DESCENT direction, where risk is asymmetric: a wrong high-Z
    constant is harmless (up/away) but a too-deep descent crashes the tip into the fixture.
    Two facts make a safe descent un-emittable today, so this fails CLOSED:

    * ``minimumZHeight`` does NOT bound the descent. Per the Opentrons MoveToWellParams
      schema it only raises the lateral-transit arc apex (no effect below the API default
      safe-Z margin); the final depth is set entirely by the resolved well target.
    * The safety model has no per-well descent FLOOR. ``dry_z_floor_mm`` is the conservative
      collision-envelope top (a transit clearance) -- the canonical fixture's A1 well-top is
      ~11 mm below it -- so there is nothing to verify a descent endpoint against.

    Therefore descent emission is gated behind ``LOW_Z_DRY_DESCENT_ENDPOINT_GROUNDED`` until a
    validated per-well dry-descent endpoint exists (mirrors OT-1's empty calibrated-source
    gate). The translator still validates everything it can (target class, session identity,
    a finite-positive high-Z park for the eventual transit clearance) and creates no motion
    authority -- it only assembles a command from already-approved inputs. The unreachable
    emission tail uses ``conservative_high_z_mm`` as the transit-arc clearance (mirroring the
    high-Z translator), NOT a descent bound.
    """
    blockers: list[str] = []
    target_class = getattr(step, "target_class", None)
    if target_class != FIRST_LOW_Z_DRY_TARGET_CLASS:
        blockers.append(
            "motion dispatch preparation is only implemented for "
            f"{FIRST_LOW_Z_DRY_TARGET_CLASS}"
        )
    if safety_profile is None:
        blockers.append("move_low_z requires a safety profile")
    elif (
        not math.isfinite(safety_profile.conservative_high_z_mm)
        or safety_profile.conservative_high_z_mm <= 0
    ):
        blockers.append("move_low_z safety-profile high-Z is not finite positive")
    if not session.loaded_labware_id:
        blockers.append("move_low_z requires loaded labware ID")
    if not session.pipette_id:
        blockers.append("move_low_z requires session pipette ID")
    if not LOW_Z_DRY_DESCENT_ENDPOINT_GROUNDED:
        blockers.append("low_z_dry_descent_endpoint_not_grounded")
    if blockers:
        return None, blockers

    assert safety_profile is not None
    return (
        {
            "data": {
                "commandType": "moveToWell",
                "key": _command_key(reservation_id),
                "params": {
                    "pipetteId": session.pipette_id,
                    "labwareId": session.loaded_labware_id,
                    "wellName": FIRST_LOW_Z_DRY_WELL_NAME,
                    "wellLocation": {
                        "origin": "top",
                        "offset": {
                            "x": 0.0,
                            "y": 0.0,
                            "z": FIRST_LOW_Z_DRY_TOP_OFFSET_MM,
                        },
                    },
                    # Transit-arc clearance ONLY (raises the lateral arc apex); it does NOT
                    # clamp the descent -- that is bounded by the (grounded) well target.
                    "minimumZHeight": safety_profile.conservative_high_z_mm,
                    "forceDirect": False,
                    "speed": FIRST_LOW_Z_DRY_SPEED_MM_PER_S,
                },
            }
        },
        [],
    )


def _command_path(run_id: str) -> str:
    return f"/maintenance_runs/{run_id}/commands?waitUntilComplete=true&timeout=60000"


def _history_path(run_id: str) -> str:
    return f"/maintenance_runs/{run_id}/commands?pageLength=1000"


def _history_path_run_id(path: str) -> str | None:
    route = path.split("?", 1)[0].strip("/")
    parts = route.split("/")
    if len(parts) == 3 and parts[0] == "maintenance_runs" and parts[2] == "commands":
        return parts[1]
    return None


def _maintenance_run_path_run_id(path: str) -> str | None:
    route = path.split("?", 1)[0].strip("/")
    parts = route.split("/")
    if len(parts) == 2 and parts[0] == "maintenance_runs":
        return parts[1]
    return None


def _journal_id(reservation_id: str) -> str:
    return f"{reservation_id}:command"


def _preparation_id(reservation_id: str) -> str:
    digest = hashlib.sha256(reservation_id.encode("utf-8")).hexdigest()
    return f"motion_dispatch_preparation:{digest[:24]}"


def _command_key(reservation_id: str) -> str:
    digest = hashlib.sha256(reservation_id.encode("utf-8")).hexdigest()
    return f"aevum-motion-{digest[:24]}"


def _vector(value: dict[str, Any]) -> dict[Literal["x", "y", "z"], float] | None:
    parsed: dict[Literal["x", "y", "z"], float] = {"x": 0.0, "y": 0.0, "z": 0.0}
    for axis in ("x", "y", "z"):
        component = value.get(axis)
        if isinstance(component, bool) or not isinstance(component, int | float):
            return None
        if not math.isfinite(float(component)):
            return None
        parsed[axis] = float(component)
    return parsed


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
