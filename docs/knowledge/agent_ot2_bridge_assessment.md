# Agent OT-2 Bridge Assessment

## Context

This assessment records the useful findings from a Brutalist architecture review
of the agent OT-2 bridge documentation on 2026-05-02. The review was adversarial,
so its claims were treated as prompts to verify rather than as authoritative
verdicts.

## Validated Findings

### Direct-Control Bypass

The current repository still contains `opentrons/test_p300_poc.py`, a direct
Python Protocol API dry-motion scaffold. That file is useful as a protocol
reference, but it bypasses the future bridge lock, offset registry, validation,
and evidence path if executed directly.

Decision: direct protocol files are debug/reference scaffolds until generated or
executed by the bridge with explicit offsets and evidence IDs.

Follow-up: `opentrons/test_p300_poc.py` now fails closed by default unless a
manual debug flag and registered fixture offset are set explicitly.

### Lock Design Was Underspecified

The phrase "single writer" is not enough. A safe bridge needs ownership, lease,
expiry, active run ID, command ID, and crash-recovery semantics.

Decision: the bridge design now requires a persistent lock record and
fail-closed recovery when local state and robot state disagree.

### Movement Retry Semantics Were Missing

A network timeout after a movement `POST` is ambiguous. Retrying a physical move
can duplicate motion. Assuming it failed can desynchronize bridge state from the
robot.

Decision: movement commands must use deterministic keys where supported,
reconcile against command history, and fail closed if reconciliation is not
possible.

### Offset Storage Needed Machine Structure

Markdown measurement notes are not sufficient input for safety gating.

Decision: offsets need a structured registry record with robot identity, fixture
identity, generated artifact checksums, deck slot, pipette setup, offset vector,
dry verification state, and evidence links.

### The Labware Definition Is Not A Collision Model

The generated custom labware definition gives wells and dimensions. It does not
encode every printed rail, post, guide plate, or future optical forbidden zone.

Decision: fixture safety envelopes must be generated from fixture parameters/CAD
metadata, not only from labware JSON.

### The Stop Path Needed Operational Detail

Maintenance-run queues are not a reliable pause mechanism after a command has
been accepted.

Decision: first fixture registration requires camera evidence or supervised
commissioning evidence, small segments, high-Z first moves, no automatic motion
retry, and explicit recovery after stops or ambiguous command state.

### Physical Print QC Was Missing From The Bridge Gate

The bridge cannot infer blocked guide holes, warping, or support damage from
generated files.

Decision: fixture checks include measured print QC before registration.

## Downgraded Or Contextual Findings

The review criticized HTTP as unsuitable for real-time jogging. That is correct
if the bridge tried to behave like a servo loop. The intended first bridge should
not do that. It should send small, deliberate, camera-observed commands and wait
for reconciliation before continuing. Human observation is a commissioning
fallback, not the target control path.

The review also criticized having both maintenance and protocol modes. That is a
real implementation risk, but not a design blocker. The revised docs narrow the
first implementation to maintenance mode and leave protocol mode as a future
target.

## Resulting Documentation Changes

- Added bypass-surface guidance.
- Added concrete lock semantics.
- Added command-key reconciliation/retry policy.
- Added structured offset registry requirements.
- Added physical fixture QC gate.
- Added stop and recovery requirements.
- Clarified that production motion should use an explicitly tested
  `Opentrons-Version`, not `*`.

## Second Assessment: Core/Session-First Revision

After revising the architecture to make MCP/CLI/HTTP adapters thin clients over
a stateful bridge core, a second adversarial review identified additional valid
risks.

### Validated Findings

- A local lock is not authoritative over the entire robot server. It only
  enforces single-writer behavior among cooperating bridge clients unless the
  lab network routes all robot-server writes through the bridge.
- The system needs an explicit observation channel for the first fixture.
  Recovery, low-Z registration, and wet operations cannot proceed from command
  history alone.
- Live motion needs one local daemon. Multiple adapters cannot safely share an
  in-memory session state machine by importing the same library.
- Lease expiry should not automatically transfer control while robot state is
  active or ambiguous.
- Opentrons command `key` support should be treated as correlation until live
  testing proves stronger idempotency semantics.
- Live no-motion testing on 2026-05-02 showed duplicate keys are accepted for
  maintenance-run `comment` commands, so keys are not an idempotency guard.
- Measured print QC must feed the runtime safety envelope, not just pass/fail
  the fixture at setup.
- A single `dry_verified` boolean is too coarse. Verification must be tied to
  target classes.
- Evidence writes need a structured index and should fail closed for physical
  motion if local storage is unavailable.

### Resulting Changes

- Added control-authority wording that downgrades single-writer claims unless
  network-level gating exists.
- Reframed first OT-2 bridge work as supervised commissioning toward unattended
  autonomy, with the OT-2 camera as the primary observation channel.
- Chose a single local daemon for live motion, with adapters as clients.
- Changed lock guidance to SQLite and stale-session recovery.
- Renamed idempotency guidance to command-key reconciliation.
- Added measured-QC runtime envelope rules and a fixture QC acceptance page.
- Replaced `dry_verified` with target-class verification in docs/templates.
- Added recovery and API-spike protocol docs.

## Camera Realignment

The OT-2 has a built-in camera. Earlier assessment language overfit to human
observation because the observation channel had not been named. The revised
architecture targets unattended autonomy and treats human confirmation as a
temporary commissioning fallback while camera capture, image analysis, and
confidence gates are validated.

Resulting changes:

- Added `docs/knowledge/ot2_camera_autonomy.md`.
- Added camera checks to the first implementation scope.
- Added `vision.py` to the proposed package shape.
- Changed registration and recovery docs to prefer camera evidence.
- Updated the API spike to test image capture and retrieval.
