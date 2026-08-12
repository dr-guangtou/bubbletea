# CLAUDE.md — BubbleTea Project Instructions

## Project Identity

- **What this is**: A reproducible research project for searching UCD galaxies using Gaia data.
  NOT a Python package or library. Contains scripts, figures, notebooks, and data.
- **Goal**: Publication-ready pipeline with clear data provenance.
- **Language**: English only. `snake_case` everywhere (files, functions, variables).

## Tools and Environment

- **Python**: 3.12+, managed exclusively by `uv` (`uv sync`, `uv run`, `uv add`)
- **Linting/formatting**: `ruff` (configured in pyproject.toml)
- **Pre-commit**: `pre-commit run --all-files` — uses ruff as single source of truth
- **No pytest**: Scripts are the unit of work. Each script is standalone and runnable.
- **Run scripts**: `uv run python scripts/phase1_literature/some_script.py`

## Directory Conventions

```
scripts/phase{N}_{name}/   — Scripts organized by research phase
scripts/config.py          — Central path configuration (ALL paths go here)
scripts/utils/             — Shared utilities (plotting, cross-match)
data/                      — All data products
data/external/             — Large catalogs (gitignored, accessed via env var)
data/literature/           — UCD literature database and catalogs
figures/phase{N}/          — Figures with companion .md caption files
reference/                 — Literature: [first_author_last_name][year]/ folders
docs/journal/              — Research journal (YYYY-MM-DD_topic.md)
docs/lessons/              — Lessons learned (append with date headers)
docs/plans/                — Per-phase task tracking with checkboxes
ucd_project/               — Legacy code (FROZEN, gitignored, read-only reference)
```

## Path Configuration

- ALL paths are defined in `scripts/config.py`. Import from there.
- NEVER hardcode absolute paths in scripts.
- External data (large catalogs): set `BUBBLETEA_EXTERNAL_DATA` environment variable.
  `config.py` falls back to `data/external/` if the env var is not set.
- Note: `/Users/shuang/data/` references appear in legacy `ucd_project/` code.
  Do not change them there; do not replicate them in new scripts.

## Provenance Rules (CRITICAL)

Every data file must be traceable to its original source:
- **ADS bibcode** (e.g., 2020ApJ...899..140W)
- **DOI** (e.g., 10.3847/1538-4357/aba842)
- **VizieR catalog ID** (e.g., J/ApJ/899/140)
- **PDF file** stored in `reference/[author][year]/`

Reference paper folders follow the naming convention:
`reference/[LAST_NAME_OF_FIRST_AUTHOR][YEAR_OF_PUBLICATION]/`
If multiple papers by the same first author in one year, append a/b/c/d.
Each folder contains: PDF, original data files, and a README.md with full provenance.

## Figure Convention

Every figure gets TWO files:
```
figures/phase{N}/descriptive_name.png
figures/phase{N}/descriptive_name.md    # Caption file
```

Caption `.md` format:
```markdown
# Figure: [Title]

**Script:** `scripts/phase1_literature/analyze_gaia_properties.py`
**Command:** `uv run python scripts/phase1_literature/analyze_gaia_properties.py`
**Data:** `data/literature/database/ucd_collection.db`
**Date:** YYYY-MM-DD

**Description:**
[What the figure shows and key takeaways]
```

Use `scripts/utils/plotting.py` for consistent matplotlib style.
The `save_figure()` helper saves both PNG and companion .md simultaneously.

## Journal Convention

- **Location:** `docs/journal/YYYY-MM-DD_brief_topic.md`
- **Format:** What was done, decisions made, results, next steps
- **Reference** specific scripts, data files, and figures by path

## Lessons Convention

- **Location:** `docs/lessons/LESSON.md` (single file, append-only)
- **Format:** New lessons appended with date headers:
  ```
  ## YYYY-MM-DD: Topic
  **Lesson:** What was learned
  **Context:** Why it matters
  **Recommendation:** What to do about it
  ```

## Task Tracking

- `docs/plans/phase_{N}_{name}.md` contains task checklists per phase
- Use markdown checkboxes: `- [ ]` pending, `- [x]` done
- Add date completed next to done items
- At the end of every task, always propose the clear next step or ask the user a
  decision question.

## Code Style

- `snake_case` for everything — files, functions, variables, constants
- Use specific, complete words for names (no abbreviations unless standard: ra, dec, mag)
- Scripts have docstrings explaining purpose, inputs, outputs
- No wildcard imports
- `pathlib.Path` for all file paths
- `logging` module (not `print`) for scripts that run long
- No redundant comments that restate function/variable names

## Scientific Communication

- Define every new scientific or project-specific term in plain language before
  using its abbreviation or shorthand.
- Do not invent jargon when an ordinary English phrase is sufficient.
- Summaries must explain what an analysis is doing and why, not only name its
  scripts, phases, catalogs, or internal labels.

## Host-Centered Measurement Geometry

- Real galaxy measurements must preserve a series of concentric circular annuli so
  the radial profile remains available; do not reduce a host immediately to one
  fixed circular count.
- Exclude a separately defined inner galaxy region from UCD inference because
  galaxy substructure, compact star-forming regions, and H II regions can dominate
  there. Calibrate this inner boundary rather than adopting the temporary benchmark
  radius or an unvalidated fixed value.
- Small fixed-angle circles used for archive-query benchmarks are diagnostics only
  and must never become the real host measurement aperture by default.

## Gaia Area Policy

- Do not apply bright-star, dust, or ancillary-imaging masks to Gaia radial-area
  measurements. For Gaia, usable area equals the area covered by verified completed
  retrieval strips; incomplete or failed strips remain explicit missing area.
- Keep any generic mask-intersection fixture labeled as geometry validation only.
  It must not be used as a Gaia scientific mask or density denominator.

## M60 Positive-Control Review Policy

- During the first M60 positive-control pass, possible stellar, non-single-star,
  QSO, galaxy, H II-region, blend, and artifact contamination must be recorded as
  review flags only. Do not automatically remove flagged sources from the frozen
  Gaia selector output or radial profile.
- Use compact Legacy Survey DR10 three-color cutouts for visual checks because the
  intended targets are compact. Keep cutout availability, imaging masks, and image
  classifications separate from Gaia coverage and area accounting.

## Git Conventions

- Branch strategy: feature branches, never work directly on `main`
- Commit messages: `phase{N}: what changed` (e.g., `phase1: add Gaia cross-match script`)
- Do NOT commit: large data files (>10MB), .db files, .fits files, __pycache__
- `ucd_project/` is gitignored (frozen legacy reference)
- `notebooks/archive/`, `reference/data/`, `doc/sql/` are ignored (legacy)

## What NOT to Do

- Do not restructure `reference/` without asking
- Do not delete or modify anything in `ucd_project/` (read-only reference)
- Do not install packages outside of `uv`
- Do not create Jupyter notebooks in the root directory
- Do not use camelCase anywhere
- Do not estimate numerical values — always benchmark and measure
- Do not add features, refactor, or "improve" beyond what was asked

## Development Phases

Active development follows a phased plan documented in `docs/PLAN.md`:
- Phase I: Literature UCDs (current)
- Phase Ib: Ancillary data
- Phase II: Galaxy sample
- Phase III: Background characterization
- Phase IV: Pilot search
- Phase V: Cross-match and characterization
- Phase VI: Statistical analysis

Migration from `ucd_project/` is demand-driven: scripts are rewritten (not copied)
when the corresponding phase begins. Always check the original script in
`ucd_project/scripts/` for reference before writing new code.
