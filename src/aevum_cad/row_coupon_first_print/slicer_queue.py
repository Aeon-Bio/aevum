"""First-print slicer-queue (+ package/queue manifest markdown) family, extracted verbatim.

Single owner of ``first_print_slicer_queue_artifacts`` / ``first_print_slicer_queue_manifest_items``
(the cross-module queue-source helpers bed_fit + slicer consume). Builds the slicer input queue
(STL list + sha256 hashes) for monolithic + final-piece modes and the package/queue manifest
markdown.
The install/service worksheet-row helpers it calls in ``first_print_package_manifest_markdown`` are
not yet extracted this cycle; they are late-bound into this module's globals by the facade via
``_bind_facade_deferred`` (same partially-initialized-module-cycle reason as ``gates``). Function
bodies stay byte-identical.
"""

from __future__ import annotations

from pathlib import Path
from shutil import copy2
from typing import Any

from aevum_cad.row_coupon import (
    row_coupon_final_print_piece_plan,
    row_coupon_part_manifest,
    row_coupon_physical_artifact_manifest,
)

from .bed_fit import (
    audit_first_print_final_piece_artifacts,
)
from .cad_targets import first_print_qc_targets
from .common import (
    _artifact_path,
    _artifact_presence,
    _markdown_table_cells,
    file_sha256,
)
from .constants import FIRST_PRINT_PHYSICAL_GATES
from .gates import (
    first_print_gate1_qc_worksheet_rows,
    first_print_gate2_dry_assembly_worksheet_rows,
    first_print_gate3_placement_worksheet_rows,
    first_print_gate4_wet_dry_witness_worksheet_rows,
    first_print_gate5_consumable_puncture_worksheet_rows,
    first_print_gate6_sensor_thermal_worksheet_rows,
)
from .models import (
    FirstPrintArtifact,
    FirstPrintGate1QCWorksheetRow,
    FirstPrintPackageAudit,
    FirstPrintQCTarget,
    FirstPrintSlicedOutputRow,
    FirstPrintSlicerQueueAudit,
    FirstPrintSlicerQueueHashMismatch,
    FirstPrintSlicerQueueItem,
)
from .package import artifact_category, audit_first_print_package

# Install/service worksheet-row helpers referenced by ``first_print_package_manifest_markdown``;
# not extracted this cycle, late-bound by the facade via ``_bind_facade_deferred``.
_FACADE_DEFERRED = (
    "first_print_install_inventory_rows",
    "first_print_service_state_review_rows",
)

first_print_install_inventory_rows = None  # bound by facade _bind_facade_deferred
first_print_service_state_review_rows = None  # bound by facade _bind_facade_deferred


def _bind_facade_deferred(facade) -> None:
    """Late-bind facade-owned install/service row helpers into this module's globals."""
    module_globals = globals()
    for name in _FACADE_DEFERRED:
        module_globals[name] = getattr(facade, name)


def _target_lookup(params: dict[str, Any]) -> dict[str, FirstPrintQCTarget]:
    return {target.name: target for target in first_print_qc_targets(params)}








def _nonprinted_model_use_and_install_requirement(
    artifact: FirstPrintArtifact,
) -> tuple[str, str]:
    if artifact.category == "cots_consumable":
        return (
            "dimensional reference only",
            "install real COTS consumable; dimensional blank not accepted",
        )
    if artifact.category == "service_tubing":
        return (
            "route and bend reference",
            "install real tubing or measured replacement with evidence",
        )
    if artifact.category == "electronics_or_dimensional_blank":
        return (
            "dry-fit blank or real package reference",
            "dimensional blank supports Gates 2-5 only; real part required "
            "for Gate 6 and operating acceptance",
        )
    return ("reference only", "explicit install decision required")


