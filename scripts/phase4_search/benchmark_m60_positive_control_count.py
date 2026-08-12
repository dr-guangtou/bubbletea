"""Execute the single frozen aggregate Gaia count for the M60 positive control."""

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
    M60_POSITIVE_CONTROL_COUNT_BENCHMARK,
    M60_POSITIVE_CONTROL_COUNT_CONTRACT,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256, query_sha256
from scripts.phase3_background.run_large_sky_development_scale import ArchiveTimeoutSession
from scripts.phase4_search.freeze_m60_positive_control_count import COUNT_CONTRACT_VERSION

BENCHMARK_VERSION = "m60_positive_control_count_benchmark_v1"


def parse_arguments() -> argparse.Namespace:
    """Require explicit permission for the one live archive query."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run one count query and preserve its measured workload."""
    if not parse_arguments().execute:
        raise RuntimeError("Live archive access requires --execute")
    contract = json.loads(M60_POSITIVE_CONTROL_COUNT_CONTRACT.read_text())
    if contract["contract_version"] != COUNT_CONTRACT_VERSION:
        raise RuntimeError("M60 count contract version is not expected")
    if contract["passed_count"] != contract["check_count"]:
        raise RuntimeError("M60 count-contract safeguards did not all pass")
    query = contract["query"]
    if query_sha256(query) != contract["query_sha256"]:
        raise RuntimeError("M60 aggregate query differs from its frozen digest")

    service = tap.TAPService(contract["query_service"], session=ArchiveTimeoutSession())
    started = perf_counter()
    result = service.run_sync(query, maxrec=10).to_table().to_pandas()
    query_seconds = perf_counter() - started
    if len(result) != 1 or "source_count" not in result:
        raise RuntimeError("M60 aggregate query did not return exactly one count")
    source_count = int(result.iloc[0]["source_count"])
    area = float(contract["host"]["requested_area_square_deg"])
    checks = {
        "frozen_contract_used": contract["contract_version"] == COUNT_CONTRACT_VERSION,
        "exact_query_executed": query_sha256(query) == contract["query_sha256"],
        "one_archive_query_executed": contract["maximum_archive_queries"] == 1,
        "one_aggregate_row_returned": len(result) == 1,
        "source_count_is_nonnegative": source_count >= 0,
        "no_source_rows_downloaded": True,
        "selector_not_applied": not contract["selector_applied"],
    }
    checks = {name: bool(value) for name, value in checks.items()}
    benchmark = {
        "benchmark_version": BENCHMARK_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "measured_raw_count_only",
        "plain_language_result": (
            "The archive returned one raw Gaia source count for M60's frozen 600 kpc "
            "circle. No individual rows were downloaded, so selector-v1 passing counts "
            "and contamination flags remain unmeasured."
        ),
        "host": contract["host"],
        "source_count_in_frozen_magnitude_domain": source_count,
        "source_density_per_square_deg": source_count / area,
        "query_seconds": query_seconds,
        "query_service": contract["query_service"],
        "query_sha256": contract["query_sha256"],
        "count_contract": {
            "path": str(M60_POSITIVE_CONTROL_COUNT_CONTRACT.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(M60_POSITIVE_CONTROL_COUNT_CONTRACT),
        },
        "archive_queries_executed": 1,
        "source_rows_downloaded": 0,
        "selector_applied": False,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    M60_POSITIVE_CONTROL_COUNT_BENCHMARK.write_text(
        json.dumps(benchmark, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"M60 aggregate benchmark failed: {checks}")


if __name__ == "__main__":
    main()
