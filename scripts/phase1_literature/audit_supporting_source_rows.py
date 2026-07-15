"""Link intentionally supporting raw-table rows to preserved literature objects.

The audit uses within-publication row order and stable source identifiers for
Chiboucas and Liu, and published Voggel identifiers plus the Dumont source citation
for Fluffy. It records measurements as supporting evidence and never changes object
identity, confirmation, or classification.
"""

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import ascii

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_REFERENCE_DB_V2,
    LITERATURE_SOURCES,
    LITERATURE_VALIDATION,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256, connect_read_only

DEFAULT_OUTPUT = LITERATURE_SOURCES / "supporting_source_row_links.json"
DEFAULT_REPORT = LITERATURE_VALIDATION / "supporting_source_row_links.md"
APPROVAL_STATUS = "approved_by_project_lead_delegation_2026-07-15"


def parse_arguments() -> argparse.Namespace:
    """Parse audit inputs and delegated approval mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--authorize-under-delegation", action="store_true")
    return parser.parse_args()


def scalar_value(value: object) -> object:
    """Convert Astropy and NumPy scalars to JSON-safe Python values."""
    if np.ma.is_masked(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def row_payload(row: object) -> dict[str, object]:
    """Convert one Astropy row to a JSON-safe dictionary."""
    return {name: scalar_value(row[name]) for name in row.colnames}


def publication_records(connection: object, bibcode: str) -> list[dict[str, object]]:
    """Return publication records in stable legacy/raw row order."""
    rows = connection.execute(
        """
        SELECT r.record_id, r.source_row_locator, r.original_name, r.ra, r.dec,
               a.canonical_object_id
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        JOIN object_record_associations a USING (record_id)
        WHERE p.bibcode = ?
        ORDER BY r.source_row_locator
        """,
        (bibcode,),
    ).fetchall()
    return [dict(row) for row in rows]


def legacy_records(records: list[dict[str, object]], prefix: str) -> list[dict[str, object]]:
    """Select stable pre-raw records by their original row-locator prefix."""
    return [record for record in records if str(record["source_row_locator"]).startswith(prefix)]


def measured_separation_arcsec(
    record: dict[str, object],
    right_ascension_deg: float,
    declination_deg: float,
) -> float:
    """Measure small source-coordinate differences without defining an identity radius."""
    source = SkyCoord(right_ascension_deg * u.deg, declination_deg * u.deg)
    target = SkyCoord(float(record["ra"]) * u.deg, float(record["dec"]) * u.deg)
    return float(source.separation(target).arcsec)


def build_links(connection: object) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Build and validate all 168 supporting-row links."""
    links = []

    chiboucas_folder = PROJECT_ROOT / "reference" / "chiboucas2011"
    chiboucas_readme = chiboucas_folder / "ReadMe.txt"
    chiboucas_table2 = ascii.read(
        chiboucas_folder / "table2.dat", readme=chiboucas_readme, format="cds"
    )
    chiboucas_table3 = ascii.read(
        chiboucas_folder / "table3.dat", readme=chiboucas_readme, format="cds"
    )
    chiboucas_table4 = ascii.read(
        chiboucas_folder / "table4.dat", readme=chiboucas_readme, format="cds"
    )
    chiboucas_primary_rows = list(chiboucas_table2) + list(chiboucas_table3)
    chiboucas_index_by_id = {
        int(row["ID"]): index for index, row in enumerate(chiboucas_primary_rows)
    }
    chiboucas_records = legacy_records(
        publication_records(connection, "2011ApJ...737...86C"),
        "2011ApJ...737...86C_",
    )
    if len(chiboucas_records) != 78:
        raise RuntimeError(f"Expected 78 Chiboucas primary records, found {len(chiboucas_records)}")
    for row_number, supporting_row in enumerate(chiboucas_table4, start=1):
        source_id = int(supporting_row["ID"])
        primary_index = chiboucas_index_by_id[source_id]
        primary_row = chiboucas_primary_rows[primary_index]
        record = chiboucas_records[primary_index]
        separation_arcsec = measured_separation_arcsec(
            record,
            float(primary_row["RAdeg"]),
            float(primary_row["DEdeg"]),
        )
        links.append(
            {
                "link_id": f"chiboucas2011_table4_{source_id}",
                "record_id": record["record_id"],
                "canonical_object_id": record["canonical_object_id"],
                "publication_bibcode": "2011ApJ...737...86C",
                "source_table": "table4.dat",
                "source_row_number": row_number,
                "source_key": str(source_id),
                "evidence_type": "supporting_structural_measurement",
                "link_method": "same_publication_id_and_primary_row_order",
                "primary_coordinate_separation_arcsec": separation_arcsec,
                "measurement": row_payload(supporting_row),
            }
        )

    liu_folder = PROJECT_ROOT / "reference" / "liu2015"
    liu_table2 = ascii.read(
        liu_folder / "table2.dat", readme=liu_folder / "ReadMe.txt", format="cds"
    )
    liu_table3_lines = (liu_folder / "table3.dat").read_text(encoding="utf-8").splitlines()
    liu_records = legacy_records(
        publication_records(connection, "2015ApJ...812...34L"),
        "2015ApJ...812...34L_",
    )
    if len(liu_table2) != 127 or len(liu_table3_lines) != 127 or len(liu_records) != 127:
        raise RuntimeError("Liu 2015 M87 primary/supporting row counts changed")
    for index, (primary_row, supporting_line, record) in enumerate(
        zip(liu_table2, liu_table3_lines, liu_records, strict=True),
        start=1,
    ):
        ngvs_identifier = supporting_line[9:28].strip()
        if ngvs_identifier != str(primary_row["NGVS"]):
            raise RuntimeError(f"Liu 2015 paired table key changed at row {index}")
        separation_arcsec = measured_separation_arcsec(
            record,
            float(primary_row["RAdeg"]),
            float(primary_row["DEdeg"]),
        )
        links.append(
            {
                "link_id": f"liu2015_table3_{index}",
                "record_id": record["record_id"],
                "canonical_object_id": record["canonical_object_id"],
                "publication_bibcode": "2015ApJ...812...34L",
                "source_table": "table3.dat",
                "source_row_number": index,
                "source_key": ngvs_identifier,
                "evidence_type": "supporting_structural_and_velocity_measurement",
                "link_method": "same_publication_ngvs_key_and_primary_row_order",
                "primary_coordinate_separation_arcsec": separation_arcsec,
                "measurement": {"raw_fixed_width_row": supporting_line},
            }
        )

    voggel_folder = PROJECT_ROOT / "reference" / "voggel2020"
    voggel_readme = voggel_folder / "ReadMe.txt"
    voggel_table2 = ascii.read(voggel_folder / "table2.dat", readme=voggel_readme, format="cds")
    voggel_table3 = ascii.read(voggel_folder / "table3.dat", readme=voggel_readme, format="cds")
    voggel_records = legacy_records(
        publication_records(connection, "2020ApJ...899..140V"),
        "2020ApJ...899..140W_",
    )
    if len(voggel_table2) != 632 or len(voggel_table3) != 14 or len(voggel_records) != 632:
        raise RuntimeError("Voggel 2020 primary/supporting row counts changed")
    voggel_index_by_name = {str(row["KV19"]): index for index, row in enumerate(voggel_table2)}
    fluffy_matches = connection.execute(
        """
        SELECT r.record_id, a.canonical_object_id, r.ra, r.dec
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        JOIN object_record_associations a USING (record_id)
        WHERE p.bibcode = '2022ApJ...929..147D' AND r.original_name = 'Fluffy'
        """
    ).fetchall()
    if len(fluffy_matches) != 1:
        raise RuntimeError(f"Expected one Dumont Fluffy record, found {len(fluffy_matches)}")
    fluffy_record = dict(fluffy_matches[0])
    for row_number, supporting_row in enumerate(voggel_table3, start=1):
        source_name = str(supporting_row["KV19"])
        if source_name == "Fluffy":
            record = fluffy_record
            link_method = "published_name_and_dumont_voggel2020_source_citation"
        else:
            primary_index = voggel_index_by_name[source_name]
            record = voggel_records[primary_index]
            link_method = "same_publication_kv19_key_and_primary_row_order"
        separation_arcsec = measured_separation_arcsec(
            record,
            float(supporting_row["RAdeg"]),
            float(supporting_row["DEdeg"]),
        )
        links.append(
            {
                "link_id": f"voggel2020_table3_{source_name.lower()}",
                "record_id": record["record_id"],
                "canonical_object_id": record["canonical_object_id"],
                "publication_bibcode": "2020ApJ...899..140V",
                "source_table": "table3.dat",
                "source_row_number": row_number,
                "source_key": source_name,
                "evidence_type": "supporting_spectroscopic_measurement",
                "link_method": link_method,
                "primary_coordinate_separation_arcsec": separation_arcsec,
                "measurement": row_payload(supporting_row),
            }
        )

    links.sort(key=lambda link: str(link["link_id"]))
    if len(links) != 168 or len({link["link_id"] for link in links}) != 168:
        raise RuntimeError(f"Expected 168 unique supporting-row links, found {len(links)}")
    summary = {
        "link_count": len(links),
        "evidence_type_counts": dict(
            sorted(Counter(str(link["evidence_type"]) for link in links).items())
        ),
        "source_table_counts": dict(
            sorted(
                Counter(
                    f"{link['publication_bibcode']}:{link['source_table']}" for link in links
                ).items()
            )
        ),
        "maximum_primary_coordinate_separation_arcsec": max(
            float(link["primary_coordinate_separation_arcsec"]) for link in links
        ),
    }
    return links, summary


