# UCD image-reference preparation

**Consolidated:** 2026-10-12  
**Role:** Topic-organized development evidence, not a replacement for current scientific requirements.

[Science guide](../science_guide.md) · [Current status](../current_status.md) · [Documentation audit](documentation_audit.md)

## Current reading guidance

The original 724-object image and Tractor-catalog reference below was followed by the interactive workbench. Its initial Tractor search used 2 arcseconds; the later review workbench uses 10 arcseconds and r < 23 to inspect off-center identifications. These are distinct retrieval versions, not conflicting instructions. On the October 12 restart, the local review database contained no saved revisions. See ../methods/reference_review.md and the August 19 journal for the implemented tool.

## Dated evidence

Each section below retains an original report's scientific content, measurements,
commands, and limitations. Status statements apply to that report's original date;
read the guidance above and current SPEC before following an old next step.

<a id="record-ucd_legacy_survey_reference"></a>

> Dated source record: `docs/ucd_legacy_survey_reference.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/ucd_legacy_survey_reference.md -->
## UCD Legacy Survey Appearance and Catalog Reference

### Purpose

This reference shows how published ultra-compact dwarf galaxies (UCDs) and one
published high-probability candidate sample appear in Legacy Survey images and
catalog measurements. It is a learning and diagnostic resource. It does not define
a new UCD selection rule and does not change any object's literature classification.

The fixed target list contains:

- 680 canonical objects classified as confirmed under `confirmation_rules_v1`; and
- 44 objects from the high-probability candidate table in Saifollahi et al. (2021),
  `tablea6.dat`. These 44 objects remain candidates, not confirmed UCDs.

The target list and its provenance are in
`data/literature/catalogs/ucd_legacy_reference_targets_v1.csv`. The scope was frozen
before inspecting Gaia or Legacy Survey outcomes.

### Three-color images

The retrieval requested a 64-by-64-pixel Legacy Survey DR10 three-color JPEG at each
literature coordinate. The pixel scale is 0.262 arcseconds per pixel, so every image
is 16.768 arcseconds wide. The image files are stored outside the repository under
`$BUBBLETEA_EXTERNAL_DATA/bubbletea/ucd_legacy_reference_v1/cutouts/`.

The server returned a readable JPEG for all 724 coordinates. A readable JPEG does
not necessarily contain survey imaging: 17 returned files are low-color viewer
placeholder tiles, while 707 contain nonuniform image content. The placeholder rule
is based on the measured distribution in this retrieval: placeholders have at most
10 distinct RGB colors, followed by a gap to 40 colors. Inspected examples at or
below 6 colors are flat blue or white viewer tiles. The outcome is 663 confirmed UCD
images, all 44 candidate images, and 17 confirmed objects without a scientifically
useful three-color image from this request.

Eight contact-sheet pages provide the visual atlas: seven pages for confirmed UCDs,
beginning with `figures/phase4/ucd_legacy_reference_confirmed_ucd_page_01_v1.png`,
and one page for the Saifollahi candidates,
`figures/phase4/ucd_legacy_reference_saifollahi_high_probability_candidate_page_01_v1.png`.

The stable label printed above each image links to
`data/literature/catalogs/ucd_legacy_reference_atlas_index_v1.csv`. That lookup table
contains the complete literature provenance, image path and status, Gaia overlap
flags, and the closest Legacy Survey catalog measurement. All images remain
`not_reviewed`; atlas generation made no source-by-source visual judgment.

### Gaia catalog overlap

The Gaia test uses an exact Gaia DR3 source identifier already recorded in the
literature database. It does not perform a new coordinate match. Of the 724 reference
objects, 175 confirmed-object rows have one testable identifier, representing 174
distinct Gaia sources. The other 549 objects are recorded as not testable rather than
as absent from the catalogs. None of the 44 Saifollahi candidates has an exact Gaia
identifier in the literature database.

Among the testable confirmed-object rows:

- 0 are in Gaia's non-single-star catalog;
- 8 are in Gaia's QSO-candidate catalog; and
- 74 are in Gaia's galaxy-candidate catalog, representing 73 distinct Gaia sources.

“Non-single star” means Gaia published an orbital or other multiple-star solution for
that source. “QSO candidate” means Gaia's processing identified the source as a
possible quasi-stellar object. “Galaxy candidate” means Gaia's processing identified
it as a possible galaxy; it is not a spectroscopic truth label. These overlaps are
evidence to inspect, not automatic rejections. In particular, the 74 confirmed-UCD
overlaps demonstrate that Gaia galaxy-candidate membership cannot be used as a UCD
veto. The detailed result is
`data/literature/catalogs/ucd_legacy_reference_gaia_membership_v1.csv`.

### Legacy Survey photometric catalog

The Legacy Survey DR10 Tractor catalog contains measurements made by fitting simple
light profiles to the images. The retrieval keeps every catalog source within 2
arcseconds of each literature coordinate and marks the closest one separately. This
preserves cases in which more than one catalog source is nearby.

There is at least one match for 585 of 724 targets: 541 confirmed UCDs and all 44
Saifollahi candidates. There is no match within 2 arcseconds for 139 confirmed UCDs.
Of the matched targets, 101 have two or more possible catalog associations, so their
closest row should not be accepted without checking the separation and image.

For the closest associations, the fitted Legacy Survey profile types are:

- 303 `PSF`: consistent with the survey's point-spread function;
- 205 `REX`: a round exponential profile;
- 38 `SER`: a Sérsic profile with a fitted Sérsic index;
- 25 `DEV`: a de Vaucouleurs profile;
- 6 `EXP`: an exponential profile with fitted ellipticity; and
- 8 `DUP`: a duplicate catalog detection.

These describe how the pipeline fit the light, not physical source classes. A `PSF`
fit does not prove that an object is a star, and an extended fit does not prove that
it is a background galaxy.

The retained catalog fields include measured and dust-corrected optical magnitudes,
infrared magnitudes, measurement uncertainties, number of exposures, fit quality,
contamination fractions, mask bits, the fitted profile type, size, ellipticity, and
Sérsic index where the catalog supplies them. Derived magnitudes are present only for
positive flux with a positive inverse variance. All associations are in
`data/literature/catalogs/ucd_legacy_reference_tractor_matches_v1.csv`; the per-target
match count and nearest two separations are in
`data/literature/validation/ucd_legacy_reference_tractor_audit_v1.csv`.

### How to use the reference

Use the atlas first to learn the range of observed UCD appearances, including barely
resolved sources, nearby companions, crowded fields, low signal-to-noise detections,
and occasional image problems. Use the atlas index to look up the corresponding
catalog fit and Gaia flags. Differences between confirmed UCDs and the 44 candidates
should be evaluated statistically before any catalog measurement becomes a review
priority or selection rule.

The immediate scientific follow-up is to summarize which Legacy Survey measurements
separate obviously extended contaminants from the confirmed-UCD reference while
retaining the known range of compact UCD appearances. That analysis must keep Gaia
high-significance astrometry and non-single-star/QSO evidence as the higher-priority
point-source contamination checks.
<!-- preserved_source_end: docs/ucd_legacy_survey_reference.md -->


