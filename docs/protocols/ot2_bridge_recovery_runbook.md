# OT-2 Bridge Recovery Runbook

Operational runbook for `ot2_abort_or_recover` — the agent-facing abort/recover
facade over the proven `recover_no_motion_session` state machine. This is the
"what do I do next" companion to the principles in
[`ot2_bridge_recovery.md`](./ot2_bridge_recovery.md).

## When to run

Run `ot2_abort_or_recover(session_id)` (or
`BridgeService.abort_or_recover(session_id)`) after any ambiguous robot state:
timeout, bridge crash, stop event, foreign-command detection, evidence write
failure, or local/robot state disagreement.

The facade is non-destructive on its own surface: it delegates the only
fail-closed `DELETE` to the proven state machine and otherwise performs read-only
lookups. It never sends motion and never sets `motion_allowed` `True`.

## Reading the report

| Field | Meaning |
| --- | --- |
| `recovery_state` | Session/lock state after the recovery attempt. |
| `disposition` | The underlying `NoMotionRecoveryDisposition` the state machine reached. |
| `required_action` | The single next action you must take (see decision table). |
| `motion_allowed` | Always `False` out of this path. Re-arming motion is a separate approved step. |
| `latest_recovery_image_handle` | Path to the most recent camera image in the session evidence index, or `null`. |
| `last_command_key` / `last_command_id` | Last known bridge command key and last observed robot command ID. |
| `recovery_report` | The embedded `NoMotionRecoveryReport` (full audit detail and notes). |

## Disposition → action decision table

| `disposition` | `required_action` | `motion_allowed` | What it means | Operator next step |
| --- | --- | --- | --- | --- |
| `recovered_closed` | `NONE` | `False` | The known no-motion / setup run was reconciled and the session is closed. | Nothing required. Start a fresh session for new work; re-arm motion only through the normal approval path. |
| `recovered_active` | `CAPTURE_CAMERA_EVIDENCE` | `False` | A single known journaled motion command (e.g. `moveToWell`) was reconciled; the maintenance run remains active and pose state is now stale. | Capture a fresh camera observation before any further motion; re-validate pose, then re-arm motion through approval. |
| `unresolved_recovery` | `SUPERVISED_RECOVERY` | `False` | Robot and local state could not be reconciled (unexpected command types, incomplete history, or unreadable run). Session held in `recovery_required`. | Bring in a human. Inspect the deck and command history; do not reuse offsets or dry-verification evidence from this session. |
| `no_local_session` | `SUPERVISED_RECOVERY` | `False` | No local session record exists for the ID. Nothing to reconcile from this side. | Verify the session ID and check the robot directly for orphaned maintenance runs; resolve under supervision. |
| `not_started` | `MANUAL_HARDWARE_ABORT` | `False` | The state machine reports a run that never reached a recovery decision — an unexpected, indeterminate state. | Treat as worst case: physically confirm the head is clear / abort at the hardware before any further automation. |
| _any unmapped disposition_ | `SUPERVISED_RECOVERY` | `False` | Fail-closed default for a disposition with no explicit projection. | Treat as unresolved: escalate to a human before any motion. |

`CAPTURE_CAMERA_EVIDENCE` and `SUPERVISED_RECOVERY` both block autonomous motion
until satisfied. `NONE` means the recovery itself needs no follow-up — it does
**not** mean motion is authorized; motion is always re-armed through the separate
approval path.

## What this facade does NOT do

- It does not call `post_json` / `delete_json` or otherwise drive the robot.
- It does not clear locks or delete maintenance runs itself.
- It does not set `motion_allowed` `True`.
- It does not re-arm motion or grant approval.

A boundary test asserts the module contains no executable reference to the robot
transport (`.post_json(`, `.delete_json(`, `Ot2Client`).

## Surfacing status

- Implemented: core facade `ot2_abort_or_recover` and
  `BridgeService.abort_or_recover`.
- Follow-up: HTTP route, daemon client method, and CLI subcommand wiring (a
  transport, not motion authority).
