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
  corridor** (120.4 mm), not the bay or the Ø32 keepout — a multi-agent study + empirical
  test found the head must thread the legs (footprint ≤ ~21 mm; a Ø25 barrel strikes them).
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
actually printing 21 STLs and sourcing parts. The **observer** splits into
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
| OT-2 | `set_offset` validation gate + translator, or formal closure (dead op today) | A |
| OT-3 | Physical-event / foreign-command invalidation primitive (`detect_foreign_commands`, whole-history scan for any command not authored by us) — **done 2026-06-17** | A |
| OT-4 | `move_low_z` dry-target translator (gates exist; translator missing) | A |
| OT-5 | `liquid_handling` (wet) translator — design + closed scaffold | A |
| OT-6 | Post-motion high-Z evidence shape + recording path (input to OT-1) — **done 2026-06-17** | A |
| OT-7 | MCP agent adapter `adapters/mcp.py` (no file exists) | A |
| OT-8 | MCP/HTTP pose route-parity tests (no-canonical-default proof) — ship-gate for motion-capable MCP | A |
| OT-9 | HTTP programmatic adapter (optional) | A |
| OT-10 | Recovery runbook + `ot2_abort_or_recover` wiring | A |
| OT-11 | Trajectory/task-graph doc reconciliation (high-Z already landed — stale prose) | A |
| OT-12 | Daemon arm/execute operability (commissioning script) | A |
| OT-B1..B7 | First live commissioning (fresh session, drift checks, home→high-Z, low-Z offset, wet) | B |
| C-OT1..5 | single-writer enforcement, set_offset semantics, autonomy threshold, named-vs-raw first move, evidence sufficiency | C |

### Track 2 — Row-coupon physical (Gate 1→6, hard-sequential)

| Item | Produces | Tag |
|---|---|---|
| RC-W1 | Print the 21-file split batch (PETG) — precondition for everything downstream | B |
| RC-W2 | Procure/blank 12 install-inventory items + real sensor PCBs | B/C |
| RC-W3 | Gate-1 print-QC measurements (21-row worksheet) | B |
| RC-W4 | Gate-2 dry assembly + 5× service cycles | B |
| RC-W5 | Gate-3 OT-2 placement + real toolhead-envelope measurement | B |
| RC-W6 | Gate-4 passive leak / wet-dry / condensate challenge | B |
| RC-W7 | Gate-5 plate/mat metrology + all-384 puncture | B |
| RC-W8 | Gate-6 sensor + observer mechanical seating (converges with the observer track) | B |
| RC-W9 | Operating-prototype acceptance | B |
| RC-W*a | Contingent CAD revisions, triggered only by a measured Gate failure | A |
| RC-W10 | Powered env-control + BSL1 biology (beyond first-print) | B/C |

### Track 3 — Observer CAD hardening (all pure-A do→review)

