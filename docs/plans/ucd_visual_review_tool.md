# UCD Reference Review Workbench

## Summary

Build a local, single-reviewer web application for examining the complete reference
set of:

- 680 canonical objects classified as confirmed ultra-compact dwarf galaxies (UCDs)
  under `confirmation_rules_v1`; and
- 44 objects from the Saifollahi et al. (2021) high-probability candidate table.

The tool will combine two-scale Legacy Survey imaging with literature provenance,
Gaia measurements, host-galaxy context, Legacy Survey catalog measurements, and
external contaminant-catalog evidence. It will record auditable visual observations,
coordinate-correction proposals, and a manual decision about whether each confirmed
UCD belongs in a clean positive design reference for deriving detailed UCD selection
rules from combined Gaia and Legacy Survey measurements.

The application is a review and evidence-management system. It must never alter the
canonical literature database, silently replace an object's coordinates, invent an
unknown host, treat catalog membership as physical truth, or automatically remove an
object from the positive design reference.

## Scientific context

The current mosaic figures are useful for rapid comparison but are insufficient for
source-by-source diagnosis. Important problems include:

- the apparent source can be displaced from the literature coordinate;
- host-galaxy light or structure can dominate a small cutout;
- the source can be too faint for a reliable visual judgment;
- nearby objects or image artifacts can confuse the interpretation; and
- the expected appearance depends on host distance, because a nearby UCD may be
  visibly resolved while the same physical object would appear point-like farther
  away.

For this reason, “resolved” is an observation rather than an automatic contamination
label. The interface must display it beside host distance and physical scale. The
design-reference decision remains a separate human judgment supported by all available
evidence.

The 44 Saifollahi high-probability objects remain candidates. They will be reviewed
with the same interface but cannot enter the confirmed positive design reference.
Their output is a separate follow-up-priority pool.

## Existing data on this computer

### Canonical literature and reference cohort

The canonical literature database is:

`data/literature/database/ucd_reference_v2.db`

It contains publications, datasets, immutable literature records, canonical objects,
object-record associations, classifications, aliases, and evidence. The frozen
724-object review scope is:

`data/literature/catalogs/ucd_legacy_reference_targets_v1.csv`

The scope contract is:

`data/literature/sources/ucd_legacy_reference_contract_v1.json`

The target table includes canonical identifiers, adopted literature coordinates,
classification state, names, published host or environment strings, Gaia identifiers
reported in accepted source records, bibcodes, row locators, dataset identifiers,
catalog identifiers, and local source paths.

### Legacy Survey images

The existing compact three-color images are under:

`$BUBBLETEA_EXTERNAL_DATA/bubbletea/ucd_legacy_reference_v1/cutouts/`

With the expected environment setting, this resolves to:

`~/Dropbox/work/data/bubbletea/ucd_legacy_reference_v1/cutouts/`

Each current image is 64 by 64 pixels at 0.262 arcseconds per pixel, or 16.768
arcseconds wide. The retrieval manifest is:

`data/literature/catalogs/ucd_legacy_reference_cutouts_v1.csv`

The server returned a readable JPEG for all 724 coordinates, but 17 files are
low-color Legacy Survey viewer placeholders rather than useful sky images. The
remaining 707 files contain nonuniform image content: 663 confirmed UCDs and all 44
Saifollahi candidates. Transport success and useful image content must remain
separate states in the review application.

### Legacy Survey catalog measurements

All Legacy Survey DR10 Tractor associations within 10 arcseconds are stored in:

`data/literature/catalogs/ucd_legacy_reference_tractor_matches_v1.csv`

The per-target association audit is:

`data/literature/validation/ucd_legacy_reference_tractor_audit_v1.csv`

At least one association exists for 683 targets, including all 44 Saifollahi
candidates. The 10-arcsecond radius was adopted (2026-08-13) after the 2-arcsecond
pilot missed off-center literature coordinates, such as Hydra-UCD33. The tool must
show all nearby associations and identify the closest row without presenting it as
certainly correct.

