"""Measure PHANGS-MUSE H II-to-Gaia separations against displaced controls."""

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    HII_GAIA_ASSOCIATION_CALIBRATION,
    HII_GAIA_ASSOCIATION_CANDIDATES,
    LITERATURE_REFERENCE_DB_V2,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import (
    DATALAB_TAP_URL,
    GAIA_FEATURE_COLUMNS,
    VIZIER_TAP_URL,
    build_literature_benchmark_rows,
    serialize_path,
)
from scripts.utils.crossmatch import build_datalab_cone_predicate

logger = logging.getLogger(__name__)

PHANGS_TABLE = '"J/MNRAS/520/4902/catalog"'
EXPLORATORY_MAXIMUM_RADIUS_ARCSEC = 5.0
CALIBRATION_RADII_ARCSEC = [0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]
CONTROL_OFFSETS_ARCSEC = [
    (30.0, 0.0),
    (-30.0, 0.0),
    (0.0, 30.0),
    (0.0, -30.0),
    (60.0, 0.0),
    (-60.0, 0.0),
    (0.0, 60.0),
    (0.0, -60.0),
]


def parse_arguments() -> argparse.Namespace:
    """Parse output paths and bounded smoke-run controls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--candidates", type=Path, default=HII_GAIA_ASSOCIATION_CANDIDATES)
    parser.add_argument("--calibration", type=Path, default=HII_GAIA_ASSOCIATION_CALIBRATION)
    parser.add_argument("--limit-galaxies", type=int)
    return parser.parse_args()


def retrieve_hii_regions() -> tuple[pd.DataFrame, str]:
    """Retrieve high-confidence star-forming PHANGS nebulae with clean flags."""
    query = f'''SELECT "Galaxy", "RegionID", "RAJ2000", "DEJ2000", "Area",
                       "BPT-NII", "BPT-SII", "BPT-OI", "recno"
                FROM {PHANGS_TABLE}
                WHERE "FlagEdge" = 0 AND "FlagStar" = 0
                  AND "BPT-NII" = 0 AND "BPT-SII" = 0 AND "BPT-OI" = 0
                ORDER BY "Galaxy", "RegionID"'''
    service = tap.TAPService(VIZIER_TAP_URL)
    regions = service.run_sync(query, maxrec=40_000).to_table().to_pandas()
    regions = regions.rename(
        columns={
            "Galaxy": "galaxy",
            "RegionID": "region_id",
            "RAJ2000": "hii_ra",
            "DEJ2000": "hii_dec",
            "Area": "region_area_pixels",
            "BPT-NII": "bpt_nii",
            "BPT-SII": "bpt_sii",
            "BPT-OI": "bpt_oi",
            "recno": "source_record_number",
        }
    )
    return regions, query


def field_geometry(regions: pd.DataFrame) -> tuple[float, float, float]:
    """Return a spherical mean center and covering radius for one PHANGS galaxy."""
    coordinates = SkyCoord(
        regions["hii_ra"].to_numpy() * u.deg, regions["hii_dec"].to_numpy() * u.deg
    )
    cartesian = coordinates.cartesian
    center = SkyCoord(
        x=np.mean(cartesian.x),
        y=np.mean(cartesian.y),
        z=np.mean(cartesian.z),
        representation_type="cartesian",
    ).spherical
    center_coordinate = SkyCoord(center.lon, center.lat)
    covering_radius = float(center_coordinate.separation(coordinates).max().arcsec)
    query_margin = max(
        max(abs(value) for offset in CONTROL_OFFSETS_ARCSEC for value in offset), 0.0
    )
    return float(center.lon.deg), float(center.lat.deg), covering_radius + query_margin + 10.0


def retrieve_gaia_field(
    galaxy: str,
    center_ra: float,
    center_dec: float,
    radius_arcsec: float,
    minimum_g: float,
    maximum_g: float,
) -> tuple[pd.DataFrame, str]:
    """Retrieve all Gaia sources covering the real and displaced PHANGS positions."""
    columns = ", ".join(GAIA_FEATURE_COLUMNS)
    predicate = build_datalab_cone_predicate(center_ra, center_dec, radius_arcsec)
    query = f"""SELECT {columns} FROM gaia_dr3.gaia_source
                WHERE {predicate}
                  AND phot_g_mean_mag BETWEEN {minimum_g} AND {maximum_g}
                ORDER BY source_id"""
    service = tap.TAPService(DATALAB_TAP_URL)
    for attempt in range(1, 5):
        try:
            sources = service.run_sync(query, maxrec=100_000).to_table().to_pandas()
            break
        except Exception:  # noqa: BLE001
            if attempt == 4:
                raise
            delay_seconds = 2**attempt
            logger.warning(
                "%s: Gaia query attempt %d failed; retrying in %d seconds",
                galaxy,
                attempt,
                delay_seconds,
            )
            time.sleep(delay_seconds)
    logger.info("%s: retrieved %d Gaia sources", galaxy, len(sources))
    return sources, query


def nearest_distances(
    target_ra: np.ndarray,
    target_dec: np.ndarray,
    sources: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """Return nearest-source indices and separations for target positions."""
    if sources.empty:
        return np.full(len(target_ra), -1), np.full(len(target_ra), np.inf)
    targets = SkyCoord(target_ra * u.deg, target_dec * u.deg)
    source_coordinates = SkyCoord(
        sources["ra"].to_numpy() * u.deg, sources["dec"].to_numpy() * u.deg
    )
    indices, separations, _ = targets.match_to_catalog_sky(source_coordinates)
    return indices, separations.arcsec


def displaced_coordinates(
    regions: pd.DataFrame, ra_offset_arcsec: float, dec_offset_arcsec: float
) -> tuple[np.ndarray, np.ndarray]:
    """Apply a small tangent-plane offset for local-density control positions."""
    dec = regions["hii_dec"].to_numpy() + dec_offset_arcsec / 3600.0
    ra_scale = np.cos(np.deg2rad(regions["hii_dec"].to_numpy()))
    ra = (regions["hii_ra"].to_numpy() + ra_offset_arcsec / (3600.0 * ra_scale)) % 360.0
    return ra, dec


def build_candidates(regions: pd.DataFrame, sources: pd.DataFrame) -> pd.DataFrame:
    """Attach the nearest Gaia source within the exploratory maximum radius."""
    indices, distances = nearest_distances(
        regions["hii_ra"].to_numpy(), regions["hii_dec"].to_numpy(), sources
    )
    rows = regions.copy()
    rows["nearest_distance_arcsec"] = distances
    rows["within_exploratory_radius"] = distances <= EXPLORATORY_MAXIMUM_RADIUS_ARCSEC
    for column in GAIA_FEATURE_COLUMNS:
        rows[column] = pd.NA
    matched = rows["within_exploratory_radius"].to_numpy()
    if matched.any():
        selected = sources.iloc[indices[matched]].reset_index(drop=True)
        for column in GAIA_FEATURE_COLUMNS:
            rows.loc[matched, column] = selected[column].to_numpy()
    return rows


def main() -> None:
    """Run the separation-control audit without promoting any H II label."""
    arguments = parse_arguments()
    if arguments.limit_galaxies is not None and arguments.limit_galaxies <= 0:
        raise ValueError("--limit-galaxies must be positive")
    literature_rows = build_literature_benchmark_rows(arguments.reference_database)
    minimum_g = float(literature_rows["phot_g_mean_mag"].min())
    maximum_g = float(literature_rows["phot_g_mean_mag"].max())
    regions, phangs_query = retrieve_hii_regions()
    galaxies = sorted(regions["galaxy"].unique())
    if arguments.limit_galaxies is not None:
        galaxies = galaxies[: arguments.limit_galaxies]
        regions = regions.loc[regions["galaxy"].isin(galaxies)].copy()

    candidate_frames = []
    gaia_queries = []
    control_distances: list[float] = []
    real_distances: list[float] = []
    field_counts = []
    for galaxy in galaxies:
        galaxy_regions = regions.loc[regions["galaxy"] == galaxy].copy()
        center_ra, center_dec, radius_arcsec = field_geometry(galaxy_regions)
        sources, query = retrieve_gaia_field(
            galaxy, center_ra, center_dec, radius_arcsec, minimum_g, maximum_g
        )
        gaia_queries.append({"galaxy": galaxy, "query": query})
        candidates = build_candidates(galaxy_regions, sources)
        candidate_frames.append(candidates)
        field_real_distances = candidates["nearest_distance_arcsec"].to_numpy()
        real_distances.extend(field_real_distances.tolist())
        field_control_distances: list[float] = []
        for ra_offset, dec_offset in CONTROL_OFFSETS_ARCSEC:
            control_ra, control_dec = displaced_coordinates(galaxy_regions, ra_offset, dec_offset)
            _, distances = nearest_distances(control_ra, control_dec, sources)
            control_distances.extend(distances.tolist())
            field_control_distances.extend(distances.tolist())
        field_control_array = np.asarray(field_control_distances)
        field_cumulative = []
        for radius in CALIBRATION_RADII_ARCSEC:
            field_real_count = int(np.sum(field_real_distances <= radius))
            field_control_mean = float(
                np.sum(field_control_array <= radius) / len(CONTROL_OFFSETS_ARCSEC)
            )
            field_cumulative.append(
                {
                    "radius_arcsec": radius,
                    "real_match_count": field_real_count,
                    "control_match_mean_per_offset": field_control_mean,
                    "estimated_excess_count": field_real_count - field_control_mean,
                }
            )
        field_counts.append(
            {
                "galaxy": galaxy,
                "hii_region_count": len(galaxy_regions),
                "gaia_source_count": len(sources),
                "query_radius_arcsec": radius_arcsec,
                "cumulative_separation_counts": field_cumulative,
            }
        )

    candidates = pd.concat(candidate_frames, ignore_index=True)
    candidates["gaia_dr3_id"] = candidates["source_id"].map(
        lambda value: str(int(value)) if not pd.isna(value) else None
    )
    candidates["association_status"] = "exploratory_not_approved"
    candidates["source_catalog"] = "J/MNRAS/520/4902/catalog"
    candidates["publication_bibcode"] = "2023MNRAS.520.4902G"
    candidates["source_row_locator"] = candidates["source_record_number"].map(
        lambda value: f"recno={int(value)}"
    )
    arguments.candidates.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(arguments.candidates, index=False)

    real_array = np.asarray(real_distances)
    control_array = np.asarray(control_distances)
    control_count = len(CONTROL_OFFSETS_ARCSEC)
    cumulative = []
    for radius in CALIBRATION_RADII_ARCSEC:
        real_count = int(np.sum(real_array <= radius))
        control_total = int(np.sum(control_array <= radius))
        expected_control = control_total / control_count
        excess = real_count - expected_control
        selected = candidates.loc[candidates["nearest_distance_arcsec"] <= radius]
        unique_source_count = int(selected["gaia_dr3_id"].nunique())
        cumulative.append(
            {
                "radius_arcsec": radius,
                "real_match_count": real_count,
                "unique_gaia_source_count": unique_source_count,
                "repeated_source_assignment_count": real_count - unique_source_count,
                "control_match_total": control_total,
                "control_match_mean_per_offset": expected_control,
                "estimated_excess_count": excess,
                "estimated_excess_fraction": excess / real_count if real_count else None,
            }
        )
    report = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "status": "exploratory_not_approved",
        "publication_bibcode": "2023MNRAS.520.4902G",
        "catalog_id": "J/MNRAS/520/4902/catalog",
        "smoke_limit_galaxies": arguments.limit_galaxies,
        "magnitude_domain": [minimum_g, maximum_g],
        "magnitude_domain_source": serialize_path(arguments.reference_database),
        "quality_rule": "FlagEdge=0, FlagStar=0, and all three BPT flags equal star formation",
        "control_offsets_arcsec": CONTROL_OFFSETS_ARCSEC,
        "exploratory_maximum_radius_arcsec": EXPLORATORY_MAXIMUM_RADIUS_ARCSEC,
        "phangs_query": phangs_query,
        "gaia_queries": gaia_queries,
        "query_sha256": hashlib.sha256(
            json.dumps([phangs_query, gaia_queries], sort_keys=True).encode()
        ).hexdigest(),
        "field_counts": field_counts,
        "cumulative_separation_counts": cumulative,
        "candidate_output": serialize_path(arguments.candidates),
        "candidate_output_sha256": calculate_sha256(arguments.candidates),
    }
    arguments.calibration.parent.mkdir(parents=True, exist_ok=True)
    arguments.calibration.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %d exploratory H II association rows", len(candidates))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
