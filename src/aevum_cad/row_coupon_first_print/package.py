"""First-print CAD output package catalog + package audit (extracted, behavior-preserving)."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aevum_cad.row_coupon import (
    row_coupon_final_print_piece_plan,
    row_coupon_part_manifest,
    row_coupon_physical_artifact_manifest,
    row_coupon_physical_artifact_print_policies,
)

from .common import file_sha256  # noqa: F401  (re-exported via facade)
from .constants import (
    FIRST_PRINT_OPTIONAL_VALIDATION_TOOLS,
    FIRST_PRINT_REQUIRED_VALIDATION_CHECKS,
)
from .models import (
    FirstPrintArtifact,
    FirstPrintPackageAudit,
)


def artifact_category(fabrication_source: str) -> str:
    if fabrication_source == "printed_polymer":
        return "printed"
    if fabrication_source == "compressible_elastomer_or_printed_tpu":
        return "compressible_or_flexible"
    if fabrication_source == "cots_consumable":
        return "cots_consumable"
    if fabrication_source == "cots_flexible_tubing":
        return "service_tubing"
    if fabrication_source in {
        "cots_electronics",
        "custom_or_cots_pcb_assembly",
        "electronics_assembly",
        "electronics_microcarrier",
        "cots_cable_assembly",
    }:
        return "electronics_or_dimensional_blank"
    if fabrication_source == "validation_only_geometry":
        return "validation"
    return "other"


def expected_production_artifacts(
    params: dict[str, Any],
    out_dir: str | Path,
) -> tuple[FirstPrintArtifact, ...]:
    out = Path(out_dir)
    prefix = params["name"]
    manifest = row_coupon_physical_artifact_manifest(params)
    artifacts: list[FirstPrintArtifact] = []
    for row in row_coupon_final_print_piece_plan(params):
        name = str(row["name"])
        source = str(row["source_artifact"])
        entry = manifest[source]
        stl_path = out / "final_print_pieces" / f"{prefix}_{name}.stl"
        step_path = out / "final_print_pieces" / f"{prefix}_{name}.step"
        artifacts.append(
            FirstPrintArtifact(
                name=name,
                category="printed",
                stl_path=stl_path,
                step_path=step_path,
                stl_exists=stl_path.exists(),
                step_exists=step_path.exists(),
                fabrication_source=entry["fabrication_source"],
                role=entry["role"],
            )
        )
    for policy in row_coupon_physical_artifact_print_policies(
        params,
        bed_x_mm=250.0,
        bed_y_mm=210.0,
        fits_rectangular_bed=lambda target_x, target_y, bed_x, bed_y: (
            target_x <= bed_x
            and target_y <= bed_y
            or target_x <= bed_y
            and target_y <= bed_x
        ),
    ):
        if policy.policy != "nonprinted_or_flexible":
            continue
        entry = manifest[policy.name]
        fabrication_source = entry["fabrication_source"]
        artifacts.append(
            FirstPrintArtifact(
                name=policy.name,
                category=artifact_category(fabrication_source),
                stl_path=out / f"{prefix}_{policy.name}.stl",
                step_path=out / f"{prefix}_{policy.name}.step",
                stl_exists=(out / f"{prefix}_{policy.name}.stl").exists(),
                step_exists=(out / f"{prefix}_{policy.name}.step").exists(),
                fabrication_source=fabrication_source,
                role=entry["role"],
            )
        )
    return tuple(artifacts)


def _validation_artifact(
    *,
    name: str,
    prefix: str,
    out: Path,
    role: str,
    optional: bool = False,
) -> FirstPrintArtifact:
    stl_path = out / f"{prefix}_validation_{name}.stl"
    step_path = out / f"{prefix}_validation_{name}.step"
    return FirstPrintArtifact(
        name=name,
        category="optional_validation" if optional else "validation",
        stl_path=stl_path,
        step_path=step_path,
        stl_exists=stl_path.exists(),
        step_exists=step_path.exists(),
        fabrication_source="validation_only_geometry",
        role=role,
    )


def expected_validation_artifacts(
    params: dict[str, Any],
    out_dir: str | Path,
) -> tuple[FirstPrintArtifact, ...]:
    out = Path(out_dir)
    prefix = params["name"]
    validation_manifest = row_coupon_part_manifest()["validation"]
    return tuple(
        _validation_artifact(
            name=name,
            prefix=prefix,
            out=out,
            role=validation_manifest[name]["role"],
        )
        for name in FIRST_PRINT_REQUIRED_VALIDATION_CHECKS
    )


def expected_optional_validation_artifacts(
    params: dict[str, Any],
    out_dir: str | Path,
) -> tuple[FirstPrintArtifact, ...]:
    out = Path(out_dir)
    prefix = params["name"]
    validation_manifest = row_coupon_part_manifest()["validation"]
    return tuple(
        _validation_artifact(
            name=name,
            prefix=prefix,
            out=out,
            role=validation_manifest[name]["role"],
            optional=True,
        )
        for name in FIRST_PRINT_OPTIONAL_VALIDATION_TOOLS
    )


def audit_first_print_package(
    params: dict[str, Any],
    out_dir: str | Path,
) -> FirstPrintPackageAudit:
    out = Path(out_dir)
    assembly_step = out / f"{params['name']}_assembly.step"
    return FirstPrintPackageAudit(
        name=params["name"],
        out_dir=out,
        assembly_step=assembly_step,
        assembly_step_exists=assembly_step.exists(),
        production_artifacts=expected_production_artifacts(params, out),
        validation_artifacts=expected_validation_artifacts(params, out),
        optional_validation_artifacts=expected_optional_validation_artifacts(params, out),
    )




def first_print_artifact_category_counts(
    audit: FirstPrintPackageAudit,
) -> dict[str, int]:
    counts = Counter(artifact.category for artifact in audit.production_artifacts)
    return dict(sorted(counts.items()))


def _required_artifact_paths(audit: FirstPrintPackageAudit) -> tuple[Path, ...]:
    paths = [audit.assembly_step]
    for artifact in (*audit.production_artifacts, *audit.validation_artifacts):
        paths.extend((artifact.stl_path, artifact.step_path))
    return tuple(paths)


def latest_required_artifact_timestamp(audit: FirstPrintPackageAudit) -> str:
    mtimes = [
        path.stat().st_mtime
        for path in _required_artifact_paths(audit)
        if path.exists()
    ]
    if not mtimes:
        return ""
    timestamp = datetime.fromtimestamp(max(mtimes), tz=UTC)
    return timestamp.isoformat(timespec="seconds").replace("+00:00", "Z")


def first_print_audit_snapshot_markdown(audit: FirstPrintPackageAudit) -> str:
    lines = [
        "## Gate 0 Audit Snapshot",
        "",
        "This snapshot only verifies CAD output package presence. It does not mark any",
        "physical readiness gate as passed.",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Package | `{audit.name}` |",
        f"| Output directory | `{audit.out_dir}` |",
        f"| Assembly STEP | {'present' if audit.assembly_step_exists else 'missing'} |",
        f"| Required production artifacts | {len(audit.production_artifacts)} |",
        f"| Required validation artifacts | {len(audit.validation_artifacts)} |",
        f"| Optional validation artifacts | {len(audit.optional_validation_artifacts)} |",
        f"| Audit ready | {'true' if audit.ready else 'false'} |",
        "",
        "| Production artifact category | Count |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {category} | {count} |"
        for category, count in first_print_artifact_category_counts(audit).items()
    )

    missing = audit.missing_paths
    if missing:
        lines.extend(
            [
                "",
                "| Missing required artifact |",
                "|---|",
            ]
        )
        lines.extend(f"| `{path}` |" for path in missing)
    else:
        lines.extend(["", "Missing required artifacts: none"])

    return "\n".join(lines)
