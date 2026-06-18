# Row Coupon Revision Hypergraph

## Purpose

This graph controls how the one-row coupon evolves from production-shaped CAD
into production-like assembly behavior.

A normal task list is not enough here. A CAD change can touch geometry, tests,
generated artifacts, viewer state, design claims, and knowledge-base context at
the same time. This document treats each revision as a hyperedge: one unit of
work that connects all of those nodes and is incomplete until the connected
evidence and context have been reviewed.

## Cycle Rule

Every row-coupon revision uses the same do-review-context cycle:

```text
do
  -> revise params / CadQuery builders / tests / generated artifacts
review
  -> inspect CAD intent, run focused tests, run full checks when scope warrants,
     smoke the viewer, and name remaining mechanical gaps
context
  -> update one_row_coupon.md, print_native_row_module.md, task graph links,
     decision log when stance changes, and final working context
```

A hyperedge is not closed by code alone. It closes only when:

- the physical claim is named;
- the CAD object carrying that claim is a production part or an explicit
  validation check;
- the generated files and CQ-Editor scene show the intended object set;
- tests protect the claim against easy regression;
- the first-print split operating-prototype acceptance audit refuses
  production-operating acceptance until print-start artifacts and the complete
  Gate 1-6 physical evidence chain are ready;
- the knowledge base states what was proven and what remains symbolic;
- the next edge is visible.

## Node Sets

```text
C* claim nodes
  C1 production assembly tree
  C2 print-native no-metal/no-glue force path
  C3 serviceable COTS plate and septum insert path
  C4 row-shared contained wet headspace
  C5 dry observer swept-body clearance
  C6 OT-2 per-slot deck fit
  C7 real COTS consumable geometry and puncture behavior
  C8 thermal, condensation, and evaporation authority
  C9 leak, pressure relief, and spill isolation
  C10 BSL1 material, cleaning, and biological compatibility
  C11 optical quality, stray light, vibration, and focus stability
  C12 row tiling, service routing, and external module interfaces
  C13 assembly-state sensing, QC gauges, and operator error resistance

G* geometry nodes
  G1 deck_pods
  G2 plate_support_frame
  G3 lower_gasket
  G4 wet_chamber_frame
  G5 cots_microplates
  G6 cots_septum_mats
  G7 upper_gasket
  G8 lid_manifold_shell
  G9 lid_cover
  G10 printed_wedge_locks, wet-frame tension posts, and lid receiver rails
  G11 validation-only keepouts and swept volumes
  G12 exploded/service views
  G13 measured plate and septum mat profiles
  G14 pipette tip/cone swept paths and puncture-force load path checks
  G15 pressure relief, drain, spill, and wet/dry isolation features
  G16 thermal/condensation control placeholders and sensor/heater carriers
  G17 optical baffles, fiducials, focus targets, and vibration keepouts
  G18 row-to-row tiling, service-bus, tube/cable bend, and connector checks
  G19 print QC gauges, assembly-state witnesses, and error-proofing features

E* evidence nodes
  E1 focused CAD tests
  E2 full lint and test suite
  E3 generated STL/STEP artifacts
  E4 CQ-Editor installed-part scene
  E5 visual or screenshot review when geometry is hard to read from bounds
  E6 physical print and measurement record
  E7 leak, fog, flow, humidity, condensation, and observer-sweep checks
  E8 COTS plate and septum metrology
  E9 pipette puncture force, repeat puncture, septum reseal, and tip-deflection tests
  E10 thermal/RH/CO2 response, evaporation, edge-effect, and condensation evidence
  E11 material compatibility, cleaning, leachable/odor, and BSL1 survival controls
  E12 pressure relief, leak-rate, spill, and wet/dry failure evidence
  E13 optical contrast, focus repeatability, vibration, and stray-light evidence
  E14 row tiling, external service routing, and connector strain-relief evidence
  E15 slicer, print QC, gauge, and assembly-state inspection evidence

K* context nodes
  K1 one_row_coupon.md
  K2 print_native_row_module.md
  K3 task_graph.md
  K4 decision_log.md
  K5 architecture/materials/hardware lessons pages when system stance changes
  K6 final turn summary and active residual gaps
  K7 row_coupon_cycle_log.md
```

