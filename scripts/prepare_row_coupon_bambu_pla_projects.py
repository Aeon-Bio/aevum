"""Pack and slice the 38 rigid row-coupon bodies for a Bambu Lab printer.

Unlike the MK4 pipeline (one failure domain per plate), this packer minimises
the number of plates: every body that fits shares a plate, with only bed
margin and inter-object gap as constraints.  Rotation is restricted to 0/90
degrees about Z so the functional Z axis of every piece is preserved.

Pipeline per plate:
  1. write pre-positioned STL copies (rotated + translated into bed space)
  2. BambuStudio CLI pass 1: load STLs with arrange disabled -> project 3MF
  3. patch Metadata/model_settings.config for per-object support where the
     MK4 package needed a support-review plate
  4. BambuStudio CLI pass 2: slice the patched project -> <plate>.gcode.3mf

The Bambu CLI does not resolve preset `inherits` chains, so machine/process/
filament presets are flattened from the app bundle before use.  The flattened
presets (with our overrides) are written next to the outputs for review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "outputs" / "cad" / "final_print_pieces"
DEFAULT_AUTHORITY = ROOT / "docs" / "assembly" / "artifact_authority.json"
DEFAULT_MK4_MANIFEST = ROOT / "outputs" / "sliced" / "mk4_elegoo_pla" / "package_manifest.json"
DEFAULT_BAMBU_APP = Path("/Applications/BambuStudio.app")
FILE_PREFIX = "aevum_one_row_coupon_"
RIGID_BODY_COUNT = 38

# Presets are the Bambu Studio system presets; the CLI needs the 0.4 nozzle
# machine preset and the model-specific process/filament presets.
PRINTERS: dict[str, dict[str, Any]] = {
    "p1s": {"machine": "Bambu Lab P1S 0.4 nozzle", "process": "0.20mm Standard @BBL X1C", "filament": "Generic PLA"},
    "p1p": {"machine": "Bambu Lab P1P 0.4 nozzle", "process": "0.20mm Standard @BBL X1C", "filament": "Generic PLA"},
    "x1c": {"machine": "Bambu Lab X1 Carbon 0.4 nozzle", "process": "0.20mm Standard @BBL X1C", "filament": "Generic PLA"},
    "a1": {"machine": "Bambu Lab A1 0.4 nozzle", "process": "0.20mm Standard @BBL A1", "filament": "Generic PLA @BBL A1"},
    "p2s": {"machine": "Bambu Lab P2S 0.4 nozzle", "process": "0.20mm Standard @BBL P2S", "filament": "Generic PLA @BBL P2S"},
    "h2d": {"machine": "Bambu Lab H2D 0.4 nozzle", "process": "0.20mm Standard @BBL H2D", "filament": "Generic PLA @BBL H2D"},
    "h2s": {"machine": "Bambu Lab H2S 0.4 nozzle", "process": "0.20mm Standard @BBL H2S", "filament": "Generic PLA @BBL H2S"},
    "a1mini": {"machine": "Bambu Lab A1 mini 0.4 nozzle", "process": "0.20mm Standard @BBL A1M", "filament": "Generic PLA @BBL A1M"},
}

# Mirrors the MK4 "structural" profile intent (3 perimeters, 20% gyroid,
# 5 top / 4 bottom, 0.2 mm layers, no global support).
PROCESS_OVERRIDES: dict[str, Any] = {
    "layer_height": "0.2",
    "initial_layer_print_height": "0.2",
    "wall_loops": "3",
    "sparse_infill_density": "20%",
    "sparse_infill_pattern": "gyroid",
    "top_shell_layers": "5",
    "bottom_shell_layers": "4",
    "enable_support": "0",
    "support_type": "normal(auto)",
    "support_on_build_plate_only": "1",
    "brim_type": "auto_brim",
    "brim_width": "3",
    "seam_position": "aligned",
    "skirt_loops": "0",
    "print_sequence": "by layer",
}


@dataclass(frozen=True)
class Body:
    body_id: str
    stl: Path
    sha256: str
    bounds: tuple[float, float, float, float, float, float]
    disposition: str
    source_artifact: str
    needs_support: bool

    @property
    def width(self) -> float:
        return self.bounds[3] - self.bounds[0]

    @property
    def depth(self) -> float:
        return self.bounds[4] - self.bounds[1]

    @property
    def height(self) -> float:
        return self.bounds[5] - self.bounds[2]


@dataclass
class Placement:
    body: Body
    rotation_z_deg: int
    x_min: float
    y_min: float
    footprint_x: float
    footprint_y: float


@dataclass
class Plate:
    index: int
    placements: list[Placement] = field(default_factory=list)

    @property
    def name(self) -> str:
        anchor = max(self.placements, key=lambda p: p.footprint_x * p.footprint_y).body.body_id
        extra = len(self.placements) - 1
        suffix = f"_plus_{extra:02d}_more" if extra else ""
        return f"{self.index:02d}_{anchor}{suffix}"


# ---------------------------------------------------------------- presets

def _profiles_dir(app: Path) -> Path:
    return app / "Contents" / "Resources" / "profiles" / "BBL"


def _find_preset(app: Path, name: str) -> Path:
    for kind in ("machine", "process", "filament"):
        candidate = _profiles_dir(app) / kind / f"{name}.json"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Bambu preset not found in app bundle: {name}")


def flatten_preset(app: Path, name: str) -> dict[str, Any]:
    """Resolve a preset's `inherits` chain and its `include` templates into one
    self-contained dict.  Bambu Studio 2.x keeps the long machine gcode blocks
    (start/end/layer-change/filament-change/timelapse/wrapping) in separate
    "template" JSON files listed under `include`; without merging them the CLI
    silently falls back to the generic stub in fdm_machine_common, which is not
    the printer's real start-up sequence."""
    data = json.loads(_find_preset(app, name).read_text())
    parent = data.get("inherits")
    merged = flatten_preset(app, parent) if parent else {}
    for template in data.get("include", []):
        tpl = json.loads(_find_preset(app, template).read_text())
        merged.update({k: v for k, v in tpl.items() if k not in ("name", "inherits", "instantiation", "include")})
    merged.update({k: v for k, v in data.items() if k not in ("inherits", "include")})
    merged["inherits"] = ""
    return merged


