"""Benchmark Gaia field-condition measurements on one target and two comparisons."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_FIELD_CONDITIONS_BENCHMARK,
    BACKGROUND_FIELD_CONDITIONS_BENCHMARK_MANIFEST,
    BACKGROUND_REVIEW_HOSTS,
    PROJECT_ROOT,
)
from scripts.phase3_background.control_geometry import (
    constant_galactic_latitude_offset,
    physical_radius_to_angle_deg,
)
from scripts.utils.point_source_selector import MAXIMUM_G_MAGNITUDE, MINIMUM_G_MAGNITUDE

DATA_LAB_TAP_URL = "https://datalab.noirlab.edu/tap"
TEST_PATCH_RADIUS_DEG = 0.1
TEST_GROUP_RADIUS_MULTIPLIER = 2.0
TEST_CENTER_SEPARATION_MULTIPLIER = 1.2


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a local input file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cone_predicate(ra_deg: float, dec_deg: float) -> str:
    """Return a validated Data Lab cone predicate for the test patch."""
    return (
        "'t' = Q3C_RADIAL_QUERY(ra, dec, "
        f"{ra_deg:.12f}, {dec_deg:.12f}, {TEST_PATCH_RADIUS_DEG:.12f})"
    )


def run_field_queries(service: tap.TAPService, field: dict[str, object]) -> dict[str, object]:
    """Measure counts and observation coverage without applying the UCD selector."""
    predicate = cone_predicate(float(field["ra_deg"]), float(field["dec_deg"]))
    aggregate_query = (
        "SELECT COUNT(*) AS source_count, "
        "COUNT(visibility_periods_used) AS visibility_period_count, "
        "SUM(visibility_periods_used) AS visibility_period_sum, "
        "COUNT(astrometric_matched_transits) AS matched_transit_count, "
        "SUM(astrometric_matched_transits) AS matched_transit_sum "
        "FROM gaia_dr3.gaia_source WHERE "
        f"{predicate} AND phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} "
        f"AND {MAXIMUM_G_MAGNITUDE}"
    )
    started = perf_counter()
    aggregate = service.run_sync(aggregate_query, maxrec=10).to_table().to_pandas().iloc[0]
    aggregate_seconds = perf_counter() - started
    low_transit_count_query = (
        "SELECT COUNT(*) AS source_count FROM gaia_dr3.gaia_source WHERE "
        f"{predicate} AND astrometric_matched_transits <= 10 "
        "AND phot_g_mean_mag IS NOT NULL"
    )
    started = perf_counter()
    low_transit_count = int(
        service.run_sync(low_transit_count_query, maxrec=10)
        .to_table()
        .to_pandas()
        .iloc[0]["source_count"]
    )
    low_transit_count_seconds = perf_counter() - started
    low_transit_query = (
        "SELECT phot_g_mean_mag FROM gaia_dr3.gaia_source WHERE "
        f"{predicate} AND astrometric_matched_transits <= 10 "
        "AND phot_g_mean_mag IS NOT NULL"
    )
    started = perf_counter()
    low_transit = (
        service.run_sync(low_transit_query, maxrec=low_transit_count + 1).to_table().to_pandas()
    )
    low_transit_seconds = perf_counter() - started
    valid_magnitudes = low_transit["phot_g_mean_mag"].dropna().astype(float)
    source_count = int(aggregate["source_count"])
    visibility_period_count = int(aggregate["visibility_period_count"])
    matched_transit_count = int(aggregate["matched_transit_count"])
    area_square_deg = (
        2 * np.pi * (1 - np.cos(np.deg2rad(TEST_PATCH_RADIUS_DEG))) * (180 / np.pi) ** 2
    )
    coordinate = SkyCoord(float(field["ra_deg"]) * u.deg, float(field["dec_deg"]) * u.deg)
    return {
        **field,
        "galactic_latitude_deg": coordinate.galactic.b.deg,
        "ecliptic_latitude_deg": coordinate.barycentrictrueecliptic.lat.deg,
        "patch_area_square_deg": area_square_deg,
        "source_count_in_frozen_magnitude_domain": source_count,
        "source_density_per_square_deg": source_count / area_square_deg,
        "visibility_period_non_null_count": visibility_period_count,
        "matched_transit_non_null_count": matched_transit_count,
        "mean_visibility_periods_used": (
            float(aggregate["visibility_period_sum"]) / visibility_period_count
        ),
        "mean_astrometric_matched_transits": (
            float(aggregate["matched_transit_sum"]) / matched_transit_count
        ),
        "low_transit_source_count": low_transit_count,
        "retrieved_low_transit_source_count": len(low_transit),
        "m10_median_g_magnitude": float(valid_magnitudes.median()),
        "aggregate_query_seconds": aggregate_seconds,
        "low_transit_count_query_seconds": low_transit_count_seconds,
        "low_transit_retrieval_seconds": low_transit_seconds,
        "aggregate_query_sha256": hashlib.sha256(aggregate_query.encode()).hexdigest(),
        "low_transit_count_query_sha256": hashlib.sha256(
            low_transit_count_query.encode()
        ).hexdigest(),
        "low_transit_query_sha256": hashlib.sha256(low_transit_query.encode()).hexdigest(),
        "query_contract_uses_selector_output": any(
            term in f"{aggregate_query} {low_transit_count_query} {low_transit_query}".lower()
            for term in (
                "point_source",
                "selector",
                "astrometric_excess_noise_sig",
                "ipd_frac_multi_peak",
                "ipd_gof_harmonic_amplitude",
            )
        ),
    }


def main() -> None:
    """Run the bounded three-patch benchmark and write measured results."""
    review = pd.read_csv(BACKGROUND_REVIEW_HOSTS)
    host = review.loc[review["review_case"].eq("highest_ranked_one_galaxy_catalog_case")].iloc[0]
    host_coordinate = SkyCoord(host["ra"] * u.deg, host["dec"] * u.deg)
    exclusion_radius_deg = physical_radius_to_angle_deg(
        float(host["dist_best"]),
        1000 * TEST_GROUP_RADIUS_MULTIPLIER * float(host["group_second_turnaround_radius_mpc"]),
    )
    center_separation_deg = TEST_CENTER_SEPARATION_MULTIPLIER * (
        exclusion_radius_deg + TEST_PATCH_RADIUS_DEG
    )
    fields = [
        {
            "field_role": "target_test_patch",
            "host_name": host["objname"],
            "ra_deg": host["ra"],
            "dec_deg": host["dec"],
            "center_separation_from_host_deg": 0.0,
        }
    ]
    for direction, direction_name in [(-1, "west_test_patch"), (1, "east_test_patch")]:
        coordinate = constant_galactic_latitude_offset(
            host_coordinate, center_separation_deg, direction
        )
        fields.append(
            {
                "field_role": direction_name,
                "host_name": host["objname"],
                "ra_deg": coordinate.ra.deg,
                "dec_deg": coordinate.dec.deg,
                "center_separation_from_host_deg": center_separation_deg,
            }
        )
    service = tap.TAPService(DATA_LAB_TAP_URL)
    started = perf_counter()
    results = pd.DataFrame([run_field_queries(service, field) for field in fields])
    total_seconds = perf_counter() - started
    BACKGROUND_FIELD_CONDITIONS_BENCHMARK.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(BACKGROUND_FIELD_CONDITIONS_BENCHMARK, index=False)
    checks = {
        "three_test_fields": len(results) == 3,
        "same_galactic_latitude": (
            results["galactic_latitude_deg"] - results.iloc[0]["galactic_latitude_deg"]
        )
        .abs()
        .max()
        <= 1e-10,
        "low_transit_retrieval_complete": results["low_transit_source_count"].tolist()
        == results["retrieved_low_transit_source_count"].tolist(),
        "observation_counts_complete": (
            results["visibility_period_non_null_count"]
            .eq(results["source_count_in_frozen_magnitude_domain"])
            .all()
            and results["matched_transit_non_null_count"]
            .eq(results["source_count_in_frozen_magnitude_domain"])
            .all()
        ),
        "positive_usable_area": results["patch_area_square_deg"].gt(0).all(),
        "no_selector_output_used": ~results["query_contract_uses_selector_output"].any(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    manifest = {
        "benchmark_version": "background_field_conditions_benchmark_v1",
        "benchmark_scope": "one_target_two_comparisons_test_only_no_ucd_selector",
        "generated_at_utc": datetime.now(UTC).isoformat(),
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
        "test_inputs": {
            "patch_radius_deg": TEST_PATCH_RADIUS_DEG,
            "group_radius_multiplier": TEST_GROUP_RADIUS_MULTIPLIER,
            "center_separation_multiplier": TEST_CENTER_SEPARATION_MULTIPLIER,
            "minimum_g_magnitude": MINIMUM_G_MAGNITUDE,
            "maximum_g_magnitude": MAXIMUM_G_MAGNITUDE,
        },
        "host_name": host["objname"],
        "field_count": len(results),
        "total_elapsed_seconds": total_seconds,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    BACKGROUND_FIELD_CONDITIONS_BENCHMARK_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Gaia field-condition benchmark failed: {checks}")


if __name__ == "__main__":
    main()
