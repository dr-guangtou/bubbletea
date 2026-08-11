"""Retrieve and score the frozen large-sky development pilot fields."""

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
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST,
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST,
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_PLAN,
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_GAIA_RETRIEVAL_DIR,
    POINT_SOURCE_LOGISTIC_MODEL,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import (
    AdaptiveGaiaRetriever,
    AdaptiveStrip,
    file_sha256,
    load_leaf_plan,
    plan_adaptive_strips,
    query_sha256,
    write_json_atomic,
    write_plan,
)
from scripts.phase3_background.benchmark_full_selector_retrieval import (
    source_identifier_sha256,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.benchmark_large_sky_development_retrieval import (
    checkpoint_inventory,
    field_base_where,
    require_external_checkpoint_root,
)
from scripts.utils.point_source_selector import (
    MAXIMUM_G_MAGNITUDE,
    MINIMUM_G_MAGNITUDE,
    RAW_GAIA_COLUMNS,
    SELECTOR_VERSION,
    load_frozen_selector,
)

LOGGER = logging.getLogger(__name__)
RETRIEVAL_VERSION = "large_sky_development_retrieval_v1"


def plan_contract(base_where: str, maximum_rows_per_strip: int) -> dict[str, object]:
    """Return the identity contract for a persistent measured strip plan."""
    return {
        "base_where_sha256": query_sha256(base_where),
        "maximum_rows_per_strip": maximum_rows_per_strip,
        "raw_gaia_columns": RAW_GAIA_COLUMNS,
    }


def load_all_plan_nodes(plan_path: Path) -> list[AdaptiveStrip]:
    """Load every node from a measured adaptive plan."""
    frame = pd.read_csv(plan_path)
    return [AdaptiveStrip(**record) for record in frame.to_dict(orient="records")]


def plan_is_reusable(
    plan_path: Path,
    contract_path: Path,
    expected_contract: dict[str, object],
    field_id: str,
    benchmark_manifest: dict[str, object],
) -> bool:
    """Return whether an external measured plan matches the current query contract."""
    if not plan_path.exists():
        return False
    if contract_path.exists():
        try:
            return json.loads(contract_path.read_text(encoding="utf-8")) == expected_contract
        except json.JSONDecodeError:
            return False
    return (
        field_id == benchmark_manifest["benchmark_field_id"]
        and benchmark_manifest["base_where_sha256"] == expected_contract["base_where_sha256"]
        and benchmark_manifest["maximum_rows_per_strip"]
        == expected_contract["maximum_rows_per_strip"]
        and benchmark_manifest["raw_gaia_columns"] == expected_contract["raw_gaia_columns"]
    )


def write_frame_atomic(frame: pd.DataFrame, path: Path) -> None:
    """Write one CSV through a temporary file before replacement."""
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary_path, index=False)
    temporary_path.replace(path)


