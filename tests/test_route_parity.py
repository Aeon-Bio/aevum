"""Route parity proof: MCP and HTTP surfaces expose the same pose-bearing
routes with NO SILENT canonical default.

The pose-bearing route set is DERIVED, never hand-listed: we parse
``server/app.py`` for the literal POST route suffixes and the request model
validated in each branch, then keep only the routes whose bound request model
carries a pose-input field. If a route is added/removed in ``app.py`` or a pose
field is added/dropped from a request model, this derivation -- and the
assertions built on it -- shift with the code, so drift breaks the test instead
of silently passing.

Two safety properties are pinned here:

1. HTTP no-SILENT-default: every pose-bearing route carries every pose field it
   is responsible for, the ``DaemonClient`` methods that drive those routes
   carry every pose field as an explicit parameter, and wherever ``orientation``
   defaults to ``"canonical"`` the default is EXPLICIT and pinned at its exact
   site(s) -- it can neither move nor become implicit without failing a test.

2. MCP-vs-HTTP parity: the MCP agent surface exposes the same single pose input
   (``orientation`` on session start, with the identical explicitly-pinned
   ``"canonical"`` default) and exposes NO other pose/motion-authority input on
   its plan tools -- so an agent cannot silently assert pose or mint motion
   authority through the MCP surface either.
"""

from __future__ import annotations

import ast
import inspect

from aevum_ot2.adapters import mcp
from aevum_ot2.server import app
from aevum_ot2.server.client import DaemonClient

# The three request models that own pose-bearing route inputs. Imported by
# reference (not name strings) so a rename in app.py is a hard import failure.
_REQUEST_MODELS = {
    "StartNoMotionSessionRequest": app.StartNoMotionSessionRequest,
    "PlanRouteRequest": app.PlanRouteRequest,
    "ArmMotionApprovalRequest": app.ArmMotionApprovalRequest,
}

# The pose-input fields the parity proof tracks across both surfaces.
POSE_INPUT_FIELDS = {"orientation", "fixture_pose", "pose_claims"}

# The canonical orientation value whose default must never become silent.
CANONICAL_ORIENTATION = "canonical"


def _post_route_model_bindings() -> dict[str, str]:
    """Parse ``app.py``'s ``do_POST`` for route-literal -> request-model bindings.

    Two routing shapes are recognized, matching the handler source:

    * ``if path == "<route>": ... Model.model_validate(body)`` (the literal-path
      start-session route), and
    * ``session_id = _session_id_for_route(path, "<suffix>")`` immediately
      followed by ``if session_id is not None: ... Model.model_validate(body)``
      (the session-scoped routes).

    The route's bound model is the request model whose ``model_validate`` is
    called inside that branch.
    """

    source = inspect.getsource(app)
    do_post = _find_function(ast.parse(source), "do_POST")
    assert do_post is not None, "do_POST handler not found in server.app"

    # Flatten the handler body, descending through try blocks so the
    # session_id-assignment + guard-if pairs sit adjacently in one sequence.
    flat: list[ast.stmt] = []

    def _collect(body: list[ast.stmt]) -> None:
        for stmt in body:
            flat.append(stmt)
            if isinstance(stmt, ast.Try):
                _collect(stmt.body)

    _collect(do_post.body)

    bindings: dict[str, str] = {}

    # Shape 1: literal `path == "<route>"` guards.
    for node in ast.walk(do_post):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "path"
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and isinstance(test.comparators[0].value, str)
        ):
            model = _model_validate_target(node)
            if model is not None:
                bindings[test.comparators[0].value] = model

    # Shape 2: `_session_id_for_route(path, "<suffix>")` followed by a guard-if.
    for index, stmt in enumerate(flat):
        suffix = _session_id_route_suffix(stmt)
        if suffix is None:
            continue
        guard = flat[index + 1] if index + 1 < len(flat) else None
        if isinstance(guard, ast.If):
            model = _model_validate_target(guard)
            if model is not None:
                bindings[suffix] = model

    return bindings


