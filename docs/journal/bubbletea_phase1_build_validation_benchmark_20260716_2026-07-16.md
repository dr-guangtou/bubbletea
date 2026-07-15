---
date: 2026-07-16
repo: bubbletea
branch: phase1_build_validation_benchmark_20260716
tags:
  - journal
  - phase1
  - scientific-validation
---

## Progress

- Built `data/literature/benchmarks/gaia_validation_benchmark_v1.csv` with 3,857 unique Gaia DR3 sources across literature UCD, SDSS DR16 galaxy and QSO, Gaia DR3 non-single-star, PHANGS-MUSE H II, and van Zee dwarf-host H II cohorts.
- Fixed immutable HEALPix-based spatial partitions with 3,136 development rows and 721 validation rows.
- Retained 199 confirmed UCDs as primary positives, 619 candidate UCDs as sensitivity-only positives, and 22 uncertain literature roles as sensitivity-only rows.
- Calibrated 175 PHANGS-MUSE associations at 0.3 arcseconds and 13 van Zee associations to 12 unique Gaia sources at 3.0 arcseconds with eight displaced controls per source position.
- Saved source provenance, query text, input hashes, association calibrations, and the exact ADS dwarf-H II search with source dispositions.
- Passed all 32 benchmark release checks without modifying either literature database or running the destructive redundancy script.

## Lessons Learned

- Association radii must follow each catalog's coordinate construction; PHANGS centroids and integer-offset van Zee slit positions require different calibrated radii.
- A source-level uniqueness invariant is necessary because separate published H II positions can select one Gaia source.
- Spiral-host and dwarf-host H II cohorts must remain explicit and removable so environmental coverage is not mistaken for a universal contaminant distribution.

## Key Issues

- `benchmark_v1` is ready for project-lead review before the feature branch is committed, merged, or pushed.
- The next scientific step is BT-002: measure Gaia-feature distributions and label-sensitivity behavior on development data before freezing the selector, while leaving the validation partition untouched.
