from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tree(path: str) -> ast.Module:
    return ast.parse((ROOT / path).read_text())


def _imported_modules(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


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


def test_daemon_http_adapter_does_not_import_raw_ot2_transport() -> None:
    tree = _tree("src/aevum_ot2/server/app.py")

    assert "aevum_ot2.core.client" not in _imported_modules(tree)
    assert not {"post_json", "delete_json"} & _called_attributes(tree)


def test_daemon_client_adapter_does_not_import_raw_ot2_transport() -> None:
    tree = _tree("src/aevum_ot2/server/client.py")

    assert "aevum_ot2.core.client" not in _imported_modules(tree)
    assert not {"post_json", "delete_json"} & _called_attributes(tree)


def test_cli_adapter_does_not_send_raw_robot_commands() -> None:
    tree = _tree("src/aevum_ot2/adapters/cli.py")

    assert "Ot2Client" not in _imported_names(tree)
    assert not {"post_json", "delete_json"} & _called_attributes(tree)


def test_robot_command_post_call_sites_are_allowlisted() -> None:
    allowed = {
        Path("src/aevum_ot2/core/client.py"),
        Path("src/aevum_ot2/core/command_journal.py"),
        Path("src/aevum_ot2/core/maintenance.py"),
        Path("src/aevum_ot2/core/recovery.py"),
        Path("src/aevum_ot2/core/sessions.py"),
    }
    offenders: list[str] = []
    for path in (ROOT / "src/aevum_ot2").rglob("*.py"):
        relative = path.relative_to(ROOT)
        tree = ast.parse(path.read_text())
        if {"post_json", "delete_json"} & _called_attributes(tree) and relative not in allowed:
            offenders.append(str(relative))

    assert offenders == []


def test_mcp_policy_surface_excludes_raw_robot_control() -> None:
    text = (ROOT / "docs/engineering/implementation_trajectory.md").read_text()
    expected_tools = {
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

    for tool in expected_tools:
        assert tool in text
    assert "ot2_post_json" not in text
    assert "ot2_raw_http" not in text
    assert "ot2_move_coordinates" not in text
    assert "ot2_set_offset" not in text


# --- OT-7: MCP agent adapter boundary ----------------------------------------------------


def test_mcp_adapter_does_not_send_raw_robot_commands() -> None:
    # Same boundary as the CLI adapter: no mutating raw transport. The read-only
    # fetch_robot_status helper from core.client is allowed (ot2_status), exactly as cli.py
    # uses it; what is forbidden is the Ot2Client transport and any post_json/delete_json.
    tree = _tree("src/aevum_ot2/adapters/mcp.py")
    assert "Ot2Client" not in _imported_names(tree)
    assert not {"post_json", "delete_json"} & _called_attributes(tree)


def test_mcp_adapter_exposes_exactly_the_allow_listed_agent_tools() -> None:
    from aevum_ot2.adapters.mcp import ALLOWED_AGENT_TOOLS, DENIED_AGENT_TOOLS

    assert set(ALLOWED_AGENT_TOOLS) == {
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
    assert {
        "set_offset",
        "move_to_coordinates",
        "post_command",
        "ot2_set_offset",
        "ot2_move_coordinates",
        "ot2_post_json",
        "ot2_raw_http",
    } <= set(DENIED_AGENT_TOOLS)
    assert set(ALLOWED_AGENT_TOOLS).isdisjoint(DENIED_AGENT_TOOLS)
    assert "arm_motion_approval" not in ALLOWED_AGENT_TOOLS


def test_mcp_adapter_never_arms_motion_approval() -> None:
    tree = _tree("src/aevum_ot2/adapters/mcp.py")
    # No agent tool mints/consumes motion authority.
    assert "arm_motion_approval" not in _called_attributes(tree)
    assert "arm_motion_approval" not in _imported_names(tree)


# --- OT-10: abort/recover facade boundary ------------------------------------------------


def test_abort_recover_facade_does_not_send_raw_robot_commands() -> None:
    tree = _tree("src/aevum_ot2/core/abort_recover.py")
    assert "Ot2Client" not in _imported_names(tree)
    assert not {"post_json", "delete_json"} & _called_attributes(tree)
