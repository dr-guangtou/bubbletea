"""Validate a Part I submission and recompute its selections for instructor review.

Run with --answers path/to/student.json. Results go to stdout unless --output is
given. This is an instructor tool: it reads the separate reference key and never
changes student files or the scientific catalogs. Uncertainty and Task 3 need
human assessment; no final grade is assigned automatically.
"""

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import teaching_part1_key, teaching_part1_packet
from scripts.teaching.build_part1_materials import feature_definitions

feature_keys = [field[0] for field in feature_definitions]


def exact_keys(value, keys):
    return isinstance(value, dict) and set(value) == set(keys)


def check_text(value, limit):
    return isinstance(value, str) and len(value) <= limit


def validate_rules(rules):
    if not exact_keys(rules, feature_keys):
        raise ValueError("Invalid feature set")
    for field, rule in rules.items():
        if (
            not exact_keys(rule, ["enabled", "minimum", "maximum"])
            or type(rule["enabled"]) is not bool
        ):
            raise ValueError(f"Invalid rule: {field}")
        for bound in [rule["minimum"], rule["maximum"]]:
            if bound is not None and (
                type(bound) not in [int, float] or not math.isfinite(bound) or abs(bound) > 1e15
            ):
                raise ValueError("Invalid bound")
        if (
            rule["minimum"] is not None
            and rule["maximum"] is not None
            and rule["minimum"] > rule["maximum"]
        ):
            raise ValueError("Reversed interval")


def score_rules(packet, rules, missing_policy):
    """Use independent vectorized masks, including nulls and inclusive boundaries."""
    validate_rules(rules)
    if missing_policy not in ["keep", "exclude"]:
        raise ValueError("Invalid missing-data policy")
    columns = {name: index for index, name in enumerate(packet["catalog_columns"])}
    rows = packet["catalog_rows"]
    selected = np.ones(len(rows), dtype=bool)
    missing = np.zeros(len(rows), dtype=bool)
    for key, rule in rules.items():
        if not rule["enabled"]:
            continue
        values = np.array(
            [row[columns[key]] if row[columns[key]] is not None else np.nan for row in rows]
        )
        unavailable = np.isnan(values)
        missing |= unavailable
        accepted = np.ones(len(rows), dtype=bool)
        if rule["minimum"] is not None:
            accepted &= values >= rule["minimum"]
        if rule["maximum"] is not None:
            accepted &= values <= rule["maximum"]
        accepted[unavailable] = missing_policy == "keep"
        selected &= accepted
    labels = np.array([row[columns["reference_class"]] for row in rows])
    counts = {
        label: int(np.sum(selected & (labels == label)))
        for label in ["ucd", "star", "qso", "candidate"]
    }
    counts["selected_missing"] = int(np.sum(selected & missing))
    counts["total_selected"] = int(selected.sum())
    scored = counts["ucd"] + counts["star"] + counts["qso"]
    total_ucd = int(np.sum(labels == "ucd"))
    return {
        "counts": counts,
        "metrics": {
            "purity": counts["ucd"] / scored if scored else None,
            "completeness": counts["ucd"] / total_ucd if total_ucd else None,
            "f1": 2 * counts["ucd"] / (total_ucd + scored) if total_ucd + scored else None,
        },
    }


def same_numbers(left, right):
    if not exact_keys(left, right):
        return False
    return all(
        left[key] is None
        if value is None
        else type(left[key]) in [int, float]
        and math.isfinite(left[key])
        and abs(left[key] - value) < 1e-12
        for key, value in right.items()
    )


def upgrade_v2_answers(answers, packet, top_keys):
    """Keep old final choices, validate old scores, and require a new final selection."""
    if not isinstance(answers, dict) or answers.get("schema_version") != "bubbletea_answers_v2":
        return answers
    old_keys = [
        name
        for name in top_keys
        if name not in ["task2_final_selection", "imported_v2_final_rules"]
    ] + ["task2_final_rules"]
    if (
        not exact_keys(answers, old_keys)
        or not isinstance(answers["task2_attempts"], list)
        or len(answers["task2_attempts"]) > 500
    ):
        raise ValueError("Invalid older submission structure")
    upgraded = copy.deepcopy(answers)
    for attempt in upgraded["task2_attempts"]:
        if not exact_keys(attempt, ["attempt_id", "rules", "missing_policy", "counts", "metrics"]):
            raise ValueError("Invalid older attempt structure")
        result = score_rules(packet, attempt["rules"], attempt["missing_policy"])
        old_metrics = {name: result["metrics"][name] for name in ["purity", "completeness"]}
        if not same_numbers(attempt["counts"], result["counts"]) or not same_numbers(
            attempt["metrics"], old_metrics
        ):
            raise ValueError("Older counts or scores do not reproduce")
        attempt["metrics"] = result["metrics"]
    upgraded["schema_version"] = "bubbletea_answers_v3"
    upgraded["imported_v2_final_rules"] = upgraded.pop("task2_final_rules")
    upgraded["task2_final_selection"] = {"attempt_id": "", "why_it_works": "", "how_to_improve": ""}
    return upgraded


