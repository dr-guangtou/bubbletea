# Extragalactic Contaminant Reference Strategy

**Decision date:** 2026-07-17  
**Status:** Approved detour completed; supplementary catalogs staged without changing
`benchmark_v1`

## Why the Original Cohorts Were Moderate

The 805 SDSS galaxies, 491 SDSS QSOs, and 1,412 Gaia non-single-star sources in
`benchmark_v1` were selected as bounded engineering cohorts for the first
development-only feature diagnostic. Their purpose was to expose distinct failure
modes quickly without letting abundant negative classes overwhelm the 175 confirmed
development UCDs. They were never intended to measure the sky density, prevalence,
or full diversity of contaminants.

The SDSS documentation contained a material scale error. The retained interval was
`0.0 <= random_id < 0.1`, but SDSS `random_id` spans 0 to 100. The benchmark therefore
used a deterministic 0.1% interval, not a 10% interval. The row-level benchmark and
its manifest correctly preserve the exact interval, so the released identities and
partition remain reproducible; only the prose interpretation was wrong. Future code
and documentation must express the interval and its measured domain together.

The NSS cohort similarly uses `MOD(recno, 500) = 1` independently in 17 solution
tables. It is a systematic engineering subsample of published binary or multiple-star
solutions, not an ordinary-star baseline or an estimate of binary prevalence. A
full magnitude-restricted server-side NSS count was attempted on 2026-07-17, but the
remote join did not complete within the measured interactive audit window; no
unmeasured parent count is inferred from the stride.

## Three Reference Roles Must Remain Separate

1. **Relatively independent calibration labels.** Spectroscopic classes are used to
   measure how Gaia features behave for objects identified outside the Gaia-only
   selector. Survey targeting and Gaia-detection biases still have to be reported.
2. **Gaia failure-mode stress catalogs.** Large Gaia-derived candidate catalogs test
   compact galaxies, bright nuclei, morphology processing, and other cases that the
   search will actually encounter. They cannot serve as independent training truth
   when their construction uses the same Gaia features being evaluated.
3. **Sky-density and spatial-null catalogs.** Large catalogs and published selection
   functions test whether candidate densities vary around nearby galaxies or across
   the survey footprint. Raw catalog density is not inserted as a class prior in the
   selector benchmark.

This separation prevents a large but circular Gaia catalog from making a Gaia-only
selector look artificially successful, while still addressing the scientific risk
that compact or nuclear galaxies are numerous enough to mimic a rare-object excess.

## Selected Reference Layers

| Layer | Measured size | Approved role | Principal limitation |
|---|---:|---|---|
| Clean SDSS DR16 spectra linked to Gaia DR3 | 747,153 galaxies; 494,203 QSOs | Relatively independent class calibration and density reference | SDSS targeting, footprint, and Gaia-match selection |
| Gaia DR3 galaxy candidates with a published Sersic morphology fit | 914,837 candidates | Primary compact/core-dominated extended-source failure-mode and host-field stress catalog | Candidate catalog; Gaia-derived and therefore circular for Gaia-feature fitting |
| Quaia v1, `G < 20.0` | 755,850 QSOs | All-sky QSO spatial null with its published selection function | Parent sample and filtering use Gaia quantities |

The complete files are stored outside the repository under
`$BUBBLETEA_EXTERNAL_DATA/bubbletea/extragalactic_reference/`. Exact paths, hashes,
queries, row counts, and dispositions are recorded in
`data/literature/sources/extragalactic_reference_catalogs.json` and checked by
`scripts/phase1_literature/audit_extragalactic_reference_catalogs.py`.
The ADS query strings, result counts, and curated literature dispositions are in
`data/literature/discovery/extragalactic_contaminant_literature_search_2026-07-17.json`.

### Spectroscopic SDSS Layer

