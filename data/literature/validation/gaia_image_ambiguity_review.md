# Gaia Image-Ambiguity Review

**Date:** 2026-07-14
**Status:** Project-lead-approved split treatment recorded.

## Scope

- Held two-position groups audited: 23
- `fornax_spectroscopic_compilations`: 7
- `liu_m87_and_fahrion_compilation`: 16
- Frozen group-review input: `data/literature/validation/gaia_association_group_review.csv`
  (SHA256 `7573076010c5688a72812272a066b646e0136786e0804ba4748619d1c69562f8`)
- Frozen pair-geometry input: `data/literature/validation/gaia_association_pair_geometry.csv`
  (SHA256 `16bf6e4912bdd4563e8a938b1879528b422fcaa2c118e6e2532eecf4d816ac9d`)
- Review annotations: `data/literature/sources/gaia_image_ambiguity_reviews.json`
  (SHA256 `5ebaf8a3d7f60a159838e0d6b28455a454b1d7606a447fa01bbfb04b2ad6a569`)

## Measured Gaia Neighborhoods

- Groups with a competing Gaia DR3 source within 1 arcsecond: 0
- Groups with a competing Gaia DR3 source within 2 arcseconds: 0
- Groups with a competing Gaia DR3 source within 5 arcseconds: 1

The 5-arcsecond aperture is a diagnostic neighborhood, not an association or
identity radius. The TAP request uses conservative coordinate boxes, followed by
an exact local spherical-separation filter.

## Imaging Boundary

Legacy Survey DR10 data, model, and residual JPEG cutouts are centered on the
authoritative Gaia coordinate. They are diagnostic views only. The viewer JPEGs
do not establish DR10 `maskbits`, catalog measurement quality, or an astrophysical
identity by themselves; DR10 known issues and bitmask definitions must be checked
before using Legacy Survey measurements in scientific selection.

## Decision State

The project lead approved accepting 22
shared identities and retaining 1 close pair as a separate pair of
canonical objects sharing ambiguous Gaia evidence. This audit artifact records
the authorization but does not itself modify the database; the deterministic v2
builder applies the approved treatment.
