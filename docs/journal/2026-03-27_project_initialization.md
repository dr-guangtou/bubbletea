# 2026-03-27: Project Initialization

## What was done

- Created formal directory structure for the BubbleTea project
- Wrote core project files:
  - `README.md` — project overview with scientific context, phases, and structure
  - `CLAUDE.md` / `AGENTS.md` — project conventions and rules for AI-assisted development
  - `pyproject.toml` — Python 3.12+, dependencies (astropy, astroquery, pandas, numpy, matplotlib, scipy), ruff config
  - `.pre-commit-config.yaml` — ruff check + format hooks
  - `scripts/config.py` — central path configuration with environment variable support
  - `.gitignore` — updated for research project (gitignore FITS, DB, ucd_project/)
- Wrote development plan:
  - `docs/PLAN.md` — master plan with 6 phases
  - `docs/plans/phase_1_literature_ucds.md` — detailed Phase I task tracking
- Migrated data from `ucd_project/`:
  - `ucd_collection.db` (756 KB, 1,542 UCDs from 6 sources)
  - Per-source CSV catalogs (9 files)
  - Source metadata JSONs (key_papers.json, vizier_inventory.json)
  - `galaxy_sample_ranked.csv` (2,155 galaxies, 446 KB)
- Migrated `LESSON.md` to `docs/lessons/LESSON.md`
- Added provenance README.md to `reference/voggel2020/` and `reference/wang2023/`

## Decisions made

- Scripts directory named `scripts/` (not `src/`) — more natural for a research project
- External data accessed via `BUBBLETEA_EXTERNAL_DATA` environment variable
- Journal entries go in `docs/journal/` (repo-local, not Obsidian)
- Migration is demand-driven: scripts rewritten per-phase, not bulk copied
- Phase I scope: migrate and verify existing 6 papers first; literature expansion comes later
- `ucd_project/` is frozen and gitignored — serves as read-only reference during migration

## Current state

- 1,542 known UCDs in database from 6 literature sources
- 59% Gaia DR3 match rate, 59.5% Legacy Survey DR10 match rate
- 2,155 target galaxies (D < 25 Mpc) in ranked sample
- 7 galaxies with high-contrast (>10x) UCD signal in pilot search
- Background density varies 10x with galactic latitude

## Next steps

- Verify migrated database integrity
- Begin Phase I.3: rewrite core database scripts
- Write `scripts/utils/plotting.py` for consistent figure generation
- Start Gaia cross-match verification (I.4)
