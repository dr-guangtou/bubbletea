---
date: 2026-07-17
repo: bubbletea
branch: phase1_calibrate_selector_20260716
tags:
  - journal
  - phase1
  - selector-calibration
  - contaminant-audit
---

## Progress

- Completed the development-only Gaia selector feature analysis for 3,136 sources without querying the 721 validation identifiers.
- Documented every contaminant cohort, Gaia selector feature, and direction-adjusted ROC AUC interpretation.
- Corrected the SDSS benchmark sampling description: `[0.0, 0.1)` on a measured 0--100 `random_id` domain is a 0.1% engineering slice, not 10%.
- Expanded the clean Gaia-linked SDSS reference outside the repository to 747,153 galaxies and 494,203 QSOs with unique Gaia identifiers.
- Downloaded 914,837 Gaia DR3 galaxy candidates with successful Sersic fits and 755,850 Quaia `G < 20.0` QSOs plus the Quaia selection function under `BUBBLETEA_EXTERNAL_DATA`.
- Recorded exact external paths, selection queries, row counts, file sizes, SHA-256 hashes, catalog roles, and circularity limitations.
- Searched Gaia extragalactic literature and identified CatGlobe, nearby-galaxy classification comparisons, foreground studies, LQAC-6, and Gaia DR4 methods as relevant references.
- Passed 20 external-catalog integrity checks, 19 selector-development checks, and 32 benchmark checks without changing `benchmark_v1`.

## Lessons Learned

- A sampling interval cannot be interpreted without measuring and recording the complete numerical domain of its archive field.
- Large Gaia-derived catalogs are valuable failure-mode and density stress sets but are not independent truth for calibrating a Gaia-only selector.
- Spectroscopic calibration, Gaia failure-mode stress testing, and sky-density or spatial-null testing require separate catalog roles.
- Compact and bright-core galaxies require host-centric density tests because they can be spatially associated with nearby-galaxy fields, unlike an approximately uniform QSO background.
- Feature discrimination must be interpreted together with positive-class coverage and explicit null handling.

## Key Issues

- `benchmark_v1` remains immutable; the expanded external catalogs are supplementary layers only.
- A clean magnitude- and sky-matched ordinary-star cohort is still required before selector freezing.
- The Gaia morphology and expanded SDSS identifiers need positional and approved Gaia-feature enrichment before host-field testing.
- The next action is a bounded host-field test of galaxy surface density and provisional-selector acceptance versus host-centric radius, magnitude, and morphology.
- Repository-wide Ruff remains blocked by 67 pre-existing legacy-script findings tracked under BT-016; targeted changed-file checks pass.

## Gaia Morphology Candidate Clarification

- Corrected the earlier “known galaxy” interpretation: the 914,837-source layer is
  a Gaia DR3 galaxy-candidate subset with successful Sersic fits, not a uniformly
  spectroscopically confirmed galaxy sample.
- Prohibited morphology-catalog membership as a UCD parent-sample requirement,
  because unresolved or barely resolved UCDs can lack a published Sersic fit.
- Restricted the exact-ID cross-match to the development partition. None of 175
  high-confidence confirmed UCDs, one of 569 uncertain UCD candidates, and none of
  127 H II regions match; all 721 validation rows remain blind.
- Retained Sersic radius, index, uncertainties, and quality flags as supplementary
  morphology evidence to be calibrated against independent high-resolution imaging,
  with no hard rejection threshold approved.

## Spectroscopic Stellar Reference

- Measured 812,893 clean Gaia-linked SDSS stellar spectrum associations over the
  audited external-reference G interval and staged a deterministic 10% `random_id`
  pool outside the repository.
- Excluded all 3,857 existing benchmark Gaia identifiers in the archive query and
  matched 525 unique spectroscopic stars 3:1 to the 175 confirmed development UCDs
  using G, absolute Galactic latitude, and absolute ecliptic latitude only.
- Explicitly declined to call the cohort “single stars”; SDSS spectroscopy does not
  establish singleness, and Gaia NSS remains a separate failure-mode sample.
