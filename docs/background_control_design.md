# Background control design

**Status:** Draft for project-lead review  
**Date:** 2026-07-18  
**Issues:** BT-005, BT-009, BT-022; interfaces with BT-006, BT-020, and BT-021

## Purpose

The background is the expected number and spatial variation of Gaia sources that
pass the exact frozen selector but are not members of the target galaxy's compact-
stellar-system population. It is not assumed to be spatially uniform, and a missing
or unusable control measurement is never represented as zero.

The background design has to separate three effects:

1. Milky Way source-density variation, especially with Galactic latitude;
2. Gaia sky-position completeness and measurement variation from crowding and the
   scanning law; and
3. real extragalactic structure, including other nearby-galaxy or group halos.

Cantat-Gaudin et al. model Gaia DR3 completeness as a function of magnitude and sky
position using the local `M10` diagnostic, demonstrating that Galactic latitude
alone is insufficient (`2023A&A...669A..55C`,
https://arxiv.org/abs/2208.09335). Gaia-CRF3 also shows large- and small-scale sky
inhomogeneity associated with source density, magnitude, and ecliptic latitude
(`2022A&A...667A.148G`).

## Required geometry terms

- **Signal aperture:** The host-centered region in which an excess will eventually
  be tested. Its scale and inner mask belong to BT-021 and are not fixed here.
- **Halo exclusion radius:** A conservative sky radius inside which a field cannot
  be treated as background for the host. It is derived from an upper-limit halo
  radius and a frozen safety factor.
- **Local annulus:** A host-centered annulus whose inner edge lies outside the halo
  exclusion radius. It is distinct from the old fixed 150--300 kpc annulus.
- **Off-target control aperture:** A region with the same angular shape and usable
  area as the signal aperture, displaced away from the host and all screened halos.
- **Large-field model:** A model learned from many control fields using sky and Gaia
  observing-condition predictors. It is a population-level diagnostic, not a
  substitute for missing local data unless a fallback rule is approved in advance.

## Recommended three-layer design

### Layer 1: Paired off-target controls — recommended primary

Generate multiple candidate control apertures symmetrically around each host. A
control must:

- match the signal aperture's angular geometry and magnitude/selector contract;
- lie entirely outside the host halo exclusion radius;
- satisfy predeclared tolerances in Galactic latitude, ecliptic latitude, and an
  empirical Gaia completeness or observing-condition diagnostic such as `M10`;
- avoid the buffered halos of other cataloged nearby galaxies, groups, and clusters;
- retain bright-star, crowding, missing-area, and query-truncation masks; and
- receive a permanent accepted or rejected status with a reason.

Symmetric candidates reduce the risk that one preferred direction is chosen after
seeing source counts. The number of controls and matching tolerances must be
calibrated from control-control comparisons, not selected to minimize a host's
background.

### Layer 2: Valid host-centered local annulus — robustness method

Use a host-centered annulus only when its inner edge is outside the halo exclusion
radius and its full usable area is measured. This method has the strongest local
match to Gaia and Milky Way conditions, but it can fail for nearby galaxies, large
halos, cluster environments, or neighboring systems. Failure produces an explicit
`unavailable` status, not zero density and not automatic substitution.

### Layer 3: Stratified large-field model — population diagnostic

Recompute the Phase III random-field experiment with the frozen selector and exact
areas. Stratify or model at least:

- absolute Galactic latitude;
- ecliptic latitude;
- Gaia source density or the DR3 `M10` completeness proxy;
- magnitude distribution within the frozen applicability domain; and
- masking and query-completeness indicators.

This layer measures residual sky variation, calibrates control-matching tolerances,
and supports BT-022's Galactic-latitude decision. It must use spatially separated
development and validation fields so that the model's predictive scatter is
measured out of sample.

## Halo exclusion radius

The current host table contains K-band luminosity and distance but no verified
`R50`, stellar mass, group membership, halo mass, or `R200c`. Therefore the
exclusion radius cannot yet be calculated reproducibly.

For isolated central galaxies, one feasible route is K-band luminosity to stellar
mass, then a published stellar-mass--halo-mass relation, then `R200c`, propagating
scatter and using a declared upper envelope. Moster et al. provide a fitted
stellar-to-halo relation (`2013MNRAS.428.3121M`,
https://arxiv.org/abs/1205.5807), but it is a central/subhalo population relation
rather than a precise mass measurement for an individual galaxy. A size-based
cross-check is possible after verified half-light radii exist; Kravtsov reports an
approximately linear galaxy-size--halo-radius relation with substantial scatter
(`2013ApJ...764L..31K`, https://arxiv.org/abs/1212.2980).

For satellites and brightest group or cluster galaxies, the containing environment
halo—not only the individual galaxy halo—can contaminate a control. These systems
require verified central/satellite and group/cluster information. The inherited
`is_cluster` field is not adequate because it is an undocumented sky-circle proxy.

## Area and query safeguards

- Use spherical geometry for all apertures and intersections.
- Record requested, masked, successfully queried, and usable solid angle separately.
- Do not impose a fixed angular cap that truncates a required physical region.
- Detect archive row limits and query truncation; a truncated field fails.
- Store raw retrieved sources once per sky tile and apply the shared frozen selector
  locally so target and control denominators remain identical.
- Preserve one Gaia source with multiple host/control associations rather than
  silently deduplicating it.
- Version the selector, geometry, masks, host catalog, environment catalog, and
  every control disposition in a run manifest.

## Statistical interface

BT-005 supplies background counts, usable areas, field-to-field variation, and
method differences. BT-006 must then propagate Poisson count uncertainty,
background-estimation uncertainty, and between-method disagreement. This design
does not approve the old `(observed - expected) / sqrt(expected)` diagnostic.

Negative excesses remain valid. A host with no valid background measurement remains
in the run manifest with an unavailable inferential result rather than being
discarded or assigned zero background.

## Small-scale validation before retrieval

1. Build a geometry-only fixture containing a nearby isolated host, a more distant
   isolated host, a group/cluster central, a satellite, and a host with a nearby
   contaminating galaxy.
2. Generate control candidates without querying Gaia.
3. Verify halo exclusion, constant-area matching, spherical geometry, neighbor
   screening, and explicit failure states.
4. Run bounded Gaia queries for one accepted target/control set only after the
   geometry and metadata contract pass.
5. Benchmark elapsed time, returned rows, and usable area before scaling.

## Decisions required before implementation

1. Whether paired off-target controls are the primary estimator, with the valid
   local annulus and large-field model used as robustness methods.
2. Whether unresolved group/cluster membership should block inferential background
   assignment while permitting clearly labeled exploratory profiles.
3. Whether to wait for verified `R50` and environment data, or permit a conservative
   K-luminosity--based upper `R200c` proxy for isolated centrals in the first fixture.

