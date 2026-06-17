# Architecture Notes

## Current Scope

Plate mode only. Microfluidics are intentionally deferred.

Aevum is a tileable live-cell plate platform for the OT-2. Each tile is a
registered glass-bottom SBS plate module, four neighboring tiles share a
controlled row headspace, and the tile grid shares a dry inverted observation
bay underneath. The OT-2 addresses the tiles from above; a separate inverted
sensor-suite module moves through the rectilinear dry bay below them.

The hardware contract is:

1. A glass-bottom SBS plate, initially a CellVis P96-1.5H-N or compatible
   Raman/observation plate, sits on a raised local support datum.
2. Each tile owns plate support, registration, local heat paths, access geometry,
   and evidence identity.
3. Four tiles share one controlled atmospheric headspace for CO2 and humidity,
   because a practical CO2 sensor/control stack is too large for a single
   standard-plate-footprint tile.
4. A row lid, sealing mat, gasket, or septum plane provides liquid access and
   headspace control above the four plates.
5. The glass-bottom plate is the primary optical boundary for observation.
6. The shared dry inverted bay remains clear for a moving observation/sensor
   module under a rectilinear tile layout.
7. The OT-2 deck remains a dry kinematic reference, not an incubator wall or
   heater.

The working liquid-access target is +1.5 mm X from the well center. That keeps
the well center available for inverted imaging while leaving the first PoC with
an offset sweep of center, +1.0, +1.5, and +2.0 mm.

The broader hardware stance is captured in
[hardware systems lessons](hardware_systems_lessons.md). Aevum should be treated
as an incubated, registered, observable, robotic plate instrument, not as an
OT-2 accessory. The recurring hardware rule is to separate authority for
datums, seals, thermal paths, flow, optics, biology, and motion so no prototype
geometry quietly becomes calibration truth.

## Environmental Tile Contract

The tile is not just a deck fixture under a plate. It is a registered plate cell
inside a larger row-level environmental machine. It has to satisfy the OT-2
coordinate system, the observation-module coordinate system, and the row
headspace interface without breaking adjacency to neighboring tiles.

Required tile interfaces:

- per-plate OT-2 deck-space engagement so each tile seats into a known deck
  plate space rather than relying on one long floating bridge;
- standard-plate footprint discipline so neighboring tiles can share the same
  observation bay without side-frame interference;
- plate support and lateral registration that contact the plate frame/skirt/rim,
  not the glass observation region;
- local heat paths, temperature sensing where useful, module identity, wiring,
  and fail-state evidence;
- a sealed or sealable interface to the row headspace/lid/rim with
  hard-stop-limited gasket compression;
- pipette access through a septum, mat, port, or lid feature without consuming
  the central imaging region;
- a clear dry-bay aperture and objective/sensor keepout under the glass-bottom
  plate;
- fiducials or datum features usable by the OT-2 registration workflow and the
  moving observation module;
- service exits that do not cross pipette paths, cassette locators, deck-contact
  faces, observation apertures, or adjacent tile envelopes.

The observer-side requirement is as important as the OT-2 requirement. A
sensor-suite module moving at useful speeds under the array needs a stiff,
repeatable bay frame, predictable tile-to-tile aperture geometry, and local
fiducials to correct residual print, assembly, and thermal error. Tile
registration is therefore dual-use: it must preserve pipette targeting and
observer targeting.

The OT-2 side of that registration is also per-tile. A row module may have a
shared lid and shared dry bay, but its deck interface should still click into or
otherwise positively seat at each plate space so row pitch, yaw, rocking, and
service reinstall error stay measurable.

The dry bay should be modeled as a swept keepout and datum corridor early, even
before the observer carriage exists. Aperture holes alone do not protect the
future objective, illumination, wiring, spill boundary, or service-routing
clearance.

For Raman spectroscopy and broader biophotonics, the dry bay should be budgeted
as a moving robotics corridor, not only an optical hole. The preferred split is
to carry a compact front-end observer head in the bay and offload bulky or
heat-generating laser, spectrometer, detector, and control hardware outside the
swept volume. The bay needs explicit allowances for carriage stiffness, focus
travel, cable/fiber bend radius, homing, fiducial viewing, baffles, vibration
paths, and service recovery.

## Row-Shared Headspace

The atmospheric-control unit is a row of four plate modules, not a single plate
tile. CO2 sensing, humidity generation, gas mixing, pressure relief, and the
main supply/return plumbing should live in a row lid, row manifold, or adjacent
row service module. A single tile may still carry local temperature sensing or
heater interfaces, but it should not be expected to package a complete CO2/RH
control stack inside one standard-plate footprint.

