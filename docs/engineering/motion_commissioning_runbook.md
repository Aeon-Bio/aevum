# Motion commissioning operability runbook (OT-12)

This runbook covers the **operator workflow** for first physical motion on the
OT-2 bridge. It is an operability layer over the **already-existing**
motion-capable daemon (`aevum-ot2 daemon-serve`, `BridgeService.serve()` /
`create_server`). OT-12 does not add a daemon, a gate, or a dispatch path.

## What this layer is — and is not

`src/aevum_ot2/core/commissioning.py` sequences calls to the existing
`BridgeService` and reports the outcome. It is **fail-closed** and creates **no
motion authority**:

- It never constructs a `MotionApproval`.
- It never sets `motion_allowed`.
- It never calls `consume_motion_approval` or any dispatch primitive directly.
- It calls only `BridgeService` methods: `health`, `list_sessions`,
  `get_session_context`, `validate_plan`, `arm_motion_approval`,
  `execute_next`.

The bridge core remains the **sole authority** for every gate. This layer only
orchestrates, surfaces blockers, and refuses to advance unless the operator
explicitly confirms each transition. `report.armed` / `report.executed` stay
`False` on any blocker.

## The transitions

`run_commissioning_preflight(...)` (read-only):

1. **health / state-db check** — `service.health()` + `service.list_sessions()`.
   Any exception or `health.ok is False` is a fail-closed stop.
2. **session context** — `service.get_session_context(session_id, ...)`.
3. **validate (motion-disabled, no approval)** — `service.validate_plan(...)`.
   Confirms the plan is blocked **only** by the bridge's missing-approval
   reason (`motion_approval: motion approval is required for motion
   execution`). Any other reason — or an unexpected "allowed" result — is
   surfaced as a blocker and stops the run.

`run_commissioning_sequence(...)` runs the preflight, then:

4. **arm gate** — **STOP unless** the caller passes **both**
   `confirm_arm=True` **and** `motion_enabled=True`. The **default is a
   dry-run** that reports "would arm" and emits nothing (`arm_motion_approval`
   is never called).
5. **arm** — on confirm, `service.arm_motion_approval(...)` mints and persists
   the approval inside the bridge core. The layer reports `armed` + any
   `blockers`.
6. **execute gate** — **STOP unless** the caller passes `confirm_execute=True`.
7. **execute** — on confirm, `service.execute_next(..., motion_approval=<the
   bridge-minted approval>)`. The layer reports `motion_commands_sent` +
   `blockers`.

## Operator commands

The operator script is `scripts/ot2_motion_commissioning.py`. It is a thin
argparse wrapper; **dry-run is the default**.

```bash
# 1. Dry-run preflight only (never arms). This is the default.
python scripts/ot2_motion_commissioning.py SESSION_ID plan.json \
    --safety-profile profile.json

# 2. Arm a bridge-minted approval (no motion is dispatched yet).
python scripts/ot2_motion_commissioning.py SESSION_ID plan.json \
    --safety-profile profile.json --motion-enabled --confirm-arm \
    --approved-by alice

# 3. Arm AND execute the single approved motion step.
python scripts/ot2_motion_commissioning.py SESSION_ID plan.json \
    --safety-profile profile.json --motion-enabled --confirm-arm \
    --confirm-execute --approved-by alice
```

The script exits non-zero whenever the report carries any blocker, so CI gates
and operators treat an unarmed / unexecuted run as a stop.

A CLI subcommand (`aevum-ot2 motion-commission`) is proposed for the bridge
CLI; it wraps the same `run_commissioning_preflight` / `run_commissioning_
sequence` functions with the identical dry-run-by-default contract.

## Pre-conditions before arming

The bridge core enforces all of these; the operator should expect them. Arming
requires:

- a `ready_no_motion` session with a non-expired lease and a recorded
  succeeded last command;
- an uploaded labware definition and loaded fixture labware ID;
- a fixture safety profile;
- a plan with **exactly one** motion step that the bridge blocks **only** on
  the missing approval (i.e. all readiness / pose / target / clearance gates
  already pass with motion disabled).

If the preflight reports anything other than
`plan_blocked_by_missing_approval_only = true`, resolve the surfaced blockers
before attempting to arm. Do not attempt to bypass them; this layer cannot —
and by design will not — manufacture the missing authority.

## Safety boundary

The authority exception boundary for physical motion is the bridge core and the
GX16 umbilical/local motion backend, not this layer. This operability wrapper
is read-only by default and only ever asks the bridge to do what the operator
has explicitly confirmed, one fail-closed transition at a time.
