# Literature Wave 1 Identity Candidate Audit

**Status:** `approved_by_project_lead_2026-07-15`
**Reference database SHA-256:** `6e3811c5eb45898c2fd5aa896374822758c69f664f6d513ba8bd9b1cfee1a8a7`

This read-only audit compares Wave 1 object and comparison rows only with
canonical identities containing pre-Wave literature records. Position alone never
creates a candidate: every row below requires an exact normalized name or a
published alias from a source payload.

## Coverage

| Measure | Count |
|---|---:|
| Pre-Wave canonical identities | 2314 |
| Wave 1 literature rows | 2339 |
| Wave 1 rows already linked to pre-Wave identities | 15 |
| Remaining Wave 1 rows screened | 2324 |
| Wave 1 rows with name or alias matches | 161 |
| Wave-to-canonical identifier match pairs | 186 |

## Routing

| Recommendation | Match pairs | Wave rows |
|---|---:|---:|
| `identifier_collision_not_recommended` | 4 | 4 |
| `manual_identity_review` | 175 | 153 |
| `recommend_same_identity` | 7 | 7 |

| Routing reason | Match pairs |
|---|---:|
| `identifier_match_is_spatially_inconsistent` | 4 |
| `multiple_baseline_canonicals_within_1_arcsec` | 175 |
| `unique_nearest_name_or_alias_match_within_1_arcsec` | 7 |

`recommend_same_identity` requires identifier evidence, the matched canonical as
the nearest baseline object, separation no greater than one arcsecond, and no
competing baseline object within one arcsecond. The angular condition is a guard
on a name-led cohort, not a reusable matching radius.

## Proposed High-Confidence Cohort

| Wave bibcode | Wave name | Baseline names | Separation, arcsec | Evidence | Minimum velocity difference, km/s |
|---|---|---|---:|---|---:|
| 2017ApJ...835..212K | M87UCD-1 | M87UCD-1 | 0.007032699785 | `direct_name` | 0.0 |
| 2017ApJ...835..212K | S9053 | S9053 | 0.010544213542 | `direct_name` | 0.0 |
| 2017ApJ...835..212K | M87UCD-31 | M87UCD-31 | 0.017579352593 | `direct_name` | 0.0 |
| 2020ApJS..250...17L | NGVS-UCD460 | M87UCD-1 | 0.044253276092 | `published_alias` | 0.0 |
| 2020ApJS..250...17L | NGVS-UCD725 | M59-UCD3 | 0.046782355557 | `published_alias` |  |
| 2020ApJS..250...17L | NGVS-UCD391 | M87UCD-38 | 0.074503892048 | `published_alias` | 0.0 |
| 2020ApJS..250...17L | NGVS-UCD719 | M59cO | 0.136000985070 | `published_alias` |  |

Rows routed to manual review or identifier collision remain in the companion CSV.
No association, canonical identity, or classification was changed.