Available measurements include coordinates, separation, fitted light-profile type,
g/r/i/z/W1/W2 fluxes and inverse variances, observed and dust-corrected magnitudes,
number of exposures, fit quality, contamination fractions, mask values, point-spread
function sizes, fitted size, ellipticity, and Sérsic index.

The Tractor profile type describes how the survey pipeline fit the light. `PSF` does
not prove that a source is a star, and an extended profile does not prove that it is a
background galaxy.

### Gaia information

The current exact-identifier catalog-membership table is:

`data/literature/catalogs/ucd_legacy_reference_gaia_membership_v1.csv`

Only 175 confirmed-object rows have one accepted Gaia identifier, representing 174
distinct Gaia sources. The current exact-identifier overlaps are:

- 0 Gaia non-single-star catalog members;
- 8 Gaia QSO-candidate catalog members; and
- 74 Gaia galaxy-candidate rows representing 73 distinct Gaia sources.

The canonical Gaia cross-match table contains the complete Gaia measurements for
these exact identifiers:

`data/literature/catalogs/canonical_gaia_dr3_crossmatch.csv`

It includes Gaia coordinates, G/BP/RP photometry, parallax, proper motion,
uncertainties, astrometric excess noise, RUWE, image-parameter diagnostics, and match
separation. Objects without an accepted identifier currently remain not testable for
exact identifier membership. The new preparation stage will retrieve diagnostic Gaia
neighbors around every literature coordinate without promoting those neighbors to
accepted counterparts.

### Host-galaxy information

The nearby-galaxy table is:

`data/galaxy_sample/galaxy_sample_ranked.csv`

It contains galaxy coordinates, adopted distance and distance source, absolute
K-band magnitude, logarithmic K-band luminosity, and related photometry. It cannot be
joined blindly to the published UCD host strings. Many UCD rows contain a cluster
name, multiple possible hosts, or no host. The application requires a separately
audited host-association register before it may calculate host separation or display
host luminosity as object-specific evidence.

The literature database also contains source-level distance values and an approved
distance-provenance review:

`data/literature/sources/host_distance_reviews.json`

Source-level cluster distance must not be presented as proof of one unique host
galaxy.

### External catalogs already downloaded

Large external catalogs are stored outside the repository under:

`~/Dropbox/work/data/bubbletea/extragalactic_reference/`

Available files include:

- Gaia DR3 morphology galaxies with Sérsic measurements;
- the Quaia G < 20 all-sky QSO catalog and its selection function; and
- a Gaia-linked clean SDSS DR16 spectroscopic galaxy and QSO catalog.

Their provenance, row counts, selection rules, paths, and SHA-256 digests are recorded
in:

`data/literature/sources/extragalactic_reference_catalogs.json`

These catalogs have different scientific roles. Gaia candidate catalogs are useful
warnings but are not independent truth. Quaia begins from Gaia QSO candidates. SDSS
spectroscopic classifications are stronger external evidence but have footprint and
targeting selection effects.

## Data preparation before application development

The data-preparation stage must finish and validate a versioned review-input bundle
before the web interface is built. Large products belong under:

`$BUBBLETEA_EXTERNAL_DATA/bubbletea/ucd_visual_review_v1/`

Repository-tracked manifests and compact tables must refer to external files through
`BUBBLETEA_EXTERNAL_DATA`; scripts must import all paths from `scripts/config.py`.

### Two Legacy Survey image scales

Keep the existing compact view and prefetch one wider view for every target, except
the 17 objects whose compact image is already a viewer-placeholder tile:

| View | Pixels | Pixel scale | Field width | Purpose |
| --- | ---: | ---: | ---: | --- |
| Compact | 64 × 64 | 0.262 arcsec/pixel | 16.768 arcsec | Central morphology and centering |
| Wide | 256 × 256 | 0.262 arcsec/pixel | 67.072 arcsec | Neighbors, host light, and local context |

