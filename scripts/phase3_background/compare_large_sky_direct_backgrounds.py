"""Compare direct random-field background procedures on development fields only."""

import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST,
    LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
    LARGE_SKY_DIRECT_BACKGROUND_CONTRACT,
    LARGE_SKY_DIRECT_BACKGROUND_FOLD_RESULTS,
    LARGE_SKY_DIRECT_BACKGROUND_MANIFEST,
    LARGE_SKY_DIRECT_BACKGROUND_PREDICTIONS,
    LARGE_SKY_DIRECT_BACKGROUND_REFERENCE,
    LARGE_SKY_DIRECT_BACKGROUND_SUMMARY,
    LARGE_SKY_FIELD_GRID,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256

COMPARISON_VERSION = "large_sky_direct_background_comparison_v1"
EXPECTED_CONTRACT_ID = "direct_background_contract_fcf4570e7d04075f5f78"
PROCEDURE_ORDER = (
    "galactic_latitude_band",
    "latitude_band_and_gaia_density_third",
    "twenty_nearest_latitude_and_gaia_density",
)


def prepare_frame(measurements: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    """Join the frozen latitude band to measured development-field densities."""
    frame = measurements.merge(
        grid[["field_id", "equal_area_latitude_band_index"]],
        on="field_id",
        validate="one_to_one",
    ).sort_values("field_id", ignore_index=True)
    return frame.assign(
        absolute_galactic_latitude_deg=frame["galactic_latitude_deg"].abs(),
        log_total_gaia_source_density=np.log(frame["total_gaia_source_density_per_square_deg"]),
    )


def density_third(values: pd.Series, lower: float, upper: float) -> pd.Series:
    """Assign low, middle, or high using two training-only dividing values."""
    return pd.Series(
        np.searchsorted([lower, upper], values.to_numpy(dtype=float), side="right"),
        index=values.index,
    )


def comparison_pool(
    training: pd.DataFrame,
    target: pd.Series,
    procedure_id: str,
    nearest_field_count: int = 20,
) -> pd.DataFrame:
    """Return directly measured training fields selected by one frozen procedure."""
    target_band = int(target["equal_area_latitude_band_index"])
    same_band = training.loc[training["equal_area_latitude_band_index"].eq(target_band)].copy()
    if procedure_id == "galactic_latitude_band":
        return same_band.sort_values("field_id")
    if procedure_id == "latitude_band_and_gaia_density_third":
        lower, upper = same_band["total_gaia_source_density_per_square_deg"].quantile(
            [1 / 3, 2 / 3]
        )
        training_thirds = density_third(
            same_band["total_gaia_source_density_per_square_deg"], lower, upper
        )
        target_third = int(
            np.searchsorted(
                [lower, upper],
                float(target["total_gaia_source_density_per_square_deg"]),
                side="right",
            )
        )
        return same_band.loc[training_thirds.eq(target_third)].sort_values("field_id")
    if procedure_id == "twenty_nearest_latitude_and_gaia_density":
        feature_columns = [
            "absolute_galactic_latitude_deg",
            "log_total_gaia_source_density",
        ]
        training_features = training[feature_columns].to_numpy(dtype=float)
        center = training_features.mean(axis=0)
        scale = training_features.std(axis=0)
        if np.any(scale <= 0):
            raise RuntimeError("Nearest-field comparison has a zero training scale")
        target_features = target[feature_columns].to_numpy(dtype=float)
        standardized_training = (training_features - center) / scale
        standardized_target = (target_features - center) / scale
        distances = np.sqrt(np.square(standardized_training - standardized_target).sum(axis=1))
        return (
            training.assign(comparison_distance=distances)
            .sort_values(["comparison_distance", "field_id"])
            .head(nearest_field_count)
        )
    raise ValueError(f"Unknown direct background procedure: {procedure_id}")


def prediction_record(
    target: pd.Series,
    pool: pd.DataFrame,
    procedure_id: str,
    outer_fold: int,
) -> dict[str, object]:
    """Summarize one preserved distribution of directly measured comparison fields."""
    densities = pool["selected_source_density_per_square_deg"].to_numpy(dtype=float)
    lower_95, lower_68, upper_68, upper_95 = np.quantile(densities, [0.025, 0.16, 0.84, 0.975])
    observed = float(target["selected_source_density_per_square_deg"])
    median = float(np.median(densities))
    return {
        "comparison_version": COMPARISON_VERSION,
        "procedure_id": procedure_id,
        "outer_fold": outer_fold,
        "field_id": str(target["field_id"]),
        "sky_block_id": str(target["sky_block_id"]),
        "environment_flag_state": str(target["environment_flag_state"]),
        "absolute_galactic_latitude_deg": float(target["absolute_galactic_latitude_deg"]),
        "total_gaia_source_density_per_square_deg": float(
            target["total_gaia_source_density_per_square_deg"]
        ),
        "observed_selected_source_density_per_square_deg": observed,
        "comparison_pool_field_count": len(pool),
        "comparison_pool_field_ids": ";".join(pool["field_id"].astype(str)),
        "comparison_pool_sky_block_ids": ";".join(sorted(set(pool["sky_block_id"].astype(str)))),
        "comparison_pool_densities_json": json.dumps(densities.tolist()),
        "comparison_density_median_per_square_deg": median,
        "comparison_density_mean_per_square_deg": float(np.mean(densities)),
        "comparison_density_68_lower_per_square_deg": float(lower_68),
        "comparison_density_68_upper_per_square_deg": float(upper_68),
        "comparison_density_95_lower_per_square_deg": float(lower_95),
        "comparison_density_95_upper_per_square_deg": float(upper_95),
        "log_observed_to_comparison_median": float(np.log(observed / median)),
        "inside_comparison_68_percent_range": bool(lower_68 <= observed <= upper_68),
        "inside_comparison_95_percent_range": bool(lower_95 <= observed <= upper_95),
    }


def evaluate_procedures(
    frame: pd.DataFrame,
    procedure_ids: tuple[str, ...],
    fold_count: int,
) -> pd.DataFrame:
    """Create held-out predictions while excluding each target's whole sky block."""
    splitter = GroupKFold(n_splits=fold_count)
    records = []
    for outer_fold, (training_indices, test_indices) in enumerate(
        splitter.split(frame, groups=frame["sky_block_id"]), start=1
    ):
        training = frame.iloc[training_indices]
        test = frame.iloc[test_indices]
        for procedure_id in procedure_ids:
            for _, target in test.iterrows():
                pool = comparison_pool(training, target, procedure_id)
                records.append(prediction_record(target, pool, procedure_id, outer_fold))
    return pd.DataFrame(records)


def fold_results(predictions: pd.DataFrame) -> pd.DataFrame:
    """Summarize the direct comparison errors and measured-range coverage by fold."""
    records = []
    for (procedure_id, outer_fold), fields in predictions.groupby(
        ["procedure_id", "outer_fold"], sort=True
    ):
        errors = fields["log_observed_to_comparison_median"].to_numpy(dtype=float)
        pool_counts = fields["comparison_pool_field_count"].to_numpy(dtype=int)
        records.append(
            {
                "comparison_version": COMPARISON_VERSION,
                "procedure_id": procedure_id,
                "outer_fold": outer_fold,
                "field_count": len(fields),
                "median_absolute_log_density_error": float(np.median(np.abs(errors))),
                "root_mean_square_log_density_error": float(np.sqrt(np.mean(np.square(errors)))),
                "empirical_68_percent_range_coverage": float(
                    fields["inside_comparison_68_percent_range"].mean()
                ),
                "empirical_95_percent_range_coverage": float(
                    fields["inside_comparison_95_percent_range"].mean()
                ),
                "minimum_comparison_pool_field_count": int(pool_counts.min()),
                "median_comparison_pool_field_count": float(np.median(pool_counts)),
                "maximum_comparison_pool_field_count": int(pool_counts.max()),
            }
        )
    return pd.DataFrame(records)


def summarize_procedures(predictions: pd.DataFrame, folds: pd.DataFrame) -> pd.DataFrame:
    """Apply the frozen simplest-within-one-standard-error selection rule."""
    records = []
    for complexity_rank, procedure_id in enumerate(PROCEDURE_ORDER, start=1):
        procedure_folds = folds.loc[folds["procedure_id"].eq(procedure_id)]
        procedure_fields = predictions.loc[predictions["procedure_id"].eq(procedure_id)]
        fold_scores = procedure_folds["median_absolute_log_density_error"].to_numpy()
        errors = procedure_fields["log_observed_to_comparison_median"].to_numpy()
        records.append(
            {
                "comparison_version": COMPARISON_VERSION,
                "procedure_id": procedure_id,
                "complexity_rank": complexity_rank,
                "mean_fold_median_absolute_log_density_error": float(np.mean(fold_scores)),
                "fold_score_standard_deviation": float(np.std(fold_scores, ddof=1)),
                "fold_score_standard_error": float(
                    np.std(fold_scores, ddof=1) / math.sqrt(len(fold_scores))
                ),
                "overall_median_absolute_log_density_error": float(np.median(np.abs(errors))),
                "overall_root_mean_square_log_density_error": float(
                    np.sqrt(np.mean(np.square(errors)))
                ),
                "empirical_68_percent_range_coverage": float(
                    procedure_fields["inside_comparison_68_percent_range"].mean()
                ),
                "empirical_95_percent_range_coverage": float(
                    procedure_fields["inside_comparison_95_percent_range"].mean()
                ),
                "minimum_comparison_pool_field_count": int(
                    procedure_fields["comparison_pool_field_count"].min()
                ),
                "median_comparison_pool_field_count": float(
                    procedure_fields["comparison_pool_field_count"].median()
                ),
                "maximum_comparison_pool_field_count": int(
                    procedure_fields["comparison_pool_field_count"].max()
                ),
            }
        )
    summary = pd.DataFrame(records)
    best_index = summary["mean_fold_median_absolute_log_density_error"].idxmin()
    threshold = float(
        summary.loc[best_index, "mean_fold_median_absolute_log_density_error"]
        + summary.loc[best_index, "fold_score_standard_error"]
    )
    selected_index = summary.loc[
        summary["mean_fold_median_absolute_log_density_error"].le(threshold)
    ]["complexity_rank"].idxmin()
    summary["best_measured_score"] = summary.index == best_index
    summary["one_standard_error_threshold"] = threshold
    summary["inside_one_standard_error_threshold"] = summary[
        "mean_fold_median_absolute_log_density_error"
    ].le(threshold)
    summary["selected_direct_procedure"] = summary.index == selected_index
    return summary


def write_frame_atomic(frame: pd.DataFrame, path: Path) -> None:
    """Write a table without leaving a partial final file."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def main() -> None:
    """Compare, select, and freeze one direct random-field procedure."""
    started = perf_counter()
    contract = json.loads(LARGE_SKY_DIRECT_BACKGROUND_CONTRACT.read_text(encoding="utf-8"))
    scale_manifest = json.loads(LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST.read_text(encoding="utf-8"))
    measurements = pd.read_csv(LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY)
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    frame = prepare_frame(measurements, grid)
    procedure_ids = tuple(procedure["procedure_id"] for procedure in contract["procedures"])
    predictions = evaluate_procedures(
        frame, procedure_ids, int(contract["evaluation"]["grouped_fold_count"])
    )
    folds = fold_results(predictions)
    summary = summarize_procedures(predictions, folds)
    selected_id = str(summary.loc[summary["selected_direct_procedure"], "procedure_id"].iloc[0])
    reference = predictions.loc[predictions["procedure_id"].eq(selected_id)].copy()
    extreme = reference.loc[reference["field_id"].eq("sky_field_0317")].iloc[0]

    LARGE_SKY_DIRECT_BACKGROUND_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    write_frame_atomic(summary, LARGE_SKY_DIRECT_BACKGROUND_SUMMARY)
    write_frame_atomic(folds, LARGE_SKY_DIRECT_BACKGROUND_FOLD_RESULTS)
    write_frame_atomic(predictions, LARGE_SKY_DIRECT_BACKGROUND_PREDICTIONS)
    write_frame_atomic(reference, LARGE_SKY_DIRECT_BACKGROUND_REFERENCE)

    validation_ids = set(
        grid.loc[grid["experiment_partition"].eq("validation"), "field_id"].astype(str)
    )
    prediction_ids = set(predictions["field_id"].astype(str))
    pool_block_overlaps = []
    block_by_field = frame.set_index("field_id")["sky_block_id"].to_dict()
    for _, row in predictions.iterrows():
        pool_blocks = {
            block_by_field[field_id] for field_id in row["comparison_pool_field_ids"].split(";")
        }
        pool_block_overlaps.append(row["sky_block_id"] in pool_blocks)
    checks = {
        "frozen_contract_identifier_matches": contract["contract_id"] == EXPECTED_CONTRACT_ID,
        "frozen_contract_passed_all_checks": contract["passed_count"] == contract["check_count"],
        "complete_measurements_passed_all_checks": scale_manifest["passed_count"]
        == scale_manifest["check_count"],
        "all_three_procedures_evaluated": tuple(summary["procedure_id"]) == PROCEDURE_ORDER,
        "each_procedure_predicts_all_398_fields_once": predictions.groupby("procedure_id")[
            "field_id"
        ]
        .nunique()
        .eq(398)
        .all(),
        "no_held_out_sky_block_enters_its_comparison_pool": not any(pool_block_overlaps),
        "no_validation_field_used": validation_ids.isdisjoint(prediction_ids),
        "all_comparison_pools_meet_minimum_size": predictions["comparison_pool_field_count"]
        .ge(contract["applicability"]["minimum_comparison_field_count"])
        .all(),
        "all_measured_ranges_ordered": (
            predictions["comparison_density_95_lower_per_square_deg"]
            <= predictions["comparison_density_68_lower_per_square_deg"]
        ).all()
        and (
            predictions["comparison_density_68_lower_per_square_deg"]
            <= predictions["comparison_density_median_per_square_deg"]
        ).all()
        and (
            predictions["comparison_density_median_per_square_deg"]
            <= predictions["comparison_density_68_upper_per_square_deg"]
        ).all()
        and (
            predictions["comparison_density_68_upper_per_square_deg"]
            <= predictions["comparison_density_95_upper_per_square_deg"]
        ).all(),
        "exactly_one_direct_procedure_selected": summary["selected_direct_procedure"].sum() == 1,
        "selected_procedure_satisfies_one_standard_error_rule": summary.loc[
            summary["selected_direct_procedure"], "inside_one_standard_error_threshold"
        ].all(),
        "reference_preserves_398_selected_procedure_distributions": len(reference) == 398
        and reference["field_id"].is_unique,
        "extreme_flagged_field_preserved": extreme["environment_flag_state"]
        == "one_or_more_count_blind_environment_flags",
        "fitted_model_remains_diagnostic_only": contract["fitted_model_role"]
        == "diagnostic_interpolation_only",
        "validation_results_remain_unopened": contract["validation_selector_results_opened"]
        is False,
        "no_field_scientifically_approved": not grid["eligible_for_scientific_background"]
        .astype(bool)
        .any(),
        "no_archive_query_executed": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    outputs = [
        LARGE_SKY_DIRECT_BACKGROUND_SUMMARY,
        LARGE_SKY_DIRECT_BACKGROUND_FOLD_RESULTS,
        LARGE_SKY_DIRECT_BACKGROUND_PREDICTIONS,
        LARGE_SKY_DIRECT_BACKGROUND_REFERENCE,
    ]
    report = {
        "comparison_version": COMPARISON_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "direct_random_field_procedure_selected_validation_unopened",
        "contract_id": contract["contract_id"],
        "plain_language_scope": (
            "Three ways of selecting directly measured comparison fields were tested on "
            "398 development fields. No fitted curve supplies the primary reference."
        ),
        "selected_procedure_id": selected_id,
        "field_count": len(frame),
        "sky_block_count": frame["sky_block_id"].nunique(),
        "extreme_flagged_field_result": {
            key: extreme[key]
            for key in (
                "field_id",
                "observed_selected_source_density_per_square_deg",
                "comparison_density_median_per_square_deg",
                "comparison_density_68_lower_per_square_deg",
                "comparison_density_68_upper_per_square_deg",
                "comparison_density_95_lower_per_square_deg",
                "comparison_density_95_upper_per_square_deg",
                "comparison_pool_field_count",
                "inside_comparison_95_percent_range",
            )
        },
        "applicability": contract["applicability"],
        "host_reporting_interface": contract["host_reporting_interface"],
        "fitted_model_role": contract["fitted_model_role"],
        "held_back_validation_field_count": 102,
        "validation_selector_results_opened": False,
        "scientific_background_approval": False,
        "archive_queries_executed": 0,
        "elapsed_seconds": perf_counter() - started,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                LARGE_SKY_DIRECT_BACKGROUND_CONTRACT,
                LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
                LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST,
                LARGE_SKY_FIELD_GRID,
            )
        ],
        "outputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in outputs
        ],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DIRECT_BACKGROUND_MANIFEST.write_text(
        json.dumps(report, indent=2, default=lambda value: value.item()) + "\n",
        encoding="utf-8",
    )
    if not all(checks.values()):
        raise RuntimeError(f"Direct background comparison failed: {checks}")


if __name__ == "__main__":
    main()
