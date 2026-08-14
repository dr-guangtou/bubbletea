"""Shared review model for the UCD visual review workbench."""

FOUR_STATE = ["not_reviewed", "yes", "no", "uncertain"]
IMAGE_USABILITY = ["not_reviewed", "usable", "partly_usable", "unusable"]
CONFIRMED_DECISIONS = ["not_reviewed", "include", "exclude", "hold"]
CANDIDATE_DECISIONS = ["not_reviewed", "prioritize", "standard", "deprioritize", "hold"]

OBSERVATIONS = [
    "resolved",
    "off_center",
    "close_to_host_light",
    "too_faint_to_judge",
    "blend_or_nearby_source",
    "image_artifact",
    "star_forming_or_young_cluster_appearance",
]

COORDINATE_PROPOSAL_RESPONSES = [
    "no_correction_needed",
    "no_correction_proposed",
    "source_selected",
    "manual_ra_dec",
]

CONFIRMED_COHORT = "confirmed_ucd"
CANDIDATE_COHORT = "saifollahi_high_probability_candidate"


def allowed_decisions(cohort: str) -> list[str]:
    """Return the cohort-specific final-decision values."""
    if cohort == CANDIDATE_COHORT:
        return CANDIDATE_DECISIONS
    return CONFIRMED_DECISIONS


def decision_requires_reason(cohort: str, decision: str) -> bool:
    """Return whether a final decision requires a non-empty reason."""
    if cohort == CANDIDATE_COHORT:
        return decision in {"deprioritize", "hold"}
    return decision in {"exclude", "hold"}


def validate_review(payload: dict, cohort: str) -> list[str]:
    """Return a list of structured validation errors for one review payload."""
    errors = []
    if payload.get("image_usability") not in IMAGE_USABILITY:
        errors.append("image_usability is not an allowed value")

    observations = payload.get("observations") or {}
    for name in OBSERVATIONS:
        if observations.get(name) not in FOUR_STATE:
            errors.append(f"observation {name} is not an allowed value")

    decision = payload.get("final_decision")
    if decision not in allowed_decisions(cohort):
        errors.append("final_decision is not allowed for this cohort")
    if cohort == CANDIDATE_COHORT and decision == "include":
        errors.append("a candidate cannot be included in the confirmed design reference")

    if decision_requires_reason(cohort, decision) and not str(
        payload.get("decision_reason") or ""
    ).strip():
        errors.append("decision_reason is required for this final decision")

    off_center = observations.get("off_center")
    proposal = payload.get("coordinate_proposal") or {}
    if off_center in {"yes", "uncertain"}:
        response = proposal.get("response")
        if response not in COORDINATE_PROPOSAL_RESPONSES or response == "no_correction_needed":
            errors.append(
                "a coordinate-proposal response is required when off_center is yes or uncertain"
            )
        elif response == "source_selected":
            if not proposal.get("gaia_source_id") and not proposal.get("legacy_source_id"):
                errors.append("source_selected requires a Gaia or Legacy source identifier")
        elif response == "manual_ra_dec":
            if proposal.get("proposed_ra") is None or proposal.get("proposed_dec") is None:
                errors.append("manual_ra_dec requires proposed_ra and proposed_dec")

    if payload.get("image_usability") == "unusable":
        if decision != "hold":
            errors.append("an unusable image requires final_decision hold")

    return errors


def review_complete(payload: dict, cohort: str) -> bool:
    """Return whether a review payload satisfies the completion rules."""
    if payload.get("image_usability") == "unusable":
        return payload.get("final_decision") == "hold" and bool(
            str(payload.get("decision_reason") or "").strip()
        )
    if payload.get("image_usability") not in {"usable", "partly_usable"}:
        return False
    observations = payload.get("observations") or {}
    if any(observations.get(name) == "not_reviewed" for name in OBSERVATIONS):
        return False
    if observations.get("off_center") in {"yes", "uncertain"}:
        proposal = payload.get("coordinate_proposal") or {}
        if proposal.get("response") not in COORDINATE_PROPOSAL_RESPONSES:
            return False
    if payload.get("final_decision") not in allowed_decisions(cohort):
        return False
    if decision_requires_reason(cohort, payload.get("final_decision")) and not str(
        payload.get("decision_reason") or ""
    ).strip():
        return False
    return True
