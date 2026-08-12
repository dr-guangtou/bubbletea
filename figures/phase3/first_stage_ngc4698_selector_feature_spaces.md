# Figure: NGC 4698 frozen-selector feature spaces

**Script:** `scripts/phase3_background/plot_first_stage_host_candidates.py`
**Command:** `BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python scripts/phase3_background/plot_first_stage_host_candidates.py`
**Data:** `$BUBBLETEA_EXTERNAL_DATA/bubbletea/gaia_host_profiles_v1/ngc_4698/scored_sources.csv`
**Date:** 2026-08-12

**Description:**
The exact nine measured feature inputs used by the frozen logistic selector, plus its output score and feature missingness. Gray points are rejected Gaia sources and blue points pass the frozen threshold. A--E are transparent review examples, not a candidate rank. Each scatter panel states how many passing sources have both plotted measurements. Display axes use the measured 0.5th to 99.5th percentiles so extreme archive values do not compress the main distribution; no row is removed from counts or analysis outputs. Panel F shows that missing five-parameter astrometry is common among passing sources and is explicitly handled by the frozen model. A high score is a selector output, not a calibrated probability that the source is a real UCD.
