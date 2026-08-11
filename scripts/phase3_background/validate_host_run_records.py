"""Build and validate permanent per-galaxy receipts for bounded Gaia runs."""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_HOSTS,
    GAIA_FULL_COLUMN_MULTIFIELD_PLAN,
    GAIA_FULL_COLUMN_MULTIFIELD_RETRIEVAL,
    GAIA_FULL_COLUMN_MULTIFIELD_VALIDATION,
    HOST_RUN_RECORD_INDEX,
    HOST_RUN_RECORD_VALIDATION,
    HOST_RUN_RECORDS_DIR,
    PROJECT_ROOT,
    RADIAL_RING_AREA_ACCOUNTING,
    RADIAL_RING_AREA_ACCOUNTING_MANIFEST,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256
from scripts.phase3_background.host_run_record import (
    content_sha256,
    host_record_path,
    host_run_identifier,
    run_identifier,
    write_immutable_json,
)
from scripts.utils.point_source_selector import MAXIMUM_G_MAGNITUDE, MINIMUM_G_MAGNITUDE

RECEIPT_SCHEMA_VERSION = "host_run_record_v1"
COMPLETE_AREA_SCENARIO = "measured_complete_gaia_policy"
PARTIAL_AREA_SCENARIO = "controlled_partial_gaia_policy"
PARTIAL_TEST_HOST_NAME = "MESSIER 060"
AREA_IDENTITY_TOLERANCE_SQUARE_DEG = 1e-8
RING_AREA_COLUMNS = (
    "requested_area_square_deg",
    "successfully_queried_area_square_deg",
    "masked_area_square_deg",
    "missing_area_square_deg",
    "usable_area_square_deg",
    "queried_integration_error_square_deg",
    "masked_integration_error_square_deg",
)


def provenance_entry(path: Path) -> dict[str, str]:
    """Return a repository-relative path and file hash."""
    return {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}


def ring_receipts(rows: pd.DataFrame) -> list[dict[str, object]]:
    """Convert validated ring rows into plain JSON-compatible receipt entries."""
    receipts = []
    for _, row in rows.sort_values("inner_radius_deg").iterrows():
        receipt = {
            "ring_id": str(row["ring_id"]),
            "inner_radius_deg": float(row["inner_radius_deg"]),
            "outer_radius_deg": float(row["outer_radius_deg"]),
            "inference_role": str(row["inference_role"]),
            "area_status": str(row["area_status"]),
        }
        receipt.update({column: float(row[column]) for column in RING_AREA_COLUMNS})
        receipts.append(receipt)
    return receipts


def make_host_record(
    run_id: str,
    run_configuration: dict[str, object],
    source_run_generated_at_utc: str,
    host_name: str,
    host: pd.Series,
    retrieval: dict[str, object],
    rings: list[dict[str, object]],
    status: str,
    failures: list[dict[str, str]],
    is_controlled_fixture: bool,
) -> dict[str, object]:
    """Return one complete, explicit per-galaxy receipt."""
    host_ra_deg = float(host["ra"])
    host_dec_deg = float(host["dec"])
    host_run_id = host_run_identifier(run_id, host_name, host_ra_deg, host_dec_deg)
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "run_id": run_id,
        "host_run_id": host_run_id,
        "recorded_at_utc": source_run_generated_at_utc,
        "purpose": "bounded_retrieval_and_area_validation_not_scientific_search",
        "is_controlled_fixture": is_controlled_fixture,
        "host": {
            "name": host_name,
            "ra_deg": host_ra_deg,
            "dec_deg": host_dec_deg,
        },
        "status": status,
        "failures": failures,
        "run_configuration": run_configuration,
        "run_configuration_sha256": content_sha256(run_configuration),
        "retrieval": retrieval,
        "radial_rings": rings,
    }


