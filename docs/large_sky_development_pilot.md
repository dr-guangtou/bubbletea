# Frozen large-sky development pilot

**Status:** Field identities frozen before Gaia retrieval
**Date:** 2026-07-19
**Issues:** BT-009, BT-022

## Selection rule

The performance benchmark is `sky_field_0000`, the development field with the
smallest absolute Galactic latitude. `field_id` breaks an exact tie. This uses sky
position only and is intended to exercise a relatively demanding part of the
declared `|b| >= 20` degree domain.

The small pilot contains the benchmark and one stable-hash-selected development
field from each of the other nine combinations of Galactic hemisphere and
equal-area Galactic-latitude band. Those ten fields did not cover two of the six
fixed ecliptic-latitude bands, so the lowest-hash development field in each missing
band was added. The measured pilot therefore contains 12 fields.

The pilot includes both fields with and without count-blind catalog-environment
flags. Those flags remain labels for later sensitivity comparisons, not reasons to
delete a field.

## Isolation and allowed use

All 12 identities were written before any 0.8-degree grid field was queried. Every
field belongs to the 398-field development partition. None of the 102 held-back
validation identifiers is present.

Development fields may be used to benchmark retrieval, measure pre-selector Gaia
conditions, apply the frozen selector, and choose the eventual large-sky model.
Validation fields remain unopened until the model and its evaluation rules are
fixed.

All ten checks pass. They verify unique development identities, the benchmark
rule, complete Galactic and ecliptic coverage, representation of both environment-
flag states, and absence of Gaia-count and selector-result columns.

## Artifacts and reproduction

- `data/results/background/large_sky_development_pilot_fields_v1.csv`
- `data/results/background/large_sky_development_pilot_fields_v1.json`

```bash
uv run python scripts/phase3_background/freeze_large_sky_development_pilot.py
```
