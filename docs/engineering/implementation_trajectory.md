# Implementation Trajectory

> Historical design record. Generic robot-control implementation now belongs to
> [`Aeon-Bio/ot2-harness`](https://github.com/Aeon-Bio/ot2-harness); Aevum owns only its
> consumer fixture/profile, CAD, physical protocols, and evidence. Names below describe
> the pre-extraction implementation and are not current package paths.

## Direction

Aevum should be implemented as a stateful OT-2 bridge core with thin adapters.
The package should not optimize around the CLI, MCP, or ad hoc scripts. Those
are access surfaces over the same core state machine.

The current trajectory is:

```text
generated artifacts
  -> no-motion robot session
  -> evidence packets, claims, and structured commissioning records
  -> read-only readiness join
  -> context pack and plan validation
  -> local live-control daemon
  -> MCP/HTTP/CLI adapters over daemon operations
  -> first high-Z motion commissioning
  -> dry target-class promotion
  -> wet workflow
```

## Current Implementation

The repo currently has these pieces:

- `aevum_cad`: CAD, STEP/STL/3MF, and labware generation from shared params.
- `aevum_ot2.core.client`: narrow robot-server HTTP client.
- `aevum_ot2.core.discovery`: explicit/env/mDNS robot URL resolution.
- `aevum_ot2.core.camera`: direct still-image capture from `/camera/picture` as
  one evidence source, with captured-at time, image checksum, and optional
  session evidence-index stamping.
- `aevum_ot2.core.vision`: camera evidence-quality analysis that never
  authorizes motion.
- `aevum_ot2.core.maintenance`: no-motion maintenance-run probes and helpers.
- `aevum_ot2.core.lock`: local SQLite single-writer lock state with atomic
  compare-and-set acquisition for new bridge ownership.
- `aevum_ot2.core.sessions`: no-motion session persistence, state-root-scoped
  session artifacts, operator-proposed fixture orientation at session start,
  durable fixture-pose JSON persistence, run-local oriented labware upload/load
  with journaled `loadLabware` dispatch, cleanup verification by post-delete
  lookup, persisted pipette identity snapshots, deterministic close/recovery
  state, and schema-v1 loading for SQLite session payload JSON.
- `aevum_ot2.core.pose`: v1 fixture pose primitives for exactly `canonical` and
  `rot180`, stable pose digests, durable pose JSON write/load helpers,
  frame-tagged canonical/installed transforms, distinct oriented labware
  compilation with unsupported-coordinate fail-fast checks,
  evidence-handle-bound pose-orientation/upright claim gating that revalidates
  the referenced pose artifact, nested image/vision checksums, and camera
  capture timestamp/robot URL against the expected session evidence index,
  rejects claims outside the session authority window, and pose-scope checks
  for safety, target, offset, and home-clearance inputs.
- `aevum_ot2.core.pose_evidence`: evidence-packet-to-claim derivation for
  fixture pose orientation and fixture upright state, requiring checksummed
  artifact-backed usable packets, schema-v1 `FixturePoseEvidenceArtifact`
  summaries over camera/vision/inspection artifacts, session-scoped
  transaction-backed commit helpers for those claims, claim-load revalidation
  of external artifact/image/vision checksums, session-scoped indexed
  camera-capture provenance with non-empty session ID and session robot URL,
  plus pose claim-to-packet linkage, and a CLI commit path for post-capture
  pose evidence. HTTP plan routes reject raw pose-claim JSON; pose authority
  must enter through committed session evidence.
- `aevum_ot2.core.records`: fixture QC and target-class JSON records plus
  scaffold helpers for blocked/no-motion commissioning records. Record loaders
  now reject unknown durable schema versions, target-class authority requires
  checksum-matched usable evidence handles plus
  `target_class_verified:<target_class>` claims, pose-scoped sessions require a
  pose object before target authority, duplicate target records block
  validation, and old target camera/vision/free-text aliases are
  compatibility-only and not emitted by writers.
- `aevum_ot2.core.evidence`: serialized legacy evidence-event indexes plus
  crash-recoverable evidence transactions with packet/claim files, checksums,
  committed manifests, fail-closed claim loading, and recovery scans for
  orphaned, partial, tampered, path-escaped, root-escaped, index-mismatched,
  artifact-mismatched, packet-unlinked, session-inconsistent, or
  unknown-version transactions.
- `aevum_ot2.core.schema`: shared durable JSON load-boundary checks for current
  schema version enforcement.
- `aevum_ot2.core.targets`: explicit target policy and geometry table for every
  declared target class, including Z tier, predecessors, boundary/mat-patch
  flags, first-pass eligibility, and future required claims.
- `aevum_ot2.core.safety`: pure fixture safety-profile input builder from
  generated artifact identity plus measured fixture QC records, scoped QC
  claims, and optional pose authority; it computes `safety_profile_sha256` and
  blocks low-Z, wet, and home-clearance inputs when measurements, pose scope,
  claim scope, or profile checksum integrity are missing. It also owns the
  home-clearance input gate over safety profile, pose authority, session state,
  and explicit recovery disposition. Safety profiles now have schema-v1
  load/write helpers for durable artifacts.
- `aevum_ot2.core.registry`: offset registry helpers plus promoted-offset
  authority gate; proposed offsets, stale safety-profile checksums, target
  record/session mismatches, and robot/slot/pipette/fixture/pose scope
  mismatches fail closed.
- `aevum_ot2.core.readiness`: local read-only readiness join across session,
  installed pose, committed pose claims, fixture QC, and target record handles.
- `aevum_ot2.core.context`: compact local session context packs with allowed
  next operations and blocked motion operations.
- `aevum_ot2.core.plans`: typed local operation/plan fragments with explicit
  schema-v1 parsing for file and HTTP payloads.
- `aevum_ot2.core.validation`: local plan validation that keeps motion blocked
  unless daemon motion is enabled and explicit motion gate results pass. Motion
  step validation now emits gate results for home-clearance, first high-Z,
  low-Z dry, wet, and promoted offset authority instead of relying only on
  prose reasons.
- `aevum_ot2.core.execution`: typed daemon execution results for approved
  next-step attempts; current execution is local/no-motion only and never sends
  motion commands.
- `aevum_ot2.core.revalidation`: execute-time guard over approved motion steps.
  It fails closed on non-ready reloaded session state, stale session or lock
  leases, non-motion lock states, missing live status, incomplete robot/API
  identity, incomplete pipette identity, robot/server/API drift, pipette drift,
  missing gate state, command mismatch, or gate blockers before a future
  physical backend can run.
- `aevum_ot2.core.recovery`: no-motion session recovery against exact
  maintenance run IDs, with incomplete or unsafe command histories left
  blocked.
- `aevum_ot2.server.service`: workflow-level service API over the bridge core,
  including start-session orientation and plan-route pose/claim inputs.
- `aevum_ot2.server.app`: local stdlib HTTP daemon transport for the workflow
  API with typed start-session orientation validation.
- `aevum_ot2.server.client`: thin typed client for the local daemon API with
  parity for orientation, fixture pose, and pose claims.
- `aevum_ot2.core.records.write_target_class_scaffold`: blocked target-class
  record generation from a no-motion session.
- `aevum_ot2.core.target_evidence`: target-class camera/vision/inspection
  artifact to evidence-packet to `target_class_verified:<target_class>` claim
  derivation, transaction commit, and target-record promotion helpers.
- `aevum_ot2.core.motion_approval`: schema-v1 dispatch-boundary approval
  artifacts that bind one motion step to the plan digest, session, robot,
  installed pose digest, safety-profile checksum, expiry window, and required
  motion-armed session/lock state.
- `aevum_ot2.core.motion_commissioning`: SQLite-backed arm/consume transition
  for motion approvals. It re-reads session and lock under `BEGIN IMMEDIATE`,
  enforces one armed approval record per session, revokes expired approvals
  before re-arm, rejects approval windows beyond the current lease, and consumes
  a persisted approval exactly once while atomically creating a pre-dispatch
  dispatch reservation and, when live preparation passes, a prepared command
  journal row.
- `aevum_ot2.core.dispatch_reservation`: durable post-approval reservation
  record. It binds consumed approval scope to session/run/step state before any
  physical command POST.
- `aevum_ot2.core.dispatch_preparation`: no-post conversion from approval or
  reservation scope to a prepared command-journal entry after live
  maintenance-run, loaded-labware, labware-offset, and command-history readback.
  Only `home` has a command-body translator; unsupported motion operations fail
  closed before approval consumption.
- `aevum_ot2.core.motion_backend`: explicitly gated prepared-journal dispatcher.
  It repeats live run/history readback immediately before POST, requires the
  fresh preparation to match the consumed preparation, calls the journaled
  command helper, reconciles history, and updates session/lock last-command
  authority only on completed reconciliation; ambiguous or failed dispatch moves
  local state to recovery.
- `aevum_ot2.adapters.cli fixture-qc-scaffold`: local fixture QC record
  creation from measured bounds and explicit evidence gates, with optional
  session/pose-digest binding for pose-scoped readiness.
- `aevum_ot2.adapters.cli safety-profile-build`: persisted measured-bound safety
  profile generation from an active pose-scoped session, committed pose claims,
  and a fixture QC record.
- `aevum_ot2.adapters.cli plan-validate`: local plan-fragment validation,
  including optional motion-boundary gate evaluation without executing robot
  motion; target-class context can be supplied as a scoped directory instead of
  expanding every record path. First high-Z validation now requires
  target-class authority for the selected target, so blocked scaffolds remain
  registration context only.
- `aevum_ot2.adapters.cli target-evidence-commit`: local target-class
  promotion from usable target evidence; it writes the evidence artifact,
  commits deterministic target claims, checks target authority against committed
  evidence plus pose claims, and only then writes the promoted target record.
- `aevum_ot2.adapters.cli`: operator/debug commands for the current core.

This is enough for no-motion commissioning. It is not enough for unattended
motion.

## Next Engineering Work

### 1. Finish The Print-To-Evidence Package

Trigger: the physical fixture is available after printing.

Completed for active no-motion session `reg-20260506-001615-6d1a9607`:

- physical fixture QC JSON from measured bounds `127.35 x 85.01 x 89.71 mm`,
- session-indexed camera capture in slot `5`,
- explicit installed fixture pose for physical `rot180`,
- committed pose-orientation and fixture-upright claims,
- blocked target-class scaffold records for every declared target,
- committed usable target evidence for `center_high_z`,
- promoted `center_high_z` through `target_class_evidence_packet_v1`,
- registration readiness against the active no-motion session,
- measured-bound fixture safety profile,
- validation-only `home` and first `center_high_z` plans at the local
  motion-boundary gate.

Remaining:

- keep or close the active no-motion session depending on whether motion
  commissioning is immediately next,
- add high-Z target command-body translation and final no-post-to-post backend
  gating,
- implement the physical motion backend behind execute-time revalidation and
  the command journal,
- record post-motion high-Z evidence before any low-Z dry target is considered.

Code impact should be small: real measurement record paths, evidence handles,
claim/gate summaries, and tests around readiness failure messages.

### 2. Build The Motion Execution Path In The Daemon

Live motion should go through one local bridge daemon. The daemon owns the
in-memory session state and uses SQLite for recovery after crashes.

The daemon should expose workflow operations, not raw OT-2 endpoints:

- status/context,
- start session,
- validate plan,
- execute approved next step,
- capture evidence,
- record evidence and derived claims,
- evaluate gates,
- abort/recover,
- close session.

The current daemon API exists for no-motion workflows, has an `execute-next`
boundary for local/no-motion operations, rejects unknown plan-fragment schema
versions, and has a typed local daemon client for future adapters. New session
starts now acquire local bridge ownership atomically before any maintenance-run
POST and persist selected-mount pipette identity; legacy maintenance spikes also
abort when an active bridge lock exists. Motion-bound validation now requires a
schema-valid, persisted `MotionApproval` before plan-level `allowed` or
`motion_allowed` can pass. The daemon arm route rejects caller-supplied approval
JSON, requires a pre-arm validation blocked only by missing approval, and
atomically persists `motion_commissioning_armed` session/lock state with one
armed approval record. Execute-time revalidation requires the fixed armed lock
state, fresh session and lock leases, complete session/live robot and pipette
identity, matching last command state, passing gates, persisted approval scope,
and one-shot approval consumption before the backend can be reached. The
daemon validation route also checks approval persistence before reporting
`motion_allowed=true`, so raw approval JSON cannot look authoritative through
the service API. The daemon now prepares a home command-journal entry only after
live maintenance-run/labware/history readback passes, and commits that prepared
entry in the same transaction as approval consumption and reservation creation.
The prepared-`home` backend path is implemented behind a separate flag; the
remaining software slice before target motion is high-Z target translation,
transaction-backed offset authority, physical-event invalidation, and then an
explicitly approved motion backend behind the execution boundary. Plan fragments now use canonical
`capture_evidence` naming, explicit
operation categories, and typed per-operation parameter allowlists; legacy
`capture_observation` input is a read shim only and cannot be emitted by plan
writers. The daemon now requires explicit plan request envelopes, rejects
chunked request bodies, caps body size and JSON nesting depth, and refuses
non-loopback unauthenticated binds unless the operator passes an explicit
remote-bind override. The CLI can remain for no-motion smoke tests and operator
debugging.

### 3. Add Agent Adapters

Only after the core and daemon own validation should MCP or HTTP be added.
Motion-capable MCP must not ship until pose route-parity tests cover its tool
schema and prove it cannot default orientation to canonical.

**Landed 2026-06-18 (OT-7 / OT-8):** `src/aevum_ot2/adapters/mcp.py` is the thin policy
adapter below; it routes through `DaemonClient`, never mints motion approval, and the
route-parity / no-silent-canonical-default ship-gate is `tests/test_route_parity.py`. The
adapter is no-motion today — it exposes none of the live-motion arming surface. **OT-12** added
`core/commissioning.py`, a fail-closed operability layer over the existing daemon (dry-run
default; never auto-arms). **OT-11** reconciled the task graphs: the high-Z command-body
translator, OT-3 physical-event invalidation, and OT-6 post-motion evidence are DONE; the
live-motion backend that POSTs the translated target command (RG14) remains the open, B-gated tail.

The MCP surface should stay small:

```text
ot2_status
ot2_start_session
ot2_get_session_context
ot2_validate_plan
ot2_execute_next
ot2_capture_evidence
ot2_record_evidence
ot2_evaluate_gates
ot2_abort_or_recover
ot2_close_session
```

Do not expose raw coordinates, arbitrary robot-server HTTP, arbitrary Python, or
offset mutation as agent tools.

## Current Blockers

- The printed fixture is installed in slot `5` as physical `rot180`; the active
  evidence set and measured-bound safety profile are usable only while a fresh
  no-motion session authority, pose claims, fixture QC record, and target
  evidence all match the same pose digest.
- The previous physical session authority is stale. Any motion-commissioning
  attempt must rerun or refresh the no-motion session/evidence path before
  arming.
- Motion approval arm/mint/persist/consume is implemented in the daemon. With
  the default backend-disabled service, execution consumes only after live
  readback and home dispatch preparation pass, atomically persists a
  pre-dispatch reservation plus prepared command-journal row, and returns
  `not_implemented` without sending a robot command. A separate
  `motion_backend_enabled` flag can dispatch the prepared `home` command through
  final readback, journaled POST, reconciliation, and session/lock authority
  update. The HTTP daemon requires a local `X-Aevum-Bridge-Token` when that
  backend flag is enabled and refuses remote unauthenticated backend binds.
- Fixture pose/orientation is first-class through core helpers, evidence claim
  derivation, no-motion session lifecycle, readiness/context, HTTP/service/client
  routes, and CLI init. Live execution still cannot use slot-5 `rot180`
  coordinates until pose freshness and labware-offset bounds are rechecked at
  dispatch.
- The live backend path is implemented only for prepared `home` and is disabled
  by default. High-Z, low-Z, wet, and liquid-handling translators remain closed;
  no live command should be sent until a fresh slot-5 session and current
  physical evidence are re-established.

## Stop Conditions

Do not proceed to live motion if any of these are true:

- generated fixture dimensions or checksums do not match the records,
- installed fixture pose is missing, unsupported, or mismatched across session,
  evidence, records, offsets, and planned target coordinates,
- pose orientation/upright claims are missing, stale, or sourced only from
  operator assertion,
- OT-2 labware offsets exceed the safety-profile jog allowance,
- the live robot pipette state differs from the session/record state,
- a local lock is active for another session,
- a previous maintenance run cannot be reconciled,
- required fixture evidence packets or claims are missing,
- target-class scaffold records are incomplete,
- readiness result is not `registration_ready=true`,
- any tool path would bypass the bridge core.

## Near-Term File Shape

Expected additions before first motion:

```text
src/aevum_ot2/adapters/mcp.py      # later, thin workflow adapter
```

Avoid adding these prematurely if the behavior still belongs in existing
modules. The next real implementation belongs behind `execute-next`: add the
first high-Z target command-body translator, physical-event invalidation, and
the final no-post-to-post backend transition. Motion-capable adapters should
wait until those core paths exist behind the daemon.
