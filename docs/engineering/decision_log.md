# Decision Log

## 2026-05-02: CadQuery As Primary CAD

Decision: use CadQuery as the master CAD generator.

Reason: the printed geometry, STEP/STL exports, and OT-2 labware JSON can all be
generated from the same parameter set.

## 2026-05-02: First Artifact Is An Interaction Mule

Decision: first print is not a simple reach gauge. It is a screwless raised
interaction PoC section for P300 access, off-axis targets, and future cassette
collision envelope.

Reason: the OT-2 is expected to be capable enough; the unknown is the combined
interaction of raised geometry, mat/cassette envelope, and off-axis pipetting.

## 2026-05-02: P300 Gen2 Is The Initial Compatibility Target

Decision: design and protocol scaffolds target P300 Gen2 workflows first.
Those first workflows assume `p300_single_gen2` on the left mount unless a
newer hardware record explicitly updates the pipette and mount.

Reason: the original compatibility and motion target was P300 access through the
raised fixture. Later no-motion bridge evidence showed a right-mount P20 Gen2
present during subsequent spikes, so current pipette state must be treated as
observed robot state, not as a standing design assumption. The bridge must
verify attached pipettes and mounts before any motion-capable workflow.

## 2026-05-02: Agent Bridge Owns OT-2 Control

Decision: Aevum will not use the Opentrons App as its primary control plane. LLM
agents will interact with the OT-2 through a package-owned bridge that talks to
the Opentrons HTTP API, serializes robot access, validates plans, applies
labware offsets, and records evidence.

Reason: physical robot motion needs one writer through Aevum-controlled paths,
durable command history, fixture-aware safety checks, and agent-native
registration. Direct App workflows, Jupyter notebooks, or arbitrary Python
execution do not provide the right control boundary for multi-agent operation.

## 2026-05-02: Bridge Core Before Adapters

Decision: implement the OT-2 integration as a stateful bridge core with sessions,
locking, validation, offset registry, and evidence writing before choosing MCP,
local HTTP, or CLI as the primary adapter.

Reason: adapters are transport surfaces for clients. They should not own robot
state or safety policy. A small MCP surface is likely useful for LLM agents, but
it should expose workflow-level session operations rather than raw OT-2 commands.

## 2026-05-02: Unattended Autonomy Is The Target

Decision: Aevum's target operating mode is unattended autonomy for validated
workflows. Supervised commissioning is a temporary phase for the first fixture
and unproven target classes.

Reason: the OT-2 includes a built-in camera that can provide machine evidence
for deck state, fixture presence, high-Z approaches, and run audit records. Until
camera gates and recovery behavior are validated, human observation may be used
as a commissioning fallback, but it is not the product architecture.

## 2026-05-02: Live Control Uses A Single Local Daemon

Decision: live robot motion should go through one local bridge daemon. MCP,
local HTTP, and CLI adapters should be clients of that daemon for motion-capable
operations.

Reason: separate adapter processes cannot safely share in-memory session state.
A daemon makes the ownership boundary explicit while SQLite persists lock,
session, offset, and recovery state for crash handling.

## 2026-05-02: Task Graph Is The Coordination Surface

Decision: Aevum should treat the repository task graph and implementation
trajectory as the coordination surface. Engineering lanes are package
components, not agent ownership boundaries.

Reason: conversational handoffs between agents are too expensive for the pace of
fixture commissioning. The durable docs should define dependencies, blockers,
exit criteria, and stop conditions clearly enough that one agent can own all
lanes without duplicating or bypassing safety-critical work.

## 2026-05-05: Chamber-First Thermal Architecture

Decision: the preferred plate-mode incubator architecture is chamber-first. The
under-plate support interface locates the plate and may act as a secondary
thermal spreader, but live-cell temperature, humidity, CO2 stability, and
condensation control should be dominated by a heated lid/rim/septum plane and
warm humidified headspace. Later row-level packaging keeps this principle but
shares the atmospheric headspace across four adjacent tiles.

Reason: conventional SBS plates leave almost no lateral room for external
support or heating frames, especially when plates must be contiguous. Perimeter
heating through a plastic plate skirt alone is unlikely to guarantee
sample-plane uniformity. A compact stage-top-style row headspace stack preserves
the contiguous plate envelope while putting thermal and gas control where the
cells actually are.

## 2026-05-05: Multi-Plate Observer Platform

Decision: the long-term instrument is a tiled plate platform with one roving
observer, not a fixed microscope under one isolated plate. Plate-resident
sensors remain on the tile for modalities that cannot rove. The shared platform
layers are dry rectilinear observer transport, row-shared atmospheric envelope
with tile-local support/thermal interfaces, and electrical/data service
interfaces.

Reason: multiple plates must be sturdy, accurately registered, and reliable as
a row or grid while preserving contiguous SBS plate adjacency. The tile support
interface should support the real plate, define observer aperture and keepout,
land the chamber/lid stack, and provide future bridge geometry for adjacent
tiles. Experimental hardware should plug into these shared interfaces instead
of forcing one-off side frames around each plate.

## 2026-05-06: Row-Shared Environmental Module

Decision: the next hardware architecture target is a row-shared environmental
module, not merely a raised OT-2 deck cartridge and not a fully independent
CO2/RH system per plate. Each tile holds a glass-bottom SBS plate, owns support,
registration, local heat-transfer interfaces, pipette access, and the aperture
to the shared dry inverted observation bay. A row of four tiles shares one
controlled atmospheric headspace for CO2 and humidity.

Reason: the platform has two precision clients: the OT-2 pipette and the moving
observation/sensor-suite module. Both need a stable tile datum and local
fiducials, while neighboring tiles need to remain contiguous. Side protrusions,
casual service fittings, or single-tile optical assumptions would break the
rectilinear observation bay and make high-speed observer registration fragile.
A practical CO2 sensor, humidification path, mixing volume, and gas plumbing are
too large to package honestly inside every standard-plate-footprint tile.

## 2026-05-06: Low-Turbulence Row Headspace

Decision: the four-plate row headspace must distribute conditioned air evenly
without turbulent jets over the wells. CO2/RH sensing should be row-level, in a
representative return or mixed sampling path, while recirculation and active
mixing should happen upstream of the plate volume.

Reason: shared atmosphere solves the component-placement problem but creates a
flow-quality problem. Uneven or turbulent delivery can cause local evaporation,
condensation jets, droplet movement, pressure pulses during septum puncture,
and inconsistent CO2/RH across plates. The row module therefore needs diffuser,
plenum, restrictor, and return-path evidence before live-cell assumptions are
made.

## 2026-05-06: Printed Architecture With Authority Inserts

Decision: 3D printing is the preferred way to prototype module volume,
packaging, ducts, baffles, covers, cassettes, and carriers, but not the sole
source of datum, sealing, thermal, optical, biological, or flow authority. The
row-module PoC should combine printed ASA/PC/PA12-class parts with metal datums
and thermal spreaders, elastomer seals, glass-bottom plates, inert tubing, COTS
sensors, diffusers, and replaceable inserts.

Reason: warm humidified CO2, gasket compression, low-turbulence row flow,
high-speed observer alignment, sample-plane thermal stability, and cell-facing
compatibility exceed what unvalidated printed plastic should be trusted to
provide. Printed parts should make the architecture testable while inserts and
commercial materials carry the interfaces that must remain accurate, sealed,
clean, quiet, and calibratable.

## 2026-05-16: Hardware Authority Separation

Decision: treat Aevum as an incubated, registered, observable, robotic plate
instrument rather than an OT-2 accessory. Hardware design should separate datum,
seal, thermal, flow, optical, biological, and motion authority, and every
authority-bearing physical claim should be cheap to revalidate after assembly,
service, heat, humidity, and motion.

Reason: adjacent instrument families show that systems like this usually fail
through quiet coupling between subsystems: gaskets become thermal paths, side
fittings break tiling, airflow creates evaporation bias, printed carriers become
calibration assumptions, and service actions invalidate registration. The next
hardware object should therefore be a one-row mechanical/environmental coupon
that proves interface coexistence before the design tries to become a full
incubator.

## 2026-05-16: No Standalone Headspace Spacer

Decision: the row module should not use a separate headspace spacer. Headspace
is a controlled empty volume owned by the lid/manifold and its underside relief,
while seal compression is owned by a thin replaceable gasket or septum plus
hard stops integrated into the lid/base datum architecture.

Reason: a removable spacer adds an avoidable tolerance stack, leak path,
cleaning burden, assembly state, condensation surface, and service event. It
also risks teaching the wrong authority model: the final design needs the lid,
seal, hard stops, and plate datum to define headspace and compression directly.
The one-row coupon now represents the gasket and headspace volume separately so
the CAD distinguishes material from controlled void.

## 2026-05-17: Dry Bay As Observer Corridor

Decision: represent the dry bay as a protected observer corridor, not merely as
four plate aperture holes. The coupon should show a reference swept volume below
the row, boundary/rail references outside that sweep, and underside observer
fiducials around each aperture while keeping these references separate from the
manufactured stack envelope.

Reason: the moving inverted observer is a precision client of the hardware. It
needs predictable clear volume, local registration marks, and routing exclusion
as much as the OT-2 needs pipette clearance. If the dry bay stays implicit, late
tubes, wires, clips, baffles, spill barriers, or glossy surfaces can silently
pollute the optical/mechanical path.

## 2026-05-17: Per-Plate OT-2 Deck Engagement

Decision: the row coupon should not float over the OT-2 as one abstract slab.
Each plate position needs its own deck-space engagement reference so the row
indexes into the OT-2 deck as four plate-addressable spaces while preserving a
clear dry observer bay between the deck plane and the plate support plane.

Reason: the OT-2 deck remains the dry kinematic reference for pipette targeting.
If the row module only registers as one long bridge, pitch, yaw, rocking, and
service reinstall error can accumulate across the row. Per-plate engagement
features make deck seating, row straightness, and remove/reinstall repeatability
measurable before the final latch or clip mechanism is chosen.

## 2026-05-17: Per-Slot Deck Shoes And Frame Keepouts

Decision: the one-row coupon must not use a continuous lower baseplate at the
OT-2 deck plane. The OT-2 deck frames every plate position with machined
aluminum ribs, so the deck-contact geometry should be four per-slot shoes
inset inside the slot openings, plus explicit deck-frame keepout references.

Reason: standoff pillars alone reserve vertical space but do not prove seating
on the real deck, and a continuous bottom plate collides with the aluminum deck
frame. A row module must sit on the same mechanical reality as a plate: slot
openings, rib contact, clip pressure, local protrusions, and remove/reinstall
repeatability. Modeling slot shoes and frame keepouts now prevents the observer
bay from becoming a beautiful but unseatable bridge.

## 2026-05-17: 80 mm Dry Bay Exploration Budget

Decision: use an 80 mm dry-bay height for the next one-row coupon variant. The
bay should include reference envelopes for a moving observer head and side
service raceway, while keeping the full deck-to-top stack near 123 mm with the
lower OT-2 slot shoes included.

Reason: Raman spectroscopy and biophotonics need more than a simple objective
keepout. The dry bay must reserve volume for a front-end optical head, focus
axis, folded pickup, baffles, fiducial viewing, cable/fiber service loops,
strain relief, and motion clearances. Larger heat-generating or bulky elements
such as laser sources, spectrometers, detectors, and controllers should remain
offloaded from the swept bay unless later evidence proves they can ride on the
carriage without compromising vibration, heat, or OT-2 clearance.

## 2026-05-17: Explicit Wet Chamber Barrier

Decision: the coupon should treat the row headspace as a biology-facing
environmental volume with an explicit boundary, seal compression region,
conditioned-gas supply, return, sampling, and pressure-relief paths. Headspace
should not appear as only a transparent void under a generic cap.

Reason: the biological client needs a controlled atmosphere, not merely
clearance. The CAD must make the wet/dry boundary, gasket compression region,
diffuser path, return path, and service ports visible early enough that optical
bay hardware, pipette access, condensation management, and OT-2 deck fitment do
not compete invisibly.

## 2026-05-18: COTS Round Pre-Slit Septum Mat

Decision: use the Cole-Parmer EW-12920-06 round pre-slit silicone 96-well mat as
the coupon's all-well pipette access reference, not a square-plug mat or custom
96-port lid. The mat should be modeled as a replaceable per-plate consumable
captured by the lid/skirt/gasket stack. The lid/manifold must leave the septum
well field open so the OT-2 approaches exposed pre-slit silicone, not a solid
lid roof.

Reason: a COTS round-plug pre-slit mat gives a real liquid-handler access layer
for all 96 wells without forcing the coupon to invent a fragile 96-port sealing
system. It still does not replace the outer wet-chamber barrier: the mat seals
well access, while the chamber skirt/gasket defines the row-level environmental
boundary. A solid manifold over the mat would defeat the access layer and hide
the key liquid-handler interface we need to validate.

## 2026-05-18: Reject Pipette Chimneys

Decision: pipette access must not become a set of rigid well-by-well chimney
volumes. The row chamber remains one shared atmospheric volume with an outer
skirt/gasket and a continuous underside relief across all four plate positions.
The septum mat is the pierceable liquid-handler interface; it is not a 96-port
gas manifold and should not partition the row headspace into isolated wells or
isolated plates in the coupon model.

Reason: chimney-like access volumes add dead volume, condensation surfaces,
evaporation gradients, pressure pulses, and geometry that is hard to clean or
validate. More importantly, they obscure the core environmental requirement: the
four plates must experience one conditioned row headspace through lateral
supply, return, sampling, and pressure relief paths. The coupon should make that
claim visually and testably explicit before biology experiments depend on it.

## 2026-05-18: Septum Mats Are Serviceable Inserts

Decision: the coupon should model the Cole-Parmer round pre-slit mats as
installed, swappable consumables rather than abstract well-target references.
Each plate position carries one physical mat insert with sheet, round plug, and
slit-mark geometry. The lid/manifold provides shallow underside seat pockets and
local pick-relief notches so the assembly communicates insertion, compression,
inspection, and replacement.

Reason: biology workflows will require mat replacement after puncture wear,
contamination, swelling, failed seating, or plate service. A pure well-grid
reference hides the real service operation and can lead to a design that has no
path for removing a sticky silicone mat, no way to inspect seating, and no
clear compression datum. The PoC should force these mechanics into view while
keeping the shared headspace and all-well OT-2 access intact.

## 2026-05-18: Keep References Out Of The Primary CAD View

Decision: the CQ-Editor viewer should show only installed physical parts as
separate objects.
Validation reference builders may remain inside tests for geometric assertions,
but deck keepouts, dry bay swept volumes, observer envelopes, and headspace
control volumes should not be exported by the default row-coupon generator or
appear in the primary CAD scene.

Reason: reference bodies are evidence geometry, not build geometry. Showing them
by default makes the coupon look like a pile of abstract overlays and obscures
which solids are intended to be fabricated, bought, inserted, compressed, or
serviced. Keeping them out of the primary viewer and default output directory
makes the CAD represent the assembly we are actually designing, while showing
parts separately preserves assembly, replacement, and manufacturing intent.

## 2026-05-18: Row Coupon Needs A Removable Wet-Chamber Skirt

Decision: the one-row coupon should not show exposed plates sitting between a
base and a lid. The installed stack needs a physical side boundary: a removable
wet-chamber skirt that is installed after plates are loaded top-down into the
base nests, then sealed by the lid/manifold and gasket stack. The consumable
microplates should also be rendered as plate sidewalls/window bodies rather
than simple solid blocks.

Reason: chamber-first incubation requires a contained humidified CO2 volume, not
only pipette access through septa. If the plate row has no side boundary, the
model quietly assumes away leakage, thermal gradients, evaporation gradients,
condensation paths, cleaning access, and service order. If the side boundary is
fixed to the base, plate insertion and recovery become fragile. A removable
skirt keeps service honest while making the incubated wet boundary, seal
surfaces, and future leak/flow tests visible in CAD.

## 2026-05-18: Wet-Chamber Boundary Runs To The Row Envelope

Decision: the removable wet-chamber skirt is a full-footprint environmental
frame, not a small collar around the plate pack. Its outer boundary follows the
base/lid row envelope, and its side margins are treated as real service lanes
for supply/return routing, representative sensor ports, sampling/relief, and
future drains or condensation management.

Reason: a plate-local skirt hides the hard part of the product. It leaves the
gas path, sensor placement, leak path, and service routing as afterthoughts
while making the CAD look more resolved than the architecture is. A full-row
frame forces routing, sealing, pipette access, plate service, dry-bay isolation,
and no-side-protrusion constraints to be negotiated in the same geometry.

## 2026-05-21: Deck Feet Must Not Consume Observer Sweep

Decision: row-coupon standoff feet should be driven to the OT-2 slot-edge
perimeter and validated as keepout geometry against the dry-bay observer sweep.
The foot rectangles are now layout data, and tests fail if a foot is outside
the OT-2 slot opening or overlaps the modeled observer rectangle.

Reason: a large sensor module cannot be protected by visual inspection of the
CAD. The observer problem is a swept-volume problem: every well center must be
reachable with the module body, focus axis, fibers/cables, and recovery path
included. Feet that sit comfortably under a plate can still become the hidden
limit on imaging all wells.

## 2026-05-21: Lid Compression Stops Follow The Row Axis

Decision: lid hard-stop pads are now generated from the row axis. For the
four-plate column, stops are mirrored on the left and right perimeter rails and
placed at the row ends plus each inter-plate seam.

Reason: the earlier stop computation reused the horizontal-row seam formula for
a vertical OT-2 column, creating repeated stop positions near one X coordinate.
That made the CAD look like it had hard stops while failing to support the
actual full-row gasket and removable wet-chamber frame.

## 2026-05-22: Row Module Path Is Print-Native

Decision: the path to the real row module should avoid metal inserts, metal
fasteners, springs, glue, adhesives, solvent welding, thermal staking,
permanent welds, and hidden bonded authority parts. The assembly should be made
from printed structural parts, printed latch/compression features, printed seal
carriers or printed flexible seals, COTS plates, and COTS septum mats.

Reason: the coupon is meant to mirror the actual device assemblage. If the
prototype relies on metal hardware, glued inserts, adhesive bonds, or a
monolithic print that would not exist in the final device, it may validate the
wrong force paths, service paths, failure modes, and tolerances. A print-native
stack makes the hard parts visible: deck fit, plate support, dry-bay clearance,
chamber frame, gasket capture, printed wedge/cam compression, lid routing, and
service order.

## 2026-05-25: Row Coupon Matches Production Assembly Tree

Decision: the default one-row coupon CAD, exports, and CQ-Editor scene should
use production assembly units rather than collapsed placeholders. The installed
tree is deck pods, plate-support frame, lower gasket, wet-chamber frame, COTS
microplates, COTS septum mats, upper gasket, lid-manifold shell, lid cover, and
printed wedge locks.

Reason: a production-like coupon should validate assembly order and service
order, not only envelope coexistence. Separate named parts force the design to
show which objects are printed, which are consumables, where seal compression
is carried, where the lid/manifold splits for printability, and how no-metal,
no-glue compression will be represented before the biology or sensing claims
depend on it.

## 2026-05-25: Row Coupon Revisions Use A Do-Review Hypergraph

