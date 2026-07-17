"""Compare weak and absent logistic regularization across grouped repeats."""

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
from scripts.phase1_literature.analyze_logistic_regularization_convergence import (
    build_logistic_model,
    configuration_name,
)
from scripts.phase1_literature.analyze_point_source_ml_stability import REPEAT_SEEDS
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.compare_point_source_ml import (
    MODEL_FEATURES,
    PRIORITY_COHORTS,
    TARGET_UCD_RECALL,
    equal_cohort_weights,
    load_cohorts,
    macro_priority_retention,
    threshold_for_recall,
)

CONFIGURATIONS: list[float | None] = [1000.0, 3000.0, None]
METRICS_OUTPUT = LITERATURE_VALIDATION / "logistic_regularization_stability_metrics_v1.csv"
SUMMARY_OUTPUT = LITERATURE_VALIDATION / "logistic_regularization_stability_v1.json"
SOURCE_SUMMARY_OUTPUT = (
    LITERATURE_VALIDATION / "logistic_regularization_frozen_c1000_source_summary_v1.csv"
)


def main() -> None:
    """Run fixed grouped repeats and write comparison artifacts."""
    rows = load_cohorts(SELECTOR_DEVELOPMENT_FEATURES, SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    rows = rows.loc[rows["fit_role"].eq("model_fit")].reset_index(drop=True)
    records = []
    frozen_source_records = []
    for repeat_index, seed in enumerate(REPEAT_SEEDS, start=1):
        splits = list(
            StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed).split(
                rows, rows["target"], rows["ml_group"]
            )
        )
        for regularization_c in CONFIGURATIONS:
            name = configuration_name(regularization_c)
            scores = np.full(len(rows), np.nan)
            coefficient_vectors = []
            for train_index, test_index in splits:
                train = rows.iloc[train_index]
                model = build_logistic_model(regularization_c)
                model.fit(
                    train[MODEL_FEATURES],
                    train["target"],
                    model__sample_weight=equal_cohort_weights(train),
                )
                scores[test_index] = model.predict_proba(rows.iloc[test_index][MODEL_FEATURES])[
                    :, 1
                ]
                coefficient_vectors.append(model.named_steps["model"].coef_[0])
            positive = rows["target"].eq(1).to_numpy()
            threshold = threshold_for_recall(pd.Series(scores[positive]), TARGET_UCD_RECALL)
            selected = scores >= threshold
            coefficients = np.vstack(coefficient_vectors)
            if regularization_c == 1000.0:
                frozen_source_records.extend(
                    {
                        "repeat_index": repeat_index,
                        "repeat_seed": seed,
                        "row_id": row["row_id"],
                        "gaia_dr3_id": row["gaia_dr3_id"],
                        "ml_group": row["ml_group"],
                        "ml_cohort": row["ml_cohort"],
                        "score": score,
                        "threshold": threshold,
                        "selected": bool(selection),
                    }
                    for (_, row), score, selection in zip(
                        rows.iterrows(), scores, selected, strict=True
                    )
                )
            records.append(
                {
                    "repeat_index": repeat_index,
                    "repeat_seed": seed,
                    "configuration": name,
                    "threshold": threshold,
                    "ucd_recall": float(selected[positive].mean()),
                    "macro_priority_retention": macro_priority_retention(rows, selected),
                    **{
                        f"{cohort}_retention": float(
                            selected[rows["ml_cohort"].eq(cohort).to_numpy()].mean()
                        )
                        for cohort in PRIORITY_COHORTS
                    },
                    "maximum_coefficient_l2_norm": float(
                        np.linalg.norm(coefficients, axis=1).max()
                    ),
                }
            )

    metrics = pd.DataFrame(records)
    METRICS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(METRICS_OUTPUT, index=False)
    frozen_predictions = pd.DataFrame(frozen_source_records)
    source_summary = (
        frozen_predictions.groupby(
            ["row_id", "gaia_dr3_id", "ml_group", "ml_cohort"], as_index=False
        )
        .agg(
            mean_score=("score", "mean"),
            selection_frequency=("selected", "mean"),
        )
        .sort_values(["ml_cohort", "row_id"])
    )
    source_summary["persistent_failure_case"] = np.where(
        source_summary["ml_cohort"].eq("confirmed_ucd"),
        source_summary["selection_frequency"].eq(0.0),
        source_summary["selection_frequency"].eq(1.0),
    )
    source_summary.to_csv(SOURCE_SUMMARY_OUTPUT, index=False)
    configuration_summary = {}
    for configuration, group in metrics.groupby("configuration", sort=False):
        configuration_summary[configuration] = {
            "ucd_recall": {
                "minimum": float(group["ucd_recall"].min()),
                "median": float(group["ucd_recall"].median()),
                "maximum": float(group["ucd_recall"].max()),
            },
            "macro_priority_retention": {
                "minimum": float(group["macro_priority_retention"].min()),
                "median": float(group["macro_priority_retention"].median()),
                "maximum": float(group["macro_priority_retention"].max()),
            },
            "maximum_coefficient_l2_norm": float(group["maximum_coefficient_l2_norm"].max()),
        }
    paired_winners = []
    for repeat_index, group in metrics.groupby("repeat_index"):
        ordered = group.sort_values(["macro_priority_retention", "configuration"])
        paired_winners.append(
            {
                "repeat_index": int(repeat_index),
                "lowest_retention_configuration": str(ordered.iloc[0]["configuration"]),
                "lowest_retention": float(ordered.iloc[0]["macro_priority_retention"]),
            }
        )
    summary = {
        "analysis_version": "logistic_regularization_stability_v1",
        "validation_partition_inspected": False,
        "repeat_seeds": REPEAT_SEEDS,
        "grouped_folds_per_repeat": 5,
        "target_ucd_recall": TARGET_UCD_RECALL,
        "configurations": [configuration_name(value) for value in CONFIGURATIONS],
        "configuration_summary": configuration_summary,
        "paired_repeat_winners": paired_winners,
        "inputs": {
            "development_sha256": calculate_sha256(SELECTOR_DEVELOPMENT_FEATURES),
            "stars_sha256": calculate_sha256(SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES),
        },
        "metrics_sha256": calculate_sha256(METRICS_OUTPUT),
        "frozen_c1000_source_summary_sha256": calculate_sha256(SOURCE_SUMMARY_OUTPUT),
        "frozen_c1000_persistent_failure_counts": {
            str(cohort): int(count)
            for cohort, count in source_summary.loc[source_summary["persistent_failure_case"]][
                "ml_cohort"
            ]
            .value_counts()
            .sort_index()
            .items()
        },
        "decision_status": "development_regularization_policy_comparison_no_threshold_frozen",
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
