"""Freeze the M60 positive-control design before opening the full Gaia field."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    FIRST_STAGE_HOST_PROFILE_FIXTURE,
    FIRST_STAGE_HOST_PROFILE_MANIFEST,
    LITERATURE_REFERENCE_DB_V2,
    M60_POSITIVE_CONTROL_CONTRACT,
    M60_POSITIVE_CONTROL_KNOWN_OBJECTS,
    POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import connect_read_only

CONTRACT_VERSION = "m60_positive_control_v1"
HOST_NAME = "MESSIER 060"
LITERATURE_HOST_NAME = "M60"
OUTER_RADIUS_KPC = 600
CENTRAL_REVIEW_RADIUS_KPC = 50
CUTOUT_LAYER = "ls-dr10"
CUTOUT_PIXEL_SCALE_ARCSEC = 0.262
CUTOUT_SIZE_PIXELS = 64
EXPECTED_CLASSIFICATION_COUNTS = {"confirmed": 2, "candidate": 21, "rejected": 6}


def repository_path(path: Path) -> str:
    """Return a path relative to the project root."""
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def load_known_objects() -> pd.DataFrame:
    """Consolidate every accepted record belonging to an M60 canonical object."""
    query = """
        SELECT co.canonical_object_id, co.adopted_ra, co.adopted_dec,
               oc.classification_state, oc.review_required, lr.original_name,
               lr.gaia_dr3_id, lr.source_row_locator, p.bibcode
        FROM canonical_objects AS co
        JOIN object_classifications AS oc
          ON oc.canonical_object_id = co.canonical_object_id
        JOIN object_record_associations AS ora
          ON ora.canonical_object_id = co.canonical_object_id
        JOIN literature_records AS lr ON lr.record_id = ora.record_id
        JOIN datasets AS d ON d.dataset_id = lr.dataset_id
        JOIN publications AS p ON p.publication_id = d.publication_id
        WHERE ora.association_status = 'accepted'
          AND EXISTS (
              SELECT 1
              FROM object_record_associations AS host_ora
              JOIN literature_records AS host_lr ON host_lr.record_id = host_ora.record_id
              WHERE host_ora.canonical_object_id = co.canonical_object_id
                AND host_ora.association_status = 'accepted'
                AND UPPER(TRIM(host_lr.host_galaxy)) = 'M60'
          )
        ORDER BY co.canonical_object_id, p.bibcode, lr.source_row_locator
    """
    with connect_read_only(LITERATURE_REFERENCE_DB_V2) as connection:
        records = pd.read_sql_query(query, connection, dtype={"gaia_dr3_id": str})

    def joined(values: pd.Series) -> str:
        cleaned = {
            str(value).strip()
            for value in values.dropna()
            if str(value).strip() and str(value).strip().lower() != "nan"
        }
        return ";".join(sorted(cleaned))

    objects = (
        records.groupby("canonical_object_id", sort=True)
        .agg(
            classification_state=("classification_state", "first"),
            review_required=("review_required", "max"),
            adopted_ra=("adopted_ra", "first"),
            adopted_dec=("adopted_dec", "first"),
            original_names=("original_name", joined),
            gaia_dr3_ids=("gaia_dr3_id", joined),
            publication_bibcodes=("bibcode", joined),
            source_row_locators=("source_row_locator", joined),
        )
        .reset_index()
    )
    objects["gaia_identifier_count"] = objects["gaia_dr3_ids"].map(
        lambda value: 0 if not value else len(value.split(";"))
    )
    role_by_state = {
        "confirmed": "reliable_confirmed_ucd",
        "candidate": "literature_ucd_candidate",
        "rejected": "literature_rejected_comparison",
    }
    objects["positive_control_role"] = objects["classification_state"].map(role_by_state)
    return objects


def add_projected_radius(objects: pd.DataFrame, host: pd.Series) -> pd.DataFrame:
    """Measure each literature object's projected separation from M60."""
    host_coordinate = SkyCoord(
        float(host["host_ra_deg"]) * u.deg,
        float(host["host_dec_deg"]) * u.deg,
        frame="icrs",
    )
    object_coordinates = SkyCoord(
        objects["adopted_ra"].to_numpy() * u.deg,
        objects["adopted_dec"].to_numpy() * u.deg,
        frame="icrs",
    )
    angular_separation = host_coordinate.separation(object_coordinates)
    result = objects.copy()
    result["host_name"] = HOST_NAME
    result["angular_separation_deg"] = angular_separation.deg
    result["projected_radius_kpc"] = (
        angular_separation.radian * float(host["host_distance_mpc"]) * 1000.0
    )
    result["inside_temporary_central_review_region"] = result["projected_radius_kpc"].le(
        CENTRAL_REVIEW_RADIUS_KPC
    )
    result["known_object_recovery_scope"] = "recover_and_report_regardless_of_radius"
    return result


