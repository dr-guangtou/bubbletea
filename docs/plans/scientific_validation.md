# Initial Scientific Validation Plan

**Created:** 2026-07-14
**Status:** Ready for execution after initial scientific-definition interview
**Specification:** `docs/SPEC.md`
**Issue register:** `docs/todo.md`

## Goal

Establish a reproducible Gaia-only selection and statistical validation framework
before expanding the UCD search to a final galaxy sample. Preserve null and
negative results, quantify sensitivity, and separate population inference from
value-added candidate characterization.

## Stage 1: Stabilize Reference Data

- [x] Reconcile literature rows, unique objects, source associations, confirmation
  tiers, and the 180 exact duplicate-coordinate groups (`BT-003`, `BT-028`).
  - [x] Audit the current database and per-source catalogs read-only; preserve all
    duplicate memberships and record exact-coordinate label conflicts (2026-07-14).
  - [x] Define the canonical object, source-association, evidence, and
    confirmation-tier model in `docs/SPEC.md` (2026-07-14).
  - [x] Retrieve 34 raw VizieR files for 11 source packages and build a separate
    v2 database without modifying the legacy database (2026-07-14).
  - [x] Export all 140 non-exact Gaia links and every confirmation promotion for
    review instead of accepting them automatically (2026-07-14).
  - [x] Reconcile Saifollahi tables A1, A5, and A6 into 61 operational reference
    UCDs pending evidence review, 587 comparison records, a separate 1,155-row
    selection pool, and 44 linked final candidates (2026-07-14).
  - [x] Produce a read-only row-level role and overlap review for the 79 Liu, 57
    Voggel, and four coordinate-null Fahrion rows without changing v2 membership
    (2026-07-14).
  - [x] Implement the approved Liu, Voggel, and coordinate-null Fahrion membership
    treatment with 86 accepted source associations, no open source-table identity
    proposals, and four reviewed unassociated provenance records (2026-07-14).
  - [x] Resolve T17-1596 as Fahrion HHH86-C15 using the published Taylor GC0218
    and Woodley HHH86-C15 alias chain while retaining the 1.37-arcsecond catalog
    offset as association provenance (2026-07-14).
  - [x] Retrieve authoritative Gaia DR3 positions for all 117 shared-source groups
    and recompute spherical geometry for all 140 proposals without changing
    canonical membership (2026-07-14).
  - [x] Review the Gaia identity routing artifact: 72 recommended shared
    identities, 23 Gaia image-ambiguity groups, 8 multi-position groups, and 14
    identity-plus-classification groups (2026-07-14).
  - [x] Implement the 72 approved clean shared-Gaia identities, retain all 72
    retired canonical identifiers as aliases, and leave 65 pair proposals across
    45 review groups (2026-07-14).
  - [x] Merge the 14 separately approved shared identities with reported UCD/GC
    role conflicts and label them
    `uncertain / reported_ucd_role_conflict`, leaving 49 pair proposals across 31
    image or multi-position review groups (2026-07-14).
  - [x] Retrieve Gaia DR3 neighborhoods and Legacy Survey DR10 data, model, and
    residual cutouts for the 23 two-position image-ambiguity groups; recommend 22
    shared identities while retaining S547/VUCD3 as a distinct close pair pending
    project-lead approval (2026-07-14).
  - [x] Implement the approved 22 image-reviewed identities, consolidate the
    Zhang/Fahrion S547 records, retain VUCD3 separately, and store two explicit
    ambiguous shared-Gaia evidence rows; leave 26 proposals across eight
    multi-position groups (2026-07-14).
  - [x] Trace the eight remaining multi-position groups through Gregg velocities
    and aliases, Fahrion/Mieske measurements, Saifollahi photometry and sizes,
    Brüns cross-identifications, and ADS metadata; recommend eight shared
    identities pending project-lead approval (2026-07-14).
  - [x] Implement the eight approved three-position shared-Gaia identities while
    preserving all 16 retired canonical identifiers, the F-6/Gregg 27 velocity
    tension, and both identical Saifollahi F-1/UCD2 source rows; close the
    spherical-identity gate with zero remaining proposals (2026-07-15).
  - [x] Expand the ADS discovery search with a targeted 2015-2026 UCD-title query
    and screen the exact 345-paper metadata corpus; identify 27 proposed retrieval
    sources with zero pending screening rows, pending project-lead cohort review
    (2026-07-15).
  - [x] Retrieve the approved 19-source high-priority cohort, including five
    authoritative VizieR packages and four publisher source-data workbooks;
    validate 365 PDF pages and preserve 4,535 machine-readable source rows without
    changing canonical membership, identity, or confirmation (2026-07-15).
  - [x] Implement the approved Wave 1 treatment: 855 unconfirmed positive records,
    1,484 negative comparison records, a separate 904-row Wittmann mixed pool,
    109 Ahn bins attached as one M59-UCD3 measurement dataset, four exact Ko role
    conflicts retained as uncertain, and one provenance-preserving S999 identity
    consolidation (2026-07-15).
  - [x] Audit remaining Wave 1 records against pre-Wave identities using only
    direct names or published aliases plus spherical and velocity context; propose
    seven unique high-confidence associations, route 153 rows with multiple nearby
    baseline canonicals to manual group review, and reject four distant identifier
    collisions without changing membership (2026-07-15).
  - [x] Implement the seven approved Wave 1 name-or-alias associations across six
    pre-Wave candidate identities, retain seven superseded canonical identifiers
    as aliases, and leave all 153 multi-canonical cases untouched pending a
    separate group-level audit (2026-07-15).
  - [x] Audit all 153 multi-canonical Wave 1 rows as 91 connected groups, preserve
    every nearby baseline contender, propose 12 complete shared-identifier groups
    for project-lead review, and leave 79 conservative manual groups unchanged
    (2026-07-15).
  - [x] Implement the 12 approved Wave 1 group identities, consolidate 40 prior
    canonicals into 12 objects, retain all 28 superseded canonical identifiers as
    aliases, and preserve 79 unresolved groups without new proposals (2026-07-15).
  - [x] Complete the delegated source audit for the remaining 79 groups, resolve
    them as 80 source-supported identities while keeping S547 and VUCD3 distinct,
    retain 229 superseded canonical identifiers as aliases, and close the post-
    build multi-canonical audit with zero remaining groups (2026-07-15).
  - [x] Close the raw-row gate by attaching all 168 intentionally supporting rows
    as measurement evidence without changing identity or membership (2026-07-15).
  - [x] Close the host-distance gate: correct the 27 Mieske Centaurus-cluster rows
    to the source-stated 43 Mpc, keep Fahrion's heterogeneous compilation distance
    null, and preserve every legacy value in immutable payloads (2026-07-15).
  - [x] Close the confirmation gate under `confirmation_rules_v1`: approve 1,316
    spectroscopic evidence rows, derive 740 confirmed canonicals, retain 22
    reviewed role conflicts as uncertain, and record 57 Voggel non-promotions
    where qualifying local evidence is absent (2026-07-15).
  - [x] Close the new-literature gate against the hashed 345-paper ADS corpus with
    zero pending screens, 19 approved retrievals, and explicit scoped dispositions
    for the eight deferred retrieval candidates (2026-07-15).
