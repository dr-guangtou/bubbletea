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

## Complete selector-version-1 result

The complete field was retrieved in 14 verified declination strips and scored
locally with the unchanged selector version 1. The selector retained 4,920 of 45,402
sources, or 10.8365%. This is the observed candidate workload before any catalog or
visual contamination review; it is not an estimated UCD fraction.

Both reliable UCD controls were retrieved and retained, with selector scores 0.9810
and 0.9249. All nine literature candidates that have one unique Gaia identifier were
also retrieved and retained. Twelve other literature candidates and all six rejected
comparisons lack a unique Gaia identifier in the frozen reference table, so an exact
identifier test cannot determine whether they were recovered. They remain explicitly
labeled as not testable rather than being counted as missed.

The radial profile shows a strong density increase inside 50 kpc in both raw Gaia
sources and selector-retained sources. This confirms the need to keep the inner
region diagnostic. Outside 50 kpc, the selector-retained density declines from
628.47 sources per square degree in the 50--75 kpc interval to 339.59 sources per
square degree in the 300--600 kpc interval. These measurements have not yet been
corrected for contamination and do not establish a UCD excess.

Source-level tables are stored outside the repository under
`$BUBBLETEA_EXTERNAL_DATA/bubbletea/m60_positive_control_v1/`. The checked profile,
known-object recovery table, and run record are stored in
`data/results/radial_search/`. The companion figure is
`figures/phase4/m60_positive_control_radial_profile_v1.png`.

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

The following plain-language flags are approved for the complete M60 field. The
review columns and allowed values are frozen in
`data/results/radial_search/m60_positive_control_review_rules_v1.json`.

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

The evidence is recorded separately:

- A published H II-region or young-cluster catalog association can assign the flag.
  These catalogs are rare and incomplete, so no catalog match provides no evidence
  against the flag.
- Color can prioritize a source for inspection but cannot assign the flag by itself.
  Genuine UCDs can also be blue.
- Visual inspection can assign the flag when the source is associated with visible
  star-forming structure or shows irregular compact emission. Ambiguous appearance
  is recorded as uncertain.

A positive flag requires either a catalog association or visual evidence. It remains
a review flag and is not an automatic rejection.

### Nearby-source blend or image problem

This flag requires visual inspection of the small image. Assign it when the image
shows overlapping or nearby sources, multiple brightness peaks, asymmetric light,
a mismatch between the Gaia position and image center, saturation, diffraction
features, an image boundary, or another artifact. Ambiguous cases remain uncertain,
and an unusable image is never labeled clean.

Gaia measurements such as the multiple-peak fraction or BP/RP flux-excess factor can
prioritize a source for inspection. They are stored as a separate Gaia warning and
cannot assign this visual flag. The visual flag describes the reliability of the
image interpretation; it is not a physical classification.

## Separation of the audit and candidate shortlist

The individual Gaia rows have now been retrieved and selector version 1 has been
applied locally. Visual inspection uses two separate sets:

- a representative review sample used to measure what kinds of contaminants remain;
  and
- a promising-candidate shortlist used to identify follow-up targets.

Keeping these sets separate prevents a deliberately attractive shortlist from being
misreported as the real contamination rate. The representative audit is frozen
below. The promising shortlist will be designed separately after the audit images
are retrieved.

## Frozen representative visual audit

The first visual audit contains 400 selector-retained sources that are not among the
11 literature objects with exact Gaia identifiers. It includes 100 randomly selected
sources from each of four radial zones: 0--50, 50--150, 150--300, and 300--600 kpc.
Within a zone, sources are ordered by a permanent SHA-256 hash of the audit version
and Gaia identifier, so every eligible source in that zone has the same selection
chance and the selection can be reproduced without relying on a particular random-
number generator.

The eligible population contains 4,909 sources: 151, 372, 982, and 3,404 in the four
zones respectively. Because the audit selects the same number from zones of different
sizes, population summaries must use the stored weights 1.51, 3.72, 9.82, and 34.04.
An unweighted average of the four reviewed groups would overrepresent the inner
region. The sample is recorded in
`data/results/radial_search/m60_positive_control_visual_audit_sample_v1.csv`.

The known literature objects remain separate controls. The promising-candidate
shortlist will also remain separate and cannot be used to estimate the contamination
rate. At the time of freezing, every visual field in the audit sample remains marked
“not reviewed,” and no audit image has been requested or opened.

## Complete unreviewed audit images

All 400 frozen audit sources now have verified Legacy Survey DR10 three-color images.
Each image is 64 by 64 pixels at 0.262 arcseconds per pixel, or 16.768 arcseconds
wide. The files occupy 1.6 MB and are stored outside the repository under
`$BUBBLETEA_EXTERNAL_DATA/bubbletea/m60_positive_control_v1/audit_cutouts/`.
The manifest records the exact URL, portable path, byte count, and SHA-256 digest for
every image.

Four contact sheets show 100 sources per radial zone. Each panel is labeled only by
its permanent audit identifier; Gaia score, magnitude, and candidate priority are
omitted to reduce visual-review bias. Creating and inspecting the contact sheets does
not itself assign a flag. Every review column remains “not reviewed” until a reviewer
records an explicit assessment using the frozen rules.
