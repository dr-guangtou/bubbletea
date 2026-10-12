# Gaia selector development and validation

**Consolidated:** 2026-10-12  
**Role:** Topic-organized development evidence, not a replacement for current scientific requirements.

[Science guide](../science_guide.md) · [Current status](../current_status.md) · [Documentation audit](documentation_audit.md)

## Current reading guidance

Selector v1 is the reproducible baseline, not a physical-UCD probability. The one-time benchmark validation is complete; later real-field contamination and sensitivity work remains open. Read the frozen-model and validation records before older exploratory scores. The astrometric assessment did not support a universal hard veto at the required reliable-UCD retention.

## Dated evidence

Each section below retains an original report's scientific content, measurements,
commands, and limitations. Status statements apply to that report's original date;
read the guidance above and current SPEC before following an old next step.

<a id="record-point_source_selector_calibration"></a>

> Dated source record: `docs/point_source_selector_calibration.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/point_source_selector_calibration.md -->
## Point-Source-Priority Selector Calibration

**Date:** 2026-07-17  
**Status:** Development operating points measured; no threshold frozen

### Approved Priority

The primary Stage 3 objective is to reject ordinary stars, Gaia NSS/binary failure
modes, and spectroscopic QSOs while retaining confirmed UCDs. Each point-source
cohort contributes equally to the optimization objective, regardless of its row
count. Spectroscopic galaxies are a secondary stress set intended for ancillary
imaging or photometric rejection. H II regions and compact young clusters remain a
separate host-correlated color/morphology safeguard.

### Score Architecture

The complete-coverage core combines two empirical ranks:

- absolute astrometric excess noise; and
- BP/RP flux-excess factor.

Each rank is the mean empirical CDF across the three equally weighted priority
cohorts. A small conditional penalty may be applied using covariance-aware proper-
motion and absolute-parallax zero-significance. Missing five-parameter astrometry
receives no penalty; it never removes a source. Missing BP/RP flux excess leaves the
AEN component rather than rejecting the source.

The grid tests AEN core weights of 0.25, 0.50, and 0.75; astrometric penalty weights
of 0.0, 0.1, 0.2, and 0.3; and empirical confirmed-UCD completeness targets of 80%,
85%, 90%, and 95%. These are operating-point measurements, not approved values.

### Measured Trade-off

The best equal-cohort point-source retention at each completeness target is:

| Target UCD completeness | Measured | Mean priority retention | Stars | NSS | QSOs |
|---:|---:|---:|---:|---:|---:|
| 80% | 80.0% | 2.22% | 4.19% | 0.00% | 2.48% |
| 85% | 85.1% | 2.56% | 4.95% | 0.00% | 2.73% |
| 90% | 90.3% | 3.73% | 6.48% | 0.00% | 4.71% |
| 95% | 95.4% | 6.84% | 13.33% | 0.00% | 7.20% |

The leading 90% operating point uses 25% AEN rank, 75% flux-excess rank, and a 10%
conditional astrometric penalty. It retains 98.6% of spectroscopic galaxies, as
expected under the approved secondary-galaxy policy. It also retains 90.6% of H II
rows and only 53.6% of uncertain literature UCD candidates. The latter is a
sensitivity warning, not evidence that confirmed-UCD completeness is wrong.

### H II Color Safeguard

A standalone `BP-RP >= 0.8588` development cut retains 90.3% of confirmed UCDs and
19.7% of H II rows. Applying it simultaneously with the 90% core operating point
would retain only 82.3% of confirmed UCDs. It therefore should not be silently added
as a hard primary cut. The safer current treatment is an H II/color review flag or
a separately calibrated second-round morphology/color rejection after the primary
point-source selection.

### Decision Needed Before Freezing

The recommended starting operating point is the measured 90% configuration because
it rejects the three priority point-source cohorts strongly without accepting the
larger stellar leakage of the 95% point. Freezing it still requires project-lead
approval. The exact threshold, rank reference distributions, null behavior, and
version must then move into one shared selector implementation before validation is
opened.

### Reproducibility

- Calibration: `scripts/phase1_literature/calibrate_point_source_selector.py`
- Validator: `scripts/phase1_literature/validate_point_source_selector_calibration.py`
- Components: `data/literature/validation/point_source_selector_components_v1.csv`
- Operating points: `data/literature/validation/point_source_selector_operating_points_v1.csv`
- Summary: `data/literature/validation/point_source_selector_calibration_v1.json`
- Validation: `data/literature/validation/point_source_selector_calibration_validation_v1.json`
<!-- preserved_source_end: docs/point_source_selector_calibration.md -->

<a id="record-point_source_ml_comparison"></a>

> Dated source record: `docs/point_source_ml_comparison.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/point_source_ml_comparison.md -->
## Development-only point-source ML comparison

