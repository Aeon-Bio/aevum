# Materials Strategy For Row-Shared Tile Modules

## Purpose

This page defines the material stance for moving beyond the passive 4 x 4
fixture into a row-shared environmental module: four registered glass-bottom
plate tiles under one controlled atmospheric headspace.

Status note, 2026-05-25: the current one-row coupon path is intentionally
stricter than this older material stance. For the print-native coupon, no metal,
glue, adhesive, solvent weld, heat stake, or hidden bonded authority is allowed;
COTS plates and COTS septum mats remain the only nonprinted consumables in the
assembly tree. Any future return to metal inserts, metal stops, commercial
compression parts, or bonded authority must be recorded as an explicit design
exception with its own evidence and service model.

Status note, 2026-05-26: the first latch mechanical screens use provisional
material and process assumptions only: prototype PETG or engineering resin,
0.15 mm layer height, 12 MPa allowable wet-polymer stress, mu=0.35 minimum
friction, 2.0..25.0 N insertion-force range, 1.0..15.0 N release-force range,
and 8.0 N expected clamp force per latch. These values are CAD gates for a
print-test, not material validation. M4 must replace them with print orientation
and slicer evidence before parts are cut, and physical coupon data must replace
them before any retained-compression or wet-cycle claim is closed.

Status note, 2026-05-28: the production prototype's power section is recorded
as an explicit design exception under the rule above. The power enclosure
contains a genuine MeanWell HRP-150-24 PSU, MeanWell DDR-series isolated
DC-DC step-downs, ceramic fuses, a 10D471K MOV, Vishay P6KE24A TVS clamps,
and Phoenix-compatible UK2.5B terminal distribution. Glue, solvent welding,
and heat staking remain disallowed inside the power enclosure (terminal
screws and ferrules are mechanical); the metals and bonded authority used
there are confined to commercial parts whose certification, surge clamping,
and isolation behavior the prototype depends on. The boundary between this
exception and the print-native row coupon is the GX16 aviation umbilical:
[`docs/engineering/power_section.md`](../engineering/power_section.md)
documents the exception, its authority parts, its layered failure response,
and the counterfeit-authentication protocol that protects the exception from
quietly becoming a clone-introduced failure mode.

Status note, 2026-05-31: a second COTS-authority exception is recorded for
the custom sensor PCB carrying STC31 CO2 and SHT41 RH/T elements. The PCB
is fabricated externally (JLCPCB) with PCBA assembly and user-supplied
Sensirion chips. The boundary between this exception and the print-native
row coupon is the printed sensor pocket geometry: the row coupon's CAD
defines the mount features and gas channel aperture; the sensor PCB
populates the resulting envelope. The PCB itself contains soldered SMD
components, FR4 substrate, copper traces, ENIG plating, and metal headers,
all of which are forbidden by the print-native discipline of the row coupon
mechanical assembly. The exception is scoped to a discrete physical object
(the PCB) with a defined mechanical boundary; it does not migrate into the
printed parts. [`docs/engineering/sensor_pcb.md`](../engineering/sensor_pcb.md)
documents the design, fab workflow, sourcing path, authentication, and
service operations. The same counterfeit-authentication discipline applies
to the Sensirion chips supplied for assembly.

Status note, 2026-05-31: sensor electronics are scoped exceptions, but
their row-module retention is not. The printed row coupon should hold
sensor PCBs, per-plate SHT41 carriers, and MLX90614 IR sensors with
printed datum features, pockets, clips, wedges, sliding keepers, or
covers wherever possible. Metal screws, threaded inserts, adhesive, or
bonded sensor retention do not come along for free with the electronics
exception; they require their own exception and evidence if later proven
necessary.

Status note, 2026-06-04: the one-row coupon first-print package now records
`first_print_row_coupon_print_native_no_hidden_authority` as the active
material-authority decision. For this coupon, the older authority-insert stance
is superseded for mechanical retention, datum, latch, service-retention, and
validation bodies. COTS consumables, electronics, gaskets, cable assemblies,
and tubing remain explicit boundary parts; they do not authorize hidden metal,
glue, springs, bonded features, or threaded retention in the printed coupon.
Any future exception must be recorded as a new decision with tests, generated
artifact changes, and physical service evidence.

