# Current research status

**Reviewed:** 2026-10-12  
**Latest research checkpoint:** 2026-08-19  
**Purpose:** A dated restart summary, not a live dashboard or a new scientific result.

[Documentation guide](documentation_guide.md) · [Science roadmap](PLAN.md) ·
[Scientific requirements](SPEC.md) · [Open issues](todo.md)

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
| Gaia selection baseline | One shared version-1 logistic selector is used by reference, background, and host workflows | [Selector integration](point_source_selector_integration_v1.md) |
| Random comparison fields | 398 development fields and 102 independently reserved validation fields processed; direct latitude-band measurements are primary | [Validation report](large_sky_validation_run.md) |
| NGC 4698 profile | 23,811 magnitude-limited Gaia sources retrieved; 2,548 pass selector v1; 14 radial rings retained | [First-host profile](first_stage_host_profile_fixture.md) |
| M60 profile | 45,402 magnitude-limited Gaia sources retrieved; 4,920 pass selector v1; both reliable confirmed controls recovered | [M60 report](m60_positive_control.md) |
| M60 inspection sample | 400 representative passing sources and their cutouts prepared; visual classification pending | [Pilot tracking](plans/phase_4_pilot_search.md) |
| UCD image reference | 680 literature-confirmed UCDs and 44 Saifollahi high-probability candidates; 707 non-placeholder images and 17 placeholders (visual usability still unreviewed) | [Reference report](ucd_legacy_survey_reference.md) |
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

The current task is documentation maintenance and a static HTML reading portal.
It does not change any scientific selector, catalog, image classification, or
radial measurement. An observational-astronomy teaching project will follow as a
separate brief. Audience, lesson scope, exercises, and student data access have
not yet been specified; research plans must not be presented as established results.

## Snapshot limitations

This page records the repository and local data inspected on the review date.
Review counts, branch names, and remote state can change afterward. The
[issue register](todo.md) tracks work; the [journal](journal/2026-08-19_ucd_visual_review_workbench.md)
preserves dated evidence. Update this page when the next substantial checkpoint is reached.
