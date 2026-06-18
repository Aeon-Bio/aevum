# Abstraction Divergence Task Graph

## Purpose

This graph turns current architectural drift into explicit engineering work.
It is not a feature backlog. It is the dependency structure required to keep
the OT-2 bridge coherent before exposing more functionality to agents or live
motion.

The recurring rule is:

```text
evidence source -> evidence packet -> derived claim -> gate decision -> record/readiness state -> plan/execution authority
```

No adapter, record, image, command response, target record, or session field can
authorize motion by itself.

## Review Cadence

Every divergence below moves through the same cycle:

```text
do -> local review -> Brutalist review -> patch graph -> implement next slice
```

Local review checks invariants and test coverage. Brutalist review attacks the
boundary from an adversarial position: stale state, forged evidence, ambiguous
commands, cross-session reuse, and agent-context leakage.

Brutalist attacks are not meeting notes. Each attack should become an
executable regression test, initially marked as blocked or xfail when it
describes a known divergence. A divergence is not closed until its attack tests
pass or are deliberately superseded by stricter tests.

## Brutalist Corrections Incorporated

The first external critique found several missing owners in the original graph.
These corrections are now treated as graph requirements:

- command reconciliation and command journaling need their own divergence lane;
  duplicate maintenance command keys were already observed, so key matching is
  not an idempotency guarantee,
- evidence writes must be serialized and session-scoped before they can be a
  fail-closed substrate for motion,
- session `state` and `kind` need typed values before more modules depend on
  them,
- pipette state must become a session invariant, not just a target-record field,
- `home` needs an explicit gate because it is physical motion and can collide
  before target-specific gates matter,
- evidence and claims need freshness/TTL semantics where the physical world can
  change,
- adapter thinness needs an import/route test, not only a review checklist,
- schema renames, especially plan operation names, need compatibility shims and
  schema-version/migration rules,
- evidence durability means crash-atomic packet/index/claim transactions, not
  only serialized writes,
- home-clearance gates must depend on the fixture safety profile and recovery
  state; naming a home gate before safety inputs exist is not enough.

## D1 Evidence Versus Observation

### Drift

The docs now define evidence packets, claims, and gates, but some compatibility
surfaces still have image-centered vocabulary:

- `EvidenceEvent`/`EvidenceIndex` are append-only event payloads, not typed
  evidence packets.
- `LegacyImageEvidenceRecord` is explicitly compatibility-only.
- target records can read old `camera_images`, `vision_results`, and free-text
  commissioning aliases, but writers no longer emit them and their presence
  blocks target-class authority.
- `capture_observation` is now a compatibility-only plan input alias for
  canonical `capture_evidence`; context and writers expose evidence naming.

### Task Graph

```text
D1.0 freeze current no-motion evidence behavior
  -> D1.1 define EvidenceHandle, EvidencePacket, EvidenceClaim, GateResult
  -> D1.2 define source and claim taxonomy
       generated_artifact, robot_state, command_response, command_history,
       camera_capture, vision_analysis, physical_measurement, inspection_note,
       offset_measurement, fixture_pose_orientation, fixture_upright
  -> D1.3 wrap current EvidenceEvent/EvidenceIndex as legacy packet storage
  -> D1.4 add serialized writes and session-scoped evidence indexes
  -> D1.5 add crash-atomic evidence transaction semantics
       packet file, index entry, checksum, claim derivation, recovery scan
  -> D1.6 add packet checksums, freshness/TTL, and quality states
  -> D1.7 define claim freshness and invalidation policy
       clock source, max age by claim, robot/session events that revoke claims;
       pose claims expire on door-open, e-stop, recovery_required, lock lease
       expiry, or maintenance-run reset
  -> D1.8 derive fixture QC claims from existing FixtureQcRecord booleans
  -> D1.9 replace CommissioningObservationRecord with generic evidence packet
       or demote it to a legacy image-note adapter [demoted]
  -> D1.10 rename capture_observation surfaces with compatibility shims [done]
       capture_observation -> capture_evidence
  -> D1.11 context exposes evidence handles, missing claims, and gate summaries
```

### Do -> Review Cycles

1. Do: add pure evidence models without changing callers.
   Review: models are source-agnostic, contain provenance, quality state, and
   cannot carry motion authorization.

2. Do: add serialized evidence writes and per-session evidence index paths.
   Review: concurrent writers cannot silently lose events; evidence write
   failure is testable and fail-closed.

3. Do: add crash-atomic evidence transaction behavior.
   Review: packet write, index update, checksum, and claim derivation either
   commit coherently or leave a recoverable failed transaction; no orphan packet
   can satisfy a gate.

4. Do: add claim freshness/invalidation table.
   Review: each claim either has an explicit TTL/invalidation trigger or is
   declared timeless because it is a generated artifact checksum.

5. Do: add compatibility derivation from current fixture QC records to claims.
   Review: registration readiness output stays unchanged; every legacy boolean
   has explicit legacy provenance.

6. Do: replace image-centered observation naming in plans/context/service.
   Review: no default agent context treats an image as the canonical evidence
   artifact; old plan operation strings have a schema-versioned compatibility
   path.

### Brutalist Attacks

- One good image but missing physical measurements must not pass fixture QC.
- Passing legacy booleans without provenance must be either explicit legacy
  evidence or rejected.
- A single evidence packet must never set `motion_allowed=true`.
- Ambiguous or failed evidence quality must become a missing usable claim.
- Stale fixture-presence claims must expire; replayed old claims must not pass
  physical gates.
- Concurrent evidence writes must preserve both events or fail loudly.

## D2 Readiness Versus Gates

### Drift

`ReadinessResult` is registration-specific, but it is becoming the generic gate
surface. Fixture QC, registration, high-Z, low-Z, wet, and recovery gates need
one predicate/result shape before motion expands.

### Task Graph

```text
D2.0 preserve ReadinessResult no-motion contract
  -> D2.1 define gate names and gate inputs
       fixture_qc, registration, first_high_z, low_z_dry, wet, recovery
  -> D2.2 define GateResult with passed, missing_claims, blockers, handles
  -> D2.3 implement fixture_qc_gate from evidence claims
  -> D2.4 implement registration_gate over session + fixture + targets + claims
  -> D2.5 make evaluate_registration_readiness delegate to registration_gate
  -> D2.6 expose gate summaries in SessionContext
```

### Do -> Review Cycles

1. Do: create `GateResult` and blocked placeholders for future gates.
   Review: low-Z/wet gates exist but are hard-blocked until explicit evidence.

2. Do: adapt registration readiness to include gate result details.
   Review: `registration_ready=true` can still occur for no-motion, while
   `motion_allowed=false` remains invariant.

3. Do: update context pack to report missing claims and blockers.
   Review: context stays compact and does not dump raw evidence payloads.

### Brutalist Attacks

- Registration readiness must not imply high-Z, low-Z, wet, or offset authority.
- A stale record handle must not override file contents.
- Gate evaluation must block cross-robot, cross-slot, and checksum mismatch.

## D3 Domain Records Versus Evidence Store

### Drift

`FixtureQcRecord`, `TargetClassVerificationRecord`, and `OffsetRecord` are
workflow summaries, but current fields mix evidence, derived state, and gate
facts. If they become raw evidence stores, records will grow without preserving
provenance or claim quality.

### Task Graph

```text
D3.0 classify current records as domain records
  -> D3.1 add evidence_handle and claim_handle references to records
  -> D3.2 keep large/raw artifacts only in evidence packets
  -> D3.3 keep legacy fields readable but mark them as derived/compatibility
  -> D3.4 update target-class validation to require claims over camera paths
  -> D3.5 update target-record writers to emit handles and omit legacy fields
```

### Do -> Review Cycles

1. Do: add evidence/claim handle arrays without removing legacy fields.
   Review: existing JSON round trips still pass.

2. Do: update validators to consume generic claims.
   Review: camera paths, vision-result paths, and free text never satisfy
   target authority; usable `target_class_verified:<target_class>` claims do.

3. Do: document record schema responsibilities.
   Review: records summarize durable workflow state and do not embed full
   evidence packets.

### Brutalist Attacks

- Target promotion with raw image paths but no matching claims must block.
- Evidence from another session, robot, slot, fixture checksum, or pipette must
  not satisfy record validation.
- Free text must not satisfy a machine gate except through an explicit
  supervised-commissioning fallback claim.

## D4 No-Motion Session Versus Bridge Session Capabilities

### Drift

The current session lifecycle is intentionally no-motion. That is correct for
the print phase, but future code needs a generic bridge session with explicit
capabilities, gates, and transitions rather than a permanent `ready_no_motion`
center.

### Task Graph

```text
D4.0 freeze no-motion session behavior
  -> D4.1 convert session state and kind to typed values
  -> D4.2 define session capability model
       inspect, record_evidence, validate, close, recover, motion_commission
  -> D4.3 define motion lifecycle states
       ready_no_motion, motion_commissioning_armed, high_z_ready,
       dry_ready, wet_ready, recovery_required, closed
  -> D4.4 define transition guard predicates
  -> D4.5 define explicit recovery_required exit paths
       recovered_closed, supervised_override_closed, unresolved_recovery
       recovery across pose change remains unresolved for motion; supervised
       compatibility may annotate inspection records only
  -> D4.6 keep no-motion init/close/recover as specific lifecycle helpers
  -> D4.7 update context to compute allowed ops from capabilities and gates
```

### Do -> Review Cycles

1. Do: add tests that freeze no-motion session invariants.
   Review: no current path can send motion or leave ready sessions open.

2. Do: replace string state/kind comparisons with typed values.
   Review: typo states fail validation at model boundaries.

