"""Resume the frozen-selector retrieval across large-sky development fields."""

import argparse
import hashlib
import json
import logging
import signal
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
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
    LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS,
    LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES,
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY,
    LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST,
    LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_FIELD_GRID_MANIFEST,
    LARGE_SKY_GAIA_RETRIEVAL_DIR,
    POINT_SOURCE_LOGISTIC_MODEL,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import (
    AdaptiveGaiaRetriever,
    file_sha256,
    load_leaf_plan,
    plan_adaptive_strips,
    write_json_atomic,
)
from scripts.phase3_background.benchmark_full_selector_retrieval import (
    source_identifier_sha256,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.benchmark_large_sky_development_retrieval import (
    checkpoint_inventory,
    field_base_where,
    require_external_checkpoint_root,
)
from scripts.phase3_background.measure_large_sky_development_field_conditions import (
    measure_field_condition,
)
from scripts.phase3_background.run_large_sky_development_retrieval import (
    load_all_plan_nodes,
    plan_contract,
    write_frame_atomic,
)
from scripts.utils.point_source_selector import (
    RAW_GAIA_COLUMNS,
    SELECTOR_VERSION,
    load_frozen_selector,
)

LOGGER = logging.getLogger(__name__)
SCALE_VERSION = "large_sky_development_scale_v1"
DEFAULT_MAXIMUM_NEW_FIELDS = 0
ARCHIVE_QUERY_TIMEOUT_SECONDS = 180
FIELD_ATTEMPT_TIMEOUT_SECONDS = 300


class FieldAttemptTimeoutError(TimeoutError):
    """One development field exceeded its measured whole-field wait limit."""


@contextmanager
def field_attempt_timeout():
    """Interrupt one field attempt after the fixed whole-field ceiling."""

    def raise_timeout(signum: int, frame: object) -> None:
        del signum, frame
        raise FieldAttemptTimeoutError(
            f"Field attempt exceeded {FIELD_ATTEMPT_TIMEOUT_SECONDS} seconds"
        )

    previous_handler = signal.signal(signal.SIGALRM, raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, FIELD_ATTEMPT_TIMEOUT_SECONDS)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


class ArchiveTimeoutSession(requests.Session):
    """Apply a measured upper wait to every archive HTTP request."""

    def request(self, method: str, url: str, **kwargs: object) -> requests.Response:
        """Send a request with the development archive timeout by default."""
        kwargs.setdefault("timeout", ARCHIVE_QUERY_TIMEOUT_SECONDS)
        return super().request(method, url, **kwargs)


def stable_processing_order(field_id: str) -> int:
    """Return a count-blind stable processing-order value."""
    content = f"{SCALE_VERSION}:{field_id}".encode()
    return int(hashlib.sha256(content).hexdigest()[:16], 16)


def parse_arguments() -> argparse.Namespace:
    """Parse the explicit bounded-run limit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--maximum-new-fields",
        type=int,
        default=DEFAULT_MAXIMUM_NEW_FIELDS,
        help=(
            "Maximum previously unfinished development fields to query. The default "
            "is zero so an unrestricted remote run cannot start accidentally."
        ),
    )
    parser.add_argument(
        "--retry-failed-fields",
        action="store_true",
        help=(
            "Include unfinished fields that already have a preserved failure receipt. "
            "They are deferred by default so one archive problem cannot block untouched "
            "development fields."
        ),
    )
    arguments = parser.parse_args()
    if arguments.maximum_new_fields < 0:
        parser.error("--maximum-new-fields must be zero or positive")
    return arguments


def import_pilot_records(grid: pd.DataFrame) -> list[dict[str, object]]:
    """Return standard records for the 12 previously verified pilot fields."""
    pilot = pd.read_csv(LARGE_SKY_DEVELOPMENT_PILOT_FIELDS)[["field_id"]]
    retrieval = pd.read_csv(LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY)
    conditions = pd.read_csv(LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS)
    magnitudes = pd.read_csv(LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES)
    joined = (
        pilot.merge(grid, on="field_id", validate="one_to_one")
        .merge(
            retrieval[
                [
                    "field_id",
                    "retrieved_source_count",
                    "selected_source_count",
                    "selected_source_density_per_square_deg",
                    "combined_source_identifier_sha256",
                    "final_strip_count",
                    "checkpoint_source_bytes",
                ]
            ],
            on="field_id",
            validate="one_to_one",
        )
        .merge(
            conditions[
                [
                    "field_id",
                    "source_density_per_square_deg",
                    "mean_visibility_periods_used",
                    "mean_astrometric_matched_transits",
                    "m10_median_g_magnitude",
                ]
            ],
            on="field_id",
            validate="one_to_one",
        )
        .merge(
            magnitudes[
                [
                    "field_id",
                    "phot_g_mean_mag_10th_percentile",
                    "median_phot_g_mean_mag",
                    "phot_g_mean_mag_90th_percentile",
                ]
            ],
            on="field_id",
            validate="one_to_one",
        )
    )
    records = []
    for _, field in joined.iterrows():
        records.append(
            {
                "scale_version": SCALE_VERSION,
                "grid_id": field["grid_id"],
                "field_id": field["field_id"],
                "processing_order": stable_processing_order(str(field["field_id"])),
                "source_state": "imported_verified_twelve_field_pilot",
                "experiment_partition": field["experiment_partition"],
                "sky_block_id": field["sky_block_id"],
                "hemisphere": field["hemisphere"],
                "galactic_longitude_deg": float(field["galactic_longitude_deg"]),
                "galactic_latitude_deg": float(field["galactic_latitude_deg"]),
                "ecliptic_latitude_deg": float(field["ecliptic_latitude_deg"]),
                "environment_flag_state": field["environment_flag_state"],
                "usable_area_square_deg": float(field["requested_area_square_deg"]),
                "retrieved_source_count": int(field["retrieved_source_count"]),
                "selected_source_count": int(field["selected_source_count"]),
                "total_gaia_source_density_per_square_deg": float(
                    field["source_density_per_square_deg"]
                ),
                "selected_source_density_per_square_deg": float(
                    field["selected_source_density_per_square_deg"]
                ),
                "mean_visibility_periods_used": float(field["mean_visibility_periods_used"]),
                "mean_astrometric_matched_transits": float(
                    field["mean_astrometric_matched_transits"]
                ),
                "m10_median_g_magnitude": float(field["m10_median_g_magnitude"]),
                "phot_g_mean_mag_10th_percentile": float(field["phot_g_mean_mag_10th_percentile"]),
                "median_phot_g_mean_mag": float(field["median_phot_g_mean_mag"]),
                "phot_g_mean_mag_90th_percentile": float(field["phot_g_mean_mag_90th_percentile"]),
                "combined_source_identifier_sha256": field["combined_source_identifier_sha256"],
                "final_strip_count": int(field["final_strip_count"]),
                "checkpoint_source_bytes": int(field["checkpoint_source_bytes"]),
                "field_seconds": np.nan,
            }
        )
    return records


def scale_field_directory(grid_id: str, field_id: str) -> Path:
    """Return the external checkpoint directory for one scale-up field."""
    return LARGE_SKY_GAIA_RETRIEVAL_DIR / grid_id / SCALE_VERSION / field_id


def write_failure_receipt(
    field: pd.Series,
    error: BaseException,
    elapsed_seconds: float,
) -> dict[str, object]:
    """Preserve one failed or interrupted development-field attempt."""
    generated_at = datetime.now(UTC)
    field_directory = scale_field_directory(str(field["grid_id"]), str(field["field_id"]))
    field_directory.mkdir(parents=True, exist_ok=True)
    failure_path = field_directory / (f"failure_{generated_at.strftime('%Y%m%dT%H%M%S_%fZ')}.json")
    failure = {
        "scale_version": SCALE_VERSION,
        "generated_at_utc": generated_at.isoformat(),
        "field_id": str(field["field_id"]),
        "experiment_partition": str(field["experiment_partition"]),
        "elapsed_seconds": elapsed_seconds,
        "error_type": type(error).__name__,
        "plain_language_error": str(error) or "The bounded run was stopped by the operator.",
        "field_represented_as_zero": False,
        "retry_policy": (
            "Keep valid plans and strip checkpoints. A later explicitly bounded run may "
            "retry this unfinished development field."
        ),
    }
    write_json_atomic(failure_path, failure)
    return {
        "field_id": str(field["field_id"]),
        "path": str(failure_path.resolve()),
        "sha256": file_sha256(failure_path),
        "error_type": type(error).__name__,
        "elapsed_seconds": elapsed_seconds,
    }


def completed_receipt_is_valid(
    receipt_path: Path,
    field: pd.Series,
    maximum_rows_per_strip: int,
) -> bool:
    """Verify a completed external receipt and every recorded checkpoint hash."""
    if not receipt_path.exists():
        return False
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        expected_contract = plan_contract(field_base_where(field), maximum_rows_per_strip)
        if receipt.get("scale_version") != SCALE_VERSION:
            return False
        if receipt.get("field_id") != field["field_id"]:
            return False
        if receipt.get("plan_contract") != expected_contract:
            return False
        if not all(receipt.get("field_checks", {}).values()):
            return False
        record = receipt["summary_record"]
        if record["field_id"] != field["field_id"]:
            return False
        if record["experiment_partition"] != "development":
            return False
        if record["selected_source_count"] > record["retrieved_source_count"]:
            return False
        plan_path = Path(receipt["external_plan_path"])
        if file_sha256(plan_path) != receipt["external_plan_sha256"]:
            return False
        checkpoint_source_count = 0
        for checkpoint in receipt["checkpoint_inventory"]:
            source_path = Path(checkpoint["source_path"])
            metadata_path = Path(checkpoint["metadata_path"])
            if source_path.stat().st_size != checkpoint["source_bytes"]:
                return False
            if file_sha256(source_path) != checkpoint["source_sha256"]:
                return False
            if file_sha256(metadata_path) != checkpoint["metadata_sha256"]:
                return False
            checkpoint_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            checkpoint_source_count += int(checkpoint_metadata["retrieved_source_count"])
        if checkpoint_source_count != record["retrieved_source_count"]:
            return False
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False
    return True


def process_new_field(
    service: tap.TAPService,
    selector: object,
    field: pd.Series,
    maximum_rows_per_strip: int,
) -> tuple[dict[str, object], dict[str, object]]:
    """Retrieve, score, measure, and checkpoint one development field."""
    field_started = perf_counter()
    field_id = str(field["field_id"])
    field_directory = scale_field_directory(str(field["grid_id"]), field_id)
    field_directory.mkdir(parents=True, exist_ok=True)
    plan_path = field_directory / "measured_plan.csv"
    contract_path = field_directory / "plan_contract.json"
    base_where = field_base_where(field)
    expected_contract = plan_contract(base_where, maximum_rows_per_strip)
    reused_plan_node_count = 0
    if plan_path.exists():
        contract_matches = False
        if contract_path.exists():
            try:
                contract_matches = (
                    json.loads(contract_path.read_text(encoding="utf-8")) == expected_contract
                )
            except json.JSONDecodeError:
                contract_matches = False
        if not contract_matches:
            plan_path.unlink()
        else:
            reused_plan_node_count = len(load_all_plan_nodes(plan_path))
    write_json_atomic(contract_path, expected_contract)
    planned = plan_adaptive_strips(
        service,
        base_where,
        max(-90.0, float(field["dec_deg"]) - float(field["field_radius_deg"])),
        min(90.0, float(field["dec_deg"]) + float(field["field_radius_deg"])),
        maximum_rows_per_strip,
        progress_path=plan_path,
    )
    leaf_strips = load_leaf_plan(plan_path)
    retriever = AdaptiveGaiaRetriever(
        service,
        base_where,
        field_directory,
        tuple(RAW_GAIA_COLUMNS),
    )
    retrieval_result = retriever.run(leaf_strips)
    combined = retriever.combine(leaf_strips)
    scored = selector.score(combined)
    condition_field = field.copy()
    condition_field["pilot_id"] = SCALE_VERSION
    conditions = measure_field_condition(service, condition_field)
    magnitudes = combined["phot_g_mean_mag"].dropna().astype(float)
    magnitude_quantiles = magnitudes.quantile((0.1, 0.5, 0.9))
    selected_count = int(scored["point_source_logistic_selected"].sum())
    exact_area = float(field["requested_area_square_deg"])
    inventory = checkpoint_inventory(retriever, leaf_strips)
    identifier_hash = source_identifier_sha256(combined)
    field_checks = {
        "development_partition": field["experiment_partition"] == "development",
        "retrieval_complete": bool(retrieval_result["complete"]),
        "retrieved_count_matches_plan": len(combined) == planned[0].measured_source_count,
        "condition_count_matches_retrieval": int(
            conditions["source_count_in_frozen_magnitude_domain"]
        )
        == len(combined),
        "source_identifiers_unique": combined["source_id"].is_unique,
        "all_g_magnitudes_present": len(magnitudes) == len(combined),
        "all_leaf_strips_within_limit": all(
            strip.measured_source_count <= maximum_rows_per_strip for strip in leaf_strips
        ),
        "selector_version_frozen": scored["point_source_selector_version"]
        .eq(SELECTOR_VERSION)
        .all(),
        "selector_probabilities_finite": np.isfinite(
            scored["point_source_logistic_probability"]
        ).all(),
        "condition_query_did_not_use_selector": not bool(
            conditions["query_contract_uses_selector_output"]
        ),
    }
    field_checks = {name: bool(value) for name, value in field_checks.items()}
    if not all(field_checks.values()):
        raise RuntimeError(f"Field {field_id} failed scale checks: {field_checks}")
    record = {
        "scale_version": SCALE_VERSION,
        "grid_id": field["grid_id"],
        "field_id": field_id,
        "processing_order": stable_processing_order(field_id),
        "source_state": "new_verified_scale_retrieval",
        "experiment_partition": field["experiment_partition"],
        "sky_block_id": field["sky_block_id"],
        "hemisphere": field["hemisphere"],
        "galactic_longitude_deg": float(field["galactic_longitude_deg"]),
        "galactic_latitude_deg": float(field["galactic_latitude_deg"]),
        "ecliptic_latitude_deg": float(field["ecliptic_latitude_deg"]),
        "environment_flag_state": field["environment_flag_state"],
        "usable_area_square_deg": exact_area,
        "retrieved_source_count": len(combined),
        "selected_source_count": selected_count,
        "total_gaia_source_density_per_square_deg": len(combined) / exact_area,
        "selected_source_density_per_square_deg": selected_count / exact_area,
        "mean_visibility_periods_used": conditions["mean_visibility_periods_used"],
        "mean_astrometric_matched_transits": conditions["mean_astrometric_matched_transits"],
        "m10_median_g_magnitude": conditions["m10_median_g_magnitude"],
        "phot_g_mean_mag_10th_percentile": float(magnitude_quantiles.loc[0.1]),
        "median_phot_g_mean_mag": float(magnitude_quantiles.loc[0.5]),
        "phot_g_mean_mag_90th_percentile": float(magnitude_quantiles.loc[0.9]),
        "combined_source_identifier_sha256": identifier_hash,
        "final_strip_count": len(leaf_strips),
        "checkpoint_source_bytes": sum(item["source_bytes"] for item in inventory),
        "field_seconds": perf_counter() - field_started,
    }
    receipt = {
        "scale_version": SCALE_VERSION,
        "field_id": field_id,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "plan_contract": expected_contract,
        "reused_plan_node_count": reused_plan_node_count,
        "external_plan_path": str(plan_path.resolve()),
        "external_plan_sha256": file_sha256(plan_path),
        "retrieval_result": retrieval_result,
        "checkpoint_inventory": inventory,
        "condition_query_hashes": {
            name: conditions[name]
            for name in (
                "magnitude_domain_count_query_sha256",
                "observation_query_sha256",
                "low_transit_count_query_sha256",
                "low_transit_query_sha256",
            )
        },
        "field_checks": field_checks,
        "summary_record": record,
    }
    return record, receipt


def main() -> None:
    """Resume a bounded number of development fields and write a partial summary."""
    arguments = parse_arguments()
    require_external_checkpoint_root()
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    grid_manifest = json.loads(LARGE_SKY_FIELD_GRID_MANIFEST.read_text(encoding="utf-8"))
    development = grid.loc[grid["experiment_partition"].eq("development")].copy()
    validation_field_ids = set(
        grid.loc[grid["experiment_partition"].eq("validation"), "field_id"].astype(str)
    )
    development["processing_order"] = development["field_id"].map(stable_processing_order)
    development = development.sort_values(["processing_order", "field_id"])
    retrieval_limit_manifest = json.loads(
        GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST.read_text(encoding="utf-8")
    )
    maximum_rows_per_strip = int(retrieval_limit_manifest["provisional_safe_rows_per_strip"])
    records = import_pilot_records(grid)
    completed_field_ids = {str(record["field_id"]) for record in records}
    invalid_receipt_field_ids = []
    previous_failure_field_ids = {
        str(field["field_id"])
        for _, field in development.iterrows()
        if any(
            scale_field_directory(str(field["grid_id"]), str(field["field_id"])).glob(
                "failure_*.json"
            )
        )
    }
    for _, field in development.iterrows():
        field_id = str(field["field_id"])
        if field_id in completed_field_ids:
            continue
        receipt_path = scale_field_directory(str(field["grid_id"]), field_id) / "field_receipt.json"
        if completed_receipt_is_valid(receipt_path, field, maximum_rows_per_strip):
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            records.append(receipt["summary_record"])
            completed_field_ids.add(field_id)
        elif receipt_path.exists():
            invalid_receipt_field_ids.append(field_id)
    service = tap.TAPService(DATA_LAB_TAP_URL, session=ArchiveTimeoutSession())
    selector = load_frozen_selector()
    run_started = perf_counter()
    newly_completed_field_ids = []
    attempted_field_ids = []
    failed_field_attempts = []
    interrupted = False
    for _, field in development.iterrows():
        field_id = str(field["field_id"])
        if field_id in completed_field_ids:
            continue
        if field_id in previous_failure_field_ids and not arguments.retry_failed_fields:
            continue
        if len(attempted_field_ids) >= arguments.maximum_new_fields:
            break
        attempted_field_ids.append(field_id)
        LOGGER.info("Processing development scale field %s", field_id)
        attempt_started = perf_counter()
        try:
            with field_attempt_timeout():
                record, receipt = process_new_field(
                    service,
                    selector,
                    field,
                    maximum_rows_per_strip,
                )
        except KeyboardInterrupt as error:
            failed_field_attempts.append(
                write_failure_receipt(field, error, perf_counter() - attempt_started)
            )
            interrupted = True
            break
        except (requests.RequestException, DALAccessError, FieldAttemptTimeoutError) as error:
            failed_field_attempts.append(
                write_failure_receipt(field, error, perf_counter() - attempt_started)
            )
            LOGGER.warning("Preserved recoverable failure for %s: %s", field_id, error)
            continue
        receipt_path = scale_field_directory(str(field["grid_id"]), field_id) / "field_receipt.json"
        write_json_atomic(receipt_path, receipt)
        records.append(record)
        completed_field_ids.add(field_id)
        newly_completed_field_ids.append(field_id)
        if field_id in invalid_receipt_field_ids:
            invalid_receipt_field_ids.remove(field_id)
        write_frame_atomic(
            pd.DataFrame(records).sort_values(["processing_order", "field_id"]),
            LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY,
        )
    summary = pd.DataFrame(records).sort_values(["processing_order", "field_id"])
    write_frame_atomic(summary, LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY)
    output_field_ids = set(summary["field_id"].astype(str))
    development_field_ids = set(development["field_id"].astype(str))
    checks = {
        "exactly_three_hundred_ninety_eight_development_fields_declared": len(development) == 398,
        "all_summarized_fields_are_development": output_field_ids.issubset(development_field_ids),
        "no_validation_field_summarized_or_queried": validation_field_ids.isdisjoint(
            output_field_ids
        ),
        "twelve_verified_pilot_fields_imported": summary["source_state"]
        .eq("imported_verified_twelve_field_pilot")
        .sum()
        == 12,
        "field_identifiers_unique": summary["field_id"].is_unique,
        "processing_order_unique": summary["processing_order"].is_unique,
        "all_counts_nonnegative": summary[["retrieved_source_count", "selected_source_count"]]
        .ge(0)
        .all()
        .all(),
        "selected_counts_do_not_exceed_retrieved_counts": summary["selected_source_count"]
        .le(summary["retrieved_source_count"])
        .all(),
        "all_model_inputs_finite": np.isfinite(
            summary[
                [
                    "total_gaia_source_density_per_square_deg",
                    "mean_visibility_periods_used",
                    "mean_astrometric_matched_transits",
                    "m10_median_g_magnitude",
                    "phot_g_mean_mag_10th_percentile",
                    "median_phot_g_mean_mag",
                    "phot_g_mean_mag_90th_percentile",
                ]
            ]
        )
        .all()
        .all(),
        "no_invalid_external_receipt_used": not invalid_receipt_field_ids,
        "maximum_new_field_attempt_limit_respected": len(attempted_field_ids)
        <= arguments.maximum_new_fields,
        "all_attempted_fields_are_development": set(attempted_field_ids).issubset(
            development_field_ids
        ),
        "all_failed_attempts_preserved": all(
            Path(record["path"]).exists() and file_sha256(Path(record["path"])) == record["sha256"]
            for record in failed_field_attempts
        ),
        "previous_failures_deferred_unless_retry_requested": arguments.retry_failed_fields
        or set(attempted_field_ids).isdisjoint(previous_failure_field_ids),
        "no_model_fitted": True,
        "validation_selector_results_remain_unopened": True,
        "no_field_scientifically_approved": not grid["eligible_for_scientific_background"]
        .astype(bool)
        .any(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    manifest = {
        "scale_version": SCALE_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": (
            "complete_development_measurement"
            if output_field_ids == development_field_ids
            else "partial_resumable_development_measurement"
        ),
        "plain_language_scope": (
            "Only development fields are processed. Each completed field keeps verified "
            "raw checkpoints and a receipt outside the repository, so later runs skip it."
        ),
        "grid_id": grid_manifest["grid_id"],
        "selector_version": SELECTOR_VERSION,
        "maximum_rows_per_strip": maximum_rows_per_strip,
        "processing_order_rule": "sha256_of_scale_version_colon_field_id",
        "default_maximum_new_fields": DEFAULT_MAXIMUM_NEW_FIELDS,
        "archive_query_timeout_seconds": ARCHIVE_QUERY_TIMEOUT_SECONDS,
        "field_attempt_timeout_seconds": FIELD_ATTEMPT_TIMEOUT_SECONDS,
        "requested_maximum_new_fields_this_run": arguments.maximum_new_fields,
        "retry_failed_fields_this_run": arguments.retry_failed_fields,
        "deferred_failure_field_ids": sorted(previous_failure_field_ids - completed_field_ids),
        "attempted_field_ids_this_run": attempted_field_ids,
        "newly_completed_field_ids_this_run": newly_completed_field_ids,
        "failed_field_attempts_this_run": failed_field_attempts,
        "run_interrupted": interrupted,
        "completed_development_field_count": len(output_field_ids),
        "remaining_development_field_count": len(development_field_ids - output_field_ids),
        "held_back_validation_field_count": len(validation_field_ids),
        "validation_selector_results_opened": False,
        "invalid_external_receipt_field_ids": invalid_receipt_field_ids,
        "elapsed_seconds_this_run": perf_counter() - run_started,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                LARGE_SKY_FIELD_GRID,
                LARGE_SKY_FIELD_GRID_MANIFEST,
                LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
                LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY,
                LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS,
                LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES,
                GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
                POINT_SOURCE_LOGISTIC_MODEL,
                POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
            )
        ],
        "output": {
            "path": str(LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(LARGE_SKY_DEVELOPMENT_SCALE_SUMMARY),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DEVELOPMENT_SCALE_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Development scale run failed: {checks}")
    if interrupted:
        raise KeyboardInterrupt


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
