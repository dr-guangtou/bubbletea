"""Calibrate point-source-priority selector operating points on development data.

The script reports a grid of interpretable score configurations and completeness
operating points. It does not inspect validation rows or freeze a threshold.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    POINT_SOURCE_SELECTOR_CALIBRATION,
    POINT_SOURCE_SELECTOR_COMPONENTS,
    POINT_SOURCE_SELECTOR_OPERATING_POINTS,
    SELECTOR_DEVELOPMENT_FEATURES,
    SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES,
)
from scripts.phase1_literature.analyze_selector_development import add_derived_features
from scripts.phase1_literature.audit_reference_data import calculate_sha256

CALIBRATION_VERSION = "point_source_selector_calibration_v3"
PRIORITY_COHORTS = ["spectroscopic_star", "gaia_non_single_star", "spectroscopic_qso"]
CORE_AEN_WEIGHTS = [0.25, 0.5, 0.75]
ASTROMETRIC_PENALTY_WEIGHTS = [0.0, 0.1, 0.2, 0.3]
TARGET_UCD_COMPLETENESS = [0.8, 0.85, 0.9, 0.95]


def parse_arguments() -> argparse.Namespace:
    """Parse development, stellar, and output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES)
    parser.add_argument("--stars", type=Path, default=SPECTROSCOPIC_STELLAR_REFERENCE_MATCHES)
    parser.add_argument("--components", type=Path, default=POINT_SOURCE_SELECTOR_COMPONENTS)
    parser.add_argument(
        "--operating-points", type=Path, default=POINT_SOURCE_SELECTOR_OPERATING_POINTS
    )
    parser.add_argument("--summary", type=Path, default=POINT_SOURCE_SELECTOR_CALIBRATION)
    return parser.parse_args()


def cohort_cdf(values: pd.Series, reference_groups: list[pd.Series]) -> pd.Series:
    """Return the equal-cohort mean empirical CDF for each finite value."""
    output = np.full(len(values), np.nan)
    finite_values = values.to_numpy(dtype=float)
    finite = np.isfinite(finite_values)
    cdfs = []
    for group in reference_groups:
        reference = np.sort(group.to_numpy(dtype=float))
        reference = reference[np.isfinite(reference)]
        cdfs.append(
            np.searchsorted(reference, finite_values[finite], side="right") / len(reference)
        )
    output[finite] = np.mean(cdfs, axis=0)
    return pd.Series(output, index=values.index)


def build_rows(development_path: Path, stars_path: Path) -> pd.DataFrame:
    """Combine allowed development cohorts with the disjoint stellar supplement."""
    development = add_derived_features(pd.read_csv(development_path, dtype={"gaia_dr3_id": str}))
    stars = add_derived_features(pd.read_csv(stars_path, dtype={"source_id": str}))
    development["calibration_cohort"] = development["label_subtype"].map(
        {
            "ucd_confirmed": "confirmed_ucd",
            "ucd_candidate": "candidate_ucd",
            "gaia_non_single_star": "gaia_non_single_star",
            "spectroscopic_qso": "spectroscopic_qso",
            "spectroscopic_galaxy": "spectroscopic_galaxy",
            "compact_hii_region": "hii_region",
            "dwarf_galaxy_hii_region": "hii_region",
            "reported_non_ucd_comparison": "reported_non_ucd",
        }
    )
    stars["calibration_cohort"] = "spectroscopic_star"
    stars["gaia_dr3_id"] = stars["source_id"]
    shared_columns = sorted(set(development.columns).intersection(stars.columns))
    rows = pd.concat([development[shared_columns], stars[shared_columns]], ignore_index=True)
    return rows.loc[rows["calibration_cohort"].notna()].copy()


def add_components(rows: pd.DataFrame) -> pd.DataFrame:
    """Add equal-cohort ranks and a conditional astrometric compatibility term."""
    priority = {
        cohort: rows.loc[rows["calibration_cohort"].eq(cohort)] for cohort in PRIORITY_COHORTS
    }
    rows = rows.copy()
    rows["aen_priority_cdf"] = cohort_cdf(
        rows["astrometric_excess_noise"],
        [priority[cohort]["astrometric_excess_noise"] for cohort in PRIORITY_COHORTS],
    )
    rows["flux_excess_priority_cdf"] = cohort_cdf(
        rows["phot_bp_rp_excess_factor"],
        [priority[cohort]["phot_bp_rp_excess_factor"] for cohort in PRIORITY_COHORTS],
    )
    astrometric_reference_cohorts = ["spectroscopic_star", "gaia_non_single_star"]
    pm_cdf = cohort_cdf(
        rows["proper_motion_zero_significance"],
        [
            priority[cohort]["proper_motion_zero_significance"]
            for cohort in astrometric_reference_cohorts
        ],
    )
    parallax_cdf = cohort_cdf(
        rows["absolute_parallax_zero_significance"],
        [
            priority[cohort]["absolute_parallax_zero_significance"]
            for cohort in astrometric_reference_cohorts
        ],
    )
    available = pd.concat([pm_cdf, parallax_cdf], axis=1)
    rows["astrometric_compatibility"] = 1.0 - available.mean(axis=1, skipna=True)
    rows.loc[available.notna().sum(axis=1).eq(0), "astrometric_compatibility"] = 1.0
    return rows


