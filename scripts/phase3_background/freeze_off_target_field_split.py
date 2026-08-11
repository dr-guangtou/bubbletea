"""Freeze count-blind off-target development and validation field identities."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from itertools import product
from pathlib import Path

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_FIELD_POSITIONS,
    BACKGROUND_REVIEW_FIELD_POSITIONS_MANIFEST,
    OFF_TARGET_FIELD_SPLIT,
    OFF_TARGET_FIELD_SPLIT_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256
from scripts.phase3_background.benchmark_gaia_field_conditions import TEST_PATCH_RADIUS_DEG

DEVELOPMENT_REVIEW_CASES = (
    "highest_ranked_one_galaxy_catalog_case",
    "highest_ranked_group_main_galaxy",
)
VALIDATION_REVIEW_CASES = (
    "nearest_one_galaxy_catalog_case",
    "highest_ranked_group_member",
)
OFF_TARGET_FIELD_ROLES = ("west_test_patch", "east_test_patch")
SPLIT_VERSION = "off_target_field_split_v1"


def stable_split_identifier(input_sha256: str) -> str:
    """Return a stable identifier for the declared split contract and input."""
    contract = {
        "split_version": SPLIT_VERSION,
        "input_sha256": input_sha256,
        "development_review_cases": DEVELOPMENT_REVIEW_CASES,
        "validation_review_cases": VALIDATION_REVIEW_CASES,
        "off_target_field_roles": OFF_TARGET_FIELD_ROLES,
    }
    encoded = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    return f"split_{hashlib.sha256(encoded).hexdigest()[:20]}"


def minimum_cross_partition_separation_deg(fields: pd.DataFrame) -> float:
    """Return the smallest center separation between development and validation fields."""
    development = fields.loc[fields["experiment_partition"].eq("development")]
    validation = fields.loc[fields["experiment_partition"].eq("validation")]
    separations = []
    for (_, first), (_, second) in product(development.iterrows(), validation.iterrows()):
        first_coordinate = SkyCoord(float(first["ra_deg"]) * u.deg, float(first["dec_deg"]) * u.deg)
        second_coordinate = SkyCoord(
            float(second["ra_deg"]) * u.deg, float(second["dec_deg"]) * u.deg
        )
        separations.append(float(first_coordinate.separation(second_coordinate).deg))
    return min(separations)


def main() -> None:
    """Write the frozen split and validate that selector information was not used."""
    positions = pd.read_csv(BACKGROUND_REVIEW_FIELD_POSITIONS)
    position_manifest = json.loads(
        BACKGROUND_REVIEW_FIELD_POSITIONS_MANIFEST.read_text(encoding="utf-8")
    )
    input_sha256 = file_sha256(BACKGROUND_REVIEW_FIELD_POSITIONS)
    split_id = stable_split_identifier(input_sha256)
    output = positions.copy()
    output.insert(0, "split_id", split_id)
    output.insert(1, "experiment_partition", "excluded")
    output.insert(2, "frozen_for_selector_experiment", False)
    output.insert(3, "partition_reason", "target_field_not_in_off_target_split")

    is_off_target = output["field_role"].isin(OFF_TARGET_FIELD_ROLES)
    is_development = output["review_case"].isin(DEVELOPMENT_REVIEW_CASES)
    is_validation = output["review_case"].isin(VALIDATION_REVIEW_CASES)
    output.loc[is_off_target & is_development, "experiment_partition"] = "development"
    output.loc[is_off_target & is_development, "frozen_for_selector_experiment"] = True
    output.loc[is_off_target & is_development, "partition_reason"] = (
        "predeclared_host_role_assigned_to_development"
    )
    output.loc[is_off_target & is_validation, "experiment_partition"] = "validation"
    output.loc[is_off_target & is_validation, "frozen_for_selector_experiment"] = True
    output.loc[is_off_target & is_validation, "partition_reason"] = (
        "predeclared_host_role_held_back_for_validation"
    )

    assigned = output.loc[output["frozen_for_selector_experiment"].astype(bool)].copy()
    host_partition_counts = assigned.groupby("host_rank")["experiment_partition"].nunique()
    partition_host_roles = (
        assigned[["experiment_partition", "host_rank", "catalog_environment_role"]]
        .drop_duplicates()
        .groupby("experiment_partition")["catalog_environment_role"]
        .apply(set)
    )
    latitude_signs = (
        assigned.assign(
            galactic_latitude_sign=assigned["galactic_latitude_deg"].map(
                lambda value: "positive" if value > 0 else "negative"
            )
        )
        .groupby("experiment_partition")["galactic_latitude_sign"]
        .apply(set)
    )
    minimum_cross_separation_deg = minimum_cross_partition_separation_deg(assigned)
    required_non_overlap_separation_deg = 2 * TEST_PATCH_RADIUS_DEG
    forbidden_count_columns = {
        "source_count_in_frozen_magnitude_domain",
        "source_density_per_square_deg",
        "selected_source_count",
        "point_source_logistic_selected",
    }
    checks = {
        "thirteen_input_positions_preserved": len(output) == 13,
        "eight_off_target_fields_assigned": len(assigned) == 8,
        "four_development_fields": assigned["experiment_partition"].eq("development").sum() == 4,
        "four_validation_fields": assigned["experiment_partition"].eq("validation").sum() == 4,
        "four_host_systems_assigned": assigned["host_rank"].nunique() == 4,
        "each_host_system_kept_in_one_partition": host_partition_counts.eq(1).all(),
        "each_host_system_keeps_east_and_west_fields": assigned.groupby("host_rank")["field_role"]
        .apply(set)
        .eq(set(OFF_TARGET_FIELD_ROLES))
        .all(),
        "each_partition_has_isolated_and_group_cases": all(
            any(role == "catalog_isolated_principal" for role in roles)
            and any(role in {"catalog_group_principal", "catalog_group_member"} for role in roles)
            for roles in partition_host_roles
        ),
        "each_partition_has_positive_and_negative_galactic_latitude": all(
            signs == {"positive", "negative"} for signs in latitude_signs
        ),
        "development_and_validation_circles_do_not_overlap": minimum_cross_separation_deg
        > required_non_overlap_separation_deg,
        "target_fields_excluded": output.loc[
            output["field_role"].eq("target_test_patch"), "experiment_partition"
        ]
        .eq("excluded")
        .all(),
        "no_field_promoted_to_scientific_background": (
            ~output["eligible_for_scientific_background"].astype(bool)
        ).all(),
        "no_gaia_or_selector_count_columns_used": forbidden_count_columns.isdisjoint(
            output.columns
        ),
        "input_positions_were_count_blind": position_manifest["selection_contract"]
        == "host_and_environment_geometry_only_no_gaia_counts",
    }
    checks = {name: bool(value) for name, value in checks.items()}
    OFF_TARGET_FIELD_SPLIT.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OFF_TARGET_FIELD_SPLIT, index=False)
    manifest = {
        "split_version": SPLIT_VERSION,
        "split_id": split_id,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "plain_language_definition": {
            "development": "fields allowed for choosing and tuning the background method",
            "validation": "fields held back until the method choices are fixed",
            "excluded": "target-centered fields that are not part of this off-target split",
        },
        "selection_contract": (
            "review_case_and_geometry_only_no_gaia_source_counts_no_selector_outputs"
        ),
        "input": {
            "path": str(BACKGROUND_REVIEW_FIELD_POSITIONS.relative_to(PROJECT_ROOT)),
            "sha256": input_sha256,
        },
        "assignment_rule": {
            "development_review_cases": list(DEVELOPMENT_REVIEW_CASES),
            "validation_review_cases": list(VALIDATION_REVIEW_CASES),
            "keep_east_and_west_from_one_host_together": True,
        },
        "field_count": len(output),
        "assigned_off_target_field_count": len(assigned),
        "development_field_count": int(assigned["experiment_partition"].eq("development").sum()),
        "validation_field_count": int(assigned["experiment_partition"].eq("validation").sum()),
        "excluded_target_field_count": int(output["experiment_partition"].eq("excluded").sum()),
        "minimum_development_to_validation_center_separation_deg": (minimum_cross_separation_deg),
        "test_patch_radius_deg": TEST_PATCH_RADIUS_DEG,
        "required_non_overlap_center_separation_deg": required_non_overlap_separation_deg,
        "scientific_background_approval_status": "none_approved_diagnostic_fields_only",
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    OFF_TARGET_FIELD_SPLIT_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Off-target field split validation failed: {checks}")


if __name__ == "__main__":
    main()
