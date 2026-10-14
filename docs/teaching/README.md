# A Galaxy in Disguise

**Updated:** 2026-10-14. **Status:** classroom file finalized after instructor
revisions and all five code-review fixes. English/Chinese introductions accompany it.

[Open the student HTML](ucd_investigation.html) ·
[Instructor guide](instructor_notes.md) ·
[Implementation plan](../plans/teaching_part1_redesign.md) ·
[Development and validation record](../development/teaching_materials.md)

This is Part I of a semester-long, no-code observational astronomy project for
STEM-background junior undergraduates. Students already know coordinates,
magnitude, color, and the purpose of Gaia. They investigate real measurements
and images, rather than complete a reading-comprehension quiz.

## The complete student project

The required activity is **[ucd_investigation.html](ucd_investigation.html)**. It contains
the reading, original Gaia scanning and interactive angular-size illustrations, all required observations,
74 saved Legacy Survey DR11 cutouts, and every task. No supporting data package,
website, local server, Python, account, installation, or internet is required.
Students save the attachment and open it in a desktop browser, not an email
preview. Optional Gaia, Legacy Survey, SDSS, SIMBAD, and Aladin links need internet.

Include either or both student-facing Project Introductions as assignment briefs:

- English: [Markdown](project_introduction_en.md) · [three-page PDF](project_introduction_en.pdf).
- Chinese: [Markdown](project_introduction_zh.md) · [three-page PDF](project_introduction_zh.pdf).

Both cover background, all three tasks, deliverables, saving/resuming, and LLM use.
Students rename the JSON export to **`[NAME]_[STUDENT_ID].json`** and upload it to
**Tsinghua Online Classroom (网络学堂)**. The webpage asks only for Student ID;
the name is supplied in the filename. TXT is optional, not a substitute for JSON.
Do not distribute instructor keys or the whole repository as the student package.

| Section | What students do |
| --- | --- |
| Motivation and background | Learn why compact systems are interesting and how Gaia collects measurements; definitions remain neutral rather than prescribing cuts |
| Seven labeled examples | Compare M60-UCD1, M59-UCD3, M59cO, two stars, and two quasars; M59cO explicitly illustrates a classification boundary |
| Task 1 | Investigate 30 neutral-coded sources; choose a class or uncertainty using buttons; confidence and evidence records are optional; no answer reveal |
| Task 2 | Explore 21,118 real catalog rows, adjust measurement ranges, compare purity/completeness/F1, and save one final selection with two explanations |
| Task 3 | Answer one open question about association with a host galaxy, without hints; carry the response into Part II |
| Save and submit | Export/import JSON, download a readable text report, and briefly disclose responsible LLM assistance |

Aim for about 30 minutes of core reading and example study, with longer independent
task time. This is a design target, not measured student completion time.
Task 2 includes 20,000 spectroscopic stars, 121 UCD references, 391 spectroscopic
quasars, and 606 unconfirmed candidates. The candidates are counted separately
and enter none of purity, completeness, or F1. F1 combines purity and completeness
using their harmonic mean; students try to improve it without a fixed pass mark.
The constructed mixture is not an
unbiased sample of a new galaxy field. There is no automated best-cut suggestion.

Students should save JSON early and often. Browser storage is best-effort; an
exported file is the reliable record. Keep the exact HTML used for the class:
imports check its data snapshot. Nothing is uploaded automatically, and classroom
answers cannot change the research database.

Task 1 places measurements above the review area in two columns on wider screens.
Below, the close/context images remain beside the classification and evidence
controls; the image column stays in view while scrolling that panel. Previous/next
returns to the new object's images and classification. Narrow windows stack the
panels without shrinking the controls into an unusable sidebar.

The revised answer format is `bubbletea_answers_v3`; the underlying data remain
the same version 2 packet. Older same-packet v2 answers import safely, preserving
responses, evaluated attempts, and old final choices. Students then designate
one final selection and answer the revised explanation prompts. The tool guide
is folded by default, external links open new tabs, and optional equations render
without downloading a library.

## Validation and distribution

The [instructor guide](instructor_notes.md) explains the source curation, difficult
cases, evidence-based grading, JSON checker, and review priorities. The lesson
works offline in installed Chrome on macOS, including denied browser storage.
No Windows or other-browser rehearsal is claimed. Browser performance, exact
file size, and test environment are recorded in the
[build report](part1_build_report.json) and
[validation report](part1_validation_report.json).

All five findings in the [final code review](../development/teaching_materials.md#html-code-review-and-student-id-wording-2026-10-14)
are fixed: rejected imports preserve answers, malformed numbers retain the last
valid cut, the table includes excess noise, hover text refreshes, and slider
endpoints retain exact extrema. The full suite passes 43,740 assertions, including
26 focused regressions. The frozen data packet and answer schema are unchanged.
Both introduction PDFs have embedded Unicode fonts and were visually checked on
all three pages. See the [introduction build report](project_introduction_build_report.json).

Pedagogical review concerns reading depth, the 30-object
workload, and treatment of justified uncertainty in the actual page. Technical
tests do not establish that every source can be uniquely classified from Gaia
and a thumbnail. The separate instructor record audits every displayed image pair
and retains the independent literature/spectroscopic evidence.

## Maintaining the materials

[SPEC](../SPEC.md#teaching-redesign-interview-requested-2026-10-14) owns the approved
requirements; the [Part I plan](../plans/teaching_part1_redesign.md) tracks completion.
[Data provenance and reproduction](../../data/teaching/README.md) documents the
frozen packet and external image cache. Implementation details belong in
[development/teaching_materials.md](../development/teaching_materials.md), not a
new top-level document. Paths are defined in `scripts/config.py`.

The research selector, canonical catalog, contamination decisions, and radial
measurements are unchanged. New-host searches belong to later teaching parts.
The [provisional host shortlist](target_shortlist.md) still needs full-area
imaging, literature, and sensitivity checks before any discovery assignment.

## Retained version 1 and supporting reading

The earlier six-object lesson is preserved as
[ucd_investigation_v1.html](ucd_investigation_v1.html), alongside its
[six-page PDF](ucd_worksheet.pdf), [worksheet source](worksheet.md), and
[version 1 instructor notes](instructor_notes_v1.md). They do **not** implement the
new three-task project. The new introduction PDFs explain the assignment;
they are not printable replacements for the interactive HTML.
The legacy builder now writes the v1 HTML path and cannot overwrite Part I v2.

The [concept guide](concepts.md), [platform-independent tool guide](tool_guide.md),
and [original source checks](source_checks.md) remain useful supporting references.
The current student reading is maintained in [part1_reading.md](part1_reading.md)
and embedded directly in the distributed HTML. The repository reading portal
under `docs/html/` is separate and is not a student distribution package.

**Next step:** upload the finalized HTML and the preferred introduction PDF(s) to
the course platform, set the assignment deadline, and collect students' JSON files.
Part II/new-candidate searching remains a separate task.
