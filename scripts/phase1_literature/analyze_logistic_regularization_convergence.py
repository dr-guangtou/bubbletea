"""Compare weakly regularized and unregularized logistic selector fits.

The analysis uses only benchmark-v3 development rows. It measures full-development
coefficient and prediction convergence to the unregularized fit and fixed grouped
out-of-fold behavior without selecting or freezing a threshold.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_VALIDATION,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.compare_point_source_ml import (
    MODEL_FEATURES,
    PRIORITY_COHORTS,
    RANDOM_SEED,
    TARGET_UCD_RECALL,
    build_model,
    equal_cohort_weights,
    load_cohorts,
    macro_priority_retention,
    threshold_for_recall,
)

REGULARIZATION_VALUES = [100.0, 300.0, 1000.0, 3000.0]
COEFFICIENT_OUTPUT = (
    LITERATURE_VALIDATION / "logistic_regularization_convergence_coefficients_v1.csv"
)
SUMMARY_OUTPUT = LITERATURE_VALIDATION / "logistic_regularization_convergence_v1.json"


def build_logistic_model(regularization_c: float | None):
    """Build the shared pipeline with finite or absent L2 regularization."""
    effective_c = np.inf if regularization_c is None else regularization_c
    return build_model("logistic_regression", {"regularization_c": effective_c})


def configuration_name(regularization_c: float | None) -> str:
    """Return a stable configuration label."""
    return "unregularized" if regularization_c is None else f"c_{regularization_c:g}"


def main() -> None:
    """Measure convergence and write deterministic development artifacts."""
    rows = load_cohorts(SELECTOR_DEVELOPMENT_FEATURES, SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    rows = rows.loc[rows["fit_role"].eq("model_fit")].reset_index(drop=True)
    configurations: list[float | None] = [*REGULARIZATION_VALUES, None]
    full_scores: dict[str, np.ndarray] = {}
    coefficient_rows = []
    for regularization_c in configurations:
        name = configuration_name(regularization_c)
        model = build_logistic_model(regularization_c)
        model.fit(
            rows[MODEL_FEATURES],
            rows["target"],
            model__sample_weight=equal_cohort_weights(rows),
        )
        full_scores[name] = model.predict_proba(rows[MODEL_FEATURES])[:, 1]
        transformed_names = model.named_steps["preprocessing"].get_feature_names_out()
        coefficients = model.named_steps["model"].coef_[0]
        coefficient_rows.extend(
            {
                "configuration": name,
                "regularization_c": regularization_c,
                "transformed_feature": feature,
                "coefficient": coefficient,
            }
            for feature, coefficient in zip(transformed_names, coefficients, strict=True)
        )

    unregularized_scores = full_scores["unregularized"]
    coefficients = pd.DataFrame(coefficient_rows)
    unregularized_coefficients = coefficients.loc[
        coefficients["configuration"].eq("unregularized")
    ].set_index("transformed_feature")["coefficient"]
    convergence = []
    for regularization_c in REGULARIZATION_VALUES:
        name = configuration_name(regularization_c)
        current_coefficients = coefficients.loc[coefficients["configuration"].eq(name)].set_index(
            "transformed_feature"
        )["coefficient"]
        coefficient_difference = current_coefficients - unregularized_coefficients
        score_difference = full_scores[name] - unregularized_scores
        convergence.append(
            {
                "configuration": name,
                "maximum_absolute_coefficient_difference": float(
                    coefficient_difference.abs().max()
                ),
                "coefficient_vector_relative_l2_difference": float(
                    np.linalg.norm(coefficient_difference)
                    / np.linalg.norm(unregularized_coefficients)
                ),
                "maximum_absolute_probability_difference": float(np.abs(score_difference).max()),
                "mean_absolute_probability_difference": float(np.abs(score_difference).mean()),
                "probability_correlation": float(
                    np.corrcoef(full_scores[name], unregularized_scores)[0, 1]
                ),
            }
        )

    grouped_metrics = []
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    for regularization_c in configurations:
        name = configuration_name(regularization_c)
        oof_scores = np.full(len(rows), np.nan)
        for train_index, test_index in splitter.split(rows, rows["target"], rows["ml_group"]):
            train = rows.iloc[train_index]
            model = build_logistic_model(regularization_c)
            model.fit(
                train[MODEL_FEATURES],
                train["target"],
                model__sample_weight=equal_cohort_weights(train),
            )
            oof_scores[test_index] = model.predict_proba(rows.iloc[test_index][MODEL_FEATURES])[
                :, 1
            ]
        positive = rows["target"].eq(1).to_numpy()
        threshold = threshold_for_recall(pd.Series(oof_scores[positive]), TARGET_UCD_RECALL)
        selected = oof_scores >= threshold
        grouped_metrics.append(
            {
                "configuration": name,
                "threshold": threshold,
                "ucd_recall": float(selected[positive].mean()),
                "macro_priority_retention": macro_priority_retention(rows, selected),
                "priority_retention": {
                    cohort: float(selected[rows["ml_cohort"].eq(cohort).to_numpy()].mean())
                    for cohort in PRIORITY_COHORTS
                },
            }
        )

    COEFFICIENT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    coefficients.to_csv(COEFFICIENT_OUTPUT, index=False)
    summary = {
        "analysis_version": "logistic_regularization_convergence_v1",
        "validation_partition_inspected": False,
        "configurations": [configuration_name(value) for value in configurations],
        "target_ucd_recall": TARGET_UCD_RECALL,
        "fit_row_count": len(rows),
        "model_features": MODEL_FEATURES,
        "convergence_to_unregularized": convergence,
        "fixed_grouped_oof_metrics": grouped_metrics,
        "inputs": {
            "development_sha256": calculate_sha256(SELECTOR_DEVELOPMENT_FEATURES),
            "stars_sha256": calculate_sha256(SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES),
        },
        "coefficients_sha256": calculate_sha256(COEFFICIENT_OUTPUT),
        "decision_status": "development_convergence_measurement_no_model_or_threshold_frozen",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
