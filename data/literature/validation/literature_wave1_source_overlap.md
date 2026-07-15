# Literature Wave 1 Source Overlap Audit

**Role review status:** `approved_by_project_lead_2026-07-15`
**Pre-ingestion v2 database SHA-256:** `d9978289cc74b47660d352397d17e47c1935a13eee4f1b240ef33320d15f05bb`

This read-only audit measured the five retrieved VizieR packages against the
pre-ingestion v2 canonical positions. It records the subsequently approved table
roles but made no source
membership, identity, classification, or confirmation change.

## Measured Coverage

| Measure | Count |
|---|---:|
| Source tables | 11 |
| Preserved source rows | 4535 |
| Rows with direct or explicitly linked object coordinates | 4426 |
| Unique source coordinates | 3227 |
| Minimum nearest-canonical separation, arcsec | 0.000000000000 |
| Median nearest-canonical separation, arcsec | 138.055158029410 |
| Maximum nearest-canonical separation, arcsec | 18212.465675155705 |

## Positional Overlap

| Class | Rows |
|---|---:|
| `coordinate_not_applicable` | 109 |
| `exact_coordinate` | 16 |
| `no_counterpart_within_5_arcsec` | 3067 |
| `within_1_arcsec` | 1315 |
| `within_5_arcsec` | 28 |

## Reviewed Table Roles

| Role | Rows |
|---|---:|
| `candidate_and_contaminant_records` | 828 |
| `foreground_and_background_comparison_records` | 635 |
| `fornax_compact_system_reference_compilation` | 904 |
| `globular_cluster_comparison_records` | 633 |
| `supporting_spatial_kinematic_bins` | 109 |
| `supporting_structure_and_classification` | 828 |
| `supporting_structure_measurements` | 355 |
| `ucd_companion_evidence_records` | 21 |
| `ucd_reference_records` | 209 |
| `ucd_structural_evidence_records` | 13 |

## Decision-Relevant Source Subgroups

| Source-reported subgroup | Rows | Unique coordinates | Exact | Within 1 arcsec | Within 5 arcsec | Beyond 5 arcsec |
|---|---:|---:|---:|---:|---:|---:|
| Source-reported UCD or possible UCD | 855 | 844 | 7 | 321 | 16 | 511 |
| Wittmann compact-system compilation | 904 | 904 | 0 | 484 | 10 | 410 |
| Source-reported comparison or contaminant | 1484 | 1484 | 4 | 21 | 1 | 1458 |

Repeated rows across primary and supporting tables remain separate provenance.
An exact or nearby coordinate is overlap evidence only and does not authorize an
association. The 109 Ahn kinematic bins are supporting measurements for one UCD,
not 109 astrophysical objects.
