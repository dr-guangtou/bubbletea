"""Audit Wave 1 name and published-alias matches against pre-Wave identities.

The audit excludes canonical objects represented only by Wave 1 rows and does not
use positional proximity by itself as identity evidence. It records spherical
separation, velocities, and competing nearby baseline objects for each direct-name
or published-alias match. It never changes database membership or identity.
"""

import argparse
import csv
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_REFERENCE_DB_V2,
    LITERATURE_SOURCES,
    LITERATURE_VALIDATION,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256, connect_read_only

WAVE1_BIBCODES = {
    "2016A&A...586A.102V",
    "2017ApJ...835..212K",
    "2020ApJS..250...17L",
}
IDENTIFIER_KEYS = {
    "altname",
    "aname",
    "id",
    "name",
    "oldid",
    "oname",
    "original_name",
}
IGNORED_IDENTIFIERS = {"gal", "gc", "star", "ucd", "none", "null"}
DEFAULT_OUTPUT_CSV = LITERATURE_VALIDATION / "literature_wave1_identity_candidates.csv"
DEFAULT_OUTPUT_JSON = LITERATURE_SOURCES / "literature_wave1_identity_proposals.json"
DEFAULT_OUTPUT_REPORT = LITERATURE_VALIDATION / "literature_wave1_identity_candidates.md"


def parse_arguments() -> argparse.Namespace:
    """Parse audit paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-report", type=Path, default=DEFAULT_OUTPUT_REPORT)
    return parser.parse_args()


def normalize_identifier(value: object) -> str:
    """Normalize one catalog identifier without inventing equivalences."""
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def valid_identifier(value: object) -> bool:
    """Return whether a token is sufficiently specific for identity screening."""
    normalized = normalize_identifier(value)
    return (
        normalized not in IGNORED_IDENTIFIERS
        and len(normalized) >= 2
        and any(character.isalpha() for character in normalized)
        and any(character.isdigit() for character in normalized)
    )


def split_identifier_value(value: object) -> list[str]:
    """Split only explicit catalog alias delimiters."""
    if value is None:
        return []
    return [
        token.strip()
        for token in re.split(r"[/;,]", str(value))
        if token.strip() and valid_identifier(token)
    ]


def collect_payload_identifiers(payload: object, path: str = "payload") -> list[dict[str, str]]:
    """Collect identifiers from reviewed name-bearing payload fields."""
    identifiers = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            child_path = f"{path}.{key}"
            if key.lower() in IDENTIFIER_KEYS and not isinstance(value, dict | list):
                identifiers.extend(
                    {"identifier": token, "source": child_path}
                    for token in split_identifier_value(value)
                )
            elif isinstance(value, dict | list):
                identifiers.extend(collect_payload_identifiers(value, child_path))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            identifiers.extend(collect_payload_identifiers(value, f"{path}[{index}]"))
    return identifiers


def record_identifiers(record: dict[str, object]) -> list[dict[str, str]]:
    """Return deduplicated original and published identifiers for one row."""
    identifiers = []
    if valid_identifier(record["original_name"]):
        identifiers.append({"identifier": str(record["original_name"]), "source": "original_name"})
    identifiers.extend(collect_payload_identifiers(record["payload"]))
    deduplicated = {}
    for item in identifiers:
        key = (normalize_identifier(item["identifier"]), item["source"])
        deduplicated[key] = item
    return list(deduplicated.values())


def first_numeric(value: object) -> float | None:
    """Parse one finite numeric value."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if np.isfinite(parsed) else None


