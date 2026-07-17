"""Analyze Gaia selector features on the sealed benchmark development partition.

The script measures feature coverage, univariate discrimination, label-sensitivity
scenarios, and the two inherited Model C definitions. It does not inspect the
benchmark validation partition or define a new selector threshold.
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    SELECTOR_DEVELOPMENT_FEATURE_METRICS,
    SELECTOR_DEVELOPMENT_FEATURES,
    SELECTOR_DEVELOPMENT_FEATURES_MANIFEST,
    SELECTOR_DEVELOPMENT_SENSITIVITY,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_selector_development_features import (
    DEVELOPMENT_FEATURE_VERSION,
)
from scripts.utils.plotting import save_figure, set_style

logger = logging.getLogger(__name__)

COMMAND = "uv run python scripts/phase1_literature/analyze_selector_development.py"
BOOTSTRAP_ITERATIONS = 500
FIGURE_SCRIPT = "scripts/phase1_literature/analyze_selector_development.py"
DATA_SOURCE = "data/literature/benchmarks/gaia_selector_development_features_v3.csv"

FEATURE_LABELS = {
    "astrometric_excess_noise": "Astrometric excess noise (mas)",
    "astrometric_excess_noise_sig": "Astrometric excess-noise significance",
    "ruwe": "RUWE",
    "ipd_frac_multi_peak": "IPD multi-peak windows (percent)",
    "ipd_frac_odd_win": "IPD odd-window transits (percent)",
    "bp_rp": "BP - RP (mag)",
    "bp_g": "BP - G (mag)",
    "g_rp": "G - RP (mag)",
    "phot_bp_rp_excess_factor": "BP/RP flux-excess factor",
    "absolute_parallax_zero_significance": "Absolute parallax zero-significance",
    "proper_motion_zero_significance": "Proper-motion zero-significance",
    "phot_g_mean_flux_over_error": "G flux signal-to-noise",
    "phot_bp_mean_flux_over_error": "BP flux signal-to-noise",
    "phot_rp_mean_flux_over_error": "RP flux signal-to-noise",
    "classprob_dsc_combmod_galaxy": "DSC galaxy probability",
    "classprob_dsc_combmod_quasar": "DSC quasar probability",
    "classprob_dsc_combmod_star": "DSC star probability",
    "duplicated_source": "Duplicated-source flag",
    "non_single_star": "Non-single-star flag",
}

PRIMARY_PLOT_GROUPS = [
    ("Confirmed UCD", "#000000", "-"),
    ("Candidate UCD", "#0072B2", "--"),
    ("Gaia NSS", "#E69F00", "-."),
    ("Galaxy", "#009E73", ":"),
    ("QSO", "#56B4E9", "--"),
    ("H II", "#D55E00", "-"),
    ("Reported non-UCD", "#CC79A7", "-."),
]


def parse_arguments() -> argparse.Namespace:
    """Parse development feature inputs and analysis outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES)
    parser.add_argument(
        "--features-manifest", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES_MANIFEST
    )
    parser.add_argument("--metrics", type=Path, default=SELECTOR_DEVELOPMENT_FEATURE_METRICS)
    parser.add_argument("--sensitivity", type=Path, default=SELECTOR_DEVELOPMENT_SENSITIVITY)
    parser.add_argument("--bootstrap-iterations", type=int, default=BOOTSTRAP_ITERATIONS)
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Skip figure generation for a measured analysis smoke run.",
    )
    return parser.parse_args()


def add_derived_features(rows: pd.DataFrame) -> pd.DataFrame:
    """Add Gaia-native colors and astrometric significance features."""
    rows = rows.copy()
    rows["bp_rp"] = rows["phot_bp_mean_mag"] - rows["phot_rp_mean_mag"]
    rows["bp_g"] = rows["phot_bp_mean_mag"] - rows["phot_g_mean_mag"]
    rows["g_rp"] = rows["phot_g_mean_mag"] - rows["phot_rp_mean_mag"]
    rows["absolute_parallax_zero_significance"] = rows["parallax"].abs() / rows["parallax_error"]
    standardized_pmra = rows["pmra"] / rows["pmra_error"]
    standardized_pmdec = rows["pmdec"] / rows["pmdec_error"]
    correlation = rows["pmra_pmdec_corr"]
    valid_inputs = (
        rows["pmra_error"].gt(0.0)
        & rows["pmdec_error"].gt(0.0)
        & np.isfinite(standardized_pmra)
        & np.isfinite(standardized_pmdec)
        & np.isfinite(correlation)
        & correlation.abs().lt(1.0)
    )
    squared_significance = (
        np.square(standardized_pmra)
        + np.square(standardized_pmdec)
        - 2.0 * correlation * standardized_pmra * standardized_pmdec
    ) / (1.0 - np.square(correlation))
    rows["proper_motion_zero_significance"] = np.sqrt(
        squared_significance.clip(lower=0.0).where(valid_inputs)
    )
    return rows


