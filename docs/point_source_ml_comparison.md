# Development-only point-source ML comparison

## Purpose

This experiment tests whether a classical classifier improves on the interpretable
rank score without changing the scientific objective. It is a development-only
comparison, not a frozen selector and not a validation result.

The positive class is the 175 confirmed development UCDs. The three priority
negative cohorts are 525 matched SDSS spectroscopic stars, 1,125 Gaia non-single-
star sources, and 403 spectroscopic QSOs. Each negative cohort receives equal total
weight, irrespective of its row count. Spectroscopic galaxies and H II regions are
secondary stress samples and never enter model fitting or threshold selection.

## Leakage controls

- Five outer grouped folds measure held-out performance; four inner grouped folds
  choose hyperparameters and the threshold targeting 90% confirmed-UCD recall.
- Every matched star inherits the spatial partition group of its matched UCD, so a
  matched UCD-star neighborhood cannot occur on both sides of a fold.
- Preprocessing, missing-value imputation, empirical rank references, model fitting,
  and threshold choice are all fit inside the relevant training fold.
- The 721-row validation partition remains sealed, and none of its Gaia source
  identifiers appears in the prediction artifact.

## Features and models

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

## Measured result

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

## Interpretation and next decision

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

## Reproduction

- Script: `scripts/phase1_literature/compare_point_source_ml.py`
- Validation: `scripts/phase1_literature/validate_point_source_ml.py`
- Command: `uv run python scripts/phase1_literature/compare_point_source_ml.py`
- Predictions: `data/literature/validation/point_source_ml_oof_predictions_v1.csv`
- Fold metrics: `data/literature/validation/point_source_ml_fold_metrics_v1.csv`
- Summary: `data/literature/validation/point_source_ml_comparison_v1.json`
- Validation report: `data/literature/validation/point_source_ml_comparison_validation_v1.json`
- Date: 2026-07-17
