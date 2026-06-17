# One-Row Coupon

## Purpose

The one-row coupon is the next hardware interface proof between the first P300
interaction mule and the future row-shared environmental module.

It is not a full incubator. It is a CadQuery-generated mechanical coupon for
testing whether four OT-2 column plate positions, a lid-owned controlled
headspace, a replaceable seal/compression interface, dry observation apertures,
pipette access, vertical service exits, compression stops, and dry-side observer
fiducials can coexist without breaking the platform architecture.

The headspace is not a removable spacer. The coupon represents headspace as one
continuous engineered empty volume under the lid/manifold across all four plate
positions. The gasket at that layer is an outer row skirt, not four sealed
plate-by-plate islands.

The source parameters are:

```text
cad/one_row_coupon.params.json
```

The generator is:

```text
src/aevum_cad/row_coupon.py
```

The print-native path to the real device is:

```text
docs/engineering/print_native_row_module.md
```

The active do-review-context task hypergraph for CAD revisions is:

```text
docs/engineering/row_coupon_revision_hypergraph.md
```

The latest CAD-level cycle outcomes and next physical review tasks are:

```text
docs/engineering/row_coupon_cycle_log.md
```

That cycle log also tracks a missing-gap audit for domains not yet closed by the
CAD pass: COTS consumable metrology, pipette puncture mechanics, thermal and
condensation authority, pressure relief, spill isolation, BSL1 material
compatibility, optical quality, row tiling, service routing, and fail-closed
assembly-state inspection.

Generate artifacts with:

```bash
uv run python scripts/generate_row_coupon.py
```

Open the viewer smoke file in CQ-Editor:

```text
cad/view_one_row_coupon.py
```

The viewer shows installed physical parts as separate objects. Keepout envelopes
and controlled-volume claims are hidden by default because they are validation
evidence, not fabricated parts. Enclosed gas sensor PCB envelopes are also
hidden from the default surface view so the installed model shows the printed
cassette/door geometry rather than bare green boards protruding from the lid.
Expose those PCB envelopes only for electronics service review with:

```bash
uv run python cad/view_one_row_coupon.py --show-internal-electronics
```

RH10/RH11 review geometry is available with:

```bash
uv run python cad/view_one_row_coupon.py --show-validation-tools
```

The printable latch-mechanism demonstrator is available with:

```bash
uv run python cad/view_one_row_coupon.py --show-latch-demo
```

Sensor installation and port service/negative review scenes are available as
opt-in view modes:

```bash
uv run python cad/view_one_row_coupon.py --view-mode sensor_install
uv run python cad/view_one_row_coupon.py --view-mode sample_relief_cap_missing
uv run python cad/view_one_row_coupon.py --view-mode sample_relief_cap_unseated
uv run python cad/view_one_row_coupon.py --view-mode latches_unseated
uv run python cad/view_one_row_coupon.py --view-mode septum_mats_missing
uv run python cad/view_one_row_coupon.py --view-mode microplates_missing
uv run python cad/view_one_row_coupon.py --view-mode perimeter_gaskets_missing
uv run python cad/view_one_row_coupon.py --view-mode gas_pcbs_missing
uv run python cad/view_one_row_coupon.py --view-mode service_leads_missing
uv run python cad/view_one_row_coupon.py --view-mode electrical_connectors_unmated
```

For CQ-Editor, set the equivalent environment flag before launching:

```bash
AEVUM_ROW_COUPON_VIEW_MODE=sensor_install bash scripts/open_cq_editor.sh cad/view_one_row_coupon.py
AEVUM_ROW_COUPON_SHOW_INTERNAL_ELECTRONICS=1 bash scripts/open_cq_editor.sh cad/view_one_row_coupon.py
AEVUM_ROW_COUPON_SHOW_LATCH_DEMO=1 bash scripts/open_cq_editor.sh cad/view_one_row_coupon.py
```

It is also exported as separate validation STL/STEP parts by:

```bash
uv run python scripts/generate_row_coupon.py
```

Running the viewer file from plain Python prints the installed part bounds.

## Current Generated Envelope

The current installed assembly envelope is:

```text
assembly: 219.60 x 405.25 x 140.60 mm
deck pods installed: 128.00 x 357.50 x 84.10 mm
plate support frame installed: 148.60 x 377.25 x 11.20 mm
IR thermopiles installed: 8.00 x 279.50 x 4.85 mm
IR thermopile face gaskets installed: 8.00 x 279.50 x 0.45 mm
lower sensor harness installed: 9.40 x 325.38 x 0.45 mm
lower harness cover installed: 10.40 x 326.38 x 0.70 mm
lower sensor service connector installed: 10.80 x 8.60 x 5.10 mm
printed lower sensor connector shroud installed: 12.40 x 9.40 x 4.80 mm
lower sensor service cable pigtail installed: 3.20 x 30.00 x 1.20 mm
lower gasket installed: 148.60 x 377.25 x 0.80 mm
wet chamber frame installed: 148.60 x 377.25 x 32.10 mm
COTS microplates installed: 127.60 x 357.25 x 14.30 mm
COTS septum mats installed: 127.60 x 357.25 x 4.50 mm
upper gasket installed: 148.60 x 377.25 x 0.80 mm
lid manifold shell installed: 148.60 x 377.25 x 8.60 mm
headspace SHT41 microcarriers installed: 12.00 x 283.50 x 4.00 mm
lid sensor harness installed: 146.00 x 325.38 x 8.05 mm
lid harness cover installed: 147.00 x 326.38 x 8.30 mm
lid sensor service connectors installed: 145.60 x 8.60 x 5.10 mm
printed lid sensor connector shrouds installed: 147.20 x 9.40 x 4.80 mm
lid sensor service cable pigtails installed: 138.00 x 30.00 x 1.20 mm
lid cover installed: 162.80 x 377.25 x 26.00 mm
COTS gas service tubes installed: 219.60 x 262.25 x 5.00 mm
gas PCB interface gaskets installed: 128.20 x 269.25 x 2.80 mm
printed gas PCB keeper doors installed: 141.00 x 289.65 x 0.80 mm
printed sample/relief cap installed: 16.80 x 12.00 x 4.60 mm
printed wedge locks installed: 148.60 x 377.25 x 3.00 mm
```

The following validation envelopes are checked by tests, retained as CadQuery
builders, hidden from the default installed viewer scene, and exported as
separate validation tools:

```text
deck slot footprint check: 130.00 x 359.50 x 0.80 mm
deck frame keepout check: 148.60 x 377.25 x 2.50 mm
deck pod seating repeatability check: 70.00 x 58.00 x 0.50 mm
dry bay envelope check: 120.20 x 357.50 x 80.00 mm
dry bay boundary check: 132.20 x 357.50 x 3.00 mm
wet/dry failure path check: 94.40 x 326.30 x 0.45 mm
observer front-end swept body check: 120.00 x 347.50 x 40.00 mm
observer carriage envelope check: 100.00 x 58.00 x 62.00 mm
observer service raceway envelope check: 8.00 x 357.50 x 24.00 mm
observer infinity port datum check: 120.00 x 347.50 x 0.50 mm
observer kinematic split check: 58.00 x 78.00 x 0.45 mm
headspace barrier check: 148.60 x 377.25 x 5.80 mm
headspace volume check: 138.60 x 367.25 x 5.80 mm
pipette puncture swept path check: 101.50 x 337.00 x 41.30 mm
pipette toolhead swept body check: 250.00 x 445.50 x 45.00 mm
side gas tube envelope check: 219.60 x 263.25 x 6.00 mm
operating service dress check: 220.60 x 348.75 x 43.30 mm
adjacent deck slot keepout check: 395.00 x 359.50 x 110.00 mm
consumable metrology gauge: 143.60 x 101.75 x 3.00 mm
printability support cleanup check: 64.00 x 80.00 x 1.20 mm
```

The coupon is now four SBS-like plate positions along one OT-2 column:

```text
plate footprint: 127.60 x 85.75 mm
OT-2 slot opening: 130.00 x 88.00 mm
OT-2 slot pitch along column: 90.50 mm
inter-tile gap along Y: 4.75 mm
X margin: 10.00 mm
Y end margin: 10.00 mm
```

The installed plate support load path is physical and now follows the
production assembly tree. Four CellVis P96-1.5H-N-sized microplate consumables
sit between the printed plate-support frame and the lid/manifold stack. The
plate-support frame includes integral 2.00 mm tall, 5.00 mm wide perimeter
lands around each plate plus 1.20 mm tall lateral locator rails around each
plate pocket. Those lands raise the support plane from the 8.00 mm frame top to the
10.00 mm plate-bottom datum. The printed deck pods own OT-2 slot fit and raise
the frame above the deck while staying out of the dry observer sweep. The lid,
upper gasket, septum mats, wet-chamber frame, lower gasket, and printed wedge
locks clamp from above, but vertical plate load is carried through the plate rim
into the printed support lands, then through the deck pods into the OT-2 deck.

