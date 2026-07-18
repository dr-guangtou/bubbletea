# Five-host Gaia field-condition review

**Status:** Diagnostic measurements completed; no scientific background field approved
**Date:** 2026-07-18
**Gaia release reference:** `2023A&A...674A...1G`, DOI
`10.1051/0004-6361/202243940`

## Purpose

This review asks whether temporary same-Galactic-latitude comparison circles have
similar Gaia coverage and total source density across five different nearby-galaxy
settings. “Before selection” means that these measurements are made before applying
the UCD classifier. No UCD-candidate count is used to choose or approve a field.

The five target galaxies are NGC 4698, the nearby ESO 006-G001, the group main
galaxy NGC 1316, the group member M60, and the unresolved-environment case Arp 244.

## Temporary geometry

In this document, a **galaxy-centered test circle** is a 0.1-degree-radius circle
centered on the named galaxy. Earlier summaries called this the “target patch.” A
**comparison test circle** is an equal-size circle moved away from the galaxy while
remaining at the same Galactic latitude. Earlier summaries called these
“diagnostic patches.” They are measured to test the method; they are not yet
approved for subtracting contamination from the galaxy measurement.

The 0.1-degree radius was chosen only for a bounded archive-query test. It is not
the real galaxy measurement aperture. At the catalog distances used here, this
angle corresponds to a projected radius of 4.712394 kpc for ESO 006-G001 and
41.771283 kpc for NGC 4698. The real measurement must instead preserve a series of
concentric circular rings in physical and host-size-normalized radius. A calibrated
inner circular region will be omitted from UCD inference because galaxy
substructure, compact star-forming regions, and H II regions can dominate it.

For the four galaxies with accepted Kourkchi-Tully catalog associations, two
comparison test circles were placed east and west at exactly the galaxy's Galactic
latitude. Their temporary separation uses twice the catalog's estimated
collapsed-group radius, followed by a 1.2 center-separation multiplier. These are
test values, not approved halo boundaries.

For group cases, each comparison test circle was also checked against a circle
centered on the catalog's group main galaxy. All four group test circles clear that
temporary boundary, but this does not make them valid scientific backgrounds. Arp
244 has no accepted environment association, so only its galaxy-centered circle
was measured. We did not create off-galaxy comparison coordinates from an
unverified group center or group size. That is what the earlier phrase “no invented
comparison” meant; it did not mean that any observed data were fabricated.

## Quantities measured

- **Total Gaia source count and density:** every Gaia DR3 catalog entry inside the
  circle whose G magnitude lies between 11.262918 and 21.757988. No parallax,
  proper-motion, binary-star, QSO, morphology, or UCD-classifier filter is applied.
  These counts are therefore expected to be dominated by ordinary Milky Way stars.
- **Visibility periods:** separated groups of Gaia observations contributing to a
  source. The table reports the average within each patch.
- **Matched astrometric transits:** individual Gaia passages associated with a
  source's astrometric processing. The table reports the patch average.
- **`M10`:** the median G magnitude of Gaia entries with no more than ten matched
  astrometric transits and a reported G magnitude. Unlike the total-count column,
  this depth calculation is not restricted to the classifier's G-magnitude range.
  It is a local Gaia-depth indicator; a brighter value generally indicates
  shallower coverage.

## Measured result

| Host | Circle | Gaia entries in the stated G range | Entries per square degree | Mean visibility periods | Mean matched transits | M10 |
|---|---|---:|---:|---:|---:|---:|
| NGC 4698 | Target | 121 | 3851.55 | 15.98 | 39.12 | 21.187 |
| NGC 4698 | West test | 100 | 3183.10 | 12.07 | 37.97 | 21.093 |
| NGC 4698 | East test | 122 | 3883.38 | 14.46 | 35.92 | 21.102 |
| ESO 006-G001 | Target | 530 | 16870.43 | 23.55 | 33.55 | 21.018 |
| ESO 006-G001 | West test | 460 | 14642.26 | 21.17 | 28.54 | 20.913 |
| ESO 006-G001 | East test | 584 | 18589.30 | 24.85 | 35.07 | 21.001 |
| NGC 1316 | Target | 136 | 4329.02 | 23.05 | 37.38 | 21.213 |
| NGC 1316 | West diagnostic | 110 | 3501.41 | 26.65 | 56.51 | 21.129 |
| NGC 1316 | East diagnostic | 81 | 2578.31 | 24.69 | 40.88 | 21.631 |
| M60 | Target | 289 | 9199.16 | 9.96 | 35.94 | 21.384 |
| M60 | West diagnostic | 59 | 1878.03 | 12.64 | 21.32 | 20.886 |
| M60 | East diagnostic | 130 | 4138.03 | 15.58 | 33.87 | 21.049 |
| Arp 244 | Target only | 330 | 10504.23 | 11.82 | 21.14 | 21.134 |

The complete run took 46.93 seconds. All nine validation checks passed: all frozen
positions were measured, retrievals were complete, required observation values
were present, every patch had positive area, the queries contained no selector
output, and no test patch was marked as an approved scientific background.

## Interpretation

The two one-galaxy catalog cases have comparatively small `M10` ranges across their
three patches: 0.094 magnitude for NGC 4698 and 0.105 magnitude for ESO 006-G001.
The group cases have larger ranges: 0.503 magnitude for NGC 1316 and 0.498 magnitude
for M60. The average observation counts also vary substantially within some sets.
This confirms that exact Galactic-latitude matching does not guarantee similar Gaia
coverage.

Total Gaia density needs more careful treatment. M60's target patch contains 289
Gaia sources, while its test patches contain 59 and 130. The target patch may
contain real sources associated with M60 or the Virgo environment, not merely a
different level of Gaia crowding or completeness. Therefore total Gaia density is
a useful diagnostic but cannot be required to match the target rigidly: doing so
could reject genuine host-associated populations before the UCD selector is even
applied.

The next calibration should learn how field properties predict selected-source
density from comparison fields that are not centered on target galaxies. It should
then test that relationship on spatially separate comparison fields. Target
overdensities must not be used to choose the matching tolerances.

## Artifacts and reproduction

- `data/results/background/background_review_field_positions_v1.csv`
- `data/results/background/background_review_field_positions_v1.json`
- `data/results/background/background_review_field_conditions_v1.csv`
- `data/results/background/background_review_field_conditions_v1.json`

```bash
uv run python scripts/phase3_background/build_background_review_field_positions.py
uv run python scripts/phase3_background/measure_background_review_field_conditions.py
```
