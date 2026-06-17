# Aevum

Engineering workspace for a tileable OT-2 plate-mode live-cell platform with
registered glass-bottom plate tiles, row-shared controlled headspace, and a
shared dry inverted observation bay for a moving sensor-suite module.

The current printed artifact is a first physical proof of concept for the
raised plate interaction stack:

- Opentrons OT-2 with P300 Gen2 attached.
- Screwless PLA interaction mule.
- Separate raised mock CellVis plate cap.
- Cole-Parmer pre-slit silicone round-well sealing mat held above the mock wells.
- Off-axis pipette access geometry.
- CAD and OT-2 labware targets generated from the same parameters.

## Project Structure

```text
cad/                  Source parameter files for generated CAD
src/aevum_cad/        Python/CadQuery generators
opentrons/            OT-2 protocol scaffolds
docs/knowledge/       Design context and accumulated decisions
docs/engineering/     Dimensions, coordinate systems, validation plans
docs/protocols/       OT-2 registration and run procedures
data/measurements/    Measured plate, mat, tip, and robot data
outputs/              Generated CAD, labware, protocols, and reports
scripts/              Command-line entry points
```

## Local Setup

CadQuery should run in the local project environment rather than the system Python.

```bash
uv sync --python 3.11 --extra dev
```

Generate first PoC artifacts:

```bash
uv run python scripts/generate_all.py
```

Generated artifacts are written under `outputs/`.

Generate the one-row hardware coupon:

```bash
uv run python scripts/generate_row_coupon.py
```

## Viewing CAD

Open this file in CQ-Editor:

```text
cad/view_p300_poc_fixture.py
```

For the one-row coupon, open:

```text
cad/view_one_row_coupon.py
```

Or run a non-GUI smoke test:

```bash
uv run python cad/view_p300_poc_fixture.py
```

See [docs/engineering/viewing_cad.md](docs/engineering/viewing_cad.md).

## Printing

The current first-print STLs are:

```text
outputs/cad/aevum_p300_poc_fixture_base.stl
outputs/cad/aevum_p300_poc_fixture_plate_cap.stl
outputs/cad/aevum_p300_poc_fixture_mat_cassette.stl
```

Prusa MK4 print notes are in
[docs/engineering/prusa_mk4_printing.md](docs/engineering/prusa_mk4_printing.md).
