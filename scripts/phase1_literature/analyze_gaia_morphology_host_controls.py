"""Compare Gaia morphology-candidate density in frozen host and control fields."""

import argparse
import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from matplotlib.lines import Line2D
from pyvo.dal import tap
from scipy.stats import binomtest, wilcoxon

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GAIA_MORPHOLOGY_HOST_CONTROL_COMPARISON,
    GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN,
    GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_MANIFEST,
    GAIA_MORPHOLOGY_HOST_CONTROL_FIELD_SUMMARY,
    GAIA_MORPHOLOGY_HOST_CONTROL_MANIFEST,
    GAIA_MORPHOLOGY_HOST_CONTROL_METRICS,
    GAIA_MORPHOLOGY_HOST_CONTROL_SOURCES,
    VALIDATION_BENCHMARK_MANIFEST,
)
from scripts.phase1_literature.analyze_gaia_morphology_host_fields import (
    AIP_TAP_URL,
    GAIA_QUERY_COLUMNS,
    MORPHOLOGY_QUERY_COLUMNS,
    RADIAL_BIN_EDGES_KPC,
    add_derived_features,
    annulus_area_deg2,
    inherited_model_selections,
    poisson_count_interval,
    wilson_fraction_interval,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import serialize_path
from scripts.phase1_literature.synchronize_crossmatch_products import run_query
from scripts.utils.plotting import save_figure, set_style

logger = logging.getLogger(__name__)

ANALYSIS_VERSION = "gaia_morphology_host_control_v1"
FIGURE_NAME = "gaia_morphology_host_control_comparison"
COMMAND = (
    "BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python "
    "scripts/phase1_literature/analyze_gaia_morphology_host_controls.py"
)
SCAN_QUERY_COLUMNS = [
    "matched_transits",
    "visibility_periods_used",
    "astrometric_n_good_obs_al",
    "scan_direction_strength_k4",
]


def parse_arguments() -> argparse.Namespace:
    """Parse frozen design, outputs, and bounded smoke controls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN)
    parser.add_argument(
        "--design-manifest",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_MANIFEST,
    )
    parser.add_argument("--benchmark-manifest", type=Path, default=VALIDATION_BENCHMARK_MANIFEST)
    parser.add_argument("--sources-output", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_SOURCES)
    parser.add_argument("--metrics-output", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_METRICS)
    parser.add_argument(
        "--field-summary-output",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_CONTROL_FIELD_SUMMARY,
    )
    parser.add_argument(
        "--comparison-output",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_CONTROL_COMPARISON,
    )
    parser.add_argument("--manifest", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_MANIFEST)
    parser.add_argument("--limit-fields", type=int, help="Limit fields for a smoke run.")
    parser.add_argument("--skip-figure", action="store_true")
    parser.add_argument(
        "--reuse-existing-sources",
        action="store_true",
        help="Recompute local products from sources verified against the existing manifest.",
    )
    return parser.parse_args()


def build_query(field: dict[str, object]) -> str:
    """Build an outcome-complete morphology-candidate field query."""
    selected_columns = [
        *(f"g.{column}" for column in GAIA_QUERY_COLUMNS),
        *(f"g.{column}" for column in SCAN_QUERY_COLUMNS),
        *(f"c.{column}" for column in MORPHOLOGY_QUERY_COLUMNS),
    ]
    return f"""SELECT {", ".join(selected_columns)}
        FROM gaiadr3.galaxy_candidates AS c
        JOIN gaiadr3.gaia_source AS g USING (source_id)
        WHERE c.radius_sersic IS NOT NULL
          AND 1 = CONTAINS(
              POINT('ICRS', g.ra, g.dec),
              CIRCLE(
                  'ICRS', {float(field["field_ra"])}, {float(field["field_dec"])},
                  {float(field["field_radius_deg"])}
              )
          )
        ORDER BY g.source_id"""


def retrieve_sources(
    design: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Retrieve all morphology candidates and preserve field associations."""
    service = tap.TAPService(AIP_TAP_URL)
    frames = []
    query_records = []
    for field in design.to_dict("records"):
        query = build_query(field)
        started = perf_counter()
        rows = run_query(service, query, maxrec=100_000)
        elapsed_seconds = perf_counter() - started
        rows["source_id"] = rows["source_id"].map(lambda value: str(int(value)))
        field_coordinate = SkyCoord(
            float(field["field_ra"]) * u.deg,
            float(field["field_dec"]) * u.deg,
        )
        source_coordinates = SkyCoord(rows["ra"].to_numpy() * u.deg, rows["dec"].to_numpy() * u.deg)
        rows["equivalent_projected_radius_kpc"] = (
            float(field["host_distance_mpc"])
            * 1000.0
            * np.tan(field_coordinate.separation(source_coordinates).rad)
        )
        for column in [
            "field_id",
            "field_role",
            "pair_id",
            "host_rank",
            "host_name",
            "host_distance_mpc",
            "host_log_l_k",
            "luminosity_stratum",
            "latitude_stratum",
            "field_ra",
            "field_dec",
            "field_galactic_latitude_deg",
            "field_ecliptic_latitude_deg",
            "field_radius_deg",
        ]:
            rows[column] = field[column]
        rows["field_source_association_id"] = rows["source_id"].map(
            lambda source_id: f"{field['field_id']}:gaia_dr3_{source_id}"
        )
        frames.append(rows)
        query_records.append(
            {
                "field_id": field["field_id"],
                "field_role": field["field_role"],
                "returned_row_count": len(rows),
                "elapsed_seconds": elapsed_seconds,
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                "query": query,
            }
        )
        logger.info(
            "%s (%s): %d rows in %.2f seconds",
            field["field_id"],
            field["field_role"],
            len(rows),
            elapsed_seconds,
        )
    sources = pd.concat(frames, ignore_index=True)
    if sources["field_source_association_id"].duplicated().any():
        raise RuntimeError("Duplicate field-source association identifiers")
    return sources, query_records


def add_selection_states(
    sources: pd.DataFrame,
    minimum_g: float,
    maximum_g: float,
) -> pd.DataFrame:
    """Add applicability and legacy retention states after retrieval."""
    sources = add_derived_features(sources)
    sources["in_applicability_domain"] = sources["phot_g_mean_mag"].between(
        minimum_g,
        maximum_g,
        inclusive="both",
    )
    for model_name, selected in inherited_model_selections(sources).items():
        sources[f"selected_{model_name}"] = selected
    return sources


def summarize_rows(rows: pd.DataFrame, area_deg2: float) -> dict[str, object]:
    """Summarize one field or equivalent annulus with exact count intervals."""
    applicable = rows["in_applicability_domain"]
    applicable_count = int(applicable.sum())
    count_lower, count_upper = poisson_count_interval(applicable_count)
    result = {
        "all_morphology_row_count": len(rows),
        "applicability_row_count": applicable_count,
        "area_deg2": area_deg2,
        "applicability_density_per_deg2": applicable_count / area_deg2,
        "applicability_density_poisson_lower_per_deg2": count_lower / area_deg2,
        "applicability_density_poisson_upper_per_deg2": count_upper / area_deg2,
    }
    coverage_features = [
        "proper_motion_zero_significance",
        "ruwe",
        "astrometric_excess_noise",
        "ipd_frac_multi_peak",
        "phot_bp_rp_excess_factor",
    ]
    for feature in coverage_features:
        result[f"{feature}_coverage_fraction"] = (
            float(rows.loc[applicable, feature].notna().mean()) if applicable_count else None
        )
    for scan_feature in SCAN_QUERY_COLUMNS:
        result[f"median_{scan_feature}"] = (
            float(rows.loc[applicable, scan_feature].median()) if applicable_count else None
        )
    for model_name in ["phase3_model_c_70_30", "phase4_model_c_60_30_10"]:
        selected_count = int(rows.loc[applicable, f"selected_{model_name}"].sum())
        fraction = selected_count / applicable_count if applicable_count else None
        lower, upper = wilson_fraction_interval(selected_count, applicable_count)
        result[f"{model_name}_selected_count"] = selected_count
        result[f"{model_name}_selection_fraction"] = fraction
        result[f"{model_name}_selection_fraction_lower"] = lower
        result[f"{model_name}_selection_fraction_upper"] = upper
    return result


def build_metrics(
    sources: pd.DataFrame,
    design: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build full-field summaries and matched equivalent radial profiles."""
    field_summary = []
    radial_metrics = []
    for field in design.to_dict("records"):
        field_rows = sources.loc[sources["field_id"].eq(field["field_id"])]
        common = {
            key: field[key]
            for key in [
                "field_id",
                "field_role",
                "pair_id",
                "host_name",
                "host_log_l_k",
                "luminosity_stratum",
                "latitude_stratum",
                "field_galactic_latitude_deg",
                "field_ecliptic_latitude_deg",
            ]
        }
        full_area = annulus_area_deg2(
            float(field["host_distance_mpc"]),
            0.0,
            RADIAL_BIN_EDGES_KPC[-1],
        )
        field_summary.append({**common, **summarize_rows(field_rows, full_area)})
        for inner_kpc, outer_kpc in zip(
            RADIAL_BIN_EDGES_KPC[:-1],
            RADIAL_BIN_EDGES_KPC[1:],
            strict=True,
        ):
            in_annulus = field_rows["equivalent_projected_radius_kpc"].ge(inner_kpc) & field_rows[
                "equivalent_projected_radius_kpc"
            ].lt(outer_kpc)
            area = annulus_area_deg2(
                float(field["host_distance_mpc"]),
                inner_kpc,
                outer_kpc,
            )
            radial_metrics.append(
                {
                    **common,
                    "inner_equivalent_radius_kpc": inner_kpc,
                    "outer_equivalent_radius_kpc": outer_kpc,
                    **summarize_rows(field_rows.loc[in_annulus], area),
                }
            )
    return pd.DataFrame(field_summary), pd.DataFrame(radial_metrics)


def build_comparison(sources: pd.DataFrame, field_summary: pd.DataFrame) -> dict[str, object]:
    """Build aggregate and paired results without promoting a clustering claim."""
    role_results = {}
    for field_role, rows in field_summary.groupby("field_role"):
        row_count = int(rows["applicability_row_count"].sum())
        area_deg2 = float(rows["area_deg2"].sum())
        role_result = {
            "field_count": len(rows),
            "applicability_row_count": row_count,
            "area_deg2": area_deg2,
            "density_per_deg2": row_count / area_deg2,
        }
        for model_name in ["phase3_model_c_70_30", "phase4_model_c_60_30_10"]:
            selected_count = int(rows[f"{model_name}_selected_count"].sum())
            role_result[f"{model_name}_selected_count"] = selected_count
            role_result[f"{model_name}_selection_fraction"] = selected_count / row_count
        role_results[str(field_role)] = role_result

    paired_density = field_summary.pivot(
        index="pair_id",
        columns="field_role",
        values="applicability_density_per_deg2",
    )
    density_difference = paired_density["host"] - paired_density["control"]
    positive_pair_count = int(density_difference.gt(0.0).sum())
    sign_test = binomtest(positive_pair_count, len(density_difference), 0.5)
    signed_rank = wilcoxon(density_difference, alternative="two-sided", zero_method="wilcox")

    scan_matching = {}
    for feature in SCAN_QUERY_COLUMNS:
        paired_feature = field_summary.pivot(
            index="pair_id",
            columns="field_role",
            values=f"median_{feature}",
        ).dropna()
        absolute_difference = (paired_feature["host"] - paired_feature["control"]).abs()
        scan_matching[feature] = {
            "complete_pair_count": len(paired_feature),
            "median_absolute_difference": float(absolute_difference.median()),
            "maximum_absolute_difference": float(absolute_difference.max()),
        }

    stratum_results = []
    for (luminosity_stratum, latitude_stratum, field_role), rows in field_summary.groupby(
        ["luminosity_stratum", "latitude_stratum", "field_role"],
        sort=True,
    ):
        row_count = int(rows["applicability_row_count"].sum())
        area_deg2 = float(rows["area_deg2"].sum())
        stratum_results.append(
            {
                "luminosity_stratum": luminosity_stratum,
                "latitude_stratum": latitude_stratum,
                "field_role": field_role,
                "field_count": len(rows),
                "applicability_row_count": row_count,
                "area_deg2": area_deg2,
                "density_per_deg2": row_count / area_deg2,
            }
        )
    return {
        "interpretation_status": (
            "exploratory_field_variation_large_no_host_clustering_detection_claim"
        ),
        "role_results": role_results,
        "paired_density_test": {
            "pair_count": len(density_difference),
            "host_density_higher_pair_count": positive_pair_count,
            "median_host_minus_control_density_per_deg2": float(density_difference.median()),
            "mean_host_minus_control_density_per_deg2": float(density_difference.mean()),
            "two_sided_sign_test_p_value": float(sign_test.pvalue),
            "wilcoxon_signed_rank_statistic": float(signed_rank.statistic),
            "wilcoxon_signed_rank_two_sided_p_value": float(signed_rank.pvalue),
        },
        "legacy_rule_disagreement_count": int(
            (
                sources["selected_phase3_model_c_70_30"]
                != sources["selected_phase4_model_c_60_30_10"]
            ).sum()
        ),
        "zero_morphology_control_field_count": int(
            field_summary.loc[
                field_summary["field_role"].eq("control"),
                "applicability_row_count",
            ]
            .eq(0)
            .sum()
        ),
        "scan_matching": scan_matching,
        "stratum_results": stratum_results,
    }


def plot_comparison(field_summary: pd.DataFrame) -> None:
    """Plot paired full-field density and legacy 70/30 retention fraction."""
    set_style()
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 8,
            "axes.labelsize": 9,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.grid": False,
        }
    )
    figure, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))
    colors = {"low": "#0072B2", "middle": "#E69F00", "high": "#009E73"}
    line_styles = {"30_to_50_deg": "-", "50_to_90_deg": "--"}
    for _, pair in field_summary.groupby("pair_id", sort=True):
        pair = pair.set_index("field_role").loc[["control", "host"]]
        color = colors[str(pair["luminosity_stratum"].iloc[0])]
        line_style = line_styles[str(pair["latitude_stratum"].iloc[0])]
        density = pair["applicability_density_per_deg2"].to_numpy()
        density_error = np.vstack(
            [
                density - pair["applicability_density_poisson_lower_per_deg2"].to_numpy(),
                pair["applicability_density_poisson_upper_per_deg2"].to_numpy() - density,
            ]
        )
        density_error = np.clip(density_error, 0.0, None)
        axes[0].errorbar(
            [0, 1],
            density,
            yerr=density_error,
            color=color,
            linestyle=line_style,
            marker="o",
            linewidth=1.0,
            alpha=0.8,
            capsize=2,
        )
        fraction = pair["phase3_model_c_70_30_selection_fraction"].to_numpy()
        fraction_error = np.vstack(
            [
                fraction - pair["phase3_model_c_70_30_selection_fraction_lower"].to_numpy(),
                pair["phase3_model_c_70_30_selection_fraction_upper"].to_numpy() - fraction,
            ]
        )
        fraction_error = np.clip(fraction_error, 0.0, None)
        axes[1].errorbar(
            [0, 1],
            fraction,
            yerr=fraction_error,
            color=color,
            linestyle=line_style,
            marker="o",
            linewidth=1.0,
            alpha=0.8,
            capsize=2,
        )
    for axis in axes:
        axis.set_xticks([0, 1], ["Paired control", "Host field"])
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Morphology candidates per square degree")
    axes[1].set_ylabel("Legacy 70/30 retention fraction")
    axes[1].set_ylim(-0.05, 1.05)
    axes[0].text(-0.13, 1.03, "A", transform=axes[0].transAxes, fontweight="bold")
    axes[1].text(-0.13, 1.03, "B", transform=axes[1].transAxes, fontweight="bold")
    handles = [
        Line2D([0], [0], color=colors[name], marker="o", label=f"{name} K luminosity")
        for name in ["low", "middle", "high"]
    ]
    handles.extend(
        [
            Line2D(
                [0],
                [0],
                color="black",
                linestyle="-",
                label="30–50° absolute Galactic latitude",
            ),
            Line2D(
                [0],
                [0],
                color="black",
                linestyle="--",
                label="50–90° absolute Galactic latitude",
            ),
        ]
    )
    axes[0].legend(handles=handles, frameon=False, fontsize=6)
    figure.tight_layout()
    save_figure(
        figure,
        FIGURE_NAME,
        phase=1,
        script_path="scripts/phase1_literature/analyze_gaia_morphology_host_controls.py",
        command=COMMAND,
        data_source="data/literature/validation/gaia_morphology_host_control_field_summary.csv",
        description=(
            "Paired full-field results for 12 predefined hosts and 12 geometric controls. "
            "Panel A shows morphology-candidate density with exact 95% Poisson intervals. "
            "Panel B shows the legacy 70/30 rule's retention fraction with 95% "
            "Wilson intervals. Colors encode K-band luminosity strata and line styles "
            "encode absolute Galactic-latitude strata."
        ),
        title="Gaia morphology candidates in paired host and control fields",
    )
    plt.close(figure)


def main() -> None:
    """Query the frozen design, calculate comparisons, and record provenance."""
    arguments = parse_arguments()
    design = pd.read_csv(arguments.design)
    design_manifest = json.loads(arguments.design_manifest.read_text(encoding="utf-8"))
    if design_manifest["design_status"] != "frozen_before_gaia_outcome_queries":
        raise RuntimeError("The field design was not frozen before outcome queries")
    if calculate_sha256(arguments.design) != design_manifest["output_sha256"]:
        raise RuntimeError("The frozen field design digest changed")
    if arguments.limit_fields is not None:
        if arguments.limit_fields <= 0:
            raise ValueError("--limit-fields must be positive")
        design = design.head(arguments.limit_fields).copy()
    benchmark_manifest = json.loads(arguments.benchmark_manifest.read_text(encoding="utf-8"))
    minimum_g = float(benchmark_manifest["applicability_domain"]["minimum_phot_g_mean_mag"])
    maximum_g = float(benchmark_manifest["applicability_domain"]["maximum_phot_g_mean_mag"])
    data_retrieval_mode = "remote_queries"
    if arguments.reuse_existing_sources:
        if not arguments.manifest.is_file() or not arguments.sources_output.is_file():
            raise FileNotFoundError("Existing sources and manifest are required for reuse")
        previous_manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
        expected_source_digest = previous_manifest["outputs"]["sources_sha256"]
        if calculate_sha256(arguments.sources_output) != expected_source_digest:
            raise RuntimeError("Existing source digest does not match the prior manifest")
        sources = pd.read_csv(arguments.sources_output, dtype={"source_id": str})
        query_records = previous_manifest["query_records"]
        expected_nonempty_fields = {
            item["field_id"] for item in query_records if int(item["returned_row_count"]) > 0
        }
        if set(sources["field_id"]) != expected_nonempty_fields:
            raise RuntimeError("Existing sources do not represent the current design")
        data_retrieval_mode = "verified_existing_sources"
    else:
        sources, query_records = retrieve_sources(design)
    sources = add_selection_states(sources, minimum_g, maximum_g)
    field_summary, metrics = build_metrics(sources, design)
    comparison = build_comparison(sources, field_summary)
    arguments.sources_output.parent.mkdir(parents=True, exist_ok=True)
    sources.to_csv(arguments.sources_output, index=False)
    metrics.to_csv(arguments.metrics_output, index=False)
    field_summary.to_csv(arguments.field_summary_output, index=False)
    arguments.comparison_output.write_text(
        json.dumps(comparison, indent=2) + "\n",
        encoding="utf-8",
    )
    if not arguments.skip_figure and arguments.limit_fields is None:
        plot_comparison(field_summary)
    manifest = {
        "analysis_version": ANALYSIS_VERSION,
        "generated_utc": datetime.now(UTC).isoformat(),
        "analysis_status": "exploratory_no_selector_or_environment_claim_approved",
        "validation_partition_inspected": False,
        "endpoint": AIP_TAP_URL,
        "smoke_limit_fields": arguments.limit_fields,
        "data_retrieval_mode": data_retrieval_mode,
        "inputs": {
            "design": serialize_path(arguments.design),
            "design_sha256": calculate_sha256(arguments.design),
            "design_manifest": serialize_path(arguments.design_manifest),
            "design_manifest_sha256": calculate_sha256(arguments.design_manifest),
            "benchmark_manifest": serialize_path(arguments.benchmark_manifest),
            "benchmark_manifest_sha256": calculate_sha256(arguments.benchmark_manifest),
        },
        "query_records": query_records,
        "outputs": {
            "sources": serialize_path(arguments.sources_output),
            "sources_sha256": calculate_sha256(arguments.sources_output),
            "radial_metrics": serialize_path(arguments.metrics_output),
            "radial_metrics_sha256": calculate_sha256(arguments.metrics_output),
            "field_summary": serialize_path(arguments.field_summary_output),
            "field_summary_sha256": calculate_sha256(arguments.field_summary_output),
            "comparison": serialize_path(arguments.comparison_output),
            "comparison_sha256": calculate_sha256(arguments.comparison_output),
        },
        "counts": {
            "field_count": len(design),
            "host_field_count": int(design["field_role"].eq("host").sum()),
            "control_field_count": int(design["field_role"].eq("control").sum()),
            "field_source_association_count": len(sources),
            "unique_gaia_source_count": sources["source_id"].nunique(),
            "radial_metric_row_count": len(metrics),
        },
    }
    arguments.manifest.parent.mkdir(parents=True, exist_ok=True)
    arguments.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
