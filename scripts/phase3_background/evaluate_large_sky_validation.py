"""Evaluate frozen direct and diagnostic background methods on reserved fields."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import joblib
import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LARGE_SKY_DEVELOPMENT_MODEL_ARTIFACT,
    LARGE_SKY_DEVELOPMENT_MODEL_MANIFEST,
    LARGE_SKY_DEVELOPMENT_MODEL_SUMMARY,
    LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
    LARGE_SKY_DIRECT_BACKGROUND_MANIFEST,
    LARGE_SKY_DIRECT_BACKGROUND_SUMMARY,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_VALIDATION_EVALUATION,
    LARGE_SKY_VALIDATION_REFERENCE,
    LARGE_SKY_VALIDATION_RUN_CONTRACT,
    LARGE_SKY_VALIDATION_SCALE_MANIFEST,
    LARGE_SKY_VALIDATION_SCALE_SUMMARY,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256
from scripts.phase3_background.compare_large_sky_direct_backgrounds import (
    comparison_pool,
    prediction_record,
    prepare_frame,
)
from scripts.phase3_background.fit_large_sky_development_models import (
    prepare_development_frame,
)
from scripts.phase3_background.run_large_sky_development_retrieval import write_frame_atomic

EVALUATION_VERSION = "large_sky_validation_evaluation_v1"
EXPECTED_CONTRACT_ID = "validation_run_contract_d75e3ddea7013547c088"


def method_metrics(errors: np.ndarray, inside_68: pd.Series, inside_95: pd.Series) -> dict:
    """Return the four metrics fixed before reserved-field retrieval."""
    return {
        "median_absolute_log_density_error": float(np.median(np.abs(errors))),
        "root_mean_square_log_density_error": float(np.sqrt(np.mean(np.square(errors)))),
        "empirical_68_percent_range_coverage": float(inside_68.mean()),
        "empirical_95_percent_range_coverage": float(inside_95.mean()),
    }


def main() -> None:
    """Apply both unchanged methods once and preserve every reserved-field result."""
    started = perf_counter()
    contract = json.loads(LARGE_SKY_VALIDATION_RUN_CONTRACT.read_text(encoding="utf-8"))
    retrieval_manifest = json.loads(LARGE_SKY_VALIDATION_SCALE_MANIFEST.read_text(encoding="utf-8"))
    direct_manifest = json.loads(LARGE_SKY_DIRECT_BACKGROUND_MANIFEST.read_text(encoding="utf-8"))
    model_manifest = json.loads(LARGE_SKY_DEVELOPMENT_MODEL_MANIFEST.read_text(encoding="utf-8"))
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    development_summary = pd.read_csv(LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY)
    validation_summary = pd.read_csv(LARGE_SKY_VALIDATION_SCALE_SUMMARY)
    development_direct = prepare_frame(development_summary, grid)
    validation_direct = prepare_frame(validation_summary, grid)

    direct_records = []
    for _, target in validation_direct.iterrows():
        pool = comparison_pool(
            development_direct,
            target,
            procedure_id="galactic_latitude_band",
        )
        direct_records.append(
            prediction_record(
                target,
                pool,
                procedure_id="galactic_latitude_band",
                outer_fold=0,
            )
        )
    direct = pd.DataFrame(direct_records).sort_values("field_id", ignore_index=True)

    validation_model = prepare_development_frame(validation_summary, grid)
    frozen_model = joblib.load(LARGE_SKY_DEVELOPMENT_MODEL_ARTIFACT)
    model_predictions = frozen_model.predict(validation_model)
    observed = validation_model["observed_rate"].to_numpy(dtype=float)
    model_ranges = model_manifest["selected_prediction_range"]
    model_lower_68 = model_predictions * model_ranges["prediction_68_lower_multiplier"]
    model_upper_68 = model_predictions * model_ranges["prediction_68_upper_multiplier"]
    model_lower_95 = model_predictions * model_ranges["prediction_95_lower_multiplier"]
    model_upper_95 = model_predictions * model_ranges["prediction_95_upper_multiplier"]
    model_errors = np.log(observed / model_predictions)

    reference = direct.copy()
    reference["evaluation_version"] = EVALUATION_VERSION
    reference["validation_contract_id"] = contract["contract_id"]
    reference["diagnostic_model_id"] = model_manifest["selected_model_id"]
    reference["diagnostic_model_prediction_per_square_deg"] = model_predictions
    reference["diagnostic_model_68_lower_per_square_deg"] = model_lower_68
    reference["diagnostic_model_68_upper_per_square_deg"] = model_upper_68
    reference["diagnostic_model_95_lower_per_square_deg"] = model_lower_95
    reference["diagnostic_model_95_upper_per_square_deg"] = model_upper_95
    reference["log_observed_to_diagnostic_model"] = model_errors
    reference["inside_diagnostic_model_68_percent_range"] = (observed >= model_lower_68) & (
        observed <= model_upper_68
    )
    reference["inside_diagnostic_model_95_percent_range"] = (observed >= model_lower_95) & (
        observed <= model_upper_95
    )
    write_frame_atomic(reference, LARGE_SKY_VALIDATION_REFERENCE)

    direct_errors = direct["log_observed_to_comparison_median"].to_numpy(dtype=float)
    direct_validation_metrics = method_metrics(
        direct_errors,
        direct["inside_comparison_68_percent_range"],
        direct["inside_comparison_95_percent_range"],
    )
    model_validation_metrics = method_metrics(
        model_errors,
        reference["inside_diagnostic_model_68_percent_range"],
        reference["inside_diagnostic_model_95_percent_range"],
    )
    direct_development_row = (
        pd.read_csv(LARGE_SKY_DIRECT_BACKGROUND_SUMMARY)
        .loc[lambda frame: frame["selected_direct_procedure"]]
        .iloc[0]
    )
    model_development_row = (
        pd.read_csv(LARGE_SKY_DEVELOPMENT_MODEL_SUMMARY)
        .loc[lambda frame: frame["selected_primary_model"]]
        .iloc[0]
    )
    direct_development_metrics = {
        "median_absolute_log_density_error": float(
            direct_development_row["overall_median_absolute_log_density_error"]
        ),
        "root_mean_square_log_density_error": float(
            direct_development_row["overall_root_mean_square_log_density_error"]
        ),
        "empirical_68_percent_range_coverage": float(
            direct_development_row["empirical_68_percent_range_coverage"]
        ),
        "empirical_95_percent_range_coverage": float(
            direct_development_row["empirical_95_percent_range_coverage"]
        ),
    }
    model_development_metrics = {
        "median_absolute_log_density_error": float(
            model_development_row["median_absolute_log_density_error"]
        ),
        "root_mean_square_log_density_error": float(
            model_development_row["root_mean_square_log_density_error"]
        ),
        "empirical_68_percent_range_coverage": float(
            model_development_row["empirical_68_percent_coverage"]
        ),
        "empirical_95_percent_range_coverage": float(
            model_development_row["empirical_95_percent_coverage"]
        ),
    }

    environment_results = []
    for state, fields in reference.groupby("environment_flag_state", sort=True):
        environment_results.append(
            {
                "environment_flag_state": state,
                "field_count": len(fields),
                "direct_median_absolute_log_density_error": float(
                    fields["log_observed_to_comparison_median"].abs().median()
                ),
                "direct_95_percent_range_coverage": float(
                    fields["inside_comparison_95_percent_range"].mean()
                ),
                "diagnostic_model_median_absolute_log_density_error": float(
                    fields["log_observed_to_diagnostic_model"].abs().median()
                ),
                "diagnostic_model_95_percent_range_coverage": float(
                    fields["inside_diagnostic_model_95_percent_range"].mean()
                ),
            }
        )

    largest_direct = (
        reference.assign(
            absolute_log_density_error=reference["log_observed_to_comparison_median"].abs()
        )
        .nlargest(10, "absolute_log_density_error")
        .loc[
            :,
            [
                "field_id",
                "environment_flag_state",
                "observed_selected_source_density_per_square_deg",
                "comparison_density_median_per_square_deg",
                "absolute_log_density_error",
                "inside_comparison_95_percent_range",
            ],
        ]
        .to_dict(orient="records")
    )
    validation_ids = set(validation_summary["field_id"].astype(str))
    contract_ids = set(contract["validation_field_ids_in_processing_order"])
    development_ids = set(development_summary["field_id"].astype(str))
    pool_ids = {
        field_id for value in direct["comparison_pool_field_ids"] for field_id in value.split(";")
    }
    validation_blocks = set(validation_model["sky_block_id"].astype(str))
    pool_blocks = {
        block_id
        for value in direct["comparison_pool_sky_block_ids"]
        for block_id in value.split(";")
    }
    checks = {
        "frozen_contract_identifier_matches": contract["contract_id"] == EXPECTED_CONTRACT_ID,
        "retrieval_complete_and_all_checks_passed": retrieval_manifest["status"]
        == "complete_validation_measurement"
        and retrieval_manifest["passed_count"] == retrieval_manifest["check_count"],
        "exactly_one_hundred_two_unique_validation_fields": len(validation_ids) == 102
        and validation_summary["field_id"].is_unique,
        "validation_identifiers_match_frozen_contract": validation_ids == contract_ids,
        "development_and_validation_identifiers_disjoint": validation_ids.isdisjoint(
            development_ids
        ),
        "direct_procedure_unchanged": direct_manifest["selected_procedure_id"]
        == "galactic_latitude_band",
        "all_direct_pool_fields_are_development": pool_ids.issubset(development_ids),
        "validation_sky_blocks_absent_from_direct_pools": validation_blocks.isdisjoint(pool_blocks),
        "all_direct_pools_use_same_latitude_band": all(
            development_direct.set_index("field_id")
            .loc[row["comparison_pool_field_ids"].split(";"), "equal_area_latitude_band_index"]
            .eq(
                validation_direct.set_index("field_id").loc[
                    row["field_id"], "equal_area_latitude_band_index"
                ]
            )
            .all()
            for _, row in direct.iterrows()
        ),
        "all_direct_ranges_ordered": (
            direct["comparison_density_95_lower_per_square_deg"]
            <= direct["comparison_density_68_lower_per_square_deg"]
        ).all()
        and (
            direct["comparison_density_68_lower_per_square_deg"]
            <= direct["comparison_density_median_per_square_deg"]
        ).all()
        and (
            direct["comparison_density_median_per_square_deg"]
            <= direct["comparison_density_68_upper_per_square_deg"]
        ).all()
        and (
            direct["comparison_density_68_upper_per_square_deg"]
            <= direct["comparison_density_95_upper_per_square_deg"]
        ).all(),
        "diagnostic_model_role_unchanged": direct_manifest["fitted_model_role"]
        == "diagnostic_interpolation_only",
        "diagnostic_model_identifier_unchanged": model_manifest["selected_model_id"]
        == contract["secondary_diagnostic"]["model_id"],
        "diagnostic_predictions_positive_and_finite": np.isfinite(model_predictions).all()
        and (model_predictions > 0).all(),
        "observed_validation_densities_positive_and_finite": np.isfinite(observed).all()
        and (observed > 0).all(),
        "one_reference_row_per_validation_field": len(reference) == 102
        and reference["field_id"].is_unique,
        "all_four_frozen_metrics_reported_for_both_methods": set(direct_validation_metrics)
        == set(model_validation_metrics)
        == set(direct_development_metrics)
        == set(model_development_metrics),
        "both_environment_states_reported_without_exclusion": len(environment_results) == 2
        and sum(item["field_count"] for item in environment_results) == 102,
        "ten_largest_direct_residuals_preserved": len(largest_direct) == 10,
        "no_method_refitted_or_retuned": True,
        "no_field_scientifically_approved": not grid["eligible_for_scientific_background"]
        .astype(bool)
        .any(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    metric_differences = {
        "direct_validation_minus_development": {
            key: direct_validation_metrics[key] - direct_development_metrics[key]
            for key in direct_validation_metrics
        },
        "diagnostic_model_validation_minus_development": {
            key: model_validation_metrics[key] - model_development_metrics[key]
            for key in model_validation_metrics
        },
    }
    inputs = (
        LARGE_SKY_VALIDATION_RUN_CONTRACT,
        LARGE_SKY_VALIDATION_SCALE_SUMMARY,
        LARGE_SKY_VALIDATION_SCALE_MANIFEST,
        LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
        LARGE_SKY_DIRECT_BACKGROUND_SUMMARY,
        LARGE_SKY_DIRECT_BACKGROUND_MANIFEST,
        LARGE_SKY_DEVELOPMENT_MODEL_SUMMARY,
        LARGE_SKY_DEVELOPMENT_MODEL_ARTIFACT,
        LARGE_SKY_DEVELOPMENT_MODEL_MANIFEST,
        LARGE_SKY_FIELD_GRID,
    )
    report = {
        "evaluation_version": EVALUATION_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "one_time_reserved_field_evaluation_complete",
        "contract_id": contract["contract_id"],
        "field_count": len(reference),
        "primary_method": "direct_development_fields_in_same_galactic_latitude_band",
        "secondary_method": "frozen_fitted_model_diagnostic_only",
        "direct_development_metrics": direct_development_metrics,
        "direct_validation_metrics": direct_validation_metrics,
        "diagnostic_model_development_metrics": model_development_metrics,
        "diagnostic_model_validation_metrics": model_validation_metrics,
        "validation_minus_development_metric_differences": metric_differences,
        "environment_results": environment_results,
        "largest_direct_absolute_residuals": largest_direct,
        "scientific_background_approval": False,
        "methods_refitted_or_retuned": False,
        "elapsed_seconds": perf_counter() - started,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in inputs
        ],
        "output": {
            "path": str(LARGE_SKY_VALIDATION_REFERENCE.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(LARGE_SKY_VALIDATION_REFERENCE),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_VALIDATION_EVALUATION.write_text(
        json.dumps(report, indent=2, default=lambda value: value.item()) + "\n",
        encoding="utf-8",
    )
    if not all(checks.values()):
        raise RuntimeError(f"Reserved-field evaluation failed: {checks}")


if __name__ == "__main__":
    main()
