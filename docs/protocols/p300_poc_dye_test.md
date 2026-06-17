# P300 PoC Dye Test

## Purpose

Use water plus visible dye to test whether the printed fixture can handle wet
P300 access after dry motion has already passed.

This is not a live-cell, sterile, incubated, or gas-controlled test. It is a
mechanical/liquid-handling evidence run.

## Files

Protocol scaffold:

```text
opentrons/test_p300_poc_dye.py
```

Generated fixture labware:

```text
outputs/labware/aevum_p300_poc_fixture.json
```

## Default Assumptions

```text
pipette: p300_single_gen2
mount: left
tiprack: opentrons_96_tiprack_300ul in slot 2
fixture: aevum_p300_poc_fixture in slot 1
dye source: nest_12_reservoir_15ml in slot 3, well A1
dye volume: 5 uL per target
first wet targets: C1 center, C2 +1.0 mm X, C3 +1.5 mm X
first wet guide-hole diameter: row C = 4.0 mm
boundary targets: +2.0 mm column and row D 4.5 mm large-clearance row,
excluded by default
```

Edit constants in `opentrons/test_p300_poc_dye.py` if the physical deck layout
differs.

## Preconditions

Do not run this protocol until:

1. The fixture has passed print QC.
2. The fixture is registered in the OT-2 slot.
3. Dry high-Z and low-Z moves have passed for the target class being tested.
4. The active guide holes and mock wells are clear of support debris.
5. The base does not rock in the deck slot.
6. A structured measurement session is open under `data/measurements/`.

The protocol fails closed until these are manually set:

```python
ALLOW_MANUAL_DYE_RUN = True
DRY_TARGET_CLASSES_VERIFIED = True
REGISTERED_FIXTURE_OFFSET_MM = (x, y, z)
```

## Test Order

Run wet tests in this order:

1. No mat, dry fixture, empty mock wells.
2. No mat, mock wells prefilled with a small amount of water.
3. Suspended Cole-Parmer mat patch aligned to +1.5 mm X, only after no-mat wet
   tests behave.
4. Do not test the +2.0 mm boundary target until center, +1.0, and +1.5 mm pass.
5. Treat row A/B/C/D as different guide-hole diameter evidence. A successful
   row C wet result does not prove row A or B clearance.

## What To Record

Record:

- target well and offset,
- dispense volume,
- dispense Z,
- whether the tip scraped the guide hole, mat, or well wall,
- droplet location,
- splash,
- bubble formation,
- wall wetting,
- whether liquid reaches the central imaging region,
- whether dye appears in the wrong well/headspace,
- camera evidence before and after each dispense.

## Failure Conditions

Stop the wet run if any of these occur:

- tip bends, scrapes, or visibly deflects,
- fixture shifts or rocks,
- guide hole catches the tip,
- dye bridges to a neighboring feature,
- dye exits the mock well or enters the inverted-bay tunnel,
- +1.5 mm target approaches the wall too closely,
- camera evidence is missing when required.

## Interpretation

A successful dye run means:

```text
the printed geometry supports low-volume aqueous dosing into selected mock wells
under the tested offset and Z conditions
```

It does not mean:

```text
the final incubator is sealed
the mat is sterile-compatible
CO2/RH recovery is acceptable
the same geometry is safe for live cells
the optical bay is validated
```
