# Readiness Contract

## Purpose

This page defines the boundary between no-motion bridge sessions,
commissioning records, and the read-only readiness join.

`sessions.py` persists live no-motion session state. `records.py` persists
fixture QC and target-class readiness records. `readiness.py` joins both data
sources and returns a local planning result. It does not authorize motion.

## Components

```text
src/aevum_ot2/core/sessions.py
  records robot URL, robot serial, server version, maintenance run ID,
  fixture identity, uploaded definition URI, loaded labware ID, slot, lock state

src/aevum_ot2/core/records.py
  records fixture QC measurements, evidence gates, target-class scaffolds,
  target-class result state, and file handles

src/aevum_ot2/core/readiness.py
  compares session state and commissioning records by handle/path and returns
  blockers
```

Session payloads should reference commissioning records by `RecordHandle` or
path when those links become durable session fields. They should not duplicate
print-QC fields, target-class dependency rules, or target-class result state.

## Record Handles

`RecordHandle` is the stable reference shape:

```json
{
  "record_type": "fixture_qc",
  "path": "data/measurements/2026-05-02_first_fixture_qc.json",
  "record_id": "aevum_p300_poc_fixture:<params_sha12>:<labware_sha12>"
}
```

Target-class handles use:

```json
{
  "record_type": "target_class_verification",
  "path": "data/measurements/target_classes/center_high_z.json",
  "record_id": "center_high_z:<robot_serial>:slot-5:<pose_digest_sha12>:p300_single_gen2:left"
}
```

The record file remains the source of truth. The handle is only an indexable
pointer. If a handle and record contents disagree, the record contents win and
the stale handle must be regenerated.

## Registration Readiness

`evaluate_registration_readiness()` checks:

- session state is `ready_no_motion`,
- session lease has not expired,
- session still has a maintenance-run ID, definition URI, and loaded labware ID,
- fixture identity dimensions match generated labware,
- fixture QC record passes registration readiness,
- fixture load name and artifact checksums match the session,
- if the session is pose-scoped, the persisted fixture pose loads, committed
  pose-orientation/upright claims satisfy `pose_match_gate`, and fixture QC plus
  target records carry the same `pose_digest_sha256`,
- pose claims, evidence handles, and pose evidence artifacts are not older than
  the active session authority timestamp and are not being evaluated after the
  session lease expires,
- pose-unknown sessions can only pair with pose-unknown records; a record that
  carries a pose digest against a pose-unknown session is inspect-only and
  readiness-blocked,
- target-class records match session slot, robot, fixture, and checksums,
- all declared target classes have a record, even if the result is still
  `blocked`.

It returns:

```json
{
  "registration_ready": true,
  "low_z_ready": false,
  "motion_allowed": false,
  "reasons": []
}
```

`low_z_ready` and `motion_allowed` are deliberately false in this no-motion
contract. Low-Z and wet readiness require later motion-commissioning evidence.

The current `readiness-check` command accepts an active local session ID and
record paths. It reads local SQLite session state and local JSON records. It does
not contact the robot.

The current target scaffold command is:

```bash
uv run aevum-ot2 target-scaffold SESSION_ID \
  --output-dir data/measurements/target_classes/<session_id> \
  --pipette-name p300_single_gen2 \
  --pipette-mount left
```

Use a fresh no-motion session that reflects the live robot pipette state and
fixture slot. The scaffold records start as `blocked`; this is intentional.

The current fixture QC scaffold command is:

```bash
uv run aevum-ot2 fixture-qc-scaffold \
  --session-id SESSION_ID \
  --output data/measurements/fixture_qc/<session_or_date>.json \
  --x-bound-mm 127.76 \
  --y-bound-mm 85.48 \
  --z-bound-mm 91.0 \
  --camera-capture-indexed \
  --fixture-visible \
  --vision-evidence-ok \
  --base-seated \
  --guide-holes-open \
  --support-debris-absent \
  --mock-wells-undeformed \
  --warping-lift-absent
```

The command defaults every measurement and evidence gate to blocking. A passing
record must use real post-print measurements and explicit inspection results.
For pose-scoped sessions, pass `--session-id` so the fixture identity and pose
digest come from the active session. Offline scaffolding may use
`--pose-digest-sha256`, but it must match the session digest before readiness
can pass.

Capture the pose image through the active session first, either through the
daemon `capture_evidence` operation or the CLI session path:

```bash
uv run aevum-ot2 camera-capture \
  --session-id SESSION_ID \
  --service-name aevum \
  --filename <slot5_rot180_image>.jpg \
  --output data/measurements/images/<slot5_rot180_image>.capture.json
```

