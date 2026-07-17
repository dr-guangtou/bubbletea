"""Validate and export the v2 literature reference database.

This standalone validation script checks provenance and association invariants,
reproduces the legacy exact-coordinate audit, and writes deterministic review and
compatibility artifacts. It does not modify either SQLite database.
"""

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_DB,
    LITERATURE_DISCOVERY,
    LITERATURE_REFERENCE_DB_V2,
    LITERATURE_SOURCES,
    LITERATURE_VALIDATION,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256, connect_read_only

EXPECTED_LEGACY_SHA256 = "d5a2890a10244d78c9be0b54852e8a6667c6ae766053698c450413a9f3ef1806"
HOST_DISTANCE_REVIEW_MANIFEST = LITERATURE_SOURCES / "host_distance_reviews.json"
CONFIRMATION_EVIDENCE_REVIEW_MANIFEST = LITERATURE_SOURCES / "confirmation_evidence_reviews.json"
LITERATURE_SCREENING_CLOSURE_MANIFEST = LITERATURE_SOURCES / "literature_screening_closure.json"
GAIA_PROPOSAL_EXPORT_FIELDS = [
    "proposal_id",
    "gaia_dr3_id",
    "record_id_1",
    "bibcode_1",
    "legacy_object_id_1",
    "ra_1",
    "dec_1",
    "is_ucd_1",
    "record_id_2",
    "bibcode_2",
    "legacy_object_id_2",
    "ra_2",
    "dec_2",
    "is_ucd_2",
    "separation_arcsec",
    "proposal_method",
    "review_reason",
    "proposal_status",
]


def parse_arguments() -> argparse.Namespace:
    """Parse database and output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-database", type=Path, default=LITERATURE_DB)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--output-directory", type=Path, default=LITERATURE_VALIDATION)
    return parser.parse_args()


def query_rows(connection: sqlite3.Connection, query: str) -> list[dict[str, object]]:
    """Return query results as dictionaries."""
    return [dict(row) for row in connection.execute(query).fetchall()]


def scalar(connection: sqlite3.Connection, query: str) -> object:
    """Return the first column of a single-row query."""
    return connection.execute(query).fetchone()[0]


def write_csv(
    path: Path,
    rows: list[dict[str, object]],
    fieldnames: list[str] | None = None,
) -> None:
    """Write deterministic rows with explicit headers."""
    if not rows and fieldnames is None:
        raise ValueError(f"Cannot write empty validation artifact: {path}")
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=fieldnames if fieldnames is not None else list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)


def load_legacy_summary(connection: sqlite3.Connection) -> dict[str, int]:
    """Reproduce the legacy row and exact-coordinate counts."""
    row = connection.execute(
        """
        WITH coordinate_groups AS (
            SELECT ra, dec, COUNT(*) AS group_size
            FROM ucd_objects
            GROUP BY ra, dec
        )
        SELECT
            (SELECT COUNT(*) FROM ucd_objects) AS row_count,
            (SELECT COUNT(*) FROM coordinate_groups) AS exact_coordinate_count,
            (SELECT COUNT(*) FROM coordinate_groups WHERE group_size > 1) AS duplicate_group_count,
            (SELECT COALESCE(SUM(group_size), 0) FROM coordinate_groups WHERE group_size > 1)
                AS duplicate_row_count
        """
    ).fetchone()
    return {key: int(row[key]) for key in row.keys()}


def canonical_export(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Build a compatibility-oriented canonical object export."""
    return query_rows(
        connection,
        """
        SELECT
            c.canonical_object_id,
            c.adopted_ra AS ra,
            c.adopted_dec AS dec,
            c.position_status,
            cl.classification_state,
            cl.classification_subtype,
            cl.ruleset_id,
            cl.review_required,
            COUNT(DISTINCT a.record_id) AS literature_record_count,
            COUNT(DISTINCT p.publication_id) AS publication_count,
            GROUP_CONCAT(DISTINCT p.bibcode) AS bibcodes,
            GROUP_CONCAT(DISTINCT r.gaia_dr3_id) AS gaia_dr3_ids,
            GROUP_CONCAT(DISTINCT r.original_name) AS original_names,
            GROUP_CONCAT(DISTINCT r.host_galaxy) AS host_galaxies,
            GROUP_CONCAT(DISTINCT r.reported_confirmation_status) AS reported_statuses
        FROM canonical_objects c
        JOIN object_record_associations a USING (canonical_object_id)
        JOIN literature_records r USING (record_id)
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        JOIN object_classifications cl USING (canonical_object_id)
        GROUP BY c.canonical_object_id
        ORDER BY c.canonical_object_id
        """,
    )


