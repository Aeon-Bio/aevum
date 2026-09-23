# Observer Evidence Row Schema — Gate-6 Record Format

## Purpose

This protocol freezes the SHAPE of one observer evidence row inside the row-coupon
Gate-6 record. It is the imaging companion to the sensor/thermal rows owned by
`one_row_coupon_first_print_readiness.md` Gate 6 (gas-PCB, SHT41, IR-thermopile,
harness, thermal-proxy): the same physical-evidence gate, but for a measured observer
frame instead of a sensor/thermal reading. It answers exactly one question — *what
fields must a captured observer frame carry before it can occupy a Gate-6 row* — and
nothing more.

It proves nothing physical. A row written to this schema is a record, not a
measurement: it freezes the format a frame must take to be admissible, not whether the
frame shows anything. Imaging performance (focus through the wet stack, contrast,
field flatness, countable cells) is the Stage-0 optical bench's job
(`observer_optical_bench_stage0.md`); moving-system imaging is a Stage 1–4 motion
property; the leg-corridor/barrel fit is `observer_leg_corridor_objective_metrology.md`.
This schema sits downstream of all of them and decides only admissibility of shape.

CAD envelope geometry is NOT evidence and never fills a row. The CAD checks
`observer_front_end_swept_body_check` and `observer_carriage_envelope_check`
(`src/aevum_cad/row_coupon/`) are geometric scaffolding — reserved-air placeholders
that prove a head *could* fit a dry-bay budget, not that a frame *was* captured. They
do not satisfy any field below and may not be entered as an observer Gate-6 row. Only a
minted, persisted observer frame fills a row.

## Authority Boundary (load-bearing)

The schema is a record format, not a controller. It MUST NOT create motion authority.

An observer Gate-6 row is an indexed, checksummed *acquisition record* — an
`EvidencePacket` of `source_kind=OBSERVER_FRAME`, packets-only, carrying NO claims. A
filled row never authorizes the next motion: an acquisition record committed to the
durable store does not, by existing, advance any gate or grant any lease (the
`evidence_model.md` rule — `persist_observer_scan_evidence` commits `claims=[]`, so
`load_committed_evidence_claims` stays empty until a separate gate derives a claim from
these packets).

The four upstream authorities stay SEPARATE from this record format. Cite the
`src/aevum_ot2/core/observer.py` module docstring — the authority blocks are kept
deliberately apart and must not collapse into one success boolean:

- **Lease (software/motion) authority** — the `observer_scan` bridge lease
  (`acquire_observer_scan_lease` / `BridgeLeaseKind.OBSERVER_SCAN`). Mutually exclusive
  with the pipetting lease; whichever subsystem asks second is refused. The row binds to
  the lease that authorized the frame, but the row does not *re-grant* the lease.
- **Registration authority** — the fiducial transform (HX2 / IN-C5/C6). Carried in the
  row only as `pose_digest_sha256` PROVENANCE. A digest in a row is NOT a statement that
  registration passed; an empty digest is allowed at this layer (the registration gate,
  not this schema, decides whether a frame may be acquired without one).
- **Source-enable / condensation** — separate fail-closed gates upstream of acquisition
  (`aevum_smis.safety` / `aevum_smis.condensation`). The row does not assert them.
- **Hardware enable-line interlock** — the physical backstop layered on the lease
  (HX3 / IN-C7: lease released → enable drops). The record format does not assert it.

A frame that lacks lease binding, or carries a non-`observer_scan` lease kind, is
refused at mint (`ObserverLeaseError` in `mint_observer_scan_evidence`) and again at
persist (`persist_observer_scan_evidence`) — defense in depth — so a forged provenance
cannot reach the durable store and therefore cannot fill a Gate-6 row.

## Canonical Field List Of One Observer Gate-6 Row

A row is one persisted `EvidencePacket`. The frozen source models are
`ObserverScanEvidence` and `EvidencePacket` in `src/aevum_ot2/core/models.py`; the
mapping is `observer_scan_evidence_to_packet` in `src/aevum_ot2/core/observer.py`. This
table is single-sourced from that code — the doc never invents a field the models do
not carry.

