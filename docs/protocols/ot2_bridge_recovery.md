# OT-2 Bridge Recovery

## Purpose

Recovery is the fail-closed workflow after ambiguous robot state. It is required
after a timeout, bridge crash, stop event, foreign-command detection, evidence
write failure, or disagreement between local session state and robot-server
state.

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

## Recovery Procedure

1. Stop agent-driven execution for the session.
2. Record the reason recovery was entered.
3. Read robot health, active runs, maintenance runs, and command history.
4. Record the last known bridge command key and last observed robot command.
5. Capture a recovery camera image and attach it to evidence.
6. If a command may still be running, wait and re-read command state.
7. If camera evidence is ambiguous, escalate to supervised recovery.
8. If robot state and local state reconcile, mark the session `recovered` and
   require a fresh camera observation before any further motion.
9. If state does not reconcile, close the session as `unresolved_recovery` and
   do not reuse offsets or dry-verification evidence from that session.
10. Only home or retreat when the active evidence mode confirms the path is
    physically clear.

## Adapter Behavior

`ot2_abort_or_recover(session_id)` should return:

- current recovery state,
- owning session ID,
- last command key,
- last robot command ID if known,
- required camera or supervised action,
- latest recovery image handle if available,
- whether any further motion is allowed.

It should not silently clear locks or delete runs.
