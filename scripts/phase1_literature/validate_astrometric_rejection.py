"""Validate the frozen development-only astrometric-rejection assessment."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    FIGURES_DIR,
    POINT_SOURCE_ASTROMETRIC_REJECTION_CONTRACT,
    POINT_SOURCE_ASTROMETRIC_REJECTION_CURVE,
    POINT_SOURCE_ASTROMETRIC_REJECTION_SUMMARY,
    POINT_SOURCE_ASTROMETRIC_REJECTION_UCD_REVIEW,
    POINT_SOURCE_ASTROMETRIC_REJECTION_VALIDATION,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.compare_point_source_ml import PRIORITY_COHORTS

COHORTS = [
    "confirmed_ucd",
    "spectroscopic_star",
    "gaia_non_single_star",
    "spectroscopic_qso",
    "spectroscopic_galaxy",
    "hii_region",
]


def main() -> None:
    """Reproduce structural, monotonicity, and no-retuning safeguards."""
    contract = json.loads(POINT_SOURCE_ASTROMETRIC_REJECTION_CONTRACT.read_text())
    summary = json.loads(POINT_SOURCE_ASTROMETRIC_REJECTION_SUMMARY.read_text())
    curve = pd.read_csv(POINT_SOURCE_ASTROMETRIC_REJECTION_CURVE)
    ucd_review = pd.read_csv(
        POINT_SOURCE_ASTROMETRIC_REJECTION_UCD_REVIEW,
        dtype={"gaia_dr3_id": str},
    )
    checks: dict[str, bool] = {}

    checks["contract_frozen"] = contract["status"] == "frozen_development_only_before_measurement"
    checks["contract_digest"] = summary["inputs"]["contract_sha256"] == calculate_sha256(
        POINT_SOURCE_ASTROMETRIC_REJECTION_CONTRACT
    )
    checks["curve_digest"] = summary["inputs"]["curve_sha256"] == calculate_sha256(
        POINT_SOURCE_ASTROMETRIC_REJECTION_CURVE
    )
    checks["curve_count"] = len(curve) == summary["counts"]["curve_boundaries"]
    checks["boundaries_unique_and_ordered"] = bool(
        curve["boundary_sigma"].is_unique and curve["boundary_sigma"].is_monotonic_increasing
    )
    checks["zero_endpoint_present"] = bool(curve["boundary_sigma"].iloc[0] == 0.0)
    checks["one_three_sigma_row"] = bool(
        curve["is_three_sigma_literature_reference"].sum() == 1
        and curve.loc[curve["is_three_sigma_literature_reference"], "boundary_sigma"].iloc[0] == 3.0
    )
    monotonic_columns = [f"{cohort}_selected_count" for cohort in COHORTS]
    monotonic_columns += [f"{cohort}_selected_fraction" for cohort in COHORTS]
    monotonic_columns.append("macro_priority_selected_fraction")
    checks["retention_monotonic_with_boundary"] = bool(
        all(curve[column].is_monotonic_increasing for column in monotonic_columns)
    )
    baseline = summary["selector_v1_baseline"]
    checks["maximum_boundary_reproduces_baseline"] = bool(
        all(
            np.isclose(
                curve.iloc[-1][f"{cohort}_selected_fraction"],
                baseline["cohorts"][cohort]["selected_fraction"],
            )
            for cohort in COHORTS
        )
    )
    three_sigma = curve.loc[curve["is_three_sigma_literature_reference"]].iloc[0]
    checks["three_sigma_summary_reproduced"] = bool(
        all(
            np.isclose(
                three_sigma[f"{cohort}_selected_fraction"],
                summary["three_sigma_literature_reference"][f"{cohort}_selected_fraction"],
            )
            for cohort in COHORTS
        )
    )
    ninety_percent_anchor = summary["historical_ninety_percent_recall_anchor"]
    reproduced_anchor = curve.loc[
        curve["confirmed_ucd_selected_count"].ge(
            ninety_percent_anchor["minimum_reliable_ucd_count"]
        )
    ].iloc[0]
    checks["ninety_percent_anchor_reproduced"] = bool(
        np.isclose(reproduced_anchor["boundary_sigma"], ninety_percent_anchor["boundary_sigma"])
        and np.isclose(
            reproduced_anchor["macro_priority_selected_fraction"],
            ninety_percent_anchor["macro_priority_selected_fraction"],
        )
    )
    checks["priority_macro_reproduced"] = bool(
        np.allclose(
            curve["macro_priority_selected_fraction"],
            np.mean(
                np.vstack([curve[f"{cohort}_selected_fraction"] for cohort in PRIORITY_COHORTS]),
                axis=0,
            ),
        )
    )
    checks["probability_parity"] = bool(summary["probability_parity"]["passed"])
    checks["ucd_review_digest"] = summary["reliable_ucd_three_sigma_review"][
        "artifact_sha256"
    ] == calculate_sha256(POINT_SOURCE_ASTROMETRIC_REJECTION_UCD_REVIEW)
    checks["ucd_review_scope"] = bool(
        len(ucd_review) == summary["reliable_ucd_three_sigma_review"]["above_three_sigma_count"]
        and ucd_review["astrometric_decision_significance"].gt(3.0).all()
        and ucd_review["classification_state"].eq("confirmed").all()
    )
    checks["ucd_three_sigma_loss_reproduced"] = bool(
        ucd_review["rejected_at_three_sigma"].sum()
        == summary["three_sigma_literature_reference"]["reliable_ucd_removed_from_baseline_count"]
    )
    checks["no_boundary_approved"] = (
        summary["status"] == "development_measurement_complete_no_boundary_approved"
        and "no_operating_point_selected" in summary["interpretation_limits"]
    )
    checks["validation_not_used"] = (
        contract["safeguards"]["validation_partition_use"] == "prohibited"
        and "validation_partition_not_used" in summary["interpretation_limits"]
    )
    figure = FIGURES_DIR / "phase1" / "point_source_astrometric_rejection_tradeoff_v1.png"
    caption = figure.with_suffix(".md")
    checks["figure_caption_pair"] = figure.is_file() and caption.is_file()

    checks = {name: bool(passed) for name, passed in checks.items()}
    report = {
        "assessment_version": contract["assessment_version"],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "failed_count": len(checks) - sum(checks.values()),
        "checks": checks,
    }
    POINT_SOURCE_ASTROMETRIC_REJECTION_VALIDATION.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    if not all(checks.values()):
        raise RuntimeError(f"Astrometric-rejection validation failed: {checks}")


if __name__ == "__main__":
    main()