### Purpose

This experiment tests whether a classical classifier improves on the interpretable
rank score without changing the scientific objective. It is a development-only
comparison, not a frozen selector and not a validation result.

The positive class is the 175 confirmed development UCDs. The three priority
negative cohorts are 525 matched SDSS spectroscopic stars, 1,125 Gaia non-single-
star sources, and 403 spectroscopic QSOs. Each negative cohort receives equal total
weight, irrespective of its row count. Spectroscopic galaxies and H II regions are
secondary stress samples and never enter model fitting or threshold selection.

### Leakage controls

- Five outer grouped folds measure held-out performance; four inner grouped folds
  choose hyperparameters and the threshold targeting 90% confirmed-UCD recall.
- Every matched star inherits the spatial partition group of its matched UCD, so a
  matched UCD-star neighborhood cannot occur on both sides of a fold.
- Preprocessing, missing-value imputation, empirical rank references, model fitting,
  and threshold choice are all fit inside the relevant training fold.
- The 721-row validation partition remains sealed, and none of its Gaia source
  identifiers appears in the prediction artifact.

### Features and models

Regularized logistic regression and shallow histogram gradient boosting use nine
Gaia measurements: transformed astrometric excess noise and its significance,
BP/RP flux-excess factor, measured BP-RP color, transformed RUWE, the two IPD
percentages, and transformed absolute-parallax and proper-motion zero-significance.
Color is therefore a soft learned feature rather than a hard color cut.

Gaia NSS membership, DSC class probabilities, Gaia galaxy/QSO-candidate membership,
and Sersic parameters are excluded from primary inputs because they would be
tautological, circular, or inappropriate parent-sample requirements. The hand-score
baseline uses its previously approved 25/75 excess-noise/flux-excess core and 10%
conditional astrometric penalty, but its empirical references and threshold are
also refit inside grouped folds.

### Measured result

| Method | Confirmed-UCD recall | Stars retained | NSS retained | QSOs retained | Equal-cohort mean retained | Outer-fold UCD recall range |
|---|---:|---:|---:|---:|---:|---:|
| Logistic regression | 93.71% | 7.24% | 0.36% | 4.47% | 4.02% | 81.82–100.00% |
| Shallow gradient boosting | 88.57% | 7.43% | 0.00% | 3.23% | 3.55% | 70.59–100.00% |
| Hand rank score | 89.14% | 6.86% | 0.00% | 4.71% | 3.86% | 76.47–97.06% |

Logistic regression is the only tested method whose pooled outer-fold predictions
meet the nominal 90% recall target, while retaining 4.02% of the equal-weight
priority contaminants. Its improvement over the hand score is modest, and its
81.82–100% fold range shows that the result is not yet stable enough to freeze.
Boosting obtains the lowest contaminant retention but misses the recall target and
has the widest recall instability; it is not preferred at this stage.

The secondary stress results are descriptive only. Majority decisions across the
five outer models retain 98.59% of development spectroscopic galaxies and 89.76%
of H II regions for logistic regression. This is consistent with their declared
later imaging and separate color/morphology treatment; it is not evidence that the
point-source layer solves those contaminants.

### Interpretation and next decision

Classical ML is feasible and regularized logistic regression is a promising
replacement for a sequence of linear cuts. The present comparison does not justify
unsealing validation or freezing a model. The next defensible test is a repeated
grouped nested-CV stability analysis, including coefficient/sign inspection and
performance by magnitude and sky position. Only after that analysis is declared
and reviewed should one candidate implementation and threshold be frozen for the
single withheld-validation evaluation.

That stability analysis was completed on 2026-07-17. The logistic model passes the
predeclared repeated-CV gate, while identifying 11 persistently missed confirmed
UCDs and magnitude/latitude-dependent limitations that require review. See
`docs/point_source_ml_stability.md`; validation remains sealed.