def first_print_package_manifest_markdown(
    params: dict[str, Any],
    audit: FirstPrintPackageAudit,
) -> str:
    manifest = row_coupon_part_manifest()
    production_manifest = row_coupon_physical_artifact_manifest(params)
    final_piece_sources = {
        str(row["name"]): str(row["source_artifact"])
        for row in row_coupon_final_print_piece_plan(params)
    }
    policy = manifest["policy"]
    forbidden_authority = ", ".join(
        f"`{term}`" for term in policy["forbidden_retention_authority_terms"]
    )
    targets = _target_lookup(params)
    printed = [
        artifact
        for artifact in audit.production_artifacts
        if artifact.category == "printed"
    ]
    flexible = [
        artifact
        for artifact in audit.production_artifacts
        if artifact.category == "compressible_or_flexible"
    ]
    nonprinted = []
    for name, entry in manifest["installed"].items():
        category = artifact_category(entry["fabrication_source"])
        if category not in {
            "cots_consumable",
            "electronics_or_dimensional_blank",
            "service_tubing",
        }:
            continue
        stl_path = audit.out_dir / f"{audit.name}_{name}.stl"
        step_path = audit.out_dir / f"{audit.name}_{name}.step"
        nonprinted.append(
            FirstPrintArtifact(
                name=name,
                category=category,
                stl_path=stl_path,
                step_path=step_path,
                stl_exists=stl_path.exists(),
                step_exists=step_path.exists(),
                fabrication_source=entry["fabrication_source"],
                role=entry["role"],
            )
        )

    lines = [
        f"# {audit.name} First-Print Package Manifest",
        "",
        "This is a print/procurement handoff for the production-operating one-row",
        "coupon. It separates slicer-ready printed parts from flexible seal parts,",
        "COTS/electronics/service items, and validation-only bodies.",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| CAD package audit ready | {'true' if audit.ready else 'false'} |",
        f"| Assembly STEP | {_artifact_path(audit.assembly_step)} |",
        f"| Printed slicer parts | {len(printed)} |",
        f"| Flexible/compressible parts | {len(flexible)} |",
        f"| COTS/electronics/service items | {len(nonprinted)} |",
        f"| Required validation bodies | {len(audit.validation_artifacts)} |",
        f"| Optional validation bodies | {len(audit.optional_validation_artifacts)} |",
        f"| Assembly policy | `{policy['assembly_rule']}` |",
        "| Material authority decision | "
        f"`{policy['material_authority_decision_date']} "
        f"{policy['material_authority_decision']}` |",
        f"| Supersedes older insert strategy | `{policy['supersedes_material_strategy']}` |",
        f"| Nonprinted exception policy | `{policy['nonprinted_parts']}` |",
        f"| Forbidden retention authority | {forbidden_authority} |",
        "",
        "## Operating Readiness Scope",
        "",
        "Package readiness only verifies CAD output presence and handoff scope.",
        "It does not mark any physical gate or operating acceptance row as passed.",
        "",
        "| Evidence set | Generated scope | Acceptance rule |",
        "|---|---:|---|",
        "| Service-state review | "
        f"{len(first_print_service_state_review_rows())} viewer modes | "
        "every installed, service, bench-only, and fail-closed review mode must "
        "pass before preflight closes |",
        f"| Gate 1 Print QC | {len(first_print_gate1_qc_worksheet_rows(params))} rows | "
        "every printed or flexible part row requires measurements and evidence |",
        "| Gate 2 Dry Assembly Fit | "
        f"{len(first_print_gate2_dry_assembly_worksheet_rows(params))} rows | "
        "requires Gate 1 print QC, install inventory, service-state review, and "
        "all dry-assembly target evidence |",
        "| Gate 3 OT-2 Placement And No-Motion Clearance | "
        f"{len(first_print_gate3_placement_worksheet_rows(params))} rows | "
        "requires Gate 2 readiness plus deck placement and no-motion clearance "
        "evidence |",
        "| Gate 4 Passive Leak And Wet/Dry Witness | "
        f"{len(first_print_gate4_wet_dry_witness_worksheet_rows(params))} rows | "
        "requires Gate 3 readiness plus wet/dry boundary and witness evidence |",
        "| Gate 5 Consumable And Puncture Link | "
        f"{len(first_print_gate5_consumable_puncture_worksheet_rows(params))} rows | "
        "requires Gate 4 readiness plus real consumables and puncture evidence |",
        "| Gate 6 Sensor And Thermal Link | "
        f"{len(first_print_gate6_sensor_thermal_worksheet_rows(params))} rows | "
        "requires Gate 5 readiness, real sensor inventory, powered sensor "
        "evidence, and thermal-proxy evidence |",
        f"| Install inventory | {len(first_print_install_inventory_rows())} rows | "
        "COTS consumables, service tubing, electronics, and sensor items must "
        "match their operating requirements; dimensional blanks cannot support "
        "Gate 6 or operating acceptance |",
        f"| Operating prototype acceptance | {len(FIRST_PRINT_PHYSICAL_GATES)} gates | "
        "requires preflight artifacts, print-start readiness, service-state "
        "review, the full physical gate chain, and real sensor inventory |",
        "",
        "## Slicer Queue: Printed Polymer Parts",
        "",
        "Print these production STLs. Do not add metal, glue, or hidden bonded",
        "authority to make them pass Gate 1.",
        "",
        "| Part | STL | STEP | Target X mm | Target Y mm | Target Z mm | Presence | Role |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for artifact in printed:
        target = targets[artifact.name]
        lines.append(
            "| "
            f"`{artifact.name}` | {_artifact_path(artifact.stl_path)} | "
            f"{_artifact_path(artifact.step_path)} | {target.target_x_mm:.2f} | "
            f"{target.target_y_mm:.2f} | {target.target_z_mm:.2f} | "
            f"{_artifact_presence(artifact)} | {artifact.role} |"
        )

    lines.extend(
        [
            "",
            "## Flexible Or Compressible Parts",
            "",
            "Make or procure these as compliant seal parts. Their CAD bounds are nominal",
            "uncompressed targets until real stock or printed TPU is measured.",
            "",
            "| Part | STL | STEP | Target X mm | Target Y mm | Target Z mm | Presence | Role |",
            "|---|---|---|---:|---:|---:|---|---|",
        ]
    )
    for artifact in flexible:
        target = targets[artifact.name]
        lines.append(
            "| "
            f"`{artifact.name}` | {_artifact_path(artifact.stl_path)} | "
            f"{_artifact_path(artifact.step_path)} | {target.target_x_mm:.2f} | "
            f"{target.target_y_mm:.2f} | {target.target_z_mm:.2f} | "
            f"{_artifact_presence(artifact)} | {artifact.role} |"
        )

    lines.extend(
        [
            "",
            "## Procure Or Install: Do Not Print As Production Parts",
            "",
            "| Part | Category | STL/STEP model use | Operating install requirement | "
            "Presence | Role |",
            "|---|---|---|---|---|---|",
        ]
    )
    for artifact in nonprinted:
        model_use, install_requirement = _nonprinted_model_use_and_install_requirement(
            artifact
        )
        lines.append(
            "| "
            f"`{artifact.name}` | {artifact.category} | {model_use} | "
            f"{install_requirement} | {_artifact_presence(artifact)} | {artifact.role} |"
        )

    lines.extend(
        [
            "",
            "## Operating Material And Exposure Policy",
            "",
            "This classifies installed operating surfaces for first-print handling.",
            "It does not mark BSL1 material, cleaning, leachable, or biological",
            "compatibility evidence as passed.",
            "",
            "Every installed operating surface is listed here, whether or not it is",
            "printed in this batch: a part that is not printed still contacts the",
            "sample and still needs an exposure class. `Provenance` is the",
            "distinction. `printed_in_this_batch` rows are slicer output and carry a",
            "print-piece name; every other row is supplied or procured and is NOT in",
            "the slicer queue.",
            "",
            "| Part | Provenance | Exposure class | Service disposition | Evidence gate |",
            "|---|---|---|---|---|",
        ]
    )
    covered_installed_parts: set[str] = set()
    for artifact in audit.production_artifacts:
        source = final_piece_sources.get(artifact.name, artifact.name)
        entry = production_manifest[source]
        covered_installed_parts.add(str(entry["installed_part"]))
        provenance = (
            "printed_in_this_batch"
            if artifact.category == "printed"
            else f"supplied_{artifact.category}"
        )
        lines.append(
            "| "
            f"`{artifact.name}` | {provenance} | {entry['exposure_class']} | "
            f"{entry['service_disposition']} | {entry['material_evidence_gate']} |"
        )
    for artifact in nonprinted:
        entry = manifest["installed"][artifact.name]
        covered_installed_parts.add(artifact.name)
        lines.append(
            "| "
            f"`{artifact.name}` | not_printed_{artifact.category} | "
            f"{entry['exposure_class']} | {entry['service_disposition']} | "
            f"{entry['material_evidence_gate']} |"
        )
    # Fail closed on coverage.  This table previously iterated release bodies
    # only, so COTS consumables and electronics silently vanished from an
    # operator-facing document while every assertion about it still passed.
    # row_coupon_part_manifest() already guarantees that the material surface
    # policy covers every installed part; this guarantees the rendered table
    # does too, so a part cannot drop out again without failing here.
    uncovered = sorted(set(manifest["installed"]) - covered_installed_parts)
    if uncovered:
        raise ValueError(
            "operating material and exposure policy table does not cover every "
            f"installed part: {uncovered}"
        )

    lines.extend(
        [
            "",
            "## Validation Bodies: Do Not Install As Production Parts",
            "",
            "| Body | Required | STL | STEP | Presence | Role |",
            "|---|---|---|---|---|---|",
        ]
    )
    for artifact in audit.validation_artifacts:
        lines.append(
            "| "
            f"`{artifact.name}` | yes | {_artifact_path(artifact.stl_path)} | "
            f"{_artifact_path(artifact.step_path)} | {_artifact_presence(artifact)} | "
            f"{artifact.role} |"
        )
    for artifact in audit.optional_validation_artifacts:
        lines.append(
            "| "
            f"`{artifact.name}` | optional | {_artifact_path(artifact.stl_path)} | "
            f"{_artifact_path(artifact.step_path)} | {_artifact_presence(artifact)} | "
            f"{artifact.role} |"
        )

    if audit.missing_paths:
        lines.extend(["", "## Missing Required Files", "", "| Path |", "|---|"])
        lines.extend(f"| {_artifact_path(path)} |" for path in audit.missing_paths)
    else:
        lines.extend(["", "Missing required files: none"])

    return "\n".join(lines)


def first_print_slicer_queue_artifacts(
    audit: FirstPrintPackageAudit,
) -> tuple[FirstPrintArtifact, ...]:
    return tuple(
        artifact
        for artifact in audit.production_artifacts
        if artifact.category == "printed"
    )


def first_print_slicer_queue_manifest_markdown(
    *,
    params: dict[str, Any],
    items: tuple[FirstPrintSlicerQueueItem, ...],
    queue_dir: str | Path,
) -> str:
    lines = [
        f"# {params['name']} First-Print Slicer Queue",
        "",
        "This directory contains only printed production STL files for the",
        "one-row coupon first print. Do not add COTS consumables, electronics,",
        "service tubing, flexible seal bodies, or validation bodies to this queue.",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Queue directory | `{Path(queue_dir)}` |",
        f"| Printed slicer queue files | {len(items)} |",
        "",
        "| Part | Queued STL | SHA256 | Target X mm | Target Y mm | Target Z mm | Role |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for item in items:
        lines.append(
            "| "
            f"`{item.name}` | {_artifact_path(item.queue_stl_path)} | "
            f"`{item.sha256}` | {item.target_x_mm:.2f} | "
            f"{item.target_y_mm:.2f} | {item.target_z_mm:.2f} | {item.role} |"
        )
    return "\n".join(lines)




def first_print_slicer_queue_manifest_items(
    queue_dir: str | Path,
) -> tuple[FirstPrintSlicerQueueItem, ...]:
    queue = Path(queue_dir)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    if not manifest.exists():
        return ()
    items: list[FirstPrintSlicerQueueItem] = []
    for line in manifest.read_text().splitlines():
        cells = _markdown_table_cells(line)
        if len(cells) < 7 or not cells[1].strip("`").endswith(".stl"):
            continue
        queue_stl = queue / Path(cells[1].strip("`")).name
        try:
            target_x = float(cells[3])
            target_y = float(cells[4])
            target_z = float(cells[5])
        except ValueError:
            continue
        items.append(
            FirstPrintSlicerQueueItem(
                name=cells[0].strip("`"),
                source_stl_path=queue_stl,
                queue_stl_path=queue_stl,
                sha256=cells[2].strip("`"),
                target_x_mm=target_x,
                target_y_mm=target_y,
                target_z_mm=target_z,
                role=cells[6],
            )
        )
    return tuple(items)


def audit_first_print_slicer_queue_manifest(
    queue_dir: str | Path,
) -> FirstPrintSlicerQueueAudit:
    queue = Path(queue_dir)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    items = first_print_slicer_queue_manifest_items(queue)
    expected_stl_paths = tuple(item.queue_stl_path for item in items)
    expected_path_set = set(expected_stl_paths)
    actual_paths = tuple(sorted(path for path in queue.iterdir())) if queue.exists() else ()
    actual_file_paths = tuple(path for path in actual_paths if path.is_file())
    actual_stl_paths = tuple(path for path in actual_file_paths if path.suffix.lower() == ".stl")
    allowed_paths = {*expected_path_set, manifest}
    extra_paths = tuple(path for path in actual_file_paths if path not in allowed_paths)
    missing_stl_paths = tuple(path for path in expected_stl_paths if not path.exists())
    mismatches: list[FirstPrintSlicerQueueHashMismatch] = []
    for item in items:
        if not item.queue_stl_path.exists():
            continue
        actual_sha = file_sha256(item.queue_stl_path)
        if actual_sha != item.sha256:
            mismatches.append(
                FirstPrintSlicerQueueHashMismatch(
                    path=item.queue_stl_path,
                    expected_sha256=item.sha256,
                    actual_sha256=actual_sha,
                )
            )
    source_issues = () if items else ("slicer queue manifest has no STL rows",)
    return FirstPrintSlicerQueueAudit(
        queue_dir=queue,
        manifest_path=manifest,
        manifest_exists=manifest.exists(),
        expected_stl_paths=expected_stl_paths,
        actual_stl_paths=actual_stl_paths,
        missing_stl_paths=missing_stl_paths,
        extra_paths=extra_paths,
        hash_mismatches=tuple(mismatches),
        package_missing_paths=(),
        source_issues=source_issues,
    )


def first_print_sliced_output_rows_from_slicer_queue_manifest(
    *,
    queue_dir: str | Path,
    selected_setup_summary: str = "",
) -> tuple[FirstPrintSlicedOutputRow, ...]:
    rows: list[FirstPrintSlicedOutputRow] = []
    for item in first_print_slicer_queue_manifest_items(queue_dir):
        rows.append(
            FirstPrintSlicedOutputRow(
                part=item.name,
                queued_stl_path=str(item.queue_stl_path),
                queued_stl_sha256=(
                    file_sha256(item.queue_stl_path)
                    if item.queue_stl_path.exists()
                    else item.sha256
                ),
                selected_setup_summary=selected_setup_summary,
            )
        )
    return tuple(rows)


def first_print_gate1_qc_rows_from_slicer_queue_manifest(
    queue_dir: str | Path,
) -> tuple[FirstPrintGate1QCWorksheetRow, ...]:
    rows: list[FirstPrintGate1QCWorksheetRow] = []
    for item in first_print_slicer_queue_manifest_items(queue_dir):
        source = "printed_final_piece" if "final print piece" in item.role else "printed"
        rows.append(
            FirstPrintGate1QCWorksheetRow(
                part=item.name,
                source=source,
                target_x_mm=item.target_x_mm,
                target_y_mm=item.target_y_mm,
                target_z_mm=item.target_z_mm,
            )
        )
    return tuple(rows)


def prepare_first_print_slicer_queue(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    queue_dir: str | Path,
    overwrite: bool = False,
) -> tuple[FirstPrintSlicerQueueItem, ...]:
    audit = audit_first_print_package(params, out_dir)
    if audit.missing_paths:
        raise FileNotFoundError(audit.missing_paths[0])

    queue = Path(queue_dir)
    queue.mkdir(parents=True, exist_ok=True)
    targets = _target_lookup(params)
    printed_artifacts = first_print_slicer_queue_artifacts(audit)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    if manifest.exists() and not overwrite:
        raise FileExistsError(manifest)
    for artifact in printed_artifacts:
        destination = queue / artifact.stl_path.name
        if destination.exists() and not overwrite:
            raise FileExistsError(destination)

    items: list[FirstPrintSlicerQueueItem] = []
    for artifact in printed_artifacts:
        target = targets[artifact.name]
        destination = queue / artifact.stl_path.name
        copy2(artifact.stl_path, destination)
        items.append(
            FirstPrintSlicerQueueItem(
                name=artifact.name,
                source_stl_path=artifact.stl_path,
                queue_stl_path=destination,
                sha256=file_sha256(destination),
                target_x_mm=target.target_x_mm,
                target_y_mm=target.target_y_mm,
                target_z_mm=target.target_z_mm,
                role=artifact.role,
            )
        )

    manifest.write_text(
        first_print_slicer_queue_manifest_markdown(
            params=params,
            items=tuple(items),
            queue_dir=queue,
        )
    )
    return tuple(items)


def first_print_final_piece_slicer_queue_items(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    piece_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
) -> tuple[FirstPrintSlicerQueueItem, ...]:
    piece_audit = audit_first_print_final_piece_artifacts(
        params=params,
        out_dir=out_dir,
        piece_dir=piece_dir,
        slicer_setup_path=slicer_setup_path,
    )
    targets = _target_lookup(params)

    queue = Path(queue_dir)
    items: list[FirstPrintSlicerQueueItem] = []
    for row in piece_audit.rows:
        target = targets[row.split_part]
        role = target.role
        if row.segment_count > 1:
            role = (
                f"{role}; final print piece "
                f"{row.segment_index}/{row.segment_count} from {row.source_part} at "
                f"{row.interface_zone}"
            )
        items.append(
            FirstPrintSlicerQueueItem(
                name=row.split_part,
                source_stl_path=row.stl_path,
                queue_stl_path=queue / row.stl_path.name,
                sha256=file_sha256(row.stl_path) if row.stl_exists else "",
                target_x_mm=row.target_x_mm,
                target_y_mm=row.target_y_mm,
                target_z_mm=row.target_z_mm,
                role=role,
            )
        )
    return tuple(items)


def prepare_first_print_final_piece_slicer_queue(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    piece_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
    overwrite: bool = False,
) -> tuple[FirstPrintSlicerQueueItem, ...]:
    piece_audit = audit_first_print_final_piece_artifacts(
        params=params,
        out_dir=out_dir,
        piece_dir=piece_dir,
        slicer_setup_path=slicer_setup_path,
    )
    if not piece_audit.final_piece_artifacts_ready:
        detail = piece_audit.issues[0].message if piece_audit.issues else "not ready"
        raise ValueError(f"final-piece artifacts are not ready: {detail}")

    queue = Path(queue_dir)
    queue.mkdir(parents=True, exist_ok=True)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    if manifest.exists() and not overwrite:
        raise FileExistsError(manifest)

    items = first_print_final_piece_slicer_queue_items(
        params=params,
        out_dir=out_dir,
        piece_dir=piece_dir,
        queue_dir=queue,
        slicer_setup_path=slicer_setup_path,
    )
    for item in items:
        if item.queue_stl_path.exists() and not overwrite:
            raise FileExistsError(item.queue_stl_path)

    copied: list[FirstPrintSlicerQueueItem] = []
    for item in items:
        copy2(item.source_stl_path, item.queue_stl_path)
        copied.append(
            FirstPrintSlicerQueueItem(
                name=item.name,
                source_stl_path=item.source_stl_path,
                queue_stl_path=item.queue_stl_path,
                sha256=file_sha256(item.queue_stl_path),
                target_x_mm=item.target_x_mm,
                target_y_mm=item.target_y_mm,
                target_z_mm=item.target_z_mm,
                role=item.role,
            )
        )

    manifest.write_text(
        first_print_slicer_queue_manifest_markdown(
            params=params,
            items=tuple(copied),
            queue_dir=queue,
        )
    )
    return tuple(copied)


def audit_first_print_slicer_queue(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    queue_dir: str | Path,
) -> FirstPrintSlicerQueueAudit:
    package_audit = audit_first_print_package(params, out_dir)
    queue = Path(queue_dir)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    printed_artifacts = first_print_slicer_queue_artifacts(package_audit)
    expected_stl_paths = tuple(queue / artifact.stl_path.name for artifact in printed_artifacts)
    expected_path_set = set(expected_stl_paths)

    actual_paths = tuple(sorted(path for path in queue.iterdir())) if queue.exists() else ()
    actual_file_paths = tuple(path for path in actual_paths if path.is_file())
    actual_stl_paths = tuple(path for path in actual_file_paths if path.suffix.lower() == ".stl")
    allowed_paths = {*expected_path_set, manifest}
    extra_paths = tuple(path for path in actual_file_paths if path not in allowed_paths)
    missing_stl_paths = tuple(path for path in expected_stl_paths if not path.exists())

    mismatches: list[FirstPrintSlicerQueueHashMismatch] = []
    for artifact in printed_artifacts:
        queue_path = queue / artifact.stl_path.name
        if not queue_path.exists() or not artifact.stl_path.exists():
            continue
        expected_sha = file_sha256(artifact.stl_path)
        actual_sha = file_sha256(queue_path)
        if expected_sha != actual_sha:
            mismatches.append(
                FirstPrintSlicerQueueHashMismatch(
                    path=queue_path,
                    expected_sha256=expected_sha,
                    actual_sha256=actual_sha,
                )
            )

    return FirstPrintSlicerQueueAudit(
        queue_dir=queue,
        manifest_path=manifest,
        manifest_exists=manifest.exists(),
        expected_stl_paths=expected_stl_paths,
        actual_stl_paths=actual_stl_paths,
        missing_stl_paths=missing_stl_paths,
        extra_paths=extra_paths,
        hash_mismatches=tuple(mismatches),
        package_missing_paths=package_audit.missing_paths,
    )


def audit_first_print_final_piece_slicer_queue(
    *,
    params: dict[str, Any],
    out_dir: str | Path,
    piece_dir: str | Path,
    queue_dir: str | Path,
    slicer_setup_path: str | Path,
) -> FirstPrintSlicerQueueAudit:
    piece_audit = audit_first_print_final_piece_artifacts(
        params=params,
        out_dir=out_dir,
        piece_dir=piece_dir,
        slicer_setup_path=slicer_setup_path,
    )
    package_audit = audit_first_print_package(params, out_dir)
    queue = Path(queue_dir)
    manifest = queue / "SLICER_QUEUE_MANIFEST.md"
    items = first_print_final_piece_slicer_queue_items(
        params=params,
        out_dir=out_dir,
        piece_dir=piece_dir,
        queue_dir=queue,
        slicer_setup_path=slicer_setup_path,
    )
    expected_stl_paths = tuple(item.queue_stl_path for item in items)
    expected_path_set = set(expected_stl_paths)

    actual_paths = tuple(sorted(path for path in queue.iterdir())) if queue.exists() else ()
    actual_file_paths = tuple(path for path in actual_paths if path.is_file())
    actual_stl_paths = tuple(path for path in actual_file_paths if path.suffix.lower() == ".stl")
    allowed_paths = {*expected_path_set, manifest}
    extra_paths = tuple(path for path in actual_file_paths if path not in allowed_paths)
    missing_stl_paths = tuple(path for path in expected_stl_paths if not path.exists())

    mismatches: list[FirstPrintSlicerQueueHashMismatch] = []
    missing_source_paths: list[Path] = []
    for item in items:
        if not item.source_stl_path.exists():
            missing_source_paths.append(item.source_stl_path)
            continue
        if not item.queue_stl_path.exists():
            continue
        expected_sha = file_sha256(item.source_stl_path)
        actual_sha = file_sha256(item.queue_stl_path)
        if expected_sha != actual_sha:
            mismatches.append(
                FirstPrintSlicerQueueHashMismatch(
                    path=item.queue_stl_path,
                    expected_sha256=expected_sha,
                    actual_sha256=actual_sha,
                )
            )

    source_issues = tuple(
        f"{issue.split_part} | {issue.field} | {issue.message}"
        for issue in piece_audit.issues
    )
    return FirstPrintSlicerQueueAudit(
        queue_dir=queue,
        manifest_path=manifest,
        manifest_exists=manifest.exists(),
        expected_stl_paths=expected_stl_paths,
        actual_stl_paths=actual_stl_paths,
        missing_stl_paths=missing_stl_paths,
        extra_paths=extra_paths,
        hash_mismatches=tuple(mismatches),
        package_missing_paths=(
            *package_audit.missing_paths,
            *tuple(missing_source_paths),
        ),
        source_issues=source_issues,
    )
