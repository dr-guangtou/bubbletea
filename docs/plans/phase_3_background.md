# Phase III: Background Characterization — Task Tracking

**Goal:** Measure the spatially varying density of sources passing the frozen Gaia
selector and provide valid host-specific controls.

**Status:** Large-sky development and reserved-field validation complete; real-host
annulus calibration remains

**Checkpoint (2026-10-12):** All 500 random-field measurements and the one-time
102-field validation are complete. Direct measurements, not a fitted sky model,
are the primary large-sky reference. Host-specific background validity and full
inferential uncertainty remain open. Earlier approved designs below are dated
history; see [current status](../current_status.md), [validation report](../development/background_measurements.md#record-large_sky_validation_run),
and [roadmap](../PLAN.md).

## III.1 Control design

- [x] Audit the inherited random-field, annulus, and legacy background methods
  (2026-07-18).
- [x] Draft the three-layer background design and permanent failure-state rules
  (2026-07-18).
- [x] Approve paired off-target controls as primary, with a valid local annulus and
  large-field model as robustness methods (2026-07-18).
- [x] Block inferential background assignment for unresolved group or cluster
  environments while retaining exploratory profiles (2026-07-18).
- [x] Permit a conservative K-luminosity-based upper `R200c` proxy for isolated
  centrals in the geometry fixture only (2026-07-18).

## III.2 Geometry validation

- [x] Build the five-case geometry-only fixture (2026-07-18).
- [x] Validate spherical aperture areas, halo exclusion, neighboring-halo screening,
  and explicit unavailable states; all nine checks pass (2026-07-18).
- [ ] Freeze control-candidate generation before inspecting selected-source counts.

## III.2a Environment reference

- [x] Stage Kourkchi-Tully 2017 member and group tables outside the repository with
  source identifiers and SHA-256 provenance (2026-07-18).
- [x] Audit all 2,155 hosts and accept 1,792 unique associations within the
  shift-calibrated 5-arcsec rule; preserve 2 ambiguities and 361 unmatched hosts
  (2026-07-18).
- [x] Audit whether accepted group `R2t` and association `R1t` provide conservative
  exclusion geometry; neither is a universal one-radius solution (2026-07-18).
- [ ] Approve separate exclusion treatment for isolated principals, ordinary groups,
  and rich groups or clusters.

## III.3 Frozen-selector background experiment

- [x] Freeze four off-target development and four held-back validation fields using
  host roles and geometry only; all 14 checks pass (2026-07-18).
- [x] Select a deterministic five-host review set without using Gaia source counts
  (2026-07-18).
- [x] Run one bounded target/two-comparison field-condition query without applying
  the selector; all six checks pass in 11.19 seconds (2026-07-18).
- [x] Extend pre-selector measurements to all five review hosts using 13 frozen
  patches; all nine checks pass in 46.93 seconds, and no patch is approved as a
  scientific background (2026-07-18).
- [x] Recompute the random-field experiment with exact usable areas and the shared
  frozen selector (development 2026-07-19; validation 2026-08-11).
- [x] Replace the unseeded random coordinates with a deterministic 500-field sky
  grid and freeze 398 development and 102 held-back fields; all 16 checks pass
  (2026-07-19).
- [ ] Calibrate matching tolerances and the conservative Galactic-latitude limit.

Large-sky grid progress, 2026-07-19:

- [x] Preserve the inherited 500-field count and 0.8-degree diagnostic radius while
  using the exact 2.010586633-square-degree spherical area.
- [x] Place 250 deterministic, equal-sky-area centers in each Galactic hemisphere
  over the catalog domain `|b| >= 20` degrees.
- [x] Keep each broad sky block wholly in development or validation and cover all
  declared Galactic- and ecliptic-latitude bands in both partitions.
- [x] Record represented group, association, and project-host intersections as
  count-blind sensitivity flags without deleting or scientifically approving a
  field.
- [x] Measure pre-selector Gaia conditions for all 398 development fields; keep all
  102 validation fields unopened (2026-07-19).
- [x] Freeze a 12-field development retrieval pilot before Gaia queries: ten
  hemisphere/latitude representatives plus two ecliptic-band supplements; all ten
  checks pass (2026-07-19).
- [x] Benchmark the full 19-column 0.8-degree retrieval on `sky_field_0000`: 84,025
  rows in 26 strips, controlled stop/resume successful, and all 18 checks pass
  (2026-07-19).
- [x] Retrieve and score all 12 frozen development pilot fields: 275,404 Gaia rows,
  11,583 passing candidates, 83 strips, and all nine aggregate checks pass
  (2026-07-19).
- [x] Measure pre-selector Gaia conditions in all 12 pilot fields: total catalog
  density, M10, mean visibility periods, and mean matched transits span useful
  ranges, and all 12 safeguards pass (2026-07-19).
- [x] Freeze six candidate comparisons, grouped development evaluation, settings,
  scoring rules, and the simple-model preference before scale-up; all 13 safeguards
  pass and no model is fitted (2026-07-19).
- [x] Derive the three frozen G-magnitude summaries from verified raw checkpoints;
  all nine checks pass with no archive query (2026-07-19).
- [x] Validate the resumable all-development continuation with a zero-query dry run,
  one new live field, and a zero-query restart; 13 development fields are complete,
  all 14 run checks pass, and validation remains unopened (2026-07-19).
- [x] Add measured per-request and whole-field time ceilings, permanent failure
  receipts, attempt-based batch limits, and default deferral of failed fields after
  one archive stall; all 17 run checks pass (2026-07-19).
- [x] Extend retrieval and pre-selector measurements to all 398 development fields
  in explicitly bounded runs; 8,001,113 Gaia sources were measured, 403,920 pass
  the frozen selector, all 17 run checks pass, and validation remains unopened
  (2026-07-19).
- [x] Save adaptive planning progress after every measured count and verify it
  before reuse; the local stop-and-restart test passes all eight checks, and the
  dense final field resumes safely to completion (2026-07-19).
- [x] Fit and compare the six frozen model choices using only the 398 development
  fields; the sky-position-plus-Gaia-conditions regression is selected, all 22
  safeguards pass, and validation remains unopened (2026-07-19).
- [x] Preserve `sky_field_0317` as an explicit flagged applicability warning after
  its held-out density exceeds the selected prediction by a factor of 11.548; do
  not delete it or use the unflagged sensitivity fit as the primary model
  (2026-07-19).
- [x] Review the frozen model and demote it to a diagnostic interpolation after its
  extreme-field failure clarified that direct measurements should remain primary
  (2026-08-11).
- [x] Retrieve and evaluate the 102 held-back validation fields exactly once without
  retuning the direct procedure, refitting the diagnostic model, or changing the
  applicability warning (2026-08-11).
- [x] Freeze and compare the three approved direct random-field procedures using
  only the 398 development fields; preserve comparison identities, measured
  distributions, and the `|b| >= 20` applicability limit; the simple latitude-band
  procedure is selected and all 17 safeguards pass (2026-08-11).
- [x] Make the selected direct procedure primary for the large-sky reference and
  demote the fitted model to a diagnostic interpolation (2026-08-11).
- [x] Freeze the future host report to show the valid outer-annulus measurement,
  direct random-field distribution, their difference, and their ratio
  (2026-08-11).
- [x] Close the design branch with all 102 large-sky validation fields still
  unopened, merge it into `master`, and begin the one-time evaluation on a fresh
  branch (2026-08-11).
- [x] Freeze the 102 field identifiers, count-blind order, bounded retrieval, direct
  evaluation metrics, and secondary fitted-model diagnostic before the first query;
  all 11 contract checks pass (2026-08-11).
- [x] Run the zero-query validation start: no reserved result is opened, no archive
  query is made, and all 17 retrieval safeguards pass (2026-08-11).
- [x] Retrieve exactly one reserved field and run a zero-query restart; 11,680 Gaia
  sources yield 1,108 passing sources in four verified strips, all receipt hashes
  and 17 run safeguards pass, and 101 fields remain (2026-08-11).
- [x] Complete a ten-attempt validation batch without failure and verify another
  zero-query restart; cumulative coverage is 11 fields, 142,703 Gaia sources, 9,908
  passing sources, and 42 verified strips (2026-08-11).
- [x] Complete the next 25-attempt batch without failure; cumulative coverage is 36
  fields, 533,034 Gaia sources, 30,972 passing sources, and 163 verified strips,
  with all 17 restart safeguards passing (2026-08-11).
- [x] Complete a 35-attempt continuation without failure; cumulative coverage is 71
  fields, 974,992 Gaia sources, 59,951 passing sources, and 291 verified strips,
  with 31 fields remaining (2026-08-11).
- [x] Retrieve the 102 reserved fields in measured, explicitly bounded batches;
  1,534,299 Gaia sources yield 86,189 passing sources in 459 verified strips with
  no failed field (2026-08-11).
- [x] Apply the frozen direct reference and diagnostic model once, report differences
  from development performance, and do not retune either method; all 20 evaluation
  safeguards pass (2026-08-11).

Off-target split progress, 2026-07-18:

- [x] Keep east and west fields from each host system in one partition.
- [x] Assign NGC 4698 and NGC 1316 fields to development; hold ESO 006-G001 and M60
  fields for validation.
- [x] Preserve one isolated case, one grouped case, one positive latitude, and one
  negative latitude in each partition.
- [x] Verify no development and validation circles overlap; the minimum measured
  center separation is 11.949376 degrees for 0.1-degree-radius circles.
- [x] Confirm the split reads no Gaia source counts, densities, or selector outputs
  and promotes no field to an approved scientific background.

Development-selector progress, 2026-07-18:

- [x] Retrieve all 19 frozen-selector inputs for the four development fields only.
- [x] Apply `point_source_logistic_model_v1` locally to 413 Gaia sources; 44 pass
  the frozen threshold over 0.125664 square degree.
- [x] Save field-level query fingerprints, source-identifier fingerprints, exact
  spherical areas, selector probabilities, and decisions.
- [x] Verify all 18 safeguards, including complete row counts and absence of every
  held-back validation field from selector queries and outputs.
- [x] Freeze the bounded field, related-host-pair, and descriptive all-development
  summary procedure before opening validation; all 16 checks pass (2026-07-18).
- [x] Open the four held-back fields once under the unchanged selector and summary
  rules; 52 of 1,233 sources pass and all 24 safeguards pass (2026-07-19).

Frozen-summary progress, 2026-07-18:

- [x] Preserve all four development fields separately.
- [x] Combine east and west only within NGC 1316 and within NGC 4698.
- [x] Report exact 68% and 95% counting-only ranges for field, host-pair, and
  descriptive all-development rows.
- [x] Conserve 413 retrieved sources, 44 passing sources, and 0.125664 square degree
  at every summary level.
- [x] Keep the selector threshold fixed and all held-back validation identifiers
  absent.

Held-back validation progress, 2026-07-19:

- [x] Query exactly the four frozen validation fields and exclude all development
  identifiers from queries and outputs.
- [x] Apply the unchanged 19-column selector, threshold, Gaia area rule, host-pair
  grouping, and 68% and 95% counting-only ranges.
- [x] Preserve 1,233 retrieved sources, 52 passing sources, and 0.125664 square
  degree across four field rows, two host-pair rows, and one descriptive total.
- [x] Record the validation/development density ratio of 1.181818 and overlapping
  field and host-pair density ranges as descriptions, not scientific approval.

## III.4 Interface with the real host measurement

- [x] Confirm that the 0.1-degree field-condition circles are query benchmarks only
  and do not define the real host aperture (2026-07-18).
- [x] Require concentric circular annuli for the real radial profile and a separately
  calibrated central exclusion for galaxy substructure and H II contamination
  (2026-07-18).
- [ ] Define the exploratory physical-kpc annuli and host-size-normalized annuli
  under BT-021 before a real host search.
  Physical rings were frozen on 2026-08-11; the normalized view remains unavailable
  where verified half-light radii are missing. This checkbox covers both views.
- [ ] Calibrate the central exclusion and final radial signal region under BT-021.

Interview decisions, 2026-08-11:

- [x] Require both physical-kpc and `R50`-normalized profiles when a verified
  `R50` exists; missing `R50` makes only the normalized view unavailable.
- [x] Use 0--50 kpc as a deliberately conservative first-stage contamination
  region while preserving every inner component ring; do not treat it as final.
- [x] Retain the exploratory profile through 600 kpc and inspect the measured outer
  behavior before selecting the final outer signal boundary.
- [x] Freeze and validate a count-blind first-stage profile fixture before any real
  600 kpc Gaia query; five hosts retain 14 rings each, all 16 safeguards pass, and
  NGC 4698 is the geometry-only first benchmark (2026-08-11).
- [x] Measure the NGC 4698 600 kpc archive count before a full source retrieval:
  23,811 frozen-domain Gaia sources over 6.478776 square degrees in 2.004 seconds,
  with no source rows or selector output retrieved; all nine checks pass
  (2026-08-11).
- [x] Retrieve the frozen NGC 4698 circle in six measured non-overlapping strips,
  preserve all 23,811 continuous source radii outside the repository, apply the
  frozen point-source contamination selector locally, and report both profiles;
  2,548 sources remain and all fourteen checks pass (2026-08-11).
- [x] Plot all 2,548 passing-source locations and the nine frozen-selector feature
  inputs; preserve five transparent review examples without inventing a candidate
  rank, document the 95.02% missing five-parameter-astrometry fraction, and pass
  all seven initial checks (2026-08-12).
- [x] Add the literature-standard G-magnitude versus raw BP/RP flux-excess QA plane,
  preserve Liu et al.'s 1.7 value as a reference rather than a new cut, and record
  the project lead's visual classification of example E as a star; all eight
  updated checks pass (2026-08-12).
- [x] Review the first profile and select M60 as the next positive-control host
  because of its known UCDs, not its Gaia density (2026-08-12); see the
  [M60 design](../development/host_pilot_profiles.md#record-m60_positive_control). No final outer boundary was selected.

Progress, 2026-07-18:

- [x] Audit the count-blind angular geometry for all 2,155 hosts; all seven checks
  pass, and no `R50` field is currently available.
- [x] Define a recombinable exploratory physical-ring view while preserving
  continuous source radius; the displayed edges are not final boundaries.
- [x] Remove the inherited two-degree cap from the design requirement: a 600 kpc
  diagnostic radius exceeds two degrees for 1,018 hosts.
- [ ] Acquire provenance-bearing `R50` measurements under BT-020 before calibrating
  the normalized central exclusion.
- [x] Implement and validate strip-based retrieval and exact per-ring usable areas
  (NGC 4698 completed 2026-08-11; M60 completed 2026-08-12).

Query-partition progress, 2026-07-18:

- [x] Validate a complete circle against four non-overlapping horizontal sky strips;
  both retrieve exactly the same 500 Gaia source identifiers and all nine checks
  pass in 12.96 seconds.
- [x] Validate one-time assignment of shared strip boundaries and clipping at a
  celestial pole.
- [x] Add measured-row-count splitting, per-strip checkpoints, and resume behavior
  (2026-07-18).
- [x] Validate spherical requested, successfully queried, missing, masked, and
  usable areas for recombined radial rings; all 18 checks pass (2026-07-18).

Adaptive-retrieval progress, 2026-07-18:

- [x] Add measured row-count splitting and save the complete plan before retrieval.
- [x] Write and verify atomic per-strip source and metadata checkpoints.
- [x] Validate a controlled stop after two strips and a fresh restart that skips
  those files and downloads only four unfinished strips.
- [x] Detect and replace one deliberately corrupted strip while preserving five
  valid strips; all 15 checks pass in 21.68 seconds.
- [x] Benchmark and freeze a 5,000-row per-strip limit using all 19 frozen-selector
  input columns; retain actual file bytes per checkpoint (2026-07-18).
- [x] Integrate verified strip-completion states with spherical radial-ring usable
  areas in the bounded component (2026-07-18).

Radial-ring area progress, 2026-07-18:

- [x] Define requested, successfully queried, missing, masked, and usable area in
  plain language and enforce their accounting identities.
- [x] Reproduce complete retrieval-circle areas for NGC 4698, M60, and
  ESO 006-G001 using their measured final strip plans.
- [x] Preserve positive missing area in a controlled one-of-two-strip M60 state.
- [x] Subtract the union of two overlapping synthetic circular masks once to test
  the generic geometry code.
- [x] Freeze the Gaia-specific policy: apply no bright-star, dust, or ancillary-
  imaging masks; usable area equals successfully queried area and incomplete strips
  remain missing area. All 18 checks pass in 0.216274 seconds (2026-07-18).

Per-galaxy receipt progress, 2026-07-18:

- [x] Define a permanent JSON receipt containing galaxy identity, configuration
  fingerprint, retrieval status, completed strips, source checks, ring areas, and
  plain-language failures.
- [x] Write three completed performance-field receipts under one run identifier and
  one controlled partial M60 receipt under a separate identifier.
- [x] Reuse identical receipts and reject changed content instead of overwriting;
  all 18 checks pass in 0.014978 seconds.
- [ ] Apply the receipt format to real physical-ring requests after their geometry
  and central scientific exclusion are declared.

Full-column benchmark progress, 2026-07-18:

- [x] Benchmark all 19 frozen-selector input columns at 100, 500, 1,000, 2,500,
  5,000, and 10,000 returned rows; all ten checks pass in 17.719464 seconds.
- [x] Repeat 5,000 rows three times with identical source identifiers, measured
  query times of 1.948628--1.976649 seconds, and 1,027,468 serialized bytes.
- [x] Approve 5,000 rows as a provisional development checkpoint limit, half the
  largest successful test and explicitly not an archive maximum.
- [x] Validate the provisional limit in multiple fields with different source
  densities and in a full-column controlled restart (2026-07-18).

Multi-field full-column validation, 2026-07-18:

- [x] Preserve the failed first diversity test: 0.5-degree fields contained 2,991,
  3,098, and 13,010 rows, so only one field required splitting.
- [x] Expand only the M60 performance-test circle to 0.75 degree rather than weaken
  the two-split-field requirement.
- [x] Validate 2,991-row unsplit, 6,497-row two-strip, and 13,010-row four-strip
  cases; exact identifier references match and all 13 checks pass in 29.589341
  seconds.
- [x] Freeze 5,000 rows as the development and pilot per-strip limit for the current
  19-column contract.

## Review

- The inherited 0.8-degree fields use an obsolete selector and divide by 2.0 square
  degrees rather than the exact circular area.
- The inherited Phase IV annulus can be absent under the two-degree cap and does not
  exclude the host or environment halo.
- The current host catalog lacks the verified size, halo, and environment fields
  required to finalize exclusion radii.
- The query-free fixture evaluates 20 symmetric candidates: 11 accepted and 9
  rejected, with a maximum Galactic-latitude mismatch of `7.11e-14` degrees.
- `1.5 R2t`, `2 R2t`, and `3 R2t` enclose 91.73%, 97.73%, and 99.77% of accepted
  group members, while one association `R1t` encloses 86.41% of usable members;
  no universal safety factor is frozen.
- The first live-archive test found 121, 100, and 122 Gaia sources in three equal
  patches at exactly the same Galactic latitude. Gaia coverage and total source
  density must therefore be measured, but three patches cannot set a tolerance.
- The five-host review shows larger field-condition variation for the two group
  cases. Total Gaia density is partly signal-sensitive near a target and cannot be
  used as a rigid matching requirement.
