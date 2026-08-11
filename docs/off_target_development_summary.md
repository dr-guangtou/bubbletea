# Frozen development summary rules

**Status:** Summary procedure frozen before validation
**Date:** 2026-07-18
**Issues:** BT-005, BT-009

## What is frozen

The development results will be summarized at three levels:

1. Keep each of the four fields as a separate measurement.
2. Combine east and west fields only when they come from the same host system.
3. Show one all-development total for description only, not as a universal
   background density.

The frozen selector threshold remains `0.8277833628791744`. It will not be changed
after seeing these counts. No development field is promoted to an approved
scientific background.

## Small-count ranges in plain language

When only a few sources are counted, repeating an equivalent measurement can
produce a different count by chance. A Poisson model is the standard simple model
for that random counting variation when events are independent and have one average
rate over a fixed area.

For every field and combined row, the table records 68% and 95% exact central
Poisson ranges. These give ranges of average counts compatible with the observed
small count under that simple model. The corresponding density ranges divide the
count ranges by the exact usable area.

The percentage describes repeated use of the procedure: under the Poisson model,
ranges constructed this way include the true average rate at least that percentage
of the time over many equivalent experiments. It is not the probability that one
particular displayed range contains the true value.

These ranges do **not** include real differences among sky fields, correlated
sources, changes in Gaia observing conditions, or uncertainty in the selector.
They are therefore counting-only ranges, not the final background uncertainty.

## Host-pair and overall summaries

| Summary | Passing sources | Usable area (square degrees) | Density per square degree | 68% counting-only range | 95% counting-only range |
|---|---:|---:|---:|---:|---:|
| NGC 1316 east + west | 26 | 0.062832 | 413.802957 | 333.564113–511.396270 | 270.309830–606.317208 |
| NGC 4698 east + west | 18 | 0.062832 | 286.478970 | 219.901362–370.724732 | 169.785594–452.760282 |
| All development fields, descriptive only | 44 | 0.125664 | 350.140964 | 297.819151–410.960003 | 254.412960–470.047901 |

The all-development value is not a claim that every sky field has the same
background. It is retained so count and area totals can be audited.

## Validation boundary

The four held-back validation identifiers do not appear in the input or output.
When validation is opened, the same seven-row structure, confidence levels,
selector threshold, and host-pair rule must be used. Validation results cannot be
used to rewrite this development summary procedure.

All 16 checks pass. They verify field preservation, east/west pairing, count and
area conservation, interval ordering, zero-count support, unchanged selector
threshold, and continued absence of validation fields.

## Artifacts and reproduction

- `data/results/background/off_target_development_frozen_summary_v1.csv`
- `data/results/background/off_target_development_frozen_summary_v1.json`

```bash
uv run python scripts/phase3_background/freeze_off_target_development_summary.py
```
