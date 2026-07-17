# BubbleTea Scientific Specification

**Status:** Initial scientific specification; methodological research remains open
**Created:** 2026-07-14
**Initial interview completed:** 2026-07-14
**Source of truth:** Approved scientific definitions and analysis requirements

This specification records decisions approved by the project lead during the
initial scientific-definition interview. It will evolve through the registered
methodological research, but unresolved topics must not be converted into
implementation assumptions.

## Primary Target

BubbleTea is a search for ultra-compact dwarf galaxies (UCDs), not a general
globular-cluster search.

The physical boundary between UCDs and globular clusters is fuzzy and is not
treated as a perfectly physical division. The operational candidate population is
therefore composed of objects that:

- Gaia clearly indicates are extended rather than point sources; and
- are probably too luminous or too large to be ordinary globular clusters at the
  distance of the associated nearby galaxy.

Ambiguous luminous or extended clusters may remain in the candidate population,
but recovery of ordinary globular clusters is not an optimization objective.

## Scientific Objectives

The objectives are ordered by priority.

1. Provide conclusive statistical evidence for or against an excess of extended
   but compact stellar systems, such as UCDs, around nearby galaxies relative to
   the background.
2. Test how the measured excess, including non-detections, correlates with host
   properties such as luminosity, color, environment, halo mass, and morphology.
3. Produce prominent candidate lists of previously unidentified UCDs around nearby
   systems, ranked primarily by the probability that each source is not a point
   source.

The first two objectives are population-level statistical analyses. Candidate
lists are a secondary product and must not weaken the reproducibility or
interpretability of the population selection function.

## Distance and Detectability

The survey does not use one distance-independent UCD threshold or treat 25 or
50 Mpc as a universal sensitivity boundary. Gaia's photometric limit, astrometric
capability, and catalog uncertainties determine what UCD luminosities and sizes are
reliably identifiable at each distance.

- Within 25 Mpc, the analysis should aim for a more complete census of the UCD
  population that Gaia can detect.
- Between 25 and 50 Mpc, the analysis should target only the most obvious UCDs that
  remain reliably detectable by Gaia.
- The practical outer boundary should follow measured Gaia capability rather than
  an assumed fixed cutoff.
- Selection, completeness, excess measurements, and host-property correlations
  must be interpreted within distance-dependent luminosity and size limits.

The project must measure the selection or sensitivity function across distance,
luminosity, size, magnitude, and relevant Gaia uncertainty properties before
combining galaxies with different detection limits.

## Approved Interpretation Rules

- A Gaia-selected source is an extended-source candidate, not a confirmed UCD.
- A database row is not necessarily a unique or confirmed astrophysical object.
- A radial excess is a population measurement, not by itself an individual UCD
  discovery.
- Completeness and background contamination are meaningful only for the exact same
  versioned selection function.
- Non-detections must remain in the host-property analysis when their sensitivity
  limits permit a meaningful constraint.

## Background and Control Regions

The background definition must be tested with multiple methods so that the primary
overdensity result is not dependent on one arbitrary control geometry. At minimum,
the analysis should explore:

- an average over a large field of view to improve statistical precision; and
- off-target circular or annular control regions sufficiently far from the target
  galaxy.

Every background method must account for the following constraints:

- Gaia-selected source density correlates strongly and systematically with Milky
  Way stellar density and Galactic latitude. Target and control regions must have
  sufficiently similar Galactic latitude, or the residual dependence must be
  modeled and validated.
- The control region must lie beyond a conservative upper-limit estimate of the
  target halo radius, `R200c`. This estimate may use galaxy luminosity-halo mass or
  galaxy size-halo size relations, including `R50` where available.
- A configurable safety buffer should be applied outside the upper-limit halo
  estimate. A factor such as 1.5 is an initial example, not a fixed value until it
  is calibrated.
- Control regions must be checked for other nearby galaxies whose compact-system
  populations or halos could contaminate the inferred background.

The final analysis must compare the background methods and propagate their
differences into the overdensity uncertainty or robustness assessment. A missing
or contaminated control region must not be represented as a zero-density
background.

## Evidence and Null Results

The analysis must be designed to avoid confirmation bias and must not assume that
nearby galaxies host detectable UCD populations. Null and negative results are
scientifically acceptable.

- Every eligible galaxy remains in the population analysis, including galaxies
  with zero measured overdensity and galaxies with negative measured overdensity.
- Negative overdensities are valid outcomes of background fluctuations and
  measurement uncertainty. They must not be clipped to zero or removed merely
  because they are negative.
- Analysis choices that can change the inferred excess, including the selection
  function, radial range, background method, and exclusion masks, must be fixed or
  calibrated without choosing the version that maximizes a target signal.
- Low-mass or low-luminosity dwarf galaxies are scientifically useful empirical
  false-positive checks because detectable UCD companions are not generally
  expected around many such systems. They must still be analyzed identically rather
  than forced to be non-detections.
- Compact star-forming regions and H II regions are a specific false-positive
  population around dwarf and star-forming galaxies. Their exclusion must use
  documented color or morphology evidence and be incorporated consistently into
  the selection or contamination model.

As an initial evidence standard, a 3-sigma overdensity relative to the full
background uncertainty within a defined radial range counts as a reliable
overdensity. The radial range remains to be calibrated from actual background and
sensitivity behavior. If multiple radial ranges, selectors, background methods, or
hosts are searched, the analysis must account for the resulting trial factors or
otherwise distinguish exploratory from confirmatory significance.

## Role of External Imaging

The primary statistical characterization must be based on Gaia data alone. A
galaxy's inclusion in the statistical sample, its selected-source counts, its
background estimate, and its overdensity measurement must not depend on external
imaging availability.

External imaging is value-added content:

- Multi-band imaging may provide SED or color-color checks where coverage exists.
- Space-based or other high-resolution imaging, including HST and Euclid, may test
  candidate morphology directly.
- Galaxies with significant Gaia-based excesses may receive targeted multi-band
  imaging analysis in a later characterization stage.

Ancillary coverage and validation outcomes must be recorded, but they must not be
used retrospectively to alter the Gaia-only statistical selection. Any analysis of
an imaging-covered subset must be labeled as such and kept distinct from the
all-Gaia population inference.

## Extended-Source Probability Calibration

The method for assigning a Gaia-only probability that a source is non-point-like
is an open research question. It must be explored and validated rather than fixed
from the current provisional score.

The calibration data should include:

