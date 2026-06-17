# Evidence Model

## Purpose

Aevum should not model autonomy around images. Images are one evidence source.
The bridge needs a broader evidence model that can support physical
measurements, robot state, command history, generated artifact identity, camera
captures, vision analysis, and supervised commissioning notes.

The core abstraction is:

```text
evidence source -> evidence packet -> derived claim -> gate decision -> record/readiness state
```

Agents should normally see compact gate state and evidence handles. They should
not be asked to infer safety from raw images, command logs, or free text.

## Layers

### Evidence Source

An evidence source is where a fact came from:

- generated CAD, params, labware JSON, and checksums,
- robot health, API version, pipette state, and run state,
- maintenance-run or protocol-run command responses,
- command history reconciliation,
- camera still captures,
- image-analysis results,
- physical fixture measurements from calipers or inspection,
- offset measurements,
- supervised commissioning notes.

Camera evidence is important because it can become a machine observation
channel, but it should not be the only evidence class.

### Evidence Packet

An evidence packet is an immutable indexed artifact. It should include:

- evidence ID,
- source kind,
- created time,
- session ID when available,
- robot serial and API/server version when available,
- fixture identity and checksums when relevant,
- operation or command ID when relevant,
- artifact path or inline structured payload,
- provenance, such as tool, operator, agent, or robot endpoint,
- quality state, such as `usable`, `ambiguous`, or `failed`.

Evidence packets belong under `data/measurements/` for physical work and must be
referenced by handles in agent context.

Current packet persistence uses evidence transactions. A transaction writes
packet and claim JSON files with checksum sidecars, fsyncs the writes, stores a
committed manifest, and indexes the manifest checksum. Claim loaders accept only
indexed, committed, checksum-valid transactions whose artifact paths remain
inside the transaction directory. Recovery scans report orphan, unindexed,
missing, tampered, or path-escaped transaction state without promoting claims.
Mixed-session transactions are rejected. Unknown schema versions in transaction
manifests, packets, claims, or nested evidence handles fail closed before claims
are returned to gates. Claim loading also binds indexed manifests to the active
transaction root and active evidence index, checks that artifact IDs match the
packet/claim payload IDs, requires each transaction claim to reference packet
handles in the same transaction, and rejects session-inconsistent artifacts.

### Claim

A claim is a machine-readable assertion derived from one or more evidence
packets. Examples:

- `fixture_dimensions_within_tolerance`,
- `fixture_visible_in_slot`,
- `guide_holes_open`,
- `no_active_protocol_runs`,
- `labware_definition_uploaded`,
- `load_labware_succeeded`,
- `high_z_target_centered`,
- `low_z_dry_target_passed`,
- `command_history_reconciled`.

Claims should carry source evidence handles, method, confidence or tolerance,
and a timestamp. A claim is not automatically a permission to move.

The current implementation has a compatibility adapter for `FixtureQcRecord`.
It derives fixture QC claims with `quality=legacy`, records the legacy file path
and checksum when available, and allows those claims only through the fixture-QC
compatibility gate. This keeps the old record useful for registration readiness
without making hand-edited booleans indistinguishable from future packet-derived
claims.

### Gate

A gate is a validator predicate over session state and claims. Examples:

- registration readiness,
- fixture QC readiness,
- first high-Z motion readiness,
- promoted offset authority,
- low-Z dry readiness,
- wet workflow readiness,
- recovery readiness.

Gate results are what agents should use for planning context: pass/fail,
blocking reasons, missing claims, and allowed next operations.

Current gate results default `motion_allowed=false`. Registration, fixture-QC,
and promoted-offset compatibility gates can pass while still refusing motion.
Home-clearance now exists as an input gate over safety profile, session state,
and explicit recovery disposition, and it also keeps `motion_allowed=false`.
High-Z, low-Z, wet, and recovery gates remain separate work and must not be
implied by registration readiness.

The current promoted-offset authority gate can pass as an input gate while still
returning `motion_allowed=false`. It requires an `OffsetRecord` with
`authority_state=promoted`, a matching target-class record reference, the active
session identity, the current `FixtureSafetyProfile`, and exact scope across
robot serial, server/API version, fixture checksums, slot, pipette, tiprack,
target class, target-policy digest, and `safety_profile_sha256`.

The current home-clearance gate requires a current `FixtureSafetyProfile`, a
`ready_no_motion` session, and an explicit recovery disposition. Missing,
unknown, `no_local_session`, or `unresolved_recovery` dispositions fail closed.
Passing home-clearance allows validation to reach the daemon execution boundary,
where physical motion still returns `not_implemented` until the live backend is
implemented and revalidated; this boundary does not set `executed_step_id` or
advance the plan cursor.

