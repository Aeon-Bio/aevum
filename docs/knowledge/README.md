# Knowledge Base

This directory records durable technical context for Aevum. It should explain
why the package is shaped the way it is, not just how to run the current files.

## Core Context

- [Architecture notes](architecture.md): platform scope, physical direction, and
  modalities to preserve.
- [CAD tooling](cad_tooling.md): why CadQuery is the mechanical source of truth.
- [OT-2 control surfaces](ot2_control_surfaces.md): official Opentrons APIs,
  calibration behavior, and what each control path is good for.
- [Agent OT-2 bridge](agent_ot2_bridge.md): target architecture for LLM-agent
  interaction with the robot.
- [Agent interface strategy](agent_interface_strategy.md): why MCP/CLI/HTTP are
  adapters over a stateful bridge core, not the architecture itself.
- [Evidence model](evidence_model.md): evidence packets, claims, gates, and why
  images are one source rather than the central abstraction.
- [OT-2 camera and autonomy](ot2_camera_autonomy.md): camera evidence strategy
  for moving from supervised commissioning to unattended operation.
- [Hardware systems lessons](hardware_systems_lessons.md): adjacent instrument
  families, common hardware failure modes, authority separation, and the next
  row-module coupon focus.
- [Byonoy plate readers](byonoy_plate_readers.md): adjacent prior art — the
  solid-state 96-channel on-deck reader, what it settles about parallel-vs-scanning
  architecture, the catalog gap it exposes, and the cost it adds to the C-OB2
  illumination fork.
- [Materials strategy](materials_strategy.md): material boundaries for a
  row-shared environmental module, including what can be printed and what needs
  inserts, glass, elastomers, metal, sensors, diffusers, or COTS parts, and the
  open water-immersion proposal against the plate-as-consumable per-well sensing
  clause (2026-09-23; a proposal, not an amendment).
- [Agent OT-2 bridge assessment](agent_ot2_bridge_assessment.md): validated
  risks and mitigations from adversarial architecture review.
- [First fixture QC acceptance](../engineering/fixture_qc_acceptance.md):
  provisional machine gates for the printed fixture.
- [Aevum OT-2 task graph](../engineering/task_graph.md): dependency graph and
  current no-motion print-to-evidence readiness path.
- [One-row coupon](../engineering/one_row_coupon.md): generated CadQuery row
  coupon, current artifact envelope, and hardware validation intent.
- [Row coupon revision hypergraph](../engineering/row_coupon_revision_hypergraph.md):
  do-review-context cycles tying CAD edits to generated artifacts, tests,
  viewer state, and durable hardware context.
- [Aevum realization hypergraph](../engineering/realization_hypergraph.md):
  seven-branch do-review structure tying physical measurements, row-coupon gates,
  observer CAD/protocols, SMIS, integration, and OT-2 control without duplicating
  the canonical backlog.
- [Row coupon cycle log](../engineering/row_coupon_cycle_log.md): current
  RH-cycle outcomes, engineering findings, and next print/review cycles.
- [Abstraction divergence task graph](../engineering/divergence_task_graph.md):
  engineering graph for evidence, gates, sessions, plans, targets, offsets, and
  adapter boundary cleanup.
- [Implementation trajectory](../engineering/implementation_trajectory.md):
  current code shape, next engineering phases, blockers, and stop conditions.
- [Readiness contract](../engineering/readiness_contract.md): boundary between
  no-motion sessions, commissioning records, and read-only readiness checks.
- [Schema inventory](../engineering/schema_inventory.md): persisted payload
  owners, migration policy, retention rules, and fail-closed gaps.
- [Power section](../engineering/power_section.md): production-prototype
  AC-mains-to-DC distribution stack, authority-bearing COTS exception, rail
  architecture, umbilical interface, layered failure response, and
  counterfeit-authentication protocol.
- [Sensor PCB](../engineering/sensor_pcb.md): custom-fabricated PCB carrying
  STC31 CO2 and SHT41 RH/T elements for the row module's gas-sampling
  positions, second authority-bearing COTS exception, JLCPCB fab + PCBA
  workflow, gas aperture and mounting interface to row coupon, validation
  and service protocols.
- [First fixture camera evidence](../protocols/first_fixture_camera_evidence.md):
  first installed-fixture camera capture and fixture-presence analysis runbook.
- [One-row coupon first-print readiness](../protocols/one_row_coupon_first_print_readiness.md):
  print/assembly/OT-2 placement/leak/sensor gates that prevent further CAD
  detail from outrunning physical evidence.
- [Row coupon passive leak and wet/dry validation](../protocols/row_coupon_passive_leak_wet_dry_validation.md):
  dye, condensate, witness-gutter, and dry-bay ingress evidence for Gate 4.
- [OT-2 target-class verification](../protocols/target_class_verification.md):
  scoped dry/wet target promotion rules for the first fixture.
- [OT-2 bridge recovery](../protocols/ot2_bridge_recovery.md): fail-closed
  recovery runbook after ambiguous robot state.
- [OT-2 bridge API spike](../protocols/ot2_bridge_api_spike.md): live robot
  checks required before implementing motion.

## Current Source Of Truth

Active row-coupon hardware workstream:

- Mechanical parameters: `cad/one_row_coupon.params.json`
- CAD generator: `src/aevum_cad/row_coupon/`
- CAD viewer: `cad/view_one_row_coupon.py`
- Generated artifacts: `outputs/cad/`
- Focused CAD tests: `tests/test_row_coupon_cad.py`

Earlier P300 fixture workstream:

- Mechanical parameters: `cad/p300_poc_fixture.params.json`
- CAD generator: `src/aevum_cad/fixture_model.py`
- Labware generator: `src/aevum_cad/labware.py`
- Generated labware JSON: `outputs/labware/aevum_p300_poc_fixture.json`
- Starter dry-motion protocol: `opentrons/test_p300_poc.py`
- Physical validation records: `data/measurements/`

## Documentation Rule

When a design decision depends on external robot behavior, cite the official
Opentrons documentation in the relevant knowledge page and record the package
decision in `docs/engineering/decision_log.md`.