- [x] Repair spherical cross-match geometry and ambiguity handling (`BT-007`;
  2026-07-15).
- [x] Synchronize the Gaia and Legacy Survey exports with the canonical database
  (`BT-004`; 2026-07-15).
- [x] Complete per-paper provenance packages and reconcile documentation counts
  (`BT-014`, `BT-015`; 2026-07-16).
- [x] Build the 3,857-source labeled UCD and contaminant benchmark with fixed
  spatial validation partitions and 32 passing release checks (`BT-019`;
  2026-07-16).

**Gate:** A non-destructive validation report reproduces all canonical counts and
every benchmark label retains provenance and uncertainty.

**Gate status, 2026-07-16:** Passed. The benchmark manifest hashes every local
input, the validation report reproduces all label and partition counts, and the
legacy and v2 literature databases remain unchanged.

## Stage 2: Define the Galaxy Samples

- [ ] Review published nearby-galaxy censuses with public completeness analyses,
  including multi-messenger and dark-siren catalogs (`BT-027`).
- [ ] Select and verify a parent selection function without changing its denominator
  during catalog enrichment (`BT-027`).
- [ ] Retrieve consistent `R50` and morphology values with provenance and quality
  indicators (`BT-020`).
- [ ] Calibrate the conservative Galactic-latitude eligibility limit (`BT-022`).
- [ ] Freeze the near-complete primary sample and the broader valid diversity sample
  (`BT-026`).

**Gate:** The primary and diversity samples can be regenerated from documented
inputs, and every exclusion has a recorded reason.

## Stage 3: Calibrate One Gaia-Only Selector

