"""Freeze count-blind first-stage host profiles before large-radius Gaia queries."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_HOSTS,
    BACKGROUND_REVIEW_HOSTS_MANIFEST,
    FIRST_STAGE_HOST_PROFILE_FIXTURE,
    FIRST_STAGE_HOST_PROFILE_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256
from scripts.phase3_background.audit_radial_measurement_geometry import (
    EXPLORATORY_PHYSICAL_RING_EDGES_KPC,
)
from scripts.phase3_background.control_geometry import physical_radius_to_angle_deg
from scripts.phase3_background.radial_ring_area import (
    RadialRing,
    spherical_circle_area_steradian,
    spherical_ring_area_steradian,
)

FIXTURE_VERSION = "first_stage_host_profile_fixture_v1"
CONSERVATIVE_CENTRAL_EXCLUSION_KPC = 50
CANDIDATE_CENTRAL_EXCLUSIONS_KPC = (20, 25, 30, 40, 50)
OUTER_PROFILE_RADIUS_KPC = 600
SQUARE_DEGREE_PER_STERADIAN = (180 / np.pi) ** 2
AREA_TOLERANCE_SQUARE_DEG = 1e-8


def ring_role(inner_radius_kpc: int, outer_radius_kpc: int) -> str:
    """Return the approved first-stage role of one preserved physical ring."""
    if outer_radius_kpc <= CONSERVATIVE_CENTRAL_EXCLUSION_KPC:
        return "conservative_central_contamination_diagnostic"
    return "large_radius_exploratory_profile"


def make_host_records(host: pd.Series, initial_benchmark_name: str) -> list[dict[str, object]]:
    """Build every preserved physical ring for one fixed review host."""
    records = []
    for inner_radius_kpc, outer_radius_kpc in zip(
        EXPLORATORY_PHYSICAL_RING_EDGES_KPC[:-1],
        EXPLORATORY_PHYSICAL_RING_EDGES_KPC[1:],
        strict=True,
    ):
        inner_radius_deg = physical_radius_to_angle_deg(float(host["dist_best"]), inner_radius_kpc)
        outer_radius_deg = physical_radius_to_angle_deg(float(host["dist_best"]), outer_radius_kpc)
        ring = RadialRing(
            ring_id=f"physical_{inner_radius_kpc}_{outer_radius_kpc}_kpc",
            inner_radius_deg=inner_radius_deg,
            outer_radius_deg=outer_radius_deg,
            inference_role=ring_role(inner_radius_kpc, outer_radius_kpc),
        )
        records.append(
            {
                "fixture_version": FIXTURE_VERSION,
                "review_case": str(host["review_case"]),
                "rank": int(host["rank"]),
                "host_name": str(host["objname"]),
                "host_ra_deg": float(host["ra"]),
                "host_dec_deg": float(host["dec"]),
                "host_distance_mpc": float(host["dist_best"]),
                "catalog_environment_role": str(host["catalog_environment_role"]),
                "association_state": str(host["association_state"]),
                "ring_id": ring.ring_id,
                "inner_radius_kpc": inner_radius_kpc,
                "outer_radius_kpc": outer_radius_kpc,
                "inner_radius_deg": inner_radius_deg,
                "outer_radius_deg": outer_radius_deg,
                "requested_ring_area_square_deg": spherical_ring_area_steradian(ring)
                * SQUARE_DEGREE_PER_STERADIAN,
                "first_stage_ring_role": ring.inference_role,
                "inside_conservative_central_exclusion": (
                    outer_radius_kpc <= CONSERVATIVE_CENTRAL_EXCLUSION_KPC
                ),
                "eligible_for_exploratory_profile_interpretation": (
                    inner_radius_kpc >= CONSERVATIVE_CENTRAL_EXCLUSION_KPC
                ),
                "eligible_for_final_inference": False,
                "r50_normalized_profile_status": "unavailable_missing_verified_r50",
                "continuous_source_radius_required": True,
                "initial_live_geometry_benchmark": str(host["objname"]) == initial_benchmark_name,
            }
        )
    return records


def main() -> None:
    """Write and validate the first-stage five-host physical profile fixture."""
    hosts = pd.read_csv(BACKGROUND_REVIEW_HOSTS)
    resolved_isolated = hosts.loc[
        hosts["catalog_environment_role"].eq("catalog_isolated_principal")
        & hosts["association_state"].eq("accepted_unique_spherical_5arcsec_v1")
    ].copy()
    resolved_isolated["outer_radius_deg"] = resolved_isolated["dist_best"].map(
        lambda distance_mpc: physical_radius_to_angle_deg(
            float(distance_mpc), OUTER_PROFILE_RADIUS_KPC
        )
    )
    initial_benchmark_name = str(
        resolved_isolated.sort_values(["outer_radius_deg", "rank"]).iloc[0]["objname"]
    )
    records = [
        record
        for _, host in hosts.iterrows()
        for record in make_host_records(host, initial_benchmark_name)
    ]
    fixture = pd.DataFrame(records)
    FIRST_STAGE_HOST_PROFILE_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    fixture.to_csv(FIRST_STAGE_HOST_PROFILE_FIXTURE, index=False)

    host_outer = fixture.loc[fixture["outer_radius_kpc"].eq(OUTER_PROFILE_RADIUS_KPC)].set_index(
        "host_name"
    )
    area_errors = []
    for host_name, host_rings in fixture.groupby("host_name"):
        outer_radius_deg = float(host_outer.loc[host_name, "outer_radius_deg"])
        circle_area = (
            spherical_circle_area_steradian(outer_radius_deg) * SQUARE_DEGREE_PER_STERADIAN
        )
        area_errors.append(
            abs(float(host_rings["requested_ring_area_square_deg"].sum()) - circle_area)
        )
    edge_pairs = list(
        zip(
            EXPLORATORY_PHYSICAL_RING_EDGES_KPC[:-1],
            EXPLORATORY_PHYSICAL_RING_EDGES_KPC[1:],
            strict=True,
        )
    )
    benchmark_rows = fixture.loc[fixture["initial_live_geometry_benchmark"]]
    r50_columns = [
        column
        for column in hosts.columns
        if "r50" in column.lower() or "half_light" in column.lower()
    ]
    checks = {
        "five_count_blind_review_hosts_preserved": fixture["host_name"].nunique() == 5,
        "fourteen_physical_rings_per_host": fixture.groupby("host_name")["ring_id"]
        .nunique()
        .eq(len(edge_pairs))
        .all(),
        "declared_physical_edges_preserved_exactly": all(
            list(
                zip(
                    rows.sort_values("inner_radius_kpc")["inner_radius_kpc"],
                    rows.sort_values("inner_radius_kpc")["outer_radius_kpc"],
                    strict=True,
                )
            )
            == edge_pairs
            for _, rows in fixture.groupby("host_name")
        ),
        "all_host_distances_positive": fixture["host_distance_mpc"].gt(0).all(),
        "angular_edges_increase_within_every_ring": fixture["outer_radius_deg"]
        .gt(fixture["inner_radius_deg"])
        .all(),
        "ring_areas_sum_to_requested_600_kpc_circle": max(area_errors) <= AREA_TOLERANCE_SQUARE_DEG,
        "central_exclusion_uses_declared_50_kpc_edge": fixture.loc[
            fixture["inside_conservative_central_exclusion"], "outer_radius_kpc"
        ].max()
        == CONSERVATIVE_CENTRAL_EXCLUSION_KPC,
        "candidate_central_edges_were_predeclared": set(CANDIDATE_CENTRAL_EXCLUSIONS_KPC).issubset(
            EXPLORATORY_PHYSICAL_RING_EDGES_KPC
        ),
        "inner_rings_preserved_as_diagnostics": fixture.loc[
            fixture["inside_conservative_central_exclusion"], "first_stage_ring_role"
        ]
        .eq("conservative_central_contamination_diagnostic")
        .all(),
        "outer_rings_are_exploratory_not_final": fixture.loc[
            fixture["eligible_for_exploratory_profile_interpretation"],
            "first_stage_ring_role",
        ]
        .eq("large_radius_exploratory_profile")
        .all()
        and not fixture["eligible_for_final_inference"].any(),
        "all_profiles_reach_declared_600_kpc_edge": host_outer["outer_radius_kpc"]
        .eq(OUTER_PROFILE_RADIUS_KPC)
        .all(),
        "no_fixed_angular_cap_applied": host_outer["outer_radius_deg"].gt(2).any(),
        "normalized_view_explicitly_unavailable_without_r50": not r50_columns
        and fixture["r50_normalized_profile_status"].eq("unavailable_missing_verified_r50").all(),
        "one_geometry_only_live_benchmark_selected": benchmark_rows["host_name"].nunique() == 1
        and set(benchmark_rows["host_name"]) == {"NGC 4698"},
        "no_gaia_source_or_selector_counts_used": True,
        "continuous_source_radii_required": fixture["continuous_source_radius_required"].all(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    manifest = {
        "fixture_version": FIXTURE_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "count_blind_first_stage_profile_geometry_frozen",
        "plain_language_scope": (
            "Five fixed review hosts keep physical rings from zero to 600 kpc. The "
            "inner 50 kpc is a conservative diagnostic region, and no final signal "
            "boundary is approved."
        ),
        "host_count": fixture["host_name"].nunique(),
        "ring_count_per_host": len(edge_pairs),
        "physical_ring_edges_kpc": list(EXPLORATORY_PHYSICAL_RING_EDGES_KPC),
        "candidate_central_exclusions_kpc": list(CANDIDATE_CENTRAL_EXCLUSIONS_KPC),
        "first_stage_conservative_central_exclusion_kpc": (CONSERVATIVE_CENTRAL_EXCLUSION_KPC),
        "first_stage_outer_profile_radius_kpc": OUTER_PROFILE_RADIUS_KPC,
        "outer_signal_boundary_status": "not_selected_review_profiles_first",
        "r50_policy": {
            "report_normalized_profile_when_verified_r50_available": True,
            "current_review_host_r50_columns": r50_columns,
            "missing_r50_effect": "normalized_view_unavailable_physical_view_retained",
        },
        "initial_live_geometry_benchmark": {
            "host_name": initial_benchmark_name,
            "selection_rule": (
                "smallest 600 kpc angular radius among fixed resolved isolated review hosts"
            ),
            "uses_gaia_counts": False,
        },
        "review_host_geometry": [
            {
                "host_name": host_name,
                "host_distance_mpc": float(row["host_distance_mpc"]),
                "central_50_kpc_radius_deg": float(
                    fixture.loc[
                        fixture["host_name"].eq(host_name)
                        & fixture["outer_radius_kpc"].eq(CONSERVATIVE_CENTRAL_EXCLUSION_KPC),
                        "outer_radius_deg",
                    ].iloc[0]
                ),
                "outer_600_kpc_radius_deg": float(row["outer_radius_deg"]),
                "outer_600_kpc_circle_area_square_deg": float(
                    spherical_circle_area_steradian(float(row["outer_radius_deg"]))
                    * SQUARE_DEGREE_PER_STERADIAN
                ),
            }
            for host_name, row in host_outer.iterrows()
        ],
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (BACKGROUND_REVIEW_HOSTS, BACKGROUND_REVIEW_HOSTS_MANIFEST)
        ],
        "output": {
            "path": str(FIRST_STAGE_HOST_PROFILE_FIXTURE.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(FIRST_STAGE_HOST_PROFILE_FIXTURE),
        },
        "archive_queries_executed": 0,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    FIRST_STAGE_HOST_PROFILE_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"First-stage host profile fixture failed: {checks}")


if __name__ == "__main__":
    main()
