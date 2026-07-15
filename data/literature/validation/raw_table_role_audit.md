# Raw Literature Table Role Audit

**Review status:** `approved_by_project_lead_2026-07-14`

This audit measures retrieved tables and proposes roles. It does not change v2
membership, object identity, evidence approval, or confirmation state.

## Proposed Roles

| Role | Tables |
|---|---:|
| `candidate_records` | 1 |
| `mixed_reference_records` | 1 |
| `primary_records` | 13 |
| `primary_reference_records` | 1 |
| `selection_pool_records` | 1 |
| `supporting_evidence` | 2 |
| `supporting_measurements` | 4 |

## Current v2 Coverage

| Status | Tables |
|---|---:|
| `ingested_all_rows_four_unassociated` | 1 |
| `ingested_as_candidate_subset` | 1 |
| `ingested_from_legacy` | 8 |
| `ingested_from_raw` | 2 |
| `ingested_with_object_level_roles` | 2 |
| `ingested_with_reproduced_roles` | 1 |
| `ingested_with_reviewed_associations` | 1 |
| `row_linked_as_evidence` | 2 |
| `row_linked_as_supporting_measurements` | 4 |
| `separate_selection_pool` | 1 |

The proposed primary/reference tables currently absent from direct source-table
membership contain 0 measured rows. This does not imply that
every object lacks a canonical counterpart; row-level overlaps are reported in
`pending_source_row_review.md`. The approved, separate Saifollahi selection pool
contains 1155 measured rows and is excluded from the positive
reference denominator.

The detailed CSV records raw row counts, coordinate coverage, multiplicity, current
publication-level v2 counts, and the four coordinate-null Fahrion row names. The
manifest review status governs which proposed roles may be implemented.