The expanded extraction uses clean primary SDSS DR16 spectra (`scienceprimary = 1`,
`zwarning = 0`) in the complete benchmark Gaia-magnitude interval. Ten exact
`random_id` bins spanning `[0, 100)` were retrieved per class to avoid the archive's
100,001-row result cap. Before association resolution there were 753,558 galaxy and
494,608 QSO spectrum matches. The audit found zero cross-class Gaia conflicts;
retaining the nearest unique Gaia-spectrum pair produces 747,153 galaxies and
494,203 QSOs, all
with unique Gaia identifiers.

This layer replaces the old sample-size limitation for spectroscopic comparisons,
but it does not make SDSS a complete sky census. Analyses must stratify by magnitude,
sky position, and relevant spectroscopic subtype rather than interpreting its raw
galaxy-to-QSO ratio as an astrophysical prior.

### Gaia DR3 Galaxy Layers

The integrated Gaia DR3 `galaxy_candidates` table contains 4,842,342 rows. The Gaia
DR3 extragalactic-content analysis emphasizes that the full table is designed for
completeness and is not a pure galaxy sample. Its recommended higher-purity union is:

```sql
radius_sersic IS NOT NULL
OR classlabel_dsc_joint = 'galaxy'
OR vari_best_class_name = 'GALAXY'
```

The union contains 2,891,132 rows in the audited service. It is appropriate for
large-scale sky-density and sensitivity queries, with its Gaia-derived nature made
explicit.

The downloaded primary stress layer is the 914,837-source subset with
`radius_sersic IS NOT NULL`. Gaia's surface-brightness pipeline processed sources
for which galaxy profile fitting was possible. Gaia's onboard windowing and source
detection favor compact high-surface-brightness structure and detectable bulges or
nuclei over diffuse discs. This makes the subset especially relevant to the user's
concern: the galaxies most likely to enter the Gaia UCD search are compact systems
or systems whose central light is detected as a Gaia source.

These rows are not uniformly confirmed galaxies. UCDs, H II regions, galaxy nuclei,
and other compact or extended sources can in principle enter the candidate table.
The subset therefore cannot be the UCD-search parent sample: requiring a successful
Sersic fit would remove unresolved and barely resolved UCDs. Its approved role is
conditional density and failure-mode measurement plus supplementary morphology
evidence, never mandatory search-sample membership.

The morphology subset is not used as truth to optimize Gaia features. It is used to
measure selector acceptance, magnitude and morphology dependence, host-centric
density, and failure examples after candidate score terms have been defined using
less circular evidence.

### Gaia DR3 and External QSO Layers

The integrated Gaia DR3 `qso_candidates` table contains 6,649,162 rows. The audited
higher-purity union follows the Gaia extragalactic-content work:

```sql
gaia_crf_source = true
OR host_galaxy_flag < 6
OR classlabel_dsc_joint = 'quasar'
OR vari_best_class_name = 'AGN'
```

It contains 1,942,825 rows. Like the galaxy union, it is Gaia-derived and must not be
treated as independent selector truth.

Quaia combines the Gaia DR3 QSO candidate set with unWISE information and provides
an all-sky catalog plus a published selection function. The downloaded `G < 20.0`
version contains 755,850 unique Gaia sources. It is the selected QSO spatial-null
resource because the selection function makes sky-density tests more interpretable.
QSO contamination remains a lower host-correlated priority than galaxy contamination,
but it remains useful for checking broad footprint and scanning-law structure.

CatNorth was reviewed but is northern-only and uses Gaia astrometry in its classifier.
The newer CatGlobe compilation is a useful future all-sky sensitivity comparison.
The Gaia-WISE AGN catalog remains an important historical astrometric reference but
uses Gaia DR1. None is needed as a second large download before Quaia is tested.

### Gaia DR4 Work

The Gaia DR4 extragalactic-classification paper is a methods reference, not an
operational catalog input for this audit. It informs future classifier design and
the value of CatWISE information, but a pre-release methods paper must not be
silently treated as released DR4 data.

## Nearby-Galaxy Field Evidence

Two literature results make the galaxy detour scientifically necessary rather than
merely a sample-size expansion:

