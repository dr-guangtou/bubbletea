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
docs/development/          — Topic-organized implementation notes, benchmarks, and audits
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

- Always read and serialize Gaia source identifiers as strings when matching,
  excluding, or recording provenance. Their 19 digits can be rounded by floating-
  point conversion.

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

## Documentation Organization

- Keep only project-level key Markdown documents directly under `docs/`:
  scientific specification, roadmap, current status, issue register, documentation
  guide, and the project science guide. The HTML entrance is `docs/index.html`.
- Put implementation notes, experiment logs, retrieval benchmarks, debugging
  records, and development audits under `docs/development/`, organized by topic.
  Extend an existing topic document rather than creating another top-level note.
- Keep permanent scientific definitions and reference explanations under
  `docs/methods/`; keep task checklists under `docs/plans/`.
- Journals remain under `docs/journal/` and lessons under `docs/lessons/`.
  Development notes are not a replacement for either.
- Keep course materials, student instructions, and teaching target lists under
  `docs/teaching/`, separate from the scientific roadmap and research decisions.
- Distributable teaching HTML must work when opened directly as a local file,
  without a website, local server, installation, or mandatory network requests.
  Embed required assets and data; make online links optional and export student
  answers separately. Do not require access to a Windows computer for preparation.
- Deliver the entire teaching Part 1 project in one self-contained HTML file.
  Aim for about 30 minutes of core reading, link/cite advanced material separately,
  and allow longer independent work on the tasks with saved progress.
- End teaching Part 1 with one open question about establishing a candidate's
  membership in a host galaxy. Save the response for Part II; do not provide a
  hint panel, worked solution, or automatic correctness feedback for this question.
- In the teaching introduction, define measured quantities and provide optional
  deeper reading without revealing which features or cut directions distinguish
  UCDs from stars or quasars. Students investigate those relationships themselves.
- For teaching classification exercises, keep Task 1 reference labels and
  correctness feedback out of the student-facing presentation. Record selections
  for instructor grading; reserve iterative selection feedback for Task 2.
- In teaching Task 1, only the classification choice is mandatory. Confidence,
  evidence basis, notes, and citations are optional; do not count them as required
  completion fields or silently reinstate the earlier requirements.
- Ask for the individual student's ID in the teaching submission panel and
  readable report, not a group identifier. Preserve the existing submission key.
- For this course, students rename their exported answers to
  `[NAME]_[STUDENT_ID].json` and upload to Tsinghua Online Classroom (网络学堂).
  Keep the HTML form limited to Student ID; explain the filename separately.
- The requested Chinese Project Introduction is an explicit exception to the
  English-only rule. Provide equivalent English and Chinese Markdown/PDF teaching
  introductions; code, logs, and other project documentation remain in English.
- Open external text links in the student lesson in a new tab with safe link
  attributes. Keep internal section navigation in the current page and embed
  required content so that saved work does not depend on online services.
- Allow and encourage responsible LLM assistance in the teaching activity, with
  brief disclosure. Teach students to verify its claims against observations and
  sources; do not impose a ban or an unaided-first requirement.
- Verify the student-visible evidence for every Task 1 teaching object before
  assignment: source identity, usable images, measurements, and supporting external
  records must permit a defensible classification. Record unresolved ambiguities
  explicitly rather than treating an instructor label as sufficient evidence.
- Use a genuinely star-rich teaching Task 2 catalog; set its final size by measuring
  the complete offline file. Apply current reference reliability exclusions, score
  secure classes only, and report selected unconfirmed candidates separately.
- Keep Task 2 range controls. Use purity, completeness, and their harmonic mean
  (F1) for feedback, with one explained final selection; do not reinstate the
  superseded two-list requirement or replace ranges with scoring weights.
- Before adding a document, consult `docs/documentation_guide.md` and link to the
  existing owner of the topic. Record consolidation and removal decisions in the
  development documentation audit. Preserve unique scientific evidence and
  provenance; do not treat a superseded result as current policy.
- HTML is generated, not hand-maintained. Rebuild it after moving or merging
  Markdown documents and validate internal links and script output destinations.

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
- Do not assign a compact star-forming-region or young-cluster flag from color alone.
  Require a catalog association or visual evidence; because such catalogs are rare
  and incomplete, no catalog match is unknown evidence rather than evidence against
  the flag.
- Assign a nearby-source blend or image-problem flag only from visual inspection.
  Gaia image-quality measurements may prioritize a source for inspection, but they
  remain separate warnings and cannot assign the visual flag.

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
