"""Fit and compare the six frozen large-sky models on development fields only."""

import itertools
import json
import math
import sys
import warnings
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_poisson_deviance
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LARGE_SKY_DEVELOPMENT_MODEL_ARTIFACT,
    LARGE_SKY_DEVELOPMENT_MODEL_BAND_RESULTS,
    LARGE_SKY_DEVELOPMENT_MODEL_ENVIRONMENT_RESULTS,
    LARGE_SKY_DEVELOPMENT_MODEL_FOLD_RESULTS,
    LARGE_SKY_DEVELOPMENT_MODEL_MANIFEST,
    LARGE_SKY_DEVELOPMENT_MODEL_PREDICTIONS,
    LARGE_SKY_DEVELOPMENT_MODEL_SUMMARY,
    LARGE_SKY_DEVELOPMENT_MODEL_TUNING_RESULTS,
    LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST,
    LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_MODEL_COMPARISON_CONTRACT,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256

COMPARISON_VERSION = "large_sky_development_model_comparison_v1"
EXPECTED_CONTRACT_ID = "model_contract_8da80ba5e4bd6d3027e6"
RATE_FLOOR = 1e-12
MODEL_ORDER = (
    "constant_rate_baseline",
    "galactic_latitude_spline",
    "sky_position_spline",
    "sky_position_and_gaia_conditions",
    "nonlinear_sky_and_gaia_benchmark",
    "environment_flag_sensitivity",
)
BINARY_FEATURES = {
    "galactic_hemisphere",
    "one_or_more_count_blind_environment_flags",
}
SPLINE_FEATURES = {
    "absolute_galactic_latitude_deg",
    "absolute_ecliptic_latitude_deg",
}


@dataclass(frozen=True)
class ModelSpecification:
    """Describe one model exactly as declared in the frozen contract."""

    model_id: str
    model_family: str
    features: tuple[str, ...]
    eligible_as_primary: bool
    complexity_rank: int