def _stamp_printer_model_id(sliced: Path, app: Path, machine: dict[str, Any]) -> None:
    """The headless CLI leaves `printer_model_id` blank in Metadata/slice_info.config
    (the GUI fills it from the model definition, e.g. O1S for the H2S).  The H2-series
    touchscreen needs it to offer AMS slot mapping ("current model does not support
    AMS manual mapping" otherwise), so copy it from the model JSON after slicing."""
    model_json = _find_preset(app, machine.get("printer_model", ""))
    model_id = json.loads(model_json.read_text()).get("model_id", "")
    if not model_id:
        return
    tmp = sliced.with_suffix(".tmp")
    with zipfile.ZipFile(sliced) as zin, zipfile.ZipFile(tmp, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "Metadata/slice_info.config":
                data = data.decode().replace('key="printer_model_id" value=""', f'key="printer_model_id" value="{model_id}"').encode()
            zout.writestr(item, data, compress_type=item.compress_type)
    tmp.replace(sliced)


def _bambu_version(app: Path) -> str:
    plist = app / "Contents" / "Info.plist"
    result = subprocess.run(
        ["/usr/bin/defaults", "read", str(plist), "CFBundleShortVersionString"],
        check=False, capture_output=True, text=True,
    )
    return result.stdout.strip() or "unknown"


def _bed_from_machine(machine: dict[str, Any]) -> dict[str, Any]:
    """Usable bed for a single filament: the intersection of every extruder's
    printable area (H2D/H2S nozzles reach different X ranges, and one filament
    must be printable by one nozzle everywhere), minus the machine's exclusion
    zones (purge corner, wrapping-detection strip)."""

    def _pts(raw: Any) -> list[tuple[float, float]]:
        if isinstance(raw, str):
            raw = raw.split(",")
        out = []
        for item in raw:
            x, y = item.split("x")
            out.append((float(x), float(y)))
        return out

    def _bbox(pts: list[tuple[float, float]]) -> tuple[float, float, float, float]:
        return (min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts))

    full = _bbox(_pts(machine["printable_area"]))
    usable = full
    per_extruder = machine.get("extruder_printable_area") or []
    for raw in per_extruder:
        b = _bbox(_pts(raw))
        usable = (max(usable[0], b[0]), max(usable[1], b[1]), min(usable[2], b[2]), min(usable[3], b[3]))
    heights = [float(h) for h in (machine.get("extruder_printable_height") or []) if h]
    height = min(heights) if heights else float(machine.get("printable_height") or 0)
    # (rect, padded): the purge/wipe corner is a physical toolpath region and
    # keeps the object gap; the wrapping-detection strip is only a camera zone.
    excludes: list[tuple[tuple[float, float, float, float], bool]] = []
    for key, padded in (("bed_exclude_area", True), ("wrapping_exclude_area", False)):
        raw = machine.get(key) or []
        if raw:
            excludes.append((_bbox(_pts(raw)), padded))
    return {
        "bed_x": full[2] - full[0], "bed_y": full[3] - full[1], "bed_z": height,
        "usable": usable, "excludes": excludes, "extruders": max(1, len(per_extruder)),
    }


