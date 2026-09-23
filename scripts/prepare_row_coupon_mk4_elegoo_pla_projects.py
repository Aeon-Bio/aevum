from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import struct
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "outputs" / "cad" / "final_print_pieces"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "sliced" / "mk4_elegoo_pla"
DEFAULT_AUTHORITY = ROOT / "docs" / "assembly" / "artifact_authority.json"
DEFAULT_LEDGER = ROOT / "docs" / "assembly" / "printability_ledger.json"
DEFAULT_PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
DEFAULT_PRUSA_SLICER = Path(
    "/Applications/Original Prusa Drivers/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"
)
DEFAULT_DATADIR = Path.home() / "Library" / "Application Support" / "PrusaSlicer"

PRINTER_PROFILE = "Original Prusa MK4 Input Shaper 0.4 nozzle"
MATERIAL_PROFILE = "Generic PLA @PGIS"
BED_X_MM = 250.0
BED_Y_MM = 210.0
BED_MARGIN_MM = 8.0
OBJECT_GAP_MM = 8.0
FILE_PREFIX = "aevum_one_row_coupon_"
PRUSA_SLICER_PROJECT_APPLICATION = "PrusaSlicer-2.9.4"
PACKAGE_MANIFEST = "package_manifest.json"
DECODED_REPORT = "decoded_toolpath_report.json"
LEDGER_SNAPSHOT = "printability_ledger_snapshot.json"
LIBBGCODE_SOURCE_COMMIT = "d4da9073616d70a43c151e8c1d7fbff879d2e08a"
RIGID_BODY_COUNT = 38
EXPORTED_CAD_PATH_COUNT = RIGID_BODY_COUNT * 2
SERVICE_BODY_COUNT = 18
LEGACY_LEDGER_BODY_MIGRATIONS = {
    "printed_wedge_lock_station_06_x_min": "printed_wedge_lock_station_06_x_max",
    "printed_wedge_lock_station_10_x_max": "printed_wedge_lock_station_09_x_max",
    "printed_wedge_lock_station_11_x_max": "printed_wedge_lock_station_09_x_max",
    "printed_wedge_lock_station_12_x_max": "printed_wedge_lock_station_09_x_max",
}
DISPOSITION_RANK = {
    "print-now-test-article": 0,
    "coupon-first": 1,
    "hold": 2,
}


@dataclass(frozen=True)
class Mesh:
    path: Path
    vertices: tuple[tuple[float, float, float], ...]
    triangles: tuple[tuple[int, int, int], ...]
    bounds: tuple[float, float, float, float, float, float]

    @property
    def width(self) -> float:
        return self.bounds[1] - self.bounds[0]

    @property
    def depth(self) -> float:
        return self.bounds[3] - self.bounds[2]


@dataclass(frozen=True)
class PlateSpec:
    name: str
    profile: str
    part_names: tuple[str, ...]
    rotate_z_90_names: tuple[str, ...] = ()
    bed_margin_mm: float = BED_MARGIN_MM
    object_gap_mm: float = OBJECT_GAP_MM


PROFILE_SPECS = {
    "structural": {
        "print_profile": "0.20mm STRUCTURAL @MK4IS 0.4",
        "overrides": (
            "--temperature",
            "205",
            "--first-layer-temperature",
            "210",
            "--bed-temperature",
            "60",
            "--first-layer-bed-temperature",
            "60",
            "--max-print-speed",
            "70",
            "--first-layer-infill-speed",
            "70",
            "--perimeter-speed",
            "70",
            "--infill-speed",
            "70",
            "--solid-infill-speed",
            "70",
            "--top-solid-infill-speed",
            "70",
            "--support-material-speed",
            "70",
            "--perimeters",
            "3",
            "--fill-density",
            "20%",
            "--fill-pattern",
            "gyroid",
            "--support-material",
            "--support-material-auto",
            "--support-material-buildplate-only",
        ),
    },
    "fine_service": {
        "print_profile": "0.15mm STRUCTURAL @MK4IS 0.4",
        "overrides": (
            "--temperature",
            "205",
            "--first-layer-temperature",
            "210",
            "--bed-temperature",
            "60",
            "--first-layer-bed-temperature",
            "60",
            "--max-print-speed",
            "70",
            "--first-layer-infill-speed",
            "70",
            "--perimeter-speed",
            "70",
            "--infill-speed",
            "70",
            "--solid-infill-speed",
            "70",
            "--top-solid-infill-speed",
            "70",
            "--support-material-speed",
            "70",
            "--perimeters",
            "3",
            "--fill-density",
            "30%",
            "--fill-pattern",
            "gyroid",
            "--no-support-material",
            "--brim-width",
            "3",
        ),
    },
    "relief_cap_support_review": {
        "print_profile": "0.15mm STRUCTURAL @MK4IS 0.4",
        "overrides": (
            "--temperature",
            "205",
            "--first-layer-temperature",
            "210",
            "--bed-temperature",
            "60",
            "--first-layer-bed-temperature",
            "60",
            "--max-print-speed",
            "70",
            "--first-layer-infill-speed",
            "70",
            "--perimeter-speed",
            "70",
            "--infill-speed",
            "70",
            "--solid-infill-speed",
            "70",
            "--top-solid-infill-speed",
            "70",
            "--support-material-speed",
            "70",
            "--perimeters",
            "3",
            "--fill-density",
            "30%",
            "--fill-pattern",
            "gyroid",
            "--support-material",
            "--support-material-auto",
            "--support-material-buildplate-only",
            "--brim-width",
            "3",
        ),
    },
    "coupon_support_review": {
        "print_profile": "0.15mm STRUCTURAL @MK4IS 0.4",
        "overrides": (
            "--temperature",
            "205",
            "--first-layer-temperature",
            "210",
            "--bed-temperature",
            "60",
            "--first-layer-bed-temperature",
            "60",
            "--max-print-speed",
            "70",
            "--first-layer-infill-speed",
            "70",
            "--perimeter-speed",
            "70",
            "--infill-speed",
            "70",
            "--solid-infill-speed",
            "70",
            "--top-solid-infill-speed",
            "70",
            "--support-material-speed",
            "70",
            "--perimeters",
            "3",
            "--fill-density",
            "30%",
            "--fill-pattern",
            "gyroid",
            "--support-material",
            "--support-material-auto",
            "--support-material-buildplate-only",
            "--brim-width",
            "3",
        ),
    },
}


def _canonical_name(path: Path) -> str:
    if not path.stem.startswith(FILE_PREFIX):
        raise ValueError(f"unexpected STL filename: {path.name}")
    return path.stem.removeprefix(FILE_PREFIX)


