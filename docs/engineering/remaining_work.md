# Remaining Work Backlog

## Purpose

The canonical, prioritized enumeration of all remaining work to take Aevum to a
working production prototype, organized for execution as do→review cycles. It is
a synthesis across the six work tracks, grounded in the existing planning docs
(`implementation_trajectory.md`, `task_graph.md`, `readiness_contract.md`,
`row_coupon_cycle_log.md`) and this session's observer/platform work. Every item
is tagged by **addressability**:

- **A — workflow-addressable now:** CAD / code / docs / test / design-analysis,
  drivable by a do→review cycle with no hardware.
- **B — needs hardware:** physical print / build / measurement.
- **C — needs a user decision:** an engineering choice only the builder can make
  (most default to a conservative branch until one measurement forces otherwise).

This doc is the execution queue. As cycles land, fold their results into the
owning planning docs (`task_graph.md` gates, `row_coupon_cycle_log.md` RP cycles,
`decision_log.md`).

Cross-branch dependency and review structure is tracked in
`docs/engineering/realization_hypergraph.md`. This file remains the canonical
item inventory; the hypergraph owns joins, authority boundaries, and stop
conditions.

## Progress log

- **2026-09-23 — observer optics/thermal doc pass** (docs only; no `src/`, `tests/`, or
  `cad/*.json` touched, suite left at 501 passed / 0 failed). Books the open work surfaced by the
  session's measured geometry/optics/thermal review; closes nothing. New items: **OP-B20**
  (measure G_obj-ambient — the 50 mW/K estimate the whole thermal gate rests on), **OP-B21**
  (objective barrel OD 9-11 mm back from the tip, which sets the reachable-well inset), **OP-B22**
  (borosilicate Raman background through the plate bottom), **OC-A16** (does the carriage body
  thread the 117.4 mm leg corridor), **OC-A17** (`covered_well_count` reports 384 where the
  optically reachable set is 128), **OC-A18** (two `aevum_smis/manifest.py` recommendations
  recorded, deliberately not applied), **SM-4.5** (the throughput / sampling-policy gap), and
  **IN-C10** (the water-immersion amendment decision, staged as an open proposal in
  `docs/knowledge/materials_strategy.md`).

- **2026-06-18 — remaining A-queue batch** (11 items, parallel workflow + do→review→fix per item,
  then orchestrator-integrated shared files): **OT-7** MCP agent adapter (policy-allowlisted, routes
  via DaemonClient, no motion authority), **OT-8** MCP/HTTP route-parity / no-silent-canonical-default
  ship-gate, **OT-10** `ot2_abort_or_recover` facade + recovery runbook, **OT-11** task-graph
  reconciliation (translator/evidence/invalidation DONE; live-POST backend tail preserved), **OT-12**
  commissioning operability layer over the existing daemon (dry-run default, never auto-arms),
  **OP-P3/P4/P5/P8** observer protocol docs (condensation purge, ADXL345 settle, kinematic-dock
  repeatability, Gate-6 evidence-row schema), **OC-A8** 40×40@25 mm red-case test (empirically pinned),
  **OC-A13** RH6/RH15/RP5 OC-A fold. Reviews ship-it (OP-P3 had a must-fix on the condensation warning
  band → fixed; OT-10's boundary-test snippet was vacuous → orchestrator replaced it with an AST check).
  661 across the non-CAD surface + OC-A8 green, ruff clean. Then **OT-4 follow-up** (`core/well_geometry.py`):
  the real checksum-anchored per-well access bounds, wired into the descent gate as a reachable fail-closed
  bounds check (replacing the envelope-top misuse); emission still gated on a measured dry depth (B). Review
  verdict ship-it, no findings; 669 across the non-CAD surface, ruff clean. This closes the entire
  software/CAD-addressable A-queue; the remainder is B (hardware/measurement) or C (product decision).
- **2026-06-17 — OT-1, OT-3, + backlog reconciliation** (do→review→commit).
  - **OT-1** (transaction-backed offset authority): producer pipeline + safety core, PROMOTED
    gated behind an empty `CALIBRATED_OFFSET_SOURCES` allowlist. Adversarial review found two
    latent JOIN holes (caller-trusted offset claim; unchecked external-artifact tamper) — both
    fixed (committed-store re-fetch + checksum verify). 15 tests. Committed `45cf7b7`.
  - **OT-3** (foreign-command invalidation primitive `detect_foreign_commands`): fail-closed
    whole-history scan; closes the gap `matched_command_is_latest` can't see (foreign command
    BEFORE ours). Review found a fail-OPEN blocker (`any(_matches_entry)` let one entry vouch for
    unlimited duplicate executions) — fixed with a 1:1 consuming pass mirroring reconcile's
    duplicate-key guard; re-verified. 18 tests. Committed `6dd4ce4`.
  - **OT-4** (`move_low_z` dry-target translator): `_move_low_z_command_body` + routing. Review
    (vs the Opentrons schema + canonical fixture) caught an unsafe descent — `minimumZHeight` only
    bounds the transit arc, not the descent, and `dry_z_floor_mm` is the collision-envelope top
    (~11 mm above the A1 well-top). Descent emission gated fail-closed
    (`low_z_dry_descent_endpoint_not_grounded`) until a per-well descent floor exists; semantics
    corrected. 4 tests.
  - **OT-2** (`set_offset`): formal closure. A labware offset is a run-setup `/labwareOffsets`
    record consumed by the `OFFSET_AUTHORITY` gate, not a motion command — declared in
    `plans.FORMALLY_CLOSED_OPERATIONS`, rejected fail-closed with an explicit reason at
    context/validation/dispatch. 2 tests.
  - **OT-5** (`liquid_handling` wet): closed scaffold. Restricted to `center_wet`, validates
    inputs fail-closed, emits nothing (`liquid_handling_wet_workflow_not_grounded`); the wet
    sequence (descend into liquid → aspirate/dispense → retract) is documented but unwired and
    ungrounded. 3 tests. (Completes the OT translator track: OT-4 gated, OT-2 closed, OT-5 scaffold.)
  - **Backlog reconciliation (closes the OC-A13 the tables never got):** verified Track 3 (OC-A*)
    is substantially DONE — the progress log said so since 2026-06-14, but the Track 3/Track 4
    tables and "Recommended next 3 cycles" still listed those items open and even recommended
    already-done work. Reconciled the tables to verified ground truth (observer-geometry test
    selection: 22 passed). True-open A-queue is now OT-2/OT-4/OT-5 translators, OT-7/OT-8 MCP
    adapter + route-parity, OP-P3/P4/P5/P8 docs, OC-A8 red-case.
- **2026-06-14 — Cycle 1 (OC-A1 + OC-A2 + OC-A4):** done + broad-verified (172 passed,
  0 failed across the observer/gate/first_print/manifest slice). The FE swept-body check
  now gates its own dry-bay containment (`front_end_body_fits_dry_bay`), the
  traverse scan-span is tied to the body extent (closing the decoupling bug where
  an oversized body overflowed while the traverse reported "fits"), and the static
  carriage box got the same containment gate (found by review). Shared
  `_dry_bay_containment` helper; `scan_axis_footprint_mm` (raw) split from
  `scan_axis_extent_mm` (effective). do→review→fix, suite green.
- **2026-06-14 — Cycle 2 (OP-P1 + OP-P2):** done. Authored
  `docs/protocols/observer_optical_bench_stage0.md`,
  `docs/protocols/observer_contrast_fork_ws2812.md`, and their measurement
  templates under `data/measurements/templates/`. Runnable Stage-0 procedures with
  the three gating numbers, the illumination-fork decision tree, and the CAD-feed
  mapping that retires `observer_sweep_extra_x/y`.
- **2026-06-14 — Cycle 3 (SM-3.1):** done. New `src/aevum_smis/` package:
  `ModuleManifest` schema + `validate_manifest_envelope` re-running the observer
  CAD's falsifiable arithmetic (barrel Ø ≤ 32, footprint Ø ≤ 32, Z-closure
  8+FE_z+stroke ≤ 62, mass ≤ 900) so a head claiming an envelope it doesn't fit is
  rejected at dock. Review-fixed: boundary table (exact-at-budget passes / +0.001
  fails per axis), `smis_version` made required (honest capture; compatibility gate
  landed in SM-4.4), digest canonicalization pinned. 17 tests, ruff clean.
