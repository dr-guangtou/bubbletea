# Radial-ring area accounting

**Status:** Spherical area component validated; real survey masks not yet supplied
**Date:** 2026-07-18
**Issues:** BT-005, BT-010, BT-021

## Plain-language definitions

Each radial ring now carries five separate areas:

- **Requested area:** the entire ring that the measurement asked for.
- **Successfully queried area:** the part covered by retrieval strips whose saved
  files passed all completion and integrity checks.
- **Missing area:** the requested part without a verified completed strip.
- **Masked area:** the union of explicitly unusable regions inside the successfully
  queried area. Overlapping masks are counted once, not once per mask.
- **Usable area:** successfully queried area minus masked area. This is the
  denominator for a source density.

An interrupted query therefore produces a positive missing area rather than a
false zero source density. A complete query can still have less usable area than
requested area if an authoritative mask removes part of the sky.

The central galaxy exclusion is a different concept. It marks inner rings as
diagnostic-only for the scientific analysis; it does not pretend that those rings
were missing from the archive or geometrically unusable.

## Spherical calculation

The requested area is the analytic area between two circles on a sphere. Retrieval
strips and circular masks are intersected with each ring on the sphere, including
right-ascension wraparound and polar geometry. The intersections are integrated to
an internal absolute tolerance of `1e-13` steradian and validated to `1e-8` square
degree. Here, "exact area" means spherical rather than a flat-sky approximation,
with the numerical integration error recorded in every row.

Each mask must have an identifier, center, angular radius, reason, and provenance.
The area code forms the union of all masks before subtraction, so overlapping masks
cannot remove the same sky twice.

## Bounded validation

The measured retrieval plans for NGC 4698, M60, and ESO 006-G001 were divided into
four test rings each. These are fractions of the archive performance-test circles,
not physical-kiloparsec rings or approved scientific apertures.

For all three completed retrievals, the successfully queried area reproduces the
requested spherical area. The largest ring-level difference is
`1.873002e-12` square degree, and the four rings for each host sum to the analytic
circle area within `1.110223e-16` square degree.

Two overlapping circular masks were then placed in the M60 fixture. They are
explicitly labeled `synthetic_fixture_not_survey_coverage`; they are not real Gaia,
bright-star, dust, or imaging masks. The complete fixture contains
`1.767121` square degrees of requested and successfully queried area. The union of
the two masks removes `0.039362` square degree, leaving `1.727758` square degrees
usable. A controlled partial state with only one of two retrieval strips complete
records `0.884062` square degree queried and `0.883059` square degree missing.

All 16 predeclared checks pass in `0.263657` seconds. They cover completed and
partial retrievals, area identities, overlapping-mask union, non-negative areas,
polar geometry, central-ring disposition, retrieval-plan counts, and the synthetic-
mask provenance warning.

## Remaining boundary

The accounting component is ready, but the project does not yet have an approved
real bright-star, missing-coverage, dust, or ancillary-imaging mask contract. Real
host densities must not use the synthetic fixture masks. Each real mask source must
be selected, documented, versioned, and validated before it can reduce usable area.

## Artifacts and reproduction

- `data/results/background/radial_ring_area_accounting_validation_v1.csv`
- `data/results/background/radial_ring_area_accounting_validation_v1.json`

```bash
uv run python scripts/phase3_background/validate_radial_ring_area_accounting.py
```
