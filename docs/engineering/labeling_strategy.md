# Labeling Strategy

## Print Result

The first PLA print made the small CAD text illegible. The failure mode is
expected for FDM:

```text
text height: 1.8-2.2 mm
relief / engraving: 0.25 mm
nozzle: 0.4 mm
material: PLA
result: counters and gaps fuse
```

The fixture should not depend on tiny printed text for safety, registration, or
target-class promotion.

## Current Rule

Generated fixtures carry coarse integrated labels only. They are cut into
non-critical faces and shelves of the generated fixture parts: base, plate cap,
and mat cassette. The labels are never placed in guide holes, locator seats,
mock wells, mat pockets, or the optical-bay opening.

Use geometry as the primary reference:

```text
fiducial holes
guide-hole matrix
diameter coupon holes
Z-step coupon blocks
keyed locator pins and cutouts
objective keepout and crosshair cuts
mat-patch corner marks
```

Human-readable labels are integrated into the printable parts:

```text
base front side: FRONT SLOT 1
base top near origin: +X and +Y direction arrows
plate cap front side: PLATE A1, rotated where that print's install orientation requires it
plate cap top margins: A1 and final well label
mat cassette top shelves: MAT, offset, and guide-diameter labels where there is clearance
```

The labels use coarse lettering and about 0.45 mm cut depth. They are operator
aids, not robot datums.

## If Text Returns

Text belongs only as coarse integrated geometry:

```text
minimum text height: 5-6 mm
minimum relief or engraving: 0.6-0.8 mm
avoid thin fonts
avoid negative/engraved microtext on top faces
prefer large cut or raised lettering on non-contact surfaces
verify slicer preview before printing
```

Text is acceptable as an operator convenience. It must not be the only evidence
that a target, fiducial, or deck slot is correct.
