"""Measure Gaia morphology-candidate behavior in a predefined three-host test.

Every source with a published Gaia DR3 Sersic fit is retrieved before the two
historical selectors are evaluated. This exploratory analysis does not tune or
approve a selector or radial threshold.
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from math import atan, degrees, pi, radians
from pathlib import Path
from time import perf_counter

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from matplotlib.lines import Line2D
from pyvo.dal import tap
from scipy.stats import chi2

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    EXTRAGALACTIC_REFERENCE_SOURCES,
    GAIA_MORPHOLOGY_HOST_FIELD_MANIFEST,
    GAIA_MORPHOLOGY_HOST_FIELD_RADIAL_METRICS,
    GAIA_MORPHOLOGY_HOST_FIELD_SOURCES,
    GALAXY_SAMPLE_CSV,
    VALIDATION_BENCHMARK_MANIFEST,
)
from scripts.phase1_literature.analyze_selector_development import (
    add_derived_features,
    inherited_model_selections,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import serialize_path
from scripts.phase1_literature.synchronize_crossmatch_products import run_query
from scripts.utils.plotting import save_figure, set_style

logger = logging.getLogger(__name__)

ANALYSIS_VERSION = "gaia_morphology_host_field_v1"
AIP_TAP_URL = "https://gaia.aip.de/tap"
RADIAL_BIN_EDGES_KPC = [0.0, 25.0, 50.0, 100.0, 150.0, 300.0, 600.0]
LOCAL_COMPARISON_MINIMUM_KPC = 300.0
HOST_COUNT = 3
MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG = 30.0
MINIMUM_DISTANCE_MPC = 15.0
MAXIMUM_DISTANCE_MPC = 25.0
MAXIMUM_ANGULAR_RADIUS_DEG = 2.1
FIGURE_NAME = "gaia_morphology_host_field_stress"
COMMAND = (
    "BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python "
    "scripts/phase1_literature/analyze_gaia_morphology_host_fields.py"
)

GAIA_QUERY_COLUMNS = [
    "source_id",
    "ra",
    "dec",
    "phot_g_mean_mag",
    "phot_bp_mean_mag",
    "phot_rp_mean_mag",
    "parallax",
    "parallax_error",
    "pmra",
    "pmra_error",
    "pmdec",
    "pmdec_error",
    "pmra_pmdec_corr",
    "astrometric_excess_noise",
    "astrometric_excess_noise_sig",
    "ruwe",
    "ipd_frac_multi_peak",
    "ipd_frac_odd_win",
    "phot_bp_rp_excess_factor",
]
MORPHOLOGY_QUERY_COLUMNS = [
    "radius_sersic",
    "n_sersic",
    "flags_sersic",
    "classprob_dsc_combmod_galaxy",
    "classprob_dsc_combmod_quasar",
]


def parse_arguments() -> argparse.Namespace:
    """Parse host, output, and bounded-run controls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-catalog", type=Path, default=GALAXY_SAMPLE_CSV)
    parser.add_argument("--benchmark-manifest", type=Path, default=VALIDATION_BENCHMARK_MANIFEST)
    parser.add_argument("--source-registry", type=Path, default=EXTRAGALACTIC_REFERENCE_SOURCES)
    parser.add_argument("--sources-output", type=Path, default=GAIA_MORPHOLOGY_HOST_FIELD_SOURCES)
    parser.add_argument(
        "--radial-output",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_FIELD_RADIAL_METRICS,
    )
    parser.add_argument("--manifest", type=Path, default=GAIA_MORPHOLOGY_HOST_FIELD_MANIFEST)
    parser.add_argument("--limit-hosts", type=int, help="Limit hosts for a measured smoke run.")
    parser.add_argument(
        "--maximum-radius-kpc",
        type=float,
        default=RADIAL_BIN_EDGES_KPC[-1],
        help="Bound the aperture for a measured smoke run.",
    )
    parser.add_argument("--skip-figure", action="store_true")
    return parser.parse_args()


def angular_radius_deg(distance_mpc: float, radius_kpc: float) -> float:
    """Convert projected physical radius to an angular radius."""
    return degrees(atan(radius_kpc / (distance_mpc * 1000.0)))


