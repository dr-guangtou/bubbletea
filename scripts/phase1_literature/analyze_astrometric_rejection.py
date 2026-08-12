"""Measure the frozen development-only astrometric-rejection tradeoff.

The unchanged point-source selector is applied first. A second rule then rejects a
passing source when either available Gaia parallax or proper-motion significance is
strictly above a trial boundary. Missing astrometry is not treated as zero motion.
"""

import json
import logging
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    POINT_SOURCE_ASTROMETRIC_REJECTION_CONTRACT,
    POINT_SOURCE_ASTROMETRIC_REJECTION_CURVE,
    POINT_SOURCE_ASTROMETRIC_REJECTION_SUMMARY,
    POINT_SOURCE_ASTROMETRIC_REJECTION_UCD_REVIEW,
    POINT_SOURCE_LOGISTIC_MODEL,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.compare_point_source_ml import (
    MODEL_FEATURES,
    PRIORITY_COHORTS,
    load_cohorts,
)
from scripts.utils.plotting import save_figure, set_style

logger = logging.getLogger(__name__)

COMMAND = "uv run python scripts/phase1_literature/analyze_astrometric_rejection.py"
DEVELOPMENT_PREDICTIONS = (
    POINT_SOURCE_LOGISTIC_MODEL.parent / "point_source_logistic_development_predictions_v1.csv"
)
FIGURE_NAME = "point_source_astrometric_rejection_tradeoff_v1"
FIGURE_SCRIPT = "scripts/phase1_literature/analyze_astrometric_rejection.py"
COHORTS = [
    "confirmed_ucd",
    "spectroscopic_star",
    "gaia_non_single_star",
    "spectroscopic_qso",
    "spectroscopic_galaxy",
    "hii_region",
]
COHORT_LABELS = {
    "confirmed_ucd": "Reliable UCD",
    "spectroscopic_star": "Ordinary star",
    "gaia_non_single_star": "Gaia non-single star",
    "spectroscopic_qso": "QSO",
    "spectroscopic_galaxy": "Galaxy",
    "hii_region": "H II region",
}
COHORT_COLORS = {
    "confirmed_ucd": "#000000",
    "spectroscopic_star": "#D55E00",
    "gaia_non_single_star": "#E69F00",
    "spectroscopic_qso": "#0072B2",
    "spectroscopic_galaxy": "#009E73",
    "hii_region": "#CC79A7",
}
COHORT_LINE_STYLES = {
    "confirmed_ucd": "-",
    "spectroscopic_star": "--",
    "gaia_non_single_star": "-.",
    "spectroscopic_qso": ":",
    "spectroscopic_galaxy": "--",
    "hii_region": "-.",
}


def verify_contract_inputs(contract: dict[str, object]) -> None:
    """Stop if any input differs from the frozen pre-measurement contract."""
    inputs = {
        "development_features": SELECTOR_DEVELOPMENT_FEATURES,
        "spectroscopic_stars": SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
        "selector_model": POINT_SOURCE_LOGISTIC_MODEL,
        "selector_model_manifest": POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
        "development_predictions": DEVELOPMENT_PREDICTIONS,
    }
    for name, path in inputs.items():
        expected = contract["inputs"][name]["sha256"]
        if calculate_sha256(path) != expected:
            raise RuntimeError(f"Frozen input changed: {name}")


def add_astrometric_decision_statistic(rows: pd.DataFrame) -> pd.DataFrame:
    """Recover the two significances and use the larger available measurement."""
    rows = rows.copy()
    rows["absolute_parallax_significance"] = np.expm1(
        rows["log1p_absolute_parallax_zero_significance"]
    )
    rows["proper_motion_significance"] = np.expm1(rows["log1p_proper_motion_zero_significance"])
    rows["astrometric_decision_significance"] = rows[
        ["absolute_parallax_significance", "proper_motion_significance"]
    ].max(axis=1, skipna=True)
    return rows


def cohort_measurements(rows: pd.DataFrame, selected: np.ndarray) -> dict[str, object]:
    """Return selected counts and fractions for every declared cohort."""
    measurements = {}
    for cohort in COHORTS:
        mask = rows["ml_cohort"].eq(cohort).to_numpy()
        measurements[cohort] = {
            "row_count": int(mask.sum()),
            "selected_count": int(selected[mask].sum()),
            "selected_fraction": float(selected[mask].mean()),
        }
    return measurements