The plates are loaded top-down with the chamber module removed. The installed
assembly then adds a full-footprint removable wet-chamber frame. The frame is
not a fixed base cage and not a plate-local collar: it reaches the support/lid
envelope so the incubated chamber boundary, gasket land, side gas lanes, and
sensor/service routing all live in the same physical row module. Internal
divider rails form supply/return side lanes with per-plate upper diffuser
windows into the shared chamber. The current microplate CAD is no longer a
solid slab: it includes perimeter sidewalls, a bottom observation window, and a
published-profile top well deck with 96 openings per plate. The CellVis
first-build profile now carries 6.80 mm upper well openings, 6.21 mm lower well
diameter, 6.18 mm well-bottom equivalent diameter, and a 0.47 mm top recess
depth so the consumable plate itself is part of the boundary, load path, and
liquid-handler access geometry we must reason about. A validation-only
`well_cell_plane_check` marks the published 6.18 mm equivalent-diameter
cell-plane target disk in every well at the 12.40 mm plate-top-to-cell-plane
depth; this makes the biology/observer target explicit without turning cells or
liquid into installed production geometry. A separate validation-only
`ir_thermopile_fov_spot_check` marks the projected IR thermopile field-of-view
spot on the plate-underside margin for each plate. This keeps the IR role honest:
the installed thermopiles measure a plate-margin proxy that must be correlated
to the cell plane, not a direct in-well biology temperature.
`thermal_condensation_proxy_check` combines the per-plate center cell-plane
reference, plate-margin IR proxy spot, SHT41 headspace aperture/drip-ring point,
and the wet-chamber condensation low-point pockets into one Gate 6 review map.
It makes the measurement plan explicit without treating thermal authority,
condensation control, or evaporation behavior as proven by CAD.

The production operating gas path is side-connected, not top-cap-connected.
Supply and return now enter through printed side fittings integrated into the
`lid_cover` duct part. Each side service has a printed manifold block, side duct
opening, short tube stem, raised barb-retention bead, printed strain-relief yoke,
shallow outboard witness gutters, an inboard raised leak dam, and installed COTS
gas tube pigtails. The current first-build tubing assumption is a 3.0 mm ID /
5.0 mm OD flexible tube on a 3.1 mm printed stem with a 3.6 mm barb peak, pending
real tube/fitting pull-off and leak data. The installed tube CAD is a hollow
tube-wall body with a modeled flow bore, while the rectangular tube bend
envelopes remain validation-only clearance volumes around those physical tube
bodies. These are aligned with the
gas-PCB duct sampling cells so the gas sensors read the controlled supply/return
streams through sealed low-dead-volume interfaces. The witness gutters are
intentionally outboard of the dry-bay footprint; their modeled failure direction
is toward the visible row edge, not into the observer bay.

The side gas tube and fitting envelopes are also checked against adjacent OT-2
slot keepouts. In the current CAD, the side services use reserved adjacent-slot
overhead: they horizontally overlap the neighboring slot envelope only above a
110.00 mm keepout from the deck plane, with 4.10 mm minimum modeled vertical
clearance. This is a CAD-level service-routing assumption, not proof that every
neighboring module can remain installed beside the coupon.
The validation-only `operating_service_dress_check` combines the side gas
fitting/tube/strain-relief envelopes with the row-end electrical cable bend
envelopes as one normal-operation service dress body. It is not an installed
part; it is the CAD target for physical tube/cable dressing and OT-2 neighbor
clearance inspection.
The validation-only `row_tiling_service_clearance_check` composes the installed
row footprint, adjacent OT-2 slot keepout volumes, and operating service-dress
rectangles into one first-print review body. It preserves the 4.10 mm modeled
minimum vertical clearance over the 2.00 mm requirement, but still requires a
printed row and dressed services to be inspected on the OT-2 before Gate 3 can
pass.

Only one vertical top port remains in the production lid model: a
`sample_relief` service port. Its separate installed cap is named
`printed_sample_relief_cap`; this is a sealed production service feature, not a
generic gas inlet/return cap. Former top supply, return, and representative
sensor ports are no longer modeled as production operating interfaces.

The cap/lid seal is now modeled as a matched production interface. The
removable cap carries an integrated annular compliant lip below its flange, and
the printed lid-cover boss has a shallow annular receiving seat. The current
first-print assumption is a 0.35 mm lip with a 0.23 mm seat depth and 0.12 mm
nominal compression, so the CAD represents a normally closed service closure
rather than only a friction plug over a hole.

The sample/relief cap now has its own printed failure hierarchy on the
`lid_cover`. A shallow outboard witness shelf and gutter run from the cap/boss
edge to the visible right row edge, while a small inboard dam sits on the
chamber side of the boss below the cap flange. This keeps the top pipette field
clear while making cap leakage or condensate visible at the outer edge before
it can silently route inward. This is CAD-level geometry, not leak-rate proof.

The 80 mm dry bay is a Raman/biophotonics exploration budget, not a proven
final height. It reserves room for a moving front-end optical head, focus axis,
folded optical pickup, baffles, and dry service routing while keeping larger
laser, spectrometer, detector, heat, and control electronics offloaded outside
the swept observer volume.

The dry bay is not protected by clearance alone. Each optical aperture now has
a printed raised threshold on the plate-support frame, flush to the aperture
edge and low enough to sit below the plate datum. Shallow wet/dry witness
gutters sit outside those thresholds, so a leak path adjacent to an aperture is
captured in printed geometry before it silently routes into the observer bay.

The deck interface no longer uses a continuous lower baseplate. Each plate
position has its own lower shoe, inset 1.00 mm per side inside the machined OT-2
slot opening. The standoff feet are now pushed to the slot-edge perimeter:
first-slot feet occupy x=9.88..13.88 mm and x=133.88..137.88 mm while the
observer sweep occupies x=13.88..133.88 mm. That preserves the full modeled
120.00 mm dry-bay X sweep for the moving observer instead of letting support
posts consume the bay interior. The generated deck-frame keepout STEP marks
aluminum rib keepout at the deck plane; no printed deck-contact geometry should
occupy that volume. The deck pods now also carry printed pod/frame keys that
enter matching underside pockets in the plate-support frame. Those keys make
the split lower assembly a located interface rather than two unrelated parts,
while keeping the replaceable pod wear surface outside the dry observer sweep.
The required validation-only
`outputs/cad/aevum_one_row_coupon_validation_deck_pod_seating_repeatability_check.step`
and `.stl` bind those feet and keys to Gate 3 evidence: five OT-2 deck
seat/release cycles, no rocking or yaw, no shoe/key wear that affects seating,
no frame contact, and no dry-bay debris bridge.

This does not by itself prove a large camera/spectroscopy module can image every
well. The well-center sweep across the row is 99.00 mm in X and 334.50 mm in Y.
The current CAD adds a 120.00 x 347.50 x 40.00 mm observer front-end swept body
that reaches all well centers without intersecting the slot-edge deck feet. The
review finding is important: a compact 21.00 x 13.00 mm front-end can fit this
claim, but the larger 100.00 x 58.00 mm carriage cannot be treated as an
objective-centered body across the full row. The production observer therefore
needs a kinematic split between compact optical front end, focus axis, carriage
body, service loop, and raceway.

The row headspace is a biology-facing environmental volume, not just mechanical
clearance above the wells. In this context, "contained wet chamber" means the
volume is bounded by the plate/septum/skirt/lid stack, sees humidified
cell-culture atmosphere, and must be controlled for CO2, humidity, pressure
relief, sampling, evaporation, and condensation. The internal headspace volume
check records this as one connected row volume spanning the plate field,
inter-plate gaps, and side service lanes. The lid manifold routing is
column-oriented: supply and return plenums run down the long sides of the four
plates, with side-connected supply/return fittings and a single sealed
sample/relief service boss on top. The skirt-side divider windows and lid
diffuser/return slots make each plate position part of the same controlled
volume without creating well-by-well chimneys.

The liquid-handler access layer is represented by four installed Cole-Parmer
EW-12920-06 round pre-slit silicone 96-well mats, one removable insert per
plate. The CAD shows the physical sheet, round plug pattern, and through-depth
slit reliefs in the modeled plug/sheet stack. The well grid only locates those
plug features; it is not a separate abstract target layer. Plug diameter,
protrusion, sheet thickness, slit-relief dimensions, and seated height remain
measurement-gated first-build assumptions until the physical mats are measured.

The gasket interfaces now include capture grooves and service tabs. The lower
gasket is captured between the plate-support frame and wet-chamber frame; the
upper gasket is captured between the wet-chamber frame and lid shell. The shell
groove preserves an outer printed datum land, because a groove that removes the
entire shell bottom perimeter would falsely delete the seating authority we
need to validate.

The service-tab roots now have their own leak/witness treatment. Each lower and
upper front/rear tab sits in the narrow row-end service margin, outside the
dry-bay envelope and outside the septum access windows. The plate-support frame
and lid shell include shallow tab-root witness gutters plus low inboard dams so
liquid at a tab root is caught in a visible service margin before it can track
toward the plate row or dry observer bay. These are small print features sized
to the existing margin; they are not leak-rate evidence.

