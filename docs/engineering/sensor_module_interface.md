# Swappable Sensor Module Interface (SMIS v0.1)

## Purpose

The observer bench (`observer_optical_bench.md`) proves one thing: an inverted
optical head can image cells in a CellVis well from underneath, inside the 80 mm
dry bay, through the real wet boundary. This page asserts the next, larger claim:
**the stage built to carry that head is the actual instrument, and the imaging
modality is a swappable part.** Once the bay holds a fiducial-registered 3-axis
scanner (`observation_module.md`), a head-side Pi, an offboard PSU/compute over the GX16 umbilical
(`power_section.md`), and the single-writer motion lease of the OT-2 bridge
(`agent_ot2_bridge.md`), nothing about that carrier is specific to brightfield.
A dichroic, a beamsplitter, a fiber pickoff, a Raman probe, or a non-optical
impedance head can all ride the same dock if — and only if — there is a frozen
contract for them to ride.

This document is that contract, in three parts: the **interface spec (SMIS
v0.1)**, the **modality catalog** it is designed to host, and the **scaling
roadmap** that takes it from one solo-built head to a platform with partner-built
heads.

It must be read with the same honesty discipline the rest of this knowledge base
uses. **SMIS is a v0.1 contract to design against, not a built subsystem.** It
sits in exactly the state the dry bay was in when the observer bench doc was
written: correctly reserved, deliberately scoped, and carrying **zero installed
parts**. Every dimension, pinout, and ABI signature below is a *specification*,
not a measurement; every imaging or motion claim it makes is **Gate-6 unproven**
until a physical dock is printed and a head is docked. The bench is Stage 0 of
filling the bay with one head; SMIS is the contract for filling it with the
*second* head, and it is honest to say that second head does not yet exist. This
is reserved-and-deferred, like the bay itself.

## Stance

SMIS is a COTS-authority exception in the same family as the power section, the
sensor PCB, and the observer bench. The print-native row coupon
(`one_row_coupon.md`) is a strict no-metal, no-glue mechanical proof; SMIS
deliberately brings commercial optical, electrical, and computing authority into
the dry bay at three named boundaries. Those boundaries are the whole point of the
spec:

- the **dock plane** (mechanical authority hands off to the gantry),
- the **infinity port** (optical authority hands off to the shared objective
  train), and
- the **HEAD-BUS connector** (electrical authority hands off to the offboard PSU,
  a superset of the GX16 umbilical from `power_section.md`).

Above those three planes the platform owns a **frozen** contract. Below them a
module owns a **free** design the platform trusts only after a digest check, an
interlock check, and a registration check — the same fail-closed evidence
discipline the OT-2 bridge already runs. The authority boundary that governs
everything is still the dry-bay envelope: a SMIS head may not intrude on the
sealed wet chamber, touch the CellVis plate (the plate-as-consumable rule from
`materials_strategy.md` holds — all sensing is non-contact from below or a
sibling consumable), or consume the deck-foot keepouts the row coupon validates.

The thesis in one sentence: **the stage is the sensor-agnostic instrument, and
modalities are plug-in heads above two frozen planes** — and the discipline that
keeps this from being vaporware is that the spec is allowed to be only as wide as
two real paid heads demand (see the trap at the end).

## The one number that organizes the catalog

The observer bench picked a **4× plan-achromat, NA 0.10** as the primary
objective. That choice propagates into every modality SMIS can host, through a
single physical fact:

> Collection efficiency ∝ NA²/4 ≈ 0.10²/4 ≈ **0.0025 — about 0.25 % of 4π
> steradian.**

A NA-0.10 objective throws away ~99.75 % of the light a sample emits, and is
~16× more photon-starved than an NA-0.4 air objective, ~400× worse than the
NA-1.3 oil objectives in the quantum-sensing literature. The consequence is that
**the platform's value gradient runs opposite to its difficulty gradient.** The
modalities that need the fewest photons (computational phase, ratiometric
thermometry) are the cheapest, highest-TRL near-term wins; the highest-information
modalities (Raman, single-emitter NV) are exactly the ones the NA penalty makes a
photon-budget fight. This is *why the cheap computational wedge is the correct
place to start*, not a compromise.

The second governing fact is the observer bench's own finding: **the collimated
infinity space between the objective and the f=50 mm tube lens is the only
aberration-free place to insert an optic.** A plane-parallel element (dichroic,
notch, polarizer, beamsplitter, fiber pickoff) in collimated light adds zero
defocus and negligible aberration — a tilted plate just shifts the beam laterally
instead of adding spherical/coma. SMIS turns that ~25-40 mm slot into a *named,
dimensioned, mechanically standardized port* (§ Optical). The modularity slot is
not invented here; it is the same trick every infinity-corrected microscope uses.
SMIS only freezes its geometry.

These two facts split the catalog cleanly:

- **Back-end / front-end swap** — keep the objective and plate-side hardware,
  change only what lives in or after the infinity space. Registration survives
  trivially. The cheap, fast, high-value zone.
- **Whole-head swap** — change the objective itself (different NA/WD), re-register.
  A real engineering tax.
- **Fork** — needs electrodes or probes in contact with cells. Breaks the
  no-contact plate rule, so it is a *sibling consumable*, not a head.

## The modality catalog

