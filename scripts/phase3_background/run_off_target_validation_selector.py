"""Open the held-back off-target fields once under the frozen procedure."""

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY,
    OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY_MANIFEST,
    OFF_TARGET_DEVELOPMENT_MANIFEST,
    OFF_TARGET_FIELD_SPLIT,
    OFF_TARGET_FIELD_SPLIT_MANIFEST,
    OFF_TARGET_VALIDATION_FROZEN_SUMMARY,
    OFF_TARGET_VALIDATION_MANIFEST,
    OFF_TARGET_VALIDATION_SOURCES,
    OFF_TARGET_VALIDATION_SUMMARY,
    POINT_SOURCE_LOGISTIC_MODEL,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.freeze_off_target_development_summary import (
    CONFIDENCE_LEVELS,
    summary_record,
)
from scripts.phase3_background.run_off_target_development_selector import retrieve_field
from scripts.utils.point_source_selector import (
    MAXIMUM_G_MAGNITUDE,
    MINIMUM_G_MAGNITUDE,
    RAW_GAIA_COLUMNS,
    SELECTOR_VERSION,
    load_frozen_selector,
)

LOGGER = logging.getLogger(__name__)
DEVELOPMENT_PARTITION = "development"
VALIDATION_PARTITION = "validation"
VALIDATION_SUMMARY_VERSION = "off_target_validation_frozen_summary_v1"


def build_validation_summary(field_summary: pd.DataFrame) -> pd.DataFrame:
    """Apply the frozen field, host-pair, and total summary procedure."""
    records = []
    for _, field in field_summary.sort_values("field_id").iterrows():
        records.append(
            summary_record(
                "field",
                f"field:{field['field_id']}",
                str(field["host_name"]),
                [str(field["field_id"])],
                int(field["retrieved_source_count"]),
                int(field["selected_source_count"]),
                float(field["usable_area_square_deg"]),
            )
        )
    for host_name, host_fields in field_summary.groupby("host_name", sort=True):
        records.append(
            summary_record(
                "host_pair",
                f"host_pair:{host_name}",
                str(host_name),
                host_fields["field_id"].astype(str).tolist(),
                int(host_fields["retrieved_source_count"].sum()),
                int(host_fields["selected_source_count"].sum()),
                float(host_fields["usable_area_square_deg"].sum()),
            )
        )
    records.append(
        summary_record(
            "all_validation_descriptive_only",
            "all_validation_fields",
            "all_validation_hosts",
            field_summary["field_id"].astype(str).tolist(),
            int(field_summary["retrieved_source_count"].sum()),
            int(field_summary["selected_source_count"].sum()),
            float(field_summary["usable_area_square_deg"].sum()),
        )
    )
    output = pd.DataFrame(records)
    output["summary_version"] = VALIDATION_SUMMARY_VERSION
    return output


def density_range(frame: pd.DataFrame, summary_level: str) -> dict[str, float]:
    """Return the measured density range at one summary level."""
    values = frame.loc[
        frame["summary_level"].eq(summary_level),
        "selected_source_density_per_square_deg",
    ]
    return {"minimum": float(values.min()), "maximum": float(values.max())}


def ranges_overlap(first: dict[str, float], second: dict[str, float]) -> bool:
    """Return whether two closed numerical ranges overlap."""
    return max(first["minimum"], second["minimum"]) <= min(first["maximum"], second["maximum"])


