"""Freeze a reproducible four-zone M60 visual-audit sample before viewing images."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    EXTERNAL_DATA_DIR,
    M60_POSITIVE_CONTROL_AUDIT_CONTRACT,
    M60_POSITIVE_CONTROL_AUDIT_SAMPLE,
    M60_POSITIVE_CONTROL_KNOWN_RECOVERY,
    M60_POSITIVE_CONTROL_REVIEW_RULES,
    M60_POSITIVE_CONTROL_RUN_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.freeze_m60_review_rules import REVIEW_RULES_VERSION

AUDIT_VERSION = "m60_positive_control_visual_audit_v1"
SAMPLE_SIZE_PER_ZONE = 100
RADIAL_ZONES = (
    ("central_diagnostic_0_50_kpc", 0.0, 50.0),
    ("near_host_50_150_kpc", 50.0, 150.0),
    ("intermediate_150_300_kpc", 150.0, 300.0),
    ("far_300_600_kpc", 300.0, 600.0),
)


def resolve_external(path_text: str) -> Path:
    """Resolve a portable external-data locator."""
    prefix = "$BUBBLETEA_EXTERNAL_DATA/"
    if not path_text.startswith(prefix):
        raise RuntimeError(f"Expected an external-data locator: {path_text}")
    return EXTERNAL_DATA_DIR / path_text.removeprefix(prefix)


def assign_radial_zone(radius_kpc: float) -> str:
    """Assign one source to exactly one approved physical-radius zone."""
    for index, (name, lower, upper) in enumerate(RADIAL_ZONES):
        lower_match = radius_kpc >= lower if index == 0 else radius_kpc > lower
        if lower_match and radius_kpc <= upper:
            return name
    raise ValueError(f"Radius is outside the frozen M60 field: {radius_kpc}")


def selection_hash(source_id: int) -> str:
    """Return a stable ordering key for unbiased selection within a zone."""
    return hashlib.sha256(f"{AUDIT_VERSION}:{source_id}".encode()).hexdigest()


def main() -> None:
    """Write the unopened-field audit sample and its statistical weights."""
    run = json.loads(M60_POSITIVE_CONTROL_RUN_MANIFEST.read_text())
    rules = json.loads(M60_POSITIVE_CONTROL_REVIEW_RULES.read_text())
    review_path = resolve_external(run["external_outputs"]["selector_passing_review"])
    if calculate_sha256(review_path) != run["external_outputs"]["selector_passing_review_sha256"]:
        raise RuntimeError("External selector-passing table differs from its run digest")
    passing = pd.read_csv(review_path, dtype={"source_id": "int64"})
    known = pd.read_csv(M60_POSITIVE_CONTROL_KNOWN_RECOVERY, dtype={"gaia_dr3_ids": str})
    known_source_ids = set(
        pd.to_numeric(
            known.loc[known["gaia_identifier_count"].eq(1), "gaia_dr3_ids"],
            errors="raise",
        ).astype("int64")
    )
    eligible = passing.loc[~passing["source_id"].isin(known_source_ids)].copy()
    eligible["audit_radial_zone"] = eligible["projected_radius_kpc"].map(assign_radial_zone)
    eligible["audit_selection_hash"] = eligible["source_id"].map(selection_hash)

    sampled_frames = []
    zone_records = []
    for zone_name, lower, upper in RADIAL_ZONES:
        population = eligible.loc[eligible["audit_radial_zone"].eq(zone_name)].copy()
        if len(population) < SAMPLE_SIZE_PER_ZONE:
            raise RuntimeError(f"Zone {zone_name} contains fewer than 100 eligible sources")
        selected = population.sort_values(["audit_selection_hash", "source_id"]).head(
            SAMPLE_SIZE_PER_ZONE
        )
        selected["audit_sample_rank_in_zone"] = range(1, len(selected) + 1)
        selected["audit_zone_population_count"] = len(population)
        selected["audit_zone_sample_count"] = len(selected)
        selected["audit_inclusion_probability"] = len(selected) / len(population)
        selected["audit_design_weight"] = len(population) / len(selected)
        sampled_frames.append(selected)
        zone_records.append(
            {
                "zone_name": zone_name,
                "lower_radius_kpc": lower,
                "upper_radius_kpc": upper,
                "eligible_population_count": len(population),
                "sample_count": len(selected),
                "inclusion_probability": len(selected) / len(population),
                "design_weight": len(population) / len(selected),
            }
        )
    sample = pd.concat(sampled_frames, ignore_index=True)
    sample.insert(0, "audit_sample_id", [f"m60_audit_{index:04d}" for index in range(1, 401)])
    sample["audit_interpretation_scope"] = (
        "representative_visual_audit_not_promising_candidate_shortlist"
    )
    M60_POSITIVE_CONTROL_AUDIT_SAMPLE.write_text(sample.to_csv(index=False), encoding="utf-8")

    checks = {
        "complete_run_checks_passed": run["passed_count"] == run["check_count"],
        "review_rules_are_frozen": rules["review_rules_version"] == REVIEW_RULES_VERSION,
        "passing_population_matches_run": len(passing) == run["selector_passing_source_count"],
        "eleven_exact_identifier_literature_objects_are_separate": len(known_source_ids) == 11,
        "known_identifier_objects_are_excluded_from_audit": not sample["source_id"]
        .isin(known_source_ids)
        .any(),
        "four_hundred_unique_sources_are_sampled": len(sample) == 400
        and sample["source_id"].is_unique,
        "one_hundred_sources_are_sampled_per_zone": sample.groupby("audit_radial_zone")
        .size()
        .eq(SAMPLE_SIZE_PER_ZONE)
        .all(),
        "all_eligible_sources_have_one_zone": len(eligible)
        == sum(record["eligible_population_count"] for record in zone_records),
        "every_sampled_source_has_equal_chance_within_zone": sample.groupby("audit_radial_zone")[
            "audit_inclusion_probability"
        ]
        .nunique()
        .eq(1)
        .all(),
        "visual_flags_remain_unreviewed": sample["possible_star_forming_region_or_young_cluster"]
        .eq("not_reviewed")
        .all()
        and sample["possible_nearby_source_blend_or_image_problem"].eq("not_reviewed").all(),
        "no_image_was_requested_or_opened": True,
        "candidate_shortlist_is_not_part_of_audit": sample["audit_interpretation_scope"]
        .eq("representative_visual_audit_not_promising_candidate_shortlist")
        .all(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    artifact = {
        "audit_version": AUDIT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "frozen_before_audit_image_retrieval",
        "plain_language_scope": (
            "Randomly select 100 previously unidentified selector-retained sources "
            "from each of four physical-radius zones. Known literature objects and "
            "the deliberately promising shortlist remain separate."
        ),
        "selection_method": (
            "Within each radial zone, sort the SHA-256 hash of the audit version and "
            "Gaia source identifier, then select the first 100 rows."
        ),
        "zone_design": zone_records,
        "known_exact_identifier_object_count_kept_separate": len(known_source_ids),
        "eligible_unidentified_passing_population_count": len(eligible),
        "sample_count": len(sample),
        "weighting_rule": (
            "For population summaries, multiply each reviewed row by its audit design "
            "weight; do not treat the four zones as equally common."
        ),
        "sample_output": {
            "path": str(M60_POSITIVE_CONTROL_AUDIT_SAMPLE.relative_to(PROJECT_ROOT)),
            "sha256": calculate_sha256(M60_POSITIVE_CONTROL_AUDIT_SAMPLE),
        },
        "inputs": {
            "run_manifest_sha256": calculate_sha256(M60_POSITIVE_CONTROL_RUN_MANIFEST),
            "known_recovery_sha256": calculate_sha256(M60_POSITIVE_CONTROL_KNOWN_RECOVERY),
            "review_rules_sha256": calculate_sha256(M60_POSITIVE_CONTROL_REVIEW_RULES),
            "external_selector_passing_review_sha256": calculate_sha256(review_path),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    M60_POSITIVE_CONTROL_AUDIT_CONTRACT.write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"M60 visual-audit freeze failed: {checks}")


if __name__ == "__main__":
    main()
