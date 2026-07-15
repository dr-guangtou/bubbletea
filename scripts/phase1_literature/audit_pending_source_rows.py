"""Audit source rows that are absent from v2 literature membership.

The audit covers Liu M49 and M60 tables, the Voggel previously confirmed
comparison table, and the coordinate-null Fahrion rows. It reads the v2 database
without modifying it and exports row-level role, label, name, and positional
overlap diagnostics for project-lead review.
"""

import argparse
import csv
import sqlite3
from collections import Counter
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import ascii

from scripts.config import (
    LITERATURE_REFERENCE_DB_V2,
    LITERATURE_VALIDATION,
    REFERENCE_DIR,
)
from scripts.phase1_literature.audit_reference_data import connect_read_only

OUTPUT_CSV = "pending_source_row_review.csv"
OUTPUT_REPORT = "pending_source_row_review.md"


def parse_arguments() -> argparse.Namespace:
    """Parse database and output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--output-directory", type=Path, default=LITERATURE_VALIDATION)
    return parser.parse_args()


def normalized_name(value: object) -> str:
    """Normalize a source name for conservative exact-name comparison."""
    return " ".join(str(value).strip().lower().split())


def scalar_text(value: object) -> str:
    """Convert table scalars and masked values into stable CSV text."""
    if np.ma.is_masked(value):
        return ""
    return str(value).strip()


def load_canonical_context(
    connection: sqlite3.Connection,
) -> tuple[list[dict[str, object]], dict[tuple[float, float], list[str]], dict[str, list[str]]]:
    """Load canonical positions plus exact coordinate and name indexes."""
    canonical_rows = [
        dict(row)
        for row in connection.execute(
            """
            SELECT DISTINCT c.canonical_object_id, c.adopted_ra, c.adopted_dec
            FROM canonical_objects c
            JOIN object_record_associations a USING (canonical_object_id)
            JOIN literature_records r USING (record_id)
            JOIN datasets d USING (dataset_id)
            JOIN publications p USING (publication_id)
            WHERE c.adopted_ra IS NOT NULL
              AND c.adopted_dec IS NOT NULL
              AND NOT (
                  (p.bibcode = '2015ApJ...812...34L'
                   AND d.dataset_name IN ('table4.dat', 'table6.dat'))
                  OR (p.bibcode = '2020ApJ...899..140V'
                      AND d.dataset_name = 'table4.dat')
                  OR (p.bibcode = '2019A&A...625A..50F'
                      AND d.dataset_name = 'tableb1_coordinate_null_rows')
              )
            ORDER BY c.canonical_object_id
            """
        )
    ]
    canonical_by_id = {str(row["canonical_object_id"]): row for row in canonical_rows}
    for row in canonical_rows:
        row["bibcodes"] = set()
        row["original_names"] = set()
        row["reported_statuses"] = set()
    for row in connection.execute(
        """
        SELECT
            a.canonical_object_id,
            p.bibcode,
            r.original_name,
            r.reported_confirmation_status
        FROM object_record_associations a
        JOIN literature_records r USING (record_id)
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        WHERE NOT (
            (p.bibcode = '2015ApJ...812...34L'
             AND d.dataset_name IN ('table4.dat', 'table6.dat'))
            OR (p.bibcode = '2020ApJ...899..140V'
                AND d.dataset_name = 'table4.dat')
            OR (p.bibcode = '2019A&A...625A..50F'
                AND d.dataset_name = 'tableb1_coordinate_null_rows')
        )
        ORDER BY a.canonical_object_id, p.bibcode, r.record_id
        """
    ):
        canonical_row = canonical_by_id[str(row["canonical_object_id"])]
        canonical_row["bibcodes"].add(str(row["bibcode"]))
        if row["original_name"]:
            canonical_row["original_names"].add(str(row["original_name"]))
        if row["reported_confirmation_status"]:
            canonical_row["reported_statuses"].add(str(row["reported_confirmation_status"]))
    coordinate_index: dict[tuple[float, float], list[str]] = {}
    for row in canonical_rows:
        coordinate = (float(row["adopted_ra"]), float(row["adopted_dec"]))
        coordinate_index.setdefault(coordinate, []).append(str(row["canonical_object_id"]))

    name_index: dict[str, list[str]] = {}
    for row in connection.execute(
        """
        SELECT r.record_id, r.original_name
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        WHERE r.original_name IS NOT NULL
          AND TRIM(r.original_name) != ''
          AND NOT (
              (p.bibcode = '2015ApJ...812...34L'
               AND d.dataset_name IN ('table4.dat', 'table6.dat'))
              OR (p.bibcode = '2020ApJ...899..140V'
                  AND d.dataset_name = 'table4.dat')
              OR (p.bibcode = '2019A&A...625A..50F'
                  AND d.dataset_name = 'tableb1_coordinate_null_rows')
          )
        ORDER BY r.record_id
        """
    ):
        name_index.setdefault(normalized_name(row["original_name"]), []).append(
            str(row["record_id"])
        )
    return canonical_rows, coordinate_index, name_index


def load_liu_rows() -> list[dict[str, object]]:
    """Load M49 and M60 photometry with paired classification metadata."""
    folder = REFERENCE_DIR / "liu2015"
    rows = []
    table_pairs = (
        ("table4.dat", "table5.dat", "M49"),
        ("table6.dat", "table7.dat", "M60"),
    )
    for photometry_file, classification_file, host in table_pairs:
        photometry = ascii.read(
            folder / photometry_file,
            readme=folder / "ReadMe.txt",
            format="cds",
        )
        classifications = ascii.read(
            folder / classification_file,
            readme=folder / "ReadMe.txt",
            format="cds",
            fill_values=[("---", "0")],
        )
        if len(photometry) != len(classifications):
            raise ValueError(f"Liu paired-table row mismatch: {photometry_file}")
        for photometry_row, classification_row in zip(photometry, classifications, strict=True):
            if int(photometry_row["ID"]) != int(classification_row["ID"]):
                raise ValueError(f"Liu paired-table ID mismatch: {photometry_file}")
            reported_is_ucd = int(photometry_row["UCD"])
            rows.append(
                {
                    "bibcode": "2015ApJ...812...34L",
                    "source_table": photometry_file,
                    "supporting_table": classification_file,
                    "source_row_locator": f"raw_row_{int(photometry_row['ID'])}",
                    "original_name": scalar_text(photometry_row["NGVS"]),
                    "host_or_region": host,
                    "ra": float(photometry_row["RAdeg"]),
                    "dec": float(photometry_row["DEdeg"]),
                    "coordinate_status": "available",
                    "source_role": "candidate_and_comparison_records",
                    "reported_class": f"class_{int(classification_row['Class'])}",
                    "reported_is_ucd": reported_is_ucd,
                    "proposed_treatment": (
                        "unconfirmed_candidate_record"
                        if reported_is_ucd == 1
                        else "explicit_non_ucd_comparison_record"
                    ),
                    "source_notes": (
                        "Preserve the paired structural and redshift row; do not promote "
                        "reported UCD status automatically."
                    ),
                }
            )
    return rows


def load_voggel_rows() -> list[dict[str, object]]:
    """Load the previously confirmed Voggel comparison objects."""
    folder = REFERENCE_DIR / "voggel2020"
    table = ascii.read(
        folder / "table4.dat",
        readme=folder / "ReadMe.txt",
        format="cds",
    )
    return [
        {
            "bibcode": "2020ApJ...899..140V",
            "source_table": "table4.dat",
            "supporting_table": "",
            "source_row_locator": f"raw_row_{index}",
            "original_name": scalar_text(row["Name"]),
            "host_or_region": "Centaurus A",
            "ra": float(row["RAdeg"]),
            "dec": float(row["DEdeg"]),
            "coordinate_status": "available",
            "source_role": "previously_confirmed_comparison_records",
            "reported_class": "previously_confirmed_ucd",
            "reported_is_ucd": 1,
            "proposed_treatment": "reference_record_pending_evidence_review",
            "source_notes": (
                "Retain as a comparison/reference record, separate from the 632 new "
                "Gaia-selected candidates."
            ),
        }
        for index, row in enumerate(table, start=1)
    ]


def load_fahrion_coordinate_null_rows() -> list[dict[str, object]]:
    """Load only Fahrion rows whose authoritative table omits coordinates."""
    rows = []
    path = REFERENCE_DIR / "fahrion2019" / "tableb1.dat"
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        coordinate_fields = line[36:60]
        if coordinate_fields.strip():
            continue
        rows.append(
            {
                "bibcode": "2019A&A...625A..50F",
                "source_table": "tableb1.dat",
                "supporting_table": "",
                "source_row_locator": f"raw_row_{line_number}",
                "original_name": line[:19].strip(),
                "host_or_region": line[20:35].strip(),
                "ra": "",
                "dec": "",
                "coordinate_status": "missing_in_authoritative_table",
                "source_role": "literature_compilation_record",
                "reported_class": "literature_ucd",
                "reported_is_ucd": 1,
                "proposed_treatment": "coordinate_null_record_pending_identity_resolution",
                "source_notes": (
                    "Preserve as an unresolved provenance record; do not create a "
                    "coordinate-based canonical object."
                ),
            }
        )
    if len(rows) != 4:
        raise ValueError(f"Expected 4 coordinate-null Fahrion rows, found {len(rows)}")
    return rows


def add_overlap_diagnostics(
    rows: list[dict[str, object]],
    canonical_rows: list[dict[str, object]],
    coordinate_index: dict[tuple[float, float], list[str]],
    name_index: dict[str, list[str]],
) -> list[dict[str, object]]:
    """Add exact and diagnostic spherical overlap measurements."""
    canonical_coordinates = SkyCoord(
        ra=[float(row["adopted_ra"]) for row in canonical_rows] * u.deg,
        dec=[float(row["adopted_dec"]) for row in canonical_rows] * u.deg,
    )
    output_rows = []
    for review_index, row in enumerate(rows, start=1):
        name_matches = name_index.get(normalized_name(row["original_name"]), [])
        if row["coordinate_status"] == "available":
            coordinate = (float(row["ra"]), float(row["dec"]))
            exact_matches = coordinate_index.get(coordinate, [])
            source_coordinate = SkyCoord(ra=coordinate[0] * u.deg, dec=coordinate[1] * u.deg)
            separations = source_coordinate.separation(canonical_coordinates).arcsec
            nearest_index = int(np.argmin(separations))
            nearest_separation = float(separations[nearest_index])
            within_one_arcsec_count = int(np.count_nonzero(separations <= 1.0))
            within_five_arcsec_count = int(np.count_nonzero(separations <= 5.0))
            if exact_matches:
                overlap_status = "exact_coordinate_overlap"
            elif within_one_arcsec_count:
                overlap_status = "diagnostic_position_within_1_arcsec"
            elif within_five_arcsec_count:
                overlap_status = "diagnostic_position_within_5_arcsec"
            else:
                overlap_status = "no_position_within_5_arcsec"
            nearest_canonical_object_id = str(canonical_rows[nearest_index]["canonical_object_id"])
            nearest_bibcodes = ";".join(sorted(canonical_rows[nearest_index]["bibcodes"]))
            nearest_original_names = ";".join(
                sorted(canonical_rows[nearest_index]["original_names"])
            )
            nearest_reported_statuses = ";".join(
                sorted(canonical_rows[nearest_index]["reported_statuses"])
            )
        else:
            exact_matches = []
            nearest_canonical_object_id = ""
            nearest_separation = ""
            nearest_bibcodes = ""
            nearest_original_names = ""
            nearest_reported_statuses = ""
            within_one_arcsec_count = 0
            within_five_arcsec_count = 0
            overlap_status = (
                "exact_name_overlap_without_coordinates"
                if name_matches
                else "unresolved_without_coordinates"
            )
        output_rows.append(
            {
                "review_row_id": f"pending_source_row_{review_index:04d}",
                **row,
                "exact_name_match_count": len(name_matches),
                "exact_name_match_record_ids": ";".join(name_matches),
                "exact_coordinate_match_count": len(exact_matches),
                "exact_coordinate_canonical_object_ids": ";".join(exact_matches),
                "nearest_canonical_object_id": nearest_canonical_object_id,
                "nearest_separation_arcsec": nearest_separation,
                "nearest_bibcodes": nearest_bibcodes,
                "nearest_original_names": nearest_original_names,
                "nearest_reported_statuses": nearest_reported_statuses,
                "canonical_objects_within_1_arcsec": within_one_arcsec_count,
                "canonical_objects_within_5_arcsec": within_five_arcsec_count,
                "overlap_status": overlap_status,
            }
        )
    return output_rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write the deterministic row-level review artifact."""
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown_counts(counter: Counter[str]) -> str:
    """Render sorted counts as Markdown rows."""
    return "\n".join(f"| `{key}` | {value} |" for key, value in sorted(counter.items()))