def _find_function(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _session_id_route_suffix(stmt: ast.stmt) -> str | None:
    if not (isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call)):
        return None
    call = stmt.value
    if not (isinstance(call.func, ast.Name) and call.func.id == "_session_id_for_route"):
        return None
    if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
        value = call.args[1].value
        if isinstance(value, str):
            return value
    return None


def _model_validate_target(node: ast.AST) -> str | None:
    for inner in ast.walk(node):
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr == "model_validate"
            and isinstance(inner.func.value, ast.Name)
            and inner.func.value.id in _REQUEST_MODELS
        ):
            return inner.func.value.id
    return None


def _pose_bearing_routes() -> dict[str, str]:
    """Routes whose bound request model carries at least one pose-input field.

    Derived from the AST binding + the live model_fields -- not a literal list.
    """

    routes: dict[str, str] = {}
    for route, model_name in _post_route_model_bindings().items():
        fields = set(_REQUEST_MODELS[model_name].model_fields)
        if fields & POSE_INPUT_FIELDS:
            routes[route] = model_name
    return routes


POSE_BEARING_ROUTES = _pose_bearing_routes()


def _pose_fields_for(model_name: str) -> set[str]:
    return set(_REQUEST_MODELS[model_name].model_fields) & POSE_INPUT_FIELDS


# --------------------------------------------------------------------------- #
# Derivation sanity: the parser must actually find the routes, and it must find
# exactly the routes whose models carry pose inputs (so a broken parser that
# silently finds nothing cannot make every "carries every pose field" assertion
# below vacuously true).
# --------------------------------------------------------------------------- #


def test_pose_bearing_routes_are_derived_not_handlisted() -> None:
    # All three pose request models must be reachable from a POST route.
    bound_models = set(_post_route_model_bindings().values())
    assert bound_models == set(_REQUEST_MODELS), (
        "every pose request model must bind to a POST route in app.py; "
        f"found {bound_models}"
    )

    # The pose-bearing set must be non-empty and every entry must really carry a
    # pose field (guards against a vacuous-pass parser bug).
    assert POSE_BEARING_ROUTES, "no pose-bearing routes derived from app.py"
    for route, model_name in POSE_BEARING_ROUTES.items():
        assert _pose_fields_for(model_name), (
            f"route {route!r} bound to {model_name} carries no pose field"
        )

    # The session-start route owns the orientation pose input; the plan-shaped
    # routes own fixture_pose + pose_claims. This anchors the derivation against
    # a model getting its pose fields silently stripped.
    by_field: dict[str, set[str]] = {field: set() for field in POSE_INPUT_FIELDS}
    for route, model_name in POSE_BEARING_ROUTES.items():
        for field in _pose_fields_for(model_name):
            by_field[field].add(route)
    assert by_field["orientation"] == {"/sessions/start-nomotion"}
    assert by_field["fixture_pose"] == {"/validate-plan", "/execute-next", "/motion-approval/arm"}
    assert by_field["pose_claims"] == {"/validate-plan", "/execute-next", "/motion-approval/arm"}


# --------------------------------------------------------------------------- #
# (1) HTTP surface: no SILENT canonical default.
# --------------------------------------------------------------------------- #


def test_http_routes_carry_every_pose_field_they_own() -> None:
    # Restate the property positively against the live request models: the model
    # bound to each pose-bearing route must actually expose the pose field(s)
    # the route is responsible for. PlanRouteRequest/ArmMotionApprovalRequest
    # must expose both plan-shaped pose fields; the start model must expose
    # orientation.
    plan_pose = {"fixture_pose", "pose_claims"}
    for route, model_name in POSE_BEARING_ROUTES.items():
        fields = set(_REQUEST_MODELS[model_name].model_fields)
        if model_name == "StartNoMotionSessionRequest":
            assert "orientation" in fields, route
        else:
            assert plan_pose <= fields, (
                f"plan-shaped route {route!r} ({model_name}) must carry "
                f"{sorted(plan_pose)}; missing {sorted(plan_pose - fields)}"
            )


