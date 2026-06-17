# Coordinate System

All generated CAD and OT-2 labware definitions must share one coordinate source.

## Fixture Coordinates

- Units: millimeters.
- `Z = 0`: bottom plane touching the OT-2 deck.
- `X`: plate columns direction.
- `Y`: plate rows direction.
- Origin: front-left/A1-style corner of the fixture base.

## Important Z Planes

- `base_top_z`: top of the printed SBS base.
- `mock_plate_top_z`: top plane of the mock raised plate.
- `well_bottom_z`: bottom of the mock wells.
- `mat_plane_z`: nominal top of the silicone mat/access plane.
- `fixture_top_z`: tallest printed collision-envelope point.

## OT-2 Registration

The fixture is loaded as custom labware in one deck slot. Opentrons labware offsets
then fine-tune the labware-in-slot location. Offsets are not a substitute for
large coordinate errors.

## Installed Pose

The generated labware definition is canonical geometry, not proof that the
physical fixture was installed in the canonical orientation. The installed
fixture pose must become an explicit bridge input before any motion-capable
path can consume target coordinates.

Minimum pose fields:

```text
slot
orientation: canonical | rot180
transform_matrix_canonical_to_installed_mm
pose_digest_sha256
evidence_handles
pose_orientation_claim
fixture_upright_claim
```

`canonical` and `rot180` are the only v1 motion-capable orientations. Adding
`rot90`, `rot270`, mirror, or any other orientation is a schema and gate
migration, not an enum-only change.

For the first printed PoC, the camera-visible installation is slot `5` with the
fixture physically rotated 180 degrees in deck yaw, while remaining upright.
The in-plane transform from canonical fixture coordinates into the installed
fixture frame is:

```text
x' = x_dimension - x
y' = y_dimension - y
z' = z
```

For the current generated dimensions, `x_dimension = 127.76 mm` and
`y_dimension = 85.48 mm`; canonical `A1 = (25.00, 25.00, 67.60)` therefore maps
to `(102.76, 60.48, 67.60)` in the installed `rot180` frame.

Do not treat labware offsets as an orientation mechanism. Offsets translate; an
installed 180-degree rotation must be represented by a pose transform and,
before robot dispatch, by a run-local oriented labware definition. Runtime
motion code must not transform target coordinates again.

The pose v1 well identity policy literal is:

```text
preserve_canonical_feature_names_v1
```

The oriented labware variant preserves physical feature identity. `A1` still
means the same printed `A1` target/fiducial/well as in canonical geometry; in a
`rot180` install, its labware coordinate is the transformed coordinate above.
It does not rename `A1` to whichever feature is physically front-left in the
deck slot.

Direction-suffixed access ports also keep canonical-frame semantics. For
example, `A1_port_x_1p5` means canonical `A1` plus `+1.5 mm` in canonical X,
then transformed once into installed labware coordinates. The name does not
mean `+1.5 mm` in deck X after a `rot180` install.

The oriented labware definition must have a distinct identity from canonical
labware, including a load-name suffix such as `_rot180`, its own checksum, and
its full load name/namespace/version tuple in the pose digest. OT-2 labware
offsets must remain small translation-only corrections bounded by the safety
profile; a large offset that attempts to compensate for orientation is a
recovery blocker.

For canonical pose, the oriented-labware identity fields are populated with the
canonical labware identity and checksum. They are never empty.

`pose_digest_sha256` is computed from a canonical JSON object containing:

```text
schema_version
slot
orientation
fixture_load_name
fixture_namespace
fixture_version
fixture_definition_sha256
oriented_labware_load_name
oriented_labware_namespace
oriented_labware_version
oriented_labware_definition_sha256
transform_matrix_canonical_to_installed_mm
well_identity_policy: preserve_canonical_feature_names_v1
```

Keys are sorted, numeric values are encoded with fixed millimeter precision, and
empty or null digest values never satisfy a motion gate. Unknown, missing, or
mismatched pose blocks target authority, offset reuse, home clearance, and all
motion.

For each well:

- `A1_center`: imaging/well-center coordinate.
- `A1_port_center`: P300 access coordinate equal to `A1_center`.
- `A1_port_x_1p0`: P300 access coordinate offset +1.0 mm in X.
- `A1_port_x_1p5`: P300 access coordinate offset +1.5 mm in X.
- `A1_port_x_2p0`: P300 access coordinate offset +2.0 mm in X.
- `A1_port_x_1p5` is the current candidate final access coordinate. The
  printed center/+1.0/+1.5/+2.0 columns are a first-print offset sweep, not a
  final multi-offset lid design.
