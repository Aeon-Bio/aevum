# OT-2 Comment Command Key No-Motion Spike

Date: 2026-05-02
Robot display name: aevum
Robot URL resolved by bridge: `http://rough-morning.local:31950`
Command path: maintenance-run `comment` commands only

## Goal

Probe maintenance-run command `key` behavior without sending any motion, homing,
pipetting, labware, or hardware-control command.

## Command

```text
uv run aevum-ot2 maintenance-comment-key-spike --service-name aevum --discovery-timeout 10 --timeout 15
```

## Preflight

```text
GET /health: ok
GET /runs: ok, totalLength 0
```

Current pipettes observed:

```text
left:  p300_single_gen2, model p300_single_v2.1, id P3HSV212021022403
right: p20_single_gen2, model p20_single_v2.2, id P20SV222021050621
```

## Maintenance Run

```text
run_id: 6117b063-e42a-43b7-ac1f-3788eb34ff65
command_key: aevum-comment-key-20260502-134017
```

## First Comment Command

```text
command_id: 67a1d562-5a42-45af-a02d-d3459e228cbb
commandType: comment
key: aevum-comment-key-20260502-134017
status: succeeded
intent: setup
commands totalLength after first command: 1
```

`GET /maintenance_runs/{runId}/commands/{commandId}` returned the same command
ID, key, status, and params.

## Duplicate-Key Comment Command

The spike posted a second `comment` command with the same `key`.

```text
command_id: fc77e21f-e461-487a-8f66-fb1912bf76bf
commandType: comment
key: aevum-comment-key-20260502-134017
status: succeeded
commands totalLength after duplicate: 2
```

The duplicate key was accepted and produced a separate command ID.

## Cleanup

```text
DELETE /maintenance_runs/{runId}: ok
GET /maintenance_runs/{runId}: 404 RunNotFound
```

No motion commands were sent.

## Design Impact

On this robot-server version, maintenance-run command keys are not an
idempotency guard. They are useful correlation labels, but duplicate keys can
exist in the same maintenance run. Recovery logic must reconcile by command ID,
command index, command status, timestamps, and payload, not by key alone.
