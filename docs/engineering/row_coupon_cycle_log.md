# Row Coupon Cycle Log

## 2026-05-25: RH1-RH9 CAD-Level Closure Pass

This pass flowed through the row-coupon revision hypergraph as a CAD-level
do-review-context cycle. It closes geometry and review coverage for the
interfaces that can be represented in CadQuery today, while keeping print,
leak, flow, humidity, condensation, and wet-biology evidence as explicit next
cycles.

## Closed At CAD Level

```text
RH1 pod/frame mechanical joint
  do: added printed pod/frame keys on the deck pods and matching underside
  pockets in the plate-support frame.
  review: focused CAD tests prove the keys stay outside the observer sweep, the
  support frame remains the plate datum, and pod/frame solids do not overlap.
  finding: the joint is now located and replaceable in CAD, but the printed
  wear behavior of the key/pocket fit still needs assembly cycling.
  next: print lower-stack coupon; assemble/remove ten times; record pod wear,
  rocking, yaw, and replaceability.

RH2 gasket capture and squeeze control
  do: added upper/lower capture grooves, gasket service tabs, and hard-stop
  preserving groove geometry.
  review: focused CAD tests compare grooved and ungrooved part volumes and
  preserve gasket bounds.
  finding: the first shell groove cut removed the bottom datum land; the groove
  now preserves an outer printed land so the shell still owns a real seating
  surface.
  next: section-print gasket seats; test TPU/TPE or dummy gasket insertion,
  pull-tab access, compression witness marks, and leak shortcuts around tabs.

RH3 wedge/receiver compression mechanism
  do: kept wedge locks as sacrificial separate printed parts, added printed
  tension posts/caps to the wet-chamber frame, cut side-entry post slots into
  the wedges, rotated receiver rails to retain the wedges along their real
  slide axis, and added explicit bearing flats, low-tail anti-lift lips,
  travel stops, release ears, detent bumps, raised witness stripes, and
  post-root reinforcement.
  review: focused tests keep locks, receivers, and latch posts inside the row
  footprint, off the septum access fields, clear of lid service ports, and
  prove the wedge bearing flats sit under the post caps with the post slot open
  before the bearing land.
  finding: CAD now shows a print-testable assembled latch load path, but not
  real compression force, post-cap wear, sliding friction, or humid release.
  next: print a latch station or compression-stack coupon; measure insertion
  force, hard-stop contact, release access, retained clamp force, and wear
  after cycling.

RH4 lid shell/cover reversible duct seal
  do: added a lid-cover tongue and matching shell groove so the split lid is no
  longer only stacked bodies.
  review: focused tests prove the tongue changes the cover lower bound and the
  shell groove is owned by the shell.
  finding: this is a reversible printed locating/seal feature, not yet a proven
  gas-tight duct seal.
  next: inspect print orientation and trapped-support risk; run passive smoke
  or fog through the shell/cover duct path.

RH5 wet-chamber boundary and routing
  do: added internal condensation pockets to the wet-chamber frame while keeping
  the full-footprint row boundary and side service lanes.
  review: geometry still represents one row chamber and keeps side routing
  inside the footprint.
  finding: condensation logic is now represented as geometry, but wet behavior
  is unproven.
  next: warm humid exposure with shallow water; inspect pocket wetting, pooling,
  wipe access, and leak paths.

RH6 observer front-end swept-body check
  do: added a parameterized front-end swept-body check covering every well
  center through the dry bay.
  review: focused tests show the front-end swept body exactly fits the modeled
  dry bay and does not overlap the deck feet.
  finding: a small 21.0 x 13.0 mm front-end can cover all wells; the larger
  100.0 x 58.0 mm carriage cannot be interpreted as an objective-centered body
  across the whole row. The carriage must be offset, folded, or decoupled from
  the front-end head.
  next: design the observer kinematic split between compact front-end head,
  focus axis, carriage body, service loop, and raceway.

RH7 service and exploded states
  do: added installed, exploded, lid-off, mats-exposed, wet-frame-off, and
  plates-removable service modes to the CadQuery viewer path.
  review: focused tests confirm service modes preserve part identity and move
  the expected service groups.
  finding: service actions are now reviewable in CAD; they still need human CAD
  inspection and screenshots before print release.
  next: capture installed and service-state screenshots; review plate removal,
  mat replacement, latch access, and no trapped-service moves.

RH8 passive flow and environmental proxy setup
  do: added removable flow-test adapter geometry for the vertical service ports.
  review: focused tests prove adapters are explicit review geometry and not
  default production parts.
  finding: adapters let the next coupon accept smoke/fog or humidity tracer
  tests without altering the production assembly tree.
  next: define smoke/fog, shallow-water disturbance, humidity response, and
  condensation proxy protocols.

RH9 print/package review
  do: expanded print-native parameters for pod keys, gasket capture, lid tongue,
  wedge receivers, condensation pockets, flow adapters, and service views.
  review: full CAD lint and focused tests pass at the source level.
  finding: the CAD now has print-native interface vocabulary, but slicer and
  material review still need a dedicated pass.
  next: review print orientation, support risk, tolerances, sacrificial wedge
  replacement, gasket material, and which parts may be printed together.
```

## Viewer Smoke Bounds

```text
installed deck_pods: 128.00 x 357.50 x 84.10 mm
installed plate_support_frame: 147.60 x 377.25 x 11.20 mm
installed lower_gasket: 147.60 x 377.25 x 0.80 mm
installed wet_chamber_frame: 147.60 x 377.25 x 32.10 mm
installed cots_microplates: 127.60 x 357.25 x 14.30 mm
installed cots_septum_mats: 127.60 x 357.25 x 4.50 mm
installed upper_gasket: 147.60 x 377.25 x 0.80 mm
installed lid_manifold_shell: 147.60 x 377.25 x 8.00 mm
installed lid_cover: 147.60 x 377.25 x 8.00 mm
installed printed_wedge_locks: 147.60 x 377.25 x 3.00 mm

observer_front_end_swept_body_check: 120.00 x 347.50 x 40.00 mm
flow_test_adapters: 134.60 x 320.25 x 5.00 mm
consumable_metrology_gauge: 143.60 x 101.75 x 3.00 mm
pipette_puncture_swept_path_check: 101.50 x 337.00 x 23.30 mm
```

## Next Physical Review Cycle

```text
RP1 lower-stack print cycle
  inputs: RH1, RH2
  evidence: fit, pod wear, frame rocking/yaw, lower gasket insertion, service
  tabs, plate support flatness, dry-bay clearance.

RP2 compression-stack print cycle
  inputs: RH2, RH3, RH4
  evidence: wedge travel, hard-stop contact, compression repeatability, upper
  gasket witness marks, shell/cover duct continuity.

RP3 service-state review
  inputs: RH7
  evidence: screenshots and human CAD review of installed, exploded, lid-off,
  mats-exposed, wet-frame-off, and plates-removable states.

RP4 passive flow and humidity proxy cycle
  inputs: RH5, RH8
  evidence: smoke/fog path, shallow-water disturbance, humidity response,
  condensation pocket behavior, leak inspection.

RP5 observer kinematic split
  inputs: RH6
  evidence: compact front-end head dimensions, focus stroke, carriage offset,
  cable/fiber bend radius, and raceway recovery envelope.
```

## Missing-Gap Audit

The CAD-level RH1-RH9 pass exposed several domains that were not sufficiently
represented in the first hypergraph. These are now added as RH10-RH17 in
`docs/engineering/row_coupon_revision_hypergraph.md`.

```text
RH10 COTS consumable metrology
  missing: real plate rim/skirt/underside/glass-window geometry and real
  Cole-Parmer mat plug, slit, seated-height, and wet-swelling dimensions.
  why it matters: placeholder consumable geometry can make support, puncture,
  sealing, and service removal look easier than they are.
  next cycle: measure plates and mats; update params only where measured
  differences change mechanical claims.

RH11 liquid-handler puncture mechanics
  missing: pipette tip/cone swept path, puncture force, tip deflection, plate
  deflection, septum reseal after repeated puncture, and aspiration/dispense
  behavior through a mat.
  why it matters: all-96 access is not just an open window; it is a force and
  wear problem that can move the plate, tear septa, or bias liquid handling.
  next cycle: add tip/cone geometry and puncture-force test plan.

RH12 thermal, evaporation, and condensation authority
  missing: heat source location, temperature sensing, lid/rim warming,
  evaporation edge-effect evidence, and condensation control.
  why it matters: a contained wet chamber without thermal/RH authority can still
  fail biology through evaporation, cold lids, local condensation, or slow
  recovery after access.
  next cycle: define thermal placeholders and proxy measurements before any
  incubation claim.

RH13 pressure relief, leak hierarchy, and spill isolation
  missing: pressure relief path, leak-rate test path, drain/spill hierarchy,
  and explicit wet/dry failure boundary.
  why it matters: septum puncture and gas flow can create pressure pulses, while
  leaks or condensate must not silently enter the observer bay.
  next cycle: add relief/drain/test-port features or explicit blocked claims.

RH14 BSL1 material, cleaning, and biological compatibility
  missing: humid-atmosphere exposed material list, cleaning/decontamination
  path, leachables/odor assumptions, and contamination controls.
  why it matters: print-native does not automatically mean cell-compatible,
  cleanable, or stable in warm humid CO2.
  next cycle: write a print-native material/cleaning matrix for the coupon.

RH15 optical quality and observer stability
  missing: stray light, reflections, baffles, vibration, focus targets, thermal
  drift, fiducial strategy, and signal-quality claims for imaging/Raman.
  why it matters: geometric clearance is not usable optical performance.
  next cycle: turn the observer front-end envelope into an optical stability
  and calibration requirement.

RH16 row tiling and service interfaces
  missing: adjacent-row keepouts, tube/cable bend radii, connector access,
  external conditioning module handoff, and populated-deck service clearance.
  why it matters: a one-row module can still fail the product if services block
  neighboring rows, pipette motion, or observer travel.
  next cycle: add row-to-row and service-bus checks.

RH17 assembly state, QC, and fail-closed operation
  missing: visible latch-state, gasket-compression, mat-present, plate-present,
  orientation, and post-service inspection signals.
  why it matters: the robot should not depend on a hidden human assembly state.
  next cycle: add QC gauges and witness features that can be checked by eye,
  camera, or caliper.
```

## RH10/RH11 CAD Tooling Pass

RH10 COTS consumable metrology
  do: aligned the one-row coupon plate body to the persisted CellVis
  P96-1.5H-N published footprint, preserved the 90.50 mm OT-2 column pitch by
  reducing the Y inter-tile gap, and added a printable consumable metrology
  gauge with a plate pocket plus 96 round-plug pockets.
  review: focused CAD tests now protect the new plate footprint, the separate
  validation-tool export, and the fact that the gauge remains outside the
  production assembly tree.
  still blocked: Cole-Parmer mat sheet thickness, plug diameter/depth, slit
  behavior, seated height, and wet swelling remain placeholder dimensions until
  caliper/microscope/humid-exposure records exist.
  next: print the validation gauge, seat the real mat, and record the measured
  mat dimensions before changing mat parameters.

RH11 liquid-handler puncture mechanics
  do: added printed lateral locator rails around each plate pocket and an
  all-96 pipette puncture swept-path check that passes through the open septum
  field instead of a lid or per-well chimney.
  review: focused CAD tests check every swept path target, the plate-locator
  rails, observer/deck-foot separation after the CellVis footprint change, and
  default production parts versus validation-only geometry.
  still blocked: puncture force, tip deflection, plate shift, mat reseal,
  repeated puncture wear, and dispense/aspirate bias through the mat are still
  unproven physical behaviors.
  next: run `docs/protocols/row_coupon_consumable_puncture_validation.md` with
  water/dye before any BSL1 biology.

Lid latch and port interpretation
  finding: the red lid-top tabs are printed wedge locks, while the round
  lid-top bosses are gas/sample/sensor service ports. Both classes are real
  production needs in some form, but not at the same XY station.
  do: made wedge-lock placement port-aware so a lock and its receiver envelope
  are omitted when they would overlap a lid port boss/service adapter keepout.
  still blocked: final production latch shape, port count, port locations, and
  service adapter envelope remain open until flow, leak, and service-routing
  evidence exists.

Latch mechanism demonstrator
  do: added an optional printable latch section showing lower catch,
  compressed-gasket proxy, upper receiver, sliding wedge, hard stop, handle,
  and witness mark as separate solids.
  review: this demonstrates the intended non-print-in-place mechanism. The
  installed row module now carries the integrated print-test version through
  wet-frame tension posts, post caps, lid receiver rails, capture lips, travel
  stops, release tabs, detents, witness stripes, and removable side wedges.
  next: print the latch section and the integrated compression stack; compare
  insertion force, retained clamp force, wear, release, and humid exposure
  behavior.

## 2026-05-26: M0-M3 Latch Mechanical Screening Pass

M0 mechanical assumptions register
  do: added first-print latch assumptions to `cad/one_row_coupon.params.json`:
  provisional PETG or engineering resin, 0.15 mm layer height, 0.45 mm latch
  tolerance allowance, 0.20/0.55/0.80 mm gasket squeeze min/target/max, mu=0.35
  minimum friction, 2.0..25.0 N insertion-force range, 1.0..15.0 N
  release-force range, 8.0 N expected clamp force per latch, 12 MPa
  provisional wet-polymer allowable, and minimum stress/bearing/span gates.
  review: the assumptions are named and test-addressable, but they are still
  placeholders until actual print material, orientation, humidity exposure, and
  force data exist.
  next: M4 print spec cards must freeze material, process, orientation, support
  policy, and critical surfaces before cutting parts.

M1 compression budget
  do: added `latch_compression_budget` to `row_coupon_layout` using production
  wedge geometry: 2.20 mm ramp rise, 6.40 mm ramp run, 0.45 mm tolerance
  allowance, and 0.55 mm bounded target squeeze against a 0.80 mm hard-stop
  limit.
  review: focused tests prove the calculation uses `production_assembly`, not
  `latch_mechanism_demo`, and remains inside the gasket squeeze limit.
  next: measure retained compression or gap-gauge witness values on a printed
  station and on an integrated compression stack.

M2 ramp backdrive / self-lock check
  do: added `latch_ramp_self_lock` with ramp angle, friction angle, margin,
  minimum-margin result, and backdrive risk flag.
  review: the current ramp is 18.97 deg against 19.29 deg at mu=0.35. It is
  barely self-locking by the simple friction check, but misses the 1.0 deg
  minimum margin, so detent retention and wet backdrive remain open.
  next: verify insertion/release force and backdrive after humidity exposure;
  redesign ramp angle, detent, or stop if the print walks back under gasket
  rebound.

M3 post/cap/root screening
  do: added `latch_post_stress_screen` for the production printed post, cap
  bearing flat, and root gusset pad.
  review: the nominal screen passes at 8.0 N per latch with 4.524 mm2 post area,
  1.768 MPa shaft stress, 6.786x provisional safety factor, 19.2 mm2 cap
  bearing area, and 30.0 mm2 root pad area.
  next: inspect real post deflection, cap underside wear, receiver lip wear,
  debris, and creep over 0/10/20 assembly cycles.

M7 station asymmetry surfaced during M0-M3
  do: added `latch_station_asymmetry` so the omitted right-side port station is
  not hidden by a clean-looking latch set.
  review: the current row has 10 expected compression stations, 9 active wedge
  stations, one omitted port-side station, and a 181.0 mm max active-station
  span against the 100.0 mm warning threshold.
  next: either move the port, restore an alternate latch, or accept a measured
  asymmetric-compression plan during integrated stack testing.

## 2026-05-31: PF3/PF7 Service-Port Production-Fidelity Slice

PF3 ports/adapters/tubing/sensor interfaces
  do: replaced anonymous lid-port layout entries with role-typed production
  interfaces: `supply`, `return`, `sample_relief`, `sensor_tile_2`, and
  `sensor_tile_3`. Added printed seal lands, role marker counts, cap plug
  diameters, cap flange diameters, and a separate default production part
  `printed_port_caps`.
  review: focused tests protect the role order, cap dimensions, production
  tree/export names, default production membership, and service-view movement.
  finding: the default CAD no longer treats open cylindrical bosses as finished
  service interfaces. Final tubing, filters, sensors, pressure taps, and COTS
  fittings are still open PF3/PF9 exceptions until exact envelopes and printed
  captures exist.
  next: add printed adapters or selected COTS fitting envelopes, pressure/test
  port states, cap/adapter missing states, and no-side-protrusion checks.

PF7 assembly witnesses and fail-closed form
  do: made capped/plugged service-port state visible in the default production
  assembly through separate printed caps with grip tabs and role-marker
  metadata.
  review: the cap part lifts with the lid service views and remains outside
  validation-only exports.
  finding: port installed/capped state is now represented as form, but plate,
  mat, gasket, lid-orientation, adapter-missing, and negative-state scenes
  remain open.
  next: add negative-state viewer modes and visible witnesses for plate,
  mat, gasket, latch, lid orientation, and port/adapter states.

PF4 wet/dry boundary and failure-path geometry
  do: added printed raised thresholds around every dry-bay optical aperture in
  the plate-support frame, plus shallow wet/dry witness gutters outside those
  thresholds. Added a hidden validation body for the gutter path.
  review: focused tests protect threshold/aperture registration, gutter
  placement outside the aperture cutouts, support-frame geometry change, and
  validation-only membership.
  finding: dry-bay protection is no longer only an observer keepout envelope;
  the CAD now carries physical leak-diversion/witness geometry adjacent to each
  aperture. This does not yet close drain/catch volume sizing, optical shielding,
  humidity condensate routing, or observer electronics isolation.
  next: add drain/catch features, optical shield geometry, spill-capacity
  sizing, and explicit negative-state checks for leak paths into the observer
  bay.

## 2026-05-31: RG1/RG2 Port Negative-State Framework

RG1 negative/service-state viewer framework
  do: added opt-in service view modes `port_caps_missing`,
  `wrong_port_caps`, and `adapter_missing`. Each state removes the default
  `printed_port_caps` part and adds review-only geometry: missing-cap witness
  rings, lifted/mismatched wrong caps, or taller adapter-missing witness rings.
  review: focused tests prove the default installed part tree is unchanged,
  each negative state has a visible geometry delta, review bodies do not enter
  validation parts, and production exports remain free of missing/witness/review
  bodies.
  finding: port bad states can now be inspected in CAD without pretending those
  bodies are production parts. This gives RG3/RG4/RG5 a reusable pattern for
  leak, flow-insert, and observer service states.
  next: extend this framework to plate/mat/gasket/lid/latch negative states and
  to wet/dry leak-to-observer review scenes.

RG2 port-state carry-through
  do: modeled an `adapter_missing` review state using expected adapter envelope
  rings rather than adding a fake adapter to production CAD.
  review: the state is opt-in through the viewer and service-parts API and is
  excluded from fabrication exports.
  finding: exact tubing, filter, sensor, pressure/test, and COTS fitting
  envelopes remain open. The review state only proves the service-state
  framework and expected adapter occupancy.
  next: choose real adapter/fitting envelopes and add printed capture/seal and
  strain-relief geometry.

## 2026-05-31: RS1-RS3 Sensor Mount Realization Pass

RS1 supply/return gas-state PCB mounts
  do: added two vertical screwless side-cartridge sockets to the raised
  supply/return duct volumes, with printed shelves, rails, anti-lift lips,
  gas-channel apertures, cable-exit cuts, and installed PCB envelopes.
  review: focused CAD tests prove the sockets are vertical, screwless, aligned
  to gas-channel apertures, outside septum access fields, and exported as
  separate installed sensor PCB parts.
  finding: the row coupon now embodies the STC31 + colocated SHT41 gas-state
  role mechanically, but final PCB outline, edge notches/tabs, coating,
  connector strain relief, and harness handoff still need the PCB/harness CAD
  pass.
  next: co-design the PCB edge geometry and printed keeper release feature;
  then check seated PCB insertion/removal, aperture registration, and harness
  bend/strain relief in CAD before fabrication.

RS2 per-plate headspace SHT41 microcarrier mounts
  do: added four screwless lid-shell sockets for 12 x 12 x 4 mm SHT41
  microcarriers, with wet-headspace exposure apertures and an inline covered
  lid-shell sensor bus toward the removable-lid service connector.
  review: focused CAD tests prove the carriers are physical installed parts,
  exposed to the wet headspace, outside the septum/pipette access field,
  outside the observer sweep, and routed away from deck-contact faces.
  finding: plate-local headspace sensing is no longer stranded in the electrical
  topology. Condensate shedding, splash protection, membrane wetting, and
  service-loop routing remain physical and harness-layout review items.
  next: add drip/labyrinth detail if needed after humidity exposure review;
  freeze the microcarrier outline and keeper release geometry with the wiring
  harness pass.

RS3 plate-margin IR thermopile mounts
  do: added four underside plate-support-frame pockets for MLX90614-style
  TO-39 thermopiles, each with a dedicated plate-margin aperture, screwless
  retention lips, lower dry harness branch, and installed sensor envelope.
  review: focused CAD tests prove each IR aperture is distinct from the central
  observer aperture, outside the modeled well-grid rectangle, outside the
  observer front-end swept body, and inside the plate footprint.
  finding: the sample-plane proxy temperature role now exists as physical CAD
  without touching the consumable plate. Edge-to-center temperature offset,
  emissivity behavior through the real plate, and sensor calibration remain
  commissioning evidence, not CAD proof.
  next: define the dummy-plate/thermal-camera or thermocouple-grid protocol for
  edge-to-center offset, and keep the IR apertures out of the observer optical
  path in every future support-frame revision.

RS4 sensor harness route realization
  do: replaced single cable-exit stubs with two service-domain harnesses:
  a lower dry IR bus in the plate-support underside and a removable-lid sensor
  bus split between gas-PCB lid-cover routes and SHT41 lid-shell routes. Added
  installed wire-envelope parts, printed snap-cover parts, strain-relief
  rectangles, and keyed service connector envelopes later replaced by RS5
  connector geometry.
  review: focused CAD tests prove lower IR branches stay outside dry apertures,
  observer swept volume, and deck feet; lid buses stay outside septum/pipette
  access fields; gas branches satisfy the minimum bend-length screen; and all
  harness bodies/covers/connectors remain inside the row footprint.
  finding: the CAD now proves buildable first routing topology rather than only
  "wire exits here." It still does not prove actual connector family, pinout,
  crimp/solder termination, splash/condensation protection, or service-loop
  durability.
  next: replace connector envelopes with production-shaped connector geometry,
  add exact bend-radius arcs if the selected cable requires them, and add
  negative-state review scenes for loose, uncaptured, or crossed harness
  routing.

RS5 connector envelope replacement
  do: replaced the single gray service-connector cube with production-shaped
  JST GH 1.25 mm 4-circuit connector assemblies: small service PCB rectangle,
  header body, mating plug body, latch tab, pin-1 marker, printed keyed shroud,
  and opt-in service-clearance check. Split the lower dry connector from the
  removable-lid connectors so service views keep the production assembly tree
  honest.
  review: focused CAD tests prove the connector family is named in layout
  metadata, each connector is keyed and oriented for +Y mating, service
  clearance exists, lid connectors belong to the lid stack, and printed shrouds
  stay inside the row footprint.
  finding: the gray cube is gone; the model now communicates connector family,
  latch side, shroud, and clearance. It still does not freeze the crimp part
  number, cable assembly vendor, pin assignment, potting/conformal strategy, or
  service-cycle durability.
  next: choose exact GH housing/contact/header orderable part numbers, pin the
  lower/lid connector pinouts, and add negative review scenes for unmated,
  reversed, and unlatched connector states.

RS6 gas-PCB wet-boundary correction
  do: changed the gas sensor PCB sockets from partial exposed rails into
  full-height printed dry-side cassettes and added layout metadata that marks
  the PCB pocket as dry-side gas-duct aperture-only, with no wet-headspace
  intrusion. The default CQ-Editor installed view now hides the bare PCB
  envelopes so the model reads as closed cassette hardware; internal PCB
  envelopes are opt-in for electronics service review.
  review: focused CAD tests now prove each gas PCB starts above the modeled
  wet headspace, its sensing aperture lives in the lid-cover gas duct Z band,
  and the PCB pocket is not represented as a biology-facing headspace object.
  finding: the vertical PCB envelope is still a real installed electronics
  cartridge, but the production intent is no longer a bare board visually
  emerging from the chamber. The only intentional gas communication is the
  small registered aperture at the supply/return duct.
  next: co-design the actual PCB edge/cassette detail, aperture gasket or
  labyrinth, removable keeper, and conformal/splash strategy so the CAD proves
  insertion, service, and environmental isolation rather than only envelope
  placement.

RS7 production-prototype sensor installation workflow
  do: added a sensor-install CAD service mode, printed gas-PCB keeper-door
  parts, sensor installation path checks, and layout metadata for ten
  production-prototype sensor service steps: two gas PCB cartridges, four
  headspace SHT41 microcarriers, and four lower IR thermopiles.
  review: focused CAD tests prove the service vectors and path checks exist,
  gas cartridges pull +Z after releasing printed keepers, SHT41 carriers pull
  +X from the lid service side, IR thermopiles pull -Z from the lower dry side,
  and every retained sensor follows the no-screws/no-glue policy.
  finding: the prototype now has a modeled install/test story instead of only
  installed sensor envelopes. The sequence is bench electrical, pocket
  fit/retention, aperture registration, installed dry electrical,
  environmental step response, wet non-biological exposure, then BSL1 biology
  commissioning.
  next: turn the test gates into executable bench fixtures and fixture-QC
  records: exact pin maps, sensor IDs, bus scan acceptance, force limits,
  aperture witness photos, wet-exposure drift thresholds, and service-cycle
  durability counts.

RS8 gas-PCB sealed duct sampling interface
  do: replaced the abstract "PCB near aperture" claim with explicit gas-PCB
  interface geometry: compressible gasket patches, printed seal lands,
  compression pads, shallow low-dead-volume flow cells, and a validation flow
  cell check part. The default installed view now includes the gasket/interface
  hardware while still hiding bare PCB envelopes.
  review: focused CAD tests prove both gas PCB interfaces are sealed dry-side
  duct sampling cells, the flow-cell volume stays low, gasket compression is
  positive and below nominal gasket thickness, the flow cell stays inside the
  lid-cover duct height band, and the gasket/land geometry is not an open-top
  sampling assumption.
  finding: this is now closer to what the production prototype must print and
  assemble: the gas sensors read duct gas through a controlled window, not room
  air above the lid. Remaining proof is empirical: leak rate, response time,
  condensation resistance, gasket material aging, and repeated cartridge
  insertion wear.
  next: create the bench validation record for gas-step response and leak
  testing, then tune flow-cell depth/volume against measured STC31 response and
  condensation behavior.

RS9 production operating side gas services
  do: moved production supply/return operation away from generic top gas ports.
  The lid cover now carries integrated side gas service features: printed
  manifold blocks, side duct openings, short tube stems, low-profile flanges,
  printed strain-relief yokes, and validation-only tube bend envelopes. The
  production top surface now retains only the explicit sample/relief service
  port with `printed_sample_relief_cap`; top supply/return/sensor bosses are no
  longer modeled as production operating interfaces.
  review: focused CAD tests prove the installed production tree uses
  `printed_sample_relief_cap`, side services have supply/return roles, tube
  envelopes are validation-only, side service blocks and tube envelopes avoid
  all septum access windows, and gas PCB apertures align to the side service
  duct references rather than top ports. `uv run pytest
  tests/test_row_coupon_cad.py -q` passed 44 tests after this change.
  finding: the default installed CAD state is now closer to normal OT-2
  operation: side services connected, top pipette field not cluttered by gas
  caps, gas sensors sampling controlled duct streams, and bench/review geometry
  kept opt-in. The side fitting protrusion is now explicit in `lid_cover`
  bounds; future cycles need an OT-2 adjacent-slot/service-tube routing check
  against the real deck and neighboring modules.
  next: prove side tube routing on the physical OT-2 deck, add leak/witness
  routing for side fittings, and decide whether the sample/relief cap should
  become a normally closed printed valve or remain a removable cap.

RS10 side gas leak/witness routing
  do: added leak-management geometry to each side gas service block. Each
  supply/return side service now has two shallow outboard witness gutters and
  one printed inboard dam on the lid cover, plus a validation-only
  `side_gas_leak_witness_check` overlay. The gutters are cut into the printed
  gas-service block and the dams are raised print features, so the failure path
  is visible in the production geometry instead of only described in prose.
  review: focused CAD tests prove the leak witness overlay is validation-only,
  each side service has two gutters and one dam, gutter depth and dam height
  follow `gas_service` params, supply drains toward -X and return drains toward
  +X, and gutter rectangles do not overlap the dry-bay footprint.
  finding: side gas services now have a modeled leak hierarchy: side duct and
  tube failures are biased to a visible external edge before they can silently
  route inward. This is still CAD-level geometry, not leak-rate evidence; the
  next physical cycle must verify capillary behavior, print roughness, cleaning,
  and humid condensate behavior.
  next: add measured OT-2 adjacent-slot/tube routing checks and create a bench
  side-service leak/condensate witness protocol.

RS11 adjacent-slot side-service overhead clearance
  do: added adjacent OT-2 slot keepout metadata, validation CAD, and clearance
  summary logic for side gas external service envelopes. The model now exports
  `adjacent_deck_slot_keepout_check` and records the vertical clearance between
  each side-service fitting/tube envelope and the modeled neighboring slot
  overhead keepout.
  review: focused tests prove the adjacent-slot keepout is validation-only,
  eight neighboring slot volumes are represented for the four-plate column,
  side service external envelopes overlap neighboring slot XY only in a
  reserved overhead corridor, and the minimum vertical clearance is 4.10 mm
  over the 110.00 mm adjacent-slot keepout, exceeding the 2.00 mm requirement.
  finding: this does not prove arbitrary neighboring modules can coexist with
  the coupon. It makes the assumption explicit: side gas tubing consumes
  reserved adjacent-slot overhead and must be checked against the real OT-2
  deck plus any neighboring hardware intended for the same run.
  next: measure the physical OT-2 deck/neighbor module envelope and decide
  whether production tubing must reroute to a row end or remain as reserved
  adjacent-slot overhead.

RS12 sample/relief cap leak-witness routing
  do: added production `lid_cover` leak-management geometry for the only
  remaining top service port. The sample/relief boss now has a printed
  outboard witness shelf, shallow gutter to the visible right row edge, and
  small inboard dam below the cap flange, plus a validation-only
  `sample_relief_leak_witness_check` overlay.
  review: focused CAD tests prove the overlay is validation-only, the witness
  route drains to the visible +X edge, the shelf/gutter remain outboard of the
  dry-bay footprint, the shelf/gutter/dam avoid all septum access windows, and
  the dam/shelf stay below the cap flange so the installed
  `printed_sample_relief_cap` can still seat.
  finding: the sample/relief cap is no longer just a capped top feature. It has
  a modeled failure hierarchy consistent with normal production operation:
  cap leakage or condensate is biased outward and made visible. This still does
  not prove leak rate, liquid wetting behavior, capillary behavior, or repeated
  cap service wear.
  next: add empirical cap leak/condensate witness protocol and extend the
  same failure-path review to upper/lower gasket service tabs.