The lid/manifold is now split into a printed manifold shell and printed cover.
The shell leaves the septum well fields open for mechanical access.
Each plate position has a rectangular access window over the 96-well
plug/slit field, so the OT-2 approach path is checked against the exposed
pre-slit silicone mat. These openings are not pipette chimneys and are not the
gas distribution architecture. The manifold shell remains a shared retainer and
underside headspace structure; the cover carries the raised side duct frame,
service bosses, and row-axis hard-stop pads. The shell includes shallow
underside mat-seat pockets and local pick-relief notches so the coupon
communicates that the mats are inserted, compressed, inspected, and swapped as
consumables. The production design must make the septum/frame interface the
chamber boundary without adding well-by-well vertical dead volumes.

The lid cover now has a downward tongue seated in a matching shell groove, and
the cover carries side-oriented wedge receiver rails around the separate printed
wedge locks. The wet-chamber frame carries printed tension posts and caps that
pass through the lid clearance holes. Each red wedge slides in from the side,
uses an open U-slot to pass around the post, then seats a high bearing flat
under the post cap. Low-end receiver lips capture the wedge tail against lift,
travel-stop blocks limit insertion, and release tabs, detent bumps, plus raised
witness stripes make the locked state serviceable from above. This is CAD-level
mechanical closure for a first latch print, but compression force, sliding
friction, duct leakage, and humid cycle release remain physical review tasks.
The `latches_unseated` review mode removes the installed wedge locks, shows the
same wedge bodies pulled outward along their real insertion axes, and adds
yellow bearing-flat witnesses at the seated latch stations. This is an
assembly-state inspection scene, not a production alternative and not a
validation export.

The lid hard-stop pads are row-axis aware. For the current four-plate OT-2
column, stop centers sit on the left and right perimeter rails at x=5.00 mm and
x=142.60 mm, with Y stations at the row ends and inter-plate seams:
5.00, 98.125, 188.625, 279.125, and 372.25 mm. The right-side station at
y=188.625 mm is currently omitted because its receiver envelope would overlap a
lid service-port boss. This replaces the earlier repeated near-front stop
positions and makes the lid compression structure visible where the gasket and
removable wet-chamber frame actually need support.

The CAD now exposes first-pass mechanical screens for the latch. These screens
use production latch geometry, not the abstract latch demonstrator. Current
values are:

- assumptions register: provisional PETG or engineering resin, provisional
  FDM/resin process, 0.15 mm layer height, 2.0..25.0 N insertion-force range,
  and 1.0..15.0 N release-force range for the first bench protocol;
- compression budget: 2.20 mm ramp rise, 6.40 mm ramp run, 0.45 mm tolerance
  allowance, 0.55 mm bounded target squeeze, 0.80 mm hard-stop/max squeeze
  limit;
- ramp self-lock screen: 18.97 deg ramp angle versus 19.29 deg friction angle
  at mu=0.35. The geometry has a positive 0.32 deg self-lock margin, but it is
  below the 1.0 deg minimum margin, so backdrive remains flagged for physical
  testing;
- post stress screen: 8.0 N assumed clamp force per latch, 2.4 mm post
  diameter, 4.524 mm2 shaft area, 1.768 MPa nominal shaft stress, and 6.786x
  stress safety factor against the provisional 12 MPa wet-polymer allowable;
- station asymmetry screen: 10 expected stations, 9 active stations, one
  port-omitted right-side station, and a 181.0 mm maximum active-station span
  on that side against a 100.0 mm warning limit.

These are CAD screening gates only. They make the mechanical assumptions
auditable before printing, but they do not prove insertion force, retained
compression, creep, wear, wet release, or leak behavior.
The latch retention/span check is exported as
`outputs/cad/aevum_one_row_coupon_validation_latch_retention_span_check.step`
and `.stl`. It is a required validation-only Gate 2 blocker tying the thin
self-lock margin and omitted-station span warning to dry-cycle detent hold,
omitted-station bow, post/cap bearing, and gasket-squeeze-after-cycle evidence
before any wet test can treat the latch as production-retentive.

The real assemblage avoids metal inserts, metal fasteners, glue, adhesives,
solvent welding, thermal staking, permanent welds, and hidden bonded authority
features. Printed wedge locks, printed hard-stop witnesses, printed gasket
capture, and printed service tabs replace the vague "fasten later" assumption.
COTS plates and COTS septum mats remain consumables; the structural, latch,
datum, and seal-carrier parts are printable, reversible, and serviceable in the
same order as the actual device.
The first-print package now records the active material-authority decision
`2026-06-04 first_print_row_coupon_print_native_no_hidden_authority`, which
supersedes the older authority-insert stance for this coupon's mechanical
assembly. COTS consumables, electronics, gaskets, cable assemblies, and tubing
remain scoped boundary parts, but they do not permit hidden metal, glue, spring,
bonded, or threaded authority inside the printed coupon.

## Generated Parts

```text
outputs/cad/aevum_one_row_coupon_deck_pods.stl
outputs/cad/aevum_one_row_coupon_deck_pods.step
outputs/cad/aevum_one_row_coupon_plate_support_frame.stl
outputs/cad/aevum_one_row_coupon_plate_support_frame.step
outputs/cad/aevum_one_row_coupon_ir_thermopiles.stl
outputs/cad/aevum_one_row_coupon_ir_thermopiles.step
outputs/cad/aevum_one_row_coupon_ir_thermopile_face_gaskets.stl
outputs/cad/aevum_one_row_coupon_ir_thermopile_face_gaskets.step
outputs/cad/aevum_one_row_coupon_lower_sensor_harness.stl
outputs/cad/aevum_one_row_coupon_lower_sensor_harness.step
outputs/cad/aevum_one_row_coupon_lower_harness_cover.stl
outputs/cad/aevum_one_row_coupon_lower_harness_cover.step
outputs/cad/aevum_one_row_coupon_lower_sensor_service_connector.stl
outputs/cad/aevum_one_row_coupon_lower_sensor_service_connector.step
outputs/cad/aevum_one_row_coupon_printed_lower_sensor_connector_shroud.stl
outputs/cad/aevum_one_row_coupon_printed_lower_sensor_connector_shroud.step
outputs/cad/aevum_one_row_coupon_lower_sensor_service_cable_pigtail.stl
outputs/cad/aevum_one_row_coupon_lower_sensor_service_cable_pigtail.step
outputs/cad/aevum_one_row_coupon_lower_gasket.stl
outputs/cad/aevum_one_row_coupon_lower_gasket.step
outputs/cad/aevum_one_row_coupon_wet_chamber_frame.stl
outputs/cad/aevum_one_row_coupon_wet_chamber_frame.step
outputs/cad/aevum_one_row_coupon_cots_microplates.stl
outputs/cad/aevum_one_row_coupon_cots_microplates.step
outputs/cad/aevum_one_row_coupon_cots_septum_mats.stl
outputs/cad/aevum_one_row_coupon_cots_septum_mats.step
outputs/cad/aevum_one_row_coupon_upper_gasket.stl
outputs/cad/aevum_one_row_coupon_upper_gasket.step
outputs/cad/aevum_one_row_coupon_lid_manifold_shell.stl
outputs/cad/aevum_one_row_coupon_lid_manifold_shell.step
outputs/cad/aevum_one_row_coupon_headspace_sht41_microcarriers.stl
outputs/cad/aevum_one_row_coupon_headspace_sht41_microcarriers.step
outputs/cad/aevum_one_row_coupon_lid_sensor_harness.stl
outputs/cad/aevum_one_row_coupon_lid_sensor_harness.step
outputs/cad/aevum_one_row_coupon_lid_harness_cover.stl
outputs/cad/aevum_one_row_coupon_lid_harness_cover.step
outputs/cad/aevum_one_row_coupon_lid_sensor_service_connectors.stl
outputs/cad/aevum_one_row_coupon_lid_sensor_service_connectors.step
outputs/cad/aevum_one_row_coupon_printed_lid_sensor_connector_shrouds.stl
outputs/cad/aevum_one_row_coupon_printed_lid_sensor_connector_shrouds.step
outputs/cad/aevum_one_row_coupon_lid_sensor_service_cable_pigtails.stl
outputs/cad/aevum_one_row_coupon_lid_sensor_service_cable_pigtails.step
outputs/cad/aevum_one_row_coupon_lid_cover.stl
outputs/cad/aevum_one_row_coupon_lid_cover.step
outputs/cad/aevum_one_row_coupon_cots_gas_service_tubes.stl
outputs/cad/aevum_one_row_coupon_cots_gas_service_tubes.step
outputs/cad/aevum_one_row_coupon_gas_pcb_interface_gaskets.stl
outputs/cad/aevum_one_row_coupon_gas_pcb_interface_gaskets.step
outputs/cad/aevum_one_row_coupon_printed_gas_pcb_keeper_doors.stl
outputs/cad/aevum_one_row_coupon_printed_gas_pcb_keeper_doors.step
outputs/cad/aevum_one_row_coupon_gas_sensor_pcbs.stl
outputs/cad/aevum_one_row_coupon_gas_sensor_pcbs.step
outputs/cad/aevum_one_row_coupon_printed_sample_relief_cap.stl
outputs/cad/aevum_one_row_coupon_printed_sample_relief_cap.step
outputs/cad/aevum_one_row_coupon_printed_wedge_locks.stl
outputs/cad/aevum_one_row_coupon_printed_wedge_locks.step
outputs/cad/aevum_one_row_coupon_assembly.step
```

