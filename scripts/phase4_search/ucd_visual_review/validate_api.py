"""Validate the UCD visual review API against frozen bundle data.

Runs deterministic API checks with the Flask test client (no live server or remote
queries): endpoint shape, review validation, optimistic concurrency, and export.
Writes a validation JSON and fails non-zero if any check fails.
"""

import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.config import (
    PROJECT_ROOT,
    UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST,
    UCD_VISUAL_REVIEW_BUNDLE_INDEX,
)
from scripts.phase4_search.ucd_visual_review import review_model
from scripts.phase4_search.ucd_visual_review.app import create_app

VALIDATION_PATH = (
    PROJECT_ROOT
    / "data"
    / "literature"
    / "validation"
    / "ucd_visual_review_api_validation_v1.json"
)


def valid_review() -> dict:
    """Return a complete, valid confirmed-UCD review payload."""
    return {
        "client_revision": 0,
        "image_usability": "usable",
        "observations": {name: "no" for name in review_model.OBSERVATIONS},
        "final_decision": "include",
        "evidence_note": "validation",
        "decision_reason": "",
        "coordinate_proposal": {"response": "no_correction_needed"},
    }


def find_fixtures() -> dict[str, str]:
    """Locate one real object per required fixture from frozen tables."""
    index = pd.read_csv(UCD_VISUAL_REVIEW_BUNDLE_INDEX, dtype={"canonical_object_id": "string"})
    cutouts = pd.read_csv(
        UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST, dtype={"canonical_object_id": "string"}
    )
    placeholders = set(
        cutouts.loc[cutouts["image_content_status"].eq("viewer_placeholder_tile"), "canonical_object_id"]
    )
    fixtures = {}
    fixtures["candidate"] = index.loc[
        index["reference_cohort"].eq("saifollahi_high_probability_candidate"),
        "canonical_object_id",
    ].iloc[0]
    fixtures["excluded"] = index.loc[
        index["design_reference_membership"].eq("excluded_stripped_nucleus_or_luminous_gc"),
        "canonical_object_id",
    ].iloc[0]
    fixtures["confirmed"] = index.loc[
        index["reference_cohort"].eq("confirmed_ucd")
        & index["design_reference_membership"].eq("include"),
        "canonical_object_id",
    ].iloc[0]
    fixtures["cluster_host"] = index.loc[
        index["host_association_state"].eq("published_environment_only"),
        "canonical_object_id",
    ].iloc[0]
    placeholder_rows = index[index["canonical_object_id"].isin(placeholders)]
    fixtures["placeholder"] = (
        placeholder_rows.iloc[0]["canonical_object_id"] if len(placeholder_rows) else None
    )
    return fixtures


def main() -> None:
    """Run all API checks and write the validation artifact."""
    app = create_app()
    client = app.test_client()
    fixtures = find_fixtures()
    checks: dict[str, bool] = {}

    summary = client.get("/api/summary")
    checks["summary_200"] = summary.status_code == 200
    checks["summary_total_724"] = summary.get_json()["total"] == 724

    objects = client.get("/api/objects?cohort=saifollahi_high_probability_candidate")
    payload = objects.get_json()
    checks["objects_filter_cohort"] = objects.status_code == 200 and payload["total"] == 44

    detail = client.get(f"/api/objects/{fixtures['confirmed']}")
    document = detail.get_json()
    checks["detail_grouped"] = set(
        ["object", "host", "images", "gaia", "legacy_survey", "external_catalogs", "links"]
    ).issubset(set(document.keys()))

    compact_image = client.get(f"/api/images/{fixtures['confirmed']}/compact")
    wide_image = client.get(f"/api/images/{fixtures['confirmed']}/wide")
    checks["compact_image_200"] = compact_image.status_code == 200
    checks["wide_image_200"] = wide_image.status_code == 200

    # Valid save and optimistic concurrency.
    save = client.post(
        f"/api/objects/{fixtures['confirmed']}/reviews", json=valid_review()
    )
    checks["valid_save_201"] = save.status_code == 201
    stale = client.post(
        f"/api/objects/{fixtures['confirmed']}/reviews", json=valid_review()
    )
    checks["stale_save_409"] = stale.status_code == 409

    # Invalid four-state value.
    bad = valid_review()
    bad["observations"]["resolved"] = "maybe"
    invalid = client.post(f"/api/objects/{fixtures['confirmed']}/reviews", json=bad)
    checks["invalid_state_400"] = invalid.status_code == 400

    # Candidate cannot be included.
    candidate_include = valid_review()
    candidate_include["final_decision"] = "include"
    candidate_save = client.post(
        f"/api/objects/{fixtures['candidate']}/reviews", json=candidate_include
    )
    checks["candidate_include_400"] = candidate_save.status_code == 400

    # Excluded object cannot be included.
    excluded_save = client.post(
        f"/api/objects/{fixtures['excluded']}/reviews", json=valid_review()
    )
    checks["excluded_include_400"] = excluded_save.status_code == 400

    # Exclude/hold require a reason.
    no_reason = valid_review()
    no_reason["final_decision"] = "exclude"
    no_reason["decision_reason"] = ""
    reason_save = client.post(f"/api/objects/{fixtures['confirmed']}/reviews", json=no_reason)
    checks["exclude_requires_reason_400"] = reason_save.status_code == 400

    # Off-center requires a coordinate-proposal response.
    off_center = valid_review()
    off_center["observations"]["off_center"] = "yes"
    off_center["coordinate_proposal"] = {"response": None}
    proposal_save = client.post(
        f"/api/objects/{fixtures['confirmed']}/reviews", json=off_center
    )
    checks["off_center_requires_proposal_400"] = proposal_save.status_code == 400

    export = client.post("/api/export")
    checks["export_200"] = export.status_code == 200

    history = client.get(f"/api/objects/{fixtures['confirmed']}/history")
    checks["history_preserves_revision"] = len(history.get_json()) == 1

    checks = {name: bool(value) for name, value in checks.items()}
    validation = {
        "validation_version": "ucd_visual_review_api_validation_v1",
        "status": "passed" if all(checks.values()) else "failed",
        "fixtures": fixtures,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=2))
    if not all(checks.values()):
        raise RuntimeError(f"API validation failed: {checks}")


if __name__ == "__main__":
    main()
