# Print-Native Row Module

## Stance

The one-row module should be a real printed assemblage, not a monolithic print
that merely resembles one. The path to the actual device is a family of printed
parts that can be loaded, latched, sealed, inspected, cleaned, and reassembled
in the same order as the final system.

Hard constraint for this path:

- no metal inserts, metal screws, pins, springs, or external structural
  fasteners;
- no glue, adhesive, epoxy, solvent welding, thermal staking, permanent welds,
  or hidden bonded authority features;
- COTS microplates and COTS septum mats remain consumables, not printed parts;
- gasket and latch behavior must be represented by printed geometry, either as
  rigid print plus printed flexible gasket, or as a printed compliant feature
  where the process can actually produce it.

This makes the build harder, but cleaner: every force path, seal path, service
path, and failure path has to be visible in the printed assembly.

As of 2026-06-04, this rule is the active material-authority decision for the
one-row coupon first-print package. It supersedes the older
`2026-05-06: Printed Architecture With Authority Inserts` stance for this
coupon's mechanical assembly. COTS plates, septum mats, electronics, gaskets,
cable assemblies, and tubing remain scoped boundary parts, but they do not
bring hidden metal, glue, spring, bonded, or threaded authority into printed
coupon retention.

CAD revisions for this module are sequenced by the do-review-context hypergraph
in `docs/engineering/row_coupon_revision_hypergraph.md`. That graph keeps each
geometry change tied to review evidence and knowledge-base updates.

## Real Assemblage

The production-like module should resolve into these printed service units:

```text
top

  printed wedge locks
        |
  printed port caps / printed adapters / modeled COTS fittings
        |
  printed lid cover
        |
  printed lid-manifold shell
        |
  printed upper flexible gasket or printed compliant seal lip
        |
  replaceable round pre-slit silicone septum mats
        |
  COTS SBS glass-bottom plates
        |
  printed removable wet-chamber frame/skirt
        |
  printed lower flexible gasket or printed compliant seal lip
        |
  printed plate-support datum frame
        |
  printed deck-interface pods / slot shoes

bottom
```

The CAD should not collapse these into one printable sculpture. It should show
the actual service order and the actual removable parts.

## Assembly Order

```text
1. Install printed deck-interface pods into the OT-2 slot openings.
2. Seat the printed plate-support datum frame onto the deck pods.
3. Drop COTS plates top-down into the printed support lands and lateral
   locator rails.
4. Place the lower printed flexible gasket into its support-frame perimeter seat.
5. Lower the printed wet-chamber frame around the four plates.
6. Press COTS septum mats into each plate.
7. Place the upper printed flexible gasket onto the chamber perimeter.
8. Lower the printed lid-manifold shell.
9. Fit the printed lid cover over the manifold shell.
10. Install printed port caps, printed adapters, or modeled COTS fittings on
   the typed vertical service ports.
11. Engage printed wedge/cam/slide locks until hard-stop witnesses touch.
12. Inspect witness marks, latch positions, port caps/adapters, plate/mat
   seating, pipette access, and dry-bay clearances.
13. Run consumable metrology, puncture, leak, flow, evaporation, temperature,
   humidity, and observer-sweep checks.
```

The reverse order must be possible after humid exposure without damaging plates,
septa, the chamber frame, or the observer bay.

## Printed Locking Strategy

The print-native replacement for screws and metal inserts is not a weak snap
feature. It should be a visible compression mechanism with hard stops:

```text
lid edge
  |
  +-- printed ramp receiver
       ^
       |
printed sliding wedge / quarter-turn cam
       |
       v
base or skirt rail
```

Required properties:

- latch force is applied at the perimeter rails, not over the pipette windows;
- compression is limited by printed hard stops, not by user feel;
- latch state is visible from above;
- latches cannot interfere with OT-2 pipette access or deck adjacency;
- latches cannot overlap gas/sample/sensor ports or their service adapters;
- latches are replaceable or printable as separate sacrificial parts;
- latch travel remains outside the dry observer swept body.

