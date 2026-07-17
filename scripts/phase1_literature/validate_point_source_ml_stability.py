"""Validate repeated nested-CV point-source logistic stability artifacts."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    POINT_SOURCE_ML_STABILITY_COEFFICIENT_SUMMARY,
    POINT_SOURCE_ML_STABILITY_COEFFICIENTS,
    POINT_SOURCE_ML_STABILITY_FOLDS,
    POINT_SOURCE_ML_STABILITY_PREDICTIONS,
    POINT_SOURCE_ML_STABILITY_SOURCE_SUMMARY,
    POINT_SOURCE_ML_STABILITY_STRATA,
    POINT_SOURCE_ML_STABILITY_SUMMARY,
    POINT_SOURCE_ML_STABILITY_VALIDATION,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
    VALIDATION_BENCHMARK,
)
from scripts.phase1_literature.analyze_point_source_ml_stability import (
    MINIMUM_COEFFICIENT_SIGN_AGREEMENT,
    MINIMUM_MEDIAN_RECALL,
    MINIMUM_REPEAT_RECALL,
    REPEAT_COUNT,
    REPEAT_SEEDS,
    STABILITY_VERSION,
    summarize_coefficients,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.compare_point_source_ml import (
    LOGISTIC_PARAMETERS,
    MODEL_FEATURES,
    OUTER_FOLDS,
    PRIORITY_COHORTS,
    load_cohorts,
)


def parse_arguments() -> argparse.Namespace:
    """Parse stability inputs and validation output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--development", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES)
    parser.add_argument("--stars", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    parser.add_argument("--predictions", type=Path, default=POINT_SOURCE_ML_STABILITY_PREDICTIONS)
    parser.add_argument(
        "--source-summary", type=Path, default=POINT_SOURCE_ML_STABILITY_SOURCE_SUMMARY
    )
    parser.add_argument("--fold-metrics", type=Path, default=POINT_SOURCE_ML_STABILITY_FOLDS)
    parser.add_argument("--coefficients", type=Path, default=POINT_SOURCE_ML_STABILITY_COEFFICIENTS)
    parser.add_argument(
        "--coefficient-summary",
        type=Path,
        default=POINT_SOURCE_ML_STABILITY_COEFFICIENT_SUMMARY,
    )
    parser.add_argument("--strata", type=Path, default=POINT_SOURCE_ML_STABILITY_STRATA)
    parser.add_argument("--summary", type=Path, default=POINT_SOURCE_ML_STABILITY_SUMMARY)
    parser.add_argument("--output", type=Path, default=POINT_SOURCE_ML_STABILITY_VALIDATION)
    return parser.parse_args()


def serialize_numpy_scalar(value: object) -> int | float | bool | str:
    """Convert NumPy scalar diagnostics for JSON serialization."""
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def main() -> None:
    """Run partition, repeat, fold, coefficient, metric, and hash checks."""
    arguments = parse_arguments()
    benchmark = pd.read_csv(arguments.benchmark, dtype={"gaia_dr3_id": str})
    predictions = pd.read_csv(arguments.predictions, dtype={"gaia_dr3_id": str})
    source_summary = pd.read_csv(arguments.source_summary, dtype={"gaia_dr3_id": str})
    folds = pd.read_csv(arguments.fold_metrics)
    coefficient_fits = pd.read_csv(arguments.coefficients)
    coefficient_summary = pd.read_csv(arguments.coefficient_summary)
    strata = pd.read_csv(arguments.strata)
    summary = json.loads(arguments.summary.read_text(encoding="utf-8"))
    expected_rows = load_cohorts(arguments.development, arguments.stars)
    expected_fit_rows = expected_rows.loc[expected_rows["fit_role"].eq("model_fit")]
    validation_ids = set(benchmark.loc[benchmark["partition"].eq("validation"), "gaia_dr3_id"])
    checks = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    repeat_counts = predictions.groupby("row_id")["repeat_index"].nunique()
    repeat_row_counts = predictions.groupby(["repeat_index", "row_id"]).size()
    group_fold_counts = predictions.groupby(["repeat_index", "ml_group"])["outer_fold"].nunique()
    expected_c_values = {float(item["regularization_c"]) for item in LOGISTIC_PARAMETERS}
    recomputed_coefficient_summary = summarize_coefficients(coefficient_fits)
    coefficient_comparison = coefficient_summary.merge(
        recomputed_coefficient_summary,
        on=["coefficient_feature", "is_missing_indicator", "fit_count", "median_sign"],
        suffixes=("_reported", "_recomputed"),
        validate="one_to_one",
    )
    coefficient_numeric_match = all(
        np.allclose(
            coefficient_comparison[f"{column}_reported"],
            coefficient_comparison[f"{column}_recomputed"],
        )
        for column in [
            "coefficient_minimum",
            "coefficient_median",
            "coefficient_maximum",
            "sign_agreement_fraction",
        ]
    )

    repeat_metrics = []
    for repeat_index, group in predictions.groupby("repeat_index", sort=True):
        cohort_retention = {
            cohort: float(group.loc[group["ml_cohort"].eq(cohort), "selected"].mean())
            for cohort in PRIORITY_COHORTS
        }
        repeat_metrics.append(
            {
                "repeat_index": int(repeat_index),
                "ucd_recall": float(
                    group.loc[group["ml_cohort"].eq("confirmed_ucd"), "selected"].mean()
                ),
                "macro_priority_retention": float(np.mean(list(cohort_retention.values()))),
            }
        )
    repeat_frame = pd.DataFrame(repeat_metrics)
    measurement_coefficients = coefficient_summary.loc[
        coefficient_summary["coefficient_feature"].isin(MODEL_FEATURES)
    ]
    readiness = {
        "median_ucd_recall_at_least_0p90": bool(
            repeat_frame["ucd_recall"].median() >= MINIMUM_MEDIAN_RECALL
        ),
        "minimum_repeat_ucd_recall_at_least_0p85": bool(
            repeat_frame["ucd_recall"].min() >= MINIMUM_REPEAT_RECALL
        ),
        "all_measurement_coefficient_sign_agreement_at_least_0p80": bool(
            measurement_coefficients["sign_agreement_fraction"]
            .ge(MINIMUM_COEFFICIENT_SIGN_AGREEMENT)
            .all()
        ),
    }
    reported_repeat_frame = pd.DataFrame(summary["repeat_metrics"])
    metric_merge = reported_repeat_frame.merge(
        repeat_frame,
        on="repeat_index",
        suffixes=("_reported", "_recomputed"),
        validate="one_to_one",
    )
    repeat_metrics_match = all(
        np.allclose(
            metric_merge[f"{column}_reported"],
            metric_merge[f"{column}_recomputed"],
        )
        for column in ["ucd_recall", "macro_priority_retention"]
    )
    source_recomputed = (
        predictions.groupby("row_id", as_index=False)
        .agg(
            selection_frequency=("selected", "mean"),
            prediction_count=("repeat_index", "size"),
        )
        .merge(
            source_summary[["row_id", "selection_frequency"]],
            on="row_id",
            suffixes=("_recomputed", "_reported"),
            validate="one_to_one",
        )
    )

    check(
        "stability_version",
        summary["stability_version"] == STABILITY_VERSION,
        summary["stability_version"],
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
    check("declared_repeat_count", summary["repeat_count"] == REPEAT_COUNT, summary["repeat_count"])
    check("declared_repeat_seeds", summary["repeat_seeds"] == REPEAT_SEEDS, summary["repeat_seeds"])
    check(
        "prediction_row_count",
        len(predictions) == len(expected_fit_rows) * REPEAT_COUNT,
        len(predictions),
    )
    check(
        "each_source_has_every_repeat",
        repeat_counts.eq(REPEAT_COUNT).all(),
        repeat_counts.value_counts().to_dict(),
    )
    check(
        "one_prediction_per_source_repeat",
        repeat_row_counts.eq(1).all(),
        int(repeat_row_counts.max()),
    )
    check(
        "groups_do_not_cross_outer_folds",
        group_fold_counts.eq(1).all(),
        int(group_fold_counts.max()),
    )
    check("fold_metrics_complete", len(folds) == REPEAT_COUNT * OUTER_FOLDS, len(folds))
    check(
        "regularization_grid_respected",
        set(folds["regularization_c"]).issubset(expected_c_values),
        sorted(folds["regularization_c"].unique()),
    )
    check(
        "scores_finite",
        np.isfinite(predictions["score"]).all(),
        int((~np.isfinite(predictions["score"])).sum()),
    )
    check(
        "source_summary_complete",
        len(source_summary) == len(expected_fit_rows),
        len(source_summary),
    )
    check(
        "source_selection_frequency_reproduced",
        np.allclose(
            source_recomputed["selection_frequency_reported"],
            source_recomputed["selection_frequency_recomputed"],
        ),
        float(
            np.max(
                np.abs(
                    source_recomputed["selection_frequency_reported"]
                    - source_recomputed["selection_frequency_recomputed"]
                )
            )
        ),
    )
    check(
        "coefficient_fit_count",
        coefficient_fits.groupby("coefficient_feature").size().eq(REPEAT_COUNT * OUTER_FOLDS).all(),
        coefficient_fits.groupby("coefficient_feature").size().to_dict(),
    )
    check(
        "measurement_coefficients_present",
        set(MODEL_FEATURES).issubset(set(coefficient_fits["coefficient_feature"])),
        sorted(set(MODEL_FEATURES) - set(coefficient_fits["coefficient_feature"])),
    )
    check(
        "coefficient_summary_reproduced",
        coefficient_numeric_match and len(coefficient_comparison) == len(coefficient_summary),
        len(coefficient_comparison),
    )
    check("repeat_metrics_reproduced", repeat_metrics_match, repeat_metrics)
    check("readiness_criteria_reproduced", summary["readiness_criteria"] == readiness, readiness)
    check(
        "readiness_status_consistent",
        summary["ready_for_selector_freeze_review"] == all(readiness.values()),
        summary["ready_for_selector_freeze_review"],
    )
    check(
        "strata_prediction_counts",
        strata.groupby("dimension")["prediction_count"].sum().eq(len(predictions)).all(),
        strata.groupby("dimension")["prediction_count"].sum().to_dict(),
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
    artifact_paths = {
        "predictions_sha256": arguments.predictions,
        "source_summary_sha256": arguments.source_summary,
        "fold_metrics_sha256": arguments.fold_metrics,
        "coefficients_sha256": arguments.coefficients,
        "coefficient_summary_sha256": arguments.coefficient_summary,
        "strata_sha256": arguments.strata,
    }
    check(
        "artifact_hashes",
        all(
            summary["artifacts"][name] == calculate_sha256(path)
            for name, path in artifact_paths.items()
        ),
        {name: calculate_sha256(path) for name, path in artifact_paths.items()},
    )
    check(
        "validation_still_sealed",
        summary["decision_status"].endswith("validation_still_sealed"),
        summary["decision_status"],
    )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "stability_version": STABILITY_VERSION,
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
            "Point-source ML stability validation failed: "
            + ", ".join(item["name"] for item in failed)
        )


if __name__ == "__main__":
    main()
