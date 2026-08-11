# Multi-field full-column Gaia retrieval validation

**Status:** 5,000-row per-strip retrieval limit validated for development and pilot use
**Date:** 2026-07-18
**Selector:** `point_source_logistic_model_v1`
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`

## Purpose

This test checks whether the adaptive stop-and-restart workflow works with all 19
Gaia columns required by the frozen classifier in fields with different measured
source densities. It uses the previously measured 5,000-row limit for each saved
sky strip.

The circles are performance-test regions, not scientific galaxy apertures. NGC
4698 and ESO 006-G001 use 0.5-degree radii. M60 uses 0.75 degree so the intermediate-
density case contains enough rows to exercise splitting.

## Preserved failed test

The first run used 0.5 degree for all three fields. It measured 2,991 rows for NGC
4698, 3,098 for M60, and 13,010 for ESO 006-G001. Only ESO 006-G001 required
splitting, so the predeclared requirement that at least two fields exercise restart
behavior failed. All identity and column checks passed, but that run was not
accepted.

The requirement was not weakened. The M60 performance-test radius was expanded to
0.75 degree, while NGC 4698 was retained as the below-limit case and ESO 006-G001
as the higher-density case. This geometry change affects only retrieval validation
and cannot define a scientific search radius.

## Accepted measurements

| Field | Test radius (degrees) | Gaia rows | Final strips | Largest strip | Saved CSV bytes | Largest saved strip (bytes) | Elapsed seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| NGC 4698 | 0.50 | 2,991 | 1 | 2,991 | 581,964 | 581,964 | 5.556552 |
| M60 | 0.75 | 6,497 | 2 | 3,326 | 1,255,861 | 639,072 | 8.158222 |
| ESO 006-G001 | 0.50 | 13,010 | 4 | 4,123 | 2,723,286 | 859,723 | 15.873899 |

The fields contain 22,498 Gaia rows in total and produce seven final strips. Every
strip remains below 5,000 rows. The two split fields deliberately stop after their
first saved strip; fresh retrieval instances verify and skip that strip, download
only unfinished strips, and complete successfully. NGC 4698 completes as one strip
without unnecessary splitting.

For every field, the combined full-column rows are unique and their source-
identifier hash exactly matches an independent complete-circle identifier query.
All required classifier columns are present and all classifier probabilities are
finite. The selected-source counts are validation outputs only and are not used for
an astrophysical decision. All 13 checks pass in 29.589341 seconds.

## Decision

Freeze 5,000 rows as the maximum for one saved Gaia retrieval strip in development
and pilot runs using the current 19-column contract. This value is supported by:

- three repeated 5,000-row full-column benchmarks with identical identifiers;
- a successful 10,000-row full-column stress test;
- one unsplit and two split multifield cases;
- controlled full-column stop-and-restart behavior; and
- exact independent source-identifier agreement in all three fields.

This limit controls one archive response, not the total size of a galaxy run.
Multi-degree hosts may require many strips. Every strip must still record its actual
row count, file bytes, query hash, file hash, and completion state. Changing the
Gaia column contract, archive, or data release requires a new benchmark.

## Artifacts and reproduction

- `data/results/background/gaia_full_column_multifield_retrieval_v1.csv`
- `data/results/background/gaia_full_column_multifield_plan_v1.csv`
- `data/results/background/gaia_full_column_multifield_validation_v1.json`

```bash
uv run python scripts/phase3_background/validate_full_column_multifield_retrieval.py
```
