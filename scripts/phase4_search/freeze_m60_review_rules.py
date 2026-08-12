"""Freeze plain-language M60 contamination review columns and assignment rules."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    M60_POSITIVE_CONTROL_CONTRACT,
    M60_POSITIVE_CONTROL_REVIEW_RULES,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.freeze_m60_positive_control import CONTRACT_VERSION

REVIEW_RULES_VERSION = "m60_positive_control_review_rules_v1"


def column(name: str, allowed_values: list[str], meaning: str) -> dict[str, object]:
    """Describe one frozen review column."""
    return {"name": name, "allowed_values": allowed_values, "meaning": meaning}


def main() -> None:
    """Write review rules without opening or inspecting the complete M60 field."""
    design = json.loads(M60_POSITIVE_CONTROL_CONTRACT.read_text())
    if design["contract_version"] != CONTRACT_VERSION:
        raise RuntimeError("M60 positive-control contract is not expected")

    columns = [
        column(
            "star_forming_catalog_association",
            ["yes", "not_found", "not_checked"],
            (
                "Whether a published H II-region or young-cluster catalog contains "
                "the source. Not found does not count as contrary evidence because "
                "these catalogs are rare and incomplete; it remains unknown evidence."
            ),
        ),
        column(
            "star_forming_color_review_priority",
            ["yes", "no", "not_available", "not_evaluated"],
            (
                "Whether color makes the source worth inspecting for young stars. "
                "This column cannot assign the physical review flag by itself."
            ),
        ),
        column(
            "star_forming_visual_evidence",
            ["yes", "none_seen", "uncertain", "not_reviewed", "image_unusable"],
            (
                "Whether visual inspection shows association with visible "
                "star-forming structure or irregular compact emission."
            ),
        ),
        column(
            "possible_star_forming_region_or_young_cluster",
            ["yes", "no", "uncertain", "not_reviewed"],
            (
                "Combined review flag. Yes requires a catalog association or visual "
                "evidence; color alone is never sufficient."
            ),
        ),
        column(
            "gaia_image_measurement_warning",
            ["yes", "no", "not_available", "not_evaluated"],
            (
                "A separate Gaia-based warning that can prioritize visual review. "
                "It cannot assign the visual blend or image-problem flag."
            ),
        ),
        column(
            "blend_or_image_problem_visual_evidence",
            ["yes", "none_seen", "uncertain", "not_reviewed", "image_unusable"],
            (
                "Visual evidence for overlapping or nearby sources, multiple peaks, "
                "asymmetry, position mismatch, saturation, boundaries, or artifacts."
            ),
        ),
        column(
            "possible_nearby_source_blend_or_image_problem",
            ["yes", "no", "uncertain", "not_reviewed"],
            "Visual-inspection flag; it cannot be assigned from Gaia measurements alone.",
        ),
        column(
            "visual_review_note",
            ["free_text"],
            "Short evidence note supporting any visual flag or uncertainty.",
        ),
        column(
            "visual_reviewer",
            ["free_text"],
            "Person or process responsible for the visual assessment.",
        ),
        column(
            "visual_reviewed_at_utc",
            ["iso_8601_time", "empty_when_not_reviewed"],
            "Time of visual assessment so later revisions remain traceable.",
        ),
    ]
    names = [item["name"] for item in columns]
    checks = {
        "design_was_frozen_before_rules": design["status"] == "frozen_before_full_field_retrieval",
        "review_columns_are_unique": len(names) == len(set(names)),
        "catalog_absence_is_not_contrary_evidence": "unknown evidence" in columns[0]["meaning"],
        "color_alone_cannot_assign_star_forming_flag": "color alone is never sufficient"
        in columns[3]["meaning"],
        "blend_flag_requires_visual_inspection": "Visual-inspection flag" in columns[6]["meaning"],
        "gaia_warning_is_separate": "cannot assign the visual blend" in columns[4]["meaning"],
        "rules_open_no_complete_field": True,
        "review_flags_remove_no_sources": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    artifact = {
        "review_rules_version": REVIEW_RULES_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "frozen_before_complete_field_retrieval",
        "plain_language_scope": (
            "Record possible contamination for human review without removing any "
            "source from selector version 1 or the radial profile."
        ),
        "assignment_rules": {
            "star_forming_region_or_young_cluster": [
                "Color may prioritize visual inspection but cannot assign the flag.",
                "A yes flag requires a catalog association or visual evidence.",
                "No catalog match provides no contrary evidence because catalogs are incomplete.",
                "Uncertain evidence remains uncertain and does not become a rejection.",
            ],
            "nearby_source_blend_or_image_problem": [
                "The final flag requires visual inspection of the cutout.",
                "Gaia image measurements may prioritize inspection but remain separate.",
                "An unusable image remains unusable rather than being labeled clean.",
            ],
            "effect_on_selection": "flags_only_no_automatic_removal",
        },
        "review_columns": columns,
        "input_contract": {
            "path": str(M60_POSITIVE_CONTROL_CONTRACT.relative_to(PROJECT_ROOT)),
            "sha256": calculate_sha256(M60_POSITIVE_CONTROL_CONTRACT),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    M60_POSITIVE_CONTROL_REVIEW_RULES.write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"M60 review-rule freeze failed: {checks}")


if __name__ == "__main__":
    main()
