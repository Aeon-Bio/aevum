from __future__ import annotations

import json
from typing import Any, TypeVar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from pydantic import BaseModel

from aevum_ot2.core.context import SessionContext
from aevum_ot2.core.execution import PlanExecutionResult
from aevum_ot2.core.models import (
    BridgeSession,
    EvidenceClaim,
    NoMotionSessionCloseReport,
    NoMotionSessionInitReport,
    OffsetRegistry,
)
from aevum_ot2.core.motion_approval import MotionApproval
from aevum_ot2.core.motion_commissioning import MotionApprovalArmResult
from aevum_ot2.core.plans import PlanFragment
from aevum_ot2.core.pose import FixturePose
from aevum_ot2.core.recovery import NoMotionRecoveryReport
from aevum_ot2.core.safety import FixtureSafetyProfile
from aevum_ot2.core.validation import PlanValidationResult
from aevum_ot2.server.service import BridgeServiceHealth

T = TypeVar("T", bound=BaseModel)


class DaemonClientError(Exception):
    def __init__(self, status_code: int | None, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class DaemonClient:
    """Thin HTTP client for the local Aevum OT-2 daemon."""

    def __init__(self, base_url: str = "http://127.0.0.1:8765", *, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout

    def health(self) -> BridgeServiceHealth:
        return self._get_model("health", BridgeServiceHealth)

    def list_sessions(
        self,
        *,
        robot_url: str | None = None,
        state: str | None = None,
    ) -> list[BridgeSession]:
        query = _query({"robot_url": robot_url, "state": state})
        payload = self._request("GET", "sessions" + query)
        if not isinstance(payload, list):
            raise DaemonClientError(None, "bad_response", "expected session list")
        return [BridgeSession.model_validate(item) for item in payload]

    def get_session_context(
        self,
        session_id: str,
        *,
        fixture_qc_record: str | None = None,
        target_class_records: list[str] | None = None,
    ) -> SessionContext:
        query = _query(
            {
                "fixture_qc_record": fixture_qc_record,
                "target_class_record": target_class_records or [],
            }
        )
        return self._get_model(f"sessions/{session_id}/context{query}", SessionContext)

    def validate_plan(
        self,
        session_id: str,
        plan: PlanFragment,
        *,
        fixture_qc_record: str | None = None,
        target_class_records: list[str] | None = None,
        offset_registry: OffsetRegistry | None = None,
        safety_profile: FixtureSafetyProfile | None = None,
        fixture_pose: FixturePose | None = None,
        pose_claims: list[EvidenceClaim] | None = None,
        recovery_disposition: str | None = None,
        motion_approval: MotionApproval | None = None,
    ) -> PlanValidationResult:
        return self._post_model(
            f"sessions/{session_id}/validate-plan",
            _plan_body(
                plan,
                fixture_qc_record,
                target_class_records,
                offset_registry,
                safety_profile,
                fixture_pose,
                pose_claims,
                recovery_disposition,
                motion_approval,
            ),
            PlanValidationResult,
        )

    def execute_next(
        self,
        session_id: str,
        plan: PlanFragment,
        *,
        fixture_qc_record: str | None = None,
        target_class_records: list[str] | None = None,
        offset_registry: OffsetRegistry | None = None,
        safety_profile: FixtureSafetyProfile | None = None,
        fixture_pose: FixturePose | None = None,
        pose_claims: list[EvidenceClaim] | None = None,
        recovery_disposition: str | None = None,
        motion_approval: MotionApproval | None = None,
    ) -> PlanExecutionResult:
        return self._post_model(
            f"sessions/{session_id}/execute-next",
            _plan_body(
                plan,
                fixture_qc_record,
                target_class_records,
                offset_registry,
                safety_profile,
                fixture_pose,
                pose_claims,
                recovery_disposition,
                motion_approval,
            ),
            PlanExecutionResult,
        )

    def arm_motion_approval(
        self,
        session_id: str,
        plan: PlanFragment,
        *,
        approved_by: str,
        fixture_qc_record: str | None = None,
        target_class_records: list[str] | None = None,
        offset_registry: OffsetRegistry | None = None,
        safety_profile: FixtureSafetyProfile | None = None,
        fixture_pose: FixturePose | None = None,
        pose_claims: list[EvidenceClaim] | None = None,
        recovery_disposition: str | None = None,
        expires_in_seconds: int = 300,
    ) -> MotionApprovalArmResult:
        body = _plan_body(
            plan,
            fixture_qc_record,
            target_class_records,
            offset_registry,
            safety_profile,
            fixture_pose,
            pose_claims,
            recovery_disposition,
            None,
        )
        body["approved_by"] = approved_by
        body["expires_in_seconds"] = expires_in_seconds
        return self._post_model(
            f"sessions/{session_id}/motion-approval/arm",
            body,
            MotionApprovalArmResult,
        )

    def start_no_motion_session(
        self,
        robot_url: str,
        *,
        owner_id: str,
        kind: str = "registration",
        slot: str = "1",
        orientation: str = "canonical",
        pipette_mount: str = "left",
        labware_path: str | None = None,
        lease_minutes: int = 15,
        timeout_seconds: float = 10.0,
    ) -> NoMotionSessionInitReport:
        body: dict[str, Any] = {
            "robot_url": robot_url,
            "owner_id": owner_id,
            "kind": kind,
            "slot": slot,
            "orientation": orientation,
            "pipette_mount": pipette_mount,
            "lease_minutes": lease_minutes,
            "timeout_seconds": timeout_seconds,
        }
        if labware_path is not None:
            body["labware_path"] = labware_path
        return self._post_model(
            "sessions/start-nomotion",
            body,
            NoMotionSessionInitReport,
        )

    def close_no_motion_session(
        self,
        session_id: str,
        *,
        timeout_seconds: float = 10.0,
    ) -> NoMotionSessionCloseReport:
        return self._post_model(
            f"sessions/{session_id}/close-nomotion",
            {"timeout_seconds": timeout_seconds},
            NoMotionSessionCloseReport,
        )

    def recover_no_motion_session(
        self,
        session_id: str,
        *,
        timeout_seconds: float = 10.0,
    ) -> NoMotionRecoveryReport:
        return self._post_model(
            f"sessions/{session_id}/recover-nomotion",
            {"timeout_seconds": timeout_seconds},
            NoMotionRecoveryReport,
        )

    def _get_model(self, path: str, model_type: type[T]) -> T:
        return model_type.model_validate(self._request("GET", path))

    def _post_model(
        self,
        path: str,
        body: dict[str, Any],
        model_type: type[T],
    ) -> T:
        return model_type.model_validate(self._request("POST", path, body))

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> object:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            urljoin(self.base_url, path),
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise _client_error_from_http(exc) from exc
        except (TimeoutError, URLError, OSError) as exc:
            raise DaemonClientError(None, "daemon_unreachable", str(exc)) from exc


def _plan_body(
    plan: PlanFragment,
    fixture_qc_record: str | None,
    target_class_records: list[str] | None,
    offset_registry: OffsetRegistry | None,
    safety_profile: FixtureSafetyProfile | None,
    fixture_pose: FixturePose | None,
    pose_claims: list[EvidenceClaim] | None,
    recovery_disposition: str | None,
    motion_approval: MotionApproval | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"plan": plan.model_dump(mode="json")}
    if fixture_qc_record is not None:
        body["fixture_qc_record"] = fixture_qc_record
    if target_class_records:
        body["target_class_records"] = target_class_records
    if offset_registry is not None:
        body["offset_registry"] = offset_registry.model_dump(mode="json")
    if safety_profile is not None:
        body["safety_profile"] = safety_profile.model_dump(mode="json")
    if fixture_pose is not None:
        body["fixture_pose"] = fixture_pose.model_dump(mode="json")
    if pose_claims:
        body["pose_claims"] = [claim.model_dump(mode="json") for claim in pose_claims]
    if recovery_disposition is not None:
        body["recovery_disposition"] = recovery_disposition
    if motion_approval is not None:
        body["motion_approval"] = motion_approval.model_dump(mode="json")
    return body


def _query(params: dict[str, str | list[str] | None]) -> str:
    pairs: list[tuple[str, str]] = []
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, list):
            pairs.extend((key, item) for item in value)
        else:
            pairs.append((key, value))
    return "" if not pairs else "?" + urlencode(pairs)


def _client_error_from_http(exc: HTTPError) -> DaemonClientError:
    try:
        payload = json.loads(exc.read().decode("utf-8"))
    except (json.JSONDecodeError, OSError):
        payload = {}
    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        code = str(error.get("code", "daemon_error"))
        message = str(error.get("message", exc.reason))
    else:
        code = "daemon_error"
        message = str(exc.reason)
    return DaemonClientError(exc.code, code, message)
