from __future__ import annotations

from pathlib import Path

import pytest

from aevum_cad.params import load_params
from aevum_cad.row_coupon.artifacts import (
    _keeper_door_models,
    _lid_harness_cover_models,
    _printed_lid_shroud_models,
    row_coupon_physical_artifact_specs,
)
from aevum_cad.row_coupon.layout import row_coupon_layout
from aevum_cad.row_coupon.parts.gas_pcb import (
    build_cots_gas_service_tubes,
    build_gas_sensor_pcbs,
)
from aevum_cad.row_coupon.parts.harness import (
    build_lid_sensor_service_connectors,
    build_lower_sensor_harness,
    build_lower_sensor_service_connector,
    build_printed_lower_sensor_connector_shroud,
)
from aevum_cad.row_coupon.parts.sample_relief import build_printed_sample_relief_cap
from aevum_cad.row_coupon.parts.sealing import build_upper_gasket
from aevum_cad.row_coupon.parts.structural import build_lid_cover, build_lid_manifold_shell

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "cad" / "one_row_coupon.params.json"
EPSILON_MM3 = 1e-6


@pytest.fixture(scope="module")
def service_stack() -> dict[str, object]:
    params = load_params(PARAMS)
    return {
        "params": params,
        "layout": row_coupon_layout(params),
        "lid_cover": build_lid_cover(params, assembly_position=True),
        "lid_shell": build_lid_manifold_shell(params, assembly_position=True),
        "connectors": build_lid_sensor_service_connectors(params, assembly_position=True),
        "pcbs": build_gas_sensor_pcbs(params, assembly_position=True),
        "lower_connector": build_lower_sensor_service_connector(params, assembly_position=True),
        "lower_harness": build_lower_sensor_harness(params, assembly_position=True),
        "lower_shroud": build_printed_lower_sensor_connector_shroud(params, assembly_position=True),
        "covers": _lid_harness_cover_models(params, assembly_position=True),
        "shrouds": _printed_lid_shroud_models(params, assembly_position=True),
        "doors": _keeper_door_models(params, assembly_position=True),
    }


def _overlap_mm3(left: object, right: object) -> float:
    return float(left.intersect(right).val().Volume())


def test_service_artifact_ids_remain_canonical() -> None:
    params = load_params(PARAMS)
    ids = {spec.name for spec in row_coupon_physical_artifact_specs(params)}
    assert {
        "lid_harness_cover_lid_cover_left_gas_bus",
        "lid_harness_cover_lid_cover_right_gas_bus",
        "lid_harness_cover_lid_shell_right_sht41_bus",
        "printed_lower_sensor_connector_shroud",
        "printed_lid_sensor_connector_shroud_lid_left_gas_service_connector",
        "printed_lid_sensor_connector_shroud_lid_right_sensor_service_connector",
        "gas_pcb_interface_gasket_supply_gas_sensor_pcb",
        "gas_pcb_interface_gasket_return_gas_sensor_pcb",
        "printed_gas_pcb_keeper_door_supply_gas_sensor_pcb",
        "printed_gas_pcb_keeper_door_return_gas_sensor_pcb",
        "printed_sample_relief_cap",
    } <= ids


def test_rigid_service_parts_do_not_consume_installed_mates(
    service_stack: dict[str, object],
) -> None:
    cover = service_stack["lid_cover"]
    shell = service_stack["lid_shell"]
    for name, model in service_stack["covers"].items():
        owner = shell if "lid_shell" in name else cover
        assert len(model.solids().vals()) == 1
        assert _overlap_mm3(model, owner) <= EPSILON_MM3

    connectors = service_stack["connectors"]
    for model in service_stack["shrouds"].values():
        assert len(model.solids().vals()) == 1
        assert _overlap_mm3(model, connectors) <= EPSILON_MM3
        assert _overlap_mm3(model, cover) <= EPSILON_MM3

    lower_shroud = service_stack["lower_shroud"]
    assert len(lower_shroud.solids().vals()) == 1
    assert _overlap_mm3(lower_shroud, service_stack["lower_connector"]) <= EPSILON_MM3
    assert _overlap_mm3(lower_shroud, service_stack["lower_harness"]) <= EPSILON_MM3

    pcbs = service_stack["pcbs"]
    for model in service_stack["doors"].values():
        assert len(model.solids().vals()) == 1
        assert _overlap_mm3(model, pcbs) <= EPSILON_MM3
        assert _overlap_mm3(model, cover) <= EPSILON_MM3


