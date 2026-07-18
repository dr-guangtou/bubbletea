# Large-sky development continuation

**Date:** 2026-07-19

**Scripts:**
`scripts/phase3_background/derive_large_sky_development_g_magnitude_summaries.py`
and `scripts/phase3_background/run_large_sky_development_scale.py`

## What was added

The 12 completed development fields now include three fixed descriptions of their
Gaia G-magnitude distributions:

- the magnitude below which 10% of the field's sources lie;
- the median magnitude;
- the magnitude below which 90% of the field's sources lie.

These are calculated from already downloaded sources. The definitions were fixed
before the remaining development fields are measured. They describe each entire
field and are not cuts applied to individual sources.

The continuation script combines four operations for every new development field:

1. divide the circular Gaia request into measured, non-overlapping strips;
2. save and verify the 19 columns required by the frozen source selector;
3. apply that selector locally and count the passing sources;
4. measure the pre-selector field conditions and calculate all fixed magnitude
   summaries.

After a field finishes, its raw files, measured strip plan, hashes, checks, and
plain field summary are written outside the repository under the configured
external-data directory. A later run checks that record and the saved file hashes
before treating the field as complete. An interrupted field reuses valid strips and
continues from the unfinished work.

## Safety rules

- Only rows marked `development` in the frozen grid may be processed.
- The 102 held-back validation identifiers are never placed in the processing list.
- The default command permits zero new remote fields. Starting remote work requires
  an explicit nonnegative `--maximum-new-fields` value.
- Processing order is a reproducible hash of the run version and field identifier.
  It uses no Gaia count, selector result, or host excess.
- A field with incomplete or invalid files is not represented as a zero count.
- This step measures inputs only. It fits no sky-background model and approves no
  field as a scientific background.

## Measured validation

The local magnitude calculation read all 12 completed fields in 1.416442 seconds,
made zero archive queries, and passed all nine safeguards. Every field's source
count and source-identifier fingerprint match the original retrieval.

The continuation first completed a zero-query dry run, importing the 12 existing
fields and passing all 14 run safeguards. It then processed exactly one new field,
`sky_field_0167`, selected by the fixed count-blind order:

- 9,095 Gaia sources in two verified strips;
- 540 sources pass the frozen selector;
- total density 4,523.555389 sources per square degree;
- selected density 268.578330 sources per square degree;
- complete field processing in 13.655484 seconds;
- all ten field checks and all 14 run checks pass.

A subsequent zero-query restart retained 13 completed development fields, started
no new field, and finished its state check in 0.005078 seconds. There are 385
unfinished development fields. All 102 validation fields remain unopened.

## Interpretation

This validates the complete continuation path at the required small scale. It does
not establish the total duration of the remaining run because fields can differ
substantially in source density and the number of required strips. Runtime and
storage must be accumulated from the actual completed fields rather than projected
from this one field.
