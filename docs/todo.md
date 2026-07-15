# BubbleTea Issue Register

**Created:** 2026-07-14
**Scope:** Open scientific, data, reproducibility, and implementation issues found
during the project takeover review

This file tracks cross-phase issues that do not belong to only one phase plan.
Phase-specific execution tasks remain in `docs/plans/`.

## Status and Priority

- Checkbox unchecked: open.
- Checkbox checked: resolved and verified.
- P0: blocks scientific interpretation or a reliable pilot rerun.
- P1: required before scaling or publishing a candidate catalog.
- P2: project-quality or maintenance work that does not currently block analysis.

## P0: Scientific Definition and Validity

- [x] **BT-001 - Define the scientific target population and create `docs/SPEC.md`
  (completed 2026-07-14).**
  Evidence: The repository alternates among UCDs, stripped nuclei, luminous or
  extended globular clusters, and generic compact stellar systems. `docs/SPEC.md`
  is required by `AGENTS.md` but is absent.
  Interview decision, 2026-07-14: The primary target is UCDs, not ordinary
  globular clusters. Because their physical boundary is fuzzy, retain Gaia-resolved
  objects that are probably too luminous or too large for ordinary globular
  clusters. The ordered outputs are: first, conclusive population-level evidence
  for or against an overdensity around nearby galaxies; second, correlations of
  that excess or non-detection with host properties; third, prominent unidentified
  UCD candidate lists ranked by the probability of being non-point-like.
  Distance is sensitivity-driven: seek greater completeness within 25 Mpc and only
  the most obvious Gaia-detectable UCDs from 25 to 50 Mpc. Quantitative luminosity
  and size limits must be measured as functions of distance and Gaia uncertainty
  properties. Other operational boundaries remain open as separately registered
  research issues. `docs/SPEC.md` records the approved initial specification.
  Resolution criteria: The project lead approves definitions, labels, distance
  scope, environmental questions, validation standards, and the role of Gaia
  selection. The decisions are recorded in `docs/SPEC.md`.

- [ ] **BT-002 - Freeze one versioned compact-source selection function.**
  Evidence: Phase I and Phase III use a 70/30 AEN-significance and BP/RP-excess
  score, while Phase IV uses a 60/30/10 score with a color term and different
  prefilters. All are called `Model C`.
  Interview decision, 2026-07-14: The primary statistical selector must use Gaia
  data alone. External imaging is value-added and must not change statistical
  sample membership or Gaia source counts. Gaia `BP-RP` is the starting color for
  rejecting obvious very blue star-forming or H II contaminants, and other
  Gaia-native color combinations may be explored. Exact thresholds require
  validation; no additional H II criterion is approved yet.
  Resolution criteria: One shared implementation contains all query prefilters,
  null handling, score terms, thresholds, and a version identifier. Literature,
  background, and radial-search scripts call the same implementation.
  Depends on: BT-001.

