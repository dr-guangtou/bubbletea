# Documentation organization and HTML portal

**Date:** 2026-10-12  
**Issue:** BT-032  
**Scope:** Documentation only; no scientific processing or public deployment.

**Status:** Original appearance approved; document consolidation and HTML relocation complete.

## Approved organization revision

The project lead reviewed and approved the visual style on 2026-10-12 and requested
further cleanup: move the entrance to `docs/index.html`, consolidate same-topic
notes, remove superseded standalone files, and keep only key project documents at
the top of `docs/`. Development records are distinct from automatic journals.

The revised layout has six project-level Markdown documents; permanent scientific
explanations live in `methods/`; merged implementation and experiment records live
in `development/`. Keep `plans/`, `journal/`, and `lessons/` separate. Generated
pages and assets move from root `site/` to `docs/html/`, with the same approved design.

Before removing a note, retain its unique measurements, commands, limitations, and
scientific provenance in a dated section of the owning topic document. Preserve
journals unchanged. Record old-to-new paths and section anchors in a machine-readable
migration register so historical references remain interpretable. Update live links
and script citations; do not leave obsolete top-level compatibility documents.

- [x] Audit and classify every top-level document (2026-10-12).
- [x] Consolidate development records and relocate scientific explanations (2026-10-12).
- [x] Add a short project science guide and a complete disposition register (2026-10-12).
- [x] Persist the new organization rule for future agents (2026-10-12).
- [x] Move generated HTML, rebuild, and validate current and historical links (2026-10-12).

[Documentation guide](../documentation_guide.md) · [Current status](../current_status.md)

## Request and boundaries

The project lead requested a separate documentation branch after preserving the
existing work and updating remote master. Organize the relationship between
documents, correct stale status, generate HTML views, and provide an `index.html`
summarizing progress, the science roadmap, repository layout, and document links.
An observational-astronomy teaching project follows separately; its course brief
has not yet been provided.

The old feature branch remains unmerged. The documentation branch starts from its
latest committed state so the portal includes the workbench implementation.

## Architecture

- Markdown remains the source of truth; SPEC owns approved scientific decisions.
- `docs/current_status.md` owns the dated restart summary; PLAN owns the roadmap.
- `docs/documentation_guide.md` explains ownership, reading routes, and history.
- A standalone Python builder uses Python-Markdown for tables, fenced code,
  headings, and a per-page contents list. No frontend framework or remote service
  is needed.
- Inputs and outputs are configured centrally in `scripts/config.py`.
- `docs/index.html` is the generated entrance; `docs/html/` contains mirrored document
  pages, a complete directory, shared CSS/JavaScript, and a build report.
- Root/project guides and documents are discoverable by category. The project lead
  selected root guides plus `docs/` for the first build, with supporting documents
  elsewhere linked rather than rendered. Keep an optional `--scope all` for a
  separately requested expansion. Include newly added documentation; exclude frozen, ignored,
  dependency, and generated trees. Do not rearrange source provenance folders.
- Relative Markdown links become relative HTML links when the target is rendered.
  Source/data/image links resolve against their original file location. External
  URLs remain unchanged. Missing source links remain explicit historical warnings.
- Include source links, category labels, a contents list, related reading, and
  backlinks. Journal pages are labelled historical records rather than current policy.
- Search/filter runs locally. The site needs no network for navigation or styling.
  Scientific formulas remain readable as their source notation; do not promise
  offline mathematical typesetting without implementing it.
- Use a restrained editorial field-notebook design: warm paper, dark ink, teal
  navigation, serif titles, readable long-form text, accessible focus states,
  responsive layouts, and reduced-motion support.

## Safety and validation

The builder must never open a scientific database for writing, start the review
application, query archives, overwrite source Markdown, or follow a path outside
the repository. Writes are confined to the generated home page and site directory.

Validate at small scale before the complete build. Check generated pages and
fragment targets, source coverage, unique page paths and heading identifiers,
rendered tables/code/task lists, reproducibility, and local-link rewriting. Report
pre-existing missing historical files separately from broken generated navigation.
Measure build time and output size. Inspect desktop and narrow layouts in a browser.

## Checklist

- [x] Confirm clean feature-branch checkpoint and push remote master (2026-10-12).
- [x] Back up the existing feature branch remotely without merging (2026-10-12).
- [x] Create a separate documentation branch (2026-10-12).
- [x] Correct top-level status and duplicate issue identifier without rewriting history (2026-10-12).
- [x] Add document-ownership guide and dated current status (2026-10-12).
- [x] Implement reproducible Markdown-to-HTML builder and local navigation (2026-10-12).
- [x] Build all selected documents and check generated navigation (2026-10-12).
- [x] Record checks, limitations, and the teaching-project next step (2026-10-12).
- [x] Receive project-lead approval of the home-page appearance (2026-10-12).
  Automated browser inspection and narrow-width visual checks were unavailable;
  these remain presentation limitations, not completed tests.

## Review

### Consolidated revision

The revised build covers 58 Markdown documents and produces 60 HTML pages. The
top-level Markdown count fell from 52 to six. Forty-two development reports became
ten topic records; five permanent-definition reports became four methods
documents, alongside a new reference-review guide. All 47 retired paths have
registered destinations and original source hashes. A preservation audit compares
retained text, commands, measurements, and caveats with the original Git checkpoint.
Journals, lessons, scientific data, figures, and reference-paper packages are unchanged.

The site entrance is `docs/index.html`, all generated pages/assets are in
`docs/html/`, and obsolete root copies are removed. The original visual style was
approved by the project lead; the new structure is ready for review. Exact timing,
file size, source hashes, and link-check results are in the current build report.

### Original first-build measurements (historical)

- A five-document pilot built seven pages in 0.216 seconds before full execution.
- The complete build covers 88 root/docs Markdown documents and 90 HTML pages.
  One measured full build took 0.927184 seconds and wrote 1,238,774 HTML bytes
  before this review text was added. Exact current measurements are recorded in
  [the generated build report](../html/build_report.json).
- The standalone validator passed 109 checks: source coverage and digests,
  Markdown rendering, local links, anchors, and identifier preservation. No
  unavailable source links or unresolved fragments were found in the selected scope.
- Two successive builds produced byte-identical results for all 92 HTML and asset
  files. Timing fields in the build report are intentionally measured afresh.
- Scoped Ruff and pre-commit checks passed. Scientific data, source classifications,
  review storage, selector behavior, and profiles were not modified.
- Browser review was not completed: the in-app browser was unavailable, and native
  Chrome interaction was stopped after concurrent-user-activity guards. The
  responsive stylesheet is implemented, but its visual appearance still needs
  manual inspection. Open [the home page](../index.html), then a long specification
  and the directory filter. No public deployment was performed.
- Teaching content is intentionally deferred until audience, learning goals, time
  available, and student data access are specified.
