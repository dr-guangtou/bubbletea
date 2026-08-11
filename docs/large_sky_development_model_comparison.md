# Large-sky development model comparison

**Date:** 2026-07-19

**Script:** `scripts/phase3_background/fit_large_sky_development_models.py`

**Command:**
`uv run python scripts/phase3_background/fit_large_sky_development_models.py`

**Input:**
`data/results/background/large_sky_development_scale_summary_v1.csv`

**Machine-readable result:**
`data/results/background/large_sky_development_model_comparison_v1.json`

## Outcome and revised role

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

## Predictive comparison

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

## Prediction ranges

Grouped predictions for fields excluded from their current fit give these frozen
observed-to-predicted multipliers:

- central 68% range: 0.858 to 1.174;
- central 95% range: 0.685 to 1.374.

For example, a prediction of 100 passing sources per square degree corresponds to
a development residual range of about 86--117 for the central 68% and 68--137 for
the central 95%. These are empirical field-to-field ranges from the development
sample. They are not yet independently validated confidence intervals.

## Important instability

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

## Safeguards and status

The local 60-field synthetic comparison passed all ten checks before the real fit.
The full comparison completed in 220.35 seconds with all 22 safeguards passing and
no convergence warning. All transformations were fitted within training data, all
six frozen model forms were evaluated, and residuals were recorded by Galactic
band, ecliptic band, and environment-flag state.

The fitted development model and its prediction ranges are now frozen. No field is
approved as a scientific background, and selector results for all 102 held-back
validation fields remain unopened.

## Reserved-field diagnostic result

The earlier plan to validate this fitted model as the primary background procedure
was superseded on 2026-08-11. The 102 reserved fields were later opened once to
evaluate the frozen direct procedure, with this serialized model included only as a
secondary diagnostic. Its validation typical difference is a factor of 1.128;
66/102 fields lie inside its frozen 68% range and 100/102 inside its frozen 95%
range. It was not refitted or retuned and remains secondary. See
`docs/large_sky_validation_run.md`.
