# Aevum Realization Hypergraph

## Purpose

This hypergraph coordinates the path from current code/CAD scaffolds to a
working observer row module across seven realization branches.

`remaining_work.md` owns the canonical backlog item list. This document owns the
cross-branch dependencies, do-review closure rules, authority boundaries, and
review questions that keep those items from becoming redundant parallel task
lists.

## Cycle Rule

Every branch advances by a do-review-context cycle:

```text
do
  -> change one authority-bearing surface: code, CAD, protocol, evidence schema,
     physical measurement, or decision record
review
  -> run focused tests or physical checks, inspect the relevant artifact, and name
     what remains unproven
context
  -> update only the durable source-of-truth docs/knowledge entries that changed
     meaning; leave item inventory in remaining_work.md
```

A node is not closed by implementation alone. It closes only when the review
artifact proves the claimed authority and the next unblocked edge is visible.

## Engineering Distinction

The graph keeps these authorities separate:

- **Mechanical authority:** CAD geometry, printed parts, measured fit, and service
  order.
- **Electrical authority:** GX16/HEAD-BUS pinouts, rails, interlocks, shield,
  data lanes, and no-hot-mate rules.
- **Optical authority:** infinity port, PD-0, contrast, focus, vibration,
  condensation, and registration spine.
- **Software authority:** bridge leases, evidence packets, claims, gates,
  adapters, and fail-closed state transitions.
- **Biology/process authority:** humidity, CO2, evaporation, cleaning, BSL1
  compatibility, and operating-prototype acceptance.
- **Decision authority:** unresolved C nodes where code must not pretend the
  product choice is already made.

If a cycle crosses two authorities, the review must name both and prove the
handoff. Example: a bridge `observer_scan` lease is software authority; the
enable-line it gates is electrical authority; the proof must not blur them.

## Seven Branches

```text
RB1 physical measurement + procurement gates
  owns: real buys, caliper runs, contrast test, settle log, dock-redock test
  source: critical-path and B/C rows in remaining_work.md
  review: measurement packets, photos/logs, receipts/part IDs, pass/fail records
  stop: no code may promote a physical claim without a physical evidence handle

RB2 row-coupon operating-prototype gates
  owns: RC-W1..RC-W10 and Gate 1..6 evidence chain
  source: one_row_coupon_first_print_readiness.md and row_coupon_cycle_log.md
  review: print QC, dry assembly, OT-2 placement, leak/wet-dry, puncture, Gate 6
  stop: CAD proxy closure cannot become operating-prototype acceptance

RB3 observer CAD hardening
  owns: OC-A* pure-A falsifiable CAD assertions and validation bodies
  source: row_coupon_revision_hypergraph.md plus remaining_work.md OC rows
  review: focused CAD tests, validation STEP/STL exports, viewer/screenshot check
  stop: oversized/negative cases must go red before a geometry claim closes

RB4 observer protocols + stage builds
  owns: OP-P*, OP-S* design-ahead, Stage-0..4 evidence writers
  source: observation_module.md and docs/protocols
  review: protocol completeness first, then measured Stage evidence
  stop: stage design may reserve interfaces but cannot claim measured contrast,
        settle, condensation, or traversal performance

RB5 SMIS platform/dock/head authority
  owns: dock plane, manifest, HEAD-BUS, infinity port, compatibility, registration,
        source-enable, cal-vault, ModuleDriver ABI
  source: sensor_module_interface.md and src/aevum_smis
  review: typed schemas, fail-closed validators, focused SMIS tests
  stop: mechanical dock acceptance, registration, compatibility, and source-enable
        must remain separate gates

RB6 integration bridge + observer safety weave
  owns: IN-C* bridge lease, observer evidence schema, registration spine,
        two-layer interlock, observer/SMIS authentication, service routing
  source: this graph plus remaining_work.md Track 6
  review: cross-authority tests that prove exclusivity, evidence shape,
        fail-closed interlocks, and no implicit motion permission
  stop: no observer acquisition without a valid lease, registration, condensation
        gate, source-enable decision, and evidence output path

RB7 OT-2 control stack
  owns: OT-* offset authority, physical-event invalidation, translators,
        MCP/HTTP adapters, recovery, commissioning
  source: task_graph.md, divergence_task_graph.md, docs/knowledge/evidence_model.md
  review: transaction-backed evidence, gate tests, adapter parity, recovery tests
  stop: no adapter can create motion authority; only the bridge core can mint and
        consume bounded approvals
```

## Cross-Branch Hyperedges