def main() -> None:
    """Create three completed receipts and one controlled partial receipt."""
    started = perf_counter()
    hosts = pd.read_csv(BACKGROUND_REVIEW_HOSTS).set_index("objname")
    plan = pd.read_csv(GAIA_FULL_COLUMN_MULTIFIELD_PLAN)
    retrieval = pd.read_csv(GAIA_FULL_COLUMN_MULTIFIELD_RETRIEVAL).set_index("host_name")
    areas = pd.read_csv(RADIAL_RING_AREA_ACCOUNTING)
    retrieval_manifest = json.loads(
        GAIA_FULL_COLUMN_MULTIFIELD_VALIDATION.read_text(encoding="utf-8")
    )
    area_manifest = json.loads(RADIAL_RING_AREA_ACCOUNTING_MANIFEST.read_text(encoding="utf-8"))
    input_paths = (
        BACKGROUND_REVIEW_HOSTS,
        GAIA_FULL_COLUMN_MULTIFIELD_PLAN,
        GAIA_FULL_COLUMN_MULTIFIELD_RETRIEVAL,
        GAIA_FULL_COLUMN_MULTIFIELD_VALIDATION,
        RADIAL_RING_AREA_ACCOUNTING,
        RADIAL_RING_AREA_ACCOUNTING_MANIFEST,
    )
    input_provenance = [provenance_entry(path) for path in input_paths]
    run_configuration = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "purpose": "three_field_complete_performance_validation",
        "receipt_embeds_complete_run_configuration": True,
        "gaia_release": retrieval_manifest["data_source"]["catalog_release"],
        "gaia_table": retrieval_manifest["data_source"]["table"],
        "query_service": retrieval_manifest["data_source"]["query_service"],
        "query_contract": {
            "geometry": "host_centered_performance_test_circle_partitioned_by_declination",
            "minimum_g_magnitude": MINIMUM_G_MAGNITUDE,
            "maximum_g_magnitude": MAXIMUM_G_MAGNITUDE,
            "selector_applied_after_retrieval": True,
        },
        "selector_version": retrieval_manifest["selector_version"],
        "raw_gaia_columns": retrieval_manifest["raw_selector_columns"],
        "maximum_rows_per_strip": retrieval_manifest["approved_rows_per_strip"],
        "gaia_area_policy": area_manifest["gaia_area_policy"],
        "ring_view": {
            "status": "performance_test_fractions_not_scientific_aperture",
            "radius_fractions": area_manifest["test_ring_radius_fractions"],
        },
        "inputs": input_provenance,
    }
    complete_run_id = run_identifier(run_configuration)
    records: list[dict[str, object]] = []
    write_dispositions = []
    for host_name, retrieval_row in retrieval.iterrows():
        host_plan = plan.loc[plan["host_name"].eq(host_name) & plan["is_leaf"].astype(bool)]
        completed_strip_ids = host_plan["strip_id"].astype(str).tolist()
        host_areas = areas.loc[
            areas["scenario"].eq(COMPLETE_AREA_SCENARIO) & areas["host_name"].eq(host_name)
        ]
        retrieval_receipt = {
            "status": "complete",
            "test_radius_deg": float(retrieval_row["test_radius_deg"]),
            "expected_strip_count": int(retrieval_row["final_strip_count"]),
            "completed_strip_ids": completed_strip_ids,
            "measured_source_count": int(retrieval_row["available_rows"]),
            "combined_source_count": int(retrieval_row["combined_rows"]),
            "combined_source_identifier_sha256": str(retrieval_row["combined_identifier_sha256"]),
            "reference_source_identifier_sha256": str(retrieval_row["reference_identifier_sha256"]),
            "base_where_sha256": str(retrieval_row["base_where_sha256"]),
            "reference_query_sha256": str(retrieval_row["reference_query_sha256"]),
            "checkpoint_files_retained": False,
            "saved_csv_bytes": int(retrieval_row["checkpoint_csv_bytes"]),
            "maximum_saved_strip_bytes": int(retrieval_row["maximum_checkpoint_csv_bytes"]),
            "elapsed_seconds": float(retrieval_row["field_elapsed_seconds"]),
        }
        record = make_host_record(
            complete_run_id,
            run_configuration,
            retrieval_manifest["generated_at_utc"],
            host_name,
            hosts.loc[host_name],
            retrieval_receipt,
            ring_receipts(host_areas),
            "complete",
            [],
            False,
        )
        path = host_record_path(
            HOST_RUN_RECORDS_DIR, complete_run_id, host_name, str(record["host_run_id"])
        )
        first_disposition = write_immutable_json(path, record)
        second_disposition = write_immutable_json(path, record)
        write_dispositions.append((first_disposition, second_disposition))
        records.append({"record": record, "path": path})

    partial_configuration = {
        **run_configuration,
        "purpose": "controlled_partial_receipt_validation",
        "controlled_completed_strip_count": 1,
    }
    partial_run_id = run_identifier(partial_configuration)
    partial_host = hosts.loc[PARTIAL_TEST_HOST_NAME]
    partial_plan = plan.loc[
        plan["host_name"].eq(PARTIAL_TEST_HOST_NAME) & plan["is_leaf"].astype(bool)
    ]
    partial_completed_strip = partial_plan.iloc[0]
    partial_areas = areas.loc[
        areas["scenario"].eq(PARTIAL_AREA_SCENARIO) & areas["host_name"].eq(PARTIAL_TEST_HOST_NAME)
    ]
    partial_retrieval = {
        "status": "partial",
        "test_radius_deg": float(retrieval.loc[PARTIAL_TEST_HOST_NAME, "test_radius_deg"]),
        "expected_strip_count": len(partial_plan),
        "completed_strip_ids": [str(partial_completed_strip["strip_id"])],
        "measured_source_count": int(retrieval.loc[PARTIAL_TEST_HOST_NAME, "available_rows"]),
        "combined_source_count": None,
        "combined_source_identifier_sha256": None,
        "reference_source_identifier_sha256": str(
            retrieval.loc[PARTIAL_TEST_HOST_NAME, "reference_identifier_sha256"]
        ),
        "base_where_sha256": str(retrieval.loc[PARTIAL_TEST_HOST_NAME, "base_where_sha256"]),
        "reference_query_sha256": str(
            retrieval.loc[PARTIAL_TEST_HOST_NAME, "reference_query_sha256"]
        ),
        "checkpoint_files_retained": False,
        "saved_csv_bytes": None,
        "maximum_saved_strip_bytes": None,
        "elapsed_seconds": None,
    }
    partial_record = make_host_record(
        partial_run_id,
        partial_configuration,
        retrieval_manifest["generated_at_utc"],
        PARTIAL_TEST_HOST_NAME,
        partial_host,
        partial_retrieval,
        ring_receipts(partial_areas),
        "partial",
        [
            {
                "failure_code": "incomplete_retrieval",
                "plain_language": "Only one of two required sky strips has a verified file.",
            }
        ],
        True,
    )
    partial_path = host_record_path(
        HOST_RUN_RECORDS_DIR,
        partial_run_id,
        PARTIAL_TEST_HOST_NAME,
        str(partial_record["host_run_id"]),
    )
    partial_first_disposition = write_immutable_json(partial_path, partial_record)
    partial_second_disposition = write_immutable_json(partial_path, partial_record)
    write_dispositions.append((partial_first_disposition, partial_second_disposition))
    records.append({"record": partial_record, "path": partial_path})

    with TemporaryDirectory(prefix="bubbletea_immutable_receipt_") as temporary_directory:
        conflict_path = Path(temporary_directory) / "receipt.json"
        write_immutable_json(conflict_path, records[0]["record"])
        changed_record = {**records[0]["record"], "status": "changed_after_creation"}
        conflict_rejected = False
        try:
            write_immutable_json(conflict_path, changed_record)
        except FileExistsError:
            conflict_rejected = True

    index_rows = []
    for item in records:
        record = item["record"]
        path = item["path"]
        rings = record["radial_rings"]
        index_rows.append(
            {
                "run_id": record["run_id"],
                "host_run_id": record["host_run_id"],
                "host_name": record["host"]["name"],
                "status": record["status"],
                "is_controlled_fixture": record["is_controlled_fixture"],
                "expected_strip_count": record["retrieval"]["expected_strip_count"],
                "completed_strip_count": len(record["retrieval"]["completed_strip_ids"]),
                "ring_count": len(rings),
                "requested_area_square_deg": sum(
                    ring["requested_area_square_deg"] for ring in rings
                ),
                "successfully_queried_area_square_deg": sum(
                    ring["successfully_queried_area_square_deg"] for ring in rings
                ),
                "missing_area_square_deg": sum(ring["missing_area_square_deg"] for ring in rings),
                "usable_area_square_deg": sum(ring["usable_area_square_deg"] for ring in rings),
                "record_path": str(path.relative_to(PROJECT_ROOT)),
                "record_file_sha256": file_sha256(path),
            }
        )
    index = pd.DataFrame(index_rows)
    HOST_RUN_RECORD_INDEX.parent.mkdir(parents=True, exist_ok=True)
    temporary_index_path = HOST_RUN_RECORD_INDEX.with_suffix(".csv.tmp")
    index.to_csv(temporary_index_path, index=False)
    temporary_index_path.replace(HOST_RUN_RECORD_INDEX)

    complete_records = [
        item["record"] for item in records if not item["record"]["is_controlled_fixture"]
    ]
    all_rings = [ring for item in records for ring in item["record"]["radial_rings"]]
    checks = {
        "three_complete_host_receipts": len(complete_records) == 3
        and all(record["status"] == "complete" for record in complete_records),
        "complete_receipts_share_one_run_identifier": len(
            {record["run_id"] for record in complete_records}
        )
        == 1,
        "every_host_receipt_identifier_unique": len(
            {item["record"]["host_run_id"] for item in records}
        )
        == len(records),
        "stable_identical_write_reused": all(
            second == "existing_identical" for _, second in write_dispositions
        ),
        "different_content_cannot_overwrite_receipt": conflict_rejected,
        "no_temporary_files_remain": not list(HOST_RUN_RECORDS_DIR.rglob("*.tmp")),
        "record_files_match_index_hashes": all(
            file_sha256(PROJECT_ROOT / row["record_path"]) == row["record_file_sha256"]
            for _, row in index.iterrows()
        ),
        "every_receipt_embeds_matching_configuration": all(
            content_sha256(item["record"]["run_configuration"])
            == item["record"]["run_configuration_sha256"]
            for item in records
        ),
        "every_receipt_preserves_query_fingerprints": all(
            bool(item["record"]["retrieval"]["base_where_sha256"])
            and bool(item["record"]["retrieval"]["reference_query_sha256"])
            for item in records
        ),
        "four_rings_in_every_receipt": all(
            len(item["record"]["radial_rings"]) == 4 for item in records
        ),
        "gaia_usable_area_equals_queried_area": all(
            abs(ring["usable_area_square_deg"] - ring["successfully_queried_area_square_deg"])
            <= AREA_IDENTITY_TOLERANCE_SQUARE_DEG
            for ring in all_rings
        ),
        "queried_plus_missing_equals_requested": all(
            abs(
                ring["successfully_queried_area_square_deg"]
                + ring["missing_area_square_deg"]
                - ring["requested_area_square_deg"]
            )
            <= AREA_IDENTITY_TOLERANCE_SQUARE_DEG
            for ring in all_rings
        ),
        "complete_receipts_have_no_failures": all(
            not record["failures"] for record in complete_records
        ),
        "partial_receipt_has_plain_failure": partial_record["status"] == "partial"
        and partial_record["failures"][0]["failure_code"] == "incomplete_retrieval"
        and bool(partial_record["failures"][0]["plain_language"]),
        "partial_receipt_preserves_missing_area": sum(
            ring["missing_area_square_deg"] for ring in partial_record["radial_rings"]
        )
        > 0,
        "partial_receipt_has_separate_run_identifier": partial_run_id != complete_run_id,
        "complete_retrieval_counts_and_hashes_preserved": all(
            record["retrieval"]["combined_source_count"]
            == record["retrieval"]["measured_source_count"]
            and record["retrieval"]["combined_source_identifier_sha256"]
            == record["retrieval"]["reference_source_identifier_sha256"]
            for record in complete_records
        ),
        "complete_run_index_contains_only_three_hosts": len(
            index.loc[index["run_id"].eq(complete_run_id)]
        )
        == 3,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    validation = {
        "validation_version": "host_run_record_validation_v1",
        "plain_language_name": "per_galaxy_analysis_receipt",
        "complete_run_id": complete_run_id,
        "controlled_partial_run_id": partial_run_id,
        "receipt_schema_version": RECEIPT_SCHEMA_VERSION,
        "input_provenance": input_provenance,
        "receipt_count": len(records),
        "complete_receipt_count": len(complete_records),
        "controlled_partial_receipt_count": 1,
        "write_dispositions": [
            {"first_write": first, "repeat_write": second} for first, second in write_dispositions
        ],
        "elapsed_seconds": perf_counter() - started,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    HOST_RUN_RECORD_VALIDATION.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    if not all(checks.values()):
        raise RuntimeError(f"Host-run receipt validation failed: {checks}")


if __name__ == "__main__":
    main()