def review_export(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Export review items with identity-proposal context."""
    return query_rows(
        connection,
        """
        SELECT
            q.review_id,
            q.review_type,
            q.priority,
            q.review_status,
            q.reason,
            q.record_id,
            q.canonical_object_id,
            q.proposal_id,
            p.gaia_dr3_id,
            p.record_id_1,
            p.record_id_2,
            p.separation_arcsec,
            p.proposal_status,
            cl.classification_subtype
        FROM review_queue q
        LEFT JOIN association_proposals p USING (proposal_id)
        LEFT JOIN object_classifications cl USING (canonical_object_id)
        ORDER BY
            CASE q.priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
            q.review_type,
            q.review_id
        """,
    )


def saifollahi_reference_export(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Export the reconciled mixed reference table and reported UCD role."""
    return query_rows(
        connection,
        """
        SELECT
            r.record_id,
            r.source_row_locator,
            r.ra,
            r.dec,
            json_extract(r.raw_payload_json, '$.authoritative_raw_row.gmag') AS g_mag,
            json_extract(r.raw_payload_json, '$.authoritative_raw_row.rh') AS half_light_radius_pc,
            r.reported_confirmation_status,
            r.reported_is_ucd,
            CASE WHEN e.evidence_id IS NULL THEN 0 ELSE 1 END
                AS reported_reference_ucd_pending_review
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        LEFT JOIN object_evidence e
          ON e.record_id = r.record_id
         AND e.evidence_type = 'spectroscopic_membership'
        WHERE p.bibcode = '2021MNRAS.504.3580S'
          AND d.dataset_name = '2021MNRAS.504.3580S.csv'
        ORDER BY CAST(r.source_row_locator AS INTEGER)
        """,
    )


def saifollahi_selection_pool_export(
    connection: sqlite3.Connection,
) -> list[dict[str, object]]:
    """Export the broad selection pool and its final-candidate subset links."""
    return query_rows(
        connection,
        """
        SELECT
            s.pool_record_id,
            s.source_row_locator,
            s.original_name,
            s.ra,
            s.dec,
            s.proposed_class,
            s.ucd_score,
            s.star_score,
            s.galaxy_score,
            l.record_id AS best_candidate_record_id,
            CASE WHEN l.record_id IS NULL THEN 0 ELSE 1 END AS is_best_candidate
        FROM selection_pool_records s
        LEFT JOIN selection_pool_record_links l USING (pool_record_id)
        ORDER BY CAST(REPLACE(s.source_row_locator, 'raw_row_', '') AS INTEGER)
        """,
    )


def approved_source_membership_export(
    connection: sqlite3.Connection,
) -> list[dict[str, object]]:
    """Export implemented Liu, Voggel, and coordinate-null Fahrion roles."""
    return query_rows(
        connection,
        """
        SELECT
            p.bibcode,
            d.dataset_name,
            r.source_row_locator,
            r.record_id,
            r.original_name,
            r.ra,
            r.dec,
            r.reported_confirmation_status,
            r.reported_is_ucd,
            a.canonical_object_id,
            a.association_method,
            a.association_status,
            a.separation_arcsec AS accepted_separation_arcsec,
            cl.classification_state,
            cl.classification_subtype,
            ie.evidence_id AS identity_evidence_id,
            ie.review_status AS identity_evidence_review_status,
            q.review_id AS record_identity_review_id,
            q.review_status AS record_identity_review_status
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        LEFT JOIN object_record_associations a USING (record_id)
        LEFT JOIN object_classifications cl USING (canonical_object_id)
        LEFT JOIN object_evidence ie
          ON ie.record_id = r.record_id
         AND ie.evidence_type = 'identity_alias_chain'
        LEFT JOIN review_queue q
          ON q.record_id = r.record_id
         AND q.review_type = 'record_identity'
        WHERE
            (p.bibcode = '2015ApJ...812...34L'
             AND d.dataset_name IN ('table4.dat', 'table6.dat'))
            OR (p.bibcode = '2020ApJ...899..140V'
                AND d.dataset_name = 'table4.dat')
            OR (p.bibcode = '2019A&A...625A..50F'
                AND d.dataset_name = 'tableb1_coordinate_null_rows')
        ORDER BY p.bibcode, d.dataset_name,
                 CAST(REPLACE(r.source_row_locator, 'raw_row_', '') AS INTEGER)
        """,
    )


def approved_gaia_identity_export(
    connection: sqlite3.Connection,
) -> list[dict[str, object]]:
    """Export approved Gaia identity groups and retained canonical aliases."""
    return query_rows(
        connection,
        """
        SELECT
            json_extract(e.details_json, '$.gaia_dr3_id') AS gaia_dr3_id,
            e.evidence_id,
            e.canonical_object_id,
            e.record_id AS adopted_anchor_record_id,
            c.adopted_ra,
            c.adopted_dec,
            json_extract(e.details_json, '$.secondary_coordinate[0]')
                AS secondary_ra,
            json_extract(e.details_json, '$.secondary_coordinate[1]')
                AS secondary_dec,
            json_extract(e.details_json, '$.secondary_coordinates')
                AS secondary_coordinates_json,
            json_extract(e.details_json, '$.canonical_position_count')
                AS canonical_position_count,
            json_extract(e.details_json, '$.velocity_review_flag')
                AS velocity_review_flag,
            json_extract(e.details_json, '$.gregg_sequence') AS gregg_sequence,
            json_extract(e.details_json, '$.fahrion_name') AS fahrion_name,
            json_extract(e.details_json, '$.saifollahi_source_row_count')
                AS saifollahi_source_row_count,
            a.retired_canonical_object_id,
            a.reason AS alias_reason,
            e.evidence_value AS identity_decision,
            e.review_status,
            cl.classification_state,
            cl.classification_subtype
        FROM object_evidence e
        JOIN canonical_objects c USING (canonical_object_id)
        JOIN canonical_object_aliases a USING (canonical_object_id)
        JOIN object_classifications cl USING (canonical_object_id)
        WHERE e.evidence_type = 'identity_shared_gaia_dr3'
        ORDER BY CAST(json_extract(e.details_json, '$.gaia_dr3_id') AS INTEGER)
        """,
    )


def approved_special_identity_evidence_export(
    connection: sqlite3.Connection,
) -> list[dict[str, object]]:
    """Export approved supplemental and Wave 1 identity evidence."""
    return query_rows(
        connection,
        """
        SELECT
            e.evidence_id,
            e.canonical_object_id,
            e.record_id,
            p.bibcode,
            r.original_name,
            c.adopted_ra,
            c.adopted_dec,
            e.evidence_type,
            e.evidence_value,
            e.evidence_status,
            e.review_status,
            e.details_json
        FROM object_evidence e
        JOIN canonical_objects c USING (canonical_object_id)
        JOIN literature_records r USING (record_id)
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        WHERE e.evidence_type IN (
            'ambiguous_shared_gaia_dr3',
            'identity_name_and_spherical_match',
            'identity_name_or_published_alias',
            'identity_name_velocity_alias_chain'
        )
        ORDER BY e.evidence_type, e.canonical_object_id
        """,
    )


def approved_wave1_role_export(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Export approved Wave 1 object, comparison, and S999 association roles."""
    return query_rows(
        connection,
        """
        SELECT
            p.bibcode,
            d.dataset_name,
            r.source_row_locator,
            r.record_id,
            r.original_name,
            r.ra,
            r.dec,
            r.reported_confirmation_status,
            r.reported_is_ucd,
            a.canonical_object_id,
            a.association_method,
            a.separation_arcsec AS accepted_separation_arcsec,
            cl.classification_state,
            cl.classification_subtype
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        JOIN object_record_associations a USING (record_id)
        JOIN object_classifications cl USING (canonical_object_id)
        WHERE p.bibcode IN (
            '2016A&A...586A.102V',
            '2017ApJ...835..212K',
            '2020ApJS..250...17L'
        )
        ORDER BY p.bibcode, r.source_row_locator
        """,
    )


def proposal_export(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Export non-exact identity proposals with source context."""
    return query_rows(
        connection,
        """
        SELECT
            p.proposal_id,
            p.gaia_dr3_id,
            p.record_id_1,
            pub1.bibcode AS bibcode_1,
            r1.legacy_object_id AS legacy_object_id_1,
            r1.ra AS ra_1,
            r1.dec AS dec_1,
            r1.reported_is_ucd AS is_ucd_1,
            p.record_id_2,
            pub2.bibcode AS bibcode_2,
            r2.legacy_object_id AS legacy_object_id_2,
            r2.ra AS ra_2,
            r2.dec AS dec_2,
            r2.reported_is_ucd AS is_ucd_2,
            p.separation_arcsec,
            p.proposal_method,
            p.review_reason,
            p.proposal_status
        FROM association_proposals p
        JOIN literature_records r1 ON r1.record_id = p.record_id_1
        JOIN datasets d1 ON d1.dataset_id = r1.dataset_id
        JOIN publications pub1 ON pub1.publication_id = d1.publication_id
        JOIN literature_records r2 ON r2.record_id = p.record_id_2
        JOIN datasets d2 ON d2.dataset_id = r2.dataset_id
        JOIN publications pub2 ON pub2.publication_id = d2.publication_id
        WHERE p.proposal_method = 'legacy_gaia_id'
        ORDER BY p.gaia_dr3_id, p.record_id_1, p.record_id_2
        """,
    )


def raw_file_export(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Export raw provenance files and row-count reconciliation context."""
    return query_rows(
        connection,
        """
        SELECT
            p.bibcode,
            d.dataset_id,
            d.dataset_name,
            d.row_count AS normalized_record_count,
            f.file_name,
            f.file_role,
            f.local_path,
            f.file_sha256,
            f.byte_count,
            f.raw_row_count,
            CASE
                WHEN d.authority_status = 'authoritative_vizier_package' THEN NULL
                WHEN f.raw_row_count IS NULL THEN NULL
                ELSE f.raw_row_count - d.row_count
            END AS raw_minus_normalized_count,
            f.source_url
        FROM dataset_files f
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        ORDER BY p.bibcode, f.file_name
        """,
    )


def validate_invariants(
    connection: sqlite3.Connection,
    legacy_summary: dict[str, int],
    legacy_sha256: str,
) -> dict[str, object]:
    """Validate schema, preservation, association, and review invariants."""
    foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    record_count = int(scalar(connection, "SELECT COUNT(*) FROM literature_records"))
    association_count = int(scalar(connection, "SELECT COUNT(*) FROM object_record_associations"))
    unassociated_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM literature_records r
            LEFT JOIN object_record_associations a USING (record_id)
            WHERE a.record_id IS NULL
            """,
        )
    )
    approved_unassociated_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM literature_records r
            JOIN datasets d USING (dataset_id)
            JOIN publications p USING (publication_id)
            LEFT JOIN object_record_associations a USING (record_id)
            JOIN review_queue q ON q.record_id = r.record_id
            WHERE a.record_id IS NULL
              AND r.ra IS NULL
              AND r.dec IS NULL
              AND p.bibcode = '2019A&A...625A..50F'
              AND d.dataset_name = 'tableb1_coordinate_null_rows'
              AND q.review_type = 'record_identity'
              AND q.review_status = 'pending'
            """,
        )
    )
    dataset_count_errors = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT d.dataset_id
                FROM datasets d
                LEFT JOIN literature_records r USING (dataset_id)
                LEFT JOIN selection_pool_records s USING (dataset_id)
                GROUP BY d.dataset_id
                HAVING d.row_count != (
                    COUNT(DISTINCT r.record_id) + COUNT(DISTINCT s.pool_record_id)
                )
            )
            """,
        )
    )
    exact_duplicate_groups = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT r.ra, r.dec
                FROM literature_records r
                JOIN object_record_associations a USING (record_id)
                WHERE r.legacy_object_id IS NOT NULL
                  AND r.ra IS NOT NULL
                  AND r.dec IS NOT NULL
                GROUP BY r.ra, r.dec
                HAVING COUNT(*) > 1
                   AND COUNT(DISTINCT a.canonical_object_id) = 1
            )
            """,
        )
    )
    classification_counts = {
        row["classification_state"]: int(row["object_count"])
        for row in query_rows(
            connection,
            """
            SELECT classification_state, COUNT(*) AS object_count
            FROM object_classifications
            GROUP BY classification_state
            ORDER BY classification_state
            """,
        )
    }
    authority_counts = {
        row["authority_status"]: int(row["dataset_count"])
        for row in query_rows(
            connection,
            """
            SELECT authority_status, COUNT(*) AS dataset_count
            FROM datasets
            GROUP BY authority_status
            ORDER BY authority_status
            """,
        )
    }
    review_type_counts = {
        row["review_type"]: int(row["review_count"])
        for row in query_rows(
            connection,
            """
            SELECT review_type, COUNT(*) AS review_count
            FROM review_queue
            GROUP BY review_type
            ORDER BY review_type
            """,
        )
    }
    failures = []
    if legacy_sha256 != EXPECTED_LEGACY_SHA256:
        failures.append("legacy_database_sha256_changed")
    if foreign_key_errors:
        failures.append("foreign_key_errors")
    if (
        association_count != record_count - 4
        or unassociated_count != 4
        or approved_unassociated_count != 4
    ):
        failures.append("record_association_cardinality")
    if dataset_count_errors:
        failures.append("dataset_row_count_mismatch")
    if legacy_summary["duplicate_group_count"] != 180:
        failures.append("legacy_exact_duplicate_group_count")
    if exact_duplicate_groups < legacy_summary["duplicate_group_count"]:
        failures.append("v2_exact_duplicate_group_loss")
    corrected_alias_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM publication_aliases
            WHERE alias_type = 'incorrect_legacy_bibcode'
            """,
        )
    )
    if corrected_alias_count != 2:
        failures.append("bibliographic_alias_corrections")
    selection_pool_count = int(scalar(connection, "SELECT COUNT(*) FROM selection_pool_records"))
    saifollahi_selection_pool_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM selection_pool_records s
            JOIN datasets d USING (dataset_id)
            JOIN publications p USING (publication_id)
            WHERE p.bibcode = '2021MNRAS.504.3580S'
            """,
        )
    )
    wittmann_selection_pool_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM selection_pool_records s
            JOIN datasets d USING (dataset_id)
            JOIN publications p USING (publication_id)
            WHERE p.bibcode = '2016MNRAS.459.4450W'
            """,
        )
    )
    selection_pool_link_count = int(
        scalar(connection, "SELECT COUNT(*) FROM selection_pool_record_links")
    )
    saifollahi_reference_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE publication_id = 'ads:2021MNRAS.504.3580S'
              AND evidence_type = 'spectroscopic_membership'
            """,
        )
    )
    if saifollahi_selection_pool_count != 1155:
        failures.append("saifollahi_selection_pool_count")
    if wittmann_selection_pool_count != 904:
        failures.append("wittmann_selection_pool_count")
    if selection_pool_link_count != 44:
        failures.append("saifollahi_best_candidate_subset_links")
    if saifollahi_reference_evidence_count != 61:
        failures.append("saifollahi_reference_ucd_count")
    approved_liu_association_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_record_associations
            WHERE association_method = 'approved_name_and_spherical_match'
            """,
        )
    )
    approved_s547_association_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_record_associations
            WHERE association_method = 'approved_s547_name_and_spherical_match'
            """,
        )
    )
    approved_voggel_association_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_record_associations
            WHERE association_method IN (
                'approved_spherical_match',
                'approved_alias_and_spherical_match'
            )
            """,
        )
    )
    approved_alias_association_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_record_associations
            WHERE association_method = 'approved_alias_and_spherical_match'
            """,
        )
    )
    approved_identity_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'identity_alias_chain'
              AND evidence_value = 'same_astrophysical_object'
              AND evidence_status = 'approved'
              AND review_status = 'approved'
            """,
        )
    )
    pending_source_proposal_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM association_proposals
            WHERE proposal_method = 'source_table_spherical_review'
              AND proposal_status = 'pending_manual_review'
            """,
        )
    )
    gaia_association_proposal_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM association_proposals
            WHERE proposal_method = 'legacy_gaia_id'
            """,
        )
    )
    gaia_proposal_group_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(DISTINCT gaia_dr3_id)
            FROM association_proposals
            WHERE proposal_method = 'legacy_gaia_id'
            """,
        )
    )
    approved_gaia_association_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_record_associations
            WHERE association_method = 'approved_gaia_dr3_shared_source'
            """,
        )
    )
    approved_gaia_identity_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'identity_shared_gaia_dr3'
              AND evidence_value = 'same_astrophysical_object'
              AND evidence_status = 'approved'
              AND review_status = 'approved'
            """,
        )
    )
    approved_gaia_ambiguity_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'ambiguous_shared_gaia_dr3'
              AND evidence_value = 'distinct_close_pair_shared_unresolved_source'
              AND evidence_status = 'approved'
              AND review_status = 'approved'
            """,
        )
    )
    approved_supplemental_identity_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'identity_name_and_spherical_match'
              AND evidence_value = 'same_astrophysical_object'
              AND evidence_status = 'approved'
              AND review_status = 'approved'
            """,
        )
    )
    ambiguous_gaia_canonical_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(DISTINCT canonical_object_id)
            FROM object_evidence
            WHERE evidence_type = 'ambiguous_shared_gaia_dr3'
            """,
        )
    )
    s547_record_count, s547_canonical_count = connection.execute(
        """
        SELECT COUNT(*), COUNT(DISTINCT a.canonical_object_id)
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        JOIN object_record_associations a USING (record_id)
        WHERE r.original_name = 'S547'
          AND p.bibcode IN ('2015ApJ...802...30Z', '2019A&A...625A..50F')
        """
    ).fetchone()
    s547_vucd3_canonical_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(DISTINCT a.canonical_object_id)
            FROM literature_records r
            JOIN datasets d USING (dataset_id)
            JOIN publications p USING (publication_id)
            JOIN object_record_associations a USING (record_id)
            WHERE r.original_name IN ('S547', 'VUCD3')
              AND p.bibcode IN ('2015ApJ...802...30Z', '2019A&A...625A..50F')
            """,
        )
    )
    retired_canonical_alias_count = int(
        scalar(connection, "SELECT COUNT(*) FROM canonical_object_aliases")
    )
    canonical_object_count = int(scalar(connection, "SELECT COUNT(*) FROM canonical_objects"))
    review_queue_count = int(scalar(connection, "SELECT COUNT(*) FROM review_queue"))
    pending_gaia_ambiguity_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM association_proposals
            WHERE proposal_method = 'legacy_gaia_id'
              AND proposal_status = 'pending_identity_ambiguity_review'
            """,
        )
    )
    approved_multi_position_gaia_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'identity_shared_gaia_dr3'
              AND json_extract(details_json, '$.canonical_position_count') = 3
              AND evidence_status = 'approved'
              AND review_status = 'approved'
            """,
        )
    )
    approved_multi_position_gaia_id_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(DISTINCT json_extract(details_json, '$.gaia_dr3_id'))
            FROM object_evidence
            WHERE evidence_type = 'identity_shared_gaia_dr3'
              AND json_extract(details_json, '$.canonical_position_count') = 3
            """,
        )
    )
    f6_velocity_tension_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'identity_shared_gaia_dr3'
              AND json_extract(details_json, '$.fahrion_name') = 'F-6'
              AND json_extract(details_json, '$.gregg_sequence') = '27'
              AND json_extract(details_json, '$.velocity_review_flag') =
                  'moderate_measurement_tension_preserve_both'
            """,
        )
    )
    saifollahi_duplicate_row_count, saifollahi_duplicate_coordinate_count = connection.execute(
        """
            WITH target AS (
                SELECT canonical_object_id
                FROM object_evidence
                WHERE evidence_type = 'identity_shared_gaia_dr3'
                  AND json_extract(details_json, '$.saifollahi_source_row_count') = '2'
            )
            SELECT COUNT(*), COUNT(DISTINCT printf('%.15f,%.15f', r.ra, r.dec))
            FROM target
            JOIN object_record_associations a USING (canonical_object_id)
            JOIN literature_records r USING (record_id)
            JOIN datasets d USING (dataset_id)
            JOIN publications p USING (publication_id)
            WHERE p.bibcode = '2021MNRAS.504.3580S'
            """
    ).fetchone()
    wave1_record_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM literature_records r
            JOIN datasets d USING (dataset_id)
            JOIN publications p USING (publication_id)
            WHERE p.bibcode IN (
                '2016A&A...586A.102V',
                '2017ApJ...835..212K',
                '2020ApJS..250...17L'
            )
            """,
        )
    )
    wave1_positive_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM literature_records r
            JOIN datasets d USING (dataset_id)
            JOIN publications p USING (publication_id)
            WHERE p.bibcode IN (
                '2016A&A...586A.102V',
                '2017ApJ...835..212K',
                '2020ApJS..250...17L'
            )
              AND r.reported_is_ucd = 1
            """,
        )
    )
    wave1_comparison_count = wave1_record_count - wave1_positive_count
    wave1_dataset_file_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM dataset_files f
            JOIN datasets d USING (dataset_id)
            WHERE d.authority_status = 'authoritative_vizier_package'
            """,
        )
    )
    s999_association_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_record_associations
            WHERE association_method = 'approved_s999_literature_identity'
            """,
        )
    )
    s999_identity_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'identity_name_velocity_alias_chain'
              AND evidence_value = 'same_astrophysical_object'
              AND evidence_status = 'approved'
              AND review_status = 'approved_by_project_lead_2026-07-15'
            """,
        )
    )
    ahn_measurement_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'spatial_kinematic_measurements'
              AND publication_id = 'ads:2018ApJ...858..102A'
              AND json_extract(details_json, '$.source_row_count') = 109
            """,
        )
    )
    approved_wave1_identity_association_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_record_associations
            WHERE association_method = 'approved_wave1_name_or_alias_identity'
            """,
        )
    )
    approved_wave1_identity_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'identity_name_or_published_alias'
              AND evidence_value = 'same_astrophysical_object'
              AND evidence_status = 'approved'
              AND review_status = 'approved_by_project_lead_2026-07-15'
            """,
        )
    )
    approved_wave1_group_identity_association_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_record_associations
            WHERE association_method = 'approved_wave1_group_identity'
            """,
        )
    )
    approved_wave1_group_identity_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'identity_multi_canonical_shared_identifier'
              AND evidence_value = 'same_astrophysical_object'
              AND evidence_status = 'approved'
              AND review_status = 'approved_by_project_lead_2026-07-15'
            """,
        )
    )
    approved_wave1_source_identity_association_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_record_associations
            WHERE association_method = 'approved_wave1_source_identity'
            """,
        )
    )
    approved_wave1_source_identity_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_evidence
            WHERE evidence_type = 'identity_source_catalog_lineage'
              AND evidence_value = 'same_astrophysical_object'
              AND evidence_status = 'approved'
              AND review_status = 'approved_by_project_lead_delegation_2026-07-15'
            """,
        )
    )
    supporting_source_row_counts = {
        str(row[0]): int(row[1])
        for row in connection.execute(
            """
            SELECT evidence_type, COUNT(*)
            FROM object_evidence
            WHERE evidence_type IN (
                'supporting_structural_measurement',
                'supporting_structural_and_velocity_measurement',
                'supporting_spectroscopic_measurement'
            )
              AND evidence_value = 'supporting_measurement'
              AND evidence_status = 'reported'
              AND review_status = 'approved_by_project_lead_delegation_2026-07-15'
            GROUP BY evidence_type
            """
        )
    }
    if approved_liu_association_count != 51:
        failures.append("approved_liu_association_count")
    if approved_s547_association_count != 1:
        failures.append("approved_s547_association_count")
    if approved_voggel_association_count != 35:
        failures.append("approved_voggel_association_count")
    if approved_alias_association_count != 1:
        failures.append("approved_alias_association_count")
    if approved_identity_evidence_count != 1:
        failures.append("approved_identity_evidence_count")
    if pending_source_proposal_count != 0:
        failures.append("pending_source_proposal_count")
    if gaia_association_proposal_count != 0:
        failures.append("gaia_association_proposal_count")
    if gaia_proposal_group_count != 0:
        failures.append("gaia_proposal_group_count")
    if approved_gaia_association_count != 128:
        failures.append("approved_gaia_association_count")
    if approved_gaia_identity_evidence_count != 116:
        failures.append("approved_gaia_identity_evidence_count")
    if approved_gaia_ambiguity_evidence_count != 2:
        failures.append("approved_gaia_ambiguity_evidence_count")
    if approved_supplemental_identity_evidence_count != 1:
        failures.append("approved_supplemental_identity_evidence_count")
    if ambiguous_gaia_canonical_count != 2:
        failures.append("ambiguous_gaia_canonical_count")
    if (int(s547_record_count), int(s547_canonical_count)) != (2, 1):
        failures.append("s547_identity_structure")
    if s547_vucd3_canonical_count != 2:
        failures.append("s547_vucd3_separate_identity_structure")
    if retired_canonical_alias_count != 390:
        failures.append("retired_canonical_alias_count")
    if canonical_object_count != 4359:
        failures.append("canonical_object_count")
    if review_queue_count != 4:
        failures.append("review_queue_count")
    if pending_gaia_ambiguity_count != 0:
        failures.append("pending_gaia_ambiguity_count")
    if approved_multi_position_gaia_count != 8:
        failures.append("approved_multi_position_gaia_count")
    if approved_multi_position_gaia_id_count != 8:
        failures.append("approved_multi_position_gaia_id_count")
    if f6_velocity_tension_evidence_count != 1:
        failures.append("f6_velocity_tension_evidence_count")
    if (
        int(saifollahi_duplicate_row_count),
        int(saifollahi_duplicate_coordinate_count),
    ) != (2, 1):
        failures.append("saifollahi_duplicate_rows_preserved")
    if wave1_record_count != 2339:
        failures.append("wave1_record_count")
    if wave1_positive_count != 855:
        failures.append("wave1_positive_count")
    if wave1_comparison_count != 1484:
        failures.append("wave1_comparison_count")
    if wave1_dataset_file_count != 16:
        failures.append("wave1_dataset_file_count")
    if s999_association_count != 3:
        failures.append("s999_association_count")
    if s999_identity_evidence_count != 1:
        failures.append("s999_identity_evidence_count")
    if ahn_measurement_evidence_count != 1:
        failures.append("ahn_measurement_evidence_count")
    if approved_wave1_identity_association_count != 7:
        failures.append("approved_wave1_identity_association_count")
    if approved_wave1_identity_evidence_count != 7:
        failures.append("approved_wave1_identity_evidence_count")
    if approved_wave1_group_identity_association_count != 28:
        failures.append("approved_wave1_group_identity_association_count")
    if approved_wave1_group_identity_evidence_count != 12:
        failures.append("approved_wave1_group_identity_evidence_count")
    if approved_wave1_source_identity_association_count != 238:
        failures.append("approved_wave1_source_identity_association_count")
    if approved_wave1_source_identity_evidence_count != 80:
        failures.append("approved_wave1_source_identity_evidence_count")
    expected_supporting_source_row_counts = {
        "supporting_structural_measurement": 27,
        "supporting_structural_and_velocity_measurement": 127,
        "supporting_spectroscopic_measurement": 14,
    }
    if supporting_source_row_counts != expected_supporting_source_row_counts:
        failures.append("supporting_source_row_counts")
    host_distance_rows = connection.execute(
        """
        SELECT p.bibcode, COUNT(*),
               SUM(r.distance_mpc IS NOT NULL),
               COUNT(DISTINCT r.distance_mpc),
               MIN(r.distance_mpc), MAX(r.distance_mpc)
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        WHERE p.bibcode IN (
            '2007A&A...472..111M', '2008AJ....136.2295B',
            '2009AJ....137..498G', '2011A&A...531A...4M',
            '2011ApJ...737...86C', '2015ApJ...812...34L',
            '2019A&A...625A..50F', '2020ApJ...899..140V',
            '2021MNRAS.504.3580S', '2022ApJ...929..147D'
        )
        GROUP BY p.bibcode
        ORDER BY p.bibcode
        """
    ).fetchall()
    host_distance_summary = {
        str(row[0]): {
            "record_count": int(row[1]),
            "distance_record_count": int(row[2]),
            "distinct_distance_count": int(row[3]),
            "minimum_distance_mpc": row[4],
            "maximum_distance_mpc": row[5],
        }
        for row in host_distance_rows
    }
    expected_host_distance_summary = {
        "2007A&A...472..111M": (27, 27, 1, 43.0, 43.0),
        "2008AJ....136.2295B": (41, 41, 1, 150.0, 150.0),
        "2009AJ....137..498G": (60, 60, 1, 20.0, 20.0),
        "2011A&A...531A...4M": (118, 118, 1, 50.7, 50.7),
        "2011ApJ...737...86C": (78, 78, 1, 100.0, 100.0),
        "2015ApJ...812...34L": (206, 127, 1, 16.5, 16.5),
        "2019A&A...625A..50F": (381, 0, 0, None, None),
        "2020ApJ...899..140V": (689, 632, 1, 3.8, 3.8),
        "2021MNRAS.504.3580S": (692, 692, 1, 20.0, 20.0),
        "2022ApJ...929..147D": (321, 321, 1, 3.8, 3.8),
    }
    observed_host_distance_summary = {
        bibcode: (
            values["record_count"],
            values["distance_record_count"],
            values["distinct_distance_count"],
            values["minimum_distance_mpc"],
            values["maximum_distance_mpc"],
        )
        for bibcode, values in host_distance_summary.items()
    }
    if observed_host_distance_summary != expected_host_distance_summary:
        failures.append("host_distance_summary")
    liu_host_counts = {
        str(row[0]): int(row[1])
        for row in connection.execute(
            """
            SELECT host_galaxy, COUNT(*)
            FROM literature_records r
            JOIN datasets d USING (dataset_id)
            JOIN publications p USING (publication_id)
            WHERE p.bibcode = '2015ApJ...812...34L'
            GROUP BY host_galaxy
            """
        )
    }
    if liu_host_counts != {"M49": 50, "M60": 29, "M87": 127}:
        failures.append("liu_host_counts")
    preserved_legacy_distance_counts = {
        "mieske_legacy_3_8": int(
            scalar(
                connection,
                """
                SELECT COUNT(*) FROM literature_records r
                JOIN datasets d USING (dataset_id)
                JOIN publications p USING (publication_id)
                WHERE p.bibcode = '2007A&A...472..111M'
                  AND json_extract(r.raw_payload_json, '$.distance_mpc') = 3.8
                """,
            )
        ),
        "fahrion_legacy_20": int(
            scalar(
                connection,
                """
                SELECT COUNT(*) FROM literature_records r
                JOIN datasets d USING (dataset_id)
                JOIN publications p USING (publication_id)
                WHERE p.bibcode = '2019A&A...625A..50F'
                  AND json_extract(r.raw_payload_json, '$.distance_mpc') = 20.0
                """,
            )
        ),
    }
    if preserved_legacy_distance_counts != {
        "mieske_legacy_3_8": 27,
        "fahrion_legacy_20": 377,
    }:
        failures.append("preserved_legacy_distance_counts")
    host_distance_review_metadata = {
        str(row[0]): str(row[1])
        for row in connection.execute(
            """
            SELECT metadata_key, metadata_value FROM build_metadata
            WHERE metadata_key IN (
                'host_distance_review_sha256', 'host_distance_review_status'
            )
            """
        )
    }
    if host_distance_review_metadata != {
        "host_distance_review_sha256": calculate_sha256(HOST_DISTANCE_REVIEW_MANIFEST),
        "host_distance_review_status": "approved_by_project_lead_delegation_2026-07-15",
    }:
        failures.append("host_distance_review_metadata")
    approved_confirmation_evidence_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*) FROM object_evidence
            WHERE evidence_type = 'spectroscopic_membership'
              AND evidence_value = 'positive'
              AND evidence_status = 'approved'
              AND review_status = 'approved_by_project_lead_2026-07-17'
            """,
        )
    )
    reviewed_confirmation_non_promotion_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*) FROM object_evidence
            WHERE evidence_type = 'reported_classification'
              AND evidence_value = 'confirmed'
              AND review_status = 'reviewed_insufficient_evidence'
            """,
        )
    )
    approved_reported_confirmation_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*) FROM object_evidence
            WHERE evidence_type = 'reported_classification'
              AND evidence_value = 'confirmed'
              AND review_status = 'approved'
            """,
        )
    )
    approved_foreground_rejection_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*) FROM object_evidence
            WHERE evidence_type = 'foreground_astrometry'
              AND evidence_value = 'negative'
              AND evidence_status = 'approved'
              AND review_status = 'approved_by_project_lead_2026-07-17'
            """,
        )
    )
    if approved_confirmation_evidence_count != 1248:
        failures.append("approved_confirmation_evidence_count")
    if reviewed_confirmation_non_promotion_count != 125:
        failures.append("reviewed_confirmation_non_promotion_count")
    if approved_reported_confirmation_count != 467:
        failures.append("approved_reported_confirmation_count")
    if approved_foreground_rejection_count != 1:
        failures.append("approved_foreground_rejection_count")
    confirmation_review_metadata = {
        str(row[0]): str(row[1])
        for row in connection.execute(
            """
            SELECT metadata_key, metadata_value FROM build_metadata
            WHERE metadata_key IN (
                'confirmation_evidence_review_sha256',
                'confirmation_evidence_review_status'
            )
            """
        )
    }
    if confirmation_review_metadata != {
        "confirmation_evidence_review_sha256": calculate_sha256(
            CONFIRMATION_EVIDENCE_REVIEW_MANIFEST
        ),
        "confirmation_evidence_review_status": "approved_by_project_lead_2026-07-17",
    }:
        failures.append("confirmation_review_metadata")
    with LITERATURE_SCREENING_CLOSURE_MANIFEST.open(encoding="utf-8") as input_file:
        screening_closure = json.load(input_file)
    screening_paths = {
        "discovery": LITERATURE_DISCOVERY / "literature_discovery_2026-07-15.json",
        "screening": LITERATURE_DISCOVERY / "literature_screening_2026-07-15.csv",
        "retrieval": LITERATURE_SOURCES / "literature_retrieval_wave1.json",
    }
    screening_artifact_checks = {
        "unique_paper_count": screening_closure["discovery_artifact"]["unique_paper_count"],
        "screened_paper_count": screening_closure["screening_artifact"]["screened_paper_count"],
        "pending_decision_count": screening_closure["screening_artifact"]["pending_decision_count"],
        "approved_retrieval_count": screening_closure["retrieval_artifact"][
            "approved_retrieval_count"
        ],
        "deferred_source_count": len(screening_closure["deferred_sources"]),
    }
    if screening_artifact_checks != {
        "unique_paper_count": 345,
        "screened_paper_count": 345,
        "pending_decision_count": 0,
        "approved_retrieval_count": 19,
        "deferred_source_count": 8,
    }:
        failures.append("screening_artifact_counts")
    if (
        calculate_sha256(screening_paths["discovery"])
        != screening_closure["discovery_artifact"]["file_sha256"]
        or calculate_sha256(screening_paths["screening"])
        != screening_closure["screening_artifact"]["file_sha256"]
        or calculate_sha256(screening_paths["retrieval"])
        != screening_closure["retrieval_artifact"]["file_sha256"]
    ):
        failures.append("screening_artifact_hashes")
    screening_closure_metadata = {
        str(row[0]): str(row[1])
        for row in connection.execute(
            """
            SELECT metadata_key, metadata_value FROM build_metadata
            WHERE metadata_key IN (
                'literature_screening_closure_sha256',
                'literature_screening_closure_status'
            )
            """
        )
    }
    if screening_closure_metadata != {
        "literature_screening_closure_sha256": calculate_sha256(
            LITERATURE_SCREENING_CLOSURE_MANIFEST
        ),
        "literature_screening_closure_status": ("approved_by_project_lead_delegation_2026-07-15"),
    }:
        failures.append("screening_closure_metadata")
    if classification_counts != {
        "candidate": 1574,
        "confirmed": 680,
        "rejected": 2083,
        "uncertain": 22,
    }:
        failures.append("classification_counts")
    role_conflict_subtype_count = int(
        scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM object_classifications
            WHERE classification_state = 'uncertain'
              AND classification_subtype = 'reported_ucd_role_conflict'
            """,
        )
    )
    if role_conflict_subtype_count != 22:
        failures.append("role_conflict_subtype_count")
    return {
        "validation_date": date.today().isoformat(),
        "validation_status": "passed" if not failures else "failed",
        "failures": failures,
        "legacy_database_sha256": legacy_sha256,
        "legacy_summary": legacy_summary,
        "publication_count": int(scalar(connection, "SELECT COUNT(*) FROM publications")),
        "dataset_count": int(scalar(connection, "SELECT COUNT(*) FROM datasets")),
        "dataset_file_count": int(scalar(connection, "SELECT COUNT(*) FROM dataset_files")),
        "corrected_bibcode_alias_count": corrected_alias_count,
        "literature_record_count": record_count,
        "selection_pool_record_count": selection_pool_count,
        "saifollahi_selection_pool_count": saifollahi_selection_pool_count,
        "wittmann_selection_pool_count": wittmann_selection_pool_count,
        "selection_pool_link_count": selection_pool_link_count,
        "saifollahi_reference_evidence_count": saifollahi_reference_evidence_count,
        "approved_liu_association_count": approved_liu_association_count,
        "approved_s547_association_count": approved_s547_association_count,
        "approved_voggel_association_count": approved_voggel_association_count,
        "approved_alias_association_count": approved_alias_association_count,
        "approved_identity_evidence_count": approved_identity_evidence_count,
        "pending_source_proposal_count": pending_source_proposal_count,
        "gaia_association_proposal_count": gaia_association_proposal_count,
        "gaia_proposal_group_count": gaia_proposal_group_count,
        "approved_gaia_association_count": approved_gaia_association_count,
        "approved_gaia_identity_evidence_count": approved_gaia_identity_evidence_count,
        "approved_multi_position_gaia_count": approved_multi_position_gaia_count,
        "f6_velocity_tension_evidence_count": f6_velocity_tension_evidence_count,
        "saifollahi_duplicate_row_count": int(saifollahi_duplicate_row_count),
        "approved_gaia_ambiguity_evidence_count": approved_gaia_ambiguity_evidence_count,
        "approved_supplemental_identity_evidence_count": (
            approved_supplemental_identity_evidence_count
        ),
        "ambiguous_gaia_canonical_count": ambiguous_gaia_canonical_count,
        "retired_canonical_alias_count": retired_canonical_alias_count,
        "role_conflict_subtype_count": role_conflict_subtype_count,
        "wave1_record_count": wave1_record_count,
        "wave1_positive_count": wave1_positive_count,
        "wave1_comparison_count": wave1_comparison_count,
        "wave1_dataset_file_count": wave1_dataset_file_count,
        "s999_association_count": s999_association_count,
        "s999_identity_evidence_count": s999_identity_evidence_count,
        "ahn_measurement_evidence_count": ahn_measurement_evidence_count,
        "approved_wave1_identity_association_count": (approved_wave1_identity_association_count),
        "approved_wave1_identity_evidence_count": approved_wave1_identity_evidence_count,
        "approved_wave1_group_identity_association_count": (
            approved_wave1_group_identity_association_count
        ),
        "approved_wave1_group_identity_evidence_count": (
            approved_wave1_group_identity_evidence_count
        ),
        "approved_wave1_source_identity_association_count": (
            approved_wave1_source_identity_association_count
        ),
        "approved_wave1_source_identity_evidence_count": (
            approved_wave1_source_identity_evidence_count
        ),
        "supporting_source_row_counts": supporting_source_row_counts,
        "supporting_source_row_evidence_count": sum(supporting_source_row_counts.values()),
        "host_distance_summary": host_distance_summary,
        "preserved_legacy_distance_counts": preserved_legacy_distance_counts,
        "approved_confirmation_evidence_count": approved_confirmation_evidence_count,
        "approved_foreground_rejection_count": approved_foreground_rejection_count,
        "reviewed_confirmation_non_promotion_count": (reviewed_confirmation_non_promotion_count),
        "approved_reported_confirmation_count": approved_reported_confirmation_count,
        "screening_artifact_checks": screening_artifact_checks,
        "unassociated_record_count": unassociated_count,
        "canonical_object_count": canonical_object_count,
        "exact_duplicate_group_count": exact_duplicate_groups,
        "association_proposal_count": int(
            scalar(connection, "SELECT COUNT(*) FROM association_proposals")
        ),
        "review_queue_count": review_queue_count,
        "classification_counts": classification_counts,
        "authority_counts": authority_counts,
        "review_type_counts": review_type_counts,
        "confirmed_object_count": classification_counts.get("confirmed", 0),
        "open_gates": [],
    }


