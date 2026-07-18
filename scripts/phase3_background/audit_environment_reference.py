"""Audit host associations to the Kourkchi-Tully 2017 group catalog."""

import gzip
import json
import re
import sys
from pathlib import Path

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord, search_around_sky

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GALAXY_SAMPLE_CSV,
    KOURKCHI_TULLY_2017_GROUPS,
    KOURKCHI_TULLY_2017_MEMBERS,
    KOURKCHI_TULLY_ENVIRONMENT_AUDIT,
    KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES,
)

MEMBER_COLUMNS = [
    "pgc",
    "name",
    "ra_deg",
    "dec_deg",
    "galactic_longitude_deg",
    "galactic_latitude_deg",
    "supergalactic_longitude_deg",
    "supergalactic_latitude_deg",
    "morphological_type",
    "b_magnitude",
    "ks_magnitude",
    "log_k_luminosity",
    "heliocentric_velocity_km_s",
    "local_sheet_velocity_km_s",
    "distance_mpc",
    "distance_percent_error",
    "group_principal_pgc",
]
MEMBER_COLSPECS = [
    (0, 7),
    (8, 36),
    (37, 45),
    (46, 54),
    (55, 63),
    (64, 72),
    (73, 81),
    (82, 90),
    (91, 95),
    (96, 101),
    (102, 107),
    (108, 113),
    (114, 118),
    (119, 123),
    (124, 130),
    (131, 133),
    (134, 141),
]
GROUP_COLUMNS = [
    "group_principal_pgc",
    "association_principal_pgc",
    "member_count",
    "galactic_longitude_deg",
    "galactic_latitude_deg",
    "supergalactic_longitude_deg",
    "supergalactic_latitude_deg",
    "total_ks_magnitude",
    "log_k_luminosity",
    "heliocentric_velocity_km_s",
    "local_sheet_velocity_km_s",
    "distance_member_count",
    "distance_mpc",
    "distance_percent_error",
    "luminosity_velocity_dispersion_km_s",
    "measured_velocity_dispersion_km_s",
    "second_turnaround_radius_mpc",
    "projected_virial_radius_mpc",
    "log_luminosity_mass",
    "log_dynamical_mass",
]
GROUP_COLSPECS = [
    (0, 7),
    (8, 15),
    (16, 19),
    (20, 28),
    (29, 37),
    (38, 46),
    (47, 55),
    (56, 61),
    (62, 67),
    (68, 72),
    (73, 77),
    (78, 81),
    (82, 87),
    (88, 90),
    (91, 94),
    (95, 98),
    (99, 104),
    (105, 110),
    (111, 117),
    (118, 124),
]


def read_fixed_width_gzip(path: Path, colspecs: list[tuple[int, int]], names: list[str]):
    """Parse a CDS fixed-width gzip table from its published byte ranges."""
    with gzip.open(path, mode="rt", encoding="ascii") as handle:
        return pd.read_fwf(handle, colspecs=colspecs, names=names)


def environment_role(row: pd.Series) -> str:
    """Describe the catalog role without asserting host identity."""
    if int(row["pgc"]) == int(row["group_principal_pgc"]):
        if int(row["member_count"]) == 1:
            return "catalog_isolated_principal"
        return "catalog_group_principal"
    return "catalog_group_member"


def normalize_identifier(value: object) -> str:
    """Normalize common catalog names for agreement diagnostics only."""
    normalized = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    match = re.fullmatch(r"(NGC|IC|UGC|PGC)0*([0-9]+)", normalized)
    if match:
        return f"{match.group(1)}{int(match.group(2))}"
    return normalized


