# Sensor PCB

## Purpose

The sensor PCB is the custom-designed printed circuit board carrying the
row module's CO2 and humidity/temperature sensing elements. One design,
two populated boards: one in the supply path, one in the return path of
the row module's gas plumbing.

This page documents the PCB as a discrete production-prototype subsystem,
separate from the power section and from the print-native row coupon. It
is the second deliberate departure from the print-native discipline,
documented per the materials-strategy exception rule.

## Stance

The sensor PCB is a COTS-authority exception in the same family as the
power section. Where the power section converts AC mains to clean DC
rails, the sensor PCB converts the row module's gas atmosphere into
digital I2C measurements. Both bring commercial-authority precision into
the device at a defined boundary; neither violates the print-native
discipline of the mechanical row coupon itself.

The authority boundary for the sensor PCB is the **GX16-6 umbilical** on
one side (per `power_section.md`) and the **printed mount features in
the row coupon** on the other. The PCB itself is fabricated by an
external PCB house; its mechanical envelope and mounting interface are
designed jointly with the row coupon's gas plumbing geometry.

## Why A Custom PCB Instead Of A Dev-Module Breakout

The default hobby pattern is to buy a development module (sensor
pre-mounted on a generic breakout board with header pins), zip-tie it
inside the chamber, and connect via DuPont jumpers. This approach was
considered and rejected for the production prototype.

Reasons for custom PCB:

- **Sensor placement matters for measurement quality.** The STC31's gas
  aperture must register with the row module's gas channel, not face an
  arbitrary direction. The SHT41 must sit within 5 mm of the STC31 to
  give valid compensation data. Dev modules cannot guarantee either.
- **Mechanical integration with the row coupon.** The row coupon's CAD
  defines the gas plumbing geometry; the sensor PCB must mount in a way
  that locates the sensor in the gas flow, not in a stagnant pocket.
  Printed mount features in the row coupon position the PCB precisely;
  a generic dev module floating on jumper wires does not.
- **Wet biology cleanliness.** A loose dev module with exposed solder
  joints and header pins is a contamination harbor. A coated PCB with
  defined connector exits can be wiped between runs.
- **Production prototype discipline.** The project's documentation
  treats the row module as a production-prototype assemblage, not a
  bench breadboard. The sensors should match that discipline.

Reasons against (acknowledged tradeoffs):

- Custom PCB adds a 2–3 week design-and-fab cycle to the build schedule.
- Hand-assembled QFN12 (STC31) is borderline impractical; PCBA service
  required for first batch.
- Sensirion parts (STC31, SHT41) are not stocked by JLCPCB's in-house
  LCSC library and must be supplied as user-provided components,
  adding a $2 setup fee per part per board.

The fab cost premium (~3x the cost of two dev modules) is acceptable in
exchange for the integration quality. See decision log entry
2026-05-31: Sensor PCB Designed And Fabricated For Production Prototype.

## Components On Board

```text
top layer:
  STC31 (QFN12, 3.0 x 3.0 mm)        - CO2 measurement via thermal conductivity
  SHT41 (DFN-4, 1.5 x 1.5 mm)        - colocated RH/T for STC31 compensation
  decoupling cap C1 (100 nF, 0402)    - STC31 VDD bypass
  decoupling cap C2 (1 uF, 0603)      - STC31 VDD bulk
  decoupling cap C3 (100 nF, 0402)    - SHT41 VDD bypass
  4-pin output header J1              - SDA, SCL, VDD, GND
                                        (or solder pads for direct flying-lead wiring)

bottom layer:
  copper ground pour                  - thermal pad for STC31 heatsinking
                                        (STC31 is thermal-conductivity-based;
                                         consistent thermal coupling matters)
  printed-retention datum reliefs     - copper keepouts or annular clearance
                                        around holes/notches used by printed
                                        alignment and retention features

mechanical:
  gas aperture (2 mm through-hole)    - directly above STC31 measurement region,
                                        per Sensirion datasheet
  2x optional holes or edge notches   - position TBD by row coupon gas channel CAD;
                                        used by printed keepers/alignment posts,
                                        not by row-module metal screws
```

I2C pull-up resistors (typically 4.7 kohm on SDA and SCL) are **not** on
the sensor PCB. They live on the ESP32 host side, where the I2C bus
master is. Adding pull-ups on the sensor PCB would create double-loading
on the bus, which causes signal-integrity problems on the umbilical's
~1 m cable run.

## I2C Address Plan

The STC31's I2C address is `0x29` (fixed; no address pins).