- the existing literature UCD collection as the best available positive reference,
  while explicitly accounting for the fact that some entries are candidates and
  may be incorrectly classified;
- spectroscopically identified QSOs and compact background galaxies in the relevant
  magnitude range, potentially drawn from SDSS, GAMA, and DESI catalogs;
- a published Gaia binary-star catalog, combined with Gaia evidence of binarity,
  because unresolved binaries can produce astrometric behavior that mimics source
  extension; and
- compact star-forming and H II regions as a host-dependent contaminant population
  for star-forming, spiral, and dwarf galaxies.

For the primary Gaia-only analysis, Gaia `BP-RP` is the starting color for rejecting
obvious very blue star-forming and H II contaminants because UCDs should not be
extremely blue. Other color combinations available from Gaia data may also be
explored. The thresholds, distance or magnitude dependence, and effects on UCD
completeness remain to be confirmed experimentally. No other H II rejection
criterion is approved yet. Optical-image rejection remains value-added candidate
validation rather than part of the uniform Gaia statistical selector.

Reference labels, provenance, magnitude coverage, sky dependence, and label
uncertainty must be retained. Confirmed and candidate UCDs must not be treated as
equally certain training labels without testing the effect of that assumption.

The permanent source-by-source definitions, selection rules, bias limitations,
and required safeguards are maintained in `docs/contaminant_benchmark.md`. That
document is normative for interpreting benchmark contaminant labels.

Large extragalactic supplements have three distinct roles: relatively independent
spectroscopic calibration, Gaia-derived failure-mode stress testing, and spatial
density or null testing. Their approved catalog choices, exact counts, provenance,
and circularity constraints are maintained in
`docs/extragalactic_contaminant_catalogs.md`. They must not mutate
`benchmark_v1` or be pooled according to raw catalog size.

The ordinary-stellar development supplement is the matched SDSS DR16 spectroscopic
stellar reference defined in `docs/spectroscopic_stellar_reference.md`. It is
disjoint from `benchmark_v1`, uses no selector feature for retrieval or matching,
and must not be called a physically single-star sample. Its 525 sources are matched
3:1 to the 175 confirmed development UCDs in G magnitude, absolute Galactic
latitude, and absolute ecliptic latitude. It may calibrate stellar failure behavior
but may not change the sealed validation partition or be pooled with Gaia NSS.

The first bounded Gaia-morphology host-field diagnostic uses a predefined
three-galaxy test sample and cannot
set a selector threshold. It selects the first three ranked current host-catalog
rows satisfying `|b| >= 30 degrees`, `15 <= distance_mpc <= 25`, and an angular
radius for 600 kpc no larger than 2.1 degrees. It retrieves every source with a
published Gaia DR3 Sersic fit out to 600 kpc, without selector prefilters, and
retains physical annuli `[0, 25, 50, 100, 150, 300, 600]` kpc. The 300--600 kpc
annulus is a local comparison region, not an uncontaminated background. Both
inherited selector definitions are evaluated after retrieval solely as historical
failure-rate baselines. The test may expose galaxy contamination behavior but may
not tune annuli, choose hosts, define priors, inspect validation identifiers, or
authorize a selector.

The fixed diagnostic returned 814 host-source associations. The two inherited
selectors made identical decisions and retained 714 morphology candidates (87.7%).
Only 11.9% had RUWE and covariance-aware proper-motion significance. The combined
inner density did not exceed the local 300--600 kpc comparison density, so this
test supports a candidate-selection failure-mode claim but not a host-clustering
claim. In this context, “selected” means retained as a possible UCD candidate despite
membership in the Gaia DR3 galaxy-candidate Sersic-fit subset. It is not a pure
false-positive label because candidate membership is not astrophysical confirmation.

The expanded comparison freezes 12 hosts across three K-band luminosity and two
absolute Galactic-latitude strata plus one geometrically matched control per host.
Environment is not a stratum because the inherited `is_cluster` field is an
undocumented sky-circle proxy. The 24 fields contain 9,144 morphology candidates.
Host fields have a higher combined density, but only 8 of 12 paired differences are
positive and the two-sided sign-test p-value is 0.3877; no host-clustering claim is
approved. The legacy 70/30 and 60/30/10 rules falsely retain 85.5% and 85.4% of host-
field candidates and about 88.1% of control-field candidates. This high retained
fraction, not clustering, is the selector-calibration result. The morphology subset
must not define the UCD parent sample because unresolved UCDs may lack Sersic fits;
its parameters may be used only as supplementary evidence under a separately frozen
policy.

An exact-ID cross-match restricted to the blind-safe development partition found no
Sersic-catalog membership among 175 high-confidence confirmed UCDs, one membership
among 569 uncertain UCD candidates, and none among 127 H II regions. The 24 confirmed
validation UCDs remain uninspected until selector and morphology-use freezing. These
results are defined in `docs/gaia_morphology_ucd_crossmatch.md`.

The permanent definitions, units, derivations, official Gaia references, and
interpretation safeguards for selector inputs are maintained in
`docs/gaia_selector_features.md`. That document is normative for feature names
and scientific interpretation.

The versioned Gaia-only calibration benchmark is a derived validation product,
not a new classification layer in the literature database. Its first version
uses the complete observed Gaia-magnitude span of the literature cohort as its
applicability domain and retains the following label roles separately:

- `ucd_confirmed` objects are high-confidence positive references under
  `confirmation_rules_v1`;
- `ucd_candidate` objects are positive-sensitivity references and never primary
  labels;
- `ucd_role_conflict` objects are conflict-sensitivity references and never
  primary labels;
- source-reported non-UCD comparison objects remain a moderate-confidence,
  heterogeneous comparison cohort rather than being relabeled as a specific
  contaminant class;
- clean SDSS DR16 spectroscopic `QSO` and `GALAXY` sources linked to Gaia DR3 are
  high-confidence extragalactic contaminants; and
- Gaia DR3 non-single-star solutions are a binary-star contaminant cohort whose
  exact solution type remains explicit.

Benchmark rows retain the publication, catalog, source-row identifier, label
basis, confidence tier, Gaia association method, and all Gaia selector inputs.
Objects sharing a coarse Gaia HEALPix parent cell must remain in one partition.
`benchmark_partition_v1` assigns those spatial groups deterministically to
development or validation data using a published hash rule; labels and features
do not influence assignment. The partition is immutable once released.