The assembly STEP is exported as a multipart assembly so CAD inspection keeps
part identity. It is not the only source of geometry; the individual part files
above remain the manufacturing, purchased-consumable, and service units.
The deck and chamber validation checks are exported as
`outputs/cad/aevum_one_row_coupon_validation_deck_slot_footprint_check.step`,
`outputs/cad/aevum_one_row_coupon_validation_deck_frame_keepout_check.step`,
`outputs/cad/aevum_one_row_coupon_validation_deck_pod_seating_repeatability_check.step`,
`outputs/cad/aevum_one_row_coupon_validation_dry_bay_envelope_check.step`,
`outputs/cad/aevum_one_row_coupon_validation_dry_bay_boundary_check.step`,
`outputs/cad/aevum_one_row_coupon_validation_headspace_barrier_check.step`,
`outputs/cad/aevum_one_row_coupon_validation_headspace_volume_check.step`, and
`outputs/cad/aevum_one_row_coupon_validation_well_cell_plane_check.step`, and
`outputs/cad/aevum_one_row_coupon_validation_ir_thermopile_fov_spot_check.step`,
and
`outputs/cad/aevum_one_row_coupon_validation_thermal_condensation_proxy_check.step`
with matching `.stl` files. These make deck fit, deck-pod seating
repeatability, dry observer reservation, shared wet-headspace claims, the
published CellVis biology target plane, IR plate-margin proxy spots, and the
combined thermal/condensation proxy map
reviewable outside the test suite.
The headspace barrier and volume checks are required first-print Gate 4
validation bodies. They make the sealed perimeter and continuous shared row
headspace explicit in the package, but leak, condensate, and humid-cycle
behavior still require physical wet/dry evidence before Gate 4 can pass.
The dry-bay envelope and boundary checks are also required first-print Gate 4
validation bodies. They make the reserved observer volume and side boundary rail
clearance explicit, but dry-bay ingress protection still requires physical dye,
condensate, debris, and service-dress evidence.
The pipette puncture swept-path check is exported as
`outputs/cad/aevum_one_row_coupon_validation_pipette_puncture_swept_path_check.step`
and `.stl`. It is a required first-print Gate 5 validation body so every septum
target path can be inspected separately from the larger toolhead envelope
before all-well puncture access is accepted.
The sensor installation path check is also exported as
`outputs/cad/aevum_one_row_coupon_validation_sensor_installation_path_check.step`
and `.stl` for offline review of service directions.
The pipette toolhead swept body check is exported as
`outputs/cad/aevum_one_row_coupon_validation_pipette_toolhead_swept_body_check.step`
and `.stl` so the modeled lower OT-2 toolhead operating envelope can be
reviewed with side gas/electrical service envelopes connected. This is a
conservative CAD clearance envelope that requires physical OT-2 measurement; it
does not replace live-motion authorization.
The dry observer clearance checks are exported as
`outputs/cad/aevum_one_row_coupon_validation_observer_front_end_swept_body_check.step`,
`outputs/cad/aevum_one_row_coupon_validation_observer_carriage_envelope_check.step`,
and
`outputs/cad/aevum_one_row_coupon_validation_observer_service_raceway_envelope_check.step`
with matching `.stl` files. These show the compact optical front-end swept
volume, larger carriage reserved volume, and service raceway volume as required
first-print Gate 6 validation artifacts rather than internal layout references.
They make observer clearance reviewable before operation, but they do not prove
observer installation, focus recovery, vibration stability, imaging, Raman, or
biophotonics performance.
The observer fiducial/focus target check is exported as
`outputs/cad/aevum_one_row_coupon_validation_observer_fiducial_focus_target_check.step`
and `.stl`. It makes the underside bottom recess, objective keepout disk,
crosshair bars, and four local fiducials around each dry-bay aperture
inspectable as a required first-print validation body. It is a target-location
check, not proof of optical contrast, focus repeatability, vibration stability,
or Raman/biophotonics signal quality.
The observer optical stability check is exported as
`outputs/cad/aevum_one_row_coupon_validation_observer_optical_stability_check.step`
and `.stl`. It is a required validation-only blocker checklist tying eight
Gate 6 evidence requirements to observer performance claims: stray light,
baffle reflections, fiducial visibility, focus repeatability, vibration
stability, thermal drift, signal baseline, and wet-boundary optical
contamination. It is CAD proxy evidence only; it does not prove imaging,
Raman, or biophotonics performance.
The observer kinematic split check is exported as
`outputs/cad/aevum_one_row_coupon_validation_observer_kinematic_split_check.step`
and `.stl`. It is a required Gate 6 validation-only checklist that binds the
compact front-end swept body, carriage envelope, service raceway, dry bay, and
fiducial/focus targets into one observer split rule. A Gate 6 pass cannot treat
the larger carriage as an objective-centered body or claim service-loop/focus
recovery until the physical split is inspected.
The assembly-state witness check is exported as
`outputs/cad/aevum_one_row_coupon_validation_assembly_state_witness_check.step`
and `.stl`. It combines the negative-state witness footprints already used by
the opt-in service modes for missing microplates, missing septum mats, missing
perimeter gaskets, missing gas PCB cartridges, missing service leads, missing
sample/relief cap, and unseated latch bearing flats. This is validation-only
geometry; it proves the review cues exist in the package, not that a physical
operator has inspected or passed the assembly.
The gasket compression gap gauge is exported as
`outputs/cad/aevum_one_row_coupon_validation_gasket_compression_gap_gauge.step`
and `.stl`. It is a validation-only printable gauge with three reference blades
for the current latch compression budget: minimum, target, and maximum gasket
squeeze. It gives Gate 2 dry assembly a concrete gap-reference artifact, but it
does not prove gasket compression until the printed stack is measured.
The fail-closed pre-run inspection check is exported as
`outputs/cad/aevum_one_row_coupon_validation_fail_closed_prerun_inspection_check.step`
and `.stl`. It is a validation-only inspection coupon whose metadata enumerates
eight blockers that prevent OT-2 operation until evidenced: missing stack
items, unseated sample/relief cap, unlatched wedges, out-of-range gasket
squeeze, missing gas PCB cartridges, missing or unmated service leads, service
dress over the operating field, and blocked dry-bay/witness paths. It does not
act as an interlock; it makes the Gate 2 pre-run inspection rule explicit.
The printability support-cleanup check is exported as
`outputs/cad/aevum_one_row_coupon_validation_printability_support_cleanup_check.step`
and `.stl`. It is a required Gate 1 validation body whose checklist blocks
print QC pass until support scars, slide-path debris, gas barb bore blockage,
sensor pocket debris, dry-bay gutter bridges, and split-segment edge cleanup
that removes authority features have been physically inspected.
The sensor service cable envelope check is exported as
`outputs/cad/aevum_one_row_coupon_validation_sensor_service_cable_envelope_check.step`
and `.stl` so row-end electrical cable bend and egress space can be reviewed
without making external cables printed production parts.
The sensor connector service clearance check is exported as
`outputs/cad/aevum_one_row_coupon_validation_sensor_connector_service_clearance_check.step`
and `.stl`. It is a required first-print Gate 6 validation body so connector
mating, unmating, latch access, and cable service clearance must be inspected
before side electrical service can support a sensor/thermal pass claim.
The electrical connector mating-state check is exported as
`outputs/cad/aevum_one_row_coupon_validation_electrical_connector_mating_state_check.step`
and `.stl`. It uses the same geometry as the
`electrical_connectors_unmated` review mode: stationary board/header bodies,
pulled-back plug/latch/cable bodies, and mating-gap witnesses for each lower
or lid service connector. This is validation-only geometry and is not installed
as a production part.
The combined operating service dress check is exported as
`outputs/cad/aevum_one_row_coupon_validation_operating_service_dress_check.step`
and `.stl` so the attached gas and electrical service path can be inspected as
one normal OT-2 operating envelope. The first-print Gate 3 placement worksheet
is generated from the same target set, so physical deck-placement evidence must
check the seated, dressed assembly against that service-dress envelope before
OT-2 placement can be marked pass-ready.
The row tiling/service clearance check is exported as
`outputs/cad/aevum_one_row_coupon_validation_row_tiling_service_clearance_check.step`
and `.stl`. It combines the installed row footprint with eight neighboring-slot
keepout volumes and eleven gas/electrical service envelopes so Gate 3 can review
row-to-row tiling and service dress as one artifact.
The first-print Gate 2 dry assembly worksheet is generated from the dry stack,
latch, service-dress, sensor-install, and dry-bay openness targets, so a dry-fit
pass requires measured or photo evidence before wet testing or OT-2 placement.
The first-print Gate 4 wet/dry witness worksheet is generated from the required
headspace barrier and shared-volume bodies, required dry-bay envelope and
boundary bodies, wet collector, inboard dam, aperture-threshold, and
witness-gutter targets, so sealed headspace and dry-bay protection cannot be
marked pass-ready without dye, condensate, debris, continuity, boundary
clearance, and ingress evidence.
The passive leak/wet-dry protocol and template define the physical dye,
condensate, witness-gutter, inboard-dam, aperture-threshold, and protected
dry-bay evidence required to close that worksheet.
The first-print Gate 5 consumable/puncture worksheet is generated from the
required consumable metrology gauge, required all-well swept-path body, real
plate/mat metrology, all-well puncture, puncture-force, repeat-cycle, and
plate-shift targets, so pipette/septum access cannot be marked pass-ready from
CAD alone.
The first-print Gate 6 sensor/thermal worksheet is generated from sensor
package or blank installation, gas-PCB cartridge sealing, SHT41 exposure, IR
gasket/FOV, harness continuity, required connector service clearance, cable
dress, required observer envelope checks, observer kinematic split, and
thermal-proxy planning targets, so powered sensor, observer, or
cell-temperature claims cannot be marked pass-ready from CAD alone.
The first-print service-state review worksheet is generated from the CAD
service and negative-review mode manifest. The writer can generate one
plain-Python CadQuery bounds CSV per installed, service, and negative-review
viewer mode and mark the worksheet ready only when each referenced CSV has
matching mode metadata, positive part bounds, absent expected-removed parts, and
present negative-review witness parts. This closes the digital service-state
review surface while leaving Gate 1-6 physical acceptance unchanged.
The gas PCB flow-cell check is exported as
`outputs/cad/aevum_one_row_coupon_validation_gas_pcb_flow_cell_check.step`
and `.stl`; it is a required first-print Gate 6 validation body so gas PCB
aperture, dead-volume, and gasket-registration evidence must trace to a duct
sampling cell instead of an open top-headspace claim before sensor/thermal pass
can be accepted.
The next physical gate is
[`docs/protocols/one_row_coupon_first_print_readiness.md`](../protocols/one_row_coupon_first_print_readiness.md).
That protocol ties the current generated parts and validation checks to print
QC, dry assembly, OT-2 placement, passive leak/wet-dry witness, consumable
puncture, and sensor/thermal proxy evidence. It is also the scope guard for
overengineering: further CAD detail should come from failed or incomplete
physical gates, not visual completeness.
The side gas tube envelope check is exported as
`outputs/cad/aevum_one_row_coupon_validation_side_gas_tube_envelope_check.step`
and `.stl` so side service bend and strain-relief space remain reviewable
without making tubing a printed production part.
The wet/dry failure-path check is exported as
`outputs/cad/aevum_one_row_coupon_validation_wet_dry_failure_path_check.step`
and `.stl` so aperture-local witness gutters can be reviewed as a required
first-print Gate 4 validation body instead of only as hidden CAD layout data.
The dry-bay envelope and boundary checks are exported as
`outputs/cad/aevum_one_row_coupon_validation_dry_bay_envelope_check.step` and
`outputs/cad/aevum_one_row_coupon_validation_dry_bay_boundary_check.step` with
matching `.stl` files; both are required first-print Gate 4 bodies so the
reserved observer volume and boundary rail clearance are reviewed before
dry-bay protection claims.
The headspace barrier and headspace volume checks are exported as
`outputs/cad/aevum_one_row_coupon_validation_headspace_barrier_check.step` and
`outputs/cad/aevum_one_row_coupon_validation_headspace_volume_check.step` with
matching `.stl` files; both are required first-print Gate 4 bodies so the
sealed perimeter and continuous shared row headspace are reviewed before wet/dry
pass claims.
The side gas leak witness check is exported as
`outputs/cad/aevum_one_row_coupon_validation_side_gas_leak_witness_check.step`
and `.stl`; it is a required first-print Gate 4 body so side-service gutter and
inboard-dam routing can be reviewed separately from the solid lid cover.
The sample/relief leak witness check is exported as
`outputs/cad/aevum_one_row_coupon_validation_sample_relief_leak_witness_check.step`
and `.stl`; it is a required first-print Gate 4 body so the cap shelf, gutter,
and inboard dam can be reviewed separately from the solid lid cover.
The gasket tab leak witness check is exported as
`outputs/cad/aevum_one_row_coupon_validation_gasket_tab_leak_witness_check.step`
and `.stl`; it is a required first-print Gate 4 body so the lower/upper
front/rear tab-root gutters and dams can be reviewed separately from the support
frame and lid shell.
The dry-bay ingress audit check is exported as
`outputs/cad/aevum_one_row_coupon_validation_dry_bay_ingress_audit_check.step`
and `.stl` so external wet-service collectors, inboard dams, and the protected
dry-bay footprint can be reviewed together without making the audit overlay a
production part.
The adjacent deck slot keepout check is exported as
`outputs/cad/aevum_one_row_coupon_validation_adjacent_deck_slot_keepout_check.step`
and `.stl`. It shows the modeled neighboring OT-2 slot envelopes used to test
side-service overhead clearance.
The material cleaning witness coupon is exported as
`outputs/cad/aevum_one_row_coupon_validation_material_cleaning_witness_coupon.step`
and `.stl`; it is a required first-print validation body for same-material
cleaning, soak, scrub, odor, and exposure observations on installed surface
classes whose manifest disposition remains cleaning-pending. It is not a proxy
for disposable COTS consumables, electronics, cable leads, tubing, or biological
compatibility evidence.

