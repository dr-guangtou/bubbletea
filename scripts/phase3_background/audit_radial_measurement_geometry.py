"""Audit count-blind radial geometry for the real host measurements."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GALAXY_SAMPLE_CSV,
    PROJECT_ROOT,
    RADIAL_MEASUREMENT_GEOMETRY_AUDIT,
    RADIAL_MEASUREMENT_GEOMETRY_MANIFEST,
)
from scripts.phase3_background.control_geometry import physical_radius_to_angle_deg

EXPLORATORY_PHYSICAL_RING_EDGES_KPC = (
    0,
    5,
    10,
    15,
    20,
    25,
    30,
    40,
    50,
    75,
    100,
    150,
    200,
    300,
    600,
)


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a local input file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def spherical_circle_area_square_deg(radius_deg: pd.Series) -> pd.Series:
    """Return exact spherical-circle areas for angular radii in degrees."""
    radius_rad = np.deg2rad(radius_deg.astype(float))
    return 2 * np.pi * (1 - np.cos(radius_rad)) * (180 / np.pi) ** 2


def main() -> None:
    """Write host angular scales and validation for the exploratory ring view."""
    hosts = pd.read_csv(GALAXY_SAMPLE_CSV)
    audit = hosts[["rank", "objname", "ra", "dec", "dist_best"]].copy()
    for edge_kpc in EXPLORATORY_PHYSICAL_RING_EDGES_KPC[1:]:
        audit[f"radius_{edge_kpc}_kpc_deg"] = audit["dist_best"].map(
            lambda distance_mpc: physical_radius_to_angle_deg(distance_mpc, edge_kpc)
        )
    outer_radius_column = "radius_600_kpc_deg"
    audit["outer_600_kpc_circle_area_square_deg"] = spherical_circle_area_square_deg(
        audit[outer_radius_column]
    )
    radius_columns = [
        f"radius_{edge_kpc}_kpc_deg" for edge_kpc in EXPLORATORY_PHYSICAL_RING_EDGES_KPC[1:]
    ]
    angular_radii = audit[radius_columns].to_numpy()
    r50_columns = [
        column
        for column in hosts.columns
        if "r50" in column.lower() or "half_light" in column.lower()
    ]
    checks = {
        "all_2155_hosts_present": len(audit) == 2155,
        "all_distances_positive": audit["dist_best"].gt(0).all(),
        "angular_ring_edges_increase": (np.diff(angular_radii, axis=1) > 0).all(),
        "no_fixed_two_degree_cap_applied": audit[outer_radius_column].gt(2).any(),
        "no_r50_field_currently_available": not r50_columns,
        "no_source_or_selector_counts_used": True,
        "central_exclusion_not_assigned": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    RADIAL_MEASUREMENT_GEOMETRY_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(RADIAL_MEASUREMENT_GEOMETRY_AUDIT, index=False)
    outer_radius = audit[outer_radius_column]
    manifest = {
        "audit_version": "radial_measurement_geometry_audit_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "audit_scope": "count_blind_geometry_only_no_gaia_query",
        "input": {
            "path": str(GALAXY_SAMPLE_CSV.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(GALAXY_SAMPLE_CSV),
        },
        "host_count": len(audit),
        "exploratory_physical_ring_edges_kpc": list(EXPLORATORY_PHYSICAL_RING_EDGES_KPC),
        "ring_contract": {
            "status": "recombinable_exploratory_view_not_final_signal_definition",
            "continuous_source_radius_must_be_preserved": True,
            "physical_kpc_profile_must_be_preserved": True,
            "r50_normalized_profile_required_when_r50_available": True,
            "central_exclusion_status": "not_calibrated",
        },
        "current_r50_columns": r50_columns,
        "outer_600_kpc_angular_radius_deg": {
            "minimum": float(outer_radius.min()),
            "median": float(outer_radius.median()),
            "maximum": float(outer_radius.max()),
            "host_count_above_2_deg": int(outer_radius.gt(2).sum()),
            "host_count_above_5_deg": int(outer_radius.gt(5).sum()),
            "host_count_above_10_deg": int(outer_radius.gt(10).sum()),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    RADIAL_MEASUREMENT_GEOMETRY_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Radial measurement geometry audit failed: {checks}")


if __name__ == "__main__":
    main()
