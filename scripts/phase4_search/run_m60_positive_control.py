"""Retrieve, score, and measure the frozen complete M60 Gaia field."""

import argparse
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    FIRST_STAGE_HOST_PROFILE_FIXTURE,
    M60_POSITIVE_CONTROL_COUNT_BENCHMARK,
    M60_POSITIVE_CONTROL_EXTERNAL_DIR,
    M60_POSITIVE_CONTROL_KNOWN_OBJECTS,
    M60_POSITIVE_CONTROL_KNOWN_RECOVERY,
    M60_POSITIVE_CONTROL_PROFILE,
    M60_POSITIVE_CONTROL_RETRIEVAL_CONTRACT,
    M60_POSITIVE_CONTROL_RETRIEVAL_PLAN,
    M60_POSITIVE_CONTROL_RUN_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase3_background.adaptive_gaia_retrieval import (
    AdaptiveGaiaRetriever,
    file_sha256,
    load_leaf_plan,
    plan_adaptive_strips,
    write_plan,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.run_first_stage_host_profile import (
    add_projected_radius,
    make_profile,
)
from scripts.phase3_background.run_large_sky_development_scale import ArchiveTimeoutSession
from scripts.phase4_search.freeze_m60_source_retrieval import RETRIEVAL_CONTRACT_VERSION
from scripts.utils.point_source_selector import load_frozen_selector

RUN_VERSION = "m60_positive_control_run_v1"
HOST_NAME = "MESSIER 060"


def parse_arguments() -> argparse.Namespace:
    """Require explicit permission for source-row archive queries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def portable_external_path(path: Path) -> str:
    """Return a path rooted at the configured external-data directory."""
    relative_path = path.resolve().relative_to(M60_POSITIVE_CONTROL_EXTERNAL_DIR.parent.parent)
    return f"$BUBBLETEA_EXTERNAL_DATA/{relative_path.as_posix()}"


def known_recovery(scored: pd.DataFrame) -> pd.DataFrame:
    """Record exact Gaia-identifier recovery without inventing missing identifiers."""
    known = pd.read_csv(
        M60_POSITIVE_CONTROL_KNOWN_OBJECTS,
        dtype={"gaia_dr3_ids": str},
    )
    source_lookup = scored.set_index("source_id", drop=False)
    records = []
    for _, row in known.iterrows():
        record = row.to_dict()
        if int(row["gaia_identifier_count"]) != 1:
            record.update(
                {
                    "recovery_status": "not_testable_no_unique_gaia_identifier",
                    "retrieved_gaia_source": False,
                    "selector_passing": pd.NA,
                    "selector_probability": pd.NA,
                    "retrieved_g_mag": pd.NA,
                }
            )
        else:
            source_id = int(row["gaia_dr3_ids"])
            if source_id not in source_lookup.index:
                record.update(
                    {
                        "recovery_status": "unique_gaia_identifier_not_retrieved",
                        "retrieved_gaia_source": False,
                        "selector_passing": pd.NA,
                        "selector_probability": pd.NA,
                        "retrieved_g_mag": pd.NA,
                    }
                )
            else:
                source = source_lookup.loc[source_id]
                record.update(
                    {
                        "recovery_status": "exact_gaia_identifier_retrieved",
                        "retrieved_gaia_source": True,
                        "selector_passing": bool(source["point_source_logistic_selected"]),
                        "selector_probability": float(source["point_source_logistic_probability"]),
                        "retrieved_g_mag": float(source["phot_g_mean_mag"]),
                    }
                )
        records.append(record)
    return pd.DataFrame(records)


def main() -> None:
    """Run the complete frozen retrieval and write checked scientific artifacts."""
    if not parse_arguments().execute:
        raise RuntimeError("Live archive access requires --execute")
    if M60_POSITIVE_CONTROL_EXTERNAL_DIR.resolve().is_relative_to(PROJECT_ROOT.resolve()):
        raise RuntimeError("Set BUBBLETEA_EXTERNAL_DATA outside the repository")

    contract = json.loads(M60_POSITIVE_CONTROL_RETRIEVAL_CONTRACT.read_text())
    count = json.loads(M60_POSITIVE_CONTROL_COUNT_BENCHMARK.read_text())
    if contract["retrieval_contract_version"] != RETRIEVAL_CONTRACT_VERSION:
        raise RuntimeError("M60 retrieval contract is not expected")
    if contract["passed_count"] != contract["check_count"]:
        raise RuntimeError("M60 retrieval-contract safeguards did not pass")
    for path_text, expected_digest in contract["inputs"].items():
        if calculate_sha256(PROJECT_ROOT / path_text) != expected_digest:
            raise RuntimeError(f"Frozen M60 input changed: {path_text}")

    fixture = pd.read_csv(FIRST_STAGE_HOST_PROFILE_FIXTURE)
    host_fixture = fixture.loc[fixture["host_name"].eq(HOST_NAME)].copy()
    outer_rows = host_fixture.loc[host_fixture["outer_radius_kpc"].eq(600)]
    if len(host_fixture) != 14 or len(outer_rows) != 1:
        raise RuntimeError("Frozen M60 geometry is incomplete")
    host = outer_rows.iloc[0]

    M60_POSITIVE_CONTROL_EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    external_plan_path = M60_POSITIVE_CONTROL_EXTERNAL_DIR / "measured_plan.csv"
    external_scored_path = M60_POSITIVE_CONTROL_EXTERNAL_DIR / "scored_sources.csv"
    external_review_path = M60_POSITIVE_CONTROL_EXTERNAL_DIR / "selector_passing_review.csv"
    service = tap.TAPService(DATA_LAB_TAP_URL, session=ArchiveTimeoutSession())
    total_started = perf_counter()
    planning_started = perf_counter()
    planned = plan_adaptive_strips(
        service,
        contract["base_where"],
        max(-90.0, host["host_dec_deg"] - host["outer_radius_deg"]),
        min(90.0, host["host_dec_deg"] + host["outer_radius_deg"]),
        int(contract["maximum_rows_per_strip"]),
        progress_path=external_plan_path,
    )
    planning_seconds = perf_counter() - planning_started
    write_plan(external_plan_path, planned)
    pd.DataFrame([asdict(strip) for strip in planned]).to_csv(
        M60_POSITIVE_CONTROL_RETRIEVAL_PLAN, index=False
    )
    leaf_strips = load_leaf_plan(external_plan_path)
    retriever = AdaptiveGaiaRetriever(
        service,
        contract["base_where"],
        M60_POSITIVE_CONTROL_EXTERNAL_DIR / "strips",
        tuple(contract["source_columns"]),
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
    profile.to_csv(M60_POSITIVE_CONTROL_PROFILE, index=False)

    passing_review = scored.loc[scored["point_source_logistic_selected"]].copy()
    for column_name, default_value in contract["review_defaults"].items():
        passing_review[column_name] = default_value
    passing_review.to_csv(external_review_path, index=False)
    recovery = known_recovery(scored)
    recovery.to_csv(M60_POSITIVE_CONTROL_KNOWN_RECOVERY, index=False)
    total_seconds = perf_counter() - total_started

    leaf_count = sum(strip.measured_source_count for strip in leaf_strips)
    confirmed = recovery.loc[recovery["classification_state"].eq("confirmed")]
    checks = {
        "retrieval_completed": bool(retrieval_result["complete"]),
        "leaf_counts_match_raw_count": leaf_count == contract["raw_source_count"],
        "retrieved_rows_match_raw_count": len(scored) == contract["raw_source_count"],
        "source_identifiers_are_unique": scored["source_id"].is_unique,
        "all_rings_are_preserved": len(profile) == 14,
        "profile_contains_every_source": int(profile["all_source_count"].sum()) == len(scored),
        "profile_selected_count_matches_rows": int(profile["selector_passing_source_count"].sum())
        == len(passing_review),
        "two_confirmed_controls_are_retrieved": len(confirmed) == 2
        and confirmed["retrieved_gaia_source"].all(),
        "review_rows_start_unreviewed": passing_review[
            "possible_nearby_source_blend_or_image_problem"
        ]
        .eq("not_reviewed")
        .all(),
        "review_flags_remove_no_sources": len(passing_review)
        == int(scored["point_source_logistic_selected"].sum()),
        "source_rows_are_external": not external_scored_path.resolve().is_relative_to(
            PROJECT_ROOT.resolve()
        ),
        "no_gaia_imaging_masks_applied": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    manifest = {
        "run_version": RUN_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "complete_m60_selector_v1_profile",
        "plain_language_scope": (
            "Every Gaia source in the frozen M60 circle and magnitude range was "
            "retrieved, scored locally, and counted in preserved physical rings. "
            "Review columns were initialized but no source was visually classified."
        ),
        "selector_version": contract["selector_version"],
        "raw_source_count": len(scored),
        "selector_passing_source_count": len(passing_review),
        "confirmed_control_retrieved_count": int(confirmed["retrieved_gaia_source"].sum()),
        "confirmed_control_selector_passing_count": int(
            confirmed["selector_passing"].fillna(False).sum()
        ),
        "planned_node_count": len(planned),
        "final_strip_count": len(leaf_strips),
        "maximum_leaf_source_count": max(strip.measured_source_count for strip in leaf_strips),
        "planning_seconds": planning_seconds,
        "retrieval_seconds": retrieval_seconds,
        "scoring_seconds": scoring_seconds,
        "total_seconds": total_seconds,
        "profile_output": {
            "path": str(M60_POSITIVE_CONTROL_PROFILE.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(M60_POSITIVE_CONTROL_PROFILE),
        },
        "known_recovery_output": {
            "path": str(M60_POSITIVE_CONTROL_KNOWN_RECOVERY.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(M60_POSITIVE_CONTROL_KNOWN_RECOVERY),
        },
        "external_outputs": {
            "scored_sources": portable_external_path(external_scored_path),
            "scored_sources_sha256": file_sha256(external_scored_path),
            "selector_passing_review": portable_external_path(external_review_path),
            "selector_passing_review_sha256": file_sha256(external_review_path),
        },
        "archive_count_queries_executed_or_reused": len(planned),
        "archive_source_queries_executed_or_reused": len(leaf_strips),
        "count_benchmark_source_count": count["source_count_in_frozen_magnitude_domain"],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    M60_POSITIVE_CONTROL_RUN_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"M60 complete-field run failed: {checks}")


if __name__ == "__main__":
    main()