def curve_row(
    rows: pd.DataFrame,
    baseline_selected: np.ndarray,
    boundary: float,
) -> dict[str, object]:
    """Measure the post-rule selection at one significance boundary."""
    significance = rows["astrometric_decision_significance"].to_numpy(dtype=float)
    rejected = np.isfinite(significance) & (significance > boundary)
    selected = baseline_selected & ~rejected
    result: dict[str, object] = {
        "boundary_sigma": float(boundary),
        "is_three_sigma_literature_reference": bool(boundary == 3.0),
    }
    for cohort in COHORTS:
        mask = rows["ml_cohort"].eq(cohort).to_numpy()
        result[f"{cohort}_selected_count"] = int(selected[mask].sum())
        result[f"{cohort}_selected_fraction"] = float(selected[mask].mean())
    priority_fractions = [result[f"{cohort}_selected_fraction"] for cohort in PRIORITY_COHORTS]
    result["macro_priority_selected_fraction"] = float(np.mean(priority_fractions))
    reliable_ucd = rows["ml_cohort"].eq("confirmed_ucd").to_numpy()
    result["reliable_ucd_removed_from_baseline_count"] = int(
        baseline_selected[reliable_ucd].sum() - selected[reliable_ucd].sum()
    )
    return result


def measurement_availability(rows: pd.DataFrame) -> dict[str, object]:
    """Describe which astrometric evidence is available in each cohort."""
    availability = {}
    parallax = rows["absolute_parallax_significance"].notna()
    proper_motion = rows["proper_motion_significance"].notna()
    for cohort in COHORTS:
        mask = rows["ml_cohort"].eq(cohort)
        availability[cohort] = {
            "row_count": int(mask.sum()),
            "both_available_count": int((mask & parallax & proper_motion).sum()),
            "one_or_both_available_count": int((mask & (parallax | proper_motion)).sum()),
            "both_missing_count": int((mask & ~parallax & ~proper_motion).sum()),
            "one_or_both_available_fraction": float((parallax | proper_motion)[mask].mean()),
        }
    return availability


def make_figure(curve: pd.DataFrame, baseline: dict[str, object]) -> None:
    """Plot boundary behavior and the UCD-versus-contaminant tradeoff."""
    set_style()
    figure, axes = plt.subplots(1, 2, figsize=(13.0, 5.4))
    positive_boundary = curve.loc[curve["boundary_sigma"].gt(0.0)]

    for cohort in COHORTS:
        axes[0].step(
            positive_boundary["boundary_sigma"],
            100.0 * positive_boundary[f"{cohort}_selected_fraction"],
            where="post",
            color=COHORT_COLORS[cohort],
            linestyle=COHORT_LINE_STYLES[cohort],
            linewidth=2.0 if cohort == "confirmed_ucd" else 1.5,
            label=COHORT_LABELS[cohort],
        )
    axes[0].axvline(3.0, color="#777777", linestyle=":", linewidth=1.5)
    axes[0].set_xscale("log")
    selected_count_columns = [f"{cohort}_selected_count" for cohort in COHORTS]
    changed = curve[selected_count_columns].ne(curve[selected_count_columns].shift()).any(axis=1)
    changed_boundaries = curve.loc[changed & curve["boundary_sigma"].gt(0.0), "boundary_sigma"]
    axes[0].set_xlim(changed_boundaries.min() / 1.5, changed_boundaries.max() * 1.5)
    axes[0].set_xlabel("Astrometric rejection boundary (standard deviations)")
    axes[0].set_ylabel("Fraction passing both rules (percent)")
    axes[0].set_title("A  Retention by source type", loc="left", fontweight="bold")
    axes[0].legend(frameon=False, fontsize=9, ncol=2)

    axes[1].plot(
        100.0 * curve["macro_priority_selected_fraction"],
        100.0 * curve["confirmed_ucd_selected_fraction"],
        color="#0072B2",
        linewidth=2.0,
    )
    reference = curve.loc[curve["is_three_sigma_literature_reference"]].iloc[0]
    axes[1].scatter(
        100.0 * reference["macro_priority_selected_fraction"],
        100.0 * reference["confirmed_ucd_selected_fraction"],
        color="#D55E00",
        marker="s",
        s=55,
        zorder=3,
        label="3-standard-deviation reference",
    )
    axes[1].scatter(
        100.0 * baseline["macro_priority_selected_fraction"],
        100.0 * baseline["cohorts"]["confirmed_ucd"]["selected_fraction"],
        color="#000000",
        marker="o",
        s=55,
        zorder=3,
        label="Selector version 1 alone",
    )
    axes[1].set_xlabel("Priority contaminants passing (percent; equal-cohort mean)")
    axes[1].set_ylabel("Reliable UCDs passing (percent)")
    axes[1].set_title("B  Completeness–contamination tradeoff", loc="left", fontweight="bold")
    axes[1].legend(frameon=False, fontsize=9)

    for axis in axes:
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
    figure.tight_layout()
    save_figure(
        figure,
        FIGURE_NAME,
        phase=1,
        script_path=FIGURE_SCRIPT,
        command=COMMAND,
        data_source=(
            "data/literature/benchmarks/gaia_selector_development_features_v3.csv; "
            "data/literature/benchmarks/spectroscopic_stellar_reference_matches_v3.csv; "
            "data/literature/validation/point_source_logistic_model_v1.joblib"
        ),
        title="Post-selector astrometric rejection tradeoff",
        description=(
            "Development-only tradeoff after applying the unchanged point-source selector "
            "and then rejecting sources whose available parallax or proper-motion "
            "significance exceeds the plotted boundary. Panel A reports every declared "
            "cohort; panel B compares reliable-UCD retention with the equal-weight mean "
            "retention of ordinary stars, Gaia non-single stars, and QSOs. The orange "
            "square is the Liu et al. (2020) 3-standard-deviation reference, not an "
            "approved BubbleTea cutoff. Missing astrometry causes no rejection."
        ),
    )
    plt.close(figure)


