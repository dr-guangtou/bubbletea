# Random-field background comparisons and validation

**Consolidated:** 2026-10-12  
**Role:** Topic-organized development evidence, not a replacement for current scientific requirements.

[Science guide](../science_guide.md) · [Current status](../current_status.md) · [Documentation audit](documentation_audit.md)

## Current reading guidance

Direct Galactic-latitude-band field measurements are the primary large-sky reference. A fitted sky model is diagnostic only, following its extreme-field failure. All 398 development and 102 reserved validation fields were processed. The reports below preserve the earlier model contract, comparison, approved change of method hierarchy, and final independent test.

## Dated evidence

Each section below retains an original report's scientific content, measurements,
commands, and limitations. Status statements apply to that report's original date;
read the guidance above and current SPEC before following an old next step.

<a id="record-large_sky_model_comparison_contract"></a>

> Dated source record: `docs/large_sky_model_comparison_contract.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/large_sky_model_comparison_contract.md -->
## Large-sky background model comparison

**Date:** 2026-07-19

**Script:** `scripts/phase3_background/freeze_large_sky_model_comparison.py`

**Machine-readable contract:**
`data/results/background/large_sky_model_comparison_contract_v1.json`

**Contract identifier:** `model_contract_8da80ba5e4bd6d3027e6`

### What is being predicted

For each field, the measured quantity is the number of sources passing the frozen
Gaia selector per square degree of successfully queried area. The model works with
the count and exact area together so that fields with more measured area carry the
appropriate statistical weight. An incomplete field keeps a failure record and is
left out of fitting; it is never changed to a zero count.

### Models to compare

The models are ordered from simplest to most flexible:

1. One average rate for the entire development sky.
2. A rate that can change smoothly with distance from the Milky Way plane.
3. A sky-position model that also uses Galactic hemisphere and longitude, plus
   distance from the ecliptic plane.
4. The position model plus measured Gaia conditions: total Gaia source density,
   M10, mean visibility periods, mean matched transits, and three summaries of the
   G-magnitude distribution.
5. A limited tree model using the same information. This checks whether simple
   nonlinear relationships improve prediction enough to justify a less transparent
   model.
6. A diagnostic version that adds the count-blind environment flag. This comparison
   cannot approve or delete a background field and cannot be selected as the main
   model.

A smooth curve is used where a straight-line relationship would be unnecessarily
restrictive. The allowed curve complexity and the limited tree settings are fixed
in the machine-readable contract before the 398-field measurements.

### How prediction is tested

The 398 development fields belong to 95 broad sky blocks. All fields in one block
stay together throughout testing, which prevents nearby fields from appearing on
both sides of the same test.

- An **outer grouped fold** holds out whole development sky blocks, fits the model
  on the other blocks, and measures how well it predicts the held-out blocks. Five
  different outer splits provide the performance estimate.
- An **inner grouped fold** operates only inside the current outer training set. Its
  sole job is to choose among the already declared curve, penalty, or tree settings.
  Four inner splits are used. Inner results are not reported as final performance.

The main score is mean Poisson deviance, which compares predicted and observed
counts while respecting the count nature of the data; lower is better. Supporting
checks report typical and root-mean-square log-density errors, residual patterns by
Galactic and ecliptic latitude, and whether the stated 68% and 95% prediction ranges
contain the expected fractions of held-out fields.

### Choosing the final development model

The lowest average outer-fold deviance identifies the measured best score. The
chosen model is the simplest candidate whose score is statistically indistinguishable
from that best score under the predeclared one-standard-error rule. In plain
language, a more complicated model is used only when its improvement is larger than
the field-to-field uncertainty in the comparison.

After selection, the development fit, all data transformations, and the method for
constructing prediction ranges are frozen. Only then may the 102 held-back fields be
opened once for a final check. They cannot be used to revise the model.

### Current status

The frozen comparison has now been run on all 398 development fields. The selected
model combines sky position with measured Gaia conditions and uses three spline
knots with `alpha = 0.1`. All 22 fitting safeguards pass. The extreme flagged field
`sky_field_0317` is retained and documented rather than deleted; it dominates one
outer fold and limits the model's applicability in unusual crowded or physically
associated regions. No validation selector result has been opened, and no
large-sky field has been approved as a scientific background. See
`docs/large_sky_development_model_comparison.md`.

After reviewing the extreme-field failure, this fitted model was reassigned on
2026-08-11 to a secondary diagnostic role. It can describe smooth trends, but it
does not supply the primary background value. The primary large-sky reference is
now the preserved distribution of directly measured development fields in the
same broad absolute-Galactic-latitude band. See
`docs/large_sky_direct_background_comparison.md`.
<!-- preserved_source_end: docs/large_sky_model_comparison_contract.md -->

<a id="record-large_sky_development_model_comparison"></a>

> Dated source record: `docs/large_sky_development_model_comparison.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/large_sky_development_model_comparison.md -->
## Large-sky development model comparison

**Date:** 2026-07-19

**Script:** `scripts/phase3_background/fit_large_sky_development_models.py`

