"""Freeze descriptive summaries for off-target development selector counts."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from scipy.stats import chi2

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY,
    OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY_MANIFEST,
    OFF_TARGET_DEVELOPMENT_MANIFEST,
    OFF_TARGET_DEVELOPMENT_SUMMARY,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256

CONFIDENCE_LEVELS = (0.68, 0.95)
SUMMARY_VERSION = "off_target_development_frozen_summary_v1"


def poisson_count_interval(count: int, confidence_level: float) -> tuple[float, float]:
    """Return an exact central Poisson interval for an underlying average count."""
    if count < 0:
        raise ValueError("Count must be non-negative")
    if not 0 < confidence_level < 1:
        raise ValueError("Confidence level must lie between zero and one")
    tail_probability = 1 - confidence_level
    lower = 0.0 if count == 0 else 0.5 * chi2.ppf(tail_probability / 2, 2 * count)
    upper = 0.5 * chi2.ppf(1 - tail_probability / 2, 2 * (count + 1))
    return float(lower), float(upper)


def summary_record(
    summary_level: str,
    summary_id: str,
    host_name: str,
    field_ids: list[str],
    retrieved_source_count: int,
    selected_source_count: int,
    usable_area_square_deg: float,
) -> dict[str, object]:
    """Return one count- and area-preserving descriptive summary row."""
    record = {
        "summary_version": SUMMARY_VERSION,
        "summary_level": summary_level,
        "summary_id": summary_id,
        "host_name": host_name,
        "field_ids": ";".join(sorted(field_ids)),
        "field_count": len(field_ids),
        "retrieved_source_count": retrieved_source_count,
        "selected_source_count": selected_source_count,
        "usable_area_square_deg": usable_area_square_deg,
        "selected_source_density_per_square_deg": selected_source_count / usable_area_square_deg,
    }
    for confidence_level in CONFIDENCE_LEVELS:
        percentage = round(confidence_level * 100)
        lower_count, upper_count = poisson_count_interval(selected_source_count, confidence_level)
        record[f"poisson_{percentage}_lower_count"] = lower_count
        record[f"poisson_{percentage}_upper_count"] = upper_count
        record[f"poisson_{percentage}_lower_density_per_square_deg"] = (
            lower_count / usable_area_square_deg
        )
        record[f"poisson_{percentage}_upper_density_per_square_deg"] = (
            upper_count / usable_area_square_deg
        )
    return record


def main() -> None:
    """Write field, related host-pair, and all-development descriptive summaries."""
    development = pd.read_csv(OFF_TARGET_DEVELOPMENT_SUMMARY)
    selector_manifest = json.loads(OFF_TARGET_DEVELOPMENT_MANIFEST.read_text(encoding="utf-8"))
    records = []
    for _, field in development.sort_values("field_id").iterrows():
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
    for host_name, host_fields in development.groupby("host_name", sort=True):
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
            "all_development_descriptive_only",
            "all_development_fields",
            "all_development_hosts",
            development["field_id"].astype(str).tolist(),
            int(development["retrieved_source_count"].sum()),
            int(development["selected_source_count"].sum()),
            float(development["usable_area_square_deg"].sum()),
        )
    )
    output = pd.DataFrame(records)
    field_rows = output.loc[output["summary_level"].eq("field")]
    pair_rows = output.loc[output["summary_level"].eq("host_pair")]
    overall_row = output.loc[output["summary_level"].eq("all_development_descriptive_only")].iloc[0]
    input_by_field = development.set_index("field_id").sort_index()
    output_by_field = (
        field_rows.assign(field_id=field_rows["field_ids"]).set_index("field_id").sort_index()
    )
    held_back_ids = set(selector_manifest["held_back_validation_field_ids"])
    output_field_ids = {
        field_id for field_ids in output["field_ids"] for field_id in field_ids.split(";")
    }
    checks = {
        "four_development_fields_preserved": len(field_rows) == 4,
        "two_host_pair_summaries": len(pair_rows) == 2,
        "one_all_development_summary": output["summary_level"]
        .eq("all_development_descriptive_only")
        .sum()
        == 1,
        "seven_total_summary_rows": len(output) == 7,
        "field_counts_match_selector_input": output_by_field["selected_source_count"].equals(
            input_by_field["selected_source_count"]
        )
        and output_by_field["retrieved_source_count"].equals(
            input_by_field["retrieved_source_count"]
        ),
        "field_areas_match_selector_input": output_by_field["usable_area_square_deg"].equals(
            input_by_field["usable_area_square_deg"]
        ),
        "each_host_pair_contains_two_related_fields": pair_rows["field_count"].eq(2).all(),
        "selected_counts_conserved_at_each_summary_level": int(
            field_rows["selected_source_count"].sum()
        )
        == int(pair_rows["selected_source_count"].sum())
        == int(overall_row["selected_source_count"])
        == selector_manifest["total_selected_source_count"],
        "retrieved_counts_conserved_at_each_summary_level": int(
            field_rows["retrieved_source_count"].sum()
        )
        == int(pair_rows["retrieved_source_count"].sum())
        == int(overall_row["retrieved_source_count"])
        == selector_manifest["total_retrieved_source_count"],
        "usable_area_conserved_at_each_summary_level": abs(
            field_rows["usable_area_square_deg"].sum() - pair_rows["usable_area_square_deg"].sum()
        )
        <= 1e-12
        and abs(
            field_rows["usable_area_square_deg"].sum()
            - float(overall_row["usable_area_square_deg"])
        )
        <= 1e-12,
        "observed_density_inside_every_interval": all(
            output[f"poisson_{percentage}_lower_density_per_square_deg"]
            .le(output["selected_source_density_per_square_deg"])
            .all()
            and output[f"poisson_{percentage}_upper_density_per_square_deg"]
            .ge(output["selected_source_density_per_square_deg"])
            .all()
            for percentage in (68, 95)
        ),
        "ninety_five_percent_ranges_enclose_sixty_eight_percent_ranges": output[
            "poisson_95_lower_density_per_square_deg"
        ]
        .le(output["poisson_68_lower_density_per_square_deg"])
        .all()
        and output["poisson_95_upper_density_per_square_deg"]
        .ge(output["poisson_68_upper_density_per_square_deg"])
        .all(),
        "zero_count_interval_supported": poisson_count_interval(0, 0.95)[0] == 0
        and poisson_count_interval(0, 0.95)[1] > 0,
        "validation_fields_absent": held_back_ids.isdisjoint(output_field_ids),
        "selector_threshold_unchanged": selector_manifest["selector_threshold"]
        == 0.8277833628791744,
        "input_selector_run_passed_all_checks": selector_manifest["passed_count"]
        == selector_manifest["check_count"],
    }
    checks = {name: bool(value) for name, value in checks.items()}
    OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY, index=False)
    manifest = {
        "summary_version": SUMMARY_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "summary_scope": "development_only_descriptive_not_final_background_model",
        "input": {
            "path": str(OFF_TARGET_DEVELOPMENT_SUMMARY.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(OFF_TARGET_DEVELOPMENT_SUMMARY),
        },
        "selector_manifest": {
            "path": str(OFF_TARGET_DEVELOPMENT_MANIFEST.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(OFF_TARGET_DEVELOPMENT_MANIFEST),
        },
        "frozen_rules": {
            "retain_every_field_separately": True,
            "combine_east_and_west_only_within_same_host": True,
            "all_development_row_is_descriptive_only": True,
            "confidence_levels": list(CONFIDENCE_LEVELS),
            "count_range_method": "exact_central_poisson_garwood",
            "selector_threshold_must_not_change": selector_manifest["selector_threshold"],
            "validation_selector_results_must_remain_unopened": True,
            "scientific_background_approval": False,
        },
        "plain_language_limit": (
            "Poisson ranges describe random small-count variation only; they do not include "
            "field-to-field differences or make these fields scientific backgrounds."
        ),
        "summary_row_count": len(output),
        "field_row_count": len(field_rows),
        "host_pair_row_count": len(pair_rows),
        "overall_selected_source_count": int(overall_row["selected_source_count"]),
        "overall_usable_area_square_deg": float(overall_row["usable_area_square_deg"]),
        "overall_selected_source_density_per_square_deg": float(
            overall_row["selected_source_density_per_square_deg"]
        ),
        "held_back_validation_field_ids": sorted(held_back_ids),
        "output": {
            "path": str(OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    OFF_TARGET_DEVELOPMENT_FROZEN_SUMMARY_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Frozen development summary failed: {checks}")


if __name__ == "__main__":
    main()