- Measured leading stellar-reference AUC values of 0.961 for AEN significance,
  0.940 for RUWE with limited coverage, 0.940 for BP/RP flux excess, and 0.934 for
  AEN. No selector or threshold was approved, and 19 validation checks pass.

## Point-Source-Priority Operating Points

- Recorded the project lead's priority ordering: reject ordinary stars,
  NSS/binaries, and QSOs first with equal cohort weight; treat galaxies as a
  secondary ancillary-imaging problem and H II/young clusters with separate
  color/morphology safeguards.
- Replaced AEN significance in the proposed core because it does not distinguish
  confirmed UCDs from NSS; calibrated absolute AEN and BP/RP flux-excess empirical
  ranks with an optional conditional astrometric penalty.
- Measured 48 development-only operating points. The leading 90% completeness
  configuration measures 90.3% confirmed-UCD retention and 3.73% equal-cohort
  point-source retention (6.48% stars, 0.00% NSS, 4.71% QSOs).
- Kept the H II color layer separate: combining two individually 90%-complete cuts
  would reduce confirmed-UCD completeness to 82.3%. Fourteen calibration validation
  checks pass, and no score threshold is frozen.

## Classical ML Comparison

- Added scikit-learn through the locked uv environment and implemented regularized
  logistic regression and shallow histogram gradient boosting alongside the hand
  score.
- Used five outer and four inner spatially grouped folds. Matched stars inherit
  their matched UCD's group; all preprocessing, empirical references,
  hyperparameter selection, and 90% recall threshold selection occur inside
  training folds.
- Used measured BP-RP as a soft feature while excluding NSS membership, DSC class
  probabilities, candidate-catalog membership, and Sersic parameters from primary
  model inputs. Galaxy and H II cohorts remain fit-excluded stress samples.
- Logistic regression achieved 93.7% pooled confirmed-UCD recall with 4.02%
  equal-cohort priority retention. The hand score achieved 89.1% and 3.86%; shallow
  boosting achieved 88.6% and 3.55%.
- Kept the selector and validation partition frozen because logistic-regression
  recall spans 81.8--100% across outer folds. Twenty comparison-integrity checks
  pass; repeated grouped-CV stability and stratified performance are the next gate.

## Logistic Stability Gate

- Predeclared and ran ten deterministic five-outer/four-inner grouped-CV repeats
  for the provisional logistic model; the final measured runtime was 45.19 seconds.
- Measured 93.14--95.43% confirmed-UCD recall and 3.75--4.42% equal-cohort priority
  retention across complete repeats. All 50 fits chose `C = 3.0` and all nine
  measurement-feature coefficient signs agreed.
- Preserved 22,280 held-out predictions, all fold-local coefficients, fixed-bin
  magnitude/latitude metrics, and source-level selection frequencies. Twenty-five
  integrity and reproduction checks pass; validation remains sealed.
- Identified 11 persistently missed UCDs, 37 persistent stars, 4 NSS sources, and
  20 QSOs. Several missed UCDs share spatial groups or have strongly star-like Gaia
  astrometry, so provenance and association review is required before freezing.

## Persistent-UCD Source Audit Blocker

- Found that the 11 missed UCDs span seven HEALPix groups and are not a single
  spatial cohort. Available normalized distances are too incomplete for a robust
  farther-distance claim; their hosts are all nearby systems or clusters.
- Traced the `G = 12.34` row to M31 object B409 at Gaia RA 12.663251280395 deg and
  Dec +41.293171078320 deg. Its Gaia parallax is 77.9 sigma and total proper motion
  is 6.127 mas/yr, strongly indicating a foreground stellar Gaia source.
- Identified a confirmation-evidence error: Fahrion table B1 has 68 coordinate-
  bearing rows with `RV = 0.0`, but the review promoted all 377 rows as positive
  velocity evidence. Thirty affected objects occur in the confirmed development
  benchmark.
- Suspended selector-freeze readiness. No labels were changed; a provenance-
  preserving Fahrion zero-RV re-audit and downstream rebuild are now required.
