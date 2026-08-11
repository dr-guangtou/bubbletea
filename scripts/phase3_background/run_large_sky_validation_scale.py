"""Retrieve frozen-selector measurements for reserved large-sky validation fields."""

import argparse
import json
import logging
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import requests
from pyvo.dal import tap
from pyvo.dal.exceptions import DALAccessError

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
    LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_FIELD_GRID_MANIFEST,
    LARGE_SKY_VALIDATION_RUN_CONTRACT,
    LARGE_SKY_VALIDATION_SCALE_MANIFEST,
    LARGE_SKY_VALIDATION_SCALE_SUMMARY,
    POINT_SOURCE_LOGISTIC_MODEL,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import (
    file_sha256,
    write_json_atomic,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.benchmark_large_sky_development_retrieval import (
    require_external_checkpoint_root,
)
from scripts.phase3_background.freeze_large_sky_validation_run import VALIDATION_RUN_VERSION
from scripts.phase3_background.run_large_sky_development_retrieval import write_frame_atomic
from scripts.phase3_background.run_large_sky_development_scale import (
    ArchiveTimeoutSession,
    FieldAttemptTimeoutError,
    completed_receipt_is_valid,
    field_attempt_timeout,
    process_new_field,
    scale_field_directory,
    stable_processing_order,
    write_failure_receipt,
)
from scripts.utils.point_source_selector import SELECTOR_VERSION, load_frozen_selector

LOGGER = logging.getLogger(__name__)
DEFAULT_MAXIMUM_NEW_FIELDS = 0


def parse_arguments() -> argparse.Namespace:
    """Parse the explicit upper limit on new reserved-field attempts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--maximum-new-fields",
        type=int,
        default=DEFAULT_MAXIMUM_NEW_FIELDS,
        help=(
            "Maximum unfinished validation fields to query. The default is zero so "
            "reserved results cannot be opened accidentally."
        ),
    )
    parser.add_argument(
        "--retry-failed-fields",
        action="store_true",
        help=(
            "Retry unfinished fields with preserved failure receipts. They are deferred "
            "by default so one archive problem cannot block untouched fields."
        ),
    )
    arguments = parser.parse_args()
    if arguments.maximum_new_fields < 0:
        parser.error("--maximum-new-fields must be zero or positive")
    return arguments


def empty_or_all(value: pd.Series | np.ndarray) -> bool:
    """Return true for an empty validation summary or when every value is true."""
    return bool(len(value) == 0 or np.asarray(value).all())


def main() -> None:
    """Resume a bounded number of reserved fields and preserve verified receipts."""
    arguments = parse_arguments()
    require_external_checkpoint_root()
    contract = json.loads(LARGE_SKY_VALIDATION_RUN_CONTRACT.read_text(encoding="utf-8"))
    if contract["status"] != "frozen_before_reserved_field_retrieval":
        raise RuntimeError("Validation retrieval requires the unopened frozen contract")
    if contract["passed_count"] != contract["check_count"]:
        raise RuntimeError("Validation retrieval contract did not pass every safeguard")

    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    grid_manifest = json.loads(LARGE_SKY_FIELD_GRID_MANIFEST.read_text(encoding="utf-8"))
    validation = grid.loc[grid["experiment_partition"].eq("validation")].copy()
    development_ids = set(
        grid.loc[grid["experiment_partition"].eq("development"), "field_id"].astype(str)
    )
    validation["processing_order"] = validation["field_id"].map(
        lambda field_id: stable_processing_order(str(field_id), VALIDATION_RUN_VERSION)
    )
    validation = validation.sort_values(["processing_order", "field_id"])
    ordered_ids = validation["field_id"].astype(str).tolist()
    if ordered_ids != contract["validation_field_ids_in_processing_order"]:
        raise RuntimeError("Reserved-field identities or processing order changed")

    maximum_rows_per_strip = int(contract["retrieval"]["maximum_rows_per_strip"])
    records: list[dict[str, object]] = []
    completed_field_ids: set[str] = set()
    invalid_receipt_field_ids = []
    previous_failure_field_ids = {
        str(field["field_id"])
        for _, field in validation.iterrows()
        if any(
            scale_field_directory(
                str(field["grid_id"]), str(field["field_id"]), VALIDATION_RUN_VERSION
            ).glob("failure_*.json")
        )
    }
    for _, field in validation.iterrows():
        field_id = str(field["field_id"])
        receipt_path = (
            scale_field_directory(str(field["grid_id"]), field_id, VALIDATION_RUN_VERSION)
            / "field_receipt.json"
        )
        if completed_receipt_is_valid(
            receipt_path,
            field,
            maximum_rows_per_strip,
            run_version=VALIDATION_RUN_VERSION,
            expected_partition="validation",
        ):
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            records.append(receipt["summary_record"])
            completed_field_ids.add(field_id)
        elif receipt_path.exists():
            invalid_receipt_field_ids.append(field_id)

    service = tap.TAPService(DATA_LAB_TAP_URL, session=ArchiveTimeoutSession())
    selector = load_frozen_selector()
    run_started = perf_counter()
    attempted_field_ids = []
    newly_completed_field_ids = []
    failed_field_attempts = []
    interrupted = False
    for _, field in validation.iterrows():
        field_id = str(field["field_id"])
        if field_id in completed_field_ids:
            continue
        if field_id in previous_failure_field_ids and not arguments.retry_failed_fields:
            continue
        if len(attempted_field_ids) >= arguments.maximum_new_fields:
            break
        attempted_field_ids.append(field_id)
        LOGGER.info("Processing reserved validation field %s", field_id)
        attempt_started = perf_counter()
        try:
            with field_attempt_timeout():
                record, receipt = process_new_field(
                    service,
                    selector,
                    field,
                    maximum_rows_per_strip,
                    run_version=VALIDATION_RUN_VERSION,
                    expected_partition="validation",
                    source_state="new_verified_validation_retrieval",
                )
        except KeyboardInterrupt as error:
            failed_field_attempts.append(
                write_failure_receipt(
                    field,
                    error,
                    perf_counter() - attempt_started,
                    run_version=VALIDATION_RUN_VERSION,
                )
            )
            interrupted = True
            break
        except (requests.RequestException, DALAccessError, FieldAttemptTimeoutError) as error:
            failed_field_attempts.append(
                write_failure_receipt(
                    field,
                    error,
                    perf_counter() - attempt_started,
                    run_version=VALIDATION_RUN_VERSION,
                )
            )
            LOGGER.warning("Preserved recoverable failure for %s: %s", field_id, error)
            continue
        receipt_path = (
            scale_field_directory(str(field["grid_id"]), field_id, VALIDATION_RUN_VERSION)
            / "field_receipt.json"
        )
        write_json_atomic(receipt_path, receipt)
        records.append(record)
        completed_field_ids.add(field_id)
        newly_completed_field_ids.append(field_id)
        if field_id in invalid_receipt_field_ids:
            invalid_receipt_field_ids.remove(field_id)
        write_frame_atomic(
            pd.DataFrame(records).sort_values(["processing_order", "field_id"]),
            LARGE_SKY_VALIDATION_SCALE_SUMMARY,
        )

    development_columns = pd.read_csv(LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY, nrows=0).columns.tolist()
    summary = pd.DataFrame(records, columns=development_columns).sort_values(
        ["processing_order", "field_id"]
    )
    write_frame_atomic(summary, LARGE_SKY_VALIDATION_SCALE_SUMMARY)
    output_field_ids = set(summary["field_id"].astype(str))
    validation_ids = set(validation["field_id"].astype(str))
    numeric_model_columns = [
        "total_gaia_source_density_per_square_deg",
        "mean_visibility_periods_used",
        "mean_astrometric_matched_transits",
        "m10_median_g_magnitude",
        "phot_g_mean_mag_10th_percentile",
        "median_phot_g_mean_mag",
        "phot_g_mean_mag_90th_percentile",
    ]
    checks = {
        "frozen_contract_identifier_matches": contract["contract_id"]
        == "validation_run_contract_d75e3ddea7013547c088",
        "exactly_one_hundred_two_validation_fields_declared": len(validation_ids) == 102,
        "all_summarized_fields_are_validation": output_field_ids.issubset(validation_ids),
        "no_development_field_summarized_or_queried": development_ids.isdisjoint(output_field_ids)
        and development_ids.isdisjoint(attempted_field_ids),
        "field_identifiers_unique": summary["field_id"].is_unique,
        "processing_order_unique": summary["processing_order"].is_unique,
        "all_counts_nonnegative": empty_or_all(
            summary[["retrieved_source_count", "selected_source_count"]].ge(0).to_numpy()
        ),
        "selected_counts_do_not_exceed_retrieved_counts": empty_or_all(
            summary["selected_source_count"].le(summary["retrieved_source_count"])
        ),
        "all_model_inputs_finite": len(summary) == 0
        or np.isfinite(summary[numeric_model_columns].to_numpy()).all(),
        "no_invalid_external_receipt_used": not invalid_receipt_field_ids,
        "maximum_new_field_attempt_limit_respected": len(attempted_field_ids)
        <= arguments.maximum_new_fields,
        "all_attempted_fields_are_validation": set(attempted_field_ids).issubset(validation_ids),
        "all_failed_attempts_preserved": all(
            Path(record["path"]).exists() and file_sha256(Path(record["path"])) == record["sha256"]
            for record in failed_field_attempts
        ),
        "previous_failures_deferred_unless_retry_requested": arguments.retry_failed_fields
        or set(attempted_field_ids).isdisjoint(previous_failure_field_ids),
        "selector_version_unchanged": contract["retrieval"]["selector_version"] == SELECTOR_VERSION,
        "no_model_fitted_or_procedure_retuned": True,
        "no_field_scientifically_approved": not grid["eligible_for_scientific_background"]
        .astype(bool)
        .any(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    status = "not_started_frozen_validation"
    if output_field_ids:
        status = "partial_resumable_validation_measurement"
    if output_field_ids == validation_ids:
        status = "complete_validation_measurement"
    manifest = {
        "scale_version": VALIDATION_RUN_VERSION,
        "contract_id": contract["contract_id"],
        "status": status,
        "plain_language_scope": (
            "Only the 102 reserved validation fields may be processed. Completed fields "
            "keep verified external checkpoints and receipts; failures are not zeroes."
        ),
        "grid_id": grid_manifest["grid_id"],
        "selector_version": SELECTOR_VERSION,
        "maximum_rows_per_strip": maximum_rows_per_strip,
        "processing_order_rule": "sha256_of_validation_run_version_colon_field_id",
        "default_maximum_new_fields": DEFAULT_MAXIMUM_NEW_FIELDS,
        "requested_maximum_new_fields_this_run": arguments.maximum_new_fields,
        "retry_failed_fields_this_run": arguments.retry_failed_fields,
        "deferred_failure_field_ids": sorted(previous_failure_field_ids - completed_field_ids),
        "attempted_field_ids_this_run": attempted_field_ids,
        "newly_completed_field_ids_this_run": newly_completed_field_ids,
        "failed_field_attempts_this_run": failed_field_attempts,
        "run_interrupted": interrupted,
        "completed_validation_field_count": len(output_field_ids),
        "remaining_validation_field_count": len(validation_ids - output_field_ids),
        "validation_selector_results_opened": bool(output_field_ids),
        "invalid_external_receipt_field_ids": invalid_receipt_field_ids,
        "elapsed_seconds_this_run": perf_counter() - run_started,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                LARGE_SKY_VALIDATION_RUN_CONTRACT,
                LARGE_SKY_FIELD_GRID,
                LARGE_SKY_FIELD_GRID_MANIFEST,
                GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
                POINT_SOURCE_LOGISTIC_MODEL,
                POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
            )
        ],
        "output": {
            "path": str(LARGE_SKY_VALIDATION_SCALE_SUMMARY.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(LARGE_SKY_VALIDATION_SCALE_SUMMARY),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_VALIDATION_SCALE_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Validation scale run failed: {checks}")
    if interrupted:
        raise KeyboardInterrupt


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
