# Frozen-C1000 persistent UCD audit

**Date:** 2026-07-18  
**Model:** `point_source_logistic_policy_v1`, frozen `C = 1000`  
**Scope:** Development only; validation remains sealed

## Result

Ten of 146 reliable confirmed UCDs are missed in every one of ten grouped-OOF
repeats. None warrants removal from the reliable sample on current evidence.

- Five are multiply published Virgo/M87 UCDs. Their Gaia sources have two-parameter
  solutions, no usable parallax or proper motion, `G = 20.92--21.14`, and
  astrometric excess noise of 7.12--10.06 mas. They are genuine faint, extended
  hard positives rather than foreground-like associations.
- Three are Saifollahi spectroscopic A1 compact systems (rows 36, 39, and 59) with
  published half-light radii of 5.6, 9.9, and 13.2 pc. Their Gaia proper-motion
  significance is 0.27, 0.56, and 2.79. They remain valid hard positives.
- One is object 3 from Gregg et al. (2009), with low proper-motion significance
  (0.25), 3.60 mas excess noise, and a spectroscopic confirmation record.
- One is a Voggel et al. NGC 5128 object at `G = 18.37`. Its Gaia proper-motion
  significance is 11.66, but the literature-to-Gaia separation is only 0.019
  arcsec, the BP/RP flux-excess factor is 2.39, and astrometric excess noise is
  1.35 mas. The evidence favors corrupted Gaia astrometry for an extended source
  over a chance foreground association. It remains reliable but should be flagged
  for ancillary-image review.

The persistent misses therefore document the intended completeness cost of a
point-source-contaminant selector: faint or measurably extended UCDs and sources
with incomplete or corrupted Gaia astrometry are the hardest positive cases. They
must remain in completeness accounting. Removing them would bias the selector
toward easy, point-like UCDs.

## Artifacts

- `data/literature/validation/logistic_regularization_frozen_c1000_source_summary_v1.csv`
- `data/literature/validation/logistic_regularization_stability_v1.json`
- `data/literature/validation/logistic_regularization_stability_validation_v1.json`

