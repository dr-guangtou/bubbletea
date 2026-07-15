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
