# Large-sky development continuation

**Date:** 2026-07-19

**Scripts:**
`scripts/phase3_background/derive_large_sky_development_g_magnitude_summaries.py`
and `scripts/phase3_background/run_large_sky_development_scale.py`

## What was added

The 12 pilot development fields include three fixed descriptions of their
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
no new field, and finished its state check in 0.005078 seconds.

Continued bounded runs completed all 398 development fields. Together they contain
8,001,113 Gaia sources, of which 403,920 pass the frozen selector, over
800.213480 square degrees. The external raw checkpoints contain 2,356 final strips
and 1,640,878,040 CSV bytes. Total Gaia density spans 2,401.289216--618,195.694388
sources per square degree; passing-source density spans
99.970823--37,714.863283 per square degree. These are measured ranges, not
projections from the pilot.

One unusually dense field, `sky_field_0317`, contains 1,242,936 Gaia sources and
75,829 passing sources in 386 final strips. Its adaptive planning repeatedly met
the fixed time ceiling. The planner now saves every completed count measurement,
checks its query and geometry before reuse, and resumes from that point. A local
stop-and-restart test passed all eight safeguards without an archive query. The
live field then resumed across bounded attempts until it completed; earlier failed
attempts remain as permanent external records and are not converted to zero.

The workflow retains a 180-second ceiling for each archive request and a 300-second
ceiling for each complete field attempt. Failed fields are deferred by default so
they cannot consume the first slot of every later batch, and retrying them requires
the explicit `--retry-failed-fields` option. All 17 aggregate safeguards pass. A
final zero-work run verified all 398 external field records, made no new field
attempt, and finished in 0.025172 seconds. All 102 validation fields remain
unopened.

## Interpretation

This validates the complete development measurement, failure preservation, bounded
waiting, planning and retrieval restarts, and local aggregate verification. It does
not select a sky-background model or approve any field as a scientific background.
The next step is to fit and compare the six already frozen model choices using only
these 398 development rows, while keeping all validation results closed.
