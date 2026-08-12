# Figure: Post-selector astrometric rejection tradeoff

**Script:** `scripts/phase1_literature/analyze_astrometric_rejection.py`
**Command:** `uv run python scripts/phase1_literature/analyze_astrometric_rejection.py`
**Data:** `data/literature/benchmarks/gaia_selector_development_features_v3.csv; data/literature/benchmarks/spectroscopic_stellar_reference_matches_v3.csv; data/literature/validation/point_source_logistic_model_v1.joblib`
**Date:** 2026-08-12

**Description:**
Development-only tradeoff after applying the unchanged point-source selector and then rejecting sources whose available parallax or proper-motion significance exceeds the plotted boundary. Panel A reports every declared cohort; panel B compares reliable-UCD retention with the equal-weight mean retention of ordinary stars, Gaia non-single stars, and QSOs. The orange square is the Liu et al. (2020) 3-standard-deviation reference, not an approved BubbleTea cutoff. Missing astrometry causes no rejection.
