"""Compare classical ML and hand-score point-source selectors with nested CV.

Only development rows and the benchmark-disjoint stellar supplement are used.
Models are fitted against equally weighted ordinary-star, NSS, and QSO cohorts;
galaxy and H II rows are predicted only as secondary stress samples.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    POINT_SOURCE_ML_COMPARISON,
    POINT_SOURCE_ML_FOLDS,
    POINT_SOURCE_ML_PREDICTIONS,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.utils.point_source_selector import MODEL_FEATURES, add_model_features

COMPARISON_VERSION = "point_source_ml_comparison_v5"
OUTER_FOLDS = 5
INNER_FOLDS = 4
RANDOM_SEED = 20260717
TARGET_UCD_RECALL = 0.9
PRIORITY_COHORTS = ["spectroscopic_star", "gaia_non_single_star", "spectroscopic_qso"]
EXCLUDED_PRIMARY_FEATURES = [
    "non_single_star",
    "classprob_dsc_combmod_galaxy",
    "classprob_dsc_combmod_quasar",
    "classprob_dsc_combmod_star",
    "in_galaxy_candidates",
    "in_qso_candidates",
    "radius_sersic",
    "n_sersic",
]
LOGISTIC_PARAMETERS = [
    {"regularization_c": value}
    for value in [0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0, 3000.0]
]
BOOSTING_PARAMETERS = [
    {
        "max_leaf_nodes": leaves,
        "learning_rate": learning_rate,
        "l2_regularization": regularization,
    }
    for leaves in [3, 7]
    for learning_rate in [0.03, 0.08]
    for regularization in [1.0, 10.0]
]


@dataclass
class HandScoreReference:
    """Training-fold empirical references for the interpretable baseline."""

    aen_groups: list[np.ndarray]
    flux_excess_groups: list[np.ndarray]
    proper_motion_groups: list[np.ndarray]
    parallax_groups: list[np.ndarray]


def parse_arguments() -> argparse.Namespace:
    """Parse development inputs and comparison outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES)
    parser.add_argument("--stars", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    parser.add_argument("--predictions", type=Path, default=POINT_SOURCE_ML_PREDICTIONS)
    parser.add_argument("--fold-metrics", type=Path, default=POINT_SOURCE_ML_FOLDS)
    parser.add_argument("--comparison", type=Path, default=POINT_SOURCE_ML_COMPARISON)
    return parser.parse_args()


def load_cohorts(development_path: Path, stars_path: Path) -> pd.DataFrame:
    """Build training and stress cohorts with leakage-safe spatial groups."""
    development = pd.read_csv(development_path, dtype={"gaia_dr3_id": str})
    development = add_model_features(development)
    development["ml_cohort"] = development["label_subtype"].map(
        {
            "ucd_confirmed": "confirmed_ucd",
            "gaia_non_single_star": "gaia_non_single_star",
            "spectroscopic_qso": "spectroscopic_qso",
            "spectroscopic_galaxy": "spectroscopic_galaxy",
            "compact_hii_region": "hii_region",
            "dwarf_galaxy_hii_region": "hii_region",
        }
    )
    development["ml_group"] = development["partition_group"]
    development["row_id"] = development["benchmark_id"]

    ucd_groups = development.loc[
        development["ml_cohort"].eq("confirmed_ucd"),
        ["gaia_dr3_id", "partition_group"],
    ].set_index("gaia_dr3_id")["partition_group"]
    stars = pd.read_csv(
        stars_path,
        dtype={"source_id": str, "matched_ucd_gaia_dr3_id": str},
    )
    stars = add_model_features(stars)
    stars["gaia_dr3_id"] = stars["source_id"]
    stars["ml_cohort"] = "spectroscopic_star"
    stars["ml_group"] = stars["matched_ucd_gaia_dr3_id"].map(ucd_groups)
    stars["row_id"] = stars["source_id"].map(lambda value: f"sdss_star:{value}")

    required = ["row_id", "gaia_dr3_id", "ml_cohort", "ml_group", *MODEL_FEATURES]
    rows = pd.concat(
        [
            development.loc[development["ml_cohort"].notna(), required],
            stars[required],
        ],
        ignore_index=True,
    )
    rows["target"] = rows["ml_cohort"].eq("confirmed_ucd").astype(int)
    rows["fit_role"] = np.where(
        rows["ml_cohort"].isin(["confirmed_ucd", *PRIORITY_COHORTS]),
        "model_fit",
        "secondary_stress",
    )
    if rows["ml_group"].isna().any():
        raise RuntimeError("An ML comparison row lacks its leakage-control group")
    return rows


def equal_cohort_weights(rows: pd.DataFrame) -> np.ndarray:
    """Give positives half the weight and each priority cohort one sixth."""
    weights = np.zeros(len(rows), dtype=float)
    positive = rows["ml_cohort"].eq("confirmed_ucd")
    weights[positive] = 0.5 / positive.sum()
    for cohort in PRIORITY_COHORTS:
        mask = rows["ml_cohort"].eq(cohort)
        weights[mask] = (0.5 / len(PRIORITY_COHORTS)) / mask.sum()
    return weights


def build_model(model_family: str, parameters: dict[str, float | int]) -> Pipeline:
    """Construct one deterministic classical model."""
    if model_family == "logistic_regression":
        preprocessing = ColumnTransformer(
            [
                (
                    "features",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                            ("scale", StandardScaler()),
                        ]
                    ),
                    MODEL_FEATURES,
                )
            ],
            remainder="drop",
        )
        estimator = LogisticRegression(
            C=float(parameters["regularization_c"]),
            max_iter=2_000,
            solver="lbfgs",
            random_state=RANDOM_SEED,
        )
        return Pipeline([("preprocessing", preprocessing), ("model", estimator)])
    if model_family == "histogram_gradient_boosting":
        estimator = HistGradientBoostingClassifier(
            max_iter=150,
            max_leaf_nodes=int(parameters["max_leaf_nodes"]),
            learning_rate=float(parameters["learning_rate"]),
            l2_regularization=float(parameters["l2_regularization"]),
            min_samples_leaf=20,
            random_state=RANDOM_SEED,
        )
        return Pipeline([("model", estimator)])
    raise ValueError(f"Unknown model family: {model_family}")