## Hyperedges

```text
RH0 production part-tree baseline [closed]
  claims: C1, C2, C3
  geometry: G1, G2, G3, G4, G5, G6, G7, G8, G9, G10
  evidence: E1, E2, E3, E4
  context: K1, K2, K4, K6, K7
  residual gap: parts have correct identity, but several interfaces are still
  simplified bodies rather than working printed mechanisms.

RH1 pod/frame mechanical joint [CAD-proxy closed; seating-cycle pending]
  claims: C2, C5, C6
  geometry: G1, G2, G11
  do: add printed pod/frame locating joints, insertion direction, release
  clearance, anti-yaw constraint, witness features, and the required
  `deck_pod_seating_repeatability_check`.
  review: Gate 3 must prove five printed-row OT-2 deck seat/release cycles,
  no rocking/yaw, no pod/key wear that affects seating, no deck-frame contact,
  and no dry-bay debris bridge before operating deck use.
  context: update K1, K2, K3, K6, and K7.

RH2 gasket capture and squeeze control [CAD-closed; section-print pending]
  claims: C2, C4
  geometry: G2, G3, G4, G7, G8
  do: add upper and lower gasket grooves, keyed seats, service tabs, corner
  reliefs, compression stops, and witness marks.
  review: prove gaskets cannot slide into the headspace or observer aperture,
  squeeze height is hard-stop limited, and service tabs do not create leak
  shortcuts.
  context: update K1, K2, K3, K6, and K7.

RH3 wedge/receiver compression mechanism [CAD-proxy closed; force-cycle pending]
  claims: C2, C4
  geometry: G4, G8, G9, G10
  do: realize the latch as an assembled print-native stack: wet-frame tension
  posts/caps, lid receiver rails, side-insert U-slotted wedges, stop faces,
  high bearing flats, anti-lift capture lips, detent bumps, raised witness
  marks, visible latch positions, and release geometry.
  review: confirm latch force lands on perimeter rails, never over septum access
  windows, clears lid service ports, and does not interfere with OT-2 adjacency
  or observer sweep. Current layout data also exposes M0-M3 first-print
  mechanical screens: compression budget, ramp self-lock/backdrive margin,
  post/cap/root stress, and omitted latch-station span risk. The self-lock
  margin is positive but below target, and the omitted port-side station creates
  an explicit span warning. The first-print handoff now requires
  `latch_retention_span_check`, a validation-only Gate 2 blocker tying those
  risks to dry-cycle detent hold, omitted-station bow, post/cap bearing, and
  gasket-squeeze-after-cycle evidence.
  context: update K1, K2, K3, K4 if the locking stance changes, K6, and K7.

RH4 lid shell/cover reversible duct seal [CAD-closed; leak-cycle pending]
  claims: C2, C4
  geometry: G8, G9
  do: add tongue-and-groove, labyrinth, trapped printed gasket, or equivalent
  print-native shell/cover seal path for ducts and service bosses.
  review: inspect printability, trapped-support risk, duct continuity, service
  access, and humid-cycle disassembly path.
  context: update K1, K2, K3, K6, and K7.

RH5 wet-chamber boundary and routing [CAD-proxy closed; humid-cycle pending]
  claims: C4
  geometry: G3, G4, G7, G8, G9, G11
  do: require `headspace_barrier_check`, `headspace_volume_check`,
  `dry_bay_envelope_check`, and `dry_bay_boundary_check` in the first-print
  handoff alongside wet/dry boundary, side service lanes, diffuser windows,
  return slots, sampling/relief path, condensation low points, and wipe access.
  review: the required Gate 4 barrier and volume bodies make the sealed
  perimeter and one shared row volume inspectable, while the required dry-bay
  envelope and boundary bodies make the protected observer volume and side
  rails inspectable before any wet/dry pass claim. Humid-cycle, leak,
  condensate, continuity, and dry-bay ingress behavior still require physical
  evidence.
  context: update K1, K2, K5 when environmental stance changes, K6, and K7.

RH6 observer module swept body [CAD-proxy closed; physical evidence pending]
  claims: C5
  geometry: G1, G2, G11
  do: require `observer_front_end_swept_body_check`,
  `observer_carriage_envelope_check`, `observer_service_raceway_envelope_check`,
  and `observer_kinematic_split_check` alongside the fiducial/focus target
  checks.
  review: the required Gate 6 envelope and split checks block observer
  readiness until the compact front end, larger carriage, focus recovery, and
  service loop are physically reviewed as separate mechanisms. CAD still does
  not prove observer installation, focus, vibration, or signal quality. The
  OC-A1..A9/A14 hardening makes each observer body fail-closed on its own
  geometry rather than on a single layout-level test: every swept and reserved
  box now runs the shared `_dry_bay_containment` overflow helper, so the
  front-end body reports `front_end_body_fits_dry_bay`/`front_end_body_overflow_mm`
  (OC-A1) and the static carriage box reports
  `carriage_box_fits_dry_bay`/`carriage_box_overflow_mm` (OC-A4) -- an oversized
  measured dimension surfaces an overflow here instead of silently passing. The
  scan-axis traverse span is tied to the head body via
  `max(front_end_scan_axis_footprint, front_end_length_x/width_y)` (reported as
  `scan_axis_extent_mm`, OC-A2), closing the decoupling where an oversized body
  could overflow the bay while the traverse, reading only the smaller
  scan-footprint param, still read "fits". The service raceway, which had no
  asserts, now carries falsifiable ones -- `raceway_clears_dry_bay_sweep`,
  `raceway_z_within_bay_depth`, `r10_loop_fits_raceway_z`, gated by
  `raceway_geometry_clears` (OC-A3) -- and the thin-truck traverse adds its own
  `fits_dry_bay`/`clears_traverse`, `deck_foot_collision_count`, and
  `adjacent_slot_collision_count` asserts (OC-A14). The front-end vertical budget
  now sums an explicit `front_end_service_margin_z` param into
  `vertical_budget_required_mm`/`front_end_vertical_budget_closes` (OC-A7). The
  conflated objective gate is split into the authoritative round-barrel keepout
  `front_end_barrel_fits_keepout` (barrel Ø vs `objective_keepout_diameter`) and
  the separate head-bbox-vs-dry-bay `front_end_body_fits_dry_bay` (OC-A9).
  context: update K1, K3, K5, K6, and K7.

RH7 service and exploded states [CAD bounds evidence closed; physical service pending]
  claims: C1, C3
  geometry: G1 through G10, G12
  do: add installed, lid-off, mats-exposed, wet-frame-off, plates-removable, and
  exploded/service viewer modes, including connected-service negative review
  states such as missing service leads and unmated electrical connectors, with
  exported validation bodies when the state protects first-print operating
  acceptance.
  review: the service-state worksheet now covers every installed, service, and
  negative-review viewer mode. Its ready audit rejects pass claims unless each
  row references an existing screenshot or generated bounds CSV, and each bounds
  CSV matches the mode metadata, has positive part bounds, removes expected
  missing parts, and includes the negative-review witness parts. Physical
  serviceability still requires later assembly evidence that no step requires
  bending plates, peeling trapped mats, or inaccessible release moves.
  context: update K1, K2, K3, K6, and K7.

RH8 passive flow and environmental proxy setup [CAD-proxy closed; wet evidence pending]
  claims: C4
  geometry: G4, G8, G9, G11
  do: require `gas_pcb_flow_cell_check` in the first-print handoff alongside
  smoke/fog, humidity tracer, shallow-water disturbance, and condensation
  inspection proxies without changing the core production assembly tree.
  review: gas PCB aperture, dead-volume, and gasket registration now have a
  required Gate 6 validation body; define what each proxy can and cannot prove
  and keep biology claims blocked until measured.
  context: update K1, K2, K5, K6, and K7.

RH9 print/package review [CAD-proxy closed; print evidence pending]
  claims: C2, C3
  geometry: G1 through G10
  do: require `printability_support_cleanup_check` in the first-print handoff
  alongside print orientations, tolerance allowances, sacrificial/wear parts,
  support cleanup risk, material split, and post-print inspection features.
  review: support scars on gasket lands, debris in wedge slide paths, blocked
  side-gas barbs, blocked sensor pockets, bridged dry-bay gutters, and
  split-edge cleanup damage now have a required Gate 1 validation body. Actual
  print quality remains blocked until the physical Gate 1 rows pass.
  context: update K2, K3, K5, K6, and K7.

RH10 COTS consumable metrology [CAD-proxy closed; measurement pending]
  claims: C3, C7
  geometry: G5, G6, G13, G14
  do: require `consumable_metrology_gauge` in the first-print handoff and
  measure the actual plate rim, skirt, underside support lands, glass window
  recess, septum sheet, round plugs, slit depth/width, seated height, and mat
  swelling after wet exposure.
  review: replace placeholder dimensions only where they affect support,
  puncture, sealing, imaging, or service removal; keep published plate X/Y truth
  unless fit evidence contradicts it. The printable metrology gauge is now a
  required Gate 5 validation body, and the coupon plate footprint aligns to the
  persisted CellVis profile; mat plug/slit/seated-height values remain
  placeholder-gated.
  context: update K1, K2, K5, K6, and K7.

RH11 liquid-handler puncture mechanics [CAD-proxy closed; force evidence pending]
  claims: C3, C7, C13
  geometry: G6, G8, G9, G14, G19
  do: require `pipette_puncture_swept_path_check` in the first-print handoff
  alongside septum puncture depth, puncture-force limit, repeat-cycle, plate
  shift, tip-deflection, and post-puncture reseal evidence.
  review: all 384 septum targets now have a required Gate 5 swept-path body,
  separate from the larger OT-2 toolhead envelope. Force, deflection, reseal,
  plate shift, and liquid-handling behavior still require physical puncture
  evidence before access claims pass.
  context: update K1, K3, K5, K6, and K7.

RH12 thermal, evaporation, and condensation authority [CAD-proxy closed; physical evidence pending]
  claims: C4, C8
  geometry: G4, G7, G8, G9, G16
  do: export `thermal_condensation_proxy_check`, driven from the same layout
  values as the plate-center cell-plane references, plate-margin IR FOV spots,
  SHT41 headspace drip-ring apertures, and wet-chamber condensation low-point
  pockets. Keep heater/lid-warming authority as a measured follow-on, not a
  visual placeholder.
  review: CAD now exposes the Gate 6 thermal/condensation measurement map, but
  incubation claims remain blocked until thermal/RH/CO2 recovery, evaporation,
  edge-effect, and condensation evidence exists for all four plate positions.
  context: update K1, K2, K5, K6, and K7.

RH13 pressure relief, leak hierarchy, and spill isolation [CAD-proxy closed; physical evidence pending]
  claims: C4, C9
  geometry: G3, G4, G7, G8, G9, G15
  do: require the existing side-gas, sample/relief-cap, and gasket-tab leak
  witness STEP/STL bodies in the first-print handoff, alongside the headspace
  barrier/volume checks, dry-bay envelope/boundary checks, wet/dry failure-path,
  and dry-bay ingress audit overlays that bound dry observer exposure.
  review: CAD now exposes the Gate 4 leak hierarchy and sealed-headspace
  perimeter in the package, but septum puncture pressure pulses, overpressure,
  condensate, and plate leakage remain unproven until dye/condensate/spill
  evidence shows liquid cannot silently route into the dry observer bay.
  context: update K1, K2, K5, K6, and K7.

RH14 BSL1 material, cleaning, and biological compatibility [CAD-proxy closed; physical evidence pending]
  claims: C10
  geometry: G3, G4, G5, G6, G7, G8, G9, G19
  do: define installed surface exposure/disposition in the manifest and export
  `material_cleaning_witness_coupon`, a required validation-only coupon set for
  same-material cleaning, soak, scrub, odor, and exposure observations on
  cleaning-pending printed and flexible/elastomer surfaces.
  review: keep biology claims blocked until material exposure, cleaning,
  leachables/odor, contamination, and survival controls are recorded. The coupon
  set deliberately excludes disposable COTS consumables, electronics, cable
  leads, and tubing so the package does not imply those are cleaned or
  biologically qualified by printed witness geometry.
  context: update K2, K5, K6, and K7.

RH15 optical quality and observer stability [CAD-proxy closed; physical evidence pending]
  claims: C5, C11
  geometry: G2, G5, G11, G17, G18
  do: add optical baffle, stray-light, reflection, focus target, vibration,
  thermal drift, local fiducial, and measured-performance blocker requirements
  for the compact front-end head.
  review: distinguish geometric clearance from usable imaging, Raman, or
  biophotonics signal quality. The CAD now exports local observer
  fiducial/focus target geometry and the required
  `observer_optical_stability_check` first-print validation blocker, but
  optical performance evidence remains a physical Gate 6 requirement. The OC-A11
  hardening makes geometry overflow propagate into this check: it now folds an
  `observer_geometry_clears` verdict over the front-end body, carriage box,
  carriage `clears_traverse`, raceway `raceway_geometry_clears`, and fiducial
  clearance, and appends a hard `geometry_overflow_blocks_optical_stability`
  blocker when any of them fails -- so a geometry overflow can no longer read as
  "only physical evidence pending." OC-A12 surfaces razor-thin margins as
  fail-soft warnings (`traverse_margin_is_razor_thin`,
  `scan_margin_is_razor_thin`, threshold `razor_thin_margin_warn_threshold_mm`)
  so a sub-millimeter param drift cannot erode a positive-but-tiny margin
  silently. OC-A15 adds scan-corridor diagnostics that report both real
  scan-axis walls -- the standoff-leg corridor (`scan_corridor_width_mm`,
  `scan_corridor_margin_mm`) and the milled per-wall dry-bay clearance
  (`scan_bay_per_wall_margin_mm`) -- and binds the razor-thin flag to the
  tightest of the two via `scan_binding_margin_mm`, and surfaces the diagnostic
  barrel-vs-corridor checks (`front_end_barrel_within_head_footprint`,
  `barrel_threads_scan_corridor`, mirroring the SMIS
  `scan_corridor_footprint_max` dock gate) that flag, without autonomously
  overturning the "fits" verdict, that a realistic objective barrel does not
  thread the placeholder-driven scan corridor.
  context: update K1, K3, K5, K6, and K7.

RH16 row tiling and service interfaces [CAD-proxy closed; physical evidence pending]
  claims: C6, C12
  geometry: G1, G2, G4, G8, G9, G18
  do: model adjacent-row keepouts, vertical service exits, external service
  dress, tube/cable bend radii, connector/service strain relief, and
  install/remove clearance on a populated OT-2 deck. CAD now exports
  `row_tiling_service_clearance_check`, a required validation-only composite
  body joining the installed row footprint, adjacent OT-2 slot keepouts, and
  operating gas/electrical service envelopes. Gate 6 also requires
  `sensor_connector_service_clearance_check` alongside cable-envelope and
  electrical connector mating-state checks.
  review: physical Gate 3 evidence must still prove the printed, dressed row
  does not become a side protrusion or prevent neighboring row modules,
  pipette motion, or observer travel, while physical Gate 6 evidence must prove
  connector mating/service clearance before side electrical service can support
  sensor readiness.
  context: update K1, K3, K5, K6, and K7.

RH17 assembly state, QC, and fail-closed operation [CAD-proxy closed; physical evidence pending]
  claims: C1, C13
  geometry: G10, G12, G19
  do: add latch-state witnesses, gasket-compression gauges, orientation keys,
  no-plate/no-mat visible states, print QC gauges, and post-service inspection
  features. CAD now exports `fail_closed_prerun_inspection_check`, a required
  validation-only pre-run blocker checklist tying negative states, out-of-range
  gasket squeeze, unmated connectors, service-dress collisions, and hidden
  witness paths to visual, manual-cycle, or caliper evidence.
  review: define which states can be checked by eye, camera, caliper, or later
  sensors before any OT-2 run assumes the module is assembled correctly. The CAD
  now exports a required assembly-state witness validation body that combines
  missing-plate, missing-mat, missing-perimeter-gasket, missing-gas-PCB,
  missing-service-lead, missing-sample/relief-cap, and unseated-latch witness
  geometry. It also exports a required gasket-compression gap gauge with
  min/target/max squeeze reference blades from the latch compression budget.
  These are still package checks; real operator inspection, gasket compression,
  service cycling, dry-bay inspection, and fail-closed behavior remain Gate 1-6
  evidence.
  context: update K1, K2, K3, K6, and K7.
```