Use the Legacy Survey DR10 three-color JPEG endpoint with the frozen literature
coordinate as the requested center. Reuse verified existing compact images. Record
the exact URL, coordinate, layer, dimensions, pixel scale, byte count, digest,
content type, retrieval outcome, and image-content outcome for both scales.

A valid JPEG does not prove useful imaging. Preserve at least these content states:

- `nonuniform_image_content`
- `viewer_placeholder_tile`
- `unavailable_or_non_jpeg`
- `unusable_wrong_dimensions`

Do not automatically recenter an image on a catalog source. A mismatch between the
literature coordinate and the visible source is evidence the tool is intended to
record.

### Gaia source preparation

For every target, preserve two distinct evidence paths:

1. an accepted exact Gaia source identifier from the canonical literature evidence;
2. diagnostic Gaia neighbors found by position.

Retrieve all Gaia DR3 sources within 5 arcseconds of every literature coordinate.
Five arcseconds is a diagnostic search radius, not an association rule. Retain every
neighbor and calculate its separation and position angle. Never automatically assign
the nearest neighbor as the counterpart.

For accepted identifiers and positional neighbors, retrieve:

- source identifier and ICRS coordinates;
- G, BP, and RP magnitudes and fluxes where available;
- raw BP/RP flux-excess factor;
- parallax and uncertainty;
- proper motion in both axes and uncertainties;
- the proper-motion correlation needed for the combined significance calculation;
- RUWE;
- astrometric excess noise and its significance;
- image-parameter multi-peak fraction;
- image-parameter odd-window fraction;
- duplicated-source status;
- astrometric parameters solved;
- visibility periods and observation counts where available;
- Gaia classification probabilities; and
- Gaia QSO-candidate, galaxy-candidate, and non-single-star membership.

Compute absolute parallax significance as `abs(parallax) / parallax_error` only when
the uncertainty is finite and positive. Compute the two-dimensional proper-motion
significance using the full covariance matrix, not by adding independent axis
significances. Store raw inputs beside derived values.

Query all Gaia DR3 non-single-star solution tables used by the existing benchmark.
Record which table contains a source and the published solution/model type. A source
without an accepted Gaia identifier can only have positional-neighbor NSS evidence;
it cannot be called an NSS catalog member of the UCD itself.

### External catalog preparation

Use exact Gaia identifiers where the catalog supports them. Also perform bounded
positional searches around every literature coordinate so objects lacking an
accepted Gaia identifier remain diagnosable.

Every association must record:

- catalog name and release;
- catalog source identifier;
- exact-identifier or positional-neighbor match basis;
- catalog coordinates;
- angular separation;
- class or candidate label;
- redshift and uncertainty where available;
- catalog-specific measurements relevant to morphology or classification; and
- provenance registry entry.

At minimum, integrate:

- Gaia DR3 QSO candidates;
- Gaia DR3 galaxy candidates;
- Gaia DR3 non-single-star solution tables;
- Quaia G < 20;
- Gaia morphology galaxies with Sérsic fits; and
- the local SDSS DR16 spectroscopic galaxy/QSO reference.

Exact identifier membership is stronger than a positional neighbor. The interface
and exports must never collapse them into one Boolean flag.

### Host-association register

Create a versioned host-association register with one row per canonical object and
one of these states:

- `verified_unique_host`
- `published_environment_only`
- `ambiguous_host`
- `host_unavailable`

Normalize published host names only through reviewed aliases. Do not select the
nearest galaxy automatically. For a verified unique host, preserve:

- canonical host name and aliases;
- host coordinates;
- host-table row identifier;
- adopted distance and distance source;
- absolute K-band magnitude;
- logarithmic K-band luminosity;
- literature-coordinate angular separation;
- projected separation at the adopted distance; and
- parsecs per arcsecond.

For `published_environment_only`, show the published cluster/group text and
source-level distance evidence, but do not calculate a galaxy-specific projected
separation or attach one galaxy's luminosity. For ambiguous or unavailable hosts,
leave derived host quantities missing and preserve an explanatory note.

Host assignments are scientific evidence and must be audited before the application
uses them. Any later correction needs a new register version rather than an in-place
edit without provenance.

