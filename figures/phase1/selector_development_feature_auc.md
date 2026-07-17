# Figure: Development-only univariate Gaia feature discrimination

**Script:** `scripts/phase1_literature/analyze_selector_development.py`
**Command:** `uv run python scripts/phase1_literature/analyze_selector_development.py`
**Data:** `data/literature/benchmarks/gaia_selector_development_features_v1.csv`
**Date:** 2026-07-16

**Description:**
Direction-adjusted univariate ROC AUC for 175 confirmed UCDs versus each development-partition contaminant role. Values approach one when a feature separates the two roles in either direction and 0.5 for no rank separation. The companion metrics table reports deterministic stratified-bootstrap 95% confidence intervals from 500 resamples. Feature definitions and safeguards are recorded in docs/gaia_selector_features.md.