RS13 gasket service-tab root leak/witness routing
  do: added lower/upper front/rear gasket-tab witness geometry. The
  plate-support frame now has shallow lower tab-root witness gutters and low
  inboard dams; the lid shell now has underside upper tab-root gutters and
  downward inboard dams. A validation-only `gasket_tab_leak_witness_check`
  overlay makes these small features inspectable.
  review: focused CAD tests prove the overlay is validation-only, all four
  lower/upper front/rear tab-root sites are present, gutters and dams are owned
  by the intended printed parts, the features remain outside the dry-bay
  envelope, and they avoid every septum access window.
  finding: the service tabs now have a modeled failure margin instead of being
  unqualified pull flaps. The model still does not prove leak rate, tab-root
  wetting, material wicking, or whether the inboard tab strategy remains the
  best production service approach.
  next: print a gasket/tab section coupon and test dummy gasket removal,
  witness wetting, compression marks, and whether service tabs should be
  redesigned as edge-exposed tabs rather than inboard chamber-margin tabs.

RS14 electrical service cable egress envelope
  do: added validation-only external cable bend envelopes to all three JST-GH
  service connector assemblies. The installed model keeps the shaped connector,
  mated plug, latch, keyed shroud, pin-1 marker, snap covers, and strain-relief
  channels as production geometry; the new `sensor_service_cable_envelope_check`
  shows the nonprinted +Y electrical cable handoff volume.
  review: focused CAD tests prove the cable envelope check is validation-only,
  every service connector has one external cable envelope, each envelope starts
  at the connector service side, includes bend-radius plus straight-service
  length, exits beyond the row footprint, and avoids dry-bay and septum access
  windows.
  finding: electrical service connectivity is now represented with the same
  discipline as gas tubing: the connector is a real installed part and the
  cable route is an explicit operating envelope. This still does not prove
  cable supplier, pinout, actual bend fatigue, strain-relief durability, or
  OT-2 deck-cable dress with neighboring modules.
  next: measure the physical OT-2 rear/side cable handoff clearance, choose
  real cable assemblies, and add unmated/reversed/unlatched electrical review
  scenes if they remain useful.

RS15 OT-2 pipette/toolhead operating swept body
  do: added a validation-only `pipette_toolhead_swept_body_check` beside the
  existing all-well tip puncture swept-path check. The new envelope spans all
  384 septum targets plus modeled lower-toolhead overtravel and starts above
  the assembled coupon and connected side gas/electrical service envelopes.
  The current computed envelope is 250.00 x 445.50 x 45.00 mm, bottoming at
  z=66.10 mm. It records 8.00 mm clearance above the assembled stack,
  27.90 mm above the highest modeled operating service envelope, and 2.00 mm
  above the tip puncture swept path.
  review: focused CAD tests prove the toolhead envelope is validation-only,
  covers every well center, clears side gas tube/fitting and electrical cable
  service envelopes in Z, remains separate from the production installed part
  tree, and is exported as its own validation STL/STEP artifact.
  finding: the CAD no longer treats pipette access as only a thin tip cylinder.
  It now distinguishes the puncturing tip path from the larger lower-toolhead
  operating body while side services are connected. The envelope is still a
  conservative model requiring measured OT-2 geometry, real cable/tube dress,
  and live-motion dry-run evidence before authorizing operation.
  next: measure the actual OT-2 pipette lower-body and gantry clearances,
  dress real gas/electrical services on the deck, and update the envelope from
  conservative params to measured hardware data.

RS16 connected COTS gas/electrical service leads in installed state
  do: promoted service connectivity from envelope-only representation to
  explicit installed COTS service bodies. The default production tree now
  includes `cots_gas_service_tubes`, `lower_sensor_service_cable_pigtail`, and
  `lid_sensor_service_cable_pigtails`. The gas and cable bend envelopes remain
  validation-only clearance checks around those physical service bodies.
  review: focused CAD tests prove the installed gas tubes are production-tree
  COTS parts, one per side supply/return service, sit inside the existing tube
  bend envelopes, and are not validation parts. The sensor harness tests now
  prove all three service connectors have installed +Y cable pigtails inside
  their larger validation envelopes. The export tree now writes separate
  STL/STEP artifacts for lower cable pigtail, lid cable pigtails, and COTS gas
  service tubes.
  finding: the default `installed` view now better matches normal OT-2
  operation: the coupon is not merely fitted with empty barbs and connector
  plugs; it visibly carries connected gas tubing and electrical service
  pigtails. This increases the service-connected operating envelope to
  219.60 x 405.25 x 140.60 mm. Real cable/tube dress, supplier part numbers,
  bend fatigue, strain-relief cycling, and neighboring-module coexistence still
  need physical proof.
  next: choose actual tube and cable assemblies, measure dressed routing on
  the OT-2 deck, and replace the straight pigtail approximations with measured
  service routing if the physical dress differs.

RS17 latch unseated review mode
  do: added an opt-in `latches_unseated` service/review mode. The default
  installed state still carries `printed_wedge_locks`; the review mode removes
  those production wedges and adds `unseated_wedge_locks_review` plus
  `latch_unseated_witnesses`. The pulled-back review wedges reuse the exact
  production wedge body geometry and translate outward along each latch's real
  insertion axis. The witnesses mark the seated bearing-flat stations.
  review: focused tests prove the unseated latch scene is available through
  `ROW_COUPON_SERVICE_MODES`, is opt-in only, does not enter production parts,
  does not enter validation parts, shows one pulled-back wedge and one witness
  per active latch station, and expands beyond the installed wedge bounds by
  the configured review offset.
  finding: latch state is no longer only implied by red tabs in the installed
  model. The CAD now has a negative assembly-state scene that can be inspected
  in CQ-Editor without changing the production export tree. This still does
  not prove latch insertion force, retained compression, wet release, creep, or
  backdrive behavior.
  next: add similar negative-state scenes for missing plates/mats/gaskets or
  lid orientation if assembly-state inspection remains weak after visual
  review; physically test wedge insertion/release and retained compression.

RS18 septum mat missing review mode
  do: added an opt-in `septum_mats_missing` service/review mode for the COTS
  round pre-slit silicone mats. The default installed state still includes
  `cots_septum_mats`; the review mode removes that part and adds
  `missing_septum_mat_witnesses`, one per plate tile, at the expected seated
  mat top plane.
  review: focused tests prove the mode is present in `ROW_COUPON_SERVICE_MODES`,
  removes only `cots_septum_mats`, does not add production or validation
  geometry, spans the same X/Y footprint as the installed mat set, and uses the
  configured missing-mat witness height and frame width. Viewer smoke confirms
  the default installed state still carries `cots_septum_mats`, validation mode
  keeps the review witness out of validation geometry, and
  `septum_mats_missing` loads with `missing_septum_mat_witnesses`.
  finding: the CAD now has a review path for a missing consumable septum mat
  without confusing it with normal operation. This helps inspect an assembly
  state that would break containment and pipette puncture behavior even though
  the rest of the lid/lock/service stack appears installed. It still does not
  prove mat swelling, insertion force, puncture endurance, or wet sealing.
  next: add missing/mis-seated plate or gasket review scenes only if the visual
  service review still cannot catch those assembly errors; physically measure
  the Cole-Parmer mat dimensions and puncture/seal behavior.

RS19 missing plate-stack and perimeter-gasket review modes
  do: added opt-in `microplates_missing` and `perimeter_gaskets_missing`
  service/review modes. The default installed state still carries
  `cots_microplates`, `cots_septum_mats`, `lower_gasket`, and `upper_gasket`.
  `microplates_missing` removes the plates and their dependent septum mats,
  then shows per-plate support-datum witness frames. `perimeter_gaskets_missing`
  removes the lower and upper perimeter gaskets, then shows the missing
  compressed gasket volumes as review witnesses.
  review: focused tests prove both modes are present in
  `ROW_COUPON_SERVICE_MODES`, are opt-in only, do not enter production or
  validation geometry, remove only their intended installed parts, and preserve
  footprint/alignment metadata for the missing plate stack and gasket volumes.
  Viewer smoke confirms both modes load from `cad/view_one_row_coupon.py`.
  Full row-coupon CAD tests passed after this cycle.
  finding: the CAD can now inspect three fatal consumable/seal absence states:
  missing plates, missing septum mats, and missing perimeter gaskets. This
  closes a visual audit gap where the lid, frame, services, and latches could
  appear installed while the biology support or wet-chamber seal was absent.
  It still does not prove gasket compression force, gasket material choice,
  plate flatness, humid creep, or real seal behavior.
  next: physically characterize plate/mat/gasket stack height, insertion force,
  wet exposure swelling, puncture endurance, compression set, and leak behavior;
  add mis-seated, not merely missing, review scenes only if visual service
  inspection remains ambiguous.

RS20 dry-bay ingress audit overlay
  do: added validation-only `dry_bay_ingress_audit_check` geometry and layout
  metadata. The overlay combines the protected dry-bay footprint with external
  wet-service collection features and inboard dams from side gas services,
  the sample/relief cap, and gasket service-tab roots.
  review: focused CAD tests prove the audit check is hidden from the installed
  production tree, present in validation geometry, exported as its own
  validation artifact, classifies wet collectors separately from inboard dams,
  and verifies all wet-collection rectangles stay outside the protected dry-bay
  footprint. Viewer smoke confirms the overlay loads in validation view, CAD
  generation emitted the corresponding STEP/STL outputs, and full row-coupon
  CAD tests passed after this cycle.
  finding: dry-bay protection is no longer only a collection of separate
  local checks. The CAD now has one review overlay for external wet-service
  ingress toward the observer bay, while aperture-local wet/dry gutters remain
  covered by `wet_dry_failure_path_check`. This still does not prove wetting,
  capillary behavior, condensate transport, cleaning behavior, or leak rate.
  next: run physical side-service, sample/relief, gasket-tab, and optical
  aperture wetting tests with dye or humidity tracer; update the CAD if real
  liquid bridges any collector/dam boundary.

RS21 assembly-role manifest
  do: added `row_coupon_part_manifest()` as a machine-checkable role manifest
  for installed production parts, validation overlays, service modes, and
  opt-in review states. Installed entries now carry an operating role,
  fabrication source, retention/no-glue statement, and visibility class.
  Validation entries are explicitly validation-only. Review-mode entries
  declare their removed installed parts and added review geometry.
  review: focused CAD tests prove the manifest exactly covers the installed
  production builder, validation builder, and every service/review mode in
  `ROW_COUPON_SERVICE_MODES`. The test also checks that installed entries have
  explicit roles, fabrication sources, no-glue retention semantics, and no
  screw assumption unless marked `no_screws`. Installed viewer smoke, CAD
  generation, and full row-coupon CAD tests passed after this cycle.
  finding: the row coupon now has a code-level guard against mystery geometry:
  any future visible installed part, validation overlay, or review-state part
  must be role-typed or tests fail. This improves production-operating
  traceability without changing physical geometry.
  next: use the manifest as the acceptance gate for future CAD additions; if a
  new COTS or electronics exception appears, add its role and fabrication
  exception explicitly.

RS22 gas PCB cartridge missing review mode
  do: added opt-in `gas_pcbs_missing` service/review mode. The default
  installed state still carries `gas_sensor_pcbs`, `gas_pcb_interface_gaskets`,
  and `printed_gas_pcb_keeper_doors`. The review mode removes the gas PCB bodies
  and their dependent duct-interface gaskets, then adds supply/return cartridge
  footprint witnesses plus duct-seal gasket witnesses while leaving the printed
  keeper doors in operating position.
  review: focused tests prove the mode is present in
  `ROW_COUPON_SERVICE_MODES`, removes only the gas PCB and interface gasket
  parts, keeps the keeper doors installed, does not enter production or
  validation geometry, and locates each witness from the actual gas PCB mount
  and gas-interface metadata. The part manifest now declares the review delta.
  Gas-PCB-missing viewer smoke, CAD generation, full ruff, and full
  row-coupon CAD tests passed after this cycle.
  finding: the CAD can now inspect a production-critical hidden failure where
  the module appears assembled but the gas-state cartridges and sealed duct
  sampling compression are absent. This closes a sensor-operating audit gap
  without changing the normal installed assembly.
  next: add analogous review states for unmated electrical service connectors
  or missing gas/cable service leads only if visual inspection cannot catch
  those failures; physically test gas cartridge insertion, compression, leak,
  and response behavior.

RS23 connected service leads missing review mode
  do: added opt-in `service_leads_missing` service/review mode. The default
  installed state still carries the COTS gas service tubes and all lower/lid
  electrical cable pigtails. The review mode removes only those connected COTS
  service leads while leaving the printed gas fittings, strain relief, keyed
  connectors, connector shrouds, lid cover, and lower frame in operating
  position, then adds gas-tube and electrical-cable handoff witnesses.
  review: focused tests prove the mode is present in
  `ROW_COUPON_SERVICE_MODES`, removes only the gas/electrical service lead
  parts, keeps the printed interface hardware installed, does not enter
  production or validation geometry, and locates every witness from actual
  installed gas tube and service cable metadata. The part manifest declares the
  review delta. Service-leads-missing viewer smoke, CAD generation, full ruff,
  and full row-coupon CAD tests passed after this cycle.
  finding: this closes a production-operating audit gap where the module can
  appear fitted with barbs and connector bodies but still lack the connected
  tube/cable services required for operation.
  next: use physical tube/cable dress measurements to replace the conservative
  service envelopes; add unmated/reversed connector review only if the selected
  connector family and cable assemblies cannot be inspected reliably.

RS24 retire future-adapter missing review state
  do: removed the opt-in `adapter_missing` service/review mode because it
  represented a future adapter absence rather than a current production,
  service, or validation role. Passive `flow_test_adapters` remain available as
  explicit opt-in validation geometry through `--show-flow-adapters`; they are
  not production installed parts and no longer imply a missing production
  adapter state.
  review: focused tests prove `adapter_missing` is absent from
  `ROW_COUPON_SERVICE_MODES`, absent from port review metadata, absent from the
  manifest review-mode set, and absent from viewer/parameter/docs references
  except historical cycle-log context. Flow-adapter viewer smoke, CAD
  generation, full ruff, and full row-coupon CAD tests passed after this
  cycle.
  finding: this removes a forward-reference stub from the CAD service-mode
  vocabulary and keeps top-port semantics narrowed to the actual sample/relief
  cap plus explicit validation adapters.
  next: continue retiring or converting any remaining future-facing review
  states unless they can be tied to a real installed, service, or validation
  role.

RS25 rename legacy plural port-cap review modes
  do: replaced the live `port_caps_missing` and `wrong_port_caps` service modes
  with production-specific `sample_relief_cap_missing` and
  `sample_relief_cap_unseated`. The review geometry now adds
  `missing_sample_relief_cap_witness` or
  `unseated_sample_relief_cap_review`, tied to the one real
  `printed_sample_relief_cap` in the installed assembly.
  review: focused tests prove the new modes are present in
  `ROW_COUPON_SERVICE_MODES`, the retired plural names are rejected, the
  manifest review-mode set matches the service builders, and viewer/docs/params
  no longer advertise the old live names except historical cycle-log context.
  Viewer smoke for both renamed review modes, CAD generation, and full ruff
  and full row-coupon CAD tests passed after this cycle.
  finding: the top-port review vocabulary now matches the production device:
  one sample/relief cap can be missing or unseated. There is no longer an
  implied family of generic port caps in the live CAD API.
  next: keep top-port changes constrained to the sample/relief service role
  unless a new production port earns its own operating and validation evidence.

RS26 remove generic printed port-cap builder
  do: removed the live `build_printed_port_caps` builder and made
  `build_printed_sample_relief_cap` construct the single sample/relief cap
  directly from the one `sample_relief` lid port. The builder now rejects any
  layout that does not have exactly one sample/relief port.
  review: focused tests prove `printed_sample_relief_cap` remains the installed
  sealing part, `printed_port_caps` is not an installed part, the generic
  `build_printed_port_caps` symbol is absent, and the manifest still covers the
  production/review assembly tree. Installed-view smoke, CAD generation, and
  full ruff and full row-coupon CAD tests passed after this cycle.
  finding: the live CAD API no longer exposes a generic top-cap builder after
  the production design has converged to one sample/relief cap plus side gas
  services. This closes the last live plural-port-cap semantic leak.
  next: keep helper APIs aligned to the current production assembly names; only
  introduce generic port/cap builders if a new production port class is
  physically realized and validated.

RS27 retire legacy compound assembly builders
  do: removed the public `build_row_coupon_base` and `build_lid_manifold`
  wrappers. The production lower stack is now exposed and tested as separate
  `deck_pods` plus `plate_support_frame` parts; the production lid stack is
  exposed and tested as separate `lid_manifold_shell` plus `lid_cover` parts.
  review: focused CAD tests prove the retired compound symbols are absent, the
  split lower stack still preserves deck engagement and plate-support bounds,
  the separate lid shell and cover leave the septum/pipette field clear, and
  component bounds are computed from production parts rather than legacy
  unions. Viewer smoke with validation tools and flow adapters loaded the split
  installed scene. CAD generation, `uv run ruff check .`, and
  `uv run pytest tests/test_row_coupon_cad.py -q` passed after this cycle.
  finding: this closes another semantic leak from the old CAD vocabulary. A
  future designer can no longer import a unified `base` or `lid_manifold`
  helper and accidentally treat the coupon as fewer fabricated parts than the
  production assembly tree actually contains.
  next: keep retiring public helpers whose names imply nonexistent production
  parts; preserve validation overlays only when they are explicitly
  validation-only and role-typed by the manifest.

RS28 promote observer clearance to exported validation artifacts
  do: added the dry observer front-end swept body, carriage envelope, and
  service raceway envelope to the role manifest, validation part builder,
  validation export tree, and viewer options as explicit validation overlays.
  The observer-robotics parameter description now treats these as
  production-reserved dry volumes rather than future reference placeholders.
  review: focused tests prove the manifest covers the new observer validation
  overlays, the validation export tree emits STEP/STL names for all three
  observer clearance bodies, the front-end swept body still reaches all well
  centers without hitting deck feet, and validation overlays stay out of the
  default installed production tree. CAD generation emitted the three new
  observer validation STEP/STL artifacts, validation-viewer smoke loaded all
  three overlay bounds, `uv run ruff check .` passed, and the full row-coupon
  CAD suite passed after this cycle.
  finding: dry observer clearance is no longer only an internal layout/helper
  assertion. The generated CAD outputs now carry reviewable bodies for the
  compact optical front-end sweep, larger carriage reserved volume, and service
  raceway, which makes the dry-bay production claim easier to inspect before
  printing or fitting real optics.
  next: replace the observer carriage, front-end, focus, and service-raceway
  dimensions with measured or selected hardware envelopes once the first real
  observer module architecture is chosen.

RS29 align observer validation helper API names
  do: renamed the live observer validation helpers and layout keys to match the
  exported artifacts: `build_observer_front_end_swept_body_check`,
  `build_observer_carriage_envelope_check`,
  `build_observer_service_raceway_envelope_check`, and matching
  `row_coupon_layout()` keys. The former module/envelope helper names and
  layout keys are now regression-rejected.
  review: focused tests prove the old public helper names and old layout keys
  are absent, the new check-named layout keys are present, the manifest and
  validation export tree still use the exported artifact names, the front-end
  swept body still reaches all well centers without hitting deck feet, and the
  validation overlays remain outside the installed production tree. CAD
  generation, validation-viewer smoke, `uv run ruff check .`, and the full
  row-coupon CAD suite passed after this cycle.
  finding: the dry-observer CAD API now speaks the same production-validation
  vocabulary as the generated STEP/STL outputs. There is no longer a live
  `observer_module_swept_body` helper path implying a vague future module
  instead of a compact front-end clearance check.
  next: keep layout keys and builder names aligned to exported production or
  validation artifact names; retire any remaining public helper names that
  describe an obsolete part or hidden reference.

RS30 export remaining validation check geometry
  do: promoted the remaining hidden validation checks into the role manifest,
  validation part builder, validation export tree, and viewer options:
  `deck_slot_footprint_check`, `deck_frame_keepout_check`,
  `dry_bay_envelope_check`, `dry_bay_boundary_check`,
  `headspace_barrier_check`, `headspace_volume_check`, and
  `pipette_puncture_swept_path_check`. The docs now list their STEP/STL export
  paths explicitly.
  review: focused tests prove the manifest and validation builder include the
  promoted checks, the validation export tree emits all new STEP/STL artifacts,
  the checks remain absent from the installed production tree, the pipette
  puncture path still covers every septum target, the headspace volume remains
  one shared row volume, and component bounds remain stable. CAD generation,
  validation-viewer smoke, `uv run ruff check .`, and the full row-coupon CAD
  suite passed after this cycle.
  finding: validation geometry for deck fit, deck-frame keepout, dry observer
  reservation, shared headspace, chamber barrier, and tip puncture access is no
  longer hidden behind tests or prose. It is now reviewable in CQ-Editor and in
  generated CAD outputs just like the gas, sensor, observer, leak, and toolhead
  validation artifacts.
  next: keep every validation-only helper either exported/manifested or remove
  it; do not let test-only geometry accumulate as an implicit design claim.

RS31 protect headspace SHT41 microcarriers as side-loaded cassettes
  do: changed the per-plate SHT41 headspace mounts from simple carrier sockets
  into protected side-loaded lid-shell cassette tunnels. Each mount now carries
  layout metadata and CAD geometry for the service-edge pocket, nonzero datum
  floor, roof/anti-lift keeper, side and back stops, registration key/notch,
  finger relief, and underside drip-break ring around the controlled membrane
  aperture.
  review: focused tests prove the SHT41 carriers remain installed physical
  sensor modules, the wet boundary is `controlled_membrane_aperture_only`, the
  cassette tunnel opens to the service edge for -X installation/+X removal, the
  floor/keeper/stops/key/drip-break features are present, the protected cassette
  and drip-break ring stay outside septum access windows, sensor-install
  workflow metadata remains coherent, the installed assembly tree is unchanged,
  component bounds remain stable, full `uv run ruff check .` passes, installed,
  sensor-install, and validation-tools viewer smokes load with the updated
  lid-shell envelope, and `scripts/generate_row_coupon.py` regenerated the
  production and validation CAD outputs. The full row-coupon CAD suite passed
  after this cycle.
  finding: the SHT41 headspace sensors no longer read as exposed blocks in the
  wet chamber. The production intent is now a removable electronics
  microcarrier in a protected lid-shell tunnel, with only the sensing membrane
  aperture and drip-break geometry exposed to wet headspace.
  next: verify the cassette geometry against real SHT41 microcarrier PCB
  outlines, solder/potting strategy, conformal coating limits, humidity
  response lag, condensation behavior, and repeated install/remove force.

RS32 seal lower IR thermopile apertures at the wet/dry boundary
  do: added a production IR aperture boundary construction. The
  `plate_support_frame` now carries an integral raised drip collar around each
  plate-margin IR aperture, and the installed production tree now includes
  `ir_thermopile_face_gaskets` as separate compressible dry-side face seals
  captured with the TO-39 thermopile bodies. The sensor-install view translates
  the gaskets with the IR thermopiles.
  review: focused tests prove the new gasket is a manifest/exported installed
  part, the IR mount metadata declares a
  `drip_collared_aperture_with_dry_side_face_gasket` wet boundary, the gasket
  inner/outer diameters and compression are valid, the collar remains below the
  plate bottom, the collar and aperture stay outside the central observer
  aperture, and the gasket moves with the IR service state. Installed and
  sensor-install viewer smokes load the new part and updated support-frame
  geometry. Full `uv run ruff check .`, validation-tools viewer smoke, CAD
  generation, and the full row-coupon CAD suite passed after this cycle.
  finding: the IR aperture is no longer only a line-of-sight hole through the
  support frame. The CAD now distinguishes the optical opening from the wet/dry
  sealing interface: printed top collar for splash/drip management and a
  replaceable compressible face gasket at the dry sensor module.
  next: validate gasket material, compression set, IR optical obstruction,
  condensate behavior, and repeated sensor install/remove against real
  thermopile packages and printed pockets.

RS33 remove generic top support-frame datum pockets from the seal land
  do: removed the legacy `fiducials` and `insert_pockets` parameter blocks and
  the matching `_cut_fiducials` / `_cut_insert_pockets` support-frame cuts. The
  engineering doc now states that the installed production support frame has no
  generic top fiducial or insert-pocket cuts in the lower seal land; only the
  underside dry-bay observer fiducials remain.
  review: focused tests prove the legacy parameters/helpers are absent, the
  dry-bay observer fiducials remain, manifest roles do not describe visible CAD
  geometry as placeholders/stubs/abstract features, and the production base
  split still preserves support/deck interfaces. `uv run ruff check .`, the
  installed viewer smoke, CAD generation, and the full row-coupon CAD suite
  passed after this cycle.
  finding: the removed top pockets were not harmless review marks. They lived
  at the support-frame top face where the lower gasket capture/groove occupies
  the perimeter, so leaving them in the installed part would have implied an
  avoidable wet-seal discontinuity and a placeholder production role.
  next: keep service/QA datums either dry-side, underside, validation-only, or
  explicitly outside seal/wet paths; do not add blind top pockets under the wet
  chamber unless they have a tested sealing and cleaning role.

RS34 make side gas tube retention explicitly barbed and no-glue
  do: replaced the side gas fitting's generic equal-diameter flange/stem
  assumption with a print-native tube-retention construction: 3.0 mm tube ID,
  5.0 mm tube OD, 3.1 mm printed stem, and 3.6 mm raised barb-retention bead.
  The side gas service layout now exposes `printed_barb_retention_bead` and
  `tube_retention` metadata, and the installed COTS tube pigtails carry matching
  inner/outer diameter and retention evidence.
  review: focused side-gas tests prove the stem engages the tube ID, the barb
  peak exceeds the stem, the barb remains inside the tube OD, the tube OD stays
  inside the bend envelope, the old smooth `printed_barb_flange` envelope name
  is absent, and side gas services still avoid septum access, dry-bay wet
  routing, and adjacent-slot keepouts. `uv run ruff check .`, installed viewer
  smoke, CAD generation, and the full row-coupon CAD suite passed after this
  cycle.
  finding: the side gas connection no longer depends on a smooth printed nipple
  plus an abstract "fitting capture" claim. The CAD now represents a printable
  barb shoulder and strain-relief yoke as the no-glue tube retention mechanism,
  with pull-off/leak behavior still left to physical testing.
  next: test real tubing ID/OD, printed barb process limits, insertion force,
  pull-off force, leak rate, cleaning residue, and humid-cycle creep; update the
  assumed 3.0/5.0 mm tube and 3.1/3.6 mm printed barb dimensions from measured
  hardware.

RS35 make installed side gas tubes hollow flow bodies
  do: changed `build_cots_gas_service_tubes` from solid cylinder geometry to a
  hollow tube-wall primitive using the modeled tube ID/OD. Installed COTS gas
  tube metadata now declares `geometry: hollow_tube_wall` and
  `flow_bore_diameter` equal to the tube inner diameter.
  review: the focused side-gas test now compares generated tube volume against
  the expected hollow-wall volume and proves it is less than the solid-cylinder
  approximation. Installed and `service_leads_missing` viewer smokes still load
  correctly; the latter removes the COTS tubes while leaving printed fittings
  and missing-lead witnesses. `uv run ruff check .`, CAD generation, and the
  full row-coupon CAD suite passed after this cycle.
  finding: the connected gas service no longer presents its COTS tubing as a
  solid decorative cylinder. The installed operating CAD now has a physical bore
  consistent with the supply/return gas-flow claim and the barbed tube-retention
  interface from RS34.
  next: verify real tube bore, wall compliance, printed barb occlusion risk,
  internal cleaning/drain behavior, pressure drop, leak rate, and flow-step
  response after printing and assembly.

RS36 give the sample/relief cap a matched lip-and-seat seal
  do: added cap-seal lip parameters and layout metadata for inner/outer
  diameter, height, receiving-seat depth, nominal compression, and role. The
  `printed_sample_relief_cap` now carries an integrated annular compliant lip
  below its flange, and the `lid_cover` sample/relief boss cuts a matching
  annular seat so the installed service closure is more than a friction plug.
  review: focused tests prove the lip is sized from the port hole, plug
  clearance, boss diameter, and configured width; the receiving-seat depth plus
  nominal compression equals the lip height; the cap body gains lip volume; the
  lid cover loses the matching seat volume; and the unseated review scene lifts
  the same production cap geometry. `uv run ruff check .`, installed,
  `sample_relief_cap_missing`, and `sample_relief_cap_unseated` viewer smokes,
  CAD generation, and the full row-coupon CAD suite passed after this cycle.
  finding: the only remaining top service closure now has explicit seal
  mechanics in the CAD: compliant cap lip, lid-side seat, nominal compression,
  outboard witness shelf/gutter, and inboard dam. It still needs physical leak,
  insertion-force, compression-set, cleaning, and repeat-service evidence.
  next: print and test candidate cap/lid materials and clearances; measure
  cap insertion/removal force, wet leak rate, humidity/condensate behavior,
  lip compression set, and whether the service closure should become a normally
  closed relief/sample valve instead of a removable cap.

RS37 align the part manifest with the sample/relief lip-and-seat seal
  do: updated the `printed_sample_relief_cap` manifest retention policy from
  the obsolete `printed_friction_plug_no_glue` description to
  `printed_annular_lip_in_lid_seat_no_screws_no_glue`, and added a focused
  regression test tying that manifest entry to the cap seal metadata.
  review: focused tests prove the manifest still covers installed, validation,
  and review-mode builders; the sample/relief cap manifest now rejects
  friction-plug wording and requires a positive lid-seat depth; the visible-role
  placeholder guard still passes. `uv run ruff check .` also passed.
  finding: the CAD geometry had advanced in RS36, but the machine-checkable
  acceptance contract was lagging one design cycle behind it. The manifest now
  states the production retention mechanism future edits must preserve.
  next: keep manifest semantics synchronized with every CAD mechanism change,
  especially for retention, sealing, and service-removal behavior.

RS38 convert septum mat marks into through-depth slit reliefs
  do: renamed the first-build septum mat slit parameters from mark language to
  `slit_cut_length_x` and `slit_cut_width_y`, then changed
  `build_septum_mat_inserts` so every pre-slit location cuts through the modeled
  silicone sheet and round plug stack rather than only engraving a shallow top
  mark.
  review: focused tests prove the installed COTS mat bodies keep the same
  per-plate bounds, reject the old `slit_mark_*` parameter names, and lose
  material compared with a no-slit control. Septum access, pipette puncture
  sweep, and overall component bounds still pass. `uv run ruff check .`,
  installed and `septum_mats_missing` viewer smokes, CAD generation, and the
  full row-coupon CAD suite passed after this cycle.
  finding: the liquid-handler access layer is now represented as a physical
  pre-slit consumable interface, not only top-surface witness marks on an
  otherwise solid silicone insert. The exact slit and plug dimensions still
  require caliper and wet-swelling measurement from the real mats.
  next: measure the Cole-Parmer mat sheet thickness, plug diameter/depth, slit
  length/width, swelling, and seated compression; update the first-build
  assumptions and metrology gauge from those records.

