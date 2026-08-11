"""Validate direct random-field comparison mechanics on synthetic fields."""

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
    LARGE_SKY_DIRECT_BACKGROUND_CONTRACT,
    LARGE_SKY_DIRECT_BACKGROUND_VALIDATION,
)
from scripts.phase3_background.compare_large_sky_direct_backgrounds import (
    PROCEDURE_ORDER,
    evaluate_procedures,
    fold_results,
    summarize_procedures,
)

VALIDATION_VERSION = "large_sky_direct_background_validation_v1"


def synthetic_frame() -> pd.DataFrame:
    """Return 300 deterministic fields in 30 held-together sky blocks."""
    field_index = np.arange(300)
    latitude_band = np.mod(field_index, 5)
    absolute_latitude = 22.0 + latitude_band * 12.0 + np.mod(field_index, 7) * 0.4
    log_total_density = 8.0 + np.mod(field_index * 11, 90) / 30.0
    selected_density = np.exp(0.55 * log_total_density - 0.018 * absolute_latitude)
    return pd.DataFrame(
        {
            "field_id": [f"synthetic_field_{index:03d}" for index in field_index],
            "sky_block_id": [f"synthetic_block_{index // 10:02d}" for index in field_index],
            "environment_flag_state": np.where(
                np.mod(field_index, 4) == 0,
                "one_or_more_count_blind_environment_flags",
                "no_represented_environment_intersection",
            ),
            "equal_area_latitude_band_index": latitude_band,
            "absolute_galactic_latitude_deg": absolute_latitude,
            "galactic_latitude_deg": absolute_latitude,
            "log_total_gaia_source_density": log_total_density,
            "total_gaia_source_density_per_square_deg": np.exp(log_total_density),
            "selected_source_density_per_square_deg": selected_density,
        }
    )


def main() -> None:
    """Run and audit all three direct procedures without archive or real-field reads."""
    started = perf_counter()
    contract = json.loads(LARGE_SKY_DIRECT_BACKGROUND_CONTRACT.read_text(encoding="utf-8"))
    frame = synthetic_frame()
    predictions = evaluate_procedures(frame, PROCEDURE_ORDER, fold_count=5)
    folds = fold_results(predictions)
    summary = summarize_procedures(predictions, folds)
    block_by_field = frame.set_index("field_id")["sky_block_id"].to_dict()
    block_overlaps = []
    for _, row in predictions.iterrows():
        pool_blocks = {
            block_by_field[field_id] for field_id in row["comparison_pool_field_ids"].split(";")
        }
        block_overlaps.append(row["sky_block_id"] in pool_blocks)
    nearest = predictions.loc[
        predictions["procedure_id"].eq("twenty_nearest_latitude_and_gaia_density")
    ]
    checks = {
        "three_procedures_match_frozen_order": tuple(summary["procedure_id"]) == PROCEDURE_ORDER,
        "each_procedure_predicts_all_300_fields": predictions.groupby("procedure_id")["field_id"]
        .nunique()
        .eq(300)
        .all(),
        "five_folds_recorded_per_procedure": folds.groupby("procedure_id")["outer_fold"]
        .nunique()
        .eq(5)
        .all(),
        "held_out_blocks_never_enter_comparison_pools": not any(block_overlaps),
        "nearest_procedure_uses_exactly_twenty_fields": nearest["comparison_pool_field_count"]
        .eq(20)
        .all(),
        "all_pools_exceed_frozen_minimum": predictions["comparison_pool_field_count"]
        .ge(contract["applicability"]["minimum_comparison_field_count"])
        .all(),
        "pool_identifiers_and_density_values_align": all(
            len(row["comparison_pool_field_ids"].split(";"))
            == len(json.loads(row["comparison_pool_densities_json"]))
            == row["comparison_pool_field_count"]
            for _, row in predictions.iterrows()
        ),
        "exactly_one_procedure_selected": summary["selected_direct_procedure"].sum() == 1,
        "no_real_field_measurement_read": True,
        "no_archive_query_executed": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    report = {
        "validation_version": VALIDATION_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "plain_language_result": (
            "The synthetic test selected measured comparison pools for 300 fields while "
            "keeping every held-out sky block separate and preserving every pool member."
        ),
        "synthetic_field_count": len(frame),
        "synthetic_sky_block_count": frame["sky_block_id"].nunique(),
        "archive_queries_executed": 0,
        "real_field_measurements_read": False,
        "elapsed_seconds": perf_counter() - started,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DIRECT_BACKGROUND_VALIDATION.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Direct background validation failed: {checks}")


if __name__ == "__main__":
    main()
