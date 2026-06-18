# OT-2 Bridge Recovery

## Purpose

Recovery is the fail-closed workflow after ambiguous robot state. It is required
after a timeout, bridge crash, stop event, foreign-command detection, evidence
write failure, or disagreement between local session state and robot-server
state. Recovery reconciles only **known no-motion maintenance runs**; anything it
cannot prove safe stays blocked and escalates to a human.

## Authority Boundary

There are two layers, and only one of them owns motion authority:

- `recover_no_motion_session` (`src/aevum_ot2/core/recovery.py`) is the **proven
  state machine**. It owns the only fail-closed `DELETE` of a maintenance run and
  is the allowlisted mutator of session/lock state. It is not modified by the
  agent path.
- `ot2_abort_or_recover` (`src/aevum_ot2/core/abort_recover.py`) is the
  **agent-facing facade**. It is pure composition: it calls the state machine,
  then PROJECTS the resulting `NoMotionRecoveryReport` into the agent contract
  using read-only lookups (`read_session`, `read_lock`, and the session evidence
  index). It MUST NOT call `post_json` / `delete_json` and MUST NOT create motion
  authority.

`motion_allowed` in the agent report is **always derived** from the recovered
session and is **never** `True` out of this path. The recovery state machine
leaves `session.motion_allowed` `False` on every disposition, so the facade only
ever surfaces a fail-closed motion gate. Re-arming motion is a separate,
explicitly-approved step that happens after recovery, never inside it.

## Recovery Principles

- Do not issue more motion until state is reconciled.
- Treat bridge pose state as stale.
- Capture camera evidence before any recovery motion when image capture is
  available.
- Record every recovery decision in the evidence file.
- Prefer camera evidence and command-history reconciliation before any retreat
  or home command.
- Use human intervention only when camera evidence is unavailable, ambiguous, or
  insufficient for a safe autonomous recovery decision.
- The facade never silently clears locks or deletes runs; it reports what the
  proven state machine decided.

## Recovery Procedure

1. Stop agent-driven execution for the session.
2. Record the reason recovery was entered.
3. Read robot health, active runs, maintenance runs, and command history.
4. Record the last known bridge command key and last observed robot command.
5. Capture a recovery camera image and attach it to evidence.
6. If a command may still be running, wait and re-read command state.
7. If camera evidence is ambiguous, escalate to supervised recovery.
8. If robot state and local state reconcile, mark the session recovered and
   require a fresh camera observation before any further motion.
9. If state does not reconcile, hold the session in `recovery_required` as
   `unresolved_recovery` and do not reuse offsets or dry-verification evidence
   from that session.
10. Only home or retreat when the active evidence mode confirms the path is
    physically clear.

## Agent Contract (`ot2_abort_or_recover`)

`ot2_abort_or_recover(session_id)` returns an `AbortOrRecoverReport`:

- `recovery_state` — projected session/lock state after recovery.
- `owning_session_id` — the session the recovery acted on.
- `last_command_key` — last known bridge command key.
- `last_command_id` — last observed robot command ID, if known.
- `required_action` — the single fail-closed next action
  (`NONE` | `CAPTURE_CAMERA_EVIDENCE` | `SUPERVISED_RECOVERY` |
  `MANUAL_HARDWARE_ABORT`).
- `latest_recovery_image_handle` — read-only handle of the most recent camera
  image in the session evidence index, if any.
- `motion_allowed` — always derived, never `True` out of this path.
- `disposition` — the underlying `NoMotionRecoveryDisposition`.
- `recovery_report` — the embedded `NoMotionRecoveryReport`, carried verbatim for
  audit.

The disposition-to-action mapping is the operational decision table; see
[`ot2_bridge_recovery_runbook.md`](./ot2_bridge_recovery_runbook.md).

## Surfacing

The facade is exposed at the service layer as
`BridgeService.abort_or_recover(session_id)`. Wiring an HTTP route, a daemon
client method, and a CLI subcommand is follow-up work and is intentionally not
part of the facade itself (it would add a transport, not motion authority).
