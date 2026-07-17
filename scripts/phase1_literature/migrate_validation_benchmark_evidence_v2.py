"""Create evidence-corrected v2 benchmark artifacts without new Gaia queries.

The migration preserves every v1 row, Gaia feature, spatial partition, and source
provenance field. It updates only literature classification and label fields from
the rebuilt reference database, writes new files, and never overwrites v1.
"""

import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_BENCHMARKS,
    LITERATURE_REFERENCE_DB_V2,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256, connect_read_only
from scripts.phase1_literature.build_validation_benchmark import literature_label_fields

SOURCE_BENCHMARK = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v1.csv"
SOURCE_BENCHMARK_MANIFEST = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v1_manifest.json"
OUTPUT_BENCHMARK = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v2.csv"
OUTPUT_BENCHMARK_MANIFEST = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v2_manifest.json"
SOURCE_FEATURES = LITERATURE_BENCHMARKS / "gaia_selector_development_features_v1.csv"
SOURCE_FEATURES_MANIFEST = (
    LITERATURE_BENCHMARKS / "gaia_selector_development_features_v1_manifest.json"
)
OUTPUT_FEATURES = LITERATURE_BENCHMARKS / "gaia_selector_development_features_v2.csv"
OUTPUT_FEATURES_MANIFEST = (
    LITERATURE_BENCHMARKS / "gaia_selector_development_features_v2_manifest.json"
)


def serialize_path(path: Path) -> str:
    """Return a repository-relative path."""
    return str(path.resolve().relative_to(PROJECT_ROOT))