### Reproduction

- Script: `scripts/phase1_literature/compare_point_source_ml.py`
- Validation: `scripts/phase1_literature/validate_point_source_ml.py`
- Command: `uv run python scripts/phase1_literature/compare_point_source_ml.py`
- Predictions: `data/literature/validation/point_source_ml_oof_predictions_v1.csv`
- Fold metrics: `data/literature/validation/point_source_ml_fold_metrics_v1.csv`
- Summary: `data/literature/validation/point_source_ml_comparison_v1.json`
- Validation report: `data/literature/validation/point_source_ml_comparison_validation_v1.json`
- Date: 2026-07-17
<!-- preserved_source_end: docs/point_source_ml_comparison.md -->

<a id="record-point_source_ml_stability"></a>

> Dated source record: `docs/point_source_ml_stability.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/point_source_ml_stability.md -->
## Repeated point-source logistic-regression stability

### Decision status

The provisional logistic model passes the predeclared development stability gate
and is ready for selector-freeze review. It is not yet a frozen selector, and the
721-row validation partition remains sealed.

### Design

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

### Stability result

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

### Coefficient behavior

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

### Persistent failures

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

### Fixed-stratum behavior

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

### 2026-07-17 preliminary source audit

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

### Readiness gate and required review

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

### Reproduction

- Analysis: `scripts/phase1_literature/analyze_point_source_ml_stability.py`
- Validation: `scripts/phase1_literature/validate_point_source_ml_stability.py`
- Command: `uv run python scripts/phase1_literature/analyze_point_source_ml_stability.py`
- Runtime measured on 2026-07-17: 45.19 seconds for the final ten-repeat run
- Summary: `data/literature/validation/point_source_ml_stability_summary_v1.json`
- Validation report: `data/literature/validation/point_source_ml_stability_validation_v1.json`
<!-- preserved_source_end: docs/point_source_ml_stability.md -->

<a id="record-point_source_ml_stability_v2"></a>

> Dated source record: `docs/point_source_ml_stability_v2.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/point_source_ml_stability_v2.md -->
## Point-source ML stability after the Fahrion evidence correction

**Date:** 2026-07-18  
**Partition:** Development only; validation remains sealed  
**Benchmark:** `benchmark_v2` with `benchmark_partition_v1`

### Evidence-corrected training cohort

Benchmark v2 preserves every benchmark row, Gaia feature, spatial group, and
partition from v1. It updates 26 Gaia-linked literature labels after treating
Fahrion table B1 `RV = 0.0` as unavailable evidence: 25 objects become candidates
and B409 becomes a rejected foreground object. Twenty-five of those corrections
occur in development. The high-confidence positive class therefore decreases from
175 to 150 development UCDs. The external spectroscopic-star pool was reused and
rematched, yielding 450 unique controls at the unchanged three-to-one ratio.

### Repeated grouped nested cross-validation

The same ten repeat seeds, five outer folds, four inner folds, nine measured
features, equal priority-cohort weighting, and 90% target recall were rerun.

| Measurement | Minimum | Median | Maximum |
|---|---:|---:|---:|
| Confirmed-UCD recall | 94.67% | 95.33% | 96.00% |
| Equal-cohort priority retention | 3.77% | 4.23% | 4.39% |

All 50 outer fits again select `C = 3.0`, the least-regularized tested boundary,
and all measurement-feature coefficients retain 100% sign agreement. Seven of 150
confirmed UCDs are missed in every repeat, compared with 11 of 175 under the
superseded v1 labels. Persistent priority-contaminant failures comprise 30 matched
spectroscopic stars, four Gaia NSS objects, and 21 spectroscopic QSOs.

The single nested comparison repeat gives logistic regression 95.33% UCD recall
and 4.32% macro priority retention. Histogram gradient boosting falls below the
target at 84.0% recall. The hand-ranked score reaches exactly 90.0% recall with
4.02% macro priority retention. Galaxies and H II regions remain secondary stress
cohorts rather than optimization targets.

### Interpretation

