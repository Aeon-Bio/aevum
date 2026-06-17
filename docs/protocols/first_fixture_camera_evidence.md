# First Fixture Camera Evidence Procedure

## Purpose

Capture the first installed-fixture OT-2 camera evidence after print QC and
before any registration or dry-motion work. This procedure records
fixture-presence evidence for commissioning, fixture QC, and later detector
calibration. It does not authorize robot motion.

## Preconditions

1. The printed `aevum_p300_poc_fixture` has completed post-print cleanup.
2. Print QC measurements and visible defects have been recorded against
   `docs/engineering/fixture_qc_acceptance.md`.
3. The fixture is seated in the intended OT-2 deck slot, with no tip, liquid, or
   commanded robot motion required for this procedure.
4. The bridge can resolve the robot service name or has `AEVUM_OT2_ROBOT_URL`
   set for the target robot.
5. Robot identity, fixture slot, fixture load name, and operator/agent notes are
   recorded in the measurement session file.

## Capture

Use the non-motion camera path:

```text
uv run aevum-ot2 camera-observe --service-name aevum --purpose fixture-presence
```

If the service name is not `aevum`, pass the correct `--service-name` or set
`AEVUM_OT2_ROBOT_URL`. To make the evidence filename session-specific:

```text
uv run aevum-ot2 camera-observe --service-name aevum --purpose fixture-presence --filename YYYY-MM-DD_first_fixture_fixture_presence.jpg
```

For an image captured by another approved no-motion path, run the same analysis
explicitly:

```text
uv run aevum-ot2 camera-analyze data/measurements/images/<image>.jpg --purpose fixture-presence
```

## Evidence

Store the session note under:

```text
data/measurements/YYYY-MM-DD_first_fixture_camera_evidence.md
```

Camera captures are written under:

```text
data/measurements/images/
```

Default capture filenames use:

```text
aevum_camera_picture_YYYY-MM-DD_HHMMSS.jpg
```

The capture and `purpose=fixture-presence` analysis append evidence events to:

```text
data/measurements/ot2_evidence_index.json
```

Record the image path, analysis payload, robot URL or service name, fixture slot,
fixture load name, print-QC record path, and any manual commissioning notes in
the session file.

## Manual Commissioning Inspection

Inspect the image and the physical setup for:

- fixture visible in the expected deck region and slot,
- gross orientation correct for the generated labware definition,
- base seated flat with no rocking, lifted corner, or deck interference,
- guide holes and access geometry open,
- no support debris, stringing, or deformation in guide/access features,
- mock wells visibly intact at planned test locations,
- lighting, focus, and contrast sufficient for later detector labeling,
- any occlusion from pipettes, tips, cables, hands, tools, or deck clutter.

If the camera image is ambiguous, repeat capture after correcting lighting or
setup. Keep failed or ambiguous captures as evidence; do not delete them from
the evidence index.

## Expected Gate Result

For the current vision scaffold, fixture-presence analysis may report
`evidence_ok: true`, but it must report:

```text
motion_gate: false
```

The expected blocker is `validated_fixture_detector`: fixture/fiducial detection
has not yet been calibrated from installed-fixture evidence. Any
`motion_gate: true` result from this procedure is unexpected and must be treated
as a bridge defect until reviewed.

## Downstream Use

Use this evidence to decide whether the printed fixture can continue through
fixture QC and registration preparation. The image and manual labels become
training/calibration material for fixture-presence and fiducial detectors.

Later detector calibration may promote fixture-presence checks from
commissioning evidence to machine gates. That promotion requires repeated
installed-fixture evidence, target-specific thresholds, and documented bridge
changes. This procedure alone never promotes a fixture, offset, target class, or
motion plan.

## Non-Authorization

This is an evidence-only procedure. It does not home the robot, start a motion
run, register an offset, verify a target class, or permit any dry or wet motion.
Robot motion remains blocked until the registration procedure, fixture QC gates,
and active evidence mode explicitly authorize the specific next move.
