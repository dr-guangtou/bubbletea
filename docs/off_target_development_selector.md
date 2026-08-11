# Frozen-selector results for off-target development fields

**Status:** Development fields measured; validation selector results remain unopened
**Date:** 2026-07-18
**Issues:** BT-005, BT-009

## What was done

The four frozen development circles were queried for all 19 Gaia columns required
by `point_source_logistic_model_v1`. The selector was then applied locally, using
its frozen probability threshold of `0.8277833628791744`.

A source that **passes the frozen selector** has a model probability at or above
that threshold. It is a search candidate, not a confirmed UCD. These small circles
measure the selector's off-target behavior and cannot establish an astrophysical
background by themselves.

## Measured development results

Each circle has a 0.1-degree radius and an exact spherical area of 0.031416 square
degree. Gaia usable area equals queried area, with no imaging masks.

| Field | Host system | Gaia sources | Sources passing selector | Passing-source density per square degree |
|---|---|---:|---:|---:|
| `1:east` | NGC 1316 | 81 | 18 | 572.957941 |
| `1:west` | NGC 1316 | 110 | 8 | 254.647974 |
| `58:east` | NGC 4698 | 122 | 12 | 381.971960 |
| `58:west` | NGC 4698 | 100 | 6 | 190.985980 |

The four fields contain 413 Gaia sources in total; 44 pass the selector over a
combined usable area of 0.125664 square degree. The observed field-to-field
difference must be tested explicitly; four fields from only two host systems do not
by themselves show that one common density is invalid. No matching tolerance or
final background model is selected by this measurement alone.

## Validation isolation

The held-back identifiers are `2115:east`, `2115:west`, `4:east`, and `4:west`.
The script checks these identifiers before every query and again in both output
tables. None was queried or summarized.

Pre-selector observing-condition measurements already exist for those sky
positions. “Unopened” here specifically means that no frozen-selector probability,
decision, or selected-source count has been produced for the held-back fields.

## Validation result

All 18 checks pass in 10.560200 seconds. They verify:

- exactly the four frozen development fields were queried;
- the four held-back identifiers and their frozen host-role assignments are intact;
- no held-back field appears in a query or output;
- measured and retrieved row counts agree;
- all 19 raw Gaia columns and selector outputs are present;
- source identifiers are unique and have recorded fingerprints;
- probabilities are finite and use the frozen selector version;
- summary counts match the saved source decisions; and
- Gaia queried and usable areas agree, with zero missing or masked area.

## Artifacts and reproduction

- `data/results/background/off_target_development_selector_sources_v1.csv`
- `data/results/background/off_target_development_selector_summary_v1.csv`
- `data/results/background/off_target_development_selector_v1.json`

Reproduction deliberately re-queries only development fields:

```bash
uv run python scripts/phase3_background/run_off_target_development_selector.py
```
