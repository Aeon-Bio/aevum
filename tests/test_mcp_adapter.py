from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from aevum_ot2.adapters import mcp
from aevum_ot2.adapters.mcp import (
    ALLOWED_AGENT_TOOLS,
    DENIED_AGENT_TOOLS,
    AgentPolicyError,
    AgentToolRegistry,
    build_mcp_server,
)

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TOOLS = {
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


class _FakeModel:
    """Stand-in for a pydantic result that supports model_dump(mode=...)."""

    def __init__(self, **data: Any) -> None:
        self._data = data

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        return dict(self._data)


class FakeDaemonClient:
    """Captures DaemonClient calls so tests can assert what crosses the boundary."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def _record(self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> _FakeModel:
        self.calls.append((name, args, kwargs))
        return _FakeModel(ok=True, op=name)

    def start_no_motion_session(self, *args: Any, **kwargs: Any) -> _FakeModel:
        return self._record("start_no_motion_session", args, kwargs)

    def get_session_context(self, *args: Any, **kwargs: Any) -> _FakeModel:
        self.calls.append(("get_session_context", args, kwargs))
        return _FakeModel(
            session_id=args[0] if args else kwargs.get("session_id"),
            state="ready_no_motion",
            readiness=None,
            allowed_next_ops=["inspect_context", "capture_evidence"],
            blocked_ops=[{"operation": "home", "reason": "no motion", "severity": "blocker"}],
            motion_allowed=False,
        )

    def validate_plan(self, *args: Any, **kwargs: Any) -> _FakeModel:
        return self._record("validate_plan", args, kwargs)

    def execute_next(self, *args: Any, **kwargs: Any) -> _FakeModel:
        return self._record("execute_next", args, kwargs)

    def recover_no_motion_session(self, *args: Any, **kwargs: Any) -> _FakeModel:
        return self._record("recover_no_motion_session", args, kwargs)

    def close_no_motion_session(self, *args: Any, **kwargs: Any) -> _FakeModel:
        return self._record("close_no_motion_session", args, kwargs)


@pytest.fixture
def fake_client(monkeypatch) -> FakeDaemonClient:
    client = FakeDaemonClient()
    monkeypatch.setattr(mcp, "_daemon_client", lambda *a, **k: client)
    return client


def _registry() -> AgentToolRegistry:
    registry = AgentToolRegistry(daemon_url="http://127.0.0.1:8765")
    registry.register_allowed_tools()
    return registry


# --------------------------------------------------------------------------- #
# Surface / policy
# --------------------------------------------------------------------------- #


def test_allow_and_deny_lists_are_the_expected_disjoint_sets() -> None:
    assert set(ALLOWED_AGENT_TOOLS) == EXPECTED_TOOLS
    assert DENIED_AGENT_TOOLS == {
        "set_offset",
        "move_to_coordinates",
        "post_command",
        "ot2_set_offset",
        "ot2_move_coordinates",
        "ot2_post_json",
        "ot2_raw_http",
    }
    assert ALLOWED_AGENT_TOOLS.isdisjoint(DENIED_AGENT_TOOLS)
    assert "arm_motion_approval" not in ALLOWED_AGENT_TOOLS
    assert "ot2_arm_motion_approval" not in ALLOWED_AGENT_TOOLS


def test_registry_registers_exactly_the_ten_allowed_tools() -> None:
    registry = _registry()
    assert registry.registered_names() == EXPECTED_TOOLS
    assert len(registry.registered_names()) == 10


def test_register_tool_fail_closed_on_denied_name() -> None:
    registry = AgentToolRegistry()
    for name in DENIED_AGENT_TOOLS:
        with pytest.raises(AgentPolicyError, match="denied"):
            registry.register_tool(name)


def test_register_tool_fail_closed_on_unknown_name() -> None:
    registry = AgentToolRegistry()
    with pytest.raises(AgentPolicyError, match="not on the agent allow-list"):
        registry.register_tool("ot2_definitely_not_a_tool")


def test_dispatch_rechecks_allowlist_even_if_registry_tampered() -> None:
    registry = _registry()
    # Smuggle a denied/unknown name straight into the internal table to prove the
    # dispatcher does NOT trust the registry blindly (defense in depth).
    registry._tools["ot2_post_json"] = registry._tools["ot2_status"]  # type: ignore[index]
    with pytest.raises(AgentPolicyError, match="denied"):
        registry.dispatch("ot2_post_json", {})

    registry._tools["totally_unknown"] = registry._tools["ot2_status"]  # type: ignore[index]
    with pytest.raises(AgentPolicyError, match="not on the agent allow-list"):
        registry.dispatch("totally_unknown", {})


def test_dispatch_rejects_unregistered_allowed_tool() -> None:
    registry = AgentToolRegistry()  # nothing registered yet
    with pytest.raises(AgentPolicyError, match="not registered"):
        registry.dispatch("ot2_status", {"robot": "http://ot2.local:31950"})


# --------------------------------------------------------------------------- #
# ot2_status -> read-only direct core, never the daemon
# --------------------------------------------------------------------------- #


def test_ot2_status_uses_resolve_and_fetch_not_daemon(monkeypatch) -> None:
    seen: dict[str, Any] = {}

    def fake_resolve(robot, *, service_name, timeout_seconds):
        seen["resolve"] = (robot, service_name, timeout_seconds)
        return SimpleNamespace(
            robot_url="http://ot2.local:31950",
            model_dump=lambda mode="python": {
                "robot_url": "http://ot2.local:31950",
                "source": "argument",
            },
        )

    def fake_fetch(robot_url, *, timeout_seconds):
        seen["fetch"] = (robot_url, timeout_seconds)
        return _FakeModel(robot_url=robot_url, ok=True)

    def fail_daemon(*a, **k):  # pragma: no cover - must never be called
        raise AssertionError("ot2_status must not touch the daemon")

    monkeypatch.setattr(mcp, "resolve_robot", fake_resolve)
    monkeypatch.setattr(mcp, "fetch_robot_status", fake_fetch)
    monkeypatch.setattr(mcp, "_daemon_client", fail_daemon)

    registry = _registry()
    result = registry.dispatch("ot2_status", {"robot": "http://ot2.local:31950"})

    assert seen["resolve"][0] == "http://ot2.local:31950"
    assert seen["fetch"][0] == "http://ot2.local:31950"
    assert result["status"]["ok"] is True


# --------------------------------------------------------------------------- #
# Stateful tools route through DaemonClient, never minting motion authority
# --------------------------------------------------------------------------- #


def test_validate_plan_never_injects_motion_approval_or_orientation(fake_client) -> None:
    registry = _registry()
    registry.dispatch(
        "ot2_validate_plan",
        {
            "session_id": "session-1",
            "plan": {
                "session_id": "session-1",
                "steps": [{"step_id": "home", "operation": "home"}],
            },
        },
    )
    name, args, kwargs = fake_client.calls[-1]
    assert name == "validate_plan"
    assert "motion_approval" not in kwargs
    assert "orientation" not in kwargs
    assert args[0] == "session-1"


def test_execute_next_never_injects_motion_approval_or_orientation(fake_client) -> None:
    registry = _registry()
    registry.dispatch(
        "ot2_execute_next",
        {
            "session_id": "session-1",
            "plan": {
                "session_id": "session-1",
                "steps": [{"step_id": "inspect", "operation": "inspect_context"}],
            },
        },
    )
    name, args, kwargs = fake_client.calls[-1]
    assert name == "execute_next"
    assert "motion_approval" not in kwargs
    assert "orientation" not in kwargs


def test_validate_plan_rejects_session_id_mismatch(fake_client) -> None:
    registry = _registry()
    with pytest.raises(AgentPolicyError, match="does not match"):
        registry.dispatch(
            "ot2_validate_plan",
            {
                "session_id": "session-1",
                "plan": {
                    "session_id": "other-session",
                    "steps": [{"step_id": "home", "operation": "home"}],
                },
            },
        )


def test_capture_evidence_routes_through_execute_next(fake_client) -> None:
    registry = _registry()
    registry.dispatch(
        "ot2_capture_evidence",
        {"session_id": "session-1", "filename": "deck.jpg"},
    )
    name, args, kwargs = fake_client.calls[-1]
    assert name == "execute_next"
    plan = args[1]
    assert [step.operation for step in plan.steps] == ["capture_evidence"]
    assert plan.steps[0].parameters["filename"] == "deck.jpg"
    assert "motion_approval" not in kwargs


def test_record_evidence_routes_through_execute_next(fake_client) -> None:
    registry = _registry()
    registry.dispatch(
        "ot2_record_evidence",
        {
            "session_id": "session-1",
            "evidence_id": "ev-1",
            "source_kind": "camera_capture",
            "path": "data/measurements/images/deck.jpg",
            "checksum_sha256": "a" * 64,
        },
    )
    name, args, kwargs = fake_client.calls[-1]
    assert name == "execute_next"
    plan = args[1]
    assert [step.operation for step in plan.steps] == ["record_evidence"]
    assert plan.steps[0].parameters["evidence_id"] == "ev-1"
    assert "motion_approval" not in kwargs


def test_evaluate_gates_reads_context_and_reports_motion_blocked(fake_client) -> None:
    registry = _registry()
    result = registry.dispatch(
        "ot2_evaluate_gates",
        {"session_id": "session-1"},
    )
    name, _args, _kwargs = fake_client.calls[-1]
    assert name == "get_session_context"
    assert result["motion_allowed"] is False
    assert result["session_id"] == "session-1"


def test_abort_or_recover_routes_to_recover(fake_client) -> None:
    registry = _registry()
    registry.dispatch("ot2_abort_or_recover", {"session_id": "session-1"})
    assert fake_client.calls[-1][0] == "recover_no_motion_session"


def test_close_session_routes_to_close(fake_client) -> None:
    registry = _registry()
    registry.dispatch("ot2_close_session", {"session_id": "session-1"})
    assert fake_client.calls[-1][0] == "close_no_motion_session"


def test_start_session_carries_operator_orientation(fake_client) -> None:
    registry = _registry()
    registry.dispatch(
        "ot2_start_session",
        {
            "robot_url": "http://ot2.local:31950",
            "owner_id": "agent-1",
            "slot": "5",
            "orientation": "rot180",
        },
    )
    name, _args, kwargs = fake_client.calls[-1]
    assert name == "start_no_motion_session"
    assert kwargs["orientation"] == "rot180"


# --------------------------------------------------------------------------- #
# Input models forbid extras (motion authority cannot be smuggled in)
# --------------------------------------------------------------------------- #


def test_tool_inputs_forbid_unknown_fields(fake_client) -> None:
    registry = _registry()
    with pytest.raises(ValidationError):  # extra='forbid' on the tool input model
        registry.dispatch(
            "ot2_execute_next",
            {
                "session_id": "session-1",
                "plan": {"session_id": "session-1", "steps": []},
                "motion_approval": {"approval_id": "x"},
            },
        )


# --------------------------------------------------------------------------- #
# build_mcp_server lazy-imports the SDK and fails clearly when absent
# --------------------------------------------------------------------------- #


def test_build_mcp_server_raises_clear_import_error_without_sdk(monkeypatch) -> None:
    import builtins

    real_import = builtins.__import__

    def blocked_import(name: str, *args: Any, **kwargs: Any):
        if name.startswith("mcp.server") or name == "mcp":
            raise ImportError("no mcp sdk in test environment")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    with pytest.raises(ImportError, match="MCP SDK is required"):
        build_mcp_server()


# --------------------------------------------------------------------------- #
# Static boundary scan (mirrors tests/test_adapter_boundaries.py house style)
# --------------------------------------------------------------------------- #


def _tree(path: str) -> ast.Module:
    return ast.parse((ROOT / path).read_text())


def _imported_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.asname or alias.name.rsplit(".", 1)[-1] for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in node.names)
    return names


def _called_attributes(tree: ast.Module) -> set[str]:
    attributes: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attributes.add(node.func.attr)
    return attributes


def test_mcp_adapter_imports_no_raw_robot_transport() -> None:
    tree = _tree("src/aevum_ot2/adapters/mcp.py")
    names = _imported_names(tree)
    assert "Ot2Client" not in names
    assert "post_json" not in _called_attributes(tree)
    assert "delete_json" not in _called_attributes(tree)


def test_mcp_adapter_does_not_arm_motion_approval() -> None:
    tree = _tree("src/aevum_ot2/adapters/mcp.py")
    assert "arm_motion_approval" not in _called_attributes(tree)
