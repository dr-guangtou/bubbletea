"""Retrieve frozen Gaia inputs for the authorized validation evaluation."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_BENCHMARKS, LITERATURE_SOURCES, LITERATURE_VALIDATION
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_selector_development_features import (
    ADDITIONAL_GAIA_COLUMNS,
    GAIA_RELEASE,
    retrieve_features,
)
from scripts.phase1_literature.build_validation_benchmark import serialize_path
from scripts.phase1_literature.synchronize_crossmatch_products import DATALAB_TAP_URL

BENCHMARK = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v3.csv"
BENCHMARK_MANIFEST = LITERATURE_BENCHMARKS / "gaia_validation_benchmark_v3_manifest.json"
AUTHORIZATION = LITERATURE_SOURCES / "point_source_validation_authorization_v1.json"
OUTPUT = LITERATURE_VALIDATION / "gaia_selector_validation_features_v1.csv"
MANIFEST_OUTPUT = LITERATURE_VALIDATION / "gaia_selector_validation_features_v1_manifest.json"


def main() -> None:
    """Query exact validation identifiers after checking frozen authorization."""
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    if (
        authorization["authorization_status"] != "approved_by_project_lead"
        or authorization["retuning_after_evaluation"] != "prohibited"
    ):
        raise RuntimeError("Validation evaluation lacks frozen authorization")
    benchmark = pd.read_csv(BENCHMARK, dtype={"gaia_dr3_id": str})
    validation = benchmark.loc[benchmark["partition"].eq("validation")].copy()
    requested_ids = validation["gaia_dr3_id"].astype(str).tolist()
    features, query_records = retrieve_features(requested_ids)
    if set(features["source_id"]) != set(requested_ids):
        raise RuntimeError("Validation Gaia query did not return the exact identifier set")
    output = validation.merge(
        features, left_on="gaia_dr3_id", right_on="source_id", validate="1:1"
    ).drop(columns="source_id")
    if set(output["partition"]) != {"validation"}:
        raise RuntimeError("Validation feature output contains another partition")
    output.to_csv(OUTPUT, index=False)
    manifest = {
        "feature_version": "gaia_selector_validation_features_v1",
        "generated_utc": datetime.now(UTC).isoformat(),
        "gaia_release": GAIA_RELEASE,
        "endpoint": DATALAB_TAP_URL,
        "partition": "validation",
        "authorization": serialize_path(AUTHORIZATION),
        "authorization_sha256": calculate_sha256(AUTHORIZATION),
        "inputs": {
            "benchmark": serialize_path(BENCHMARK),
            "benchmark_sha256": calculate_sha256(BENCHMARK),
            "benchmark_manifest": serialize_path(BENCHMARK_MANIFEST),
            "benchmark_manifest_sha256": calculate_sha256(BENCHMARK_MANIFEST),
        },
        "additional_gaia_columns": ADDITIONAL_GAIA_COLUMNS[1:],
        "query_batches": query_records,
        "counts": {
            "requested_validation_rows": len(requested_ids),
            "output_rows": len(output),
            "unique_output_gaia_sources": output["gaia_dr3_id"].nunique(),
        },
        "output": serialize_path(OUTPUT),
        "output_sha256": calculate_sha256(OUTPUT),
    }
    MANIFEST_OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
