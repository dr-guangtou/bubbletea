# Large-sky background model comparison

**Date:** 2026-07-19

**Script:** `scripts/phase3_background/freeze_large_sky_model_comparison.py`

**Machine-readable contract:**
`data/results/background/large_sky_model_comparison_contract_v1.json`

**Contract identifier:** `model_contract_8da80ba5e4bd6d3027e6`

## What is being predicted

For each field, the measured quantity is the number of sources passing the frozen
Gaia selector per square degree of successfully queried area. The model works with
the count and exact area together so that fields with more measured area carry the
appropriate statistical weight. An incomplete field keeps a failure record and is
left out of fitting; it is never changed to a zero count.

## Models to compare

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

## How prediction is tested

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

## Choosing the final development model

The lowest average outer-fold deviance identifies the measured best score. The
chosen model is the simplest candidate whose score is statistically indistinguishable
from that best score under the predeclared one-standard-error rule. In plain
language, a more complicated model is used only when its improvement is larger than
the field-to-field uncertainty in the comparison.

After selection, the development fit, all data transformations, and the method for
constructing prediction ranges are frozen. Only then may the 102 held-back fields be
opened once for a final check. They cannot be used to revise the model.

## Current status

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