For a first coupon, sliding wedges are preferable to delicate snap hooks because
their compression and witness positions are easier to measure. The installed CAD
now uses that path: printed tension posts and caps are integrated into the
wet-chamber frame, pass through the lid clearance holes, and are locked by
removable side-insert wedges retained by lid receiver rails. The current latch
detail adds a ramped wedge, high bearing flat under the post cap, low-tail
anti-lift receiver lips, insertion stops, release ears, and small detent bumps.
Raised witness stripes mark the seated latch state. This is an assembled
print-native latch, not a print-in-place captive slider.

The production scene now treats service ports the same way: a port is not only
a hole in a boss. Each vertical port is role-typed, has a printed seal land and
role witness markers, and carries a separate printed cap/plug in the installed
assembly. Future tubing, sensors, filters, and fittings must either become
filament-printable adapters or named non-filament exceptions with exact
envelopes and printed capture/seal geometry.

The wet/dry boundary follows the same rule. Dry-bay protection is not only a
hidden keepout envelope: the plate-support frame prints raised lips around each
optical aperture and includes shallow witness gutters beside those lips. Future
drains, catch volumes, shields, and observer electronics isolation must be
added as geometry or explicit non-filament exceptions, not implied by empty
space below the plates.

The current CAD includes an optional latch-mechanism demonstrator:

```bash
uv run python cad/view_one_row_coupon.py --show-latch-demo
```

That demonstrator is a separate printable mechanism section, not a
print-in-place part and not part of the installed row assembly. It shows the
preferred production direction: separate lower catch, upper receiver, sliding
wedge, hard stop, and visible witness mark. This keeps latch force, wear, and
cleaning surfaces inspectable.

The installed latch now carries M0-M3 first-print mechanical screens in the
layout data. These are not physical validation, but they make the first print
honest enough to cut parts:

- the assumptions register names the provisional print material/process,
  0.15 mm layer height, 2.0..25.0 N insertion-force range, and 1.0..15.0 N
  release-force range for the first bench protocol;
- the compression budget uses the production wedge, not the demo wedge:
  2.20 mm ramp rise, 6.40 mm ramp run, 0.45 mm tolerance allowance, and
  0.55 mm target bounded squeeze against a 0.80 mm hard-stop limit;
- the ramp self-lock check is explicit: 18.97 deg ramp angle against a
  19.29 deg friction angle at mu=0.35. The 0.32 deg positive margin is below
  the 1.0 deg desired margin, so backdrive remains a print-test risk rather
  than a closed claim;
- the post/cap/root screen assumes 8.0 N per latch, a 2.4 mm printed post,
  4.524 mm2 shaft area, 1.768 MPa nominal shaft stress, and 6.786x provisional
  safety factor against a 12 MPa wet-polymer allowable;
- the latch-station screen shows the port-driven asymmetry: 10 expected
  compression stations, 9 active wedge stations, one omitted right-side station,
  and a 181.0 mm maximum active-station span against the 100.0 mm warning
  threshold.

That means the next physical question is sharply scoped. The print has to
measure insertion force, release force, retained compression, wet backdrive,
post-cap wear, humid-cycle behavior, and leak/fog behavior. The CAD does not
claim those are solved.

## Printed Sealing Strategy

The row module needs three distinct seal interfaces:

```text
lid <-> gasket <-> wet-chamber frame
wet-chamber frame <-> base/support datum
septum mat <-> plate rim / well field
```

The CAD should represent each one separately.

For an all-printed path:

- rigid frame parts can be PETG, PC, PP, nylon, or another printable polymer
  chosen for dimensional stability and wet compatibility;
- compliant seals should be printed TPU/TPE or another printable elastomer if
  the constraint is "printed parts only";
- if a single rigid material is required, the first coupon should not claim
  gas-tight incubation, only fit, flow visibility, and gross leak behavior.

The gasket should not be a decorative flat rail. It should have:

- a capture groove or keyed seat;
- visible compression witness features;
- corner reliefs;
- controlled squeeze height;
- drainage or condensation escape logic where appropriate;
- a service tab or notch that does not compromise the seal.

## Printed Deck And Observer Strategy

The lower structure should remain modular:

```text
printed plate-support datum frame
        |
  printed vertical webs / perimeter walls outside observer sweep
        |
  printed deck pods with slot shoes
```

The current row coupon splits the lower structure into deck pods and a
plate-support frame so the print does not rely on tall thin columns supporting a
broad plate. The remaining production work is to turn that split into a
measurable printed joint with visible engagement and release states.

Rules:

- deck pods own OT-2 slot fit and click-in behavior;
- plate-support frame owns plate flatness and row straightness;
- dry observer bay owns a swept body, not just apertures;
- support webs stay outside the observer swept body;
- pod/frame joints use printed dovetails, hooks, or wedges with measurable
  witness positions;
- worn deck pods can be replaced without replacing the wet chamber or lid.

## Print Orientation

Preferred print intent:

```text
deck pods:        print upright or sideways for shoe accuracy and latch strength
support frame:    print flat, datum side up if surface finish supports plate seating
wet frame/skirt:  print flat as a frame, then inspect warp and seal-plane flatness
lid shell:        print flat enough to preserve seal and septum-seat surfaces
lid cover:        print to keep ducts, bosses, and hard-stop witnesses inspectable
gaskets:          print flat in flexible material or print as separate compliant rails
wedge locks:      print in force direction that avoids layer-splitting under compression
```

For the current latch, wedge locks should be oriented so the U-slot, ramp,
detent bumps, release ears, and witness stripes are open to inspection and do
not require hidden support removal. The wet-frame post roots and lid receiver
lips are printability gates: if a slicer requires trapped support on the post
cap underside, ramp bearing surface, or receiver capture lip, that geometry is
not ready for a coupon print.

The lid should not remain a one-piece fantasy if the ducts are meant to work.
For the real path it should become a printed manifold shell and printed cover
joined by printed locks, trapped seals, labyrinth paths, tongue-and-groove
capture, or another reversible printed seal strategy that can be inspected.

## Coupon Ladder

```text
Coupon A: printed fit stack
  - deck pods
  - support frame
  - plates
  - wet-chamber frame
  - lid shell
  - lid cover
  - printed dummy upper/lower gaskets
  Evidence: fit, service order, pipette access, observer sweep.

Coupon B: printed compression stack
  - printed flexible gasket
  - printed wedge locks
  - hard-stop witnesses
  Evidence: compression repeatability, gasket witness marks, gross leak paths.

Coupon C: passive flow stack
  - printed manifold shell and cover
  - visible supply/return lanes
  - diffuser windows
  Evidence: smoke/fog flow, liquid-surface disturbance, return balance.

Coupon D: BSL1 wet biology stack
  - same assembly order
  - same printed lock/seal architecture
  - real plates and septum mats
  Evidence: evaporation, condensation, temperature/RH/CO2 proxy sensing,
  intervention repeatability, imaging clearance.
```

Each coupon should promote only the claims it actually measures. A successful
fit stack does not prove incubation. A successful leak stack does not prove
biology. A successful passive flow stack does not prove temperature stability.

## CAD Consequences

The current CAD iteration already:

- splits the base into printed deck pods and printed plate-support frame;
- adds printed pod/frame keys and matching support-frame pockets;
- splits the lid/manifold into a printed shell and printed cover;
- adds upper and lower gasket parts as separate production service units;
- adds gasket capture grooves, service tabs, and preserved datum lands;
- adds printed wet-frame latch posts, separate printed wedge locks,
  side-oriented receiver rails, capture lips, travel stops, release tabs, and
  detent bumps with raised witness stripes;
- adds production-derived latch mechanical screening fields for compression
  budget, ramp self-lock/backdrive margin, post/cap/root stress, and omitted
  station span risk;
- adds role-typed service-port layout data, printed port seal lands, role
  markers, and separate installed printed port caps/plugs;
- adds a lid-cover tongue and shell groove for reversible cover alignment;
- adds service-state viewer modes and passive-flow adapter geometry;
- adds a compact observer front-end swept-body check.

The next CAD iteration should:

- turn the current CAD-level interfaces into physical evidence through lower
  stack, compression stack, service-state, passive-flow, and observer-kinematic
  review cycles;
- refine wedge release paths, post-cap wear, and witness positions after
  compression-force measurement;
- run the M4-M10 print-validation path: slicer support maps, production-matched
  single-station coupon, release usability, asymmetry mitigation, bench
  protocol, integrated compression stack, and full coupon print decision;
- refine shell/cover duct sealing after passive smoke/fog review;
- design the observer kinematic split between compact front end, focus axis,
  larger carriage body, and service raceway.

This is the path that keeps the coupon honest while still moving toward the
actual printable device.
