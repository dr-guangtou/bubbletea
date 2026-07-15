"""Audit proposed literature associations against authoritative Gaia DR3 positions.

The script reads the non-destructive v2 database, retrieves or reuses a cached
Gaia DR3 source table, and writes group-level and pair-level geometry artifacts.
It never changes canonical membership or proposal status.
"""

import argparse
import csv
import hashlib
import json
import logging
import sqlite3
from collections import defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import astropy.units as u
from astropy.coordinates import SkyCoord

from scripts.config import (
    LITERATURE_REFERENCE_DB_V2,
    LITERATURE_SOURCES,
    LITERATURE_VALIDATION,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256, connect_read_only

logger = logging.getLogger(__name__)

GAIA_TAP_ENDPOINT = "https://datalab.noirlab.edu/tap/sync"
GAIA_CACHE = LITERATURE_SOURCES / "gaia_dr3_association_sources.csv"
GAIA_RETRIEVAL_MANIFEST = LITERATURE_SOURCES / "gaia_dr3_association_sources.json"
GROUP_OUTPUT = "gaia_association_group_review.csv"
PAIR_OUTPUT = "gaia_association_pair_geometry.csv"
REPORT_OUTPUT = "gaia_association_geometry_audit.md"


def parse_arguments() -> argparse.Namespace:
    """Parse database, cache, and output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--gaia-cache", type=Path, default=GAIA_CACHE)
    parser.add_argument("--retrieval-manifest", type=Path, default=GAIA_RETRIEVAL_MANIFEST)
    parser.add_argument("--output-directory", type=Path, default=LITERATURE_VALIDATION)
    parser.add_argument(
        "--refresh-gaia",
        action="store_true",
        help="Retrieve the proposal source IDs from the Gaia DR3 TAP table.",
    )
    return parser.parse_args()


def query_rows(connection: sqlite3.Connection, query: str) -> list[dict[str, object]]:
    """Return SQLite query results as dictionaries."""
    return [dict(row) for row in connection.execute(query).fetchall()]


def load_proposals(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Load every pending Gaia proposal with literature context."""
    return query_rows(
        connection,
        """
        SELECT
            p.proposal_id,
            p.gaia_dr3_id,
            p.separation_arcsec,
            p.record_id_1,
            a1.canonical_object_id AS canonical_object_id_1,
            pub1.bibcode AS bibcode_1,
            r1.original_name AS original_name_1,
            r1.ra AS ra_1,
            r1.dec AS dec_1,
            r1.host_galaxy AS host_galaxy_1,
            r1.reported_is_ucd AS reported_is_ucd_1,
            r1.reported_confirmation_status AS reported_status_1,
            COALESCE(
                json_extract(r1.raw_payload_json, '$.gaia_xmatch_dist'),
                json_extract(r1.raw_payload_json, '$.legacy_record.gaia_xmatch_dist')
            ) AS legacy_gaia_distance_1,
            p.record_id_2,
            a2.canonical_object_id AS canonical_object_id_2,
            pub2.bibcode AS bibcode_2,
            r2.original_name AS original_name_2,
            r2.ra AS ra_2,
            r2.dec AS dec_2,
            r2.host_galaxy AS host_galaxy_2,
            r2.reported_is_ucd AS reported_is_ucd_2,
            r2.reported_confirmation_status AS reported_status_2,
            COALESCE(
                json_extract(r2.raw_payload_json, '$.gaia_xmatch_dist'),
                json_extract(r2.raw_payload_json, '$.legacy_record.gaia_xmatch_dist')
            ) AS legacy_gaia_distance_2
        FROM association_proposals p
        JOIN literature_records r1 ON r1.record_id = p.record_id_1
        JOIN datasets d1 ON d1.dataset_id = r1.dataset_id
        JOIN publications pub1 ON pub1.publication_id = d1.publication_id
        JOIN object_record_associations a1 ON a1.record_id = r1.record_id
        JOIN literature_records r2 ON r2.record_id = p.record_id_2
        JOIN datasets d2 ON d2.dataset_id = r2.dataset_id
        JOIN publications pub2 ON pub2.publication_id = d2.publication_id
        JOIN object_record_associations a2 ON a2.record_id = r2.record_id
        WHERE p.proposal_method = 'legacy_gaia_id'
        ORDER BY p.gaia_dr3_id, p.record_id_1, p.record_id_2
        """,
    )


def build_gaia_query(source_ids: list[str]) -> str:
    """Build the deterministic Gaia DR3 query for proposal source IDs."""
    identifier_list = ",".join(sorted(source_ids, key=int))
    return f"""SELECT
    source_id, ra, dec, ra_error, dec_error, phot_g_mean_mag,
    duplicated_source, ipd_frac_multi_peak, ipd_frac_odd_win, ruwe
FROM gaia_dr3.gaia_source
WHERE source_id IN ({identifier_list})
ORDER BY source_id"""


def retrieve_gaia_sources(source_ids: list[str], cache_path: Path, manifest_path: Path) -> None:
    """Retrieve Gaia DR3 rows and record the exact query and file digest."""
    query = build_gaia_query(source_ids)
    request_body = urlencode(
        {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}
    ).encode("utf-8")
    request = Request(GAIA_TAP_ENDPOINT, data=request_body, method="POST")
    with urlopen(request, timeout=120) as response:  # noqa: S310
        response_bytes = response.read()

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(response_bytes)
    rows = load_gaia_sources(cache_path)
    returned_ids = set(rows)
    expected_ids = set(source_ids)
    if returned_ids != expected_ids:
        missing_ids = sorted(expected_ids - returned_ids, key=int)
        unexpected_ids = sorted(returned_ids - expected_ids, key=int)
        raise RuntimeError(
            f"Gaia retrieval mismatch: missing={missing_ids}, unexpected={unexpected_ids}"
        )

    manifest = {
        "schema_version": 1,
        "retrieval_date": date.today().isoformat(),
        "service": "NOIRLab Astro Data Lab TAP",
        "endpoint": GAIA_TAP_ENDPOINT,
        "table": "gaia_dr3.gaia_source",
        "query": query,
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "row_count": len(rows),
        "csv_path": cache_path.relative_to(Path.cwd()).as_posix(),
        "csv_sha256": calculate_sha256(cache_path),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    logger.info("Retrieved %d Gaia DR3 sources to %s", len(rows), cache_path)


def load_gaia_sources(path: Path) -> dict[str, dict[str, str]]:
    """Load cached Gaia rows keyed by exact source ID strings."""
    with path.open(encoding="utf-8", newline="") as input_file:
        rows = list(csv.DictReader(input_file))
    return {row["source_id"]: row for row in rows}


def angular_separation_arcsec(ra_1: float, dec_1: float, ra_2: float, dec_2: float) -> float:
    """Measure a spherical angular separation in arcseconds."""
    first = SkyCoord(ra_1 * u.deg, dec_1 * u.deg)
    second = SkyCoord(ra_2 * u.deg, dec_2 * u.deg)
    return float(first.separation(second).arcsec)


def add_gaia_geometry(
    proposals: list[dict[str, object]], gaia_sources: dict[str, dict[str, str]]
) -> list[dict[str, object]]:
    """Add authoritative Gaia-to-literature separations to proposal pairs."""
    audited_rows = []
    for proposal in proposals:
        source_id = str(proposal["gaia_dr3_id"])
        gaia_source = gaia_sources[source_id]
        gaia_ra = float(gaia_source["ra"])
        gaia_dec = float(gaia_source["dec"])
        gaia_distance_1 = angular_separation_arcsec(
            float(proposal["ra_1"]),
            float(proposal["dec_1"]),
            gaia_ra,
            gaia_dec,
        )
        gaia_distance_2 = angular_separation_arcsec(
            float(proposal["ra_2"]),
            float(proposal["dec_2"]),
            gaia_ra,
            gaia_dec,
        )
        audited_rows.append(
            {
                **proposal,
                "gaia_ra": gaia_ra,
                "gaia_dec": gaia_dec,
                "gaia_ra_error_mas": gaia_source["ra_error"],
                "gaia_dec_error_mas": gaia_source["dec_error"],
                "gaia_g_mag": gaia_source["phot_g_mean_mag"],
                "gaia_duplicated_source": gaia_source["duplicated_source"],
                "gaia_ipd_frac_multi_peak": gaia_source["ipd_frac_multi_peak"],
                "gaia_ipd_frac_odd_win": gaia_source["ipd_frac_odd_win"],
                "gaia_ruwe": gaia_source["ruwe"],
                "gaia_distance_1_arcsec": gaia_distance_1,
                "legacy_minus_spherical_distance_1_arcsec": (
                    float(proposal["legacy_gaia_distance_1"]) - gaia_distance_1
                ),
                "gaia_distance_2_arcsec": gaia_distance_2,
                "legacy_minus_spherical_distance_2_arcsec": (
                    float(proposal["legacy_gaia_distance_2"]) - gaia_distance_2
                ),
                "reported_is_ucd_conflict": int(
                    proposal["reported_is_ucd_1"] != proposal["reported_is_ucd_2"]
                ),
                "canonical_identity_decision": "pending_project_review",
            }
        )
    return audited_rows


def build_group_review(pair_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Summarize each shared Gaia source across distinct canonical positions."""
    pairs_by_source = defaultdict(list)
    for row in pair_rows:
        pairs_by_source[str(row["gaia_dr3_id"])].append(row)

    group_rows = []
    for source_id, rows in sorted(pairs_by_source.items(), key=lambda item: int(item[0])):
        records = {}
        canonical_positions = {}
        for row in rows:
            for suffix in ("1", "2"):
                record_id = str(row[f"record_id_{suffix}"])
                canonical_object_id = str(row[f"canonical_object_id_{suffix}"])
                records[record_id] = {
                    "bibcode": row[f"bibcode_{suffix}"],
                    "reported_is_ucd": row[f"reported_is_ucd_{suffix}"],
                }
                canonical_positions[canonical_object_id] = (
                    float(row[f"ra_{suffix}"]),
                    float(row[f"dec_{suffix}"]),
                )

        position_pairs = list(combinations(canonical_positions.values(), 2))
        position_separations = [
            angular_separation_arcsec(*first, *second) for first, second in position_pairs
        ]
        gaia_distances = []
        gaia_ra = float(rows[0]["gaia_ra"])
        gaia_dec = float(rows[0]["gaia_dec"])
        for ra, dec in canonical_positions.values():
            gaia_distances.append(angular_separation_arcsec(ra, dec, gaia_ra, gaia_dec))

        bibcodes = sorted({str(record["bibcode"]) for record in records.values()})
        labels = {record["reported_is_ucd"] for record in records.values()}
        canonical_count = len(canonical_positions)
        source_context = (
            "liu_m87_and_fahrion_compilation"
            if bibcodes == ["2015ApJ...812...34L", "2019A&A...625A..50F"]
            else "fornax_spectroscopic_compilations"
        )
        has_gaia_image_flag = (
            rows[0]["gaia_duplicated_source"] == "1" or int(rows[0]["gaia_ipd_frac_multi_peak"]) > 0
        )
        has_label_conflict = len(labels) > 1
        if canonical_count > 2:
            recommended_action = "manual_multi_position_identity_review"
        elif has_label_conflict:
            recommended_action = "identity_and_classification_review"
        elif has_gaia_image_flag:
            recommended_action = "manual_gaia_image_ambiguity_review"
        else:
            recommended_action = "recommend_accept_shared_identity"
        group_rows.append(
            {
                "gaia_dr3_id": source_id,
                "record_count": len(records),
                "canonical_position_count": canonical_count,
                "proposal_pair_count": len(rows),
                "bibcodes": ";".join(bibcodes),
                "source_context": source_context,
                "reported_is_ucd_conflict": int(has_label_conflict),
                "minimum_position_separation_arcsec": min(position_separations),
                "maximum_position_separation_arcsec": max(position_separations),
                "minimum_gaia_distance_arcsec": min(gaia_distances),
                "maximum_gaia_distance_arcsec": max(gaia_distances),
                "gaia_duplicated_source": rows[0]["gaia_duplicated_source"],
                "gaia_ipd_frac_multi_peak": rows[0]["gaia_ipd_frac_multi_peak"],
                "gaia_ipd_frac_odd_win": rows[0]["gaia_ipd_frac_odd_win"],
                "geometry_class": (
                    "shared_gaia_two_position"
                    if canonical_count == 2
                    else "shared_gaia_three_position_ambiguous"
                ),
                "recommended_action": recommended_action,
            }
        )
    return group_rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write deterministic CSV rows with explicit headers."""
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    path: Path,
    group_rows: list[dict[str, object]],
    pair_rows: list[dict[str, object]],
) -> None:
    """Write measured Gaia geometry and unresolved decision classes."""
    two_position_rows = [row for row in group_rows if row["canonical_position_count"] == 2]
    three_position_rows = [row for row in group_rows if row["canonical_position_count"] == 3]
    label_conflict_rows = [row for row in group_rows if row["reported_is_ucd_conflict"]]
    duplicated_source_rows = [row for row in group_rows if row["gaia_duplicated_source"] == "1"]
    multi_peak_rows = [row for row in group_rows if int(row["gaia_ipd_frac_multi_peak"]) > 0]
    action_counts = defaultdict(int)
    for row in group_rows:
        action_counts[str(row["recommended_action"])] += 1
    spherical_distance_differences = [
        abs(float(row[f"legacy_minus_spherical_distance_{suffix}_arcsec"]))
        for row in pair_rows
        for suffix in ("1", "2")
    ]
    maximum_gaia_distance = max(
        float(row[f"gaia_distance_{suffix}_arcsec"]) for row in pair_rows for suffix in ("1", "2")
    )
    action_lines = "\n".join(
        f"| `{action}` | {count} |" for action, count in sorted(action_counts.items())
    )
    report = f"""# Gaia Association Geometry Audit

**Date:** {date.today().isoformat()}
**Decision status:** `86_two_position_groups_approved_31_groups_pending`
**Gaia table:** `gaia_dr3.gaia_source`

## Measured Scope

| Measure | Count |
|---|---:|
| Gaia DR3 source IDs | {len(group_rows)} |
| Two-position Gaia groups | {len(two_position_rows)} |
| Three-position ambiguous Gaia groups | {len(three_position_rows)} |
| Groups with reported `is_ucd` conflicts | {len(label_conflict_rows)} |
| Gaia rows flagged `duplicated_source` | {len(duplicated_source_rows)} |
| Gaia rows with nonzero `ipd_frac_multi_peak` | {len(multi_peak_rows)} |
| Maximum literature-to-Gaia separation (arcsec) | {maximum_gaia_distance:.12f} |
| Maximum legacy planar-vs-spherical distance difference (arcsec) | {max(spherical_distance_differences):.12f} |

All Gaia source IDs were resolved against authoritative DR3 coordinates. The
pair and group exports record spherical Gaia-to-literature distances, legacy
cross-match distances, source combinations, label conflicts, and Gaia image-
parameter diagnostics.

## Review Routing

| Recommended action | Gaia groups |
|---|---:|
{action_lines}

The 64 M87 groups compare Liu primary-table coordinates with the later Fahrion
compilation. The other 53 groups are in Fornax. Saifollahi table A1 explicitly
describes its KNOWN UCD/GC sample as a compilation of earlier spectroscopic
catalogs, including Gregg et al. through the Maddox compilation. That source
history supports cross-catalog identity, but reported GC/UCD role conflicts remain
classification questions rather than evidence that may be silently discarded.

## Interpretation Boundary

A shared Gaia detection is strong cross-catalog evidence, but it does not by
itself prove that two close literature positions are the same astrophysical
object. This is especially important for the three-position groups and for
groups with conflicting reported UCD roles. This audit itself is read-only. The
builder separately implements the approved 72 clean groups and 14 role-conflict
groups, retaining the other 31 groups for image or multi-position review.

Review `{GROUP_OUTPUT}` first, then use
`{PAIR_OUTPUT}` for row-level evidence.
The cached Gaia rows and exact TAP query are recorded in
`data/literature/sources/gaia_dr3_association_sources.csv` and its JSON manifest.
"""
    path.write_text(report, encoding="utf-8")


def main() -> None:
    """Retrieve Gaia context when requested and write non-destructive audits."""
    arguments = parse_arguments()
    with connect_read_only(arguments.reference_database) as connection:
        proposals = load_proposals(connection)
    if len(proposals) != 140:
        raise RuntimeError(f"Expected 140 Gaia proposals, found {len(proposals)}")
    source_ids = sorted({str(row["gaia_dr3_id"]) for row in proposals}, key=int)

    if arguments.refresh_gaia:
        retrieve_gaia_sources(source_ids, arguments.gaia_cache, arguments.retrieval_manifest)
    if not arguments.gaia_cache.exists():
        raise FileNotFoundError("Gaia cache is absent; rerun with --refresh-gaia")
    gaia_sources = load_gaia_sources(arguments.gaia_cache)
    if set(gaia_sources) != set(source_ids):
        raise RuntimeError("Cached Gaia source IDs do not match current proposals")

    pair_rows = add_gaia_geometry(proposals, gaia_sources)
    group_rows = build_group_review(pair_rows)
    if len(group_rows) != 117:
        raise RuntimeError(f"Expected 117 Gaia groups, found {len(group_rows)}")

    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    write_csv(arguments.output_directory / PAIR_OUTPUT, pair_rows)
    write_csv(arguments.output_directory / GROUP_OUTPUT, group_rows)
    write_report(arguments.output_directory / REPORT_OUTPUT, group_rows, pair_rows)
    logger.info("Audited %d proposals across %d Gaia source IDs", len(pair_rows), len(group_rows))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
