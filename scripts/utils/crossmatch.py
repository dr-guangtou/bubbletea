"""Shared spherical-geometry helpers for catalog cross-matches."""

import json
import math
from typing import Any

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord


def validate_crossmatch_target(ra: float, dec: float, radius_arcsec: float) -> None:
    """Validate one sky position and a positive cone radius."""
    if not math.isfinite(ra) or not 0.0 <= ra < 360.0:
        raise ValueError(f"Right ascension must be finite and in [0, 360): {ra}")
    if not math.isfinite(dec) or not -90.0 <= dec <= 90.0:
        raise ValueError(f"Declination must be finite and in [-90, 90]: {dec}")
    if not math.isfinite(radius_arcsec) or radius_arcsec <= 0.0:
        raise ValueError(f"Cross-match radius must be positive and finite: {radius_arcsec}")


def build_datalab_cone_predicate(
    ra: float,
    dec: float,
    radius_arcsec: float,
    ra_column: str = "ra",
    dec_column: str = "dec",
) -> str:
    """Build a NOIRLab Data Lab Q3C cone predicate after validating inputs."""
    validate_crossmatch_target(ra, dec, radius_arcsec)
    radius_degrees = radius_arcsec / 3600.0
    return (
        "'t' = Q3C_RADIAL_QUERY("
        f"{ra_column}, {dec_column}, {ra:.12f}, {dec:.12f}, {radius_degrees:.12f}"
        ")"
    )


def _json_scalar(value: Any) -> Any:
    """Convert table scalar values to deterministic JSON-compatible values."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def select_spherical_match(
    candidates: pd.DataFrame,
    target_ra: float,
    target_dec: float,
    radius_arcsec: float,
    identifier_column: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Select the nearest in-cone candidate and preserve ambiguity diagnostics."""
    validate_crossmatch_target(target_ra, target_dec, radius_arcsec)
    required_columns = {identifier_column, "ra", "dec"}
    missing_columns = sorted(required_columns - set(candidates.columns))
    if missing_columns:
        raise ValueError(f"Candidate table is missing columns: {missing_columns}")

    valid_candidates = candidates.copy()
    valid_candidates["ra"] = pd.to_numeric(valid_candidates["ra"], errors="coerce")
    valid_candidates["dec"] = pd.to_numeric(valid_candidates["dec"], errors="coerce")
    valid_coordinates = valid_candidates["ra"].between(
        0.0, 360.0, inclusive="left"
    ) & valid_candidates["dec"].between(-90.0, 90.0, inclusive="both")
    valid_candidates = valid_candidates.loc[valid_coordinates].copy()
    valid_candidates["dist_arcsec"] = pd.Series(index=valid_candidates.index, dtype="float64")

    if not valid_candidates.empty:
        target = SkyCoord(target_ra * u.deg, target_dec * u.deg)
        candidate_coordinates = SkyCoord(
            valid_candidates["ra"].to_numpy() * u.deg,
            valid_candidates["dec"].to_numpy() * u.deg,
        )
        valid_candidates.loc[:, "dist_arcsec"] = target.separation(candidate_coordinates).arcsec
        valid_candidates = valid_candidates.loc[
            valid_candidates["dist_arcsec"] <= radius_arcsec
        ].copy()

    valid_candidates["_stable_identifier"] = valid_candidates.get(
        identifier_column, pd.Series(dtype="object")
    ).astype(str)
    valid_candidates = valid_candidates.sort_values(
        ["dist_arcsec", "_stable_identifier"], kind="mergesort"
    )

    candidate_summaries = [
        {
            identifier_column: _json_scalar(row[identifier_column]),
            "ra": float(row["ra"]),
            "dec": float(row["dec"]),
            "dist_arcsec": float(row["dist_arcsec"]),
        }
        for _, row in valid_candidates.iterrows()
    ]
    match_count = len(valid_candidates)
    nearest_distance = float(valid_candidates.iloc[0]["dist_arcsec"]) if match_count else None
    second_nearest_distance = (
        float(valid_candidates.iloc[1]["dist_arcsec"]) if match_count > 1 else None
    )
    diagnostics = {
        "query_radius_arcsec": radius_arcsec,
        "match_count_within_radius": match_count,
        "nearest_dist_arcsec": nearest_distance,
        "second_nearest_dist_arcsec": second_nearest_distance,
        "nearest_neighbor_gap_arcsec": (
            second_nearest_distance - nearest_distance
            if second_nearest_distance is not None and nearest_distance is not None
            else None
        ),
        "ambiguous_match": match_count > 1,
        "candidate_matches_json": json.dumps(
            candidate_summaries, sort_keys=True, separators=(",", ":")
        ),
    }
    if not match_count:
        return None, diagnostics

    selected = valid_candidates.drop(columns="_stable_identifier").iloc[0].to_dict()
    return selected, diagnostics
