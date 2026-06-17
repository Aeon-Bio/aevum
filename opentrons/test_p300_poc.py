"""Manual dry-motion scaffold for the Aevum P300 PoC fixture.

Normal Aevum operation should go through the agent OT-2 bridge. This file is a
manual debug override only because direct execution bypasses bridge locking,
structured offset checks, and evidence capture.
"""

from opentrons.types import Point

from opentrons import protocol_api

metadata = {
    "protocolName": "Aevum P300 PoC Fixture Dry Motion Test",
    "author": "Aevum",
    "description": "Slow P300 dry motion checks for the raised interaction mule.",
}

PROTOCOL_API_LEVEL = "2.28"

requirements = {"robotType": "OT-2", "apiLevel": PROTOCOL_API_LEVEL}

PIPETTE_NAME = "p300_single_gen2"
PIPETTE_MOUNT = "left"
TIPRACK_LOAD_NAME = "opentrons_96_tiprack_300ul"
TIPRACK_SLOT = "2"
FIXTURE_SLOT = "1"
PORT_OFFSET_BY_COLUMN_MM = {
    "1": 0.0,
    "2": 1.0,
    "3": 1.5,
    "4": 2.0,
}
TARGET_FINAL_PORT_OFFSET_MM = 1.5
ALLOW_MANUAL_DEBUG_RUN = False
REGISTERED_FIXTURE_OFFSET_MM = None
CAPTURE_CAMERA_EVIDENCE = True
CAMERA_RESOLUTION = (1920, 1080)


def run(protocol: protocol_api.ProtocolContext):
    if not ALLOW_MANUAL_DEBUG_RUN or REGISTERED_FIXTURE_OFFSET_MM is None:
        raise RuntimeError(
            "Do not run this protocol directly until fixture registration is "
            "recorded. Use the agent OT-2 bridge, or explicitly set "
            "ALLOW_MANUAL_DEBUG_RUN=True and REGISTERED_FIXTURE_OFFSET_MM."
        )

    fixture = protocol.load_labware("aevum_p300_poc_fixture", FIXTURE_SLOT)
    tiprack = protocol.load_labware(TIPRACK_LOAD_NAME, TIPRACK_SLOT)
    p300 = protocol.load_instrument(PIPETTE_NAME, PIPETTE_MOUNT, tip_racks=[tiprack])
    fixture.set_offset(
        x=REGISTERED_FIXTURE_OFFSET_MM[0],
        y=REGISTERED_FIXTURE_OFFSET_MM[1],
        z=REGISTERED_FIXTURE_OFFSET_MM[2],
    )

    if CAPTURE_CAMERA_EVIDENCE:
        protocol.capture_image(
            filename="aevum_fixture_loaded",
            resolution=CAMERA_RESOLUTION,
            zoom=1.0,
        )

    p300.pick_up_tip()

    # Each column has a different printed guide-hole offset:
    # column 1=center, column 2=+1.0 mm, column 3=+1.5 mm, column 4=+2.0 mm.
    # Each row has a different printed guide-hole diameter:
    # row A=3.0 mm, B=3.5 mm, C=4.0 mm, D=4.5 mm.
    # +1.5 mm X is the current candidate final global mat/lid offset.
    # Keep Z conservative; change only after camera/commissioning evidence.
    for well_name in [
        "A1",
        "A2",
        "A3",
        "A4",
        "B1",
        "B2",
        "B3",
        "B4",
        "C1",
        "C2",
        "C3",
        "C4",
        "D1",
        "D2",
        "D3",
        "D4",
    ]:
        well = fixture[well_name]
        column = well_name[1:]
        dx = PORT_OFFSET_BY_COLUMN_MM[column]
        high_target = well.top(z=15).move(Point(x=dx, y=0, z=0))
        low_target = well.top(z=5).move(Point(x=dx, y=0, z=0))

        p300.move_to(high_target)
        if CAPTURE_CAMERA_EVIDENCE:
            protocol.capture_image(
                filename=f"aevum_{well_name}_high_z",
                resolution=CAMERA_RESOLUTION,
                zoom=1.0,
            )
        protocol.delay(seconds=1)
        p300.move_to(low_target)
        protocol.delay(seconds=1)
        p300.move_to(high_target)
        protocol.delay(seconds=1)

    p300.drop_tip()
