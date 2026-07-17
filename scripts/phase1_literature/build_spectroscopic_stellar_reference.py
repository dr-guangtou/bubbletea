"""Build a blind-safe SDSS spectroscopic stellar reference matched to UCDs.

SDSS spectroscopy supplies the stellar label but does not prove physical
singleness. Matching uses Gaia G magnitude and sky-position summaries only; no
candidate-selector feature is used to retrieve, filter, or match the cohort.
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.table import Table
from pyvo.dal import tap
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    SPECTROSCOPIC_STELLAR_REFERENCE_MANIFEST,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
    STELLAR_REFERENCE_DIR,
    VALIDATION_BENCHMARK,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import serialize_path
from scripts.phase1_literature.synchronize_crossmatch_products import (
    DATALAB_TAP_URL,
    run_query,
)

logger = logging.getLogger(__name__)

REFERENCE_VERSION = "spectroscopic_stellar_reference_v3"
RANDOM_ID_MINIMUM = 0.0
RANDOM_ID_MAXIMUM = 10.0
RANDOM_ID_DOMAIN = [0.0, 100.0]
AUDITED_ASSOCIATION_COUNT = 812_893
AUDITED_ASSOCIATION_COUNT_G_INTERVAL = [14.0992431640625, 21.818605422973633]
CONTROLS_PER_UCD = 3
EXTERNAL_RELATIVE_PATH = "sdss_dr16/gaia_linked_clean_spectroscopic_stars_random_0_10_v2.fits"
GAIA_COLUMNS = [
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
    "pmra_pmdec_corr",
    "astrometric_excess_noise",
    "astrometric_excess_noise_sig",
    "ruwe",
    "ipd_frac_multi_peak",
    "ipd_frac_odd_win",
    "duplicated_source",
    "phot_g_mean_flux_over_error",
    "phot_bp_mean_flux_over_error",
    "phot_rp_mean_flux_over_error",
    "phot_bp_rp_excess_factor",
    "classprob_dsc_combmod_quasar",
    "classprob_dsc_combmod_galaxy",
    "classprob_dsc_combmod_star",
    "in_qso_candidates",
    "in_galaxy_candidates",
    "non_single_star",
]
MATCH_COLUMNS = [
    "phot_g_mean_mag",
    "absolute_galactic_latitude_deg",
    "absolute_ecliptic_latitude_deg",
]
NEAREST_POOL_CANDIDATES_PER_TARGET = 200


def parse_arguments() -> argparse.Namespace:
    """Parse benchmark and output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--external-directory", type=Path, default=STELLAR_REFERENCE_DIR)
    parser.add_argument("--matches", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    parser.add_argument("--manifest", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_MANIFEST)
    parser.add_argument("--reuse-existing-pool", action="store_true")
    return parser.parse_args()


def build_query(excluded_ids: list[str], minimum_g: float, maximum_g: float) -> str:
    """Build the deterministic stellar query with benchmark IDs excluded."""
    columns = ", ".join(f"g.{column}" for column in GAIA_COLUMNS)
    exclusions = ",".join(sorted(excluded_ids, key=int))
    return f"""SELECT {columns}, x.distance AS gaia_association_distance_arcsec,
               s.specobjid, s.class AS spectroscopic_class, s.subclass, s.random_id
        FROM gaia_dr3.x1p5__gaia_source__sdss_dr16__specobj AS x
        JOIN gaia_dr3.gaia_source AS g ON x.id1 = g.source_id
        JOIN sdss_dr16.specobj AS s ON x.id2 = s.specobjid
        WHERE s.scienceprimary = 1 AND s.zwarning = 0 AND s.class = 'STAR'
          AND s.random_id >= {RANDOM_ID_MINIMUM}
          AND s.random_id < {RANDOM_ID_MAXIMUM}
          AND g.phot_g_mean_mag BETWEEN {minimum_g} AND {maximum_g}
          AND g.source_id NOT IN ({exclusions})
        ORDER BY g.source_id, x.distance, s.specobjid"""


def resolve_associations(rows: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Retain the nearest unique Gaia-spectrum association."""
    rows["source_id"] = rows["source_id"].map(lambda value: str(int(value)))
    raw_count = len(rows)
    rows = rows.sort_values(["specobjid", "gaia_association_distance_arcsec", "source_id"])
    rows = rows.drop_duplicates("specobjid", keep="first")
    after_spectrum_resolution = len(rows)
    rows = rows.sort_values(["source_id", "gaia_association_distance_arcsec", "specobjid"])
    rows = rows.drop_duplicates("source_id", keep="first").sort_values("source_id")
    return rows, {
        "raw_association_count": raw_count,
        "after_unique_spectrum_count": after_spectrum_resolution,
        "unique_gaia_source_count": len(rows),
    }


def add_sky_coordinates(frame: pd.DataFrame, ra_column: str, dec_column: str) -> pd.DataFrame:
    """Add Galactic and barycentric-true-ecliptic latitude summaries."""
    result = frame.copy()
    coordinates = SkyCoord(
        result[ra_column].to_numpy(dtype=float) * u.deg,
        result[dec_column].to_numpy(dtype=float) * u.deg,
        frame="icrs",
    )
    result["absolute_galactic_latitude_deg"] = np.abs(coordinates.galactic.b.deg)
    result["ecliptic_latitude_deg"] = coordinates.barycentrictrueecliptic.lat.deg
    result["absolute_ecliptic_latitude_deg"] = np.abs(result["ecliptic_latitude_deg"])
    return result


def match_stars(targets: pd.DataFrame, pool: pd.DataFrame) -> pd.DataFrame:
    """Find three unique minimum-cost stellar controls per development UCD."""
    repeated_targets = targets.loc[targets.index.repeat(CONTROLS_PER_UCD)].reset_index(drop=True)
    combined = pd.concat([repeated_targets[MATCH_COLUMNS], pool[MATCH_COLUMNS]], ignore_index=True)
    scales = combined[MATCH_COLUMNS].std(ddof=0).replace(0, 1.0)
    target_values = repeated_targets[MATCH_COLUMNS].to_numpy(dtype=float) / scales.to_numpy()
    pool_values = pool[MATCH_COLUMNS].to_numpy(dtype=float) / scales.to_numpy()
    tree = cKDTree(pool_values)
    nearest_count = min(NEAREST_POOL_CANDIDATES_PER_TARGET, len(pool))
    _, nearest_indices = tree.query(target_values, k=nearest_count)
    candidate_pool_indices = np.unique(np.asarray(nearest_indices).reshape(-1))
    candidate_values = pool_values[candidate_pool_indices]
    squared_cost = ((target_values[:, None, :] - candidate_values[None, :, :]) ** 2).sum(axis=2)
    target_indices, pool_indices = linear_sum_assignment(squared_cost)
    if len(target_indices) != len(repeated_targets):
        raise RuntimeError("Not every development UCD received its requested controls")
    matched = pool.iloc[candidate_pool_indices[pool_indices]].reset_index(drop=True).copy()
    target_rows = repeated_targets.iloc[target_indices].reset_index(drop=True)
    matched.insert(0, "matched_ucd_gaia_dr3_id", target_rows["gaia_dr3_id"])
    matched.insert(1, "matched_ucd_canonical_object_id", target_rows["canonical_object_id"])
    matched.insert(2, "control_number", matched.groupby("matched_ucd_gaia_dr3_id").cumcount() + 1)
    for column in MATCH_COLUMNS:
        matched[f"matched_ucd_{column}"] = target_rows[column]
        matched[f"difference_{column}"] = matched[column] - target_rows[column]
    return matched


def main() -> None:
    """Retrieve, resolve, match, and record the stellar reference."""
    arguments = parse_arguments()
    benchmark = pd.read_csv(arguments.benchmark, dtype={"gaia_dr3_id": str})
    targets = benchmark.loc[
        benchmark["partition"].eq("development")
        & benchmark["label_subtype"].eq("ucd_confirmed")
        & benchmark["primary_label_eligible"].eq(True)  # noqa: E712
    ].copy()
    excluded_ids = benchmark["gaia_dr3_id"].astype(str).tolist()
    minimum_g = float(benchmark["phot_g_mean_mag"].min())
    maximum_g = float(benchmark["phot_g_mean_mag"].max())
    external_path = arguments.external_directory / EXTERNAL_RELATIVE_PATH
    query = build_query(excluded_ids, minimum_g, maximum_g)

    if arguments.reuse_existing_pool:
        pool = Table.read(external_path, memmap=True).to_pandas()
        pool["source_id"] = pool["source_id"].map(lambda value: str(int(value)))
        for column in ["spectroscopic_class", "subclass"]:
            pool[column] = pool[column].map(
                lambda value: value.decode() if isinstance(value, bytes) else value
            )
        query_seconds = None
        counts = {
            "raw_association_count": None,
            "after_unique_spectrum_count": None,
            "unique_gaia_source_count": len(pool),
        }
    else:
        started = perf_counter()
        rows = run_query(tap.TAPService(DATALAB_TAP_URL), query, maxrec=100_000)
        query_seconds = perf_counter() - started
        pool, counts = resolve_associations(rows)
        external_path.parent.mkdir(parents=True, exist_ok=True)
        Table.from_pandas(pool).write(external_path, overwrite=False)

    targets = add_sky_coordinates(targets, "ra", "dec")
    pool = add_sky_coordinates(pool, "ra", "dec")
    matches = match_stars(targets, pool)
    arguments.matches.parent.mkdir(parents=True, exist_ok=True)
    matches.to_csv(arguments.matches, index=False)

    balance = {}
    for column in MATCH_COLUMNS:
        difference = matches[f"difference_{column}"].abs()
        balance[column] = {
            "median_absolute_difference": float(difference.median()),
            "maximum_absolute_difference": float(difference.max()),
        }
    manifest = {
        "reference_version": REFERENCE_VERSION,
        "generated_utc": datetime.now(UTC).isoformat(),
        "label": "sdss_dr16_clean_primary_spectroscopic_star",
        "singleness_status": "not_established",
        "role": "development_only_stellar_reference_supplement",
        "validation_partition_inspected": False,
        "selector_features_used_for_selection_or_matching": [],
        "matching_variables": MATCH_COLUMNS,
        "controls_per_ucd": CONTROLS_PER_UCD,
        "nearest_pool_candidates_per_target": NEAREST_POOL_CANDIDATES_PER_TARGET,
        "provenance": {
            "publication_bibcode": "2020ApJS..249....3A",
            "doi": "10.3847/1538-4365/ab929e",
            "endpoint": DATALAB_TAP_URL,
            "random_id_domain": RANDOM_ID_DOMAIN,
            "random_id_interval": [RANDOM_ID_MINIMUM, RANDOM_ID_MAXIMUM],
            "audited_association_count": AUDITED_ASSOCIATION_COUNT,
            "audited_association_count_g_interval": AUDITED_ASSOCIATION_COUNT_G_INTERVAL,
            "audited_count_warning": (
                "The count uses the earlier expanded-extragalactic G interval, not the "
                "current stellar-pool query interval; it documents archive scale only."
            ),
            "query_sha256": hashlib.sha256(query.encode()).hexdigest(),
            "query": query,
            "query_seconds": query_seconds,
        },
        "inputs": {
            "benchmark": serialize_path(arguments.benchmark),
            "benchmark_sha256": calculate_sha256(arguments.benchmark),
        },
        "counts": {
            **counts,
            "excluded_benchmark_identifier_count": len(excluded_ids),
            "development_confirmed_ucd_count": len(targets),
            "matched_stellar_control_count": len(matches),
            "unique_matched_stellar_control_count": matches["source_id"].nunique(),
        },
        "balance": balance,
        "external_pool": str(Path(EXTERNAL_RELATIVE_PATH)),
        "external_pool_file_size_bytes": external_path.stat().st_size,
        "external_pool_sha256": calculate_sha256(external_path),
        "matches": serialize_path(arguments.matches),
        "matches_sha256": calculate_sha256(arguments.matches),
    }
    arguments.manifest.parent.mkdir(parents=True, exist_ok=True)
    arguments.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %d unique matched stellar controls", len(matches))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