The shared row headspace is now an explicit design object:

```text
row supply / conditioning / sensing
  -> low-velocity distribution plenum
  -> four-plate shared headspace
  -> balanced return / exhaust / relief path
```

Distribution must be even and quiet. The control air should refresh the row
without creating visible well-surface disturbance, droplets, local evaporation
hot spots, condensation jets, or pressure pulses at septum punctures.

Design implications:

- use a generous plenum, diffuser, porous section, perforated baffle, or
  distributed slots so gas enters as a low-velocity sheet rather than a jet;
- separate supply and return enough to avoid short-circuit flow, but keep both
  paths outside pipette access and observer keepouts;
- equalize pressure drops across the four plate positions with symmetric
  manifolds, restrictors, or calibrated orifices;
- place the CO2/RH sensor in a representative row return or mixed sampling path,
  not in a stagnant corner or a direct supply jet;
- keep recirculation and active mixing upstream of the plate volume where
  turbulence cannot disturb wells;
- make the row lid/manifold removable and keyed so tile registration and gasket
  compression are repeatable after service;
- treat the row as one atmospheric domain for contamination, condensation,
  recovery time, and evidence until later isolation features are proven.

The PoC needs evidence for flow distribution before live-cell assumptions are
made: smoke or fog visualization, dye/water surface disturbance checks, humidity
step response at all four plate positions, CO2 step response or tracer
equivalent, condensation inspection, and recovery after pipette access.

## Contiguous SBS Plate Constraint

The core engineering problem is a tiled-plate platform, not a single plate with
free space around it. Conventional SBS plates are already close to the OT-2 slot
envelope, and neighboring plate modules may need to sit contiguously. Therefore
the system cannot depend on external side frames, sidecar clamps, or service
features that protrude into adjacent plate space.

The footprint may exceed a nominal OT-2 slot only where it does not prevent a
rectilinear plate array or the observation module's travel envelope. No thermal
part, gas fitting, gasket carrier, latch, sensor boss, cable strain relief, or
optical-bay feature should become a side protrusion that makes tiling impossible.

Design consequences:

- plate support must live under the plate footprint;
- thermal and environmental control should be dominated by a conditioned
  row headspace/lid/rim stack, with the under-plate support interface acting as
  a support datum and secondary thermal spreader rather than the only heater;
- the lateral deck datum must remain a one-slot object even when the real plate
  envelope slightly exceeds the nominal SBS slot;
- the lower OT-2 interface must use per-slot shoes and deck-frame keepouts, not
  a continuous baseplate or tall supports above an abstract deck plane;
- contiguous modules must preserve plate-to-plate adjacency, so wet services,
  dry optics, wiring, and gas routing exit vertically, underneath, through the
  lid, or through separate one-slot service modules;
- environmental control should be treated as a plate-top and under-plate stack,
  not as a frame wrapped around the outside of a plate;
- any future heater, gasket, clamp, or lid feature must prove it supports the
  plate without consuming the neighboring plate envelope.

Preferred thermal architecture:

```text
heated/conditioned four-plate row lid and septum/rim
  -> warm humidified low-turbulence CO2 row headspace
  -> culture plate wells across four tiles
  -> supported plate perimeters on tile support interfaces
  -> dry inverted optical bay
```

This is closest to a stage-top incubator and avoids overloading the under-plate
perimeter support with all thermal control. That support interface still
matters: it locates the plate, supports puncture loads, provides a controlled
thermal datum, and can carry a heater or sensor. But live-cell stability should
come from a small conditioned row chamber volume above and around the wells,
with lid/rim heating to prevent condensation and low-turbulence gas flow to
maintain CO2/RH.

## Multi-Plate Observer Architecture

The long-term platform is not one incubated plate with a fixed microscope. It is
an array of environmental plate tiles over a shared dry inverted observation
bay. A sensor-suite module moves through that rectilinear bay and visits
registered plates from below, while plate-resident sensors remain on each tile
for modalities that cannot practically rove. The architecture is closer to a
CNC machine with a swappable tool head than to a single benchtop incubator.

Three shared infrastructure layers define the system:

```text
dry rectilinear observer transport
  -> one moving optical/photonic/sensor suite visits registered plate tiles

row environmental envelope
  -> four tiles share controlled CO2/RH headspace while tile heat/support stays local

electrical/data/service interface
  -> plate-resident sensors, heaters, valves, IDs, and safety interlocks plug in
```

