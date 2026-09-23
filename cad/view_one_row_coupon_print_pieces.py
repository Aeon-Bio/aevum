# ruff: noqa: E402, F821
"""Inspect the active one-row final print-piece queue beside the intact assembly.

Open this file directly in CQ-Editor.  The left-hand model is the installed
assembly.  The right-hand kit contains the exact printed-polymer artifacts in
the final first-print queue: bed-fit artifacts remain unchanged, and oversized
structural bodies are shown as deterministic printable pieces.

Running the file with plain Python prints the same inventory as a smoke test.
"""

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import aevum_cad.params as params_module
import aevum_cad.row_coupon as row_coupon_module

params_module = importlib.reload(params_module)
row_coupon_module = importlib.reload(row_coupon_module)

DEFAULT_PARAMS = ROOT / "cad" / "one_row_coupon.params.json"


def _queue_models(params):
    """Return the final printed-polymer models and their planner rows."""

    realization = row_coupon_module.realize_row_coupon_final_print_pieces(params)
    realization.require_printable()
    return realization.pieces, {
        str(row["name"]): row for row in realization.plan
    }


def _pair_layout(params, final_models, plan_by_name):
    """Lay queue artifacts out as a compact, readable print kit."""

    seam_gap = 10.0
    groups = []
    source_order = []
    for row in plan_by_name.values():
        source = str(row["source_artifact"])
        if source not in source_order:
            source_order.append(source)
    for source in source_order:
        source_rows = [
            row
            for row in plan_by_name.values()
            if str(row["source_artifact"]) == source
        ]
        group = []
        for row in sorted(source_rows, key=lambda entry: int(entry["piece_index"])):
            name = str(row["name"])
            model = final_models[name]
            if int(row["piece_count"]) > 1:
                offset_y = (
                    -seam_gap / 2
                    if int(row["piece_index"]) == 1
                    else seam_gap / 2
                )
                model = model.translate((0, offset_y, 0)).rotate(
                    (0, 0, 0), (0, 0, 1), -90
                )
            group.append((name, model))
        groups.append(tuple(group))

    bounds = []
    for group in groups:
        boxes = [model.val().BoundingBox() for _name, model in group]
        bounds.append(
            (
                min(bb.xmin for bb in boxes),
                max(bb.xmax for bb in boxes),
                min(bb.ymin for bb in boxes),
                max(bb.ymax for bb in boxes),
                min(bb.zmin for bb in boxes),
            )
        )

    cell_width = max(xmax - xmin for xmin, xmax, _ymin, _ymax, _zmin in bounds) + 24.0
    cell_height = max(ymax - ymin for _xmin, _xmax, ymin, ymax, _zmin in bounds) + 24.0
    columns = 2
    kit_origin_x = 230.0
    laid_out = {}
    for index, (group, bound) in enumerate(zip(groups, bounds, strict=True)):
        xmin, _xmax, ymin, _ymax, zmin = bound
        column = index % columns
        row = index // columns
        offset = (
            kit_origin_x + column * cell_width - xmin,
            row * cell_height - ymin,
            -zmin,
        )
        for name, model in group:
            laid_out[name] = model.translate(offset)
    return laid_out


params = params_module.load_params(DEFAULT_PARAMS)
final_models, plan_by_name = _queue_models(params)
print_pieces = _pair_layout(params, final_models, plan_by_name)
assembly_parts = row_coupon_module.build_row_coupon_installed_parts(params)

ASSEMBLY_OPTIONS = {
    "deck_pods": {"alpha": 0.76, "color": (0.55, 0.58, 0.62)},
    "plate_support_frame": {"alpha": 0.78, "color": (0.75, 0.78, 0.82)},
    "lower_gasket": {"alpha": 0.72, "color": (0.36, 0.78, 0.50)},
    "wet_chamber_frame": {"alpha": 0.36, "color": (0.12, 0.48, 0.45)},
    "cots_microplates": {"alpha": 0.62, "color": (0.25, 0.70, 0.95)},
    "cots_septum_mats": {"alpha": 0.70, "color": (0.75, 0.35, 0.95)},
    "upper_gasket": {"alpha": 0.76, "color": (0.40, 0.80, 0.45)},
    "lid_manifold_shell": {"alpha": 0.34, "color": (0.95, 0.68, 0.25)},
    "lid_cover": {"alpha": 0.50, "color": (0.95, 0.55, 0.18)},
    "printed_wedge_locks": {"alpha": 0.86, "color": (0.90, 0.20, 0.16)},
}
DEFAULT_ASSEMBLY_OPTION = {"alpha": 0.82, "color": (0.24, 0.28, 0.32)}

