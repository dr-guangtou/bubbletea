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
in Milky Way foreground-star density and in how completely and repeatedly Gaia
observed the sky. In particular, they should be close to the same Galactic latitude
as the galaxy.

This is different from the separate random-sky experiment. The random-sky
experiment deliberately samples many Galactic latitudes to measure how foreground
contamination changes across the sky. It helps us decide which galaxies can be
studied reliably and how closely a comparison patch must match its galaxy. It is
not intended to replace the galaxy-specific comparison patches.

In this design, a **galaxy-centered region** is a circle or annulus centered on the
nearby galaxy being studied. A **comparison region** is an equal-area region moved
away from that galaxy and used to estimate unrelated sources. A region described
as **diagnostic-only** is measured to test the method but is not approved for the
final background subtraction. When an environment is unresolved, the workflow
does not generate comparison coordinates from an unverified group center or size;
earlier summaries referred to avoiding such coordinates as “no invented
comparison.”

Counts explicitly described as **before selection** contain Gaia DR3 catalog
entries in the stated magnitude range before any UCD classifier or contaminant
removal is applied. They are not the sources that survive the point-source, binary,
QSO, or other contaminant filters. Counts after the frozen selector is applied will
always be labeled separately as selected-source or UCD-candidate counts.

## What “similar Gaia observing conditions” means

Gaia is above Earth's atmosphere, so this phrase does not refer to weather. Gaia
scanned different sky positions a different number of times and at different scan
angles. Source crowding also changes whether Gaia detects a source and whether it
publishes a complete astrometric solution. Consequently, two equal-area patches can
produce different selected-source counts even when their true populations are
otherwise similar.

For this project, a galaxy patch and its comparison patch should be checked using
measured field-level quantities that do not use the UCD selector's output:

- **Ecliptic latitude:** a simple sky-position indicator related to Gaia's scanning
  pattern. It is a diagnostic, not a complete description of the scan history.
- **Gaia `M10` completeness indicator:** the median G magnitude of Gaia sources with
  no more than ten matched astrometric transits in a small sky patch. A brighter
  `M10` generally indicates shallower or less complete Gaia coverage.
- **Observation-count distributions:** quantities such as the number of visibility
  periods and matched astrometric transits, which describe how often sources in the
  patch contributed to Gaia measurements.
- **Total Gaia source density:** a crowding indicator measured before applying the
  frozen UCD selector.
- **Query and usable-area status:** whether the archive query completed without row
  truncation and how much of the requested patch has verified completed retrieval.

Galactic latitude is related but separate: it primarily tracks how many Milky Way
foreground stars lie in the direction of the patch. Dust and bright-star conditions
may be recorded as diagnostics, but they do not remove area from the Gaia
measurement.

The exact matching tolerances for these quantities have not been chosen. They must
be measured from comparison-patch pairs without looking for the values that produce
the largest galaxy overdensity. We also must test which diagnostics materially
predict the density of sources passing the frozen selector; a diagnostic that adds
no measured predictive value need not become a matching requirement.

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

- **Galaxy-centered radial profile:** Counts and usable areas measured in a series
  of concentric circular rings around the galaxy. The real measurement preserves
  this profile rather than returning only one number.
- **Central exclusion region:** The inner circular part of the galaxy omitted from
  UCD inference because galaxy substructure, compact star-forming regions, H II
  regions, and source-extraction artifacts can dominate it. Its calibrated size
  belongs to BT-021 and is not fixed here.
- **Signal region:** The set of radial rings outside the central exclusion that may
  eventually be combined for an excess measurement. Its outer scale belongs to
  BT-021 and is not fixed here.
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
  empirical Gaia completeness indicator such as `M10`;
- avoid the buffered halos of other cataloged nearby galaxies, groups, and clusters;
- retain crowding diagnostics and explicit missing-area or query-truncation states;
  and
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

## Bounded Gaia field-condition result

A first live-archive benchmark used NGC 4698 and two 0.1-degree-radius comparison
patches with exactly the same Galactic latitude. It deliberately did not apply or
inspect the UCD selector. The target, west, and east patches contained 121, 100,
and 122 Gaia sources in the allowed G magnitude range. Their average numbers of
visibility periods were 15.98, 12.07, and 14.46, while their `M10` values—the median
G magnitude of sources with no more than ten matched astrometric transits—were
21.187, 21.093, and 21.102.

