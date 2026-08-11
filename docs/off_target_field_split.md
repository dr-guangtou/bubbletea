# Off-target development and validation fields

**Status:** Bounded diagnostic split frozen
**Date:** 2026-07-18
**Issues:** BT-005, BT-009

## Plain-language definitions

An **off-target field** here is one of the existing 0.1-degree test circles placed
away from a review galaxy. These circles were created to test background methods;
they are not the real galaxy measurement rings.

- **Development fields** may be used to choose or adjust the background method.
- **Validation fields** are held back until those choices are fixed. They then test
  whether the method works in different sky regions.
- **Excluded fields** are the five galaxy-centered test circles. They are not part
  of this off-target split.

“Held back” is a procedural rule: selector results from validation fields must not
be used to choose cuts, matching tolerances, or model settings.

## Frozen assignment

The split identifier is `split_04329736d47c538b7aa0`.

| Partition | Host system | Environment case | Galactic latitude | Fields |
|---|---|---|---:|---|
| Development | NGC 4698 | Isolated principal in the group catalog | +71.345091° | west, east |
| Development | NGC 1316 | Main galaxy of a cataloged group | −56.690166° | west, east |
| Validation | ESO 006-G001 | Isolated principal in the group catalog | −25.222591° | west, east |
| Validation | M60 | Member of a cataloged group | +74.317758° | west, east |

Both off-target circles generated from one host remain in the same partition. This
prevents closely related east/west measurements from appearing on opposite sides of
the method test. Each partition contains one isolated case, one grouped case, one
positive Galactic latitude, and one negative Galactic latitude.

The smallest measured center-to-center separation between a development circle and
a validation circle is 11.949376 degrees. The test-circle diameter is 0.2 degree,
so no development circle overlaps a validation circle.

## What was not used

The assignment script reads only the previously frozen field positions and their
host, environment, and sky coordinates. It does not read the field-condition table,
Gaia source counts, source densities, or frozen-selector results.

Pre-selector field-condition measurements already exist for these positions and
have been discussed previously. They were not inputs to this assignment. No
selected-source count has been calculated or inspected for this split.

## Important limitation

These eight circles form a small first experiment, not a final survey-wide
validation sample. All still have
`eligible_for_scientific_background = false`. The split allows the canonical
selector experiment to test procedure and leakage control; it does not approve any
circle as the background for a real galaxy or calibrate a final Galactic-latitude
limit.

## Artifacts and reproduction

- `data/results/background/off_target_field_split_v1.csv`
- `data/results/background/off_target_field_split_v1.json`

```bash
uv run python scripts/phase3_background/freeze_off_target_field_split.py
```
