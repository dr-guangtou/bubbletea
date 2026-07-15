# Phase I: Literature UCDs — Task Tracking

**Goal:** Establish the known UCD population as a reference dataset, understand their
Gaia DR3 properties, and devise distance-dependent selection criteria.

**Status:** In progress

Sections completed in April-May 2026 record the historical exploratory pipeline.
Canonical counts and scientific validation status are governed by
`docs/plans/scientific_validation.md` and the generated status artifact.

---

## I.1 Infrastructure Setup

- [x] Create directory structure (2026-03-27)
- [x] Write pyproject.toml with dependencies (2026-03-27)
- [x] Configure ruff in pyproject.toml (2026-03-27)
- [x] Create .pre-commit-config.yaml (2026-03-27)
- [x] Write scripts/config.py (2026-03-27)
- [x] Update .gitignore (2026-03-27)
- [x] Write README.md (2026-03-27)
- [x] Write CLAUDE.md and AGENTS.md (2026-03-27)
- [x] Write docs/PLAN.md (2026-03-27)
- [x] Write this task tracking file (2026-03-27)
- [x] Migrate LESSON.md to docs/lessons/LESSON.md (2026-03-27)
- [x] Create first journal entry (2026-03-27)
- [x] Write scripts/utils/plotting.py (matplotlib defaults + save_figure helper) (2026-04-15)

## I.2 Literature Database Migration and Verification

- [x] Copy ucd_collection.db to data/literature/database/ (2026-03-27)
- [x] Copy by_source CSVs to data/literature/catalogs/by_source/ (2026-03-27)
- [x] Copy sources JSON files to data/literature/sources/ (2026-03-27)
- [x] Copy galaxy_sample_ranked.csv to data/galaxy_sample/ (2026-03-27)
- [x] Verify historical database checkpoint (1,542 rows, 6 sources) (2026-04-15)
- [x] Validate current v2 database (5,049 records, 4,359 canonicals) (2026-07-15)
- [x] Write data/README.md documenting provenance of each file (2026-04-15)
- [x] Add provenance README.md to reference/voggel2020/ (2026-04-15)
- [x] Add provenance README.md to reference/wang2023/ (2026-04-15)

## I.3 Rewrite Core Database Scripts

Source: `ucd_project/scripts/ucd_database/`

- [x] `scripts/phase1_literature/ucd_database.py` — schema + utilities (2026-04-15)
- [x] `scripts/phase1_literature/fetch_vizier_catalog.py` — VizieR ingestion (2026-04-15)
- [ ] Verify: run ingestion against existing DB, confirm same counts

## I.4 Gaia Cross-match

Source: `ucd_project/scripts/legacy_survey/xmatch_gaia_final.py`

- [x] `scripts/phase1_literature/xmatch_gaia.py` — Gaia DR3 cross-match (2026-04-15)
- [x] Synchronize all 963 canonical Gaia associations (2026-07-15)
- [x] Preserve the 632-row historical export and generate a complete 4,359-target
  canonical audit (2026-07-15)

## I.5 Legacy Survey Cross-match

Source: `ucd_project/scripts/legacy_survey/xmatch_legacy_survey.py`

- [x] `scripts/phase1_literature/xmatch_legacy_survey.py` — NOIRLab Data Lab TAP (2026-04-15)
- [x] Run spherical cross-match for all 4,359 canonical targets (2026-07-15)
- [x] Export 3,723 matches and preserve 636 no-match audit states (2026-07-15)
- [x] Preserve the 917-row historical export by manifest digest (2026-07-15)

## I.6 Gaia Property Analysis and Figures

Source: `ucd_project/scripts/analysis/analyze_ucd_properties.py`, `color_color_analysis.py`

- [x] `scripts/phase1_literature/analyze_gaia_properties.py` (2026-04-15)
- [x] Figure: AEN distribution vs host galaxy distance (2026-04-15)
- [x] Figure: UCD property distributions (AEN, BP-RP, G mag, RUWE) (2026-04-15)
- [x] Figure: Color-magnitude diagram (2026-04-15)
- [x] Figure: classprob_galaxy analysis (2026-04-15)
- [ ] Figure: Background vs UCD property comparison

## I.7 Distance-dependent Selection Criteria

Source: `ucd_project/scripts/analysis/distance_analysis.py`

- [x] `scripts/phase1_literature/distance_selection.py` (2026-05-11)
- [x] Study AEN threshold as function of distance (2026-05-11)
- [x] Study magnitude limits as function of distance (2026-05-11)
- [x] Derive parametric selection criteria (Model C - Probabilistic) (2026-05-11)
- [x] Document in docs/plans/selection_criteria.md (Pending creation of separate file, summary in journal)
- [x] Figure: Selection criteria vs distance (2026-05-11)
- [x] Figure: Completeness vs distance (2026-05-11)

## I.8 Phase I Summary

- [x] Write journal entry summarizing Phase I findings (2026-05-11)
- [x] Update docs/PLAN.md with Phase I results (2026-05-11)
- [x] Update reference/summary.md if new papers were added (2026-05-11)
- [x] Mark Phase I complete (2026-05-11)

---

## Scripts Migration Reference

| New script | Source in ucd_project/ | Purpose |
|-----------|------------------------|---------|
| ucd_database.py | scripts/ucd_database/ucd_database.py | Schema + utilities |
| fetch_vizier_catalog.py | scripts/ucd_database/ingest_improved.py | VizieR ingestion |
| xmatch_gaia.py | scripts/legacy_survey/xmatch_gaia_final.py | Gaia cross-match |
| xmatch_legacy_survey.py | scripts/legacy_survey/xmatch_legacy_survey.py | Legacy Survey cross-match |
| analyze_gaia_properties.py | scripts/analysis/analyze_ucd_properties.py | Property analysis |
| distance_selection.py | scripts/analysis/distance_analysis.py | Selection criteria |