- **2026-06-14 — Cycle 4 (SM-1.2):** done (do→review→fix). `aevum_smis/dock.py`:
  `DockSpec` + `validate_dock` falsifiable dock check — canonical 3-2-1 seat, magnet
  pull-margin ≥ 5× the **1 g-scan demand** (static + inertial), ball-circle clears the
  Ø32 keepout, anti-rotation dowel. **Review found a BLOCKER** (margin divided by static
  weight only, over-claiming ~6.7× vs the real ~3.3×) → fixed by modeling the load case,
  which moved the dock spec from 2 to **3 magnets** (decision logged), and tightened the
  seat to the exact 3-2-1 multiset (not any 6-DOF arrangement). 12 dock tests (29 SMIS
  total), ruff clean.
- **2026-06-14 — Cycle 5 (SM-4.1):** done (do→review→fix). `aevum_smis/driver.py`:
  the `ModuleDriver` ABI (`on_dock`/`configure`/`acquire(well, lease)→Evidence`/`health`/
  `on_undock`), a lease-gated fail-closed `run_scan` orchestrator (one loop, N
  modalities), `ModuleEvidence` packet, and a `DriverRegistry` with entry-point
  discovery. Structural decoupling: `MotionLease` is a Protocol the bridge's
  `BridgeLock` satisfies (proven in test) so SMIS never imports the bridge. Review-fixed:
  lease validity now mirrors the bridge's terminal-exclusion rule (was a stricter
  `== active` that would reject valid non-active states), `run_scan` re-checks the lease
  after each acquire (discards a capture if the lease lapsed mid-acquisition),
  `on_dock(platform)` restored to the frozen spec, evidence carries session/command/cal
  provenance. 9 driver tests (38 SMIS total), ruff clean. Bridge durable-`EvidencePacket`
  mapping deferred to IN-C5.
- **2026-06-14 — Cycle 6 (SM-3.2a + SM-4.3):** done (do→review→fix).
  `aevum_smis/safety.py`: the safety spine. Cal-vault HMAC challenge-response (DS28E07
  model, constant-time verify), `detect_module`, and the fail-closed
  `evaluate_source_enable` gate. **Security review found a BLOCKER** (the gate was a
  danger-denylist → counterfeit could self-declare a benign class to dodge it, and new
  dangerous classes defaulted uncertified-allowed) → **inverted to a safe-allowlist**
  (`CAL_VAULT_EXEMPT_CLASSES = {passive, led}`; everything else, incl. `laser_class_1`,
  requires certification; decision logged), plus replay hardening (fresh `issue_challenge`
  nonce) and length-prefixed MAC. 13 safety tests (50 SMIS total), ruff clean.
- **2026-06-14 — Cycle 7 (OC-A5):** done + broad-verified (172 passed, 0 failed).
  Fixed the carriage-traverse Z: it copied the static 62 mm carriage-box Z, but the thing
  that traverses is the 40 mm moving head (the front-end swept body, z=-48..-8). The
  traverse now takes the head's swept Z (`swept_z`/`swept_height_z`), surfaces
  `z_within_dry_bay`, and the dead `rect` param was removed. 9 targeted tests, ruff clean.
- **2026-06-14 — Cycle 8 (OC-A3 + A6 + A7 + A9 + A11 + A12 + A13):** done (do→review→fix).
  Closed the observer-CAD hardening seam — added falsifiable asserts to the checks that
  previously under-gated. **The 3-lens review confirmed all six items are genuinely
  falsifiable** (validated end-to-end through `row_coupon_layout`) and found a fail-open
  **BLOCKER** (the geometry propagation read `traverse_fits_dry_bay` not `clears_traverse`,
  so a deck-foot / adjacent-slot collision wouldn't block optical stability) — **fixed** —
  plus MAJOR coverage gaps (fiducial containment is now disk-radius + Z aware; new blockers
  are sorted lists) and **exposed two real placeholder inconsistencies now tracked as
  OC-A14/A15 below**. Items:
  - **OC-A3** raceway check had zero asserts → `raceway_clears_dry_bay_sweep` (no XY
    overlap with the optical sweep), `raceway_z_within_bay_depth`, `r10_loop_fits_raceway_z`
    (2·R bend-loop ≤ 24 mm reserved → 4 mm margin) + blockers.
  - **OC-A6** fiducial check was count-only → `fiducial_multiplicity_ok` (4 disks + 4
    marks per aperture) + `all_targets_within_dry_bay` + blockers.
  - **OC-A7** `front_end_service_margin_z` promoted to an explicit (provenance-noted)
    param; Z-closure carries it.
  - **OC-A9** split the conflated keepout: added `front_end_barrel_diameter` (=25.0,
    matches the SMIS manifest) + `front_end_barrel_fits_keepout` (authoritative round-barrel
    gate) vs the conservative head-bbox circumscribed Ø.
  - **OC-A11** geometry overflow now propagates a hard blocker
    (`geometry_overflow_blocks_optical_stability`) into the optical-stability check.
  - **OC-A12** razor-thin margins (0.4 mm traverse / 0.2 mm scan) flagged so sub-mm drift
    can't erode the budget silently.
  - **OC-A13** this reconciliation. Removed the now-dead `rect` param from the traverse
    helper (carried over from OC-A5). 15 targeted tests, ruff clean.
  The observer-CAD A-track is now substantially closed; remaining observer items are
  hardware-gated (Stage-0 metrology retires the placeholder `front_end_*` numbers).
- **OC-A14 (DONE, C decision resolved 2026-06-15):** chose the conservative footprint
  extension rather than reducing service clearance. `row.end_margin_x` is now 10.5 mm
  (coupon X 148.6 mm), enough for the service raceway to clear the boundary-rail lane
  after the length clamp. `raceway_clears_boundary_rail` is now True for the live axis
  "y"; the diagnostic remains pinned so future footprint/raceway changes cannot silently
  reintroduce the intrusion. See `decision_log.md`.
- **SM-2.2 (DONE 2026-06-15):** HEAD-BUS is now a frozen machine-checkable schema
  (`aevum_smis.head_bus.FROZEN_HEAD_BUS`) with validation for required signal groups,
  unique line IDs, no-hot-mate, EEPROM `0x50`, active-low make-last/break-first laser/MW
  interlocks, and single-point shield bonding. 12 new tests; SMIS focused suite green.
- **SM-2.1 (DONE 2026-06-15):** Infinity-port PD-0 is now a validation-only CAD
  check (`observer_infinity_port_datum_check`) with frozen 28 mm objective-shoulder
  offset, Ø20 clear aperture, 30 mm cage standard, RMS+C-mount presence, and 50 mm
  tube-lens-to-sensor spacing. Red cases reject oversized aperture, missing standard,
  and spacing drift. Export package list includes the new validation STEP/STL.
- **SM-4.4 (DONE 2026-06-15):** SMIS semver policy is now fail-closed in
  `aevum_smis.compatibility`: malformed versions, major mismatch, future minor modules,
  HEAD-BUS version drift, HEAD-BUS structural drift, and driver entry-point group drift
  all block compatibility before driver load/source enable. 8 new tests; SMIS focused
  suite green.
- **SM-1.3/1.5a (DONE 2026-06-15):** head-swap registration is now a separate
  platform authority in `aevum_smis.registration`. Tier A defaults to one-fiducial
  coupling trust, `requires_post_dock_autofocus` requires Tier B / 3 fiducials, and
  first install or forced re-cal requires Tier C / 16 fiducials. Unknown tier,
  failed `on_dock`, insufficient tier, or insufficient fiducials fail closed before
  acquisition. 4 new tests; SMIS focused suite green.
- **IN-C1/C2 (DONE 2026-06-15):** observer GX16/M12 umbilical is now a frozen
  machine-checkable boundary in `aevum_smis.observer_umbilical`. GX16-4 carries
  24 V/5 V, GX16-6 carries I2C/3.3 V/alarm/observer-enable, GigE is forced onto
  the M12 X-coded bulkhead, and a reconciliation check proves HEAD-BUS remains a
  superset of the observer boundary. 7 new tests; focused HEAD-BUS/compatibility
  suite green.
- **IN-C3 (DONE 2026-06-16):** sensor telemetry now feeds a machine-checkable
  condensation gate in `aevum_smis.condensation`. The policy computes dew point
  from local SHT41 RH/T, compares MLX90614 plate-underside temperature against
  the reserved +2°C margin, requests purge/heat action as the margin closes, and
  blocks acquisition when the margin is spent or RH is saturated. 8 new tests;
  focused SMIS suite green. Final purge/lip-heat setpoints remain Stage-0
  warm-media evidence, not coded claims.
- **IN-C4 (DONE 2026-06-16):** the `observer_scan` bridge lease is a first-class
  mutually-exclusive lease kind. `BridgeLock` gained `lease_kind` (defaults
  `pipetting`, so prior OT-2 sessions are unchanged; pre-IN-C4 lock DBs migrate
  their unlabeled rows to `pipetting`), and `src/aevum_ot2/core/observer.py` adds
  `acquire_observer_scan_lease` + the fail-closed `mint_observer_scan_evidence`.
  Mutual exclusion is structural (one non-terminal lock per `robot_url`): a held
  pipetting lease refuses an observer scan lease and vice versa, and the refusal
  carries the holder's `lease_kind`. `ObserverScanEvidence` (well/focus-Z/focus
  metric/illumination/pose-digest/lease provenance) emits an
  `EvidenceHandle(source_kind=observer_frame)`. Authority kept separate: minting is
  fail-closed against the lease only (wrong-kind/terminal/expired → `ObserverLeaseError`);
  the pose digest rides as registration *provenance*, NOT a registration gate, and
  source-enable/condensation/the hardware enable-line stay separate gates. 17 new tests
  (`tests/test_observer_lease.py`), focused lock/SMIS/schema suites green (138 passed),
  ruff clean.