## Plate-As-Consumable Constraint

The CellVis P96-1.5H-N glass-bottom plate is a removable consumable in the
row module's architecture. Each plate hosts one experiment's cells; the
next experiment uses a fresh plate. Contaminants, instrumentation residue,
adhesive marks, or attached hardware carry over between experiments and
break the plate's role as a clean biology vessel.

**No instrumentation, label, adhesive, fastener, marker, or mechanical
fixture may attach to the plate.** The plate must seat freely into the
printed support frame, lift out freely for replacement between
experiments, remain undamaged through repeated install/remove cycles,
arrive sterile, and leave clean.

This rules out:

- Adhesive sensors on plate underside (thermistors, PT100s, optical
  spots, strain gauges);
- Plate-mounted labels, barcodes, or printed identifiers;
- Plate-mounted optical fiducials, retroreflectors, or markers;
- Plate-attached cabling or instrumentation harnesses;
- Mechanical clamps that grip the glass or the well field;
- Anything that would contaminate the next experiment's cells or
  interfere with the plate's role as a sterile biology container.

All plate-related sensing must come from the row-module side, not the
plate side. The row module's printed support frame, lid manifold, dry
bay, and gas plumbing are the appropriate homes for sensors,
instrumentation, registration features, and identification readers; the
plate itself remains untouched.

Examples of compliant approaches:

- **Sample-plane temperature**: non-contact IR thermopile (MLX90614) in
  the support frame's plate-margin area, aimed at plate underside; see
  decision log 2026-05-31 entry on sample-plane measurement.
- **Plate identity / batch tracking**: optical reader in the row module
  that reads molded or contact-printed marks already present on the
  plate from the manufacturer, not added marks.
- **Per-well sensing**: optical (transmission, fluorescence, IR) through
  the glass from the row module's dry bay or lid, not contact.

Examples of non-compliant approaches that have been considered and
rejected:

- Thin-film PT100 adhered to plate underside (proposed 2026-05-31 for
  sample-plane temperature; rejected; replaced with non-contact IR).

The principle applies regardless of subsystem. Any future design
recommendation that proposes attaching something to the plate must be
screened against this constraint before being accepted.

The row module can use 3D printing for most of its visible geometry, but not for
every authority-bearing interface. Printed plastic should create shape,
packaging, ducts, baffles, carriers, covers, and replaceable fixtures. Datum
truth, sealing truth, thermal truth, optical truth, biological truth, and
CO2/RH sensing authority should come from inserts, elastomers, glass, metal, and
validated commercial parts.

This page is the material-specific companion to
[hardware systems lessons](hardware_systems_lessons.md), which defines the
broader failure modes and authority-separation rule for the row-module design.

## Fixed Assumptions

- The culture vessel is a glass-bottom SBS plate. The plate glass is the primary
  optical boundary for the dry inverted observation module.
- The support structure must contact the plate frame, skirt, rim, or other
  validated support lands, not the central glass observation region.
- Four adjacent plate tiles share one controlled atmospheric headspace for CO2
  and humidity. Tile-local hardware may still support heat transfer,
  registration, identification, and sensing.
- The tile footprint cannot grow side features that prevent a rectilinear tiled
  array or the motion envelope of the dry observation module.
- Warm humidified CO2 is a hostile environment for unvalidated printed plastic:
  porosity, water uptake, creep, leachables, odor, and dimensional drift must be
  assumed until measured.

## First Row-Module PoC Stack

```text
row conditioning / sensing / mixing module
  -> low-velocity row distribution plenum
  -> four-plate environmental lid / rim / septum assembly
  -> platinum-cured silicone gasket or sealing mat
  -> four glass-bottom SBS plates
  -> validated plate-frame support lands
  -> metal or graphite thermal spreaders where needed
  -> printed tile chassis and service-routing shells
  -> metal datum pins, bushings, threaded inserts, and compression stops
  -> open apertures to the shared dry inverted observation bay
  -> blackened baffles and sensor-suite clearance interfaces
```

