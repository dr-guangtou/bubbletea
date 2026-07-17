# Contaminant Benchmark Definitions and Limitations

**Status:** Permanent definition record for `benchmark_v1`
**Date:** 2026-07-16
**Benchmark:** `data/literature/benchmarks/gaia_validation_benchmark_v1.csv`
**Source registry:** `data/literature/sources/validation_benchmark_sources.json`

## Purpose and Meaning of “Contaminant”

In this project, a contaminant is a Gaia source that is not a primary UCD target
but could be selected by a Gaia-only compact-extended-source rule. The word does
not mean that the source is spurious, scientifically uninteresting, or incorrectly
classified by its source publication.

The benchmark is a collection of deliberately different failure modes. Its raw
cohort proportions are not estimates of contaminant prevalence in a real Gaia
host search. Overall accuracy, purity, or pooled AUC must therefore not be used as
population quantities without an explicit weighting model. Every selector result
must also be reported by contaminant cohort.

All external cohorts are restricted to the observed Gaia `G`-magnitude span of
the literature reference sample, 11.262918 to 21.757988 mag. The fixed spatial
partition prevents nearby Gaia sources from crossing development and validation
data. One benchmark row represents one unique Gaia DR3 source.

## Cohort Summary

| Label subtype | Source | Total | Development | Validation | Confidence | Intended failure mode |
|---|---|---:|---:|---:|---|---|
| `spectroscopic_galaxy` | SDSS DR16 spectroscopy | 805 | 638 | 167 | High | Gaia-detected galaxies and compact/nuclear galaxy light |
| `spectroscopic_qso` | SDSS DR16 spectroscopy | 491 | 403 | 88 | High | Extragalactic point-like or marginally resolved AGN |
| `gaia_non_single_star` | Gaia DR3 NSS | 1,412 | 1,125 | 287 | High | Binary and multiple-star astrometric or spectroscopic failure modes |
| `compact_hii_region` | PHANGS-MUSE nebulae | 175 | 118 | 57 | Moderate | Star-forming nebulae in nearby spiral disks |
| `dwarf_galaxy_hii_region` | van Zee et al. dwarf-irregular spectroscopy | 12 | 9 | 3 | Moderate | Star-forming nebulae in dwarf-galaxy environments |
| `reported_non_ucd_comparison` | Stabilized UCD literature database | 122 | 82 | 40 | Moderate | Source-reported non-UCD compact-system comparisons |

## SDSS DR16 Spectroscopic Galaxies

**Source:** Ahumada et al. 2020, bibcode `2020ApJS..249....3A`, DOI
`10.3847/1538-4365/ab929e`, accessed through the NOIRLab Data Lab tables and the
precomputed Gaia DR3–SDSS DR16 1.5-arcsecond cross-match.

**Definition:**

- SDSS `specObj` class exactly `GALAXY`;
- `scienceprimary = 1`;
- `zwarning = 0`;
- SDSS `random_id` in the deterministic interval `[0.0, 0.1)` on its measured
  0--100 domain, hence a 0.1% engineering slice;
- Gaia `G` within the benchmark magnitude domain;
- nearest unique Gaia–SDSS pair retained after removing Gaia sources linked to
  conflicting SDSS spectral classes;
- one row per SDSS spectrum and one row per Gaia source.

**Why included:** A Gaia-based extendedness selector can accept compact galaxies,
galaxy nuclei, or blended galaxy light. The Gaia cross-match itself preferentially
selects galaxies with a Gaia-detectable compact component, making the cohort
relevant to this failure mode.

**Limitations and possible bias:** This is not a representative galaxy census.
It inherits the SDSS spectroscopic targeting function, footprint, redshift and
surface-brightness limits, and the requirement that the object have a Gaia match.
It mixes galaxy morphologies and does not currently isolate compact galaxies.
The deterministic 0.1% `random_id` slice controls size but does not remove those
survey-selection effects. It must be evaluated separately rather than allowed to
dominate a pooled negative class.

## SDSS DR16 Spectroscopic QSOs

**Source:** The same SDSS DR16 release, quality rules, deterministic `random_id`
slice, magnitude domain, and Gaia cross-match as the galaxy cohort, with SDSS
class exactly `QSO`.

**Why included:** QSOs test an extragalactic source class that is often point-like
in ground-based imaging but can acquire Gaia astrometric or photometric anomalies.
They are a useful check that an extendedness rule does not simply select any
extragalactic source.

