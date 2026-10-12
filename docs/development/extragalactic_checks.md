# Extragalactic-catalog stress tests

**Consolidated:** 2026-10-12  
**Role:** Topic-organized development evidence, not a replacement for current scientific requirements.

[Science guide](../science_guide.md) · [Current status](../current_status.md) · [Documentation audit](documentation_audit.md)

## Current reading guidance

Gaia galaxy candidates are neither spectroscopic truth labels nor a valid UCD parent sample. These development-only checks test spatial density, historical-selector acceptance, and Sérsic-fit membership. The morphology-fit subset differs from the full galaxy-candidate catalog used by the later UCD image-reference audit.

## Dated evidence

Each section below retains an original report's scientific content, measurements,
commands, and limitations. Status statements apply to that report's original date;
read the guidance above and current SPEC before following an old next step.

<a id="record-gaia_morphology_host_field_stress"></a>

> Dated source record: `docs/gaia_morphology_host_field_stress.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/gaia_morphology_host_field_stress.md -->
## Gaia Morphology-Galaxy Host-Field Stress Test

**Date:** 2026-07-17  
**Status:** Exploratory predefined three-galaxy test sample; no selector or radial
threshold approved

### Question

Do compact or bright-core galaxies represented in Gaia occur at scientifically
relevant surface densities around nearby hosts, and how often do the two inherited
`Model C` selectors accept them?

This is a failure-mode diagnostic, not an independent selector validation. The
Gaia morphology catalog and the two legacy candidate-selection rules both use Gaia
measurements.

### Fixed Fixture

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

### Measured Results

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

### Interpretation

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

### Reproducibility

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

### Required Next Experiment

Before selector freezing, expand this design to declared environment and host-mass
strata with off-target fields matched in Galactic latitude and Gaia scanning
conditions. Preserve host and control results separately, use exact usable areas,
and choose the cohort and weighting rules without reference to selector outcomes.

The first expansion is complete and documented in
`docs/gaia_morphology_host_control_comparison.md`. It uses luminosity and Galactic-
latitude strata, not environment strata, because the existing environment flag is
not scientifically defensible. The expanded comparison confirms the high false-
selection rate but does not establish host-centered clustering.
<!-- preserved_source_end: docs/gaia_morphology_host_field_stress.md -->

<a id="record-gaia_morphology_host_control_comparison"></a>

> Dated source record: `docs/gaia_morphology_host_control_comparison.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/gaia_morphology_host_control_comparison.md -->
## Gaia Morphology-Galaxy Host and Control Comparison

**Date:** 2026-07-17  
**Status:** Exploratory paired comparison; no host-clustering, environment, or final
selector claim approved

### Plain-Language Question

Are Gaia-detected compact or bright-core galaxies more numerous in fields centered
on nearby galaxies than in comparable off-target fields, and how often would the two
old BubbleTea candidate-selection rules incorrectly keep them as possible UCDs?

### Predefined Field Sample

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

### Measured Catalog Size and Density

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

### Retention by the Two Legacy Rules

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

### Gaia Scanning Comparison

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

### Interpretation and Limitations

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

### Reproducibility Artifacts

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

### Next Scientific Decision

The extended-source problem is now established as a high retained-fraction problem,
while host-centered clustering remains unproven. Before adding more host fields,
selector development should test how supplementary morphology evidence can reject
clearly extended sources without requiring morphology-catalog membership or five-
parameter astrometry.
Any later density expansion should first define a defensible morphology-catalog
selection function or use a more independent, spatially characterized galaxy sample.
<!-- preserved_source_end: docs/gaia_morphology_host_control_comparison.md -->

<a id="record-gaia_morphology_ucd_crossmatch"></a>