The corrected labels strengthen rather than reverse the development-only result:
logistic regression remains the preferred model family and passes the predeclared
repeat-stability gates. This does not freeze a model or threshold. The unanimous
selection of boundary value `C = 3.0` still requires a higher-C sensitivity test,
and the seven persistent UCD failures require provenance and association review.
Validation performance must remain uninspected until those development decisions
are frozen.

### Artifacts

- Benchmark: `data/literature/benchmarks/gaia_validation_benchmark_v2.csv`
- Development features: `data/literature/benchmarks/gaia_selector_development_features_v2.csv`
- Stellar matches: `data/literature/benchmarks/spectroscopic_stellar_reference_matches_v2.csv`
- ML comparison: `data/literature/validation/point_source_ml_comparison_v2.json`
- Stability summary: `data/literature/validation/point_source_ml_stability_summary_v2.json`
- Stability validation: `data/literature/validation/point_source_ml_stability_validation_v2.json`
<!-- preserved_source_end: docs/point_source_ml_stability_v2.md -->

<a id="record-point_source_ml_v2_failure_audit"></a>

> Dated source record: `docs/point_source_ml_v2_failure_audit.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/point_source_ml_v2_failure_audit.md -->
## Benchmark-v2 persistent UCD failure audit

**Date:** 2026-07-18  
**Scope:** Seven confirmed UCDs missed in all ten development-only logistic repeats  
**Validation partition:** Sealed and uninspected

### Result

The seven failures are not one homogeneous class. All seven retain approved
spectroscopic membership evidence, so this audit does not recommend changing their
UCD classifications. Four Gaia associations are nevertheless unsafe as positive
training examples because the matched Gaia source has highly significant proper
motion. The remaining three are plausible hard UCD examples at `G > 20` and should
remain in development.

| Literature object | Gaia DR3 source | G | Literature-to-Gaia offset | Proper-motion zero-significance | Assessment |
|---|---:|---:|---:|---:|---|
| NGC 1400_1 | 5107392559411455616 | 19.571 | 0.466 arcsec | 14.31 | Suspect foreground superposition or wrong Gaia association |
| NGC1400_2 | 5107470379920956160 | 19.049 | 0.392 arcsec | 44.87 | Suspect foreground superposition or wrong Gaia association |
| Dorado2 | 4778649573525185024 | 19.825 | 0.741 arcsec | 9.91 | Suspect foreground superposition or wrong Gaia association |
| Saifollahi A1 row 32 | 4860354282585368064 | 20.338 | 0.121 arcsec | 11.67 | Suspect foreground superposition despite close positional match |
| Saifollahi A1 row 36 | 4860213682535953792 | 20.456 | 0.112 arcsec | 0.27 | Plausible hard UCD; faint and blue |
| Saifollahi A1 row 39 | 4860359470905910656 | 20.575 | 0.301 arcsec | 0.56 | Plausible hard UCD; faint and moderately extended in Gaia |
| Saifollahi A1 row 59 | 4860293126545559424 | 20.351 | 0.270 arcsec | 2.80 | Plausible hard UCD; resolved-size evidence and Gaia excess noise |

The proper-motion significance uses the full Gaia two-dimensional covariance, not
the two components independently. The four suspect associations have significance
between 9.91 and 44.87, whereas the other three range from 0.27 to 2.80. The three
Fahrion objects have nonzero published velocities. The four Saifollahi objects are
members of the spectroscopic A1 reference sample and have published half-light
radii of 15.2, 5.6, 9.9, and 13.2 pc, respectively. Thus, the conflict is between
the confirmed literature object and the Gaia association, not evidence that the
literature object itself is a foreground star.

### Approved treatment

Retain all seven canonical objects as confirmed UCDs. Mark the four high-motion Gaia
links as `suspect_foreground_superposition_or_wrong_gaia_association` and exclude
those links from selector training until image/epoch-aware association review is
complete. Do not relabel the underlying UCDs. Keep the other three as intentional
hard positive examples. The project lead approved this treatment on 2026-07-18.
The five-case evidence register, including rejected B409, is
`data/literature/sources/ucd_reliability_reviews.json`.

Benchmark v3 implements the decision non-destructively. It retains all 3,857 rows
and changes no published classification or partition assignment, but makes the four
conflicted links ineligible for reliable training. Development then contains 146
reliable confirmed UCDs and 438 rematched stars. Ten-repeat logistic recall is
93.84--96.58% (median 94.18%) and macro priority retention is 3.61--4.00% (median
3.78%). All stability gates pass, although nine reliable UCDs are now persistent
misses and all 50 fits still choose boundary `C = 3.0`.
<!-- preserved_source_end: docs/point_source_ml_v2_failure_audit.md -->

<a id="record-logistic_regularization_sensitivity"></a>

> Dated source record: `docs/logistic_regularization_sensitivity.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/logistic_regularization_sensitivity.md -->
## Logistic regularization sensitivity

