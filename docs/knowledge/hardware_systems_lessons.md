# Hardware Systems Lessons

## Purpose

This note preserves the hardware reasoning from the 2026-05-16 design
discussion. It is deliberately broader than the first P300 fixture. It names
what kind of machine Aevum is becoming, what adjacent engineering traditions
have learned, and which failure modes should shape the next row-module design.

The short version:

```text
Aevum is not an OT-2 accessory.
It is an incubated, registered, observable, robotic plate instrument.
```

The first printed P300 PoC proves an interaction envelope. The platform problem
is harder: can a row of adjacent plate tiles behave like a stable environmental
and optical datum while remaining accessible to the OT-2 and transparent to a
moving inverted observer?

## What This Is Like

Aevum sits between several mature instrument families:

- stage-top incubators;
- automated live-cell imaging systems;
- microplate automation decks;
- plate hotels and environmental plate incubators;
- metrology fixtures and kinematic nests;
- wafer, slide, and sample handling systems;
- CNC-like machines with toolheads and explicit coordinate frames;
- environmental test chambers;
- robotic assay platforms;
- multi-client hardware control systems.

None of those analogies is sufficient alone. The hard part is their overlap:
wet biology above, dry precision observation below, robot access from above,
row-level environmental control, and tile adjacency pressure from the sides.

The machine therefore has multiple precision clients:

- the OT-2 pipette needs safe, repeatable target access;
- the glass-bottom plate and cells need stable temperature, humidity, CO2, and
  low-disturbance liquid surfaces;
- the moving inverted observer needs a dry, clear, repeatable optical bay;
- the software bridge needs evidence that the current physical state still
  matches its model;
- the operator needs service actions that do not destroy registration.

The hardware architecture should be judged by whether it lets all of those
clients share one physical truth without hidden coupling.

## The Big Lesson

Systems like this usually fail from quiet coupling between subsystems that were
designed as if independent.

Examples:

- a plate support datum becomes an optical datum;
- a gasket becomes a thermal path;
- a side fitting becomes a tiling blocker;
- a small airflow jet becomes an evaporation bias;
- a printed carrier becomes a calibration assumption;
- a labware offset becomes a hidden coordinate transform;
- a camera image becomes false confidence;
- a service action invalidates a pose without leaving evidence;
- a lid feature fixes humidity while blocking pipette clearance;
- a dry-bay baffle improves contrast while disturbing objective clearance.

The job is to decide what owns truth for each interface, then make that truth
easy to re-measure after assembly, service, heat, humidity, and motion.

## Authority Separation

Mature precision instruments separate authority. Aevum should follow the same
rule.

```text
Datum authority      -> metal pins, bushings, machined lands, fiducials
Seal authority       -> elastomers, compression stops, leak checks
Thermal authority    -> spreaders, heaters, sensors near relevant planes
Flow authority       -> plenums, diffusers, returns, restrictors, visualization
Optical authority    -> glass-path control, baffles, matte surfaces, references
Biological authority -> validated contact materials, sterile/replaceable parts
Motion authority     -> state machine, locks, command journal, recovery
```

Printed plastic is valuable for shape, packaging, ducts, baffles, covers,
fixtures, and iteration speed. It should not be the only source of datum truth,
sealing truth, thermal truth, optical truth, biological truth, or CO2/RH sensing
truth.

## Common Pitfalls

### Treating Nominal CAD As Reality

CAD defines intent. Real hardware supplies evidence.

Printed parts warp. SBS plates vary. Gaskets compress unevenly. Glass bottoms
are not universal datums. Humid heat changes dimensions. A fixture that is
correct in a STEP file can be wrong on the deck after printing, cleaning,
warming, or service.

Required countermeasures:

- measured bounds and support flatness;
- explicit fiducials and accessible QC features;
- hard stops where compression or Z authority matters;
- recordable plate, lid, tile, and observer datum checks;
- post-service revalidation.

### Making The Tile Do Too Much

A standard plate footprint is already crowded. A tile that tries to own CO2
sensing, humidity generation, mixing, heating, sealing, wiring, optical access,
pipette access, registration, and service connectors becomes unbuildable or
un-tileable.

The row-shared headspace is therefore a central architecture decision, not a
convenience. Some functions are naturally row-scale:

- CO2/RH sensing;
- humidification;
- gas mixing;
- pressure relief;
- low-velocity distribution;
- return/exhaust handling;
- lid/rim heating and condensation management.

Each tile should still own local support, registration, identity, gasket land,
heat-transfer interfaces where useful, pipette-access geometry, and dry-bay
aperture discipline.

The row may be shared, but OT-2 deck engagement should remain local. Each plate
space needs a positive seating feature or click-in reference so a long row
module cannot hide yaw, rocking, or accumulated pitch error behind one global
labware offset.

Tall standoffs do not equal a deck interface. The real OT-2 deck has machined
ribs around each slot opening and local retention hardware, so the row coupon
needs per-slot lower shoes, frame keepouts, and measured retainer clearances
before it can claim repeatable seating.

