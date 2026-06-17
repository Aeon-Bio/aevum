from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aevum_cad.params import well_center, well_name


def build_labware_definition(params: dict[str, Any]) -> dict[str, Any]:
    base = params["base"]
    stack = params["raised_stack"]
    wells = params["mock_wells"]
    mat = params["mat_plane"]
    meta = params["labware"]

    mat_z = stack["height_to_mock_plate_top"] + mat["height_above_mock_plate_top"]
    fixture_top_z = mat_z + mat["frame_thickness"]
    plate_bottom_z = stack["height_to_mock_plate_top"] - wells["plate_height_z"]
    well_z = plate_bottom_z + wells["bottom_height"] + wells["coverslip_thickness"]
    well_depth = stack["height_to_mock_plate_top"] - well_z

    ordering: list[list[str]] = []
    well_defs: dict[str, Any] = {}

    for col in range(wells["columns"]):
        col_names = []
        for row in range(wells["rows"]):
            name = well_name(row, col)
            x, y = well_center(params, row, col)
            col_names.append(name)
            well_defs[name] = {
                "depth": well_depth,
                "totalLiquidVolume": meta["well_total_liquid_volume"],
                "shape": meta["well_shape"],
                "diameter": wells.get("upper_diameter_mm", wells["diameter"]),
                "x": x,
                "y": y,
                "z": well_z,
            }
        ordering.append(col_names)

    return {
        "ordering": ordering,
        "brand": {"brand": "Aevum", "brandId": ["aevum"]},
        "metadata": {
            "displayName": meta["display_name"],
            "displayCategory": "wellPlate",
            "displayVolumeUnits": "\u00b5L",
            "tags": ["fixture", "p300", "poc"],
        },
        "dimensions": {
            "xDimension": base["length_x"],
            "yDimension": base["width_y"],
            "zDimension": fixture_top_z,
        },
        "wells": well_defs,
        "groups": [
            {
                "metadata": {
                    "displayName": meta["display_name"],
                    "displayCategory": "wellPlate",
                    "wellBottomShape": "flat",
                },
                "wells": list(well_defs.keys()),
                "brand": {"brand": "Aevum", "brandId": ["aevum"]},
            }
        ],
        "parameters": {
            "format": "96Standard",
            "isTiprack": False,
            "isMagneticModuleCompatible": False,
            "loadName": meta["load_name"],
        },
        "namespace": meta["namespace"],
        "version": meta["version"],
        "schemaVersion": 2,
        "cornerOffsetFromSlot": {"x": 0, "y": 0, "z": 0},
    }


def export_labware(params: dict[str, Any], out_dir: str | Path) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = build_labware_definition(params)
    path = out / f"{params['labware']['load_name']}.json"
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path
