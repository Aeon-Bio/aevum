from __future__ import annotations

import copy
import csv
import hashlib
import html
import json
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import cadquery as cq

from aevum_cad.params import ROOT

from .final_print_pieces import _keyed_split_pair
from .parts.latches import build_lid_latch_coupon_pair
from .parts.sealing import build_lid_tongue_groove_coupon_pair
from .qc_gauges import (
    build_material_cleaning_witness_coupon,
    build_printability_support_cleanup_check,
)

ASSEMBLY_COUPON_FAMILY_IDS = (
    "lid_tongue_groove",
    "structural_split_joint",
    "snap_keeper",
    "wedge_receiver",
    "shroud_connector",
    "gasket_land_compression",
    "barb_tube",
    "support_cleanup",
)

ASSEMBLY_COUPON_PRINTER_SCOPE = {
    "printer_model": "Original Prusa MK4 Input Shaper 0.4 nozzle",
    "nozzle_diameter_mm": 0.4,
    "rigid_material": "Elegoo PLA",
    "rigid_profile": "0.15mm STRUCTURAL coupon profile",
    "transfer_rule": (
        "Results apply only to the recorded printer, nozzle, material product/lot, "
        "profile hash, orientation, and environmental conditioning."
    ),
}

_LADDER_DELTAS_MM = (-0.1, 0.0, 0.1)


def _with_index_bars(model: cq.Workplane, index: int) -> cq.Workplane:
    """Cut a simple, printable unary index into a non-mating underside corner."""

    bb = model.val().BoundingBox()
    bar_w = 0.7
    bar_l = 2.4
    gap = 0.45
    bars = None
    for bar_index in range(index):
        bar = (
            cq.Workplane("XY")
            .box(bar_w, bar_l, 0.35, centered=(False, False, False))
            .translate(
                (
                    float(bb.xmin) + 0.8 + bar_index * (bar_w + gap),
                    float(bb.ymin) + 0.8,
                    float(bb.zmin) - 0.05,
                )
            )
        )
        bars = bar if bars is None else bars.union(bar)
    if bars is None:
        raise ValueError("coupon station index must be positive")
    return model.cut(bars)


def _move_pair_to_station(
    pair: Mapping[str, cq.Workplane],
    *,
    family_id: str,
    station_index: int,
) -> dict[str, cq.Workplane]:
    moved: dict[str, cq.Workplane] = {}
    y_shift = (station_index - 1) * 16.0
    for role, model in pair.items():
        moved[f"{family_id}_s{station_index}_{role}"] = _with_index_bars(
            model.translate((0.0, y_shift, 0.0)), station_index
        )
    return moved


def _tongue_groove_models(params: dict[str, Any]) -> dict[str, cq.Workplane]:
    models: dict[str, cq.Workplane] = {}
    nominal_xy = float(params["production_assembly"]["lid_cover_tongue_clearance_xy"])
    nominal_z = float(params["production_assembly"]["lid_cover_tongue_clearance_z"])
    for index, delta in enumerate(_LADDER_DELTAS_MM, start=1):
        station_params = copy.deepcopy(params)
        station_params["production_assembly"]["lid_cover_tongue_clearance_xy"] = nominal_xy + delta
        station_params["production_assembly"]["lid_cover_tongue_clearance_z"] = nominal_z + delta
        models.update(
            _move_pair_to_station(
                build_lid_tongue_groove_coupon_pair(station_params),
                family_id="lid_tongue_groove",
                station_index=index,
            )
        )
    return models