All six validation checks passed, including complete retrieval, non-missing
observation counts, positive area, and a query contract containing no selector
output. The measured run took 11.19 seconds. Same Galactic latitude therefore did
not guarantee identical Gaia coverage or source density in this bounded test. One
target and two comparisons are insufficient to choose diagnostics or matching
tolerances, so no scientific rule is frozen. Full definitions, measurements, and
limitations are recorded in `docs/background_field_conditions_benchmark.md`.

The 0.1-degree radius was chosen only to keep this first archive query small and
quick. It is not a host-measurement recommendation. At the measured catalog
distances, 0.1 degree corresponds to a projected radius of 4.712394 kpc for
ESO 006-G001 but 41.771283 kpc for NGC 4698. A fixed angle therefore cannot provide
the planned comparable radial profile across nearby galaxies.

The follow-up count-blind audit covers all 2,155 hosts and preserves an exploratory,
recombinable physical-ring view rather than one fixed circular count. A provisional
600 kpc diagnostic radius exceeds two degrees for 1,018 hosts and reaches
13.064418 degrees, so complete retrieval may require multiple archive tiles. The
current host table has no `R50` field; the central exclusion and normalized radial
profile therefore remain uncalibrated. The complete measurement contract is in
`docs/radial_measurement_design.md`.

For large circular regions, the validated query partition uses non-overlapping
declination ranges while retaining the exact original circle in every archive
request. One bounded NGC 4698 test reconstructed the complete query's 500 unique
Gaia identifiers exactly from four ranges, with all nine checks passing. Production
queries still require row-count-based splitting, checkpoints, and resume behavior;
see `docs/gaia_query_partition_validation.md`.

The follow-up restart test now measures row counts, recursively splits oversized
ranges, writes atomic checkpoints, and resumes from verified files. It stopped after
two of six strips, reused those two on restart, completed the remaining four, and
replaced one deliberately damaged strip without repeating five valid downloads.
All 15 checks pass. At that stage, the full-column row limit and masked radial-ring
areas had not yet been validated; see `docs/gaia_adaptive_retrieval_validation.md`.

The subsequent 19-column benchmark succeeded through 10,000 rows. Three repeated
5,000-row queries returned identical identifiers in 1.948628--1.976649 seconds and
produced 1,027,468 serialized bytes each. That benchmark set 5,000 rows as the
provisional development checkpoint limit. It is not an archive maximum; see
`docs/gaia_full_selector_retrieval_benchmark.md`.

The three-field full-column restart validation measures 2,991 rows for NGC 4698,
6,497 for M60, and 13,010 for ESO 006-G001, producing one, two, and four final
strips. Both split fields resume from a verified saved strip, every combined source-
identifier hash matches an independent reference, and all 13 checks pass. Freeze
5,000 rows per strip for development and pilot runs under the current 19-column
contract; see `docs/gaia_full_column_multifield_validation.md`.

The radial-area component now distinguishes the entire requested ring, the part
covered by verified completed retrieval strips, the missing part, the union of
explicit unusable masks, and the remaining usable area. Complete retrieval plans
for the three performance fields reproduce their spherical requested areas, while
a controlled interrupted state retains positive missing area. Two overlapping
synthetic masks are subtracted once, and all 18 checks pass. The Gaia-specific path
applies no bright-star, dust, or ancillary-imaging masks: usable area equals
successfully queried area. Synthetic masks test only the generic geometry code. See
`docs/radial_ring_area_accounting.md`.

Each processed galaxy can now retain a permanent analysis receipt containing its
configuration fingerprint, completed strips, source checks, ring areas, and any
failure in plain language. Identical content is reused, while different content is
refused rather than overwriting an earlier receipt. Three completed performance
fields and one controlled partial M60 case pass all 18 checks; see
`docs/host_run_records.md`.

The first selector experiment now has a frozen count-blind field split. Four
off-target circles around NGC 4698 and NGC 1316 are development fields, where method
choices may be made. Four circles around ESO 006-G001 and M60 are held back for
validation. East and west circles from one host remain together, and each partition
contains isolated/grouped and positive/negative-latitude cases. The assignment does
not read Gaia counts or selector outputs, all 14 checks pass, and no circle is
promoted to a scientific background. See `docs/off_target_field_split.md`.

The four development circles have now been retrieved with all 19 Gaia inputs and
scored locally with the frozen selector. They contain 413 Gaia sources; 44 pass the
threshold, with field-level counts of 18, 8, 12, and 6. These are retained search
candidates, not confirmed UCDs. All 18 checks pass, and the four validation field
identifiers are absent from every selector query and output. See
`docs/off_target_development_selector.md`.

