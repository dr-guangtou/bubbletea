"""Independently validate the complete M60 selector-v1 run artifacts."""

import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    EXTERNAL_DATA_DIR,
    M60_POSITIVE_CONTROL_KNOWN_RECOVERY,
    M60_POSITIVE_CONTROL_PROFILE,
    M60_POSITIVE_CONTROL_RUN_MANIFEST,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256


def external_path(path_text: str) -> Path:
    """Resolve an external-data locator on the current machine."""
    prefix = "$BUBBLETEA_EXTERNAL_DATA/"
    if not path_text.startswith(prefix):
        raise RuntimeError(f"Expected external-data locator: {path_text}")
    return EXTERNAL_DATA_DIR / path_text.removeprefix(prefix)


def main() -> None:
    """Verify external hashes and independent count relationships."""
    manifest = json.loads(M60_POSITIVE_CONTROL_RUN_MANIFEST.read_text())
    profile = pd.read_csv(M60_POSITIVE_CONTROL_PROFILE)
    recovery = pd.read_csv(M60_POSITIVE_CONTROL_KNOWN_RECOVERY)
    scored_path = external_path(manifest["external_outputs"]["scored_sources"])
    review_path = external_path(manifest["external_outputs"]["selector_passing_review"])
    scored = pd.read_csv(scored_path, dtype={"source_id": "int64"})
    review = pd.read_csv(review_path, dtype={"source_id": "int64"})
    confirmed = recovery.loc[recovery["classification_state"].eq("confirmed")]
    checks = {
        "run_safeguards_passed": manifest["passed_count"] == manifest["check_count"],
        "profile_digest_matches": file_sha256(M60_POSITIVE_CONTROL_PROFILE)
        == manifest["profile_output"]["sha256"],
        "recovery_digest_matches": file_sha256(M60_POSITIVE_CONTROL_KNOWN_RECOVERY)
        == manifest["known_recovery_output"]["sha256"],
        "external_scored_digest_matches": file_sha256(scored_path)
        == manifest["external_outputs"]["scored_sources_sha256"],
        "external_review_digest_matches": file_sha256(review_path)
        == manifest["external_outputs"]["selector_passing_review_sha256"],
        "all_source_count_matches_profile": len(scored) == int(profile["all_source_count"].sum()),
        "passing_count_matches_profile": len(review)
        == int(profile["selector_passing_source_count"].sum()),
        "review_contains_exact_passing_identifiers": set(review["source_id"])
        == set(scored.loc[scored["point_source_logistic_selected"], "source_id"]),
        "all_visual_flags_are_unreviewed": review["possible_nearby_source_blend_or_image_problem"]
        .eq("not_reviewed")
        .all()
        and review["possible_star_forming_region_or_young_cluster"].eq("not_reviewed").all(),
        "both_confirmed_controls_pass_selector": len(confirmed) == 2
        and confirmed["selector_passing"].astype(bool).all(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    if not all(checks.values()):
        raise RuntimeError(f"M60 run validation failed: {checks}")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