def select_hosts(host_catalog: Path, limit_hosts: int | None) -> pd.DataFrame:
    """Select the predefined ranked host sample without outcome information."""
    hosts = pd.read_csv(host_catalog)
    hosts["maximum_angular_radius_deg"] = hosts["dist_best"].map(
        lambda value: angular_radius_deg(float(value), RADIAL_BIN_EDGES_KPC[-1])
    )
    eligible = hosts.loc[
        hosts["glat"].abs().ge(MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG)
        & hosts["dist_best"].between(MINIMUM_DISTANCE_MPC, MAXIMUM_DISTANCE_MPC)
        & hosts["maximum_angular_radius_deg"].le(MAXIMUM_ANGULAR_RADIUS_DEG)
    ].sort_values(["rank", "objname"])
    selected_count = HOST_COUNT if limit_hosts is None else min(HOST_COUNT, limit_hosts)
    if selected_count <= 0:
        raise ValueError("--limit-hosts must be positive")
    selected = eligible.head(selected_count).copy()
    if len(selected) != selected_count:
        raise RuntimeError("The host catalog does not contain enough eligible test rows")
    return selected


def build_query(host: dict[str, object], radius_kpc: float) -> tuple[str, float]:
    """Build one unfiltered Gaia morphology-galaxy cone query."""
    radius_deg = angular_radius_deg(float(host["dist_best"]), radius_kpc)
    selected_columns = [
        *(f"g.{column}" for column in GAIA_QUERY_COLUMNS),
        *(f"c.{column}" for column in MORPHOLOGY_QUERY_COLUMNS),
    ]
    query = f"""SELECT {", ".join(selected_columns)}
        FROM gaiadr3.galaxy_candidates AS c
        JOIN gaiadr3.gaia_source AS g USING (source_id)
        WHERE c.radius_sersic IS NOT NULL
          AND 1 = CONTAINS(
              POINT('ICRS', g.ra, g.dec),
              CIRCLE('ICRS', {float(host["ra"])}, {float(host["dec"])}, {radius_deg})
          )
        ORDER BY g.source_id"""
    return query, radius_deg