def test_sensor_drip_breaks_clear_the_compressed_upper_gasket(
    service_stack: dict[str, object],
) -> None:
    gasket = build_upper_gasket(service_stack["params"], assembly_position=True)
    assert _overlap_mm3(gasket, service_stack["lid_shell"]) <= EPSILON_MM3


def test_service_motion_retention_and_print_targets_are_explicit(
    service_stack: dict[str, object],
) -> None:
    layout = service_stack["layout"]
    assert {trunk["install_axis"] for trunk in layout["lid_sensor_harness_trunks"]} == {
        "+Z",
        "-Z",
    }
    assert all(
        "physical_retention_gate" in trunk["retention"]
        for trunk in layout["lid_sensor_harness_trunks"]
    )
    assert all(
        "no_internal_support" in trunk["critical_surface_printing"]
        for trunk in layout["lid_sensor_harness_trunks"]
    )

    lower_shroud = layout["lower_ir_connector_envelope"]["printed_shroud"]
    assert lower_shroud["install_axis"] == "+Z_from_below_to_datum"
    assert lower_shroud["removal_axis"] == "-Z_then_+Y_connector_unmate"

    for connector in layout["lid_service_connector_envelopes"]:
        shroud = connector["printed_shroud"]
        assert shroud["install_axis"] == "+Z"
        assert shroud["retention_target"]
        assert shroud["physical_gate"]
        assert "no_internal_support" in shroud["print_orientation"]

    assert lower_shroud["retention_target"]
    assert lower_shroud["physical_gate"]
    assert "no_internal_support" in lower_shroud["print_orientation"]

    for mount in layout["gas_sensor_pcb_mounts"]:
        assert mount["keeper_install_axis"] == mount["keeper_removal_axis"] == "+Z"
        assert mount["keeper_vertical_clearance_z"] > 0
        assert mount["keeper_physical_gate"]
        assert "no_internal_support" in mount["keeper_print_orientation"]
        interface = mount["gas_interface"]
        assert 0 < interface["nominal_compression_x"] < interface["nominal_gasket_thickness_x"]
        assert interface["gasket_material_intent"].endswith("printed_tpu")
        assert interface["gasket_physical_gate"]
        assert "no_support" in interface["gasket_print_orientation"]


def test_flexible_service_mates_keep_bend_interference_and_physical_gates_explicit(
    service_stack: dict[str, object],
) -> None:
    params = service_stack["params"]
    layout = service_stack["layout"]
    tubes = build_cots_gas_service_tubes(params, assembly_position=True)
    cap = build_printed_sample_relief_cap(params, assembly_position=True)
    assert len(tubes.solids().vals()) == 2
    assert len(cap.solids().vals()) == 1

    for interface in layout["side_gas_service_interfaces"]:
        retention = interface["tube_retention"]
        assert interface["tube_min_bend_radius"] >= 18.0
        assert interface["installed_tube"]["route_axis"] in {"-X", "+X", "-Y", "+Y"}
        assert retention["tube_inner_diameter"] <= retention["stem_diameter"]
        assert retention["barb_peak_diameter"] > retention["tube_inner_diameter"]
        assert "no_glue" in retention["retention"]

    relief = next(port for port in layout["lid_port_positions"] if port["role"] == "sample_relief")
    assert relief["cap_install_axis"] == "-Z"
    assert relief["cap_removal_axis"] == "+Z"
    assert relief["cap_seal_lip_nominal_compression_z"] > 0
    assert relief["cap_physical_gate"]
    assert "no_destructive_cleanup" in relief["cap_critical_surface_printing"]