- [x] **BT-003 - Reconcile the literature database non-destructively (completed
  2026-07-15).**
  Evidence: The database contains 2,108 rows, 2,064 UCD-flagged rows, 1,928 exact
  coordinate pairs, and 180 exact duplicate-coordinate groups. Candidate and
  confirmed labels are mixed. The existing redundancy script deletes rows.
  Resolution criteria: Preserve every source record, define canonical objects and
  source associations, document confirmation labels, and produce a validation
  report without deleting provenance-bearing rows.
  Progress, 2026-07-14: Added a read-only audit and separate v2 schema/build, then
  reconciled the Saifollahi source into 61 operational
  spectroscopic reference UCDs and 587 comparison records from table A1, 44
  unconfirmed final candidates from table A6, and a separate 1,155-record table A5
  selection pool. The initial v2 checkpoint preserved 2,710 literature records and 2,331
  canonical objects, all 180 legacy duplicate-coordinate groups, and 26 non-exact
  Gaia association proposals across eight groups. Structural checks pass with five
  scientific-review gates still open. No legacy row was changed or deleted.
  Progress, 2026-07-14: The pending-row audit shows that the 79 Liu rows split
  into 51 `UCD=1` candidates already represented by sub-arcsecond v2 counterparts
  and 28 explicit `UCD=0` comparison rows with no counterpart within five
  arcseconds. Of 57 Voggel reference objects, 35 have exact or sub-arcsecond v2
  counterparts, one lies within five arcseconds, and 22 have none within five
  arcseconds. Four Fahrion rows remain coordinate-null. Membership is unchanged
  pending project-lead review.
  Progress, 2026-07-14: The project lead approved and the builder implemented the
  pending-row treatment. It preserves all 140 rows, accepts 51 Liu and 35 Voggel
  source associations, creates 28 Liu negative-comparison and 22 new Voggel
  reference objects, and retains four coordinate-null Fahrion records without
  canonical associations. T17-1596 is associated with HHH86-C15 through the
  published Taylor and Woodley alias chain, with its 1.37-arcsecond offset
  retained. The review queue contains 728 items and all invariants pass.
  Progress, 2026-07-14: Authoritative Gaia DR3 coordinates were retrieved for all
  117 source IDs represented by the 140 non-exact proposals. Spherical validation
  routes 72 groups to recommended shared-identity acceptance and retains 45 for
  explicit review: 23 Gaia image-ambiguity, 8 multi-position, and 14 combined
  identity/classification cases. No canonical membership changed. The largest
  measured difference from the legacy planar distance is 0.176110481759 arcsec.
  Progress, 2026-07-14: The project lead approved the 72 clean shared-Gaia
  identities. The builder merges those groups, records 72 approved identity
  evidence rows, retains 72 retired canonical identifiers as aliases, and leaves
  the other 45 groups as 65 explicitly routed proposals. The current build has
  2,368 canonical objects and 649 review items; all invariants pass.
  Progress, 2026-07-14: The project lead separately approved the 14 shared-Gaia
  identity groups with conflicting reported UCD/GC roles. They are merged as
  identities and labeled `uncertain / reported_ucd_role_conflict`, with both
  source labels preserved. The build now has 2,354 canonical objects, 86 retained
  canonical aliases, 49 proposals across 31 groups, and 642 review items.
  Progress, 2026-07-14: The 23 two-position image-ambiguity groups now have
  provenance-tracked five-arcsecond Gaia DR3 neighborhoods and Legacy Survey DR10
  data/model/residual cutouts. No group has a competing Gaia source within two
  arcseconds; one has a separate neighbor at 4.710023680999 arcseconds. Visual and
  source-table review recommends accepting 22 shared identities while retaining
  S547 and VUCD3 as separate objects sharing one unresolved Gaia source. No
  identity decision or database membership has changed pending project-lead
  review.
  Progress, 2026-07-14: The project lead approved and the builder implemented the
  split image-review treatment. Twenty-two groups are merged identities. Zhang
  and Fahrion S547 are consolidated at a measured 0.058627924650-arcsecond
  separation, while S547 and VUCD3 remain separate canonical objects with two
  approved `ambiguous_shared_gaia_dr3` evidence rows. The deterministic build has
  2,331 canonical objects, 109 retained aliases, 26 proposals across eight
  multi-position groups, and 618 review items. All invariants pass.
  Progress, 2026-07-14: The final eight multi-position groups were audited against
  authoritative Gregg, Fahrion, and Saifollahi tables, Brüns aliases, and a
  five-paper ADS metadata query. All eight combine three sub-arcsecond positions
  around one clean Gaia source with positive reported roles and consistent Fornax
  membership. Seven velocity comparisons agree within 1.7 Gregg uncertainties;
  F-6/Gregg 27 has a preserved 268 km/s (2.65-sigma) measurement tension. The
  audit recommends eight shared identities but changes no memberships pending
  project-lead review.
  Progress, 2026-07-15: The project lead approved all eight three-position
  shared-Gaia identities. The builder now merges them generically by declared
  position count, retains 16 additional canonical aliases, preserves the
  F-6/Gregg 27 velocity tension and both identical Saifollahi F-1/UCD2 rows, and
  leaves no shared-Gaia proposals. The deterministic build contains 2,315
  canonical objects (1,726 candidate, 575 rejected, 14 uncertain), 125 aliases,
  116 approved shared-Gaia identity evidence rows, and 584 review items. All 180
  legacy exact duplicate-coordinate groups remain represented, and the immutable
  legacy database hash is unchanged.
  Progress, 2026-07-15: A targeted 2015-2026 ADS title query exposed 45 papers
  absent from the original citation-led discovery set, including seven relevant
  object studies from 2015-2018. The exact 345-paper union was screened by title
  and abstract with corpus SHA-256
  `54619aad14b33d82ff9408d7da7db0190d2f14709673c0b7a4e4fcf702788f79`.
  Five sources are already ingested, 313 are context-only, and 27 are proposed
  for retrieval; no source membership changes are authorized pending project-lead
  review of the retrieval cohort.
  Progress, 2026-07-15: The project lead approved and the builder implemented the
  five-part Wave 1 treatment. The deterministic v2 product now preserves 5,049
  literature records and 2,059 separate pool records across 30 publications and
  22 datasets. Wave 1 contributes 855 unconfirmed positive records, 1,484 negative
  comparisons, a 904-row Wittmann mixed compact-system pool, and one Ahn evidence
  record referencing all 109 M59-UCD3 spatial bins. Four exact Ko UCD/GC conflicts
  remain `uncertain / reported_ucd_role_conflict`. Four S999 source rows share the
  Gaia-bearing Fahrion canonical, and the prior Zhang canonical identifier remains
  an alias. The build has 4,623 canonicals, 126 aliases, 587 review items, and no
  association proposals; all invariants pass and the legacy database is unchanged.
  Progress, 2026-07-15: A name-led audit screened all 2,324 Wave 1 rows not already
  linked to pre-Wave identities. It found 161 rows with direct-name or published-
  alias evidence. Seven rows have one unique nearest baseline canonical within one
  arcsecond and are proposed for project-lead approval; 153 rows intersect multiple
  baseline canonicals within one arcsecond and require group-level identity review.
  Four reused Fornax-style identifiers are spatially inconsistent by more than
  474,000 arcseconds and are explicitly not recommended. No general radius rule or
  database change was made.
  Progress, 2026-07-15: The project lead approved the seven-row high-confidence
  cohort. The builder links those rows to six reviewed pre-Wave candidates using
  `approved_wave1_name_or_alias_identity`, stores seven approved evidence records,
  and retains all seven superseded Wave canonical identifiers as aliases. The
  deterministic build now has 4,616 canonicals (2,547 candidate, 2,051 rejected,
  and 18 uncertain), 133 aliases, and 587 review items. The 153 multi-canonical
  cases and four distant identifier collisions remain unchanged.
  Progress, 2026-07-15: A read-only group audit covers all 153 multi-canonical
  rows in 91 connected groups and retains all 200 nearby pre-Wave canonical
  contenders. Twelve groups containing 16 Wave rows and 24 pre-Wave canonicals
  have complete shared-identifier coverage, identical retained velocities, no
  distinct-Gaia conflict, and no reported-role conflict; they are proposed for
  project-lead review. Of the 79 unchanged manual groups, 74 contain at least one
  nearby canonical without an identifier link and five retain non-identical
  published velocities. No identity, membership, classification, or production
  database state changed.
  Progress, 2026-07-15: The project lead approved all 12 complete shared-identifier
  groups. The builder now consolidates their 40 prior canonicals into 12 candidate
  objects, stores 12 approved group-level identity evidence records, and retains
  all 28 superseded canonical identifiers as aliases. The deterministic v2 product
  has 4,588 canonicals (2,519 candidate, 2,051 rejected, and 18 uncertain), 161
  aliases, and 575 review items. A post-build audit leaves exactly 79 manual groups
  covering 137 Wave rows and produces no new proposals. All 180 exact duplicate-
  coordinate groups remain preserved and the legacy database is unchanged.
  Progress, 2026-07-15: Under the project lead's delegated source-audit authority,
  the remaining 79 groups resolve into 80 identities. Seventy-two follow exact Liu
  2015 NGVS keys and published aliases, two use Brodie catalog evidence, four
  preserve differing independent or weighted velocity measurements, and S547 and
  VUCD3 remain two distinct identities. The builder moves 238 records, stores 80
  approved source-lineage evidence records, and retains 229 additional superseded
  canonical identifiers as aliases. The deterministic v2 product now has 4,359
  canonicals (2,290 candidate, 2,048 rejected, and 21 uncertain), 390 aliases, and
  493 review items. The post-build Wave 1 multi-canonical audit is empty; all 5,049
  literature records, all 180 exact duplicate-coordinate groups, and the unchanged
  legacy database remain preserved.
  Completion, 2026-07-15: Closed all four remaining validation gates. The 168
  supporting raw rows are object-linked as measurements; host and distance
  normalization is source-scoped; 1,316 approved spectroscopic evidence rows
  produce 740 confirmed canonicals; and the hashed 345-paper literature screen has
  zero pending decisions. The final v2 database preserves 5,049 literature records
  and 4,359 canonical objects classified as 740 confirmed, 1,515 candidate, 2,082
  rejected, and 22 uncertain. The only remaining review rows are four coordinate-
  null Fahrion provenance records. Validation passes with no open Stage 1 gates,
  all 180 legacy duplicate-coordinate groups are reproduced, the legacy SHA-256 is
  unchanged, and no destructive redundancy operation was used.
  Depends on: BT-001.

