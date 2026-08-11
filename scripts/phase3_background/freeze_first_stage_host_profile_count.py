"""Freeze the first large-radius Gaia count query without executing it."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    FIRST_STAGE_HOST_PROFILE_COUNT_CONTRACT,
    FIRST_STAGE_HOST_PROFILE_FIXTURE,
    FIRST_STAGE_HOST_PROFILE_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256, query_sha256
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.query_partition import cone_predicate
from scripts.utils.point_source_selector import MAXIMUM_G_MAGNITUDE, MINIMUM_G_MAGNITUDE

CONTRACT_VERSION = "first_stage_host_profile_count_contract_v1"
EXPECTED_FIXTURE_VERSION = "first_stage_host_profile_fixture_v1"
EXPECTED_BENCHMARK_HOST = "NGC 4698"
EXPECTED_OUTER_RADIUS_KPC = 600
MAXIMUM_ARCHIVE_QUERIES = 1


def count_query(ra_deg: float, dec_deg: float, radius_deg: float) -> str:
    """Return the exact count-only query for the frozen magnitude domain."""
    predicate = cone_predicate(ra_deg, dec_deg, radius_deg)
    return (
        "SELECT COUNT(*) AS source_count FROM gaia_dr3.gaia_source WHERE "
        f"{predicate} AND phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} "
        f"AND {MAXIMUM_G_MAGNITUDE}"
    )


def main() -> None:
    """Write a checked zero-query contract for the first host benchmark."""
    fixture = pd.read_csv(FIRST_STAGE_HOST_PROFILE_FIXTURE)
    fixture_manifest = json.loads(FIRST_STAGE_HOST_PROFILE_MANIFEST.read_text(encoding="utf-8"))
    benchmark_rows = fixture.loc[
        fixture["initial_live_geometry_benchmark"].astype(bool)
        & fixture["outer_radius_kpc"].eq(EXPECTED_OUTER_RADIUS_KPC)
    ]
    if len(benchmark_rows) != 1:
        raise RuntimeError("Expected exactly one frozen 600 kpc benchmark host")
    benchmark = benchmark_rows.iloc[0]
    query = count_query(
        float(benchmark["host_ra_deg"]),
        float(benchmark["host_dec_deg"]),
        float(benchmark["outer_radius_deg"]),
    )
    forbidden_terms = (
        "point_source_logistic",
        "astrometric_excess_noise",
        "ipd_frac_multi_peak",
        "classprob_dsc",
    )
    checks = {
        "fixture_version_is_expected": (
            fixture_manifest["fixture_version"] == EXPECTED_FIXTURE_VERSION
        ),
        "fixture_checks_all_passed": (
            fixture_manifest["passed_count"] == fixture_manifest["check_count"]
        ),
        "fixture_file_matches_manifest": (
            file_sha256(FIRST_STAGE_HOST_PROFILE_FIXTURE) == fixture_manifest["output"]["sha256"]
        ),
        "benchmark_host_is_frozen_ngc_4698": (
            str(benchmark["host_name"]) == EXPECTED_BENCHMARK_HOST
        ),
        "query_reaches_frozen_600_kpc_edge": (
            int(benchmark["outer_radius_kpc"]) == EXPECTED_OUTER_RADIUS_KPC
        ),
        "query_returns_only_one_aggregate_count": query.startswith(
            "SELECT COUNT(*) AS source_count"
        ),
        "query_uses_frozen_magnitude_domain": (
            f"BETWEEN {MINIMUM_G_MAGNITUDE} AND {MAXIMUM_G_MAGNITUDE}" in query
        ),
        "query_does_not_apply_selector_features": not any(
            term in query.lower() for term in forbidden_terms
        ),
        "contract_executes_no_archive_query": True,
        "maximum_live_query_count_is_one": MAXIMUM_ARCHIVE_QUERIES == 1,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    contract = {
        "contract_version": CONTRACT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "frozen_not_executed",
        "plain_language_scope": (
            "Count Gaia sources in the frozen magnitude range inside the NGC 4698 "
            "600 kpc circle. Return one number and no source rows. This measures "
            "archive workload and does not select UCD candidates."
        ),
        "host_name": str(benchmark["host_name"]),
        "host_ra_deg": float(benchmark["host_ra_deg"]),
        "host_dec_deg": float(benchmark["host_dec_deg"]),
        "host_distance_mpc": float(benchmark["host_distance_mpc"]),
        "outer_radius_kpc": int(benchmark["outer_radius_kpc"]),
        "outer_radius_deg": float(benchmark["outer_radius_deg"]),
        "requested_area_square_deg": float(
            fixture.loc[fixture["host_name"].eq(benchmark["host_name"]),][
                "requested_ring_area_square_deg"
            ].sum()
        ),
        "minimum_g_magnitude": MINIMUM_G_MAGNITUDE,
        "maximum_g_magnitude": MAXIMUM_G_MAGNITUDE,
        "query_service": DATA_LAB_TAP_URL,
        "query": query,
        "query_sha256": query_sha256(query),
        "maximum_archive_queries": MAXIMUM_ARCHIVE_QUERIES,
        "source_rows_requested": False,
        "selector_applied": False,
        "scientific_boundaries_changed": False,
        "inputs": [
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "sha256": file_sha256(path),
            }
            for path in (FIRST_STAGE_HOST_PROFILE_FIXTURE, FIRST_STAGE_HOST_PROFILE_MANIFEST)
        ],
        "archive_queries_executed": 0,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    FIRST_STAGE_HOST_PROFILE_COUNT_CONTRACT.write_text(
        json.dumps(contract, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"First-stage count contract failed: {checks}")


if __name__ == "__main__":
    main()
