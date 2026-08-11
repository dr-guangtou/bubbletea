"""Freeze the one-time large-sky validation run before opening reserved fields."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
    LARGE_SKY_DEVELOPMENT_MODEL_ARTIFACT,
    LARGE_SKY_DEVELOPMENT_MODEL_MANIFEST,
    LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
    LARGE_SKY_DIRECT_BACKGROUND_CONTRACT,
    LARGE_SKY_DIRECT_BACKGROUND_MANIFEST,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_FIELD_GRID_MANIFEST,
    LARGE_SKY_VALIDATION_RUN_CONTRACT,
    POINT_SOURCE_LOGISTIC_MODEL,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256
from scripts.phase3_background.run_large_sky_development_scale import stable_processing_order
from scripts.utils.point_source_selector import SELECTOR_VERSION

VALIDATION_RUN_VERSION = "large_sky_validation_scale_v1"
CONTRACT_VERSION = "large_sky_validation_run_contract_v1"


def stable_contract_identifier(contract: dict[str, object]) -> str:
    """Return an identifier that changes whenever a frozen rule changes."""
    encoded = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    return f"validation_run_contract_{hashlib.sha256(encoded).hexdigest()[:20]}"


def main() -> None:
    """Write or verify the count-blind one-time validation contract."""
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    validation = grid.loc[grid["experiment_partition"].eq("validation")].copy()
    development = grid.loc[grid["experiment_partition"].eq("development")].copy()
    validation["processing_order"] = validation["field_id"].map(
        lambda field_id: stable_processing_order(str(field_id), VALIDATION_RUN_VERSION)
    )
    validation = validation.sort_values(["processing_order", "field_id"])
    direct_manifest = json.loads(LARGE_SKY_DIRECT_BACKGROUND_MANIFEST.read_text(encoding="utf-8"))
    direct_contract = json.loads(LARGE_SKY_DIRECT_BACKGROUND_CONTRACT.read_text(encoding="utf-8"))
    model_manifest = json.loads(LARGE_SKY_DEVELOPMENT_MODEL_MANIFEST.read_text(encoding="utf-8"))
    retrieval_limit = json.loads(
        GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST.read_text(encoding="utf-8")
    )
    contract_core = {
        "contract_version": CONTRACT_VERSION,
        "validation_run_version": VALIDATION_RUN_VERSION,
        "grid_id": str(validation["grid_id"].iloc[0]),
        "validation_field_ids_in_processing_order": validation["field_id"].astype(str).tolist(),
        "validation_sky_block_ids": sorted(validation["sky_block_id"].astype(str).unique()),
        "retrieval": {
            "field_count": 102,
            "maximum_rows_per_strip": int(retrieval_limit["provisional_safe_rows_per_strip"]),
            "archive_query_timeout_seconds": 180,
            "field_attempt_timeout_seconds": 300,
            "default_maximum_new_fields": 0,
            "raw_selector_columns_unchanged": True,
            "selector_version": SELECTOR_VERSION,
            "exact_requested_area_used": True,
            "failures_preserved_not_zero": True,
        },
        "primary_evaluation": {
            "procedure_id": direct_manifest["selected_procedure_id"],
            "development_fields_supply_reference_only": True,
            "same_five_absolute_galactic_latitude_bands": True,
            "reference_center": "development_band_median",
            "report_reference_mean": True,
            "report_central_measured_ranges": [0.68, 0.95],
            "metrics": [
                "median_absolute_log_density_error",
                "root_mean_square_log_density_error",
                "empirical_68_percent_range_coverage",
                "empirical_95_percent_range_coverage",
            ],
            "preserve_each_validation_field_result": True,
            "no_retuning": True,
        },
        "secondary_diagnostic": {
            "model_id": model_manifest["selected_model_id"],
            "model_role": "diagnostic_interpolation_only",
            "settings": model_manifest["selected_model_final_settings"],
            "use_frozen_serialized_model": True,
            "report_same_four_metrics": True,
            "no_refit_or_retuning": True,
        },
        "interpretation": {
            "compare_development_and_validation_metrics": True,
            "report_environment_flags_without_excluding_fields": True,
            "report_largest_absolute_residuals": 10,
            "do_not_approve_individual_fields_as_scientific_backgrounds": True,
            "do_not_change_the_twenty_degree_applicability_limit": True,
        },
    }
    contract_id = stable_contract_identifier(contract_core)
    validation_ids = set(validation["field_id"].astype(str))
    development_ids = set(development["field_id"].astype(str))
    measured_development_ids = set(
        pd.read_csv(LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY)["field_id"].astype(str)
    )
    checks = {
        "exactly_one_hundred_two_validation_fields_declared": len(validation_ids) == 102,
        "exactly_three_hundred_ninety_eight_development_fields_declared": len(development_ids)
        == 398,
        "partitions_are_disjoint": validation_ids.isdisjoint(development_ids),
        "all_development_measurements_available": measured_development_ids == development_ids,
        "processing_order_is_complete_and_unique": len(
            contract_core["validation_field_ids_in_processing_order"]
        )
        == len(validation_ids)
        and len(set(contract_core["validation_field_ids_in_processing_order"]))
        == len(validation_ids),
        "direct_procedure_is_frozen_latitude_band": direct_manifest["selected_procedure_id"]
        == "galactic_latitude_band"
        and direct_manifest["contract_id"] == direct_contract["contract_id"],
        "fitted_model_is_diagnostic_only": direct_manifest["fitted_model_role"]
        == "diagnostic_interpolation_only",
        "direct_validation_was_unopened": direct_manifest["validation_selector_results_opened"]
        is False,
        "model_validation_was_unopened": model_manifest["validation_selector_results_opened"]
        is False,
        "all_input_artifacts_passed_their_checks": all(
            artifact["passed_count"] == artifact["check_count"]
            for artifact in (
                direct_manifest,
                direct_contract,
                model_manifest,
                json.loads(LARGE_SKY_FIELD_GRID_MANIFEST.read_text(encoding="utf-8")),
                retrieval_limit,
            )
        ),
        "no_field_scientifically_approved": not grid["eligible_for_scientific_background"]
        .astype(bool)
        .any(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    inputs = (
        LARGE_SKY_FIELD_GRID,
        LARGE_SKY_FIELD_GRID_MANIFEST,
        LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
        LARGE_SKY_DIRECT_BACKGROUND_CONTRACT,
        LARGE_SKY_DIRECT_BACKGROUND_MANIFEST,
        LARGE_SKY_DEVELOPMENT_MODEL_ARTIFACT,
        LARGE_SKY_DEVELOPMENT_MODEL_MANIFEST,
        GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
        POINT_SOURCE_LOGISTIC_MODEL,
        POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    )
    report = {
        **contract_core,
        "contract_id": contract_id,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "frozen_before_reserved_field_retrieval",
        "validation_selector_results_opened": False,
        "archive_queries_executed": 0,
        "scientific_background_approval": False,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in inputs
        ],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    if not all(checks.values()):
        raise RuntimeError(f"Validation run contract failed: {checks}")
    serialized = json.dumps(report, indent=2) + "\n"
    if LARGE_SKY_VALIDATION_RUN_CONTRACT.exists():
        existing = json.loads(LARGE_SKY_VALIDATION_RUN_CONTRACT.read_text(encoding="utf-8"))
        if existing["contract_id"] != contract_id:
            raise RuntimeError("Existing validation contract differs from the frozen rules")
        return
    LARGE_SKY_VALIDATION_RUN_CONTRACT.write_text(serialized, encoding="utf-8")


if __name__ == "__main__":
    main()
