# Point-Source-Priority Selector Calibration

**Date:** 2026-07-17  
**Status:** Development operating points measured; no threshold frozen

## Approved Priority

The primary Stage 3 objective is to reject ordinary stars, Gaia NSS/binary failure
modes, and spectroscopic QSOs while retaining confirmed UCDs. Each point-source
cohort contributes equally to the optimization objective, regardless of its row
count. Spectroscopic galaxies are a secondary stress set intended for ancillary
imaging or photometric rejection. H II regions and compact young clusters remain a
separate host-correlated color/morphology safeguard.

## Score Architecture

The complete-coverage core combines two empirical ranks:

- absolute astrometric excess noise; and
- BP/RP flux-excess factor.

Each rank is the mean empirical CDF across the three equally weighted priority
cohorts. A small conditional penalty may be applied using covariance-aware proper-
motion and absolute-parallax zero-significance. Missing five-parameter astrometry
receives no penalty; it never removes a source. Missing BP/RP flux excess leaves the
AEN component rather than rejecting the source.

The grid tests AEN core weights of 0.25, 0.50, and 0.75; astrometric penalty weights
of 0.0, 0.1, 0.2, and 0.3; and empirical confirmed-UCD completeness targets of 80%,
85%, 90%, and 95%. These are operating-point measurements, not approved values.

## Measured Trade-off

The best equal-cohort point-source retention at each completeness target is:

| Target UCD completeness | Measured | Mean priority retention | Stars | NSS | QSOs |
|---:|---:|---:|---:|---:|---:|
| 80% | 80.0% | 2.22% | 4.19% | 0.00% | 2.48% |
| 85% | 85.1% | 2.56% | 4.95% | 0.00% | 2.73% |
| 90% | 90.3% | 3.73% | 6.48% | 0.00% | 4.71% |
| 95% | 95.4% | 6.84% | 13.33% | 0.00% | 7.20% |

The leading 90% operating point uses 25% AEN rank, 75% flux-excess rank, and a 10%
conditional astrometric penalty. It retains 98.6% of spectroscopic galaxies, as
expected under the approved secondary-galaxy policy. It also retains 90.6% of H II
rows and only 53.6% of uncertain literature UCD candidates. The latter is a
sensitivity warning, not evidence that confirmed-UCD completeness is wrong.

## H II Color Safeguard

A standalone `BP-RP >= 0.8588` development cut retains 90.3% of confirmed UCDs and
19.7% of H II rows. Applying it simultaneously with the 90% core operating point
would retain only 82.3% of confirmed UCDs. It therefore should not be silently added
as a hard primary cut. The safer current treatment is an H II/color review flag or
a separately calibrated second-round morphology/color rejection after the primary
point-source selection.

## Decision Needed Before Freezing

The recommended starting operating point is the measured 90% configuration because
it rejects the three priority point-source cohorts strongly without accepting the
larger stellar leakage of the 95% point. Freezing it still requires project-lead
approval. The exact threshold, rank reference distributions, null behavior, and
version must then move into one shared selector implementation before validation is
opened.

## Reproducibility

- Calibration: `scripts/phase1_literature/calibrate_point_source_selector.py`
- Validator: `scripts/phase1_literature/validate_point_source_selector_calibration.py`
- Components: `data/literature/validation/point_source_selector_components_v1.csv`
- Operating points: `data/literature/validation/point_source_selector_operating_points_v1.csv`
- Summary: `data/literature/validation/point_source_selector_calibration_v1.json`
- Validation: `data/literature/validation/point_source_selector_calibration_validation_v1.json`