The CAD module also exposes a machine-checkable assembly manifest through
`row_coupon_part_manifest()`. The manifest assigns every installed part a
role, fabrication source, retention/no-glue policy, and visibility class; it
assigns every validation overlay a validation-only role; and it declares the
parts removed/added by each opt-in review state. The test suite compares this
manifest against the actual installed, validation, and review-mode builders so
new visible geometry cannot enter the model without an operating, service, or
validation role. The manifest also carries the explicit first-print policy:
allowed installed fabrication sources, allowed nonprinted exceptions, and
forbidden retention authority terms such as metal inserts, metal fasteners,
adhesive bonds, thermal stakes, permanent welds, and hidden bonded authority.
The generated first-print package manifest prints those policy rows so the
handoff cannot silently reintroduce metal or glue to make Gate 1 pass. It also
prints the 2026-06-04 material-authority decision that supersedes the older
authority-insert stance for this coupon's mechanical assembly, and prints an
operating material/exposure table for every installed part:
wet-headspace boundaries, wet consumables, gas sample paths, dry sensor
packages, dry electrical service regions, dry latch/exterior surfaces, their
service disposition, and the physical gate expected to supply evidence. This is
a classification contract only; BSL1 material, cleaning, leachable, odor, and
biological survival claims remain blocked until measured. The sample/relief cap
manifest entry now matches the modeled seal interface:
`printed_annular_lip_in_lid_seat_no_screws_no_glue`, not the older friction-plug
description.

The installed part tree is:

```text
top

  printed_wedge_locks
  printed_sample_relief_cap
  gas_sensor_pcbs
  printed_gas_pcb_keeper_doors
  gas_pcb_interface_gaskets
  cots_gas_service_tubes
  lid_cover
  lid_sensor_service_cable_pigtails
  printed_lid_sensor_connector_shrouds
  lid_sensor_service_connectors
  lid_harness_cover
  lid_sensor_harness
  headspace_sht41_microcarriers
  lid_manifold_shell
  upper_gasket
  cots_septum_mats
  cots_microplates
  wet_chamber_frame
  lower_gasket
  lower_sensor_service_cable_pigtail
  printed_lower_sensor_connector_shroud
  lower_sensor_service_connector
  lower_harness_cover
  lower_sensor_harness
  ir_thermopile_face_gaskets
  ir_thermopiles
  plate_support_frame
  deck_pods

bottom
```

The CAD API intentionally does not expose `base` or `lid_manifold` compound
builders. The lower assembly is validated as separate `deck_pods` and
`plate_support_frame` parts, and the lid is validated as separate
`lid_manifold_shell` and `lid_cover` parts. This keeps helper APIs aligned with
the production assembly tree instead of preserving unified bench compounds.

The red tabs in the viewer are `printed_wedge_locks`: removable printed
compression wedges for the lid/gasket stack. They are not caps, ports, or sensor
fixtures. Each wedge is a slotted U-shaped side-insert with a lead-in ramp, high
bearing flat, release ears, detent bumps, raised witness stripes, and visible
seated position. The remaining round/cylindrical top feature is the
sample/relief service port and its explicit `printed_sample_relief_cap`. Supply
and return gas features now sit on the side edges of `lid_cover`, outside the
septum access windows. Production needs reversible perimeter compression and
service ports, but the latch stations must clear every port boss and adapter;
the current CAD omits any wedge station whose receiver envelope would overlap
the remaining top service port.

The blue service piece in the default viewer is `printed_sample_relief_cap`.
It seals the explicit sample/relief port with an integral annular lip seated in
the printed lid-cover boss, and it is not a flow adapter. It now uses only the
cap flange, seal lip, and grip tab needed for closure and removal; the former
role-code marker nubs are removed because the operating design has only one top
sample/relief closure. The orange/yellow geometry around that boss is part of
the printed `lid_cover`: the receiving seal seat, an outboard leak/witness
shelf with a shallow gutter, plus an inboard dam. The optional blue
`flow_test_adapters` remain opt-in validation geometry and are not part of the
default production scene.