Decision: row-coupon CAD work should advance through explicit do-review-context
hyperedges rather than isolated CAD tasks. A revision is closed only when the
geometry, tests, generated artifacts, CQ-Editor scene, design documents, and
remaining mechanical gaps are updated together.

Reason: the coupon is being used to make physical claims about production
assembly behavior. If CAD changes, validation evidence, and durable context move
separately, the project can accidentally accept symbolic geometry as real
mechanical function. Hyperedges keep each claim tied to the parts that carry it,
the evidence that reviewed it, and the next unresolved interface.

## 2026-05-25: CAD Closure Is Distinct From Physical Closure

Decision: the RH1-RH9 row-coupon hyperedges may close at CAD level when they
have owned geometry, focused tests, generated artifacts, viewer support, and
updated context, but print, leak, compression, humid exposure, service cycling,
and observer kinematic evidence remain separate RP-cycle tasks.

Reason: CadQuery can prove ownership, envelope discipline, part identity, and
some collision properties. It cannot prove printed friction, gasket squeeze,
duct leakage, humid release, condensation behavior, material creep, or repeated
assembly wear. The row coupon therefore records CAD closure and physical closure
as different engineering states.

## 2026-05-25: Missing-Gap Audit Extends The Row Coupon Graph

Decision: the row-coupon graph now explicitly tracks additional missing domains:
COTS consumable metrology, liquid-handler puncture mechanics, thermal and
evaporation authority, pressure relief, spill isolation, BSL1 material and
cleaning compatibility, optical quality, row tiling, service interfaces, and
fail-closed assembly-state inspection.

Reason: the first RH1-RH9 pass made the mechanical part interfaces much more
honest, but it still left several product-critical failure modes outside the
closure loop. Those domains cannot be implied by a clean CAD stack. They need
their own geometry, measurement, physical evidence, or explicit blocked claims.

## 2026-05-25: RH10/RH11 Need Physical Consumable And Puncture Evidence

Decision: the one-row coupon now uses the persisted CellVis published footprint
for the COTS plate body, adds printed lateral locator rails around each plate,
exports a separate consumable metrology gauge, and exposes an optional all-96
pipette puncture swept-path check in the viewer.

Reason: all-96 access through a pre-slit silicone mat is not only an open-lid
clearance problem. The real risk is whether the COTS mat seats, swells, reseals,
and tolerates repeated puncture without moving the plate or biasing liquid
handling. The CAD can now point to those risks, but it does not close them until
physical mat metrology and puncture tests exist.

## 2026-05-26: Latches Are Assembled Print-Native Parts, Not Print-In-Place

Decision: the row coupon should realize lid compression with printed wet-frame
tension posts/caps, lid-owned receiver rails, and removable side-insert printed
wedges. The latch is assembled from inspectable printed parts; it is not a
print-in-place captive mechanism.

Reason: the latch lives next to wet biology, silicone mats, humid gas, and
service ports. A hidden captive slider would be hard to clean, dry, inspect,
measure for creep/wear, or replace after failure. Separate printed latch parts
mirror production service order: load plates and mats, install the wet frame and
lid, slide wedges around the printed posts, inspect lock state, then remove and
replace worn wedges without destroying the coupon.

Update: the coupon latch CAD now encodes that service order with explicit
lead-in ramps, high bearing flats under post caps, low-tail receiver capture
lips, insertion stops, release ears, detent bumps, raised witness stripes, and
reinforced post roots. These features close the CAD mechanism gate for a first
latch print, but they do not replace physical insertion-force,
retained-compression, wet-cycle, wear, or leak evidence.

## 2026-05-26: Latch Mechanical Screens Are First-Print Gates, Not Validation

Decision: the row coupon layout must expose production-derived latch mechanical
screens before the first latch print: compression budget, ramp self-lock or
backdrive margin, post/cap/root stress screen, and latch-station asymmetry.

Reason: a clean printed latch shape can still fail through tolerance stack,
gasket over-compression, wet backdrive, post creep, cap wear, receiver-lip wear,
or an omitted station near a service port. These risks need to be visible in
layout data and tests before slicer or bench work starts.

Update: the current CAD passes the compression and nominal post-stress screens,
but the ramp self-lock margin is thin and the omitted port-side station creates
an explicit span warning. Physical validation remains blocked until printed
latch and compression-stack coupons measure insertion force, release force,
retained compression, humid cycling, wear, and leak/smoke/fog behavior.

## 2026-05-28: Power Section Uses COTS Authority Via Explicit Design Exception

Decision: the production prototype's power section, AC mains to DC distribution
to subsystem rails, is composed entirely of commercial off-the-shelf
authority-bearing parts. This is the first deliberate departure from the
print-native discipline that governs the row coupon. The exception is scoped
to a discrete physical block (the power enclosure plus its umbilical) and is
documented in detail in `docs/engineering/power_section.md`.

The authority boundary is the umbilical interface: GX16 aviation connectors
between the power enclosure and the row module's lid manifold. On the
umbilical's row-module side, print-native discipline resumes. On the
umbilical's PSU side, commercial authority governs.

Reason: no printed plastic can provide power conversion, regulation,
galvanic isolation, surge clamping, sensing accuracy, or sourced load current
with the precision biology and observation require. Per materials strategy,
"any future return to metal inserts, metal stops, commercial compression
parts, or bonded authority must be recorded as an explicit design exception
with its own evidence and service model." The power section is precisely such
an exception, and the umbilical is the physical line that prevents the
exception from creeping into the print-native mechanical assembly.

The reference architecture is a genuine MeanWell HRP-150-24 (24 V, 150 W,
fanless to ~80 W) feeding through a fused +24 V trunk, with isolated MeanWell
DDR-30G-12 and DDR-15G-5 modules producing the +12 V and +5 V rails. Layered
protection includes a ceramic AC fuse, a 10D471K MOV across mains, a ceramic
DC trunk fuse, P6KE24A TVS at each subsystem entry, 1N4007 flyback diodes on
solenoid coils, and a polyimide heater thermal fuse with independent safety
MCU enable.

Counterfeit identification is treated as the highest-leverage quality check
in the build because a fake MeanWell, Sensirion, or Vishay part is
indistinguishable from genuine at install time but corrupts every downstream
measurement and safety claim once running.

## 2026-05-28: Counterfeit Authentication Is A Required Receiving Step

Decision: every authority-bearing component (PSU, environmental sensors,
TVS/MOV protection, heaters) must be authenticated on receipt before
installation. The authentication protocol per part is documented in
`docs/engineering/power_section.md` under "Counterfeit Identification."

Reason: counterfeit MeanWell, Sensirion, and Vishay parts are widely
distributed on Taobao, and the unit-price savings are dwarfed by the
debugging cost when a fake part produces plausible-looking but incorrect
readings or fails open under transient stress. The cost of debugging a
counterfeit failure is 10..100x the cost of authentication at receiving. The
MeanWell knockoff brand `明伟` is deliberately phonetically identical to the
genuine `明纬`, with one character substituted; this kind of trap is the
default state of the parts market, not the exception, and protocol-level
discipline is required to avoid it.

## 2026-05-31: Service Ports Need Production Interfaces

Decision: the one-row coupon should not represent gas, sample, relief, or sensor
services as anonymous open cylinders. The default production CAD now role-types
the vertical ports and installs separate printed port caps/plugs with seal-land
and witness geometry.

Reason: service ports are part of the production assembly and failure model. A
bare boss can hide missing caps, wrong adapters, tubing strain, fitting capture,
pressure-test access, and sensor installation state. Modeling caps/plugs as
separate printed service parts makes capped/installed state visible before any
flow, leak, or environmental claims are allowed.

Update: final tubing, filters, sensors, pressure taps, and any COTS fittings
remain PF3/PF9 work. They must be represented as filament-printable adapters or
explicit non-filament exceptions with exact envelopes and printed capture/seal
geometry.

## 2026-05-31: Dry Bay Protection Needs Physical Failure Paths

Decision: the one-row coupon should not represent dry-bay protection as only a
clearance envelope below the plate. The default production CAD now prints raised
threshold lips around each optical aperture and cuts shallow wet/dry witness
gutters outside those lips in the plate-support frame.

Reason: the observer bay is where optics, cables, sensors, and electronics will
eventually live. A leak or condensate path that reaches an aperture before
becoming visible corrupts the dry-bay premise. Physical threshold and gutter
geometry gives the CAD a first fail-visible wet/dry boundary instead of a clean
but silent open hole.

Update: gutter capacity, drain/catch sizing, optical shielding, and exact
observer electronics isolation remain PF4/PF6 work.

## 2026-05-31: Sensor Selection Corrected From SCD41 To STC31

Decision: the row module's CO2 measurement sensor is the Sensirion STC31
(thermal conductivity, 0..100% CO2 range, accurate region 0..25%), not the
Sensirion SCD41 (NDIR, 400..40,000 ppm = 0..4% range) originally listed in
earlier sourcing notes.

Reason: mammalian cell culture targets 5% CO2 (50,000 ppm), which is above
the SCD41's competent range. SCD41 saturates and reports incorrect or clipped
values at cell-culture CO2 levels. The STC31 covers the entire 0..25% range
with consistent accuracy and is Sensirion's designated sensor for industrial
process gas monitoring including incubator-class applications.

The STC31 requires colocated RH/T compensation from a SHT41 within 5 mm; the
pairing is mandatory per Sensirion's reference design. The SHT41 was already
in the sensor list for per-plate humidity sampling, but two additional SHT41s
are now required (one per STC31, on the sensor PCBs).

The SCD41 may retain a future role as an ambient-air monitor or chamber-leak
detector for the lab itself, since at atmospheric CO2 concentrations (~420
ppm) it is more accurate than the STC31. That role is optional and not on
the first build.

This is a correction of an earlier sourcing recommendation, caught during
application-level review rather than via failed evidence. Documented per
the project's discipline of preserving errors and corrections alongside
final decisions.

## 2026-05-31: Sensor PCB Designed And Fabricated For Production Prototype

Decision: the row module's CO2 and humidity/temperature sensors are mounted
on a custom-designed printed circuit board, fabricated via JLCPCB with
PCBA assembly, rather than installed as commercial development modules.
One PCB design serves both supply-path and return-path sensor positions
(2 populated boards needed; 5 fabricated per batch for spares).

Reason: dev-module breakouts cannot guarantee sensor placement relative to
the gas channel, cannot guarantee STC31-SHT41 colocation distance under 5
mm, and introduce contamination harbors (exposed solder, DuPont headers)
incompatible with wet biology cleanliness. A custom PCB integrates with
the row coupon's printed gas plumbing geometry at a defined mechanical
interface and aligns the STC31's gas aperture with the row module's
channel cross-section.

The sensor PCB is the second COTS-authority exception under the materials
strategy rule, scoped to a discrete physical object (the PCB) with a
defined boundary (the GX16-6 umbilical on one side, printed mount features
in the row coupon on the other). It does not violate the print-native
discipline of the row coupon's mechanical assembly.

The full design specification, fab workflow, component sourcing path,
authentication protocol, validation protocol, and service operations are
documented in `docs/engineering/sensor_pcb.md`.

The row coupon CAD now carries supply-path and return-path sensor
pockets with printed screwless retention and channel-aligned gas
apertures. PCB holes or notches may support printed alignment and
retention, but metal screws are not part of the row-module production
intent unless a separate materials-strategy exception is recorded.

## 2026-05-31: Sample-Plane Temperature Is A Distinct Measurement

Decision: the row module's thermal sensing inventory must include
sample-plane (cell-contact) temperature sensors, distinct from the
headspace air temperature measured by the per-plate SHT41 sensors.
Sensing is **non-contact, from the row-module side below the plate**,
using MLX90614ESF-DCH (Melexis) IR thermopiles aimed up through
dedicated plate-margin IR apertures at each plate's underside.

Reason: cells live on the glass-bottom plate surface, not in the
headspace gas. Headspace air temperature can differ from cell-contact
temperature by 1..3°C depending on chamber design, heater placement, and
condensation behavior. For cell biology validity, the cell-contact
temperature is the controlled variable; headspace temperature is a
proxy that the heater control loop uses but must not be the only
measurement of record. The architecture documentation already requires
"thermal response at headspace, rim, plate support, and near the
glass-bottom sample plane"; the sensor inventory must match.

**Constraint**: the CellVis plate is a removable consumable. Nothing
may be adhered, taped, glued, or mechanically fastened to the plate.
The plate must seat freely into the printed support frame, lift out
freely for replacement, remain undamaged through repeated install/
remove cycles, and accept no labels or instrumentation. All sensing
must come from the row-module side, not the plate side.

Approach: IR thermopile mounted in the row module's printed support
frame, aimed up through a dedicated plate-margin aperture that is
separate from the central observer aperture, reads the glass bottom's
outer surface temperature. Glass has emissivity ~0.95 (matches MLX90614
default), and the thermal gradient through 1.7 mm of glass at typical
incubator heat flux is ~0.1°C, so the measured glass-surface temperature
is a very good proxy for cell-contact temperature.

Four sample-plane sensors total (one per plate position) are required
for the first row module build. Per-plate independent measurement is
mandatory to validate thermal uniformity across the row.

Bus addressing: MLX90614 default address `0x5A` is fixed by silicon but
the sensor supports a one-time EEPROM rewrite to a different address
via I2C command. At factory test, each of the four sensors is
reprogrammed to a unique address (`0x5A`, `0x5B`, `0x5C`, `0x5D`) so
they share a single I2C channel on the TCA9548A multiplexer without
requiring four separate channels.

**Placement constraint**: each IR sensor must sit in the row module's
support frame in the **plate-margin area**, not under the well-grid
central swept volume. The CellVis plate's well grid spans ~99 x 63 mm
centered on the plate; margins of ~11-14 mm exist on all four sides
between the well grid and the plate footprint edge. An 8 mm TO-39
MLX90614 fits in those margins. Placing the sensor under the well grid
would occlude the observer's line of sight to those wells and violate
the architecture requirement to image every well. The row coupon's
support frame now adds a small IR-sensor aperture per plate position
in the plate-margin area, distinct from the central observer aperture.

**Measurement consequence**: a margin-placed IR sensor reads the plate
underside's edge region, which is thermally closer to the support
frame contact and any frame-resident heater than the central well-area
glass. A one-time edge-to-center thermal characterization (using a
thermal camera, thermocouple grid, or controlled-temperature dummy
plate) maps the offset; runtime cell-area temperature is computed as
IR reading + offset. The characterization is documented in the row
module's validation evidence.

**Future Phase 5 extension**: when the observer carriage subsystem is
built, one MLX90614 mounted on the carriage gives per-well thermal
mapping by sensor positioning, without occlusion (the sensor moves with
the carriage). The four fixed perimeter sensors continue to provide
continuous edge-temperature readout; the two measurements together
characterize both steady-state edge temperature and on-demand well-area
temperature distribution.

Earlier draft of this entry proposed a thin-film PT100 adhered to each
plate's underside; that proposal violated the plate-as-consumable
constraint and was rejected. A subsequent draft placed the IR sensor
"aimed up through the existing dry-bay aperture" without distinguishing
between the central observer aperture and the perimeter IR aperture;
that draft also failed to specify the placement constraint that
preserves observer well access. This entry is the corrected version.

## 2026-05-31: First-Build Sensor Roles Require Real Mount Features

Decision: the row-coupon CAD must realize all first-build sensing roles
as physical, serviceable mount features:

- two supply/return gas-state sensor PCBs, each carrying STC31 CO2 plus
  colocated SHT41 RH/T compensation;
- four per-plate standalone SHT41 RH/T sensors for plate-local headspace
  evidence across the row;
- four per-plate MLX90614 IR thermopiles for sample-plane proxy
  temperature at the plate underside margin.

Reason: the row module's biological claims depend on gas state, local
headspace humidity/air temperature, and plate-underside sample-plane
proxy temperature as distinct measurements. Representing only the
supply/return PCBs and the IR sensors would leave the per-plate
headspace role stranded in the power topology instead of embodied in the
mechanical design.

The row coupon should retain these sensor subassemblies with printed
mechanisms wherever practical: pockets, datum shelves, stops, clips,
wedges, sliding keepers, or covers. Metal fasteners, threaded inserts,
adhesive, or bonded retention remain outside the row-module production
intent unless an explicit materials-strategy exception is recorded.

Current status: the CAD now implements two vertical screwless side
cartridge sockets for the supply/return gas-state PCBs, four screwless
per-plate SHT41 microcarrier sockets exposed to the shared wet
headspace, and four screwless plate-margin IR thermopile pockets in the
plate-support frame. The exported assembly includes the installed sensor
envelopes as separate parts so the sensing roles remain inspectable in
the production scene. The CAD also now includes two physical service-domain
harnesses: a lower dry IR harness with printed snap cover and row-end JST GH
1.25 mm 4-circuit connector geometry, and a removable-lid sensor harness with
covered gas-PCB and SHT41 bus routes, strain-relief rectangles, and printed
keyed connector shrouds.

## 2026-05-31: Bad Assembly States Belong In Opt-In Review CAD

Decision: missing caps, wrong caps, and missing adapters should be explicit CAD
states, but they should not pollute the default production scene or production
export tree. The row-coupon viewer now exposes `port_caps_missing`,
`wrong_port_caps`, and `adapter_missing` as opt-in service/negative view modes.

Reason: a clean installed assembly can hide the exact failures we need to catch
before printing: uncapped ports, wrong cap sizes, and expected adapters that are
not installed. Modeling those as review states makes the failure visible while
preserving the authority of the default production assembly.

Update: the same pattern should be reused for plate, mat, gasket, lid, latch,
wet/dry leak, flow-insert, and observer service states.

## 2026-06-04: First-Print Row Coupon Has No Hidden Authority Parts

Decision: for the one-row coupon first-print path, the 2026-05-06
"Printed Architecture With Authority Inserts" stance is superseded by a stricter
print-native mechanical rule. Printed structural, datum, latch, seal-carrier,
service-retention, and validation bodies must not depend on metal inserts,
metal fasteners, threaded inserts, adhesive bonds, glue, solvent welding,
thermal staking, permanent welds, springs, or hidden bonded authority.

Reason: the current objective is to prove the row coupon as a
production-operating prototype shape, not to hide fragile interfaces behind
unmodeled hardware. The package manifest now carries this decision as a
machine-readable material-authority policy and still allows explicit COTS
consumables, electronics, gaskets, cable assemblies, and tubing as scoped
boundary parts. Any future return to metal, bonded, spring, or commercial
authority inside the row coupon requires a new exception decision, generated
artifact updates, tests, and physical service evidence.

## 2026-06-13: Observation Module Motion Architecture And The Thin-Truck Traverse

Decision: the moving observer is a 3-axis Cartesian micro-scanner — a compact head
indexing Y across the four plates (334.5 mm) on a flat low-profile truck, scanning X
across one plate (99 mm), and focusing Z over the 12 mm stroke on a voice-coil — that
drops into the dry bay as a kinematically-mounted cartridge, runs stop-and-shoot with a
strobed exposure, keeps compute head-side (CSI to a head Pi, Gigabit Ethernet over the
umbilical, never raw USB3 over the moving cable), and takes its authority to move from a
mutually-exclusive lease on the existing OT-2 bridge daemon plus a hardware E-stop
interlock. The full design is `observation_module.md`.