def threshold_for_recall(scores: pd.Series, target: float) -> float:
    """Return the observed positive-score cutoff retaining at least target recall."""
    ordered = np.sort(scores.dropna().to_numpy(dtype=float))[::-1]
    return float(ordered[int(np.ceil(target * len(ordered))) - 1])


def macro_priority_retention(rows: pd.DataFrame, selected: np.ndarray) -> float:
    """Return equal-cohort mean selected fraction across priority negatives."""
    return float(
        np.mean(
            [
                selected[rows["ml_cohort"].eq(cohort).to_numpy()].mean()
                for cohort in PRIORITY_COHORTS
            ]
        )
    )


def inner_oof_scores(
    rows: pd.DataFrame,
    model_family: str,
    parameters: dict[str, float | int],
    seed: int,
) -> np.ndarray:
    """Return grouped inner out-of-fold probabilities for hyperparameter choice."""
    scores = np.full(len(rows), np.nan)
    splitter = StratifiedGroupKFold(n_splits=INNER_FOLDS, shuffle=True, random_state=seed)
    for train_index, test_index in splitter.split(rows, rows["target"], rows["ml_group"]):
        train = rows.iloc[train_index]
        model = build_model(model_family, parameters)
        model.fit(
            train[MODEL_FEATURES],
            train["target"],
            model__sample_weight=equal_cohort_weights(train),
        )
        scores[test_index] = model.predict_proba(rows.iloc[test_index][MODEL_FEATURES])[:, 1]
    return scores


def choose_parameters(
    rows: pd.DataFrame,
    model_family: str,
    parameter_grid: list[dict[str, float | int]],
    seed: int,
) -> tuple[dict[str, float | int], float, float]:
    """Choose the minimum-macro-retention inner-CV configuration."""
    candidates = []
    positive = rows["target"].eq(1)
    for parameters in parameter_grid:
        scores = inner_oof_scores(rows, model_family, parameters, seed)
        threshold = threshold_for_recall(pd.Series(scores[positive.to_numpy()]), TARGET_UCD_RECALL)
        selected = scores >= threshold
        candidates.append(
            (
                macro_priority_retention(rows, selected),
                json.dumps(parameters, sort_keys=True),
                parameters,
                threshold,
            )
        )
    candidates.sort(key=lambda item: (item[0], item[1]))
    best = candidates[0]
    return best[2], best[3], best[0]