The SHT41's I2C address is `0x44` (default; fixed without pin tying,
which the DFN-4 package does not support).

Two sensor PCBs on the same I2C bus would create address conflicts:
two STC31s at `0x29`, two SHT41s at `0x44`. Resolution:

- **TCA9548A I2C multiplexer on the ESP32 host side** routes traffic
  to one PCB at a time. Already in the power-section sensor cluster
  plan.
- Each sensor PCB connects to a dedicated TCA9548A channel, isolating
  its STC31 and SHT41 from the other PCB's pair.

The sensor PCB itself does not include the mux; the mux is one per
ESP32, hosting up to 8 channels (we use 2 for the sensor PCBs plus 4
for the standalone per-plate SHT41 sensors).

The four per-plate SHT41 sensors are a separate microcarrier role, not a
copy of this STC31 PCB. The row coupon reserves ~12 x 12 x 4 mm
screwless pockets for those carriers so each plate position has local
headspace RH/T evidence in addition to the supply/return gas-state
measurements documented here.

Those per-plate SHT41 readings are also the input to the observer condensation
gate in `src/aevum_smis/condensation.py`: the platform computes local dew point
from SHT41 RH/T and compares it to the MLX90614 underside temperature before
observer acquisition. This uses the existing sensor inventory; it does not add a
new PCB role or prove final purge/heater setpoints before Stage-0 warm-media
testing.

## Gas Aperture Spec

Per Sensirion STC31 application note:

- Gas access opening above the sensor: minimum 2 mm diameter, centered
  on the STC31 measurement region (offset from the chip center per
  datasheet)
- The aperture must allow gas exchange between the row module's gas
  channel and the STC31's measurement cell
- Aperture should be on the **top** side of the PCB (component side),
  facing the gas flow
- Distance from sensor surface to row-module gas channel boundary
  should be minimized; ideally the PCB sits flush against the channel
  opening with the aperture aligned to the channel cross-section

The row coupon's gas plumbing CAD must include matching aperture
geometry on the channel side. This is a row-coupon CAD revision item.

## Mechanical Envelope

```text
PCB outline: approximately 25 x 30 mm, 1.0 mm thick FR4
component height (top side): ~3 mm (tallest part is the SHT41
                                     or the through-hole header if used)
retention features: 2 x optional holes, edge notches, or tabs near the
                    short edges for printed clips/keepers
retention spacing: TBD; determined by row coupon CAD
connector exit: along one short edge, perpendicular to mounting axis
```

The exact outline is constrained by where the PCB physically sits in
the row module's gas plumbing. The current row-coupon CAD allocates a
vertical side-cartridge envelope for each supply/return PCB; the final
PCB outline freezes when the board edge notches/tabs and printed keeper
geometry are co-designed.

## Mounting Interface To Row Coupon

The row coupon CAD now provides, and `one_row_coupon.md` documents:

- **Supply-path sensor pocket** in the upstream mixing volume / plenum,
  with printed datum shelves, lateral/end stops, gas-aperture
  registration, and a screwless anti-lift clip, wedge, snap, or sliding
  keeper matched to the PCB's holes/notches/tabs
- **Return-path sensor pocket** in the downstream return path, with
  matching mount features
- **Gas channel aperture** on both pockets, aligned to the PCB's gas
  aperture when the PCB is seated against its mount
- **Covered lid-cover harness branch** routing the 4-wire I2C harness
  from each PCB into the removable lid's gas sensor bus with modeled
  strain relief and a JST GH 1.25 mm 4-circuit keyed service connector
  assembly. Exact crimp, pin assignment, cable assembly, and GX16-6
  handoff geometry remain power/service CAD details.

Both pockets should locate the PCB so the STC31 sees representative
gas, neither in a stagnant corner nor in a direct supply jet, per the
low-turbulence row headspace requirement from
[architecture](../knowledge/architecture.md).

Metal screws are not part of the row-module production intent. The PCB
may include holes or notches because they are useful for printed location,
bench fixtures, and fabrication handling, but the row coupon should retain
the board with printed mechanisms unless a separate materials-strategy
exception is explicitly logged.

## Fab And Assembly Workflow

### EDA tool

**LCEDA (立创EDA)**, JLCPCB's free cloud-based schematic + layout
tool. Direct submission to JLCPCB for fab + PCBA. Chinese-language
default, English UI available. Component library integrates with LCSC
inventory for in-house parts.

### Fab specifications

- 2-layer FR4
- 1.0 mm thick
- 1 oz copper both layers
- ENIG surface finish (gold over nickel; better solderability for
  QFN12 thermal pad than the cheaper HASL)