### Review-input bundle

Produce a compact, application-ready bundle rather than having the web server scan
large FITS files or query remote services during review. The bundle must include:

- one object row per canonical object;
- all literature provenance associations;
- accepted and diagnostic Gaia sources;
- all Legacy Survey associations;
- all external-catalog associations;
- host associations;
- image manifests for both scales; and
- link templates or complete URLs.

Create a manifest containing input hashes, external file hashes, query text, match
radii, retrieval dates, row counts, software command, output hashes, validation
checks, and the review-bundle version.

## Application architecture

### Technology

Implement a localhost-only Flask application with vanilla HTML, CSS, and JavaScript.

- Add Flask through `uv`; do not use pip, conda, or another package manager.
- Bind only to `127.0.0.1` by default.
- Do not add accounts, remote authentication, cloud storage, or public deployment in
  version 1.
- Serve the prepared object bundle and cached images locally.
- Store review state in a small external SQLite database.
- Export compact CSV and JSON artifacts for version control.

The application should use a restrained observatory-console visual design: a dark
neutral background, image-dominant layout, compact evidence tables, clear typography,
high-contrast coordinate markers, and colorblind-safe status colors. Avoid decorative
animation that distracts from image diagnosis.

### Startup contract

Provide one documented command that:

- resolves external data through `BUBBLETEA_EXTERNAL_DATA`;
- validates the input manifest and required images;
- opens or creates the review database; and
- starts the server on localhost.

The server must refuse to start if the review bundle's recorded input hashes do not
match the files on disk. A command-line option may allow read-only inspection of an
older review database but must not silently migrate or rewrite it.

### Review storage

The review SQLite database belongs under:

`$BUBBLETEA_EXTERNAL_DATA/bubbletea/ucd_visual_review_v1/reviews/`

Every save creates an append-only revision. Do not update or delete earlier
revisions. Store:

- review database schema version;
- review-input bundle version and digest;
- canonical object identifier;
- UTC timestamp;
- prior revision identifier;
- all visual evidence states;
- image usability;
- design-reference or follow-up decision;
- required reason and notes;
- coordinate proposal, if any; and
- client revision used for optimistic concurrency control.

The application is designed for one reviewer, but it must still prevent two browser
tabs from silently overwriting one another. Reject a save if the submitted parent
revision is no longer current and show the newer saved revision to the user.

## User interface

### Object list and navigation

Provide a searchable, filterable object list. Search must cover:

- original and canonical names;
- canonical object identifier;
- atlas identifier;
- published host/environment text;
- verified host name;
- publication bibcode;
- Gaia source identifier; and
- Legacy Survey source identifier.

Filters must include:

- confirmed UCD or Saifollahi candidate cohort;
- complete, incomplete, or not-started review;
- host-association status;
- host-distance interval;
- image-content/usability status;
- each visual evidence state;
- Gaia QSO, galaxy, or non-single-star evidence;
- external catalog name and match basis;
- Legacy Survey fitted profile type;
- no, one, or multiple Legacy Survey associations;
- coordinate proposal status; and
- design-reference or candidate follow-up decision.

Allow sorting by object name, host name, host distance, parsecs per arcsecond, G
magnitude, Legacy Survey magnitude, host separation, image status, and review status.

Previous and next navigation must follow the current filtered and sorted list. Show
separate progress counts for confirmed UCDs and Saifollahi candidates. Never combine
candidate review completion with confirmed positive design-reference completion.

### Image inspector

Place the compact and wide Legacy Survey images side by side. Each image must support
independent zoom and pan while retaining a reset-to-fit control.

Provide overlay toggles for:

- literature-coordinate crosshair;
- accepted Gaia source;
- all diagnostic Gaia neighbors;
- closest Legacy Survey catalog source;
- alternative Legacy Survey associations;
- proposed corrected coordinate;
- field width; and
- north/east orientation.

Use different marker shapes and colors for literature, Gaia, Legacy Survey, and
proposed coordinates. Label neighbor markers with their angular separation. Include
a legend that states whether the Gaia marker is accepted by identifier or merely a
positional neighbor.

