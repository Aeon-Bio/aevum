"""Build the Row Coupon Print Kit viewer bundle from the live model and the slicer packages.

The viewer (``cad/print_kit/index.html``) is a static three.js page that reads
``meta.json`` plus one glTF-in-JSON mesh file per view. Everything in those files is
derived here, from sources that already carry authority in this repo:

- installed parts: ``build_row_coupon_installed_parts`` (the live CAD model)
- print bodies: ``realize_row_coupon_final_print_pieces`` (the live CAD model), placed
  where each printer's slicer package says they sit on the bed
- part class (printed / seal / electronics / consumable / hardware): the artifact
  authority registry, plus an explicit table for the COTS families it does not own
- assembly step: ``docs/assembly/sequence_and_split_matrix.json``
- colours: ``PART_OPTIONS`` in ``cad/view_one_row_coupon.py``, parsed rather than copied

A plate view is only emitted if every body in that slicer package still hashes to the
STL the current model exports. A stale package is refused, not drawn: the plate view
claims to show what will print, and after a geometry change it would not.
"""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cadquery as cq
import numpy as np

PART_CLASSES = ("printed", "seal", "electronics", "consumable", "hardware")

# Installed families the artifact registry does not own (it registers print and compliant
# sources only). Every installed part must land in exactly one class; see classify_parts().
COTS_PART_CLASSES: dict[str, str] = {
    "ir_thermopiles": "electronics",
    "lower_sensor_harness": "electronics",
    "lower_sensor_service_connector": "electronics",
    "lower_sensor_service_cable_pigtail": "electronics",
    "headspace_sht41_microcarriers": "electronics",
    "lid_sensor_harness": "electronics",
    "lid_sensor_service_connectors": "electronics",
    "lid_sensor_service_cable_pigtails": "electronics",
    "gas_sensor_pcbs": "electronics",
    "cots_microplates": "consumable",
    "cots_septum_mats": "consumable",
    "cots_gas_service_tubes": "hardware",
}

# Plate grid on the viewer's floor: four beds per row, one bed width/depth plus a gap apart.
PLATE_GRID_COLUMNS = 4
PLATE_GRID_GAP_MM = 40.0

# The MK4 package predates the printer block the Bambu packages carry.
MK4_PRINTER = {
    "model": "Prusa MK4",
    "bed_x_mm": 250.0,
    "bed_y_mm": 210.0,
    "usable_area_mm": [0.0, 0.0, 250.0, 210.0],
    "exclusion_zones_mm": [],
}

LAYOUTS: tuple[dict[str, str], ...] = (
    {
        "key": "h2s",
        "label": "Bambu H2S",
        "dir": "bambu_h2s_pla",
        "note": "Fewest-plates packing; bodies of any disposition share a plate.",
    },
    {
        "key": "h2d",
        "label": "Bambu H2D",
        "dir": "bambu_h2d_pla",
        "note": "Fewest-plates packing; bodies of any disposition share a plate.",
    },
    {
        "key": "p1s",
        "label": "Bambu P1S / X1C / A1",
        "dir": "bambu_p1s_pla",
        "note": "Fewest-plates packing; bodies of any disposition share a plate.",
    },
    {
        "key": "mk4",
        "label": "Prusa MK4",
        "dir": "mk4_elegoo_pla",
        "note": "One failure domain per plate; 8 structural anchors each own a plate.",
    },
)

_PIECE_RE = re.compile(r"_piece_(\d+)_of_(\d+)")


# --------------------------------------------------------------------------- sources