def _split_joint_models(params: dict[str, Any]) -> dict[str, cq.Workplane]:
    models: dict[str, cq.Workplane] = {}
    base_interface = copy.deepcopy(params["production_assembly"]["final_piece_interface"])
    base_interface.pop("source_overrides", None)
    base_interface["key_x_positions_mm"] = [14.0]
    # The coupon intentionally exposes the entire clearance ladder as missing
    # reconstruction volume. Keep the canonical feature, but size the proof
    # budget for this compact witness rather than inheriting a full-part cap.
    base_interface["max_missing_volume_mm3"] = 50.0
    base_interface["max_missing_fraction"] = 0.02
    nominal = float(base_interface["fit_class_clearance_mm"])
    for index, delta in enumerate(_LADDER_DELTAS_MM, start=1):
        interface = {**base_interface, "fit_class_clearance_mm": nominal + delta}
        source = cq.Workplane("XY").box(28.0, 16.0, 8.0, centered=(False, False, False))
        lower, upper, proof = _keyed_split_pair(
            source,
            source_y_min=0.0,
            source_y_max=16.0,
            split_y=8.0,
            interface=interface,
        )
        if proof["mating_feature_kind"] == "plain_butt_fallback":
            raise ValueError("structural split coupon unexpectedly fell back to a plain seam")
        pair = {
            "boss": lower,
            "pocket": upper.translate((0.0, 10.0, 0.0)),
        }
        models.update(
            _move_pair_to_station(
                pair,
                family_id="structural_split_joint",
                station_index=index,
            )
        )
    return models


def _snap_keeper_models(params: dict[str, Any]) -> dict[str, cq.Workplane]:
    models: dict[str, cq.Workplane] = {}
    nominal = float(params["sensor_harness"]["lower_cover_hook_clearance_xy"])
    for index, delta in enumerate(_LADDER_DELTAS_MM, start=1):
        clearance = nominal + delta
        base_l, base_w, base_h = 22.0, 10.0, 2.0
        tab_w, tab_l, tab_h = 2.0, 6.0, 1.2
        tab = cq.Workplane("XY").box(base_l, base_w, base_h, centered=(False, False, False))
        tab = tab.union(
            cq.Workplane("XY")
            .box(tab_w, tab_l, tab_h + 0.1, centered=(False, False, False))
            .translate((10.0, 2.0, base_h - 0.1))
        )
        tab = tab.union(
            cq.Workplane("XY")
            .box(1.0, 1.0, 0.6, centered=(False, False, False))
            .translate((11.0, 7.0, base_h + tab_h - 0.1))
        )
        keeper = (
            cq.Workplane("XY")
            .box(base_l, base_w, base_h + tab_h + 0.8, centered=(False, False, False))
            .cut(
                cq.Workplane("XY")
                .box(
                    tab_w + 2 * clearance,
                    tab_l + 2 * clearance,
                    tab_h + 0.7,
                    centered=(False, False, False),
                )
                .translate((10.0 - clearance, 2.0 - clearance, base_h - 0.05))
            )
            .translate((base_l + 4.0, 0.0, 0.0))
        )
        models.update(
            _move_pair_to_station(
                {"snap_tab": tab, "keeper_receptacle": keeper},
                family_id="snap_keeper",
                station_index=index,
            )
        )
    return models


def _wedge_receiver_models(params: dict[str, Any]) -> dict[str, cq.Workplane]:
    models: dict[str, cq.Workplane] = {}
    nominal = float(params["production_assembly"]["wedge_receiver_clearance_x"])
    for index, delta in enumerate(_LADDER_DELTAS_MM, start=1):
        station_params = copy.deepcopy(params)
        station_params["production_assembly"]["wedge_receiver_clearance_x"] = nominal + delta
        models.update(
            _move_pair_to_station(
                build_lid_latch_coupon_pair(station_params),
                family_id="wedge_receiver",
                station_index=index,
            )
        )
    return models


def _shroud_connector_models(params: dict[str, Any]) -> dict[str, cq.Workplane]:
    models: dict[str, cq.Workplane] = {}
    harness = params["sensor_harness"]
    connector_l = float(harness["service_connector_header_length_x"])
    connector_w = float(harness["service_connector_header_width_y"])
    connector_h = float(harness["service_connector_header_height_z"])
    wall = float(harness["service_connector_shroud_wall_xy"])
    nominal = float(harness["channel_clearance_xy"])
    for index, delta in enumerate(_LADDER_DELTAS_MM, start=1):
        clearance = nominal + delta
        outer_l = connector_l + 2 * (wall + clearance)
        outer_w = connector_w + 2 * (wall + clearance)
        base_h = 2.0
        sleeve_h = connector_h + 1.0
        fixture = cq.Workplane("XY").box(
            outer_l + 6.0, outer_w + 6.0, base_h, centered=(False, False, False)
        )
        sleeve = (
            cq.Workplane("XY")
            .box(outer_l, outer_w, sleeve_h, centered=(False, False, False))
            .translate((3.0, 3.0, base_h - 0.1))
        )
        opening = (
            cq.Workplane("XY")
            .box(
                connector_l + 2 * clearance,
                connector_w + 2 * clearance,
                sleeve_h + 0.2,
                centered=(False, False, False),
            )
            .translate((3.0 + wall, 3.0 + wall, base_h))
        )
        fixture = fixture.union(sleeve).cut(opening)
        models[f"shroud_connector_s{index}_printed_shroud_fixture"] = _with_index_bars(
            fixture.translate((0.0, (index - 1) * 20.0, 0.0)), index
        )
    return models


