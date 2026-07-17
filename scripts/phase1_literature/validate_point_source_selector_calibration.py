"""Validate development-only point-source selector calibration artifacts."""

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
    VALIDATION_BENCHMARK,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.calibrate_point_source_selector import (
    ASTROMETRIC_PENALTY_WEIGHTS,
    CALIBRATION_VERSION,
    CORE_AEN_WEIGHTS,
    PRIORITY_COHORTS,
    TARGET_UCD_COMPLETENESS,
)


def parse_arguments() -> argparse.Namespace:
    """Parse calibration artifact paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--components", type=Path, default=POINT_SOURCE_SELECTOR_COMPONENTS)
    parser.add_argument(
        "--operating-points", type=Path, default=POINT_SOURCE_SELECTOR_OPERATING_POINTS
    )
    parser.add_argument("--summary", type=Path, default=POINT_SOURCE_SELECTOR_CALIBRATION)
    parser.add_argument(
        "--output",
        type=Path,
        default=POINT_SOURCE_SELECTOR_CALIBRATION.with_name(
            "point_source_selector_calibration_validation_v3.json"
        ),
    )
    return parser.parse_args()


def main() -> None:
    """Run partition, grid, objective, hash, and decision-state checks."""
    arguments = parse_arguments()
    benchmark = pd.read_csv(arguments.benchmark, dtype={"gaia_dr3_id": str})
    components = pd.read_csv(arguments.components, dtype={"gaia_dr3_id": str})
    points = pd.read_csv(arguments.operating_points)
    summary = json.loads(arguments.summary.read_text(encoding="utf-8"))
    validation_ids = set(benchmark.loc[benchmark["partition"].eq("validation"), "gaia_dr3_id"])
    checks = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    expected_rows = (
        len(CORE_AEN_WEIGHTS) * len(ASTROMETRIC_PENALTY_WEIGHTS) * len(TARGET_UCD_COMPLETENESS)
    )
    priority_columns = [f"{cohort}_retention_fraction" for cohort in PRIORITY_COHORTS]
    recomputed_macro = points[priority_columns].mean(axis=1)
    check(
        "calibration_version",
        summary["calibration_version"] == CALIBRATION_VERSION,
        summary["calibration_version"],
    )
    check(
        "validation_partition_blind",
        summary["validation_partition_inspected"] is False,
        summary["validation_partition_inspected"],
    )
    check(
        "no_validation_identifiers",
        set(components["gaia_dr3_id"]).isdisjoint(validation_ids),
        len(set(components["gaia_dr3_id"]).intersection(validation_ids)),
    )
    check(
        "priority_cohorts",
        summary["priority_cohorts"] == PRIORITY_COHORTS,
        summary["priority_cohorts"],
    )
    check(
        "equal_cohort_objective",
        summary["priority_objective"] == "equal_cohort_mean_retention",
        summary["priority_objective"],
    )
    check("operating_point_count", len(points) == expected_rows, len(points))
    check(
        "aen_weight_grid",
        set(points["aen_core_weight"]) == set(CORE_AEN_WEIGHTS),
        sorted(points["aen_core_weight"].unique()),
    )
    check(
        "astrometric_weight_grid",
        set(points["astrometric_penalty_weight"]) == set(ASTROMETRIC_PENALTY_WEIGHTS),
        sorted(points["astrometric_penalty_weight"].unique()),
    )
    check(
        "completeness_grid",
        set(points["target_ucd_completeness"]) == set(TARGET_UCD_COMPLETENESS),
        sorted(points["target_ucd_completeness"].unique()),
    )
    check(
        "macro_retention_reproduced",
        np.allclose(points["equal_cohort_priority_retention"], recomputed_macro),
        float(np.max(np.abs(points["equal_cohort_priority_retention"] - recomputed_macro))),
    )
    check(
        "measured_completeness_meets_target",
        points["measured_ucd_completeness"].ge(points["target_ucd_completeness"]).all(),
        int(points["measured_ucd_completeness"].lt(points["target_ucd_completeness"]).sum()),
    )
    check(
        "components_hash",
        summary["components_sha256"] == calculate_sha256(arguments.components),
        summary["components_sha256"],
    )
    check(
        "operating_points_hash",
        summary["operating_points_sha256"] == calculate_sha256(arguments.operating_points),
        summary["operating_points_sha256"],
    )
    check(
        "threshold_not_frozen",
        summary["decision_status"] == "operating_points_only_no_threshold_frozen",
        summary["decision_status"],
    )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "calibration_version": CALIBRATION_VERSION,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "checks": checks,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failed:
        raise RuntimeError(
            "Point-source selector calibration validation failed: "
            + ", ".join(item["name"] for item in failed)
        )


if __name__ == "__main__":
    main()