The port negative states are review scenes, not production alternatives. In
`sample_relief_cap_missing`, the sample/relief cap is removed and a red witness
ring marks the uncapped service port. In `sample_relief_cap_unseated`, the
review cap is shown lifted from its seated plug position. The former plural
port-cap and future-adapter-missing review states have been removed; passive
`flow_test_adapters` remain opt-in validation geometry shown only with
`--show-flow-adapters`, not a production assembly-state claim. None of these
review bodies are exported as production fabrication parts.
The `latches_unseated` review scene follows the same rule: it replaces
`printed_wedge_locks` with pulled-back review wedges and seated-station
witnesses without changing the production export tree.
The `septum_mats_missing` review scene removes `cots_septum_mats` and adds
per-plate footprint witness frames at the expected seated mat top plane. It
checks assembly-state visibility for a missing consumable mat while keeping the
lid, plates, gaskets, latches, and services in their normal operating positions.
The `microplates_missing` review scene removes `cots_microplates` and the
dependent `cots_septum_mats`, then adds per-plate support-datum witness frames
so an absent plate stack is visible without changing the normal installed
state. The `perimeter_gaskets_missing` review scene removes `lower_gasket` and
`upper_gasket`, then colors the missing compressed gasket volumes as witnesses
between the support frame, wet chamber frame, and lid shell. Both scenes keep
the rest of the assembly in its normal operating position to expose failures
that would otherwise be hidden by an apparently assembled stack.

The `dry_bay_ingress_audit_check` validation overlay combines the protected
dry-bay footprint with external wet-service collectors and their inboard dams.
It distinguishes collection geometry, which must sit outside the dry-bay
footprint, from barrier geometry, which may sit at the protected margin. This
is a CAD-level ingress routing audit; it does not replace wetting, capillary,
condensate, or leak-rate testing.

The `gas_pcbs_missing` review scene removes `gas_sensor_pcbs` and the dependent
`gas_pcb_interface_gaskets`, then adds supply/return cartridge-footprint and
duct-seal witnesses. The printed keeper doors remain in place so the view
shows the dangerous state where the lid can look assembled while the gas-state
electronics and sealed duct sampling interface are absent.

The `service_leads_missing` review scene removes only the connected COTS service
leads: `cots_gas_service_tubes`, `lower_sensor_service_cable_pigtail`, and
`lid_sensor_service_cable_pigtails`. It leaves the printed side gas fittings,
strain-relief features, keyed electrical connectors, connector shrouds, lid,
and lower frame in their operating positions, then adds handoff witnesses where
the absent tubes and cable pigtails should enter those interfaces. This checks
the production claim that the coupon is connected for operation, not merely
equipped with printed barbs and connector bodies.

The `electrical_connectors_unmated` review scene removes the installed
electrical connector assemblies and COTS cable pigtails, then replaces them
with pulled-back plug/latch/cable review geometry plus mating-gap witnesses.
The printed shrouds, harness channels, snap covers, lid, and lower frame remain
in normal operating position so an unplugged service lead cannot be hidden by
the presence of a connector-shaped printed interface.

The `--show-latch-demo` scene is not part of the installed production tree. It
is a print-native mechanism section showing the intended complete latch: lower
catch, compressed gasket proxy, upper receiver, sliding wedge, hard stop, and
visible witness mark as separate printable solids. The installed coupon now
realizes the same non-print-in-place direction with wet-frame tension posts,
lid-owned receiver rails, and removable side wedges rather than a hidden captive
slider.

The current geometry includes:

- four printed deck pods arranged along one OT-2 column;
- slot-edge standoff feet that preserve the modeled dry-bay observer sweep;
- four lower OT-2 slot shoes that fit inside the deck openings;
- printed pod/frame keys and matching support-frame underside pockets;
- a separate printed plate-support datum frame;
- deck-frame keepout checks for the aluminum ribs between openings;
- keyed front-foot notches for orientation and click-in inspection;
- deck slot footprint checks below the slot shoes;
- four plate support nests with perimeter lands;
- a separate lower perimeter gasket with service tabs between support frame and
  wet chamber;
- lower gasket capture grooves in the support frame and wet-chamber frame;
- lower tab-root witness gutters and inboard dams in the plate-support frame;
- a full-footprint removable wet-chamber frame enclosing the row after top-down
  plate loading;
- side service lanes and per-plate plenum divider windows in that frame;
- internal condensation pockets in the wet-chamber frame service lanes;
- four installed SBS microplate bodies with perimeter sidewalls, bottom
  observation windows, and 96 published-profile well openings per plate seated
  on those integral support lands;
- dry-bay apertures under each plate position;
- plate-margin IR sensor apertures, integral raised drip collars, underside
  pockets, screwless retention lips, installed MLX90614 thermopile envelopes,
  and dry-side compressible face gaskets outside the central observer aperture;
- a lower dry IR sensor harness with branch routes from each thermopile pocket
  into a covered left-side dry raceway and a JST-GH-shaped row-end service
  connector assembly;
- printed raised wet/dry thresholds around each dry-bay aperture;
- shallow wet/dry witness gutters beside those thresholds in the plate-support
  frame;
- bottom-side objective keepout and crosshair cuts;
- underside observer fiducial pockets around each aperture;
- internal dry-bay swept observer volume checks;
- internal dry-bay boundary/rail checks outside the swept volume;
- representative moving observer-head envelope for focus, front-end optics, and
  carriage clearance;
- observer front-end swept-body check that reaches all well centers with the
  compact optical head, not the full carriage body;
- side service raceway check for flex, fiber, wiring, air isolation, and
  strain relief outside the observer sweep;
- microplate observation-region recesses;
- a separate upper compressed outer-row gasket with service tabs on the full
  chamber perimeter;
- upper gasket capture grooves in the wet-chamber frame and lid shell;
- upper tab-root witness gutters and underside dams in the lid shell;
- four installed round pre-slit 96-well silicone septum mat inserts with plug
  and through-depth slit-relief geometry;
- an internal wet-chamber barrier check around the full row perimeter;
- an internal shared-headspace volume check that includes side service lanes;
- a printed lid manifold shell with shared underside headspace relief,
  mat-seat pockets, pick-relief notches for service, and four screwless
  per-plate SHT41 microcarrier sockets tied into a covered lid-shell sensor
  bus;
- four installed SHT41 headspace microcarrier envelopes for plate-local RH/T
  evidence;
- a lid sensor harness with separate covered gas-PCB and SHT41 bus routes;
- a lid harness cover with printed snap-tab retention kept inside the row
  footprint;
- a separate printed lid cover carrying raised side duct bars, integrated side
  supply/return gas fittings, the sample/relief service boss, row-axis
  hard-stop pads, screwless supply/return gas-PCB side cartridges, and covered
  gas-PCB harness routes;
- two installed supply/return gas-state PCB envelopes carrying STC31 CO2 plus
  colocated SHT41 RH/T compensation;
- JST GH 1.25 mm 4-circuit service connector geometry for the lower dry IR bus
  and the removable lid sensor buses, each seated in a printed keyed shroud;
- a printed lid-cover tongue and matching shell groove for reversible duct
  alignment;
- printed wedge locks for fastener-free compression;
- printed wedge receiver rails integrated into the lid cover;
- an explicit sample/relief lid service port with printed seal land, annular
  lip seat, cap plug/flange/grip/lip metadata, and a separate installed
  `printed_sample_relief_cap`;
- a sample/relief cap leak witness shelf, shallow gutter, and inboard dam
  integrated into the printed lid cover;
- raised column-side supply and return ducts;
- side-connected supply/return gas fittings with printed barb-retention beads,
  printed strain relief, and validation-only tube bend envelopes;
- removable flow-test adapter geometry for passive smoke/fog and humidity
  proxy setup;
- side diffuser and return slots per plate position;
- open septum-field access windows for all 96 liquid-handler targets per plate,
  without treating those paths as gas chimneys;
- no generic top fiducial or insert-pocket cuts in the lower support-frame seal
  land; only underside dry-bay observer fiducials remain in the installed
  production geometry;
- installed, exploded, lid-off, sensor-install, mats-exposed, wet-frame-off,
  and plates-removable CAD service views;
- opt-in port review modes for missing and mis-seated sample/relief caps.

## Implemented First-Build Sensor Mount Features

The following mount and harness features are now represented in the generated
CAD as physical envelopes, pockets, apertures, covered routes, screwless
retention, and JST-GH-shaped service connector assemblies. They are driven by
sensor-architecture decisions documented in
[`docs/engineering/sensor_pcb.md`](sensor_pcb.md) and the 2026-05-31
decision log entries (sensor PCB, sample-plane temperature).

The current row coupon realizes all first-build sensing roles as physical
features, not as reference markers:

- two supply/return gas-state sensor PCBs, each carrying STC31 CO2 plus
  colocated SHT41 RH/T compensation;
- four per-plate headspace SHT41 RH/T sensors for spatial headspace
  evidence across the row;
