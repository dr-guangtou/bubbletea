"""Audit approved Wave 1 tables against the current canonical reference database.

The audit preserves every source row, applies only proposed table roles, and
measures exact, one-arcsecond, and five-arcsecond positional overlap. It never
changes source membership, canonical identity, or confirmation evidence.
"""

import argparse
import csv
import json
import sys
import warnings
from collections import Counter
from pathlib import Path
from statistics import median

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import ascii
from astropy.units import UnitsWarning

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_REFERENCE_DB_V2,
    LITERATURE_SOURCES,
    LITERATURE_VALIDATION,
    REFERENCE_DIR,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256, connect_read_only

DEFAULT_ROLE_MANIFEST = LITERATURE_SOURCES / "literature_wave1_table_roles.json"
DEFAULT_OUTPUT_CSV = LITERATURE_VALIDATION / "literature_wave1_source_overlap.csv"
DEFAULT_OUTPUT_REPORT = LITERATURE_VALIDATION / "literature_wave1_source_overlap.md"


def parse_arguments() -> argparse.Namespace:
    """Parse audit paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role-manifest", type=Path, default=DEFAULT_ROLE_MANIFEST)
    parser.add_argument("--reference-directory", type=Path, default=REFERENCE_DIR)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-report", type=Path, default=DEFAULT_OUTPUT_REPORT)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, object]:
    """Load one JSON document."""
    with path.open(encoding="utf-8") as input_file:
        return json.load(input_file)


def load_table(folder: Path, file_name: str) -> object:
    """Load one CDS table while preserving masked values."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UnitsWarning)
        return ascii.read(folder / file_name, readme=folder / "ReadMe.txt", format="cds")


def scalar_text(value: object) -> str:
    """Return stable text for one table value."""
    if np.ma.is_masked(value):
        return ""
    return str(value).strip()


def direct_coordinate(row: object, column_names: list[str]) -> tuple[float, float] | None:
    """Read a decimal or sexagesimal coordinate from one CDS row."""
    if {"RAdeg", "DEdeg"}.issubset(column_names):
        return float(row["RAdeg"]), float(row["DEdeg"])
    required = {"RAh", "RAm", "RAs", "DE-", "DEd", "DEm", "DEs"}
    if not required.issubset(column_names):
        return None
    ra = (float(row["RAh"]) + float(row["RAm"]) / 60 + float(row["RAs"]) / 3600) * 15
    sign = -1 if scalar_text(row["DE-"]) == "-" else 1
    dec = sign * (float(row["DEd"]) + float(row["DEm"]) / 60 + float(row["DEs"]) / 3600)
    return ra, dec


def row_identifier(file_name: str, row: object, column_names: list[str], index: int) -> str:
    """Build a source-stable row identifier."""
    if file_name == "table2.dat" and {"S/G", "Seq"}.issubset(column_names):
        return f"{scalar_text(row['S/G'])}_{scalar_text(row['Seq'])}"
    for column_name in ("Name", "ID", "Seq", "UCD-FORS", "Bin"):
        if column_name in column_names:
            return scalar_text(row[column_name])
    return str(index)


def reported_role(reference_folder: str, file_name: str, row: object) -> str:
    """Describe the source-reported row role without promoting it."""
    if reference_folder == "liu2020" and file_name == "table3.dat":
        return "reported_ucd_or_possible" if int(row["UCD?"]) == 1 else "reported_contaminant"
    if reference_folder == "ko2017" and file_name == "table2.dat":
        return "foreground_star" if scalar_text(row["S/G"]) == "STAR" else "background_galaxy"
    if reference_folder == "ko2017" and file_name == "table3.dat":
        return "reported_globular_cluster"
    if reference_folder == "ko2017" and file_name == "table4.dat":
        return "reported_ucd"
    if reference_folder == "wittmann2016" and file_name == "table1.dat":
        return "spectroscopically_confirmed_fornax_compact_system"
    if reference_folder == "wittmann2016" and file_name == "table3.dat":
        return "working_sample_structure_measurement"
    if reference_folder == "ahn2018":
        return "spatial_kinematic_bin_for_m59_ucd3"
    if reference_folder == "voggel2016":
        return "reported_ucd"
    return "supporting_measurement"


def build_linked_coordinate_maps(reference_directory: Path) -> dict[tuple[str, str], object]:
    """Build coordinate maps for supporting tables with source-row keys."""
    maps = {}
    wittmann_folder = reference_directory / "wittmann2016"
    wittmann_table = load_table(wittmann_folder, "table1.dat")
    maps[("wittmann2016", "table1.dat:Seq")] = {
        scalar_text(row["Seq"]): direct_coordinate(row, wittmann_table.colnames)
        for row in wittmann_table
    }
    liu_folder = reference_directory / "liu2020"
    liu_table = load_table(liu_folder, "table3.dat")
    maps[("liu2020", "table3.dat:Name")] = {
        scalar_text(row["Name"]): direct_coordinate(row, liu_table.colnames) for row in liu_table
    }
    return maps


