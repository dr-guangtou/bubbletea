# Point-source ML stability after the Fahrion evidence correction

**Date:** 2026-07-18  
**Partition:** Development only; validation remains sealed  
**Benchmark:** `benchmark_v2` with `benchmark_partition_v1`

## Evidence-corrected training cohort

Benchmark v2 preserves every benchmark row, Gaia feature, spatial group, and
partition from v1. It updates 26 Gaia-linked literature labels after treating
Fahrion table B1 `RV = 0.0` as unavailable evidence: 25 objects become candidates
and B409 becomes a rejected foreground object. Twenty-five of those corrections
occur in development. The high-confidence positive class therefore decreases from
175 to 150 development UCDs. The external spectroscopic-star pool was reused and
rematched, yielding 450 unique controls at the unchanged three-to-one ratio.

## Repeated grouped nested cross-validation

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

## Interpretation

The corrected labels strengthen rather than reverse the development-only result:
logistic regression remains the preferred model family and passes the predeclared
repeat-stability gates. This does not freeze a model or threshold. The unanimous
selection of boundary value `C = 3.0` still requires a higher-C sensitivity test,
and the seven persistent UCD failures require provenance and association review.
Validation performance must remain uninspected until those development decisions
are frozen.

## Artifacts

- Benchmark: `data/literature/benchmarks/gaia_validation_benchmark_v2.csv`
- Development features: `data/literature/benchmarks/gaia_selector_development_features_v2.csv`
- Stellar matches: `data/literature/benchmarks/spectroscopic_stellar_reference_matches_v2.csv`
- ML comparison: `data/literature/validation/point_source_ml_comparison_v2.json`
- Stability summary: `data/literature/validation/point_source_ml_stability_summary_v2.json`
- Stability validation: `data/literature/validation/point_source_ml_stability_validation_v2.json`

