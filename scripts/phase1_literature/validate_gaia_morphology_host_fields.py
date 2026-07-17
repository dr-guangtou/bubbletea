"""Validate the fixed Gaia morphology-galaxy host-field stress artifacts."""

import argparse
import json
import sys
from math import radians
from pathlib import Path

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    EXTRAGALACTIC_REFERENCE_SOURCES,
    FIGURES_DIR,
    GAIA_MORPHOLOGY_HOST_FIELD_MANIFEST,
    GAIA_MORPHOLOGY_HOST_FIELD_RADIAL_METRICS,
    GAIA_MORPHOLOGY_HOST_FIELD_SOURCES,
    GAIA_MORPHOLOGY_HOST_FIELD_VALIDATION,
    GALAXY_SAMPLE_CSV,
    VALIDATION_BENCHMARK_MANIFEST,
)
from scripts.phase1_literature.analyze_gaia_morphology_host_fields import (
    ANALYSIS_VERSION,
    FIGURE_NAME,
    HOST_COUNT,
    RADIAL_BIN_EDGES_KPC,
    select_hosts,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256


def parse_arguments() -> argparse.Namespace:
    """Parse host-field artifact paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-catalog", type=Path, default=GALAXY_SAMPLE_CSV)
    parser.add_argument("--benchmark-manifest", type=Path, default=VALIDATION_BENCHMARK_MANIFEST)
    parser.add_argument("--source-registry", type=Path, default=EXTRAGALACTIC_REFERENCE_SOURCES)
    parser.add_argument("--sources", type=Path, default=GAIA_MORPHOLOGY_HOST_FIELD_SOURCES)
    parser.add_argument(
        "--radial-metrics",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_FIELD_RADIAL_METRICS,
    )
    parser.add_argument("--manifest", type=Path, default=GAIA_MORPHOLOGY_HOST_FIELD_MANIFEST)
    parser.add_argument("--output", type=Path, default=GAIA_MORPHOLOGY_HOST_FIELD_VALIDATION)
    return parser.parse_args()


def main() -> None:
    """Run deterministic provenance, geometry, and status checks."""
    arguments = parse_arguments()
    sources = pd.read_csv(arguments.sources, dtype={"source_id": str})
    metrics = pd.read_csv(arguments.radial_metrics)
    manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
    expected_hosts = select_hosts(arguments.host_catalog, None)
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("analysis_version", manifest["analysis_version"] == ANALYSIS_VERSION, ANALYSIS_VERSION)
    check(
        "exploratory_status",
        manifest["analysis_status"] == "exploratory_no_selector_or_radial_threshold_approved",
        manifest["analysis_status"],
    )
    check(
        "validation_partition_not_inspected",
        manifest["validation_partition_inspected"] is False,
        manifest["validation_partition_inspected"],
    )
    check("production_host_count", manifest["counts"]["host_count"] == HOST_COUNT, HOST_COUNT)
    check(
        "fixed_host_fixture",
        manifest["hosts"]
        == expected_hosts[
            ["rank", "objname", "ra", "dec", "glat", "dist_best", "maximum_angular_radius_deg"]
        ].to_dict("records"),
        [item["objname"] for item in manifest["hosts"]],
    )
    check(
        "host_catalog_digest",
        calculate_sha256(arguments.host_catalog) == manifest["inputs"]["host_catalog_sha256"],
        manifest["inputs"]["host_catalog_sha256"],
    )
    check(
        "benchmark_manifest_digest",
        calculate_sha256(arguments.benchmark_manifest)
        == manifest["inputs"]["benchmark_manifest_sha256"],
        manifest["inputs"]["benchmark_manifest_sha256"],
    )
    check(
        "source_registry_digest",
        calculate_sha256(arguments.source_registry) == manifest["inputs"]["source_registry_sha256"],
        manifest["inputs"]["source_registry_sha256"],
    )
    check(
        "sources_digest",
        calculate_sha256(arguments.sources) == manifest["outputs"]["sources_sha256"],
        manifest["outputs"]["sources_sha256"],
    )
    check(
        "radial_metrics_digest",
        calculate_sha256(arguments.radial_metrics) == manifest["outputs"]["radial_metrics_sha256"],
        manifest["outputs"]["radial_metrics_sha256"],
    )
    check(
        "unique_host_source_associations",
        sources["host_source_association_id"].is_unique,
        len(sources),
    )
    check(
        "all_sources_have_morphology",
        sources["radius_sersic"].notna().all(),
        int(sources["radius_sersic"].isna().sum()),
    )
    check(
        "all_sources_inside_aperture",
        sources["projected_radius_kpc"].between(0.0, RADIAL_BIN_EDGES_KPC[-1]).all(),
        float(sources["projected_radius_kpc"].max()),
    )
    query_row_count = sum(int(item["returned_row_count"]) for item in manifest["query_records"])
    check("query_rows_represented", query_row_count == len(sources), query_row_count)
    check(
        "manifest_association_count",
        manifest["counts"]["host_source_association_count"] == len(sources),
        len(sources),
    )
    check(
        "manifest_unique_source_count",
        manifest["counts"]["unique_gaia_source_count"] == sources["source_id"].nunique(),
        sources["source_id"].nunique(),
    )
    expected_metric_rows = HOST_COUNT * (len(RADIAL_BIN_EDGES_KPC) - 1)
    check("complete_radial_metric_grid", len(metrics) == expected_metric_rows, len(metrics))
    observed_edges = set(zip(metrics["inner_radius_kpc"], metrics["outer_radius_kpc"], strict=True))
    expected_edges = set(zip(RADIAL_BIN_EDGES_KPC[:-1], RADIAL_BIN_EDGES_KPC[1:], strict=True))
    check("declared_radial_edges", observed_edges == expected_edges, sorted(observed_edges))
    check(
        "radial_counts_sum_to_associations",
        int(metrics["all_morphology_row_count"].sum()) == len(sources),
        int(metrics["all_morphology_row_count"].sum()),
    )
    for model_name in ["phase3_model_c_70_30", "phase4_model_c_60_30_10"]:
        selected_column = f"selected_{model_name}"
        check(
            f"{model_name}_selection_is_boolean",
            set(sources[selected_column].dropna().unique()).issubset({True, False}),
            sorted(sources[selected_column].dropna().unique().tolist()),
        )
        check(
            f"{model_name}_selected_rows_are_applicable",
            sources.loc[sources[selected_column], "in_applicability_domain"].all(),
            int(sources[selected_column].sum()),
        )

    host_coordinates = SkyCoord(
        sources["host_ra"].to_numpy() * u.deg, sources["host_dec"].to_numpy() * u.deg
    )
    source_coordinates = SkyCoord(
        sources["ra"].to_numpy() * u.deg, sources["dec"].to_numpy() * u.deg
    )
    recomputed_radius = (
        sources["host_distance_mpc"].to_numpy()
        * 1000.0
        * np.tan(host_coordinates.separation(source_coordinates).rad)
    )
    maximum_geometry_difference = float(
        np.max(np.abs(recomputed_radius - sources["projected_radius_kpc"].to_numpy()))
    )
    check(
        "projected_geometry_recomputed",
        maximum_geometry_difference < radians(1.0 / 3_600_000.0),
        maximum_geometry_difference,
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
        "counts": {
            "host_count": sources["host_name"].nunique(),
            "host_source_association_count": len(sources),
            "unique_gaia_source_count": sources["source_id"].nunique(),
            "radial_metric_row_count": len(metrics),
        },
        "checks": checks,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failed:
        failed_names = ", ".join(str(item["name"]) for item in failed)
        raise RuntimeError(f"Gaia morphology host-field validation failed: {failed_names}")


if __name__ == "__main__":
    main()
