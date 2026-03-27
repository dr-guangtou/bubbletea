# Phase I: Literature UCDs — Task Tracking

**Goal:** Establish the known UCD population as a reference dataset, understand their
Gaia DR3 properties, and devise distance-dependent selection criteria.

**Status:** In progress

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
- [ ] Write scripts/utils/plotting.py (matplotlib defaults + save_figure helper)

## I.2 Literature Database Migration and Verification

- [x] Copy ucd_collection.db to data/literature/database/ (2026-03-27)
- [x] Copy by_source CSVs to data/literature/catalogs/by_source/ (2026-03-27)
- [x] Copy sources JSON files to data/literature/sources/ (2026-03-27)
- [x] Copy galaxy_sample_ranked.csv to data/galaxy_sample/ (2026-03-27)
- [ ] Verify database integrity (row counts: 1,542 UCDs, 6 sources)
- [ ] Write data/README.md documenting provenance of each file
- [ ] Add provenance README.md to reference/voggel2020/
- [ ] Add provenance README.md to reference/wang2023/

## I.3 Rewrite Core Database Scripts

Source: `ucd_project/scripts/ucd_database/`

- [ ] `scripts/phase1_literature/ucd_database.py` — schema + utilities
- [ ] `scripts/phase1_literature/fetch_vizier_catalog.py` — VizieR ingestion
- [ ] Verify: run ingestion against existing DB, confirm same counts

## I.4 Gaia Cross-match

Source: `ucd_project/scripts/legacy_survey/xmatch_gaia_final.py`

- [ ] `scripts/phase1_literature/xmatch_gaia.py` — Gaia DR3 cross-match
- [ ] Run cross-match for all 1,542 UCDs
- [ ] Verify: ~913 matches (59.2%)
- [ ] Save to data/literature/catalogs/all_ucds_gaia_matched.csv

## I.5 Legacy Survey Cross-match

Source: `ucd_project/scripts/legacy_survey/xmatch_legacy_survey.py`

- [ ] `scripts/phase1_literature/xmatch_legacy_survey.py` — NOIRLab Data Lab TAP
- [ ] Run cross-match
- [ ] Verify: ~917 matches (59.5%)
- [ ] Save to data/literature/catalogs/all_ucds_legacy_matched.csv

## I.6 Gaia Property Analysis and Figures

Source: `ucd_project/scripts/analysis/analyze_ucd_properties.py`, `color_color_analysis.py`

- [ ] `scripts/phase1_literature/analyze_gaia_properties.py`
- [ ] Figure: AEN distribution vs host galaxy distance
- [ ] Figure: UCD property distributions (AEN, BP-RP, G mag, RUWE)
- [ ] Figure: Color-magnitude diagram
- [ ] Figure: classprob_galaxy analysis
- [ ] Figure: Background vs UCD property comparison

## I.7 Distance-dependent Selection Criteria

Source: `ucd_project/scripts/analysis/distance_analysis.py`

- [ ] `scripts/phase1_literature/distance_selection.py`
- [ ] Study AEN threshold as function of distance
- [ ] Study magnitude limits as function of distance
- [ ] Derive parametric selection criteria
- [ ] Document in docs/plans/selection_criteria.md
- [ ] Figure: Selection criteria vs distance
- [ ] Figure: Completeness vs distance

## I.8 Phase I Summary

- [ ] Write journal entry summarizing Phase I findings
- [ ] Update docs/PLAN.md with Phase I results
- [ ] Update reference/summary.md if new papers were added
- [ ] Mark Phase I complete

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