def write_report(path: Path, rows: list[dict[str, object]]) -> None:
    """Write a compact project-lead decision report."""
    treatment_counts = Counter(str(row["proposed_treatment"]) for row in rows)
    overlap_counts = Counter(str(row["overlap_status"]) for row in rows)
    source_counts = Counter(f"{row['bibcode']} / {row['source_table']}" for row in rows)
    detail_counts = Counter(
        (
            f"{row['bibcode']} / {row['source_table']}",
            str(row["proposed_treatment"]),
            str(row["overlap_status"]),
        )
        for row in rows
    )
    detail_lines = "\n".join(
        f"| `{source}` | `{treatment}` | `{overlap}` | {count} |"
        for (source, treatment, overlap), count in sorted(detail_counts.items())
    )
    exact_name_match_count = sum(int(int(row["exact_name_match_count"]) > 0) for row in rows)
    matched_provenance_counts = Counter(
        (
            f"{row['bibcode']} / {row['source_table']}",
            str(row["nearest_bibcodes"]),
        )
        for row in rows
        if row["overlap_status"]
        in {
            "exact_coordinate_overlap",
            "diagnostic_position_within_1_arcsec",
            "diagnostic_position_within_5_arcsec",
        }
    )
    matched_provenance_lines = "\n".join(
        f"| `{source}` | `{matched_bibcodes}` | {count} |"
        for (source, matched_bibcodes), count in sorted(matched_provenance_counts.items())
    )
    report = f"""# Pending Literature Source-Row Review

**Date:** 2026-07-14
**Review status:** `approved_and_implemented_2026-07-14`
**Membership changes:** Implemented by the reproducible v2 builder

This read-only audit preserves the pre-implementation comparison for source rows
that lacked direct v2 membership. The baseline queries deliberately exclude the
newly approved source records so reruns continue to measure the reviewed decision.
Exact coordinate matches are measured literally. The 1- and 5-arcsecond counts
are diagnostic review aids only; they do not establish object identity.

## Source Rows

| Source table | Rows |
|---|---:|
{markdown_counts(source_counts)}

## Approved Treatments

| Proposed treatment | Rows |
|---|---:|
{markdown_counts(treatment_counts)}

The Liu tables contain explicit object-level UCD flags. Rows with `UCD=1` are
stored as unconfirmed candidates; rows with `UCD=0` remain explicit non-positive
comparison records. The paired structural/redshift tables must be retained as
supporting measurements. Voggel table 4 remains a previously confirmed comparison
sample pending object-level evidence review. Coordinate-null Fahrion rows remain
unresolved provenance records and must not create coordinate-based canonical
objects.

## Existing-v2 Overlap Diagnostics

| Overlap status | Rows |
|---|---:|
{markdown_counts(overlap_counts)}

## Row-role and Overlap Breakdown

| Source table | Proposed treatment | Overlap status | Rows |
|---|---|---|---:|
{detail_lines}

Exact normalized source names match existing literature records for
{exact_name_match_count} rows. Name equality is supporting context only and does
not override the positional review requirement.

## Nearest Existing Provenance Within Five Arcseconds

| Pending source table | Existing nearest bibcode | Rows |
|---|---|---:|
{matched_provenance_lines}

Review `pending_source_row_review.csv` for source labels, exact matches, nearest
canonical-object separations, matched bibcodes and names, and the proposed
treatment of every row. This remains a historical pre-decision overlap audit.
The T17-1596 diagnostic at 1.37 arcseconds was subsequently resolved as Fahrion
HHH86-C15 through the published Taylor GC0218 and Woodley HHH86-C15 alias chain;
the approved evidence is recorded in `source_association_reviews.json`. The audit
itself remains read-only; approved treatments are implemented separately by
`build_reference_database.py`.
"""
    path.write_text(report, encoding="utf-8")


def main() -> None:
    """Generate pending source-row review artifacts without database writes."""
    arguments = parse_arguments()
    rows = load_liu_rows() + load_voggel_rows() + load_fahrion_coordinate_null_rows()
    if len(rows) != 140:
        raise ValueError(f"Expected 140 pending rows, found {len(rows)}")
    with connect_read_only(arguments.reference_database) as connection:
        canonical_rows, coordinate_index, name_index = load_canonical_context(connection)
    review_rows = add_overlap_diagnostics(rows, canonical_rows, coordinate_index, name_index)
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    write_csv(arguments.output_directory / OUTPUT_CSV, review_rows)
    write_report(arguments.output_directory / OUTPUT_REPORT, review_rows)


if __name__ == "__main__":
    main()
