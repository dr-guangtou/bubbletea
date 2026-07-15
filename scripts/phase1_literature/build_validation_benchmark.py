"""Build the versioned Gaia-only UCD and contaminant validation benchmark.

The script reads the stabilized literature database, retrieves release-fixed
spectroscopic and non-single-star comparison cohorts, and writes a derived CSV
plus a provenance manifest. It never modifies the reference database.
"""

import argparse
import hashlib
import json
import logging
import sqlite3
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    DWARF_HII_GAIA_ASSOCIATION_CALIBRATION,
    DWARF_HII_GAIA_ASSOCIATION_CANDIDATES,
    HII_GAIA_ASSOCIATION_CALIBRATION,
    HII_GAIA_ASSOCIATION_CANDIDATES,
    LITERATURE_REFERENCE_DB_V2,
    PROJECT_ROOT,
    VALIDATION_BENCHMARK,
    VALIDATION_BENCHMARK_MANIFEST,
    VALIDATION_BENCHMARK_SOURCES,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.synchronize_crossmatch_products import (
    DATALAB_TAP_URL,
    retrieve_gaia_sources,
)

logger = logging.getLogger(__name__)

BENCHMARK_VERSION = "benchmark_v1"
PARTITION_RULESET = "benchmark_partition_v1"
VIZIER_TAP_URL = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap"
SDSS_RANDOM_ID_MINIMUM = 0.0
SDSS_RANDOM_ID_MAXIMUM = 0.1
NSS_SYSTEMATIC_ROW_STRIDE = 500
NSS_SYSTEMATIC_ROW_OFFSET = 1
GAIA_HEALPIX_SOURCE_LEVEL = 12
PARTITION_HEALPIX_LEVEL = 6
VALIDATION_HASH_REMAINDER = 0
PARTITION_HASH_MODULUS = 5
HII_ASSOCIATION_RADIUS_ARCSEC = 0.3
DWARF_HII_ASSOCIATION_RADIUS_ARCSEC = 3.0

NSS_TABLES = [
    "acc7",
    "acc9",
    "linspec1",
    "linspec2",
    "tboasb1c",
    "tboeb",
    "tboes",
    "tbooac",
    "tbooavc",
    "tbooc",
    "tbootsc",
    "tbootsvc",
    "tbosb1",
    "tbosb1c",
    "tbosb2",
    "tbosb2c",
    "vimfl",
]

GAIA_FEATURE_COLUMNS = [
    "source_id",
    "ra",
    "dec",
    "phot_g_mean_mag",
    "phot_bp_mean_mag",
    "phot_rp_mean_mag",
    "parallax",
    "parallax_error",
    "pmra",
    "pmra_error",
    "pmdec",
    "pmdec_error",
    "astrometric_excess_noise",
    "astrometric_excess_noise_sig",
    "ruwe",
    "ipd_frac_multi_peak",
    "ipd_frac_odd_win",
    "duplicated_source",
]