| Item | Produces | Tag |
|---|---|---|
| OC-A1 | `front_end_body_fits_dry_bay` containment assert + overflow fields in the FE swept-body check (gap: enforced only by a layout test today) | A |
| OC-A2 | Reconcile `front_end_length_x/width_y` ↔ `front_end_scan_axis_footprint` (decoupling bug: oversized body overflows while traverse reports "fits") | A |
| OC-A3 | Falsifiable asserts in the service-raceway check (zero today): outside-bay-X, Z-within-depth, clears boundary rail, R10 loop-height watch | A |
| OC-A4 | Carriage static-box containment + carriage-clears-raceway assert (latent Y-overlap) | A |
| OC-A5 | Focus-stroke-vs-Z-budget assert at traverse level (traverse sweeps the wrong 62 mm height; should be the 40 mm FE swept Z) | A |
| OC-A6 | Make the fiducial-focus check falsifiable (count-only today): multiplicity, within-bay, keepout non-overlap | A |
| OC-A7 | Promote `front_end_service_margin_z` from silent `0.0` to an explicit param | A |
| OC-A8 | Negative "measured 40×40 head @ 25 mm WD" red-case test (proves A1/A2/A5 are genuinely falsifiable — the bench-doc promise) | A |
| OC-A9 | Split circumscribed-diameter into barrel-Ø vs head-bbox (+ `front_end_barrel_diameter`) | A |
| OC-A10 | Encode the SMIS envelope as a CAD assert cross-checking observer params | A |
| OC-A11 | Cross-reference optical-stability checkpoints to the geometry booleans they cite (overflow doesn't propagate today) | A |
| OC-A12 | Gate the razor-thin margins (0.2 mm scan / 0.4 mm traverse) so a param nudge goes red | A |
| OC-A13 | Doc reconciliation (stale line numbers; fold A1–A12 into RH6/RH15/RP5) | A |

### Track 4 — Observer prototyping (protocols A; measurements B; forks C)

| Item | Produces | Tag |
|---|---|---|
| OP-P1..P5, P8 | Missing `docs/protocols/` docs: Stage-0 bench, WS2812 contrast fork, condensation purge, ADXL345 settle, kinematic-dock repeatability, + Gate-6 observer evidence-row schema | A |
| OP-S1des..S3des, S4evid | Stage 1–3 build-drawing CAD + the evidence-packet writer (design-ahead) | A |
| OP-B0..Bcad | Stage-0 bench build + the three gating measurements (focus/WD, contrast, field-flatness) + condensation + feed numbers to CAD | B (Bcad→A) |
| OP-S1b..S4opt | Stage 1–4 builds (VCM focus, one-plate settle, full-row traverse, dock/soak/interlock) + optical characterization | B |
| C-OB1..8 | 10× vs 4×, oblique-vs-lid-window, single-vs-split gantry, camera coaxial-vs-offboard, shutter, setpoints, deepen-bay | C |

### Track 5 — SMIS platform (greenfield)

| Item | Produces | Tag |
|---|---|---|
| SM-1.1/1.2 | Dock-plane + 3-2-1 seat CAD + falsifiable dock-envelope asserts | A |
| SM-1.3/1.5a | Swap-kinematics into traverse check; Tier-A/B/C registration ritual skeleton — **done 2026-06-15** | A |
| SM-2.1 | Infinity-port CAD + datum check — **done 2026-06-15** | A |
| SM-2.2 | HEAD-BUS pinout as frozen machine-checkable schema — **done 2026-06-15** | A |
| SM-3.1/3.2a | `module.json` manifest schema + falsifiable envelope re-check; `platform.detect()` auto-ID + cal-vault | A |
| SM-4.1..4.4 | `ModuleDriver` Protocol + plugin loader; `acquire(well,lease)→Evidence` on the bridge lease + Evidence model; fail-closed source-enable; semver policy — **done 2026-06-15** | A |
| SM-B1.4 | **Print the dock, measure ≤5 µm dock-redock repeatability — proves or kills the platform thesis** | B |
| SM-B2.x, H0..H5 | Blind-mate connector + interlock hardware; head builds brightfield→QPI→fluorescence→2nd(FREEZE)→Raman→NV | B |
| C-SM1..3 | open-vs-closed boundary; the wedge customer; connector scope for un-built modalities | C |

### Track 6 — Decisions + integration (cross-cutting)

| Item | Produces | Tag |
|---|---|---|
| IN-C1/C2 | GX16 observer-umbilical pinout (new authority boundary) + HEAD-BUS reconciled as a superset of GX16 — **done 2026-06-15** | A |
| IN-C3 | Sensor-PCB telemetry → condensation control law (SHT41 dew point; sensors already exist) — **done 2026-06-16** | A |
| IN-C4 | Bridge `observer_scan` lease (mutually-exclusive lease kind) + observer Evidence schema — **done 2026-06-16** | A |
| IN-C5/C6 | `acquire()→Evidence` ABI integration; 16-fiducial registration spine (A1 offset 14.38, 11.24; pose-digest cross-check) | A |
| IN-C7 | OT-2↔observer two-layer safety interlock (software lease + enable-line protocol; hardware half is B) | A |
| IN-C8/C9 | Cal-vault/counterfeit authentication extended to observer+SMIS parts; R10 cable-carrier CAD | A |

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
(settle log — decides gantry + concurrency). Then the ~¥1,885 bench BOM, the
observer Stage chain, the SMIS dock print, and the entire row-coupon Gate chain
(starting with **printing the 21 STLs**). Real-parts lead time: JLCPCB sensor
PCBs, Cole-Parmer mat, tube/cable assemblies.

**C — the two genuinely product-level calls only you can make:** does the biology
need 10× (sets the focus-tier difficulty), and the wedge customer (gates the third
head and the freeze width). The rest are measurement-gated forks that default
conservative until one B measurement resolves them.

## Recommended next 3 cycles

1. **OC-A1 + OC-A2** — FE-body-vs-dry-bay containment + footprint/scan-axis
   reconciliation. Highest leverage per effort: confirmed reproducible hole —
   `front_end_length_x = 60` overflows the bay X by ~19.5 mm while the traverse
   still reports `fits = True`, because the body footprint and the scan span come
   from two decoupled params with no consistency gate. Precondition for the OC-A8
   red-case test.
2. **OP-P1 + OP-P2** — author the Stage-0 bench + WS2812 contrast-fork protocol
   docs. The eight missing `docs/protocols/` observer docs are the biggest pure-A
   block, and the contrast test is the most upstream experiment in the program.
3. **SM-3.1** — `module.json` manifest schema + falsifiable envelope re-check,
   reusing the `8 + FE_z + stroke ≤ 62` / barrel-Ø ≤ 32 arithmetic so a manifest
   claiming an envelope it does not fit is rejected at dock.

These three touch disjoint files (CAD / docs / Python schema) and each unblocks
its track with zero hardware and zero pending decisions.
