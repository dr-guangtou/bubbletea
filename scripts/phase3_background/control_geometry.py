"""Generate and evaluate spherical off-target background control apertures."""

from dataclasses import dataclass

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord


@dataclass(frozen=True)
class HostControlGeometry:
    """Geometry inputs for one host without scientific source counts."""

    host_id: str
    ra_deg: float
    dec_deg: float
    distance_mpc: float
    signal_radius_kpc: float
    r200c_upper_kpc: float
    halo_safety_factor: float
    environment_state: str

    @property
    def signal_radius_deg(self) -> float:
        """Return the signal-aperture angular radius."""
        return physical_radius_to_angle_deg(self.distance_mpc, self.signal_radius_kpc)

    @property
    def halo_exclusion_radius_deg(self) -> float:
        """Return the buffered upper halo radius on the sky."""
        radius_kpc = self.r200c_upper_kpc * self.halo_safety_factor
        return physical_radius_to_angle_deg(self.distance_mpc, radius_kpc)


@dataclass(frozen=True)
class NeighborExclusion:
    """One neighboring halo represented by a conservative sky circle."""

    neighbor_id: str
    ra_deg: float
    dec_deg: float
    exclusion_radius_deg: float


def physical_radius_to_angle_deg(distance_mpc: float, radius_kpc: float) -> float:
    """Convert a projected physical radius to an exact angular radius."""
    if distance_mpc <= 0 or radius_kpc < 0:
        raise ValueError("Distance must be positive and radius must be non-negative")
    return float(np.rad2deg(np.arctan2(radius_kpc, distance_mpc * 1000)))


def constant_galactic_latitude_offset(
    host_coordinate: SkyCoord, separation_deg: float, direction: int
) -> SkyCoord:
    """Offset east or west while preserving the host's Galactic latitude."""
    if direction not in {-1, 1}:
        raise ValueError("Direction must be -1 or 1")
    galactic = host_coordinate.galactic
    latitude = galactic.b.to_value(u.rad)
    separation = np.deg2rad(separation_deg)
    denominator = np.cos(latitude) ** 2
    if denominator <= 0:
        raise ValueError("A constant-latitude offset is undefined at a Galactic pole")
    cosine_longitude_offset = (np.cos(separation) - np.sin(latitude) ** 2) / denominator
    if not -1 <= cosine_longitude_offset <= 1:
        raise ValueError("Requested separation is unavailable at this Galactic latitude")
    longitude_offset = direction * np.arccos(cosine_longitude_offset) * u.rad
    return SkyCoord(l=galactic.l + longitude_offset, b=galactic.b, frame="galactic").icrs


def generate_symmetric_candidates(
    host: HostControlGeometry, separation_multipliers: tuple[float, ...]
) -> list[dict[str, object]]:
    """Generate count-blind east/west candidates at declared fixture separations."""
    host_coordinate = SkyCoord(host.ra_deg * u.deg, host.dec_deg * u.deg, frame="icrs")
    minimum_center_separation = host.halo_exclusion_radius_deg + host.signal_radius_deg
    candidates = []
    for multiplier in separation_multipliers:
        if multiplier <= 1:
            raise ValueError("Fixture separation multipliers must exceed one")
        separation_deg = multiplier * minimum_center_separation
        for direction, direction_name in [(-1, "west"), (1, "east")]:
            coordinate = constant_galactic_latitude_offset(
                host_coordinate, separation_deg, direction
            )
            candidates.append(
                {
                    "host_id": host.host_id,
                    "candidate_id": f"{host.host_id}:{multiplier:g}:{direction_name}",
                    "ra_deg": coordinate.ra.deg,
                    "dec_deg": coordinate.dec.deg,
                    "galactic_latitude_deg": coordinate.galactic.b.deg,
                    "center_separation_deg": separation_deg,
                    "signal_radius_deg": host.signal_radius_deg,
                    "halo_exclusion_radius_deg": host.halo_exclusion_radius_deg,
                    "separation_multiplier": multiplier,
                    "direction": direction_name,
                }
            )
    return candidates


def evaluate_candidates(
    host: HostControlGeometry,
    candidates: list[dict[str, object]],
    neighbors: list[NeighborExclusion],
) -> list[dict[str, object]]:
    """Assign deterministic geometry dispositions without using source counts."""
    unresolved_environment = host.environment_state != "isolated_central"
    evaluated = []
    for candidate in candidates:
        reasons = []
        if unresolved_environment:
            reasons.append("unresolved_environment")
        minimum_separation = host.halo_exclusion_radius_deg + host.signal_radius_deg
        if float(candidate["center_separation_deg"]) < minimum_separation:
            reasons.append("intersects_host_halo_exclusion")
        candidate_coordinate = SkyCoord(
            float(candidate["ra_deg"]) * u.deg,
            float(candidate["dec_deg"]) * u.deg,
            frame="icrs",
        )
        intersecting_neighbors = []
        for neighbor in neighbors:
            neighbor_coordinate = SkyCoord(
                neighbor.ra_deg * u.deg, neighbor.dec_deg * u.deg, frame="icrs"
            )
            separation = candidate_coordinate.separation(neighbor_coordinate).deg
            if separation < host.signal_radius_deg + neighbor.exclusion_radius_deg:
                intersecting_neighbors.append(neighbor.neighbor_id)
        if intersecting_neighbors:
            reasons.append("intersects_neighbor_halo_exclusion")
        evaluated.append(
            {
                **candidate,
                "environment_state": host.environment_state,
                "geometry_status": "accepted" if not reasons else "rejected",
                "rejection_reasons": ";".join(reasons),
                "intersecting_neighbor_ids": ";".join(intersecting_neighbors),
            }
        )
    return evaluated
