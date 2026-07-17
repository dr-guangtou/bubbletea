# Gaia Morphology-Galaxy Host and Control Comparison

**Date:** 2026-07-17  
**Status:** Exploratory paired comparison; no host-clustering, environment, or final
selector claim approved

## Plain-Language Question

Are Gaia-detected compact or bright-core galaxies more numerous in fields centered
on nearby galaxies than in comparable off-target fields, and how often would the two
old BubbleTea candidate-selection rules incorrectly keep them as possible UCDs?

## Predefined Field Sample

The field list was written and hashed before any Gaia outcome query. It contains 12
nearby host galaxies and one off-target control for each host.

The 12 hosts were selected from 1,163 eligible catalog rows with measured K-band
luminosity, distances of 15--25 Mpc, absolute Galactic latitude of at least 30
degrees, and a 600 kpc aperture no larger than 2.1 degrees. The eligible population
was divided into:

- low, middle, and high thirds of measured K-band luminosity; and
- absolute Galactic-latitude intervals of 30--50 and 50--90 degrees.

Two hosts were selected from each of the six cells at predefined interior positions
in the luminosity ordering. K-band luminosity is a host-mass proxy, not a direct
stellar-mass measurement.

Each control has the same angular area as its paired host field. Controls were
selected using sky geometry only: similar absolute Galactic latitude, ecliptic
latitude within two degrees, no overlap with another control, and no overlap with
the current nearby-galaxy catalog's screened apertures. Ecliptic latitude is only a
proxy for Gaia scanning behavior, so actual Gaia transit statistics were measured
afterward.

The old `is_cluster` flag was not used. It is a rough sky-circle proxy around Virgo
and Fornax, not a provenance-bearing environment measurement. Therefore this test
does not claim to be environment-stratified.

## Measured Catalog Size and Density

The 24 fields contain 9,144 unique Gaia morphology candidates in the broad
`benchmark_v1` magnitude domain:

| Field role | Fields | Candidates | Area (deg²) | Combined density (deg⁻²) |
|---|---:|---:|---:|---:|
| Host-centered | 12 | 5,224 | 123.7247 | 42.2228 |
| Paired control | 12 | 3,920 | 123.7247 | 31.6832 |

The combined host density is higher, but combining all fields hides extreme
field-to-field variation. Host density exceeds its paired control in 8 of 12 pairs.
The median paired difference is +8.2217 galaxies per square degree, but:

- the two-sided sign-test p-value is 0.3877;
- the Wilcoxon signed-rank two-sided p-value is 0.1294;
- one control contains no morphology-catalog galaxy;
- individual pair differences range from strong host deficits to strong host
  excesses.

This experiment therefore does **not** establish that Gaia morphology candidates
cluster around the selected nearby hosts. It demonstrates that catalog density is
highly spatially variable and that a larger sample plus a better characterized Gaia
morphology selection function would be needed for a population claim.

## Retention by the Two Legacy Rules

Here, “retention” means that a Gaia DR3 galaxy candidate with a successful Sersic
fit would be retained as a possible UCD candidate. It is not a pure false-positive
rate because catalog membership does not prove that every row is a background
galaxy; host-associated compact stellar systems or H II regions can in principle
enter this catalog.

| Field role | Legacy 70/30 rule | Legacy 60/30/10 rule |
|---|---:|---:|
| Host-centered | 4,468/5,224 (85.53%) | 4,464/5,224 (85.45%) |
| Paired control | 3,452/3,920 (88.06%) | 3,452/3,920 (88.06%) |

The two rules disagree for only four of 9,144 galaxies. The older color and
proper-motion additions therefore have almost no effect on this contaminant class.
This is the robust result of the experiment: both old candidate-selection rules
retain the great majority of Gaia morphology candidates, whether the field is centered
on a nearby host or placed off target.

The names refer to formula weights, not current project stages:

- **Legacy 70/30 rule:** 70% astrometric-excess-noise significance and 30% BP/RP
  flux excess, inherited from the old Phase III background work.
- **Legacy 60/30/10 rule:** 60% astrometric-excess-noise significance, 30% BP/RP
  flux excess, and 10% color, with an additional proper-motion condition, inherited
  from the old Phase IV pilot search.

Neither rule is proposed as the final Stage 3 selector.

## Gaia Scanning Comparison

Eleven pairs have morphology candidates in both fields. Across those pairs, the
median absolute host-control differences are:

- 2 matched transits;
- 1 visibility period;
- 26 good along-scan astrometric observations; and
- 0.0588 in Gaia's fourth-order scan-direction-strength statistic.

The maximum differences are larger, including 19 matched transits and 0.5565 in
scan-direction strength. Holding ecliptic latitude nearly fixed therefore reduces
but does not eliminate scan-pattern mismatch. The scan quantities must remain
explicit covariates in any larger density analysis.

## Interpretation and Limitations

- Gaia candidates with fitted compact or bright-core morphology are a serious
  retained extended-source population for the old BubbleTea rules.
- This result is not evidence that 85--88% of all astrophysical galaxies would be
  selected. The sample is conditioned on Gaia detection and a published Sersic fit.
- The catalog is not a valid UCD parent sample. Requiring a Sersic fit would exclude
  unresolved or barely resolved UCDs, and some host-field morphology candidates may
  themselves be UCDs, H II regions, nuclei, or other host-associated sources.
- The paired density result is inconclusive because spatial variation is large and
  the morphology catalog has no simple uniform all-sky selection function.
- K-band luminosity provides useful stratification but is not a direct host-mass
  measurement.
- Environment remains untested until a published group or cluster catalog supplies
  provenance-bearing membership flags.
- A geometrically screened control is not automatically an ideal statistical
  control. Actual Gaia coverage and catalog-completeness indicators must be checked.

## Reproducibility Artifacts

- Frozen design: `data/literature/validation/gaia_morphology_host_control_design.csv`
- Design manifest: `data/literature/validation/gaia_morphology_host_control_design_manifest.json`
- Design validation: `data/literature/validation/gaia_morphology_host_control_design_validation.json`
- Source associations: `data/literature/validation/gaia_morphology_host_control_sources.csv`
- Full-field summary: `data/literature/validation/gaia_morphology_host_control_field_summary.csv`
- Radial metrics: `data/literature/validation/gaia_morphology_host_control_metrics.csv`
- Statistical comparison: `data/literature/validation/gaia_morphology_host_control_comparison.json`
- Query manifest: `data/literature/validation/gaia_morphology_host_control_manifest.json`
- Analysis validation: `data/literature/validation/gaia_morphology_host_control_validation.json`
- Figure and caption: `figures/phase1/gaia_morphology_host_control_comparison.png` and `.md`

The one-field smoke run completed in 7.0 seconds. The production archive queries
required 92.57 measured seconds. The frozen design passes 14 checks and the analysis
passes 26 checks.

## Next Scientific Decision

The extended-source problem is now established as a high retained-fraction problem,
while host-centered clustering remains unproven. Before adding more host fields,
selector development should test how supplementary morphology evidence can reject
clearly extended sources without requiring morphology-catalog membership or five-
parameter astrometry.
Any later density expansion should first define a defensible morphology-catalog
selection function or use a more independent, spatially characterized galaxy sample.
