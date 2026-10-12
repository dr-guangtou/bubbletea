# First real-host profiles: NGC 4698 and M60

**Consolidated:** 2026-10-12  
**Role:** Topic-organized development evidence, not a replacement for current scientific requirements.

[Science guide](../science_guide.md) · [Current status](../current_status.md) · [Documentation audit](documentation_audit.md)

## Current reading guidance

NGC 4698 and M60 have 14-ring profiles through 600 kpc. M60's 400-source representative contamination sample awaits visual classification. The first-stage 50 kpc central exclusion is conservative working geometry, not a final scientific boundary. Flagged sources remain in the frozen-selector profiles during the first pass.

## Dated evidence

Each section below retains an original report's scientific content, measurements,
commands, and limitations. Status statements apply to that report's original date;
read the guidance above and current SPEC before following an old next step.

<a id="record-first_stage_host_profile_fixture"></a>

> Dated source record: `docs/first_stage_host_profile_fixture.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/first_stage_host_profile_fixture.md -->
## First-stage host profile fixture

**Date:** 2026-08-11

**Script:** `scripts/phase3_background/freeze_first_stage_host_profiles.py`

**Command:**
`uv run python scripts/phase3_background/freeze_first_stage_host_profiles.py`

**Outputs:**

- `data/results/background/first_stage_host_profile_fixture_v1.csv`
- `data/results/background/first_stage_host_profile_fixture_v1.json`

### Purpose

This fixture defines the physical rings to retrieve before any large-radius Gaia
source count is inspected. It uses the five review galaxies that were already
selected from host identity, distance, and environment information alone.

Every host retains the same 14 rings with edges at 0, 5, 10, 15, 20, 25, 30, 40,
50, 75, 100, 150, 200, 300, and 600 kpc. The source-level output must also retain
continuous physical radius so these rings can be recombined without another Gaia
query.

### Temporary central treatment

The inner 0--50 kpc is labeled as a conservative contamination region for the first
stage. Its eight component rings remain in the output, but they are withheld from
UCD inference. Candidate boundaries at 20, 25, 30, 40, and 50 kpc may later be
compared using contamination behavior; they cannot be selected because one gives a
larger apparent UCD excess.

This 50 kpc choice is deliberately conservative and temporary. It is not a claim
that every galaxy has a 50 kpc visible body.

### Outer profile

Every requested profile reaches 600 kpc. No final outer signal boundary is selected
yet. The measured profile will be inspected first, and failed or incomplete outer
coverage will remain missing area rather than silently shortening the profile.

| Host | Distance (Mpc) | 50 kpc radius (deg) | 600 kpc radius (deg) | 600 kpc circle area (deg²) |
| --- | ---: | ---: | ---: | ---: |
| NGC 4698 | 23.933158 | 0.119699 | 1.436094 | 6.478776 |
| ESO 006-G001 | 2.700000 | 1.060912 | 12.528808 | 491.177142 |
| NGC 1316 | 19.769696 | 0.144908 | 1.738363 | 9.492875 |
| M60 | 16.657123 | 0.171985 | 2.062938 | 13.368272 |
| Arp 244 | 19.933481 | 0.143717 | 1.724089 | 9.337623 |

The nearby dwarf remains part of the fixed review set even though its requested sky
area is much larger. Geometry difficulty is not a scientific exclusion criterion.

### Galaxy-size-normalized view

The current host table contains no verified `R50`, the radius enclosing half of a
galaxy's light. Physical profiles therefore remain available, while the `R50`-
normalized view is explicitly unavailable. Once a provenance-bearing `R50` is
added, both views must be reported.

### First live benchmark

NGC 4698 is the first archive benchmark because it has the smallest 600 kpc angular
radius among the fixed review galaxies whose isolated-environment association is
resolved. This is a geometry-only choice and uses no Gaia source count.

All 16 fixture checks pass with zero archive queries.

The count-only 600 kpc NGC 4698 benchmark measured 23,811 Gaia sources in the
frozen G-magnitude range over 6.478776 square degrees. The archive returned the
single aggregate count in 2.004 seconds. No source rows were downloaded, and the
point-source contamination selector was not applied. All nine benchmark checks
pass.

The next step is the explicitly bounded, resumable NGC 4698 source retrieval. Its
output will report both the density of all Gaia sources in the frozen magnitude
range and the density that remains after the point-source contamination selector
in every preserved physical ring.

### First measured profile

The complete source retrieval used six non-overlapping sky strips, each containing
no more than the previously validated 5,000-row limit. It retrieved all 23,811
unique sources and retained their continuous angular and projected physical radius
outside the repository under `BUBBLETEA_EXTERNAL_DATA`. The frozen point-source
contamination selector retained 2,548 sources. All fourteen run checks pass.

Outside the temporary 50 kpc central exclusion, the all-source density ranges from
3,599.136759 to 4,087.777954 per square degree and the selector-passing density
ranges from 317.377181 to 426.550743 per square degree. The six outer rings contain
23,650 all-source objects and 2,530 selector-passing objects over 6.433764 square
degrees. The remaining ring-to-ring variation is consistent with a broadly flat
first profile, but one host is not enough to select a final outer signal boundary.

The inner bins have very small areas and few objects. For example, the apparently
high selector-passing density inside 5 kpc is based on one object. The temporary
0--50 kpc exclusion therefore remains unchanged rather than being tightened from
this profile.

The profile is shown in
`figures/phase3/first_stage_ngc4698_radial_profile.png`. Vertical error bars are
exact central 68.27% intervals from counting uncertainty; horizontal bars show the
full physical width of each ring.

The locations of all passing sources and their distributions in the nine frozen
selector features are documented in
`docs/first_stage_ngc4698_candidate_diagnostics.md`. That diagnostic finds no
strong Gaia-only standout and changes no selector or radial boundary.
<!-- preserved_source_end: docs/first_stage_host_profile_fixture.md -->

<a id="record-first_stage_ngc4698_candidate_diagnostics"></a>

> Dated source record: `docs/first_stage_ngc4698_candidate_diagnostics.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/first_stage_ngc4698_candidate_diagnostics.md -->
## First-stage NGC 4698 candidate diagnostics

