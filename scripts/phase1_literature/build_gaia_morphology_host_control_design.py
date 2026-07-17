"""Build a frozen luminosity/latitude host and geometric control-field design."""

import argparse
import json
import sys
from datetime import UTC, datetime
from math import atan, degrees
from pathlib import Path

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import BarycentricMeanEcliptic, SkyCoord
from astropy.time import Time

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN,
    GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_MANIFEST,
    GALAXY_SAMPLE_CSV,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import serialize_path

DESIGN_VERSION = "gaia_morphology_host_control_design_v1"
MAXIMUM_RADIUS_KPC = 600.0
MINIMUM_DISTANCE_MPC = 15.0
MAXIMUM_DISTANCE_MPC = 25.0
MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG = 30.0
LATITUDE_BOUNDARY_DEG = 50.0
MAXIMUM_FIELD_RADIUS_DEG = 2.1
HOSTS_PER_STRATUM = 2
CONTROL_LONGITUDE_OFFSET_MINIMUM_DEG = 15
CONTROL_LONGITUDE_OFFSET_MAXIMUM_DEG = 180
CONTROL_ECLIPTIC_LATITUDE_OFFSETS_DEG = [-2.0, -1.0, 0.0, 1.0, 2.0]
NEARBY_GALAXY_SCREEN_RADIUS_KPC = 300.0
NEARBY_GALAXY_SCREEN_CAP_DEG = 2.1
ECLIPTIC_FRAME = BarycentricMeanEcliptic(equinox=Time("J2000"))


def parse_arguments() -> argparse.Namespace:
    """Parse host catalog and design artifact paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-catalog", type=Path, default=GALAXY_SAMPLE_CSV)
    parser.add_argument("--output", type=Path, default=GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=GAIA_MORPHOLOGY_HOST_CONTROL_DESIGN_MANIFEST,
    )
    return parser.parse_args()


def angular_radius_deg(distance_mpc: float, radius_kpc: float) -> float:
    """Convert projected physical radius to angular radius."""
    return degrees(atan(radius_kpc / (distance_mpc * 1000.0)))


def eligible_hosts(host_catalog: pd.DataFrame) -> tuple[pd.DataFrame, list[float]]:
    """Build the outcome-independent eligible host population and strata."""
    hosts = host_catalog.dropna(subset=["ra", "dec", "dist_best", "glat", "log_L_K"]).copy()
    hosts["field_radius_deg"] = hosts["dist_best"].map(
        lambda value: angular_radius_deg(float(value), MAXIMUM_RADIUS_KPC)
    )
    hosts = hosts.loc[
        hosts["glat"].abs().ge(MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG)
        & hosts["dist_best"].between(MINIMUM_DISTANCE_MPC, MAXIMUM_DISTANCE_MPC)
        & hosts["field_radius_deg"].le(MAXIMUM_FIELD_RADIUS_DEG)
    ].copy()
    lower_boundary, upper_boundary = hosts["log_L_K"].quantile([1.0 / 3.0, 2.0 / 3.0])
    hosts["luminosity_stratum"] = "middle"
    hosts.loc[hosts["log_L_K"].le(lower_boundary), "luminosity_stratum"] = "low"
    hosts.loc[hosts["log_L_K"].gt(upper_boundary), "luminosity_stratum"] = "high"
    hosts["latitude_stratum"] = "50_to_90_deg"
    hosts.loc[
        hosts["glat"].abs().lt(LATITUDE_BOUNDARY_DEG),
        "latitude_stratum",
    ] = "30_to_50_deg"
    return hosts, [float(lower_boundary), float(upper_boundary)]


def select_stratified_hosts(eligible: pd.DataFrame) -> pd.DataFrame:
    """Select two interior luminosity quantiles from each of six strata."""
    selected_rows = []
    for _, group in eligible.groupby(
        ["luminosity_stratum", "latitude_stratum"],
        sort=True,
    ):
        ordered = group.sort_values(["log_L_K", "dist_best", "rank"]).reset_index(drop=True)
        indices = [round((len(ordered) - 1) / 3.0), round(2.0 * (len(ordered) - 1) / 3.0)]
        selected_rows.extend(ordered.iloc[indices].to_dict("records"))
    selected = pd.DataFrame(selected_rows).sort_values("rank").reset_index(drop=True)
    if len(selected) != 6 * HOSTS_PER_STRATUM:
        raise RuntimeError("The stratified design did not produce exactly 12 hosts")
    coordinates = SkyCoord(selected["ra"].to_numpy() * u.deg, selected["dec"].to_numpy() * u.deg)
    separation = coordinates[:, None].separation(coordinates[None, :]).deg
    np.fill_diagonal(separation, np.inf)
    radius_sum = (
        selected["field_radius_deg"].to_numpy()[:, None]
        + selected["field_radius_deg"].to_numpy()[None, :]
    )
    if np.any(separation <= radius_sum):
        raise RuntimeError("Selected host fields overlap")
    return selected


def control_candidates(
    host: dict[str, object],
    all_galaxy_coordinates: SkyCoord,
    all_galaxy_screen_radius_deg: np.ndarray,
    existing_controls: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Generate screened control candidates near the host's two sky latitudes."""
    host_coordinate = SkyCoord(float(host["ra"]) * u.deg, float(host["dec"]) * u.deg)
    host_ecliptic = host_coordinate.transform_to(ECLIPTIC_FRAME)
    candidates = []
    for ecliptic_latitude_offset_deg in CONTROL_ECLIPTIC_LATITUDE_OFFSETS_DEG:
        candidate_ecliptic_latitude = host_ecliptic.lat.deg + ecliptic_latitude_offset_deg
        for direction in (-1, 1):
            for offset_deg in range(
                CONTROL_LONGITUDE_OFFSET_MINIMUM_DEG,
                CONTROL_LONGITUDE_OFFSET_MAXIMUM_DEG + 1,
            ):
                signed_offset_deg = direction * offset_deg
                coordinate = SkyCoord(
                    lon=(host_ecliptic.lon.deg + signed_offset_deg) * u.deg,
                    lat=candidate_ecliptic_latitude * u.deg,
                    frame=ECLIPTIC_FRAME,
                ).icrs
                galactic = coordinate.galactic
                if abs(galactic.b.deg) < MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG:
                    continue
                galaxy_separation = coordinate.separation(all_galaxy_coordinates).deg
                clearance = galaxy_separation - (
                    float(host["field_radius_deg"]) + all_galaxy_screen_radius_deg
                )
                minimum_clearance_deg = float(clearance.min())
                if minimum_clearance_deg <= 0.0:
                    continue
                if existing_controls:
                    control_coordinates = SkyCoord(
                        [item["field_ra"] for item in existing_controls] * u.deg,
                        [item["field_dec"] for item in existing_controls] * u.deg,
                    )
                    control_radii = np.array(
                        [item["field_radius_deg"] for item in existing_controls]
                    )
                    if np.any(
                        coordinate.separation(control_coordinates).deg
                        <= float(host["field_radius_deg"]) + control_radii
                    ):
                        continue
                galactic_latitude_difference_deg = abs(
                    abs(galactic.b.deg) - abs(float(host["glat"]))
                )
                ecliptic_latitude_difference_deg = abs(ecliptic_latitude_offset_deg)
                candidates.append(
                    {
                        "coordinate": coordinate,
                        "galactic": galactic,
                        "signed_ecliptic_longitude_offset_deg": signed_offset_deg,
                        "ecliptic_latitude_deg": candidate_ecliptic_latitude,
                        "galactic_latitude_difference_deg": galactic_latitude_difference_deg,
                        "ecliptic_latitude_difference_deg": ecliptic_latitude_difference_deg,
                        "geometric_match_score_deg": (
                            galactic_latitude_difference_deg + ecliptic_latitude_difference_deg
                        ),
                        "minimum_nearby_galaxy_clearance_deg": minimum_clearance_deg,
                    }
                )
    return sorted(
        candidates,
        key=lambda item: (
            item["geometric_match_score_deg"],
            abs(item["signed_ecliptic_longitude_offset_deg"]),
            item["signed_ecliptic_longitude_offset_deg"],
        ),
    )


