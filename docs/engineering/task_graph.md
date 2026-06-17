# Aevum OT-2 Task Graph

## Scope

This graph is the package-owned path from the first printed P300 PoC fixture to
validated OT-2 commissioning. It is an engineering dependency graph, not an
agent ownership map.

Detailed cleanup work for abstractions that are drifting is tracked in
`docs/engineering/divergence_task_graph.md`.

The active hardware-CAD revision loop for the one-row coupon is tracked in
`docs/engineering/row_coupon_revision_hypergraph.md`. That file is the
do-review-context hypergraph for CadQuery edits, generated artifacts, viewer
state, tests, and knowledge-base updates.

The latest row-coupon cycle outcomes and next physical review tasks are tracked
in `docs/engineering/row_coupon_cycle_log.md`.

The seven-branch realization structure that ties row-coupon gates, observer
CAD/protocols, SMIS, integration, OT-2 control, and physical measurements is
tracked in `docs/engineering/realization_hypergraph.md`.

The active continuation policy is the resolution-gated `RG*` graph in
`docs/engineering/divergence_task_graph.md`. Each software node advances by its
own resolved review artifact: focused tests, full tests, lint, Brutalist
review, graph patch, and no new unhandled blockers. Chat approval is not an
input for local software continuation.

No node in the current graph authorizes robot motion by itself. Motion remains
blocked until the no-motion evidence packets, derived claims, gate results,
active session state, structured records, plan validation, and recovery
behavior all agree.

## Current Facts

As of 2026-05-06:

- the generated fixture CAD/labware dimensions match params:
  `127.76 x 85.48 x 91.0 mm`,
- corrected labware definition SHA256 is
  `c45f53aef70eb77fc402134f62f058bbbadc8793a39657e9e5fb4f9998674294`,
- robot service `aevum` is reachable at `http://192.168.109.136:31950`,
- robot-server API is `9.0.0`; max protocol API is `2.28`,
- live pipettes observed: left `p300_single_gen2`, right `p20_single_gen2`,
- direct camera capture works as one evidence source; live stream is
  unavailable on this OT-2,
- maintenance runs can be created and deleted without motion,
- run-local custom labware upload is required before `loadLabware`,
- `session-init-nomotion` and `session-close-nomotion` passed a live no-motion
  smoke and left the local lock closed,
- `records.py` persists fixture QC and target-class JSON records,
- `readiness.py` joins an active no-motion session with record handles and keeps
  `motion_allowed=false`,
- `context.py` builds compact local session context packs with allowed next ops
  and blocked motion ops,
- `plans.py` and `validation.py` provide local typed plan validation; motion
  remains blocked unless a future daemon explicitly enables it and evidence
  gates pass,
- `pose.py` provides core v1 pose primitives, stable pose digests, `rot180`
  oriented labware compilation, frame-tagged transforms, and `pose_match_gate`
  wiring for supplied pose-scoped safety, target, offset, home, and plan inputs,
- no-motion session init can persist a state-root-scoped `FixturePose`, upload
  the matching oriented labware definition, load that oriented identity into
  slot `5`, and carry pose metadata through CLI, daemon service, HTTP, daemon
  client, and context routes,
- `pose_evidence.py` derives usable pose-orientation and fixture-upright claims
  only from checksummed artifact-backed evidence packets scoped to the active
  session, and readiness joins those claims through `pose_match_gate`,
- `execution.py` and daemon `execute-next` define a typed execution result
  boundary; current execution is limited to local/no-motion operations and
  always reports `motion_commands_sent=false`,
- `recovery.py` reconciles stale or failed no-motion sessions against their
  exact maintenance run ID and leaves `recovery_required` on unsafe or ambiguous
  command history,
- `server.service` and `server.app` define the local daemon workflow API for
  health, sessions, context, validation, and no-motion lifecycle operations,
- `server.client` provides a thin typed local daemon client for future MCP/CLI
  adapters,
