# Instructor evidence record and remaining preparation

**Check date:** 2026-10-12  
**Scope:** Read-only reference checks and a small online feasibility test  
**Not performed:** New sky search, selector changes, catalog edits, classroom deployment

[Course guide](README.md) · [Concepts](concepts.md) · [Shortlist](target_shortlist.md)

## Gaia measurements: retrieval and exact identifiers

Endpoint: `https://gea.esac.esa.int/tap-server/tap/sync`, synchronous GET with
`REQUEST=doQuery`, `LANG=ADQL`, `FORMAT=csv`. This is an instructor reproducibility
record; students do not need to write or run query language.

```sql
SELECT source_id, ra, dec, phot_g_mean_mag, bp_rp,
       parallax, parallax_error, pmra, pmra_error, pmdec, pmdec_error,
       pmra_pmdec_corr, astrometric_params_solved, ruwe,
       astrometric_excess_noise, astrometric_excess_noise_sig,
       phot_bp_rp_excess_factor, ipd_frac_multi_peak, ipd_frac_odd_win
FROM gaiadr3.gaia_source
WHERE source_id IN
      (3928413763095214592, 3928425445406259456, 3681343123693230336)
   OR 1 = CONTAINS(POINT('ICRS', ra, dec),
                  CIRCLE('ICRS', 190.8999, 11.5347, 0.001388888888888889))
```

HTTP 200; four rows returned. The circle is a five-arcsecond identification check
around the published M60-UCD1 position, not a host search aperture. Snapshot:

```csv
source_id,ra,dec,phot_g_mean_mag,bp_rp,parallax,parallax_error,pmra,pmra_error,pmdec,pmdec_error,pmra_pmdec_corr,astrometric_params_solved,ruwe,astrometric_excess_noise,astrometric_excess_noise_sig,phot_bp_rp_excess_factor,ipd_frac_multi_peak,ipd_frac_odd_win
3681343123693230336,188.86962553574625,-3.7892273034273836,20.011778,1.6481342,,,,,,,,3,,20.483147,87.61437,14.027047,0,0
3928413763095214592,190.54602278774948,11.644788807179935,17.850197,1.3634567,0.37005448835480237,0.41709605,0.09610431738777558,0.49103335,-0.3610979218563479,0.48753542,-0.2133063,95,2.505549,2.946191,71.23422,6.1350255,0,0
3927659910436411136,190.89985109702346,11.534629821482913,18.114574,1.393795,-0.07908963212446929,0.39496252,0.42010192290665743,0.47508794,-0.5473674291859698,0.4324203,-0.38418424,95,1.9795566,2.3343117,50.317596,4.6536803,0,0
3928425445406259456,190.48055767488492,11.667719481928792,19.513365,1.3728333,,,,,,,,3,,10.038126,92.513596,9.460632,0,0
```

The corresponding `astrometric_params_solved` values 95 and 3 mean six-parameter
and position-only solutions, respectively. The sixth fitted parameter is a
pseudocolor used in astrometric calibration. Neither code is a UCD label. See the
[official DR3 data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html).
The two image-window diagnostic fields are retained for reproducibility, not
included in the core student lesson.

### Foreground comparison query

```sql
SELECT TOP 3 source_id, ra, dec, phot_g_mean_mag, bp_rp,
       parallax, parallax_error, pmra, pmra_error, pmdec, pmdec_error,
       pmra_pmdec_corr, ruwe, astrometric_excess_noise,
       astrometric_excess_noise_sig, phot_bp_rp_excess_factor
FROM gaiadr3.gaia_source
WHERE 1 = CONTAINS(POINT('ICRS', ra, dec),
                  CIRCLE('ICRS', 190.54602278774948, 11.644788807179935, 0.15))
  AND phot_g_mean_mag BETWEEN 17 AND 19
  AND bp_rp BETWEEN 1.0 AND 2.0
  AND parallax_over_error > 10
  AND ruwe < 1.2
  AND SQRT(pmra * pmra + pmdec * pmdec) > 10
ORDER BY phot_g_mean_mag ASC
```