- [ ] Compare Gaia extendedness features and color combinations on the fixed
  benchmark without treating uncertain UCD candidates as certain labels
  (`BT-002`, `BT-019`).
  - [x] Enrich and analyze all 3,136 development sources without querying any of
    the 721 validation identifiers; measure 190 primary and sensitivity metrics
    with 19 passing artifact checks (2026-07-16).
  - [x] Review the development findings and approve a tiered selector direction
    prioritizing equal-weight rejection of ordinary stars, NSS/binaries, and QSOs;
    keep galaxies secondary and H II/young clusters as separate color/morphology
    safeguards (2026-07-17).
  - [x] Audit expanded extragalactic references and stage spectroscopic SDSS,
    Gaia morphology-galaxy, and Quaia spatial-null layers outside the repository
    without changing `benchmark_v1` (2026-07-17).
  - [x] Run and validate the predefined three-galaxy Gaia morphology stress test;
    measure 814 host-source associations, 87.7% false selection by both legacy rules,
    and no inner-density enhancement claim (2026-07-17).
  - [x] Freeze and validate 12 luminosity/latitude-stratified hosts with 12 paired
    geometric controls; measure 9,144 morphology galaxies, strong spatial variation,
    and 85--88% false selection without an environment or clustering claim
    (2026-07-17).
  - [x] Reclassify the Sersic-fit layer as a Gaia galaxy-candidate stress catalog,
    prohibit its use as the UCD parent sample, and exact-match only the development
    partition: 0/175 confirmed UCDs, 1/569 uncertain UCD candidates, and 0/127 H II
    regions have catalog membership (2026-07-17).
  - [ ] After selector and morphology-use freezing, run the predeclared exact match
    on the withheld validation partition and evaluate Sersic evidence without
    changing the frozen selection rule.
  - [x] Build a benchmark-disjoint SDSS spectroscopic stellar reference matched 3:1
    to 175 confirmed development UCDs using G and sky latitudes only; retain 525
    unique controls, measure 19 Gaia features, and pass 19 validation checks without
    claiming physical singleness or inspecting validation identifiers (2026-07-17).
  - [x] Measure 48 point-source-priority score operating points with equal cohort
    weight for stars, NSS/binaries, and QSOs; validate the rank-score/null-policy
    grid without freezing a threshold (2026-07-17).
  - [x] Run a leakage-controlled classical-ML comparison with measured BP-RP as a
    soft feature and equal priority-cohort weights (2026-07-17). Nested grouped CV
    favors logistic regression provisionally, but its 81.8--100% fold recall range
    prevents model or threshold freezing.
  - [x] Measure repeated grouped-CV stability and magnitude/sky-position behavior
    (2026-07-17). Ten repeats give 93.14--95.43% UCD recall and 3.75--4.42%
    equal-cohort retention; all 50 fits select `C = 3.0` with invariant measurement-
    feature signs. The formal stability gate passes, but 11 persistent UCD failures
    require provenance and association review.
  - [ ] Audit persistent UCD and contaminant failures and approve the final grouped-
    OOF threshold-calibration rule and applicability domain.
    Source-audit blocker: 68 Fahrion compilation rows use `RV = 0.0`, including 30
    current confirmed development objects; the prior evidence review incorrectly
    treated every coordinate-bearing row as positive velocity evidence.
  - [x] Re-audit the 68 Fahrion zero-RV rows and their independent evidence, preserve
    all source records, reject only B409 as an incorrectly classified UCD, and derive
    immutable benchmark/development-feature v2 artifacts (2026-07-17). Eight remain
    confirmed through independent evidence, 59 become candidates, and 26 Gaia-linked
    benchmark labels change in total.
  - [x] Recompute the matched stellar reference and every development-only selector
    artifact from benchmark v2 (2026-07-18). Ten repeats yield 94.67--96.00% UCD
    recall and 3.77--4.39% macro priority retention; seven UCDs remain persistent
    failures and all 50 fits still select boundary `C = 3.0`. Benchmark-v1 results
    remain immutable and superseded; validation remains sealed.
  - [x] Test weaker logistic regularization beyond the original `C = 3.0` grid
    boundary before freezing the model hyperparameters.
    Failure audit, 2026-07-18: four of seven persistent v2 UCD misses have Gaia
    proper-motion significance of 9.91--44.87 and should have their Gaia associations
    quarantined without changing the spectroscopic UCD classifications. The project
    lead approved this treatment; benchmark v3 uses 146 reliable UCDs, passes all
    repeated stability gates, and leaves validation sealed.
    Sensitivity result, 2026-07-18: four of five folds still select the boundary
    when the grid ends at 100 and again at 3000. Compare weakly regularized and
    unregularized fits directly; do not freeze 3000 or keep expanding arbitrarily.
    Direct comparison result: `C = 1000` has the lowest fixed-split macro retention
    at the same 90.41% recall; `C = 3000` and unregularized have identical aggregate
    decisions. Repeat these three configurations before freezing a policy.
    Ten-repeat result: all configurations retain exactly 90.41%; `C = 1000` has
    lower median macro retention, wins 7/10 paired repeats, and has smaller
    coefficient norms. The project lead approved and froze `C = 1000` on 2026-07-18;
    threshold calibration remains pending and validation remains sealed.
  - [x] Audit frozen-`C = 1000` persistent failures (2026-07-18). Ten reliable UCDs
    are persistent misses, but all retain strong literature evidence or extended-
    source Gaia diagnostics. Keep all ten in completeness accounting; no new
    reliability quarantine is approved or recommended.
  - [x] Freeze the operating threshold at `0.8277833629` (2026-07-18), using the
    project-lead-approved median of ten grouped-OOF thresholds that individually
    target at least 90% reliable-UCD recall. Validation remains sealed.
  - [x] Fit the complete development model and pass serialization, parameter-export,
    prediction-parity, provenance, and validation-ID-exclusion checks (2026-07-18).
    The final artifact is ready for a separately authorized one-time validation run.
  - [x] Complete the one-time frozen validation run (2026-07-18): 91.30% reliable-
    UCD recall and 0.57% macro retention across Gaia NSS and QSO. Retuning is closed;
    any future model generation requires a new independent validation cohort.
  - [ ] Review and approve one measured operating point before implementing and
    freezing the shared selector.