- [ ] **BT-004 - Synchronize Gaia and Legacy Survey cross-match products.**
  Evidence: The database has 1,097 Gaia matches, while the Gaia export has 632
  rows. The Legacy export has 917 rows, while the current database has zero Legacy
  IDs.
  Resolution criteria: A reproducible export from the canonical database matches
  database counts and records query service, catalog release, radius, timestamp,
  and match-quality fields.
  Depends on: BT-003, BT-007.

- [ ] **BT-005 - Make local-background estimation valid for nearby galaxies.**
  Evidence: The 2-degree query cap reaches only 129.2 kpc at 3.7 Mpc. M81 and
  NGC 253 therefore contain no data in the declared 150-300 kpc background
  annulus, producing zero background densities and undefined contrasts.
  Resolution criteria: The search either covers the full background annulus or
  uses documented large-area and off-target circular or annular controls. Controls
  match or model Galactic latitude, lie beyond a conservatively buffered upper
  estimate of `R200c`, and exclude regions influenced by other nearby galaxies.
  Competing valid methods are compared and their differences propagated. The
  workflow must fail explicitly when required area is missing rather than
  reporting zero background.
  Depends on: BT-001, BT-002.

- [ ] **BT-006 - Replace the pilot significance diagnostic with a validated
  statistical model.**
  Evidence: Significance is currently `(observed - expected) / sqrt(expected)` and
  does not propagate local-background uncertainty, selection effects, overlapping
  apertures, or small-count behavior.
  Interview decision, 2026-07-14: Use an initial 3-sigma overdensity standard
  within a defined radial range, retain positive, zero, and negative measurements,
  and include every eligible galaxy in population analyses. Null results are
  acceptable. Low-mass dwarfs should help diagnose false positives, including
  compact star-forming and H II regions.
  Resolution criteria: `docs/SPEC.md` defines the null hypothesis and statistic;
  simulations or control fields calibrate the radial range and full background
  uncertainty; trial factors are handled; outputs distinguish exploratory ranking
  metrics from inferential significance.
  Depends on: BT-001, BT-002, BT-005, BT-021.