RS39 add published-profile well openings to the installed COTS microplates
  do: extended the CellVis P96-1.5H-N plate params with the published coverslip,
  bottom height, upper/lower well diameter, well-bottom equivalent diameter,
  internal-depth, cell-plane-depth, and top-recess values. `build_microplates`
  now adds a connected top well deck and cuts 96 upper-well openings per plate
  at the existing well-grid centers instead of representing the consumable as
  only perimeter sidewalls plus a bottom observation window.
  review: focused tests prove the published well dimensions are present, the
  upper well opening is larger than the septum plug diameter, the 96-well grid
  remains intact, the openings remove material from a solid-deck control, and
  installed septum mats do not intersect installed microplates. Existing
  support-land, septum, lid-access, and component-bounds tests still pass.
  `uv run ruff check .`, installed and `microplates_missing` viewer smokes, CAD
  generation, and the full row-coupon CAD suite passed after this cycle.
  finding: the biology-bearing consumable in the installed view now contains
  the well openings that the OT-2 pipette, septum plugs, headspace, and cells
  interact with. Lower-well taper, molded wall detail, bottom glass shape, and
  plate-to-plate manufacturing variation still need physical measurement.
  next: add or measure lower-well/taper geometry only when it changes an active
  clearance, optical, sealing, or fluidic claim; otherwise keep the published
  profile as the first-build authority and validate with real fit evidence.

RS40 add validation-only CellVis biology target-plane disks
  do: added a first-build `cell_plane_check_thickness_z` parameter, public
  `build_well_cell_plane_check`, validation export/viewer registration, docs,
  and tests for the published CellVis well-bottom target plane.
  review: focused tests prove the validation overlay contains one disk per
  well across all 384 one-row coupon well positions, uses the published
  6.18 mm equivalent-diameter well-bottom area, sits at the published
  12.40 mm plate-top-to-cell-plane depth, remains inside the installed plate
  stack, exports as separate validation STEP/STL artifacts, and does not enter
  the default installed production tree. `uv run ruff check .`,
  validation-tools viewer smoke, CAD generation, and the full row-coupon CAD
  suite passed after this cycle.
  finding: the CAD now exposes the actual biology/imaging target plane we are
  designing around without pretending cells, liquid, or assay state are
  installed production geometry. It remains a validation overlay only.
  next: use this overlay to bound optical/IR field of view, observer focus
  reach, per-well coverage, and edge-to-center biology-plane thermal
  characterization; replace published assumptions with measured plate data
  where they change clearance, optics, sealing, or fluidic behavior.

RS41 add validation-only IR thermopile FOV spot checks
  do: added a first-build `ir_fov_spot_check_thickness_z` parameter, public
  `build_ir_thermopile_fov_spot_check`, validation export/viewer registration,
  docs, and tests for the projected plate-margin FOV spot for each lower IR
  thermopile.
  review: focused tests prove the overlay contains one spot per installed IR
  thermopile, uses the layout-computed FOV spot diameter, sits at the plate
  underside, remains on the plate-margin side of the modeled well grid, stays
  outside every published CellVis well-bottom cell-plane disk, exports as
  separate validation STEP/STL artifacts, and does not enter the default
  installed production tree. `uv run ruff check .`, validation-tools viewer
  smoke, CAD generation, and the full row-coupon CAD suite passed after this
  cycle.
  finding: the CAD now distinguishes the direct biology/observer target plane
  from the IR thermopile's plate-margin proxy spot. That avoids overclaiming
  that the lower IR sensors directly measure cell temperature. The overlay is
  useful only if the next thermal protocol correlates plate-margin readings to
  the cell plane.
  next: shift the next cycle toward physical proof and scope discipline. Use
  the cell-plane and IR-spot overlays to write/execute edge-to-center thermal
  characterization; avoid adding further representational CAD detail unless it
  protects OT-2 fit, wet/dry isolation, print-native assembly, or a near-term
  physical measurement.

RS42 add the first-print readiness gate instead of more CAD detail
  do: added `docs/protocols/one_row_coupon_first_print_readiness.md` and linked
  it from the knowledge index plus the one-row coupon engineering doc. The
  protocol binds the existing production parts and validation artifacts to
  physical gates for CAD artifact identity, print QC, dry assembly, OT-2
  placement/no-motion clearance, passive leak and wet/dry witness behavior,
  consumable puncture, and sensor/thermal proxy readiness.
  review: `uv run ruff check .` passed; referenced output artifacts for the
  current assembly, CellVis cell-plane check, and IR FOV spot check exist; and
  the edited docs pass an ASCII sweep. No CAD geometry, generated STEP/STL
  output, or CAD tests changed in this cycle.
  finding: the immediate risk is not lack of more CAD representation; it is
  letting CAD claims outrun measured print, assembly, OT-2, leak, and sensor
  evidence. The new protocol makes "defer" and "block" valid outcomes and
  requires future CAD revisions to be driven by physical gate failures or
  near-term measurement needs.
  next: execute the first-print readiness protocol or use it to scope the print
  package. Do not add another CAD feature unless it directly protects OT-2 fit,
  wet/dry isolation, print-native assembly/service, or a physical measurement
  planned for the next build.

RS43 add a first-print measurement record template
  do: added
  `data/measurements/templates/one_row_coupon_first_print_readiness.md` and
  linked it from the first-print readiness protocol plus the measurements README.
  The template turns the protocol gates into ready-to-fill tables for session
  identity, CAD artifact identity, print QC, dry assembly, OT-2 placement,
  passive leak/wet-dry witness, consumable puncture, sensor/thermal proxy
  readiness, final decision, evidence-authorized CAD changes, and explicitly
  deferred features.
  review: `uv run ruff check .` passed; link/reference checks prove the
  protocol and measurements README point at the template; and the edited
  measurement/protocol docs pass an ASCII sweep. No CAD geometry, generated
  output, or CAD tests changed in this cycle.
  finding: the first print now has a concrete evidence capture surface, not only
  a prose protocol. This keeps the next build from inventing pass/fail criteria
  during assembly and makes `defer` a recorded anti-overengineering outcome.
  next: use the template for the first real row-coupon print record, then revise
  CAD only from measured failures, missing measurement targets, or blocked gates.

RS44 add a first-print CAD output package audit
  do: added `src/aevum_cad/row_coupon_first_print.py`,
  `scripts/audit_row_coupon_first_print_package.py`, and focused tests. The audit
  uses `row_coupon_part_manifest()` to classify required production artifacts by
  fabrication source, checks the assembly STEP, checks the ten required
  first-print validation artifacts from the protocol, and keeps the consumable
  metrology gauge optional rather than blocking.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  three tests; `uv run ruff check .` passed; the audit command passed on the
  current output package with 12 printed, 4 compressible/flexible, 2 COTS
  consumable, 9 electronics-or-dimensional-blank, 1 service-tubing, 10 required
  validation, and 1 optional validation artifacts; and the edited code/docs pass
  an ASCII sweep. No CAD geometry or generated output changed in this cycle.
  finding: Gate 0 now has a machine-checkable package audit. This prevents a
  first-print run from discovering missing STL/STEP files during assembly and
  keeps nonprintable COTS/electronics parts from being confused with printed
  production parts.
  next: run `uv run python scripts/audit_row_coupon_first_print_package.py`
  whenever the first-print output package is regenerated, then use the
  measurement template for physical Gate 1-6 evidence.

RS45 scaffold the first-print measurement record from the package audit
  do: extended `src/aevum_cad/row_coupon_first_print.py` with params checksum,
  output timestamp, production artifact category counts, a Gate 0 audit snapshot,
  and `scaffold_first_print_measurement_record()`. Added
  `scripts/scaffold_row_coupon_first_print_record.py` so the first-print record
  can be created from the current CAD package instead of hand-copying the
  template. Updated the readiness protocol and measurements README to use the
  scaffold command.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  six tests; `uv run ruff check .` passed; `uv run python
  scripts/audit_row_coupon_first_print_package.py` passed on the current output
  package; and `uv run python scripts/scaffold_row_coupon_first_print_record.py
  --output /tmp/aevum_one_row_coupon_first_print_scaffold_check.md --overwrite`
  created a record whose Gate 0 audit snapshot is ready while Gate 0-6 remain
  `not_tested`. No CAD geometry or generated output changed in this cycle.
  finding: the first-print path now has a reproducible evidence shell. This
  closes the gap between "the generated files exist" and "the physical record is
  ready to collect print, assembly, OT-2 placement, leak, consumable, and sensor
  evidence" without pretending that CAD artifact identity proves physical
  readiness.
  next: create the real first-print record, print/procure only the listed
  production parts and COTS/electronics blanks, then use Gate 1-6 failures to
  drive the next CAD revision.

RS46 create the real first-print record and pass Gate 0 CAD identity
  do: created
  `data/measurements/2026-06-02_one_row_coupon_first_print.md` from the scaffold,
  corrected the Gate 0 template table so it includes the package audit and
  scaffold commands required by the protocol, regenerated the row-coupon output
  package, and recorded Gate 0 CAD Artifact Identity as `pass` from observed
  evidence. Gate 1-6 remain `not_tested`.
  review: `uv run ruff check .` passed; `uv run pytest
  tests/test_row_coupon_cad.py -q` passed with 62 tests and seven third-party
  deprecation warnings; `uv run python scripts/generate_row_coupon.py`
  regenerated the output package; `uv run python
  scripts/audit_row_coupon_first_print_package.py` reported ready true with no
  missing required artifacts; `uv run python cad/view_one_row_coupon.py
  --show-validation-tools` loaded the installed validation scene and printed
  bounds; focused first-print metadata tests passed with seven tests; and record
  sanity checks proved Gate 0 is pass while physical Gate 1-6 are not marked
  pass.
  finding: the project now has a live first-print evidence record, not just a
  template. CAD artifact identity is proven for the current generated package,
  but this still authorizes only the next physical proof step. Print QC,
  screwless dry assembly, OT-2 placement/no-motion clearance, passive leak and
  wet/dry witness behavior, consumable puncture, and sensor/thermal readiness
  remain unproven.
  next: run Gate 1 Print QC after printing/procuring the package, then let any
  measured failure revise the CAD. Do not use Gate 0 pass to justify more
  representational CAD detail.

RS47 add Gate 1 CAD target bounds without claiming Print QC
  do: extended the first-print scaffold with
  `first_print_qc_targets()` and `first_print_qc_target_bounds_markdown()`.
  The scaffold now computes installed CAD bounds for every printed and
  compressible/flexible production artifact and inserts them as a Gate 1 CAD
  Target Bounds section. Updated the live first-print record, measurement
  template, readiness protocol, measurements README, and focused tests.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  eight tests; `uv run ruff check .` passed; `uv run python
  scripts/audit_row_coupon_first_print_package.py` still reports ready true;
  record sanity checks prove Gate 0 remains pass, Gate 1-6 are not marked pass,
  and the live record contains 16 printed/compressible target rows including
  `deck_pods` at 128.00 x 357.50 x 84.10 mm. The edited files pass an ASCII
  sweep. No CAD geometry or generated output changed in this cycle.
  finding: Gate 1 now has bench-useful target dimensions before the first print
  is measured. This closes a practical gap in the Print QC workflow without
  overclaiming: the target table is CAD expectation only, not physical evidence,
  and compressible/flexible parts remain nominal uncompressed bodies until real
  stock or printed TPU is measured.
  next: print/procure the package and fill Gate 1 measured values against these
  targets. CAD changes should come from measured misses, fit failures, support
  scars on seal lands, latch/cap service failures, or blocked sensor/observer
  access.

RS48 generate the first-print package handoff manifest
  do: added `first_print_package_manifest_markdown()` and
  `write_first_print_package_manifest()` to
  `src/aevum_cad/row_coupon_first_print.py`, plus
  `scripts/write_row_coupon_first_print_package_manifest.py`. Generated
  `outputs/cad/aevum_one_row_coupon_first_print_package_manifest.md` and linked
  it from the live first-print record. Updated the readiness protocol and
  measurements README to make the manifest part of the pre-slicing handoff.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  ten tests; `uv run ruff check .` passed; `uv run python
  scripts/audit_row_coupon_first_print_package.py` still reports ready true;
  and `uv run python scripts/write_row_coupon_first_print_package_manifest.py
  --overwrite` reports 12 printed slicer parts and zero missing required
  artifacts. Sanity checks prove COTS microplates are absent from the slicer
  queue, present in the procurement section, and the live record links the
  generated manifest. Edited/generated files pass an ASCII sweep.
  finding: the first print now has an explicit handoff boundary: printed STLs
  are separated from flexible/compressible parts, COTS/electronics/service
  items, and validation-only bodies. This reduces the risk of accidentally
  treating dimensional reference models or validation artifacts as production
  parts.
  next: use the manifest to slice only the 12 printed polymer parts and procure
  or blank the nonprinted items, then run Gate 1 measured Print QC against the
  live record's target table.

RS49 prepare the printed-STL-only slicer queue
  do: added `FirstPrintSlicerQueueItem`,
  `first_print_slicer_queue_artifacts()`,
  `first_print_slicer_queue_manifest_markdown()`, and
  `prepare_first_print_slicer_queue()` to
  `src/aevum_cad/row_coupon_first_print.py`, plus
  `scripts/prepare_row_coupon_first_print_slicer_queue.py`. Generated
  `outputs/cad/first_print_slicer_queue/` with only the 12 printed production
  STL files and a `SLICER_QUEUE_MANIFEST.md` containing SHA256 hashes and CAD
  target bounds. Linked the queue from the live first-print record and updated
  the readiness protocol plus measurements README.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  fourteen tests; `uv run ruff check .` passed; and `uv run python
  scripts/prepare_row_coupon_first_print_slicer_queue.py --overwrite`
  regenerated the queue with 12 printed STLs. `uv run python
  scripts/audit_row_coupon_first_print_package.py` still reports ready true.
  Sanity checks showed 12 queued STL files and no COTS, electronics, service,
  flexible, or validation names in the queue.
  finding: the first print now has an actual slicer input directory, not only a
  prose/markdown instruction. The queue is intentionally narrower than the CAD
  output package and blocks the common error of slicing microplates, electronics
  envelopes, gasket reference bodies, or validation overlays as production
  parts.
  next: slice and print the 12 queued STL files, then fill Gate 1 measured
  values in the live record. Keep flexible seals, COTS consumables,
  electronics, service tubing, and validation bodies out of the production print
  job unless a separate protocol explicitly calls for a gauge or blank.

RS50 audit the slicer queue against the generated CAD package
  do: added `FirstPrintSlicerQueueAudit`,
  `FirstPrintSlicerQueueHashMismatch`, and
  `audit_first_print_slicer_queue()` to
  `src/aevum_cad/row_coupon_first_print.py`, plus
  `scripts/audit_row_coupon_first_print_slicer_queue.py`. Updated the
  readiness protocol, measurement template, measurements README, and live
  first-print record so the slicer queue audit is part of the pre-print
  evidence trail.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  eighteen tests; `uv run ruff check .` passed; `uv run python
  scripts/audit_row_coupon_first_print_slicer_queue.py` reported queue manifest
  ok, 12 expected printed STLs, 12 actual printed STLs, zero package missing
  artifacts, zero missing queue STLs, zero extra queue files, zero hash
  mismatches, and ready true; and `uv run python
  scripts/audit_row_coupon_first_print_package.py` still reports ready true.
  Record sanity checks prove the queue-audit row is pass while Gate 1-6 remain
  unpassed, and queue sanity checks prove no forbidden COTS/electronics/service,
  flexible/gasket, or validation files are queued.
  finding: the slicer queue is now auditable, not only generated. This closes
  the stale/contaminated-queue failure mode before physical printing and keeps
  the pre-print boundary machine-checkable.
  next: slice and print the audited 12-STL queue, then record Gate 1 measured
  part bounds, surface/fit defects, latch/cap behavior, and any required CAD
  revisions.

RS51 generate a blank Gate 1 QC worksheet from installed CAD targets
  do: added `FirstPrintGate1QCWorksheetRow`,
  `first_print_gate1_qc_worksheet_rows()`,
  `first_print_gate1_qc_worksheet_csv()`, and
  `write_first_print_gate1_qc_worksheet()` to
  `src/aevum_cad/row_coupon_first_print.py`, plus
  `scripts/write_row_coupon_first_print_gate1_qc_worksheet.py`. Generated
  `data/measurements/2026-06-02_one_row_coupon_gate1_qc.csv` with one blank
  inspection row for each printed or compressible/flexible production artifact
  and linked it from the live first-print record. Updated the measurement
  template, readiness protocol, and measurements README so the worksheet is a
  normal pre-print evidence surface.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  twenty-one tests; `uv run ruff check .` passed; `uv run python
  scripts/write_row_coupon_first_print_gate1_qc_worksheet.py --output
  data/measurements/2026-06-02_one_row_coupon_gate1_qc.csv --overwrite`
  generated 16 rows with default result `not_tested`; the package audit and
  slicer queue audit still report ready true. Sanity checks showed 17 CSV lines
  including the header, no `cots_microplates` row, no accidental `pass`,
  `revise`, or `block` results, and Gate 1-6 still unpassed in the live record.
  finding: Gate 1 now has a concrete measurement-entry artifact tied to the
  installed CAD target bounds. This reduces inspection ambiguity without
  claiming physical readiness before the print exists.
  next: slice and print the audited 12-STL queue, procure or blank nonprinted
  items, then fill the Gate 1 worksheet and live record with measured bounds,
  surface defects, latch/cap fit, sensor pocket fit, and any CAD revisions
  authorized by real failures.

RS52 audit the Gate 1 QC worksheet claim boundary
  do: added `FirstPrintGate1QCWorksheetIssue`,
  `FirstPrintGate1QCWorksheetAudit`, and
  `audit_first_print_gate1_qc_worksheet()` to
  `src/aevum_cad/row_coupon_first_print.py`, plus
  `scripts/audit_row_coupon_first_print_gate1_qc_worksheet.py`. The audit
  validates the generated worksheet schema, expected installed CAD target rows,
  duplicate/missing/extra parts, allowed result states, coherent measurement
  vectors, and the rule that a row marked `pass` must include measured X/Y/Z
  values within the +/- 1.0 mm first-print tolerance. Linked the audit command
  from the measurement template, live record, readiness protocol, and
  measurements README.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  twenty-five tests; `uv run ruff check` on the touched code/scripts passed;
  `uv run python scripts/audit_row_coupon_first_print_gate1_qc_worksheet.py
  --worksheet data/measurements/2026-06-02_one_row_coupon_gate1_qc.csv`
  reported `worksheet_valid: true`, `gate1_pass_ready: false`, 16 expected and
  actual rows, 16 `not_tested` rows, no missing/extra/duplicate parts, and zero
  issues. Package and slicer queue audits still report ready true.
  finding: the blank worksheet is now machine-checkable as a valid pre-print
  artifact while remaining explicitly not pass-ready. This blocks a false Gate 1
  pass claim from empty measurement fields, extra COTS rows, malformed targets,
  or out-of-tolerance measurements marked `pass`.
  next: slice and print the audited 12-STL queue, procure or blank nonprinted
  items, enter measured values into the Gate 1 worksheet, rerun the worksheet
  audit, and let any `revise`, `block`, out-of-tolerance, or fit-failure row
  drive the next CAD revision.

RS53 add nonprinted installed-item inventory and audit
  do: added `FirstPrintInstallInventoryRow`,
  `FirstPrintInstallInventoryIssue`, `FirstPrintInstallInventoryAudit`,
  `first_print_install_inventory_rows()`,
  `first_print_install_inventory_csv()`,
  `write_first_print_install_inventory()`, and
  `audit_first_print_install_inventory()` to
  `src/aevum_cad/row_coupon_first_print.py`, plus
  `scripts/write_row_coupon_first_print_install_inventory.py` and
  `scripts/audit_row_coupon_first_print_install_inventory.py`. Generated
  `data/measurements/2026-06-02_one_row_coupon_install_inventory.csv` with
  twelve blank `not_tested` rows covering COTS consumables, side gas tubing,
  electronics, cable pigtails, headspace carriers, IR packages, and gas sensor
  PCBs or allowed dimensional blanks. Linked the worksheet and audit command
  from the measurement template, live record, readiness protocol, and
  measurements README.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  thirty-one tests; `uv run ruff check .` passed; package and slicer queue
  audits still report ready true; the Gate 1 QC worksheet still audits as
  valid but not pass-ready; and the install inventory audit reports
  `worksheet_valid: true`, `install_inventory_ready: false`, twelve expected
  and actual rows, twelve `not_tested` rows, no missing/extra/duplicate parts,
  and zero issues. ASCII and physical-gate-pass scans passed.
  finding: the installed operating prototype now has a machine-checkable
  nonprinted-item boundary. COTS plates and septum mats must be real parts to
  pass inventory; gas tubing may be a measured replacement; electronics and
  sensor packages may use dimensionally faithful blanks only with explicit
  mechanical-only notes. This keeps dry assembly from silently treating CAD
  reference bodies as installed hardware.
  next: slice and print the audited 12-STL queue, identify or procure every
  inventory row, rerun the inventory audit, then proceed to measured Gate 1
  Print QC and Gate 2 dry assembly only with real or explicitly blanked parts.

RS54 add first-print preflight audit across all pre-print artifacts
  do: added `FirstPrintPreflightIssue`, `FirstPrintPreflightAudit`, and
  `audit_first_print_preflight()` to
  `src/aevum_cad/row_coupon_first_print.py`, plus
  `scripts/audit_row_coupon_first_print_preflight.py`. The audit composes the
  CAD package audit, printed-STL queue audit, Gate 1 QC worksheet audit, install
  inventory audit, and live measurement-record gate/link checks. It requires
  Gate 0 CAD Artifact Identity to be passed, requires the linked manifest,
  queue, worksheet, and inventory paths to exist, and requires physical Gates
  1-6 to remain unpassed for the pre-print state. Linked the command from the
  measurement template, live record, readiness protocol, and measurements
  README.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  thirty-four tests; `uv run ruff check .` passed; `uv run python
  scripts/audit_row_coupon_first_print_preflight.py --record
  data/measurements/2026-06-02_one_row_coupon_first_print.md` reported
  `preprint_ready: true`, package ready true, slicer queue ready true, Gate 1
  worksheet valid true and pass-ready false, install inventory valid true and
  install-ready false, Gate 0 pass true, zero physical gate passes, zero missing
  record links, and zero issues. ASCII and physical-gate-pass scans passed.
  finding: the pre-print state is now a single machine-checkable claim rather
  than a loose collection of green subcommands. It explicitly authorizes moving
  toward slicing/printing while preventing worksheet or inventory preparation
  from being mistaken for physical Gate 1-6 evidence.
  next: slice and print the audited 12-STL queue. After the print exists, fill
  the Gate 1 QC worksheet with measured dimensions and defects, update the
  install inventory with real parts or allowed blanks, and let the next audit
  failure decide whether CAD changes are warranted.

RS55 correct preflight to require explicit slicing setup
  do: tightened `FirstPrintPreflightAudit` and
  `audit_first_print_preflight()` so `preprint_ready` requires the live
  measurement record to fill `Printer / material / profile`. Updated
  `scripts/audit_row_coupon_first_print_preflight.py` to print required-session
  field status and missing field names. Updated the live first-print record so
  the preflight command is `block`, not `pass`, until the actual printer,
  material, and slicing profile are recorded. Updated the readiness protocol
  and measurements README to make this explicit.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  thirty-five tests; `uv run ruff check .` passed; package and slicer queue
  audits remain ready true; the live preflight audit exits nonzero with
  `preprint_ready: false`, package ready true, queue ready true, Gate 1
  worksheet valid true and pass-ready false, install inventory valid true and
  install-ready false, Gate 0 pass true, one missing session field
  (`Printer / material / profile`), zero physical gate passes, zero missing
  record links, and one issue for the blank required field. ASCII and physical
  gate pass scans passed.
  finding: RS54 overclaimed readiness to start slicing because the record still
  lacked the concrete printer/material/profile. The corrected boundary keeps the
  audited STL queue intact but blocks slicing/printing until the real slicing
  setup is named. Local slicer app binaries were found at
  `/Applications/Original Prusa Drivers/PrusaSlicer.app/Contents/MacOS/PrusaSlicer`
  and `/Applications/BambuStudio.app/Contents/MacOS/BambuStudio`, but neither
  is accepted as the active profile until recorded in the measurement record.
  next: choose the actual printer/material/profile, record it in the live
  first-print measurement record, rerun the preflight audit to restore
  `preprint_ready: true`, then slice and print the audited 12-STL queue.

RS56 add selected-slicer setup worksheet and bind it to preflight
  do: added `FirstPrintSlicerSetupRow`, `FirstPrintSlicerSetupIssue`,
  `FirstPrintSlicerSetupAudit`, local slicer-discovery helpers,
  `write_first_print_slicer_setup()`, `audit_first_print_slicer_setup()`,
  `scripts/write_row_coupon_first_print_slicer_setup.py`, and
  `scripts/audit_row_coupon_first_print_slicer_setup.py`. The generated
  worksheet records slicer executable, version, printer profile, material
  profile, print profile, profile source, selection state, result, and notes.
  The first-print preflight now requires the linked slicer setup worksheet to
  be structurally valid, requires exactly one selected row marked `pass`, and
  requires the live `Printer / material / profile` field to exactly match the
  selected setup summary.
  review: `uv run pytest tests/test_row_coupon_first_print.py -q` passed with
  thirty-nine tests; `uv run ruff check .` passed; `uv run python
  scripts/audit_row_coupon_first_print_slicer_setup.py --worksheet
  data/measurements/2026-06-02_one_row_coupon_slicer_setup.csv` reported
  `worksheet_valid: true`, `setup_selected: false`, two rows, zero selected
  rows, and zero issues; package and slicer queue audits report ready true; and
  the live preflight exits nonzero with `preprint_ready: false`, package ready
  true, queue ready true, slicer setup valid true, slicer setup selected false,
  Gate 1 worksheet valid true, install inventory valid true, Gate 0 pass true,
  one missing session field (`Printer / material / profile`), zero physical
  gate passes, zero missing record links, and two issues. ASCII scan passed.
  finding: local candidates are now auditable without being silently accepted.
  The discovered PrusaSlicer row names `Original Prusa MK4 Input Shaper 0.4
  nozzle`, `Generic PETG @PGIS`, and `0.20mm STRUCTURAL @MK4IS 0.4` from
  `PrusaSlicer.ini`; the BambuStudio row is intentionally incomplete until
  machine, filament, and process profiles are selected. No setup is selected
  yet, so the preflight stays blocked even though the CAD package and printed
  STL queue are clean.
  next: choose the actual printer/material/profile row, mark exactly one setup
  row `selected=yes` and `result=pass`, copy its summary into the live
  `Printer / material / profile` field, rerun the slicer-setup audit and
  preflight, then slice the audited 12-STL queue.

RS57 make slicer setup selection an atomic audited operation
  do: added `FirstPrintSlicerSetupSelection` and
  `select_first_print_slicer_setup()` to
  `src/aevum_cad/row_coupon_first_print.py`, plus
  `scripts/select_row_coupon_first_print_slicer_setup.py`. The selector can
  match by exact setup summary or by slicer/profile fields, refuses incomplete
  candidates, marks exactly one row `selected=yes` and `result=pass`, marks all
  other rows unselected, audits the updated worksheet, and writes the selected
  setup summary into the live `Printer / material / profile` record field.
  Updated the readiness template, live measurement record, protocol, and
  measurements README so the path no longer depends on hand-copying a profile
  string.
  review: focused selector/template tests passed with six tests; the full
  first-print suite passed with forty-one tests; `uv run ruff check .` passed;
  `uv run python scripts/select_row_coupon_first_print_slicer_setup.py --help`
  printed the expected selector arguments; a temporary-copy smoke selection of
  the PrusaSlicer row selected row 0, produced a valid selected worksheet, and
  wrote the matching setup summary into the copied record. The live worksheet
  remains intentionally unselected with `worksheet_valid: true`, two rows, zero
  selected rows, and zero issues. The live preflight still exits nonzero with
  `preprint_ready: false`, package ready true, queue ready true, slicer setup
  valid true, slicer setup selected false, Gate 1 worksheet valid true,
  install inventory valid true, Gate 0 pass true, one missing session field
  (`Printer / material / profile`), zero physical gate passes, zero missing
  record links, and two issues. ASCII and physical-gate-pass scans passed.
  finding: the first-print path now has a reversible, auditable transition from
  discovered slicer candidates to one real print setup. The implementation
  avoids making a hidden printer choice while removing the manual transcription
  failure mode that could make the live record disagree with the setup CSV.
  next: run the selector on the live worksheet only after the actual printer,
  material, and profile are chosen, then rerun slicer-setup and preflight
  audits before slicing the audited 12-STL queue.

RS58 add sliced-output worksheet and audit before print start
  do: added `FirstPrintSlicedOutputRow`, `FirstPrintSlicedOutputIssue`,
  `FirstPrintSlicedOutputAudit`, `first_print_sliced_output_rows()`,
  `first_print_sliced_output_csv()`, `write_first_print_sliced_outputs()`,
  and `audit_first_print_sliced_outputs()` to
  `src/aevum_cad/row_coupon_first_print.py`, plus
  `scripts/write_row_coupon_first_print_sliced_outputs.py` and
  `scripts/audit_row_coupon_first_print_sliced_outputs.py`. The worksheet is
  generated from the audited printed-STL queue and records each queued STL
  path/hash, sliced output path/hash, selected setup summary, result, and notes.
  The audit distinguishes a valid blank worksheet from a print-ready sliced
  package, checks current queue hashes, requires pass rows to name the selected
  setup, requires recognized sliced-output suffixes, and verifies sliced-output
  file hashes. Updated the scaffold, readiness template, live measurement
  record, protocol, measurements README, and tests.
  review: focused sliced-output/template/scaffold tests passed with six tests;
  the full first-print suite passed with forty-five tests; `uv run ruff check
  .` passed; live slicer queue audit reports ready true with twelve expected
  and actual STLs, zero missing, zero extra, and zero hash mismatches; generated
  `data/measurements/2026-06-02_one_row_coupon_sliced_outputs.csv` with twelve
  blank `not_tested` rows; live sliced-output audit reports `worksheet_valid:
  true`, `sliced_outputs_ready: false`, `queue_ready: true`, twelve expected
  and actual rows, zero missing/extra/duplicate parts, and zero issues. The live
  preflight still exits nonzero only for the intended unselected slicer setup
  and blank `Printer / material / profile` field. ASCII and physical-gate-pass
  scans passed.
  finding: the path now has a machine-checkable boundary between a correct STL
  queue and actual slicer output. This prevents print start from relying on an
  informal assumption that sliced files correspond to the audited queue and the
  selected printer/material/profile.
  next: after the actual setup is selected and preflight passes, slice the
  queued STLs, fill each sliced-output row with output path/hash and the selected
  setup summary, rerun the sliced-output audit with readiness required, and only
  then start the first print.

RS59 remove obsolete sample/relief role-marker nubs
  do: removed the production `port_role_marker_*` parameters, `role_marker_count`
  layout field, lid-cover marker solids, and cap-marker helper path. Replaced
  the reused marker-overlap parameter with the production-specific
  `port_cap_grip_attachment_overlap_xy`, keeping only the sample/relief cap
  flange, annular seal lip, and grip tab needed for closure and service removal.
  Updated the CAD tests so the single remaining top sample/relief port must not
  carry role-marker metadata, and updated `docs/engineering/one_row_coupon.md`
  to state that the former role-code marker nubs are removed because the
  operating design has only one top closure.
  review: focused port/cap CAD tests passed with fourteen tests; the full CAD
  suite passed with sixty-two tests; `uv run ruff check .` passed; installed
  and validation-tools viewer smokes loaded; `uv run python
  scripts/generate_row_coupon.py` regenerated the CAD output package with
  layout x=147.60 y=377.25 stack_z=58.10 deck_to_top_z=140.60 mm; package
  manifest, printed-STL queue, and sliced-output worksheet were regenerated;
  package audit and slicer queue audit report ready true; sliced-output audit
  reports `worksheet_valid: true`, `sliced_outputs_ready: false`,
  `queue_ready: true`, twelve expected/actual rows, and zero issues. The live
  preflight still exits nonzero only for the intended unselected slicer setup
  and blank `Printer / material / profile` field. ASCII and physical-gate-pass
  scans passed.
  finding: the default operating view no longer preserves old multi-port role
  encoding on the single remaining top sample/relief cap. The marker-removal
  regeneration also exposed a readiness gap: the live record's params hash had
  to be updated manually, and current preflight does not yet verify that the
  record `Params SHA256` matches the active params file.
  next: add a preflight params-hash/timestamp consistency check so stale live
  measurement records cannot pass after a CAD or params regeneration; then
  continue toward selecting the actual slicer setup, slicing the audited queue,
  and filling the sliced-output worksheet.