def retrieve_host_sources(
    hosts: pd.DataFrame,
    maximum_radius_kpc: float,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Retrieve morphology sources and retain one-to-many host associations."""
    service = tap.TAPService(AIP_TAP_URL)
    frames = []
    query_records = []
    for host in hosts.to_dict("records"):
        query, radius_deg = build_query(host, maximum_radius_kpc)
        started = perf_counter()
        rows = run_query(service, query, maxrec=100_000)
        elapsed_seconds = perf_counter() - started
        rows["source_id"] = rows["source_id"].map(lambda value: str(int(value)))
        host_coordinate = SkyCoord(float(host["ra"]) * u.deg, float(host["dec"]) * u.deg)
        source_coordinates = SkyCoord(rows["ra"].to_numpy() * u.deg, rows["dec"].to_numpy() * u.deg)
        separation_radians = host_coordinate.separation(source_coordinates).rad
        rows["projected_radius_kpc"] = (
            float(host["dist_best"]) * 1000.0 * np.tan(separation_radians)
        )
        rows["host_rank"] = int(host["rank"])
        rows["host_name"] = str(host["objname"])
        rows["host_ra"] = float(host["ra"])
        rows["host_dec"] = float(host["dec"])
        rows["host_glat"] = float(host["glat"])
        rows["host_distance_mpc"] = float(host["dist_best"])
        rows["host_source_association_id"] = rows["source_id"].map(
            lambda source_id: f"host_rank_{int(host['rank'])}:gaia_dr3_{source_id}"
        )
        frames.append(rows)
        query_records.append(
            {
                "host_rank": int(host["rank"]),
                "host_name": str(host["objname"]),
                "maximum_radius_kpc": maximum_radius_kpc,
                "angular_radius_deg": radius_deg,
                "returned_row_count": len(rows),
                "elapsed_seconds": elapsed_seconds,
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                "query": query,
            }
        )
        logger.info(
            "%s: retrieved %d morphology sources in %.2f seconds",
            host["objname"],
            len(rows),
            elapsed_seconds,
        )
    combined = pd.concat(frames, ignore_index=True)
    if combined["host_source_association_id"].duplicated().any():
        raise RuntimeError("Duplicate host-source association identifiers")
    return combined, query_records


def annulus_area_deg2(distance_mpc: float, inner_kpc: float, outer_kpc: float) -> float:
    """Return the exact small-circle annulus area in square degrees."""
    inner_radians = radians(angular_radius_deg(distance_mpc, inner_kpc))
    outer_radians = radians(angular_radius_deg(distance_mpc, outer_kpc))
    steradians = 2.0 * pi * (np.cos(inner_radians) - np.cos(outer_radians))
    return float(steradians * (180.0 / pi) ** 2)


def radial_edges(maximum_radius_kpc: float) -> list[float]:
    """Return declared bin edges truncated at a bounded smoke radius."""
    if maximum_radius_kpc <= 0.0 or maximum_radius_kpc > RADIAL_BIN_EDGES_KPC[-1]:
        raise ValueError("--maximum-radius-kpc must be in (0, 600]")
    edges = [value for value in RADIAL_BIN_EDGES_KPC if value < maximum_radius_kpc]
    return [*edges, float(maximum_radius_kpc)]


def poisson_count_interval(count: int, confidence: float = 0.95) -> tuple[float, float]:
    """Return an exact central Poisson confidence interval."""
    alpha = 1.0 - confidence
    lower = 0.0 if count == 0 else 0.5 * chi2.ppf(alpha / 2.0, 2 * count)
    upper = 0.5 * chi2.ppf(1.0 - alpha / 2.0, 2 * (count + 1))
    return float(lower), float(upper)


def wilson_fraction_interval(
    selected_count: int,
    total_count: int,
    z_score: float = 1.959963984540054,
) -> tuple[float | None, float | None]:
    """Return a two-sided 95% Wilson binomial interval."""
    if total_count == 0:
        return None, None
    fraction = selected_count / total_count
    denominator = 1.0 + z_score**2 / total_count
    center = (fraction + z_score**2 / (2.0 * total_count)) / denominator
    half_width = (
        z_score
        * np.sqrt(fraction * (1.0 - fraction) / total_count + z_score**2 / (4.0 * total_count**2))
        / denominator
    )
    return float(center - half_width), float(center + half_width)


def build_radial_metrics(
    sources: pd.DataFrame,
    minimum_g: float,
    maximum_g: float,
    maximum_radius_kpc: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate density, feature coverage, and historical acceptance."""
    sources = add_derived_features(sources)
    sources["in_applicability_domain"] = sources["phot_g_mean_mag"].between(
        minimum_g,
        maximum_g,
        inclusive="both",
    )
    selections = inherited_model_selections(sources)
    for model_name, selected in selections.items():
        sources[f"selected_{model_name}"] = selected

    metrics = []
    edges = radial_edges(maximum_radius_kpc)
    for host_name, host_rows in sources.groupby("host_name", sort=False):
        distance_mpc = float(host_rows["host_distance_mpc"].iloc[0])
        for inner_kpc, outer_kpc in zip(edges[:-1], edges[1:], strict=True):
            annulus = host_rows["projected_radius_kpc"].ge(inner_kpc) & host_rows[
                "projected_radius_kpc"
            ].lt(outer_kpc)
            rows = host_rows.loc[annulus]
            applicable = rows["in_applicability_domain"]
            applicable_count = int(applicable.sum())
            area_deg2 = annulus_area_deg2(distance_mpc, inner_kpc, outer_kpc)
            count_lower, count_upper = poisson_count_interval(applicable_count)
            density = applicable_count / area_deg2
            result = {
                "host_rank": int(host_rows["host_rank"].iloc[0]),
                "host_name": host_name,
                "host_distance_mpc": distance_mpc,
                "inner_radius_kpc": inner_kpc,
                "outer_radius_kpc": outer_kpc,
                "area_deg2": area_deg2,
                "all_morphology_row_count": len(rows),
                "applicability_row_count": applicable_count,
                "applicability_density_per_deg2": density,
                "applicability_density_poisson_lower_per_deg2": count_lower / area_deg2,
                "applicability_density_poisson_upper_per_deg2": count_upper / area_deg2,
                "median_phot_g_mean_mag": (
                    float(rows.loc[applicable, "phot_g_mean_mag"].median())
                    if applicable_count
                    else None
                ),
                "astrometry_coverage_fraction": (
                    float(rows.loc[applicable, "proper_motion_zero_significance"].notna().mean())
                    if applicable_count
                    else None
                ),
            }
            coverage_features = [
                "astrometric_excess_noise",
                "astrometric_excess_noise_sig",
                "ruwe",
                "ipd_frac_multi_peak",
                "ipd_frac_odd_win",
                "phot_bp_rp_excess_factor",
            ]
            for feature in coverage_features:
                result[f"{feature}_coverage_fraction"] = (
                    float(rows.loc[applicable, feature].notna().mean())
                    if applicable_count
                    else None
                )
            for model_name in selections:
                selected_count = int(rows.loc[applicable, f"selected_{model_name}"].sum())
                result[f"{model_name}_selected_count"] = selected_count
                result[f"{model_name}_selection_fraction"] = (
                    selected_count / applicable_count if applicable_count else None
                )
                interval_lower, interval_upper = wilson_fraction_interval(
                    selected_count,
                    applicable_count,
                )
                result[f"{model_name}_selection_fraction_lower"] = interval_lower
                result[f"{model_name}_selection_fraction_upper"] = interval_upper
            metrics.append(result)
    return sources, pd.DataFrame(metrics).sort_values(["host_rank", "inner_radius_kpc"])


def plot_metrics(metrics: pd.DataFrame) -> None:
    """Plot host-centric density and historical baseline acceptance."""
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
    host_styles = [
        ("#0072B2", "o", "-"),
        ("#D55E00", "s", "--"),
        ("#009E73", "^", ":"),
    ]
    for (host_name, host_rows), (color, marker, line_style) in zip(
        metrics.groupby("host_name", sort=False), host_styles, strict=True
    ):
        radius = np.sqrt(host_rows["inner_radius_kpc"] * host_rows["outer_radius_kpc"])
        radius = radius.mask(radius.eq(0.0), host_rows["outer_radius_kpc"] / 2.0)
        density = host_rows["applicability_density_per_deg2"].to_numpy()
        density_error = np.vstack(
            [
                density - host_rows["applicability_density_poisson_lower_per_deg2"].to_numpy(),
                host_rows["applicability_density_poisson_upper_per_deg2"].to_numpy() - density,
            ]
        )
        axes[0].errorbar(
            radius,
            density,
            yerr=density_error,
            marker=marker,
            linestyle=line_style,
            linewidth=1.2,
            capsize=2,
            color=color,
            label=host_name,
        )
        phase3_fraction = host_rows["phase3_model_c_70_30_selection_fraction"].to_numpy()
        phase3_error = np.vstack(
            [
                phase3_fraction
                - host_rows["phase3_model_c_70_30_selection_fraction_lower"].to_numpy(),
                host_rows["phase3_model_c_70_30_selection_fraction_upper"].to_numpy()
                - phase3_fraction,
            ]
        )
        phase4_fraction = host_rows["phase4_model_c_60_30_10_selection_fraction"].to_numpy()
        phase4_error = np.vstack(
            [
                phase4_fraction
                - host_rows["phase4_model_c_60_30_10_selection_fraction_lower"].to_numpy(),
                host_rows["phase4_model_c_60_30_10_selection_fraction_upper"].to_numpy()
                - phase4_fraction,
            ]
        )
        axes[1].errorbar(
            radius * 1.03,
            phase3_fraction,
            yerr=phase3_error,
            marker=marker,
            linestyle="-",
            linewidth=1.2,
            capsize=2,
            color=color,
            label=f"{host_name}: legacy 70/30",
        )
        axes[1].errorbar(
            radius,
            phase4_fraction,
            yerr=phase4_error,
            marker=marker,
            markerfacecolor="white",
            linestyle="--",
            linewidth=1.2,
            capsize=2,
            color=color,
        )
    axes[0].set_ylabel("Morphology candidates per square degree")
    axes[1].set_ylabel("Historical selector acceptance fraction")
    axes[1].set_ylim(-0.05, 1.05)
    for axis in axes:
        axis.set_xlabel("Projected host-centric radius (kpc)")
        axis.set_xscale("log")
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].text(-0.14, 1.03, "A", transform=axes[0].transAxes, fontweight="bold")
    axes[1].text(-0.14, 1.03, "B", transform=axes[1].transAxes, fontweight="bold")
    host_handles = [
        Line2D(
            [0],
            [0],
            color=color,
            marker=marker,
            linestyle=line_style,
            label=host_name,
        )
        for host_name, (color, marker, line_style) in zip(
            metrics["host_name"].drop_duplicates(), host_styles, strict=True
        )
    ]
    phase_handles = [
        Line2D([0], [0], color="black", marker="o", linestyle="-", label="Legacy 70/30"),
        Line2D(
            [0],
            [0],
            color="black",
            marker="o",
            markerfacecolor="white",
            linestyle="--",
            label="Legacy 60/30/10 (offset)",
        ),
    ]
    axes[0].legend(handles=host_handles, frameon=False, loc="upper right")
    host_legend = axes[1].legend(handles=host_handles, frameon=False, loc="lower right")
    axes[1].add_artist(host_legend)
    axes[1].legend(handles=phase_handles, frameon=False, loc="lower left")
    figure.tight_layout()
    save_figure(
        figure,
        FIGURE_NAME,
        phase=1,
        script_path="scripts/phase1_literature/analyze_gaia_morphology_host_fields.py",
        command=COMMAND,
        data_source="data/literature/validation/gaia_morphology_host_field_radial_metrics.csv",
        description=(
            "Exploratory profiles for the fixed three-host Gaia DR3 morphology-candidate "
            "test sample (814 host-source associations). The left panel gives applicability-"
            "domain surface density with exact 95% Poisson count intervals. The right "
            "panel gives the two rejected historical Model C acceptance fractions with "
            "95% Wilson intervals; legacy 60/30/10 points are offset by 3% in radius only for "
            "visibility. No selector or radial threshold is tuned."
        ),
        title="Gaia morphology-candidate host-field stress test",
    )
    plt.close(figure)