def label_masks(rows: pd.DataFrame) -> dict[str, tuple[pd.Series, pd.Series]]:
    """Return primary and declared sensitivity label scenarios."""
    confirmed = rows["label_subtype"].eq("ucd_confirmed")
    candidate = rows["label_subtype"].eq("ucd_candidate")
    contaminants = rows["label"].eq("contaminant") & rows["primary_label_eligible"]
    phangs = rows["source_cohort"].eq("phangs_muse_hii")
    all_hii = rows["source_cohort"].isin(["phangs_muse_hii", "van_zee_dwarf_hii"])
    return {
        "primary_confirmed_ucd": (confirmed, contaminants),
        "candidate_as_positive_sensitivity": (confirmed | candidate, contaminants),
        "exclude_phangs_sensitivity": (confirmed, contaminants & ~phangs),
        "exclude_all_hii_sensitivity": (confirmed, contaminants & ~all_hii),
    }


def raw_auc(positive: np.ndarray, negative: np.ndarray) -> float:
    """Return the rank-based probability that a positive exceeds a negative."""
    combined = np.concatenate([positive, negative])
    ranks = rankdata(combined, method="average")
    positive_rank_sum = ranks[: len(positive)].sum()
    return float(
        (positive_rank_sum - len(positive) * (len(positive) + 1) / 2)
        / (len(positive) * len(negative))
    )


def auc_metrics(
    positive_values: pd.Series,
    negative_values: pd.Series,
    bootstrap_iterations: int,
    seed_key: str,
) -> dict[str, object]:
    """Measure AUC direction and a deterministic stratified bootstrap interval."""
    positive = positive_values.to_numpy(dtype=float)
    negative = negative_values.to_numpy(dtype=float)
    positive = positive[np.isfinite(positive)]
    negative = negative[np.isfinite(negative)]
    if len(positive) == 0 or len(negative) == 0:
        return {
            "raw_auc": None,
            "discrimination_auc": None,
            "auc_ci_lower": None,
            "auc_ci_upper": None,
            "ucd_direction": None,
            "positive_non_null_count": len(positive),
            "negative_non_null_count": len(negative),
            "positive_median": None,
            "negative_median": None,
        }
    measured_raw_auc = raw_auc(positive, negative)
    higher_for_ucd = measured_raw_auc >= 0.5
    measured_auc = measured_raw_auc if higher_for_ucd else 1.0 - measured_raw_auc
    seed = int(hashlib.sha256(seed_key.encode("utf-8")).hexdigest()[:16], 16)
    generator = np.random.default_rng(seed)
    bootstrap_auc = np.empty(bootstrap_iterations)
    for iteration in range(bootstrap_iterations):
        sampled_positive = generator.choice(positive, len(positive), replace=True)
        sampled_negative = generator.choice(negative, len(negative), replace=True)
        iteration_raw_auc = raw_auc(sampled_positive, sampled_negative)
        bootstrap_auc[iteration] = iteration_raw_auc if higher_for_ucd else 1.0 - iteration_raw_auc
    return {
        "raw_auc": measured_raw_auc,
        "discrimination_auc": measured_auc,
        "auc_ci_lower": float(np.quantile(bootstrap_auc, 0.025)),
        "auc_ci_upper": float(np.quantile(bootstrap_auc, 0.975)),
        "ucd_direction": "higher" if higher_for_ucd else "lower",
        "positive_non_null_count": len(positive),
        "negative_non_null_count": len(negative),
        "positive_median": float(np.median(positive)),
        "negative_median": float(np.median(negative)),
    }


