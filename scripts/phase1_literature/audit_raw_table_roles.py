"""Audit proposed roles and current v2 coverage of retrieved literature tables."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from astropy.io import ascii

from scripts.config import (
    LITERATURE_CATALOGS,
    LITERATURE_REFERENCE_DB_V2,
    LITERATURE_SOURCES,
    LITERATURE_VALIDATION,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import connect_read_only

ROLE_MANIFEST = LITERATURE_SOURCES / "raw_table_roles.json"


def parse_arguments() -> argparse.Namespace:
    """Parse input and output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role-manifest", type=Path, default=ROLE_MANIFEST)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--output-directory", type=Path, default=LITERATURE_VALIDATION)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    """Load one JSON document."""
    with path.open(encoding="utf-8") as input_file:
        return json.load(input_file)


def parse_fahrion_coordinates(path: Path) -> tuple[int, list[tuple[float, float]], list[str]]:
    """Parse coordinates and coordinate-null names from the fixed-width Fahrion table."""
    lines = path.read_text(encoding="utf-8").splitlines()
    coordinates = []
    coordinate_null_names = []
    for line in lines:
        try:
            ra = (float(line[36:38]) + float(line[39:41]) / 60 + float(line[42:47]) / 3600) * 15
            sign = -1 if line[48] == "-" else 1
            dec = sign * (float(line[49:51]) + float(line[52:54]) / 60 + float(line[55:60]) / 3600)
            coordinates.append((ra, dec))
        except ValueError:
            coordinate_null_names.append(line[:19].strip())
    return len(lines), coordinates, coordinate_null_names


def table_coordinates(table: object) -> list[tuple[float, float]]:
    """Extract decimal coordinates from a CDS table when present."""
    if "RAdeg" in table.colnames:
        return list(zip(map(float, table["RAdeg"]), map(float, table["DEdeg"]), strict=True))
    required_columns = {"RAh", "RAm", "RAs", "DE-", "DEd", "DEm", "DEs"}
    if not required_columns.issubset(table.colnames):
        return []
    ra = (
        np.asarray(table["RAh"], dtype=float)
        + np.asarray(table["RAm"], dtype=float) / 60
        + np.asarray(table["RAs"], dtype=float) / 3600
    ) * 15
    sign = np.where(np.asarray(table["DE-"]).astype(str) == "-", -1, 1)
    dec = sign * (
        np.asarray(table["DEd"], dtype=float)
        + np.asarray(table["DEm"], dtype=float) / 60
        + np.asarray(table["DEs"], dtype=float) / 3600
    )
    return list(zip(map(float, ra), map(float, dec), strict=True))


def inspect_table(reference_folder: str, file_name: str) -> dict[str, object]:
    """Measure rows and coordinate multiplicity for one retrieved table."""
    folder = PROJECT_ROOT / "reference" / reference_folder
    table_path = folder / file_name
    if file_name == "tableb1.dat" and reference_folder == "fahrion2019":
        row_count, coordinates, coordinate_null_names = parse_fahrion_coordinates(table_path)
    else:
        try:
            table = ascii.read(table_path, readme=folder / "ReadMe.txt", format="cds")
            row_count = len(table)
            coordinates = table_coordinates(table)
        except ValueError:
            row_count = len(table_path.read_text(encoding="utf-8").splitlines())
            coordinates = []
        coordinate_null_names = []
    coordinate_counts = Counter(coordinates)
    return {
        "raw_row_count": row_count,
        "coordinate_row_count": len(coordinates),
        "unique_coordinate_count": len(coordinate_counts),
        "duplicate_coordinate_row_count": sum(
            count for count in coordinate_counts.values() if count > 1
        ),
        "coordinate_null_names": ";".join(coordinate_null_names),
    }


def processed_row_counts() -> dict[str, int]:
    """Count legacy processed CSV rows by source identifier."""
    counts = {}
    for path in sorted((LITERATURE_CATALOGS / "by_source").glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as input_file:
            counts[path.stem] = sum(1 for _ in csv.DictReader(input_file))
    return counts


def publication_record_counts(database: Path) -> dict[str, int]:
    """Count current v2 literature records by corrected bibcode."""
    query = """
        SELECT publications.bibcode, COUNT(*)
        FROM literature_records
        JOIN datasets USING (dataset_id)
        JOIN publications USING (publication_id)
        GROUP BY publications.bibcode
    """
    with connect_read_only(database) as connection:
        return {str(row[0]): int(row[1]) for row in connection.execute(query)}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write measured table-role rows."""
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, rows: list[dict[str, object]], review_status: str) -> None:
    """Write the table-role review artifact."""
    status_counts = Counter(str(row["current_v2_status"]) for row in rows)
    role_counts = Counter(str(row["proposed_role"]) for row in rows)
    absent_primary_rows = sum(
        int(row["raw_row_count"])
        for row in rows
        if row["current_v2_status"] == "not_ingested"
        and row["proposed_role"] in {"primary_records", "primary_reference_records"}
    )
    selection_pool_rows = sum(
        int(row["raw_row_count"])
        for row in rows
        if row["proposed_role"] == "selection_pool_records"
    )
    status_lines = "\n".join(
        f"| `{key}` | {value} |" for key, value in sorted(status_counts.items())
    )
    role_lines = "\n".join(f"| `{key}` | {value} |" for key, value in sorted(role_counts.items()))
    report = f"""# Raw Literature Table Role Audit

**Review status:** `{review_status}`

This audit measures retrieved tables and proposes roles. It does not change v2
membership, object identity, evidence approval, or confirmation state.

## Proposed Roles

| Role | Tables |
|---|---:|
{role_lines}

## Current v2 Coverage

| Status | Tables |
|---|---:|
{status_lines}

The proposed primary/reference tables currently absent from direct source-table
membership contain {absent_primary_rows} measured rows. This does not imply that
every object lacks a canonical counterpart; row-level overlaps are reported in
`pending_source_row_review.md`. The approved, separate Saifollahi selection pool
contains {selection_pool_rows} measured rows and is excluded from the positive
reference denominator.

The detailed CSV records raw row counts, coordinate coverage, multiplicity, current
publication-level v2 counts, and the four coordinate-null Fahrion row names. The
manifest review status governs which proposed roles may be implemented.
"""
    path.write_text(report, encoding="utf-8")


def main() -> None:
    """Generate deterministic raw table-role review artifacts."""
    arguments = parse_arguments()
    manifest = load_json(arguments.role_manifest)
    processed_counts = processed_row_counts()
    v2_counts = publication_record_counts(arguments.reference_database)
    rows = []
    for entry in manifest["tables"]:
        measurement = inspect_table(str(entry["reference_folder"]), str(entry["file_name"]))
        legacy_identifier = str(entry["bibcode"])
        if legacy_identifier == "2019A&A...625A..50F":
            legacy_identifier = "2019A&A...625A..50V"
        elif legacy_identifier == "2020ApJ...899..140V":
            legacy_identifier = "2020ApJ...899..140W"
        rows.append(
            {
                **entry,
                **measurement,
                "legacy_processed_row_count": processed_counts.get(legacy_identifier, 0),
                "current_v2_publication_record_count": v2_counts.get(str(entry["bibcode"]), 0),
            }
        )
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    write_csv(arguments.output_directory / "raw_table_role_audit.csv", rows)
    write_report(
        arguments.output_directory / "raw_table_role_audit.md",
        rows,
        str(manifest["review_status"]),
    )


if __name__ == "__main__":
    main()
