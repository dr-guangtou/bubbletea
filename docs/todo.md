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

- [ ] **BT-003 - Reconcile the literature database non-destructively.**
  Evidence: The database contains 2,108 rows, 2,064 UCD-flagged rows, 1,928 exact
  coordinate pairs, and 180 exact duplicate-coordinate groups. Candidate and
  confirmed labels are mixed. The existing redundancy script deletes rows.
  Resolution criteria: Preserve every source record, define canonical objects and
  source associations, document confirmation labels, and produce a validation
  report without deleting provenance-bearing rows.
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
