# Licensing

Aevum is published under two licences, split by what the material is.

## Hardware design source — CERN-OHL-S-2.0

The CERN Open Hardware Licence Version 2, Strongly Reciprocal
([`LICENSE-HARDWARE`](LICENSE-HARDWARE), SPDX `CERN-OHL-S-2.0`) covers the
hardware design source: everything needed to Make the instrument.

- `cad/` — CadQuery parameter files and viewer scripts
- `src/aevum_cad/` — the CadQuery generators (these are design source in the
  CERN-OHL-S sense even though they are Python)
- `outputs/cad/` and any generated STL, STEP, drawings, or labware definitions
- `docs/engineering/` — dimensions, coordinate systems, tolerances, QC gates,
  power section, sensor PCB
- `docs/protocols/` — physical registration and run procedures
- `data/measurements/` — measured plate, mat, tip, and robot data

Strong reciprocity means: you may build, modify, and sell hardware from this
source, but if you convey a modified design or a product made from it, you must
make the complete modified source available under the same licence.

## Control, profile, and analysis code — Apache-2.0

The Apache License, Version 2.0 ([`LICENSE-CODE`](LICENSE-CODE), SPDX
`Apache-2.0`) covers the software that is not hardware design source:

- `src/aevum_ot2_profile/` — the fixture manifest and target-policy profile
  consumed by [`ot2-harness`](https://github.com/Aeon-Bio/ot2-harness)
- `src/aevum_smis/`
- `opentrons/` — OT-2 protocol scaffolds
- `scripts/`, `tests/`

This matches the licence of `ot2-harness` itself, so the Aevum profile and the
harness compose without licence friction.

## Everything else

`docs/knowledge/` and other prose that is neither design source nor code is
covered by CERN-OHL-S-2.0 as Notices and documentation accompanying the design.

## Copyright

Copyright 2026 Aeon Bio. Third-party components (Opentrons labware
definitions, CellVis plate geometry, Cole-Parmer mat data, COTS parts) remain
under their own terms and are Available Components under CERN-OHL-S section 1.7.

SPDX-License-Identifier: CERN-OHL-S-2.0 AND Apache-2.0
