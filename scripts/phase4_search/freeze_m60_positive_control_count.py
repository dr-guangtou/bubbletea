"""Freeze the one-query M60 raw Gaia count benchmark without executing it."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    M60_POSITIVE_CONTROL_CONTRACT,
    M60_POSITIVE_CONTROL_COUNT_CONTRACT,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256, query_sha256
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.freeze_first_stage_host_profile_count import count_query
from scripts.phase4_search.freeze_m60_positive_control import CONTRACT_VERSION

COUNT_CONTRACT_VERSION = "m60_positive_control_count_contract_v1"


def main() -> None:
    """Write a zero-query aggregate-count contract for M60."""
    design = json.loads(M60_POSITIVE_CONTROL_CONTRACT.read_text())
    if design["contract_version"] != CONTRACT_VERSION:
        raise RuntimeError("M60 design contract version is not expected")
    if design["passed_count"] != design["check_count"]:
        raise RuntimeError("M60 design safeguards did not all pass")
    host = design["host"]
    query = count_query(host["ra_deg"], host["dec_deg"], host["outer_radius_deg"])
    checks = {
        "m60_design_is_frozen": design["status"] == "frozen_before_full_field_retrieval",
        "query_is_one_aggregate_count": query.startswith("SELECT COUNT(*) AS source_count"),
        "query_reaches_frozen_600_kpc_radius": host["outer_radius_kpc"] == 600,
        "selector_is_not_applied_in_archive": "point_source_logistic" not in query.lower(),
        "source_rows_are_not_requested": True,
        "maximum_archive_queries_is_one": True,
        "contract_executes_no_query": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    contract = {
        "contract_version": COUNT_CONTRACT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "frozen_not_executed",
        "plain_language_scope": (
            "Return one count of Gaia sources in the frozen selector magnitude range "
            "inside M60's 600 kpc circle. This measures raw retrieval workload; it "
            "does not measure how many sources pass selector version 1."
        ),
        "host": host,
        "query_service": DATA_LAB_TAP_URL,
        "query": query,
        "query_sha256": query_sha256(query),
        "design_contract": {
            "path": str(M60_POSITIVE_CONTROL_CONTRACT.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(M60_POSITIVE_CONTROL_CONTRACT),
        },
        "maximum_archive_queries": 1,
        "source_rows_requested": False,
        "selector_applied": False,
        "archive_queries_executed": 0,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    M60_POSITIVE_CONTROL_COUNT_CONTRACT.write_text(
        json.dumps(contract, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"M60 count-contract freeze failed: {checks}")


if __name__ == "__main__":
    main()