Row-shared headspace does not imply a removable headspace spacer. The preferred
assembly is a lid-owned chamber interface: the lid/manifold carries the
underside relief, plenum, diffuser/return features, access geometry,
compression-stop locations, and heated/controlled surfaces. The headspace
itself is an empty controlled volume. A thin replaceable gasket or septum may be
a separate consumable, but it should not become structural spacer authority.

### Underestimating Humidity

Warm humidified CO2 is hostile to unvalidated hardware. It can cause:

- condensation on lids, glass, sensors, and optical shields;
- polymer creep, swelling, odor, leachables, and dimensional drift;
- corrosion at fasteners, contacts, sensors, and heater terminations;
- adhesive failure and label loss;
- microbial residue and cleaning difficulty;
- fogging or film formation in the optical path;
- sensor drift and unrepresentative readings.

A dry prototype that works mechanically has not yet proven incubator behavior.

### Treating Sealing As Only A Gasket Problem

Seals are compression architectures. A usable row seal needs:

- controlled squeeze;
- hard-stop-limited compression;
- replaceable elastomer or mat parts;
- service repeatability;
- tolerance stack accounting;
- leak and recovery evidence;
- no side clamps or protrusions that break plate adjacency.

Printed latches or flexible walls can help retain parts during a mule test, but
they should not be trusted as long-term sealing authority.

### Airflow Arrogance

"Move gas through the chamber" is not enough. Near open wells, small flow
differences become biological differences.

Flow must be:

- low velocity at the wells;
- evenly distributed across four plates;
- returned without short-circuiting;
- buffered against septum-puncture pressure pulses;
- free of jets, dead zones, and condensation streams;
- demonstrated with smoke/fog, surface disturbance checks, humidity response,
  and CO2 or tracer response.

Biology will notice evaporation gradients long before the machine looks wrong.

### Measuring Temperature At The Wrong Place

A heater sensor is not a sample-plane sensor. A tile-body sensor is not the well
liquid. A lid sensor is not the glass-bottom region.

Thermal evidence should distinguish:

- row headspace temperature;
- lid/rim temperature and condensation margin;
- plate support temperature;
- plate skirt/frame contact behavior;
- near-glass/sample-plane temperature;
- edge versus center well behavior;
- recovery after lid access or pipette access.

The support datum may carry heat, but the live-cell stability problem is
dominated by the small humid headspace, lid/rim condensation control, plate
thermal paths, and local evaporation.

### Polluting The Optical Bay

The dry inverted bay is not leftover space. It is an optical and mechanical
datum volume.

Late convenience features can ruin it:

- extra windows that add reflections, aberration, fouling, or cleaning burden;
- glossy printed surfaces;
- cable shadows;
- gas tubes and fittings crossing the objective envelope;
- baffles that block travel;
- vibration paths from fans or pumps;
- condensation shields that become part of the optical path without evidence.

Add a second optical window only if spill protection, pressure isolation, or
contamination control requires it. If one is added, make it removable,
cleanable, and evidence-scoped.

### Letting Coordinate Systems Drift

Aevum has multiple frames:

- OT-2 deck frame;
- generated fixture frame;
- installed fixture pose;
- oriented labware definition;
- plate/well frame;
- camera frame;
- observer module frame;
- target-class frame.

Offsets should correct small translation errors. They must not hide wrong
orientation, wrong labware identity, stale pose evidence, fixture creep, or
unmodeled service changes.

The hardware should make frame truth visible through fiducials, keyed geometry,
pose evidence, and bounded revalidation.

### Forgetting Service

If a lid, gasket, plate, tile, sensor, heater, cable, baffle, or optical module
cannot be removed and replaced repeatably, the machine will decay into a set of
untracked manual adjustments.

Service events are physical events. They should either preserve datum authority
by design or invalidate the relevant evidence until refreshed.

Service-facing hardware should provide:

- keyed replacement;
- visible seating state;
- compression stops;
- accessible leak/flow/flatness checks;
- fiducials still visible after assembly;
- strain relief outside pipette and observer keepouts;
- records that identify replaced parts.

### Letting Prototype Success Become Architecture

The first PLA fixture succeeding does not prove:

- incubator behavior;
- live-cell material compatibility;
- row flow;
- condensation control;
- dry-bay optical stability;
- long-term registration;
- real plate support;
- gasket compression;
- low-Z or wet workflow safety.

It proves a valuable but narrow interaction envelope: the OT-2/P300 can work
around a raised cassette-like stack with center and off-axis access targets.

Do not let that success freeze the next design into a short, single-plate,
printed-only fixture. If the P300 has comfortable Z margin, spend it on dry-bay
height, service routing, spill separation, baffles, and future observer
clearance.

## Hardware Focus Areas

### Plate Tile Datum

Each tile needs a repeatable real-plate nest:

- support the SBS plate frame/skirt/rim, not the observation glass;
- separate lateral registration from vertical support;
- expose fiducials to the OT-2 camera and the moving observer;
- preserve standard-plate adjacency;
- accept plate-specific support adapters where plate undersides differ;
- use measured hard features for authority where repeatability matters.

