# Row Coupon Passive Leak And Wet/Dry Validation

## Purpose

This protocol closes the first physical evidence loop for Gate 4 of the
one-row coupon: passive leak routing, condensate behavior, wet/dry witness
features, and protected dry optics/electronics volumes.

It validates whether the printed witness geometry makes wet failures visible
before they silently enter the dry bay, sensor pockets, harness channels, or
connector shrouds. It does not prove sterility, long-duration incubation,
powered sensor response, or biology readiness.

## CAD Review Aids

Inspect these generated artifacts before the wet run:

```text
outputs/cad/aevum_one_row_coupon_validation_dry_bay_ingress_audit_check.step
outputs/cad/aevum_one_row_coupon_validation_side_gas_leak_witness_check.step
outputs/cad/aevum_one_row_coupon_validation_sample_relief_leak_witness_check.step
outputs/cad/aevum_one_row_coupon_validation_gasket_tab_leak_witness_check.step
cad/view_one_row_coupon.py --show-validation-tools
```

The validation bodies are inspection references only. Do not install them as
production hardware.

## Measurement Record

Create the run record under:

```text
data/measurements/YYYY-MM-DD_row_coupon_passive_leak_wet_dry.md
```

Use `data/measurements/templates/row_coupon_passive_leak_wet_dry_validation.md`
as the starting record. Keep the linked first-print Gate 4 worksheet
`not_tested` until each row has measured or photo evidence.

Record at minimum:

| Item | Tool | Pass condition |
|---|---|---|
| Dry-bay protected volume | dye/photo/visual | no dye, condensate, debris, or service lead enters protected volume |
| Dry-bay ingress audit | CAD overlay/photo | no wet collector, dam, or debris bridge enters the protected footprint |
| Side-gas service witnesses | dye/photo | side fitting dye routes to visible outboard collectors |
| Sample/relief cap witness | dye/photo | cap-seat dye routes to visible edge witness |
| Gasket-tab root witnesses | dye/photo | lower/upper front/rear tab roots stay outside dry bay |
| Dry-bay aperture thresholds | visual/photo | raised collars remain unbridged by dye or support debris |
| Aperture-adjacent gutters | dye/photo | aperture-side dye stays in witness gutters and out of optics bay |
| Humid condensate exposure | humidity source/photo | condensate remains visible and outside dry electronics/optics volumes |
| Post-test dry inspection | visual/photo | dry bay, IR pockets, gas PCB pockets, SHT41 pockets, harness channels, and connector shrouds remain dry |

## Setup

Use water with visible dye before electronics or biology.

1. Assemble the printed coupon with plates, septum mats, lower and upper
   gaskets, side gas tubes or dimensional tube blanks, sensor packages or
   dimensional blanks, cable pigtails or dimensional cable blanks, lid, and
   wedge locks installed.
2. Keep electronics unpowered.
3. Photograph the dry assembled state from above, side-service edges, and the
   dry-bay observer side.
4. Confirm the Gate 4 wet/dry witness worksheet matches current CAD targets.

## Dye Challenge

1. Apply small droplets to each side gas fitting exterior and barb shoulder.
2. Apply a droplet at the sample/relief cap seat.
3. Apply droplets at lower and upper gasket-tab roots.
4. Apply droplets near optical-aperture-adjacent wet surfaces without flooding
   the dry bay.
5. Add shallow dyed water to representative plate wells under installed septum
   mats.
6. Photograph each wet collector, inboard dam, aperture threshold, and
   aperture-adjacent gutter before touching or wiping the assembly.

## Condensate Challenge

1. Hold the assembled coupon in a warm humid environment long enough to show
   first condensation behavior.
2. Photograph visible condensate paths, especially side-service exits,
   sample/relief cap area, gasket tabs, optical apertures, sensor pockets, and
   harness exits.
3. Inspect the dry bay, IR pockets, gas PCB pockets, SHT41 pockets, harness
   channels, and connector shrouds.

## Pass/Fail Boundary

Gate 4 remains blocked if any of these occur:

- dye, free water, condensate, support debris, or service lead enters the dry
  protected volume;
- any dry-bay ingress audit witness bridges from wet collector or dam geometry
  into the protected footprint;
- dye crosses an inboard dam instead of collecting at a visible witness;
- an aperture threshold is bridged by wetting or debris;
- a sensor pocket, harness channel, or connector shroud receives wetting;
- wetting is invisible until disassembly;
- a tube, cable, cap, gasket tab, or latch must be hand-held to avoid ingress.

Passing this protocol only supports the Gate 4 passive leak/wet-dry witness
claim. It does not authorize powered sensors, OT-2 motion, biology, or any CAD
change unless the first-print record identifies the measured evidence and the
specific geometry that failed or needs revision.