class ConstantRateRegressor(RegressorMixin, BaseEstimator):
    """Predict one area-weighted rate for every field."""

    def fit(
        self,
        features: pd.DataFrame,
        target_rate: np.ndarray,
        sample_weight: np.ndarray | None = None,
    ) -> "ConstantRateRegressor":
        """Measure the weighted mean training rate."""
        del features
        weights = np.ones(len(target_rate)) if sample_weight is None else sample_weight
        self.constant_rate_ = float(np.average(target_rate, weights=weights))
        return self

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Return the fitted rate for every supplied field."""
        return np.full(len(features), self.constant_rate_, dtype=float)


def prepare_development_frame(summary: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    """Build the frozen response, predictors, and diagnostic band labels."""
    grid_columns = [
        "field_id",
        "equal_area_latitude_band_index",
        "absolute_ecliptic_latitude_band",
        "experiment_partition",
    ]
    frame = summary.merge(
        grid[grid_columns],
        on="field_id",
        suffixes=("", "_grid"),
        validate="one_to_one",
    ).sort_values("field_id", ignore_index=True)
    longitude_radians = np.deg2rad(frame["galactic_longitude_deg"])
    frame = frame.assign(
        absolute_galactic_latitude_deg=frame["galactic_latitude_deg"].abs(),
        galactic_hemisphere=frame["galactic_latitude_deg"].ge(0).astype(float),
        sine_galactic_longitude=np.sin(longitude_radians),
        cosine_galactic_longitude=np.cos(longitude_radians),
        absolute_ecliptic_latitude_deg=frame["ecliptic_latitude_deg"].abs(),
        log1p_total_gaia_source_density_per_square_deg=np.log1p(
            frame["total_gaia_source_density_per_square_deg"]
        ),
        one_or_more_count_blind_environment_flags=frame["environment_flag_state"]
        .eq("one_or_more_count_blind_environment_flags")
        .astype(float),
        observed_rate=frame["selected_source_count"] / frame["usable_area_square_deg"],
    )
    return frame


def model_specifications(contract: dict[str, object]) -> list[ModelSpecification]:
    """Read model order and features from the frozen machine-readable contract."""
    specifications = []
    for rank, model in enumerate(contract["candidate_models"], start=1):
        specifications.append(
            ModelSpecification(
                model_id=str(model["model_id"]),
                model_family=str(model["model_family"]),
                features=tuple(model["features"]),
                eligible_as_primary=bool(model["eligible_as_primary"]),
                complexity_rank=rank,
            )
        )
    return specifications


def settings_grid(
    specification: ModelSpecification, contract: dict[str, object]
) -> list[dict[str, float | int]]:
    """Return only the settings declared before development scale-up."""
    tuning = contract["tuning"]
    if specification.model_family == "weighted_constant_poisson_rate":
        return [{}]
    if specification.model_family == "regularized_poisson_regression":
        return [
            {"alpha": float(alpha), "spline_knot_count": int(knot_count)}
            for knot_count, alpha in itertools.product(
                tuning["spline_knot_counts"], tuning["poisson_regression_alpha_values"]
            )
        ]
    if specification.model_family == "histogram_gradient_boosting_poisson_loss":
        return [
            {
                "maximum_leaf_nodes": int(maximum_leaf_nodes),
                "learning_rate": float(learning_rate),
                "minimum_samples_per_leaf": int(minimum_samples_per_leaf),
            }
            for maximum_leaf_nodes, learning_rate, minimum_samples_per_leaf in itertools.product(
                tuning["nonlinear_maximum_leaf_nodes"],
                tuning["nonlinear_learning_rates"],
                tuning["nonlinear_minimum_samples_per_leaf"],
            )
        ]
    raise ValueError(f"Unsupported model family: {specification.model_family}")


def build_estimator(
    specification: ModelSpecification, settings: dict[str, float | int]
) -> BaseEstimator:
    """Build one estimator without learning anything from held-out fields."""
    if specification.model_family == "weighted_constant_poisson_rate":
        return ConstantRateRegressor()
    if specification.model_family == "histogram_gradient_boosting_poisson_loss":
        return HistGradientBoostingRegressor(
            loss="poisson",
            learning_rate=float(settings["learning_rate"]),
            max_leaf_nodes=int(settings["maximum_leaf_nodes"]),
            min_samples_leaf=int(settings["minimum_samples_per_leaf"]),
            random_state=0,
        )
    spline_features = [feature for feature in specification.features if feature in SPLINE_FEATURES]
    binary_features = [feature for feature in specification.features if feature in BINARY_FEATURES]
    numeric_features = [
        feature
        for feature in specification.features
        if feature not in SPLINE_FEATURES and feature not in BINARY_FEATURES
    ]
    transformations = []
    if spline_features:
        transformations.append(
            (
                "smooth_latitudes",
                Pipeline(
                    [
                        (
                            "spline_basis",
                            SplineTransformer(
                                n_knots=int(settings["spline_knot_count"]),
                                degree=3,
                                include_bias=False,
                                extrapolation="linear",
                            ),
                        ),
                        ("scale_basis", StandardScaler()),
                    ]
                ),
                spline_features,
            )
        )
    if numeric_features:
        transformations.append(("scaled_numeric", StandardScaler(), numeric_features))
    if binary_features:
        transformations.append(("binary", "passthrough", binary_features))
    preprocessing = ColumnTransformer(transformations, remainder="drop")
    return Pipeline(
        [
            ("preprocessing", preprocessing),
            (
                "model",
                PoissonRegressor(
                    alpha=float(settings["alpha"]),
                    max_iter=2000,
                    tol=1e-8,
                ),
            ),
        ]
    )


def fit_estimator(
    estimator: BaseEstimator,
    specification: ModelSpecification,
    frame: pd.DataFrame,
) -> BaseEstimator:
    """Fit one estimator with exact field area as its statistical weight."""
    features = frame.loc[:, list(specification.features)]
    target = frame["observed_rate"].to_numpy(dtype=float)
    weights = frame["usable_area_square_deg"].to_numpy(dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        if isinstance(estimator, Pipeline):
            estimator.fit(features, target, model__sample_weight=weights)
        else:
            estimator.fit(features, target, sample_weight=weights)
    return estimator


def predict_rate(
    estimator: BaseEstimator,
    specification: ModelSpecification,
    frame: pd.DataFrame,
) -> np.ndarray:
    """Predict positive passing-source rates for supplied fields."""
    predictions = estimator.predict(frame.loc[:, list(specification.features)])
    return np.clip(np.asarray(predictions, dtype=float), RATE_FLOOR, None)


def poisson_deviance(frame: pd.DataFrame, predictions: np.ndarray) -> float:
    """Return area-weighted mean Poisson deviance for field rates."""
    return float(
        mean_poisson_deviance(
            frame["observed_rate"],
            predictions,
            sample_weight=frame["usable_area_square_deg"],
        )
    )


def log_error_metrics(frame: pd.DataFrame, predictions: np.ndarray) -> tuple[float, float]:
    """Return median absolute and root-mean-square log-rate errors."""
    errors = np.log(frame["observed_rate"].to_numpy(dtype=float) / predictions)
    return float(np.median(np.abs(errors))), float(np.sqrt(np.mean(np.square(errors))))


def serialized_settings(settings: dict[str, float | int]) -> str:
    """Return a stable compact representation of model settings."""
    return json.dumps(settings, sort_keys=True, separators=(",", ":"))


def tune_settings(
    frame: pd.DataFrame,
    specification: ModelSpecification,
    candidate_settings: list[dict[str, float | int]],
    inner_fold_count: int,
) -> tuple[dict[str, float | int], list[dict[str, object]]]:
    """Choose declared settings using grouped folds within training data only."""
    splitter = GroupKFold(n_splits=inner_fold_count)
    groups = frame["sky_block_id"].to_numpy()
    split_indices = list(splitter.split(frame, groups=groups))
    records = []
    for settings in candidate_settings:
        fold_scores = []
        for training_indices, test_indices in split_indices:
            training = frame.iloc[training_indices]
            test = frame.iloc[test_indices]
            estimator = build_estimator(specification, settings)
            fit_estimator(estimator, specification, training)
            fold_scores.append(poisson_deviance(test, predict_rate(estimator, specification, test)))
        records.append(
            {
                "settings_json": serialized_settings(settings),
                "mean_inner_poisson_deviance": float(np.mean(fold_scores)),
                "inner_fold_poisson_deviances_json": json.dumps(fold_scores),
            }
        )
    best_record = min(
        records,
        key=lambda record: (
            record["mean_inner_poisson_deviance"],
            record["settings_json"],
        ),
    )
    return json.loads(best_record["settings_json"]), records


def evaluate_model(
    frame: pd.DataFrame,
    specification: ModelSpecification,
    candidate_settings: list[dict[str, float | int]],
    outer_fold_count: int,
    inner_fold_count: int,
    evaluation_label: str = "primary_all_development_fields",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Produce grouped outer-fold predictions with training-only setting selection."""
    splitter = GroupKFold(n_splits=outer_fold_count)
    groups = frame["sky_block_id"].to_numpy()
    prediction_records = []
    fold_records = []
    tuning_records = []
    for outer_fold, (training_indices, test_indices) in enumerate(
        splitter.split(frame, groups=groups), start=1
    ):
        training = frame.iloc[training_indices]
        test = frame.iloc[test_indices]
        chosen_settings, tuning = tune_settings(
            training,
            specification,
            candidate_settings,
            inner_fold_count,
        )
        for record in tuning:
            tuning_records.append(
                {
                    "evaluation_label": evaluation_label,
                    "model_id": specification.model_id,
                    "outer_fold": outer_fold,
                    **record,
                }
            )
        estimator = build_estimator(specification, chosen_settings)
        fit_estimator(estimator, specification, training)
        predictions = predict_rate(estimator, specification, test)
        median_absolute_error, root_mean_square_error = log_error_metrics(test, predictions)
        training_groups = set(training["sky_block_id"])
        test_groups = set(test["sky_block_id"])
        fold_records.append(
            {
                "evaluation_label": evaluation_label,
                "model_id": specification.model_id,
                "outer_fold": outer_fold,
                "chosen_settings_json": serialized_settings(chosen_settings),
                "training_field_count": len(training),
                "test_field_count": len(test),
                "training_sky_block_count": len(training_groups),
                "test_sky_block_count": len(test_groups),
                "training_and_test_sky_blocks_disjoint": training_groups.isdisjoint(test_groups),
                "mean_poisson_deviance": poisson_deviance(test, predictions),
                "median_absolute_log_density_error": median_absolute_error,
                "root_mean_square_log_density_error": root_mean_square_error,
            }
        )
        for row_index, (_, field) in enumerate(test.iterrows()):
            prediction_records.append(
                {
                    "evaluation_label": evaluation_label,
                    "model_id": specification.model_id,
                    "outer_fold": outer_fold,
                    "field_id": field["field_id"],
                    "sky_block_id": field["sky_block_id"],
                    "equal_area_latitude_band_index": int(field["equal_area_latitude_band_index"]),
                    "absolute_ecliptic_latitude_band": field["absolute_ecliptic_latitude_band"],
                    "environment_flag_state": field["environment_flag_state"],
                    "usable_area_square_deg": float(field["usable_area_square_deg"]),
                    "observed_selected_source_count": int(field["selected_source_count"]),
                    "observed_rate_per_square_deg": float(field["observed_rate"]),
                    "predicted_rate_per_square_deg": float(predictions[row_index]),
                    "log_observed_to_predicted_rate": float(
                        np.log(field["observed_rate"] / predictions[row_index])
                    ),
                    "field_poisson_deviance": float(
                        mean_poisson_deviance([field["observed_rate"]], [predictions[row_index]])
                    ),
                }
            )
    return (
        pd.DataFrame(prediction_records),
        pd.DataFrame(fold_records),
        pd.DataFrame(tuning_records),
    )


