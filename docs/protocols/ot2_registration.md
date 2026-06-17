# OT-2 Agent Registration Procedure

## Files

Generated labware definition:

```text
outputs/labware/aevum_p300_poc_fixture.json
```

Generated/handwritten test protocol:

```text
opentrons/test_p300_poc.py
```

Guarded dye-test protocol:

```text
opentrons/test_p300_poc_dye.py
```

## Control Assumption

Aevum does not rely on the Opentrons App as the primary control plane. Fixture
registration should be driven by the package-owned OT-2 bridge described in:

```text
docs/knowledge/agent_ot2_bridge.md
docs/knowledge/ot2_control_surfaces.md
```

The bridge should talk to the robot server HTTP API, serialize robot access,
validate every move against fixture geometry, and record offsets/evidence under
`data/measurements/`.

Direct execution of `opentrons/test_p300_poc.py` is a manual debug override, not
the normal registration path. If used before the bridge exists, record that
override explicitly in the measurement session and do not reuse any offset unless
the same robot, fixture definition, deck slot, and pipette setup are documented.
The protocol is guarded to fail closed unless the manual override flag and
registered fixture offset are set in the file.

## Procedure

1. Place the printed fixture in the selected deck slot.
2. Confirm the bridge can read robot health and attached pipettes.
3. Confirm the bridge can capture and retrieve OT-2 camera images.
4. Confirm robot serial, robot-server/API version, fixture slot, tiprack slot,
   pipette name, and pipette mount. Do not use protocol defaults for motion
   unless they match the live `GET /pipettes` result and the measurement record.
5. Capture a fixture-installed deck image and evaluate print/QC gates: flat
   base, open guide holes, no deformed mock wells, no support debris in access
   geometry.
6. Start a maintenance run through the bridge.
7. Home the robot.
8. Move to nominal A1 at conservative high Z.
9. Capture a high-Z A1 camera image and evaluate tip/target alignment.
10. Jog X/Y in small increments only when camera evidence or commissioning
   observation provides a correction direction.
11. Jog Z only after X/Y centering and clearance are confirmed by the active
   evidence mode.
12. Save the measured labware offset with robot serial, fixture definition,
   deck slot, pipette setup, run ID, timestamp, and notes.
13. Write or update the structured offset registry entry.
14. Run dry slow moves to center targets first.
15. Mark only the observed target class as verified after command history and
   camera or commissioning evidence agree. Use
   `docs/protocols/target_class_verification.md` for target names and
   promotion rules.
16. Run offset targets only after center targets pass.
17. Add dye/water only after dry positions and camera gates are verified.
18. Use `docs/protocols/p300_poc_dye_test.md` for the wet evidence run.

## Caution

The OT-2 does not sense contact with well bottoms. Keep first moves slow and
conservative, and never start by commanding a bottom-contact Z target.

Improper offset reuse can move the robot to unexpected positions. Reuse fixture
offsets only for the same robot, same generated labware definition, same deck
slot, and same pipette setup.

The target architecture is unattended autonomy. Human observations are temporary
commissioning evidence until camera gates are validated for the fixture and
target class.

## Current Protocol Assumptions

The first P300 registration workflow currently assumes:

```text
api level: 2.28
fixture slot: 1
tiprack slot: 2
pipette: p300_single_gen2
mount: left
```

This is the original compatibility/motion target, not proof of current hardware
state. Later no-motion bridge spikes observed a right-mount P20 Gen2, so the
bridge must verify the attached pipette name and mount before any registration
motion. Edit the constants at the top of `opentrons/test_p300_poc.py` only after
recording a hardware-state change that makes the P300 workflow valid for the
installed pipette and mount. If the installed robot software does not support
API `2.28`, complete the API spike before lowering the protocol version; camera
autonomy requires API `2.27` or newer.