## Active Order

The CAD-level pass for RH1-RH9 is recorded in:

```text
docs/engineering/row_coupon_cycle_log.md
```

The next productive physical/review loop is:

```text
RP1 lower-stack print cycle
RP2 compression-stack print cycle
RP3 service-state CAD bounds review ready; physical service evidence pending
RP4 passive flow and humidity proxy cycle
RP5 observer kinematic split
RM1 missing-gap graph expansion
RH10/RH11 consumable metrology and puncture validation
RP6 first-print split operating-prototype acceptance after Gate 1-6 evidence
```

CAD closure means the interface exists as owned geometry with tests and context.
It does not mean the interface has survived assembly cycles, humid exposure,
leak testing, or biology. Those are the RP* cycles in the cycle log.

The latch-specific M0-M3 overlay has now moved RH3 from geometry-only closure
to CAD mechanical screening. The current production layout reports a bounded
compression budget, explicit ramp/self-lock margin, simple post/cap/root stress
screen, and the port-driven latch-station asymmetry. This is still not physical
closure. M4-M10 remain open: slicer support evidence, a production-matched latch
coupon, release usability, asymmetry mitigation, bench force/compression
protocol, integrated compression-stack testing, and full coupon print release.

RP5 (observer kinematic split) is the productive loop that the OC-A1..A12 and
A14/A15 observer-CAD hardening advances. It is no longer a single swept-body
claim: the four observer checks each model a separate mechanism with its own
falsifiable asserts -- the compact front-end body
(`observer_front_end_swept_body_check`, now gating `front_end_body_fits_dry_bay`,
the barrel/keepout split `front_end_barrel_fits_keepout`, and the
`front_end_service_margin_z`-aware `front_end_vertical_budget_closes`), the
static reserved carriage box (`observer_carriage_envelope_check`,
`carriage_box_fits_dry_bay`), the thin-gantry-truck traverse
(`carriage_traverse` with `clears_traverse`, `fits_dry_bay`, and the
body-tied `scan_axis_extent_mm`), and the service-loop raceway
(`observer_service_raceway_envelope_check`, `raceway_geometry_clears`). The
44.6 mm Y overflow the earlier model flagged is resolved at the layout level by
the thin-truck topology, with the residual burden surfaced -- not hidden -- on the
scan axis as a razor-thin ~0.2 mm margin (OC-A12/A15 diagnostics) that excludes
the post-fold camera arm. This is geometric/topological closure against
PLACEHOLDER head footprints only; the achievable beam width, real barrel and
head footprints, camera-routing strategy, and whether a thin truck can traverse
the full row inside the bench hold-still spec stay Gate-6 / Stage-0 physical work.

