# Documentation guide

[Current status](current_status.md) · [Science guide](science_guide.md) ·
[Roadmap](PLAN.md) · [Scientific requirements](SPEC.md) · [Open issues](todo.md)

## Start here

The HTML entrance is [docs/index.html](index.html). Read current status for where
work stopped, the science guide for what we measure, and the roadmap for what comes
next. SPEC owns approved requirements; detailed reports provide the evidence.

## The six key project documents

Only these Markdown documents belong directly under `docs/`:

| Document | Responsibility |
| --- | --- |
| [current_status.md](current_status.md) | Dated progress, unfinished work, and next research action |
| [science_guide.md](science_guide.md) | Plain-language scientific reading map and key interpretation limits |
| [PLAN.md](PLAN.md) | Scientific roadmap and phase-level status |
| [SPEC.md](SPEC.md) | Approved definitions, scientific requirements, and architecture |
| [todo.md](todo.md) | Cross-phase issues and their resolution requirements |
| [documentation_guide.md](documentation_guide.md) | Document ownership, placement, linking, and maintenance |

The repository [README](../README.md) remains the setup and layout entry point.
Do not create another status summary or roadmap at the same level.

## What belongs in each folder

| Folder | Contents | How to maintain it |
| --- | --- | --- |
| `methods/` | Permanent Gaia feature, contaminant, catalog, radial, and review explanations | Extend the scientific topic owner; cite original sources and distinguish versions |
| `development/` | Implementation notes, experiment records, retrieval benchmarks, debugging, and audits | Extend a consolidated topic record; label dated results and superseded instructions |
| `plans/` | Phase checklists, validation stages, and detailed implementation specifications | Link back to SPEC and the relevant issue; do not create competing scientific policy |
| `teaching/` | Course brief, concepts, example objects, and instructor preparation | Keep the no-code teaching activity separate from research selection and confirmation; start at the [course guide](teaching/README.md) |
| `journal/` | Automatically generated or session-based dated progress records | Preserve the historical record; not a substitute for development documentation |
| `lessons/` | Append-only mistakes, rationale, and safeguards | Follow the existing lesson convention |
| `html/` | Generated reading pages, directory, assets, and build report | Rebuild; never hand-edit generated HTML |

Data provenance stays with [data](../data/README.md), [reference papers](../reference/summary.md),
and figure captions. Do not move those into development notes or restructure the
reference-paper folders for documentation cleanup.

## How these documents connect

```text
README / docs/index.html
    |
    +-- current_status: where we stopped
    +-- science_guide: what the measurements mean
    +-- PLAN: the scientific sequence
         |
         +-- SPEC: approved requirements
         +-- plans/scientific_validation: evidence required
         +-- todo / phase plans: remaining work
              |
              +-- methods: permanent scientific explanations
              +-- development: dated experiments --> scripts, data, figures
              +-- journal: historical session records
```

When documents disagree, distinguish requirements from measurements and compare
their dates. An old development snapshot cannot silently override a later approved
requirement. Current status summarizes evidence; it does not replace it. Ask the
project lead if approved scientific decisions actually conflict.

## Topic owners and reading routes