- `fixture-qc-scaffold` writes a fixture QC record from measured bounds and
  explicit evidence gates; missing measurements or unchecked gates remain
  blocking. For pose-scoped sessions, it can bind the record to the session
  fixture identity and pose digest,
- `target-scaffold` writes one blocked target-class record per declared target
  class from a local no-motion session,
- `target_evidence.py` can turn target camera/vision/inspection artifacts into
  target-class evidence packets, derive deterministic
  `target_class_verified:<target_class>` claims, commit them through the
  evidence transaction store, and promote a target record only when the approved
  target evidence method is usable and committed,
- attached target vision results must parse as `VisionAnalysisResult`, target
  `high_z_target`, match the artifact image path, and have `evidence_ok=true`;
  otherwise packetization fails closed,
- active session `reg-20260506-001615-6d1a9607` loaded the `rot180` oriented
  fixture definition in slot `5` with no motion commands. Its session-indexed
  camera capture, pose evidence, fixture QC record, measured-bound safety
  profile, and `center_high_z` target evidence all share pose digest
  `b86a40914b4364b4456204ee35e8b768d73b169bfcf8f81e953d64db2df8adf6`,
- measured full assembly bounds are `127.35 x 85.01 x 89.71 mm`; the safety
  profile uses conservative bounds `127.76 x 85.48 x 91.0 mm`,
- `readiness-check` returns `registration_ready=true`, `low_z_ready=false`, and
  `motion_allowed=false` for the current slot `5` / `rot180` evidence set,
- validation-only `home` and first `center_high_z` plan fragments pass local
  motion-boundary gates when motion validation is enabled, but
  `motion_allowed` remains false until the daemon atomically mints and persists
  a `MotionApproval` bound to the exact plan, session, safety profile, and armed
  session/lock state. The daemon now has that arm/consume transaction, and the
  default backend-disabled path consumes the approval once only after live
  readback and home dispatch preparation pass, persists a pre-dispatch
  reservation plus a prepared command-journal row, and then returns
  `not_implemented`; the separately gated motion backend can now dispatch only
  that prepared `home` command after one more fresh readback/reconciliation
  cycle. No robot motion has been dispatched from those plan files. No low-Z or
  wet target is authorized.

Physical post-print QC is complete for the current printed assembly
(`127.35 x 85.01 x 89.71 mm`) and the measured-bound safety profile exists.
Motion is additionally blocked on fresh session authority, target-class
promotion evidence, future MCP parity, live labware-offset bounds, and
execute-time pose freshness because the usable camera installation is `rot180`.

## Graph