def load_classifications(database: Path) -> dict[str, dict[str, str]]:
    """Load the current classification fields keyed by canonical identifier."""
    with connect_read_only(database) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT canonical_object_id, classification_state,
                   classification_subtype, ruleset_id
            FROM object_classifications
            """
        ).fetchall()
    return {str(row["canonical_object_id"]): dict(row) for row in rows}


def update_literature_rows(
    rows: pd.DataFrame, classifications: dict[str, dict[str, str]]
) -> tuple[pd.DataFrame, int]:
    """Apply current evidence labels while preserving non-literature rows."""
    output = rows.copy()
    changed_rows = 0
    evidence_fields = {
        "label",
        "label_subtype",
        "confidence_tier",
        "primary_label_eligible",
        "sensitivity_label_eligible",
        "label_basis",
        "classification_state",
    }
    literature_mask = output["source_cohort"].eq("literature_ucd")
    for index in output.index[literature_mask]:
        canonical_ids = str(output.at[index, "canonical_object_id"]).split(";")
        current = [classifications[canonical_id] for canonical_id in canonical_ids]
        if len(current) == 1:
            classification = current[0]
            labels = literature_label_fields(classification["classification_state"])
            updated_fields = {**classification, **labels}
        else:
            updated_fields = {
                "classification_state": ";".join(
                    sorted({item["classification_state"] for item in current})
                ),
                "classification_subtype": ";".join(
                    sorted({str(item["classification_subtype"] or "") for item in current})
                ),
                "ruleset_id": ";".join(sorted({str(item["ruleset_id"] or "") for item in current})),
            }
        if any(
            str(output.at[index, key]) != str(value)
            for key, value in updated_fields.items()
            if key in evidence_fields
        ):
            changed_rows += 1
        for key, value in updated_fields.items():
            output.at[index, key] = value
    output["benchmark_version"] = "benchmark_v2"
    return output, changed_rows


def main() -> None:
    """Write versioned corrected benchmark and cached development features."""
    classifications = load_classifications(LITERATURE_REFERENCE_DB_V2)
    benchmark = pd.read_csv(
        SOURCE_BENCHMARK,
        dtype={"gaia_dr3_id": str, "canonical_object_id": str},
        keep_default_na=False,
    )
    corrected_benchmark, changed_rows = update_literature_rows(benchmark, classifications)
    if not corrected_benchmark["benchmark_id"].equals(benchmark["benchmark_id"]):
        raise RuntimeError("Benchmark row identity or order changed")
    immutable_columns = [
        column
        for column in benchmark.columns
        if column
        not in {
            "benchmark_version",
            "label",
            "label_subtype",
            "confidence_tier",
            "primary_label_eligible",
            "sensitivity_label_eligible",
            "label_basis",
            "classification_state",
            "classification_subtype",
            "ruleset_id",
        }
    ]
    if not corrected_benchmark[immutable_columns].equals(benchmark[immutable_columns]):
        raise RuntimeError("An evidence-independent benchmark field changed")
    corrected_benchmark.to_csv(OUTPUT_BENCHMARK, index=False)

    generated_utc = datetime.now(UTC).isoformat()
    benchmark_manifest = {
        "benchmark_version": "benchmark_v2",
        "partition_ruleset": "benchmark_partition_v1",
        "generated_utc": generated_utc,
        "migration_policy": "evidence_fields_only_from_corrected_reference_database",
        "sealed_validation_policy": "no_validation_metrics_or_feature_outcomes_inspected",
        "inputs": {
            "benchmark_v1": serialize_path(SOURCE_BENCHMARK),
            "benchmark_v1_sha256": calculate_sha256(SOURCE_BENCHMARK),
            "benchmark_v1_manifest": serialize_path(SOURCE_BENCHMARK_MANIFEST),
            "benchmark_v1_manifest_sha256": calculate_sha256(SOURCE_BENCHMARK_MANIFEST),
            "reference_database": serialize_path(LITERATURE_REFERENCE_DB_V2),
            "reference_database_sha256": calculate_sha256(LITERATURE_REFERENCE_DB_V2),
        },
        "invariants": {
            "row_count": len(corrected_benchmark),
            "changed_evidence_row_count": changed_rows,
            "row_identity_and_order_preserved": True,
            "gaia_features_preserved": True,
            "partition_assignments_preserved": True,
        },
        "output": serialize_path(OUTPUT_BENCHMARK),
        "output_sha256": calculate_sha256(OUTPUT_BENCHMARK),
    }
    OUTPUT_BENCHMARK_MANIFEST.write_text(
        json.dumps(benchmark_manifest, indent=2) + "\n", encoding="utf-8"
    )

    features = pd.read_csv(
        SOURCE_FEATURES,
        dtype={"gaia_dr3_id": str, "canonical_object_id": str},
        keep_default_na=False,
    )
    corrected_features, changed_feature_rows = update_literature_rows(features, classifications)
    if set(corrected_features["partition"]) != {"development"}:
        raise RuntimeError("Development feature cache contains a non-development row")
    corrected_features.to_csv(OUTPUT_FEATURES, index=False)
    source_feature_manifest = json.loads(SOURCE_FEATURES_MANIFEST.read_text(encoding="utf-8"))
    feature_manifest = {
        "feature_version": "gaia_selector_development_features_v2",
        "generated_utc": generated_utc,
        "migration_policy": "reuse_v1_gaia_features_and_apply_benchmark_v2_evidence_fields",
        "inputs": {
            "benchmark": serialize_path(OUTPUT_BENCHMARK),
            "benchmark_sha256": calculate_sha256(OUTPUT_BENCHMARK),
            "features_v1": serialize_path(SOURCE_FEATURES),
            "features_v1_sha256": calculate_sha256(SOURCE_FEATURES),
            "features_v1_manifest": serialize_path(SOURCE_FEATURES_MANIFEST),
            "features_v1_manifest_sha256": calculate_sha256(SOURCE_FEATURES_MANIFEST),
            "benchmark_v2": serialize_path(OUTPUT_BENCHMARK),
            "benchmark_v2_sha256": calculate_sha256(OUTPUT_BENCHMARK),
        },
        "invariants": {
            "row_count": len(corrected_features),
            "changed_evidence_row_count": changed_feature_rows,
            "gaia_features_preserved": True,
            "development_partition_only": True,
        },
        "counts": {
            "benchmark_rows": len(corrected_benchmark),
            "development_rows": len(corrected_features),
            "validation_rows": len(corrected_benchmark) - len(corrected_features),
            "queried_development_rows": 0,
            "queried_validation_rows": 0,
            "output_rows": len(corrected_features),
        },
        "query_batches": source_feature_manifest["query_batches"],
        "query_batch_policy": "reused_v1_results_without_new_queries",
        "output": serialize_path(OUTPUT_FEATURES),
        "output_sha256": calculate_sha256(OUTPUT_FEATURES),
    }
    OUTPUT_FEATURES_MANIFEST.write_text(
        json.dumps(feature_manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
