---
date: 2026-08-12
repo: bubbletea
branch: phase1_reassess_astrometric_rejection_20260812
tags:
  - journal
  - phase1
  - selector
  - astrometry
---

## Progress

- Froze the development-only astrometric-rejection contract before calculating any
  retention-versus-rejection result.
- Applied the unchanged selector version 1 first and measured 1,885 exact boundaries
  using the larger available parallax or proper-motion significance.
- Preserved missing parallax and proper motion as unknown; sources with both missing
  were not rejected by the second rule.
- Measured that the 3-standard-deviation literature reference lowers reliable-UCD
  retention from 135/146 to 131/146 while removing one retained ordinary star and
  one retained QSO.
- Verified that every measured boundary retaining at least 90% of all reliable UCDs
  leaves the equal-weight priority-contaminant retention unchanged from selector
  version 1.
- Preserved the five reliable UCD associations above 3 standard deviations in a
  source-level review table; all five originate in the Voggel et al. NGC 5128
  catalog.
- Generated the full tradeoff curve and companion figure; all 19 deterministic
  validation checks and task-specific Ruff and pre-commit checks passed.

## Lessons Learned

- Large Gaia motion significance is a useful warning for individual review but is
  not a safe universal rejection rule for barely resolved UCDs.
- A contaminant-cohort retention fraction does not estimate real-field catalog
  purity because ordinary stars are vastly more common than genuine UCDs.
- A real-host positive control must separate an unbiased contamination-audit sample
  from a deliberately promising new-candidate shortlist.

## Key Issues

- The approved recommendation is to keep selector version 1 unchanged and retain
  significant astrometry as an explicit warning rather than a hard rejection.
- M60 is the next positive-control host. Its two reliable confirmed UCDs test
  end-to-end recovery but are development objects, so their recovery is not an
  independent selector validation.
- The M60 branch must freeze its radial geometry, known-object recovery list,
  representative contamination sampling, and candidate-ranking rules before the
  full passing-source list or ancillary images are inspected.
- Star, non-single-star, QSO, galaxy, and other contaminant treatments require
  separate plain-language definitions and project-lead discussion before any
  exclusion is implemented.
