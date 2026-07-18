"""Build count-blind Gaia field positions for the five-host background review."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_FIELD_POSITIONS,
    BACKGROUND_REVIEW_FIELD_POSITIONS_MANIFEST,
    BACKGROUND_REVIEW_HOSTS,
    PROJECT_ROOT,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import (
    TEST_CENTER_SEPARATION_MULTIPLIER,
    TEST_GROUP_RADIUS_MULTIPLIER,
    TEST_PATCH_RADIUS_DEG,
)
from scripts.phase3_background.control_geometry import (
    constant_galactic_latitude_offset,
    physical_radius_to_angle_deg,
)

ACCEPTED_ASSOCIATION_STATE = "accepted_unique_spherical_5arcsec_v1"


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a local input file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def target_field(host: pd.Series) -> dict[str, object]:
    """Return the target-field record for one review host."""
    environment_resolved = host["association_state"] == ACCEPTED_ASSOCIATION_STATE
    return {
        "review_case": host["review_case"],
        "field_id": f"{int(host['rank'])}:target",
        "field_role": "target_test_patch",
        "host_name": host["objname"],
        "host_rank": int(host["rank"]),
        "ra_deg": float(host["ra"]),
        "dec_deg": float(host["dec"]),
        "center_separation_from_host_deg": 0.0,
        "galactic_latitude_deg": float(host["glat"]),
        "catalog_environment_role": host["catalog_environment_role"],
        "environment_association_state": host["association_state"],
        "field_geometry_state": (
            "target_measurement_environment_resolved"
            if environment_resolved
            else "target_measurement_environment_unresolved"
        ),
        "group_exclusion_clear_in_test_geometry": pd.NA,
        "eligible_for_scientific_background": False,
    }


def comparison_fields(host: pd.Series) -> list[dict[str, object]]:
    """Return provisional comparison fields only for resolved environments."""
    if host["association_state"] != ACCEPTED_ASSOCIATION_STATE:
        return []
    host_coordinate = SkyCoord(float(host["ra"]) * u.deg, float(host["dec"]) * u.deg)
    group_center = SkyCoord(
        float(host["group_principal_ra_deg"]) * u.deg,
        float(host["group_principal_dec_deg"]) * u.deg,
    )
    test_group_exclusion_radius_deg = physical_radius_to_angle_deg(
        float(host["dist_best"]),
        1000 * TEST_GROUP_RADIUS_MULTIPLIER * float(host["group_second_turnaround_radius_mpc"]),
    )
    center_separation_deg = TEST_CENTER_SEPARATION_MULTIPLIER * (
        test_group_exclusion_radius_deg + TEST_PATCH_RADIUS_DEG
    )
    one_galaxy_case = host["catalog_environment_role"] == "catalog_isolated_principal"
    fields = []
    for direction, direction_name in [(-1, "west"), (1, "east")]:
        coordinate = constant_galactic_latitude_offset(
            host_coordinate, center_separation_deg, direction
        )
        group_center_separation_deg = coordinate.separation(group_center).deg
        group_exclusion_clear = group_center_separation_deg >= (
            test_group_exclusion_radius_deg + TEST_PATCH_RADIUS_DEG
        )
        if one_galaxy_case:
            geometry_state = "provisional_one_galaxy_catalog_geometry"
        elif group_exclusion_clear:
            geometry_state = "diagnostic_group_geometry_clear_of_test_circle"
        else:
            geometry_state = "diagnostic_group_geometry_intersects_test_circle"
        fields.append(
            {
                "review_case": host["review_case"],
                "field_id": f"{int(host['rank'])}:{direction_name}",
                "field_role": f"{direction_name}_test_patch",
                "host_name": host["objname"],
                "host_rank": int(host["rank"]),
                "ra_deg": coordinate.ra.deg,
                "dec_deg": coordinate.dec.deg,
                "center_separation_from_host_deg": center_separation_deg,
                "galactic_latitude_deg": coordinate.galactic.b.deg,
                "catalog_environment_role": host["catalog_environment_role"],
                "environment_association_state": host["association_state"],
                "field_geometry_state": geometry_state,
                "group_exclusion_clear_in_test_geometry": group_exclusion_clear,
                "eligible_for_scientific_background": False,
                "test_group_exclusion_radius_deg": test_group_exclusion_radius_deg,
                "group_center_separation_deg": group_center_separation_deg,
            }
        )
    return fields


def main() -> None:
    """Write review positions and their count-blind validation manifest."""
    hosts = pd.read_csv(BACKGROUND_REVIEW_HOSTS)
    rows = []
    for _, host in hosts.iterrows():
        rows.append(target_field(host))
        rows.extend(comparison_fields(host))
    positions = pd.DataFrame(rows)
    target_latitude = positions.loc[
        positions["field_role"].eq("target_test_patch"),
        ["host_rank", "galactic_latitude_deg"],
    ].rename(columns={"galactic_latitude_deg": "target_galactic_latitude_deg"})
    comparisons = positions.loc[~positions["field_role"].eq("target_test_patch")].merge(
        target_latitude, on="host_rank", validate="many_to_one"
    )
    checks = {
        "five_target_fields": positions["field_role"].eq("target_test_patch").sum() == 5,
        "eight_comparison_fields": (~positions["field_role"].eq("target_test_patch")).sum() == 8,
        "all_hosts_represented": positions["host_rank"].nunique() == 5,
        "comparison_latitudes_match_targets": (
            comparisons["galactic_latitude_deg"] - comparisons["target_galactic_latitude_deg"]
        )
        .abs()
        .max()
        <= 1e-10,
        "unresolved_environment_has_no_comparison": positions.loc[
            positions["environment_association_state"].ne(ACCEPTED_ASSOCIATION_STATE)
        ]["field_role"]
        .eq("target_test_patch")
        .all(),
        "no_field_is_approved_scientific_background": (
            ~positions["eligible_for_scientific_background"].astype(bool)
        ).all(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    BACKGROUND_REVIEW_FIELD_POSITIONS.parent.mkdir(parents=True, exist_ok=True)
    positions.to_csv(BACKGROUND_REVIEW_FIELD_POSITIONS, index=False)
    manifest = {
        "position_version": "background_review_field_positions_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "selection_contract": "host_and_environment_geometry_only_no_gaia_counts",
        "input": {
            "path": str(BACKGROUND_REVIEW_HOSTS.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(BACKGROUND_REVIEW_HOSTS),
        },
        "temporary_test_values": {
            "patch_radius_deg": TEST_PATCH_RADIUS_DEG,
            "group_radius_multiplier": TEST_GROUP_RADIUS_MULTIPLIER,
            "center_separation_multiplier": TEST_CENTER_SEPARATION_MULTIPLIER,
        },
        "field_count": len(positions),
        "target_field_count": int(positions["field_role"].eq("target_test_patch").sum()),
        "comparison_field_count": int((~positions["field_role"].eq("target_test_patch")).sum()),
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    BACKGROUND_REVIEW_FIELD_POSITIONS_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Review field-position validation failed: {checks}")


if __name__ == "__main__":
    main()