```text
HX1 observer scan authority
  branches: RB5, RB6, RB7
  do: define `observer_scan` lease and observer evidence schema
  review: prove mutual exclusion with OT-2 lease/motion state, reject missing or
          stale lease, emit evidence handles
  context: sensor_module_interface.md, evidence_model.md, remaining_work.md
  next: IN-C4

HX2 16-fiducial registration spine
  branches: RB3, RB5, RB6, RB7
  do: connect plate-support fiducials, SMIS registration tiers, pose digest, and
      observer evidence
  review: prove A1 offset/sign conventions and stale-pose rejection
  context: coordinate_system.md, sensor_module_interface.md, task_graph.md
  next: IN-C5/C6

HX3 two-layer observer interlock
  branches: RB5, RB6, RB7
  do: split software lease authority from hardware enable-line semantics
  review: prove lease release disables observer enable and pipetting lease is
          refused until observer parked/Z-retracted evidence exists
  context: observation_module.md, power_section.md, sensor_module_interface.md
  next: IN-C7

HX4 observer identity and counterfeit boundary
  branches: RB5, RB6
  do: extend cal-vault/counterfeit checks to observer and SMIS parts without
      merging them with compatibility or registration
  review: challenge/response tests, manifest digest binding, fail-closed source
          enable
  context: sensor_module_interface.md, power_section.md, sensor_pcb.md
  next: IN-C8

HX5 service routing and cable carrier
  branches: RB2, RB3, RB5, RB6
  do: reconcile R10 cable carrier, GX16/HEAD-BUS/M12 routes, wet/dry boundary,
      and row-to-row service access
  review: CAD clearance tests, bend-radius checks, service-state review
  context: one_row_coupon.md, observation_module.md, power_section.md
  next: IN-C9

HX6 physical observer truth
  branches: RB1, RB3, RB4, RB5
  do: turn contrast, settle, condensation, traverse, and dock-redock measurements
      into evidence packets consumed by gates
  review: measured packets beat CAD/prose proxies; failed measurements fork C
          decisions instead of being patched over
  context: protocols, decision_log.md, remaining_work.md
  next: OP-B*, SM-B1.4

HX7 row-coupon operating prototype acceptance
  branches: RB1, RB2, RB4, RB6, RB7
  do: join Gate 1..6 row-coupon evidence with observer seating, safety lease, and
      OT-2 placement/operation evidence
  review: operating-prototype acceptance stays false until every gate has real
          evidence and no dimensional blanks remain
  context: one_row_coupon_first_print_readiness.md, evidence_model.md
  next: RC-W8/RC-W9
```

## Active Queue

```text
done
  -> HX1 / IN-C4: observer_scan lease + observer Evidence schema (2026-06-16)
       lease_kind on BridgeLock; aevum_ot2.core.observer; ObserverScanEvidence ->
       EvidenceHandle(observer_frame). Mutual exclusion proven; minting fail-closed
       against the lease only (registration/source-enable/interlock kept separate).
  -> HX2 / IN-C5 (full): ObserverScanEvidence AND generic SMIS ModuleEvidence -> durable
       EvidencePacket via the transaction store (2026-06-16). Packets-only, no claims (no
       bare-packet motion authority); fail-closed on forged lease_kind / missing lease_owner /
       mixed sessions. The SMIS mapping uses a SensorModuleEvidenceLike structural Protocol —
       neither core package imports the other (the bridge<->SMIS fork resolved). The
       "evidence output path" the stop-condition requires now exists for every modality.
  -> HX2 / IN-C6 (pose cross-check): cross_check_observer_pose + ObserverPoseCheck in
       aevum_smis.registration (2026-06-16). Stale-declared-pose, residual-over-tolerance,
       <3-fiducial, and malformed-digest rejection — each a named blocker, distinct from the
       Tier A/B/C ritual. Binds on opaque digests (no bridge import). A1 offset/sign already
       single-sourced in the CAD well map.

  -> HX3 / IN-C7 (software half): observer_interlock.py (2026-06-16). observer_enable_intent
       (lease-held => enable intended, NOT the hardware enable) + pipetting_lease_admission
       (refused while observer lease active; after release, until a fresh parked+Z-retracted
       ObserverParkReport). Fail-closed, named blockers. Hardware enable-line/limit switch = B.
  -> HX4 / IN-C8: cal-vault/counterfeit (2026-06-16). Substance already built
       (aevum_smis.safety, SM-3.2a/4.3/4.4); review confirmed the head is the only crypto-
       cal-vault part (non-head parts ride the receiving-step COTS discipline, decision_log
       2026-05-28). Added the HX4 "without merging compatibility/registration" proof: the
       three authorities are independent functions over independent inputs.
  -> HX5 / IN-C9 (A-geometry): the raceway envelope, R10 loop-height Z budget, dry-bay-sweep
       and boundary-rail clearances are already in OC-A3/OC-A14, and the GX16/HEAD-BUS/M12
       route reconciliation is in IN-C1/C2. The binding cable-bundle fit is B-gated (below).

the IN-C1..C9 cross-branch integration spine is closed to its software/CAD-addressable
boundary; OT-1 (offset authority) and OT-3 (foreign-command invalidation) are now done
(2026-06-17), leaving the remaining now-queue in the OP-P* protocol-doc track.

now (decision/measurement-gated tails of closed edges)
  -> HX5 / IN-C9 (binding, B): does the real R10 chain + GX16/M12 bundle fit the 8 mm raceway
       thin dimension at the bend radius — caliper the chain with cable in it (no faked ODs)
  -> HX6 IN-C6 tail: the residual tolerance + the sub-pixel centroiding/Umeyama fit that
       produces recovered_residual_um (Stage-0/Stage-3 metrology, B)
  -> HX3 / IN-C7 (hardware half, B): GX16 enable line, 24 V rail cut, physical parked limit,
       and the measured DEFAULT_MAX_PARK_AGE freshness window (Stage-4 interlock build)

parallel physical unblockers
  -> HX6: contrast test, settle log, dock-redock repeatability
  -> HX7: row-coupon Gate chain after printed parts exist
```

## Review Questions

- Which authority changed: mechanical, electrical, optical, software, biology,
  or decision?
- Which existing source of truth owns the detailed item list?
- What evidence proves the new claim: test, CAD artifact, physical measurement,
  transaction, or decision record?
- What remains symbolic, reserved, or hardware-gated?
- Does the change create an implicit permission to move, emit light, heat, purge,
  or acquire data?
- Does the review include a negative case that fails closed?
- Which next hyperedge is now unblocked?

## Stop Conditions

Stop and revise the graph if:

- a node duplicates a backlog table instead of naming a cross-branch dependency;
- a software gate promotes CAD/prose into physical evidence;
- a lease, registration, compatibility, source-enable, or condensation decision
  is merged into a generic success boolean;
- a physical measurement fails and the graph tries to continue without a C-node
  decision;
- docs move without tests/evidence for an implemented claim;
- code moves without updating the source-of-truth context for a changed authority.