def score_rows(rows: pd.DataFrame, aen_weight: float, penalty_weight: float) -> pd.Series:
    """Return the core rank with a bounded conditional astrometric penalty."""
    core_terms = pd.concat(
        [
            rows["aen_priority_cdf"] * aen_weight,
            rows["flux_excess_priority_cdf"] * (1.0 - aen_weight),
        ],
        axis=1,
    )
    term_weights = pd.concat(
        [
            rows["aen_priority_cdf"].notna().astype(float) * aen_weight,
            rows["flux_excess_priority_cdf"].notna().astype(float) * (1.0 - aen_weight),
        ],
        axis=1,
    )
    core = core_terms.sum(axis=1, skipna=True) / term_weights.sum(axis=1)
    return core * (1.0 - penalty_weight * (1.0 - rows["astrometric_compatibility"]))


def threshold_for_completeness(scores: pd.Series, target: float) -> float:
    """Return the observed-score cutoff retaining at least the requested fraction."""
    ordered = np.sort(scores.dropna().to_numpy(dtype=float))[::-1]
    retained_count = int(np.ceil(target * len(ordered)))
    return float(ordered[retained_count - 1])


def main() -> None:
    """Write score components, operating-point grid, and calibration summary."""
    arguments = parse_arguments()
    rows = add_components(build_rows(arguments.development, arguments.stars))
    component_columns = [
        "gaia_dr3_id",
        "calibration_cohort",
        "aen_priority_cdf",
        "flux_excess_priority_cdf",
        "astrometric_compatibility",
        "bp_rp",
    ]
    arguments.components.parent.mkdir(parents=True, exist_ok=True)
    rows[component_columns].to_csv(arguments.components, index=False)

    results = []
    ucd_mask = rows["calibration_cohort"].eq("confirmed_ucd")
    reporting_cohorts = [
        *PRIORITY_COHORTS,
        "candidate_ucd",
        "spectroscopic_galaxy",
        "hii_region",
        "reported_non_ucd",
    ]
    for aen_weight in CORE_AEN_WEIGHTS:
        for penalty_weight in ASTROMETRIC_PENALTY_WEIGHTS:
            scores = score_rows(rows, aen_weight, penalty_weight)
            for target in TARGET_UCD_COMPLETENESS:
                threshold = threshold_for_completeness(scores.loc[ucd_mask], target)
                selected = scores.ge(threshold)
                record = {
                    "calibration_version": CALIBRATION_VERSION,
                    "aen_core_weight": aen_weight,
                    "flux_excess_core_weight": 1.0 - aen_weight,
                    "astrometric_penalty_weight": penalty_weight,
                    "target_ucd_completeness": target,
                    "score_threshold": threshold,
                    "measured_ucd_completeness": float(selected.loc[ucd_mask].mean()),
                }
                priority_fractions = []
                for cohort in reporting_cohorts:
                    mask = rows["calibration_cohort"].eq(cohort)
                    fraction = float(selected.loc[mask].mean())
                    record[f"{cohort}_retention_fraction"] = fraction
                    if cohort in PRIORITY_COHORTS:
                        priority_fractions.append(fraction)
                record["equal_cohort_priority_retention"] = float(np.mean(priority_fractions))
                results.append(record)
    operating_points = pd.DataFrame(results).sort_values(
        ["target_ucd_completeness", "equal_cohort_priority_retention"]
    )
    arguments.operating_points.parent.mkdir(parents=True, exist_ok=True)
    operating_points.to_csv(arguments.operating_points, index=False)

    color_results = []
    ucd_colors = rows.loc[ucd_mask, "bp_rp"].dropna().sort_values()
    for target in TARGET_UCD_COMPLETENESS:
        cutoff = float(
            ucd_colors.iloc[max(0, len(ucd_colors) - int(np.ceil(target * len(ucd_colors))))]
        )
        passes = rows["bp_rp"].ge(cutoff)
        color_results.append(
            {
                "target_ucd_completeness": target,
                "bp_rp_minimum": cutoff,
                "measured_ucd_completeness": float(passes.loc[ucd_mask].mean()),
                "hii_retention_fraction": float(
                    passes.loc[rows["calibration_cohort"].eq("hii_region")].mean()
                ),
            }
        )
    summary = {
        "calibration_version": CALIBRATION_VERSION,
        "validation_partition_inspected": False,
        "priority_cohorts": PRIORITY_COHORTS,
        "priority_objective": "equal_cohort_mean_retention",
        "galaxy_role": "secondary_stress_not_primary_optimization",
        "hii_role": "separate_color_safeguard",
        "null_policy": {
            "missing_flux_excess": "score_from_available_aen_core_term",
            "missing_five_parameter_astrometry": "neutral_no_astrometric_penalty",
        },
        "grid": {
            "aen_core_weights": CORE_AEN_WEIGHTS,
            "astrometric_penalty_weights": ASTROMETRIC_PENALTY_WEIGHTS,
            "target_ucd_completeness": TARGET_UCD_COMPLETENESS,
        },
        "color_safeguard_grid": color_results,
        "counts": rows["calibration_cohort"].value_counts().sort_index().to_dict(),
        "inputs": {
            "development_sha256": calculate_sha256(arguments.development),
            "stars_sha256": calculate_sha256(arguments.stars),
        },
        "components_sha256": calculate_sha256(arguments.components),
        "operating_points_sha256": calculate_sha256(arguments.operating_points),
        "decision_status": "operating_points_only_no_threshold_frozen",
    }
    arguments.summary.parent.mkdir(parents=True, exist_ok=True)
    arguments.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