def main() -> None:
    """Run the fixed host-field retrieval and exploratory analysis."""
    arguments = parse_arguments()
    hosts = select_hosts(arguments.host_catalog, arguments.limit_hosts)
    benchmark_manifest = json.loads(arguments.benchmark_manifest.read_text(encoding="utf-8"))
    minimum_g = float(benchmark_manifest["applicability_domain"]["minimum_phot_g_mean_mag"])
    maximum_g = float(benchmark_manifest["applicability_domain"]["maximum_phot_g_mean_mag"])
    sources, query_records = retrieve_host_sources(hosts, arguments.maximum_radius_kpc)
    sources, metrics = build_radial_metrics(
        sources, minimum_g, maximum_g, arguments.maximum_radius_kpc
    )
    arguments.sources_output.parent.mkdir(parents=True, exist_ok=True)
    sources.to_csv(arguments.sources_output, index=False)
    metrics.to_csv(arguments.radial_output, index=False)
    if not arguments.skip_figure and arguments.limit_hosts is None:
        plot_metrics(metrics)

    manifest = {
        "analysis_version": ANALYSIS_VERSION,
        "generated_utc": datetime.now(UTC).isoformat(),
        "analysis_status": "exploratory_no_selector_or_radial_threshold_approved",
        "validation_partition_inspected": False,
        "endpoint": AIP_TAP_URL,
        "fixture_rule": {
            "host_count": HOST_COUNT,
            "minimum_absolute_galactic_latitude_deg": MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG,
            "minimum_distance_mpc": MINIMUM_DISTANCE_MPC,
            "maximum_distance_mpc": MAXIMUM_DISTANCE_MPC,
            "maximum_angular_radius_deg": MAXIMUM_ANGULAR_RADIUS_DEG,
            "radial_bin_edges_kpc": RADIAL_BIN_EDGES_KPC,
            "local_comparison_minimum_kpc": LOCAL_COMPARISON_MINIMUM_KPC,
            "smoke_limit_hosts": arguments.limit_hosts,
            "run_maximum_radius_kpc": arguments.maximum_radius_kpc,
        },
        "applicability_domain": {
            "minimum_phot_g_mean_mag": minimum_g,
            "maximum_phot_g_mean_mag": maximum_g,
        },
        "hosts": hosts[
            ["rank", "objname", "ra", "dec", "glat", "dist_best", "maximum_angular_radius_deg"]
        ].to_dict("records"),
        "query_records": query_records,
        "inputs": {
            "host_catalog": serialize_path(arguments.host_catalog),
            "host_catalog_sha256": calculate_sha256(arguments.host_catalog),
            "benchmark_manifest": serialize_path(arguments.benchmark_manifest),
            "benchmark_manifest_sha256": calculate_sha256(arguments.benchmark_manifest),
            "source_registry": serialize_path(arguments.source_registry),
            "source_registry_sha256": calculate_sha256(arguments.source_registry),
        },
        "outputs": {
            "sources": serialize_path(arguments.sources_output),
            "sources_sha256": calculate_sha256(arguments.sources_output),
            "radial_metrics": serialize_path(arguments.radial_output),
            "radial_metrics_sha256": calculate_sha256(arguments.radial_output),
        },
        "counts": {
            "host_count": len(hosts),
            "host_source_association_count": len(sources),
            "unique_gaia_source_count": sources["source_id"].nunique(),
            "radial_metric_row_count": len(metrics),
        },
    }
    arguments.manifest.parent.mkdir(parents=True, exist_ok=True)
    arguments.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %d host-source associations", len(sources))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
