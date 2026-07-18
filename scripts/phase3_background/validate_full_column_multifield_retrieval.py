"""Validate full-column adaptive Gaia retrieval across three source densities."""

import json
import logging
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import numpy as np
import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_HOSTS,
    GAIA_FULL_COLUMN_MULTIFIELD_PLAN,
    GAIA_FULL_COLUMN_MULTIFIELD_RETRIEVAL,
    GAIA_FULL_COLUMN_MULTIFIELD_VALIDATION,
    GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import (
    AdaptiveGaiaRetriever,
    file_sha256,
    load_leaf_plan,
    plan_adaptive_strips,
    query_sha256,
    write_plan,
)
from scripts.phase3_background.benchmark_full_selector_retrieval import (
    source_identifier_sha256,
)
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
TEST_HOST_NAMES = ("NGC 4698", "MESSIER 060", "ESO 006- G 001")
TEST_RADIUS_DEG_BY_HOST = {
    "NGC 4698": 0.5,
    "MESSIER 060": 0.75,
    "ESO 006- G 001": 0.5,
}
PRESERVED_INITIAL_FAILED_TEST = {
    "test_radius_deg_for_all_fields": 0.5,
    "measured_rows_by_host": {
        "NGC 4698": 2991,
        "MESSIER 060": 3098,
        "ESO 006- G 001": 13010,
    },
    "split_field_count": 1,
    "failed_requirement": "at_least_two_fields_required_splitting",
    "disposition": "not_accepted_requirement_preserved",
}


def retrieve_reference_identifiers(
    service: tap.TAPService, base_where: str, expected_count: int
) -> tuple[pd.DataFrame, str]:
    """Retrieve an independent source-identifier reference for one complete circle."""
    query = f"SELECT source_id FROM gaia_dr3.gaia_source WHERE {base_where}"
    rows = service.run_sync(query, maxrec=expected_count + 1).to_table().to_pandas()
    if len(rows) != expected_count:
        raise RuntimeError(f"Reference expected {expected_count} rows but retrieved {len(rows)}")
    return rows, query_sha256(query)


