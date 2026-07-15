# Literature Reference Audit

**Date:** 2026-07-14
**Stage:** Stage 1 - Stabilize Reference Data
**Issues:** `BT-003`, `BT-028`

## What Was Done

- Verified that clean local `master` and `origin/master` both pointed to `c05b6bc`,
  then created `phase1_stabilize_literature_20260714` before editing.
- Reviewed the handover, scientific specification, issue register, validation plan,
  lessons, literature database utilities, ingestion, cross-match, and destructive
  redundancy script.
- Added `scripts/phase1_literature/audit_reference_data.py`, which opens the SQLite
  database read-only and produces deterministic source, label, and exact-coordinate
  audit artifacts in `data/literature/validation/`.
- Ran the smallest local audit before writing the canonical outputs. The corrected
  dry run completed in 2.96 seconds; the canonical run completed in 0.24 seconds.

## Decisions

- Exact coordinate equality is provisional identity evidence, not an approved
  canonical-object definition.
- Existing `ucd_objects` rows are provenance-bearing literature rows. They must
  remain immutable when separate canonical objects and many-to-many source
  associations are introduced.
- Current `candidate` and `confirmed` values are source-ingestion labels, not
  evidence-based object confirmation tiers.
- The destructive `redundancy_check.py` script was not run.

## Results

- The database SHA-256 remained
  `d5a2890a10244d78c9be0b54852e8a6667c6ae766053698c450413a9f3ef1806` before and
  after the audit.
- Measured 2,108 literature rows, 1,928 exact coordinate pairs, and 180 duplicate
  groups containing 360 rows. Every duplicate group has exactly two rows.
- Of the 180 groups, 148 connect different papers and all 148 conflict on stored
  `candidate` versus `confirmed` labels. The other 32 are within-source duplicate
  pairs; their payloads are identical after excluding row IDs and timestamps.
- No exact-coordinate group conflicts on `is_ucd` or stored Gaia source ID.
- The 95-row confirmed catalog `2015ApJ...802...30Z.csv` has no corresponding source
  or object rows in the database.
- All nine database source rows lack DOI and declared object-count values. The
  database contains zero Legacy Survey IDs, consistent with the prior handover.

## Next Steps

1. Define and review separate canonical-object, literature-row association,
   evidence, and confirmation-tier tables without migrating or deleting rows.
2. Review the 32 identical within-source pairs against original catalog structure
   and retain their original row/table provenance even if they map to one object.
3. Resolve the missing `2015ApJ...802...30Z` database association and source-level
   provenance gaps before using a confirmed-object denominator.
4. Audit near-coordinate identity only after the spherical matching and ambiguity
   policy for `BT-007` is specified.