| Row field | Source (frozen model / mapping) | Meaning in the row |
|---|---|---|
| `evidence_id` | `EvidencePacket.evidence_id` ← `ObserverScanEvidence.evidence_id` | Stable id of this one frame's record |
| `source_kind` | `EvidencePacket.source_kind` = `EvidenceSourceKind.OBSERVER_FRAME` | Fixed; identifies the row as an observer acquisition (not a pose source) |
| `created_at` | `EvidencePacket.created_at` ← `ObserverScanEvidence.captured_at` | When the frame was captured |
| `session_id` | `EvidencePacket.session_id` ← lease `session_id` | The acquisition session that owned the lease |
| `operation` | `EvidencePacket.operation` = `"observer_scan"` (`OBSERVER_SCAN_OPERATION`) | Names the acquisition operation; one query surfaces every observer frame |
| `command_id` | `EvidencePacket.command_id` ← `ObserverScanEvidence.run_id` | The scan run binding |
| `pose_digest_sha256` | `EvidencePacket.pose_digest_sha256` ← `ObserverScanEvidence.pose_digest_sha256` | Registration PROVENANCE only — 64-char sha256 when present (validated by `ObserverScanEvidence._validate_pose_digest`); empty allowed, NOT a pass |
| `artifact_path` | `EvidencePacket.artifact_path` ← `ObserverScanEvidence.artifact_path` | The captured frame's path/handle (`OBSERVER_FRAME` is not a pose kind, so no on-disk file is forced — a remote GigE capture handle persists honestly) |
| `checksum_sha256` | `EvidencePacket.checksum_sha256` ← `ObserverScanEvidence.checksum_sha256` | Integrity checksum of the frame artifact |
| `provenance.lease_owner` | `EvidencePacket.provenance["lease_owner"]` ← `ObserverScanEvidence.owner_id` | The lease owner that authorized the frame |
| `provenance.lease_kind` | `EvidencePacket.provenance["lease_kind"]` ← `ObserverScanEvidence.lease_kind` | Always `observer_scan`; the binding to software/motion authority |
| `provenance.illumination_mode` | `EvidencePacket.provenance["illumination_mode"]` ← `ObserverScanEvidence.illumination_mode` | Brightfield / oblique / darkfield mode of the capture |
| `payload.well_id` | `EvidencePacket.payload["well_id"]` ← `ObserverScanEvidence.well_id` | The imaged well |
| `payload.focus_z_mm` | `EvidencePacket.payload["focus_z_mm"]` ← `ObserverScanEvidence.focus_z_mm` | Focus Z at capture |
| `payload.focus_metric` | `EvidencePacket.payload["focus_metric"]` ← `ObserverScanEvidence.focus_metric` | The focus-quality scalar recorded for the frame |
| `payload.illumination_mode` | `EvidencePacket.payload["illumination_mode"]` ← `ObserverScanEvidence.illumination_mode` | Illumination mode (mirrored into payload for query) |
| `quality` | `EvidencePacket.quality` ← `ObserverScanEvidence.quality` | `EvidenceQuality` (`usable` / `ambiguous` / `failed` / `legacy`) — the row's self-assessed admissibility, NOT a gate verdict |

Fields not listed (`robot_serial`, `fixture_*`, `labware_definition_sha256`, `notes`)
default empty on the observer path and are not part of an observer Gate-6 row; do not
hand-populate them to imply provenance the frame did not carry.

A batch of rows is committed as one transaction (`persist_observer_scan_evidence`) and
must share one `session_id` — the transaction store rejects mixed sessions, so a batch
spanning two sessions fails closed rather than blurring authority.

## Outcomes

After mapping a captured frame to this schema:

```text
admissible:
  the frame minted against a valid observer_scan lease and maps to every required
  field above; it may occupy a Gate-6 observer row as an acquisition record

inadmissible (refused at mint/persist):
  no observer_scan lease, wrong lease_kind, or terminal/expired lease — ObserverLeaseError;
  the frame never reaches the store and cannot fill a row

not-a-row (CAD geometry):
  observer_front_end_swept_body_check / observer_carriage_envelope_check output; it is
  geometric scaffolding, not a captured frame — record it as CAD validation, never as a row

malformed:
  pose_digest_sha256 present but not 64 chars (rejected by the model validator), or a
  hand-built field the frozen models do not carry — fix the producer, do not relax the schema
```

An `admissible` row is still only a record. It does not, by itself, mark Gate 6 passed,
prove imaging, or authorize motion.

## What This Gates

Passing this schema check makes a captured observer frame *admissible* as a Gate-6
observer evidence row — it freezes the shape so the imaging companion rows are
single-sourced with the frozen `ObserverScanEvidence` / `EvidencePacket` models and
cannot drift from the code. It does not retire any optical, motion, or geometric
uncertainty: focus and contrast remain the Stage-0 bench's verdict
(`observer_optical_bench_stage0.md`), corridor/barrel fit remains
`observer_leg_corridor_objective_metrology.md`, and Gate 6 imaging performance stays
blocked until the physical gantry is built and measured. It grants no lease, asserts no
registration pass, and authorizes no motion; those four authorities remain separate
upstream gates per `src/aevum_ot2/core/observer.py`.