**Date:** 2026-08-12

**Script:** `scripts/phase3_background/plot_first_stage_host_candidates.py`

**Command:**
`BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python scripts/phase3_background/plot_first_stage_host_candidates.py`

### Distance

The host catalog adopts a distance of 23.933158 Mpc for NGC 4698 from its
Cosmicflows-4 (`CF4`) entry. This is approximately 78.06 million light-years. It is
the distance used to convert every angular separation in this run to projected
kiloparsecs; this summary does not add an independent distance uncertainty.

### What is plotted

The location figure shows all 2,548 Gaia sources that remain after the frozen
point-source contamination selector. The full view reaches 600 kpc, and the second
panel enlarges the central 150 kpc. The gray central circle is the temporary
0--50 kpc contamination region. Point color is Gaia G magnitude, so lower numbers
are brighter objects.

The feature-space figure shows the nine measured inputs used by the frozen
selector:

- astrometric excess noise and its Gaia-reported significance;
- Gaia BP-RP color and the BP/RP flux-excess factor;
- renormalized unit weight error (`RUWE`), a measure of disagreement with Gaia's
  ordinary single-source astrometric fit;
- the percentages of image-processing windows with multiple peaks or nearby-window
  warnings;
- the significance of nonzero parallax and proper motion; and
- explicit feature availability, because the model also records when selected
  measurements are missing.

Gray points were rejected and blue points pass the frozen score threshold. The
scatter-panel display limits are the measured 0.5th and 99.5th percentiles only to
keep extreme archive values from compressing the visible distributions. No rows
are removed from counts or saved analysis outputs. Full feature definitions and
safeguards are in `docs/gaia_selector_features.md`.

