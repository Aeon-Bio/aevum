# First PoC Fixture

## Purpose

Build a screwless PLA raised interaction mule for the OT-2/P300 Gen2.

This print should push the system interaction, not merely prove basic reach.
It is not the row-shared environmental module. The full module target is an
array of registered glass-bottom plate tiles with a four-plate shared controlled
headspace over the shared dry inverted observation bay; this first fixture only
establishes access geometry, Z margin, and the wet/dry boundary.

## Tests

1. P300 body/nozzle collision with raised cassette envelope.
2. P300 access into mock 96-well geometry.
3. Center vs. off-axis access targets.
4. Repeated approach/retract cycles.
5. Dye dispense into mock wells.
6. Optional crude Cole-Parmer mat patch test if the patch can be mechanically trapped.
7. Bottom-side inverted-bay aperture and objective keepout reference.
8. Print QC through-hole and Z-step features for post-print measurement.
9. Incubator headspace boundary and wet/dry separator proxy.
10. Coarse geometry marks for orientation, target identity, offsets, fiducials,
    QC features, and Z-stack interpretation.

## Non-Goals

- Final sterile chamber surfaces.
- Final thermal design.
- Quantitative CO2/humidity validation.
- Functional gas sealing, humidification, or temperature control.

## Initial Parameters

The first source file is:

```text
cad/p300_poc_fixture.params.json
```

The initial stack height is intentionally editable:

```text
height_to_mock_plate_top = 80.0 mm
mat_plane = mock_plate_top + 8.0 mm
support_post_width = 6.0 mm
guide_plate_thickness = 1.5 mm
guide_hole_diameter = 4.0 mm
guide_hole_diameter_by_row = 3.0 / 3.5 / 4.0 / 4.5 mm
guide_style = separate_cassette
continuous sidewall = disabled
```

The emulated plate is based on the CellVis P96-1.5H-N product page:

```text
plate length: 127.60 mm
plate width: 85.75 mm
plate height: 14.30 mm
height with lid: 16.50 mm
well pitch: 9.00 mm
coverslip: #1.5H glass, 0.170 +/- 0.005 mm
bottom height: 1.73 mm from bottom of coverslip to plate bottom
catalog well size: 6.0 mm
well upper/opening diameter from dimension diagram: 6.80 mm
well lower diameter from dimension diagram: 6.21 mm
well bottom area: 30 mm^2
area-equivalent diameter from bottom area: 6.18 mm
diagram internal well depth: 11.93 mm
computed plate-top to cell-plane depth: 12.40 mm
implied top-recess/rim difference: 0.47 mm
max volume: 0.35 mL
```

Source:

```text
https://www.cellvis.com/_96-well-glass-bottom-plate-with-high-performance-number-1.5-cover-glass_/product_detail.php?product_id=50
```

The CAD well cut is now tapered: 6.21 mm at the lower end and 6.80 mm at the
opening. The labware definition reports the 6.80 mm opening diameter. The
12.40 mm depth is retained for the cell-plane/coverslip target because it comes
from the official plate height, bottom height, and coverslip thickness stack.

The first print includes one guide hole per mock well. Columns step through access
offsets so one run tests multiple geometries:

```text
column 1: center
column 2: +1.0 mm X
column 3: +1.5 mm X
column 4: +2.0 mm X
```

The current candidate final offset is:

```text
target offset: +1.5 mm X
```

The reason for the offset is to keep the central well region available for
inverted imaging while dosing near the side of the well. The 1.0/1.5/2.0 mm
columns are an offset sweep; +1.5 mm is the working target until the P300,
round mat, and CellVis plate are tested together. +2.0 mm is intentionally more
aggressive and may be too close to the wall for reliable low-Z liquid handling.

The first PoC is now split into three printed parts. The base print carries the
OT-2 datum and the mock-plate locator posts only. The mock CellVis plate cap
prints as its own part, carries the 4 x 4 mock wells, and carries the mat
cassette standoffs/pins. The mat cassette prints flat, drops over the plate-cap
cassette pins, sits 8 mm above the emulated plate top, and carries the offset
guide holes. This keeps the slit-to-well relationship registered through the
mock plate instead of through the base, while removing the need for
slicer-generated supports inside the optical bay.

## Top Mat Emulation

The interaction stack is split into three printed parts:

```text
base print:
  mock-plate support posts
  keyed screwless locator pins for the mock plate cap
  open optical-bay envelope

mock plate cap print:
  emulated CellVis plate slab
  4 x 4 mock wells
  locator cutouts matching the base plate pins
  vertical mat-cassette support posts
  keyed screwless locator pins for the mat cassette

mat cassette print:
  flat continuous printed mat/cassette emulator
  printed guide holes at offset entry points
  row diameter sweep: A=3.0 / B=3.5 / C=4.0 / D=4.5 mm
  shallow Cole-Parmer mat patch recess
  locator cutouts matching the plate-cap cassette pins
```

The cassette emulates access coordinates, the suspended mat plane, and the
top-of-cassette Z envelope. It does not mechanically emulate the flexible
silicone. The real Cole-Parmer mat will still need a separate cassette/coupon
test because Cole-Parmer does not publish plug diameter, mat thickness, slit
length, or slit orientation on the product page.

Important limitation: one physical mat patch has a regular 9 mm slit grid, so
it cannot simultaneously align to the center, +1.0, +1.5, and +2.0 mm columns.
The printed offset sweep can be tested without a mat first. With a real mat
patch, align the patch to one global offset at a time, starting with +1.5 mm X.

## Incubator Boundary

The first print now includes an open mechanical incubator envelope, not a
functional incubator:

```text
headspace height: 8 mm above mock plate top
continuous sidewall frame: disabled
four vertical cassette posts on the mock plate cap show the cassette/chamber envelope
mock plate cap: separate print, no under-plate support lattice
separate flat cassette shows offset access coordinates at the mat plane
explicit emulated plate lip: 2 mm
explicit emulated CellVis plate height: 14.30 mm
emulated plate bottom: z = 65.70 mm
emulated plate top: z = 80.00 mm
base print top: z = 67.70 mm at the mock-plate locator pins
installed stack top: z = 91.00 mm at the mat-cassette locator pins
cell-plane/well-bottom: z = 67.60 mm
wet/dry separator thickness below mock well bottoms: 3 mm
```

This tests the architectural boundary between the future humid culture side and
the dry inverted bay without introducing heaters, gas fittings, gaskets, or
biological materials. It intentionally favors visibility and print success over
a sealed sidewall.

## Labels

The first PLA print showed that small CAD text is not a reliable evidence aid.
The 1.8-2.2 mm text and 0.25 mm engraving/relief fused at the nozzle scale, so
the generated fixture now disables tiny printed text by default.

Use the physical geometry as the evidence source:

```text
guide-hole matrix location
guide-hole diameter coupon
Z-step coupon
round fiducial holes
keyed locator pins/cutouts
objective keepout/crosshair cuts
mat-patch corner marks
```

Human-readable labels and axis arrows are integrated into the printed parts as
coarse cuts. Do not make robot safety depend on printed text.

The current label set names the base/front/slot context, plate cap/A1 context,
mat cassette context, offset classes, and guide-hole diameters where there is
clear shelf space. Labels are kept away from guide holes, locator seats, mock
wells, mat pockets, and the optical-bay opening.

The base top includes +X and +Y arrows near the origin corner so the deck
coordinate frame can be read directly from the printed part.

The base-level registration marks are not well labels. They are exposed
fiducials for detecting the assembled fixture position and rotation after the
plate cap is installed:

```text
REG 1: x = 82.0 mm, y = 8.0 mm
REG 2: x = 119.76 mm, y = 77.48 mm
base orientation labels: integrated front-side cut
```

Previously attempted CAD labels, now removed from functional CAD:

```text
FRONT
OT2 SLOT 1
+X → / +Y ↑
REG 1 / REG 2
3.0 / 3.5 / 4.0 / 4.5 hole-QC labels
+1 / +2 / +3 Z-step labels
OPT AXIS
```

The surrounding 28 mm circular recess is the objective keepout/reference
footprint. The through-reference at the well-field center remains as geometry,
not as a printed text label.

Plate-field labels:

```text
rows: A / B / C / D
columns: 1 / 2 / 3 / 4
BAY BELOW
```

Cassette labels:

```text
offset columns: 0 / +1 / +1.5 / +2
diameter rows: 3 / 3.5 / 4 / 4.5
```

Tiny CAD text stays off the fixture. The current labels are coarse integrated
cuts with slicer preview required before use.

## Sealing Mat

Current mat target:

```text
Cole-Parmer 96-Well Microplate Sealing Mat, Silicone, Round, Pre-Slit; 5/PK
Catalog/item: EW-12920-06 / 1292006
```