The literature coordinate remains the image center. If the apparent object is not at
the crosshair, the reviewer records `off_center`; the application must not hide the
problem by recentering the displayed image.

### Literature provenance panel

Display:

- current canonical classification and ruleset;
- confirmed or candidate cohort;
- all original names;
- all published host/environment strings;
- every accepted source-row association;
- source row locator and local data file;
- reported confirmation status;
- reported radial velocity, size, magnitude, or mass when present in the raw source
  record;
- publication title, authors, year, bibcode, DOI, and catalog identifier; and
- classification rationale and existing review-required status.

Do not flatten conflicting source measurements into an unexplained single value.
Show source-specific measurements with their provenance.

### Gaia panel

Show accepted Gaia evidence separately from diagnostic neighbors. For every displayed
Gaia source, show:

- match basis and separation;
- identifier and coordinates;
- G, BP, RP, and BP-RP;
- raw BP/RP flux-excess factor;
- parallax and absolute parallax significance;
- proper motion and combined significance;
- RUWE;
- astrometric excess noise and significance;
- image-parameter multi-peak and odd-window fractions;
- duplicated-source and astrometric-solution information; and
- Gaia QSO, galaxy, and non-single-star catalog evidence.

Define each non-obvious Gaia field in expandable plain-language help. Missing values
must be labeled unavailable, not displayed as zero.

### Host or environment panel

Always show the host-association state. For `verified_unique_host`, show host name,
coordinates, adopted distance, distance source, `M_Ks`, `log_L_K`, angular
separation, projected separation, and parsecs per arcsecond.

For a published cluster or group without one verified host, show the environment and
distance evidence but state plainly that galaxy-specific luminosity and separation
are unavailable. Never present a nearest catalog galaxy as the host unless a separate
audited register explicitly verifies it.

### Legacy Survey panel

Show every catalog association within 10 arcseconds, ordered by separation. Identify
the closest association but show an ambiguity warning whenever another source is
also within the radius.

For each association show:

- Legacy Survey identifier and coordinates;
- separation;
- primary-source status;
- fitted profile type;
- g/r/i/z/W1/W2 magnitudes and uncertainties where valid;
- number of observations;
- per-band fit quality;
- flux contamination, masked fraction, and fraction of model inside the blob;
- mask and fit flags with decoded plain-language definitions;
- point-spread function size;
- fitted radius and ellipticity; and
- Sérsic index and uncertainty.

Raw values must remain available even when the interface summarizes them as warnings.

### External-catalog panel

Group evidence by catalog. For each result show catalog role, source identifier,
class/candidate label, redshift where available, exact-identifier versus positional
match basis, and separation.

Use explicit wording such as “Gaia galaxy candidate,” “Quaia QSO candidate,” “SDSS
spectroscopic galaxy,” or “Gaia positional neighbor with an NSS solution.” Do not use
a generic “contaminant” label that erases the evidence type.

### External links

Include links to:

- Legacy Survey viewer centered on the literature coordinate;
- Legacy Survey viewer centered on a proposed coordinate when present;
- Gaia Archive source page or search for accepted and neighboring source IDs;
- SIMBAD coordinate and name searches;
- NED coordinate and name searches;
- ADS abstract pages;
- DOI landing pages; and
- local reference files and source packages.

Links should open in a new tab and display the destination name before navigation.

## Review model

### Four-state visual evidence

Use a four-state segmented control for each visual observation:

- `not_reviewed`
- `yes`
- `no`
- `uncertain`

Require these seven observations for every usable image:

1. `resolved`
2. `off_center`
3. `close_to_host_light`
4. `too_faint_to_judge`
5. `blend_or_nearby_source`
6. `image_artifact`
7. `star_forming_or_young_cluster_appearance`

Definitions:

- **Resolved:** The central source appears broader or structurally extended relative
  to nearby point sources. This is not automatically negative; interpretation
  depends on distance and image quality.
