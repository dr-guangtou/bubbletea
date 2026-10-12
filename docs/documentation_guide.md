# How to read and maintain the documentation

[Current status](current_status.md) · [Science roadmap](PLAN.md) ·
[Scientific requirements](SPEC.md) · [Open issues](todo.md)

## Start here

Read [current status](current_status.md) for where work stopped, then the
[roadmap](PLAN.md) for the scientific sequence. Use [SPEC.md](SPEC.md) when deciding
what an analysis is allowed to mean. Open a detailed report only when its evidence
is needed. The HTML home page is [index.html](../index.html).

## One purpose per document

| Document or location | Its job | What it must not become |
| --- | --- | --- |
| [README](../README.md) | Entry point, setup, and repository layout | A competing detailed task list |
| [Current status](current_status.md) | Dated restart summary and next research step | A claim of continuously live measurements |
| [PLAN](PLAN.md) | Science roadmap and phase-level status | A second scientific specification |
| [SPEC](SPEC.md) | Approved definitions, requirements, and architecture | A log of every implementation detail |
| [Issue register](todo.md) | Cross-phase open issues and resolution requirements | An unlabelled mixture of old and current status |
| [Validation stages](plans/scientific_validation.md) | Evidence needed before scientific scale-up | Proof that unchecked stages are complete |
| Phase plans in `docs/plans/` | Phase-specific checklists and delivery details | Independent scientific policy |
| Method and result reports in `docs/` | Reproducible evidence, limitations, and artifact pointers | Current policy when explicitly superseded |
| `docs/journal/` | Dated decisions and session records | Instructions that automatically override later decisions |
| [Lessons](lessons/LESSON.md) | Append-only explanations of mistakes and safeguards | A current scientific status summary |
| [Data guide](../data/README.md), [literature guide](../reference/summary.md), and figure captions | Provenance and interpretation of specific artifacts | General roadmap or unchecked scientific claims |
| [AGENTS](../AGENTS.md) | Operational rules for agents | Scientific evidence |

## How these documents connect

```text
README / HTML home
        |
        +-- current_status: where we stopped
        +-- PLAN: the scientific sequence
                 |
                 +-- SPEC: approved requirements
                 +-- scientific_validation: evidence required
                 +-- todo / phase plans: work still needed
                          |
                          +-- reports --> data, scripts, figures, provenance
                          +-- journals: dated decisions and checkpoints
```

When documents disagree, distinguish requirements from measurements and check
their dates. Approved scientific requirements belong in SPEC; a later report
cannot silently authorize a different method. The current-status page summarizes
evidence but does not override it. Ask the project lead when approved decisions
actually conflict.

## Reading routes

- **New collaborator:** [current status](current_status.md) → [roadmap](PLAN.md) →
  [context](CONTEXT.md) → [scientific requirements](SPEC.md).
- **Source selection:** [Gaia features](gaia_selector_features.md) →
  [selector integration](point_source_selector_integration_v1.md) →
  [astrometric rejection assessment](point_source_astrometric_rejection_assessment_v1.md).
- **Background measurements:** [direct comparison](large_sky_direct_background_comparison.md)
  → [independent validation](large_sky_validation_run.md) →
  [radial measurement design](radial_measurement_design.md).
- **Visual reference review:** [reference images and catalogs](ucd_legacy_survey_reference.md)
  → [tool specification](plans/ucd_visual_review_tool.md) →
  [launch instructions](../scripts/phase4_search/ucd_visual_review/README.md).
- **Real-field contamination:** [M60 report](m60_positive_control.md) →
  [pilot checklist](plans/phase_4_pilot_search.md).
- **Teaching preparation:** Start with current status and the feature definitions;
  prepare a separate student-facing account after the course brief is agreed.

## Linking and historical records

- Write relative Markdown links, such as `[roadmap](PLAN.md)`; avoid machine-specific
  absolute paths in new navigation links.
- Link to the document that owns a statement rather than copying its entire content.
- Use headings as stable destinations and check links after renaming a heading.
- Keep journals, source packages, and old results in place. Label historical or
  superseded material rather than rewriting the history of a measurement.
- The original `BT-023` means probabilistic host association. The M60 task was
  accidentally assigned the same number; it is now `BT-031`. Old dated references
  are preserved and must be interpreted by their task title.
- Do not change raw data, review databases, or selection outputs during a
  documentation build. Local-only and missing files must be labelled, not fabricated.

## Build the HTML reading portal

```bash
uv sync
uv run python scripts/documentation/build_documentation.py
```

Open `index.html` at the repository root. Generated document pages live under
`site/`, mirroring their Markdown locations. A complete document directory and
text filter are available from the home page. Each page links to its Markdown
source, related documents, and the pages that cite it.

The agreed first build covers root guides and everything under `docs/`, including
journals. Supporting paper READMEs, figure captions, and script guides elsewhere
remain links to their source files. An explicitly requested broader build can use
`--scope all`; neither mode includes the frozen `ucd_project/` tree. The build does
not download catalogs or publish a website. Local files are linked in place, so
keep the generated site with the repository. Some evidence requires locally
available large data; the site is not a self-contained copy of those datasets.

HTML is a generated reading view. Edit Markdown, the builder, or its source assets,
then rebuild; do not hand-edit generated pages. The build records its source-file
hashes, checked local links, and known unavailable historical targets in a report.
The standalone check is `uv run python scripts/documentation/validate_documentation.py`.

## Maintenance checkpoint

After substantial work: update the owning specification or report, relevant task
checkboxes, current status, and roadmap as needed; add a journal entry; rebuild
HTML and inspect the home page and one long document. Do not change dates merely
to make old material appear current.