def parse_arguments() -> argparse.Namespace:
    """Parse benchmark paths and bounded smoke-run controls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--source-registry", type=Path, default=VALIDATION_BENCHMARK_SOURCES)
    parser.add_argument("--output", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--manifest", type=Path, default=VALIDATION_BENCHMARK_MANIFEST)
    parser.add_argument(
        "--limit-per-cohort",
        type=int,
        help="Limit each cohort for a measured smoke run; production runs omit this.",
    )
    return parser.parse_args()


def connect_read_only(path: Path) -> sqlite3.Connection:
    """Open the reference database without write permission."""
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def serialize_path(path: Path) -> str:
    """Return a repository-relative path when the file belongs to this project."""
    resolved_path = path.resolve()
    try:
        return str(resolved_path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved_path)


def load_literature_cohort(connection: sqlite3.Connection) -> pd.DataFrame:
    """Load one provenance-bearing row per Gaia-linked canonical object."""
    query = """
        SELECT
            c.canonical_object_id,
            cl.classification_state,
            cl.classification_subtype,
            cl.ruleset_id,
            MIN(r.gaia_dr3_id) AS gaia_dr3_id,
            GROUP_CONCAT(DISTINCT p.bibcode) AS publication_bibcodes,
            GROUP_CONCAT(DISTINCT d.dataset_name) AS dataset_names,
            GROUP_CONCAT(DISTINCT r.source_row_locator) AS source_row_locators
        FROM canonical_objects c
        JOIN object_classifications cl USING (canonical_object_id)
        JOIN object_record_associations a USING (canonical_object_id)
        JOIN literature_records r USING (record_id)
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        WHERE r.gaia_dr3_id IS NOT NULL
        GROUP BY c.canonical_object_id
        ORDER BY c.canonical_object_id
    """
    rows = pd.read_sql_query(query, connection)
    if rows["gaia_dr3_id"].duplicated().any():
        duplicated = rows.loc[rows["gaia_dr3_id"].duplicated(False), "gaia_dr3_id"].unique()
        logger.warning("Literature cohort contains %d shared Gaia source IDs", len(duplicated))
    return rows


def retrieve_gaia_by_identifier(source_ids: list[str]) -> pd.DataFrame:
    """Retrieve Gaia selector inputs for exact release-fixed source identifiers."""
    service = tap.TAPService(DATALAB_TAP_URL)
    sources, _ = retrieve_gaia_sources(service, source_ids)
    return sources


def literature_label_fields(state: str) -> dict[str, object]:
    """Map a v2 classification state to an explicit benchmark role."""
    if state == "confirmed":
        return {
            "label": "ucd",
            "label_subtype": "ucd_confirmed",
            "confidence_tier": "high",
            "primary_label_eligible": True,
            "sensitivity_label_eligible": True,
            "label_basis": "confirmation_rules_v1_positive_spectroscopic_membership",
        }
    if state == "candidate":
        return {
            "label": "ucd",
            "label_subtype": "ucd_candidate",
            "confidence_tier": "uncertain",
            "primary_label_eligible": False,
            "sensitivity_label_eligible": True,
            "label_basis": "source_reported_ucd_candidate_without_approved_confirmation",
        }
    if state == "rejected":
        return {
            "label": "contaminant",
            "label_subtype": "reported_non_ucd_comparison",
            "confidence_tier": "moderate",
            "primary_label_eligible": True,
            "sensitivity_label_eligible": True,
            "label_basis": "source_reported_non_ucd_without_positive_confirmation",
        }
    if state == "uncertain":
        return {
            "label": "uncertain",
            "label_subtype": "ucd_role_conflict",
            "confidence_tier": "conflict",
            "primary_label_eligible": False,
            "sensitivity_label_eligible": True,
            "label_basis": "reported_ucd_role_conflict",
        }
    raise ValueError(f"Unexpected classification state: {state}")


def build_literature_rows(literature: pd.DataFrame, gaia: pd.DataFrame) -> pd.DataFrame:
    """Combine literature labels and Gaia features without changing either source."""
    gaia = gaia.copy()
    gaia["source_id"] = gaia["source_id"].map(lambda value: str(int(value)))
    rows = literature.merge(gaia, left_on="gaia_dr3_id", right_on="source_id", validate="m:1")
    labels = pd.DataFrame(
        [literature_label_fields(state) for state in rows["classification_state"]]
    )
    rows = pd.concat([rows.reset_index(drop=True), labels], axis=1)
    rows["benchmark_id"] = rows["canonical_object_id"].map(lambda value: f"literature:{value}")
    rows["source_cohort"] = "literature_ucd"
    rows["source_object_id"] = rows["canonical_object_id"]
    rows["publication_bibcode"] = rows.pop("publication_bibcodes")
    rows["catalog_id"] = "ucd_reference_v2"
    rows["source_row_locator"] = rows.pop("source_row_locators")
    rows["source_detail"] = rows.pop("dataset_names")
    rows["gaia_association_method"] = "literature_reported_gaia_dr3_id"
    rows["gaia_association_distance_arcsec"] = pd.NA
    shared_source_rows = []
    duplicated_sources = rows.loc[rows["source_id"].duplicated(False), "source_id"].unique()
    for source_id in duplicated_sources:
        group = rows.loc[rows["source_id"] == source_id].copy()
        shared = group.iloc[0].copy()
        canonical_ids = sorted(group["canonical_object_id"].astype(str).unique())
        shared["benchmark_id"] = f"literature_shared_gaia:{source_id}"
        shared["source_object_id"] = source_id
        shared["canonical_object_id"] = ";".join(canonical_ids)
        shared["label"] = "uncertain"
        shared["label_subtype"] = "ambiguous_shared_gaia_distinct_objects"
        shared["confidence_tier"] = "conflict"
        shared["primary_label_eligible"] = False
        shared["sensitivity_label_eligible"] = True
        shared["label_basis"] = "approved_distinct_objects_sharing_one_unresolved_gaia_source"
        shared["classification_state"] = ";".join(
            sorted(group["classification_state"].astype(str).unique())
        )
        shared["source_detail"] = (
            f"canonical_objects={';'.join(canonical_ids)};{shared['source_detail']}"
        )
        shared_source_rows.append(shared)
    if shared_source_rows:
        rows = rows.loc[~rows["source_id"].isin(duplicated_sources)].copy()
        rows = pd.concat([rows, pd.DataFrame(shared_source_rows)], ignore_index=True)
    return rows


def build_literature_benchmark_rows(reference_database: Path) -> pd.DataFrame:
    """Build the Gaia-enriched literature cohort from the read-only database."""
    with connect_read_only(reference_database) as connection:
        literature = load_literature_cohort(connection)
    literature_gaia = retrieve_gaia_by_identifier(literature["gaia_dr3_id"].tolist())
    return build_literature_rows(literature, literature_gaia)


def sdss_query(source_class: str, minimum_g: float, maximum_g: float) -> str:
    """Build the deterministic Gaia-linked clean SDSS spectroscopy query."""
    gaia_columns = ", ".join(f"g.{column}" for column in GAIA_FEATURE_COLUMNS)
    return f"""
        SELECT {gaia_columns}, x.distance AS gaia_association_distance_arcsec,
               s.specobjid, s.class AS spectroscopic_class, s.subclass,
               s.z AS spectroscopic_redshift, s.random_id
        FROM gaia_dr3.x1p5__gaia_source__sdss_dr16__specobj AS x
        JOIN gaia_dr3.gaia_source AS g ON x.id1 = g.source_id
        JOIN sdss_dr16.specobj AS s ON x.id2 = s.specobjid
        WHERE s.scienceprimary = 1
          AND s.zwarning = 0
          AND s.class = '{source_class}'
          AND s.random_id >= {SDSS_RANDOM_ID_MINIMUM}
          AND s.random_id < {SDSS_RANDOM_ID_MAXIMUM}
          AND g.phot_g_mean_mag BETWEEN {minimum_g} AND {maximum_g}
        ORDER BY g.source_id, x.distance, s.specobjid
    """


def retrieve_sdss_rows(minimum_g: float, maximum_g: float) -> tuple[pd.DataFrame, list[str]]:
    """Retrieve deterministic spectroscopic QSO and galaxy comparison rows."""
    service = tap.TAPService(DATALAB_TAP_URL)
    frames = []
    queries = []
    for source_class in ("QSO", "GALAXY"):
        query = sdss_query(source_class, minimum_g, maximum_g)
        queries.append(query)
        frame = service.run_sync(query, maxrec=20_000).to_table().to_pandas()
        frames.append(frame)
    rows = pd.concat(frames, ignore_index=True)
    rows["source_id"] = rows["source_id"].map(lambda value: str(int(value)))
    rows["sdss_gaia_candidate_count"] = rows.groupby("specobjid")["source_id"].transform("nunique")
    rows["gaia_sdss_candidate_count"] = rows.groupby("source_id")["specobjid"].transform("nunique")
    class_counts = rows.groupby("source_id")["spectroscopic_class"].nunique()
    conflicting = set(class_counts[class_counts > 1].index)
    rows = rows.loc[~rows["source_id"].isin(conflicting)].copy()
    rows = rows.sort_values(
        ["specobjid", "gaia_association_distance_arcsec", "source_id"]
    ).drop_duplicates("specobjid", keep="first")
    rows = rows.sort_values(["source_id", "gaia_association_distance_arcsec", "specobjid"])
    rows = rows.drop_duplicates("source_id", keep="first")
    rows["benchmark_id"] = rows.apply(
        lambda row: f"sdss_dr16:{row['spectroscopic_class'].lower()}:{int(row['specobjid'])}",
        axis=1,
    )
    rows["source_cohort"] = rows["spectroscopic_class"].map(
        {"QSO": "sdss_dr16_qso", "GALAXY": "sdss_dr16_galaxy"}
    )
    rows["source_object_id"] = rows["specobjid"].map(lambda value: str(int(value)))
    rows["label"] = "contaminant"
    rows["label_subtype"] = rows["spectroscopic_class"].map(
        {"QSO": "spectroscopic_qso", "GALAXY": "spectroscopic_galaxy"}
    )
    rows["confidence_tier"] = "high"
    rows["primary_label_eligible"] = True
    rows["sensitivity_label_eligible"] = True
    rows["label_basis"] = "sdss_dr16_clean_primary_spectrum_zwarning_zero"
    rows["publication_bibcode"] = "2020ApJS..249....3A"
    rows["catalog_id"] = "SDSS_DR16_specObj_Gaia_DR3_x1p5"
    rows["source_row_locator"] = rows["specobjid"].map(lambda value: f"specobjid={int(value)}")
    rows["source_detail"] = rows.apply(
        lambda row: (
            f"class={row['spectroscopic_class']};subclass={row['subclass']};"
            f"z={row['spectroscopic_redshift']};"
            f"sdss_gaia_candidate_count={int(row['sdss_gaia_candidate_count'])};"
            f"gaia_sdss_candidate_count={int(row['gaia_sdss_candidate_count'])}"
        ),
        axis=1,
    )
    rows["gaia_association_method"] = (
        "nearest_unique_pair_in_noirlab_precomputed_1p5_arcsec_crossmatch"
    )
    rows["canonical_object_id"] = pd.NA
    rows["classification_state"] = pd.NA
    rows["classification_subtype"] = pd.NA
    rows["ruleset_id"] = pd.NA
    return rows, queries


def retrieve_nss_rows(minimum_g: float, maximum_g: float) -> tuple[pd.DataFrame, list[str]]:
    """Retrieve a systematic NSS sample joined to the VizieR Gaia DR3 table."""
    service = tap.TAPService(VIZIER_TAP_URL)
    frames = []
    queries = []
    for table_name in NSS_TABLES:
        query = f"""SELECT
                        n."Source" AS source_id,
                        n."NSSmodel" AS nss_model,
                        n."recno" AS source_record_number,
                        g."RA_ICRS" AS ra,
                        g."DE_ICRS" AS dec,
                        g."Gmag" AS phot_g_mean_mag,
                        g."BPmag" AS phot_bp_mean_mag,
                        g."RPmag" AS phot_rp_mean_mag,
                        g."Plx" AS parallax,
                        g."e_Plx" AS parallax_error,
                        g."pmRA" AS pmra,
                        g."e_pmRA" AS pmra_error,
                        g."pmDE" AS pmdec,
                        g."e_pmDE" AS pmdec_error,
                        g."epsi" AS astrometric_excess_noise,
                        g."sepsi" AS astrometric_excess_noise_sig,
                        g."RUWE" AS ruwe,
                        g."IPDfmp" AS ipd_frac_multi_peak,
                        g."IPDfow" AS ipd_frac_odd_win,
                        g."Dup" AS duplicated_source
                    FROM "I/357/{table_name}" AS n
                    JOIN "I/355/gaiadr3" AS g ON n."Source" = g."Source"
                    WHERE MOD(n."recno", {NSS_SYSTEMATIC_ROW_STRIDE}) = {NSS_SYSTEMATIC_ROW_OFFSET}
                      AND g."Gmag" BETWEEN {minimum_g} AND {maximum_g}
                    ORDER BY source_record_number"""
        queries.append(query)
        logger.info("Retrieving Gaia NSS cohort table I/357/%s", table_name)
        frame = service.run_sync(query, maxrec=10_000).to_table().to_pandas()
        frame["nss_table"] = table_name
        frames.append(frame)
    rows = pd.concat(frames, ignore_index=True)
    rows["source_id"] = rows["source_id"].map(lambda value: str(int(value)))
    rows = rows.sort_values(["source_id", "nss_table", "source_record_number"]).drop_duplicates(
        "source_id"
    )
    rows["benchmark_id"] = rows.apply(
        lambda row: f"gaia_dr3_nss:{row['nss_table']}:{int(row['source_record_number'])}",
        axis=1,
    )
    rows["source_cohort"] = "gaia_dr3_non_single_star"
    rows["source_object_id"] = rows["source_id"]
    rows["label"] = "contaminant"
    rows["label_subtype"] = "gaia_non_single_star"
    rows["confidence_tier"] = "high"
    rows["primary_label_eligible"] = True
    rows["sensitivity_label_eligible"] = True
    rows["label_basis"] = "gaia_dr3_non_single_star_solution"
    rows["publication_bibcode"] = "2023A&A...674A..34G"
    rows["catalog_id"] = rows["nss_table"].map(lambda value: f"I/357/{value}")
    rows["source_row_locator"] = rows.apply(
        lambda row: f"recno={int(row['source_record_number'])};source_id={row['source_id']}",
        axis=1,
    )
    rows["source_detail"] = rows.apply(
        lambda row: f"nss_model={row['nss_model']};nss_table={row['nss_table']}",
        axis=1,
    )
    rows["gaia_association_method"] = "exact_gaia_dr3_source_id"
    rows["gaia_association_distance_arcsec"] = 0.0
    rows["canonical_object_id"] = pd.NA
    rows["classification_state"] = pd.NA
    rows["classification_subtype"] = pd.NA
    rows["ruleset_id"] = pd.NA
    return rows, queries


def build_hii_rows(candidates_path: Path) -> pd.DataFrame:
    """Load approved moderate-confidence PHANGS H II-to-Gaia associations."""
    candidates = pd.read_csv(candidates_path, dtype={"gaia_dr3_id": str})
    rows = candidates.loc[
        candidates["nearest_distance_arcsec"] <= HII_ASSOCIATION_RADIUS_ARCSEC
    ].copy()
    rows["source_id"] = rows["gaia_dr3_id"]
    rows["benchmark_id"] = rows.apply(
        lambda row: f"phangs_muse:{row['galaxy']}:{row['region_id']:g}", axis=1
    )
    rows["source_cohort"] = "phangs_muse_hii"
    rows["source_object_id"] = rows.apply(
        lambda row: f"{row['galaxy']}:{row['region_id']:g}", axis=1
    )
    rows["label"] = "contaminant"
    rows["label_subtype"] = "compact_hii_region"
    rows["confidence_tier"] = "moderate"
    rows["primary_label_eligible"] = True
    rows["sensitivity_label_eligible"] = True
    rows["label_basis"] = "phangs_muse_clean_three_bpt_star_forming_and_calibrated_gaia_association"
    rows["publication_bibcode"] = "2023MNRAS.520.4902G"
    rows["catalog_id"] = "J/MNRAS/520/4902/catalog"
    rows["source_detail"] = rows.apply(
        lambda row: (
            f"galaxy={row['galaxy']};region_id={row['region_id']:g};"
            f"region_area_pixels={row['region_area_pixels']:g};"
            "bpt_nii=star_formation;bpt_sii=star_formation;bpt_oi=star_formation"
        ),
        axis=1,
    )
    rows["gaia_association_method"] = "hii_gaia_association_v1_nearest_within_0p3_arcsec"
    rows["gaia_association_distance_arcsec"] = rows["nearest_distance_arcsec"]
    rows["canonical_object_id"] = pd.NA
    rows["classification_state"] = pd.NA
    rows["classification_subtype"] = pd.NA
    rows["ruleset_id"] = pd.NA
    return rows


def build_dwarf_hii_rows(candidates_path: Path) -> pd.DataFrame:
    """Load approved moderate-confidence dwarf H II-to-Gaia associations."""
    candidates = pd.read_csv(candidates_path, dtype={"gaia_dr3_id": str})
    rows = candidates.loc[
        candidates["nearest_distance_arcsec"] <= DWARF_HII_ASSOCIATION_RADIUS_ARCSEC
    ].copy()
    consolidated_rows = []
    for _, group in rows.groupby("gaia_dr3_id", sort=True):
        group = group.sort_values(["nearest_distance_arcsec", "source_record_numbers"])
        consolidated = group.iloc[0].copy()
        consolidated["source_record_numbers"] = ",".join(group["source_record_numbers"].astype(str))
        consolidated["source_row_locator"] = ";".join(group["source_row_locator"].astype(str))
        consolidated["slit_measurements"] = "|".join(group["slit_measurements"].astype(str))
        consolidated["spectroscopic_measurement_count"] = group[
            "spectroscopic_measurement_count"
        ].sum()
        consolidated["maximum_halpha_to_hbeta"] = group["maximum_halpha_to_hbeta"].max()
        consolidated["maximum_hbeta_flux_1e18_w_m2"] = group["maximum_hbeta_flux_1e18_w_m2"].max()
        consolidated["associated_hii_position_count"] = len(group)
        consolidated["association_distances_arcsec"] = ",".join(
            f"{distance:.12f}" for distance in group["nearest_distance_arcsec"]
        )
        consolidated_rows.append(consolidated)
    rows = pd.DataFrame(consolidated_rows)
    rows["source_id"] = rows["gaia_dr3_id"]
    rows["benchmark_id"] = rows.apply(
        lambda row: f"van_zee_dwarf_hii:{row['galaxy']}:{row['source_record_numbers']}",
        axis=1,
    )
    rows["source_cohort"] = "van_zee_dwarf_hii"
    rows["source_object_id"] = rows.apply(
        lambda row: f"{row['galaxy']}:{row['source_record_numbers']}", axis=1
    )
    rows["label"] = "contaminant"
    rows["label_subtype"] = "dwarf_galaxy_hii_region"
    rows["confidence_tier"] = "moderate"
    rows["primary_label_eligible"] = True
    rows["sensitivity_label_eligible"] = True
    rows["label_basis"] = "van_zee_long_slit_hii_spectroscopy_and_calibrated_gaia_association"
    rows["publication_bibcode"] = "2006ApJ...636..214V"
    rows["catalog_id"] = "J/ApJ/636/214/table3"
    rows["source_detail"] = rows.apply(
        lambda row: (
            f"galaxy={row['galaxy']};"
            f"associated_hii_positions={int(row['associated_hii_position_count'])};"
            f"association_distances_arcsec={row['association_distances_arcsec']};"
            f"slit_measurements={row['slit_measurements']};"
            f"spectroscopic_measurement_count={int(row['spectroscopic_measurement_count'])};"
            f"maximum_halpha_to_hbeta={row['maximum_halpha_to_hbeta']}"
        ),
        axis=1,
    )
    rows["gaia_association_method"] = "dwarf_hii_gaia_association_v1_nearest_within_3p0_arcsec"
    rows["gaia_association_distance_arcsec"] = rows["nearest_distance_arcsec"]
    rows["canonical_object_id"] = pd.NA
    rows["classification_state"] = pd.NA
    rows["classification_subtype"] = pd.NA
    rows["ruleset_id"] = pd.NA
    return rows


def partition_group(source_id: str) -> str:
    """Return the level-6 parent of the Gaia source-ID level-12 HEALPix cell."""
    level_difference = GAIA_HEALPIX_SOURCE_LEVEL - PARTITION_HEALPIX_LEVEL
    source_healpix = int(source_id) >> 35
    parent_healpix = source_healpix >> (2 * level_difference)
    return f"gaia_healpix_level_{PARTITION_HEALPIX_LEVEL}:{parent_healpix}"


def fixed_partition(group: str) -> str:
    """Assign one spatial group using the immutable benchmark_partition_v1 hash."""
    payload = f"{PARTITION_RULESET}|{group}".encode()
    remainder = int(hashlib.sha256(payload).hexdigest()[:16], 16) % PARTITION_HASH_MODULUS
    return "validation" if remainder == VALIDATION_HASH_REMAINDER else "development"


def normalize_output(rows: pd.DataFrame) -> pd.DataFrame:
    """Apply fixed partitions and select the stable benchmark schema."""
    rows = rows.copy()
    rows["gaia_dr3_id"] = rows["source_id"].map(lambda value: str(int(value)))
    rows["partition_group"] = rows["gaia_dr3_id"].map(partition_group)
    rows["partition"] = rows["partition_group"].map(fixed_partition)
    rows["benchmark_version"] = BENCHMARK_VERSION
    rows["partition_ruleset"] = PARTITION_RULESET
    columns = [
        "benchmark_id",
        "benchmark_version",
        "partition_ruleset",
        "source_cohort",
        "source_object_id",
        "canonical_object_id",
        "gaia_dr3_id",
        "label",
        "label_subtype",
        "confidence_tier",
        "primary_label_eligible",
        "sensitivity_label_eligible",
        "label_basis",
        "classification_state",
        "classification_subtype",
        "ruleset_id",
        "partition",
        "partition_group",
        "publication_bibcode",
        "catalog_id",
        "source_row_locator",
        "source_detail",
        "gaia_association_method",
        "gaia_association_distance_arcsec",
        *GAIA_FEATURE_COLUMNS[1:],
    ]
    return rows[columns].sort_values(["source_cohort", "benchmark_id"]).reset_index(drop=True)


def count_mapping(rows: pd.DataFrame, columns: list[str]) -> dict[str, int]:
    """Return stable string-keyed counts for a set of columns."""
    counts = Counter("|".join(map(str, values)) for values in rows[columns].itertuples(False, None))
    return dict(sorted(counts.items()))


def main() -> None:
    """Build the benchmark and write its reproducibility manifest."""
    arguments = parse_arguments()
    if arguments.limit_per_cohort is not None and arguments.limit_per_cohort <= 0:
        raise ValueError("--limit-per-cohort must be positive")
    with arguments.source_registry.open(encoding="utf-8") as input_file:
        source_registry = json.load(input_file)
    if source_registry["benchmark_version"] != BENCHMARK_VERSION:
        raise RuntimeError("Source registry benchmark version does not match the builder")

    literature_rows = build_literature_benchmark_rows(arguments.reference_database)
    minimum_g = float(literature_rows["phot_g_mean_mag"].min())
    maximum_g = float(literature_rows["phot_g_mean_mag"].max())

    sdss_rows, sdss_queries = retrieve_sdss_rows(minimum_g, maximum_g)
    nss_rows, nss_queries = retrieve_nss_rows(minimum_g, maximum_g)
    hii_rows = build_hii_rows(HII_GAIA_ASSOCIATION_CANDIDATES)
    dwarf_hii_rows = build_dwarf_hii_rows(DWARF_HII_GAIA_ASSOCIATION_CANDIDATES)
    existing_gaia_ids = set(
        pd.concat(
            [literature_rows["source_id"], sdss_rows["source_id"], nss_rows["source_id"]],
            ignore_index=True,
        ).astype(str)
    )
    hii_overlap = hii_rows["source_id"].astype(str).isin(existing_gaia_ids)
    hii_overlap_count = int(hii_overlap.sum())
    hii_rows = hii_rows.loc[~hii_overlap].copy()
    existing_gaia_ids.update(hii_rows["source_id"].astype(str))
    dwarf_hii_overlap = dwarf_hii_rows["source_id"].astype(str).isin(existing_gaia_ids)
    dwarf_hii_overlap_count = int(dwarf_hii_overlap.sum())
    dwarf_hii_rows = dwarf_hii_rows.loc[~dwarf_hii_overlap].copy()

    cohorts = [literature_rows, sdss_rows, nss_rows, hii_rows, dwarf_hii_rows]
    if arguments.limit_per_cohort is not None:
        cohorts = [frame.head(arguments.limit_per_cohort).copy() for frame in cohorts]
    benchmark = normalize_output(pd.concat(cohorts, ignore_index=True, sort=False))
    if benchmark["benchmark_id"].duplicated().any():
        raise RuntimeError("Benchmark identifiers are not unique")
    partition_counts = benchmark.groupby("partition_group")["partition"].nunique()
    if (partition_counts != 1).any():
        raise RuntimeError("A spatial partition group crosses benchmark partitions")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    benchmark.to_csv(arguments.output, index=False)
    manifest: dict[str, Any] = {
        "benchmark_version": BENCHMARK_VERSION,
        "partition_ruleset": PARTITION_RULESET,
        "generated_utc": datetime.now(UTC).isoformat(),
        "smoke_limit_per_cohort": arguments.limit_per_cohort,
        "inputs": {
            "reference_database": serialize_path(arguments.reference_database),
            "reference_database_sha256": calculate_sha256(arguments.reference_database),
            "source_registry": serialize_path(arguments.source_registry),
            "source_registry_sha256": calculate_sha256(arguments.source_registry),
            "hii_association_candidates": serialize_path(HII_GAIA_ASSOCIATION_CANDIDATES),
            "hii_association_candidates_sha256": calculate_sha256(HII_GAIA_ASSOCIATION_CANDIDATES),
            "hii_association_calibration": serialize_path(HII_GAIA_ASSOCIATION_CALIBRATION),
            "hii_association_calibration_sha256": calculate_sha256(
                HII_GAIA_ASSOCIATION_CALIBRATION
            ),
            "dwarf_hii_association_candidates": serialize_path(
                DWARF_HII_GAIA_ASSOCIATION_CANDIDATES
            ),
            "dwarf_hii_association_candidates_sha256": calculate_sha256(
                DWARF_HII_GAIA_ASSOCIATION_CANDIDATES
            ),
            "dwarf_hii_association_calibration": serialize_path(
                DWARF_HII_GAIA_ASSOCIATION_CALIBRATION
            ),
            "dwarf_hii_association_calibration_sha256": calculate_sha256(
                DWARF_HII_GAIA_ASSOCIATION_CALIBRATION
            ),
        },
        "applicability_domain": {
            "minimum_phot_g_mean_mag": minimum_g,
            "maximum_phot_g_mean_mag": maximum_g,
            "basis": "complete_observed_literature_gaia_cohort_span",
        },
        "sampling": {
            "sdss_random_id_interval": [SDSS_RANDOM_ID_MINIMUM, SDSS_RANDOM_ID_MAXIMUM],
            "nss_systematic_row_stride": NSS_SYSTEMATIC_ROW_STRIDE,
            "nss_systematic_row_offset": NSS_SYSTEMATIC_ROW_OFFSET,
            "hii_association_radius_arcsec": HII_ASSOCIATION_RADIUS_ARCSEC,
            "hii_rows_excluded_for_existing_gaia_source": hii_overlap_count,
            "dwarf_hii_association_radius_arcsec": DWARF_HII_ASSOCIATION_RADIUS_ARCSEC,
            "dwarf_hii_rows_excluded_for_existing_gaia_source": dwarf_hii_overlap_count,
        },
        "partition": {
            "group": f"Gaia source-ID HEALPix parent at level {PARTITION_HEALPIX_LEVEL}",
            "hash_payload": f"{PARTITION_RULESET}|<partition_group>",
            "hash_prefix_hex_characters": 16,
            "modulus": PARTITION_HASH_MODULUS,
            "validation_remainder": VALIDATION_HASH_REMAINDER,
        },
        "queries": {"sdss_dr16": sdss_queries, "gaia_dr3_nss_vizier": nss_queries},
        "counts": {
            "total_rows": len(benchmark),
            "by_cohort": count_mapping(benchmark, ["source_cohort"]),
            "by_label_role": count_mapping(benchmark, ["label", "label_subtype"]),
            "by_partition_and_label": count_mapping(benchmark, ["partition", "label_subtype"]),
            "primary_label_eligible": int(benchmark["primary_label_eligible"].sum()),
            "sensitivity_label_eligible": int(benchmark["sensitivity_label_eligible"].sum()),
        },
        "deferred_cohorts": {},
        "output": serialize_path(arguments.output),
        "output_sha256": calculate_sha256(arguments.output),
    }
    arguments.manifest.parent.mkdir(parents=True, exist_ok=True)
    arguments.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %d benchmark rows to %s", len(benchmark), arguments.output)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
