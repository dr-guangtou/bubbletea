"""Measure pre-selector Gaia conditions for the five-host background review."""

import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_FIELD_CONDITIONS,
    BACKGROUND_REVIEW_FIELD_CONDITIONS_MANIFEST,
    BACKGROUND_REVIEW_FIELD_POSITIONS,
    PROJECT_ROOT,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import (
    DATA_LAB_TAP_URL,
    run_field_queries,
)

LOGGER = logging.getLogger(__name__)


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a local input file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    """Query the frozen review positions and validate the returned measurements."""
    positions = pd.read_csv(BACKGROUND_REVIEW_FIELD_POSITIONS)
    service = tap.TAPService(DATA_LAB_TAP_URL)
    started = perf_counter()
    measured_fields = []
    for field_index, field in enumerate(positions.to_dict(orient="records"), start=1):
        LOGGER.info(
            "Measuring field %d/%d: %s %s",
            field_index,
            len(positions),
            field["host_name"],
            field["field_role"],
        )
        measured_fields.append(run_field_queries(service, field))
    results = pd.DataFrame(measured_fields)
    total_seconds = perf_counter() - started
    checks = {
        "thirteen_fields_measured": len(results) == 13,
        "five_hosts_measured": results["host_rank"].nunique() == 5,
        "five_target_fields_measured": results["field_role"].eq("target_test_patch").sum() == 5,
        "eight_comparison_fields_measured": (~results["field_role"].eq("target_test_patch")).sum()
        == 8,
        "low_transit_retrieval_complete": results["low_transit_source_count"].tolist()
        == results["retrieved_low_transit_source_count"].tolist(),
        "observation_counts_complete": (
            results["visibility_period_non_null_count"]
            .eq(results["source_count_in_frozen_magnitude_domain"])
            .all()
            and results["matched_transit_non_null_count"]
            .eq(results["source_count_in_frozen_magnitude_domain"])
            .all()
        ),
        "positive_patch_area": results["patch_area_square_deg"].gt(0).all(),
        "no_selector_output_used": ~results["query_contract_uses_selector_output"].any(),
        "no_field_is_approved_scientific_background": (
            ~results["eligible_for_scientific_background"].astype(bool)
        ).all(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    BACKGROUND_REVIEW_FIELD_CONDITIONS.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(BACKGROUND_REVIEW_FIELD_CONDITIONS, index=False)
    manifest = {
        "measurement_version": "background_review_field_conditions_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "measurement_scope": "five_hosts_pre_selector_diagnostic_only",
        "data_source": {
            "catalog_release": "Gaia DR3",
            "table": "gaia_dr3.gaia_source",
            "query_service": DATA_LAB_TAP_URL,
            "publication_bibcode": "2023A&A...674A...1G",
            "publication_doi": "10.1051/0004-6361/202243940",
        },
        "input": {
            "path": str(BACKGROUND_REVIEW_FIELD_POSITIONS.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(BACKGROUND_REVIEW_FIELD_POSITIONS),
        },
        "field_count": len(results),
        "total_elapsed_seconds": total_seconds,
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    BACKGROUND_REVIEW_FIELD_CONDITIONS_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Review field-condition validation failed: {checks}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
