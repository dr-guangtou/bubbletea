# Repeated point-source logistic-regression stability

## Decision status

The provisional logistic model passes the predeclared development stability gate
and is ready for selector-freeze review. It is not yet a frozen selector, and the
721-row validation partition remains sealed.

## Design

The analysis repeated five-outer/four-inner grouped cross-validation ten times
using the deterministic seeds declared in `docs/SPEC.md`. Each of the 2,228 fitting
rows receives one held-out prediction per repeat. Matched stars remain grouped with
their matched UCD; preprocessing, imputation, hyperparameter selection, and the
90% recall threshold remain fold-local.

The model and scientific objective are unchanged from the first comparison:

- positive class: 175 confirmed development UCDs;
- equal-weight priority negatives: 525 matched spectroscopic stars, 1,125 Gaia NSS
  sources, and 403 spectroscopic QSOs;
- nine Gaia measurement features, including BP-RP as a soft feature;
- no NSS membership, DSC class probability, candidate-catalog membership, or
  Sersic model input; and
- no fitting to the galaxy or H II secondary stress cohorts.

## Stability result

| Metric across ten repeats | Minimum | Median | Maximum |
|---|---:|---:|---:|
| Confirmed-UCD recall | 93.14% | 93.71% | 95.43% |
| Equal-cohort priority retention | 3.75% | 3.96% | 4.42% |

All 50 outer fits selected logistic regularization `C = 3.0`. Their inner-selected
probability thresholds range from 0.474 to 0.585, demonstrating that the numerical
threshold is training-sample dependent and must be calibrated for the final
full-development model rather than copied from one fold.

`C = 3.0` is also the least-regularized boundary of the tested grid. Unanimous
selection therefore demonstrates reproducibility within this grid, not that the
regularization optimum has been enclosed. A bounded development-only extension
above `C = 3.0` is required before choosing the final regularization strength.

Individual outer-fold recall still ranges from 81.82% to 100%. The ten-repeat
pooled result is stable because every source rotates through held-out folds, but
the remaining fold range warns that spatially concentrated failure modes still
matter. This distinction is why the result advances to review rather than directly
to validation.

## Coefficient behavior

All nine measurement-feature coefficients retain the same sign in all 50 fits.
The coefficients are measured after fold-local standardization, so their magnitudes
are comparable within the fitted model but are not causal feature importances.
Correlated Gaia diagnostics can share predictive weight.

| Feature | Median standardized coefficient | Sign in 50/50 fits |
|---|---:|---:|
| Log astrometric excess noise | +0.587 | Positive |
| Log excess-noise significance | +0.259 | Positive |
| BP/RP flux-excess factor | +0.198 | Positive |
| Log proper-motion zero-significance | -0.197 | Negative |
| Log absolute-parallax zero-significance | -0.159 | Negative |
| BP-RP color | +0.066 | Positive |
| Log IPD multi-peak percentage | +0.066 | Positive |
| Log RUWE | +0.060 | Positive |
| Log IPD odd-window percentage | +0.055 | Positive |

Positive coefficients increase the fitted UCD-like score; negative parallax and
proper-motion coefficients correctly penalize significant nonzero astrometry.

## Persistent failures

A persistent failure means a confirmed UCD is selected in at most five of ten
repeats, or a priority contaminant is selected in at least five repeats.

| Cohort | Persistent failures | Cohort size | Fraction |
|---|---:|---:|---:|
| Confirmed UCD | 11 | 175 | 6.29% |
| Matched spectroscopic star | 37 | 525 | 7.05% |
| Gaia NSS | 4 | 1,125 | 0.36% |
| Spectroscopic QSO | 20 | 403 | 4.96% |

Three persistently missed UCDs share HEALPix group 34534, two share group 43262,
and two share group 36290. Several have Gaia measurements that are very star-like:
zero astrometric excess noise, RUWE near one, and significant proper motion. One
particularly bright row has `G = 12.34` and extremely precise nonzero astrometry.
These objects remain confirmed literature UCD labels; the diagnostic does not
relabel them. Their literature identity, Gaia association, and possible foreground
or nuclear interpretation require source-level audit before selector freezing.

The complete source list, including identifiers, sky position, magnitude, mean
score, and selection frequency, is preserved in
`data/literature/validation/point_source_ml_stability_source_summary_v1.csv`.

## Fixed-stratum behavior