def _gasket_compression_models(params: dict[str, Any]) -> dict[str, cq.Workplane]:
    models: dict[str, cq.Workplane] = {}
    nominal = float(params["seal_interface"]["compressed_gasket_height_z"])
    gasket_w = float(params["seal_interface"]["gasket_rail_width"])
    for index, delta in enumerate(_LADDER_DELTAS_MM, start=1):
        target_gap = nominal + delta
        base_l, base_w, base_h = 28.0, gasket_w + 8.0, 2.0
        lower = cq.Workplane("XY").box(base_l, base_w, base_h, centered=(False, False, False))
        land = (
            cq.Workplane("XY")
            .box(20.0, gasket_w, 0.6, centered=(False, False, False))
            .translate((4.0, 4.0, base_h - 0.1))
        )
        lower = lower.union(land)
        stop_h = 0.6 + target_gap
        for x in (2.0, base_l - 4.0):
            lower = lower.union(
                cq.Workplane("XY")
                .box(2.0, 2.0, stop_h + 0.1, centered=(False, False, False))
                .translate((x, 1.0, base_h - 0.1))
            )
        upper = (
            cq.Workplane("XY")
            .box(base_l, base_w, base_h, centered=(False, False, False))
            .translate((base_l + 4.0, 0.0, 0.0))
        )
        models.update(
            _move_pair_to_station(
                {"lower_land_and_stops": lower, "upper_platen": upper},
                family_id="gasket_land_compression",
                station_index=index,
            )
        )
    return models


def _barb_tube_models(params: dict[str, Any]) -> dict[str, cq.Workplane]:
    models: dict[str, cq.Workplane] = {}
    gas = params["gas_service"]
    nominal_diameter = float(gas["barb_flange_diameter"])
    stem_diameter = float(gas["fitting_outer_diameter"])
    for index, delta in enumerate(_LADDER_DELTAS_MM, start=1):
        barb_diameter = nominal_diameter + 2 * delta
        base = cq.Workplane("XY").box(3.0, 14.0, 14.0, centered=(False, False, False))
        stem = cq.Workplane("YZ").circle(stem_diameter / 2).extrude(9.0).translate((3.0, 7.0, 7.0))
        barb = (
            cq.Workplane("YZ")
            .circle(barb_diameter / 2)
            .extrude(float(gas["barb_flange_width_x"]))
            .translate((10.8, 7.0, 7.0))
        )
        model = base.union(stem).union(barb)
        models[f"barb_tube_s{index}_printed_barb_fixture"] = _with_index_bars(
            model.translate((0.0, (index - 1) * 18.0, 0.0)), index
        )
    return models


def _support_cleanup_models(params: dict[str, Any]) -> dict[str, cq.Workplane]:
    return {
        "support_cleanup_printability_witness": build_printability_support_cleanup_check(params),
        "support_cleanup_material_cleaning_witness": (
            build_material_cleaning_witness_coupon(params)
        ),
    }


_FAMILY_BUILDERS = {
    "lid_tongue_groove": _tongue_groove_models,
    "structural_split_joint": _split_joint_models,
    "snap_keeper": _snap_keeper_models,
    "wedge_receiver": _wedge_receiver_models,
    "shroud_connector": _shroud_connector_models,
    "gasket_land_compression": _gasket_compression_models,
    "barb_tube": _barb_tube_models,
    "support_cleanup": _support_cleanup_models,
}


