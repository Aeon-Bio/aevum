# OT-2 Control Surfaces

## Purpose

Aevum will not rely on the Opentrons App as its primary control plane. The robot
will be controlled through a package-owned bridge core that targets unattended
autonomy for validated workflows, talks to documented Opentrons interfaces,
records evidence, and prevents concurrent or unsafe motion among bridge clients.

This page records the relevant OT-2 APIs and how they should inform our bridge.

## Control Surface Summary

| Surface | Role In Aevum | Strengths | Hazards |
| --- | --- | --- | --- |
| Robot HTTP API | Primary transport for the bridge | Remote, typed, OpenAPI-described, exposes runs, maintenance runs, commands, offsets, logs, and health | Physical motion is easy to trigger; commands must be serialized and safety-checked |
| Python Protocol API | Semantic model for protocol generation and simulation | Stable labware/pipette/well abstractions; good for repeatable runs | Too permissive if handed directly to an agent REPL |
| Built-in OT-2 camera | Primary autonomy observation channel | 2 MP deck/working-area still images; Python API `capture_image()` in API v2.27 | No documented protocol-run live stream path; vision confidence must be validated |
| Jupyter Notebook | Manual debugging only | Cell-by-cell robot control; runs on the robot | Stateful, easy to desynchronize, requires self-managed offsets |
| `opentrons_execute` | Batch execution fallback | Runs protocol files from the robot command line | Coarse control surface; still requires offsets in code |
| Opentrons App | Optional reference/calibration aid, not primary control | Mature Labware Position Check workflow | Breaks agent-native control loop and manualizes setup |

## Robot HTTP API

The robot server exposes an HTTP API described by an OpenAPI specification. The
published reference says the spec can be retrieved from a robot on port `31950`
at `/openapi`; the health response includes links such as `/openapi.json` and
robot logs. Most HTTP API endpoints require an `Opentrons-Version` header, with
`*` accepted to request the latest version unconditionally. Aevum should use
`*` only during discovery/debugging. Motion commands should use an explicitly
tested version.

Relevant API families:

- `/health`: verify that the robot server and motor controller are ready and
  discover API/log links.
- `/pipettes`: verify attached instruments before any motion plan.
- `/labwareOffsets`: inspect, search, create, or delete persisted labware
  offsets.
- `/runs`: create a tracked run, add labware offsets, enqueue setup/protocol
  commands, play/pause/stop, and read command history/errors.
- `/maintenance_runs`: create a direct-control run and enqueue commands that
  execute immediately in order.
- `/commands`: simple stateless command endpoint. The docs describe this as
  meant for simple control and recommend creating a run for complex control.
- `/logs/*`: collect API, serial, server, and related logs for evidence.

The deprecated `/robot/move` endpoint is still documented, but the official
reference points users toward `moveToCoordinates` commands inside maintenance
runs instead. Aevum should not build new logic on deprecated movement endpoints.

### Maintenance Runs

Maintenance runs are the right first transport for the printed
`p300_poc_fixture` validation because we need direct, slow, observable robot
motion before trusting a full protocol. Maintenance-run commands are enqueued on
`/maintenance_runs/{runId}/commands` and execute immediately in order. They are
not pauseable as a queue, so the bridge must use small movement increments and
wait for each command result before sending the next one. After any timeout, the
bridge must reconcile command history before issuing another motion command.

Use maintenance runs for:

- robot discovery and readiness checks,
- homing,
- loading or declaring relevant labware/instruments where supported,
- high-Z fixture approach,
- measured jog/registration steps,
- dry collision-clearance checks,
- first low-Z approach only after explicit registration.

Do not use maintenance runs for unattended liquid-handling experiments until the
fixture geometry, offsets, camera gates, and guardrails are proven.

### Built-In Camera

Official Opentrons docs say every OT-2 has a built-in 2-megapixel camera that
can capture still images of the deck and working area. The Python Protocol API
documents `ProtocolContext.capture_image()` in API `v2.27`. The App feature docs
also note that, due to processing and memory limits, the OT-2 cannot live-stream
a protocol run through that documented path.

Aevum should use still-image capture as the first autonomy observation channel:

- fixture presence and orientation,
- post-print QC evidence,
- high-Z target approach evidence,
- target-class verification,
- recovery snapshots,
- unattended run audit records.

The bridge must verify the exact camera capture and retrieval path on the
installed robot software before depending on camera gates for unattended
operation.

Bench verification on 2026-05-02 showed the robot service instance then named
`aevum` resolving through the historical host `rough-morning.local:31950`.
Current bench state on 2026-05-05 reaches robot `aevum` directly at
`http://192.168.109.136:31950`; bridge commands should use discovery or the
explicit URL override rather than hard-coding the historical hostname. The same
robot exposes `POST /camera/picture` for direct non-motion JPEG capture.
`GET /camera/stream/settings` reports that the Opentrons live stream service is
not available on OT-2.