- **Off-center:** The likely intended object is visibly displaced from the literature
  coordinate crosshair.
- **Close to host light:** Host-galaxy light, a galaxy halo, dust, or visible host
  substructure materially affects the cutout. This is distinct from a measured
  projected host separation.
- **Too faint to judge:** The source is present weakly or not detected well enough to
  decide its morphology or centering reliably.
- **Blend or nearby source:** A neighbor overlaps the source or is close enough to
  compromise visual or catalog measurements.
- **Image artifact:** Saturation, diffraction, missing coverage, seams, unusual color
  patches, placeholder output, or another imaging problem compromises interpretation.
- **Star-forming or young-cluster appearance:** The source appears associated with
  visible star-forming structure or irregular compact emission. Color alone cannot
  assign this observation.

Provide an image-usability field with:

- `not_reviewed`
- `usable`
- `partly_usable`
- `unusable`

An unusable image may complete through an explicit unusable-image path. In that path,
visual flags may remain `not_reviewed`; the final design-reference decision must be `hold`,
and the reviewer must provide a reason.

### Notes

Provide:

- one concise evidence note associated with visual flags;
- one optional general comment; and
- a required decision reason for `exclude`, `hold`, `deprioritize`, or candidate
  `hold`.

The interface should encourage factual descriptions such as “central source is 1.2
arcseconds east of the literature crosshair” rather than unsupported physical
conclusions.

### Coordinate-correction proposals

When `off_center` is `yes` or `uncertain`, require one of:

- select an accepted or diagnostic Gaia source;
- select a Legacy Survey association;
- enter a manual ICRS RA and Dec; or
- state that no corrected coordinate can yet be proposed.

Store:

- proposed RA and Dec;
- proposal source type and source identifier;
- separation from the literature coordinate;
- supporting note;
- UTC time; and
- review revision identifier.

A proposal is exported for a separate provenance audit. It must never update the
canonical object or trigger automatic image recentering.

### Confirmed-UCD design-reference decision

For confirmed UCDs, record one manual state:

- `not_reviewed`
- `include`
- `exclude`
- `hold`

`exclude` and `hold` require a reason. `include` may coexist with a positive visual
flag, because a nearby real UCD can be resolved or close to host light. In that case,
show a confirmation warning so inclusion is intentional.

An object cannot enter the clean design-reference export unless:

- its image is usable or partly usable;
- all seven visual observations have been answered;
- any off-center evidence has a completed coordinate-proposal response;
- its design-reference decision is `include`; and
- the current review revision passes server-side validation.

The tool does not automatically translate any single catalog flag into exclusion.

### Candidate follow-up decision

For Saifollahi candidates, use a separate state:

- `not_reviewed`
- `prioritize`
- `standard`
- `deprioritize`
- `hold`

Candidates cannot enter the confirmed positive design-reference export. Their review output
is a follow-up pool with all provenance and evidence retained.

### Completion rules

A usable-image review is complete only when:

- image usability is answered;
- all seven visual observations are answered;
- an off-center proposal response is complete when required;
- the cohort-appropriate final decision is answered; and
- a required reason is present.

Review completion and design-reference eligibility are different. An excluded or held object
can have a complete review.

## Local API

Provide these minimum routes:

- `GET /api/summary`
- `GET /api/objects`
- `GET /api/objects/{canonical_object_id}`
- `GET /api/objects/{canonical_object_id}/history`
- `GET /api/images/{canonical_object_id}/{compact|wide}`
- `POST /api/objects/{canonical_object_id}/reviews`
- `POST /api/export`

`GET /api/objects` must support filtering, sorting, pagination, and stable navigation.
The object-detail response must group provenance, Gaia, host, Legacy Survey, external
catalogs, images, links, and current review state rather than returning one ambiguous
flat namespace.

The save endpoint must validate:

- allowed four-state values;
- allowed image-usability values;
- cohort-specific final decisions;
- required reasons;
- required coordinate-proposal response;
- candidate prohibition from confirmed design-reference inclusion;
- parent revision currency; and
- canonical object membership in the frozen input bundle.

