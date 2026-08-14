"""Generate the versioned review exports for the UCD visual review workbench.

Exports are produced from a transactionally consistent snapshot of the review
database plus the frozen bundle index, and written as repository-ready CSV and JSON
artifacts with a manifest recording input and output digests.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from scripts.config import (
    PROJECT_ROOT,
    UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP,
    UCD_VISUAL_REVIEW_BUNDLE_INDEX,
    UCD_VISUAL_REVIEW_EXPORT_DIR,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.ucd_visual_review import review_model, schema

EXPORT_VERSION = "ucd_visual_review_export_v1"

OBSERVATION_COLUMNS = [f"obs_{name}" for name in review_model.OBSERVATIONS]


def load_index() -> list[dict]:
    """Load the bundle index rows with empty values preserved as empty strings."""
    frame = pd.read_csv(
        UCD_VISUAL_REVIEW_BUNDLE_INDEX,
        dtype={"canonical_object_id": "string"},
        keep_default_na=False,
    )
    return frame.to_dict("records")


def current_state_rows(index: list[dict], state_map: dict) -> list[dict]:
    """Build one current-review row per object."""
    rows = []
    for entry in index:
        oid = entry["canonical_object_id"]
        cohort = entry["reference_cohort"]
        review = state_map.get(oid)
        complete = bool(review and review_model.review_complete(review, cohort))
        observations = {
            f"obs_{name}": review["observations"][name] if review else ""
            for name in review_model.OBSERVATIONS
        }
        rows.append(
            {
                "canonical_object_id": oid,
                "reference_cohort": cohort,
                "original_names": entry["original_names"],
                "host_name": entry["host_name"],
                "host_association_state": entry["host_association_state"],
                "design_reference_membership": entry["design_reference_membership"],
                "adopted_distance_mpc": entry["adopted_distance_mpc"],
                "review_status": (
                    "complete" if complete else ("incomplete" if review else "not_started")
                ),
                "image_usability": review["image_usability"] if review else "",
                "final_decision": review["final_decision"] if review else "",
                "decision_reason": review["decision_reason"] if review else "",
                "evidence_note": review["evidence_note"] if review else "",
                "revision_id": review["revision_id"] if review else "",
                "utc_timestamp": review["utc_timestamp"] if review else "",
                **observations,
            }
        )
    return rows


def history_rows(index: list[dict], connection) -> list[dict]:
    """Flatten every saved revision across all objects."""
    rows = []
    for entry in index:
        for revision in schema.history(connection, entry["canonical_object_id"]):
            observations = {
                f"obs_{name}": revision["observations"][name]
                for name in review_model.OBSERVATIONS
            }
            rows.append(
                {
                    "revision_id": revision["revision_id"],
                    "canonical_object_id": revision["canonical_object_id"],
                    "utc_timestamp": revision["utc_timestamp"],
                    "prior_revision_id": revision["prior_revision_id"],
                    "client_revision": revision["client_revision"],
                    "image_usability": revision["image_usability"],
                    "final_decision": revision["final_decision"],
                    "decision_reason": revision["decision_reason"],
                    "evidence_note": revision["evidence_note"],
                    "general_comment": revision["general_comment"],
                    "coordinate_proposal_json": json.dumps(
                        revision["coordinate_proposal"], sort_keys=True
                    ),
                    **observations,
                }
            )
    return rows


def coordinate_proposal_rows(state_rows: list[dict], state_map: dict) -> list[dict]:
    """Extract objects with a recorded coordinate-correction proposal."""
    rows = []
    for row in state_rows:
        review = state_map.get(row["canonical_object_id"])
        if not review:
            continue
        proposal = review.get("coordinate_proposal") or {}
        if proposal.get("response") not in {"source_selected", "manual_ra_dec"}:
            continue
        rows.append(
            {
                "canonical_object_id": row["canonical_object_id"],
                "reference_cohort": row["reference_cohort"],
                "revision_id": review["revision_id"],
                "utc_timestamp": review["utc_timestamp"],
                "response": proposal.get("response"),
                "gaia_source_id": proposal.get("gaia_source_id"),
                "legacy_source_id": proposal.get("legacy_source_id"),
                "coordinate_reference": proposal.get("coordinate_reference"),
                "proposed_ra": proposal.get("proposed_ra"),
                "proposed_dec": proposal.get("proposed_dec"),
                "reference_quality": proposal.get("reference_quality"),
            }
        )
    return rows


def summary_counts(index: list[dict], state_rows: list[dict]) -> dict:
    """Cross-tabulate review state by cohort and evidence dimensions."""

    def by_cohort(rows: list[dict], key: str) -> dict:
        result = {}
        for row in rows:
            cohort = row["reference_cohort"]
            value = row[key] or "not_reviewed"
            result.setdefault(cohort, {}).setdefault(str(value), 0)
            result[cohort][str(value)] += 1
        return result

    observation_counts = {
        name: by_cohort(state_rows, f"obs_{name}") for name in review_model.OBSERVATIONS
    }
    return {
        "review_completion": by_cohort(state_rows, "review_status"),
        "image_usability": by_cohort(state_rows, "image_usability"),
        "final_decision": by_cohort(state_rows, "final_decision"),
        "host_association_state": by_cohort(index, "host_association_state"),
        "observations": observation_counts,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    """Write a CSV when rows exist, otherwise an empty file with a header note."""
    if rows:
        pd.DataFrame(rows).to_csv(path, index=False)
    else:
        path.write_text("", encoding="utf-8")


def generate_exports(connection) -> dict:
    """Generate all nine exports and return the manifest summary."""
    index = load_index()
    state_map = schema.review_state_map(connection)
    state_rows = current_state_rows(index, state_map)
    history = history_rows(index, connection)
    proposals = coordinate_proposal_rows(state_rows, state_map)

    included = [
        row
        for row in state_rows
        if row["reference_cohort"] == "confirmed_ucd"
        and row["review_status"] == "complete"
        and row["final_decision"] == "include"
        and row["design_reference_membership"] == "include"
    ]
    excluded = [
        row
        for row in state_rows
        if row["reference_cohort"] == "confirmed_ucd" and row["final_decision"] == "exclude"
    ]
    held = [
        row
        for row in state_rows
        if row["reference_cohort"] == "confirmed_ucd" and row["final_decision"] == "hold"
    ]
    candidate_pool = [
        row for row in state_rows if row["reference_cohort"] == "saifollahi_high_probability_candidate"
    ]

    UCD_VISUAL_REVIEW_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "review_state_v1.csv": state_rows,
        "review_history_v1.csv": history,
        "included_confirmed_ucds_v1.csv": included,
        "excluded_confirmed_ucds_v1.csv": excluded,
        "held_confirmed_ucds_v1.csv": held,
        "saifollahi_candidate_pool_v1.csv": candidate_pool,
        "coordinate_proposals_v1.csv": proposals,
    }
    for filename, rows in artifacts.items():
        write_csv(UCD_VISUAL_REVIEW_EXPORT_DIR / filename, rows)

    summary = {
        "export_version": EXPORT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "counts": {
            "total": len(state_rows),
            "reviewed": sum(1 for row in state_rows if row["review_status"] != "not_started"),
            "complete": sum(1 for row in state_rows if row["review_status"] == "complete"),
            "included_confirmed": len(included),
            "excluded_confirmed": len(excluded),
            "held_confirmed": len(held),
            "candidate_pool": len(candidate_pool),
            "coordinate_proposals": len(proposals),
        },
        "cross_tabulations": summary_counts(index, state_rows),
    }
    summary_path = UCD_VISUAL_REVIEW_EXPORT_DIR / "summary_counts_v1.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "export_version": EXPORT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "complete",
        "inputs": {
            str(UCD_VISUAL_REVIEW_BUNDLE_INDEX.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_VISUAL_REVIEW_BUNDLE_INDEX
            ),
            str(UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP.relative_to(PROJECT_ROOT)): calculate_sha256(
                UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP
            ),
        },
        "outputs": {
            filename: calculate_sha256(UCD_VISUAL_REVIEW_EXPORT_DIR / filename)
            for filename in list(artifacts) + ["summary_counts_v1.json"]
        },
        "counts": summary["counts"],
    }
    manifest_path = UCD_VISUAL_REVIEW_EXPORT_DIR / "export_manifest_v1.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return summary
