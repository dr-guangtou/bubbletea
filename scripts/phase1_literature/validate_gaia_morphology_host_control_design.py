"""Validate the frozen Gaia morphology host/control field design."""

import argparse
import json
import sys
from pathlib import Path

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN,
    GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_MANIFEST,
    GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_VALIDATION,
    GALAXY_SAMPLE_CSV,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_gaia_morphology_host_control_design import DESIGN_VERSION


def parse_arguments() -> argparse.Namespace:
    """Parse field-design artifact paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-catalog", type=Path, default=GALAXY_SAMPLE_CSV)
    parser.add_argument("--design", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_MANIFEST,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_VALIDATION,
    )
    return parser.parse_args()


def main() -> None:
    """Run deterministic design checks without Gaia outcome data."""
    arguments = parse_arguments()
    design = pd.read_csv(arguments.design)
    manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("design_version", manifest["design_version"] == DESIGN_VERSION, DESIGN_VERSION)
    check(
        "frozen_before_outcome_queries",
        manifest["design_status"] == "frozen_before_gaia_outcome_queries",
        manifest["design_status"],
    )
    check(
        "environment_deferred",
        manifest["environment_stratification_status"]
        == "deferred_existing_is_cluster_is_an_undocumented_sky_circle_proxy",
        manifest["environment_stratification_status"],
    )
    check(
        "design_digest",
        calculate_sha256(arguments.design) == manifest["output_sha256"],
        manifest["output_sha256"],
    )
    check(
        "host_catalog_digest",
        calculate_sha256(arguments.host_catalog) == manifest["host_catalog_sha256"],
        manifest["host_catalog_sha256"],
    )
    check("unique_field_ids", design["field_id"].is_unique, len(design))
    check("twelve_pairs", design["pair_id"].nunique() == 12, design["pair_id"].nunique())
    pair_role_counts = design.groupby(["pair_id", "field_role"]).size().unstack(fill_value=0)
    check(
        "one_host_and_control_per_pair",
        set(pair_role_counts.columns) == {"host", "control"} and pair_role_counts.eq(1).all().all(),
        pair_role_counts.to_dict(),
    )
    hosts = design.loc[design["field_role"].eq("host")]
    controls = design.loc[design["field_role"].eq("control")]
    stratum_counts = hosts.groupby(["luminosity_stratum", "latitude_stratum"]).size()
    check(
        "two_hosts_per_six_strata",
        len(stratum_counts) == 6 and stratum_counts.eq(2).all(),
        {"|".join(key): int(value) for key, value in stratum_counts.items()},
    )
    check(
        "control_ecliptic_latitude_match",
        controls["ecliptic_latitude_difference_deg"].le(2.0).all(),
        float(controls["ecliptic_latitude_difference_deg"].max()),
    )
    check(
        "control_absolute_galactic_latitude_match_recorded",
        controls["galactic_latitude_difference_deg"].le(7.0).all(),
        float(controls["galactic_latitude_difference_deg"].max()),
    )
    check(
        "controls_clear_current_nearby_galaxy_apertures",
        controls["minimum_nearby_galaxy_clearance_deg"].gt(0.0).all(),
        float(controls["minimum_nearby_galaxy_clearance_deg"].min()),
    )
    control_coordinates = SkyCoord(
        controls["field_ra"].to_numpy() * u.deg,
        controls["field_dec"].to_numpy() * u.deg,
    )
    separation = control_coordinates[:, None].separation(control_coordinates[None, :]).deg
    np.fill_diagonal(separation, np.inf)
    radius_sum = (
        controls["field_radius_deg"].to_numpy()[:, None]
        + controls["field_radius_deg"].to_numpy()[None, :]
    )
    check(
        "control_fields_do_not_overlap",
        bool(np.all(separation > radius_sum)),
        float(np.min(separation - radius_sum)),
    )
    check(
        "no_gaia_outcome_columns",
        not any(
            column in design.columns
            for column in ["source_id", "row_count", "density", "selection_fraction"]
        ),
        sorted(design.columns),
    )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "design_version": DESIGN_VERSION,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "checks": checks,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failed:
        failed_names = ", ".join(str(item["name"]) for item in failed)
        raise RuntimeError(f"Host/control design validation failed: {failed_names}")


if __name__ == "__main__":
    main()
