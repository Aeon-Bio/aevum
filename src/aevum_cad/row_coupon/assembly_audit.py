from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from itertools import combinations
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from aevum_cad.params import ROOT, load_params

from .artifacts import row_coupon_physical_artifact_specs
from .assembly import (
    build_row_coupon_installed_parts,
    measure_row_coupon_realized_installed_pair_intersections,
)
from .assembly_coupons import (
    ASSEMBLY_COUPON_FAMILY_IDS,
    MEASUREMENT_FIELDS,
    row_coupon_assembly_coupon_manifest,
)
from .final_print_pieces import realize_row_coupon_final_print_pieces

EXPECTED_COUNTS = {
    "canonical_sources": 38,
    "release_bodies": 46,
    "rigid_print_pieces": 38,
    "installed_families": 28,
    "unordered_pairs": 378,
    "interfaces": 64,
    "exclusions": 314,
    "split_sources": 8,
    "service_paths": 9,
    "coupon_families": 8,
    "plates": 12,
}
EXPECTED_COTS_CLASSES = {
    "gas_pcb",
    "gas_service_tube",
    "ir_thermopile",
    "jst_gh_1p25_4_circuit",
    "microplate",
    "septum_mat",
    "sht41_module",
}
DIMENSIONS = ("digital", "manufacturing", "coupon", "physical")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pair_key(left: str, right: str) -> str:
    return "::".join(sorted((left, right)))


def _finding(
    findings: list[dict[str, Any]],
    dimension: str,
    code: str,
    message: str,
    **evidence: Any,
) -> None:
    findings.append(
        {"dimension": dimension, "code": code, "message": message, "evidence": evidence}
    )


