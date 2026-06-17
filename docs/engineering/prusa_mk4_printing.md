# Prusa MK4 Printing Procedure

## Current Print Target

```text
outputs/cad/aevum_p300_poc_fixture_base.stl
outputs/cad/aevum_p300_poc_fixture_plate_cap.stl
outputs/cad/aevum_p300_poc_fixture_mat_cassette.stl
```

Do not use `outputs/cad/aevum_p300_poc_fixture.3mf` for the current print. That
file is a stale slicer scene from an earlier geometry revision and may still
show old base features such as the original covered QC-hole locations. The
source of truth is the regenerated STL set above.

Current generated bounds:

```text
functional SBS base footprint: 127.76 x 85.48 mm
base STL footprint: 127.76 x 85.48 mm
base installed height with mock-plate locator pins: 67.70 mm
separate mock plate cap installed height: 25.30 mm
separate cassette thickness: 3.00 mm
installed stack height: 91.00 mm
```

The first PoC is three functional printed solids: a base print, a separate mock
plate cap with integrated mat-cassette posts, and a separate flat mat cassette.
Coarse labels are cut into these same parts. This avoids slicer supports in the
wells, headspace, and optical-bay envelope while preserving the installed stack
height and access geometry.

The base STL no longer includes sacrificial mouse-ear adhesion tabs. If extra
adhesion is needed, use a slicer brim and remove the brim before OT-2 use.

The raised mock plate stack uses the CellVis P96-1.5H-N dimensions, with the
emulated plate occupying z = 65.70-80.00 mm and the cell-plane/well-bottom at
z = 67.60 mm.

The current print geometry is open above the emulated plate:

```text
continuous sidewalls: disabled
top guide/mat plane: separate flat cassette print
mock plate: separate flat cap print
base support: plate-cap locator posts only
plate-cap support: integrated cassette towers and keyed cassette locator pins
under-plate support: no lattice, no continuous optical-bay tunnel walls
air gap: retained between emulated plate top and installed cassette
cassette/chamber collision envelope: retained by plate-cap posts plus installed cassette
well visibility: preserved when cassette is removed
mat entry points: offset by column in the cassette per CAD params
integrated labels: coarse cut labels on non-contact surfaces
axis arrows: +X and +Y cut into the base top near the origin corner
physical marks: guide-hole matrix, fiducial holes, QC coupons, locator keying
human labels: already integrated; marker/tape only for temporary annotations
```

For the first 4 x 4 PoC, base fiducials are intentionally in exposed base
lanes, not under the installed plate cap. Treat them as assembled-fixture
registration witnesses, not well labels.

Small CAD text is not an acceptance feature. The first PLA print fused the text
gaps; the current CAD uses coarse integrated cut labels plus geometry evidence.

## Open In PrusaSlicer

From Finder, open:

```text
outputs/cad/aevum_p300_poc_fixture_base.stl
outputs/cad/aevum_p300_poc_fixture_plate_cap.stl
outputs/cad/aevum_p300_poc_fixture_mat_cassette.stl
```

or from the project root, open one print target at a time:

```bash
open -a "/Applications/Original Prusa Drivers/PrusaSlicer.app" \
  outputs/cad/aevum_p300_poc_fixture_base.stl

open -a "/Applications/Original Prusa Drivers/PrusaSlicer.app" \
  outputs/cad/aevum_p300_poc_fixture_plate_cap.stl

open -a "/Applications/Original Prusa Drivers/PrusaSlicer.app" \
  outputs/cad/aevum_p300_poc_fixture_mat_cassette.stl
```

If multiple STLs are loaded into one PrusaSlicer plate, arrange them manually before
slicing. Their native CAD coordinates are meaningful for assembly inspection,
not for automatic bed layout.

## Recommended PLA Print Settings

Printer:

```text
Original Prusa MK4
0.4 mm default nozzle
```

Filament:

```text
PLA or PLA+
```

This first print is a geometry mule. PLA is appropriate because the hard
requirements are low warp, clean guide features, fast iteration, and enough
stiffness for dry and dye interaction tests. It is not a final incubator
material.

Print profile:

```text
0.20 mm STRUCTURAL or 0.20 mm QUALITY
```

Starting profile:

