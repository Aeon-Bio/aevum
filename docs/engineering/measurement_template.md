# Measurement Session Template

Copy this into `data/measurements/YYYY-MM-DD_topic.md`.

````text
# Measurement Session

Date:
Operator:
Robot:
Robot server version:
Pipette:
Tip type:
Fixture version:
Params file:
Params SHA256:
Labware definition:
Labware definition SHA256:
Deck slot:
Run ID:
Camera available:
Camera API/path:
Target class:
Target-class result:

## Goal

## Setup

## Structured Offset Record

```json
{
  "schema_version": 1,
  "created_at": "",
  "robot_serial": "",
  "robot_server_version": "",
  "opentrons_api_version": "",
  "fixture_load_name": "aevum_p300_poc_fixture",
  "fixture_definition_uri": "",
  "fixture_params_sha256": "",
  "labware_definition_sha256": "",
  "slot": "1",
  "pipette_name": "p300_single_gen2",
  "pipette_mount": "left",
  "tiprack_load_name": "opentrons_96_tiprack_300ul",
  "offset_mm": {"x": null, "y": null, "z": null},
  "verification_targets": [],
  "camera_evidence": [],
  "evidence_file": "",
  "run_id": ""
}
```

## Target-Class Verification Record

```json
{
  "schema_version": 1,
  "target_class": "",
  "fixture_load_name": "aevum_p300_poc_fixture",
  "fixture_params_sha256": "",
  "labware_definition_sha256": "",
  "robot_serial": "",
  "robot_server_version": "",
  "slot": "1",
  "pipette_name": "",
  "pipette_mount": "",
  "tiprack_load_name": "opentrons_96_tiprack_300ul",
  "offset_registry_record": "",
  "run_id": "",
  "maintenance_run_id": "",
  "command_ids": [],
  "evidence": [
    {
      "schema_version": 1,
      "evidence_id": "",
      "source_kind": "vision_analysis",
      "path": "",
      "checksum_sha256": "",
      "session_id": "",
      "quality": "usable"
    }
  ],
  "claims": [
    {
      "schema_version": 1,
      "claim_id": "",
      "claim_type": "target_class_verified:<target_class>",
      "value": true,
      "session_id": "",
      "fixture_load_name": "aevum_p300_poc_fixture",
      "fixture_params_sha256": "",
      "labware_definition_sha256": "",
      "method": "",
      "quality": "usable",
      "evidence": []
    }
  ],
  "result": "blocked|passed|failed",
  "predecessor_records": []
}
```

## Measurements

| Item | Value | Tool | Notes |
|---|---:|---|---|
| Fixture X bound |  | calipers |  |
| Fixture Y bound |  | calipers |  |
| Fixture Z bound |  | calipers |  |
| QC gate result |  | bridge/manual |  |
| Camera capture path verified |  | bridge |  |
| Fixture deck image |  | camera | path/confidence |
| High-Z A1 image |  | camera | path/confidence |
| Base flat in deck slot |  | visual |  |
| Base flat on reference surface |  | visual/feeler gauge | reject if rocking or repeatable corner gap |
| Largest corner gap |  | paper/feeler gauge | after brim cleanup |
| Guide holes open |  | visual/probe |  |
| Mock wells clean/deformed |  | visual/probe |  |
| Real-plate support contact surface |  | visual/calipers | only if designing hard stops or datum pads |
| Real-plate underside glass/recess clearance |  | visual/calipers | avoid support contact with optical bottom |
| Real-plate top rim / gasket land |  | calipers | needed for chamber/lid, not published footprint |
| Gasket contact around plate perimeter |  | paper/feeler gauge | PoC seal check before dye/humidity |
| Plate shift after cassette puncture |  | calipers/camera | compare before/after P300 puncture |
| Compression bridge preload repeatability |  | visual/force proxy | confirm stack locks without bowing cassette |
| P300 tip length |  | calipers |  |
| Tip OD at nozzle |  | calipers |  |
| Tip OD 2 mm above nozzle |  | calipers/microscope | approximates well-rim contact for shallow dispense |
| Tip OD 10 mm above nozzle |  | calipers/microscope | approximates mat contact for 8 mm gap + shallow well entry |
| Tip OD at mat contact depth |  | calipers |  |
| Mat thickness |  | calipers |  |
| Mat plug protrusion below sheet |  | calipers | required to compute effective free gap |
| Mat plug diameter |  | calipers | verify against 6.80 mm CellVis opening / 6.21 mm lower well |
| Mat slit length |  | microscope/calipers |  |
| Effective free gap |  | calculation | 8.0 mm - plug protrusion below mat plane |
| Comfortable stack height |  | OT-2 run |  |

## Run Notes

## Failures / Collisions

## Changes For Next Print
````