**Date:** 2026-07-18  
**Benchmark:** v3 development partition only  
**Validation partition:** Sealed and uninspected

The original grid ended at `C = 3`. All 50 repeated outer fits selected that
boundary, so the nested comparison grid was expanded first through `C = 100` and
then through `C = 3000`.

With the grid ending at 100, four of five outer folds selected 100 and one selected
30. With the grid ending at 3000, four folds selected 3000 and one selected 100.
The resulting pooled logistic recall is 92.47%, and macro priority-contaminant
retention is 2.18%. Individual-fold recall remains 80.77--97.30%, so the apparent
contaminant improvement does not remove fold instability.

This experiment shows that `C = 3` imposed more regularization than the current
inner objective prefers. It does not justify selecting 3000: the preference remains
at the search boundary, and repeatedly enlarging the grid would convert small,
fold-specific retention differences into an effectively unregularized model choice.
The correct next comparison is therefore explicit weakly regularized versus
unregularized logistic regression, assessed for coefficient and prediction
convergence as well as grouped-CV behavior. No `C` or threshold is frozen.

That direct comparison uses `C = 100, 300, 1000, 3000` and an explicitly
unregularized fit. At the fixed grouped-OOF 90% recall operating point, all models
measure 90.41% UCD recall. Macro priority retention is 2.25%, 1.91%, 1.88%, 2.03%,
and 2.03%, respectively. Thus `C = 3000` and the unregularized model already make
identical aggregate selection decisions, while `C = 1000` is slightly better on
this fixed split and retains a finite regularization safeguard. Full-development
probability correlation with the unregularized model rises from 0.955 at `C = 100`
to 0.991 at 1000 and 0.997 at 3000. Raw coefficient vectors converge more slowly,
so coefficient equality is not claimed.

The measured candidate for repeated stability is `C = 1000`, compared directly
against `C = 3000` and unregularized logistic regression. This is a development-only
candidate, not a frozen hyperparameter.

Across ten fixed grouped repeats, all three configurations retain exactly 90.41%
of reliable UCDs. Median macro priority retention is 1.96% for `C = 1000`, 2.11%
for `C = 3000`, and 2.11% for the unregularized fit. `C = 1000` has the lowest
paired retention in seven repeats, versus one for 3000 and two for unregularized.
Its maximum fold coefficient-vector norm is 5.35, compared with 7.01 and 12.94.
The evidence therefore recommends `C = 1000`: it gives the best repeated retention
at identical measured recall and avoids unnecessary coefficient growth. Project-lead
approval is still required before recording it as the frozen regularization policy.

The project lead approved `C = 1000` on 2026-07-18. The frozen regularization and
subsequently approved threshold are recorded in
`data/literature/sources/point_source_logistic_policy_v1.json`.

The frozen threshold is 0.8277833629, defined as the median of ten grouped-OOF
thresholds individually calibrated to retain at least 90% of reliable UCDs. It is
not an in-sample quantile and was not selected using validation data.

Artifacts:

- `data/literature/validation/point_source_ml_comparison_v4.json` (`C <= 100`)
- `data/literature/validation/point_source_ml_comparison_v5.json` (`C <= 3000`)
- `data/literature/validation/point_source_ml_fold_metrics_v5.csv`
- `data/literature/validation/logistic_regularization_convergence_v1.json`
- `data/literature/validation/logistic_regularization_convergence_coefficients_v1.csv`
- `data/literature/validation/logistic_regularization_stability_v1.json`
- `data/literature/validation/logistic_regularization_stability_metrics_v1.csv`
- `data/literature/validation/logistic_regularization_stability_validation_v1.json`
<!-- preserved_source_end: docs/logistic_regularization_sensitivity.md -->

<a id="record-frozen_c1000_persistent_ucd_audit"></a>

