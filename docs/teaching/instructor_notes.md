# Instructor guide: A Galaxy in Disguise, Part I

**Date:** 2026-10-14. **Status:** classroom file finalized after approved revisions
and regression-tested fixes. These notes are not embedded in the
student HTML.

[Student activity](ucd_investigation.html) · [Course guide](README.md) ·
[Technical record](../development/teaching_materials.md) ·
[Data provenance](../../data/teaching/README.md)

## What to review first

The [code review](../development/teaching_materials.md#html-code-review-and-student-id-wording-2026-10-14)
findings are resolved with 26 focused regressions, including a forced import
rendering failure. The full suite passes 43,740 assertions. The Student ID label
is corrected; no group ID is asked. The instructor has approved finalization.

1. Read the background and compare the labeled examples. Is the depth appropriate
   for your students? The approximately 30-minute reading path is a target, not a
   classroom timing measurement.
2. Inspect Task 1, especially **Object 03** (a QSO with overlapping compact-system
   measurements), **Object 21** (the least conspicuous UCD by flux excess), and
   **Object 25** (a QSO with nearby light). Decide how much credit a well-supported
   `uncertain` response should receive. No numerical grade threshold is imposed.
3. Try a few Task 2 rules, compare F1 alongside purity/completeness, save one final
   selection with the two explanations, and export/import JSON. Check
   whether the 30-object investigation plus selection exercise fits the intended
   out-of-class workload. Task 3 deliberately has no hints or answer key here.

These remain useful teaching/grading checks, not unresolved implementation gates.
Research follow-up and new-host searches remain later work.

## Distribution and submissions

Send **`ucd_investigation.html`** with the preferred
[English](project_introduction_en.pdf) and/or [Chinese](project_introduction_zh.pdf)
Project Introduction. Students save and open the HTML in a desktop
browser. All 74 image cutouts, the reading, and catalog data are embedded. They
need no software installation, local server, internet, or supporting files for
the core tasks. Optional archive/viewer links need internet. Do not distribute
the instructor directory as an answer key.

Ask students to rename their **JSON answer file** to **`[NAME]_[STUDENT_ID].json`**
and upload it to **Tsinghua Online Classroom (网络学堂)**. They replace the two
placeholders with their name and Student ID, omit brackets, and keep the extension.
The page itself asks only for Student ID. The readable TXT is optional and does
not replace JSON. JSON supports resuming in this exact activity version and independently
checking the rules. Browser storage is not a reliable submission mechanism, and
there is no automatic upload. Incomplete work can be exported. Keep a copy of the
exact HTML and packet used by the class; data changes deliberately invalidate old
submissions. The retained version 1 PDF is not a print version of this lesson.

LLM assistance is welcome with a brief disclosure of its contribution and what
the student checked. Do not require private chat histories or an unaided attempt.
Assess observations, reasoning, uncertainty, citations, and reproducible work.

## What the reference classes mean

The seven demonstrations are M60-UCD1, M59-UCD3, M59cO, two independently
spectroscopically classified stars, and two spectroscopic quasars. M59cO is
explicitly labeled as a UCD/compact-elliptical boundary case with unavailable
astrometry; it is not a clean binary-classification answer and is not in either task.

Task 1 has **10 UCD references, 10 spectroscopic stars, and 10 spectroscopic
quasars**, presented in a separately shuffled order. That composition is not
shown to students. Its UCDs are Sombrero UCD1, three Fornax objects, VUCD1, VUCD2,
VUCD5, VUCD6, S804, and J122636.42+125512.9. They span G = 18.677–20.079, rounded
for this summary. Four of the ten have unavailable Gaia motion solutions.
These are current approved literature reference labels, not new confirmations.

Several brighter Cen A cutouts contained severe colored slabs or obscured centers.
NGC 3923 UCD1 was lost against its displayed host background. They were replaced
with somewhat fainter, usable images; their scientific records were not rejected.
Every retained close/context pair has explicit visual notes and image hashes in
[the review record](../../data/teaching/instructor/part1_image_reviews_v2.json).

Introductory stellar cards deliberately require combined proper-motion significance
at least 4, so students have clearer motion evidence. This two-component statistic
is **not** a one-dimensional four-sigma probability. This curation applies only to
the small gallery. **Task 2 has no proper-motion, parallax, color, flux-excess, or
image-quality cut on its sampled stars.** Its difficult low-motion and missing-data
stars are retained. Magnitude matching in the gallery does not make the parent
catalog representative of every region of sky.

## Task 1: grade evidence, not certainty

The [instructor reference key](../../data/teaching/instructor/part1_reference_key_v2.json)
retains exact string Gaia identifiers, canonical identities, original publication
or spectrum information, source-file hashes, association offsets, and the review
notes. No Task 1 reference classes or class-bearing object names are embedded in
its student cards. Coordinates and identifiers are provided for open investigation;
finding the published identity is allowed if cited.

Only the classification (including `uncertain`) is mandatory. Confidence, evidence
basis, notes, and citations are optional. The button-style choices preserve an
unanswered state. Do not penalize omitted optional fields as incomplete Task 1
submissions; assess evidence and confidence when students choose to supply them.
Galactic longitude and latitude are calculated from each saved Gaia position and
shown on every object card, without introducing them as a classification rule.

The layout keeps measurements above the images and answers. On wider windows,
the images stay beside the response panel while students classify, type evidence,
or advance. Previous/next returns the new images and classification to view,
retaining the previous object's answers. Narrow windows use a stacked layout.
This is a layout-only revision; existing answer files require no new migration.

Gaia plus an RGB image supports a comparison, not necessarily a unique physical
class. Small motion is not proof of a quasar or UCD. Flux excess can overlap;
missing astrometry is not zero; surrounding light can affect interpretation.
Some definite reference QSOs are legitimately **uncertain from the supplied
observations alone**. In particular, Object 03 overlaps UCD-like measurements.
Credit a careful uncertain answer rather than force unsupported confidence.
The current audit is agent-assisted preparation, not an independent blind human
classification experiment or measured student success rate.

Suggested review dimensions for any supplied supporting evidence, without fixed point weights:

- Did the student identify the intended source and use actual measurements/errors?
- Does the explanation distinguish observations from interpretation and literature?
- Is the stated confidence defensible, including missing values and image limitations?
- If an external record supplied the class, is that evidence cited?

Catalog STAR does not prove singleness. No absence of an NSS, galaxy, or QSO-candidate
flag is assumed. An image-quality warning does not itself establish a blend;
color does not itself establish a young cluster. Classroom answers must not be
imported into canonical research classifications.

## Task 2: what its scores establish

The fixed catalog contains **20,000 stars + 121 UCD references + 391 QSOs +
606 unconfirmed candidates = 21,118 sources**. Examples and Task 1 are disjoint
from it. Approved reliability exclusions are applied; 13 later source-status
exclusions are retained only among the unscored candidates. Scientific validation
measurements are not used to construct the exercise. The already-public M60
example comes from the preserved v1 teaching packet.

Purity is selected reference UCDs divided by selected reference UCDs, stars,
and QSOs. Completeness is selected reference UCDs divided by all 121 reference
UCDs, **including those with missing measurements**. F1 is their harmonic mean,
equivalently `2 TP / (2 TP + FP + FN)`: selected UCDs are TP, selected stars/QSOs
are FP, and missed reference UCDs are FN. The 606 candidates enter none of the
three scores; their selected count remains visible. Empty scored selections
have undefined purity, not 100%, and F1 = 0. All intervals include their endpoints and combine
with AND; the missing-data policy is part of the saved rule.

These are scores for this constructed reference subset, not a prediction of
purity near a new host. SDSS targeting, spectroscopic success, footprint, literature
selection, magnitude distributions, and chosen class proportions all matter.
The student page explains the distinction. Repeated experiments are appropriate
for learning, but scores after repeated tuning are not an independent scientific
validation result. No learned research-model coefficients or optimized cuts are
provided. Individual plotted points remain classless after evaluation.

Require one evaluated final selection and answers to **"Why do you think this
works?"** and **"How do you think this selection can be improved?"**. The learning
objective is higher F1, not higher purity or completeness in isolation. Evaluate
whether the actual recorded results support the explanation. A perfect score or
particular threshold is neither promised nor required. The IPD window fractions
are genuine measurements, not fake distractors:
both have median zero in every scored class in this sample, so students can discover
their limited simple separation themselves. That observation is not a claim that
the fields are universally useless.

### Instructor-only range-cut trial

The [measured trial](../../data/teaching/instructor/part1_selection_trial.json)
tests 4,536 combinations of ranges using fields available to students. Its best
result selects **76/121 UCDs, 42 stars, 5 QSOs**, plus **168 unconfirmed candidates**:
purity **61.8%**, completeness **62.8%**, F1 **0.623**. Its active cuts are flux
excess at least 2.5 and astrometric excess noise at least 5 mas, with missing active
measurements excluded. This is one achievable solution, not a global optimum,
independent scientific validation, or recommended production selector. Keep these
thresholds out of the student page; there is no automatic solution preset.

Selecting everything yields F1 **0.0117** despite complete UCD recovery. Selecting
exactly one reference UCD by its unique G value yields F1 **0.0164** despite 100%
reference purity; selecting nothing yields zero. The one-object rule deliberately
uses the instructor label to illustrate the earlier exercise's loophole, not to
recommend an observational strategy. F1 is a better classroom objective for this
concern, but it still depends on the chosen class mixture and the unknown candidates
remain unscored. ROC AUC is explained as optional background, not used to optimize
these binary range selections.

## Check submitted files

Only the instructor needs the repository and Python environment:

```sh
uv run python scripts/teaching/check_part1_answers.py \
  --answers /path/to/student_answers.json \
  --output /path/to/instructor_check.json
```

The checker validates the version and exact packet digest, verifies object IDs,
and recomputes each attempt from the actual saved rules and missing-data policy.
It rejects mismatched or altered counts, invalid thresholds, and bad references.
Its output combines each student explanation with the instructor evidence notes;
`class_agrees` is a comparison, **not an automatic grade**. Task 3 and justified
uncertainty always require human assessment. Never overwrite the original submission.

Current submissions use `bubbletea_answers_v3` with the unchanged version 2 data
packet. Valid same-packet older v2 submissions are checked, their F1 scores are
recomputed, and the two old final choices are preserved separately. The browser
asks for a new single final selection and both new explanations; it does not
silently choose for the student. Wrong packets, version 1 answers, and tampered
older scores are rejected without replacing existing work.

This is not an anti-cheating system. Offline Task 2 feedback necessarily includes
information sufficient to recover its reference classes by inspecting the HTML.
Task 1's separate key is not shipped, but its public sky identities are discoverable.

## Testing and remaining limits

The complete local file was tested with network disabled in installed Chrome on
macOS, including image decoding, independent scoring, JSON/text downloads, restore,
invalid imports, denied storage, narrow layouts, keyboard focus, and paused/reduced-
motion behavior. At fourfold CPU throttling, startup and evaluation met the plan's
5-second and 300-ms targets. Exact measurements are in the
[validation report](part1_validation_report.json); the file remains below 10 MB.
Student-device performance, other browsers, live archive interfaces, accessibility
with a screen reader, and classroom completion time have not been established.

**Next step:** distribute the finalized HTML and introduction PDF(s), announce the
deadline on the course platform, and collect JSON submissions before Part II.