RS60 bind first-print preflight to live CAD identity
  do: added machine checks in `audit_first_print_preflight()` so the linked
  `Params file` must exist, the live `Params SHA256` must match that file, and
  the live `Generated output timestamp` must match the current generated CAD
  package timestamp. Added the `Params file` link to the required preflight
  fields, exposed params/timestamp match fields in the CLI report, updated the
  scaffold to overwrite the template params path for copied/test records, and
  added stale params-hash plus stale generated-timestamp regression tests.
  Updated the readiness protocol, measurements README, and live first-print
  record evidence note so the preflight contract is explicit.
  review: touched-code ruff passed; the focused preflight/scaffold pytest subset
  passed with eight tests in 590.08 s; the live preflight exits nonzero with
  `preprint_ready: false`, package ready true, slicer queue ready true,
  `params_hash_matches: true`,
  `generated_output_timestamp_matches: true`, Gate 1 worksheet valid true,
  install inventory valid true, Gate 0 pass true, one missing session field
  (`Printer / material / profile`), zero physical gate passes, zero missing
  record links, and two intended issues: blank printer/material/profile and no
  selected passing slicer setup.
  finding: the stale-record gap exposed by RS59 is closed. A regenerated CAD
  package or changed params file can no longer leave a plausible live
  first-print record that passes preflight with old identity fields.
  next: run the slicer-setup selector on the live worksheet only after the
  actual printer, material, and profile are chosen; rerun slicer-setup and
  preflight audits, slice the audited queued STLs, fill and audit sliced-output
  rows as ready, then start Gate 1 print QC.

RS61 expose Gate 3 OT-2 placement targets in the print record
  do: added `first_print_ot2_placement_targets_markdown()` to the first-print
  scaffold path and inserted the generated block into the live measurement
  record below Gate 3. The block pulls current CAD layout values for
  deck-to-top assembly envelope, assembly footprint, adjacent-slot service
  clearance, required clearance margin, 384 septum puncture targets, and the
  protected dry-bay footprint. Updated the readiness protocol to state that
  these are Gate 3 measurement targets, not a pass claim.
  review: touched-code ruff passed; focused scaffold/OT-2-placement tests
  passed with two tests; the live preflight still exits nonzero with package
  ready true, slicer queue ready true, params hash/timestamp matches true, zero
  physical gate passes, zero missing record links, and the two intended issues:
  blank `Printer / material / profile` and no selected passing slicer setup.
  Touched-file ASCII scan and physical-gate-pass scan passed.
  finding: the OT-2 placement gate no longer asks for an "assembly high point"
  without giving the bench a CAD target. The record now carries the concrete
  140.60 mm deck-to-top envelope and 141.60 mm first-print high-point limit
  next to adjacent-slot, pipette-target, and dry-bay footprint targets.
  next: choose the actual printer/material/profile, select exactly one slicer
  setup row, rerun preflight, slice the audited queue, then use the Gate 1 and
  Gate 3 targets during physical inspection instead of adding more CAD detail.

RS62 expose Gate 4 wet/dry witness targets in the print record
  do: added `first_print_wet_dry_witness_targets_markdown()` to the first-print
  scaffold path and inserted the generated block into the live measurement
  record below Gate 4. The block pulls current CAD dry-bay ingress audit values
  for the protected dry-bay volume, side-gas wet collectors and dams,
  sample/relief cap collectors and dam, gasket-tab root collectors and dams,
  dry-bay aperture thresholds, and aperture-adjacent witness gutters. Updated
  the readiness protocol to state that these are dye/condensate inspection
  targets, not a Gate 4 pass claim.
  review: touched-code ruff passed; focused scaffold/wet-dry-target tests
  passed with two tests; the live record still has every Gate 4 source and
  Gate 1-6 result at `not_tested`.
  finding: the passive leak/wet-dry gate no longer asks the bench to "inspect
  gutters and dams" without a countable target set. The record now says the
  printed coupon should expose 10 wet collectors, 7 inboard dams, 4 raised
  dry-bay aperture thresholds, and 8 aperture-adjacent gutters, all while
  keeping the 120.20 x 357.50 x 80.00 mm dry-bay volume dry.
  next: select the actual printer/material/profile and slice the audited queue;
  during Gate 4, use dye and humidity exposure to validate the witness target
  set before allowing sensor electronics or biology-facing wet operation.

RS63 expose Gate 5 consumable/puncture targets in the print record
  do: added `first_print_consumable_puncture_targets_markdown()` to the
  first-print scaffold path and inserted the generated block into the live
  measurement record below Gate 5. The block pulls current CAD/protocol values
  for four plates, four septum mats, CellVis plate footprint, plate support
  datum, locator rail count/height, placeholder Cole-Parmer mat stack, plug and
  slit assumptions, 384 puncture targets, puncture swept diameter and Z range,
  8.00 N force limit, 20-cycle repeat minimum, and 0.25 mm plate-shift limit.
  Updated the readiness protocol to state that these are measurement targets,
  not a Gate 5 pass claim.
  review: touched-code ruff passed; focused scaffold/consumable-puncture-target
  tests passed with two tests; the live record still has every Gate 5 source
  and Gate 1-6 result at `not_tested`.
  finding: the consumable/puncture gate no longer hides placeholder mat
  geometry behind a linked protocol. The first-print record now says exactly
  which consumable assumptions the bench must measure or revise before CAD
  septum access can be treated as physically true.
  next: select the actual printer/material/profile and slice the audited queue;
  after Gates 1-4 pass, run the linked consumable puncture protocol against the
  Gate 5 target block before claiming all-well liquid-handler access through
  the Cole-Parmer mat.

RS64 expose Gate 6 sensor/thermal targets in the print record
  do: tightened `first_print_sensor_thermal_targets_markdown()` so the
  scaffolded Gate 6 target block records the reversible sensor install
  workflow, supply/return gas PCB cartridge envelope, duct sampling aperture
  and dead-volume cell, gas-PCB gasket thickness/compression, SHT41 carrier
  envelope and drip-ring aperture, IR thermopile pocket, IR aperture/gasket,
  plate-margin IR proxy FOV, lower/lid harness route counts, service connector
  and cable envelope counts, cable bend relief, and the required thermal proxy
  plan. Inserted the generated block into the live first-print record below the
  Gate 6 checklist and updated the protocol so those rows are installation
  targets, not powered sensor or biology evidence.
  review: touched-code ruff passed; focused scaffold/sensor-thermal-target
  tests passed with two tests; full first-print tests passed with 51 tests.
  Full ruff, `git diff --check`, touched-file ASCII scan, physical-gate-pass
  scan, and the expected-failing live preflight audit passed. The live preflight
  still reports `preprint_ready: false`, package/queue/worksheet/hash/timestamp
  checks clean, zero physical gate passes, and only the unchosen
  printer/material/profile plus no selected slicer setup blocking readiness.
  finding: Gate 6 no longer hides sensor installability behind prose. The
  first-print record now tells the bench exactly what sensor cartridges,
  apertures, gaskets, cable dress, and proxy thermal assumptions must be
  inspected before powered gas/RH/CO2/IR or biology-facing claims are allowed.
  next: select the actual printer/material/profile and slice the audited queue;
  then use Gate 6 only after Gates 1-5 have established print fit, OT-2
  placement, wet/dry witness behavior, and consumable puncture access.

RS65 expose Gate 2 dry assembly targets in the print record
  do: added `first_print_dry_assembly_targets_markdown()` and inserted its
  scaffolded target block into the live first-print record below Gate 2. The
  block pulls current CAD/service values for dry installed stack order, five
  plate/mat service cycles, plate support datum, locator rails, consumable
  envelope, latch gasket squeeze budget, wedge-lock station count and travel
  body, omitted latch-span inspection, latch self-lock margin, side gas tube
  envelope/bend radius, electrical pigtail bend radius, sensor package dry fit,
  and dry-bay open volume. Updated the protocol so Gate 2 uses those rows as
  dry production assembly targets, not pass evidence.
  review: touched-code ruff passed; focused scaffold/dry-assembly-target tests
  passed with two tests; the full first-print suite passed with 52 tests. The
  expected-failing live preflight audit still reports package/queue/worksheet,
  params-hash, and generated-output timestamp checks clean, zero physical gate
  passes, and only the unchosen printer/material/profile plus no selected
  slicer setup blocking readiness.
  finding: Gate 2 no longer asks the bench to infer dry assembly expectations
  from the CAD model. The live record now calls out the exact service cycles,
  stack fit, latch squeeze, and service-dress targets to inspect, including the
  current omitted latch station and 181.00 mm active-span watch before any wet
  or powered claim is allowed.
  next: select the actual printer/material/profile and slice the audited queue;
  after print, let Gate 2 dry assembly decide whether the omitted latch station,
  wedge detent margin, and service routing are acceptable or require CAD
  revision.

RS66 bind live preflight to generated CAD target sections
  do: added `first_print_cad_target_sections_markdown()` and extended
  `audit_first_print_preflight()` so `preprint_ready` requires every generated
  Gate 1-6 CAD target block in the live measurement record to match the current
  params/layout. The preflight CLI now reports `cad_target_sections_match` and
  lists stale target section names. Updated the live first-print record and
  readiness protocol to make this a pre-print invariant.
  review: touched-code ruff passed; focused target-section/preflight tests
  passed with three tests; the full first-print suite passed with 54 tests;
  full ruff, `git diff --check`, touched-file ASCII scan, physical-gate-pass
  scan, and the expected-failing live preflight audit passed. The live preflight
  now reports
  `cad_target_sections_match: true`, `stale_cad_target_sections: 0`, package
  and queue ready, params hash and generated timestamp matched, zero physical
  gate passes, and only the unchosen printer/material/profile plus no selected
  slicer setup blocking readiness.
  finding: the first-print packet can no longer drift after a CAD/params change
  while still looking preflight-clean. If any Gate 1-6 generated target block is
  missing or stale, preflight names the stale section and blocks slicing/print
  authorization before physical evidence starts.
  next: select the actual printer/material/profile, run the selector on the live
  slicer setup worksheet, rerun preflight, slice the audited queue, and let
  print/assembly gates decide any CAD revisions.

RS67 bind live preflight to sliced-output worksheet validity
  do: added `Sliced output worksheet` to the required preflight link set and
  composed `audit_first_print_sliced_outputs()` into
  `audit_first_print_preflight()`. The preflight now reports
  `sliced_outputs_valid` and `sliced_outputs_ready`, requires a valid linked
  sliced-output worksheet before `preprint_ready`, and still allows
  `sliced_outputs_ready: false` before actual slicing. Updated the CLI,
  readiness protocol, live record note, and first-print preflight fixture/tests.
  review: touched-code ruff passed; focused sliced-output/preflight tests
  passed with six tests; the full first-print suite passed with 55 tests; full
  ruff, `git diff --check`, touched-file ASCII scan, physical-gate-pass scan,
  and the expected-failing live preflight audit passed. The live preflight now
  reports
  `sliced_outputs_valid: true`, `sliced_outputs_ready: false`,
  `cad_target_sections_match: true`, zero stale target sections, zero physical
  gate passes, and only the unchosen printer/material/profile plus no selected
  slicer setup blocking readiness.
  finding: the first-print packet no longer has an unaudited slice handoff
  link. Preflight now proves the blank sliced-output worksheet corresponds to
  the current queue before setup selection/slicing, while preserving the later
  requirement that actual sliced files and hashes must be filled before print
  start.
  next: select the actual printer/material/profile, run the selector on the live
  setup worksheet, rerun preflight, slice the audited queue, and fill/audit
  sliced-output rows before print start.

RS68 add explicit print-start readiness gate
  do: added `print_start_ready` to `FirstPrintPreflightAudit` as the stricter
  composition of `preprint_ready` and `sliced_outputs_ready`. The preflight CLI
  now prints `print_start_ready` and supports
  `--require-sliced-outputs-ready` for the post-slicing, pre-print authorization
  check. Updated the readiness protocol, live first-print record note, and
  first-print tests so a valid blank sliced-output worksheet can pass preprint
  readiness while still blocking print start.
  review: focused preflight readiness tests passed with two tests; the full
  first-print suite passed with 56 tests; full ruff, `git diff --check`,
  touched-file ASCII scan, and physical-gate-pass scan passed. The live
  preflight and the stricter print-start invocation both intentionally exit
  nonzero while reporting `preprint_ready: false`, `print_start_ready: false`,
  `sliced_outputs_valid: true`, `sliced_outputs_ready: false`, current
  params/generated CAD target evidence, zero physical gate passes, and two live
  blockers: blank `Printer / material / profile` plus no selected passing
  slicer setup row.
  finding: the first-print packet now has separate machine-readable states for
  "CAD/package/session is ready to slice" and "actual sliced files are ready to
  print." This prevents a valid worksheet template from being mistaken for
  authorization to start printing the production-operating coupon.
  next: select the actual printer/material/profile, run the selector on the live
  setup worksheet, rerun preflight, slice the audited queue, fill/audit
  sliced-output rows, then rerun preflight with
  `--require-sliced-outputs-ready` before print start.

RS69 add combined operating service-dress validation body
  do: added `operating_service_dress_check` as a validation-only CadQuery body
  and required first-print validation artifact. The layout now publishes a
  non-duplicated `operating_service_dress_envelopes` list built from side gas
  fitting/barb/strain-relief/tube envelopes plus row-end electrical cable bend
  envelopes; the pipette toolhead clearance uses the same list. Regenerated CAD
  outputs, package manifest, printed-STL queue, and blank sliced-output
  worksheet. Updated the first-print record generated-output timestamp to
  `2026-06-02T21:48:31Z`.
  review: focused CAD tests passed with four tests, focused first-print package
  tests passed with two tests, the full row-coupon CAD suite passed with
  63 tests, the full first-print suite passed with 56 tests, full ruff passed,
  package audit ready true with 11 required validation bodies, slicer queue
  ready true with 12 printed STLs, sliced-output worksheet valid true and
  ready false, validation-viewer smoke loaded the new
  `operating_service_dress_check`, and the live preflight remains intentionally
  blocked only by the unchosen printer/material/profile plus no selected
  passing slicer setup row.
  finding: connected gas and electrical services are no longer checked only as
  separate overlays. The CAD now has one normal-operation service-dress target
  for physical tube/cable dressing, OT-2 neighbor-slot clearance, dry-bay
  avoidance, septum-field avoidance, and toolhead-clearance accounting.
  next: use this composite body during the physical OT-2 deck and neighbor-slot
  dress check; replace conservative cable/tube envelopes with measured routing
  only if the physical service-dress gate fails or records tighter clearance.

RS70 bind Gate 3 targets to operating service-dress body
  do: extended `first_print_ot2_placement_targets_markdown()` so Gate 3 now
  records the combined operating service-dress envelope bounds and envelope
  count from the RS69 CAD body. Updated the live first-print record and Gate 3
  protocol text so dressed gas and electrical services are compared against the
  exported `operating_service_dress_check`, not just separate adjacent-slot and
  cable/tube notes.
  review: focused Gate 3/scaffold tests passed with three tests; touched ruff
  passed; the live preflight intentionally exits nonzero while reporting
  `cad_target_sections_match: true`, zero stale CAD target sections, package
  ready true, slicer queue ready true, sliced-output worksheet valid true, and
  only the unchosen printer/material/profile plus no selected passing slicer
  setup row blocking readiness.
  finding: Gate 3 now has a concrete service-dress physical target:
  219.60 x 348.75 x 43.30 mm across 11 gas/electrical service envelopes. The
  printed OT-2 placement check can reject any tube or cable route that cannot
  stay inside the exported validation body without hand-holding.
  next: select the actual printer/material/profile, slice and print only after
  strict print-start readiness, then use the Gate 3 service-dress target during
  physical deck placement and adjacent-slot clearance review.

RS71 add Gate 3 placement worksheet and audit
  do: added `first_print_gate3_placement_targets()`, worksheet CSV helpers, a
  Gate 3 placement worksheet audit, write/audit CLI commands, preflight link
  validation, and live/template/protocol/measurement-record links. The worksheet
  is generated from the same CAD placement targets that include the combined
  operating service-dress body, so physical OT-2 deck placement now has a
  fillable evidence surface instead of only record text.
  review: generated
  `data/measurements/2026-06-02_one_row_coupon_gate3_placement.csv` with eight
  blank `not_tested` rows. The worksheet audit reports `worksheet_valid: true`,
  `gate3_pass_ready: false`, eight expected/actual rows, and zero issues.
  Focused Gate 3/preflight/scaffold/template tests passed with 22 tests; touched
  ruff passed; the live preflight intentionally exits nonzero while reporting
  `gate3_placement_worksheet_valid: true`, `gate3_placement_pass_ready: false`,
  zero missing record links, and zero stale CAD target sections.
  finding: Gate 3 is now machine-checkable without creating a false placement
  pass. Blank setup evidence is valid for preprint plumbing, but every `pass`
  row requires measured values and an evidence path from the real seated,
  dressed assembly.
  next: after printer/material/profile selection, slicing, and printing, dress
  the gas/electrical services on the OT-2 deck and fill the Gate 3 worksheet
  with measurements/photos before any OT-2 placement pass claim.

RS72 add Gate 2 dry assembly worksheet and audit
  do: added `first_print_gate2_dry_assembly_targets()`, worksheet CSV helpers,
  a Gate 2 dry assembly worksheet audit, write/audit CLI commands, preflight
  link validation, and live/template/protocol/measurement-record links. The
  worksheet is generated from the same CAD dry assembly targets as the record,
  covering dry stack order, plate/mat cycling, latch squeeze and self-lock,
  side gas/electrical service dry fit, sensor package dry fit, and dry-bay
  openness.
  review: generated
  `data/measurements/2026-06-02_one_row_coupon_gate2_dry_assembly.csv` with
  thirteen blank `not_tested` rows. The worksheet audit reports
  `worksheet_valid: true`, `gate2_pass_ready: false`, thirteen expected/actual
  rows, and zero issues. Focused Gate 2/preflight/scaffold/template tests
  passed with 23 tests; touched ruff passed; the live preflight intentionally
  exits nonzero while reporting `gate2_dry_assembly_worksheet_valid: true`,
  `gate2_dry_assembly_pass_ready: false`, zero missing record links, and zero
  stale CAD target sections. Full ruff, ASCII scan, physical-gate-pass scan,
  and `git diff --check` passed.
  finding: Gate 2 dry assembly is now machine-checkable without allowing a
  false dry-fit pass. Blank dry-fit evidence is valid for preprint plumbing, but
  every `pass` row requires a measured value or observation plus an evidence
  path from the printed dry assembly.
  next: after print, fill the Gate 2 worksheet with dry stack, latch, service,
  sensor-blank, and dry-bay evidence before wet testing or OT-2 placement.

RS73 add Gate 4 wet/dry witness worksheet and audit
  do: added `first_print_gate4_wet_dry_witness_targets()`, worksheet CSV
  helpers, a Gate 4 wet/dry witness worksheet audit, write/audit CLI commands,
  preflight link validation, and live/template/protocol/measurement-record
  links. The worksheet is generated from the same CAD wet/dry witness targets as
  the record, covering protected dry-bay volume, side-gas service witnesses,
  sample/relief cap witnesses, gasket-tab root witnesses, dry-bay aperture
  thresholds, and aperture-adjacent witness gutters.
  review: generated
  `data/measurements/2026-06-02_one_row_coupon_gate4_wet_dry_witness.csv` with
  six blank `not_tested` rows. The worksheet audit reports `worksheet_valid:
  true`, `gate4_pass_ready: false`, six expected/actual rows, and zero issues.
  Focused Gate 4/preflight/scaffold/template tests passed with 24 tests; ruff
  passed; the live preflight intentionally exits nonzero while reporting
  `gate4_wet_dry_witness_worksheet_valid: true`,
  `gate4_wet_dry_witness_pass_ready: false`, zero missing record links, and
  zero stale CAD target sections. Full ruff, ASCII scan, physical-gate-pass
  scan, and `git diff --check` passed.
  finding: Gate 4 wet/dry protection is now machine-checkable without allowing a
  false leak/witness pass. Blank wet/dry evidence is valid for preprint plumbing,
  but every `pass` row requires a measured value or observation plus an evidence
  path from the printed assembly after dye, condensate, debris, or ingress
  inspection.
  next: after dry assembly and before powered sensors or biology, fill the Gate
  4 worksheet with side-service, sample/relief, gasket-tab, aperture, and
  dry-bay inspection evidence.

RS74 add Gate 5 consumable/puncture worksheet and audit
  do: added `first_print_gate5_consumable_puncture_targets()`, worksheet CSV
  helpers, a Gate 5 consumable/puncture worksheet audit, write/audit CLI
  commands, preflight link validation, and live/template/protocol/measurement
  record links. The worksheet is generated from the same CAD/protocol
  consumable-puncture targets as the record, covering the real plate/mat set,
  plate footprint/support/locator rails, mat stack/plug/slit, all-well
  puncture count, swept diameter/Z range, force limit, repeat cycles, and plate
  shift.
  review: generated
  `data/measurements/2026-06-02_one_row_coupon_gate5_consumable_puncture.csv`
  with thirteen blank `not_tested` rows. The worksheet audit reports
  `worksheet_valid: true`, `gate5_pass_ready: false`, thirteen expected/actual
  rows, and zero issues. Focused Gate 5/preflight/scaffold/template tests
  passed with 25 tests; touched-code and full ruff passed. The live preflight
  and strict print-start preflight intentionally exit nonzero while reporting
  `gate5_consumable_puncture_worksheet_valid: true`,
  `gate5_consumable_puncture_pass_ready: false`, zero missing record links, and
  zero stale CAD target sections. ASCII scan, physical-gate-pass scan, and
  `git diff --check` passed.
  finding: Gate 5 consumable/puncture access is now machine-checkable without
  allowing a false consumable or septum-access pass. Blank rows are valid for
  preprint plumbing, but every `pass` row requires measured values or
  observations plus evidence paths from real plate/mat metrology and puncture
  testing.
  next: after print/dry/wet/OT-2 placement, fill Gate 5 with measured
  plate/mat, puncture force, all-well access, repeat-cycle, and plate-shift
  evidence before treating septum/pipette access as validated.

RS75 add Gate 6 sensor/thermal worksheet and audit
  do: added `first_print_gate6_sensor_thermal_targets()`, worksheet CSV
  helpers, a Gate 6 sensor/thermal worksheet audit, write/audit CLI commands,
  preflight link validation, and live/template/protocol/measurement-record
  links. The worksheet is generated from the same CAD/protocol sensor-thermal
  targets as the record, covering reversible sensor workflow, gas-PCB cartridge
  seating and duct-cell gasket compression, SHT41 carrier exposure, IR gasket
  and FOV proxy, harness routes, service connectors/cables, cable dress, and
  thermal-proxy planning.
  review: generated
  `data/measurements/2026-06-02_one_row_coupon_gate6_sensor_thermal.csv` with
  fourteen blank `not_tested` rows. The worksheet audit reports
  `worksheet_valid: true`, `gate6_pass_ready: false`, fourteen expected/actual
  rows, and zero issues. Focused Gate 6/preflight/scaffold/template tests
  passed with 26 tests; touched-code and full ruff passed. The live preflight
  and strict print-start preflight intentionally exit nonzero while reporting
  `gate6_sensor_thermal_worksheet_valid: true`,
  `gate6_sensor_thermal_pass_ready: false`, zero missing record links, and
  zero stale CAD target sections. ASCII scan, physical-gate-pass scan, and
  `git diff --check` passed.
  finding: Gate 6 sensor/thermal readiness is now machine-checkable without
  allowing false powered-sensor, gas-response, RH-response, IR-calibration, or
  cell-temperature claims. Blank rows are valid for preflight plumbing, but
  every `pass` row requires measured values or observations plus evidence
  paths from sensor/blanks, harness, cable dress, and thermal-proxy planning.
  next: after dry, wet, consumable, and OT-2 placement evidence exists, fill
  Gate 6 with gas-PCB cartridge, SHT41 carrier, IR package/gasket, harness
  continuity, cable-dress, and edge-to-center thermal-plan evidence before
  treating powered sensor or thermal claims as validated.

RS76 add passive leak/wet-dry validation protocol
  do: added
  `docs/protocols/row_coupon_passive_leak_wet_dry_validation.md` and
  `data/measurements/templates/row_coupon_passive_leak_wet_dry_validation.md`.
  The protocol defines Gate 4 dye challenge, condensate challenge, dry-bay
  ingress inspection, witness-gutter/inboard-dam observations, and pass/fail
  boundaries for side gas, sample/relief cap, gasket-tab, aperture-threshold,
  and protected dry-bay evidence. Linked it from the first-print readiness
  protocol, first-print measurement template, live first-print record,
  measurements README, and knowledge index.
  review: focused passive leak protocol/template tests passed with 2 tests;
  touched test lint and full ruff passed. The new template includes all six
  Gate 4 worksheet closure targets as `not_tested` rows and records
  dye/condensate inspections without marking Gate 4 passed. The live preflight
  intentionally exits nonzero only for the selected-slicer/profile blockers,
  while reporting zero missing record links, zero stale CAD target sections,
  and `gate4_wet_dry_witness_pass_ready: false`. ASCII scan,
  physical-gate-pass scan, and `git diff --check` passed.
  finding: Gate 4 now has a physical wet/dry evidence protocol, not only a
  worksheet and CAD target block. Passive leak and dry-bay protection still
  remain unproven until dye, condensate, and post-test dry inspections produce
  evidence paths.
  next: after Gate 1-3 physical evidence exists, run the passive leak/wet-dry
  protocol, fill the Gate 4 worksheet from its evidence, and revise CAD only if
  real wetting bridges a witness, dam, threshold, dry-bay boundary, sensor
  pocket, harness channel, or connector shroud.

RS77 select audited PrusaSlicer setup and restore preprint readiness
  do: selected the complete active PrusaSlicer setup row using the selector,
  which atomically marked row 0 selected/pass and wrote the selected setup
  summary into live Printer / material / profile. Regenerated the sliced-output
  worksheet with the same selected setup summary while keeping all output paths
  and hashes blank and rows `not_tested`.
  review: the slicer setup selector reported `worksheet_valid: true` and
  `setup_selected: true`. The sliced-output audit reports
  `worksheet_valid: true`, `sliced_outputs_ready: false`, `queue_ready: true`,
  expected setup summary
  `PrusaSlicer / Original Prusa MK4 Input Shaper 0.4 nozzle / Generic PETG @PGIS / 0.20mm STRUCTURAL @MK4IS 0.4`,
  12 expected/actual rows, and zero issues. Normal live preflight exits 0 with
  `preprint_ready: true`, `print_start_ready: false`, zero issues, zero
  physical gate passes, zero missing links, zero stale CAD target sections, and
  all Gate 1-6 worksheet/pass-ready booleans valid/false. Strict print-start
  preflight still exits nonzero because `sliced_outputs_ready: false`.
  finding: preprint readiness is now unblocked without claiming print start or
  physical evidence. The next blocker is actual sliced files, hashes, and
  passing sliced-output rows.
  next: slice the audited 12-STL queue with the selected PrusaSlicer setup,
  fill sliced-output paths and hashes, then rerun the sliced-output audit with
  `--require-ready` and strict preflight before printing.

RS78 add selected-printer bed-fit gate
  do: added a first-print slicer bed-fit audit to the composed preflight. The
  audit reads the selected setup row, resolves `bed_shape` from the recorded
  profile source and inherited vendor profiles, then compares the selected bed
  against every printed queue target with arbitrary XY rotation. The test
  fixture now records an explicit 500 x 500 mm bed, regression tests reject a
  250 x 210 mm selected bed, and the geometric unit test covers a thin long
  rectangle that only fits when diagonally rotated.
  review: focused first-print tests passed with 101 tests before the resolver
  correction and the targeted bed-fit/preflight subset passed with 5 tests after
  it. `uv run ruff check .` passed. The live preflight now exits nonzero with
  `preprint_ready: false`, `slicer_bed_fit_ready: false`, selected MK4 bed
  250.00 x 210.00 mm, and 9 oversized printed queue parts: `deck_pods`,
  `plate_support_frame`, `lower_harness_cover`, `wet_chamber_frame`,
  `lid_manifold_shell`, `lid_harness_cover`, `lid_cover`,
  `printed_gas_pcb_keeper_doors`, and `printed_wedge_locks`.
  finding: RS77's selected setup is locally valid but not print-feasible for
  the current one-row production queue. Preprint readiness is correctly blocked
  before slicing, with zero physical gate passes and no stale CAD target
  sections.
  next: either select a proven printer with a bed that fits the current 377.25
  mm queue parts, or redesign the printed production split with explicit
  print-native retention, serviceability, sealing, and OT-2 fit evidence before
  regenerating the queue.

RS79 refine bed-fit audit for arbitrary XY rotation
  do: replaced the initial normal/90-degree bed-fit check with an analytic
  arbitrary-rotation interval check for rectangular part bounds. Added a
  focused geometry regression where a thin long rectangle fits only when
  diagonally rotated, plus the current 377.25 mm row-scale part still failing a
  360 x 360 mm bed.
  review: the focused bed-fit/preflight subset passed with 4 tests and
  `uv run ruff check .` passed. Normal and strict live preflight both still
  exit nonzero with `preprint_ready: false`, `slicer_bed_fit_ready: false`,
  selected MK4 bed 250.00 x 210.00 mm, and the same 9 oversized printed queue
  parts.
  finding: the selected MK4 blocker is not an artifact of checking only 0/90
  degree orientations. Future larger-printer selection and split decisions now
  use the actual rectangular XY rotation feasibility rule.
  next: resolve bed fit by selecting a proven printer that fits the row-scale
  queue under arbitrary XY rotation, or split the printed production bodies with
  explicit print-native retention, sealing, serviceability, and OT-2 fit
  evidence before regenerating and slicing the queue.