- [ ] **BT-007 - Correct and validate spherical cross-match geometry.**
  Evidence: Gaia and Legacy scripts retrieve rectangular boxes, calculate planar
  coordinate differences without the right-ascension cosine factor, and retain
  the nearest row without enforcing the requested cone radius.
  Resolution criteria: Use a spherical separation or service-side cone match,
  enforce the radius, retain ambiguity diagnostics, and validate against known
  matches at representative declinations.

- [ ] **BT-008 - Repair literature-recovery and new-candidate validation.**
  Evidence: Each host is matched against the full literature database rather than
  an eligible host-region subset. The unmatched-candidate calculation uses
  literature indices against candidate row indices.
  Resolution criteria: Define the eligible literature denominator per host, match
  in the correct index direction, report completeness with denominators, and test
  on at least one known rich host and one control target.
  Depends on: BT-002, BT-003, BT-007.

- [ ] **BT-019 - Build a labeled reference and contaminant benchmark.**
  Evidence: The Gaia-only non-point-source probability is an open research
  question. The literature collection mixes confirmed UCDs with candidates that
  may be wrong, while the present selector has no documented point-source and
  contaminant benchmark.
  Interview decision, 2026-07-14: Explore the existing UCD sample with label
  uncertainty; spectroscopic QSOs and compact galaxies in the relevant magnitude
  range from surveys such as SDSS, GAMA, and DESI; published Gaia binary-star
  references with Gaia binarity evidence; and compact star-forming or H II regions
  around star-forming, spiral, and dwarf galaxies.
  Resolution criteria: Produce a provenance-complete benchmark with confidence
  tiers, relevant magnitude and sky coverage, fixed development and validation
  partitions, and explicit tests of sensitivity to uncertain UCD labels.
  Depends on: BT-003, BT-014.

