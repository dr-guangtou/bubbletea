# Held-back off-target validation result

**Status:** One-time held-back check complete; no field approved as a scientific background
**Date:** 2026-07-19
**Issues:** BT-005, BT-009

## What was tested

The four off-target circles kept out of development were opened after the selector
and summary rules were fixed. The run used the same 19 Gaia columns, G-magnitude
range, selector version, probability threshold, 0.1-degree circle, usable-area
definition, east/west host pairing, and counting-only ranges used for development.
No setting was changed after the validation counts became visible.

Here, **validation** means a one-time check on circles whose selector
probabilities, decisions, and passing-source counts were not used to choose the
procedure. Earlier measurements of total Gaia source density and observing
conditions at these positions were allowed and remain separate.

A source that passes the selector is a retained search candidate, not a confirmed
UCD. These circles are diagnostic measurements and are not approved backgrounds
for a host-galaxy measurement.

## Field results

Each circle has an exact spherical area of 0.031416 square degree. For this Gaia
measurement, usable area equals successfully queried area; no bright-star, dust,
or ancillary-imaging masks are applied.

| Field | Related host | Gaia sources | Sources passing selector | Passing-source density per square degree |
|---|---|---:|---:|---:|
| `2115:east` | ESO 006-G001 | 584 | 16 | 509.295947 |
| `2115:west` | ESO 006-G001 | 460 | 19 | 604.788937 |
| `4:east` | M60 | 130 | 14 | 445.633954 |
| `4:west` | M60 | 59 | 3 | 95.492990 |

The four fields contain 1,233 Gaia sources. Fifty-two pass the selector over
0.125664 square degree, giving a descriptive combined density of 413.802957 per
square degree.

## Frozen summaries

East and west are combined only within the same related host. The ranges below
describe random variation in small independent counts under a Poisson model. They
do not include real differences among sky fields, correlated sources, Gaia
observing-condition differences, or selector uncertainty.

| Summary | Passing sources | Density per square degree | 68% counting-only range | 95% counting-only range |
|---|---:|---:|---:|---:|
| ESO 006-G001 east + west | 35 | 557.042442 | 463.798777–667.425658 | 388.000471–774.711191 |
| M60 east + west | 17 | 270.563472 | 205.896317–352.952862 | 157.613193–433.198328 |
| All validation fields, descriptive only | 52 | 413.802957 | 356.892019–479.163152 | 309.047841–542.647524 |

## Comparison with development

The combined validation density is 1.181818 times the combined development
density of 350.140964 per square degree. It falls outside the development 68%
counting-only range but inside the development 95% range. This is a description,
not a rule that the result must pass.

Individual development fields span 190.985980–572.957941 per square degree, while
validation fields span 95.492990–604.788937. Development host pairs span
286.478970–413.802957, while validation host pairs span 270.563472–557.042442.
Both pairs of ranges overlap.

The result supports the limited claim that the fixed procedure can be executed on
untouched fields without an obvious incompatible total density. It also shows
large field-to-field variation. Four validation circles from two host systems are
therefore too few and too small to define a survey-wide background model, matching
tolerance, or Galactic-latitude limit.

## Safeguards and artifacts

All 24 safeguards pass. They verify the frozen field identities, exclusion of all
development fields from validation queries and outputs, complete retrieval,
unchanged selector and area rules, count and area conservation, the fixed
seven-row summary structure, unchanged development files, and the explicitly
descriptive status of every comparison.

- `data/results/background/off_target_validation_selector_sources_v1.csv`
- `data/results/background/off_target_validation_selector_summary_v1.csv`
- `data/results/background/off_target_validation_frozen_summary_v1.csv`
- `data/results/background/off_target_validation_selector_v1.json`

The recorded run took 12.439364 seconds:

```bash
uv run python scripts/phase3_background/run_off_target_validation_selector.py
```
