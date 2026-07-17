# Point-source logistic validation v1

**Date:** 2026-07-18  
**Evaluation:** One-time frozen validation; complete  
**Retuning:** Prohibited

The project-lead-authorized evaluation applied `point_source_logistic_model_v1`
unchanged to all 721 benchmark-v3 validation rows. The model used frozen
`C = 1000` and threshold `0.8277833628791744`. No validation outcome contributed
to feature choice, training, regularization, threshold calibration, or reliability
labels.

## Primary result

| Cohort | Selected | Total | Retention |
|---|---:|---:|---:|
| Reliable confirmed UCD | 21 | 23 | 91.30% |
| Gaia NSS | 0 | 287 | 0.00% |
| Spectroscopic QSO | 1 | 88 | 1.14% |

Macro retention across the two available priority validation cohorts is 0.57%.
The independent sample therefore meets the predeclared 90% reliable-UCD recall
target while strongly rejecting the point-source contaminants that motivated the
selector.

## Secondary stress cohorts

The selector retains 146/167 spectroscopic galaxies (87.43%), 30/57 compact H II
regions (52.63%), and 1/3 dwarf-host H II regions. This is consistent with their
predeclared role: the Gaia-only model was not optimized to remove extended
extragalactic sources. Imaging, morphology, and photometric modeling remain the
second-round safeguards.

## False negatives and post-validation evidence

Dorado1 has probability 0.000090, 34.57-sigma Gaia proper motion, and a 0.769-arcsec
literature-to-Gaia offset. It is a newly exposed published-UCD/Gaia-counterpart
conflict analogous to Dorado2. The frozen validation label and outcome are retained;
no metric is revised. Any future model generation should quarantine this Gaia link
and use a new independent validation cohort.

M85-HCC1 has probability 0.693918, insignificant Gaia motion, 1.41 mas astrometric
excess noise, RUWE 1.24, and BP/RP flux-excess factor 2.18. It remains a credible
hard UCD and a genuine completeness failure.

## Artifacts

- `data/literature/validation/gaia_selector_validation_features_v1.csv`
- `data/literature/validation/point_source_logistic_validation_predictions_v1.csv`
- `data/literature/validation/point_source_logistic_validation_summary_v1.json`
- `data/literature/validation/point_source_logistic_validation_validation_v1.json`
- `data/literature/sources/point_source_validation_findings_v1.json`