Ranked by value-per-effort for a solo builder. "Share" = back-end/front-end swap
preserving the 4× objective and the fiducial registration; "Head-swap" = new
objective/probe plus re-registration; "Fork" = plate contact required → sibling
consumable, not a head; "Level-3" = non-imaging — no objective and no infinity
port, dock + bus + manifest only. Cost is added optics/source only (the shared
camera, objective, and stage are sunk). TRL-solo is the realistic
technology-readiness for *this* geometry built by one person, not the modality's
textbook maturity.

Rows #1-#12 are rank-ordered. **#13 is appended, not ranked** — the numbering was
already load-bearing across this document and the roadmap when it was added, and
renumbering a catalog other sections cite by number is a silent reference break.
On value-per-effort #13 sits near #4/#5, below the two wedge heads.

| # | Modality | Measures | Share / swap / fork | Cost | TRL-solo | Verdict |
|---|---|---|---|---|---|---|
| 1 | **QPI / DPC / FPM** ⭐ | Label-free dry mass (pg/cell), morphology, confluency, motility | **Share** — LED matrix only | ~$20 | 7-8 | **Near-term win. The wedge. Build now.** Quantitative, differentiating, zero new optics. |
| 2 | **Epifluorescence 1-4 ch** ⭐ | Viability, GFP/RFP reporters, nuclei, IF, Ca²⁺ | **Share** — dichroic cube in infinity port | $300-800 | 8-9 | **Near-term win. The revenue modality.** NA 0.10 limits it to *bright* labels; dim single-molecule needs a high-NA head. |
| 3 | **Multispectral + polarization** ⭐ | Absorbance/chromophore; birefringence (collagen, spindle, fibrosis) | **Share** — reuses #1/#2 hardware | <$100 | 7-8 | **Near-term win, as free variants.** Absorbance survives NA 0.10 because it is **ratiometric** (I/I₀), so the collection penalty largely cancels — the #4 argument, not a free-rider accident. What ships is *serial per-well spectrophotometry of an imaged field*, never a 3-second plate read (`../knowledge/byonoy_plate_readers.md`). Transmission absorbance also needs the lid-window branch of C-OB2. Ship with #1/#2, not as headline heads. Plastic-optic strain birefringence is the watch-out. |
| 4 | **UCNP / lanthanide ratiometric thermometry** ⭐ | Sample-plane / per-well T, 0.1-0.5 K, in living cells | **Share** — 980 nm pump + 525/545 split | <$550 | ~6 | **Near-term win. The real quantum-adjacent head.** Ratiometric ⇒ NA-insensitive; no microwave; a genuine upgrade over the MLX90614 thermopiles. |
| 5 | **Optical O₂ / pH chemical-spot** | Dissolved O₂, pH ratiometrically (Ru/porphyrin, fluorescein) | **Share** — same epi path as #4 | ~$200 | 7 | Near-term, no-contact compatible (spot lives in media/film, not on hardware). Metabolic readout. |
| 6 | **Raman 785 nm point-probe** 🎯 | Label-free molecular fingerprint (lipid/protein/NA, drug uptake) | **Share** pickoff; **wants own high-NA head**; spectrometer **offboard via fiber** | $10-23k | 4-5 pt / 2-3 map | **Frontier bet. The moat, and the reason the 80 mm bay exists.** Throughput-limited to sparse/targeted spot-checks — *not* a 384-well raster. Must not gate the platform. |
| 7 | **NV-diamond ODMR thermometry** 🎯 | mK-class T (D = 2.87 GHz, dD/dT = −74.2 kHz/K), window-bonded diamond | **Head-ish** — dichroic + MW; CPW printed on head-top window | ~$0.5-1.2k | 5 bench / 2-3 in-platform | **Frontier bet. The credible "quantum" headline** — as an mK *non-contact reference thermometer*. **NOT intracellular, NOT magnetometry** (see bounded claims). |
| 8 | SPAD / FLIM | Lifetime (ns) → NAD(P)H metabolism, FRET, pH/viscosity | **Share** — detector swap behind infinity port | $20-60k | 3-4 | Very high value, **sourcing-blocked**: no Taobao path to a SPAD array. Park until consumer-LiDAR SPADs commoditize. |
| 9 | ECIS / impedance / TEER | Barrier, adhesion, migration (label-free, kinetic) | **Fork** — electrodes contact cells | <$100 chip | 7 standalone / 3 integrated | Strong razor-blade *second consumable*, not a head. Shares gantry/registration/daemon, not the optics. |
| 10 | Electrochemical (O₂/pH/lactate/neurotransmitter) | Amperometric/potentiometric media analytes | **Fork** (prefer optical #5 for no-contact) | low | 7 / 3 | Use the optical route #5 instead where possible. |
| 11 | IR-thermography (microbolometer) | Coarse bay/lid thermal map | Head/lid-side only | ~$150 | 8 | Low. Glass is LWIR-opaque → cannot see the sample plane through the coverslip from below; lid/oblique only. |
| 12 | Photoacoustic | Optical-absorption contrast at depth | Head-swap | $5-23k | 4 | Niche. Acoustic couplant breaks the dry-bay/no-contact rule. |
| 13 | **Luminescence (SiPM, non-imaging)** | ATP/viability, luciferase reporters, pathway + circadian kinetics | **Level-3** — no objective; one large-area SiPM + light guide, scanned well-to-well by the stage that already exists | ~$150-300 | 6-7 | **Reserved, not promised — and the first honest Level-3 candidate.** The one entry where *deleting* the objective improves the measurement: a SiPM under the well buys back one to two orders of magnitude of solid angle over the 0.25 % NA-0.10 path (geometric estimate, unmeasured). One detector, not Byonoy's 96, because the stage scans. Failure modes are environmental, not optical (see bounded claims). Does not gate the wedge. |
| — | OCT / CARS-SRS / O-PTIR / light-sheet / SIM-STORM | 3D structure / fast Raman / IR-chem / sectioning / super-res | Whole new instrument or architecturally excluded | high | 1-3 | Platform-headroom slide only. Geometry or NA forbids on this stage. |

Rows #3 and #13 come from a review of the commercial solid-state parallel readers
(Byonoy / the Opentrons Flex absorbance module) in
`../knowledge/byonoy_plate_readers.md`: absorbance survives NA 0.10 because it is
ratiometric, what we would ship is serial per-well spectrophotometry of an imaged
field rather than plate reading, and luminescence — which that review found the
catalog was missing entirely — is the one modality that is *better* without an
objective.

### The bounded claims (honesty, load-bearing)

Four entries in the catalog are routinely over-sold, and SMIS documents their
real limits so the project stops spending cycles on them:

- **NV is an mK *reference* thermometer, not intracellular thermometry and not
  cell magnetometry.** The defensible build is architecture (B): a thin NV-diamond
  membrane plus a printed coplanar-waveguide microwave antenna bonded to a
  head-top window ~8 mm below the plate. The diamond and its antenna travel with
  the head, off-plate, fully under module authority, and deliver mK-class
  *non-contact bath / sample-plane* temperature — a real upgrade over the
  thermopiles. It measures the window's temperature, ~8 mm from the cells, **not**
  intracellular temperature. Intracellular FND thermometry through the NA-0.10
  objective is TRL 2-3 and likely will not close without an NA ≥ 0.7 head.
- **NV magnetometry of cells is infeasible on this geometry — do not promise it.**
  The landmark single-neuron result needed the diamond ~10 µm from an *excised
  invertebrate giant axon* (mm-scale, enormous current) and still got SNR ≈ 1.2.
  Mammalian cells through 0.17 mm of coverslip + media with the sensor ~8 mm away
  put the signal **3-4 orders of magnitude below** the NV floor. This is not a
  sensitivity-tuning problem. The only legitimate use of the magnetometry channel
  here is rejecting stray-field artifacts in the mK thermometer (read both ODMR
  transitions to separate B from T).
- **Raman is throughput-limited to sparse spot-checks and wants its own head.**
  Spontaneous Raman cross-sections (~10⁻³⁰ cm²) × the 0.25 % NA collection ×
  cellular autofluorescence make per-point integration realistically 1-30+ s. A
  hyperspectral map of one Ø6.21 mm well at 10 µm steps is ~300k points —
  physically impossible at screening throughput. Raman on this platform is a
  *targeted molecular spot-check*, it genuinely wants a dedicated higher-NA
  Level-2 head, and the heavy cooled spectrometer **rides offboard via fiber**,
  never on the head (see the offboard rule). It is the flagship R&D module,
  partner-built against a frozen spec, and must not gate the platform.
- **Luminescence is a photon-collection problem, and the objective is the
  problem.** The over-sell is "we get luminescence free on the imaging head":
  through the 4× NA-0.10 path a reporter-level bioluminescent signal is
  integration-bound — seconds to minutes per field, flux-dependent — because the
  objective throws away 99.75 % of an emission that has no excitation to turn up.
  The defensible build is **Level-3, non-imaging**: one large-area SiPM with a
  light guide directly under the well, one number per well, scanned by the stage
  (#13). What that buys is solid angle and no focus requirement; what it does
  **not** buy is spatial information — it reports that the well lit up, never
  which cells did. It is also the only catalog entry whose dominant failure modes
  are environmental rather than optical: stray light in the bay (the WS2812 ring
  and any deck-side leak must be dark during acquisition, which the bay is not
  built for today), SiPM dark-count rise at the 37 °C row setpoint, and
  plate/mat afterglow following any illuminated step. Those three, not the
  detector, are the build. Electrically it is an ordinary tenant of the existing
  bus — SiPM bias (~27-55 V, part-dependent) is a **module-side** boost from the
  HEAD-BUS +24 V rail, which the FREE column already allows — so appending #13
  forces no SMIS-major bump. An appended row owes the contract that check.
- **SPAD/FLIM is sourcing-blocked, not physics-blocked.** The optics are a clean
  detector swap behind the infinity port; the wall is that a SPAD array is
  $20-60k+ with no China/Taobao path. Park it; revisit when automotive-LiDAR SPAD
  supply commoditizes.

**Near-term wins (build now):** #1 QPI/FPM, #2 fluorescence, #4 UCNP thermometry,
with #3 and #5 as cheap riders. **Frontier bets:** #6 Raman and #7 NV-thermometry
arch-(B). **Reserved Level-3 candidate:** #13 luminescence — cheap and
physically favorable, but it spends the same solo build-hours as the wedge, so it
waits behind #1 and #2 and is not a third head.

## SMIS v0.1 — the interface contract

Status: **DRAFT-FOR-FREEZE.** Authority class: COTS-authority exception. Authority
boundaries: the dock plane (mechanical), the infinity port (optical), the HEAD-BUS
connector (electrical). Above those three planes = FROZEN platform contract; below
them = FREE per-module design.

### FROZEN vs FREE at a glance

| Layer | FROZEN (platform owns) | FREE (module owns) |
|---|---|---|
| Mechanical | Dock plane DP-0, 3-2-1 kinematic seats + 3 magnets + dowel, bolt pattern, mass ≤ 900 g, envelope 120 × 347.5 × 40 mm, Ø32 barrel keepout, 62 mm Z, front face ≤ z = −8 | Internal optomech, where mass sits, fold count, source mounts |
| Optical | Infinity-port plane PD-0, Ø20 clear collimated aperture, 30 mm cage + RMS + C-mount triple standard, parfocal datum, tube-lens-to-sensor = 50 mm | Whatever drops into the infinity space; the objective itself if Level-2; nothing if Level-3 |
| Electrical | HEAD-BUS pinout (24 V / 5 V / 3.3 V / GigE / I2C / 1-Wire / MW-coax / 2× interlock / shield), blind-mate float connector, no hot-mate, ID-EEPROM at I2C `0x50` | Which rails it draws, what rides the data lane, MW power, laser class |
| Software | `module.json` manifest schema, the driver plugin ABI, `acquire(well, lease) -> Evidence`, the safety-class enum, the lease protocol | Driver internals, calibration model, per-modality params |
| Registration | 16 × Ø2 mm fiducials on the plate-support frame *are* the world frame; only the module→dock transform is re-established on a swap | The module's internal optical-axis offset (declared in manifest, verified on dock) |

A change to anything in the FROZEN column is a **SMIS-major** bump and re-validates
every head. A change in the FREE column is a per-module bump. SMIS-minor is
additive-only. This is the same rule `coordinate_system.md` applies to pose
schema, and the same contract discipline `power_section.md` froze for the GX16
pinout.

### The three tiers

- **Level-1 — back-end swap.** Objective, fold, tube lens, and oblique LED ring
  stay; the module is a cage insert dropped into the infinity space (fluorescence
  dichroic cube, 50:50 beamsplitter for epi, fiber pickoff to an offboard
  spectrometer, polarizer/analyzer). Parfocal by construction, Tier-A
  registration. Cheapest and fastest; #1-#5 all live here.
- **Level-2 — whole-head swap.** The module brings its own objective (high-NA
  Raman head, long-WD head). The entire head undocks at the kinematic dock; the
  new head must still respect the envelope, mass, keepout, Z budget, and present
  the same HEAD-BUS. Tier-B/C registration.
- **Level-3 — non-imaging.** No objective, no infinity port: impedance probe,
  MW-resonator, NV quantum head, SiPM luminescence head (#13 — the first
  candidate that is *better* in this tier than above it, and the first the tier
  has to actually exercise). Uses only the dock + bus + manifest.

### Mechanical — the kinematic dock (FROZEN)

- **Dock plane DP-0:** a horizontal plane on the gantry Z-carriage; all module
  Z-offsets are declared downward from it. DP-0 is the single mechanical truth.
- **Envelope, inherited verbatim from the bench, not renegotiable:** swept body
  **120 × 347.5 × 40 mm**; **Ø32 mm** barrel keepout (= `objective_keepout_diameter`
  in `cad/one_row_coupon.params.json`); **62 mm** usable Z below DP-0
  (= `carriage_height_z`); front face **≥ 8 mm below the plate** (never crosses
  z = −8, = `carriage_top_clearance_z`).
- **Mass budget ≤ 900 g (target 600 g).** The Y-truck indexes 334.5 mm and focus-Z
  must settle inside the bench's vibration spec (≈ ±27 µm at 4×) at exposure;
  heavier heads lower the structural-loop resonance and lengthen settle. Mass and
  CG are manifest fields that gate the scan-speed profile.
- **Coupling — a quasi-kinematic 3-2-1 with magnetic preload.** A true Maxwell
  kinematic is fussy to print and a contamination trap in a wet-adjacent bay, so
  the decisive choice is **3 hardened-ball-on-cone/vee/flat contacts + 2 pull
  magnets + 1 anti-rotation dowel.** One cone (3 DOF), one vee (2 DOF), one flat
  (1 DOF) = 6 contacts, 6 DOF, exactly constrained. Three Ø6 mm grade-25
  chrome-steel balls (`钢珠 6mm`) press into the *module*; the cone/vee/flat seats
  are on the *gantry* and are the long-lived datum (precision on the shared part,
  not the swap-frequency module). Preload by **3× N52 pot magnets Ø10×5 mm**,
  ~3 kg each (`强力磁铁 沉孔 D10`) → ~9 kg pull. The margin is taken against the
  **1 g-scan separating demand** — the head's static weight *plus* its inertial
  reaction at 1 g (~2× the 900 g weight = 1.8 kg-f), not the static weight alone —
  giving 9 / 1.8 = **5.0×**. (The original 2-magnet figure read ~6.7× against static
  weight but only ~3.3× against this demand; the SM-1.2 dock-check review surfaced
  the load-case error and the spec moved to 3 magnets — see `decision_log.md`.) A
  single Ø3 dowel + lead-in chamfer makes the dock one-handed and blind; 2× M3
  captive thumbscrews are secondary retention if a magnet is heat-demagnetized.
- **Repeatability target: ≤ 5 µm lateral** (reserved-and-unproven until the bench
  measures it — see Top 3 moves). 5 µm is comfortably inside the 4× DOF (±55 µm),
  so 4× and low-NA heads trust the coupling. **At 10× the DOF is ±4 µm and the
  coupling alone is not enough** — those heads declare
  `requires_post_dock_autofocus: true`.
- **Swap never touches the wet stack.** The dock is *under* the deck; the plate is
  70+ mm *above*, on the opposite side of the deck plane. The swap runs with Z
  retracted to dock-park (z = −60) and Y at the service index off all four plates,
  approached from the reserved service-raceway side. Same frozen service order as
  the umbilical: de-energize → unplug → swap → re-plug → re-energize → detect →
  re-register.

### Optical — the infinity port (FROZEN)

- **Port datum plane PD-0:** the plane in the collimated space where a back-end
  mates, set **28 mm above the objective shoulder** (the infinity space is
  25-40 mm; 28 mm leaves room either side for a fold/dichroic). The row-coupon
  CAD now surfaces this as `observer_infinity_port_datum_check`, a Gate-6
  validation-only PD-0 datum slab that fails if PD-0 leaves the front-end Z
  envelope.
- **Clear aperture at PD-0: Ø20 mm** of unvignetted collimated beam. The
  4×/NA0.10 + f50 train fills only ~Ø8-10 mm; Ø20 gives headroom for higher-NA and
  off-axis fields.
- **Triple mechanical standard, all three present, frozen:** the **30 mm cage**
  system (4× Ø6 mm rods, structural), the **RMS thread** on the objective side
  (parfocal 4×/10×/20× swap), and **C-mount** on the detector side (inherited
  directly from the bench's IMX178 camera). They are orthogonal roles — cage
  carries load, RMS carries the objective, C-mount carries the detector — so
  freezing all three costs nothing and lets off-the-shelf adapters bolt to the
  port. **Tube-lens-to-sensor = 50 mm** is frozen for the shared imaging back-end
  (the one critical spacing the bench pinned); a re-imaging Level-1 back-end
  declares its own conjugate past PD-0. The same CAD check pins the Ø20 aperture,
  30 mm cage standard, RMS/C-mount presence, and 50 mm spacing so Level-1
  back-end swaps cannot silently drift the optical datum.
- **The offboard rule (mass + thermal escape hatch).** Heavy or bulky analyzers —
  Raman spectrometer, cooled detector, pulsed laser, high-sensitivity PMT — **never
  ride the head.** The head carries only a fiber pickoff/launch at PD-0; the
  analyzer lives offboard in the PSU/compute enclosure, coupled by a fiber routed
  down the service raceway alongside the GX16 umbilical. This is exactly how the
  80 mm bay budget is spent without breaking the 900 g ceiling.

### Electrical — the HEAD-BUS (FROZEN)

A single blind-mate connector at the dock, **float-mounted ±0.5 mm** so the
kinematic balls register position and the connector follows (it never fights the
datum). **No hot-mate:** rails are de-energized at the offboard PSU before any
dock/undock, enforced by a make-last/break-first short pin on the interlock loop —
undocking physically opens the laser and MW enable loops before any signal pin
parts. HEAD-BUS is a **superset of the GX16 contract** from `power_section.md`,
reusing its rail definitions, levels, and single-point-earth ground plan so one
offboard PSU serves both umbilicals.

| Signal group | Line(s) | Spec | Notes |
|---|---|---|---|
| +24 V / GND | 2 | from HRP-150-24, fused at head branch | motion/heater-class loads only |
| +5 V / GND | 2 | from DDR-15G-5, isolated | head-Pi, LED-ring driver |
| +3.3 V / GND | 2 | ≤ 500 mA, sensor/logic | matches GX16-6 level |
| I2C SDA/SCL | 2 | 3.3 V logic | ID-EEPROM + low-rate module sensors |
| 1-Wire | 1 | DS28E07-class | redundant ID + per-module cal vault |
| GigE data | 4 (M12 X-coded) | 1000BASE-T | head-Pi capture lane; the frozen high-speed path — reuse it, do not invent CSI-over-coax |
| MW coax | SMP/SMA | DC-6 GHz, **populated NV-only**, capped otherwise | NV magnetometry/thermometry |
| Fiber bulkhead | FC/SMA905 | on the float carrier | spectroscopy offboard signal (optical, not electrical) |
| INTERLOCK_LASER | 1 | active-low hardware loop | breaks laser-enable if head undocked or lid open |
| INTERLOCK_MW | 1 | active-low hardware loop | breaks MW-amp enable |
| ALARM | 1 | open-drain active-low | inherited from GX16-6 pin 5 semantics |
| SHIELD / chassis | 1 | 360° backshell | single-point bonded at the sensor-cluster star — **no second earth bond** (power-section rule) |

The frozen HEAD-BUS table is mirrored as a machine-checkable schema in
`src/aevum_smis/head_bus.py` (`FROZEN_HEAD_BUS`). The validator pins the required
signal groups, unique line IDs, no-hot-mate rule, EEPROM address `0x50`,
make-last/break-first active-low laser/MW interlocks, and single-point shield
bond so a hardware record cannot silently drift from this table.

The observer offboard umbilical is separately frozen in
`src/aevum_smis/observer_umbilical.py` (`FROZEN_OBSERVER_UMBILICAL`): GX16-4 carries
24 V and 5 V, GX16-6 carries I2C, 3.3 V, alarm, and the observer enable loop, and
GigE stays on the M12 X-coded bulkhead rather than GX16. The reconciliation check
proves HEAD-BUS remains a superset of those GX16/M12 authority classes before a
future dock or head revision can claim compatibility.

**Module auto-ID and the cal vault.** An **ID-EEPROM at fixed I2C `0x50`** holds
the module identity and manifest digest (`sku`, `module_serial`, `smis_version`,
`hw_rev`, `safety_class`, `axis_offset_mm`, `parfocal_z_mm`, `mass_g`, `cg_mm`,
`manifest_sha256`), read on dock by `platform.detect()`. A **1-Wire DS28E07**
serves as the calibration vault and anti-counterfeit token (factory cal blob plus
a crypto challenge) so the platform can **refuse to drive a Class-4 laser from an
uncertified head** — the connector-level expression of the Sensirion
genuine-parts discipline in `power_section.md`/`sensor_pcb.md`. The `0x50`
EEPROM never collides; any module-local I2C sensors sit behind a per-head
TCA9548A, the same pattern the dual STC31/SHT41 PCBs already use. The
laser/MW interlocks are **hardware** loops (series-wired through head-docked seat
switch, bay-lid-closed, OT-2 bridge E-stop) — software can additionally disable
but can never override the loop to enable.

### Software — the `acquire() -> Evidence` ABI (FROZEN)

A module is, to the orchestrator, a thing that produces evidence at a well under
the motion lease. It plugs directly into the OT-2 bridge core
(`agent_ot2_bridge.md`) and the immutable Evidence packet model
(`evidence_model.md`). Every modality implements one driver interface:

```python
class ModuleDriver(Protocol):
    manifest: Manifest
    def on_dock(self, platform: PlatformCtx) -> RegistrationResult: ...   # tier A/B/C
    def configure(self, params: dict) -> None: ...
    def acquire(self, well: WellTarget, lease: MotionLease) -> Evidence: ...  # the polymorphic call
    def health(self) -> HealthReport: ...
    def on_undock(self) -> None: ...                                      # source off, park, release
```

`acquire(well, lease) -> Evidence` is the single polymorphic call. A brightfield
head returns an image stack; a Raman head returns a spectrum at a point; an
impedance head returns a Z(f) sweep — **all return the same `Evidence` packet
type** the bridge already defines (immutable, handle-referenced, carrying
`manifest_sha256`, `module_serial`, well id, run/command ids, calibration ref).
The orchestrator's loop — *for each well in plan: ensure lease → drive stage →
`acquire(well)` → write evidence → gate* — never changes per modality. **One
orchestrator, N modalities** is the platform payoff. Drivers are entry-point
plugins (`aevum_modules.<modality>`) loaded by the manifest `driver` field on
dock; the platform never hard-codes a modality.

The manifest carries **falsifiable assertions** the platform re-checks against the
frozen keepout — `mechanical.envelope_ok` and `front_face_z_mm` are verified
against the same `8 + FE_z + stroke ≤ 62` and `barrel Ø ≤ 32` arithmetic the
observer bench made test-failable. A manifest that claims an envelope it does not
fit is rejected at dock, not discovered by a crash.

**Tie to the lease and fail-closed.** `acquire()` runs only while the driver holds
a valid `MotionLease` from the bridge's single-writer lock; a module is just
another lease-respecting client, and an undock releases the lease. The bridge
reads `safety_class` and refuses source-enable unless the hardware interlock loop
is closed *and* the 1-Wire cal vault validates. Manifest-digest mismatch, missing
post-dock registration, evidence-write failure, or interlock-open → no motion, no
source. These are not new rules; they are the bridge's existing non-negotiables
applied to the module boundary.

### Registration survives the swap

Registration is anchored on the **16 × Ø2 mm fiducials on the plate-support
frame** (`observer_fiducial_diameter = 2.0` in `cad/one_row_coupon.params.json`).
That is the world frame and it does **not** move when a head swaps. A swap only
re-derives the **module→dock transform** — where this head's optical axis sits
relative to DP-0 — at one of three tiers declared in the manifest:

- **Tier A — trust the coupling** (default for 4× and low-NA): apply the declared
  `axis_offset_mm` / `parfocal_z_mm`, verify with one fiducial touch-up (~5 s).
- **Tier B — re-fiducial** (high-NA / Level-2): 3-fiducial affine solve + per-region
  autofocus map (~30-60 s). Required whenever `requires_post_dock_autofocus`.
- **Tier C — full re-cal** (non-parfocal Level-2, or first install of a SKU): full
  16-fiducial solve + focus map + the module's own ritual (dark frame, lamp
  warm-up), cached by `module_serial`.

This policy is encoded in `src/aevum_smis/registration.py`. Docking, manifest
compatibility, and registration are separate gates: a head may be mechanically
accepted and still fail closed for acquisition if `on_dock()` reports too weak a
tier, too few fiducials, an unknown tier, or `ok=false`.

### FROZEN vs FREE, one sentence

The dock plane, the Ø20 infinity port on cage+RMS+C-mount, the HEAD-BUS pinout,
the `module.json` schema, and the `acquire(well) -> Evidence` ABI are the immovable
platform contract; everything a head does below those planes — optics, source,
analyzer, calibration — is the module's free design, trusted only after digest +
interlock + registration check.

## The scaling roadmap

### Build sequence — each head validates exactly one interface layer

The discipline is *never build a modality to get the modality; build each
modality to validate the one interface layer whose failure would kill the
platform, in that order.* Each step ships a usable instrument on its own.

| Order | Head | Proves (the interface layer) | The hard part it retires |
|---|---|---|---|
| 0 | Oblique brightfield (the bench head) | Dock + fiducial registration + OT-2 lease | "Can I image 384 wells from below, repeatably, with trustworthy coordinates?" |
| 1 | **QPI / FPM** (LED matrix) | Compute/registration spine, zero new optics | "Is the reconstruction pipeline robust across 384 wells?" — and it is the wedge |
| 2 | **Fluorescence 1-ch** | **Infinity port + electrical auto-ID** | "Does a real dichroic drop in with zero registration penalty, and does the head self-announce?" — for ~$150, not after a Raman build |
| 3 | 2nd fluor head (multi-band) | **Hot-swap interchangeability, N=2 → FREEZE the spec** | "Two heads, one stage, swap without recal, config travels with the head?" Modularity is unproven until N=2 |
| 4 | Raman pickoff (partner-built) | 80 mm bay + **offboard fiber back-end bus** | "Is the bay a real systems budget or a fiction?" |
| 5 | NV-thermometry / non-optical | The abstraction survives a non-camera | "Does the platform host something that isn't a microscope?" |

This order is forced, not arbitrary. Brightfield first because if registration off
the 16 fiducials does not survive a focus sweep and a Y-index across four plates,
nothing else matters. Fluorescence second and non-negotiable because it is the
*minimum* change that exercises the infinity port (insert a dichroic), the bus
(excitation power + auto-ID), and the software (a new acquire mode) — if the port
standard is wrong, fluorescence exposes it for ~$150 instead of after a Raman
build. A second fluorescence head before Raman because **modularity is unproven
until N=2**: that is the first time interchangeability *itself* is demonstrated.
Raman before NV because Raman is the first head that breaks "it's a camera on the
end" and validates the offboard fiber back-end. NV last because it abandons the
optical train's purpose entirely.

**The static bench de-risks every module.** A fixed off-gantry bench with
identical infinity-port geometry, objective, and dock face, on a breadboard with
one well or a calibration slide, validates each head's *physics* with motion
removed from the loop. Only a head that produces correct signal there earns a live
dock. This decouples "is the physics right" from "is the motion right" — the most
expensive coupling for a solo builder to debug — and it is the artifact handed to
a partner so they validate *their* physics without the motion stack.

### Solo → platform: the frozen published spec is the team you don't have

A solo founder cannot build five modalities serially in any reasonable time. The
only way one person becomes a platform is to make modalities into *independent,
parallelizable, delegable* tracks, and the thing that makes them independent is a
**frozen, published interface.** You personally build the stage, dock, bus,
registration loop, software abstraction, and the **first two heads** — you cannot
publish an interface you have never built against, and N=2 is the minimum that
reveals the true axis of variation and the maximum a solo founder should
generalize from. Then **freeze v1 additive-only** and parallelize: contract out
fabrication, PCBs, filters; **partner** Raman (a spectroscopist) and NV (a quantum
group), each building against the spec plus a static-bench unit, touching the
dock/port/bus but never the stage, shipping back a docking module. Documentation
plus the bench *are* the org; semver is how you do not break partners — a head
built against v1 docks forever, exactly as `power_section.md` froze its umbilical
pinout as a contract future row modules design against.

### Platform strategy

- **The wedge = automated below-deck live-cell fluorescence (+ brightfield/QPI)
  on the OT-2.** Not brightfield (commoditized), not Raman (small market, long
  sell), not NV (no buyer). Fluorescence is the largest "I'll pay today" market in
  cell biology, and it is the *same work* as the modularity proof (steps 1-3), so
  you never choose between de-risking the platform and shipping the product.
- **The desperate first customer:** a lab or small biotech running high-content
  **live-cell** assays on an OT-2 with no on-deck imaging — today they pull plates
  and walk them to an $80-250k imager, breaking the automated, incubated,
  liquid-handled context. They are desperate for registered, protocol-triggered
  fluorescence *that lives on the deck so cells never leave the workflow.*
- **Razor-and-blades:** razor = the stage (dock, registration, OT-2 integration —
  the install base); blades = certified heads + calibration + analysis software.
  You do not own the CellVis plate, so recurring revenue is heads + cal + software,
  and every later head is a low-friction upsell to a customer who already trusts
  the stage.
- **Open the dock, close the back-end.** *Publish* the mechanical dock, the
  infinity port (cage/RMS/C-mount are already open standards), the HEAD-BUS
  pinout, the manifest schema, and the `ModuleDriver` API — openness grows the
  catalog and makes your dock the standard. *Hold* the registration IP, the
  lease/arbitration daemon, the motion stack, and the cal-vault/safety-class
  certification — so only validated heads can drive lasers on your stage. Open
  enough to grow the catalog, closed enough that the stage and the best blades are
  yours.

### The top 3 moves now

1. **Print the dock and measure dock-undock-redock repeatability — ~¥50 and an
   afternoon.** 3 balls + cone/vee/flat + 3 magnets + dowel on the existing bench
   cradle; image the USAF target across 20 cycles. **Gate: ≤ 5 µm lateral, focus
   ≤ DOF.** This single experiment proves or kills the entire platform thesis. It
   is the SMIS equivalent of the WS2812 matrix — the highest-leverage purchase on
   the list, and it converts the dock's central reserved-and-unproven claim into
   physical Gate-6 evidence.
2. **Buy the ~$20 LED matrix and ship QPI/FPM as Module #0+#1.** Free
   physics-per-dollar; turns Aevum from "another well-plate camera" into a
   *measurement* platform (dry mass) and de-risks the compute/registration spine
   with zero new optics.
3. **Build the one fluorescence head and land one desperate live-cell OT-2
   customer** (revenue or signed LOI) before any third head. This is
   simultaneously the wedge product, the infinity-port test, and the auto-ID test.
   Freeze SMIS v1 from what these two head families actually needed — then, and
   only then, hand the frozen spec + a bench unit to a Raman partner.

### The trap

**Generalizing the interface against five imagined modalities instead of two paid
heads.** The solo-founder death is spending 18 months perfecting a
dock/bus/abstraction elegant enough to host Raman and NV — designing the bus for
the laser you have not built — and running out of money with a beautiful spec and
zero install base. The discipline: design the interface only as wide as two paid
heads (brightfield + fluorescence) demand, make it additive-only so Raman and NV
*extend* it later without breaking it, and let desperate customers — not the
catalog — pull the platform into being. **The interface is the moat, but the wedge
is the company.**

## What SMIS does not prove (scope lock)

Like the observer bench's "what Stage 0 does not prove," SMIS is explicit about
its own limits:

- **It is a contract, not a build.** Zero SMIS parts are installed. Every
  dimension, pinout, and ABI signature is a specification to design against, and
  every motion/imaging claim it implies is Gate-6 blocked until a physical dock is
  printed and a head is docked. The ≤ 5 µm repeatability number is a *target*, not
  a measurement (Top 3 move #1 exists to retire it).
- **It rides on the observer bench, not the other way around.** SMIS assumes the
  bench has already answered focus, contrast, the illumination fork, and the 62 mm
  Z-closure for *one* head. Those answers (and their caliper-measured `front_end_*`
  and `observer_sweep_extra_x/y` values) are inputs to the SMIS envelope; SMIS
  does not re-derive them.
- **It does not resolve the carriage-traversal gap.** Whether a 62 mm head
  traverses the full 334.5 mm row between the deck feet inside 80 mm is the
  observer bench's Stage-3 motion problem, unchanged by SMIS. SMIS only guarantees
  that *any* head it hosts respects the same envelope the gantry must carry.
- **The catalog's frontier rows are reserved, not promised.** Raman, NV, SPAD,
  ECIS — and the appended Level-3 luminescence row #13 — are documented so the
  platform is designed not to *preclude* them, not asserted as deliverable on the
  current geometry. #13 is cheap and physically favorable, which is exactly why
  it needs saying: cheap is not the same as scheduled, and nothing about it has
  been built or measured. The bounded-claims section is
  load-bearing: NV is an mK reference, not intracellular and not magnetometry;
  Raman is sparse spot-checks wanting its own head; SPAD is sourcing-blocked.

## Cross-references

- Stage 0 optical bench, envelope, optical train, infinity-space thesis,
  Z-closure asserts: `observer_optical_bench.md`
- The moving 3-axis stage SMIS heads dock to — kinematics, scan cycle, mass/Z
  envelope, the OT-2 lease, and the kinematic mount this dock extends:
  `observation_module.md`
- Dry bay, deck interface, well grid, fiducials, observer-reserved CAD params:
  `one_row_coupon.md` and `cad/one_row_coupon.params.json`
- GX16 frozen umbilical pinout, rail levels, single-point-earth ground plan,
  no-second-earth-bond rule, counterfeit-authentication discipline:
  `power_section.md`
- Custom-PCB COTS-authority-exception pattern, I2C addressing, TCA9548A, genuine
  Sensirion discipline: `sensor_pcb.md`
- World frame, pose-digest and schema-versioning precedent ("rot90 is a schema and
  gate migration"): `coordinate_system.md`
- Single-writer motion lease, evidence→claim→gate, fail-closed rules the software
  layer plugs into: `agent_ot2_bridge.md`
- The immutable Evidence packet the `acquire()` ABI returns into:
  `evidence_model.md`
- Plate-as-consumable / no-contact rule and the COTS-authority-exception framing:
  `materials_strategy.md`
- Low-turbulence headspace and per-plate sampling rationale: `architecture.md`
- Decision history: `decision_log.md`