- Green soldermask, white silkscreen
- Minimum 0.15 mm trace/space (well within JLCPCB capabilities)

### Order quantity

- **5 boards** per fab order
  - 2 needed for the row module (supply + return)
  - 3 spares for assembly mishaps, bench testing, future iterations

### PCBA service (assembly)

- JLCPCB PCBA covers all standard components from LCSC: passives
  (caps, resistors), headers, mounting hardware
- **STC31 and SHT41 must be user-supplied** (not stocked in LCSC):
  ordered separately from Taobao (genuine Sensirion via 16-year-old
  store such as `瑞翔科技`), shipped to JLCPCB warehouse, placed during
  PCBA
- Per-board PCBA cost: ~$3–5
- Per-batch one-time setup: ~$8

### Component sourcing

| Part | Source | Quantity (5-board batch) | Estimated cost |
|---|---|---:|---:|
| STC31 (QFN12) | Taobao, 16-year-old genuine Sensirion seller | 5 | ~¥1,100 |
| SHT41 (DFN-4) | Taobao, similar | 5 | ~¥150 |
| Passives (0402/0603) | JLCPCB in-house | included in PCBA | ~¥10 |
| 4-pin headers | JLCPCB in-house | included in PCBA | ~¥5 |
| PCB fab | JLCPCB | 5 boards | ~¥50 |
| PCBA assembly | JLCPCB | 5 boards both sides | ~¥80 |
| Shipping | | | ~¥30 |
| **Total per 5-board batch** | | | **~¥1,425** |

### Round-trip timeline

- PCB design: 1–2 weeks (schematic + layout + 3D model export for row
  coupon CAD integration)
- PCB fab: 3–5 business days
- Component sourcing in parallel with fab
- PCBA: 5–7 business days after components arrive at JLCPCB warehouse
- Shipping: 3–7 business days
- **Realistic total**: 3–4 weeks from "design submitted" to "boards
  in hand"

## Counterfeit Authentication

Same Sensirion authentication discipline as documented in
`power_section.md`. STC31 verification on receipt:

1. **Visual check** of laser-etched part number on top of QFN12
2. **I2C address scan** with ESP32: STC31 must appear at `0x29`
3. **Functional check** via the baking-soda + vinegar bag test:
   place sensor + small dish in 1 L ziploc, add 10 g baking soda,
   pour 20 mL white vinegar onto the soda, seal immediately.
   Sensor should read climbing from 0% toward 2–5% CO2 within
   60 seconds. A constant or random reading indicates counterfeit.
4. **Long-soak test** after the bag: open and let read room air.
   Should return to near 0% within a minute. Hysteresis or stuck
   readings indicate fake or damaged unit.

SHT41 verification:

1. Visual check of laser-etched part number on top of DFN-4
2. I2C address scan: SHT41 must appear at `0x44`
3. **Breath-humidity test**: exhale ~5 cm from sensor for 2 seconds;
   reading should jump from ~50% to ~85–95% RH within 2 seconds and
   recover to room RH within 30 seconds. No response or sluggish
   response indicates counterfeit.
4. **Temperature check**: hold sensor between fingers for 60 seconds;
   reading should rise from room temperature toward ~30–34°C and
   recover to room temperature within ~60 seconds after release.

All five sensors of each batch (5 STC31, 5 SHT41) must pass these
checks before PCB assembly. Failures are returned to the Taobao seller
under the 7-day no-reason-required return policy.

## Validation Protocol

After PCBA and component installation, before integration into the row
module:

1. **Power-on test**: connect each PCB to ESP32 via DuPont jumpers
   on the 4-pin header. Apply 3.3 V via the ESP32's onboard LDO.
   Verify ~1 mA quiescent current draw per board (sub-mA when not
   actively measuring; ~6 mA STC31 + ~1 mA SHT41 during measurement
   cycles).
2. **I2C bus scan**: ESP32 scans the bus and finds devices at `0x29`
   (STC31) and `0x44` (SHT41). Both addresses must appear.
3. **Read test**: ESP32 firmware reads STC31 and SHT41 sequentially,
   logs values. Room air reading: STC31 ~0% CO2, SHT41 ~40-60% RH,
   ~20-25°C. Values should be stable within sensor noise floor.
4. **Compensation test**: STC31 reading with and without SHT41 RH/T
   data should differ by ~0.1-0.5% CO2 in ambient air. The compensated
   reading is the correct one.
