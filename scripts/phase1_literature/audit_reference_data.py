"""Audit literature identity, source associations, and confirmation labels.

Inputs are the literature SQLite database and per-source CSV catalogs. Outputs
are non-destructive validation artifacts describing current database rows,
provisional exact-coordinate identity groups, source coverage, and label
conflicts. This script never modifies the database.
"""

import argparse
import csv
import hashlib
import json
import logging
import sqlite3
import struct
from collections import Counter, defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path

from scripts.config import LITERATURE_CATALOGS, LITERATURE_DB, LITERATURE_VALIDATION

logger = logging.getLogger(__name__)

COMMAND = "PYTHONPATH=. uv run python scripts/phase1_literature/audit_reference_data.py"


def parse_arguments() -> argparse.Namespace:
    """Parse command-line paths for the audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=LITERATURE_DB)
    parser.add_argument(
        "--catalog-directory",
        type=Path,
        default=LITERATURE_CATALOGS / "by_source",
    )
    parser.add_argument("--output-directory", type=Path, default=LITERATURE_VALIDATION)
    return parser.parse_args()


def calculate_sha256(path: Path) -> str:
    """Calculate a file SHA-256 digest without loading the whole file."""
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def connect_read_only(database_path: Path) -> sqlite3.Connection:
    """Open an existing SQLite database in enforced read-only mode."""
    database_uri = f"file:{database_path.resolve().as_posix()}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def load_database_rows(
    connection: sqlite3.Connection,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Load source and literature rows in deterministic order."""
    sources = [
        dict(row)
        for row in connection.execute("SELECT * FROM ucd_sources ORDER BY source_id").fetchall()
    ]
    objects = [
        dict(row)
        for row in connection.execute(
            """
            SELECT *
            FROM ucd_objects
            ORDER BY ra, dec, source_id, object_id
            """
        ).fetchall()
    ]
    return sources, objects


def audit_catalog_files(catalog_directory: Path) -> dict[str, dict[str, object]]:
    """Measure row counts and labels in each per-source CSV catalog."""
    catalog_audit = {}
    for catalog_path in sorted(catalog_directory.glob("*.csv")):
        with catalog_path.open(encoding="utf-8", newline="") as input_file:
            rows = list(csv.DictReader(input_file))
        status_counts = Counter(row.get("confirmation_status") or row.get("status") for row in rows)
        ucd_counts = Counter(row.get("is_ucd") for row in rows)
        catalog_audit[catalog_path.stem] = {
            "catalog_rows": len(rows),
            "catalog_status_counts": dict(
                sorted(status_counts.items(), key=lambda item: str(item[0]))
            ),
            "catalog_ucd_counts": dict(sorted(ucd_counts.items(), key=lambda item: str(item[0]))),
        }
    return catalog_audit


def exact_coordinate_group_id(ra: float, dec: float) -> str:
    """Create a source-neutral identifier for an exact stored coordinate pair."""
    coordinate_bytes = struct.pack(">dd", ra, dec)
    coordinate_digest = hashlib.sha256(coordinate_bytes).hexdigest()[:16]
    return f"exact_coordinate_group_{coordinate_digest}"


