# Gaia Multi-Position Identity Review

**Date:** 2026-07-15
**Status:** Project-lead-approved shared identities recorded.

## Scope and Provenance

- Three-position Gaia groups: 8
- Frozen group review: `data/literature/validation/gaia_association_group_review.csv`
  (SHA256 `7573076010c5688a72812272a066b646e0136786e0804ba4748619d1c69562f8`)
- Frozen pair geometry: `data/literature/validation/gaia_association_pair_geometry.csv`
  (SHA256 `16bf6e4912bdd4563e8a938b1879528b422fcaa2c118e6e2532eecf4d816ac9d`)
- ADS source metadata: `data/literature/sources/gaia_multi_position_literature.json`
  (SHA256 `12abd402d2246e3989c533c68ca7874e97abb7a7e6841fa0a6cc357c9d5b23cd`)
- Project-lead decision manifest: `data/literature/sources/gaia_multi_position_reviews.json`
  (SHA256 `938efafa034ac448e2f5806abd15b408cbf6f371547a69b2e39802344cfac4d8`)
- Authoritative source tables: Gregg table 2, Fahrion table B1, and Saifollahi
  table A1. Brüns catalog aliases are supporting cross-identifications.

## Evidence Summary

All eight groups combine one Gregg, one Fahrion/Mieske, and one Saifollahi
position around the same Gaia DR3 source. All reported roles are positive; Gaia
has no duplicated-source, IPD multi-peak, or odd-window flag in these groups.
Independent Gregg and Fahrion velocities remain consistent with Fornax membership
and refer to the same sub-arcsecond coordinate locus. Brüns supplies explicit
historical cross-identifications for five loci, including `F-24(UCD4)`,
`F-1(UCD2)`, `F-12`, `F-7`, and `F-22`.

| Gaia DR3 ID | Fahrion | Gregg | Gregg aliases | Brüns aliases | Max position separation (arcsec) | Velocity difference (km/s) |
|---|---|---:|---|---|---:|---:|
| 4860278691160658816 | F-9 | 35 | 1-2024 |  | 0.7383329672054952 | 54.0 |
| 4860292508072273536 | F-7 | 28 | 89:22 | 89:22;F-7;UCD33 | 0.4243600342652094 | 15.0 |
| 4860293779382565504 | F-1a | 20 | UCD 2, 2-2111, 91:93 | 91:93;F-1(UCD2) | 0.48611669073637886 | 51.0 |
| 4860294324842097792 | F-6 | 27 | 0-2024 |  | 0.6113898460225893 | 268.0 |
| 4860297176700385408 | F-5 | 24 | 2-2134 |  | 0.8285033965841646 | 92.0 |
| 4860372905562802688 | F-24 | 53 | UCD 4, 1-2083 | F-24(UCD4) | 0.6189201258610015 | 18.0 |
| 4860376994371696256 | F-22 | 50 | 1-060, GC241.1 | F-22 | 0.5647791276910767 | 32.0 |
| 4860388367445133696 | F-12 | 38 | 0-2031 | F-12 | 0.8739343135854314 | 59.0 |

The largest coordinate span is 0.8739343135854314
arcseconds for Gaia DR3 `4860388367445133696`. The largest
velocity difference is 268.0 km/s
for `F-6` / Gregg
`27`; both measurements still identify a
Fornax member at the same Gaia-centered locus. This comparison is flagged as
`moderate_measurement_tension_preserve_both`; neither velocity is averaged,
discarded, or used to alter the reported source measurements. Saifollahi table A1
also contains two identical rows at the F-1/UCD2 locus; both provenance records
remain preserved at one canonical position.

## Recommendation

The project lead approved all eight groups as eight astrophysical objects, each retaining every
literature record, measurement, original name, and superseded canonical identifier
as provenance. This audit records the authorization but does not itself change
database membership or proposal status; the deterministic v2 builder applies it.
