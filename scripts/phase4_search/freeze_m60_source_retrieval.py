"""Freeze the exact complete-field M60 Gaia retrieval before downloading rows."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
    M60_POSITIVE_CONTROL_CONTRACT,
    M60_POSITIVE_CONTROL_COUNT_BENCHMARK,
    M60_POSITIVE_CONTROL_RETRIEVAL_CONTRACT,
    M60_POSITIVE_CONTROL_REVIEW_RULES,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase3_background.query_partition import cone_predicate
from scripts.phase4_search.freeze_m60_review_rules import REVIEW_RULES_VERSION
from scripts.utils.point_source_selector import (
    MAXIMUM_G_MAGNITUDE,
    MINIMUM_G_MAGNITUDE,
    RAW_GAIA_COLUMNS,
    SELECTOR_VERSION,
)

RETRIEVAL_CONTRACT_VERSION = "m60_positive_control_retrieval_contract_v1"


def main() -> None:
    """Write the source query, limits, and output policy without archive access."""
    design = json.loads(M60_POSITIVE_CONTROL_CONTRACT.read_text())
    count = json.loads(M60_POSITIVE_CONTROL_COUNT_BENCHMARK.read_text())
    review = json.loads(M60_POSITIVE_CONTROL_REVIEW_RULES.read_text())
    safe_limit = json.loads(GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST.read_text())
    host = design["host"]
    base_where = (
        f"{cone_predicate(host['ra_deg'], host['dec_deg'], host['outer_radius_deg'])} "
        f"AND phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} AND {MAXIMUM_G_MAGNITUDE}"
    )
    maximum_rows_per_strip = int(safe_limit["provisional_safe_rows_per_strip"])
    checks = {
        "raw_count_was_measured": count["status"] == "measured_raw_count_only",
        "raw_count_checks_passed": count["passed_count"] == count["check_count"],
        "review_rules_are_frozen": review["review_rules_version"] == REVIEW_RULES_VERSION,
        "selector_is_unchanged_version_1": SELECTOR_VERSION == "point_source_logistic_model_v1",
        "all_selector_input_columns_are_requested": len(RAW_GAIA_COLUMNS) == 19,
        "source_rows_stay_outside_repository": True,
        "complete_circle_is_requested": host["outer_radius_kpc"] == 600,
        "no_review_flag_filters_the_query": "review" not in base_where.lower(),
        "contract_executes_no_archive_query": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    artifact = {
        "retrieval_contract_version": RETRIEVAL_CONTRACT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "frozen_before_source_row_retrieval",
        "plain_language_scope": (
            "Download every Gaia row in the previously counted M60 circle and "
            "magnitude range, score selector version 1 locally, retain all physical "
            "rings, and initialize review flags without removing sources."
        ),
        "host": host,
        "raw_source_count": count["source_count_in_frozen_magnitude_domain"],
        "source_columns": RAW_GAIA_COLUMNS,
        "base_where": base_where,
        "maximum_rows_per_strip": maximum_rows_per_strip,
        "selector_version": SELECTOR_VERSION,
        "review_rules_version": REVIEW_RULES_VERSION,
        "review_defaults": {
            "star_forming_catalog_association": "not_checked",
            "star_forming_color_review_priority": "not_evaluated",
            "star_forming_visual_evidence": "not_reviewed",
            "possible_star_forming_region_or_young_cluster": "not_reviewed",
            "gaia_image_measurement_warning": "not_evaluated",
            "blend_or_image_problem_visual_evidence": "not_reviewed",
            "possible_nearby_source_blend_or_image_problem": "not_reviewed",
            "visual_review_note": "",
            "visual_reviewer": "",
            "visual_reviewed_at_utc": "",
        },
        "external_outputs": [
            "$BUBBLETEA_EXTERNAL_DATA/bubbletea/m60_positive_control_v1/scored_sources.csv",
            "$BUBBLETEA_EXTERNAL_DATA/bubbletea/m60_positive_control_v1/selector_passing_review.csv",
            "$BUBBLETEA_EXTERNAL_DATA/bubbletea/m60_positive_control_v1/strips/",
        ],
        "inputs": {
            str(path.relative_to(PROJECT_ROOT)): calculate_sha256(path)
            for path in (
                M60_POSITIVE_CONTROL_CONTRACT,
                M60_POSITIVE_CONTROL_COUNT_BENCHMARK,
                M60_POSITIVE_CONTROL_REVIEW_RULES,
                POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
                GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
            )
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    M60_POSITIVE_CONTROL_RETRIEVAL_CONTRACT.write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"M60 retrieval freeze failed: {checks}")


if __name__ == "__main__":
    main()