3. Do: add capability model and transition table without live motion.
   Review: motion transitions are declared but unreachable without gates and an
   explicit backend.

4. Do: context derives allowed/blocked ops from session capability state.
   Review: no hard-coded future contradiction between context and validation.

### Brutalist Attacks

- Expired/stale lease must not promote to another session.
- Context must not advertise motion while execution backend is disabled.
- Recovery session must not execute normal workflow motion.
- A recovery-required session must have a documented non-destructive terminal
  path if automatic reconciliation cannot complete.

## D4b Robot And Pipette Identity Invariants

### Drift

Robot serial, server/API version, and pipette state are read during status and
stored in target records, but the live session model does not yet make pipette
identity a first-class invariant. A target record can appear valid even if the
mounted instrument has changed.

### Task Graph

```text
D4b.0 preserve current robot discovery behavior
  -> D4b.1 add session pipette identity fields
       pipette name, model, mount, pipette ID when available, tip length
  -> D4b.2 re-check robot/server/pipette identity at execute time
  -> D4b.3 make readiness and gate evaluation reject pipette drift
  -> D4b.4 evidence packets record robot/pipette provenance
```

### Do -> Review Cycles

1. Do: add pipette identity to session context and persisted session models
   with compatibility defaults.
   Review: existing no-motion sessions load; new sessions store observed
   pipette facts.

2. Do: add pure drift checks before execution.
   Review: wrong pipette name, mount, ID, server version, or robot serial
   blocks physical execution.

### Brutalist Attacks

- Reuse target records after swapping P300/P20 or left/right mount.
- Reuse evidence from the same robot after robot-server version drift.
- Validate a plan from stale session data after live pipette state changes.

## D5 Plan Operations Versus Typed Intents

### Drift

`PlanOperation` has been split into explicit categories and `PlanStep` now
validates per-operation parameter allowlists. The remaining divergence is that
`record_evidence`, offset writes, and live motion payloads are still declared
as intent names, not implemented execution backends.

### Task Graph

```text
D5.0 keep current plan validation read-only
  -> D5.1 split operation categories [done]
       context, evidence, gate, session, motion, recovery
  -> D5.2 define typed payload allowlists [done]
       capture_evidence, record_evidence, close_session, home,
       high_z_target, low_z_dry_target, set_offset_proposal, liquid_handling
  -> D5.3 forbid arbitrary coordinates except bounded registration diagnostics [done]
  -> D5.4 validate duplicate step IDs and unknown parameters [done]
  -> D5.5 depend on the global schema migration policy
  -> D5.6 add operation-name migration shims [done]
  -> D5.7 add execute-time revalidation inputs [done]
       live robot status, lock freshness, run command history, pipette state
  -> D5.8 keep direct offset writes unreachable until command journaling and
       offset authority are transaction-backed
```

### Do -> Review Cycles

1. Do: add schema tests for current loose-parameter risks.
   Review: malformed or unexpected motion payloads fail validation.

2. Do: introduce typed plan payloads while keeping old plan fragments for
   no-motion inspection.
   Review: motion payloads cannot encode raw OT-2 HTTP or arbitrary Python.

3. Do: add execute-time guard function as pure validation.
   Review: stale lock, wrong pipette, wrong serial, missing gate, or command
   ambiguity fails closed.

### Brutalist Attacks

- Unexpected keys in `parameters` must not smuggle raw coordinates or HTTP.
- Unknown or legacy operation strings must not be silently dropped.
- Validation and context cannot disagree about motion authority.
- `motion_enabled=true` cannot bypass missing gates or malformed payloads.

## D6 Target Class Versus Target Geometry And Policy

### Drift

`TargetClass` currently names verification categories, but it does not encode
the full policy: geometry, Z tier, first-pass eligibility, offset requirements,
claim requirements, safety profile, and predecessor constraints.

### Task Graph

```text
D6.0 preserve existing target names
  -> D6.1 define TargetPolicy
       target_class, geometry_id, column_offset, z_tier, wet/dry,
       mat_patch, boundary, first_pass_allowed, required_predecessors,
       required_claims
  -> D6.2 define TargetGeometry or TargetInstance separately from TargetClass
  -> D6.3 replace string substitution predecessor checks with policy lookup
  -> D6.4 add target-promotion gate
  -> D6.5 context reports target status by policy, not ad hoc record fields
```

### Do -> Review Cycles

1. Do: build `TargetPolicy` data and tests matching docs.
   Review: all declared target names remain present; boundary and mat-patch
   dependencies are explicit.

2. Do: use policy lookup in validation instead of `_low_z_dry -> _high_z`.
   Review: no center evidence can authorize offset targets; no dry evidence can
   authorize wet targets.

3. Do: target-promotion gate consumes claims and predecessor status.
   Review: target records cannot self-promote by setting `result=passed`.

### Brutalist Attacks

- Authorize offset low-Z using center high-Z evidence.
- Promote boundary target as first-pass.
- Promote mat-patch wet without both mat-patch dry and no-mat wet evidence.

## D7 Offset Record Versus Offset Authority

### Drift

`OffsetRecord` stores scoped fields and `verification_targets`, but plan
validation does not yet enforce a matching offset registry entry for low-Z or
wet plans.

### Task Graph

```text
D7.0 preserve current registry read/write behavior
  -> D7.1 depend on TargetPolicy and FixtureSafetyProfile identity
  -> D7.2 implement offset_match_gate
       robot serial, server/API, fixture load/checksums, slot,
       pipette name/mount, tiprack, target class, safety_profile_sha256
  -> D7.3 require offset match for low_z_dry and wet gates
  -> D7.4 distinguish proposed offset from promoted offset
  -> D7.5 record evidence handles for offset measurement and confirmation
```

### Do -> Review Cycles

1. Do: pure offset match tests against existing `OffsetRecord`.
   Review: every scope mismatch blocks.

2. Do: connect offset match to low-Z and wet validation.
   Review: `offset_registry_record="not-yet-registered"` cannot authorize
   low-Z.

3. Do: add proposed/promoted offset lifecycle.
   Review: an offset cannot be reused without target verification claims.

### Brutalist Attacks

- Reuse offset across robot, slot, pipette, fixture checksum, or target class.
- Use a proposed offset as a promoted offset.
- Use target-class `passed` without matching offset authority.

## D8 Safety Envelope Versus Labware Definition

### Drift

Generated labware gives dimensions and well centers. It is not a collision or
safety model. The bridge needs a fixture-specific safety profile from CAD
params, measured QC, target policy, and future forbidden zones.

### Task Graph

```text
D8.0 identify safety inputs
       params, generated labware, measured QC, target policy, pipette state
  -> D8.1 define FixtureSafetyProfile
       measured bounds, conservative high Z, dry Z floor, wet Z floor,
       max jog, boundary target handling, forbidden zones
  -> D8.2 derive profile from generated params and QC claims
  -> D8.3 compute safety_profile_sha256 and freshness inputs
  -> D8.4 define home_clearance_gate over safety profile and recovery state
  -> D8.5 require safety profile for motion validation
  -> D8.6 expose safety blockers in gate/context summaries
```

### Do -> Review Cycles

1. Do: create pure safety profile model.
   Review: missing measured QC blocks low-Z and wet; generated dimensions alone
   are insufficient.

2. Do: wire safety checks into plan validation.
   Review: out-of-bounds, unsafe Z, large jog, and boundary default all block.

3. Do: add context safety summary.
   Review: agents get blockers, not raw geometry dumps.

### Brutalist Attacks

- Treat labware JSON dimensions as full collision model.
- Treat `home` as safe without a safety profile and recovery-state check.
- Permit low-Z with missing or worse-than-CAD measured bounds.
- Permit boundary target motion before inner targets prove margin.
- Reuse an offset after a safety profile checksum changes.

## D9 Run Mode Versus Session Kind

### Drift

Docs distinguish maintenance mode and protocol mode. Code has session kinds
(`registration`, `dry_run`, `recovery`, `no_motion_probe`) but no explicit run
mode policy layer.

### Task Graph

```text
D9.0 preserve first implementation as maintenance/no-motion
  -> D9.1 define RunMode policy
       maintenance, protocol
  -> D9.2 map session kind to allowed run modes
  -> D9.3 reject protocol-mode motion until dry commissioning passes
  -> D9.4 make recovery mode separate from normal motion mode
```

### Do -> Review Cycles

1. Do: introduce run-mode policy without changing live behavior.
   Review: registration uses maintenance; protocol remains unavailable for
   first fixture motion.

2. Do: validate run mode in plan validation.
   Review: dry-run/protocol/liquid plans cannot slip into registration.

3. Do: add recovery-specific allowed operations.
   Review: recovery session cannot execute normal workflow motion.

### Brutalist Attacks

- Protocol-mode liquid handling before dry verification.
- Recovery session executing normal high-Z/low-Z workflow.
- Maintenance command used to bypass protocol safety gates.

## D10 Adapter Surface Versus Bridge Semantics

### Drift

The docs say adapters are thin, but as more operations are added there is a
risk that CLI/MCP/HTTP each reimplement validation, evidence, or OT-2 calls.

### Task Graph

```text
D10.0 keep BridgeService as adapter boundary
  -> D10.1 add daemon endpoints only after core semantics exist
  -> D10.2 make CLI motion-capable commands daemon clients only
  -> D10.3 MCP tools map one-to-one to workflow operations
  -> D10.4 add adapter-thinness import and route parity tests
```

### Do -> Review Cycles

1. Do: add import-graph test for adapter boundaries.
   Review: motion-capable adapters cannot import raw OT-2 transport or own
   validation logic.

2. Do: add tests for daemon client/app route parity.
   Review: no naming drift such as singular/plural target records.

