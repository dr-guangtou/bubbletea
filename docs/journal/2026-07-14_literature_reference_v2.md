# Literature Reference v2 Build and Discovery

**Date:** 2026-07-14
**Stage:** Stage 1 - Stabilize Reference Data
**Issues:** `BT-003`, `BT-014`, `BT-028`

## What Was Done

- Defined publications, datasets, immutable literature records, canonical objects,
  associations, proposals, evidence, derived classifications, and review queues in
  `scripts/phase1_literature/reference_schema.sql` and `docs/SPEC.md`.
- Added a non-destructive builder and validator. The builder opens
  `data/literature/database/ucd_collection.db` read-only and writes the gitignored
  `ucd_reference_v2.db` alongside it.
- Retrieved 34 authoritative VizieR files for 11 source packages and recorded
  paths, table identifiers, SHA-256 hashes, and row counts.
- Corrected the Voggel 2020 and Fahrion 2019 ADS bibcodes while retaining their
  legacy identifiers as explicit aliases.
- Added `confirmation_rules_v1` and a deterministic fixture covering confirmed,
  candidate, rejected, uncertain, pending-review, and identity-conflict behavior.
- Ran eight paginated NASA ADS queries covering priority papers, recent object
  data, spectroscopy/catalog searches, and citation networks. The result contains
  300 unique papers and a tracked manual-screening worksheet. arXiv fallback is
  implemented but was not requested because ADS completed successfully.

## Measured Results

- The v2 draft preserves 2,710 literature records and associates 2,706 of them
  with 2,331 canonical objects. Four coordinate-null provenance records remain
  intentionally unassociated.
- The 1,155-row Saifollahi table A5 broad selection pool is retained separately;
  its 44 table A6 final candidates are linked to the pool and included as
  unconfirmed literature records.
- Saifollahi table A1 is reproducibly divided into 61 operational spectroscopic
  reference UCDs and 587 comparison records using the paper's magnitude and size
  criteria. The 61 positive records remain pending evidence review.
- All 180 legacy exact duplicate-coordinate groups remain represented.
- The approved Gaia cohorts merge 72 clean, 14 reported-role-conflict, and 22
  image-reviewed groups. Together with the consolidated Zhang/Fahrion S547
  identity, they retain 109 superseded canonical identifiers as aliases and leave
  26 pair proposals across eight multi-position groups.
- The review queue contains 618 items. The conservative draft contains 1,742
  candidates, 575 rejected objects, and 14 objects labeled
  `uncertain / reported_ucd_role_conflict`, with zero automatic confirmations.
- Two consecutive final build-and-validation passes completed in 0.93/0.25 and
  0.94/0.24 seconds. Both produced database SHA-256
  `4699bde98f1fdb1099a221711d1d9409d3bc85872ff84469513e07afc314e4bc`
  and canonical export SHA-256
  `94ee2f6f082251923bfcddaa11df6ec1c655dab01c29f8713a72fdd92ff1ab97`.
  The approved shared-Gaia export SHA-256 is
  `9097583bc1e0a047aebdfab24eef98a19448859faf36cdde1c883d0f609834b8`,
  and the special S547/VUCD3 evidence export SHA-256 is
  `fdb38156280625c34b0f98e6fb20d4f9d04c728f1bf1d25a4a39357bb6f52383`.
- The legacy database SHA-256 remained
  `d5a2890a10244d78c9be0b54852e8a6667c6ae766053698c450413a9f3ef1806`.
- The Gaia identity audit resolved all 117 repeated source IDs against
  authoritative DR3 positions and recomputed all 140 pair separations on the
  sphere. The 117 groups contain 109 two-position and 8 three-position cases;
  14 have reported UCD-role conflicts, 10 Gaia rows have `duplicated_source`, and
  17 have nonzero `ipd_frac_multi_peak`. The review routing identified 72 clean
  shared identities, 14 role-conflict identities, and 31 image or multi-position
  groups requiring further review.
- The largest literature-to-Gaia separation is 0.861040672349 arcseconds. The
  largest difference between a stored legacy planar distance and the recomputed
  spherical distance is 0.176110481759 arcseconds.
- The 23 held two-position image-ambiguity groups were checked with exact
  five-arcsecond Gaia DR3 neighborhoods and 69 provenance-tracked Legacy Survey
  DR10 data/model/residual cutouts. No group has a competing Gaia source within
  two arcseconds; 22 have none within five arcseconds, and one has a separate
  neighbor at 4.710023680999 arcseconds. The full cached rerun completed in 1.67
  seconds after the 149.21-second remote retrieval.

## Decisions

- Raw source files and immutable source-row payloads are authoritative. Processed
  catalogs and normalized fields are derived.
- Exact stored coordinates are the only automatic identity relation in this draft.
  Non-exact Gaia and positional relations require spherical revalidation.
- Reported confirmation remains candidate-level until its object-level evidence is
  reviewed. Distant samples remain declared sensitivity data.
- Suspect Centaurus-cluster and heterogeneous compilation distances are preserved
  in raw payloads but cleared from normalized v2 fields pending reconciliation.
- Selectors remain unchanged, and the destructive redundancy script remains unused.