def main() -> None:
    """Retrieve, score, summarize, and compare only the validation fields."""
    protected_paths = (
        OFF_TARGET_DEVELOPMENT_MANIFEST,
        OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY,
        OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY_MANIFEST,
    )
    protected_hashes = {path: file_sha256(path) for path in protected_paths}
    split = pd.read_csv(OFF_TARGET_FIELD_SPLIT)
    split_manifest = json.loads(OFF_TARGET_FIELD_SPLIT_MANIFEST.read_text(encoding="utf-8"))
    development_manifest = json.loads(OFF_TARGET_DEVELOPMENT_MANIFEST.read_text(encoding="utf-8"))
    development_summary_manifest = json.loads(
        OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY_MANIFEST.read_text(encoding="utf-8")
    )
    development_summary = pd.read_csv(OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY)
    validation = split.loc[
        split["experiment_partition"].eq(VALIDATION_PARTITION)
        & split["frozen_for_selector_experiment"].astype(bool)
    ].copy()
    development_field_ids = set(
        split.loc[
            split["experiment_partition"].eq(DEVELOPMENT_PARTITION)
            & split["frozen_for_selector_experiment"].astype(bool),
            "field_id",
        ].astype(str)
    )
    expected_validation_ids = set(development_manifest["held_back_validation_field_ids"])
    actual_validation_ids = set(validation["field_id"].astype(str))
    if actual_validation_ids != expected_validation_ids:
        raise RuntimeError("Held-back field identities do not match the frozen development record")

    selector = load_frozen_selector()
    if (
        selector.threshold
        != development_summary_manifest["frozen_rules"]["selector_threshold_must_not_change"]
    ):
        raise RuntimeError("Frozen selector threshold changed before validation")

    service = tap.TAPService(DATA_LAB_TAP_URL)
    started = perf_counter()
    source_frames = []
    field_records = []
    queried_field_ids = []
    for _, field in validation.sort_values("field_id").iterrows():
        field_id = str(field["field_id"])
        if field_id in development_field_ids:
            raise RuntimeError(f"Refusing to query development field {field_id}")
        LOGGER.info("Opening held-back validation field %s", field_id)
        scored, field_record = retrieve_field(service, selector, field)
        source_frames.append(scored)
        field_records.append(field_record)
        queried_field_ids.append(field_id)
    sources = pd.concat(source_frames, ignore_index=True)
    field_summary = pd.DataFrame(field_records)
    frozen_summary = build_validation_summary(field_summary)
    total_seconds = perf_counter() - started

    field_rows = frozen_summary.loc[frozen_summary["summary_level"].eq("field")]
    pair_rows = frozen_summary.loc[frozen_summary["summary_level"].eq("host_pair")]
    overall_row = frozen_summary.loc[
        frozen_summary["summary_level"].eq("all_validation_descriptive_only")
    ].iloc[0]
    development_overall = development_summary.loc[
        development_summary["summary_level"].eq("all_development_descriptive_only")
    ].iloc[0]
    development_field_range = density_range(development_summary, "field")
    validation_field_range = density_range(frozen_summary, "field")
    development_pair_range = density_range(development_summary, "host_pair")
    validation_pair_range = density_range(frozen_summary, "host_pair")
    validation_density = float(overall_row["selected_source_density_per_square_deg"])
    development_density = float(development_overall["selected_source_density_per_square_deg"])
    comparison = {
        "interpretation": "descriptive_only_not_a_scientific_background_approval_test",
        "development_overall_density_per_square_deg": development_density,
        "validation_overall_density_per_square_deg": validation_density,
        "validation_to_development_overall_density_ratio": (
            validation_density / development_density
        ),
        "validation_overall_inside_development_poisson_68_density_range": bool(
            development_overall["poisson_68_lower_density_per_square_deg"]
            <= validation_density
            <= development_overall["poisson_68_upper_density_per_square_deg"]
        ),
        "validation_overall_inside_development_poisson_95_density_range": bool(
            development_overall["poisson_95_lower_density_per_square_deg"]
            <= validation_density
            <= development_overall["poisson_95_upper_density_per_square_deg"]
        ),
        "development_field_density_range_per_square_deg": development_field_range,
        "validation_field_density_range_per_square_deg": validation_field_range,
        "field_density_ranges_overlap": ranges_overlap(
            development_field_range, validation_field_range
        ),
        "development_host_pair_density_range_per_square_deg": development_pair_range,
        "validation_host_pair_density_range_per_square_deg": validation_pair_range,
        "host_pair_density_ranges_overlap": ranges_overlap(
            development_pair_range, validation_pair_range
        ),
    }

    source_field_ids = set(sources["field_id"].astype(str))
    summary_field_ids = set(field_summary["field_id"].astype(str))
    frozen_output_field_ids = {
        field_id for field_ids in frozen_summary["field_ids"] for field_id in field_ids.split(";")
    }
    expected_columns = set(RAW_GAIA_COLUMNS) | {
        "point_source_logistic_probability",
        "point_source_logistic_selected",
        "point_source_selector_version",
    }
    checks = {
        "four_validation_fields_queried_once": len(queried_field_ids) == 4
        and len(set(queried_field_ids)) == 4
        and set(queried_field_ids) == expected_validation_ids,
        "validation_ids_match_frozen_held_back_ids": actual_validation_ids
        == expected_validation_ids,
        "no_development_field_queried_or_written": development_field_ids.isdisjoint(
            queried_field_ids
        )
        and development_field_ids.isdisjoint(source_field_ids)
        and development_field_ids.isdisjoint(summary_field_ids)
        and development_field_ids.isdisjoint(frozen_output_field_ids),
        "source_and_field_summaries_match_validation_ids": source_field_ids
        == summary_field_ids
        == expected_validation_ids,
        "all_measured_counts_retrieved": field_summary["measured_source_count"]
        .eq(field_summary["retrieved_source_count"])
        .all(),
        "summary_counts_match_source_rows": field_summary.set_index("field_id")[
            "retrieved_source_count"
        ].equals(sources.groupby("field_id").size()),
        "all_raw_columns_and_selector_outputs_present": expected_columns.issubset(sources.columns),
        "source_identifiers_unique_within_fields": sources.groupby("field_id")["source_id"]
        .apply(lambda values: values.is_unique)
        .all(),
        "non_overlapping_fields_have_unique_source_identifiers": sources["source_id"].is_unique,
        "all_selector_probabilities_finite": np.isfinite(
            sources["point_source_logistic_probability"]
        ).all(),
        "all_rows_use_frozen_selector_version": sources["point_source_selector_version"]
        .eq(SELECTOR_VERSION)
        .all(),
        "selected_counts_match_source_decisions": field_summary.set_index("field_id")[
            "selected_source_count"
        ].equals(sources.groupby("field_id")["point_source_logistic_selected"].sum().astype(int)),
        "gaia_area_policy_unchanged": field_summary["usable_area_square_deg"]
        .eq(field_summary["successfully_queried_area_square_deg"])
        .all()
        and field_summary["masked_area_square_deg"].eq(0).all()
        and field_summary["missing_area_square_deg"].eq(0).all(),
        "split_identifier_unchanged": field_summary["split_id"]
        .eq(split_manifest["split_id"])
        .all(),
        "selector_threshold_unchanged": selector.threshold
        == development_manifest["selector_threshold"],
        "four_fields_two_pairs_one_total": len(field_rows) == 4
        and len(pair_rows) == 2
        and len(frozen_summary) == 7,
        "each_pair_contains_two_related_fields": pair_rows["field_count"].eq(2).all(),
        "selected_counts_conserved": int(field_rows["selected_source_count"].sum())
        == int(pair_rows["selected_source_count"].sum())
        == int(overall_row["selected_source_count"]),
        "retrieved_counts_conserved": int(field_rows["retrieved_source_count"].sum())
        == int(pair_rows["retrieved_source_count"].sum())
        == int(overall_row["retrieved_source_count"]),
        "usable_area_conserved": abs(
            field_rows["usable_area_square_deg"].sum() - pair_rows["usable_area_square_deg"].sum()
        )
        <= 1e-12
        and abs(
            field_rows["usable_area_square_deg"].sum()
            - float(overall_row["usable_area_square_deg"])
        )
        <= 1e-12,
        "summary_columns_match_frozen_development_contract": list(frozen_summary.columns)
        == list(development_summary.columns),
        "confidence_levels_unchanged": list(CONFIDENCE_LEVELS)
        == development_summary_manifest["frozen_rules"]["confidence_levels"],
        "development_artifacts_not_modified": all(
            file_sha256(path) == expected_hash for path, expected_hash in protected_hashes.items()
        ),
        "comparison_is_not_scientific_background_approval": comparison["interpretation"]
        == "descriptive_only_not_a_scientific_background_approval_test",
    }
    checks = {name: bool(value) for name, value in checks.items()}

    OFF_TARGET_VALIDATION_SOURCES.parent.mkdir(parents=True, exist_ok=True)
    sources.to_csv(OFF_TARGET_VALIDATION_SOURCES, index=False)
    field_summary.to_csv(OFF_TARGET_VALIDATION_SUMMARY, index=False)
    frozen_summary.to_csv(OFF_TARGET_VALIDATION_FROZEN_SUMMARY, index=False)
    manifest = {
        "experiment_version": "off_target_validation_selector_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "experiment_scope": "one_time_opening_of_four_held_back_off_target_fields",
        "data_source": {
            "catalog_release": "Gaia DR3",
            "table": "gaia_dr3.gaia_source",
            "query_service": DATA_LAB_TAP_URL,
            "publication_bibcode": "2023A&A...674A...1G",
            "publication_doi": "10.1051/0004-6361/202243940",
        },
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                OFF_TARGET_FIELD_SPLIT,
                OFF_TARGET_FIELD_SPLIT_MANIFEST,
                OFF_TARGET_DEVELOPMENT_MANIFEST,
                OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY,
                OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY_MANIFEST,
                POINT_SOURCE_LOGISTIC_MODEL,
                POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
            )
        ],
        "split_id": split_manifest["split_id"],
        "validation_field_ids": queried_field_ids,
        "protected_development_field_ids": sorted(development_field_ids),
        "selector_version": SELECTOR_VERSION,
        "selector_threshold": selector.threshold,
        "minimum_g_magnitude": MINIMUM_G_MAGNITUDE,
        "maximum_g_magnitude": MAXIMUM_G_MAGNITUDE,
        "raw_gaia_column_count": len(RAW_GAIA_COLUMNS),
        "raw_gaia_columns": RAW_GAIA_COLUMNS,
        "frozen_summary_rules": {
            "retain_every_field_separately": True,
            "combine_east_and_west_only_within_same_host": True,
            "all_validation_row_is_descriptive_only": True,
            "confidence_levels": list(CONFIDENCE_LEVELS),
            "count_range_method": "exact_central_poisson_garwood",
            "scientific_background_approval": False,
        },
        "plain_language_limit": (
            "This small held-back check tests whether the frozen procedure behaves similarly "
            "on four untouched circles. It does not make any circle a scientific background "
            "and does not establish a survey-wide background model."
        ),
        "validation_field_count": len(field_summary),
        "total_retrieved_source_count": int(field_summary["retrieved_source_count"].sum()),
        "total_selected_source_count": int(field_summary["selected_source_count"].sum()),
        "total_usable_area_square_deg": float(field_summary["usable_area_square_deg"].sum()),
        "total_elapsed_seconds": total_seconds,
        "comparison": comparison,
        "outputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                OFF_TARGET_VALIDATION_SOURCES,
                OFF_TARGET_VALIDATION_SUMMARY,
                OFF_TARGET_VALIDATION_FROZEN_SUMMARY,
            )
        ],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    OFF_TARGET_VALIDATION_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Off-target validation experiment failed: {checks}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
