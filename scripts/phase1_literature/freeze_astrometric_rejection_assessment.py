"""Freeze the development-only astrometric-rejection assessment before measurement.

The contract keeps the fitted point-source selector unchanged. It defines a second
rule that can reject a selector-passing source when an available Gaia parallax or
proper-motion measurement is significantly inconsistent with zero.
"""

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    POINT_SOURCE_ASTROMETRIC_REJECTION_CONTRACT,
    POINT_SOURCE_LOGISTIC_MODEL,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256

DEVELOPMENT_PREDICTIONS = (
    POINT_SOURCE_LOGISTIC_MODEL.parent / "point_source_logistic_development_predictions_v1.csv"
)


def input_record(path: Path) -> dict[str, str]:
    """Return a repository-relative input path and its SHA-256 digest."""
    return {"path": str(path.relative_to(Path.cwd())), "sha256": calculate_sha256(path)}


def main() -> None:
    """Write the pre-measurement assessment contract."""
    contract = {
        "assessment_version": "point_source_astrometric_rejection_assessment_v1",
        "status": "frozen_development_only_before_measurement",
        "purpose": (
            "Measure whether a separate astrometric rejection rule improves the frozen "
            "selector without changing point_source_logistic_model_v1."
        ),
        "selection_sequence": [
            "apply_point_source_logistic_model_v1_and_its_frozen_threshold",
            "reject_a_passing_source_only_if_either_available_astrometric_significance_exceeds_the_boundary",
        ],
        "statistics": {
            "absolute_parallax_significance": "absolute(parallax) / parallax_error",
            "proper_motion_significance": (
                "covariance_aware_two_dimensional_distance_from_zero_using_pmra_pmdec_corr"
            ),
            "decision_statistic": "maximum_of_the_available_two_significances",
            "rejection_comparison": "decision_statistic_strictly_greater_than_boundary",
            "missing_measurement_policy": (
                "use_the_other_measurement_if_available; if_both_are_missing_do_not_reject"
            ),
        },
        "boundary_curve": {
            "construction": (
                "zero_plus_every_unique_finite_development_decision_statistic_plus_3_sigma"
            ),
            "literature_reference": {
                "boundary_sigma": 3.0,
                "source": "Liu et al. (2020), DOI 10.3847/1538-4365/abad91",
                "status": "reference_only_not_an_approved_bubbletea_boundary",
            },
        },
        "cohorts": {
            "positive": "benchmark_v3_development_reliable_ucds",
            "priority_contaminants": [
                "spectroscopic_star",
                "gaia_non_single_star",
                "spectroscopic_qso",
            ],
            "secondary_stress_sets": ["spectroscopic_galaxy", "hii_region"],
            "priority_summary": "equal_weight_mean_of_the_three_priority_cohort_retentions",
        },
        "reported_measurements": [
            "astrometric_measurement_availability_by_cohort",
            "selector_v1_baseline_retention_by_cohort",
            "post_rule_retention_by_cohort_at_every_boundary",
            "reliable_ucd_loss_relative_to_selector_v1",
            "priority_contaminant_reduction_relative_to_selector_v1",
            "the_3_sigma_reference_result",
        ],
        "safeguards": {
            "validation_partition_use": "prohibited",
            "ngc4698_star_use": "external_demonstration_only_not_threshold_selection",
            "host_profile_use": "prohibited_for_threshold_selection",
            "automatic_operating_point_selection": False,
            "selector_v1_modification": False,
            "future_selector_v2_requirement": (
                "new_independent_validation_cohort_and_predeclared_review_protocol"
            ),
        },
        "inputs": {
            "development_features": input_record(SELECTOR_DEVELOPMENT_FEATURES),
            "spectroscopic_stars": input_record(SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES),
            "selector_model": input_record(POINT_SOURCE_LOGISTIC_MODEL),
            "selector_model_manifest": input_record(POINT_SOURCE_LOGISTIC_MODEL_MANIFEST),
            "development_predictions": input_record(DEVELOPMENT_PREDICTIONS),
        },
    }
    POINT_SOURCE_ASTROMETRIC_REJECTION_CONTRACT.write_text(
        json.dumps(contract, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