# ---------------------------------------------------------------- inputs

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stl_bounds(path: Path) -> tuple[float, float, float, float, float, float]:
    data = path.read_bytes()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        raise ValueError(f"{path.name}: ASCII STL not supported; export binary STL")
    count = struct.unpack("<I", data[80:84])[0]
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for i in range(count):
        v = struct.unpack("<12f", data[84 + i * 50 : 84 + i * 50 + 48])
        for k in range(3):
            for j in (3, 6, 9):
                lo[k] = min(lo[k], v[j + k])
                hi[k] = max(hi[k], v[j + k])
    return (lo[0], lo[1], lo[2], hi[0], hi[1], hi[2])


def _write_placed_stl(src: Path, dst: Path, placement: Placement) -> None:
    """Copy a binary STL rotated 0/90 deg about Z (about its bbox centre) and
    translated so its footprint min corner lands at (x_min, y_min, 0)."""
    data = src.read_bytes()
    count = struct.unpack("<I", data[80:84])[0]
    b = placement.body.bounds
    cx, cy = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
    rot = placement.rotation_z_deg % 360
    if rot == 0:
        rx = lambda x, y: x  # noqa: E731
        ry = lambda x, y: y  # noqa: E731
        rot_min_x, rot_min_y = b[0], b[1]
    elif rot == 90:
        # (x, y) -> (cx - (y - cy), cy + (x - cx))
        rx = lambda x, y: cx - (y - cy)  # noqa: E731
        ry = lambda x, y: cy + (x - cx)  # noqa: E731
        rot_min_x, rot_min_y = cx - (b[4] - cy), cy + (b[0] - cx)
    else:
        raise ValueError("only 0/90 degree rotations are allowed")
    tx = placement.x_min - rot_min_x
    ty = placement.y_min - rot_min_y
    tz = -b[2]
    out = bytearray(data[:84])
    for i in range(count):
        rec = list(struct.unpack("<12fH", data[84 + i * 50 : 84 + (i + 1) * 50]))
        nx, ny = rec[0], rec[1]
        rec[0], rec[1] = rx(nx, ny) - rx(0, 0), ry(nx, ny) - ry(0, 0)
        for j in (3, 6, 9):
            x, y = rec[j], rec[j + 1]
            rec[j] = rx(x, y) + tx
            rec[j + 1] = ry(x, y) + ty
            rec[j + 2] += tz
        out += struct.pack("<12fH", *rec)
    dst.write_bytes(bytes(out))


def load_bodies(input_dir: Path, authority: Path, mk4_manifest: Path) -> list[Body]:
    registry = json.loads(authority.read_text())
    rigid = [b for b in registry["release_bodies"] if b["body_class"] == "rigid_print_piece"]
    if len(rigid) != RIGID_BODY_COUNT:
        raise ValueError(f"authority lists {len(rigid)} rigid bodies, expected {RIGID_BODY_COUNT}")

    manifest = json.loads(mk4_manifest.read_text())
    mk4_bodies = {b["release_body_id"]: b for b in manifest["bodies"]}
    # MK4 parity: every plate except the zero-support fine-service plate ran
    # PrusaSlicer with automatic build-plate-only support.  Carry that over per
    # object so the fine harness/service bodies stay support-free while the
    # structural halves, pods and support-review bodies keep auto support.
    supported_plates = {
        p["plate_id"] for p in manifest["plates"] if p["profile"] != "fine_service"
    }

    bodies: list[Body] = []
    for entry in rigid:
        body_id = entry["release_body_id"]
        stl = ROOT / entry["outputs"]["stl"]["path"]
        if stl.parent != input_dir:
            stl = input_dir / stl.name
        if not stl.exists():
            raise FileNotFoundError(f"missing STL for {body_id}: {stl}")
        digest = _sha256(stl)
        expected = entry["outputs"]["stl"]["sha256"]
        if digest != expected:
            raise ValueError(
                f"{stl.name} sha256 {digest[:12]} does not match artifact authority {expected[:12]}; "
                "regenerate CAD or refresh docs/assembly/artifact_authority.json"
            )
        mk4 = mk4_bodies.get(body_id)
        if mk4 is None:
            raise ValueError(f"{body_id} has no disposition in the MK4 package manifest")
        bodies.append(
            Body(
                body_id=body_id,
                stl=stl,
                sha256=digest,
                bounds=_stl_bounds(stl),
                disposition=mk4["a2_disposition"],
                source_artifact=entry["source_artifact_id"],
                needs_support=mk4["plate_id"] in supported_plates,
            )
        )
    return bodies