PHANGS-MUSE star-forming nebulae form a named spiral-host contaminant cohort. The
Gaia association audit uses eight 30- and 60-arcsecond displaced-position controls
and measures the full 0.1--5.0-arcsecond cumulative separation curve. The approved
`hii_gaia_association_v1` rule retains the 175 unique Gaia sources within 0.3
arcseconds as moderate-confidence H II contaminants. The controls predict 13.25
chance matches at that radius, giving a measured excess fraction of 0.9243. The
cohort is primary-eligible but must also be excluded as a declared sensitivity
test. It represents nearby spiral environments only; dwarf-host H II coverage
is supplied separately by the van Zee et al. (2006) long-slit spectroscopy of H II
regions in 21 dwarf irregular galaxies. That source retains 63 unique published
positions after repeated slit measurements are consolidated. Its integer-arcsecond
offset coordinate construction requires a separate association calibration:
`dwarf_hii_gaia_association_v1` retains 13 associations within 3.0 arcseconds.
They resolve to 12 unique Gaia sources because two
published UGC 3647 slit positions select the same Gaia source; the benchmark
consolidates those positions without discarding either source-row locator. With
one expected displaced-control match, the measured association-level excess
fraction is 0.9231. These are also moderate-confidence, primary-eligible labels
that must be removable as a cohort-level sensitivity test.

`benchmark_v1` contains 3,857 rows representing 3,857 unique Gaia DR3 sources:
962 literature-reference sources, 805 SDSS DR16 galaxies, 491 SDSS DR16 QSOs,
1,412 Gaia DR3 non-single-star sources, 175 PHANGS-MUSE H II associations, and 12
van Zee dwarf-host H II Gaia sources. The fixed spatial partition contains 3,136
development and 721 validation rows. Primary analyses may use the 3,216
primary-eligible rows; all 3,857 rows remain available to declared sensitivity
analyses. The machine-readable validation report must pass before selector work
uses this benchmark.

Selector calibration begins on the `benchmark_partition_v1` development rows
only. The validation source identifiers, labels, and feature distributions remain
unexamined until one selector implementation, its null behavior, and its decision
thresholds are frozen. A development enrichment may retrieve additional Gaia DR3
columns by exact source identifier, but it must select development identifiers
before querying and prove that no validation identifier appears in its output.

The first development analysis compares Gaia-native extendedness, image-fit,
astrometric, photometric, and classification features. It includes astrometric
excess noise and significance, RUWE, IPD multi-peak and odd-window percentages,
Gaia colors, BP/RP flux excess, parallax and proper-motion zero-significance,
flux signal-to-noise, and Gaia DSC probabilities. The proper-motion statistic is
the covariance-aware two-dimensional distance from zero using Gaia
`pmra_pmdec_corr`; the earlier diagonal approximation is superseded. The
inherited Phase III 70/30 score
and Phase IV 60/30/10 score are historical baselines, not approved selector
definitions.

Primary discrimination metrics compare high-confidence confirmed UCDs against
primary-eligible contaminants. Declared sensitivity analyses add uncertain UCD
candidates as positives and remove the PHANGS-MUSE or all H II cohorts from the
negative class. Reported role conflicts and the unresolved shared-Gaia row remain
excluded from primary calibration. This exploratory pass may identify useful
features and failure modes, but it does not authorize a selector threshold.

The project lead approved a tiered selector direction on 2026-07-17 with an
explicit contaminant priority. The primary calibration objective is rejection of
point-source contaminants: ordinary spectroscopic stars, Gaia NSS/binary failure
modes, and spectroscopic QSOs. These three cohorts receive equal cohort weight so
their unequal row counts do not define the objective. Galaxy candidates are a
secondary stress set because ancillary optical imaging and photometric catalogs can
reject extended extragalactic sources in a later pass, and most unrelated galaxies
should not cluster around nearby hosts. H II regions and compact young clusters are
the host-correlated exception and retain separate color/morphology safeguards.

The approved architecture has a complete-coverage extendedness/color ranking plus
conditional parallax and proper-motion evidence when five-parameter astrometry is
available. Missing astrometry is neutral rather than a rejection. DSC, NSS, and
Sersic membership may be retained as flags or supplementary evidence but cannot be
hard parent-sample cuts. Development calibration must show cohort-specific
completeness and retention before one score, null policy, and threshold are frozen.

The first development-only measurement contains 3,136 unique Gaia sources and
passes 19 artifact and partition checks. Under the primary labels, proper-motion
and absolute-parallax zero-significance have direction-adjusted univariate AUC
values of 0.850 and 0.847, but both exist for only 46.9% of confirmed UCDs; they
cannot be hard completeness requirements. Astrometric excess noise is the strongest
fully observed continuous feature (AUC 0.737). BP/RP flux excess reaches 0.677,
while excess-noise significance and raw BP-RP color alone are near 0.553 and
0.522 against the mixed contaminant population. The `non_single_star` flag is
tautological for the benchmark cohort selected from Gaia NSS tables and must not
be interpreted as independent validation evidence.

Label uncertainty changes the feature ordering. When uncertain UCD candidates are
included as positive sensitivity rows, IPD multi-peak percentage reaches AUC 0.742
and RUWE reaches 0.704, while proper-motion zero-significance falls to 0.765.
This is consistent with the candidate cohort containing more high-motion or poor-fit
sources and prevents candidate labels from defining the primary score. The two
inherited Model C definitions retain only 66.3% and 64.0% of confirmed UCDs while
selecting 20.7% and 20.2% of primary contaminants. Both select about 55% of SDSS
galaxies and roughly half of the H II cohorts, so neither is acceptable as the
frozen selector. These are development findings only; the validation partition
remains sealed.

The approved classical-classification experiment compares regularized logistic
regression, shallow histogram gradient boosting, and the hand rank score using
development-only nested grouped cross-validation. Each matched spectroscopic star
inherits its matched UCD's spatial group; preprocessing, empirical references,
model fitting, hyperparameter selection, and the 90% recall threshold occur inside
training folds. The three priority negative cohorts retain equal total weight.
Measured BP-RP is permitted as a soft feature, while NSS membership, DSC class
probabilities, candidate-catalog membership, and Sersic parameters are prohibited
as primary model inputs. Galaxies and H II regions remain fit-excluded stress sets.

