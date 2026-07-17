"""Build the non-destructive v2 literature reference database.

The legacy SQLite database and per-source CSVs are opened as immutable inputs.
Only exact stored coordinates create automatic canonical identity associations.
Project-lead-approved source associations are encoded with their measured
separations; all other non-exact links and confirmation promotions remain review
items.
"""

import argparse
import csv
import gzip
import hashlib
import json
import logging
import sqlite3
import sys
import uuid
import warnings
from collections import Counter, defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import ascii
from astropy.units import UnitsWarning

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_CATALOGS,
    LITERATURE_DB,
    LITERATURE_REFERENCE_DB_V2,
    LITERATURE_SOURCES,
    LITERATURE_VALIDATION,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256, connect_read_only

logger = logging.getLogger(__name__)

RULESET_ID = "confirmation_rules_v1"
IDENTIFIER_NAMESPACE = uuid.UUID("7bc01ef8-f960-4f62-ae8b-0f40f5687607")
SOURCE_MANIFEST = LITERATURE_SOURCES / "source_corrections.json"
ASSOCIATION_REVIEW_MANIFEST = LITERATURE_SOURCES / "source_association_reviews.json"
GAIA_ASSOCIATION_REVIEW_MANIFEST = LITERATURE_SOURCES / "gaia_association_reviews.json"
RETRIEVAL_REPORT = LITERATURE_VALIDATION / "vizier_retrieval.json"
WAVE1_RETRIEVAL_MANIFEST = LITERATURE_SOURCES / "literature_retrieval_wave1.json"
WAVE1_VIZIER_REPORT = LITERATURE_VALIDATION / "vizier_retrieval_wave1.json"
WAVE1_ROLE_MANIFEST = LITERATURE_SOURCES / "literature_wave1_table_roles.json"
WAVE1_IDENTITY_REVIEW_MANIFEST = LITERATURE_SOURCES / "literature_wave1_identity_reviews.json"
WAVE1_IDENTITY_PROPOSAL_MANIFEST = LITERATURE_SOURCES / "literature_wave1_identity_proposals.json"
WAVE1_GROUP_IDENTITY_PROPOSAL_MANIFEST = (
    LITERATURE_SOURCES / "literature_wave1_group_identity_proposals.json"
)
WAVE1_REMAINING_IDENTITY_REVIEW_MANIFEST = (
    LITERATURE_SOURCES / "literature_wave1_remaining_identity_reviews.json"
)
SUPPORTING_SOURCE_ROW_LINK_MANIFEST = LITERATURE_SOURCES / "supporting_source_row_links.json"
HOST_DISTANCE_REVIEW_MANIFEST = LITERATURE_SOURCES / "host_distance_reviews.json"
CONFIRMATION_EVIDENCE_REVIEW_MANIFEST = LITERATURE_SOURCES / "confirmation_evidence_reviews.json"
LITERATURE_SCREENING_CLOSURE_MANIFEST = LITERATURE_SOURCES / "literature_screening_closure.json"
WAVE1_DISCOVERY = (
    PROJECT_ROOT / "data" / "literature" / "discovery" / "literature_discovery_2026-07-15.json"
)
SCHEMA_PATH = Path(__file__).with_name("reference_schema.sql")


def parse_arguments() -> argparse.Namespace:
    """Parse build paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-database", type=Path, default=LITERATURE_DB)
    parser.add_argument("--output-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--source-manifest", type=Path, default=SOURCE_MANIFEST)
    parser.add_argument("--retrieval-report", type=Path, default=RETRIEVAL_REPORT)
    parser.add_argument(
        "--catalog-directory",
        type=Path,
        default=LITERATURE_CATALOGS / "by_source",
    )
    return parser.parse_args()


def stable_identifier(prefix: str, value: str) -> str:
    """Return a deterministic UUID-based identifier."""
    identifier = uuid.uuid5(IDENTIFIER_NAMESPACE, f"{prefix}:{value}")
    return f"{prefix}_{identifier.hex}"


def relative_path(path: Path) -> str:
    """Represent repository files with a portable relative path."""
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def load_source_manifest(path: Path) -> list[dict[str, object]]:
    """Load and validate corrected publication metadata."""
    with path.open(encoding="utf-8") as input_file:
        manifest = json.load(input_file)
    sources = manifest["sources"]
    legacy_ids = [source["legacy_source_id"] for source in sources]
    bibcodes = [source["bibcode"] for source in sources]
    if len(legacy_ids) != len(set(legacy_ids)) or len(bibcodes) != len(set(bibcodes)):
        raise ValueError("Source manifest contains duplicate identifiers")
    return sources


def create_database(path: Path) -> sqlite3.Connection:
    """Create a fresh v2 database from the checked-in schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return connection


def insert_publications(
    connection: sqlite3.Connection, sources: list[dict[str, object]]
) -> dict[str, dict[str, object]]:
    """Insert corrected publications and legacy identifier aliases."""
    sources_by_legacy_id = {}
    for source in sources:
        publication_id = f"ads:{source['bibcode']}"
        source = {**source, "publication_id": publication_id}
        sources_by_legacy_id[str(source["legacy_source_id"])] = source
        connection.execute(
            """
            INSERT INTO publications (
                publication_id, bibcode, doi, title, authors, publication_year,
                legacy_source_id, screening_category, provenance_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                publication_id,
                source["bibcode"],
                source["doi"],
                source["title"],
                source["authors"],
                source["year"],
                source["legacy_source_id"],
                source["screening_category"],
                "processed_catalog_only",
                "Raw authoritative package pending unless documented separately",
            ),
        )
        if source["legacy_source_id"] != source["bibcode"]:
            connection.execute(
                """
                INSERT INTO publication_aliases (
                    alias, publication_id, alias_type, correction_reason
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    source["legacy_source_id"],
                    publication_id,
                    "incorrect_legacy_bibcode",
                    "Corrected against NASA ADS and the VizieR ReadMe",
                ),
            )
    return sources_by_legacy_id


def insert_wave1_publications(
    connection: sqlite3.Connection,
) -> dict[str, dict[str, object]]:
    """Insert every project-approved Wave 1 publication from reviewed metadata."""
    with WAVE1_RETRIEVAL_MANIFEST.open(encoding="utf-8") as input_file:
        retrieval_manifest = json.load(input_file)
    with WAVE1_DISCOVERY.open(encoding="utf-8") as input_file:
        discovery = json.load(input_file)
    papers = {str(paper["bibcode"]): paper for paper in discovery["papers"]}
    sources_by_bibcode = {}
    for approved_source in retrieval_manifest["sources"]:
        bibcode = str(approved_source["bibcode"])
        paper = papers.get(bibcode)
        if paper is None:
            raise RuntimeError(f"Wave 1 publication is absent from discovery metadata: {bibcode}")
        publication_id = f"ads:{bibcode}"
        source = {
            **approved_source,
            "publication_id": publication_id,
            "legacy_source_id": bibcode,
            "catalog_id": approved_source.get("vizier_catalog"),
        }
        connection.execute(
            """
            INSERT INTO publications (
                publication_id, bibcode, doi, title, authors, publication_year,
                legacy_source_id, screening_category, provenance_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                publication_id,
                bibcode,
                approved_source["doi"],
                paper["title"],
                "; ".join(str(author) for author in paper["authors"]),
                paper["year"],
                None,
                approved_source["screening_category"],
                "approved_wave1_files_retrieved",
                "Retrieval alone does not approve identity or confirmation evidence",
            ),
        )
        sources_by_bibcode[bibcode] = source
    if len(sources_by_bibcode) != 19:
        raise RuntimeError(
            f"Expected 19 approved Wave 1 publications, found {len(sources_by_bibcode)}"
        )
    return sources_by_bibcode


def insert_wave1_package_dataset(
    connection: sqlite3.Connection,
    source: dict[str, object],
    table_paths: list[Path],
    row_count: int,
) -> str:
    """Insert one authoritative Wave 1 VizieR package dataset."""
    catalog_id = str(source["catalog_id"])
    dataset_name = f"{catalog_id}_wave1_package"
    dataset_id = stable_identifier("dataset", f"{source['bibcode']}:{dataset_name}")
    package_digest = hashlib.sha256(
        "".join(calculate_sha256(path) for path in sorted(table_paths)).encode()
    ).hexdigest()
    connection.execute(
        """
        INSERT INTO datasets (
            dataset_id, publication_id, dataset_name, catalog_id, table_id,
            local_path, file_sha256, row_count, authority_status,
            retrieval_method, retrieval_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dataset_id,
            source["publication_id"],
            dataset_name,
            catalog_id,
            None,
            relative_path(table_paths[0].parent),
            package_digest,
            row_count,
            "authoritative_vizier_package",
            "approved_wave1_vizier_retrieval",
            date.today().isoformat(),
        ),
    )
    return dataset_id


def insert_wave1_package_files(
    connection: sqlite3.Connection,
    dataset_by_bibcode: dict[str, str],
) -> None:
    """Register every retrieved Wave 1 VizieR file with its reviewed hash."""
    with WAVE1_VIZIER_REPORT.open(encoding="utf-8") as input_file:
        report = json.load(input_file)
    registered_file_count = 0
    for source in report["sources"]:
        if source["retrieval_status"] != "complete":
            raise RuntimeError(f"Incomplete approved VizieR package: {source['bibcode']}")
        dataset_id = dataset_by_bibcode[str(source["bibcode"])]
        for file_data in source["files"]:
            file_path = (
                PROJECT_ROOT / "reference" / source["reference_folder"] / file_data["file_name"]
            )
            if calculate_sha256(file_path) != file_data["sha256"]:
                raise RuntimeError(f"Wave 1 VizieR hash mismatch: {file_path}")
            dataset_file_id = stable_identifier(
                "dataset_file", f"{dataset_id}:{file_data['file_name']}"
            )
            connection.execute(
                """
                INSERT INTO dataset_files (
                    dataset_file_id, dataset_id, file_name, local_path, file_role,
                    file_sha256, byte_count, raw_row_count, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dataset_file_id,
                    dataset_id,
                    file_data["file_name"],
                    relative_path(file_path),
                    (
                        "vizier_readme"
                        if file_data["file_name"] == "ReadMe.txt"
                        else "raw_machine_readable_table"
                    ),
                    file_data["sha256"],
                    file_data["byte_count"],
                    raw_row_count(file_path),
                    file_data["source_url"],
                ),
            )
            registered_file_count += 1
    if registered_file_count != 16:
        raise RuntimeError(
            f"Expected 16 Wave 1 VizieR package files, found {registered_file_count}"
        )


def insert_dataset(
    connection: sqlite3.Connection,
    source: dict[str, object],
    catalog_path: Path,
    row_count: int,
    *,
    authority_status: str = "processed_legacy_csv",
    retrieval_method: str = "legacy_ingestion_export",
    table_id: str | None = None,
    dataset_name: str | None = None,
) -> str:
    """Insert a processed or authoritative dataset and return its identifier."""
    resolved_dataset_name = dataset_name or catalog_path.name
    dataset_id = stable_identifier("dataset", f"{source['bibcode']}:{resolved_dataset_name}")
    connection.execute(
        """
        INSERT INTO datasets (
            dataset_id, publication_id, dataset_name, catalog_id, table_id,
            local_path, file_sha256, row_count, authority_status,
            retrieval_method, retrieval_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dataset_id,
            source["publication_id"],
            resolved_dataset_name,
            table_id or source["catalog_id"],
            source["catalog_id"],
            relative_path(catalog_path),
            calculate_sha256(catalog_path),
            row_count,
            authority_status,
            retrieval_method,
            date.today().isoformat() if retrieval_method == "vizier_raw_table" else None,
        ),
    )
    return dataset_id


def raw_row_count(path: Path) -> int | None:
    """Count records in a VizieR fixed-width table."""
    if path.name.endswith(".dat.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as input_file:
            return sum(1 for _ in input_file)
    if path.name.endswith(".dat"):
        with path.open(encoding="utf-8") as input_file:
            return sum(1 for _ in input_file)
    return None


def insert_raw_dataset_files(connection: sqlite3.Connection, retrieval_report: Path) -> None:
    """Link retrieved VizieR files to normalized datasets with hashes and row counts."""
    with retrieval_report.open(encoding="utf-8") as input_file:
        report = json.load(input_file)
    for source in report["sources"]:
        if source["retrieval_status"] != "complete":
            continue
        publication_id = f"ads:{source['bibcode']}"
        publication_datasets = connection.execute(
            """
            SELECT dataset_id, dataset_name, local_path, authority_status
            FROM datasets
            WHERE publication_id = ?
            ORDER BY dataset_id
            """,
            (publication_id,),
        ).fetchall()
        if not publication_datasets:
            continue
        default_dataset = next(
            (row for row in publication_datasets if str(row["dataset_name"]).endswith(".csv")),
            publication_datasets[0],
        )
        for file_data in source["files"]:
            file_path = (
                PROJECT_ROOT / "reference" / source["reference_folder"] / file_data["file_name"]
            )
            paired_primary_file = {
                ("2015ApJ...812...34L", "table5.dat"): "table4.dat",
                ("2015ApJ...812...34L", "table7.dat"): "table6.dat",
            }.get((source["bibcode"], file_data["file_name"]))
            if paired_primary_file:
                matching_dataset = next(
                    row
                    for row in publication_datasets
                    if row["dataset_name"] == paired_primary_file
                )
            elif (
                source["bibcode"] == "2019A&A...625A..50F"
                and file_data["file_name"] == "tableb1.dat"
            ):
                matching_dataset = next(
                    row for row in publication_datasets if str(row["dataset_name"]).endswith(".csv")
                )
            else:
                matching_dataset = next(
                    (
                        row
                        for row in publication_datasets
                        if row["local_path"] == relative_path(file_path)
                    ),
                    default_dataset,
                )
            dataset_id = matching_dataset["dataset_id"]
            dataset_file_id = stable_identifier(
                "dataset_file", f"{dataset_id}:{file_data['file_name']}"
            )
            connection.execute(
                """
                INSERT INTO dataset_files (
                    dataset_file_id, dataset_id, file_name, local_path, file_role,
                    file_sha256, byte_count, raw_row_count, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dataset_file_id,
                    dataset_id,
                    file_data["file_name"],
                    relative_path(file_path),
                    "vizier_readme"
                    if file_data["file_name"] == "ReadMe.txt"
                    else "raw_machine_readable_table",
                    file_data["sha256"],
                    file_data["byte_count"],
                    raw_row_count(file_path),
                    file_data["source_url"],
                ),
            )
        connection.execute(
            """
            UPDATE datasets
            SET authority_status = CASE
                WHEN authority_status = 'processed_legacy_csv'
                THEN 'normalized_records_linked_to_raw_package'
                ELSE authority_status
            END
            WHERE publication_id = ?
            """,
            (publication_id,),
        )
        connection.execute(
            """
            UPDATE publications
            SET provenance_status = 'raw_package_retrieved'
            WHERE publication_id = ?
            """,
            (publication_id,),
        )


def normalize_scalar(value: object) -> object:
    """Convert empty CSV values to null while preserving strings exactly."""
    if value == "" or value is None:
        return None
    return value


def parse_float(value: object) -> float | None:
    """Parse an optional numeric value."""
    value = normalize_scalar(value)
    return None if value is None else float(value)


def parse_integer(value: object) -> int | None:
    """Parse an optional integer value."""
    value = normalize_scalar(value)
    return None if value is None else int(float(value))


def load_legacy_rows(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Load every legacy row from a read-only connection."""
    return [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM ucd_objects ORDER BY source_id, object_id"
        ).fetchall()
    ]


def load_zhang_raw_rows() -> tuple[Path, list[dict[str, object]]]:
    """Load all 97 rows from the authoritative Zhang VizieR table."""
    table_path = PROJECT_ROOT / "reference" / "zhang2015" / "table1.dat"
    readme_path = PROJECT_ROOT / "reference" / "zhang2015" / "ReadMe.txt"
    table = ascii.read(table_path, readme=readme_path, format="cds")
    return table_path, serialize_table_rows(table)


def serialize_table_rows(table: object) -> list[dict[str, object]]:
    """Convert an Astropy table to JSON-compatible row dictionaries."""
    rows = []
    for table_row in table:
        row = {}
        for column_name in table.colnames:
            value = table_row[column_name]
            if np.ma.is_masked(value):
                row[column_name] = None
            elif hasattr(value, "item"):
                row[column_name] = value.item()
            else:
                row[column_name] = value
        rows.append(row)
    return rows


def load_dumont_raw_rows() -> tuple[Path, list[dict[str, object]]]:
    """Load the authoritative Dumont target catalog."""
    table_path = PROJECT_ROOT / "reference" / "dumont2022" / "table2.dat"
    readme_path = PROJECT_ROOT / "reference" / "dumont2022" / "ReadMe.txt"
    table = ascii.read(table_path, readme=readme_path, format="cds")
    return table_path, serialize_table_rows(table)


def load_saifollahi_table(file_name: str) -> tuple[Path, list[dict[str, object]]]:
    """Load one authoritative Saifollahi VizieR table."""
    table_path = PROJECT_ROOT / "reference" / "saifollahi2021" / file_name
    readme_path = PROJECT_ROOT / "reference" / "saifollahi2021" / "ReadMe.txt"
    table = ascii.read(table_path, readme=readme_path, format="cds")
    return table_path, serialize_table_rows(table)


def load_vizier_table(
    reference_folder: str,
    file_name: str,
    *,
    fill_values: list[tuple[str, str]] | None = None,
) -> tuple[Path, list[dict[str, object]]]:
    """Load one authoritative VizieR table from a reference package."""
    folder = PROJECT_ROOT / "reference" / reference_folder
    table_path = folder / file_name
    read_options = {}
    if fill_values is not None:
        read_options["fill_values"] = fill_values
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UnitsWarning)
        table = ascii.read(
            table_path,
            readme=folder / "ReadMe.txt",
            format="cds",
            **read_options,
        )
    return table_path, serialize_table_rows(table)