## Open Gates

1. Reconcile every normalized row with its authoritative raw table.
2. Reconcile host identities and distances.
3. Revalidate non-exact Gaia associations with spherical geometry and ambiguity
   handling. The clean and role-conflict cohorts are implemented. The image audit
   recommends 22 further shared identities and retaining S547/VUCD3 as a distinct
   close pair; eight multi-position groups remain for later review.
4. Review object-level confirmation evidence and conflicts.
5. Screen the 300-paper ADS result for additional nearby object-level literature
   and retrieve approved sources.

## Raw Table Role Checkpoint

After completing the Coma and Virgo source packages, the measured table-role audit
identified 23 scientific tables. The initial audit found four primary/reference
tables absent from direct source membership: 50 M49 Liu rows, 29 M60 Liu rows, and
57 previously confirmed Voggel comparison objects. It also found four
coordinate-null Fahrion rows.

The project lead approved separate treatment of Saifollahi tables A1, A5, and A6.
The downloaded paper, source tables, and full provenance are recorded under
`reference/saifollahi2021/`.

The subsequent project-lead-approved Liu, Voggel, and Fahrion treatment closes the
direct primary/reference table-membership gap. Three supporting/evidence tables
remain intentionally not row-linked and are covered by the broader raw-row gate.

## Pending Source-Row Review

A read-only audit of 140 rows absent from direct v2 membership is recorded in
`data/literature/validation/pending_source_row_review.csv` and its companion
Markdown report. The audit combines Liu photometry with its paired classification,
structure, and redshift tables and measures exact, one-arcsecond, and five-arcsecond
overlap diagnostics without assigning identity.

- The 79 Liu rows split into 51 `UCD=1` unconfirmed candidates and 28 explicit
  `UCD=0` comparison records. All 51 positive rows have sub-arcsecond v2
  counterparts; none of the 28 non-positive rows has a counterpart within five
  arcseconds.
- Of 57 previously confirmed Voggel comparison objects, 10 exactly match existing
  canonical coordinates, 24 have a counterpart within one arcsecond, one has a
  counterpart at 1.37 arcseconds, and 22 have none within five arcseconds.
- The four Fahrion rows without published coordinates have no exact normalized
  name match in v2 and remain unresolved provenance records.

The project lead approved the treatments, which are now implemented by the v2
builder. All 140 source rows are immutable literature records. The build accepts
51 Liu name-and-position associations, 34 sub-arcsecond Voggel spherical
associations, and the T17-1596 alias-chain association to Fahrion HHH86-C15 at
1.37 arcseconds. It creates canonical objects for the 28 Liu non-UCD comparisons
and 22 new Voggel reference positions and preserves four coordinate-null Fahrion
rows without canonical objects. The direct implementation export is
`data/literature/validation/approved_source_memberships.csv`.

## Gaia Image-Ambiguity Review

The non-destructive audit in
`scripts/phase1_literature/audit_gaia_image_ambiguity.py` preserves the frozen
23-group cohort and records the exact Gaia query, spherical five-arcsecond
neighborhoods, all 69 cutout URLs and SHA-256 hashes, and aligned review montages.
The five-arcsecond aperture is a diagnostic neighborhood rather than a match
radius. Legacy Survey JPEGs are visual diagnostics and do not establish DR10
maskbit or catalog-quality status.

For 22 groups, both literature positions overlay one centered modeled source and
no competing Gaia source lies within two arcseconds. These are recommended shared
identities and were approved by the project lead. The remaining group is not an identity
duplicate: Fahrion table B1 preserves S547 and VUCD3 as separate M87 objects with
different references, magnitudes, and effective sizes at a separation of
0.412226650676 arcseconds. They are recommended to remain separate canonical
objects sharing ambiguous unresolved Gaia evidence. The approved implementation
also consolidates the Zhang and Fahrion S547 records at a measured
0.058627924650-arcsecond separation while retaining VUCD3 separately. Two
object-level ambiguity evidence rows and one supplemental S547 identity-evidence
row record the treatment without changing either object's classification.

## Gaia Multi-Position Review

The final eight shared-Gaia groups were traced through Gregg table 2 velocities
and historical aliases, Fahrion table B1 velocities and structural measurements,
Saifollahi table A1 photometry and sizes, the Brüns extended-object alias catalog,
and a deterministic five-paper ADS metadata query. Each group contains three
sub-arcsecond literature positions at one Gaia DR3 source with no duplicated-source
or IPD image flags and no reported UCD-role conflict.

Brüns explicitly supports several cross-identifications, including F-24/UCD4,
F-1/UCD2, F-12, F-7, and F-22. Seven Gregg/Fahrion velocity comparisons agree
within 1.7 Gregg uncertainties. F-6/Gregg 27 differs by 268 km/s, or 2.65 Gregg
uncertainties; both measurements are preserved as a moderate tension because the
three positions remain within 0.611389846023 arcseconds of the same clean Gaia
source and both velocities indicate Fornax membership. Saifollahi table A1 also
contains two identical source rows at the F-1/UCD2 position; both provenance rows
remain preserved at one canonical position. The audit recommends accepting all
eight identities but makes no database change before project-lead approval.
