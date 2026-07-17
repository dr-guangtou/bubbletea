"""Validate the development-only nested-CV point-source ML comparison."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    POINT_SOURCE_ML_COMPARISON,
    POINT_SOURCE_ML_FOLDS,
    POINT_SOURCE_ML_PREDICTIONS,
    POINT_SOURCE_ML_VALIDATION,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
    VALIDATION_BENCHMARK,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.compare_point_source_ml import (
    COMPARISON_VERSION,
    EXCLUDED_PRIMARY_FEATURES,
    MODEL_FEATURES,
    OUTER_FOLDS,
    PRIORITY_COHORTS,
    load_cohorts,
)

MODEL_FAMILIES = [
    "logistic_regression",
    "histogram_gradient_boosting",
    "hand_rank_score",
]


def serialize_numpy_scalar(value: object) -> int | float | bool | str:
    """Convert NumPy scalar diagnostics for JSON serialization."""
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def parse_arguments() -> argparse.Namespace:
    """Parse comparison inputs and validation output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--development", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES)
    parser.add_argument("--stars", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    parser.add_argument("--predictions", type=Path, default=POINT_SOURCE_ML_PREDICTIONS)
    parser.add_argument("--fold-metrics", type=Path, default=POINT_SOURCE_ML_FOLDS)
    parser.add_argument("--comparison", type=Path, default=POINT_SOURCE_ML_COMPARISON)
    parser.add_argument("--output", type=Path, default=POINT_SOURCE_ML_VALIDATION)
    return parser.parse_args()


def main() -> None:
    """Run partition, fold, feature, metric, hash, and decision checks."""
    arguments = parse_arguments()
    benchmark = pd.read_csv(arguments.benchmark, dtype={"gaia_dr3_id": str})
    predictions = pd.read_csv(arguments.predictions, dtype={"gaia_dr3_id": str})
    folds = pd.read_csv(arguments.fold_metrics)
    summary = json.loads(arguments.comparison.read_text(encoding="utf-8"))
    source_rows = load_cohorts(arguments.development, arguments.stars)
    fit_rows = source_rows.loc[source_rows["fit_role"].eq("model_fit")]
    stress_rows = source_rows.loc[source_rows["fit_role"].eq("secondary_stress")]
    validation_ids = set(benchmark.loc[benchmark["partition"].eq("validation"), "gaia_dr3_id"])
    checks = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    oof = predictions.loc[predictions["prediction_role"].isin(["nested_outer_oof", "outer_oof"])]
    stress = predictions.loc[
        predictions["prediction_role"].eq("secondary_stress_mean_outer_models")
    ]
    family_counts = oof.groupby("model_family").size().to_dict()
    stress_counts = stress.groupby("model_family").size().to_dict()
    recomputed = {}
    for family in MODEL_FAMILIES:
        family_rows = oof.loc[oof["model_family"].eq(family)]
        cohort_retention = {
            cohort: float(family_rows.loc[family_rows["ml_cohort"].eq(cohort), "selected"].mean())
            for cohort in PRIORITY_COHORTS
        }
        recomputed[family] = {
            "ucd_recall": float(
                family_rows.loc[family_rows["ml_cohort"].eq("confirmed_ucd"), "selected"].mean()
            ),
            "macro_retention": float(np.mean(list(cohort_retention.values()))),
        }

    check(
        "comparison_version",
        summary["comparison_version"] == COMPARISON_VERSION,
        summary["comparison_version"],
    )
    check(
        "validation_partition_blind",
        summary["validation_partition_inspected"] is False,
        summary["validation_partition_inspected"],
    )
    check(
        "no_validation_identifiers",
        set(predictions["gaia_dr3_id"]).isdisjoint(validation_ids),
        len(set(predictions["gaia_dr3_id"]).intersection(validation_ids)),
    )
    check(
        "model_families",
        sorted(predictions["model_family"].unique()) == sorted(MODEL_FAMILIES),
        sorted(predictions["model_family"].unique()),
    )
    check(
        "one_oof_prediction_per_fit_row",
        family_counts == {family: len(fit_rows) for family in MODEL_FAMILIES},
        family_counts,
    )
    check(
        "one_stress_prediction_per_stress_row",
        stress_counts == {family: len(stress_rows) for family in MODEL_FAMILIES},
        stress_counts,
    )
    check(
        "outer_fold_count",
        set(oof["outer_fold"]) == set(range(1, OUTER_FOLDS + 1)),
        sorted(oof["outer_fold"].unique()),
    )
    check(
        "groups_do_not_cross_outer_folds",
        int(oof.groupby(["model_family", "ml_group"])["outer_fold"].nunique().max()) == 1,
        int(oof.groupby(["model_family", "ml_group"])["outer_fold"].nunique().max()),
    )
    check(
        "stars_share_matched_ucd_fold",
        int(
            oof.loc[oof["ml_cohort"].isin(["confirmed_ucd", "spectroscopic_star"])]
            .groupby(["model_family", "ml_group"])["outer_fold"]
            .nunique()
            .max()
        )
        == 1,
        "maximum fold count per matched group",
    )
    check("fold_metrics_complete", len(folds) == len(MODEL_FAMILIES) * OUTER_FOLDS, len(folds))
    check(
        "priority_cohorts",
        summary["priority_cohorts"] == PRIORITY_COHORTS,
        summary["priority_cohorts"],
    )
    check("color_is_soft_feature", "bp_rp" in summary["model_features"], summary["model_features"])
    check(
        "model_features_exact",
        summary["model_features"] == MODEL_FEATURES,
        summary["model_features"],
    )
    check(
        "tautological_features_excluded",
        set(summary["model_features"]).isdisjoint(EXCLUDED_PRIMARY_FEATURES),
        sorted(set(summary["model_features"]).intersection(EXCLUDED_PRIMARY_FEATURES)),
    )
    check(
        "development_hash",
        summary["inputs"]["development_sha256"] == calculate_sha256(arguments.development),
        summary["inputs"]["development_sha256"],
    )
    check(
        "stars_hash",
        summary["inputs"]["stars_sha256"] == calculate_sha256(arguments.stars),
        summary["inputs"]["stars_sha256"],
    )
    check(
        "predictions_hash",
        summary["predictions_sha256"] == calculate_sha256(arguments.predictions),
        summary["predictions_sha256"],
    )
    check(
        "fold_metrics_hash",
        summary["fold_metrics_sha256"] == calculate_sha256(arguments.fold_metrics),
        summary["fold_metrics_sha256"],
    )
    check(
        "reported_metrics_reproduced",
        all(
            np.isclose(
                summary["comparison"][family]["nested_oof_ucd_recall"],
                recomputed[family]["ucd_recall"],
            )
            and np.isclose(
                summary["comparison"][family]["nested_oof_macro_priority_retention"],
                recomputed[family]["macro_retention"],
            )
            for family in MODEL_FAMILIES
        ),
        recomputed,
    )
    check(
        "selector_not_frozen",
        summary["decision_status"] == "development_comparison_only_no_model_or_threshold_frozen",
        summary["decision_status"],
    )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "comparison_version": COMPARISON_VERSION,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "checks": checks,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, default=serialize_numpy_scalar) + "\n",
        encoding="utf-8",
    )
    if failed:
        raise RuntimeError(
            "Point-source ML comparison validation failed: "
            + ", ".join(item["name"] for item in failed)
        )


if __name__ == "__main__":
    main()
