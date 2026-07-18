"""Benchmark resumable full-column retrieval on one frozen development field."""

import json
import logging
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
    LARGE_SKY_DEVELOPMENT_BENCHMARK_MANIFEST,
    LARGE_SKY_DEVELOPMENT_BENCHMARK_PLAN,
    LARGE_SKY_DEVELOPMENT_BENCHMARK_SUMMARY,
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_GAIA_RETRIEVAL_DIR,
    POINT_SOURCE_LOGISTIC_MODEL,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
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
BENCHMARK_VERSION = "large_sky_development_benchmark_v1"


def require_external_checkpoint_root() -> None:
    """Refuse to place large raw checkpoints inside the repository."""
    if LARGE_SKY_GAIA_RETRIEVAL_DIR.resolve().is_relative_to(PROJECT_ROOT.resolve()):
        raise RuntimeError(
            "Raw large-sky Gaia checkpoints must be outside the repository; set "
            "BUBBLETEA_EXTERNAL_DATA, for example to ~/Dropbox/work/data"
        )


def field_base_where(field: pd.Series) -> str:
    """Return the frozen magnitude and circular-geometry query predicate."""
    return (
        f"{cone_predicate(float(field['ra_deg']), float(field['dec_deg']), float(field['field_radius_deg']))} "
        f"AND phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} AND {MAXIMUM_G_MAGNITUDE}"
    )


def checkpoint_inventory(
    retriever: AdaptiveGaiaRetriever, leaf_strips: list[object]
) -> list[dict[str, object]]:
    """Return path, size, and hash records for verified external checkpoints."""
    records = []
    for strip in leaf_strips:
        source_path, metadata_path = retriever.checkpoint_paths(strip)
        records.append(
            {
                "strip_id": strip.strip_id,
                "source_path": str(source_path.resolve()),
                "source_bytes": source_path.stat().st_size,
                "source_sha256": file_sha256(source_path),
                "metadata_path": str(metadata_path.resolve()),
                "metadata_sha256": file_sha256(metadata_path),
            }
        )
    return records