- [ ] **BT-021 - Calibrate the host-scaled signal aperture and inner mask.**
  Evidence: Fixed physical bins do not scale with galaxy size, while central galaxy
  substructure and compact star-forming regions can create false excesses. The
  final `[M, N] x R50` signal region and inner exclusion are not yet defined.
  Interview decision, 2026-07-14: Preserve annular profiles during exploration;
  use measured `R50` where possible; allow a calibrated luminosity- or stellar-mass
  to-`R50` relation for temporary estimates; and explore an inner mask such as
  `2 x R50` without fixing that example in advance. Retain physical-kpc profiles.
  Resolution criteria: Declare development and validation data; calibrate `M`,
  `N`, and the inner limit with uncertainty; test sensitivity to the `R50` band and
  estimation method; and account for radial-scan trial factors.
  Depends on: BT-002, BT-006, BT-020.

- [ ] **BT-022 - Calibrate and freeze the Galactic-latitude limit.**
  Evidence: Milky Way contamination varies strongly with Galactic latitude. The
  inherited sample uses `|b| > 20` degrees and the pilot uses 30 degrees, but those
  values were not calibrated with one canonical selection function.
  Interview decision, 2026-07-14: Experiment across Galactic latitude, identify
  where background density is too high for meaningful constraints, and apply a
  conservative `|b|` cut to the final sample. No minimum sensitivity is known in
  advance; deriving a defensible criterion from the data is part of the research.
  Resolution criteria: Define a meaningful-constraint metric; measure background
  density and variance across `|b|` with the canonical selector; freeze and record
  the conservative threshold before final host inference; preserve excluded fields
  as contamination diagnostics.
  Depends on: BT-002, BT-009.

## P1: Pilot Reproducibility and Scale-up

- [ ] **BT-009 - Recompute the background experiment with the canonical
  selection.**
  Evidence: Phase III omits the Phase IV proper-motion filter and color score. Its
  density model is therefore not calibrated to the pilot selector. It also divides
  by 2.0 square degrees instead of the measured 2.010619 square degrees for a
  0.8-degree-radius circle.
  Resolution criteria: Background and pilot use BT-002, exact usable areas are
  recorded, failures are preserved, and the latitude model includes uncertainty
  and a stated applicability domain.
  Depends on: BT-002.

- [ ] **BT-010 - Make pilot runs atomic, resumable, and auditable.**
  Evidence: The current summary contains 17 targets rather than the intended 20.
  M49, M59, and NGC 1097 are absent, while a stale M49 candidate/profile pair
  remains on disk. A rerun overwrites the summary without a run identifier.
  Resolution criteria: Each run has configuration metadata, target status,
  failures, timestamps, and an immutable run identifier. Aggregation includes only
  products from the selected run and can resume safely.
  Depends on: BT-002, BT-005.