def build_feature_metrics(rows: pd.DataFrame, bootstrap_iterations: int) -> pd.DataFrame:
    """Measure overall scenario and primary contaminant-subtype discrimination."""
    metrics = []
    scenarios = label_masks(rows)
    for scenario_name, (positive_mask, negative_mask) in scenarios.items():
        negative_groups = {"all_primary_contaminants": negative_mask}
        if scenario_name == "primary_confirmed_ucd":
            for subtype in sorted(rows.loc[negative_mask, "label_subtype"].unique()):
                negative_groups[subtype] = negative_mask & rows["label_subtype"].eq(subtype)
        for negative_group, group_mask in negative_groups.items():
            for feature in FEATURE_LABELS:
                measurement = auc_metrics(
                    rows.loc[positive_mask, feature],
                    rows.loc[group_mask, feature],
                    bootstrap_iterations,
                    f"{scenario_name}|{negative_group}|{feature}",
                )
                metrics.append(
                    {
                        "scenario": scenario_name,
                        "negative_group": negative_group,
                        "feature": feature,
                        "feature_label": FEATURE_LABELS[feature],
                        "positive_row_count": int(positive_mask.sum()),
                        "negative_row_count": int(group_mask.sum()),
                        "positive_coverage_fraction": float(
                            rows.loc[positive_mask, feature].notna().mean()
                        ),
                        "negative_coverage_fraction": float(
                            rows.loc[group_mask, feature].notna().mean()
                        ),
                        **measurement,
                    }
                )
    return pd.DataFrame(metrics)


def inherited_model_selections(rows: pd.DataFrame) -> dict[str, pd.Series]:
    """Return the two incompatible historical Model C selections."""
    probability_aen = norm.cdf(rows["astrometric_excess_noise_sig"] - 2.0)
    probability_br = np.clip((rows["phot_bp_rp_excess_factor"] - 1.2) / 0.5, 0.0, 1.0)
    probability_color = rows["bp_rp"].between(0.8, 1.8, inclusive="both").astype(float)
    phase3_score = probability_aen * 0.7 + probability_br * 0.3
    phase4_score = probability_aen * 0.6 + probability_br * 0.3 + probability_color * 0.1
    phase3_prefilter = (
        rows["phot_g_mean_mag"].between(16.0, 21.0, inclusive="both")
        & rows["astrometric_excess_noise"].gt(0.3)
        & rows["astrometric_excess_noise_sig"].gt(1.0)
    )
    legacy_pm_significance = np.sqrt(np.square(rows["pmra"]) + np.square(rows["pmdec"])) / np.sqrt(
        np.square(rows["pmra_error"]) + np.square(rows["pmdec_error"])
    )
    phase4_pm_rule = (
        rows["pmra"].isna()
        | rows["pmdec"].isna()
        | legacy_pm_significance.le(3.0)
        | np.sqrt(np.square(rows["pmra"]) + np.square(rows["pmdec"])).lt(2.92)
    )
    phase4_prefilter = (
        rows["phot_g_mean_mag"].between(16.0, 21.0, inclusive="both")
        & rows["astrometric_excess_noise"].gt(0.3)
        & phase4_pm_rule
    )
    return {
        "phase3_model_c_70_30": phase3_prefilter & phase3_score.gt(0.5),
        "phase4_model_c_60_30_10": phase4_prefilter & phase4_score.gt(0.5),
    }


def inherited_model_results(rows: pd.DataFrame) -> dict[str, object]:
    """Summarize the two incompatible historical Model C definitions."""
    selections = inherited_model_selections(rows)
    masks = label_masks(rows)
    results = {}
    for model_name, selected in selections.items():
        scenarios = {}
        for scenario_name, (positive, negative) in masks.items():
            scenarios[scenario_name] = {
                "positive_row_count": int(positive.sum()),
                "positive_selected_count": int((positive & selected).sum()),
                "positive_selection_fraction": float(selected.loc[positive].mean()),
                "negative_row_count": int(negative.sum()),
                "negative_selected_count": int((negative & selected).sum()),
                "negative_selection_fraction": float(selected.loc[negative].mean()),
            }
        subtype_results = {}
        for subtype, subtype_rows in rows.groupby("label_subtype"):
            subtype_selected = selected.loc[subtype_rows.index]
            subtype_results[subtype] = {
                "row_count": len(subtype_rows),
                "selected_count": int(subtype_selected.sum()),
                "selection_fraction": float(subtype_selected.mean()),
            }
        results[model_name] = {
            "label_scenarios": scenarios,
            "selection_by_label_subtype": subtype_results,
        }
    return results


def plotting_group(rows: pd.DataFrame) -> pd.Series:
    """Map detailed benchmark roles to readable distribution groups."""
    group = pd.Series("Excluded uncertainty", index=rows.index)
    mappings = {
        "ucd_confirmed": "Confirmed UCD",
        "ucd_candidate": "Candidate UCD",
        "gaia_non_single_star": "Gaia NSS",
        "spectroscopic_galaxy": "Galaxy",
        "spectroscopic_qso": "QSO",
        "reported_non_ucd_comparison": "Reported non-UCD",
        "compact_hii_region": "H II",
        "dwarf_galaxy_hii_region": "H II",
    }
    for subtype, group_name in mappings.items():
        group.loc[rows["label_subtype"].eq(subtype)] = group_name
    return group