The material-authority conflict is resolved for the one-row coupon first-print
path by decision log entry `2026-06-04: First-Print Row Coupon Has No Hidden
Authority Parts`. The package manifest carries that decision as a
machine-readable policy and supersedes the older 2026-05-06 authority-insert
stance for this coupon's mechanical assembly. Any future exception must become
a new explicit decision with tests, generated artifacts, and physical service
evidence.

RM1 expands the graph around domains that the first CAD closure did not cover:
real consumable metrology, puncture force, thermal authority, pressure relief,
biology/material compatibility, optical quality, service routing, tiling, and
fail-closed assembly state.

## Review Questions

Each do-review cycle must answer these before closure:

- Which physical claim did this geometry make stronger?
- Which part owns the datum, seal, latch, service, or failure authority?
- What is still a placeholder or visual proxy?
- What would break during ten assembly/disassembly cycles?
- What changes after humid exposure, cleaning, or print warp?
- Does the liquid handler still reach all 96 septum targets per plate?
- Does the observer swept body still reach all well centers?
- Did the generated exports, tests, viewer, and docs move together?

## Stop Conditions

Stop the current CAD edge and revise the graph if:

- a printed interface needs metal, glue, heat staking, or hidden bonded authority
  to work;
- service order requires inserting or removing plates through a closed frame;
- latch or gasket compression lands over pipette access windows;
- dry observer clearance is protected only by visual impression rather than a
  tested swept body;
- environmental claims move faster than leak, flow, humidity, condensation, or
  biology evidence;
- the docs and generated CAD disagree about which objects are real parts.