- [ ] **BT-011 - Build a host-aware master candidate catalog.**
  Evidence: The current 18 candidate files contain 18,552 rows but only 17,995
  unique Gaia source IDs; 557 sources occur in multiple host files.
  Interview decision, 2026-07-14: Treat each host-centered case independently in
  the first round and allow one Gaia source to contribute to multiple hosts. Do not
  collapse or silently double-count these associations in aggregate products.
  Resolution criteria: Store one Gaia-source record with one-to-many host
  associations, projected radii, selection version, and per-host statistics.
  Depends on: BT-010.

- [ ] **BT-023 - Develop probabilistic host association after the first round.**
  Evidence: Overlapping halos create one-to-many source-host associations, and a
  uniquely assigned host is not justified during the exploratory search.
  Interview decision, 2026-07-14: Preserve independent host measurements first;
  later assign the probability that a source is a UCD associated with each target.
  Resolution criteria: Define and validate host-membership probabilities, retain
  ambiguous associations, and quantify the effect of shared sources on population
  correlations and uncertainties.
  Depends on: BT-011, BT-012, BT-021.

- [ ] **BT-024 - Test whether host overdensity improves candidate probability.**
  Evidence: A real host excess may make individual UCD candidates more plausible,
  but no current result establishes how large that effect is or whether it is
  useful.
  Interview decision, 2026-07-14: Pin this question until more results are
  available. Preserve Gaia-only source evidence and host overdensity separately in
  the first round.
  Resolution criteria: Define a non-circular statistical model or independent
  validation design; test calibration and ranking improvement on held-out hosts or
  controls; document whether host context is retained as a candidate prior.
  Depends on: BT-006, BT-008, BT-011, BT-019.

- [ ] **BT-028 - Implement explicit candidate and confirmation labels.**
  Evidence: Current catalogs mix confirmed and candidate literature entries, while
  Gaia-selected sources do not have a defined evidence-level schema.
  Interview decision, 2026-07-14: Candidate-level conclusions are sufficient.
  Confirmation requires either space-based high-resolution imaging establishing
  UCD-like resolved structure or spectroscopy consistent with the nearby system.
  Confirmation opportunities may be rare and are not mandatory.
  Resolution criteria: Define provenance-bearing evidence and status fields;
  migrate literature labels without overstating certainty; keep Gaia-only and
  overdensity-selected sources as candidates; validate status transitions.
  Progress, 2026-07-14: Implemented versioned `confirmation_rules_v1`, evidence
  records, four derived states, transition fixtures, and mandatory review for
  every confirmation promotion. The current draft deliberately contains no
  confirmed objects until evidence reviews are approved.
  Depends on: BT-003, BT-008, BT-013, BT-023.

- [ ] **BT-025 - Compare and validate per-galaxy excess metrics.**
  Evidence: No established metric currently defines how background-subtracted
  counts or densities should be normalized across galaxies of different size and
  luminosity, and there is no direct literature precedent for this Gaia-UCD use
  case.
  Interview decision, 2026-07-14: Experiment broadly and seek methods from relevant
  fields with analogous statistical problems. Do not select a metric because it
  strengthens a preferred host correlation.
  Resolution criteria: Compare candidate metrics using controls or simulations,
  uncertainty calibration, background robustness, distance sensitivity, and
  interpretability; document the approved primary and secondary metrics before the
  final correlation analysis.
  Depends on: BT-002, BT-005, BT-006, BT-021.

- [ ] **BT-026 - Define the complete primary and broad diversity samples.**
  Evidence: The current Top-100 pilot is luminosity-ranked and cannot support
  unbiased host-property correlations. The completeness of the 2,155-galaxy parent
  table has not been measured against a defined galaxy census.
  Interview decision, 2026-07-14: Define a lower luminosity limit and volume giving
  a nearly luminosity-complete primary correlation sample; greater than 80 percent
  is an example, not a fixed requirement. Also use the entire valid sample to show
  the diversity of UCD excess across host-property space.
  Resolution criteria: Select a parent census; measure completeness versus
  luminosity, distance, and sky position; freeze the primary sample limits; record
  all exclusions; and label broader-sample results as descriptive or exploratory
  where unbiased inference is unsupported.
  Depends on: BT-001, BT-015, BT-020, BT-022, BT-027.

