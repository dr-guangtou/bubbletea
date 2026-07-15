"""Validate canonical Gaia and Legacy Survey cross-match products."""

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.config import (
    CANONICAL_CROSSMATCH_MANIFEST,
    CANONICAL_CROSSMATCH_VALIDATION,
    CANONICAL_GAIA_CROSSMATCH_AUDIT,
    CANONICAL_GAIA_CROSSMATCH_EXPORT,
    CANONICAL_LEGACY_CROSSMATCH_AUDIT,
    CANONICAL_LEGACY_CROSSMATCH_EXPORT,
    LITERATURE_REFERENCE_DB_V2,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256


def require(condition: bool, message: str, checks: list[str]) -> None:
    """Record a passed invariant or raise a validation failure."""
    if not condition:
        raise RuntimeError(message)
    checks.append(message)


def load_database_counts(path: Path) -> dict[str, int]:
    """Load canonical target and Gaia-association counts read-only."""
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        row = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM canonical_objects
                    WHERE adopted_ra IS NOT NULL AND adopted_dec IS NOT NULL),
                (SELECT COUNT(DISTINCT a.canonical_object_id)
                    FROM object_record_associations a
                    JOIN literature_records r USING (record_id)
                    WHERE r.gaia_dr3_id IS NOT NULL),
                (SELECT COUNT(DISTINCT r.gaia_dr3_id)
                    FROM object_record_associations a
                    JOIN literature_records r USING (record_id)
                    WHERE r.gaia_dr3_id IS NOT NULL)
            """
        ).fetchone()
    finally:
        connection.close()
    return {
        "canonical_target_count": int(row[0]),
        "canonical_gaia_association_count": int(row[1]),
        "distinct_gaia_source_count": int(row[2]),
    }


def validate_manifest_files(
    manifest: dict[str, Any], checks: list[str]
) -> dict[str, dict[str, Any]]:
    """Require every manifest product digest and row count to match disk."""
    summaries = {}
    entries = [
        manifest["gaia"]["matched_export"],
        manifest["gaia"]["target_audit"],
        manifest["legacy_survey"]["matched_export"],
        manifest["legacy_survey"]["target_audit"],
        *manifest["superseded_historical_exports"],
    ]
    for entry in entries:
        path = Path(entry["path"])
        require(path.is_file(), f"Manifest file exists: {path}", checks)
        require(
            calculate_sha256(path) == entry["sha256"],
            f"Manifest digest matches: {path}",
            checks,
        )
        row_count = len(pd.read_csv(path))
        require(
            row_count == entry["row_count"],
            f"Manifest row count matches: {path}",
            checks,
        )
        summaries[path.as_posix()] = {"row_count": row_count, "sha256": entry["sha256"]}
    return summaries


def validate_candidate_json(frame: pd.DataFrame, checks: list[str]) -> None:
    """Require candidate JSON to reproduce every recorded in-radius count."""
    for row in frame.itertuples(index=False):
        candidates = json.loads(row.candidate_matches_json)
        if len(candidates) != row.match_count_within_radius:
            raise RuntimeError(f"Candidate JSON count differs for {row.canonical_object_id}")
        distances = [candidate["dist_arcsec"] for candidate in candidates]
        if distances != sorted(distances):
            raise RuntimeError(
                f"Candidate JSON order is not deterministic for {row.canonical_object_id}"
            )
    checks.append("Legacy candidate JSON counts and distance order match")


def main() -> None:
    """Run all product invariants and write a concise validation artifact."""
    checks = []
    manifest = json.loads(CANONICAL_CROSSMATCH_MANIFEST.read_text(encoding="utf-8"))
    database_counts = load_database_counts(LITERATURE_REFERENCE_DB_V2)
    require(manifest["schema_version"] == 1, "Manifest schema version is 1", checks)
    require(not manifest["limited_smoke_run"], "Manifest represents the full run", checks)
    require(
        manifest["command"].endswith("synchronize_crossmatch_products.py"),
        "Manifest records the reproducible command",
        checks,
    )
    query_batches = [
        *manifest["gaia"]["query_batches"],
        *manifest["legacy_survey"]["query_batches"],
    ]
    require(
        all(len(batch["query_sha256"]) == 64 for batch in query_batches),
        "Every remote query batch has a SHA-256 digest",
        checks,
    )
    require(
        manifest["reference_database"]["sha256"] == calculate_sha256(LITERATURE_REFERENCE_DB_V2),
        "Reference database digest matches the retrieval input",
        checks,
    )
    require(
        manifest["reference_database"]["canonical_target_count"]
        == database_counts["canonical_target_count"],
        "Manifest target count matches the canonical database",
        checks,
    )
    file_summaries = validate_manifest_files(manifest, checks)

    gaia = pd.read_csv(CANONICAL_GAIA_CROSSMATCH_EXPORT, dtype={"gaia_dr3_id": str})
    gaia_audit = pd.read_csv(CANONICAL_GAIA_CROSSMATCH_AUDIT)
    legacy = pd.read_csv(CANONICAL_LEGACY_CROSSMATCH_EXPORT)
    legacy_audit = pd.read_csv(CANONICAL_LEGACY_CROSSMATCH_AUDIT)

    require(
        len(gaia) == database_counts["canonical_gaia_association_count"],
        "Gaia export count matches canonical database associations",
        checks,
    )
    require(
        gaia["gaia_dr3_id"].nunique() == database_counts["distinct_gaia_source_count"],
        "Gaia unique-source count matches the canonical database",
        checks,
    )
    require(gaia["canonical_object_id"].is_unique, "Gaia canonical IDs are unique", checks)
    require(
        gaia["within_query_radius"].all(),
        "Every canonical Gaia association is within the diagnostic radius",
        checks,
    )
    require(
        len(gaia_audit) == database_counts["canonical_target_count"],
        "Gaia audit contains every canonical target",
        checks,
    )
    gaia_status_counts = gaia_audit["match_status"].value_counts().to_dict()
    require(
        gaia_status_counts.get("matched_by_source_id", 0) == len(gaia),
        "Gaia matched audit count equals export count",
        checks,
    )

    require(
        len(legacy_audit) == database_counts["canonical_target_count"],
        "Legacy audit contains every canonical target",
        checks,
    )
    require(
        legacy["canonical_object_id"].is_unique,
        "Legacy export has one selected row per canonical target",
        checks,
    )
    require(
        legacy["dist_arcsec"].le(manifest["legacy_survey"]["match_radius_arcsec"]).all(),
        "Every Legacy match is within the enforced radius",
        checks,
    )
    legacy_status_counts = legacy_audit["match_status"].value_counts().to_dict()
    require(
        legacy_status_counts.get("matched", 0) == len(legacy),
        "Legacy matched audit count equals export count",
        checks,
    )
    validate_candidate_json(legacy, checks)

    shared_gaia_counts = gaia["gaia_dr3_id"].value_counts()
    shared_legacy_counts = legacy["ls_id"].astype(str).value_counts()
    expected_legacy_counts = legacy["ls_id"].astype(str).map(shared_legacy_counts)
    require(
        legacy["selected_source_canonical_count"].eq(expected_legacy_counts).all(),
        "Legacy shared-source counts reproduce selected source usage",
        checks,
    )
    require(
        legacy["shared_selected_source"].eq(expected_legacy_counts > 1).all(),
        "Legacy shared-source flags reproduce selected source usage",
        checks,
    )
    output = {
        "status": "passed",
        "checks": checks,
        "database_counts": database_counts,
        "gaia": {
            "export_row_count": len(gaia),
            "audit_status_counts": gaia_status_counts,
            "maximum_distance_arcsec": float(gaia["dist_arcsec"].max()),
            "shared_source_count": int((shared_gaia_counts > 1).sum()),
            "maximum_canonicals_per_source": int(shared_gaia_counts.max()),
        },
        "legacy_survey": {
            "export_row_count": len(legacy),
            "audit_status_counts": legacy_status_counts,
            "ambiguous_target_count": int(legacy["ambiguous_match"].sum()),
            "candidate_count_distribution": {
                str(key): value
                for key, value in sorted(
                    Counter(legacy["match_count_within_radius"].astype(int)).items()
                )
            },
            "maximum_distance_arcsec": float(legacy["dist_arcsec"].max()),
            "shared_source_count": int((shared_legacy_counts > 1).sum()),
            "maximum_canonicals_per_source": int(shared_legacy_counts.max()),
        },
        "validated_files": file_summaries,
    }
    CANONICAL_CROSSMATCH_VALIDATION.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
