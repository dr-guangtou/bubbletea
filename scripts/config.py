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
EXTRAGALACTIC_REFERENCE_DIR = EXTERNAL_DATA_DIR / "bubbletea" / "extragalactic_reference"
STELLAR_REFERENCE_DIR = EXTERNAL_DATA_DIR / "bubbletea" / "stellar_reference"
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