def _plate_specs(
    part_names: set[str],
    disposition_by_body: dict[str, str],
) -> tuple[PlateSpec, ...]:
    lid_cover = sorted(name for name in part_names if name.startswith("lid_cover_piece_"))
    lid_manifold = sorted(
        name for name in part_names if name.startswith("lid_manifold_shell_piece_")
    )
    plate_support = sorted(
        name for name in part_names if name.startswith("plate_support_frame_piece_")
    )
    wet_chamber = sorted(
        name for name in part_names if name.startswith("wet_chamber_frame_piece_")
    )
    large = sorted((*lid_cover, *lid_manifold, *plate_support, *wet_chamber))
    deck = sorted(name for name in part_names if name.startswith("deck_pod_tile_"))
    harness = sorted(
        name
        for name in part_names
        if name.startswith("lower_harness_cover_piece_")
        or name.startswith("lid_harness_cover_")
    )
    service = sorted(name for name in part_names if name.startswith("printed_"))

    relief_cap = "printed_sample_relief_cap"
    lid_shrouds = {
        name
        for name in service
        if name.startswith("printed_lid_sensor_connector_shroud_")
    }
    fine_small = set((*harness, *service)) - {relief_cap, *lid_shrouds}

    expected_dispositions = {
        deck[0]: "hold",
        deck[1]: "print-now-test-article",
        deck[2]: "hold",
        deck[3]: "print-now-test-article",
    }
    actual_dispositions = {
        body_id: disposition_by_body.get(body_id) for body_id in expected_dispositions
    }
    if actual_dispositions != expected_dispositions:
        raise ValueError(
            "deck-pod A2 dispositions changed; packing must be reviewed: "
            f"{actual_dispositions}"
        )

    # Every large half anchors one plate. HOLD pods 1/3 share the compatible
    # structural profile and failure domain with HOLD anchors. PRINT-NOW pods
    # 2/4 share a separate structural plate so a held anchor cannot suppress or
    # contaminate their test-article job. Twenty-three zero-support harness/service
    # bodies remain a separate fine-profile failure domain. The HOLD relief cap
    # gets its own support-review plate because PrusaSlicer detects its canonical
    # orientation as a floating part when supports are disabled. The two
    # coupon-first lid shrouds get a separate support-review failure domain because
    # the locked C1 solids trigger PrusaSlicer's loose-extrusion warning.
    specs = [
        PlateSpec(
            f"01_{lid_cover[0]}",
            "structural",
            (lid_cover[0],),
            rotate_z_90_names=(lid_cover[0],),
        ),
        PlateSpec(
            f"02_{lid_cover[1]}",
            "structural",
            (lid_cover[1],),
            rotate_z_90_names=(lid_cover[1],),
        ),
        PlateSpec(
            f"03_{lid_manifold[0]}",
            "structural",
            (lid_manifold[0],),
            rotate_z_90_names=(lid_manifold[0],),
        ),
        PlateSpec(
            f"04_{lid_manifold[1]}",
            "structural",
            (lid_manifold[1],),
            rotate_z_90_names=(lid_manifold[1],),
        ),
        PlateSpec(
            f"05_{plate_support[0]}_plus_{deck[0]}",
            "structural",
            (plate_support[0], deck[0]),
            rotate_z_90_names=(deck[0],),
            bed_margin_mm=3.0,
            object_gap_mm=6.0,
        ),
        PlateSpec(
            f"06_{plate_support[1]}_plus_{deck[2]}",
            "structural",
            (plate_support[1], deck[2]),
            rotate_z_90_names=(deck[2],),
            bed_margin_mm=3.0,
            object_gap_mm=6.0,
        ),
        PlateSpec(
            f"07_{wet_chamber[0]}",
            "structural",
            (wet_chamber[0],),
            rotate_z_90_names=(wet_chamber[0],),
        ),
        PlateSpec(
            f"08_{wet_chamber[1]}",
            "structural",
            (wet_chamber[1],),
            rotate_z_90_names=(wet_chamber[1],),
        ),
        PlateSpec(
            f"09_{deck[1]}_plus_{deck[3]}",
            "structural",
            (deck[1], deck[3]),
            rotate_z_90_names=(deck[1], deck[3]),
            bed_margin_mm=3.0,
            object_gap_mm=6.0,
        ),
        PlateSpec(
            "10_fine_harness_and_service_parts",
            "fine_service",
            tuple(sorted(fine_small)),
            bed_margin_mm=4.0,
            object_gap_mm=8.0,
        ),
        PlateSpec(
            "11_sample_relief_cap_support_review",
            "relief_cap_support_review",
            (relief_cap,),
            bed_margin_mm=8.0,
            object_gap_mm=8.0,
        ),
        PlateSpec(
            "12_lid_connector_shrouds_support_review",
            "coupon_support_review",
            tuple(sorted(lid_shrouds)),
            bed_margin_mm=8.0,
            object_gap_mm=8.0,
        ),
    ]

    assigned = [name for spec in specs for name in spec.part_names]
    if len(deck) != 4:
        raise ValueError(f"expected four deck pods, found {len(deck)}")
    if len(large) != 8:
        raise ValueError(f"expected eight large structural halves, found {len(large)}")
    if len(harness) != 8:
        raise ValueError(f"expected eight harness-cover halves, found {len(harness)}")
    if len(service) != SERVICE_BODY_COUNT:
        raise ValueError(
            f"expected {SERVICE_BODY_COUNT} service bodies, found {len(service)}"
        )
    if len(assigned) != len(set(assigned)):
        raise ValueError("a printable body was assigned to more than one plate")
    missing = part_names - set(assigned)
    extra = set(assigned) - part_names
    if missing or extra:
        raise ValueError(
            f"plate assignment mismatch: missing={sorted(missing)} extra={sorted(extra)}"
        )
    return tuple(specs)


def _rotate_mesh_z_90(mesh: Mesh) -> Mesh:
    vertices = tuple((-y, x, z) for x, y, z in mesh.vertices)
    xs = [point[0] for point in vertices]
    ys = [point[1] for point in vertices]
    zs = [point[2] for point in vertices]
    return Mesh(
        path=mesh.path,
        vertices=vertices,
        triangles=mesh.triangles,
        bounds=(min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)),
    )


def _meshes_for_spec(spec: PlateSpec, meshes_by_name: dict[str, Mesh]) -> tuple[Mesh, ...]:
    rotated = set(spec.rotate_z_90_names)
    return tuple(
        _rotate_mesh_z_90(meshes_by_name[name]) if name in rotated else meshes_by_name[name]
        for name in spec.part_names
    )


def _read_stl(path: Path) -> Mesh:
    data = path.read_bytes()
    triangles_xyz: list[tuple[tuple[float, float, float], ...]] = []
    if len(data) >= 84:
        triangle_count = struct.unpack_from("<I", data, 80)[0]
        is_binary = len(data) == 84 + triangle_count * 50
    else:
        is_binary = False

    if is_binary:
        for index in range(triangle_count):
            values = struct.unpack_from("<12fH", data, 84 + index * 50)
            coordinates = values[3:12]
            triangles_xyz.append(
                tuple(
                    tuple(float(value) for value in coordinates[offset : offset + 3])
                    for offset in (0, 3, 6)
                )
            )
    else:
        matches = re.findall(
            rb"vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)",
            data,
        )
        if len(matches) % 3:
            raise ValueError(f"invalid ASCII STL vertex count: {path}")
        points = [tuple(float(value) for value in match) for match in matches]
        triangles_xyz = [tuple(points[index : index + 3]) for index in range(0, len(points), 3)]

    vertex_ids: dict[tuple[float, float, float], int] = {}
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for triangle in triangles_xyz:
        indices: list[int] = []
        for point in triangle:
            if point not in vertex_ids:
                vertex_ids[point] = len(vertices)
                vertices.append(point)
            indices.append(vertex_ids[point])
        triangles.append(tuple(indices))

    if not vertices or not triangles:
        raise ValueError(f"empty STL: {path}")
    xs = [point[0] for point in vertices]
    ys = [point[1] for point in vertices]
    zs = [point[2] for point in vertices]
    return Mesh(
        path=path,
        vertices=tuple(vertices),
        triangles=tuple(triangles),
        bounds=(min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)),
    )


def _placements(
    meshes: tuple[Mesh, ...],
    *,
    bed_margin_mm: float = BED_MARGIN_MM,
    object_gap_mm: float = OBJECT_GAP_MM,
) -> tuple[tuple[float, float, float], ...]:
    if len(meshes) == 1:
        mesh = meshes[0]
        if mesh.width > BED_X_MM - 2 * bed_margin_mm:
            raise ValueError(f"{mesh.path.name} is too wide for the selected bed margin")
        if mesh.depth > BED_Y_MM - 2 * bed_margin_mm:
            raise ValueError(f"{mesh.path.name} is too deep for the selected bed margin")
        return (
            (
                BED_X_MM / 2 - (mesh.bounds[0] + mesh.bounds[1]) / 2,
                BED_Y_MM / 2 - (mesh.bounds[2] + mesh.bounds[3]) / 2,
                -mesh.bounds[4],
            ),
        )

    packed: list[tuple[int, float, float, float, float]] = []
    order = sorted(
        range(len(meshes)),
        key=lambda index: (
            -max(meshes[index].width, meshes[index].depth),
            -min(meshes[index].width, meshes[index].depth),
            meshes[index].path.name,
        ),
    )
    for index in order:
        mesh = meshes[index]
        if mesh.width > BED_X_MM - 2 * bed_margin_mm:
            raise ValueError(f"{mesh.path.name} is too wide for the selected bed")
        if mesh.depth > BED_Y_MM - 2 * bed_margin_mm:
            raise ValueError(f"{mesh.path.name} is too deep for the selected bed")

        candidate_xs = {bed_margin_mm}
        candidate_ys = {bed_margin_mm}
        for _, x, y, width, depth in packed:
            candidate_xs.add(x + width + object_gap_mm)
            candidate_ys.add(y + depth + object_gap_mm)

        position: tuple[float, float] | None = None
        for y, x in sorted((y, x) for y in candidate_ys for x in candidate_xs):
            if x + mesh.width > BED_X_MM - bed_margin_mm:
                continue
            if y + mesh.depth > BED_Y_MM - bed_margin_mm:
                continue
            overlaps = any(
                not (
                    x + mesh.width + object_gap_mm <= other_x
                    or other_x + other_width + object_gap_mm <= x
                    or y + mesh.depth + object_gap_mm <= other_y
                    or other_y + other_depth + object_gap_mm <= y
                )
                for _, other_x, other_y, other_width, other_depth in packed
            )
            if not overlaps:
                position = (x, y)
                break
        if position is None:
            raise ValueError(f"plate packing overflow while placing {mesh.path.name}")
        packed.append((index, *position, mesh.width, mesh.depth))

    min_x = min(x for _, x, _, _, _ in packed)
    max_x = max(x + width for _, x, _, width, _ in packed)
    min_y = min(y for _, _, y, _, _ in packed)
    max_y = max(y + depth for _, _, y, _, depth in packed)
    center_dx = BED_X_MM / 2 - (min_x + max_x) / 2
    center_dy = BED_Y_MM / 2 - (min_y + max_y) / 2

    placements: list[tuple[float, float, float] | None] = [None] * len(meshes)
    for index, x, y, _, _ in packed:
        mesh = meshes[index]
        placements[index] = (
            x + center_dx - mesh.bounds[0],
            y + center_dy - mesh.bounds[2],
            -mesh.bounds[4],
        )
    if any(placement is None for placement in placements):
        raise AssertionError("internal packing error: missing placement")
    return tuple(placement for placement in placements if placement is not None)


