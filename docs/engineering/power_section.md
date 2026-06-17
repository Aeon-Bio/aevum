# Power Section

## Purpose

The power section is the AC-mains-to-DC distribution stack that supplies the
production prototype's environmental control, sensing, and motion subsystems.
It does not power the OT-2; the OT-2 retains its own AC cord and internal
supplies. The power section powers everything the row module's lid manifold,
service stack, and future observer hardware need to be active: heaters,
solenoid valves, fans, peristaltic pumps, environmental sensors, control
microcontrollers, and any later observer-side electronics that live outside
the OT-2's own power tree.

This page documents the production-prototype power section. It is intentionally
distinct from the print-native row coupon documentation; the row coupon is a
strict no-metal, no-glue mechanical proof, while the power section is the first
deliberate departure from that discipline into commercial authority.

## Stance

Per [materials strategy](../knowledge/materials_strategy.md), "any future
return to metal inserts, metal stops, commercial compression parts, or bonded
authority must be recorded as an explicit design exception with its own
evidence and service model." The power section is precisely such an exception.
It is composed entirely of commercial off-the-shelf authority-bearing parts
because no printed plastic can provide power conversion, regulation,
isolation, surge clamping, sensing accuracy, or sourced load current with the
precision biology and observation require.

The authority boundary is the **umbilical interface**: GX16 aviation connectors
between the power enclosure and the row module's lid manifold. On the
umbilical's row-module side, print-native discipline resumes. On the
umbilical's PSU side, commercial authority governs. This boundary keeps the
authority exception scoped to a discrete physical block of the prototype, not
allowed to creep into the print-native mechanical assembly.

## Hard Constraints

- AC input is **220 V / 50 Hz China mains via GB 1002 (国标三孔) plug**. Any
  cord with a US (NEMA), UK (BS 1363), or EU (CEE 7/7) plug end is wrong and
  must be re-sourced. This was an active sourcing mistake the first time; see
  cross-reference below.
- AC mains live is enclosed at all times during operation. No exposed L or N
  terminals. The enclosure must be closed before the IEC cord is connected to
  the wall.
- Authority parts must be **genuine**, with verifiable provenance, not
  knockoff clones. The unit-price savings of a counterfeit are dwarfed by the
  weeks of debugging "biology anomalies" that turn out to be unreliable
  readings from a fake Sensirion or a low-regulation fake PSU.
- All output rails (+24 V, +12 V, +5 V) are **galvanically isolated** from
  each other. This is the explicit function of the DDR-series DC-DC modules.
  Non-isolated buck converters (LM2596, MP1584) are forbidden on sensor or
  logic rails; they may be tolerated on a fan or pump where ground noise has
  no consequence, but never where ADC accuracy matters.
- The DC output ground (-V / 24 V GND) is **floating from earth at the PSU**
  and bonded once to earth at the sensor cluster ground star point. Multiple
  earth-to-DC-ground bonds are forbidden; they create ground loops that
  corrupt every analog measurement on the device.
- No safety device may be skipped or "added later." The AC fuse, MOV, DC fuse,
  TVS, thermal fuse, and earth bond are not optional features; they are the
  layered failure response the build relies on, and each layer covers a
  specific failure mode the others cannot.

## Rail Architecture

```text
220 V AC mains (国标 wall outlet)
        |
        v
IEC C13/C14 power cord (国标三孔 to C13, 18 AWG, UL or ETL certified)
        |
        v
IEC C14 panel inlet, switched, fused (T2.5 A ceramic 5x20 in drawer)
        |
        +- E (PE earth) -> enclosure chassis bond
        |                -> HRP-150 FG terminal
        |                -> USLKG-2.5 PE terminal on DIN rail (star)
        |
        +- L -> 10D471K MOV across L-N -> HRP-150 AC/L input
        |
        v
        N -> HRP-150 AC/N input
        |
        v
MeanWell HRP-150-24 (genuine, Class I, 150 W, fanless to ~80 W)
        | +V_out / -V_out (with +S/-S remote-sense pins jumpered locally)
        v
5x20 ceramic slow-blow fuse, T6.3 A 250 V, panel-mount holder
        |
        v
+24 V / 24 V GND distribution (UK2.5B terminals on 35 mm DIN rail,
                               jumpered via FBI-10-5 Phillips bridges)
        |
        +- Heater SSR -> polyimide heater -> 24 V GND
        |       (snubber: 100 nF ceramic + 100 uF electrolytic across heater)
        |       (P6KE24A TVS across local +24 V / GND entry)
        |
        +- Solenoid driver MOSFET -> solenoid coil -> 24 V GND
        |       (flyback: 1N4007 across coil, cathode to +24 V)
        |       (P6KE24A TVS across local +24 V / GND entry)
        |
        +- DDR-30G-12 (24 V -> 12 V isolated, 30 W)
        |       |
        |       v +12 V (galvanically isolated from 24 V GND)
        |       +- quiet 12 V mixing fan
        |       +- mini 12 V peristaltic pump
        |
        +- DDR-15G-5 (24 V -> 5 V isolated, 15 W)
                |
                v +5 V (galvanically isolated from 24 V GND;
                        this becomes the logic ground reference)
                +- ESP32-S3 #1 (primary sensor host)
                |       +- on-board 3.3 V LDO -> I2C bus -> TCA9548A mux
                |       +- channels 0-1: sensor PCBs (each STC31 + SHT41)
                |       +- channels 2-5: per-plate SHT41 (headspace RH/T)
                |       +- channel 6: 4x MLX90614 IR thermopiles (sample-plane T,
                |              addresses reprogrammed to 0x5A..0x5D so all four
                |              share one mux channel)
                |       +- SPI: MAX31865 + PT1000 (heater control sensor)
                +- ESP32-S3 #2 (independent safety MCU)
                        +- SPI: independent MAX31865 + PT1000 (safety read)
                        +- SSR enable line (ANDed with primary command)
                        +- watchdog timer
```