> Dated source record: `docs/frozen_c1000_persistent_ucd_audit.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/frozen_c1000_persistent_ucd_audit.md -->
## Frozen-C1000 persistent UCD audit

**Date:** 2026-07-18  
**Model:** `point_source_logistic_policy_v1`, frozen `C = 1000`  
**Scope:** Development only; validation remains sealed

### Result

Ten of 146 reliable confirmed UCDs are missed in every one of ten grouped-OOF
repeats. None warrants removal from the reliable sample on current evidence.

- Five are multiply published Virgo/M87 UCDs. Their Gaia sources have two-parameter
  solutions, no usable parallax or proper motion, `G = 20.92--21.14`, and
  astrometric excess noise of 7.12--10.06 mas. They are genuine faint, extended
  hard positives rather than foreground-like associations.
- Three are Saifollahi spectroscopic A1 compact systems (rows 36, 39, and 59) with
  published half-light radii of 5.6, 9.9, and 13.2 pc. Their Gaia proper-motion
  significance is 0.27, 0.56, and 2.79. They remain valid hard positives.
- One is object 3 from Gregg et al. (2009), with low proper-motion significance
  (0.25), 3.60 mas excess noise, and a spectroscopic confirmation record.
- One is a Voggel et al. NGC 5128 object at `G = 18.37`. Its Gaia proper-motion
  significance is 11.66, but the literature-to-Gaia separation is only 0.019
  arcsec, the BP/RP flux-excess factor is 2.39, and astrometric excess noise is
  1.35 mas. The evidence favors corrupted Gaia astrometry for an extended source
  over a chance foreground association. It remains reliable but should be flagged
  for ancillary-image review.

The persistent misses therefore document the intended completeness cost of a
point-source-contaminant selector: faint or measurably extended UCDs and sources
with incomplete or corrupted Gaia astrometry are the hardest positive cases. They
must remain in completeness accounting. Removing them would bias the selector
toward easy, point-like UCDs.

### Artifacts

- `data/literature/validation/logistic_regularization_frozen_c1000_source_summary_v1.csv`
- `data/literature/validation/logistic_regularization_stability_v1.json`
- `data/literature/validation/logistic_regularization_stability_validation_v1.json`
<!-- preserved_source_end: docs/frozen_c1000_persistent_ucd_audit.md -->

<a id="record-point_source_logistic_model_v1"></a>

> Dated source record: `docs/point_source_logistic_model_v1.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/point_source_logistic_model_v1.md -->
## Point-source logistic model v1

**Date:** 2026-07-18  
**Training scope:** Benchmark-v3 development model-fit rows only  
**Validation:** Sealed and uninspected

The final development model is an L2 logistic-regression pipeline with frozen
`C = 1000` and operating threshold `0.8277833628791744`. It uses the approved nine
Gaia measurement features, median imputation with missingness indicators, standard
scaling, and equal total weight for reliable UCDs versus the three equally weighted
priority contaminant cohorts.

The fit contains 146 reliable UCDs and 1,966 priority contaminants, including 438
matched spectroscopic stars. Apparent full-development recall is 92.47% and macro
priority retention is 1.65%; these are descriptive training-set values, not
validation performance.

The serialized 4.1 KB pipeline reproduces all stored development probabilities to
a maximum absolute difference of `1.11e-16`. Eight checks pass, including model and
prediction hashes, row-order parity, threshold parity, the feature contract, and
absence of every validation Gaia identifier from fitting. The transparent manifest
records imputer statistics, missing-indicator indices, scaler means and scales,
coefficients, intercept, threshold, and provenance hashes.

Artifacts:

- `data/literature/validation/point_source_logistic_model_v1.joblib`
- `data/literature/validation/point_source_logistic_model_v1.json`
- `data/literature/validation/point_source_logistic_development_predictions_v1.csv`
- `data/literature/validation/point_source_logistic_model_validation_v1.json`
<!-- preserved_source_end: docs/point_source_logistic_model_v1.md -->

<a id="record-point_source_selector_integration_v1"></a>

