from __future__ import annotations

import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import ip_address
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qs, urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from aevum_ot2.core.models import EvidenceClaim, OffsetRegistry
from aevum_ot2.core.motion_approval import MOTION_APPROVAL_MAX_TTL, MotionApproval
from aevum_ot2.core.plans import parse_plan_fragment
from aevum_ot2.core.pose import FixturePose
from aevum_ot2.core.safety import FixtureSafetyProfile
from aevum_ot2.core.sessions import DEFAULT_SESSION_DB
from aevum_ot2.server.service import BridgeService, BridgeServiceError

MAX_REQUEST_BODY_BYTES = 1_000_000
MAX_JSON_NESTING_DEPTH = 100
REQUEST_READ_TIMEOUT_SECONDS = 10.0
MAX_RECORD_PATHS = 100
MOTION_BACKEND_TOKEN_HEADER = "X-Aevum-Bridge-Token"


class StartNoMotionSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    robot_url: str
    owner_id: str
    kind: str = "registration"
    slot: str = "1"
    orientation: Literal["canonical", "rot180"] = "canonical"
    pipette_mount: str = "left"
    labware_path: str | None = None
    lease_minutes: int = 15
    timeout_seconds: float = 10.0

    @field_validator("robot_url", "owner_id", "kind", "slot", "pipette_mount")
    @classmethod
    def _validate_nonempty_string(cls, value: str) -> str:
        if not value:
            raise ValueError("field must be a non-empty string")
        return value

    @field_validator("labware_path")
    @classmethod
    def _validate_optional_nonempty_string(cls, value: str | None) -> str | None:
        if value == "":
            raise ValueError("labware_path must be non-empty when provided")
        return value


class PlanRouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: dict[str, Any]
    fixture_qc_record: str | None = None
    target_class_records: list[str] = Field(default_factory=list)
    offset_registry: dict[str, Any] | None = None
    safety_profile: dict[str, Any] | None = None
    fixture_pose: dict[str, Any] | None = None
    pose_claims: list[dict[str, Any]] = Field(default_factory=list)
    recovery_disposition: str | None = None
    motion_approval: dict[str, Any] | None = None

    @field_validator("fixture_qc_record", mode="before")
    @classmethod
    def _validate_fixture_qc_record(cls, value: object) -> str | None:
        if value is None:
            return None
        return _safe_record_path(value)

    @field_validator("target_class_records", mode="before")
    @classmethod
    def _validate_target_class_records(cls, value: object) -> object:
        if value is None:
            return []
        if not isinstance(value, list):
            return value
        if len(value) > MAX_RECORD_PATHS:
            raise ValueError(f"too many record paths; max {MAX_RECORD_PATHS}")
        return [_safe_record_path(item) for item in value]

    @field_validator("pose_claims")
    @classmethod
    def _reject_raw_pose_claims(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if value:
            raise ValueError(
                "raw pose_claims are not accepted; commit pose evidence to the "
                "session evidence store"
            )
        return value


class ArmMotionApprovalRequest(PlanRouteRequest):
    approved_by: str
    expires_in_seconds: int = 300

    @field_validator("approved_by")
    @classmethod
    def _validate_approved_by(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("approved_by must be a non-empty string")
        return value

    @field_validator("expires_in_seconds")
    @classmethod
    def _validate_expires_in_seconds(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("expires_in_seconds must be positive")
        max_seconds = int(MOTION_APPROVAL_MAX_TTL.total_seconds())
        if value > max_seconds:
            raise ValueError(f"expires_in_seconds must be <= {max_seconds}")
        return value

    @model_validator(mode="after")
    def _reject_supplied_approval(self) -> ArmMotionApprovalRequest:
        if self.motion_approval is not None:
            raise ValueError("motion_approval is minted by the arm route")
        return self


def create_handler(
    service: BridgeService,
    *,
    motion_backend_token: str | None = None,
) -> type[BaseHTTPRequestHandler]:
    class BridgeRequestHandler(BaseHTTPRequestHandler):
        server_version = "AevumOT2Bridge/0.1"

        def setup(self) -> None:
            super().setup()
            self.connection.settimeout(REQUEST_READ_TIMEOUT_SECONDS)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            query = parse_qs(parsed.query)
            try:
                if path == "/health":
                    self._write_model(service.health())
                    return
                if path == "/sessions":
                    self._write_json(
                        [
                            session.model_dump(mode="json")
                            for session in service.list_sessions(
                                robot_url=_first(query, "robot_url"),
                                state=_first(query, "state"),
                            )
                        ]
                    )
                    return
                session_id = _session_id_for_route(path, "/context")
                if session_id is not None:
                    self._write_model(
                        service.get_session_context(
                            session_id,
                            fixture_qc_record=_safe_optional_record_path(
                                _first(query, "fixture_qc_record")
                            ),
                            target_class_records=_safe_record_paths(
                                _many(query, "target_class_record")
                            ),
                        )
                    )
                    return
            except BridgeServiceError as exc:
                self._write_error(exc.status_code, exc.code, exc.message)
                return
            except sqlite3.OperationalError as exc:
                self._write_error(503, "state_db_busy", str(exc))
                return
            except (ValueError, ValidationError, TypeError) as exc:
                self._write_error(400, "bad_request", str(exc))
                return

            self._write_error(404, "not_found", f"unknown endpoint: {path}")

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            try:
                body = self._read_json()
                if path == "/sessions/start-nomotion":
                    request = StartNoMotionSessionRequest.model_validate(body)
                    self._write_model(
                        service.start_no_motion_session(
                            request.robot_url,
                            owner_id=request.owner_id,
                            kind=request.kind,
                            slot=request.slot,
                            orientation=request.orientation,
                            pipette_mount=request.pipette_mount,
                            labware_path=request.labware_path,
                            lease_minutes=request.lease_minutes,
                            timeout_seconds=request.timeout_seconds,
                        )
                    )
                    return
                session_id = _session_id_for_route(path, "/validate-plan")
                if session_id is not None:
                    request = PlanRouteRequest.model_validate(body)
                    self._write_model(
                        service.validate_plan(
                            session_id,
                            parse_plan_fragment(request.plan),
                            fixture_qc_record=request.fixture_qc_record,
                            target_class_records=request.target_class_records,
                            offset_registry=_offset_registry(request),
                            safety_profile=_safety_profile(request),
                            fixture_pose=_fixture_pose(request),
                            pose_claims=_pose_claims(request),
                            recovery_disposition=request.recovery_disposition,
                            motion_approval=_motion_approval(request),
                        )
                    )
                    return
                session_id = _session_id_for_route(path, "/motion-approval/arm")
                if session_id is not None:
                    if not self._authorize_motion_backend():
                        return
                    request = ArmMotionApprovalRequest.model_validate(body)
                    self._write_model(
                        service.arm_motion_approval(
                            session_id,
                            parse_plan_fragment(request.plan),
                            approved_by=request.approved_by,
                            fixture_qc_record=request.fixture_qc_record,
                            target_class_records=request.target_class_records,
                            offset_registry=_offset_registry(request),
                            safety_profile=_safety_profile(request),
                            fixture_pose=_fixture_pose(request),
                            pose_claims=_pose_claims(request),
                            recovery_disposition=request.recovery_disposition,
                            expires_in_seconds=request.expires_in_seconds,
                        )
                    )
                    return
                session_id = _session_id_for_route(path, "/execute-next")
                if session_id is not None:
                    if not self._authorize_motion_backend():
                        return
                    request = PlanRouteRequest.model_validate(body)
                    self._write_model(
                        service.execute_next(
                            session_id,
                            parse_plan_fragment(request.plan),
                            fixture_qc_record=request.fixture_qc_record,
                            target_class_records=request.target_class_records,
                            offset_registry=_offset_registry(request),
                            safety_profile=_safety_profile(request),
                            fixture_pose=_fixture_pose(request),
                            pose_claims=_pose_claims(request),
                            recovery_disposition=request.recovery_disposition,
                            motion_approval=_motion_approval(request),
                        )
                    )
                    return
                session_id = _session_id_for_route(path, "/close-nomotion")
                if session_id is not None:
                    self._write_model(
                        service.close_no_motion_session(
                            session_id,
                            timeout_seconds=float(body.get("timeout_seconds", 10.0)),
                        )
                    )
                    return
                session_id = _session_id_for_route(path, "/recover-nomotion")
                if session_id is not None:
                    self._write_model(
                        service.recover_no_motion_session(
                            session_id,
                            timeout_seconds=float(body.get("timeout_seconds", 10.0)),
                        )
                    )
                    return
            except BridgeServiceError as exc:
                self._write_error(exc.status_code, exc.code, exc.message)
                return
            except sqlite3.OperationalError as exc:
                self._write_error(503, "state_db_busy", str(exc))
                return
            except (ValueError, ValidationError, TypeError) as exc:
                self._write_error(400, "bad_request", str(exc))
                return

            self._write_error(404, "not_found", f"unknown endpoint: {path}")

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            if self.headers.get("Transfer-Encoding"):
                raise ValueError("Transfer-Encoding is not supported")
            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc
            if length < 0:
                raise ValueError("invalid Content-Length")
            if length > MAX_REQUEST_BODY_BYTES:
                raise ValueError(
                    f"request body too large; max {MAX_REQUEST_BODY_BYTES} bytes"
                )
            if length == 0:
                return {}
            content_type = self.headers.get("Content-Type", "")
            if "application/json" not in content_type.lower():
                raise ValueError("Content-Type must be application/json")
            raw = self.rfile.read(length).decode("utf-8")
            _reject_excessive_json_depth(raw)
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("expected JSON object body")
            return data

        def _authorize_motion_backend(self) -> bool:
            if not getattr(service, "motion_backend_enabled", False):
                return True
            if self.headers.get(MOTION_BACKEND_TOKEN_HEADER) == motion_backend_token:
                return True
            self._write_error(
                403,
                "motion_backend_auth_required",
                f"missing or invalid {MOTION_BACKEND_TOKEN_HEADER}",
            )
            return False

        def _write_model(self, model: BaseModel, status_code: int = 200) -> None:
            self._write_json(model.model_dump(mode="json"), status_code=status_code)

        def _write_json(self, data: object, status_code: int = 200) -> None:
            encoded = (json.dumps(data, indent=2) + "\n").encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _write_error(self, status_code: int, code: str, message: str) -> None:
            self._write_json(
                {"error": {"code": code, "message": message}},
                status_code=status_code,
            )

    return BridgeRequestHandler


def create_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    state_db_path: str | Path | None = None,
    motion_enabled: bool = False,
    motion_backend_enabled: bool = False,
    motion_backend_token: str | None = None,
    allow_remote: bool = False,
) -> ThreadingHTTPServer:
    _validate_bind_host(host, allow_remote=allow_remote)
    if motion_backend_enabled and allow_remote:
        raise ValueError("motion backend cannot be enabled on a remote unauthenticated bind")
    if motion_backend_enabled and not motion_backend_token:
        raise ValueError("motion backend requires a local auth token")
    service = BridgeService(
        state_db_path=state_db_path or DEFAULT_SESSION_DB,
        motion_enabled=motion_enabled,
        motion_backend_enabled=motion_backend_enabled,
    )
    return ThreadingHTTPServer(
        (host, port),
        create_handler(service, motion_backend_token=motion_backend_token),
    )


def serve(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    state_db_path: str | Path | None = None,
    motion_enabled: bool = False,
    motion_backend_enabled: bool = False,
    motion_backend_token: str | None = None,
    allow_remote: bool = False,
) -> None:
    server = create_server(
        host=host,
        port=port,
        state_db_path=state_db_path,
        motion_enabled=motion_enabled,
        motion_backend_enabled=motion_backend_enabled,
        motion_backend_token=motion_backend_token,
        allow_remote=allow_remote,
    )
    server.serve_forever()


def _session_id_for_route(path: str, suffix: str) -> str | None:
    prefix = "/sessions/"
    if not path.startswith(prefix) or not path.endswith(suffix):
        return None
    session_id = path[len(prefix) : len(path) - len(suffix)]
    if not session_id or "/" in session_id:
        raise ValueError("session_id must be a single non-empty path segment")
    return session_id


def _first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    return values[0]


def _many(query: dict[str, list[str]], key: str) -> list[str]:
    return query.get(key, [])


def _safe_record_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("record path must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or "\\" in value:
        raise ValueError("record path must be relative")
    parts = path.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("record path must not contain traversal segments")
    return value


def _safe_optional_record_path(value: str | None) -> str | None:
    if value is None:
        return None
    return _safe_record_path(value)


def _safe_record_paths(values: list[str]) -> list[str]:
    if len(values) > MAX_RECORD_PATHS:
        raise ValueError(f"too many record paths; max {MAX_RECORD_PATHS}")
    return [_safe_record_path(value) for value in values]


def _offset_registry(request: PlanRouteRequest) -> OffsetRegistry | None:
    if request.offset_registry is None:
        return None
    return OffsetRegistry.model_validate(request.offset_registry)


def _safety_profile(request: PlanRouteRequest) -> FixtureSafetyProfile | None:
    if request.safety_profile is None:
        return None
    return FixtureSafetyProfile.model_validate(request.safety_profile)


def _fixture_pose(request: PlanRouteRequest) -> FixturePose | None:
    if request.fixture_pose is None:
        return None
    return FixturePose.model_validate(request.fixture_pose)


def _pose_claims(request: PlanRouteRequest) -> list[EvidenceClaim]:
    return [EvidenceClaim.model_validate(item) for item in request.pose_claims]


def _motion_approval(request: PlanRouteRequest) -> MotionApproval | None:
    if request.motion_approval is None:
        return None
    return MotionApproval.model_validate(request.motion_approval)


def _validate_bind_host(host: str, *, allow_remote: bool) -> None:
    if allow_remote or _is_loopback_bind_host(host):
        return
    raise ValueError(
        f"refusing unauthenticated daemon bind on non-loopback host {host!r}; "
        "pass allow_remote=True only behind an explicit network control"
    )


def _is_loopback_bind_host(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def _reject_excessive_json_depth(raw: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for char in raw:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            if depth > MAX_JSON_NESTING_DEPTH:
                raise ValueError(
                    f"JSON nesting too deep; max {MAX_JSON_NESTING_DEPTH}"
                )
        elif char in "]}":
            depth = max(depth - 1, 0)
