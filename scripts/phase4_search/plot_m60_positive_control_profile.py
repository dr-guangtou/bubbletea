"""Plot the complete all-source and selector-passing M60 radial profiles."""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import M60_POSITIVE_CONTROL_PROFILE
from scripts.phase3_background.plot_first_stage_host_profile import poisson_density_errors
from scripts.utils.plotting import save_figure, set_style


def main() -> None:
    """Create the two-panel M60 positive-control radial-profile figure."""
    profile = pd.read_csv(M60_POSITIVE_CONTROL_PROFILE).sort_values("inner_radius_kpc")
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
    figure, axes = plt.subplots(2, 1, figsize=(6.5, 6.2), sharex=True)
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
            "Sources retained by selector version 1",
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
    axes[-1].set_xlabel("Projected radius from M60 (kpc)")
    axes[-1].set_xlim(2.3, 650)
    figure.tight_layout()
    save_figure(
        figure,
        name="m60_positive_control_radial_profile_v1",
        phase=4,
        script_path="scripts/phase4_search/plot_m60_positive_control_profile.py",
        command="uv run python scripts/phase4_search/plot_m60_positive_control_profile.py",
        data_source="data/results/radial_search/m60_positive_control_profile_v1.csv",
        description=(
            "Measured M60 surface density in all fourteen frozen physical rings. "
            "Panel A includes all Gaia sources in the frozen G-magnitude range; panel "
            "B includes sources retained by selector version 1. Horizontal bars show "
            "ring widths, and vertical bars show exact central 68.27% Poisson counting "
            "intervals. The gray region marks the temporary 0--50 kpc diagnostic "
            "region. Its elevated density is not used for UCD inference. No possible "
            "contaminant has been removed, and no final outer signal boundary is "
            "selected from this profile."
        ),
        title="M60 positive-control radial profile",
    )
    plt.close(figure)


if __name__ == "__main__":
    main()
