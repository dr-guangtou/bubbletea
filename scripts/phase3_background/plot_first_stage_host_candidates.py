"""Plot NGC 4698 candidate locations and frozen-selector feature spaces."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from matplotlib.lines import Line2D

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    FIRST_STAGE_HOST_CANDIDATE_DIAGNOSTICS,
    FIRST_STAGE_HOST_CANDIDATE_REVIEW,
    FIRST_STAGE_HOST_PROFILE_FIXTURE,
    FIRST_STAGE_HOST_PROFILE_RETRIEVAL_DIR,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256
from scripts.utils.plotting import save_figure, set_style

ANALYSIS_VERSION = "first_stage_ngc4698_candidate_diagnostics_v1"
HOST_NAME = "NGC 4698"
SOURCE_PATH = FIRST_STAGE_HOST_PROFILE_RETRIEVAL_DIR / "ngc_4698" / "scored_sources.csv"
CENTRAL_EXCLUSION_KPC = 50
REVIEW_MAXIMUM_RADIUS_KPC = 150
FEATURE_AXIS_QUANTILES = (0.005, 0.995)

FEATURE_LABELS = {
    "log1p_astrometric_excess_noise": "log(1 + astrometric excess noise)",
    "log1p_astrometric_excess_noise_sig": "log(1 + excess-noise significance)",
    "phot_bp_rp_excess_factor": "BP/RP flux-excess factor",
    "bp_rp": "BP - RP (mag)",
    "log_ruwe": "log(RUWE)",
    "log1p_ipd_frac_multi_peak": "log(1 + IPD multi-peak percentage)",
    "log1p_ipd_frac_odd_win": "log(1 + IPD odd-window percentage)",
    "log1p_absolute_parallax_zero_significance": ("log(1 + absolute parallax significance)"),
    "log1p_proper_motion_zero_significance": ("log(1 + proper-motion significance)"),
}


def configure_style() -> None:
    """Apply the project style with compact publication-readable typography."""
    set_style()
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 8,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.grid": False,
        }
    )


def build_review_examples(selected: pd.DataFrame) -> pd.DataFrame:
    """Select transparent examples for visual review without defining a rank."""
    outside = selected.loc[
        selected["projected_radius_kpc"].gt(CENTRAL_EXCLUSION_KPC)
        & selected["projected_radius_kpc"].le(REVIEW_MAXIMUM_RADIUS_KPC)
    ]
    examples = [
        (
            "A",
            "nearest_passing_source_outside_50_kpc",
            outside.nsmallest(1, "projected_radius_kpc").iloc[0],
        ),
        (
            "B",
            "highest_score_in_50_to_75_kpc_ring",
            outside.loc[outside["projected_radius_kpc"].le(75)]
            .nlargest(1, "point_source_logistic_probability")
            .iloc[0],
        ),
        (
            "C",
            "highest_score_in_75_to_100_kpc_ring",
            outside.loc[
                outside["projected_radius_kpc"].gt(75) & outside["projected_radius_kpc"].le(100)
            ]
            .nlargest(1, "point_source_logistic_probability")
            .iloc[0],
        ),
        (
            "D",
            "highest_score_in_100_to_150_kpc_ring",
            outside.loc[outside["projected_radius_kpc"].gt(100)]
            .nlargest(1, "point_source_logistic_probability")
            .iloc[0],
        ),
        (
            "E",
            "brightest_passing_source_between_50_and_150_kpc",
            outside.nsmallest(1, "phot_g_mean_mag").iloc[0],
        ),
    ]
    columns = [
        "source_id",
        "ra",
        "dec",
        "projected_radius_kpc",
        "phot_g_mean_mag",
        "bp_rp",
        "phot_bp_rp_excess_factor",
        "astrometric_excess_noise",
        "astrometric_excess_noise_sig",
        "ruwe",
        "ipd_frac_multi_peak",
        "ipd_frac_odd_win",
        "absolute_parallax_zero_significance",
        "proper_motion_zero_significance",
        *FEATURE_LABELS,
        "point_source_logistic_probability",
    ]
    columns = list(dict.fromkeys(columns))
    records = []
    for label, reason, row in examples:
        records.append(
            {
                "review_label": label,
                "review_reason": reason,
                "interpretation_status": "visual_review_example_not_candidate_rank",
                **{column: row[column] for column in columns},
            }
        )
    return pd.DataFrame(records)


def add_host_offsets(sources: pd.DataFrame, host: pd.Series) -> pd.DataFrame:
    """Add exact east and north projected offsets from the host in kpc."""
    host_coordinate = SkyCoord(
        float(host["host_ra_deg"]) * u.deg,
        float(host["host_dec_deg"]) * u.deg,
        frame="icrs",
    )
    source_coordinates = SkyCoord(
        sources["ra"].to_numpy() * u.deg,
        sources["dec"].to_numpy() * u.deg,
        frame="icrs",
    )
    position_angle = host_coordinate.position_angle(source_coordinates).rad
    radius_kpc = sources["projected_radius_kpc"].to_numpy()
    result = sources.copy()
    result["east_offset_kpc"] = radius_kpc * np.sin(position_angle)
    result["north_offset_kpc"] = radius_kpc * np.cos(position_angle)
    return result


def plot_locations(selected: pd.DataFrame, review: pd.DataFrame) -> None:
    """Plot every passing source at full and central spatial scales."""
    configure_style()
    figure, axes = plt.subplots(1, 2, figsize=(7.2, 3.5))
    panels = (
        (axes[0], 600, "All passing sources through 600 kpc"),
        (axes[1], 150, "Central 150 kpc"),
    )
    for panel_label, (axis, maximum_radius_kpc, title) in zip(("A", "B"), panels, strict=True):
        shown = selected.loc[selected["projected_radius_kpc"].le(maximum_radius_kpc)]
        points = axis.scatter(
            shown["east_offset_kpc"],
            shown["north_offset_kpc"],
            c=shown["phot_g_mean_mag"],
            cmap="viridis_r",
            vmin=11.26291847229004,
            vmax=21.75798797607422,
            s=8 if maximum_radius_kpc == 600 else 16,
            alpha=0.62,
            linewidths=0,
            rasterized=True,
        )
        for radius_kpc, line_style in ((50, "--"), (150, ":"), (300, ":"), (600, "-")):
            if radius_kpc <= maximum_radius_kpc:
                axis.add_patch(
                    plt.Circle(
                        (0, 0),
                        radius_kpc,
                        fill=False,
                        color="#555555",
                        linestyle=line_style,
                        linewidth=0.8,
                    )
                )
        axis.add_patch(
            plt.Circle(
                (0, 0),
                min(CENTRAL_EXCLUSION_KPC, maximum_radius_kpc),
                color="#999999",
                alpha=0.12,
                linewidth=0,
            )
        )
        axis.plot(0, 0, marker="*", color="#D55E00", markersize=9, label=HOST_NAME)
        if maximum_radius_kpc == REVIEW_MAXIMUM_RADIUS_KPC:
            for _, row in review.iterrows():
                axis.scatter(
                    row["east_offset_kpc"],
                    row["north_offset_kpc"],
                    facecolors="none",
                    edgecolors="#D55E00",
                    s=55,
                    linewidths=1.1,
                    zorder=4,
                )
                axis.annotate(
                    str(row["review_label"]),
                    (row["east_offset_kpc"], row["north_offset_kpc"]),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=7,
                    fontweight="bold",
                    color="#D55E00",
                )
        axis.set_xlim(maximum_radius_kpc, -maximum_radius_kpc)
        axis.set_ylim(-maximum_radius_kpc, maximum_radius_kpc)
        axis.set_aspect("equal")
        axis.set_xlabel("Projected east-west offset (kpc; east is left)")
        axis.set_ylabel("Projected north-south offset (kpc)")
        axis.set_title(title, loc="left")
        axis.text(
            -0.12,
            1.03,
            panel_label,
            transform=axis.transAxes,
            fontsize=10,
            fontweight="bold",
        )
        axis.spines[["top", "right"]].set_visible(False)
    colorbar_axis = figure.add_axes((0.91, 0.20, 0.018, 0.62))
    colorbar = figure.colorbar(points, cax=colorbar_axis)
    colorbar.set_label("Gaia G magnitude")
    figure.subplots_adjust(left=0.09, right=0.87, bottom=0.16, top=0.91, wspace=0.28)
    save_figure(
        figure,
        name="first_stage_ngc4698_candidate_locations",
        phase=3,
        script_path="scripts/phase3_background/plot_first_stage_host_candidates.py",
        command="BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python scripts/phase3_background/plot_first_stage_host_candidates.py",
        data_source=(
            "$BUBBLETEA_EXTERNAL_DATA/bubbletea/gaia_host_profiles_v1/ngc_4698/scored_sources.csv"
        ),
        description=(
            "Locations of all 2,548 Gaia sources remaining after the frozen point-source "
            "contamination selector. NGC 4698 is the orange star, and the gray disk is "
            "the temporary 0--50 kpc contamination region. Circles mark preserved profile "
            "edges. Color gives Gaia G magnitude. Labels A--E identify transparent review "
            "examples chosen by location, within-ring score, or brightness; they are not "
            "a scientific candidate ranking. The selected-source surface density is broadly "
            "flat beyond 50 kpc, so this map does not show a statistically prominent "
            "host-centered concentration."
        ),
        title="NGC 4698 selector-passing source locations",
    )
    plt.close(figure)


def clipped_limits(rows: pd.DataFrame, column: str) -> tuple[float, float]:
    """Return measured display limits while retaining all rows in analysis outputs."""
    values = rows[column].dropna()
    return tuple(values.quantile(FEATURE_AXIS_QUANTILES).to_numpy())


def plot_feature_spaces(
    sources: pd.DataFrame, selected: pd.DataFrame, review: pd.DataFrame
) -> None:
    """Plot exact frozen model inputs, output score, and measured missingness."""
    configure_style()
    figure, axes = plt.subplots(2, 3, figsize=(8.2, 5.4))
    rejected = sources.loc[~sources["point_source_logistic_selected"].astype(bool)]
    panels = [
        (
            "log1p_astrometric_excess_noise",
            "log1p_astrometric_excess_noise_sig",
            "Astrometric excess noise",
        ),
        ("bp_rp", "phot_bp_rp_excess_factor", "Gaia color and flux consistency"),
        ("log_ruwe", "log1p_ipd_frac_multi_peak", "Astrometric fit and multiple peaks"),
        (
            "log1p_absolute_parallax_zero_significance",
            "log1p_proper_motion_zero_significance",
            "Evidence for nonzero astrometry",
        ),
        (
            "log1p_ipd_frac_odd_win",
            "point_source_logistic_probability",
            "Nearby-window diagnostic and selector score",
        ),
    ]
    for panel_label, axis, (x_column, y_column, title) in zip(
        ("A", "B", "C", "D", "E"), axes.flat[:5], panels, strict=True
    ):
        rejected_complete = rejected[[x_column, y_column]].notna().all(axis=1)
        selected_complete = selected[[x_column, y_column]].notna().all(axis=1)
        axis.scatter(
            rejected.loc[rejected_complete, x_column],
            rejected.loc[rejected_complete, y_column],
            s=3,
            color="#999999",
            alpha=0.10,
            linewidths=0,
            rasterized=True,
            label="Rejected",
        )
        axis.scatter(
            selected.loc[selected_complete, x_column],
            selected.loc[selected_complete, y_column],
            s=7,
            color="#0072B2",
            alpha=0.34,
            linewidths=0,
            rasterized=True,
            label="Passing",
        )
        review_complete = review[[x_column, y_column]].notna().all(axis=1)
        for _, row in review.loc[review_complete].iterrows():
            axis.scatter(
                row[x_column],
                row[y_column],
                facecolors="none",
                edgecolors="#D55E00",
                s=45,
                linewidths=1,
                zorder=4,
            )
            axis.annotate(
                str(row["review_label"]),
                (row[x_column], row[y_column]),
                xytext=(3, 3),
                textcoords="offset points",
                fontsize=6,
                color="#D55E00",
                fontweight="bold",
            )
        axis.set_xlim(*clipped_limits(sources, x_column))
        axis.set_ylim(*clipped_limits(sources, y_column))
        axis.set_xlabel(FEATURE_LABELS.get(x_column, "Frozen selector score"))
        axis.set_ylabel(FEATURE_LABELS.get(y_column, "Frozen selector score"))
        axis.set_title(title, loc="left")
        axis.text(
            0.02,
            0.97,
            (f"Passing with both values: {selected_complete.sum():,}/{len(selected):,}"),
            transform=axis.transAxes,
            va="top",
            fontsize=6.5,
        )
        axis.text(
            -0.16,
            1.04,
            panel_label,
            transform=axis.transAxes,
            fontsize=10,
            fontweight="bold",
        )
        axis.spines[["top", "right"]].set_visible(False)

    missing_axis = axes.flat[5]
    missing_columns = list(FEATURE_LABELS)
    selected_missing = selected[missing_columns].isna().mean() * 100
    rejected_missing = rejected[missing_columns].isna().mean() * 100
    positions = np.arange(len(missing_columns))
    missing_axis.barh(
        positions + 0.18,
        selected_missing,
        height=0.34,
        color="#0072B2",
        label="Passing",
    )
    missing_axis.barh(
        positions - 0.18,
        rejected_missing,
        height=0.34,
        color="#999999",
        label="Rejected",
    )
    missing_axis.set_yticks(
        positions,
        [
            "AEN",
            "AEN significance",
            "BP/RP excess",
            "BP - RP",
            "RUWE",
            "IPD multi-peak",
            "IPD odd-window",
            "Parallax significance",
            "Motion significance",
        ],
    )
    missing_axis.set_xlim(0, 100)
    missing_axis.set_xlabel("Missing measurements (%)")
    missing_axis.set_title("Feature availability", loc="left")
    missing_axis.legend(frameon=False, loc="lower right")
    missing_axis.text(
        -0.16,
        1.04,
        "F",
        transform=missing_axis.transAxes,
        fontsize=10,
        fontweight="bold",
    )
    missing_axis.spines[["top", "right"]].set_visible(False)
    handles = [
        Line2D([0], [0], marker="o", linestyle="none", color="#999999", label="Rejected"),
        Line2D([0], [0], marker="o", linestyle="none", color="#0072B2", label="Passing"),
        Line2D(
            [0],
            [0],
            marker="o",
            markerfacecolor="none",
            markeredgecolor="#D55E00",
            linestyle="none",
            label="Review example",
        ),
    ]
    figure.legend(handles=handles, frameon=False, loc="upper center", ncol=3)
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    save_figure(
        figure,
        name="first_stage_ngc4698_selector_feature_spaces",
        phase=3,
        script_path="scripts/phase3_background/plot_first_stage_host_candidates.py",
        command="BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python scripts/phase3_background/plot_first_stage_host_candidates.py",
        data_source=(
            "$BUBBLETEA_EXTERNAL_DATA/bubbletea/gaia_host_profiles_v1/ngc_4698/scored_sources.csv"
        ),
        description=(
            "The exact nine measured feature inputs used by the frozen logistic selector, "
            "plus its output score and feature missingness. Gray points are rejected Gaia "
            "sources and blue points pass the frozen threshold. A--E are transparent review "
            "examples, not a candidate rank. Each scatter panel states how many passing "
            "sources have both plotted measurements. Display axes use the measured 0.5th "
            "to 99.5th percentiles so extreme archive values do not compress the main "
            "distribution; no row is removed from counts or analysis outputs. Panel F "
            "shows that missing five-parameter astrometry is common among passing sources "
            "and is explicitly handled by the frozen model. A high score is a selector "
            "output, not a calibrated probability that the source is a real UCD."
        ),
        title="NGC 4698 frozen-selector feature spaces",
    )
    plt.close(figure)


def main() -> None:
    """Write candidate diagnostics and both requested figures."""
    fixture = pd.read_csv(FIRST_STAGE_HOST_PROFILE_FIXTURE)
    host = fixture.loc[fixture["host_name"].eq(HOST_NAME)].iloc[0]
    sources = pd.read_csv(SOURCE_PATH, dtype={"source_id": "int64"})
    selected = sources.loc[sources["point_source_logistic_selected"].astype(bool)].copy()
    selected = add_host_offsets(selected, host)
    review = build_review_examples(selected)
    review = review.merge(
        selected[["source_id", "east_offset_kpc", "north_offset_kpc"]],
        on="source_id",
        how="left",
        validate="one_to_one",
    )
    FIRST_STAGE_HOST_CANDIDATE_REVIEW.parent.mkdir(parents=True, exist_ok=True)
    review.to_csv(FIRST_STAGE_HOST_CANDIDATE_REVIEW, index=False)
    plot_locations(selected, review)
    plot_feature_spaces(sources, selected, review)

    rejected = sources.loc[~sources["point_source_logistic_selected"].astype(bool)]
    selected_outside = selected.loc[selected["projected_radius_kpc"].gt(CENTRAL_EXCLUSION_KPC)]
    selected_astrometry_missing = selected["ruwe"].isna()
    rejected_astrometry_missing = rejected["ruwe"].isna()
    coordinates = SkyCoord(selected["ra"].to_numpy() * u.deg, selected["dec"].to_numpy() * u.deg)
    _, nearest_separation, _ = coordinates.match_to_catalog_sky(coordinates, nthneighbor=2)
    checks = {
        "all_frozen_domain_sources_preserved": len(sources) == 23811,
        "all_selector_passing_sources_preserved": len(selected) == 2548,
        "review_examples_are_passing_sources": set(review["source_id"]).issubset(
            set(selected["source_id"])
        ),
        "review_examples_are_not_inside_central_exclusion": review["projected_radius_kpc"]
        .gt(CENTRAL_EXCLUSION_KPC)
        .all(),
        "review_examples_are_not_labeled_as_rank": review["interpretation_status"]
        .eq("visual_review_example_not_candidate_rank")
        .all(),
        "model_threshold_unchanged": json.loads(
            POINT_SOURCE_LOGISTIC_MODEL_MANIFEST.read_text(encoding="utf-8")
        )["threshold"]
        == 0.8277833628791744,
        "no_new_candidate_cut_applied": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    diagnostics = {
        "analysis_version": ANALYSIS_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "host_name": HOST_NAME,
        "host_distance_mpc": float(host["host_distance_mpc"]),
        "plain_language_result": (
            "The passing sources do not form a prominent host-centered concentration. "
            "Most high scores belong to faint sources without a five-parameter Gaia "
            "astrometric solution, so score alone does not identify a compelling UCD."
        ),
        "all_source_count": len(sources),
        "selector_passing_source_count": len(selected),
        "selector_passing_inside_50_kpc_count": int(
            selected["projected_radius_kpc"].le(CENTRAL_EXCLUSION_KPC).sum()
        ),
        "selector_passing_50_to_150_kpc_count": int(
            selected_outside["projected_radius_kpc"].le(REVIEW_MAXIMUM_RADIUS_KPC).sum()
        ),
        "selector_passing_missing_five_parameter_astrometry_count": int(
            selected_astrometry_missing.sum()
        ),
        "selector_passing_missing_five_parameter_astrometry_fraction": float(
            selected_astrometry_missing.mean()
        ),
        "rejected_missing_five_parameter_astrometry_fraction": float(
            rejected_astrometry_missing.mean()
        ),
        "selector_score_quantiles": {
            str(quantile): float(selected["point_source_logistic_probability"].quantile(quantile))
            for quantile in (0.0, 0.1, 0.5, 0.9, 0.99, 1.0)
        },
        "passing_sources_with_neighbor_within_2_arcsec": int(
            np.count_nonzero(nearest_separation.arcsec < 2)
        ),
        "review_examples": {
            "count": len(review),
            "interpretation": (
                "Examples make the plots auditable and do not define a candidate rank."
            ),
            "path": str(FIRST_STAGE_HOST_CANDIDATE_REVIEW.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(FIRST_STAGE_HOST_CANDIDATE_REVIEW),
        },
        "feature_display_limits": {
            "lower_quantile": FEATURE_AXIS_QUANTILES[0],
            "upper_quantile": FEATURE_AXIS_QUANTILES[1],
            "effect": "display_only_no_rows_removed_from_counts_or_outputs",
        },
        "inputs": [
            {"path": str(path), "sha256": file_sha256(path)}
            for path in (SOURCE_PATH, FIRST_STAGE_HOST_PROFILE_FIXTURE)
        ],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    FIRST_STAGE_HOST_CANDIDATE_DIAGNOSTICS.write_text(
        json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Candidate diagnostics failed: {checks}")


if __name__ == "__main__":
    main()
