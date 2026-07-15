"""Audit Wave 1 identifier matches that intersect multiple baseline canonicals.

The audit builds connected groups from Wave 1 rows with direct-name or published-
alias evidence and every pre-Wave canonical within one arcsecond. It records names,
velocities, Gaia identifiers, reported roles, and unreferenced positional contenders.
It never changes database membership, identity, or classification.
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import LITERATURE_REFERENCE_DB_V2, LITERATURE_SOURCES, LITERATURE_VALIDATION
from scripts.phase1_literature.audit_reference_data import calculate_sha256, connect_read_only
from scripts.phase1_literature.audit_wave1_identity_candidates import (
    WAVE1_BIBCODES,
    collect_velocity_measurements,
    load_records,
    normalize_identifier,
    record_identifiers,
)

DEFAULT_GROUP_CSV = LITERATURE_VALIDATION / "literature_wave1_multi_canonical_groups.csv"
DEFAULT_MEMBER_CSV = LITERATURE_VALIDATION / "literature_wave1_multi_canonical_members.csv"
DEFAULT_PROPOSALS = LITERATURE_SOURCES / "literature_wave1_group_identity_proposals.json"
DEFAULT_REPORT = LITERATURE_VALIDATION / "literature_wave1_multi_canonical_groups.md"
GROUP_FIELDS = (
    "group_id",
    "recommendation",
    "routing_reason",
    "wave_record_count",
    "baseline_canonical_count",
    "matched_baseline_canonical_count",
    "unreferenced_baseline_canonical_count",
    "current_canonical_count",
    "recommended_anchor_canonical_object_id",
    "wave_record_ids",
    "baseline_canonical_object_ids",
    "unreferenced_baseline_canonical_object_ids",
    "matching_identifiers_json",
    "matching_identifiers",
    "distinct_gaia_dr3_ids",
    "reported_is_ucd_values",
    "velocity_measurement_count",
    "velocity_minimum_km_s",
    "velocity_maximum_km_s",
    "velocity_spread_km_s",
    "maximum_group_separation_arcsec",
)
MEMBER_FIELDS = (
    "group_id",
    "member_type",
    "member_id",
    "current_canonical_object_id",
    "bibcodes",
    "names",
    "ra",
    "dec",
    "gaia_dr3_ids",
    "reported_is_ucd_values",
    "classification_states",
    "identifier_linked",
    "minimum_wave_separation_arcsec",
    "velocities_json",
    "nearby_baseline_separations_json",
)


def parse_arguments() -> argparse.Namespace:
    """Parse audit paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--group-csv", type=Path, default=DEFAULT_GROUP_CSV)
    parser.add_argument("--member-csv", type=Path, default=DEFAULT_MEMBER_CSV)
    parser.add_argument("--proposals", type=Path, default=DEFAULT_PROPOSALS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def stable_group_id(node_ids: list[str]) -> str:
    """Return a deterministic identifier for one connected review group."""
    digest = hashlib.sha256("\n".join(sorted(node_ids)).encode()).hexdigest()[:16]
    return f"wave1_identity_group_{digest}"


def record_identifier_map(record: dict[str, object]) -> dict[str, list[dict[str, str]]]:
    """Index one record's original names and published aliases."""
    identifiers = defaultdict(list)
    for item in record_identifiers(record):
        identifiers[normalize_identifier(item["identifier"])].append(item)
    return dict(identifiers)


def build_groups(
    records: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict]:
    """Build connected multi-canonical review groups and proposal rows."""
    baseline_records = [record for record in records if record["bibcode"] not in WAVE1_BIBCODES]
    wave_records = [record for record in records if record["bibcode"] in WAVE1_BIBCODES]
    baseline_by_canonical = defaultdict(list)
    baseline_identifier_index = defaultdict(set)
    for record in baseline_records:
        canonical_object_id = str(record["canonical_object_id"])
        baseline_by_canonical[canonical_object_id].append(record)
        for identifier in record_identifier_map(record):
            baseline_identifier_index[identifier].add(canonical_object_id)

    baseline_canonical_ids = sorted(baseline_by_canonical)
    baseline_coordinates = SkyCoord(
        [float(baseline_by_canonical[item][0]["adopted_ra"]) for item in baseline_canonical_ids]
        * u.deg,
        [float(baseline_by_canonical[item][0]["adopted_dec"]) for item in baseline_canonical_ids]
        * u.deg,
    )
    baseline_id_by_index = dict(enumerate(baseline_canonical_ids))
    baseline_ids = set(baseline_canonical_ids)
    remaining_wave_records = [
        record for record in wave_records if str(record["canonical_object_id"]) not in baseline_ids
    ]

    wave_by_id = {str(record["record_id"]): record for record in remaining_wave_records}
    wave_identifier_matches = defaultdict(lambda: defaultdict(set))
    wave_nearby_baseline = {}
    adjacency = defaultdict(set)
    for wave_record in remaining_wave_records:
        wave_record_id = str(wave_record["record_id"])
        identifier_map = record_identifier_map(wave_record)
        for identifier in identifier_map:
            for canonical_object_id in baseline_identifier_index.get(identifier, set()):
                wave_identifier_matches[wave_record_id][canonical_object_id].add(identifier)
        if not wave_identifier_matches[wave_record_id]:
            continue
        coordinate = SkyCoord(float(wave_record["ra"]) * u.deg, float(wave_record["dec"]) * u.deg)
        separations = coordinate.separation(baseline_coordinates).arcsec
        nearby_ids = {
            baseline_id_by_index[int(index)]: float(separations[int(index)])
            for index in np.flatnonzero(separations <= 1.0)
        }
        matching_nearby_ids = set(wave_identifier_matches[wave_record_id]) & set(nearby_ids)
        if len(nearby_ids) <= 1 or not matching_nearby_ids:
            continue
        wave_nearby_baseline[wave_record_id] = nearby_ids
        wave_node = f"wave:{wave_record_id}"
        for canonical_object_id in nearby_ids:
            baseline_node = f"baseline:{canonical_object_id}"
            adjacency[wave_node].add(baseline_node)
            adjacency[baseline_node].add(wave_node)

    seen = set()
    components = []
    for start_node in sorted(adjacency):
        if start_node in seen:
            continue
        stack = [start_node]
        seen.add(start_node)
        component = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in sorted(adjacency[node]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component))

    group_rows = []
    member_rows = []
    proposals = []
    for component in components:
        group_id = stable_group_id(component)
        wave_record_ids = sorted(
            node.removeprefix("wave:") for node in component if node.startswith("wave:")
        )
        baseline_group_ids = sorted(
            node.removeprefix("baseline:") for node in component if node.startswith("baseline:")
        )
        group_wave_records = [wave_by_id[record_id] for record_id in wave_record_ids]
        group_baseline_records = [
            record
            for canonical_object_id in baseline_group_ids
            for record in baseline_by_canonical[canonical_object_id]
        ]
        matched_baseline_ids = {
            canonical_object_id
            for wave_record_id in wave_record_ids
            for canonical_object_id in wave_identifier_matches[wave_record_id]
            if canonical_object_id in baseline_group_ids
        }
        unreferenced_baseline_ids = sorted(set(baseline_group_ids) - matched_baseline_ids)
        gaia_ids = sorted(
            {
                str(record["payload"].get("gaia_dr3_id") or "").strip()
                for record in group_baseline_records + group_wave_records
                if str(record["payload"].get("gaia_dr3_id") or "").strip()
            }
        )
        reported_roles = sorted(
            {
                int(record["reported_is_ucd"])
                for record in group_baseline_records + group_wave_records
                if record["reported_is_ucd"] is not None
            }
        )
        velocity_measurements = [
            {
                **measurement,
                "record_id": record["record_id"],
                "bibcode": record["bibcode"],
                "name": record["original_name"],
            }
            for record in group_baseline_records + group_wave_records
            for measurement in collect_velocity_measurements(record["payload"])
        ]
        velocity_values = [float(item["velocity_km_s"]) for item in velocity_measurements]
        velocity_spread = max(velocity_values) - min(velocity_values) if velocity_values else None
        coordinate_nodes = [
            (str(record["record_id"]), float(record["ra"]), float(record["dec"]))
            for record in group_wave_records
        ] + [
            (
                canonical_object_id,
                float(baseline_by_canonical[canonical_object_id][0]["adopted_ra"]),
                float(baseline_by_canonical[canonical_object_id][0]["adopted_dec"]),
            )
            for canonical_object_id in baseline_group_ids
        ]
        group_coordinates = SkyCoord(
            [item[1] for item in coordinate_nodes] * u.deg,
            [item[2] for item in coordinate_nodes] * u.deg,
        )
        maximum_separation = 0.0
        for index in range(len(coordinate_nodes)):
            if index + 1 < len(coordinate_nodes):
                maximum_separation = max(
                    maximum_separation,
                    float(
                        np.max(
                            group_coordinates[index]
                            .separation(group_coordinates[index + 1 :])
                            .arcsec
                        )
                    ),
                )

        if len(gaia_ids) > 1:
            recommendation = "retain_separate_distinct_gaia_sources"
            routing_reason = "multiple_distinct_gaia_dr3_ids"
        elif unreferenced_baseline_ids:
            recommendation = "manual_group_review"
            routing_reason = "nearby_baseline_canonical_lacks_identifier_link"
        elif velocity_spread is not None and velocity_spread > 0:
            recommendation = "manual_group_review"
            routing_reason = "reported_velocities_are_not_identical"
        elif reported_roles == [0, 1]:
            recommendation = "recommend_merge_as_uncertain_role_conflict"
            routing_reason = "complete_identifier_coverage_with_conflicting_reported_roles"
        else:
            recommendation = "recommend_merge_group"
            routing_reason = "complete_identifier_coverage_without_gaia_or_role_conflict"

        anchor_candidates = sorted(
            baseline_group_ids,
            key=lambda canonical_object_id: (
                -sum(
                    bool(str(record["payload"].get("gaia_dr3_id") or "").strip())
                    for record in baseline_by_canonical[canonical_object_id]
                ),
                -len(baseline_by_canonical[canonical_object_id]),
                canonical_object_id,
            ),
        )
        recommended_anchor = anchor_candidates[0]
        identifiers_by_edge = {
            f"{wave_record_id}|{canonical_object_id}": sorted(identifiers)
            for wave_record_id in wave_record_ids
            for canonical_object_id, identifiers in wave_identifier_matches[wave_record_id].items()
            if canonical_object_id in baseline_group_ids
        }
        matching_identifiers = sorted(
            {
                identifier
                for identifiers in identifiers_by_edge.values()
                for identifier in identifiers
            }
        )
        group_row = {
            "group_id": group_id,
            "recommendation": recommendation,
            "routing_reason": routing_reason,
            "wave_record_count": len(wave_record_ids),
            "baseline_canonical_count": len(baseline_group_ids),
            "matched_baseline_canonical_count": len(matched_baseline_ids),
            "unreferenced_baseline_canonical_count": len(unreferenced_baseline_ids),
            "current_canonical_count": len(
                {
                    str(record["canonical_object_id"])
                    for record in group_wave_records
                    + [baseline_by_canonical[item][0] for item in baseline_group_ids]
                }
            ),
            "recommended_anchor_canonical_object_id": recommended_anchor,
            "wave_record_ids": ";".join(wave_record_ids),
            "baseline_canonical_object_ids": ";".join(baseline_group_ids),
            "unreferenced_baseline_canonical_object_ids": ";".join(unreferenced_baseline_ids),
            "matching_identifiers_json": json.dumps(
                identifiers_by_edge, sort_keys=True, separators=(",", ":")
            ),
            "matching_identifiers": ";".join(matching_identifiers),
            "distinct_gaia_dr3_ids": ";".join(gaia_ids),
            "reported_is_ucd_values": ";".join(str(value) for value in reported_roles),
            "velocity_measurement_count": len(velocity_measurements),
            "velocity_minimum_km_s": min(velocity_values) if velocity_values else "",
            "velocity_maximum_km_s": max(velocity_values) if velocity_values else "",
            "velocity_spread_km_s": velocity_spread if velocity_spread is not None else "",
            "maximum_group_separation_arcsec": maximum_separation,
        }
        group_rows.append(group_row)

        for wave_record in group_wave_records:
            nearby = wave_nearby_baseline[str(wave_record["record_id"])]
            member_rows.append(
                {
                    "group_id": group_id,
                    "member_type": "wave_record",
                    "member_id": wave_record["record_id"],
                    "current_canonical_object_id": wave_record["canonical_object_id"],
                    "bibcodes": wave_record["bibcode"],
                    "names": wave_record["original_name"],
                    "ra": wave_record["ra"],
                    "dec": wave_record["dec"],
                    "gaia_dr3_ids": "",
                    "reported_is_ucd_values": wave_record["reported_is_ucd"],
                    "classification_states": wave_record["classification_state"],
                    "identifier_linked": 1,
                    "minimum_wave_separation_arcsec": 0.0,
                    "velocities_json": json.dumps(
                        collect_velocity_measurements(wave_record["payload"]),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "nearby_baseline_separations_json": json.dumps(
                        nearby, sort_keys=True, separators=(",", ":")
                    ),
                }
            )
        for canonical_object_id in baseline_group_ids:
            canonical_records = baseline_by_canonical[canonical_object_id]
            minimum_wave_separation = min(
                wave_nearby_baseline[wave_record_id][canonical_object_id]
                for wave_record_id in wave_record_ids
                if canonical_object_id in wave_nearby_baseline[wave_record_id]
            )
            member_rows.append(
                {
                    "group_id": group_id,
                    "member_type": "baseline_canonical",
                    "member_id": canonical_object_id,
                    "current_canonical_object_id": canonical_object_id,
                    "bibcodes": ";".join(
                        sorted({str(record["bibcode"]) for record in canonical_records})
                    ),
                    "names": ";".join(
                        sorted({str(record["original_name"]) for record in canonical_records})
                    ),
                    "ra": canonical_records[0]["adopted_ra"],
                    "dec": canonical_records[0]["adopted_dec"],
                    "gaia_dr3_ids": ";".join(
                        sorted(
                            {
                                str(record["payload"].get("gaia_dr3_id") or "").strip()
                                for record in canonical_records
                                if str(record["payload"].get("gaia_dr3_id") or "").strip()
                            }
                        )
                    ),
                    "reported_is_ucd_values": ";".join(
                        str(value)
                        for value in sorted(
                            {
                                int(record["reported_is_ucd"])
                                for record in canonical_records
                                if record["reported_is_ucd"] is not None
                            }
                        )
                    ),
                    "classification_states": ";".join(
                        sorted(
                            {str(record["classification_state"]) for record in canonical_records}
                        )
                    ),
                    "identifier_linked": int(canonical_object_id in matched_baseline_ids),
                    "minimum_wave_separation_arcsec": minimum_wave_separation,
                    "velocities_json": json.dumps(
                        [
                            {**measurement, "record_id": record["record_id"]}
                            for record in canonical_records
                            for measurement in collect_velocity_measurements(record["payload"])
                        ],
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "nearby_baseline_separations_json": "",
                }
            )

        if recommendation.startswith("recommend_merge"):
            proposals.append(
                {
                    "group_id": group_id,
                    "review_status": "proposed_pending_project_lead_review",
                    "decision": "same_astrophysical_object",
                    "identity_changes_authorized": False,
                    "recommended_classification_treatment": (
                        "uncertain_reported_ucd_role_conflict"
                        if recommendation == "recommend_merge_as_uncertain_role_conflict"
                        else "derive_without_identity_conflict"
                    ),
                    "recommended_anchor_canonical_object_id": recommended_anchor,
                    "wave_record_ids": wave_record_ids,
                    "baseline_canonical_object_ids": baseline_group_ids,
                    "current_canonical_object_ids": sorted(
                        {str(record["canonical_object_id"]) for record in group_wave_records}
                        | set(baseline_group_ids)
                    ),
                    "matching_identifiers": matching_identifiers,
                    "distinct_gaia_dr3_ids": gaia_ids,
                    "reported_is_ucd_values": reported_roles,
                    "velocity_spread_km_s": velocity_spread,
                    "maximum_group_separation_arcsec": maximum_separation,
                    "routing_reason": routing_reason,
                }
            )

    group_rows.sort(key=lambda row: (str(row["recommendation"]), str(row["group_id"])))
    member_rows.sort(
        key=lambda row: (str(row["group_id"]), str(row["member_type"]), str(row["member_id"]))
    )
    proposals.sort(key=lambda row: str(row["group_id"]))
    summary = {
        "group_count": len(group_rows),
        "wave_record_count": len(
            {
                record_id
                for row in group_rows
                for record_id in str(row["wave_record_ids"]).split(";")
            }
        ),
        "baseline_canonical_count": len(
            {
                canonical_object_id
                for row in group_rows
                for canonical_object_id in str(row["baseline_canonical_object_ids"]).split(";")
            }
        ),
        "proposal_group_count": len(proposals),
        "proposal_wave_record_count": sum(
            int(row["wave_record_count"])
            for row in group_rows
            if str(row["recommendation"]).startswith("recommend_merge")
        ),
        "proposal_baseline_canonical_count": sum(
            int(row["baseline_canonical_count"])
            for row in group_rows
            if str(row["recommendation"]).startswith("recommend_merge")
        ),
        "proposal_current_canonical_count": sum(
            int(row["current_canonical_count"])
            for row in group_rows
            if str(row["recommendation"]).startswith("recommend_merge")
        ),
        "recommendation_counts": dict(
            sorted(Counter(str(row["recommendation"]) for row in group_rows).items())
        ),
        "routing_reason_counts": dict(
            sorted(Counter(str(row["routing_reason"]) for row in group_rows).items())
        ),
    }
    return group_rows, member_rows, proposals, summary


def write_csv(
    path: Path,
    rows: list[dict[str, object]],
    fieldnames: tuple[str, ...],
) -> None:
    """Write a deterministic CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=list(rows[0]) if rows else list(fieldnames),
        )
        writer.writeheader()
        writer.writerows(rows)


def write_proposals(
    path: Path,
    proposals: list[dict[str, object]],
    summary: dict[str, object],
    database_sha256: str,
) -> None:
    """Write proposed group decisions without authorizing changes."""
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if str(existing.get("review_status", "")).startswith("approved_by_project_lead"):
            return
    artifact = {
        "schema_version": 1,
        "audit_date": date.today().isoformat(),
        "review_status": "proposed_pending_project_lead_review",
        "reference_database_sha256": database_sha256,
        "decision_scope": (
            "Connected name-or-alias groups with all nearby baseline canonicals represented; "
            "proximity alone is never identity evidence."
        ),
        "proposal_group_count": len(proposals),
        "audit_summary": summary,
        "proposals": proposals,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(
    path: Path,
    group_rows: list[dict[str, object]],
    summary: dict[str, object],
    database_sha256: str,
) -> None:
    """Write a concise group-level review report."""
    recommendation_rows = "\n".join(
        f"| `{key}` | {value} |" for key, value in summary["recommendation_counts"].items()
    )
    proposed_rows = [
        row for row in group_rows if str(row["recommendation"]).startswith("recommend_merge")
    ]
    report_status = (
        "complete_no_new_proposals" if not proposed_rows else "proposed_pending_project_lead_review"
    )
    proposed_table = "\n".join(
        f"| `{row['group_id']}` | {row['matching_identifiers']} | "
        f"{row['wave_record_count']} | "
        f"{row['baseline_canonical_count']} | `{row['recommendation']}` | "
        f"{row['reported_is_ucd_values']} | {row['velocity_spread_km_s']} | "
        f"{float(row['maximum_group_separation_arcsec']):.6f} |"
        for row in proposed_rows
    )
    report = f"""# Literature Wave 1 Multi-Canonical Group Audit

**Status:** `{report_status}`
**Reference database SHA-256:** `{database_sha256}`

This read-only audit groups the Wave 1 rows whose identifier evidence intersects
multiple pre-Wave canonical objects within one arcsecond. Every nearby baseline
canonical is retained in the review group. Position alone never supports a merge.

## Coverage

| Measure | Count |
|---|---:|
| Connected review groups | {summary["group_count"]} |
| Wave 1 rows | {summary["wave_record_count"]} |
| Pre-Wave canonical objects | {summary["baseline_canonical_count"]} |
| Proposed merge groups | {summary["proposal_group_count"]} |
| Wave 1 rows in proposed groups | {summary["proposal_wave_record_count"]} |
| Pre-Wave canonicals in proposed groups | {summary["proposal_baseline_canonical_count"]} |
| Current canonicals in proposed groups | {summary["proposal_current_canonical_count"]} |

## Routing

| Recommendation | Groups |
|---|---:|
{recommendation_rows}

Groups with distinct Gaia DR3 identifiers are explicitly retained separately.
Groups with an unreferenced nearby canonical or non-identical reported velocities
remain manual. A proposed merge requires identifier coverage for every baseline
canonical and no Gaia conflict; reported positive/negative conflicts are routed to
the existing uncertain role-conflict treatment.

## Proposed Groups

| Group | Shared identifier | Wave rows | Baseline canonicals | Recommendation | UCD roles | Velocity spread, km/s | Maximum separation, arcsec |
|---|---|---:|---:|---|---|---:|---:|
{proposed_table}

The companion membership CSV preserves every record, identifier link, velocity,
Gaia identifier, and separation used for review. No identity or classification
was changed by this audit. Previously approved groups already associated with a
pre-Wave canonical are excluded from this remaining-case report.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")


def main() -> None:
    """Run the read-only group audit."""
    arguments = parse_arguments()
    database_sha256 = calculate_sha256(arguments.reference_database)
    with connect_read_only(arguments.reference_database) as connection:
        records = load_records(connection)
    group_rows, member_rows, proposals, summary = build_groups(records)
    write_csv(arguments.group_csv, group_rows, GROUP_FIELDS)
    write_csv(arguments.member_csv, member_rows, MEMBER_FIELDS)
    write_proposals(arguments.proposals, proposals, summary, database_sha256)
    write_report(arguments.report, group_rows, summary, database_sha256)


if __name__ == "__main__":
    main()
