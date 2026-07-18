"""Measure how published group R2t scales enclose accepted host members."""

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
    KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES,
    KOURKCHI_TULLY_HALO_EXCLUSION_ANALYSIS,
    KOURKCHI_TULLY_HALO_EXCLUSION_OUTLIERS,
)

SAFETY_FACTORS = [1, 1.25, 1.5, 2, 3]


def main() -> None:
    """Write internal-consistency metrics without freezing an exclusion factor."""
    rows = pd.read_csv(KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES)
    accepted = rows.loc[rows["association_state"].eq("accepted_unique_spherical_5arcsec_v1")].copy()
    host_coordinates = SkyCoord(
        accepted["catalog_ra_deg"].to_numpy() * u.deg,
        accepted["catalog_dec_deg"].to_numpy() * u.deg,
    )
    principal_coordinates = SkyCoord(
        accepted["group_principal_ra_deg"].to_numpy() * u.deg,
        accepted["group_principal_dec_deg"].to_numpy() * u.deg,
    )
    separation_rad = host_coordinates.separation(principal_coordinates).rad
    accepted["projected_group_radius_mpc"] = np.tan(separation_rad) * accepted["dist_best"]
    accepted["projected_radius_over_group_r2t"] = (
        accepted["projected_group_radius_mpc"] / accepted["group_second_turnaround_radius_mpc"]
    )
    association_coordinates = SkyCoord(
        accepted["association_principal_ra_deg"].to_numpy() * u.deg,
        accepted["association_principal_dec_deg"].to_numpy() * u.deg,
    )
    association_separation_rad = host_coordinates.separation(association_coordinates).rad
    accepted["projected_association_radius_mpc"] = (
        np.tan(association_separation_rad) * accepted["association_distance_mpc"]
    )
    accepted["projected_radius_over_association_r1t"] = (
        accepted["projected_association_radius_mpc"]
        / accepted["association_first_turnaround_radius_mpc"]
    )
    group_members = accepted.loc[
        accepted["catalog_environment_role"].eq("catalog_group_member")
    ].copy()
    ratios = group_members["projected_radius_over_group_r2t"]
    association_ratios = group_members["projected_radius_over_association_r1t"]
    outliers = group_members.loc[ratios.gt(1.5)].sort_values(
        "projected_radius_over_group_r2t", ascending=False
    )
    KOURKCHI_TULLY_HALO_EXCLUSION_OUTLIERS.parent.mkdir(parents=True, exist_ok=True)
    outliers.to_csv(KOURKCHI_TULLY_HALO_EXCLUSION_OUTLIERS, index=False)
    report = {
        "analysis_version": "kourkchi_tully_halo_exclusion_analysis_v1",
        "analysis_status": "internal_catalog_consistency_only_safety_factor_not_frozen",
        "accepted_host_count": len(accepted),
        "accepted_group_member_count": len(group_members),
        "enclosure_by_r2t_factor": {
            str(factor): {
                "enclosed_count": int(ratios.le(factor).sum()),
                "enclosed_fraction": float(ratios.le(factor).mean()),
                "outside_count": int(ratios.gt(factor).sum()),
            }
            for factor in SAFETY_FACTORS
        },
        "ratio_quantiles": {
            str(quantile): float(ratios.quantile(quantile))
            for quantile in [0.5, 0.9, 0.95, 0.99, 1]
        },
        "association_r1t_enclosure": {
            "usable_count": int(association_ratios.notna().sum()),
            "within_1_count": int(association_ratios.le(1).sum()),
            "within_1_fraction": float(association_ratios.le(1).mean()),
            "maximum_ratio": float(association_ratios.max()),
        },
        "interpretation": (
            "R2t and membership come from the same catalog construction; enclosure is not an "
            "independent halo validation. Review outliers and external environment evidence "
            "before freezing a safety factor."
        ),
        "outlier_output": str(KOURKCHI_TULLY_HALO_EXCLUSION_OUTLIERS),
    }
    KOURKCHI_TULLY_HALO_EXCLUSION_ANALYSIS.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
