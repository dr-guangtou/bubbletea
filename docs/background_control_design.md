# Background control design

**Status:** Method hierarchy approved; geometry fixture validated
**Date:** 2026-07-18
**Issues:** BT-005, BT-009, BT-022; interfaces with BT-006, BT-020, and BT-021

## Purpose

The background is the expected number and spatial variation of Gaia sources that
pass the exact frozen selector but are not members of the target galaxy's compact-
stellar-system population. It is not assumed to be spatially uniform, and a missing
or unusable control measurement is never represented as zero.

## Plain-language overview

Yes: this work starts from the existing catalog of 2,155 nearby galaxies and tries
to find suitable comparison patches of sky for each galaxy.

For every galaxy, we want to compare the number of selected Gaia sources near the
galaxy with the number in one or more patches that should contain no objects
belonging to that galaxy. The comparison patches should be as similar as possible
in Milky Way foreground-star density and Gaia observing conditions. In particular,
they should be close to the same Galactic latitude as the galaxy.

This is different from the separate random-sky experiment. The random-sky
experiment deliberately samples many Galactic latitudes to measure how foreground
contamination changes across the sky. It helps us decide which galaxies can be
studied reliably and how closely a comparison patch must match its galaxy. It is
not intended to replace the galaxy-specific comparison patches.

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

- **Excluded background region:** A patch of sky that is not allowed to serve as a
  background comparison because it may contain objects belonging to the target
  galaxy, another nearby galaxy, a galaxy group, or a cluster. “Excluded” applies
  only to its use as background; sources there are not deleted from the project.

## Kourkchi-Tully catalog terms

- **Principal galaxy:** The galaxy the catalog uses as the main or brightest galaxy
  of a group. It is the group's catalog anchor, not a claim that the galaxy is the
  only scientifically important member.
- **Isolated principal:** A galaxy that the catalog treats as a one-member group:
  the galaxy is its own principal galaxy and no other cataloged galaxy was assigned
  to its group. In plain language, this is one ordinary galaxy that this particular
  catalog did not place in a multi-galaxy group. It does not prove that the galaxy
  is physically isolated or has no faint satellites.
- **`R2t`, the estimated second-turnaround radius:** A model-based estimate of the
  size of the more collapsed, gravitationally bound part of a galaxy group. The
  catalog derives it from the group's K-band luminosity and inferred mass. It is
  roughly a group-scale halo boundary, not a directly observed sharp edge.
- **`R1t`, the estimated first-turnaround radius:** A model-based estimate of the
  larger surrounding association where matter has stopped joining the general
  expansion of the Universe and is beginning to fall inward. It describes a wider
  region than the settled group core. It is also not a directly observed sharp
  edge.

The two radii answer different questions. `R2t` describes the smaller collapsed
group region; `R1t` describes a larger association around one or more groups. That
is why neither can be substituted automatically for the other.

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

All three decisions were approved by the project lead on 2026-07-18 as recommended.

## Geometry-fixture result

The synthetic, query-free fixture in
`scripts/phase3_background/validate_background_control_geometry.py` contains a
nearby isolated host, a more distant isolated host, an unresolved cluster central,
an unresolved satellite, and an isolated host with one direction contaminated by a
neighbor halo. It produces 20 symmetric control candidates at exactly matched
Galactic latitude. Eleven are accepted and nine rejected. All nine predeclared
checks pass, including explicit environment blocking, neighbor rejection with
alternative controls preserved, and a nearby exclusion radius larger than the old
two-degree cap. The maximum numerical Galactic-latitude mismatch is
`7.11e-14` degrees.

Artifacts:

- `data/results/background/background_control_geometry_fixture_v1.csv`
- `data/results/background/background_control_geometry_validation_v1.json`

The fixture inputs are synthetic geometry values, not estimates for real hosts and
not permission to infer a background before the real environment and halo-proxy
contracts are validated.

## Environment-radius audit

The Kourkchi-Tully accepted associations were tested against the catalog's own
group second-turnaround radius, `R2t`. Among 883 accepted group members, `1.5 R2t`
encloses 810 (91.73%), `2 R2t` encloses 863 (97.73%), and `3 R2t` encloses 881
(99.77%). The maximum projected ratio is 7.22. This is an internal catalog-
consistency test because both membership and `R2t` come from the same construction;
it is not independent halo validation.

The larger association first-turnaround scale, `R1t`, is also not a universal
replacement. It is usable for 832 accepted group members and encloses 763 (86.41%)
at one radius in the published association geometry. Group membership, association
membership, and physical halo exclusion must therefore remain distinct. No safety
factor is frozen.
