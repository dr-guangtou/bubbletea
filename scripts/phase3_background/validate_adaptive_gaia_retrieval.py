"""Validate measured splitting, checkpointing, and restartable Gaia retrieval."""

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_HOSTS,
    GAIA_ADAPTIVE_RETRIEVAL_PLAN,
    GAIA_ADAPTIVE_RETRIEVAL_SOURCES,
    GAIA_ADAPTIVE_RETRIEVAL_VALIDATION,
    GAIA_QUERY_PARTITION_SOURCES,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import (
    AdaptiveGaiaRetriever,
    file_sha256,
    load_leaf_plan,
    plan_adaptive_strips,
    write_plan,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.query_partition import cone_predicate
from scripts.utils.point_source_selector import MAXIMUM_G_MAGNITUDE, MINIMUM_G_MAGNITUDE

LOGGER = logging.getLogger(__name__)
TEST_RADIUS_DEG = 0.2
TEST_MAXIMUM_ROWS_PER_STRIP = 130
TEST_FIRST_PASS_RETRIEVAL_COUNT = 2
TEST_SOURCE_COLUMNS = ("source_id", "ra", "dec", "phot_g_mean_mag")


def main() -> None:
    """Interrupt and resume one bounded adaptive retrieval, then validate identity."""
    review_hosts = pd.read_csv(BACKGROUND_REVIEW_HOSTS)
    host = review_hosts.loc[
        review_hosts["review_case"].eq("highest_ranked_one_galaxy_catalog_case")
    ].iloc[0]
    base_where = (
        f"{cone_predicate(float(host['ra']), float(host['dec']), TEST_RADIUS_DEG)} "
        f"AND phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} AND {MAXIMUM_G_MAGNITUDE}"
    )
    minimum_dec_deg = max(-90.0, float(host["dec"]) - TEST_RADIUS_DEG)
    maximum_dec_deg = min(90.0, float(host["dec"]) + TEST_RADIUS_DEG)
    service = tap.TAPService(DATA_LAB_TAP_URL)
    started = perf_counter()
    planned = plan_adaptive_strips(
        service,
        base_where,
        minimum_dec_deg,
        maximum_dec_deg,
        TEST_MAXIMUM_ROWS_PER_STRIP,
    )
    GAIA_ADAPTIVE_RETRIEVAL_PLAN.parent.mkdir(parents=True, exist_ok=True)
    write_plan(GAIA_ADAPTIVE_RETRIEVAL_PLAN, planned)
    leaf_strips = load_leaf_plan(GAIA_ADAPTIVE_RETRIEVAL_PLAN)
    with TemporaryDirectory(prefix="bubbletea_gaia_resume_") as temporary_directory:
        checkpoint_directory = Path(temporary_directory)
        first_retriever = AdaptiveGaiaRetriever(
            service, base_where, checkpoint_directory, TEST_SOURCE_COLUMNS
        )
        first_pass = first_retriever.run(
            leaf_strips,
            maximum_new_retrievals=TEST_FIRST_PASS_RETRIEVAL_COUNT,
        )
        first_checkpoint_hashes = {
            strip_id: file_sha256(checkpoint_directory / f"strip_{strip_id}.csv")
            for strip_id in first_pass["completed_strip_ids"]
        }
        LOGGER.info("Controlled stop after strips: %s", first_pass["completed_strip_ids"])
        resumed_leaf_strips = load_leaf_plan(GAIA_ADAPTIVE_RETRIEVAL_PLAN)
        resumed_retriever = AdaptiveGaiaRetriever(
            service, base_where, checkpoint_directory, TEST_SOURCE_COLUMNS
        )
        resumed_pass = resumed_retriever.run(resumed_leaf_strips)
        unchanged_checkpoint_hashes = all(
            file_sha256(checkpoint_directory / f"strip_{strip_id}.csv") == checkpoint_hash
            for strip_id, checkpoint_hash in first_checkpoint_hashes.items()
        )
        corrupted_strip = resumed_leaf_strips[-1]
        corrupted_source_path = resumed_retriever.checkpoint_paths(corrupted_strip)[0]
        with corrupted_source_path.open("a", encoding="utf-8") as handle:
            handle.write("\n")
        recovery_retriever = AdaptiveGaiaRetriever(
            service, base_where, checkpoint_directory, TEST_SOURCE_COLUMNS
        )
        recovery_pass = recovery_retriever.run(resumed_leaf_strips)
        combined = recovery_retriever.combine(resumed_leaf_strips)
    total_seconds = perf_counter() - started
    reference = pd.read_csv(GAIA_QUERY_PARTITION_SOURCES, dtype={"source_id": "int64"})
    reference_ids = set(reference["source_id"])
    combined_ids = set(combined["source_id"])
    leaf_count = sum(strip.measured_source_count for strip in leaf_strips)
    checks = {
        "adaptive_split_required": len(leaf_strips) > 1,
        "every_leaf_within_test_row_limit": all(
            strip.measured_source_count <= TEST_MAXIMUM_ROWS_PER_STRIP for strip in leaf_strips
        ),
        "leaf_counts_sum_to_reference": leaf_count == len(reference),
        "first_pass_stopped_incomplete": not first_pass["complete"],
        "first_pass_saved_two_strips": len(first_pass["retrieved_strip_ids"])
        == TEST_FIRST_PASS_RETRIEVAL_COUNT,
        "resume_skipped_saved_strips": set(first_pass["completed_strip_ids"]).issubset(
            resumed_pass["skipped_strip_ids"]
        ),
        "saved_checkpoint_hashes_unchanged": unchanged_checkpoint_hashes,
        "resumed_run_completed": resumed_pass["complete"],
        "corrupted_checkpoint_retrieved_again": recovery_pass["retrieved_strip_ids"]
        == [corrupted_strip.strip_id],
        "uncorrupted_checkpoints_skipped_during_recovery": set(recovery_pass["skipped_strip_ids"])
        == {strip.strip_id for strip in resumed_leaf_strips[:-1]},
        "corruption_recovery_completed": recovery_pass["complete"],
        "combined_source_count_matches_reference": len(combined) == len(reference),
        "combined_source_identifiers_unique": combined["source_id"].is_unique,
        "combined_source_identifiers_match_reference": combined_ids == reference_ids,
        "no_selector_output_used": all(
            term not in base_where.lower()
            for term in (
                "point_source",
                "selector",
                "astrometric_excess_noise_sig",
                "ipd_frac_multi_peak",
            )
        ),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    combined.to_csv(GAIA_ADAPTIVE_RETRIEVAL_SOURCES, index=False)
    manifest = {
        "validation_version": "gaia_adaptive_retrieval_validation_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "validation_scope": "bounded_measured_split_checkpoint_stop_and_resume",
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
            for path in (BACKGROUND_REVIEW_HOSTS, GAIA_QUERY_PARTITION_SOURCES)
        ],
        "host_name": host["objname"],
        "test_radius_deg": TEST_RADIUS_DEG,
        "test_maximum_rows_per_strip": TEST_MAXIMUM_ROWS_PER_STRIP,
        "test_first_pass_retrieval_count": TEST_FIRST_PASS_RETRIEVAL_COUNT,
        "planned_node_count": len(planned),
        "final_strip_count": len(leaf_strips),
        "final_strip_source_counts": {
            strip.strip_id: strip.measured_source_count for strip in leaf_strips
        },
        "first_pass": first_pass,
        "resumed_pass": resumed_pass,
        "corruption_recovery_pass": recovery_pass,
        "combined_source_count": len(combined),
        "elapsed_seconds": total_seconds,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    GAIA_ADAPTIVE_RETRIEVAL_VALIDATION.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Adaptive Gaia retrieval validation failed: {checks}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
