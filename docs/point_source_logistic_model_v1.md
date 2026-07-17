# Point-source logistic model v1

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