Source:

```text
https://www.coleparmer.com/i/cole-parmer-96-well-microplate-sealing-mat-silicone-round-pre-slit-5-pk/1292006
```

Cole-Parmer specifies:

```text
number of wells: 96
well shape: round, deep
material: silicone
description: 96-Well Microplate Sealing Mat, Silicone, Round, Pre-Slit; 5/PK
```

Cole-Parmer also states that the silicone reseals after injections/pipetting,
that individual well plugs reduce cross-contamination, that the pre-slit option
supports easy pipetting, and that the mats fit standard 96- and 384-well
microplates.

Not published on the product page and still measurement-required:

```text
mat thickness
round plug diameter
plug height/profile
slit length
slit orientation
slit location relative to mat edge
outer mat dimensions
```

## Mat-To-Plate Gap Assessment

Current generated geometry:

```text
CellVis plate top: z = 80.00 mm
printed mat/guide plane: z = 88.00 mm
printed guide top: z = 89.50 mm
nominal plate-top to mat-plane gap: 8.00 mm
nominal plate-top to guide-top gap: 9.50 mm
```

This is acceptable for the first PoC because it intentionally tests a tall,
conservative headspace/cassette envelope. It is not yet a final cassette
dimension.

The self-sealing slit does not require the mat to be close to the plate. The
slit seals at the silicone plane. The mat-to-plate gap matters for different
reasons:

```text
1. tip guidance after the tip exits the slit
2. clearance for downward-facing round/deep mat plugs
3. CO2/RH headspace volume
4. whether the tip can enter the tapered CellVis well without wall scrape
```

For the candidate +1.5 mm X access offset:

```text
CellVis lower mock well radius: 3.105 mm
target offset: 1.5 mm
remaining radial clearance before tip radius/error: 1.605 mm
```

The basic clearance condition is:

```text
offset + tip_radius_at_well_rim + lateral_error < well_radius
```

At +1.5 mm offset this becomes:

```text
tip_radius_at_well_rim + lateral_error < 1.5 mm
```

That is plausible for a P300 tip, but it must be measured with the actual
Opentrons tip. The +2.0 mm offset leaves only 1.0 mm before accounting for tip
radius and lateral error, so it should be treated as an aggressive boundary
test, not the likely final offset.

The current 8 mm gap also amplifies angular error after the tip exits the slit:

```text
lateral_error_from_tilt = free_gap * tan(tip_tilt_angle)
2 degrees over 8 mm ~= 0.28 mm
5 degrees over 8 mm ~= 0.70 mm
```

If the real Cole-Parmer plugs protrude downward, the effective free gap is:

```text
effective_free_gap = 8.0 mm - plug_protrusion_below_mat_plane
```

That may make the real gap closer to the desired final range. If the plug
protrusion is greater than 8 mm, the current headspace will collide and must be
increased. If the plugs are too wide to enter the CellVis wells, the mat must be
held as a suspended septum plane rather than seated onto the plate.

Final cassette guidance after measuring the mat:

```text
target effective free gap from plug/slit underside to plate top: ~3-5 mm
keep +1.5 mm X as the first real offset target
keep +2.0 mm X as a stress test only
measure P300 tip OD at the mat contact depth and at the well rim
```

## Inverted Bay Reference

The underside includes shallow reference geometry for the future dry inverted
optics bay:

```text
aperture reference: 50 x 50 mm
separate mock plate cap leaves the optical-bay envelope open
wet/dry separator: 3 mm below printed well bottoms
objective keepout: 28 mm diameter
center mark: 2 mm through-reference at well-field center
crosshair: 18 mm x/y reference
objective reference zones: 4x / 10x / 20x placeholders
```

These are not optical holes yet. They are physical planning marks for checking
where an objective, folded mirror path, or bay envelope would sit relative to the
well field and OT-2 deck slot.

## Print QC Features

The base includes small calibration features that do not affect the OT-2
interaction test:

```text
guide-hole test diameters: 3.0 / 3.5 / 4.0 / 4.5 mm
guide-hole test location: exposed right-side base lane, not under the plate cap
Z-step blocks: 1 / 2 / 3 mm above base top
mat-patch corner marks: shallow alignment dots on the cassette pocket
```

Use these after printing to decide whether the PLA profile over- or
under-sizes holes, and whether we need to regenerate the guide-hole diameter
before printing a second mule.

If the OT-2/P300 has large margin, increase this height to create more room for
the inverted bay. If access is marginal, decrease it before adding optical
constraints.

