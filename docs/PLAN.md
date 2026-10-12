# BubbleTea — Master Development Plan

**Last updated:** 2026-10-12

[Current status](current_status.md) · [Documentation guide](documentation_guide.md) ·
[Scientific requirements](SPEC.md) · [Validation stages](plans/scientific_validation.md) ·
[Open issues](todo.md)

## Overview

Systematic search for Ultra-Compact Dwarf (UCD) galaxies around nearby galaxies
(D < 50 Mpc) using Gaia DR3 astrometry and imaging survey photometry.

Development proceeds in six phases, each building on the previous. Detailed task
tracking for each phase is in `docs/plans/`.

Phases overlap in implementation; a completed script does not close its scientific
validation stage. The latest research checkpoint is 2026-08-19. Teaching materials
are a separate upcoming documentation task, not an expansion of the research sample.

## Immediate sequence

1. Verify the implemented review workbench with a small, varied reference pilot.
2. Inspect the 724-object reference and export clean confirmed objects separately
   from the candidate follow-up pool.
3. Classify the representative 400-source M60 sample to measure real contamination.
4. Evaluate selection improvements against the frozen Gaia-only baseline.
5. Finish host geometry, background validity, and uncertainty before scientific scale-up.

## Phases

### Phase I: Literature UCDs (Reference audit complete; selection validation active)

**Goal:** Establish the known UCD population as a reference dataset. Understand their
Gaia DR3 properties. Devise distance-dependent selection criteria.

- Preserve and validate 5,049 literature records from 14 record-contributing
  publications as 4,359 canonical objects; retain 30 registered publication
  provenance packages
- Rewrite core scripts (database management, VizieR ingestion, cross-matching)
- Maintain complete canonical Gaia DR3 and Legacy Survey DR10 cross-match audits
- Analyze AEN, color, proper motion, and classprob distributions
- Calibrate one versioned Gaia-only selector; historical thresholds are exploratory
- Shared selector v1 is implemented; the 724-object visual-reference tool is ready
  but its local review database has zero saved reviews as of 2026-10-12
- **Tracking:** [Literature tasks](plans/phase_1_literature_ucds.md),
  [review-tool specification](plans/ucd_visual_review_tool.md)

### Phase Ib: Ancillary Data Collection (Reference subset prepared; broader work pending)

**Goal:** Gather complementary data from public surveys.

- Identify DESI spectroscopic data in UCD candidate regions
- Catalog imaging survey coverage (LegacySurvey, DES, KiDS, HSC)
- Cross-match known UCDs with multi-wavelength catalogs (2MASS, WISE, GALEX)
- Legacy Survey reference images, catalog matches, and Gaia external-catalog flags
  are already prepared; this is not complete multi-survey coverage
- **Tracking:** [Reference report](development/reference_imaging.md#record-ucd_legacy_survey_reference),
  [open issues](todo.md) (no separate Phase Ib checklist exists yet)

### Phase II: Target Galaxy Sample (Inherited sample audited; final definition open)

**Goal:** Define and prioritize the nearby galaxy sample (D < 50 Mpc).

- Build unified galaxy sample from LVG, CF4, NED-LVS, SGA-2020
- Collect photometry, morphology, star-formation properties
- Check imaging survey footprint overlap
- Rank by luminosity, distance, galactic latitude, and imaging coverage
- The inherited 2,155-host catalog has been audited; parent-sample completeness,
  consistent morphology, and half-light radii remain open
- **Tracking:** [Host-sample tasks](plans/phase_2_galaxy_sample.md)

### Phase III: Background Characterization (Random fields complete; host calibration open)

**Goal:** Characterize the "background density" of Gaia sources passing UCD selection.

- Measure background density versus Galactic latitude using hundreds of random
  fields
- Use directly measured same-latitude field distributions as the primary large-sky
  reference; keep the fitted model as a diagnostic only
- Report the random-field distribution alongside a valid local outer annulus and
  preserve their difference
- Validate on known UCD hosts
- All 398 development and 102 independently reserved validation fields are complete
- **Tracking:** [Background tasks](plans/phase_3_background.md),
  [independent validation](development/background_measurements.md#record-large_sky_validation_run)

### Phase IV: Pilot Search (Exploratory profiles measured; visual assessment pending)

**Goal:** Search around confirmed UCD hosts and high-priority targets.

- Validate search pipeline by recovering known UCDs
- Run radial search on high-priority targets from Phase II
- Compare radial profiles to local background
- Identify candidates (statistical excess + individual sources)
- Characterize contamination and false positive rate
- NGC 4698 and M60 profiles retain 14 rings through 600 kpc; M60's representative
  400-source visual assessment remains pending
- **Tracking:** [Pilot tasks](plans/phase_4_pilot_search.md), [M60 report](development/host_pilot_profiles.md#record-m60_positive_control)

### Phase V: Cross-match and Characterization (Planned)

**Goal:** Characterize candidates using multi-wavelength data.

- Legacy Survey morphology (TYPE, shape_r, colors)
- HST/Euclid archive search for high-resolution imaging
- DESI/SDSS spectroscopic cross-match
- Clean up sample based on multi-wavelength evidence
- **Tracking:** [Validation stages 5--6](plans/scientific_validation.md) and
  [open issues](todo.md); no dedicated Phase V checklist exists yet

### Phase VI: Statistical Analysis and Discussion (Planned)

**Goal:** Review results, draw conclusions, discuss future work.

- Statistical review of detection rates across galaxy sample
- Comparison with literature expectations
- Perspectives for future surveys (Euclid, Rubin/LSST, 4MOST)
- Spin-off project ideas
- **Tracking:** [Validation stage 6](plans/scientific_validation.md) and
  [open issues](todo.md); no dedicated Phase VI checklist exists yet

## Migration Strategy

Scripts are rewritten (not copied) from `ucd_project/` when the corresponding
phase begins. The `ucd_project/` directory is frozen and gitignored. See the
plan file for the full migration table.

## Key References

- Voggel et al. (2020), ApJ 899, 140 — Primary methodology paper
- Wang et al. (2023), ApJ 954, 206 — Gaia GC search around M31
- Saifollahi et al. (2021), MNRAS 504, 3580 — Fornax UCD sample
- See `reference/summary.md` for the complete literature table