def _write_3mf(
    path: Path,
    title: str,
    meshes: tuple[Mesh, ...],
    profile_config: bytes,
    *,
    bed_margin_mm: float = BED_MARGIN_MM,
    object_gap_mm: float = OBJECT_GAP_MM,
) -> tuple[tuple[float, float, float], ...]:
    placements = _placements(
        meshes,
        bed_margin_mm=bed_margin_mm,
        object_gap_mm=object_gap_mm,
    )
    embedded_profile_lines = [
        f"; {line.removeprefix('# ')}" if line else ""
        for line in profile_config.decode("utf-8").splitlines()
    ]
    embedded_profile = "\n".join(embedded_profile_lines) + "\n"
    model_config_lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<config>"]
    for object_id, mesh in enumerate(meshes, start=1):
        name = html.escape(_canonical_name(mesh.path), quote=True)
        model_config_lines.extend(
            (
                f' <object id="{object_id}" instances_count="1">',
                f'  <metadata type="object" key="name" value="{name}"/>',
                f'  <volume firstid="0" lastid="{len(mesh.triangles) - 1}">',
                f'   <metadata type="volume" key="name" value="{name}"/>',
                '   <metadata type="volume" key="volume_type" value="ModelPart"/>',
                '   <metadata type="volume" key="matrix" '
                'value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>',
                '   <mesh edges_fixed="0" degenerate_facets="0" facets_removed="0" '
                'facets_reversed="0" backwards_edges="0"/>',
                "  </volume>",
                " </object>",
            )
        )
    model_config_lines.append("</config>")
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""
    relationships = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("Metadata/Slic3r_PE.config", embedded_profile)
        archive.writestr(
            "Metadata/Slic3r_PE_model.config",
            "\n".join(model_config_lines) + "\n",
        )
        with archive.open("3D/3dmodel.model", "w") as model:
            def emit(text: str) -> None:
                model.write(text.encode("utf-8"))

            emit('<?xml version="1.0" encoding="UTF-8"?>\n')
            emit(
                '<model unit="millimeter" xml:lang="en-US" '
                'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
                'xmlns:slic3rpe="http://schemas.slic3r.org/3mf/2017/06">\n'
            )
            emit(' <metadata name="slic3rpe:Version3mf">1</metadata>\n')
            emit(
                f' <metadata name="Application">'
                f"{PRUSA_SLICER_PROJECT_APPLICATION}</metadata>\n"
            )
            emit(f' <metadata name="Title">{html.escape(title)}</metadata>\n <resources>\n')
            for object_id, mesh in enumerate(meshes, start=1):
                name = html.escape(_canonical_name(mesh.path), quote=True)
                emit(
                    f'  <object id="{object_id}" type="model" name="{name}">\n'
                    "   <mesh>\n    <vertices>\n"
                )
                for x, y, z in mesh.vertices:
                    emit(f'     <vertex x="{x:.7g}" y="{y:.7g}" z="{z:.7g}"/>\n')
                emit("    </vertices>\n    <triangles>\n")
                for v1, v2, v3 in mesh.triangles:
                    emit(f'     <triangle v1="{v1}" v2="{v2}" v3="{v3}"/>\n')
                emit("    </triangles>\n   </mesh>\n  </object>\n")
            emit(" </resources>\n <build>\n")
            for object_id, (x, y, z) in enumerate(placements, start=1):
                emit(
                    f'  <item objectid="{object_id}" '
                    f'transform="1 0 0 0 1 0 0 0 1 {x:.7g} {y:.7g} {z:.7g}" printable="1"/>\n'
                )
            emit(" </build>\n</model>\n")
    return placements


def _run(command: list[str]) -> str:
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode:
        detail = "\n".join((result.stderr or result.stdout).strip().splitlines()[-20:])
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return "\n".join(part for part in (result.stdout, result.stderr) if part).strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _portable_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _authority_maps(authority_path: Path) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    authority = json.loads(authority_path.read_text())
    bodies = {
        row["release_body_id"]: row
        for row in authority["release_bodies"]
        if row["body_class"] == "rigid_print_piece"
    }
    if len(bodies) != RIGID_BODY_COUNT:
        raise ValueError(
            "authority must contain "
            f"{RIGID_BODY_COUNT} rigid print pieces, found {len(bodies)}"
        )
    return (
        {body_id: row["source_artifact_id"] for body_id, row in bodies.items()},
        bodies,
    )


def _current_dispositions(ledger_path: Path, body_ids: set[str]) -> dict[str, str]:
    ledger = json.loads(ledger_path.read_text())
    dispositions = {
        row["release_body_id"]: row["disposition"] for row in ledger["bodies"]
    }
    expected_prior_ids = (
        body_ids - set(LEGACY_LEDGER_BODY_MIGRATIONS)
    ) | set(LEGACY_LEDGER_BODY_MIGRATIONS.values())
    disposition_ids = set(dispositions)
    if disposition_ids != body_ids and disposition_ids != expected_prior_ids:
        raise ValueError(
            "A2 ledger body IDs do not match either current rigid-body authority "
            "or the explicit 9-to-12-wedge migration"
        )
    return {
        body_id: dispositions[
            body_id
            if body_id in dispositions
            else LEGACY_LEDGER_BODY_MIGRATIONS[body_id]
        ]
        for body_id in body_ids
    }


def _project_body_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("Metadata/Slic3r_PE_model.config"))
    return [
        next(
            metadata.attrib["value"]
            for metadata in obj.findall("metadata")
            if metadata.attrib.get("key") == "name"
        )
        for obj in root.findall("object")
    ]


def _decode_bgcode(decoder: Path, bgcode: Path, destination: Path) -> None:
    # The pinned libbgcode CLI accepts one input path and always writes a
    # sibling with the opposite extension. Decode a private copy so inspection
    # cannot create an untracked plaintext file beside the release artifact.
    with tempfile.TemporaryDirectory(prefix="aevum-bgcode-decode-") as work_name:
        work_dir = Path(work_name)
        private_input = work_dir / bgcode.name
        private_input.write_bytes(bgcode.read_bytes())
        _run([str(decoder), str(private_input)])
        decoded = private_input.with_suffix(".gcode")
        if not decoded.is_file() or decoded.stat().st_size == 0:
            raise RuntimeError(f"BGCODE decoder produced no output for {bgcode.name}")
        destination.write_bytes(decoded.read_bytes())


def _decoded_m486_names(text: str) -> list[str]:
    # Prusa firmware names may be shortened with an ellipsis. Identity remains
    # the exact 3MF object name plus the ordered M486 ordinal, both bound to the
    # BGCODE hash in the package manifest.
    names: list[str] = []
    for match in re.finditer(r"^M486\s+A(?:\"([^\"]+)\"|(\S+))", text, re.MULTILINE):
        names.append(match.group(1) or match.group(2))
    if names:
        return names
    return re.findall(r"^; printing object (.+?)(?: id:\d+)?$", text, re.MULTILINE)


def _m486_name_match(body_id: str, decoded_name: str) -> str:
    if decoded_name == body_id:
        return "exact"
    if decoded_name.endswith("...") and body_id.startswith(decoded_name[:-3]):
        return "truncated_prefix"
    raise RuntimeError(
        f"decoded M486 identity does not match 3MF authority: {decoded_name!r} != {body_id!r}"
    )


def _support_evidence(text: str) -> dict[str, Any]:
    support_markers = sum(
        1 for line in text.splitlines() if line.startswith(";TYPE:Support material")
    )
    return {
        "decoded_support_type_markers": support_markers,
        "support_present": support_markers > 0,
        "critical_surface_contact_status": (
            "physical_cleanup_mapping_pending"
            if support_markers
            else "not_applicable_no_decoded_support"
        ),
    }


