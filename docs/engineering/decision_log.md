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
