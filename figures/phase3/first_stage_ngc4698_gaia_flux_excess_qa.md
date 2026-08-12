# Figure: NGC 4698 Gaia BP/RP flux-excess QA

**Script:** `scripts/phase3_background/plot_first_stage_host_candidates.py`
**Command:** `BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python scripts/phase3_background/plot_first_stage_host_candidates.py`
**Data:** `$BUBBLETEA_EXTERNAL_DATA/bubbletea/gaia_host_profiles_v1/ngc_4698/scored_sources.csv`
**Date:** 2026-08-12

**Description:**
Gaia G magnitude versus the raw BP/RP flux-excess factor, defined as (I_BP + I_RP) / I_G. The layout follows Figure 7 of Liu et al. (2020, ApJS 250, 17; DOI 10.3847/1538-4365/abad91). Gray points are all Gaia sources in the frozen G range, blue open circles pass the frozen BubbleTea point-source contamination selector, and the orange star is example E, visually classified by the project lead as a star. Panel A reproduces the literature-style excess-factor display range; panel B shows the complete measured range on a logarithmic axis. The dotted 1.7 line is Liu et al.'s sample-specific reference and is not a new BubbleTea cut.