3. Do: add MCP only after evidence/gate/session/plan models settle.
   Review: no raw coordinates, raw HTTP, arbitrary Python, or direct offset
   mutation tools.

### Brutalist Attacks

- Prove an adapter can bypass `BridgeService.validate_plan`.
- Add an MCP tool that leaks raw robot-server HTTP.
- Add CLI live motion that instantiates a separate in-process bridge state.

## D11 Command Journal And Reconciliation

### Drift

Command-key testing showed duplicate maintenance command keys can both succeed.
The bridge therefore cannot treat command keys as idempotency guards. The graph
needs an explicit owner for command journaling, reconciliation, ambiguity, and
recovery entry.

### Task Graph

```text
D11.0 preserve no-motion command-key bench evidence
  -> D11.1 define CommandJournalEntry [done]
       step ID, command key, command ID, index, command type, params hash,
       status, timestamps, run ID, maintenance/protocol mode
  -> D11.2 require journal availability before any physical command POST [done]
  -> D11.3 persist pre-dispatch journal entry before POST [done]
  -> D11.4 persist accepted/completed journal updates after responses [done]
  -> D11.5 define crash states [done]
       before POST, after POST before response, after response before update,
       during history fetch timeout
  -> D11.6 reconcile timeout by command ID, index, status, timestamps, [done]
       command type, params hash, and run history
  -> D11.7 mark ambiguous results as recovery_required [done]
  -> D11.8 expose command-history claims to gate evaluation
```

### Do -> Review Cycles

1. Do: add pure command journal models and no-motion tests.
   Review: duplicate keys are explicitly represented as non-idempotent. [done]

2. Do: add reconciliation function over mocked command history.
   Review: accepted/completed/failed/ambiguous outcomes are distinct. [done]

3. Do: add dispatch transaction tests.
   Review: journal unavailable means no POST; crash-state recovery is explicit
   for every before/after edge. [done]

4. Do: connect ambiguous reconciliation to recovery-required transition.
   Review: no automatic retry can issue a second motion command. [done]

### Brutalist Attacks

- Timeout after `POST` must not trigger blind retry.
- Duplicate command keys must not be merged into one command.
- Command history mismatch must enter recovery rather than infer success.
- Command response without matching journal entry must not promote a target.

## D12 Schema Evolution And Data Retention

### Drift

Several divergences require renaming or widening persisted schemas: plan
operation names, evidence events, session state/kind, records, offsets, command
journals, and future safety profiles. Local compatibility shims are not enough;
schema migration needs one owner.

### Task Graph

```text
D12.0 inventory persisted schemas and default paths
  -> D12.1 define schema-version policy and migration rules
  -> D12.2 define compatibility adapters for current records/plans/sessions
  -> D12.3 define evidence index retention and rotation policy
  -> D12.4 require migration tests for every persisted schema change
  -> D12.5 define invalid/unknown schema fail-closed behavior
```

### Do -> Review Cycles

1. Do: inventory persisted JSON/SQLite payloads.
   Review: every schema has an owner, version, and migration/fail policy.

2. Do: add migration tests for plan operation renames and record widening.
   Review: old no-motion artifacts either load compatibly or fail with typed
   recovery instructions.

3. Do: add evidence retention/rotation policy.
   Review: per-session evidence can be summarized without deleting raw physical
   evidence needed for audit or recovery.

### Brutalist Attacks

- Unknown plan operation must not be silently ignored.
- Old evidence events must not satisfy new gates without a compatibility claim.
- Unknown schema version must fail closed with an actionable recovery message.
- Evidence retention must not delete packets referenced by active records,
  offsets, command journals, or recovery sessions.

## Consolidated Critical Path

```text
CP-pre0 freeze no-motion invariants as executable tests [initial anchors added]
  -> CP-pre1 type session state/kind and define non-destructive recovery exits [initial boundary added]
  -> CP-pre2 serialize/session-scope evidence writes [index append boundary added]
  -> CP-pre3 convert Brutalist attacks into pytest cases
  -> CP-pre4 enforce adapter import boundary for future motion-capable adapters
  -> CP1 evidence packet/claim/gate models and schema evolution policy
  -> CP2 target policy model
  -> CP3 fixture QC and registration gates
  -> CP4 session capabilities and pipette/robot invariants
  -> CP5 typed plan intent schemas with migration shims
  -> CP6 safety profile, home-clearance, and offset match gates
  -> CP7 plan validation v2 over gates and typed intents
  -> CP8 execute-time revalidation, command journal, and reconciliation
  -> CP9 first high-Z motion backend
  -> CP10 thin MCP/CLI/HTTP adapters
```

Anything that tries to implement live motion, MCP motion tools, low-Z, wet
workflow, or offset promotion before `CP-pre0` through `CP8` is out of order.

## Resolution-Gated Execution Graph

This graph is the autonomous continuation contract for the remaining work. User
input is not required to move from one software task to the next. The output of
each review cycle is the input to the next task.

Every node has the same control loop:

```text
do -> local review -> Brutalist review -> resolution patch -> next input
```

Resolution means:

- focused tests cover the new behavior and the highest-risk attack cases,
- `uv run pytest -q` passes with only intentionally documented xfails,
- `uv run ruff check .` passes,
- Brutalist findings are either fixed immediately or converted into scheduled
  graph nodes before continuing,
- no live robot motion was added unless the live-motion graph has resolved
  through `RG12`,
- `docs/engineering/divergence_task_graph.md` records completed work, remaining
  risk, and the next resolved input.

If a review finds a blocker, that blocker becomes the next node and preempts the
planned sequence. If a review finds only future work, the graph advances.

### Current Software Path

```text
RG0 current resolved baseline
  -> RG1 target policy and target geometry model
  -> RG2 fixture safety profile and home-clearance inputs
  -> RG3 promoted offset authority gate
  -> RG4 home-clearance gate
  -> RG5 plan validation v2 over gates
  -> RG6 crash-atomic evidence transactions
  -> RG7 schema-version blockers and migration fixtures
  -> RG8 compare-and-set lock acquisition
  -> RG9 target-record evidence/claim handle cleanup
  -> RG10 session pipette invariants and execute-time revalidation
  -> RG11 typed plan intents and operation-name shims
  -> RG12 command journal and reconciliation
  -> RG13 adapter thinness tests and MCP readiness
  -> RG14-pre fixture pose and oriented labware
  -> RG14 first high-Z motion backend
```

### Node Contracts

#### RG0 Current Resolved Baseline

Input: current repository state.

Do:

- Preserve the current no-motion envelope and the two intentional xfails:
  promoted offset authority and home-clearance.

Review:

- Full tests and lint pass.
- Graph records all completed slices and current xfails.

Resolution:

- `BaselineResolution` with test/lint status and active xfail inventory.

Next input:

- `BaselineResolution` feeds `RG1`.

#### RG1 Target Policy And Target Geometry Model

Input: `BaselineResolution`, current `TARGET_CLASSES`, target-class tests, and
target verification docs.

Do:

- Define `TargetPolicy` data for every declared target class.
- Encode geometry ID, Z tier, dry/wet, mat patch, boundary, first-pass
  eligibility, required predecessors, and required claims.
- Keep existing target names stable.

Review:

- Tests prove all existing target names map to policies.
- Boundary targets cannot be first-pass targets.
- Mat-patch wet requires both mat-patch dry and no-mat wet predecessors.
- Existing target-class records still load.

Brutalist focus:

- Authorize offset low-Z using center high-Z evidence.
- Promote boundary target as first pass.
- Promote mat-patch wet with one predecessor missing.

Resolution:

- `TargetPolicyResolution` with policy coverage and attack-test status.

Next input:

- `TargetPolicyResolution` feeds `RG2` and `RG3`.

#### RG2 Fixture Safety Profile And Home-Clearance Inputs

Input: `TargetPolicyResolution`, generated params/labware identity, fixture QC
claims, and readiness contract.

Do:

- Define `FixtureSafetyProfile` from generated params plus measured QC claims.
- Include measured bounds, conservative high Z, dry/wet Z floors, max jog,
  forbidden zones, boundary handling, and `safety_profile_sha256`.
- Keep generated labware dimensions classified as artifact identity, not a
  collision model.

Review:

- Missing measured QC blocks low-Z, wet, and home-clearance gates.
- Generated labware JSON alone cannot create a passing safety profile.
- Safety profile checksum changes when measured bounds or policy inputs change.

Brutalist focus:

- Treat labware JSON dimensions as a full safety model.
- Permit boundary motion before inner target margin exists.
- Reuse an offset after safety profile checksum drift.

Resolution:

- `SafetyProfileResolution` with safety profile checksum semantics and blockers.

Next input:

- `SafetyProfileResolution` feeds `RG3` and `RG4`.

#### RG3 Promoted Offset Authority Gate

Input: `TargetPolicyResolution`, `SafetyProfileResolution`, current
`OffsetRecord`/registry model, and low-Z xfail.

Do:

- Define offset authority state: proposed versus promoted.
- Implement `offset_match_gate` scoped by robot serial, server/API, fixture
  checksums, slot, pipette, tiprack, target policy, and safety profile checksum.
- Require promoted offset authority for low-Z and wet gates.

Review:

- The current low-Z xfail becomes a passing test.
- `offset_registry_record="not-yet-registered"` blocks low-Z.
- Scope mismatches block: robot, slot, pipette, fixture checksum, target, safety
  profile checksum.

Brutalist focus:

- Reuse offset across robot, slot, pipette, fixture, or target class.
- Use proposed offset as promoted authority.
- Use target-class `passed` without matching offset authority.

Resolution:

- `OffsetAuthorityResolution` with the promoted-offset xfail removed.