def sexagesimal_coordinate(row: dict[str, object]) -> tuple[float, float]:
    """Convert one CDS sexagesimal position to decimal degrees."""
    ra = (float(row["RAh"]) + float(row["RAm"]) / 60 + float(row["RAs"]) / 3600) * 15
    sign = -1 if str(row["DE-"]).strip() == "-" else 1
    dec = sign * (float(row["DEd"]) + float(row["DEm"]) / 60 + float(row["DEs"]) / 3600)
    return ra, dec


def insert_wave1_object_record(
    connection: sqlite3.Connection,
    dataset_id: str,
    source: dict[str, object],
    file_name: str,
    row_number: int,
    normalized: dict[str, object],
    raw_payload: dict[str, object],
) -> dict[str, object]:
    """Insert one approved Wave 1 object or comparison record."""
    record_id = insert_literature_record(
        connection,
        dataset_id,
        f"{file_name}:raw_row_{row_number}",
        None,
        normalized,
        raw_payload,
    )
    return {
        **normalized,
        "object_id": None,
        "record_id": record_id,
        "source_id": source["bibcode"],
        "source": source,
        "wave1_source_row": True,
        "wave1_file_name": file_name,
    }


def ingest_wave1_tables(
    connection: sqlite3.Connection,
    sources_by_bibcode: dict[str, dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, str]]:
    """Apply the approved Wave 1 row roles without broad identity matching."""
    with WAVE1_ROLE_MANIFEST.open(encoding="utf-8") as input_file:
        role_manifest = json.load(input_file)
    if role_manifest["review_status"] != "approved_by_project_lead_2026-07-15":
        raise RuntimeError("Wave 1 table roles lack project-lead approval")

    entries_by_bibcode = defaultdict(list)
    loaded_tables = {}
    for entry in role_manifest["tables"]:
        bibcode = str(entry["bibcode"])
        entries_by_bibcode[bibcode].append(entry)
        table_path, table_rows = load_vizier_table(
            str(entry["reference_folder"]), str(entry["file_name"])
        )
        loaded_tables[(bibcode, str(entry["file_name"]))] = (table_path, table_rows)

    dataset_by_bibcode = {}
    normalized_row_counts = {
        "2016A&A...586A.102V": 105,
        "2016MNRAS.459.4450W": 904,
        "2017ApJ...835..212K": 1406,
        "2018ApJ...858..102A": 0,
        "2020ApJS..250...17L": 828,
    }
    for bibcode, entries in sorted(entries_by_bibcode.items()):
        table_paths = [loaded_tables[(bibcode, str(entry["file_name"]))][0] for entry in entries]
        dataset_by_bibcode[bibcode] = insert_wave1_package_dataset(
            connection,
            sources_by_bibcode[bibcode],
            table_paths,
            normalized_row_counts[bibcode],
        )

    inserted_records = []

    voggel_source = sources_by_bibcode["2016A&A...586A.102V"]
    voggel_dataset_id = dataset_by_bibcode["2016A&A...586A.102V"]
    for file_name in ("table1.dat", "tablea1.dat", "tablea2.dat"):
        _, rows = loaded_tables[("2016A&A...586A.102V", file_name)]
        for row_number, row in enumerate(rows, start=1):
            ra, dec = sexagesimal_coordinate(row)
            normalized = {
                "original_name": f"UCD-FORS {int(row['UCD-FORS'])}",
                "ra": ra,
                "dec": dec,
                "distance_mpc": None,
                "confirmation_status": "candidate",
                "is_ucd": 1,
                "gaia_dr3_id": None,
                "host_galaxy": "NGC 1399",
            }
            inserted_records.append(
                insert_wave1_object_record(
                    connection,
                    voggel_dataset_id,
                    voggel_source,
                    file_name,
                    row_number,
                    normalized,
                    row,
                )
            )

    wittmann_bibcode = "2016MNRAS.459.4450W"
    wittmann_dataset_id = dataset_by_bibcode[wittmann_bibcode]
    _, wittmann_primary_rows = loaded_tables[(wittmann_bibcode, "table1.dat")]
    _, wittmann_supporting_rows = loaded_tables[(wittmann_bibcode, "table3.dat")]
    supporting_by_sequence = {int(row["Seq"]): row for row in wittmann_supporting_rows}
    for row_number, row in enumerate(wittmann_primary_rows, start=1):
        sequence = int(row["Seq"])
        ra, dec = sexagesimal_coordinate(row)
        pool_record_id = stable_identifier(
            "pool_record", f"{wittmann_dataset_id}:table1.dat:raw_row_{row_number}"
        )
        connection.execute(
            """
            INSERT INTO selection_pool_records (
                pool_record_id, dataset_id, source_row_locator, original_name,
                ra, dec, proposed_class, ucd_score, star_score, galaxy_score,
                raw_payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pool_record_id,
                wittmann_dataset_id,
                f"table1.dat:raw_row_{row_number}",
                row["Simbad"] or f"Wittmann-{sequence}",
                ra,
                dec,
                "mixed_fornax_compact_system",
                None,
                None,
                None,
                json.dumps(
                    {
                        "authoritative_primary_row": row,
                        "supporting_structure_measurement": supporting_by_sequence.get(sequence),
                        "supporting_table": "table3.dat",
                    },
                    sort_keys=True,
                    default=str,
                ),
            ),
        )
    if len(supporting_by_sequence) != 355:
        raise RuntimeError(
            f"Expected 355 Wittmann supporting rows, found {len(supporting_by_sequence)}"
        )

    ko_bibcode = "2017ApJ...835..212K"
    ko_source = sources_by_bibcode[ko_bibcode]
    ko_dataset_id = dataset_by_bibcode[ko_bibcode]
    ko_records = []
    for file_name in ("table2.dat", "table3.dat", "table4.dat"):
        _, rows = loaded_tables[(ko_bibcode, file_name)]
        for row_number, row in enumerate(rows, start=1):
            if file_name == "table2.dat":
                original_name = f"{row['S/G']}_{int(row['Seq'])}"
                reported_is_ucd = 0
            else:
                original_name = str(row["ID"])
                reported_is_ucd = int(file_name == "table4.dat")
            normalized = {
                "original_name": original_name,
                "ra": row["RAdeg"],
                "dec": row["DEdeg"],
                "distance_mpc": None,
                "confirmation_status": "candidate" if reported_is_ucd else "not_ucd",
                "is_ucd": reported_is_ucd,
                "gaia_dr3_id": None,
                "host_galaxy": "Virgo cluster",
            }
            record = insert_wave1_object_record(
                connection,
                ko_dataset_id,
                ko_source,
                file_name,
                row_number,
                normalized,
                row,
            )
            ko_records.append(record)
            inserted_records.append(record)
    ko_records_by_coordinate = defaultdict(list)
    for record in ko_records:
        ko_records_by_coordinate[(float(record["ra"]), float(record["dec"]))].append(record)
    ko_role_conflict_groups = [
        group
        for group in ko_records_by_coordinate.values()
        if {int(record["is_ucd"]) for record in group} == {0, 1}
    ]
    if len(ko_role_conflict_groups) != 4:
        raise RuntimeError(
            f"Expected four exact Ko UCD/GC role conflicts, found {len(ko_role_conflict_groups)}"
        )
    for group in ko_role_conflict_groups:
        for record in group:
            record["approved_classification_subtype"] = "reported_ucd_role_conflict"

    liu_bibcode = "2020ApJS..250...17L"
    liu_source = sources_by_bibcode[liu_bibcode]
    liu_dataset_id = dataset_by_bibcode[liu_bibcode]
    _, liu_primary_rows = loaded_tables[(liu_bibcode, "table3.dat")]
    _, liu_supporting_rows = loaded_tables[(liu_bibcode, "table4.dat")]
    if len(liu_primary_rows) != len(liu_supporting_rows):
        raise RuntimeError("Liu Wave 1 paired-table row counts differ")
    for row_number, (primary_row, supporting_row) in enumerate(
        zip(liu_primary_rows, liu_supporting_rows, strict=True), start=1
    ):
        if primary_row["Name"] != supporting_row["Name"]:
            raise RuntimeError(f"Liu Wave 1 paired-table name mismatch at row {row_number}")
        reported_is_ucd = int(primary_row["UCD?"])
        normalized = {
            "original_name": primary_row["Name"],
            "ra": primary_row["RAdeg"],
            "dec": primary_row["DEdeg"],
            "distance_mpc": None,
            "confirmation_status": "candidate" if reported_is_ucd else "not_ucd",
            "is_ucd": reported_is_ucd,
            "gaia_dr3_id": None,
            "host_galaxy": "Virgo cluster",
        }
        record = insert_wave1_object_record(
            connection,
            liu_dataset_id,
            liu_source,
            "table3.dat",
            row_number,
            normalized,
            {
                "authoritative_primary_row": primary_row,
                "authoritative_supporting_row": supporting_row,
                "supporting_table": "table4.dat",
            },
        )
        aliases = str(supporting_row.get("OName") or "").split("/")
        record["wave1_aliases"] = [alias.strip() for alias in aliases if alias.strip()]
        inserted_records.append(record)

    role_counts = Counter(record["is_ucd"] for record in inserted_records)
    expected_role_counts = Counter({0: 1484, 1: 855})
    if role_counts != expected_role_counts:
        raise RuntimeError(f"Unexpected Wave 1 object roles: {role_counts}")
    wittmann_pool_count = connection.execute(
        "SELECT COUNT(*) FROM selection_pool_records WHERE dataset_id = ?",
        (wittmann_dataset_id,),
    ).fetchone()[0]
    if wittmann_pool_count != 904:
        raise RuntimeError(
            f"Expected 904 Wittmann selection-pool rows, found {wittmann_pool_count}"
        )
    insert_wave1_package_files(connection, dataset_by_bibcode)
    return inserted_records, dataset_by_bibcode


def is_saifollahi_reference_ucd(raw_row: dict[str, object]) -> bool:
    """Apply the paper's reported bright, measured-size UCD definition."""
    half_light_radius = raw_row.get("rh")
    return (
        float(raw_row["gmag"]) <= 21
        and half_light_radius is not None
        and 0 <= float(half_light_radius) < 75
    )


def ingest_saifollahi_legacy_records(
    connection: sqlite3.Connection,
    source: dict[str, object],
    catalog_path: Path,
    source_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Reconcile the mixed spectroscopic UCD/GC table with the legacy rows."""
    _, raw_rows = load_saifollahi_table("tablea1.dat")
    if len(source_rows) != len(raw_rows):
        raise RuntimeError("Saifollahi legacy and raw table A1 row counts differ")
    selected_count = sum(is_saifollahi_reference_ucd(row) for row in raw_rows)
    if selected_count != 61:
        raise RuntimeError(f"Expected 61 Saifollahi reference UCDs, found {selected_count}")

    dataset_id = insert_dataset(connection, source, catalog_path, len(source_rows))
    inserted_records = []
    for legacy_row, raw_row in zip(source_rows, raw_rows, strict=True):
        if float(legacy_row["ra"]) != float(raw_row["RAdeg"]) or float(legacy_row["dec"]) != float(
            raw_row["DEdeg"]
        ):
            raise RuntimeError("Saifollahi legacy and raw table A1 row order differs")
        reference_ucd = is_saifollahi_reference_ucd(raw_row)
        normalized = {
            **legacy_row,
            "confirmation_status": "confirmed" if reference_ucd else "not_ucd",
            "is_ucd": 1 if reference_ucd else 0,
        }
        record_id = insert_literature_record(
            connection,
            dataset_id,
            str(legacy_row["object_id"]),
            str(legacy_row["object_id"]),
            normalized,
            {"legacy_record": legacy_row, "authoritative_raw_row": raw_row},
        )
        inserted_records.append(
            {
                **normalized,
                "record_id": record_id,
                "source": source,
                "saifollahi_reference_ucd": reference_ucd,
            }
        )
    return inserted_records


def ingest_saifollahi_candidate_tables(
    connection: sqlite3.Connection, source: dict[str, object]
) -> list[dict[str, object]]:
    """Keep table A5 as a screening pool and ingest only the 44 BEST candidates."""
    pool_path, pool_rows = load_saifollahi_table("tablea5.dat")
    pool_dataset_id = insert_dataset(
        connection,
        source,
        pool_path,
        len(pool_rows),
        authority_status="authoritative_selection_pool",
        retrieval_method="vizier_raw_table",
        table_id="tablea5",
    )
    pool_by_coordinate = {}
    proposed_class_counts = Counter()
    for row_number, row in enumerate(pool_rows, start=1):
        proposed_class = (
            "ucd_candidate"
            if str(row["ID"]).startswith("UCD-CAND-")
            else "globular_cluster_candidate"
        )
        proposed_class_counts[proposed_class] += 1
        pool_record_id = stable_identifier("pool_record", f"{pool_dataset_id}:raw_row_{row_number}")
        connection.execute(
            """
            INSERT INTO selection_pool_records (
                pool_record_id, dataset_id, source_row_locator, original_name,
                ra, dec, proposed_class, ucd_score, star_score, galaxy_score,
                raw_payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pool_record_id,
                pool_dataset_id,
                f"raw_row_{row_number}",
                row["ID"],
                row["RAdeg"],
                row["DEdeg"],
                proposed_class,
                row["UCD"],
                row["Star"],
                row["Gal"],
                json.dumps(row, sort_keys=True, default=str),
            ),
        )
        pool_by_coordinate[(float(row["RAdeg"]), float(row["DEdeg"]))] = pool_record_id
    if proposed_class_counts != Counter({"ucd_candidate": 222, "globular_cluster_candidate": 933}):
        raise RuntimeError(f"Unexpected Saifollahi table A5 classes: {proposed_class_counts}")

    best_path, best_rows = load_saifollahi_table("tablea6.dat")
    if len(best_rows) != 44:
        raise RuntimeError(f"Expected 44 Saifollahi BEST candidates, found {len(best_rows)}")
    best_dataset_id = insert_dataset(
        connection,
        source,
        best_path,
        len(best_rows),
        authority_status="authoritative_candidate_table",
        retrieval_method="vizier_raw_table",
        table_id="tablea6",
    )
    inserted_records = []
    for row_number, row in enumerate(best_rows, start=1):
        coordinate = (float(row["RAdeg"]), float(row["DEdeg"]))
        pool_record_id = pool_by_coordinate.get(coordinate)
        if pool_record_id is None:
            raise RuntimeError(f"Saifollahi BEST candidate absent from table A5: {row['ID']}")
        normalized = {
            "original_name": row["ID"],
            "ra": row["RAdeg"],
            "dec": row["DEdeg"],
            "distance_mpc": 20.0,
            "confirmation_status": "candidate",
            "is_ucd": 1,
            "gaia_dr3_id": None,
            "host_galaxy": "Fornax cluster",
        }
        record_id = insert_literature_record(
            connection,
            best_dataset_id,
            f"raw_row_{row_number}",
            None,
            normalized,
            row,
        )
        connection.execute(
            """
            INSERT INTO selection_pool_record_links (
                pool_record_id, record_id, relationship, association_method
            ) VALUES (?, ?, ?, ?)
            """,
            (pool_record_id, record_id, "best_candidate_subset", "exact_coordinate"),
        )
        inserted_records.append(
            {
                **normalized,
                "object_id": None,
                "record_id": record_id,
                "source_id": source["legacy_source_id"],
                "source": source,
                "saifollahi_best_candidate": True,
            }
        )
    return inserted_records


def ingest_liu_pending_tables(
    connection: sqlite3.Connection, source: dict[str, object]
) -> list[dict[str, object]]:
    """Ingest approved Liu M49 and M60 candidate and comparison records."""
    inserted_records = []
    table_pairs = (
        ("table4.dat", "table5.dat", "M49"),
        ("table6.dat", "table7.dat", "M60"),
    )
    for primary_file, supporting_file, host in table_pairs:
        primary_path, primary_rows = load_vizier_table("liu2015", primary_file)
        _, supporting_rows = load_vizier_table(
            "liu2015",
            supporting_file,
            fill_values=[("---", "0")],
        )
        if len(primary_rows) != len(supporting_rows):
            raise RuntimeError(f"Liu paired-table row mismatch: {primary_file}")
        dataset_id = insert_dataset(
            connection,
            source,
            primary_path,
            len(primary_rows),
            authority_status="authoritative_mixed_candidate_comparison_table",
            retrieval_method="vizier_raw_table",
            table_id=primary_file.removesuffix(".dat"),
        )
        for row_number, (primary_row, supporting_row) in enumerate(
            zip(primary_rows, supporting_rows, strict=True), start=1
        ):
            if int(primary_row["ID"]) != int(supporting_row["ID"]):
                raise RuntimeError(f"Liu paired-table ID mismatch: {primary_file}")
            reported_is_ucd = int(primary_row["UCD"])
            normalized = {
                "original_name": primary_row["NGVS"],
                "ra": primary_row["RAdeg"],
                "dec": primary_row["DEdeg"],
                "distance_mpc": None,
                "confirmation_status": "candidate" if reported_is_ucd else "not_ucd",
                "is_ucd": reported_is_ucd,
                "gaia_dr3_id": None,
                "host_galaxy": host,
            }
            record_id = insert_literature_record(
                connection,
                dataset_id,
                f"raw_row_{row_number}",
                None,
                normalized,
                {
                    "authoritative_primary_row": primary_row,
                    "authoritative_supporting_row": supporting_row,
                    "supporting_table": supporting_file,
                },
            )
            inserted_records.append(
                {
                    **normalized,
                    "object_id": None,
                    "record_id": record_id,
                    "source_id": source["legacy_source_id"],
                    "source": source,
                    "liu_pending_source_row": True,
                }
            )
    ucd_counts = Counter(record["is_ucd"] for record in inserted_records)
    if ucd_counts != Counter({1: 51, 0: 28}):
        raise RuntimeError(f"Unexpected Liu UCD flags: {ucd_counts}")
    return inserted_records


def ingest_voggel_reference_table(
    connection: sqlite3.Connection, source: dict[str, object]
) -> list[dict[str, object]]:
    """Ingest the 57 previously confirmed Voggel comparison objects."""
    table_path, raw_rows = load_vizier_table("voggel2020", "table4.dat")
    if len(raw_rows) != 57:
        raise RuntimeError(f"Expected 57 Voggel reference rows, found {len(raw_rows)}")
    dataset_id = insert_dataset(
        connection,
        source,
        table_path,
        len(raw_rows),
        authority_status="authoritative_reference_table",
        retrieval_method="vizier_raw_table",
        table_id="table4",
    )
    inserted_records = []
    for row_number, row in enumerate(raw_rows, start=1):
        normalized = {
            "original_name": row["Name"],
            "ra": row["RAdeg"],
            "dec": row["DEdeg"],
            "distance_mpc": None,
            "confirmation_status": "confirmed",
            "is_ucd": 1,
            "gaia_dr3_id": None,
            "host_galaxy": "NGC 5128",
        }
        record_id = insert_literature_record(
            connection,
            dataset_id,
            f"raw_row_{row_number}",
            None,
            normalized,
            row,
        )
        inserted_records.append(
            {
                **normalized,
                "object_id": None,
                "record_id": record_id,
                "source_id": source["legacy_source_id"],
                "source": source,
                "voggel_reference_row": True,
            }
        )
    return inserted_records


def ingest_fahrion_coordinate_null_rows(
    connection: sqlite3.Connection, source: dict[str, object]
) -> list[dict[str, object]]:
    """Preserve four Fahrion rows that lack authoritative coordinates."""
    table_path = PROJECT_ROOT / "reference" / "fahrion2019" / "tableb1.dat"
    raw_rows = []
    for line_number, line in enumerate(
        table_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if line[36:60].strip():
            continue
        raw_rows.append(
            {
                "source_row_locator": f"raw_row_{line_number}",
                "Name": line[:19].strip(),
                "Host": line[20:35].strip(),
                "raw_line": line,
            }
        )
    if len(raw_rows) != 4:
        raise RuntimeError(f"Expected 4 coordinate-null Fahrion rows, found {len(raw_rows)}")
    dataset_id = insert_dataset(
        connection,
        source,
        table_path,
        len(raw_rows),
        authority_status="authoritative_coordinate_null_supplement",
        retrieval_method="vizier_raw_table",
        table_id="tableb1_coordinate_null_rows",
        dataset_name="tableb1_coordinate_null_rows",
    )
    inserted_records = []
    for row in raw_rows:
        normalized = {
            "original_name": row["Name"],
            "ra": None,
            "dec": None,
            "distance_mpc": None,
            "confirmation_status": "confirmed",
            "is_ucd": 1,
            "gaia_dr3_id": None,
            "host_galaxy": row["Host"],
        }
        record_id = insert_literature_record(
            connection,
            dataset_id,
            str(row["source_row_locator"]),
            None,
            normalized,
            row,
        )
        inserted_records.append(
            {
                **normalized,
                "object_id": None,
                "record_id": record_id,
                "source_id": source["legacy_source_id"],
                "source": source,
                "defer_canonical_association": True,
            }
        )
    return inserted_records


def ingest_dumont_records(
    connection: sqlite3.Connection, source: dict[str, object]
) -> list[dict[str, object]]:
    """Ingest all Dumont targets as candidates without overstating UCD identity."""
    table_path, raw_rows = load_dumont_raw_rows()
    dataset_id = insert_dataset(connection, source, table_path, len(raw_rows))
    inserted_records = []
    for row_number, row in enumerate(raw_rows, start=1):
        normalized = {
            "original_name": row.get("ID"),
            "ra": row.get("RAdeg"),
            "dec": row.get("DEdeg"),
            "distance_mpc": 3.8,
            "confirmation_status": "candidate",
            "is_ucd": None,
            "gaia_dr3_id": None,
            "host_galaxy": "NGC 5128",
        }
        record_id = insert_literature_record(
            connection,
            dataset_id,
            f"raw_row_{row_number}",
            None,
            normalized,
            row,
        )
        inserted_records.append(
            {
                **normalized,
                "object_id": None,
                "record_id": record_id,
                "source_id": source["legacy_source_id"],
                "source": source,
            }
        )
    return inserted_records


def insert_literature_record(
    connection: sqlite3.Connection,
    dataset_id: str,
    source_row_locator: str,
    legacy_object_id: str | None,
    normalized: dict[str, object],
    raw_payload: dict[str, object],
) -> str:
    """Insert one immutable literature record."""
    record_id = stable_identifier("record", f"{dataset_id}:{source_row_locator}")
    connection.execute(
        """
        INSERT INTO literature_records (
            record_id, dataset_id, source_row_locator, legacy_object_id,
            original_name, ra, dec, host_galaxy, distance_mpc,
            reported_confirmation_status, reported_is_ucd, gaia_dr3_id,
            raw_payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record_id,
            dataset_id,
            source_row_locator,
            legacy_object_id,
            normalize_scalar(normalized.get("original_name")),
            parse_float(normalized.get("ra")),
            parse_float(normalized.get("dec")),
            normalize_scalar(normalized.get("host_galaxy")),
            parse_float(normalized.get("distance_mpc")),
            normalize_scalar(normalized.get("confirmation_status")),
            parse_integer(normalized.get("is_ucd")),
            normalize_scalar(normalized.get("gaia_dr3_id")),
            json.dumps(raw_payload, sort_keys=True, default=str),
        ),
    )
    return record_id


def ingest_records(
    connection: sqlite3.Connection,
    legacy_database: Path,
    catalog_directory: Path,
    sources_by_legacy_id: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    """Ingest legacy rows and the missing Zhang catalog without altering inputs."""
    with connect_read_only(legacy_database) as legacy_connection:
        legacy_rows = load_legacy_rows(legacy_connection)
    rows_by_source = defaultdict(list)
    for row in legacy_rows:
        rows_by_source[str(row["source_id"])].append(row)

    inserted_records = []
    for legacy_source_id, source in sources_by_legacy_id.items():
        if source["bibcode"] == "2022ApJ...929..147D":
            inserted_records.extend(ingest_dumont_records(connection, source))
            continue
        catalog_path = catalog_directory / f"{legacy_source_id}.csv"
        if not catalog_path.exists():
            raise FileNotFoundError(catalog_path)
        source_rows = rows_by_source.get(legacy_source_id, [])
        if source_rows:
            if source["bibcode"] == "2021MNRAS.504.3580S":
                inserted_records.extend(
                    ingest_saifollahi_legacy_records(
                        connection,
                        source,
                        catalog_path,
                        source_rows,
                    )
                )
                inserted_records.extend(ingest_saifollahi_candidate_tables(connection, source))
                continue
            dataset_id = insert_dataset(connection, source, catalog_path, len(source_rows))
            liu_primary_rows = None
            if source["bibcode"] == "2015ApJ...812...34L":
                _, liu_primary_rows = load_vizier_table("liu2015", "table2.dat")
                if len(liu_primary_rows) != len(source_rows):
                    raise RuntimeError("Liu M87 legacy and authoritative row counts differ")
            for row_index, row in enumerate(source_rows):
                normalized = dict(row)
                if source["bibcode"] == "2007A&A...472..111M":
                    normalized["distance_mpc"] = 43.0
                elif source["bibcode"] == "2019A&A...625A..50F":
                    normalized["distance_mpc"] = None
                elif source["bibcode"] == "2015ApJ...812...34L":
                    primary_row = liu_primary_rows[row_index]
                    if (float(row["ra"]), float(row["dec"])) != (
                        float(primary_row["RAdeg"]),
                        float(primary_row["DEdeg"]),
                    ):
                        raise RuntimeError(f"Liu M87 row order changed at index {row_index}")
                    normalized["original_name"] = str(primary_row["NGVS"])
                    normalized["is_ucd"] = int(primary_row["UCD"])
                    normalized["confirmation_status"] = (
                        "candidate" if normalized["is_ucd"] else "not_ucd"
                    )
                    normalized["host_galaxy"] = "M87"
                record_id = insert_literature_record(
                    connection,
                    dataset_id,
                    str(row["object_id"]),
                    str(row["object_id"]),
                    normalized,
                    row,
                )
                inserted_records.append({**normalized, "record_id": record_id, "source": source})
            if source["bibcode"] == "2015ApJ...812...34L":
                inserted_records.extend(ingest_liu_pending_tables(connection, source))
            elif source["bibcode"] == "2019A&A...625A..50F":
                inserted_records.extend(ingest_fahrion_coordinate_null_rows(connection, source))
            elif source["bibcode"] == "2020ApJ...899..140V":
                inserted_records.extend(ingest_voggel_reference_table(connection, source))
            continue

        raw_table_path, catalog_rows = load_zhang_raw_rows()
        dataset_id = insert_dataset(connection, source, raw_table_path, len(catalog_rows))
        for row_number, row in enumerate(catalog_rows, start=1):
            normalized = {
                "original_name": row.get("ID"),
                "ra": row.get("RAdeg"),
                "dec": row.get("DEdeg"),
                "distance_mpc": None,
                "confirmation_status": "confirmed",
                "is_ucd": 1,
                "gaia_dr3_id": None,
                "host_galaxy": "M87",
            }
            record_id = insert_literature_record(
                connection,
                dataset_id,
                f"raw_row_{row_number}",
                None,
                normalized,
                row,
            )
            inserted_records.append(
                {
                    **normalized,
                    "object_id": None,
                    "record_id": record_id,
                    "source_id": legacy_source_id,
                    "source": source,
                }
            )
    return inserted_records


def normalized_object_name(value: object) -> str:
    """Normalize an object name for approved exact-name associations."""
    return " ".join(str(value).strip().lower().split())


def prepare_approved_source_associations(
    records: list[dict[str, object]], association_reviews: list[dict[str, object]]
) -> None:
    """Annotate approved Liu and Voggel links to existing provenance records."""
    approved_alias_reviews = {
        normalized_object_name(review["source_name"]): review
        for review in association_reviews
        if review["decision"] == "same_astrophysical_object"
    }
    fahrion_by_name = {
        normalized_object_name(record["original_name"]): record
        for record in records
        if record["source"]["bibcode"] == "2019A&A...625A..50F"
        and not record.get("defer_canonical_association")
    }
    baseline_records = [
        record
        for record in records
        if record["source"]["bibcode"] in {"2019A&A...625A..50F", "2022ApJ...929..147D"}
        and record.get("ra") is not None
        and record.get("dec") is not None
    ]
    baseline_coordinates = SkyCoord(
        ra=[float(record["ra"]) for record in baseline_records] * u.deg,
        dec=[float(record["dec"]) for record in baseline_records] * u.deg,
    )

    liu_association_count = 0
    for record in records:
        if not record.get("liu_pending_source_row") or record.get("is_ucd") != 1:
            continue
        anchor = fahrion_by_name.get(normalized_object_name(record["original_name"]))
        if anchor is None:
            raise RuntimeError(
                f"Approved Liu association lacks Fahrion name: {record['original_name']}"
            )
        source_coordinate = SkyCoord(float(record["ra"]) * u.deg, float(record["dec"]) * u.deg)
        anchor_coordinate = SkyCoord(float(anchor["ra"]) * u.deg, float(anchor["dec"]) * u.deg)
        separation_arcsec = float(source_coordinate.separation(anchor_coordinate).arcsec)
        if separation_arcsec > 1.0:
            raise RuntimeError(
                f"Approved Liu association exceeds 1 arcsec: {record['original_name']}"
            )
        record["association_anchor_record"] = anchor
        record["approved_association_separation_arcsec"] = separation_arcsec
        record["approved_association_method"] = "approved_name_and_spherical_match"
        liu_association_count += 1
    if liu_association_count != 51:
        raise RuntimeError(f"Expected 51 approved Liu associations, found {liu_association_count}")

    voggel_counts = Counter()
    for record in records:
        if not record.get("voggel_reference_row"):
            continue
        source_coordinate = SkyCoord(float(record["ra"]) * u.deg, float(record["dec"]) * u.deg)
        separations = source_coordinate.separation(baseline_coordinates).arcsec
        nearest_index = int(np.argmin(separations))
        separation_arcsec = float(separations[nearest_index])
        anchor = baseline_records[nearest_index]
        alias_review = approved_alias_reviews.get(normalized_object_name(record["original_name"]))
        if alias_review:
            if (
                normalized_object_name(anchor["original_name"])
                != normalized_object_name(alias_review["target_name"])
                or anchor["source"]["bibcode"] != alias_review["target_bibcode"]
                or abs(separation_arcsec - float(alias_review["separation_arcsec"])) > 1e-9
            ):
                raise RuntimeError(
                    f"Approved alias review no longer matches: {record['original_name']}"
                )
            record["association_anchor_record"] = anchor
            record["approved_association_separation_arcsec"] = separation_arcsec
            record["approved_association_method"] = alias_review["association_method"]
            record["association_review"] = alias_review
            voggel_counts["approved_alias"] += 1
        elif separation_arcsec <= 1.0:
            record["association_anchor_record"] = anchor
            record["approved_association_separation_arcsec"] = separation_arcsec
            record["approved_association_method"] = "approved_spherical_match"
            voggel_counts["approved"] += 1
        elif separation_arcsec <= 5.0:
            raise RuntimeError(
                f"Unreviewed Voggel association within 5 arcsec: {record['original_name']}"
            )
        else:
            voggel_counts["new_reference_object"] += 1
    expected_voggel_counts = Counter(
        {"approved": 34, "approved_alias": 1, "new_reference_object": 22}
    )
    if voggel_counts != expected_voggel_counts:
        raise RuntimeError(f"Unexpected Voggel association roles: {voggel_counts}")


def prepare_approved_wave1_identity(
    records: list[dict[str, object]],
) -> dict[str, object]:
    """Apply the separately approved S999 identity consolidation."""
    with WAVE1_IDENTITY_REVIEW_MANIFEST.open(encoding="utf-8") as input_file:
        manifest = json.load(input_file)
    if manifest["review_status"] != "approved_by_project_lead_2026-07-15":
        raise RuntimeError("Wave 1 identity review lacks project-lead approval")
    reviews = manifest["reviews"]
    if len(reviews) != 1:
        raise RuntimeError(f"Expected one Wave 1 identity review, found {len(reviews)}")
    review = reviews[0]
    if review.get("decision") != "same_astrophysical_object" or not review.get(
        "identity_changes_authorized"
    ):
        raise RuntimeError("S999 identity consolidation is not authorized")

    def find_record(bibcode: str, name: str) -> dict[str, object]:
        matches = [
            record
            for record in records
            if record["source"]["bibcode"] == bibcode
            and normalized_object_name(record["original_name"]) == normalized_object_name(name)
        ]
        if len(matches) != 1:
            raise RuntimeError(f"Expected one {bibcode} {name} record, found {len(matches)}")
        return matches[0]

    fahrion_record = find_record("2019A&A...625A..50F", "S999")
    zhang_record = find_record("2015ApJ...802...30Z", "S999")
    ko_record = find_record("2017ApJ...835..212K", "S999")
    liu_matches = [
        record
        for record in records
        if record["source"]["bibcode"] == "2020ApJS..250...17L"
        and "S999" in record.get("wave1_aliases", [])
    ]
    if len(liu_matches) != 1:
        raise RuntimeError(f"Expected one Liu S999 alias record, found {len(liu_matches)}")
    liu_record = liu_matches[0]

    current_fahrion_canonical = stable_identifier("canonical", str(fahrion_record["record_id"]))
    current_zhang_canonical = stable_identifier("canonical", str(zhang_record["record_id"]))
    reviewed_ids = set(review["canonical_object_ids"])
    if reviewed_ids != {current_fahrion_canonical, current_zhang_canonical}:
        raise RuntimeError("S999 reviewed canonical identifiers no longer match the builder")

    anchor_coordinate = SkyCoord(
        float(fahrion_record["ra"]) * u.deg,
        float(fahrion_record["dec"]) * u.deg,
    )
    for record in (zhang_record, ko_record, liu_record):
        source_coordinate = SkyCoord(float(record["ra"]) * u.deg, float(record["dec"]) * u.deg)
        record["association_anchor_record"] = fahrion_record
        record["approved_association_separation_arcsec"] = float(
            source_coordinate.separation(anchor_coordinate).arcsec
        )
        record["approved_association_method"] = "approved_s999_literature_identity"
        record["wave1_identity_review"] = review
    fahrion_record["wave1_identity_review"] = review
    fahrion_record.setdefault("retired_canonical_aliases", []).append(current_zhang_canonical)
    fahrion_record.setdefault("retired_canonical_alias_reasons", {})[current_zhang_canonical] = (
        "Approved S999 literature identity consolidation"
    )
    return review


def prepare_approved_wave1_identity_proposals(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Apply the seven approved name-led Wave 1 associations."""
    with WAVE1_IDENTITY_PROPOSAL_MANIFEST.open(encoding="utf-8") as input_file:
        manifest = json.load(input_file)
    if manifest["review_status"] != "approved_by_project_lead_2026-07-15":
        raise RuntimeError("Wave 1 identity proposal cohort lacks project-lead approval")
    proposals = manifest["proposals"]
    if manifest["proposal_count"] != 7 or len(proposals) != 7:
        raise RuntimeError(f"Expected seven approved Wave 1 proposals, found {len(proposals)}")
    records_by_id = {str(record["record_id"]): record for record in records}
    seen_wave_records = set()
    for proposal in proposals:
        if (
            proposal["review_status"] != "approved_by_project_lead_2026-07-15"
            or proposal["decision"] != "same_astrophysical_object"
            or not proposal["identity_changes_authorized"]
        ):
            raise RuntimeError(f"Wave 1 proposal is not authorized: {proposal['proposal_id']}")
        wave_record_id = str(proposal["wave_record_id"])
        target_anchor_record_id = str(proposal["target_anchor_record_id"])
        if wave_record_id in seen_wave_records:
            raise RuntimeError(f"Wave 1 record is approved twice: {wave_record_id}")
        seen_wave_records.add(wave_record_id)
        wave_record = records_by_id.get(wave_record_id)
        target_anchor = records_by_id.get(target_anchor_record_id)
        if wave_record is None or target_anchor is None:
            raise RuntimeError(
                f"Approved Wave 1 proposal record is missing: {proposal['proposal_id']}"
            )
        if wave_record.get("association_anchor_record"):
            raise RuntimeError(f"Approved Wave 1 record already has an anchor: {wave_record_id}")
        target_canonical_object_id = stable_identifier("canonical", str(target_anchor["record_id"]))
        if target_canonical_object_id != proposal["target_canonical_object_id"]:
            raise RuntimeError(f"Reviewed Wave 1 target changed: {proposal['proposal_id']}")
        retired_wave_canonical_object_id = stable_identifier(
            "canonical", str(wave_record["record_id"])
        )
        if retired_wave_canonical_object_id != proposal["retired_wave_canonical_object_id"]:
            raise RuntimeError(
                f"Reviewed Wave 1 source identity changed: {proposal['proposal_id']}"
            )
        source_coordinate = SkyCoord(
            float(wave_record["ra"]) * u.deg,
            float(wave_record["dec"]) * u.deg,
        )
        target_coordinate = SkyCoord(
            float(target_anchor["ra"]) * u.deg,
            float(target_anchor["dec"]) * u.deg,
        )
        separation_arcsec = float(source_coordinate.separation(target_coordinate).arcsec)
        if abs(separation_arcsec - float(proposal["separation_arcsec"])) > 1e-9:
            raise RuntimeError(f"Reviewed Wave 1 separation changed: {proposal['proposal_id']}")
        wave_record["association_anchor_record"] = target_anchor
        wave_record["approved_association_separation_arcsec"] = separation_arcsec
        wave_record["approved_association_method"] = "approved_wave1_name_or_alias_identity"
        wave_record["approved_wave1_identity_proposal"] = proposal
        target_anchor.setdefault("retired_canonical_aliases", []).append(
            retired_wave_canonical_object_id
        )
        target_anchor.setdefault("retired_canonical_alias_reasons", {})[
            retired_wave_canonical_object_id
        ] = "Approved Wave 1 direct-name or published-alias identity"
    return proposals


def effective_coordinate(record: dict[str, object]) -> tuple[float, float]:
    """Return the coordinate currently used to form a canonical group."""
    anchor = record.get("association_anchor_record")
    position_record = anchor if anchor else record
    return float(position_record["ra"]), float(position_record["dec"])


def map_current_canonical_records(
    records: list[dict[str, object]],
) -> tuple[dict[str, list[dict[str, object]]], dict[str, dict[str, object]]]:
    """Reconstruct current canonical groups before a subsequent approved review."""
    records_by_effective_coordinate = defaultdict(list)
    for record in records:
        if record.get("defer_canonical_association"):
            continue
        records_by_effective_coordinate[effective_coordinate(record)].append(record)

    records_by_current_canonical = {}
    anchor_record_by_current_canonical = {}
    for coordinate, coordinate_records in records_by_effective_coordinate.items():
        position_records = [
            record
            for record in coordinate_records
            if float(record["ra"]) == coordinate[0] and float(record["dec"]) == coordinate[1]
        ]
        if not position_records:
            raise RuntimeError(f"Canonical coordinate lacks a position record: {coordinate}")
        anchor_record = min(position_records, key=lambda row: str(row["record_id"]))
        canonical_object_id = stable_identifier("canonical", str(anchor_record["record_id"]))
        records_by_current_canonical[canonical_object_id] = coordinate_records
        anchor_record_by_current_canonical[canonical_object_id] = anchor_record
    return records_by_current_canonical, anchor_record_by_current_canonical


def prepare_approved_wave1_group_identities(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Apply the 12 approved multi-canonical Wave 1 identity groups."""
    with WAVE1_GROUP_IDENTITY_PROPOSAL_MANIFEST.open(encoding="utf-8") as input_file:
        manifest = json.load(input_file)
    approval_status = "approved_by_project_lead_2026-07-15"
    if manifest["review_status"] != approval_status:
        raise RuntimeError("Wave 1 group identity cohort lacks project-lead approval")
    proposals = manifest["proposals"]
    if manifest["proposal_group_count"] != 12 or len(proposals) != 12:
        raise RuntimeError(f"Expected 12 approved Wave 1 group proposals, found {len(proposals)}")

    records_by_current_canonical, anchor_record_by_current_canonical = (
        map_current_canonical_records(records)
    )

    seen_current_canonical_ids = set()
    for proposal in proposals:
        group_id = str(proposal["group_id"])
        if (
            proposal["review_status"] != approval_status
            or proposal["decision"] != "same_astrophysical_object"
            or not proposal["identity_changes_authorized"]
        ):
            raise RuntimeError(f"Wave 1 group proposal is not authorized: {group_id}")
        if proposal["recommended_classification_treatment"] != "derive_without_identity_conflict":
            raise RuntimeError(f"Unexpected Wave 1 group classification treatment: {group_id}")

        current_canonical_ids = set(proposal["current_canonical_object_ids"])
        if current_canonical_ids & seen_current_canonical_ids:
            raise RuntimeError(f"Wave 1 group canonical appears twice: {group_id}")
        seen_current_canonical_ids.update(current_canonical_ids)
        missing_canonical_ids = current_canonical_ids - records_by_current_canonical.keys()
        if missing_canonical_ids:
            raise RuntimeError(
                f"Reviewed Wave 1 group identities changed for {group_id}: "
                f"{sorted(missing_canonical_ids)}"
            )
        reviewed_baseline_ids = set(proposal["baseline_canonical_object_ids"])
        if not reviewed_baseline_ids <= current_canonical_ids:
            raise RuntimeError(f"Wave 1 group baseline membership changed: {group_id}")
        reviewed_wave_record_ids = set(proposal["wave_record_ids"])
        current_group_record_ids = {
            str(record["record_id"])
            for canonical_object_id in current_canonical_ids
            for record in records_by_current_canonical[canonical_object_id]
        }
        if not reviewed_wave_record_ids <= current_group_record_ids:
            raise RuntimeError(f"Wave 1 group row membership changed: {group_id}")
        recommended_anchor_canonical_id = str(proposal["recommended_anchor_canonical_object_id"])
        if recommended_anchor_canonical_id not in current_canonical_ids:
            raise RuntimeError(f"Wave 1 group anchor is outside its reviewed group: {group_id}")
        anchor_record = anchor_record_by_current_canonical[recommended_anchor_canonical_id]
        anchor_coordinate = SkyCoord(
            float(anchor_record["ra"]) * u.deg,
            float(anchor_record["dec"]) * u.deg,
        )
        anchor_record.setdefault("approved_wave1_group_identity_evidence", []).append(proposal)

        for canonical_object_id in sorted(current_canonical_ids):
            if canonical_object_id == recommended_anchor_canonical_id:
                continue
            source_anchor = anchor_record_by_current_canonical[canonical_object_id]
            source_coordinate = SkyCoord(
                float(source_anchor["ra"]) * u.deg,
                float(source_anchor["dec"]) * u.deg,
            )
            separation_arcsec = float(source_coordinate.separation(anchor_coordinate).arcsec)
            for record in records_by_current_canonical[canonical_object_id]:
                record["association_anchor_record"] = anchor_record
                record["approved_association_separation_arcsec"] = separation_arcsec
                record["approved_association_method"] = "approved_wave1_group_identity"
                record["approved_wave1_group_identity_proposal"] = proposal
            anchor_record.setdefault("retired_canonical_aliases", []).append(canonical_object_id)
            anchor_record.setdefault("retired_canonical_alias_reasons", {})[canonical_object_id] = (
                "Approved Wave 1 multi-canonical shared-identifier identity"
            )

    if len(seen_current_canonical_ids) != 40:
        raise RuntimeError(
            "Expected 40 reviewed current canonicals across Wave 1 group identities, "
            f"found {len(seen_current_canonical_ids)}"
        )
    return proposals


def prepare_approved_wave1_remaining_identities(
    records: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Apply the delegated source audit for all 79 remaining review groups."""
    with WAVE1_REMAINING_IDENTITY_REVIEW_MANIFEST.open(encoding="utf-8") as input_file:
        manifest = json.load(input_file)
    approval_status = "approved_by_project_lead_delegation_2026-07-15"
    if manifest["review_status"] != approval_status:
        raise RuntimeError("Remaining Wave 1 source identities lack delegated approval")
    proposals = manifest["proposals"]
    if len(proposals) != 80 or manifest["summary"]["proposed_identity_count"] != 80:
        raise RuntimeError(
            f"Expected 80 approved remaining Wave 1 identities, found {len(proposals)}"
        )

    records_by_current_canonical, anchor_record_by_current_canonical = (
        map_current_canonical_records(records)
    )
    seen_current_canonical_ids = set()
    retired_canonical_count = 0
    for proposal in proposals:
        decision_id = str(proposal["decision_id"])
        if (
            proposal["review_status"] != approval_status
            or proposal["decision"] != "same_astrophysical_object"
            or not proposal["identity_changes_authorized"]
        ):
            raise RuntimeError(f"Remaining Wave 1 identity is not authorized: {decision_id}")
        current_canonical_ids = set(proposal["current_canonical_object_ids"])
        if current_canonical_ids & seen_current_canonical_ids:
            raise RuntimeError(f"Remaining Wave 1 canonical appears twice: {decision_id}")
        seen_current_canonical_ids.update(current_canonical_ids)
        missing_canonical_ids = current_canonical_ids - records_by_current_canonical.keys()
        if missing_canonical_ids:
            raise RuntimeError(
                f"Remaining Wave 1 source identities changed for {decision_id}: "
                f"{sorted(missing_canonical_ids)}"
            )
        recommended_anchor_canonical_id = str(proposal["recommended_anchor_canonical_object_id"])
        if recommended_anchor_canonical_id not in current_canonical_ids:
            raise RuntimeError(f"Remaining Wave 1 anchor is outside its identity: {decision_id}")
        anchor_record = anchor_record_by_current_canonical[recommended_anchor_canonical_id]
        anchor_coordinate = SkyCoord(
            float(anchor_record["ra"]) * u.deg,
            float(anchor_record["dec"]) * u.deg,
        )
        anchor_record.setdefault("approved_wave1_remaining_identity_evidence", []).append(proposal)
        classification_treatment = proposal["recommended_classification_treatment"]
        if classification_treatment == "uncertain_reported_ucd_role_conflict":
            anchor_record["approved_classification_subtype"] = "reported_ucd_role_conflict"
        elif classification_treatment != "derive_without_identity_conflict":
            raise RuntimeError(
                f"Unexpected remaining Wave 1 classification treatment: {decision_id}"
            )

        for canonical_object_id in sorted(current_canonical_ids):
            source_anchor = anchor_record_by_current_canonical[canonical_object_id]
            for record in records_by_current_canonical[canonical_object_id]:
                record["approved_wave1_remaining_identity_proposal"] = proposal
            if canonical_object_id == recommended_anchor_canonical_id:
                continue
            source_coordinate = SkyCoord(
                float(source_anchor["ra"]) * u.deg,
                float(source_anchor["dec"]) * u.deg,
            )
            separation_arcsec = float(source_coordinate.separation(anchor_coordinate).arcsec)
            for record in records_by_current_canonical[canonical_object_id]:
                record["association_anchor_record"] = anchor_record
                record["approved_association_separation_arcsec"] = separation_arcsec
                record["approved_association_method"] = "approved_wave1_source_identity"
            anchor_record.setdefault("retired_canonical_aliases", []).append(canonical_object_id)
            anchor_record.setdefault("retired_canonical_alias_reasons", {})[canonical_object_id] = (
                "Approved Wave 1 source-catalog identity lineage"
            )
            retired_canonical_count += 1

    if len(seen_current_canonical_ids) != 309 or retired_canonical_count != 229:
        raise RuntimeError(
            "Expected 309 current canonicals and 229 retired identities in the remaining "
            f"Wave 1 audit, found {len(seen_current_canonical_ids)} and "
            f"{retired_canonical_count}"
        )
    return proposals


def load_approved_gaia_groups(
    review: dict[str, object],
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    dict[str, dict[str, str]],
]:
    """Load and verify all project-approved Gaia review cohorts."""
    review_path = PROJECT_ROOT / str(review["review_artifact"])
    image_review_path = PROJECT_ROOT / str(review["image_review_artifact"])
    multi_position_review_path = PROJECT_ROOT / str(review["multi_position_review_artifact"])
    gaia_cache_path = PROJECT_ROOT / str(review["gaia_source_cache"])
    if calculate_sha256(review_path) != review["review_artifact_sha256"]:
        raise RuntimeError("Gaia review artifact SHA-256 does not match approval manifest")
    if calculate_sha256(gaia_cache_path) != review["gaia_source_cache_sha256"]:
        raise RuntimeError("Gaia source cache SHA-256 does not match approval manifest")
    if calculate_sha256(image_review_path) != review["image_review_artifact_sha256"]:
        raise RuntimeError("Gaia image-review artifact SHA-256 does not match approval manifest")
    if (
        calculate_sha256(multi_position_review_path)
        != review["multi_position_review_artifact_sha256"]
    ):
        raise RuntimeError(
            "Gaia multi-position review artifact SHA-256 does not match approval manifest"
        )

    with review_path.open(encoding="utf-8", newline="") as input_file:
        reviewed_groups = list(csv.DictReader(input_file))
    approved_groups = []
    for cohort in review["approved_cohorts"]:
        cohort_groups = [
            {
                **row,
                "approved_classification_subtype": cohort["classification_subtype"],
            }
            for row in reviewed_groups
            if row[str(review["selection_field"])] == cohort["selection_value"]
        ]
        if len(cohort_groups) != int(cohort["approved_group_count"]):
            raise RuntimeError(
                f"Unexpected approved Gaia cohort count for {cohort['selection_value']}: "
                f"{len(cohort_groups)}"
            )
        approved_groups.extend(cohort_groups)
    if len(approved_groups) != int(review["historical_approved_group_count"]):
        raise RuntimeError(
            f"Unexpected historical approved Gaia group count: {len(approved_groups)}"
        )

    with image_review_path.open(encoding="utf-8", newline="") as input_file:
        image_review_rows = list(csv.DictReader(input_file))
    image_approved_groups = [
        {
            **row,
            "canonical_position_count": "2",
            "approved_classification_subtype": None,
        }
        for row in image_review_rows
        if row[str(review["image_review_selection_field"])]
        == review["image_approved_selection_value"]
    ]
    separate_groups = [
        row
        for row in image_review_rows
        if row[str(review["image_review_selection_field"])]
        == review["image_separate_selection_value"]
    ]
    if len(image_approved_groups) != int(review["image_approved_group_count"]):
        raise RuntimeError(
            f"Unexpected image-approved Gaia group count: {len(image_approved_groups)}"
        )
    if len(separate_groups) != int(review["image_separate_group_count"]):
        raise RuntimeError(f"Unexpected separate shared-Gaia group count: {len(separate_groups)}")
    if any(
        row["identity_decision"] != "approved_same_astrophysical_object"
        for row in image_approved_groups
    ):
        raise RuntimeError("Image-approved Gaia group lacks an approved identity decision")
    if any(
        row["identity_decision"] != "approved_retain_separate_shared_gaia_source"
        for row in separate_groups
    ):
        raise RuntimeError("Separate shared-Gaia group lacks an approved identity decision")
    approved_groups.extend(image_approved_groups)

    with multi_position_review_path.open(encoding="utf-8", newline="") as input_file:
        multi_position_review_rows = list(csv.DictReader(input_file))
    multi_position_approved_groups = [
        {
            **row,
            "approved_classification_subtype": None,
        }
        for row in multi_position_review_rows
        if row[str(review["multi_position_selection_field"])]
        == review["multi_position_approved_selection_value"]
    ]
    if len(multi_position_review_rows) != int(review["multi_position_approved_group_count"]):
        raise RuntimeError(
            f"Unexpected Gaia multi-position review row count: {len(multi_position_review_rows)}"
        )
    if len(multi_position_approved_groups) != int(review["multi_position_approved_group_count"]):
        raise RuntimeError(
            "Unexpected approved Gaia multi-position group count: "
            f"{len(multi_position_approved_groups)}"
        )
    if any(
        row["identity_decision"] != "approved_same_astrophysical_object"
        for row in multi_position_approved_groups
    ):
        raise RuntimeError("Multi-position Gaia group lacks an approved identity decision")
    approved_groups.extend(multi_position_approved_groups)
    approved_ids = [group["gaia_dr3_id"] for group in approved_groups]
    separate_ids = [group["gaia_dr3_id"] for group in separate_groups]
    reviewed_ids = {group["gaia_dr3_id"] for group in reviewed_groups}
    if len(image_review_rows) != 23:
        raise RuntimeError(f"Unexpected Gaia image-review row count: {len(image_review_rows)}")
    if not set(approved_ids + separate_ids).issubset(reviewed_ids):
        raise RuntimeError("Gaia approval contains a source outside the frozen cohort")
    if len(approved_ids + separate_ids) != len(set(approved_ids + separate_ids)):
        raise RuntimeError("Approved and separate Gaia review groups overlap")
    if len(approved_groups) != int(review["approved_group_count"]):
        raise RuntimeError(f"Unexpected total approved Gaia group count: {len(approved_groups)}")
    retained_count = len(reviewed_groups) - len(approved_groups) - len(separate_groups)
    if retained_count != int(review["retained_review_group_count"]):
        raise RuntimeError("Unexpected retained Gaia review group count")

    with gaia_cache_path.open(encoding="utf-8", newline="") as input_file:
        gaia_sources = {row["source_id"]: row for row in csv.DictReader(input_file)}
    return reviewed_groups, approved_groups, separate_groups, gaia_sources


def prepare_approved_gaia_associations(
    records: list[dict[str, object]], review: dict[str, object]
) -> None:
    """Merge only the approved two-position groups using Gaia-reviewed geometry."""
    reviewed_groups, approved_groups, separate_groups, gaia_sources = load_approved_gaia_groups(
        review
    )
    records_by_gaia_id = defaultdict(list)
    records_by_coordinate = defaultdict(list)
    for record in records:
        if record.get("defer_canonical_association"):
            continue
        records_by_coordinate[effective_coordinate(record)].append(record)
        gaia_dr3_id = normalize_scalar(record.get("gaia_dr3_id"))
        if gaia_dr3_id is not None:
            records_by_gaia_id[str(gaia_dr3_id)].append(record)

    for association in review.get("supplemental_identity_associations", []):
        source_records = [
            record
            for record in records
            if record["source"]["bibcode"] == association["source_bibcode"]
            and record.get("original_name") == association["object_name"]
        ]
        target_records = [
            record
            for record in records
            if record["source"]["bibcode"] == association["target_bibcode"]
            and record.get("original_name") == association["object_name"]
        ]
        if len(source_records) != 1 or len(target_records) != 1:
            raise RuntimeError(
                f"Unexpected supplemental identity records for {association['object_name']}: "
                f"source={len(source_records)}, target={len(target_records)}"
            )
        source_record = source_records[0]
        target_record = target_records[0]
        source_coordinate = SkyCoord(
            float(source_record["ra"]) * u.deg, float(source_record["dec"]) * u.deg
        )
        target_coordinate = SkyCoord(
            float(target_record["ra"]) * u.deg, float(target_record["dec"]) * u.deg
        )
        separation_arcsec = float(source_coordinate.separation(target_coordinate).arcsec)
        if separation_arcsec > float(association["maximum_separation_arcsec"]):
            raise RuntimeError(
                f"Supplemental identity exceeds approved separation: {association['object_name']}"
            )
        if source_record.get("association_anchor_record"):
            raise RuntimeError(
                f"Supplemental identity source already associated: {association['object_name']}"
            )
        source_record["association_anchor_record"] = target_record
        source_record["approved_association_separation_arcsec"] = separation_arcsec
        source_record["approved_association_method"] = association["association_method"]
        retired_canonical_object_id = stable_identifier(
            "canonical", str(source_record["record_id"])
        )
        target_record.setdefault("retired_canonical_aliases", []).append(
            retired_canonical_object_id
        )
        target_record.setdefault("retired_canonical_alias_reasons", {})[
            retired_canonical_object_id
        ] = "Approved S547 name and spherical identity review"
        target_record.setdefault("approved_supplemental_identity_evidence", []).append(
            {
                **association,
                "source_record_id": source_record["record_id"],
                "target_record_id": target_record["record_id"],
                "measured_separation_arcsec": separation_arcsec,
            }
        )

    used_coordinates = set()
    approved_gaia_ids = {group["gaia_dr3_id"] for group in approved_groups}
    for group in reviewed_groups:
        if group["gaia_dr3_id"] in approved_gaia_ids:
            continue
        for record in records_by_gaia_id[group["gaia_dr3_id"]]:
            record["gaia_review_action"] = group["recommended_action"]

    for group in separate_groups:
        gaia_dr3_id = group["gaia_dr3_id"]
        gaia_records = records_by_gaia_id[gaia_dr3_id]
        group_coordinates = sorted({effective_coordinate(record) for record in gaia_records})
        if len(group_coordinates) != 2:
            raise RuntimeError(f"Reviewed separate Gaia group is not two-position: {gaia_dr3_id}")
        for coordinate in group_coordinates:
            position_records = [
                record
                for record in records_by_coordinate[coordinate]
                if record.get("ra") is not None
                and (float(record["ra"]), float(record["dec"])) == coordinate
            ]
            if not position_records:
                raise RuntimeError(
                    f"Reviewed separate Gaia position has no native record: {gaia_dr3_id}"
                )
            evidence_record = min(position_records, key=lambda row: str(row["record_id"]))
            evidence_record.setdefault("approved_gaia_ambiguity_evidence", []).append(
                {
                    "gaia_dr3_id": gaia_dr3_id,
                    "review_id": review["review_id"],
                    "review_status": review["review_status"],
                    "decision": group["identity_decision"],
                    "evidence_type": review["separate_shared_source_evidence_type"],
                    "evidence_value": review["separate_shared_source_evidence_value"],
                    "literature_coordinate": coordinate,
                    "literature_position_separation_arcsec": float(
                        group["literature_position_separation_arcsec"]
                    ),
                    "review_rationale": group["review_rationale"],
                }
            )
        for record in gaia_records:
            record["reviewed_separate_gaia_dr3_id"] = gaia_dr3_id

    for group in approved_groups:
        gaia_dr3_id = group["gaia_dr3_id"]
        gaia_records = records_by_gaia_id[gaia_dr3_id]
        group_coordinates = sorted({effective_coordinate(record) for record in gaia_records})
        expected_position_count = int(group["canonical_position_count"])
        if (
            expected_position_count not in {2, 3}
            or len(group_coordinates) != expected_position_count
        ):
            raise RuntimeError(
                f"Approved Gaia group position count changed: {gaia_dr3_id}, "
                f"expected={expected_position_count}, found={len(group_coordinates)}"
            )
        if used_coordinates.intersection(group_coordinates):
            raise RuntimeError(f"Approved Gaia groups overlap in canonical position: {gaia_dr3_id}")
        used_coordinates.update(group_coordinates)

        gaia_source = gaia_sources[gaia_dr3_id]
        gaia_coordinate = SkyCoord(
            float(gaia_source["ra"]) * u.deg, float(gaia_source["dec"]) * u.deg
        )
        coordinate_distances = []
        for coordinate in group_coordinates:
            literature_coordinate = SkyCoord(coordinate[0] * u.deg, coordinate[1] * u.deg)
            coordinate_distances.append(
                (float(literature_coordinate.separation(gaia_coordinate).arcsec), coordinate)
            )
        _, anchor_coordinate = min(coordinate_distances)
        secondary_coordinates = [
            coordinate for coordinate in group_coordinates if coordinate != anchor_coordinate
        ]
        position_records = [
            record
            for record in records_by_coordinate[anchor_coordinate]
            if record.get("ra") is not None
            and (float(record["ra"]), float(record["dec"])) == anchor_coordinate
        ]
        if not position_records:
            raise RuntimeError(f"Approved Gaia anchor has no native position: {gaia_dr3_id}")
        anchor_record = min(position_records, key=lambda row: str(row["record_id"]))

        for secondary_coordinate in secondary_coordinates:
            retired_position_records = [
                record
                for record in records_by_coordinate[secondary_coordinate]
                if record.get("ra") is not None
                and (float(record["ra"]), float(record["dec"])) == secondary_coordinate
            ]
            retired_anchor_record = min(
                retired_position_records, key=lambda row: str(row["record_id"])
            )
            retired_canonical_object_id = stable_identifier(
                "canonical", str(retired_anchor_record["record_id"])
            )
            anchor_record.setdefault("retired_canonical_aliases", []).append(
                retired_canonical_object_id
            )
            anchor_record.setdefault("retired_canonical_alias_reasons", {})[
                retired_canonical_object_id
            ] = "Approved shared Gaia DR3 identity review"
        anchor_record.setdefault("approved_gaia_identity_evidence", []).append(
            {
                "gaia_dr3_id": gaia_dr3_id,
                "review_id": review["review_id"],
                "review_status": review["review_status"],
                "decision": review["decision"],
                "association_method": review["association_method"],
                "anchor_coordinate": anchor_coordinate,
                "secondary_coordinate": (
                    secondary_coordinates[0] if len(secondary_coordinates) == 1 else None
                ),
                "secondary_coordinates": secondary_coordinates,
                "canonical_position_count": expected_position_count,
                "gaia_ra": float(gaia_source["ra"]),
                "gaia_dec": float(gaia_source["dec"]),
                "classification_subtype": group["approved_classification_subtype"],
                "velocity_review_flag": group.get("velocity_review_flag"),
                "gregg_sequence": group.get("gregg_sequence"),
                "fahrion_name": group.get("fahrion_name"),
                "saifollahi_source_row_count": group.get("saifollahi_source_row_count"),
            }
        )
        if group["approved_classification_subtype"]:
            anchor_record["approved_classification_subtype"] = group[
                "approved_classification_subtype"
            ]

        anchor_sky_coordinate = SkyCoord(anchor_coordinate[0] * u.deg, anchor_coordinate[1] * u.deg)
        for secondary_coordinate in secondary_coordinates:
            secondary_sky_coordinate = SkyCoord(
                secondary_coordinate[0] * u.deg, secondary_coordinate[1] * u.deg
            )
            separation_arcsec = float(
                anchor_sky_coordinate.separation(secondary_sky_coordinate).arcsec
            )
            for record in records_by_coordinate[secondary_coordinate]:
                if record.get("association_anchor_record"):
                    raise RuntimeError(
                        "Approved Gaia merge would overwrite an existing association: "
                        f"{gaia_dr3_id}"
                    )
                record["association_anchor_record"] = anchor_record
                record["approved_association_separation_arcsec"] = separation_arcsec
                record["approved_association_method"] = review["association_method"]
                record["approved_gaia_dr3_id"] = gaia_dr3_id
        for record in gaia_records:
            record["approved_gaia_dr3_id"] = gaia_dr3_id


def create_canonical_objects(
    connection: sqlite3.Connection, records: list[dict[str, object]]
) -> dict[str, str]:
    """Create canonical objects with exact and explicitly approved associations."""
    grouped_records = defaultdict(list)
    for record in records:
        if record.get("defer_canonical_association"):
            continue
        association_anchor = record.get("association_anchor_record")
        if association_anchor:
            key = (
                "coordinate",
                float(association_anchor["ra"]),
                float(association_anchor["dec"]),
            )
        elif record.get("ra") is None or record.get("dec") is None:
            key = ("record", record["record_id"])
        else:
            key = ("coordinate", float(record["ra"]), float(record["dec"]))
        grouped_records[key].append(record)

    canonical_by_record = {}
    for key, group_records in sorted(grouped_records.items(), key=lambda item: str(item[0])):
        if key[0] == "coordinate":
            position_records = [
                record
                for record in group_records
                if float(record["ra"]) == key[1] and float(record["dec"]) == key[2]
            ]
            if not position_records:
                raise RuntimeError(f"Canonical group lacks its position record: {key}")
            anchor_record = min(position_records, key=lambda row: str(row["record_id"]))
        else:
            anchor_record = min(group_records, key=lambda row: str(row["record_id"]))
        canonical_object_id = stable_identifier("canonical", str(anchor_record["record_id"]))
        if key[0] == "coordinate":
            adopted_ra = key[1]
            adopted_dec = key[2]
            position_status = "exact_reported_position"
        else:
            adopted_ra = None
            adopted_dec = None
            position_status = "missing_position"
        connection.execute(
            """
            INSERT INTO canonical_objects (
                canonical_object_id, adopted_ra, adopted_dec, position_record_id,
                position_status, created_from_record_id
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                canonical_object_id,
                adopted_ra,
                adopted_dec,
                anchor_record["record_id"],
                position_status,
                anchor_record["record_id"],
            ),
        )
        for record in group_records:
            if record.get("association_anchor_record"):
                association_method = str(record["approved_association_method"])
                separation_arcsec = float(record["approved_association_separation_arcsec"])
            elif key[0] == "coordinate":
                association_method = "exact_coordinate"
                separation_arcsec = 0.0
            else:
                association_method = "singleton_record"
                separation_arcsec = None
            canonical_by_record[str(record["record_id"])] = canonical_object_id
            connection.execute(
                """
                INSERT INTO object_record_associations (
                    canonical_object_id, record_id, association_method,
                    association_status, separation_arcsec, review_required
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    canonical_object_id,
                    record["record_id"],
                    association_method,
                    "accepted",
                    separation_arcsec,
                    0,
                ),
            )
    return canonical_by_record


def add_canonical_object_aliases(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
) -> None:
    """Retain identifiers for canonical objects merged by approved review."""
    alias_count = 0
    expected_alias_count = sum(
        len(record.get("retired_canonical_aliases", [])) for record in records
    )
    for record in records:
        canonical_object_id = canonical_by_record.get(str(record["record_id"]))
        for retired_canonical_object_id in record.get("retired_canonical_aliases", []):
            if retired_canonical_object_id == canonical_object_id:
                raise RuntimeError("Retired canonical alias equals its adopted identifier")
            connection.execute(
                """
                INSERT INTO canonical_object_aliases (
                    retired_canonical_object_id, canonical_object_id, reason
                ) VALUES (?, ?, ?)
                """,
                (
                    retired_canonical_object_id,
                    canonical_object_id,
                    record.get("retired_canonical_alias_reasons", {}).get(
                        retired_canonical_object_id,
                        "Approved canonical identity review",
                    ),
                ),
            )
            alias_count += 1
    if alias_count != expected_alias_count:
        raise RuntimeError(
            f"Expected {expected_alias_count} retired canonical aliases, found {alias_count}"
        )


def prepare_approved_confirmation_evidence(records: list[dict[str, object]]) -> None:
    """Attach delegated object-level confirmation reviews to immutable records."""
    with CONFIRMATION_EVIDENCE_REVIEW_MANIFEST.open(encoding="utf-8") as input_file:
        manifest = json.load(input_file)
    approval_status = "approved_by_project_lead_2026-07-17"
    if (
        manifest["review_status"] != approval_status
        or manifest["ruleset_id"] != RULESET_ID
        or not manifest["confirmation_changes_authorized"]
        or manifest["identity_changes_authorized"]
        or manifest["classification_changes_outside_ruleset_authorized"]
    ):
        raise RuntimeError("Confirmation evidence reviews lack scoped delegated approval")
    reviews = manifest["reviews"]
    non_promotion_reviews = manifest["non_promotion_reviews"]
    rejection_reviews = manifest["rejection_reviews"]
    if (
        len(reviews) != 1248
        or manifest["summary"]["approved_evidence_count"] != 1248
        or len(non_promotion_reviews) != 125
        or manifest["summary"]["explicit_non_promotion_count"] != 125
        or len(rejection_reviews) != 1
        or manifest["summary"]["approved_rejection_count"] != 1
    ):
        raise RuntimeError(f"Expected 1248 confirmation reviews, found {len(reviews)}")
    records_by_id = {str(record["record_id"]): record for record in records}
    for review in reviews:
        record_id = str(review["record_id"])
        record = records_by_id.get(record_id)
        if record is None:
            raise RuntimeError(f"Confirmation review target record is missing: {record_id}")
        if record.get("approved_confirmation_review"):
            raise RuntimeError(f"Duplicate confirmation review target: {record_id}")
        record["approved_confirmation_review"] = review
    for review in non_promotion_reviews:
        record_id = str(review["record_id"])
        record = records_by_id.get(record_id)
        if record is None:
            raise RuntimeError(f"Confirmation non-promotion target is missing: {record_id}")
        if record.get("approved_confirmation_review"):
            raise RuntimeError(f"Confirmation promotion and non-promotion conflict: {record_id}")
        record["confirmation_non_promotion_review"] = review
    for review in rejection_reviews:
        record_id = str(review["record_id"])
        record = records_by_id.get(record_id)
        if record is None:
            raise RuntimeError(f"Rejection review target record is missing: {record_id}")
        record["approved_rejection_review"] = review


def add_evidence_and_classifications(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
) -> None:
    """Store reported labels as evidence and derive conservative v1 states."""
    evidence_by_object = defaultdict(list)
    for record in records:
        canonical_object_id = canonical_by_record.get(str(record["record_id"]))
        if canonical_object_id is None:
            continue
        publication_id = str(record["source"]["publication_id"])
        reported_status = record.get("confirmation_status")
        reported_is_ucd = parse_integer(record.get("is_ucd"))
        evidence_value = "not_ucd" if reported_is_ucd == 0 else str(reported_status or "unlabeled")
        evidence_id = stable_identifier("evidence", f"{record['record_id']}:reported")
        approved_confirmation_review = record.get("approved_confirmation_review")
        approved_rejection_review = record.get("approved_rejection_review")
        review_status = (
            "approved"
            if reported_status == "confirmed" and approved_confirmation_review
            else "reviewed_insufficient_evidence"
            if reported_status == "confirmed" and record.get("confirmation_non_promotion_review")
            else "pending"
            if reported_status == "confirmed"
            else "not_required"
        )
        connection.execute(
            """
            INSERT INTO object_evidence (
                evidence_id, canonical_object_id, record_id, publication_id,
                evidence_type, evidence_value, evidence_status, review_status,
                details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                canonical_object_id,
                record["record_id"],
                publication_id,
                "reported_classification",
                evidence_value,
                "reported",
                review_status,
                json.dumps(
                    {
                        "reported_confirmation_status": reported_status,
                        "reported_is_ucd": reported_is_ucd,
                    },
                    sort_keys=True,
                ),
            ),
        )
        evidence_by_object[canonical_object_id].append(
            {
                "reported_status": reported_status,
                "reported_is_ucd": reported_is_ucd,
                "record": record,
            }
        )

        if approved_confirmation_review:
            spectroscopy_id = stable_identifier(
                "evidence", f"confirmation_review:{approved_confirmation_review['review_id']}"
            )
            connection.execute(
                """
                INSERT INTO object_evidence (
                    evidence_id, canonical_object_id, record_id, publication_id,
                    evidence_type, evidence_value, evidence_status, review_status,
                    details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    spectroscopy_id,
                    canonical_object_id,
                    record["record_id"],
                    f"ads:{approved_confirmation_review['publication_bibcode']}",
                    approved_confirmation_review["evidence_type"],
                    approved_confirmation_review["evidence_value"],
                    "approved",
                    "approved_by_project_lead_2026-07-17",
                    json.dumps(approved_confirmation_review, sort_keys=True),
                ),
            )

        if approved_rejection_review:
            rejection_id = stable_identifier(
                "evidence", f"rejection_review:{approved_rejection_review['review_id']}"
            )
            connection.execute(
                """
                INSERT INTO object_evidence (
                    evidence_id, canonical_object_id, record_id, publication_id,
                    evidence_type, evidence_value, evidence_status, review_status,
                    details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rejection_id,
                    canonical_object_id,
                    record["record_id"],
                    f"ads:{approved_rejection_review['publication_bibcode']}",
                    approved_rejection_review["evidence_type"],
                    approved_rejection_review["evidence_value"],
                    "approved",
                    "approved_by_project_lead_2026-07-17",
                    json.dumps(approved_rejection_review, sort_keys=True),
                ),
            )

    for canonical_object_id, object_evidence in evidence_by_object.items():
        ucd_values = {item["reported_is_ucd"] for item in object_evidence}
        classification_evidence = [
            {
                "evidence_type": "reported_classification",
                "evidence_value": ("not_ucd" if item["reported_is_ucd"] == 0 else "candidate"),
                "review_status": "not_required",
            }
            for item in object_evidence
        ]
        classification_evidence.extend(
            {
                "evidence_type": item["record"]["approved_confirmation_review"]["evidence_type"],
                "evidence_value": item["record"]["approved_confirmation_review"]["evidence_value"],
                "review_status": "approved",
            }
            for item in object_evidence
            if item["record"].get("approved_confirmation_review")
        )
        classification_evidence.extend(
            {
                "evidence_type": item["record"]["approved_rejection_review"]["evidence_type"],
                "evidence_value": item["record"]["approved_rejection_review"]["evidence_value"],
                "review_status": "approved",
            }
            for item in object_evidence
            if item["record"].get("approved_rejection_review")
        )
        classification_state, rationale = derive_classification(
            classification_evidence,
            identity_conflict=0 in ucd_values and 1 in ucd_values,
        )
        classification_subtypes = {
            item["record"].get("approved_classification_subtype")
            for item in object_evidence
            if item["record"].get("approved_classification_subtype")
        }
        if len(classification_subtypes) > 1:
            raise RuntimeError(
                f"Conflicting classification subtypes for {canonical_object_id}: "
                f"{classification_subtypes}"
            )
        classification_subtype = next(iter(classification_subtypes), None)
        if 0 in ucd_values and 1 in ucd_values and classification_subtype is None:
            classification_subtype = "reported_ucd_role_conflict"
        if classification_subtype and classification_state != "uncertain":
            raise RuntimeError(
                f"Classification subtype requires uncertain state: {canonical_object_id}"
            )
        if classification_subtype == "reported_ucd_role_conflict":
            rationale = "Approved shared identity with conflicting reported UCD roles"
        reported_confirmation_pending = any(
            item["reported_status"] == "confirmed"
            and not item["record"].get("approved_confirmation_review")
            and not item["record"].get("confirmation_non_promotion_review")
            for item in object_evidence
        )
        approved_role_conflict = (
            classification_state == "uncertain"
            and classification_subtype == "reported_ucd_role_conflict"
        )
        review_required = int(
            reported_confirmation_pending
            or (classification_state == "uncertain" and not approved_role_conflict)
        )
        if reported_confirmation_pending and classification_state == "candidate":
            rationale = "Reported confirmation requires evidence review"
        connection.execute(
            """
            INSERT INTO object_classifications (
                canonical_object_id, classification_state, classification_subtype, ruleset_id,
                review_required, rationale
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                canonical_object_id,
                classification_state,
                classification_subtype,
                RULESET_ID,
                review_required,
                rationale,
            ),
        )
        if review_required:
            review_id = stable_identifier("review", f"classification:{canonical_object_id}")
            connection.execute(
                """
                INSERT INTO review_queue (
                    review_id, review_type, canonical_object_id, proposal_id,
                    priority, reason, review_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    "classification_evidence",
                    canonical_object_id,
                    None,
                    "high",
                    rationale,
                    "pending",
                ),
            )


def derive_classification(
    evidence: list[dict[str, str]], identity_conflict: bool = False
) -> tuple[str, str]:
    """Derive one of the four confirmation_rules_v1 states."""
    confirming_types = {"spectroscopic_membership", "space_based_resolved_structure"}
    approved_positive = any(
        item["evidence_type"] in confirming_types
        and item["evidence_value"] in {"positive", "positive_reported"}
        and item["review_status"] == "approved"
        for item in evidence
    )
    explicit_negative = any(
        item["evidence_value"] in {"not_ucd", "negative"}
        and item["review_status"] in {"approved", "not_required"}
        for item in evidence
    )
    if identity_conflict or (approved_positive and explicit_negative):
        return "uncertain", "Conflicting evidence or unresolved object identity"
    if approved_positive:
        return "confirmed", "Approved confirmation evidence under confirmation_rules_v1"
    if explicit_negative:
        return "rejected", "Explicit non-UCD evidence without approved positive confirmation"
    return "candidate", "No approved confirmation or rejection evidence"


def add_dumont_dynamical_evidence(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
) -> None:
    """Attach Dumont dynamical measurements as supportive, non-confirming evidence."""
    dumont_records = {
        str(record["original_name"]): record
        for record in records
        if record["source"]["bibcode"] == "2022ApJ...929..147D"
    }
    table_path = PROJECT_ROOT / "reference" / "dumont2022" / "table3.dat"
    readme_path = PROJECT_ROOT / "reference" / "dumont2022" / "ReadMe.txt"
    table = ascii.read(table_path, readme=readme_path, format="cds")
    for row_number, measurement in enumerate(serialize_table_rows(table), start=1):
        record = dumont_records.get(str(measurement["ID"]))
        if record is None:
            raise RuntimeError(f"Dumont measurement has no target record: {measurement['ID']}")
        canonical_object_id = canonical_by_record[str(record["record_id"])]
        evidence_id = stable_identifier(
            "evidence", f"{record['record_id']}:dumont_table3:{row_number}"
        )
        connection.execute(
            """
            INSERT INTO object_evidence (
                evidence_id, canonical_object_id, record_id, publication_id,
                evidence_type, evidence_value, evidence_status, review_status,
                details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                canonical_object_id,
                record["record_id"],
                record["source"]["publication_id"],
                "dynamical_measurement",
                "supportive_not_confirming",
                "reported",
                "not_required",
                json.dumps(
                    {
                        "source_table": "table3.dat",
                        "source_row_locator": f"raw_row_{row_number}",
                        "measurement": measurement,
                    },
                    sort_keys=True,
                ),
            ),
        )


def add_source_association_review_evidence(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
) -> None:
    """Store approved alias-chain identity evidence on accepted associations."""
    reviewed_records = [record for record in records if record.get("association_review")]
    if len(reviewed_records) != 1:
        raise RuntimeError(
            f"Expected one approved source association review, found {len(reviewed_records)}"
        )
    record = reviewed_records[0]
    review = record["association_review"]
    canonical_object_id = canonical_by_record[str(record["record_id"])]
    evidence_id = stable_identifier("evidence", f"{record['record_id']}:source_association_review")
    connection.execute(
        """
        INSERT INTO object_evidence (
            evidence_id, canonical_object_id, record_id, publication_id,
            evidence_type, evidence_value, evidence_status, review_status,
            details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            evidence_id,
            canonical_object_id,
            record["record_id"],
            record["source"]["publication_id"],
            "identity_alias_chain",
            "same_astrophysical_object",
            "approved",
            "approved",
            json.dumps(review, sort_keys=True),
        ),
    )


def add_gaia_association_review_evidence(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
) -> None:
    """Store approved shared-Gaia identity evidence on merged objects."""
    evidence_count = 0
    expected_evidence_count = sum(
        len(record.get("approved_gaia_identity_evidence", [])) for record in records
    )
    for record in records:
        canonical_object_id = canonical_by_record.get(str(record["record_id"]))
        for details in record.get("approved_gaia_identity_evidence", []):
            evidence_id = stable_identifier("evidence", f"gaia_identity:{details['gaia_dr3_id']}")
            connection.execute(
                """
                INSERT INTO object_evidence (
                    evidence_id, canonical_object_id, record_id, publication_id,
                    evidence_type, evidence_value, evidence_status, review_status,
                    details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    canonical_object_id,
                    record["record_id"],
                    record["source"]["publication_id"],
                    "identity_shared_gaia_dr3",
                    "same_astrophysical_object",
                    "approved",
                    "approved",
                    json.dumps(details, sort_keys=True),
                ),
            )
            evidence_count += 1
    if evidence_count != expected_evidence_count:
        raise RuntimeError(
            f"Expected {expected_evidence_count} Gaia identity evidence rows, "
            f"found {evidence_count}"
        )


def add_gaia_shared_source_ambiguity_evidence(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
) -> None:
    """Store approved ambiguous Gaia evidence for distinct close-pair objects."""
    evidence_count = 0
    expected_evidence_count = sum(
        len(record.get("approved_gaia_ambiguity_evidence", [])) for record in records
    )
    for record in records:
        canonical_object_id = canonical_by_record.get(str(record["record_id"]))
        for details in record.get("approved_gaia_ambiguity_evidence", []):
            evidence_id = stable_identifier(
                "evidence",
                f"gaia_ambiguity:{details['gaia_dr3_id']}:{canonical_object_id}",
            )
            connection.execute(
                """
                INSERT INTO object_evidence (
                    evidence_id, canonical_object_id, record_id, publication_id,
                    evidence_type, evidence_value, evidence_status, review_status,
                    details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    canonical_object_id,
                    record["record_id"],
                    record["source"]["publication_id"],
                    details["evidence_type"],
                    details["evidence_value"],
                    "approved",
                    "approved",
                    json.dumps(details, sort_keys=True),
                ),
            )
            evidence_count += 1
    if evidence_count != expected_evidence_count:
        raise RuntimeError(
            f"Expected {expected_evidence_count} shared-Gaia ambiguity evidence rows, "
            f"found {evidence_count}"
        )


def add_supplemental_identity_evidence(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
) -> None:
    """Store approved name-and-position identity evidence for supplemental records."""
    evidence_count = 0
    expected_evidence_count = sum(
        len(record.get("approved_supplemental_identity_evidence", [])) for record in records
    )
    for record in records:
        canonical_object_id = canonical_by_record.get(str(record["record_id"]))
        for details in record.get("approved_supplemental_identity_evidence", []):
            evidence_id = stable_identifier(
                "evidence", f"supplemental_identity:{details['source_record_id']}"
            )
            connection.execute(
                """
                INSERT INTO object_evidence (
                    evidence_id, canonical_object_id, record_id, publication_id,
                    evidence_type, evidence_value, evidence_status, review_status,
                    details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    canonical_object_id,
                    record["record_id"],
                    record["source"]["publication_id"],
                    details["evidence_type"],
                    details["evidence_value"],
                    "approved",
                    "approved",
                    json.dumps(details, sort_keys=True),
                ),
            )
            evidence_count += 1
    if evidence_count != expected_evidence_count:
        raise RuntimeError(
            f"Expected {expected_evidence_count} supplemental identity evidence rows, "
            f"found {evidence_count}"
        )


def add_unassociated_record_reviews(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
) -> None:
    """Queue coordinate-null provenance records without creating objects."""
    unassociated_records = [
        record for record in records if str(record["record_id"]) not in canonical_by_record
    ]
    if len(unassociated_records) != 4 or not all(
        record.get("defer_canonical_association") for record in unassociated_records
    ):
        raise RuntimeError(
            f"Unexpected unassociated literature records: {len(unassociated_records)}"
        )
    for record in unassociated_records:
        review_id = stable_identifier("review", f"record_identity:{record['record_id']}")
        connection.execute(
            """
            INSERT INTO review_queue (
                review_id, review_type, record_id, canonical_object_id,
                proposal_id, priority, reason, review_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                "record_identity",
                record["record_id"],
                None,
                None,
                "medium",
                "Authoritative Fahrion row has no published coordinates",
                "pending",
            ),
        )


def add_wave1_supporting_evidence(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
    dataset_by_bibcode: dict[str, str],
    wave1_identity_review: dict[str, object],
    wave1_identity_proposals: list[dict[str, object]],
    wave1_group_identity_proposals: list[dict[str, object]],
) -> None:
    """Attach approved Ahn measurements and S999 identity evidence."""
    m59_records = [
        record
        for record in records
        if normalized_object_name(record.get("original_name")) == "m59-ucd3"
    ]
    if len(m59_records) != 1:
        raise RuntimeError(f"Expected one M59-UCD3 record, found {len(m59_records)}")
    m59_record = m59_records[0]
    m59_canonical_object_id = canonical_by_record[str(m59_record["record_id"])]
    ahn_dataset_id = dataset_by_bibcode["2018ApJ...858..102A"]
    ahn_file = connection.execute(
        """
        SELECT local_path, file_sha256, raw_row_count
        FROM dataset_files
        WHERE dataset_id = ? AND file_name = 'table3.dat'
        """,
        (ahn_dataset_id,),
    ).fetchone()
    if ahn_file is None or ahn_file["raw_row_count"] != 109:
        raise RuntimeError("Ahn table 3 package registration is incomplete")
    ahn_evidence_id = stable_identifier("evidence", f"{m59_record['record_id']}:ahn2018_table3")
    connection.execute(
        """
        INSERT INTO object_evidence (
            evidence_id, canonical_object_id, record_id, publication_id,
            evidence_type, evidence_value, evidence_status, review_status,
            details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ahn_evidence_id,
            m59_canonical_object_id,
            m59_record["record_id"],
            "ads:2018ApJ...858..102A",
            "spatial_kinematic_measurements",
            "supportive_not_confirming",
            "reported",
            "not_required",
            json.dumps(
                {
                    "dataset_id": ahn_dataset_id,
                    "source_table": "table3.dat",
                    "source_row_count": 109,
                    "local_path": ahn_file["local_path"],
                    "file_sha256": ahn_file["file_sha256"],
                    "treatment": "measurements_of_one_object_not_independent_objects",
                },
                sort_keys=True,
            ),
        ),
    )

    records_by_id = {str(record["record_id"]): record for record in records}
    for proposal in wave1_identity_proposals:
        wave_record = records_by_id[str(proposal["wave_record_id"])]
        canonical_object_id = canonical_by_record[str(wave_record["record_id"])]
        if canonical_object_id != proposal["target_canonical_object_id"]:
            raise RuntimeError(
                f"Approved Wave 1 proposal missed its target: {proposal['proposal_id']}"
            )
        evidence_id = stable_identifier(
            "evidence", f"{wave_record['record_id']}:approved_wave1_identity"
        )
        connection.execute(
            """
            INSERT INTO object_evidence (
                evidence_id, canonical_object_id, record_id, publication_id,
                evidence_type, evidence_value, evidence_status, review_status,
                details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                canonical_object_id,
                wave_record["record_id"],
                wave_record["source"]["publication_id"],
                "identity_name_or_published_alias",
                "same_astrophysical_object",
                "approved",
                "approved_by_project_lead_2026-07-15",
                json.dumps(proposal, sort_keys=True),
            ),
        )

    group_anchor_records = {
        str(proposal["group_id"]): record
        for record in records
        for proposal in record.get("approved_wave1_group_identity_evidence", [])
    }
    if set(group_anchor_records) != {
        str(proposal["group_id"]) for proposal in wave1_group_identity_proposals
    }:
        raise RuntimeError("Approved Wave 1 group identity anchors are incomplete")
    for proposal in wave1_group_identity_proposals:
        group_id = str(proposal["group_id"])
        anchor_record = group_anchor_records[group_id]
        canonical_object_id = canonical_by_record[str(anchor_record["record_id"])]
        group_record_ids = {
            str(record["record_id"])
            for record in records
            if record.get("approved_wave1_group_identity_proposal") == proposal
        } | {str(anchor_record["record_id"])}
        reviewed_canonical_ids = set(proposal["current_canonical_object_ids"])
        if len(reviewed_canonical_ids) != len(group_record_ids):
            raise RuntimeError(f"Wave 1 group record coverage changed: {group_id}")
        if len({canonical_by_record[record_id] for record_id in group_record_ids}) != 1:
            raise RuntimeError(f"Approved Wave 1 group did not consolidate: {group_id}")
        evidence_id = stable_identifier("evidence", f"{group_id}:approved_wave1_group_identity")
        connection.execute(
            """
            INSERT INTO object_evidence (
                evidence_id, canonical_object_id, record_id, publication_id,
                evidence_type, evidence_value, evidence_status, review_status,
                details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                canonical_object_id,
                anchor_record["record_id"],
                anchor_record["source"]["publication_id"],
                "identity_multi_canonical_shared_identifier",
                "same_astrophysical_object",
                "approved",
                "approved_by_project_lead_2026-07-15",
                json.dumps(proposal, sort_keys=True),
            ),
        )

    s999_records = [record for record in records if record.get("wave1_identity_review")]
    if len(s999_records) != 4:
        raise RuntimeError(f"Expected four S999 identity records, found {len(s999_records)}")
    s999_anchor = next(
        record for record in s999_records if record["source"]["bibcode"] == "2019A&A...625A..50F"
    )
    s999_canonical_object_id = canonical_by_record[str(s999_anchor["record_id"])]
    if len({canonical_by_record[str(record["record_id"])] for record in s999_records}) != 1:
        raise RuntimeError("Approved S999 records did not consolidate to one canonical object")
    s999_evidence_id = stable_identifier(
        "evidence", f"{s999_anchor['record_id']}:wave1_s999_identity"
    )
    connection.execute(
        """
        INSERT INTO object_evidence (
            evidence_id, canonical_object_id, record_id, publication_id,
            evidence_type, evidence_value, evidence_status, review_status,
            details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            s999_evidence_id,
            s999_canonical_object_id,
            s999_anchor["record_id"],
            s999_anchor["source"]["publication_id"],
            "identity_name_velocity_alias_chain",
            "same_astrophysical_object",
            "approved",
            "approved_by_project_lead_2026-07-15",
            json.dumps(wave1_identity_review, sort_keys=True),
        ),
    )


def add_wave1_remaining_identity_evidence(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
    proposals: list[dict[str, object]],
) -> None:
    """Store one approved evidence record for each delegated source identity."""
    anchor_records = {
        str(proposal["decision_id"]): record
        for record in records
        for proposal in record.get("approved_wave1_remaining_identity_evidence", [])
    }
    if set(anchor_records) != {str(proposal["decision_id"]) for proposal in proposals}:
        raise RuntimeError("Remaining Wave 1 identity evidence anchors are incomplete")

    for proposal in proposals:
        decision_id = str(proposal["decision_id"])
        anchor_record = anchor_records[decision_id]
        identity_records = [
            record
            for record in records
            if record.get("approved_wave1_remaining_identity_proposal") == proposal
        ]
        canonical_object_ids = {
            canonical_by_record[str(record["record_id"])] for record in identity_records
        }
        if len(canonical_object_ids) != 1:
            raise RuntimeError(f"Remaining Wave 1 identity did not consolidate: {decision_id}")
        canonical_object_id = canonical_object_ids.pop()
        evidence_id = stable_identifier("evidence", f"{decision_id}:approved_wave1_source_identity")
        connection.execute(
            """
            INSERT INTO object_evidence (
                evidence_id, canonical_object_id, record_id, publication_id,
                evidence_type, evidence_value, evidence_status, review_status,
                details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                canonical_object_id,
                anchor_record["record_id"],
                anchor_record["source"]["publication_id"],
                "identity_source_catalog_lineage",
                "same_astrophysical_object",
                "approved",
                "approved_by_project_lead_delegation_2026-07-15",
                json.dumps(proposal, sort_keys=True),
            ),
        )


def add_supporting_source_row_evidence(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    canonical_by_record: dict[str, str],
) -> None:
    """Store approved object links for intentionally supporting raw-table rows."""
    with SUPPORTING_SOURCE_ROW_LINK_MANIFEST.open(encoding="utf-8") as input_file:
        manifest = json.load(input_file)
    approval_status = "approved_by_project_lead_delegation_2026-07-15"
    if (
        manifest["review_status"] != approval_status
        or not manifest["supporting_evidence_links_authorized"]
        or manifest["identity_changes_authorized"]
        or manifest["classification_changes_authorized"]
        or manifest["confirmation_changes_authorized"]
    ):
        raise RuntimeError("Supporting source-row links lack scoped delegated approval")
    links = manifest["links"]
    if len(links) != 168 or manifest["summary"]["link_count"] != 168:
        raise RuntimeError(f"Expected 168 supporting source-row links, found {len(links)}")

    records_by_id = {str(record["record_id"]): record for record in records}
    publication_by_bibcode = {
        str(row["bibcode"]): str(row["publication_id"])
        for row in connection.execute("SELECT publication_id, bibcode FROM publications")
    }
    for link in links:
        link_id = str(link["link_id"])
        record_id = str(link["record_id"])
        record = records_by_id.get(record_id)
        if record is None:
            raise RuntimeError(f"Supporting source-row target record is missing: {link_id}")
        canonical_object_id = canonical_by_record[record_id]
        if canonical_object_id != link["canonical_object_id"]:
            raise RuntimeError(f"Supporting source-row target identity changed: {link_id}")
        evidence_id = stable_identifier("evidence", f"supporting_source_row:{link_id}")
        connection.execute(
            """
            INSERT INTO object_evidence (
                evidence_id, canonical_object_id, record_id, publication_id,
                evidence_type, evidence_value, evidence_status, review_status,
                details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                canonical_object_id,
                record_id,
                publication_by_bibcode[str(link["publication_bibcode"])],
                link["evidence_type"],
                "supporting_measurement",
                "reported",
                approval_status,
                json.dumps(link, sort_keys=True),
            ),
        )


def add_gaia_association_proposals(
    connection: sqlite3.Connection, records: list[dict[str, object]]
) -> None:
    """Create review-only proposals for repeated Gaia IDs at different coordinates."""
    records_by_gaia_id = defaultdict(list)
    approved_gaia_ids = {
        str(record["approved_gaia_dr3_id"])
        for record in records
        if record.get("approved_gaia_dr3_id")
    }
    approved_gaia_ids.update(
        str(record["reviewed_separate_gaia_dr3_id"])
        for record in records
        if record.get("reviewed_separate_gaia_dr3_id")
    )
    for record in records:
        gaia_dr3_id = normalize_scalar(record.get("gaia_dr3_id"))
        if (
            gaia_dr3_id is not None
            and record.get("ra") is not None
            and record.get("dec") is not None
        ):
            records_by_gaia_id[str(gaia_dr3_id)].append(record)

    for gaia_dr3_id, group_records in sorted(records_by_gaia_id.items()):
        if len(group_records) < 2:
            continue
        if gaia_dr3_id in approved_gaia_ids:
            continue
        non_exact_pairs = [
            (first_record, second_record)
            for first_record, second_record in combinations(group_records, 2)
            if not (
                float(first_record["ra"]) == float(second_record["ra"])
                and float(first_record["dec"]) == float(second_record["dec"])
            )
        ]
        if not non_exact_pairs:
            continue
        review_actions = {
            str(record["gaia_review_action"])
            for record in group_records
            if record.get("gaia_review_action")
        }
        if len(review_actions) != 1:
            raise RuntimeError(f"Gaia review routing is missing or inconsistent: {gaia_dr3_id}")
        review_action = review_actions.pop()
        for first_record, second_record in non_exact_pairs:
            first_coordinate = SkyCoord(first_record["ra"] * u.deg, first_record["dec"] * u.deg)
            second_coordinate = SkyCoord(second_record["ra"] * u.deg, second_record["dec"] * u.deg)
            separation_arcsec = first_coordinate.separation(second_coordinate).arcsec
            ordered_record_ids = sorted(
                (str(first_record["record_id"]), str(second_record["record_id"]))
            )
            proposal_id = stable_identifier(
                "proposal", f"gaia:{ordered_record_ids[0]}:{ordered_record_ids[1]}"
            )
            review_reasons = {
                "identity_and_classification_review": (
                    "Shared Gaia DR3 source with conflicting reported UCD roles"
                ),
                "manual_gaia_image_ambiguity_review": (
                    "Shared Gaia DR3 source with duplicated-source or multi-peak image diagnostic"
                ),
                "manual_multi_position_identity_review": (
                    "Shared Gaia DR3 source spanning three canonical literature positions"
                ),
            }
            review_reason = review_reasons[review_action]
            connection.execute(
                """
                INSERT INTO association_proposals (
                    proposal_id, gaia_dr3_id, record_id_1, record_id_2,
                    separation_arcsec, proposal_method, review_reason,
                    proposal_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal_id,
                    gaia_dr3_id,
                    ordered_record_ids[0],
                    ordered_record_ids[1],
                    separation_arcsec,
                    "legacy_gaia_id",
                    review_reason,
                    "pending_identity_ambiguity_review",
                ),
            )
            review_id = stable_identifier("review", f"association:{proposal_id}")
            connection.execute(
                """
                INSERT INTO review_queue (
                    review_id, review_type, canonical_object_id, proposal_id,
                    priority, reason, review_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    "identity_association",
                    None,
                    proposal_id,
                    (
                        "high"
                        if review_action
                        in {
                            "identity_and_classification_review",
                            "manual_multi_position_identity_review",
                        }
                        else "medium"
                    ),
                    review_reason,
                    "pending",
                ),
            )


def insert_build_metadata(
    connection: sqlite3.Connection, legacy_database: Path, record_count: int
) -> None:
    """Record reproducibility and safety metadata."""
    metadata = {
        "schema_version": "1",
        "ruleset_id": RULESET_ID,
        "build_date": date.today().isoformat(),
        "legacy_database_path": relative_path(legacy_database),
        "legacy_database_sha256": calculate_sha256(legacy_database),
        "literature_record_count": str(record_count),
        "canonicalization_scope": ("exact_coordinates_and_project_lead_approved_identity_groups"),
        "authoritative_input_status": ("raw_packages_linked_with_approved_wave1_row_roles"),
        "host_distance_review_sha256": calculate_sha256(HOST_DISTANCE_REVIEW_MANIFEST),
        "host_distance_review_status": "approved_by_project_lead_delegation_2026-07-15",
        "confirmation_evidence_review_sha256": calculate_sha256(
            CONFIRMATION_EVIDENCE_REVIEW_MANIFEST
        ),
        "confirmation_evidence_review_status": "approved_by_project_lead_2026-07-17",
        "literature_screening_closure_sha256": calculate_sha256(
            LITERATURE_SCREENING_CLOSURE_MANIFEST
        ),
        "literature_screening_closure_status": ("approved_by_project_lead_delegation_2026-07-15"),
    }
    connection.executemany(
        "INSERT INTO build_metadata (metadata_key, metadata_value) VALUES (?, ?)",
        sorted(metadata.items()),
    )


def main() -> None:
    """Build the v2 database from immutable inputs."""
    arguments = parse_arguments()
    legacy_hash_before = calculate_sha256(arguments.legacy_database)
    sources = load_source_manifest(arguments.source_manifest)
    connection = create_database(arguments.output_database)
    try:
        sources_by_legacy_id = insert_publications(connection, sources)
        wave1_sources_by_bibcode = insert_wave1_publications(connection)
        records = ingest_records(
            connection,
            arguments.legacy_database,
            arguments.catalog_directory,
            sources_by_legacy_id,
        )
        wave1_records, wave1_dataset_by_bibcode = ingest_wave1_tables(
            connection, wave1_sources_by_bibcode
        )
        records.extend(wave1_records)
        insert_raw_dataset_files(connection, arguments.retrieval_report)
        with ASSOCIATION_REVIEW_MANIFEST.open(encoding="utf-8") as input_file:
            association_reviews = json.load(input_file)["reviews"]
        prepare_approved_source_associations(records, association_reviews)
        wave1_identity_review = prepare_approved_wave1_identity(records)
        wave1_identity_proposals = prepare_approved_wave1_identity_proposals(records)
        with GAIA_ASSOCIATION_REVIEW_MANIFEST.open(encoding="utf-8") as input_file:
            gaia_association_review = json.load(input_file)
        prepare_approved_gaia_associations(records, gaia_association_review)
        wave1_group_identity_proposals = prepare_approved_wave1_group_identities(records)
        wave1_remaining_identity_proposals = prepare_approved_wave1_remaining_identities(records)
        prepare_approved_confirmation_evidence(records)
        canonical_by_record = create_canonical_objects(connection, records)
        add_canonical_object_aliases(connection, records, canonical_by_record)
        add_evidence_and_classifications(connection, records, canonical_by_record)
        add_dumont_dynamical_evidence(connection, records, canonical_by_record)
        add_source_association_review_evidence(connection, records, canonical_by_record)
        add_gaia_association_review_evidence(connection, records, canonical_by_record)
        add_gaia_shared_source_ambiguity_evidence(connection, records, canonical_by_record)
        add_supplemental_identity_evidence(connection, records, canonical_by_record)
        add_wave1_supporting_evidence(
            connection,
            records,
            canonical_by_record,
            wave1_dataset_by_bibcode,
            wave1_identity_review,
            wave1_identity_proposals,
            wave1_group_identity_proposals,
        )
        add_wave1_remaining_identity_evidence(
            connection,
            records,
            canonical_by_record,
            wave1_remaining_identity_proposals,
        )
        add_supporting_source_row_evidence(connection, records, canonical_by_record)
        add_unassociated_record_reviews(connection, records, canonical_by_record)
        add_gaia_association_proposals(connection, records)
        insert_build_metadata(connection, arguments.legacy_database, len(records))
        connection.commit()
        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_errors:
            raise RuntimeError(f"Foreign-key validation failed: {foreign_key_errors}")
    finally:
        connection.close()

    if calculate_sha256(arguments.legacy_database) != legacy_hash_before:
        raise RuntimeError("Legacy database changed during v2 build")
    logger.info(
        "Built %s from %d preserved literature records", arguments.output_database, len(records)
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