RS80 add selected-bed split-plan worksheet
  do: added a generated first-print bed-fit split-plan worksheet plus audit and
  CLI scripts. The worksheet derives each printed queue part from the current
  CAD package and selected slicer bed, records whether it fits as exported, and
  computes the minimum Y-axis segment count that would fit the selected bed.
  The scaffold/template/live record now link the worksheet as a decision
  artifact before sliced outputs.
  review: generated
  `data/measurements/2026-06-02_one_row_coupon_bed_fit_split_plan.csv`.
  Its audit reports `worksheet_valid: true`, `split_plan_ready: false`, 12
  expected/actual rows, 9 split-required parts, and zero issues. For the
  selected MK4 bed, every oversized queue part has `minimum_y_segments: 2` and
  `segment_fits_selected_bed: yes`, while the three small parts fit as
  exported. Focused scaffold/template/split-plan tests passed with 4 tests and
  `uv run ruff check .` passed.
  finding: the MK4 path now has a concrete production split decision table:
  two Y segments are enough geometrically, but no row may be marked ready until
  real split CAD/STLs carry print-native retention, serviceability, sealing,
  and OT-2 fit evidence.
  next: implement split production CAD for the 9 oversized printed bodies or
  select a proven larger printer. If splitting, start with the row-scale
  sealing/latching bodies (`plate_support_frame`, `wet_chamber_frame`,
  `lid_manifold_shell`, `lid_cover`, and `printed_wedge_locks`) and keep split
  interfaces away from gasket tabs, sensor pockets, gas PCB seals, and pipette
  access windows.

RS81 add generated production Y-split CAD artifacts
  do: added explicit first-print production Y-split configuration to
  `cad/one_row_coupon.params.json`, CAD helpers that clip the 9 oversized
  printed bodies into two inter-plate-gap Y segments, and
  `export_row_coupon_production_y_split_parts()`. `scripts/generate_row_coupon.py`
  now exports those split bodies under `outputs/cad/first_print_y_split_parts/`.
  Added `audit_first_print_y_split_artifacts()` plus
  `scripts/audit_row_coupon_first_print_y_split_artifacts.py` so the split STEP/STL
  set is checked against the selected slicer bed before it can be considered for
  queue replacement.
  review: regenerated CAD outputs. The split directory now contains 36 files:
  18 split bodies, each with STL and STEP. The live split-artifact audit reports
  `split_artifacts_ready: true`, selected MK4 bed 250.00 x 210.00 mm, 18
  expected/actual rows, 9 split source parts, all 9 selected-bed oversized source
  parts covered, zero missing oversized parts, and zero issues. The monolithic
  slicer queue still audits ready with 12 printed STLs and zero hash mismatches.
  Focused production split CAD tests passed with 3 tests; focused first-print
  bed-fit/split-artifact tests passed with 5 tests; touched-code ruff passed.
  finding: the selected MK4 path now has real generated split STEP/STL artifacts
  that fit the selected bed, but they are not yet the active slicer queue.
  Preflight must continue to block on the monolithic 12-STL queue until a split
  queue replacement is explicitly implemented, audited, sliced, and then tied to
  Gate 1, Gate 2, and Gate 4 physical evidence.
  next: implement a split-artifact slicer queue/manifest and sliced-output
  worksheet path, or keep the monolithic queue and select a larger proven printer.
  Do not mark print-start ready until the active queue, sliced outputs, and
  physical evidence all refer to the same artifact set.

RS82 add split-artifact slicer queue handoff
  do: added an explicit first-print production Y-split slicer queue path, queue
  manifest/audit, split sliced-output worksheet generator/audit, CLI scripts,
  scaffold/template links, live record evidence, and protocol/measurement docs.
  The split queue replaces the 9 oversized monolithic printed STLs with 18
  selected-bed-fit split segment STLs while retaining the 3 small monolithic
  printed STLs that already fit.
  review: generated `outputs/cad/first_print_y_split_slicer_queue/` and
  `data/measurements/2026-06-02_one_row_coupon_y_split_sliced_outputs.csv`.
  The live split queue audit reports `ready: true`, 21 expected/actual printed
  STLs, zero source issues, zero missing files, zero extras, and zero hash
  mismatches. The split sliced-output audit reports `worksheet_valid: true`,
  `sliced_outputs_ready: false`, `queue_ready: true`, 21 expected/actual rows,
  and zero issues. Focused split queue/sliced-output tests passed with 3 tests;
  touched-code ruff passed.
  finding: the MK4 split print handoff is now machine-checkable through queue
  preparation, queue audit, blank sliced-output rows, and sliced-output audit,
  but it is not yet the active preflight queue. Preflight should continue to
  block on the monolithic queue until split Gate 1 QC targets and preflight
  linkage intentionally refer to the same split artifact set.
  next: bind preflight to the split queue only after the split Gate 1 QC target
  surface exists, or add an explicit queue mode/record linkage that keeps active
  queue, sliced outputs, and physical Gate 1 evidence mutually consistent.

RS83 add split Gate 1 QC target surface
  do: added split-artifact Gate 1 QC worksheet generation and audit, including
  CLI scripts, scaffold/template links, protocol/measurement docs, focused
  tests, and live record evidence. The split worksheet is derived from the same
  21-item split queue target surface: 18 selected-bed-fit split segment STLs
  plus the 3 small monolithic printed STLs.
  review: generated
  `data/measurements/2026-06-02_one_row_coupon_y_split_gate1_qc.csv`. The live
  split Gate 1 audit reports `worksheet_valid: true`, `gate1_pass_ready:
  false`, 21 expected/actual rows, 21 `not_tested` rows, and zero issues.
  Focused split Gate 1/scaffold tests passed with 4 tests; full ruff passed.
  finding: the alternate MK4 split path now has consistent split queue, split
  sliced-output, and split Gate 1 target evidence, but it is still not the
  active preflight print path. Preflight must remain blocked on the monolithic
  queue until the active record links and preflight checks intentionally point
  to the split artifact set and physical Gate 1 measurements exist.
  next: add an explicit active queue mode or switch the record/preflight
  authority to the audited split queue, split sliced outputs, and split Gate 1
  worksheet together; do not mix monolithic and split evidence for print start.

RS84 make split-Y the active preflight queue mode
  do: added an explicit `Active print queue mode` session field with
  `monolithic` and `split_y` modes. Split-Y preflight now audits the split
  slicer queue, split sliced-output worksheet, split Gate 1 QC worksheet, and
  selected-bed split artifacts together instead of mixing monolithic and split
  evidence. The scaffold defaults to `monolithic`; the live first-print record
  is set to `split_y`.
  review: focused preflight tests passed with 3 tests, including the small-bed
  split-mode case. Regenerated the live split sliced-output worksheet with the
  default absolute split queue path, reran recorded split sliced-output and
  split Gate 1 write/audit commands, and reran live preflight. The live preflight
  now reports `active_queue_mode: split_y`, `preprint_ready: true`,
  `print_start_ready: false`, `slicer_bed_fit_ready: true`, selected MK4 bed
  250.00 x 210.00 mm, zero oversized active split queue parts,
  `sliced_outputs_valid: true`, `sliced_outputs_ready: false`, all Gate 1-6
  worksheets valid/pass-ready false, zero physical gate passes, zero missing
  links, zero stale CAD target sections, and zero issues.
  finding: the MK4 bed-fit blocker is resolved for preprint readiness only when
  the active queue mode is explicitly `split_y`. Print start remains blocked
  until 21 split sliced output files and hashes are entered and physical Gate 1
  measurements are collected.
  next: slice the 21 active split queue STLs with the selected PrusaSlicer setup,
  enter sliced output paths/hashes, then collect physical Gate 1 dimensions
  against the split Gate 1 worksheet before any print-start or physical pass
  claim.

RS85 slice active split-Y queue to print-start readiness
  do: added manifest-backed split queue audit, split sliced-output expected rows,
  and split Gate 1 expected rows so post-queue audits and split-mode preflight
  use the prepared slicer queue manifest instead of rebuilding split CAD
  geometry repeatedly. Added batch split queue slicing through the selected
  PrusaSlicer setup and recorded the real 21-file G-code handoff.
  review: live batch slicing wrote 21 G-code files under
  `outputs/sliced/first_print_y_split` and rewrote
  `data/measurements/2026-06-02_one_row_coupon_y_split_sliced_outputs.csv` with
  pass rows and hashes. The live split sliced-output audit reports
  `worksheet_valid: true`, `sliced_outputs_ready: true`, `queue_ready: true`, 21
  expected/actual rows, and zero issues. Strict live preflight now reports
  `active_queue_mode: split_y`, `preprint_ready: true`,
  `print_start_ready: true`, split bed 250.00 x 210.00 mm, zero oversized active split queue parts,
  all Gate 1-6 worksheets valid/pass-ready false, zero physical gate passes,
  zero missing links, zero stale CAD target sections, and zero issues. Full ruff
  passed; focused batch-slicing, split preflight, and split queue manifest tests
  passed individually.
  finding: the selected MK4 split queue is now machine-ready to start a print
  from the 21 generated G-code files, but no physical print, dimensional QC,
  dry assembly, wet/dry witness, consumable puncture, sensor/thermal, or install
  inventory evidence has been collected. Gate 1-6 pass states must remain false.
  next: print the 21 active split queue files, collect Gate 1 dimensions against
  the split Gate 1 QC worksheet, and keep every downstream gate blocked until
  measured physical evidence is entered.

RS86 add split print batch traveler handoff
  do: added a split-Y print batch traveler worksheet, generator, audit, CLI
  scripts, scaffold/template link, live record link, protocol docs, and focused
  tests. The traveler is generated from the audited split sliced-output
  worksheet and split Gate 1 QC worksheet, binding print order, queued STL
  hashes, G-code paths/hashes, selected setup, current Gate 1 result, and a
  separate physical print status for each active split queue part.
  review: generated
  `data/measurements/2026-06-02_one_row_coupon_y_split_print_batch_traveler.csv`.
  The live traveler audit reports `worksheet_valid: true`, `handoff_ready:
  true`, `sliced_outputs_ready: true`, `gate1_qc_worksheet_valid: true`, 21
  expected/actual rows, 21 `not_printed` rows, and zero issues. Focused
  traveler/scaffold tests passed with 2 tests; ruff passed before final docs and
  record trace updates.
  finding: the 21-file MK4 split print handoff is now machine-checkable and
  physically traceable without turning any physical gate green. The prototype
  remains unprinted; Gate 1-6 pass states must stay false until measured
  evidence is entered.
  next: run the physical 21-file print batch, update traveler rows from
  `not_printed` to printed/failed as appropriate, then collect Gate 1 dimensions
  against the split Gate 1 QC worksheet.

RS87 expose OT-2 toolhead envelope in Gate 3 readiness
  do: extended the generated Gate 3 OT-2 placement targets and worksheet with
  two explicit conservative toolhead checks: the larger validation-only OT-2
  toolhead swept-body envelope and the lower-clearance stack above the printed
  assembly, dressed services, and tip path. Updated focused tests, live Gate 3
  worksheet, live target section, and protocol/measurement docs so tip puncture
  access cannot be mistaken for full toolhead clearance.
  review: regenerated
  `data/measurements/2026-06-02_one_row_coupon_gate3_placement.csv` with 10
  blank `not_tested` rows. The Gate 3 audit reports `worksheet_valid: true`,
  `gate3_pass_ready: false`, 10 expected/actual rows, 10 `not_tested` rows, and
  zero issues.
  finding: Gate 3 now carries both the 384-well tip access check and the
  conservative 250.00 x 445.50 x 45.00 mm two-pipette OT-2 toolhead clearance
  check. The conservative CAD envelope remains a validation target only and must
  not be replaced until measured OT-2 lower-body/service-dress evidence exists.
  next: after the split print batch and Gate 1 dimensions, use the Gate 3
  worksheet to collect seated-deck, service-dress, and measured toolhead
  clearance evidence before any OT-2 placement or no-motion clearance pass.

RS88 bind split Gate 1 QC to printed traveler rows
  do: added a combined split-Y Gate 1 print-QC audit and CLI command that checks
  the split Gate 1 dimensional worksheet against the split print batch traveler
  and ready sliced-output worksheet. The combined audit keeps the worksheet
  audit separate from the physical print/QC claim: dimensions can be internally
  valid, but `print_qc_ready` requires every matching traveler row to be
  `printed` and every Gate 1 row to pass.
  review: the live combined audit reports `print_qc_ready: false`,
  `gate1_qc_worksheet_valid: true`, `gate1_pass_ready: false`,
  `print_batch_handoff_ready: true`, 21 expected rows, 0 printed rows, 21
  unprinted parts, and zero issues. Focused tiny split handoff tests passed and
  prove a Gate 1 pass row is rejected when the traveler row is still
  `not_printed`.
  finding: Gate 1 can no longer become a machine-accepted physical print-QC
  claim from measurements alone. The physical print batch must update traveler
  rows to `printed` before the split Gate 1 pass can be accepted.
  next: run the physical 21-file print batch, update traveler print results,
  collect split Gate 1 dimensions, then rerun the combined audit with
  `--require-print-qc-ready`.

RS89 bind Gate 2 dry assembly to print QC and installed inventory
  do: added a combined split-Y Gate 2 dry-assembly readiness audit and CLI
  command that checks the Gate 2 dry-assembly worksheet against split Gate 1
  print-QC readiness and the nonprinted installed-item inventory. The audit lets
  a blank Gate 2 worksheet remain valid, but rejects any Gate 2 pass claim until
  the split print batch/Gate 1 chain and install inventory are ready.
  review: the live combined audit reports `dry_assembly_ready: false`,
  `gate2_dry_assembly_worksheet_valid: true`,
  `gate2_dry_assembly_pass_ready: false`, 0 Gate 2 pass rows,
  `gate1_print_qc_ready: false`, `install_inventory_valid: true`,
  `install_inventory_ready: false`, and zero issues. Focused tests cover
  valid-blank, false Gate 2 pass with missing upstream evidence, and fully ready
  states.
  finding: Gate 2 can no longer become a machine-accepted dry-assembly claim
  from its worksheet alone. Printed-part QC and nonprinted installed-item
  evidence must both be ready before dry assembly can pass.
  next: run the physical split print batch, collect Gate 1 dimensions, identify
  installed consumables/services/packages or blanks, then rerun the combined
  Gate 2 audit with `--require-dry-assembly-ready`.

RS90 bind Gate 3 OT-2 placement to dry assembly readiness
  do: added a combined split-Y Gate 3 placement-readiness audit and CLI command
  that checks the Gate 3 OT-2 placement worksheet against the combined Gate 2
  dry-assembly readiness chain. The audit leaves a blank Gate 3 worksheet valid
  but rejects any Gate 3 pass claim until Gate 2 dry assembly is ready.
  review: the live combined audit reports `placement_ready: false`,
  `gate3_placement_worksheet_valid: true`,
  `gate3_placement_pass_ready: false`, 0 Gate 3 pass rows,
  `gate2_dry_assembly_ready: false`,
  `gate2_dry_assembly_worksheet_valid: true`,
  `gate2_dry_assembly_pass_ready: false`, and zero issues. Focused tests cover
  valid-blank, false Gate 3 pass with missing Gate 2 readiness, and fully ready
  states.
  finding: Gate 3 can no longer become a machine-accepted OT-2 placement claim
  from its worksheet alone. The dry assembled printed/cabled/service state must
  pass first.
  next: after Gate 2 dry assembly is physically evidenced, collect seated-deck,
  service-dress, tip access, and measured toolhead-clearance evidence, then run
  the combined Gate 3 audit with `--require-placement-ready`.

RS91 bind Gate 4 wet/dry witness to placement readiness
  do: added a combined split-Y Gate 4 wet/dry witness readiness audit and CLI
  command that checks the Gate 4 witness worksheet against the combined Gate 3
  placement readiness chain. The audit leaves a blank Gate 4 worksheet valid,
  but rejects any Gate 4 pass claim until Gate 3 placement is ready.
  review: the live combined audit reports `wet_dry_witness_ready: false`,
  `gate4_wet_dry_witness_worksheet_valid: true`,
  `gate4_wet_dry_witness_pass_ready: false`, 0 Gate 4 pass rows,
  `gate3_placement_ready: false`, `gate3_placement_worksheet_valid: true`,
  `gate3_placement_pass_ready: false`, and zero issues. Focused tests cover
  valid-blank, false Gate 4 pass with missing Gate 3 readiness, and fully ready
  states.
  finding: Gate 4 can no longer become a machine-accepted production wet/dry
  isolation claim from its worksheet alone. The assembled/seated/service-dressed
  OT-2 placement state must be ready first.
  next: after Gate 3 placement is physically evidenced, collect leak collector,
  witness gutter, dry-bay threshold, and condensate path evidence, then run the
  combined Gate 4 audit with `--require-wet-dry-witness-ready`.

RS92 bind Gate 5 consumable/puncture to wet/dry readiness
  do: added a combined split-Y Gate 5 consumable/puncture readiness audit and
  CLI command that checks the Gate 5 worksheet against the combined Gate 4
  wet/dry witness readiness chain. The audit leaves a blank Gate 5 worksheet
  valid, but rejects any Gate 5 pass claim until Gate 4 wet/dry witness is
  ready.
  review: the live combined audit reports `consumable_puncture_ready: false`,
  `gate5_consumable_puncture_worksheet_valid: true`,
  `gate5_consumable_puncture_pass_ready: false`, 0 Gate 5 pass rows,
  `gate4_wet_dry_witness_ready: false`,
  `gate4_wet_dry_witness_worksheet_valid: true`,
  `gate4_wet_dry_witness_pass_ready: false`, and zero issues. Focused tests
  cover valid-blank, false Gate 5 pass with missing Gate 4 readiness, and fully
  ready states.
  finding: Gate 5 can no longer become a machine-accepted production puncture
  or consumable-compatibility claim from its worksheet alone. Wet/dry isolation
  evidence must pass first.
  next: after Gate 4 wet/dry evidence is collected, enter real plate/mat
  metrology, all-well puncture access, puncture-force, repeat-cycle, and
  plate-shift evidence, then run the combined Gate 5 audit with
  `--require-consumable-puncture-ready`.

RS93 bind Gate 6 sensor/thermal to consumable readiness
  do: added a combined split-Y Gate 6 sensor/thermal readiness audit and CLI
  command that checks the Gate 6 worksheet against the combined Gate 5
  consumable/puncture readiness chain. The audit leaves a blank Gate 6 worksheet
  valid, but rejects any Gate 6 pass claim until Gate 5 consumable/puncture is
  ready.
  review: the live combined audit reports `sensor_thermal_ready: false`,
  `gate6_sensor_thermal_worksheet_valid: true`,
  `gate6_sensor_thermal_pass_ready: false`, 0 Gate 6 pass rows,
  `gate5_consumable_puncture_ready: false`,
  `gate5_consumable_puncture_worksheet_valid: true`,
  `gate5_consumable_puncture_pass_ready: false`, and zero issues. Focused
  tests cover valid-blank, false Gate 6 pass with missing Gate 5 readiness, and
  fully ready states.
  finding: Gate 6 can no longer become a machine-accepted production sensor,
  gas-response, harness, cable-dress, or thermal-proxy claim from its worksheet
  alone. Consumable/puncture evidence must pass first.
  next: after Gate 5 consumable/puncture evidence is collected, enter sensor
  package or blank installation, gas-PCB sealing, SHT41 carrier exposure, IR
  gasket/FOV, harness continuity, cable dress, and thermal-proxy plan evidence,
  then run the combined Gate 6 audit with `--require-sensor-thermal-ready`.

RS94 add top-level operating prototype acceptance audit
  do: added a split-Y operating-prototype acceptance audit and CLI command that
  composes strict print-start artifact readiness with the full Gate 1-6 physical
  evidence chain. The audit can report print start ready while still refusing a
  production-operating prototype claim.
  review: the live audit reports `operating_prototype_ready: false`,
  `preflight_artifacts_ready: true`, `print_start_ready: true`,
  `sensor_thermal_ready: false`, `gate6_sensor_thermal_worksheet_valid: true`,
  `gate6_sensor_thermal_pass_ready: false`, 0 Gate 6 pass rows, 0 physical gate
  passes, and zero issues. Focused tests cover not-ready and fully-ready paths.
  finding: print-start readiness is no longer confusable with
  production-operating acceptance; the final prototype claim requires the
  terminal Gate 6 readiness chain.
  next: run the physical split print batch, Gate 1 print QC, install inventory,
  and Gates 2-6 evidence collection before rerunning the acceptance audit with
  `--require-operating-prototype-ready`.

RS95 add unmated electrical connector review state
  do: added an opt-in `electrical_connectors_unmated` service/review mode. The
  default installed state still shows the normal connected JST-GH-shaped
  service connectors and cable pigtails, while the review mode removes the
  installed connector/cable parts and replaces them with stationary
  board/header geometry, pulled-back plug/latch/cable geometry, and mating-gap
  witnesses at the printed shrouds.
  review: focused CAD tests prove the mode is opt-in, removes only lower/lid
  electrical connector and cable-pigtail parts, keeps printed shrouds, harness
  covers, lid, and lower frame in operating position, and creates one board,
  header, pulled plug, latch, cable, and witness rectangle for each of the three
  service connectors.
  finding: the production-operating electrical service claim is now reviewable
  as connected, missing, or visibly unmated. A connector-shaped printed shroud
  can no longer imply that the row's lower IR or lid sensor bus is electrically
  connected.
  next: after selecting the actual cable assemblies, replace the straight
  pigtail approximations with measured dressed cable routing and add reversed
  or unlatched review states only if those failure modes are not visually
  obvious from the chosen keyed connector family.

RS96 export electrical connector mating-state validation body
  do: promoted the unmated electrical connector geometry into a required
  validation-only export named `electrical_connector_mating_state_check`. The
  body is derived from the same stationary board/header, pulled-back
  plug/latch/cable, and mating-gap witness rectangles used by the opt-in review
  mode, but it remains out of the installed production tree.
  review: focused CAD tests prove the validation builder and export list include
  the new body, that it is absent from installed parts, and that its bounds
  match the unmated connector review geometry. Regenerated CAD outputs include
  `aevum_one_row_coupon_validation_electrical_connector_mating_state_check`
  STEP/STL, the package audit reports ready true with 12 required validation
  bodies, the validation viewer smoke shows the new body, and strict live
  preflight is back to `print_start_ready: true` with matching generated
  timestamp and zero issues.
  finding: electrical service connectedness now has both an interactive review
  state and a generated STEP/STL validation artifact. The package handoff can
  no longer prove service-cable clearance while omitting the mated/unmated
  connector-state surface.
  next: use the exported mating-state check during dry assembly and Gate 6
  sensor/harness evidence collection; replace straight pigtail approximations
  only after measured cable dress data exists.

RS97 export and require aperture wet/dry failure-path body
  do: added `wet_dry_failure_path_check` to the validation exporter and to the
  first-print required validation list. This uses the existing aperture-local
  witness-gutter geometry already present in the validation part map and Gate 4
  worksheet targets, but turns it into an actual STEP/STL handoff artifact.
  review: focused tests now assert the exporter produces the
  `aevum_one_row_coupon_validation_wet_dry_failure_path_check` STEP/STL names
  and that the first-print required validation list includes the body.
  Regenerated CAD outputs now include the wet/dry failure-path validation
  STEP/STL, the package audit reports ready true with 13 required validation
  bodies, strict live preflight is back to `print_start_ready: true` with the
  regenerated timestamp matched, and operating acceptance remains
  `operating_prototype_ready: false` with zero physical gate passes. This is a
  package-contract change only; it does not mark Gate 4 pass-ready and still
  requires dye, condensate, debris, and ingress evidence before wet/dry
  isolation can pass.
  finding: Gate 4 wet/dry witness evidence can no longer depend on hidden CAD
  layout data while the required package omits the aperture gutter body. The
  protected dry-bay ingress overlay and the aperture-local failure-path check
  are now both first-print validation handoff surfaces.
  next: use the exported wet/dry failure-path body alongside
  `dry_bay_ingress_audit_check` during Gate 4 evidence collection; revise CAD
  only if dye, condensate, debris, or ingress observations contradict the
  witness geometry.

RS98 expose no-metal/no-glue retention policy in package contract
  do: expanded `row_coupon_part_manifest()` with structured allowed installed
  fabrication sources, allowed nonprinted exceptions, and forbidden retention
  authority terms for metal inserts, metal fasteners, threaded inserts,
  adhesive bonds, solvent welds, thermal stakes, permanent welds, hidden bonded
  authority, and springs. The first-print package manifest now prints those
  policy rows next to the artifact counts.
  review: tests now check that every installed manifest entry uses an allowed
  fabrication source, that nonprinted installed items are explicit exceptions,
  and that retention strings do not contain forbidden authority terms. The
  package-manifest test verifies the no-metal/no-glue policy is visible in the
  handoff rather than only described in prose. Rewrote the first-print package
  manifest, confirmed the policy rows appear in the generated handoff, reran
  package audit ready true with 13 required validation bodies, and reran strict
  live preflight with `print_start_ready: true`, matched generated timestamp,
  and zero issues. Operating acceptance remains `operating_prototype_ready:
  false` with zero physical gate passes.
  finding: the print-native rule is now a machine-checked package contract.
  Future attempts to make a visible installed part depend on hidden metal,
  glue, permanent bonding, or spring authority must either fail tests or become
  an explicit policy exception.
  next: keep any future metal, glue, permanent-bond, or spring proposal as a
  manifest/test-visible exception, not an implicit rescue during print QC.

RS99 classify installed material/exposure surfaces in the handoff
  do: added a material/exposure classification to every installed manifest
  entry: exposure class, service disposition, and the physical evidence gate
  that must eventually prove the surface handling claim. The manifest now
  raises if a new installed part lacks this classification, and the
  first-print package manifest prints an `Operating Material And Exposure
  Policy` table for all installed parts.
  review: focused tests require allowed exposure classes and dispositions for
  every installed part, check representative wet-headspace, wet-consumable, and
  dry-electrical-service entries, and verify those rows appear in the generated
  package handoff. The hypergraph now records that RH14 has a CAD classification
  contract while BSL1 material, cleaning, leachable, odor, contamination, and
  survival evidence remain blocked until physical testing. Regenerated the
  first-print package manifest, confirmed representative material/exposure
  rows in the generated handoff, reran package audit ready true with 13
  required validation bodies, and reran strict live preflight with
  `print_start_ready: true`, matched generated timestamp, and zero issues.
  Operating acceptance remains `operating_prototype_ready: false` with zero
  physical gate passes.
  finding: production operating surfaces are no longer only implicit in part
  names or prose. The package now tells a builder which installed surfaces are
  wet-headspace boundaries, consumables, gas sample paths, dry sensor packages,
  dry service regions, or latch/exterior surfaces before any material or
  cleaning claim can be marked pass-ready.
  next: use the material/exposure table during Gate 4, Gate 5, and Gate 6
  evidence collection; do not mark RH14 biology/material claims pass-ready until
  real cleaning, leachable, odor, contamination, and survival evidence exists.

RS100 export observer fiducial/focus target validation body
  do: added `observer_fiducial_focus_target_check`, a validation-only body
  derived from the same bottom recess, objective keepout, crosshair, and
  underside observer-fiducial parameters cut into the plate-support frame. The
  artifact records eight target features per plate position: the bottom recess,
  objective keepout disk, horizontal and vertical focus crosshairs, and four
  local fiducial disks. It is now part of the first-print required validation
  set.
  review: focused tests verify the target metadata count and kinds, prove the
  body stays out of installed production parts, and prove validation export and
  first-print required-artifact lists include the new STEP/STL names, and the
  full CAD plus first-print regression files passed 188 tests with 7 warnings.
  Regenerated CAD/package outputs, wrote the package manifest with 14 required
  validation bodies, updated the live generated-output timestamp, reran package
  audit ready true, reran strict preflight with `print_start_ready: true` and
  zero issues, and smoked the validation viewer with the observer target body
  present at 106.00 x 341.50 x 1.00 mm. Operating acceptance remains false with
  zero physical gate passes. This remains a geometric target-location check only;
  optical contrast, focus repeatability, vibration, thermal drift, and usable
  imaging/Raman signal quality still require physical evidence.
  finding: RH15 now has a generated local fiducial/focus target surface in the
  handoff instead of relying only on broad observer swept volumes and hidden
  support-frame cuts. Builders can inspect the observer target pattern before
  any optical-quality claim is made.
  next: use the observer target body during underside fiducial/focus evidence
  collection, and keep RH15 optical-performance claims blocked until measured
  contrast, focus, drift, vibration, and signal-quality evidence exists.

RS101 export assembly-state witness validation body
  do: added `assembly_state_witness_check`, a validation-only body that unions
  the existing negative-state witnesses for missing microplates, missing septum
  mats, missing perimeter gaskets, missing gas PCB cartridges, missing service
  leads, a missing sample/relief cap, and unseated latch bearing flats. It is
  now part of the first-print required validation set without adding any default
  installed production geometry.
  review: focused tests prove the body is validation-only, encloses the witness
  geometry from every negative review mode, exports with the expected STEP/STL
  names, and appears in the first-print required-artifact list. Regenerated
  CAD/package outputs, wrote the package manifest with 15 required validation
  bodies, updated the live generated-output timestamp, reran package audit ready
  true, and smoked the validation viewer with the assembly-state witness body
  present at 163.60 x 383.25 x 61.70 mm. This remains a geometric witness check
  only; operator inspection, print QC, dry assembly cycling, and fail-closed
  behavior remain physical Gate 1-6 evidence.
  finding: RH17 now has a package-level witness body tying the scattered
  negative service modes into one first-print artifact. The default installed
  state stays normal operation, while missing or unseated states are explicit
  review/validation geometry.
  next: use the assembly-state witness body during Gate 1 print QC and Gate 2
  dry assembly review, and keep fail-closed operating claims blocked until real
  inspection, cycling, and operator-error evidence exists.

RS102 export gasket-compression gap gauge
  do: added `gasket_compression_gap_gauge`, a validation-only printable gauge
  derived from the current production latch compression budget. The gauge
  exports three separate reference blades for minimum, target, and maximum
  gasket squeeze, stays outside the default installed production tree, and is
  now part of the first-print required validation set.
  review: focused tests prove the blade thicknesses match the latch compression
  budget, prove the gauge is validation-only, and prove validation export and
  first-print required-artifact lists include the new STEP/STL names.
  Regenerated CAD/package outputs, rewrote the package manifest with 16 required
  validation bodies, reran package audit ready true, and smoked the validation
  viewer with the gauge body present at 36.00 x 19.00 x 0.80 mm. This remains a
  reference gauge only; real gasket compression, latch force, and dry assembly
  survivability remain physical Gate 2 evidence.
  finding: RH17 now has a concrete first-print gap-reference artifact for
  gasket/latch compression instead of only a symbolic CAD squeeze budget.
  next: print/use the gauge during Gate 2 dry assembly, record measured
  compression or revise the latch/gasket stack, and keep fail-closed operating
  claims blocked until physical latch cycling and compression evidence exists.

RS103 export thermal/condensation proxy map
  do: added `thermal_condensation_proxy_check`, a validation-only Gate 6 body
  driven by layout metadata for the four plate-center cell-plane references,
  four plate-margin IR proxy spots, four SHT41 headspace aperture/drip-ring
  points, and four wet-chamber condensation low-point pockets. The body is now
  exported, required in the first-print validation set, visible in the viewer,
  and reflected in the Gate 6 sensor/thermal worksheet row.
  review: focused tests prove the target metadata traces to plate grid centers,
  IR mounts, SHT41 mounts, and the same condensation-pocket geometry cut into
  the wet chamber. Regenerated CAD/package outputs, rewrote the package
  manifest with 17 required validation bodies, regenerated the Gate 6 worksheet,
  reran package and Gate 6 audits, and smoked the validation viewer with
  `thermal_condensation_proxy_check` present at 145.60 x 370.85 x 17.05 mm.
  This remains a measurement map only; thermal authority, RH/CO2 recovery,
  evaporation, edge-effect, and condensation behavior still require physical
  Gate 6 evidence.
  finding: RH12 no longer relies on prose-only thermal proxy planning. The
  package has a generated body and worksheet value that tell the builder where
  to correlate center biology-plane references, edge IR readings, local
  headspace readings, and condensate low points before any incubation claim is
  accepted.
  next: use the proxy map during Gate 6 evidence collection, and revise heater,
  lid/rim warming, or condensation features only from measured recovery,
  evaporation, or pooling failures.