def row_coordinate(
    entry: dict[str, object],
    row: object,
    column_names: list[str],
    linked_maps: dict[tuple[str, str], object],
) -> tuple[float, float] | None:
    """Resolve a direct or explicitly linked source coordinate."""
    coordinate_source = str(entry["coordinate_source"])
    if coordinate_source == "self":
        return direct_coordinate(row, column_names)
    if coordinate_source == "not_object_coordinates":
        return None
    reference_folder = str(entry["reference_folder"])
    linked_map = linked_maps[(reference_folder, coordinate_source)]
    key_column = coordinate_source.split(":", maxsplit=1)[1]
    return linked_map[scalar_text(row[key_column])]


def load_canonical_coordinates(
    database_path: Path,
) -> tuple[list[dict[str, object]], SkyCoord, dict[tuple[float, float], list[str]]]:
    """Load the current canonical positions and exact-coordinate index."""
    with connect_read_only(database_path) as connection:
        rows = [
            dict(row)
            for row in connection.execute(
                """
                SELECT canonical_object_id, adopted_ra, adopted_dec
                FROM canonical_objects
                WHERE adopted_ra IS NOT NULL AND adopted_dec IS NOT NULL
                ORDER BY canonical_object_id
                """
            )
        ]
    coordinates = SkyCoord(
        [float(row["adopted_ra"]) for row in rows] * u.deg,
        [float(row["adopted_dec"]) for row in rows] * u.deg,
    )
    exact_index: dict[tuple[float, float], list[str]] = {}
    for row in rows:
        key = (float(row["adopted_ra"]), float(row["adopted_dec"]))
        exact_index.setdefault(key, []).append(str(row["canonical_object_id"]))
    return rows, coordinates, exact_index


def add_overlap_context(
    rows: list[dict[str, object]],
    canonical_rows: list[dict[str, object]],
    canonical_coordinates: SkyCoord,
    exact_index: dict[tuple[float, float], list[str]],
) -> None:
    """Add nearest canonical and conservative overlap bins in place."""
    coordinate_rows = [row for row in rows if row["ra"] != ""]
    if not coordinate_rows:
        return
    source_coordinates = SkyCoord(
        [float(row["ra"]) for row in coordinate_rows] * u.deg,
        [float(row["dec"]) for row in coordinate_rows] * u.deg,
    )
    nearest_indices, separations, _ = source_coordinates.match_to_catalog_sky(canonical_coordinates)
    for row, nearest_index, separation in zip(
        coordinate_rows, nearest_indices, separations, strict=True
    ):
        coordinate = (float(row["ra"]), float(row["dec"]))
        exact_ids = exact_index.get(coordinate, [])
        separation_arcsec = float(separation.arcsec)
        if exact_ids:
            overlap_class = "exact_coordinate"
            canonical_ids = exact_ids
        elif separation_arcsec <= 1:
            overlap_class = "within_1_arcsec"
            canonical_ids = [str(canonical_rows[int(nearest_index)]["canonical_object_id"])]
        elif separation_arcsec <= 5:
            overlap_class = "within_5_arcsec"
            canonical_ids = [str(canonical_rows[int(nearest_index)]["canonical_object_id"])]
        else:
            overlap_class = "no_counterpart_within_5_arcsec"
            canonical_ids = [str(canonical_rows[int(nearest_index)]["canonical_object_id"])]
        row["overlap_class"] = overlap_class
        row["nearest_canonical_object_id"] = canonical_ids[0]
        row["exact_canonical_object_ids"] = ";".join(exact_ids)
        row["nearest_separation_arcsec"] = separation_arcsec