def main() -> None:
    """Plan, stop, resume, combine, and score the frozen benchmark field."""
    require_external_checkpoint_root()
    pilot = pd.read_csv(LARGE_SKY_DEVELOPMENT_PILOT_FIELDS)
    pilot_manifest = json.loads(
        LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST.read_text(encoding="utf-8")
    )
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    retrieval_limit_manifest = json.loads(
        GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST.read_text(encoding="utf-8")
    )
    benchmark_rows = pilot.loc[pilot["is_single_field_performance_benchmark"].astype(bool)]
    if len(benchmark_rows) != 1:
        raise RuntimeError("Frozen pilot must contain exactly one performance benchmark")
    field = benchmark_rows.iloc[0]
    field_id = str(field["field_id"])
    validation_field_ids = set(
        grid.loc[grid["experiment_partition"].eq("validation"), "field_id"].astype(str)
    )
    if field_id in validation_field_ids or field["experiment_partition"] != "development":
        raise RuntimeError(f"Refusing to query non-development field {field_id}")

    maximum_rows_per_strip = int(retrieval_limit_manifest["provisional_safe_rows_per_strip"])
    base_where = field_base_where(field)
    checkpoint_directory = (
        LARGE_SKY_GAIA_RETRIEVAL_DIR / str(field["grid_id"]) / str(field["pilot_id"]) / field_id
    )
    checkpoint_directory.mkdir(parents=True, exist_ok=True)
    service = tap.TAPService(DATA_LAB_TAP_URL)
    total_started = perf_counter()
    plan_started = perf_counter()
    planned = plan_adaptive_strips(
        service,
        base_where,
        max(-90.0, float(field["dec_deg"]) - float(field["field_radius_deg"])),
        min(90.0, float(field["dec_deg"]) + float(field["field_radius_deg"])),
        maximum_rows_per_strip,
    )
    plan_seconds = perf_counter() - plan_started
    plan_records = [{"field_id": field_id, **asdict(node)} for node in planned]
    pd.DataFrame(plan_records).to_csv(LARGE_SKY_DEVELOPMENT_BENCHMARK_PLAN, index=False)
    external_plan_path = checkpoint_directory / "measured_plan.csv"
    write_plan(external_plan_path, planned)
    leaf_strips = load_leaf_plan(external_plan_path)
    retriever = AdaptiveGaiaRetriever(
        service,
        base_where,
        checkpoint_directory,
        tuple(RAW_GAIA_COLUMNS),
    )
    valid_before_run = [
        strip.strip_id for strip in leaf_strips if retriever.checkpoint_valid(strip)
    ]
    retrieval_started = perf_counter()
    first_pass = retriever.run(leaf_strips, maximum_new_retrievals=1)
    resumed_pass = retriever.run(leaf_strips)
    retrieval_seconds = perf_counter() - retrieval_started
    combined = retriever.combine(leaf_strips)
    scoring_started = perf_counter()
    selector = load_frozen_selector()
    scored = selector.score(combined)
    scoring_seconds = perf_counter() - scoring_started
    inventory = checkpoint_inventory(retriever, leaf_strips)
    total_seconds = perf_counter() - total_started

    selected_count = int(scored["point_source_logistic_selected"].sum())
    exact_area_square_deg = float(field["requested_area_square_deg"])
    summary = pd.DataFrame(
        [
            {
                "benchmark_version": BENCHMARK_VERSION,
                "pilot_id": field["pilot_id"],
                "grid_id": field["grid_id"],
                "field_id": field_id,
                "experiment_partition": field["experiment_partition"],
                "ra_deg": float(field["ra_deg"]),
                "dec_deg": float(field["dec_deg"]),
                "galactic_latitude_deg": float(field["galactic_latitude_deg"]),
                "ecliptic_latitude_deg": float(field["ecliptic_latitude_deg"]),
                "field_radius_deg": float(field["field_radius_deg"]),
                "usable_area_square_deg": exact_area_square_deg,
                "measured_source_count": int(planned[0].measured_source_count),
                "retrieved_source_count": len(combined),
                "selected_source_count": selected_count,
                "all_source_density_per_square_deg": len(combined) / exact_area_square_deg,
                "selected_source_density_per_square_deg": (selected_count / exact_area_square_deg),
                "planned_node_count": len(planned),
                "final_strip_count": len(leaf_strips),
                "maximum_leaf_source_count": max(
                    strip.measured_source_count for strip in leaf_strips
                ),
                "combined_source_identifier_sha256": source_identifier_sha256(combined),
                "checkpoint_source_bytes": sum(int(record["source_bytes"]) for record in inventory),
                "combined_dataframe_memory_bytes": int(
                    combined.memory_usage(index=True, deep=True).sum()
                ),
                "plan_seconds": plan_seconds,
                "retrieval_seconds": retrieval_seconds,
                "selector_seconds": scoring_seconds,
                "total_seconds": total_seconds,
            }
        ]
    )
    summary.to_csv(LARGE_SKY_DEVELOPMENT_BENCHMARK_SUMMARY, index=False)

    plan_field_ids = {str(record["field_id"]) for record in plan_records}
    raw_and_output_columns = set(RAW_GAIA_COLUMNS) | {
        "point_source_logistic_probability",
        "point_source_logistic_selected",
        "point_source_selector_version",
    }
    leaf_count = sum(strip.measured_source_count for strip in leaf_strips)
    checks = {
        "frozen_benchmark_field_queried": field_id == pilot_manifest["benchmark_field_id"],
        "benchmark_is_development_only": field["experiment_partition"] == "development",
        "no_validation_field_in_plan_or_output": validation_field_ids.isdisjoint(
            plan_field_ids | {field_id}
        ),
        "adaptive_split_required": len(leaf_strips) > 1,
        "every_leaf_within_five_thousand_rows": all(
            strip.measured_source_count <= maximum_rows_per_strip for strip in leaf_strips
        ),
        "leaf_counts_conserve_root_count": leaf_count == planned[0].measured_source_count,
        "retrieved_count_matches_measured_count": len(combined) == planned[0].measured_source_count,
        "combined_source_identifiers_unique": combined["source_id"].is_unique,
        "all_raw_columns_and_selector_outputs_present": raw_and_output_columns.issubset(
            scored.columns
        ),
        "all_selector_probabilities_finite": np.isfinite(
            scored["point_source_logistic_probability"]
        ).all(),
        "all_rows_use_frozen_selector_version": scored["point_source_selector_version"]
        .eq(SELECTOR_VERSION)
        .all(),
        "controlled_first_pass_retrieved_at_most_one_new_strip": len(
            first_pass["retrieved_strip_ids"]
        )
        <= 1,
        "resumed_run_complete": bool(resumed_pass["complete"]),
        "all_checkpoints_valid_after_resume": all(
            retriever.checkpoint_valid(strip) for strip in leaf_strips
        ),
        "external_checkpoint_directory_outside_repository": not checkpoint_directory.resolve().is_relative_to(
            PROJECT_ROOT.resolve()
        ),
        "no_selector_prefilter_in_archive_query": all(
            term not in base_where.lower()
            for term in (
                "point_source",
                "selector",
                "astrometric_excess_noise_sig",
                "ipd_frac_multi_peak",
            )
        ),
        "selected_count_matches_saved_decisions": selected_count
        == int(scored["point_source_logistic_selected"].sum()),
        "input_pilot_passed_all_checks": pilot_manifest["passed_count"]
        == pilot_manifest["check_count"],
    }
    checks = {name: bool(value) for name, value in checks.items()}
    manifest = {
        "benchmark_version": BENCHMARK_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "benchmark_scope": "one_frozen_low_latitude_development_field_full_19_columns",
        "data_source": {
            "catalog_release": "Gaia DR3",
            "table": "gaia_dr3.gaia_source",
            "query_service": DATA_LAB_TAP_URL,
            "publication_bibcode": "2023A&A...674A...1G",
            "publication_doi": "10.1051/0004-6361/202243940",
        },
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
                LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST,
                GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
                POINT_SOURCE_LOGISTIC_MODEL,
                POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
            )
        ],
        "benchmark_field_id": field_id,
        "selection_rule": "minimum_absolute_galactic_latitude_then_field_id",
        "selector_version": SELECTOR_VERSION,
        "selector_threshold": selector.threshold,
        "minimum_g_magnitude": MINIMUM_G_MAGNITUDE,
        "maximum_g_magnitude": MAXIMUM_G_MAGNITUDE,
        "raw_gaia_columns": RAW_GAIA_COLUMNS,
        "maximum_rows_per_strip": maximum_rows_per_strip,
        "base_where_sha256": query_sha256(base_where),
        "valid_checkpoint_ids_before_run": valid_before_run,
        "first_pass": first_pass,
        "resumed_pass": resumed_pass,
        "external_checkpoint_directory": str(checkpoint_directory.resolve()),
        "external_measured_plan": {
            "path": str(external_plan_path.resolve()),
            "sha256": file_sha256(external_plan_path),
        },
        "external_checkpoint_inventory": inventory,
        "summary": json.loads(summary.to_json(orient="records"))[0],
        "outputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                LARGE_SKY_DEVELOPMENT_BENCHMARK_PLAN,
                LARGE_SKY_DEVELOPMENT_BENCHMARK_SUMMARY,
            )
        ],
        "held_back_validation_field_count": len(validation_field_ids),
        "validation_selector_results_opened": False,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DEVELOPMENT_BENCHMARK_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Large-sky development benchmark failed: {checks}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
