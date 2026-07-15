"""Audit and route the remaining Wave 1 multi-canonical source identities.

This audit resolves catalog lineage from original Liu, Zhang, Ko, Fahrion, and
Brodie source rows. It treats S547 and VUCD3 as two distinct objects and never
uses proximity alone as identity evidence. The default output is review-only;
authorization requires the explicit delegated-approval command-line flag.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LITERATURE_REFERENCE_DB_V2,
    LITERATURE_SOURCES,
    LITERATURE_VALIDATION,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256, connect_read_only
from scripts.phase1_literature.audit_wave1_identity_candidates import (
    load_records,
    normalize_identifier,
    record_identifiers,
)

DEFAULT_GROUP_CSV = LITERATURE_VALIDATION / "literature_wave1_multi_canonical_groups.csv"
DEFAULT_MEMBER_CSV = LITERATURE_VALIDATION / "literature_wave1_multi_canonical_members.csv"
DEFAULT_OUTPUT = LITERATURE_SOURCES / "literature_wave1_remaining_identity_reviews.json"
DEFAULT_REPORT = LITERATURE_VALIDATION / "literature_wave1_remaining_identity_reviews.md"
LIU2015_TABLE = PROJECT_ROOT / "reference" / "liu2015" / "table3.dat"
BRODIE_EVIDENCE = LITERATURE_SOURCES / "brodie2011_identity_evidence.json"
GAIA_IMAGE_REVIEW = LITERATURE_SOURCES / "gaia_image_ambiguity_reviews.json"

WHOLE_VELOCITY_IDENTIFIERS = {"h36612", "s5065", "vucd5", "vucd7"}
SPECIAL_SOURCE_IDENTIFIERS = {"s887", "t15886"}
DELEGATED_APPROVAL_STATUS = "approved_by_project_lead_delegation_2026-07-15"


def parse_arguments() -> argparse.Namespace:
    """Parse audit inputs and approval mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--group-csv", type=Path, default=DEFAULT_GROUP_CSV)
    parser.add_argument("--member-csv", type=Path, default=DEFAULT_MEMBER_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--authorize-under-delegation",
        action="store_true",
        help="Record the project lead's delegated source-audit authorization.",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read one audit CSV."""
    with path.open(encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def load_liu2015_aliases() -> dict[str, str]:
    """Map Liu 2015 NGVS coordinate identifiers to published alternate names."""
    aliases = {}
    for line in LIU2015_TABLE.read_text(encoding="utf-8").splitlines():
        ngvs_identifier = line[9:28].strip()
        alternate_name = line[126:134].strip()
        if ngvs_identifier and alternate_name and alternate_name != "---":
            aliases[ngvs_identifier] = alternate_name
    if len(aliases) != 80:
        raise RuntimeError(f"Expected 80 Liu 2015 aliases, found {len(aliases)}")
    return aliases


def record_identifier_set(record: dict[str, object]) -> set[str]:
    """Return normalized source-published identifiers for one record."""
    return {normalize_identifier(item["identifier"]) for item in record_identifiers(record)}


def liu_ngvs_identifiers(record: dict[str, object]) -> set[str]:
    """Return NGVS coordinate identifiers retained in a record payload."""
    identifiers = set()
    payload = record["payload"]
    if isinstance(payload, dict):
        primary_row = payload.get("authoritative_primary_row")
        if isinstance(primary_row, dict) and primary_row.get("NGVS"):
            identifiers.add(str(primary_row["NGVS"]))
    original_name = str(record.get("original_name") or "")
    if re.fullmatch(r"J\d{6}(?:\.\d+)?[+-]\d{6}(?:\.\d+)?", original_name):
        identifiers.add(original_name)
    return identifiers


def proposal_status(authorized: bool) -> tuple[str, bool]:
    """Return explicit review status and authorization state."""
    if authorized:
        return DELEGATED_APPROVAL_STATUS, True
    return "proposed_pending_project_lead_review", False


def build_proposals(
    groups: list[dict[str, str]],
    members: list[dict[str, str]],
    records: list[dict[str, object]],
    authorized: bool,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Build source-supported identity decisions for every remaining group."""
    members_by_group = defaultdict(list)
    for member in members:
        members_by_group[member["group_id"]].append(member)
    records_by_id = {str(record["record_id"]): record for record in records}
    liu2015_aliases = load_liu2015_aliases()
    brodie_evidence = json.loads(BRODIE_EVIDENCE.read_text(encoding="utf-8"))
    brodie_by_identifier = {
        normalize_identifier(row["identifier"]): row for row in brodie_evidence["rows"]
    }
    gaia_review = json.loads(GAIA_IMAGE_REVIEW.read_text(encoding="utf-8"))
    separate_pair = gaia_review["recommended_separate_objects"][0]
    if set(separate_pair["object_names"]) != {"S547", "VUCD3"}:
        raise RuntimeError("The approved S547/VUCD3 separate-object decision changed")

    review_status, identity_changes_authorized = proposal_status(authorized)
    proposals = []
    evidence_counts = Counter()
    covered_group_ids = set()
    covered_current_canonical_ids = set()

    def append_proposal(
        group: dict[str, str],
        suffix: str,
        current_canonical_ids: set[str],
        anchor_canonical_id: str,
        matching_identifiers: list[str],
        evidence_class: str,
        evidence: dict[str, object],
        classification_treatment: str,
        retained_separate_from: list[str] | None = None,
    ) -> None:
        overlap = current_canonical_ids & covered_current_canonical_ids
        if overlap:
            raise RuntimeError(f"Canonical identity is proposed twice: {sorted(overlap)}")
        if anchor_canonical_id not in current_canonical_ids:
            raise RuntimeError(f"Proposal anchor is outside its identity: {group['group_id']}")
        covered_current_canonical_ids.update(current_canonical_ids)
        evidence_counts[evidence_class] += 1
        proposals.append(
            {
                "decision_id": f"{group['group_id']}:{suffix}",
                "parent_group_id": group["group_id"],
                "review_status": review_status,
                "decision": "same_astrophysical_object",
                "identity_changes_authorized": identity_changes_authorized,
                "current_canonical_object_ids": sorted(current_canonical_ids),
                "recommended_anchor_canonical_object_id": anchor_canonical_id,
                "matching_identifiers": matching_identifiers,
                "evidence_class": evidence_class,
                "source_evidence": evidence,
                "recommended_classification_treatment": classification_treatment,
                "retained_separate_from": retained_separate_from or [],
            }
        )

    for group in groups:
        group_id = group["group_id"]
        group_members = members_by_group[group_id]
        identifier_values = group["matching_identifiers"].split(";")
        group_current_canonical_ids = {
            member["current_canonical_object_id"] for member in group_members
        }
        classification_treatment = (
            "uncertain_reported_ucd_role_conflict"
            if group["reported_is_ucd_values"] == "0;1"
            else "derive_without_identity_conflict"
        )

        if group["matching_identifiers"] == "s547;vucd3":
            for target_identifier in ("s547", "vucd3"):
                target_members = []
                for member in group_members:
                    if member["member_type"] == "wave_record":
                        identifiers = record_identifier_set(records_by_id[member["member_id"]])
                    else:
                        identifiers = {
                            normalize_identifier(name) for name in member["names"].split(";")
                        }
                    if target_identifier in identifiers:
                        target_members.append(member)
                target_canonical_ids = {
                    member["current_canonical_object_id"] for member in target_members
                }
                baseline_targets = [
                    member["current_canonical_object_id"]
                    for member in target_members
                    if member["member_type"] == "baseline_canonical"
                ]
                if len(target_canonical_ids) != 2 or len(baseline_targets) != 1:
                    raise RuntimeError(f"Unexpected {target_identifier} subgroup membership")
                append_proposal(
                    group,
                    target_identifier,
                    target_canonical_ids,
                    baseline_targets[0],
                    [target_identifier],
                    "published_identifier_with_reviewed_close_pair_split",
                    {
                        "gaia_dr3_id": separate_pair["gaia_dr3_id"],
                        "separate_object_rationale": separate_pair["rationale"],
                        "source_rows": "Zhang 2015, Ko 2017, Liu 2020, and Fahrion 2019",
                    },
                    "derive_without_identity_conflict",
                    ["vucd3" if target_identifier == "s547" else "s547"],
                )
            covered_group_ids.add(group_id)
            continue

        identifier = identifier_values[0]
        if identifier in WHOLE_VELOCITY_IDENTIFIERS:
            append_proposal(
                group,
                identifier,
                group_current_canonical_ids,
                group["recommended_anchor_canonical_object_id"],
                identifier_values,
                "published_identifier_with_independent_or_weighted_velocity_measurements",
                {
                    "liu2020_velocity_treatment": (
                        "heliocentric radial velocity or weighted mean when multiple "
                        "measurements are available"
                    ),
                    "velocity_spread_km_s": float(group["velocity_spread_km_s"]),
                    "source_rows": "Zhang 2015, Ko 2017, Liu 2020, and Fahrion 2019",
                },
                classification_treatment,
            )
            covered_group_ids.add(group_id)
            continue

        if identifier in SPECIAL_SOURCE_IDENTIFIERS:
            if identifier == "s887":
                brodie_row = brodie_by_identifier["s887"]
                evidence_class = "brodie_identifier_corrects_fahrion_transcription"
                evidence = {
                    "brodie_catalog_id": brodie_evidence["catalog_id"],
                    "brodie_row": brodie_row,
                    "fahrion_identifier": "S877",
                    "zhang_ko_identifier": "S887",
                    "shared_velocity_km_s": 1811.0,
                }
            else:
                brodie_row = brodie_by_identifier["h39168"]
                evidence_class = "brodie_cross_catalog_position_velocity_size_identity"
                evidence = {
                    "brodie_catalog_id": brodie_evidence["catalog_id"],
                    "brodie_identifier": "H39168",
                    "brodie_row": brodie_row,
                    "zhang_ko_identifier": "T15886",
                    "shared_velocity_km_s": 1349.0,
                    "shared_half_light_radius_pc": 11.0,
                }
            append_proposal(
                group,
                identifier,
                group_current_canonical_ids,
                group["recommended_anchor_canonical_object_id"],
                identifier_values,
                evidence_class,
                evidence,
                classification_treatment,
            )
            covered_group_ids.add(group_id)
            continue

        ngvs_candidates = set()
        for member in group_members:
            if member["member_type"] == "wave_record":
                ngvs_candidates.update(liu_ngvs_identifiers(records_by_id[member["member_id"]]))
            for name in member["names"].split(";"):
                if name.startswith("J"):
                    ngvs_candidates.add(name)
        alias_matches = [
            (ngvs_identifier, alternate_name)
            for ngvs_identifier, alternate_name in liu2015_aliases.items()
            if ngvs_identifier in ngvs_candidates
            and normalize_identifier(alternate_name) == identifier
        ]
        if len(alias_matches) != 1:
            raise RuntimeError(
                f"Expected one Liu 2015 alias-chain match for {group_id}, found {alias_matches}"
            )
        ngvs_identifier, alternate_name = alias_matches[0]
        append_proposal(
            group,
            identifier,
            group_current_canonical_ids,
            group["recommended_anchor_canonical_object_id"],
            identifier_values,
            "liu2015_published_alias_chain",
            {
                "liu2015_bibcode": "2015ApJ...812...34L",
                "liu2015_ngvs_identifier": ngvs_identifier,
                "liu2015_other_name": alternate_name,
                "fahrion_reference_code": 2,
                "fahrion_reference_meaning": "Brodie et al. 2011",
                "wave_sources": "Ko 2017 direct name and/or Liu 2020 OName",
            },
            classification_treatment,
        )
        covered_group_ids.add(group_id)

    expected_group_ids = {group["group_id"] for group in groups}
    if covered_group_ids != expected_group_ids:
        raise RuntimeError(
            f"Remaining source audit missed groups: {sorted(expected_group_ids - covered_group_ids)}"
        )
    if len(proposals) != 80 or len(covered_current_canonical_ids) != 309:
        raise RuntimeError(
            "Expected 80 identities covering 309 current canonicals, found "
            f"{len(proposals)} and {len(covered_current_canonical_ids)}"
        )
    summary = {
        "input_group_count": len(groups),
        "proposed_identity_count": len(proposals),
        "covered_current_canonical_count": len(covered_current_canonical_ids),
        "retained_final_identity_count": len(proposals),
        "retired_canonical_count": len(covered_current_canonical_ids) - len(proposals),
        "evidence_class_counts": dict(sorted(evidence_counts.items())),
        "classification_treatment_counts": dict(
            sorted(
                Counter(
                    proposal["recommended_classification_treatment"] for proposal in proposals
                ).items()
            )
        ),
    }
    proposals.sort(key=lambda proposal: str(proposal["decision_id"]))
    return proposals, summary


def write_artifact(
    path: Path,
    proposals: list[dict[str, object]],
    summary: dict[str, object],
    database_sha256: str,
    authorized: bool,
) -> None:
    """Write the deterministic decision manifest without overwriting approval."""
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if str(existing.get("review_status", "")).startswith("approved_by_project_lead_delegation"):
            return
    review_status, _ = proposal_status(authorized)
    artifact = {
        "schema_version": 1,
        "audit_date": date.today().isoformat(),
        "review_status": review_status,
        "delegated_authorization_scope": (
            "Continue source auditing autonomously until scientific input is absolutely required"
            if authorized
            else None
        ),
        "reference_database_sha256": database_sha256,
        "decision_scope": (
            "Source-specific catalog lineage and object evidence; proximity alone is never "
            "identity evidence. S547 and VUCD3 remain distinct."
        ),
        "summary": summary,
        "proposals": proposals,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(
    path: Path,
    summary: dict[str, object],
    database_sha256: str,
    authorized: bool,
) -> None:
    """Write a concise human-readable source-audit report."""
    review_status, _ = proposal_status(authorized)
    evidence_rows = "\n".join(
        f"| `{key}` | {value} |" for key, value in summary["evidence_class_counts"].items()
    )
    report = f"""# Wave 1 Remaining Source Identity Audit

**Status:** `{review_status}`
**Reference database SHA-256:** `{database_sha256}`

## Coverage

| Measure | Count |
|---|---:|
| Input connected groups | {summary["input_group_count"]} |
| Source-supported final identities | {summary["proposed_identity_count"]} |
| Current canonicals covered | {summary["covered_current_canonical_count"]} |
| Superseded canonical identifiers to retain as aliases | {summary["retired_canonical_count"]} |

## Evidence Routing

| Evidence class | Identities |
|---|---:|
{evidence_rows}

Seventy-two identities are supported by exact Liu 2015 NGVS catalog keys and
published `Other` aliases that connect the coordinate-designated Liu/Fahrion rows
to the Zhang, Ko, and Liu 2020 names. Brodie catalog evidence resolves S887/S877
and T15886/H39168. Four velocity-difference groups retain every published value;
the Liu 2020 values are adopted or weighted means, not competing object IDs.

The prior S547/VUCD3 review is preserved: their rows form two identities rather
than one, and their unresolved shared Gaia source remains ambiguity evidence.
Position is context only and is never used as the identity relation.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")


def main() -> None:
    """Run the remaining source identity audit."""
    arguments = parse_arguments()
    database_sha256 = calculate_sha256(arguments.reference_database)
    groups = read_csv(arguments.group_csv)
    members = read_csv(arguments.member_csv)
    if not groups:
        if not arguments.output.exists():
            raise RuntimeError("No remaining groups and no approved source-audit artifact")
        persisted_artifact = json.loads(arguments.output.read_text(encoding="utf-8"))
        if not str(persisted_artifact.get("review_status", "")).startswith(
            "approved_by_project_lead_delegation"
        ):
            raise RuntimeError("Empty post-build audit lacks an approved source decision")
        write_report(
            arguments.report,
            persisted_artifact["summary"],
            str(persisted_artifact["reference_database_sha256"]),
            True,
        )
        return
    with connect_read_only(arguments.reference_database) as connection:
        records = load_records(connection)
    proposals, summary = build_proposals(
        groups,
        members,
        records,
        arguments.authorize_under_delegation,
    )
    write_artifact(
        arguments.output,
        proposals,
        summary,
        database_sha256,
        arguments.authorize_under_delegation,
    )
    persisted_artifact = json.loads(arguments.output.read_text(encoding="utf-8"))
    effective_authorized = str(persisted_artifact.get("review_status", "")).startswith(
        "approved_by_project_lead_delegation"
    )
    write_report(arguments.report, summary, database_sha256, effective_authorized)


if __name__ == "__main__":
    main()
