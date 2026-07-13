---
date: 2026-07-14
repo: bubbletea
branch: review_project_context_20260714
tags:
  - journal
  - takeover
  - scientific-specification
---

## Progress

- Audited the repository, legacy context, research journals, active scripts, generated data products, and the local Voggel (2020) and Wang (2023) reference papers.
- Recorded the Gaia-only UCD research definition and priority-ordered objectives in `docs/SPEC.md` and the operational project state in `docs/CONTEXT.md`.
- Registered 29 audit issues in `docs/todo.md`; BT-001 is complete and 28 issues remain open.
- Added the six-stage validation sequence in `docs/plans/scientific_validation.md`; the next stage is literature reference stabilization.
- Committed the accumulated Phase I-IV snapshot and review documentation as `bef96ea` (`phase4: consolidate pipeline and scientific validation`).
- Appended and verified the one-sentence development snapshot in the `wensai` Obsidian daily note for 2026-07-14.

## Lessons Learned

- The primary scientific target is a Gaia-detectable UCD population, operationally defined by evidence of extension and luminosity or size beyond ordinary globular clusters rather than a fixed physical boundary.
- Population overdensity must be established with Gaia data alone; external imaging and spectroscopy are value-added validation products.
- Null and negative excess measurements are scientifically required, and any provisional three-sigma threshold must account for searched radial and selection trials.
- The database and exported literature catalogs are not synchronized, so object identity, source association, confirmation tier, and duplicate handling must be stabilized before selection criteria are trained.
- Distance, Galactic latitude, local environment, and Gaia scanning behavior are selection-function variables that require empirical characterization rather than assumed numerical thresholds.

## Key Issues

- Begin Stage 1 by auditing canonical literature objects, source associations, confirmation tiers, and the 180 exact duplicate-coordinate groups without destructive deduplication.
- Reconcile the 2,108-row database with exported Gaia and Legacy Survey products before using either representation as authoritative.
- Resolve missing provenance folders for seven cited sources and distinguish confirmed UCDs from literature candidates.
- Ruff reports 85 issues across active scripts even though all 26 Python files parse successfully.
- Preserve the first-round Gaia-only statistical design while leaving color cuts, annular signal regions, latitude limits, and candidate probabilities empirically open.