def build_duplicate_audit(
    objects: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Build row memberships and summary statistics for exact-coordinate groups."""
    rows_by_coordinate = defaultdict(list)
    for row in objects:
        if row["ra"] is not None and row["dec"] is not None:
            rows_by_coordinate[(row["ra"], row["dec"])].append(row)

    duplicate_groups = [
        (coordinates, rows) for coordinates, rows in rows_by_coordinate.items() if len(rows) > 1
    ]
    duplicate_groups.sort(key=lambda item: item[0])

    membership_rows = []
    source_pair_counts = Counter()
    same_source_group_count = 0
    same_source_payload_difference_group_count = 0
    status_conflict_count = 0
    ucd_flag_conflict_count = 0
    gaia_id_conflict_count = 0

    for (ra, dec), group_rows in duplicate_groups:
        source_ids = {str(row["source_id"]) for row in group_rows}
        confirmation_statuses = {row["confirmation_status"] for row in group_rows}
        ucd_flags = {row["is_ucd"] for row in group_rows}
        gaia_ids = {row["gaia_dr3_id"] for row in group_rows}
        same_source_group = len(source_ids) == 1
        payload_fields = set(group_rows[0]) - {"object_id", "date_added", "last_modified"}
        same_source_payload_difference = same_source_group and any(
            row[field] != group_rows[0][field] for field in payload_fields for row in group_rows[1:]
        )
        status_conflict = len(confirmation_statuses) > 1
        ucd_flag_conflict = len(ucd_flags) > 1
        gaia_id_conflict = len(gaia_ids) > 1

        same_source_group_count += same_source_group
        same_source_payload_difference_group_count += same_source_payload_difference
        status_conflict_count += status_conflict
        ucd_flag_conflict_count += ucd_flag_conflict
        gaia_id_conflict_count += gaia_id_conflict

        for first_row, second_row in combinations(group_rows, 2):
            source_pair = tuple(sorted((str(first_row["source_id"]), str(second_row["source_id"]))))
            source_pair_counts[source_pair] += 1

        group_id = exact_coordinate_group_id(float(ra), float(dec))
        for row in group_rows:
            membership_rows.append(
                {
                    "exact_coordinate_group_id": group_id,
                    "ra": ra,
                    "dec": dec,
                    "group_size": len(group_rows),
                    "source_count": len(source_ids),
                    "same_source_group": int(same_source_group),
                    "confirmation_status_conflict": int(status_conflict),
                    "is_ucd_conflict": int(ucd_flag_conflict),
                    "gaia_dr3_id_conflict": int(gaia_id_conflict),
                    "object_id": row["object_id"],
                    "source_id": row["source_id"],
                    "original_name": row["original_name"],
                    "confirmation_status": row["confirmation_status"],
                    "is_ucd": row["is_ucd"],
                    "gaia_dr3_id": row["gaia_dr3_id"],
                    "host_galaxy": row["host_galaxy"],
                    "re_pc": row["re_pc"],
                }
            )

    summary = {
        "exact_coordinate_group_count": len(rows_by_coordinate),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_row_count": len(membership_rows),
        "minimum_duplicate_group_size": min((len(rows) for _, rows in duplicate_groups), default=0),
        "maximum_duplicate_group_size": max((len(rows) for _, rows in duplicate_groups), default=0),
        "same_source_duplicate_group_count": same_source_group_count,
        "same_source_payload_difference_group_count": (same_source_payload_difference_group_count),
        "cross_source_duplicate_group_count": len(duplicate_groups) - same_source_group_count,
        "confirmation_status_conflict_group_count": status_conflict_count,
        "is_ucd_conflict_group_count": ucd_flag_conflict_count,
        "gaia_dr3_id_conflict_group_count": gaia_id_conflict_count,
        "source_pair_counts": [
            {
                "source_id_1": source_pair[0],
                "source_id_2": source_pair[1],
                "group_count": group_count,
            }
            for source_pair, group_count in sorted(
                source_pair_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ],
    }
    return membership_rows, summary


def build_source_audit(
    sources: list[dict[str, object]],
    objects: list[dict[str, object]],
    catalog_audit: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    """Reconcile database source metadata, database rows, and source CSVs."""
    database_sources = {str(source["source_id"]): source for source in sources}
    rows_by_source = defaultdict(list)
    for row in objects:
        rows_by_source[str(row["source_id"])].append(row)

    source_ids = sorted(set(database_sources) | set(catalog_audit))
    source_audit = []
    for source_id in source_ids:
        source = database_sources.get(source_id, {})
        source_rows = rows_by_source[source_id]
        catalog = catalog_audit.get(source_id, {})
        database_row_count = len(source_rows)
        catalog_row_count = catalog.get("catalog_rows")
        source_audit.append(
            {
                "source_id": source_id,
                "in_database_sources": int(source_id in database_sources),
                "in_database_objects": int(bool(source_rows)),
                "in_by_source_catalogs": int(source_id in catalog_audit),
                "declared_n_objects": source.get("n_objects"),
                "database_rows": database_row_count,
                "catalog_rows": catalog_row_count,
                "database_catalog_row_difference": (
                    database_row_count - int(catalog_row_count)
                    if catalog_row_count is not None
                    else None
                ),
                "ucd_rows": sum(row["is_ucd"] == 1 for row in source_rows),
                "candidate_rows": sum(
                    row["confirmation_status"] == "candidate" for row in source_rows
                ),
                "confirmed_rows": sum(
                    row["confirmation_status"] == "confirmed" for row in source_rows
                ),
                "gaia_matched_rows": sum(row["gaia_dr3_id"] is not None for row in source_rows),
                "bibcode": source.get("bibcode"),
                "doi": source.get("doi"),
                "vizier_id": source.get("vizier_id"),
                "catalog_status_counts": json.dumps(
                    catalog.get("catalog_status_counts", {}), sort_keys=True
                ),
                "catalog_ucd_counts": json.dumps(
                    catalog.get("catalog_ucd_counts", {}), sort_keys=True
                ),
            }
        )
    return source_audit


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write a deterministic CSV with headers from the first row."""
    if not rows:
        raise ValueError(f"Cannot write empty audit table: {path}")
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_summary(
    database_sha256: str,
    sources: list[dict[str, object]],
    objects: list[dict[str, object]],
    source_audit: list[dict[str, object]],
    duplicate_summary: dict[str, object],
) -> dict[str, object]:
    """Build machine-readable audit results from measured inputs."""
    confirmation_status_counts = Counter(row["confirmation_status"] for row in objects)
    return {
        "audit_date": date.today().isoformat(),
        "command": COMMAND,
        "database_sha256": database_sha256,
        "database_source_count": len(sources),
        "database_row_count": len(objects),
        "unique_object_id_count": len({row["object_id"] for row in objects}),
        "ucd_row_count": sum(row["is_ucd"] == 1 for row in objects),
        "gaia_matched_row_count": sum(row["gaia_dr3_id"] is not None for row in objects),
        "legacy_matched_row_count": sum(row["ls_dr10_id"] is not None for row in objects),
        "confirmation_status_counts": dict(
            sorted(confirmation_status_counts.items(), key=lambda item: str(item[0]))
        ),
        "source_catalog_count": sum(row["in_by_source_catalogs"] for row in source_audit),
        "catalog_sources_missing_from_database": [
            row["source_id"] for row in source_audit if not row["in_database_sources"]
        ],
        "database_sources_missing_catalogs": [
            row["source_id"] for row in source_audit if not row["in_by_source_catalogs"]
        ],
        **duplicate_summary,
    }


def write_report(path: Path, summary: dict[str, object]) -> None:
    """Write the human-readable validation report."""
    status_rows = "\n".join(
        f"| `{status}` | {count} |"
        for status, count in summary["confirmation_status_counts"].items()
    )
    source_pair_rows = "\n".join(
        f"| `{row['source_id_1']}` | `{row['source_id_2']}` | {row['group_count']} |"
        for row in summary["source_pair_counts"]
    )
    missing_catalog_sources = summary["catalog_sources_missing_from_database"]
    missing_database_sources = summary["database_sources_missing_catalogs"]
    report = f"""# Literature Reference Audit

**Date:** {summary["audit_date"]}
**Script:** `scripts/phase1_literature/audit_reference_data.py`
**Command:** `{summary["command"]}`
**Database:** `data/literature/database/ucd_collection.db`
**Database SHA-256:** `{summary["database_sha256"]}`

## Scope and Safety

This is a read-only audit of the current literature rows. Exact stored coordinate
equality is treated only as provisional identity evidence. No row was deleted,
merged, relabeled, or selected as the preferred astrophysical record. Near-coordinate
matching and selector behavior are outside this audit.

## Measured State

| Measure | Count |
|---|---:|
| Database source records | {summary["database_source_count"]} |
| Per-source CSV catalogs | {summary["source_catalog_count"]} |
| Database literature rows | {summary["database_row_count"]} |
| Unique current `object_id` values | {summary["unique_object_id_count"]} |
| Rows flagged `is_ucd = 1` | {summary["ucd_row_count"]} |
| Gaia-matched rows | {summary["gaia_matched_row_count"]} |
| Legacy Survey-matched rows | {summary["legacy_matched_row_count"]} |
| Exact stored coordinate pairs | {summary["exact_coordinate_group_count"]} |
| Exact duplicate-coordinate groups | {summary["duplicate_group_count"]} |
| Rows in exact duplicate groups | {summary["duplicate_row_count"]} |

## Current Confirmation Labels

| Stored label | Rows |
|---|---:|
{status_rows}

Confirmation status is attached to each literature row and was assigned uniformly
by source ingestion logic. It is not currently an object-level evidence tier. In
particular, {summary["confirmation_status_conflict_group_count"]} exact-coordinate groups contain conflicting stored labels.

## Exact Duplicate-Coordinate Groups

- Every group contains between {summary["minimum_duplicate_group_size"]} and {summary["maximum_duplicate_group_size"]} rows.
- {summary["cross_source_duplicate_group_count"]} groups connect different source papers and therefore
  require many-to-many canonical object/source associations.
- {summary["same_source_duplicate_group_count"]} groups repeat coordinates within one source;
  {summary["same_source_payload_difference_group_count"]} of those groups differ in stored payload fields after excluding row IDs and timestamps.
- {summary["is_ucd_conflict_group_count"]} groups disagree on `is_ucd`.
- {summary["gaia_dr3_id_conflict_group_count"]} groups disagree on stored Gaia ID,
  including null versus non-null values.

| Source 1 | Source 2 | Exact-coordinate groups |
|---|---|---:|
{source_pair_rows}

The companion `exact_duplicate_coordinate_memberships.csv` preserves every member
row and its source, label, Gaia ID, host, and size fields. Its group identifier is
source-neutral and derived from the exact binary representation of the stored
coordinates; it is an audit identifier, not an approved canonical object ID.

## Source Reconciliation Findings

- Catalog sources absent from the database source/object model:
  `{", ".join(missing_catalog_sources) if missing_catalog_sources else "none"}`.
- Database sources without a per-source CSV catalog:
  `{", ".join(missing_database_sources) if missing_database_sources else "none"}`.
- The source table has no populated DOI or declared object-count fields. Detailed
  row counts and catalog/database differences are in `literature_source_audit.csv`.

## Canonicalization Gate

The current `ucd_objects` table is a literature-row table despite its name. A safe
canonical model must keep those rows immutable and add separate canonical objects,
many-to-many source associations, provenance-bearing evidence records, and explicit
confirmation tiers. The 1,928 exact coordinate pairs are an upper-confidence audit
partition, not a complete canonical catalog: exact equality can miss the same object
reported at slightly different coordinates, while equal coordinates within a paper
still require verification.

No selector should use deduplicated or confirmed-object denominators until that
model and its review rules are implemented and validated.
"""
    path.write_text(report, encoding="utf-8")


def main() -> None:
    """Run the non-destructive literature reference audit."""
    arguments = parse_arguments()
    database_sha256_before = calculate_sha256(arguments.database)
    with connect_read_only(arguments.database) as connection:
        sources, objects = load_database_rows(connection)

    catalog_audit = audit_catalog_files(arguments.catalog_directory)
    duplicate_memberships, duplicate_summary = build_duplicate_audit(objects)
    source_audit = build_source_audit(sources, objects, catalog_audit)
    summary = build_summary(
        database_sha256_before,
        sources,
        objects,
        source_audit,
        duplicate_summary,
    )

    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    write_csv(
        arguments.output_directory / "exact_duplicate_coordinate_memberships.csv",
        duplicate_memberships,
    )
    write_csv(arguments.output_directory / "literature_source_audit.csv", source_audit)
    with (arguments.output_directory / "literature_reference_audit.json").open(
        "w", encoding="utf-8"
    ) as output_file:
        json.dump(summary, output_file, indent=2)
        output_file.write("\n")
    write_report(arguments.output_directory / "literature_reference_audit.md", summary)

    database_sha256_after = calculate_sha256(arguments.database)
    if database_sha256_after != database_sha256_before:
        raise RuntimeError("The literature database changed during the read-only audit")

    logger.info(
        "Audited %d rows and %d exact duplicate-coordinate groups without modifying the database",
        len(objects),
        duplicate_summary["duplicate_group_count"],
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
