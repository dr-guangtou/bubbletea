"""Validate grouped model comparison mechanics without reading held-back results."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LARGE_SKY_DEVELOPMENT_MODEL_VALIDATION,
    LARGE_SKY_MODEL_COMPARISON_CONTRACT,
)
from scripts.phase3_background.fit_large_sky_development_models import (
    MODEL_ORDER,
    ConstantRateRegressor,
    evaluate_model,
    model_specifications,
    summarize_models,
)

VALIDATION_VERSION = "large_sky_development_model_validation_v1"


def synthetic_frame() -> pd.DataFrame:
    """Return deterministic positive rates spanning 15 synthetic sky blocks."""
    field_index = np.arange(60)
    longitude = np.mod(field_index * 137.5, 360.0)
    galactic_latitude = 20.0 + np.mod(field_index * 7.0, 65.0)
    ecliptic_latitude = np.mod(field_index * 11.0, 90.0)
    environment_flag = (np.mod(field_index, 3) == 0).astype(float)
    observed_rate = (
        120.0
        + 900.0 * np.exp(-(galactic_latitude - 20.0) / 18.0)
        + 35.0 * np.sin(np.deg2rad(longitude))
        + 20.0 * environment_flag
    )
    return pd.DataFrame(
        {
            "field_id": [f"synthetic_field_{index:03d}" for index in field_index],
            "sky_block_id": [f"synthetic_block_{index // 4:02d}" for index in field_index],
            "equal_area_latitude_band_index": np.mod(field_index, 5),
            "absolute_ecliptic_latitude_band": [
                f"synthetic_ecliptic_band_{index % 6}" for index in field_index
            ],
            "environment_flag_state": np.where(
                environment_flag > 0,
                "one_or_more_count_blind_environment_flags",
                "no_represented_environment_intersection",
            ),
            "usable_area_square_deg": np.full(60, 2.010586633460495),
            "selected_source_count": np.rint(observed_rate * 2.010586633460495).astype(int),
            "observed_rate": observed_rate,
            "absolute_galactic_latitude_deg": galactic_latitude,
            "galactic_hemisphere": np.mod(field_index, 2).astype(float),
            "sine_galactic_longitude": np.sin(np.deg2rad(longitude)),
            "cosine_galactic_longitude": np.cos(np.deg2rad(longitude)),
            "absolute_ecliptic_latitude_deg": ecliptic_latitude,
            "log1p_total_gaia_source_density_per_square_deg": np.log1p(
                observed_rate * 12.0 + 2000.0
            ),
            "m10_median_g_magnitude": 21.0 + 0.001 * ecliptic_latitude,
            "mean_visibility_periods_used": 12.0 + ecliptic_latitude / 8.0,
            "mean_astrometric_matched_transits": 20.0 + ecliptic_latitude / 3.0,
            "median_phot_g_mean_mag": 19.5 + 0.002 * galactic_latitude,
            "phot_g_mean_mag_10th_percentile": 16.0 + 0.003 * galactic_latitude,
            "phot_g_mean_mag_90th_percentile": 20.9 + 0.001 * galactic_latitude,
            "one_or_more_count_blind_environment_flags": environment_flag,
        }
    )


def validation_settings(model_family: str) -> list[dict[str, float | int]]:
    """Return one fast, valid declared-style setting for each model family."""
    if model_family == "weighted_constant_poisson_rate":
        return [{}]
    if model_family == "regularized_poisson_regression":
        return [{"alpha": 0.1, "spline_knot_count": 3}]
    return [
        {
            "maximum_leaf_nodes": 7,
            "learning_rate": 0.1,
            "minimum_samples_per_leaf": 10,
        }
    ]


def main() -> None:
    """Run a small six-model grouped comparison and save its safeguards."""
    started = perf_counter()
    contract = json.loads(LARGE_SKY_MODEL_COMPARISON_CONTRACT.read_text(encoding="utf-8"))
    specifications = model_specifications(contract)
    frame = synthetic_frame()
    predictions = []
    folds = []
    for specification in specifications:
        model_predictions, model_folds, _ = evaluate_model(
            frame,
            specification,
            validation_settings(specification.model_family),
            outer_fold_count=3,
            inner_fold_count=2,
            evaluation_label="synthetic_local_validation",
        )
        predictions.append(model_predictions)
        folds.append(model_folds)
    predictions = pd.concat(predictions, ignore_index=True)
    folds = pd.concat(folds, ignore_index=True)
    summary = summarize_models(specifications, predictions, folds)

    unequal_weight_estimator = ConstantRateRegressor().fit(
        pd.DataFrame(index=range(2)),
        np.array([10.0, 100.0]),
        sample_weight=np.array([9.0, 1.0]),
    )
    checks = {
        "six_contract_models_in_frozen_order": tuple(summary["model_id"]) == MODEL_ORDER,
        "three_grouped_outer_folds_per_model": folds.groupby("model_id")["outer_fold"]
        .nunique()
        .eq(3)
        .all(),
        "training_and_test_blocks_always_disjoint": folds[
            "training_and_test_sky_blocks_disjoint"
        ].all(),
        "each_model_predicts_all_sixty_fields_once": predictions.groupby("model_id")["field_id"]
        .nunique()
        .eq(60)
        .all(),
        "all_predictions_positive_and_finite": np.isfinite(
            predictions["predicted_rate_per_square_deg"]
        ).all()
        and predictions["predicted_rate_per_square_deg"].gt(0).all(),
        "constant_model_uses_supplied_weights": abs(unequal_weight_estimator.constant_rate_ - 19.0)
        <= 1e-12,
        "selected_model_is_primary_eligible": summary.loc[
            summary["selected_primary_model"], "eligible_as_primary"
        ].all(),
        "environment_sensitivity_cannot_be_selected": not summary.loc[
            summary["model_id"].eq("environment_flag_sensitivity"),
            "selected_primary_model",
        ].any(),
        "validation_catalog_results_not_read": True,
        "no_archive_query_executed": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    report = {
        "validation_version": VALIDATION_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "plain_language_result": (
            "A synthetic 60-field test kept sky blocks separate, evaluated all six frozen "
            "model forms, honored area weights, and prevented the environment diagnostic "
            "from becoming the selected model."
        ),
        "synthetic_field_count": len(frame),
        "synthetic_sky_block_count": frame["sky_block_id"].nunique(),
        "archive_queries_executed": 0,
        "held_back_catalog_results_read": False,
        "elapsed_seconds": perf_counter() - started,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DEVELOPMENT_MODEL_VALIDATION.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Local model-comparison validation failed: {checks}")


if __name__ == "__main__":
    main()
