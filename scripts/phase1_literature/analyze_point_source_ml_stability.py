"""Measure repeated nested-CV stability of the provisional logistic selector."""

import argparse
import json
import sys
from pathlib import Path

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from sklearn.model_selection import StratifiedGroupKFold

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
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.compare_point_source_ml import (
    INNER_FOLDS,
    LOGISTIC_PARAMETERS,
    MODEL_FEATURES,
    OUTER_FOLDS,
    PRIORITY_COHORTS,
    RANDOM_SEED,
    TARGET_UCD_RECALL,
    build_model,
    choose_parameters,
    equal_cohort_weights,
    load_cohorts,
    macro_priority_retention,
)

STABILITY_VERSION = "point_source_ml_stability_v3"
REPEAT_COUNT = 10
REPEAT_SEED_STEP = 1009
REPEAT_SEEDS = [RANDOM_SEED + REPEAT_SEED_STEP * index for index in range(REPEAT_COUNT)]
MINIMUM_REPEAT_RECALL = 0.85
MINIMUM_MEDIAN_RECALL = 0.9
MINIMUM_COEFFICIENT_SIGN_AGREEMENT = 0.8
MAGNITUDE_BINS = [-np.inf, 18.0, 19.0, 20.0, np.inf]
MAGNITUDE_LABELS = ["g_le_18", "18_lt_g_le_19", "19_lt_g_le_20", "g_gt_20"]
LATITUDE_BINS = [0.0, 30.0, 60.0, np.inf]
LATITUDE_LABELS = ["0_to_30", "30_to_60", "60_to_90"]


def parse_arguments() -> argparse.Namespace:
    """Parse development inputs and stability artifact paths."""
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument(
        "--repeat-count",
        type=int,
        default=REPEAT_COUNT,
        choices=range(1, REPEAT_COUNT + 1),
        help="Run a deterministic prefix of the declared repeat seeds.",
    )
    return parser.parse_args()


def add_context(rows: pd.DataFrame, development_path: Path, stars_path: Path) -> pd.DataFrame:
    """Attach non-model magnitude and sky coordinates for stratified diagnostics."""
    development = pd.read_csv(
        development_path,
        dtype={"gaia_dr3_id": str},
        usecols=["benchmark_id", "ra", "dec", "phot_g_mean_mag"],
    ).rename(columns={"benchmark_id": "row_id"})
    stars = pd.read_csv(
        stars_path,
        dtype={"source_id": str},
        usecols=["source_id", "ra", "dec", "phot_g_mean_mag"],
    )
    stars["row_id"] = stars["source_id"].map(lambda value: f"sdss_star:{value}")
    context = pd.concat(
        [development, stars[["row_id", "ra", "dec", "phot_g_mean_mag"]]],
        ignore_index=True,
    )
    rows = rows.merge(context, on="row_id", how="left", validate="one_to_one")
    if rows[["ra", "dec", "phot_g_mean_mag"]].isna().any().any():
        raise RuntimeError("A stability row lacks magnitude or sky-position context")
    coordinates = SkyCoord(ra=rows["ra"].to_numpy() * u.deg, dec=rows["dec"].to_numpy() * u.deg)
    rows["absolute_galactic_latitude_deg"] = np.abs(coordinates.galactic.b.deg)
    rows["absolute_ecliptic_latitude_deg"] = np.abs(coordinates.barycentrictrueecliptic.lat.deg)
    return rows


def clean_coefficient_name(name: str) -> str:
    """Remove the ColumnTransformer prefix from an output feature name."""
    return name.removeprefix("features__")


def coefficient_records(
    model: object,
    repeat_index: int,
    repeat_seed: int,
    outer_fold: int,
) -> list[dict[str, object]]:
    """Return standardized logistic coefficients from one outer-fold model."""
    preprocessing = model.named_steps["preprocessing"]
    estimator = model.named_steps["model"]
    names = preprocessing.get_feature_names_out()
    return [
        {
            "repeat_index": repeat_index,
            "repeat_seed": repeat_seed,
            "outer_fold": outer_fold,
            "coefficient_feature": clean_coefficient_name(str(name)),
            "standardized_coefficient": float(value),
            "is_missing_indicator": "missingindicator_" in str(name),
        }
        for name, value in zip(names, estimator.coef_[0], strict=True)
    ]


