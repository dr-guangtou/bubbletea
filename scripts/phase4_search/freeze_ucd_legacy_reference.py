"""Freeze confirmed and published high-probability UCD reference targets."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_REFERENCE_DB_V2,
    PROJECT_ROOT,
    UCD_LEGACY_REFERENCE_CONTRACT,
    UCD_LEGACY_REFERENCE_TARGETS,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import connect_read_only

CONTRACT_VERSION = "ucd_legacy_reference_contract_v1"
SAIFOLLAHI_DATASET_ID = "dataset_5610cf4c81d05a339fa8b38a25388d69"


def joined(values: pd.Series) -> str:
    """Join unique non-empty provenance strings deterministically."""
    cleaned = {
        str(value).strip()
        for value in values.dropna()
        if str(value).strip() and str(value).strip().lower() != "nan"
    }
    return ";".join(sorted(cleaned))


def load_records() -> pd.DataFrame:
    """Load all accepted records for confirmed and Saifollahi reference objects."""
    query = """
        WITH high_probability_objects AS (
            SELECT DISTINCT ora.canonical_object_id
            FROM literature_records AS lr
            JOIN object_record_associations AS ora USING (record_id)
            WHERE lr.dataset_id = ? AND ora.association_status = 'accepted'
        )
        SELECT co.canonical_object_id, co.adopted_ra, co.adopted_dec,
               oc.classification_state, oc.ruleset_id, oc.review_required,
               lr.original_name, lr.host_galaxy, lr.gaia_dr3_id,
               lr.source_row_locator, lr.dataset_id, p.bibcode,
               d.catalog_id, d.local_path,
               CASE WHEN h.canonical_object_id IS NOT NULL THEN 1 ELSE 0 END
                   AS in_saifollahi_high_probability_table
        FROM canonical_objects AS co
        JOIN object_classifications AS oc USING (canonical_object_id)
        LEFT JOIN high_probability_objects AS h USING (canonical_object_id)
        JOIN object_record_associations AS ora
          ON ora.canonical_object_id = co.canonical_object_id
         AND ora.association_status = 'accepted'
        JOIN literature_records AS lr USING (record_id)
        JOIN datasets AS d USING (dataset_id)
        JOIN publications AS p USING (publication_id)
        WHERE oc.classification_state = 'confirmed'
           OR h.canonical_object_id IS NOT NULL
        ORDER BY co.canonical_object_id, p.bibcode, lr.source_row_locator
    """
    with connect_read_only(LITERATURE_REFERENCE_DB_V2) as connection:
        return pd.read_sql_query(query, connection, params=(SAIFOLLAHI_DATASET_ID,))


def main() -> None:
    """Write one count-blind target table and immutable scope contract."""
    records = load_records()
    targets = (
        records.groupby("canonical_object_id", sort=True)
        .agg(
            adopted_ra=("adopted_ra", "first"),
            adopted_dec=("adopted_dec", "first"),
            classification_state=("classification_state", "first"),
            ruleset_id=("ruleset_id", "first"),
            review_required=("review_required", "max"),
            in_saifollahi_high_probability_table=(
                "in_saifollahi_high_probability_table",
                "max",
            ),
            original_names=("original_name", joined),
            host_galaxies=("host_galaxy", joined),
            gaia_dr3_ids=("gaia_dr3_id", joined),
            publication_bibcodes=("bibcode", joined),
            source_row_locators=("source_row_locator", joined),
            source_dataset_ids=("dataset_id", joined),
            source_catalog_ids=("catalog_id", joined),
            source_local_paths=("local_path", joined),
        )
        .reset_index()
    )
    targets["reference_cohort"] = "confirmed_ucd"
    high_probability = targets["in_saifollahi_high_probability_table"].astype(bool)
    targets.loc[high_probability, "reference_cohort"] = "saifollahi_high_probability_candidate"
    targets["gaia_identifier_count"] = targets["gaia_dr3_ids"].map(
        lambda value: 0 if not value else len(value.split(";"))
    )
    targets["gaia_catalog_membership_testability"] = "not_testable_no_unique_gaia_identifier"
    targets.loc[targets["gaia_identifier_count"].eq(1), "gaia_catalog_membership_testability"] = (
        "testable_exact_unique_gaia_identifier"
    )
    targets["legacy_image_testability"] = "testable_at_literature_coordinate"
    targets["legacy_tractor_testability"] = "testable_at_literature_coordinate"
    UCD_LEGACY_REFERENCE_TARGETS.parent.mkdir(parents=True, exist_ok=True)
    targets.to_csv(UCD_LEGACY_REFERENCE_TARGETS, index=False)

    cohort_counts = {
        str(cohort): int(count)
        for cohort, count in targets["reference_cohort"].value_counts().items()
    }
    gaia_counts = {
        str(cohort): int(group["gaia_identifier_count"].eq(1).sum())
        for cohort, group in targets.groupby("reference_cohort")
    }
    checks = {
        "confirmed_cohort_has_680_objects": cohort_counts.get("confirmed_ucd") == 680,
        "saifollahi_cohort_has_44_candidates": cohort_counts.get(
            "saifollahi_high_probability_candidate"
        )
        == 44,
        "cohorts_are_disjoint": len(targets) == sum(cohort_counts.values()) == 724,
        "saifollahi_objects_remain_candidates": targets.loc[
            high_probability, "classification_state"
        ]
        .eq("candidate")
        .all(),
        "all_objects_have_literature_coordinates": targets[["adopted_ra", "adopted_dec"]]
        .notna()
        .all(axis=None),
        "confirmed_gaia_testable_count_is_175": gaia_counts.get("confirmed_ucd") == 175,
        "saifollahi_gaia_testable_count_is_zero": gaia_counts.get(
            "saifollahi_high_probability_candidate"
        )
        == 0,
        "gaia_membership_requires_exact_identifier": targets.loc[
            targets["gaia_catalog_membership_testability"].eq(
                "testable_exact_unique_gaia_identifier"
            ),
            "gaia_identifier_count",
        ]
        .eq(1)
        .all(),
        "no_catalog_or_image_outcome_inspected": True,
        "tractor_model_type_is_not_physical_truth": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    contract = {
        "contract_version": CONTRACT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "frozen_before_gaia_legacy_catalog_and_image_outcomes",
        "plain_language_scope": (
            "Build a visual and photometric reference from all approved confirmed "
            "UCDs and the published Saifollahi high-probability candidate subset."
        ),
        "cohort_definitions": {
            "confirmed_ucd": (
                "Canonical classification_state=confirmed under confirmation_rules_v1."
            ),
            "saifollahi_high_probability_candidate": (
                "Accepted canonical objects from Saifollahi et al. 2021 tablea6.dat; "
                "these remain candidates, not confirmed UCDs."
            ),
        },
        "cohort_counts": cohort_counts,
        "gaia_exact_identifier_testable_counts": gaia_counts,
        "gaia_membership_policy": (
            "Test NSS, galaxy-candidate, and QSO-candidate membership only by one "
            "exact literature Gaia DR3 source identifier."
        ),
        "legacy_tractor_policy": (
            "Query within 2 arcseconds of each literature coordinate, retain every "
            "nearby match, and record nearest and second-nearest separations before "
            "selecting the closest row for per-object summaries."
        ),
        "legacy_image_policy": (
            "Request one 64-by-64 ls-dr10 JPEG at 0.262 arcseconds per pixel for every "
            "coordinate and preserve unavailable or unusable outcomes explicitly."
        ),
        "interpretation_limits": [
            "saifollahi_high_probability_does_not_mean_spectroscopically_confirmed",
            "no_unique_gaia_identifier_means_not_testable_not_nonmember",
            "tractor_psf_type_does_not_prove_star",
            "tractor_extended_type_does_not_prove_galaxy",
            "legacy_image_or_catalog_absence_does_not_disprove_ucd_status",
        ],
        "target_output": {
            "path": str(UCD_LEGACY_REFERENCE_TARGETS.relative_to(PROJECT_ROOT)),
            "sha256": calculate_sha256(UCD_LEGACY_REFERENCE_TARGETS),
        },
        "inputs": {
            str(LITERATURE_REFERENCE_DB_V2.relative_to(PROJECT_ROOT)): calculate_sha256(
                LITERATURE_REFERENCE_DB_V2
            )
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    UCD_LEGACY_REFERENCE_CONTRACT.parent.mkdir(parents=True, exist_ok=True)
    UCD_LEGACY_REFERENCE_CONTRACT.write_text(
        json.dumps(contract, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"UCD Legacy reference freeze failed: {checks}")


if __name__ == "__main__":
    main()
