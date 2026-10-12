# Documentation consolidation audit

**Date:** 2026-10-12  
**Original checkpoint:** `9dd2569`  
**Scope:** Documentation organization only; no scientific data or classification changes.

[Documentation guide](../documentation_guide.md) · [Science guide](../science_guide.md) · [Current status](../current_status.md)

## Decisions

- Keep six project-level Markdown documents directly in `docs/`: SPEC, PLAN,
  current status, issue register, documentation guide, and science guide.
- Move permanent feature, contaminant, catalog, and radial definitions to `methods/`.
- Merge 42 development reports into ten topic records. Preserve each report's
  unique scientific content and original-date limitations in a labelled section;
  the section wrappers distinguish past decisions from current reading guidance.
- Retire the July CONTEXT entry point into project history. Its stale setup and
  next-step instructions are no longer recommended; current status replaces that role.
- Remove the 47 old standalone files only after their content is retained below.
  No unique measurement or provenance is deliberately discarded. Git retains the
  original checkpoint, and the register stores original source hashes.
- Keep journals and lessons unchanged. Existing historical path citations can be
  resolved with this table and the HTML renderer's migration register.
- Keep the unreferenced HSC example image and legacy SQL in development assets,
  not at the project-document level. They are historical examples, not active pipeline inputs.
- Place the HTML entrance at `docs/index.html` and all generated pages/assets at
  `docs/html/`. Remove the obsolete root index and root site copies.
- Future development notes extend these topic records instead of creating another
  top-level report. This rule is persisted in AGENTS.md and CLAUDE.md.

## Closeout preservation correction

The 2026-10-12 closeout adds a new journal and appends a lesson; it does not rewrite
historical journals or lessons. The validator now checks each original journal
byte-for-byte and requires the original lesson bytes to remain an unchanged prefix,
while allowing new files. The former directory-wide diff would incorrectly reject
normal additions. Rebuild the portal after each addition; current source/page
counts and navigation results are recorded in `docs/html/build_report.json`.

## Disposition of every relocated or merged Markdown document

The five existing project-level owners were retained: `PLAN.md` (roadmap),
`SPEC.md` (approved requirements), `current_status.md` (dated status), `todo.md`
(issues), and `documentation_guide.md` (organization). The sixth,
`science_guide.md`, is a new plain-language reading map, not a competing specification.

“Merge” removes the former standalone file but keeps its content in a dated section.
“Relocate definitions” preserves a permanent scientific explanation below methods.
“Retire entry point” keeps the old context only as historical evidence.