The current pose evidence commit command is:

```bash
uv run aevum-ot2 pose-evidence-commit SESSION_ID \
  data/measurements/images/<slot5_rot180_image>.jpg \
  --observed-orientation rot180 \
  --fixture-upright \
  --inspection-note "<operator inspection summary>" \
  --vision-result-path data/measurements/images/<slot5_rot180_image>.vision.json \
  --quality usable
```

It reads the persisted session pose, writes a schema-v1 pose evidence artifact,
and commits pose-orientation/upright claims through the session evidence
transaction path. It does not contact the robot. `usable` quality is only valid
when the artifact is backed by a matching session-indexed camera capture event,
the captured image checksum, optional vision checksum, a capture timestamp
inside the active session authority window, the same session robot URL, and a
non-empty inspection note.

## CLI Use

The current local read-only check is:

```bash
uv run aevum-ot2 readiness-check SESSION_ID \
  --fixture-qc-record data/measurements/<fixture_qc>.json \
  --target-class-dir data/measurements/target_classes/<session_id>
```

For compact agent context, prefer `--target-class-dir` with the scoped session
directory. `--target-class-record` remains available for explicit single-record
inputs and can be repeated. The command exits nonzero when registration
readiness is false. It does not contact the robot or issue robot commands.

After registration readiness passes, build the fixture safety profile from the
same active session, pose-scoped QC record, and committed pose claims:

```bash
uv run aevum-ot2 safety-profile-build SESSION_ID \
  --fixture-qc-record data/measurements/fixture_qc/<session_id>_fixture_qc.json \
  --output data/measurements/sessions/<session_id>/fixture_safety_profile.json
```

This persists the measured-bound safety envelope, including conservative bounds,
high-Z clearance, boundary-target handling, target-policy digest, and
`safety_profile_sha256`. A passing safety profile is still an input artifact, not
a command to move.

Target classes are promoted only from artifact-backed target evidence:

```bash
uv run aevum-ot2 target-evidence-commit SESSION_ID \
  data/measurements/target_classes/<session_id>/center_high_z.json \
  data/measurements/images/<center_high_z_image>.jpg \
  --inspection-note "<target evidence summary>" \
  --vision-result-path data/measurements/images/<center_high_z_image>.vision.json \
  --quality usable
```

The command writes a target evidence artifact, derives
`target_class_verified:<target_class>`, checks target authority, commits the
evidence transaction, and writes the promoted target-class record. It fails
before committing if the target evidence, pose authority, or target record scope
does not pass. It does not contact the robot.

Validate candidate motion plans locally before any physical backend is enabled:

```bash
uv run aevum-ot2 plan-validate SESSION_ID data/measurements/plans/<plan>.json \
  --fixture-qc-record data/measurements/fixture_qc/<session_id>_fixture_qc.json \
  --target-class-dir data/measurements/target_classes/<session_id> \
  --safety-profile data/measurements/sessions/<session_id>/fixture_safety_profile.json \
  --recovery-disposition not_started \
  --motion-enabled
```

`--motion-enabled` on `plan-validate` only tests the motion-boundary gates. The
command does not execute the plan or contact the robot, and motion-step
validation returns plan-level `allowed=false` and `motion_allowed=false` unless a
schema-valid `MotionApproval` binds that exact plan step to a motion-armed
session and lock.
A `move_high_z` plan must still have target-class authority for its target; a
blocked scaffold record is enough for registration readiness, but not enough
for motion validation.

## Non-Authorization

Registration readiness means the next registration plan can be prepared. It
does not mean:

- home the robot,
- move to high Z,
- move to low Z,
- pipette liquid,
- promote a target class,
- reuse an offset.

Motion commissioning remains blocked until a future workflow explicitly joins
session state, offset registry state, target-class records, generic evidence
packets, derived claims, gate results, and recovery state.

## Implementation Rules

- `BridgeSession` may store record handles in the future, but should not embed
  full fixture QC or target-class record payloads.
- Record JSON helpers should stay in `records.py`; readiness joins should stay
  in `readiness.py`; live robot lifecycle should stay in `sessions.py` and
  maintenance helpers.
- CLI commands may expose all three components, but the command name and help
  text must make clear whether it is local-only, no-motion-live, or
  motion-capable.
- Any future motion-capable readiness result needs a new schema field or model.
  It must not silently change the meaning of this no-motion
  `ReadinessResult.motion_allowed=false` contract.