- Hales et al. compare Gaia classifications with NED and SIMBAD in 1,040 nearby
  galaxies and show that classification behavior in host fields differs materially
  from a clean all-sky interpretation; literature galaxies can appear star-like in
  Gaia, and Gaia QSO labels in these fields have low purity.
- Barmby studies roughly half a million Gaia sources projected toward 1,401 Local
  Volume galaxies and finds that foreground and host-associated populations vary
  with radius and magnitude.

Therefore the decisive galaxy test is not only a global ROC statistic. It is the
surface density and selector acceptance of Gaia-detected galaxies as a function of
host-centric radius, magnitude, morphology-fit properties, Galactic latitude, and
host environment. That analysis must preserve one-to-many source-host associations.

## Decisions and Safeguards

- `benchmark_v1` remains immutable; no labels, partitions, or validation identifiers
  are replaced by this detour.
- The expanded SDSS catalog is the preferred independent extragalactic supplement.
- Gaia morphology candidates are the principal extended-source failure-mode stress
  set, not a spectroscopic truth sample or UCD parent sample.
- The full Gaia higher-purity unions are query layers for density and sensitivity,
  not training labels.
- Quaia is the preferred QSO spatial-null layer; QSO and galaxy results remain
  separate rather than pooled according to catalog size.
- NSS remains a binary/multiple-system failure-mode sample. Its moderate benchmark
  size is adequate for the initial diagnostic but cannot substitute for the pending
  clean ordinary-star cohort.
- Performance must be reported by contaminant subtype and magnitude. Catalog row
  fractions must never be interpreted as astrophysical prevalence.
- Validation-partition identifiers remain uninspected until the selector is frozen.

## Bounded Host-Field Result

The approved predefined three-galaxy stress test retrieved 814 Gaia morphology
candidates around NGC 1316, M49, and NGC 2974. Both rejected legacy candidate-selection
rules retained the same 714 candidates (87.7%), while RUWE
and covariance-aware proper-motion significance
were available for only 11.9%. The combined surface density was 21.7614 per square
degree inside 300 kpc and 28.7721 per square degree at 300--600 kpc. Thus the test
does not establish central clustering, but it confirms a high-acceptance compact-
galaxy failure mode. Full methods, per-host results, limitations, and artifacts are
in `docs/gaia_morphology_host_field_stress.md`.

A blind-safe exact-ID cross-match found zero morphology-catalog memberships among
175 high-confidence development UCDs, one among 569 uncertain development UCD
candidates, and zero among 127 development H II regions. The 24 confirmed validation
UCDs remain blind. Definitions, morphology interpretation, and reproducibility
artifacts are in `docs/gaia_morphology_ucd_crossmatch.md`.

## Primary References

- Gaia Collaboration, *Gaia Data Release 3: The extragalactic content*,
  `2023A&A...674A..41G`, DOI `10.1051/0004-6361/202243232`.
- Ducourant et al., *Gaia Data Release 3: Surface brightness profiles of galaxies*,
  `2023A&A...674A..11D`, DOI `10.1051/0004-6361/202243798`.
- Storey-Fisher et al., *Quaia, the Gaia-unWISE Quasar Catalog*,
  `2024ApJ...964...69S`, DOI `10.3847/1538-4357/ad1328`, arXiv `2306.17749`,
  Zenodo `10403370`.
- Shu et al., *The Gaia-unWISE AGN Catalog*, `2018ApJS..236...37S`,
  DOI `10.3847/1538-4365/aabcb7`, VizieR `J/ApJS/236/37`.
- Fu et al., *CatNorth*, `2024ApJS..271...54F`, arXiv `2310.12704`.
- Hughes et al., *Comparing Gaia, NED, and SIMBAD source classifications in nearby
  galaxies*, `2024MNRAS.533.3415H`, arXiv `2408.12717`.
- Barmby, *Gaia sources in the directions of nearby galaxies*,
  `2023MNRAS.518.3746B`, arXiv `2211.04341`.