The first five-outer/four-inner-fold comparison finds 93.7% pooled confirmed-UCD
recall and 4.02% equal-cohort priority retention for logistic regression, compared
with 89.1% and 3.86% for the hand score. Shallow boosting reaches 88.6% and 3.55%.
The logistic outer-fold recall spans 81.8--100%, so no model or threshold is frozen.
Repeated grouped stability checks and performance stratification must be reviewed
before selecting one implementation for the single withheld-validation test.

The logistic-regression stability gate uses ten deterministic repeats with seeds
`20260717 + 1009 * repeat_index`, five outer grouped folds, and four inner grouped
folds. It preserves the first comparison's feature set, equal cohort weights,
hyperparameter grid, target recall, and matched-star/UCD group coupling. Every
development fit row receives one outer-fold prediction per repeat. The analysis
records repeat and fold metrics, standardized fold-local coefficients including
imputation indicators, and source-level selection frequency. A confirmed UCD
selected in at most half of repeats or a priority contaminant selected in at least
half is reported as a persistent failure case, without removing or relabeling it.

Performance stratification uses fixed, predeclared bins rather than bins chosen
from results: Gaia G magnitude `(-inf, 18]`, `(18, 19]`, `(19, 20]`, and
`(20, inf)` mag; absolute Galactic latitude `[0, 30)`, `[30, 60)`, and
`[60, 90]` degrees; and absolute ecliptic latitude with the same angular bins.
Every stratum reports its source and repeated-prediction counts; sparse strata are
descriptive and cannot set a threshold. Readiness for selector-freeze review
requires the median repeated pooled UCD recall to meet 90%, no repeat below 85%,
and at least 80% coefficient-sign agreement for each nonzero median measurement
feature. These development criteria do not authorize validation unsealing.

The ten-repeat measurement passes all three criteria. Confirmed-UCD recall ranges
from 93.1% to 95.4% across complete repeats, with a 93.7% median; equal-cohort
priority retention ranges from 3.75% to 4.42%, with a 3.96% median. All 50 outer
fits select `C = 3.0`, and every measurement-feature coefficient has 100% sign
agreement. Because `C = 3.0` is the least-regularized boundary of the tested grid,
a bounded higher-C sensitivity must enclose or characterize the optimum before the
regularization strength is frozen. Eleven confirmed UCDs are persistently missed,
including spatially grouped and strongly star-like Gaia associations. Fixed-stratum
UCD recall is lower
in the `G <= 18`, `19 < G <= 20`, mid-Galactic-latitude, and mid-ecliptic-latitude
bins; the highest ecliptic bin contains only one UCD and cannot support a population
claim. The model is ready for selector-freeze review only. Failure-case provenance,
the applicability domain, the regularization-boundary sensitivity, and the full-
development threshold-calibration procedure must be approved before a versioned
model is fitted and validation is unsealed.

A source-level audit triggered by the stability failures suspends that readiness.
The bright M31 entry B409 is associated with Gaia DR3 `375037265841433344`, whose
parallax is measured at 77.9 sigma and whose total proper motion is 6.127 mas/yr.
Fahrion table B1 gives B409 `RV = 0.0` and `reff = 0.0`. The approved confirmation
review incorrectly stated that every coordinate-bearing Fahrion compilation row
supplies a radial velocity: 68/377 rows use `RV = 0.0`, and 30 of those objects are
in the current confirmed development benchmark. These rows require non-destructive
re-audit for independent spectroscopic or structural evidence and Gaia association
validity. No selector may be frozen and validation may not be unsealed until the
benchmark is rederived under a corrected zero-RV policy.

The approved correction treats `RV = 0.0` as unavailable evidence, not a velocity
measurement. All 377 Fahrion rows and their raw provenance remain unchanged: 309
nonzero-velocity rows receive positive membership evidence and all 68 zero-velocity
rows receive explicit non-promotion reviews. Independent evidence keeps 8 of the 68
canonical objects confirmed; 59 are candidates. B409 alone is rejected as an
incorrectly classified UCD through approved negative foreground-astrometry evidence,
while its original reported classification remains preserved. The resulting database
contains 680 confirmed, 1,574 candidate, 2,083 rejected, and 22 uncertain canonical
objects. Benchmark v1 and its selector products are immutable historical artifacts;
benchmark v2 preserves every row, Gaia measurement, spatial group, and partition but
updates 26 Gaia-linked literature labels (25 confirmed to candidate and B409 to
rejected). Development-only cached Gaia features are carried forward without a new
query. All selector metrics derived from benchmark v1 are scientifically superseded
and must be recomputed before selector-freeze review resumes.

The benchmark-v2 development rebuild uses 150 confirmed UCDs and 450 newly rematched
spectroscopic-star controls. Across the same ten grouped nested-CV repeats, logistic
recall is 94.67--96.00% with a 95.33% median, and equal-cohort priority retention is
3.77--4.39% with a 4.23% median. All 50 fits again select boundary value `C = 3.0`,
and every measurement-feature coefficient retains 100% sign agreement. Seven
confirmed UCDs are persistently missed. These v2 results pass the declared stability
gate but do not approve a model or threshold: the seven failures and the higher-C
sensitivity remain development-only prerequisites to selector freezing.

Published-UCD reliability and Gaia-counterpart reliability are separate states.
The approved `ucd_reliability_reviews.json` register records B409 as a rejected
published classification and records NGC 1400_1, NGC1400_2, Dorado2, and Saifollahi
A1 row 32 as unresolved published-UCD/Gaia-counterpart conflicts. The latter four
retain their spectroscopic UCD classifications but are excluded from the reliable
training sample because their Gaia counterparts have 9.91--44.87-sigma proper
motion. Benchmark v3 preserves every row, feature, and partition, changes no
published classification, and sets only these four associations ineligible. Its
development sample has 146 reliable UCDs and 438 rematched stars. Ten-repeat recall
is 93.84--96.58% with a 94.18% median; macro priority retention is 3.61--4.00% with
a 3.78% median. Nine reliable UCDs remain persistent failures.

Regularization sensitivity extends the logistic grid from `C <= 3` first to
`C <= 100` and then to `C <= 3000`. Four of five outer folds select the upper
boundary in both extensions; the remaining fold selects 30 and 100, respectively.
Thus `C = 3` is too restrictive under the current inner objective, but no finite
optimum is enclosed. The project must compare explicit weakly regularized and
unregularized fits for coefficient and prediction convergence rather than continue
arbitrary geometric grid expansion. No regularization value is frozen.