### Row Headspace Module

The atmospheric-control object is a row of four plates, not one tile.

The row module should own:

- low-velocity supply distribution;
- balanced return/exhaust/relief;
- CO2/RH sensing in representative return or mixed sampling;
- humidification and mixing upstream of the plate volume;
- lid/rim/septum/gasket stack;
- condensation control;
- pipette-access plane;
- serviceable, keyed removal.

The chamber boundary should run to the row-module perimeter, not merely around
the plate pack. A local plate collar can make the model look enclosed while
leaving the actual air path, sensor path, condensation path, and leak path
unowned. The perimeter margins are valuable architecture: they are where side
service lanes, mixed return sampling, sensor ports, pressure relief, drains,
and routed wet services can coexist with pipette access and no side protrusions.

### Dry Observation Bay

The dry bay should remain:

- rectilinear;
- open to a moving sensor-suite path;
- protected from wet headspace leakage;
- datum-rich;
- matte and baffled where needed;
- free of side protrusions and casual service routing;
- compatible with objective, illumination, folded optics, and future sensor
  payload clearances.

The coupon should therefore show the dry bay as a swept observer volume and
routing-exclusion zone, not only as aperture cuts. Apertures, underside
fiducials, boundary references, spill/condensation exclusion, and service
routing exclusions need to be visible before the observer module exists.

Standoff placement is part of the optical design, not only the deck interface.
The relevant clearance is the objective-center sweep over every well expanded
by the real sensor module body, focus stroke, cable/fiber bend radius, and
service recovery path. Feet, rails, plate lands, baffles, and deck features
should be tested against that swept body. Moving posts to slot edges is only a
first correction; if the desired module still collides, the design needs a
smaller optical nose, folded/off-axis optics, edge rails outside the swept
volume, or a different support architecture.

At an 80 mm dry-bay budget, the robotics problem becomes first-order. The bay
must support a moving carriage or optical head with:

- stiff rail/datums and measurable straightness;
- focus-axis travel and homing without touching the wet stack or deck;
- cable, flex, and fiber bend-radius management;
- vibration isolation from pumps, fans, and OT-2 motion;
- heat isolation from sensors, emitters, and drive electronics;
- laser and stray-light containment for Raman or fluorescence excitation;
- service and recovery access without invalidating plate/headspace registration.

### Authority Inserts

The next hardware should deliberately choose what printed plastic carries and
what inserts carry.

For the row module path, the working constraint is stricter: avoid metal
inserts, external structural hardware, glue, adhesive bonds, solvent welding,
thermal staking, and permanent welds unless a later measured failure forces a
specific exception. The first real assemblage should be print-native and
reversible, using printed datum parts, printed latch/compression parts, printed
seal carriers or printed flexible seals, COTS plates, and COTS septum mats.
This keeps the prototype aligned with the actual device's service order and
failure modes.

When that constraint is relaxed for future systems, good insert candidates are:

- metal datum pins, dowels, bushings, kinematic seats;
- threaded inserts and shoulder screws;
- compression limiters and hard stops;
- platinum-cured silicone, EPDM, or FKM seals;
- metal or graphite thermal spreaders;
- RTDs, thermistors, heater films, fuses, and independent cutoffs;
- COTS CO2/RH sensors and gas components;
- diffuser media, restrictors, or porous flow elements;
- optical fiducials or post-machined reference marks;
- black anodized or validated matte optical surfaces.

## Next Hardware Object

The next physical object should be a one-row mechanical/environmental coupon,
not merely another single-slot raised deck fixture.

Minimum useful scope:

- four plate positions or dimensionally faithful plate dummies;
- a row lid/manifold;
- hard-stop gasket or mat compression stack;
- low-velocity supply and balanced return path;
- dry-bay aperture and observer keepout across the row;
- tile fiducials visible after assembly;
- pipette access through the intended top stack;
- service exits that do not break adjacency;
- places to instrument temperature, humidity, and flow;
- measurement features for support flatness and row alignment.

It does not need full biological control on the first pass. It does need to
prove that the interfaces can coexist.

The evidence target for this coupon is:

- plate/dummy seating repeatability;
- support flatness;
- gasket compression height;
- leak behavior;
- flow distribution;
- liquid-surface disturbance or lack of it;
- condensation pattern;
- pipette access envelope;
- observer clearance;
- fiducial repeatability after assembly and service.

## Design Principle

Every physical claim should be cheap to revalidate.

If a claim cannot be revalidated after assembly, service, heat, humidity, and
motion, it should not become a motion, optical, thermal, sealing, or biological
authority.

That principle aligns the hardware with the bridge software:

```text
physical source -> evidence packet -> derived claim -> gate decision -> operation
```

For hardware, this becomes:

```text
measured feature -> scoped evidence -> authority claim -> design permission
```

The machine should grow by promoting measured claims, not by assuming that a
successful prototype establishes all future authority.
