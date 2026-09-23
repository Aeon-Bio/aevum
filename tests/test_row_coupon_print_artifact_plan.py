from __future__ import annotations

from collections import Counter
from pathlib import Path

import cadquery as cq
import pytest

from aevum_cad.params import ROOT, load_params
from aevum_cad.row_coupon import (
    build_deck_pods,
    build_gas_pcb_interface_gaskets,
    build_gas_sensor_pcbs,
    build_ir_thermopile_face_gaskets,
    build_lid_cover,
    build_lid_harness_cover,
    build_lid_manifold_shell,
    build_lid_sensor_service_connectors,
    build_lower_gasket,
    build_lower_harness_cover,
    build_plate_support_frame,
    build_printed_gas_pcb_keeper_doors,
    build_printed_lid_sensor_connector_shrouds,
    build_printed_lower_sensor_connector_shroud,
    build_printed_sample_relief_cap,
    build_printed_wedge_locks,
    build_row_coupon_physical_artifacts,
    build_upper_gasket,
    build_wet_chamber_frame,
    group_row_coupon_physical_artifacts_by_installed_part,
    row_coupon_final_print_piece_plan,
    row_coupon_layout,
    row_coupon_physical_artifact_manifest,
    row_coupon_physical_artifact_specs,
)
from aevum_cad.row_coupon_first_print import expected_production_artifacts

PARAMS = ROOT / "cad" / "one_row_coupon.params.json"


def _rounded_bounds(shape: cq.Shape, ndigits: int = 2) -> tuple[float, ...]:
    bb = shape.BoundingBox()
    return tuple(
        round(value, ndigits)
        for value in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)
    )


def _installed_artifact_family_models(params: dict) -> dict[str, cq.Workplane]:
    return {
        "deck_pods": build_deck_pods(params),
        "plate_support_frame": build_plate_support_frame(params),
        "ir_thermopile_face_gaskets": build_ir_thermopile_face_gaskets(
            params,
            assembly_position=True,
        ),
        "lower_harness_cover": build_lower_harness_cover(params, assembly_position=True),
        "printed_lower_sensor_connector_shroud": build_printed_lower_sensor_connector_shroud(
            params,
            assembly_position=True,
        ),
        "lower_gasket": build_lower_gasket(params, assembly_position=True),
        "wet_chamber_frame": build_wet_chamber_frame(params, assembly_position=True),
        "upper_gasket": build_upper_gasket(params, assembly_position=True),
        "lid_manifold_shell": build_lid_manifold_shell(params, assembly_position=True),
        "lid_harness_cover": build_lid_harness_cover(params, assembly_position=True),
        "printed_lid_sensor_connector_shrouds": build_printed_lid_sensor_connector_shrouds(
            params,
            assembly_position=True,
        ),
        "lid_cover": build_lid_cover(params, assembly_position=True),
        "gas_pcb_interface_gaskets": build_gas_pcb_interface_gaskets(
            params,
            assembly_position=True,
        ),
        "printed_gas_pcb_keeper_doors": build_printed_gas_pcb_keeper_doors(
            params,
            assembly_position=True,
        ),
        "printed_sample_relief_cap": build_printed_sample_relief_cap(
            params,
            assembly_position=True,
        ),
        "printed_wedge_locks": build_printed_wedge_locks(params, assembly_position=True),
    }