The explicit convergence comparison measures `C = 100, 300, 1000, 3000` and an
unregularized fit on identical grouped development folds. At 90.41% measured UCD
recall, macro priority retention is 2.25%, 1.91%, 1.88%, 2.03%, and 2.03%,
respectively. `C = 3000` and the unregularized model have identical aggregate
operating-point decisions; `C = 1000` is slightly better on the fixed split and
retains finite regularization. It is therefore the candidate for repeated stability,
with 3000 and unregularized fits retained as convergence comparators. No value is
yet frozen.

Across ten paired grouped repeats, `C = 1000`, `C = 3000`, and unregularized fits
all retain exactly 90.41% of reliable UCDs. Median macro priority retention is
1.96%, 2.11%, and 2.11%, respectively. `C = 1000` wins seven paired repeats and
has a maximum fold coefficient norm of 5.35, versus 7.01 and 12.94. The recommended
finite regularization policy is therefore `C = 1000`; it remains pending explicit
project-lead freeze approval.

The project lead approved and froze `C = 1000` on 2026-07-18 under
`point_source_logistic_policy_v1`. The model family, L2 regularization, nine-feature
contract, fold-local imputation and scaling, benchmark-v3 reliable-training policy,
and equal priority-cohort weighting are recorded in the machine-readable policy.
This approval freezes regularization only. The probability threshold is not frozen,
no final full-development model is authorized yet, and validation remains sealed.

The frozen-`C = 1000` repeated source audit identifies ten persistent reliable-UCD
misses. Five are multiply published faint Virgo UCDs with two-parameter Gaia
solutions and 7.12--10.06 mas excess noise; three are spectroscopic Saifollahi A1
systems with published sizes; one is a Gregg spectroscopic object; and one is a
Voggel NGC 5128 object whose significant Gaia motion is paired with a 0.019-arcsec
match and extended-source quality anomalies. None is excluded. These objects remain
in completeness accounting to avoid biasing the reliable sample toward easy,
point-like Gaia sources.

The project lead approved and froze the operating threshold on 2026-07-18. The
calibration rule takes the median of ten grouped out-of-fold thresholds, where each
repeat threshold is the lowest reliable-UCD score retaining at least 90%. The
repeat thresholds span 0.8149084969--0.8419524172 and give the frozen value
0.8277833629. Applied to the full development fit, this threshold has apparent
92.47% reliable-UCD recall and 1.65% macro priority-contaminant retention. These
full-fit values are descriptive, not validation performance. Validation remains
sealed until the final model artifact and parity checks are complete.

`point_source_logistic_model_v1` is the final fitted development artifact. It uses
146 reliable UCDs and 1,966 priority contaminants, serializes the complete imputation,
scaling, and logistic pipeline, and exposes all fitted parameters in a transparent
JSON manifest. Reloaded probabilities agree with stored development probabilities
to `1.11e-16`; all eight provenance, parity, feature-contract, and blind-safety
checks pass. Apparent full-development recall is 92.47% and macro priority retention
is 1.65%, neither of which is validation performance. Model fitting and verification
do not unseal validation.

The authorized one-time frozen validation evaluation is complete. On 721 independent
rows, the model retains 21/23 reliable UCDs (91.30%), 0/287 Gaia NSS objects, and
1/88 spectroscopic QSOs; macro retention across the available priority cohorts is
0.57%. It retains 87.43% of spectroscopic galaxies and 52.63% of compact H II
regions, confirming that these remain second-round imaging and photometric problems.
No retuning is authorized. Dorado1 is recorded post hoc as a 34.57-sigma-motion,
0.769-arcsec UCD/Gaia conflict, but its frozen validation label and outcome remain
unchanged. M85-HCC1 remains a genuine hard-UCD false negative.

## Host-Galaxy Properties

The primary host-correlation analysis requires the following properties:

- galaxy luminosity, using the most widely available consistent measurement in the
  host database rather than a photometric band fixed in advance;
- galaxy size, expressed as `R50` measured in a consistent band across the sample;
  and
- galaxy morphology.

Optical color, environment, and central velocity dispersion are not mandatory.
They may be included when they are available for a significant and scientifically
usable fraction of the sample. Other host properties may also be explored when
available.

Property provenance, measurement band, uncertainty, coverage fraction, and
missingness must be recorded. Optional-property analyses must be identified as
such and must not be selected only after inspecting which property produces a
desired correlation.

The luminosity band is not a critical scientific choice at this stage. The current
K-band luminosity has complete coverage and is a practical starting point, but it
is not mandatory if another consistent measurement later provides better usable
coverage. Incomparable bands must not be mixed within one correlation without a
documented calibration.

Missing `R50` or morphology does not remove an otherwise eligible galaxy from the
primary Gaia overdensity analysis. It affects only correlation analyses that
require the missing property. For these nearby galaxies, the required information
is expected to be recoverable through careful literature and database searches and
cross-matching. Missing values should be completed from provenance-bearing sources
rather than used to narrow the overdensity sample or filled by undocumented
imputation.

## Signal Aperture and Central Exclusion

During the exploratory stage, the search should retain a series of annular
measurements rather than reduce each host immediately to one signal aperture. The
annular profiles will be used to calibrate a final host-scaled definition.

The intended final signal region may take the form `[M, N] x R50`, with `M` and `N`
determined from validated behavior rather than assumed now. The analysis should
also exclude an inner region representing the main body of the galaxy, where
galaxy substructure, compact star-forming regions, and source-extraction artifacts
can dominate.

- When a measured, consistent-band `R50` is available, it should anchor the inner
  exclusion and host-normalized annuli.
- When `R50` is temporarily unavailable, a luminosity- or stellar-mass-to-`R50`
  relation may provide an estimated inner limit, with the relation and uncertainty
  calibrated from galaxies with measurements.
- An inner limit such as `2 x R50` is an initial example, not an approved fixed
  threshold.
- Physical-kpc profiles should be retained alongside normalized profiles so the
  behavior and inferred aperture can be audited.

Using observed target excesses to choose `M`, `N`, or the inner limit can introduce
confirmation and look-elsewhere bias. The final definition must therefore be
calibrated on declared reference or development data and validated separately, or
the radial scan must be treated as exploratory with its trial factors included.

## Galactic-Latitude Eligibility

The final sample should use a conservative absolute Galactic-latitude cut, but the
threshold must be measured rather than adopted from the inherited 20-degree or
30-degree exploratory cuts.

1. Apply the canonical Gaia selection to fields spanning a range of absolute
   Galactic latitude.
2. Measure where Milky Way background density and its field-to-field variation
   become too large to support a meaningful UCD overdensity constraint.
