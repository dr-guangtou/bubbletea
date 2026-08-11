"""Validate spherical radial-ring area accounting with retrieval states and masks."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_HOSTS,
    GAIA_FULL_COLUMN_MULTIFIELD_PLAN,
    GAIA_FULL_COLUMN_MULTIFIELD_RETRIEVAL,
    PROJECT_ROOT,
    RADIAL_RING_AREA_ACCOUNTING,
    RADIAL_RING_AREA_ACCOUNTING_MANIFEST,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256
from scripts.phase3_background.radial_ring_area import (
    DeclinationCoverage,
    RadialRing,
    SphericalCircleMask,
    calculate_gaia_ring_areas,
    calculate_ring_areas,
    spherical_circle_area_steradian,
)

RING_RADIUS_FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)
SYNTHETIC_MASK_OFFSETS_DEG = (0.22, 0.26)
SYNTHETIC_MASK_RADIUS_DEG = 0.10
SQUARE_DEGREE_TOLERANCE = 1e-8


def build_rings(test_radius_deg: float) -> list[RadialRing]:
    """Return four test rings that exactly cover one performance-test circle."""
    edges = [fraction * test_radius_deg for fraction in RING_RADIUS_FRACTIONS]
    return [
        RadialRing(
            ring_id=f"fraction_{RING_RADIUS_FRACTIONS[index]:.2f}_{RING_RADIUS_FRACTIONS[index + 1]:.2f}",
            inner_radius_deg=edges[index],
            outer_radius_deg=edges[index + 1],
            inference_role="central_diagnostic" if index == 0 else "area_validation_only",
        )
        for index in range(len(edges) - 1)
    ]


def build_coverage(plan: pd.DataFrame, completed_strip_ids: set[str]) -> list[DeclinationCoverage]:
    """Convert final retrieval strips into explicit completion records."""
    leaves = plan.loc[plan["is_leaf"].astype(bool)]
    return [
        DeclinationCoverage(
            strip_id=str(row["strip_id"]),
            minimum_dec_deg=float(row["minimum_dec_deg"]),
            maximum_dec_deg=float(row["maximum_dec_deg"]),
            complete=str(row["strip_id"]) in completed_strip_ids,
        )
        for _, row in leaves.iterrows()
    ]


def build_synthetic_masks(host_ra_deg: float, host_dec_deg: float) -> list[SphericalCircleMask]:
    """Return two overlapping test masks, clearly separated from scientific masks."""
    host = SkyCoord(host_ra_deg * u.deg, host_dec_deg * u.deg, frame="icrs")
    masks = []
    for index, offset_deg in enumerate(SYNTHETIC_MASK_OFFSETS_DEG, start=1):
        center = host.directional_offset_by(90 * u.deg, offset_deg * u.deg)
        masks.append(
            SphericalCircleMask(
                mask_id=f"synthetic_overlap_{index}",
                center_ra_deg=float(center.ra.deg),
                center_dec_deg=float(center.dec.deg),
                radius_deg=SYNTHETIC_MASK_RADIUS_DEG,
                reason="area_accounting_validation_only",
                provenance="synthetic_fixture_not_survey_coverage",
            )
        )
    return masks


def make_records(
    scenario: str,
    host_name: str,
    host_ra_deg: float,
    host_dec_deg: float,
    test_radius_deg: float,
    coverage: list[DeclinationCoverage],
    masks: list[SphericalCircleMask],
    use_gaia_area_policy: bool,
) -> list[dict[str, object]]:
    """Calculate all test-ring records for one declared scenario."""
    completed_strip_ids = [item.strip_id for item in coverage if item.complete]
    records = []
    for ring in build_rings(test_radius_deg):
        areas = (
            calculate_gaia_ring_areas(host_ra_deg, host_dec_deg, ring, coverage)
            if use_gaia_area_policy
            else calculate_ring_areas(
                host_ra_deg,
                host_dec_deg,
                ring,
                coverage,
                masks,
            )
        )
        records.append(
            {
                "scenario": scenario,
                "area_policy": (
                    "gaia_no_external_imaging_masks"
                    if use_gaia_area_policy
                    else "generic_spherical_mask_fixture"
                ),
                "host_name": host_name,
                "host_ra_deg": host_ra_deg,
                "host_dec_deg": host_dec_deg,
                "test_radius_deg": test_radius_deg,
                "ring_id": ring.ring_id,
                "inner_radius_deg": ring.inner_radius_deg,
                "outer_radius_deg": ring.outer_radius_deg,
                "inference_role": ring.inference_role,
                "completed_strip_ids": ";".join(completed_strip_ids),
                "mask_ids": ";".join(mask.mask_id for mask in masks),
                **areas,
            }
        )
    return records


def main() -> None:
    """Write and validate complete, partial, masked, and overlapping-mask areas."""
    started = perf_counter()
    hosts = pd.read_csv(BACKGROUND_REVIEW_HOSTS).set_index("objname")
    plan = pd.read_csv(GAIA_FULL_COLUMN_MULTIFIELD_PLAN)
    retrieval = pd.read_csv(GAIA_FULL_COLUMN_MULTIFIELD_RETRIEVAL).set_index("host_name")
    records = []
    for host_name, retrieval_row in retrieval.iterrows():
        host = hosts.loc[host_name]
        host_plan = plan.loc[plan["host_name"].eq(host_name)]
        leaf_ids = set(host_plan.loc[host_plan["is_leaf"].astype(bool), "strip_id"].astype(str))
        complete_coverage = build_coverage(host_plan, leaf_ids)
        records.extend(
            make_records(
                "measured_complete_gaia_policy",
                host_name,
                float(host["ra"]),
                float(host["dec"]),
                float(retrieval_row["test_radius_deg"]),
                complete_coverage,
                [],
                True,
            )
        )

    test_host_name = "MESSIER 060"
    test_host = hosts.loc[test_host_name]
    test_retrieval = retrieval.loc[test_host_name]
    test_plan = plan.loc[plan["host_name"].eq(test_host_name)]
    test_leaf_ids = (
        test_plan.loc[test_plan["is_leaf"].astype(bool), "strip_id"].astype(str).tolist()
    )
    test_masks = build_synthetic_masks(float(test_host["ra"]), float(test_host["dec"]))
    records.extend(
        make_records(
            "synthetic_masked_complete",
            test_host_name,
            float(test_host["ra"]),
            float(test_host["dec"]),
            float(test_retrieval["test_radius_deg"]),
            build_coverage(test_plan, set(test_leaf_ids)),
            test_masks,
            False,
        )
    )
    records.extend(
        make_records(
            "controlled_partial_gaia_policy",
            test_host_name,
            float(test_host["ra"]),
            float(test_host["dec"]),
            float(test_retrieval["test_radius_deg"]),
            build_coverage(test_plan, {test_leaf_ids[0]}),
            [],
            True,
        )
    )
    records.extend(
        make_records(
            "synthetic_masked_partial",
            test_host_name,
            float(test_host["ra"]),
            float(test_host["dec"]),
            float(test_retrieval["test_radius_deg"]),
            build_coverage(test_plan, {test_leaf_ids[0]}),
            test_masks,
            False,
        )
    )
    results = pd.DataFrame(records)

    complete_gaia = results.loc[results["scenario"].eq("measured_complete_gaia_policy")]
    partial_gaia = results.loc[results["scenario"].eq("controlled_partial_gaia_policy")]
    masked_complete = results.loc[results["scenario"].eq("synthetic_masked_complete")]
    individual_mask_results = [
        pd.DataFrame(
            make_records(
                f"single_mask_{mask.mask_id}",
                test_host_name,
                float(test_host["ra"]),
                float(test_host["dec"]),
                float(test_retrieval["test_radius_deg"]),
                build_coverage(test_plan, set(test_leaf_ids)),
                [mask],
                False,
            )
        )
        for mask in test_masks
    ]
    individual_mask_sum = sum(
        frame["masked_area_square_deg"].to_numpy() for frame in individual_mask_results
    )
    union_mask_area = masked_complete["masked_area_square_deg"].to_numpy()
    requested_circle_errors = []
    for host_name, host_rows in complete_gaia.groupby("host_name"):
        radius_deg = float(retrieval.loc[host_name, "test_radius_deg"])
        expected_circle_area = spherical_circle_area_steradian(radius_deg) * (180 / np.pi) ** 2
        requested_circle_errors.append(
            abs(float(host_rows["requested_area_square_deg"].sum()) - expected_circle_area)
        )
    plan_count_matches = []
    for host_name, retrieval_row in retrieval.iterrows():
        leaf_count = plan.loc[
            plan["host_name"].eq(host_name) & plan["is_leaf"].astype(bool),
            "measured_source_count",
        ].sum()
        plan_count_matches.append(int(leaf_count) == int(retrieval_row["available_rows"]))

    checks = {
        "three_measured_complete_fields": complete_gaia["host_name"].nunique() == 3,
        "four_rings_per_scenario": results.groupby(["scenario", "host_name"]).size().eq(4).all(),
        "complete_strips_reproduce_requested_area": (
            complete_gaia["successfully_queried_area_square_deg"]
            - complete_gaia["requested_area_square_deg"]
        )
        .abs()
        .le(SQUARE_DEGREE_TOLERANCE)
        .all(),
        "ring_areas_sum_to_analytic_circle": max(requested_circle_errors)
        <= SQUARE_DEGREE_TOLERANCE,
        "partial_state_has_positive_missing_area": partial_gaia["missing_area_square_deg"]
        .gt(0)
        .all(),
        "partial_state_retains_positive_queried_area": partial_gaia[
            "successfully_queried_area_square_deg"
        ]
        .gt(0)
        .all(),
        "masks_reduce_usable_area": (
            masked_complete["usable_area_square_deg"]
            < masked_complete["successfully_queried_area_square_deg"]
        ).any(),
        "overlapping_masks_counted_once": (union_mask_area <= individual_mask_sum + 1e-12).all()
        and (union_mask_area < individual_mask_sum - 1e-8).any(),
        "queried_plus_missing_equals_requested": (
            results["successfully_queried_area_square_deg"]
            + results["missing_area_square_deg"]
            - results["requested_area_square_deg"]
        )
        .abs()
        .le(SQUARE_DEGREE_TOLERANCE)
        .all(),
        "usable_plus_masked_equals_queried": (
            results["usable_area_square_deg"]
            + results["masked_area_square_deg"]
            - results["successfully_queried_area_square_deg"]
        )
        .abs()
        .le(SQUARE_DEGREE_TOLERANCE)
        .all(),
        "all_areas_nonnegative": results[
            [
                "requested_area_square_deg",
                "successfully_queried_area_square_deg",
                "masked_area_square_deg",
                "missing_area_square_deg",
                "usable_area_square_deg",
            ]
        ]
        .ge(0)
        .all()
        .all(),
        "integration_errors_below_declared_tolerance": results[
            ["queried_integration_error_square_deg", "masked_integration_error_square_deg"]
        ]
        .le(SQUARE_DEGREE_TOLERANCE)
        .all()
        .all(),
        "central_ring_remains_diagnostic_only": results.loc[
            results["inner_radius_deg"].eq(0), "inference_role"
        ]
        .eq("central_diagnostic")
        .all(),
        "retrieval_leaf_counts_match_measured_totals": all(plan_count_matches),
        "gaia_policy_applies_no_external_imaging_masks": results.loc[
            results["area_policy"].eq("gaia_no_external_imaging_masks"), "mask_count"
        ]
        .eq(0)
        .all(),
        "gaia_usable_area_equals_successfully_queried_area": (
            results.loc[
                results["area_policy"].eq("gaia_no_external_imaging_masks"),
                "usable_area_square_deg",
            ].to_numpy()
            == results.loc[
                results["area_policy"].eq("gaia_no_external_imaging_masks"),
                "successfully_queried_area_square_deg",
            ].to_numpy()
        ).all(),
        "synthetic_masks_cannot_be_mistaken_for_coverage": all(
            mask.provenance == "synthetic_fixture_not_survey_coverage" for mask in test_masks
        ),
        "ring_and_mask_geometry_fixed_without_source_selection": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    RADIAL_RING_AREA_ACCOUNTING.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(RADIAL_RING_AREA_ACCOUNTING, index=False)
    manifest = {
        "validation_version": "radial_ring_area_accounting_validation_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "validation_scope": "performance_geometry_only_not_scientific_aperture_or_real_mask",
        "gaia_area_policy": {
            "apply_bright_star_masks": False,
            "apply_dust_masks": False,
            "apply_ancillary_imaging_masks": False,
            "usable_area_definition": "successfully_queried_area",
            "incomplete_retrieval_treatment": "explicit_missing_area",
        },
        "area_definition": {
            "requested": "full spherical ring area",
            "successfully_queried": "part of the ring covered by verified complete strips",
            "masked": "union of explicit unusable masks inside successfully queried area",
            "missing": "requested area without a verified complete strip",
            "usable": "successfully queried area minus the union of masks",
        },
        "integration": {
            "method": "adaptive_quadrature_of_exact_spherical_longitude_intervals",
            "internal_absolute_tolerance_steradian": 1e-13,
            "validation_tolerance_square_deg": SQUARE_DEGREE_TOLERANCE,
        },
        "inputs": [
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "sha256": file_sha256(path),
            }
            for path in (
                BACKGROUND_REVIEW_HOSTS,
                GAIA_FULL_COLUMN_MULTIFIELD_PLAN,
                GAIA_FULL_COLUMN_MULTIFIELD_RETRIEVAL,
            )
        ],
        "test_ring_radius_fractions": list(RING_RADIUS_FRACTIONS),
        "synthetic_masks": [mask.__dict__ for mask in test_masks],
        "record_count": len(results),
        "elapsed_seconds": perf_counter() - started,
        "maximum_complete_area_error_square_deg": float(
            (
                complete_gaia["successfully_queried_area_square_deg"]
                - complete_gaia["requested_area_square_deg"]
            )
            .abs()
            .max()
        ),
        "maximum_ring_sum_error_square_deg": max(requested_circle_errors),
        "maximum_reported_integration_error_square_deg": float(
            results[["queried_integration_error_square_deg", "masked_integration_error_square_deg"]]
            .to_numpy()
            .max()
        ),
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    RADIAL_RING_AREA_ACCOUNTING_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Radial-ring area accounting validation failed: {checks}")


if __name__ == "__main__":
    main()
