---
date: 2026-07-15
repo: bubbletea
branch: phase1_repair_crossmatch_geometry_20260715
tags:
  - journal
  - phase1
  - crossmatch
---

## Progress

- Completed BT-007 without changing the legacy or v2 databases and without
  running a full catalog cross-match.
- Added shared spherical selection in `scripts/utils/crossmatch.py`; both matchers
  now use NOIRLab Q3C cones and locally enforce the requested great-circle radius.
- Preserved the existing one-arcsecond Gaia and two-arcsecond Legacy Survey query
  defaults as explicit, uncalibrated parameters.
- Added matched-row ambiguity fields and companion audit products that preserve
  matched, no-match, and query-error outcomes.
- Added `validate_crossmatch_geometry.py` and the measured
  `crossmatch_geometry_validation.json` artifact.
- Verified deterministic cases at 0, +80, and -80 degrees, right-ascension
  wraparound, strict radius inclusion, ambiguity, stable ties, and no-match state.
- Reproduced cached authoritative Gaia separations at -35.92 and +13.26 degrees.
- Verified one bounded live Gaia DR3 query and one bounded live Legacy Survey DR10
  query; both returned one locally valid in-radius row.
- Measured 1,000 three-candidate local selections in 1.575960 seconds.
- Passed scoped Ruff, Ruff formatting, compile, and pre-commit checks for every
  BT-007 Python file; the repository-wide hook still reports 13 unrelated legacy
  script and archived-notebook findings.

## Lessons Learned

- The historical Gaia export's 632 rows are all within one spherical arcsecond,
  but its planar distances differ from spherical distances by up to 0.106154
  arcsec and cover only -45.29 to -40.75 degrees in declination.
- The 917-row Legacy export uses identifiers that do not join to the current
  canonical database and contains no stored match distances, so it is not a
  suitable BT-007 validation reference.
- NOIRLab Data Lab does not support `CONTAINS(POINT, CIRCLE)` on this TAP endpoint;
  its Q3C cone predicate must be used and locally verified.

## Key Issues

- BT-004 remains open: regenerate and synchronize Gaia and Legacy Survey products
  from the stabilized canonical database using the repaired matchers.
- Matching-radius calibration remains separate from BT-007 and must use measured
  reference behavior before the defaults become scientific selection thresholds.