The DC-DC stage placement is deliberate: 24 V is the trunk because the heaters
and steppers (future) want it natively; 12 V and 5 V are local conversions
near the loads. This avoids running a noisy 12 V or 5 V rail across the long
umbilical run, where it would pick up interference from the heater PWM
returning on the 24 V GND.

## Load Budget

| Rail | Steady-state | Worst transient | Source module | Headroom |
|---|---:|---:|---|---:|
| +24 V | 30 W | 110 W | HRP-150-24 (150 W) | 36% over transient |
| +12 V | 5 W | 12 W | DDR-30G-12 (30 W) | 150% over transient |
| +5 V | 3 W | 8 W | DDR-15G-5 (15 W) | 88% over transient |

Worst-case +24 V loads (cumulative): two polyimide heaters at 30 W each at
full duty (60 W); solenoid valve at 10 W energized; future observer carriage
with two NEMA17 steppers at 12 W each (24 W). Combined transient ~110 W.
Steady-state with one heater duty-cycled at 30% and no observer motion
~25 W.

The HRP-150 stays fanless up to ~80 W. Steady-state operation should remain
below that threshold without forced cooling. If a future expansion pushes
steady-state above 80 W, either size up to HRP-300-24 or add a quiet
enclosure fan blowing across the PSU heatsink. Do not mount the HRP-150 in a
sealed box.

## Authority Boundary - The Umbilical

The umbilical is the line where commercial authority hands off to the
print-native row module. The recommended physical realization is two GX16
aviation connectors per row module:

```text
GX16-4 (power umbilical):
  pin 1 = +24 V
  pin 2 = 24 V GND
  pin 3 = +5 V
  pin 4 = 5 V GND (isolated from 24 V GND through DDR-15G-5)

GX16-6 (sensor/control umbilical):
  pin 1 = I2C SDA (3.3 V logic level)
  pin 2 = I2C SCL (3.3 V logic level)
  pin 3 = +3.3 V (sensor power, from primary ESP32 LDO, max 150 mA)
  pin 4 = 3.3 V GND (common with 5 V GND)
  pin 5 = ALARM (open-drain, active low; asserted on safety-MCU thermal trip)
  pin 6 = SPARE (reserved; leave floating in current build)
```

Each connector has a panel-mount socket on the power enclosure side and a
cable-mount plug on the row module side. The physical disconnect supports the
row module's service order: unplug both umbilicals before lifting the lid,
plug back in after the wedge locks are re-engaged.

The +12 V rail does not currently cross the umbilical because its loads (fan,
pump) live with the PSU or in a separate fluidics module. If a future row
module needs 12 V locally (e.g., a lid-mounted backup fan), add a second
GX16-4 carrying +12 V / 12 V GND rather than mixing onto the existing power
umbilical.

This pinout is frozen as a contract. Any future row module designs against
this pinout, not against a one-off wiring decision.

The GX16-6 I2C bus carries traffic for the two custom sensor PCBs
(each with STC31 + SHT41) documented in `sensor_pcb.md`, plus the four
per-plate standalone SHT41 sensors that share the bus via a TCA9548A
multiplexer on the ESP32 carrier. The sensor PCB itself does not host
the multiplexer; it is one per ESP32, hosting up to 8 channels.

The four standalone per-plate SHT41 sensors are real first-build
headspace RH/T measurements, not logical placeholders. The row-coupon CAD
now provides screwless pockets for ~12 x 12 x 4 mm SHT41 microcarriers
that expose the sensor membrane/opening to plate-local headspace and an
inline covered lid-shell sensor bus routed to a removable-lid service
connector represented as JST GH 1.25 mm 4-circuit geometry. The current CAD
also keeps that route outside pipette, deck-contact, and observer apertures.
Exact crimp, pin assignment, cable assembly, and GX16-6 handoff remain
power/service CAD details.

## Host Interface Isolation

The ESP32-S3 control microcontrollers connect to a host PC for programming,
debugging, and (later) bridge-daemon telemetry. Without isolation, the host
PC's switching power supply ground and the prototype's lab-floor earth can
sit at meaningfully different potentials. The resulting ground loop appears
as 50/60 Hz hum and broadband noise on every analog measurement the device
makes, corrupting ADC readings on the PT1000 RTD, masking real biology
signals, and making bring-up debugging much harder than it needs to be.

The host interface is therefore galvanically isolated via a USB isolator
inserted between the PC's USB port and the ESP32-S3.

### Specification

- **Reference part**: 正点原子 USB 隔离器 HUB23 (ALIENTEK HUB23) or
  equivalent.
- **Speed**: USB 2.0 full-speed (12 Mbps). Sufficient for ESP32-S3 CDC, UART,
  and USB JTAG/debug traffic. Cheap "480 Mbps" claims at the same price
  point are almost always ADuM3160-based units with marketing fiction; the
  actual speed is 12 Mbps, which does not matter for this application.
- **Isolation**: at least 1500 V (2000 V on the HUB23). Adequate for
  ground-loop elimination; medical-grade isolation (4 kV+) is not required.
- **Device-side power**: at least 100 mA isolated. The ESP32-S3 itself runs
  off the +5 V rail (DDR-15G-5), not from USB bus power; the isolator only
  needs to provide enough current for the isolator chip and the ESP32's VBUS
  detection circuit.
- **Host-side connector**: USB-C, so the isolator plugs directly into the
  PC's USB-C port without a Type-A adapter dongle. If the chosen unit has
  only USB-A male input, use a USB-C-to-USB-A cable to the PC.

### Connection chain

```text
PC USB-C
  |
  v
(USB-C cable, or direct plug if isolator has USB-C input)
  |
  v
USB isolator host-side input
  |          (galvanic isolation barrier here)
  v
USB isolator device-side output (USB-A female)
  |
  v
(USB-A to USB-C cable)
  |
  v
ESP32-S3 dev board USB-C port
```

### Interaction with the +5 V rail

The ESP32-S3 dev board draws operating power from the production +5 V rail
through its VIN/5V pin and simultaneously sees VBUS from the isolator's
device-side output. The onboard Schottky diode on the ESP32-S3 dev board
handles the OR-ing safely: VIN supplies the actual current, VBUS supplies
the detection signal that wakes USB-CDC enumeration. This is the standard
configuration and does not require cutting the VBUS line or modifying the
dev board.

