"""Validate spherical cross-match geometry, radius enforcement, and diagnostics.

Inputs are deterministic synthetic positions plus the cached authoritative Gaia
association geometry. The script performs no remote queries and changes no
database state. It writes one reproducible JSON validation artifact.
"""

import argparse
import json
import logging
import math
from pathlib import Path
from time import perf_counter

import pandas as pd
from pyvo.dal import tap

from scripts.config import CROSSMATCH_GEOMETRY_VALIDATION, LITERATURE_VALIDATION
from scripts.phase1_literature.xmatch_gaia import DATALAB_TAP_URL, build_gaia_query
from scripts.phase1_literature.xmatch_legacy_survey import build_legacy_query
from scripts.utils.crossmatch import select_spherical_match

logger = logging.getLogger(__name__)

KNOWN_GEOMETRY_PATH = LITERATURE_VALIDATION / "gaia_association_pair_geometry.csv"


def parse_arguments() -> argparse.Namespace:
    """Parse the optional read-only live-service validation flag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live-service",
        action="store_true",
        help="Run one small read-only cone query against each NOIRLab catalog.",
    )
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    """Raise a validation error when a required condition is false."""
    if not condition:
        raise RuntimeError(message)


def offset_ra(ra: float, dec: float, separation_arcsec: float) -> float:
    """Approximate a small eastward angular offset for fixture construction."""
    return (ra + separation_arcsec / (3600.0 * math.cos(math.radians(dec)))) % 360.0


def validate_query_geometry() -> dict[str, bool]:
    """Require both service queries to use ADQL spherical cones."""
    query_checks = {}
    for catalog_name, query in {
        "gaia": build_gaia_query(359.9999, 80.0, 1.0),
        "legacy": build_legacy_query(359.9999, 80.0, 2.0),
    }.items():
        normalized_query = query.upper()
        uses_cone = "Q3C_RADIAL_QUERY(" in normalized_query
        avoids_box = " BETWEEN " not in normalized_query
        require(uses_cone, f"{catalog_name} query does not use a spherical cone")
        require(avoids_box, f"{catalog_name} query still uses a rectangular box")
        query_checks[f"{catalog_name}_uses_cone"] = uses_cone
        query_checks[f"{catalog_name}_avoids_box"] = avoids_box
    return query_checks


def validate_synthetic_cases() -> list[dict[str, object]]:
    """Exercise declination, wraparound, radius, ambiguity, and tie cases."""
    fixture_results = []
    selected, diagnostics = select_spherical_match(
        pd.DataFrame(columns=["source_id", "ra", "dec"]),
        120.0,
        0.0,
        1.0,
        "source_id",
    )
    require(selected is None, "Empty candidate table produced a match")
    require(diagnostics["match_count_within_radius"] == 0, "Empty count is wrong")
    fixture_results.append(
        {
            "case": "no_match",
            "selected_source_id": None,
            "distance_arcsec": None,
            "match_count_within_radius": diagnostics["match_count_within_radius"],
        }
    )
    positions = [
        ("equator", 120.0, 0.0),
        ("north_high_declination", 120.0, 80.0),
        ("south_high_declination", 120.0, -80.0),
        ("right_ascension_wrap", 359.9999, 0.0),
    ]
    for case_name, ra, dec in positions:
        candidate_ra = offset_ra(ra, dec, 0.5)
        candidates = pd.DataFrame(
            [{"source_id": f"{case_name}_source", "ra": candidate_ra, "dec": dec}]
        )
        selected, diagnostics = select_spherical_match(candidates, ra, dec, 1.0, "source_id")
        require(selected is not None, f"{case_name} in-radius source was rejected")
        require(
            math.isclose(selected["dist_arcsec"], 0.5, abs_tol=1e-6),
            f"{case_name} spherical distance is incorrect",
        )
        fixture_results.append(
            {
                "case": case_name,
                "selected_source_id": selected["source_id"],
                "distance_arcsec": selected["dist_arcsec"],
                "match_count_within_radius": diagnostics["match_count_within_radius"],
            }
        )

    radius_candidates = pd.DataFrame(
        [
            {"source_id": "inside", "ra": 20.0, "dec": 10.0 + 0.999 / 3600.0},
            {"source_id": "outside", "ra": 20.0, "dec": 10.0 + 1.001 / 3600.0},
        ]
    )
    selected, diagnostics = select_spherical_match(radius_candidates, 20.0, 10.0, 1.0, "source_id")
    require(selected is not None and selected["source_id"] == "inside", "Radius failed")
    require(diagnostics["match_count_within_radius"] == 1, "Outside source retained")
    fixture_results.append(
        {
            "case": "strict_radius",
            "selected_source_id": selected["source_id"],
            "distance_arcsec": selected["dist_arcsec"],
            "match_count_within_radius": diagnostics["match_count_within_radius"],
        }
    )

    ambiguous_candidates = pd.DataFrame(
        [
            {"source_id": "farther", "ra": 30.0, "dec": 20.0 + 0.6 / 3600.0},
            {"source_id": "nearer", "ra": 30.0, "dec": 20.0 + 0.2 / 3600.0},
        ]
    )
    selected, diagnostics = select_spherical_match(
        ambiguous_candidates, 30.0, 20.0, 1.0, "source_id"
    )
    require(selected is not None and selected["source_id"] == "nearer", "Nearest failed")
    require(diagnostics["ambiguous_match"] is True, "Ambiguity was not retained")
    require(diagnostics["match_count_within_radius"] == 2, "Candidate count is wrong")
    require(
        math.isclose(diagnostics["nearest_neighbor_gap_arcsec"], 0.4, abs_tol=1e-6),
        "Nearest-neighbor gap is wrong",
    )
    require(len(json.loads(diagnostics["candidate_matches_json"])) == 2, "Candidates lost")
    fixture_results.append(
        {
            "case": "ambiguity",
            "selected_source_id": selected["source_id"],
            "distance_arcsec": selected["dist_arcsec"],
            "match_count_within_radius": diagnostics["match_count_within_radius"],
        }
    )

    tied_candidates = pd.DataFrame(
        [
            {"source_id": "source_b", "ra": 40.0, "dec": 0.0001},
            {"source_id": "source_a", "ra": 40.0, "dec": 0.0001},
        ]
    )
    selected, _ = select_spherical_match(tied_candidates, 40.0, 0.0, 1.0, "source_id")
    require(selected is not None and selected["source_id"] == "source_a", "Tie unstable")
    fixture_results.append(
        {
            "case": "stable_tie",
            "selected_source_id": selected["source_id"],
            "distance_arcsec": selected["dist_arcsec"],
            "match_count_within_radius": 2,
        }
    )
    return fixture_results


def validate_known_matches(path: Path) -> list[dict[str, object]]:
    """Reproduce cached authoritative matches at positive and negative declination."""
    rows = pd.read_csv(path)
    representative_rows = [
        rows.loc[rows["gaia_dec"].idxmin()],
        rows.loc[rows["gaia_dec"].idxmax()],
    ]
    results = []
    for row in representative_rows:
        candidates = pd.DataFrame(
            [{"source_id": row["gaia_dr3_id"], "ra": row["gaia_ra"], "dec": row["gaia_dec"]}]
        )
        radius_arcsec = float(row["gaia_distance_1_arcsec"]) + 0.001
        selected, _ = select_spherical_match(
            candidates,
            float(row["ra_1"]),
            float(row["dec_1"]),
            radius_arcsec,
            "source_id",
        )
        require(selected is not None, "Known authoritative Gaia match was not recovered")
        require(
            math.isclose(
                selected["dist_arcsec"],
                float(row["gaia_distance_1_arcsec"]),
                abs_tol=1e-9,
            ),
            "Known authoritative Gaia separation was not reproduced",
        )
        results.append(
            {
                "gaia_dr3_id": str(int(row["gaia_dr3_id"])),
                "declination_degrees": float(row["gaia_dec"]),
                "distance_arcsec": selected["dist_arcsec"],
            }
        )
    return results


def benchmark_geometry(iterations: int = 1000) -> dict[str, float | int]:
    """Measure the local selection cost on a small deterministic workload."""
    candidates = pd.DataFrame(
        [
            {"source_id": "one", "ra": offset_ra(120.0, 80.0, 0.2), "dec": 80.0},
            {"source_id": "two", "ra": offset_ra(120.0, 80.0, 0.7), "dec": 80.0},
            {"source_id": "outside", "ra": offset_ra(120.0, 80.0, 1.2), "dec": 80.0},
        ]
    )
    started = perf_counter()
    for _ in range(iterations):
        select_spherical_match(candidates, 120.0, 80.0, 1.0, "source_id")
    elapsed_seconds = perf_counter() - started
    return {
        "iterations": iterations,
        "elapsed_seconds": elapsed_seconds,
        "milliseconds_per_selection": elapsed_seconds * 1000.0 / iterations,
    }


def validate_live_service() -> list[dict[str, float | int | str]]:
    """Run one bounded read-only cone query against each catalog."""
    service = tap.TAPService(DATALAB_TAP_URL)
    target_ra = 188.4429630041478
    target_dec = 11.950621659136852
    results = []
    query_definitions = [
        ("gaia_dr3", build_gaia_query(target_ra, target_dec, 1.0), "source_id", 1.0),
        (
            "legacy_survey_dr10",
            build_legacy_query(target_ra, target_dec, 2.0),
            "ls_id",
            2.0,
        ),
    ]
    for catalog_name, query, identifier_column, radius_arcsec in query_definitions:
        started = perf_counter()
        candidates = service.run_sync(query, maxrec=10).to_table().to_pandas()
        elapsed_seconds = perf_counter() - started
        selected, diagnostics = select_spherical_match(
            candidates,
            target_ra,
            target_dec,
            radius_arcsec,
            identifier_column,
        )
        require(selected is not None, f"Live {catalog_name} cone returned no local match")
        results.append(
            {
                "catalog": catalog_name,
                "elapsed_seconds": elapsed_seconds,
                "rows_returned": len(candidates),
                "rows_within_radius": diagnostics["match_count_within_radius"],
                "nearest_distance_arcsec": selected["dist_arcsec"],
            }
        )
    return results


def main() -> None:
    """Run all validations and write the measured artifact."""
    arguments = parse_arguments()
    started = perf_counter()
    output = {
        "schema_version": 1,
        "query_checks": validate_query_geometry(),
        "synthetic_cases": validate_synthetic_cases(),
        "known_gaia_matches": validate_known_matches(KNOWN_GEOMETRY_PATH),
        "benchmark": benchmark_geometry(),
    }
    if arguments.live_service:
        output["live_service_checks"] = validate_live_service()
    output["total_elapsed_seconds"] = perf_counter() - started
    CROSSMATCH_GEOMETRY_VALIDATION.parent.mkdir(parents=True, exist_ok=True)
    CROSSMATCH_GEOMETRY_VALIDATION.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    logger.info("Wrote cross-match validation to %s", CROSSMATCH_GEOMETRY_VALIDATION)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
