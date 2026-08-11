---
date: 2026-08-11
repo: bubbletea
branch: phase3_background_design_20260718
tags:
  - journal
  - phase3
  - background
  - gaia
---

## Progress

- Completed verified selector measurements for all 398 large-sky development fields:
  8,001,113 Gaia sources, 403,920 passing sources, and 800.213480 square degrees.
- Compared six frozen fitted models, preserved the extreme `sky_field_0317` result,
  and reassigned the selected fitted model to a secondary diagnostic role.
- Froze and compared three direct random-field procedures without opening any of the
  102 reserved validation fields or making an archive query.
- Selected the simplest procedure: use all measured development fields in the same
  broad absolute-Galactic-latitude band and preserve their identities and densities.
- Measured a typical held-out density difference of a factor of 1.182; the direct
  68% and 95% ranges contained 65.6% and 91.0% of development fields.
- Required future host reports to show both a valid outer-annulus density and the
  direct random-field distribution, including their numerical difference and ratio.

## Lessons Learned

- Direct measurements are a clearer primary background reference than a fitted
  curve when the comparison-field densities are already available.
- An extreme field should remain an explicit out-of-range result instead of being
  deleted or hidden by a smooth prediction.
- Automatic repository-wide lint fixes must be scoped carefully because legacy
  files can be rewritten before pre-existing failures are reported.

## Key Issues

- The 102 reserved fields remain unopened and require one-time evaluation on a new
  branch without changing the frozen direct procedure.
- The measured 95% development range achieved 91.0% coverage; the reserved-field
  evaluation must report whether that shortfall persists without retuning.
- Real host work still requires calibration of the central exclusion and outer
  annuli before the official nearby-galaxy run.
- Repository-wide pre-commit remains blocked by 13 pre-existing Ruff errors in
  archived notebooks and older scripts; all task-specific hooks pass.
