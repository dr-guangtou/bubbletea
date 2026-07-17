# Gaia Selector Feature Definitions and Limitations

**Status:** Permanent definition record for the Stage 3 development analysis  
**Date:** 2026-07-16  
**Figure:** `figures/phase1/selector_development_feature_auc.png`  
**Metrics:** `data/literature/validation/gaia_selector_development_feature_metrics.csv`

## Scope

This document defines every feature measured by
`scripts/phase1_literature/analyze_selector_development.py`. It distinguishes
columns published by Gaia DR3 from quantities derived by BubbleTea. None of these
diagnostics is, by itself, a physical source-size measurement or a calibrated UCD
probability.

The authoritative archive definitions are in the
[Gaia DR3 `gaia_source` data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html).
The Gaia processing and interpretation details are in the
[Gaia DR3 documentation](https://gea.esac.esa.int/archive/documentation/GDR3/).

## Features Displayed in the AUC Figure

### Astrometric excess noise

- **Archive column:** `astrometric_excess_noise`, in milliarcseconds.
- **Definition:** Extra per-observation angular noise that Gaia adds in quadrature
  to make the residuals of the single-source astrometric solution statistically
  consistent with the assumed observational noise.
- **Interpretation:** A positive value means that the ordinary astrometric model
  did not explain the observations at their nominal uncertainties. Extension,
  unresolved multiplicity, crowding, variability-induced motion, calibration
  problems, or other model failures can all produce it.
- **Safeguard:** It is not a direct angular radius and is not unique to extended
  sources.

### Astrometric excess-noise significance

- **Archive column:** `astrometric_excess_noise_sig`, dimensionless.
- **Definition:** Gaia's significance statistic, conventionally denoted \(D\), for
  the estimated astrometric excess noise. It is a Gaia-produced statistic, not
  `astrometric_excess_noise` divided by an error column.
- **Interpretation:** Gaia documents values above 2 as probably significant, but
  also advises users to calibrate the statistic empirically for their application.
- **Safeguard:** A large value says that excess noise is statistically supported;
  it does not identify its physical cause.

### RUWE

- **Archive column:** `ruwe`, dimensionless.
- **Definition:** The renormalized unit weight error of the astrometric fit. Gaia
  starts from the square root of the along-scan chi-square per degree of freedom
  and divides by an empirical normalization that depends on magnitude and color.
- **Interpretation:** Larger RUWE indicates a poorer fit to the ordinary
  single-source astrometric model after normalization.
- **Safeguard:** Binarity, crowding, source structure, variability, and calibration
  effects can all raise RUWE. Gaia sets it to null for two-parameter solutions.
  BubbleTea does not assume a universal RUWE threshold at this stage.

### IPD multi-peak windows

- **Archive column:** `ipd_frac_multi_peak`, stored as an integer percentage from
  0 to 100 despite `frac` in the column name.
- **Definition:** Percentage of windows with a successful Image Parameter
  Determination (IPD) result in which the IPD algorithm identified more than one
  image peak.
- **Interpretation:** A nonzero value can indicate a visually resolved double,
  binary, blend, or structured source.
- **Safeguard:** This is an observation-level image diagnostic, not an extension
  probability and not proof that the peaks belong to one astrophysical object.

### IPD odd-window transits

- **Archive column:** `ipd_frac_odd_win`, stored as an integer percentage from 0
  to 100.
- **Definition:** Percentage of successful-IPD transits having a truncated window
  or multiple gates flagged in at least one window.
- **Interpretation:** Gaia states that the onboard processing encountered a nearby
  detection; a nonzero value therefore warns that another real or spurious source
  may contaminate the measurements.
- **Safeguard:** It does not measure oddness of the source, image asymmetry, or
  resolved size. “IDD” is a typographical error; the Gaia subsystem is IPD.

### Gaia colors

- **Derived columns:** `bp_rp`, `bp_g`, and `g_rp`, in magnitudes.
- **Definitions:**
  - `bp_rp = phot_bp_mean_mag - phot_rp_mean_mag`
  - `bp_g = phot_bp_mean_mag - phot_g_mean_mag`
  - `g_rp = phot_g_mean_mag - phot_rp_mean_mag`
- **Interpretation:** These describe the relative integrated fluxes measured in
  Gaia's BP, G, and RP passbands.
- **Safeguard:** Crowding, background subtraction, blending, and extended-source
  flux loss can affect the colors. They are not independent because
  `bp_rp = bp_g + g_rp`.

### BP/RP flux-excess factor

- **Archive column:** `phot_bp_rp_excess_factor`, dimensionless.
- **Definition:** The sum of the integrated BP and RP fluxes divided by the G-band
  flux.
- **Interpretation:** Departure from the expected color-dependent locus signals
  inconsistency among the three flux measurements. Crowding, blending, background,
  or source extension may contribute.
- **Safeguard:** The raw factor has a strong color dependence. It is not a pure
  morphology statistic and must not be interpreted using one universal cutoff
  without color calibration.

### Absolute parallax zero-significance

- **BubbleTea-derived column:** `absolute_parallax_zero_significance`.
- **Definition:**

  \[
  S_{\varpi}=\frac{|\varpi|}{\sigma_{\varpi}},
  \]

  using Gaia `parallax` and `parallax_error`. It is the absolute value of Gaia's
  signed `parallax_over_error` quantity.
- **Interpretation:** The number of reported random standard errors by which the
  measured parallax differs from zero, ignoring its sign.
- **Safeguard:** This is a project diagnostic, not an official Gaia column and not
  a distance estimate. A large negative parallax has a large value here and can
  reflect model failure or systematics. The statistic does not include the Gaia
  parallax zero point or spatially correlated systematic uncertainty.

### Proper-motion zero-significance

- **BubbleTea-derived column:** `proper_motion_zero_significance`.
- **Definition:** The two-dimensional Mahalanobis distance of the Gaia proper-motion
  vector from zero. Let

  \[
  x=\frac{\mu_{\alpha *}}{\sigma_{\mu_{\alpha *}}},\quad
  y=\frac{\mu_{\delta}}{\sigma_{\mu_{\delta}}},\quad
  \rho=\texttt{pmra\_pmdec\_corr}.
  \]

  BubbleTea computes

  \[
  S_{\mu}=\sqrt{\frac{x^2-2\rho xy+y^2}{1-\rho^2}}.
  \]

- **Interpretation:** This tests the two-component null hypothesis of zero proper
  motion while respecting Gaia's published correlation between the right-ascension
  and declination components.
- **Safeguard:** This is a project-derived statistic, not Gaia's scalar `pm` divided
  by a scalar error. It is null when either component, error, or correlation is
  unavailable, or when the reported correlation cannot define a nonsingular
  covariance matrix. It uses only the 2D proper-motion covariance submatrix and
  does not add Gaia systematic-error floors. Missing five-parameter astrometry is
  retained as missing rather than interpreted as zero motion.

### DSC galaxy and star probabilities

- **Archive columns:** `classprob_dsc_combmod_galaxy` and
  `classprob_dsc_combmod_star` from the Discrete Source Classifier (DSC) combined
  model. The metrics table also includes the quasar probability.
- **Definition:** Normalized posterior class probabilities produced by Gaia's
  combination of its spectral and astrometry/photometry classifiers. See the
  official [Gaia DR3 DSC documentation](https://gea.esac.esa.int/archive/documentation/GDR3/Data_analysis/chap_cu8par/sec_cu8par_apsis/ssec_cu8par_apsis_dsc.html).
- **Interpretation:** They summarize evidence for Gaia's mutually modeled source
  classes under DSC's training data and adopted class priors.
- **Safeguard:** They are model outputs, not spectroscopic truth. Their priors,
  training-set selection, missing-input behavior, and domain shift matter. Because
  DSC itself uses astrometric and photometric diagnostics, its probabilities are
  not independent confirmation of those same inputs.

## Additional Features in the Machine-Readable Metrics

| Feature | Definition | Principal limitation |
|---|---|---|
| `phot_g_mean_flux_over_error` | Mean G flux divided by its reported error | Signal-to-noise and data-quality diagnostic, not morphology |
| `phot_bp_mean_flux_over_error` | Mean BP flux divided by its reported error | Missingness and crowding can differ by source class |
| `phot_rp_mean_flux_over_error` | Mean RP flux divided by its reported error | Missingness and crowding can differ by source class |
| `classprob_dsc_combmod_quasar` | DSC combined-model quasar posterior probability | Model- and prior-dependent, not a truth label |
| `duplicated_source` | Gaia processing flag indicating multiple source identifiers were considered for one detection | Processing-history flag, not proof of astrophysical multiplicity |
| `non_single_star` | Gaia flag indicating membership in the DR3 NSS tables | Tautological for the benchmark's Gaia NSS cohort and prohibited as independent validation evidence |

## How to Read the AUC Figure

### ROC and ordinary AUC

ROC means receiver operating characteristic. For one feature, imagine moving a
threshold from one end of its observed range to the other and, at every threshold,
measuring:

- the true-positive rate: the fraction of confirmed UCDs retained; and
- the false-positive rate: the fraction of the selected contaminant cohort
  retained.

The ROC curve plots the true-positive rate against the false-positive rate over
all thresholds. Its area under the curve is the ROC AUC. In this univariate
analysis, ordinary AUC has the equivalent rank interpretation

\[
\mathrm{AUC}_{\mathrm{raw}}
=P(X_{\mathrm{UCD}}>X_{\mathrm{contaminant}})
+\frac{1}{2}P(X_{\mathrm{UCD}}=X_{\mathrm{contaminant}}).
\]

Thus, a raw AUC of 0.80 means that a randomly drawn confirmed UCD has a larger
feature value than a randomly drawn member of that contaminant cohort 80% of the
time, with tied pairs contributing one half. It does not mean 80% accuracy, 80%
purity, or 80% completeness.

### Direction adjustment used in the heatmap

Some useful UCD diagnostics are expected to be lower rather than higher. To show
separation strength on one common 0.5--1.0 scale, BubbleTea plots

\[
\mathrm{AUC}_{\mathrm{display}}
=\max(\mathrm{AUC}_{\mathrm{raw}},1-\mathrm{AUC}_{\mathrm{raw}}).
\]

- A raw AUC of 0.90 becomes a displayed AUC of 0.90 and has direction `higher`.
- A raw AUC of 0.10 also becomes a displayed AUC of 0.90, but has direction
  `lower`.
- A displayed AUC near 0.50 means little rank separation.
- A displayed AUC near 1.00 means nearly complete rank separation in one
  direction.

The adjustment is equivalent to allowing the inequality of a one-feature rule to
be reversed. It does not improve the underlying data or fit a classifier. Because
the heatmap suppresses the sign, the `ucd_direction` column in
`gaia_selector_development_feature_metrics.csv` must be read before interpreting
which values are UCD-like.

For example, proper-motion zero-significance against Gaia NSS has raw AUC 0.009
and displayed AUC 0.991. The direction is `lower`: confirmed UCDs generally have
lower measured proper-motion significance than the published non-single stars.
By contrast, BP - RP against the nine development-partition dwarf-host H II rows
has raw and displayed AUC 1.000 with direction `higher`. That perfect rank ordering
is conditional on a very small comparison cohort and does not establish a
universal color threshold.

### What one heatmap cell does and does not measure

Each cell compares one feature for the finite measurements among 175 confirmed
UCDs and one contaminant cohort in the development partition. It is univariate:
it does not describe the performance of a multi-feature selector. The AUC is also
independent of the relative number of UCDs and contaminants, so it does not yield
survey purity or a false-discovery rate.

The direction and deterministic 95% bootstrap interval are stored in the metrics
table. The interval measures sampling variation within the assembled development
cohorts; it does not account for mislabeled sources, survey selection effects,
Gaia systematics, or missing-not-at-random feature coverage.

A high cell does not establish a selector rule. It can be driven by missingness,
the selection function of a contaminant cohort, or a feature whose physical cause
is not unique. Coverage, direction, magnitude dependence, and each contaminant
cohort must be evaluated before a feature enters a frozen selector.

## Q2 Decision Record

On 2026-07-16, the project lead requested explicit definitions and official Gaia
references for the `_auc.png` features. The audit found two correctable issues:
the figure called Gaia's percentage-valued IPD fields “fractions,” and the first
proper-motion diagnostic ignored the published correlation between the two
components. The permanent treatment is to label the IPD quantities as percentages,
rename the derived astrometric quantities as zero-significance diagnostics, and
use the covariance-aware two-dimensional proper-motion formula above. The prior
diagonal approximation is superseded and must not be used for selector design.

## Q3 Decision Record

On 2026-07-16, the project lead requested a permanent explanation of the
direction-adjusted ROC AUC used in the QA heatmap. The figure remains
direction-adjusted because it is useful for comparing separation strength across
features, but every scientific interpretation must consult the raw AUC,
`ucd_direction`, finite sample counts, coverage fractions, and bootstrap interval
in the companion metrics table. A displayed AUC must never be described as
accuracy, purity, completeness, or an approved selector threshold.