3. Freeze a conservative `|b|` limit from that experiment before the final host
   analysis.

Low-latitude fields remain useful for diagnosing contamination behavior, even when
they are excluded from the final inferential sample. The experiment and final cut
must use the same versioned Gaia selection and background definition as the host
analysis.

No minimum sensitivity criterion is known in advance. This systematic calibration
is itself new work for the project. The analysis should first measure background
variance and achievable overdensity sensitivity across latitude, then derive and
justify the meaningful-constraint criterion from those data. The criterion must not
be tuned to increase the number of detected host excesses.

## Groups and Clusters

The first-stage overdensity analysis should ignore environment as a selection or
methodological distinction. Galaxies in groups and clusters should initially be
processed with the same host-centered Gaia procedure as isolated galaxies.

Within 50 Mpc, the prominent groups and clusters are few and well known. They
should be flagged so they can be isolated for dedicated analysis later, without
removing them from the first-stage measurements.

Dense environments require explicit comparison of local and global background
definitions. A local estimate may contain a real intragroup or intracluster compact
system population, while a global estimate may better represent unrelated
foreground and background sources. The difference between these estimates is a
scientific diagnostic and systematic uncertainty; the method must not choose the
background that maximizes a desired excess.

## Overlapping Hosts

In the first-stage analysis, every galaxy is treated as an independent
host-centered case. When search regions overlap, the same Gaia source may
contribute to measurements around more than one galaxy.

The data model must preserve one source-to-many-host associations, including the
source's projected radius and selection quantities for each host. It must not
silently deduplicate a source to one galaxy or count host-source associations as
unique astrophysical objects in an aggregate candidate total.

Overlapping host measurements are not statistically independent even though the
first-stage processing is independent. Population analyses must identify this
dependence and test its effect. A later probabilistic procedure may assign the
probability that a source is a UCD associated with each plausible host; that model
is not required for the first exploratory round.

## Candidate Ranking and Host Context

It is currently unknown how a host's measured overdensity should affect the
probability that an individual source is a real UCD. The working suspicion is that
a genuine excess should increase candidate plausibility, but this is not yet an
approved probability term.

The first-round products should therefore preserve the Gaia-only source evidence
and the host-level overdensity as separate quantities. A later experiment may test
whether host overdensity provides a calibrated contextual prior.

This test must address circularity: the same sources used to measure an excess
cannot be allowed to boost their own probabilities without a valid statistical
model or separate validation. The effect should be revisited only after more
results and control measurements are available.

## Candidate and Confirmation Labels

BubbleTea may conclude at the candidate level. Confirmation of individual UCDs is
not a required project deliverable, and no confirmation yield should be assumed.

A Gaia-selected or statistically prominent source remains a candidate unless it
meets a high confirmation standard through either:

- space-based high-resolution imaging, such as HST or Roman data, that establishes
  resolved structure consistent with a UCD; or
- spectroscopy that provides a redshift or radial velocity consistent with the
  associated nearby system.

DESI or archival space-imaging overlap may provide rare confirmations, but these
are value-added opportunities. Candidate tables must keep the evidence type and
confirmation status explicit and must not describe Gaia extendedness or host
overdensity alone as confirmation.

## Literature Reference Data Model

The literature reference collection is rebuilt non-destructively as a versioned
database alongside the legacy `ucd_collection.db`. The legacy database remains an
immutable comparison input. Original machine-readable files, their cryptographic
hashes, table identifiers, and source-row locators are authoritative; processed
CSVs and legacy database rows are derived products.

The reference model separates publications, datasets, immutable literature rows,
canonical astrophysical objects, object-to-row associations, evidence, and derived
classification states. It must preserve rows without coordinates, repeated rows,
conflicting measurements, compilation reference codes, and aliases for corrected
bibliographic identifiers. Canonical identifiers must remain stable when records
are merged by retaining aliases for retired identifiers.

Exact coordinate equality may create an automatic identity association when no
identifier or host conflict exists. Non-exact Gaia or positional associations must
remain proposed until spherical geometry, the Gaia match, and ambiguity handling
are validated. Matching radii must be calibrated from measured reference behavior,
not assumed. Identity conflicts, `is_ucd` conflicts, ambiguous geometry, and every
promotion to confirmed status require human review.

The Gaia identity audit must recompute great-circle separations from authoritative
Gaia DR3 coordinates. Legacy `gaia_xmatch_dist` values were calculated with a
planar degree-space formula and are retained only as provenance. For the initial
117 shared-source groups, the maximum measured difference between the legacy
planar value and the spherical distance is 0.176110481759 arcseconds. A shared
Gaia detection is strong identity evidence but does not override multi-position,
Gaia image-parameter, or reported UCD-role review requirements.

Operational Gaia and Legacy Survey cross-matches must use a service-side spherical
cone and must independently recompute and enforce the requested radius with
great-circle separations. They must retain the number of in-radius candidates,
the nearest and second-nearest distances, their separation gap, and every
in-radius candidate identifier and coordinate. More than one in-radius candidate
is descriptive ambiguity evidence, not an automatic rejection or identity merge.
The historical one-arcsecond Gaia and two-arcsecond Legacy Survey defaults remain
explicit query parameters until their scientific calibration is completed; the
geometry repair does not validate those values as selection thresholds.

Canonical cross-match products must use the stabilized v2 canonical identifiers
and must include a complete target audit, not only successful matches. Gaia
source-ID synchronization preserves the 963 canonical associations represented
by 1,097 literature rows and 962 unique Gaia sources; canonical consolidation is
not missing-match loss. Legacy Survey matching is a fresh positional enrichment
of all 4,359 positioned canonical objects. A selected Legacy source shared by
multiple canonical targets is explicit association evidence and must not merge
those targets. Retrieval manifests must record the reference-database digest,
service and table, catalog release, radius, UTC timestamps, batch measurements,
row counts, and output digests. The older 632-row Gaia and 917-row Legacy files
remain hashed historical products and are not canonical inputs.

The approved Gaia cohorts contain 72 clean two-position groups, 14 separately
reviewed two-position role-conflict groups, 22 image-reviewed two-position groups,
and eight literature-reviewed three-position groups. Their canonical objects are
merged using the literature position nearest the authoritative Gaia DR3
coordinate, while every superseded canonical identifier remains an alias. No
shared-Gaia identity proposal remains open.

