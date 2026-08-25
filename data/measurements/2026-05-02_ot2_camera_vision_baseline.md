# OT-2 Camera Vision Baseline

Date: 2026-05-02
Robot display name: aevum
Robot URL resolved by bridge: `http://rough-morning.local:31950`
Command path: non-motion camera still plus local image analysis

## Goal

Establish the first agent-readable camera observation record for the OT-2 deck
without authorizing any robot motion.

## Command

```text
uv run aevum-ot2 camera-observe --service-name aevum --discovery-timeout 10 --timeout 20 --purpose deck-baseline
```

The CLI accepts either hyphenated or underscored purpose names; the stored schema
uses underscores.

## Capture

```text
endpoint: POST /camera/picture
image: data/measurements/images/aevum_camera_picture_2026-05-02_124832.jpg
content_type: image/jpg
bytes_written: 31125
resolution: 640x480
```

No motion commands were sent.

## Analysis

```text
purpose: deck_baseline
mean_luma: 142.927
luma_stddev: 55.457
edge_mean: 12.75
evidence_ok: true
motion_gate: false
summary: image recorded; vision gate does not authorize motion
```

Passing checks:

- minimum resolution,
- underexposure guard,
- overexposure guard,
- contrast guard,
- coarse structure warning threshold.

Deliberate blocker:

- `motion_authorization`: this first-pass analysis is evidence-only.

## Interpretation

The OT-2 camera provides usable deck evidence under current bench lighting. This
does not validate fixture presence, fixture orientation, tip localization, or any
motion envelope. The next camera step after the print finishes is an installed
fixture observation with purpose `fixture-presence`; that result should remain
motion-blocked until a calibrated fixture/fiducial detector exists.