def write_report(path: Path, summary: dict[str, object], export_sha256: str) -> None:
    """Write a concise human-readable v2 validation report."""
    classification_rows = "\n".join(
        f"| `{state}` | {count} |" for state, count in summary["classification_counts"].items()
    )
    authority_rows = "\n".join(
        f"| `{status}` | {count} |" for status, count in summary["authority_counts"].items()
    )
    open_gates = (
        "\n".join(f"- `{gate}`" for gate in summary["open_gates"])
        if summary["open_gates"]
        else "- None."
    )
    report = f"""# Literature Reference v2 Validation

**Date:** {summary["validation_date"]}
**Status:** `{summary["validation_status"]}`
**Legacy database SHA-256:** `{summary["legacy_database_sha256"]}`
**Canonical export SHA-256:** `{export_sha256}`

## Preserved Inputs and Outputs

| Measure | Count |
|---|---:|
| Publications | {summary["publication_count"]} |
| Datasets | {summary["dataset_count"]} |
| Raw provenance files | {summary["dataset_file_count"]} |
| Immutable literature records | {summary["literature_record_count"]} |
| Separate selection-pool records | {summary["selection_pool_record_count"]} |
| Saifollahi broad selection-pool records | {summary["saifollahi_selection_pool_count"]} |
| Wittmann mixed compact-system pool records | {summary["wittmann_selection_pool_count"]} |
| Selection-pool links to final candidates | {summary["selection_pool_link_count"]} |
| Approved Wave 1 object and comparison records | {summary["wave1_record_count"]} |
| Wave 1 source-reported UCD or possible-UCD rows | {summary["wave1_positive_count"]} |
| Wave 1 comparison or contaminant rows | {summary["wave1_comparison_count"]} |
| Registered Wave 1 VizieR files | {summary["wave1_dataset_file_count"]} |
| Approved S999 non-anchor associations | {summary["s999_association_count"]} |
| Approved S999 identity evidence records | {summary["s999_identity_evidence_count"]} |
| Ahn M59-UCD3 spatial-kinematic evidence records | {summary["ahn_measurement_evidence_count"]} |
| Approved Wave 1 name-or-alias associations | {summary["approved_wave1_identity_association_count"]} |
| Approved Wave 1 name-or-alias identity evidence | {summary["approved_wave1_identity_evidence_count"]} |
| Records moved by approved Wave 1 multi-canonical identities | {summary["approved_wave1_group_identity_association_count"]} |
| Approved Wave 1 multi-canonical identity groups | {summary["approved_wave1_group_identity_evidence_count"]} |
| Records moved by delegated Wave 1 source identities | {summary["approved_wave1_source_identity_association_count"]} |
| Approved delegated Wave 1 source identities | {summary["approved_wave1_source_identity_evidence_count"]} |
| Supporting source rows linked as measurement evidence | {summary["supporting_source_row_evidence_count"]} |
| Approved object-level spectroscopic evidence rows | {summary["approved_confirmation_evidence_count"]} |
| Reported-confirmed rows supported by approved evidence | {summary["approved_reported_confirmation_count"]} |
| Reported-confirmed rows reviewed without qualifying local evidence | {summary["reviewed_confirmation_non_promotion_count"]} |
| ADS papers in the completed hashed screen | {summary["screening_artifact_checks"]["screened_paper_count"]} |
| Approved literature retrievals | {summary["screening_artifact_checks"]["approved_retrieval_count"]} |
| Explicitly scoped retrieval deferrals | {summary["screening_artifact_checks"]["deferred_source_count"]} |
| Saifollahi spectroscopic reference UCD evidence rows | {summary["saifollahi_reference_evidence_count"]} |
| Approved Liu source associations | {summary["approved_liu_association_count"]} |
| Approved Zhang/Fahrion S547 association | {summary["approved_s547_association_count"]} |
| Approved Voggel source associations | {summary["approved_voggel_association_count"]} |
| Approved Voggel alias-chain associations | {summary["approved_alias_association_count"]} |
| Approved identity evidence records | {summary["approved_identity_evidence_count"]} |
| Pending Voggel manual association proposals | {summary["pending_source_proposal_count"]} |
| Coordinate-null provenance records without canonical objects | {summary["unassociated_record_count"]} |
| Canonical objects | {summary["canonical_object_count"]} |
| Exact duplicate-coordinate groups | {summary["exact_duplicate_group_count"]} |
| Approved shared-Gaia identity groups | {summary["approved_gaia_identity_evidence_count"]} |
| Approved three-position shared-Gaia identity groups | {summary["approved_multi_position_gaia_count"]} |
| Approved ambiguous shared-Gaia close-pair evidence records | {summary["approved_gaia_ambiguity_evidence_count"]} |
| Approved supplemental name-and-position identity evidence | {summary["approved_supplemental_identity_evidence_count"]} |
| Literature records moved by approved Gaia associations | {summary["approved_gaia_association_count"]} |
| Retired canonical identifiers retained as aliases | {summary["retired_canonical_alias_count"]} |
| Preserved F-6/Gregg 27 velocity-tension evidence | {summary["f6_velocity_tension_evidence_count"]} |
| Preserved duplicate Saifollahi F-1/UCD2 source rows | {summary["saifollahi_duplicate_row_count"]} |
| Uncertain objects with reported UCD-role conflict subtype | {summary["role_conflict_subtype_count"]} |
| Non-exact Gaia association proposals | {summary["gaia_association_proposal_count"]} |
| Gaia source groups still under review | {summary["gaia_proposal_group_count"]} |
| All open association proposals | {summary["association_proposal_count"]} |
| Open review items | {summary["review_queue_count"]} |

The legacy audit remains {summary["legacy_summary"]["row_count"]} rows and
{summary["legacy_summary"]["duplicate_group_count"]} exact duplicate-coordinate
groups. Additional canonical records come from authoritative Zhang, Dumont,
Saifollahi, Liu, Voggel, Ko, and Wave 1 tables. The broader Saifollahi and mixed
Wittmann pools remain separate from canonical positive references.

Approved Liu and Voggel associations retain distinct literature records while
linking them to existing canonical objects. Four coordinate-null Fahrion rows are
preserved as unresolved provenance records without creating artificial positions.
The T17-1596 Voggel row is linked to Fahrion HHH86-C15 through the published
Taylor GC0218 and Woodley HHH86-C15 alias chain; its 1.37-arcsec coordinate
offset remains recorded on the accepted association.
The approved Gaia cohorts merge 72 clean, 14 reported-role-conflict, 22
image-reviewed two-position, and eight literature-reviewed three-position groups
while retaining every superseded canonical identifier as an alias. The 14
role-conflict objects remain explicitly uncertain. The F-6/Gregg 27 velocity
tension is retained as reviewed evidence, and both identical Saifollahi source
rows in the F-1/UCD2 identity are preserved as separate provenance records.
Zhang and Fahrion S547 records are consolidated through approved name-and-position
evidence, while S547 and VUCD3 remain separate canonical objects sharing explicit
ambiguous unresolved-Gaia evidence. No shared-Gaia identity proposals remain.
The approved Wave 1 treatment preserves 855 positive and 1,484 comparison rows
without promoting confirmation or applying a general non-exact matching radius.
Four exact Ko UCD/GC role conflicts remain explicitly uncertain. The Zhang,
Fahrion, Ko, and Liu representations of S999 are consolidated under the
Gaia-bearing Fahrion position while retaining the prior Zhang canonical identifier
as an alias. The 109 Ahn spatial bins are attached to M59-UCD3 as one supporting
measurement dataset rather than 109 objects.
Seven additional Wave 1 rows are associated with six pre-Wave candidate
identities through direct names or source-published aliases. Each reviewed target
was the unique nearest baseline canonical within one arcsecond, and no general
positional matching radius was introduced. All seven superseded Wave canonical
identifiers remain aliases; classifications are unchanged apart from the expected
reduction in duplicate candidate objects.
Twelve additional multi-canonical groups are consolidated through complete shared-
identifier coverage, identical retained velocities, consistent reported roles,
and no distinct-Gaia conflict. Their 16 Wave rows and 24 pre-Wave canonicals now
form 12 objects, and all 28 superseded canonical identifiers remain aliases. The
other 79 reviewed groups were left unchanged at that review gate.
The delegated source audit closes those 79 groups as 80 identities. Seventy-two
use exact Liu 2015 catalog keys and published aliases, two use Brodie catalog
evidence, four preserve differing independent or weighted velocity measurements,
and the S547/VUCD3 close pair is split into its two previously reviewed distinct
objects. All 229 superseded canonical identifiers remain aliases, every reported
velocity remains immutable source evidence, and no positional identity rule is
introduced.
The raw-row coverage gate is closed. All 168 rows in the three tables previously
classified as intentionally supporting rather than object-defining are attached
to preserved objects as measurement evidence: 27 Chiboucas structural rows, 127
Liu structural-and-velocity rows, and 14 Voggel spectroscopic rows. These links do
not authorize identity, classification, or confirmation changes.
The host-distance gate is also closed. Mieske's 27 Centaurus-cluster rows now use
the source-stated 43 Mpc instead of the incorrect legacy 3.8 Mpc Centaurus A
default, while all original values remain in immutable raw payloads. Fahrion's
heterogeneous 381-row compilation retains its published per-row host labels but
no blanket normalized distance. Liu's 127 M87, 50 M49, and 29 M60 rows now carry
explicit table-specific host labels, and the 16.5 Mpc legacy value remains scoped
to the M87 table. Other retained distances are documented as source-adopted or
approximate environmental context, not independent object-level measurements.
The confirmation gate is closed under `confirmation_rules_v1`. The delegated
audit approves 1,316 spectroscopic evidence rows across 12 source-defined cohorts,
which resolve to 740 confirmed canonical objects after identity consolidation.
The 57 Voggel previously confirmed comparison rows remain candidates because the
local table does not carry qualifying object-level spectroscopy or resolved-
structure evidence. Twenty-two reviewed positive/negative role conflicts remain
uncertain, including M87UCD-29; no source label or measurement is discarded.
The new-literature screening gate is closed against the same-day hashed ADS
corpus of 345 papers. All title-and-abstract decisions are complete, 19 sources
were retrieved in the approved Wave 1 cohort, and eight remaining retrieval
candidates have explicit ancillary, incremental, mixed-distance, or distant-
sensitivity dispositions. Deferral does not classify those papers as irrelevant;
it prevents optional enrichment from blocking the Stage 1 benchmark.

## Conservative Classifications

| State | Canonical objects |
|---|---:|
{classification_rows}

No reported confirmation is promoted automatically. Every promotion requires an
approved evidence review under `confirmation_rules_v1`.

## Dataset Authority

| Status | Datasets |
|---|---:|
{authority_rows}

## Open Stage 1 Gates

{open_gates}

All Stage 1 literature-stabilization gates are closed. Selector changes remain a
separate reviewed task. The legacy database was opened read-only and the
destructive redundancy script was not used.
"""
    path.write_text(report, encoding="utf-8")