PRINT_COLORS = {
    "deck_pods": (0.55, 0.58, 0.62),
    "plate_support_frame": (0.75, 0.78, 0.82),
    "lower_harness_cover": (0.50, 0.52, 0.56),
    "wet_chamber_frame": (0.12, 0.58, 0.52),
    "lid_manifold_shell": (0.95, 0.68, 0.25),
    "lid_harness_cover": (0.72, 0.50, 0.24),
    "lid_cover": (0.95, 0.55, 0.18),
    "printed_gas_pcb_keeper_doors": (0.82, 0.48, 0.18),
    "printed_wedge_locks": (0.90, 0.20, 0.16),
    "printed_lower_sensor_connector_shroud": (0.45, 0.47, 0.50),
    "printed_lid_sensor_connector_shrouds": (0.72, 0.50, 0.24),
    "printed_sample_relief_cap": (0.18, 0.55, 0.92),
}

SMALL_SERVICE_INSTALLED_PARTS = frozenset(
    {
        "printed_gas_pcb_keeper_doors",
        "printed_wedge_locks",
        "printed_lower_sensor_connector_shroud",
        "printed_lid_sensor_connector_shrouds",
        "printed_sample_relief_cap",
    }
)


def _print_queue_summary():
    """Explain the physical meaning of the CQ object-tree groups."""

    structural_sources = sorted(
        {
            str(row["source_artifact"])
            for row in plan_by_name.values()
            if row["action"] == "structural_split"
        }
    )
    small_service_names = [
        name
        for name, row in plan_by_name.items()
        if str(row["installed_part"]) in SMALL_SERVICE_INSTALLED_PARTS
    ]
    larger_whole_names = [
        name
        for name, row in plan_by_name.items()
        if int(row["piece_count"]) == 1
        and str(row["installed_part"]) not in SMALL_SERVICE_INSTALLED_PARTS
    ]
    print(f"{params['name']}: installed assembly + canonical rigid print kit")
    print(
        f"PRINT_STRUCTURAL: {len(structural_sources)} sources / "
        f"{sum(int(row['piece_count']) > 1 for row in plan_by_name.values())} pieces"
    )
    print(f"PRINT_WHOLE: {len(larger_whole_names)} larger whole pieces")
    print(f"PRINT_SERVICE: {len(small_service_names)} small removable pieces")
    print("Structural pairs: " + ", ".join(structural_sources))
    print("Small service pieces: " + ", ".join(small_service_names))


def _print_options(name):
    source = str(plan_by_name[name]["installed_part"])
    alpha = 0.96 if int(plan_by_name[name]["piece_index"]) == 1 else 0.76
    return {"alpha": alpha, "color": PRINT_COLORS[source]}


def _print_tree_name(name):
    row = plan_by_name[name]
    if str(row["installed_part"]) in SMALL_SERVICE_INSTALLED_PARTS:
        group = "SERVICE"
    elif int(row["piece_count"]) > 1:
        group = "STRUCTURAL"
    else:
        group = "WHOLE"
    return f"PRINT_{group}_{name}"


_print_queue_summary()


try:
    _show_object = show_object  # type: ignore[name-defined]  # noqa: F821
except NameError:
    _show_object = None

if _show_object is not None:
    for name, model in assembly_parts.items():
        _show_object(
            model,
            name=f"ASSEMBLY_{name}",
            options=ASSEMBLY_OPTIONS.get(name, DEFAULT_ASSEMBLY_OPTION),
        )
    for name, model in print_pieces.items():
        _show_object(
            model,
            name=_print_tree_name(name),
            options=_print_options(name),
        )
else:
    print(f"assembly components: {len(assembly_parts)}")
    print(f"queued printed artifacts: {len(print_pieces)}")
    for name, model in print_pieces.items():
        bb = model.val().BoundingBox()
        print(f"{name}: x={bb.xlen:.2f} y={bb.ylen:.2f} z={bb.zlen:.2f} mm")
    print("Open this file in CQ-Editor to inspect the models interactively.")