| Topic | Permanent explanation | Development evidence |
| --- | --- | --- |
| Source selection | [Gaia features](methods/gaia_features.md), [contaminant samples](methods/contaminant_samples.md) | [Selector experiments and validation](development/selector_experiments.md) |
| Extragalactic sources | [Reference catalogs](methods/extragalactic_catalogs.md) | [Catalog stress tests](development/extragalactic_checks.md) |
| Radial measurements | [Radial definitions](methods/radial_measurements.md) | [Retrieval and area](development/retrieval_and_area.md), [host profiles](development/host_pilot_profiles.md) |
| Background comparisons | [Science guide](science_guide.md#4-measure-unrelated-sources-directly) | [Background measurements](development/background_measurements.md), [off-target experiments](development/off_target_controls.md), [geometry history](development/background_geometry.md) |
| Random-field retrieval | [Background tasks](plans/phase_3_background.md) | [Sky retrieval](development/sky_retrieval.md) |
| UCD reference inspection | [Review rules](methods/reference_review.md), [tool specification](plans/ucd_visual_review_tool.md) | [Image-reference preparation](development/reference_imaging.md), [application launch guide](../scripts/phase4_search/ucd_visual_review/README.md) |
| Documentation maintenance | This guide and [site plan](plans/documentation_site.md) | [Consolidation audit](development/documentation_audit.md) |
| Teaching project | [Course guide](teaching/README.md), [instructor guide](teaching/instructor_notes.md), [Part I plan](plans/teaching_part1_redesign.md) | [Teaching implementation and validation](development/teaching_materials.md) |

The [historical project context](development/project_history.md) is retained only
for the July takeover rationale. It is not recommended as the restart entry point.
The [teaching guide](teaching/README.md) owns the separate no-code undergraduate
semester project; its [Part I implementation plan](plans/teaching_part1_redesign.md)
owns the single-file lesson, evidence audits, catalog construction, and acceptance
checks. The guide distinguishes the retained version 1 artifacts from the delivered
Part I redesign, now finalized with bilingual Project Introductions. Teaching shortlists are not
approved research samples or discovery claims.

## Before adding another document

1. Find the existing topic owner in the table above.
2. Add permanent definitions to `methods/`; add implementation or experimental
   detail to the relevant `development/` topic. Do not create a new top-level note.
3. Record dates, input versions, commands, results, limitations, and links to
   artifacts. Distinguish a failed alternative from current practice.
4. Create a new topic document only when the subject genuinely differs; link it
   from this guide and the relevant plan or issue.
5. Keep journal generation separate. Agent operating rules are in [AGENTS](../AGENTS.md)
   and [CLAUDE](../CLAUDE.md), both of which include this placement policy.

## Linking, consolidation, and deletion

Use relative Markdown links and point to the document that owns a statement.
Do not copy whole requirements into competing summaries. Check heading anchors
after a move or merge.

The [consolidation audit](development/documentation_audit.md) records all 47 retired
or relocated files. Its [machine-readable register](development/documentation_migration.json)
stores original hashes, destinations, and retained-section anchors. Unique
scientific content is preserved in dated sections; obsolete standalone entry
points are removed. Journals and lessons remain unchanged. Old historical path
citations can be resolved through the register, and the HTML renderer redirects
links to their retained sections.

Do not delete a document merely because its experiment failed. Remove redundant
files after retaining their unique evidence, and ask the project lead before
discarding scientific or provenance content whose value is uncertain.

The original `BT-023` means probabilistic host association; the accidentally
duplicated M60 task is `BT-031`. Interpret old dated references by their task title.

## Build and check HTML

```bash
uv sync
uv run python scripts/documentation/build_documentation.py
uv run python scripts/documentation/validate_documentation.py
```

Open `docs/index.html`. All generated document pages are under `docs/html/`:
project documents are directly in that folder, scientific and development pages
mirror their source subfolders, and root guides are grouped under `html/project/`.
The directory is `docs/html/directory.html`; shared CSS and JavaScript are in
`docs/html/assets/`. No root `index.html` or root `site/` copy is maintained.

The default build covers root guides and all Markdown under `docs/`, excluding
generated content. Supporting files elsewhere remain source links. Use `--scope all`
only for an explicitly requested expansion. Navigation and styling work without
network access; some scientific evidence requires locally available external data.
Mathematical notation is preserved as source text rather than promising offline
typesetting. This is a reading portal, not the application that saves source reviews.

The build does not query archives, publish a website, or modify scientific data.
Edit Markdown or source assets, rebuild HTML, and inspect the home page and a long
document. After substantial research work, update the owning requirements/report,
task checkboxes, dated status, and roadmap as needed. Do not refresh historical
dates just to make a note appear current.
