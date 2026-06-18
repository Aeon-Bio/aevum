"""Policy-enforcing MCP agent adapter for the Aevum OT-2 bridge.

This adapter exposes a deliberately narrow, allow-listed surface of validated
session-transition tools to autonomous agents. It mirrors ``adapters/cli.py``:
every stateful operation is routed through ``server.client.DaemonClient`` so
the daemon stays the single arbiter of session state and gates. The only
direct-core call permitted here is the read-only robot status fetch.

Hard safety properties (enforced fail-closed and covered by boundary tests):

* No agent tool mints or consumes motion approval. ``arm_motion_approval`` is
  intentionally NOT exposed -- approval is an operator action behind the
  motion-backend auth boundary, never an agent-callable tool.
* ``validate_plan`` / ``execute_next`` NEVER inject a ``motion_approval`` and
  NEVER default fixture orientation to ``canonical``. Orientation lives in the
  session; the adapter does not let an agent assert it.
* An adapter/translator MUST NOT create motion authority. This module never
  calls ``Ot2Client`` / ``core.client`` and never calls ``post_json`` /
  ``delete_json``. The single direct-core touch is ``fetch_robot_status``
  (read-only), exactly as the CLI does it.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aevum_ot2.core.client import fetch_robot_status
from aevum_ot2.core.discovery import DEFAULT_ROBOT_SERVICE_NAME, resolve_robot
from aevum_ot2.core.plans import PlanFragment, parse_plan_fragment
from aevum_ot2.server.client import DaemonClient

# The complete agent surface. Anything outside this set is unreachable: the
# registry refuses to bind it and the dispatcher refuses to route it.
ALLOWED_AGENT_TOOLS: frozenset[str] = frozenset(
    {
        "ot2_status",
        "ot2_start_session",
        "ot2_get_session_context",
        "ot2_validate_plan",
        "ot2_execute_next",
        "ot2_capture_evidence",
        "ot2_record_evidence",
        "ot2_evaluate_gates",
        "ot2_abort_or_recover",
        "ot2_close_session",
    }
)

# Names that must NEVER appear on the agent surface, even if a future refactor
# accidentally lists one. The registry and dispatcher reject these explicitly
# so a denied name can never collide back into the allow-list silently.
DENIED_AGENT_TOOLS: frozenset[str] = frozenset(
    {
        "set_offset",
        "move_to_coordinates",
        "post_command",
        "ot2_set_offset",
        "ot2_move_coordinates",
        "ot2_post_json",
        "ot2_raw_http",
    }
)


class AgentPolicyError(Exception):
    """Raised when a tool registration or dispatch violates the agent policy."""


# --------------------------------------------------------------------------- #
# Tool input models. Each crosses the agent boundary, so extra='forbid'.
# None of these accept a motion_approval or a fixture orientation: motion
# authority is not an agent-mintable field, and orientation is read from the
# session by the daemon.
# --------------------------------------------------------------------------- #


class _AgentToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Ot2StatusInput(_AgentToolInput):
    robot: str | None = None
    service_name: str = DEFAULT_ROBOT_SERVICE_NAME
    discovery_timeout: float = 5.0
    timeout: float = 5.0


class Ot2StartSessionInput(_AgentToolInput):
    robot_url: str
    owner_id: str
    kind: str = "registration"
    slot: str = "1"
    # Operator-proposed orientation for a brand-new session only. There is no
    # default applied by the adapter for already-established sessions: the
    # daemon validates and the session is the source of truth thereafter.
    orientation: str = "canonical"
    pipette_mount: str = "left"
    labware_path: str | None = None
    lease_minutes: int = 15
    timeout: float = 10.0


class Ot2GetSessionContextInput(_AgentToolInput):
    session_id: str
    fixture_qc_record: str | None = None
    target_class_records: list[str] = Field(default_factory=list)


class Ot2ValidatePlanInput(_AgentToolInput):
    session_id: str
    plan: dict[str, Any]
    fixture_qc_record: str | None = None
    target_class_records: list[str] = Field(default_factory=list)


class Ot2ExecuteNextInput(_AgentToolInput):
    session_id: str
    plan: dict[str, Any]
    fixture_qc_record: str | None = None
    target_class_records: list[str] = Field(default_factory=list)


class Ot2CaptureEvidenceInput(_AgentToolInput):
    session_id: str
    step_id: str = "capture-evidence"
    filename: str | None = None
    timeout_seconds: float | None = None


class Ot2RecordEvidenceInput(_AgentToolInput):
    session_id: str
    step_id: str = "record-evidence"
    evidence_id: str
    source_kind: str
    path: str
    checksum_sha256: str
    quality: str = "ambiguous"


class Ot2EvaluateGatesInput(_AgentToolInput):
    session_id: str
    fixture_qc_record: str | None = None
    target_class_records: list[str] = Field(default_factory=list)


class Ot2AbortOrRecoverInput(_AgentToolInput):
    session_id: str
    timeout: float = 10.0


class Ot2CloseSessionInput(_AgentToolInput):
    session_id: str
    timeout: float = 10.0


# --------------------------------------------------------------------------- #
# Tool implementations. Every stateful tool goes through DaemonClient; the only
# direct-core call is the read-only status fetch.
# --------------------------------------------------------------------------- #


def _daemon_client(daemon_url: str, *, timeout: float = 10.0) -> DaemonClient:
    return DaemonClient(daemon_url, timeout=timeout)


def _tool_ot2_status(args: Ot2StatusInput) -> dict[str, Any]:
    # Read-only direct-core call, mirroring cli.py `status`: resolve the robot
    # then fetch its health/pipette status. No daemon involved, no commands.
    discovery = resolve_robot(
        args.robot,
        service_name=args.service_name,
        timeout_seconds=args.discovery_timeout,
    )
    status = fetch_robot_status(discovery.robot_url, timeout_seconds=args.timeout)
    return {
        "discovery": discovery.model_dump(mode="json"),
        "status": status.model_dump(mode="json"),
    }


def _tool_ot2_start_session(client: DaemonClient, args: Ot2StartSessionInput) -> dict[str, Any]:
    report = client.start_no_motion_session(
        args.robot_url,
        owner_id=args.owner_id,
        kind=args.kind,
        slot=args.slot,
        orientation=args.orientation,
        pipette_mount=args.pipette_mount,
        labware_path=args.labware_path,
        lease_minutes=args.lease_minutes,
        timeout_seconds=args.timeout,
    )
    return report.model_dump(mode="json")


def _tool_ot2_get_session_context(
    client: DaemonClient,
    args: Ot2GetSessionContextInput,
) -> dict[str, Any]:
    context = client.get_session_context(
        args.session_id,
        fixture_qc_record=args.fixture_qc_record,
        target_class_records=args.target_class_records or None,
    )
    return context.model_dump(mode="json")


def _tool_ot2_validate_plan(client: DaemonClient, args: Ot2ValidatePlanInput) -> dict[str, Any]:
    plan = _parse_session_plan(args.session_id, args.plan)
    # NEVER pass motion_approval and NEVER assert orientation here: the daemon
    # reads orientation from the session and gates motion fail-closed.
    result = client.validate_plan(
        args.session_id,
        plan,
        fixture_qc_record=args.fixture_qc_record,
        target_class_records=args.target_class_records or None,
    )
    return result.model_dump(mode="json")


def _tool_ot2_execute_next(client: DaemonClient, args: Ot2ExecuteNextInput) -> dict[str, Any]:
    plan = _parse_session_plan(args.session_id, args.plan)
    # NEVER pass motion_approval: an agent cannot mint or carry motion authority.
    result = client.execute_next(
        args.session_id,
        plan,
        fixture_qc_record=args.fixture_qc_record,
        target_class_records=args.target_class_records or None,
    )
    return result.model_dump(mode="json")


def _tool_ot2_capture_evidence(
    client: DaemonClient,
    args: Ot2CaptureEvidenceInput,
) -> dict[str, Any]:
    parameters: dict[str, Any] = {}
    if args.filename is not None:
        parameters["filename"] = args.filename
    if args.timeout_seconds is not None:
        parameters["timeout_seconds"] = args.timeout_seconds
    plan = _parse_session_plan(
        args.session_id,
        {
            "session_id": args.session_id,
            "steps": [
                {
                    "step_id": args.step_id,
                    "operation": "capture_evidence",
                    "parameters": parameters,
                }
            ],
        },
    )
    result = client.execute_next(args.session_id, plan)
    return result.model_dump(mode="json")


def _tool_ot2_record_evidence(
    client: DaemonClient,
    args: Ot2RecordEvidenceInput,
) -> dict[str, Any]:
    plan = _parse_session_plan(
        args.session_id,
        {
            "session_id": args.session_id,
            "steps": [
                {
                    "step_id": args.step_id,
                    "operation": "record_evidence",
                    "parameters": {
                        "evidence_id": args.evidence_id,
                        "source_kind": args.source_kind,
                        "path": args.path,
                        "checksum_sha256": args.checksum_sha256,
                        "quality": args.quality,
                    },
                }
            ],
        },
    )
    result = client.execute_next(args.session_id, plan)
    return result.model_dump(mode="json")


def _tool_ot2_evaluate_gates(
    client: DaemonClient,
    args: Ot2EvaluateGatesInput,
) -> dict[str, Any]:
    # Gate evaluation is surfaced through the daemon session context, which
    # carries readiness, allowed/blocked operations, and the motion_allowed
    # flag. No motion is dispatched; this is a read of evaluated gates.
    context = client.get_session_context(
        args.session_id,
        fixture_qc_record=args.fixture_qc_record,
        target_class_records=args.target_class_records or None,
    )
    payload = context.model_dump(mode="json")
    return {
        "session_id": payload["session_id"],
        "state": payload["state"],
        "readiness": payload.get("readiness"),
        "allowed_next_ops": payload.get("allowed_next_ops", []),
        "blocked_ops": payload.get("blocked_ops", []),
        "motion_allowed": payload.get("motion_allowed", False),
    }


def _tool_ot2_abort_or_recover(
    client: DaemonClient,
    args: Ot2AbortOrRecoverInput,
) -> dict[str, Any]:
    report = client.recover_no_motion_session(args.session_id, timeout_seconds=args.timeout)
    return report.model_dump(mode="json")


def _tool_ot2_close_session(client: DaemonClient, args: Ot2CloseSessionInput) -> dict[str, Any]:
    report = client.close_no_motion_session(args.session_id, timeout_seconds=args.timeout)
    return report.model_dump(mode="json")


def _parse_session_plan(session_id: str, plan: dict[str, Any]) -> PlanFragment:
    # Agent-supplied plans may omit the explicit schema_version envelope field;
    # default it to the current version before strict canonical parsing of steps.
    if "schema_version" not in plan:
        plan = {**plan, "schema_version": 1}
    fragment = parse_plan_fragment(plan)
    if fragment.session_id != session_id:
        raise AgentPolicyError(
            f"plan session_id {fragment.session_id!r} does not match tool session_id "
            f"{session_id!r}"
        )
    return fragment


# --------------------------------------------------------------------------- #
# Pure-Python registry / policy / dispatch. Fully testable without the MCP SDK.
# --------------------------------------------------------------------------- #


class AgentTool(BaseModel):
    """A registered agent tool: its name, input model, and bound handler."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: str
    description: str
    input_model: type[BaseModel]