- **IN-C5 (PARTIAL — observer evidence output path DONE 2026-06-16):**
  `observer_scan_evidence_to_packet` + `persist_observer_scan_evidence`
  (`src/aevum_ot2/core/observer.py`) map an `ObserverScanEvidence` frame into the bridge's
  durable `EvidencePacket`/transaction store, completing the "evidence output path" the
  hypergraph requires before any observer acquisition. Frames commit as packets with **no
  claims** (a bare acquisition record never authorizes motion — the `evidence_model.md`
  rule, proven by `load_committed_evidence_claims == []`). Fail-closed defense in depth:
  persistence refuses a hand-built frame carrying a non-`observer_scan` `lease_kind`, and
  a batch spanning two sessions fails closed (the transaction store rejects mixed sessions).
  6 new tests, ruff clean.
- **IN-C5 tail (DONE 2026-06-16):** the generic SMIS `ModuleEvidence` now reaches the same
  durable store via `module_evidence_to_packet` / `persist_module_evidence`
  (`src/aevum_ot2/core/observer.py`). The "where the mapping lives" fork resolved
  conservatively: the bridge defines a `SensorModuleEvidenceLike` **structural Protocol** and
  imports nothing from `aevum_smis` (mirror of how SMIS uses `MotionLease` to avoid importing
  the bridge); a test asserts the real `aevum_smis.ModuleEvidence` satisfies it so the seam
  can't drift. Same rule as the observer path — packets only, no claims, `observer_frame`
  source kind, fail-closed on a missing `lease_owner`. IN-C5 is now fully closed. 4 new tests
  (526 passed across the surface), ruff clean.
- **IN-C6 (PARTIAL — pose cross-check DONE 2026-06-16):** `cross_check_observer_pose` +
  `ObserverPoseCheck` (`src/aevum_smis/registration.py`) add the registration spine's
  coordinate gate: the observer independently recovers the installed pose from ≥3
  non-collinear fiducials and the gate fails closed on a stale declared pose (digest changed
  since registration), a fit residual over the (measured-gated) tolerance, too few fiducials
  for a rigid fit, or a missing/malformed digest — each a separate named blocker, never one
  boolean. Distinct authority from the Tier A/B/C ritual (`validate_registration_result`);
  Tier A trust-coupling skips the fit/residual checks but staleness still applies. Binds on
  opaque digest strings (no bridge import). 8 new tests (506 passed across the surface), ruff
  clean. The A1 offset/sign convention (14.38/11.24, 9 mm pitch) is already the single-source
  analytic well map in the CAD params, so it was not re-encoded. **Open tail:** the residual
  tolerance is a placeholder pending Stage-0/Stage-3 metrology (B); the actual sub-pixel
  centroiding + Umeyama fit that produces `recovered_residual_um` is hardware-gated (B).
- **IN-C7 (PARTIAL — software half DONE 2026-06-16):** the two-layer interlock's software
  side in `src/aevum_ot2/core/observer_interlock.py`. `observer_enable_intent` derives the
  observer enable INTENT (true only while a valid `observer_scan` lease is held — released/
  expired/terminal/wrong-kind drops it), explicitly NOT the hardware enable. The
  `pipetting_lease_admission` handoff refuses a pipetting lease while an observer lease is
  active and, after release, until a fresh parked + Z-retracted `ObserverParkReport` exists —
  fail-closed on absent/false/stale/future-dated reports, each a named blocker. 13 new tests
  (519 passed across the surface), ruff clean. **Open tail (B):** the hardware enable line,
  the GX16 safety loop, the physical limit switch, and the real `DEFAULT_MAX_PARK_AGE`
  freshness window (Stage-4 interlock build).
- **IN-C8 (DONE 2026-06-16):** the cal-vault/counterfeit substance was already built
  (`aevum_smis.safety`: DS28E07 HMAC challenge-response bound to `challenge || manifest_sha256
  || serial`, fresh-nonce replay defense, fail-closed `evaluate_source_enable` with the
  safe-allowlist; SM-3.2a/4.3/4.4). The review confirmed the **head is the only active,
  swappable, counterfeit-risk SMIS part**; non-head parts (sensor PCB, power section) ride the
  already-decided receiving-step COTS discipline (decision_log 2026-05-28), so no new
  per-part crypto token is required — adding a DS28E07 to the sensor PCB would be a future B
  hardware option, not a blocking decision. The genuine HX4 gap was the **"without merging
  with compatibility or registration"** proof: added 3 tests showing the three authorities
  are independent functions over independent inputs (a genuine head can be version-
  incompatible; a genuine head can fail registration; `evaluate_source_enable` consumes only
  detection + interlock, never compatibility/registration). 3 new tests, ruff clean.