Plan validation now includes gate results on motion step validation entries.
Malformed motion target inputs still emit blocking gate results, so agents can
read structured gate state rather than inferring authority from prose reasons.
Motion-step gate entries can pass locally, but plan-level
`PlanValidationResult.allowed` and `motion_allowed` remain false unless a
schema-valid, daemon-persisted `MotionApproval` binds the exact plan step,
semantic plan digest, session, robot, installed pose digest, safety profile,
capped expiry window, and motion-armed session/lock state. The arm transition
is a local state transaction, not evidence: it can only mint an approval from a
validation result blocked solely by missing approval, and execute consumes the
persisted record exactly once. The transaction enforces one armed approval per
session, revokes expired armed approvals before re-arm, and refuses approval
windows that outlive the active session or lock lease. Daemon validation and
execute-time dispatch preparation both check that a supplied approval is the
persisted armed record before using `motion_allowed=true`. The backend-disabled
execution path first performs live maintenance-run, loaded-labware,
labware-offset, and command-history readback. If readback or command-body
preparation fails, the approval remains armed and no reservation or command
journal row is written. If preparation passes, the daemon writes a
`MotionDispatchReservation(state=reserved_pre_dispatch)` and a
`CommandJournalEntry(state=prepared)` in the same transaction that consumes the
approval and disarms session/lock. Validation artifacts, unpersisted approval
JSON, pre-dispatch reservation records, and prepared journal rows must not be
treated as physical dispatch authority. Reservation loaders fail closed on
row/payload mismatch, reservations may name only the reservation-derived
prepared command journal ID, and reservation payloads cannot claim a posted
robot command. The explicitly enabled backend can POST only after fresh readback
regenerates the same preparation and journal identity, a final session/lock
lease check still passes, and the command journal row is advanced to
`dispatching`. Command-history reconciliation must match the latest command
before session/lock last-command authority is updated. Only `home` currently has
a command-body translator.

Persisted or replayed gate summaries are also schema-versioned. The loader
accepts only `GateResult.schema_version=1` and rejects unknown nested evidence
handle versions, so a future gate result cannot be interpreted under stale
semantics.

### Fixture Safety Profile

`FixtureSafetyProfile` is a derived input for future motion gates, not a gate
and not a motion authorization. It joins generated artifact identity with real
post-print measurements and scoped fixture QC claims.

The current builder refuses to create a passing profile from generated labware
dimensions alone. A valid profile requires:

- matching fixture load name and params/labware checksums,
- measured `x_bound`, `y_bound`, and `z_bound` values from `FixtureQcRecord`,
- fixture QC claims scoped to the same fixture identity,
- no duplicate claim types,
- target-policy inputs for boundary target handling.

The profile records measured bounds, conservative bounds, conservative high Z,
dry and wet Z floors, registration jog size, symbolic forbidden zones, boundary
target handling, target-policy digest, source claim IDs, and
`safety_profile_sha256`. Missing or stale profile inputs block low-Z, wet, and
home-clearance consumers. Home-clearance and promoted-offset authority gates
recompute the profile digest before use, so a profile whose checksum no longer
matches its contents cannot satisfy those inputs.

### Domain Record

Domain records summarize evidence and claims for durable workflow state:

- `FixtureQcRecord`,
- `TargetClassVerificationRecord`,
- `OffsetRecord`,
- future recovery or run records.

Records should reference evidence handles rather than embedding large payloads.
They are not raw evidence stores; they are durable workflow state derived from
evidence.

Target-class records are now authority-bearing only through handles and claims.
A passed result is necessary but not sufficient: predecessor gates require a
usable evidence handle and a true usable
`target_class_verified:<target_class>` claim scoped to the active session and
fixture identity. The handle path must exist, its checksum must match, and any
handle embedded in the claim must match the record handle rather than providing
a second conflicting copy of the evidence identity. Duplicate target records
for the same class block plan validation. Legacy `camera_images`,
`vision_results`, and `commissioning_observation` aliases can still be read for
compatibility, but writers do not emit them and their presence blocks
target-class authority.

The former image-shaped commissioning observation record has been renamed in
code to `LegacyImageEvidenceRecord`. It is a compatibility adapter for image
paths, vision-analysis JSON, and supervised commissioning notes. It can read old
`observation_id`/`human_observation` keys, but new records serialize as
`legacy_record_id`/`human_note`, and validation rejects any attempt to use the
record as a motion gate. When old aliases are loaded through the adapter, the
record receives a compatibility note so downstream context can distinguish
legacy load paths from native v1 records. The legacy adapter also validates that
referenced image and vision-result files still exist; a non-empty path string is
not enough evidence.

### Schema Boundary

Durable JSON artifacts are loaded through schema-version checks rather than raw
Pydantic defaults. Missing or unknown root versions fail with
`SchemaVersionError`; gate-significant nested models also need explicit v1
schema versions. Evidence transaction recovery emits blockers for
unknown-version manifests, packets, claims, and nested evidence handles.

The current explicit load boundaries cover:

- fixture QC, target-class, and legacy image-evidence records,
- evidence indexes and evidence transaction artifacts,
- offset registries and widened old offset records,
- plan fragments at file and HTTP boundaries,
- bridge session SQLite payload JSON,
- replayed gate result summaries.

Legacy evidence events remain append-only compatibility logs. They are not
converted into committed claims, so an old event payload that looks like a claim
cannot satisfy a future motion gate.

## Agent Context

Agent context packs should expose:

- current session state,
- active gate results,
- missing required claims,
- compact evidence handles,
- allowed next operations,
- blocked operations with reasons.

They should avoid dumping raw command histories, full images, or full evidence
payloads. Agents can fetch specific evidence artifacts explicitly when needed.

## Naming

Prefer evidence-oriented operation names:

```text
capture_evidence
record_evidence
evaluate_gates
get_evidence_summary
```

Avoid making `observation` synonymous with camera image. If the term
`observation` is used, it should mean any observed evidence source, including
physical measurements and robot state, not just vision.

The current CLI command for this compatibility surface is
`legacy-image-evidence-record`; `observation-record` is no longer the active
command name. Its default output is timestamped under
`data/measurements/legacy_image_evidence/` instead of rewriting one singleton
record.

## Design Rule

No single evidence packet should authorize motion. Motion authority comes from a
gate decision that joins evidence-derived claims with session state, recovery
state, fixture identity, robot identity, and the approved plan.