# Static registry of tool name -> (input model, description, handler kind).
# Handler kind selects how the tool is invoked: a "status" tool needs no daemon,
# every other tool needs a DaemonClient.
_TOOL_SPECS: dict[str, tuple[type[_AgentToolInput], str, str]] = {
    "ot2_status": (
        Ot2StatusInput,
        "Read-only robot health/pipette status (no daemon, no commands).",
        "status",
    ),
    "ot2_start_session": (
        Ot2StartSessionInput,
        "Start a no-motion bridge session through the daemon.",
        "daemon",
    ),
    "ot2_get_session_context": (
        Ot2GetSessionContextInput,
        "Fetch the compact session context pack from the daemon.",
        "daemon",
    ),
    "ot2_validate_plan": (
        Ot2ValidatePlanInput,
        "Validate a plan fragment against session gates (no motion approval).",
        "daemon",
    ),
    "ot2_execute_next": (
        Ot2ExecuteNextInput,
        "Execute the next approved no-motion step (never carries motion approval).",
        "daemon",
    ),
    "ot2_capture_evidence": (
        Ot2CaptureEvidenceInput,
        "Capture no-motion camera evidence via a single-step plan.",
        "daemon",
    ),
    "ot2_record_evidence": (
        Ot2RecordEvidenceInput,
        "Record an evidence artifact via a single-step plan.",
        "daemon",
    ),
    "ot2_evaluate_gates": (
        Ot2EvaluateGatesInput,
        "Read evaluated readiness gates and allowed/blocked operations.",
        "daemon",
    ),
    "ot2_abort_or_recover": (
        Ot2AbortOrRecoverInput,
        "Run the no-motion recovery/abort disposition for a session.",
        "daemon",
    ),
    "ot2_close_session": (
        Ot2CloseSessionInput,
        "Close a no-motion bridge session through the daemon.",
        "daemon",
    ),
}

