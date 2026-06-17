# ruff: noqa: E402, F821, I001
"""Open this file in CQ-Editor to inspect the one-row coupon.

Running it from plain Python prints model bounds as a smoke test.
"""

import argparse
import importlib
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import aevum_cad.params as params_module  # noqa: E402
import aevum_cad.row_coupon as row_coupon_module  # noqa: E402

params_module = importlib.reload(params_module)
row_coupon_module = importlib.reload(row_coupon_module)

load_params = params_module.load_params
ROW_COUPON_SERVICE_MODES = row_coupon_module.ROW_COUPON_SERVICE_MODES
build_flow_test_adapters = row_coupon_module.build_flow_test_adapters
build_latch_mechanism_demo_parts = row_coupon_module.build_latch_mechanism_demo_parts
build_row_coupon_service_parts = row_coupon_module.build_row_coupon_service_parts
build_row_coupon_validation_parts = row_coupon_module.build_row_coupon_validation_parts


DEFAULT_PARAMS = ROOT / "cad" / "one_row_coupon.params.json"


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _params_path(*values: str | Path | None) -> Path:
    for value in values:
        if value is None:
            continue
        candidate = Path(value)
        if candidate.suffix.lower() != ".json":
            continue
        if candidate.is_absolute():
            return candidate
        cwd_candidate = Path.cwd() / candidate
        if cwd_candidate.exists():
            return cwd_candidate
        return ROOT / candidate
    return DEFAULT_PARAMS


parser = argparse.ArgumentParser()
parser.add_argument(
    "params",
    nargs="?",
    default=None,
    help="Path to a one-row coupon params JSON file.",
)
parser.add_argument(
    "--view-mode",
    default=os.environ.get("AEVUM_ROW_COUPON_VIEW_MODE", "installed"),
    choices=list(ROW_COUPON_SERVICE_MODES),
    help="Installed or service-state view.",
)
parser.add_argument(
    "--show-flow-adapters",
    action="store_true",
    default=_env_flag("AEVUM_ROW_COUPON_SHOW_FLOW_ADAPTERS"),
    help="Show removable passive-flow test adapters on the service ports.",
)
parser.add_argument(
    "--show-validation-tools",
    action="store_true",
    default=_env_flag("AEVUM_ROW_COUPON_SHOW_VALIDATION_TOOLS"),
    help="Show physical/review tools for COTS metrology and pipette puncture checks.",
)
parser.add_argument(
    "--show-latch-demo",
    action="store_true",
    default=_env_flag("AEVUM_ROW_COUPON_SHOW_LATCH_DEMO"),
    help="Show the printable non-print-in-place latch mechanism demonstrator.",
)
parser.add_argument(
    "--show-internal-electronics",
    action="store_true",
    default=_env_flag("AEVUM_ROW_COUPON_SHOW_INTERNAL_ELECTRONICS"),
    help="Show enclosed PCB/electronics envelopes that are hidden in the default surface view.",
)
args, _unknown = parser.parse_known_args()

params = load_params(_params_path(args.params, *_unknown))
parts = build_row_coupon_service_parts(params, mode=args.view_mode)
if args.view_mode == "installed" and not args.show_internal_electronics:
    parts.pop("gas_sensor_pcbs", None)
if args.show_flow_adapters:
    parts["flow_test_adapters"] = build_flow_test_adapters(
        params,
        assembly_position=True,
    )
if args.show_validation_tools:
    parts.update(build_row_coupon_validation_parts(params))
if args.show_latch_demo:
    parts.update(build_latch_mechanism_demo_parts(params, assembly_position=True))

