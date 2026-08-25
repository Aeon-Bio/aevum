# OT-2 Maintenance-Run No-Motion Spike

Date: 2026-05-02
Robot display name: aevum
Robot URL resolved by bridge: `http://rough-morning.local:31950`
Command path: maintenance-run lifecycle only

## Goal

Verify the bridge can create, inspect, and delete a maintenance run without
enqueueing any robot command.

## Command

```text
uv run aevum-ot2 maintenance-spike-nomotion --service-name aevum --discovery-timeout 10 --timeout 15
```

## Preflight

```text
GET /health: ok
GET /runs: ok, totalLength 0
```

Current pipettes observed during this spike:

```text
left:  p300_single_gen2, model p300_single_v2.1, id P3HSV212021022403
right: p20_single_gen2, model p20_single_v2.2, id P20SV222021050621
```

The right-mount P20 was not present in the earlier read-only spike snapshot.
Future clearance and registration assumptions must use the current two-pipette
state unless the right mount is intentionally changed before motion.

## Lifecycle Result

Created maintenance run:

```text
id: db1bec0a-c35b-46c3-bc02-d64542d01078
status: idle
current: true
```

Read commands:

```text
GET /maintenance_runs/{runId}/commands: ok
command totalLength: 0
```

Deleted maintenance run:

```text
DELETE /maintenance_runs/{runId}: ok
GET /maintenance_runs/{runId}: 404 RunNotFound
```

No maintenance-run commands were enqueued. No motion commands were sent.
The structured evidence index contains the full corrected report, including the
expected post-delete 404 note.

## API Behavior Learned

- `GET /runs` is available and returned an empty protocol-run list.
- `GET /maintenance_runs` is not allowed on this robot-server version.
- `POST /maintenance_runs` creates a maintenance run and, per OpenAPI, may clear
  an existing maintenance run.
- Maintenance-run command history is readable through
  `GET /maintenance_runs/{runId}/commands`.
- Deleting an idle maintenance run succeeds and post-delete lookup returns 404.

## Design Impact

The bridge cannot rely on listing maintenance runs after a crash. It must persist
the active maintenance-run ID locally before using maintenance mode, then
reconcile that specific run ID on resume. Creating a new maintenance run should
be treated as a state-changing operation because it may clear an existing
maintenance run.