## Remaining PoC Considerations

These are the remaining gates to treat as first-print evidence, not design
assumptions:

1. **P300 mount and tip type**

   The generated protocol assumes:

   ```text
   pipette: p300_single_gen2
   mount: left
   tiprack: opentrons_96_tiprack_300ul
   ```

   If the physical P300 is mounted on the right side, update params/protocol
   before running. Measure the exact tip length and OD profile for the tips used
   in the OT-2 run.

2. **Guide-hole clearance**

   Active cassette guide holes now sweep by row:

   ```text
   row A: 3.0 mm
   row B: 3.5 mm
   row C: 4.0 mm
   row D: 4.5 mm
   ```

   Columns still sweep offset:

   ```text
   col 1: center
   col 2: +1.0 mm X
   col 3: +1.5 mm X
   col 4: +2.0 mm X
   ```

   This means the cassette tests all 16 diameter/offset combinations. The
   printed cassette is still a rigid PLA guide, not a self-sealing silicone
   slit. Use the exposed base QC holes to understand print sizing, then use the
   cassette rows to test real P300 path clearance. A tighter P20-specific
   cassette can be generated later.

   The cassette now has no printed labels. Keep the mat plane as clean geometry:
   guide holes, pocket relief, and corner marks only. Offset and guide-diameter
   identity should be tracked in the generated labware definition and test
   notes rather than cut into the mat cassette surface.

3. **Mat compatibility with CellVis wells**

   The Cole-Parmer mat is specified as round/deep, but the page does not publish
   plug diameter or protrusion. It may not seat into a CellVis imaging plate. For
   this PoC, treat the mat as a suspended septum patch. Do not assume it is a
   final plate-sealing mat until plug diameter and protrusion are measured.

4. **Offset interpretation**

   The print tests four offset columns. A real mat patch should be tested at one
   global alignment at a time, starting at +1.5 mm X. The +2.0 mm column is a
   boundary test because it leaves only 1.0 mm radial clearance before tip radius
   and lateral error.

5. **Wet dispense behavior**

   A successful dry path does not prove liquid handling. Dye tests should record
   droplet placement, wall wetting, splash, bubble creation, meniscus effects,
   and whether offset dispensing reaches the intended well without crossing into
   the central imaging region. Use the guarded dye protocol in:

   ```text
   opentrons/test_p300_poc_dye.py
   docs/protocols/p300_poc_dye_test.md
   ```

## Platform Height Escalation

The first printed fixture should be interpreted as a physical platform seed, not
only a reach coupon. If P300 high-Z, low-Z dry, and wet dye tests show
comfortable margin at the current 91.0 mm top envelope, the next print should
raise the plate stack to make the inverted bay more realistic.

Do not spend all observed Z margin. Reserve clearance for:

```text
tip length variation
fixture measurement error
printed warping or cap seating error
labware calibration error
future real mat thickness and plug protrusion
operator recovery moves
```

Recommended escalation rule after measuring the first print:

```text
available_margin = measured_safe_margin_above_low_z_target
height_increase = min(30 mm, max(0 mm, available_margin - 10 mm reserve))
next_height_to_mock_plate_top = 80.0 mm + height_increase
```

The first tall variant should keep the 4 x 4 target field and the same
diameter/offset matrix. This isolates the vertical platform question from the
larger-plate coverage question. A later print can then expand laterally toward a
larger chamber envelope after the vertical stack is proven.

6. **Base flatness and tower stability**

   The fixture is tall relative to a one-slot footprint. Rocking, warped corners,
   or a lifted brim edge invalidate low-Z robot motion even if the CAD is correct.
   Base seating is a hard gate. The CAD no longer includes mouse-ear tabs; if
   a slicer brim is used, remove it fully before OT-2 registration.

7. **Support cleanup**

   The current PLA geometry is intended to print without supports. If supports
   are enabled, debris inside guide holes, mock wells, the open headspace, or the
   inverted-bay tunnel changes the evidence. Blocked target classes should be
   marked unavailable rather than forced.

8. **Incubator realism**

   This print has an incubator boundary and wet/dry separator proxy only. It is
   intentionally not sealed, heated, humidified, sterile, or gas-controlled.

9. **Optical-bay realism**

   The underside marks and tunnel are an envelope reference, not an optical
   system. They do not validate objective working distance, vibration, focus
   stability, illumination, or camera/spectrometer packaging.