| Confirmed-UCD stratum | Sources | Repeated recall |
|---|---:|---:|
| `G <= 18` | 7 | 85.71% |
| `18 < G <= 19` | 17 | 90.59% |
| `19 < G <= 20` | 22 | 86.36% |
| `G > 20` | 129 | 96.28% |
| `abs(b) < 30 deg` | 32 | 91.88% |
| `30 <= abs(b) < 60 deg` | 46 | 85.22% |
| `abs(b) >= 60 deg` | 97 | 98.97% |
| `abs(ecliptic latitude) < 30 deg` | 103 | 99.03% |
| `30 <= abs(ecliptic latitude) < 60 deg` | 71 | 88.17% |
| `abs(ecliptic latitude) >= 60 deg` | 1 | 0.00% |

The final ecliptic bin contains one source and is not a population estimate. The
magnitude and latitude differences are descriptive development diagnostics, not
new cuts. They reinforce the need to audit failure cases and declare the final
selector's applicability domain.

## 2026-07-17 preliminary source audit

The 11 persistently missed UCDs occupy seven level-6 HEALPix groups rather than one
group. Group 34534 contains three, groups 43262 and 36290 contain two each, and four
groups contain one each. Their host contexts are four spectroscopically confirmed
Fornax systems from Saifollahi table A1, two NGC 1400/1407 objects, two NGC 5128
objects, and one each around M87, NGC 1553/1549, and M31.

The normalized distance field is present for only 5/11 missed objects and 105/164
other confirmed development UCDs. Its measured medians are 20.0 and 16.5 Mpc,
respectively, but the asymmetric missingness prevents a conclusion that the missed
objects are systematically farther away. The host mix contains no high-redshift
population; the relevant quantity is local host distance and spectroscopic
membership rather than cosmological redshift.

The bright M31 row exposes a more serious evidence issue:

- literature name: `B409`;
- canonical ID: `canonical_a71db2a61b8856cb835b46670601f951`;
- Gaia DR3 source ID: `375037265841433344`;
- Gaia position: RA `12.663251280395 deg`, Dec `+41.293171078320 deg`;
- literature position: RA `12.663250000000 deg`, Dec `+41.293130555556 deg`;
- positional separation: approximately `0.146 arcsec`;
- Gaia G: `12.340369` mag;
- parallax: `1.126604 +/- 0.014465` mas (`77.9 sigma`);
- proper motion: `pmra = -5.316260 +/- 0.013725` and
  `pmdec = +3.045072 +/- 0.010659` mas/yr; and
- Gaia radial velocity: `-37.13 +/- 2.25 km/s`.

Fahrion table B1 lists B409 with `RV = 0.0`, `reff = 0.0`, and reference 11 to the
M31 Revised Bologna Catalog. The confirmation review had interpreted every
coordinate-bearing Fahrion row as supplying a radial velocity, but 68/377 such rows
use `RV = 0.0`; 30 of those currently occur among the 175 confirmed development
UCDs. For B409, the Gaia measurements are strongly consistent with a foreground
Milky Way star. This could mean a foreground superposition was assigned to the real
M31 compact object, or that the literature object itself should not be treated as a
confirmed UCD. The current evidence does not distinguish those cases.

Consequently, selector-freeze readiness is suspended pending a non-destructive
re-audit of the 68 zero-RV Fahrion rows, their independent evidence, and their Gaia
associations. No label or provenance record has been altered by this diagnostic.

## Readiness gate and required review

All predeclared numerical criteria pass:

- median repeated recall is at least 90%;
- no complete repeat falls below 85% recall; and
- every measurement coefficient has at least 80% sign agreement (measured: 100%).

The later source audit supersedes numerical readiness. Before validation can be
unsealed, the project must:

1. audit the 11 persistently missed confirmed UCD associations without changing
   labels merely because the classifier dislikes them;
2. correct the zero-RV Fahrion evidence rule and rederive the benchmark while
   preserving every source row and prior decision as provenance;
3. review the 61 persistent priority-contaminant failures;
4. extend the regularization sensitivity above the current `C = 3.0` grid boundary;
5. define how the final full-development model receives one reproducible threshold;
6. fit and serialize one versioned selector with its null policy and applicability
   domain; and
7. freeze all of the above before the single withheld-validation evaluation.

## Reproduction

- Analysis: `scripts/phase1_literature/analyze_point_source_ml_stability.py`
- Validation: `scripts/phase1_literature/validate_point_source_ml_stability.py`
- Command: `uv run python scripts/phase1_literature/analyze_point_source_ml_stability.py`
- Runtime measured on 2026-07-17: 45.19 seconds for the final ten-repeat run
- Summary: `data/literature/validation/point_source_ml_stability_summary_v1.json`
- Validation report: `data/literature/validation/point_source_ml_stability_validation_v1.json`