**Limitations and possible bias:** This cohort inherits SDSS QSO targeting,
footprint, color, magnitude, and redshift selection and requires a Gaia match. It
is not a sky-matched sample of all AGN and is not an estimate of the QSO density
around nearby galaxies.

## Gaia DR3 Non-Single Stars (NSS)

**Source:** Gaia Collaboration 2023, bibcode `2023A&A...674A..34G`, DOI
`10.1051/0004-6361/202243782`, VizieR catalog `I/357`.

**Definition:**

- exact Gaia source identifiers from 17 Gaia DR3 NSS solution tables;
- the published `NSSmodel` and source-table name are retained for every row;
- deterministic systematic sample satisfying `MOD(recno, 500) = 1` in each
  table;
- joined to the Gaia DR3 main table and restricted to the benchmark magnitude
  domain;
- duplicate source identifiers across NSS tables consolidated to one row.

**What NSS means:** NSS is Gaia's “non-single-star” solution collection. These
sources have Gaia evidence requiring a binary or multiple-system solution rather
than the ordinary single-source astrometric model. They are included because
orbital motion, multiplicity, and difficult image fits can produce excess noise,
high RUWE, or other signals that resemble source extension.

**Limitations and possible bias:** NSS is not a sample of ordinary stars and is
not a complete sample of binaries. It is conditioned on Gaia having published an
NSS solution. The systematic `recno` subsample is reproducible but is not asserted
to be statistically random in sky position or solution type. The Gaia
`non_single_star` flag is tautological for this cohort and cannot be counted as
independent evidence that a selector works. A separate clean single-star control
is still required before selector freezing.

## PHANGS-MUSE Spiral-Host H II Regions

**Source:** Groves et al. 2023, bibcode `2023MNRAS.520.4902G`, DOI
`10.1093/mnras/stad114`, VizieR table `J/MNRAS/520/4902/catalog`.

**Nebular definition:**

- `FlagEdge = 0` and `FlagStar = 0`;
- all three published BPT classifications (`NII`, `SII`, and `OI`) equal star
  formation;
- 20,577 qualifying nebular positions across 19 PHANGS spiral-galaxy fields were
  audited against Gaia.

**Gaia association:** Eight displaced controls at plus or minus 30 and 60
arcseconds in right ascension and declination were measured over the full
0.1–5.0-arcsecond separation curve. The approved 0.3-arcsecond radius yields 175
associations to 175 unique Gaia sources. The controls predict 13.25 chance matches,
for a measured association-level excess fraction of 0.9243. These labels are
therefore moderate confidence and removable as a cohort-level sensitivity test.

**Why included:** Compact or blended star-forming nebulae in a host disk can look
extended to Gaia and are spatially correlated with the galaxies being searched.
They are more dangerous than a uniform background contaminant because they can
create a false central overdensity.

**Limitations and possible bias:** The cohort represents Gaia-detected PHANGS
nebulae in nearby spiral disks, not all H II regions. It is conditioned on clean
three-diagram BPT classification, PHANGS target selection, local crowding, and a
Gaia association. It does not represent dwarf-host metallicities or coordinate
precision, and approximately 7.6% of the accepted association count is predicted
from displaced controls.

## van Zee Dwarf-Host H II Regions

**Source:** van Zee et al. 2006, bibcode `2006ApJ...636..214V`, DOI
`10.1086/498017`, VizieR table `J/ApJ/636/214/table3`.

**Meaning of “dwarf-host”:** This is an environmental source-cohort label, not a
new physical H II classification and not a statement that each nebula is itself
dwarf-sized. The H II spectra were obtained in 21 isolated dwarf irregular host
galaxies. The label records that their metallicity, stellar population, surface
brightness, crowding, and host environment may differ systematically from the
PHANGS spiral fields.

**Nebular definition:** Object-level long-slit H II-region spectroscopy from the
published table. Repeated spectra at identical derived positions are consolidated
while all source-row numbers and slit measurements are retained. This produces 63
unique published positions.

**Gaia association:** The catalog positions are constructed from published galaxy
centers and integer-arcsecond slit offsets, so the PHANGS 0.3-arcsecond radius is
not transferable. A separate eight-control separation audit approves a
3.0-arcsecond radius: 13 associations, 12 unique Gaia sources, one repeated Gaia
assignment, and one expected control association. The measured association-level
excess fraction is 0.9231. Both UGC 3647 slit rows selecting the repeated Gaia
source are preserved in its row-level provenance.

**Why it remains separate from PHANGS:**