| Original path | Action | New owner and retained section |
| --- | --- | --- |
| `docs/point_source_selector_calibration.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-point_source_selector_calibration) |
| `docs/point_source_ml_comparison.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-point_source_ml_comparison) |
| `docs/point_source_ml_stability.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-point_source_ml_stability) |
| `docs/point_source_ml_stability_v2.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-point_source_ml_stability_v2) |
| `docs/point_source_ml_v2_failure_audit.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-point_source_ml_v2_failure_audit) |
| `docs/logistic_regularization_sensitivity.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-logistic_regularization_sensitivity) |
| `docs/frozen_c1000_persistent_ucd_audit.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-frozen_c1000_persistent_ucd_audit) |
| `docs/point_source_logistic_model_v1.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-point_source_logistic_model_v1) |
| `docs/point_source_selector_integration_v1.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-point_source_selector_integration_v1) |
| `docs/point_source_logistic_validation_v1.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-point_source_logistic_validation_v1) |
| `docs/point_source_astrometric_rejection_assessment_v1.md` | merge | [selector_experiments.md](../development/selector_experiments.md#record-point_source_astrometric_rejection_assessment_v1) |
| `docs/gaia_query_partition_validation.md` | merge | [retrieval_and_area.md](../development/retrieval_and_area.md#record-gaia_query_partition_validation) |
| `docs/gaia_adaptive_retrieval_validation.md` | merge | [retrieval_and_area.md](../development/retrieval_and_area.md#record-gaia_adaptive_retrieval_validation) |
| `docs/gaia_full_selector_retrieval_benchmark.md` | merge | [retrieval_and_area.md](../development/retrieval_and_area.md#record-gaia_full_selector_retrieval_benchmark) |
| `docs/gaia_full_column_multifield_validation.md` | merge | [retrieval_and_area.md](../development/retrieval_and_area.md#record-gaia_full_column_multifield_validation) |
| `docs/radial_ring_area_accounting.md` | merge | [retrieval_and_area.md](../development/retrieval_and_area.md#record-radial_ring_area_accounting) |
| `docs/host_run_records.md` | merge | [retrieval_and_area.md](../development/retrieval_and_area.md#record-host_run_records) |
| `docs/background_field_conditions_benchmark.md` | merge | [off_target_controls.md](../development/off_target_controls.md#record-background_field_conditions_benchmark) |
| `docs/background_review_field_conditions.md` | merge | [off_target_controls.md](../development/off_target_controls.md#record-background_review_field_conditions) |
| `docs/off_target_field_split.md` | merge | [off_target_controls.md](../development/off_target_controls.md#record-off_target_field_split) |
| `docs/off_target_development_selector.md` | merge | [off_target_controls.md](../development/off_target_controls.md#record-off_target_development_selector) |
| `docs/off_target_development_summary.md` | merge | [off_target_controls.md](../development/off_target_controls.md#record-off_target_development_summary) |
| `docs/off_target_validation_selector.md` | merge | [off_target_controls.md](../development/off_target_controls.md#record-off_target_validation_selector) |
| `docs/large_sky_field_grid.md` | merge | [sky_retrieval.md](../development/sky_retrieval.md#record-large_sky_field_grid) |
| `docs/large_sky_development_pilot.md` | merge | [sky_retrieval.md](../development/sky_retrieval.md#record-large_sky_development_pilot) |
| `docs/large_sky_development_retrieval.md` | merge | [sky_retrieval.md](../development/sky_retrieval.md#record-large_sky_development_retrieval) |
| `docs/large_sky_development_field_conditions.md` | merge | [sky_retrieval.md](../development/sky_retrieval.md#record-large_sky_development_field_conditions) |
| `docs/large_sky_development_scale.md` | merge | [sky_retrieval.md](../development/sky_retrieval.md#record-large_sky_development_scale) |
| `docs/large_sky_model_comparison_contract.md` | merge | [background_measurements.md](../development/background_measurements.md#record-large_sky_model_comparison_contract) |
| `docs/large_sky_development_model_comparison.md` | merge | [background_measurements.md](../development/background_measurements.md#record-large_sky_development_model_comparison) |
| `docs/large_sky_direct_background_comparison.md` | merge | [background_measurements.md](../development/background_measurements.md#record-large_sky_direct_background_comparison) |
| `docs/large_sky_validation_run.md` | merge | [background_measurements.md](../development/background_measurements.md#record-large_sky_validation_run) |
| `docs/background_control_design.md` | merge | [background_geometry.md](../development/background_geometry.md#record-background_control_design) |
| `docs/kourkchi_tully_environment_audit.md` | merge | [background_geometry.md](../development/background_geometry.md#record-kourkchi_tully_environment_audit) |
| `docs/gaia_morphology_host_field_stress.md` | merge | [extragalactic_checks.md](../development/extragalactic_checks.md#record-gaia_morphology_host_field_stress) |
| `docs/gaia_morphology_host_control_comparison.md` | merge | [extragalactic_checks.md](../development/extragalactic_checks.md#record-gaia_morphology_host_control_comparison) |
| `docs/gaia_morphology_ucd_crossmatch.md` | merge | [extragalactic_checks.md](../development/extragalactic_checks.md#record-gaia_morphology_ucd_crossmatch) |
| `docs/first_stage_host_profile_fixture.md` | merge | [host_pilot_profiles.md](../development/host_pilot_profiles.md#record-first_stage_host_profile_fixture) |
| `docs/first_stage_ngc4698_candidate_diagnostics.md` | merge | [host_pilot_profiles.md](../development/host_pilot_profiles.md#record-first_stage_ngc4698_candidate_diagnostics) |
| `docs/m60_positive_control.md` | merge | [host_pilot_profiles.md](../development/host_pilot_profiles.md#record-m60_positive_control) |
| `docs/ucd_legacy_survey_reference.md` | merge | [reference_imaging.md](../development/reference_imaging.md#record-ucd_legacy_survey_reference) |
| `docs/CONTEXT.md` | retire entry point | [project_history.md](../development/project_history.md#record-CONTEXT) |
| `docs/gaia_selector_features.md` | relocate definitions | [gaia_features.md](../methods/gaia_features.md#record-gaia_selector_features) |
| `docs/contaminant_benchmark.md` | merge definitions | [contaminant_samples.md](../methods/contaminant_samples.md#record-contaminant_benchmark) |
| `docs/spectroscopic_stellar_reference.md` | merge definitions | [contaminant_samples.md](../methods/contaminant_samples.md#record-spectroscopic_stellar_reference) |
| `docs/extragalactic_contaminant_catalogs.md` | relocate definitions | [extragalactic_catalogs.md](../methods/extragalactic_catalogs.md#record-extragalactic_contaminant_catalogs) |
| `docs/radial_measurement_design.md` | relocate definitions | [radial_measurements.md](../methods/radial_measurements.md#record-radial_measurement_design) |

## Machine-readable traceability

[documentation_migration.json](documentation_migration.json) records original
paths, source SHA-256 hashes, destination paths, and stable section anchors. The
original content is recoverable with `git show 9dd2569:path/to/original.md`.
Reorganization changes heading depth and relative document links mechanically;
measurements, commands, tables, and caveats are retained. A separate preservation
check compares these transformations against the original source reports.

## Review and next step

The revised 58-document, 60-page build passed 278 checks, including original-source
hashes, preservation of scientific text and commands, migration routing, source
coverage, and generated local links. No unavailable links or unresolved fragments
were found. Two builds produced identical content for all 62 HTML and asset files.
Scoped Ruff and pre-commit checks passed. No scientific data, figures, source-paper
packages, journals, or lessons were changed.

The project lead approved the existing website appearance. Rebuild the relocated
portal and validate links, source coverage, all retained report sections, unchanged
journals, and the six-document top-level policy. Review the science guide and this
disposition table before beginning the separate observational-astronomy teaching brief.

