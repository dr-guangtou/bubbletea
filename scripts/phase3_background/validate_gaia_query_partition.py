"""Validate a non-overlapping strip partition against one complete Gaia query."""

import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_HOSTS,
    GAIA_QUERY_PARTITION_SOURCES,
    GAIA_QUERY_PARTITION_STRIPS,
    GAIA_QUERY_PARTITION_VALIDATION,
    PROJECT_ROOT,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.query_partition import (
    cone_predicate,
    generate_declination_strips,
)
from scripts.utils.point_source_selector import MAXIMUM_G_MAGNITUDE, MINIMUM_G_MAGNITUDE

LOGGER = logging.getLogger(__name__)
TEST_RADIUS_DEG = 0.2
TEST_MAXIMUM_STRIP_HEIGHT_DEG = 0.1


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a local input file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def query_sha256(query: str) -> str:
    """Return the SHA-256 digest of an archive query."""
    return hashlib.sha256(query.encode()).hexdigest()


def magnitude_predicate() -> str:
    """Return the shared bounded-test magnitude predicate."""
    return f"phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} AND {MAXIMUM_G_MAGNITUDE}"


def retrieve_query(service: tap.TAPService, query: str, expected_count: int) -> pd.DataFrame:
    """Retrieve a measured number of rows and fail on truncation."""
    result = service.run_sync(query, maxrec=expected_count + 1).to_table().to_pandas()
    if len(result) != expected_count:
        raise RuntimeError(f"Expected {expected_count} rows but retrieved {len(result)}")
    return result


def main() -> None:
    """Compare one complete cone retrieval with its disjoint strip retrievals."""
    review_hosts = pd.read_csv(BACKGROUND_REVIEW_HOSTS)
    host = review_hosts.loc[
        review_hosts["review_case"].eq("highest_ranked_one_galaxy_catalog_case")
    ].iloc[0]
    predicate = cone_predicate(float(host["ra"]), float(host["dec"]), TEST_RADIUS_DEG)
    base_where = f"{predicate} AND {magnitude_predicate()}"
    reference_count_query = (
        "SELECT COUNT(*) AS source_count FROM gaia_dr3.gaia_source WHERE " + base_where
    )
    reference_query = (
        "SELECT source_id, ra, dec, phot_g_mean_mag FROM gaia_dr3.gaia_source WHERE " + base_where
    )
    strips = generate_declination_strips(
        float(host["dec"]), TEST_RADIUS_DEG, TEST_MAXIMUM_STRIP_HEIGHT_DEG
    )
    service = tap.TAPService(DATA_LAB_TAP_URL)
    started = perf_counter()
    reference_count = int(
        service.run_sync(reference_count_query, maxrec=10)
        .to_table()
        .to_pandas()
        .iloc[0]["source_count"]
    )
    reference = retrieve_query(service, reference_query, reference_count)
    strip_records = []
    strip_sources = []
    for strip in strips:
        strip_where = f"{base_where} AND {strip.dec_predicate()}"
        count_query = (
            "SELECT COUNT(*) AS source_count FROM gaia_dr3.gaia_source WHERE " + strip_where
        )
        source_query = (
            "SELECT source_id, ra, dec, phot_g_mean_mag "
            "FROM gaia_dr3.gaia_source WHERE " + strip_where
        )
        strip_count = int(
            service.run_sync(count_query, maxrec=10).to_table().to_pandas().iloc[0]["source_count"]
        )
        LOGGER.info("Retrieving strip %d with %d measured rows", strip.strip_index, strip_count)
        sources = retrieve_query(service, source_query, strip_count)
        sources.insert(0, "strip_index", strip.strip_index)
        strip_sources.append(sources)
        strip_records.append(
            {
                "strip_index": strip.strip_index,
                "minimum_dec_deg": strip.minimum_dec_deg,
                "maximum_dec_deg": strip.maximum_dec_deg,
                "includes_maximum_dec": strip.includes_maximum_dec,
                "measured_source_count": strip_count,
                "count_query_sha256": query_sha256(count_query),
                "source_query_sha256": query_sha256(source_query),
            }
        )
    combined = pd.concat(strip_sources, ignore_index=True)
    total_seconds = perf_counter() - started
    center = SkyCoord(float(host["ra"]) * u.deg, float(host["dec"]) * u.deg)
    combined_coordinates = SkyCoord(
        combined["ra"].to_numpy() * u.deg, combined["dec"].to_numpy() * u.deg
    )
    reference_ids = set(reference["source_id"].astype("int64"))
    combined_ids = set(combined["source_id"].astype("int64"))
    test_boundary_values = [strips[0].minimum_dec_deg] + [strip.maximum_dec_deg for strip in strips]
    boundary_assignment_counts = [
        sum(strip.contains_dec(value) for strip in strips) for value in test_boundary_values
    ]
    pole_strips = generate_declination_strips(89.95, 0.2, 0.1)
    checks = {
        "reference_contains_sources": reference_count > 0,
        "four_test_strips": len(strips) == 4,
        "strip_counts_sum_to_reference": len(combined) == reference_count,
        "no_source_repeated_between_strips": combined["source_id"].is_unique,
        "source_identifier_sets_match_exactly": combined_ids == reference_ids,
        "all_sources_inside_exact_circle": (
            center.separation(combined_coordinates).deg <= TEST_RADIUS_DEG + 1e-12
        ).all(),
        "every_strip_boundary_assigned_once": boundary_assignment_counts
        == [1] * len(boundary_assignment_counts),
        "circle_at_north_pole_clipped_exactly": (
            pole_strips[0].minimum_dec_deg == 89.75
            and pole_strips[-1].maximum_dec_deg == 90.0
            and pole_strips[-1].includes_maximum_dec
        ),
        "no_selector_output_used": all(
            term not in f"{reference_query} {base_where}".lower()
            for term in (
                "point_source",
                "selector",
                "astrometric_excess_noise_sig",
                "ipd_frac_multi_peak",
            )
        ),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    GAIA_QUERY_PARTITION_SOURCES.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(GAIA_QUERY_PARTITION_SOURCES, index=False)
    pd.DataFrame(strip_records).to_csv(GAIA_QUERY_PARTITION_STRIPS, index=False)
    manifest = {
        "validation_version": "gaia_query_partition_validation_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "validation_scope": "bounded_whole_circle_vs_non_overlapping_declination_strips",
        "data_source": {
            "catalog_release": "Gaia DR3",
            "table": "gaia_dr3.gaia_source",
            "query_service": DATA_LAB_TAP_URL,
            "publication_bibcode": "2023A&A...674A...1G",
            "publication_doi": "10.1051/0004-6361/202243940",
        },
        "input": {
            "path": str(BACKGROUND_REVIEW_HOSTS.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(BACKGROUND_REVIEW_HOSTS),
        },
        "host_name": host["objname"],
        "test_radius_deg": TEST_RADIUS_DEG,
        "test_maximum_strip_height_deg": TEST_MAXIMUM_STRIP_HEIGHT_DEG,
        "reference_source_count": reference_count,
        "strip_count": len(strips),
        "combined_source_count": len(combined),
        "unique_combined_source_count": len(combined_ids),
        "elapsed_seconds": total_seconds,
        "reference_count_query_sha256": query_sha256(reference_count_query),
        "reference_source_query_sha256": query_sha256(reference_query),
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    GAIA_QUERY_PARTITION_VALIDATION.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Gaia query partition validation failed: {checks}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
