"""Manual dye-dispense scaffold for the Aevum P300 PoC fixture.

Run this only after the dry-motion target class has passed. Normal Aevum
operation should go through the agent OT-2 bridge; this file is a guarded manual
override for first wet evidence.
"""

from opentrons.types import Point

from opentrons import protocol_api

metadata = {
    "protocolName": "Aevum P300 PoC Fixture Dye Test",
    "author": "Aevum",
    "description": "Small-volume dye dispense checks for off-axis P300 access.",
}

PROTOCOL_API_LEVEL = "2.28"

requirements = {"robotType": "OT-2", "apiLevel": PROTOCOL_API_LEVEL}

PIPETTE_NAME = "p300_single_gen2"
PIPETTE_MOUNT = "left"
TIPRACK_LOAD_NAME = "opentrons_96_tiprack_300ul"
TIPRACK_SLOT = "2"
FIXTURE_SLOT = "1"

# Change these if your available dye source labware differs.
DYE_SOURCE_LOAD_NAME = "nest_12_reservoir_15ml"
DYE_SOURCE_SLOT = "3"
DYE_SOURCE_WELL = "A1"

PORT_OFFSET_BY_COLUMN_MM = {
    "1": 0.0,
    "2": 1.0,
    "3": 1.5,
    "4": 2.0,
}
TARGET_FINAL_PORT_OFFSET_MM = 1.5

DYE_VOLUME_UL = 5
PRE_WET_VOLUME_UL = 20
ASPIRATE_RATE_UL_S = 15
DISPENSE_RATE_UL_S = 8
SAFE_CLEARANCE_ABOVE_MAT_MM = 15
PRE_ENTRY_ABOVE_PLATE_TOP_MM = 5
DISPENSE_DEPTH_BELOW_PLATE_TOP_MM = 2
POST_DISPENSE_DWELL_S = 1

ALLOW_MANUAL_DYE_RUN = False
REGISTERED_FIXTURE_OFFSET_MM = None
DRY_TARGET_CLASSES_VERIFIED = False
CAPTURE_CAMERA_EVIDENCE = True
CAMERA_RESOLUTION = (1920, 1080)

# Start wet testing on row C, whose cassette guide holes are 4.0 mm. Row A/B
# are tighter clearance tests; row D is the large-clearance boundary. A +2.0 mm
# column is still a boundary offset and should not be used first.
TARGET_WELLS = ["C1", "C2", "C3"]


def _port_target(well, column: str, z_from_plate_top_mm: float):
    dx = PORT_OFFSET_BY_COLUMN_MM[column]
    return well.top(z=z_from_plate_top_mm).move(Point(x=dx, y=0, z=0))


def run(protocol: protocol_api.ProtocolContext):
    if (
        not ALLOW_MANUAL_DYE_RUN
        or REGISTERED_FIXTURE_OFFSET_MM is None
        or not DRY_TARGET_CLASSES_VERIFIED
    ):
        raise RuntimeError(
            "Do not run dye tests until dry target classes are verified and the "
            "fixture offset is recorded. Set ALLOW_MANUAL_DYE_RUN=True, "
            "DRY_TARGET_CLASSES_VERIFIED=True, and REGISTERED_FIXTURE_OFFSET_MM "
            "only for a documented manual commissioning run."
        )

    fixture = protocol.load_labware("aevum_p300_poc_fixture", FIXTURE_SLOT)
    dye_source = protocol.load_labware(DYE_SOURCE_LOAD_NAME, DYE_SOURCE_SLOT)
    tiprack = protocol.load_labware(TIPRACK_LOAD_NAME, TIPRACK_SLOT)
    p300 = protocol.load_instrument(PIPETTE_NAME, PIPETTE_MOUNT, tip_racks=[tiprack])
    fixture.set_offset(
        x=REGISTERED_FIXTURE_OFFSET_MM[0],
        y=REGISTERED_FIXTURE_OFFSET_MM[1],
        z=REGISTERED_FIXTURE_OFFSET_MM[2],
    )

    p300.flow_rate.aspirate = ASPIRATE_RATE_UL_S
    p300.flow_rate.dispense = DISPENSE_RATE_UL_S

    if CAPTURE_CAMERA_EVIDENCE:
        protocol.capture_image(
            filename="aevum_dye_fixture_loaded",
            resolution=CAMERA_RESOLUTION,
            zoom=1.0,
        )

    source = dye_source[DYE_SOURCE_WELL]
    p300.pick_up_tip()

    # Wet the tip before recording evidence. This makes first droplet behavior
    # less misleading, but still keeps the test low-volume.
    p300.aspirate(PRE_WET_VOLUME_UL, source.bottom(z=2))
    p300.dispense(PRE_WET_VOLUME_UL, source.top(z=-2))

    for well_name in TARGET_WELLS:
        well = fixture[well_name]
        column = well_name[1:]
        high_target = _port_target(well, column, SAFE_CLEARANCE_ABOVE_MAT_MM)
        pre_entry_target = _port_target(well, column, PRE_ENTRY_ABOVE_PLATE_TOP_MM)
        dispense_target = _port_target(well, column, -DISPENSE_DEPTH_BELOW_PLATE_TOP_MM)

        p300.move_to(high_target)
        if CAPTURE_CAMERA_EVIDENCE:
            protocol.capture_image(
                filename=f"aevum_dye_{well_name}_pre_aspirate",
                resolution=CAMERA_RESOLUTION,
                zoom=1.0,
            )

        p300.aspirate(DYE_VOLUME_UL, source.bottom(z=2))
        p300.move_to(high_target)
        p300.move_to(pre_entry_target)
        p300.move_to(dispense_target)
        p300.dispense(DYE_VOLUME_UL, dispense_target)
        protocol.delay(seconds=POST_DISPENSE_DWELL_S)
        p300.move_to(pre_entry_target)
        p300.move_to(high_target)

        if CAPTURE_CAMERA_EVIDENCE:
            protocol.capture_image(
                filename=f"aevum_dye_{well_name}_post_dispense",
                resolution=CAMERA_RESOLUTION,
                zoom=1.0,
            )

    p300.drop_tip()