The isolator's device-side power output (~50..100 mA from a typical
ADuM3160-based unit, up to 2.5 W on the HUB23) is more than enough for the
ESP32's USB peripheral but not enough to power the ESP32 by itself. This
is intentional: it means the ESP32 only operates when the production +5 V
rail is up, and a USB cable disconnect does not power-cycle the ESP32.

### What this isolator does and does not protect

Does:

- Eliminates ground-loop hum from the PC chassis ground onto the analog
  sensor lines.
- Permits the PC's switching PSU to sit at any potential relative to the
  prototype's earth without affecting measurements.
- Prevents a PC USB fault from sourcing or sinking destructive current
  through the ESP32 into the prototype's other electronics.

Does not:

- Provide protection against the PC if the prototype's PSU faults; that is
  the umbilical disconnect's job.
- Substitute for ESD protection on exposed sensor harnesses; use TVS
  devices on any wire that leaves the enclosure.
- Replace the discipline of single-point ground bonding at the sensor
  cluster; isolation reduces the consequences of ground-loop mistakes, but
  the star-point bond is still the right physical topology.

### Excluded alternatives

- Audio-grade isolators (e.g., TOPPING HS02 at ¥500+) are latency-optimized
  for DAC use and overpriced for ESP32 CDC.
- Premium chip-based isolators (TI ISOUSB211 at ¥170+) are higher quality
  than ADuM3160 but offer no functional benefit for this application.
- "USB 3.0" or "480 Mbps" branded units at the ¥30..¥90 price point are
  almost always full-speed (12 Mbps) units with misleading marketing; the
  actual function is identical to a properly-labeled ADuM3160 unit at the
  same price.

## Enclosure

The power section lives in a wall-mountable ABS plastic enclosure with a
removable transparent cover and an internal mounting backplane. The
enclosure provides finger protection from AC live conductors, dust
containment, panel-mount surfaces for the IEC inlet and umbilical
connectors, and a defined physical boundary the umbilical hands off from.

### Reference part

**带圆孔 400 x 300 x 200 mm 透明盖 + 底板** (round-hole pattern, transparent
cover, with mounting backplane). ABS plastic, wall-mountable, typically sold
on Taobao as a "配电箱" (distribution box) or "电气盒" (electrical box).

### Why this size

The dimensional bottleneck is the DIN rail occupancy, not the PSU
footprint. A first-pass estimate that assumed a shorter rail was undersized
by ~30%; doing the math properly shows ~280 mm of rail is needed in a
realistic layout.

DIN rail occupancy:

| Group | Items | Width (mm) |
|---|---|---:|
| PE star | 1 x USLKG-2.5 | 8.2 |
| +24 V rail | 6 x UK2.5B (PSU+, fuse out, heater feed, solenoid feed, DDR-30G in, DDR-15G in) | 31.2 |
| 24 V GND rail | 6 x UK2.5B | 31.2 |
| DDR-30G-12 module | DIN-rail housing | ~25 |
| DDR-15G-5 module | DIN-rail housing | ~17 |
| +12 V rail | 4 x UK2.5B (DDR out, fan, pump, spare) | 20.8 |
| 12 V GND rail | 4 x UK2.5B | 20.8 |
| +5 V rail | 4 x UK2.5B (DDR out, ESP32 #1, ESP32 #2, to umbilical) | 20.8 |
| 5 V GND rail | 4 x UK2.5B | 20.8 |
| End plates (D-UK) | 6 x 1.5 mm | 9.0 |
| End clamps (E-UK) | 6 x ~8 mm | 48.0 |
| Spare margin | | 30.0 |
| Total rail length | | ~282 mm |

The HRP-150-24 is 199 x 98 x 38 mm. The DIN rail and PSU must coexist on
the backplane with wire-routing channels around both.

Why 400 x 300 (footprint):

- **400 mm length** gives ~380 mm interior, fits the 282 mm DIN rail with
  ~95 mm spare for end clearance and a future module or two.
- **300 mm depth** gives ~280 mm interior, fits the PSU (98 mm wide) +
  ~40 mm rail strip + ~60 mm wire channels + ~80 mm spare for a future
  stepper-driver row or a breadboarded MOSFET driver card.

Why 200 mm height (not 170 mm):

- DDR modules mounted on DIN rail sit ~115 mm above the backplane (25 mm
  bracket + 90 mm module body).
- 170 mm enclosure gives ~155 mm interior height, leaving only ~40 mm
  clearance under the cover - cramped for wire bends and rules out a
  side-mounted fan port without crowding.
- 200 mm enclosure gives ~185 mm interior, leaving ~70 mm clearance for
  wire bends, a future 60 mm fan port, and an INA219 telemetry board on
  a second tier above the rail.

### Backplane layout

```text
   <----------- 400 mm (long axis) ----------->
  ^  +-----------------------------------------+
  |  | DIN rail (~282 mm of components)        |   ~40 mm
  |  | wire channel above rail                 |   ~30 mm
  3  +-----------------------------------------+
  0  | wire channel between PSU and rail       |   ~30 mm
  0  +-----------------------------------------+
  m  | HRP-150-24 (199 x 98)        | spare   |   PSU 98 mm
  m  |                              | for fan |
  |  +-----------------------------------------+
  v  | wire channel below PSU                  |   ~30 mm
     +-----------------------------------------+
```

PSU on the long side of the backplane; DIN rail parallel above it; wire
channels above, below, and between. Panel-mount items (IEC inlet, DC fuse,
GX16 connectors) on the enclosure walls, with internal wires routed through
the channels to their destinations.

### Hole pattern

**带圆孔** (round-hole) pattern is correct because the round pre-cut holes
fit GX16 panel-mount sockets (16..22 mm) cleanly. Unused round holes plug
with rubber grommets or cable glands.

- **带U型孔** (U-shaped) holes are cut for Chinese GB power-strip sockets;
  wrong shape for both the rectangular IEC C14 inlet and the round GX16
  connectors. Skip.
- **不带孔** (no holes) is a blank canvas but the listings only offer it in
  small sizes (210 x 130 x 110 mm and smaller); for 400 x 300 x 200 you
  would need to contact the seller for a custom no-hole order, adding lead
  time.

### Cover choice

**透明盖** (transparent cover) for the prototype phase. Lets you verify
status LEDs, see whether a fuse has blown, confirm ferrule color discipline,
and observe wire dressing without opening the enclosure. Once bring-up is
complete, swap to **灰盖** (opaque gray cover) if the cleaner appearance is
preferred for installed use.

### Cuts and modifications

Even with round holes pre-cut, the enclosure needs:

- **Rectangular cutout for the IEC C14 inlet** on the rear panel,
  ~47 x 27 mm. Step drill plus small files, or a Dremel cutting wheel.
- **Round cutout for the panel-mount DC fuse holder** on the front, ~16 mm.
  Step drill bit.
- **Ventilation slots** on side panels for convection, ~3 x 50 mm slots near
  the PSU heatsink. Drill a row of 3 mm holes and join with a small file.
  Keep openings small enough that a finger cannot enter (finger-probe IPXXB
  if compliance ever matters).
- **Optional 60 mm fan port** on a side panel opposite the ventilation
  slots, if steady-state load rises above ~50 W and the PSU heatsink runs
  hot to the touch. Powered from the +12 V rail. Do not pre-cut; add when
  measurements show it is needed.

### Material

ABS plastic is correct for indoor benchtop lab use. Aluminum enclosures
offer better EMI shielding and structural mounting, but the prototype's
signal levels do not need shielding and the plastic enclosure is much
easier to drill and modify during bring-up.

### Color

Default 灰色 (gray) shell. Decorative colors (粉红, 玫红, 蓝色, etc.) shown
at the bottom of the listing are not appropriate for a production prototype
that will be photographed for documentation; they look unprofessional once
cutouts and labels are added.

### Alternative paths if 400 x 300 x 200 is too large

These are documented for the future, not recommended for the first build.

1. **Two-enclosure split**: small enclosure (300 x 200 x 170) for AC +
   PSU + +24 V trunk; second small enclosure (210 x 130 x 110) for DC-DC
   rails and umbilical patch panel. Adds an inter-enclosure cable. Saves
   bench area at the cost of one more wire run.
2. **Remote DC-DC modules**: PSU + AC + +24 V distribution in a small box;
   +24 V umbilical to the row module side; DDR modules located there. Trades
   a smaller power enclosure for more heat and switching noise near the
   biology and a more complex umbilical carrying 24 V at amps.

Neither is as clean as one 400 x 300 x 200 enclosure for the first build.

## Component Selection Criteria

The power section's component choices follow invariants that should survive
maintenance and team turnover.

### Mains-side authority

- **PSU**: MeanWell HRP-150-24, genuine. The HRP series gives tighter
  regulation under load steps than the cheaper LRS series and includes remote
  sense pins (+S, -S) to compensate for cable IR drop. For a heater-PWM and
  solenoid-kick load profile, the regulation matters.
- **AC fuse**: 5x20 mm **ceramic** slow-blow (T-rated), 2.0..2.5 A. Glass
  fuses are inadequate at 220 V mains because their fault-current breaking
  capacity (~35 A) cannot interrupt a real short-circuit arc; ceramic fuses
  (~1500 A) can. This is a fire-safety constraint, not a preference.
- **MOV**: 10D471K (10 mm disc, 470 V clamp). Across L-N only, on the load
  side of the AC fuse, with leads kept under 25 mm to maintain low inductance.
  Higher clamp voltages (10D561K, 560 V) let larger surges through; lower
  clamp voltages (10D391K, 390 V) conduct on normal AC peak transients and
  wear out fast.
- **IEC inlet**: C14 panel-mount, switched, with built-in fuse drawer. This
  consolidates AC switch, fuse holder, and inlet into one panel cut-out and
  removes the failure mode of unrelated AC-switch wiring.
- **Power cord**: 18 AWG (3 x 0.824 mm²) UL- or ETL-certified, **国标
  (GB 1002)** plug at wall end, IEC C13 socket at inlet end. Length 1.5 m.

### DC-side authority

- **DC trunk fuse**: 5x20 mm ceramic slow-blow, T6.3 A 250 V, panel-mount
  holder on the +24 V rail between PSU output and distribution terminals.
- **DC-DC step-down**: MeanWell DDR-series, **G suffix** (9..36 V input range,
  with 24 V sitting comfortably mid-range). The L suffix is 18..75 V input
  for 48 V systems; using L on 24 V puts the input at the bottom edge, hurting
  regulation. Output voltage is the last number (`-5`, `-12`).
  - 24 V -> 12 V: DDR-30G-12
  - 24 V -> 5 V: DDR-15G-5
- **TVS**: P6KE24A (through-hole DO-15, uni-directional 单向, 600 W,
  Vishay-branded). One per subsystem entry point, cathode to +24 V, anode to
  GND. Place at the load end of each branch, not back at the PSU; local
  clamping intercepts the transient at the source.
- **Flyback diode**: 1N4007 across every solenoid coil, cathode toward
  +24 V. Without this, coil de-energization back-EMF destroys the driver
  MOSFET and injects spikes into the rail.
- **Snubber**: 100 nF ceramic in parallel with 100 uF electrolytic across each
  heater's SSR-side terminals. Suppresses switching transients into the rail.

### Distribution and wiring

- **DIN rail**: 35 mm wide, ≥0.8 mm thick, 国标 spec. International 1.0 mm
  spec is preferable if available but 0.8 mm is acceptable for low-current
  lab use; the difference is slight rail flex under tight clamping.
- **Terminal blocks**: Phoenix-compatible UK2.5B with **copper fittings** and
  **V0** insulation. Reject "Grey Alloy" and "Economy" variants: alloy
  contacts corrode under humidity (a hostile environment for a humidified-CO2
  prototype), and non-V0 insulation supports flame propagation.
- **PE grounding terminal**: USLKG-2.5 (yellow-green) which auto-bonds to the
  DIN rail metal. One per group, placed at the chassis-earth star point.
  Generic green-colored UK2.5B is not a PE block; it does not bond to the
  rail.
- **End plates (挡板)**: D-UK2.5B at the end of each terminal group. Covers
  the exposed contact slot on the last terminal; prevents
  screwdriver-slip shorts.
- **End clamps (端子固定件)**: E-UK rail clamps at both ends of each terminal
  group. Prevents terminal strips from sliding axially on the rail.
- **Jumper bridges**: FBI-10-5 (10-position, 5.2 mm pitch, Phillips head).
  Trim to length with side cutters. The visually-similar FBI-10-6 is 6.2 mm
  pitch for UK5N and **will not seat** on UK2.5B; verify pitch with the
  seller before purchase, because Phoenix's `FBI-X-Y` naming convention is
  not always honored by Chinese knockoffs. UK2.5B and UK3N share the 5.2 mm
  pitch; listings labeled only for UK3N are also correct for UK2.5B.
- **Hookup wire**: silicone-jacket, tinned copper. 18 AWG for AC and DC
  trunk; 24 AWG for sensor harness and control lines.
- **Ferrules**: bootlace crimps sized to wire (VE0508 for 22..24 AWG, VE1008
  for 18 AWG, VE1508 for 16 AWG). Required on all terminal-screw
  connections; bare strands at AC terminals are a fire hazard.
- **Ferrule crimper**: SN-06WF or equivalent ratcheting four-sided square-die
  tool, 0.25..6 mm² range. Self-adjusting hex/square ratchet crimpers give
  gas-tight connections; plain pliers do not.
- **Wire stripper**: separate self-adjusting tool. The crimper does not
  strip; using diagonal cutters nicks conductors and seeds future failures.

### Wire color discipline

The Chinese convention is brown (L), blue (N), green-yellow striped (E). If
only a five-color set (red/yellow/blue/black/green) is available, the
workaround is:

```text
L = RED conductor + brown heat-shrink wrap at both terminal ends
N = BLUE conductor (matches convention, no wrap needed)
E = GREEN conductor + yellow heat-shrink wrap at both terminal ends
```

This is acceptable but creates a hazard if undocumented: the next person to
open the enclosure must immediately tell which wire is live. Always apply the
heat-shrink wraps and post a color-code legend label inside the enclosure.

### Connectors

- **GX16 aviation connectors**: 4-pin for the power umbilical, 6-pin for the
  sensor/control umbilical. Panel-mount socket on enclosure, cable-mount plug
  on row module. Both halves of each connector should be ordered together
  (匹配 male/female pair).
- **Internal DuPont headers**: acceptable for ESP32-to-sensor breakouts
  inside the enclosure, but never for inter-enclosure runs. DuPont is for
  bench prototyping, not for a mounted production prototype.

## Wiring Procedure

### Pre-assembly

1. Mount the HRP-150-24 to the enclosure backplane via its M4 mounting holes,
   or to a DIN rail using a PSU bracket. Leave clearance around the heatsink
   fins for convection.
2. Mount the IEC C14 inlet to a cut-out on the enclosure's rear panel.
3. Mount the 35 mm DIN rail inside the enclosure with sufficient length for:
   PE terminal, AC L/N/E terminals, +24 V / 24 V GND distribution with FBI
   bridges, two DDR modules, and end stops at both ends of each group.
4. Mount the panel-mount fuse holder near the DIN rail entry for the +24 V
   trunk.

### AC side (PSU UNPLUGGED, IEC switch OFF)

1. Cut three 15 cm lengths of 18 AWG silicone wire per color discipline.
2. Strip 6 mm of insulation off each end, crimp ferrules.
3. Wire IEC inlet L -> HRP-150 AC/L; N -> AC/N; E -> FG.
4. Across L-N at the HRP input terminals, install the 10D471K MOV with
   leads ≤25 mm.
5. Run the PE wire from the IEC inlet's E terminal to the USLKG-2.5
   grounding terminal block on the DIN rail.

### DC side

1. HRP +V -> red 18 AWG -> fuse holder -> +24 V rail (first UK2.5B terminal).
2. HRP -V -> black 18 AWG -> 24 V GND rail.
3. Jumper +24 V and 24 V GND rails with FBI-10-5 bridges, trimmed to the
   active position count.
4. Each DDR module: +Vin from +24 V rail, -Vin from 24 V GND. +Vout to its
   respective new rail (+12 V or +5 V). -Vout starts a new isolated ground
   rail.
5. **Remote sense (HRP-150 +S and -S terminals)**: jumper +S to +V and -S to
   -V directly at the PSU output if the cable run to load is under 30 cm.
   For longer runs, route +S and -S as a separate twisted pair to the load
   end so the PSU regulates against actual load-end voltage.

### Earthing - single bond rule

The HRP-150 FG terminal bonds to enclosure earth and to the USLKG-2.5 PE
terminal at a single star point. The DC output ground (-V / 24 V GND) is
**not** bonded to earth at the PSU. It finds its earth reference exactly
once, at the sensor cluster ground bond on the row module side.

### TVS and snubber install

- P6KE24A on each subsystem's +24 V entry point, **at the load**, not at the
  PSU. Cathode (banded end) to +24 V, anode to GND. Short leads.
- 1N4007 across every solenoid coil. Cathode to the +24 V side of the coil.
  Either soldered with strain relief or installed at the terminal block
  adjacent to the coil leads.
- 100 nF ceramic + 100 uF electrolytic in parallel across each SSR's load-side
  terminals where the heater connects. Reduces switching ripple injected into
  the rail.

### Subsystem connection order

The first power-on is a **no-load test**. Build out subsystems incrementally
and verify each rail after every addition.

1. AC wired, PSU unloaded.
2. First power-on: verify 24.0 ± 0.3 V at HRP output. Use the VR1 trim
   potentiometer to set exactly 24.0 V.
3. Power off. Connect DDR-30G-12. Power on. Verify 12.0 V at its output.
4. Power off. Connect DDR-15G-5. Power on. Verify 5.0 V at its output.
5. Power off. Connect ESP32-S3s, sensors, SSRs in turn, verifying each rail
   after each addition.
6. Power off. Connect heater (no power command yet). Power on, command 5%
   duty cycle, observe rail stays stable.
7. Repeat for solenoid valve (command short pulse, observe flyback works, no
   MOSFET damage, rail stays stable).
8. Full-stack burn-in: 24 hour idle test, log all rail voltages and
   temperatures.

## Verification Procedure

### Pre-power-on continuity check (PSU UNPLUGGED, multimeter in continuity mode)

```text
[ ] IEC inlet L  <-> HRP AC/L: beeps
[ ] IEC inlet N  <-> HRP AC/N: beeps
[ ] IEC inlet E  <-> HRP FG: beeps
[ ] IEC inlet E  <-> exposed metal on enclosure: beeps
[ ] IEC inlet L  <-> IEC inlet N: NO beep
[ ] IEC inlet L  <-> IEC inlet E: NO beep
[ ] HRP +V       <-> HRP -V: NO beep after initial cap charge
[ ] +24 V rail   <-> 24 V GND rail: NO beep after initial cap charge
[ ] +24 V rail   <-> enclosure earth: NO beep (floating, as designed)
[ ] DDR-30G-12 +Vin connected to +24 V rail
[ ] DDR-15G-5  +Vin connected to +24 V rail
[ ] MOV installed across HRP AC/L and AC/N, leads short
[ ] DC fuse installed in holder
[ ] AC fuse installed in IEC inlet drawer
[ ] All terminal screws firmly seated, no loose strands visible
[ ] All ferrules used at terminals (no bare strands)
[ ] Enclosure cover closes without pinching wires
```

### First power-on

1. Plug IEC cord into the inlet (PSU end). Wall end stays out.
2. IEC inlet switch OFF.
3. Plug into the wall.
4. Switch ON. Watch for any smoke, pop, smell, or immediate fuse blow.
5. Multimeter on HRP +V and -V: should read 24.0 ± 0.3 V. Trim VR1 to 24.0 V
   exact.
6. Power off. Add DDR-30G-12. Power on. Multimeter on DDR-30G-12 +Vout and
   -Vout: 12.0 V.
7. Power off. Add DDR-15G-5. Power on. Multimeter on DDR-15G-5 +Vout and
   -Vout: 5.0 V.

Any reading more than ±5% off nominal: power off, recheck wiring, confirm
the DDR variant is G (9..36 V input, not L 18..75 V), confirm the HRP's
remote-sense pins are jumpered.

## Failure Modes and Recovery

The build relies on **layered failure response**. Each layer covers failure
modes the others cannot, and each layer is identifiable by which device fired.

| Layer | Device | Triggered by | Recovery |
|---|---|---|---|
| 1 | MOV (10D471K) | AC mains surge above ~470 V peak | MOV chars or cracks; AC fuse blows. Replace both. |
| 2 | AC fuse (T2.5 A) | Sustained AC overcurrent | Identify cause (PSU short, MOV failure, wiring fault). Replace fuse only after fixing cause. |
| 3 | PSU internal OVP/OCP/OTP | DC output overload, short, or overtemperature | PSU latches off. Power-cycle after 30 s and fix the load. |
| 4 | DC fuse (T6.3 A) | DC trunk overcurrent | Identify which subsystem shorted, isolate, replace fuse. |
| 5 | P6KE24A TVS (per subsystem) | Transient on +24 V above ~33 V | TVS clamps. Repeated firing suggests heater PWM or solenoid wiring issue; check flyback diode and snubber. |
| 6 | DDR module shutdown | Output short or overtemperature | Module latches off; other rails unaffected because they are isolated. Power-cycle after 30 s. |
| 7 | Thermal fuse in heater circuit | Heater surface above ~100 °C | Fuse blows permanently; replace heater assembly. |
| 8 | Safety MCU software cutoff | PT1000 reads above setpoint plus margin | Safety MCU drops SSR enable line. Primary MCU logs the event. |
| 9 | Operator E-stop (if installed) | Anything visible going wrong | Cuts L on the AC side. Power-cycle to reset. |

## Service Operations

### Replacing a fuse

1. Power off, unplug IEC cord, wait 30 s for cap discharge.
2. Open the fuse drawer (AC, inside IEC inlet) or panel fuse holder (DC).
3. Visually confirm the fuse element is broken.
4. Replace with identical T-rated value and form factor. Never substitute a
   higher-current fuse to "stop it from blowing."
5. Reseat the drawer/holder cap.
6. Re-run the first-power-on procedure.

### Replacing a DDR module

1. Power off, unplug IEC cord.
2. Loosen all four DDR terminals (in/out, positive/negative).
3. Lift module off the DIN rail.
4. Install the replacement module on the rail.
5. Reconnect terminals per the silkscreen markings.
6. Power on; verify output voltage with a multimeter before reconnecting any
   loads.

### Replacing the PSU

1. Power off, unplug IEC cord, wait 30 s.
2. Photograph all input and output terminal wiring before disconnecting.
3. Remove AC and DC wiring from the PSU.
4. Unbolt the PSU from the chassis.
5. Install the replacement. It must be HRP-150-24, **genuine**; re-run the
   counterfeit checks below before installing.
6. Reconnect per the photographs.
7. **Re-run the full verification procedure**, including continuity checks
   and first-power-on. Do not assume the replacement is wired identically;
   verify.

### Servicing the row module (umbilical disconnect)

1. Power off, unplug IEC cord.
2. Unscrew GX16-4 (power) and GX16-6 (sensor/control) cable-mount plugs from
   the panel-mount sockets.
3. Service the row module per its own procedure (printed wedge locks, lid
   removal, COTS consumable swap).
4. On reassembly: physically reconnect both umbilicals before powering on.
5. Verify rails at the row module side using DIN rail test points, then
   proceed to subsystem-level checks.

## Counterfeit Identification

Authority-bearing parts must be authenticated on receipt. The cost of
debugging a counterfeit failure is 10..100x the cost of authentication. This
is the most important quality check in the entire build, more important than
any single component selection.

### MeanWell HRP-150-24

- Genuine has a holographic anti-counterfeit sticker on the housing; the code
  is verifiable at meanwell.com.
- Genuine carries multiple certification etchings: at minimum CB, CE, UL,
  TÜV.
- Genuine PCB silkscreen reads `MEAN WELL` in full, not `MW` or unmarked.
- Open-frame metal end-cap, not all-plastic.
- Authorized seller storefronts use prefixes like `tw-` or `明纬授权经销`.
- Genuine price band on Taobao from authorized sellers: roughly ¥130..¥250
  for the HRP-150-24. Below ¥90 is fake.
- The Chinese knockoff brand is `明伟 (Míng Wěi)`, deliberately phonetically
  identical to MeanWell `明纬 (Míng Wěi)` but with the character `伟` (great)
  substituted for the genuine `纬` (weft). Many sellers confuse the two or
  exploit the confusion. The character difference is the giveaway.

### Sensirion STC31 (and SHT41 on the sensor PCB)

The STC31 replaced the originally-listed SCD41 after application review:
SCD41 saturates at 4% CO2 and cannot measure the 5% setpoint used for
mammalian cell culture. See decision-log entry 2026-05-31 (Sensor Selection
Corrected From SCD41 To STC31).

STC31 authentication on receipt:

- Visual check of laser-etched part number on QFN12 top
- I2C address scan: STC31 must appear at `0x29`
- Baking-soda + vinegar bag test: place sensor in 1 L ziploc with ~10 g
  baking soda and ~20 mL white vinegar; sensor should read climbing
  from 0% toward 2-5% CO2 within 60 seconds. Constant or random readings
  indicate counterfeit. (The exhale-test from the SCD41 protocol does not
  work here because STC31 is not sensitive at the low ppm range.)
- Long-soak return: after bag test, open and let read room air; should
  return to near 0% within a minute. Hysteresis indicates fake or damaged
  unit.

SHT41 authentication on receipt:

- Visual check of laser-etched part number on DFN-4 top
- I2C address scan: SHT41 must appear at `0x44`
- Breath-humidity test: exhale ~5 cm from sensor; reading should jump
  from ~50% to ~85-95% RH within 2 seconds and recover to room RH within
  30 seconds.
- Temperature check: hold between fingers for 60 seconds; reading should
  rise toward 30-34°C and recover after release.

Full sensor PCB validation protocol (post-fabrication) is documented in
`sensor_pcb.md`.

### Vishay TVS (P6KE24A)

- Genuine in original Vishay packaging (printed box with part number, date
  code, lot trace).
- Counterfeits may clamp 10..20% higher than datasheet — defeats the purpose.
  For sensor-protection roles, validate at least one sample on a curve tracer
  or against a calibrated transient source if the application is mission-
  critical.

### Generic risk

Counterfeits of MeanWell, Sensirion, and Vishay parts are widely distributed
on Taobao. Cheap is not always fake, but cheap from an unauthorized seller
almost always is. The cost premium for authorized sellers is the single
highest-leverage spend in the build.

## Sourcing Hazards Observed In Practice

These were active failure modes during the first sourcing pass; they are
documented here so they do not repeat on future orders.

1. **Power cord plug type.** The first sourced power cord arrived (or was
   nearly purchased) with a NEMA 5-15 (US) plug end, despite a Chinese
   sourcing context. Always verify the wall-plug end is `国标三孔` /
   `GB 1002`. The IEC C13 socket end is universal regardless.
2. **MeanWell DDR L vs G suffix.** Phoenix's `FBI X-Y` numbering convention
   suggests letters map to specific features, but Chinese seller listings
   often use letters as marketing SKUs without consistent meaning. **Trust
   the input-voltage-range labels next to each variant, not the letter.**
   For a 24 V system, pick the variant with 9..36 V input range. The seller
   labels here showed L = 18..75 V and G = 9..36 V; this is the opposite of
   what some internet sources claim. Always confirm by the explicit voltage
   range on the listing.
3. **FBI bridge pitch.** Phoenix's `FBI-X-Y` naming has Y = pitch in mm, so
   `FBI-10-5` = 5.2 mm pitch (UK2.5B, UK3N) and `FBI-10-6` = 6.2 mm pitch
   (UK5N). A 6 mm bridge on UK2.5B will visibly sit cocked and only seat one
   or two prongs. Many Chinese listings claim "UK2.5B compatible" while
   selling FBI-10-6; verify pitch in mm with the seller before purchase.
4. **D-UK vs E-UK confusion.** D-UK is the flat end plate (挡板) that covers
   the exposed contact slot on the last terminal in a group. E-UK is the
   rail-clamp end stop (堵头) that prevents the strip from sliding. They are
   different parts with different roles; both are required.
5. **Through-hole vs SMD package.** TVS and MOV searches surface mostly
   surface-mount (SMA, SMB, SMC) parts by default. For terminal-block
   prototyping, search explicitly for `直插` (through-hole) or by axial
   package codes (DO-15, DO-201). SMD parts require a PCB or breakout board.
6. **"Alloy" vs "copper" terminal blocks.** Sellers default to "Grey Alloy"
   recommendations because their margin is higher. Alloy contacts corrode
   under the humidified-CO2 environment this prototype operates in. Always
   pick `Copper Fittings V0` for any production terminal.
7. **TB1510 vs FBI bridges.** Searching for "短接条" (jumper bridge) returns
   both TB-series (fork/spade short-circuit pieces for TB terminal strips)
   and FBI-series (center-jumper bridges for UK terminals). They are
   incompatible. Filter for "中心连接条" or "FBI" to avoid TB matches.
8. **DIN rail length is the actual enclosure-sizing bottleneck, not PSU
   footprint.** A first-pass sizing estimate based on the PSU footprint
   alone (HRP-150 is 199 x 98 mm, "fits in a 300 x 200 box") was undersized
   by ~30%. A realistic terminal count with isolated +24/+12/+5 V rails,
   per-load branch terminals, two DDR modules, end plates, and end clamps
   adds up to ~280 mm of DIN rail, which does not fit alongside the PSU in
   a 300 x 200 interior. Always tally the rail occupancy explicitly before
   choosing an enclosure; the temptation to under-size based on visual
   inspection of the PSU dimensions is strong and wrong.

## Excluded Parts and Why

| Excluded | Reason |
|---|---|
| ATX PSU | Multi-rail without isolation; noisy fan; ground loops between rails. |
| Adjustable bench PSU (DPS3005, RD6006) | Bench tool, not production-mountable. |
| Bridge rectifier | PSU handles AC -> DC; no in-house rectification needed. |
| Zener voltage references | DDR modules handle regulation; no precision reference required. |
| Fast-recovery diodes (UF4007, RHRP) | 1N4007 is fast enough for solenoid switching at <1 kHz. |
| Non-isolated buck converters (LM2596, MP1584) for sensors | Heater PWM ground noise couples into the sensor rail. |
| Glass fuses on AC side | Fault-current breaking capacity inadequate for mains. |
| SMD-only parts when through-hole exists | Hand-prototyping with terminal blocks favors leaded parts. |
| 10D391K MOV | Clamp voltage (390 V) too tight; conducts on normal AC peak. |
| 10D561K MOV | Clamp voltage (560 V) too loose; passes larger surges. |
| Plain-pliers ferrule crimpers | Inconsistent compression; loose AC strands are a fire hazard. |
| Aluminum-contact terminal blocks | Corrode under humidity; hostile to this prototype's environment. |
| Non-V0 insulation terminal blocks | Support flame propagation; unsafe for AC distribution. |
| DDR-15L-X or DDR-30L-X variants | 18..75 V input range; 24 V sits at the bottom edge with poor regulation. |
| TB-series short-circuit bridges | Wrong terminal family (TB, not UK). |
| FBI-10-6 jumpers on UK2.5B | 6.2 mm pitch; will not seat on 5.2 mm UK2.5B terminals. |
| Generic "UK2.5B" green terminals as PE | Not bonded to DIN rail; need USLKG-2.5 specifically. |
| 美规 (US plug) power cords | Will not fit Chinese GB 1002 wall outlets. |
| Audio-grade USB isolators (TOPPING HS02 etc.) | Latency-optimized for DAC use; overpriced for ESP32 CDC. |
| "USB 3.0" / "480 Mbps" budget USB isolators | ADuM3160 chip inside despite branding; same actual function as a properly-labeled full-speed isolator at the same price. |

## Open Considerations

These are deliberate gaps acknowledged in the current build. They are not
non-goals; they are deferred until a specific need triggers them.

- **Emergency stop button.** A latching mushroom-head E-stop wired to break
  AC L is good practice for benchtop biology work but is not yet specified.
  Add when the first heater is wired and the prototype starts seeing wet
  biology.
- **Power-on sequencing.** Currently all rails come up together when the IEC
  switch flips on. For a future build, a soft-start sequence (PSU -> DDR
  rails -> ESP32s -> heater enable) could prevent inrush hits on weak USB
  hosts during programming. Not required for the current scope.
- **Per-subsystem fusing.** A blown trunk DC fuse takes the whole system
  down. Per-subsystem polyfuses or replaceable mini-fuses would isolate
  faults better. Not justified at current subsystem count.
- **Current monitoring.** INA219 modules on each subsystem feed would let the
  primary ESP32 log per-load current and detect anomalies (stuck valve, dead
  heater) before they trip protection. Add when telemetry becomes a project
  goal.
- **UPS or battery backup.** A small UPS on the IEC inlet would prevent
  mid-experiment power loss. Not required for the first prototype.
- **Lab GFCI / RCD upstream.** The lab's wall outlet should be on a GFCI
  branch. Document the outlet's protection state when the prototype is
  installed.
- **Compliance certification.** CE, FCC, CCC are not in scope for the
  research prototype. Build to safe standards anyway so a future compliance
  pass is not a redesign.
- **Thermal management of the PSU at high steady-state.** The HRP-150 is
  fanless to ~80 W. If a future expansion pushes steady-state above 80 W
  (more heaters, observer steppers under continuous motion), add either a
  larger PSU (HRP-300-24) or a quiet enclosure fan blowing across the
  heatsink.
- **Documentation of as-built schematic.** A KiCad or equivalent schematic of
  the as-built power section, alongside this prose, would catch wiring drift
  and aid faster service. Not required for the prototype but recommended
  before the second build.

## Non-Goals

- Powering the OT-2 itself; the OT-2 retains its own AC cord and supplies.
- Power factor correction beyond what the HRP-150's built-in PFC provides.
- Programmable per-rail voltage adjustment beyond the HRP-150's VR1 trim.
- Hot-swap PSU redundancy.
- Galvanic isolation between the ESP32 and its USB programming host (a USB
  isolator is recommended but not part of the power section).
- AC mains conditioning beyond surge clamping (no isolation transformer, no
  PFC stage, no harmonic filter).
- Power for the print-native row coupon's CAD-level validation; the coupon is
  a passive mechanical proof and does not need any electrical service.

## Cross-References

- Materials authority and exception framing:
  [materials strategy](../knowledge/materials_strategy.md)
- Production prototype architecture:
  [architecture](../knowledge/architecture.md)
- Print-native row module assembly tree:
  [print-native row module](print_native_row_module.md)
- Failure-mode philosophy and authority separation:
  [hardware systems lessons](../knowledge/hardware_systems_lessons.md)
- Decision history:
  [decision log](decision_log.md) entries 2026-05-28 (power section authority
  exception, counterfeit authentication) and 2026-05-31 (sensor selection
  correction SCD41 -> STC31, sensor PCB design, sample-plane temperature)
- Sensor PCB design and fab workflow:
  [sensor PCB](sensor_pcb.md)
