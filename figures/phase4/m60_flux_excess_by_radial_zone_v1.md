# Figure: M60 Gaia flux excess by radial zone

**Script:** `scripts/phase4_search/plot_m60_flux_excess_by_radius.py`
**Command:** `BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python scripts/phase4_search/plot_m60_flux_excess_by_radius.py`
**Data:** `$BUBBLETEA_EXTERNAL_DATA/bubbletea/m60_positive_control_v1/scored_sources.csv; data/results/radial_search/m60_positive_control_visual_audit_sample_v1.csv`
**Date:** 2026-08-12

**Description:**
Gaia G magnitude versus the raw BP/RP flux-excess factor, defined as (I_BP + I_RP) / I_G, for all 4,920 M60 sources retained by selector version 1. Panels preserve the four frozen radial zones. Gray points show the complete retained population, blue open circles show the separately frozen representative visual-audit sample, and orange stars show the two reliable M60 UCD controls. Each panel reports finite plotted counts; rows without a usable excess-factor measurement remain in all scientific tables. The dotted 1.7 line is the Liu et al. (2020) sample-specific reference, not a BubbleTea selection boundary. High raw flux excess can reflect resolved structure, crowding, or measurement problems and does not by itself establish a galaxy classification.
