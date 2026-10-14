# Retained version 1 instructor notes: a star in disguise?

**Superseded for the current project:** these notes accompany only the original
six-object HTML/PDF. Use the [current instructor guide](instructor_notes.md) for
the redesigned Part I activity.

**Prepared:** 2026-10-13. **Audience:** junior undergraduates; one or two sessions;
no programming. These notes are not embedded in the student activity.

[Course overview](README.md) · [Version 1 activity](ucd_investigation_v1.html) ·
[PDF worksheet](ucd_worksheet.pdf) · [Source checks](source_checks.md)

## What to distribute

For version 1 only, send `ucd_investigation_v1.html` and optionally `ucd_worksheet.pdf`. The HTML alone
contains the full offline activity, including background reading, tool steps,
six Gaia records, and twelve images. Students save the attachment and open it in
a modern desktop browser rather than an email preview. They need no Python,
Aladin installation, website, or auxiliary files for the core exercise.

Ask for a student/group identifier, the exported readable report, and optionally
the JSON answer file. The JSON can be imported into the **same version** of the
activity to resume; it records a digest identifying the exact data snapshot.
There is no instructor inbox or automatic upload. Local browser storage may be
unavailable; an exported file is the reliable copy. Do not distribute these answer
notes if students are expected to derive the worked results independently.

The PDF is a paper worksheet, not an editable form. Its candidate pages include
both image scales; its three comparison images are close views only. Students
using paper alone should explicitly note that missing wider context in Q2.
Use extra paper for longer explanations. Optional live tool exercises are not
necessary to answer the core questions.

## A manageable lesson

For one session, introduce the motivation, demonstrate M60-UCD1 versus the
foreground star, then let pairs answer the questions and review the two published
candidates. If time is short, assign one candidate per pair and compare independent
reviews in discussion. For two sessions, use the second for the optional Gaia /
Aladin / Legacy Survey guide, independent second reviews, and follow-up proposals.
Completion time has **not** been measured with students; the workload needs your
review. There is no requirement to rehearse on Windows.

The known objects teach what a compact system can look like. The foreground star
teaches a strong alternative explanation. M59cO teaches missing measurements and
classification boundaries. The two published candidates teach evidence recording;
neither is a new discovery from this course. A new-host search remains a separate,
unfinished extension, not a prerequisite for this lesson.

## Answer guidance, not a classification key

- **Q1:** Galaxy interactions can strip a larger galaxy to its dense center;
  other UCDs may be massive star clusters. Finding candidates helps test assembly
  histories, but these images and Gaia records cannot establish a new object's
  formation history, black hole, membership, or UCD confirmation.
- **Q2:** M60-UCD1 is Gaia `3927659910436411136`; the foreground comparison is
  `3928418917055971968`. Both have compact bright centers. M60's host-light
  gradient and nearby streaks are visible. An image alone does not settle the
  distinction. Accept defensible descriptions and stated image limitations rather
  than require a predetermined resolved/unresolved flag.
- **Q3:** Using the unrounded snapshot, absolute parallax significance is
  **0.200** for M60-UCD1 and **10.333** for the foreground comparison. Rounded
  PDF values give slightly different results. M60's motion components are
  +0.420 ± 0.475 and −0.547 ± 0.432 mas/year; the star's are
  +10.984 ± 0.090 and −50.070 ± 0.082 mas/year. The latter is strong foreground
  evidence. No convincing motion is compatible with a distant system but also
  with other objects; do not interpret it as a UCD confirmation or a measured
  extragalactic distance. These simple ratios do not correct Gaia systematics.
- **Q4:** `206265 × 24.2 / distance_pc` gives angular half-light radii
  **0.303 arcsec at 16.5 Mpc**, **0.998 arcsec at 5 Mpc**, and
  **0.100 arcsec at 50 Mpc**, rounded. The physical radius stays fixed. The
  angular diameter is twice the angular radius; neither equals the blurred
  image width. The slider changes geometry, not signal-to-noise or detection
  probability. It is not an image simulation.
- **Q5:** Pixel sampling, separating two point sources, catalog completeness,
  and locating a source center are different questions. Direction, brightness
  contrast, repeated scans, and processing matter. Some extended sources with
  bright compact components enter Gaia. Pair-separation values are not UCD
  half-light-radius limits. Follow the primary citations in the background.
- **Q6:** M60-UCD1, M59-UCD3, and the foreground star have raw excess factors
  **4.654, 6.135, and 1.220** respectively; G is **18.115, 17.850, and 17.129**.
  Extension, neighboring light, host background, or measurement problems can
  affect flux excess. Multiple-star motion can affect astrometric fit quality.
  Flux excess depends on color; it is not one for all stars. This deliberately
  selected six-object set cannot measure a population contamination rate,
  completeness, or a reliable threshold.
- **Q7:** M59cO has a position-only solution in this snapshot. Its parallax,
  both proper-motion components, and RUWE are absent. No conclusion about a
  measured zero motion follows. Do not replace missing values with zeros.
- **Q8 / candidate reviews:** Reward explicit observations, values and errors,
  plausible alternatives, uncertainty, and a useful next check. Candidate A has
  conspicuous neighboring light; candidate B has neighboring extended objects.
  Whether these cause a blend is a question to inspect, not an assigned truth
  label. Both candidate pages provide close and context views. No definitive
  retain/reject answer is supplied. Color alone cannot establish a young cluster
  or H II region; a poor Gaia fit alone cannot assign a visual artifact or blend.

External quasar, galaxy, and non-single-star associations are **not checked** in
this packet. This is not evidence that such associations are absent. Keep each
student's independent review; discuss disagreements and adjudicate separately.
Do not import classroom answers into the scientific database or use a majority
vote as a confirmed label. No new selector is fitted by this exercise.

## Data and testing limits

The [data README](../../data/teaching/README.md) records the source packet and
reproduction commands. Retrieval timestamps are UTC; the 2026-10-12 UTC snapshot
was prepared on 2026-10-13 in Shanghai. Image layer is `ls-dr11`, not the blank
`ls-dr11-grz` responses encountered in initial preparation. RGB colors are display
colors, not calibrated photometry. Requested centers use Gaia J2016.0 positions;
image epochs differ, particularly relevant to a moving foreground star.

Validation used installed Chrome on macOS with network access disabled and direct
`file://` opening: all 41 checks passed, including images, exact string identifiers,
answer downloads, import rejection, keyboard plot navigation, narrow layout,
and denied browser storage. All six PDF pages were rendered and visually inspected;
desktop and narrow HTML inspection layouts were inspected. No Windows test or
complete live-archive GUI rehearsal is claimed. The portable guide names operations
because menus can change. Download/display checks are not scientific image
classifications. Raw image review fields remain pending for independent review.

**Next instructor review:** Are the background depth and eight questions suitable
for your class? Are two candidate reviews manageable? Once approved, the next
research extension is to finish one new host's literature, sensitivity, and
full-area DR11 coverage checks before preparing a new-search candidate list.
