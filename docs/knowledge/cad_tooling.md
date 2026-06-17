# CAD Tooling

## Decision

Use CadQuery as the primary CAD generator.

Blender may be used for visualization, screenshots, or mesh inspection, but it is
not the source of truth for mechanical dimensions.

## Rationale

For this project, the CAD system must be:

- scriptable by an agent,
- deterministic,
- parametric,
- able to export STL for printing,
- able to export STEP for later machined parts,
- easy to keep synchronized with OT-2 labware JSON.

CadQuery satisfies those constraints because models are Python source code and can
share parameters with the protocol/labware generators.

## Current Local Install

The project uses uv with a local Python 3.11 virtual environment.

```bash
uv sync --python 3.11 --extra dev
uv run python -c "import cadquery as cq; print(cq.__version__)"
```

Confirmed local version:

```text
cadquery 2.7.0
```

## Sources

- CadQuery documentation: https://cadquery.readthedocs.io/
- CadQuery installation: https://cadquery.readthedocs.io/en/stable/installation.html
- Blender 3D Print Toolbox: https://docs.blender.org/manual/en/latest/addons/mesh/3d_print_toolbox.html
- Blender Python API: https://docs.blender.org/api/current/

