"""Benchmark bounded Gaia retrievals with every frozen-selector input column."""

import hashlib
import json
import logging
import resource
import sys
import tracemalloc
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_HOSTS,
    GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK,
    GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256, query_sha256
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.query_partition import cone_predicate
from scripts.utils.point_source_selector import (
    MAXIMUM_G_MAGNITUDE,
    MINIMUM_G_MAGNITUDE,
    RAW_GAIA_COLUMNS,
    SELECTOR_VERSION,
    load_frozen_selector,
)

LOGGER = logging.getLogger(__name__)
TEST_RADIUS_DEG = 0.5
TEST_ROW_COUNTS = (100, 500, 1000, 2500, 5000, 10000)
TEST_REPEAT_ROW_COUNT = 5000
TEST_REPEAT_COUNT = 3
PROVISIONAL_SAFE_ROWS_PER_STRIP = 5000


def source_identifier_sha256(rows: pd.DataFrame) -> str:
    """Hash the sorted source identifiers returned by one benchmark query."""
    source_ids = sorted(rows["source_id"].astype("int64"))
    content = "\n".join(str(source_id) for source_id in source_ids)
    return hashlib.sha256(content.encode()).hexdigest()


def process_peak_resident_bytes() -> int:
    """Return the process peak resident memory in bytes for the current platform."""
    raw_value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(raw_value if sys.platform == "darwin" else raw_value * 1024)


def benchmark_query(
    service: tap.TAPService,
    selector: object,
    base_where: str,
    requested_rows: int,
    repeat_index: int,
) -> dict[str, object]:
    """Retrieve, serialize, and score one measured full-column benchmark sample."""
    query = (
        f"SELECT TOP {requested_rows} {', '.join(RAW_GAIA_COLUMNS)} "
        f"FROM gaia_dr3.gaia_source WHERE {base_where} ORDER BY source_id"
    )
    tracemalloc.start()
    started = perf_counter()
    rows = service.run_sync(query, maxrec=requested_rows + 1).to_table().to_pandas()
    query_seconds = perf_counter() - started
    dataframe_memory_bytes = int(rows.memory_usage(index=True, deep=True).sum())
    serialized_csv = rows.to_csv(index=False).encode()
    started = perf_counter()
    scored = selector.score(rows)
    selector_seconds = perf_counter() - started
    _, python_traced_peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "requested_rows": requested_rows,
        "repeat_index": repeat_index,
        "returned_rows": len(rows),
        "returned_column_count": len(rows.columns),
        "dataframe_memory_bytes": dataframe_memory_bytes,
        "serialized_csv_bytes": len(serialized_csv),
        "query_seconds": query_seconds,
        "selector_seconds": selector_seconds,
        "python_traced_peak_bytes": python_traced_peak_bytes,
        "process_peak_resident_bytes": process_peak_resident_bytes(),
        "selected_rows": int(scored["point_source_logistic_selected"].sum()),
        "all_probabilities_finite": bool(
            np.isfinite(scored["point_source_logistic_probability"]).all()
        ),
        "source_identifiers_unique": bool(rows["source_id"].is_unique),
        "source_identifier_sha256": source_identifier_sha256(rows),
        "query_sha256": query_sha256(query),
    }


def main() -> None:
    """Run progressive full-column retrieval benchmarks and record a safe test limit."""
    review_hosts = pd.read_csv(BACKGROUND_REVIEW_HOSTS)
    host = review_hosts.loc[review_hosts["review_case"].eq("nearest_one_galaxy_catalog_case")].iloc[
        0
    ]
    base_where = (
        f"{cone_predicate(float(host['ra']), float(host['dec']), TEST_RADIUS_DEG)} "
        f"AND phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} AND {MAXIMUM_G_MAGNITUDE}"
    )
    count_query = "SELECT COUNT(*) AS source_count FROM gaia_dr3.gaia_source WHERE " + base_where
    service = tap.TAPService(DATA_LAB_TAP_URL)
    available_rows = int(
        service.run_sync(count_query, maxrec=10).to_table().to_pandas().iloc[0]["source_count"]
    )
    selector = load_frozen_selector()
    benchmark_requests = [(row_count, 0) for row_count in TEST_ROW_COUNTS]
    benchmark_requests.extend(
        (TEST_REPEAT_ROW_COUNT, repeat_index) for repeat_index in range(1, TEST_REPEAT_COUNT)
    )
    started = perf_counter()
    records = []
    for requested_rows, repeat_index in benchmark_requests:
        LOGGER.info("Benchmarking %d rows, repeat %d", requested_rows, repeat_index)
        records.append(
            benchmark_query(
                service,
                selector,
                base_where,
                requested_rows,
                repeat_index,
            )
        )
    total_seconds = perf_counter() - started
    results = pd.DataFrame(records)
    repeated = results.loc[results["requested_rows"].eq(TEST_REPEAT_ROW_COUNT)]
    checks = {
        "field_contains_at_least_10000_rows": available_rows >= max(TEST_ROW_COUNTS),
        "all_requested_rows_returned": results["requested_rows"].eq(results["returned_rows"]).all(),
        "all_raw_selector_columns_returned": results["returned_column_count"]
        .eq(len(RAW_GAIA_COLUMNS))
        .all(),
        "source_identifiers_unique_within_every_query": results["source_identifiers_unique"].all(),
        "all_selector_probabilities_finite": results["all_probabilities_finite"].all(),
        "three_5000_row_measurements": len(repeated) == TEST_REPEAT_COUNT,
        "repeated_5000_row_identifiers_match": repeated["source_identifier_sha256"].nunique() == 1,
        "10000_row_full_column_query_completed": results.loc[
            results["requested_rows"].eq(10000), "returned_rows"
        ].tolist()
        == [10000],
        "provisional_limit_directly_measured": PROVISIONAL_SAFE_ROWS_PER_STRIP
        in results["returned_rows"].tolist(),
        "provisional_limit_no_more_than_half_maximum_tested": (
            PROVISIONAL_SAFE_ROWS_PER_STRIP <= results["returned_rows"].max() / 2
        ),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK, index=False)
    manifest = {
        "benchmark_version": "gaia_full_selector_retrieval_benchmark_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "benchmark_scope": "bounded_full_selector_columns_progressive_rows",
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
        "available_rows_in_test_circle": available_rows,
        "raw_selector_column_count": len(RAW_GAIA_COLUMNS),
        "raw_selector_columns": RAW_GAIA_COLUMNS,
        "selector_version": SELECTOR_VERSION,
        "count_query_sha256": query_sha256(count_query),
        "test_row_counts": list(TEST_ROW_COUNTS),
        "repeat_row_count": TEST_REPEAT_ROW_COUNT,
        "repeat_count": TEST_REPEAT_COUNT,
        "maximum_successful_tested_rows": int(results["returned_rows"].max()),
        "provisional_safe_rows_per_strip": PROVISIONAL_SAFE_ROWS_PER_STRIP,
        "provisional_limit_scope": (
            "development_default_pending_multi_field_production_validation"
        ),
        "total_elapsed_seconds": total_seconds,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Full-selector retrieval benchmark failed: {checks}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