def test_daemon_client_methods_carry_every_pose_field() -> None:
    # The HTTP client methods that drive the pose-bearing routes must expose the
    # pose inputs as explicit parameters; no pose field may be reachable only by
    # a silent server-side default.
    plan_methods = {
        DaemonClient.validate_plan,
        DaemonClient.execute_next,
        DaemonClient.arm_motion_approval,
    }
    for method in plan_methods:
        params = set(inspect.signature(method).parameters)
        assert {"fixture_pose", "pose_claims"} <= params, (
            f"{method.__qualname__} must accept fixture_pose and pose_claims; "
            f"has {sorted(params)}"
        )

    start_params = inspect.signature(DaemonClient.start_no_motion_session).parameters
    assert "orientation" in start_params, (
        "DaemonClient.start_no_motion_session must accept orientation explicitly"
    )


def test_http_orientation_default_is_explicit_canonical_and_pinned() -> None:
    # Site 1: the request model field default. It must be present, EXPLICIT
    # (the model_fields entry is not required and its default is the canonical
    # string), and the field type must constrain it to the two known
    # orientations so the default cannot silently widen.
    field = app.StartNoMotionSessionRequest.model_fields["orientation"]
    assert field.is_required() is False, (
        "orientation must have an explicit default, not be a required field"
    )
    assert field.default == CANONICAL_ORIENTATION, (
        "StartNoMotionSessionRequest.orientation default moved off 'canonical'; "
        f"now {field.default!r}"
    )

    # The orientation field is a Literal["canonical", "rot180"] -- pin the exact
    # permitted set so a silent default value cannot be introduced by widening
    # the type (e.g. to a free-form str whose default could drift).
    instance = app.StartNoMotionSessionRequest(robot_url="http://ot2.local", owner_id="op")
    assert instance.orientation == CANONICAL_ORIENTATION
    annotation = repr(app.StartNoMotionSessionRequest.model_fields["orientation"].annotation)
    assert "canonical" in annotation and "rot180" in annotation, (
        "orientation must stay a Literal pinned to {'canonical', 'rot180'}; "
        f"annotation is {annotation}"
    )

    # Site 2: the DaemonClient signature default. Same canonical value, pinned to
    # the exact parameter site, so the client cannot start passing orientation
    # implicitly or drift its default.
    client_default = inspect.signature(
        DaemonClient.start_no_motion_session
    ).parameters["orientation"].default
    assert client_default == CANONICAL_ORIENTATION, (
        "DaemonClient.start_no_motion_session orientation default moved off "
        f"'canonical'; now {client_default!r}"
    )


def test_http_plan_routes_have_no_orientation_default() -> None:
    # The plan-shaped routes must NOT carry an orientation field at all: a
    # canonical orientation default leaking onto a plan/execute/arm route would
    # be exactly the silent default this test exists to forbid. Orientation is
    # owned by the session, asserted only at session start.
    for model_name in ("PlanRouteRequest", "ArmMotionApprovalRequest"):
        assert "orientation" not in _REQUEST_MODELS[model_name].model_fields, (
            f"{model_name} must not expose orientation; it would be a silent "
            "default on a plan route"
        )


# --------------------------------------------------------------------------- #
# (2) MCP surface: parity with HTTP, no silent canonical default.
# --------------------------------------------------------------------------- #


def test_mcp_orientation_is_only_pose_input_and_pinned_canonical() -> None:
    # Parity: the MCP agent surface exposes orientation in exactly one place --
    # session start -- with the identical explicitly-pinned 'canonical' default
    # as the HTTP surface. No other MCP tool input may carry orientation.
    orientation_inputs = {
        name
        for name, model in _mcp_tool_input_models().items()
        if "orientation" in model.model_fields
    }
    assert orientation_inputs == {"ot2_start_session"}, (
        "MCP must expose orientation only on ot2_start_session; "
        f"found on {sorted(orientation_inputs)}"
    )

    field = mcp.Ot2StartSessionInput.model_fields["orientation"]
    assert field.is_required() is False
    assert field.default == CANONICAL_ORIENTATION, (
        "MCP Ot2StartSessionInput.orientation default moved off 'canonical'; "
        f"now {field.default!r}"
    )
    # Match the HTTP start route's default at the value level: same canonical
    # string, so the two surfaces cannot diverge on the orientation default.
    http_default = app.StartNoMotionSessionRequest.model_fields["orientation"].default
    assert field.default == http_default