def build_design(host_catalog: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Build paired host and control rows with no Gaia outcome information."""
    eligible, luminosity_boundaries = eligible_hosts(host_catalog)
    selected_hosts = select_stratified_hosts(eligible)
    positioned_galaxies = host_catalog.dropna(subset=["ra", "dec", "dist_best"]).copy()
    all_galaxy_coordinates = SkyCoord(
        positioned_galaxies["ra"].to_numpy() * u.deg,
        positioned_galaxies["dec"].to_numpy() * u.deg,
    )
    all_galaxy_screen_radius_deg = np.minimum(
        positioned_galaxies["dist_best"].map(
            lambda value: angular_radius_deg(float(value), NEARBY_GALAXY_SCREEN_RADIUS_KPC)
        ),
        NEARBY_GALAXY_SCREEN_CAP_DEG,
    ).to_numpy()

    rows = []
    controls = []
    for pair_number, host in enumerate(selected_hosts.to_dict("records"), start=1):
        host_coordinate = SkyCoord(float(host["ra"]) * u.deg, float(host["dec"]) * u.deg)
        host_ecliptic = host_coordinate.transform_to(ECLIPTIC_FRAME)
        pair_id = f"host_control_pair_{pair_number:02d}"
        common = {
            "pair_id": pair_id,
            "host_rank": int(host["rank"]),
            "host_name": str(host["objname"]),
            "host_distance_mpc": float(host["dist_best"]),
            "host_log_l_k": float(host["log_L_K"]),
            "luminosity_stratum": str(host["luminosity_stratum"]),
            "latitude_stratum": str(host["latitude_stratum"]),
            "field_radius_deg": float(host["field_radius_deg"]),
            "equivalent_maximum_radius_kpc": MAXIMUM_RADIUS_KPC,
        }
        rows.append(
            {
                **common,
                "field_id": f"{pair_id}_host",
                "field_role": "host",
                "field_ra": float(host["ra"]),
                "field_dec": float(host["dec"]),
                "field_galactic_longitude_deg": float(host_coordinate.galactic.l.deg),
                "field_galactic_latitude_deg": float(host_coordinate.galactic.b.deg),
                "field_ecliptic_longitude_deg": float(host_ecliptic.lon.deg),
                "field_ecliptic_latitude_deg": float(host_ecliptic.lat.deg),
                "signed_ecliptic_longitude_offset_deg": 0.0,
                "galactic_latitude_difference_deg": 0.0,
                "ecliptic_latitude_difference_deg": 0.0,
                "geometric_match_score_deg": 0.0,
                "minimum_nearby_galaxy_clearance_deg": 0.0,
            }
        )
        candidates = control_candidates(
            host,
            all_galaxy_coordinates,
            all_galaxy_screen_radius_deg,
            controls,
        )
        if not candidates:
            raise RuntimeError(f"No screened control candidate for {host['objname']}")
        selected_control = candidates[0]
        coordinate = selected_control.pop("coordinate")
        galactic = selected_control.pop("galactic")
        control_ecliptic_latitude_deg = selected_control.pop("ecliptic_latitude_deg")
        control_row = {
            **common,
            "field_id": f"{pair_id}_control",
            "field_role": "control",
            "field_ra": float(coordinate.ra.deg),
            "field_dec": float(coordinate.dec.deg),
            "field_galactic_longitude_deg": float(galactic.l.deg),
            "field_galactic_latitude_deg": float(galactic.b.deg),
            "field_ecliptic_longitude_deg": float(
                host_ecliptic.lon.deg + selected_control["signed_ecliptic_longitude_offset_deg"]
            )
            % 360.0,
            "field_ecliptic_latitude_deg": control_ecliptic_latitude_deg,
            **selected_control,
        }
        rows.append(control_row)
        controls.append(control_row)
    design = pd.DataFrame(rows).sort_values(["pair_id", "field_role"], ascending=[True, False])
    metadata = {
        "eligible_host_count": len(eligible),
        "luminosity_tercile_boundaries_log_l_k": luminosity_boundaries,
        "selected_host_count": len(selected_hosts),
        "control_count": len(controls),
    }
    return design.reset_index(drop=True), metadata


def main() -> None:
    """Write the frozen geometric field design and provenance manifest."""
    arguments = parse_arguments()
    host_catalog = pd.read_csv(arguments.host_catalog)
    design, metadata = build_design(host_catalog)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    design.to_csv(arguments.output, index=False)
    manifest = {
        "design_version": DESIGN_VERSION,
        "generated_utc": datetime.now(UTC).isoformat(),
        "design_status": "frozen_before_gaia_outcome_queries",
        "environment_stratification_status": (
            "deferred_existing_is_cluster_is_an_undocumented_sky_circle_proxy"
        ),
        "host_catalog": serialize_path(arguments.host_catalog),
        "host_catalog_sha256": calculate_sha256(arguments.host_catalog),
        "selection_rules": {
            "distance_interval_mpc": [MINIMUM_DISTANCE_MPC, MAXIMUM_DISTANCE_MPC],
            "minimum_absolute_galactic_latitude_deg": (MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG),
            "latitude_boundary_deg": LATITUDE_BOUNDARY_DEG,
            "maximum_radius_kpc": MAXIMUM_RADIUS_KPC,
            "maximum_field_radius_deg": MAXIMUM_FIELD_RADIUS_DEG,
            "hosts_per_luminosity_latitude_stratum": HOSTS_PER_STRATUM,
            "host_selection_within_stratum": (
                "rows_nearest_one_third_and_two_thirds_positions_after_sorting_by_"
                "log_l_k_distance_and_rank"
            ),
            "control_ecliptic_latitude_offsets_deg": (CONTROL_ECLIPTIC_LATITUDE_OFFSETS_DEG),
            "control_ecliptic_longitude_offset_interval_deg": [
                CONTROL_LONGITUDE_OFFSET_MINIMUM_DEG,
                CONTROL_LONGITUDE_OFFSET_MAXIMUM_DEG,
            ],
            "nearby_galaxy_screen_radius_kpc": NEARBY_GALAXY_SCREEN_RADIUS_KPC,
            "nearby_galaxy_screen_cap_deg": NEARBY_GALAXY_SCREEN_CAP_DEG,
            "control_rank_rule": (
                "minimize_absolute_galactic_latitude_difference_plus_absolute_"
                "ecliptic_latitude_difference_then_longitude_offset"
            ),
        },
        "counts": metadata,
        "output": serialize_path(arguments.output),
        "output_sha256": calculate_sha256(arguments.output),
    }
    arguments.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
