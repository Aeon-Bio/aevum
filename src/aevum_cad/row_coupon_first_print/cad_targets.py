"""First-print CAD/QC target tables + section markdown, extracted behavior-preserving.

These ``*_targets()`` functions are the numeric dimensional/acceptance spec each gate
worksheet derives its rows from; ``first_print_cad_target_sections_markdown`` aggregates the
per-gate markdown. Extracted verbatim from the package facade (lines 136/138 consts + 380-1189).
"""

from __future__ import annotations

from typing import Any

from aevum_cad.row_coupon import (
    build_row_coupon_service_parts,
    row_coupon_layout,
    row_coupon_part_manifest,
)

from .constants import FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM
from .models import (
    FirstPrintQCTarget,
    FirstPrintGate2DryAssemblyTarget,
    FirstPrintGate3PlacementTarget,
    FirstPrintGate4WetDryWitnessTarget,
    FirstPrintGate5ConsumablePunctureTarget,
    FirstPrintGate6SensorThermalTarget,
)
from .package import artifact_category


FIRST_PRINT_PUNCTURE_PLATE_SHIFT_LIMIT_MM = 0.25
FIRST_PRINT_DRY_ASSEMBLY_SERVICE_CYCLES = 5


def first_print_qc_targets(params: dict[str, Any]) -> tuple[FirstPrintQCTarget, ...]:
    manifest = row_coupon_part_manifest()["installed"]
    parts = build_row_coupon_service_parts(params, mode="installed")
    targets: list[FirstPrintQCTarget] = []
    for name, entry in manifest.items():
        category = artifact_category(entry["fabrication_source"])
        if category not in {"printed", "compressible_or_flexible"}:
            continue
        bb = parts[name].val().BoundingBox()
        targets.append(
            FirstPrintQCTarget(
                name=name,
                category=category,
                target_x_mm=round(bb.xlen, 2),
                target_y_mm=round(bb.ylen, 2),
                target_z_mm=round(bb.zlen, 2),
                role=entry["role"],
            )
        )
    return tuple(targets)


def first_print_qc_target_bounds_markdown(params: dict[str, Any]) -> str:
    lines = [
        "## Gate 1 CAD Target Bounds",
        "",
        "These are CAD target bounds for first-print caliper comparison. They do",
        "not mark Gate 1 passed, and compressible/flexible parts remain nominal",
        "uncompressed CAD bodies until real stock or printed TPU is measured.",
        "",
        "| Part | Source | Target X mm | Target Y mm | Target Z mm | Role |",
        "|---|---|---:|---:|---:|---|",
    ]
    for target in first_print_qc_targets(params):
        lines.append(
            "| "
            f"`{target.name}` | {target.category} | "
            f"{target.target_x_mm:.2f} | {target.target_y_mm:.2f} | "
            f"{target.target_z_mm:.2f} | {target.role} |"
        )
    return "\n".join(lines)


