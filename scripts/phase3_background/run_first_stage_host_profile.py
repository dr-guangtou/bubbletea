"""Retrieve and measure the first frozen 600 kpc Gaia host profile."""

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    FIRST_STAGE_HOST_PROFILE,
    FIRST_STAGE_HOST_PROFILE_COUNT_BENCHMARK,
    FIRST_STAGE_HOST_PROFILE_FIXTURE,
    FIRST_STAGE_HOST_PROFILE_RETRIEVAL_DIR,
    FIRST_STAGE_HOST_PROFILE_RETRIEVAL_PLAN,
    FIRST_STAGE_HOST_PROFILE_RUN_MANIFEST,
    GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import (
    AdaptiveGaiaRetriever,
    file_sha256,
    load_leaf_plan,
    plan_adaptive_strips,
    write_plan,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.freeze_first_stage_host_profile_count import count_query
from scripts.phase3_background.query_partition import cone_predicate
from scripts.phase3_background.run_large_sky_development_scale import ArchiveTimeoutSession
from scripts.utils.point_source_selector import (
    MAXIMUM_G_MAGNITUDE,
    MINIMUM_G_MAGNITUDE,
    RAW_GAIA_COLUMNS,
    SELECTOR_VERSION,
    load_frozen_selector,
)

RUN_VERSION = "first_stage_host_profile_ngc4698_v1"
EXPECTED_HOST_NAME = "NGC 4698"
EXPECTED_OUTER_RADIUS_KPC = 600


def parse_arguments() -> argparse.Namespace:
    """Require explicit permission for planning and source retrieval queries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute measured planning counts and resumable source retrieval.",
    )
    return parser.parse_args()


def require_external_checkpoint_root() -> None:
    """Refuse to save source-level Gaia data inside the repository."""
    if FIRST_STAGE_HOST_PROFILE_RETRIEVAL_DIR.resolve().is_relative_to(PROJECT_ROOT.resolve()):
        raise RuntimeError(
            "Source-level host data must be outside the repository; set "
            "BUBBLETEA_EXTERNAL_DATA, for example to ~/Dropbox/work/data"
        )


def base_where(host: pd.Series) -> str:
    """Return the frozen circular and magnitude-domain source predicate."""
    return (
        f"{cone_predicate(float(host['host_ra_deg']), float(host['host_dec_deg']), float(host['outer_radius_deg']))} "
        f"AND phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} AND {MAXIMUM_G_MAGNITUDE}"
    )


def add_projected_radius(sources: pd.DataFrame, host: pd.Series) -> pd.DataFrame:
    """Add continuous angular and projected physical radius from the host."""
    host_coordinate = SkyCoord(
        float(host["host_ra_deg"]) * u.deg,
        float(host["host_dec_deg"]) * u.deg,
        frame="icrs",
    )
    source_coordinates = SkyCoord(
        sources["ra"].to_numpy() * u.deg,
        sources["dec"].to_numpy() * u.deg,
        frame="icrs",
    )
    separation_deg = host_coordinate.separation(source_coordinates).deg
    result = sources.copy()
    result["host_separation_deg"] = separation_deg
    result["projected_radius_kpc"] = (
        np.tan(np.deg2rad(separation_deg)) * float(host["host_distance_mpc"]) * 1000
    )
    return result


def make_profile(scored: pd.DataFrame, fixture: pd.DataFrame) -> pd.DataFrame:
    """Count all and selector-passing sources in every preserved physical ring."""
    records = []
    for _, ring in fixture.sort_values("inner_radius_kpc").iterrows():
        inner_radius_kpc = float(ring["inner_radius_kpc"])
        outer_radius_kpc = float(ring["outer_radius_kpc"])
        inside = scored["projected_radius_kpc"].gt(inner_radius_kpc) & scored[
            "projected_radius_kpc"
        ].le(outer_radius_kpc)
        if inner_radius_kpc == 0:
            inside = scored["projected_radius_kpc"].ge(0) & scored["projected_radius_kpc"].le(
                outer_radius_kpc
            )
        ring_sources = scored.loc[inside]
        selected_count = int(ring_sources["point_source_logistic_selected"].sum())
        all_source_count = len(ring_sources)
        area_square_deg = float(ring["requested_ring_area_square_deg"])
        records.append(
            {
                **ring.to_dict(),
                "all_source_count": all_source_count,
                "selector_passing_source_count": selected_count,
                "all_source_density_per_square_deg": all_source_count / area_square_deg,
                "selector_passing_density_per_square_deg": selected_count / area_square_deg,
                "selector_passing_fraction": (
                    selected_count / all_source_count if all_source_count else np.nan
                ),
                "profile_measurement_status": "complete_verified_gaia_coverage",
            }
        )
    return pd.DataFrame(records)


def main() -> None:
    """Plan, retrieve, score, and summarize the NGC 4698 profile."""
    arguments = parse_arguments()
    if not arguments.execute:
        raise RuntimeError("Live archive access requires the explicit --execute flag")
    require_external_checkpoint_root()
    fixture = pd.read_csv(FIRST_STAGE_HOST_PROFILE_FIXTURE)
    host_fixture = fixture.loc[fixture["host_name"].eq(EXPECTED_HOST_NAME)].copy()
    outer_rows = host_fixture.loc[host_fixture["outer_radius_kpc"].eq(EXPECTED_OUTER_RADIUS_KPC)]
    if len(outer_rows) != 1 or len(host_fixture) != 14:
        raise RuntimeError("Frozen NGC 4698 profile geometry is incomplete")
    host = outer_rows.iloc[0]
    count_benchmark = json.loads(
        FIRST_STAGE_HOST_PROFILE_COUNT_BENCHMARK.read_text(encoding="utf-8")
    )
    retrieval_limit = json.loads(
        GAIA_FULL_SELECTOR_RETRIEVAL_BENCHMARK_MANIFEST.read_text(encoding="utf-8")
    )
    maximum_rows_per_strip = int(retrieval_limit["provisional_safe_rows_per_strip"])
    query_predicate = base_where(host)
    expected_count_query = count_query(
        float(host["host_ra_deg"]),
        float(host["host_dec_deg"]),
        float(host["outer_radius_deg"]),
    )
    if count_benchmark["query_sha256"] != hashlib.sha256(expected_count_query.encode()).hexdigest():
        raise RuntimeError("Count benchmark does not match the frozen host geometry")

    checkpoint_directory = FIRST_STAGE_HOST_PROFILE_RETRIEVAL_DIR / "ngc_4698"
    checkpoint_directory.mkdir(parents=True, exist_ok=True)
    external_plan_path = checkpoint_directory / "measured_plan.csv"
    external_scored_path = checkpoint_directory / "scored_sources.csv"
    service = tap.TAPService(DATA_LAB_TAP_URL, session=ArchiveTimeoutSession())
    total_started = perf_counter()
    plan_started = perf_counter()
    planned = plan_adaptive_strips(
        service,
        query_predicate,
        max(-90.0, float(host["host_dec_deg"]) - float(host["outer_radius_deg"])),
        min(90.0, float(host["host_dec_deg"]) + float(host["outer_radius_deg"])),
        maximum_rows_per_strip,
        progress_path=external_plan_path,
    )
    planning_seconds = perf_counter() - plan_started
    write_plan(external_plan_path, planned)
    pd.DataFrame([asdict(strip) for strip in planned]).to_csv(
        FIRST_STAGE_HOST_PROFILE_RETRIEVAL_PLAN, index=False
    )
    leaf_strips = load_leaf_plan(external_plan_path)
    retriever = AdaptiveGaiaRetriever(
        service,
        query_predicate,
        checkpoint_directory / "strips",
        tuple(RAW_GAIA_COLUMNS),
    )
    retrieval_started = perf_counter()
    retrieval_result = retriever.run(leaf_strips)
    retrieval_seconds = perf_counter() - retrieval_started
    sources = retriever.combine(leaf_strips)
    scoring_started = perf_counter()
    scored = load_frozen_selector().score(add_projected_radius(sources, host))
    scoring_seconds = perf_counter() - scoring_started
    scored.to_csv(external_scored_path, index=False)
    profile = make_profile(scored, host_fixture)
    profile.to_csv(FIRST_STAGE_HOST_PROFILE, index=False)
    total_seconds = perf_counter() - total_started

    leaf_count = sum(strip.measured_source_count for strip in leaf_strips)
    profile_all_count = int(profile["all_source_count"].sum())
    profile_selected_count = int(profile["selector_passing_source_count"].sum())
    checks = {
        "frozen_host_and_outer_radius_used": (
            host["host_name"] == EXPECTED_HOST_NAME
            and int(host["outer_radius_kpc"]) == EXPECTED_OUTER_RADIUS_KPC
        ),
        "count_benchmark_checks_passed": (
            count_benchmark["passed_count"] == count_benchmark["check_count"]
        ),
        "adaptive_plan_is_complete": bool(retrieval_result["complete"]),
        "every_leaf_is_below_measured_row_limit": all(
            strip.measured_source_count <= maximum_rows_per_strip for strip in leaf_strips
        ),
        "leaf_counts_match_initial_count_benchmark": (
            leaf_count == count_benchmark["source_count_in_frozen_magnitude_domain"]
        ),
        "retrieved_rows_match_measured_leaf_counts": len(sources) == leaf_count,
        "retrieved_source_identifiers_are_unique": sources["source_id"].is_unique,
        "all_sources_have_continuous_physical_radius": scored["projected_radius_kpc"].notna().all(),
        "all_sources_fall_inside_profile_rings": profile_all_count == len(scored),
        "profile_has_all_fourteen_frozen_rings": len(profile) == 14,
        "selected_profile_matches_source_decisions": profile_selected_count
        == int(scored["point_source_logistic_selected"].sum()),
        "central_rings_remain_withheld_from_final_inference": not profile.loc[
            profile["inside_conservative_central_exclusion"].astype(bool),
            "eligible_for_final_inference",
        ].any(),
        "r50_normalized_profile_remains_explicitly_unavailable": profile[
            "r50_normalized_profile_status"
        ]
        .eq("unavailable_missing_verified_r50")
        .all(),
        "no_gaia_imaging_masks_applied": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    manifest = {
        "run_version": RUN_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "complete_first_stage_single_host_profile",
        "plain_language_scope": (
            "The complete frozen Gaia circle around NGC 4698 was divided into "
            "fourteen physical rings. Both all-source and point-source-selector "
            "counts are reported. The inner 50 kpc remains a diagnostic region, "
            "and no final outer boundary is selected."
        ),
        "host_name": EXPECTED_HOST_NAME,
        "selector_version": SELECTOR_VERSION,
        "maximum_rows_per_strip": maximum_rows_per_strip,
        "planned_node_count": len(planned),
        "final_strip_count": len(leaf_strips),
        "maximum_leaf_source_count": max(strip.measured_source_count for strip in leaf_strips),
        "count_benchmark_source_count": count_benchmark["source_count_in_frozen_magnitude_domain"],
        "retrieved_source_count": len(scored),
        "selector_passing_source_count": int(scored["point_source_logistic_selected"].sum()),
        "planning_seconds": planning_seconds,
        "retrieval_seconds": retrieval_seconds,
        "scoring_seconds": scoring_seconds,
        "total_seconds": total_seconds,
        "profile_output": {
            "path": str(FIRST_STAGE_HOST_PROFILE.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(FIRST_STAGE_HOST_PROFILE),
        },
        "plan_output": {
            "path": str(FIRST_STAGE_HOST_PROFILE_RETRIEVAL_PLAN.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(FIRST_STAGE_HOST_PROFILE_RETRIEVAL_PLAN),
        },
        "external_source_output": {
            "path": str(external_scored_path.resolve()),
            "sha256": file_sha256(external_scored_path),
            "bytes": external_scored_path.stat().st_size,
        },
        "archive_count_queries_executed_or_reused": len(planned),
        "archive_source_queries_executed_or_reused": len(leaf_strips),
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    FIRST_STAGE_HOST_PROFILE_RUN_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"First-stage host profile failed: {checks}")


if __name__ == "__main__":
    main()
