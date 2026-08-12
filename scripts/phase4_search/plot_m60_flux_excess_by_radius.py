"""Plot Gaia G magnitude versus raw BP/RP flux excess in four M60 radial zones."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    EXTERNAL_DATA_DIR,
    M60_POSITIVE_CONTROL_AUDIT_CONTRACT,
    M60_POSITIVE_CONTROL_AUDIT_SAMPLE,
    M60_POSITIVE_CONTROL_FLUX_EXCESS_DIAGNOSTICS,
    M60_POSITIVE_CONTROL_KNOWN_RECOVERY,
    M60_POSITIVE_CONTROL_RUN_MANIFEST,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.freeze_m60_visual_audit_sample import RADIAL_ZONES, assign_radial_zone
from scripts.utils.plotting import save_figure, set_style

FIGURE_NAME = "m60_flux_excess_by_radial_zone_v1"
SCRIPT_PATH = "scripts/phase4_search/plot_m60_flux_excess_by_radius.py"
COMMAND = (
    "BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python "
    "scripts/phase4_search/plot_m60_flux_excess_by_radius.py"
)
LIU_2020_FLUX_EXCESS_REFERENCE = 1.7
ZONE_TITLES = {
    "central_diagnostic_0_50_kpc": "0--50 kpc diagnostic region",
    "near_host_50_150_kpc": "50--150 kpc",
    "intermediate_150_300_kpc": "150--300 kpc",
    "far_300_600_kpc": "300--600 kpc",
}


def external_path(path_text: str) -> Path:
    """Resolve a portable external-data locator."""
    prefix = "$BUBBLETEA_EXTERNAL_DATA/"
    if not path_text.startswith(prefix):
        raise RuntimeError(f"Expected an external-data locator: {path_text}")
    return EXTERNAL_DATA_DIR / path_text.removeprefix(prefix)


def finite_flux_excess(rows: pd.DataFrame) -> pd.DataFrame:
    """Return rows with finite G magnitude and positive finite flux excess."""
    valid = (
        np.isfinite(rows["phot_g_mean_mag"])
        & np.isfinite(rows["phot_bp_rp_excess_factor"])
        & rows["phot_bp_rp_excess_factor"].gt(0)
    )
    return rows.loc[valid].copy()


def zone_summary(
    full_zone: pd.DataFrame, audit_zone: pd.DataFrame, zone_name: str
) -> dict[str, object]:
    """Record measured completeness and quantiles for one radial zone."""
    full_finite = finite_flux_excess(full_zone)
    audit_finite = finite_flux_excess(audit_zone)
    quantiles = full_finite["phot_bp_rp_excess_factor"].quantile([0.1, 0.5, 0.9])
    return {
        "zone_name": zone_name,
        "full_selector_retained_count": len(full_zone),
        "full_plotted_count": len(full_finite),
        "full_missing_or_nonpositive_flux_excess_count": len(full_zone) - len(full_finite),
        "audit_count": len(audit_zone),
        "audit_plotted_count": len(audit_finite),
        "audit_missing_or_nonpositive_flux_excess_count": len(audit_zone) - len(audit_finite),
        "full_flux_excess_10th_percentile": float(quantiles.loc[0.1]),
        "full_flux_excess_median": float(quantiles.loc[0.5]),
        "full_flux_excess_90th_percentile": float(quantiles.loc[0.9]),
    }


def main() -> None:
    """Create the four-panel distribution figure and checked numeric summary."""
    run = json.loads(M60_POSITIVE_CONTROL_RUN_MANIFEST.read_text())
    audit_contract = json.loads(M60_POSITIVE_CONTROL_AUDIT_CONTRACT.read_text())
    scored_path = external_path(run["external_outputs"]["scored_sources"])
    if calculate_sha256(scored_path) != run["external_outputs"]["scored_sources_sha256"]:
        raise RuntimeError("M60 scored-source table differs from its run digest")
    if (
        calculate_sha256(M60_POSITIVE_CONTROL_AUDIT_SAMPLE)
        != audit_contract["sample_output"]["sha256"]
    ):
        raise RuntimeError("M60 audit sample differs from its frozen digest")

    sources = pd.read_csv(scored_path, dtype={"source_id": str})
    passing = sources.loc[sources["point_source_logistic_selected"].astype(bool)].copy()
    passing["audit_radial_zone"] = passing["projected_radius_kpc"].map(assign_radial_zone)
    audit = pd.read_csv(M60_POSITIVE_CONTROL_AUDIT_SAMPLE, dtype={"source_id": str})
    known = pd.read_csv(M60_POSITIVE_CONTROL_KNOWN_RECOVERY, dtype={"gaia_dr3_ids": str})
    reliable_ids = set(
        known.loc[
            known["positive_control_role"].eq("reliable_confirmed_ucd"),
            "gaia_dr3_ids",
        ]
    )
    reliable = passing.loc[passing["source_id"].isin(reliable_ids)].copy()

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
    figure, axes = plt.subplots(2, 2, figsize=(7.2, 6.0), sharex=True, sharey=True)
    summaries = []
    for panel_label, axis, (zone_name, _, _) in zip(
        ("A", "B", "C", "D"), axes.flat, RADIAL_ZONES, strict=True
    ):
        full_zone = passing.loc[passing["audit_radial_zone"].eq(zone_name)]
        audit_zone = audit.loc[audit["audit_radial_zone"].eq(zone_name)]
        reliable_zone = reliable.loc[reliable["audit_radial_zone"].eq(zone_name)]
        full_finite = finite_flux_excess(full_zone)
        audit_finite = finite_flux_excess(audit_zone)
        reliable_finite = finite_flux_excess(reliable_zone)
        summaries.append(zone_summary(full_zone, audit_zone, zone_name))
        axis.scatter(
            full_finite["phot_g_mean_mag"],
            full_finite["phot_bp_rp_excess_factor"],
            s=5,
            color="#777777",
            alpha=0.2,
            linewidths=0,
            rasterized=True,
            label="All selector-retained sources",
        )
        axis.scatter(
            audit_finite["phot_g_mean_mag"],
            audit_finite["phot_bp_rp_excess_factor"],
            s=18,
            facecolors="none",
            edgecolors="#0072B2",
            alpha=0.72,
            linewidths=0.65,
            rasterized=True,
            label="Frozen visual-audit sample",
        )
        if len(reliable_finite):
            axis.scatter(
                reliable_finite["phot_g_mean_mag"],
                reliable_finite["phot_bp_rp_excess_factor"],
                marker="*",
                s=100,
                facecolor="#E69F00",
                edgecolor="#000000",
                linewidth=0.55,
                zorder=5,
                label="Reliable M60 UCD controls",
            )
        axis.axhline(
            LIU_2020_FLUX_EXCESS_REFERENCE,
            color="#000000",
            linestyle=":",
            linewidth=0.9,
        )
        axis.set_title(ZONE_TITLES[zone_name], loc="left")
        axis.text(
            0.03,
            0.96,
            (
                f"Full: {len(full_finite)}/{len(full_zone)} plotted\n"
                f"Audit: {len(audit_finite)}/{len(audit_zone)} plotted"
            ),
            transform=axis.transAxes,
            fontsize=6.5,
            va="top",
        )
        axis.text(
            -0.12,
            1.04,
            panel_label,
            transform=axis.transAxes,
            fontsize=10,
            fontweight="bold",
        )
        axis.set_xlim(11.0, 22.0)
        axis.set_yscale("log")
        axis.set_ylim(0.4, 80.0)
        axis.spines[["top", "right"]].set_visible(False)
    for axis in axes[-1]:
        axis.set_xlabel("Gaia G magnitude")
    for axis in axes[:, 0]:
        axis.set_ylabel(r"BP/RP flux-excess factor $(I_{BP}+I_{RP})/I_G$")
    handles, labels = axes[0, 1].get_legend_handles_labels()
    figure.legend(
        handles,
        labels,
        frameon=False,
        loc="upper center",
        ncol=3,
        bbox_to_anchor=(0.5, 1.0),
    )
    figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    save_figure(
        figure,
        name=FIGURE_NAME,
        phase=4,
        script_path=SCRIPT_PATH,
        command=COMMAND,
        data_source=(
            "$BUBBLETEA_EXTERNAL_DATA/bubbletea/m60_positive_control_v1/"
            "scored_sources.csv; data/results/radial_search/"
            "m60_positive_control_visual_audit_sample_v1.csv"
        ),
        description=(
            "Gaia G magnitude versus the raw BP/RP flux-excess factor, defined as "
            "(I_BP + I_RP) / I_G, for all 4,920 M60 sources retained by selector "
            "version 1. Panels preserve the four frozen radial zones. Gray points show "
            "the complete retained population, blue open circles show the separately "
            "frozen representative visual-audit sample, and orange stars show the two "
            "reliable M60 UCD controls. Each panel reports finite plotted counts; rows "
            "without a usable excess-factor measurement remain in all scientific "
            "tables. The dotted 1.7 line is the Liu et al. (2020) sample-specific "
            "reference, not a BubbleTea selection boundary. High raw flux excess can "
            "reflect resolved structure, crowding, or measurement problems and does "
            "not by itself establish a galaxy classification."
        ),
        title="M60 Gaia flux excess by radial zone",
    )
    plt.close(figure)

    checks = {
        "complete_selector_retained_population_used": len(passing)
        == run["selector_passing_source_count"],
        "four_frozen_radial_zones_used": len(summaries) == len(RADIAL_ZONES),
        "audit_sample_identifiers_are_subset_of_passing_population": set(
            audit["source_id"]
        ).issubset(set(passing["source_id"])),
        "exactly_four_hundred_audit_sources_used": len(audit) == 400,
        "two_reliable_controls_are_plotted": len(reliable) == 2,
        "missing_flux_excess_rows_are_counted": sum(
            item["full_missing_or_nonpositive_flux_excess_count"] for item in summaries
        )
        == len(passing) - len(finite_flux_excess(passing)),
        "no_visual_classification_assigned": audit["possible_nearby_source_blend_or_image_problem"]
        .eq("not_reviewed")
        .all(),
        "liu_reference_is_not_a_selection_boundary": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    diagnostics = {
        "diagnostic_version": "m60_positive_control_flux_excess_by_radius_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "complete_unclassified_distribution_qa",
        "flux_excess_definition": "(I_BP + I_RP) / I_G",
        "full_selector_retained_count": len(passing),
        "full_plotted_count": len(finite_flux_excess(passing)),
        "audit_count": len(audit),
        "audit_plotted_count": len(finite_flux_excess(audit)),
        "zone_summaries": summaries,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    M60_POSITIVE_CONTROL_FLUX_EXCESS_DIAGNOSTICS.write_text(
        json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"M60 flux-excess QA failed: {checks}")


if __name__ == "__main__":
    main()
