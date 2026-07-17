"""Measure Gaia-feature behavior for matched SDSS spectroscopic stars and UCDs."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MANIFEST,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
    SPECTROSCOPIC_STELLAR_REFERENCE_METRICS,
    SPECTROSCOPIC_STELLAR_REFERENCE_SUMMARY,
)
from scripts.phase1_literature.analyze_selector_development import (
    BOOTSTRAP_ITERATIONS,
    FEATURE_LABELS,
    add_derived_features,
    auc_metrics,
    inherited_model_selections,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256

ANALYSIS_VERSION = "spectroscopic_stellar_reference_analysis_v3"


def parse_arguments() -> argparse.Namespace:
    """Parse UCD, stellar-reference, and output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ucd-features", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES)
    parser.add_argument(
        "--stellar-matches", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES
    )
    parser.add_argument(
        "--stellar-manifest", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_MANIFEST
    )
    parser.add_argument("--metrics", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_METRICS)
    parser.add_argument("--summary", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_SUMMARY)
    parser.add_argument("--bootstrap-iterations", type=int, default=BOOTSTRAP_ITERATIONS)
    return parser.parse_args()


def main() -> None:
    """Write univariate metrics and legacy-rule retention summaries."""
    arguments = parse_arguments()
    development = pd.read_csv(arguments.ucd_features, dtype={"gaia_dr3_id": str})
    ucds = development.loc[
        development["label_subtype"].eq("ucd_confirmed")
        & development["primary_label_eligible"].eq(True)  # noqa: E712
    ].copy()
    stars = pd.read_csv(arguments.stellar_matches, dtype={"source_id": str})
    ucds = add_derived_features(ucds)
    stars = add_derived_features(stars)

    measurements = []
    for feature, feature_label in FEATURE_LABELS.items():
        measurement = auc_metrics(
            ucds[feature],
            stars[feature],
            arguments.bootstrap_iterations,
            f"matched_spectroscopic_star|{feature}",
        )
        measurements.append(
            {
                "analysis_version": ANALYSIS_VERSION,
                "negative_group": "matched_sdss_spectroscopic_star",
                "feature": feature,
                "feature_label": feature_label,
                "ucd_row_count": len(ucds),
                "stellar_row_count": len(stars),
                "ucd_coverage_fraction": float(ucds[feature].notna().mean()),
                "stellar_coverage_fraction": float(stars[feature].notna().mean()),
                **measurement,
            }
        )
    metrics = pd.DataFrame(measurements)
    arguments.metrics.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(arguments.metrics, index=False)

    legacy = {}
    for name, selected in inherited_model_selections(stars).items():
        legacy[name] = {
            "stellar_row_count": len(stars),
            "stellar_selected_count": int(selected.sum()),
            "stellar_selected_fraction": float(selected.mean()),
        }
    manifest = json.loads(arguments.stellar_manifest.read_text(encoding="utf-8"))
    summary = {
        "analysis_version": ANALYSIS_VERSION,
        "reference_version": manifest["reference_version"],
        "validation_partition_inspected": False,
        "singleness_status": manifest["singleness_status"],
        "counts": {
            "confirmed_development_ucds": len(ucds),
            "matched_spectroscopic_stars": len(stars),
            "metric_rows": len(metrics),
        },
        "legacy_rule_retention": legacy,
        "inputs": {
            "ucd_features_sha256": calculate_sha256(arguments.ucd_features),
            "stellar_matches_sha256": calculate_sha256(arguments.stellar_matches),
            "stellar_manifest_sha256": calculate_sha256(arguments.stellar_manifest),
        },
        "metrics_sha256": calculate_sha256(arguments.metrics),
        "decision_status": "development_measurement_only_no_selector_threshold_approved",
    }
    arguments.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