PART_OPTIONS = {
    "deck_pods": {"alpha": 0.76, "color": (0.55, 0.58, 0.62)},
    "plate_support_frame": {"alpha": 0.78, "color": (0.75, 0.78, 0.82)},
    "ir_thermopiles": {"alpha": 0.9, "color": (0.1, 0.1, 0.12)},
    "ir_thermopile_face_gaskets": {"alpha": 0.78, "color": (0.34, 0.78, 0.46)},
    "lower_sensor_harness": {"alpha": 0.9, "color": (0.04, 0.04, 0.05)},
    "lower_harness_cover": {"alpha": 0.82, "color": (0.5, 0.52, 0.56)},
    "lower_sensor_service_connector": {"alpha": 0.9, "color": (0.04, 0.08, 0.05)},
    "printed_lower_sensor_connector_shroud": {"alpha": 0.8, "color": (0.45, 0.47, 0.5)},
    "lower_sensor_service_cable_pigtail": {"alpha": 0.86, "color": (0.02, 0.02, 0.03)},
    "lower_gasket": {"alpha": 0.72, "color": (0.36, 0.78, 0.5)},
    "wet_chamber_frame": {"alpha": 0.36, "color": (0.12, 0.48, 0.45)},
    "cots_microplates": {"alpha": 0.62, "color": (0.25, 0.7, 0.95)},
    "cots_septum_mats": {"alpha": 0.7, "color": (0.75, 0.35, 0.95)},
    "upper_gasket": {"alpha": 0.76, "color": (0.4, 0.8, 0.45)},
    "lid_manifold_shell": {"alpha": 0.34, "color": (0.95, 0.68, 0.25)},
    "headspace_sht41_microcarriers": {"alpha": 0.86, "color": (0.02, 0.55, 0.28)},
    "lid_sensor_harness": {"alpha": 0.9, "color": (0.02, 0.04, 0.05)},
    "lid_harness_cover": {"alpha": 0.78, "color": (0.72, 0.5, 0.24)},
    "lid_sensor_service_connectors": {"alpha": 0.9, "color": (0.04, 0.08, 0.05)},
    "printed_lid_sensor_connector_shrouds": {"alpha": 0.8, "color": (0.72, 0.5, 0.24)},
    "lid_sensor_service_cable_pigtails": {"alpha": 0.86, "color": (0.02, 0.02, 0.03)},
    "lid_cover": {"alpha": 0.5, "color": (0.95, 0.55, 0.18)},
    "cots_gas_service_tubes": {"alpha": 0.82, "color": (0.05, 0.05, 0.06)},
    "gas_pcb_interface_gaskets": {"alpha": 0.78, "color": (0.18, 0.72, 0.58)},
    "printed_gas_pcb_keeper_doors": {"alpha": 0.88, "color": (0.82, 0.48, 0.18)},
    "gas_sensor_pcbs": {"alpha": 0.86, "color": (0.0, 0.42, 0.22)},
    "sensor_connector_service_clearance_check": {"alpha": 0.16, "color": (0.9, 0.2, 0.1)},
    "sensor_service_cable_envelope_check": {"alpha": 0.18, "color": (0.95, 0.18, 0.45)},
    "electrical_connector_mating_state_check": {"alpha": 0.24, "color": (1.0, 0.34, 0.0)},
    "sensor_installation_path_check": {"alpha": 0.22, "color": (0.95, 0.95, 0.1)},
    "gas_pcb_flow_cell_check": {"alpha": 0.28, "color": (0.15, 0.85, 1.0)},
    "side_gas_tube_envelope_check": {"alpha": 0.18, "color": (0.1, 0.75, 1.0)},
    "side_gas_leak_witness_check": {"alpha": 0.32, "color": (1.0, 0.65, 0.05)},
    "sample_relief_leak_witness_check": {"alpha": 0.34, "color": (1.0, 0.82, 0.05)},
    "gasket_tab_leak_witness_check": {"alpha": 0.34, "color": (0.95, 0.9, 0.18)},
    "dry_bay_ingress_audit_check": {"alpha": 0.18, "color": (1.0, 0.28, 0.0)},
    "adjacent_deck_slot_keepout_check": {"alpha": 0.14, "color": (1.0, 0.25, 0.12)},
    "printed_sample_relief_cap": {"alpha": 0.88, "color": (0.18, 0.55, 0.92)},
    "printed_wedge_locks": {"alpha": 0.86, "color": (0.9, 0.2, 0.16)},
    "unseated_wedge_locks_review": {"alpha": 0.72, "color": (1.0, 0.24, 0.08)},
    "latch_unseated_witnesses": {"alpha": 0.62, "color": (1.0, 0.85, 0.0)},
    "missing_microplate_witnesses": {"alpha": 0.56, "color": (1.0, 0.14, 0.02)},
    "missing_septum_mat_witnesses": {"alpha": 0.58, "color": (1.0, 0.08, 0.05)},
    "missing_perimeter_gasket_witnesses": {"alpha": 0.58, "color": (1.0, 0.18, 0.0)},
    "missing_gas_pcb_cartridge_witnesses": {"alpha": 0.62, "color": (1.0, 0.12, 0.02)},
    "missing_service_lead_witnesses": {"alpha": 0.62, "color": (1.0, 0.2, 0.0)},
    "unmated_sensor_service_connectors_review": {"alpha": 0.68, "color": (1.0, 0.34, 0.0)},
    "missing_sample_relief_cap_witness": {"alpha": 0.62, "color": (1.0, 0.1, 0.05)},
    "unseated_sample_relief_cap_review": {"alpha": 0.78, "color": (1.0, 0.45, 0.0)},
    "flow_test_adapters": {"alpha": 0.78, "color": (0.15, 0.25, 0.95)},
    "consumable_metrology_gauge": {"alpha": 0.82, "color": (0.95, 0.92, 0.35)},
    "deck_slot_footprint_check": {"alpha": 0.18, "color": (0.8, 0.8, 0.85)},
    "deck_frame_keepout_check": {"alpha": 0.16, "color": (1.0, 0.3, 0.18)},
    "deck_pod_seating_repeatability_check": {
        "alpha": 0.76,
        "color": (0.25, 0.72, 0.28),
    },
    "dry_bay_envelope_check": {"alpha": 0.12, "color": (0.0, 0.78, 0.9)},
    "dry_bay_boundary_check": {"alpha": 0.22, "color": (0.0, 0.55, 0.75)},
    "headspace_barrier_check": {"alpha": 0.18, "color": (0.25, 0.9, 0.45)},
    "headspace_volume_check": {"alpha": 0.10, "color": (0.2, 0.75, 0.35)},
    "well_cell_plane_check": {"alpha": 0.34, "color": (0.95, 0.15, 0.65)},
    "ir_thermopile_fov_spot_check": {"alpha": 0.46, "color": (1.0, 0.86, 0.12)},
    "thermal_condensation_proxy_check": {
        "alpha": 0.38,
        "color": (0.16, 0.82, 0.72),
    },
    "pipette_puncture_swept_path_check": {"alpha": 0.22, "color": (0.1, 0.35, 1.0)},
    "pipette_toolhead_swept_body_check": {"alpha": 0.10, "color": (0.02, 0.16, 0.95)},
    "observer_front_end_swept_body_check": {"alpha": 0.20, "color": (0.0, 0.7, 0.95)},
    "observer_carriage_envelope_check": {"alpha": 0.16, "color": (0.05, 0.55, 0.85)},
    "observer_service_raceway_envelope_check": {"alpha": 0.18, "color": (0.0, 0.85, 0.65)},
    "observer_fiducial_focus_target_check": {"alpha": 0.38, "color": (0.0, 0.95, 0.9)},
    "observer_optical_stability_check": {"alpha": 0.70, "color": (0.58, 0.34, 0.95)},
    "assembly_state_witness_check": {"alpha": 0.50, "color": (1.0, 0.22, 0.02)},
    "gasket_compression_gap_gauge": {"alpha": 0.82, "color": (0.98, 0.68, 0.08)},
    "latch_retention_span_check": {"alpha": 0.78, "color": (0.95, 0.48, 0.14)},
    "fail_closed_prerun_inspection_check": {
        "alpha": 0.78,
        "color": (0.85, 0.16, 0.20),
    },
    "material_cleaning_witness_coupon": {"alpha": 0.82, "color": (0.42, 0.72, 0.26)},
    "row_tiling_service_clearance_check": {
        "alpha": 0.14,
        "color": (0.05, 0.72, 0.42),
    },
    "wet_dry_failure_path_check": {"alpha": 0.34, "color": (0.0, 0.6, 0.95)},
    "latch_demo_lower_catch": {"alpha": 0.84, "color": (0.14, 0.46, 0.43)},
    "latch_demo_compressed_gasket": {"alpha": 0.72, "color": (0.36, 0.78, 0.5)},
    "latch_demo_upper_receiver": {"alpha": 0.6, "color": (0.95, 0.55, 0.18)},
    "latch_demo_sliding_wedge": {"alpha": 0.9, "color": (0.9, 0.2, 0.16)},
}

try:
    _show_object = show_object  # type: ignore[name-defined] # noqa: F821
except NameError:
    _show_object = None

if _show_object is not None:
    for name, part in parts.items():
        _show_object(
            part,
            name=f"{params['name']}_{name}",
            options=PART_OPTIONS[name],
        )
else:
    print(f"{params['name']} ({args.view_mode} parts)")
    for name, part in parts.items():
        bb = part.val().BoundingBox()
        print(f"{name}: bounds x={bb.xlen:.2f} y={bb.ylen:.2f} z={bb.zlen:.2f} mm")
    print("Open this file in CQ-Editor to view it interactively.")