def main() -> None:
    """Write nearest-neighbor proposals and measured coverage tiers."""
    for path in [KOURKCHI_TULLY_2017_MEMBERS, KOURKCHI_TULLY_2017_GROUPS]:
        if not path.exists():
            raise FileNotFoundError(
                f"Missing external catalog {path}; set BUBBLETEA_EXTERNAL_DATA correctly"
            )
    hosts = pd.read_csv(GALAXY_SAMPLE_CSV)
    members = read_fixed_width_gzip(KOURKCHI_TULLY_2017_MEMBERS, MEMBER_COLSPECS, MEMBER_COLUMNS)
    groups = read_fixed_width_gzip(KOURKCHI_TULLY_2017_GROUPS, GROUP_COLSPECS, GROUP_COLUMNS)
    if len(members) != 15_004 or members["pgc"].duplicated().any():
        raise RuntimeError("Kourkchi-Tully member-table identity contract failed")
    if groups["group_principal_pgc"].duplicated().any():
        raise RuntimeError("Kourkchi-Tully group identifiers are not unique")
    members = members.merge(groups, on="group_principal_pgc", how="left", suffixes=("", "_group"))
    if members["member_count"].isna().any():
        raise RuntimeError("A member row lacks its group-property record")

    host_coordinates = SkyCoord(hosts["ra"].to_numpy() * u.deg, hosts["dec"].to_numpy() * u.deg)
    member_coordinates = SkyCoord(
        members["ra_deg"].to_numpy() * u.deg,
        members["dec_deg"].to_numpy() * u.deg,
    )
    member_index, separation, _ = host_coordinates.match_to_catalog_sky(member_coordinates)
    nearby_host_index, _, _, _ = search_around_sky(
        host_coordinates, member_coordinates, 5 * u.arcsec
    )
    nearby_counts = (
        pd.Series(nearby_host_index).value_counts().reindex(range(len(hosts)), fill_value=0)
    )
    shifted_control_match_counts = {}
    for position_angle_deg in range(0, 360, 45):
        shifted_coordinates = host_coordinates.directional_offset_by(
            position_angle_deg * u.deg, 1 * u.deg
        )
        shifted_host_index, _, _, _ = search_around_sky(
            shifted_coordinates, member_coordinates, 5 * u.arcsec
        )
        shifted_control_match_counts[str(position_angle_deg)] = len(shifted_host_index)
    nearest = members.iloc[member_index].reset_index(drop=True)
    candidates = hosts[["rank", "objname", "ra", "dec", "dist_best", "log_L_K"]].copy()
    candidates["nearest_separation_arcsec"] = separation.arcsec
    candidates["catalog_pgc"] = nearest["pgc"].astype(int)
    candidates["catalog_name"] = nearest["name"].str.strip()
    candidates["normalized_name_agreement"] = [
        normalize_identifier(host_name) == normalize_identifier(catalog_name)
        for host_name, catalog_name in zip(
            candidates["objname"], candidates["catalog_name"], strict=True
        )
    ]
    candidates["catalog_ra_deg"] = nearest["ra_deg"]
    candidates["catalog_dec_deg"] = nearest["dec_deg"]
    candidates["group_principal_pgc"] = nearest["group_principal_pgc"].astype(int)
    candidates["group_member_count"] = nearest["member_count"].astype(int)
    candidates["catalog_environment_role"] = nearest.apply(environment_role, axis=1)
    candidates["group_second_turnaround_radius_mpc"] = nearest["second_turnaround_radius_mpc"]
    candidates["group_log_luminosity_mass"] = nearest["log_luminosity_mass"]
    candidates["catalog_distance_mpc"] = nearest["distance_mpc"]
    candidates["absolute_distance_difference_mpc"] = (
        candidates["dist_best"] - candidates["catalog_distance_mpc"]
    ).abs()
    candidates["fractional_distance_difference"] = (
        candidates["absolute_distance_difference_mpc"] / candidates["dist_best"]
    )
    candidates["catalog_neighbors_within_5_arcsec"] = nearby_counts.to_numpy()
    unique_close = candidates["nearest_separation_arcsec"].le(5) & candidates[
        "catalog_neighbors_within_5_arcsec"
    ].eq(1)
    ambiguous_close = candidates["catalog_neighbors_within_5_arcsec"].gt(1)
    candidates["association_state"] = "unmatched_beyond_5_arcsec"
    candidates.loc[unique_close, "association_state"] = "accepted_unique_spherical_5arcsec_v1"
    candidates.loc[ambiguous_close, "association_state"] = (
        "manual_ambiguous_multiple_within_5arcsec"
    )
    KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES, index=False)

    tiers_arcsec = [1, 3, 5, 10, 30, 60]
    within_five = candidates["nearest_separation_arcsec"].le(5)
    within_five_rows = candidates.loc[within_five]
    shared_pgc = within_five_rows["catalog_pgc"].duplicated(keep=False)
    report = {
        "audit_version": "kourkchi_tully_environment_audit_v1",
        "audit_status": "unique_5arcsec_associations_accepted_ambiguities_preserved",
        "host_count": len(hosts),
        "catalog_member_count": len(members),
        "catalog_group_count": len(groups),
        "nearest_separation_tier_counts": {
            str(limit): int(candidates["nearest_separation_arcsec"].le(limit).sum())
            for limit in tiers_arcsec
        },
        "nearest_separation_arcsec": {
            "minimum": float(candidates["nearest_separation_arcsec"].min()),
            "median": float(candidates["nearest_separation_arcsec"].median()),
            "maximum": float(candidates["nearest_separation_arcsec"].max()),
        },
        "proposed_role_counts_within_5_arcsec": candidates.loc[
            within_five, "catalog_environment_role"
        ]
        .value_counts()
        .sort_index()
        .to_dict(),
        "identity_diagnostics_within_5_arcsec": {
            "normalized_name_agreement_count": int(
                within_five_rows["normalized_name_agreement"].sum()
            ),
            "distinct_catalog_pgc_count": int(within_five_rows["catalog_pgc"].nunique()),
            "rows_sharing_catalog_pgc_count": int(shared_pgc.sum()),
            "shared_catalog_pgc_count": int(
                within_five_rows.loc[shared_pgc, "catalog_pgc"].nunique()
            ),
            "fractional_distance_difference_median": float(
                within_five_rows["fractional_distance_difference"].median()
            ),
            "fractional_distance_difference_90th_percentile": float(
                within_five_rows["fractional_distance_difference"].quantile(0.9)
            ),
            "fractional_distance_difference_over_0_5_count": int(
                within_five_rows["fractional_distance_difference"].gt(0.5).sum()
            ),
        },
        "association_state_counts": candidates["association_state"]
        .value_counts()
        .sort_index()
        .to_dict(),
        "shifted_control_calibration": {
            "offset_deg": 1,
            "position_angle_step_deg": 45,
            "shifted_position_count": len(hosts) * len(shifted_control_match_counts),
            "match_radius_arcsec": 5,
            "match_counts_by_position_angle_deg": shifted_control_match_counts,
            "total_match_count": sum(shifted_control_match_counts.values()),
        },
        "output": str(KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES),
        "next_gate": "audit ambiguous and unmatched hosts; do not infer environment for them",
    }
    KOURKCHI_TULLY_ENVIRONMENT_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    KOURKCHI_TULLY_ENVIRONMENT_AUDIT.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
