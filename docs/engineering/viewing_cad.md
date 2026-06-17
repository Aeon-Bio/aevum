# Viewing CAD

## Preferred Interactive View

Use CQ-Editor and open:

```text
cad/view_p300_poc_fixture.py
```

For the one-row coupon, open:

```text
cad/view_one_row_coupon.py
```

Optional one-row review flags:

```bash
uv run python cad/view_one_row_coupon.py --view-mode exploded
uv run python cad/view_one_row_coupon.py --show-flow-adapters
uv run python cad/view_one_row_coupon.py --show-validation-tools
uv run python cad/view_one_row_coupon.py --show-latch-demo
AEVUM_ROW_COUPON_SHOW_LATCH_DEMO=1 bash scripts/open_cq_editor.sh cad/view_one_row_coupon.py
```

The P300 file rebuilds the fixture from:

```text
cad/p300_poc_fixture.params.json
```

and calls `show_object(...)`, which CQ-Editor provides in its runtime.

## Smoke Test Without A GUI

From the project root:

```bash
uv run python cad/view_p300_poc_fixture.py
```

Expected output:

```text
aevum_p300_poc_fixture
base: bounds x=127.76 y=85.48 z=67.70 mm
plate cap installed: bounds x=70.00 y=70.00 z=25.30 mm
cassette installed: bounds x=70.00 y=70.00 z=3.00 mm
assembly: bounds x=127.76 y=85.48 z=91.00 mm
Open this file in CQ-Editor to view it interactively.
```

## Generated Print/Machining Artifacts

Regenerate outputs:

```bash
uv run python scripts/generate_all.py
```

Outputs:

```text
outputs/cad/aevum_p300_poc_fixture_base.stl
outputs/cad/aevum_p300_poc_fixture_base.step
outputs/cad/aevum_p300_poc_fixture_plate_cap.stl
outputs/cad/aevum_p300_poc_fixture_plate_cap.step
outputs/cad/aevum_p300_poc_fixture_mat_cassette.stl
outputs/cad/aevum_p300_poc_fixture_mat_cassette.step
outputs/cad/aevum_p300_poc_fixture_assembly.step
outputs/labware/aevum_p300_poc_fixture.json
```

Use the STLs for slicing. Use the STEP files for CAD exchange or later
machining work. The assembly STEP is for inspection only; print the base, plate
cap, and cassette as separate jobs or separate objects. Labels are integrated
into those parts.

## CQ-Editor Notes

CQ-Editor is the CadQuery GUI. CadQuery's documentation describes it as the
preferred GUI for interactively editing and inspecting CadQuery scripts.

On macOS, the easiest path is the packaged CQ-Editor download from CadQuery. The
project script is self-contained enough to load from CQ-Editor because it adds the
local `src/` folder to `sys.path` before importing the project generator.

## Local Install

For this workspace, CQ-Editor is installed locally under:

```text
tools/cq-editor/CQ-editor
```

This folder is git-ignored because it contains the downloaded GUI binary.

Launch it from the project root:

```bash
bash scripts/open_cq_editor.sh
```

The launcher sets:

```text
PYINSTALLER_SUPPRESS_SPLASH_SCREEN=1
```

This avoids the packaged CQ-Editor/PyInstaller splash-screen crash on macOS:

```text
KeyError: '_PYI_SPLASH_IPC'
```

Sources:

- CadQuery downloads: https://cadquery.github.io/downloads
- CadQuery installation docs: https://cadquery.readthedocs.io/en/stable/installation.html
- PyInstaller splash-screen notes: https://pyinstaller.org/en/latest/usage.html#splash-screen-experimental
