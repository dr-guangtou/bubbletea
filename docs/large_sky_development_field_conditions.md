# Large-sky development field conditions

**Date:** 2026-07-19

**Scope:** The 12 frozen development pilot fields only

**Script:** `scripts/phase3_background/measure_large_sky_development_field_conditions.py`

**Outputs:** `data/results/background/large_sky_development_field_conditions_v1.csv`
and its JSON provenance record

## Purpose

These measurements describe the Gaia catalog in each field before the UCD selector
is applied. They test whether variations in Gaia coverage, depth, or total catalog
density help predict how many sources pass the selector. They do not decide whether
a field is a valid scientific background.

## Measurements in plain language

- **Total Gaia source density:** all Gaia sources in the selector's allowed G-magnitude
  range, divided by the exact queried area. It can reflect Milky Way source density,
  crowding, and real astrophysical populations as well as survey behavior. It is not
  a pure observing-condition measurement and cannot become a rigid host-to-control
  matching cut.
- **Mean visibility periods:** the average number of groups of Gaia observations
  separated in time. It describes how often sources in the field were observed on
  distinct occasions.
- **Mean matched transits:** the average number of Gaia focal-plane crossings that
  were associated with a catalog source. It is a second description of observation
  frequency.
- **M10:** the median G magnitude of sources with no more than ten matched transits.
  A fainter value generally indicates that such sparsely observed sources reach
  fainter magnitudes. M10 is a local depth indicator, not a selector cut.

The archive service overflowed when it summed the two integer observation-count
columns directly. The final procedure therefore retrieves each field's compact
source identifier and observation counts, verifies that the retrieval is complete
and unique, and calculates both means locally. The total count is independently
measured and must also equal the count from the existing 19-column retrieval.

## Measured result

All 12 development fields pass all 12 safeguards. The complete run took
66.501269 seconds. The measured ranges are:

| Measurement | Minimum | Maximum |
| --- | ---: | ---: |
| Total Gaia sources per square degree | 2,874.285496 | 41,791.285489 |
| Mean visibility periods | 12.437076 | 24.246461 |
| Mean matched transits | 19.192643 | 56.199413 |
| M10, G magnitude | 20.894909 | 21.158578 |

The full-column and compact pre-selector retrievals have identical source counts
in every field. None of the 102 held-back validation fields was queried or scored.

Three additional field descriptions were calculated later from the verified raw
checkpoints: the 10th percentile, median, and 90th percentile of all G magnitudes
inside the frozen magnitude range. All nine checks pass, all source counts and
identifier fingerprints match the original retrieval, and no archive query was
needed. See `docs/large_sky_development_scale.md`.

## Interpretation limit

The fields were selected to cover sky position, not to estimate correlations
precisely. Their ranges show that the candidate predictors vary enough to test in
the 398-field development experiment. Associations seen among only these 12 fields
must not select a predictor, model, threshold, or scientific background.
