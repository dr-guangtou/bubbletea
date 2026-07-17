"""Validate expanded Gaia morphology host/control comparison artifacts."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    FIGURES_DIR,
    GAIA_MORPHOLOGY_HOST_CONTROL_COMPARISON,
    GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN,
    GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_MANIFEST,
    GAIA_MORPHOLOGY_HOST_CONTROL_FIELD_SUMMARY,
    GAIA_MORPHOLOGY_HOST_CONTROL_MANIFEST,
    GAIA_MORPHOLOGY_HOST_CONTROL_METRICS,
    GAIA_MORPHOLOGY_HOST_CONTROL_SOURCES,
    GAIA_MORPHOLOGY_HOST_CONTROL_VALIDATION,
    VALIDATION_BENCHMARK_MANIFEST,
)
from scripts.phase1_literature.analyze_gaia_morphology_host_controls import (
    ANALYSIS_VERSION,
    FIGURE_NAME,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256


def parse_arguments() -> argparse.Namespace:
    """Parse expanded comparison artifact paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN)
    parser.add_argument(
        "--design-manifest",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_MANIFEST,
    )
    parser.add_argument("--benchmark-manifest", type=Path, default=VALIDATION_BENCHMARK_MANIFEST)
    parser.add_argument("--sources", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_SOURCES)
    parser.add_argument("--metrics", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_METRICS)
    parser.add_argument(
        "--field-summary",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_CONTROL_FIELD_SUMMARY,
    )
    parser.add_argument(
        "--comparison",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_CONTROL_COMPARISON,
    )
    parser.add_argument("--manifest", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_MANIFEST)
    parser.add_argument("--output", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_VALIDATION)
    return parser.parse_args()


def main() -> None:
    """Run deterministic expanded-comparison checks."""
    arguments = parse_arguments()
    design = pd.read_csv(arguments.design)
    sources = pd.read_csv(arguments.sources, dtype={"source_id": str})
    metrics = pd.read_csv(arguments.metrics)
    field_summary = pd.read_csv(arguments.field_summary)
    manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
    comparison = json.loads(arguments.comparison.read_text(encoding="utf-8"))
    design_manifest = json.loads(arguments.design_manifest.read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("analysis_version", manifest["analysis_version"] == ANALYSIS_VERSION, ANALYSIS_VERSION)
    check(
        "exploratory_status",
        manifest["analysis_status"] == "exploratory_no_selector_or_environment_claim_approved",
        manifest["analysis_status"],
    )
    check(
        "validation_partition_not_inspected",
        manifest["validation_partition_inspected"] is False,
        manifest["validation_partition_inspected"],
    )
    check(
        "frozen_design_used",
        design_manifest["design_status"] == "frozen_before_gaia_outcome_queries",
        design_manifest["design_status"],
    )
    input_paths = {
        "design": arguments.design,
        "design_manifest": arguments.design_manifest,
        "benchmark_manifest": arguments.benchmark_manifest,
    }
    for name, path in input_paths.items():
        check(
            f"{name}_digest",
            calculate_sha256(path) == manifest["inputs"][f"{name}_sha256"],
            manifest["inputs"][f"{name}_sha256"],
        )
    output_paths = {
        "sources": arguments.sources,
        "radial_metrics": arguments.metrics,
        "field_summary": arguments.field_summary,
        "comparison": arguments.comparison,
    }
    for name, path in output_paths.items():
        check(
            f"{name}_digest",
            calculate_sha256(path) == manifest["outputs"][f"{name}_sha256"],
            manifest["outputs"][f"{name}_sha256"],
        )
    check("twenty_four_fields", len(design) == 24, len(design))
    check("twelve_pairs", design["pair_id"].nunique() == 12, design["pair_id"].nunique())
    check(
        "complete_field_summary",
        set(field_summary["field_id"]) == set(design["field_id"]),
        len(field_summary),
    )
    check("complete_radial_grid", len(metrics) == 24 * 6, len(metrics))
    check(
        "unique_field_source_associations",
        sources["field_source_association_id"].is_unique,
        len(sources),
    )
    returned_count = sum(int(item["returned_row_count"]) for item in manifest["query_records"])
    check("all_query_rows_represented", returned_count == len(sources), returned_count)
    nonempty_fields = {
        item["field_id"]
        for item in manifest["query_records"]
        if int(item["returned_row_count"]) > 0
    }
    check("source_field_set", set(sources["field_id"]) == nonempty_fields, sorted(nonempty_fields))
    check(
        "manifest_counts",
        manifest["counts"]["field_source_association_count"] == len(sources)
        and manifest["counts"]["unique_gaia_source_count"] == sources["source_id"].nunique(),
        manifest["counts"],
    )
    check(
        "all_sources_have_morphology",
        sources["radius_sersic"].notna().all(),
        int(sources["radius_sersic"].isna().sum()),
    )
    check(
        "all_sources_inside_equivalent_aperture",
        sources["equivalent_projected_radius_kpc"].between(0.0, 600.0).all(),
        float(sources["equivalent_projected_radius_kpc"].max()),
    )
    check(
        "field_counts_sum",
        int(field_summary["all_morphology_row_count"].sum()) == len(sources),
        int(field_summary["all_morphology_row_count"].sum()),
    )
    check(
        "comparison_pair_count",
        comparison["paired_density_test"]["pair_count"] == 12,
        comparison["paired_density_test"],
    )
    disagreement_count = int(
        (
            sources["selected_phase3_model_c_70_30"] != sources["selected_phase4_model_c_60_30_10"]
        ).sum()
    )
    check(
        "legacy_disagreement_count",
        comparison["legacy_rule_disagreement_count"] == disagreement_count,
        disagreement_count,
    )
    check(
        "no_clustering_claim",
        comparison["interpretation_status"]
        == "exploratory_field_variation_large_no_host_clustering_detection_claim",
        comparison["interpretation_status"],
    )
    figure_path = FIGURES_DIR / "phase1" / f"{FIGURE_NAME}.png"
    caption_path = FIGURES_DIR / "phase1" / f"{FIGURE_NAME}.md"
    check(
        "figure_caption_pair",
        figure_path.is_file() and caption_path.is_file(),
        {"figure": str(figure_path), "caption": str(caption_path)},
    )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "analysis_version": ANALYSIS_VERSION,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "counts": manifest["counts"],
        "checks": checks,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failed:
        failed_names = ", ".join(str(item["name"]) for item in failed)
        raise RuntimeError(f"Host/control comparison validation failed: {failed_names}")


if __name__ == "__main__":
    main()