def write_artifact(
    path: Path,
    links: list[dict[str, object]],
    summary: dict[str, object],
    database_sha256: str,
    authorized: bool,
) -> None:
    """Write deterministic supporting-row link decisions."""
    review_status = APPROVAL_STATUS if authorized else "proposed_pending_project_lead_review"
    artifact = {
        "schema_version": 1,
        "audit_date": date.today().isoformat(),
        "review_status": review_status,
        "identity_changes_authorized": False,
        "classification_changes_authorized": False,
        "confirmation_changes_authorized": False,
        "supporting_evidence_links_authorized": authorized,
        "reference_database_sha256": database_sha256,
        "summary": summary,
        "links": links,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(
    path: Path,
    summary: dict[str, object],
    database_sha256: str,
    authorized: bool,
) -> None:
    """Write a concise supporting-row audit report."""
    review_status = APPROVAL_STATUS if authorized else "proposed_pending_project_lead_review"
    count_rows = "\n".join(
        f"| `{key}` | {value} |" for key, value in summary["source_table_counts"].items()
    )
    report = f"""# Supporting Source-Row Link Audit

**Status:** `{review_status}`
**Reference database SHA-256:** `{database_sha256}`

| Source table | Linked rows |
|---|---:|
{count_rows}

All {summary["link_count"]} intentionally supporting rows have deterministic
object links. Chiboucas rows use same-publication IDs and primary-row order; Liu
rows use exact NGVS keys and paired row order; Voggel rows use KV19 identifiers,
with Fluffy linked through the Dumont record that explicitly cites Voggel 2020.

These links preserve structural, velocity, and spectroscopic measurements only.
They do not authorize identity, classification, or confirmation changes. The
largest measured primary-coordinate difference is
{summary["maximum_primary_coordinate_separation_arcsec"]:.12f} arcseconds.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")


def main() -> None:
    """Run the supporting source-row audit."""
    arguments = parse_arguments()
    database_sha256 = calculate_sha256(arguments.reference_database)
    with connect_read_only(arguments.reference_database) as connection:
        links, summary = build_links(connection)
    write_artifact(
        arguments.output,
        links,
        summary,
        database_sha256,
        arguments.authorize_under_delegation,
    )
    write_report(
        arguments.report,
        summary,
        database_sha256,
        arguments.authorize_under_delegation,
    )


if __name__ == "__main__":
    main()
