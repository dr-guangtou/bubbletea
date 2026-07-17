"""Validate the blind-safe spectroscopic stellar reference and feature analysis."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    SPECTROSCOPIC_STELLAR_REFERENCE_MANIFEST,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
    SPECTROSCOPIC_STELLAR_REFERENCE_METRICS,
    SPECTROSCOPIC_STELLAR_REFERENCE_SUMMARY,
    SPECTROSCOPIC_STELLAR_REFERENCE_VALIDATION,
    STELLAR_REFERENCE_DIR,
    VALIDATION_BENCHMARK,
)
from scripts.phase1_literature.analyze_selector_development import FEATURE_LABELS
from scripts.phase1_literature.analyze_spectroscopic_stellar_reference import ANALYSIS_VERSION
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_spectroscopic_stellar_reference import (
    CONTROLS_PER_UCD,
    MATCH_COLUMNS,
    REFERENCE_VERSION,
)


def parse_arguments() -> argparse.Namespace:
    """Parse reference artifact paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--matches", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    parser.add_argument("--manifest", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_MANIFEST)
    parser.add_argument("--metrics", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_METRICS)
    parser.add_argument("--summary", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_SUMMARY)
    parser.add_argument("--external-directory", type=Path, default=STELLAR_REFERENCE_DIR)
    parser.add_argument("--output", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_VALIDATION)
    return parser.parse_args()


def main() -> None:
    """Run provenance, partition, matching, and analysis checks."""
    arguments = parse_arguments()
    benchmark = pd.read_csv(arguments.benchmark, dtype={"gaia_dr3_id": str})
    matches = pd.read_csv(
        arguments.matches,
        dtype={"source_id": str, "matched_ucd_gaia_dr3_id": str},
    )
    metrics = pd.read_csv(arguments.metrics)
    manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
    summary = json.loads(arguments.summary.read_text(encoding="utf-8"))
    external_path = arguments.external_directory / manifest["external_pool"]
    checks = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    benchmark_ids = set(benchmark["gaia_dr3_id"])
    validation_ids = set(benchmark.loc[benchmark["partition"].eq("validation"), "gaia_dr3_id"])
    target_counts = matches.groupby("matched_ucd_gaia_dr3_id").size()
    check(
        "reference_version",
        manifest["reference_version"] == REFERENCE_VERSION,
        manifest["reference_version"],
    )
    check(
        "analysis_version",
        summary["analysis_version"] == ANALYSIS_VERSION,
        summary["analysis_version"],
    )
    check(
        "singleness_not_claimed",
        manifest["singleness_status"] == "not_established",
        manifest["singleness_status"],
    )
    check(
        "validation_partition_blind",
        manifest["validation_partition_inspected"] is False
        and summary["validation_partition_inspected"] is False,
        [manifest["validation_partition_inspected"], summary["validation_partition_inspected"]],
    )
    check(
        "no_selector_feature_matching",
        manifest["selector_features_used_for_selection_or_matching"] == [],
        manifest["selector_features_used_for_selection_or_matching"],
    )
    check(
        "declared_matching_variables",
        manifest["matching_variables"] == MATCH_COLUMNS,
        manifest["matching_variables"],
    )
    check(
        "unique_stellar_sources",
        not matches["source_id"].duplicated().any(),
        int(matches["source_id"].duplicated().sum()),
    )
    check(
        "no_benchmark_source_overlap",
        set(matches["source_id"]).isdisjoint(benchmark_ids),
        len(set(matches["source_id"]).intersection(benchmark_ids)),
    )
    check(
        "no_validation_target",
        set(matches["matched_ucd_gaia_dr3_id"]).isdisjoint(validation_ids),
        len(set(matches["matched_ucd_gaia_dr3_id"]).intersection(validation_ids)),
    )
    check(
        "three_controls_per_target",
        target_counts.eq(CONTROLS_PER_UCD).all(),
        target_counts.value_counts().to_dict(),
    )
    check(
        "all_spectroscopic_star",
        matches["spectroscopic_class"].eq("STAR").all(),
        matches["spectroscopic_class"].value_counts().to_dict(),
    )
    check(
        "associations_within_1p5_arcsec",
        matches["gaia_association_distance_arcsec"].le(1.5).all(),
        float(matches["gaia_association_distance_arcsec"].max()),
    )
    check("external_pool_exists", external_path.is_file(), str(external_path))
    if external_path.is_file():
        check(
            "external_pool_hash",
            calculate_sha256(external_path) == manifest["external_pool_sha256"],
            manifest["external_pool_sha256"],
        )
    check(
        "matches_hash",
        calculate_sha256(arguments.matches) == manifest["matches_sha256"],
        manifest["matches_sha256"],
    )
    check(
        "metric_feature_set",
        set(metrics["feature"]) == set(FEATURE_LABELS),
        sorted(metrics["feature"]),
    )
    check("metric_row_count", len(metrics) == len(FEATURE_LABELS), len(metrics))
    check(
        "metrics_hash",
        calculate_sha256(arguments.metrics) == summary["metrics_sha256"],
        summary["metrics_sha256"],
    )
    check(
        "no_threshold_approved",
        summary["decision_status"] == "development_measurement_only_no_selector_threshold_approved",
        summary["decision_status"],
    )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "reference_version": REFERENCE_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "checks": checks,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failed:
        raise RuntimeError(
            "Spectroscopic stellar reference validation failed: "
            + ", ".join(item["name"] for item in failed)
        )


if __name__ == "__main__":
    main()