RS104 require Gate 4 leak-hierarchy witness bodies
  do: promoted `side_gas_leak_witness_check`,
  `sample_relief_leak_witness_check`, and `gasket_tab_leak_witness_check` from
  exported-but-not-required validation bodies into the first-print required
  validation set. These are the exact bodies behind the Gate 4 side-gas,
  sample/relief-cap, and gasket-tab wet/dry witness worksheet rows, so the
  handoff can no longer omit them while still asking for physical dye evidence.
  review: focused tests verify the required validation list, package-manifest
  count, Gate 4 worksheet targets, and validation export names. Rewrote the
  package manifest with 20 required validation bodies; package audit reports
  ready true, required_validation 20, optional_validation 1, and zero missing
  required artifacts. Strict preflight remains `print_start_ready: true` with
  zero issues and no stale CAD target sections. No STEP/STL geometry changed in
  this cycle because the three witness bodies were already generated.
  finding: RH13 now has a package-level leak hierarchy instead of relying on
  hidden CAD layout metadata plus a broad dry-bay ingress overlay. Side-service
  fitting leaks, sample/relief cap-seat leaks, and gasket-tab root leaks all
  have required first-print review bodies before Gate 4 can be evidenced.
  next: use the three required leak witness bodies during Gate 4 dye and
  condensate inspection, and keep pressure, overpressure, spill, and wet/dry
  isolation claims blocked until the physical worksheets contain real evidence.

RS105 export material-cleaning witness coupon set
  do: added `material_cleaning_witness_coupon`, a validation-only same-material
  coupon set driven by the installed material/exposure policy. The layout groups
  only installed surfaces whose service disposition is cleaning-pending:
  printed reusable surfaces and replaceable elastomer/TPU-like surfaces. It
  deliberately excludes COTS consumables, electronics, service leads, and tubing
  so the CAD does not imply those items are cleaned or biologically qualified by
  printed witness geometry.
  review: focused tests verify the coupon metadata traces to cleaning-pending
  exposure/disposition groups, excludes disposable/COTS/electronics parts,
  remains validation-only, exports with expected STEP/STL names, and is required
  in the first-print handoff. Regenerated CAD/package outputs, rewrote the
  package manifest with 21 required validation bodies, reran package audit ready
  true, and smoked the validation viewer with `material_cleaning_witness_coupon`
  present at 38.00 x 127.00 x 1.55 mm. Strict preflight returns to
  `print_start_ready: true` after updating the generated timestamp. This is a
  coupon for cleaning/soak/scrub/odor/exposure evidence only; it does not mark
  BSL1 compatibility, leachables, contamination, or survival controls passed.
  finding: RH14 now has a first-print artifact that separates cleanable printed
  and flexible material evidence from disposable consumables and electronics.
  The material/exposure policy is no longer only a manifest table; it has a
  required physical witness surface for same-material observations.
  next: print/use the coupon set with the same material or flexible stock used
  for the relevant parts, record cleaning/decontamination observations and any
  odor/leachable/surface-change evidence, and keep biology claims blocked until
  actual Gate evidence exists.

RS106 row tiling/service clearance composite validation
  do: added `row_tiling_service_clearance_check`, a validation-only CadQuery
  body that combines the installed row footprint, eight adjacent OT-2 slot
  keepout volumes, and eleven operating gas/electrical service envelopes into
  one Gate 3 review artifact. The layout metadata carries the row axis, tile
  count, service-envelope count, adjacent-keepout count, the 4.10 mm modeled
  minimum vertical clearance, and the 2.00 mm requirement.
  review: focused tests verify the composite body is validation-only, uses the
  same neighbor-slot and service-dress source rectangles, exports with expected
  STEP/STL names, is required in the first-print handoff, and updates the Gate 3
  worksheet target set from 10 to 11 not-tested rows. Regenerated CAD/package
  outputs, rewrote the package manifest with 22 required validation bodies,
  reran package audit ready true, regenerated and audited the Gate 3 worksheet
  with 11 blank rows, and smoked the validation viewer with
  `row_tiling_service_clearance_check` present at 395.00 x 405.25 x 120.70 mm.
  finding: RH16 now has a single first-print artifact for row-to-row tiling and
  service-interface clearance instead of relying on separate adjacent-slot and
  service-dress bodies. This is still CAD proxy evidence only.
  next: use the required composite body during Gate 3 OT-2 placement review,
  capture printed row and dressed tube/cable evidence with adjacent-slot context,
  and keep row tiling/service-interface claims blocked until the physical
  worksheet has pass evidence.

RS107 fail-closed pre-run inspection validation
  do: added `fail_closed_prerun_inspection_check`, a validation-only first-print
  artifact whose metadata enumerates eight blockers that prevent OT-2 operation
  until evidenced: missing stack items, unseated sample/relief cap, unlatched
  wedges, out-of-range gasket squeeze, missing gas PCB cartridges, missing or
  unmated service leads, service dress over the operating field, and blocked
  dry-bay/witness paths. The exported solid is intentionally a simple checklist
  coupon slab so the rich blocker metadata does not make CadQuery validation
  exports expensive.
  review: focused tests verify the blocker metadata, source validation checks,
  validation-only separation, export names, required first-print inclusion, and
  the Gate 2 dry-assembly target/worksheet update from 13 to 14 not-tested
  rows. Regenerated CAD/package outputs, rewrote the package manifest with 23
  required validation bodies, regenerated and audited the Gate 2 worksheet with
  14 blank rows, and smoked the validation viewer with
  `fail_closed_prerun_inspection_check` present at 46.00 x 74.00 x 0.45 mm.
  finding: RH17 now has a required pre-run inspection artifact that ties the
  existing negative-state witnesses, gasket gauge, connector checks,
  service-dress checks, and dry-bay witness checks into an explicit fail-closed
  rule: any failed blocker prevents OT-2 operation.
  next: fill Gate 2 with real print-QC, dry assembly, service cycling, gasket
  measurement, connector/cap/latch photos, and dry-bay inspection evidence, and
  keep fail-closed operating claims blocked until those rows pass.

RS108 observer optical stability validation
  do: added `observer_optical_stability_check`, a required validation-only
  first-print artifact whose metadata enumerates eight observer-performance
  blockers: stray light blank frame, baffle/reflection screen, fiducial
  visibility, focus repeatability, vibration stability, thermal drift, signal
  quality baseline, and wet-boundary optical contamination. The exported solid
  is intentionally a single 56.00 x 72.00 x 0.45 mm checklist slab so the
  optical evidence metadata does not make CadQuery exports expensive.
  review: focused tests verify the blocker metadata, validation-only separation,
  export names, required first-print inclusion, Gate 6 target/worksheet update
  from 14 to 15 not-tested rows, and y-split operating-acceptance row counts.
  Regenerated CAD/package outputs, rewrote the package manifest with 24
  required validation bodies, regenerated and audited the Gate 6 worksheet with
  15 blank rows, and smoked the validation viewer with
  `observer_optical_stability_check` present at 56.00 x 72.00 x 0.45 mm.
  finding: RH15 now has CAD-proxy closure for observer optical quality and
  stability because both local fiducial/focus geometry and measured-performance
  blockers are required in the first-print handoff. This still does not prove
  imaging, Raman, or biophotonics signal quality.
  next: fill Gate 6 with real blank-frame, reflection, fiducial, focus,
  vibration, thermal-drift, signal-baseline, and wet-boundary optical
  contamination evidence before making observer performance claims.

RS109 latch retention/span validation
  do: added `latch_retention_span_check`, a required validation-only first-print
  artifact whose metadata binds the RH3 thin self-lock margin and omitted
  station span warning to four Gate 2 blockers: detent retention through dry
  cycling, omitted-station bow, post/cap bearing condition, and gasket squeeze
  after latch cycling. The exported solid is intentionally a single
  60.00 x 62.00 x 0.45 mm checklist slab so the mechanical-screen metadata does
  not make validation exports expensive.
  review: focused tests verify validation-only separation, export names,
  required first-print inclusion, blocker metadata, Gate 2 target/worksheet
  update from 14 to 15 not-tested rows, and y-split Gate 2 readiness row counts.
  Regenerated CAD/package outputs, rewrote the package manifest with 25 required
  validation bodies, regenerated and audited the Gate 2 worksheet with 15 blank
  rows, and smoked the validation viewer with `latch_retention_span_check`
  present at 60.00 x 62.00 x 0.45 mm.
  finding: RH3 now has CAD-proxy closure for latch retention/span risk because
  the first-print handoff explicitly blocks wet tests until the thin ramp margin,
  omitted station, post/cap bearing, and post-cycle gasket squeeze have physical
  dry assembly evidence. This still does not prove insertion force, creep, wear,
  wet release, or leak behavior.
  next: print the latch stack, run the dry cycling/detent/bow/gap-gauge checks
  in Gate 2, and keep latch production-retention claims blocked until those rows
  pass with evidence.

RS110 deck-pod seating repeatability validation
  do: added `deck_pod_seating_repeatability_check`, a required validation-only
  first-print artifact whose metadata binds RH1 deck feet and pod/frame keys to
  five Gate 3 blockers: repeat seating, rocking/yaw, shoe/key wear, deck-frame
  contact, and dry-bay debris after pod cycling. The exported solid is a single
  70.00 x 58.00 x 0.50 mm checklist slab so the OT-2 seating evidence metadata
  does not make validation exports expensive.
  review: focused tests verify validation-only separation, export-map
  inclusion, required first-print inclusion, blocker metadata, Gate 3
  target/worksheet update from 11 to 12 not-tested rows, and y-split Gate 3
  readiness row counts.
  finding: RH1 now has CAD-proxy closure for deck seating repeatability because
  the first-print handoff explicitly blocks operating deck use until the printed
  row survives five OT-2 seat/release cycles without rocking, yaw, wear-driven
  looseness, frame contact, or dry-bay debris bridging. This still does not
  prove the physical interface until Gate 3 rows pass with evidence.
  next: after split print QC and Gate 2 dry assembly evidence, seat the printed
  dressed row on the OT-2 deck, run five remove/reinstall cycles, fill the Gate
  3 repeatability row with photos/measurements, and keep downstream wet tests
  blocked until the combined Gate 3 readiness audit passes.

RS111 require gas PCB flow-cell validation body
  do: promoted `gas_pcb_flow_cell_check` into the required first-print
  validation set and made Gate 6's gas PCB aperture/dead-volume target read
  from that validation metadata. The layout now exposes the validation record
  directly, including the two cartridges, two flow cells, two apertures,
  2.00 mm aperture diameter, 12.80 mm3 cell volume, gasket thickness, gasket
  compression, and physical-evidence requirement.
  review: focused tests verify the validation-only separation, required
  first-print inclusion, Gate 6 target wording, package-manifest count, and
  y-split Gate 6/operating acceptance counts. Regenerated package outputs
  should now carry 27 required validation bodies while the Gate 6 worksheet
  remains 15 blank evidence rows.
  finding: RH8 no longer lets gas PCB sampling-cell evidence stay as optional
  exported geometry. A Gate 6 pass now has to reference the required flow-cell
  body when proving aperture alignment, dead volume, and gasket registration.
  next: inspect or print the flow-cell check with the sensor blanks/cartridges,
  then fill Gate 6 with real aperture, gasket-compression, leak/response, and
  thermal proxy evidence after Gates 1-5 are physically ready.

RS112 require consumable metrology gauge for Gate 5
  do: promoted `consumable_metrology_gauge` from optional validation tooling
  into the required first-print validation set and added a Gate 5 target row
  for the gauge dimensions. The target ties the 143.60 x 101.75 x 3.00 mm
  gauge body to plate/mat lot-fit inspection before any puncture or
  consumable-compatibility pass claim.
  review: focused tests verify required first-print inclusion, zero optional
  validation bodies, package-manifest count, Gate 5 target wording, 14-row
  Gate 5 worksheet generation, blank-sheet validity, evidenced-row pass
  counting, and y-split Gate 5 readiness row counts.
  finding: RH10 no longer treats consumable metrology as optional package
  context while Gate 5 asks for real plate/mat evidence. The handoff now blocks
  consumable/puncture pass claims unless the required gauge row has physical
  evidence alongside plate, mat, puncture-force, repeat-cycle, and plate-shift
  evidence.
  next: inspect or print the required gauge with the current plate/mat lots,
  fill the new Gate 5 row with gauge photos/measurements, and revise params
  only where measured fit changes support, sealing, puncture, imaging, or
  service-removal claims.

RS113 require printability support-cleanup validation
  do: added `printability_support_cleanup_check`, a required validation-only
  Gate 1 body whose metadata binds six post-print cleanup blockers to physical
  print QC: gasket-land support scars, wedge slide-path debris, side-gas barb
  bore blockage, sensor-pocket debris, dry-bay gutter bridging, and split-edge
  cleanup that removes authority features.
  review: focused tests verify the blocker metadata, validation-only export,
  required first-print inclusion, package-manifest count, validation separation,
  and viewer bounds at 64.00 x 80.00 x 1.20 mm. Regeneration should carry 29
  required validation bodies with zero optional validation bodies.
  finding: RH9 no longer leaves support cleanup as prose-only package review.
  Gate 1 still needs real printed-part evidence before any print QC pass claim.
  next: use the required cleanup checklist during split print QC, record photos
  and measurements for support scars, debris, bores, pockets, gutters, and
  split edges, then revise CAD or print process only from measured failures.

RS114 require observer kinematic split validation
  do: added `observer_kinematic_split_check`, a required validation-only Gate 6
  body that binds the compact observer front-end swept volume, larger carriage
  envelope, service raceway, dry bay, and fiducial/focus targets into one
  kinematic split evidence rule.
  review: focused tests verify validation-only export, required first-print
  inclusion, package-manifest count, Gate 6 worksheet generation with 16 blank
  rows, split-Y sensor/thermal readiness row counts, and operating-acceptance
  gating. Regenerated CAD/package outputs now carry 30 required validation
  bodies, and the viewer should show the split checklist at
  58.00 x 78.00 x 0.45 mm.
  finding: RH6 no longer leaves the observer kinematic split as prose beside
  three separate clearance bodies. The package now blocks Gate 6 observer
  readiness unless the physical front-end/carriage/focus/service-loop split is
  reviewed, while still refusing to claim imaging, Raman, or biophotonics
  performance from CAD.
  next: use the split checklist during Gate 6 observer installation and service
  cycling, record focus-travel and service-loop recovery evidence, and revise
  the observer mechanism only from measured install, snag, drift, vibration, or
  signal failures.

RS115 require all-well pipette puncture swept path
  do: promoted `pipette_puncture_swept_path_check` into the required
  first-print validation set and made the Gate 5 puncture target row name the
  required swept-path body for all 384 septum targets.
  review: focused tests verify required first-print inclusion, package-manifest
  count, Gate 5 target wording, blank-sheet validity, evidenced-row pass
  counting, and y-split Gate 5 readiness gating. No STEP/STL geometry changed;
  the swept-path body was already generated and the package manifest now
  reports 31 required validation bodies with zero optional bodies.
  finding: RH11 no longer relies on an exported-but-not-required all-well
  puncture path while Gate 5 asks for physical puncture evidence. The handoff
  now blocks all-well pipette/septum access claims unless the required swept
  path is present and the Gate 5 worksheet carries physical evidence.
  next: after Gates 1-4 pass, use the required swept-path body with real
  plate/mat lots, measure puncture force, repeat puncture/reseal behavior, tip
  deflection, and plate lateral shift, then revise CAD only from measured
  failures.

RS116 require headspace barrier and shared-volume Gate 4 validation
  do: promoted `headspace_barrier_check` and `headspace_volume_check` into the
  required first-print validation set and added two Gate 4 worksheet targets for
  the sealed headspace perimeter and continuous shared row volume.
  review: focused Gate4/package tests passed (10 passed, 7 warnings). The
  package manifest now reports 33 required validation bodies with zero optional
  bodies, and the Gate 4 worksheet regenerates as 8 blank not_tested rows. No
  STEP/STL geometry changed because both headspace bodies were already exported.
  finding: RH5 no longer leaves the wet chamber sealed perimeter and shared row
  volume as exported-but-not-required geometry while Gate 4 asks for leak and
  wet/dry evidence.
  next: inspect the required barrier and volume bodies during Gate 4 setup,
  then collect dye, condensate, continuity, and dry-bay ingress evidence before
  any sealed-headspace or wet/dry pass claim.

RS117 require dry-bay envelope and boundary Gate 4 validation
  do: promoted `dry_bay_envelope_check` and `dry_bay_boundary_check` into the
  required first-print validation set and added a Gate 4 worksheet target for
  dry-bay boundary rail clearance while making the protected-volume row trace to
  the required dry-bay envelope body.
  review: focused Gate4/package tests passed (10 passed, 7 warnings). The
  package manifest now reports 35 required validation bodies with zero optional
  bodies, and the Gate 4 worksheet regenerates as 9 blank not_tested rows. No
  STEP/STL geometry changed because both dry-bay bodies were already exported.
  finding: RH5 no longer leaves the reserved observer volume and side boundary
  rails as exported-but-not-required geometry while Gate 4 asks for wet/dry and
  dry-bay ingress evidence.
  next: inspect the required dry-bay envelope and boundary bodies during Gate 4
  setup, then collect dye, condensate, debris, service-dress, and ingress
  evidence before any dry-bay protection pass claim.

RS118 require remaining Gate 6 connector and observer envelope validation
  do: promoted `sensor_connector_service_clearance_check`,
  `observer_front_end_swept_body_check`, `observer_carriage_envelope_check`,
  and `observer_service_raceway_envelope_check` into the required first-print
  validation set; added Gate 6 rows for connector clearance and the three
  observer envelope bodies; fixed `export_row_coupon_validation_tools()` so the
  connector clearance STEP/STL is emitted.
  review: focused export/Gate6/package tests passed (12 passed, 7 warnings).
  Regenerated CAD, manifest, and Gate 6 worksheet; package audit now reports
  39 required validation bodies, 0 optional, ready true; Gate 6 worksheet
  regenerates as 20 blank not_tested rows.
  finding: the first-print handoff no longer contains exported-but-not-required
  validation bodies. Gate 6 still blocks connector service, observer
  installation, focus recovery, service-loop, imaging/Raman/biophotonics, and
  sensor/thermal claims until physical evidence exists.
  next: inspect the required connector-clearance and observer envelope bodies
  during Gate 6 setup, then collect connector mating/service-cycle, observer
  install/focus/service-loop, optical stability, and sensor/thermal evidence
  before any Gate 6 pass claim.

RS119 resolve first-print material authority conflict
  do: added a machine-readable material-authority decision to
  `row_coupon_part_manifest()`, printed it in the first-print package manifest,
  and recorded the 2026-06-04 decision that the one-row coupon first-print path
  supersedes the older authority-insert stance for mechanical retention, datum,
  latch, service-retention, and validation bodies.
  review: focused manifest/policy tests protect the decision rows. The package
  manifest still allows explicit COTS consumables, electronics, gaskets, cable
  assemblies, and tubing as scoped boundary parts while forbidding metal
  inserts, metal fasteners, threaded inserts, adhesive bonds, glue, solvent
  welds, thermal stakes, permanent welds, hidden bonded authority, and springs
  as coupon retention authority.
  finding: the context conflict is no longer open for the first-print coupon.
  Future metal, bonded, spring, or commercial mechanical authority must become a
  new explicit exception with tests, generated artifacts, and physical service
  evidence instead of quietly entering the installed state.
  next: keep M4-M10 physical latch/compression evidence as the next material
  risk surface; do not relax the first-print package policy unless measured
  failure forces a recorded exception.

RS120 add service-state review worksheet
  do: added a first-print service-state review worksheet and audit generated
  from `ROW_COUPON_SERVICE_MODES`, `service_modes`, and `review_modes`; linked
  the worksheet from scaffolded and live first-print records; added CLI writers
  and audits for the CSV.
  review: focused tests passed (9 passed, 7 warnings). The live worksheet
  regenerates as 17 blank `not_tested` rows covering installed, service, and
  negative-review viewer modes. The audit reports worksheet_valid true,
  service_state_review_ready false, 0 issues; preflight now rejects a missing
  service-state worksheet link.
  finding: RH7 no longer leaves service-state screenshot review as an
  untracked prose item. The worksheet still does not prove physical
  serviceability or mark any Gate 1-6 row passed; it only creates the evidence
  surface for screenshots or plain-Python bounds review.
  next: fill the 17 service-state rows with CQ screenshots or plain-Python
  bounds evidence, then use physical Gate 2 assembly cycling to decide whether
  any service mode requires geometry revision.

RS121 add service-state bounds evidence
  do: factored the service-mode CAD builder so plain-Python evidence can reuse
  one installed assembly build, added per-mode CadQuery bounds evidence CSV
  generation, and taught the service-state review writer to mark rows pass
  against those evidence files.
  review: focused tests passed (14 passed, 7 warnings). The live writer produced
  17 service-state review pass rows and 17 per-mode bounds CSVs under
  `data/measurements/2026-06-02_one_row_coupon_service_state_bounds`. The ready
  audit reports worksheet_valid true, service_state_review_ready true, 17 pass
  rows, 0 not_tested rows, and 0 issues.
  finding: RH7 digital service-state review is now evidence-backed instead of a
  manually editable path list. The audit checks existing files, matching mode
  metadata, positive part bounds, absent expected-removed parts, and present
  negative-review witness parts. This still does not prove physical
  serviceability or mark any Gate 1-6 row passed.
  next: use physical Gate 2 dry-assembly cycling and later Gate 6 sensor/thermal
  work to decide whether the bounds-reviewed service states need geometry
  changes before operating-prototype acceptance.

RS122 require service-state readiness in preflight
  do: wired the first-print service-state review audit into the main preflight
  and operating-prototype acceptance audits, exposed service_state_review_valid
  and service_state_review_ready in CLI output, and made a blank linked
  service-state worksheet block preprint/print-start readiness.
  review: focused tests passed (8 passed, 7 warnings). Live strict preflight now
  reports preprint_ready true, print_start_ready true,
  service_state_review_valid true, service_state_review_ready true, zero
  physical gate passes, zero missing links, zero stale CAD target sections, and
  0 issues. Live operating acceptance still reports operating_prototype_ready
  false, service_state_review_ready true, sensor_thermal_ready false, Gate 6
  pass rows 0, and physical_gate_passes 0.
  finding: service-state evidence is no longer an orphan side audit; the
  top-level first-print gates now require it before preflight can close. This
  raises the digital handoff bar without converting CAD/viewer evidence into
  physical Gate 1-6 acceptance.
  next: fill physical Gate 1 print QC and Gate 2 dry-assembly evidence against
  the split print traveler, then advance the physical chain toward Gate 6.

RS123 require service-state readiness for Gate 2 dry assembly
  do: wired the service-state review worksheet into the Gate 2 dry-assembly
  readiness audit and passed that dependency through Gate 3, Gate 4, Gate 5,
  Gate 6, and operating-prototype acceptance scripts. Updated the template and
  protocols so combined readiness commands pass `--service-state-review`.
  review: focused physical-chain readiness tests passed (6 passed, 7 warnings).
  Live Gate 2 readiness now reports dry_assembly_ready false,
  gate2_dry_assembly_pass_ready false, gate1_print_qc_ready false,
  install_inventory_ready false, service_state_review_ready true, and 0 issues.
  Live Gate 3-6 readiness remains false with 0 issues because the physical
  chain has no pass rows. Operating acceptance remains operating_prototype_ready
  false with service_state_review_ready true, sensor_thermal_ready false,
  Gate 6 pass rows 0, and physical_gate_passes 0.
  finding: a direct Gate 2 pass can no longer bypass the service-state review
  evidence that preflight already requires. The first physical serviceability
  gate now depends on the digital installed/service/negative-review mode audit
  plus print QC and installed-item inventory.
  next: physical Gate 1 print QC and install inventory remain the immediate
  blockers before any Gate 2 dry-assembly pass row can be accepted.

RS124 require evidence paths for install inventory pass rows
  do: added an `evidence_path` column to the first-print install inventory
  worksheet and audit. Every inventory pass row now requires an item or blank
  identifier, an allowed `installed_as` value for its source, and a physical
  evidence path before the inventory can become ready for Gate 2 dry assembly.
  review: focused install-inventory/Gate 2 tests passed (7 passed, 7
  warnings), and targeted scaffold/template/preflight tests passed (5 passed, 7
  warnings). The live inventory worksheet regenerated as 12 blank not_tested
  rows with the new column; its audit reports worksheet_valid true,
  install_inventory_ready false, 12 not_tested rows, and 0 issues. Live strict
  preflight remains preprint_ready true and print_start_ready true with
  install_inventory_ready false and physical_gate_passes 0. Operating
  acceptance remains operating_prototype_ready false with sensor_thermal_ready
  false, Gate 6 pass rows 0, and physical_gate_passes 0.
  finding: installed nonprinted items can no longer be promoted from text-only
  identifiers to Gate 2 readiness. The first physical assembly gate now needs
  visible evidence for real consumables, tubing, electronics/cables, sensor
  packages, or dimensional blanks before any dry-assembly pass row can count.
  next: collect the physical inventory evidence paths while filling split Gate
  1 print QC and the print batch traveler; keep Gate 2 blocked until both are
  ready.

RS125 require evidence paths for Gate 1 print QC pass rows
  do: added an `evidence_path` column to the first-print Gate 1 QC worksheet
  schema and audit for both monolithic and split-Y print paths. Every Gate 1
  pass row now requires measured X/Y/Z values within tolerance and a physical
  evidence path before print QC can become ready.
  review: focused Gate 1, split print traveler, and Gate 2 readiness tests
  passed (9 passed, 7 warnings). Live monolithic Gate 1 regenerated as 16 blank
  not_tested rows and live split-Y Gate 1 regenerated as 21 blank not_tested
  rows, both with evidence_path columns and 0 audit issues. Live combined split
  Gate 1 print QC remains print_qc_ready false with gate1_pass_ready false,
  print_batch_handoff_ready true, 0 printed rows, 21 unprinted parts, and 0
  issues. Live strict preflight remains preprint_ready true and
  print_start_ready true with gate1_pass_ready false and physical_gate_passes
  0. Operating acceptance remains operating_prototype_ready false with Gate 6
  pass rows 0 and physical_gate_passes 0.
  finding: the first physical print gate can no longer be closed from typed
  dimensions alone. Gate 2 now inherits a Gate 1 prerequisite that requires the
  physical print batch to exist, the traveler rows to be marked printed, and
  every passing printed/split part to carry measured dimensions plus evidence.
  next: print the 21 split queue files, mark traveler rows printed only after
  the batch exists, attach Gate 1 evidence paths for every measured part, and
  keep Gate 2 blocked until install inventory is evidenced too.

RS126 require evidence paths for printed split traveler rows
  do: added `print_evidence_path` to the split print batch traveler and audit.
  Traveler rows may remain `not_printed` with blank evidence for handoff, but
  any row changed to `printed` now requires physical print evidence before it
  can support combined Gate 1 print-QC readiness.
  review: focused split traveler, Gate 2, Gate 3, and operating acceptance
  tests passed (4 passed, 7 warnings). The live split traveler regenerated with
  a `print_evidence_path` column, audits handoff_ready true with 21 not_printed
  rows and 0 issues, and combined Gate 1 print QC remains print_qc_ready false
  with 0 printed rows, 21 unprinted parts, and 0 issues. Live Gate 2 remains
  dry_assembly_ready false with gate1_print_qc_ready false,
  install_inventory_ready false, service_state_review_ready true, and 0
  issues. Live strict preflight remains preprint_ready true and
  print_start_ready true with physical_gate_passes 0. Operating acceptance
  remains operating_prototype_ready false with physical_gate_passes 0.
  finding: the print batch handoff can no longer be converted to physical Gate
  1 evidence by flipping `print_result` to `printed` alone. Gate 1 now requires
  both per-part print-batch evidence and per-part print-QC measurement
  evidence before it can unblock Gate 2.
  next: after the physical split print, attach traveler `print_evidence_path`
  rows, then enter measured Gate 1 dimensions/evidence and inventory evidence
  before attempting any Gate 2 dry assembly pass row.

RS127 require real first-print evidence files
  do: tightened the first physical evidence audits so Gate 1 pass rows and
  printed split-traveler rows must reference evidence paths that resolve to
  existing nonempty files. Reused the worksheet-relative path resolver used by
  service-state evidence and updated docs/templates to state the file
  requirement explicitly.
  review: ruff passed for `src/aevum_cad/row_coupon_first_print.py` and
  `tests/test_row_coupon_first_print.py`. Focused Gate 1, split traveler, Gate
  2, Gate 3, and operating acceptance tests passed (7 passed, 7 warnings).
  Live split Gate 1 remains worksheet_valid true, gate1_pass_ready false, 21
  not_tested rows, and 0 issues. Live traveler remains handoff_ready true with
  21 not_printed rows and 0 issues. Combined Gate 1 print QC remains
  print_qc_ready false with 0 printed rows, 21 unprinted parts, and 0 issues.
  Live Gate 2 remains dry_assembly_ready false; operating acceptance remains
  operating_prototype_ready false with physical_gate_passes 0; preflight
  remains preprint_ready true and print_start_ready true with 0 issues.
  finding: evidence cells are no longer sufficient as paperwork. First physical
  print readiness now requires actual local evidence artifacts behind both
  print-batch and Gate 1 measurement claims.
  next: print the 21 split queue parts, save nonempty print evidence files,
  enter traveler `print_evidence_path` rows, then enter measured Gate 1
  dimensions with evidence files and collect install-inventory evidence before
  attempting Gate 2 dry assembly.

RS128 require real downstream physical evidence files
  do: extended the worksheet-relative nonempty evidence-file requirement to
  Gate 2 dry assembly, Gate 3 OT-2 placement, Gate 4 wet/dry witness, Gate 5
  consumable/puncture, Gate 6 sensor/thermal, and the nonprinted install
  inventory. Updated tests, the first-print protocol, measurement README,
  template, and live measurement record to state that pass rows require real
  evidence files, not just path strings.
  review: ruff passed for `src/aevum_cad/row_coupon_first_print.py` and
  `tests/test_row_coupon_first_print.py`. Direct downstream evidence tests
  passed (8 passed, 7 warnings), and the chained Gate 2-6/operating readiness
  tests passed (6 passed, 7 warnings). Live Gate 2-6 worksheets remain
  worksheet_valid true, pass_ready false, all rows not_tested, and 0 issues.
  Live install inventory remains worksheet_valid true, install_inventory_ready
  false, 12 not_tested rows, and 0 issues. Live Gate 2 readiness remains
  dry_assembly_ready false with Gate 1 print QC and install inventory still
  false; operating acceptance remains operating_prototype_ready false with
  physical_gate_passes 0; preflight remains preprint_ready true and
  print_start_ready true with 0 issues.
  finding: the physical chain can no longer be advanced by entering measurement
  prose and placeholder evidence paths after Gate 1. Every downstream pass now
  has to leave a local artifact trail for the measured assembly, placement,
  wet/dry, consumable/puncture, sensor/thermal, or installed-item claim.
  next: collect real print, Gate 1, inventory, and Gate 2 evidence files in
  order; only then should Gate 3-6 physical rows be promoted from not_tested.