Avoid adding a second optical window below the plate unless spill protection,
pressure isolation, or contamination control requires it. If a shield is needed,
use borosilicate or quartz and make it removable and evidence-scoped, because
it becomes part of the optical path.

## Printed Parts

Good candidates for printing:

- tile chassis, row-lid shell, and non-critical structural volume;
- low-velocity plenum shapes, diffuser carriers, baffles, and replaceable duct
  prototypes;
- septum, mat, gasket, and plate-carrier geometry;
- gasket compression frames when compression stops are metal or otherwise
  authority-bearing inserts;
- sensor, heater, fan, valve, tube, and wire mounts;
- dry-bay light baffles, aperture masks, and sensor-suite clearance mockups;
- service-bus mockups and strain-relief routing;
- removable covers and inspection fixtures.

Material bias:

- `ASA`: preferred FDM baseline for larger non-wetted structural parts and
  baffles because it handles heat better than PLA.
- `PC` or `PC-CF`: useful for stiffer loaded carriers when printing is reliable
  and warping is controlled.
- `PA12` by SLS/MJF: useful for compact ducts and complex module shells, but
  gas and humidity paths need sealing, liners, or validation.
- `PETG`: acceptable for low-authority carriers and covers; watch creep.
- `PLA`: fit mules only, not warm incubated modules.
- SLA resins: use cautiously for small detail parts or fit checks; keep them out
  of incubated headspace unless a specific resin, post-cure, coating, and
  biological compatibility path are validated.

## Inserts And Commercial Parts

Use inserts or commercial parts for:

- datum pins, dowels, bushings, kinematic seats, shoulder screws, threaded
  inserts, and compression limiters;
- platinum-cured silicone, EPDM, or FKM seals, selected by gas permeability,
  compression behavior, and cleaning compatibility;
- aluminum, copper, stainless, or graphite thermal spreaders;
- polyimide heaters, RTDs, thermistors, thermal fuses, and independent safety
  cutoffs;
- CO2/RH sensors in a representative row return, mixed sampling path, or row
  service module rather than inside a single tile;
- quiet fans, pumps, restrictors, calibrated orifices, diffuser media, or porous
  sections for low-turbulence row distribution;
- PTFE, FEP, or PFA gas tubing where stiffness allows; use silicone tubing only
  where flexibility is more important than permeability;
- COTS gas fittings, filters, membranes, valves, pressure sensors, and leak
  checks;
- optical fiducials, retroreflective markers, metal fiducial inserts, or
  post-machined/marked reference surfaces;
- black anodized aluminum or validated matte-black surfaces near high-value
  optical paths.

## Authority Boundaries

Do not rely on printed plastic alone for:

- gas-tightness or humidity retention over time;
- sterile or cell-facing surfaces;
- long-term gasket compression;
- CO2/RH measurement accuracy or representative row sampling;
- quiet, uniform air distribution across four plates;
- high-speed observer registration;
- thermal uniformity at the sample plane;
- repeated calibration datums;
- fine optical alignment;
- threaded or latched retention under repeated service cycles.

Printed surfaces may still participate in those systems as carriers, covers,
duct volume, or sacrificial prototypes. The authority should come from
measured inserts and replaceable components.

## Validation Implications

Material choices need their own evidence, not just CAD intent:

- measured tile bounds and plate support flatness;
- gasket compression height and leak behavior;
- row-to-row and plate-position-to-plate-position flow balance;
- visible disturbance checks at liquid surfaces under conditioned flow;
- thermal response at headspace, rim, plate support, and near the glass-bottom
  sample plane;
- CO2 and humidity recovery after lid opening or pipette access at all four
  plate positions;
- condensation patterns after warm humid operation;
- observer fiducial repeatability after heat/humidity cycling;
- printed-part creep or warp after warm humid operation;
- compatibility notes for any material exposed to incubated headspace.
