# Gaia Association Geometry Audit

**Date:** 2026-07-14
**Decision status:** `86_two_position_groups_approved_31_groups_pending`
**Gaia table:** `gaia_dr3.gaia_source`

## Measured Scope

| Measure | Count |
|---|---:|
| Gaia DR3 source IDs | 117 |
| Two-position Gaia groups | 109 |
| Three-position ambiguous Gaia groups | 8 |
| Groups with reported `is_ucd` conflicts | 14 |
| Gaia rows flagged `duplicated_source` | 10 |
| Gaia rows with nonzero `ipd_frac_multi_peak` | 17 |
| Maximum literature-to-Gaia separation (arcsec) | 0.861040672349 |
| Maximum legacy planar-vs-spherical distance difference (arcsec) | 0.176110481759 |

All Gaia source IDs were resolved against authoritative DR3 coordinates. The
pair and group exports record spherical Gaia-to-literature distances, legacy
cross-match distances, source combinations, label conflicts, and Gaia image-
parameter diagnostics.

## Review Routing

| Recommended action | Gaia groups |
|---|---:|
| `identity_and_classification_review` | 14 |
| `manual_gaia_image_ambiguity_review` | 23 |
| `manual_multi_position_identity_review` | 8 |
| `recommend_accept_shared_identity` | 72 |

The 64 M87 groups compare Liu primary-table coordinates with the later Fahrion
compilation. The other 53 groups are in Fornax. Saifollahi table A1 explicitly
describes its KNOWN UCD/GC sample as a compilation of earlier spectroscopic
catalogs, including Gregg et al. through the Maddox compilation. That source
history supports cross-catalog identity, but reported GC/UCD role conflicts remain
classification questions rather than evidence that may be silently discarded.

## Interpretation Boundary

A shared Gaia detection is strong cross-catalog evidence, but it does not by
itself prove that two close literature positions are the same astrophysical
object. This is especially important for the three-position groups and for
groups with conflicting reported UCD roles. This audit itself is read-only. The
builder separately implements the approved 72 clean groups and 14 role-conflict
groups, retaining the other 31 groups for image or multi-position review.

Review `gaia_association_group_review.csv` first, then use
`gaia_association_pair_geometry.csv` for row-level evidence.
The cached Gaia rows and exact TAP query are recorded in
`data/literature/sources/gaia_dr3_association_sources.csv` and its JSON manifest.