RS129 require real sensor inventory for Gate 6 and operating acceptance
  do: split install-inventory readiness into dry mechanical inventory readiness
  and stricter real sensor/electrical inventory readiness. Dimensional
  electronics or sensor blanks can still satisfy the mechanical dry-fit
  inventory path, but Gate 6 sensor/thermal readiness and top-level
  operating-prototype acceptance now require every electronics,
  electrical-service, IR, gas-sensor, and headspace-sensor inventory row to be
  installed as a real part. The Gate 6 readiness issue is also surfaced through
  operating acceptance when a Gate 6 pass worksheet tries to use blanks.
  review: ruff passed for the touched CAD audit, CLI, and test files. Focused
  install-inventory, Gate 6, and operating acceptance tests passed (4 passed, 7
  warnings). Live install inventory remains worksheet_valid true but
  install_inventory_ready false and real_sensor_inventory_ready false. Live
  Gate 6 remains sensor_thermal_ready false with Gate 6 pass rows 0 and
  real_sensor_inventory_ready false. Live operating acceptance remains
  operating_prototype_ready false while print_start_ready true and
  physical_gate_passes 0.
  finding: the first-print path no longer lets dimensionally faithful sensor
  or electrical blanks masquerade as final powered-operating readiness. Blanks
  are now explicitly mechanical-envelope evidence only; the operating prototype
  claim needs real local headspace, IR, gas-sensor, harness, connector, and
  electrical-service inventory evidence before Gate 6 can close.
  next: collect real installed sensor/electrical evidence in the inventory only
  after Gate 1 print evidence and the mechanical Gate 2-5 chain are ready; keep
  operating_prototype_ready false until both the physical chain and real sensor
  inventory pass.

RS130 add acceptance-gate ownership to service-state evidence
  do: added `acceptance_gate` to the first-print service-state review worksheet
  and to every generated plain-Python bounds evidence CSV. The writer now
  records which physical gate owns each installed, service, or negative-review
  state, and the audit rejects stale worksheet or bounds evidence when the gate
  ownership no longer matches the expected mode.
  review: ruff passed for the touched service-state code, scripts, and tests.
  Focused service-state tests passed (10 passed, 7 warnings). Regenerated the
  live service-state worksheet and 17 bounds CSVs; the live service-state audit
  reports worksheet_valid true, service_state_review_ready true, 17 pass rows,
  and 0 issues. Live strict preflight remains preprint_ready true and
  print_start_ready true, while operating acceptance remains
  operating_prototype_ready false with physical_gate_passes 0.
  finding: digital service-state evidence now says which gate owns each
  installed/service/negative-state claim instead of being a free-floating viewer
  checklist. This keeps the preflight service review from blurring into
  physical Gate 1-6 acceptance while making the final operating chain easier to
  audit mode by mode.
  next: keep using the service-state review as digital preflight evidence only;
  physical Gate 1 print QC, install inventory, and later Gate 2-6 evidence must
  still close before operating_prototype_ready can become true.

RS131 separate nonprinted reference geometry from operating installed parts
  do: tightened the first-print package manifest's nonprinted handoff table so
  it no longer describes every COTS, service, and electronics item as a generic
  dimensional reference or blank. COTS consumables now say real parts are
  required, service tubing says real or measured replacement tubing is required,
  and electronics/sensor rows say dimensional blanks support Gates 2-5 only
  while real parts are required for Gate 6 and operating acceptance.
  review: focused package-manifest test passed (1 passed, 7 warnings), and
  ruff passed for the touched package-manifest code, script, and test. The live
  package manifest regenerated with the explicit operating install requirement
  column; package audit readiness stayed true with 12 printed slicer parts and
  zero missing required artifacts.
  finding: the print/procurement handoff no longer undercuts the stricter
  install-inventory audits by implying that sensor or electrical blanks are
  acceptable final operating hardware. Reference STEP/STL bodies remain useful
  for dry fit, but the manifest now names the real-part boundary at the handoff
  surface.
  next: use the regenerated manifest as the procurement authority for real
  COTS consumables, tubing, harnesses, connectors, IR packages, headspace
  carriers, and gas-sensor PCBs; keep Gate 6 and operating acceptance blocked
  until the inventory evidence shows real installed sensor/electrical parts.

RS132 add operating requirements to install inventory rows
  do: added an `operating_requirement` column to the first-print install
  inventory worksheet and audit. The generated rows now carry the final
  operating rule beside the acceptable item: COTS consumables require real
  parts, service tubing requires real or measured-replacement tubing with
  evidence, and electronics/sensor rows state that dimensional blanks are
  dry-fit only through Gate 5 with real parts required for Gate 6 and operating
  acceptance.
  review: ruff passed for the touched install-inventory code, scripts, and
  tests. Focused install-inventory tests passed (5 passed, 7 warnings).
  Regenerated the live install inventory with the new column; its audit reports
  worksheet_valid true, install_inventory_ready false,
  real_sensor_inventory_ready false, 12 not_tested rows, and 0 issues. Strict
  preflight still reports preprint_ready true and print_start_ready true.
  finding: the inventory worksheet itself now carries the real-part boundary
  instead of relying on a separate manifest or protocol note. A stale worksheet
  that says sensor blanks are acceptable for final operation is rejected before
  it can support Gate 2 or later readiness.
  next: collect physical inventory evidence without changing the
  operating_requirement text; keep all electronics/sensor rows as real_part
  before any Gate 6 or operating acceptance claim.

RS133 make service validation bodies own their physical gates
  do: promoted the operating service dress, side-gas tube envelope, side-gas
  leak witness, row-tiling service clearance, and dry-bay ingress audit
  validation bodies from geometry-only aids into layout specs with
  `evidence_gate`, `failure_rule`, `requires_physical_evidence`, and blocked
  operating claims. Gate 2 side-gas and Gate 3 service-dress worksheet rows now
  consume those CAD-owned values directly, and Gate 4 now has an explicit
  `Dry-bay ingress audit` target row tied to the exported
  `dry_bay_ingress_audit_check`.
  review: ruff passed for the touched CAD, first-print, and test modules, and
  `git diff --check` passed. Focused CAD/first-print tests passed (14 passed, 7
  warnings). Regenerated the live Gate 4 worksheet; its audit reports
  worksheet_valid true, 10 expected rows, 10 actual rows, 10 not_tested rows,
  and 0 issues. Strict preflight still reports preprint_ready true,
  print_start_ready true, cad_target_sections_match true, and
  physical_gate_passes 0. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, and 0 issues.
  finding: the remaining service/dry-bay validation bodies now state which
  physical gate owns them and which operating claims remain blocked until real
  evidence exists. This reduces the chance that connected gas/electrical
  service clearance, side-gas wet routing, or dry-bay ingress protection is
  treated as a passive viewer overlay instead of an operating-prototype gate.
  next: keep CAD target sections stable while collecting physical Gate 1-6
  evidence; Gate 4 must now pass the dry-bay ingress audit row in addition to
  the existing witness and condensate rows before supporting downstream gates.

RS134 make sensor-installation validation own Gate 6 serviceability
  do: promoted `sensor_installation_path_check` from a geometry-only export
  into a Gate 6 layout spec with `evidence_gate`, `failure_rule`,
  `requires_physical_evidence`, `requires_real_sensor_inventory`, module-kind
  counts, swept-path body rectangles, and blocked operating claims for gas PCB
  cartridges, local headspace SHT41 sensors, local IR thermopiles, and powered
  sensor/thermal readiness. The Gate 6 `Sensor install workflow` target now
  consumes that CAD-owned `cad_value` instead of reconstructing the count from
  the summary.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused Gate 6/CAD tests passed (10 passed, 7 warnings), including validation
  export separation and unchanged first-print Gate 6 worksheet behavior.
  Regenerated the live Gate 6 worksheet; its audit reports worksheet_valid true,
  20 expected rows, 20 actual rows, 20 not_tested rows, and 0 issues. Strict
  preflight still reports preprint_ready true, print_start_ready true,
  cad_target_sections_match true, and physical_gate_passes 0. Operating
  acceptance remains operating_prototype_ready false with sensor_thermal_ready
  false, real_sensor_inventory_ready false, Gate 6 pass rows 0, and 0 issues.
  finding: local headspace and IR sensor installation can no longer be treated
  as a generic service-mode visual. The exported install-path validation body
  now explicitly blocks Gate 6 until real sensor inventory and install/remove,
  retention, aperture-registration, and dry electrical evidence exist.
  next: collect real sensor inventory and Gate 6 physical evidence only after
  the upstream physical Gate 1-5 chain is ready; keep operating acceptance false
  until the real sensor install path and sensor/thermal worksheet rows pass.

RS135 make Gate 6 electrical service validation own its evidence specs
  do: promoted `sensor_connector_service_clearance_check`,
  `sensor_service_cable_envelope_check`, and
  `electrical_connector_mating_state_check` into Gate 6 layout specs with
  `evidence_gate`, `failure_rule`, `requires_physical_evidence`, blocked
  operating claims, and CAD-owned body rectangles. The Gate 6 worksheet target
  values for service connectors/cables, connector service clearance, service
  cable envelope, and service cable bend envelope now consume those specs
  directly.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (10 passed, 7 warnings), including
  validation-only separation, export registration, connector/cable body counts,
  and unchanged 20-row Gate 6 worksheet values. Regenerated the live Gate 6
  worksheet; its audit reports worksheet_valid true, 20 expected rows, 20
  actual rows, 20 not_tested rows, and 0 issues. Gate 6 readiness remains false
  because Gate 5, real sensor inventory, and all Gate 6 pass rows are still
  missing. Preflight still reports preprint_ready true, print_start_ready true,
  cad_target_sections_match true, and physical_gate_passes 0. Operating
  acceptance remains operating_prototype_ready false with sensor_thermal_ready
  false, real_sensor_inventory_ready false, Gate 6 pass rows 0, and 0 issues.
  finding: electrical service bodies can no longer be treated as passive viewer
  overlays. Connector clearance, external cable dress, and mated/unmated
  connector state now explicitly block powered sensor/thermal readiness until
  physical service-cycle, continuity, mating, and cable-dress evidence exists.
  next: keep the CAD target values stable and collect physical Gate 1-5 evidence
  before attempting Gate 6; Gate 6 must then prove real sensor inventory,
  connector mating, cable continuity, cable bend/egress, and thermal proxy rows
  before operating acceptance can close.

RS136 make pipette access checks own Gate 3/Gate 5 evidence
  do: promoted `pipette_toolhead_swept_body_check` into a Gate 3 layout spec
  with `evidence_gate`, `failure_rule`, `requires_physical_evidence`, blocked
  top-field operating claims, CAD-owned body rectangles, and the lower-clearance
  worksheet value. Promoted `pipette_puncture_swept_path_check` into a Gate 5
  layout spec with all-well target centers, puncture diameter, Z range, target
  count, blocked puncture/serviceability claims, and CAD-owned worksheet values.
  Gate 3 OT-2 placement and Gate 5 consumable/puncture target generation now
  consume those specs directly.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (10 passed, 7 warnings), including
  validation-only separation, all 384 puncture bodies, top toolhead envelope
  bounds, and unchanged Gate 3/Gate 5 worksheet values. Regenerated the live
  Gate 3 and Gate 5 worksheets; their audits report worksheet_valid true, 12/14
  expected rows, all rows not_tested, and 0 issues. Gate 3 readiness remains
  false because Gate 2 and all Gate 3 pass rows are missing; Gate 5 readiness
  remains false because Gate 4 and all Gate 5 pass rows are missing. Preflight
  still reports preprint_ready true, print_start_ready true,
  cad_target_sections_match true, and physical_gate_passes 0. Operating
  acceptance remains operating_prototype_ready false with sensor_thermal_ready
  false, real_sensor_inventory_ready false, Gate 6 pass rows 0, and 0 issues.
  finding: top pipette clearance and all-well septum puncture access can no
  longer be treated as simple derived geometry. The required validation bodies
  now explicitly block OT-2 placement and consumable/puncture pass claims until
  measured toolhead-clearance, all-target puncture, mat wear, and plate-shift
  evidence exists.
  next: keep CAD target values stable while collecting physical Gate 1-5
  evidence; Gate 3 must prove the measured OT-2 top field with connected
  services, and Gate 5 must prove all 384 puncture targets with real plates and
  septum mats before downstream sensor/thermal evidence can close.

RS137 make observer clearance envelopes own Gate 6 evidence
  do: promoted `observer_front_end_swept_body_check`,
  `observer_carriage_envelope_check`, and
  `observer_service_raceway_envelope_check` from raw rectangle exports into
  Gate 6 layout specs with `evidence_gate`, `failure_rule`,
  `requires_physical_evidence`, blocked observer/sensor readiness claims,
  CAD-owned body rectangles, and worksheet-owned `cad_value` strings. Gate 6
  observer target generation now consumes those specs directly while preserving
  the existing front-end, carriage, and raceway dimensions.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (10 passed, 7 warnings), including
  validation-only separation, front-end all-well/dry-bay bounds, observer
  optical stability dependencies, kinematic split dependencies, and unchanged
  Gate 6 worksheet values. Regenerated the live Gate 6 worksheet; its audit
  reports worksheet_valid true, 20 expected rows, 20 actual rows, 20 not_tested
  rows, and 0 issues. Gate 6 readiness remains false because Gate 5, real sensor
  inventory, and all Gate 6 pass rows are still missing. Preflight still reports
  preprint_ready true, print_start_ready true, cad_target_sections_match true,
  and physical_gate_passes 0. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, and 0 issues.
  finding: dry observer clearance is no longer represented as anonymous helper
  boxes. The front-end sweep, offset carriage volume, and service raceway now
  explicitly block observer readiness and powered sensor/thermal operation until
  measured clearance, focus travel, and service-loop recovery evidence exists.
  next: keep observer CAD values stable while collecting the upstream physical
  Gate 1-5 chain; Gate 6 must then prove real observer clearance, optical
  stability, kinematic split, and service-loop recovery before any observer or
  sensor/thermal readiness claim can close.

RS138 make deck-fit validation own Gate 3 evidence
  do: promoted `deck_slot_footprint_check`, `deck_frame_keepout_check`, and
  `adjacent_deck_slot_keepout_check` into Gate 3 layout specs with
  `evidence_gate`, `failure_rule`, `requires_physical_evidence`, blocked OT-2
  placement claims, and CAD-owned validation bodies. Filled the missing blocked
  claims on `deck_pod_seating_repeatability_check`. Gate 3 placement target
  generation now consumes the deck-frame spec for assembly footprint values.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (10 passed, 7 warnings), including deck
  slot footprint geometry, deck-frame keepout cutouts, adjacent-slot overhead
  keepouts, deck-pod repeatability blockers, validation-only separation, and
  unchanged Gate 3 worksheet values. Regenerated the live Gate 3 worksheet; its
  audit reports worksheet_valid true, 12 expected rows, 12 actual rows, 12
  not_tested rows, and 0 issues. Gate 3 readiness remains false because Gate 2
  and all Gate 3 pass rows are still missing. Preflight still reports
  preprint_ready true, print_start_ready true, cad_target_sections_match true,
  and physical_gate_passes 0. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, and 0 issues.
  finding: deck seating and neighboring-slot clearance are no longer raw
  exported helper geometry. The slot footprint, frame keepout, deck-pod cycling,
  and adjacent-slot overhead bodies now explicitly block OT-2 placement and
  connected-service row tiling until measured deck fit, seating repeatability,
  no-rock/no-yaw, frame clearance, and neighbor-slot service clearance evidence
  exists.
  next: keep deck-fit CAD values stable while collecting Gate 1 and Gate 2
  physical evidence; Gate 3 must then prove deck-slot engagement, frame
  clearance, adjacent-slot overhead, and repeat seating before downstream wet,
  puncture, or sensor gates can close.

RS139 make wet/dry witness validation own Gate 4 evidence
  do: promoted `wet_dry_failure_path_check`,
  `sample_relief_leak_witness_check`, and `gasket_tab_leak_witness_check`
  into Gate 4 layout specs with `evidence_gate`, `failure_rule`,
  `requires_physical_evidence`, blocked wet/dry operating claims, CAD-owned
  body rectangles, and worksheet-owned CAD values. The validation builders now
  consume those specs instead of reconstructing solids from raw witness
  geometry, while production aperture thresholds and witness gutters remain
  unchanged.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (10 passed, 7 warnings), including
  validation-only separation, aperture gutter/threshold metadata,
  sample-relief cap witness metadata, gasket-tab root witness metadata, and
  unchanged Gate 4 worksheet values. Regenerated the live Gate 4 worksheet; its
  audit reports worksheet_valid true, 10 expected rows, 10 actual rows, 10
  not_tested rows, and 0 issues. Gate 4 readiness remains false because Gate 3
  readiness is false and all Gate 4 pass rows are still missing. Preflight still
  reports preprint_ready true, print_start_ready true,
  cad_target_sections_match true, and physical_gate_passes 0. Operating
  acceptance remains operating_prototype_ready false with sensor_thermal_ready
  false, real_sensor_inventory_ready false, Gate 6 pass rows 0, and 0 issues.
  finding: dry-bay wet-failure routing is no longer split between raw
  aperture-local geometry, cap witness lists, gasket-tab witness lists, and
  worksheet counters. The exported validation bodies now state exactly which
  Gate 4 physical evidence must prove aperture leaks stay in witness gutters,
  sample/relief cap-seat dye routes to a visible edge witness, and serviceable
  gasket-tab roots remain outside the protected dry bay.
  next: keep the Gate 4 CAD values stable while collecting physical wet/dry
  evidence; no downstream puncture, sensor, or operating acceptance claim can
  rely on these checks until Gate 3 placement and all Gate 4 wet/dry worksheet
  rows pass with real evidence.

RS140 make wet/dry containment validation own Gate 4 evidence
  do: promoted `headspace_barrier_check`, `headspace_volume_check`,
  `dry_bay_envelope_check`, and `dry_bay_boundary_check` into Gate 4 layout
  specs with `evidence_gate`, `failure_rule`, `requires_physical_evidence`,
  blocked containment claims, and CAD-owned body rectangles. The validation
  builders now consume those specs, and the Gate 4 worksheet target generation
  reads the same `cad_value`s for sealed perimeter, shared headspace volume,
  protected dry-bay volume, and boundary-rail clearance.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (9 passed, 7 warnings), including
  headspace barrier metadata, shared-volume metadata, dry-bay protected-volume
  metadata, boundary-rail metadata, validation-only separation, and unchanged
  Gate 4 worksheet values. Regenerated the live Gate 4 worksheet; its audit
  reports worksheet_valid true, 10 expected rows, 10 actual rows, 10 not_tested
  rows, and 0 issues. The layout-spec audit no longer lists the four Gate 4
  containment checks as missing specs; remaining gaps are Gate 1 metrology and
  cleaning tools, Gate 2 assembly/fail-closed checks, and Gate 6 observer or
  thermal target helpers. Gate 4 readiness remains false because Gate 3
  readiness is false and all Gate 4 pass rows are still missing. Preflight
  still reports preprint_ready true, print_start_ready true,
  cad_target_sections_match true, and physical_gate_passes 0. Operating
  acceptance remains operating_prototype_ready false with sensor_thermal_ready
  false, real_sensor_inventory_ready false, Gate 6 pass rows 0, and 0 issues.
  finding: wet/dry containment is no longer split between builder math and
  worksheet reconstruction. The sealed wet perimeter, shared headspace volume,
  dry observer bay volume, and boundary rails now explicitly block sealed
  headspace, dry-bay protection, and wet operation claims until dye,
  condensate, debris, service-lead, and boundary-bridge evidence exists.
  next: continue promoting the remaining required validation exports into
  gate-owned specs, with priority on Gate 2 assembly-state and fail-closed
  readiness before downstream physical evidence collection.

RS141 make dry-assembly blockers own Gate 2 evidence
  do: promoted `assembly_state_witness_check` into a Gate 2 layout spec and
  filled the missing Gate 2 evidence contract on `gasket_compression_gap_gauge`
  and `fail_closed_prerun_inspection_check`. The assembly-state builder now
  drives its composite witness export from the spec's required review parts,
  the gasket gap gauge builder consumes spec body rectangles, and Gate 2 dry
  assembly target generation reads the dry-stack, gasket-squeeze, and
  fail-closed CAD values from those specs.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (11 passed, 7 warnings), including
  assembly-state witness metadata, gasket gap-gauge metadata, fail-closed
  blocker metadata, latch retention/span continuity, validation-only
  separation, and unchanged Gate 2 worksheet values. Regenerated the live Gate
  2 worksheet; its audit reports worksheet_valid true, 15 expected rows, 15
  actual rows, 15 not_tested rows, and 0 issues. Gate 2 readiness remains false
  because Gate 1 print QC, install inventory readiness, and all Gate 2 pass
  rows are still missing. Preflight still reports preprint_ready true,
  print_start_ready true, cad_target_sections_match true, and
  physical_gate_passes 0. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, and 0 issues. The
  layout-spec audit no longer lists the Gate 2 assembly-state, gap-gauge, or
  fail-closed checks as missing specs; remaining gaps are Gate 1 metrology and
  cleaning tools plus Gate 6 observer or thermal target helpers.
  finding: dry assembly is no longer split between negative-state witness
  geometry, gap-gauge blade math, and worksheet reconstruction. Missing plates,
  mats, gaskets, gas PCB cartridges, service leads, the sample/relief cap, or
  unseated wedge locks now explicitly block dry assembly and normal OT-2
  operation until physical evidence exists, and any fail-closed blocker still
  prevents OT-2 operation.
  next: promote the remaining required validation exports into gate-owned
  specs, with priority on Gate 6 observer/thermal helper targets before final
  sensor-readiness evidence collection.

RS142 make observer/thermal helper validation own Gate 6 evidence
  do: promoted `well_cell_plane_check`, `ir_thermopile_fov_spot_check`,
  `thermal_condensation_proxy_check`, and
  `observer_fiducial_focus_target_check` into Gate 6 layout specs with
  `evidence_gate`, `failure_rule`, `requires_physical_evidence`, blocked
  sensor/thermal claims, and CAD-owned shape targets. Added the missing
  physical-evidence requirement to `observer_optical_stability_check`. The
  validation builders now consume those shape targets, and Gate 6 target
  generation reads the IR proxy FOV and thermal proxy plan values from the
  promoted specs.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (13 passed, 7 warnings), including well
  cell-plane metadata, IR FOV metadata, thermal/condensation proxy metadata,
  observer fiducial/focus metadata, optical stability blockers, validation-only
  separation, and unchanged Gate 6 worksheet values. Regenerated the live Gate
  6 worksheet; its audit reports worksheet_valid true, 20 expected rows, 20
  actual rows, 20 not_tested rows, and 0 issues. Gate 6 readiness remains false
  because Gate 5 readiness is false, real sensor inventory is false, and all
  Gate 6 pass rows are still missing. Preflight still reports preprint_ready
  true, print_start_ready true, cad_target_sections_match true, and
  physical_gate_passes 0. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, and 0 issues. The
  layout-spec audit now lists only the Gate 1 material-cleaning and consumable
  metrology tools as missing specs.
  finding: Gate 6 thermal and observer helper targets are no longer loose
  shape lists. Cell-plane references, IR plate-margin FOV spots, SHT41/IR/center
  thermal proxy points, condensation pocket low points, and observer
  fiducial/focus patterns now explicitly block cell-temperature, biology,
  condensation-free sensor operation, observer focus repeatability, and imaging
  quality claims until physical evidence exists.
  next: promote the remaining Gate 1 material-cleaning and consumable metrology
  validation tools into gate-owned specs, then keep CAD values stable while
  collecting physical Gate 1-6 evidence.

RS143 make Gate 1 material and metrology validation own evidence
  do: promoted `consumable_metrology_gauge` and
  `material_cleaning_witness_coupon` into Gate 1 layout specs with
  `evidence_gate`, `failure_rule`, `requires_physical_evidence`, blocked
  physical claims, CAD values, and source layout checks. The consumable gauge
  spec owns the plate/mat pocket geometry and 96 plug-pocket centers; the
  material-cleaning spec wraps the ten coupon groups, 16 represented parts, and
  38.00 x 127.00 x 1.55 mm witness body. The builders now consume those specs,
  and the standalone material-cleaning export no longer depends on a missing
  top-level coupon `z` field.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (12 passed, 7 warnings), including
  consumable metrology metadata, material-cleaning witness metadata,
  validation-only separation, required validation evidence contracts, Gate 1
  worksheets, split print-QC handoff, and downstream physical-chain blocking.
  The required-validation layout-spec audit now reports missing_count 0 across
  all 39 required validation checks. Regenerated the installed, split-Y, and
  validation STL/STEP outputs; the live record generated-output timestamp is
  `2026-06-04T18:41:46Z` and preflight reports generated_output_timestamp_matches
  true, cad_target_sections_match true, preprint_ready true, print_start_ready
  true, physical_gate_passes 0, and 0 issues. Regenerated Gate 1 worksheets:
  monolithic has 16 expected/actual not_tested rows, split-Y has 21
  expected/actual not_tested rows, and combined split print-QC remains
  print_qc_ready false with 0 printed rows, 21 unprinted parts, and 0 issues.
  Operating acceptance remains operating_prototype_ready false with
  sensor_thermal_ready false, real_sensor_inventory_ready false, Gate 6 pass
  rows 0, physical_gate_passes 0, and 0 issues.
  finding: the required validation package no longer has loose Gate 1 tooling.
  COTS plate fit, septum mat fit, plug alignment, and same-material cleaning or
  exposure claims now explicitly block Gate 1 print QC and normal OT-2
  operation until real printed/procured evidence exists.
  next: keep the CAD target values and regenerated output package stable while
  collecting physical split print batch evidence, Gate 1 measurements, install
  inventory, and Gate 2-6 evidence; the overall operating prototype remains
  unclosed until those physical gates pass.

RS144 demote bench-sealed service state from operating authority
  do: changed the `bench_sealed` service-mode scope from a sealed installed
  alias to `bench-only sealed leak/setup review; not normal OT-2 operating
  authority`, and changed its first-print acceptance gate to `preflight
  digital bench-only service-state review`. The geometry remains the same as
  installed for digital bounds comparison, but the manifest, service-state
  worksheet, and generated bounds evidence no longer present it as another
  normal OT-2 operating state.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (4 passed, 7 warnings), verifying
  `bench_sealed` is same-geometry service review, not operating authority, and
  that service-state review/preflight metadata enforce the bench-only gate.
  Regenerated the live service-state review worksheet and all 17 plain-Python
  bounds evidence CSVs; its audit reports worksheet_valid true,
  service_state_review_ready true, 17 expected rows, 17 actual rows, 17 pass
  rows, and 0 issues. Preflight remains preprint_ready true, print_start_ready
  true, generated_output_timestamp_matches true, cad_target_sections_match
  true, service_state_review_ready true, physical_gate_passes 0, and 0 issues.
  Operating acceptance remains operating_prototype_ready false with
  sensor_thermal_ready false, real_sensor_inventory_ready false, Gate 6 pass
  rows 0, physical_gate_passes 0, and 0 issues.
  finding: the default installed state is now the only service state described
  as normal OT-2 operation. Bench sealing remains useful as a digital/bench
  review view, but it cannot substitute for installed operating authority or
  any physical Gate 1-6 evidence.
  next: continue keeping bench/review states explicitly non-operating while
  collecting physical split print batch, Gate 1, inventory, and Gate 2-6
  evidence.

RS145 make sample/relief flow-test adapter an explicit bench service state
  do: added `sample_relief_flow_test` as a bench-only service mode. It removes
  the installed `printed_sample_relief_cap`, adds
  `sample_relief_flow_test_adapter`, and records that cap/adapter swap in the
  first-print service-state evidence contract. `build_flow_test_adapters()` now
  requires exactly one `sample_relief` lid port instead of iterating arbitrary
  future lid ports, so the adapter is tied to the single production
  sample/relief role and remains out of normal installed operation.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (7 passed, 7 warnings), verifying the
  adapter mode removes the installed cap, adds the bench-only adapter, updates
  service-state review rows, and audits bounds evidence for the expected
  removed/review parts. Regenerated the live service-state review worksheet and
  all 18 plain-Python bounds evidence CSVs; its audit reports worksheet_valid
  true, service_state_review_ready true, 18 expected rows, 18 actual rows, 18
  pass rows, and 0 issues. Preflight remains preprint_ready true,
  print_start_ready true, generated_output_timestamp_matches true,
  cad_target_sections_match true, service_state_review_ready true,
  physical_gate_passes 0, and 0 issues. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, physical_gate_passes
  0, and 0 issues.
  finding: flow-test adapter geometry is no longer just a generic top-port
  helper. It is an explicit sample/relief bench-review state with cap removal
  and adapter presence recorded in generated evidence, while installed OT-2
  operation still carries the seated sample/relief cap and no bench adapter.
  next: keep any remaining bench/test geometry behind explicit service or
  validation modes while collecting the real split print batch, Gate 1,
  inventory, and Gate 2-6 evidence.

RS146 split side-gas tube unseated review from missing service leads
  do: added `side_gas_tubes_unseated` as a negative service-review state. The
  normal installed state still carries `cots_gas_service_tubes`; the new review
  state removes that installed tube part, keeps the electrical service pigtails
  installed, and adds `unseated_side_gas_tubes_review` with the same hollow
  supply/return tube geometry pulled outward from the printed barbs. The
  assembly-state witness check now includes this review body, and the
  fail-closed service-leads checkpoint blocks on `side_gas_tubes_unseated`
  separately from missing leads or unmated electrical connectors.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (7 passed, 7 warnings), proving the
  unseated gas-tube mode is distinct from `service_leads_missing`, the
  assembly witness composite contains the new review part, and generated
  service-state bounds evidence records the expected removed/review parts.
  Regenerated installed, split-Y, and validation STL/STEP outputs; the latest
  required artifact timestamp is `2026-06-04T19:36:33Z`. Regenerated the live
  service-state review worksheet and all 19 plain-Python bounds evidence CSVs;
  its audit reports worksheet_valid true, service_state_review_ready true, 19
  expected rows, 19 actual rows, 19 pass rows, and 0 issues. Preflight is back
  to preprint_ready true and print_start_ready true with generated output
  timestamp match, cad_target_sections_match true, service_state_review_ready
  true, physical_gate_passes 0, and 0 issues. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, physical_gate_passes
  0, and 0 issues.
  finding: side gas service is no longer only binary present/missing in CAD.
  The review set now distinguishes connected normal operation from tubes that
  are present but pulled off their barbs, which better matches the operating
  requirement that side supply/return services are seated and retained.
  next: continue demoting any remaining bench/test ambiguity while the real
  split print batch, Gate 1 measurements, install inventory, and Gate 2-6
  physical evidence are collected.

