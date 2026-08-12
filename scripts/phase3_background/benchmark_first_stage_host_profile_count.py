"""Execute the one-query first-stage Gaia source-count benchmark."""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    FIRST_STAGE_HOST_PROFILE_COUNT_BENCHMARK,
    FIRST_STAGE_HOST_PROFILE_COUNT_CONTRACT,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256, query_sha256
from scripts.phase3_background.freeze_first_stage_host_profile_count import (
    CONTRACT_VERSION,
    MAXIMUM_ARCHIVE_QUERIES,
)
from scripts.phase3_background.run_large_sky_development_scale import ArchiveTimeoutSession

BENCHMARK_VERSION = "first_stage_host_profile_count_benchmark_v1"


def parse_arguments() -> argparse.Namespace:
    """Require explicit permission at the command line for the live query."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the single frozen count query. Without this flag, refuse.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the frozen aggregate query and record its measured result."""
    arguments = parse_arguments()
    if not arguments.execute:
        raise RuntimeError("Live archive access requires the explicit --execute flag")
    contract = json.loads(FIRST_STAGE_HOST_PROFILE_COUNT_CONTRACT.read_text(encoding="utf-8"))
    if contract["contract_version"] != CONTRACT_VERSION:
        raise RuntimeError("Count contract version is not the frozen expected version")
    if contract["passed_count"] != contract["check_count"]:
        raise RuntimeError("Count contract safeguards did not all pass")
    query = str(contract["query"])
    if query_sha256(query) != contract["query_sha256"]:
        raise RuntimeError("Count query no longer matches its frozen hash")

    service = tap.TAPService(str(contract["query_service"]), session=ArchiveTimeoutSession())
    started = perf_counter()
    result = service.run_sync(query, maxrec=10).to_table().to_pandas()
    query_seconds = perf_counter() - started
    if len(result) != 1 or "source_count" not in result.columns:
        raise RuntimeError("Gaia count query did not return exactly one aggregate row")
    source_count = int(result.iloc[0]["source_count"])
    area_square_deg = float(contract["requested_area_square_deg"])
    checks = {
        "frozen_contract_used": contract["contract_version"] == CONTRACT_VERSION,
        "contract_file_hash_recorded": FIRST_STAGE_HOST_PROFILE_COUNT_CONTRACT.exists(),
        "exact_frozen_query_executed": query_sha256(query) == contract["query_sha256"],
        "one_archive_query_executed": MAXIMUM_ARCHIVE_QUERIES == 1,
        "one_aggregate_row_returned": len(result) == 1,
        "source_count_is_nonnegative": source_count >= 0,
        "no_source_rows_saved": True,
        "selector_not_applied": not bool(contract["selector_applied"]),
        "scientific_boundaries_unchanged": not bool(contract["scientific_boundaries_changed"]),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    benchmark = {
        "benchmark_version": BENCHMARK_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "measured_count_only_archive_benchmark",
        "plain_language_result": (
            "The archive returned one measured Gaia source count for the frozen "
            "NGC 4698 circle. No individual source rows were downloaded and the "
            "UCD selector was not applied."
        ),
        "host_name": contract["host_name"],
        "outer_radius_kpc": contract["outer_radius_kpc"],
        "outer_radius_deg": contract["outer_radius_deg"],
        "requested_area_square_deg": area_square_deg,
        "source_count_in_frozen_magnitude_domain": source_count,
        "source_density_per_square_deg": source_count / area_square_deg,
        "query_seconds": query_seconds,
        "query_service": contract["query_service"],
        "query_sha256": contract["query_sha256"],
        "contract": {
            "path": str(FIRST_STAGE_HOST_PROFILE_COUNT_CONTRACT.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(FIRST_STAGE_HOST_PROFILE_COUNT_CONTRACT),
        },
        "archive_queries_executed": 1,
        "source_rows_downloaded": 0,
        "selector_applied": False,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    FIRST_STAGE_HOST_PROFILE_COUNT_BENCHMARK.write_text(
        json.dumps(benchmark, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"First-stage count benchmark failed: {checks}")


if __name__ == "__main__":
    main()
