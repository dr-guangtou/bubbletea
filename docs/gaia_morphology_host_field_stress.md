# Gaia Morphology-Galaxy Host-Field Stress Test

**Date:** 2026-07-17  
**Status:** Exploratory predefined three-galaxy test sample; no selector or radial
threshold approved

## Question

Do compact or bright-core galaxies represented in Gaia occur at scientifically
relevant surface densities around nearby hosts, and how often do the two inherited
`Model C` selectors accept them?

This is a failure-mode diagnostic, not an independent selector validation. The
Gaia morphology catalog and the two legacy candidate-selection rules both use Gaia
measurements.

## Fixed Fixture

Before querying outcomes, the test selected the first three ranked current host
rows satisfying all of the following:

- absolute Galactic latitude at least 30 degrees;
- distance between 15 and 25 Mpc, inclusive;
- 600 kpc angular radius no larger than 2.1 degrees.

The selected hosts are NGC 1316, M49, and NGC 2974. Every Gaia DR3
`galaxy_candidates` source with `radius_sersic IS NOT NULL` was retrieved out to
600 kpc by joining the morphology table to `gaiadr3.gaia_source`. No selector
feature, magnitude, astrometry, or color prefilter was applied at the archive.

The declared physical annuli are `[0, 25, 50, 100, 150, 300, 600]` kpc. The
300--600 kpc annulus is only a local comparison region; it is not asserted to be
free of host, group, or cluster galaxies.

## Measured Results

| Host | Morphology galaxies | Legacy 70/30 rule falsely selected | Legacy 60/30/10 rule falsely selected | PM/RUWE coverage |
|---|---:|---:|---:|---:|
| NGC 1316 | 395 | 316 (80.0%) | 316 (80.0%) | 19.5% |
| M49 | 285 | 276 (96.8%) | 276 (96.8%) | 2.8% |
| NGC 2974 | 134 | 122 (91.0%) | 122 (91.0%) | 9.0% |
| Combined | 814 | 714 (87.7%) | 714 (87.7%) | 11.9% |

All 814 rows fall inside the broad `benchmark_v1` Gaia-magnitude applicability
domain. Astrometric excess noise, its significance, and both IPD percentages are
present for every row; BP/RP flux excess is present for 99.9%. RUWE and the
covariance-aware proper-motion zero-significance are present for only 11.9%.

The two legacy rules make identical decisions on every morphology candidate in this
test sample. “Selected” means retained as a possible UCD candidate despite a
successful Gaia galaxy-candidate Sersic fit; candidate membership does not prove
that every row is a background galaxy. The rules' different weighting and color
term therefore do not address
this failure mode. Their 87.7% combined acceptance is much higher than their roughly
55% acceptance of the small SDSS galaxy benchmark cohort. That contrast is not a
population estimate: the morphology sample is deliberately Gaia-selected and
conditioned on successful Sersic fitting.

Across all three hosts, 164 morphology candidates occupy 7.5363 square degrees inside
300 kpc, or 21.7614 per square degree. The 300--600 kpc annuli contain 650 across
22.5914 square degrees, or 28.7721 per square degree. The individual profiles are
sparse and heterogeneous. This test therefore does **not** establish a central
candidate-density enhancement. It does establish that Gaia morphology candidates have a
non-negligible absolute density and that the inherited selectors reject very few
of them.

## Interpretation

- The user's concern is confirmed as a selector-contamination problem: compact or
  core-dominated Gaia galaxies readily satisfy both inherited selections.
- The small test sample does not confirm that these sources cluster toward host centers.
  A larger, environment-stratified host/control experiment is required for that
  population claim.
- Missing five-parameter astrometry is part of the failure mode. A selector cannot
  rely on proper motion or RUWE without discarding most morphology candidates and a
  large fraction of confirmed UCDs.
- The legacy 70/30 and 60/30/10 rules remain rejected comparison baselines, not
  candidates for the final selector. They came from the old Phase III background
  analysis and Phase IV pilot search, respectively; those historical project phases
  are distinct from Stage 3 of the current scientific-validation plan.
- Archive-side selector prefilters must remain prohibited in contaminant audits;
  applying them before retrieval would erase rejected objects and bias acceptance.

## Reproducibility

- Script: `scripts/phase1_literature/analyze_gaia_morphology_host_fields.py`
- Validator: `scripts/phase1_literature/validate_gaia_morphology_host_fields.py`
- Source associations: `data/literature/validation/gaia_morphology_host_field_sources.csv`
- Radial metrics: `data/literature/validation/gaia_morphology_host_field_radial_metrics.csv`
- Manifest: `data/literature/validation/gaia_morphology_host_field_manifest.json`
- Validation: `data/literature/validation/gaia_morphology_host_field_validation.json`
- Figure: `figures/phase1/gaia_morphology_host_field_stress.png`
- Caption: `figures/phase1/gaia_morphology_host_field_stress.md`

The measured smoke run used one host and 100 kpc, returning 10 rows in 4.21 seconds
and completing end-to-end in 6.8 seconds. The production query returned 814
host-source associations with approximately 12 seconds of measured archive time.
All 25 production validation checks pass.

## Required Next Experiment

Before selector freezing, expand this design to declared environment and host-mass
strata with off-target fields matched in Galactic latitude and Gaia scanning
conditions. Preserve host and control results separately, use exact usable areas,
and choose the cohort and weighting rules without reference to selector outcomes.

The first expansion is complete and documented in
`docs/gaia_morphology_host_control_comparison.md`. It uses luminosity and Galactic-
latitude strata, not environment strata, because the existing environment flag is
not scientifically defensible. The expanded comparison confirms the high false-
selection rate but does not establish host-centered clustering.