- [ ] Measure selection behavior across magnitude, distance, inferred luminosity,
  inferred size, Galactic latitude, and Gaia uncertainty properties (`BT-002`).
- [ ] Freeze one versioned selector used identically for literature, control fields,
  and host searches (`BT-002`, `BT-017`).
- [ ] Add fast deterministic validation scripts for selector parity and null handling
  (`BT-018`).

**Gate:** The selector has measured completeness and contamination behavior over a
declared applicability domain and one implementation produces all selections.

## Stage 4: Validate Background and Radial Statistics

- [ ] Recompute background behavior with the canonical selector and exact usable
  areas (`BT-009`).
- [ ] Compare large-field, off-target circular, and off-target annular backgrounds
  matched in Galactic latitude and screened for nearby halos (`BT-005`).
- [ ] Calibrate exploratory physical and `R50`-normalized annuli, including the
  central exclusion and trial factors (`BT-021`).
- [ ] Define and calibrate the full overdensity uncertainty and provisional 3-sigma
  evidence standard (`BT-006`).
- [ ] Compare per-galaxy excess metrics without selecting the strongest correlation
  (`BT-025`).

**Gate:** Known hosts, low-mass controls, nearby angular-cap cases, and blank fields
produce calibrated positive, zero, and negative measurements without special-case
code paths.

## Stage 5: Run an Auditable Pilot

- [ ] Implement immutable run metadata, target status, failure recording, and safe
  resume behavior (`BT-010`).
- [ ] Run a deliberately small validation set before any larger remote query.
- [ ] Build a source-level catalog with one-to-many host associations (`BT-011`).
- [ ] Validate literature recovery and candidate indexing (`BT-008`).
- [ ] Preserve Gaia-only candidate evidence separately from host context (`BT-024`).
- [ ] Record external imaging and spectroscopy only as value-added evidence
  (`BT-013`, `BT-028`).

**Gate:** A repeated pilot run produces the same versioned products, complete
failure accounting, and no stale files from another run.

## Stage 6: Population Analysis and Final Systematics

- [ ] Include every eligible host measurement, including zero and negative excess,
  in the appropriate population products.
- [ ] Quantify correlations in the primary near-complete sample and depict diversity
  in the broader valid sample.
- [ ] Flag known groups and clusters, compare local and global backgrounds, and
  perform dedicated secondary analysis (`BT-012`).
- [ ] Develop probabilistic host association only after independent first-stage
  measurements are stable (`BT-023`).
- [ ] Test Gaia scanning-pattern systematics and apply a model, uncertainty term, or
  quality mask only if measurements require it (`BT-029`).
- [ ] Pass Ruff and pre-commit without changing scientific behavior (`BT-016`).

**Gate:** Final claims state the selection domain, sample selection function,
background method sensitivity, trial handling, and remaining systematic limits.

## Small-Scale Validation Rule

Before each full execution, run the smallest representative local fixture or query
that exercises the same code path. Measure its runtime and output rather than
estimating either. Local deterministic checks should complete within the project
mandate's sub-minute validation window; remote archive latency must be measured and
recorded separately before scaling.

## Review

- [x] The plan follows the approved scientific priority order.
- [x] Population inference remains Gaia-only.
- [x] Candidate confirmation is optional and value-added.
- [x] Null and negative results remain valid outputs.
- [x] Full execution is blocked by explicit validation gates rather than an
  estimated schedule.