```text
G0 generated artifact identity
  -> G1 CAD/STL/STEP/3MF generated from params
  -> G2 labware JSON generated from same params
  -> G3 fixture-check passes dimensions and checksums

L0 fixture label plan
  -> L1 geometry marks encode +X/+Y orientation, A1/keying, offsets, fiducials, QC features, and Z references
  -> L2 functional CAD parts use coarse integrated labels, not tiny text
  -> L3 slicer preview confirms geometry marks do not block wells, locator seats, or guide holes
  -> L4 post-print inspection confirms geometry marks and integrated labels match measurement records

B0 boundary and service-routing stance
  -> B1 wet/incubator services are assigned to a future removable chamber/lid module
  -> B2 dry optical services are assigned to a future separate optical-bay module
  -> B3 first PoC remains passive: no active wires, tubes, heaters, sensors, or sidewall enclosure
  -> B4 slicer/inspection confirms the separate plate cap leaves the optical-bay envelope open

MP0 multi-plate observer architecture
  -> MP1 plate tile exposes one-slot OT-2 datum and local plate-support datum
  -> MP2 tile-to-tile bridge/key features preserve contiguous standard-plate adjacency
  -> MP3 shared dry rectilinear observation bay defines rail, aperture, and keepout conventions
  -> MP4 moving sensor-suite module can visit every tile without tile side protrusions
  -> MP5 each four-tile row exposes shared CO2/RH headspace, low-turbulence distribution, lid/rim, and service-bus interfaces
  -> MP6 each tile exposes local heat-transfer, plate support, identity, and gasket-land interfaces
  -> MP7 resident sensors have module identity, wiring/data exits, and evidence scope
  -> MP8 local fiducials let the OT-2 and roving observer correct residual tile error

FM0 row-shared environmental module PoC
  -> FM1 glass-bottom SBS plate support avoids the central observation glass
  -> FM2 hard-stop-limited row seal stack and full-footprint removable wet frame control four-plate headspace without fixed side clamps
  -> FM3 CO2/RH sensing, humidification, mixing, supply, return, sampling, and relief are packaged in row-scale service lanes
  -> FM4 print-native material stack uses printed datum, latch, compression, and seal-carrier parts before any metal or hidden hardware exception
  -> FM5 dry-bay aperture, slot-edge standoffs, baffles, and fiducials are compatible with the swept body of a moving sensor-suite module
  -> FM6 service routing exits vertically, through the row lid, underneath, or through a reviewed service bus
  -> FM7 row flow distribution is even enough to avoid liquid-surface disturbance and local evaporation hot spots
  -> FM8 leak, thermal, humidity, CO2, support-flatness, flow, and observer-registration evidence is recorded
  -> RH* row-coupon CAD revisions close through the do-review-context hypergraph
     before any new physical claim is treated as accepted

P0 physical print completes
  -> P1 support/adhesion cleanup
  -> P2 measured bounds and defect inspection
  -> P3 FixtureQcRecord written under data/measurements/
  -> P4 fixture QC validates registration readiness
  -> P5 measured P300 Z margin determines whether the next print becomes a tall platform mule

R0 robot reachable
  -> R1 health, API version, and pipettes read
  -> R2 no active protocol runs
  -> R3 camera still capture works
  -> R4 no-motion maintenance run works
  -> R5 custom fixture labware upload/load works

S0 no-motion bridge session
  -> S1 acquire local SQLite lock
  -> S2 create maintenance run
  -> S3 persist session-scoped fixture pose proposal
  -> S4 upload canonical or oriented fixture labware definition
  -> S5 load fixture labware identity into selected slot
  -> S6 persist session, lock, fixture identity, pose digest/path, command IDs, evidence handles
  -> S7 close or recover maintenance run deterministically

E0 fixture installed in intended deck slot
  -> E1 fixture-presence evidence packet exists
  -> E2 fixture-presence claims derived from camera/vision and inspection
  -> E3 gate ties evidence handles, slot, robot, print QC, and session

O0 installed fixture pose
  -> O1 pose declares slot and orientation as canonical or rot180
  -> O2 operator-declared orientation is only a proposal until a usable pose-orientation claim exists
  -> O3 pose transform maps every canonical well, fiducial, and target into the installed frame
  -> O4 pose digest has stable canonical keys, fixed well-identity policy, and is never empty for motion-authority records
  -> O5 pose digest is stored on session, fixture QC, target records, offsets, safety profile, and evidence
  -> O6 pose_match_gate is the single primitive that every motion-authority gate, including target-class authority, calls before its own predicate
  -> O7 non-canonical pose uses a distinct run-local oriented labware definition preserving physical well identity
  -> O8 direction-suffixed access targets keep canonical-frame semantics
  -> O9 runtime motion code does not import or apply a second coordinate transform
  -> O10 labware offsets are bounded after load and revalidated immediately before dispatch
  -> O11 unknown, missing, stale, mismatched, or unsupported pose blocks all motion gates

T0 target-class scaffold
  -> T1 one TargetClassVerificationRecord exists for every declared target class
  -> T2 each record matches robot, slot, fixture checksums, pose digest, and pipette state
  -> T3 records remain blocked until matching target evidence exists
  -> T4 target evidence artifacts are packetized into target-class claims
  -> T5 target records are promoted only from usable target_class_evidence_packet_v1 claims

Q0 readiness join
  -> Q1 active no-motion session is ready_no_motion
  -> Q2 FixtureQcRecord matches session artifact identity
  -> Q3 target-class records are complete and identity-matched
  -> Q4 pose scope matches evidence and records
  -> Q5 readiness-check returns registration_ready=true and motion_allowed=false

C0 context pack
  -> C1 compact session/robot/fixture context generated from local state
  -> C2 record handles and readiness result included when available
  -> C3 context lists allowed local ops and blocked motion ops

M0 motion commissioning plan
  -> M1 typed operation/plan model exists
  -> M2 plan validator rejects low-Z, wet, and unscaffolded targets
  -> M3 recovery reconciliation handles stale/failed no-motion sessions
  -> M4 daemon execution boundary exists and refuses unsupported motion
  -> M5 local daemon owns the live robot session for motion-capable operations
  -> M6 first motion is home plus high-Z target approach only
  -> M7 evidence packets and claims recorded after each bounded step
  -> M8 offset record written only after evidence agrees

D0 dry target promotion
  -> D1 high-Z target class passes
  -> D2 matching low-Z dry target may be attempted
  -> D3 dry target class passes with evidence

W0 wet workflow
  -> W1 blocked until dry target class passes
  -> W2 dye/water dispense test with evidence
  -> W3 wet target class passes
```

