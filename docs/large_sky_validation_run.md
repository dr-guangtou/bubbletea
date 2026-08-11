# One-time large-sky validation run

**Date:** 2026-08-11

**Contract script:**
`scripts/phase3_background/freeze_large_sky_validation_run.py`

**Retrieval script:**
`scripts/phase3_background/run_large_sky_validation_scale.py`

**Contract:**
`data/results/background/large_sky_validation_run_contract_v1.json`

## What is being tested

The 102 reserved fields are fixed sky positions whose Gaia selector results were
not used to choose the background procedure. They provide a one-time test of how
well that already chosen procedure works on new parts of the sky.

The primary procedure is direct measurement. For each reserved field, it uses the
398 development fields in the same broad absolute-Galactic-latitude band as the
comparison sample. The comparison sample supplies its measured median, mean, and
central 68% and 95% ranges. It is not a fitted prediction.

The previously fitted sky curve will also be evaluated from the same retrieved
measurements, but only as a secondary diagnostic. It will not be refitted, and its
performance cannot change the primary procedure.

## Rules frozen before the first query

- The contract contains all 102 field identifiers in a count-blind processing
  order. Count-blind means the order was computed from identifiers, not Gaia source
  counts or selector results.
- Retrieval uses the unchanged 19 selector inputs, frozen selector version, exact
  circular area, 5,000-row strip limit, 180-second request limit, and 300-second
  whole-field attempt limit.
- The default command retrieves zero new fields. Every live run requires an
  explicit upper limit on the number of fields attempted.
- Completed fields keep verified raw checkpoints and a receipt outside the
  repository under `BUBBLETEA_EXTERNAL_DATA`.
- A failed or interrupted field keeps a failure receipt and remains missing. It is
  never recorded as zero sources.
- Environment flags are reported but cannot remove fields from the primary result.
- Neither the direct procedure nor the fitted diagnostic may be retuned after a
  reserved result is opened.

## Frozen measurements to report

For both the direct procedure and the fitted diagnostic, report:

- the typical absolute log-density difference;
- the root-mean-square log-density difference;
- the fraction of reserved fields inside the frozen 68% range; and
- the fraction inside the frozen 95% range.

Also preserve every field-level result, list the ten largest absolute differences,
and compare validation performance numerically with development performance.

## Current status

Contract `validation_run_contract_d75e3ddea7013547c088` passes all 11 safeguards.
The zero-query start passes all 17 retrieval safeguards with zero completed fields,
102 remaining fields, and no reserved selector result opened.

The first bounded retrieval then opened only `sky_field_0422`. It measured 11,680
Gaia sources, selected 1,108, used four verified strips, and completed in 35.113735
seconds. A zero-query restart recovered the field from its external receipt, made
no new attempt, and passed all 17 safeguards with one completed field and 101
remaining. Every recorded source and metadata hash was independently verified.

A subsequent ten-attempt batch completed all ten fields without failure in
238.688603 seconds. The cumulative 11-field summary contains 142,703 Gaia sources,
9,908 passing sources, and 42 verified strips. A second zero-query restart reused
all 11 receipts, attempted no field, and passed all 17 safeguards with 91 fields
remaining.

The next 25-attempt batch also completed without failure, taking 712.880576
seconds. Cumulative coverage is 36 fields with 533,034 Gaia sources, 30,972 passing
sources, and 163 verified strips. The longest measured field so far is
`sky_field_0255`: 74,812 Gaia sources in 24 strips and 121.586662 seconds, still
inside the frozen field ceiling. A zero-query restart passed all 17 safeguards with
66 fields remaining.

A 35-attempt continuation completed every field without failure in 828.929929
seconds. Cumulative coverage is 71 fields with 974,992 Gaia sources, 59,951 passing
sources, and 291 verified strips. A zero-query restart passed all 17 safeguards
with exactly 31 fields remaining.

The final 31-attempt batch completed without failure in 989.520193 seconds. The
complete retrieval contains all 102 fields, 1,534,299 Gaia sources, 86,189 passing
sources, 459 verified strips, and 205.079837 square degrees. An independent audit
verified all 102 receipts, every strip hash, and the complete source count. The
final zero-query restart made no new attempt and passed all 17 safeguards.

## One-time evaluation result

The table reports both methods and their differences from development. A typical
factor is the multiplicative difference corresponding to the median absolute log
difference; for example, 1.197 means the measured density typically differs from
the reference by a factor of about 1.197 in either direction.

| Method | Sample | Typical factor | Root-mean-square log difference | Inside 68% range | Inside 95% range |
| --- | --- | ---: | ---: | ---: | ---: |
| Direct latitude-band measurements | Development | 1.182 | 0.397446 | 65.58% | 90.95% |
| Direct latitude-band measurements | Validation | 1.197 | 0.299110 | 61.76% (63/102) | 92.16% (94/102) |
| Frozen fitted diagnostic | Development | 1.112 | 0.219669 | 67.84% | 94.97% |
| Frozen fitted diagnostic | Validation | 1.128 | 0.157033 | 64.71% (66/102) | 98.04% (100/102) |

During development, each field was tested against a reduced pool because its whole
sky block had to be excluded from training. Validation uses all 398 already frozen
development measurements because every reserved sky block is separate from them.
The resulting validation pools contain 75--85 fields. The comparison therefore
tests the final deployed reference rather than recreating the smaller development
folds.

For the direct method, validation minus development is +0.013045 in median absolute
log difference, -0.098336 in root-mean-square log difference, -3.81 percentage
points in 68% coverage, and +1.20 percentage points in 95% coverage. The validation
95% coverage is closer to 95% than the development value, although it remains below
95%; no range was changed after seeing this result.

The eight direct results outside the frozen development 95% ranges are
`sky_field_0016`, `sky_field_0215`, `sky_field_0236`, `sky_field_0256`,
`sky_field_0269`, `sky_field_0290`, `sky_field_0332`, and `sky_field_0422`. They
remain ordinary validation outcomes and are not deleted. The two fitted-diagnostic
results outside its 95% range are `sky_field_0249` and `sky_field_0256`.

For the fitted diagnostic, the corresponding differences are +0.014158, -0.062636,
-3.13 percentage points, and +3.06 percentage points. The fitted diagnostic is
numerically tighter on these 102 fields, but it remains secondary. That role was
fixed before validation, and the development analysis had already shown that a
smooth fitted curve can fail badly for an extreme field.

The count-blind environment flag is descriptive only. Flagged validation fields
happen to have smaller direct errors than unflagged fields in this fixed sample;
this does not show that an environment intersection improves prediction and is not
used to remove or reweight any field.

All 20 evaluation safeguards pass. Every field-level direct comparison pool,
measured range, fitted diagnostic value, and residual is preserved in
`data/results/background/large_sky_validation_reference_v1.csv`.
