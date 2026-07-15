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
- [ ] Complete per-paper provenance packages and reconcile documentation counts
  (`BT-014`, `BT-015`).
- [ ] Build the labeled UCD and contaminant benchmark with fixed validation
  partitions (`BT-019`).

**Gate:** A non-destructive validation report reproduces all canonical counts and
every benchmark label retains provenance and uncertainty.

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