Return structured validation errors that the interface can place beside the relevant
field.

## User interaction details

Provide:

- explicit Save and Save-and-next buttons;
- `Ctrl+S` or `Cmd+S` to save;
- previous/next keyboard shortcuts that do not fire while editing text;
- an unsaved-change warning before navigation or tab closure;
- a visible saved timestamp and revision identifier;
- a history drawer showing every prior revision; and
- a conflict dialog when another tab has saved a newer revision.

Do not autosave individual flag clicks. A review is a coherent revision and should be
saved explicitly after the reviewer checks the evidence.

## Versioned exports

Exports must be generated from a transactionally consistent snapshot of the review
database. Write compact repository-ready CSV and JSON artifacts plus a manifest.

Required exports:

1. current review state for all 724 objects;
2. complete append-only revision history;
3. included confirmed-UCD positive design reference;
4. excluded confirmed UCDs with reasons;
5. held confirmed UCDs with reasons;
6. Saifollahi candidate follow-up pool;
7. coordinate-correction proposals;
8. summary counts and cross-tabulations; and
9. export manifest with input/output hashes and validation checks.

Summary tables must report confirmed UCDs and candidates separately and include
counts by:

- review completion;
- image usability;
- each visual observation;
- design-reference or follow-up decision;
- host-association state and distance interval;
- Gaia catalog evidence;
- external catalog and match basis;
- Legacy Survey profile type; and
- coordinate-proposal status.

The clean positive design-reference export must contain only confirmed objects with current
`include` decisions that satisfy every eligibility rule. It must link back to the
review revision and all source evidence; it must not become a replacement canonical
literature table.

## Validation fixtures

Create deterministic fixtures representing at least:

1. an exact Gaia identifier with QSO and galaxy-candidate overlap;
2. an object without an accepted Gaia identifier but with positional neighbors;
3. multiple Legacy Survey associations;
4. a viewer placeholder or unusable image;
5. a nearby verified host;
6. a cluster-only published environment;
7. an unknown host;
8. a visibly resolved nearby UCD;
9. an off-center source with a coordinate proposal;
10. a Saifollahi candidate;
11. included, excluded, and held confirmed objects; and
12. conflicting saves from two browser tabs.

Fixtures must use synthetic or explicitly frozen small data so tests do not query
remote services.

## Acceptance criteria

### Scientific integrity

- The canonical literature database and frozen input tables remain byte-identical
  during review.
- Exact-identifier and positional-neighbor evidence cannot be confused in the UI or
  exports.
- Unknown or ambiguous hosts never acquire calculated host luminosity or projected
  separation.
- Candidate status never becomes confirmed status through review.
- Saifollahi candidates never enter the confirmed positive design-reference export.
- Coordinate proposals appear only as proposals and never change canonical
  coordinates.
- Catalog membership and fitted profile types remain evidence, not automatic truth
  labels.
- Incomplete reviews cannot enter the clean positive design-reference export.

### Image and geometry validation

- Every image endpoint serves the file recorded for the requested object and scale.
- Image dimensions and digests match the image manifest.
- Literature coordinates map to the image center within numerical rendering
  tolerance.
- Gaia, Legacy Survey, and proposal overlays reproduce recorded separations and
  position angles using the documented pixel transformation.
- Placeholder and unavailable images are never labeled clean automatically.

### Persistence and API behavior

- Restarting the server preserves every saved revision.
- Saving creates a new revision and retains the previous one.
- A stale parent revision produces a conflict rather than overwriting new work.
- Server-side validation rejects invalid flag states, incomplete required evidence,
  or cohort-incompatible final decisions.
- Exporting does not change review state.

### Interface behavior

- Search, filters, sorting, and filtered previous/next navigation work on all 724
  objects.
- Both image scales load and overlays can be toggled independently.
- Zoom, pan, reset, keyboard save, history, unsaved-change warnings, and external
  links work in the supported browser.
- Missing measurements display as unavailable rather than zero.
- Confirmed and candidate progress remain visibly separate.