> Dated source record: `docs/point_source_selector_integration_v1.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/point_source_selector_integration_v1.md -->
## Point-source selector integration v1

**Date:** 2026-07-18  
**Model:** `point_source_logistic_model_v1`  
**Threshold:** `0.8277833628791744`

The shared inference implementation is
`scripts/utils/point_source_selector.py`. It loads the frozen serialized pipeline,
verifies its SHA-256 digest, checks the exact nine-feature order, reproduces the
approved feature derivations, and preserves missing values for the fitted median
imputation and missingness indicators.

The Phase IV Gaia query retrieves every raw column needed by the model. It does not
apply the historical astrometric-excess-noise, proper-motion, or color cuts before
inference. It limits the denominator to the complete measured benchmark domain of
`11.26291847229004 <= phot_g_mean_mag <= 21.75798797607422`; these are the measured
minimum and maximum in
`data/literature/benchmarks/gaia_validation_benchmark_v3.csv`, not estimated limits.

Each scored row records:

- `point_source_logistic_probability`;
- `point_source_logistic_selected`; and
- `point_source_selector_version`.

The validator
`scripts/phase4_search/validate_frozen_selector_integration.py` performs seven
checks. It reproduces the stored 2,112 development probabilities with maximum
absolute difference `1.11e-16`, reproduces every threshold decision, verifies the
version and feature contract, confirms all raw query columns, and confirms the two
legacy astrometric prefilters are absent. The machine-readable report is
`data/literature/validation/point_source_logistic_integration_validation_v1.json`.

This integration authorizes use of the frozen selector. It does not validate the
current Phase IV background geometry or significance calculation, which remain
blocked by BT-005 and BT-006 and must be corrected before a scientific pilot rerun.
<!-- preserved_source_end: docs/point_source_selector_integration_v1.md -->

<a id="record-point_source_logistic_validation_v1"></a>

> Dated source record: `docs/point_source_logistic_validation_v1.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/point_source_logistic_validation_v1.md -->
## Point-source logistic validation v1

**Date:** 2026-07-18  
**Evaluation:** One-time frozen validation; complete  
**Retuning:** Prohibited

The project-lead-authorized evaluation applied `point_source_logistic_model_v1`
unchanged to all 721 benchmark-v3 validation rows. The model used frozen
`C = 1000` and threshold `0.8277833628791744`. No validation outcome contributed
to feature choice, training, regularization, threshold calibration, or reliability
labels.

### Primary result

| Cohort | Selected | Total | Retention |
|---|---:|---:|---:|
| Reliable confirmed UCD | 21 | 23 | 91.30% |
| Gaia NSS | 0 | 287 | 0.00% |
| Spectroscopic QSO | 1 | 88 | 1.14% |

Macro retention across the two available priority validation cohorts is 0.57%.
The independent sample therefore meets the predeclared 90% reliable-UCD recall
target while strongly rejecting the point-source contaminants that motivated the
selector.

### Secondary stress cohorts

The selector retains 146/167 spectroscopic galaxies (87.43%), 30/57 compact H II
regions (52.63%), and 1/3 dwarf-host H II regions. This is consistent with their
predeclared role: the Gaia-only model was not optimized to remove extended
extragalactic sources. Imaging, morphology, and photometric modeling remain the
second-round safeguards.

### False negatives and post-validation evidence

Dorado1 has probability 0.000090, 34.57-sigma Gaia proper motion, and a 0.769-arcsec
literature-to-Gaia offset. It is a newly exposed published-UCD/Gaia-counterpart
conflict analogous to Dorado2. The frozen validation label and outcome are retained;
no metric is revised. Any future model generation should quarantine this Gaia link
and use a new independent validation cohort.

M85-HCC1 has probability 0.693918, insignificant Gaia motion, 1.41 mas astrometric
excess noise, RUWE 1.24, and BP/RP flux-excess factor 2.18. It remains a credible
hard UCD and a genuine completeness failure.

### Artifacts

- `data/literature/validation/gaia_selector_validation_features_v1.csv`
- `data/literature/validation/point_source_logistic_validation_predictions_v1.csv`
- `data/literature/validation/point_source_logistic_validation_summary_v1.json`
- `data/literature/validation/point_source_logistic_validation_validation_v1.json`
- `data/literature/sources/point_source_validation_findings_v1.json`
<!-- preserved_source_end: docs/point_source_logistic_validation_v1.md -->

<a id="record-point_source_astrometric_rejection_assessment_v1"></a>