- **OT-1 (producer + safety core DONE 2026-06-17; PROMOTED gated-blocked):** the missing offset
  authority producer (`OffsetAuthorityState.PROMOTED` was checked but never set, so the offset gate
  could never pass). New `src/aevum_ot2/core/offset_evidence.py` mirrors the proven
  artifact→packet(`OFFSET_MEASUREMENT`)→claim(`offset_measured:<class>`)→commit→promote pipeline.
  `promoted_offset_record` is the terminal trust boundary: it flips PROPOSED→PROMOTED only after a
  fail-closed JOIN of four independent facts — (1) the offset claim re-fetched from the COMMITTED
  store (never a caller arg; symmetric with high-Z), its bound artifact checksum-verified against the
  committed handle (post-commit tamper-evident) and its `offset_mm` matching the record, (2) the OT-6
  `high_z_motion_completed` claim re-fetched
  from the COMMITTED store (never caller-supplied), (3) that move re-reconciled against the LIVE
  command journal NOW (catches a stalled motor that merely reported success at OT-6 build time), and
  (4) `offset_source ∈ CALIBRATED_OFFSET_SOURCES`. Per the **builder decision ("pipeline only,
  PROMOTED blocked")**, that allowlist is EMPTY — operator-attested offsets are RECORDED as evidence
  but cannot promote, so the gate stays unreachable until a calibrated source is deliberately added
  (mirrors the SMIS source-enable safe-allowlist). Authority isolation held: no `motion_allowed`, no
  `MotionApproval`, no `motion_commissioning` import, no authorizing `GateResult`. Registry upsert
  (`promote_offset_record_in_registry`) replaces the same-id PROPOSED record (id is a scope hash, so
  promotion keeps the id). `OffsetRecord` gained `offset_source`/`measurement_method`/`high_z_*`
  command-binding fields (additive; not in the id hash, so existing ids/digests unchanged). An
  adversarial review (verdict ship-it) found two latent JOIN holes behind the empty allowlist —
  caller-trusted offset claim + unchecked external-artifact tamper — both **fixed** (committed-store
  re-fetch + checksum verification) with regression tests. 15 tests (the JOIN proven member-by-member;
  the headline blocked-by-uncalibrated; a monkeypatched-allowlist "machinery-works" proof; tamper +
  uncommitted-claim regressions; 587 across the surface), ruff clean. **Open tail:** the offset_mm vector
  auto-measurement is B/C-gated (uncalibrated vision); the `offset-evidence-commit` CLI is a remaining
  thin adapter; flipping the allowlist on requires a calibrated source (B).
- **OT-6 (DONE 2026-06-17):** post-motion high-Z evidence shape + recording path in
  `src/aevum_ot2/core/high_z_motion_evidence.py` (+ `HighZMotionRecord`, claim helpers,
  `HIGH_Z_LANDING` source kind). It answers the POST-motion question ("did the commanded
  first high-Z move execute and reconcile?") — distinct from `target_evidence.py`'s PRE-motion
  "does a reachable target exist?". Mirrors the proven artifact→packet(`HIGH_Z_LANDING`)→claim
  (`high_z_motion_completed:<class>`)→`commit_evidence_transaction`→promoted-record pattern,
  and additionally binds executed-command provenance from the real
  `CommandJournalEntry`/`CommandReconciliationResult` (never fabricated). Produces EVIDENCE
  only — never sets `motion_allowed`, mints no `MotionApproval`, emits no `GateResult`,
  promotes no `OffsetRecord` (that is OT-1). Vision is uncalibrated for high-Z
  (`motion_gate=False`), so a USABLE claim rests on the human `inspection_note` + command
  reconciliation + an indexed post-move camera capture, never on geometry; there is no
  computed achieved-Z/offset (conservative C-default, see decision_log). **Built via a
  multi-agent understand→implement→adversarial-review cycle**: the review found 3 blockers +
  1 major (forge via promote, unbound reconciliation, pre-move-frame replay, foreign-session
  command) + a residual (self-contradictory claim) — **all fixed and regression-tested**. 30
  tests (556 across the bridge/SMIS/server surface), ruff clean. **Constraint on OT-1 (the
  consuming gate):** OT-6's promote re-validates claim *identity* but deliberately defers
  committed-store + live-command-journal re-verification of the reconciliation/landing facts
  to the consuming offset-promotion gate (those facts are not on the claim). OT-1 must
  re-validate the `high_z_motion_completed` claim against `load_committed_evidence_claims` and
  the live command journal before promoting an offset. **Brutalist design review (2026-06-17)**
  applied 3 OT-6-local fixes: a declarative `_PACKET_PAYLOAD_FIELDS` table now drives BOTH the
  packet build and the payload↔artifact verify (closing a fail-open gap where a forgotten field
  silently stopped being checked; + a property test corrupting every field); `HighZMotionRecord`
  got its own `HighZMotionResult` enum (so a future `result == TargetClassResult.PASSED` filter
  can't sweep up motion records); and `__all__` + bypass-seam docstrings hide the
  provenance-skipping low-level packet/claim helpers. 31 tests, 557 surface, ruff clean.
- **TECH-DEBT — evidence-primitive consolidation (DONE 2026-06-17, brutalist-flagged):** the 6
  security-relevant primitives (`_sha256_file`, `_safe_path_segment` — the path-traversal guard,
  `_transaction_root_for_index` — the on-disk layout invariant, `_same_path`, `_is_timezone_aware`,
  `_datetime_payload`), formerly copied 3–6× across `core/`, now live ONCE in a new stdlib-only leaf
  module `src/aevum_ot2/core/evidence_primitives.py` (a graph sink — cycle-proof; chosen over
  evidence.py, which drags in models+schema). All 7 consumers (evidence, target_evidence,
  pose_evidence, high_z_motion_evidence, records, pose, motion_approval) import from it; local copies
  deleted (grep confirms each defined exactly once). **Built via do→review workflow cycles:** a
  verify-and-plan workflow proved 5 primitives byte/behavior-identical and caught that `_same_path`
  had **two divergent variants** whose call sites made *neither* body universally safe (object-guard
  rejected legitimate `Path` args; str|Path crashed on untrusted `None`) — reconciled into one
  superset body (guard admits `str`|`Path`, fails closed on anything else). An adversarial review
  workflow confirmed behavior-preservation (the object-guard sites only ever see JSON-derived
  `str`/`None`; the str|Path sites only see `str`/`Path` — observably identical everywhere) and found
  one more inline copy (`pose.py` `_coerce_naive_datetime`), now routed through the canonical. New
  `tests/test_evidence_primitives.py` (11 tests) locks the reconciliation + the security guards; 568
  across the bridge/SMIS/server surface, ruff clean, no import cycle. NOT the descriptor-engine
  extraction (inverts the proven per-module mirror convention; out of scope).
- **TECH-DEBT — residual primitive near-duplicates (DONE 2026-06-17, do→review workflow cycles):**
  the second consolidation pass. **Unified (provably zero digest/behavior change):** (e) the
  stable-JSON-hash family — `_stable_json_sha256` now lives ONCE in `evidence_primitives.py`, and
  `command_journal`, `dispatch_preparation`, `safety` (was `_sha256_json`), `pose.sha256_json`,
  AND the two inline copies the review caught (`motion_approval.plan_fragment_digest`,
  `motion_approval_scope_digest`) plus `registry.offset_record_id` all route to it; the
  `json.dumps(sort_keys, compact).encode()+sha256` pattern now exists in exactly one place
  (verified by grep). (b) `artifacts.sha256_file` and `gates._sha256_if_file` delegate to the
  canonical `_sha256_file`. (a) the evidence-transactions dir name is single-sourced as
  `EVIDENCE_TRANSACTIONS_DIRNAME` (used by `_transaction_root_for_index`, `evidence.py`,
  `server/service.py`). Digest stability is the load-bearing property: all persisted digests
  (command body/params hashes, safety-profile/target-policy/pose digests, offset id, plan/scope
  digests → approval id) are byte-unchanged — proven because `.encode()`≡`.encode("utf-8")`
  (ensure_ascii=True → pure ASCII) and chunked≡whole-file, confirmed by the full digest-comparison
  suite + a new hardcoded **golden-vector** test that pins the exact encoding. **Left + documented
  (legitimately separate, confirmed by review):** (c) `motion_approval._safe_segment` (the `"empty"`
  fallback is a label, not an id-uniqueness mechanism — id uniqueness rides on the scope digest over
  raw fields; a comment now warns against "fixing" it into a raise); (d) the four
  `_require_session_evidence_index` inline resolve-compares (trusted inputs; routing through
  `_same_path` would swap fail-loud OSError for a string-equality fallback in a tamper gate — keep).
  16 tests in `test_evidence_primitives.py`; 572 across the bridge/SMIS/server surface, ruff clean,
  no import cycle.
- **IN-C9 (A-geometry DONE; binding reconciliation B-GATED 2026-06-16):** review concluded
  the A-addressable CAD geometry is already complete — the service-raceway envelope, the R10
  loop-height Z budget (`2·service_bend_radius = 20 ≤ service_raceway_height_z = 24`, 4 mm
  margin), the dry-bay-sweep clearance, and the boundary-rail clearance all landed in OC-A3 /
  OC-A14 (`_observer_service_raceway_envelope_check`), and the GX16/HEAD-BUS/M12 **route**
  reconciliation landed in IN-C1/C2 (`reconcile_observer_umbilical_with_head_bus`). The
  remaining HX5 reconciliation — does the real R10 chain + GX16/M12 cable bundle physically
  fit the 8 mm raceway thin dimension (`service_raceway_width_y`) at the bend radius — is
  **B-gated**: observation_module.md explicitly calls for buying one chain segment and
  calipering the real loop height *with cable in it* before freezing the lid. A software
  check using guessed cable ODs would manufacture a physical-fit claim without evidence
  (forbidden), so none was added. No code change this cycle.
- **OC-A15 (MODELED + Stage-0-gated):** the binding constraint is the **standoff-leg scan
  corridor** (117.4 mm live; head budget **15.56 mm**, see the OC-A15 correction of
  2026-09-21), not the bay or the Ø32 keepout — the head must thread the legs, and at the
  live 21.0 mm placeholder footprint it strikes the near leg by 2.72 mm. An RMS thread
  floors near Ø20.32, so **no RMS objective threads this corridor at all**. Three open
  resolutions: source a sub-15.56 mm head (no RMS train qualifies); re-route the service
  shroud so `lower_service_foot_inset_x` goes 3.0 → 0.0 (budget 21.24 mm, a Ø20.32 RMS
  barrel then clears by +0.46 mm); or reshape the corner posts into X-strip rails
  (budget 24.84 mm at 2.0 mm rails, with 3.2x the bearing area).
  **Superseded in part 2026-09-23 by OC-A18(a) below** (the same marker OC-A16 already
  carries): 15.56 mm is the residual for scanning **all 12** well columns, which the 88 mm
  tile aperture never admitted — it admits **8**, spanning 63.0 mm. Budgeted against the
  reachable columns the head budget is
  `min(2 x (42.88 - 17.10), 2 x (134.50 - 105.88))` = **51.56 mm**, at which a Ø20.32 RMS
  barrel clears by **+31.24 mm** with no geometry moved. **"No RMS objective threads this
  corridor at all" is withdrawn**, and none of the three resolutions above is required for a
  catalog head. Which budget applies is coupled to the aperture: enlarging it to ~110 x 74 mm
  to recover all 384 wells returns the reachable span to 99.0 mm and the budget toward
  15.56 mm — the wide aperture and the wide head are alternatives, not a package. The frozen
  SMIS contract deliberately still carries 15.56 (`src/aevum_smis/manifest.py:68`), so a head
  sourced against 51.56 mm is rejected at dock until that is changed.
  **Done (2026-06-14):** (a) the CAD surfaces the leg corridor as the binding scan wall
  (`scan_corridor_width_mm` / `scan_corridor_margin_mm`) and the bay-Y was resized to the
  wet/dry-bounded extent (`sweep_extra_y` 12.2→17.0); (b) Stage-0 protocol
  `observer_leg_corridor_objective_metrology.md` authored; and the **SMIS envelope now gates
  every modality head against the corridor** (`scan_corridor_footprint_max_mm`, rejecting a
  Ø25 head that clears the keepout). **Still OPEN (C/B):** the actual resolution — source a
  slim ≤21 mm objective vs. relocate the standoff legs out of the corridor — is the builder's
  call, gated on the Stage-0 caliper measurement. See `decision_log.md`.
- **Next:** the entire **IN-C1–C9 cross-branch integration spine is now closed to its
  software/CAD-addressable boundary** (IN-C9's binding reconciliation is B-gated; the HX2/HX3
  tails are B/metrology-gated), and **OT-6** (the post-motion high-Z evidence input to OT-1)
  is now done. The next high-leverage A-item is **OT-1** (transaction-backed offset authority:
  evidence→claim→promoted offset + `offset-evidence-commit` CLI — SAFETY-CRITICAL, the actual
  motion gate; **review the diff**). OT-1 now has its evidence input ready (the
  `high_z_motion_completed` claim) and must re-validate that claim against the committed store
  + live command journal before promoting. **OT-1 design note (brutalist-flagged):** OT-6's
  "post-motion" is only a timestamp comparison — a stalled motor reporting `succeeded` yields a
  baseline frame stamped USABLE. OT-6 grants no motion authority, so real physical-motion
  confidence (two-frame delta / axis-position readback) is OT-1's job, gated on the
  uncalibrated-vision hardware reality; do NOT inherit it as "solved." Then OT-3 (physical-event
  invalidation), the observer protocol docs (OP-P*), and the remaining observer-CAD items.
  Physical critical path unchanged: the ¥40 contrast + ¥20 settle buys upstream of all observer
  architecture.

## Landscape

Six tracks. The **OT-2 control stack** is the most mature — no-motion
registration, the `move_high_z` translator, validation/revalidation gates, and
backend dispatch all exist; the gaps are transaction-backed offset authority (the
only motion gate with no evidence-production path), physical-event invalidation,
agent adapters, and the first live commissioning run (hardware-gated). The
**row-coupon physical** track is the inverse: every digital scaffold is green
(`print_start_ready`, six Gate worksheets, 39 validation bodies) but **zero
physical evidence exists** — the whole Gate-1→6 chain is owed and gated on
actually printing 38 rigid print pieces (46 physical artifacts; eight flexible or
compressible parts sit outside the rigid queue — canonical fabrication contract in
`one_row_coupon.md`, the paragraph beginning "The canonical fabrication contract
contains 46 physical artifacts", regeneration witnessed as "38 STEP/STL pairs" at
`row_coupon_cycle_log.md` RS164) and sourcing parts. The **observer** splits into
**CAD-hardening** (a rich seam of pure-A do→review cycles), **prototyping** (eight
missing protocol docs are pure-A; everything downstream is hardware-gated on a
~¥40 contrast test and a ¥20 settle log), and the **SMIS platform** (zero
code/geometry exists; the dock CAD, manifest schema, and `acquire()→Evidence` ABI
are the largest greenfield A bodies). **Decisions+integration** ties them via the
GX16/HEAD-BUS umbilical, the `observer_scan` bridge lease, and ~9 open decisions.

## Backlog (canonical, by track)

### Track 1 — OT-2 control stack

| Item | Produces | Tag |
|---|---|---|
| OT-1 | Transaction-backed offset authority (evidence→claim→promoted offset) — producer pipeline + safety core **done 2026-06-17** (PROMOTED gated-blocked behind an empty calibrated-source allowlist per builder decision); `offset-evidence-commit` CLI is the remaining thin adapter | A |
| OT-2 | `set_offset` — **done 2026-06-17 (formal closure)**: a labware offset is a run-setup `/labwareOffsets` record consumed by the `OFFSET_AUTHORITY` gate, not a motion command, so `set_offset` is declared in `plans.FORMALLY_CLOSED_OPERATIONS` and rejected fail-closed with an explicit reason at context/validation/dispatch (+ absent from the agent surface) — see decision_log | A |
| OT-3 | Physical-event / foreign-command invalidation primitive (`detect_foreign_commands`, whole-history scan for any command not authored by us) — **done 2026-06-17** | A |
| OT-4 | `move_low_z` dry-target translator — **done 2026-06-17 (descent emission gated)**: `_move_low_z_command_body` + routing; descent refused (`low_z_dry_descent_endpoint_not_grounded`) until a per-well dry-descent floor exists, because `minimumZHeight` only bounds the transit arc (not the descent) and `dry_z_floor_mm` is the collision-envelope top, ~11 mm above the A1 well-top — see decision_log. **Follow-up done 2026-06-18 (A):** `core/well_geometry.py` supplies the real per-well access bounds (checksum-anchored to the labware digest), wired into the descent gate as a reachable fail-closed bounds check (replacing the envelope-top misuse); emission still gated. **Remaining tail (B):** measure the safe dry depth (liquid line) within those bounds, then flip the gate | A |
| OT-5 | `liquid_handling` (wet) translator — **done 2026-06-17 (closed scaffold)**: `_liquid_handling_command_body` + routing, restricted to `center_wet`, validates inputs fail-closed, emits nothing (`liquid_handling_wet_workflow_not_grounded`); the wet SEQUENCE design (descend into liquid → aspirate/dispense → retract) is documented but unwired and ungrounded — see decision_log | A |
| OT-6 | Post-motion high-Z evidence shape + recording path (input to OT-1) — **done 2026-06-17** | A |
| OT-7 | MCP agent adapter `adapters/mcp.py` — **done 2026-06-18**: thin policy adapter, only the 10 allow-listed validated-session tools, routes via `DaemonClient`, no `Ot2Client`/`post_json`; never mints motion approval; SDK lazy-imported/optional; `mcp-serve` CLI + boundary tests | A |
| OT-8 | MCP/HTTP pose route-parity tests — **done 2026-06-18**: `tests/test_route_parity.py` derives pose-bearing routes from `app.py` + request models and pins the "no SILENT canonical default" at its exact HTTP/MCP sites | A |
| OT-9 | HTTP programmatic adapter (optional) — **substantially covered / optional**: `server/client.py` `DaemonClient` is already the typed urllib HTTP client over the daemon (used by the CLI and the OT-7 MCP adapter); a separate external programmatic adapter adds little and is explicitly optional. Leave open-optional | A |
| OT-10 | Recovery runbook + `ot2_abort_or_recover` wiring — **done 2026-06-18**: `core/abort_recover.py` facade projecting `recover_no_motion_session` into an agent contract (`motion_allowed` never True out of this path), `BridgeService.abort_or_recover`, `session-abort-or-recover` CLI, runbook doc; HTTP-route/client-method exposure noted as follow-up | A |
| OT-11 | Trajectory/task-graph doc reconciliation — **done 2026-06-18**: marked the high-Z translator / OT-3 invalidation / OT-6 evidence DONE in both task graphs with module pointers; preserved the still-open live-motion-backend POST tail (RG14, B-gated) to avoid over-claiming live motion | A |
| OT-12 | Daemon arm/execute operability — **done 2026-06-18**: `core/commissioning.py` fail-closed operability layer over the EXISTING motion daemon (dry-run default; never arms without explicit confirm; mints no approval itself) + `scripts/ot2_motion_commissioning.py` + runbook | A |
| OT-B1..B7 | First live commissioning (fresh session, drift checks, home→high-Z, low-Z offset, wet) | B |
| C-OT1..5 | single-writer enforcement, set_offset semantics, autonomy threshold, named-vs-raw first move, evidence sufficiency | C |

### Track 2 — Row-coupon physical (Gate 1→6, hard-sequential)

| Item | Produces | Tag |
|---|---|---|
| RC-W1 | Print the 38-piece final-print-piece batch (PETG) — precondition for everything downstream. *(Corrected 2026-09-23: "21-file split batch" was the retired Y-split count; the canonical queue is `rigid_print_pieces` = 38 per `docs/assembly/artifact_authority.json`.)* | B |
| RC-W2 | Procure/blank 12 install-inventory items + real sensor PCBs | B/C |
| RC-W3 | Gate-1 print-QC measurements (38-row worksheet — one row per queued print piece) | B |
| RC-W4 | Gate-2 dry assembly + 5× service cycles | B |
| RC-W5 | Gate-3 OT-2 placement + real toolhead-envelope measurement | B |
| RC-W6 | Gate-4 passive leak / wet-dry / condensate challenge | B |
| RC-W7 | Gate-5 plate/mat metrology + all-384 puncture | B |
| RC-W8 | Gate-6 sensor + observer mechanical seating (converges with the observer track) | B |
| RC-W9 | Operating-prototype acceptance | B |
| RC-W*a | Contingent CAD revisions, triggered only by a measured Gate failure | A |
| RC-W10 | Powered env-control + BSL1 biology (beyond first-print) | B/C |

### Track 3 — Observer CAD hardening (all pure-A do→review)

**Status note (reconciled 2026-06-17):** Track 3 is substantially DONE — verified against the
code and the observer-geometry test selection (`tests/test_row_coupon_cad.py -k "observer or
dry_bay or swept or carriage or raceway or fiducial or scan"`: **22 passed**). The backlog had
drifted: A1–A7, A9–A12, A14, A15 were all implemented as falsifiable asserts but still listed
open. The OC-A2 "reproduction" below described the *pre-fix* behavior the code already corrects.
Only A8 (a specific red-case scenario — falsifiability already proven generally) and A13 (this
reconciliation) remain.

| Item | Produces | Tag |
|---|---|---|
| OC-A1 | `front_end_body_fits_dry_bay` containment assert + overflow fields in the FE swept-body check — **done** (`_dry_bay_containment`; `test_observer_oversized_body_overflows_both_checks_no_decoupling`) | A |
| OC-A2 | Reconcile `front_end_length_x/width_y` ↔ `front_end_scan_axis_footprint` — **done** (scan-span tied to body via `max(scan_footprint, body_extent)`; same regression test asserts both checks overflow at `front_end_length_x=60`) | A |
| OC-A3 | Falsifiable asserts in the service-raceway check — **done** (`test_observer_raceway_geometry_falsifiable_oc_a3`) | A |
| OC-A4 | Carriage static-box containment + carriage-clears-raceway assert — **done** (`carriage_box_fits_dry_bay` via `_dry_bay_containment`, propagated to optical-stability) | A |
| OC-A5 | Focus-stroke-vs-Z-budget assert at traverse level — **done** (traverse sweeps the 40 mm FE swept Z; dimension-sensitive falsifiability test) | A |
| OC-A6 | Make the fiducial-focus check falsifiable — **done** (`test_observer_fiducial_geometry_falsifiable_oc_a6`) | A |
| OC-A7 | Promote `front_end_service_margin_z` from silent `0.0` to an explicit param — **done** (explicit param) | A |
| OC-A8 | Negative "measured 40×40 head @ 25 mm WD" red-case test — **done 2026-06-18**: dedicated test in `test_row_coupon_cad.py` with empirically-verified pinned values (body overflow x=18.8/y=17.0, scan_axis_extent=40.0, vertical budget 65.0>62.0) proving OC-A1/A2/A5 falsifiable + a green-baseline guard | A |
| OC-A9 | Split circumscribed-diameter into barrel-Ø vs head-bbox (+ `front_end_barrel_diameter`) — **done** (`test_observer_barrel_and_optical_geometry_propagation_falsifiable_oc_a9_a11`) | A |
| OC-A10 | Encode the SMIS envelope as a CAD assert cross-checking observer params — **done** (`src/aevum_smis/manifest.py` re-runs the observer envelope arithmetic) | A |
| OC-A11 | Cross-reference optical-stability checkpoints to the geometry booleans they cite — **done** (overflow propagates to the optical-stability check) | A |
| OC-A12 | Gate the razor-thin margins so a param nudge goes red — **done** (`test_observer_razor_thin_margin_flag_is_falsifiable_oc_a12`) | A |
| OC-A13 | Doc reconciliation (fold A1–A12 into RH6/RH15/RP5) — **done 2026-06-18**: the OC-A facts (with the check field names) folded into the RH6/RH15/RP5 hyperedges in `row_coupon_revision_hypergraph.md` (the anchors live there, not realization_hypergraph.md; the staleness was semantic, not line numbers) | A |
| OC-A14 | Raceway-X clamp by coupon length (live footprint) — **done** (not in the original A1–A13 list) | A |
| OC-A15 | Barrel-vs-scan-corridor diagnostics surfaced (not gated) — **done** (`test_observer_scan_corridor_strike_is_falsifiable_oc_a15`) | A |
| OC-A16 | **Open 2026-09-23.** Carriage-body-vs-leg-corridor closure. The live standoff-leg corridor is 117.4 mm clear (inner faces X 17.10 / 134.50, `src/aevum_smis/manifest.py:51-55`); `carriage_length_x` is 100.0 (`cad/one_row_coupon.params.json:137`), but the dry-bay X beam the head rides is 120.2 mm — already wider than the corridor — and the camera arm's own X extent is still unresolved: `front_end_scan_axis_footprint` is a 21 mm bare-objective placeholder that **excludes** the arm, and the arm was held to be unroutable along that 120 mm beam because only ~0.2 mm of X remains after the **99 mm** well span (`observation_module.md`, § *The 44.6 mm carriage-Y-overflow is a CAD artifact, not a physical wall*, the paragraph beginning "But the Y fix relocated its burden onto the X scan axis"; the residual is stated in code at `src/aevum_cad/row_coupon/parts/observer.py:184-193`), which was why the arm had to fold coaxially or go offboard. **Superseded in part 2026-09-23 by OC-A18(a) below:** the 99 mm figure spans all 12 well columns, and the 88 mm tile aperture only ever admitted 8 of them (63.0 mm span, OC-A17). Against the reachable span the bay-wall residual is 120.2 − 63.0 − 21 = **~36 mm** rather than ~0.2 mm, and the binding leg-corridor budget is **51.56 mm** rather than 15.56 mm — so the coaxial-fold-or-offboard conclusion is **no longer forced**, and the camera-routing question reopens. What remains genuinely open is narrower: decide which body actually has to thread the 117.4 mm corridor, and encode it as a falsifiable assert rather than leaving it implied. (The earlier citation here pointed at `observation_module.md:217`/`:225-227`, which is the Y-axis `carriage_traverse_exceeds_dry_bay` blocker — 334.5 + 58 = 392.5 vs 347.9 — not the X residual; retargeted 2026-09-23.) | A (measurement tail B) |
| OC-A17 | **Open 2026-09-23 — reporting bug, recommendation only.** The observer front-end swept-body check reports `covered_well_count` = 384 (`src/aevum_cad/row_coupon/layout.py:965` passes `len(all_well_centers)` into `src/aevum_cad/row_coupon/parts/observer.py:578`, emitted at `:630`): that is the wells the ROW covers, not the wells the OBSERVER can reach. The optically reachable set is **128 of 384** — the per-tile through-aperture is 88 × 52 mm (`dry_bay.aperture_length_x` / `aperture_width_y`), and either the optical cone at long WD (9.27 mm at the aperture plane at WD 19.90 ⇒ 4.64 mm inset) or the physical nose at short WD (OD 8-20 mm ⇒ 4-10 mm inset) removes the outer well ring; both routes give the same 128. Split or rename the field (row-covered vs observer-reachable) so the check stops over-claiming. Code untouched in the docs-only pass | A |
| OC-A18 | **Open 2026-09-23 — two `src/aevum_smis/manifest.py` recommendations, recorded and deliberately NOT applied** (docs-only pass; suite at 501 passed / 0 failed). (a) `scan_corridor_footprint_max_mm = 15.56` (`manifest.py:68`) is the residual after a 99 mm scan across all 12 well columns, but the 88 mm tile aperture only ever admitted 8 columns (63.0 mm span); parameterised by the **reachable** columns the budget is min(2×(42.88 - 17.10), 2×(134.50 - 105.88)) = **51.56 mm**, a 3.3× increase with no CAD change. (b) `vertical_required` (`manifest.py:193-200`) is an **additive** sum (front_face_clearance + front_end_height_z + focus_stroke_z + service_margin_z ≤ z_budget), so 8 + 57 + 18 = 83 > 62 rejects every 60 mm-parfocal objective on geometry the solid model says is clear (probe cylinders to Ø25 mm rise unobstructed from z = 0 to z = 11.71 at every tile-aperture centre). Replace with a swept-envelope check that keeps a hard retract-plane assertion | A |

### Track 4 — Observer prototyping (protocols A; measurements B; forks C)

| Item | Produces | Tag |
|---|---|---|
| OP-P1, P2 | Stage-0 bench + WS2812 contrast-fork protocol docs — **done** (`docs/protocols/observer_optical_bench_stage0.md`, `observer_contrast_fork_ws2812.md`; reconciled 2026-06-17) | A |
| OP-P3, P4, P5, P8 | **done 2026-06-18**: authored `observer_condensation_purge_stage0.md`, `observer_settle_vibration_stage2_adxl345.md`, `observer_kinematic_dock_repeatability.md`, `gate6_observer_evidence_row_schema.md` (+ paired blank measurement templates) — falsifiable gated procedures, house-style; each names the real fail-closed gate/model it documents and creates no motion/emission authority | A |
| OP-S1des..S3des, S4evid | **S4evid done** (the observer evidence-packet writer is `observer.py` `mint_observer_scan_evidence`/`observer_scan_evidence_to_packet`/`persist_*`, IN-C4/C5). **S1des..S3des: gated-in-practice by B** — the Stage 1–3 build-drawing CAD depends on the Stage-0/1/2 measured numbers (the next row, OP-B*, is literally "feed numbers to CAD", Bcad→A); authoring build drawings against un-measured focus/WD/settle/dock numbers would bake unproven assumptions into CAD, against the evidence discipline. Defer until the gating measurements land | A |
| OP-B0..Bcad | Stage-0 bench build + the three gating measurements (focus/WD, contrast, field-flatness) + condensation + feed numbers to CAD | B (Bcad→A) |
| OP-S1b..S4opt | Stage 1–4 builds (VCM focus, one-plate settle, full-row traverse, dock/soak/interlock) + optical characterization | B |
| OP-B20 | **Open 2026-09-23 — measure G_obj-ambient** (objective-to-ambient thermal conductance). The 2026-09-23 steady-state model that now gates head selection uses an **estimated** 50 mW/K: at a 37 C bath in a 25 C bay it puts a water 60×/1.20 head at WD 0.31 mm at cells 29.50 C (ΔT 7.50 K), a dry 40×/0.95 at WD 0.18 mm at 1.96 K, a dry 40×/0.60 at WD 3.0 mm at 0.23 K and a dry 20×/0.45 at WD 7.5 mm at 0.15 K. The **ordering** is robust; the **absolute ΔT is not**, and it is what decides whether a 0.3 K sample-plane budget admits anything closer than ~3 mm. Highest-value early measurement | B |
| OP-B21 | **Open 2026-09-23 — objective barrel OD measured 9-11 mm back from the tip** (not the shoulder Ø, not the catalog barrel figure). At short WD the nose enters the 88 × 52 mm tile aperture, and the nose-to-aperture-edge inset (4-10 mm across OD 8-20 mm) is what sets the optically reachable well count. Feeds OC-A9's barrel-vs-keepout split and OC-A17 | B (→A) |
| OP-B22 | **Open 2026-09-23 — borosilicate Raman background** of the CellVis plate's glass bottom at 785 nm over 800-1800 cm-1, measured from below through the coverslip. Catalog row #6 is already throughput-limited to sparse spot-checks; if the substrate's own background swamps the fingerprint region, the through-glass Raman path is dead upstream of the corridor question | B |
| C-OB1..8 | 10× vs 4×, oblique-vs-lid-window, single-vs-split gantry, camera coaxial-vs-offboard, shutter, setpoints, deepen-bay | C |

### Track 5 — SMIS platform (greenfield)

| Item | Produces | Tag |
|---|---|---|
| SM-1.1/1.2 | Dock-plane + 3-2-1 seat CAD + falsifiable dock-envelope asserts — **done** (`src/aevum_smis/dock.py`: quasi-kinematic 3-2-1 seat + falsifiable dock-envelope re-check; SM-1.2 do→review cycle 4, 2026-06-14; reconciled 2026-06-18) | A |
| SM-1.3/1.5a | Swap-kinematics into traverse check; Tier-A/B/C registration ritual skeleton — **done 2026-06-15** | A |
| SM-2.1 | Infinity-port CAD + datum check — **done 2026-06-15** | A |
| SM-2.2 | HEAD-BUS pinout as frozen machine-checkable schema — **done 2026-06-15** | A |
| SM-3.1/3.2a | `module.json` manifest schema + falsifiable envelope re-check; `platform.detect()` auto-ID + cal-vault — **done** (`src/aevum_smis/manifest.py`; SM-3.1 cycle 3 + SM-3.2a cycle 6, 2026-06-14; reconciled 2026-06-18) | A |
| SM-4.1..4.4 | `ModuleDriver` Protocol + plugin loader; `acquire(well,lease)→Evidence` on the bridge lease + Evidence model; fail-closed source-enable; semver policy — **done 2026-06-15** | A |
| SM-B1.4 | **Print the dock, measure ≤5 µm dock-redock repeatability — proves or kills the platform thesis** | B |
| SM-B2.x, H0..H5 | Blind-mate connector + interlock hardware; head builds brightfield→QPI→fluorescence→2nd(FREEZE)→Raman→NV | B |
| SM-4.5 | **Open 2026-09-23 — sampling policy is missing from the Evidence contract.** Full-well tiling does not close. At NA 0.60 on a nameplate 40×, against a Ø6.18 mm (~30.0 mm²) well: **~101 tiles/well** at the Olympus f_ref 180 convention (M_eff 11.11×, 0.216 µm/px, field 0.667 × 0.446 mm = 0.298 mm²) or **~82** at the Nikon f_ref 200 convention (M_eff 10.0×, 0.24 µm/px, 0.741 × 0.495 mm = 0.367 mm²) — the costed ELWD head is a Nikon, so the band should be read, not either endpoint. Over the **128 optically reachable wells** of OC-A17 that is **~12,900 / ~10,500 tiles per pass**, **~1.4 h / ~1.2 h** at 0.4 s/tile, **~164 GB / ~133 GB** per pass at 12.7 MB/frame, and **~7.9 TB / ~6.4 TB** across 48 hourly passes — incompatible with an hourly perturbation-response cadence on either convention, and enlarging the aperture to reach all 384 makes it worse, not better (`sensor_module_interface.md`, § *The intervention ledger (CANDIDATE — recorded, not decided)*, the paragraph "A second candidate from the same session: `fields_per_well` as an explicit Evidence sampling parameter"; `observer_optical_bench.md`, § *Tiling: the throughput term nobody has costed*). *(The 192-well basis previously quoted here — 19,200 tiles, ~2.1 h, ~246 GB/pass, ~11.8 TB — is **withdrawn**: 192 is neither the 384-well grid nor the 128 reachable wells, and has no derivation in the repo. See `sensor_module_interface.md`, § Superseded 2026-09-23.)* The fix is **"N random fields per well" as a first-class, recorded Evidence parameter**, not an undocumented operator habit; unrecorded, the sampling rule is a hidden covariate in every downstream model | A |
| C-SM1..3 | open-vs-closed boundary; the wedge customer; connector scope for un-built modalities | C |

### Track 6 — Decisions + integration (cross-cutting)

| Item | Produces | Tag |
|---|---|---|
| IN-C1/C2 | GX16 observer-umbilical pinout (new authority boundary) + HEAD-BUS reconciled as a superset of GX16 — **done 2026-06-15** | A |
| IN-C3 | Sensor-PCB telemetry → condensation control law (SHT41 dew point; sensors already exist) — **done 2026-06-16** | A |
| IN-C4 | Bridge `observer_scan` lease (mutually-exclusive lease kind) + observer Evidence schema — **done 2026-06-16** | A |
| IN-C5/C6 | `acquire()→Evidence` ABI integration; 16-fiducial registration spine (pose-digest cross-check) — **done 2026-06-16** (`observer.py` evidence path + `aevum_smis/registration.py` `cross_check_observer_pose`; spine closed per realization_hypergraph; reconciled 2026-06-18) | A |
| IN-C7 | OT-2↔observer two-layer safety interlock — **software half done 2026-06-16** (`core/observer_interlock.py`: lease-held enable-intent + pipetting-lease admission, fail-closed); the hardware enable-line/limit-switch half is B | A |
| IN-C8/C9 | Cal-vault/counterfeit authentication extended to observer+SMIS parts — **done 2026-06-16** (`aevum_smis.safety`); the A-geometry (raceway envelope / R10 loop-height) is in OC-A3/A14; the binding R10+GX16/M12 cable-bundle fit at the bend radius is B (caliper measurement) | A |
| IN-C10 | **Open 2026-09-23 — water-immersion amendment decision.** Immersion is recorded as an open proposal against the plate-as-consumable per-well sensing clause (`docs/knowledge/materials_strategy.md`, status note 2026-09-23), **not** as an amendment. Adopting it requires an explicit written amendment to that clause **plus** a `decision_log.md` entry. It buys 28.09% of 4pi collected at NA 1.20 in media n = 1.335 (200× the NA 0.10 path the modality catalog is written around, 5.3× the best dry head) and the least-bad Raman fluid (its dominant band is the OH stretch at ~3000-3800 cm-1, outside the 800-1800 cm-1 fingerprint window, where hydrocarbon oils put strong C-H and C-C bands; its weak ~1640 cm-1 H-O-H bend still overlaps amide I and needs subtracting — uncited, pending OP-B22); it costs a 7.50 K sample-plane deficit without a local 37 C nose heater (OP-B20), meniscus carry-over plate-to-lens-to-plate, and wicking into the ~0.53 mm plate-to-frame seating gap (derived: glass outer z = 11.73 − `plate_support_frame` top z = 11.20; not a caliper measurement) | C |

## Critical path

**To a working observer prototype:**
```
[A] OP-P1+P2 (bench + contrast protocols)
  → [B ¥40] OP-B0 bench → OP-Bb CONTRAST TEST (Driver #1)   ← fail ⇒ optical window in the sealed lid, re-cost gas manifold
  → [C-OB2] illumination commit
  → [B ¥20] OP-S2b ADXL345 SETTLE LOG                        ← resolves single-vs-split gantry + interlock-vs-concurrency together
  → [B] OP-S3b full-row thin-truck traverse (13 mm truck fits + holds ±27 µm over 334.5 mm inside 80 mm)
  → [B] SM-B1.4 dock ≤5 µm repeatability (proves the platform thesis)
  → [B] SM-H0 brightfield head N=1
```
The two B measurements (contrast, settle) are upstream of all architecture. The A
work that de-risks this now: OC-A1/A2/A5/A8 (falsifiable traverse asserts so
Stage-0 numbers slot in cleanly), OP-P1–P5 (protocols so hardware runs record gate
evidence), SM-1.1/1.2/3.1/4.1/4.2 + IN-C4/C6 (dock CAD, manifest, ABI, lease,
registration — so when the dock prints there is software to receive its evidence).

**To closing the row-coupon Gates** (entirely B, hard-sequential): RC-W1 (print 21
STLs) → RC-W3 → RC-W4 → RC-W5 → RC-W6 → RC-W7 → RC-W8 → RC-W9. All A-tier
scaffolding is exhausted; only contingent revisions remain. The two physical
tracks **converge at RC-W8** — Gate-6 needs the observer front-end to physically
exist, so the observer prototype sits on the row-coupon critical-path tail.

## Workflow-addressable cycle queue (tag A, ordered)

**Phase I — cheap unblockers + highest-leverage CAD holes:** OC-A1+A2 → OC-A5 →
OC-A8 → OC-A7 → OC-A12 → OC-A3+A4 → OC-A6 → OC-A9 → OC-A11 → OC-A13 → OT-11.

**Phase II — observer protocol docs (biggest pure-A block; none exist):** OP-P1 →
OP-P2 → OP-P4 → OP-P3 → OP-P5 → OP-P8.

**Phase III — SMIS greenfield + offset authority:** SM-3.1 → SM-1.1+1.2 → OC-A10 →
SM-4.1+4.2 → IN-C4 → ~~OT-6~~ → ~~OT-1~~ → ~~OT-3~~ → (SM-3.2a/4.3/4.4) →
(SM-1.3/1.5a/2.1). *(OT-6/OT-1/OT-3 done 2026-06-17.)*

**Phase IV — integration spec/code + remaining control stack:** follow
`realization_hypergraph.md` HX1→HX5: IN-C4 → IN-C5/C6 → IN-C7(sw) → IN-C8/C9,
then OT-7+OT-8 → OT-12+OT-10 → OT-4/2/5 → OP-S1des..S3des/S4evid.

## What only the engineer can move

**B — the true bottleneck.** Two upstream-of-everything buys: the **¥40 WS2812
matrix** (contrast test — a fail re-architects the lid) and the **¥20 ADXL345**
(settle log — decides gantry + concurrency). Then the ~¥1,940 bench BOM, the
observer Stage chain, the SMIS dock print, and the entire row-coupon Gate chain
(starting with **printing the 38 rigid print pieces** — 46 physical artifacts,
eight flexible/compressible parts outside the rigid queue,
`one_row_coupon.md`, § the "46 physical artifacts / 38 rigid print pieces" contract paragraph). Real-parts lead time: JLCPCB sensor
PCBs, Cole-Parmer mat, tube/cable assemblies.

Added 2026-09-23: three more measurements. **OP-B20** (G_obj-ambient) joins the
contrast and settle buys as upstream-of-architecture, because head selection is
now thermally gated and that gate rests on a 50 mW/K estimate. **OP-B21** is a
caliper on the objective barrel 9-11 mm back from the tip. **OP-B22**
(borosilicate Raman background through the plate bottom) rides on whatever
spectrometer time the row-#6 fork gets, and can kill the through-glass Raman
path before any corridor work is spent on it.

**C — the genuinely product-level calls only you can make:** does the biology
need 10× (sets the focus-tier difficulty), and the wedge customer (gates the third
head and the freeze width). The rest are measurement-gated forks that default
conservative until one B measurement resolves them. **IN-C10** (2026-09-23)
is a third: water immersion would breach the plate-as-consumable per-well
sensing clause, so it cannot be adopted by engineering judgement — it needs an
explicit written amendment to `docs/knowledge/materials_strategy.md` plus a
decision-log entry.

## Recommended next 3 cycles

*(Reconciled 2026-09-23. The 2026-06-17 recommendation — OT-4, then OT-2, then OT-7+OT-8 — is
spent: all three landed on 2026-06-17/18 and are marked done in Track 1, as are the OP-P3/P4/P5/P8
protocol docs it named as the alternative track. The genuinely-open A queue is now the optics /
thermal reporting-and-budget work opened by the 2026-09-23 review, none of which needs hardware.)*

1. **OC-A17 — split `covered_well_count`.** The observer swept-body check reports 384 covered
   wells where 128 are optically reachable; every downstream readiness statement inherits the
   over-claim. Cheapest possible fix (a field split plus a falsifiable assert), and it is the
   number the rest of the optics work is measured against.
2. **OC-A18 — the two `aevum_smis/manifest.py` checks.** The corridor budget is parameterised by
   12 well columns the aperture never admitted (15.56 vs 51.56 mm), and `vertical_required` is an
   additive sum that rejects objectives the solid model says fit. Both are pure arithmetic against
   geometry already measured; both need the existing asserts kept falsifiable, including a hard
   retract-plane assertion.
3. **SM-4.5 — sampling policy as a recorded Evidence parameter.** ~10,500-12,900 tiles and
   ~133-164 GB per pass (Nikon f_ref 200 / Olympus f_ref 180, over the 128 reachable wells of
   OC-A17) is not a schedule; "N random fields per well" has to be declared and carried in the
   Evidence record before any head ships, or the sampling rule becomes a hidden covariate.

Each is genuinely open (verified against the code on 2026-09-23) and software-addressable with zero
hardware. Physical critical path is unchanged in shape, with one addition: **OP-B20**
(G_obj-ambient) now sits alongside the ¥40 contrast and ¥20 settle buys as an upstream-of-
architecture measurement, because head selection is now thermally gated and the gate currently
rests on a 50 mW/K estimate.
