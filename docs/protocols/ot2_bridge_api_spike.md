# OT-2 Bridge API Spike

## Purpose

Before implementing live motion, verify the specific robot-server behavior that
the bridge architecture depends on. Documentation is not enough for these
details because API behavior can vary by robot software version.

## Required Before Live Motion

Record results in `data/measurements/YYYY-MM-DD_ot2_api_spike.md`.

Initial read-only and direct camera results are recorded in:

```text
data/measurements/2026-05-02_ot2_api_spike.md
```

Initial no-motion maintenance-run lifecycle results are recorded in:

```text
data/measurements/2026-05-02_ot2_maintenance_nomotion.md
data/measurements/2026-05-02_ot2_comment_key_nomotion.md
data/measurements/2026-05-02_ot2_labware_definition_nomotion.md
```

The robot was renamed to display/service name `aevum`, but direct HTTP during
the first spike resolved to `rough-morning.local:31950`. Bridge code should
discover `aevum._http._tcp.local` or use `AEVUM_OT2_ROBOT_URL` when an explicit
host override is needed.

Current read-only CLI commands default to that discovery path:

```text
uv run aevum-ot2 resolve --service-name aevum
uv run aevum-ot2 status --service-name aevum
```

## Checks

1. Read `/health` and record robot serial, robot-server version, and API links.
2. Fetch `/openapi` or `/openapi.json` from port `31950` and save the observed
   API version/hash.
3. Confirm the required `Opentrons-Version` header value for the installed
   robot-server version.
4. Confirm the maximum supported Python Protocol API version. The current
   scaffold targets API `2.28`; camera autonomy requires at least API `2.27`.
5. Confirm `GET /pipettes` returns the currently attached pipette names and
   mounts. The original motion target is P300 Gen2 on the left mount, but later
   no-motion evidence observed a right-mount P20 Gen2; do not assume either
   state without a fresh read before motion.
6. Confirm camera capability on this robot software:
   - whether `ProtocolContext.capture_image()` is available,
   - required API level,
   - whether camera capture is available through maintenance-run or HTTP
     commands,
   - where images are stored and how the bridge retrieves them.
7. Capture a still image and save/retrieve it into evidence storage.
8. Create a maintenance run without motion.
9. Confirm whether maintenance-run commands accept command `key` values and
   whether those keys are unique, searchable, or merely echoed back. No-motion
   `comment` commands accepted duplicate keys on 2026-05-02, so keys must not be
   treated as idempotency guards.
10. Confirm command-history reads after a command timeout can reconcile command
   state safely enough for the bridge policy.
11. Confirm how custom labware definitions are loaded or referenced in
   maintenance runs. On 2026-05-02, the generated definition had to be uploaded
   to the maintenance run before `loadLabware`; direct reference before upload
   failed.
12. Confirm whether named labware target moves are available in maintenance mode
   for the generated fixture, or whether first registration must use bounded raw
   deck coordinates.
13. Confirm how active runs and maintenance runs are listed after bridge crash or
    client disconnect.
14. Confirm deleting a maintenance run is safe only when no command is running.
15. Confirm robot-server behavior when the Opentrons App is opened during an
    active bridge-created maintenance run.

## Acceptance

Do not implement live motion until:

- command correlation/reconciliation behavior is understood,
- camera capture/retrieval behavior is understood,
- supported Python Protocol API version is recorded,
- current attached pipettes and mounts are verified against the intended
  workflow,
- custom labware upload/load behavior is recorded,
- active-run recovery behavior is understood,
- the tested `Opentrons-Version` is recorded,
- failure cases are written into the recovery runbook.
