# Row Coupon Consumable And Puncture Validation

## Purpose

This protocol closes the first physical evidence loop for RH10/RH11: real COTS
plate/mat fit and liquid-handler puncture behavior.

The CAD now provides one required first-print gauge and one viewer-only review
aid:

```text
outputs/cad/aevum_one_row_coupon_validation_consumable_metrology_gauge.step
cad/view_one_row_coupon.py --show-validation-tools
```

The gauge is a required printable validation tool for Gate 5 plate/mat lot-fit
evidence. The pipette puncture swept path is a validation check in the viewer,
not a production part.

## Consumables

```text
Plate: CellVis P96-1.5H-N
Mat: Cole-Parmer EW-12920-06 / 1292006 round pre-slit silicone mat
```

The one-row coupon now uses the persisted CellVis published plate footprint for
the CAD plate body. The Cole-Parmer mat plug, slit, seated height, and wet-swell
values are still placeholders until measured.

## Measurement Record

Create the run record under:

```text
data/measurements/YYYY-MM-DD_row_coupon_consumable_puncture.md
```

Record at minimum:

| Item | Tool | Gate |
|---|---|---|
| Mat sheet thickness | calipers | update params if stack height changes |
| Plug diameter | calipers/microscope | fits plate well without bunching |
| Plug protrusion below sheet | calipers/depth gauge | does not bottom out on well geometry |
| Slit length and opening behavior | microscope | admits tip without tearing |
| Seated mat height dry | calipers | lid/window clearance still valid |
| Seated mat height after humid/wet exposure | calipers | no swelling that blocks service |
| Plate underside support contacts | visual/calipers | locator rails do not hit glass/recess |
| Plate lateral shift after puncture | camera/calipers | provisional target <= 0.25 mm |

Do not promote a new plate X/Y footprint unless the published profile fails a
real fit check. Promote mat dimensions once measured because the current mat
geometry is explicitly placeholder-gated.

## Puncture Test

Use water or dye before biology.

1. Seat one CellVis plate and one Cole-Parmer mat in the support frame.
2. Photograph or measure plate/mat lateral datum positions.
3. Puncture A1, A12, H1, H12, and four center wells with the intended OT-2
   pipette/tip.
4. Repeat one representative well for at least the configured minimum cycle
   count.
5. Re-measure plate and mat position.
6. Inspect slit tearing, mat lift, plug displacement, leakage, and tip damage.
7. Run a simple dispense/aspirate dye check through the mat.

The RH11 claim remains blocked if the mat shifts, the plate moves, the tip
deflects into the slit wall, reseal is poor enough to leak, or liquid-handling
behavior is visibly biased by the mat.