Next input:

- `OffsetAuthorityResolution` feeds `RG5`.

#### RG4 Home-Clearance Gate

Input: `SafetyProfileResolution`, session state, recovery disposition, and home
xfail.

Do:

- Implement `home_clearance_gate` over safety profile, session state, recovery
  state, robot identity, and pipette identity placeholders.
- Keep `home` physical motion blocked until this gate passes and execution
  revalidation exists.

Review:

- The current home-clearance xfail becomes a passing test.
- Registration readiness alone cannot authorize `home`.
- Recovery-required sessions cannot pass home-clearance.

Brutalist focus:

- Treat home as safe because it is not target-specific.
- Home after ambiguous recovery.
- Home with missing safety profile or stale session.

Resolution:

- `HomeClearanceResolution` with the home xfail removed.

Next input:

- `HomeClearanceResolution` feeds `RG5`.

#### RG5 Plan Validation V2 Over Gates

Input: `OffsetAuthorityResolution`, `HomeClearanceResolution`, current
validation tests, and daemon service tests.

Do:

- Replace validation shortcuts with gate lookups for motion operations.
- Preserve current no-motion execution behavior.
- Keep validation/context/execution authority consistent.

Review:

- No motion operation validates from registration readiness alone.
- `motion_enabled=true` cannot bypass missing gates.
- Context and validation report compatible blockers.
- Execution still returns `not_implemented` for motion backend absence.

Brutalist focus:

- Validation and context disagree about motion authority.
- Malformed or incomplete gate inputs produce allowed motion.
- A non-motion adapter bypasses validation.

Resolution:

- `PlanValidationV2Resolution` with no intentional xfails unless newly
  documented.

Next input:

- `PlanValidationV2Resolution` feeds `RG6`, `RG10`, and `RG11`.

#### RG6 Crash-Atomic Evidence Transactions

Input: `PlanValidationV2Resolution`, current evidence index, evidence packet
models, and schema inventory.

Do:

- Add packet/index/checksum/claim transaction semantics.
- Commit packet file, index entry, checksum, and derived claims coherently.
- Add recovery scan for partial transactions.

Review:

- Orphan packets cannot satisfy gates.
- Index entries with missing packets fail closed.
- Concurrent writers preserve both transactions or fail loudly.
- Recovery scan reports partial state without promoting claims.

Brutalist focus:

- Crash before index update.
- Crash after packet write but before claim derivation.
- Replay old packet after physical claim freshness expires.

Resolution:

- `EvidenceTransactionResolution`.

Next input:

- `EvidenceTransactionResolution` feeds `RG7` and `RG9`.

#### RG7 Schema-Version Blockers And Migration Fixtures

Input: `EvidenceTransactionResolution`, schema inventory, v1 artifacts, and
compatibility aliases.

Do:

- Add loader-level version checks for records, plans, evidence indexes, offset
  registries, packets, claims, and gate summaries.
- Add migration fixtures for renamed operations and widened records.
- Add explicit legacy-load telemetry or blockers where aliases are still
  accepted.

Review:

- Unknown schema versions fail closed with actionable errors.
- v1 no-motion artifacts load compatibly where declared.
- Legacy aliases cannot satisfy motion gates without compatibility claims.

Brutalist focus:

- Unknown future schema interpreted under current semantics.
- Old evidence event satisfies new motion gate.
- Retention deletes active evidence references.

Resolution:

- `SchemaResolution`.

Next input:

- `SchemaResolution` feeds `RG8`, `RG9`, and `RG11`.

#### RG8 Compare-And-Set Lock Acquisition

Input: `SchemaResolution`, lock/session DB model, and session lifecycle tests.

Do:

- Replace read-then-upsert lock acquisition with an atomic compare-and-set path.
- Preserve terminal lock states and stale lease behavior.
- Keep recovery non-destructive.

Review:

- Concurrent session-start attempts yield at most one active lock.
- Expired locks can be acquired only through documented state transition.
- Failed acquisition does not create a robot maintenance run.

Brutalist focus:

- Two daemons race from no lock to active lock.
- Expired but unreconciled lock is stolen.
- Robot-side run created before local ownership is durable.

Resolution:

- `LockResolution`.

Next input:

- `LockResolution` feeds `RG10` and live no-motion physical path.

#### RG9 Target-Record Evidence/Claim Handle Cleanup

Input: `EvidenceTransactionResolution`, `SchemaResolution`, target policy, and
target-class record tests.

Do:

- Add evidence and claim handle arrays to target records.
- Mark camera/vision/free-text fields as legacy compatibility fields.
- Update target validation to require claims and to reject raw paths/free text as
  machine gates.

Review:

- Current JSON still round-trips and old aliases still load.
- Target promotion with only raw image paths blocks.
- Cross-session, cross-robot, cross-slot, fixture, and pipette mismatches block.
- Low-Z, wet, and non-first-pass high-Z gates use predecessor target authority
  instead of `result=passed` alone.
- Evidence handle paths exist, checksums match, claim-embedded handles match
  record handles, and duplicate target records block validation.

Brutalist focus:

- Free text satisfies a machine gate.
- Evidence handle from another session promotes a target.
- Target record self-promotes by setting `result=passed`.

Resolution:

- `TargetRecordResolution`: `TargetClassVerificationRecord` now carries
  `evidence` and `claims`; legacy `camera_images`, `vision_results`, and
  `commissioning_observation` aliases load into compatibility-only fields that
  writers exclude; record validation requires a true usable
  `target_class_verified:<target_class>` claim and usable evidence handles with
  existing checksum-matched paths; claim evidence handles must match record
  handles; duplicate target records block plan validation; and motion
  predecessor gates call `target_class_authority` so a manually passed target
  record cannot promote downstream motion.

Next input:

- `TargetRecordResolution` feeds `RG10` and `RG11`.

#### RG10 Session Pipette Invariants And Execute-Time Revalidation

Input: `LockResolution`, `TargetRecordResolution`, robot status shape, and
execution boundary tests.

Do:

- Persist pipette identity fields in sessions with compatibility defaults.
- Re-check robot/server/pipette identity before any physical execution.
- Add pure execute-time revalidation inputs: live robot status, lock freshness,
  command history summary, gate state, and pipette state.

Review:

- Wrong pipette name, mount, ID, server version, robot serial, or stale lock
  blocks execution.
- Existing no-motion sessions load.
- No execute-time failure sends a robot command.

Brutalist focus:

- Swap P300/P20 after target verification.
- Validate from stale session data.
- Execute after server/API version drift.

Resolution:

- `ExecuteRevalidationResolution`: `BridgeSession` now persists additive
  pipette identity fields with empty compatibility defaults; no-motion session
  start snapshots the selected pipette mount; readiness compares target records
  against session pipette name/mount when present; and `execute_next` reruns a
  pure `core.revalidation` guard for motion steps. The guard requires passing
  plan/gate state, reloaded `ready_no_motion` session state, an unexpired
  session lease, a fresh matching bridge lock in a motion-capable state, live
  robot health, complete matching robot/server/API identity, complete matching
  live pipette name/model/ID/tip length, and a matching succeeded last command
  before the future motion backend can be reached. Missing or failed
  execute-time inputs are folded into the validation response and send no robot
  command.

Next input:

- `ExecuteRevalidationResolution` feeds `RG11` and `RG12`.

#### RG11 Typed Plan Intents And Operation-Name Shims

Input: `PlanValidationV2Resolution`, `SchemaResolution`, and
`ExecuteRevalidationResolution`.

Do:

- Split plan operation categories: context, evidence, gate, session, motion,
  recovery.
- Add typed payloads for home, high-Z target, low-Z dry target, set-offset
  proposal, write-offset, and liquid handling.
- Rename `capture_observation` through a compatibility shim to
  `capture_evidence` / `record_evidence`.

Review:

- Unknown parameters and arbitrary raw coordinates fail validation.
- Old no-motion plan fragments migrate or fail with typed blockers.
- Motion payloads cannot encode raw OT-2 HTTP or arbitrary Python.

Brutalist focus:

- Smuggle raw coordinates through `parameters`.
- Unknown legacy operation silently dropped.
- MCP/CLI route accepts a different plan schema from daemon.

Resolution:

- `TypedPlanResolution` is implemented in `core.plans`. Canonical operations
  now expose categories, `capture_observation` maps only through a read shim to
  `capture_evidence`, step extras are forbidden, `target_class` is accepted
  only for target motion intents, and each operation has a typed parameter
  allowlist. Current motion intents accept no raw parameter payloads, so raw
  coordinates, robot-server HTTP, command bodies, arbitrary Python, and direct
  offset mutation fail at the shared plan schema used by daemon routes.
  `record_evidence` has a typed payload but remains validation-blocked until
  evidence transaction write helpers own that lifecycle.

Next input:

- `TypedPlanResolution` feeds `RG12` and `RG13`.

#### RG12 Command Journal And Reconciliation

Input: `ExecuteRevalidationResolution`, `TypedPlanResolution`, command-key
bench evidence, and recovery tests.

Do:

- Define command journal entries and crash states.
- Persist pre-dispatch journal entry before any physical command POST.
- Reconcile accepted/completed/failed/ambiguous outcomes by command ID, index,
  status, timestamp, command type, params hash, and run history.
- Mark ambiguous outcomes as `recovery_required`.

Review:

- Journal unavailable means no POST.
- Timeout after POST never triggers blind retry.
- Duplicate command keys are represented as non-idempotent.
- Command response without matching journal entry cannot promote a target.

Brutalist focus:

- Network timeout after command POST.
- Duplicate command key appears successful twice.
- Command history mismatch inferred as success.

Resolution:

- `CommandJournalResolution` is implemented in `core.command_journal`.
  Dispatch preparation persists a `CommandJournalEntry` before a future command
  POST can proceed; journal write failure returns a blocker. `(run_id,
  command_key)` is unique locally, so duplicate-key blind retry is blocked
  before a second POST. The journaled dispatch helper owns prepare -> POST ->
  posted-update -> complete-history reconciliation for current session-init
  `loadLabware` and future physical command paths. It blocks missing or
  mismatched command/history run routes before POST and reports post-dispatch
  journal write failures as recovery-required outcomes instead of crashing past
  the lock. Reconciliation distinguishes completed, failed, accepted, and ambiguous
  outcomes using command ID, key, command type, params hash, command index,
  status, run ID, and complete run history. Missing, incomplete, wrong-run, or
  malformed history; queued/running terminal reconciliation attempts; duplicate
  keys; mismatched command payloads; and command responses without a journal
  entry all enter `recovery_required` and cannot trigger blind retry. Session
  initialization confirms cleanup deletes with a post-delete GET; unconfirmed
  cleanup or ambiguous reconciliation leaves the session and lock in
  `recovery_required`.

Next input:

- `CommandJournalResolution` feeds `RG13` and `RG14`.

#### RG13 Adapter Thinness Tests And MCP Readiness

Input: `TypedPlanResolution`, `CommandJournalResolution`, service/client route
map, and adapter policy.

Do:

- Add import-graph tests for CLI/HTTP/MCP boundaries.
- Ensure motion-capable adapters call daemon workflow operations only.
- Add route parity tests for safety-profile and offset-registry inputs before
  any HTTP/MCP route advertises motion capability.
- Define MCP tool surface after core semantics settle.

Review:

- Adapters cannot import raw OT-2 transport for motion.
- Route parity tests cover daemon app and client naming.
- No adapter exposes raw robot-server HTTP, arbitrary Python, direct coordinate
  motion, or direct offset mutation.

Brutalist focus:

- Adapter bypasses `BridgeService.validate_plan`.
- MCP tool leaks raw robot-server HTTP.
- CLI live motion instantiates separate in-process state.

Resolution:

- `AdapterResolution` is implemented for the current adapter surface. HTTP plan
  routes and the daemon client now carry `offset_registry`, `safety_profile`,
  and `recovery_disposition` with matching field names. GET context and POST
  plan routes share safe record-path validation for fixture-QC and target-class
  record inputs. Import/AST boundary tests pin the HTTP daemon and daemon client
  away from raw OT-2 transport, keep CLI commands from directly sending raw
  robot POST/DELETE calls, and preserve the documented MCP surface without raw
  HTTP, Python, direct coordinate motion, or direct offset mutation tools.

Next input:

- `AdapterResolution` feeds `RG14-pre`.

#### RG14-pre Fixture Pose And Oriented Labware

Input: slot-5 rotated fixture evidence, generated canonical labware definition,
target policy table, offset authority model, and no-motion session lifecycle.

Discovery:

- Printed PoC fixture is most camera-visible in slot `5` only when physically
  rotated 180 degrees.
- Slot-5 canonical no-motion session was evidence-only and closed.
- Canonical well/target coordinates are wrong for the physical slot-5 install
  until orientation is modeled.

Do:

- Define `FixtureOrientation` v1 with exactly `canonical` and `rot180`; any
  enum widening is unreachable by motion gates until transform, schema, and
  review guards are added.
- Define `FixturePose` with slot, orientation, deterministic transform or
  matrix, source fixture checksums, evidence handles, and
  `pose_digest_sha256`.
- Treat operator-provided orientation as a proposal. Motion authority requires
  usable `fixture_pose_orientation:<orientation>:<slot>:<fixture_checksum>` and
  `fixture_upright` claims derived from evidence.
- Define `pose_match_gate` as the single prerequisite gate primitive used by
  registration readiness, home clearance, target authority, offset authority,
  dry/wet gates, plan validation, and execute-time revalidation.
- Add pure transform helpers for canonical-to-installed and inverse mapping;
  the `rot180` formula is `x' = x_dimension - x`, `y' = y_dimension - y`,
  `z' = z`.
- Enumerate pose transforms as yaw-only installs; `fixture_upright` evidence is
  required before using `z' = z`.
- Generate a run-local oriented labware definition variant for non-canonical
  poses. Preserve physical well/target identity (`A1` remains canonical `A1`),
  give the variant a distinct load name such as `_rot180`, and include the
  oriented labware identity/checksum in the pose digest.
- Preserve direction-suffixed access target semantics in the canonical frame:
  `A1_port_x_1p5` means canonical `A1` plus canonical `+X` before the single
  installed-pose transform.
- Restrict the transform to a private oriented-labware compiler boundary.
  Runtime motion code must consume labware coordinates and must not import or
  reapply `canonical_to_installed`.
- Add orientation/pose inputs to CLI, daemon service, daemon HTTP route, daemon
  client, and future MCP route parity tests; no adapter may default silently to
  canonical.
- Scope fixture QC, target-class records, evidence, safety profiles, offset
  records, plan validation, and execute-time revalidation to the same
  `pose_digest_sha256`.
- Make `pose_digest_sha256` stable from a canonical sorted JSON input covering
  slot, orientation, fixture labware identity/checksum, oriented labware
  identity/checksum, `transform_matrix_canonical_to_installed_mm`, and
  `well_identity_policy=preserve_canonical_feature_names_v1`. For canonical
  pose, the oriented-labware identity fields equal the canonical labware
  identity fields and are not empty.
- Make empty or null `pose_digest_sha256` fail closed at motion-gate evaluation;
  version-1 records without pose stay inspectable but cannot satisfy motion.
- Include `pose_digest_sha256` in `FixtureSafetyProfile` inputs and recompute
  `safety_profile_sha256` per pose.
- Quarantine pre-`RG14-pre` pose-unknown evidence from motion gates unless
  accompanied by fresh in-session pose evidence. Supervised compatibility
  records may annotate old evidence for inspection but cannot satisfy motion
  gates.
- Bound OT-2 labware offsets after `loadLabware`; offsets larger than the
  safety-profile jog allowance enter recovery instead of compensating for
  orientation. Execute-time revalidation must re-read and re-bound labware
  offsets immediately before every physical dispatch.
- Invalidate pose claims on door-open, e-stop, recovery-required transition,
  lock lease expiry, or maintenance-run reset. Motion dispatch requires an
  in-session pose claim fresh enough for that dispatch, not merely a claim that
  passed at session start.
- Reject unknown, missing, unsupported, or mismatched pose before target
  authority, offset reuse, home clearance, or motion dispatch.

Review:

- `rot180` transforms by fixture dimensions, not offsets.
- Pose orientation and upright state are evidenced claims, not operator
  self-report.
- `pose_match_gate` is called by every motion-authority gate before local
  predicates run.
- Target-class authority emits a target-authority gate result and cannot hide
  pose matching inside record validation.
- Canonical labware loaded against a `rot180` physical install remains
  no-motion evidence only.
- No cross-orientation target, evidence, safety-profile, or offset reuse.
- Transform is applied exactly once at oriented-labware generation and never
  again in runtime motion.
- Oriented labware has distinct identity and preserves canonical physical well
  names.
- Direction-suffixed access targets keep canonical-frame semantics across pose.
- Version-1 records without pose remain readable for inspection but cannot
  satisfy future motion gates.
- Safety-profile checksums differ between canonical and `rot180` pose for the
  same measured QC inputs.
- Labware offsets are bounded both after labware load and immediately before
  dispatch.
- Route parity covers pose across CLI, daemon service, HTTP client/server, and
  future MCP tools; MCP cannot ship until the pose route-parity test includes
  its schema.

Required tests:

- Digest stability: identical pose inputs produce the same digest; fixture,
  slot, orientation, transform, labware identity, or well-policy changes produce
  a different digest.
- Transform equivalence: every oriented-labware well coordinate equals
  `canonical_to_installed(canonical_well_coordinate)`.
- Double-transform guard: modules that generate oriented labware are the only
  modules allowed to call `canonical_to_installed` for dispatchable target
  coordinates, and the helper is not publicly re-exported outside the pose
  compiler.
- Fail-closed migration: v1 pose-less records load for inspection but cannot
  satisfy `pose_match_gate`, even when all compared records lack pose.
- Safety-profile pose split: same measured QC and target policy under canonical
  versus `rot180` produce different `safety_profile_sha256` values.
- Route parity: CLI, service, HTTP server/client, and future MCP schema carry
  pose fields without defaulting to canonical.
- Execute-time offset bounds: a large labware offset introduced after
  validation but before dispatch blocks and enters recovery.

Brutalist focus:

- Double-rotating targets through both oriented labware and runtime transform.
- Reusing offsets or target evidence across orientation.
- Treating labware offset as rotation.
- Loading canonical labware while the physical fixture is `rot180`.
- Context omits pose while advertising readiness-like progress.
- Pose-less legacy artifacts satisfying each other through empty digest
  equality.
- Operator assertion authorizing pose without a derived pose claim.
- Stale pose claim surviving door-open, e-stop, recovery, or lease expiry.
- Oriented labware sharing canonical load identity and triggering OT-2 cache
  ambiguity.
- Adapter route silently dropping pose and defaulting to canonical.

Resolution:

- Partial `FixturePoseResolution` is implemented for the core authority slice.
  `src/aevum_ot2/core/pose.py` now defines v1 `canonical` / `rot180` pose
  models, stable sorted-JSON pose digests, frame-tagged transform helpers,
  oriented labware compilation with distinct `rot180` load identity,
  pose-orientation/upright claim checks, and `pose_match_gate`. Additive pose
  digest fields now exist on sessions, evidence, fixture QC, target records,
  offsets, and safety profiles. Safety-profile construction, home clearance,
  target authority, offset authority, and local plan validation can consume a
  supplied fixture pose and fail closed when a pose-scoped session or QC record
  omits it. Focused pose tests cover digest stability, transform math,
  direction-suffixed target semantics, double-transform rejection,
  claim/digest binding, pose-scoped safety checks, and cross-pose target/offset
  blocking.

  The session/route/durable-pose slice now persists `FixturePose` JSON under
  the selected state DB's session-artifact root, stores pose orientation,
  digest, and path together on `BridgeSession`, validates start-session
  orientation before robot calls, uploads/loads the canonical or `rot180`
  oriented labware definition during no-motion session init, exposes pose
  metadata in session context, and carries fixture pose plus pose claims through
  daemon service, HTTP server, and daemon client plan routes. Local persistence
  failures after maintenance-run creation now enter the same cleanup path as
  labware upload/load failures instead of stranding a run. Rotated labware
  generation also fails fast on coordinate-bearing definition fields outside
  wells and zero `cornerOffsetFromSlot`.

  The pose-claim/readiness slice now derives
  `fixture_pose_orientation:<orientation>:<slot>:<fixture_checksum>` and
  `fixture_upright` claims from checksummed artifact-backed evidence packets,
  commits those claims through session-scoped evidence transactions, and makes
  registration readiness load the persisted pose plus committed pose claims
  before a pose-scoped session can be ready. Readiness also checks fixture QC
  and target scaffold pose digests against the session pose, ignores
  cross-session pose claims, and exposes the pose gate in `ReadinessResult`.

  The pose-evidence artifact slice now wraps real camera/vision/inspection
  artifacts as schema-v1 `FixturePoseEvidenceArtifact` JSON, binds pose packets
  to the artifact checksum, requires usable artifacts to include a
  checksummed camera capture timestamp from the active session evidence index,
  revalidates nested image/vision checksums when committed pose claims are
  loaded, verifies pose claim-to-packet linkage, and exposes
  `pose-evidence-commit` for session-scoped pose-claim transactions.
  `pose_match_gate` now rejects free-floating pose claims without the expected
  derivation method, usable pose evidence handle, source kind, session, and
  fixture params scope; committed usable pose packets must cite a valid
  `FixturePoseEvidenceArtifact`, the gate revalidates the artifact plus nested
  image/vision checksums and matching session-indexed camera capture metadata
  behind each pose handle, including the session robot URL, and HTTP plan
  routes reject raw pose-claim JSON. Several previously-remaining `RG14-pre`
  software items have since landed: the `move_high_z` command-body translator
  is implemented (OT-1, `src/aevum_ot2/core/dispatch_preparation.py`
  `_move_high_z_command_body`, routed through `_command_body_for_operation`),
  and physical-event invalidation has a landed fail-closed primitive (OT-3,
  `src/aevum_ot2/core/command_journal.py` `detect_foreign_commands` ->
  `CommandHistoryInvalidation`, 2026-06-17, covered by
  `tests/test_command_invalidation.py`). Remaining `RG14-pre` work is now:
  run that path against fresh real slot-5 evidence, future MCP route parity,
  high-Z/low-Z-specific labware-offset handling beyond the current home
  preparation readback, wiring `detect_foreign_commands` into the live backend
  dispatch path, and execute-time pose freshness revalidation. The live-motion
  BACKEND that actually POSTs a translated target command against the physical
  fixture (RG14 proper, behind `motion_backend_enabled`) remains not done.

  The stale-claim invalidation slice now gives session-scoped pose authority an
  explicit time window. `pose_match_gate` rejects claims, handles, and pose
  evidence artifacts that predate the session's current `updated_at` authority
  timestamp, rejects image captures that predate that authority point, rejects
  authority after `lease_expires_at`, and readiness blocks expired no-motion
  sessions before they can become registration-ready. Usable pose authority
  also requires explicit claim, handle, artifact, and image-capture timestamps;
  session-scoped pose claims cannot pass `pose_match_gate` without an explicit
  session authority window, expected evidence index, and session robot URL;
  safety-profile construction requires the matching bridge session when it
  consumes session-scoped pose claims, so stale pose claims cannot be laundered
  into a profile checksum.

Next input:

- Full `FixturePoseResolution` feeds `RG14`.

#### RG14 First High-Z Motion Backend

Input: `AdapterResolution`, full `FixturePoseResolution`, physical readiness
resolution from the print path, all gates passing, and no active recovery
blockers.

Do:

- Add the first bounded high-Z backend behind daemon `execute-next`.
- Limit initial motion to home plus first high-Z target approach.
- Record evidence, command journal entries, and post-step claims.

Review:

- Dry-run tests pass with mocked robot transport.
- Execute-time revalidation runs immediately before dispatch.
- Journal transaction exists before command POST.
- Any ambiguous response enters recovery, not retry.

Brutalist focus:

- Dispatch without journal.
- Home without safety profile.
- High-Z target from stale target policy, stale offset, stale pipette state, or
  stale/mismatched fixture pose.

Resolution:

- `HighZBackendResolution`.

Next input:

- Dry target commissioning graph starts.

### Physical Print Path

This branch can run whenever the fixture becomes available. It does not require
new user approval, but it does require real physical inputs. Missing physical
inputs resolve as blockers, not as chat questions.

```text
PF0 print completed
  -> PF1 support/adhesion cleanup
  -> PF2 measured bounds and defect inspection
  -> PF3 real FixtureQcRecord
  -> PF4 installed fixture camera/image evidence
  -> PF4a installed pose record: slot 5, rot180, evidence-linked with pose claims
  -> PF5 fresh no-motion session on aevum with matching pose
  -> PF6 target-class scaffold from that session and pose
  -> PF7 readiness check returns registration_ready=true and motion_allowed=false
  -> PF8 close no-motion session unless RG14 is ready to consume it immediately
```

Each `PF*` node resolves with a concrete artifact path, measurement value,
evidence handle, session ID, readiness result, or blocker. Physical blockers do
not stop software graph progress unless their artifact is the declared input to
the next software node.

## Current Do -> Review State

### Completed In Current Cycle

- Added initial `CP-pre0` regression anchors in
  `tests/test_no_motion_invariants.py`.
- Passing anchors now prove complete registration readiness and session context
  remain no-motion, unknown plan operations fail closed at model validation, and
  the daemon execution boundary still sends no robot command even when the
  validation layer would allow future low-Z motion under a daemon flag.
- Initial expected-failure attack anchors tracked missing promoted offset
  authority for low-Z (`D7`) and missing home-clearance (`D8`); both are now
  resolved by `RG3` and `RG4`.
- `BridgeSession.kind` and `BridgeSession.state` now validate against typed
  enums. Unknown session kinds/states fail at the model boundary.
- No-motion recovery reports now carry explicit non-destructive dispositions:
  `no_local_session`, `recovered_closed`, `unresolved_recovery`, and the future
  supervised path `supervised_override_closed`.
- Evidence index appends now take a per-index lock, session-scoped index paths
  are available, and no-motion session lifecycle evidence records to the
  session index when a session exists.
- Persisted and semi-persisted schemas are inventoried in
  `docs/engineering/schema_inventory.md`, with owners, migration policy,
  retention rules, and current fail-closed gaps.
- `EvidenceHandle`, `EvidencePacket`, `EvidenceClaim`, and `GateResult` now
  exist as pure local models. Fixture QC legacy records can derive explicit
  `legacy` quality claims with checksummed file handles.
- Fixture QC and registration compatibility gates now wrap those claims while
  keeping `motion_allowed=false`; `ReadinessResult` includes the registration
  gate result without changing readiness semantics.
- Duplicate plan step IDs are now rejected before execution instead of remaining
  an expected-failure attack anchor.
- `CommissioningObservationRecord` has been renamed/demoted to
  `LegacyImageEvidenceRecord`; the active CLI command is
  `legacy-image-evidence-record`, and old `observation_id` /
  `human_observation` JSON keys remain load-compatible.
- Follow-up Brutalist review found and this cycle fixed three local issues in
  that demotion: CLI output is now timestamped rather than singleton,
  referenced image/vision files must exist for validation, and generated legacy
  IDs include fixture checksums and supervised notes.
- `RG1 TargetPolicyResolution` is complete. `src/aevum_ot2/core/targets.py`
  now defines `TargetGeometry`, `TargetPolicy`, typed Z tiers, typed required
  claims, explicit predecessor policy, first-pass eligibility, and boundary /
  mat-patch flags for every declared target class.
- RG1 attack coverage now proves offset low-Z targets require matching offset
  high-Z predecessors rather than center evidence, boundary targets cannot be
  first-pass targets, and mat-patch wet requires both mat-patch dry and no-mat
  wet predecessors.
- `RG2 SafetyProfileResolution` is complete. `src/aevum_ot2/core/safety.py`
  now defines `FixtureSafetyProfile`, measured/conservative fixture bounds,
  conservative high Z, dry/wet Z floors, max registration jog, symbolic
  forbidden zones, boundary target handling, target-policy digest, scoped source
  claim IDs, and `safety_profile_sha256`.
- RG2 attack coverage now proves generated labware identity alone cannot create
  a passing safety profile, missing measured QC blocks low-Z/wet/home-clearance
  consumers, boundary targets default to blocked until inner margin exists, and
  safety profile checksums change when measured bounds or target policy inputs
  change.
- A local RG2 adversarial review found one concrete issue before resolution:
  caller-supplied fixture QC claims were true/false checked but not scoped to
  the fixture identity. The safety builder now blocks cross-fixture claims and
  duplicate claim types.
