"""Validate reference packages and generate authoritative project headline counts."""

import json
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.config import (
    CANONICAL_GAIA_CROSSMATCH_EXPORT,
    CANONICAL_LEGACY_CROSSMATCH_AUDIT,
    CANONICAL_LEGACY_CROSSMATCH_EXPORT,
    LITERATURE_REFERENCE_DB_V2,
    LITERATURE_VALIDATION,
    PROJECT_ROOT,
    PROJECT_STATUS_COUNTS,
    PROVENANCE_DOCUMENTATION_VALIDATION,
    REFERENCE_DIR,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256

PACKAGE_MAPPING_MANIFESTS = [
    PROJECT_ROOT / "data/literature/sources/vizier_retrieval_manifest.json",
    PROJECT_ROOT / "data/literature/sources/literature_retrieval_wave1.json",
]
FILE_DIGEST_MANIFESTS = [
    LITERATURE_VALIDATION / "vizier_retrieval.json",
    LITERATURE_VALIDATION / "vizier_retrieval_wave1.json",
    LITERATURE_VALIDATION / "literature_retrieval_wave1.json",
]
REFERENCE_VALIDATION = LITERATURE_VALIDATION / "literature_reference_v2_validation.json"
DOCUMENTATION_PATHS = [
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "docs/PLAN.md",
    PROJECT_ROOT / "docs/CONTEXT.md",
    PROJECT_ROOT / "data/README.md",
    REFERENCE_DIR / "summary.md",
]
SUPERSEDED_INVENTORIES = {
    PROJECT_ROOT / "data/literature/sources/key_papers.json": (
        "superseded_historical_ingestion_plan"
    ),
    PROJECT_ROOT / "data/literature/sources/vizier_inventory.json": (
        "superseded_historical_vizier_inventory"
    ),
}
MACHINE_READABLE_SUFFIXES = {".csv", ".dat", ".fits", ".xlsx"}


def require(condition: bool, message: str, checks: list[str]) -> None:
    """Record a passed invariant or raise a validation error."""
    if not condition:
        raise RuntimeError(message)
    checks.append(message)


def connect_read_only(path: Path) -> sqlite3.Connection:
    """Open an existing SQLite database without permitting writes."""
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def load_json(path: Path) -> dict[str, Any]:
    """Load one JSON object."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_publications(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    """Load registered publications keyed by ADS bibcode."""
    rows = connection.execute(
        """
        SELECT bibcode, doi, title, publication_year, provenance_status
        FROM publications
        ORDER BY bibcode
        """
    ).fetchall()
    return {row["bibcode"]: dict(row) for row in rows}


def load_package_mapping() -> dict[str, str]:
    """Combine approved VizieR and Wave 1 publication-to-folder mappings."""
    mapping = {}
    for manifest_path in PACKAGE_MAPPING_MANIFESTS:
        for source in load_json(manifest_path)["sources"]:
            bibcode = source["bibcode"]
            folder = source["reference_folder"]
            if bibcode in mapping and mapping[bibcode] != folder:
                raise RuntimeError(f"Conflicting reference folders for {bibcode}")
            mapping[bibcode] = folder
    return mapping


def load_manifest_file_digests() -> dict[tuple[str, str], str]:
    """Load expected package-file digests from all retrieval reports."""
    digests = {}
    for manifest_path in FILE_DIGEST_MANIFESTS:
        for source in load_json(manifest_path)["sources"]:
            folder = source["reference_folder"]
            for file_entry in source["files"]:
                key = (folder, file_entry["file_name"])
                digest = file_entry["sha256"]
                if key in digests and digests[key] != digest:
                    raise RuntimeError(f"Conflicting retrieval digests for {key}")
                digests[key] = digest
    return digests


def audit_package(
    bibcode: str,
    publication: dict[str, Any],
    folder_name: str,
    manifest_digests: dict[tuple[str, str], str],
    checks: list[str],
) -> dict[str, Any]:
    """Validate one registered publication package and every retained file."""
    folder = REFERENCE_DIR / folder_name
    readme_path = folder / "README.md"
    require(folder.is_dir(), f"Reference folder exists for {bibcode}", checks)
    require(readme_path.is_file(), f"Provenance README exists for {bibcode}", checks)
    readme = readme_path.read_text(encoding="utf-8")
    require(bibcode in readme, f"README records bibcode for {bibcode}", checks)
    require(publication["doi"] in readme, f"README records DOI for {bibcode}", checks)

    files = sorted(path for path in folder.iterdir() if path.is_file() and path != readme_path)
    pdf_files = [path for path in files if path.suffix.lower() == ".pdf"]
    machine_files = [path for path in files if path.suffix.lower() in MACHINE_READABLE_SUFFIXES]
    pdf_documented = bool(pdf_files) or "PDF Access Status" in readme
    machine_status_documented = bool(machine_files) or bool(
        re.search(
            r"No (?:VizieR |machine-readable )?package|No package found",
            readme,
            re.IGNORECASE,
        )
    )
    require(pdf_documented, f"PDF or access status is documented for {bibcode}", checks)
    require(
        machine_status_documented,
        f"Machine-readable files or absence are documented for {bibcode}",
        checks,
    )

    file_rows = []
    for path in files:
        digest = calculate_sha256(path)
        manifest_digest = manifest_digests.get((folder_name, path.name))
        digest_documented = manifest_digest == digest or digest in readme
        require(
            digest_documented,
            f"Digest is documented for {folder_name}/{path.name}",
            checks,
        )
        file_rows.append(
            {
                "file_name": path.name,
                "byte_count": path.stat().st_size,
                "sha256": digest,
                "digest_location": "retrieval_manifest" if manifest_digest == digest else "README",
            }
        )
    return {
        "bibcode": bibcode,
        "doi": publication["doi"],
        "reference_folder": folder_name,
        "pdf_status": "local" if pdf_files else "documented_not_local",
        "pdf_file_count": len(pdf_files),
        "machine_readable_file_count": len(machine_files),
        "retained_file_count": len(files),
        "files": file_rows,
    }


def build_status_counts(connection: sqlite3.Connection) -> dict[str, Any]:
    """Measure the canonical counts cited by project documentation."""
    classification_counts = {
        row[0]: row[1]
        for row in connection.execute(
            "SELECT classification_state, COUNT(*) FROM object_classifications GROUP BY 1"
        )
    }
    reference_validation = load_json(REFERENCE_VALIDATION)
    gaia = pd.read_csv(CANONICAL_GAIA_CROSSMATCH_EXPORT)
    legacy = pd.read_csv(CANONICAL_LEGACY_CROSSMATCH_EXPORT)
    legacy_audit = pd.read_csv(CANONICAL_LEGACY_CROSSMATCH_AUDIT)
    return {
        "schema_version": 1,
        "measurement_date": date.today().isoformat(),
        "reference_database": {
            "path": LITERATURE_REFERENCE_DB_V2.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": calculate_sha256(LITERATURE_REFERENCE_DB_V2),
            "publication_count": connection.execute("SELECT COUNT(*) FROM publications").fetchone()[
                0
            ],
            "record_contributing_publication_count": connection.execute(
                """
                SELECT COUNT(DISTINCT p.publication_id)
                FROM publications p
                JOIN datasets d USING (publication_id)
                JOIN literature_records r USING (dataset_id)
                """
            ).fetchone()[0],
            "dataset_count": connection.execute("SELECT COUNT(*) FROM datasets").fetchone()[0],
            "dataset_file_count": connection.execute(
                "SELECT COUNT(*) FROM dataset_files"
            ).fetchone()[0],
            "literature_record_count": connection.execute(
                "SELECT COUNT(*) FROM literature_records"
            ).fetchone()[0],
            "canonical_object_count": connection.execute(
                "SELECT COUNT(*) FROM canonical_objects"
            ).fetchone()[0],
            "classification_counts": classification_counts,
            "review_queue_count": connection.execute(
                "SELECT COUNT(*) FROM review_queue"
            ).fetchone()[0],
            "exact_duplicate_group_count": reference_validation["exact_duplicate_group_count"],
            "validation_failure_count": len(reference_validation["failures"]),
            "open_gate_count": len(reference_validation["open_gates"]),
        },
        "canonical_crossmatches": {
            "gaia_association_count": len(gaia),
            "unique_gaia_source_count": int(gaia["gaia_dr3_id"].nunique()),
            "legacy_match_count": len(legacy),
            "legacy_no_match_count": int((legacy_audit["match_status"] == "no_match").sum()),
            "complete_target_audit_count": len(legacy_audit),
        },
        "command": (
            "PYTHONPATH=. uv run python scripts/phase1_literature/audit_provenance_documentation.py"
        ),
    }


def main() -> None:
    """Write generated counts and validate every package and headline document."""
    checks = []
    with connect_read_only(LITERATURE_REFERENCE_DB_V2) as connection:
        publications = load_publications(connection)
        status_counts = build_status_counts(connection)
    package_mapping = load_package_mapping()
    require(
        set(package_mapping) == set(publications),
        "Every registered publication has exactly one approved reference folder",
        checks,
    )
    manifest_digests = load_manifest_file_digests()
    package_rows = [
        audit_package(
            bibcode,
            publications[bibcode],
            package_mapping[bibcode],
            manifest_digests,
            checks,
        )
        for bibcode in sorted(publications)
    ]

    methodology_folder = REFERENCE_DIR / "wang2023"
    require(methodology_folder.is_dir(), "Wang 2023 methodology package exists", checks)
    require(
        (methodology_folder / "README.md").is_file(),
        "Wang 2023 methodology README exists",
        checks,
    )
    all_package_folders = sorted(
        path.name for path in REFERENCE_DIR.iterdir() if path.is_dir() and path.name != "data"
    )
    expected_folders = set(package_mapping.values()) | {"wang2023"}
    require(
        set(all_package_folders) == expected_folders,
        "Reference folder inventory matches registered and methodology packages",
        checks,
    )

    required_count_strings = ["5,049", "4,359"]
    for documentation_path in DOCUMENTATION_PATHS:
        text = documentation_path.read_text(encoding="utf-8")
        for count_string in required_count_strings:
            require(
                count_string in text,
                f"{documentation_path.relative_to(PROJECT_ROOT)} cites {count_string}",
                checks,
            )

    for inventory_path, expected_status in SUPERSEDED_INVENTORIES.items():
        inventory = load_json(inventory_path)
        require(
            inventory["artifact_status"] == expected_status,
            f"{inventory_path.relative_to(PROJECT_ROOT)} is explicitly historical",
            checks,
        )

    PROJECT_STATUS_COUNTS.write_text(
        json.dumps(status_counts, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    validation = {
        "status": "passed",
        "schema_version": 1,
        "checks": checks,
        "registered_publication_package_count": len(package_rows),
        "tracked_reference_folder_count": len(all_package_folders),
        "local_pdf_package_count": sum(row["pdf_file_count"] > 0 for row in package_rows),
        "documented_nonlocal_pdf_package_count": sum(
            row["pdf_status"] == "documented_not_local" for row in package_rows
        ),
        "packages": package_rows,
        "project_status_counts_path": PROJECT_STATUS_COUNTS.relative_to(PROJECT_ROOT).as_posix(),
        "project_status_counts_sha256": calculate_sha256(PROJECT_STATUS_COUNTS),
    }
    PROVENANCE_DOCUMENTATION_VALIDATION.write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
