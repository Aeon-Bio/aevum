"""Build the Row Coupon Print Kit viewer bundle into outputs/print_kit/.

    uv run python scripts/build_row_coupon_print_kit.py

Writes index.html (copied from cad/print_kit/index.html), meta.json, assembly.gltf.json,
envelopes.gltf.json (the validation envelopes, drawn as ghosts) and one
plates_<printer>.gltf.json per slicer package. The bundle is what gets published
as the Row Coupon Print Kit artifact; regenerate it whenever the model or a slicer
package changes. See src/aevum_cad/row_coupon/print_kit.py for where every field comes from.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon.assembly import (
    build_row_coupon_installed_parts,
    build_row_coupon_validation_parts,
)
from aevum_cad.row_coupon.final_print_pieces import realize_row_coupon_final_print_pieces
from aevum_cad.row_coupon.print_kit import (
    LAYOUTS,
    GltfWriter,
    build_layout,
    classify_parts,
    install_states,
    lens_membership,
    load_part_options,
    read_slicer_package,
    release_body_to_installed_part,
    stl_sha256,
    tessellate,
    verify_package,
)

TOLERANCE_MM = 0.08
GHOST_RGB = (0.45, 0.5, 0.58)  # envelopes with no colour in PART_OPTIONS
ANGULAR_RAD = 0.35


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_revision() -> str:
    try:
        rev = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--", "src", "cad", "docs/assembly"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return rev + ("+dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _write_json(path: Path, payload: object) -> int:
    text = json.dumps(payload, separators=(",", ":"))
    path.write_text(text)
    return len(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("params", nargs="?", default=ROOT / "cad" / "one_row_coupon.params.json")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs" / "print_kit")
    args = parser.parse_args()

    params_path = Path(args.params)
    params = load_params(params_path)
    registry_path = ROOT / "docs" / "assembly" / "artifact_authority.json"
    registry = json.loads(registry_path.read_text())
    sequence = json.loads(
        (ROOT / "docs" / "assembly" / "sequence_and_split_matrix.json").read_text()
    )
    options = load_part_options(ROOT / "cad" / "view_one_row_coupon.py")
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    # ---- installed assembly (live model)
    print("building installed parts ...", flush=True)
    installed = build_row_coupon_installed_parts(params)
    classes = classify_parts(list(installed), registry)
    states = install_states(sequence)
    asm = GltfWriter(params["name"])
    assembly_meta = []
    part_rgb: dict[str, list[float]] = {}
    for name, wp in installed.items():
        opt = options.get(name)
        if opt is None:
            raise SystemExit(
                f"no colour for installed part {name!r} in cad/view_one_row_coupon.py PART_OPTIONS"
            )
        rgb = [float(c) for c in opt["color"]]
        alpha = float(opt.get("alpha", 1.0))
        part_rgb[name] = rgb
        mesh = tessellate(wp, TOLERANCE_MM, ANGULAR_RAD)
        asm.add(name, mesh, (*rgb, alpha))
        assembly_meta.append(
            {
                "name": name,
                "rgb": rgb,
                "alpha": alpha,
                "triangles": int(len(mesh.triangles)),
                "bbox": mesh.bbox,
                "printed": classes[name] == "printed",
                "class": classes[name],
                "install_state": states.get(name),
            }
        )
        print(f"  {name:42s} {classes[name]:11s} {len(mesh.triangles):7d} tris", flush=True)
    size = _write_json(out / "assembly.gltf.json", asm.to_json())
    print(f"assembly.gltf.json {size / 1e6:.2f} MB")

    # ---- validation envelopes (reserved space, drawn as ghosts), and the lenses over both
    print("building validation envelopes ...", flush=True)
    envelopes = build_row_coupon_validation_parts(params)
    env_gltf = GltfWriter(f"{params['name']}_validation")
    envelope_meta = []
    for name, wp in envelopes.items():
        opt = options.get(name, {"color": GHOST_RGB, "alpha": 0.1})
        rgb = [float(c) for c in opt["color"]]
        mesh = tessellate(wp, TOLERANCE_MM, ANGULAR_RAD)
        env_gltf.add(name, mesh, (*rgb, 0.1))
        envelope_meta.append({"name": name, "rgb": rgb, "bbox": mesh.bbox})
    size = _write_json(out / "envelopes.gltf.json", env_gltf.to_json())
    print(f"envelopes.gltf.json {size / 1e6:.2f} MB  {len(envelope_meta)} envelopes")
    lenses = lens_membership(classes, list(envelopes), sequence)
    for entry in (*assembly_meta, *envelope_meta):
        entry["lenses"] = [
            lens["key"] for lens in lenses if entry["name"] in (*lens["parts"], *lens["envelopes"])
        ]

    # ---- print bodies (live model), verified against every slicer package
    print("realizing final print pieces ...", flush=True)
    realization = realize_row_coupon_final_print_pieces(params)
    realization.require_printable()
    pieces = dict(realization.pieces)
    live_sha = {name: stl_sha256(wp) for name, wp in pieces.items()}
    local_meshes = {name: tessellate(wp, TOLERANCE_MM, ANGULAR_RAD) for name, wp in pieces.items()}
    installed_part_of = release_body_to_installed_part(registry)

    layouts = []
    refused = []
    for spec in LAYOUTS:
        package_dir = ROOT / "outputs" / "sliced" / spec["dir"]
        if not (package_dir / "package_manifest.json").exists():
            refused.append(f"{spec['label']}: no package at {package_dir.relative_to(ROOT)}")
            continue
        package = read_slicer_package(package_dir)
        stale = verify_package(package, live_sha)
        if stale:
            refused.append(
                f"{spec['label']}: {len(stale)} bodies no longer match the live model "
                f"(re-slice it): {stale[:4]}{' ...' if len(stale) > 4 else ''}"
            )
            continue
        layout, writer = build_layout(spec, package, local_meshes, installed_part_of, part_rgb)
        size = _write_json(out / layout["file"], writer.to_json())
        layouts.append(layout)
        print(
            f"{layout['file']:24s} {size / 1e6:.2f} MB  {len(layout['plates'])} plates, "
            f"{len(layout['pieces'])} bodies, slice verified"
        )
    for line in refused:
        print(f"REFUSED {line}", file=sys.stderr)
    if not layouts:
        raise SystemExit(
            "no slicer package matches the live model; nothing to show on the Print plates tab"
        )

    meta = {
        "schema_version": 3,
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "source_revision": _git_revision(),
        "params_sha256": _sha256(params_path),
        "artifact_registry_sha256": _sha256(registry_path),
        "counts": {
            "installed_parts": len(assembly_meta),
            "printed_parts": sum(a["printed"] for a in assembly_meta),
            "rigid_bodies": len(pieces),
            "layouts": len(layouts),
            "envelopes": len(envelope_meta),
        },
        "assembly_states": [
            {
                "state_id": s["state_id"],
                "install_families": s["install_families"],
                "status": s["status"],
                "label": s["state_id"].split("_", 1)[1].replace("_", " "),
            }
            for s in sequence["assembly_states"]
        ],
        "service_paths": [
            {
                "path_id": p["path_id"],
                "families": p["affected_installed_families"],
                "motion": p["nominal_motion"],
                "status": p["status"],
                "missing_proof": p.get("missing_proof", []),
            }
            for p in sequence["service_paths"]
        ],
        "lenses": [
            {k: lens[k] for k in ("key", "label", "question", "centre", "parts", "envelopes")}
            for lens in lenses
        ],
        "envelopes": envelope_meta,
        "assembly": assembly_meta,
        "layouts": layouts,
        "refused_layouts": refused,
    }
    _write_json(out / "meta.json", meta)
    shutil.copyfile(ROOT / "cad" / "print_kit" / "index.html", out / "index.html")
    print(f"wrote {out.relative_to(ROOT)}/ ({len(layouts)} plate layouts, {len(refused)} refused)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