### Reproducibility and code quality

- Every generated data product has a manifest with provenance and hashes.
- Data-preparation and validation scripts are standalone and use paths from
  `scripts/config.py`.
- All dependencies are managed through `uv`.
- Ruff, pre-commit, data validation, API checks, export checks, and
  `git diff --check` pass.
- No file larger than 10 MB, database file, FITS file, or downloaded image cache is
  committed.

### Measured performance

Benchmark rather than estimate:

- startup and manifest-validation time;
- object-list response time;
- object-detail response time;
- review-save latency;
- filtered navigation latency; and
- full export time.

Record the commands, hardware context, full 724-object measurements, and acceptance
thresholds chosen from the measured pilot. Do not claim responsiveness before it has
been measured.

## Delivery sequence

1. Link this specification from `docs/SPEC.md` and `docs/todo.md` when implementation
   begins.
2. Checkpoint the completed UCD Legacy Survey reference side quest without merging
   unless the project lead explicitly approves a merge.
3. Create a new feature branch for the review workbench.
4. Review three to five similar repository scripts before adding new preparation or
   validation code.
5. Freeze schemas and provenance contracts for enriched data and review storage.
6. Build the host-association register and stop for scientific review of ambiguous
   host groups.
7. Retrieve and validate the wide images, Gaia neighbors, full Gaia measurements,
   and external-catalog associations.
8. Build and validate the compact review-input bundle.
9. Implement the append-only review database and local API.
10. Implement the image-dominant interface and evidence panels.
11. Run automated validation and a browser smoke test.
12. Conduct a 12-object pilot spanning all validation fixtures.
13. Stop for project-lead review of the interface, visual definitions, host handling,
    and exports before opening all 724 objects for production review.
14. After review approval, freeze the production review version and begin the full
    source-by-source assessment.

## Frozen assumptions and decisions

- Version 1 is local, single-user, and bound to localhost.
- The application uses Flask with plain HTML, CSS, and JavaScript.
- Review state is stored in an external SQLite database with append-only history.
- No reviewer identity is recorded; the workbench is a single local user.
- Image scales are 16.768 and 67.072 arcseconds at 0.262 arcseconds per pixel.
- Visual observations use `not_reviewed`, `yes`, `no`, and `uncertain`.
- The required visual set has seven observations.
- Host-derived properties require a separately verified unique host.
- Exact identifiers and positional neighbors are separate evidence types.
- Coordinate corrections are proposals for later provenance audit.
- Design-reference membership is manual and separate from evidence flags.
- Only confirmed UCDs can enter the positive design reference.
- Saifollahi candidates receive a separate follow-up-priority decision.
- The clean positive design reference supports deriving detailed UCD selection
  rules from combined Gaia and Legacy Survey measurements; it is not model training.
- This workbench reviews only the literature confirmed UCDs and high-probability
  candidates. The later candidate-selection review tool is a separate deliverable.
- The 17 known viewer-placeholder objects receive only the compact image; the wide
  image is not retrieved for them.
- Host-association policy (2026-08-13): a single published galaxy name resolves to
  `verified_unique_host`; a published cluster/group name resolves to
  `published_environment_only` and adopts the cluster/group distance; a galaxy pair
  (`X/Y`) resolves to the named group; an empty host field resolves from the source
  publication's documented environment rather than remaining unknown.
- The 13 Voggel 2020 candidate stripped-nucleus / luminous-globular-cluster objects
  are excluded from the confirmed positive design reference (see
  `data/literature/sources/confirmed_ucd_design_reference_exclusions_v1.json`).
- Adopted cluster distances: Virgo cluster 16.5 Mpc, Centaurus cluster 43.0 Mpc,
  Hydra I (NGC 3311) 50.7 Mpc, NGC 5128 3.8 Mpc. The register is
  `data/literature/catalogs/host_association_register_v1.csv`.
- A complete review requires all applicable visual evidence and a final decision.
- No review action changes literature classification, canonical coordinates, host
  identity, selector output, radial profiles, or source provenance.