- `RG3 OffsetAuthorityResolution` is complete. `OffsetRecord` now carries
  `authority_state`, `offset_record_id`, `safety_profile_sha256`, and
  `target_policy_digest_sha256`; old records default to `proposed`.
- RG3 attack coverage now proves `offset_registry_record="not-yet-registered"`
  blocks low-Z validation, proposed offsets cannot satisfy promoted authority,
  and promoted offsets must match robot serial, server/API version, fixture
  checksums, slot, pipette, tiprack, target class, target policy digest, and
  `safety_profile_sha256`.
- A local RG3 adversarial review found one concrete issue before resolution:
  the offset record was scoped to the session, but the target-class record that
  supplied the offset reference was not independently scoped to that same
  session. The offset authority gate now blocks target-record/session
  mismatches, duplicate offset references, and empty safety checksums.
- `RG4 HomeClearanceResolution` is complete. `home_clearance_gate` now requires
  a current `FixtureSafetyProfile`, `ready_no_motion` session state, and an
  explicit recovery disposition before `home` validation can pass.
- RG4 attack coverage now proves registration readiness alone cannot authorize
  `home`, recovery-required sessions cannot pass home-clearance, unresolved or
  missing/unknown recovery dispositions fail closed, stale safety-profile scope
  blocks, and daemon execution still sends no robot command after a passing
  home-clearance validation.
- `RG5 PlanValidationV2Resolution` is complete. Motion step validation now emits
  structured `GateResult` entries for home-clearance, first high-Z, low-Z dry,
  wet, and promoted offset authority. `move_high_z` cannot validate from
  registration readiness alone, malformed motion target inputs still emit
  blocking gate results, and unsupported motion operations such as `set_offset`
  fail closed even when daemon motion is enabled.
- `RG6 EvidenceTransactionResolution` is complete. `core.evidence` now commits
  packet/claim files with checksum sidecars, fsync-backed writes, committed
  manifests, indexed manifest checksums, fail-closed committed-claim loading,
  mixed-session rejection, and recovery scans for orphaned, unindexed, missing,
  tampered, or path-escaped transaction state.
- `RG7 SchemaResolution` is complete for durable schema boundaries. `core.schema`
  now provides typed schema-version errors, and loaders reject missing or
  unknown versions for records, evidence indexes, evidence transaction
  manifests, packet/claim artifacts, offset registries, plan fragments, and gate
  summaries. Bridge session SQLite payload JSON now goes through the same
  version boundary before session state can feed gates. Gate-significant nested
  records must carry explicit v1 schema versions, and evidence transactions are
  bound to the active root, active index, artifact IDs, and session scope before
  claims load. Transaction claims must link to packets in the same transaction,
  and safety-profile checksums are recomputed by gates before use. Migration
  coverage proves widened old offset records default to `proposed`, old
  image-evidence aliases load only through the legacy adapter with compatibility
  telemetry, and legacy evidence events do not become committed claims.
- `RG8 LockResolution` is complete. New bridge ownership now uses
  `acquire_lock` with a SQLite `BEGIN IMMEDIATE` transaction around the
  read/decision/write path. Non-terminal locks block acquisition even after
  lease expiry, terminal locks can be replaced, and no-motion session init exits
  on lock conflict before creating a robot maintenance run.

### Review Findings

- The strongest current invariant is execution-local: physical operations still
  return `not_implemented` with `motion_commands_sent=false` and no
  `executed_step_id`.
- The weakest current invariant is now the pre-motion authority gap: target and
  offset authority have strong compatibility gates, but full transaction-backed
  promotion/write lifecycles are not yet implemented for real physical records.
- The next slice should therefore finish transaction-backed target/offset
  authority or wait for the physical fixture branch before adding a motion
  backend.
- Brutalist CLI review for RG1 failed twice at the tool layer. Local adversarial
  review found one concrete issue before resolution: raw required-claim strings
  were typo-prone. They are now typed with stable string values.
- Brutalist CLI review for RG2 also failed at the tool layer with zero critic
  output. The local RG2 review fixed the scoped-claim trust-boundary issue and
  left no known RG2 blocker.
- Brutalist CLI review for RG3 failed at the tool layer with zero critic output.
  The local RG3 review fixed the target-record/session scoping issue and left no
  known RG3 blocker.
- Brutalist CLI review for RG4 succeeded and identified one accepted blocker:
  recovery disposition was optional and unknown string values failed open. The
  gate now requires an explicit disposition, rejects unknown strings, blocks all
  non-`ready_no_motion` states, and has validation/execution-boundary coverage.
- Brutalist CLI review for RG5 succeeded and identified two accepted blockers:
  low-Z/wet predecessor checks were still reason-only, and malformed target
  inputs could produce no gate result. Validation now emits low-Z/wet gates,
  malformed-input gates, failed-target blockers inside gates, and unsupported
  motion operation blockers.
- Brutalist CLI review for RG6 succeeded and identified accepted trust-chain
  blockers: manifest checksums were optional, artifact paths were not anchored
  to transaction directories, writes lacked fsync, and mixed-session
  transactions were not rejected. The final RG6 review found no remaining
  blockers after those fixes.
- Brutalist review for RG7 identified accepted blockers after the first pass:
  bridge-session SQLite payloads bypassed schema-version checks, nested
  authority-bearing records could omit `schema_version`, and committed evidence
  manifests were not sufficiently bound to the active root/index/artifact scope.
  A final review also identified packetless transaction claims and tampered
  safety-profile objects as cheap RG7-adjacent hardening wins. Those are now
  fixed with focused tests. One scope boundary remains deliberate: full
  operation-name shims belong to `RG11`, not to schema loading, and target-record
  evidence/claim handle cleanup was deferred to `RG9`.
- Brutalist review for RG8 found no concrete acquisition blocker after the CAS
  implementation. Local review keeps one deliberate conservative behavior:
  expired non-terminal locks are not stolen; recovery must reconcile them.
- Brutalist review for RG9 confirmed no raw legacy target-field path remained,
  then identified accepted hardening items: embedded evidence needed path and
  checksum verification, claim-embedded handles needed to match record handles,
  and duplicate target records needed to block instead of collapsing by last
  writer. Those fixes now have focused regression tests. Full transaction-backed
  target and offset authority remains a pre-live-motion requirement and feeds
  the execute-time revalidation work in `RG10`.
- Brutalist review for RG10 identified accepted hardening items after the first
  pass: robot identity, API identity, pipette model/ID/tip length, session lease,
  and last-command matching were too soft, and `active_no_motion` was an
  ambiguous execution lock state. The guard now requires complete session and
  live identity, fresh session and lock leases, a motion-capable lock state,
  matching last command, and matching live pipette details before the current
  `not_implemented` motion boundary. The remaining TOCTOU risk is deliberately
  assigned to `RG12` command journaling and reconciliation.
- Final RG10 review found one accepted immediate blocker after that hardening:
  the session reloaded after validation still needed execute-time state
  validation. Revalidation now checks reloaded `ready_no_motion` state and
  `motion_allowed=false`, invalid pipette mounts fail at model load, protocol
  API list parsing is stricter, and regression tests cover reloaded closed
  sessions, missing gate results, invalid mounts, and lock owner mismatch.
- RG11 local review closed the plan-payload ambiguity slice. The shared plan
  parser now rejects unknown step fields, unknown parameters, path-like evidence
  filenames, raw coordinates, raw robot-server endpoints, raw command bodies,
  arbitrary Python payloads, and ignored `target_class` fields before daemon
  validation or execution sees them. Context now advertises `capture_evidence`,
  and legacy `capture_observation` is a compatibility-only input alias.
- Brutalist RG11 review found no remaining raw-coordinate or legacy-operation
  blocker in the typed plan core, but identified accepted boundary hardening:
  mutable in-process plan objects needed reparsing at service/core boundaries,
  context advertised a non-plan readiness operation, dormant `record_evidence`
  paths needed path-escape checks before future unblocking, plan HTTP envelopes
  needed to be explicit, and unauthenticated daemon exposure/oversized bodies
  needed tighter defaults. Those are now covered by focused regression tests.
- Final RG11 review confirmed those closures. Follow-up hardening also rejects
  chunked request bodies and excessive JSON nesting, and context now lists
  dormant `record_evidence` as blocked rather than hiding it from agents. Route
  parity for future HTTP/MCP motion inputs, especially offset registries and
  fixture safety profiles, is assigned to `RG13` before any networked motion
  adapter can be considered motion-capable.
- RG12 local review closed command ambiguity for the future dispatch boundary.
  Journal unavailability blocks dispatch; timeout or unavailable history enters
  recovery; duplicate command keys are non-idempotent; mismatched command
  history cannot infer success; and command responses without a matching
  journal entry cannot promote authority.
- RG13 local review closed adapter drift for the current package. HTTP and
  daemon-client plan routes carry safety-profile, offset-registry, and recovery
  disposition inputs, while adapter boundary tests prevent raw OT-2 transport or
  raw robot-control tools from becoming agent-facing motion paths.
- Brutalist RG12/RG13 review found accepted journal hardening: queued/running
  command history must not be terminal success, duplicate command keys need a
  pre-dispatch local uniqueness guard, wrong-run or incomplete paginated history
  must fail closed, recovery-required reconciliation needs a persistence helper,
  and future command POSTs need a journaled dispatch chokepoint. A second review
  found and closed the remaining RG12/RG13 blockers: post-dispatch journal write
  failure now enters recovery, session-init ambiguous reconciliation stays
  recovery-required even after confirmed cleanup, cleanup deletes require
  post-delete absence confirmation, command/history route mismatches block before
  POST, recovery requires complete command history, and GET context record paths
  are validated like POST plan paths. Brutalist final review cleared RG12/RG13.
  Remaining RG14 blockers are outside this slice: owner/auth for networked
  motion, per-step dispatch reservation/CAS, and production-grade HTTP serving
  before remote exposure.