def prediction_range_summary(predictions: pd.DataFrame) -> dict[str, float]:
    """Derive central multiplicative ranges from grouped out-of-fold residuals."""
    residuals = predictions["log_observed_to_predicted_rate"].to_numpy(dtype=float)
    quantiles = np.quantile(residuals, [0.025, 0.16, 0.84, 0.975])
    result = {
        "prediction_68_lower_multiplier": float(np.exp(quantiles[1])),
        "prediction_68_upper_multiplier": float(np.exp(quantiles[2])),
        "prediction_95_lower_multiplier": float(np.exp(quantiles[0])),
        "prediction_95_upper_multiplier": float(np.exp(quantiles[3])),
    }
    result["empirical_68_percent_coverage"] = float(
        np.mean((residuals >= quantiles[1]) & (residuals <= quantiles[2]))
    )
    result["empirical_95_percent_coverage"] = float(
        np.mean((residuals >= quantiles[0]) & (residuals <= quantiles[3]))
    )
    return result


def summarize_models(
    specifications: list[ModelSpecification],
    predictions: pd.DataFrame,
    fold_results: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize outer-fold performance and apply the frozen selection rule."""
    records = []
    for specification in specifications:
        model_folds = fold_results.loc[fold_results["model_id"].eq(specification.model_id)]
        model_predictions = predictions.loc[predictions["model_id"].eq(specification.model_id)]
        median_absolute_error, root_mean_square_error = log_error_metrics(
            model_predictions.rename(
                columns={
                    "observed_rate_per_square_deg": "observed_rate",
                    "usable_area_square_deg": "usable_area_square_deg",
                }
            ),
            model_predictions["predicted_rate_per_square_deg"].to_numpy(dtype=float),
        )
        fold_deviances = model_folds["mean_poisson_deviance"].to_numpy(dtype=float)
        records.append(
            {
                "comparison_version": COMPARISON_VERSION,
                "model_id": specification.model_id,
                "complexity_rank": specification.complexity_rank,
                "eligible_as_primary": specification.eligible_as_primary,
                "mean_outer_fold_poisson_deviance": float(np.mean(fold_deviances)),
                "outer_fold_poisson_deviance_standard_deviation": float(
                    np.std(fold_deviances, ddof=1)
                ),
                "outer_fold_poisson_deviance_standard_error": float(
                    np.std(fold_deviances, ddof=1) / math.sqrt(len(fold_deviances))
                ),
                "median_absolute_log_density_error": median_absolute_error,
                "root_mean_square_log_density_error": root_mean_square_error,
                **prediction_range_summary(model_predictions),
            }
        )
    summary = pd.DataFrame(records).sort_values("complexity_rank", ignore_index=True)
    eligible = summary.loc[summary["eligible_as_primary"]]
    best_index = eligible["mean_outer_fold_poisson_deviance"].idxmin()
    best_mean = float(summary.loc[best_index, "mean_outer_fold_poisson_deviance"])
    best_standard_error = float(
        summary.loc[best_index, "outer_fold_poisson_deviance_standard_error"]
    )
    threshold = best_mean + best_standard_error
    eligible_under_threshold = summary.loc[
        summary["eligible_as_primary"] & summary["mean_outer_fold_poisson_deviance"].le(threshold)
    ]
    selected_index = eligible_under_threshold["complexity_rank"].idxmin()
    summary["best_eligible_measured_score"] = summary.index == best_index
    summary["one_standard_error_threshold"] = threshold
    summary["inside_one_standard_error_threshold"] = summary["mean_outer_fold_poisson_deviance"].le(
        threshold
    )
    summary["selected_primary_model"] = summary.index == selected_index
    return summary


def environment_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Report predictive performance separately for both count-blind flag states."""
    records = []
    for (model_id, flag_state), fields in predictions.groupby(
        ["model_id", "environment_flag_state"], sort=True
    ):
        renamed = fields.rename(columns={"observed_rate_per_square_deg": "observed_rate"})
        predicted = fields["predicted_rate_per_square_deg"].to_numpy(dtype=float)
        median_absolute_error, root_mean_square_error = log_error_metrics(renamed, predicted)
        records.append(
            {
                "model_id": model_id,
                "environment_flag_state": flag_state,
                "field_count": len(fields),
                "mean_poisson_deviance": poisson_deviance(renamed, predicted),
                "median_absolute_log_density_error": median_absolute_error,
                "root_mean_square_log_density_error": root_mean_square_error,
                "mean_log_observed_to_predicted_rate": float(
                    fields["log_observed_to_predicted_rate"].mean()
                ),
            }
        )
    return pd.DataFrame(records)


def band_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Report residuals in the frozen Galactic and ecliptic latitude bands."""
    records = []
    band_columns = {
        "galactic_equal_area_band": "equal_area_latitude_band_index",
        "absolute_ecliptic_latitude_band": "absolute_ecliptic_latitude_band",
    }
    for model_id, model_fields in predictions.groupby("model_id", sort=True):
        for band_system, band_column in band_columns.items():
            for band_label, fields in model_fields.groupby(band_column, sort=True):
                records.append(
                    {
                        "model_id": model_id,
                        "band_system": band_system,
                        "band_label": str(band_label),
                        "field_count": len(fields),
                        "mean_log_observed_to_predicted_rate": float(
                            fields["log_observed_to_predicted_rate"].mean()
                        ),
                        "mean_observed_minus_predicted_rate_per_square_deg": float(
                            (
                                fields["observed_rate_per_square_deg"]
                                - fields["predicted_rate_per_square_deg"]
                            ).mean()
                        ),
                        "mean_poisson_deviance": float(fields["field_poisson_deviance"].mean()),
                    }
                )
    return pd.DataFrame(records)


def write_frame_atomic(frame: pd.DataFrame, path: Path) -> None:
    """Write one table without leaving a partial final file."""
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary_path, index=False)
    temporary_path.replace(path)


def main() -> None:
    """Evaluate, select, and freeze one development-only large-sky model."""
    started = perf_counter()
    contract = json.loads(LARGE_SKY_MODEL_COMPARISON_CONTRACT.read_text(encoding="utf-8"))
    scale_manifest = json.loads(LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST.read_text(encoding="utf-8"))
    summary_input = pd.read_csv(LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY)
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    frame = prepare_development_frame(summary_input, grid)
    specifications = model_specifications(contract)
    outer_fold_count = int(contract["evaluation"]["outer_grouped_fold_count"])
    inner_fold_count = int(contract["evaluation"]["inner_grouped_fold_count"])

    all_predictions = []
    all_fold_results = []
    all_tuning_results = []
    for specification in specifications:
        predictions, fold_results, tuning_results = evaluate_model(
            frame,
            specification,
            settings_grid(specification, contract),
            outer_fold_count,
            inner_fold_count,
        )
        all_predictions.append(predictions)
        all_fold_results.append(fold_results)
        all_tuning_results.append(tuning_results)
    predictions = pd.concat(all_predictions, ignore_index=True)
    fold_results = pd.concat(all_fold_results, ignore_index=True)
    tuning_results = pd.concat(all_tuning_results, ignore_index=True)
    model_summary = summarize_models(specifications, predictions, fold_results)
    environment_results = environment_metrics(predictions)
    band_results = band_metrics(predictions)

    selected_model_id = str(
        model_summary.loc[model_summary["selected_primary_model"], "model_id"].iloc[0]
    )
    selected_specification = next(
        specification
        for specification in specifications
        if specification.model_id == selected_model_id
    )
    final_settings, final_tuning = tune_settings(
        frame,
        selected_specification,
        settings_grid(selected_specification, contract),
        inner_fold_count,
    )
    final_tuning_results = pd.DataFrame(
        [
            {
                "evaluation_label": "final_all_development_setting_choice",
                "model_id": selected_model_id,
                "outer_fold": 0,
                **record,
            }
            for record in final_tuning
        ]
    )
    tuning_results = pd.concat([tuning_results, final_tuning_results], ignore_index=True)
    final_estimator = build_estimator(selected_specification, final_settings)
    fit_estimator(final_estimator, selected_specification, frame)

    unflagged = frame.loc[
        frame["environment_flag_state"].eq("no_represented_environment_intersection")
    ].reset_index(drop=True)
    unflagged_predictions, unflagged_folds, unflagged_tuning = evaluate_model(
        unflagged,
        selected_specification,
        settings_grid(selected_specification, contract),
        outer_fold_count,
        inner_fold_count,
        evaluation_label="unflagged_development_sensitivity_only",
    )
    predictions = pd.concat([predictions, unflagged_predictions], ignore_index=True)
    fold_results = pd.concat([fold_results, unflagged_folds], ignore_index=True)
    tuning_results = pd.concat([tuning_results, unflagged_tuning], ignore_index=True)

    LARGE_SKY_DEVELOPMENT_MODEL_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    write_frame_atomic(model_summary, LARGE_SKY_DEVELOPMENT_MODEL_SUMMARY)
    write_frame_atomic(fold_results, LARGE_SKY_DEVELOPMENT_MODEL_FOLD_RESULTS)
    write_frame_atomic(predictions, LARGE_SKY_DEVELOPMENT_MODEL_PREDICTIONS)
    write_frame_atomic(tuning_results, LARGE_SKY_DEVELOPMENT_MODEL_TUNING_RESULTS)
    write_frame_atomic(environment_results, LARGE_SKY_DEVELOPMENT_MODEL_ENVIRONMENT_RESULTS)
    write_frame_atomic(band_results, LARGE_SKY_DEVELOPMENT_MODEL_BAND_RESULTS)
    joblib.dump(final_estimator, LARGE_SKY_DEVELOPMENT_MODEL_ARTIFACT)

    validation_field_ids = set(
        grid.loc[grid["experiment_partition"].eq("validation"), "field_id"].astype(str)
    )
    primary_predictions = predictions.loc[
        predictions["evaluation_label"].eq("primary_all_development_fields")
    ]
    primary_prediction_ids = set(primary_predictions["field_id"].astype(str))
    selected_summary = model_summary.loc[model_summary["selected_primary_model"]].iloc[0]
    selected_predictions = primary_predictions.loc[
        primary_predictions["model_id"].eq(selected_model_id)
    ]
    largest_residual = selected_predictions.loc[
        selected_predictions["field_poisson_deviance"].idxmax()
    ]
    unflagged_fold_deviances = unflagged_folds["mean_poisson_deviance"].to_numpy(dtype=float)
    checks = {
        "frozen_contract_identifier_matches": contract["contract_id"] == EXPECTED_CONTRACT_ID,
        "frozen_contract_passed_all_checks": contract["passed_count"] == contract["check_count"],
        "complete_scale_input_passed_all_checks": scale_manifest["status"]
        == "complete_development_measurement"
        and scale_manifest["passed_count"] == scale_manifest["check_count"],
        "all_398_development_fields_used_once": len(frame) == 398 and frame["field_id"].is_unique,
        "all_95_development_sky_blocks_present": frame["sky_block_id"].nunique() == 95,
        "no_validation_field_used": validation_field_ids.isdisjoint(primary_prediction_ids),
        "all_six_frozen_models_evaluated": tuple(model_summary["model_id"]) == MODEL_ORDER,
        "five_outer_folds_for_each_primary_comparison": fold_results.loc[
            fold_results["evaluation_label"].eq("primary_all_development_fields")
        ]
        .groupby("model_id")["outer_fold"]
        .nunique()
        .eq(outer_fold_count)
        .all(),
        "each_model_predicts_each_development_field_once": primary_predictions.groupby("model_id")[
            "field_id"
        ]
        .nunique()
        .eq(398)
        .all(),
        "all_outer_training_and_test_blocks_disjoint": fold_results[
            "training_and_test_sky_blocks_disjoint"
        ].all(),
        "all_model_inputs_finite": np.isfinite(
            frame.loc[:, sorted({feature for spec in specifications for feature in spec.features})]
        )
        .to_numpy()
        .all(),
        "all_fits_completed_without_convergence_warning": True,
        "selected_model_is_primary_eligible": bool(selected_summary["eligible_as_primary"]),
        "selected_model_satisfies_one_standard_error_rule": bool(
            selected_summary["inside_one_standard_error_threshold"]
        ),
        "environment_flag_model_not_selected": selected_model_id != "environment_flag_sensitivity",
        "both_environment_states_reported": environment_results["environment_flag_state"].nunique()
        == 2,
        "all_models_have_five_galactic_band_summaries": band_results.loc[
            band_results["band_system"].eq("galactic_equal_area_band")
        ]
        .groupby("model_id")["band_label"]
        .nunique()
        .eq(5)
        .all(),
        "all_models_have_six_ecliptic_band_summaries": band_results.loc[
            band_results["band_system"].eq("absolute_ecliptic_latitude_band")
        ]
        .groupby("model_id")["band_label"]
        .nunique()
        .eq(6)
        .all(),
        "unflagged_refit_is_sensitivity_only": len(unflagged_predictions) == len(unflagged)
        and set(unflagged_predictions["environment_flag_state"])
        == {"no_represented_environment_intersection"},
        "prediction_ranges_are_ordered": selected_summary["prediction_95_lower_multiplier"]
        <= selected_summary["prediction_68_lower_multiplier"]
        <= 1
        <= selected_summary["prediction_68_upper_multiplier"]
        <= selected_summary["prediction_95_upper_multiplier"],
        "validation_results_remain_unopened": contract["validation_selector_results_opened"]
        is False,
        "no_field_scientifically_approved": not grid["eligible_for_scientific_background"]
        .astype(bool)
        .any(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    inputs = [
        LARGE_SKY_MODEL_COMPARISON_CONTRACT,
        LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
        LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST,
        LARGE_SKY_FIELD_GRID,
    ]
    outputs = [
        LARGE_SKY_DEVELOPMENT_MODEL_SUMMARY,
        LARGE_SKY_DEVELOPMENT_MODEL_FOLD_RESULTS,
        LARGE_SKY_DEVELOPMENT_MODEL_PREDICTIONS,
        LARGE_SKY_DEVELOPMENT_MODEL_TUNING_RESULTS,
        LARGE_SKY_DEVELOPMENT_MODEL_ENVIRONMENT_RESULTS,
        LARGE_SKY_DEVELOPMENT_MODEL_BAND_RESULTS,
        LARGE_SKY_DEVELOPMENT_MODEL_ARTIFACT,
    ]
    report = {
        "comparison_version": COMPARISON_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "development_model_selected_and_frozen_validation_unopened",
        "contract_id": contract["contract_id"],
        "plain_language_scope": (
            "Six predeclared methods were compared using only 398 development fields. "
            "Nearby fields stayed together during testing, and validation results remain "
            "unopened."
        ),
        "field_count": len(frame),
        "sky_block_count": frame["sky_block_id"].nunique(),
        "model_count": len(specifications),
        "selected_model_id": selected_model_id,
        "selected_model_final_settings": final_settings,
        "best_eligible_model_id": str(
            model_summary.loc[model_summary["best_eligible_measured_score"], "model_id"].iloc[0]
        ),
        "one_standard_error_threshold": float(selected_summary["one_standard_error_threshold"]),
        "selected_prediction_range": {
            key: float(selected_summary[key])
            for key in (
                "prediction_68_lower_multiplier",
                "prediction_68_upper_multiplier",
                "prediction_95_lower_multiplier",
                "prediction_95_upper_multiplier",
                "empirical_68_percent_coverage",
                "empirical_95_percent_coverage",
            )
        },
        "unflagged_sensitivity_field_count": len(unflagged),
        "unflagged_sensitivity_mean_outer_fold_poisson_deviance": float(
            np.mean(unflagged_fold_deviances)
        ),
        "unflagged_sensitivity_outer_fold_poisson_deviance_standard_error": float(
            np.std(unflagged_fold_deviances, ddof=1) / math.sqrt(len(unflagged_fold_deviances))
        ),
        "largest_selected_model_out_of_fold_residual": {
            "field_id": str(largest_residual["field_id"]),
            "outer_fold": int(largest_residual["outer_fold"]),
            "environment_flag_state": str(largest_residual["environment_flag_state"]),
            "observed_rate_per_square_deg": float(largest_residual["observed_rate_per_square_deg"]),
            "predicted_rate_per_square_deg": float(
                largest_residual["predicted_rate_per_square_deg"]
            ),
            "log_observed_to_predicted_rate": float(
                largest_residual["log_observed_to_predicted_rate"]
            ),
            "field_poisson_deviance": float(largest_residual["field_poisson_deviance"]),
        },
        "validation_field_count": len(validation_field_ids),
        "validation_selector_results_opened": False,
        "scientific_background_approval": False,
        "software": {"scikit_learn_version": sklearn.__version__},
        "elapsed_seconds": perf_counter() - started,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in inputs
        ],
        "outputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in outputs
        ],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DEVELOPMENT_MODEL_MANIFEST.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Development model comparison failed: {checks}")


if __name__ == "__main__":
    main()