def empirical_cdf(values: pd.Series, references: list[np.ndarray]) -> np.ndarray:
    """Evaluate an equal-cohort empirical CDF fitted on training references."""
    values_array = values.to_numpy(dtype=float)
    output = np.full(len(values), np.nan)
    finite = np.isfinite(values_array)
    cohort_cdfs = []
    for reference in references:
        reference = np.sort(reference[np.isfinite(reference)])
        cohort_cdfs.append(
            np.searchsorted(reference, values_array[finite], side="right") / len(reference)
        )
    output[finite] = np.mean(cohort_cdfs, axis=0)
    return output


def fit_hand_reference(train: pd.DataFrame) -> HandScoreReference:
    """Fit fold-local empirical references for the approved hand-score baseline."""

    def groups(column: str, cohorts: list[str]) -> list[np.ndarray]:
        return [
            train.loc[train["ml_cohort"].eq(cohort), column].to_numpy(dtype=float)
            for cohort in cohorts
        ]

    return HandScoreReference(
        aen_groups=groups("log1p_astrometric_excess_noise", PRIORITY_COHORTS),
        flux_excess_groups=groups("phot_bp_rp_excess_factor", PRIORITY_COHORTS),
        proper_motion_groups=groups(
            "log1p_proper_motion_zero_significance",
            ["spectroscopic_star", "gaia_non_single_star"],
        ),
        parallax_groups=groups(
            "log1p_absolute_parallax_zero_significance",
            ["spectroscopic_star", "gaia_non_single_star"],
        ),
    )


def predict_hand_score(rows: pd.DataFrame, reference: HandScoreReference) -> np.ndarray:
    """Apply the 25/75 core and 10% conditional astrometric penalty."""
    aen = empirical_cdf(rows["log1p_astrometric_excess_noise"], reference.aen_groups)
    flux = empirical_cdf(rows["phot_bp_rp_excess_factor"], reference.flux_excess_groups)
    core_values = np.column_stack([aen, flux])
    core_weights = np.array([0.25, 0.75])
    available_weights = np.isfinite(core_values) * core_weights
    core = np.nansum(core_values * core_weights, axis=1) / available_weights.sum(axis=1)
    proper_motion = empirical_cdf(
        rows["log1p_proper_motion_zero_significance"], reference.proper_motion_groups
    )
    parallax = empirical_cdf(
        rows["log1p_absolute_parallax_zero_significance"], reference.parallax_groups
    )
    astrometry = np.column_stack([proper_motion, parallax])
    astrometry_available = np.isfinite(astrometry)
    astrometry_count = astrometry_available.sum(axis=1)
    astrometry_mean = np.divide(
        np.nansum(astrometry, axis=1),
        astrometry_count,
        out=np.zeros(len(rows), dtype=float),
        where=astrometry_count > 0,
    )
    compatibility = 1.0 - astrometry_mean
    compatibility[astrometry_count == 0] = 1.0
    return core * (1.0 - 0.1 * (1.0 - compatibility))


def inner_hand_oof_scores(rows: pd.DataFrame, seed: int) -> np.ndarray:
    """Return fold-local grouped OOF scores for the hand-score threshold."""
    scores = np.full(len(rows), np.nan)
    splitter = StratifiedGroupKFold(n_splits=INNER_FOLDS, shuffle=True, random_state=seed)
    for train_index, test_index in splitter.split(rows, rows["target"], rows["ml_group"]):
        reference = fit_hand_reference(rows.iloc[train_index])
        scores[test_index] = predict_hand_score(rows.iloc[test_index], reference)
    return scores


