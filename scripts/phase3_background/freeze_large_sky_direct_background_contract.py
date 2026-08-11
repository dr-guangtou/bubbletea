"""Freeze direct random-field background procedures before comparing outcomes."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST,
    LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
    LARGE_SKY_DIRECT_BACKGROUND_CONTRACT,
    LARGE_SKY_FIELD_GRID,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256

CONTRACT_VERSION = "large_sky_direct_background_contract_v1"


def stable_contract_identifier(contract: dict[str, object]) -> str:
    """Return a stable identifier for the direct-measurement rules."""
    encoded = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    return f"direct_background_contract_{hashlib.sha256(encoded).hexdigest()[:20]}"


def main() -> None:
    """Write the three unfitted direct comparison procedures and safeguards."""
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    measurements = pd.read_csv(LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY)
    scale_manifest = json.loads(LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST.read_text(encoding="utf-8"))
    development = grid.loc[grid["experiment_partition"].eq("development")]
    validation = grid.loc[grid["experiment_partition"].eq("validation")]
    procedures = [
        {
            "procedure_id": "galactic_latitude_band",
            "complexity_rank": 1,
            "plain_language_definition": (
                "Use every available training field in the same one of five broad "
                "absolute-Galactic-latitude bands."
            ),
        },
        {
            "procedure_id": "latitude_band_and_gaia_density_third",
            "complexity_rank": 2,
            "plain_language_definition": (
                "Within the same latitude band, use training fields in the same low, "
                "middle, or high third of total Gaia source density."
            ),
            "density_division_rule": "training_band_tertiles",
        },
        {
            "procedure_id": "twenty_nearest_latitude_and_gaia_density",
            "complexity_rank": 3,
            "plain_language_definition": (
                "Use the 20 training fields closest in absolute Galactic latitude and "
                "log total Gaia source density after training-only standardization."
            ),
            "comparison_field_count": 20,
        },
    ]
    contract_core = {
        "contract_version": CONTRACT_VERSION,
        "procedures": procedures,
        "response": {
            "measured_density_column": "selected_source_density_per_square_deg",
            "central_reference": "comparison_pool_median",
            "additional_center": "comparison_pool_arithmetic_mean",
            "central_quantile_probabilities": [0.025, 0.16, 0.84, 0.975],
            "preserve_comparison_field_identifiers": True,
        },
        "evaluation": {
            "group_column": "sky_block_id",
            "grouped_fold_count": 5,
            "primary_metric": "median_absolute_log_density_error_lower_is_better",
            "selection_rule": (
                "Choose the simplest procedure whose mean fold score is within one "
                "standard error of the lowest measured mean fold score."
            ),
            "secondary_metrics": [
                "root_mean_square_log_density_error",
                "empirical_68_percent_range_coverage",
                "empirical_95_percent_range_coverage",
                "comparison_pool_field_count",
                "extreme_flagged_field_result",
            ],
        },
        "applicability": {
            "minimum_absolute_galactic_latitude_deg": 20.0,
            "minimum_comparison_field_count": 10,
            "unavailable_not_zero": True,
            "total_gaia_density_is_comparison_property_not_source_cut": True,
        },
        "host_reporting_interface": {
            "report_valid_outer_annulus_measurement": True,
            "report_direct_random_field_distribution": True,
            "report_annulus_minus_random_median": True,
            "report_annulus_divided_by_random_median": True,
            "force_agreement": False,
            "outer_annulus_boundaries_already_calibrated": False,
        },
        "fitted_model_role": "diagnostic_interpolation_only",
        "held_back_validation_use": "unopened_on_this_branch_new_branch_only",
    }
    contract_id = stable_contract_identifier(contract_core)
    development_ids = set(development["field_id"].astype(str))
    validation_ids = set(validation["field_id"].astype(str))
    measurement_ids = set(measurements["field_id"].astype(str))
    checks = {
        "three_direct_procedures_declared": len(procedures) == 3,
        "procedures_in_increasing_complexity": [
            procedure["complexity_rank"] for procedure in procedures
        ]
        == [1, 2, 3],
        "all_398_development_measurements_available": len(measurements) == 398
        and measurement_ids == development_ids,
        "all_102_validation_fields_remain_absent": len(validation_ids) == 102
        and validation_ids.isdisjoint(measurement_ids),
        "complete_measurement_manifest_passed": scale_manifest["status"]
        == "complete_development_measurement"
        and scale_manifest["passed_count"] == scale_manifest["check_count"],
        "whole_sky_block_testing_declared": contract_core["evaluation"]["grouped_fold_count"] == 5,
        "measured_distributions_preserved": contract_core["response"][
            "preserve_comparison_field_identifiers"
        ],
        "outer_annulus_and_random_difference_required": contract_core["host_reporting_interface"][
            "report_annulus_minus_random_median"
        ],
        "fitted_model_is_diagnostic_only": contract_core["fitted_model_role"]
        == "diagnostic_interpolation_only",
        "validation_deferred_to_new_branch": contract_core["held_back_validation_use"]
        == "unopened_on_this_branch_new_branch_only",
        "no_field_scientifically_approved": not grid["eligible_for_scientific_background"]
        .astype(bool)
        .any(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    report = {
        "contract_version": CONTRACT_VERSION,
        "contract_id": contract_id,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "direct_procedures_frozen_before_outcome_comparison",
        **contract_core,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                LARGE_SKY_FIELD_GRID,
                LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
                LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST,
            )
        ],
        "development_field_count": len(development_ids),
        "held_back_validation_field_count": len(validation_ids),
        "validation_selector_results_opened": False,
        "scientific_background_approval": False,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DIRECT_BACKGROUND_CONTRACT.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Direct background contract failed: {checks}")


if __name__ == "__main__":
    main()
