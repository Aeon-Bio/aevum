# OT-2 API Spike

Date: 2026-05-02
Robot display name: aevum
Robot host used: `rough-morning.local:31950`
Robot serial: `rough-morning`
Robot model: OT-2 Standard
Bridge default discovery target: `aevum._http._tcp.local`

## Goal

Verify the read-only robot-server API surface and non-motion camera capture path
needed for the Aevum OT-2 bridge.

## Discovery

`dns-sd -B _http._tcp local` advertised:

```text
aevum._http._tcp.local
```

`dns-sd -L aevum _http._tcp local` resolved the service to:

```text
rough-morning.local.:31950
robotModel=OT-2 Standard
```

`aevum.local` did not resolve during this session. Use the mDNS service name for
discovery and `rough-morning.local:31950` for direct HTTP until hostname behavior
is changed or wrapped by discovery code.

The bridge now resolves the robot in this order:

1. explicit `--robot` URL,
2. `AEVUM_OT2_ROBOT_URL`,
3. mDNS service instance `aevum._http._tcp.local`.

Bridge discovery command:

```text
uv run aevum-ot2 resolve --service-name aevum --timeout 10
```

Observed:

```text
robot_url: http://rough-morning.local:31950
source: mdns
server: rough-morning.local
addresses: 192.168.0.136, fd0b:ebd5:7933:483c:2ae3:cc34:5efd:799a
properties.robotModel: OT-2 Standard
```

## Health

Read-only endpoint:

```text
GET /health
```

Observed:

```text
name: aevum
robot_model: OT-2 Standard
api_version: 9.0.0
system_version: 2025.02.7-13-gd4ea3613
fw_version: v1.1.0-25e5cea
maximum_protocol_api_version: 2.28
minimum_protocol_api_version: 2.0
robot_serial: rough-morning
systemAvailableMb: 451.65625
imagesDirectorySizeMb: 0.055721282958984375
apiSpec: /openapi.json
```

## Pipettes

Read-only endpoint:

```text
GET /pipettes
```

Observed:

```text
left model: p300_single_v2.1
left name: p300_single_gen2
left id: P3HSV212021022403
right: empty
```

## OpenAPI

Read-only endpoint:

```text
GET /openapi.json
```

Observed:

```text
openapi: 3.1.0
info.version: 9.0.0
path_count: 100
component_schema_count: 966
captureImage command present: yes
```

OpenAPI confirms camera-related endpoints and command schemas including:

```text
POST /camera/picture
POST /camera/capturePreviewImage
POST /runs/{runId}/camera/capturePreviewImage
GET /dataFiles/{runId}/images
GET /dataFiles/{runId}/images/download
commandType: captureImage
```

## Camera

Read-only/status endpoint:

```text
GET /camera
```

Observed:

```json
{
  "cameraEnabled": true,
  "liveStreamEnabled": false,
  "errorRecoveryCameraEnabled": false
}
```

Live stream settings on OT-2:

```text
GET /camera/stream/settings
```

Observed:

```json
{
  "message": "Opentrons Live Stream service is not available on OT-2.",
  "errorCode": "4000"
}
```

Non-motion still capture endpoint:

```text
POST /camera/picture
```

Captured image:

```text
data/measurements/images/aevum_camera_picture_2026-05-02_1205_cli.jpg
```

Observed file:

```text
JPEG image data, 640x480, 28938 bytes
```

The image clearly shows the OT-2 deck and is suitable for initial deck/fixture
presence evidence. It is not yet validated for pipette-tip localization.

## Aevum Artifact Identity

Current generated fixture identity:

```text
load_name: aevum_p300_poc_fixture
namespace: aevum
version: 1
params_sha256: 8b1387a9da8f34801691e7f5fa0a2a27d39c8c1393cf79a2c3311209bc47bbb2
labware_definition_sha256: 784e63bdd8d6b6fdb37c9df0d95111edbc1f70acd83026e0c4cdec4132836bc3
dimensions_match: true
nominal/labware dimensions: 127.76 x 85.48 x 91.0 mm
```

Later no-motion labware upload testing found that this initial labware JSON used
`metadata.displayVolumeUnits: uL`, which robot-server rejected. The generator was
corrected to emit `\u00b5L`; the current generated labware SHA is:

```text
4bc347130fa1018877fdc95ce2ea9889532e031e100af5679251f751b4eb5e23
```

## Evidence

Structured evidence index:

```text
data/measurements/ot2_evidence_index.json
```

Camera image directory:

```text
data/measurements/images/
```

## Conclusions

- Robot-server API is reachable at `rough-morning.local:31950`.
- Robot is named `aevum`, but hostname is still `rough-morning.local`.
- Max Protocol API is `2.28`, matching the current scaffold.
- P300 Single Gen2 is attached on the left mount.
- `/openapi.json` is reachable and includes camera capture command schemas.
- `/camera/picture` provides a direct non-motion still-image path.
- OT-2 live stream is not available through `/camera/stream/settings`.
- Camera stills can be captured into local evidence without creating a run.
- First-pass local vision analysis can mark deck camera images as usable
  evidence while keeping `motion_gate: false`.

## Remaining Spike Items

- Confirm `captureImage` behavior inside runs and maintenance runs.
- Confirm `GET /dataFiles/{runId}/images` and download behavior after run-based
  capture.
- Confirm command `key` semantics for maintenance-run commands beyond the
  no-motion comment-command probe.
- Confirm named labware target command behavior after successful run-local
  custom labware upload.
- Confirm camera image quality with the printed fixture installed.
- Calibrate fixture/fiducial detection before any camera result can authorize
  live motion.

Follow-up no-motion lifecycle results are recorded in:

```text
data/measurements/2026-05-02_ot2_maintenance_nomotion.md
data/measurements/2026-05-02_ot2_comment_key_nomotion.md
data/measurements/2026-05-02_ot2_labware_definition_nomotion.md
```