**Command:**
`uv run python scripts/phase3_background/fit_large_sky_development_models.py`

**Input:**
`data/results/background/large_sky_development_scale_summary_v1.csv`

**Machine-readable result:**
`data/results/background/large_sky_development_model_comparison_v1.json`

### Outcome and revised role

The selected development model combines sky position with measured Gaia observing
conditions. It uses Galactic and ecliptic latitude, Galactic hemisphere and
longitude, total Gaia source density, the local depth indicator called M10, mean
visibility periods, mean matched transits, and three summaries of the Gaia G
magnitude distribution.

The final setting has three spline knots and `alpha = 0.1`. A spline is a smooth
curve assembled from connected pieces; three knots allow a modest curved latitude
trend without a highly flexible shape. `Alpha` is the strength of a penalty that
discourages unnecessarily large regression coefficients. It is a model-stability
setting, not a source-selection cut.

This model is now a diagnostic interpolation only. Directly measured random-field
distributions are the primary large-sky reference; see
`docs/large_sky_direct_background_comparison.md`. The fitted model remains useful
for showing smooth trends and as a robustness comparison, but it does not replace
the measured comparison-field densities.

### Predictive comparison

All fields in one broad sky block stayed together. Each score therefore measures
prediction on sky blocks that were not used to fit that fold or choose its setting.
Lower mean Poisson deviance is better.

| Model | Mean deviance | Standard error | Typical absolute log error | Selected |
| --- | ---: | ---: | ---: | --- |
| One average rate | 798.187 | 717.896 | 0.318 | No |
| Galactic-latitude curve | 815.531 | 711.334 | 0.300 | No |
| Sky-position curves | 1,028.377 | 657.758 | 0.293 | No |
| Sky position plus Gaia conditions | 320.728 | 304.598 | 0.106 | Yes |
| Limited nonlinear tree | 664.273 | 617.150 | 0.123 | No |
| Gaia-condition model plus environment flag | 323.176 | 306.884 | 0.108 | Diagnostic only |

The Gaia-condition regression has the lowest eligible score. Its one-standard-error
threshold is 625.326; no simpler eligible model lies below that threshold. The
environment-flag version has a similar score but was declared diagnostic before
measurement and cannot become the primary model.

### Prediction ranges

Grouped predictions for fields excluded from their current fit give these frozen
observed-to-predicted multipliers:

- central 68% range: 0.858 to 1.174;
- central 95% range: 0.685 to 1.374.

For example, a prediction of 100 passing sources per square degree corresponds to
a development residual range of about 86--117 for the central 68% and 68--137 for
the central 95%. These are empirical field-to-field ranges from the development
sample. They are not yet independently validated confidence intervals.

### Important instability

Four outer test folds have mean Poisson deviances between 14.030 and 18.337. The
fifth has 1,539.116 because it contains an extreme development field,
`sky_field_0317`. That field has an observed passing-source density of
37,714.863 per square degree, while the model fitted without its sky block predicts
3,265.938 per square degree. It is marked by the pre-existing count-blind
environment flag and was retained exactly as required; it was not converted to a
failure, removed, or used to alter the frozen comparison.

This one field also drives the large residual summaries in Galactic equal-area band
1 and the 75--90 degree absolute-ecliptic-latitude band. When the selected model is
tested only on the 163 unflagged development fields, its mean outer-fold deviance is
66.522 with a standard error of 57.344. That sensitivity result is substantially
lower but remains diagnostic because excluding flagged fields was not allowed to
choose the primary model.

The practical conclusion is that Gaia observing conditions explain most ordinary
development-field variation, but the model does not absorb every extreme crowded
or physically associated sky region. The eventual applicability rule must retain
this limitation rather than present one smooth prediction as universally reliable.

### Safeguards and status

The local 60-field synthetic comparison passed all ten checks before the real fit.
The full comparison completed in 220.35 seconds with all 22 safeguards passing and
no convergence warning. All transformations were fitted within training data, all
six frozen model forms were evaluated, and residuals were recorded by Galactic
band, ecliptic band, and environment-flag state.

The fitted development model and its prediction ranges are now frozen. No field is
approved as a scientific background, and selector results for all 102 held-back
validation fields remain unopened.

### Reserved-field diagnostic result

The earlier plan to validate this fitted model as the primary background procedure
was superseded on 2026-08-11. The 102 reserved fields were later opened once to
evaluate the frozen direct procedure, with this serialized model included only as a
secondary diagnostic. Its validation typical difference is a factor of 1.128;
66/102 fields lie inside its frozen 68% range and 100/102 inside its frozen 95%
range. It was not refitted or retuned and remains secondary. See
`docs/large_sky_validation_run.md`.
<!-- preserved_source_end: docs/large_sky_development_model_comparison.md -->

<a id="record-large_sky_direct_background_comparison"></a>

