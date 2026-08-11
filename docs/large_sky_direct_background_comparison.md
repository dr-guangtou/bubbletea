# Direct random-field background comparison

**Date:** 2026-08-11

**Contract script:**
`scripts/phase3_background/freeze_large_sky_direct_background_contract.py`

**Comparison script:**
`scripts/phase3_background/compare_large_sky_direct_backgrounds.py`

**Input:**
`data/results/background/large_sky_development_scale_summary_v1.csv`

**Machine-readable result:**
`data/results/background/large_sky_direct_background_comparison_v1.json`

## Why this replaced a model as the primary reference

The density of Gaia sources passing the frozen selector can be measured directly in
random sky fields. A fitted mathematical curve is therefore not required to supply
the primary large-sky background reference. The curve remains useful as a secondary
check, but it can hide extreme fields behind a smooth prediction.

The direct procedure preserves the actual comparison fields and their measured
densities. It reports a median, an arithmetic mean, and central 68% and 95% ranges.
These ranges show real field-to-field variation; they are not model confidence
intervals.

## Procedures compared

The rules were frozen before their performance was measured:

1. use all training fields in the same broad absolute-Galactic-latitude band;
2. additionally require the same low, middle, or high third of total Gaia source
   density; or
3. use the 20 nearest training fields in Galactic latitude and total Gaia source
   density.

All fields in the same broad sky block stayed together. A field was therefore
tested only against comparison fields outside its held-out block.

## Result

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

## Extreme flagged field

`sky_field_0317` has a measured passing-source density of 37,714.863 per square
degree. Its 58 same-latitude comparison fields have a median of 390.433 and a
central 95% range of 177.324--659.385 per square degree. The field is therefore a
factor of 96.597 above the median and far outside the measured range.

This is more informative than forcing a smooth prediction: the direct procedure
plainly identifies the field as unlike ordinary random fields in its latitude band.
The field remains preserved with its count-blind environment flag. It is not
deleted, converted to zero, or allowed to redefine the general background.

## Interface with a real host

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

## Status

The synthetic 300-field validation passes all ten safeguards in 0.666 seconds.
The 398-field comparison passes all 17 safeguards in 1.405 seconds and makes no
archive query. All comparison-field identities and measured densities are retained.
The fitted model is now a diagnostic only. No field is approved as a scientific
background, and all 102 large-sky validation fields remain unopened for a new
branch.
