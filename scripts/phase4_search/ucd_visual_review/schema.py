"""Append-only review storage for the UCD visual review workbench."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_VERSION = "review_schema_v1"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_object_id TEXT NOT NULL,
    bundle_version TEXT NOT NULL,
    bundle_digest TEXT NOT NULL,
    utc_timestamp TEXT NOT NULL,
    prior_revision_id INTEGER,
    client_revision INTEGER NOT NULL,
    image_usability TEXT NOT NULL,
    resolved TEXT NOT NULL,
    off_center TEXT NOT NULL,
    close_to_host_light TEXT NOT NULL,
    too_faint_to_judge TEXT NOT NULL,
    blend_or_nearby_source TEXT NOT NULL,
    image_artifact TEXT NOT NULL,
    star_forming_or_young_cluster_appearance TEXT NOT NULL,
    final_decision TEXT NOT NULL,
    evidence_note TEXT,
    general_comment TEXT,
    decision_reason TEXT,
    gaia_source_id TEXT,
    legacy_source_id TEXT,
    reference_quality TEXT,
    coordinate_proposal_json TEXT,
    FOREIGN KEY (prior_revision_id) REFERENCES review_revisions(revision_id)
);

CREATE INDEX IF NOT EXISTS idx_revisions_object
    ON review_revisions(canonical_object_id, revision_id);
"""

_OBSERVATION_COLUMNS = {
    "resolved",
    "off_center",
    "close_to_host_light",
    "too_faint_to_judge",
    "blend_or_nearby_source",
    "image_artifact",
    "star_forming_or_young_cluster_appearance",
}


def connect(database_path: Path) -> sqlite3.Connection:
    """Open a review database and apply the schema."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(_SCHEMA)
    connection.execute(
        "INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', ?)",
        (SCHEMA_VERSION,),
    )
    connection.commit()
    return connection


def latest_revision_id(connection: sqlite3.Connection, canonical_object_id: str) -> int:
    """Return the newest revision identifier for one object, or 0 if none."""
    row = connection.execute(
        "SELECT MAX(revision_id) AS revision_id FROM review_revisions "
        "WHERE canonical_object_id = ?",
        (canonical_object_id,),
    ).fetchone()
    return int(row["revision_id"]) if row and row["revision_id"] is not None else 0


def save_revision(
    connection: sqlite3.Connection,
    canonical_object_id: str,
    bundle_version: str,
    bundle_digest: str,
    payload: dict,
) -> tuple[int, str]:
    """Append one review revision and return (revision_id, conflict_message).

    A non-empty conflict message means the submitted parent revision was stale and
    the save was rejected without writing anything.
    """
    current = latest_revision_id(connection, canonical_object_id)
    client_revision = int(payload.get("client_revision") or 0)
    if client_revision != current:
        return 0, (
            f"stale_revision: submitted parent revision {client_revision} but the "
            f"current revision is {current}"
        )

    observations = payload.get("observations") or {}
    coordinate_proposal = payload.get("coordinate_proposal") or {}
    cursor = connection.execute(
        """
        INSERT INTO review_revisions (
            canonical_object_id, bundle_version, bundle_digest, utc_timestamp,
            prior_revision_id, client_revision, image_usability,
            resolved, off_center, close_to_host_light, too_faint_to_judge,
            blend_or_nearby_source, image_artifact,
            star_forming_or_young_cluster_appearance, final_decision,
            evidence_note, general_comment, decision_reason,
            gaia_source_id, legacy_source_id, reference_quality,
            coordinate_proposal_json
        ) VALUES (
            :canonical_object_id, :bundle_version, :bundle_digest, :utc_timestamp,
            :prior_revision_id, :client_revision, :image_usability,
            :resolved, :off_center, :close_to_host_light, :too_faint_to_judge,
            :blend_or_nearby_source, :image_artifact,
            :star_forming_or_young_cluster_appearance, :final_decision,
            :evidence_note, :general_comment, :decision_reason,
            :gaia_source_id, :legacy_source_id, :reference_quality,
            :coordinate_proposal_json
        )
        """,
        {
            "canonical_object_id": canonical_object_id,
            "bundle_version": bundle_version,
            "bundle_digest": bundle_digest,
            "utc_timestamp": datetime.now(UTC).isoformat(),
            "prior_revision_id": current or None,
            "client_revision": client_revision,
            "image_usability": payload.get("image_usability"),
            **{
                name: observations.get(name)
                for name in sorted(_OBSERVATION_COLUMNS)
            },
            "final_decision": payload.get("final_decision"),
            "evidence_note": payload.get("evidence_note"),
            "general_comment": payload.get("general_comment"),
            "decision_reason": payload.get("decision_reason"),
            "gaia_source_id": payload.get("gaia_source_id"),
            "legacy_source_id": payload.get("legacy_source_id"),
            "reference_quality": payload.get("reference_quality"),
            "coordinate_proposal_json": json.dumps(coordinate_proposal, sort_keys=True),
        },
    )
    connection.commit()
    return int(cursor.lastrowid), ""


def revision_to_dict(row: sqlite3.Row) -> dict:
    """Convert a revision row into the client-facing review payload."""
    observations = {
        name: row[name] for name in sorted(_OBSERVATION_COLUMNS)
    }
    return {
        "revision_id": row["revision_id"],
        "canonical_object_id": row["canonical_object_id"],
        "utc_timestamp": row["utc_timestamp"],
        "prior_revision_id": row["prior_revision_id"],
        "client_revision": row["client_revision"],
        "image_usability": row["image_usability"],
        "observations": observations,
        "final_decision": row["final_decision"],
        "evidence_note": row["evidence_note"],
        "general_comment": row["general_comment"],
        "decision_reason": row["decision_reason"],
        "gaia_source_id": row["gaia_source_id"],
        "legacy_source_id": row["legacy_source_id"],
        "reference_quality": row["reference_quality"],
        "coordinate_proposal": json.loads(row["coordinate_proposal_json"] or "{}"),
    }


def current_review(connection: sqlite3.Connection, canonical_object_id: str) -> dict | None:
    """Return the current review payload for one object, or None."""
    row = connection.execute(
        "SELECT * FROM review_revisions WHERE canonical_object_id = ? "
        "ORDER BY revision_id DESC LIMIT 1",
        (canonical_object_id,),
    ).fetchone()
    return revision_to_dict(row) if row else None


def history(connection: sqlite3.Connection, canonical_object_id: str) -> list[dict]:
    """Return every revision for one object, oldest first."""
    rows = connection.execute(
        "SELECT * FROM review_revisions WHERE canonical_object_id = ? "
        "ORDER BY revision_id ASC",
        (canonical_object_id,),
    ).fetchall()
    return [revision_to_dict(row) for row in rows]


def review_state_map(connection: sqlite3.Connection) -> dict[str, dict]:
    """Return the current review payload for every reviewed object."""
    rows = connection.execute(
        "SELECT * FROM review_revisions WHERE revision_id IN ("
        "SELECT MAX(revision_id) FROM review_revisions GROUP BY canonical_object_id"
        ")"
    ).fetchall()
    return {row["canonical_object_id"]: revision_to_dict(row) for row in rows}
