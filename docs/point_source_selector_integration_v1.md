# Point-source selector integration v1

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
