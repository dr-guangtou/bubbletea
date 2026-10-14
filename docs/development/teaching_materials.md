# Teaching materials: implementation and validation

**Current checkpoint:** 2026-10-14, Part I v2 implemented on
`teaching_ucd_course_20261012`; classroom finalization approved and completed.

[Course guide](../teaching/README.md) · [Instructor guide](../teaching/instructor_notes.md) ·
[Implementation plan](../plans/teaching_part1_redesign.md) ·
[Data and reproduction](../../data/teaching/README.md)

This record owns engineering decisions and measured results for the teaching
project. Approved requirements live in
[SPEC](../SPEC.md#teaching-redesign-interview-requested-2026-10-14), not here.
Teaching changes do not alter research selectors, reference classifications,
source associations, or radial measurements.

## 2026-10-14: Part I completed through technical validation

The user authorized autonomous progress after the requirements interview. The
implemented deliverable is one offline HTML containing the motivation, neutral
Gaia definitions, original scanning illustration, seven labeled examples, three
practical tasks, and JSON/text answer handling. An image/evidence audit, separate
reference key, and instructor-side checker accompany it. Final pedagogical approval
cannot be supplied by the implementation agent and remains the clear next step.

The frontend-design skill informed the editorial reading layout and compact
investigation controls. The Legacy Survey API skill informed serial acquisition,
provenance, and the distinction between successful transport and usable imaging;
the requested teaching release is DR11, not the research review's frozen DR10.
An original SVG schematic avoids third-party image licensing or online-video
dependencies. No web framework, server, CDN, telemetry, or account is required.

### Frozen catalog accounting

| Input / role | Accounting |
| --- | --- |
| Literature development rows | 843 total; only eligible confirmed references and candidate-state rows enter teaching |
| Confirmed primary-eligible rows | 146 before 13 later source-status exclusions; 133 after them |
| Reliability exclusions | Five approved exclusions applied; none overlap those remaining 133 |
| Approved development UCD references | 10 reserved for Task 1, two for labeled demonstrations, 121 in Task 2 |
| M60-UCD1 demonstration | Reused from the already-public v1 packet; not drawn from reserved validation measurements and not included in Task 2 |
| Unconfirmed candidates | 593 candidate-state rows + 13 later source-status exclusions = 606, all unscored |
| Development spectroscopic QSOs | 403 minus two demonstrations and ten Task 1 objects = 391 in Task 2 |
| External spectroscopic STAR parent | 79,369 unique Gaia-linked rows; reserve 12 gallery stars, then select 20,000 of 79,357 eligible remaining rows by documented hash |
| Disjoint teaching roles | Seven demonstrations, 30 Task 1 objects, 21,118 Task 2 rows; no duplicate Gaia identifiers across roles |

No galaxy/H II/NSS cohort is repurposed as a definitely stellar label. Spectroscopic
STAR itself does not prove singleness. Other uncertain/rejected literature rows
do not become negative training examples. Only rows with available Gaia records
from the stated development inputs can enter the measurement exercise; this is
not the complete literature census.

Task 2 magnitude spans and missing motion, measured directly from the frozen packet:

| Reference class | Count | G minimum | G maximum | Motion significance unavailable |
| --- | ---: | ---: | ---: | ---: |
| UCD | 121 | 18.162525 | 21.757988 | 68 |
| Star | 20,000 | 11.437919 | 21.720757 | 1,098 |
| QSO | 391 | 17.590460 | 21.288103 | 82 |
| Unconfirmed candidate | 606 | 11.262918 | 21.645987 | 323 |

Displayed magnitudes above are rounded; the packet retains original numeric
precision. Missing measurements remain null and stay in the completeness
denominator. The class-dependent magnitude distributions and SDSS targeting
are real selection biases, not hidden by calling this a representative sky sample.

### Image and evidence audit

The gallery uses two native image scales: 160 pixels at 0.262 arcsec/pixel and
256 pixels at 0.8 arcsec/pixel. Every retained pair was visually inspected. The
[review JSON](../../data/teaching/instructor/part1_image_reviews_v2.json) records
individual notes and SHA-256 digests. Its statements are teaching-usability
judgments, not newly approved research morphology flags or measured centroids.
Gaia positions are J2016.0; image exposures span other epochs. Centering was
checked visually, not by propagating every source to one assumed image epoch.

Seven initially chosen Cen A objects produced severe colored slabs, stripe-like
defects, or obscured central content. For HGHH92-C6, alternative `ls-dr11-grz`
and `ls-dr11-south` probes did not rescue the display: one was blank and the other
retained the color problem. The cause was not established. The
[DR11 description](https://www.legacysurvey.org/dr11/description/) and
[known issues](https://www.legacysurvey.org/dr11/issues/) were checked; a documented
issue is not automatically the explanation for these particular cutouts.

Other rejected introductory images included a blank star cutout, a target hidden
by bright-neighbor bleed, a close double, and NGC 3923 UCD1 against a saturated
host display. Raw responses remain in the external cache. Two otherwise usable
stellar choices had weak motion evidence; the final introductory stellar cards
require combined motion significance at least 4. This is a documented pedagogical
curation, not a one-dimensional four-sigma probability or a Task 2 stellar cut.
Task 2 retains difficult faint/low-motion stars and does not impose image coverage.

The ten Task 1 UCDs now span G = 18.677337646484375–20.079315185546875; four lack
Gaia motion solutions. The images remain usable, but the request for bright
examples does not justify manufacturing ten G < 19 objects. M59cO is explicitly
presented as a UCD/compact-elliptical boundary in the labeled examples only.

Reference identity and provenance were checked against current local audited
records. SDSS associations retain their angular separation, and literature sources
retain their Gaia-to-adopted-position offsets. The review was not blind to catalog
labels, and it is not an independent human classification-success test. Quasars and
some UCDs overlap in the supplied measurements. The instructor guide explicitly
allows justified uncertainty and identifies Objects 03, 21, and 25 for review.
Live SDSS/Archive interfaces are optional and are not claimed to have passed a
complete interface rehearsal. Students can complete and submit the activity offline.

### Measurement controls: real overlap, not artificial decoys

Task 2 exposes ten genuine measurements with neutral definitions; the five more
technical controls are expandable. No fitted selector coefficients, optimized
cuts, or artificial random variables are embedded. All cuts start disabled.
Simple measured summaries establish that the controls do not all offer the same
obvious separation. For example, medians over finite values are:

| Field | UCD median | Star median | QSO median |
| --- | ---: | ---: | ---: |
| BP/RP flux excess | 3.188517 | 1.215758 | 1.270916 |
| Combined motion significance | 1.333066 | 48.602861 | 1.221175 |
| IPD multi-peak percentage | 0 | 0 | 0 |
| IPD odd-window percentage | 0 | 0 | 0 |

The odd-window value is zero in 108/121 UCDs, 19,539/20,000 stars, and 383/391
QSOs. This demonstrates overlap, not universal uselessness. These instructor
summaries are not included as recommended cut directions in the student reading.
Missing motion counts above explain why reporting only finite medians is insufficient.

### Implementation boundaries

- `prepare_part1_catalog.py` assembles observations and the separate key from
  read-only development inputs; later actions acquire images and attach explicit
  reviews. Input files and exact identifiers are checked before use.
- `build_part1_materials.py` combines the packet, cached images, reading, and
  `scripts/teaching/assets/part1.*`; it requires current image reviews and refuses
  a final HTML at or above 10,000,000 bytes.
- `check_part1_answers.py` recomputes selected counts and scores independently
  with NumPy masks. It reports evidence for manual grading and never assigns a
  final grade or modifies a student file or research record.
- `validate_part1_materials.py` checks data integrity, scoring, file portability,
  interactions, and browser timing. Temporary screenshots and synthetic answers
  stay under ignored `tmp/teaching/part1/`.
- `part1_reading.md` owns the student prose. The source HTML/CSS/JavaScript owns
  task layout and behavior; the generated student HTML is not hand-edited.

All source IDs are strings. Signed FITS SDSS spectrum identifiers are preserved
as exact integers and their original representation is retained; no floating-point
conversion is permitted. Sampling and presentation use independent hash prefixes
to avoid unintentionally grouping classes by their selection rank.

Plots draw every available coordinate pair, not a hidden subsample. Unplottable
rows remain in the catalog and denominator. Log-spaced controls save actual
physical-unit thresholds; interval endpoints are inclusive. Moving a control does
not replace the last evaluated result. History supports up to 500 evaluated
attempts, one final selection, and its two explanations after the instructor
revision below. Invalid input cannot replace
the current answer state. Imported text is rendered literally.

### Final validation and packaging

The [build report](../teaching/part1_build_report.json) records exact bytes, hashes,
counts, and domains; the [validation report](../teaching/part1_validation_report.json)
records the latest browser environment and timings. The complete file is about
9.35 MB after the revision below, with 74 images and 21,118 rows, below the 10 MB limit without reducing the
planned 20,000-star sample. A full run in installed Chrome 156.0.8078.12 on macOS
15.7.4 arm64, with network disabled and fourfold CPU throttling, initially measured 0.808 s
startup and 62.6 ms median selection evaluation plus two animation frames. These
are measured local results, not Windows emulation or promises for student devices.
Reruns can differ; the linked JSON is the latest machine-readable record.

Checks cover every derived astrometric statistic against an independent covariance
calculation; input hashes; role disjointness; current reference exclusions; all 74
images decoding offline; Task 1 label separation; independent counts/metrics;
missing-value policies; equal inclusive boundaries; no-cut and empty selections;
history reuse/reset; hover; illustration play/pause; JSON/TXT downloads; complete
restore; malformed imports, including older-answer migration; literal imported text; denied storage;
narrow layout; keyboard focus; reduced motion; and zero mandatory remote requests
or JavaScript errors. The many per-row checks are data assertions, not thousands
of independent user-interface scenarios. Screenshots were inspected at desktop
and narrow widths. A full screen-reader or cross-browser audit was not performed.
The rebuilt repository portal renders 70 Markdown documents as 72 pages and passes
314 documentation checks with no unavailable links or unresolved fragments.

Scoped Ruff/pre-commit checks for the teaching scripts, configuration, and portal
builder pass, as does JavaScript syntax checking. A repository-wide pre-commit
attempt did **not** pass: its automatic fixes touched previously clean legacy
notebooks/research scripts and it reported existing lint problems there. Those
hook-only edits were fully reversed; no legacy cleanup is included. Do not report
this teaching validation as a clean repository-wide lint result.

The original six-object HTML is preserved as `ucd_investigation_v1.html`. Its
builder and validator now target that path, so running the old PDF workflow
cannot overwrite Part I v2. The old PDF and its answer notes are clearly labeled
previous-version resources. No redesigned PDF or public website is produced here.

## Instructor revisions, 2026-10-14

The revised lesson restores the earlier angular-size control (fixed published
M60-UCD1 half-light radius, adjustable hypothetical distance) without simulating
an image or using detector sampling as a UCD-detection threshold. Expanded
measurement definitions use prominent sans-serif names and plain-language meanings.
Native MathML displays the optional equations offline, with readable text
equivalents. The detailed Gaia/Aladin/Legacy tool instructions are embedded in a
folded section; external text links open new tabs with safe attributes.

Task 1 uses accessible radio controls styled as buttons. Classification alone
counts as completion; confidence, evidence basis, notes, and citations are
optional. All 37 example/classification cards show Galactic longitude/latitude
derived with Astropy from the saved Gaia ICRS coordinates. The frozen catalog,
gallery identities, images, classifications, and research inputs are unchanged.

The instructor rejected replacing ranges with weighted scores. Keep the existing
range semantics and optimize **F1**, the harmonic mean of reference-subset purity
and completeness. Display all three plus selected class counts and missed UCDs.
Unknown candidates remain separate. Empty scored selections have undefined purity
and F1 zero. One final attempt replaces the two-list design, with "Why do you think
this works?" and "How do you think this selection can be improved?"

`benchmark_part1_selection.py` first checks 16 combinations, then a bounded grid
of 4,536 combinations of G, flux excess, motion significance, and excess-noise
ranges. The pilot took 0.127 s and the full trial 0.173 s on this machine. The
[instructor-only report](../../data/teaching/instructor/part1_selection_trial.json)
contains the packet hash, grid, exact rules, counts, controls, and independent
scikit-learn F1 verification. Its best tested result is:

| Selection | Reference UCDs | Stars | QSOs | Unknown candidates | Purity | Completeness | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| No cuts | 121 | 20,000 | 391 | 606 | 0.005899 | 1 | 0.011729 |
| One known UCD, deliberately selected by unique G | 1 | 0 | 0 | 0 | 1 | 0.008264 | 0.016393 |
| Best in the bounded grid | 76 | 42 | 5 | 168 | 0.617886 | 0.628099 | 0.622951 |
| Empty list | 0 | 0 | 0 | 0 | Undefined | 0 | 0 |

The nontrivial solution uses flux excess ≥2.5 and excess noise ≥5 mas, excluding
missing active measurements. It is not claimed to be optimal outside this grid,
held-out validation, or a new scientific selector. The one-object control is a
deliberate teaching diagnostic using the reference label. None of these rules
is a preset in the student HTML.

A preliminary ranking experiment motivated the clarification: excess-factor
midranks alone gave ROC AUC 0.987552 but average precision 0.526404 on the 20,512
known-class rows. Missing values used neutral midpoint ranks; the ranking was
evaluated on the same fixed teaching sample. Average precision is a summary
across thresholds, not the purity of a particular list. That approach was not
adopted; no scoring-weight UI or AUC-based grade is included. The optional student
reading distinguishes ranking evaluation from the range-selected list's F1.

The answer schema is now `bubbletea_answers_v3`, while the data remain
`bubbletea_part1_v2` with the unchanged packet digest. A valid same-packet v2
import must reproduce its original metrics before F1 is added. It retains all
responses, attempts, and prior final choices, while asking the student to choose
the new final selection and write the new explanations. Browser and independent
instructor-checker migration agree; malformed old scores do not replace saved work.

New browser checks verify every derived Galactic coordinate, button completion,
external-link behavior, folded guide, offline equations, the distance control's
inverse-distance scaling and keyboard input, and instructor-trial counts/F1.
The full page still makes zero mandatory network requests. Native equations,
definitions, button controls, object cards, final selection, and plots were
visually inspected. Windows, other browsers, and screen readers remain untested;
there is no hidden deployment or remote typesetting dependency. The linked build
and validation reports contain the final exact sizes and timing measurements.

The pre-layout-revision check passed 43,663 assertions (mostly per-row data checks),
with a 9,349,390-byte HTML, 0.780 s startup and 63.3 ms median evaluation plus two
animation frames at fourfold CPU throttling. All eight research-input hashes
match the frozen instructor manifest. The reference packet digest is unchanged.

## Task 1 layout follow-up, 2026-10-14

The long property table had made the response panel fall below the images. Task 1
now has a full-width measurement area, with two side-by-side tables on wider
screens. Source coordinates and optional survey links stay with those measurements.
Below, close/context cutouts sit beside one compact panel containing classification,
confidence, evidence basis, evidence notes, citation, and previous/next navigation.
The desktop image column uses CSS sticky positioning within this review area,
so it remains visible while scrolling the response panel, but does not cover
later lesson sections. Windows at or below 820 CSS pixels wide stack the panels;
at or below 600 pixels, measurements also become a single column.

Previous/next preserves the existing answers, updates both images and the response
identity, and brings the new review area into view. Keyboard focus moves to its
object label without an extra page jump. Stable response elements keep their event
handlers during object changes. The student packet, images, classification choices,
required fields, answer schema, example-card arrangement, and Task 2 are unchanged.
The frontend-design guidance was used to preserve the existing notebook typography
and colors while shortening the form and grouping the related actions together.

The offline Chrome checks now include 1440×900, 1366×768, 1100×620, and 900×600
side-by-side layouts. At each, both complete cutouts are verified within the
viewport and below the navigation bar while choosing a class, writing evidence,
using Next, and reviewing the next object. The 820×740 and 390×844 stacked layouts
have no overlap or horizontal overflow. All six test previous-answer restoration,
new-object identity/image changes, and preservation of all 15 measurements and
four classification choices. Screenshots were inspected; these are browser-window
tests on macOS, not a Windows or multi-browser claim.

The full suite passes 43,713 assertions, mostly per-row data checks, with zero
required network requests or JavaScript errors. The file is 9,352,938 bytes; the
fourfold CPU-throttled run measured 0.842 s startup and 67.2 ms median evaluation
plus two animation frames. Eight research-input hashes and the teaching packet
digest remain unchanged. Exact latest evidence is in the linked build/validation
reports; temporary screenshots remain under `tmp/teaching/part1/`.

## HTML code review and Student ID wording, 2026-10-14

The requested label is now **Student ID** in the submission panel and readable
export. The JSON key remains `student_identifier`, preserving existing answers.
Only this wording and its regression check were changed; the behavior changes
below are proposed fixes, not implemented in this review. The approved visual
design and frontend styling remain intact.

The review inspected the [HTML template](../../scripts/teaching/assets/part1.html),
[JavaScript](../../scripts/teaching/assets/part1.js), CSS, builder, independent
instructor checker, and validation coverage. Reproductions used isolated offline
Chrome contexts and synthetic answers, never real student browser storage.

### High priority: rejected imports can replace current in-memory answers

`validate_state()` checks attempt identifiers with a regular expression without
first requiring a string. JavaScript converts `["attempt_0001"]` into the string
`"attempt_0001"` for this check, so a one-element array can pass. The import handler
then assigns `state = candidate` before rendering. `render_history()` calls the
identifier's `.replace()` method, which an array does not have. The catch message
says the import was rejected and current answers were kept, but the in-memory
state and already-updated fields now contain the incoming file's answers.

Reproduced from one valid evaluated attempt with an empty final choice: change
`task2_attempts[0].attempt_id` to `["attempt_0001"]`, change the incoming ID/evidence,
and import the file. The original ID was `original_student`; after the reported
rejection, the active ID was `incoming_student` and the evidence was replaced.
The previous local-storage draft remained intact because rendering failed before
`persist()`. No on-disk submitted JSON was changed, but subsequent editing could
overwrite the browser backup too. The independent Python checker rejects this
array identifier; browser and checker validation currently disagree.

**Recommended fix:** require string attempt identifiers, reject wrong types before
changing state, and restore the previous state/UI if applying an import fails.
Add the array-identifier case and an apply-stage failure to regression checks.
This is a blocker to freezing the classroom copy.

### Medium priority: malformed numeric input silently removes a cut

In `build_rule_controls()`, the numeric-field handler treats `input.value === ""`
as an intentional unbounded endpoint. A browser also exposes an empty value when
a number field contains an incomplete number such as `-`, while setting
`input.validity.badInput` to true. The handler does not distinguish these states.

Reproduced with an enabled G maximum of 19: select the numeric text, type `-`,
leave the field, and Evaluate. The saved maximum becomes null with no error.
The selected count increases from **12,901 to 21,118**. Counts are internally
consistent with the now-unbounded rule, but the student's malformed entry has
silently broadened the selection.

**Recommended fix:** check native numeric validity before accepting an empty
value, retain the last valid bound on malformed input, and make the warning
clear. Test invalid exponent/sign input separately from an intentional blank.
This is also a blocker to freezing the classroom copy.

### Medium priority: the keyboard-accessible table omits a plotted measurement

The brightness/excess-noise canvas points users to equivalent records in the
accessible table. `render_catalog_table()` supplies only ID, G, BP−RP, flux excess,
parallax significance, and motion significance; **astrometric excess noise is
missing**. A student who cannot use hover cannot inspect that plot's numeric
vertical coordinate through the promised alternative.

**Recommended fix:** include every plotted quantity in the table, with units and
missing-value handling, and check that plot fields are a subset of table fields.
No class labels need to be added.

### Lower priority: point-selection text can be stale after evaluation

The hover line updates on mouse movement, but `render_results()` redraws plots
without updating or clearing that line. In an all-source selection, hover showed
Gaia `772819441531617408` as selected. Evaluating a G range of -1 to 0 then selected
zero objects, while the line still described that source as selected. The plot
and counts were correct; the textual selection status was stale.

**Recommended fix:** clear the hover description when the evaluated selection
changes, or retain the hovered row index and refresh its status from the new mask.
Test evaluation and answer-file restoration after hovering.

### Lower priority: logarithmic slider endpoints can exclude the maximum row

The slider maps through `log1p` and its inverse even at the endpoints. Round-trip
floating-point error can produce a maximum just below the observed maximum, so
the advertised inclusive range excludes the highest-valued row. The affected
fields in the frozen packet are flux excess, motion significance, astrometric
excess noise, and excess-noise significance. Their endpoint differences are tiny,
but the comparison uses exact numeric values, not the rounded displayed labels.

**Recommended fix:** use the stored observed minimum/maximum exactly at slider
positions 0/1000, and interpolate only interior positions. Do not introduce an
arbitrary scientific tolerance into all range comparisons. Test the handler with
all features, checking that full observed ranges retain all finite rows.

### Scope and remaining limitations

The existing suite, plus the Student ID assertion, passes **43,714 assertions**
(mostly per-row data checks). Normal save/import, old-answer migration, independent
purity/completeness/F1, six window layouts, and unchanged input hashes still pass.
Additional structural checks found no duplicate DOM IDs, broken internal anchors,
or unlabeled form controls. The label edit produces a **9,352,922-byte** HTML;
startup was 0.819 s and evaluation plus two animation frames 63.9 ms at fourfold
CPU throttling. These passes do **not** resolve the newly reproduced findings.

A browser-restored draft also starts without an unsaved-export warning; its local
copy still exists, so this is a weaker reminder rather than a demonstrated loss.
The lesson already requires JSON backups. Windows, other browsers, screen-reader
operation, shared-computer use, and live external services remain untested.
No browser test claims universal absence of bugs. Fix the confirmed findings and
add regression cases before freezing the classroom distribution copy.

## Next action at the code-review checkpoint (superseded below)

Obtain approval for the focused fixes above, implement them with regression checks,
then freeze the exact class copy and its matching packet/key. Part II
can use the saved membership answers to begin a separately scoped real-search
exercise. No commit, merge, push, or scientific-catalog mutation was part of this
autonomous implementation pass.

## Classroom finalization and Project Introductions, 2026-10-14

The instructor approved all five fixes and requested classroom finalization plus
student-facing English/Chinese assignment introductions. This supersedes the
pending approval noted in the preceding code-review checkpoint.

Implemented and verified:

1. Require primitive string attempt identifiers before regex validation. A failed
   import application restores the previous in-memory state and redraws the
   previous form/history/results; browser storage is not written before that
   application succeeds. Tests reject array IDs in both v3 and migrated v2 and
   force a rendering-stage failure after an otherwise valid import.
2. Check native numeric-input validity before treating an empty string as an
   intentionally absent bound. Incomplete minus/exponent input restores the last
   valid visible value and explains why. Deliberately clearing a box still works.
3. Include astrometric excess noise, with mas units, in the accessible catalog
   table. Check all displayed columns against their correct catalog values.
4. Clear hover descriptions on results/restoration, leaving a plot, or moving
   into empty plot space. A stale selected/not-selected claim cannot survive a
   new evaluation or an empty-history import.
5. Set slider positions 0/1000 to the exact stored extrema; interpolate only
   interior positions. Handler-level tests cover both ends of all ten features,
   including retention of every available row with the full observed interval.

The focused pilot passed **26 checks** before full validation. The full offline
suite passed **43,740 assertions** in Chrome 156.0.8078.12 on macOS 15.7.4 arm64.
As before, most assertions concern individual data rows rather than UI actions.
At fourfold CPU throttling, startup was **0.795206 seconds** and the median
evaluation plus two animation frames was **64.5 ms**. There were no mandatory
remote requests or uncaught browser errors. The HTML is **9,354,951 bytes**;
its SHA-256 is
`49bbd5851475cca8159eca904d04e89e640b4d8af86d0b27c520d936e35db68d`.
The data packet remains
`365ce898ac0ab8944adc514d24d0208b4ac91e02f0db67fc6925a34551f2f1ad`;
the answer schema remains `bubbletea_answers_v3`.

New student briefs:

- [English Markdown](../teaching/project_introduction_en.md) and
  [English PDF](../teaching/project_introduction_en.pdf).
- [Chinese Markdown](../teaching/project_introduction_zh.md) and
  [Chinese PDF](../teaching/project_introduction_zh.pdf).

Each PDF has three pages: background/startup, the three tasks, and deliverables/
submission. Markdown is the source of truth; the new
[builder](../../scripts/teaching/build_project_introductions.py) renders it,
checks source-text preservation and embedded Unicode fonts, and renders every
page for visual inspection. All six pages were inspected; a stranded colon in
the Chinese task description was corrected and re-rendered. The builder's
[report](../teaching/project_introduction_build_report.json) records source/PDF
hashes, font information, and page counts. Its automated checks do not claim to
replace this visual review. PDF styling follows the classroom page's green/ink
palette; PDFs are assignment briefs, not replacements for the interactive tasks.

Both language versions and the HTML explain submission of
`[NAME]_[STUDENT_ID].json` to Tsinghua Online Classroom (网络学堂). The existing
form asks only for Student ID; students rename the downloaded file themselves.
The TXT export includes the same instruction and is not a substitute for JSON.
No Task 1 answer labels, optimized Task 2 cuts, or Task 3 solution were added.
The scoped Chinese-language exception is recorded in `AGENTS.md`.

Reproduction:

```bash
BUBBLETEA_EXTERNAL_DATA="$HOME/Dropbox/work/data" uv run python scripts/teaching/build_part1_materials.py
uv run python scripts/teaching/validate_part1_materials.py
uv run python scripts/teaching/build_project_introductions.py
```

PDF rebuilding uses ReportLab from the `teaching` extra and installed Poppler.
The configured macOS fonts are Arial Unicode plus the Simplified Chinese face of
STHeiti Medium. Other build machines can set `BUBBLETEA_TEACHING_FONT`,
`BUBBLETEA_TEACHING_BOLD_FONT`, and `BUBBLETEA_TEACHING_BOLD_FONT_INDEX` (use 0 for
a standalone TTF) to appropriate installed Unicode fonts. The builder fails if
required glyphs are absent. Students need no fonts installed because both PDFs
embed the subsets used. All paths are centralized in `scripts/config.py`.

The PDF skill required rendering/visual checks; the frontend-design skill helped
retain the approved classroom layout without unrelated redesign. No research
catalog, selector, acquisition workflow, or grading policy was changed. Windows,
other browsers, screen-reader use, and real classroom timing remain untested.
No commit, merge, push, or upload to the course platform was performed.

**Next step:** distribute the final HTML and preferred introduction PDF(s),
announce the deadline, and collect JSON submissions. Part II remains separate work.

Final repository checks: scoped Ruff and pre-commit hooks pass, JavaScript parses,
and the independent instructor checker accepts the exported synthetic answers.
The rebuilt documentation portal contains 72 Markdown sources / 74 HTML pages;
all 316 link/structure checks pass, with zero unavailable links or fragments.
Whitespace checks pass. Repository-wide legacy lint cleanup is not included.
