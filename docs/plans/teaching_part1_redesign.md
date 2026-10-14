# A Galaxy in Disguise: Part I implementation plan

**Date:** 2026-10-14  
**Status:** Part I implemented and technically validated; final instructor review pending
**Task:** BT-033; separate teaching work on `teaching_ucd_course_20261012`

[Requirements](../SPEC.md#teaching-redesign-interview-requested-2026-10-14) ·
[Course guide](../teaching/README.md) · [Task register](../todo.md) ·
[Existing data provenance](../../data/teaching/README.md)

## 1. Outcome and boundaries

Build **one self-contained HTML file** for Part I of a semester-long undergraduate
project. It contains motivation, about 30 minutes of core reading, illustrated Gaia
background, labeled examples, three practical tasks, and save/restore/submission
controls. Students can spend longer on the investigations. No coding, installation,
local server, account, or internet connection is required for the core activity.
Online archive, survey, and literature exploration is encouraged but optional.

Implementation checkpoint, 2026-10-14: the full lesson is built, source evidence and
all 74 cutouts are reviewed, and complete-page offline/performance/scoring tests
pass. See the [development record](../development/teaching_materials.md) and
[instructor guide](../teaching/instructor_notes.md). The remaining gate is final
instructor review of the actual reading, workload, and treatment of uncertainty.
The earlier six-object HTML/PDF is **version 1**, not this redesigned lesson.

The audience already knows coordinates, magnitude, and color. Teach the additional
background needed to investigate real observations. Replace most reading-comprehension
questions with recorded decisions, source checks, and selection experiments.
Allow and encourage LLM assistance with a brief disclosure and source verification.

Part II and later parts will address membership and new searches. Do not expand
this implementation into choosing final discovery hosts, changing the scientific
selector, modifying canonical classifications, or deploying the research workbench.
The new student deliverable is HTML; the existing PDF remains a clearly labeled
previous-version resource until a redesigned print companion is separately needed.

## 2. Agreed learning sequence

| Section | Student activity | Saved evidence |
| --- | --- | --- |
| Motivation and background | Read a short scientific introduction and explore Gaia illustrations | No compulsory comprehension quiz |
| Labeled examples | Compare known UCDs, stars, and quasars at similar apparent brightness | Optional exploration; not graded answers |
| Task 1: investigate objects | Classify approximately 30 individual objects without correctness feedback | Required class or uncertain; optional confidence, evidence note/basis, and citation |
| Task 2: design selection rules | Explore a much larger star-rich catalog, adjust cuts, evaluate repeatedly | Attempts with counts, purity, completeness, and F1; one final selection with two explanations |
| Task 3: establishing membership | Answer one open question | Free text, carried forward to Part II |
| Submission | Export all work and a brief LLM-use disclosure | Versioned JSON and readable text report |

The working Task 1 composition is 10 UCDs, 10 stars, and 10 quasars. This is an
instructor preparation target, not a student-visible answer distribution. Prefer
secure reference classifications. Unconfirmed candidates may be useful teaching
objects, but cannot silently become definite graded UCD answers.

Task 2 deliberately has many more stars than UCDs or quasars. Start the build-size
experiment with **20,000 distinct stars**, the eligible UCD reference objects,
spectroscopic quasars, and the full eligible development candidate pool including
fainter objects. Final counts depend on exclusions and the finished HTML tests;
20,000 is a starting allocation, not a measured final sample size or sky abundance.

## 3. Existing data and measured feasibility

### Local source inventory, inspected 2026-10-14

| Source | Measured contents | Planned use and limitations |
| --- | --- | --- |
| `data/literature/benchmarks/gaia_selector_development_features_v3.csv` | 3,136 rows: 843 literature UCD-related records, 403 SDSS quasars, 638 SDSS galaxies, 1,125 Gaia non-single-star records, 127 H II-region records | Start with the development UCD and spectroscopic-QSO cohorts; do not turn every literature row into a positive label |
| Same file, literature subset | 593 candidate-state rows; 146 confirmed, primary-label-eligible rows before the later source exclusion | Candidate population is unscored; confirmed labels require the later decisions below |
| `data/literature/sources/confirmed_ucd_design_reference_exclusions_v1.json` | 13 excluded canonical objects, all present in those 146 rows | Their paper reports candidate stripped nuclei/luminous globular clusters, not confirmed UCDs; retain provenance, exclude from scored UCDs |
| Same development subset after those 13 exclusions | 133 rows; 11 have G < 19, 17 have G < 19.5, 25 have G < 20 | Provisional pool, before classroom role assignment and image/evidence audit; not 133 verified teaching objects |
| `data/literature/sources/ucd_reliability_reviews.json` | Five reliability exclusions, including B409; none overlap the remaining 133 | Apply explicitly nevertheless; future catalog versions must not reintroduce them |
| `data/literature/benchmarks/spectroscopic_stellar_reference_matches_v3.csv` | 438 matched spectroscopic stars | Existing small comparison set; not the limit on available stars |
| External spectroscopic stellar parent, below | 79,369 rows and unique string Gaia identifiers; all spectroscopic class STAR; G spans 11.280893325805664–21.72075653076172 | Large star-rich starting pool, not an unbiased all-sky sample or a catalog of established single stars |
| `data/literature/catalogs/ucd_legacy_reference_targets_v1.csv` and `ucd_legacy_reference_gaia_membership_v1.csv` | 724 rows in each | Names, associations, provenance, candidate tiers, and prior review context; DR10 image availability does not establish DR11 availability |
| `data/teaching/ucd_course_packet_v1.json` | Six objects and twelve embedded-image source records | Reuse verified provenance and suitable demonstration objects, not its entire instructional design |

The external parent is at
`$BUBBLETEA_EXTERNAL_DATA/bubbletea/stellar_reference/sdss_dr16/gaia_linked_clean_spectroscopic_stars_random_0_10_v2.fits`.
On this computer, set `BUBBLETEA_EXTERNAL_DATA="$HOME/Dropbox/work/data"`.
Use `STELLAR_REFERENCE_DIR` from `scripts/config.py`, not a hardcoded home directory.
The file is 14,774,400 bytes; SHA-256:
`c48b5af9e482fee1fc55c7de4c762962a576455d8b4d5e912b5266e2d98d8fe0`.
Its query/provenance is recorded in
`data/literature/benchmarks/spectroscopic_stellar_reference_manifest_v3.json` and
`scripts/phase1_literature/build_spectroscopic_stellar_reference.py`.

Missing values must remain visible: the stellar parent has 74,868 finite parallax,
proper-motion-component, and RUWE measurements, and 78,876 finite flux-excess
measurements. Missing astrometry is not zero motion or a zero-significance result.

The bright-object constraint needs care. There are only 11 G < 19 UCDs in this
provisional development pool, before reserving labeled examples. Rank by brightness,
host distance, source reliability, and usable DR11 images; do not impose an
unsupported G < 19 requirement or promise ten such objects. A somewhat fainter
but well-documented object is preferable to an unreliable bright one. Return to
the instructor only if ten defensible UCD assignments cannot be assembled after
checking those alternatives.

### Preliminary browser test, not finished-application validation

Read the real stellar FITS table without changing it. Serialize exact string
identifiers plus 18 unrounded numeric fields as compact JSON row arrays, converting
non-finite values to `null`: RA, Dec, G, BP, RP, flux excess, excess noise, excess-noise
significance, RUWE, parallax/error, both proper motions/errors, their correlation,
and both image-window fractions. Use the first N real rows for a size test only;
the final scientific sampling order will be different.

In installed Chrome 156.0.8078.12, headless, offline, on macOS 15.7.4 arm64, with
fourfold CPU throttling, measure JSON parsing, a simple eight-condition linear
filter, and four 800-by-450 canvas plots. The filter requires G < 20 and either a
missing or nonnegative value for each of flux excess, excess noise, excess-noise
significance, RUWE, parallax error, and the two proper-motion errors. These bounds
are only a repeatable processing workload. Draw one two-pixel square per finite
coordinate pair. The plots pair G/excess, G/excess noise, BP/RP magnitudes, and
parallax/RA proper motion; these are engineering workloads, not proposed student
cuts. Discard one warm-up iteration and report the median of five filter/drawing
iterations. Browser version and throttling do not emulate Windows hardware.

| Real rows | JSON bytes | Parse, ms | Filter median, ms | Four-canvas drawing-command median, ms |
| ---: | ---: | ---: | ---: | ---: |
| 1,000 | 316,515 | 2.6 | 1.1 | 1.7 |
| 10,000 | 3,139,186 | 25.8 | 1.3 | 15.2 |
| 20,000 | 6,290,883 | 52.4 | 2.1 | 30.7 |
| 50,000 | 15,705,849 | 120.6 | 9.3 | 87.8 |
| 79,369 | 24,925,730 | 194.1 | 13.2 | 212.6 |

These times exclude complete page startup, image decoding, final screen painting,
hover interactions, answer handling, and accessibility controls. They demonstrate
that simple catalog operations are feasible, not that the lesson already meets
its acceptance tests. The stronger present constraint is the repository rule
against committing files over 10 MB. Require the final single HTML to be below
10,000,000 bytes. Measure its actual size, including embedded-image overhead;
reduce only the deterministic stellar sample if needed. Do not round away scientific
information, remove uncertain values, or silently plot fewer points to meet a budget.

## 4. Scientific content and illustrations

### Motivation

Explain UCDs as compact stellar systems spanning an imperfect boundary between
massive star clusters and small galaxies. Some are candidate remnants of stripped
galactic nuclei; do not claim that all share that origin. The accessible title
is not a claim that every UCD has an unambiguous galaxy classification.

Explain that discoveries and searches have been concentrated in dense environments
and that the census remains incomplete and selection-dependent. There is room to
search around less-studied massive galaxies, disk hosts, and in lower-density
environments. Do not invent a present-day global count, assert that every massive
galaxy must host a detectable UCD, or equate an isolated host with a hostless UCD.
Disk-host systems already exist: acknowledge SUCD1 near the Sombrero galaxy.

Useful primary sources for the authoring pass:

- [Saifollahi et al., Fornax outskirts](https://arxiv.org/abs/2104.00004): distinguish
  new candidates from confirmed objects and use its search-footprint discussion.
- [Liu et al., NGVS UCD catalog](https://arxiv.org/abs/2007.15275),
  DOI `10.3847/1538-4365/abad91`: candidate richness, environment, and selection;
  its Figure 7 motivates the G-versus-flux-excess view, not a pre-taught cut.
- [Hau et al., SUCD1](https://arxiv.org/abs/0901.1693): a counterexample to a claim
  that no disk galaxy is known to host a UCD.

### Background and Gaia

Cover angular versus physical size; apparent versus intrinsic brightness;
uncertainty and significance; parallax and two-component proper motion; measurements
versus source interpretations; matching catalogs at different epochs; missing data;
and what images can and cannot resolve. Reinforce existing knowledge briefly.

Use an offline SVG or simple native animation of Gaia scanning across a small
detector window, showing repeated observations at different orientations. Support
pause, reduced-motion preferences, and a static explanation. Adapt from official
mission documentation with a caption, source, and an explicit schematic label:
[ESA source detection](https://blogs.esa.int/gaia/2014/04/03/detecting-sources/) and
[ESA scanning animation](https://www.esa.int/ESA_Multimedia/Videos/2013/06/Gaia_scanning_the_sky).
Check reuse terms before embedding third-party imagery; do not depend on a remote
video or iframe. An original, credited schematic is the simpler reliable default.

Explain why compact peaks of light can be recorded without determining whether the
object is a Galactic star. Distinguish pixel sampling, direction-dependent angular
resolution, close-pair catalog recovery, and astrometric precision. Never offer one
universal Gaia resolution or a size threshold guaranteeing UCD detection. Reuse the
verified primary-source resolution references in the existing
[background guide](../teaching/concepts.md), checking definitions during rewriting.

Present neutral definitions, units, and missing-value meanings for each control.
Do not label a feature as useful/useless, give a preferred cut direction, or preload
the research selector. Link the
[official Gaia DR3 source data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html)
and the repository [feature definitions](../methods/gaia_features.md) as optional
deeper reading. Optional instructor-oriented repository pages must not be required
for understanding the offline lesson.

### Labeled examples

Begin with M60-UCD1 and/or M59-UCD3 and magnitude-comparable, independently classified
star and QSO examples. Select more than one comparison if a single easy star would
suggest a false universal rule. Show the same measurement layout used in Task 1,
two image scales, exact identifiers, units/errors, and source links. Keep example
objects disjoint from both tasks so the answer is not copied by recognizing an image.
Use the existing tool guide for optional Gaia Archive, Visualization, Aladin, and
Legacy Survey exploration; verify changed interface instructions rather than
claiming a Windows rehearsal.

## 5. Teaching catalog construction and evidence audit

1. Freeze input paths, hashes, query dates, source releases, and the list of approved
   exclusions. Read Gaia identifiers as strings, including when loading FITS/CSV;
   never pass through floating-point identifiers. Preserve canonical object IDs and
   original publication/source-row provenance in the instructor manifest.
2. Apply current canonical/source-association decisions and the reliability and
   13-object source exclusions. Keep unresolved identities and tier conflicts out
   of scored labels. A published UCD rejected without an independent stellar/QSO
   classification is not automatically a negative example of either class.
3. Use the scientific **development** data, not the reserved scientific validation
   sample. Exclude reserved IDs through existing split metadata without inspecting
   their measurements or labels for teaching selection. Include all eligible
   development candidates down to their available faint limits, not only Task 1's
   bright subset. Objects without Gaia measurements cannot be fabricated into Gaia
   plots; record them and other exclusions in an accounting table.
4. Obtain secure stars and quasars from independent spectroscopy. The existing SDSS
   source queries use primary spectra, reliable-redshift flags, class STAR/QSO,
   and deterministic sampling. Preserve the matching separation and original record.
   A Gaia QSO-candidate flag alone is not secure QSO truth. Spectroscopic STAR does
   not establish singleness; retain ordinary binaries/non-single stars if otherwise
   eligible, with independent evidence flags in the instructor metadata.
5. Select Task 2 stars by a fixed documented hash of the string Gaia identifier
   within the lesson's measured magnitude coverage, not by proper-motion, parallax,
   color, RUWE, or flux-excess cuts. Record the magnitude domain and test overlap
   among populations. Preserve difficult faint and low-motion stars. SDSS targeting,
   spectroscopic success, and sky footprint still bias this parent; state that plainly.
6. Reserve labeled examples and Task 1 before Task 2 sampling. Deduplicate by Gaia
   source and canonical object; stop for conflicting reference classes. Do not
   replicate sources to increase class counts. Do not expose Task 1 reference labels
   by including those same objects among Task 2's feedback labels.
7. Audit Task 1 object by object: paper/spectrum identity, current reliability,
   coordinates and epoch, plausible crossmatch, DR11 centering, close/context image
   quality, visibility, supplied measurements, and an evidence path the student can
   actually follow. Keep an instructor-only audit row with pass/fail and a reason.
   Independently work through the student view with its reference label hidden.
8. Prefer secure, recognizable cases for Task 1. No promise that Gaia and an optical
   thumbnail uniquely determine every class is scientifically defensible. Supply
   sufficient observational evidence, allow external corroboration, and retain
   `uncertain` as a valid evidence-based response. Replace ambiguous graded objects;
   if a particularly valuable high-probability candidate remains, grade its reasoning
   manually and mark the instructor key as unresolved, not definitely correct UCD.

Use `scripts/teaching/prepare_teaching_data.py` and the existing reference preparation
scripts as patterns. Extend the teaching preparation code rather than rebuilding
research pipelines. Download any new Gaia rows or DR11 images to a new versioned
teaching cache under the configured external directory. Probe one object per class
first, then acquire serially with retry/backoff and preserved failures. Use actual
DR11 image content, not successful HTTP status, to establish coverage; record layer,
requested center, scale, dimensions, retrieval date, URL, and digest. A small
center-marker toggle helps students detect wrong associations without obscuring a
compact source. Record angular orientation and field size.

No all-sky download is needed. If the existing 403 development QSOs cannot supply
the required bright, imaged comparisons, extend the documented SDSS spectroscopic
query in `build_validation_benchmark.py` over a disjoint deterministic interval,
save query and results externally, and audit new associations before use. Do not
substitute photometric QSO candidates silently. Existing known-example images can
be reused only when their checked release, center, and content remain suitable.

## 6. Task 1 interface and grading

Use neutral object codes in a compact navigator and one detail panel with images,
measurement table, optional links, and response fields. Preserve RA/Dec and exact
Gaia identifiers for open investigation. Do not put class-bearing names in display
titles, image captions, alternative text, download filenames, or hidden Task 1
data. Reference labels and the audit/key remain in a separate instructor artifact.
External links may legitimately reveal a published identity: this is allowed.

Response fields: class (`ucd`, `star`, `qso`, `uncertain`, or unanswered), confidence
(`low`, `medium`, `high`, or unanswered), one short evidence note, evidence basis
(`supplied_observations`, `external_record`, or `both`), and a source URL or citation.
Under the revised 2026-10-14 request, only classification is mandatory. Use
button-style radio choices for class, confidence, and evidence basis. All other
fields are optional, including citations. Show Galactic longitude/latitude on the
object cards, computed from the saved ICRS positions; do not use the coordinate
system as a suggested selection shortcut. Keep the per-object form compact.

Layout follow-up, 2026-10-14: measurements are above the review area in two columns
on wider screens. The close/context images sit beside a compact response panel
containing the three choice groups, evidence, citation, and navigation. The image
column stays visible while scrolling the response panel on desktop-sized windows.
Previous/next brings the new images and classification back into view without
returning to the long measurements. Narrow screens stack images before responses;
the measurements become one column on the narrowest screens. Preserve the example
cards, all measurements, classification options, and the existing answer schema.

Show progress but no correctness, accuracy, class-colored symbols, or answer
distribution. Grade against the separate reference key plus the evidence notes;
do not automatically equate a cautious, justified uncertain answer with failure.
Record questionable reference cases for instructor review. Never promote student
responses into canonical research labels.

## 7. Task 2 measurements, controls, and feedback

### Data presentation and adjustable rules

Use unlabeled points initially. Required view: **G magnitude versus
(I_BP + I_RP) / I_G**, the Gaia BP/RP flux-excess factor. Add G versus astrometric
excess noise, BP−RP versus flux excess, and parallax significance versus combined
proper-motion significance. Explain log axes and non-plottable values. A source
missing a plotted coordinate remains in the catalog, selection, and denominator;
show each panel's omitted count. Do not silently replace missing values with zero.

Expose neutral, optional lower/upper interval controls for G, BP−RP, flux excess,
astrometric excess noise, its reported significance, RUWE, absolute-parallax
significance, combined proper-motion significance, and the two image-window
fractions. Keep the more technical fields in an expandable section. The existing
frozen logistic model uses most of these quantities; this exercise does **not**
ship its coefficients, predictions, labels-as-features, or optimized thresholds.
Do not promise that a particular field is unimportant in advance. The instructor
audit should establish which controls add little information in this actual sample;
do not invent random or identifier-based decoys to force that outcome.

All cuts start disabled; their displayed domains come from measured data. Enabled
intervals combine with **AND**: a source must satisfy every active rule. Inclusive
endpoints and units are explicit. One clearly labeled missing-data control chooses
whether unavailable values pass active rules; start with keep, report their count,
and save this policy with every attempt. A log-spaced slider is only an input aid:
store and apply the corresponding physical-unit boundary. Provide numeric inputs,
keyboard access, reset, and visible pending changes. Moving a slider does not
replace the last evaluated result until the student presses **Evaluate selection**.

Derived features must match the verified definitions:

- BP−RP is the difference between the two magnitudes, not a flux ratio.
- Absolute-parallax significance is `abs(parallax) / parallax_error`, requiring
  finite values and a strictly positive error. It is a comparison with zero, not
  a posterior probability or a parallax-based UCD distance.
- For proper motion, set `u = pmra / pmra_error`, `v = pmdec / pmdec_error`, and
  `rho = pmra_pmdec_corr`; use
  `sqrt((u*u + v*v - 2*rho*u*v) / (1-rho*rho))` when errors are positive,
  all inputs finite, and `abs(rho) < 1`. Otherwise report unavailable. It is a
  two-dimensional error-scaled distance from zero, not a one-dimensional Gaussian
  tail probability. Keep the full formula in optional mathematical detail.

### Feedback and one final selection (revised 2026-10-14)

After evaluation, highlight selected points without automatically revealing each
point's class. Show aggregate counts for selected secure UCDs, stars, quasars,
unconfirmed candidates, and selected objects with missing active measurements.

Let `true_positive` be selected securely classified UCDs, `false_positive` be
selected spectroscopic stars plus quasars, and `total_ucd` be **all** eligible secure
UCDs in the fixed Task 2 reference sample, including rows with missing features:

- `purity = true_positive / (true_positive + false_positive)`;
- `completeness = true_positive / total_ucd`;
- `f1 = 2 * true_positive / (total_ucd + true_positive + false_positive)`.

An empty scored selection has undefined purity, not 100%; completeness is zero
when a nonempty UCD reference sample exists; F1 is also zero. Guard all zero
denominators. Unconfirmed candidates enter none of these formulas. Label purity as **reference-subset purity**,
not the known purity of the entire selected list: show unknown selected candidates
alongside it. Explain that these metrics describe this constructed catalog, not
discovery success or an unbiased estimate for a new galaxy field.

Keep evaluated attempts with their actual rules, counts, metrics, and order. Allow
repeated attempts; avoid logging every slider movement. Students optimize F1, the
harmonic mean of purity and completeness, and designate **one final attempt**.
Require its answers to "Why do you think this works?" and "How do you think this
selection can be improved?" Do not impose a numerical pass threshold. This
supersedes the earlier two-list design. Retain range controls, not scoring weights;
ROC AUC is optional background, not the objective for a binary selection. The
instructor-only bounded trial tests achievable F1 and all/none/one-object controls
without placing optimized cuts in the student page or claiming held-out validity.

## 8. Task 3 and responsible assistance

Use exactly one prompt:

> You find a possible UCD close to a massive galaxy on the sky. How would you
> investigate whether it is physically associated with that galaxy?

One free-text box; no hint panel, worked solution, suggested answer, or automatic
score. Do not inadvertently give its worked answer in the background or concluding
section. Save it for the instructor to use at the start of Part II.

At submission, ask whether an LLM was used and, if so, for a brief description of
its contribution and what the student checked. Do not request private chat logs
or treat tool use as misconduct. Assess observational reasoning and reproducible
work, not whether prose could have been generated by a model.

## 9. Single-file architecture and answer records

Reuse `scripts/teaching/assets/activity.html`, `.css`, and `.js`, the builder,
preparation code, and validation structure. Inspect those existing files before
implementation. Define new paths in `scripts/config.py`; own new names use
`snake_case`. Keep the paper/green editorial design, clear reading hierarchy,
compact controls, and accessible contrast. Avoid adding a web framework, server,
CDN, remote fonts, package-dependent student installation, or per-point DOM nodes.

Embed styles, scripts, SVG illustrations, audited example/Task 1 JPEGs, and the
Task 2 catalog. Task 2 does not need tens of thousands of embedded thumbnails;
its core task is catalog selection. Use canvas for points, cached background plots,
and selection overlays, with a paginated accessible record table and textual counts.
Do not downsample the counted sample. If overplotting requires a density display,
state what it shows and keep selection/counting on all rows.

Proposed versioned artifacts, with paths registered centrally during implementation:

- `data/teaching/ucd_course_packet_v2.json`: distributable observations, neutral
  codes, definitions, Task 2 feedback classes, and source manifest references.
- `data/teaching/instructor/part1_reference_key_v2.json`: Task 1 truth, evidence
  audit, provenance, exclusions, role assignments, and grading policy; do not embed
  or link it from the distributed student file.
- `docs/teaching/ucd_investigation.html`: final distributable file once v2 passes
  checks; retain v1 source packet and Git history, and mark the old PDF clearly.
- Existing teaching build/validation report paths: record exact version, hashes,
  counts, sizes, tested environment, outcomes, and limitations.

Large raw FITS/catalogs and image originals stay externally cached, not committed.
The small manifests, code, teaching documentation, and final size-compliant HTML
belong in the teaching branch. Do not accidentally create a second full-sized HTML
copy in the documentation portal; the portal links to the standalone artifact.

Submission schema v3, using the unchanged v2 data packet, contains:

```text
schema_version, activity_version, packet_sha256, student_identifier
task1_responses[object_key]: class, confidence, evidence_note, evidence_basis, citation
draft_rules, draft_missing_policy
task2_attempts[]: attempt_id, rules, missing_policy, counts, metrics
task2_final_selection: attempt_id, why_it_works, how_to_improve
imported_v2_final_rules: null or preserved older final choices
task3_membership_answer
llm_disclosure: used, contribution_and_verification
```

Each rule stores enabled status, feature identifier, and minimum/maximum or null
unbounded endpoints in physical units. The implementation fixes units through the
versioned feature definitions rather than repeating them in every JSON rule;
the readable report prints the units explicitly. Attempt IDs are stable and unique.
Submitted metrics are reproducible, not trusted grading input: the instructor's
checker recomputes them from the matching frozen packet and rules. This supports
feedback audits, not an anti-cheating claim. Offline Task 2 feedback necessarily
ships information sufficient to recover its classes by inspecting the file.

Use prominent JSON export/import and a readable text report. Browser storage is
optional convenience; exports are the reliable save. Validate schema, packet hash,
identifiers, finite thresholds, ordered intervals, permitted classes/features,
attempt references, and reasonable text/file sizes before accepting an import.
Render imported text literally, never as HTML. Preserve exact Gaia identifiers.
Give incompatible v1 submissions a clear message without overwriting current work;
do not silently reinterpret Q1–Q8 answers as the new tasks. No network submission,
analytics, credentials, or scientific-database writes.

For a same-packet v2 submission, independently reproduce the original counts,
purity, and completeness before adding F1. Preserve classifications, trial history,
and the two old final choices; leave the new final choice/explanations blank and
ask the student to complete them. Reject altered old metrics or a different packet.

## 10. Implementation sequence and acceptance gates

- [x] **A. Finish requirements and read-only feasibility audit** (2026-10-14).
  Record this plan, measured inputs, browser probe, and scientific caveats.
- [x] **B. Assemble a small evidence-checked sample** (2026-10-14). Start with one UCD, star,
  and QSO plus one uncertain/missing-data case. Resolve exact identities, provenance,
  DR11 image content, and a workable student-visible evidence path before expansion.
- [x] **C. Freeze roles and build catalogs** (2026-10-14). Audit the approximately 30 Task 1
  objects, reserve labeled examples, build Task 2 from permitted data, apply all
  exclusions, measure the magnitude/class/missingness distributions, and record
  disjointness checks. No image download expansion before the small check passes.
- [x] **D. Rewrite reading and build a small complete prototype** (2026-10-14). New title,
  motivation, Gaia illustration, neutral definitions, labeled examples, compact
  Task 1 form, Task 2 rules/counts, and Task 3. First prove offline save/import and
  scoring on a small subset before loading the large catalog. Keep old artifacts
  marked v1 until replacement passes.
- [x] **E. Scale and test the full page** (2026-10-14). Measure final bytes and startup,
  evaluate/redraw, hover, reset, and history/export behavior with the actual catalog
  and images. Proposed engineering targets: file < 10,000,000 bytes, usable page
  within 5 seconds, and evaluated results/redraw within 300 ms on the documented
  Chrome/macOS test setup, including a fourfold CPU-throttled pass. These are test
  targets, not existing results or guarantees for every student's computer. Reduce
  the deterministic star sample first if needed; document the final measured counts.
- [x] **F. Verify science, grading, accessibility, and packaging** (2026-10-14). Independently
  recompute count/metric results; inspect every Task 1 image and example; exercise
  missing data, inclusive boundaries, no active cuts, empty selection, one final
  selection, repeated attempts, malformed/wrong-version imports, literal text, blocked
  browser storage, keyboard operation, narrow views, and reduced motion. Test
  `file://` with network disabled and confirm zero mandatory network requests.
  Scan student Task 1 markup/assets/data for accidental reference-label disclosure.
- [x] **F2. Implement instructor revisions** (2026-10-14). Restore the distance
  illustration and folded tool guide; expand plain-language definitions with
  prominent sans-serif names; render offline equations; add Galactic coordinates
  and button choices; require only Task 1 classification. Keep Task 2 ranges,
  benchmark F1, adopt one final selection, and test safe v2 answer migration.
- [x] **F3. Keep Task 1 images beside the response controls** (2026-10-14).
  Put measurements above, keep the desktop image column visible, and verify
  image visibility during classification/evidence/navigation at four laptop sizes.
  Check two stacked layouts, previous/next identity and saved-answer restoration.
- [x] **G. Instructor review and handoff** (2026-10-14). The instructor reviewed the
  activity, approved the revisions, and requested finalization. Resolve all five
  code-review findings, add regressions, and deliver bilingual Markdown/PDF briefs.
  Original gate: ask the instructor to review the short
  reading path, evidence-audited objects, and grading interpretation using the
  actual redesigned HTML. Provide the separate instructor manifest/checker and
  student distribution instructions. Rebuild and validate the documentation portal.

Routine layout, implementation, and deterministic-sampling choices need no new
interview. Pause if reliable teaching examples are insufficient, a scientific
classification needs changing, a required service/data source is inaccessible
without new authority, or a delivery requirement cannot be met. The final
instructor review is a meaningful pedagogical check, not a request to reapprove
every source query or interface control.

## Review of this planning task

The requested workflow is feasible. A real, large stellar pool exists; simple
browser operations are fast in a bounded measured test; the previous version has
already demonstrated offline images and answer portability. Important limits are
the finite bright-UCD pool, reference-label reliability, biased source sampling,
image availability, and final file size. None is solved by presenting unconfirmed
objects as truth or hiding missing measurements.

Documentation review: 67 Markdown sources rendered as 69 HTML pages; all 311
documentation validation checks passed, with no unavailable links or unresolved
fragments. The documentation builder passes Ruff and the tracked diff passes
whitespace checks. These checks do not validate the unbuilt v2 student application.

## Implementation review, 2026-10-14

The final catalog has 20,000 stars, 121 approved UCD references, 391 spectroscopic
QSOs, and 606 separately counted candidates. Seven demonstrations and the 30 Task 1
objects are disjoint from it. Every retained image pair has explicit notes and
hashes; nonuniform but unusable cutouts were replaced. The introductory stellar
cards are deliberately clearer than the unfiltered Task 2 stellar sample. Reference
labels do not guarantee that the offline observations uniquely determine class;
the instructor guide requires manual credit for justified uncertainty. The audit
is agent-assisted, not a blind human success-rate experiment.

The single file is below 10,000,000 bytes with all 74 cutouts embedded. Offline
image display, scoring, exact identifiers, selection boundaries, missing data,
history, save/restore, rejected imports, denied storage, narrow layouts, keyboard
focus, and reduced-motion behavior pass. The full throttled Chrome test meets
the 5-second startup and 300-ms evaluation targets. Reports:
[build](../teaching/part1_build_report.json),
[validation](../teaching/part1_validation_report.json).
The documentation portal is rebuilt as part of the handoff. The previous version
is retained separately so its builder cannot overwrite v2.
The portal now renders 70 Markdown sources as 72 HTML pages; all 314 documentation
checks pass with no unavailable links or unresolved fragments.

## Classroom handoff, 2026-10-14

The instructor approved finalization after reviewing the revised HTML. All five
code-review issues are fixed and covered by 26 focused regressions; the full suite
passes 43,740 assertions. The exact data packet and answer schema are unchanged.
English and Chinese Project Introductions are provided as Markdown and three-page
PDFs, with all pages visually checked and fonts embedded. Both explain the tasks,
deliverables, responsible LLM use, and submission of `[NAME]_[STUDENT_ID].json` to
Tsinghua Online Classroom. The classroom artifact is linked from the
[course guide](../teaching/README.md).

**Next step:** distribute the finalized HTML and preferred introduction PDF(s),
announce the deadline, and collect submissions. Part II/new searches remain
separately scoped work; no commit or merge is included in this pass.