def test_row_coupon_physical_artifact_plan_is_ordered_semantic_and_connected(
    tmp_path: Path,
    artifact_authority: dict[str, int],
) -> None:
    params = load_params(PARAMS)
    layout = row_coupon_layout(params)
    specs = row_coupon_physical_artifact_specs(params)
    artifacts = build_row_coupon_physical_artifacts(params)
    manifest = row_coupon_physical_artifact_manifest(params)
    production_artifacts = expected_production_artifacts(params, tmp_path)
    final_plan = row_coupon_final_print_piece_plan(params)

    spec_names = [spec.name for spec in specs]
    assert list(artifacts) == spec_names
    assert list(manifest) == spec_names
    printed_names = [
        artifact.name
        for artifact in production_artifacts
        if artifact.category == "printed"
    ]
    assert printed_names == [row["name"] for row in final_plan]
    assert all(manifest[spec.name]["installed_part"] == spec.installed_part for spec in specs)

    # Family cardinalities are derived, not constant: one artifact per plate
    # tile, per IR mount, per gas PCB mount, per latch station.  The literal
    # table this replaces went stale when the latch-station pattern changed
    # from 9 stations to 12 (src/aevum_cad/row_coupon/layout.py:49-61 replaces
    # the colliding centre station with a symmetric pair).  Cross-checking the
    # table against the independently built layout pins both the family set and
    # every cardinality to the source that actually decides them.
    expected_family_counts = {
        "deck_pods": len(layout["tile_origins"]),
        "plate_support_frame": 1,
        "ir_thermopile_face_gaskets": len(layout["ir_sensor_mounts"]),
        "lower_harness_cover": 1,
        "printed_lower_sensor_connector_shroud": 1,
        "lower_gasket": 1,
        "wet_chamber_frame": 1,
        "upper_gasket": 1,
        "lid_manifold_shell": 1,
        "lid_harness_cover": len(layout["lid_sensor_harness_trunks"]),
        "printed_lid_sensor_connector_shrouds": len(
            layout["lid_service_connector_envelopes"]
        ),
        "lid_cover": 1,
        "gas_pcb_interface_gaskets": len(layout["gas_sensor_pcb_mounts"]),
        "printed_gas_pcb_keeper_doors": len(layout["gas_sensor_pcb_mounts"]),
        "printed_sample_relief_cap": 1,
        "printed_wedge_locks": len(layout["wedge_lock_rectangles"]),
    }
    assert Counter(spec.installed_part for spec in specs) == expected_family_counts
    assert len(spec_names) == len(set(spec_names)) == sum(expected_family_counts.values())
    # expected_family_counts above is built from the SAME row_coupon_layout call
    # that row_coupon_physical_artifact_specs iterates, so on its own it restates
    # the generator's loop and cannot fail -- a wedge-lock pattern that silently
    # regressed from 12 stations to 9 would shrink both sides together.  The
    # external registry is the independent side of that cross-check.
    assert len(specs) == artifact_authority["canonical_sources"]

    assert [spec.name for spec in specs if spec.installed_part == "deck_pods"] == [
        f"deck_pod_tile_{tile['index']}" for tile in layout["tile_origins"]
    ]
    assert [
        spec.name for spec in specs if spec.installed_part == "ir_thermopile_face_gaskets"
    ] == [
        f"ir_thermopile_face_gasket_tile_{mount['tile_index']}"
        for mount in layout["ir_sensor_mounts"]
    ]
    assert [spec.name for spec in specs if spec.installed_part == "lid_harness_cover"] == [
        f"lid_harness_cover_{trunk['name']}"
        for trunk in layout["lid_sensor_harness_trunks"]
    ]
    assert [
        spec.name
        for spec in specs
        if spec.installed_part == "printed_lid_sensor_connector_shrouds"
    ] == [
        f"printed_lid_sensor_connector_shroud_{connector['name']}"
        for connector in layout["lid_service_connector_envelopes"]
    ]
    assert [
        spec.name for spec in specs if spec.installed_part == "gas_pcb_interface_gaskets"
    ] == [
        f"gas_pcb_interface_gasket_{mount['name']}"
        for mount in layout["gas_sensor_pcb_mounts"]
    ]
    assert [
        spec.name for spec in specs if spec.installed_part == "printed_gas_pcb_keeper_doors"
    ] == [
        f"printed_gas_pcb_keeper_door_{mount['name']}"
        for mount in layout["gas_sensor_pcb_mounts"]
    ]
    wedge_names = [spec.name for spec in specs if spec.installed_part == "printed_wedge_locks"]
    assert len(wedge_names) == len(layout["wedge_lock_rectangles"])
    expected_wedge_names = [
        f"printed_wedge_lock_station_{index:02d}_{lock['slide_axis']}_{lock['insert_from']}"
        for index, lock in enumerate(layout["wedge_lock_rectangles"], start=1)
    ]
    station_prefix_only_wedge_names = [
        f"printed_wedge_lock_station_{index:02d}"
        for index, _lock in enumerate(layout["wedge_lock_rectangles"], start=1)
    ]
    assert station_prefix_only_wedge_names != expected_wedge_names
    assert wedge_names == expected_wedge_names
    assert all("Solids" not in name for name in spec_names)

    assert all(len(model.val().Solids()) == 1 for model in artifacts.values())
    assert "deck_pods" not in artifacts
    assert "printed_wedge_locks" not in artifacts
    assert "printed_gas_pcb_keeper_doors" not in artifacts


# `lid_harness_cover` rejoined the equality loop on 2026-09-23.  The standalone
# builder used to cut only its route's owner part while the canonical grouping
# also cuts the gas PCBs, the service connectors, the printed shrouds and the
# manifold shell, so it released 267.008 mm^3 that interpenetrated four rigid
# neighbours and split into a fourth solid.  It now delegates to
# `group_row_coupon_physical_artifacts_by_installed_part`
# (src/aevum_cad/row_coupon/parts/harness.py), i.e. the same grouping
# `build_row_coupon_installed_parts` consumes, so there is no second definition
# left to drift.  Measured after the repair: volume delta 0.000000, 3 solids vs
# 3 solids.  The zero-interference assertions below are kept -- they are a
# stronger statement than the volume equality and they are what fails if the
# delegation is ever unwound.


def test_row_coupon_artifact_groups_match_installed_assembly_families() -> None:
    params = load_params(PARAMS)
    grouped = group_row_coupon_physical_artifacts_by_installed_part(
        params,
        assembly_position=True,
    )
    installed = _installed_artifact_family_models(params)

    assert set(grouped) == set(installed)
    for family, installed_model in installed.items():
        grouped_body = grouped[family].val()
        installed_body = installed_model.val()
        assert len(grouped_body.Solids()) == len(installed_body.Solids())
        assert _rounded_bounds(grouped_body) == _rounded_bounds(installed_body)
        assert grouped_body.Volume() == pytest.approx(installed_body.Volume(), rel=0.001)

    canonical = grouped["lid_harness_cover"].val()
    standalone = installed["lid_harness_cover"].val()
    assert _rounded_bounds(canonical) == _rounded_bounds(standalone)
    assert canonical.cut(standalone).Volume() == pytest.approx(0.0, abs=1e-6)
    assert standalone.cut(canonical).Volume() == pytest.approx(0.0, abs=1e-6)
    assert len(canonical.Solids()) == len(standalone.Solids()) == 3
    neighbours = {
        "lid_manifold_shell": installed["lid_manifold_shell"],
        "printed_lid_sensor_connector_shrouds": installed[
            "printed_lid_sensor_connector_shrouds"
        ],
        "gas_sensor_pcbs": build_gas_sensor_pcbs(params, assembly_position=True),
        "lid_sensor_service_connectors": build_lid_sensor_service_connectors(
            params,
            assembly_position=True,
        ),
    }
    for name, neighbour in neighbours.items():
        body = neighbour.val()
        assert canonical.intersect(body).Volume() == pytest.approx(0.0, abs=1e-6), name
        assert standalone.intersect(body).Volume() == pytest.approx(0.0, abs=1e-6), name