## Exit Criteria

`G*` is complete when `uv run aevum-ot2 fixture-check` passes and generated
artifacts are recorded.

`L*` is complete when geometry marks and integrated coarse labels in the printed
base, plate cap, and cassette match the generated params and do not interfere
with OT-2 seating, cassette registration, mock wells, guide holes, or post-print
measurements. The first PLA print showed that tiny CAD text can fuse, so text is
not a readiness signal.

`B*` is complete for the first PoC when the generated base remains a passive,
open interaction mule. It may include locator posts, labels, and keepout
references, but it must not require routed wires, gas tubes, sidewall cleanup,
slicer support cleanup in the optical bay, or an optical-bay enclosure to run
the P300/cassette evidence path.

`MP*` is complete when the next multi-plate architecture defines the tile datum,
real-plate support datum, shared dry-bay rail/aperture/keepout convention,
moving sensor-suite envelope, four-tile row headspace, low-turbulence
distribution strategy, row chamber/lid interface, service-bus exit assumptions,
resident-sensor evidence scope, and fiducial strategy well enough that a second
adjacent row can be designed without changing the first row's registration
model.

`FM*` is complete when the row-module PoC has a reviewed material stack, four
glass-bottom plate supports that preserve the observation regions, a
row-controlled CO2/RH headspace, side-protrusion-free service routes, and
evidence that the row can retain environmental control without disturbing liquid
surfaces or degrading OT-2 and observer registration.

`RH*` is complete for a CAD revision only when the production part geometry,
validation tests, generated STL/STEP artifacts, CQ-Editor scene, and knowledge
base all agree on the claim being made and the remaining symbolic gaps. The
current RH1-RH9 pass is CAD-closed, not physically validated; the next `RP*`
cycles in `docs/engineering/row_coupon_cycle_log.md` own print, compression,
service-state, passive-flow, humidity, and observer-kinematic evidence.

`P*` is complete for the current printed fixture. The installed assembly in slot
`5` was measured at `127.35 x 85.01 x 89.71 mm`; the pose-scoped fixture QC
record passes `validate_fixture_qc_record(..., readiness="registration")` and
is bound to the current fixture identity and installed pose digest.

`P5` is complete when the first printed fixture has produced a measured safe
margin at the low-Z dry or wet target. The next CAD height must reserve at least
10 mm of that margin and should spend the rest, up to 30 mm, on a taller
under-plate bay envelope before a larger plate platform is designed.

`R*` and `S*` are complete for no-motion when the robot can resolve, camera still
capture works, the fixture labware can be uploaded and loaded into a maintenance
run, and session close leaves no active local lock or run.

