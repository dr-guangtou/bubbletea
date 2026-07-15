# Pending Literature Source-Row Review

**Date:** 2026-07-14
**Review status:** `approved_and_implemented_2026-07-14`
**Membership changes:** Implemented by the reproducible v2 builder

This read-only audit preserves the pre-implementation comparison for source rows
that lacked direct v2 membership. The baseline queries deliberately exclude the
newly approved source records so reruns continue to measure the reviewed decision.
Exact coordinate matches are measured literally. The 1- and 5-arcsecond counts
are diagnostic review aids only; they do not establish object identity.

## Source Rows

| Source table | Rows |
|---|---:|
| `2015ApJ...812...34L / table4.dat` | 50 |
| `2015ApJ...812...34L / table6.dat` | 29 |
| `2019A&A...625A..50F / tableb1.dat` | 4 |
| `2020ApJ...899..140V / table4.dat` | 57 |

## Approved Treatments

| Proposed treatment | Rows |
|---|---:|
| `coordinate_null_record_pending_identity_resolution` | 4 |
| `explicit_non_ucd_comparison_record` | 28 |
| `reference_record_pending_evidence_review` | 57 |
| `unconfirmed_candidate_record` | 51 |

The Liu tables contain explicit object-level UCD flags. Rows with `UCD=1` are
stored as unconfirmed candidates; rows with `UCD=0` remain explicit non-positive
comparison records. The paired structural/redshift tables must be retained as
supporting measurements. Voggel table 4 remains a previously confirmed comparison
sample pending object-level evidence review. Coordinate-null Fahrion rows remain
unresolved provenance records and must not create coordinate-based canonical
objects.

## Existing-v2 Overlap Diagnostics

| Overlap status | Rows |
|---|---:|
| `diagnostic_position_within_1_arcsec` | 75 |
| `diagnostic_position_within_5_arcsec` | 1 |
| `exact_coordinate_overlap` | 10 |
| `no_position_within_5_arcsec` | 50 |
| `unresolved_without_coordinates` | 4 |

## Row-role and Overlap Breakdown

| Source table | Proposed treatment | Overlap status | Rows |
|---|---|---|---:|
| `2015ApJ...812...34L / table4.dat` | `explicit_non_ucd_comparison_record` | `no_position_within_5_arcsec` | 22 |
| `2015ApJ...812...34L / table4.dat` | `unconfirmed_candidate_record` | `diagnostic_position_within_1_arcsec` | 28 |
| `2015ApJ...812...34L / table6.dat` | `explicit_non_ucd_comparison_record` | `no_position_within_5_arcsec` | 6 |
| `2015ApJ...812...34L / table6.dat` | `unconfirmed_candidate_record` | `diagnostic_position_within_1_arcsec` | 23 |
| `2019A&A...625A..50F / tableb1.dat` | `coordinate_null_record_pending_identity_resolution` | `unresolved_without_coordinates` | 4 |
| `2020ApJ...899..140V / table4.dat` | `reference_record_pending_evidence_review` | `diagnostic_position_within_1_arcsec` | 24 |
| `2020ApJ...899..140V / table4.dat` | `reference_record_pending_evidence_review` | `diagnostic_position_within_5_arcsec` | 1 |
| `2020ApJ...899..140V / table4.dat` | `reference_record_pending_evidence_review` | `exact_coordinate_overlap` | 10 |
| `2020ApJ...899..140V / table4.dat` | `reference_record_pending_evidence_review` | `no_position_within_5_arcsec` | 22 |

Exact normalized source names match existing literature records for
54 rows. Name equality is supporting context only and does
not override the positional review requirement.

## Nearest Existing Provenance Within Five Arcseconds

| Pending source table | Existing nearest bibcode | Rows |
|---|---|---:|
| `2015ApJ...812...34L / table4.dat` | `2019A&A...625A..50F` | 28 |
| `2015ApJ...812...34L / table6.dat` | `2019A&A...625A..50F` | 23 |
| `2020ApJ...899..140V / table4.dat` | `2019A&A...625A..50F` | 4 |
| `2020ApJ...899..140V / table4.dat` | `2022ApJ...929..147D` | 31 |

Review `pending_source_row_review.csv` for source labels, exact matches, nearest
canonical-object separations, matched bibcodes and names, and the proposed
treatment of every row. This remains a historical pre-decision overlap audit.
The T17-1596 diagnostic at 1.37 arcseconds was subsequently resolved as Fahrion
HHH86-C15 through the published Taylor GC0218 and Woodley HHH86-C15 alias chain;
the approved evidence is recorded in `source_association_reviews.json`. The audit
itself remains read-only; approved treatments are implemented separately by
`build_reference_database.py`.