def summarize_coefficients(coefficients: pd.DataFrame) -> pd.DataFrame:
    """Summarize coefficient range and agreement with each median sign."""
    records = []
    for feature, group in coefficients.groupby("coefficient_feature", sort=True):
        values = group["standardized_coefficient"].to_numpy(dtype=float)
        median = float(np.median(values))
        median_sign = float(np.sign(median))
        sign_agreement = float(np.mean(np.sign(values) == median_sign))
        records.append(
            {
                "coefficient_feature": feature,
                "is_missing_indicator": bool(group["is_missing_indicator"].iloc[0]),
                "fit_count": len(group),
                "coefficient_minimum": float(np.min(values)),
                "coefficient_median": median,
                "coefficient_maximum": float(np.max(values)),
                "median_sign": int(median_sign),
                "sign_agreement_fraction": sign_agreement,
            }
        )
    return pd.DataFrame(records)


def add_strata(predictions: pd.DataFrame) -> pd.DataFrame:
    """Assign the predeclared magnitude and absolute-latitude strata."""
    predictions = predictions.copy()
    predictions["g_magnitude_stratum"] = pd.cut(
        predictions["phot_g_mean_mag"],
        bins=MAGNITUDE_BINS,
        labels=MAGNITUDE_LABELS,
        right=True,
    )
    for column, output in [
        ("absolute_galactic_latitude_deg", "absolute_galactic_latitude_stratum"),
        ("absolute_ecliptic_latitude_deg", "absolute_ecliptic_latitude_stratum"),
    ]:
        predictions[output] = pd.cut(
            predictions[column],
            bins=LATITUDE_BINS,
            labels=LATITUDE_LABELS,
            right=False,
        )
    return predictions


