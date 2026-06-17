# OT-2 Camera And Autonomy

## Purpose

The OT-2 has a built-in camera. Aevum should treat that camera as the first
machine perception source, not as the whole evidence model and not as permanent
human confirmation.

Official Opentrons documentation describes:

- a built-in 2-megapixel OT-2 camera,
- still images of the deck and working area,
- Python Protocol API `ProtocolContext.capture_image()` in API `v2.27`,
- camera images during Protocol Designer or Python API runs,
- no protocol-run live streaming through the documented App camera path because
  of robot processing and memory limits.

## Autonomy Target

Aevum's target is unattended autonomy for validated workflows.

Use this terminology:

| Mode | Meaning | Aevum Role |
| --- | --- | --- |
| Supervised commissioning | A human may observe or approve while robot/camera gates are being validated | Temporary first-fixture mode |
| Monitored autonomy | The bridge runs from machine evidence, with human intervention available | Intermediate operating mode |
| Unattended autonomy | The bridge runs validated workflows without human approval in the run loop | Target operating mode |

Avoid describing the architecture as human-in-the-loop except when discussing
temporary commissioning gates or unresolved recovery.

## Camera Evidence Role

Camera evidence feeds the generic evidence model described in
`docs/knowledge/evidence_model.md`. The bridge should use camera evidence for:

- fixture presence and slot occupancy,
- gross fixture orientation,
- post-print QC photo record,
- high-Z target approach evidence,
- pipette/tip position relative to printed fiducials where image quality allows,
- before/after snapshots around registration and dry-run target classes,
- unattended run audit records,
- recovery-state snapshots after ambiguous commands.

Camera images are evidence packets, not automatically truth. The bridge needs
derived claims, explicit gates, and confidence thresholds before camera
evidence can replace a supervised commissioning fallback.

## First Vision Gates

The first machine gates should be conservative:

1. Capture deck image with fixture installed.
2. Verify image capture succeeds and file is indexed in evidence.
3. Detect printed fiducials or guide-hole field coarsely.
4. Confirm the fixture appears in the expected deck region.
5. Capture image after high-Z A1 approach.
6. Estimate whether the tip projection is within a conservative region around
   the target.
7. Store confidence, image path, and derived measurements.

Only after repeated successful evidence should camera-derived claims contribute
to target-class promotion without supervised commissioning fallback.

## Current Vision Scaffold

The bridge now has an evidence-only camera analysis path:

```text
uv run aevum-ot2 camera-observe --service-name aevum --purpose deck-baseline
uv run aevum-ot2 camera-analyze data/measurements/images/<image>.jpg --purpose fixture-presence
```

The current analysis records:

- image resolution,
- mean luminance,
- luminance standard deviation,
- coarse edge/structure response,
- evidence-quality checks,
- explicit motion-gate status.

For now, `motion_gate` is always `false`. A good image may have
`evidence_ok: true`, but it does not authorize robot motion. Fixture-presence and
high-Z target purposes add a calibrated-detector blocker until fixture/fiducial
vision is trained from installed-fixture evidence.

## API Caveats

The manual dry-motion scaffold tracks Opentrons API `2.28`, which is the latest
API version documented for OT-2 on robot software `9.0.0`. Camera capture was
introduced in API `2.27`, so any camera-based protocol path requires robot
software that supports at least API `2.27`.

The local robot named `aevum` was checked on 2026-05-02:

```text
robot-server api_version: 9.0.0
maximum_protocol_api_version: 2.28
cameraEnabled: true
direct still endpoint: POST /camera/picture
captured still size: 640x480 JPEG
```

This confirms a non-motion still-image path for deck evidence. It does not yet
validate tip localization or run-associated `captureImage` behavior.

The first local deck-baseline vision run on 2026-05-02 produced usable evidence:

```text
image: data/measurements/images/aevum_camera_picture_2026-05-02_124832.jpg
resolution: 640x480
mean_luma: 142.927
luma_stddev: 55.457
edge_mean: 12.75
evidence_ok: true
motion_gate: false
```

If the installed robot software does not support API `2.28`, either update the
robot software or lower the scaffold to the highest supported API that still
includes `capture_image()`. Do not silently fall back below API `2.27` for
camera autonomy work.

Before live autonomous registration, run the API spike in:

```text
docs/protocols/ot2_bridge_api_spike.md
```

and record:

- whether camera capture is available over HTTP maintenance runs,
- whether a Python Protocol API run with `capture_image()` is required,
- where image files are stored and how the bridge retrieves them,
- supported resolution/zoom/brightness settings,
- whether images include enough detail for fiducial or tip localization.

## Sources

- OT-2 system specifications: https://docs.opentrons.com/ot-2/system-description/specs/
- OT-2 robot components: https://docs.opentrons.com/ot-2/system-description/robot/
- OT-2 App features, built-in camera: https://docs.opentrons.com/ot-2/opentrons-app/features-summary/
- Python Protocol API `capture_image`: https://docs.opentrons.com/v2/new_protocol_api.html
