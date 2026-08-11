"""Divide a circular Gaia query into complete, non-overlapping sky strips."""

from dataclasses import dataclass
from math import ceil

import numpy as np


@dataclass(frozen=True)
class DeclinationStrip:
    """One horizontal sky strip within a circular query."""

    strip_index: int
    minimum_dec_deg: float
    maximum_dec_deg: float
    includes_maximum_dec: bool

    def dec_predicate(self) -> str:
        """Return a half-open boundary predicate, closing only the final strip."""
        upper_operator = "<=" if self.includes_maximum_dec else "<"
        return (
            f"dec >= {self.minimum_dec_deg:.12f} AND "
            f"dec {upper_operator} {self.maximum_dec_deg:.12f}"
        )

    def contains_dec(self, dec_deg: float) -> bool:
        """Return whether a declination belongs to this strip's exact boundaries."""
        above_minimum = dec_deg >= self.minimum_dec_deg
        below_maximum = (
            dec_deg <= self.maximum_dec_deg
            if self.includes_maximum_dec
            else dec_deg < self.maximum_dec_deg
        )
        return above_minimum and below_maximum


def generate_declination_strips(
    center_dec_deg: float,
    radius_deg: float,
    maximum_strip_height_deg: float,
) -> list[DeclinationStrip]:
    """Partition a cone's full declination range without overlaps or gaps."""
    if not -90 <= center_dec_deg <= 90:
        raise ValueError("Center declination must lie between -90 and 90 degrees")
    if not 0 < radius_deg < 180:
        raise ValueError("Radius must lie between 0 and 180 degrees")
    if maximum_strip_height_deg <= 0:
        raise ValueError("Maximum strip height must be positive")
    minimum_dec_deg = max(-90.0, center_dec_deg - radius_deg)
    maximum_dec_deg = min(90.0, center_dec_deg + radius_deg)
    span_deg = maximum_dec_deg - minimum_dec_deg
    strip_count = max(1, ceil(span_deg / maximum_strip_height_deg - 1e-12))
    edges = np.linspace(minimum_dec_deg, maximum_dec_deg, strip_count + 1)
    return [
        DeclinationStrip(
            strip_index=index,
            minimum_dec_deg=float(edges[index]),
            maximum_dec_deg=float(edges[index + 1]),
            includes_maximum_dec=index == strip_count - 1,
        )
        for index in range(strip_count)
    ]


def cone_predicate(ra_deg: float, dec_deg: float, radius_deg: float) -> str:
    """Return the Data Lab predicate for the exact circular query."""
    return f"'t' = Q3C_RADIAL_QUERY(ra, dec, {ra_deg:.12f}, {dec_deg:.12f}, {radius_deg:.12f})"
