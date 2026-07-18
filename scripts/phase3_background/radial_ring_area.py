"""Calculate spherical radial-ring areas from retrieval coverage and circular masks."""

from dataclasses import dataclass
from math import acos, cos, pi, sin

import numpy as np
from scipy.integrate import quad

FULL_CIRCLE_RAD = 2 * pi
STERADIAN_TO_SQUARE_DEG = (180 / pi) ** 2
DEFAULT_INTEGRATION_TOLERANCE_STERADIAN = 1e-13


@dataclass(frozen=True)
class RadialRing:
    """One host-centered ring with angular inner and outer radii."""

    ring_id: str
    inner_radius_deg: float
    outer_radius_deg: float
    inference_role: str

    def __post_init__(self) -> None:
        if not 0 <= self.inner_radius_deg < self.outer_radius_deg < 180:
            raise ValueError("Ring radii must satisfy 0 <= inner < outer < 180 degrees")


@dataclass(frozen=True)
class DeclinationCoverage:
    """One retrieval strip and whether its verified checkpoint is complete."""

    strip_id: str
    minimum_dec_deg: float
    maximum_dec_deg: float
    complete: bool

    def __post_init__(self) -> None:
        if not -90 <= self.minimum_dec_deg < self.maximum_dec_deg <= 90:
            raise ValueError("Coverage declination bounds must lie within the sky")


@dataclass(frozen=True)
class SphericalCircleMask:
    """One explicitly unusable circular sky region with provenance."""

    mask_id: str
    center_ra_deg: float
    center_dec_deg: float
    radius_deg: float
    reason: str
    provenance: str

    def __post_init__(self) -> None:
        if not 0 <= self.center_ra_deg < 360:
            raise ValueError("Mask right ascension must lie in [0, 360) degrees")
        if not -90 <= self.center_dec_deg <= 90:
            raise ValueError("Mask declination must lie in [-90, 90] degrees")
        if not 0 < self.radius_deg < 180:
            raise ValueError("Mask radius must lie in (0, 180) degrees")
        if not self.reason or not self.provenance:
            raise ValueError("Every mask requires a reason and provenance")


def spherical_circle_area_steradian(radius_deg: float) -> float:
    """Return the analytic area of a spherical circle."""
    if not 0 <= radius_deg < 180:
        raise ValueError("Circle radius must lie in [0, 180) degrees")
    return 2 * pi * (1 - cos(np.deg2rad(radius_deg)))


def spherical_ring_area_steradian(ring: RadialRing) -> float:
    """Return the analytic area of a spherical ring."""
    return spherical_circle_area_steradian(ring.outer_radius_deg) - spherical_circle_area_steradian(
        ring.inner_radius_deg
    )


def merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Return the union of longitude intervals in radians."""
    ordered = sorted((start, end) for start, end in intervals if end > start)
    merged: list[tuple[float, float]] = []
    for start, end in ordered:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def intersect_intervals(
    first: list[tuple[float, float]], second: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    """Return the intersection of two longitude-interval unions."""
    first = merge_intervals(first)
    second = merge_intervals(second)
    intersections = []
    first_index = 0
    second_index = 0
    while first_index < len(first) and second_index < len(second):
        start = max(first[first_index][0], second[second_index][0])
        end = min(first[first_index][1], second[second_index][1])
        if end > start:
            intersections.append((start, end))
        if first[first_index][1] <= second[second_index][1]:
            first_index += 1
        else:
            second_index += 1
    return intersections


def subtract_intervals(
    minuend: list[tuple[float, float]], subtrahend: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    """Remove one longitude-interval union from another."""
    remaining = merge_intervals(minuend)
    for remove_start, remove_end in merge_intervals(subtrahend):
        updated = []
        for start, end in remaining:
            if remove_end <= start or remove_start >= end:
                updated.append((start, end))
                continue
            if start < remove_start:
                updated.append((start, remove_start))
            if remove_end < end:
                updated.append((remove_end, end))
        remaining = updated
    return remaining


def interval_length(intervals: list[tuple[float, float]]) -> float:
    """Return the total longitude length of disjoint intervals."""
    return sum(end - start for start, end in merge_intervals(intervals))


def circle_longitude_intervals(
    center_ra_rad: float,
    center_dec_rad: float,
    radius_rad: float,
    declination_rad: float,
) -> list[tuple[float, float]]:
    """Return longitude intervals inside a spherical circle at one declination."""
    denominator = cos(center_dec_rad) * cos(declination_rad)
    numerator = cos(radius_rad) - sin(center_dec_rad) * sin(declination_rad)
    if abs(denominator) < 1e-15:
        return [(0.0, FULL_CIRCLE_RAD)] if numerator <= 0 else []
    cosine_offset = numerator / denominator
    if cosine_offset <= -1:
        return [(0.0, FULL_CIRCLE_RAD)]
    if cosine_offset >= 1:
        return []
    half_width = acos(cosine_offset)
    center = center_ra_rad % FULL_CIRCLE_RAD
    start = center - half_width
    end = center + half_width
    if start < 0:
        return [(0.0, end), (start + FULL_CIRCLE_RAD, FULL_CIRCLE_RAD)]
    if end > FULL_CIRCLE_RAD:
        return [(0.0, end - FULL_CIRCLE_RAD), (start, FULL_CIRCLE_RAD)]
    return [(start, end)]


def ring_longitude_intervals(
    center_ra_rad: float,
    center_dec_rad: float,
    ring: RadialRing,
    declination_rad: float,
) -> list[tuple[float, float]]:
    """Return longitude intervals inside one spherical ring at one declination."""
    outer = circle_longitude_intervals(
        center_ra_rad,
        center_dec_rad,
        np.deg2rad(ring.outer_radius_deg),
        declination_rad,
    )
    if ring.inner_radius_deg == 0:
        return outer
    inner = circle_longitude_intervals(
        center_ra_rad,
        center_dec_rad,
        np.deg2rad(ring.inner_radius_deg),
        declination_rad,
    )
    return subtract_intervals(outer, inner)


def calculate_ring_areas(
    host_ra_deg: float,
    host_dec_deg: float,
    ring: RadialRing,
    coverage: list[DeclinationCoverage],
    masks: list[SphericalCircleMask],
    integration_tolerance_steradian: float = DEFAULT_INTEGRATION_TOLERANCE_STERADIAN,
) -> dict[str, float | str | int]:
    """Calculate requested, queried, masked, missing, and usable spherical areas."""
    if not 0 <= host_ra_deg < 360 or not -90 <= host_dec_deg <= 90:
        raise ValueError("Host coordinates lie outside the celestial sphere")
    if integration_tolerance_steradian <= 0:
        raise ValueError("Integration tolerance must be positive")
    completed_coverage = [item for item in coverage if item.complete]
    host_ra_rad = np.deg2rad(host_ra_deg)
    host_dec_rad = np.deg2rad(host_dec_deg)
    mask_parameters = [
        (
            np.deg2rad(mask.center_ra_deg),
            np.deg2rad(mask.center_dec_deg),
            np.deg2rad(mask.radius_deg),
        )
        for mask in masks
    ]

    def covered(declination_deg: float) -> bool:
        return any(
            item.minimum_dec_deg <= declination_deg <= item.maximum_dec_deg
            for item in completed_coverage
        )

    def longitude_lengths(declination_rad: float) -> tuple[float, float]:
        if not covered(np.rad2deg(declination_rad)):
            return 0.0, 0.0
        ring_intervals = ring_longitude_intervals(host_ra_rad, host_dec_rad, ring, declination_rad)
        queried_length = interval_length(ring_intervals)
        mask_intervals = merge_intervals(
            [
                interval
                for mask_ra_rad, mask_dec_rad, mask_radius_rad in mask_parameters
                for interval in circle_longitude_intervals(
                    mask_ra_rad,
                    mask_dec_rad,
                    mask_radius_rad,
                    declination_rad,
                )
            ]
        )
        masked_length = interval_length(intersect_intervals(ring_intervals, mask_intervals))
        return queried_length, masked_length

    outer_minimum = max(-pi / 2, host_dec_rad - np.deg2rad(ring.outer_radius_deg))
    outer_maximum = min(pi / 2, host_dec_rad + np.deg2rad(ring.outer_radius_deg))
    breakpoints = {outer_minimum, outer_maximum}
    if ring.inner_radius_deg > 0:
        inner_radius_rad = np.deg2rad(ring.inner_radius_deg)
        breakpoints.update(
            {
                max(outer_minimum, host_dec_rad - inner_radius_rad),
                min(outer_maximum, host_dec_rad + inner_radius_rad),
            }
        )
    for item in completed_coverage:
        breakpoints.update(
            {
                max(outer_minimum, np.deg2rad(item.minimum_dec_deg)),
                min(outer_maximum, np.deg2rad(item.maximum_dec_deg)),
            }
        )
    for _, mask_dec_rad, mask_radius_rad in mask_parameters:
        breakpoints.update(
            {
                max(outer_minimum, mask_dec_rad - mask_radius_rad),
                min(outer_maximum, mask_dec_rad + mask_radius_rad),
            }
        )
    ordered_breakpoints = sorted(
        value for value in breakpoints if outer_minimum <= value <= outer_maximum
    )

    def integrate_component(component_index: int) -> tuple[float, float]:
        total = 0.0
        total_error = 0.0
        for lower, upper in zip(ordered_breakpoints[:-1], ordered_breakpoints[1:], strict=True):
            if upper <= lower:
                continue
            value, error = quad(
                lambda declination: (
                    longitude_lengths(declination)[component_index] * cos(declination)
                ),
                lower,
                upper,
                epsabs=integration_tolerance_steradian,
                epsrel=1e-11,
                limit=200,
            )
            total += value
            total_error += error
        return total, total_error

    queried_steradian, queried_error = integrate_component(0)
    masked_steradian, masked_error = integrate_component(1)
    requested_steradian = spherical_ring_area_steradian(ring)
    missing_steradian = max(0.0, requested_steradian - queried_steradian)
    usable_steradian = max(0.0, queried_steradian - masked_steradian)
    area_status = (
        "unavailable"
        if queried_steradian <= integration_tolerance_steradian
        else "complete"
        if missing_steradian <= 10 * integration_tolerance_steradian
        else "partial"
    )
    return {
        "requested_area_steradian": requested_steradian,
        "successfully_queried_area_steradian": queried_steradian,
        "masked_area_steradian": masked_steradian,
        "missing_area_steradian": missing_steradian,
        "usable_area_steradian": usable_steradian,
        "requested_area_square_deg": requested_steradian * STERADIAN_TO_SQUARE_DEG,
        "successfully_queried_area_square_deg": queried_steradian * STERADIAN_TO_SQUARE_DEG,
        "masked_area_square_deg": masked_steradian * STERADIAN_TO_SQUARE_DEG,
        "missing_area_square_deg": missing_steradian * STERADIAN_TO_SQUARE_DEG,
        "usable_area_square_deg": usable_steradian * STERADIAN_TO_SQUARE_DEG,
        "queried_integration_error_square_deg": queried_error * STERADIAN_TO_SQUARE_DEG,
        "masked_integration_error_square_deg": masked_error * STERADIAN_TO_SQUARE_DEG,
        "area_status": area_status,
        "expected_strip_count": len(coverage),
        "completed_strip_count": len(completed_coverage),
        "mask_count": len(masks),
    }


def calculate_gaia_ring_areas(
    host_ra_deg: float,
    host_dec_deg: float,
    ring: RadialRing,
    coverage: list[DeclinationCoverage],
    integration_tolerance_steradian: float = DEFAULT_INTEGRATION_TOLERANCE_STERADIAN,
) -> dict[str, float | str | int]:
    """Calculate Gaia areas without bright-star, dust, or ancillary-imaging masks."""
    areas = calculate_ring_areas(
        host_ra_deg,
        host_dec_deg,
        ring,
        coverage,
        masks=[],
        integration_tolerance_steradian=integration_tolerance_steradian,
    )
    if areas["masked_area_steradian"] != 0 or (
        abs(areas["usable_area_steradian"] - areas["successfully_queried_area_steradian"])
        > integration_tolerance_steradian
    ):
        raise RuntimeError("Gaia area policy requires usable area to equal queried area")
    return areas