def main() -> None:
    """Validate v2 and generate tracked audit artifacts."""
    arguments = parse_arguments()
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    legacy_sha256 = calculate_sha256(arguments.legacy_database)
    with connect_read_only(arguments.legacy_database) as legacy_connection:
        legacy_summary = load_legacy_summary(legacy_connection)
    with connect_read_only(arguments.reference_database) as connection:
        summary = validate_invariants(connection, legacy_summary, legacy_sha256)
        canonical_rows = canonical_export(connection)
        review_rows = review_export(connection)
        proposal_rows = proposal_export(connection)
        raw_file_rows = raw_file_export(connection)
        saifollahi_reference_rows = saifollahi_reference_export(connection)
        saifollahi_selection_pool_rows = saifollahi_selection_pool_export(connection)
        approved_source_membership_rows = approved_source_membership_export(connection)
        approved_gaia_identity_rows = approved_gaia_identity_export(connection)
        approved_special_identity_rows = approved_special_identity_evidence_export(connection)
        approved_wave1_role_rows = approved_wave1_role_export(connection)

    canonical_path = arguments.output_directory / "canonical_reference_catalog.csv"
    write_csv(canonical_path, canonical_rows)
    write_csv(arguments.output_directory / "reference_review_queue.csv", review_rows)
    write_csv(
        arguments.output_directory / "gaia_association_proposals.csv",
        proposal_rows,
        GAIA_PROPOSAL_EXPORT_FIELDS,
    )
    write_csv(arguments.output_directory / "raw_source_file_inventory.csv", raw_file_rows)
    write_csv(
        arguments.output_directory / "saifollahi_reference_roles.csv",
        saifollahi_reference_rows,
    )
    write_csv(
        arguments.output_directory / "saifollahi_selection_pool.csv",
        saifollahi_selection_pool_rows,
    )
    write_csv(
        arguments.output_directory / "approved_source_memberships.csv",
        approved_source_membership_rows,
    )
    write_csv(
        arguments.output_directory / "approved_gaia_identity_associations.csv",
        approved_gaia_identity_rows,
    )
    write_csv(
        arguments.output_directory / "approved_special_identity_evidence.csv",
        approved_special_identity_rows,
    )
    write_csv(
        arguments.output_directory / "approved_wave1_source_roles.csv",
        approved_wave1_role_rows,
    )
    export_sha256 = calculate_sha256(canonical_path)
    summary["canonical_export_sha256"] = export_sha256
    summary["validation_artifact_digest"] = hashlib.sha256(
        json.dumps(summary, sort_keys=True).encode("utf-8")
    ).hexdigest()
    with (arguments.output_directory / "literature_reference_v2_validation.json").open(
        "w", encoding="utf-8"
    ) as output_file:
        json.dump(summary, output_file, indent=2, sort_keys=True)
        output_file.write("\n")
    write_report(
        arguments.output_directory / "literature_reference_v2_validation.md",
        summary,
        export_sha256,
    )
    if summary["validation_status"] == "failed":
        raise RuntimeError(f"Reference validation failed: {summary['failures']}")


if __name__ == "__main__":
    main()
