"""Validate the development-only logistic regularization stability artifacts."""

import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_VALIDATION
from scripts.phase1_literature.audit_reference_data import calculate_sha256

METRICS = LITERATURE_VALIDATION / "logistic_regularization_stability_metrics_v1.csv"
SUMMARY = LITERATURE_VALIDATION / "logistic_regularization_stability_v1.json"
OUTPUT = LITERATURE_VALIDATION / "logistic_regularization_stability_validation_v1.json"
SOURCE_SUMMARY = (
    LITERATURE_VALIDATION / "logistic_regularization_frozen_c1000_source_summary_v1.csv"
)


def main() -> None:
    """Check artifact contracts, hashes, counts, and summary reproduction."""
    metrics = pd.read_csv(METRICS)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    source_summary = pd.read_csv(SOURCE_SUMMARY, dtype={"gaia_dr3_id": str})
    checks = {
        "validation_partition_not_inspected": summary["validation_partition_inspected"] is False,
        "metrics_digest": summary["metrics_sha256"] == calculate_sha256(METRICS),
        "source_summary_digest": summary["frozen_c1000_source_summary_sha256"]
        == calculate_sha256(SOURCE_SUMMARY),
        "thirty_repeat_configuration_rows": len(metrics) == 30,
        "ten_repeats": set(metrics["repeat_index"]) == set(range(1, 11)),
        "three_configurations": set(metrics["configuration"])
        == {"c_1000", "c_3000", "unregularized"},
        "three_rows_per_repeat": metrics.groupby("repeat_index").size().eq(3).all(),
        "target_recall_met": metrics["ucd_recall"].ge(0.9).all(),
        "finite_metrics": metrics[
            ["ucd_recall", "macro_priority_retention", "maximum_coefficient_l2_norm"]
        ]
        .notna()
        .all()
        .all(),
        "source_rows_unique": source_summary["row_id"].is_unique,
    }
    checks = {name: bool(passed) for name, passed in checks.items()}
    passed_count = sum(checks.values())
    report = {
        "analysis_version": summary["analysis_version"],
        "check_count": len(checks),
        "passed_count": passed_count,
        "failed_count": len(checks) - passed_count,
        "checks": checks,
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not all(checks.values()):
        raise RuntimeError(f"Regularization stability validation failed: {checks}")


if __name__ == "__main__":
    main()