- Slot-5 fixture evidence changes the next motion precondition: the physical
  fixture is usable for camera fiducials only in a `rot180` installation, so
  `RG14-pre` now owns fixture pose, oriented labware, and cross-orientation
  record/offset blocking before `RG14`.
- Brutalist RG14-pre review identified accepted pose-authority blockers:
  missing single `pose_match_gate`, operator-declared orientation without
  derived pose/upright claims, unspecified pose digest inputs, ambiguous
  well-name semantics, possible oriented-labware identity collision, double
  transform risk, safety-profile reuse across orientation, stale pose claims,
  pre-pose evidence laundering, large labware offsets masking orientation, and
  adapter route drift. The RG14-pre contract now gates all of these before
  first high-Z motion.
- Brutalist RG14-pre second pass found accepted spec-precision blockers:
  divergent transform digest field names, undefined literal well-identity
  policy, direction-suffixed access-port frame ambiguity, missing target-class
  authority gate result, labware-offset TOCTOU before dispatch, unbounded
  supervised compatibility escape, canonical-pose oriented-labware digest
  fields, open-ended orientation enum widening, static-only double-transform
  enforcement, silent physical tamper between dispatches, and future MCP route
  drift. The contract now names canonical digest keys and literals, keeps
  supervised compatibility inspect-only, revalidates offsets at dispatch, and
  requires fresh in-session pose claims for motion.
- RG14-pre implementation review found accepted blockers in the first code
  slice: public double-transform ambiguity, two labware hash spaces,
  pose-claim digest binding missing, pose-scoped authority optional by caller,
  safety profile accepting pose without pose claims, home clearance pose
  blindness, and pose-scoped QC producing a pose-blank safety profile. The core
  slice now closes those issues with frame-tagged points, one canonicalized
  labware hash path, claim pose-digest checks, required pose objects for
  pose-scoped gates, pose claims in safety/home gates, and regression tests.
- RG14-pre session/route review found accepted blockers in the durable pose
  wiring slice: local pose/session writes could fail after maintenance-run
  creation without cleanup, tests leaked pose JSON into the repo root, and bad
  orientations were rejected only after robot status calls. The session slice
  now scopes artifacts beside the selected state DB, validates orientation at
  the boundary, fails fast on unsupported rotated labware coordinate fields,
  and routes local persistence failures through robot cleanup/recovery.
- RG14-pre pose-claim/readiness work now closes the software-only portion of
  evidence-derived pose authority: orientation/upright claims are derived from
  durable evidence packets, transaction claim loading feeds readiness, and
  pose-scoped fixture QC/target records must match the active session pose.
- RG14-pre pose-evidence artifact work now gives the real slot-5 evidence path
  a schema-v1 artifact boundary and CLI transaction commit. Usable claims still
  require a fresh active pose-scoped session plus real artifact checksums and a
  non-empty inspection note. The follow-up Brutalist pass found raw pose claims
  could still bypass artifact packetization; the shared pose gate and evidence
  transaction link checks now require pose claims to carry the expected
  packet-derived method and matching usable pose evidence handles. A final
  pass found raw pose packets and HTTP route-injected claim JSON were still a
  weaker trust path; committed pose packets now require the
  `FixturePoseEvidenceArtifact` schema, `pose_match_gate` revalidates the
  artifact, nested image/vision checksums, and active-session camera capture
  event behind each pose evidence handle, and HTTP plan routes reject raw
  `pose_claims`.
- RG14-pre stale-claim invalidation now blocks expired session leases and
  claims/artifacts/handles created before the session's active authority point.
  Door-open, e-stop, and live maintenance-run-reset event ingestion remains a
  physical-event source problem; the gate accepts the invalidation timestamp
  once such events are recorded.
- Motion-approval review accepted the next dispatch-boundary hardening: missing
  `MotionApproval` now blocks plan-level `allowed` and `motion_allowed`, approval
  TTL is capped, required session/lock states are fixed to
  `motion_commissioning_armed`, approval IDs are recomputed from a full-scope
  digest, plan digests ignore non-semantic notes, `not_implemented` no longer
  reports an executed step, and legacy maintenance spikes abort when an active
  bridge lock exists. The remaining live-motion blocker is no longer a
  permissive validation path; it is the atomic arm/mint/consume/dispatch
  protocol. The arm/mint/consume portion is closed by RG14-arm; pre-dispatch
  reservation is closed by RG14-dispatch.
- RG14-arm implementation now closes the arm/mint/persist/consume part of that
  protocol. The daemon arm route rejects caller-supplied approvals, requires a
  pre-arm validation blocked only by missing approval, re-reads session and lock
  under SQLite `BEGIN IMMEDIATE`, persists one armed `MotionApprovalRecord`,
  transitions session/lock to `motion_commissioning_armed`, and consumes the
  record exactly once at the current no-motion backend boundary. The follow-up
  hardening pass removed duplicated session/lock DDL from the commissioning
  module, added SQLite busy timeout and a partial unique index for one armed
  approval per session, made approval insert collisions fail instead of
  overwriting consumed audit rows, revoked expired armed approvals before
  re-arm, checked session/lock lease freshness during approval validation, and
  blocked approval TTLs that outlive the remaining lease. The final review gate
  also moved authoritative timestamps to after the SQLite write lock is acquired,
  capped route-level approval TTL input before `timedelta` construction,
  translated SQLite busy errors to typed HTTP errors, blocked daemon validation
  from reporting `motion_allowed=true` for unpersisted approvals, and made direct
  approval consumption block cleanly when the lock row is missing. The last
  narrow gate found and closed one cleanup rollback bug: stale approval
  revocation/disarm now commits even when a re-arm attempt remains blocked by an
  expired lease. RG14-dispatch then added a durable pre-dispatch
  `MotionDispatchReservation` written in the same transaction as approval
  consumption; reservation conflicts roll back consumption, and the execution
  result exposes the reservation while preserving `motion_commands_sent=false`
  and post-consumption `motion_allowed=false`. The reservation artifact now
  rejects backend/journal state, requires a consumed approval state from the
  transaction caller, and fails closed when row columns and payload JSON diverge.
  RG14-prepare then added live maintenance-run/labware/offset/history readback
  and a no-post home command-journal preparation. Preparation failure leaves the
  approval armed with no reservation or journal row; preparation success commits
  approval consumption, reservation creation, session/lock disarm, and
  `CommandJournalEntry(state=prepared)` in one SQLite transaction. RG14-backend
  then added a separate `motion_backend_enabled` path for prepared `home`: it
  repeats live readback, requires the fresh preparation to match the consumed
  preparation, posts through the journaled command helper, reconciles command
  history, and updates session/lock last-command authority only after completed
  latest-command reconciliation. The backend also rechecks session/lock leases
  immediately before POST, marks the journal row `dispatching` before the HTTP
  request, moves no-post backend failures to recovery without corrupting
  last-command fields, and requires a local HTTP auth token when enabled through
  the daemon. The default service still returns `not_implemented` without a
  POST when the backend flag is disabled. High-Z target command-body
  translation is now landed (OT-1): `_move_high_z_command_body` in
  `src/aevum_ot2/core/dispatch_preparation.py` emits the `center_high_z`
  `moveToWell` command body, routed through `_command_body_for_operation`
  alongside the landed `move_low_z` (OT-4) and `liquid_handling` (OT-5)
  translators. Physical-event invalidation is also landed (OT-3) as the
  fail-closed `detect_foreign_commands` whole-history scan in
  `src/aevum_ot2/core/command_journal.py`, and post-motion high-Z evidence is
  landed (OT-6) in `src/aevum_ot2/core/high_z_motion_evidence.py`. The
  genuinely-still-open part is the live-motion BACKEND that actually POSTs a
  translated target command against the physical fixture (RG14 proper, the
  `motion_backend_enabled` path in `server.service.execute_next`): it must run
  fresh real slot-5 readback, wire `detect_foreign_commands` into the dispatch
  cycle, and dispatch the prepared high-Z command — no robot target motion has
  been dispatched.

## Immediate Next Work

Continue through the `RG*` graph above. The following software nodes have
landed against verified code ground truth:

```text
DONE high-Z target command-body translation (OT-1, dispatch_preparation._move_high_z_command_body + _command_body_for_operation routing)
DONE physical-event invalidation primitive (OT-3, command_journal.detect_foreign_commands, 2026-06-17)
DONE post-motion high-Z evidence (OT-6, high_z_motion_evidence.py)
```

The next unresolved software nodes are:

```text
RG14-pre execute-time pose freshness checks
RG14-backend live high-Z target-motion BACKEND that POSTs the translated command (RG14 proper / motion_backend_enabled), including wiring detect_foreign_commands into the dispatch cycle
```

The next physical branch nodes are:

```text
PF5 fresh slot-5/rot180 no-motion authority before any live arm attempt
PF6 post-home and post-high-Z evidence after the first physical motions
```

There are no active expected-failure attack anchors. The next software risk is
the post-home target-motion path: although high-Z target translation (OT-1) and
physical-event invalidation (OT-3) have landed, fresh real slot-5 evidence
still needs to be refreshed before physical readiness can pass, and the
live-motion backend that POSTs a translated target command (RG14 proper) still
needs execute-time pose freshness, `detect_foreign_commands` wired into the
dispatch cycle, target verification, and offset promotion before any target
command can safely be prepared and posted. No robot target motion has been
dispatched.

No live robot action is required for this work.