def main() -> None:
    """Measure the exact development curve and write its figure and summary."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    contract = json.loads(POINT_SOURCE_ASTROMETRIC_REJECTION_CONTRACT.read_text())
    if contract["status"] != "frozen_development_only_before_measurement":
        raise RuntimeError("Astrometric-rejection contract is not frozen")
    verify_contract_inputs(contract)

    rows = load_cohorts(SELECTOR_DEVELOPMENT_FEATURES, SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    rows = add_astrometric_decision_statistic(rows)
    model_manifest = json.loads(POINT_SOURCE_LOGISTIC_MODEL_MANIFEST.read_text())
    model = joblib.load(POINT_SOURCE_LOGISTIC_MODEL)
    probability = model.predict_proba(rows[MODEL_FEATURES])[:, 1]
    baseline_selected = probability >= float(model_manifest["threshold"])

    frozen_predictions = pd.read_csv(DEVELOPMENT_PREDICTIONS, dtype={"gaia_dr3_id": str})
    model_fit = rows["fit_role"].eq("model_fit")
    measured_fit = pd.DataFrame(
        {
            "row_id": rows.loc[model_fit, "row_id"].to_numpy(),
            "probability": probability[model_fit.to_numpy()],
        }
    )
    parity = measured_fit.merge(
        frozen_predictions[["row_id", "probability"]],
        on="row_id",
        how="inner",
        suffixes=("_measured", "_frozen"),
        validate="one_to_one",
    )
    maximum_probability_difference = float(
        (parity["probability_measured"] - parity["probability_frozen"]).abs().max()
    )
    if len(parity) != int(model_fit.sum()) or maximum_probability_difference > 1e-12:
        raise RuntimeError("Frozen selector probability parity failed")

    finite_significance = rows.loc[
        rows["astrometric_decision_significance"].notna(),
        "astrometric_decision_significance",
    ].to_numpy(dtype=float)
    boundaries = np.unique(np.concatenate(([0.0, 3.0], finite_significance)))
    curve = pd.DataFrame([curve_row(rows, baseline_selected, boundary) for boundary in boundaries])
    POINT_SOURCE_ASTROMETRIC_REJECTION_CURVE.parent.mkdir(parents=True, exist_ok=True)
    curve.to_csv(POINT_SOURCE_ASTROMETRIC_REJECTION_CURVE, index=False)

    development_features = pd.read_csv(
        SELECTOR_DEVELOPMENT_FEATURES,
        dtype={"gaia_dr3_id": str},
    )
    ucd_review = rows.loc[
        rows["ml_cohort"].eq("confirmed_ucd") & rows["astrometric_decision_significance"].gt(3.0),
        [
            "row_id",
            "gaia_dr3_id",
            "absolute_parallax_significance",
            "proper_motion_significance",
            "astrometric_decision_significance",
        ],
    ].copy()
    ucd_review["selector_v1_probability"] = probability[ucd_review.index]
    ucd_review["selector_v1_selected"] = baseline_selected[ucd_review.index]
    ucd_review["rejected_at_three_sigma"] = ucd_review["selector_v1_selected"]
    provenance_columns = [
        "gaia_dr3_id",
        "canonical_object_id",
        "publication_bibcode",
        "source_row_locator",
        "classification_state",
        "confidence_tier",
        "ra",
        "dec",
    ]
    ucd_review = ucd_review.merge(
        development_features[provenance_columns],
        on="gaia_dr3_id",
        how="left",
        validate="one_to_one",
    )
    ucd_review = ucd_review[
        [
            "row_id",
            "canonical_object_id",
            "gaia_dr3_id",
            "publication_bibcode",
            "source_row_locator",
            "classification_state",
            "confidence_tier",
            "ra",
            "dec",
            "selector_v1_probability",
            "selector_v1_selected",
            "absolute_parallax_significance",
            "proper_motion_significance",
            "astrometric_decision_significance",
            "rejected_at_three_sigma",
        ]
    ].sort_values("astrometric_decision_significance", ascending=False)
    ucd_review.to_csv(POINT_SOURCE_ASTROMETRIC_REJECTION_UCD_REVIEW, index=False)

    baseline_cohorts = cohort_measurements(rows, baseline_selected)
    baseline = {
        "cohorts": baseline_cohorts,
        "macro_priority_selected_fraction": float(
            np.mean([baseline_cohorts[cohort]["selected_fraction"] for cohort in PRIORITY_COHORTS])
        ),
    }
    make_figure(curve, baseline)
    three_sigma = curve.loc[curve["is_three_sigma_literature_reference"]].iloc[0]
    reliable_ucd_count = baseline_cohorts["confirmed_ucd"]["row_count"]
    ninety_percent_count = int(np.ceil(0.9 * reliable_ucd_count))
    ninety_percent_anchor = curve.loc[
        curve["confirmed_ucd_selected_count"].ge(ninety_percent_count)
    ].iloc[0]
    summary = {
        "assessment_version": contract["assessment_version"],
        "status": "development_measurement_complete_no_boundary_approved",
        "selector_model_version": model_manifest["model_version"],
        "selector_threshold": model_manifest["threshold"],
        "counts": {
            "development_rows": len(rows),
            "curve_boundaries": len(curve),
            "model_fit_rows_checked_for_probability_parity": len(parity),
        },
        "measurement_availability": measurement_availability(rows),
        "selector_v1_baseline": baseline,
        "three_sigma_literature_reference": {
            key: (bool(value) if isinstance(value, np.bool_) else value.item())
            for key, value in three_sigma.items()
        },
        "historical_ninety_percent_recall_anchor": {
            "status": "descriptive_existing_selector_objective_not_an_approved_boundary",
            "minimum_reliable_ucd_count": ninety_percent_count,
            **{
                key: (bool(value) if isinstance(value, np.bool_) else value.item())
                for key, value in ninety_percent_anchor.items()
            },
        },
        "probability_parity": {
            "maximum_absolute_difference": maximum_probability_difference,
            "passed": True,
        },
        "reliable_ucd_three_sigma_review": {
            "above_three_sigma_count": len(ucd_review),
            "selected_by_selector_v1_count": int(ucd_review["selector_v1_selected"].sum()),
            "rejected_at_three_sigma_count": int(ucd_review["rejected_at_three_sigma"].sum()),
            "all_publication_bibcodes": sorted(ucd_review["publication_bibcode"].unique()),
            "artifact_sha256": calculate_sha256(POINT_SOURCE_ASTROMETRIC_REJECTION_UCD_REVIEW),
        },
        "interpretation_limits": [
            "development_sample_only",
            "three_sigma_is_a_literature_reference_not_an_approved_boundary",
            "no_operating_point_selected",
            "validation_partition_not_used",
            "ngc4698_star_not_used_to_choose_a_boundary",
            "selector_v1_unchanged",
        ],
        "inputs": {
            "contract_sha256": calculate_sha256(POINT_SOURCE_ASTROMETRIC_REJECTION_CONTRACT),
            "curve_sha256": calculate_sha256(POINT_SOURCE_ASTROMETRIC_REJECTION_CURVE),
        },
    }
    POINT_SOURCE_ASTROMETRIC_REJECTION_SUMMARY.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    logger.info("Measured %d exact astrometric boundaries", len(curve))


if __name__ == "__main__":
    main()