def build_row_coupon_assembly_coupon_families(
    params: dict[str, Any],
) -> dict[str, dict[str, cq.Workplane]]:
    return {
        family_id: _FAMILY_BUILDERS[family_id](params) for family_id in ASSEMBLY_COUPON_FAMILY_IDS
    }


def _coupon_family_for_interface(interface: dict[str, Any]) -> str | None:
    interface_id = str(interface["interface_id"])
    contact = str(interface["intended_contact_type"])
    if contact == "tongue_in_groove_closure":
        return "lid_tongue_groove"
    if "wedge" in contact or interface_id == "printed_wedge_locks::wet_chamber_frame#latch":
        return "wedge_receiver"
    if "shroud" in interface_id and interface["interface_class"] == "service":
        return "shroud_connector"
    if "snap" in contact or "keeper" in contact or "keeper_door" in interface_id:
        return "snap_keeper"
    if interface["interface_class"] == "seal":
        return "gasket_land_compression"
    if interface["interface_class"] == "tube":
        return "barb_tube"
    return None


def row_coupon_assembly_coupon_manifest(
    params: dict[str, Any],
    *,
    interface_matrix_path: Path = ROOT / "docs" / "assembly" / "interface_matrix.json",
    sequence_matrix_path: Path = ROOT / "docs" / "assembly" / "sequence_and_split_matrix.json",
) -> dict[str, Any]:
    interface_matrix = json.loads(interface_matrix_path.read_text())
    sequence_matrix = json.loads(sequence_matrix_path.read_text())
    nominal = {
        "lid_tongue_groove": float(params["production_assembly"]["lid_cover_tongue_clearance_xy"]),
        "structural_split_joint": float(
            params["production_assembly"]["final_piece_interface"]["fit_class_clearance_mm"]
        ),
        "snap_keeper": float(params["sensor_harness"]["lower_cover_hook_clearance_xy"]),
        "wedge_receiver": float(params["production_assembly"]["wedge_receiver_clearance_x"]),
        "shroud_connector": float(params["sensor_harness"]["channel_clearance_xy"]),
        "gasket_land_compression": float(params["seal_interface"]["compressed_gasket_height_z"]),
        "barb_tube": float(params["gas_service"]["barb_flange_diameter"]),
    }
    builder_sources = {
        "lid_tongue_groove": "parts.sealing.build_lid_tongue_groove_coupon_pair",
        "structural_split_joint": "final_print_pieces._keyed_split_pair",
        "snap_keeper": "assembly_coupons._snap_keeper_models",
        "wedge_receiver": "parts.latches.build_lid_latch_coupon_pair",
        "shroud_connector": "assembly_coupons._shroud_connector_models",
        "gasket_land_compression": "assembly_coupons._gasket_compression_models",
        "barb_tube": "assembly_coupons._barb_tube_models",
        "support_cleanup": (
            "qc_gauges.build_printability_support_cleanup_check+"
            "build_material_cleaning_witness_coupon"
        ),
    }
    external_mates = {
        "shroud_connector": [
            "exact JST GH 1.25 mm 4-circuit header and mating plug from recorded lot"
        ],
        "gasket_land_compression": [
            "production-intent gasket strip from recorded material and lot"
        ],
        "barb_tube": ["exact production tube from recorded material, size, and lot"],
    }
    families = []
    for family_id in ASSEMBLY_COUPON_FAMILY_IDS:
        stations = []
        if family_id != "support_cleanup":
            for index, delta in enumerate(_LADDER_DELTAS_MM, start=1):
                stations.append(
                    {
                        "station_id": f"{family_id}_s{index}",
                        "physical_label_code": "|" * index,
                        "delta_mm": delta,
                        "nominal_value_mm": nominal[family_id],
                        "test_value_mm": round(nominal[family_id] + delta, 3),
                    }
                )
        else:
            stations.extend(
                [
                    {
                        "station_id": "support_cleanup_printability_witness",
                        "physical_label_code": "|",
                        "delta_mm": None,
                    },
                    {
                        "station_id": "support_cleanup_material_cleaning_witness",
                        "physical_label_code": "||",
                        "delta_mm": None,
                    },
                ]
            )
        covered = [
            row["interface_id"]
            for row in interface_matrix["interfaces"]
            if _coupon_family_for_interface(row) == family_id
        ]
        if family_id == "structural_split_joint":
            covered = [
                f"split::{row['source_artifact_id']}" for row in sequence_matrix["split_sources"]
            ]
        if family_id == "support_cleanup":
            covered = ["process::support_cleanup", "process::material_cleaning"]
        families.append(
            {
                "family_id": family_id,
                "builder_source": builder_sources[family_id],
                "coverage_mode": "screen_only_not_final_acceptance",
                "covered_interface_ids": covered,
                "stations": stations,
                "required_external_mates": external_mates.get(family_id, []),
                "result_scope": ASSEMBLY_COUPON_PRINTER_SCOPE["transfer_rule"],
                "remaining_full_part_gate": (
                    "Installed full-part fit, motion, load, leak, service access, and durability "
                    "remain blocked until their owning gate records direct evidence."
                ),
            }
        )

    interface_coverage = []
    for interface in interface_matrix["interfaces"]:
        family_id = _coupon_family_for_interface(interface)
        if family_id is None:
            mode = "full_part_only"
            reason = (
                "Depends on installed envelope, datum, cable route, exact COTS body, collision "
                "clearance, or service sweep that a local coupon cannot preserve."
            )
        else:
            mode = "coupon_screen_plus_full_part_gate"
            reason = (
                "Coupon screens local manufacturing fit only; installed geometry and owning "
                "physical gate remain authoritative."
            )
        interface_coverage.append(
            {
                "interface_id": interface["interface_id"],
                "mode": mode,
                "coupon_family_id": family_id,
                "reason": reason,
                "evidence_owner": interface["evidence_owner"],
            }
        )

    service_path_coverage = []
    service_family = {
        "connector_shroud_and_pigtail_service": "shroud_connector",
        "harness_cover_install_and_release": "snap_keeper",
        "gas_tube_service": "barb_tube",
        "wedge_lock_release": "wedge_receiver",
    }
    for path in sequence_matrix["service_paths"]:
        family_id = service_family.get(path["path_id"])
        service_path_coverage.append(
            {
                "path_id": path["path_id"],
                "mode": ("coupon_screen_plus_full_part_gate" if family_id else "full_part_only"),
                "coupon_family_id": family_id,
                "reason": (
                    "Local fit can be screened, but the complete removal path remains a "
                    "full-part gate."
                    if family_id
                    else "The path depends on the complete installed body and destination envelope."
                ),
            }
        )

    return {
        "schema_version": 1,
        "manifest_id": "aevum-row-coupon-assembly-coupons-v1",
        "scope": dict(ASSEMBLY_COUPON_PRINTER_SCOPE),
        "policy": {
            "coupon_results_are_final_artifact_acceptance": False,
            "coupon_failure_blocks_represented_full_parts": True,
            "coupon_pass_only_authorizes_next_full_part_gate": True,
            "plain_seams_are_not_covered": True,
            "unrecorded_profile_or_material_transfer_allowed": False,
        },
        "families": families,
        "interface_coverage": interface_coverage,
        "split_source_coverage": [
            {
                "source_artifact_id": row["source_artifact_id"],
                "coupon_family_id": "structural_split_joint",
                "mode": "coupon_screen_plus_full_part_gate",
                "remaining_gate": row["seam_status"],
            }
            for row in sequence_matrix["split_sources"]
        ],
        "service_path_coverage": service_path_coverage,
    }