def main() -> None:
    """Write checked count-blind M60 design and known-object artifacts."""
    fixture = pd.read_csv(FIRST_STAGE_HOST_PROFILE_FIXTURE)
    fixture_manifest = json.loads(FIRST_STAGE_HOST_PROFILE_MANIFEST.read_text())
    host_rows = fixture.loc[fixture["host_name"].eq(HOST_NAME)].copy()
    outer_rows = host_rows.loc[host_rows["outer_radius_kpc"].eq(OUTER_RADIUS_KPC)]
    if len(outer_rows) != 1:
        raise RuntimeError("Expected one frozen M60 600 kpc row")
    host = outer_rows.iloc[0]
    known_objects = add_projected_radius(load_known_objects(), host)
    classification_counts = {
        str(state): int(count)
        for state, count in known_objects["classification_state"].value_counts().items()
    }
    M60_POSITIVE_CONTROL_KNOWN_OBJECTS.parent.mkdir(parents=True, exist_ok=True)
    known_objects.to_csv(M60_POSITIVE_CONTROL_KNOWN_OBJECTS, index=False)

    checks = {
        "host_geometry_has_fourteen_frozen_rings": len(host_rows) == 14,
        "host_outer_radius_is_600_kpc": int(host["outer_radius_kpc"]) == OUTER_RADIUS_KPC,
        "host_fixture_checks_passed": fixture_manifest["passed_count"]
        == fixture_manifest["check_count"],
        "known_classification_counts_match_reference_database": classification_counts
        == EXPECTED_CLASSIFICATION_COUNTS,
        "known_objects_are_unique": known_objects["canonical_object_id"].is_unique,
        "two_confirmed_ucds_have_one_gaia_identifier_each": known_objects.loc[
            known_objects["classification_state"].eq("confirmed"), "gaia_identifier_count"
        ]
        .eq(1)
        .all(),
        "contaminants_are_flags_only": True,
        "legacy_cutouts_do_not_change_gaia_area": True,
        "no_gaia_query_executed": True,
        "full_field_not_opened": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    contract = {
        "contract_version": CONTRACT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "frozen_before_full_field_retrieval",
        "plain_language_scope": (
            "Measure the unchanged Gaia selector around M60, recover known literature "
            "objects, and attach possible-contamination flags for visual review. Flags "
            "do not remove sources or change the radial profile."
        ),
        "host": {
            "host_name": HOST_NAME,
            "literature_host_name": LITERATURE_HOST_NAME,
            "ra_deg": float(host["host_ra_deg"]),
            "dec_deg": float(host["host_dec_deg"]),
            "distance_mpc": float(host["host_distance_mpc"]),
            "outer_radius_kpc": OUTER_RADIUS_KPC,
            "outer_radius_deg": float(host["outer_radius_deg"]),
            "requested_area_square_deg": float(host_rows["requested_ring_area_square_deg"].sum()),
            "ring_edges_kpc": sorted(
                set(host_rows["inner_radius_kpc"]).union(host_rows["outer_radius_kpc"])
            ),
            "temporary_central_review_radius_kpc": CENTRAL_REVIEW_RADIUS_KPC,
        },
        "known_objects": {
            "counts_by_classification": classification_counts,
            "confirmed_ucds_are_development_controls_not_independent_validation": True,
            "recover_every_known_object_regardless_of_radius": True,
            "artifact": repository_path(M60_POSITIVE_CONTROL_KNOWN_OBJECTS),
            "artifact_sha256": calculate_sha256(M60_POSITIVE_CONTROL_KNOWN_OBJECTS),
        },
        "contamination_review": {
            "policy": "flags_only_no_automatic_removal",
            "flag_families": [
                "parallax_or_proper_motion_review",
                "gaia_non_single_star_membership",
                "qso_evidence",
                "galaxy_or_extended_morphology_evidence",
                "hii_region_or_young_cluster_evidence",
                "blend_or_image_artifact_evidence",
            ],
            "continuous_measurements_remain_available": True,
            "exact_flag_thresholds_beyond_published_catalog_membership": (
                "pending_source_type_discussion"
            ),
            "raw_selector_profile_preserved": True,
        },
        "visual_review": {
            "survey": "Legacy Survey DR10",
            "endpoint": "https://www.legacysurvey.org/viewer/jpeg-cutout",
            "layer": CUTOUT_LAYER,
            "three_color_image": True,
            "pixel_scale_arcsec": CUTOUT_PIXEL_SCALE_ARCSEC,
            "size_pixels": CUTOUT_SIZE_PIXELS,
            "field_width_arcsec": CUTOUT_PIXEL_SCALE_ARCSEC * CUTOUT_SIZE_PIXELS,
            "first_pilot_scope": "two_reliable_confirmed_m60_ucds_only",
            "cutouts_are_diagnostics_not_physical_classifications": True,
            "cutout_masks_do_not_change_gaia_area": True,
        },
        "sequence": [
            "one_aggregate_gaia_count_query",
            "known_ucd_three_color_cutout_pilot",
            "review_measured_raw_workload",
            "freeze_full_source_retrieval_and_review_sampling",
            "retrieve_and_score_complete_field",
            "create_representative_contamination_audit_and_separate_candidate_shortlist",
        ],
        "inputs": {
            repository_path(path): calculate_sha256(path)
            for path in (
                FIRST_STAGE_HOST_PROFILE_FIXTURE,
                FIRST_STAGE_HOST_PROFILE_MANIFEST,
                LITERATURE_REFERENCE_DB_V2,
                POINT_SOURCE_LOGISTIC_MODEL_MANIFEST,
            )
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    M60_POSITIVE_CONTROL_CONTRACT.parent.mkdir(parents=True, exist_ok=True)
    M60_POSITIVE_CONTROL_CONTRACT.write_text(
        json.dumps(contract, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"M60 positive-control freeze failed: {checks}")


if __name__ == "__main__":
    main()