> Dated source record: `docs/gaia_morphology_ucd_crossmatch.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/gaia_morphology_ucd_crossmatch.md -->
## Gaia Morphology Membership and UCD Cross-Match

**Date:** 2026-07-17  
**Status:** Development-partition measurement complete; validation partition remains blind

### Scientific Role of the Catalog

The project shorthand “Gaia morphology catalog” means the 914,837 Gaia DR3
`galaxy_candidates` sources with a published Sérsic fit (`radius_sersic IS NOT
NULL`). These are **galaxy candidates with fitted profiles**, not a uniformly
spectroscopically confirmed galaxy sample. Candidate membership can include other
compact or extended objects, potentially including UCDs and H II regions.

The catalog has two approved uses:

1. measure the sky density and Gaia-selector behavior of Gaia-detected
   extragalactic or extended-source candidates; and
2. provide supplementary morphology evidence for individual search candidates.

It must not define the parent sample for the UCD search. Requiring a successful
Sérsic fit would exclude unresolved and barely resolved UCDs for which Gaia does not
publish such a fit. The Gaia-only parent sample must be selected independently of
`galaxy_candidates` membership and Sérsic-fit availability.

### Host-Field Density Caveat

The higher combined density of morphology candidates in the 12 host fields than in
the 12 controls cannot be attributed entirely to unrelated background galaxies.
Some candidates near the hosts could be genuine host-associated compact stellar
systems, H II regions, galaxy nuclei, or other extended sources. Together with the
inconclusive paired statistics and the catalog's non-uniform selection function,
this prevents interpreting the measured density difference as either a background-
galaxy clustering signal or a UCD overdensity.

The defensible quantity is the density of **Gaia DR3 galaxy candidates with
successful Sérsic fits**, conditional on the Gaia detection and morphology
pipelines.

### Blind-Safe Exact Cross-Match

The exact Gaia DR3 source-ID cross-match was restricted to the benchmark development
partition. The 721 validation rows, including 24 confirmed UCDs, remain uninspected
until the Gaia-only selector and morphology-use policy are frozen.

| Development cohort | Tested | Sérsic-catalog matches |
|---|---:|---:|
| High-confidence confirmed UCDs | 175 | 0 |
| Uncertain literature UCD candidates | 569 | 1 |
| PHANGS and dwarf-host H II regions | 127 | 0 |
| Clean SDSS spectroscopic galaxies | 638 | 75 |

The absence of confirmed-UCD matches in the development partition supports the
decision not to require morphology-catalog membership. It does not establish zero
coverage for all confirmed UCDs because the 24 validation UCDs remain blind.

The one matched literature UCD candidate is
`canonical_fc98f8ba01545cc0a4e7ae8663ccdedb` (Gaia DR3
`6088221630780081536`). It has `radius_sersic = 2601.639 mas`, `n_sersic =
3.7763`, and `flags_sersic = 6`, meaning an elliptical profile was reported as
well fitted. This is useful galaxy-like evidence for reviewing that uncertain
candidate, but one candidate and zero confirmed matches cannot calibrate a Sérsic
rejection threshold.

### Interpreting the Sérsic Parameters

- `radius_sersic` is the fitted major-axis effective radius in milliarcseconds.
  A clearly large angular radius can support rejection of an object expected to be
  unresolved at its host distance, but it must be interpreted with its uncertainty,
  quality flag, magnitude, Gaia windowing, and the host-distance hypothesis.
- `n_sersic` measures profile concentration. A high value is not, by itself, proof
  of contamination: compact spheroids and bright galaxy cores can have concentrated
  profiles, and Gaia often measures only a galaxy's inner region.
- `flags_sersic` records fit configuration and quality. Values 6 and 8 are the
  well-fitted elliptical and circular cases; other values can indicate nearby-source
  interference, failed convergence, or parameters reaching fit-domain limits.

No hard cut on radius or Sérsic index is approved. The next calibration must compare
these parameters with independent, higher-resolution optical or space-based image
modeling. That imaging can ultimately distinguish unresolved or barely resolved UCDs
from background galaxies, bright nuclei, and other extended contaminants, but it
remains value-added validation rather than a requirement for Gaia statistical-sample
membership.

### Reproducibility

- Script: `scripts/phase1_literature/crossmatch_gaia_morphology_benchmark.py`
- Command: `BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python scripts/phase1_literature/crossmatch_gaia_morphology_benchmark.py`
- Cross-match rows: `data/literature/validation/gaia_morphology_benchmark_crossmatch.csv`
- Manifest: `data/literature/validation/gaia_morphology_benchmark_crossmatch_manifest.json`
- Validator: `scripts/phase1_literature/validate_gaia_morphology_benchmark_crossmatch.py`
- Validation: `data/literature/validation/gaia_morphology_benchmark_crossmatch_validation.json`

Primary references are Gaia Collaboration, *Gaia Data Release 3: The extragalactic
content*, `2023A&A...674A..41G`, DOI `10.1051/0004-6361/202243232`, and Ducourant
et al., *Gaia Data Release 3: Surface brightness profiles of galaxies and host
galaxies of quasars*, `2023A&A...674A..11D`, DOI
`10.1051/0004-6361/202243798`.
<!-- preserved_source_end: docs/gaia_morphology_ucd_crossmatch.md -->


