# Literature Reference Audit

**Date:** 2026-07-14
**Script:** `scripts/phase1_literature/audit_reference_data.py`
**Command:** `PYTHONPATH=. uv run python scripts/phase1_literature/audit_reference_data.py`
**Database:** `data/literature/database/ucd_collection.db`
**Database SHA-256:** `d5a2890a10244d78c9be0b54852e8a6667c6ae766053698c450413a9f3ef1806`

## Scope and Safety

This is a read-only audit of the current literature rows. Exact stored coordinate
equality is treated only as provisional identity evidence. No row was deleted,
merged, relabeled, or selected as the preferred astrophysical record. Near-coordinate
matching and selector behavior are outside this audit.

## Measured State

| Measure | Count |
|---|---:|
| Database source records | 9 |
| Per-source CSV catalogs | 10 |
| Database literature rows | 2108 |
| Unique current `object_id` values | 2108 |
| Rows flagged `is_ucd = 1` | 2064 |
| Gaia-matched rows | 1097 |
| Legacy Survey-matched rows | 0 |
| Exact stored coordinate pairs | 1928 |
| Exact duplicate-coordinate groups | 180 |
| Rows in exact duplicate groups | 360 |

## Current Confirmation Labels

| Stored label | Rows |
|---|---:|
| `candidate` | 1731 |
| `confirmed` | 377 |

Confirmation status is attached to each literature row and was assigned uniformly
by source ingestion logic. It is not currently an object-level evidence tier. In
particular, 148 exact-coordinate groups contain conflicting stored labels.

## Exact Duplicate-Coordinate Groups

- Every group contains between 2 and 2 rows.
- 148 groups connect different source papers and therefore
  require many-to-many canonical object/source associations.
- 32 groups repeat coordinates within one source;
  0 of those groups differ in stored payload fields after excluding row IDs and timestamps.
- 0 groups disagree on `is_ucd`.
- 0 groups disagree on stored Gaia ID,
  including null versus non-null values.

| Source 1 | Source 2 | Exact-coordinate groups |
|---|---|---:|
| `2011A&A...531A...4M` | `2019A&A...625A..50V` | 118 |
| `2021MNRAS.504.3580S` | `2021MNRAS.504.3580S` | 30 |
| `2007A&A...472..111M` | `2019A&A...625A..50V` | 27 |
| `2009AJ....137..498G` | `2019A&A...625A..50V` | 3 |
| `2011ApJ...737...86C` | `2011ApJ...737...86C` | 2 |

The companion `exact_duplicate_coordinate_memberships.csv` preserves every member
row and its source, label, Gaia ID, host, and size fields. Its group identifier is
source-neutral and derived from the exact binary representation of the stored
coordinates; it is an audit identifier, not an approved canonical object ID.

## Source Reconciliation Findings

- Catalog sources absent from the database source/object model:
  `2015ApJ...802...30Z`.
- Database sources without a per-source CSV catalog:
  `none`.
- The source table has no populated DOI or declared object-count fields. Detailed
  row counts and catalog/database differences are in `literature_source_audit.csv`.

## Canonicalization Gate

The current `ucd_objects` table is a literature-row table despite its name. A safe
canonical model must keep those rows immutable and add separate canonical objects,
many-to-many source associations, provenance-bearing evidence records, and explicit
confirmation tiers. The 1,928 exact coordinate pairs are an upper-confidence audit
partition, not a complete canonical catalog: exact equality can miss the same object
reported at slightly different coordinates, while equal coordinates within a paper
still require verification.

No selector should use deduplicated or confirmed-object denominators until that
model and its review rules are implemented and validated.