HTTP 200; one row returned:

```csv
source_id,ra,dec,phot_g_mean_mag,bp_rp,parallax,parallax_error,pmra,pmra_error,pmdec,pmdec_error,pmra_pmdec_corr,ruwe,astrometric_excess_noise,astrometric_excess_noise_sig,phot_bp_rp_excess_factor
3928418917055971968,190.6453381977382,11.680329417651473,17.129242,1.1142445,0.7881429756883358,0.07627482,10.984085699696536,0.090215534,-50.07016177246407,0.0824956,-0.22354709,0.9647263,0.0,0.0,1.2198806
```

This deliberately selects an easy foreground example; it is not an unbiased
comparison sample or a set of proposed science-selection thresholds. Preserve
source identifiers as strings when loading these snapshots into any tool.

### Optional significance calculation

For parallax use `abs(parallax) / parallax_error`. For a two-component proper
motion, account for the correlation `rho = pmra_pmdec_corr`:

```text
u = pmra / pmra_error
v = pmdec / pmdec_error
combined_motion_significance = sqrt((u*u + v*v - 2*rho*u*v) / (1-rho*rho))
```

This is distance from zero motion in units defined by the covariance matrix; it
is not directly a one-dimensional Gaussian tail probability. Calculated values:
M60-UCD1 parallax 0.200, combined motion 1.337; M59-UCD3 parallax 0.887,
combined motion 0.742. These calculations use the quoted random-error covariance
and do not correct Gaia systematics or modeling failures.

## Legacy Survey checks