def test_mcp_plan_tools_assert_no_pose_or_motion_authority() -> None:
    # The MCP plan-shaped tools must expose NONE of fixture_pose / pose_claims /
    # motion_approval: an agent cannot silently assert fixture pose evidence nor
    # carry motion authority through the MCP surface. This is the MCP analogue
    # of "no silent canonical default" -- the only pose input agents may set is
    # orientation, and only at session start.
    forbidden = {"fixture_pose", "pose_claims", "motion_approval"}
    plan_tool_inputs = {
        "ot2_validate_plan": mcp.Ot2ValidatePlanInput,
        "ot2_execute_next": mcp.Ot2ExecuteNextInput,
    }
    for tool_name, model in plan_tool_inputs.items():
        leaked = forbidden & set(model.model_fields)
        assert not leaked, (
            f"MCP tool {tool_name} leaks pose/motion-authority input(s) {sorted(leaked)}; "
            "the agent surface must not let an agent assert pose or mint motion authority"
        )

    # And no MCP tool anywhere may surface motion_approval -- approval is an
    # operator action behind the motion-backend boundary, never agent-callable.
    for name, model in _mcp_tool_input_models().items():
        assert "motion_approval" not in model.model_fields, (
            f"MCP tool {name} must never expose motion_approval"
        )

    # arm_motion_approval must not be on the agent surface at all (parity guard:
    # the HTTP /motion-approval/arm route exists, but the agent surface omits it
    # rather than mirroring it).
    assert "ot2_arm_motion_approval" not in mcp.ALLOWED_AGENT_TOOLS
    arm_names = {name for name in mcp.ALLOWED_AGENT_TOOLS if "arm" in name or "approval" in name}
    assert arm_names == set(), (
        f"no agent tool may mint/arm motion approval; found {sorted(arm_names)}"
    )


def test_mcp_pose_inputs_match_http_pose_fields() -> None:
    # Cross-surface parity on the single shared pose input. The set of pose
    # fields the MCP surface exposes (across every tool input) must be exactly
    # the orientation input the HTTP start route exposes -- no more, no less.
    mcp_pose_fields = set()
    for model in _mcp_tool_input_models().values():
        mcp_pose_fields |= POSE_INPUT_FIELDS & set(model.model_fields)
    assert mcp_pose_fields == {"orientation"}, (
        "MCP surface must expose exactly the orientation pose input; "
        f"found {sorted(mcp_pose_fields)}"
    )
    # The HTTP surface exposes orientation as a pose-bearing input too, on the
    # session-start route; the shared input lines up.
    http_orientation_routes = {
        route
        for route, model_name in POSE_BEARING_ROUTES.items()
        if "orientation" in _REQUEST_MODELS[model_name].model_fields
    }
    assert http_orientation_routes == {"/sessions/start-nomotion"}


def _mcp_tool_input_models() -> dict[str, type]:
    """Map every allow-listed MCP tool name to its input model, via the live
    registry spec table -- so a new agent tool is automatically covered."""

    models: dict[str, type] = {}
    for name in mcp.ALLOWED_AGENT_TOOLS:
        input_model, _description, _kind = mcp._TOOL_SPECS[name]
        models[name] = input_model
    return models


def test_mcp_tool_input_models_cover_full_allow_list() -> None:
    # Guard the helper above: every allow-listed tool must have a spec, so the
    # parity sweeps cannot silently skip a tool that quietly adds a pose input.
    assert set(_mcp_tool_input_models()) == set(mcp.ALLOWED_AGENT_TOOLS)