The development summary procedure is now fixed before validation. It retains every
field, combines east and west only within the same host, and reports exact 68% and
95% ranges for random small-count variation. The all-development density of
350.140964 per square degree is descriptive only. These counting ranges do not
include real field-to-field variation or observing-condition effects. All 16 checks
pass, the selector threshold is unchanged, and validation remains absent. See
`docs/off_target_development_summary.md`.

The four held-back fields were subsequently opened once under the unchanged
procedure. Fifty-two of 1,233 Gaia sources pass over 0.125664 square degree, giving
a descriptive density of 413.802957 per square degree. This is 1.181818 times the
development value and lies inside its 95%, but not 68%, counting-only range. Field
and related-host-pair density ranges overlap across partitions. All 24 safeguards
pass. The comparison supports continued use of the procedure for a larger
calibration experiment, but the eight small circles remain diagnostic and cannot
define or approve scientific backgrounds. See `docs/off_target_validation_selector.md`.

The large-sky calibration coordinates are now frozen independently of Gaia counts.
Five hundred deterministic 0.8-degree-radius fields replace the inherited unseeded
random coordinates, with 250 in each Galactic hemisphere over `|b| >= 20` degrees.
Broad count-blind sky blocks produce 398 development and 102 held-back fields; both
partitions cover every declared Galactic- and ecliptic-latitude band. The minimum
field-center separation is 6.429656 degrees, and all 16 checks pass. Intersections
with represented groups, associations, and project hosts remain sensitivity flags,
not exclusions or scientific-background approvals. See
`docs/large_sky_field_grid.md`.

The frozen 12-field development retrieval pilot is also complete. The low-latitude
performance field contains 84,025 Gaia sources and required 26 verified strips;
controlled stop and resume passed all 18 safeguards. Across the pilot, 11,583 of
275,404 sources pass the selector over 24.127040 square degrees. Field densities
span 239.233660–708.748370 per square degree, so the next development step must
measure Gaia field conditions before fitting a larger sky model. The 102 validation
fields remain unopened. See `docs/large_sky_development_retrieval.md`.

Pre-selector conditions are now measured in the same 12 development fields. Total
Gaia source density spans 2,874.285496--41,791.285489 per square degree, mean
visibility periods span 12.437076--24.246461, mean matched transits span
19.192643--56.199413, and M10 spans G = 20.894909--21.158578. All 12 safeguards
pass. These fields establish useful predictor range but are too few and were not
sampled to choose predictors from their correlations. See
`docs/large_sky_development_field_conditions.md`.

The comparison was frozen before development scale-up as contract
`model_contract_8da80ba5e4bd6d3027e6`. It compares five eligible models of increasing
complexity and one environment-flag sensitivity model. Whole broad sky blocks stay
together in the five prediction tests, while four internal splits choose only the
already declared settings. The simplest model statistically consistent with the
best prediction score will be selected. All 13 safeguards pass; no model is fitted,
no validation result is opened, and no field is scientifically approved. See
`docs/large_sky_model_comparison_contract.md`.

The fixed G-magnitude summaries were first calculated locally for all 12 pilot
fields with nine safeguards passing and no archive query. The resumable
continuation then completed all 398 development fields: 8,001,113 Gaia sources,
403,920 passing sources, 2,356 final strips, and 800.213480 square degrees. The
dense final field demonstrated that both planning measurements and source strips
can be saved and resumed across bounded attempts. All 17 run safeguards pass, all
102 validation fields remain unopened, and no background model is fitted. See
`docs/large_sky_development_scale.md`.

## Five-host field-condition result

The same pre-selector measurements were extended to five review hosts using 13
frozen patches. Four resolved environments received east and west test patches;
Arp 244 received only a target measurement because its environment association is
unresolved. All nine validation checks pass, and the measured run took 46.93
seconds. No test patch is approved as a scientific background.

The one-galaxy catalog cases have `M10` ranges of 0.094 and 0.105 magnitude across
their three patches. The NGC 1316 and M60 group cases have larger ranges of 0.503
and 0.498 magnitude. M60 also illustrates that total Gaia density is not a pure
survey-condition measurement: its target patch contains 289 Gaia sources in the
allowed magnitude range, compared with 59 and 130 in the two diagnostic patches.
Some of the target excess may be a real M60 or Virgo population. Total Gaia density
may therefore diagnose crowding, but it must not be matched so rigidly that a real
host-associated population is treated as a field-quality failure. Full definitions
and results are in `docs/background_review_field_conditions.md`.
