"""Validate all confirmation_rules_v1 states with deterministic fixtures."""

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.phase1_literature.build_reference_database import derive_classification


def check_case(
    expected_state: str,
    evidence: list[dict[str, str]],
    identity_conflict: bool = False,
) -> None:
    """Assert one classification fixture."""
    actual_state, _ = derive_classification(evidence, identity_conflict=identity_conflict)
    if actual_state != expected_state:
        raise AssertionError(f"Expected {expected_state}, received {actual_state}")


def main() -> None:
    """Exercise confirmed, candidate, rejected, uncertain, and pending-review behavior."""
    check_case(
        "confirmed",
        [
            {
                "evidence_type": "spectroscopic_membership",
                "evidence_value": "positive",
                "review_status": "approved",
            }
        ],
    )
    check_case(
        "candidate",
        [
            {
                "evidence_type": "reported_classification",
                "evidence_value": "candidate",
                "review_status": "not_required",
            }
        ],
    )
    check_case(
        "candidate",
        [
            {
                "evidence_type": "spectroscopic_membership",
                "evidence_value": "positive_reported",
                "review_status": "pending",
            }
        ],
    )
    check_case(
        "rejected",
        [
            {
                "evidence_type": "reported_classification",
                "evidence_value": "not_ucd",
                "review_status": "not_required",
            }
        ],
    )
    check_case(
        "uncertain",
        [
            {
                "evidence_type": "spectroscopic_membership",
                "evidence_value": "positive",
                "review_status": "approved",
            },
            {
                "evidence_type": "reported_classification",
                "evidence_value": "not_ucd",
                "review_status": "not_required",
            },
        ],
    )
    check_case("uncertain", [], identity_conflict=True)


if __name__ == "__main__":
    main()