def _decoded_toolpath_evidence(text: str, body_ids: tuple[str, ...]) -> dict[str, Any]:
    decoded_names = _decoded_m486_names(text)
    if len(decoded_names) != len(body_ids):
        raise RuntimeError(
            f"decoded body count mismatch: {len(decoded_names)} != {len(body_ids)}"
        )
    matches = [
        _m486_name_match(body_id, decoded_name)
        for body_id, decoded_name in zip(body_ids, decoded_names, strict=True)
    ]
    metrics: list[dict[str, Any]] = [
        {
            "object_ordinal": ordinal,
            "release_body_id": body_id,
            "bgcode_m486_name": decoded_names[ordinal],
            "m486_name_match": matches[ordinal],
            "decoded_total_positive_extrusion_mm": 0.0,
            "decoded_model_positive_extrusion_mm": 0.0,
            "support_extrusion_mm": 0.0,
            "bridge_or_overhang_extrusion_mm": 0.0,
            "minimum_observed_model_extrusion_width_mm": None,
            "maximum_observed_model_extrusion_speed_mm_s": 0.0,
            "model_layer_extrusion_mm": {},
            "type_extrusion_mm": {},
        }
        for ordinal, body_id in enumerate(body_ids)
    ]
    current_object: int | None = None
    current_type = "Unknown"
    current_width: float | None = None
    current_z: float | None = None
    current_feed_mm_min = 0.0
    relative_extrusion = True
    absolute_e = 0.0
    motion = re.compile(r"^G[0123](?:\s|$)")
    number = re.compile(r"(?:^|\s)([A-Z])([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)")

    for raw_line in text.splitlines():
        line = raw_line.strip()
        selected = re.match(r"^M486\s+S(-?\d+)", line)
        if selected:
            ordinal = int(selected.group(1))
            current_object = ordinal if 0 <= ordinal < len(metrics) else None
            continue
        if line == "M82":
            relative_extrusion = False
            continue
        if line == "M83":
            relative_extrusion = True
            continue
        if line.startswith("G92"):
            values = {key: float(value) for key, value in number.findall(line)}
            if "E" in values:
                absolute_e = values["E"]
            continue
        if line.startswith(";TYPE:"):
            current_type = line.removeprefix(";TYPE:").strip()
            continue
        if line.startswith(";WIDTH:"):
            try:
                current_width = float(line.removeprefix(";WIDTH:"))
            except ValueError:
                current_width = None
            continue
        if line.startswith(";Z:"):
            try:
                current_z = float(line.removeprefix(";Z:"))
            except ValueError:
                current_z = None
            continue
        if not motion.match(line):
            continue

        values = {key: float(value) for key, value in number.findall(line)}
        if "Z" in values:
            current_z = values["Z"]
        if "F" in values:
            current_feed_mm_min = values["F"]
        if "E" not in values:
            continue
        if relative_extrusion:
            extrusion = values["E"]
        else:
            extrusion = values["E"] - absolute_e
            absolute_e = values["E"]
        if extrusion <= 0 or current_object is None:
            continue

        row = metrics[current_object]
        row["decoded_total_positive_extrusion_mm"] += extrusion
        by_type = row["type_extrusion_mm"]
        by_type[current_type] = by_type.get(current_type, 0.0) + extrusion
        is_support = current_type.startswith("Support material")
        is_bridge = current_type in {"Bridge infill", "Overhang perimeter"}
        is_model = current_type not in {
            "Custom",
            "Skirt/Brim",
            "Wipe tower",
            "Unknown",
        } and not is_support
        if is_support:
            row["support_extrusion_mm"] += extrusion
        if is_bridge:
            row["bridge_or_overhang_extrusion_mm"] += extrusion
        if is_model:
            row["decoded_model_positive_extrusion_mm"] += extrusion
            layer_key = "unknown" if current_z is None else f"{current_z:.6f}"
            layers = row["model_layer_extrusion_mm"]
            layers[layer_key] = layers.get(layer_key, 0.0) + extrusion
            if current_width is not None and current_width > 0:
                old_width = row["minimum_observed_model_extrusion_width_mm"]
                row["minimum_observed_model_extrusion_width_mm"] = (
                    current_width if old_width is None else min(old_width, current_width)
                )
            row["maximum_observed_model_extrusion_speed_mm_s"] = max(
                row["maximum_observed_model_extrusion_speed_mm_s"],
                current_feed_mm_min / 60.0,
            )

    for row in metrics:
        layers = row.pop("model_layer_extrusion_mm")
        numeric_layers = sorted(float(value) for value in layers if value != "unknown")
        first_layer = f"{numeric_layers[0]:.6f}" if numeric_layers else None
        row["first_model_layer_z_mm"] = numeric_layers[0] if numeric_layers else None
        row["first_model_layer_extrusion_mm"] = (
            layers[first_layer] if first_layer is not None else 0.0
        )
        row["decoded_model_layer_count"] = len(layers)
        for key in (
            "decoded_total_positive_extrusion_mm",
            "decoded_model_positive_extrusion_mm",
            "support_extrusion_mm",
            "bridge_or_overhang_extrusion_mm",
            "maximum_observed_model_extrusion_speed_mm_s",
        ):
            row[key] = round(row[key], 6)
        row["type_extrusion_mm"] = {
            key: round(value, 6) for key, value in sorted(row["type_extrusion_mm"].items())
        }
        if row["minimum_observed_model_extrusion_width_mm"] is not None:
            row["minimum_observed_model_extrusion_width_mm"] = round(
                row["minimum_observed_model_extrusion_width_mm"], 6
            )
        row["first_model_layer_extrusion_mm"] = round(
            row["first_model_layer_extrusion_mm"], 6
        )
        if (
            row["decoded_model_positive_extrusion_mm"] <= 0
            or row["first_model_layer_z_mm"] is None
        ):
            raise RuntimeError(
                f"decoded toolpath has no model extrusion for {row['release_body_id']}"
            )

    return {
        "decoded_body_count": len(decoded_names),
        "m486_names": decoded_names,
        "m486_name_matches": matches,
        "objects": metrics,
        **_support_evidence(text),
    }


def _update_authority_output_hashes(
    authority_path: Path,
    body_paths: dict[str, dict[str, Path]],
) -> None:
    authority = json.loads(authority_path.read_text())
    rigid = {
        row["release_body_id"]: row
        for row in authority["release_bodies"]
        if row["body_class"] == "rigid_print_piece"
    }
    if set(rigid) != set(body_paths):
        raise ValueError("regenerated CAD body IDs do not match artifact authority")
    for body_id, paths in body_paths.items():
        for extension in ("stl", "step"):
            path = paths[extension]
            rigid[body_id]["outputs"][extension] = {
                "path": str(path.relative_to(ROOT)),
                "sha256": _sha256(path),
            }
    _atomic_json(authority_path, authority)


def _regenerate_cad(
    input_dir: Path,
    *,
    params_path: Path,
    authority_path: Path,
) -> None:
    from aevum_cad.params import load_params
    from aevum_cad.row_coupon import export_row_coupon_final_print_pieces

    params = load_params(params_path)
    input_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{input_dir.name}.staging-",
        dir=input_dir.parent,
    ) as staging_name:
        staging = Path(staging_name)
        exported = export_row_coupon_final_print_pieces(params, staging)
        stls = sorted(staging.glob("*.stl"))
        steps = sorted(staging.glob("*.step"))
        if (
            len(stls) != RIGID_BODY_COUNT
            or len(steps) != RIGID_BODY_COUNT
            or len(exported) != EXPORTED_CAD_PATH_COUNT
        ):
            raise RuntimeError(
                "final CAD regeneration did not produce exact "
                f"{RIGID_BODY_COUNT} STEP/STL pairs"
            )
        previous = input_dir.with_name(f".{input_dir.name}.previous")
        if input_dir.exists():
            if previous.exists():
                raise RuntimeError(f"refusing to overwrite recovery directory: {previous}")
            os.replace(input_dir, previous)
        try:
            os.replace(staging, input_dir)
        except BaseException:
            if previous.exists():
                os.replace(previous, input_dir)
            raise

    body_paths = {
        _canonical_name(path): {
            "stl": path,
            "step": path.with_suffix(".step"),
        }
        for path in input_dir.glob("*.stl")
    }
    _update_authority_output_hashes(authority_path, body_paths)


