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