_DAEMON_HANDLERS: dict[str, Any] = {
    "ot2_start_session": _tool_ot2_start_session,
    "ot2_get_session_context": _tool_ot2_get_session_context,
    "ot2_validate_plan": _tool_ot2_validate_plan,
    "ot2_execute_next": _tool_ot2_execute_next,
    "ot2_capture_evidence": _tool_ot2_capture_evidence,
    "ot2_record_evidence": _tool_ot2_record_evidence,
    "ot2_evaluate_gates": _tool_ot2_evaluate_gates,
    "ot2_abort_or_recover": _tool_ot2_abort_or_recover,
    "ot2_close_session": _tool_ot2_close_session,
}


class AgentToolRegistry:
    """Fail-closed registry of allow-listed agent tools."""

    def __init__(self, *, daemon_url: str = "http://127.0.0.1:8765") -> None:
        self.daemon_url = daemon_url
        self._tools: dict[str, AgentTool] = {}

    def register_tool(self, name: str) -> AgentTool:
        """Register a tool by name, refusing anything not on the allow-list.

        Fail-closed: a name that is denied, unknown, or not in
        ``ALLOWED_AGENT_TOOLS`` raises ``AgentPolicyError`` and is never bound.
        """

        if name in DENIED_AGENT_TOOLS:
            raise AgentPolicyError(f"tool {name!r} is explicitly denied to agents")
        if name not in ALLOWED_AGENT_TOOLS:
            raise AgentPolicyError(f"tool {name!r} is not on the agent allow-list")
        if name not in _TOOL_SPECS:
            # Defensive: an allow-listed name with no implementation must not
            # silently expose an empty tool.
            raise AgentPolicyError(f"tool {name!r} has no registered implementation")
        input_model, description, _kind = _TOOL_SPECS[name]
        tool = AgentTool(name=name, description=description, input_model=input_model)
        self._tools[name] = tool
        return tool

    def register_allowed_tools(self) -> list[AgentTool]:
        """Register exactly the allow-listed tools (sorted for determinism)."""

        return [self.register_tool(name) for name in sorted(ALLOWED_AGENT_TOOLS)]

    def registered_names(self) -> set[str]:
        return set(self._tools)

    def dispatch(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Validate and route a tool call, re-checking the allow-list.

        Defense in depth: even though registration already gates the surface,
        dispatch independently rejects denied/unknown names before any routing,
        so a tampered registry cannot smuggle a forbidden call through.
        """

        if tool_name in DENIED_AGENT_TOOLS:
            raise AgentPolicyError(f"tool {tool_name!r} is explicitly denied to agents")
        if tool_name not in ALLOWED_AGENT_TOOLS:
            raise AgentPolicyError(f"tool {tool_name!r} is not on the agent allow-list")
        if tool_name not in self._tools:
            raise AgentPolicyError(f"tool {tool_name!r} is not registered")

        input_model, _description, kind = _TOOL_SPECS[tool_name]
        parsed = input_model.model_validate(args)

        if kind == "status":
            return _tool_ot2_status(parsed)  # type: ignore[arg-type]

        handler = _DAEMON_HANDLERS[tool_name]
        client = _daemon_client(self.daemon_url)
        return handler(client, parsed)


def build_mcp_server(*, daemon_url: str = "http://127.0.0.1:8765") -> Any:
    """Build a FastMCP server exposing exactly the allow-listed agent tools.

    The MCP SDK is optional and is NOT an install requirement; it is lazy
    imported here so the pure-Python registry/policy/dispatch above stays
    importable and testable without it. A missing SDK raises a clear
    ``ImportError`` rather than failing obscurely.
    """

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised only without the SDK
        raise ImportError(
            "the MCP SDK is required to build the agent server; install the optional "
            "'mcp' package (it is intentionally not an Aevum install requirement)"
        ) from exc

    registry = AgentToolRegistry(daemon_url=daemon_url)
    registry.register_allowed_tools()
    server = FastMCP("aevum-ot2")

    def _bind(tool_name: str) -> None:
        input_model, description, _kind = _TOOL_SPECS[tool_name]

        @server.tool(name=tool_name, description=description)
        def _handler(payload: input_model) -> dict[str, Any]:  # type: ignore[valid-type]
            # Re-validate through the registry's policy-checked dispatch so the
            # SDK path and the pure-Python path share one enforcement point.
            return registry.dispatch(tool_name, payload.model_dump())

    for name in sorted(ALLOWED_AGENT_TOOLS):
        _bind(name)

    return server