MEASUREMENT_FIELDS = (
    "run_id",
    "date",
    "operator",
    "family_id",
    "station_id",
    "physical_label_code",
    "printer_serial",
    "nozzle_diameter_mm",
    "material_manufacturer",
    "material_product",
    "material_lot",
    "material_color",
    "profile_name",
    "profile_sha256",
    "print_orientation",
    "conditioned_hours",
    "measured_feature_mm",
    "measured_mate_mm",
    "measured_clearance_or_compression_mm",
    "fit_result",
    "damage_observed",
    "cycle_count",
    "retention_or_insertion_force_n",
    "leak_result",
    "cleanup_method",
    "coupon_result",
    "full_part_gate_owner",
    "full_part_gate_result",
    "notes",
)


def write_row_coupon_assembly_coupon_measurement_form(manifest: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=MEASUREMENT_FIELDS)
        writer.writeheader()
        for family in manifest["families"]:
            for station in family["stations"]:
                writer.writerow(
                    {
                        "family_id": family["family_id"],
                        "station_id": station["station_id"],
                        "physical_label_code": station["physical_label_code"],
                        "nozzle_diameter_mm": manifest["scope"]["nozzle_diameter_mm"],
                        "material_manufacturer": "Elegoo",
                        "material_product": "PLA",
                        "profile_name": manifest["scope"]["rigid_profile"],
                    }
                )
    return path