`E*` is complete when installed-fixture evidence is recorded as generic
evidence packets, fixture-presence claims are derived, and the gate links those
handles to print QC, robot identity, slot, and session state.

`O*` is complete when the installed fixture pose is explicit, evidence-linked,
digest-scoped, corroborated by a usable pose-orientation claim, and compiled
exactly once into a distinct oriented labware definition that a future motion
backend will use. `pose_match_gate` must be the shared prerequisite for every
motion-authority gate, including target-class authority, and execute-time
revalidation must recheck pose freshness and labware-offset bounds immediately
before dispatch. Canonical labware loaded against a physical `rot180`
installation is no-motion evidence only; it cannot satisfy motion gates.

`T*` is complete for no-motion registration when every declared target class has
a blocked record whose robot, slot, fixture, pose digest, and pipette fields
match the active no-motion session. The current slot `5` / `rot180` session has
that scaffold set; those records still do not authorize low-Z or wet motion.

`Q*` is complete when `readiness-check` returns `registration_ready=true` while
still returning `motion_allowed=false` for records and evidence sharing the
same installed pose digest.

`C*` is complete when `session-context` returns compact local context and closed
sessions advertise only inspection while all motion operations remain blocked.

`M1`, `M2`, `M3`, `M4`, and the local daemon workflow API are complete for
local/no-motion behavior. The CLI can now persist a measured-bound safety profile
and validate plan artifacts at the motion-boundary gate without execution.
`home` validates from the measured safety profile and recovery disposition; the
first `center_high_z` artifact now fails closed until `center_high_z` has
target-class authority, not just a blocked scaffold. Agent callers should pass
the scoped target-class directory instead of expanding every target-class record
into context. Atomic daemon arm/mint/persist/consume is implemented for
`MotionApproval`, and the default backend-disabled path atomically persists a
`MotionDispatchReservation` plus prepared home `CommandJournalEntry` when live
maintenance-run, labware, offset, and command-history readback pass. The
separate `motion_backend_enabled` path can POST the prepared `home` command only
after a second matching readback and journal reconciliation; all target-motion
translators are still closed. `M*` still cannot execute live target motion until
`Q*` passes, a fresh session is armed, high-Z target translation exists, and
physical-event invalidation exists. The CLI remains an
operator/debug adapter, not the normal motion transport.

`D*` and `W*` are future commissioning phases. They require target-specific
evidence and must not be inferred from registration readiness alone.

## Immediate Path

Current continuation:

1. Treat `reg-20260506-001615-6d1a9607` as the only live authority while its
   lease is active; after lease expiry, rerun the no-motion evidence capture and
   commit path before relying on any gate result.
2. Do not dispatch motion from CLI validation artifacts. Motion approval is now
   daemon-minted only: arming requires a schema-valid local gate result blocked
   only by missing approval, then atomically persists
   `motion_commissioning_armed` session/lock state and one approval record.
3. The next implementation gate is high-Z target translation: keep the existing
   live readback and prepared-journal boundary, add a typed `move_high_z`
   command-body translator for `center_high_z`, and still do not POST until the
   final backend gate exists. Execute-time rechecks must include pose digest,
   fixture QC, safety-profile checksum, robot identity, session identity,
   approval expiry, labware-offset bounds, and recovery disposition.
4. Record post-motion high-Z evidence before any low-Z dry target is considered.
5. Keep every non-center, low-Z, wet, and boundary target blocked until its own
   target-specific evidence path is committed.

## Non-Goals

- No live motion from the current no-motion graph.
- No low-Z motion until matching high-Z evidence exists.
- No wet workflow, dye, water, or liquid handling until dry commissioning
  passes.
- No target-class promotion without matching evidence for that exact robot, deck
  slot, fixture artifact, installed pose digest, pipette state, target class,
  and access geometry.
- No raw OT-2 HTTP or Python execution exposed to agents as a normal control
  surface.