> Dated source record: `docs/large_sky_direct_background_comparison.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/large_sky_direct_background_comparison.md -->
## Direct random-field background comparison

**Date:** 2026-08-11

**Contract script:**
`scripts/phase3_background/freeze_large_sky_direct_background_contract.py`

**Comparison script:**
`scripts/phase3_background/compare_large_sky_direct_backgrounds.py`

**Input:**
`data/results/background/large_sky_development_scale_summary_v1.csv`

**Machine-readable result:**
`data/results/background/large_sky_direct_background_comparison_v1.json`

### Why this replaced a model as the primary reference

The density of Gaia sources passing the frozen selector can be measured directly in
random sky fields. A fitted mathematical curve is therefore not required to supply
the primary large-sky background reference. The curve remains useful as a secondary
check, but it can hide extreme fields behind a smooth prediction.

The direct procedure preserves the actual comparison fields and their measured
densities. It reports a median, an arithmetic mean, and central 68% and 95% ranges.
These ranges show real field-to-field variation; they are not model confidence
intervals.

### Procedures compared

The rules were frozen before their performance was measured:

1. use all training fields in the same broad absolute-Galactic-latitude band;
2. additionally require the same low, middle, or high third of total Gaia source
   density; or
3. use the 20 nearest training fields in Galactic latitude and total Gaia source
   density.

All fields in the same broad sky block stayed together. A field was therefore
tested only against comparison fields outside its held-out block.

### Result

| Procedure | Mean fold typical log error | Overall typical log error | Root-mean-square log error | 68% range coverage | 95% range coverage | Typical pool size |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Galactic-latitude band | 0.1657 | 0.1671 | 0.3974 | 65.6% | 91.0% | 61 |
| Latitude and Gaia-density third | 0.1647 | 0.1673 | 0.3790 | 60.3% | 85.9% | 20 |
| Twenty nearest fields | 0.1647 | 0.1564 | 0.3527 | 61.1% | 85.9% | 20 |

The latitude-band procedure is selected by the frozen one-standard-error rule. Its
score differs from the best measured score by only 0.0010, while it is simpler,
uses roughly three times as many comparison fields, and gives better measured-range
coverage. Its overall typical absolute error corresponds to a density factor of
1.182, or about an 18% difference between a held-out field and the comparison-pool
median.

The central ranges do not contain exactly 68% and 95% of held-out fields. Their
measured coverage is 65.6% and 91.0%, respectively. This shortfall must remain
visible and can be checked once on the still-unopened validation fields.

### Extreme flagged field

`sky_field_0317` has a measured passing-source density of 37,714.863 per square
degree. Its 58 same-latitude comparison fields have a median of 390.433 and a
central 95% range of 177.324--659.385 per square degree. The field is therefore a
factor of 96.597 above the median and far outside the measured range.

This is more informative than forcing a smooth prediction: the direct procedure
plainly identifies the field as unlike ordinary random fields in its latitude band.
The field remains preserved with its count-blind environment flag. It is not
deleted, converted to zero, or allowed to redefine the general background.

### Interface with a real host

For each real galaxy, the future result must report both:

- the density measured in a valid outer annulus around the galaxy; and
- the median, mean, central ranges, and field count from the direct random-field
  reference.

It must also report the annulus density minus the random-field median and their
ratio. Neither measurement is forced to agree with the other. A missing or invalid
outer annulus remains unavailable, not zero.

The random-field reference applies only to `|b| >= 20 degrees`, the domain actually
measured by the frozen grid. The real outer-annulus boundaries and central excluded
region still require separate calibration before the official host run.

### Status

The synthetic 300-field validation passes all ten safeguards in 0.666 seconds.
The 398-field comparison passes all 17 safeguards in 1.405 seconds and makes no
archive query. All comparison-field identities and measured densities are retained.
The fitted model is now a diagnostic only. No field is approved as a scientific
background. At this design-freeze point, all 102 large-sky validation fields were
still unopened for a new branch.

The reserved fields were subsequently opened once under the unchanged procedure.
The direct validation typical difference is a factor of 1.197, with 63/102 fields
inside the development 68% measured ranges and 94/102 inside the 95% ranges. The
procedure was not retuned and remains the primary large-sky reference. See
`docs/large_sky_validation_run.md`.
<!-- preserved_source_end: docs/large_sky_direct_background_comparison.md -->

<a id="record-large_sky_validation_run"></a>

> Dated source record: `docs/large_sky_validation_run.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/large_sky_validation_run.md -->
## One-time large-sky validation run

**Date:** 2026-08-11

**Contract script:**
`scripts/phase3_background/freeze_large_sky_validation_run.py`

**Retrieval script:**
`scripts/phase3_background/run_large_sky_validation_scale.py`

**Contract:**
`data/results/background/large_sky_validation_run_contract_v1.json`

### What is being tested

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

### Rules frozen before the first query

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

### Frozen measurements to report

For both the direct procedure and the fitted diagnostic, report:

- the typical absolute log-density difference;
- the root-mean-square log-density difference;
- the fraction of reserved fields inside the frozen 68% range; and
- the fraction inside the frozen 95% range.

Also preserve every field-level result, list the ten largest absolute differences,
and compare validation performance numerically with development performance.

### Current status

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

### One-time evaluation result

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
<!-- preserved_source_end: docs/large_sky_validation_run.md -->