- [ ] **BT-027 - Select a published completeness-calibrated galaxy census.**
  Evidence: The current galaxy table is merged from several sources and does not
  carry one documented selection function suitable for primary population
  inference.
  Interview decision, 2026-07-14: Draw the parent sample from published nearby-
  galaxy work with a completeness analysis, including consideration of catalogs
  built for gravitational-wave counterpart searches or dark-siren cosmology. Use
  a publicly available selection function when one is provided; keep enrichment
  from secondary catalogs separate from the parent denominator.
  Resolution criteria: Review candidate catalogs and their papers; compare sky,
  distance, luminosity, completeness, identifier, and property coverage; select and
  document the parent census; reproduce or verify the relevant published
  completeness result for BubbleTea's mask.

- [ ] **BT-029 - Test Gaia scanning-pattern systematics before final inference.**
  Evidence: Gaia's scan pattern can change observation geometry, astrometric
  quality, and effective sensitivity to marginal source extension across the sky.
  The current pipeline does not test this dependence.
  Interview decision, 2026-07-14: Assume Gaia is uniform enough for first-stage
  exploration, but retain scan-pattern sensitivity as a required final check.
  Resolution criteria: Test selected-source density, extendedness probability, and
  overdensity residuals against available Gaia coverage and astrometric-quality
  indicators or scan-law-related spatial patterns; model the effect, propagate it,
  or define a justified quality mask if it is material.
  Depends on: BT-002, BT-006, BT-009, BT-022.

- [ ] **BT-012 - Flag dense environments for dedicated secondary analysis.**
  Evidence: The pilot `is_cluster` flag uses rough sky circles around Virgo and
  Fornax. The reported 93 field targets are therefore not a defensible field
  sample.
  Interview decision, 2026-07-14: Environment is optional rather than mandatory
  for the primary host-correlation analysis. Use it only if a significant and
  scientifically usable fraction of the sample receives defensible measurements.
  Apply the same first-stage host-centered procedure to all galaxies, flag the
  small set of well-known groups and clusters within 50 Mpc, and analyze them
  separately later. Compare local and global backgrounds in dense environments.
  Resolution criteria: Replace the rough proxy with provenance-bearing flags for
  known dense systems; preserve first-stage measurements; quantify local-versus-
  global background sensitivity; and define any later membership analysis without
  selecting the background that maximizes excess.
  Depends on: BT-001.

- [ ] **BT-020 - Complete the mandatory host-property table.**
  Evidence: Luminosity, consistently measured `R50`, and morphology are required
  for the primary host-correlation analysis. The current 2,155-galaxy sample has
  K-band luminosity for all rows, morphology for only 200 rows in the base table,
  and no `R50` column. The separate HyperLEDA product has morphology for 457 rows.
  Interview decision, 2026-07-14: Missing `R50` or morphology never removes an
  otherwise eligible host from the primary overdensity analysis. Retrieve the
  missing information through careful literature and database cross-matching; only
  the relevant correlation analysis is limited while a property remains missing.
  The luminosity band is flexible and should maximize consistent usable coverage;
  the current complete K-band measurement is a practical starting point.
  Resolution criteria: Compile provenance-bearing luminosity, consistent-band
  `R50`, and morphology with uncertainties or quality indicators; quantify
  coverage and missingness; define the analysis policy for missing required
  properties without altering the Gaia overdensity measurements.
  Depends on: BT-001, BT-015.

