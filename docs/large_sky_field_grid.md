# Fixed large-sky field grid

**Status:** Count-blind field identities and partition frozen
**Date:** 2026-07-19
**Issues:** BT-005, BT-009, BT-022

## Purpose

This grid replaces the inherited file of 500 unseeded random positions. It will be
used to measure how the density of sources passing the frozen selector changes
across the sky. It is separate from the galaxy-specific comparison regions used
for primary background subtraction.

No Gaia source count, selector probability, or passing-source density was read to
generate a coordinate or choose its partition. All 500 fields remain diagnostic;
none is approved as a scientific background.

## Why there are 500 fields and why the radius is 0.8 degree

The field count and radius preserve the scope of the inherited 500-field Phase III
experiment. They are not a new statistical power calculation and do not define the
real galaxy aperture.

Every field is a 0.8-degree-radius circle. Its exact spherical area is
2.010586633 square degrees. The earlier value 2.010619 is the flat-circle formula
`pi * radius^2`; 2.0 is a further approximation. The new workflow uses the
spherical area.

## How the positions are distributed

The existing galaxy catalog covers absolute Galactic latitude `|b| >= 20` degrees,
so the grid uses that same declared domain. It places 250 centers north and 250
south of the Milky Way plane.

Latitude is spaced uniformly in spherical area, not uniformly in degrees. In plain
language, each successive latitude represents the same amount of sky even though
lines of longitude converge toward a pole. Longitude advances by the fixed
golden angle, 137.507764 degrees. This is a standard deterministic spacing that
prevents successive points from lining up; it does not introduce randomness.

The measured absolute Galactic-latitude range is 20.080258–87.060276 degrees, and
the measured absolute ecliptic-latitude range is 0.098908–87.171146 degrees. The
minimum separation between any two centers is 6.429656 degrees, so the
0.8-degree-radius circles do not overlap.

## Development and held-back validation

A **sky block** is a broad fixed part of the sky used only for splitting this
experiment. It combines one 30-degree Galactic-longitude band with one of five
equal-sky-area absolute-Galactic-latitude bands and one Galactic hemisphere. All
fields in a block remain on the same side of the split.

The five latitude bands have edges at 20.000000, 28.269284, 37.244105, 47.460216,
60.273704, and 90.000000 degrees. Within each hemisphere/latitude combination, two
sky blocks are assigned to validation. Five of the ten combinations contribute a
third validation block. Stable hashes choose both the extra combinations and the
blocks, using positions and version strings only.

The frozen split contains:

| Partition | Sky blocks | Fields | Allowed use |
|---|---:|---:|---|
| Development | 95 | 398 | Measure field conditions, fit models, and choose rules |
| Validation | 25 | 102 | Remain unopened until the development model and evaluation rules are fixed |

Both partitions contain northern and southern fields, every equal-area Galactic-
latitude band, and every fixed 15-degree absolute-ecliptic-latitude band. The
minimum development-to-validation center separation is 6.429656 degrees.

Ecliptic latitude is only a sky-position indicator related to Gaia's scanning
pattern. It does not prove that two fields have similar Gaia coverage. Observation
counts, local depth, total source density, query completion, and usable area must
be measured later. Those measurements begin with development fields only.

## Known-environment flags

The grid records whether each field intersects catalog geometry represented in the
current project:

- 142 fields intersect at least one circle with radius `2 R2t` around a represented
  Kourkchi-Tully group;
- 283 intersect at least one represented association circle with radius `R1t`;
- 47 contain the center of at least one galaxy in the 2,155-host project catalog;
  and
- 304 have one or more of these flags, while 196 have none.

These are sensitivity labels, not automatic exclusions. Earlier audits showed that
neither `2 R2t` nor `R1t` is a universal physical boundary, and excluding all
flagged fields would strongly change the sky coverage before its effect is tested.
The development analysis must report results both with the full diagnostic grid
and with declared environment-flag sensitivity subsets before any exclusion rule
is frozen.

## Validation result and artifacts

All 16 checks pass. They verify coordinate uniqueness, exact spherical area,
hemisphere and latitude coverage, whole-block partitioning, non-overlap, preserved
environment flags, absence of Gaia-count and selector columns, and unchanged host
and environment input row counts.

- `data/results/background/large_sky_field_grid_v1.csv`
- `data/results/background/large_sky_field_grid_v1.json`

Reproduce the count-blind grid without querying Gaia:

```bash
uv run python scripts/phase3_background/freeze_large_sky_field_grid.py
```