# ---------------------------------------------------------------- packing

Rect = tuple[float, float, float, float]  # x, y, w, h


def _split(rect: Rect, occ: tuple[float, float, float, float]) -> list[Rect]:
    x, y, w, h = rect
    ox0, oy0, ox1, oy1 = occ
    if ox0 >= x + w or ox1 <= x or oy0 >= y + h or oy1 <= y:
        return [rect]
    out: list[Rect] = []
    if ox0 > x:
        out.append((x, y, ox0 - x, h))
    if ox1 < x + w:
        out.append((ox1, y, x + w - ox1, h))
    if oy0 > y:
        out.append((x, y, w, oy0 - y))
    if oy1 < y + h:
        out.append((x, oy1, w, y + h - oy1))
    return [r for r in out if r[2] > 0.5 and r[3] > 0.5]


def _contains(a: Rect, b: Rect) -> bool:
    return a[0] <= b[0] and a[1] <= b[1] and a[0] + a[2] >= b[0] + b[2] and a[1] + a[3] >= b[1] + b[3]


def _carve(free: list[Rect], occ: tuple[float, float, float, float]) -> list[Rect]:
    pieces: list[Rect] = []
    for rect in free:
        pieces.extend(_split(rect, occ))
    return [r for i, r in enumerate(pieces) if not any(j != i and _contains(s, r) for j, s in enumerate(pieces))]


def pack_bodies(
    bodies: list[Body],
    *,
    usable: tuple[float, float, float, float],
    bed_z: float,
    margin: float,
    gap: float,
    support_gap: float,
    excludes: list[tuple[tuple[float, float, float, float], bool]],
) -> list[Plate]:
    """Fewest-plates greedy packing: first-fit-decreasing by footprint area
    over a maximal-rectangles free list, trying 0/90 rotation and all four
    corners of every free rectangle, keeping the placement that leaves the
    largest single free rectangle behind."""
    ux0, uy0, ux1, uy1 = usable
    bed_x, bed_y = ux1 - ux0, uy1 - uy0
    for body in bodies:
        if bed_z and body.height > bed_z:
            raise ValueError(f"{body.body_id} is {body.height:.1f} mm tall; bed height is {bed_z:.0f} mm")
        if min(body.width, body.depth) > min(bed_x, bed_y) - 2 * margin or max(body.width, body.depth) > max(bed_x, bed_y) - 2 * margin:
            raise ValueError(
                f"{body.body_id} ({body.width:.1f} x {body.depth:.1f} mm) cannot fit the usable {bed_x:.0f} x {bed_y:.0f} mm bed "
                f"with {margin:.0f} mm margin even rotated; the structural split must be re-planned for this bed"
            )

    remaining = sorted(bodies, key=lambda b: (-(b.width * b.depth), b.body_id))
    plates: list[Plate] = []
    while remaining:
        free: list[Rect] = [(ux0 + margin, uy0 + margin, bed_x - 2 * margin, bed_y - 2 * margin)]
        for ex, padded in excludes:
            pad = gap if padded else 0.0
            free = _carve(free, (ex[0] - pad, ex[1] - pad, ex[2] + pad, ex[3] + pad))
        plate = Plate(index=len(plates) + 1)
        for body in list(remaining):
            pad = support_gap if body.needs_support else 0.0
            best: tuple[tuple[float, float, float], int, float, float, float, float, list[Rect]] | None = None
            for rot, (pw, pd) in ((0, (body.width, body.depth)), (90, (body.depth, body.width))):
                fw, fd = pw + 2 * pad, pd + 2 * pad
                for fx, fy, frw, frh in free:
                    if fw > frw or fd > frh:
                        continue
                    for x, y in ((fx, fy), (fx + frw - fw, fy), (fx, fy + frh - fd), (fx + frw - fw, fy + frh - fd)):
                        nxt = _carve(free, (x - gap, y - gap, x + fw + gap, y + fd + gap))
                        biggest = max((r[2] * r[3] for r in nxt), default=0.0)
                        score = (-biggest, y, x)
                        if best is None or score < best[0]:
                            best = (score, rot, x + pad, y + pad, pw, pd, nxt)
            if best is None:
                continue
            _, rot, x, y, pw, pd, free = best
            plate.placements.append(Placement(body, rot, x, y, pw, pd))
            remaining.remove(body)
        if not plate.placements:
            raise AssertionError("packing made no progress")
        plates.append(plate)
    return plates


# ---------------------------------------------------------------- bambu cli

def _run_cli(app: Path, args: list[str], log: Path) -> dict[str, Any]:
    exe = app / "Contents" / "MacOS" / "BambuStudio"
    result = subprocess.run([str(exe), *args], check=False, capture_output=True, text=True)
    log.write_text(result.stdout + result.stderr)
    return {"returncode": result.returncode}