- four per-plate MLX90614 IR thermopiles for sample-plane proxy
  temperature at the plate underside margin.

Retention is screwless wherever the row module can reasonably print the
mechanism: datum shelves, stops, snap lugs, wedges, retainers, covers, or
sliding keepers. Metal screws, threaded inserts, adhesive, or bonded
retention are not part of the row-coupon intent unless a separate
materials-strategy exception is recorded.

### Sensor PCB pockets (supply path + return path)

Two screwless side-cartridge sockets in the row module's raised supply/return
duct volumes, each holding one
custom-fabricated sensor PCB carrying an STC31 CO2 sensor and a
colocated SHT41 RH/T sensor (see [sensor PCB](sensor_pcb.md) for the PCB
design).

Per pocket, the CAD provides:

- a printed vertical side-cartridge pocket sized for a ~25 x 30 x 5 mm
  PCB envelope, located on the dry side of the supply or return duct so
  the STC31 sees representative gas through a registered aperture without
  placing the PCB in the wet headspace or consuming the top septum/pipette
  access field;
- a full-height printed dry-side cassette around the PCB envelope; the
  board should read as an installed electronics cartridge, not as a bare
  blade protruding from the biology-facing headspace;
- a gasketed duct-sampling interface: a compressible gasket patch, printed
  seal land, shallow low-dead-volume flow cell, and compression pads aligned
  to the PCB sensing aperture so the sensor reads the controlled duct stream
  rather than open room air above the lid;
- a screwless printed retention mechanism: datum shelf, lateral/end
  stops, gas-aperture registration, and an anti-lift snap, wedge, clip,
  or sliding keeper that seats the PCB without crushing the sensor's gas
  aperture;
- optional PCB holes, edge notches, or tabs may be used as printed
  alignment/retention features, but the production-intent coupon must not
  require metal screws for PCB installation;
- a gas channel aperture in the pocket wall, ~2 mm diameter, aligned
  with the PCB's top-side gas aperture when the PCB is seated; this is the
  only intentional communication between the PCB pocket and the controlled
  gas path;
- a covered lid-cover harness branch routing the 4-wire I2C harness
  (SDA, SCL, VDD, GND) from each PCB into a lid-owned gas sensor bus;
- placement consistent with the low-turbulence row headspace
  requirement: supply-path pocket in the upstream mixing volume or
  plenum, return-path pocket in the downstream return path before any
  exhaust restriction;
- no interference with the lid/manifold service ports, the septum mat
  access fields, or the dry observer bay below.

### Per-plate headspace RH/T pockets (4 positions)

Four standalone SHT41 RH/T sensors are required, one at each plate
position, to measure local headspace humidity and air temperature across
the row. These are distinct from the two SHT41 sensors colocated with the
STC31 sensors on the supply/return gas-state PCBs.

Per pocket, the CAD provides:

- a printed carrier pocket or socket for a first-build SHT41 microcarrier
  envelope of ~12 x 12 x 4 mm, with the sensor membrane/opening facing
  the shared wet headspace at that plate position;
- screwless retention for the carrier: datum floor, side stops, anti-lift
  keeper, and finger/tool access for service removal;
- printed registration features matched to the microcarrier's edge
  notches, holes, or tabs so the sensor face is repeatably oriented;
- a local headspace aperture or open face that exposes the SHT41 membrane
  to representative plate-local headspace without putting the sensor in a
  direct supply jet, stagnant dead corner, liquid path, or pipette access
  field;
- drip/splash geometry so condensate cannot pool on the membrane or wick
  down the harness; solder pads and harness strain relief should sit on
  the protected service side, with only the sensing face/opening exposed
  as required;
- placement in the chamber side/service lanes or lid/manifold wet-side
  volume, outside the septum access field, outside the well-grid imaging
  sweep, and outside the dry observer bay;
- an inline covered lid-shell sensor bus routing 4-wire I2C from each
  carrier toward the removable lid's JST-GH-shaped service connector, with
  strain relief and service-loop clearance that do not cross pipette
  paths, deck-contact faces, or observer apertures;
- replacement access after lid/wet-frame service without disturbing the
  plates or the septum mats.

The current CAD implements this as a side-loaded cassette tunnel in the
`lid_manifold_shell`, open to the row-end service edge and closed to the
wet chamber except for the controlled membrane aperture. Each pocket now
has a protected outer cassette volume, a side-service pocket cut, a
nonzero datum floor, a roof/anti-lift keeper, side and back stops, a
matching registration key/notch, finger relief at the service edge, and
an underside drip-break ring around the membrane aperture. This prevents
the SHT41 carrier from being interpreted as an exposed block in the wet
headspace while still keeping the membrane in representative local
headspace.

### IR sensor pockets in the plate-margin area (4 positions)

Four pockets in the plate-support frame, each holding one MLX90614ESF-DCH
IR thermopile aimed up at the underside of one CellVis plate. These
provide sample-plane (cell-contact-proxy) temperature without touching
the plate (per the plate-as-consumable constraint).

Per pocket, the CAD provides:

- a printed pocket sized for an 8 mm TO-39 sensor body, located in the
  **plate-margin area** of the support frame, outside the central
  well-grid swept volume that the observer requires for well-imaging
  access;
- the CellVis plate's well grid spans ~99 x 63 mm centered on the plate;
  margins of ~11-14 mm exist on all four sides between the well grid
  and the plate footprint edge; the IR pocket must fall within this
  margin band, not under the well grid;