5. **Gas response test**: introduce a CO2 transient (bag with baking-
   soda + vinegar, or controlled CO2 source if available). Reading
   should respond within 5 seconds and follow the actual concentration.
6. **Stability soak**: leave PCB in stable environment for 1 hour,
   record readings every 5 seconds. Standard deviation should be
   <0.05% CO2, <0.5% RH, <0.1°C.

Each of the 5 PCBs in the batch goes through this protocol before
the 2 best are selected for installation in the row module. Spare
PCBs are tagged and stored for later replacement.

## Service Operations

### Replacing a sensor PCB

1. Power off the row module (disconnect GX16 umbilicals at the power
   enclosure).
2. Open the row module to access the sensor pocket.
3. Disconnect the PCB's 4-wire harness from the internal terminal
   block (loosen 4 terminal screws).
4. Release the printed keeper, clip, wedge, or snap feature that retains
   the PCB.
5. Lift or slide the PCB out of the pocket along the modeled service path.
6. Install a fresh PCB from the spare stock; verify gas aperture
   alignment against the channel aperture.
7. Reconnect the 4-wire harness with attention to wire color (typically
   red=VDD, black=GND, blue=SDA, yellow=SCL — match the cable label).
8. Verify I2C bus scan and read test before closing the row module.

### Cleaning between wet biology runs

The sensor PCB cannot be submerged or wiped wet. Cleaning protocol:

1. Power down.
2. Remove PCB from pocket.
3. Visually inspect for spills or contamination on the STC31 gas
   aperture or SHT41 membrane.
4. If contaminated: replace with spare. Contaminated PCBs are not
   cleaned and reused; chemical residue affects sensor calibration
   irreversibly.
5. If clean: reinstall.

## Open Considerations

These are acknowledged gaps deferred until specific need arises:

- **Conformal coating** for warm-humid environment durability. Not
  applied to first batch; revisit after first wet biology cycles
  reveal whether moisture ingress is a real failure mode.
- **EMI shielding** (copper foil over PCB) for environments with high
  electromagnetic noise. Not needed for current architecture; revisit
  if observer carriage steppers introduce noise on the I2C bus.
- **Onboard pressure sensor** (BMP280 or equivalent) for chamber
  differential pressure. Useful for leak detection and pressure
  relief verification; not on first PCB to keep the design simple.
  Could be added in revision 2.
- **Onboard small-volume flow sensor** for in-channel gas flow rate.
  Useful for low-turbulence flow validation; defer to Coupon C
  passive flow stack.
- **Sample-plane (cell-contact) temperature** via MLX90614ESF-DCH IR
  thermopiles mounted in the row module's printed support frame.
  These are non-contact (the plate is a removable consumable; nothing
  may be adhered to it) and share the same I2C bus as the sensor PCBs
  via the TCA9548A multiplexer on the ESP32 carrier. Critically, the
  IR sensors must mount in **plate-margin pockets** (perimeter area of
  the plate underside, outside the well grid) so they do not occlude
  the observer's line of sight to the wells. Each sensor needs a
  dedicated small aperture in the support frame, distinct from the
  central observer aperture. Not on the sensor PCB; documented here as
  a related Phase-2 need. See decision log entry 2026-05-31
  (Sample-Plane Temperature Is A Distinct Measurement) for the
  placement constraint, edge-to-center thermal characterization
  requirement, and Phase 5 carriage-mounted upgrade path.

## Non-Goals

The sensor PCB explicitly does **not**:

- Measure heater surface temperature (PT1000 + MAX31865 handles that)
- Measure metal spreader / wall temperature (NTC thermistor or K-type
  thermocouple handles that)
- Measure sample-plane (cell-contact) temperature (separate row-module
  MLX90614 IR thermopiles handle that without touching the plate)
- Provide passive heater overtemperature safety (thermal fuse handles
  that)
- Drive any loads (no GPIO outputs, no SSR control; the PCB is
  measurement-only)
- Host the I2C multiplexer (TCA9548A lives on the ESP32 carrier)

## Cross-References

- Materials authority and exception framing:
  [materials strategy](../knowledge/materials_strategy.md)
- Power section and GX16-6 sensor umbilical pinout:
  [power section](power_section.md)
- Row coupon mounting interface and gas channel geometry:
  [one row coupon](one_row_coupon.md)
- System sensor architecture and per-plate sampling rationale:
  [architecture](../knowledge/architecture.md)
- Decision history:
  [decision log](decision_log.md) entries 2026-05-31 (sensor PCB
  design commitment and STC31 selection)
