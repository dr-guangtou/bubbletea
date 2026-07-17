---
date: 2026-07-18
repo: bubbletea
branch: phase1_calibrate_selector_20260716
tags:
  - journal
  - phase1
  - validation
  - selector
---

## Progress

- Audited Gaia contaminant definitions, feature semantics, extragalactic catalogs,
  morphology controls, and source-level literature evidence without deleting
  provenance records.
- Corrected the Fahrion `RV = 0.0` confirmation error: 309 rows retain velocity
  evidence, 68 receive non-promotion review, and B409 is rejected as an incorrectly
  classified UCD.
- Preserved benchmark v1, derived evidence-corrected v2, and derived v3 by
  quarantining four published-UCD/Gaia-counterpart conflicts from reliable training.
- Built and validated matched stellar controls, linear calibration, classical-ML
  comparisons, repeated grouped-CV stability, and source-level failure audits.
- Froze `point_source_logistic_policy_v1` with L2 logistic regression, `C = 1000`,
  and grouped-OOF threshold `0.8277833628791744`.
- Serialized `point_source_logistic_model_v1`, exported transparent preprocessing
  and coefficient parameters, and passed exact prediction-parity and blind-safety
  checks.
- Completed the authorized one-time validation: reliable-UCD recall is 21/23
  (91.30%), Gaia NSS retention is 0/287, and QSO retention is 1/88; all 13 frozen-
  evaluation checks pass.
- Recorded Dorado1 as a post-validation Gaia-association conflict without revising
  the frozen outcome; retained M85-HCC1 as a genuine hard-UCD false negative.

## Lessons Learned

- Numeric zero may encode unavailable evidence rather than a physical measurement;
  source conventions must be checked before confirmation promotion.
- Published-object reliability and Gaia-counterpart reliability require separate
  provenance states and separate training eligibility decisions.
- Repeated boundary selection does not enclose a regularization optimum; direct
  convergence and paired fixed-policy comparisons supported a finite `C = 1000`.
- Persistent difficult UCDs must remain in completeness accounting unless evidence
  invalidates the object or association; removing hard positives would bias the
  selector toward point-like sources.
- A Gaia-only point-source selector can reject stars, NSS objects, and QSOs while
  leaving galaxies and H II regions for ancillary imaging and photometric modeling.

## Key Issues

- The frozen validation result prohibits retuning; any future selector generation
  requires a new independent validation cohort.
- Dorado1 should be quarantined from reliable training in any future model generation,
  while its current validation label and outcome remain immutable.
- The next implementation task is integrating the frozen selector into the Phase I/IV
  search workflow with identical feature and null-handling parity.
- Repository-wide pre-commit remains blocked by 13 pre-existing Ruff errors in
  archived notebooks and legacy phase scripts; targeted checks for this branch pass.
