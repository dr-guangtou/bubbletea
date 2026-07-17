"""Validate selector development artifacts without evaluating selector thresholds."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    FIGURES_DIR,
    SELECTOR_DEVELOPMENT_FEATURE_METRICS,
    SELECTOR_DEVELOPMENT_FEATURES,
    SELECTOR_DEVELOPMENT_FEATURES_MANIFEST,
    SELECTOR_DEVELOPMENT_SENSITIVITY,
    SELECTOR_DEVELOPMENT_VALIDATION,
    VALIDATION_BENCHMARK,
)
from scripts.phase1_literature.analyze_selector_development import FEATURE_LABELS
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_selector_development_features import (
    ADDITIONAL_GAIA_COLUMNS,
    DEVELOPMENT_FEATURE_VERSION,
)

EXPECTED_SCENARIOS = {
    "primary_confirmed_ucd",
    "candidate_as_positive_sensitivity",
    "exclude_phangs_sensitivity",
    "exclude_all_hii_sensitivity",
}


def parse_arguments() -> argparse.Namespace:
    """Parse selector-development artifact paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--features", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES)
    parser.add_argument(
        "--features-manifest", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES_MANIFEST
    )
    parser.add_argument("--metrics", type=Path, default=SELECTOR_DEVELOPMENT_FEATURE_METRICS)
    parser.add_argument("--sensitivity", type=Path, default=SELECTOR_DEVELOPMENT_SENSITIVITY)
    parser.add_argument("--output", type=Path, default=SELECTOR_DEVELOPMENT_VALIDATION)
    return parser.parse_args()


def main() -> None:
    """Run deterministic development-artifact checks and write a report."""
    arguments = parse_arguments()
    benchmark = pd.read_csv(arguments.benchmark, dtype={"gaia_dr3_id": str})
    features = pd.read_csv(arguments.features, dtype={"gaia_dr3_id": str})
    metrics = pd.read_csv(arguments.metrics)
    with arguments.features_manifest.open(encoding="utf-8") as input_file:
        manifest = json.load(input_file)
    with arguments.sensitivity.open(encoding="utf-8") as input_file:
        sensitivity = json.load(input_file)

    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    development_ids = set(
        benchmark.loc[benchmark["partition"].eq("development"), "gaia_dr3_id"].astype(str)
    )
    validation_ids = set(
        benchmark.loc[benchmark["partition"].eq("validation"), "gaia_dr3_id"].astype(str)
    )
    feature_ids = set(features["gaia_dr3_id"].astype(str))
    check(
        "feature_version",
        manifest["feature_version"] == DEVELOPMENT_FEATURE_VERSION,
        manifest["feature_version"],
    )
    check(
        "benchmark_digest",
        calculate_sha256(arguments.benchmark) == manifest["inputs"]["benchmark_sha256"],
        manifest["inputs"]["benchmark_sha256"],
    )
    check(
        "feature_digest",
        calculate_sha256(arguments.features) == manifest["output_sha256"],
        manifest["output_sha256"],
    )
    check("features_are_unique", features["gaia_dr3_id"].is_unique, len(features))
    check(
        "all_development_ids_represented",
        feature_ids == development_ids,
        {
            "feature_ids": len(feature_ids),
            "development_ids": len(development_ids),
        },
    )
    check(
        "no_validation_ids_represented",
        not feature_ids.intersection(validation_ids),
        len(feature_ids.intersection(validation_ids)),
    )
    check(
        "only_development_partition",
        set(features["partition"]) == {"development"},
        sorted(features["partition"].unique()),
    )
    check(
        "manifest_reports_zero_validation_queries",
        manifest["counts"]["queried_validation_rows"] == 0,
        manifest["counts"]["queried_validation_rows"],
    )
    check(
        "all_query_batches_complete",
        all(
            batch["requested_identifier_count"] == batch["returned_row_count"]
            for batch in manifest["query_batches"]
        ),
        manifest["query_batches"],
    )
    expected_columns = set(ADDITIONAL_GAIA_COLUMNS[1:])
    check(
        "additional_gaia_columns_present",
        expected_columns.issubset(features.columns),
        sorted(expected_columns - set(features.columns)),
    )
    check(
        "metrics_feature_contract",
        set(metrics["feature"]) == set(FEATURE_LABELS),
        sorted(metrics["feature"].unique()),
    )
    check(
        "metrics_scenario_contract",
        set(metrics["scenario"]) == EXPECTED_SCENARIOS,
        sorted(metrics["scenario"].unique()),
    )
    primary_overall = metrics.loc[
        metrics["scenario"].eq("primary_confirmed_ucd")
        & metrics["negative_group"].eq("all_primary_contaminants")
    ]
    expected_positive_count = int(
        (
            features["label_subtype"].eq("ucd_confirmed")
            & features["primary_label_eligible"].eq(True)  # noqa: E712
        ).sum()
    )
    expected_negative_count = int(
        (
            features["label"].eq("contaminant") & features["primary_label_eligible"].eq(True)  # noqa: E712
        ).sum()
    )
    check(
        "primary_label_counts",
        set(primary_overall["positive_row_count"]) == {expected_positive_count}
        and set(primary_overall["negative_row_count"]) == {expected_negative_count},
        {
            "positive": sorted(
                int(value) for value in primary_overall["positive_row_count"].unique()
            ),
            "negative": sorted(
                int(value) for value in primary_overall["negative_row_count"].unique()
            ),
        },
    )
    check(
        "bootstrap_intervals_ordered",
        (
            primary_overall["auc_ci_lower"].le(primary_overall["discrimination_auc"])
            & primary_overall["discrimination_auc"].le(primary_overall["auc_ci_upper"])
        ).all(),
        len(primary_overall),
    )
    check(
        "sensitivity_feature_digest",
        sensitivity["feature_matrix_sha256"] == calculate_sha256(arguments.features),
        sensitivity["feature_matrix_sha256"],
    )
    check(
        "validation_partition_not_inspected",
        sensitivity["validation_partition_inspected"] is False,
        sensitivity["validation_partition_inspected"],
    )
    check(
        "no_selector_decision_claimed",
        sensitivity["decision_status"]
        == "development_measurement_only_no_selector_or_threshold_approved",
        sensitivity["decision_status"],
    )
    for figure_name in [
        "selector_development_feature_distributions",
        "selector_development_feature_auc",
    ]:
        figure_path = FIGURES_DIR / "phase1" / f"{figure_name}.png"
        caption_path = FIGURES_DIR / "phase1" / f"{figure_name}.md"
        check(
            f"{figure_name}_pair",
            figure_path.is_file() and caption_path.is_file(),
            {"figure": str(figure_path), "caption": str(caption_path)},
        )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "feature_version": DEVELOPMENT_FEATURE_VERSION,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "counts": {
            "development_rows": len(features),
            "validation_rows": len(validation_ids),
            "metrics_rows": len(metrics),
        },
        "checks": checks,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failed:
        failed_names = ", ".join(str(item["name"]) for item in failed)
        raise RuntimeError(f"Selector development validation failed: {failed_names}")


if __name__ == "__main__":
    main()