def _patch_project(project: Path, support_bodies: set[str], machine: dict[str, Any]) -> int:
    """Patch the pass-1 project: per-object support in model_settings.config,
    and `extruder_nozzle_stats` in project_settings.config, which the CLI
    export omits but multi-extruder machines (H2D/H2S) require on reload."""
    with zipfile.ZipFile(project) as zf:
        entries = {info.filename: zf.read(info.filename) for info in zf.infolist()}

    settings = json.loads(entries["Metadata/project_settings.config"].decode("utf-8"))
    if not settings.get("extruder_nozzle_stats"):
        volumes = machine.get("nozzle_volume_type") or ["Standard"] * len(machine.get("extruder_type") or ["Direct Drive"])
        settings["extruder_nozzle_stats"] = [f"{v}#1" for v in volumes]
        entries["Metadata/project_settings.config"] = json.dumps(settings, indent=4).encode("utf-8")

    config = entries["Metadata/model_settings.config"].decode("utf-8")
    patched = 0

    def _patch(match: re.Match[str]) -> str:
        nonlocal patched
        block = match.group(0)
        name = re.search(r'<metadata key="name" value="([^"]*)"', block)
        if not name:
            return block
        body_id = Path(name.group(1)).stem
        if body_id in support_bodies:
            patched += 1
            inject = (
                '<metadata key="enable_support" value="1"/>\n'
                '    <metadata key="support_type" value="normal(auto)"/>\n'
                '    <metadata key="support_on_build_plate_only" value="1"/>\n    <part'
            )
            return block.replace("<part", inject, 1)
        return block

    config = re.sub(r'<object id="\d+">.*?</object>', _patch, config, flags=re.S)
    entries["Metadata/model_settings.config"] = config.encode("utf-8")
    tmp = project.with_suffix(".patched.3mf")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, payload in entries.items():
            zf.writestr(name, payload)
    tmp.replace(project)
    return patched


def slice_plate(
    *,
    app: Path,
    plate: Plate,
    out_dir: Path,
    settings: list[Path],
    filament: Path,
    work: Path,
    machine: dict[str, Any],
) -> dict[str, Any]:
    plate_dir = work / plate.name
    plate_dir.mkdir(parents=True, exist_ok=True)
    stls: list[Path] = []
    for placement in plate.placements:
        dst = plate_dir / f"{placement.body.body_id}.stl"
        _write_placed_stl(placement.body.stl, dst, placement)
        stls.append(dst)

    load = ";".join(str(p) for p in settings)
    pass1 = _run_cli(
        app,
        ["--load-settings", load, "--load-filaments", str(filament), "--arrange", "0", "--orient", "0",
         "--ensure-on-bed", "--export-3mf", "project.3mf", "--outputdir", str(plate_dir), "--debug", "1",
         *[str(p) for p in stls]],
        plate_dir / "pass1.log",
    )
    project = plate_dir / "project.3mf"
    if pass1["returncode"] != 0 or not project.exists():
        raise RuntimeError(f"{plate.name}: Bambu Studio project export failed (see {plate_dir / 'pass1.log'})")

    support_bodies = {p.body.body_id for p in plate.placements if p.body.needs_support}
    patched = _patch_project(project, support_bodies, machine)
    if patched != len(support_bodies):
        raise RuntimeError(f"{plate.name}: patched {patched} support objects, expected {len(support_bodies)}")

    sliced_name = f"{plate.name}.gcode.3mf"
    pass2 = _run_cli(
        app,
        ["--load-settings", load, "--load-filaments", str(filament), "--arrange", "0", "--orient", "0",
         "--slice", "0", "--export-3mf", sliced_name, "--outputdir", str(plate_dir), "--debug", "1", str(project)],
        plate_dir / "pass2.log",
    )
    result_path = plate_dir / "result.json"
    result = json.loads(result_path.read_text()) if result_path.exists() else {}
    log_dir = out_dir / "logs" / plate.name
    log_dir.mkdir(parents=True, exist_ok=True)
    for name in ("pass1.log", "pass2.log", "result.json"):
        if (plate_dir / name).exists():
            shutil.copy2(plate_dir / name, log_dir / name)
    if pass2["returncode"] != 0 or result.get("return_code") != 0:
        raise RuntimeError(f"{plate.name}: slice failed: {result.get('error_string', pass2)} (see {log_dir / 'pass2.log'})")

    sliced = plate_dir / sliced_name
    gcode = plate_dir / "plate_1.gcode"
    _stamp_printer_model_id(sliced, app, machine)
    shutil.copy2(sliced, out_dir / sliced_name)
    shutil.copy2(gcode, out_dir / f"{plate.name}.gcode")
    shutil.copy2(project, out_dir / f"{plate.name}.3mf")

    sliced_plate = result["sliced_plates"][0]
    objects = {Path(o["name"]).stem: o for o in sliced_plate["objects"]}
    if set(objects) != {p.body.body_id for p in plate.placements}:
        raise RuntimeError(f"{plate.name}: sliced object set differs from the packing plan")
    for placement in plate.placements:
        bb = objects[placement.body.body_id]["bbox"]
        if abs(bb["x"] - placement.x_min) > 0.5 or abs(bb["y"] - placement.y_min) > 0.5:
            raise RuntimeError(
                f"{plate.name}: {placement.body.body_id} landed at ({bb['x']:.2f}, {bb['y']:.2f}) "
                f"but was planned at ({placement.x_min:.2f}, {placement.y_min:.2f})"
            )
    return {
        "gcode_3mf": sliced_name,
        "gcode": f"{plate.name}.gcode",
        "project": f"{plate.name}.3mf",
        "gcode_3mf_sha256": _sha256(out_dir / sliced_name),
        "gcode_sha256": _sha256(out_dir / f"{plate.name}.gcode"),
        "estimated_seconds": sliced_plate.get("total_predication"),
        "filament_g": sum(f.get("total_used_g", 0.0) for f in sliced_plate.get("filaments", [])),
        "support_seconds": sliced_plate.get("generate_support_material_time"),
        "warning": sliced_plate.get("warning_message", ""),
        "objects": {k: v["bbox"] for k, v in objects.items()},
    }


