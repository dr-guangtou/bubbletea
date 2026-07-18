# Radial measurement and central exclusion design

**Status:** Count-blind geometry audited; scientific boundaries not calibrated
**Date:** 2026-07-18
**Issues:** BT-005, BT-020, BT-021

## What the real measurement does

For each nearby galaxy, the pipeline will keep every retrieved source's continuous
angular separation from the galaxy center. Using the galaxy distance, it will also
store projected separation in kiloparsecs. When a verified half-light radius,
`R50`, is available, it will additionally store separation divided by `R50`.

The pipeline will then summarize the sources in a series of concentric circular
rings. Each ring has an inner radius and an outer radius. Together, the rings form
a radial profile showing how selected-source density changes with distance from the
galaxy. The stored continuous separations allow the rings to be combined or changed
without repeating the Gaia query.

The following regions have different roles:

- **Central exclusion:** The innermost galaxy region. Its sources remain in the raw
  data and contamination summaries, but do not contribute to UCD inference.
- **Radial measurement rings:** Successive rings outside the center. Their counts,
  usable areas, and densities form the host profile.
- **Off-galaxy comparison rings:** The same angular ring shapes placed away from the
  galaxy. They estimate unrelated sources after halo and environment screening.
- **Outer retrieval boundary:** The largest radius downloaded around the galaxy.
  It must cover every requested ring and must not be silently shortened by a fixed
  angular cap.

## Exploratory ring view

The first recombinable physical-radius view uses edges at 0, 5, 10, 15, 20, 25,
30, 40, 50, 75, 100, 150, 200, 300, and 600 kpc. These values preserve the union of
the existing fine inner pilot grid and the earlier 600 kpc morphology diagnostic.
They are not an approved central exclusion, final signal range, or local-background
definition. In particular, the 0--5 kpc ring is not automatically accepted as UCD
signal.

Every output must retain exact requested area, masked area, successfully queried
area, and usable area for each ring. Areas use spherical geometry. Missing coverage
is an explicit failure or partial-area state, never a zero count over the requested
area.

## Geometry audit

The current host catalog contains 2,155 positive distances but no `R50` or
equivalent half-light-radius field. For a provisional 600 kpc outer diagnostic
radius, the measured angular radius ranges from 1.374835 to 13.064418 degrees, with
a median of 1.951086 degrees. It exceeds two degrees for 1,018 hosts, five degrees
for 123 hosts, and ten degrees for 25 hosts.

Therefore the inherited two-degree cap is invalid. Large nearby-host retrievals
will require tiled or otherwise complete archive queries with explicit coverage and
row-limit checks. The 600 kpc value remains exploratory; this audit does not approve
it as the final outer signal boundary.

The count-blind audit uses no Gaia source or selector counts and passes all seven
validation checks. Its artifacts are:

- `data/results/background/radial_measurement_geometry_audit_v1.csv`
- `data/results/background/radial_measurement_geometry_audit_v1.json`

Reproduce it with:

```bash
uv run python scripts/phase3_background/audit_radial_measurement_geometry.py
```

## Calibrating the central exclusion

The central boundary must be calibrated once for a declared host population, not
chosen separately for each galaxy after viewing its UCD excess.

The calibration will use development galaxies to measure, as a function of radius
divided by `R50`:

- the density of compact H II and star-forming-region references where available;
- the density of very blue sources and clearly extended galaxy substructure;
- source-extraction failures, bright-core masks, crowding, and missing Gaia area;
- the radial distribution and retained fraction of reliable literature UCDs; and
- sensitivity to the photometric band and uncertainty of the measured `R50`.

A candidate central boundary is acceptable only if it materially reduces central
contamination while retaining a declared fraction of reliable reference UCDs and
remaining stable on spatially separate validation galaxies. It must not be chosen
because it produces the largest target overdensity.

No central multiplier is approved now. The earlier `2 x R50` example remains only
a value to test. Until `R50` coverage is completed under BT-020, a host can retain
its physical-kpc exploratory profile but cannot receive a final normalized central
exclusion from an undocumented estimate.

## Calibrating the outer signal range

The final outer signal boundary will also be common to a declared host class rather
than optimized per galaxy. Development profiles will test where the selected-source
excess becomes consistent with the independently measured background, while
validation profiles will measure whether that boundary generalizes. Group and
cluster cases retain the same host-centered profile, but their scientific
background remains unavailable when the containing environment cannot be screened.

The final analysis may combine several rings only after the central exclusion,
outer signal boundary, background method, and handling of the resulting radial
scan have been declared.