def stratified_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Measure repeated OOF selection fractions in each declared stratum."""
    records = []
    dimensions = {
        "g_magnitude": "g_magnitude_stratum",
        "absolute_galactic_latitude": "absolute_galactic_latitude_stratum",
        "absolute_ecliptic_latitude": "absolute_ecliptic_latitude_stratum",
    }
    for dimension, column in dimensions.items():
        for (stratum, cohort), group in predictions.groupby(
            [column, "ml_cohort"], observed=True, sort=False
        ):
            records.append(
                {
                    "dimension": dimension,
                    "stratum": str(stratum),
                    "ml_cohort": cohort,
                    "source_count": int(group["row_id"].nunique()),
                    "prediction_count": len(group),
                    "selected_fraction": float(group["selected"].mean()),
                }
            )
    return pd.DataFrame(records)


def range_summary(values: pd.Series) -> dict[str, float]:
    """Return measured minimum, median, and maximum values."""
    return {
        "minimum": float(values.min()),
        "median": float(values.median()),
        "maximum": float(values.max()),
    }


def main() -> None:
    """Run repeated nested CV and write stability diagnostics."""
    arguments = parse_arguments()
    rows = load_cohorts(arguments.development, arguments.stars)
    rows = add_context(rows, arguments.development, arguments.stars)
    fit_rows = rows.loc[rows["fit_role"].eq("model_fit")].reset_index(drop=True)
    prediction_records = []
    fold_records = []
    all_coefficient_records = []
    repeat_records = []

    repeat_seeds = REPEAT_SEEDS[: arguments.repeat_count]
    for repeat_index, repeat_seed in enumerate(repeat_seeds, start=1):
        repeat_prediction_start = len(prediction_records)
        outer_splitter = StratifiedGroupKFold(
            n_splits=OUTER_FOLDS,
            shuffle=True,
            random_state=repeat_seed,
        )
        for outer_fold, (train_index, test_index) in enumerate(
            outer_splitter.split(fit_rows, fit_rows["target"], fit_rows["ml_group"]),
            start=1,
        ):
            train = fit_rows.iloc[train_index].reset_index(drop=True)
            test = fit_rows.iloc[test_index].reset_index(drop=True)
            parameters, threshold, inner_macro = choose_parameters(
                train,
                "logistic_regression",
                LOGISTIC_PARAMETERS,
                repeat_seed + outer_fold,
            )
            model = build_model("logistic_regression", parameters)
            model.fit(
                train[MODEL_FEATURES],
                train["target"],
                model__sample_weight=equal_cohort_weights(train),
            )
            scores = model.predict_proba(test[MODEL_FEATURES])[:, 1]
            selected = scores >= threshold
            fold_records.append(
                {
                    "repeat_index": repeat_index,
                    "repeat_seed": repeat_seed,
                    "outer_fold": outer_fold,
                    "regularization_c": float(parameters["regularization_c"]),
                    "inner_threshold": threshold,
                    "inner_macro_priority_retention": inner_macro,
                    "outer_ucd_recall": float(selected[test["target"].eq(1)].mean()),
                    "outer_macro_priority_retention": macro_priority_retention(test, selected),
                }
            )
            all_coefficient_records.extend(
                coefficient_records(model, repeat_index, repeat_seed, outer_fold)
            )
            for row, score, decision in zip(test.to_dict("records"), scores, selected, strict=True):
                prediction_records.append(
                    {
                        "repeat_index": repeat_index,
                        "repeat_seed": repeat_seed,
                        "outer_fold": outer_fold,
                        "row_id": row["row_id"],
                        "gaia_dr3_id": row["gaia_dr3_id"],
                        "ml_group": row["ml_group"],
                        "ml_cohort": row["ml_cohort"],
                        "score": float(score),
                        "selected": bool(decision),
                        "phot_g_mean_mag": float(row["phot_g_mean_mag"]),
                        "absolute_galactic_latitude_deg": float(
                            row["absolute_galactic_latitude_deg"]
                        ),
                        "absolute_ecliptic_latitude_deg": float(
                            row["absolute_ecliptic_latitude_deg"]
                        ),
                    }
                )
        repeat_predictions = pd.DataFrame(prediction_records[repeat_prediction_start:])
        repeat_selected = repeat_predictions["selected"].to_numpy(dtype=bool)
        repeat_rows = fit_rows.set_index("row_id").loc[repeat_predictions["row_id"]].reset_index()
        cohort_retention = {
            cohort: float(
                repeat_predictions.loc[
                    repeat_predictions["ml_cohort"].eq(cohort), "selected"
                ].mean()
            )
            for cohort in PRIORITY_COHORTS
        }
        repeat_records.append(
            {
                "repeat_index": repeat_index,
                "repeat_seed": repeat_seed,
                "ucd_recall": float(
                    repeat_predictions.loc[
                        repeat_predictions["ml_cohort"].eq("confirmed_ucd"), "selected"
                    ].mean()
                ),
                "macro_priority_retention": macro_priority_retention(repeat_rows, repeat_selected),
                **{f"{cohort}_retention": value for cohort, value in cohort_retention.items()},
            }
        )

    predictions = add_strata(pd.DataFrame(prediction_records))
    source_summary = predictions.groupby(
        [
            "row_id",
            "gaia_dr3_id",
            "ml_group",
            "ml_cohort",
            "phot_g_mean_mag",
            "absolute_galactic_latitude_deg",
            "absolute_ecliptic_latitude_deg",
            "g_magnitude_stratum",
            "absolute_galactic_latitude_stratum",
            "absolute_ecliptic_latitude_stratum",
        ],
        observed=True,
        as_index=False,
    ).agg(mean_score=("score", "mean"), selection_frequency=("selected", "mean"))
    source_summary["persistent_failure_case"] = np.where(
        source_summary["ml_cohort"].eq("confirmed_ucd"),
        source_summary["selection_frequency"].le(0.5),
        source_summary["selection_frequency"].ge(0.5),
    )
    folds = pd.DataFrame(fold_records)
    coefficient_fits = pd.DataFrame(all_coefficient_records)
    coefficient_summary = summarize_coefficients(coefficient_fits)
    strata = stratified_metrics(predictions)
    repeats = pd.DataFrame(repeat_records)

    for path in [
        arguments.predictions,
        arguments.source_summary,
        arguments.fold_metrics,
        arguments.coefficients,
        arguments.coefficient_summary,
        arguments.strata,
        arguments.summary,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(arguments.predictions, index=False)
    source_summary.to_csv(arguments.source_summary, index=False)
    folds.to_csv(arguments.fold_metrics, index=False)
    coefficient_fits.to_csv(arguments.coefficients, index=False)
    coefficient_summary.to_csv(arguments.coefficient_summary, index=False)
    strata.to_csv(arguments.strata, index=False)

    measurement_coefficients = coefficient_summary.loc[
        coefficient_summary["coefficient_feature"].isin(MODEL_FEATURES)
    ]
    coefficient_gate = bool(
        measurement_coefficients["sign_agreement_fraction"]
        .ge(MINIMUM_COEFFICIENT_SIGN_AGREEMENT)
        .all()
    )
    recall_median_gate = bool(repeats["ucd_recall"].median() >= MINIMUM_MEDIAN_RECALL)
    recall_minimum_gate = bool(repeats["ucd_recall"].min() >= MINIMUM_REPEAT_RECALL)
    ready = recall_median_gate and recall_minimum_gate and coefficient_gate
    persistent_counts = (
        source_summary.loc[source_summary["persistent_failure_case"]]
        .groupby("ml_cohort", observed=True)
        .size()
        .reindex(["confirmed_ucd", *PRIORITY_COHORTS], fill_value=0)
        .astype(int)
        .to_dict()
    )
    report = {
        "stability_version": STABILITY_VERSION,
        "validation_partition_inspected": False,
        "repeat_count": arguments.repeat_count,
        "repeat_seeds": repeat_seeds,
        "outer_folds": OUTER_FOLDS,
        "inner_folds": INNER_FOLDS,
        "target_ucd_recall": TARGET_UCD_RECALL,
        "model_family": "logistic_regression",
        "model_features": MODEL_FEATURES,
        "fit_row_count": len(fit_rows),
        "repeat_metrics": repeat_records,
        "ucd_recall_across_repeats": range_summary(repeats["ucd_recall"]),
        "macro_priority_retention_across_repeats": range_summary(
            repeats["macro_priority_retention"]
        ),
        "persistent_failure_counts": persistent_counts,
        "coefficient_measurement_feature_minimum_sign_agreement": float(
            measurement_coefficients["sign_agreement_fraction"].min()
        ),
        "readiness_criteria": {
            "median_ucd_recall_at_least_0p90": recall_median_gate,
            "minimum_repeat_ucd_recall_at_least_0p85": recall_minimum_gate,
            "all_measurement_coefficient_sign_agreement_at_least_0p80": coefficient_gate,
        },
        "ready_for_selector_freeze_review": ready,
        "inputs": {
            "development_sha256": calculate_sha256(arguments.development),
            "stars_sha256": calculate_sha256(arguments.stars),
        },
        "artifacts": {
            "predictions_sha256": calculate_sha256(arguments.predictions),
            "source_summary_sha256": calculate_sha256(arguments.source_summary),
            "fold_metrics_sha256": calculate_sha256(arguments.fold_metrics),
            "coefficients_sha256": calculate_sha256(arguments.coefficients),
            "coefficient_summary_sha256": calculate_sha256(arguments.coefficient_summary),
            "strata_sha256": calculate_sha256(arguments.strata),
        },
        "decision_status": (
            "ready_for_model_threshold_review_validation_still_sealed"
            if ready
            else "stability_gate_not_met_validation_still_sealed"
        ),
    }
    arguments.summary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