```text
nozzle first layer: 215 deg C
nozzle other layers: 205-210 deg C
bed first layer: 60 deg C
bed other layers: 55-60 deg C

first layer speed: 15 mm/s
external perimeters: 30 mm/s
perimeters: 45 mm/s
small perimeters: 25 mm/s
infill: 60 mm/s
solid infill: 45 mm/s
top solid infill: 35 mm/s
bridges: 20-25 mm/s
travel: 180-200 mm/s

fan disabled first layers: 2-3
fan after early layers: 100%
bridge fan: 100%

retraction: use PrusaSlicer PLA default
Z hop: 0.0 mm unless collision risk requires it
avoid crossing perimeters: enabled if available
```

Strength and dimensional settings:

```text
perimeters: 3
top solid layers: 5
bottom solid layers: 5
infill: 15%
infill pattern: gyroid or cubic
elephant-foot compensation: 0.20 mm
```

## Adhesion / Warp Control

PLA should be substantially easier than PETG-GF for this part. Still treat base
flatness as a robot-safety requirement.

```text
sheet: smooth PEI preferred for PLA; satin is also acceptable
sheet prep: wash with dish soap/warm water, dry, avoid touching print area
brim: outer brim 5-8 mm if needed for the base
brim separation: 0.10 mm
CAD mouse-ear tabs: disabled
drafts: avoid direct fan/AC during the print
removal: let bed cool before removing the part
```

If a corner or brim lifts, stop early. Do not wait until the tower is tall enough
for nozzle contact to pull the whole part loose.

After removal and brim cleanup:

```text
place the fixture on a known-flat surface
press each corner lightly
check for rocking
check corner gaps with paper or feeler gauge if available
reject for OT-2 motion if rocking is visible or repeatable
```

Do not clamp, tape, or force a warped base flat on the OT-2. That stores stress
in the part and makes the Z datum unstable.

## Supports

The current CAD parts are intended to slice with supports off:

```text
sidewalls removed
under-plate sidewall rails removed
continuous top guide plate moved to a separate flat cassette
mock wells moved to a separate flat plate cap
base has no plate slab or continuous tunnel wall under the mock wells
headspace remains support-free
plate cap prints flat on the bed
cassette prints flat on the bed
integrated labels are cut into supported faces/shelves
```

Recommended order:

1. Slice with supports off and inspect the preview.
2. Confirm the base has no generated support in mock wells or headspace.
3. Confirm the plate cap is flat on the bed and mock wells are clean vertical
   features.
4. Confirm the cassette is flat on the bed and all guide holes are open.
5. Confirm there is no tiny CAD text.
6. Confirm integrated labels slice as coarse cuts, not support structures.
7. Confirm fiducial holes, locator pins, QC holes, and objective-reference cuts
   are clean and do not merge into adjacent features.
8. If PrusaSlicer still reports unstable features, inspect the exact layer before
   enabling supports.
9. If supports are unavoidable, use snug/normal supports and blockers so no
   support material enters the emulated headspace or mock wells.

Do not accept blocked guide holes, support debris in mock wells, or deformed
cassette locator cutouts.

## Pre-Print Checklist

1. Regenerate outputs:

   ```bash
   uv run python scripts/generate_all.py
   ```

2. Confirm bounds:

   ```bash
   uv run python cad/view_p300_poc_fixture.py
   ```

3. Open STL in PrusaSlicer.
4. Confirm model is base-down and centered.
5. Slice with supports off first.
6. Inspect plate-cap locator posts and pins on the base.
7. Inspect mock wells plus mat-cassette posts/pins on the plate cap.
8. Inspect the cassette guide holes.
9. Confirm the base has no material spanning across the headspace over the mock
   wells.
10. Add marker/tape only for temporary annotations if needed.
11. Export G-code for the MK4.

## After Printing

Measure and record:

- overall X/Y/Z bounds,
- bottom-side inverted-bay reference recess,
- objective keepout/center mark position,
- exposed print-QC hole diameters and Z-step heights,
- plate-cap fit on the locator pins,
- guide-hole diameters in each printed cassette row,
- mock-well diameter,
- mock-well depth,
- cassette fit on the locator pins,
- integrated label legibility and any temporary marker/tape annotations,
- whether the base sits flat on the OT-2 deck,
- whether any guide holes are stringy or partially blocked.

Use:

```text
docs/engineering/measurement_template.md
```

for the measurement log.