The 44.6 mm carriage-Y-overflow that the CAD swept-volume check flags
(`carriage_traverse_exceeds_dry_bay`, added this session) is a modeling artifact, not a
physical wall: the check sweeps the full 58 mm `carriage_width_y` along the row when only
a ~13 mm-thick truck physically traverses it continuously. The resolution is to
re-parameterize `_observer_carriage_traverse` so `span_y` sweeps the truck dimension, not
the body box (334.5 + 13 = 347.5 < 347.9 mm dry-bay Y → fits with ~0.4 mm margin). This
is CAD/geometry evidence only; it proves the topology can fit, not that a 334.5 mm beam
holds still or traverses repeatably, which remain Gate-6 physical work for Stages 2-3.

Update (2026-06-13, implemented + do->review): the re-parameterization is implemented
(a `gantry_truck_traverse_extent` param swept on the traverse axis), and a do->review
cycle on it surfaced that the Y fix RELOCATED its burden onto the X scan axis. The head
scans the 99 mm column span, so the scan-axis swept extent is `99 + head-X-footprint`
against a 120.2 mm dry-bay X -- leaving only ~0.2 mm of budget, barely the bare objective.
The earlier notion of routing the post-fold camera arm "along the ~120 mm beam X-length"
is geometrically false (the residual after the well span is ~0.2 mm, not 120 mm): the
camera arm cannot ride along X and must be folded coaxially over the objective or taken
offboard. The check now carries an explicit `front_end_scan_axis_footprint` placeholder
(21 mm = bare objective, camera arm excluded) and gates X symmetrically -- a measured
footprint exceeding the objective by more than ~0.2 mm re-blocks the traverse on X. So
both axes fit only against the bare-objective placeholder; the camera-routing strategy is
the new binding constraint, gated and Stage-0-measurement-dependent. Suite green (170
passed) on the change.

Reason: the dry bay was the least-built part of the machine — reserved envelopes and
checklists, zero installed parts — and the observer envelopes carried a tautological
"reaches all wells" swept-body test plus a carriage modeled only as a static box at the
plate-1 end. This session strengthened the swept-body check with falsifiable asserts
(head footprint vs the Ø32 objective keepout; the `8 + FE_z + focus_stroke <= 62 mm`
Z-budget closure) that replace the definitional well-containment identity, and added the
carriage-traverse swept check that surfaced the overflow as a Gate-6 blocker rather than
hiding it. The motion architecture is the answer to that blocker: it names the binding
physics (settle forces stop-and-shoot; the structural loop must hold the cell plane inside
the bench's ±27 µm hold-still spec; condensation on the plate underside is the genuinely
hard wet-boundary interface, rejected closed-loop on the existing SHT41/MLX90614
telemetry) and ranks the build-breaking risks, while keeping every unbuilt claim
explicitly Gate-6 deferred.

## 2026-06-13: The Observer Is A Swappable-Sensor Platform, Not A Fixed Microscope

Decision: the observation module is designed from the start as a sensor-agnostic stage
that hosts interchangeable modality heads, not as a single-purpose brightfield scope. The
contract is frozen at three planes — the kinematic dock (mechanical), the infinity port
(optical), and the HEAD-BUS connector (electrical) — above which the platform owns a
frozen interface and below which each module owns a free design trusted only after a
digest, interlock, and registration check. This is the `sensor_module_interface.md`
(SMIS v0.1) spec: a 3-2-1 magnetic kinematic dock (≤5 µm target), a Ø20 cage+RMS+C-mount
infinity port, a blind-mate auto-ID HEAD-BUS with an EEPROM/cal-vault that refuses to
drive an uncertified laser, and one `acquire(well, lease) -> Evidence` software ABI that
plugs into the same single-writer bridge lease and immutable Evidence model the OT-2
control already uses.

The wedge is automated below-deck live-cell fluorescence (plus brightfield/QPI) on the
OT-2 — the largest pay-today market and the same work as the modularity proof. The build
sequence is forced: baseline brightfield, then computational phase/FPM (the free
quantitative wedge), then a fluorescence head (the first real infinity-port + auto-ID
test), then a second head to demonstrate interchangeability and freeze the spec at N=2,
then partner-built Raman, then NV. The interface is opened (dock, port, bus, manifest,
driver API) to grow the catalog while the registration IP, motion stack, and safety
certification stay closed.

Reason: the governing physics is the bench's NA-0.10 objective — collection efficiency is
~NA²/4 ≈ 0.25 % of 4π, so the platform's value gradient runs opposite its difficulty
gradient, and the cheap computational and ratiometric modalities are the correct
near-term wins while the high-information modalities are photon-budget fights. The
infinity-corrected train already reserves an aberration-free slot for a dichroic or
beamsplitter, and the 80 mm bay was reserved as a biophotonics budget, so modularity is
latent in the existing architecture; SMIS only freezes its geometry and electrical
contract. The catalog's frontier rows are reserved, not promised, and their claims are
bounded honestly: NV-diamond ODMR is an mK non-contact reference thermometer, not
intracellular thermometry and not cell magnetometry (3-4 orders below the NV floor on this
geometry); Raman is a sparse molecular spot-check that wants its own higher-NA head and an
offboard fiber-coupled spectrometer, not a 384-well raster; SPAD/FLIM is sourcing-blocked,
not physics-blocked. The discipline that keeps this from becoming vaporware is to widen the
interface only as far as two paid heads demand and let customers, not the imagined
catalog, pull the platform into being.

## 2026-06-14: SMIS Dock Uses Three Magnets Against The 1 g-Scan Demand

Decision: the SMIS kinematic dock preload is 3× N52 pot magnets (~9 kg total), not the
2× originally specced. The magnet-pull margin is evaluated against the 1 g-scan
separating demand -- the head's static weight plus its inertial reaction at 1 g scan
acceleration (~2× the 900 g weight = 1.8 kg-f) -- not against static weight alone. Three
magnets give 9 / 1.8 = 5.0×, meeting the 5× bar; two magnets gave only ~3.3× against the
same demand. Encoded in `src/aevum_smis/dock.py` (`validate_dock`, `scan_accel_g`
parameter) and `tests/test_smis_dock.py`; the dock section of `sensor_module_interface.md`
is updated.

Reason: the SM-1.2 dock-check do->review cycle found that the original check divided the
magnet pull by static head weight only and reported ~6.7×, while its own docstring claimed
"scan acceleration cannot unseat it" -- an over-claim the formula did not model. Modeling
the real load case (static + inertial at scan acceleration) showed the doc's 2-magnet
figure does not meet a 5× dynamic margin, so the spec moved to 3 magnets. This is a
geometry/statics check only; the <= 5 µm lateral repeatability remains a Stage-B physical
measurement, recorded as a target and never gated. The review also tightened the seat check
to require the canonical 3-2-1 multiset (one cone + one vee + one flat), not merely any
6-DOF arrangement, since two vees and two flats also sum to 6 DOF but are not the frozen
seat.

## 2026-06-14: SMIS Source-Enable Is A Safe-Allowlist, Not A Danger-Denylist

Decision: the SMIS fail-closed source-enable gate requires cal-vault certification for
every module safety class EXCEPT an explicit allowlist of demonstrably-safe classes
(`CAL_VAULT_EXEMPT_CLASSES = {passive, led}`). Every laser class -- including
`laser_class_1`, whose products routinely enclose a class-3B/4 emitter made safe only by
an enclosure -- plus microwave and any class added in future, requires a valid cal-vault
to energize its source. Encoded in `src/aevum_smis/safety.py`
(`evaluate_source_enable`).

