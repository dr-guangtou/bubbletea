# BubbleTea — Master Development Plan

**Last updated:** 2026-03-27

## Overview

Systematic search for Ultra-Compact Dwarf (UCD) galaxies around nearby galaxies
(D < 50 Mpc) using Gaia DR3 astrometry and imaging survey photometry.

Development proceeds in six phases, each building on the previous. Detailed task
tracking for each phase is in `docs/plans/`.

## Phases

### Phase I: Literature UCDs (Active)

**Goal:** Establish the known UCD population as a reference dataset. Understand their
Gaia DR3 properties. Devise distance-dependent selection criteria.

- Migrate and verify the existing UCD literature database (1,542 objects, 6 papers)
- Rewrite core scripts (database management, VizieR ingestion, cross-matching)
- Cross-match all known UCDs with Gaia DR3 and Legacy Survey DR10
- Analyze AEN, color, proper motion, and classprob distributions
- Derive distance-dependent selection criteria
- **Tracking:** `docs/plans/phase_1_literature_ucds.md`

### Phase Ib: Ancillary Data Collection (Planned)

**Goal:** Gather complementary data from public surveys.

- Identify DESI spectroscopic data in UCD candidate regions
- Catalog imaging survey coverage (LegacySurvey, DES, KiDS, HSC)
- Cross-match known UCDs with multi-wavelength catalogs (2MASS, WISE, GALEX)
- **Tracking:** `docs/plans/phase_1b_ancillary_data.md`

### Phase II: Target Galaxy Sample (Planned)

**Goal:** Define and prioritize the nearby galaxy sample (D < 50 Mpc).

- Build unified galaxy sample from LVG, CF4, NED-LVS, SGA-2020
- Collect photometry, morphology, star-formation properties
- Check imaging survey footprint overlap
- Rank by luminosity, distance, galactic latitude, and imaging coverage
- **Tracking:** `docs/plans/phase_2_galaxy_sample.md`

### Phase III: Background Characterization (Planned)

**Goal:** Characterize the "background density" of Gaia sources passing UCD selection.

- Map background density vs galactic latitude using hundreds of random fields
- Fit parametric model for density(|b|) and field-to-field variance
- Design local background estimation strategy (annulus method)
- Validate on known UCD hosts
- **Tracking:** `docs/plans/phase_3_background.md`

### Phase IV: Pilot Search (Planned)

**Goal:** Search around confirmed UCD hosts and high-priority targets.

- Validate search pipeline by recovering known UCDs
- Run radial search on high-priority targets from Phase II
- Compare radial profiles to local background
- Identify candidates (statistical excess + individual sources)
- Characterize contamination and false positive rate
- **Tracking:** `docs/plans/phase_4_pilot_search.md`

### Phase V: Cross-match and Characterization (Planned)

**Goal:** Characterize candidates using multi-wavelength data.

- Legacy Survey morphology (TYPE, shape_r, colors)
- HST/Euclid archive search for high-resolution imaging
- DESI/SDSS spectroscopic cross-match
- Clean up sample based on multi-wavelength evidence
- **Tracking:** `docs/plans/phase_5_crossmatch.md`

### Phase VI: Statistical Analysis and Discussion (Planned)

**Goal:** Review results, draw conclusions, discuss future work.

- Statistical review of detection rates across galaxy sample
- Comparison with literature expectations
- Perspectives for future surveys (Euclid, Rubin/LSST, 4MOST)
- Spin-off project ideas
- **Tracking:** `docs/plans/phase_6_analysis.md`

## Migration Strategy

Scripts are rewritten (not copied) from `ucd_project/` when the corresponding
phase begins. The `ucd_project/` directory is frozen and gitignored. See the
plan file for the full migration table.

## Key References

- Voggel et al. (2020), ApJ 899, 140 — Primary methodology paper
- Wang et al. (2023), ApJ 954, 206 — Gaia GC search around M31
- Saifollahi et al. (2021), MNRAS 504, 3580 — Fornax UCD sample
- See `reference/summary.md` for the complete literature table