1. The host population is dwarf irregular rather than spiral.
2. The nebular spectroscopy and source-selection functions differ.
3. The coordinate construction and approved Gaia radius differ by a factor of ten.
4. The chance-association calibration is source-specific.
5. Keeping the cohort separate permits an explicit test of environmental and
   association-systematic sensitivity.

**Limitations and possible bias:** The Gaia-matched sample is small, with only 12
unique sources, and the coordinate uncertainty is much larger than for PHANGS.
It must not be given equal statistical weight merely because it is a separate
cohort, and its nine development rows cannot define a precise universal color
cut by themselves.

## Source-Reported Non-UCD Comparisons

**Source:** `ucd_reference_v2`, which preserves the original publication,
dataset, source-row locator, reported role, and canonical association for every
literature record.

**Definition:** Gaia-linked canonical objects whose stabilized classification is
`rejected`, meaning the contributing source material reports them as non-UCD
comparisons and no approved positive confirmation overrides that role. The
benchmark retains 122 unique Gaia sources.

**Why included:** These are difficult, literature-adjacent negatives such as
compact-system comparisons near the scientific UCD boundary. They test a more
relevant distinction than generic galaxies or stars alone.

**Limitations and possible bias:** This is deliberately heterogeneous and depends
on author-specific UCD/GC definitions, host environments, and source targeting.
It is moderate confidence and is not relabeled as one physical contaminant class.
Some objects may be ordinary compact stellar systems that are difficult to
separate from UCDs using Gaia alone.

## Bias-Control Rules for Selector Development

1. Report performance separately for every contaminant subtype.
2. Do not interpret benchmark cohort fractions as astrophysical priors or use raw
   pooled purity as a survey prediction.
3. Preserve the fixed development/validation partition and do not tune on
   validation labels.
4. Report feature coverage and null behavior separately for each cohort.
5. Treat the two H II cohorts as removable sensitivity groups.
6. Do not use source-defining fields such as `non_single_star` as independent
   evidence of general selector performance.
7. Measure performance versus magnitude and sky/environment where coverage permits.
8. Freeze thresholds only after documenting how cohort weighting or multi-cohort
   constraints are chosen.

## Known Coverage Gaps Before Selector Freezing

- The missing ordinary-stellar baseline is now supplied by a disjoint 525-source
  SDSS spectroscopic stellar reference matched 3:1 to confirmed development UCDs in
  G magnitude, absolute Galactic latitude, and absolute ecliptic latitude. It is not
  proof of physical singleness and remains subject to SDSS targeting and footprint
  bias; definitions and results are in `docs/spectroscopic_stellar_reference.md`.
- SDSS galaxies are heterogeneous; a dedicated compact-galaxy or nuclear-source
  subset has not yet been defined.
- Planetary nebulae and other compact emission-line sources are not represented.
- H II coverage is limited to 19 PHANGS spiral fields and 21 van Zee dwarf hosts,
  with only 12 unique Gaia sources in the dwarf-host cohort.
- The benchmark is not matched to the final nearby-galaxy search footprint or
  Galactic-latitude distribution because those samples are not yet frozen.

These gaps do not invalidate the current diagnostic feature analysis, but they
block treating `benchmark_v1` as a complete basis for a final selector or a
population-level contamination rate.

The approved expanded treatment, catalog comparison, circularity safeguards, and
external-file provenance are documented in
`docs/extragalactic_contaminant_catalogs.md`. The large supplements do not mutate
the released benchmark.

## Reproducibility Artifacts

- `data/literature/benchmarks/gaia_validation_benchmark_v1_manifest.json`: exact
  queries, sampling rules, input hashes, magnitude domain, and counts.
- `data/literature/sources/validation_benchmark_sources.json`: bibcodes, DOIs,
  catalog identifiers, access endpoints, roles, and approval status.
- `data/literature/validation/phangs_muse_gaia_association_calibration.json`:
  PHANGS quality rule, queries, fields, displaced controls, and separation curve.
- `data/literature/validation/van_zee_dwarf_hii_gaia_association_calibration.json`:
  dwarf-host coordinate note, queries, controls, and separation curve.
- `data/literature/discovery/validation_benchmark_literature_search_2026-07-16.json`:
  exact dwarf-H II ADS search and source dispositions.
- `scripts/phase1_literature/build_validation_benchmark.py`: executable row-level
  definitions and consolidation logic.

## Q1 Decision Record

The project lead identified contaminant-source definition as a potential selector
bias on 2026-07-16. The permanent response is to retain each cohort separately,
prohibit prevalence claims from raw cohort proportions, require per-cohort and
sensitivity metrics, and close the clean-single-star and other coverage gaps
before freezing BT-002.