# ---------------------------------------------------------------- outputs

def _fmt_hms(seconds: float | None) -> str:
    if not seconds:
        return "?"
    s = int(seconds)
    return f"{s // 3600}h{(s % 3600) // 60:02d}m"


def write_readme(out_dir: Path, manifest: dict[str, Any]) -> None:
    p = manifest["printer"]
    lines = [
        f"# Aevum row coupon — Bambu Lab {p['model']} / PLA, fewest-plates packing",
        "",
        f"- Machine preset: `{p['machine_preset']}` (bed {p['bed_x_mm']:.0f} x {p['bed_y_mm']:.0f} x {p['bed_z_mm']:.0f} mm; "
        f"packed into x {p['usable_area_mm'][0]:.0f}-{p['usable_area_mm'][2]:.0f}, y {p['usable_area_mm'][1]:.0f}-{p['usable_area_mm'][3]:.0f}, "
        f"the area every nozzle can reach, minus {len(p['exclusion_zones_mm'])} exclusion zone(s))",
        f"- Process base: `{p['process_preset']}` with overrides: 0.20 mm layers, 3 walls, 20% gyroid, 5 top / 4 bottom, 3 mm auto brim, no global support",
        f"- Filament base: `{p['filament_preset']}` with overrides: {manifest['filament']['nozzle_c']} C nozzle, "
        f"{manifest['filament']['first_layer_nozzle_c']} C first layer, {manifest['filament']['bed_c']} C bed on {manifest['filament']['bed_type']}, "
        f"volumetric cap {manifest['filament']['max_volumetric_mm3_s']} mm³/s (≈{manifest['filament']['equivalent_speed_mm_s']:.0f} mm/s at 0.42 x 0.2)",
        f"- Packing: {manifest['packing']['margin_mm']:.0f} mm bed margin, {manifest['packing']['gap_mm']:.0f} mm object gap, 0/90° rotation only, "
        "functional Z axis preserved",
        f"- Sliced by BambuStudio {manifest['slicer']['version']} headless; presets flattened from the app bundle and stored beside this file",
        f"- Identity: every STL hashed against `docs/assembly/artifact_authority.json`; dispositions from `{manifest['authority']['mk4_manifest']}`",
        f"- {manifest['counts']['plates']} plates carry all {manifest['counts']['rigid_bodies']} rigid PLA bodies. "
        f"Auto build-plate-only support is enabled per object for the {len(manifest['support_bodies'])} bodies the MK4 package sliced with support "
        "(structural halves, deck pods, relief cap, lid shrouds); the 23 fine harness/service bodies stay support-free.",
        "- Dispositions are carried over unchanged from the MK4 package: `hold` bodies are still HOLD, they are just co-packed. "
        "Plates mix dispositions, so a held body on a plate does not by itself block the plate; decide per plate before printing.",
        "- Send `<plate>.gcode.3mf` to the printer (Bambu Studio, Handy, or SD card). `<plate>.3mf` is the un-sliced project for edits.",
        "- Not covered: 8 flexible gaskets, COTS plates/mats, electronics, tubing, cables.",
        "",
        "| Plate | Bodies | Est. time | Filament | Dispositions | Files |",
        "|---|---:|---:|---:|---|---|",
    ]
    for plate in manifest["plates"]:
        dispositions = sorted({b["disposition"] for b in plate["bodies"]})
        lines.append(
            f"| `{plate['plate_name']}` | {len(plate['bodies'])} | {_fmt_hms(plate['slice']['estimated_seconds'])} | "
            f"{plate['slice']['filament_g']:.0f} g | {', '.join(dispositions)} | `{plate['slice']['gcode_3mf']}` |"
        )
        for b in plate["bodies"]:
            rot = " · rotated 90°" if b["rotation_z_deg"] else ""
            sup = " · support" if b["support"] else ""
            lines.append(
                f"| &nbsp;&nbsp;`{b['release_body_id']}` |  |  |  | {b['disposition']} | "
                f"{b['footprint_mm'][0]:.1f} x {b['footprint_mm'][1]:.1f} mm at ({b['x_min_mm']:.1f}, {b['y_min_mm']:.1f}){rot}{sup} |"
            )
    (out_dir / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--printer", choices=sorted(PRINTERS), default="p1s")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=None, help="default outputs/sliced/bambu_<printer>_pla")
    parser.add_argument("--authority", type=Path, default=DEFAULT_AUTHORITY)
    parser.add_argument("--mk4-manifest", type=Path, default=DEFAULT_MK4_MANIFEST)
    parser.add_argument("--bambu-app", type=Path, default=DEFAULT_BAMBU_APP)
    parser.add_argument("--margin", type=float, default=3.0, help="bed edge margin, mm")
    parser.add_argument("--gap", type=float, default=7.0, help="object-to-object gap, mm (two 3 mm brims plus clearance)")
    parser.add_argument("--support-gap", type=float, default=0.0, help="extra clearance around support-enabled bodies, mm; build-plate-only normal support stays inside the body footprint, so 0 by default")
    parser.add_argument("--nozzle-c", type=int, default=205)
    parser.add_argument("--first-layer-nozzle-c", type=int, default=210)
    parser.add_argument("--bed-c", type=int, default=60)
    parser.add_argument("--max-speed", type=float, default=70.0, help="MK4-equivalent speed cap, mm/s, applied as a volumetric limit")
    parser.add_argument("--bed-type", default="Textured PEI Plate", help="Bambu plate type written into the project (bed temp is forced to --bed-c for every plate type)")
    parser.add_argument("--plan-only", action="store_true", help="print the packing plan and exit without slicing")
    args = parser.parse_args()

    printer = PRINTERS[args.printer]
    out_dir = args.output_dir or ROOT / "outputs" / "sliced" / f"bambu_{args.printer}_pla"
    if not args.plan_only:
        if out_dir.exists():
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            out_dir.rename(out_dir.with_name(f".{out_dir.name}.previous_{stamp}"))
        out_dir.mkdir(parents=True)

    machine = flatten_preset(args.bambu_app, printer["machine"])
    process = flatten_preset(args.bambu_app, printer["process"])
    filament = flatten_preset(args.bambu_app, printer["filament"])
    process.update(PROCESS_OVERRIDES)
    volumetric = round(0.42 * 0.2 * args.max_speed, 1)
    bed_temp_keys = [
        k for k in filament
        if k.endswith("_plate_temp") or k.endswith("_plate_temp_initial_layer")
    ]
    def _override(key: str, value: Any) -> None:
        # Multi-extruder presets (H2D/H2S) carry one entry per extruder
        # variant; keep the list length so the filament still maps.
        current = filament.get(key)
        width = len(current) if isinstance(current, list) and current else 1
        filament[key] = [str(value)] * width

    for key in bed_temp_keys:
        _override(key, args.bed_c)
    _override("nozzle_temperature", args.nozzle_c)
    _override("nozzle_temperature_initial_layer", args.first_layer_nozzle_c)
    _override("filament_max_volumetric_speed", volumetric)
    process["curr_bed_type"] = args.bed_type
    bed = _bed_from_machine(machine)
    bed_x, bed_y, bed_z = bed["bed_x"], bed["bed_y"], bed["bed_z"]
    usable = bed["usable"]

    bodies = load_bodies(args.input_dir, args.authority, args.mk4_manifest)
    plates = pack_bodies(
        bodies, usable=usable, bed_z=bed_z, margin=args.margin, gap=args.gap,
        support_gap=args.support_gap, excludes=bed["excludes"],
    )
    print(
        f"{args.printer}: bed {bed_x:.0f} x {bed_y:.0f} mm, usable x {usable[0]:.0f}-{usable[2]:.0f} y {usable[1]:.0f}-{usable[3]:.0f}"
        f" ({bed['extruders']} extruder{'s' if bed['extruders'] > 1 else ''}, {len(bed['excludes'])} exclusion zones), "
        f"{len(bodies)} bodies -> {len(plates)} plates"
    )
    for plate in plates:
        print(f"  {plate.name}: {len(plate.placements)} bodies")
        for pl in plate.placements:
            print(f"    {pl.body.body_id:<75} {pl.footprint_x:6.1f} x {pl.footprint_y:6.1f} at ({pl.x_min:6.1f}, {pl.y_min:6.1f}) rot {pl.rotation_z_deg:>2} {pl.body.disposition}")
    if args.plan_only:
        return

    preset_dir = out_dir / "presets"
    preset_dir.mkdir()
    machine_path = preset_dir / "machine.json"
    process_path = preset_dir / "process.json"
    filament_path = preset_dir / "filament.json"
    machine_path.write_text(json.dumps(machine, indent=1))
    process_path.write_text(json.dumps(process, indent=1))
    filament_path.write_text(json.dumps(filament, indent=1))

    plate_records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="aevum-bambu-") as tmp:
        work = Path(tmp)
        for plate in plates:
            print(f"slicing {plate.name} ...", flush=True)
            slice_info = slice_plate(
                app=args.bambu_app, plate=plate, out_dir=out_dir,
                settings=[machine_path, process_path], filament=filament_path, work=work, machine=machine,
            )
            plate_records.append({
                "plate_id": f"plate_{plate.index:02d}",
                "plate_name": plate.name,
                "bodies": [
                    {
                        "release_body_id": pl.body.body_id,
                        "source_artifact_id": pl.body.source_artifact,
                        "disposition": pl.body.disposition,
                        "stl_sha256": pl.body.sha256,
                        "rotation_z_deg": pl.rotation_z_deg,
                        "x_min_mm": round(pl.x_min, 3),
                        "y_min_mm": round(pl.y_min, 3),
                        "footprint_mm": [round(pl.footprint_x, 3), round(pl.footprint_y, 3), round(pl.body.height, 3)],
                        "support": pl.body.needs_support,
                    }
                    for pl in plate.placements
                ],
                "slice": slice_info,
            })
            print(f"  {plate.name}: {_fmt_hms(slice_info['estimated_seconds'])}, {slice_info['filament_g']:.0f} g")

    manifest = {
        "schema_version": 1,
        "package_id": f"row_coupon_bambu_{args.printer}_pla",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "authority": {
            "artifact_registry": str(args.authority.relative_to(ROOT)) if args.authority.is_relative_to(ROOT) else str(args.authority),
            "artifact_registry_sha256": _sha256(args.authority),
            "mk4_manifest": str(args.mk4_manifest.relative_to(ROOT)) if args.mk4_manifest.is_relative_to(ROOT) else str(args.mk4_manifest),
            "mk4_manifest_sha256": _sha256(args.mk4_manifest),
            "manufacturing_evidence_only": True,
            "operator_release_granted": False,
        },
        "slicer": {"application": "BambuStudio", "version": _bambu_version(args.bambu_app), "app": str(args.bambu_app)},
        "printer": {
            "key": args.printer,
            "model": machine.get("printer_model"),
            "machine_preset": printer["machine"],
            "process_preset": printer["process"],
            "filament_preset": printer["filament"],
            "bed_x_mm": bed_x, "bed_y_mm": bed_y, "bed_z_mm": bed_z,
            "usable_area_mm": list(usable),
            "exclusion_zones_mm": [list(e) for e, _ in bed["excludes"]],
            "extruders": bed["extruders"],
        },
        "filament": {
            "bed_type": args.bed_type, "nozzle_c": args.nozzle_c, "first_layer_nozzle_c": args.first_layer_nozzle_c, "bed_c": args.bed_c,
            "max_volumetric_mm3_s": volumetric, "equivalent_speed_mm_s": args.max_speed,
        },
        "packing": {"margin_mm": args.margin, "gap_mm": args.gap, "support_gap_mm": args.support_gap, "rotations_deg": [0, 90]},
        "counts": {"plates": len(plates), "rigid_bodies": len(bodies)},
        "support_bodies": sorted(b.body_id for b in bodies if b.needs_support),
        "plates": plate_records,
    }
    (out_dir / "package_manifest.json").write_text(json.dumps(manifest, indent=1))
    write_readme(out_dir, manifest)
    print(f"wrote {out_dir}")


if __name__ == "__main__":
    sys.exit(main())