def main() -> None:
    """Run adaptive full-column stop-and-resume validation for three fields."""
    benchmark_manifest = json.loads(
        GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST.read_text(encoding="utf-8")
    )
    maximum_rows_per_strip = int(benchmark_manifest["provisional_safe_rows_per_strip"])
    review_hosts = pd.read_csv(BACKGROUND_REVIEW_HOSTS)
    hosts = review_hosts.loc[review_hosts["objname"].isin(TEST_HOST_NAMES)].copy()
    hosts["test_order"] = hosts["objname"].map(
        {host_name: index for index, host_name in enumerate(TEST_HOST_NAMES)}
    )
    hosts = hosts.sort_values("test_order")
    service = tap.TAPService(DATA_LAB_TAP_URL)
    selector = load_frozen_selector()
    started = perf_counter()
    field_records = []
    plan_records = []
    base_where_values = []
    for _, host in hosts.iterrows():
        host_name = str(host["objname"])
        test_radius_deg = TEST_RADIUS_DEG_BY_HOST[host_name]
        LOGGER.info("Planning full-column retrieval for %s", host_name)
        base_where = (
            f"{cone_predicate(float(host['ra']), float(host['dec']), test_radius_deg)} "
            f"AND phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} "
            f"AND {MAXIMUM_G_MAGNITUDE}"
        )
        base_where_values.append(base_where)
        minimum_dec_deg = max(-90.0, float(host["dec"]) - test_radius_deg)
        maximum_dec_deg = min(90.0, float(host["dec"]) + test_radius_deg)
        field_started = perf_counter()
        planned = plan_adaptive_strips(
            service,
            base_where,
            minimum_dec_deg,
            maximum_dec_deg,
            maximum_rows_per_strip,
        )
        for node in planned:
            plan_records.append({"host_name": host_name, **asdict(node)})
        with TemporaryDirectory(prefix="bubbletea_full_column_") as temporary_directory:
            checkpoint_directory = Path(temporary_directory)
            plan_path = checkpoint_directory / "measured_plan.csv"
            write_plan(plan_path, planned)
            leaf_strips = load_leaf_plan(plan_path)
            first_retriever = AdaptiveGaiaRetriever(
                service,
                base_where,
                checkpoint_directory,
                tuple(RAW_GAIA_COLUMNS),
            )
            first_pass = first_retriever.run(leaf_strips, maximum_new_retrievals=1)
            resumed_retriever = AdaptiveGaiaRetriever(
                service,
                base_where,
                checkpoint_directory,
                tuple(RAW_GAIA_COLUMNS),
            )
            resumed_pass = resumed_retriever.run(load_leaf_plan(plan_path))
            combined = resumed_retriever.combine(load_leaf_plan(plan_path))
            checkpoint_csv_bytes = sum(
                resumed_retriever.checkpoint_paths(strip)[0].stat().st_size for strip in leaf_strips
            )
            maximum_checkpoint_csv_bytes = max(
                resumed_retriever.checkpoint_paths(strip)[0].stat().st_size for strip in leaf_strips
            )
        reference, reference_query_hash = retrieve_reference_identifiers(
            service, base_where, planned[0].measured_source_count
        )
        scored = selector.score(combined)
        requires_split = len(leaf_strips) > 1
        field_records.append(
            {
                "host_name": host_name,
                "test_radius_deg": test_radius_deg,
                "available_rows": planned[0].measured_source_count,
                "planned_node_count": len(planned),
                "final_strip_count": len(leaf_strips),
                "maximum_leaf_rows": max(strip.measured_source_count for strip in leaf_strips),
                "requires_split": requires_split,
                "first_pass_complete": bool(first_pass["complete"]),
                "first_pass_retrieved_count": len(first_pass["retrieved_strip_ids"]),
                "resumed_pass_complete": bool(resumed_pass["complete"]),
                "resumed_pass_skipped_count": len(resumed_pass["skipped_strip_ids"]),
                "combined_rows": len(combined),
                "combined_identifiers_unique": bool(combined["source_id"].is_unique),
                "combined_identifier_sha256": source_identifier_sha256(combined),
                "reference_identifier_sha256": source_identifier_sha256(reference),
                "all_raw_columns_present": set(RAW_GAIA_COLUMNS).issubset(combined.columns),
                "all_probabilities_finite": bool(
                    np.isfinite(scored["point_source_logistic_probability"]).all()
                ),
                "selected_rows": int(scored["point_source_logistic_selected"].sum()),
                "combined_dataframe_memory_bytes": int(
                    combined.memory_usage(index=True, deep=True).sum()
                ),
                "checkpoint_csv_bytes": checkpoint_csv_bytes,
                "maximum_checkpoint_csv_bytes": maximum_checkpoint_csv_bytes,
                "base_where_sha256": query_sha256(base_where),
                "reference_query_sha256": reference_query_hash,
                "field_elapsed_seconds": perf_counter() - field_started,
            }
        )
    total_seconds = perf_counter() - started
    results = pd.DataFrame(field_records)
    split_fields = results.loc[results["requires_split"]]
    unsplit_fields = results.loc[~results["requires_split"]]
    checks = {
        "three_predeclared_fields_measured": results["host_name"].tolist() == list(TEST_HOST_NAMES),
        "at_least_two_fields_required_splitting": len(split_fields) >= 2,
        "at_least_one_field_required_no_split": len(unsplit_fields) >= 1,
        "every_leaf_within_provisional_limit": results["maximum_leaf_rows"]
        .le(maximum_rows_per_strip)
        .all(),
        "all_combined_counts_match_reference": results["combined_rows"]
        .eq(results["available_rows"])
        .all(),
        "all_combined_identifiers_unique": results["combined_identifiers_unique"].all(),
        "all_combined_identifier_hashes_match_reference": results["combined_identifier_sha256"]
        .eq(results["reference_identifier_sha256"])
        .all(),
        "all_raw_selector_columns_present": results["all_raw_columns_present"].all(),
        "all_selector_probabilities_finite": results["all_probabilities_finite"].all(),
        "split_fields_stopped_after_first_checkpoint": (~split_fields["first_pass_complete"]).all()
        and split_fields["first_pass_retrieved_count"].eq(1).all(),
        "split_fields_resumed_and_skipped_checkpoint": split_fields["resumed_pass_complete"].all()
        and split_fields["resumed_pass_skipped_count"].ge(1).all(),
        "unsplit_fields_completed_in_first_pass": unsplit_fields["first_pass_complete"].all(),
        "no_selector_prefilter_used": all(
            term not in " ".join(base_where_values).lower()
            for term in (
                "point_source",
                "selector",
                "astrometric_excess_noise_sig",
                "ipd_frac_multi_peak",
            )
        ),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    GAIA_FULL_COLUMN_MULTIFIELD_RETRIEVAL.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(GAIA_FULL_COLUMN_MULTIFIELD_RETRIEVAL, index=False)
    pd.DataFrame(plan_records).to_csv(GAIA_FULL_COLUMN_MULTIFIELD_PLAN, index=False)
    manifest = {
        "validation_version": "gaia_full_column_multifield_validation_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "validation_scope": "three_field_full_column_adaptive_stop_and_resume",
        "data_source": {
            "catalog_release": "Gaia DR3",
            "table": "gaia_dr3.gaia_source",
            "query_service": DATA_LAB_TAP_URL,
            "publication_bibcode": "2023A&A...674A...1G",
            "publication_doi": "10.1051/0004-6361/202243940",
        },
        "inputs": [
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "sha256": file_sha256(path),
            }
            for path in (
                BACKGROUND_REVIEW_HOSTS,
                GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
            )
        ],
        "test_host_names": list(TEST_HOST_NAMES),
        "test_radius_deg_by_host": TEST_RADIUS_DEG_BY_HOST,
        "preserved_initial_failed_test": PRESERVED_INITIAL_FAILED_TEST,
        "provisional_rows_per_strip": maximum_rows_per_strip,
        "approved_rows_per_strip": maximum_rows_per_strip,
        "approved_limit_scope": "development_and_pilot_current_19_column_contract",
        "raw_selector_column_count": len(RAW_GAIA_COLUMNS),
        "raw_selector_columns": RAW_GAIA_COLUMNS,
        "selector_version": SELECTOR_VERSION,
        "field_count": len(results),
        "total_available_rows": int(results["available_rows"].sum()),
        "total_final_strip_count": int(results["final_strip_count"].sum()),
        "total_elapsed_seconds": total_seconds,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    GAIA_FULL_COLUMN_MULTIFIELD_VALIDATION.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Full-column multifield validation failed: {checks}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
