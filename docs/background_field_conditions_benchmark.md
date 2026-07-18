# Gaia field-condition benchmark

**Status:** Bounded diagnostic completed; matching rules not yet fixed  
**Date:** 2026-07-18  
**Host:** NGC 4698  
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`  
**Artifacts:**
`data/results/background/background_review_hosts_v1.csv`,
`data/results/background/background_review_hosts_v1.json`,
`data/results/background/background_field_conditions_benchmark_v1.csv` and
`data/results/background/background_field_conditions_benchmark_v1.json`

## Question

Does placing comparison patches at exactly the same Galactic latitude as a target
also make their Gaia coverage and total Gaia source density effectively identical?

This benchmark does not apply the UCD selector and does not count UCD candidates.
It measures only field properties that can be chosen before seeing a possible
galaxy excess.

## Test

The test uses a circular patch of radius 0.1 degree centered on NGC 4698 and two
same-size comparison patches placed east and west of it. All three patch centers
have the same Galactic latitude, 71.345091 degrees. The comparison-patch separation
and the group-radius multiplier are temporary test values, not approved scientific
rules.

The script measures:

- the number and sky density of all Gaia sources in the selector's allowed G
  magnitude range, before applying the selector;
- the average number of visibility periods and matched astrometric transits;
- ecliptic latitude; and
- `M10`, the median G magnitude of Gaia sources with no more than ten matched
  astrometric transits in the patch. Here `M10` is used only as a local Gaia-depth
  indicator: a brighter value usually means shallower coverage.

## Measured result

| Patch | Gaia sources | Sources per square degree | Mean visibility periods | Mean matched transits | M10 (G magnitude) |
|---|---:|---:|---:|---:|---:|
| NGC 4698 target | 121 | 3851.55 | 15.98 | 39.12 | 21.187 |
| West comparison | 100 | 3183.10 | 12.07 | 37.97 | 21.093 |
| East comparison | 122 | 3883.38 | 14.46 | 35.92 | 21.102 |

All six validation checks passed. The three patches had positive measured area,
complete retrieval of the low-transit sample, no missing values in either
observation-count column, and no UCD-selector output in the query contract. The
complete run took 11.19 seconds on 2026-07-18.

## Interpretation

Matching Galactic latitude alone did not make the three fields identical. The west
comparison contained 100 Gaia sources, versus 121 and 122 in the target and east
patches, and it had fewer visibility periods on average. The three `M10` values
were much closer, spanning 0.094 magnitude.

This is only one target and two comparison patches. It shows why Gaia coverage and
total source density should be measured rather than assumed, but it cannot tell us
which diagnostic is most useful or set an acceptable mismatch. Those decisions
require a larger count-blind development sample and later validation against the
frozen selector on spatially separate fields.

## Reproduction

```bash
uv run python scripts/phase3_background/build_background_review_hosts.py
uv run python scripts/phase3_background/benchmark_gaia_field_conditions.py
```
