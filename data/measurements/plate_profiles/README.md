# Plate Measurement Backlog

Published vendor dimensions are the design source for selected labware unless a
specific fit failure forces an override. The current CellVis P96-1.5H-N
reference profile is persisted in:

```text
data/measurements/plate_profiles/cellvis_p96_1p5h_n_published_profile.md
```

Use this folder only for measurements that are not available in the published
plate profile or that are needed to diagnose a physical fit issue.

Do not re-measure and promote already-published X/Y plate dimensions unless a
fixture fit failure makes the vendor profile insufficient.

The one-row coupon CAD now uses the persisted CellVis published X/Y/Z footprint,
A1 offset, 9.00 mm pitch, and published upper/lower well profile values for its
COTS plate body. The OT-2 row pitch is preserved by changing the inter-tile gap,
not by overriding the plate profile.

Optional unknowns worth measuring only after a fit, shift, seal, or binding
failure:

- top rim and gasket-land dimensions;
- A1/well-field offsets from two outside edges if a real plate shows a fit
  discrepancy;
- well opening diameters at corners and center if a real plate shows molded
  variation outside the published profile;
- underside skirt, glass/recess, and support-contact geometry;
- notes on bow, taper, raised lips, and caliper orientation.