RS147 split gas PCB cartridge unseated review from missing cartridges
  do: added `gas_pcb_cartridges_unseated` as a negative service-review state.
  The normal installed state still carries `gas_sensor_pcbs`,
  `gas_pcb_interface_gaskets`, and `printed_gas_pcb_keeper_doors`; the new
  review state removes the installed PCBs and keeper doors, leaves the duct
  gaskets seated, and adds `unseated_gas_pcb_cartridges_review` with lifted
  cartridge and keeper-door geometry. The assembly-state witness check now
  includes this review body, and the fail-closed gas-PCB checkpoint blocks on
  `gas_pcb_cartridges_unseated` separately from `gas_pcbs_missing`.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (8 passed, 7 warnings), proving the
  unseated cartridge mode is distinct from the missing-cartridge mode, keeps
  the duct gaskets installed, updates the assembly witness composite, and
  records the expected service-state removed/review parts in generated bounds
  evidence. Regenerated installed, split-Y, and validation STL/STEP outputs;
  the latest required artifact timestamp is `2026-06-04T19:59:50Z`.
  Regenerated the live service-state review worksheet and all 20 plain-Python
  bounds evidence CSVs; its audit reports worksheet_valid true,
  service_state_review_ready true, 20 expected rows, 20 actual rows, 20 pass
  rows, and 0 issues. Preflight is back to preprint_ready true and
  print_start_ready true with generated output timestamp match,
  cad_target_sections_match true, service_state_review_ready true,
  physical_gate_passes 0, and 0 issues. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, physical_gate_passes
  0, and 0 issues.
  finding: gas PCB service is no longer only present/missing in CAD. The
  installed operating state still represents cartridges sealed to duct sampling
  gaskets, while the review set now exposes cartridges that are present but
  lifted out of compression before the sensor/thermal chain can pass.
  next: continue closing any remaining CAD ambiguity while the real split
  print batch, Gate 1 measurements, install inventory, and Gate 2-6 physical
  evidence are collected.

RS148 add fail-closed local sensor missing review
  do: added `local_sensors_missing` as a negative service-review state for the
  local headspace and lower IR modules. The normal installed state still carries
  `headspace_sht41_microcarriers`, `ir_thermopiles`, and
  `ir_thermopile_face_gaskets`; the new review state removes those local sensor
  parts while leaving harnesses/connectors installed and adds
  `missing_local_sensor_witnesses` with SHT41 carrier footprints, IR thermopile
  footprints, and IR face-gasket seal witnesses. The assembly-state witness
  check now includes the new review body, and the fail-closed pre-run checklist
  blocks on `local_sensors_missing`, raising the checklist from 8 to 9 blockers.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (9 passed, 7 warnings), proving the
  local-sensor missing mode is opt-in, removes only the local SHT41/IR sensor
  parts, keeps support harness/service interfaces installed, updates the
  assembly witness composite, updates the Gate 2 fail-closed CAD target, and
  records the expected service-state removed/review parts in generated bounds
  evidence. Regenerated installed, split-Y, and validation STL/STEP outputs;
  the latest required artifact timestamp is `2026-06-04T20:25:34Z`.
  Regenerated the live Gate 2 dry-assembly worksheet with 15 blank rows and the
  updated 9-blocker fail-closed target. Regenerated the live service-state
  review worksheet and all 21 plain-Python bounds evidence CSVs; its audit
  reports worksheet_valid true, service_state_review_ready true, 21 expected
  rows, 21 actual rows, 21 pass rows, and 0 issues. Preflight is back to
  preprint_ready true and print_start_ready true with generated output timestamp
  match, cad_target_sections_match true, service_state_review_ready true,
  physical_gate_passes 0, and 0 issues. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, physical_gate_passes
  0, and 0 issues.
  finding: local headspace and IR sensors are no longer only implicit in the
  sensor-install path. CAD now distinguishes the normal operating state with all
  local sensors installed from a fail-closed review state where required local
  sensor modules or IR face seals are absent.
  next: continue closing any remaining CAD ambiguity while the real split print
  batch, Gate 1 measurements, install inventory, and Gate 2-6 physical evidence
  are collected.

RS149 add fail-closed deck module unseated review
  do: added `deck_module_unseated` as a negative service-review state for OT-2
  deck seating. The normal installed state still represents the module seated on
  all deck engagement feet; the review state keeps every installed operating
  part present, translates the installed assembly upward by the unseated lift
  offset, and adds `deck_module_unseated_review` witness rails over the deck
  engagement foot seating footprints. The fail-closed pre-run checklist now
  blocks on `deck_module_unseated`, `deck_pod_repeat_seating_unproven`, and
  `rocking_or_yaw_unmeasured` under the deck-module seated checkpoint, raising
  the checklist from 9 to 10 blockers.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD/first-print tests passed (9 passed, 7 warnings), proving the
  deck-module unseated mode is opt-in, preserves all installed part names while
  lifting `deck_pods` and `plate_support_frame`, adds only
  `deck_module_unseated_review`, updates the Gate 2 fail-closed CAD target, and
  records Gate 3 service-state evidence with no removed parts. Regenerated
  installed, split-Y, and validation STL/STEP outputs; the latest required
  artifact timestamp is `2026-06-04T20:53:11Z`. Regenerated the live Gate 2
  dry-assembly worksheet with 15 blank rows and the updated 10-blocker
  fail-closed target. Regenerated the live service-state review worksheet and
  all 22 plain-Python bounds evidence CSVs; its audit reports worksheet_valid
  true, service_state_review_ready true, 22 expected rows, 22 actual rows, 22
  pass rows, and 0 issues. Preflight is back to preprint_ready true and
  print_start_ready true with generated output timestamp match,
  cad_target_sections_match true, service_state_review_ready true,
  physical_gate_passes 0, and 0 issues. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, physical_gate_passes
  0, and 0 issues.
  finding: deck seating is no longer only a Gate 3 validation target. CAD now
  distinguishes the normal operating state with the module seated on the OT-2
  deck from a fail-closed review state where the whole installed assembly is
  visibly lifted off the deck engagement footprints.
  next: continue closing any remaining CAD ambiguity while the real split print
  batch, Gate 1 measurements, install inventory, and Gate 2-6 physical evidence
  are collected.

RS150 add fail-closed service dress over pipette field review
  do: added `service_dress_over_pipette_field` as a negative Gate 3
  service-review state for gas/electrical leads routed through the top pipette
  field. The normal installed state still keeps the gas tubes and electrical
  pigtails dressed to the side service envelopes; the review state removes
  those normal routed flexible service bodies and adds
  `misdressed_service_bundle_review` rectangles crossing each septum access
  field inside the OT-2 toolhead swept envelope. The fail-closed
  services-dressed-clear checkpoint now blocks on the explicit
  `service_dress_over_pipette_field` state in addition to the generic
  tube/cable-over-field and adjacent-slot collision blockers.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD tests passed (2 passed, 7 warnings), proving the service-dress
  review mode is opt-in, removes the normal routed gas/electrical flexible
  service parts, keeps service connectors installed, adds only
  `misdressed_service_bundle_review`, overlaps every septum access field, and
  joins the Gate 3 fail-closed blocker set. Focused first-print tests passed (4
  passed, 7 warnings), proving the service-state worksheet now covers 23 modes
  and records the expected removed/review parts for the mis-dressed service
  bundle review. Manifest coverage passed (1 passed, 7 warnings), proving the
  new review body is represented in the service/review manifest. Regenerated
  the live service-state review worksheet and all 23 plain-Python bounds
  evidence CSVs; its audit reports worksheet_valid true,
  service_state_review_ready true, 23 expected rows, 23 actual rows, 23 pass
  rows, and 0 issues. Installed and validation STL/STEP outputs did not need a
  new timestamp because the default operating and validation geometry were not
  regenerated; preflight still reports generated output timestamp match
  `2026-06-04T20:53:11Z`, cad_target_sections_match true,
  service_state_review_ready true, physical_gate_passes 0, and 0 issues.
  Operating acceptance remains operating_prototype_ready false with
  sensor_thermal_ready false, real_sensor_inventory_ready false, Gate 6 pass
  rows 0, physical_gate_passes 0, and 0 issues.
  finding: service dress is no longer only a validation clearance envelope. CAD
  now distinguishes the normal connected side-routed service state from a
  fail-closed review state where the same gas/electrical service role is routed
  through the top pipette field.
  next: keep closing explicit negative states for operating-critical physical
  gates while the real split print batch, Gate 1 measurements, install
  inventory, and Gate 2-6 physical evidence are collected.

RS151 add fail-closed dry bay obstruction review
  do: added `dry_bay_obstructed` as a negative Gate 4 service-review state for
  a blocked dry observer bay or hidden wet witness paths. The normal installed
  state still reserves an open dry bay and visible witness-path margins; the
  review state keeps all installed operating parts present and adds
  `dry_bay_obstruction_review` geometry inside the protected dry-bay envelope:
  one foreign-object block plus front/rear witness-path cover strips. The
  fail-closed dry-bay-clear checkpoint now blocks on the explicit
  `dry_bay_obstructed` state in addition to the generic dry-bay-blocked,
  wet-witness-hidden, and assembly-debris blockers.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD tests passed (2 passed, 7 warnings), proving the dry-bay
  obstruction mode is opt-in, preserves every installed part, adds only
  `dry_bay_obstruction_review`, keeps the obstruction geometry inside the
  protected dry-bay envelope, and joins the fail-closed dry-bay blocker set.
  Focused first-print tests passed (4 passed, 7 warnings), proving the
  service-state worksheet now covers 24 modes and records the no-removal,
  additive review geometry for the dry-bay obstruction state. Manifest coverage
  passed (1 passed, 7 warnings), proving the new review body is represented in
  the service/review manifest. Regenerated the live service-state review
  worksheet and all 24 plain-Python bounds evidence CSVs; its audit reports
  worksheet_valid true, service_state_review_ready true, 24 expected rows, 24
  actual rows, 24 pass rows, and 0 issues. Installed and validation STL/STEP
  outputs did not need a new timestamp because the default operating and
  validation geometry were not regenerated; preflight still reports generated
  output timestamp match `2026-06-04T20:53:11Z`, cad_target_sections_match true,
  service_state_review_ready true, physical_gate_passes 0, and 0 issues.
  Operating acceptance remains operating_prototype_ready false with
  sensor_thermal_ready false, real_sensor_inventory_ready false, Gate 6 pass
  rows 0, physical_gate_passes 0, and 0 issues.
  finding: dry-bay protection is no longer only a validation volume and audit
  checklist. CAD now distinguishes the normal open dry observer bay from a
  fail-closed review state where debris or obstruction occupies the protected
  dry bay and hides the wet witness-path margins.
  next: keep closing explicit negative states for operating-critical physical
  gates while the real split print batch, Gate 1 measurements, install
  inventory, and Gate 2-6 physical evidence are collected.

RS152 add fail-closed adjacent-slot service collision review
  do: added `service_dress_adjacent_slot_collision` as a negative Gate 3
  service-review state for gas/electrical service bundles intruding into
  adjacent OT-2 slot keepouts. The normal installed state still keeps the side
  gas tubes and electrical pigtails dressed through the approved side-service
  envelopes; the review state removes those normal routed flexible service
  bodies, keeps the service connectors installed, and adds
  `adjacent_slot_service_collision_review` rectangles inside each neighboring
  slot keepout with negative vertical clearance. The fail-closed
  services-dressed-clear checkpoint now blocks on the explicit
  `service_dress_adjacent_slot_collision` state in addition to the generic
  adjacent-slot service collision blocker.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD tests passed (2 passed, 7 warnings), proving the adjacent-slot
  collision mode is opt-in, removes the normal routed gas/electrical flexible
  service parts, keeps service connectors installed, adds only
  `adjacent_slot_service_collision_review`, places the review geometry inside
  every adjacent-slot keepout, and joins the Gate 3 fail-closed service-dress
  blocker set. Focused first-print tests passed (4 passed, 7 warnings),
  proving the service-state worksheet now covers 25 modes and records the
  expected removed/review parts for the adjacent-slot collision state. Manifest
  coverage passed (1 passed, 7 warnings), proving the new review body is
  represented in the service/review manifest. Regenerated the live
  service-state review worksheet and all 25 plain-Python bounds evidence CSVs;
  its audit reports worksheet_valid true, service_state_review_ready true, 25
  expected rows, 25 actual rows, 25 pass rows, and 0 issues. Installed and
  validation STL/STEP outputs did not need a new timestamp because the default
  operating and validation geometry were not regenerated; preflight still
  reports generated output timestamp match `2026-06-04T20:53:11Z`,
  cad_target_sections_match true, service_state_review_ready true,
  physical_gate_passes 0, and 0 issues. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, physical_gate_passes
  0, and 0 issues.
  finding: adjacent-slot service clearance is no longer only a validation
  keepout and row-tiling checklist. CAD now distinguishes the normal connected
  side-routed service state from a fail-closed review state where the same
  service role intrudes into neighboring OT-2 slot keepout volume.
  next: keep closing explicit negative states for operating-critical physical
  gates while the real split print batch, Gate 1 measurements, install
  inventory, and Gate 2-6 physical evidence are collected.

RS153 add fail-closed gasket squeeze out-of-range review
  do: added `gasket_squeeze_out_of_range` as a negative Gate 2 service-review
  state for compressed gasket stack measurements outside the allowed latch
  squeeze budget. The normal installed state still represents the lower and
  upper gaskets captured and compressed by the seated latch stack; the review
  state keeps every installed operating part present and adds
  `gasket_squeeze_out_of_range_review` witnesses at every compression stop.
  Each stop carries a short overcrush witness below the minimum gap reference
  and a tall undersqueeze witness above the maximum gap reference, tied back to
  `gasket_compression_gap_gauge`, `latch_retention_span_check`, and
  `assembly_state_witness_check`.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD tests passed (2 passed, 7 warnings), proving the gasket squeeze
  review mode is opt-in, preserves every installed part, adds only
  `gasket_squeeze_out_of_range_review`, creates overcrush and undersqueeze
  witnesses at every compression stop, and remains in the Gate 2 fail-closed
  gasket-compression blocker set. Focused first-print tests passed (4 passed,
  7 warnings), proving the service-state worksheet now covers 26 modes and
  records the no-removal, additive review geometry for the gasket squeeze
  state. Manifest coverage passed (1 passed, 7 warnings), proving the new
  review body is represented in the service/review manifest. Regenerated the
  live service-state review worksheet and all 26 plain-Python bounds evidence
  CSVs; its audit reports worksheet_valid true, service_state_review_ready
  true, 26 expected rows, 26 actual rows, 26 pass rows, and 0 issues. Installed
  and validation STL/STEP outputs did not need a new timestamp because the
  default operating and validation geometry were not regenerated; preflight
  still reports generated output timestamp match `2026-06-04T20:53:11Z`,
  cad_target_sections_match true, service_state_review_ready true,
  physical_gate_passes 0, and 0 issues. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, physical_gate_passes
  0, and 0 issues.
  finding: gasket compression is no longer only a gap-gauge validation target.
  CAD now distinguishes the normal latched, compressed gasket state from a
  fail-closed review state where measured squeeze is visibly outside the
  allowed min/max budget at the compression stops.
  next: keep closing explicit negative states for operating-critical physical
  gates while the real split print batch, Gate 1 measurements, install
  inventory, and Gate 2-6 physical evidence are collected.

RS154 add fail-closed deck pose repeatability review
  do: added `deck_pose_repeatability_unproven` as a negative Gate 3
  service-review state for unproven repeat seating and unmeasured rocking/yaw
  after deck service cycles. The normal installed state still represents the
  row coupon seated on all OT-2 deck engagement feet. The review state keeps
  every installed operating part present and adds
  `deck_pose_repeatability_review` geometry: one enlarged repeat-seat witness
  and one rock/yaw sweep witness at every deck engagement foot, tied back to
  `deck_slot_footprint_check`, `deck_frame_keepout_check`, and
  `deck_pod_seating_repeatability_check`.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD and manifest tests passed (3 passed, 7 warnings), proving the
  deck-pose review mode is opt-in, preserves every installed part, adds only
  `deck_pose_repeatability_review`, creates repeat-seat and rock/yaw witnesses
  at every deck foot, joins the Gate 3 fail-closed deck checkpoint, and is
  represented in the service/review manifest. Focused first-print tests passed
  (4 passed, 7 warnings), proving the service-state worksheet now covers 27
  modes and records the no-removal, additive review geometry for the deck-pose
  repeatability state. Regenerated the live service-state review worksheet and
  all 27 plain-Python bounds evidence CSVs; its audit reports worksheet_valid
  true, service_state_review_ready true, 27 expected rows, 27 actual rows, 27
  pass rows, and 0 issues. Installed and validation STL/STEP outputs did not
  need a new timestamp because the default operating and validation geometry
  were not regenerated; preflight still reports generated output timestamp
  match `2026-06-04T20:53:11Z`, cad_target_sections_match true,
  service_state_review_ready true, physical_gate_passes 0, and 0 issues.
  Operating acceptance remains operating_prototype_ready false with
  sensor_thermal_ready false, real_sensor_inventory_ready false, Gate 6 pass
  rows 0, physical_gate_passes 0, and 0 issues.
  finding: deck pose repeatability is no longer only a generic fail-closed
  blocker inside the deck-pod repeatability validation slab. CAD now
  distinguishes the normal seated deck state from a fail-closed review state
  where repeat-seat cycles and rocking/yaw evidence remain unproven at the
  deck feet.
  next: keep closing explicit negative states for operating-critical physical
  gates while the real split print batch, Gate 1 measurements, install
  inventory, and Gate 2-6 physical evidence are collected.

RS155 add fail-closed assembly debris review
  do: added `assembly_debris_present` as a negative Gate 2 service-review state
  for loose debris inside the protected dry bay or bridging dry-bay aperture
  threshold/witness paths after print cleanup and assembly. The normal
  installed state still represents a clean dry bay and visible wet/dry witness
  paths. The review state keeps every installed operating part present and adds
  `assembly_debris_review` geometry: one loose chip in the protected dry bay
  plus one small threshold-bridge witness at every modeled dry-bay aperture
  threshold, tied back to `printability_support_cleanup_check`,
  `assembly_state_witness_check`, `dry_bay_ingress_audit_check`, and
  `wet_dry_failure_path_check`.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD tests passed (2 passed, 7 warnings), proving the debris review
  mode is opt-in, preserves every installed part, adds only
  `assembly_debris_review`, places debris witnesses inside the protected
  dry-bay envelope, and remains in the fail-closed dry-bay/witness-path
  checkpoint. Focused first-print tests passed (4 passed, 7 warnings), proving
  the service-state worksheet now covers 28 modes and records the no-removal,
  additive review geometry for the assembly-debris state. Manifest coverage
  passed (1 passed, 7 warnings), proving the new review body is represented in
  the service/review manifest. Regenerated the live service-state review
  worksheet and all 28 plain-Python bounds evidence CSVs; its audit reports
  worksheet_valid true, service_state_review_ready true, 28 expected rows, 28
  actual rows, 28 pass rows, and 0 issues. Installed and validation STL/STEP
  outputs did not need a new timestamp because the default operating and
  validation geometry were not regenerated; preflight still reports generated
  output timestamp match `2026-06-04T20:53:11Z`, cad_target_sections_match
  true, service_state_review_ready true, physical_gate_passes 0, and 0 issues.
  Operating acceptance remains operating_prototype_ready false with
  sensor_thermal_ready false, real_sensor_inventory_ready false, Gate 6 pass
  rows 0, physical_gate_passes 0, and 0 issues.
  finding: assembly debris is no longer only a generic pre-run dry-bay blocker.
  CAD now distinguishes the normal clean dry bay and visible witness paths from
  a fail-closed review state where loose debris or threshold bridging would
  block OT-2 operation until Gate 1/Gate 2 evidence clears it.
  next: keep closing explicit negative states for operating-critical physical
  gates while the real split print batch, Gate 1 measurements, install
  inventory, and Gate 2-6 physical evidence are collected.

RS156 make fail-closed blocker review coverage explicit
  do: added machine-readable `blocker_service_review_modes` coverage metadata
  to `fail_closed_prerun_inspection_check`. Exact review states still map to
  themselves, while lower-level physical blockers now point to their explicit
  service-review scenes: deck repeatability and rocking/yaw map to
  `deck_pose_repeatability_unproven`, top-field service intrusion maps to
  `service_dress_over_pipette_field`, adjacent-slot service collision maps to
  `service_dress_adjacent_slot_collision`, and dry-bay blocked/hidden-witness
  blockers map to `dry_bay_obstructed`. Also corrected the fail-closed CAD
  target label from `10 blockers` to `10 checkpoints`, since the checklist has
  10 inspection checkpoints and more than 10 individual blocker states.
  review: ruff passed for the touched CAD, first-print, and test modules.
  Focused CAD and first-print tests passed (3 passed, 7 warnings), proving the
  fail-closed checklist now reports `10 checkpoints`, every blocker has at
  least one service-review mode, and Gate 2 target markdown/worksheet values
  match current CAD. Regenerated the Gate 2 dry-assembly worksheet with 15
  blank rows and the corrected fail-closed target value. Gate 2 readiness audit
  still reports dry_assembly_ready false with gate2_pass_rows 0,
  gate1_print_qc_ready false, install_inventory_ready false,
  service_state_review_ready true, and 0 issues. Installed, validation, and
  service-state geometry did not change, so installed/validation STEP/STL and
  service-state bounds regeneration were not needed; preflight still reports
  generated output timestamp match `2026-06-04T20:53:11Z`,
  cad_target_sections_match true, service_state_review_ready true,
  physical_gate_passes 0, and 0 issues. Operating acceptance remains
  operating_prototype_ready false with sensor_thermal_ready false,
  real_sensor_inventory_ready false, Gate 6 pass rows 0, physical_gate_passes
  0, and 0 issues.
  finding: fail-closed review coverage is no longer inferred from scattered
  review-state tests. The checklist itself now states which review mode covers
  each blocker, and the Gate 2 target wording no longer understates the number
  of blocker states as 10.
  next: keep closing CAD/evidence ambiguity while the real split print batch,
  Gate 1 measurements, install inventory, and Gate 2-6 physical evidence are
  collected.

RS157 carry operating-readiness scope in the first-print package manifest
  do: added a generated `Operating Readiness Scope` section to the
  first-print package manifest. The section is derived from the same
  service-state, worksheet, install-inventory, and physical-gate functions as
  the audits, so the print/procurement handoff now states that package
  readiness is only CAD output presence and handoff scope. It also lists the
  current evidence burden: 28 service-state modes, 16 Gate 1 QC rows, 15 Gate 2
  rows, 12 Gate 3 rows, 10 Gate 4 rows, 14 Gate 5 rows, 20 Gate 6 rows, 12
  install-inventory rows, and 6 physical gates.
  review: ruff passed for the touched first-print module and test module.
  The focused manifest test passed (1 passed, 7 warnings), proving the
  generated package manifest includes the service-state scope, Gate 1/Gate 2
  counts, Gate 6 real-sensor rule, install-inventory rule, and operating
  acceptance gate count. Regenerated
  `outputs/cad/aevum_one_row_coupon_first_print_package_manifest.md`; package
  audit still reports ready true, assembly STEP ok, 12 printed parts, 4
  flexible/compressible parts, 12 COTS/electronics/service items, 39 required
  validation bodies, 0 optional validation bodies, and 0 missing artifacts.
  Preflight remains clean with print_start_ready true, package_ready true,
  service_state_review_ready true, physical_gate_passes 0, and 0 issues.
  Operating acceptance remains operating_prototype_ready false with
  sensor_thermal_ready false, real_sensor_inventory_ready false, Gate 6 pass
  rows 0, physical_gate_passes 0, and 0 issues.
  finding: the print/procurement manifest can no longer be misread as an
  operating acceptance claim. It now carries the current physical evidence
  scope beside the package-ready statement.
  next: keep the CAD/package handoff stable while the real split print batch,
  Gate 1 measurements, install inventory, and Gate 2-6 physical evidence are
  collected.

RS158 expose the physical gate chain in operating acceptance
  do: propagated upstream readiness through the y-split Gate 3, Gate 4, Gate 5,
  and Gate 6 audit dataclasses, then exposed those fields in the top-level
  operating-prototype acceptance audit. The Gate 6 and operating-acceptance CLI
  outputs now show Gate 1 print-QC readiness, Gate 2 dry assembly readiness and
  pass rows, Gate 3 placement readiness and pass rows, Gate 4 wet/dry witness
  readiness and pass rows, Gate 5 consumable/puncture readiness and pass rows,
  install-inventory readiness, service-state review readiness, real sensor
  inventory readiness, and Gate 6 pass rows.
  review: ruff passed for the touched first-print module, Gate 6 readiness
  script, operating-acceptance script, and first-print tests. Focused tests
  passed (2 passed, 7 warnings), proving the propagated fields stay false for
  the blank/preprint state, expose a false Gate 6 pass without upstream gates,
  become true after Gate 1-5 and dry-fit inventory evidence, and still require
  real sensor inventory for sensor/thermal and operating acceptance. Live Gate
  6 readiness now reports sensor_thermal_ready false, service_state_review_ready
  true, install_inventory_ready false, gate1_print_qc_ready false, Gate 2-5
  readiness false, Gate 2-6 pass rows 0, real_sensor_inventory_ready false, and
  0 issues. Live operating acceptance now reports operating_prototype_ready
  false, preflight_artifacts_ready true, print_start_ready true,
  service_state_review_ready true, install_inventory_ready false,
  gate1_print_qc_ready false, Gate 2-5 readiness false, Gate 2-6 pass rows 0,
  sensor_thermal_ready false, real_sensor_inventory_ready false,
  physical_gate_passes 0, and 0 issues.
  finding: operating acceptance no longer hides the upstream blocker behind a
  single Gate 6 false value. The current physical stop is explicit: no installed
  inventory evidence, no split Gate 1 print-QC closure, and no Gate 2-6 pass
  rows yet.
  next: keep the CAD/package handoff stable while the real split print batch,
  Gate 1 measurements, install inventory, and Gate 2-6 physical evidence are
  collected.

RS159 report immediate next evidence actions from operating acceptance
  do: added `next_evidence_actions` to the y-split operating-prototype
  acceptance audit. The property returns no actions when operating acceptance
  is ready, otherwise reports only the immediate actionable evidence blockers:
  preflight/print-start blockers first, then service-state review, install
  inventory, and split Gate 1 print QC, then the first downstream physical gate,
  then real sensor inventory and Gate 6 sensor/thermal closure.
  review: ruff passed for the touched first-print module, operating-acceptance
  script, and first-print tests. The focused operating-acceptance test passed
  (1 passed, 7 warnings), proving the blank/preprint state reports
  `complete_install_inventory` plus `close_split_gate1_print_qc`, a dry-fit
  through-Gate-5 state reports `install_real_sensor_inventory`, and a fully
  evidenced fixture reports no next actions. Live operating acceptance now
  reports operating_prototype_ready false, preflight_artifacts_ready true,
  print_start_ready true, service_state_review_ready true,
  install_inventory_ready false, gate1_print_qc_ready false, Gate 2-6 pass rows
  0, `next_evidence_actions` 2, `complete_install_inventory`,
  `close_split_gate1_print_qc`, and 0 issues.
  finding: the next physical work queue is now machine-readable. The immediate
  evidence work is install inventory plus split Gate 1 print/QC, before Gate 2
  dry assembly or later physical gates can close.
  next: complete installed-item inventory evidence and split Gate 1 print/QC
  evidence, then resume Gate 2 dry assembly.

RS160 generate a next-evidence handoff for the immediate physical work
  do: added `first_print_next_evidence_handoff_markdown` plus
  `write_first_print_next_evidence_handoff`, and a CLI writer at
  `scripts/write_row_coupon_first_print_next_evidence_handoff.py`. The generated
  markdown handoff is derived from the current y-split operating-acceptance
  audit and lists status, immediate evidence actions, source worksheets, close
  conditions, and the audit command for each action. It does not create physical
  evidence or mark any gate passed.
  review: ruff passed for the touched first-print module, writer script, and
  first-print test module. The focused handoff test passed (1 passed, 7
  warnings), proving the handoff lists `complete_install_inventory` and
  `close_split_gate1_print_qc`, includes the source worksheets and audit
  commands, omits downstream Gate 2 actions while the immediate blockers remain
  open, and refuses overwrite by default. Generated
  `data/measurements/2026-06-02_one_row_coupon_next_evidence_handoff.md`; it
  reports operating_prototype_ready false, preflight_artifacts_ready true,
  print_start_ready true, service_state_review_ready true,
  install_inventory_ready false, gate1_print_qc_ready false, Gate 2-6 pass rows
  0, and immediate actions `complete_install_inventory` plus
  `close_split_gate1_print_qc`. Preflight remains clean with print_start_ready
  true and 0 issues. Operating acceptance remains operating_prototype_ready
  false with those same two next-evidence actions and 0 issues.
  finding: the build handoff now has one operator-facing file for the current
  physical work queue, instead of requiring the operator to correlate
  install-inventory, print traveler, split Gate 1 QC, and operating-acceptance
  output manually.
  next: fill install-inventory evidence and split print traveler/Gate 1 QC
  evidence, then rerun the handoff writer so it advances to Gate 2.

RS161 audit the next-evidence handoff against current acceptance
  do: added `audit_first_print_next_evidence_handoff` and
  `scripts/audit_row_coupon_first_print_next_evidence_handoff.py`. The audit
  rebuilds the expected handoff from the current y-split operating-acceptance
  result, compares markdown hashes, checks the actual action rows against
  `next_evidence_actions`, and reports stale or missing handoff content before
  an operator can use an outdated work queue.
  review: ruff passed for the touched first-print module, handoff audit script,
  handoff writer script, and first-print tests. The focused handoff test passed
  (1 passed, 7 warnings), proving synchronized markdown is accepted and stale
  action/content rows are rejected. The live handoff audit reports
  handoff_valid true, matching expected/actual SHA256
  `d823e02650721210db3c24e5c8787fd777ff537cc4be78d80c10f02371664c90`,
  expected/actual actions `complete_install_inventory` and
  `close_split_gate1_print_qc`, and 0 issues.
  finding: the operator-facing next-evidence handoff now has a verifier, so it
  cannot silently drift from the current acceptance audit state.
  next: fill install-inventory evidence and split print traveler/Gate 1 QC
  evidence, then regenerate and re-audit the handoff so it advances to Gate 2.

RS162 collapse the next-evidence handoff meta layer
  do: removed the generated next-evidence handoff markdown, its writer, its
  auditor, and the focused handoff test/imports. The y-split
  operating-prototype acceptance audit remains the single current source for
  `next_evidence_actions`, and the first-print record no longer links an
  additional next-evidence handoff artifact.
  review: ruff passed for the touched first-print module, first-print tests,
  and operating-acceptance script. The focused operating-acceptance test passed
  (1 passed, 7 warnings), and live preflight plus operating acceptance still
  pass cleanly with operating_prototype_ready false, install_inventory_ready
  false, gate1_print_qc_ready false, Gate 2-6 pass rows 0, and next actions
  `complete_install_inventory` plus `close_split_gate1_print_qc`.
  finding: RS160-RS161 added redundant process around an already machine-readable
  acceptance result. The current path is simpler: keep the CAD/package/preflight
  and physical gate audits, but do not maintain a second generated checklist
  around the acceptance checklist.
  next: complete install-inventory evidence and split Gate 1 print/QC evidence,
  then resume Gate 2 dry assembly.

## Resolved Context Conflict

The older materials strategy allowed metal inserts, metal stops, and commercial
authority parts for the eventual row module. The first-print row-coupon package
now carries a stricter 2026-06-04 material-authority decision: no metal, glue,
springs, threaded retention, thermal stakes, permanent welds, or hidden bonded
authority inside the printed coupon's mechanical assembly. Nonprinted
consumables, electronics, gaskets, tubing, and cable assemblies remain scoped
boundary parts, not permission to import hidden mechanical authority.
