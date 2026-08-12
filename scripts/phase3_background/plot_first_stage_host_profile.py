"""Plot the first all-source and selector-passing Gaia host profiles."""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import FIRST_STAGE_HOST_PROFILE
from scripts.utils.plotting import save_figure, set_style

ONE_SIGMA_TAIL_PROBABILITY = 1 - 0.682689492137


def poisson_density_errors(counts: np.ndarray, areas_square_deg: np.ndarray) -> np.ndarray:
    """Return exact central 68.27% Poisson density error lengths."""
    lower_counts = np.where(
        counts > 0,
        0.5 * chi2.ppf(ONE_SIGMA_TAIL_PROBABILITY / 2, 2 * counts),
        0.0,
    )
    upper_counts = 0.5 * chi2.ppf(1 - ONE_SIGMA_TAIL_PROBABILITY / 2, 2 * (counts + 1))
    density = counts / areas_square_deg
    return np.vstack(
        [density - lower_counts / areas_square_deg, upper_counts / areas_square_deg - density]
    )


def main() -> None:
    """Create the two-panel NGC 4698 radial profile figure."""
    profile = pd.read_csv(FIRST_STAGE_HOST_PROFILE).sort_values("inner_radius_kpc")
    inner = profile["inner_radius_kpc"].to_numpy(dtype=float)
    outer = profile["outer_radius_kpc"].to_numpy(dtype=float)
    midpoint = (inner + outer) / 2
    horizontal_errors = np.vstack([midpoint - inner, outer - midpoint])
    area = profile["requested_ring_area_square_deg"].to_numpy(dtype=float)

    set_style()
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
        }
    )
    fig, axes = plt.subplots(2, 1, figsize=(6.5, 6.2), sharex=True)
    panels = (
        (
            "all_source_count",
            "all_source_density_per_square_deg",
            "All Gaia sources in the frozen G range",
            "#000000",
        ),
        (
            "selector_passing_source_count",
            "selector_passing_density_per_square_deg",
            "Sources remaining after the point-source contamination selector",
            "#0072B2",
        ),
    )
    for panel_label, (axis, panel) in zip(("A", "B"), zip(axes, panels), strict=True):
        count_column, density_column, title, color = panel
        counts = profile[count_column].to_numpy(dtype=int)
        density = profile[density_column].to_numpy(dtype=float)
        axis.axvspan(2.5, 50, color="#999999", alpha=0.18, label="Temporary inner region")
        axis.errorbar(
            midpoint,
            density,
            xerr=horizontal_errors,
            yerr=poisson_density_errors(counts, area),
            fmt="o",
            color=color,
            markerfacecolor="white",
            markeredgewidth=1.2,
            markersize=4.5,
            capsize=2,
            linewidth=1,
        )
        axis.set_xscale("log")
        axis.set_ylabel("Surface density (deg$^{-2}$)")
        axis.set_title(title, loc="left")
        axis.text(
            -0.11,
            1.03,
            panel_label,
            transform=axis.transAxes,
            fontsize=11,
            fontweight="bold",
            va="bottom",
        )
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, loc="best")
    axes[-1].set_xlabel("Projected radius from NGC 4698 (kpc)")
    axes[-1].set_xlim(2.3, 650)
    fig.tight_layout()
    save_figure(
        fig,
        name="first_stage_ngc4698_radial_profile",
        phase=3,
        script_path="scripts/phase3_background/plot_first_stage_host_profile.py",
        command="uv run python scripts/phase3_background/plot_first_stage_host_profile.py",
        data_source="data/results/background/first_stage_host_profile_ngc4698_v1.csv",
        description=(
            "Measured NGC 4698 surface density in all fourteen frozen physical rings. "
            "Panel A includes all Gaia sources in the frozen G-magnitude range; panel B "
            "includes only sources remaining after the frozen point-source contamination "
            "selector. Horizontal bars show ring widths, and vertical bars show exact "
            "central 68.27% Poisson counting intervals. The gray region marks the "
            "temporary 0--50 kpc contamination region, which remains excluded from "
            "first-stage inference. The small-area inner bins contain few objects; the "
            "profile beyond 50 kpc is the relevant first inspection. No final outer "
            "signal boundary is selected from this one host."
        ),
        title="First-stage NGC 4698 radial profile",
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
