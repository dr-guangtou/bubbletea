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