The dedicated Gaia photometric QA figure follows Figure 7 of
[Liu et al. (2020)](https://doi.org/10.3847/1538-4365/abad91). It plots Gaia G
magnitude against the raw BP/RP flux-excess factor,
`(I_BP + I_RP) / I_G`. The first panel uses Liu et al.'s displayed range, while the
second preserves the complete NGC 4698 range on a logarithmic axis. Their
flux-excess value of 1.7 is shown as a literature reference only, not as a new
BubbleTea cut. The raw factor depends on color and observing conditions, so its
threshold must not be copied without project-specific validation.

Of the 2,520 passing sources with a measured flux-excess factor, 103 (4.09%) are
below 1.7, 645 (25.60%) lie from 1.7 through 5, and 1,772 (70.32%) exceed 5. The
large high-excess population reinforces the need for later image and photometric
review; it does not by itself distinguish UCDs from galaxies, blends, or problematic
photometry.

### Are there prominent candidates?

There is no strong Gaia-only standout at this stage.

- The passing-source radial density is broadly flat beyond 50 kpc rather than
  forming a clear concentration around NGC 4698.
- Only 18 passing sources lie inside the temporary 50 kpc exclusion. There are 135
  between 50 and 150 kpc, but their density is consistent with the outer profile.
- Of the 2,548 passing sources, 2,421 (95.02%) lack Gaia's five-parameter
  astrometric solution. The corresponding fraction among rejected sources is
  16.31%. Missing astrometry is explicitly handled by the frozen model, but it
  means that many scores near one describe faint or structurally difficult Gaia
  measurements rather than uniquely convincing UCDs.
- Fifty-six passing Gaia entries have another passing entry within two arcseconds.
  Such close pairs merit source-level image review because blends, extended
  objects, and multiple Gaia detections can contribute.
- A high logistic score is not a calibrated probability that an object is a real
  UCD. It means only that its available Gaia measurements resemble the reliable
  UCD training examples more than the priority point-source contaminant examples.

Labels A--E make five examples easy to find in both figures. They were chosen by
transparent rules rather than a new scientific rank:

| Label | Reason shown | Radius (kpc) | G (mag) | Selector score | Initial reading |
| --- | --- | ---: | ---: | ---: | --- |
| A | Nearest passing source outside 50 kpc | 52.421 | 21.577 | 0.997375 | Faint; five-parameter astrometry unavailable |
| B | Highest score from 50--75 kpc | 55.930 | 21.478 | 0.999998 | Faint; five-parameter astrometry unavailable |
| C | Highest score from 75--100 kpc | 94.517 | 21.492 | 0.999995 | Faint; five-parameter astrometry unavailable |
| D | Highest score from 100--150 kpc | 146.761 | 21.544 | 0.999991 | Faint; five-parameter astrometry unavailable |
| E | Brightest passing source from 50--150 kpc | 127.149 | 16.233 | 0.974892 | Visually confirmed star by the project lead |

The project lead visually inspected example E and classified it as a star on
2026-08-12. This classification and its evidence type are stored in the review
table. Example E illustrates why a high score is insufficient: it has `RUWE = 13.123`,
proper-motion significance 48.468, and absolute-parallax significance 9.069. Those
measurements independently support its stellar classification despite the fitted
selector score. Its raw BP/RP flux-excess factor is 2.084, above Liu et al.'s 1.7
reference, so that flux-excess line alone would not have rejected it.
Examples A--D instead owe much of their high score to strong excess noise combined
with missing five-parameter astrometry and require imaging before interpretation.

### Required selector re-evaluation

The current logistic model already gives negative weight to significant nonzero
parallax and proper motion, but these are soft penalties. Example E's other Gaia
measurements outweighed those penalties. A new selector version should therefore
test a separate astrometric contradiction rule after the frozen v1 score:

- measure rejection when either available parallax significance or available
  proper-motion significance exceeds a trial boundary;
- show reliable-UCD retention and star, non-single-star, binary, and QSO rejection
  for the full measured boundary curve;
- include 3 sigma as the Liu et al. literature reference, but do not adopt it before
  measuring the project's own completeness tradeoff;
- do not treat missing parallax or proper motion as evidence of zero motion; and
- preserve `point_source_logistic_model_v1` unchanged as the reproducible baseline.

This evaluation must use the established development and validation protocol. It
cannot tune a boundary from example E or from the NGC 4698 radial excess.

The exact coordinates and Gaia source identifiers for all five examples are stored
in `data/results/background/first_stage_ngc4698_candidate_review_v1.csv`. This table
is a plot-audit aid, not a follow-up priority list.

### Artifacts

- `figures/phase3/first_stage_ngc4698_candidate_locations.png`
- `figures/phase3/first_stage_ngc4698_candidate_locations.md`
- `figures/phase3/first_stage_ngc4698_selector_feature_spaces.png`
- `figures/phase3/first_stage_ngc4698_selector_feature_spaces.md`
- `figures/phase3/first_stage_ngc4698_gaia_flux_excess_qa.png`
- `figures/phase3/first_stage_ngc4698_gaia_flux_excess_qa.md`
- `data/results/background/first_stage_ngc4698_candidate_review_v1.csv`
- `data/results/background/first_stage_ngc4698_candidate_diagnostics_v1.json`

All eight diagnostic checks pass. No selector threshold, radial boundary, or
candidate-ranking rule was changed.
<!-- preserved_source_end: docs/first_stage_ngc4698_candidate_diagnostics.md -->

<a id="record-m60_positive_control"></a>

> Dated source record: `docs/m60_positive_control.md`. Superseded instructions are history, not current policy.

<!-- preserved_source_start: docs/m60_positive_control.md -->
## M60 Positive-Control Search

### Purpose

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

### Frozen field and known objects

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

### Measured raw workload

One archive query counted sources without downloading individual rows. Within the
600 kpc circle and the frozen Gaia G-magnitude range 11.2629184723--21.7579879761,
the field contains 45,402 Gaia sources, or 3,396.2505 sources per square degree. The
query took 2.6108 seconds.

This is a raw Gaia count. It does **not** say that 45,402 sources pass the UCD
selector. Individual Gaia rows must be retrieved and evaluated locally before the
selector-passing count, radial profile, or contamination rate can be measured.

### Complete selector-version-1 result

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

### Compact Legacy Survey image pilot

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

### Proposed review flags

The following plain-language flags are approved for the complete M60 field. The
review columns and allowed values are frozen in
`data/results/radial_search/m60_positive_control_review_rules_v1.json`.

#### Measured parallax or motion

Flag a source when Gaia measures parallax or proper motion much more precisely than
zero. This is evidence for a foreground star because a distant UCD should have no
measurable parallax or sky motion. Store the measurements and their uncertainties,
not only the flag, so borderline cases remain reviewable. The earlier benchmark did
not justify a universal hard rejection boundary, so this remains a warning.

#### Gaia non-single-star catalog association

Flag a source that appears in Gaia's non-single-star tables. These tables contain
sources for which Gaia fitted orbital, acceleration, or other multiple-star behavior.
Such an association is strong evidence for a stellar system, but it remains a review
flag in this first pass.

#### QSO catalog association

Flag a source associated with a Gaia or external QSO catalog. A QSO is an active
galactic nucleus whose unresolved light can resemble a compact source. Catalog
membership is evidence, not absolute truth, and QSO flags do not remove sources from
the profile.

#### Galaxy-candidate or visibly extended source

Flag catalog associations or image structure suggesting a background galaxy. Gaia's
galaxy catalog is a candidate catalog, so it may include real UCDs or compact
star-forming regions and cannot be treated as a truth label. A clearly extended image
is useful review evidence, while a point-like image does not rule out a compact
background galaxy.

#### Compact star-forming region or young cluster

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

#### Nearby-source blend or image problem

This flag requires visual inspection of the small image. Assign it when the image
shows overlapping or nearby sources, multiple brightness peaks, asymmetric light,
a mismatch between the Gaia position and image center, saturation, diffraction
features, an image boundary, or another artifact. Ambiguous cases remain uncertain,
and an unusable image is never labeled clean.

Gaia measurements such as the multiple-peak fraction or BP/RP flux-excess factor can
prioritize a source for inspection. They are stored as a separate Gaia warning and
cannot assign this visual flag. The visual flag describes the reliability of the
image interpretation; it is not a physical classification.

### Separation of the audit and candidate shortlist

The individual Gaia rows have now been retrieved and selector version 1 has been
applied locally. Visual inspection uses two separate sets:

- a representative review sample used to measure what kinds of contaminants remain;
  and
- a promising-candidate shortlist used to identify follow-up targets.

Keeping these sets separate prevents a deliberately attractive shortlist from being
misreported as the real contamination rate. The representative audit is frozen
below. The promising shortlist will be designed separately after the audit images
are retrieved.

### Frozen representative visual audit

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

### Complete unreviewed audit images

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

### G magnitude and BP/RP flux-excess distribution

The raw Gaia BP/RP flux-excess factor is
\((I_{BP}+I_{RP})/I_G\): Gaia's BP-window flux plus RP-window flux divided by its
G-window flux. High values can reflect resolved structure, crowding, or problematic
measurements; they do not by themselves establish that a source is a galaxy.

The four-panel QA figure shows all 4,920 selector-retained sources in gray and the 400
audit sources as blue open circles. The two reliable M60 UCD controls are marked
separately. Of the complete population, 4,879 have finite positive values that can be
plotted; 397 of 400 audit sources can be plotted. Missing measurements remain in the
scientific tables.

The full-population median excess factors are 2.1663, 5.1566, 6.5307, and 6.5464 from
the innermost to outermost zone. The two reliable controls lie in the 50--150 kpc zone
at G magnitudes 20.5266 and 20.3998 and excess factors 3.1222 and 3.1636. Because the
distribution changes with radius, a single global visual boundary would obscure
field-dependent behavior. The dotted value 1.7 is the Liu et al. (2020)
sample-specific reference and is not a BubbleTea rejection rule.

The figure is `figures/phase4/m60_flux_excess_by_radial_zone_v1.png`; exact counts and
quantiles are recorded in
`data/results/radial_search/m60_positive_control_flux_excess_by_radius_v1.json`.
<!-- preserved_source_end: docs/m60_positive_control.md -->