def check_answers(answers, packet, packet_digest, key):
    top_keys = [
        "schema_version",
        "activity_version",
        "packet_sha256",
        "student_identifier",
        "task1_responses",
        "draft_rules",
        "draft_missing_policy",
        "task2_attempts",
        "task2_final_selection",
        "imported_v2_final_rules",
        "task3_membership_answer",
        "llm_disclosure",
    ]
    answers = upgrade_v2_answers(answers, packet, top_keys)
    if (
        not exact_keys(answers, top_keys)
        or answers["schema_version"] != "bubbletea_answers_v3"
        or answers["activity_version"] != packet["activity_version"]
        or answers["packet_sha256"] != packet_digest
    ):
        raise ValueError("Incompatible submission schema or catalog digest")
    if not check_text(answers["student_identifier"], 80) or not exact_keys(
        answers["task1_responses"], key["task1"]
    ):
        raise ValueError("Invalid student or Task 1 identifiers")
    task1_review = []
    for object_key, reference in key["task1"].items():
        response = answers["task1_responses"][object_key]
        if (
            not exact_keys(
                response,
                [
                    "source_id",
                    "classification",
                    "confidence",
                    "evidence_note",
                    "evidence_basis",
                    "citation",
                ],
            )
            or response["source_id"] != reference["source_id"]
        ):
            raise ValueError("Invalid exact Task 1 source identifier")
        if (
            response["classification"] not in ["", "ucd", "star", "qso", "uncertain"]
            or response["confidence"] not in ["", "low", "medium", "high"]
            or response["evidence_basis"]
            not in ["", "supplied_observations", "external_record", "both"]
        ):
            raise ValueError("Invalid response choice")
        if not check_text(response["evidence_note"], 6000) or not check_text(
            response["citation"], 2000
        ):
            raise ValueError("Invalid evidence text")
        task1_review.append(
            {
                "object_key": object_key,
                "source_id": reference["source_id"],
                "reference_class": reference["reference_class"],
                "student_class": response["classification"],
                "class_agrees": response["classification"] == reference["reference_class"],
                "manual_review_required": True,
                "reference_evidence": reference["evidence_audit"],
                "image_review": reference["image_review"],
                "confidence": response["confidence"],
                "evidence_note": response["evidence_note"],
                "citation": response["citation"],
                "external_citation_missing": response["evidence_basis"]
                in ["external_record", "both"]
                and not response["citation"].strip(),
            }
        )
    validate_rules(answers["draft_rules"])
    if answers["draft_missing_policy"] not in ["keep", "exclude"]:
        raise ValueError("Invalid draft missing-data policy")
    attempts = answers["task2_attempts"]
    if not isinstance(attempts, list) or len(attempts) > 500:
        raise ValueError("Invalid attempt history")
    identifiers, results = set(), []
    for attempt in attempts:
        if not exact_keys(attempt, ["attempt_id", "rules", "missing_policy", "counts", "metrics"]):
            raise ValueError("Invalid attempt structure")
        attempt_id = attempt["attempt_id"]
        if (
            not isinstance(attempt_id, str)
            or len(attempt_id) != 12
            or not attempt_id.startswith("attempt_")
            or not attempt_id[8:].isdigit()
            or attempt_id in identifiers
        ):
            raise ValueError("Invalid or duplicate attempt identifier")
        identifiers.add(attempt_id)
        result = score_rules(packet, attempt["rules"], attempt["missing_policy"])
        if not same_numbers(attempt["counts"], result["counts"]) or not same_numbers(
            attempt["metrics"], result["metrics"]
        ):
            raise ValueError(f"Tampered or stale scores for {attempt_id}")
        results.append({"attempt_id": attempt_id, **result})
    final = answers["task2_final_selection"]
    if (
        not exact_keys(final, ["attempt_id", "why_it_works", "how_to_improve"])
        or final["attempt_id"] not in identifiers | {""}
        or not check_text(final["why_it_works"], 6000)
        or not check_text(final["how_to_improve"], 6000)
    ):
        raise ValueError("Invalid final selection")
    previous = answers["imported_v2_final_rules"]
    if previous is not None and (
        not exact_keys(
            previous,
            [
                "recovery_attempt_id",
                "purity_attempt_id",
                "recovery_explanation",
                "purity_explanation",
            ],
        )
        or any(
            previous[f"{name}_attempt_id"] not in identifiers | {""}
            or not check_text(previous[f"{name}_explanation"], 6000)
            for name in ["recovery", "purity"]
        )
    ):
        raise ValueError("Invalid preserved version 2 choices")
    disclosure = answers["llm_disclosure"]
    if (
        not check_text(answers["task3_membership_answer"], 12000)
        or not exact_keys(disclosure, ["used", "contribution_and_verification"])
        or disclosure["used"] not in ["", "yes", "no"]
        or not check_text(disclosure["contribution_and_verification"], 6000)
    ):
        raise ValueError("Invalid membership answer or disclosure")
    return {
        "valid": True,
        "student_identifier": answers["student_identifier"],
        "task1_instructor_review": task1_review,
        "task2_recomputed": results,
        "final_selection": final,
        "preserved_version_2_choices": previous,
        "task3_membership_answer": answers["task3_membership_answer"],
        "llm_disclosure": disclosure,
        "grading_note": "No automatic final grade. Assess evidence, uncertainty, reasoning, and Task 3 manually.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.answers.stat().st_size > 5_000_000:
        parser.error("Submission exceeds 5 MB safety limit")
    content = teaching_part1_packet.read_bytes()
    report = check_answers(
        json.loads(args.answers.read_text()),
        json.loads(content),
        hashlib.sha256(content).hexdigest(),
        json.loads(teaching_part1_key.read_text()),
    )
    serialized = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        if args.output.resolve() == args.answers.resolve():
            parser.error("Do not overwrite the student's submission")
        args.output.write_text(serialized)
    else:
        sys.stdout.write(serialized)


if __name__ == "__main__":
    main()