The three-position review preserves disagreement rather than using it to erase
source records. The F-6/Gregg 27 radial-velocity difference of 268 km/s, or 2.65
Gregg uncertainties, remains explicit moderate-tension evidence even though both
measurements indicate Fornax membership. The two identical Saifollahi table A1
rows at the F-1/UCD2 position remain separate immutable provenance records linked
to one canonical position.

A shared Gaia source is not itself an identity equivalence. S547 and VUCD3 remain
separate canonical objects because the Fahrion source table preserves distinct
positions, references, magnitudes, and effective sizes. Both objects retain
approved `ambiguous_shared_gaia_dr3` evidence for their unresolved shared Gaia
source. The Zhang and Fahrion S547 rows are associated with one another through
their identical name, consistent properties, and measured 0.058627924650-arcsecond
spherical separation; the superseded Zhang canonical identifier remains an alias.
Ambiguous shared-source evidence does not alter either object's classification.

Shared identity and UCD classification are separate decisions. When a reviewed
two-position Gaia group is accepted as one astrophysical object but its literature
records contain both `reported_is_ucd=0` and `reported_is_ucd=1`, the canonical
classification state is `uncertain` with subtype `reported_ucd_role_conflict`.
Both reported labels and their source provenance remain unchanged. This subtype
must not be treated as a positional-identity ambiguity or silently collapsed to a
positive or negative training label.

Literature discovery is also separate from source ingestion. ADS title-and-
abstract screening must record the exact query set and a cryptographic hash of the
reviewed metadata corpus. A paper selected for retrieval does not create canonical
objects, approve source associations, or promote confirmation evidence. The
project lead must approve each proposed retrieval cohort before source files or
rows are added to the v2 reference database.

Project-lead-approved, source-specific associations may be accepted after a
row-level audit records the source role, name evidence, spherical separation, and
alternative matches. Such approval does not establish a general matching radius.
The initial approved set links 51 Liu M49/M60 `UCD=1` rows to exact-name Fahrion
counterparts within one arcsecond and 34 Voggel reference rows to their nearest
Fahrion or Dumont counterparts within one arcsecond. The additional Voggel
T17-1596 row is associated with Fahrion HHH86-C15 at 1.37 arcseconds through the
published Taylor GC0218 and Woodley HHH86-C15 alias chain. Four coordinate-null
Fahrion rows remain literature records with identity-review entries but no
canonical object association.

Object classification uses versioned evidence rules with four states:

- `confirmed`: positive spectroscopy consistent with the associated nearby system
  or approved space-based high-resolution morphology consistent with a UCD, with
  no unresolved contradictory evidence;
- `candidate`: reported UCD or UCD candidate, or Gaia-selected extended-source
  candidate, without approved confirmation evidence;
- `rejected`: explicit non-UCD evidence without contradictory positive
  confirmation evidence; and
- `uncertain`: conflicting evidence or unresolved object identity.

Source-wide ingestion labels, compilation membership, Gaia extendedness, and host
overdensity are evidence but never confirmation by themselves. The first ruleset
is identified as `confirmation_rules_v1`.

Broad literature selection pools must be stored separately from canonical positive
reference records. A paper's final candidate subset may link back to the pool
without promoting the entire pool. For Saifollahi et al. (2021), table A1 remains a
mixed spectroscopic UCD/GC reference table, table A5 is a 1,155-row selection pool,
and only the 44 table A6 "BEST" objects enter as unconfirmed UCD candidates. The 61
reported reference UCDs satisfy the paper's `g <= 21` and `0 <= rh < 75 pc`
criteria and have approved spectroscopic-membership evidence.

Liu M49/M60 primary rows retain their object-level UCD flags: 51 `UCD=1` rows are
unconfirmed candidates and 28 `UCD=0` rows are explicit non-UCD comparisons. Their
paired structural and redshift tables are supporting measurements. Voggel table 4
is a 57-row previously confirmed comparison/reference sample, distinct from the
paper's 632 new Gaia-selected candidates. Those 57 rows remain candidates because
the local table contains Gaia photometry but not the object-level spectroscopy or
resolved-structure evidence required by `confirmation_rules_v1`; this is a
reviewed non-promotion, not an unresolved decision.

The approved 2026-07-15 Wave 1 ingestion preserves 855 source-reported UCD or
possible-UCD rows as unconfirmed literature records and 1,484 explicit foreground,
background, GC, or contaminant rows as negative comparison records. No general
non-exact matching radius is introduced. The 904-object Wittmann Fornax compact-
system compilation remains a separate mixed selection pool, with its 355
structural rows linked as supporting payloads. The 109 Ahn spatial-kinematic bins
are one supporting measurement dataset for M59-UCD3, not independent objects.
Four exact Ko rows reported in both the GC and UCD tables retain both labels and
derive `uncertain / reported_ucd_role_conflict` classifications.

The Zhang, Fahrion, Ko, and Liu representations of S999 are one approved identity.
The canonical position remains the Gaia-bearing Fahrion position; the prior Zhang
canonical identifier is retained as an alias, and all four source rows, velocities,
names, and coordinate differences remain provenance. This object-specific decision
does not authorize other non-exact Wave 1 associations.

A second approved Wave 1 identity cohort links seven rows to six pre-Wave
candidate objects. Three Ko rows use identical source names and velocities;
four Liu rows use source-published aliases for M87UCD-1, M87UCD-38, M59-UCD3,
and M59cO, with matching velocities where both catalogs retain them. Each target
was the unique nearest pre-Wave canonical within one arcsecond. This is a
name-led, object-specific approval, not a general positional rule. All seven
superseded Wave canonical identifiers remain aliases. The 153 Wave rows whose
identifier matches intersect multiple baseline canonicals within one arcsecond
remain separate. Their read-only group audit resolves them into 91 connected
review groups. Twelve groups, containing 16 Wave rows and 24 pre-Wave canonicals,
have complete shared-identifier coverage, identical retained velocities, no Gaia
identifier conflict, and no reported UCD-role conflict. The project lead approved
their object-specific consolidation on 2026-07-15. Their 40 prior canonicals now
form 12 candidate objects, all 28 superseded canonical identifiers remain aliases,
and one approved group-level evidence record preserves each decision. The other 79
groups remain unchanged: 74 contain at least one nearby baseline canonical without
an identifier link, and five retain non-identical published velocities. These
routes are conservative review states, not evidence of distinct identity or a
general positional matching rule.