def _write_profiles(prusa_slicer: Path, datadir: Path, output_dir: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name, spec in PROFILE_SPECS.items():
        output = output_dir / f"profile_{name}_mk4_elegoo_pla.ini"
        command = [
            str(prusa_slicer),
            "--datadir",
            str(datadir),
            "--printer-profile",
            PRINTER_PROFILE,
            "--print-profile",
            str(spec["print_profile"]),
            "--material-profile",
            MATERIAL_PROFILE,
            *spec["overrides"],
            "--save",
            str(output),
        ]
        _run(command)
        paths[name] = output
    return paths


def _slice_plate(prusa_slicer: Path, config: Path, project: Path, gcode: Path) -> str:
    output = _run(
        [
            str(prusa_slicer),
            "--load",
            str(config),
            "--dont-arrange",
            "--export-gcode",
            "--output",
            str(gcode),
            str(project),
        ]
    )
    if "print warning:" in output.lower():
        warnings = output[output.lower().index("print warning:") :]
        raise RuntimeError(f"PrusaSlicer rejected {project.name}:\n{warnings}")
    return output


def _rectangles_can_share_bed(
    first: tuple[float, float],
    second: tuple[float, float],
    *,
    margin_mm: float,
    gap_mm: float,
) -> bool:
    usable_x = BED_X_MM - 2 * margin_mm
    usable_y = BED_Y_MM - 2 * margin_mm
    for aw, ad in (first, first[::-1]):
        for bw, bd in (second, second[::-1]):
            if (
                aw + gap_mm + bw <= usable_x
                and max(ad, bd) <= usable_y
            ) or (
                ad + gap_mm + bd <= usable_y
                and max(aw, bw) <= usable_x
            ):
                return True
    return False


def _build_package_manifest(
    *,
    specs: tuple[PlateSpec, ...],
    meshes_by_name: dict[str, Mesh],
    profiles: dict[str, Path],
    placements_by_plate: dict[str, tuple[tuple[float, float, float], ...]],
    output_dir: Path,
    staged_dir: Path,
    input_dir: Path,
    authority_path: Path,
    disposition_by_body: dict[str, str],
    params_path: Path,
    decoded_by_plate: dict[str, dict[str, Any]],
    slicer_path: Path,
) -> dict[str, Any]:
    source_by_body, authority_bodies = _authority_maps(authority_path)
    authority_ids = set(authority_bodies)
    assigned_ids = {name for spec in specs for name in spec.part_names}
    if assigned_ids != authority_ids:
        raise ValueError("plate assignment does not exactly match rigid-body authority")

    plate_rows: list[dict[str, Any]] = []
    body_rows: list[dict[str, Any]] = []
    for plate_index, spec in enumerate(specs, start=1):
        project = staged_dir / f"{spec.name}.3mf"
        bgcode = staged_dir / f"{spec.name}.bgcode"
        profile = profiles[spec.profile]
        exact_names = _project_body_names(project)
        if exact_names != list(spec.part_names):
            raise RuntimeError(f"3MF identity mismatch on {spec.name}")
        decoded = decoded_by_plate.get(spec.name, {})
        decoded_names = decoded.get("m486_names", [])
        if decoded_names:
            if len(decoded_names) != len(exact_names):
                raise RuntimeError(f"decoded identity count mismatch on {spec.name}")
            decoded_matches = [
                _m486_name_match(body_id, decoded_name)
                for body_id, decoded_name in zip(exact_names, decoded_names, strict=True)
            ]
        else:
            decoded_matches = []
        meshes = _meshes_for_spec(spec, meshes_by_name)
        placements = placements_by_plate[spec.name]
        objects: list[dict[str, Any]] = []
        for ordinal, (body_id, mesh, placement) in enumerate(
            zip(spec.part_names, meshes, placements, strict=True)
        ):
            x, y, z = placement
            placed_bounds = {
                "x_min_mm": round(mesh.bounds[0] + x, 6),
                "x_max_mm": round(mesh.bounds[1] + x, 6),
                "y_min_mm": round(mesh.bounds[2] + y, 6),
                "y_max_mm": round(mesh.bounds[3] + y, 6),
                "z_min_mm": round(mesh.bounds[4] + z, 6),
                "z_max_mm": round(mesh.bounds[5] + z, 6),
            }
            stl = input_dir / f"{FILE_PREFIX}{body_id}.stl"
            step = stl.with_suffix(".step")
            body_row = {
                "release_body_id": body_id,
                "source_artifact_id": source_by_body[body_id],
                "a2_disposition": disposition_by_body[body_id],
                "plate_id": f"plate_{plate_index:02d}",
                "plate_name": spec.name,
                "object_ordinal": ordinal,
                "identity_chain": {
                    "authority_release_body_id": body_id,
                    "stl_sha256": _sha256(stl),
                    "step_sha256": _sha256(step),
                    "3mf_object_name": exact_names[ordinal],
                    "bgcode_m486_name": (
                        decoded_names[ordinal] if decoded_names else None
                    ),
                    "m486_name_match": (
                        decoded_matches[ordinal] if decoded_matches else None
                    ),
                    "bgcode_sha256": _sha256(bgcode) if bgcode.exists() else None,
                    "bgcode_binding": "plate hash plus ordered M486 object ordinal",
                },
                "orientation": {
                    "policy": "preserve_functional_z_axis_and_place_lowest_surface_on_bed",
                    "rotation_x_deg": 0,
                    "rotation_y_deg": 0,
                    "rotation_z_deg": 90 if body_id in spec.rotate_z_90_names else 0,
                    "translation_mm": [round(value, 6) for value in placement],
                    "placed_bounds": placed_bounds,
                },
                "decoded_toolpath": (
                    decoded["objects"][ordinal] if decoded_names else None
                ),
            }
            objects.append(body_row)
            body_rows.append(body_row)
        plate_rows.append(
            {
                "plate_id": f"plate_{plate_index:02d}",
                "plate_name": spec.name,
                "profile": spec.profile,
                "failure_domain": (
                    "fine_harness_and_service_only"
                    if spec.profile == "fine_service"
                    else (
                        "held_relief_cap_support_review_only"
                        if spec.profile == "relief_cap_support_review"
                        else (
                            "coupon_first_lid_shrouds_support_review_only"
                            if spec.profile == "coupon_support_review"
                            else "print_now_deck_pod_test_articles_only"
                            if all(
                                disposition_by_body[body_id]
                                == "print-now-test-article"
                                for body_id in spec.part_names
                            )
                            else "held_structural_anchor_and_compatible_held_pod_only"
                        )
                    )
                ),
                "bed_margin_mm": spec.bed_margin_mm,
                "minimum_model_gap_mm": spec.object_gap_mm,
                "sequential_printing": False,
                "toolhead_collision_policy": "not_applicable_sequential_printing_disabled",
                "body_ids": list(spec.part_names),
                "body_dispositions": [
                    disposition_by_body[body_id] for body_id in spec.part_names
                ],
                "objects": objects,
                "artifacts": {
                    "3mf": {
                        "path": _portable_path(output_dir / project.name),
                        "sha256": _sha256(project),
                    },
                    "bgcode": {
                        "path": _portable_path(output_dir / bgcode.name),
                        "sha256": _sha256(bgcode) if bgcode.exists() else None,
                    },
                    "profile_snapshot": {
                        "path": _portable_path(output_dir / profile.name),
                        "sha256": _sha256(profile),
                    },
                },
                "decoded_toolpath": decoded or None,
            }
        )

    anchors = [
        name
        for name in assigned_ids
        if name.startswith(
            (
                "lid_cover_piece_",
                "lid_manifold_shell_piece_",
                "plate_support_frame_piece_",
                "wet_chamber_frame_piece_",
            )
        )
    ]
    anchors.sort()
    pairwise = []
    for index, first in enumerate(anchors):
        for second in anchors[index + 1 :]:
            a = meshes_by_name[first]
            b = meshes_by_name[second]
            pairwise.append(
                {
                    "body_a": first,
                    "body_b": second,
                    "can_share_usable_bed": _rectangles_can_share_bed(
                        (a.width, a.depth),
                        (b.width, b.depth),
                        margin_mm=3.0,
                        gap_mm=6.0,
                    ),
                }
            )
    if len(anchors) != 8:
        raise ValueError(f"expected eight large anchors, found {len(anchors)}")
    if any(row["can_share_usable_bed"] for row in pairwise):
        raise ValueError("large-anchor pair unexpectedly co-packs on the selected bed")

    return {
        "schema_version": 1,
        "package_id": "aevum_row_coupon_mk4_elegoo_pla_c2",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "authority": {
            "artifact_registry": _portable_path(authority_path),
            "artifact_registry_sha256": _sha256(authority_path),
            "params": _portable_path(params_path),
            "params_sha256": _sha256(params_path),
            "manufacturing_evidence_only": True,
            "operator_release_granted": False,
        },
        "slicer": {
            "application": PRUSA_SLICER_PROJECT_APPLICATION,
            "executable": str(slicer_path),
            "executable_sha256": _sha256(slicer_path),
            "printer_profile": PRINTER_PROFILE,
            "material_profile_base": MATERIAL_PROFILE,
        },
        "counts": {
            "plates": len(specs),
            "rigid_bodies": len(body_rows),
            "large_anchor_bodies": len(anchors),
            "zero_support_fine_harness_service_bodies": sum(
                len(spec.part_names) for spec in specs if spec.profile == "fine_service"
            ),
            "relief_cap_support_review_bodies": sum(
                len(spec.part_names)
                for spec in specs
                if spec.profile == "relief_cap_support_review"
            ),
            "coupon_support_review_bodies": sum(
                len(spec.part_names)
                for spec in specs
                if spec.profile == "coupon_support_review"
            ),
        },
        "minimality": {
            "plate_lower_bound": 12,
            "large_anchor_lower_bound": 8,
            "independent_print_now_pod_failure_domain_lower_bound": 1,
            "isolated_fine_failure_domain_lower_bound": 1,
            "isolated_relief_cap_support_review_lower_bound": 1,
            "isolated_coupon_shroud_support_review_lower_bound": 1,
            "pairwise_anchor_rotation_check": pairwise,
            "reason": (
                "No two large anchors fit the usable bed at 0/90 degree rotations; "
                "PRINT-NOW pods 2/4 require one job independent of held anchors; 20 "
                "fragile zero-support bodies require one fine-profile failure domain; "
                "the floating HOLD relief cap requires one support-review job; and the "
                "two coupon-first lid shrouds require their own support-review job."
            ),
        },
        "plates": plate_rows,
        "bodies": body_rows,
    }


def _ini_settings(path: Path) -> dict[str, str]:
    settings: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if " = " in line and not line.startswith(("#", ";")):
            key, value = line.split(" = ", 1)
            settings[key] = value
    return settings


def _minimum_bbox_gap(
    body_id: str,
    objects: list[dict[str, Any]],
) -> float | None:
    target = next(row for row in objects if row["release_body_id"] == body_id)
    a = target["orientation"]["placed_bounds"]
    gaps: list[float] = []
    for other in objects:
        if other["release_body_id"] == body_id:
            continue
        b = other["orientation"]["placed_bounds"]
        dx = max(a["x_min_mm"] - b["x_max_mm"], b["x_min_mm"] - a["x_max_mm"], 0)
        dy = max(a["y_min_mm"] - b["y_max_mm"], b["y_min_mm"] - a["y_max_mm"], 0)
        gaps.append((dx * dx + dy * dy) ** 0.5)
    return round(min(gaps), 6) if gaps else None


def _current_disposition_reason(
    *,
    disposition: str,
    source: dict[str, Any],
    split_body: bool,
    support_extrusion_mm: float,
) -> str:
    reasons: list[str] = []
    geometry_state = source["geometry_state"]
    if geometry_state.startswith("blocked_"):
        reasons.append(f"canonical source remains blocked ({geometry_state})")
    if support_extrusion_mm > 0:
        reasons.append(
            "decoded support has no mapped functional-surface cleanup allowance"
        )
    if split_body:
        reasons.append(
            "source-local retained split is digitally corrected but physical seam fit, "
            "load, and cycle evidence remains pending"
        )
    if source["material_status"] == "blocked_pla_not_operating_approved":
        reasons.append("PLA is not approved for operating wedge-lock use")
    if disposition == "print-now-test-article":
        reasons.append("authorization is limited to a measured dimensional/interface article")
    elif disposition == "coupon-first" and not reasons:
        reasons.append("bounded interface coupon and COTS mating evidence remain pending")
    elif disposition == "hold" and not reasons:
        reasons.append(
            f"assembly evidence remains pending ({geometry_state}); do not queue for assembly"
        )
    return "; ".join(reasons) + "."


def _build_printability_ledger(
    *,
    package_manifest: dict[str, Any],
    prior_ledger_path: Path,
    authority_path: Path,
    staged_dir: Path,
    output_dir: Path,
    decoder_path: Path,
) -> dict[str, Any]:
    prior = json.loads(prior_ledger_path.read_text())
    prior_bodies = {row["release_body_id"]: row for row in prior["bodies"]}
    authority = json.loads(authority_path.read_text())
    sources = {
        row["source_artifact_id"]: row for row in authority["canonical_sources"]
    }
    release_bodies = {
        row["release_body_id"]: row
        for row in authority["release_bodies"]
        if row["body_class"] == "rigid_print_piece"
    }
    release_counts: dict[str, int] = {}
    for row in authority["release_bodies"]:
        if row["body_class"] == "rigid_print_piece":
            source_id = row["source_artifact_id"]
            release_counts[source_id] = release_counts.get(source_id, 0) + 1

    plate_rows: list[dict[str, Any]] = []
    body_rows: list[dict[str, Any]] = []
    for plate in package_manifest["plates"]:
        profile_name = Path(plate["artifacts"]["profile_snapshot"]["path"]).name
        settings = _ini_settings(staged_dir / profile_name)
        objects = plate["objects"]
        dispositions = [row["a2_disposition"] for row in objects]
        plate_rows.append(
            {
                "plate_id": plate["plate_id"],
                "plate_name": plate["plate_name"],
                "profile": plate["profile"],
                "failure_domain": plate["failure_domain"],
                "mixed_body_plate": len(objects) > 1,
                "body_ids": plate["body_ids"],
                "body_dispositions": dispositions,
                "plate_disposition": max(dispositions, key=DISPOSITION_RANK.__getitem__),
                "whole_plate_print_authorized": False,
                "strictest_body_policy_applied": True,
                "artifacts": {
                    **plate["artifacts"],
                    "decoded_gcode_sha256": plate["decoded_toolpath"][
                        "decoded_sha256"
                    ],
                },
                "slice_settings": {
                    "layer_height_mm": float(settings["layer_height"]),
                    "first_layer_height_mm": float(settings["first_layer_height"]),
                    "perimeters": int(settings["perimeters"]),
                    "fill_density_percent": float(settings["fill_density"].rstrip("%")),
                    "brim_width_mm": float(settings["brim_width"]),
                    "support_material": settings["support_material"] == "1",
                    "support_material_auto": settings["support_material_auto"] == "1",
                    "support_material_buildplate_only": settings[
                        "support_material_buildplate_only"
                    ]
                    == "1",
                    "max_print_speed_mm_s": float(settings["max_print_speed"]),
                    "nozzle_temperature_c": float(settings["temperature"]),
                    "first_layer_nozzle_temperature_c": float(
                        settings["first_layer_temperature"]
                    ),
                    "bed_temperature_c": float(settings["bed_temperature"]),
                },
                "decoded_body_count": plate["decoded_toolpath"]["decoded_body_count"],
                "decoded_support_type_markers": plate["decoded_toolpath"][
                    "decoded_support_type_markers"
                ],
            }
        )

        decoded_objects = plate["decoded_toolpath"]["objects"]
        for obj, decoded in zip(objects, decoded_objects, strict=True):
            body_id = obj["release_body_id"]
            source_id = obj["source_artifact_id"]
            old = prior_bodies[
                body_id
                if body_id in prior_bodies
                else LEGACY_LEDGER_BODY_MIGRATIONS[body_id]
            ]
            support_extrusion = decoded["support_extrusion_mm"]
            body_rows.append(
                {
                    "release_body_id": body_id,
                    "source_artifact_id": source_id,
                    "plate_id": plate["plate_id"],
                    "object_ordinal": obj["object_ordinal"],
                    "identity_evidence": {
                        "authority": "authority_release_id_plus_3mf_name_plus_ordered_m486",
                        "3mf_object_name": obj["identity_chain"]["3mf_object_name"],
                        "bgcode_m486_name": obj["identity_chain"]["bgcode_m486_name"],
                        "m486_name_match": obj["identity_chain"]["m486_name_match"],
                        "bgcode_sha256": obj["identity_chain"]["bgcode_sha256"],
                    },
                    "orientation": {
                        "method": obj["orientation"]["policy"],
                        "rotation_from_canonical_deg_xyz": [
                            obj["orientation"]["rotation_x_deg"],
                            obj["orientation"]["rotation_y_deg"],
                            obj["orientation"]["rotation_z_deg"],
                        ],
                        "placed_bounds": obj["orientation"]["placed_bounds"],
                        "placed_z_min_mm": obj["orientation"]["placed_bounds"][
                            "z_min_mm"
                        ],
                    },
                    "first_layer_contact": {
                        "status": (
                            "direct_model_extrusion_at_first_layer"
                            if decoded["first_model_layer_z_mm"]
                            <= float(settings["first_layer_height"]) + 1e-6
                            else "elevated_model_requires_support_review"
                        ),
                        "first_model_layer_z_mm": decoded["first_model_layer_z_mm"],
                        "first_model_layer_extrusion_mm": decoded[
                            "first_model_layer_extrusion_mm"
                        ],
                    },
                    "minimum_printed_feature": {
                        "observed_minimum_model_extrusion_width_mm": decoded[
                            "minimum_observed_model_extrusion_width_mm"
                        ],
                        "status": "unresolved_width_proxy_only",
                        "limitation": (
                            "Extrusion width is not a geometric wall, gap, or thickness "
                            "measurement; the feature-aware minimum gate remains physical."
                        ),
                    },
                    "bridges": {
                        "bridge_or_overhang_extrusion_mm": decoded[
                            "bridge_or_overhang_extrusion_mm"
                        ],
                        "present": decoded["bridge_or_overhang_extrusion_mm"] > 0,
                    },
                    "supports": {
                        "support_extrusion_mm": support_extrusion,
                        "present": support_extrusion > 0,
                        "critical_surface_contact_status": (
                            "unresolved_support_present_no_functional_surface_map"
                            if support_extrusion > 0
                            else "not_applicable_no_decoded_support"
                        ),
                        "cleanup_allowance": (
                            "none_documented" if support_extrusion > 0 else "not_applicable"
                        ),
                        "blocker": support_extrusion > 0,
                    },
                    "seams": {
                        "assembly_split_seam_status": (
                            sources[source_id]["geometry_state"]
                            if release_counts[source_id] == 2
                            else "not_applicable_unsplit_source"
                        ),
                        "slicer_layer_seam_status": "not_feature_mapped",
                    },
                    "brim": {
                        "configured_width_mm": float(settings["brim_width"]),
                        "allocation_note": (
                            "plate-level setting; global Skirt/Brim paths are not assigned "
                            "to M486 bodies"
                        ),
                    },
                    "speed": {
                        "configured_max_print_speed_mm_s": float(
                            settings["max_print_speed"]
                        ),
                        "maximum_observed_model_extrusion_speed_mm_s": decoded[
                            "maximum_observed_model_extrusion_speed_mm_s"
                        ],
                    },
                    "body_collisions": {
                        "plate_xy_bbox_intersection": False,
                        "intersecting_body_ids": [],
                        "minimum_xy_bbox_gap_to_other_body_mm": _minimum_bbox_gap(
                            body_id, objects
                        ),
                        "installed_body_collision_status": sources[source_id][
                            "geometry_state"
                        ],
                    },
                    "artifact_completeness": {
                        "canonical_stl_path": release_bodies[body_id]["outputs"][
                            "stl"
                        ]["path"],
                        "canonical_stl_sha256": obj["identity_chain"]["stl_sha256"],
                        "canonical_step_sha256": obj["identity_chain"]["step_sha256"],
                        "3mf_object_present": True,
                        "bgcode_m486_object_present": True,
                        "positive_extrusion_present": decoded[
                            "decoded_total_positive_extrusion_mm"
                        ]
                        > 0,
                        "decoded_total_positive_extrusion_mm": decoded[
                            "decoded_total_positive_extrusion_mm"
                        ],
                        "decoded_model_layer_count": decoded[
                            "decoded_model_layer_count"
                        ],
                        "complete": decoded["decoded_total_positive_extrusion_mm"] > 0,
                    },
                    "geometry_likely_to_print": old["geometry_likely_to_print"],
                    "disposition": old["disposition"],
                    "disposition_reason": _current_disposition_reason(
                        disposition=old["disposition"],
                        source=sources[source_id],
                        split_body=release_counts[source_id] == 2,
                        support_extrusion_mm=support_extrusion,
                    ),
                    "assembly_authorized": False,
                }
            )

    disposition_counts = {
        disposition: sum(row["disposition"] == disposition for row in body_rows)
        for disposition in DISPOSITION_RANK
    }
    decoded_report = staged_dir / DECODED_REPORT
    return {
        "schema_version": 2,
        "ledger_id": "aevum_row_coupon_mk4_elegoo_pla_body_printability",
        "authority": {
            "body_identity": (
                "artifact authority release ID plus exact 3MF object metadata and ordered "
                "BGCODE M486 identity; filename and plate position alone are not authority"
            ),
            "artifact_registry": _portable_path(authority_path),
            "artifact_registry_schema_version": authority["schema_version"],
            "scope": "current twelve-plate MK4 / Elegoo PLA C2 manufacturing package",
            "manufacturing_evidence_only": True,
            "prototype_acceptance_granted": False,
        },
        "supersession": {
            "status": "supersedes_prior_eight_plate_package",
            "prior_scope": "retained legacy eight-plate MK4 / Elegoo PLA package",
            "reason": (
                "C2 geometry/profile/failure-domain repack; old hashes and plate mappings "
                "must not be used with this package"
            ),
            "retained_recovery_package": _portable_path(
                output_dir.with_name(f".{output_dir.name}.previous")
            ),
        },
        "decoder_evidence": {
            "decoder": "Prusa libbgcode command-line converter",
            "decoder_executable": str(decoder_path),
            "decoder_executable_sha256": _sha256(decoder_path),
            "libbgcode_source_commit": LIBBGCODE_SOURCE_COMMIT,
            "command_pattern": "bgcode <private-copy.bgcode>",
            "plaintext_outputs_retained": False,
            "decoded_report": _portable_path(output_dir / DECODED_REPORT),
            "decoded_report_sha256": _sha256(decoded_report),
            "binding": (
                "Every decoded-gcode SHA256 and ordered M486 object list is paired with "
                "the current plate BGCODE SHA256."
            ),
        },
        "policy": prior["policy"],
        "counts": {
            "plates": len(plate_rows),
            "rigid_bodies": len(body_rows),
            "decoded_bodies": sum(row["decoded_body_count"] for row in plate_rows),
            **disposition_counts,
            "whole_plates_authorized": 0,
        },
        "plates": plate_rows,
        "bodies": body_rows,
    }


def _manifest(
    specs: tuple[PlateSpec, ...],
    meshes_by_name: dict[str, Mesh],
    output_dir: Path,
    sliced: bool,
) -> str:
    lines = [
        "# Aevum row coupon — Prusa MK4 / Elegoo PLA print projects",
        "",
        f"- Printer preset: `{PRINTER_PROFILE}`",
        f"- Material preset base: `{MATERIAL_PROFILE}`",
        "- Filament override: 205 C nozzle, 210 C first layer, 60 C bed",
        "- Maximum print speed: 70 mm/s",
        "- Bed: 250 x 210 mm. Every plate records its exact model-edge margin and gap.",
        "- Each 3MF embeds its assigned profile; open it directly in PrusaSlicer.",
        "- Generated `.bgcode` files are manufacturing inputs, not operator release.",
        "- This is the constrained minimum twelve-plate layout: each of the 8 large "
        "structural halves anchors one plate, PRINT-NOW pods remain separate from held "
        "anchors, and fragile bodies remain isolated.",
        "- Plate 09 contains PRINT-NOW deck pods 2/4. Plate 10 contains all 8 "
        "harness-cover halves and 15 zero-support service bodies. Plate 11 isolates "
        "the HOLD sample-relief cap with generated support for review. Plate 12 isolates "
        "the two coupon-first lid connector shrouds with generated support. Plates 05 and "
        "06 place one compatible HOLD pod beside a HOLD support-frame half.",
        "- The source STLs remain the unit for selective reprints.",
        "- Plate 10 uses 0.15 mm layers, 3 perimeters, 30% gyroid, no generated support, "
        "an 8 mm model gap, and a 3 mm brim. Decoded support markers must remain zero.",
        "- Plate 11 is not print-authorized: its decoded support proves why the relief "
        "cap remains HOLD pending a mapped cleanup allowance for its plug and seal lip.",
        "- Plate 12 remains coupon-first: both lid shrouds have decoded support and need "
        "physical cleanup/fit evidence before release.",
        "- Queue boundary: 38 rigid PLA bodies only, not the complete installed BOM.",
        "- Outside this queue: 8 flexible/compressible bodies (upper/lower perimeter "
        "gaskets, 4 IR face gaskets, and 2 gas-PCB interface gaskets), plus COTS "
        "plates/mats, electronics, tubing, and cables.",
        "- Full installed reference: `cad/view_one_row_coupon_print_pieces.py`.",
        "- Assembly: dry-fit every matching `piece_01` / `piece_02` pair. All eight "
        "split sources have source-local dovetail or stepped-lap retention; physical "
        "fit, load, cycle, and leak evidence remains pending.",
        "- Material assumption: standard Elegoo 1.75 mm PLA. If the spool says PLA+, "
        "Rapid PLA, Silk PLA, or another blend, select that material and reslice the 3MFs.",
        "- These are first-pass slicer projects, not physical Gate 1 acceptance evidence.",
        "",
        "| Plate | Profile | Bodies | Project | G-code |",
        "|---|---|---:|---|---|",
    ]
    for spec in specs:
        project = output_dir / f"{spec.name}.3mf"
        gcode = output_dir / f"{spec.name}.bgcode"
        lines.append(
            f"| `{spec.name}` | `{spec.profile}` | {len(spec.part_names)} | "
            f"`{project.name}` | `{gcode.name if sliced else 'not generated'}` |"
        )
        for part_name in spec.part_names:
            mesh = meshes_by_name[part_name]
            rotated = part_name in spec.rotate_z_90_names
            width, depth = (mesh.depth, mesh.width) if rotated else (mesh.width, mesh.depth)
            orientation = "; rotated 90 degrees" if rotated else ""
            lines.append(
                f"| &nbsp;&nbsp;`{part_name}` |  |  | "
                f"{width:.2f} x {depth:.2f} mm footprint{orientation} |  |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--authority", type=Path, default=DEFAULT_AUTHORITY)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--params", type=Path, default=DEFAULT_PARAMS)
    parser.add_argument("--prusa-slicer", type=Path, default=DEFAULT_PRUSA_SLICER)
    parser.add_argument("--datadir", type=Path, default=DEFAULT_DATADIR)
    parser.add_argument("--bgcode-decoder", type=Path)
    parser.add_argument(
        "--regenerate-cad",
        action="store_true",
        help="Atomically regenerate the 38 canonical STEP/STL pairs before packing.",
    )
    parser.add_argument(
        "--slice",
        action="store_true",
        help="Also generate G-code for every plate.",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.regenerate_cad:
        _regenerate_cad(
            args.input_dir,
            params_path=args.params,
            authority_path=args.authority,
        )
    if args.slice and not args.bgcode_decoder:
        raise ValueError("--slice requires --bgcode-decoder for decoded publication evidence")
    if args.bgcode_decoder and not args.bgcode_decoder.is_file():
        raise FileNotFoundError(args.bgcode_decoder)

    stl_paths = sorted(args.input_dir.glob("*.stl"))
    if len(stl_paths) != RIGID_BODY_COUNT:
        raise ValueError(
            f"expected {RIGID_BODY_COUNT} canonical STL bodies, found {len(stl_paths)}"
        )
    meshes_by_name = {_canonical_name(path): _read_stl(path) for path in stl_paths}
    disposition_by_body = _current_dispositions(args.ledger, set(meshes_by_name))
    specs = _plate_specs(set(meshes_by_name), disposition_by_body)

    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(args.output_dir)

    with tempfile.TemporaryDirectory(
        prefix=f".{args.output_dir.name}.staging-",
        dir=args.output_dir.parent,
    ) as staging_name:
        staging_dir = Path(staging_name)
        profiles = _write_profiles(args.prusa_slicer, args.datadir, staging_dir)
        placements_by_plate: dict[str, tuple[tuple[float, float, float], ...]] = {}
        decoded_by_plate: dict[str, dict[str, Any]] = {}
        for spec in specs:
            project = staging_dir / f"{spec.name}.3mf"
            meshes = _meshes_for_spec(spec, meshes_by_name)
            placements_by_plate[spec.name] = _write_3mf(
                project,
                spec.name,
                meshes,
                profiles[spec.profile].read_bytes(),
                bed_margin_mm=spec.bed_margin_mm,
                object_gap_mm=spec.object_gap_mm,
            )
            if args.slice:
                bgcode = staging_dir / f"{spec.name}.bgcode"
                _slice_plate(
                    args.prusa_slicer,
                    profiles[spec.profile],
                    project,
                    bgcode,
                )
                with tempfile.NamedTemporaryFile(suffix=".gcode") as decoded_file:
                    decoded_path = Path(decoded_file.name)
                    _decode_bgcode(args.bgcode_decoder, bgcode, decoded_path)
                    decoded_text = decoded_path.read_text(errors="replace")
                    decoded_by_plate[spec.name] = {
                        "decoder": str(args.bgcode_decoder),
                        "decoded_sha256": _sha256(decoded_path),
                        **_decoded_toolpath_evidence(decoded_text, spec.part_names),
                    }

        if args.slice:
            fine = decoded_by_plate["10_fine_harness_and_service_parts"]
            if fine["support_present"]:
                raise RuntimeError("fine service plate unexpectedly contains decoded support")
            print_now_pods = decoded_by_plate[
                "09_deck_pod_tile_2_plus_deck_pod_tile_4"
            ]
            if print_now_pods["support_present"]:
                raise RuntimeError(
                    "PRINT-NOW deck-pod plate unexpectedly contains decoded support"
                )
            relief_cap = decoded_by_plate["11_sample_relief_cap_support_review"]
            if not relief_cap["support_present"]:
                raise RuntimeError(
                    "HOLD relief-cap review plate did not preserve decoded support evidence"
                )
            shrouds = decoded_by_plate["12_lid_connector_shrouds_support_review"]
            if not shrouds["support_present"]:
                raise RuntimeError(
                    "coupon-first lid-shroud review plate did not preserve decoded "
                    "support evidence"
                )

        package_manifest = _build_package_manifest(
            specs=specs,
            meshes_by_name=meshes_by_name,
            profiles=profiles,
            placements_by_plate=placements_by_plate,
            output_dir=args.output_dir,
            staged_dir=staging_dir,
            input_dir=args.input_dir,
            authority_path=args.authority,
            disposition_by_body=disposition_by_body,
            params_path=args.params,
            decoded_by_plate=decoded_by_plate,
            slicer_path=args.prusa_slicer,
        )
        decoded_report_payload = {
            "schema_version": 1,
            "manufacturing_evidence_only": True,
            "operator_release_granted": False,
            "plates": decoded_by_plate,
        }
        _atomic_json(
            staging_dir / DECODED_REPORT,
            decoded_report_payload,
        )
        published_ledger: dict[str, Any] | None = None
        if args.slice:
            if args.bgcode_decoder is None:
                raise AssertionError("decoder is required for sliced publication")
            published_ledger = _build_printability_ledger(
                package_manifest=package_manifest,
                prior_ledger_path=args.ledger,
                authority_path=args.authority,
                staged_dir=staging_dir,
                output_dir=args.output_dir,
                decoder_path=args.bgcode_decoder,
            )
            _atomic_json(staging_dir / LEDGER_SNAPSHOT, published_ledger)
            package_manifest["printability_ledger_snapshot"] = {
                "path": _portable_path(args.output_dir / LEDGER_SNAPSHOT),
                "sha256": _sha256(staging_dir / LEDGER_SNAPSHOT),
            }
        _atomic_json(staging_dir / PACKAGE_MANIFEST, package_manifest)

        (staging_dir / "README.md").write_text(
            _manifest(specs, meshes_by_name, args.output_dir, args.slice)
        )

        backup_dir = args.output_dir.with_name(f".{args.output_dir.name}.previous")
        if backup_dir.exists():
            raise RuntimeError(f"refusing to overwrite recovery directory: {backup_dir}")
        had_previous = args.output_dir.exists()
        if had_previous:
            os.replace(args.output_dir, backup_dir)
        try:
            os.replace(staging_dir, args.output_dir)
        except BaseException:
            if had_previous:
                os.replace(backup_dir, args.output_dir)
            raise
        if (
            published_ledger is not None
            and args.output_dir.resolve() == DEFAULT_OUTPUT_DIR.resolve()
        ):
            _atomic_json(args.ledger, published_ledger)
        if published_ledger is not None:
            _atomic_json(args.ledger, published_ledger)
        # Intentionally retain the last complete package for recovery. A later
        # publication must explicitly archive or remove it; silent deletion is
        # not allowed.
    print(f"output_dir: {args.output_dir}")
    print(f"projects: {len(specs)}")
    print(f"assigned_bodies: {sum(len(spec.part_names) for spec in specs)}")
    print(f"bgcode_files: {len(specs) if args.slice else 0}")
    print("result: pass")


if __name__ == "__main__":
    main()