Everything experimental should be a module that plugs into those layers:

- plate tiles hold real SBS plates, plate-specific support adapters, local heat
  paths, gasket lands, row-headspace interfaces, and septum/mat access geometry;
- the observation module carries optics, photonics, illumination, and other
  sensors that rove below the glass-bottom plates;
- resident sensor modules stay with a plate when the signal is local, slow, or
  physically coupled, such as temperature, pH/O2 spots, electrodes, impedance,
  flow, lid heating, gas humidity, or valve state;
- service modules provide gas, heat, power, data, waste, and safety interfaces
  without forcing every plate tile to own bulky hardware.

The mechanical bridge should not depend on sidecar frames wrapped around a
plate. The bridge is a tiled datum system:

```text
one-slot deck datum per tile
  -> inter-tile alignment/keying features below or at service edges
  -> common plate-support Z datum
  -> common dry-bay rail, aperture, and keepout conventions
  -> common four-tile row chamber/lid interface
```

Adjacent plates may sit edge-to-edge, but the modules still need a sturdy and
accurate shared coordinate system. The OT-2 deck provides the coarse grid. The
platform must add repeatable local features: kinematic plate support, plate
lateral registration, inter-tile bridge/key geometry, observer fiducials, and
module identity. The observer should use local fiducials on each tile to correct
residual print, assembly, and thermal error before high-resolution observation.

Adjacent fitment remains measurement and service-spacing gated. The repository
does not currently keep a larger-plate CAD branch as standing architecture; the
next design should start from retained plate dimensions, a fresh tile datum, and
explicit neighbor-spacing requirements.

Environmental control follows row discipline. A row of four plates shares a
controlled atmospheric headspace so the CO2/RH sensor, humidification hardware,
mixing volume, and gas plumbing can be sized honestly. Each tile still owns its
support, registration, local heat-transfer interface, identity, and gasket land.
The row lid/manifold owns the shared CO2/RH domain and must distribute air
evenly without turbulence at the wells.

Service features are not wet manifolds by default. The deck fixture can reserve
dry strain-relief and keepout space, but gas, humidity, heat, power, and data
interfaces need their own reviewed stack so they do not consume plate adjacency,
observer access, pipette paths, cassette locators, or deck-contact faces.

Compression and retention are requirements for the next real-plate design, not
implemented geometry in the current CAD. The preferred direction remains
vertical, hard-stop-limited preload into a replaceable seal, with plate-specific
precision handled by swappable support or nest details rather than external side
clamps. Lateral registration should be separated from vertical support and
should be validated from real underside/skirt measurements before close-fitting
hard stops are designed.

## First Physical PoC

The first print is an interaction mule, not a final incubator component. It should test:

- P300 access through a raised cassette envelope.
- Center and off-axis access into 96-well-like geometry.
- Fit of the future lid/mat/headspace stack.
- Whether screwless printed retention is good enough for a first mat-puncture
  and robotic pick/place envelope test.
- The wet-headspace / dry-optical-bay boundary as a mechanical envelope.

It is split into three passive parts: the OT-2 base/tower datum, a removable
mock plate cap, and a removable mat cassette. This keeps the optical-bay
envelope open and avoids slicer-generated supports in the mock wells or bay.
It should not carry active wiring, sensors, heaters, illumination, or a real
optical enclosure. The first print should preserve clear service egress paths
and keepout marks so later modules can route wires, tubes, and optics without
changing the OT-2 registration strategy.

The print is still part of a physical platform, not a disposable reach coupon.
If the physical P300 test shows comfortable Z margin, the next fixture should
spend that margin on a taller under-plate bay envelope. Height is a platform
resource: it creates room for objective clearance, folded optics, drip shielding,
service routing, and future incubator separation. Do not keep the next print
short merely because the first 4 x 4 interaction mule succeeded.

The next hardware object should move toward a one-row
mechanical/environmental coupon: four plate positions or faithful plate dummies,
a removable row lid/manifold, hard-stop gasket compression, low-velocity
supply/return, dry-bay keepout, fiducials, pipette access through the intended
top stack, and service exits that preserve adjacency.

The current 4 x 4 field is a local truth patch for offsets, guide diameters, and
mat/headspace access. It is not the long-term platform footprint. Once the
height and access classes pass, the platform path should split into fresh
design branches:

```text
1. tall 4 x 4 platform mule
   preserves the proven target field while increasing the inverted-bay volume

2. larger chamber/platform mule
   expands the mechanical envelope for real chamber walls, service exits, and
   optical-bay packaging
```