Reason: the SM-3.2a/4.3 do->review cycle's security review found the original gate was a
danger-denylist (`CAL_VAULT_REQUIRED_CLASSES = {3b, 4, microwave}`), which is fail-OPEN in
two ways: (1) a counterfeit head self-declares a benign class (the manifest is
self-asserted; the digest only proves it was not altered after EEPROM write, not that the
declared class is true) and dodges the cal-vault; (2) a new dangerous class added later
defaults to not-requiring certification. Inverting to a safe-allowlist makes an unknown or
future class default to fail-closed (must be certified) and removes the self-declaration
bypass for any class that carries a dangerous source. The residual -- a head may declare
`led`/`passive` without certification -- is bounded because those classes carry no
dangerous source, and the hardware interlock loop remains the authoritative backstop the
software can only AND-against, never override. The same review hardened the cal-vault
against replay (a fresh per-dock CSPRNG challenge via `issue_challenge`; freshness is the
platform's obligation) and against MAC field-boundary ambiguity (length-prefixed encoding).

## 2026-06-15: HEAD-BUS Pinout Is A Machine-Checkable SMIS Contract

Decision: SM-2.2 is frozen as code, not prose only. `src/aevum_smis/head_bus.py`
defines `FROZEN_HEAD_BUS`, a typed SMIS v0.1 HEAD-BUS contract covering the 24 V,
5 V, 3.3 V, I2C, 1-Wire, GigE, microwave coax, fiber bulkhead, laser interlock,
MW interlock, alarm, and shield groups. The validator rejects missing/extra signal
groups, duplicate line IDs, hot-mate allowance, EEPROM addresses other than `0x50`,
non-fail-closed laser/MW interlocks, and non-single-point shield bonding.

Reason: the HEAD-BUS is the electrical equivalent of the dock plane: if it drifts
quietly, a module can appear mechanically valid while losing auto-ID, cal-vault,
source interlock, or ground-reference safety. Encoding the table as `HeadBusSpec`
gives future hardware records and module manifests one canonical object to compare
against. The schema deliberately preserves the offboard/analyzer escape hatches:
MW coax and fiber bulkhead are explicit optional bulkheads, while the safety loops
and ID/cal-vault paths are mandatory.

## 2026-06-15: SMIS Semver Fails Closed At Dock

Decision: SM-4.4 compatibility is encoded in `src/aevum_smis/compatibility.py`.
The dock accepts only parseable `major.minor` SMIS versions with the same major as
the platform and a module minor no newer than the platform minor. It also folds in
the frozen HEAD-BUS validation and the driver entry-point group, so a module with
future semver, malformed semver, HEAD-BUS drift, or ABI group drift is rejected
before driver load or source enable.

Reason: `smis_version` was already required in the manifest, but without an
accept/reject policy it was only metadata. The safe default is to treat unknown
future contracts as incompatible: a `0.2` head may depend on additive lines or
driver semantics a `0.1` platform cannot enforce, while a `1.0` head may have a
different frozen surface entirely. Older/current minor versions are accepted by
the semver gate, but schema, envelope, HEAD-BUS, cal-vault, interlock, and driver
checks still run independently.

## 2026-06-15: Infinity-Port PD-0 Is A Validation CAD Datum

Decision: SM-2.1 is encoded in the row-coupon CAD as
`observer_infinity_port_datum_check`, a validation-only Gate-6 body representing the
SMIS PD-0 swept datum plane. The check pins the frozen optical contract from
`sensor_module_interface.md`: PD-0 28 mm from the objective shoulder, Ø20 clear
aperture, 30 mm cage standard, RMS thread present, C-mount present, and
tube-lens-to-sensor spacing of 50 mm. Red cases reject PD-0 outside the front-end
Z envelope, aperture larger than the Ø32 keepout or 30 mm cage standard, missing
RMS/C-mount, and tube-lens spacing drift.

Reason: Level-1 SMIS swaps only work if the shared objective/front-end exports a
repeatable optical handoff. A prose-only infinity port would let a fluorescence
dichroic insert or detector back-end depend on geometry that the exported CAD did
not show or test. Making PD-0 a validation body keeps the optical authority plane
visible in Gate 6 evidence while staying honest that the current front-end numbers
remain Stage-0 measured-hardware placeholders.

## 2026-06-15: Observer Umbilical Is A Frozen Authority Boundary

Decision: IN-C1/C2 is encoded in `src/aevum_smis/observer_umbilical.py`. The
observer offboard boundary is now a typed GX16/M12 contract: GX16-4 carries 24 V
and 5 V, GX16-6 carries I2C, 3.3 V, alarm, and an active-low make-last/break-first
observer enable loop, and camera data is pinned to the M12 X-coded GigE bulkhead
instead of GX16. The reconciliation check proves `FROZEN_HEAD_BUS` remains a
superset of those rail, control, interlock, data, and shield classes.

Reason: the observer umbilical and the swappable-head HEAD-BUS are different
authority boundaries, but they share rail definitions, safety semantics, and the
single-point shield rule. Freezing the observer boundary separately prevents a
future observer wiring change from being hidden inside HEAD-BUS prose, while the
superset check prevents a future HEAD-BUS revision from dropping a class the
offboard observer boundary already relies on.

## 2026-06-16: Condensation Gate Uses Existing SHT41 And MLX90614 Telemetry

Decision: IN-C3 is encoded in `src/aevum_smis/condensation.py`. The platform now
has a typed observer condensation gate: compute local dew point from the per-plate
SHT41 RH/T sample, compare it to MLX90614 plate-underside temperature, require the
reserved +2°C margin before acquisition, and return explicit purge/heat actions
as the margin closes. Saturated headspace, glass below dew point, and margin below
target all fail closed.

Reason: condensation on the plate underside is an optical-path failure, not a
comfort warning. The project already committed to per-plate SHT41 and MLX90614
telemetry, so the integration boundary should consume those signals directly
instead of adding a new sensor role or leaving the rule as prose. The code freezes
the decision structure while staying honest that final purge flow and lip-heat
setpoints still require Stage-0 warm-media evidence.

## 2026-06-15: Head-Swap Registration Is A Separate SMIS Authority

Decision: SM-1.3/1.5a is encoded in `src/aevum_smis/registration.py`. The platform
distinguishes mechanical dock acceptance from post-dock registration authority:
Tier A is coupling trust plus one fiducial touch-up, Tier B is re-fiducial with
three fiducials and autofocus map, and Tier C is first-install/full re-calibration
with all 16 fiducials. `requires_post_dock_autofocus` raises the minimum ritual to
Tier B; first install or forced re-calibration raises it to Tier C.

Reason: treating `on_dock()` as a generic success boolean would blur three different
claims: the head is seated, the module version/interface is compatible, and the
module optical axis is registered into the plate-support fiducial world frame.
Those claims fail for different reasons and unblock different actions. The new
registration validator lets the driver report its result while the platform decides
whether that result is sufficient before acquisition or source-enable proceeds.

## 2026-06-14: Observer-CAD Hardening Exposed Two Placeholder Inconsistencies (OPEN)

The OC-A3/A6/A7/A9/A11/A12 hardening cycle and its adversarial review surfaced two real
geometric inconsistencies latent in the observer placeholder geometry. Both are gated as
**surfaced diagnostics** (visible in the layout output + pinned by tests) but deliberately
NOT placed in the hard fit chain, because resolving them is a design decision / is
measurement-gated and must not be papered over with arbitrary numbers. They are OPEN,
awaiting the builder's call.

**OC-A15 — a realistic objective barrel does not fit the head the razor-thin traverse
margin assumes.** `front_end_barrel_diameter = 25 mm` (a typical 4x objective, matching the
SMIS manifest `barrel_diameter_mm`) exceeds the placeholder head footprint
`front_end_width_y = 13 mm`. A round Ø25 barrel cannot fit a 13 mm-wide head, and the
plate-level traverse sweep is set by the WIDER of (head footprint, barrel). The razor-thin
0.4 mm traverse / 0.2 mm scan margins were computed on the 13 mm footprint; accounting for
the Ø25 barrel grows the traverse extent ~12 mm and the dry-bay fit does NOT close. Field:
`observer_front_end_swept_body_check.front_end_barrel_within_head_footprint` (currently
False). Resolution options: (a) a more compact objective / relay so the real barrel is ≤ the
head; (b) a wider dry bay; (c) accept the fit is contingent on Stage-0 metrology. This is the
sharpest finding: the "dry bay fits with a razor-thin margin" conclusion rests on an
unrealistically small head footprint.

**OC-A15 — analysis update (2026-06-14, multi-agent deck-geometry study + empirical
confirmation).** The binding constraint is NOT the dry-bay envelope — it is the **four 80 mm
structural standoff legs** (`_add_deck_engagement_feet`, `standoff_height_z=80`, spanning
Z[−80..0]) at the slot corners, inner faces at X=13.6 / X=134.0, forming a **120.4 mm scan
corridor** the optical head must thread. The head sweeps Z[−48..−8], *inside* the legs, so the
16 "deck-foot collisions" the traverse check reports are **real 3D interference, not a planar
artifact** (one analysis lever mis-read the legs as 2.5 mm shoes 32 mm below the head and
wrongly concluded "no compromise"; an adversarial skeptic + direct code/Z verification
refuted it). Empirically (substituting a round Ø-barrel into `row_coupon_layout` and driving
the whole footprint): leg-strike onset is at **footprint ≈ 21.4 mm** (0 hits at Ø21, 8 at
Ø21.4, 16 at Ø22+); the Ø25 barrel strikes all 16 legs and overflows the corridor by ~3.6 mm.
The traverse-Y "overflow" is largely a bay-undersizing artifact: swept-Y at Ø21 = 355.5 mm <
the 359.5 mm deck-slot span, so the real Y wall (the deck slot) has slack up to Ø25 — **the
legs (X corridor, ≤21 mm footprint) are the single binding constraint, not Y.** RESOLUTION
(low, not zero, compromise): (1) source a **slim RMS 4× objective, widest barrel ≤21 mm**
(real parts exist; RMS thread floor ~Ø20.3) — a sourcing constraint, Stage-0-caliper-gated;
(2) re-size the dry bay to the deck-slot footprint (`observer_sweep_extra_x`→21,
`observer_sweep_extra_y`→18) so `fits_dry_bay` reflects the real wall not the undersized
envelope; (3) keep the camera off the scan axis (coaxial-fold / offboard) to hold the
footprint ≤21 mm. NO loss of plates, coverage, magnification, or NA. The truly-zero-optical/
sourcing-compromise fallback: **relocate the standoff legs out of the optical scan corridor**
(end-only / outboard seating) — a structural redesign with a Stage-0 seating-repeatability
re-validation. Note: the OC-A11 hardening fix (optical-stability now reads `clears_traverse`,
which ANDs in the foot collisions) is exactly what surfaces this leg strike — without it the
Ø25 interference would have been invisible. Single most important next action: **Stage-0
caliper the real standoff-leg corridor and the widest-knurl diameter of the candidate slim
objective.**

**OC-A15 — implementation (2026-06-14, "make the model report the real wall").** Three
changes landed:
1. **CAD — leg corridor surfaced as the binding scan-axis wall.** `_observer_carriage_traverse`
   now computes and surfaces `scan_corridor_width_mm` (the clear gap between the standoff-leg
   inner faces, 120.4 mm) and `scan_corridor_margin_mm` (the real clearance to the legs,
   0.12 mm); the `scan_margin_is_razor_thin` flag now tracks the corridor, not the soft bay
   edge. The traverse-Y razor-thin flag is retired (Y is comfortable against the resized wall).
2. **CAD — bay-Y resized to the wet/dry-bounded deck extent, X left alone.** `observer_sweep_extra_y`
   12.2 → 17.0 (bay-Y 347.9 → 357.5), so `traverse_axis_fit_margin_mm` reflects the real wall
   (10 mm) not the undersized envelope (0.4 mm). The resize is bounded by THREE wet/dry
   constraints, NOT the deck slot: the wet-witness gutters (top 8.9 mm) and the gasket-tab
   witnesses (needing 0.5 mm clearance → bay-Y ≥ 9.6 mm). X was deliberately NOT resized — the
   adversarial review confirmed pushing bay-X to the deck slot drives the boundary rail (6 mm
   offset) into the right-neighbor slot keepout, so the leg corridor (not a wider bay) is the X
   resolution. The "resize freely to the deck slot" idea from the first analysis pass was wrong
   on the resize specifics too — the bay is fenced in by wet/dry sealing and the neighbor slot.
3. **SMIS — the corridor binds every modality head (cross-module).** `SmisEnvelope` gained
   `scan_corridor_footprint_max_mm = 21.4` (the leg-strike onset), and `validate_manifest_envelope`
   now rejects any head whose scan footprint `max(barrel, front_end_length_x)` exceeds it
   (`scan_footprint_exceeds_leg_corridor`), TIGHTER than the Ø32 keepout. A head with a realistic
   Ø25 barrel CLEARS the keepout but is now refused at dock — the same corridor binds the
   brightfield, fluorescence, Raman, etc. heads, not just the observer CAD. The SMIS example
   fixtures moved from Ø25 to a slim Ø20 corridor-threading barrel.

The **Stage-0 metrology protocol** for this is
`docs/protocols/observer_leg_corridor_objective_metrology.md` (+ template): it measures the
real corridor and the candidate objective, and feeds `SmisEnvelope.scan_corridor_footprint_max_mm`.

**OC-A15 — adversarial-review fixes (2026-06-14).** A 4-lens + 2-skeptic review of the
change set found one BLOCKER + three MAJORs, all fixed: (1) **BLOCKER** — 9 stale
`347.90` cad_value assertions in `test_row_coupon_first_print.py` were missed by the
first cascade pass (the decisive run was CAD-only); fixed to `357.50`. (2) **MAJOR** —
the binding scan wall is actually the **milled dry-bay hi-wall (0.02 mm)**, ~0.1 mm
*tighter* than the leg corridor (0.12 mm); the bay is milled just inside the legs, so
"the corridor, not the bay, is binding" was wrong on the +X side. The traverse now
surfaces `scan_bay_per_wall_margin_mm` + `scan_binding_margin_mm` and the razor-thin flag
tracks the binding minimum. (3) **MAJOR** — the SMIS gate (21.4) was 0.16 mm looser than
the CAD strike onset (~21.21), accepting heads the CAD rejects; tightened to **21.2** (a
shared param `observer_robotics.scan_corridor_footprint_max`). (4) **MAJOR** — the CAD
corridor read the 21 mm placeholder, not the declared Ø25 barrel, so CAD shipped green
while SMIS rejected the same part; added a CAD `barrel_threads_scan_corridor` diagnostic on
the shared constant so the two cannot silently disagree. Plus MINORs (a negative-corridor
falsifiability test, a straddle-robustness guard on the leg split) and doc-drift NITs. The
review VERIFIED the foundation (legs 80 mm spanning Z[−80..0], corridor 120.4, strike
~21.2) and REFUTED the worry that a traverse-axis-wide head could strike (the head
traverses *along* Y through the leg bands; scan-only is the correct leg metric).

**OC-A14 — the single-row coupon is too short for the service raceway, which clamps into the
boundary rail.** The raceway is placed at `dry_ref_x1 + rail_clearance(2) + rail_width(4) +
raceway_clearance(2)` then `min(length - raceway_len, ...)`-clamped to the coupon length. The
coupon (147.6 mm) is too short to hold the raceway at its intended X (141.9 mm), so the clamp
pulls it to 139.6 mm — its near edge lands ~0.3 mm inside the boundary-rail lane
(135.9–139.9 mm), consuming the entire 2 mm `service_raceway_clearance_y`. Field:
`observer_service_raceway_envelope_check.raceway_clears_boundary_rail` (False for the live
axis "y" before the resolution below). Resolution options were to extend the coupon footprint
to fit the raceway, or re-route it. Likely a single-row-COUPON artifact; the production
multi-row bay has more length.

**OC-A14 — resolution (2026-06-15).** Chose the footprint-extension branch. `row.end_margin_x`
is now 10.5 mm, making the one-row coupon 148.6 mm in X. That gives the clamped raceway enough
room to sit outside the boundary-rail lane while preserving the 2 mm service clearance and the
8 mm raceway width. `observer_service_raceway_envelope_check.raceway_clears_boundary_rail` is
now True for the live row-axis "y".

Both were invisible before this cycle (the raceway check had zero asserts; the barrel was
conflated into the bbox circumscribed Ø). The hardening's value was exposing them. The
review also fixed a genuine fail-open BLOCKER: the optical-stability geometry propagation
read `traverse_fits_dry_bay` (bay-envelope only) instead of `clears_traverse`, so a head
that fits the bay but strikes a deck foot or enters the adjacent OT-2 slot would not have
tripped the geometry blocker.

## 2026-06-16: Observer Scan Is A Mutually-Exclusive Bridge Lease Kind

Decision: IN-C4 / HX1 is encoded in `src/aevum_ot2/core/observer.py` (+ `lease_kind`
on `BridgeLock`, `ObserverScanEvidence` in `models.py`). The observer does not run its
own motion controller; it requests a `lease_kind="observer_scan"` lock from the existing
single-writer bridge. Mutual exclusion is **structural, not a new mechanism**: the bridge
already keeps one non-terminal lock per `robot_url`, so a held pipetting lease refuses an
observer scan lease and vice versa — whichever subsystem asks second gets `robot_busy`,
and the refusal carries the holder's `lease_kind` so the busy reason names who holds it.
The lease kind defaults to `pipetting`, so every prior OT-2 session is unchanged; a
pre-IN-C4 lock DB migrates its unlabeled rows to `pipetting` (the fail-safe reading of a
legacy OT-2 lock).

Reason: building an independent observer controller with a peer handshake would create a
second writer — exactly what the architecture forbids. Reusing the proven SQLite
lock/lease/recovery stack as a typed lease *kind* gives hardware-enforced one-at-a-time
operation with no parallel lock table.

Authority boundary (the load-bearing part): observer evidence minting
(`mint_observer_scan_evidence`) is fail-closed against the lease — wrong-kind, terminal, or
expired lease raises `ObserverLeaseError`, so no frame exists without motion authority for
the frame's duration. But the lease is the **only** thing it gates. The
fiducial-transform checksum rides along as `pose_digest_sha256` *provenance*; an empty
digest is allowed at this layer because **registration acceptance** (HX2 / IN-C5/C6),
**source-enable** (`aevum_smis.safety`), **condensation** (`aevum_smis.condensation`), and
the **hardware enable-line interlock** (HX3 / IN-C7) are separate gates that must not be
folded into the lease-validity boolean. The observer evidence schema emits an
`EvidenceHandle(source_kind=observer_frame)`; mapping it into the bridge's durable
`EvidencePacket`/transaction store is the still-open IN-C5 cycle.

## 2026-06-16: Observer Pose Cross-Check Is A Separate Authority From The Tier Ritual

Decision: IN-C6 / HX2 adds `cross_check_observer_pose` + `ObserverPoseCheck` to
`src/aevum_smis/registration.py`. Registration now has TWO distinct authorities:
`validate_registration_result` asks the *ritual* question (did `on_dock` satisfy the
required Tier A/B/C ritual — enough fiducials, right tier), and `cross_check_observer_pose`
asks the *coordinate* question (is the declared canonical→installed transform still
current, and does the observer's independent fiducial recovery agree with it within a
measured residual). The pose check binds on opaque sha256 digest strings, so `aevum_smis`
stays decoupled from the bridge's `FixturePose` (SMIS does not import the bridge — the same
clean isolation IN-C5's SMIS-mapping tail is gated on).

Reason: collapsing these into one boolean would blur three independently-failing claims —
the head is registered to the right ritual, the plate has not moved since (staleness), and
the recovered transform actually matches the declared one (agreement). The observer is the
shared coordinate bridge between the two robots precisely because it *cross-checks* the
declared transform rather than re-transforming target coordinates; a stale or disagreeing
pose must reject acquisition even when the tier ritual passed.

Authority boundaries: each failure is a separate named blocker
(`registration_not_accepted`, `observer_pose_stale`,
`observer_pose_residual_exceeds_tolerance`, `observer_pose_fiducials_insufficient`, digest
missing/malformed) — never one success flag. A 2D rigid fit needs ≥3 non-collinear
fiducials (`MIN_POSE_FIT_FIDUCIALS`), a separate minimum from the tier ritual's
`min_fiducials` (Tier A trusts coupling with one touch-up and does NOT independently
recover, so the fit/residual checks are skipped for it — but staleness still applies to
every tier). The residual tolerance is a conservative placeholder
(`DEFAULT_POSE_RESIDUAL_TOLERANCE_UM = 50`) that MUST be replaced by Stage-0/Stage-3
metrology before it gates a real acquisition — the gate structure is frozen; the number is
not yet evidence. The A1 offset/sign convention (`first_well_center_x/y = 14.38/11.24`,
9 mm pitch) is already the single-source analytic well map in `cad/one_row_coupon.params.json`
and is exercised throughout the CAD well-center computations, so IN-C6 did not re-encode it.

## 2026-06-16: Observer Enable Intent Is Software, Not The Hardware Enable

Decision: IN-C7 / HX3 software half is encoded in
`src/aevum_ot2/core/observer_interlock.py`. The two-layer interlock from
`observation_module.md` gets its software side: `observer_enable_intent` derives the enable
INTENT the bridge asserts to the (hardware, B) observer enable line — true only while a valid
`observer_scan` lease is held — and `pipetting_lease_admission` refuses a pipetting lease
while an observer lease is active AND, after release, until a fresh parked + Z-retracted
`ObserverParkReport` exists.

Reason: a software lock legally cannot guarantee motors are de-energized, so the code must
never pretend it does. `observer_enable_intent` returns *intent*, and `ObserverParkReport` is
the software record of a *hardware* limit readback — both deliberately one layer above the
physical E-stop backstop that drops the 24 V rail / enable line regardless of software. The
handoff is the load-bearing new authority: releasing the software lease does not prove the
head physically parked, so pipetting stays refused until the hardware limit is reported
fresh. Fail-closed throughout — absent / false / stale / future-dated park reports do not
admit, and each cause is a separate named blocker (`observer_lease_active`,
`observer_park_unconfirmed`, `observer_not_parked`, `observer_z_not_retracted`,
`observer_park_report_stale`, `observer_park_report_in_future`), never one boolean. The
freshness window (`DEFAULT_MAX_PARK_AGE = 60 s`) is a policy placeholder refined with the
Stage-4 interlock build; the hardware enable line, the GX16 safety loop, and the physical
limit switch are the B half this software layer sits on top of.

## 2026-06-16: SMIS Evidence Reaches The Durable Store Through A Structural Seam

Decision: IN-C5's tail — durably persisting the generic SMIS `ModuleEvidence` (not just the
bridge-native `ObserverScanEvidence`) — is encoded in `src/aevum_ot2/core/observer.py` via a
`SensorModuleEvidenceLike` Protocol plus `module_evidence_to_packet` /
`persist_module_evidence`. The open fork was *where the cross-package mapping lives*, since
`aevum_smis` must not import the bridge (frozen decoupling) and the bridge had no SMIS
dependency. Resolution: the bridge — the consumer of SMIS evidence — defines the **structural
shape it accepts** and imports nothing from `aevum_smis`, the mirror image of how SMIS uses
the `MotionLease` Protocol to consume the bridge's lock without importing the bridge. A test
asserts the real `aevum_smis.ModuleEvidence` satisfies the Protocol, so the seam cannot drift
silently.

Reason: a bridge→SMIS import (or a SMIS→bridge import) would couple the two core packages and
break the isolation that lets each be reasoned about and tested alone. A structural Protocol
keeps both packages independent while still giving the bridge one durable evidence store for
every modality. Both evidence paths commit packets with NO claims (a bare acquisition record
never authorizes motion), share the `observer_frame` source kind (the SMIS stage is the
observer reframed as a swappable-head carrier), and fail closed — the observer path on a
forged non-`observer_scan` lease_kind, the module path on a missing `lease_owner` (a frame
that did not come from a lease-gated `run_scan`). The DS28E07 `calibration_ref` rides as
provenance; its source-enable meaning stays a separate gate (`aevum_smis.safety`).

## 2026-06-17: Post-Motion High-Z Evidence Is A Distinct Authority From Pre-Motion Target Existence