def load_part_options(viewer_path: Path) -> dict[str, dict[str, Any]]:
    """Parse the ``PART_OPTIONS`` literal out of the CQ-Editor viewer script."""
    tree = ast.parse(viewer_path.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "PART_OPTIONS" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError(f"PART_OPTIONS not found in {viewer_path}")


def classify_parts(installed_names: list[str], registry: dict[str, Any]) -> dict[str, str]:
    """Class for every installed part; fails closed on anything unclassified or double-owned."""
    owned: dict[str, str] = {}
    for source in registry["canonical_sources"]:
        part = source["installed_part"]
        cls = "printed" if source["source_class"] == "rigid_source" else "seal"
        if owned.setdefault(part, cls) != cls:
            raise ValueError(f"installed part {part!r} has both rigid and compliant sources")
    classes: dict[str, str] = {}
    for name in installed_names:
        from_registry = owned.get(name)
        from_table = COTS_PART_CLASSES.get(name)
        if from_registry and from_table:
            raise ValueError(f"{name!r} is classified by both the registry and the COTS table")
        cls = from_registry or from_table
        if cls is None:
            raise ValueError(
                f"installed part {name!r} has no class: add it to COTS_PART_CLASSES "
                "or register it in docs/assembly/artifact_authority.json"
            )
        classes[name] = cls
    stale = sorted(set(COTS_PART_CLASSES) - set(installed_names))
    if stale:
        raise ValueError(f"COTS_PART_CLASSES names parts the model no longer installs: {stale}")
    return classes


def install_states(sequence: dict[str, Any]) -> dict[str, str]:
    """installed family -> the assembly state that installs it."""
    out: dict[str, str] = {}
    for state in sequence["assembly_states"]:
        for family in state["install_families"]:
            out[family] = state["state_id"]
    return out


def release_body_to_installed_part(registry: dict[str, Any]) -> dict[str, str]:
    """Rigid print piece -> the installed part it becomes, via the registry's own chain
    (release body -> canonical source -> installed part), never by parsing names."""
    part_of_source = {
        s["source_artifact_id"]: s["installed_part"] for s in registry["canonical_sources"]
    }
    return {
        rb["release_body_id"]: part_of_source[rb["source_artifact_id"]]
        for rb in registry["release_bodies"]
        if rb["body_class"] == "rigid_print_piece"
    }


# --------------------------------------------------------------------------- geometry


@dataclass
class Mesh:
    positions: np.ndarray  # (n, 3) float
    triangles: np.ndarray  # (m, 3) int
    line_positions: np.ndarray  # (k, 3) float
    lines: np.ndarray  # (j, 2) int

    def transformed(self, rotation_z_deg: float, min_corner: tuple[float, float, float]) -> Mesh:
        """Rotate CCW about Z (the convention both slicer packages use), then translate so the
        mesh's minimum corner lands on ``min_corner``."""
        th = np.radians(rotation_z_deg)
        r = np.array(
            [[np.cos(th), -np.sin(th), 0.0], [np.sin(th), np.cos(th), 0.0], [0.0, 0.0, 1.0]]
        )
        pos = self.positions @ r.T
        lin = self.line_positions @ r.T
        shift = np.asarray(min_corner) - pos.min(axis=0)
        return Mesh(pos + shift, self.triangles, lin + shift, self.lines)

    @property
    def bbox(self) -> list[float]:
        return [*map(float, self.positions.min(axis=0)), *map(float, self.positions.max(axis=0))]


def _shape_of(workplane: cq.Workplane) -> cq.Shape:
    shapes = [v for v in workplane.vals() if isinstance(v, cq.Shape)]
    if not shapes:
        raise ValueError("workplane holds no shapes")
    return shapes[0] if len(shapes) == 1 else cq.Compound.makeCompound(shapes)


def tessellate(workplane: cq.Workplane, tolerance: float, angular: float) -> Mesh:
    """Triangles per face (faces do not share vertices, so shading stays crisp at edges)
    plus the true B-rep edges as line segments."""
    shape = _shape_of(workplane)
    verts, tris = shape.tessellate(tolerance, angular)
    positions = np.array([(v.x, v.y, v.z) for v in verts], dtype=float)
    triangles = np.array(tris, dtype=np.int64).reshape(-1, 3)
    pts: list[tuple[float, float, float]] = []
    segs: list[tuple[int, int]] = []
    for edge in shape.Edges():
        if edge.geomType() == "LINE":
            ts = [0.0, 1.0]
        else:
            n = int(min(48, max(6, edge.Length() / 1.5)))
            ts = list(np.linspace(0.0, 1.0, n))
        base = len(pts)
        for t in ts:
            p = edge.positionAt(t)
            pts.append((p.x, p.y, p.z))
        segs.extend((base + i, base + i + 1) for i in range(len(ts) - 1))
    return Mesh(
        positions,
        triangles,
        np.array(pts, dtype=float).reshape(-1, 3),
        np.array(segs, dtype=np.int64).reshape(-1, 2),
    )


def stl_sha256(workplane: cq.Workplane) -> str:
    """sha256 of the STL the repo's own exporter writes for this body."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "body.stl"
        cq.exporters.export(workplane, str(path))
        return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- glTF


class GltfWriter:
    """Minimal glTF 2.0 writer matching the viewer's reader: one embedded base64 buffer,
    float32 POSITION, uint32 indices, one TRIANGLES and one LINES primitive per named node."""

    def __init__(self, scene_name: str) -> None:
        self.scene_name = scene_name
        self.buffer = bytearray()
        self.views: list[dict[str, Any]] = []
        self.accessors: list[dict[str, Any]] = []
        self.meshes: list[dict[str, Any]] = []
        self.materials: list[dict[str, Any]] = []
        self.nodes: list[dict[str, Any]] = []

    def _accessor(self, array: np.ndarray, *, positions: bool) -> int:
        while len(self.buffer) % 4:
            self.buffer.append(0)
        if positions:
            data = np.ascontiguousarray(array, dtype="<f4")
            comp, typ, target, count = 5126, "VEC3", 34962, len(data)
        else:
            data = np.ascontiguousarray(array, dtype="<u4").reshape(-1)
            comp, typ, target, count = 5125, "SCALAR", 34963, len(data)
        raw = data.tobytes()
        self.views.append(
            {"buffer": 0, "byteOffset": len(self.buffer), "byteLength": len(raw), "target": target}
        )
        self.buffer.extend(raw)
        acc: dict[str, Any] = {
            "bufferView": len(self.views) - 1,
            "componentType": comp,
            "count": int(count),
            "type": typ,
        }
        if positions and count:
            acc["min"] = [float(x) for x in data.min(axis=0)]
            acc["max"] = [float(x) for x in data.max(axis=0)]
        self.accessors.append(acc)
        return len(self.accessors) - 1

    def add(self, name: str, mesh: Mesh, rgba: tuple[float, float, float, float]) -> None:
        self.materials.append(
            {
                "name": name,
                "pbrMetallicRoughness": {
                    "baseColorFactor": [float(c) for c in rgba],
                    "metallicFactor": 0.05,
                    "roughnessFactor": 0.62,
                },
                "alphaMode": "BLEND" if rgba[3] < 1 else "OPAQUE",
                "doubleSided": True,
            }
        )
        prims = [
            {
                "attributes": {"POSITION": self._accessor(mesh.positions, positions=True)},
                "indices": self._accessor(mesh.triangles, positions=False),
                "material": len(self.materials) - 1,
                "mode": 4,
            }
        ]
        if len(mesh.lines):
            prims.append(
                {
                    "attributes": {"POSITION": self._accessor(mesh.line_positions, positions=True)},
                    "indices": self._accessor(mesh.lines, positions=False),
                    "mode": 1,
                }
            )
        self.meshes.append({"name": name, "primitives": prims})
        self.nodes.append({"name": name, "mesh": len(self.meshes) - 1})

    def to_json(self) -> dict[str, Any]:
        return {
            "asset": {
                "version": "2.0",
                "generator": "aevum print kit (scripts/build_row_coupon_print_kit.py)",
            },
            "scene": 0,
            "scenes": [{"name": self.scene_name, "nodes": list(range(len(self.nodes)))}],
            "nodes": self.nodes,
            "meshes": self.meshes,
            "materials": self.materials,
            "accessors": self.accessors,
            "bufferViews": self.views,
            "buffers": [
                {
                    "byteLength": len(self.buffer),
                    "uri": "data:application/octet-stream;base64,"
                    + base64.b64encode(bytes(self.buffer)).decode("ascii"),
                }
            ],
        }


# --------------------------------------------------------------------------- plate layouts


def piece_index(name: str) -> tuple[int, int]:
    m = _PIECE_RE.search(name)
    return (int(m.group(1)), int(m.group(2))) if m else (1, 1)


def plate_origin(index: int, bed_x: float, bed_y: float) -> tuple[float, float]:
    col, row = index % PLATE_GRID_COLUMNS, index // PLATE_GRID_COLUMNS
    return (col * (bed_x + PLATE_GRID_GAP_MM), -row * (bed_y + PLATE_GRID_GAP_MM))


@dataclass
class PlacedBody:
    name: str
    plate_index: int
    rotation_z_deg: int
    x_min: float
    y_min: float
    disposition: str
    stl_sha256: str
    footprint: list[float] | None
    support: bool


def read_slicer_package(package_dir: Path) -> dict[str, Any]:
    """Normalise a Bambu or MK4 package manifest into one shape."""
    manifest = json.loads((package_dir / "package_manifest.json").read_text())
    plates_out: list[dict[str, Any]] = []
    bodies: list[PlacedBody] = []
    if "printer" in manifest:  # Bambu packages (scripts/prepare_row_coupon_bambu_pla_projects.py)
        printer = manifest["printer"]
        slicer = f"{manifest['slicer']['application']} {manifest['slicer']['version']}"
        for i, plate in enumerate(manifest["plates"]):
            s = plate["slice"]
            plates_out.append(
                {
                    "plate_id": plate["plate_id"],
                    "plate_name": plate["plate_name"],
                    "profile": printer.get("process_preset", ""),
                    "gcode": s["gcode_3mf"],
                    "project": s["project"],
                    "estimated_seconds": s.get("estimated_seconds"),
                    "filament_g": s.get("filament_g"),
                    "support_markers": None,
                }
            )
            for b in plate["bodies"]:
                bodies.append(
                    PlacedBody(
                        b["release_body_id"],
                        i,
                        int(b["rotation_z_deg"]),
                        b["x_min_mm"],
                        b["y_min_mm"],
                        b["disposition"],
                        b["stl_sha256"],
                        list(b["footprint_mm"]),
                        bool(b.get("support")),
                    )
                )
    else:  # MK4 package (scripts/prepare_row_coupon_mk4_elegoo_pla_projects.py)
        printer = MK4_PRINTER
        slicer = manifest["slicer"]["application"]
        ledger = {
            p["plate_id"]: p
            for p in json.loads((package_dir / "printability_ledger_snapshot.json").read_text())[
                "plates"
            ]
        }
        by_body = {b["release_body_id"]: b for b in manifest["bodies"]}
        for i, plate in enumerate(manifest["plates"]):
            markers = ledger.get(plate["plate_id"], {}).get("decoded_support_type_markers")
            plates_out.append(
                {
                    "plate_id": plate["plate_id"],
                    "plate_name": plate["plate_name"],
                    "profile": plate["profile"],
                    "gcode": Path(plate["artifacts"]["bgcode"]["path"]).name,
                    "project": Path(plate["artifacts"]["3mf"]["path"]).name,
                    "estimated_seconds": None,
                    "filament_g": None,
                    "support_markers": markers if isinstance(markers, int) else None,
                }
            )
            for body_id in plate["body_ids"]:
                b = by_body[body_id]
                o, pb = b["orientation"], b["orientation"]["placed_bounds"]
                bodies.append(
                    PlacedBody(
                        body_id,
                        i,
                        int(o["rotation_z_deg"]),
                        pb["x_min_mm"],
                        pb["y_min_mm"],
                        b["a2_disposition"],
                        b["identity_chain"]["stl_sha256"],
                        [
                            round(pb["x_max_mm"] - pb["x_min_mm"], 3),
                            round(pb["y_max_mm"] - pb["y_min_mm"], 3),
                            round(pb["z_max_mm"] - pb["z_min_mm"], 3),
                        ],
                        bool(markers),
                    )
                )
    return {
        "generated_at_utc": manifest["generated_at_utc"],
        "slicer": slicer,
        "printer": printer,
        "plates": plates_out,
        "bodies": bodies,
    }


def verify_package(package: dict[str, Any], live_sha: dict[str, str]) -> list[str]:
    """Bodies whose sliced STL no longer matches the live model (empty list = current)."""
    problems = []
    names = [b.name for b in package["bodies"]]
    if sorted(names) != sorted(live_sha):
        problems.append(
            f"body set differs from the live model: missing {sorted(set(live_sha) - set(names))}, "
            f"extra {sorted(set(names) - set(live_sha))}"
        )
    for b in package["bodies"]:
        if b.name in live_sha and live_sha[b.name] != b.stl_sha256:
            problems.append(b.name)
    return problems


def build_layout(
    spec: dict[str, str],
    package: dict[str, Any],
    local_meshes: dict[str, Mesh],
    installed_part_of: dict[str, str],
    part_rgb: dict[str, list[float]],
) -> tuple[dict[str, Any], GltfWriter]:
    printer = package["printer"]
    bed_x, bed_y = float(printer["bed_x_mm"]), float(printer["bed_y_mm"])
    writer = GltfWriter(f"plates_{spec['key']}")
    plates = [dict(p) for p in package["plates"]]
    for i, p in enumerate(plates):
        p["origin"] = list(plate_origin(i, bed_x, bed_y))
        p["body_ids"], p["dispositions"], p["support"] = [], [], False
    pieces = []
    for b in package["bodies"]:
        plate = plates[b.plate_index]
        ox, oy = plate["origin"]
        mesh = local_meshes[b.name].transformed(b.rotation_z_deg, (ox + b.x_min, oy + b.y_min, 0.0))
        source = installed_part_of[b.name]
        rgb = part_rgb[source]
        writer.add(b.name, mesh, (*rgb, 1.0))
        bbox = mesh.bbox
        footprint = b.footprint or [bbox[3] - bbox[0], bbox[4] - bbox[1], bbox[5] - bbox[2]]
        idx, count = piece_index(b.name)
        plate["body_ids"].append(b.name)
        plate["dispositions"].append(b.disposition)
        plate["support"] = plate["support"] or b.support
        pieces.append(
            {
                "name": b.name,
                "source": source,
                "plate_id": plate["plate_id"],
                "plate_name": plate["plate_name"],
                "disposition": b.disposition,
                "rgb": rgb,
                "rotation_z_deg": b.rotation_z_deg,
                "piece_index": idx,
                "piece_count": count,
                "footprint_mm": [round(float(x), 3) for x in footprint],
                "bbox": bbox,
            }
        )
    usable = printer.get("usable_area_mm") or [0.0, 0.0, bed_x, bed_y]
    layout = {
        "key": spec["key"],
        "label": spec["label"],
        "bed": [bed_x, bed_y],
        "usable": [float(v) for v in usable],
        "excludes": [[float(v) for v in z] for z in printer.get("exclusion_zones_mm", [])],
        "file": f"plates_{spec['key']}.gltf.json",
        "plates": plates,
        "pieces": pieces,
        "sliced_dir": f"outputs/sliced/{spec['dir']}",
        "generated_at_utc": package["generated_at_utc"],
        "slicer": package["slicer"],
        "printer": printer.get("model", spec["label"]),
        "note": spec["note"],
        "slice_verified": {"bodies_matching_live_model": len(pieces), "bodies": len(pieces)},
    }
    return layout, writer