def _model_xml(models: Mapping[str, cq.Workplane], *, title: str) -> str:
    resources: list[str] = []
    build: list[str] = []
    x_cursor = 5.0
    for object_id, (name, model) in enumerate(models.items(), start=1):
        value = model.val()
        vertices, triangles = value.tessellate(0.08)
        vertex_xml = "".join(
            f'<vertex x="{v.x:.7g}" y="{v.y:.7g}" z="{v.z:.7g}"/>' for v in vertices
        )
        triangle_xml = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles)
        safe_name = html.escape(name, quote=True)
        resources.append(
            f'<object id="{object_id}" type="model" name="{safe_name}"><mesh>'
            f"<vertices>{vertex_xml}</vertices><triangles>{triangle_xml}</triangles>"
            "</mesh></object>"
        )
        bb = value.BoundingBox()
        tx = x_cursor - float(bb.xmin)
        ty = 5.0 - float(bb.ymin)
        tz = -float(bb.zmin)
        build.append(
            f'<item objectid="{object_id}" transform="1 0 0 0 1 0 0 0 1 '
            f'{tx:.7g} {ty:.7g} {tz:.7g}" printable="1"/>'
        )
        x_cursor += float(bb.xlen) + 5.0
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        f'<metadata name="Title">{html.escape(title)}</metadata>'
        f"<resources>{''.join(resources)}</resources><build>{''.join(build)}</build></model>"
    )


def _write_family_3mf(
    path: Path, family_id: str, models: Mapping[str, cq.Workplane], profile_digest: str
) -> None:
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" '
        'ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
        "</Types>"
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        "</Relationships>"
    )
    metadata = json.dumps(
        {
            "family_id": family_id,
            "scope": ASSEMBLY_COUPON_PRINTER_SCOPE,
            "profile_sha256": profile_digest,
            "final_artifact_acceptance": False,
        },
        indent=2,
        sort_keys=True,
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("3D/3dmodel.model", _model_xml(models, title=family_id))
        archive.writestr("Metadata/aevum_coupon_scope.json", metadata)


def export_row_coupon_assembly_coupon_package(
    params: dict[str, Any],
    out_dir: str | Path,
    *,
    profile_path: Path | None = None,
) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = row_coupon_assembly_coupon_manifest(params)
    profile_digest = (
        hashlib.sha256(profile_path.read_bytes()).hexdigest()
        if profile_path is not None
        else "UNSET_BLOCKS_PHYSICAL_TRANSFER"
    )
    manifest["scope"]["profile_sha256"] = profile_digest
    paths: dict[str, Path] = {}
    models_by_family = build_row_coupon_assembly_coupon_families(params)
    for family_id, models in models_by_family.items():
        family_dir = out / family_id
        family_dir.mkdir(exist_ok=True)
        for name, model in models.items():
            stl_path = family_dir / f"{name}.stl"
            step_path = family_dir / f"{name}.step"
            cq.exporters.export(model, str(stl_path))
            cq.exporters.export(model, str(step_path))
            paths[f"{name}_stl"] = stl_path
            paths[f"{name}_step"] = step_path
        project_path = out / f"{family_id}.3mf"
        _write_family_3mf(project_path, family_id, models, profile_digest)
        paths[f"{family_id}_3mf"] = project_path

    manifest_path = out / "assembly_coupon_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    measurement_path = write_row_coupon_assembly_coupon_measurement_form(
        manifest, out / "assembly_coupon_measurement_form.csv"
    )
    paths["manifest"] = manifest_path
    paths["measurement_form"] = measurement_path
    return paths