The project lead subsequently delegated the remaining source audit on 2026-07-15.
Original catalog lineage closes all 79 groups as 80 identities: 72 use exact Liu
2015 NGVS keys and published `Other` aliases, two use Brodie 2011 catalog evidence,
four preserve differing independent or weighted velocity measurements, and the
S547/VUCD3 connected group is split into its two previously reviewed distinct
objects. The builder moves 238 records, retains all 229 newly superseded canonical
identifiers as aliases, and stores 80 approved `identity_source_catalog_lineage`
evidence records. Seven identities with positive/negative source-role evidence
derive `uncertain / reported_ucd_role_conflict`; every velocity and source label
remains immutable provenance. The post-build audit has zero unresolved Wave 1
multi-canonical groups and still introduces no positional identity rule.

The completed Stage 1 source audit attaches all 168 intentionally supporting raw
rows as measurement evidence. It corrects the 27 Mieske Centaurus-cluster rows to
the source-stated 43 Mpc while retaining the erroneous legacy 3.8 Mpc values in
their immutable payloads, leaves the heterogeneous Fahrion compilation without a
blanket distance, and scopes Liu's 16.5 Mpc value to its 127 M87 rows. The Liu M87
primary table also corrects 35 unsafe legacy positive defaults to its authoritative
`UCD=0` values and supplies explicit M87 host labels.

Under `confirmation_rules_v1`, 1,316 approved spectroscopic evidence rows from 12
source-defined cohorts resolve to 740 confirmed canonical objects. The remaining
classification states are 1,515 candidate, 2,082 rejected, and 22 uncertain role
conflicts. All classifications are derived from preserved evidence; no reported
measurement is overwritten. The non-destructive validation product contains
5,049 literature records, 4,359 canonical objects, all 180 legacy exact duplicate-
coordinate groups, and only four coordinate-null Fahrion identity-review rows.

Literature expansion is evidence-first. Object-level catalogs and confirmation
evidence within 50 Mpc receive priority. More distant samples may be retained as
declared sensitivity tests, while methodology, contaminant, and formation papers
remain separate context unless they supply object-level reference data. Search
queries, pagination, screening decisions, data-access status, and retrieval dates
must be reproducible.

The 2026-07-15 discovery checkpoint hashes a 345-paper ADS metadata corpus with
zero pending title-and-abstract decisions. Nineteen approved sources were
retrieved. Eight remaining candidates have explicit ancillary, incremental,
mixed-distance, or distant-sensitivity dispositions and do not block Stage 1;
they remain discoverable for later enrichment.

## Per-Galaxy Excess Metric

The quantity used to represent a galaxy's UCD excess in host-property correlations
is an open methodological question. The project should experiment broadly with
background-subtracted counts, area-based densities, and appropriate host-normalized
quantities rather than approve one metric now.

There is no direct literature precedent for this specific Gaia-UCD application.
Methods from other fields with analogous signal-plus-background, spatial point
process, richness, or heterogeneous-detection problems may be used to guide the
experiments.

Candidate metrics must be evaluated by statistical calibration, uncertainty
behavior, robustness to background choice, distance-dependent sensitivity, and
performance on controls or simulations. The final metric must not be selected
because it creates the strongest correlation with a preferred host property.

## Final Galaxy Samples

The final analysis should distinguish an inferential primary sample from a broader
diversity sample.

### Primary Correlation Sample

The parent census should be drawn from a published nearby-galaxy catalog whose
paper provides an explicit completeness analysis. Suitable catalog families are
known to exist in multi-messenger astrophysics, including work designed for
gravitational-wave optical-counterpart searches and dark-siren cosmology. The
specific catalog remains to be selected through a literature review.

If the catalog's selection function is publicly available, BubbleTea should use
and verify it directly. Other catalogs may enrich identifiers, distances, and host
properties, but additions or corrections must be tracked separately so they do not
silently change the parent denominator or invalidate its published completeness
model.

Using that published selection function, define a lower host luminosity limit and
a volume over which the galaxy sample is close to luminosity-complete. A
completeness level such as greater than 80 percent is an initial example, not an
approved value until completeness is measured and verified for BubbleTea's sky
mask and required properties.

This sample is used for primary quantitative host-property correlations. Its
luminosity threshold, volume, sky mask, Galactic-latitude limit, and Gaia
sensitivity requirements must be fixed and reported before the final correlation
analysis.

### Valid Diversity Sample

Use the entire valid host sample to depict UCD excess across luminosity, size,
morphology, and other property spaces. This broader sample is intended to reveal
the diversity of systems and possible structures that a restrictive complete
sample might miss.

Results from the broader sample must be labeled as descriptive or exploratory when
its selection function does not support unbiased population inference. The current
luminosity-ranked Top-100 table is a development pilot, not either final sample.

## Gaia Scanning-Pattern Systematics

Gaia's scanning pattern may affect spatial resolution, astrometric sensitivity,
and the probability that a compact source is classified as non-point-like. This is
a difficult technical systematic and is not required to block the first-stage
experiments.

The initial working assumption is that Gaia data are spatially uniform enough for
the exploratory analysis after the approved Galactic-latitude and local-background
controls are applied. This assumption must be tested before final inference.

The final systematic check should examine whether selected-source density,
extendedness probability, or overdensity residuals correlate with available Gaia
coverage and astrometric-quality indicators or sky-position patterns associated
with the scan law. If a material dependence is found, it must be modeled, included
in uncertainty, or used to define an additional quality mask.

## Pending Interview Decisions

The following areas remain intentionally unspecified:

- The exact Gaia-only probability model and its validation protocol.
- The validated Gaia color combinations and boundaries for obvious blue
  contaminants.
- Probabilistic host association after the independent first-stage measurements.
- Calibrated role, if any, of host overdensity in individual candidate probability.
- Exact evidence-quality fields for candidate and confirmed-object labels.
- Validated per-galaxy excess metric and normalization.
- Selection of a published parent galaxy census with a verified completeness
  analysis for the primary correlation sample.
- Detailed group and cluster treatment after the environment-blind first stage.
- Data-driven methodology for defining a meaningful constraint and calibrating the
  final Galactic-latitude cut.
- Candidate-list validation requirements beyond the approved value-added role of
  ancillary imaging.
- Treatment of incompleteness, upper limits, and heterogeneous sensitivity in the
  host-property analysis.

## Execution Plan

The staged implementation and validation order is maintained in
`docs/plans/scientific_validation.md`. The cross-phase issue register is
`docs/todo.md`.