def collect_velocity_measurements(
    payload: object, path: str = "payload"
) -> list[dict[str, object]]:
    """Collect reported radial velocities and adjacent uncertainties."""
    measurements = []
    if isinstance(payload, dict):
        lower_keys = {key.lower(): key for key in payload}
        for key, value in payload.items():
            normalized_key = key.lower()
            if normalized_key not in {"hrv", "rv", "radial_velocity"}:
                continue
            velocity = first_numeric(value)
            if velocity is None or not -2000 <= velocity <= 300000:
                continue
            uncertainty = None
            for uncertainty_key in (
                f"e_{normalized_key}",
                "radial_velocity_err",
                "e_hrv",
                "e_rv",
            ):
                actual_key = lower_keys.get(uncertainty_key)
                if actual_key is not None:
                    uncertainty = first_numeric(payload[actual_key])
                    if uncertainty is not None:
                        break
            measurements.append(
                {
                    "velocity_km_s": velocity,
                    "uncertainty_km_s": uncertainty,
                    "source": f"{path}.{key}",
                }
            )
        for key, value in payload.items():
            if isinstance(value, dict | list):
                measurements.extend(collect_velocity_measurements(value, f"{path}.{key}"))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            measurements.extend(collect_velocity_measurements(value, f"{path}[{index}]"))
    deduplicated = {}
    for measurement in measurements:
        key = (
            measurement["velocity_km_s"],
            measurement["uncertainty_km_s"],
            measurement["source"],
        )
        deduplicated[key] = measurement
    return list(deduplicated.values())


