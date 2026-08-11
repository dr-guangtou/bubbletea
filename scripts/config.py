"""Central configuration for the BubbleTea project.

All file paths used across the project are defined here.
Import from this module instead of hardcoding paths in scripts.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root (the repository directory)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Core directories
# ---------------------------------------------------------------------------
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = PROJECT_ROOT / "figures"
REFERENCE_DIR = PROJECT_ROOT / "reference"
DOCS_DIR = PROJECT_ROOT / "docs"

# ---------------------------------------------------------------------------
# Data subdirectories
# ---------------------------------------------------------------------------
LITERATURE_DIR = DATA_DIR / "literature"
LITERATURE_DB = LITERATURE_DIR / "database" / "ucd_collection.db"
LITERATURE_REFERENCE_DB_V2 = LITERATURE_DIR / "database" / "ucd_reference_v2.db"
LITERATURE_CATALOGS = LITERATURE_DIR / "catalogs"
LITERATURE_SOURCES = LITERATURE_DIR / "sources"
LITERATURE_VALIDATION = LITERATURE_DIR / "validation"
LITERATURE_DISCOVERY = LITERATURE_DIR / "discovery"
LITERATURE_BENCHMARKS = LITERATURE_DIR / "benchmarks"
VALIDATION_BENCHMARK_LITERATURE_SEARCH = (
    LITERATURE_DISCOVERY / "validation_benchmark_literature_search_2026-07-16.json"
)
EXTRAGALACTIC_REFERENCE_LITERATURE_SEARCH = (
    LITERATURE_DISCOVERY / "extragalactic_contaminant_literature_search_2026-07-17.json"
)
LITERATURE_IMAGE_CUTOUTS = LITERATURE_VALIDATION / "gaia_image_cutouts"
GAIA_CROSSMATCH_EXPORT = LITERATURE_CATALOGS / "all_ucds_gaia_matched.csv"
GAIA_CROSSMATCH_AUDIT = LITERATURE_VALIDATION / "gaia_crossmatch_audit.csv"
LEGACY_CROSSMATCH_EXPORT = LITERATURE_CATALOGS / "all_ucds_legacy_matched.csv"
LEGACY_CROSSMATCH_AUDIT = LITERATURE_VALIDATION / "legacy_crossmatch_audit.csv"
CROSSMATCH_GEOMETRY_VALIDATION = LITERATURE_VALIDATION / "crossmatch_geometry_validation.json"
CANONICAL_GAIA_CROSSMATCH_EXPORT = LITERATURE_CATALOGS / "canonical_gaia_dr3_crossmatch.csv"
CANONICAL_GAIA_CROSSMATCH_AUDIT = LITERATURE_VALIDATION / "canonical_gaia_dr3_crossmatch_audit.csv"
CANONICAL_LEGACY_CROSSMATCH_EXPORT = (
    LITERATURE_CATALOGS / "canonical_legacy_survey_dr10_crossmatch.csv"
)
CANONICAL_LEGACY_CROSSMATCH_AUDIT = (
    LITERATURE_VALIDATION / "canonical_legacy_survey_dr10_crossmatch_audit.csv"
)
CANONICAL_CROSSMATCH_MANIFEST = LITERATURE_SOURCES / "canonical_crossmatch_manifest.json"
CANONICAL_CROSSMATCH_VALIDATION = LITERATURE_VALIDATION / "canonical_crossmatch_validation.json"
PROJECT_STATUS_COUNTS = LITERATURE_VALIDATION / "project_status_counts.json"
PROVENANCE_DOCUMENTATION_VALIDATION = (
    LITERATURE_VALIDATION / "provenance_documentation_validation.json"
)
VALIDATION_BENCHMARK = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v3.csv"
VALIDATION_BENCHMARK_MANIFEST = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v3_manifest.json"
VALIDATION_BENCHMARK_VALIDATION = (
    LITERATURE_VALIDATION / "gaia_validation_benchmark_v3_validation.json"
)
HII_GAIA_ASSOCIATION_CANDIDATES = (
    LITERATURE_VALIDATION / "phangs_muse_gaia_association_candidates.csv"
)
HII_GAIA_ASSOCIATION_CALIBRATION = (
    LITERATURE_VALIDATION / "phangs_muse_gaia_association_calibration.json"
)
DWARF_HII_GAIA_ASSOCIATION_CANDIDATES = (
    LITERATURE_VALIDATION / "van_zee_dwarf_hii_gaia_association_candidates.csv"
)
DWARF_HII_GAIA_ASSOCIATION_CALIBRATION = (
    LITERATURE_VALIDATION / "van_zee_dwarf_hii_gaia_association_calibration.json"
)
VALIDATION_BENCHMARK_SOURCES = LITERATURE_SOURCES / "validation_benchmark_sources.json"
SELECTOR_DEVELOPMENT_FEATURES = LITERATURE_BENCHMARKS / "gaia_selector_development_features_v3.csv"
SELECTOR_DEVELOPMENT_FEATURES_MANIFEST = (
    LITERATURE_BENCHMARKS / "gaia_selector_development_features_v3_manifest.json"
)
SELECTOR_DEVELOPMENT_FEATURE_METRICS = (
    LITERATURE_VALIDATION / "gaia_selector_development_feature_metrics_v3.csv"
)
SELECTOR_DEVELOPMENT_SENSITIVITY = (
    LITERATURE_VALIDATION / "gaia_selector_development_sensitivity_v3.json"
)
SELECTOR_DEVELOPMENT_VALIDATION = (
    LITERATURE_VALIDATION / "gaia_selector_development_validation_v3.json"
)

GALAXY_SAMPLE_DIR = DATA_DIR / "galaxy_sample"
GALAXY_SAMPLE_CSV = GALAXY_SAMPLE_DIR / "galaxy_sample_ranked.csv"

GAIA_QUERIES_DIR = DATA_DIR / "gaia_queries"

RESULTS_DIR = DATA_DIR / "results"
BACKGROUND_RESULTS_DIR = RESULTS_DIR / "background"
BACKGROUND_CONTROL_GEOMETRY_FIXTURE = (
    BACKGROUND_RESULTS_DIR / "background_control_geometry_fixture_v1.csv"
)
BACKGROUND_CONTROL_GEOMETRY_VALIDATION = (
    BACKGROUND_RESULTS_DIR / "background_control_geometry_validation_v1.json"
)
BACKGROUND_REVIEW_HOSTS = BACKGROUND_RESULTS_DIR / "background_review_hosts_v1.csv"
BACKGROUND_REVIEW_HOSTS_MANIFEST = BACKGROUND_RESULTS_DIR / "background_review_hosts_v1.json"
BACKGROUND_FIELD_CONDITIONS_BENCHMARK = (
    BACKGROUND_RESULTS_DIR / "background_field_conditions_benchmark_v1.csv"
)
BACKGROUND_FIELD_CONDITIONS_BENCHMARK_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "background_field_conditions_benchmark_v1.json"
)
BACKGROUND_REVIEW_FIELD_POSITIONS = (
    BACKGROUND_RESULTS_DIR / "background_review_field_positions_v1.csv"
)
BACKGROUND_REVIEW_FIELD_POSITIONS_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "background_review_field_positions_v1.json"
)
BACKGROUND_REVIEW_FIELD_CONDITIONS = (
    BACKGROUND_RESULTS_DIR / "background_review_field_conditions_v1.csv"
)
BACKGROUND_REVIEW_FIELD_CONDITIONS_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "background_review_field_conditions_v1.json"
)
RADIAL_MEASUREMENT_GEOMETRY_AUDIT = (
    BACKGROUND_RESULTS_DIR / "radial_measurement_geometry_audit_v1.csv"
)
RADIAL_MEASUREMENT_GEOMETRY_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "radial_measurement_geometry_audit_v1.json"
)
FIRST_STAGE_HOST_PROFILE_FIXTURE = (
    BACKGROUND_RESULTS_DIR / "first_stage_host_profile_fixture_v1.csv"
)
FIRST_STAGE_HOST_PROFILE_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "first_stage_host_profile_fixture_v1.json"
)
FIRST_STAGE_HOST_PROFILE_COUNT_CONTRACT = (
    BACKGROUND_RESULTS_DIR / "first_stage_host_profile_count_contract_v1.json"
)
FIRST_STAGE_HOST_PROFILE_COUNT_BENCHMARK = (
    BACKGROUND_RESULTS_DIR / "first_stage_host_profile_count_benchmark_v1.json"
)
FIRST_STAGE_HOST_PROFILE_RETRIEVAL_PLAN = (
    BACKGROUND_RESULTS_DIR / "first_stage_host_profile_retrieval_plan_v1.csv"
)
FIRST_STAGE_HOST_PROFILE = BACKGROUND_RESULTS_DIR / "first_stage_host_profile_ngc4698_v1.csv"
FIRST_STAGE_HOST_PROFILE_RUN_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "first_stage_host_profile_ngc4698_v1.json"
)
GAIA_QUERY_PARTITION_SOURCES = BACKGROUND_RESULTS_DIR / "gaia_query_partition_sources_v1.csv"
GAIA_QUERY_PARTITION_STRIPS = BACKGROUND_RESULTS_DIR / "gaia_query_partition_strips_v1.csv"
GAIA_QUERY_PARTITION_VALIDATION = BACKGROUND_RESULTS_DIR / "gaia_query_partition_validation_v1.json"
GAIA_ADAPTIVE_RETRIEVAL_SOURCES = BACKGROUND_RESULTS_DIR / "gaia_adaptive_retrieval_sources_v1.csv"
GAIA_ADAPTIVE_RETRIEVAL_PLAN = BACKGROUND_RESULTS_DIR / "gaia_adaptive_retrieval_plan_v1.csv"
GAIA_ADAPTIVE_RETRIEVAL_VALIDATION = (
    BACKGROUND_RESULTS_DIR / "gaia_adaptive_retrieval_validation_v1.json"
)
GAIA_RESUMABLE_PLANNING_VALIDATION = (
    BACKGROUND_RESULTS_DIR / "gaia_resumable_planning_validation_v1.json"
)
GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK = (
    BACKGROUND_RESULTS_DIR / "gaia_full_selector_retrieval_benchmark_v1.csv"
)
GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "gaia_full_selector_retrieval_benchmark_v1.json"
)
GAIA_FULL_COLUMN_MULTIFIELD_RETRIEVAL = (
    BACKGROUND_RESULTS_DIR / "gaia_full_column_multifield_retrieval_v1.csv"
)
GAIA_FULL_COLUMN_MULTIFIELD_PLAN = (
    BACKGROUND_RESULTS_DIR / "gaia_full_column_multifield_plan_v1.csv"
)
GAIA_FULL_COLUMN_MULTIFIELD_VALIDATION = (
    BACKGROUND_RESULTS_DIR / "gaia_full_column_multifield_validation_v1.json"
)
RADIAL_RING_AREA_ACCOUNTING = (
    BACKGROUND_RESULTS_DIR / "radial_ring_area_accounting_validation_v1.csv"
)
RADIAL_RING_AREA_ACCOUNTING_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "radial_ring_area_accounting_validation_v1.json"
)
HOST_RUN_RECORDS_DIR = BACKGROUND_RESULTS_DIR / "host_run_records_v1"
HOST_RUN_RECORD_INDEX = BACKGROUND_RESULTS_DIR / "host_run_record_index_v1.csv"
HOST_RUN_RECORD_VALIDATION = BACKGROUND_RESULTS_DIR / "host_run_record_validation_v1.json"
OFF_TARGET_FIELD_SPLIT = BACKGROUND_RESULTS_DIR / "off_target_field_split_v1.csv"
OFF_TARGET_FIELD_SPLIT_MANIFEST = BACKGROUND_RESULTS_DIR / "off_target_field_split_v1.json"
OFF_TARGET_DEVELOPMENT_SOURCES = (
    BACKGROUND_RESULTS_DIR / "off_target_development_selector_sources_v1.csv"
)
OFF_TARGET_DEVELOPMENT_SUMMARY = (
    BACKGROUND_RESULTS_DIR / "off_target_development_selector_summary_v1.csv"
)
OFF_TARGET_DEVELOPMENT_MANIFEST = BACKGROUND_RESULTS_DIR / "off_target_development_selector_v1.json"
OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY = (
    BACKGROUND_RESULTS_DIR / "off_target_development_frozen_summary_v1.csv"
)
OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "off_target_development_frozen_summary_v1.json"
)
OFF_TARGET_VALIDATION_SOURCES = (
    BACKGROUND_RESULTS_DIR / "off_target_validation_selector_sources_v1.csv"
)
OFF_TARGET_VALIDATION_SUMMARY = (
    BACKGROUND_RESULTS_DIR / "off_target_validation_selector_summary_v1.csv"
)
OFF_TARGET_VALIDATION_FROZEN_SUMMARY = (
    BACKGROUND_RESULTS_DIR / "off_target_validation_frozen_summary_v1.csv"
)
OFF_TARGET_VALIDATION_MANIFEST = BACKGROUND_RESULTS_DIR / "off_target_validation_selector_v1.json"
LARGE_SKY_FIELD_GRID = BACKGROUND_RESULTS_DIR / "large_sky_field_grid_v1.csv"
LARGE_SKY_FIELD_GRID_MANIFEST = BACKGROUND_RESULTS_DIR / "large_sky_field_grid_v1.json"
LARGE_SKY_DEVELOPMENT_PILOT_FIELDS = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_pilot_fields_v1.csv"
)
LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_pilot_fields_v1.json"
)
LARGE_SKY_DEVELOPMENT_BENCHMARK_PLAN = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_benchmark_plan_v1.csv"
)
LARGE_SKY_DEVELOPMENT_BENCHMARK_SUMMARY = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_benchmark_summary_v1.csv"
)
LARGE_SKY_DEVELOPMENT_BENCHMARK_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_benchmark_v1.json"
)
LARGE_SKY_DEVELOPMENT_RETRIEVAL_PLAN = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_retrieval_plan_v1.csv"
)
LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_retrieval_summary_v1.csv"
)
LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_retrieval_v1.json"
)
LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_field_conditions_v1.csv"
)
LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_field_conditions_v1.json"
)
LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_g_magnitude_summaries_v1.csv"
)
LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_g_magnitude_summaries_v1.json"
)
LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_scale_summary_v1.csv"
)
LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_scale_v1.json"
)
LARGE_SKY_MODEL_COMPARISON_CONTRACT = (
    BACKGROUND_RESULTS_DIR / "large_sky_model_comparison_contract_v1.json"
)
LARGE_SKY_DEVELOPMENT_MODEL_SUMMARY = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_model_summary_v1.csv"
)
LARGE_SKY_DEVELOPMENT_MODEL_FOLD_RESULTS = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_model_fold_results_v1.csv"
)
LARGE_SKY_DEVELOPMENT_MODEL_PREDICTIONS = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_model_predictions_v1.csv"
)
LARGE_SKY_DEVELOPMENT_MODEL_TUNING_RESULTS = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_model_tuning_results_v1.csv"
)
LARGE_SKY_DEVELOPMENT_MODEL_ENVIRONMENT_RESULTS = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_model_environment_results_v1.csv"
)
LARGE_SKY_DEVELOPMENT_MODEL_BAND_RESULTS = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_model_band_results_v1.csv"
)
LARGE_SKY_DEVELOPMENT_MODEL_ARTIFACT = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_model_v1.joblib"
)
LARGE_SKY_DEVELOPMENT_MODEL_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_model_comparison_v1.json"
)
LARGE_SKY_DEVELOPMENT_MODEL_VALIDATION = (
    BACKGROUND_RESULTS_DIR / "large_sky_development_model_validation_v1.json"
)
LARGE_SKY_DIRECT_BACKGROUND_CONTRACT = (
    BACKGROUND_RESULTS_DIR / "large_sky_direct_background_contract_v1.json"
)
LARGE_SKY_DIRECT_BACKGROUND_SUMMARY = (
    BACKGROUND_RESULTS_DIR / "large_sky_direct_background_summary_v1.csv"
)
LARGE_SKY_DIRECT_BACKGROUND_FOLD_RESULTS = (
    BACKGROUND_RESULTS_DIR / "large_sky_direct_background_fold_results_v1.csv"
)
LARGE_SKY_DIRECT_BACKGROUND_PREDICTIONS = (
    BACKGROUND_RESULTS_DIR / "large_sky_direct_background_predictions_v1.csv"
)
LARGE_SKY_DIRECT_BACKGROUND_REFERENCE = (
    BACKGROUND_RESULTS_DIR / "large_sky_direct_background_reference_v1.csv"
)
LARGE_SKY_DIRECT_BACKGROUND_MANIFEST = (
    BACKGROUND_RESULTS_DIR / "large_sky_direct_background_comparison_v1.json"
)
LARGE_SKY_DIRECT_BACKGROUND_VALIDATION = (
    BACKGROUND_RESULTS_DIR / "large_sky_direct_background_validation_v1.json"
)
LARGE_SKY_VALIDATION_RUN_CONTRACT = (
    BACKGROUND_RESULTS_DIR / "large_sky_validation_run_contract_v1.json"
)
LARGE_SKY_VALIDATION_SCALE_SUMMARY = (
    BACKGROUND_RESULTS_DIR / "large_sky_validation_scale_summary_v1.csv"
)
LARGE_SKY_VALIDATION_SCALE_MANIFEST = BACKGROUND_RESULTS_DIR / "large_sky_validation_scale_v1.json"
LARGE_SKY_VALIDATION_REFERENCE = BACKGROUND_RESULTS_DIR / "large_sky_validation_reference_v1.csv"
LARGE_SKY_VALIDATION_EVALUATION = BACKGROUND_RESULTS_DIR / "large_sky_validation_evaluation_v1.json"
KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES = (
    GALAXY_SAMPLE_DIR / "kourkchi_tully_environment_candidates_v1.csv"
)
KOURKCHI_TULLY_ENVIRONMENT_AUDIT = (
    BACKGROUND_RESULTS_DIR / "kourkchi_tully_environment_audit_v1.json"
)
KOURKCHI_TULLY_ENVIRONMENT_VALIDATION = (
    BACKGROUND_RESULTS_DIR / "kourkchi_tully_environment_validation_v1.json"
)
KOURKCHI_TULLY_HALO_EXCLUSION_ANALYSIS = (
    BACKGROUND_RESULTS_DIR / "kourkchi_tully_halo_exclusion_analysis_v1.json"
)
KOURKCHI_TULLY_HALO_EXCLUSION_OUTLIERS = (
    BACKGROUND_RESULTS_DIR / "kourkchi_tully_halo_exclusion_outliers_v1.csv"
)
KOURKCHI_TULLY_2017_PROVENANCE = LITERATURE_SOURCES / "kourkchi_tully_2017_groups.json"
RADIAL_SEARCH_RESULTS_DIR = RESULTS_DIR / "radial_search"
CROSSMATCH_RESULTS_DIR = RESULTS_DIR / "crossmatch"

# ---------------------------------------------------------------------------
# External data (large catalogs not stored in the repo)
#
# Set the BUBBLETEA_EXTERNAL_DATA environment variable to point to the
# directory containing large catalog files (NED-LVS, SGA-2020, CF4, etc.).
# Falls back to data/external/ if not set.
# ---------------------------------------------------------------------------
EXTERNAL_DATA_DIR = Path(os.environ.get("BUBBLETEA_EXTERNAL_DATA", str(DATA_DIR / "external")))
LARGE_SKY_GAIA_RETRIEVAL_DIR = EXTERNAL_DATA_DIR / "bubbletea" / "gaia_large_sky_v1"
FIRST_STAGE_HOST_PROFILE_RETRIEVAL_DIR = EXTERNAL_DATA_DIR / "bubbletea" / "gaia_host_profiles_v1"
EXTRAGALACTIC_REFERENCE_DIR = EXTERNAL_DATA_DIR / "bubbletea" / "extragalactic_reference"
STELLAR_REFERENCE_DIR = EXTERNAL_DATA_DIR / "bubbletea" / "stellar_reference"
ENVIRONMENT_REFERENCE_DIR = EXTERNAL_DATA_DIR / "bubbletea" / "environment_reference"
KOURKCHI_TULLY_2017_DIR = ENVIRONMENT_REFERENCE_DIR / "kourkchi2017"
KOURKCHI_TULLY_2017_MEMBERS = KOURKCHI_TULLY_2017_DIR / "table3.dat.gz"
KOURKCHI_TULLY_2017_GROUPS = KOURKCHI_TULLY_2017_DIR / "table2.dat.gz"
KOURKCHI_TULLY_2017_ASSOCIATIONS = KOURKCHI_TULLY_2017_DIR / "table4.dat"
EXTRAGALACTIC_REFERENCE_SOURCES = LITERATURE_SOURCES / "extragalactic_reference_catalogs.json"
EXTRAGALACTIC_REFERENCE_AUDIT = LITERATURE_VALIDATION / "extragalactic_reference_catalog_audit.json"
GAIA_MORPHOLOGY_HOST_FIELD_SOURCES = (
    LITERATURE_VALIDATION / "gaia_morphology_host_field_sources.csv"
)
GAIA_MORPHOLOGY_HOST_FIELD_RADIAL_METRICS = (
    LITERATURE_VALIDATION / "gaia_morphology_host_field_radial_metrics.csv"
)
GAIA_MORPHOLOGY_HOST_FIELD_MANIFEST = (
    LITERATURE_VALIDATION / "gaia_morphology_host_field_manifest.json"
)
GAIA_MORPHOLOGY_HOST_FIELD_VALIDATION = (
    LITERATURE_VALIDATION / "gaia_morphology_host_field_validation.json"
)
GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN = (
    LITERATURE_VALIDATION / "gaia_morphology_host_control_design.csv"
)
GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_MANIFEST = (
    LITERATURE_VALIDATION / "gaia_morphology_host_control_design_manifest.json"
)
GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_VALIDATION = (
    LITERATURE_VALIDATION / "gaia_morphology_host_control_design_validation.json"
)
GAIA_MORPHOLOGY_HOST_CONTROL_SOURCES = (
    LITERATURE_VALIDATION / "gaia_morphology_host_control_sources.csv"
)
GAIA_MORPHOLOGY_HOST_CONTROL_METRICS = (
    LITERATURE_VALIDATION / "gaia_morphology_host_control_metrics.csv"
)
GAIA_MORPHOLOGY_HOST_CONTROL_FIELD_SUMMARY = (
    LITERATURE_VALIDATION / "gaia_morphology_host_control_field_summary.csv"
)
GAIA_MORPHOLOGY_HOST_CONTROL_COMPARISON = (
    LITERATURE_VALIDATION / "gaia_morphology_host_control_comparison.json"
)
GAIA_MORPHOLOGY_HOST_CONTROL_MANIFEST = (
    LITERATURE_VALIDATION / "gaia_morphology_host_control_manifest.json"
)
GAIA_MORPHOLOGY_HOST_CONTROL_VALIDATION = (
    LITERATURE_VALIDATION / "gaia_morphology_host_control_validation.json"
)
GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH = (
    LITERATURE_VALIDATION / "gaia_morphology_benchmark_crossmatch.csv"
)
GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH_MANIFEST = (
    LITERATURE_VALIDATION / "gaia_morphology_benchmark_crossmatch_manifest.json"
)
GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH_VALIDATION = (
    LITERATURE_VALIDATION / "gaia_morphology_benchmark_crossmatch_validation.json"
)
SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES = (
    LITERATURE_BENCHMARKS / "spectroscopic_stellar_reference_matches_v3.csv"
)
SPECTROSCOPIC_STELLAR_REFERENCE_MANIFEST = (
    LITERATURE_BENCHMARKS / "spectroscopic_stellar_reference_manifest_v3.json"
)
SPECTROSCOPIC_STELLAR_REFERENCE_VALIDATION = (
    LITERATURE_VALIDATION / "spectroscopic_stellar_reference_validation_v3.json"
)
SPECTROSCOPIC_STELLAR_REFERENCE_METRICS = (
    LITERATURE_VALIDATION / "spectroscopic_stellar_reference_feature_metrics_v3.csv"
)
SPECTROSCOPIC_STELLAR_REFERENCE_SUMMARY = (
    LITERATURE_VALIDATION / "spectroscopic_stellar_reference_summary_v3.json"
)
POINT_SOURCE_SELECTOR_COMPONENTS = LITERATURE_VALIDATION / "point_source_selector_components_v3.csv"
POINT_SOURCE_SELECTOR_OPERATING_POINTS = (
    LITERATURE_VALIDATION / "point_source_selector_operating_points_v3.csv"
)
POINT_SOURCE_SELECTOR_CALIBRATION = (
    LITERATURE_VALIDATION / "point_source_selector_calibration_v3.json"
)
POINT_SOURCE_ML_PREDICTIONS = LITERATURE_VALIDATION / "point_source_ml_oof_predictions_v5.csv"
POINT_SOURCE_ML_FOLDS = LITERATURE_VALIDATION / "point_source_ml_fold_metrics_v5.csv"
POINT_SOURCE_ML_COMPARISON = LITERATURE_VALIDATION / "point_source_ml_comparison_v5.json"
POINT_SOURCE_ML_VALIDATION = LITERATURE_VALIDATION / "point_source_ml_comparison_validation_v5.json"
POINT_SOURCE_ML_STABILITY_PREDICTIONS = (
    LITERATURE_VALIDATION / "point_source_ml_stability_predictions_v3.csv"
)
POINT_SOURCE_ML_STABILITY_SOURCE_SUMMARY = (
    LITERATURE_VALIDATION / "point_source_ml_stability_source_summary_v3.csv"
)
POINT_SOURCE_ML_STABILITY_FOLDS = (
    LITERATURE_VALIDATION / "point_source_ml_stability_fold_metrics_v3.csv"
)
POINT_SOURCE_ML_STABILITY_COEFFICIENTS = (
    LITERATURE_VALIDATION / "point_source_ml_stability_coefficients_v3.csv"
)
POINT_SOURCE_ML_STABILITY_COEFFICIENT_SUMMARY = (
    LITERATURE_VALIDATION / "point_source_ml_stability_coefficient_summary_v3.csv"
)
POINT_SOURCE_ML_STABILITY_STRATA = LITERATURE_VALIDATION / "point_source_ml_stability_strata_v3.csv"
POINT_SOURCE_ML_STABILITY_SUMMARY = (
    LITERATURE_VALIDATION / "point_source_ml_stability_summary_v3.json"
)
POINT_SOURCE_ML_STABILITY_VALIDATION = (
    LITERATURE_VALIDATION / "point_source_ml_stability_validation_v3.json"
)
POINT_SOURCE_LOGISTIC_MODEL = LITERATURE_VALIDATION / "point_source_logistic_model_v1.joblib"
POINT_SOURCE_LOGISTIC_MODEL_MANIFEST = LITERATURE_VALIDATION / "point_source_logistic_model_v1.json"

# ---------------------------------------------------------------------------
# Gaia UCD selection criteria (from pilot study)
# ---------------------------------------------------------------------------
SELECTION_CRITERIA = {
    "aen_min": 0.5,  # Astrometric excess noise minimum (mas)
    "bp_rp_min": 0.8,  # BP-RP color minimum
    "bp_rp_max": 1.8,  # BP-RP color maximum
    "g_mag_min": 16.0,  # G-band magnitude minimum
    "g_mag_max": 21.0,  # G-band magnitude maximum
    "pm_max": 2.92,  # Proper motion upper limit (mas/yr)
    "pm_sn_threshold": 3.0,  # PM signal-to-noise threshold (accept if <= this)
    "search_radius_kpc": 300,  # Maximum search radius around galaxies (kpc)
}

# ---------------------------------------------------------------------------
# Background density reference (from pilot study, per deg^2)
# ---------------------------------------------------------------------------
BACKGROUND_DENSITY_BY_GALACTIC_LAT = {
    "20-30": {"mean": 600, "std": 300},
    "30-40": {"mean": 230, "std": 94},
    "40-50": {"mean": 90, "std": 29},
    "50-60": {"mean": 85, "std": 10},
    "60-70": {"mean": 70, "std": 11},
    "70-90": {"mean": 60, "std": 19},
}