- [ ] **BT-013 - Document ancillary imaging coverage without selection bias.**
  Evidence: Legacy Survey coverage was checked for only 500 galaxy centers with a
  small box. Center coverage does not establish usable imaging across a 300 kpc
  candidate region, and HSC coverage remains unchecked.
  Interview decision, 2026-07-14: Imaging is value-added only. Multi-band data may
  support SED or color-color checks, and HST, Euclid, or other high-resolution data
  may test morphology. Significant Gaia excesses may receive targeted imaging
  analysis later.
  Resolution criteria: Record footprint and depth over the relevant aperture for
  each ancillary survey, but do not use coverage to determine membership in the
  Gaia statistical sample. Label all covered-subset and follow-up analyses.
  Depends on: BT-001.

- [ ] **BT-014 - Complete literature provenance packages.**
  Evidence: Nine sources are ingested, but only `reference/voggel2020/` and
  `reference/wang2023/` follow the required paper-folder convention. Several
  source metadata files and counts are stale or contradictory.
  Resolution criteria: Every ingested source has a correctly named folder,
  bibliographic identifiers, source PDF or documented access status, original
  machine-readable data, and a provenance README.
  Progress, 2026-07-14: Retrieved 34 authoritative VizieR files into 11 source
  packages, recorded SHA-256 hashes and row counts, and added provenance READMEs.
  PDF acquisition or documented access status and raw-row reconciliation remain
  open.
  Progress, 2026-07-15: Retrieved the project-lead-approved 19-source Wave 1
  cohort: 19 structurally valid PDFs (365 pages), five VizieR packages (11 tables,
  4,535 preserved rows), and four publisher XLSX source-data files. The retrieval
  report is deterministic and every file has a SHA-256 digest. The table-role and
  positional-overlap review remains open; no new source row has changed canonical
  membership, identity, classification, or confirmation.
  Progress, 2026-07-15: Registered the five Wave 1 VizieR packages as 16 hashed raw
  provenance files and implemented the approved row roles in v2. The 19 PDFs and
  four publisher workbooks remain source-package provenance; no reported
  confirmation was promoted automatically. Object-level evidence review for the
  remaining PDF-only sources is still open.
  Depends on: BT-003.

- [ ] **BT-015 - Reconcile plans, journals, summaries, and data manifests.**
  Evidence: `README.md`, `docs/PLAN.md`, `data/README.md`, `reference/summary.md`,
  and phase trackers disagree about sample sizes, match rates, distance limits,
  and phase status.
  Resolution criteria: All headline counts are generated or verified from the
  canonical products, statuses reflect unresolved validation work, and documents
  link to the applicable selection and run versions.
  Depends on: BT-001 through BT-014 where applicable.

## P2: Implementation Quality

- [ ] **BT-016 - Pass the configured Ruff and pre-commit checks.**
  Evidence: All 23 active Python files parse, but `ruff check scripts` reports 397
  violations, including unfinished and unused code in addition to formatting.
  Resolution criteria: `uv run ruff check scripts` and
  `uv run pre-commit run --all-files` complete successfully without changing
  scientific behavior.

- [ ] **BT-017 - Move shared scientific constants and calculations out of scripts.**
  Evidence: Magnitude limits, score weights, radial bins, proper-motion rules,
  query radii, and background definitions are duplicated across phases and have
  already diverged.
  Resolution criteria: Versioned configuration and shared utilities are the sole
  sources for BT-002 and BT-006 behavior, with scripts recording the values used.
  Depends on: BT-001, BT-002, BT-006.

- [ ] **BT-018 - Add script-level validation for deterministic calculations.**
  Evidence: The repository intentionally does not use pytest, but currently lacks
  equivalent checks for selector parity, angular conversions, annular areas,
  cross-match geometry, duplicate handling, and recovery indexing.
  Resolution criteria: Standalone validation scripts run quickly on fixed fixtures
  and fail with a nonzero status when an invariant is violated.
  Depends on: BT-002, BT-003, BT-005 through BT-008.

## Review of This Registration

- [x] Review findings were converted into persistent, uniquely identified issues
  on 2026-07-14.
- [x] Each issue records observed evidence and verifiable resolution criteria.
- [x] Scientific-validity blockers are separated from scale-up and maintenance
  work.
- [x] No issue was marked resolved merely because it was documented.