The retained CellVis P96-1.5H-N profile should be used as input data for any
future larger-plate design. Measurement effort should still target unknown
geometry that affects an incubator stack: top rim/gasket land, underside
support/recess geometry, real access behavior, and Cole-Parmer mat plug/slit
dimensions. Do not replace published plate X/Y dimensions with casual caliper
spot checks unless a fixture fit failure requires an explicit override.

## Service Routing And Walls

The platform will eventually need service routing, but the routing belongs to
later modules, not the first printed interaction mule.

Future wet/incubator services:

- sample-stage heater wiring,
- lid/rim heater wiring,
- RTD/thermistor wiring,
- row-level CO2/RH/headspace sensor leads or sampling tube,
- row supply/return/relief gas tubes,
- optional condensate/drain path.

Future dry optical-bay services:

- camera USB/ribbon cable,
- LED/illumination power and control,
- motorized focus/scan wiring,
- observer-stage power, data, and motion-control wiring,
- spectrometer/laser interlocks,
- optional fan/thermal monitoring.

Routing rule:

```text
wet services exit through the incubator/lid module
dry optical services exit through the separate optical bay module
the OT-2 deck fixture remains a dry kinematic datum
no wire or tube should cross a pipette path, cassette locator, well, deck-contact face, observation aperture, or adjacent tile envelope
```

Sidewall rule:

```text
first PoC base: no continuous sidewalls and no under-plate tunnel walls
first PoC mock plate: separate removable cap
first PoC cassette: flat removable access plane only
future incubator: sealed sidewalls/gaskets live in a removable wet chamber module
future optical bay: light-tight sidewalls live in a separate dry bay module
```

For the first 4 x 4 print, the base only needs discrete locator posts for the
removable mock plate cap. Continuous base rails or tall under-plate walls are
still not useful here: they reduce visibility, increase print risk, hide support
defects, and imply a sealed chamber or optical enclosure that this PoC is not
validating.

## Materials And Printability

The full module can be heavily 3D-printed, but printed plastic should not be the
only authority for sealing, registration, thermal uniformity, optics, or
cell-facing compatibility. Printed parts should define architecture: chassis
volume, ducts, baffles, covers, service routing, cassettes, gasket carriers, and
sensor mounts. Replaceable inserts and commercial parts should carry datum
features, gasket compression stops, heat spreading, optical boundaries, tubing,
and incubated headspace compatibility.

The glass-bottom plate is the primary optical window. Any extra window below the
plate is an optical element and should be added only when spill protection,
pressure isolation, or contamination control justifies the penalty.

Detailed material boundaries are in [Materials strategy](materials_strategy.md).

## Modalities To Preserve

The shared dry inverted bay and moving sensor-suite module should eventually
support:

- reflected/epi brightfield and oblique contrast,
- reflection DPC/FPM experiments if useful,
- hyperspectral reflectance/autofluorescence,
- sparse fluorescence/FLIM,
- spontaneous Raman,
- future coherent Raman and mid-IR photothermal ports.

The first print only establishes interaction geometry.

## Control Architecture

The Opentrons App is not the primary control plane for this package. Aevum will
interact with the OT-2 through a package-owned bridge core that talks to the
documented Opentrons HTTP API, uses Python Protocol API concepts for labware and
protocol semantics, and owns safety/state/evidence for physical robot motion.

The bridge must be the single writer through Aevum-controlled paths. LLM agents
may propose plans and request typed actions through adapters such as MCP, but
the bridge core validates fixture geometry, offsets, deck slot, pipette
configuration, and run state before any command is sent to the OT-2. Pipette
configuration is live robot state: first P300 workflows assume
`p300_single_gen2` on the left mount only when that matches current bridge
evidence or a recorded hardware change. Later no-motion spikes observed a
right-mount P20 Gen2, so bridge-controlled motion must not inherit stale P300
defaults.

The target operating mode is unattended autonomy for validated workflows.
Supervised commissioning is a temporary mode used while the printed fixture,
camera evidence gates, registration, and recovery behavior are being proven.
The OT-2 built-in camera is the first autonomy observation channel.

Detailed control context:

- [OT-2 control surfaces](ot2_control_surfaces.md)
- [Agent OT-2 bridge](agent_ot2_bridge.md)
- [Agent interface strategy](agent_interface_strategy.md)
- [OT-2 camera and autonomy](ot2_camera_autonomy.md)