def empirical_cdf(values: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Return finite values and their empirical cumulative fractions."""
    finite = np.sort(values.to_numpy(dtype=float))
    finite = finite[np.isfinite(finite)]
    return finite, np.arange(1, len(finite) + 1) / len(finite)


def plot_feature_distributions(rows: pd.DataFrame) -> None:
    """Plot development-only empirical feature distributions by label role."""
    features = [
        "astrometric_excess_noise",
        "astrometric_excess_noise_sig",
        "ruwe",
        "ipd_frac_multi_peak",
        "bp_rp",
        "phot_bp_rp_excess_factor",
    ]
    rows = rows.copy()
    rows["plot_group"] = plotting_group(rows)
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
    figure, axes = plt.subplots(2, 3, figsize=(7.2, 5.3))
    for axis, feature in zip(axes.flat, features, strict=True):
        for group_name, color, line_style in PRIMARY_PLOT_GROUPS:
            group_values = rows.loc[rows["plot_group"].eq(group_name), feature]
            if feature in {"astrometric_excess_noise", "astrometric_excess_noise_sig"}:
                group_values = np.log10(1.0 + group_values.clip(lower=0.0))
            values, cumulative = empirical_cdf(group_values)
            if len(values):
                axis.plot(
                    values,
                    cumulative,
                    color=color,
                    linestyle=line_style,
                    linewidth=1.3,
                    label=group_name,
                )
        feature_axis_labels = {
            "astrometric_excess_noise": "log10(1 + astrometric excess noise / mas)",
            "astrometric_excess_noise_sig": "log10(1 + excess-noise significance)",
            "ipd_frac_multi_peak": "IPD multi-peak windows (percent)",
        }
        axis.set_xlabel(feature_axis_labels.get(feature, FEATURE_LABELS[feature]))
        axis.set_ylabel("Empirical cumulative fraction")
        axis.set_ylim(0.0, 1.01)
        if feature in {"ruwe", "phot_bp_rp_excess_factor"}:
            positive_values = rows.loc[rows[feature].gt(0), feature]
            if len(positive_values):
                axis.set_xscale("log")
        axis.spines[["top", "right"]].set_visible(False)
    legend_handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(
        legend_handles,
        legend_labels,
        frameon=False,
        loc="upper center",
        ncol=4,
        bbox_to_anchor=(0.5, 1.0),
    )
    figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.92))
    save_figure(
        figure,
        "selector_development_feature_distributions",
        phase=1,
        script_path=FIGURE_SCRIPT,
        command=COMMAND,
        data_source=DATA_SOURCE,
        description=(
            "Development-only empirical cumulative distributions for 175 confirmed UCDs, "
            "569 uncertain UCD candidates, and the primary contaminant cohorts. Curves show "
            "all individual finite measurements, so summary error bars are not applicable. "
            "The validation partition was not read by this analysis."
        ),
        title="Development-only Gaia selector feature distributions",
    )
    plt.close(figure)


def plot_auc_heatmap(metrics: pd.DataFrame) -> None:
    """Plot primary confirmed-UCD discrimination against contaminant roles."""
    selected_features = [
        "astrometric_excess_noise",
        "astrometric_excess_noise_sig",
        "ruwe",
        "ipd_frac_multi_peak",
        "ipd_frac_odd_win",
        "bp_rp",
        "phot_bp_rp_excess_factor",
        "absolute_parallax_zero_significance",
        "proper_motion_zero_significance",
        "classprob_dsc_combmod_galaxy",
        "classprob_dsc_combmod_star",
    ]
    primary = metrics.loc[
        metrics["scenario"].eq("primary_confirmed_ucd")
        & ~metrics["negative_group"].eq("all_primary_contaminants")
        & metrics["feature"].isin(selected_features)
    ]
    matrix = primary.pivot(
        index="feature", columns="negative_group", values="discrimination_auc"
    ).reindex(selected_features)
    contaminant_labels = {
        "compact_hii_region": "Compact H II",
        "dwarf_galaxy_hii_region": "Dwarf-host H II",
        "gaia_non_single_star": "Gaia NSS",
        "reported_non_ucd_comparison": "Reported non-UCD",
        "spectroscopic_galaxy": "SDSS galaxy",
        "spectroscopic_qso": "SDSS QSO",
    }
    heatmap_feature_labels = {
        **FEATURE_LABELS,
        "ipd_frac_multi_peak": "IPD multi-peak windows (percent)",
        "ipd_frac_odd_win": "IPD odd-window transits (percent)",
    }
    set_style()
    plt.rcParams.update({"font.family": "sans-serif", "font.size": 7, "axes.grid": False})
    figure, axis = plt.subplots(figsize=(7.8, 5.8))
    image = axis.imshow(matrix.to_numpy(), vmin=0.5, vmax=1.0, cmap="cividis", aspect="auto")
    axis.set_xticks(
        np.arange(len(matrix.columns)),
        [contaminant_labels[column] for column in matrix.columns],
        rotation=30,
        ha="right",
    )
    axis.set_yticks(
        np.arange(len(matrix.index)),
        [heatmap_feature_labels[feature] for feature in matrix.index],
    )
    for row_index in range(len(matrix.index)):
        for column_index in range(len(matrix.columns)):
            value = matrix.iloc[row_index, column_index]
            if np.isfinite(value):
                text_color = "white" if value < 0.72 else "black"
                axis.text(
                    column_index,
                    row_index,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    color=text_color,
                    fontsize=6,
                )
    colorbar = figure.colorbar(image, ax=axis, pad=0.02)
    colorbar.set_label("Direction-adjusted ROC AUC")
    axis.set_xlabel("Primary contaminant role")
    axis.set_ylabel("Gaia feature")
    figure.tight_layout()
    save_figure(
        figure,
        "selector_development_feature_auc",
        phase=1,
        script_path=FIGURE_SCRIPT,
        command=COMMAND,
        data_source=DATA_SOURCE,
        description=(
            "Direction-adjusted univariate ROC AUC for 175 confirmed UCDs versus each "
            "development-partition contaminant role. Values approach one when a feature "
            "separates the two roles in either direction and 0.5 for no rank separation. "
            "The companion metrics table reports deterministic stratified-bootstrap 95% "
            "confidence intervals from 500 resamples. Feature definitions and safeguards "
            "are recorded in docs/gaia_selector_features.md."
        ),
        title="Development-only univariate Gaia feature discrimination",
    )
    plt.close(figure)


def main() -> None:
    """Run development-only measurements and write data and figure artifacts."""
    arguments = parse_arguments()
    if arguments.bootstrap_iterations <= 0:
        raise ValueError("--bootstrap-iterations must be positive")
    with arguments.features_manifest.open(encoding="utf-8") as input_file:
        manifest = json.load(input_file)
    if manifest["feature_version"] != DEVELOPMENT_FEATURE_VERSION:
        raise RuntimeError("Unexpected development feature version")
    if manifest["counts"]["queried_validation_rows"] != 0:
        raise RuntimeError("Development feature manifest reports queried validation rows")
    if calculate_sha256(arguments.features) != manifest["output_sha256"]:
        raise RuntimeError("Development feature matrix digest does not match its manifest")

    rows = pd.read_csv(arguments.features, dtype={"gaia_dr3_id": str})
    if set(rows["partition"]) != {"development"}:
        raise RuntimeError("Selector analysis input is not development-only")
    rows = add_derived_features(rows)
    metrics = build_feature_metrics(rows, arguments.bootstrap_iterations)
    model_results = inherited_model_results(rows)
    coverage = {
        subtype: {feature: float(group[feature].notna().mean()) for feature in FEATURE_LABELS}
        for subtype, group in rows.groupby("label_subtype")
    }
    overall_primary = metrics.loc[
        metrics["scenario"].eq("primary_confirmed_ucd")
        & metrics["negative_group"].eq("all_primary_contaminants")
    ].sort_values("discrimination_auc", ascending=False)
    summary = {
        "feature_version": DEVELOPMENT_FEATURE_VERSION,
        "partition": "development",
        "validation_partition_inspected": False,
        "feature_matrix_sha256": calculate_sha256(arguments.features),
        "bootstrap_iterations": arguments.bootstrap_iterations,
        "counts": {
            "rows": len(rows),
            "gaia_sources": rows["gaia_dr3_id"].nunique(),
            "label_subtypes": rows["label_subtype"].value_counts().sort_index().to_dict(),
        },
        "feature_coverage_by_label_subtype": coverage,
        "primary_overall_feature_ranking": overall_primary[
            [
                "feature",
                "discrimination_auc",
                "auc_ci_lower",
                "auc_ci_upper",
                "ucd_direction",
            ]
        ].to_dict("records"),
        "inherited_model_results": model_results,
        "decision_status": "development_measurement_only_no_selector_or_threshold_approved",
    }
    arguments.metrics.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(arguments.metrics, index=False)
    arguments.sensitivity.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not arguments.skip_figures:
        plot_feature_distributions(rows)
        plot_auc_heatmap(metrics)
    logger.info("Wrote %d feature-scenario metrics", len(metrics))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