def _load_json(path: Path, findings: list[dict[str, Any]], dimension: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        _finding(findings, dimension, "EVIDENCE_UNREADABLE", str(exc), path=str(path))
        return {}
    if not isinstance(value, dict):
        _finding(
            findings,
            dimension,
            "EVIDENCE_WRONG_TYPE",
            "JSON root must be an object",
            path=str(path),
        )
        return {}
    return value


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _audit_authority(
    root: Path,
    params: dict[str, Any],
    authority: dict[str, Any],
    findings: list[dict[str, Any]],
    realization: Any,
) -> dict[str, Any]:
    declared_sources = authority.get("canonical_sources", [])
    declared_bodies = authority.get("release_bodies", [])
    declared_source_ids = {row.get("source_artifact_id") for row in declared_sources}
    declared_body_ids = {row.get("release_body_id") for row in declared_bodies}
    live_source_ids = {spec.name for spec in row_coupon_physical_artifact_specs(params)}

    for name, observed in (
        ("canonical_sources", len(declared_sources)),
        ("release_bodies", len(declared_bodies)),
    ):
        if observed != EXPECTED_COUNTS[name]:
            _finding(
                findings,
                "digital",
                "AUTHORITY_COUNT_MISMATCH",
                f"{name} count is not authoritative",
                field=name,
                expected=EXPECTED_COUNTS[name],
                observed=observed,
            )
    if declared_source_ids != live_source_ids:
        _finding(
            findings,
            "digital",
            "SOURCE_AUTHORITY_DRIFT",
            "live canonical sources differ from the registry",
            missing=sorted(declared_source_ids - live_source_ids),
            unknown=sorted(live_source_ids - declared_source_ids),
        )

    live_rigid_ids: set[str] = set()
    split_rows: list[dict[str, Any]] = []
    try:
        live_rigid_ids = set(realization.pieces)
        split_rows = [row for row in realization.plan if row.get("action") == "structural_split"]
    except Exception as exc:  # fail closed at the B-rep boundary
        _finding(findings, "digital", "LIVE_REALIZATION_FAILED", str(exc))
    compliant_ids = {
        str(row["source_artifact_id"])
        for row in declared_sources
        if row.get("source_class") == "compliant_source"
    }
    live_body_ids = live_rigid_ids | compliant_ids
    if (
        len(live_rigid_ids) != EXPECTED_COUNTS["rigid_print_pieces"]
        or live_body_ids != declared_body_ids
    ):
        _finding(
            findings,
            "digital",
            "RELEASE_BODY_AUTHORITY_DRIFT",
            "live release bodies differ from the registry",
            expected_rigid=EXPECTED_COUNTS["rigid_print_pieces"],
            observed_rigid=len(live_rigid_ids),
            missing=sorted(declared_body_ids - live_body_ids),
            unknown=sorted(live_body_ids - declared_body_ids),
        )

    bad_hashes: list[dict[str, str]] = []
    for row in declared_bodies:
        for artifact in row.get("outputs", {}).values():
            path = _resolve(root, artifact["path"])
            observed = _sha256(path) if path.is_file() else "MISSING"
            if observed != artifact.get("sha256"):
                bad_hashes.append(
                    {
                        "path": str(path),
                        "expected": str(artifact.get("sha256")),
                        "observed": observed,
                    }
                )
    if bad_hashes:
        _finding(
            findings,
            "digital",
            "RELEASE_ARTIFACT_HASH_MISMATCH",
            "release artifacts are absent or stale",
            mismatches=bad_hashes,
        )

    split_proofs: dict[str, dict[str, Any]] = {}
    for row in split_rows:
        source = str(row["source_artifact"])
        split_proofs.setdefault(source, row.get("seam", {}))
    invalid_seams = []
    for source, seam in split_proofs.items():
        if (
            seam.get("mating_feature_kind") == "plain_butt_fallback"
            or seam.get("fallback_reason") is not None
            or float(seam.get("pair_interference_volume_mm3", 1.0)) > 1e-4
            or float(seam.get("source_excess_volume_mm3", 1.0)) > 1e-4
            or int(seam.get("realized_key_count", seam.get("realized_feature_count", 0))) <= 0
        ):
            invalid_seams.append(source)
    if len(split_proofs) != EXPECTED_COUNTS["split_sources"] or invalid_seams:
        _finding(
            findings,
            "digital",
            "SEAM_PROOF_INCOMPLETE",
            "all eight retained seams must have bounded reconstruction proofs",
            observed=len(split_proofs),
            invalid=sorted(invalid_seams),
        )

    pending_physical = [
        row["source_artifact_id"]
        for row in declared_sources
        if row.get("evidence", {}).get("status") != "accepted"
    ]
    if pending_physical:
        _finding(
            findings,
            "physical",
            "PHYSICAL_ARTIFACT_EVIDENCE_PENDING",
            "human-owned artifact evidence is not accepted",
            count=len(pending_physical),
            source_artifact_ids=pending_physical,
        )
    unresolved_rigid = [
        row["source_artifact_id"]
        for row in declared_sources
        if row.get("source_class") == "rigid_source" and not row.get("approved_operating_material")
    ]
    unresolved_compliant = [
        row["source_artifact_id"]
        for row in declared_sources
        if row.get("source_class") == "compliant_source"
        and not row.get("approved_operating_material")
    ]
    if unresolved_rigid:
        _finding(
            findings,
            "physical",
            "RIGID_OPERATING_MATERIAL_UNAPPROVED",
            "PLA slicing is not operating-material approval",
            count=len(unresolved_rigid),
            source_artifact_ids=unresolved_rigid,
        )
    if unresolved_compliant:
        _finding(
            findings,
            "physical",
            "COMPLIANT_MATERIAL_UNRESOLVED",
            "compliant artifacts have no approved material",
            count=len(unresolved_compliant),
            source_artifact_ids=unresolved_compliant,
        )
    wedge_sources = [
        row["source_artifact_id"]
        for row in declared_sources
        if str(row.get("source_artifact_id", "")).startswith("printed_wedge_lock_station_")
        and not row.get("approved_operating_material")
    ]
    if wedge_sources:
        _finding(
            findings,
            "physical",
            "WEDGE_LOCK_OPERATING_MATERIAL_BLOCKED",
            "PLA wedge locks have no operating-material approval",
            count=len(wedge_sources),
            source_artifact_ids=wedge_sources,
        )

    return {
        "canonical_source_count": len(declared_sources),
        "release_body_count": len(declared_bodies),
        "live_rigid_piece_count": len(live_rigid_ids),
        "live_release_body_count": len(live_body_ids),
        "release_artifact_hash_mismatch_count": len(bad_hashes),
        "seam_proof_count": len(split_proofs),
        "seam_proof_sources": sorted(split_proofs),
    }


def _live_intersections(parts: dict[str, Any], epsilon: float) -> dict[str, float]:
    positives: dict[str, float] = {}
    for left, right in combinations(sorted(parts), 2):
        left_bb = parts[left].val().BoundingBox()
        right_bb = parts[right].val().BoundingBox()
        if (
            min(left_bb.xmax, right_bb.xmax) <= max(left_bb.xmin, right_bb.xmin)
            or min(left_bb.ymax, right_bb.ymax) <= max(left_bb.ymin, right_bb.ymin)
            or min(left_bb.zmax, right_bb.zmax) <= max(left_bb.zmin, right_bb.zmin)
        ):
            continue
        volume = sum(float(shape.Volume()) for shape in parts[left].intersect(parts[right]).vals())
        if volume > epsilon:
            positives[_pair_key(left, right)] = round(volume, 9)
    return positives


def _audit_interfaces(
    params: dict[str, Any],
    matrix: dict[str, Any],
    sequence: dict[str, Any],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    families = list(matrix.get("scope", {}).get("installed_families", []))
    interfaces = list(matrix.get("interfaces", []))
    exclusions = set(matrix.get("explicit_exclusion_pair_keys", []))
    interface_by_pair = {row["pair_key"]: row for row in interfaces}
    all_pairs = {_pair_key(a, b) for a, b in combinations(families, 2)}
    classified = set(interface_by_pair) | exclusions
    if (
        len(families) != EXPECTED_COUNTS["installed_families"]
        or len(all_pairs) != EXPECTED_COUNTS["unordered_pairs"]
        or len(interfaces) != EXPECTED_COUNTS["interfaces"]
        or len(exclusions) != EXPECTED_COUNTS["exclusions"]
        or classified != all_pairs
        or set(interface_by_pair) & exclusions
    ):
        _finding(
            findings,
            "digital",
            "INTERFACE_COVERAGE_INCOMPLETE",
            "interface/exclusion matrix must classify every unordered installed-family "
            "pair exactly once",
            installed_families=len(families),
            unordered_pairs=len(all_pairs),
            interfaces=len(interfaces),
            exclusions=len(exclusions),
            missing=sorted(all_pairs - classified),
            duplicated=sorted(set(interface_by_pair) & exclusions),
        )

    epsilon = float(matrix.get("scope", {}).get("volume_epsilon_mm3", 1e-6))
    release_bodies_are_installed = True
    try:
        realized_volumes = measure_row_coupon_realized_installed_pair_intersections(params)
        live = {
            key: round(volume, 9) for key, volume in realized_volumes.items() if volume > epsilon
        }
        if set(realized_volumes) != all_pairs:
            _finding(
                findings,
                "digital",
                "REALIZED_INSTALLED_PAIR_COVERAGE_INCOMPLETE",
                "realized installed geometry must measure all 378 family pairs",
                observed=len(realized_volumes),
                missing=sorted(all_pairs - set(realized_volumes)),
                unknown=sorted(set(realized_volumes) - all_pairs),
            )
    except Exception as exc:  # fail closed at the B-rep boundary
        release_bodies_are_installed = False
        installed = build_row_coupon_installed_parts(params)
        live = _live_intersections(installed, epsilon)
        _finding(
            findings,
            "digital",
            "INSTALLED_RELEASE_BODY_COLLISION_PROOF_UNAVAILABLE",
            (
                "the installed 38-rigid-body collision audit failed; the 28-family "
                "proxy is diagnostic only"
            ),
            error=f"{type(exc).__name__}: {exc}",
            proxy_family_count=len(installed),
            required_rigid_release_body_count=EXPECTED_COUNTS["rigid_print_pieces"],
        )
    static = {
        str(key): float(value)
        for key, value in matrix.get("geometry_observations", {})
        .get("positive_intersections_mm3", {})
        .items()
    }
    changed = sorted(
        key
        for key in set(static) | set(live)
        if abs(static.get(key, 0.0) - live.get(key, 0.0)) > epsilon
    )
    if changed:
        _finding(
            findings,
            "digital",
            "STATIC_LIVE_GEOMETRY_MISMATCH",
            "the checked-in observation matrix is not live geometry authority",
            static_positive_pair_count=len(static),
            live_positive_pair_count=len(live),
            changed_pair_count=len(changed),
            changed_pair_keys=changed,
        )
    unclassified = {
        key: value
        for key, value in live.items()
        if key in exclusions or key not in interface_by_pair
    }
    for key, volume in sorted(unclassified.items()):
        _finding(
            findings,
            "digital",
            "UNCLASSIFIED_LIVE_INTERSECTION",
            "live positive-volume intersection is not an intended interface",
            pair_key=key,
            volume_mm3=volume,
        )
    forbidden = {
        key: volume
        for key, volume in live.items()
        if key in interface_by_pair and interface_by_pair[key].get("forbidden_intersection")
    }
    for key, volume in sorted(forbidden.items()):
        _finding(
            findings,
            "digital",
            "FORBIDDEN_LIVE_INTERSECTION",
            "declared forbidden installed bodies intersect",
            pair_key=key,
            volume_mm3=volume,
        )

    splits = list(sequence.get("split_sources", []))
    service_paths = list(sequence.get("service_paths", []))
    if len(splits) != EXPECTED_COUNTS["split_sources"] or any(
        row.get("mating_feature_kind") == "plain_butt_fallback" for row in splits
    ):
        _finding(
            findings,
            "digital",
            "SPLIT_MATRIX_INCOMPLETE",
            "eight retained, non-plain split sources are required",
            observed=len(splits),
        )
    blocked_paths = [
        row
        for row in service_paths
        if row.get("blocking") or str(row.get("status", "")).startswith("blocked_")
    ]
    if len(service_paths) != EXPECTED_COUNTS["service_paths"]:
        _finding(
            findings,
            "digital",
            "SERVICE_PATH_COVERAGE_INCOMPLETE",
            "exactly nine service paths are required",
            observed=len(service_paths),
        )
    for row in blocked_paths:
        _finding(
            findings,
            "digital",
            "SERVICE_PATH_BLOCKED",
            "installed service motion lacks required evidence",
            path_id=row.get("path_id"),
            status=row.get("status"),
            missing_proof=row.get("missing_proof", []),
        )

    return {
        "installed_family_count": len(families),
        "unordered_pair_count": len(all_pairs),
        "interface_count": len(interfaces),
        "exclusion_count": len(exclusions),
        "static_positive_pair_count": len(static),
        "live_positive_pair_count": len(live),
        "static_live_change_count": len(changed),
        "unclassified_live_intersections_mm3": unclassified,
        "forbidden_live_intersections_mm3": forbidden,
        "split_source_count": len(splits),
        "service_path_count": len(service_paths),
        "blocked_service_path_count": len(blocked_paths),
        "collision_geometry_scope": (
            "installed_release_bodies" if release_bodies_are_installed else "grouped_family_proxy"
        ),
    }


def _three_mf_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("Metadata/Slic3r_PE_model.config"))
    return [
        str(node.attrib["value"])
        for node in root.findall("./object/metadata[@type='object'][@key='name']")
    ]


def _audit_manufacturing(
    root: Path, ledger: dict[str, Any], authority: dict[str, Any], findings: list[dict[str, Any]]
) -> dict[str, Any]:
    plates = list(ledger.get("plates", []))
    bodies = list(ledger.get("bodies", []))
    rigid_ids = {
        row["release_body_id"]
        for row in authority.get("release_bodies", [])
        if row.get("body_class") == "rigid_print_piece"
    }
    observed_ids = [str(row.get("release_body_id")) for row in bodies]
    plate_body_ids = [str(body_id) for plate in plates for body_id in plate.get("body_ids", [])]
    if len(plates) != EXPECTED_COUNTS["plates"]:
        _finding(
            findings,
            "manufacturing",
            "PLATE_COUNT_MISMATCH",
            "the final C2 package plate count does not match its release contract",
            expected=EXPECTED_COUNTS["plates"],
            observed=len(plates),
        )
    if (
        len(bodies) != EXPECTED_COUNTS["rigid_print_pieces"]
        or set(observed_ids) != rigid_ids
        or sorted(observed_ids) != sorted(plate_body_ids)
        or len(observed_ids) != len(set(observed_ids))
    ):
        _finding(
            findings,
            "manufacturing",
            "MANUFACTURING_BODY_IDENTITY_MISMATCH",
            "ledger, plate, and authority body identities must match one-to-one",
            expected=len(rigid_ids),
            observed=len(bodies),
            missing=sorted(rigid_ids - set(observed_ids)),
            unknown=sorted(set(observed_ids) - rigid_ids),
        )
    if not ledger.get("authority", {}).get("manufacturing_evidence_only") or ledger.get(
        "authority", {}
    ).get("prototype_acceptance_granted"):
        _finding(
            findings,
            "manufacturing",
            "MANUFACTURING_BOUNDARY_VIOLATION",
            "slicer evidence must not claim prototype acceptance",
        )

    artifact_errors: list[dict[str, str]] = []
    package_root = root / "outputs" / "sliced" / "mk4_elegoo_pla"
    for plate in plates:
        ids = [str(value) for value in plate.get("body_ids", [])]
        for kind in ("3mf", "bgcode", "profile_snapshot"):
            artifact = plate.get("artifacts", {}).get(kind, {})
            path = _resolve(root, str(artifact.get("path", "")))
            if not path.is_relative_to(package_root):
                artifact_errors.append(
                    {
                        "plate_id": str(plate.get("plate_id")),
                        "kind": kind,
                        "error": "outside_final_package",
                    }
                )
                continue
            observed = _sha256(path) if path.is_file() else "MISSING"
            if observed != artifact.get("sha256"):
                artifact_errors.append(
                    {"plate_id": str(plate.get("plate_id")), "kind": kind, "error": "hash_mismatch"}
                )
        project = _resolve(root, str(plate.get("artifacts", {}).get("3mf", {}).get("path", "")))
        if project.is_file():
            try:
                names = _three_mf_names(project)
                if names != ids:
                    artifact_errors.append(
                        {
                            "plate_id": str(plate.get("plate_id")),
                            "kind": "3mf",
                            "error": "object_name_order_mismatch",
                        }
                    )
            except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
                artifact_errors.append(
                    {
                        "plate_id": str(plate.get("plate_id")),
                        "kind": "3mf",
                        "error": type(exc).__name__,
                    }
                )
        bgcode = _resolve(root, str(plate.get("artifacts", {}).get("bgcode", {}).get("path", "")))
        if bgcode.is_file() and bgcode.read_bytes()[:4] != b"GCDE":
            artifact_errors.append(
                {
                    "plate_id": str(plate.get("plate_id")),
                    "kind": "bgcode",
                    "error": "not_binary_gcode",
                }
            )
    if artifact_errors:
        _finding(
            findings,
            "manufacturing",
            "TOOLPATH_IDENTITY_OR_HASH_MISMATCH",
            "3MF/BGCODE/profile identity is missing, stale, or outside the final package",
            errors=artifact_errors,
        )
    bad_body_evidence = [
        row.get("release_body_id")
        for row in bodies
        if not row.get("artifact_completeness", {}).get("complete")
        or row.get("identity_evidence", {}).get("m486_name_match")
        not in {"exact", "truncated", "truncated_prefix"}
        or row.get("assembly_authorized")
    ]
    if bad_body_evidence:
        _finding(
            findings,
            "manufacturing",
            "BODY_TOOLPATH_EVIDENCE_INCOMPLETE",
            "every body requires complete decoded identity without assembly authorization",
            release_body_ids=bad_body_evidence,
        )
    profiles = sorted({str(row.get("profile")) for row in plates})
    return {
        "plate_count": len(plates),
        "rigid_body_count": len(bodies),
        "profiles": profiles,
        "artifact_error_count": len(artifact_errors),
        "whole_plate_authorized_count": sum(
            bool(row.get("whole_plate_print_authorized")) for row in plates
        ),
    }


def _audit_coupons(
    root: Path,
    params: dict[str, Any],
    interface_matrix: dict[str, Any],
    sequence: dict[str, Any],
    findings: list[dict[str, Any]],
    measurement_path: Path,
) -> dict[str, Any]:
    manifest = row_coupon_assembly_coupon_manifest(
        params,
        interface_matrix_path=root / "docs/assembly/interface_matrix.json",
        sequence_matrix_path=root / "docs/assembly/sequence_and_split_matrix.json",
    )
    families = list(manifest.get("families", []))
    interface_coverage = list(manifest.get("interface_coverage", []))
    split_coverage = list(manifest.get("split_source_coverage", []))
    service_coverage = list(manifest.get("service_path_coverage", []))
    expected_interfaces = {row["interface_id"] for row in interface_matrix.get("interfaces", [])}
    covered_interfaces = {row.get("interface_id") for row in interface_coverage}
    expected_splits = {row["source_artifact_id"] for row in sequence.get("split_sources", [])}
    expected_services = {row["path_id"] for row in sequence.get("service_paths", [])}
    policy = manifest.get("policy", {})
    if (
        tuple(row.get("family_id") for row in families) != ASSEMBLY_COUPON_FAMILY_IDS
        or len(interface_coverage) != EXPECTED_COUNTS["interfaces"]
        or covered_interfaces != expected_interfaces
        or len(split_coverage) != EXPECTED_COUNTS["split_sources"]
        or {row.get("source_artifact_id") for row in split_coverage} != expected_splits
        or len(service_coverage) != EXPECTED_COUNTS["service_paths"]
        or {row.get("path_id") for row in service_coverage} != expected_services
    ):
        _finding(
            findings,
            "coupon",
            "COUPON_MAPPING_INCOMPLETE",
            "coupon manifest must map 8 families, 64 interfaces, 8 split sources, "
            "and 9 service paths",
            families=len(families),
            interfaces=len(interface_coverage),
            split_sources=len(split_coverage),
            service_paths=len(service_coverage),
        )
    if (
        policy.get("coupon_results_are_final_artifact_acceptance") is not False
        or policy.get("coupon_pass_only_authorizes_next_full_part_gate") is not True
        or policy.get("unrecorded_profile_or_material_transfer_allowed") is not False
    ):
        _finding(
            findings,
            "coupon",
            "COUPON_BOUNDARY_VIOLATION",
            "coupons must remain scoped screens rather than artifact acceptance",
        )

    station_count = sum(len(row.get("stations", [])) for row in families)
    completed = 0
    if not measurement_path.is_file():
        _finding(
            findings,
            "coupon",
            "COUPON_MEASUREMENTS_MISSING",
            "physical coupon measurements have not been recorded",
            path=str(measurement_path),
            expected_station_count=station_count,
        )
    else:
        with measurement_path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        required = {
            "run_id",
            "date",
            "operator",
            "printer_serial",
            "material_lot",
            "profile_sha256",
            "print_orientation",
            "coupon_result",
            "full_part_gate_owner",
        }
        completed = sum(
            all(str(row.get(field, "")).strip() for field in required)
            and row.get("coupon_result") == "pass"
            for row in rows
        )
        if tuple(rows[0].keys()) != MEASUREMENT_FIELDS if rows else True:
            _finding(
                findings,
                "coupon",
                "COUPON_MEASUREMENT_SCHEMA_MISMATCH",
                "measurement form schema is not authoritative",
                path=str(measurement_path),
            )
        if len(rows) != station_count or completed != station_count:
            _finding(
                findings,
                "coupon",
                "COUPON_MEASUREMENTS_INCOMPLETE",
                "every coupon station requires a scoped passing record",
                expected=station_count,
                observed=len(rows),
                completed=completed,
            )
    return {
        "family_count": len(families),
        "interface_mapping_count": len(interface_coverage),
        "split_mapping_count": len(split_coverage),
        "service_mapping_count": len(service_coverage),
        "station_count": station_count,
        "completed_passing_station_count": completed,
    }


def _audit_physical(
    root: Path, wet_seal: dict[str, Any], findings: list[dict[str, Any]], cots_path: Path
) -> dict[str, Any]:
    material = wet_seal.get("material_and_physical_authority", {})
    if material.get("operating_gasket_material") == "unresolved" or not material.get(
        "requires_d2_physical_evidence"
    ):
        _finding(
            findings,
            "physical",
            "OPERATING_GASKET_MATERIAL_UNRESOLVED",
            "digital compression geometry cannot select or validate an operating gasket",
            blocked_claims=material.get("blocked_claims", []),
        )
    cots_classes: set[str] = set()
    if not cots_path.is_file():
        _finding(
            findings,
            "physical",
            "EXACT_COTS_EVIDENCE_MISSING",
            "exact production mates and lots have no evidence registry",
            path=str(cots_path),
            expected_classes=sorted(EXPECTED_COTS_CLASSES),
        )
    else:
        registry = _load_json(cots_path, findings, "physical")
        rows = registry.get("mates", [])
        cots_classes = {str(row.get("cots_class")) for row in rows}
        incomplete = [
            row.get("cots_class")
            for row in rows
            if not all(
                row.get(key)
                for key in ("manufacturer", "part_number", "lot", "evidence_owner", "status")
            )
        ]
        if cots_classes != EXPECTED_COTS_CLASSES or incomplete:
            _finding(
                findings,
                "physical",
                "EXACT_COTS_EVIDENCE_INCOMPLETE",
                "COTS evidence must identify exact parts, lots, owners, and status",
                missing=sorted(EXPECTED_COTS_CLASSES - cots_classes),
                unknown=sorted(cots_classes - EXPECTED_COTS_CLASSES),
                incomplete=incomplete,
            )
    return {
        "operating_gasket_material": material.get("operating_gasket_material"),
        "blocked_seal_claims": list(material.get("blocked_claims", [])),
        "exact_cots_class_count": len(cots_classes),
        "required_exact_cots_class_count": len(EXPECTED_COTS_CLASSES),
    }


def audit_row_coupon_integrated_assembly(
    root: str | Path = ROOT,
    *,
    coupon_measurement_path: str | Path | None = None,
    cots_evidence_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    findings: list[dict[str, Any]] = []
    params = load_params(root / "cad/one_row_coupon.params.json")
    authority = _load_json(root / "docs/assembly/artifact_authority.json", findings, "digital")
    interface_matrix = _load_json(root / "docs/assembly/interface_matrix.json", findings, "digital")
    sequence = _load_json(
        root / "docs/assembly/sequence_and_split_matrix.json", findings, "digital"
    )
    ledger = _load_json(root / "docs/assembly/printability_ledger.json", findings, "manufacturing")
    wet_seal = _load_json(root / "docs/assembly/wet_seal_stack.json", findings, "physical")

    realization = realize_row_coupon_final_print_pieces(params)

    evidence = {
        "authority": _audit_authority(root, params, authority, findings, realization),
        "interfaces_and_service": _audit_interfaces(
            params,
            interface_matrix,
            sequence,
            findings,
        ),
        "manufacturing": _audit_manufacturing(root, ledger, authority, findings),
        "coupons": _audit_coupons(
            root,
            params,
            interface_matrix,
            sequence,
            findings,
            _resolve(
                root,
                coupon_measurement_path
                or "outputs/cad/assembly_coupons/assembly_coupon_measurement_form.csv",
            ),
        ),
        "physical": _audit_physical(
            root,
            wet_seal,
            findings,
            _resolve(root, cots_evidence_path or "docs/assembly/exact_cots_evidence.json"),
        ),
    }
    verdicts = {}
    for dimension in DIMENSIONS:
        dimension_findings = [finding for finding in findings if finding["dimension"] == dimension]
        verdicts[dimension] = {
            "status": "gate_fail" if dimension_findings else "gate_pass",
            "finding_count": len(dimension_findings),
            "finding_codes": [finding["code"] for finding in dimension_findings],
        }
    overall = (
        "GATE_FAIL"
        if any(row["status"] == "gate_fail" for row in verdicts.values())
        else "GATE_PASS"
    )
    return {
        "schema_version": 1,
        "audit_id": "aevum-row-coupon-integrated-assembly-d1",
        "overall_status": overall,
        "assembly_authorized": False,
        "verdicts": verdicts,
        "boundaries": {
            "digital_pass_is_physical_acceptance": False,
            "manufacturing_pass_is_assembly_acceptance": False,
            "coupon_pass_is_final_artifact_acceptance": False,
            "d2_human_physical_acceptance_required": True,
        },
        "expected_counts": dict(EXPECTED_COUNTS),
        "evidence": evidence,
        "findings": findings,
    }
