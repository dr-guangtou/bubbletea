"""Exclude approved UCD/Gaia conflicts from reliable selector training.

The migration preserves benchmark-v2 rows, features, labels, and partitions. It
changes only reliability fields for approved conflict reviews and writes v3 files.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_BENCHMARKS, LITERATURE_SOURCES, PROJECT_ROOT
from scripts.phase1_literature.audit_reference_data import calculate_sha256

REVIEW_PATH = LITERATURE_SOURCES / "ucd_reliability_reviews.json"
SOURCE_BENCHMARK = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v2.csv"
OUTPUT_BENCHMARK = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v3.csv"
OUTPUT_BENCHMARK_MANIFEST = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v3_manifest.json"
SOURCE_FEATURES = LITERATURE_BENCHMARKS / "gaia_selector_development_features_v2.csv"
OUTPUT_FEATURES = LITERATURE_BENCHMARKS / "gaia_selector_development_features_v3.csv"
OUTPUT_FEATURES_MANIFEST = (
    LITERATURE_BENCHMARKS / "gaia_selector_development_features_v3_manifest.json"
)


def serialize_path(path: Path) -> str:
    """Return a repository-relative path."""
    return str(path.resolve().relative_to(PROJECT_ROOT))


def apply_reviews(rows: pd.DataFrame, gaia_ids: set[str]) -> pd.DataFrame:
    """Quarantine reviewed Gaia links without altering published classifications."""
    output = rows.copy()
    mask = output["gaia_dr3_id"].astype(str).isin(gaia_ids)
    if int(mask.sum()) != len(gaia_ids):
        raise RuntimeError("Every approved Gaia conflict must occur exactly once")
    if not output.loc[mask, "label_subtype"].eq("ucd_confirmed").all():
        raise RuntimeError("A reviewed conflict is not currently a confirmed UCD")
    output.loc[mask, "label_subtype"] = "ucd_confirmed_gaia_association_conflict"
    output.loc[mask, "confidence_tier"] = "conflict"
    output.loc[mask, "primary_label_eligible"] = False
    output.loc[mask, "sensitivity_label_eligible"] = False
    output.loc[mask, "label_basis"] = (
        "published_ucd_retained_but_gaia_association_quarantined_2026_07_18"
    )
    output["benchmark_version"] = "benchmark_v3"
    return output


def main() -> None:
    """Write the versioned reliable-training benchmark and feature cache."""
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    if review["review_status"] != "approved_by_project_lead_2026-07-18":
        raise RuntimeError("Reliability reviews lack project-lead approval")
    conflicts = [
        item
        for item in review["reviews"]
        if item["review_class"] == "published_ucd_or_gaia_counterpart_conflict"
    ]
    gaia_ids = {str(item["gaia_dr3_id"]) for item in conflicts}
    if len(gaia_ids) != 4:
        raise RuntimeError("Expected four approved UCD/Gaia conflicts")

    benchmark = pd.read_csv(SOURCE_BENCHMARK, dtype={"gaia_dr3_id": str})
    output = apply_reviews(benchmark, gaia_ids)
    output.to_csv(OUTPUT_BENCHMARK, index=False)
    generated_utc = datetime.now(UTC).isoformat()
    manifest = {
        "benchmark_version": "benchmark_v3",
        "partition_ruleset": "benchmark_partition_v1",
        "generated_utc": generated_utc,
        "policy": "quarantine_approved_ucd_gaia_conflicts_from_reliable_training",
        "validation_partition_inspected": False,
        "inputs": {
            "benchmark_v2": serialize_path(SOURCE_BENCHMARK),
            "benchmark_v2_sha256": calculate_sha256(SOURCE_BENCHMARK),
            "reliability_reviews": serialize_path(REVIEW_PATH),
            "reliability_reviews_sha256": calculate_sha256(REVIEW_PATH),
        },
        "invariants": {
            "row_count": len(output),
            "quarantined_gaia_association_count": len(gaia_ids),
            "published_classification_changes": 0,
            "partition_assignment_changes": 0,
        },
        "output": serialize_path(OUTPUT_BENCHMARK),
        "output_sha256": calculate_sha256(OUTPUT_BENCHMARK),
    }
    OUTPUT_BENCHMARK_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    features = pd.read_csv(SOURCE_FEATURES, dtype={"gaia_dr3_id": str})
    feature_output = apply_reviews(features, gaia_ids)
    feature_output.to_csv(OUTPUT_FEATURES, index=False)
    source_feature_manifest = json.loads(
        (LITERATURE_BENCHMARKS / "gaia_selector_development_features_v2_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    feature_manifest = {
        "feature_version": "gaia_selector_development_features_v3",
        "generated_utc": generated_utc,
        "policy": manifest["policy"],
        "validation_partition_inspected": False,
        "inputs": {
            "benchmark": serialize_path(OUTPUT_BENCHMARK),
            "benchmark_sha256": calculate_sha256(OUTPUT_BENCHMARK),
            "features_v2": serialize_path(SOURCE_FEATURES),
            "features_v2_sha256": calculate_sha256(SOURCE_FEATURES),
            "benchmark_v3": serialize_path(OUTPUT_BENCHMARK),
            "benchmark_v3_sha256": calculate_sha256(OUTPUT_BENCHMARK),
            "reliability_reviews": serialize_path(REVIEW_PATH),
            "reliability_reviews_sha256": calculate_sha256(REVIEW_PATH),
        },
        "invariants": {
            "row_count": len(feature_output),
            "quarantined_gaia_association_count": len(gaia_ids),
            "development_partition_only": set(feature_output["partition"]) == {"development"},
        },
        "counts": {
            "benchmark_rows": len(output),
            "development_rows": len(feature_output),
            "validation_rows": len(output) - len(feature_output),
            "queried_development_rows": 0,
            "queried_validation_rows": 0,
            "output_rows": len(feature_output),
        },
        "query_batches": source_feature_manifest["query_batches"],
        "query_batch_policy": "reused_v2_results_without_new_queries",
        "output": serialize_path(OUTPUT_FEATURES),
        "output_sha256": calculate_sha256(OUTPUT_FEATURES),
    }
    OUTPUT_FEATURES_MANIFEST.write_text(
        json.dumps(feature_manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
