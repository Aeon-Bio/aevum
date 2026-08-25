# OT-2 Custom Labware Definition No-Motion Spike

Date: 2026-05-02
Robot display name: aevum
Robot URL resolved by bridge: `http://rough-morning.local:31950`
Command path: maintenance-run labware-definition upload and `loadLabware`

## Goal

Confirm how the bridge should provide the generated Aevum fixture labware
definition to robot-server before any motion-capable registration work.

## Command

```text
uv run aevum-ot2 maintenance-labware-spike --service-name aevum --discovery-timeout 10 --timeout 20 --slot 1
```

## Artifact

```text
load_name: aevum_p300_poc_fixture
namespace: aevum
version: 1
params_sha256: 8b1387a9da8f34801691e7f5fa0a2a27d39c8c1393cf79a2c3311209bc47bbb2
labware_definition_sha256: 4bc347130fa1018877fdc95ce2ea9889532e031e100af5679251f751b4eb5e23
dimensions: 127.76 x 85.48 x 91.0 mm
```

During the first attempt, robot-server rejected the generated labware definition
because `metadata.displayVolumeUnits` was `uL`. The generator was fixed to emit
the schema value `\u00b5L`, and `outputs/labware/aevum_p300_poc_fixture.json`
was regenerated.

## Pre-Upload Load Probe

```text
run_id: ce1df3cc-402d-46fe-97a7-a35f8ed5d6c6
command_id: 94f57d4b-1984-4060-b414-564990d1bab7
commandType: loadLabware
status: failed
detail: Labware "aevum_p300_poc_fixture" not found with version 1 in namespace "aevum".
```

Interpretation: the generated custom definition is not globally known to this
robot-server instance. A maintenance run must upload the definition before
loading this fixture by `loadName`/`namespace`/`version`.

## Upload Then Load Probe

```text
run_id: 0f3e1631-0a57-4754-b588-aad1aec1da26
definition upload: POST /maintenance_runs/{runId}/labware_definitions -> 201
definition_uri: aevum/aevum_p300_poc_fixture/1
```

Load command:

```text
command_id: 018138f2-9777-4285-8901-2d5d603341d1
commandType: loadLabware
status: succeeded
labwareId: aevum-fixture-post-upload
slot: 1
```

Location sequence returned:

```text
onAddressableArea: 1
onCutoutFixture: cutout1, singleStandardSlot
```

Run state included loaded labware:

```text
id: aevum-fixture-post-upload
loadName: aevum_p300_poc_fixture
definitionUri: aevum/aevum_p300_poc_fixture/1
location.slotName: 1
```

Cleanup:

```text
DELETE /maintenance_runs/{runId}: ok
GET /maintenance_runs/{runId}: 404 RunNotFound
```

No motion, homing, pipetting, or module command was sent.

## Design Impact

For maintenance mode, the bridge must upload the generated custom labware
definition into the maintenance run before issuing `loadLabware`. The bridge
should persist:

- labware definition SHA,
- definition URI,
- maintenance run ID,
- loadLabware command ID,
- loaded labware ID,
- slot/location sequence.

This completes task-graph node `A7` and unlocks `A8`: session lock plus local
active-run persistence.
