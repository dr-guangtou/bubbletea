# Current research status

**Reviewed:** 2026-10-14 (teaching implementation update; research checkpoint unchanged)

**Latest research checkpoint:** 2026-08-19  
**Purpose:** A dated restart summary, not a live dashboard or a new scientific result.

[Documentation guide](documentation_guide.md) · [Science roadmap](PLAN.md) ·
[Science guide](science_guide.md) · [Scientific requirements](SPEC.md) · [Open issues](todo.md)

## The question we are trying to answer

Can Gaia measurements identify a reproducible excess of ultra-compact dwarf
galaxies (UCDs) around nearby galaxies? A UCD is a compact stellar system whose
size or luminosity can place it beyond ordinary globular clusters. A source
passing our Gaia selection is **not** automatically a UCD.

Population measurements come first; individual candidate lists are secondary.
External images help interpret sources but must not silently change membership or
area in the frozen Gaia-only measurements.

## What has been completed

| Work | Measured or recorded result | Evidence |
| --- | --- | --- |
| Literature reference | 5,049 source records, 4,359 distinct catalog objects, and 30 publication provenance packages | [July 16 count audit](../data/literature/validation/project_status_counts.json) |
| Gaia selection baseline | One shared version-1 logistic selector is used by reference, background, and host workflows | [Selector integration](development/selector_experiments.md#record-point_source_selector_integration_v1) |
| Random comparison fields | 398 development fields and 102 independently reserved validation fields processed; direct latitude-band measurements are primary | [Validation report](development/background_measurements.md#record-large_sky_validation_run) |
| NGC 4698 profile | 23,811 magnitude-limited Gaia sources retrieved; 2,548 pass selector v1; 14 radial rings retained | [First-host profile](development/host_pilot_profiles.md#record-first_stage_host_profile_fixture) |
| M60 profile | 45,402 magnitude-limited Gaia sources retrieved; 4,920 pass selector v1; both reliable confirmed controls recovered | [M60 report](development/host_pilot_profiles.md#record-m60_positive_control) |
| M60 inspection sample | 400 representative passing sources and their cutouts prepared; visual classification pending | [Pilot tracking](plans/phase_4_pilot_search.md) |
| UCD image reference | 680 literature-confirmed UCDs and 44 Saifollahi high-probability candidates; 707 non-placeholder images and 17 placeholders (visual usability still unreviewed) | [Reference report](development/reference_imaging.md#record-ucd_legacy_survey_reference) |
| Interactive review tool | Full 724-object list, two image scales, catalog evidence, coordinate proposals, review history, and versioned exports implemented | [August 19 checkpoint](journal/2026-08-19_ucd_visual_review_workbench.md) |

The 724-object image-review set is a selected reference, not the full literature
database. The database's 740 confirmed objects and this set's 680 confirmed
objects are different scopes, not contradictory counts.

## Where work stopped

On 2026-10-12 the local review database contained **zero saved review revisions**.
The checked-in August 17 exports also record zero reviewed objects. The workbench
is implemented, but no clean, visually reviewed positive reference has yet been
produced from it. The stored API validation reports 15 passing checks; this
restart audit did not rerun browser tests.

Both confirmed objects and candidates use `include`, `exclude`, or `hold` review
decisions. For a candidate, `include` means retain in the follow-up pool, never
promote to confirmed. Original data and classifications remain unchanged.

## Next research steps

1. Verify the local workbench and review a small, varied pilot before the full list.
2. Review reference images and source identifications, preserving uncertainty and
   correction proposals rather than editing the canonical catalog.
3. Export a clean confirmed-UCD design reference and a separate candidate pool.
4. Inspect the representative M60 sample to measure real-field contamination;
   do not substitute a promising-candidate shortlist for that sample.
5. Test selection improvements against the frozen baseline before scaling up.

The workbench launch command is in its [README](../scripts/phase4_search/ucd_visual_review/README.md).

## What prevents final scientific claims

- **Selection sensitivity:** Completeness and contamination must be measured over
  magnitude, distance, size, and Gaia measurement availability. A selection score
  is not a calibrated probability that a source is a UCD.
- **Host properties:** The inherited 2,155-galaxy table is useful, but the final
  parent sample, consistent morphology, and half-light radii remain unfinished.
  A half-light radius is the radius enclosing half a galaxy's measured light.
- **Radial boundaries:** The initial 0--50 kpc exclusion and 600 kpc reach are
  conservative working geometry, not final scientific limits. Preserve all rings.
- **Background and uncertainty:** Random-field measurements are available, but
  valid host-specific comparisons, group/cluster treatment, and calibrated
  overdensity significance still require work.

See the [validation stages](plans/scientific_validation.md) for acceptance
requirements; completed software is not equivalent to completed science.

## Documentation and teaching pivot

Documentation maintenance and the static HTML reading portal are complete.
The entrance is [docs/index.html](index.html), with generated pages under
`docs/html/`. Six project-level Markdown documents remain directly under `docs/`;
scientific explanations live in `methods/`, and consolidated development records
live in `development/`. The [consolidation audit](development/documentation_audit.md)
records each retired document and its retained evidence.
The active side task is [A Galaxy in Disguise](teaching/README.md), a no-code
undergraduate project. The [Part I implementation](plans/teaching_part1_redesign.md)
is complete through technical validation. The
[single offline HTML](teaching/ucd_investigation.html) contains illustrated background,
seven labeled examples, 30 source classifications, a 21,118-row selection experiment,
and one open membership question. All 74 DR11 cutouts are embedded and reviewed.
JSON save/restore, independent grading calculations, malformed-import rejection,
denied storage, and offline desktop/narrow layouts pass the recorded tests.
The revised approximately 9.35 MB file meets the measured performance/size targets.
It restores the distance/angular-size illustration and folded online guide, renders
optional equations offline, and makes Task 1 classification the only required
per-object field. Task 2 retains ranges but now optimizes F1 (the harmonic mean
of purity and completeness) and saves one final selection with two explanations.
The instructor-only range trial reaches F1 0.623 on this teaching sample; it is
not an independent estimate of new-field performance. Older same-packet answers
import without losing prior work.
The Task 1 layout follow-up puts measurements above the images/response area and
keeps the desktop images beside the controls. Six window sizes pass the layout
and navigation checks; data, classifications, and the answer schema are unchanged.

Latest handoff: all five code-review findings are fixed and the classroom HTML is
finalized. The suite passes 43,740 assertions, including 26 focused regressions.
Student-facing Project Introductions are available in
[English](teaching/project_introduction_en.md) and
[Chinese](teaching/project_introduction_zh.md), each with a visually checked,
three-page PDF. Students submit `[NAME]_[STUDENT_ID].json` to Tsinghua Online
Classroom (网络学堂). Next: **distribute the HTML and introduction PDF(s), set the
course deadline, and collect JSON submissions**. See the
[handoff record](development/teaching_materials.md#classroom-finalization-and-project-introductions-2026-10-14)
and [instructor notes](teaching/instructor_notes.md).
The [development record](development/teaching_materials.md) documents curation,
reference exclusions, image failures, timing, and limitations. Technical tests do
not prove unique class identification from Gaia and a thumbnail or establish
student completion time. Windows rehearsal is not required and has not been done.
The [old six-object HTML](teaching/ucd_investigation_v1.html) and
[PDF](teaching/ucd_worksheet.pdf) remain explicitly version 1 resources.
New-search host checks belong to later teaching parts. No scientific selector,
catalog, image classification, or radial measurement is changed; teaching reviews
are not scientific confirmations.

## Snapshot limitations

This page records the repository and local data inspected on the review date.
Review counts, branch names, and remote state can change afterward. The
[issue register](todo.md) tracks work; the [journal](journal/2026-08-19_ucd_visual_review_workbench.md)
preserves dated evidence. Update this page when the next substantial checkpoint is reached.