### Protocol Runs

Protocol runs should be used after registration is stable and the task is
repeatable. The bridge can either upload/generated a Python protocol or enqueue
protocol commands over HTTP. A protocol run is the better record for a validated
procedure because commands, run state, offsets, and command errors live under a
single run ID.

Use protocol runs for:

- repeated dry motion tests,
- dye/water dispense after dry verification,
- future incubation or imaging workflows that should replay exactly,
- runs that should be analyzed before execution.

## Python Protocol API

The Python Protocol API is the right conceptual layer for Aevum's protocol
model. It expresses the biology/robotics task in labware, wells, pipettes, tips,
and movements. The current dry motion scaffold already uses this layer in
`opentrons/test_p300_poc.py`.

Keep using Protocol API concepts when designing agent plans:

- `ProtocolContext` loads labware, instruments, modules, and controls flow.
- Labware wells provide named coordinate frames.
- Pipettes can move to well locations, pick up tips, aspirate, dispense, and
  drop tips.
- Custom labware definitions let generated Aevum fixture geometry become robot
  addressable.

The bridge should not expose arbitrary Python execution to agents. Agents should
submit structured plans that are compiled into Protocol API code or HTTP run
commands after validation.

## Jupyter And Command Line Control

Opentrons documents Jupyter as an advanced control option. Flex and OT-2 robots
run Jupyter Notebook on port `48888`; code can get a `ProtocolContext` through
`opentrons.execute.get_protocol_api()`. The docs state that the first command
should be `home()` when controlling this way, otherwise a `MustHomeError` can
occur.

Jupyter is useful for manual debugging, but it is a poor primary LLM bridge:

- notebook state is implicit and hard to audit,
- multiple agents could race unless an external lock exists,
- offsets must be handled by our code,
- module control can conflict with the robot server unless handled carefully.

`opentrons_execute` can run protocol files from the robot command line. It is a
reasonable fallback for batch execution or local debugging, but not the primary
interactive agent interface.

## Labware Offsets

Labware offsets are fine positional corrections that align a pipette to a
specific piece of labware. Opentrons states that on OT-2 these offsets should be
reused only for the same labware type in the same deck slot on the same robot.
The docs also warn that improper offset reuse can cause unexpected movement or
crashes against labware.

Aevum needs an agent-native registration workflow because the Opentrons App is
not the primary control surface. The bridge must own:

- fixture definition URI and version,
- robot serial and software version,
- deck slot,
- pipette name and mount,
- measured `x/y/z` offset,
- measurement method and operator/agent notes,
- date, run ID, and command evidence.

Treat offsets as physical evidence, not just configuration. Store them under
`data/measurements/` with a structured JSON registry record and only apply them
when robot serial, fixture definition, deck slot, pipette setup, and generated
artifact checksums match.

Opentrons offset guidance is scoped to the same labware-and-slot combination on
the same robot. Aevum adds a stricter layer: offset reuse also requires matching
generated artifact checksums, measured fixture QC, and target-class
verification.

## Custom Labware

The generated fixture labware definition is built from the same parameters as
the CAD model:

```text
src/aevum_cad/labware.py
outputs/labware/aevum_p300_poc_fixture.json
```

The bridge should load the generated definition directly and should verify that
the definition dimensions match the CAD parameters before any robot run. The
fixture top Z, well centers, and offset target columns are safety-relevant.

Bench verification on 2026-05-02 showed that maintenance runs do not know the
generated Aevum fixture definition by reference at startup. The bridge must post
the generated labware JSON to
`/maintenance_runs/{runId}/labware_definitions` before sending `loadLabware`.
The corrected definition URI is `aevum/aevum_p300_poc_fixture/1`.

## Sources

- Opentrons HTTP API reference: https://docs.opentrons.com/http/api_reference.html
- Opentrons Python API overview: https://docs.opentrons.com/python-api/
- Opentrons Python API advanced control: https://docs.opentrons.com/python-api/advanced-control/
- Opentrons Jupyter advanced control: https://docs.opentrons.com/python-api/advanced-control/jupyter/
- Opentrons command-line control: https://docs.opentrons.com/python-api/advanced-control/command-line/
- OT-2 labware offsets: https://docs.opentrons.com/ot-2/calibration/labware-offsets/
- OT-2 system specifications: https://docs.opentrons.com/ot-2/system-description/specs/
- OT-2 App built-in camera: https://docs.opentrons.com/ot-2/opentrons-app/features-summary/
- Python Protocol API `capture_image`: https://docs.opentrons.com/v2/new_protocol_api.html