def main() -> None:
    """Retrieve all frozen pilot fields while keeping validation unopened."""
    require_external_checkpoint_root()
    pilot = pd.read_csv(LARGE_SKY_DEVELOPMENT_PILOT_FIELDS)
    pilot_manifest = json.loads(
        LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST.read_text(encoding="utf-8")
    )
    if pilot_manifest["passed_count"] != pilot_manifest["check_count"]:
        raise RuntimeError("Frozen development pilot did not pass all identity checks")
    benchmark_manifest = json.loads(
        LARGE_SKY_DEVELOPMENT_BENCHMARK_MANIFEST.read_text(encoding="utf-8")
    )
    retrieval_limit_manifest = json.loads(
        GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST.read_text(encoding="utf-8")
    )
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    validation_field_ids = set(
        grid.loc[grid["experiment_partition"].eq("validation"), "field_id"].astype(str)
    )
    pilot_field_ids = set(pilot["field_id"].astype(str))
    if not validation_field_ids.isdisjoint(pilot_field_ids):
        raise RuntimeError("Frozen pilot contains a held-back validation identifier")

    maximum_rows_per_strip = int(retrieval_limit_manifest["provisional_safe_rows_per_strip"])
    service = tap.TAPService(DATA_LAB_TAP_URL)
    selector = load_frozen_selector()
    run_started = perf_counter()
    summary_records = []
    plan_records = []
    receipt_records = []
    for _, field in pilot.sort_values("field_id").iterrows():
        field_id = str(field["field_id"])
        LOGGER.info("Processing frozen development field %s", field_id)
        field_started = perf_counter()
        base_where = field_base_where(field)
        field_directory = (
            LARGE_SKY_GAIA_RETRIEVAL_DIR / str(field["grid_id"]) / str(field["pilot_id"]) / field_id
        )
        field_directory.mkdir(parents=True, exist_ok=True)
        external_plan_path = field_directory / "measured_plan.csv"
        contract_path = field_directory / "plan_contract.json"
        expected_contract = plan_contract(base_where, maximum_rows_per_strip)
        planning_started = perf_counter()
        reused_plan = plan_is_reusable(
            external_plan_path,
            contract_path,
            expected_contract,
            field_id,
            benchmark_manifest,
        )
        if reused_plan:
            planned = load_all_plan_nodes(external_plan_path)
        else:
            planned = plan_adaptive_strips(
                service,
                base_where,
                max(-90.0, float(field["dec_deg"]) - float(field["field_radius_deg"])),
                min(90.0, float(field["dec_deg"]) + float(field["field_radius_deg"])),
                maximum_rows_per_strip,
            )
            write_plan(external_plan_path, planned)
        write_json_atomic(contract_path, expected_contract)
        planning_seconds = perf_counter() - planning_started
        for node in planned:
            plan_records.append(
                {
                    "field_id": field_id,
                    "plan_reused": reused_plan,
                    **asdict(node),
                }
            )
        leaf_strips = load_leaf_plan(external_plan_path)
        retriever = AdaptiveGaiaRetriever(
            service,
            base_where,
            field_directory,
            tuple(RAW_GAIA_COLUMNS),
        )
        retrieval_started = perf_counter()
        retrieval_result = retriever.run(leaf_strips)
        combined = retriever.combine(leaf_strips)
        retrieval_seconds = perf_counter() - retrieval_started
        scoring_started = perf_counter()
        scored = selector.score(combined)
        scoring_seconds = perf_counter() - scoring_started
        inventory = checkpoint_inventory(retriever, leaf_strips)
        selected_count = int(scored["point_source_logistic_selected"].sum())
        exact_area_square_deg = float(field["requested_area_square_deg"])
        field_checks = {
            "development_partition": field["experiment_partition"] == "development",
            "validation_identifier_absent": field_id not in validation_field_ids,
            "leaf_counts_conserve_root": sum(strip.measured_source_count for strip in leaf_strips)
            == planned[0].measured_source_count,
            "every_leaf_within_limit": all(
                strip.measured_source_count <= maximum_rows_per_strip for strip in leaf_strips
            ),
            "retrieval_complete": bool(retrieval_result["complete"]),
            "retrieved_count_matches_plan": len(combined) == planned[0].measured_source_count,
            "source_identifiers_unique": combined["source_id"].is_unique,
            "raw_columns_present": set(RAW_GAIA_COLUMNS).issubset(combined.columns),
            "probabilities_finite": np.isfinite(scored["point_source_logistic_probability"]).all(),
            "selector_version_frozen": scored["point_source_selector_version"]
            .eq(SELECTOR_VERSION)
            .all(),
            "checkpoints_valid": all(retriever.checkpoint_valid(strip) for strip in leaf_strips),
        }
        field_checks = {name: bool(value) for name, value in field_checks.items()}
        if not all(field_checks.values()):
            raise RuntimeError(f"Field {field_id} failed retrieval checks: {field_checks}")
        summary_records.append(
            {
                "retrieval_version": RETRIEVAL_VERSION,
                "pilot_id": field["pilot_id"],
                "grid_id": field["grid_id"],
                "field_id": field_id,
                "pilot_selection_reason": field["pilot_selection_reason"],
                "is_single_field_performance_benchmark": bool(
                    field["is_single_field_performance_benchmark"]
                ),
                "hemisphere": field["hemisphere"],
                "equal_area_latitude_band_index": int(field["equal_area_latitude_band_index"]),
                "absolute_ecliptic_latitude_band": field["absolute_ecliptic_latitude_band"],
                "environment_flag_state": field["environment_flag_state"],
                "ra_deg": float(field["ra_deg"]),
                "dec_deg": float(field["dec_deg"]),
                "galactic_latitude_deg": float(field["galactic_latitude_deg"]),
                "ecliptic_latitude_deg": float(field["ecliptic_latitude_deg"]),
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
                "plan_reused": reused_plan,
                "newly_retrieved_strip_count": len(retrieval_result["retrieved_strip_ids"]),
                "reused_checkpoint_count": len(retrieval_result["skipped_strip_ids"]),
                "combined_source_identifier_sha256": source_identifier_sha256(combined),
                "checkpoint_source_bytes": sum(int(record["source_bytes"]) for record in inventory),
                "planning_seconds": planning_seconds,
                "retrieval_seconds": retrieval_seconds,
                "selector_seconds": scoring_seconds,
                "field_seconds": perf_counter() - field_started,
            }
        )
        receipt = {
            "retrieval_version": RETRIEVAL_VERSION,
            "field_id": field_id,
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "plan_contract": expected_contract,
            "plan_reused": reused_plan,
            "external_plan_sha256": file_sha256(external_plan_path),
            "retrieval_result": retrieval_result,
            "checkpoint_inventory": inventory,
            "field_checks": field_checks,
        }
        receipt_path = field_directory / "field_receipt.json"
        write_json_atomic(receipt_path, receipt)
        receipt_records.append(
            {
                "field_id": field_id,
                "path": str(receipt_path.resolve()),
                "sha256": file_sha256(receipt_path),
            }
        )
        write_frame_atomic(pd.DataFrame(summary_records), LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY)
        write_frame_atomic(pd.DataFrame(plan_records), LARGE_SKY_DEVELOPMENT_RETRIEVAL_PLAN)

    summary = pd.DataFrame(summary_records)
    plan = pd.DataFrame(plan_records)
    output_field_ids = set(summary["field_id"].astype(str))
    checks = {
        "all_twelve_frozen_pilot_fields_completed": len(summary) == len(pilot) == 12
        and output_field_ids == pilot_field_ids,
        "no_validation_field_queried_or_summarized": validation_field_ids.isdisjoint(
            output_field_ids | set(plan["field_id"].astype(str))
        ),
        "all_field_counts_match_retrieval": summary["measured_source_count"]
        .eq(summary["retrieved_source_count"])
        .all(),
        "all_fields_have_unique_identifier_hashes": summary[
            "combined_source_identifier_sha256"
        ].is_unique,
        "all_leaf_strips_within_limit": plan.loc[
            plan["is_leaf"].astype(bool), "measured_source_count"
        ]
        .le(maximum_rows_per_strip)
        .all(),
        "benchmark_plan_and_checkpoints_reused": bool(
            summary.loc[summary["is_single_field_performance_benchmark"], "plan_reused"].iloc[0]
        )
        and int(
            summary.loc[
                summary["is_single_field_performance_benchmark"],
                "newly_retrieved_strip_count",
            ].iloc[0]
        )
        == 0,
        "all_position_coverage_categories_preserved": set(
            summary["absolute_ecliptic_latitude_band"]
        )
        == set(pilot["absolute_ecliptic_latitude_band"])
        and set(
            zip(
                summary["hemisphere"],
                summary["equal_area_latitude_band_index"],
                strict=True,
            )
        )
        == set(
            zip(
                pilot["hemisphere"],
                pilot["equal_area_latitude_band_index"],
                strict=True,
            )
        ),
        "external_receipt_for_every_field": len(receipt_records) == len(pilot),
        "validation_remains_unopened": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    manifest = {
        "retrieval_version": RETRIEVAL_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "retrieval_scope": "twelve_frozen_development_fields_full_19_columns",
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
                LARGE_SKY_DEVELOPMENT_BENCHMARK_MANIFEST,
                GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
                POINT_SOURCE_LOGISTIC_MODEL,
                POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
            )
        ],
        "selector_version": SELECTOR_VERSION,
        "selector_threshold": selector.threshold,
        "minimum_g_magnitude": MINIMUM_G_MAGNITUDE,
        "maximum_g_magnitude": MAXIMUM_G_MAGNITUDE,
        "raw_gaia_columns": RAW_GAIA_COLUMNS,
        "maximum_rows_per_strip": maximum_rows_per_strip,
        "pilot_field_ids": sorted(pilot_field_ids),
        "held_back_validation_field_count": len(validation_field_ids),
        "validation_selector_results_opened": False,
        "total_retrieved_source_count": int(summary["retrieved_source_count"].sum()),
        "total_selected_source_count": int(summary["selected_source_count"].sum()),
        "total_usable_area_square_deg": float(summary["usable_area_square_deg"].sum()),
        "total_final_strip_count": int(summary["final_strip_count"].sum()),
        "total_checkpoint_source_bytes": int(summary["checkpoint_source_bytes"].sum()),
        "total_elapsed_seconds": perf_counter() - run_started,
        "external_field_receipts": receipt_records,
        "outputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                LARGE_SKY_DEVELOPMENT_RETRIEVAL_PLAN,
                LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY,
            )
        ],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Large-sky development retrieval failed: {checks}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
