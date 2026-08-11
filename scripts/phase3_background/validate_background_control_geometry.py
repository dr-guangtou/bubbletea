"""Build and validate the five-case BT-005 control-geometry fixture."""

import json
import sys
from pathlib import Path

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_CONTROL_GEOMETRY_FIXTURE,
    BACKGROUND_CONTROL_GEOMETRY_VALIDATION,
)
from scripts.phase3_background.control_geometry import (
    HostControlGeometry,
    NeighborExclusion,
    evaluate_candidates,
    generate_symmetric_candidates,
)

SEPARATION_MULTIPLIERS = (1.2, 1.8)


def build_fixture() -> tuple[list[HostControlGeometry], dict[str, list[NeighborExclusion]]]:
    """Return synthetic cases whose numbers are test inputs, not host estimates."""
    hosts = [
        HostControlGeometry("nearby_isolated", 150, 40, 3.7, 100, 250, 1.5, "isolated_central"),
        HostControlGeometry("distant_isolated", 30, -45, 22, 100, 300, 1.5, "isolated_central"),
        HostControlGeometry("cluster_central", 180, 12, 16.8, 100, 350, 1.5, "cluster_unresolved"),
        HostControlGeometry("satellite", 200, -20, 10, 100, 180, 1.5, "satellite_unresolved"),
        HostControlGeometry("neighbor_case", 250, 35, 18, 100, 250, 1.5, "isolated_central"),
    ]
    neighbor_host = hosts[-1]
    east_candidate = generate_symmetric_candidates(neighbor_host, SEPARATION_MULTIPLIERS)[1]
    neighbors = {
        "neighbor_case": [
            NeighborExclusion(
                "synthetic_neighbor",
                float(east_candidate["ra_deg"]),
                float(east_candidate["dec_deg"]),
                0.5,
            )
        ]
    }
    return hosts, neighbors


def main() -> None:
    """Write the fixture and require all predeclared geometry behaviors."""
    hosts, neighbors = build_fixture()
    rows = []
    for host in hosts:
        candidates = generate_symmetric_candidates(host, SEPARATION_MULTIPLIERS)
        rows.extend(evaluate_candidates(host, candidates, neighbors.get(host.host_id, [])))
    fixture = pd.DataFrame(rows)
    BACKGROUND_CONTROL_GEOMETRY_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    fixture.to_csv(BACKGROUND_CONTROL_GEOMETRY_FIXTURE, index=False)

    nearby = fixture.loc[fixture["host_id"].eq("nearby_isolated")]
    cluster = fixture.loc[fixture["host_id"].eq("cluster_central")]
    satellite = fixture.loc[fixture["host_id"].eq("satellite")]
    neighbor = fixture.loc[fixture["host_id"].eq("neighbor_case")]
    latitude_difference = []
    for host in hosts:
        host_latitude = SkyCoord(host.ra_deg * u.deg, host.dec_deg * u.deg).galactic.b.deg
        values = fixture.loc[fixture["host_id"].eq(host.host_id), "galactic_latitude_deg"]
        latitude_difference.extend((values - host_latitude).abs().tolist())
    checks = {
        "five_fixture_cases": fixture["host_id"].nunique() == 5,
        "four_symmetric_candidates_per_case": len(fixture) == 20,
        "constant_galactic_latitude": max(latitude_difference) <= 1e-10,
        "nearby_case_exceeds_legacy_two_degree_cap": nearby["halo_exclusion_radius_deg"].min() > 2,
        "isolated_cases_have_accepted_controls": fixture.loc[
            fixture["environment_state"].eq("isolated_central")
        ]
        .groupby("host_id")["geometry_status"]
        .apply(lambda values: values.eq("accepted").any())
        .all(),
        "cluster_inference_blocked": cluster["rejection_reasons"]
        .str.contains("unresolved_environment")
        .all(),
        "satellite_inference_blocked": satellite["rejection_reasons"]
        .str.contains("unresolved_environment")
        .all(),
        "neighbor_intersection_rejected": neighbor["rejection_reasons"]
        .str.contains("intersects_neighbor_halo_exclusion")
        .any(),
        "neighbor_alternatives_preserved": neighbor["geometry_status"].eq("accepted").any(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    report = {
        "validation_version": "background_control_geometry_validation_v1",
        "fixture_scope": "synthetic_geometry_only_no_gaia_query_no_scientific_halo_estimates",
        "candidate_count": len(fixture),
        "accepted_count": int(fixture["geometry_status"].eq("accepted").sum()),
        "rejected_count": int(fixture["geometry_status"].eq("rejected").sum()),
        "maximum_absolute_galactic_latitude_difference_deg": max(latitude_difference),
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    BACKGROUND_CONTROL_GEOMETRY_VALIDATION.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Background control geometry validation failed: {checks}")


if __name__ == "__main__":
    main()
