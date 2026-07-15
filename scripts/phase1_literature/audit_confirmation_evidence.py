"""Audit object-level literature evidence against confirmation_rules_v1."""

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
from astropy.io import ascii

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_REFERENCE_DB_V2, LITERATURE_SOURCES, PROJECT_ROOT
from scripts.phase1_literature.audit_reference_data import calculate_sha256, connect_read_only

DEFAULT_OUTPUT = LITERATURE_SOURCES / "confirmation_evidence_reviews.json"
APPROVAL_STATUS = "approved_by_project_lead_delegation_2026-07-15"


def parse_arguments() -> argparse.Namespace:
    """Parse audit paths and delegated authorization mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--authorize-under-delegation", action="store_true")
    return parser.parse_args()


def publication_records(connection: object, bibcode: str) -> list[dict[str, object]]:
    """Return associated records for one publication in stable source-row order."""
    rows = connection.execute(
        """
        SELECT r.record_id, r.source_row_locator, r.original_name,
               r.reported_is_ucd, r.reported_confirmation_status,
               d.dataset_name, a.canonical_object_id
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        JOIN object_record_associations a USING (record_id)
        WHERE p.bibcode = ?
        ORDER BY d.dataset_name, r.source_row_locator
        """,
        (bibcode,),
    ).fetchall()
    return [dict(row) for row in rows]


def add_records(
    reviews: list[dict[str, object]],
    records: list[dict[str, object]],
    bibcode: str,
    cohort: str,
    evidence_basis: str,
) -> None:
    """Append approved spectroscopic membership evidence for records."""
    for record in records:
        reviews.append(
            {
                "review_id": f"{cohort}:{record['record_id']}",
                "record_id": record["record_id"],
                "publication_bibcode": bibcode,
                "canonical_object_id_at_review": record["canonical_object_id"],
                "evidence_type": "spectroscopic_membership",
                "evidence_value": "positive",
                "cohort": cohort,
                "evidence_basis": evidence_basis,
            }
        )


def numeric_suffix(value: object) -> int:
    """Return the final integer in a stable source-row locator."""
    return int(str(value).rsplit("_", maxsplit=1)[-1])


def has_velocity(row: object) -> bool:
    """Return whether a Liu supporting row has a reported radial velocity."""
    return any(
        not np.ma.is_masked(row[column]) and float(row[column]) != 0
        for column in ("RVS11", "RVMMT", "RVAAT", "RVSDSS")
    )


def build_reviews(
    connection: object,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    """Build conservative approvals and explicit non-promotions."""
    reviews: list[dict[str, object]] = []
    simple_cohorts = (
        (
            "2007A&A...472..111M",
            "mieske2007_centaurus_velocity_members",
            27,
            "The authoritative table reports radial velocities for 27 Centaurus-cluster compact objects.",
        ),
        (
            "2009AJ....137..498G",
            "gregg2009_fornax_velocity_members",
            60,
            "The authoritative UCD table reports velocities within the paper's explicit Fornax-membership interval.",
        ),
        (
            "2011A&A...531A...4M",
            "misgeld2011_hydra_velocity_members",
            118,
            "The authoritative table identifies all 118 rows as Hydra I cluster members and reports radial velocities.",
        ),
        (
            "2015ApJ...802...30Z",
            "zhang2015_m87_velocity_members",
            97,
            "Every authoritative row reports an M87-consistent heliocentric velocity and UCD structural selection.",
        ),
        (
            "2019A&A...625A..50F",
            "fahrion2019_compiled_velocity_members",
            377,
            "The authoritative compilation supplies a radial velocity and published host context for each associated row.",
        ),
        (
            "2021MNRAS.504.3580S",
            "saifollahi2021_spectroscopic_reference_ucds",
            61,
            "The paper's spectroscopically confirmed table and stated size and magnitude criteria identify these 61 rows as UCDs.",
        ),
        (
            "2016A&A...586A.102V",
            "voggel2016_fornax_velocity_ucds",
            105,
            "The source package reports radial velocities for its resolved Fornax UCD sample.",
        ),
    )
    for bibcode, cohort, expected_count, basis in simple_cohorts:
        records = publication_records(connection, bibcode)
        if bibcode == "2021MNRAS.504.3580S":
            records = [
                record
                for record in records
                if record["reported_confirmation_status"] == "confirmed"
            ]
        if len(records) != expected_count:
            raise RuntimeError(
                f"Expected {expected_count} records for {cohort}, found {len(records)}"
            )
        add_records(reviews, records, bibcode, cohort, basis)

    chiboucas_folder = PROJECT_ROOT / "reference" / "chiboucas2011"
    chiboucas_rows = []
    for file_name in ("table2.dat", "table3.dat"):
        chiboucas_rows.extend(
            ascii.read(
                chiboucas_folder / file_name,
                readme=chiboucas_folder / "ReadMe.txt",
                format="cds",
            )
        )
    chiboucas_records = publication_records(connection, "2011ApJ...737...86C")
    if len(chiboucas_rows) != len(chiboucas_records) != 78:
        raise RuntimeError("Chiboucas source-row count changed")
    chiboucas_members = [
        record
        for row, record in zip(chiboucas_rows, chiboucas_records, strict=True)
        if str(row["Mmb"]) == "Mem"
    ]
    if len(chiboucas_members) != 28:
        raise RuntimeError("Chiboucas member-row count changed")
    add_records(
        reviews,
        chiboucas_members,
        "2011ApJ...737...86C",
        "chiboucas2011_coma_velocity_members",
        "Only rows explicitly marked Mem under the paper's spectroscopic membership rule are approved.",
    )

    liu_folder = PROJECT_ROOT / "reference" / "liu2015"
    liu_records = publication_records(connection, "2015ApJ...812...34L")
    records_by_dataset = {}
    for record in liu_records:
        records_by_dataset.setdefault(str(record["dataset_name"]), []).append(record)
    liu_confirmed_records = []
    for primary_file, supporting_file, dataset_name in (
        ("table2.dat", "table3.dat", "2015ApJ...812...34L.csv"),
        ("table4.dat", "table5.dat", "table4.dat"),
        ("table6.dat", "table7.dat", "table6.dat"),
    ):
        primary_rows = ascii.read(
            liu_folder / primary_file, readme=liu_folder / "ReadMe.txt", format="cds"
        )
        supporting_rows = ascii.read(
            liu_folder / supporting_file,
            readme=liu_folder / "ReadMe.txt",
            format="cds",
            fill_values=[("---", "0")],
        )
        records = sorted(
            records_by_dataset[dataset_name],
            key=lambda row: numeric_suffix(row["source_row_locator"]),
        )
        for primary_row, supporting_row, record in zip(
            primary_rows, supporting_rows, records, strict=True
        ):
            if (
                int(primary_row["UCD"]) == 1
                and int(supporting_row["Class"]) == 1
                and has_velocity(supporting_row)
            ):
                liu_confirmed_records.append(record)
    if len(liu_confirmed_records) != 88:
        raise RuntimeError(
            f"Expected 88 Liu velocity-confirmed UCD rows, found {len(liu_confirmed_records)}"
        )
    add_records(
        reviews,
        liu_confirmed_records,
        "2015ApJ...812...34L",
        "liu2015_class1_velocity_ucds",
        "Only UCD=1, Class=1 rows with at least one reported radial velocity are approved.",
    )

    ko_records = [
        record
        for record in publication_records(connection, "2017ApJ...835..212K")
        if str(record["source_row_locator"]).startswith("table4.dat:")
    ]
    if len(ko_records) != 138:
        raise RuntimeError("Ko spectroscopic UCD row count changed")
    add_records(
        reviews,
        ko_records,
        "2017ApJ...835..212K",
        "ko2017_spectroscopic_ucds",
        "The authoritative table is the combined spectroscopic UCD sample and reports heliocentric velocities.",
    )

    liu2020_records = connection.execute(
        """
        SELECT r.record_id, r.source_row_locator, r.original_name,
               r.reported_is_ucd, r.reported_confirmation_status,
               d.dataset_name, a.canonical_object_id
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        JOIN object_record_associations a USING (record_id)
        WHERE p.bibcode = '2020ApJS..250...17L'
          AND r.reported_is_ucd = 1
          AND json_extract(r.raw_payload_json, '$.authoritative_supporting_row.Cl') = 1
          AND json_extract(r.raw_payload_json, '$.authoritative_supporting_row.HRV') IS NOT NULL
        ORDER BY r.source_row_locator
        """
    ).fetchall()
    liu2020_records = [dict(row) for row in liu2020_records]
    if len(liu2020_records) != 203:
        raise RuntimeError("Liu 2020 velocity-confirmed UCD row count changed")
    add_records(
        reviews,
        liu2020_records,
        "2020ApJS..250...17L",
        "liu2020_class1_velocity_ucds",
        "Only UCD=1, Class=1 rows with a reported heliocentric velocity are approved.",
    )

    with (LITERATURE_SOURCES / "supporting_source_row_links.json").open(
        encoding="utf-8"
    ) as input_file:
        supporting_links = json.load(input_file)["links"]
    voggel_spectroscopic_links = [
        link
        for link in supporting_links
        if link["evidence_type"] == "supporting_spectroscopic_measurement"
    ]
    if len(voggel_spectroscopic_links) != 14:
        raise RuntimeError("Voggel spectroscopic supporting-row count changed")
    records_by_id = {
        record["record_id"]: record
        for bibcode in ("2020ApJ...899..140V", "2022ApJ...929..147D")
        for record in publication_records(connection, bibcode)
    }
    voggel_records = [records_by_id[link["record_id"]] for link in voggel_spectroscopic_links]
    add_records(
        reviews,
        voggel_records,
        "2020ApJ...899..140V",
        "voggel2020_mike_velocity_members",
        "The 14 MIKE rows report radial velocities and uncertainties for new confirmed NGC 5128 objects.",
    )

    cohort_counts = Counter(str(review["cohort"]) for review in reviews)
    expected_total = 1316
    if len(reviews) != expected_total:
        raise RuntimeError(f"Expected {expected_total} confirmation reviews, found {len(reviews)}")
    voggel_non_promotion_records = [
        record
        for record in publication_records(connection, "2020ApJ...899..140V")
        if record["dataset_name"] == "table4.dat"
    ]
    if len(voggel_non_promotion_records) != 57:
        raise RuntimeError("Voggel reference-table non-promotion count changed")
    non_promotion_reviews = [
        {
            "review_id": f"voggel2020_reference_non_promotion:{record['record_id']}",
            "record_id": record["record_id"],
            "publication_bibcode": "2020ApJ...899..140V",
            "canonical_object_id_at_review": record["canonical_object_id"],
            "decision": "retain_candidate",
            "reason": "The local comparison table reports Gaia photometry but not the object-level spectroscopy or resolved-structure evidence required for promotion.",
        }
        for record in voggel_non_promotion_records
    ]
    summary = {
        "approved_evidence_count": len(reviews),
        "approved_record_count": len({str(review["record_id"]) for review in reviews}),
        "approved_canonical_count_at_review": len(
            {str(review["canonical_object_id_at_review"]) for review in reviews}
        ),
        "cohort_counts": dict(sorted(cohort_counts.items())),
        "explicit_non_promotion_count": len(non_promotion_reviews),
    }
    return reviews, non_promotion_reviews, summary


def main() -> None:
    """Write the deterministic confirmation review artifact."""
    arguments = parse_arguments()
    with connect_read_only(arguments.reference_database) as connection:
        reviews, non_promotion_reviews, summary = build_reviews(connection)
    payload = {
        "review_date": date.today().isoformat(),
        "review_status": (
            APPROVAL_STATUS if arguments.authorize_under_delegation else "proposal_only"
        ),
        "ruleset_id": "confirmation_rules_v1",
        "confirmation_changes_authorized": arguments.authorize_under_delegation,
        "identity_changes_authorized": False,
        "classification_changes_outside_ruleset_authorized": False,
        "reference_database_sha256_at_review": calculate_sha256(arguments.reference_database),
        "summary": summary,
        "reviews": reviews,
        "non_promotion_reviews": non_promotion_reviews,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