def main() -> None:
    """Run nested comparison and write row, fold, and summary artifacts."""
    arguments = parse_arguments()
    rows = load_cohorts(arguments.development, arguments.stars)
    fit_rows = rows.loc[rows["fit_role"].eq("model_fit")].reset_index(drop=True)
    stress_rows = rows.loc[rows["fit_role"].eq("secondary_stress")].reset_index(drop=True)
    outer_splitter = StratifiedGroupKFold(
        n_splits=OUTER_FOLDS,
        shuffle=True,
        random_state=RANDOM_SEED,
    )
    model_grids = {
        "logistic_regression": LOGISTIC_PARAMETERS,
        "histogram_gradient_boosting": BOOSTING_PARAMETERS,
    }
    prediction_records = []
    fold_records = []
    stress_accumulator: dict[str, list[np.ndarray]] = {
        family: [] for family in [*model_grids, "hand_rank_score"]
    }
    stress_selected_accumulator: dict[str, list[np.ndarray]] = {
        family: [] for family in [*model_grids, "hand_rank_score"]
    }
    for fold, (train_index, test_index) in enumerate(
        outer_splitter.split(fit_rows, fit_rows["target"], fit_rows["ml_group"]),
        start=1,
    ):
        train = fit_rows.iloc[train_index].reset_index(drop=True)
        test = fit_rows.iloc[test_index].reset_index(drop=True)
        for family, grid in model_grids.items():
            parameters, threshold, inner_macro = choose_parameters(
                train,
                family,
                grid,
                RANDOM_SEED + fold,
            )
            model = build_model(family, parameters)
            model.fit(
                train[MODEL_FEATURES],
                train["target"],
                model__sample_weight=equal_cohort_weights(train),
            )
            scores = model.predict_proba(test[MODEL_FEATURES])[:, 1]
            selected = scores >= threshold
            stress_scores = model.predict_proba(stress_rows[MODEL_FEATURES])[:, 1]
            stress_accumulator[family].append(stress_scores)
            stress_selected_accumulator[family].append(stress_scores >= threshold)
            parameters_json = json.dumps(parameters, sort_keys=True)
            fold_records.append(
                {
                    "model_family": family,
                    "outer_fold": fold,
                    "parameters": parameters_json,
                    "inner_threshold": threshold,
                    "inner_macro_priority_retention": inner_macro,
                    "outer_ucd_recall": float(selected[test["target"].eq(1)].mean()),
                    "outer_macro_priority_retention": macro_priority_retention(test, selected),
                }
            )
            for row, score, decision in zip(test.to_dict("records"), scores, selected, strict=True):
                prediction_records.append(
                    {
                        "model_family": family,
                        "row_id": row["row_id"],
                        "gaia_dr3_id": row["gaia_dr3_id"],
                        "ml_cohort": row["ml_cohort"],
                        "ml_group": row["ml_group"],
                        "outer_fold": fold,
                        "score": score,
                        "selected": bool(decision),
                        "prediction_role": "nested_outer_oof",
                    }
                )

        hand_inner_scores = inner_hand_oof_scores(train, RANDOM_SEED + fold)
        hand_threshold = threshold_for_recall(
            pd.Series(hand_inner_scores[train["target"].eq(1).to_numpy()]),
            TARGET_UCD_RECALL,
        )
        hand_reference = fit_hand_reference(train)
        hand_scores = predict_hand_score(test, hand_reference)
        hand_selected = hand_scores >= hand_threshold
        stress_hand_scores = predict_hand_score(stress_rows, hand_reference)
        stress_accumulator["hand_rank_score"].append(stress_hand_scores)
        stress_selected_accumulator["hand_rank_score"].append(stress_hand_scores >= hand_threshold)
        fold_records.append(
            {
                "model_family": "hand_rank_score",
                "outer_fold": fold,
                "parameters": json.dumps(
                    {"aen_weight": 0.25, "astrometric_penalty_weight": 0.1},
                    sort_keys=True,
                ),
                "inner_threshold": hand_threshold,
                "inner_macro_priority_retention": macro_priority_retention(
                    train, hand_inner_scores >= hand_threshold
                ),
                "outer_ucd_recall": float(hand_selected[test["target"].eq(1).to_numpy()].mean()),
                "outer_macro_priority_retention": macro_priority_retention(test, hand_selected),
            }
        )
        for row, score, decision in zip(
            test.to_dict("records"), hand_scores, hand_selected, strict=True
        ):
            prediction_records.append(
                {
                    "model_family": "hand_rank_score",
                    "row_id": row["row_id"],
                    "gaia_dr3_id": row["gaia_dr3_id"],
                    "ml_cohort": row["ml_cohort"],
                    "ml_group": row["ml_group"],
                    "outer_fold": fold,
                    "score": score,
                    "selected": bool(decision),
                    "prediction_role": "outer_oof",
                }
            )

    predictions = pd.DataFrame(prediction_records)
    for family in stress_accumulator:
        mean_scores = np.mean(stress_accumulator[family], axis=0)
        selected_fraction = np.mean(stress_selected_accumulator[family], axis=0)
        for row, score, fraction in zip(
            stress_rows.to_dict("records"), mean_scores, selected_fraction, strict=True
        ):
            predictions.loc[len(predictions)] = {
                "model_family": family,
                "row_id": row["row_id"],
                "gaia_dr3_id": row["gaia_dr3_id"],
                "ml_cohort": row["ml_cohort"],
                "ml_group": row["ml_group"],
                "outer_fold": 0,
                "score": score,
                "selected": fraction >= 0.5,
                "prediction_role": "secondary_stress_mean_outer_models",
            }
    arguments.predictions.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(arguments.predictions, index=False)
    folds = pd.DataFrame(fold_records)
    folds.to_csv(arguments.fold_metrics, index=False)

    comparison = {}
    for family in [*model_grids, "hand_rank_score"]:
        oof = predictions.loc[
            predictions["model_family"].eq(family)
            & predictions["prediction_role"].isin(["nested_outer_oof", "outer_oof"])
        ]
        positive = oof["ml_cohort"].eq("confirmed_ucd")
        cohort_retention = {
            cohort: float(oof.loc[oof["ml_cohort"].eq(cohort), "selected"].mean())
            for cohort in PRIORITY_COHORTS
        }
        stress = predictions.loc[
            predictions["model_family"].eq(family)
            & predictions["prediction_role"].eq("secondary_stress_mean_outer_models")
        ]
        comparison[family] = {
            "nested_oof_ucd_recall": float(oof.loc[positive, "selected"].mean()),
            "nested_oof_priority_retention": cohort_retention,
            "nested_oof_macro_priority_retention": float(np.mean(list(cohort_retention.values()))),
            "nested_oof_roc_auc": float(roc_auc_score(positive.astype(int), oof["score"])),
            "outer_fold_ucd_recall_range": [
                float(folds.loc[folds["model_family"].eq(family), "outer_ucd_recall"].min()),
                float(folds.loc[folds["model_family"].eq(family), "outer_ucd_recall"].max()),
            ],
            "secondary_stress_majority_retention": {
                cohort: float(stress.loc[stress["ml_cohort"].eq(cohort), "selected"].mean())
                for cohort in ["spectroscopic_galaxy", "hii_region"]
            },
        }
    report = {
        "comparison_version": COMPARISON_VERSION,
        "validation_partition_inspected": False,
        "target_ucd_recall": TARGET_UCD_RECALL,
        "outer_folds": OUTER_FOLDS,
        "inner_folds": INNER_FOLDS,
        "grouping_policy": "stars_inherit_matched_ucd_partition_group;other_rows_use_partition_group",
        "weighting_policy": "positive_total_0p5;each_priority_negative_cohort_total_0p1667",
        "priority_cohorts": PRIORITY_COHORTS,
        "model_features": MODEL_FEATURES,
        "excluded_primary_features": EXCLUDED_PRIMARY_FEATURES,
        "comparison": comparison,
        "inputs": {
            "development_sha256": calculate_sha256(arguments.development),
            "stars_sha256": calculate_sha256(arguments.stars),
        },
        "predictions_sha256": calculate_sha256(arguments.predictions),
        "fold_metrics_sha256": calculate_sha256(arguments.fold_metrics),
        "decision_status": "development_comparison_only_no_model_or_threshold_frozen",
    }
    arguments.comparison.parent.mkdir(parents=True, exist_ok=True)
    arguments.comparison.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