def load_records(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Load associated coordinate-bearing literature records."""
    rows = connection.execute(
        """
        SELECT
            r.record_id,
            p.bibcode,
            r.original_name,
            r.ra,
            r.dec,
            r.host_galaxy,
            r.reported_is_ucd,
            r.raw_payload_json,
            a.canonical_object_id,
            a.association_method,
            c.adopted_ra,
            c.adopted_dec,
            cl.classification_state,
            cl.classification_subtype
        FROM literature_records r
        JOIN datasets d USING (dataset_id)
        JOIN publications p USING (publication_id)
        JOIN object_record_associations a USING (record_id)
        JOIN canonical_objects c USING (canonical_object_id)
        JOIN object_classifications cl USING (canonical_object_id)
        WHERE r.ra IS NOT NULL AND r.dec IS NOT NULL
        ORDER BY p.bibcode, r.record_id
        """
    ).fetchall()
    return [
        {
            **dict(row),
            "payload": json.loads(row["raw_payload_json"]),
        }
        for row in rows
    ]


def compact_velocity_json(measurements: list[dict[str, object]]) -> str:
    """Serialize velocities deterministically for review."""
    return json.dumps(measurements, sort_keys=True, separators=(",", ":"))


def build_candidates(records: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict]:
    """Build name-led Wave 1 identity candidates with positional context."""
    baseline_records = [record for record in records if record["bibcode"] not in WAVE1_BIBCODES]
    wave_records = [record for record in records if record["bibcode"] in WAVE1_BIBCODES]
    baseline_canonical_ids = {str(record["canonical_object_id"]) for record in baseline_records}
    remaining_wave_records = [
        record
        for record in wave_records
        if str(record["canonical_object_id"]) not in baseline_canonical_ids
    ]

    baseline_by_canonical = defaultdict(list)
    identifier_index = defaultdict(set)
    identifier_details_by_canonical = defaultdict(list)
    for record in baseline_records:
        canonical_object_id = str(record["canonical_object_id"])
        baseline_by_canonical[canonical_object_id].append(record)
        for identifier in record_identifiers(record):
            normalized = normalize_identifier(identifier["identifier"])
            identifier_index[normalized].add(canonical_object_id)
            identifier_details_by_canonical[canonical_object_id].append(
                {**identifier, "normalized": normalized, "bibcode": record["bibcode"]}
            )

    canonical_ids = sorted(baseline_by_canonical)
    canonical_coordinates = SkyCoord(
        [float(baseline_by_canonical[item][0]["adopted_ra"]) for item in canonical_ids] * u.deg,
        [float(baseline_by_canonical[item][0]["adopted_dec"]) for item in canonical_ids] * u.deg,
    )
    canonical_index = {
        canonical_object_id: index for index, canonical_object_id in enumerate(canonical_ids)
    }

    candidates = []
    for wave_record in remaining_wave_records:
        wave_identifiers = record_identifiers(wave_record)
        wave_by_normalized = defaultdict(list)
        for identifier in wave_identifiers:
            wave_by_normalized[normalize_identifier(identifier["identifier"])].append(identifier)
        target_matches = defaultdict(set)
        for normalized_identifier in wave_by_normalized:
            for canonical_object_id in identifier_index.get(normalized_identifier, set()):
                target_matches[canonical_object_id].add(normalized_identifier)
        if not target_matches:
            continue

        wave_coordinate = SkyCoord(
            float(wave_record["ra"]) * u.deg, float(wave_record["dec"]) * u.deg
        )
        separations = wave_coordinate.separation(canonical_coordinates).arcsec
        nearest_order = np.argsort(separations)
        nearest_id = canonical_ids[int(nearest_order[0])]
        second_nearest_id = canonical_ids[int(nearest_order[1])]
        baseline_within_1_arcsec = int(np.sum(separations <= 1.0))
        baseline_within_5_arcsec = int(np.sum(separations <= 5.0))
        wave_velocities = collect_velocity_measurements(wave_record["payload"])

        for target_canonical_id, matching_identifiers in sorted(target_matches.items()):
            target_index = canonical_index[target_canonical_id]
            target_separation = float(separations[target_index])
            target_records = baseline_by_canonical[target_canonical_id]
            target_identifiers = identifier_details_by_canonical[target_canonical_id]
            direct_name = normalize_identifier(wave_record["original_name"]) in {
                normalize_identifier(record["original_name"]) for record in target_records
            }
            matching_wave_sources = sorted(
                {
                    item["source"]
                    for normalized in matching_identifiers
                    for item in wave_by_normalized[normalized]
                }
            )
            matching_target_sources = sorted(
                {
                    item["source"]
                    for item in target_identifiers
                    if item["normalized"] in matching_identifiers
                }
            )
            evidence_class = "direct_name" if direct_name else "published_alias"
            target_velocities = [
                {**measurement, "bibcode": record["bibcode"], "name": record["original_name"]}
                for record in target_records
                for measurement in collect_velocity_measurements(record["payload"])
            ]
            velocity_differences = [
                abs(float(wave["velocity_km_s"]) - float(target["velocity_km_s"]))
                for wave in wave_velocities
                for target in target_velocities
            ]
            nearest_is_target = target_canonical_id == nearest_id
            competing_within_1_arcsec = baseline_within_1_arcsec - int(target_separation <= 1.0)
            if target_separation <= 1.0 and nearest_is_target and competing_within_1_arcsec == 0:
                recommendation = "recommend_same_identity"
                routing_reason = "unique_nearest_name_or_alias_match_within_1_arcsec"
            elif target_separation <= 5.0:
                recommendation = "manual_identity_review"
                if baseline_within_1_arcsec > 1:
                    routing_reason = "multiple_baseline_canonicals_within_1_arcsec"
                elif not nearest_is_target:
                    routing_reason = "identifier_matched_target_is_not_nearest"
                else:
                    routing_reason = "name_or_alias_match_between_1_and_5_arcsec"
            else:
                recommendation = "identifier_collision_not_recommended"
                routing_reason = "identifier_match_is_spatially_inconsistent"
            candidates.append(
                {
                    "wave_record_id": wave_record["record_id"],
                    "wave_bibcode": wave_record["bibcode"],
                    "wave_original_name": wave_record["original_name"],
                    "wave_ra": wave_record["ra"],
                    "wave_dec": wave_record["dec"],
                    "wave_reported_is_ucd": wave_record["reported_is_ucd"],
                    "wave_current_canonical_object_id": wave_record["canonical_object_id"],
                    "target_canonical_object_id": target_canonical_id,
                    "target_names": ";".join(
                        sorted({str(record["original_name"]) for record in target_records})
                    ),
                    "target_bibcodes": ";".join(
                        sorted({str(record["bibcode"]) for record in target_records})
                    ),
                    "target_classification_state": target_records[0]["classification_state"],
                    "target_classification_subtype": (
                        target_records[0]["classification_subtype"] or ""
                    ),
                    "matching_identifiers": ";".join(sorted(matching_identifiers)),
                    "evidence_class": evidence_class,
                    "matching_wave_fields": ";".join(matching_wave_sources),
                    "matching_target_fields": ";".join(matching_target_sources),
                    "separation_arcsec": target_separation,
                    "target_is_nearest_baseline": int(nearest_is_target),
                    "nearest_baseline_canonical_object_id": nearest_id,
                    "nearest_baseline_separation_arcsec": float(separations[int(nearest_order[0])]),
                    "second_nearest_baseline_canonical_object_id": second_nearest_id,
                    "second_nearest_baseline_separation_arcsec": float(
                        separations[int(nearest_order[1])]
                    ),
                    "baseline_objects_within_1_arcsec": baseline_within_1_arcsec,
                    "baseline_objects_within_5_arcsec": baseline_within_5_arcsec,
                    "wave_velocities_json": compact_velocity_json(wave_velocities),
                    "target_velocities_json": compact_velocity_json(target_velocities),
                    "minimum_velocity_difference_km_s": (
                        min(velocity_differences) if velocity_differences else ""
                    ),
                    "recommendation": recommendation,
                    "routing_reason": routing_reason,
                }
            )
    candidates.sort(
        key=lambda row: (
            str(row["recommendation"]),
            float(row["separation_arcsec"]),
            str(row["wave_record_id"]),
            str(row["target_canonical_object_id"]),
        )
    )
    summary = {
        "baseline_canonical_count": len(canonical_ids),
        "wave_record_count": len(wave_records),
        "wave_records_already_linked_to_baseline": len(wave_records) - len(remaining_wave_records),
        "remaining_wave_record_count": len(remaining_wave_records),
        "identifier_match_pair_count": len(candidates),
        "matched_wave_record_count": len({row["wave_record_id"] for row in candidates}),
        "recommendation_counts": dict(
            sorted(Counter(str(row["recommendation"]) for row in candidates).items())
        ),
        "recommendation_wave_record_counts": {
            recommendation: len(
                {
                    row["wave_record_id"]
                    for row in candidates
                    if row["recommendation"] == recommendation
                }
            )
            for recommendation in sorted({str(row["recommendation"]) for row in candidates})
        },
        "evidence_class_counts": dict(
            sorted(Counter(str(row["evidence_class"]) for row in candidates).items())
        ),
        "routing_reason_counts": dict(
            sorted(Counter(str(row["routing_reason"]) for row in candidates).items())
        ),
    }
    return candidates, summary


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write deterministic row-level review evidence."""
    if not rows:
        raise RuntimeError("Wave 1 identifier audit found no matches")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_proposals(
    path: Path,
    rows: list[dict[str, object]],
    database_sha256: str,
) -> None:
    """Write the small recommended cohort pending project-lead review."""
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if str(existing.get("review_status", "")).startswith("approved_by_project_lead"):
            return
    proposals = []
    for row in rows:
        if row["recommendation"] != "recommend_same_identity":
            continue
        proposals.append(
            {
                "proposal_id": (
                    f"wave1_{row['wave_record_id']}_{row['target_canonical_object_id']}"
                ),
                "review_status": "proposed_pending_project_lead_review",
                "decision": "same_astrophysical_object",
                "identity_changes_authorized": False,
                "wave_record_id": row["wave_record_id"],
                "wave_bibcode": row["wave_bibcode"],
                "wave_original_name": row["wave_original_name"],
                "target_canonical_object_id": row["target_canonical_object_id"],
                "target_names": str(row["target_names"]).split(";"),
                "target_bibcodes": str(row["target_bibcodes"]).split(";"),
                "target_classification_state": row["target_classification_state"],
                "target_classification_subtype": row["target_classification_subtype"] or None,
                "evidence_class": row["evidence_class"],
                "matching_identifiers": str(row["matching_identifiers"]).split(";"),
                "separation_arcsec": row["separation_arcsec"],
                "target_is_nearest_baseline": bool(row["target_is_nearest_baseline"]),
                "baseline_objects_within_1_arcsec": row["baseline_objects_within_1_arcsec"],
                "minimum_velocity_difference_km_s": (
                    row["minimum_velocity_difference_km_s"]
                    if row["minimum_velocity_difference_km_s"] != ""
                    else None
                ),
            }
        )
    artifact = {
        "schema_version": 1,
        "audit_date": date.today().isoformat(),
        "review_status": "proposed_pending_project_lead_review",
        "reference_database_sha256": database_sha256,
        "decision_scope": (
            "Name or published-alias matches with the reviewed target as the unique nearest "
            "pre-Wave canonical object within one arcsecond; this is not a general radius rule."
        ),
        "proposal_count": len(proposals),
        "proposals": proposals,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(
    path: Path,
    summary: dict[str, object],
    rows: list[dict[str, object]],
    database_sha256: str,
) -> None:
    """Write a concise review report."""
    recommendation_rows = "\n".join(
        f"| `{key}` | {value} | {summary['recommendation_wave_record_counts'][key]} |"
        for key, value in summary["recommendation_counts"].items()
    )
    routing_reason_rows = "\n".join(
        f"| `{key}` | {value} |" for key, value in summary["routing_reason_counts"].items()
    )
    proposed_rows = [row for row in rows if row["recommendation"] == "recommend_same_identity"]
    proposed_table = "\n".join(
        f"| {row['wave_bibcode']} | {row['wave_original_name']} | "
        f"{row['target_names']} | {float(row['separation_arcsec']):.12f} | "
        f"`{row['evidence_class']}` | "
        f"{row['minimum_velocity_difference_km_s']} |"
        for row in proposed_rows
    )
    report = f"""# Literature Wave 1 Identity Candidate Audit

**Status:** `proposed_pending_project_lead_review`
**Reference database SHA-256:** `{database_sha256}`

This read-only audit compares Wave 1 object and comparison rows only with
canonical identities containing pre-Wave literature records. Position alone never
creates a candidate: every row below requires an exact normalized name or a
published alias from a source payload.

## Coverage

| Measure | Count |
|---|---:|
| Pre-Wave canonical identities | {summary["baseline_canonical_count"]} |
| Wave 1 literature rows | {summary["wave_record_count"]} |
| Wave 1 rows already linked to pre-Wave identities | {summary["wave_records_already_linked_to_baseline"]} |
| Remaining Wave 1 rows screened | {summary["remaining_wave_record_count"]} |
| Wave 1 rows with name or alias matches | {summary["matched_wave_record_count"]} |
| Wave-to-canonical identifier match pairs | {summary["identifier_match_pair_count"]} |

## Routing

| Recommendation | Match pairs | Wave rows |
|---|---:|---:|
{recommendation_rows}

| Routing reason | Match pairs |
|---|---:|
{routing_reason_rows}

`recommend_same_identity` requires identifier evidence, the matched canonical as
the nearest baseline object, separation no greater than one arcsecond, and no
competing baseline object within one arcsecond. The angular condition is a guard
on a name-led cohort, not a reusable matching radius.

## Proposed High-Confidence Cohort

| Wave bibcode | Wave name | Baseline names | Separation, arcsec | Evidence | Minimum velocity difference, km/s |
|---|---|---|---:|---|---:|
{proposed_table}

Rows routed to manual review or identifier collision remain in the companion CSV.
No association, canonical identity, or classification was changed.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")


def main() -> None:
    """Run the read-only Wave 1 identity audit."""
    arguments = parse_arguments()
    database_sha256 = calculate_sha256(arguments.reference_database)
    with connect_read_only(arguments.reference_database) as connection:
        records = load_records(connection)
    rows, summary = build_candidates(records)
    write_csv(arguments.output_csv, rows)
    write_proposals(arguments.output_json, rows, database_sha256)
    write_report(arguments.output_report, summary, rows, database_sha256)


if __name__ == "__main__":
    main()