Decision: OT-6 is encoded in `src/aevum_ot2/core/high_z_motion_evidence.py` (+ `HighZMotionRecord`
and the `high_z_motion_completed:<class>` claim/`HIGH_Z_LANDING` source kind in
`records.py`/`models.py`). It is a NEW module, deliberately NOT folded into `target_evidence.py`:
the target-class flow answers a PRE-motion question ("does a verified, reachable high-clearance
target exist before `move_high_z`?") keyed to `TargetClassVerificationRecord`; OT-6 answers a
POST-motion question ("after `move_high_z` executed, did it reconcile against the command journal
and command history?"). Folding the two would overload one claim_type with two meanings and blur
"a target exists" into "a move happened" — the success-boolean collapse the project forbids. OT-6
mirrors the proven artifact→packet→claim→commit→promote pattern and additionally binds executed-
command provenance from the real `CommandJournalEntry`/`CommandReconciliationResult`.

Authority boundary: OT-6 PRODUCES a durable evidence claim and nothing more — it never sets
`motion_allowed`, mints no `MotionApproval`, emits no `GateResult`, and never promotes an
`OffsetRecord` (that is OT-1, which the builder reviews). The committed-store + live-command-journal
re-verification of the claim is the consuming gate's job, not OT-6's.

Conservative C-defaults (revisit when a calibrated detector exists): the high-Z vision path is
uncalibrated (`vision.py` forces `motion_gate=False`, `validated_fixture_detector=False`), so a
USABLE claim rests on the human `inspection_note` + command reconciliation + an indexed post-move
camera capture — never on geometry. OT-6 stores only `commanded_high_z_mm`; it does NOT compute an
achieved-Z or an offset vector (inventing one would manufacture a false geometric measurement). The
offset derivation is OT-1's, from a future calibrated source.

Trust model + hardening (an adversarial review found and we fixed 3 blockers + 1 major + 1 residual):
the executed-command provenance is bound to THIS command (`reconciliation.matched_command_id ==
command_entry.command_id`, key/status correspondence, session/robot/run scoping) and the frame must
be post-motion (`command_completed_at` from the journal entry, `image_captured_at >=
command_completed_at`); `promoted_high_z_motion_record` re-validates claim identity (fixture/labware/
pose + claim-id-bound-to-handle + `HIGH_Z_LANDING` source) and rejects a self-contradictory
`value=True` claim that still carries `reasons`. The residual accepted trust: camera captures are not
cryptographically signed and OT-6 does not re-run reconciliation against the live journal at validate
time — that stronger check belongs to the consuming gate and is system-wide, not OT-6-specific.

## 2026-06-17: Shared Evidence Primitives Have One Canonical Home (evidence_primitives.py)

Decision: the six duplicated evidence primitives — `_sha256_file`, `_safe_path_segment` (the
path-traversal guard), `_transaction_root_for_index` (the on-disk transaction-layout invariant),
`_same_path`, `_is_timezone_aware`, `_datetime_payload` — now live ONCE in a new leaf module
`src/aevum_ot2/core/evidence_primitives.py`, imported by all seven evidence-layer consumers. The
home is a deliberately stdlib-only module (imports nothing from `aevum_ot2`), making it a graph
sink that cannot participate in an import cycle — chosen over `evidence.py` (which imports
models+schema and already shows cycle back-pressure via lazy imports).

Reason: in a tamper-evidence system these primitives encode SHARED INVARIANTS (a path-traversal
guard, a disk-layout rule) that must stay byte-identical everywhere; N hand-maintained copies are a
silent forgery surface, and drift had already begun. A brutalist design review flagged this as the
headline security finding; the consolidation was executed as do→review workflow cycles.

The one authority-bearing change is `_same_path`: it previously existed as two divergent variants —
an object-guard fail-closed variant (`evidence.py`/`pose.py`, used at call sites that pass untrusted
JSON dict lookups that can be `None`) and a `str|Path` variant (the three evidence modules, used at
call sites passing a real `Path`). Neither body was universally safe (the object guard would reject
a legitimate `Path`; the `str|Path` body would crash on `Path(None)`). The canonical reconciliation
admits exactly `str`|`Path` and fails closed (returns False) on anything else, with a
`str(left)==str(right)` OSError fallback — verified behavior-preserving at every call site (the
untrusted sites only ever see `str`/`None`; the Path sites only see `str`/`Path`).

A second pass (2026-06-17) finished the job: `_stable_json_sha256` and the
`EVIDENCE_TRANSACTIONS_DIRNAME` token also live once in `evidence_primitives.py`, with the
stable-JSON-hash callers (`command_journal`, `dispatch_preparation`, `safety`, `pose`,
`motion_approval`'s plan/scope digests, `registry.offset_record_id`) and the file-hash callers
(`artifacts.sha256_file`, `gates._sha256_if_file`) all routed to the canonical — provably
byte-stable on every persisted digest (`.encode()`≡`.encode("utf-8")` under ensure_ascii; pinned
by a golden-vector test). Two near-duplicates are deliberately LEFT and documented as
legitimately separate: `motion_approval._safe_segment`'s non-raising `"empty"` fallback (it is a
human-readable label; id uniqueness rides on the scope digest, so raising would be a wrong
"fix"), and the `_require_session_evidence_index` inline resolve-compares (routing through
`_same_path` would replace fail-loud OSError propagation with a string-equality fallback in a
tamper gate).
## 2026-06-17: Offset Authority Is Producer-Built But PROMOTED Stays Gated Behind A Calibrated-Source Allowlist

Decision: OT-1 is encoded in `src/aevum_ot2/core/offset_evidence.py` (+ records/models/registry
support). It is the producer that was missing: `offset_match_gate` trusts an `OffsetRecord` in
`authority_state=PROMOTED` as a motion INPUT, but nothing ever set PROMOTED, so the gate could never
pass. OT-1 builds the full evidence→claim→promote pipeline. `promoted_offset_record` is the terminal
trust boundary and flips PROPOSED→PROMOTED only after a fail-closed JOIN: a scope-valid committed
offset_measured claim (whose bound artifact's offset_mm matches the record), the OT-6
`high_z_motion_completed` claim re-fetched from the COMMITTED store (never caller-supplied), a LIVE
command-journal re-reconcile of that move (state completed / status succeeded / is-latest /
not-recovery — catching a stalled motor that merely reported success at OT-6 build time), and an
`offset_source` in `CALIBRATED_OFFSET_SOURCES`.

Builder decision ("pipeline only, PROMOTED blocked"): `CALIBRATED_OFFSET_SOURCES` is EMPTY. The
offset_mm vector has no trustworthy machine source yet (high-Z vision is uncalibrated; OT-6's
"post-motion" is only a timestamp), so an operator-attested offset may be RECORDED as durable
evidence but MUST NOT promote. The entire machinery is built, exercised, and ready (a
monkeypatched-allowlist test proves it promotes correctly when opened), yet promotion is unreachable
by construction until a calibrated source is deliberately added to the allowlist — the same
safe-allowlist discipline as SMIS source-enable. This errs toward never authorizing motion from an
unattested number.

Reason / authority boundary: OT-1 is a PRODUCER. It never sets `motion_allowed`, never
mints/arms/consumes a `MotionApproval` (motion permission is solely the arm/consume flow over the
gate), and emits no authorizing `GateResult`. It re-validates the OT-6 lineage against the committed
store + the live journal at promote time — strictly stronger than the existing gates, which consult
neither. The `offset_record_id` is a scope hash that excludes `authority_state`, so a promoted record
keeps its PROPOSED id (the registry upsert relies on this); the new `OffsetRecord` provenance fields
are additive and excluded from that hash, so no existing offset id/digest changed.

Adversarial review hardening (2026-06-17): a multi-lens review confirmed the core is fail-closed and
isolated (empty-allowlist block unconditional; strict `is True` gates; no motion authority) but found
two latent holes in the JOIN — both behind the empty allowlist so not reachable today, but they would
silently activate the instant a calibrated source is added. Both fixed before that can happen: (1) the
offset value-binding now re-verifies the external artifact against its committed handle checksum before
trusting its offset_mm (a post-commit tamper of the mutable file no longer promotes an unattested
vector); (2) `promoted_offset_record` now derives authority SOLELY from the committed evidence store —
the offset claim is re-fetched via `_committed_offset_blockers` (symmetric with the high-Z prerequisite),
so a fabricated/uncommitted caller claim is never trusted (the `offset_claims` parameter was removed).
Regression tests pin both (`test_post_commit_offset_artifact_tamper_blocks`,
`test_uncommitted_offset_claim_does_not_promote`).

## OT-3 — physical-event / foreign-command invalidation (2026-06-17)

`detect_foreign_commands` (in `command_journal.py`) adds a distinct **invalidation authority**:
a pure, fail-closed whole-history scan that asks "is the entire run command-history accounted
for by commands THIS bridge authored?" It is a withhold-trust signal, never a motion grant —
`invalidated=True` means standing authority resting on "the robot did only what we told it" must
be re-verified; it does not (and structurally cannot) permit a move. It complements, rather than
merges into, `reconcile_command_history`: that primitive is our-command-centric and its
`matched_command_is_latest` only notices a foreign command appended AFTER ours; OT-3 catches a
foreign command that executed BEFORE ours (a touchscreen jog, a second HTTP client) too.

Two design points were settled by adversarial review:
- **1:1 cardinality, not membership.** The first cut used `any(_matches_entry(...))`, letting one
  authored entry vouch for unlimited matching history rows — so a duplicate/replayed physical
  execution (`[k1,k1,k1,k1]` vs one authored `k1`) read as clean. This was a fail-OPEN regression
  against `reconcile_command_history`'s `non_idempotent_duplicate_key` guard, and the duplicate-key
  double-execution hazard is project-verified (live no-motion testing 2026-05-02). Fixed with a
  consuming pass: each authored entry accounts for at most one history command; surplus matches are
  reported `non_idempotent_duplicate_key` and invalidate.
- **No status comparison inside `_matches_entry`.** A failed-then-replayed-succeeded move is caught
  by the cardinality pass, NOT by comparing per-command status — `_matches_entry` is shared with
  reconciliation, where a live command's status legitimately differs from the prepared entry, so a
  status check there would spuriously invalidate. The matching definition stays single-sourced.

`MOTION_RELEVANT_COMMAND_TYPES` is informational only (surfaces `motion_relevant_foreign`); it never
gates `invalidated`, which fails closed on ANY unaccounted command. The primitive has no production
caller yet — its own contract is the safety boundary; wiring it into the offset-promotion / park /
lease-admission consumers is the open follow-up. 18 tests; 605 across the surface, ruff clean.

## OT-4 — move_low_z dry-target translator (descent emission gated) (2026-06-17)

Added `_move_low_z_command_body` + routing in `dispatch_preparation.py`: the translator that
turns an approved first low-Z dry step (`center_low_z_dry`) into a moveToWell command, mirroring
the high-Z translator. A translator consumes existing approval and creates no motion authority.

Adversarial review (verified against the Opentrons MoveToWellParams schema AND the canonical
fixture geometry) found the first cut commanded an UNSAFE descent, so emission is now gated
fail-closed behind `LOW_Z_DRY_DESCENT_ENDPOINT_GROUNDED = False` (mirrors OT-1's empty
calibrated-source allowlist). Two safety facts forced this:

- **`minimumZHeight` does not bound a descent.** Per the schema it only raises the lateral-transit
  ARC apex (and is a no-op below the API default safe-Z margin); it never clamps the final descent
  to the well target. The first cut passed `dry_z_floor_mm` to it and documented it as a "hard
  transit floor" — inverted. The (now-gated) emission tail uses `conservative_high_z_mm` for
  transit clearance, mirroring the high-Z translator; the descent is bounded only by the resolved
  well target.
- **The safety model has no per-well descent FLOOR.** `dry_z_floor_mm = conservative_bounds.z_mm`
  is the conservative collision-envelope TOP (a lateral-transit clearance), a different geometric
  feature from a well-access descent limit. On the canonical fixture the A1 well-top (~80 mm) is
  ~11 mm BELOW that envelope top (~91 mm), so a naive "land at well top" endpoint sits below the
  floor it claims to honor, with every guard green. Relating a descent endpoint to a real per-well
  floor requires validated well-access geometry (and a measured safe dry depth) the codebase does
  not yet carry.

So a safe low-Z dry descent cannot be emitted today without inventing physical authority — which
the realization goal forbids. The translator therefore validates everything it can (target class,
session identity, finite-positive high-Z park) and refuses the descent with
`low_z_dry_descent_endpoint_not_grounded`. **Open follow-up (B + a small A):** add a per-well
dry-descent floor distinct from the collision-envelope top (from the labware A1 well geometry +
a measured safe dry depth), verify the resolved endpoint against it, then flip the gate. 4 tests
(headline blocked, monkeypatched-grounding machinery proof that minimumZHeight is the high-Z park
not the floor, non-center-target block, fail-closed inputs). 609 across the surface, ruff clean.

## OT-2 — set_offset formally closed (not a motion command) (2026-06-17)

Decision: `set_offset` is FORMALLY CLOSED, not wired. A labware offset in Opentrons is an
evidence-backed registry record applied at run SETUP via the `/labwareOffsets` API and consumed
by the `OFFSET_AUTHORITY` gate (move_low_z / liquid_handling) — it is NOT a maintenance MOTION
command, so there is no coherent command for a `set_offset` translator to emit. OT-1 produces the
promoted offset (producer side); dispatch reads it back from run state; nothing in between needs a
"set offset" motion step.

`set_offset` stays in the PlanOperation enum for completeness but is now declared in
`plans.FORMALLY_CLOSED_OPERATIONS` and rejected fail-closed at every layer with an explicit closure
reason (not a generic "unimplemented"): the context OperationBlock (planning), `_validate_motion_step`
(validation), and `_command_body_for_operation` (dispatch, defense in depth). It is also absent from
the agent/MCP surface by policy (agent_ot2_bridge.md; test_adapter_boundaries.py). Tests assert the
explicit closure reason at validation and dispatch. No motion authority is created or removed; this
only converts an accidental-looking fall-through into a documented, declarative stance. 610 across
the surface, ruff clean.

## OT-5 — liquid_handling (wet) closed scaffold (2026-06-17)

Added `_liquid_handling_command_body` + routing as a documented CLOSED SCAFFOLD (the backlog's
own scope for OT-5). A wet op is the deepest, most dangerous motion — the tip descends BELOW the
dry target INTO liquid, then aspirates/dispenses — and every prerequisite is ungrounded, so it
emits no command and has no emission tail (a wet step is a SEQUENCE, not one command body).

Documented design, none of it wired: (1) approach the grounded dry target — depends on the OT-4
per-well descent floor, not yet grounded; (2) controlled descent INTO liquid to a measured wet
depth — ungrounded; (3) aspirate/dispense at grounded volume + flow-rate parameters — the plan
step carries `EmptyPlanParameters`, i.e. there is no wet-workflow spec to translate; (4) retract.
It also requires the WET_CLAIMS evidence (DRY_TARGET_PASSED + WET_WORKFLOW_READY), which require a
passed dry target — itself gated.

The scaffold restricts to `center_wet`, validates session/profile fail-closed, and always refuses
with `liquid_handling_wet_workflow_not_grounded` (single greppable flag `WET_WORKFLOW_GROUNDED`;
unlike OT-4's gate, flipping it is NOT sufficient — the wet sequence must be built and grounded).
Creates no motion authority; emits nothing. 3 tests. 612 across the surface, ruff clean.

This completes the OT control-stack translator track for this pass: OT-6 (high-Z evidence) and the
move_high_z translator land real commands; OT-4 (low-Z) is gated on a per-well descent floor; OT-2
(set_offset) is formally closed; OT-5 (wet) is a closed scaffold. Every descent/wet path that
lacks physical grounding is fail-closed rather than inventing motion authority.

## 2026-06-18 — remaining A-queue batch (agent surface, recovery, commissioning, protocols)

**OT-7 MCP agent adapter** (`src/aevum_ot2/adapters/mcp.py`): the fourth COTS/agent-boundary authority
exception — an adapter is a translator, NOT an authority. It exposes exactly 10 allow-listed validated
session-transition tools and routes every stateful call through `server.client.DaemonClient`; the only
direct-core call is read-only `ot2_status` (resolve_robot + fetch_robot_status), matching cli.py.
(a) Motion authority is never agent-mintable — `arm_motion_approval` is intentionally NOT a tool, and
validate_plan/execute_next never inject a motion_approval. (b) Orientation is never defaulted to
'canonical' by agent plan tools; it is owned by the session. (c) Fail-closed twice: `register_tool`
refuses denied/non-allowlisted names and `dispatch` re-checks before routing. (d) Tool inputs are
pydantic extra='forbid' so motion_approval/raw-command fields cannot be smuggled. (e) The MCP SDK is
optional, lazy-imported, NOT an install requirement.

**OT-8 route-parity ship-gate** (`tests/test_route_parity.py`): the "no SILENT canonical default" property
is pinned at its exact HTTP + MCP sites, with pose-bearing routes DERIVED from app.py + request models (not
hand-listed) so drift breaks the test. A motion-capable agent surface may never silently default a pose.

**OT-10 abort/recover facade** (`core/abort_recover.py`): `ot2_abort_or_recover` is a non-authoritative
projection over the proven `recover_no_motion_session`; `motion_allowed` is never True out of this path
(derived False unconditionally and fails closed if a session unexpectedly reports True). `required_action`
maps fail-closed per disposition. Calls no raw transport.

**OT-12 commissioning operability** (`core/commissioning.py`): a thin fail-closed ORCHESTRATOR over the
already-existing motion-capable BridgeService — NOT a new motion path. The daemon, validation,
approval-minting, and dispatch authority already live in the bridge core; commissioning only sequences and
reports. Dry-run is the default; it never auto-arms (requires explicit confirm_arm + motion_enabled), mints
no MotionApproval itself, and never sets motion_allowed.

**OP-P5 dock repeatability** is a Stage-B protocol that FEEDS registration, not a dock gate: a head that
cannot trust the ≤5 µm coupling sets `requires_post_dock_autofocus`, escalating the registration ritual —
the measured outcome does not become a new gate. **OP-P3/P4/P8** likewise document existing fail-closed
gates/models and create no motion/emission authority (condensation purge → `evaluate_condensation_control`'s
three blockers; Gate-6 observer row → an EvidencePacket record format, packets-only, that never authorizes
the next motion; settle → the inherited hold-still spec). All protocol numbers remain not-yet-evidence until
measured.

## 2026-06-18 — OT-4 follow-up: per-well descent bounds (the real floor object)

The OT-4 review found `dry_z_floor_mm` (the conservative collision-envelope TOP, ~91 mm) is the
WRONG quantity for a per-well descent — the A1 well-top (~80 mm) sits ~11 mm below it — and the
descent gate had only a boolean, no floor object. `src/aevum_ot2/core/well_geometry.py` supplies the
right object: `WellAccessGeometry` (well_top = z+depth, well_bottom = z, depth) derived ONLY from a
labware definition whose checksum matches the safety profile's existing `labware_definition_sha256`
(mirrors OT-1's re-fetch + checksum-verify — never trust a number whose source file does not match
its digest). `_move_low_z_command_body` now loads this on-demand and verifies the would-be endpoint
lies within `[well_bottom, well_top]`, failing closed on a missing/tampered definition or an
out-of-bounds endpoint.

These are GEOMETRIC bounds, NOT a dry-descent floor: the safe dry depth (the liquid line within the
bounds) is a measurement, so `LOW_Z_DRY_DESCENT_ENDPOINT_GROUNDED` stays False and emission is still
refused. No `FixtureSafetyProfile`/digest change (computed on-demand, anchored to the existing
labware digest) — zero blast radius. The check is additive and fail-closed: it can only append a
blocker, never clear one or open emission (review verdict: ship-it, no findings). 8 well-geometry
tests (bounds, checksum-mismatch, empty-checksum, unknown-well, malformed-well, missing-file,
within-bounds predicate) + a descent-translator tamper test. **Open tail (B):** ground a real
sub-rim dry endpoint by measuring the safe dry depth within these bounds, then flip the gate.

## 2026-09-21: Luminescence Is The Catalog's First Level-3 Candidate, And Row #3 Survives On Ratiometry

Decision: add **row #13, luminescence (SiPM, non-imaging)** to the SMIS modality
catalog as the first genuine exercise of the Level-3 tier, restate row #3's
absorbance verdict as *ratiometric-survives-NA* rather than free-rider, and mark
both as reserved-not-scheduled. The catalog's existing numbering is treated as a
reference surface: #13 is **appended, not rank-inserted**, because this document
and the roadmap cite rows by number (#1/#2, #1-#5, #3 and #5) and renumbering
would silently break them. The rank the row would have earned (~#4/#5) is stated
in the legend instead.

Reason: the Byonoy prior-art review (`../knowledge/byonoy_plate_readers.md`)
exposed a real gap and a real mis-rationale.

- **The gap:** bioluminescent reporters are first-class live-cell kinetics — our
  stated territory — and the catalog had no row for them. Commercial 96-SiPM
  readers demonstrate the detector side is solved and cheap.
- **Why it is Level-3 and not a head:** luminescence has no excitation to turn
  up, so it is purely collection-limited. The 4× NA-0.10 objective discards
  ~99.75 % of the emission; a large-area SiPM with a light guide directly under
  the well buys back one to two orders of magnitude of solid angle (geometric
  estimate, unmeasured) and needs no focus. It is the one entry where deleting
  the objective *improves* the measurement, which makes it the cleanest test of
  a tier the spec has reserved but never used. Because our stage scans, one
  detector replaces a commercial reader's 96.
- **What it costs:** spatial information. It reports that a well lit up, never
  which cells did. Recorded in bounded claims so it is not re-sold as imaging.
- **Where the real work is:** not the detector. Bay stray light (the WS2812 ring
  and deck-side leaks must be dark during acquisition, which the bay is not built
  for today), SiPM dark-count rise at the 37 °C row setpoint, and plate/mat
  afterglow after any illuminated step.
- **Row #3:** the recorded rationale ("reuses #1/#2 hardware") undersold the
  physics. Absorbance is I/I₀, so the NA collection penalty largely cancels — the
  same argument row #4 already makes for ratiometric thermometry. The verdict was
  right for the wrong reason, and the corrected reason also names what we would
  actually ship: serial per-well spectrophotometry of an imaged field, not a
  3-second plate read. Transmission absorbance additionally depends on the
  lid-window branch of C-OB2.

Scope: catalog and honesty text only. No FROZEN contract, envelope, gate, or
build order changes; the near-term ordering stays #1 QPI → #2 fluorescence, and
#13 explicitly does not gate the wedge or become a third head. Nothing here is
Gate-6 evidence — no SiPM has been sourced, and every collection figure is
geometric.


## 2026-09-21 — OC-A15 correction, and the phantom plate window

Two frozen numbers that several downstream conclusions rested on were re-derived from the live
model rather than from this log. Both were wrong. Neither was a modelling judgement call; both
were arithmetic that no longer matched the parameters.

### 1. The leg corridor is 117.4 mm, and the head budget is 15.56 mm — not 120.4 / 21.4

The 2026-06-14 OC-A15 entry above records a 120.4 mm corridor with leg inner faces at
X = 13.6 / 134.0 and a leg-strike onset at footprint ≈ 21.4 mm. Recomputed from
`cad/one_row_coupon.params.json` through `_deck_engagement_foot_rectangles`:

| | logged (2026-06-14) | **live (2026-09-21)** |
|---|---:|---:|
| corridor width | 120.4 mm | **117.4 mm** |
| leg inner faces (X) | 13.6 / 134.0 | **17.10 / 134.50** |
| head-footprint strike onset | 21.4 mm | **15.56 mm** |

Two independent errors compounded:

1. **`lower_service_foot_inset_x` (3.0) was not in the corridor.** It walks a single tile-4 foot
   inboard to keep the lower service connector/shroud lane clear. That one foot sets the near
   wall, costing 3.0 mm of corridor.
2. **The well array is not centred in the corridor.** The old figure took the budget as
   `corridor − 99.0 mm well span`, which is only valid for a centred array. Live slack is
   **7.78 mm near / 10.62 mm far**. The objective is on-axis, so the NEAR side binds and the
   budget is `2 × 7.78 = 15.56 mm`, not 18.4 (the corridor-minus-span figure on live geometry)
   and not 21.4.

At the frozen 21.2 mm gate the head fails **both** walls — corridor −2.82 mm, dry bay −0.08 mm —
so 21.2 never cleared anything. Confirmed by sweeping the live `carriage_traverse` check:
`clears_traverse` flips between 15.56 and 15.60. The CAD had been reporting this correctly all
along (`scan_corridor_width_mm: 117.4`, `scan_binding_margin_mm: −2.72`, `hits_deck_feet: True`);
only the frozen SMIS constant and the prose disagreed with it.

**The consequence is the important part.** An RMS thread floors a barrel near Ø20.32, so at a
15.56 mm budget **no RMS-threaded objective threads the corridor** — including the Ø20 reference
4× head used as the "valid" fixture throughout the SMIS tests. The 2026-06-14 resolution (1),
"slim RMS 4× objective ≤21 mm barrel … NO loss of plates, coverage, magnification, or NA", does
not survive: there is no ≤15.56 mm RMS barrel.

Restoring `lower_service_foot_inset_x` to 0.0 gives a 120.4 mm corridor and a 21.24 mm budget, at
which Ø20.32 clears by **+0.46 mm**. That single parameter is the difference between "no objective
fits at all" and "the current 4× fits". It has **not** been changed here — it exists for a real
service-routing reason and re-routing that shroud is a design decision, not a correction. It is
recorded as the highest-value cheap move on the table.

Changed: `scan_corridor_footprint_max` 21.2 → 15.56 in both `cad/one_row_coupon.params.json` and
`src/aevum_smis/manifest.py`; the stale leg-position comment in
`src/aevum_cad/row_coupon/parts/observer.py`; the Stage-0 metrology protocol (which would have
sent someone to measure against the wrong number, and which now asks for the two slacks separately
rather than one centred gap). SMIS tests now pin the rejection of the real Ø20 RMS 4× head as a
first-class fact rather than asserting it fits.

**Still open (unchanged by this correction):** the barrel-diameter question is a sourcing task, not
a geometry one. The working-distance figure this paragraph originally carried was wrong; it is
superseded by the standoff correction entry at the end of this log.

### 2. There is no 0.6 mm plate window

`plate.bottom_window_thickness_z = 0.6` was extruded by `build_microplates` as an 88 × 52 mm slab
across the observation window at the plate underside, and `observer_optical_bench.md` added it to
the optical standoff. The published plate profile closes exactly without it:
`bottom_height_z` 1.73 + `coverslip_thickness_z` 0.17 = 1.90 = `height_z` 14.30 −
`plate_top_to_cell_plane_depth_z` 12.40. A 0.6 mm window overshoots the published cell plane by
exactly 0.60 mm, and the parameter never appeared in the published-profile source file. The same
document that added it also states, twice, that the window is open from below and that the cells
are imaged through the 0.17 mm coverslip. RS39 in the cycle log shows it as a pre-existing
placeholder left unreconciled when the published coverslip value was added beside it.

The parameter is removed; `build_microplates` now places a `coverslip_thickness_z` slab at
`bottom_height_z`. Golden builder signature for `build_microplates` is unchanged
(`[127.6, 357.25, 14.3, 8]`), so this is a correction of where the glass is, not a change to the
plate's envelope. Glass in the optical path is now **0.17 mm**, the coverslip alone.

This one is load-bearing for resolution. Slab spherical aberration goes as `W_pv ≈
t(n²−1)/(8n³)·NA⁴`, so the admissible NA is set by *uncorrected* glass thickness. Believing
0.77 mm sat in the path capped usable NA near 0.26 and made everything above a 10× look
inadmissible. The real path is 0.17 mm of #1.5H — exactly what the objectives are corrected for —
so the ceiling is set by residual correction error instead, and NA ≈ 0.55 is reachable. The
"no subcellular domain is resolvable" conclusion was a parameter error, not a physical limit.

### Method note

Both errors survived because they were cited from this log rather than recomputed from the model,
and in the corridor case the CAD's own live output had disagreed with the log for some time. The
cheap guard is to derive such constants in a test rather than freeze them in prose; the SMIS
corridor constant remains frozen by design (it is a contract with external heads), so its comment
now carries the derivation and the date it was last checked against the CAD.


## 2026-09-21 (later the same day) — the standoff is 19.90 mm, and it inverts the objective search

The glass-window correction above also restated the cell-plane standoff as 9.90 mm. **That figure was
wrong**, in the same way the original 9.73 mm was wrong: both decomposed the standoff as "8 mm air +
plate terms", treating `carriage_top_clearance_z` as the whole air gap. It is not. That parameter only
places the head's front-face ceiling at z = -8. The plate bottom sits at z = **+10.0**, because
`base.thickness_z` (8.0) and `plate_support.land_height_z` (2.0) lie between them. The optical path
crosses both through the 88 x 52 mm aperture, so they are air -- but they are still 10 mm of standoff
that neither figure counted.

Live layout, cross-checked two independent ways:

    plate_bottom_z 10.0 + bottom_height_z 1.73 + coverslip 0.17 = cell plane z 11.90
    plate_top_z 24.30 - plate_top_to_cell_plane_depth_z 12.40    = cell plane z 11.90

Against a front-face ceiling of z = -8, the standoff is **19.90 mm** -- 0.17 mm of glass and 19.73 mm
of air.

**This inverts the objective search.** Any objective must have WD >= 19.90 mm to reach the cell plane
at all, so the entire short-working-distance catalogue is excluded and long-WD objectives are the ONLY
admissible class. The preceding entry argued the opposite -- that long-WD objectives carry reach this
design cannot use, and that the part to source was NA >= 0.40 at WD just over 9.90 mm. That reasoning
was built on the wrong standoff and is withdrawn.

It also doubles the front aperture each NA demands, since that goes as 2*WD*tan(asin(NA)):

| NA | front aperture at WD 19.90 | against the corridor |
|---:|---:|---|
| 0.10 | 4.00 mm | fits the live 15.56 budget |
| 0.40 | 17.37 mm | exceeds 15.56; fits 21.24 only as a BARE aperture, before any barrel |
| 0.50 | 22.98 mm | needs the 25.84 rail budget, bare |
| 0.55 | 26.21 mm | needs the 30.84 slot ceiling, bare |

So subcellular resolution is foreclosed harder than the earlier entry implied: at the true standoff,
NA 0.40's bare collection cone alone overruns today's corridor.

**The lever nobody has pulled.** The head ceiling sits 18 mm below the plate bottom, and the base
carries an 88 x 52 mm aperture the front element could rise into. Recovering that travel is the
largest single lever on admissible NA available anywhere in this design, and no document has yet
asked whether the front element may enter the aperture. That question should be answered before any
objective is bought.

**Method note.** This error had the same shape as the two above: a decomposition written once in prose
and thereafter cited rather than recomputed. It survived my own correction pass earlier today because
I corrected the *terms* of the standoff without recomputing the *total* from the layout. The guard is
unchanged, and I did not apply it: derive it from `row_coupon_layout`, do not restate it.


## 2026-09-23 — the aperture violates the Stage-0 cradle spec by 17.4 mm on both axes

**What was believed.** That the 88 × 52 mm observation aperture satisfies the Stage-0 cradle
requirement. The requirement is stated in three documents, four places, in identical words:

| | statement |
|---|---|
| `observer_optical_bench.md:76` | "the full 88 × 52 mm observation window is open from below — nothing under any well, skirt flange only" |
| `observer_optical_bench.md:304` | "Central cutout ≥ 90 × 54 mm so the full 88 × 52 mm observation window is open from below — **nothing under any well, skirt flange only.**" |
| `docs/protocols/observer_optical_bench_stage0.md:58` | "central cutout open from below so the full observation window is clear — nothing under any well, flange only" |
| `data/measurements/templates/observer_optical_bench_stage0.md:24` | gate row: "Plate seated skirt-only, nothing under any well" |

**What is true.** The two halves of that sentence are not the same requirement, and the second does
not follow from the first. "Nothing under any well" needs a clear span of **105.4 × 69.4 mm**
(measured this session: the 99.0 × 63.0 mm well-centre array — `well_grid` 11 × 9.0 by 7 × 9.0
(12 columns and 8 rows at 9.0 pitch; the span is pitch × *gaps*, not × wells) — plus the well
footprint at its outer ring). The aperture is 88 × 52.

    105.4 − 88 = 17.4 mm deficit on X
     69.4 − 52 = 17.4 mm deficit on Y

Symmetric about a centred aperture, that is 8.7 mm short per side against a 9.0 mm well pitch, so
exactly the perimeter ring falls outside: `plate_support_frame` material sits under **well columns 1
and 12 and rows A and H — 36 of the 96 wells on every tile**. The cradle cutout number (≥ 90 × 54)
is consistent with the aperture and inconsistent with its own stated rationale; it was sized to pass
the window through, not to clear the wells.

**How it was found.** Rising-probe metrology through the tile apertures this session (see the
standoff entry below) required the clear span to be stated as a number rather than as "the window",
at which point it no longer matched the well footprint.

**What it supersedes.** The "nothing under any well" clause at all four sites above. Two of them are
sign-off rows: a technician would today mark "Plate seated skirt-only, nothing under any well" as
passed while frame material sits under 36 wells per tile, because the cradle they were told to build
is the one that produces that state. The clause is not a measurement failure to be re-measured; it
is a specification the hardware has never met. Those files are owned elsewhere and are not edited
here — this entry is the record that the clause is wrong, not a correction applied to it.

**The fix is one number, and it is not free.** Enlarging the aperture to ≈ 110 × 74 mm satisfies the
cradle spec and reaches every well (see the well-count entry below). It also re-imposes the 99 mm
scan span and takes the corridor budget of the next entry back with it. The two are coupled and must
be decided together.


## 2026-09-23 — the 15.56 mm head budget is an artifact of scanning wells the aperture never admitted

**What was believed.** That the scan-axis head-footprint budget is **15.56 mm**, frozen in
`cad/one_row_coupon.params.json:147` and `src/aevum_smis/manifest.py:68`. The 2026-09-21 OC-A15
correction derived it correctly from the live geometry: leg inner faces at X = 17.10 / 134.50, a
99.0 mm well span, near slack 7.78 mm, budget 2 × 7.78 = 15.56 mm. Its stated consequence — "at
15.56 mm **no RMS-threaded objective threads the corridor**", including the Ø20 reference 4× head —
has governed the objective search since.

**What is true.** The arithmetic is right; the input is not. The 99.0 mm span is the span of all 12
well columns, and the 88 mm aperture has never admitted 12 columns. With the optical inset of the
well-count entry below applied, it admits **8**, spanning 63.0 mm. The budget against the set the
head can actually reach:

    near:  2 × (42.88 − 17.10)  = 2 × 25.78 = 51.56 mm   ← binds
    far:   2 × (134.50 − 105.88) = 2 × 28.62 = 57.24 mm
    budget = min(51.56, 57.24)  = 51.56 mm

**15.56 → 51.56 mm, a 3.31× increase, with no CAD change.** The whole gain comes from
parameterising the traverse check on the reachable column set instead of on the nominal well grid.
42.88 and 105.88 are the first and last reachable column centres in the corridor frame, measured
this session; their separation is the same 63.0 mm the aperture admits, computed independently.

**How it was found.** Re-verified independently this session against the same leg inner faces the
OC-A15 entry used, after the well-reach count showed that four of the twelve columns are not
optically reachable at any working distance.

**What it supersedes.**

- The operative consequence of OC-A15, not its arithmetic. At 51.56 mm an Ø20.32 RMS barrel clears
  with 31.2 mm to spare. "No RMS-threaded objective threads the corridor" is withdrawn. The
  derivation comment at `manifest.py:59-62` carries the superseded claim.
- `src/aevum_cad/row_coupon/parts/observer.py:184-193`, which states that "after the 99 mm well span
  the dry-bay X leaves only ~0.2 mm of budget", that "the residual after the well span is ~0.2 mm,
  not 120 mm", and concludes "the camera must be folded coaxially over the objective or taken
  offboard". That conclusion rests entirely on the 99 mm span and does not survive it. Coaxial
  folding may still be the right choice; it is no longer forced by X.

**Recommendation, recorded not applied** (this pass is docs-only): parameterise the traverse check
and the frozen constant on the reachable column extent —
`cad/one_row_coupon.params.json:147`, `src/aevum_smis/manifest.py:68` and the paired assertion at
`src/aevum_cad/row_coupon/parts/observer.py:663-668`. The constant is frozen by design because it is
a contract with external heads, so changing it is a contract change, not a correction.

**The honest caveat.** This budget is not found money. It is bought by conceding that a third of the
plate is unreachable. Enlarging the aperture to ≈ 110 × 74 mm restores all 12 columns, and the
budget returns to 15.56 mm. Whoever specifies the head must be told which of the two worlds the
number came from.


## 2026-09-23 — the objective is a thermal short into the well, and it is a causal-inference defect

**What was believed.** That objective standoff is a geometry and optics question — working distance,
aperture, corridor — with the thermal envelope owned by the row module's 37 °C control loop.

**What is true.** A close objective is a large metal body at bay ambient held millimetres from a
37 °C bath through 0.17 mm of glass. It is a heat sink, and it conducts. Steady-state model,
37 °C bath against a 25 °C bay:

| head | WD (mm) | cells settle at | ΔT |
|---|---:|---:|---:|
| water 60×/1.20 | 0.31 | 29.50 °C | **7.50 K** |
| dry 40×/0.95 | 0.18 | 35.04 °C | **1.96 K** |
| dry 40×/0.60 | 3.0 | 36.77 °C | 0.23 K — passes a 0.3 K budget |
| dry 20×/0.45 | 7.5 | 36.85 °C | 0.15 K — passes |

**Every head closer than ≈ 3 mm busts a 0.3 K budget, dry included.** Dryness is not the protection;
distance is. This is a new gate on the objective search, sitting alongside corridor and aperture, and
it cuts in the opposite direction to NA.

**Why this specifically confounds the work.** The platform exists to fit causal models of
perturbation response. A well's temperature would then depend on how recently and how often the
objective visited it — which is a function of the scan schedule, which is a function of which wells
carry which condition. That is an unlogged thermal perturbation **correlated with treatment
assignment**: the textbook shape of a confounder, and one that looks like a real biological effect
because it is a real biological effect, of the wrong cause. A 7.5 K depression is not a measurement
artifact to be subtracted; it is a second experiment running underneath the first.

**The mitigation is local, not global.** A 37 °C nose heater on the objective removes the sink. A
37 °C bay does not: `IMX178` dark current roughly doubles per 6–7 K, which destroys the long
integrations that the Raman and luminescence rows of the SMIS catalog depend on. Warming the bay to
protect the sample would cost the modalities the bay exists to host. Prior art is consistent —
PerkinElmer Opera Phenix Plus and Yokogawa CellVoyager CV8000 both run automated immersion from below
through glass-bottom plates, and both condition the objective rather than the enclosure.

**How it was found.** Modelled this session while checking whether the newly available short
working distances (next entry) were admissible on anything other than geometry.

**Stated caveat, and it is not small.** The model uses an **estimated** objective-to-ambient
conductance of 50 mW/K. The *ordering* of the table is robust — it follows from the standoff and
survives any plausible conductance — but the *absolute* ΔT is not. Nothing here should be quoted as
a measured temperature. This is the highest-value cheap early measurement on the board: a thermistor
or the existing MLX90614 sample-plane path against a parked objective at two standoffs settles it in
an afternoon and either confirms the gate or relaxes it.

**Water immersion is separately closed, and not by this entry.**
`docs/knowledge/materials_strategy.md:115-116` states that per-well sensing is "optical … through the
glass from the row module's dry bay or lid, not contact." An immersion objective puts couplant on the
plate underside. That is a contact path, and the 60×/1.20 row above fails the thermal gate as well.
Whether immersion is admissible is **not an interpretation question**: it would require an explicit
written amendment to that clause plus its own decision-log entry. No such amendment is made here, so
immersion remains closed.


## 2026-09-23 — the standoff conclusion inverts a second time, on a measured fact rather than a re-reading

**What was believed.** The 2026-09-21 entry above established the cell-plane standoff as 19.90 mm
against the head's front-face ceiling at z = −8, concluded that **any** objective needs WD ≥ 19.90 mm
to reach the cell plane at all, and excluded the entire short-working-distance catalogue. It closed
by naming the one lever nobody had pulled: the base carries an 88 × 52 mm aperture the front element
could rise into, and "that question should be answered before any objective is bought."

**What is true.** The question has now been answered, by measurement. Probe cylinders up to **Ø25 mm
rise unobstructed from z = 0 to z = 11.71 at every tile aperture centre** — the optical column is
clear to within **0.19 mm of the glass**. The nose may enter the aperture, and nothing in the solid
model touches it on the way up.

The travel to use it already exists in the parameters. Running the existing `focus_stroke_z` = 12.0
**upward** from the traverse plane puts the nose at z = +4.00:

    nose at z = +4.00 → cell plane 11.90 → WD 7.90 mm
    vertical budget: carriage_top_clearance_z 8 + front_end_height_z 28 + focus_stroke_z 12 = 48
                     against observer_sweep_depth_z 80 → 32 mm slack

**So the admissible objective class inverts back**, and further than it started: at WD ≈ 7.9 mm the
ELWD correction-collar class applies (Nikon CFI S Plan Fluor ELWD 20×/0.45, WD 6.9–8.2 mm, collar
0–2 mm; the 40×/0.60 of the same family at WD 2.8–3.6 mm). That class matters for a reason beyond
reach: the uncorrected 0.17 mm coverslip imposes a Maréchal cap of NA ≤ 0.363 at 550 nm (0.336 at
405, 0.397 at 785), and **a correction collar removes the cap**. Long-WD catalogue objectives are
zero-coverslip designs and carry no collar — a Mitutoyo M Plan Apo 20×/0.42 at WD 20 mm runs 1.79×
over Maréchal through 0.17 mm of glass. The long-WD class both costs aperture and cannot use it.

**Why this is not a flip-flop, and the distinction is the point.** The three corrections before this
one — the corridor, the phantom plate window, the standoff — were all the same failure: a
decomposition written once in prose and thereafter cited instead of recomputed. Each retracted an
*arithmetic error*. This entry retracts nothing of the kind. **19.90 mm is still correct.** It is
still the standoff from the traverse plane, and every number in the 2026-09-21 entry still holds at
that plane. What changed is that the traverse plane is no longer the only plane the nose may occupy,
and that is a **new measured fact about the solid model that no prior entry had taken or assumed** —
the 2026-09-21 entry explicitly flagged it as unanswered and asked for it. The earlier conclusion was
correct given what was then known and is superseded by evidence, not by re-reading the same evidence
more carefully. A conclusion that moves when a measurement arrives is the log working; one that moves
when someone re-reads the parameters is the log failing.

**What it costs and what it constrains.**

- **Tile crossing, not well stepping.** Between tiles the `plate_support_frame` (z 0 … 11.20) blocks
  at z = 0.05, so the nose must retract to cross a tile boundary — **3 retract cycles per row of 4
  tiles, not one per well.** Within a tile's aperture the nose stays raised for the whole traverse.
- **Safety.** At 40×/NA 0.60 the nose sits 2.6–3.4 mm below a *consumable* plate, and the plate is
  the thing we have committed never to touch. **Recommendation, recorded not applied:** a hardware
  Z-gate that cuts XY motor enable whenever the nose is above z = 0 — interlock, not firmware
  policy, because the failure mode is a scrapped experiment and a smashed objective on the same
  motion.
- **A software gate now rejects geometry the model says is clear.**
  `src/aevum_smis/manifest.py:193-200` computes `vertical_required` as an additive sum
  (`front_face_clearance + front_end_height_z + focus_stroke_z + service_margin_z ≤ z_budget`). For a
  60 mm-parfocal objective that is 8 + 57 + 18 = 83 > 62, which rejects **every** such head, although
  the 32 mm of slack above shows the swept envelope closes. The additive form adds clearances that
  are never occupied simultaneously. **Recommendation, recorded not applied:** replace it with a
  swept-envelope check that *retains* a hard retract-plane assertion — the additive form is wrong,
  but the retract plane it accidentally enforces is the thing standing between the nose and the
  plate, and must not be lost in the rewrite. No code is edited in this pass.


## 2026-09-23 — the optically reachable well count is 128, not 384 and not 240

**What was believed.** That the coupon covers 384 wells. `covered_well_count` reports 384 at
`src/aevum_cad/row_coupon/layout.py:865` and `:965`, where it is `len(all_well_centers)` — the total
number of wells on the coupon. It applies no aperture test and no optical test whatsoever; it is a
well count wearing a coverage name. An intermediate figure of **240** appeared while checking it:
that one does test the aperture, by counting well centres that fall inside it.

**What is true: 128 of 384.** 240 is closer and still wrong, because a well is not reachable when
its centre is inside the aperture — it is reachable when the optical cone, or the physical nose,
clears the aperture edge. That demands an inset from the edge, and the inset is what removes the
next ring of wells.

    long WD (19.90 mm), NA 0.363:
        cone at the aperture plane = 2 × 11.90 × tan(asin(0.363)) = 9.27 mm
        inset = 9.27 / 2 = 4.64 mm
    short WD (7.9 mm), nose OD 8–20 mm:
        inset = 4–10 mm

    aperture 88 × 52, well pitch 9.0, array 99.0 × 63.0 centre-to-centre
        centres inside the aperture:        10 columns × 6 rows = 60 per tile = 240
        centres clearing a 4.64 mm inset:    8 columns × 4 rows = 32 per tile = 128

**The two working-distance regimes give the identical answer.** A long-WD head loses the ring to its
collection cone; a short-WD head loses the same ring to its barrel. The inset ranges overlap across
the whole realizable catalogue, and neither buys back a single well. Reach is set by the aperture, not
by the objective — which is why no objective purchase can fix it and why the 88 × 52 number is the one
that matters.

**How it was found.** Computed this session from the live `well_grid` and `dry_bay` parameters while
establishing the reachable column extent for the corridor entry above; the 8-column result there and
the 8-column result here are the same computation reached from two directions.

**What it supersedes.** Any statement of coverage as 384, and the intermediate 240. Note what the
three numbers actually measure: 384 is how many wells exist, 240 is how many the aperture frames, 128
is how many can be imaged. Only the third is a coverage claim, and it is the one no artifact reports.

**Recommendation, recorded not applied:** `covered_well_count` at `layout.py:865` and `:965` should
either be renamed to a plain well count or derived as a genuine reachability count with the inset as
an explicit input; a name that asserts coverage while computing a total is the kind of defect that
propagates into every downstream estimate that cites it. Any per-pass throughput or duty-cycle figure
must likewise be stated against the reachable set, not the plate.

**And the coupling, again.** Enlarging the aperture to ≈ 110 × 74 mm reaches 384 of 384 *and*
satisfies the cradle spec of the first entry — and hands the corridor budget of the second entry back
from 51.56 mm to 15.56 mm. Three of today's five findings terminate on that one dimension. It should
be decided as one decision, not three.


## 2026-09-23 (follow-up, same day) — three corrections to the cradle-contradiction entry above

This log is append-only, so the entry at "the aperture violates the Stage-0 cradle spec by 17.4 mm
on both axes" is not rewritten. Three of its statements are wrong or now stale, and this entry is
the correction of record. The finding itself — that the aperture does not satisfy "nothing under any
well" — is unaffected and is not retracted; only its ruling number, its citations, and its closing
claim about ownership change.

### 1. The ruling well diameter was never named, and 105.4 × 69.4 matches no parameter

**What was written.** "'Nothing under any well' needs a clear span of **105.4 × 69.4 mm** ... plus
the well footprint at its outer ring", and a **17.4 mm** deficit on both axes.

**What is true.** 105.4 − 99.0 = 6.4 mm and 69.4 − 63.0 = 6.4 mm, so that span implies a ruling well
diameter of exactly 6.4 mm. No such parameter exists. The three candidates in
`cad/one_row_coupon.params.json:23-25` are:

| Parameter | mm | Required clear span | Deficit vs 88 × 52 |
|---|---:|---|---:|
| `upper_well_diameter` (moulded well OD) | 6.80 | 105.80 × 69.80 | **17.80 mm** |
| `lower_well_diameter` (clear glass bottom) | 6.21 | 105.21 × 69.21 | **17.21 mm** |
| `well_bottom_area_equivalent_diameter` | 6.18 | 105.18 × 69.18 | **17.18 mm** |

The clause has a mechanical reading and an optical one and they do not resolve to the same number.
"Nothing under any well" as a *seating* statement — the thing the sign-off row asks a technician to
see — is about the moulded well body, so **`upper_well_diameter` 6.80 rules it: 105.80 × 69.80, a
17.80 mm deficit on both axes**. The optical reading (nothing under any well's clear glass) gives
105.21 × 69.21 and 17.21 mm. 6.4 mm and 17.4 mm are neither, and are withdrawn.

**What does not change.** The per-side shortfall is 8.90 mm at 6.80 and 8.61 mm at 6.21, both below
the 9.0 mm well pitch, so the conclusion is identical under either diameter: exactly the perimeter
ring falls outside, and `plate_support_frame` material sits under well columns 1 and 12 and rows A
and H — 36 of the 96 wells on every tile. The entry's "8.7 mm short per side" was derived from the
same unsupported 6.4 and should be read as 8.61–8.90.

**The three aperture numbers in circulation are a ladder, not a disagreement.** 105.80 × 69.80 is
the requirement; `observer_optical_bench.md` Assembly step 2 ("Plate cradle") cuts the printed bench
cradle at ≥ 107 × 71, which clears it on both axes with 1.2 / 1.2 mm to spare; the ≈ 110 × 74
recorded for the bay aperture is the requirement plus enough margin to also clear the optical inset
of the well-count entry, which the bare requirement does not.

**How it was found.** A citation check this session: the figure was traced back for its parameter
and had none.

**Cross-references that carry the withdrawn number** and are owned elsewhere:
`observation_module.md:125-126` ("Aperture a skirt-flange-only cradle would need … 105.4 x 69.4"),
`:724` and `:793` (both "17.4 mm"), and the "The session measurement quotes 105.4 × 69.4" line in
`observer_optical_bench.md`. The bench doc already brackets the figure correctly under the two
defensible diameters and quotes 105.4 only as the session measurement;
`observation_module.md:125` additionally attributes 105.4 × 69.4 to `observer_optical_bench.md`,
which does not assert it — that provenance is wrong as written. Both are for their owners to
correct.

### 2. Two of the four citations no longer point at what they quote

**What was written.** A four-row table of sites stating the clause, cited by line.

**What is true.** Two of the four line numbers went stale inside the same pass that wrote them,
because the corrections made to those files shifted their own line numbers:

| As cited | Now |
|---|---|
| `observer_optical_bench.md:76` | verifies unchanged: "the full 88 × 52 mm observation window is open from below — nothing under any well, skirt flange only" |
| `observer_optical_bench.md:304` | wrong content — not blank. `:304` now holds the middle of the tiling-throughput recompute note ("48 hourly passes**. *(Recomputed 2026-09-23 from M_eff 11.11× to 10.0×: this"). The quoted "Central cutout ≥ 90 × 54 mm …" text survives only as a quotation, at `:475-477` ("The bench cradle follows the same arithmetic") and again inside the corrected step at `:714`; the live **Assembly step 2 ("Plate cradle")** is at `:711-723` and reads **≥ 107 × 71 mm** |
| `docs/protocols/observer_optical_bench_stage0.md:58` | blank line. That step is now **`:62`** and reads **≥ 107 × 71 mm** |
| `data/measurements/templates/observer_optical_bench_stage0.md:24` | wrong line — `:24` is `| Measurement images folder |  |`. The gate row is `:31`, and it was corrected in this same pass to "Plate seated skirt-only in a cradle whose central cutout is >= 107 x 71 mm, so nothing sits under any well", with a note recording the superseded wording and the bay-vs-bench divergence |

`observer_optical_bench.md` is being revised in the same pass and its line numbers kept moving while
this entry was being written: Assembly step 2 went :304 → :679 → :700 within the hour, and came to
rest at **:711-723**. Sites in that file — and in the measurement template, which moved for the same
reason — are therefore anchored here by heading and quoted text, which are stable, rather than by
line.

### 3. "Those files are owned elsewhere and are not edited here" is false for three of the four

**What was written.** "Those files are owned elsewhere and are not edited here — this entry is the
record that the clause is wrong, not a correction applied to it."

**What is true.** In the same pass, three of the four sites were corrected:

- `observer_optical_bench.md` gained a dated note ("**Note added 2026-09-23.** The cradle spec
  quoted here is itself internally inconsistent …") directly under the clause at `:76`, stating that
  the principle stands and the geometry violates it.
- `observer_optical_bench.md` Assembly step 2 ("Plate cradle") was rewritten from ≥ 90 × 54 mm to
  **≥ 107 × 71 mm**, with the superseded text quoted in place.
- `docs/protocols/observer_optical_bench_stage0.md:62` was rewritten to the same ≥ 107 × 71 mm.

Only **`data/measurements/templates/observer_optical_bench_stage0.md:24`** is genuinely untouched,
and it is the one that matters most operationally: it is the sign-off row. A technician running
Stage-0 today still marks "Plate seated skirt-only, nothing under any well" against a cradle that
can now achieve it (≥ 107 × 71) but against a **bay** aperture (88 × 52) that cannot. The bench and
the bay have diverged, and the template does not say which one it is gating.

**So the standing defect is two sites, not four:** the `dry_bay` aperture itself
(`cad/one_row_coupon.params.json:91-92`, CAD, not changed in a documentation pass) and that
measurement-template row. Both are owned elsewhere; this remains a record, not a fix.
*(Superseded by the end-of-pass note below: the template row was corrected before the pass closed,
so the standing defect is one site, not two. The paragraph is left standing because it is the
exhibit for its own thesis.)*

**How it was found.** Re-reading the four cited sites against the working tree after the same pass
had edited three of them. The failure mode is the one this log has now recorded twice: a claim about
the state of other files written *before* the pass that changes those files finishes, and never
re-checked. The guard is to cite by quoted text — or by heading and step name — rather than by line
alone whenever the cited file is itself in flight, and to re-verify citations at the end of a pass
rather than when they are written.

---

**Follow-up 2026-09-23, end of pass.** Re-verified at close of pass, against the finished working
tree, this entry's own claims about other files. Three of them had gone stale — inside the entry
whose subject is exactly that.

*The cross-reference list in §1 ("Cross-references that carry the withdrawn number") is stale in
every element.* `observation_module.md` now carries the corrected figures and cites them to the
right owner: the aperture requirement is at **`:154-155`** and reads 105.21 × 69.21 / 105.80 ×
69.80 with a 17.21–17.80 mm deficit, and the same bracket appears at **`:790`** (driver row 11) and
**`:860`**. `:125-126` is the unrelated WD-19.90 traverse-plane paragraph; `:724` is OT-2 lease
prose; `:793` is the "Rows 11 and 12 are appended, not inserted" note. None of the three holds the
withdrawn 105.4 × 69.4 or a bare 17.4 mm, and `observation_module.md` no longer carries a bare 17.4
anywhere (only the 117.4 mm leg corridor at `:114`). The provenance objection is also resolved:
`:154` now attributes the **bracket** to `observer_optical_bench.md` and says only that "the
session's 105.4 × 69.4 sits inside that bracket", which is accurate.

*The `observer_optical_bench.md:76` row of the §2 verification table is off by one to two lines.*
The quoted clause "the full 88 × 52 mm observation window is open from below — nothing under any
well, skirt flange only" is at **`:77-78`**; `:76` is the preceding half-sentence ("wrong, and they
contradicted the two paragraphs above and the Stage-0 cradle spec"). The row's verdict — that the
clause verifies unchanged — holds; only its line does not.

*§3's conclusion is stale.* The measurement-template gate row was corrected later in the same pass,
to a numbered cradle cutout (**≥ 107 × 71 mm**) carrying the bay-vs-bench divergence in the row
itself: the bay's 88 × 52 aperture does not meet it, ~17 mm short on both axes, with a pointer back
to this log. So all four sites of the clause were amended in this pass, and **the standing defect is
one site, not two: the `dry_bay` aperture at `cad/one_row_coupon.params.json:91-92` (88.0 × 52.0),
unchanged because this is a documentation pass.**

*One arithmetic error in the parent entry was corrected in place* rather than appended, because it
was a mis-citation of a parameter and not a claim: the well-centre span was attributed to `well_grid`
"12 × 9.0 by 8 × 9.0", which is 108 × 72. The span is pitch × *gaps* — 11 × 9.0 and 7 × 9.0 = 99.0 ×
63.0 — which is what `observer_optical_bench.md` already states correctly as "(11 × 9.0 pitch)". The
99.0 × 63.0 figures the entry reasons from were right; only the parenthetical was wrong.

**How it was found.** A close-of-pass re-read of every line number this entry cites, against the
tree as it finally stands rather than as it stood when the line was written. That is the guard §3
proposed one screen earlier and did not itself apply, which is why three of its own citations
decayed. The rule now has teeth: **anchor by quoted text, and re-verify at close of pass** — and
where a cited file is in flight, cite its heading or step name and quote the clause, so a moved line
is a recoverable pointer rather than a false statement.

*Cross-reference for the owner of `observation_module.md`:* `:154` cites
`observer_optical_bench.md:403-408` for the requirement bracket. That content is now at roughly
`:425-440` of the bench doc (`:403-408` is the depth-of-field/CTE paragraph). Same decay, different
file; recorded here, not fixed here.

### Follow-up 2026-09-23, second close of pass — the citation-decay entry decayed a second time

*Appended, not edited in place.* The two follow-ups above re-verified their own line numbers
"against the finished working tree". They were right about the tree as it stood at that moment and
wrong an hour later: `observation_module.md` and `observer_optical_bench.md` both grew during the
remainder of the same pass, and every bare `:NNN` in those follow-ups moved. This is the third
recorded instance of the same failure inside the one entry whose subject is that failure, which is
sufficient evidence that the guard as written — "re-verify at close of pass" — does not work, because
a pass has more than one close.

**The rule is amended, and this amendment is the operative one:**

> **Do not cite a line number into a file that is still in flight.** Cite the heading, the table row
> name, or the step name, and quote enough of the clause to be greppable. A bare `:NNN` is
> permissible only into a frozen artifact — a param file, a source file at a named commit, or a
> closed log entry. A line number is a convenience that decays silently; a quoted anchor decays
> loudly, or not at all.

Every anchor in this section and in the two follow-ups above is hereby **superseded by its text
anchor**. Where those follow-ups gave `:154-155`, `:790`, `:860`, `:76`, `:403-408` and `:425-440`,
read instead:

| Claim in the follow-ups above | Anchor to use | Where it sits as of this append |
|---|---|---|
| the corrected aperture requirement | `observation_module.md`, § *Aperture-limited well reach — 128 of 384*, row "Aperture a skirt-flange-only cradle would need" | `:169`, deficit row `:170` |
| the same bracket in the driver table | `observation_module.md`, driver row **11**, "Aperture-limited well reach" | `:860` |
| the requirement bracket's owner | `observer_optical_bench.md`, § *Reachable wells, and the "nothing under any well" contradiction*, the two-row bracket table | heading `:448`, table `:460-461` |
| the verified "open from below" clause | `observer_optical_bench.md`, the parenthetical "(the full 88 × 52 mm observation window is open from below — nothing under any well, skirt flange only)" | `:81-82` |

Those line numbers are given once, for this append, and are **not** the citation. The text is.

**Three substantive corrections found by the same re-read, fixed in place in their own files** (they
were false statements, not decayed pointers):

1. `observer_optical_bench.md` and `sensor_module_interface.md` both told the reader that
   `remaining_work.md` still carried the withdrawn **192-well** throughput basis "and needs the same
   correction by their owner". It was corrected in the same pass. Both now state the closure.
2. `observer_optical_bench.md`'s implementation-status paragraph described
   `_observer_carriage_traverse` as surfacing a **44.6 mm dry-bay Y overflow**. The live check
   returns `dry_bay_overflow_y_mm = 0.0` and `fits_dry_bay = True` — the thin-truck topology resolved
   it. What still blocks `clears_traverse` is `deck_foot_collision_count = 1` and
   `scan_corridor_margin_mm = −2.72`. `observation_module.md`'s driver row 2 carried the same stale
   44.6 (against a pre-2026-06-14 bay-Y of 347.9; live is 357.5). Both corrected.
3. `materials_strategy.md` labelled the ~0.53 mm plate-to-frame seating gap "**measured
   2026-09-23**". No caliper record exists. The number is sound but **derived**: glass outer surface
   z = 11.73 − `plate_support_frame` top z = 11.20 = 0.53. The label was the defect, not the figure;
   both that file and `remaining_work.md` IN-C10 now state the derivation.

**One conditional was being read as a wall.** `docs/protocols/observer_leg_corridor_objective_metrology.md`
and its measurement template carried **15.56 mm** as the live head-footprint budget, and with it the
consequence that "no RMS-threaded objective threads the corridor at all". 15.56 mm is the residual
after requiring a scan across all 12 well columns, which the 88 × 52 mm aperture never admitted; the
reachable budget is **51.56 mm**, at which a Ø20.32 RMS thread clears by +31.24 mm. A dated
correction block now sits at the head of both, stating the coupling: enlarging the aperture to
~110 × 74 mm to recover all 384 wells returns the budget toward 15.56 mm. **The wide aperture and
the wide head are alternatives, not a package.** The frozen SMIS contract still carries 15.56 mm on
purpose (`src/aevum_smis/manifest.py:68`, `scan_corridor_footprint_max_mm`) — changing it is a
SMIS-major bump plus a code change, and no code changed in this pass.

**Still standing, unchanged and deliberate:** the `dry_bay` aperture at
`cad/one_row_coupon.params.json` remains 88.0 × 52.0. This was a documentation pass.

### Follow-up 2026-09-23, convergence round 2 — what a three-lens adversarial verification found after the first close

*Appended.* The follow-up above was written at what looked like the end of the pass. A verification
round then ran three independent lenses over the finished tree — cross-reference integrity,
independent re-derivation of every number, and honesty/internal-consistency — and handed each
finding to a separate agent instructed to **refute** it. Twelve findings survived refutation, and
they deduplicate to eight defects. Recording them because three were **caused by the fixes in the
follow-up above**, which is the more useful lesson.

**Defects the pass itself introduced.**

1. *Changing a number without sweeping the tree for the old one.* The bench BOM headline was
   recomputed from ¥1,885 to **¥1,940** (the table's own rows sum to 1,940; 1,885 reproduced from
   nothing). Three other files went on quoting ¥1,885 as the live cost —
   `observation_module.md` twice and `remaining_work.md`'s critical path — and the recompute's own
   section heading still read "Recommended first purchase (~$230)" twenty-seven lines below the
   bullet that had just restated it as **¥1,265 ≈ $178**. All four corrected.
2. *Citing a section by name without checking the name holds the content.* The 0.53 mm
   plate-to-frame derivation was correctly relabelled from "measured" to derived, but was sourced to
   `observation_module.md`, § *Aperture-limited well reach*, which contains neither z anchor. Both
   live in § *Vertical motion model — retract to cross tiles, not to cross wells*. Corrected. A
   heading anchor is only better than a line number if the heading is verified too.
3. *A retarget that landed on the wrong axis.* `remaining_work.md` OC-A16 had already been
   retargeted once this pass, away from `observation_module.md:217`; the new target
   (`:258-280`) is the thin-truck **Y** fix, while the ~0.2 mm residual it cites is an **X**-axis
   claim living in the "But the Y fix relocated its burden onto the X scan axis" paragraph. The
   same error class the retarget was correcting. Now anchored by quoted text.

**Pre-existing defects the lenses surfaced.**

4. **The clear-column figure conflated two different gaps, in six places.** The aperture column is
   measured clear to **z = 11.71**. The glass outer surface is z = 11.73 and the cell plane is
   z = 11.90, so the column is clear to **0.02 mm** of the glass and **0.19 mm** of the cell plane.
   Six sites read "clear to 0.19 mm of the glass outer surface (z = 11.73)", which is internally
   contradictory — it states a gap and, in the same parenthesis, the two numbers that disprove it.
   Corrected in `observer_optical_bench.md` (3 sites), `observation_module.md`,
   `sensor_module_interface.md` and the Stage-0 record template. **`decision_log.md:1884` carries
   the same wording and is NOT edited** — this paragraph supersedes it.
5. **A pixel span derived from retired sampling.** `observation_module.md` costed fiducial
   registration at "~1400-3300 px for a 2 mm circle", which reproduces only from the withdrawn
   "~0.6-1.4 µm/px". At the corrected 2.16 µm/px it is **~930 px**, and ~2,300 px on the 10× drill-down.
6. **A DOF half-depth computed on the wrong convention.** The leg-corridor protocol paired
   "±27.5 µm at NA 0.10" (correct: half of 55.0 µm total) with "±3.5 µm at NA 0.42". λ/NA² gives
   3.12 µm **total** at NA 0.42, so the half-range is **±1.56 µm**. Corrected.
7. **An unconverted term from the retired Y-split pipeline.** `one_row_coupon_first_print_readiness.md`
   and `data/measurements/README.md` still said the traveler must match "the current **split**
   sliced-output hashes" beside a correctly-renamed "final-piece Gate 1 QC worksheet". Corrected.
   The frozen 2026-06-02 measurement record keeps its `y_split` filenames — those are the commands
   that were actually run that day.

**The rule this adds to the one above.** Anchoring by quoted text is necessary and not sufficient.
**When you change a value, grep the tree for the old one before closing** — a recompute that leaves
the superseded figure live in three other files has made the inconsistency worse, not better, because
it now has a documented winner that nothing points to. And **verify a heading anchor by opening the
heading**, not by remembering what is under it.

### Follow-up 2026-09-23, convergence round 3 — the operator-facing files were the ones still broken

*Appended.* Round 2 was retargeted at what round 1 under-covered: `docs/protocols/`,
`data/measurements/templates/`, `docs/knowledge/`, and the root-level engineering docs. Six findings
survived refutation, deduplicating to five. **Four of the five were in files an operator actually
fills in or runs commands from**, not in the engineering prose both earlier rounds had been grinding
over. That is the finding worth keeping: the verification effort had been pointed at the documents
that argue, not the documents that instruct.

1. **The blank first-print record template was the last live file on the retired Y-split pipeline.**
   `data/measurements/templates/one_row_coupon_first_print_readiness.md` asked the operator to fill
   in a session field named `Active print queue mode` — but `constants.py`
   (`FIRST_PRINT_ACTIVE_QUEUE_MODE_FIELD`) names it **`Final print queue`**, with the single legal
   value `final_print_pieces`. It also carried four link rows (`Split slicer queue`, `Split sliced
   output worksheet`, `Split print batch traveler`, `Split Gate 1 QC worksheet`) that appear nowhere
   in `FIRST_PRINT_PREFLIGHT_LINK_FIELDS` and that **nothing in `src/`, `scripts/` or `tests/`
   reads**, and 17 command rows invoking `scripts/*_y_split_*.py` files that are all deleted
   (`ls scripts/ | grep y_split` is empty; all 17 `_final_piece_` counterparts exist). This is not a
   dead document: `scripts/scaffold_row_coupon_first_print_record.py` defaults `--template` to this
   exact path and copies it verbatim apart from a fixed list of patched link fields, so every record
   scaffolded today inherited the dead field names and the deleted commands. Migrated to the names
   the already-updated protocol uses (`Final print queue`, `Final-piece slicer queue`, `Final sliced
   output worksheet`, `Final Gate 1 QC worksheet`, `Final print batch traveler`) and all 47 `y_split`
   occurrences renamed.
2. **`data/measurements/README.md` carried the same dead command chain** — 47 more `y_split`
   occurrences across two operator sections. Migrated identically.
3. **The dead `src/aevum_cad/row_coupon.py` module path** survived in four live docs after that
   module became a package. `observation_module.md` had *already listed this as a defect it was
   fixing*, and fixed only its own copies. Corrected in `docs/knowledge/README.md`,
   `docs/engineering/one_row_coupon.md`, `docs/protocols/one_row_coupon_first_print_readiness.md`
   and `docs/protocols/gate6_observer_evidence_row_schema.md`. The 2026-06-02 record keeps its
   copies: those are the commands that were actually run.
4. **The leg-corridor protocol's decision step used the arithmetic its own item (e) refutes.** Step
   1 said "compute `well_window_x + FE_scan` and compare to `W_corr`", the centred single-gap form,
   while item (e) states the array is *not* centred (live slack 7.78 near / 10.62 far) and the budget
   is `2 × min(near, far)`. It also quoted the residual as a "placeholder 0.12 mm"; the live value is
   **−2.72 mm** — it strikes. Both corrected.
5. **One more heading anchor that did not hold its content**, the same class as round 2's defect #2:
   `observation_module.md` sourced the `fields_per_well` candidate to `sensor_module_interface.md`,
   § *Software — the `acquire() → Evidence` ABI (FROZEN)*, which does not contain the identifier at
   all. It lives under § *The intervention ledger (CANDIDATE — recorded, not decided)*. The two other
   files citing the same content anchored it correctly, so this was the lone bad one.

**What this round adds.** The earlier rules were about *how* to cite. This one is about *where to
look*: **the operator-facing artifacts — blank templates, record forms, command lists — decay
silently and cost the most, because a stale engineering paragraph misleads a reader while a stale
template is copied into the next real run.** When a pipeline is renamed, the rename is not finished
when the code and the protocol agree; it is finished when the blank form an operator fills in agrees
too. A grep for the retired token across `data/` and `scripts/` is the check, and it is cheap.

### Follow-up 2026-09-23, convergence round 4 — four findings, and one the pass had been routing around

*Appended.* Round 3 ran the same three lenses over the tree after rounds 1–2 were fixed, with those
fixes pinned as ground truth and an explicit instruction that a clean verdict was the expected
outcome. Four findings survived refutation. The survival counts across the three rounds — **12, 6,
4** — are converging, and the character of what survives has changed: rounds 1–2 found broken
pointers, round 3 found a withdrawn conclusion still being acted on.

1. **`remaining_work.md` OC-A15 still stated a withdrawn conclusion as live, and listed work to do
   about it.** The bullet read "**no RMS objective threads this corridor at all**" followed by
   "Three open resolutions" — source a sub-15.56 mm head, re-route the service shroud, or reshape
   the corner posts into X-strip rails. That consequence is withdrawn in four other places
   (this log; `sensor_module_interface.md`, § *The mechanical wall was an artifact — 15.56 mm →
   51.56 mm*; the leg-corridor protocol's correction banner; and its measurement template), **and
   twice in the same file** — OC-A16 and OC-A18(a) both carry the 51.56 mm budget, and OC-A16 even
   carries the explicit "Superseded in part 2026-09-23 by OC-A18(a) below" marker that OC-A15
   lacked. This is the worst class of defect in the set, because the other three misdirect a
   *reader* while this one lists **procurement and CAD work that is not required**: against the 8
   reachable columns a Ø20.32 RMS barrel clears by **+31.24 mm**. The marker is now applied, with
   the aperture coupling and the frozen-contract caveat stated.
2. **`data/measurements/README.md` kept the dead field names in prose.** The round-3 migration
   renamed 47 `y_split` script and path strings in that file but not the sentence telling the
   operator to "set `Active print queue mode` … to `split_y`" and naming the three `Split *`
   worksheets. A token-level rename does not catch the prose that explains the token.
3. **`docs/knowledge/byonoy_plate_readers.md` still carried the air-side `NA²/4 ≈ 0.25 %`
   collection fraction, live and unmarked, in two places** — and two engineering docs were citing
   those exact lines as "still uncorrected, flagged for that file's owner". The media-side value is
   **0.140 %** (`η = (1 − cos(asin(NA/n_media)))/2`, n_media = 1.335); the air-side form was 1.8×
   high. Corrected in place with a dated block, and both citing sentences updated from "flagged for
   the owner" to "closed". *Neither argument on that page weakens* — the absorbance ratio argument
   is size-independent, and the SiPM comparison gains.
4. **One more line anchor shifted by this pass's own edits** (`sensor_module_interface.md` → the
   IMX178 array figure), re-anchored by quoted text.

**A second-order error, recorded because it is the interesting one.** The byonoy correction block as
first written said the "one to two orders of magnitude" SiPM advantage was "left as written because
no sourced SiPM collection figure exists in this repo to recompute it against". That was false, and
avoidably so: `sensor_module_interface.md` catalog row **#13** had already re-verdicted exactly that
claim on the same date — the comparison is no longer against NA 0.10 at all, because the geometry
admits **NA 0.60 at 5.334 %**, so the SiPM's residual margin is **≈2.6×** at the optimistic end of
its own claim and a **net loss** at the pessimistic end. Writing "no figure exists" without grepping
for one is the same failure as citing a heading without opening it, one level down. The block now
points at the re-verdict.

**The rule this adds.** A correction is not finished when the number is right. **Check whether the
argument the number was carrying still holds** — and before writing "nothing in the repo settles
this", grep for the thing that settles it.

### Follow-up 2026-09-23, convergence round 5 — the count went up, because the lenses finally reached the generated blocks

*Appended.* Round 4's survival count was **9**, up from round 3's 4. That is not a regression: the
numbers lens reached two files no earlier round had opened — `one_row_coupon.md` and
`row_coupon_revision_hypergraph.md` — and both carry claims quoted **from** the CAD rather than
argued in prose. Claims quoted from a model decay every time the model changes, and nothing had been
checking them. Running counts: **12, 6, 4, 9**.

**Retired negative verdicts stated as current, in the revision hypergraph.** Three sites said the
latch screen was failing. Re-run against the live `latch_retention_span_check`:

| Claim in the doc | Live value |
|---|---|
| self-lock margin "positive but **below target**" | `self_lock_margin_deg` **4.614** vs `self_lock_min_margin_deg` **1.0** — above |
| "the omitted port-side station creates an explicit span warning" | `omitted_station_count` **0**; 12 expected, 12 active |
| "the port-driven latch-station **asymmetry**" | same — there is no asymmetry |
| (implied risk) | `exceeds_allowed_span` **False** (77.125 mm vs 100.0), `cad_risk_flag` **False**, `backdrive_risk_flag` **False** |

All three corrected. The dependent open M-item "asymmetry mitigation" is retired with the asymmetry
itself — there is no omitted station to mitigate — with a note that
`latch_retention_span_check` will resurface it as `omitted_station_count > 0` if a future lid change
reintroduces a port omission. **This is the second instance of the round-3 pattern**: a doc listing
work that the model says is not required.

**Geometry quoted from the pre-`end_margin_x` layout.** `one_row_coupon.md` gave "X margin:
10.00 mm" against `row.end_margin_x` = **10.5** (and its own numbers agree: (148.60 − 127.60)/2 =
10.50). It put the first-slot feet at x = 9.88..13.88 / 133.88..137.88; live `deck_engagement_feet`
gives **10.30..14.10 / 134.50..138.30** at `foot_length_x` 3.8. The retired pair implies a 4.0 mm
foot and a frame centred on 73.88 — the geometry before the 10.5 margin.

**Two more retired Y-split counts**, in the execution queue rather than in prose:
`remaining_work.md` RC-W1 ("Print the 21-file split batch") and RC-W3 ("21-row worksheet"). The
canonical queue is **38** (`rigid_print_pieces` in `docs/assembly/artifact_authority.json`; cycle-log
RS164 witnesses "38 STEP/STL pairs"). 21 was 18 split segments + 3 monoliths from the frozen
2026-06-02 run.

**A third instance of the same self-inflicted error.** The byonoy correction block appended last
round cited `sensor_module_interface.md`, § *(1) The collection model was the wrong form* — **a
heading that does not exist**. The real one is § *(1) Collection fraction — the correct, media-side
form*, and `observer_optical_bench.md` was already citing it correctly two files away. That is the
third time in this pass that a heading anchor was written without opening the heading, **after** the
rule forbidding it was written into this log. A rule stated is not a rule followed; the check has to
be mechanical. One more bare line citation (`sensor_module_interface.md:618-621` for a figure that
lives ~30 lines later, under a different section) was re-anchored by text.

**What this round adds to the method, not just the tree.** Prose decays when an argument changes;
**a block quoted from a generator decays whenever the generator's output changes, silently, with no
edit to the file that carries it.** Those blocks need a different discipline from citations: either
regenerate them as part of the pass, or mark them with the date and the command that produced them
so a reader knows what they are looking at. `one_row_coupon.md`'s "Current Generated Envelope" is
introduced as what the viewer prints and is not; that is the class of defect, and it will recur on
the next geometry change unless the block is generated rather than transcribed.

### Follow-up 2026-09-23 — the generated-envelope blocks, regenerated and measured

*Appended, closing the item the entry above left open.* Both `text` blocks in
`one_row_coupon.md` were regenerated from the live builders rather than patched row by row,
because the drift was too broad to trust any row that happened to still match.

**"Current Generated Envelope"** — regenerated from `build_row_coupon_installed_parts(params)`.
**15 of its 27 rows were wrong**, and a 28th part was missing from the block entirely. The
assembly line read `219.60 x 405.25 x 140.60`; the live union is **220.60 x 405.25 x 141.60**.
Representative drift:

| row | block carried | live |
|---|---|---|
| lower harness cover | 10.40 × 326.38 × 0.70 | **10.90 × 314.57 × 1.15** |
| lower / upper gasket | 148.60 × 377.25 × 0.80 | **146.75 × 375.40** × 0.80 |
| lid cover | 162.80 × 377.25 × 26.00 | **163.80 × 357.25 × 25.30** |
| printed wedge locks | 148.60 × 377.25 × 3.00 | 148.60 × **347.25** × 3.00 |
| COTS gas service tubes | 219.60 × 262.25 × 5.00 | **220.60** × 262.25 × 5.00 |
| lid manifold shell | 148.60 × 377.25 × 8.60 | 148.60 × 377.25 × **9.60** |
| **gas sensor PCBs** | **absent** | 133.07 × 287.25 × 25.10 |

**The validation-envelope block was worse in a quieter way.** It opens "The following validation
envelopes are checked by tests…", which reads as exhaustive. It listed **20**. The live
`build_row_coupon_validation_parts(params)` returns **40**. Half the validation surface — including
`well_cell_plane_check`, `thermal_condensation_proxy_check`, `latch_retention_span_check` (the one
three other docs were misreporting this same session), `assembly_state_witness_check`,
`dry_bay_ingress_audit_check` and `fail_closed_prerun_inspection_check` — was invisible to anyone
reading this file as the envelope reference. Regenerated complete. Its one wrong value,
`side gas tube envelope check`, carried the retired **219.60** mm X against the live **220.60**,
the same 1.00 mm gas-tube growth that made the installed row stale.

**An omission that reads as exhaustive is a worse defect than a wrong number**, because a wrong
number invites the check that catches it and a short list invites nothing. Both blocks now carry the
date, the builder that produced them, and — on the installed block — an explicit warning that it is
**transcribed, not generated**, so it will decay again on the next geometry change unless it is
generated as part of the pass. That is the standing recommendation to this file's owner; no code
was changed here to do it automatically.

### Follow-up 2026-09-23, convergence round 5 — the numbers lens came back clean, and the rule finally got teeth

*Appended.* Survival counts across the pass: **12, 6, 4, 9, 1**. Round 5's **numbers lens returned
`clean: true`** — an exhaustive independent re-derivation of every numeric claim in the changed docs
against the live model, `cad/one_row_coupon.params.json`, `src/aevum_smis/manifest.py` and
`src/aevum_cad/row_coupon/`, with nothing failing to reproduce: the BOM sums, the optics ladder
(η, Abbe, DOF, Nyquist, Maréchal), the pupil/overfill arithmetic, the standoff and cone geometry,
the 128/384 reachable-well derivation, both corridor budgets, the throughput/storage chains on both
tube-lens conventions, the illumination ray budget and Fresnel losses, the CTE and settle figures,
and the latch stress/span screen. The honesty lens raised two findings and **both were refuted**.

**The one confirmed defect was mine, and it was the fourth of its kind.** The very first fix of this
pass — the per-axis rewrite of the fudge-factor parenthetical in `observer_optical_bench.md` —
closed with "see `decision_log.md`, OC-A1." **There is no OC-A1 in this log.** `grep -c 'OC-A1\b'`
returns 0; the log carries OC-A3, OC-A11, OC-A14, OC-A15, OC-A16 and OC-A18. Worse than dangling:
OC-A1 *is* a real item elsewhere in the same ID namespace — the `front_end_body_fits_dry_bay`
containment assert — so the reference resolved to the **wrong decision** rather than to nothing. The
content it meant is at **OC-A15 — implementation (2026-06-14), item 2**, "CAD — bay-Y resized to the
wet/dry-bounded deck extent, X left alone". Re-anchored by heading and quoted item text.

**Four self-inflicted anchor errors in one pass, every one of them written after the rule against
them was written into this log.** That is the finding. The earlier follow-ups kept restating the
rule in stronger words — anchor by quoted text, verify the heading by opening it — and the rule kept
not working, because *a rule a human or an agent has to remember at the moment of writing is not a
control.* What finally worked was mechanical: a sweep that extracts every cross-file anchor and
resolves it against the target.

**The sweep is the deliverable, not the fixes.** Run over the whole `docs/` + `data/` tree it checks
two classes:

1. **ID anchors** — every `` `file.md` ``-qualified `OC-A##`, `RS###`, `IN-C##`, `SM-#.#` reference,
   resolved against the named file. **0 broken.**
2. **Section anchors** — every `` `file.md` ``, § "Heading" reference, matched against that file's
   real `#`-headings (normalised) with a fallback to bolded paragraph leads. **2 broken, both now
   closed:** the OC-A1 site above, and `remaining_work.md`'s "§ *A second candidate…*", whose
   **ellipsis made it ungreppable** — an anchor that cannot be searched for is not an anchor. Now
   written out in full.

Re-run after the fixes: **0 broken in both classes.** The residual hit the sweep reports in this log
is this document quoting a bad heading in order to say it does not exist — a false positive, and the
correct behaviour.

**The standing recommendation, and the honest limit of this pass.** This sweep is thirty lines of
Python run by hand. It belongs in the test suite, where it would make every future citation a
failing test rather than a discovery for the next reviewer. **No code was added to do that, because
this was a documentation pass** — but that, and generating `one_row_coupon.md`'s envelope blocks
rather than transcribing them, are the two changes that would stop this entire class of defect from
recurring. Both are recorded here, neither is applied.