def first_print_gate3_placement_targets(
    params: dict[str, Any],
) -> tuple[FirstPrintGate3PlacementTarget, ...]:
    layout = row_coupon_layout(params)
    clearance = layout["side_gas_adjacent_slot_clearance"]
    dry_bay = layout["dry_bay_envelope"]
    puncture_check = layout["pipette_puncture_swept_path_check"]
    toolhead_check = layout["pipette_toolhead_swept_body_check"]
    service_dress_check = layout["operating_service_dress_check"]
    row_tiling = layout["row_tiling_service_clearance_check"]
    deck_pod_repeatability = layout["deck_pod_seating_repeatability_check"]
    deck_frame_keepout = layout["deck_frame_keepout_check"]
    assembly_envelope_z = float(layout["assembly_envelope_z"])
    tolerance = FIRST_PRINT_GATE1_QC_DIMENSION_TOLERANCE_MM
    return (
        FirstPrintGate3PlacementTarget(
            target="Assembly deck-to-top envelope",
            cad_value=f"{assembly_envelope_z:.2f} mm",
            physical_check=(
                f"measured high point <= {assembly_envelope_z + tolerance:.2f} mm"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Assembly footprint X",
            cad_value=f"{float(deck_frame_keepout['length_x']):.2f} mm",
            physical_check="seated module stays inside intended deck-frame width",
        ),
        FirstPrintGate3PlacementTarget(
            target="Assembly footprint Y",
            cad_value=f"{float(deck_frame_keepout['width_y']):.2f} mm",
            physical_check="four-plate row stays inside intended deck-frame length",
        ),
        FirstPrintGate3PlacementTarget(
            target="Deck pod seating repeatability",
            cad_value=deck_pod_repeatability["cad_value"],
            physical_check=(
                "five seat/release cycles prove no rocking, yaw, wear, "
                "frame contact, or dry-bay debris"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Adjacent-slot service clearance",
            cad_value=f"{float(clearance['min_vertical_clearance_z']):.2f} mm",
            physical_check=(
                "dressed tube/cable route does not touch adjacent-slot keepout"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Required adjacent-slot clearance",
            cad_value=f"{float(clearance['required_vertical_clearance_z']):.2f} mm",
            physical_check=(
                "measured service dress remains above the keepout by at least "
                "this margin"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Operating service dress envelope",
            cad_value=str(service_dress_check["cad_value"]),
            physical_check=(
                "dressed gas and electrical services stay inside exported "
                "validation body"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Row tiling/service clearance check",
            cad_value=str(row_tiling["cad_value"]),
            physical_check=(
                "inspect printed row with adjacent OT-2 slot/service dress before "
                "operating deck use"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="OT-2 toolhead swept body envelope",
            cad_value=str(toolhead_check["cad_value"]),
            physical_check=(
                "measured OT-2 toolhead body clears exported validation body "
                "at every puncture target"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="OT-2 toolhead lower clearance",
            cad_value=str(toolhead_check["clearance_cad_value"]),
            physical_check=(
                "do not replace conservative CAD envelope without measured "
                "two-pipette OT-2 toolhead evidence"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Pipette puncture targets",
            cad_value=str(puncture_check["target_count_cad_value"]),
            physical_check=(
                "no cap, latch, tube, cable, or connector over any septum target"
            ),
        ),
        FirstPrintGate3PlacementTarget(
            target="Dry-bay protected footprint",
            cad_value=(
                f"{float(dry_bay['length_x']):.2f} x "
                f"{float(dry_bay['width_y']):.2f} mm"
            ),
            physical_check=(
                "no service lead, wet witness path, or debris bridge enters "
                "this footprint"
            ),
        ),
    )


def first_print_ot2_placement_targets_markdown(params: dict[str, Any]) -> str:
    targets = first_print_gate3_placement_targets(params)
    lines = [
        "## Gate 3 CAD Placement Targets",
        "",
        "These are CAD targets for OT-2 placement/no-motion inspection. They do",
        "not mark Gate 3 passed; use them to compare the printed assembly and",
        "dressed services against the current CAD envelope.",
        "",
        "| Target | CAD value | Physical check |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| {target.target} | {target.cad_value} | {target.physical_check} |"
        for target in targets
    )
    return "\n".join(lines)


def first_print_gate2_dry_assembly_targets(
    params: dict[str, Any],
) -> tuple[FirstPrintGate2DryAssemblyTarget, ...]:
    layout = row_coupon_layout(params)
    plate = params["plate"]
    mat = params["septum_mat"]
    latch_ramp = layout["latch_ramp_self_lock"]
    latch_asymmetry = layout["latch_station_asymmetry"]
    wedge_locks = layout["wedge_lock_rectangles"]
    assembly_state = layout["assembly_state_witness_check"]
    gasket_gap_gauge = layout["gasket_compression_gap_gauge"]
    latch_retention = layout["latch_retention_span_check"]
    side_tube_check = layout["side_gas_tube_envelope_check"]
    sensor_summary = layout["sensor_mount_summary"]
    harness = layout["sensor_harness_summary"]
    cable_envelope = layout["sensor_service_cable_envelopes"][0]
    dry_bay = layout["dry_bay_envelope"]
    plate_locator_rails = layout["plate_locator_rails"]
    fail_closed = layout["fail_closed_prerun_inspection_check"]
    return (
        FirstPrintGate2DryAssemblyTarget(
            target="Installed dry stack",
            cad_value=str(assembly_state["stack_cad_value"]),
            physical_check=(
                "dry stack follows production order with no liquid or powered electronics"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Plate/mat service cycles",
            cad_value=f"{FIRST_PRINT_DRY_ASSEMBLY_SERVICE_CYCLES} cycles each",
            physical_check="plates and mats insert, swap, reseat, and remain captured",
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Plate support datum",
            cad_value=(
                f"z={float(layout['plate_bottom_z']):.2f}.."
                f"{float(layout['plate_top_z']):.2f} mm"
            ),
            physical_check=(
                "plate is supported without scraping or contacting optical bottom"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Plate locator rails",
            cad_value=(
                f"{len(plate_locator_rails)} rails / "
                f"{float(plate_locator_rails[0]['height_z']):.2f} mm high"
            ),
            physical_check=(
                "real plate lot loads without filing, rocking, or sidewall crush"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Consumable nominal envelope",
            cad_value=(
                f"{float(plate['length_x']):.2f} x {float(plate['width_y']):.2f} "
                "mm plate / "
                f"{float(mat['sheet_thickness_z']) + float(mat['round_plug_depth_z']):.2f} "
                "mm mat stack"
            ),
            physical_check=(
                "mat seats on plate without lifting plate from locator rails"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Latch gasket squeeze budget",
            cad_value=str(gasket_gap_gauge["cad_value"]),
            physical_check=(
                "latches close stack without plate bow, gasket overcrush, screws, or glue"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Wedge lock stations",
            cad_value=(
                f"{len(wedge_locks)} locks / "
                f"{float(wedge_locks[0]['length_x']):.2f} mm travel body"
            ),
            physical_check=(
                "every printed wedge inserts, detents, releases, and survives cycling"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Latch asymmetry watch",
            cad_value=(
                f"{int(latch_asymmetry['omitted_station_count'])} omitted / "
                f"{float(latch_asymmetry['max_active_station_span_mm']):.2f} mm "
                "max span"
            ),
            physical_check=(
                "inspect wet-frame/lid bow near omitted station before wet tests"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Latch self-lock margin",
            cad_value=(
                f"{float(latch_ramp['self_lock_margin_deg']):.2f} deg / "
                f"{latch_ramp['retention_status']}"
            ),
            physical_check=(
                "detent must hold through dry service cycling before liquid exposure"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Latch retention/span evidence",
            cad_value=str(latch_retention["cad_value"]),
            physical_check=(
                "dry-cycle detent hold, omitted-station bow, post bearing, and "
                "gasket squeeze evidence required before wet tests"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Fail-closed pre-run inspection",
            cad_value=str(fail_closed["cad_value"]),
            physical_check=(
                "any failed blocker row prevents OT-2 operation until corrected"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Side gas service dry fit",
            cad_value=str(side_tube_check["cad_value"]),
            physical_check=(
                "supply and return tubes seat on printed barbs without glue or clamps"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Electrical service dry fit",
            cad_value=(
                f"{int(harness['installed_service_cable_pigtail_count'])} pigtails / "
                f"{float(cable_envelope['min_bend_radius_y']):.2f} mm bend radius"
            ),
            physical_check=(
                "pigtails dress into +Y service exits without pinching covers"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Sensor package dry fit",
            cad_value=(
                f"{int(sensor_summary['gas_sensor_pcb_count'])} gas PCB / "
                f"{int(sensor_summary['headspace_sht41_count'])} SHT41 / "
                f"{int(sensor_summary['ir_thermopile_count'])} IR"
            ),
            physical_check=(
                "real packages or dimensional blanks install and remove without trimming"
            ),
        ),
        FirstPrintGate2DryAssemblyTarget(
            target="Dry-bay open volume",
            cad_value=(
                f"{float(dry_bay['length_x']):.2f} x "
                f"{float(dry_bay['width_y']):.2f} x "
                f"{float(dry_bay['top_z']) - float(dry_bay['bottom_z']):.2f} mm"
            ),
            physical_check=(
                "dry observer bay remains open, unblocked, and free of assembly debris"
            ),
        ),
    )


def first_print_dry_assembly_targets_markdown(params: dict[str, Any]) -> str:
    targets = first_print_gate2_dry_assembly_targets(params)
    lines = [
        "## Gate 2 CAD Dry Assembly Targets",
        "",
        "These are CAD targets for dry production assembly service checks. They",
        "do not mark Gate 2 passed; use them to catch fit, latch, service-dress,",
        "and omitted-latch-span failures before OT-2 placement, wet testing, or",
        "powered sensors.",
        "",
        "| Target | CAD/service value | Physical check |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| {target.target} | {target.cad_value} | {target.physical_check} |"
        for target in targets
    )
    return "\n".join(lines)


def first_print_gate4_wet_dry_witness_targets(
    params: dict[str, Any],
) -> tuple[FirstPrintGate4WetDryWitnessTarget, ...]:
    layout = row_coupon_layout(params)
    headspace_barrier = layout["headspace_barrier_check"]
    headspace_volume = layout["headspace_volume_check"]
    dry_bay_envelope = layout["dry_bay_envelope_check"]
    dry_bay_boundary = layout["dry_bay_boundary_check"]
    dry_bay_ingress = layout["dry_bay_ingress_audit_check"]
    side_gas_leak = layout["side_gas_leak_witness_check"]
    sample_relief_leak = layout["sample_relief_leak_witness_check"]
    gasket_tab_leak = layout["gasket_tab_leak_witness_check"]
    wet_dry_failure_path = layout["wet_dry_failure_path_check"]
    return (
        FirstPrintGate4WetDryWitnessTarget(
            target="Headspace barrier perimeter",
            cad_value=str(headspace_barrier["cad_value"]),
            physical_check=(
                "required barrier body traces sealed gasket perimeter with no dye bypass"
            ),
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Shared wet headspace volume",
            cad_value=str(headspace_volume["cad_value"]),
            physical_check=(
                "required volume body remains continuous and free of blocked bridges"
            ),
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Dry-bay protected volume",
            cad_value=str(dry_bay_envelope["cad_value"]),
            physical_check=(
                "required dry-bay envelope body admits no dye, condensate, debris, or service lead"
            ),
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Dry-bay ingress audit",
            cad_value=str(dry_bay_ingress["cad_value"]),
            physical_check=(
                "exported audit body shows no wet collector, dam, or debris bridge "
                "into protected footprint"
            ),
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Dry-bay boundary rail clearance",
            cad_value=str(dry_bay_boundary["cad_value"]),
            physical_check=(
                "required boundary body leaves side rails clear and unbridged"
            ),
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Side-gas service witness set",
            cad_value=str(side_gas_leak["cad_value"]),
            physical_check="side fitting dye routes to visible outboard collectors",
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Sample/relief cap witness set",
            cad_value=str(sample_relief_leak["cad_value"]),
            physical_check="cap-seat dye routes to visible edge witness",
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Gasket-tab root witness set",
            cad_value=str(gasket_tab_leak["cad_value"]),
            physical_check="lower/upper front/rear tab roots stay outside dry bay",
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Dry-bay aperture thresholds",
            cad_value=str(wet_dry_failure_path["threshold_cad_value"]),
            physical_check="raised collars remain unbridged by dye or support debris",
        ),
        FirstPrintGate4WetDryWitnessTarget(
            target="Aperture-adjacent witness gutters",
            cad_value=str(wet_dry_failure_path["gutter_cad_value"]),
            physical_check=(
                "aperture-side dye stays in witness gutters and out of optics bay"
            ),
        ),
    )


def first_print_wet_dry_witness_targets_markdown(params: dict[str, Any]) -> str:
    targets = first_print_gate4_wet_dry_witness_targets(params)
    lines = [
        "## Gate 4 CAD Wet/Dry Witness Targets",
        "",
        "These are CAD targets for passive dye and condensate inspection. They do",
        "not mark Gate 4 passed; use them to compare visible wet paths against",
        "the current dry-bay ingress audit geometry.",
        "",
        "| Target | CAD value | Physical check |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| {target.target} | {target.cad_value} | {target.physical_check} |"
        for target in targets
    )
    return "\n".join(lines)


def first_print_gate5_consumable_puncture_targets(
    params: dict[str, Any],
) -> tuple[FirstPrintGate5ConsumablePunctureTarget, ...]:
    layout = row_coupon_layout(params)
    plate = params["plate"]
    mat = params["septum_mat"]
    grid = params["well_grid"]
    access = params["pipette_access"]
    metrology = params["consumable_metrology"]
    puncture_check = layout["pipette_puncture_swept_path_check"]
    plate_count = int(params["row"]["plate_count"])
    wells_per_plate = int(grid["columns"]) * int(grid["rows"])
    locator_rail_count = len(layout["plate_locator_rails"])
    locator_height = params["plate_support"]["lateral_locator_wall_height_z"]
    mat_stack_height = float(mat["sheet_thickness_z"]) + float(mat["round_plug_depth_z"])
    gauge_x = float(plate["length_x"]) + 2 * float(metrology["gauge_border_xy"])
    gauge_y = float(plate["width_y"]) + 2 * float(metrology["gauge_border_xy"])
    gauge_z = float(metrology["gauge_base_thickness_z"])
    return (
        FirstPrintGate5ConsumablePunctureTarget(
            target="Installed consumable set",
            cad_value=f"{plate_count} plates / {plate_count} septum mats",
            physical_check="real CellVis plates and Cole-Parmer mats required for pass",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Consumable metrology gauge",
            cad_value=f"{gauge_x:.2f} x {gauge_y:.2f} x {gauge_z:.2f} mm",
            physical_check=(
                "required gauge checks plate/mat lot fit before puncture claims"
            ),
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Plate CAD footprint",
            cad_value=(
                f"{float(plate['length_x']):.2f} x {float(plate['width_y']):.2f} x "
                f"{float(plate['height_z']):.2f} mm"
            ),
            physical_check="measure real plate lot; revise only if fit check fails",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Plate support datum",
            cad_value=f"z={float(layout['plate_bottom_z']):.2f} mm",
            physical_check="plate underside support contacts avoid optical bottom",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Locator rail count/height",
            cad_value=f"{locator_rail_count} rails / {float(locator_height):.2f} mm",
            physical_check="rails constrain lateral shift without pinching plate",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Mat CAD thickness stack",
            cad_value=f"{mat_stack_height:.2f} mm",
            physical_check=(
                "sheet plus plug depth placeholder; replace with measured mat data"
            ),
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Mat plug CAD diameter/depth",
            cad_value=(
                f"{float(mat['round_plug_diameter']):.2f} mm / "
                f"{float(mat['round_plug_depth_z']):.2f} mm"
            ),
            physical_check="plug fits wells without bottoming, bunching, or lifting plate",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Mat slit CAD relief",
            cad_value=(
                f"{float(mat['slit_cut_length_x']):.2f} x "
                f"{float(mat['slit_cut_width_y']):.2f} mm"
            ),
            physical_check="tip admits through slit without tearing or persistent opening",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Puncture target count",
            cad_value=str(puncture_check["target_count_cad_value"]),
            physical_check=(
                f"required swept-path validation body covers all "
                f"{wells_per_plate} positions per plate"
            ),
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Puncture swept diameter",
            cad_value=str(puncture_check["diameter_cad_value"]),
            physical_check="tip plus radial clearance through septum target",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Puncture Z range",
            cad_value=str(puncture_check["z_range_cad_value"]),
            physical_check=(
                f"{float(access['puncture_depth_below_mat_top_z']):.2f} mm below mat top"
            ),
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Puncture force limit",
            cad_value=f"{float(access['puncture_force_limit_n']):.2f} N",
            physical_check="revise if intended tip/mat combination exceeds this force",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Repeat puncture minimum",
            cad_value=f"{int(access['repeat_puncture_cycles_min'])} cycles",
            physical_check="same representative well reseals without unacceptable wear",
        ),
        FirstPrintGate5ConsumablePunctureTarget(
            target="Plate lateral shift limit",
            cad_value=f"<={FIRST_PRINT_PUNCTURE_PLATE_SHIFT_LIMIT_MM:.2f} mm",
            physical_check="compare plate/mat datum positions before and after puncture",
        ),
    )


def first_print_consumable_puncture_targets_markdown(params: dict[str, Any]) -> str:
    targets = first_print_gate5_consumable_puncture_targets(params)
    lines = [
        "## Gate 5 CAD Consumable/Puncture Targets",
        "",
        "These are CAD and protocol targets for consumable metrology and first",
        "puncture testing. They do not mark Gate 5 passed; the Cole-Parmer mat",
        "dimensions remain measurement-gated until real caliper and wet-exposure",
        "data replace the current CAD assumptions.",
        "",
        "| Target | CAD/protocol value | Physical check |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| {target.target} | {target.cad_value} | {target.physical_check} |"
        for target in targets
    )
    return "\n".join(lines)


def first_print_gate6_sensor_thermal_targets(
    params: dict[str, Any],
) -> tuple[FirstPrintGate6SensorThermalTarget, ...]:
    layout = row_coupon_layout(params)
    install_check = layout["sensor_installation_path_check"]
    harness = layout["sensor_harness_summary"]
    gas_mounts = layout["gas_sensor_pcb_mounts"]
    sht_mounts = layout["headspace_sht41_mounts"]
    ir_mounts = layout["ir_sensor_mounts"]
    ir_fov_spot = layout["ir_thermopile_fov_spot_check"]
    thermal_proxy = layout["thermal_condensation_proxy_check"]
    gas_mount = gas_mounts[0]
    gas_flow_cell = layout["gas_pcb_flow_cell_check"]
    gas_interface = gas_mount["gas_interface"]
    sht_mount = sht_mounts[0]
    ir_mount = ir_mounts[0]
    face_gasket = ir_mount["face_gasket"]
    connector_clearance_check = layout["sensor_connector_service_clearance_check"]
    cable_envelope_check = layout["sensor_service_cable_envelope_check"]
    mating_state_check = layout["electrical_connector_mating_state_check"]
    observer_front_end = layout["observer_front_end_swept_body_check"]
    observer_carriage = layout["observer_carriage_envelope_check"]
    observer_service_raceway = layout["observer_service_raceway_envelope_check"]
    observer_optical_stability = layout["observer_optical_stability_check"]
    observer_kinematic_split = layout["observer_kinematic_split_check"]

    return (
        FirstPrintGate6SensorThermalTarget(
            target="Sensor install workflow",
            cad_value=str(install_check["cad_value"]),
            physical_check=(
                "install/remove follows printed reversible no-screws/no-glue policy"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Gas PCB cartridges",
            cad_value=(
                f"{len(gas_mounts)} cartridges, "
                f"{float(gas_mount['length_x']):.2f} x "
                f"{float(gas_mount['width_y']):.2f} x "
                f"{float(gas_mount['height_z']):.2f} mm"
            ),
            physical_check=(
                "supply/return cartridges seat in dry-side duct sampling cassettes"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Gas PCB aperture/dead volume",
            cad_value=gas_flow_cell["cad_value"],
            physical_check=(
                "aperture aligns to required duct sampling cell validation body, "
                "not open top headspace"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Gas PCB gasket",
            cad_value=(
                f"{float(gas_interface['nominal_gasket_thickness_x']):.2f} mm "
                "gasket / "
                f"{float(gas_interface['nominal_compression_x']):.2f} mm "
                "compression"
            ),
            physical_check="interface gasket visibly seats without crushing sensor package",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Headspace SHT41 carriers",
            cad_value=(
                f"{len(sht_mounts)} carriers, "
                f"{float(sht_mount['length_x']):.2f} x "
                f"{float(sht_mount['width_y']):.2f} x "
                f"{float(sht_mount['height_z']):.2f} mm"
            ),
            physical_check="one membrane aperture exposed per plate-local headspace",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Headspace SHT41 aperture",
            cad_value=(
                f"{float(sht_mount['aperture_diameter']):.2f} mm aperture / "
                f"{float(sht_mount['drip_break_ring']['outer_diameter']):.2f} mm "
                "drip ring OD"
            ),
            physical_check=(
                "membrane is exposed while pooling is kept off carrier electronics"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="IR thermopile pockets",
            cad_value=(
                f"{len(ir_mounts)} pockets, "
                f"{float(ir_mount['length_x']):.2f} x "
                f"{float(ir_mount['width_y']):.2f} x "
                f"{float(ir_mount['height_z']):.2f} mm"
            ),
            physical_check="plate-margin thermopiles seat with lens unobstructed",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="IR aperture/gasket",
            cad_value=(
                f"{float(ir_mount['aperture_diameter']):.2f} mm aperture / "
                f"{float(face_gasket['height_z']):.2f} mm gasket / "
                f"{float(face_gasket['nominal_compression_z']):.2f} mm "
                "compression"
            ),
            physical_check="face gasket centered and dry-side aperture face sealed",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="IR proxy FOV spot",
            cad_value=str(ir_fov_spot["spot_cad_value"]),
            physical_check=(
                "proxy only; edge-to-center plan required before cell-temperature claims"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Harness route count",
            cad_value=(
                f"{int(harness['lower_ir_route_count'])} lower / "
                f"{int(harness['lid_sensor_route_count'])} lid routes"
            ),
            physical_check="covered routes keep wires out of wet chamber and pipette field",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Service connectors/cables",
            cad_value=str(mating_state_check["cad_value"]),
            physical_check="continuity survives five install/remove service cycles",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Sensor connector service clearance",
            cad_value=str(connector_clearance_check["cad_value"]),
            physical_check=(
                "required connector clearance body stays open through mating "
                "and cable service"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Service cable envelope",
            cad_value=str(cable_envelope_check["cad_value"]),
            physical_check="row-end cable dress stays in modeled +Y envelope",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Service cable bend envelope",
            cad_value=str(cable_envelope_check["bend_cad_value"]),
            physical_check="external cable dress does not kink or pull connector shrouds",
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Observer front-end swept volume",
            cad_value=str(observer_front_end["cad_value"]),
            physical_check=(
                "required front-end swept body clears apertures and focus travel"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Observer carriage reserved volume",
            cad_value=str(observer_carriage["cad_value"]),
            physical_check=(
                "required carriage envelope stays outside wet stack and pipette field"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Observer service raceway envelope",
            cad_value=str(observer_service_raceway["cad_value"]),
            physical_check=(
                "required service raceway body keeps observer loop out of wet chamber"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Observer optical stability evidence",
            cad_value=str(observer_optical_stability["cad_value"]),
            physical_check=(
                "do not claim observer imaging/Raman quality until every optical "
                "checkpoint has evidence"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Observer kinematic split evidence",
            cad_value=str(observer_kinematic_split["cad_value"]),
            physical_check=(
                "front-end, carriage, focus travel, and service loop split must "
                "be evidenced before observer readiness claims"
            ),
        ),
        FirstPrintGate6SensorThermalTarget(
            target="Thermal proxy plan",
            cad_value=str(thermal_proxy["cad_value"]),
            physical_check=(
                "center-to-edge correlation and condensation pocket inspection plan "
                "required before cell-temperature claims"
            ),
        ),
    )


def first_print_sensor_thermal_targets_markdown(params: dict[str, Any]) -> str:
    targets = first_print_gate6_sensor_thermal_targets(params)
    lines = [
        "## Gate 6 CAD Sensor/Thermal Targets",
        "",
        "These are CAD targets for sensor installation and first thermal-proxy",
        "planning. They do not mark Gate 6 passed and do not prove gas response,",
        "RH response, CO2 control, IR calibration, or biology readiness.",
        "",
        "| Target | CAD/protocol value | Physical check |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| {target.target} | {target.cad_value} | {target.physical_check} |"
        for target in targets
    )
    return "\n".join(lines)


def first_print_cad_target_sections_markdown(
    params: dict[str, Any],
) -> dict[str, str]:
    return {
        "Gate 1 CAD Target Bounds": first_print_qc_target_bounds_markdown(params),
        "Gate 2 CAD Dry Assembly Targets": first_print_dry_assembly_targets_markdown(
            params
        ),
        "Gate 3 CAD Placement Targets": first_print_ot2_placement_targets_markdown(
            params
        ),
        "Gate 4 CAD Wet/Dry Witness Targets": (
            first_print_wet_dry_witness_targets_markdown(params)
        ),
        "Gate 5 CAD Consumable/Puncture Targets": (
            first_print_consumable_puncture_targets_markdown(params)
        ),
        "Gate 6 CAD Sensor/Thermal Targets": (
            first_print_sensor_thermal_targets_markdown(params)
        ),
    }