> Dated source record: `docs/point_source_astrometric_rejection_assessment_v1.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/point_source_astrometric_rejection_assessment_v1.md -->
## Point-source astrometric rejection assessment, version 1

### Question

Can a simple Gaia motion rule remove additional stars and QSOs after the frozen
point-source selector, without losing too many reliable ultra-compact dwarfs
(UCDs)?

Here, **astrometric significance** means how far a measured parallax or proper
motion lies from zero after accounting for its reported uncertainty. A distant UCD
should have effectively zero parallax and proper motion, so a large value can be
evidence for a foreground star. However, Gaia can also report misleading motion for
a barely resolved source whose changing image shape shifts its measured center.

The tested second rule uses the larger available value from:

- absolute parallax divided by its uncertainty; and
- the two-dimensional proper-motion distance from zero, including the reported
  correlation between the two proper-motion components.

A source is rejected only when that value is strictly above the trial boundary. If
one measurement is missing, the other can still be used. If both are missing, the
rule does not reject the source.

### Scope and safeguards

The contract in
`data/literature/sources/point_source_astrometric_rejection_assessment_v1.json`
was committed before the measurements were calculated. The analysis uses only the
benchmark-v3 development sample and the ordinary-star development supplement. It
applies `point_source_logistic_model_v1` and its frozen threshold first. It does not
inspect validation data, change selector version 1, use the NGC 4698 star to choose
a boundary, or select a new operating point automatically.

The measured sample contains 146 reliable UCDs, 438 ordinary spectroscopic stars,
1,125 Gaia non-single stars, and 403 spectroscopic QSOs. Galaxies and H II regions
are reported as secondary checks. At least one usable motion measurement exists for
69/146 UCDs, 306/438 ordinary stars, 1,125/1,125 non-single stars, and 321/403 QSOs.

### Measured result

| Treatment | Reliable UCDs passing | Ordinary stars passing | Gaia non-single stars passing | QSOs passing | Equal-weight priority-contaminant fraction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Selector version 1 alone | 135/146 (92.47%) | 13/438 (2.97%) | 0/1,125 (0.00%) | 8/403 (1.99%) | 1.651% |
| 3-standard-deviation reference | 131/146 (89.73%) | 12/438 (2.74%) | 0/1,125 (0.00%) | 7/403 (1.74%) | 1.492% |
| First measured boundary retaining at least 90% of all UCDs: 7.0397 | 132/146 (90.41%) | 13/438 (2.97%) | 0/1,125 (0.00%) | 8/403 (1.99%) | 1.651% |

The 3-standard-deviation reference removes four UCDs that selector version 1 had
retained, while removing one retained ordinary star and one retained QSO. At every
measured boundary that preserves the historical goal of at least 90% reliable-UCD
retention, the priority-contaminant fraction is unchanged from selector version 1.
The full 1,885-boundary curve is preserved in
`data/literature/validation/point_source_astrometric_rejection_curve_v1.csv`.

Five reliable UCD associations exceed 3 standard deviations. All five are from the
Voggel et al. (2020) NGC 5128 catalog (`2020ApJ...899..140V`) and retain the
project's high-confidence spectroscopic classification. Four pass selector version
1 and would be newly removed at the 3-standard-deviation reference; one is already
below the selector threshold. Their Gaia identifiers, coordinates, source rows,
selector scores, and motion measurements are preserved in
`data/literature/validation/point_source_astrometric_rejection_ucd_review_v1.csv`.
This shared origin makes extended-source astrometric corruption a plausible
explanation and does not provide evidence that their published UCD classifications
are wrong.

### Recommendation for review

Do not add a universal hard astrometric rejection boundary to the shared selector.
In this development sample it cannot improve priority-contaminant rejection while
maintaining the project's 90% UCD-retention goal. Preserve parallax and
proper-motion significance as explicit warning flags instead: a high value should
trigger individual imaging and literature review, as the NGC 4698 stellar example
demonstrates, but should not by itself erase a source from the candidate list.

The project lead should review
`figures/phase1/point_source_astrometric_rejection_tradeoff_v1.png` and approve or
reject this no-hard-boundary recommendation before the shared selection workflow is
changed.
<!-- preserved_source_end: docs/point_source_astrometric_rejection_assessment_v1.md -->


