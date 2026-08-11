"""Retrieve and score only the frozen off-target development fields."""

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    OFF_TARGET_DEVELOPMENT_MANIFEST,
    OFF_TARGET_DEVELOPMENT_SOURCES,
    OFF_TARGET_DEVELOPMENT_SUMMARY,
    OFF_TARGET_FIELD_SPLIT,
    OFF_TARGET_FIELD_SPLIT_MANIFEST,
    POINT_SOURCE_LOGISTIC_MODEL,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256, query_sha256
from scripts.phase3_background.benchmark_full_selector_retrieval import (
    source_identifier_sha256,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import (
    DATA_LAB_TAP_URL,
    TEST_PATCH_RADIUS_DEG,
)
from scripts.phase3_background.query_partition import cone_predicate
from scripts.phase3_background.radial_ring_area import (
    STERADIAN_TO_SQUARE_DEG,
    spherical_circle_area_steradian,
)
from scripts.utils.point_source_selector import (
    MAXIMUM_G_MAGNITUDE,
    MINIMUM_G_MAGNITUDE,
    RAW_GAIA_COLUMNS,
    SELECTOR_VERSION,
    load_frozen_selector,
)

LOGGER = logging.getLogger(__name__)
DEVELOPMENT_PARTITION = "development"
VALIDATION_PARTITION = "validation"


def retrieve_field(
    service: tap.TAPService, selector: object, field: pd.Series
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Retrieve all frozen-selector columns and score one development field."""
    predicate = cone_predicate(
        float(field["ra_deg"]), float(field["dec_deg"]), TEST_PATCH_RADIUS_DEG
    )
    base_where = (
        f"{predicate} AND phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} AND {MAXIMUM_G_MAGNITUDE}"
    )
    count_query = "SELECT COUNT(*) AS source_count FROM gaia_dr3.gaia_source WHERE " + base_where
    source_query = (
        f"SELECT {', '.join(RAW_GAIA_COLUMNS)} FROM gaia_dr3.gaia_source WHERE "
        f"{base_where} ORDER BY source_id"
    )
    started = perf_counter()
    measured_count = int(
        service.run_sync(count_query, maxrec=10).to_table().to_pandas().iloc[0]["source_count"]
    )
    count_seconds = perf_counter() - started
    started = perf_counter()
    rows = service.run_sync(source_query, maxrec=measured_count + 1).to_table().to_pandas()
    retrieval_seconds = perf_counter() - started
    if len(rows) != measured_count:
        raise RuntimeError(
            f"Field {field['field_id']} measured {measured_count} rows but retrieved {len(rows)}"
        )
    if not rows["source_id"].is_unique:
        raise RuntimeError(f"Field {field['field_id']} contains repeated Gaia identifiers")
    started = perf_counter()
    scored = selector.score(rows)
    selector_seconds = perf_counter() - started
    scored.insert(0, "split_id", str(field["split_id"]))
    scored.insert(1, "experiment_partition", str(field["experiment_partition"]))
    scored.insert(2, "field_id", str(field["field_id"]))
    scored.insert(3, "host_name", str(field["host_name"]))
    scored.insert(4, "field_role", str(field["field_role"]))
    patch_area_square_deg = (
        spherical_circle_area_steradian(TEST_PATCH_RADIUS_DEG) * STERADIAN_TO_SQUARE_DEG
    )
    selected_count = int(scored["point_source_logistic_selected"].sum())
    summary = {
        "split_id": str(field["split_id"]),
        "experiment_partition": str(field["experiment_partition"]),
        "field_id": str(field["field_id"]),
        "host_name": str(field["host_name"]),
        "field_role": str(field["field_role"]),
        "ra_deg": float(field["ra_deg"]),
        "dec_deg": float(field["dec_deg"]),
        "galactic_latitude_deg": float(field["galactic_latitude_deg"]),
        "patch_radius_deg": TEST_PATCH_RADIUS_DEG,
        "requested_area_square_deg": patch_area_square_deg,
        "successfully_queried_area_square_deg": patch_area_square_deg,
        "missing_area_square_deg": 0.0,
        "masked_area_square_deg": 0.0,
        "usable_area_square_deg": patch_area_square_deg,
        "measured_source_count": measured_count,
        "retrieved_source_count": len(rows),
        "selected_source_count": selected_count,
        "all_source_density_per_square_deg": measured_count / patch_area_square_deg,
        "selected_source_density_per_square_deg": selected_count / patch_area_square_deg,
        "minimum_selector_probability": float(scored["point_source_logistic_probability"].min()),
        "median_selector_probability": float(scored["point_source_logistic_probability"].median()),
        "maximum_selector_probability": float(scored["point_source_logistic_probability"].max()),
        "source_identifier_sha256": source_identifier_sha256(scored),
        "count_query_sha256": query_sha256(count_query),
        "source_query_sha256": query_sha256(source_query),
        "count_query_seconds": count_seconds,
        "source_retrieval_seconds": retrieval_seconds,
        "selector_seconds": selector_seconds,
    }
    return scored, summary


def main() -> None:
    """Run the selector on development fields while keeping validation fields sealed."""
    split = pd.read_csv(OFF_TARGET_FIELD_SPLIT)
    split_manifest = json.loads(OFF_TARGET_FIELD_SPLIT_MANIFEST.read_text(encoding="utf-8"))
    development = split.loc[
        split["experiment_partition"].eq(DEVELOPMENT_PARTITION)
        & split["frozen_for_selector_experiment"].astype(bool)
    ].copy()
    held_back_validation_ids = set(
        split.loc[split["experiment_partition"].eq(VALIDATION_PARTITION), "field_id"].astype(str)
    )
    selector = load_frozen_selector()
    service = tap.TAPService(DATA_LAB_TAP_URL)
    started = perf_counter()
    source_frames = []
    summaries = []
    queried_field_ids = []
    for _, field in development.sort_values("field_id").iterrows():
        field_id = str(field["field_id"])
        if field_id in held_back_validation_ids:
            raise RuntimeError(f"Refusing to query held-back validation field {field_id}")
        LOGGER.info("Retrieving development field %s", field_id)
        scored, summary = retrieve_field(service, selector, field)
        source_frames.append(scored)
        summaries.append(summary)
        queried_field_ids.append(field_id)
    sources = pd.concat(source_frames, ignore_index=True)
    summary = pd.DataFrame(summaries)
    total_seconds = perf_counter() - started
    expected_development_ids = set(development["field_id"].astype(str))
    frozen_development_cases = set(split_manifest["assignment_rule"]["development_review_cases"])
    frozen_validation_cases = set(split_manifest["assignment_rule"]["validation_review_cases"])
    actual_development_cases = set(development["review_case"].astype(str))
    actual_validation_cases = set(
        split.loc[split["experiment_partition"].eq(VALIDATION_PARTITION), "review_case"].astype(str)
    )
    source_field_ids = set(sources["field_id"].astype(str))
    summary_field_ids = set(summary["field_id"].astype(str))
    expected_raw_and_output_columns = set(RAW_GAIA_COLUMNS) | {
        "point_source_logistic_probability",
        "point_source_logistic_selected",
        "point_source_selector_version",
    }
    checks = {
        "four_development_fields_queried": len(queried_field_ids) == 4
        and set(queried_field_ids) == expected_development_ids,
        "four_validation_fields_remain_held_back": len(held_back_validation_ids) == 4,
        "split_assignments_match_frozen_review_cases": actual_development_cases
        == frozen_development_cases
        and actual_validation_cases == frozen_validation_cases,
        "no_validation_field_queried": held_back_validation_ids.isdisjoint(queried_field_ids),
        "no_validation_field_in_source_output": held_back_validation_ids.isdisjoint(
            source_field_ids
        ),
        "no_validation_field_in_summary_output": held_back_validation_ids.isdisjoint(
            summary_field_ids
        ),
        "source_and_summary_fields_match_frozen_development": source_field_ids
        == summary_field_ids
        == expected_development_ids,
        "all_measured_counts_retrieved": summary["measured_source_count"]
        .eq(summary["retrieved_source_count"])
        .all(),
        "summary_counts_match_source_rows": summary.set_index("field_id")[
            "retrieved_source_count"
        ].equals(sources.groupby("field_id").size()),
        "all_raw_columns_and_selector_outputs_present": expected_raw_and_output_columns.issubset(
            sources.columns
        ),
        "all_source_identifiers_unique_within_fields": sources.groupby("field_id")["source_id"]
        .apply(lambda values: values.is_unique)
        .all(),
        "non_overlapping_fields_have_unique_source_identifiers": sources["source_id"].is_unique,
        "all_selector_probabilities_finite": np.isfinite(
            sources["point_source_logistic_probability"]
        ).all(),
        "all_rows_use_frozen_selector_version": sources["point_source_selector_version"]
        .eq(SELECTOR_VERSION)
        .all(),
        "selected_counts_match_source_decisions": summary.set_index("field_id")[
            "selected_source_count"
        ].equals(sources.groupby("field_id")["point_source_logistic_selected"].sum().astype(int)),
        "gaia_usable_area_equals_queried_area": summary["usable_area_square_deg"]
        .eq(summary["successfully_queried_area_square_deg"])
        .all(),
        "gaia_masked_and_missing_areas_zero": summary["masked_area_square_deg"].eq(0).all()
        and summary["missing_area_square_deg"].eq(0).all(),
        "input_split_matches_frozen_identifier": summary["split_id"]
        .eq(split_manifest["split_id"])
        .all(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    OFF_TARGET_DEVELOPMENT_SOURCES.parent.mkdir(parents=True, exist_ok=True)
    sources.to_csv(OFF_TARGET_DEVELOPMENT_SOURCES, index=False)
    summary.to_csv(OFF_TARGET_DEVELOPMENT_SUMMARY, index=False)
    manifest = {
        "experiment_version": "off_target_development_selector_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "experiment_scope": "development_fields_only_validation_selector_results_unopened",
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
                OFF_TARGET_FIELD_SPLIT,
                OFF_TARGET_FIELD_SPLIT_MANIFEST,
                POINT_SOURCE_LOGISTIC_MODEL,
                POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
            )
        ],
        "split_id": split_manifest["split_id"],
        "development_field_ids": queried_field_ids,
        "held_back_validation_field_ids": sorted(held_back_validation_ids),
        "selector_version": SELECTOR_VERSION,
        "selector_threshold": selector.threshold,
        "minimum_g_magnitude": MINIMUM_G_MAGNITUDE,
        "maximum_g_magnitude": MAXIMUM_G_MAGNITUDE,
        "raw_gaia_column_count": len(RAW_GAIA_COLUMNS),
        "raw_gaia_columns": RAW_GAIA_COLUMNS,
        "development_field_count": len(summary),
        "total_retrieved_source_count": int(summary["retrieved_source_count"].sum()),
        "total_selected_source_count": int(summary["selected_source_count"].sum()),
        "total_usable_area_square_deg": float(summary["usable_area_square_deg"].sum()),
        "total_elapsed_seconds": total_seconds,
        "source_output": {
            "path": str(OFF_TARGET_DEVELOPMENT_SOURCES.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(OFF_TARGET_DEVELOPMENT_SOURCES),
        },
        "summary_output": {
            "path": str(OFF_TARGET_DEVELOPMENT_SUMMARY.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(OFF_TARGET_DEVELOPMENT_SUMMARY),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    OFF_TARGET_DEVELOPMENT_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Off-target development selector experiment failed: {checks}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
