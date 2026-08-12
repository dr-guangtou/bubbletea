# M60 Positive-Control Search

## Purpose

M60 is the first real nearby-galaxy field used to test the unchanged Gaia selector.
It is called a **positive control** because the literature reference database contains
two reliable UCDs associated with M60. Recovering them checks that the search can find
known examples, but it is not independent proof of selector accuracy because those
objects helped inform earlier development work.

The first pass has two separate products:

1. a radial profile containing every source that passes selector version 1; and
2. review flags that identify reasons a passing source might be a contaminant.

A review flag never removes a source or changes the radial profile. Several flags may
apply to the same source, and the absence of a flag is not proof that the source is a
UCD.

## Frozen field and known objects

The M60 center is right ascension 190.9166453 degrees and declination 11.5526118
degrees. Its adopted distance is 16.6571232806881 Mpc. The measurement keeps 14
concentric radial intervals from 0 to 600 kpc; the 600 kpc boundary is 2.0629379158
degrees from the center and encloses 13.3682719349 square degrees. The inner 50 kpc is
temporarily kept separate for review because M60 and nearby galaxy structure can make
source interpretation difficult there. This temporary boundary is not yet a
scientifically calibrated exclusion radius.

The reference database contains 29 objects associated with M60:

- 2 reliable confirmed UCDs, used as recovery controls;
- 21 literature candidates, reported separately because their UCD status is not
  confirmed; and
- 6 rejected literature comparisons, retained as checks rather than targets.

The exact identities and provenance are recorded in
`data/results/radial_search/m60_positive_control_known_objects_v1.csv`.

## Measured raw workload

One archive query counted sources without downloading individual rows. Within the
600 kpc circle and the frozen Gaia G-magnitude range 11.2629184723--21.7579879761,
the field contains 45,402 Gaia sources, or 3,396.2505 sources per square degree. The
query took 2.6108 seconds.

This is a raw Gaia count. It does **not** say that 45,402 sources pass the UCD
selector. Individual Gaia rows must be retrieved and evaluated locally before the
selector-passing count, radial profile, or contamination rate can be measured.

## Compact Legacy Survey image pilot

The two reliable UCD controls were retrieved from the Legacy Survey DR10 three-color
JPEG service. Each image is 64 by 64 pixels at 0.262 arcseconds per pixel, giving a
measured field width of 16.768 arcseconds. Both controls appear as compact central
sources at this scale. The images also retain enough immediate surroundings to reveal
nearby sources that could affect visual interpretation. This supports using the same
scale for the first review pass.

The JPEG images are stored outside the repository under
`$BUBBLETEA_EXTERNAL_DATA/bubbletea/m60_positive_control_v1/known_ucd_cutouts/`.
Their portable paths, exact URLs, and file digests are recorded in
`data/results/radial_search/m60_known_ucd_legacy_cutouts_v1.csv`. The comparison
figure is `figures/phase4/m60_known_ucd_legacy_cutouts_v1.png`.

These color images are visual aids, not calibrated morphology measurements. Legacy
Survey coverage, image masks, and visual labels do not alter Gaia coverage or the
area used for the radial profile.

## Proposed review flags

The following plain-language flags are proposed for the complete M60 field. Their
exact numerical boundaries have not been approved yet.

### Measured parallax or motion

Flag a source when Gaia measures parallax or proper motion much more precisely than
zero. This is evidence for a foreground star because a distant UCD should have no
measurable parallax or sky motion. Store the measurements and their uncertainties,
not only the flag, so borderline cases remain reviewable. The earlier benchmark did
not justify a universal hard rejection boundary, so this remains a warning.

### Gaia non-single-star catalog association

Flag a source that appears in Gaia's non-single-star tables. These tables contain
sources for which Gaia fitted orbital, acceleration, or other multiple-star behavior.
Such an association is strong evidence for a stellar system, but it remains a review
flag in this first pass.

### QSO catalog association

Flag a source associated with a Gaia or external QSO catalog. A QSO is an active
galactic nucleus whose unresolved light can resemble a compact source. Catalog
membership is evidence, not absolute truth, and QSO flags do not remove sources from
the profile.

### Galaxy-candidate or visibly extended source

Flag catalog associations or image structure suggesting a background galaxy. Gaia's
galaxy catalog is a candidate catalog, so it may include real UCDs or compact
star-forming regions and cannot be treated as a truth label. A clearly extended image
is useful review evidence, while a point-like image does not rule out a compact
background galaxy.

### Compact star-forming region or young cluster

Flag evidence that a source is an H II region, meaning gas ionized by young stars, or
a young compact star cluster associated with a nearby galaxy. These objects can
cluster around a host and therefore are more dangerous than a uniform background.
Color, position relative to visible galaxy structure, and catalog associations can
support the flag, but no single indicator is an automatic rejection in the first
pass.

### Nearby-source blend or image problem

Flag a source when the small image shows overlapping sources, a close neighbor, an
image artifact, or ambiguous centering. This flag describes the reliability of the
visual interpretation; it is not a physical classification.

## Next decision before the full field

The next step is to retrieve the individual Gaia rows needed by selector version 1,
apply the selector locally, and measure the passing count in every radial interval.
Before visually inspecting those passing sources, the project should freeze two
separate sets:

- a representative review sample used to measure what kinds of contaminants remain;
  and
- a promising-candidate shortlist used to identify follow-up targets.

Keeping these sets separate prevents a deliberately attractive shortlist from being
misreported as the real contamination rate. Catalog-based flags can be computed for
all passing sources; the number and allocation of image cutouts should be chosen only
after the actual passing count is measured.