The [official DR11 description](https://www.legacysurvey.org/dr11/description/)
documents both the standard layer and a grz alternative. Actual requests for the
two worked examples gave:

| Layer and target | Transport | Pixel/content check | Interpretation |
| --- | --- | --- | --- |
| `ls-dr11-grz`, M60-UCD1 | HTTP 200, 128×128 JPEG | Every channel of every pixel equals 32 | Blank tile, not usable imaging |
| `ls-dr11-grz`, M59-UCD3 | HTTP 200, 128×128 JPEG | Every channel of every pixel equals 32 | Blank tile, not usable imaging |
| `ls-dr11`, M60-UCD1 | HTTP 200, 128×128 JPEG | 4,153 distinct RGB colors; visually checked | Compact central source, host-light gradient, nearby streaks |
| `ls-dr11`, M59-UCD3 | HTTP 200, 128×128 JPEG | 9,450 distinct RGB colors; visually checked | Compact central source with another bright source in the wider close-up |

Color counts detect a blank response; they do not measure scientific image quality.

Request pattern, substituting the exact coordinates in the shortlist:

```text
https://www.legacysurvey.org/viewer/jpeg-cutout?ra=RA&dec=DEC&layer=ls-dr11&pixscale=0.262&size=128
```

The square covers 33.536 arcseconds per side. Standard DR11 JPEG colors need not
use the same bands as previous grz displays, so label the layer and do not infer
photometric colors from the displayed RGB values. Preserve the blank responses
as failed content checks rather than silently substituting a different release.

Downloaded records are outside Git at
`~/Dropbox/work/data/bubbletea/teaching/20261012/`:

- `m60_ucd1_dr11_grz.jpg` and `m59_ucd3_dr11_grz.jpg`: blank responses.
- `m60_ucd1_dr11_default.jpg` and `m59_ucd3_dr11_default.jpg`: inspected images.

Host-center tests used `fits-cutout`, `layer=ls-dr11`, `bands=grz`, `size=32`,
`pixscale=0.262`, at the exact host coordinates in the shortlist. NGC 2974 and
NGC 4753 returned three 32×32 planes, each with 1,024 finite and nonzero pixels.
Their wider JPEG tests (`size=256`, `pixscale=4`) had 6,392 and 7,244 distinct RGB
colors, respectively. These responses were inspected numerically in memory,
not saved as a host-coverage data product and not visually adjudicated.
NGC 1395's first FITS request returned HTTP 429, a rate limit, not evidence of
missing survey coverage. A later serial retry returned HTTP 200 and three 32×32
planes, each with 1,024 finite and nonzero pixels. Do not repeat concurrent host
requests or launch a bulk download yet; use serial requests and backoff.

Full-area coverage, per-band weights, image defects, host-background effects,
and actual candidate cutouts still need checking. Legacy image availability never
changes the Gaia radial-area denominator.

## Literature and local catalog checks

The canonical database was opened with SQLite `mode=ro`:
`data/literature/database/ucd_reference_v2.db`. Classification, source-association,
and exact host-label checks did not edit any records. M60-UCD1's coordinate
counterpart is NGVS-UCD753 from `reference/liu2020`, VizieR `J/ApJS/250/17`,
`table3.dat:raw_row_753`, bibcode `2020ApJS..250...17L`. Its approved canonical
classification is confirmed, while the original source's reported label is
candidate. Its canonical position is 190.8998699, 11.5346389; the source row has
no Gaia identifier. The live Gaia match is an independently recorded teaching
check, not a newly accepted database association.

The two M60 review seeds link to datasets from
[Liu et al. 2015](https://doi.org/10.1088/0004-637X/812/1/34)
(`2015ApJ...812...34L`, original `reference/liu2015/table6.dat`) and
[Fahrion et al. 2019](https://doi.org/10.1051/0004-6361/201834941)
(`2019A&A...625A..50F`, inherited comparative compilation at
`data/literature/catalogs/by_source/2019A&A...625A..50V.csv`).
Use the original publication/table context and the approved classification, not
the inherited source labels alone. The subsequent portable packet below preserves
these distinctions; candidate status is not confirmation.

### Portable teaching packet, 2026-10-13

The [versioned teaching data](../../data/teaching/README.md) records six exact Gaia
identifiers, original provenance, host-distance assumptions, the complete Gaia
query, retrieval timestamps, twelve image URLs/scales, and SHA-256 file digests.
The UTC retrieval date is 2026-10-12 (2026-10-13 in local Shanghai time).
Candidate A is row 22 and candidate B is row 25 of the original
`reference/liu2015/table6.dat`; both exact names were checked in that file.

A one-object download test completed in 18.203 seconds before the six-object
retrieval completed in 38.745 seconds. All twelve standard `ls-dr11` images were
nonuniform. The PDF's displayed cutouts and the HTML's two-scale inspection
layout were checked for presentation, not assigned scientific visual flags.
The raw image records deliberately retain `visual_review_status: pending`:
download/display checks are not an adjudicated source classification.

The [build report](materials_build_report.json) and
[validation report](materials_validation_report.json) record the generated files
and 41 passed offline checks. Six rendered PDF pages were inspected separately;
live archive interfaces and Windows execution were not fully tested or required.
No external QSO, galaxy, or non-single-star cross-match was performed for this
small teaching packet; all six records say **not checked**, not **no match**.

Nearby-host values came from `data/galaxy_sample/pilot_sample_top100.csv`, cross-
checked against `galaxy_sample_ranked.csv`. The ranked table does not carry
`is_lit_host` or imaging-coverage columns. The pilot flag derives from a short
hardcoded list in `scripts/phase2_galaxy_sample/rank_targets.py`, not a complete
literature audit. Exact canonical host-label associations were zero for the three
shortlisted hosts; NGC 2768 demonstrated why that is not a literature-absence test.

### Bounded ADS search

ADS search API: `https://api.adsabs.harvard.edu/v1/search/query`, `rows=100`,
`start=0`, sorted by date descending. Credentials were read from the environment;
no credential is stored here. The final title/abstract query was:

```text
(title:("ultra-compact" OR ultracompact) OR abs:("ultra-compact dwarf" OR "ultracompact dwarf" OR UCD))
AND
(title:("NGC 2974" OR "NGC 2652" OR "NGC 4753" OR "NGC 1395" OR "NGC 4699" OR "NGC 1332" OR "NGC 3585" OR "NGC 3607" OR "NGC 4125" OR "NGC 7331" OR "NGC 2841")
OR abs:("NGC 2974" OR "NGC 2652" OR "NGC 4753" OR "NGC 1395" OR "NGC 4699" OR "NGC 1332" OR "NGC 3585" OR "NGC 3607" OR "NGC 4125" OR "NGC 7331" OR "NGC 2841"))
```

HTTP 200; `numFound=3`, all three returned, so no pagination truncation:

| Bibcode | Screening result |
| --- | --- |
| `2022ApJ...938..104K` | Black-hole/lensing topic; no qualifying host UCD discovery identified |
| `2010AAS...21631607W` | NGC 2841 compact-cluster conference contribution; not evidence that a shortlisted host has a UCD |
| `1977ApJ...214..359K` | Galaxy-profile topic; no qualifying UCD discovery identified |

Title/abstract indexing and aliases can miss sources mentioned only in tables or
full text. Separate host-specific web and paper checks found the relevant SLUGGS,
NGC 1395, and NGC 4753 studies. A definitive eligibility audit must also search
coordinates, aliases, compact-object tables, recent papers, and cited/follow-up
work for the final chosen host. Do not present this query as proof of absence.

### Primary references used in this preparation

| Reference | ADS bibcode | DOI / primary text |
| --- | --- | --- |
| Strader et al. 2013, The Densest Galaxy | `2013ApJ...775L...6S` | [10.1088/2041-8205/775/1/L6](https://doi.org/10.1088/2041-8205/775/1/L6); [text](https://arxiv.org/html/1307.7707) |
| Sandoval et al. 2015, Hiding in Plain Sight | `2015ApJ...808L..32S` | [10.1088/2041-8205/808/1/L32](https://doi.org/10.1088/2041-8205/808/1/L32) |
| Chilingarian & Mamon 2008, M59cO | `2008MNRAS.385L..83C` | [10.1111/j.1745-3933.2008.00438.x](https://doi.org/10.1111/j.1745-3933.2008.00438.x) |
| Norris & Kannappan 2011, UCD origins | `2011MNRAS.414..739N` | [10.1111/j.1365-2966.2011.18440.x](https://doi.org/10.1111/j.1365-2966.2011.18440.x) |
| Forbes et al. 2017, SLUGGS velocity catalog | `2017AJ....153..114F` | [10.3847/1538-3881/153/3/114](https://doi.org/10.3847/1538-3881/153/3/114); [text](https://arxiv.org/html/1701.04835) |
| Caso et al. 2015, NGC 4753 cluster system | `2015MNRAS.453.4421C` | [10.1093/mnras/stv2015](https://doi.org/10.1093/mnras/stv2015); [text](https://arxiv.org/html/1508.07653) |
| Escudero et al. 2018, NGC 1395 cluster system | `2018MNRAS.474.4302E` | [10.1093/mnras/stx3045](https://doi.org/10.1093/mnras/stx3045) |

ADS supplied the publication metadata. Existing reference packages remain in place;
this task did not download new paper PDFs or claim a completed provenance package.

## Next preparation pass: bounded and testable

1. Rehearse one object end-to-end on Windows.
   Save screenshots, source measurements, and image-layer labels as fallbacks.
2. Check a small varied published-candidate packet, including the two M60 seeds
   only if their provenance and images pass. Give students independent worksheets.
3. Audit one possible new host, not all three simultaneously: verify luminosity
   and distance, literature status, environment, Gaia sensitivity, and DR11
   coverage of the intended rings. Record any gaps explicitly. HSC is optional.
4. Only then prepare a strict teaching-only source list. Test proposed cuts on
   the known examples first and report what they reject; do not equate a small,
   visually attractive list with a calibrated contamination or completeness result.

Stop for instructor review before fixing the classroom packet or interpreting a
source as a new discovery. No multi-user tool deployment is authorized by this
preparation task.