- a small IR-only aperture in the support frame (~5-8 mm diameter, sized
  for the MLX90614's field of view) **distinct from the central
  observer aperture**, giving the IR sensor a clear line of sight to
  the plate underside without affecting observer access to the wells;
- sensor axis aimed straight up at the plate underside; the current DCH
  narrow-FOV assumption is represented by a 12 deg FOV parameter and a
  computed spot based on sensor-to-plate distance, not a hardcoded broad
  35 deg placeholder;
- screwless retention and service removal for the TO-39 body without glue
  or metal fasteners;
- a raised printed drip collar on the plate-support top face plus a
  dry-side compressible face gasket captured around the TO-39/lens
  aperture, so the optical opening is not an unqualified wet-to-dry leak
  path;
- lower dry harness routing from each pocket into a covered left-side
  dry raceway with strain relief and a row-end JST-GH-shaped service
  connector;
- no interference with the observer's swept volume, deck feet, or
  service raceway envelopes already in the coupon design.

The current CAD treats the IR aperture as an optical opening with a
defined wet/dry interface. The printed support frame owns the top-side
drip collar, while `ir_thermopile_face_gaskets` is a separate installed
compressible seal part that moves with the IR thermopile stack in the
`sensor_install` view.

### Sensor harness domains

The harness is modeled as two service domains, because the lower support
structure and removable lid are assembled and serviced differently:

- **lower dry IR harness**: four thermopile branches route into a left-side
  underside raceway on the plate-support frame, stay outside the dry observer
  aperture/swept volume and deck feet, and terminate at a lower row-end JST GH
  1.25 mm 4-circuit connector assembly;
- **lid sensor harness**: two gas-PCB branches route in lid-cover gas buses,
  while the four SHT41 carriers share an inline lid-shell bus; these routes stay
  outside septum access windows and terminate at removable-lid JST GH 1.25 mm
  4-circuit connector assemblies;
- **printed retention**: both domains have printed snap-cover geometry and
  modeled strain-relief rectangles; each connector assembly sits inside a
  printed keyed shroud with an open +Y mating side and pin-1 marker; no glue or
  metal fasteners are assumed for harness retention.
- **external service egress**: each lower/lid service connector has a
  production-visible COTS cable pigtail exiting +Y plus a validation-only cable
  bend envelope sized from the modeled bend radius and straight service length.
  The installed connector/plug/shroud/pigtail geometry represents the connected
  operating state; the larger cable envelope is a clearance proof, not a printed
  part.

### Production-prototype sensor installation and test gates

The production prototype treats each sensor as a removable, bench-testable
module. The default installed view shows the closed surface state. The
`sensor_install` view pulls each sensor family along its service path and adds
installation path check geometry:

- gas sensor PCB cartridges release through printed keeper doors and pull +Z
  out of dry-side lid cassettes; installation is -Z into the cassette until the
  PCB aperture compresses against the interface gasket and registers to the
  low-dead-volume gas-duct sampling cell;
- headspace SHT41 microcarriers pull +X from the lid service edge and install
  -X into protected side pockets, exposing only the sensing face/opening to the
  wet headspace;
- lower IR thermopiles pull -Z from the dry underside and install +Z into the
  plate-support pockets, with the lens registered to the plate-margin aperture.

The row coupon now models ten sensor installation steps: two gas cartridges,
four headspace RH/T carriers, and four lower IR thermopiles. The test sequence
for the production prototype is:

1. incoming module electrical test: bench I2C scan, current draw, sensor
   identity, and baseline readings before installation;
2. pocket fit and retention test: insertion/removal force, no looseness, no
   crushed package, and accessible release feature;
3. aperture registration test: gas, headspace, or IR aperture centered and not
   blocked after seating;
4. installed dry electrical test: assembled dry coupon bus scan and connector
   wiggle/dropout check;
5. environmental step response test: humidity, temperature, CO2, and airflow
   steps without biology;
6. wet non-biological exposure test: loaded plates plus water/media proxy for
   condensation, splash, drift, and leak-path evidence;
7. BSL1 biology commissioning: only after the previous gates pass, using
   low-risk biology to correlate sensor traces with growth state.

### CAD validation tests these features must pass

The row coupon's focused tests now verify, and future edits should preserve:

- sensor PCB pocket center is within the row module's gas plumbing
  volume (not outside the chamber, not in the well-access path);
- sensor PCB gas aperture aligns with the channel-side aperture within
  ~0.5 mm tolerance when PCB is seated;
- sensor PCB gas aperture aligns to the side supply/return service duct
  reference, not a top gas port;
- sensor PCB interface includes a compressible gasket, printed seal land,
  compression pads, and shallow flow-cell validation volume inside the duct
  height band, so the sensor cannot be interpreted as open-top lid sampling;
- side supply/return manifold blocks, duct openings, fitting stems,
  barb-retention beads, strain-relief features, and validation tube envelopes
  stay outside all septum access windows;
- side supply/return leak witness gutters drain outboard, stay outside the
  dry-bay footprint, and are backed by a printed inboard dam;
- side gas tube/fitting envelopes meet the adjacent-slot overhead clearance
  requirement over the modeled neighboring OT-2 slot keepouts;
- the combined operating service dress check includes side gas
  fitting/tube/strain-relief envelopes plus electrical cable bend envelopes,
  avoids the dry-bay and septum access windows, and keeps any adjacent-slot
  overlaps above the modeled deck keepout;
- the OT-2 toolhead swept-body validation envelope spans all 384 septum targets
  and starts above the assembled coupon, side gas tube/fitting envelopes, and
  electrical service cable envelopes;
- the well cell-plane validation overlay spans all 384 published CellVis
  well-bottom targets at the plate-top-to-cell-plane depth and remains inside
  the installed plate stack;
- the IR thermopile FOV spot validation overlay marks each plate-margin proxy
  spot at the plate underside, stays outside all modeled well-bottom cell-plane
  disks, and remains validation-only rather than installed production geometry;
- sensor PCB retention is screwless in the row coupon and has a modeled
  service release path;
- per-plate SHT41 pocket is exposed to the wet headspace, outside the
  septum/pipette access field, outside the observer sweep, and outside
  direct supply/return jet paths;
- per-plate SHT41 carrier keeps harness strain relief and solder pads out
  of pooling condensate while exposing the sensing face/opening;
- per-plate SHT41 inline lid-shell bus remains outside septum/pipette
  access, deck-contact faces, observer apertures, and adjacent tile
  envelopes;
- IR sensor pocket is fully outside the modeled observer front-end
  swept body (current: 120.00 x 347.50 x 40.00 mm), so the IR sensor
  does not occlude the well-imaging path;
- IR sensor pocket is within the plate's footprint perimeter and does
  not protrude beyond the row footprint envelope (no side protrusions
  affecting future tile adjacency);
- IR sensor pocket and aperture are inside the plate-margin band and
  outside the modeled well-grid rectangle;
- IR sensor aperture clearance does not overlap the central observer
  aperture for the same plate position;
- IR sensor retention is screwless in the row coupon and has a modeled
  service release path;
- IR sensor field-of-view spot remains on the plate-underside margin and
  does not intrude into the modeled well-grid region;
- lower dry IR harness branches stay outside the observer apertures,
  observer swept body, and deck feet;
- gas-PCB lid-cover branches satisfy the modeled minimum bend length
  before entering the lid gas buses;
- all modeled harness parts and covers stay inside the row footprint;
- sensor harnesses remain separated into lower dry and removable-lid
  service domains with keyed JST-GH-shaped connector assemblies and service
  clearance checks;
- installed electrical cable pigtails exit +Y from the row-end connectors and
  sit inside the larger validation-only bend envelopes, which extend beyond the
  row footprint for service handoff while avoiding the dry-bay and septum access
  windows.
- electrical connector unmated review mode pulls the JST-GH-shaped plug,
  latch, and cable pigtail back along the +Y mating/service direction while
  keeping printed shrouds and harness covers installed.
- sensor-install view includes ten service steps and path checks for gas PCB
  cartridges, headspace SHT41 carriers, and lower IR thermopiles, with no
  screws or glue in the modeled retention policy.

### Edge-to-center thermal characterization (validation evidence, not CAD)

Because the IR sensors read the plate-underside margin (not the central
well area), the row module's commissioning evidence must include a
one-time thermal characterization mapping the offset between
plate-margin temperature and central well-area temperature. This is
validation evidence, not CAD geometry; the characterization protocol
belongs in a future validation document, but the requirement is
recorded here so the CAD revision does not assume the IR readings are
already cell-area temperature.

## Validation Intent

This coupon should produce evidence for interface coexistence before the design
adds full environmental control or biology.

Required checks:

- print-native service order using printed structure, printed locks, printed
  seal carriers, COTS plates, and COTS septum mats;
- microplate seating repeatability;
- per-plate deck-space click-in and rocking/yaw resistance;
- lower slot-shoe seating inside each OT-2 opening with no aluminum-rib
  interference;
- printed shoe clearance against the actual OT-2 slot frames and retainers;
- deck engagement repeatability after remove/reinstall cycles;
- pod/frame key wear, pocket clearance, release direction, rocking, and yaw
  resistance;
- support-land flatness and row straightness;
- lower and upper gasket capture, service-tab access, preserved datum lands, and
  section-print fit;
- full-footprint chamber-skirt fit, lift-off service path, and no trapped-plate
  insertion failure;
- dry-bay aperture clearance and observer keepout;
- raised threshold and witness-gutter placement around each dry-bay aperture;
- standoff-foot clearance outside the dry-bay swept observer rectangle;
- dry-bay swept-volume clearance across all four apertures;
- underside observer fiducial visibility and repeatability;
- boundary/rail clearance outside the observer sweep;
- moving observer-head clearance through the 80 mm bay;
- service-loop and fiber/wire raceway clearance without crossing apertures;
- lid/manifold footprint discipline, including no side protrusions;
- gasket/seal seating and hard-stop-limited compression height;
- row-axis compression-stop placement at the perimeter rails and inter-plate
  seams;
- printed lock engagement, release, and witness-position repeatability;
- wedge receiver rail fit, insertion force, release access, and hard-stop
  contact;
- wet-chamber barrier fit, continuity, side-service-lane routing, and
  visibility;
- lower and upper skirt sealing surfaces, gasket witness marks, and leak path
  inspection;
- lid-owned shared headspace clearance and underside recess visibility;
- unobstructed pipette access through the intended top stack into every septum
  target;
- larger OT-2 pipette/toolhead swept-body clearance above the installed
  assembly and connected side gas/electrical services, followed by physical
  measurement on the real OT-2 before authorizing live motion;
- diffuser/return geometry visibility and flow path continuity;
- side supply/return service accessibility and sample/relief cap accessibility;
- sample/relief cap leak-witness routing to a visible edge, inboard dam
  placement below the cap flange, septum-field clearance, and dry-bay
  outboard-gutter separation;
- lower/upper gasket service-tab root witness gutters, inboard dam placement,
  dry-bay separation, and septum-field clearance;
- dry-bay ingress audit overlay for side gas, sample/relief, and gasket-tab
  wet collectors versus the protected observer-bay footprint;
- opt-in sample/relief-cap negative-state review for missing or unseated caps
  without changing the production export tree;
- opt-in latch negative-state review for unseated wedges and visible
  bearing-flat station witnesses without changing the production export tree;
- opt-in septum-mat negative-state review for missing COTS mat inserts with
  per-plate seated-footprint witnesses and no production export change;
- opt-in microplate-stack and perimeter-gasket negative-state review for
  missing plate/mat support dependencies and missing wet-chamber seal volumes
  with no production export change;
- opt-in gas-PCB cartridge negative-state review for missing supply/return gas
  electronics and missing duct-interface gasket compression;
- passive flow-test adapter fit for smoke/fog or humidity-tracer review;
- service-state review of installed, exploded, lid-off, mats-exposed,
  wet-frame-off, and plates-removable modes;
- observer front-end swept-body fit plus separate carriage/body/raceway
  kinematic split, with all three observer clearance bodies exported as
  validation artifacts;
- underside observer fiducial visibility after full assembly;
- reassembly repeatability after plate, gasket, and lid service cycles.

Environmental proxy checks after the first print:

- smoke or fog visualization through the supply and return paths;
- shallow-water liquid-surface disturbance checks under flow;
- humidity or tracer response at all four plate positions;
- condensation inspection after warm humid exposure;
- dimensional drift, creep, or seal seating changes after humidity soak.

## Non-Goals

- final sterile or cell-facing material validation;
- final gasket material or compression force selection;
- quantitative CO2 control;
- full row heating architecture;
- moving observer transport implementation;
- OT-2 live motion authorization.

Those remain future work. This coupon only earns the next design permission if
its measured physical claims stay cheap to revalidate after assembly, service,
heat, humidity, and motion.
