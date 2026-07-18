"""Freeze large-sky background model comparisons before development scale-up."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS,
    LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS_MANIFEST,
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST,
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_FIELD_GRID_MANIFEST,
    LARGE_SKY_MODEL_COMPARISON_CONTRACT,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256

CONTRACT_VERSION = "large_sky_model_comparison_contract_v1"


def stable_contract_identifier(contract: dict[str, object]) -> str:
    """Return a stable identifier for the scientific comparison contract."""
    encoded = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    return f"model_contract_{hashlib.sha256(encoded).hexdigest()[:20]}"


def main() -> None:
    """Write the unfitted candidate-model and grouped-evaluation contract."""
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    pilot = pd.read_csv(LARGE_SKY_DEVELOPMENT_PILOT_FIELDS)
    conditions = pd.read_csv(LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS)
    condition_manifest = json.loads(
        LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS_MANIFEST.read_text(encoding="utf-8")
    )
    retrieval = pd.read_csv(LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY)
    retrieval_manifest = json.loads(
        LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST.read_text(encoding="utf-8")
    )
    development = grid.loc[grid["experiment_partition"].eq("development")]
    validation = grid.loc[grid["experiment_partition"].eq("validation")]

    pilot_diagnostics = conditions.merge(
        retrieval[["field_id", "selected_source_density_per_square_deg"]],
        on="field_id",
        validate="one_to_one",
    ).assign(
        absolute_galactic_latitude_deg=lambda frame: frame["galactic_latitude_deg"].abs(),
        absolute_ecliptic_latitude_deg=lambda frame: frame["ecliptic_latitude_deg"].abs(),
    )
    measured_predictors = [
        "absolute_galactic_latitude_deg",
        "absolute_ecliptic_latitude_deg",
        "source_density_per_square_deg",
        "mean_visibility_periods_used",
        "mean_astrometric_matched_transits",
        "m10_median_g_magnitude",
    ]
    descriptive_correlations = {
        predictor: float(
            pilot_diagnostics[["selected_source_density_per_square_deg", predictor]]
            .corr(method="spearman")
            .iloc[0, 1]
        )
        for predictor in measured_predictors
    }
    response_contract = {
        "count_column": "selected_source_count",
        "rate_column": "selected_source_count / usable_area_square_deg",
        "statistical_weight_column": "usable_area_square_deg",
        "selector_version": retrieval_manifest["selector_version"],
        "incomplete_field_treatment": "preserve_failure_and_exclude_from_fit_never_zero",
    }
    shared_position_features = [
        "absolute_galactic_latitude_deg",
        "galactic_hemisphere",
        "sine_galactic_longitude",
        "cosine_galactic_longitude",
        "absolute_ecliptic_latitude_deg",
    ]
    gaia_condition_features = [
        "log1p_total_gaia_source_density_per_square_deg",
        "m10_median_g_magnitude",
        "mean_visibility_periods_used",
        "mean_astrometric_matched_transits",
        "median_phot_g_mean_mag",
        "phot_g_mean_mag_10th_percentile",
        "phot_g_mean_mag_90th_percentile",
    ]
    candidate_models = [
        {
            "model_id": "constant_rate_baseline",
            "plain_language_question": "Does one average rate predict unseen sky blocks?",
            "model_family": "weighted_constant_poisson_rate",
            "features": [],
            "eligible_as_primary": True,
        },
        {
            "model_id": "galactic_latitude_spline",
            "plain_language_question": (
                "How much prediction improves when the Milky Way latitude trend is allowed "
                "to curve smoothly?"
            ),
            "model_family": "regularized_poisson_regression",
            "features": ["absolute_galactic_latitude_deg"],
            "eligible_as_primary": True,
        },
        {
            "model_id": "sky_position_spline",
            "plain_language_question": (
                "Do hemisphere, longitude, and ecliptic latitude improve on Galactic "
                "latitude alone?"
            ),
            "model_family": "regularized_poisson_regression",
            "features": shared_position_features,
            "eligible_as_primary": True,
        },
        {
            "model_id": "sky_position_and_gaia_conditions",
            "plain_language_question": (
                "Do measured Gaia depth, observation frequency, crowding, and magnitude "
                "distribution improve prediction on unseen sky blocks?"
            ),
            "model_family": "regularized_poisson_regression",
            "features": shared_position_features + gaia_condition_features,
            "eligible_as_primary": True,
        },
        {
            "model_id": "nonlinear_sky_and_gaia_benchmark",
            "plain_language_question": (
                "Does a limited nonlinear tree model materially improve unseen-block "
                "prediction over the interpretable regression?"
            ),
            "model_family": "histogram_gradient_boosting_poisson_loss",
            "features": shared_position_features + gaia_condition_features,
            "eligible_as_primary": True,
        },
        {
            "model_id": "environment_flag_sensitivity",
            "plain_language_question": (
                "Does adding the count-blind environment flag change development "
                "predictions or residuals?"
            ),
            "model_family": "regularized_poisson_regression",
            "features": shared_position_features
            + gaia_condition_features
            + ["one_or_more_count_blind_environment_flags"],
            "eligible_as_primary": False,
            "reason_not_primary": (
                "The flag uses provisional catalog circles and cannot approve or delete a "
                "scientific background field."
            ),
        },
    ]
    evaluation_contract = {
        "group_column": "sky_block_id",
        "outer_grouped_fold_count": 5,
        "outer_fold_purpose": (
            "Measure prediction on development sky blocks not used to fit that fold."
        ),
        "inner_grouped_fold_count": 4,
        "inner_fold_purpose": (
            "Choose only the declared regularization, spline, or tree settings inside each "
            "outer training set."
        ),
        "primary_metric": "mean_poisson_deviance_lower_is_better",
        "secondary_metrics": [
            "median_absolute_log_density_error",
            "root_mean_square_log_density_error",
            "mean_residual_by_galactic_latitude_band",
            "mean_residual_by_ecliptic_latitude_band",
            "empirical_68_and_95_percent_prediction_range_coverage",
        ],
        "selection_rule": (
            "Choose the simplest model whose outer-fold mean Poisson deviance is within one "
            "standard error of the lowest measured value."
        ),
        "prediction_range_rule": (
            "Use grouped out-of-fold log observed-to-predicted residual quantiles to form "
            "68 and 95 percent multiplicative ranges, then freeze them before validation."
        ),
        "validation_use": (
            "One final evaluation on all 102 held-back fields after preprocessing, model, "
            "settings, and prediction ranges are frozen."
        ),
    }
    tuning_contract = {
        "poisson_regression_alpha_values": [0.0, 0.001, 0.01, 0.1, 1.0, 10.0],
        "spline_knot_counts": [3, 4, 5, 6],
        "nonlinear_maximum_leaf_nodes": [7, 15, 31],
        "nonlinear_learning_rates": [0.03, 0.1],
        "nonlinear_minimum_samples_per_leaf": [10, 20, 40],
        "preprocessing_fit_scope": "inside_each_training_fold_only",
    }
    sensitivity_contract = {
        "report_metrics_separately_for_environment_flag_states": True,
        "refit_on_unflagged_development_fields": "sensitivity_only",
        "add_environment_flag_predictor": "sensitivity_only",
        "field_deletion_or_scientific_approval": False,
        "total_source_density_limit": (
            "It is allowed in the large-sky diagnostic but cannot become a rigid target-to-"
            "control matching cut because a target field can contain real host sources."
        ),
    }
    contract_core = {
        "contract_version": CONTRACT_VERSION,
        "response": response_contract,
        "candidate_models": candidate_models,
        "evaluation": evaluation_contract,
        "tuning": tuning_contract,
        "sensitivity": sensitivity_contract,
    }
    contract_id = stable_contract_identifier(contract_core)
    validation_field_ids = set(validation["field_id"].astype(str))
    pilot_field_ids = set(pilot["field_id"].astype(str))
    checks = {
        "three_hundred_ninety_eight_development_fields": len(development) == 398,
        "one_hundred_two_validation_fields_remain_held_back": len(validation) == 102,
        "ninety_five_development_sky_blocks": development["sky_block_id"].nunique() == 95,
        "twenty_five_validation_sky_blocks": validation["sky_block_id"].nunique() == 25,
        "pilot_contains_development_only": validation_field_ids.isdisjoint(pilot_field_ids),
        "condition_and_retrieval_pilot_fields_match": set(conditions["field_id"].astype(str))
        == set(retrieval["field_id"].astype(str))
        == pilot_field_ids,
        "input_measurements_passed_all_checks": condition_manifest["passed_count"]
        == condition_manifest["check_count"]
        and retrieval_manifest["passed_count"] == retrieval_manifest["check_count"],
        "constant_and_increasing_complexity_models_declared": len(candidate_models) == 6
        and candidate_models[0]["model_id"] == "constant_rate_baseline",
        "environment_model_is_sensitivity_only": not candidate_models[-1]["eligible_as_primary"],
        "grouped_nested_development_evaluation_declared": evaluation_contract[
            "outer_grouped_fold_count"
        ]
        == 5
        and evaluation_contract["inner_grouped_fold_count"] == 4,
        "validation_not_used_for_pilot_diagnostics": validation_field_ids.isdisjoint(
            set(pilot_diagnostics["field_id"].astype(str))
        ),
        "no_model_fitted_by_contract_freeze": True,
        "no_field_scientifically_approved": not grid["eligible_for_scientific_background"]
        .astype(bool)
        .any(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    report = {
        "contract_version": CONTRACT_VERSION,
        "contract_id": contract_id,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "candidate_models_and_evaluation_frozen_no_model_fitted",
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                LARGE_SKY_FIELD_GRID,
                LARGE_SKY_FIELD_GRID_MANIFEST,
                LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
                LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS,
                LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS_MANIFEST,
                LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY,
                LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST,
            )
        ],
        **contract_core,
        "predictor_readiness": {
            "measured_in_twelve_field_pilot": measured_predictors,
            "derived_from_existing_raw_gaia_checkpoints_before_full_fit": [
                "median_phot_g_mean_mag",
                "phot_g_mean_mag_10th_percentile",
                "phot_g_mean_mag_90th_percentile",
            ],
        },
        "pilot_descriptive_only": {
            "field_count": len(pilot_diagnostics),
            "spearman_correlations_with_selected_source_density": (descriptive_correlations),
            "interpretation_limit": (
                "These twelve coverage-oriented fields confirm predictor range only; their "
                "correlations do not choose a model or predictor."
            ),
        },
        "development_field_count": len(development),
        "held_back_validation_field_count": len(validation),
        "held_back_validation_field_ids_sha256": hashlib.sha256(
            "\n".join(sorted(validation_field_ids)).encode()
        ).hexdigest(),
        "validation_selector_results_opened": False,
        "scientific_background_approval": False,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_MODEL_COMPARISON_CONTRACT.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Large-sky model comparison freeze failed: {checks}")


if __name__ == "__main__":
    main()