def build_rows(manifest: dict[str, object], reference_directory: Path) -> list[dict[str, object]]:
    """Load every reviewed table row with its proposed role."""
    linked_maps = build_linked_coordinate_maps(reference_directory)
    rows = []
    for entry in manifest["tables"]:
        reference_folder = str(entry["reference_folder"])
        file_name = str(entry["file_name"])
        folder = reference_directory / reference_folder
        table = load_table(folder, file_name)
        for index, source_row in enumerate(table, start=1):
            coordinate = row_coordinate(entry, source_row, table.colnames, linked_maps)
            rows.append(
                {
                    "bibcode": entry["bibcode"],
                    "reference_folder": reference_folder,
                    "file_name": file_name,
                    "source_row_locator": f"raw_row_{index}",
                    "source_identifier": row_identifier(
                        file_name, source_row, table.colnames, index
                    ),
                    "proposed_role": entry["proposed_role"],
                    "reported_role": reported_role(reference_folder, file_name, source_row),
                    "coordinate_source": entry["coordinate_source"],
                    "ra": coordinate[0] if coordinate is not None else "",
                    "dec": coordinate[1] if coordinate is not None else "",
                    "overlap_class": "coordinate_not_applicable",
                    "nearest_canonical_object_id": "",
                    "exact_canonical_object_ids": "",
                    "nearest_separation_arcsec": "",
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write deterministic row-level overlap evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    path: Path,
    rows: list[dict[str, object]],
    review_status: str,
    reference_database_sha256: str,
) -> None:
    """Write a concise Wave 1 overlap report."""
    overlap_counts = Counter(str(row["overlap_class"]) for row in rows)
    role_counts = Counter(str(row["proposed_role"]) for row in rows)
    reported_positive_roles = {"reported_ucd", "reported_ucd_or_possible"}
    comparison_roles = {
        "background_galaxy",
        "foreground_star",
        "reported_contaminant",
        "reported_globular_cluster",
    }
    reported_positive_rows = [
        row for row in rows if str(row["reported_role"]) in reported_positive_roles
    ]
    wittmann_rows = [
        row
        for row in rows
        if row["reported_role"] == "spectroscopically_confirmed_fornax_compact_system"
    ]
    comparison_rows = [row for row in rows if str(row["reported_role"]) in comparison_roles]
    coordinate_rows = [row for row in rows if row["ra"] != ""]
    separations = [float(row["nearest_separation_arcsec"]) for row in coordinate_rows]
    unique_coordinates = {(float(row["ra"]), float(row["dec"])) for row in coordinate_rows}
    overlap_lines = "\n".join(
        f"| `{key}` | {value} |" for key, value in sorted(overlap_counts.items())
    )
    role_lines = "\n".join(f"| `{key}` | {value} |" for key, value in sorted(role_counts.items()))

    def subgroup_line(label: str, subgroup_rows: list[dict[str, object]]) -> str:
        """Summarize one source-reported subgroup without changing its role."""
        subgroup_counts = Counter(str(row["overlap_class"]) for row in subgroup_rows)
        subgroup_coordinates = {
            (float(row["ra"]), float(row["dec"])) for row in subgroup_rows if row["ra"] != ""
        }
        return (
            f"| {label} | {len(subgroup_rows)} | {len(subgroup_coordinates)} | "
            f"{subgroup_counts['exact_coordinate']} | {subgroup_counts['within_1_arcsec']} | "
            f"{subgroup_counts['within_5_arcsec']} | "
            f"{subgroup_counts['no_counterpart_within_5_arcsec']} |"
        )

    subgroup_lines = "\n".join(
        [
            subgroup_line("Source-reported UCD or possible UCD", reported_positive_rows),
            subgroup_line("Wittmann compact-system compilation", wittmann_rows),
            subgroup_line("Source-reported comparison or contaminant", comparison_rows),
        ]
    )
    report = f"""# Literature Wave 1 Source Overlap Audit

**Role review status:** `{review_status}`
**Reference database SHA-256:** `{reference_database_sha256}`

This read-only audit measures the five retrieved VizieR packages against the
current v2 canonical positions. It applies the reviewed table roles for audit
grouping but makes no source
membership, identity, classification, or confirmation change.

## Measured Coverage

| Measure | Count |
|---|---:|
| Source tables | {len({(row["bibcode"], row["file_name"]) for row in rows})} |
| Preserved source rows | {len(rows)} |
| Rows with direct or explicitly linked object coordinates | {len(coordinate_rows)} |
| Unique source coordinates | {len(unique_coordinates)} |
| Minimum nearest-canonical separation, arcsec | {min(separations):.12f} |
| Median nearest-canonical separation, arcsec | {median(separations):.12f} |
| Maximum nearest-canonical separation, arcsec | {max(separations):.12f} |

## Positional Overlap

| Class | Rows |
|---|---:|
{overlap_lines}

## Reviewed Table Roles

| Role | Rows |
|---|---:|
{role_lines}

## Decision-Relevant Source Subgroups

| Source-reported subgroup | Rows | Unique coordinates | Exact | Within 1 arcsec | Within 5 arcsec | Beyond 5 arcsec |
|---|---:|---:|---:|---:|---:|---:|
{subgroup_lines}

Repeated rows across primary and supporting tables remain separate provenance.
An exact or nearby coordinate is overlap evidence only and does not authorize an
association. The 109 Ahn kinematic bins are supporting measurements for one UCD,
not 109 astrophysical objects.
"""
    path.write_text(report, encoding="utf-8")


def main() -> None:
    """Run the read-only Wave 1 source overlap audit."""
    arguments = parse_arguments()
    manifest = load_json(arguments.role_manifest)
    rows = build_rows(manifest, arguments.reference_directory)
    canonical_rows, canonical_coordinates, exact_index = load_canonical_coordinates(
        arguments.reference_database
    )
    add_overlap_context(rows, canonical_rows, canonical_coordinates, exact_index)
    write_csv(arguments.output_csv, rows)
    write_report(
        arguments.output_report,
        rows,
        str(manifest["review_status"]),
        calculate_sha256(arguments.reference_database),
    )


if __name__ == "__main__":
    main()
