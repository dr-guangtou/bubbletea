"""Validate large external extragalactic reference catalogs non-destructively.

The source registry is stored in the repository, while the large FITS files live
under ``BUBBLETEA_EXTERNAL_DATA``. The audit reads but never modifies those files.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from astropy.table import Table

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    EXTRAGALACTIC_REFERENCE_AUDIT,
    EXTRAGALACTIC_REFERENCE_DIR,
    EXTRAGALACTIC_REFERENCE_SOURCES,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256


def parse_arguments() -> argparse.Namespace:
    """Parse external catalog, registry, and report paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-directory", type=Path, default=EXTRAGALACTIC_REFERENCE_DIR)
    parser.add_argument("--source-registry", type=Path, default=EXTRAGALACTIC_REFERENCE_SOURCES)
    parser.add_argument("--output", type=Path, default=EXTRAGALACTIC_REFERENCE_AUDIT)
    return parser.parse_args()


def file_measurements(
    path: Path,
    source_id_column: str | None,
    class_count_column: str | None = None,
) -> dict[str, object]:
    """Measure a FITS file without changing it."""
    table = Table.read(path, memmap=True)
    unique_source_id_count = None
    if source_id_column is not None:
        unique_source_id_count = len(set(int(value) for value in table[source_id_column]))
    class_counts = None
    if class_count_column is not None:
        class_counts = dict(
            sorted(Counter(str(value) for value in table[class_count_column]).items())
        )
    return {
        "file_size_bytes": path.stat().st_size,
        "row_count": len(table),
        "unique_source_id_count": unique_source_id_count,
        "class_counts": class_counts,
        "sha256": calculate_sha256(path),
        "columns": list(table.colnames),
    }


def main() -> None:
    """Validate registered files and write a machine-readable audit."""
    arguments = parse_arguments()
    registry = json.loads(arguments.source_registry.read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []
    files: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    for catalog in registry["catalogs"]:
        catalog_id = catalog["catalog_id"]
        file_path = arguments.external_directory / catalog["external_relative_path"]
        check(f"{catalog_id}_file_exists", file_path.is_file(), catalog["external_relative_path"])
        if not file_path.is_file():
            continue
        measured = file_measurements(
            file_path,
            "source_id",
            catalog.get("class_count_column"),
        )
        files.append(
            {
                "catalog_id": catalog_id,
                "external_relative_path": catalog["external_relative_path"],
                **measured,
            }
        )
        for field in ["file_size_bytes", "row_count", "unique_source_id_count", "sha256"]:
            check(
                f"{catalog_id}_{field}",
                measured[field] == catalog[field],
                {"expected": catalog[field], "measured": measured[field]},
            )
        if "class_counts" in catalog:
            check(
                f"{catalog_id}_class_counts",
                measured["class_counts"] == catalog["class_counts"],
                {
                    "expected": catalog["class_counts"],
                    "measured": measured["class_counts"],
                },
            )

        selection_function_path = catalog.get("selection_function_external_relative_path")
        if selection_function_path is None:
            continue
        file_path = arguments.external_directory / selection_function_path
        check(
            f"{catalog_id}_selection_function_file_exists",
            file_path.is_file(),
            selection_function_path,
        )
        if not file_path.is_file():
            continue
        measured = file_measurements(file_path, None)
        files.append(
            {
                "catalog_id": f"{catalog_id}_selection_function",
                "external_relative_path": selection_function_path,
                **measured,
            }
        )
        expected_fields = {
            "file_size_bytes": catalog["selection_function_file_size_bytes"],
            "row_count": catalog["selection_function_row_count"],
            "sha256": catalog["selection_function_sha256"],
        }
        for field, expected in expected_fields.items():
            check(
                f"{catalog_id}_selection_function_{field}",
                measured[field] == expected,
                {"expected": expected, "measured": measured[field]},
            )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "registry_version": registry["registry_version"],
        "source_registry_sha256": calculate_sha256(arguments.source_registry),
        "external_relative_root": registry["external_relative_root"],
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "files": files,
        "checks": checks,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failed:
        failed_names = ", ".join(str(item["name"]) for item in failed)
        raise RuntimeError(f"Extragalactic reference audit failed: {failed_names}")


if __name__ == "__main__":
    main()
