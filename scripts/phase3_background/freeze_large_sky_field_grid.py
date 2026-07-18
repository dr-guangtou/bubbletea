"""Freeze a count-blind, deterministic sky grid for background calibration."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GALAXY_SAMPLE_CSV,
    KOURKCHI_TULLY_2017_PROVENANCE,
    KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_FIELD_GRID_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256
from scripts.phase3_background.control_geometry import physical_radius_to_angle_deg
from scripts.phase3_background.radial_ring_area import (
    STERADIAN_TO_SQUARE_DEG,
    spherical_circle_area_steradian,
)

GRID_VERSION = "large_sky_field_grid_v1"
FIELD_COUNT_PER_HEMISPHERE = 250
MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG = 20.0
FIELD_RADIUS_DEG = 0.8
GALACTIC_LONGITUDE_BLOCK_WIDTH_DEG = 30.0
EQUAL_AREA_LATITUDE_BAND_COUNT = 5
BASE_VALIDATION_BLOCKS_PER_HEMISPHERE_LATITUDE_BAND = 2
HEMISPHERE_LATITUDE_BANDS_WITH_THIRD_VALIDATION_BLOCK = 5
GROUP_RADIUS_MULTIPLIER = 2.0
ECLIPTIC_LATITUDE_BAND_EDGES_DEG = (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0)
ACCEPTED_ASSOCIATION_STATE = "accepted_unique_spherical_5arcsec_v1"


def stable_hash_integer(value: str) -> int:
    """Return a stable integer derived from a text value."""
    return int(hashlib.sha256(value.encode()).hexdigest()[:16], 16)


def equal_area_latitude_edges_deg() -> list[float]:
    """Return latitude edges that divide each Galactic cap into equal sky areas."""
    minimum_sine = np.sin(np.deg2rad(MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG))
    fractions = np.linspace(0.0, 1.0, EQUAL_AREA_LATITUDE_BAND_COUNT + 1)
    sine_edges = minimum_sine + fractions * (1.0 - minimum_sine)
    return np.rad2deg(np.arcsin(sine_edges)).tolist()


def generate_field_centers(field_count_per_hemisphere: int) -> pd.DataFrame:
    """Generate deterministic centers uniform in area over both Galactic caps."""
    if field_count_per_hemisphere <= 0:
        raise ValueError("Field count per hemisphere must be positive")
    minimum_sine = np.sin(np.deg2rad(MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG))
    golden_angle_deg = 180.0 * (3.0 - np.sqrt(5.0))
    rows = []
    for latitude_sign, hemisphere, longitude_offset_deg in (
        (1, "north", 0.0),
        (-1, "south", golden_angle_deg / 2.0),
    ):
        for sequence_index in range(field_count_per_hemisphere):
            fraction = (sequence_index + 0.5) / field_count_per_hemisphere
            sine_absolute_latitude = minimum_sine + fraction * (1.0 - minimum_sine)
            absolute_latitude_deg = np.rad2deg(np.arcsin(sine_absolute_latitude))
            galactic_latitude_deg = latitude_sign * absolute_latitude_deg
            galactic_longitude_deg = (
                sequence_index * golden_angle_deg + longitude_offset_deg
            ) % 360.0
            rows.append(
                {
                    "hemisphere": hemisphere,
                    "hemisphere_sequence_index": sequence_index,
                    "galactic_longitude_deg": galactic_longitude_deg,
                    "galactic_latitude_deg": galactic_latitude_deg,
                }
            )
    fields = pd.DataFrame(rows)
    coordinates = SkyCoord(
        l=fields["galactic_longitude_deg"].to_numpy() * u.deg,
        b=fields["galactic_latitude_deg"].to_numpy() * u.deg,
        frame="galactic",
    )
    fields.insert(0, "field_id", [f"sky_field_{index:04d}" for index in range(len(fields))])
    fields["ra_deg"] = coordinates.icrs.ra.deg
    fields["dec_deg"] = coordinates.icrs.dec.deg
    fields["ecliptic_latitude_deg"] = coordinates.icrs.barycentrictrueecliptic.lat.deg
    fields["absolute_galactic_latitude_deg"] = fields["galactic_latitude_deg"].abs()
    fields["absolute_ecliptic_latitude_deg"] = fields["ecliptic_latitude_deg"].abs()
    fields["field_radius_deg"] = FIELD_RADIUS_DEG
    fields["requested_area_square_deg"] = (
        spherical_circle_area_steradian(FIELD_RADIUS_DEG) * STERADIAN_TO_SQUARE_DEG
    )
    return fields


def add_sky_blocks_and_partition(fields: pd.DataFrame) -> pd.DataFrame:
    """Assign broad sky blocks and keep each block in one partition."""
    output = fields.copy()
    minimum_sine = np.sin(np.deg2rad(MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG))
    sine_absolute_latitude = np.sin(np.deg2rad(output["absolute_galactic_latitude_deg"]))
    equal_area_fraction = (sine_absolute_latitude - minimum_sine) / (1.0 - minimum_sine)
    output["equal_area_latitude_band_index"] = np.minimum(
        np.floor(equal_area_fraction * EQUAL_AREA_LATITUDE_BAND_COUNT).astype(int),
        EQUAL_AREA_LATITUDE_BAND_COUNT - 1,
    )
    output["galactic_longitude_block_index"] = np.floor(
        output["galactic_longitude_deg"] / GALACTIC_LONGITUDE_BLOCK_WIDTH_DEG
    ).astype(int)
    output["sky_block_id"] = (
        output["hemisphere"]
        + ":latitude_band_"
        + output["equal_area_latitude_band_index"].astype(str)
        + ":longitude_band_"
        + output["galactic_longitude_block_index"].map(lambda value: f"{value:02d}")
    )
    blocks = output[
        ["sky_block_id", "hemisphere", "equal_area_latitude_band_index"]
    ].drop_duplicates()
    blocks["hemisphere_latitude_band_id"] = (
        blocks["hemisphere"] + ":" + blocks["equal_area_latitude_band_index"].astype(str)
    )
    blocks["block_hash"] = blocks["sky_block_id"].map(
        lambda value: stable_hash_integer(f"{GRID_VERSION}:block:{value}")
    )
    hemisphere_latitude_band_ids = blocks["hemisphere_latitude_band_id"].unique()
    extra_block_band_ids = set(
        sorted(
            hemisphere_latitude_band_ids,
            key=lambda value: stable_hash_integer(f"{GRID_VERSION}:stratum:{value}"),
        )[:HEMISPHERE_LATITUDE_BANDS_WITH_THIRD_VALIDATION_BLOCK]
    )
    validation_block_ids = set()
    for band_id, band_blocks in blocks.groupby("hemisphere_latitude_band_id"):
        validation_block_count = BASE_VALIDATION_BLOCKS_PER_HEMISPHERE_LATITUDE_BAND
        if band_id in extra_block_band_ids:
            validation_block_count += 1
        validation_block_ids.update(
            band_blocks.nsmallest(validation_block_count, "block_hash")["sky_block_id"]
        )
    output["experiment_partition"] = np.where(
        output["sky_block_id"].isin(validation_block_ids),
        "validation",
        "development",
    )
    output["partition_reason"] = "stable_hash_of_count_blind_sky_block"
    ecliptic_labels = [
        f"{int(lower):02d}_to_{int(upper):02d}_deg"
        for lower, upper in zip(
            ECLIPTIC_LATITUDE_BAND_EDGES_DEG[:-1],
            ECLIPTIC_LATITUDE_BAND_EDGES_DEG[1:],
            strict=True,
        )
    ]
    output["absolute_ecliptic_latitude_band"] = pd.cut(
        output["absolute_ecliptic_latitude_deg"],
        bins=ECLIPTIC_LATITUDE_BAND_EDGES_DEG,
        labels=ecliptic_labels,
        include_lowest=True,
        right=False,
    ).astype(str)
    return output


def catalog_circles(
    environments: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return represented group and association circles for sensitivity flags."""
    accepted = environments.loc[
        environments["association_state"].eq(ACCEPTED_ASSOCIATION_STATE)
    ].copy()
    groups = accepted.sort_values("rank").drop_duplicates("group_principal_pgc").copy()
    groups["screening_radius_deg"] = groups.apply(
        lambda row: physical_radius_to_angle_deg(
            float(row["catalog_distance_mpc"]),
            1000.0 * GROUP_RADIUS_MULTIPLIER * float(row["group_second_turnaround_radius_mpc"]),
        ),
        axis=1,
    )
    association_columns = [
        "association_principal_pgc",
        "association_principal_ra_deg",
        "association_principal_dec_deg",
        "association_first_turnaround_radius_mpc",
        "association_distance_mpc",
    ]
    associations = (
        accepted.dropna(subset=association_columns)
        .sort_values("rank")
        .drop_duplicates("association_principal_pgc")
        .copy()
    )
    associations["screening_radius_deg"] = associations.apply(
        lambda row: physical_radius_to_angle_deg(
            float(row["association_distance_mpc"]),
            1000.0 * float(row["association_first_turnaround_radius_mpc"]),
        ),
        axis=1,
    )
    return groups, associations


def circle_intersections(
    field_coordinates: SkyCoord,
    catalog: pd.DataFrame,
    ra_column: str,
    dec_column: str,
    identifier_column: str,
) -> tuple[list[int], list[str]]:
    """Return counts and identifiers of catalog circles intersecting each field."""
    catalog_coordinates = SkyCoord(
        catalog[ra_column].to_numpy() * u.deg,
        catalog[dec_column].to_numpy() * u.deg,
    )
    catalog_radii = catalog["screening_radius_deg"].to_numpy()
    identifiers = catalog[identifier_column].astype(int).astype(str).to_numpy()
    counts = []
    joined_identifiers = []
    for field_coordinate in field_coordinates:
        intersects = field_coordinate.separation(catalog_coordinates).deg < (
            catalog_radii + FIELD_RADIUS_DEG
        )
        counts.append(int(intersects.sum()))
        joined_identifiers.append(";".join(identifiers[intersects]))
    return counts, joined_identifiers


def add_environment_flags(
    fields: pd.DataFrame,
    environments: pd.DataFrame,
    hosts: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Record known-environment intersections without removing fields."""
    output = fields.copy()
    field_coordinates = SkyCoord(
        output["ra_deg"].to_numpy() * u.deg,
        output["dec_deg"].to_numpy() * u.deg,
    )
    groups, associations = catalog_circles(environments)
    group_counts, group_ids = circle_intersections(
        field_coordinates,
        groups,
        "group_principal_ra_deg",
        "group_principal_dec_deg",
        "group_principal_pgc",
    )
    association_counts, association_ids = circle_intersections(
        field_coordinates,
        associations,
        "association_principal_ra_deg",
        "association_principal_dec_deg",
        "association_principal_pgc",
    )
    host_coordinates = SkyCoord(hosts["ra"].to_numpy() * u.deg, hosts["dec"].to_numpy() * u.deg)
    host_ranks = hosts["rank"].astype(int).astype(str).to_numpy()
    nearest_host_index, nearest_host_separation, _ = field_coordinates.match_to_catalog_sky(
        host_coordinates
    )
    inside_host_counts = []
    inside_host_ids = []
    for field_coordinate in field_coordinates:
        inside = field_coordinate.separation(host_coordinates).deg < FIELD_RADIUS_DEG
        inside_host_counts.append(int(inside.sum()))
        inside_host_ids.append(";".join(host_ranks[inside]))
    output["represented_group_circle_intersection_count"] = group_counts
    output["represented_group_principal_pgc"] = group_ids
    output["represented_association_circle_intersection_count"] = association_counts
    output["represented_association_principal_pgc"] = association_ids
    output["project_host_center_inside_field_count"] = inside_host_counts
    output["project_host_ranks_inside_field"] = inside_host_ids
    output["nearest_project_host_rank"] = hosts.iloc[nearest_host_index]["rank"].to_numpy()
    output["nearest_project_host_center_separation_deg"] = nearest_host_separation.deg
    output["environment_flag_state"] = np.where(
        output[
            [
                "represented_group_circle_intersection_count",
                "represented_association_circle_intersection_count",
                "project_host_center_inside_field_count",
            ]
        ]
        .gt(0)
        .any(axis=1),
        "one_or_more_count_blind_environment_flags",
        "no_represented_environment_intersection",
    )
    return output, {
        "represented_group_count": len(groups),
        "represented_association_count": len(associations),
    }


def minimum_distinct_field_separation_deg(fields: pd.DataFrame) -> float:
    """Return the minimum center separation among distinct fields."""
    coordinates = SkyCoord(
        fields["ra_deg"].to_numpy() * u.deg,
        fields["dec_deg"].to_numpy() * u.deg,
    )
    separation_matrix_deg = coordinates[:, None].separation(coordinates).deg
    np.fill_diagonal(separation_matrix_deg, np.inf)
    return float(separation_matrix_deg.min())


def minimum_cross_partition_separation_deg(fields: pd.DataFrame) -> float:
    """Return the minimum development-to-validation center separation."""
    development = fields.loc[fields["experiment_partition"].eq("development")]
    validation = fields.loc[fields["experiment_partition"].eq("validation")]
    development_coordinates = SkyCoord(
        development["ra_deg"].to_numpy() * u.deg,
        development["dec_deg"].to_numpy() * u.deg,
    )
    validation_coordinates = SkyCoord(
        validation["ra_deg"].to_numpy() * u.deg,
        validation["dec_deg"].to_numpy() * u.deg,
    )
    return float(development_coordinates[:, None].separation(validation_coordinates).deg.min())


def design_identifier(input_hashes: dict[str, str]) -> str:
    """Return a stable identifier for the grid contract and source files."""
    contract = {
        "grid_version": GRID_VERSION,
        "field_count_per_hemisphere": FIELD_COUNT_PER_HEMISPHERE,
        "minimum_absolute_galactic_latitude_deg": MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG,
        "field_radius_deg": FIELD_RADIUS_DEG,
        "galactic_longitude_block_width_deg": GALACTIC_LONGITUDE_BLOCK_WIDTH_DEG,
        "equal_area_latitude_band_count": EQUAL_AREA_LATITUDE_BAND_COUNT,
        "base_validation_blocks_per_hemisphere_latitude_band": (
            BASE_VALIDATION_BLOCKS_PER_HEMISPHERE_LATITUDE_BAND
        ),
        "hemisphere_latitude_bands_with_third_validation_block": (
            HEMISPHERE_LATITUDE_BANDS_WITH_THIRD_VALIDATION_BLOCK
        ),
        "input_hashes": input_hashes,
    }
    encoded = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    return f"sky_grid_{hashlib.sha256(encoded).hexdigest()[:20]}"


def main() -> None:
    """Write and validate the fixed 500-field count-blind sky grid."""
    input_paths = (
        GALAXY_SAMPLE_CSV,
        KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES,
        KOURKCHI_TULLY_2017_PROVENANCE,
    )
    input_hashes = {str(path.relative_to(PROJECT_ROOT)): file_sha256(path) for path in input_paths}
    hosts = pd.read_csv(GALAXY_SAMPLE_CSV)
    environments = pd.read_csv(KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES)
    fields = generate_field_centers(FIELD_COUNT_PER_HEMISPHERE)
    fields = add_sky_blocks_and_partition(fields)
    fields, catalog_counts = add_environment_flags(fields, environments, hosts)
    fields.insert(0, "grid_id", design_identifier(input_hashes))
    fields["eligible_for_scientific_background"] = False
    fields["field_use"] = "large_sky_calibration_diagnostic_only"

    minimum_separation_deg = minimum_distinct_field_separation_deg(fields)
    minimum_cross_separation_deg = minimum_cross_partition_separation_deg(fields)
    block_partition_counts = fields.groupby("sky_block_id")["experiment_partition"].nunique()
    partition_hemisphere = fields.groupby(["experiment_partition", "hemisphere"]).size()
    partition_latitude_band = fields.groupby(
        ["experiment_partition", "equal_area_latitude_band_index"]
    ).size()
    partition_ecliptic_band = fields.groupby(
        ["experiment_partition", "absolute_ecliptic_latitude_band"]
    ).size()
    validation_block_count = fields.loc[
        fields["experiment_partition"].eq("validation"), "sky_block_id"
    ].nunique()
    forbidden_columns = {
        "source_count_in_frozen_magnitude_domain",
        "source_density_per_square_deg",
        "selected_source_count",
        "selected_source_density_per_square_deg",
        "point_source_logistic_probability",
        "point_source_logistic_selected",
    }
    checks = {
        "five_hundred_fields": len(fields) == 500,
        "two_hundred_fifty_fields_per_hemisphere": fields.groupby("hemisphere")
        .size()
        .eq(FIELD_COUNT_PER_HEMISPHERE)
        .all(),
        "field_identifiers_unique": fields["field_id"].is_unique,
        "all_fields_in_declared_latitude_domain": fields["absolute_galactic_latitude_deg"]
        .ge(MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG)
        .all(),
        "all_fields_have_exact_spherical_area": fields["requested_area_square_deg"]
        .eq(spherical_circle_area_steradian(FIELD_RADIUS_DEG) * STERADIAN_TO_SQUARE_DEG)
        .all(),
        "development_and_validation_both_nonempty": set(fields["experiment_partition"])
        == {"development", "validation"},
        "every_sky_block_stays_in_one_partition": block_partition_counts.eq(1).all(),
        "twenty_five_balanced_validation_sky_blocks": validation_block_count == 25,
        "both_partitions_cover_both_hemispheres": partition_hemisphere.index.nlevels == 2
        and len(partition_hemisphere) == 4,
        "both_partitions_cover_all_equal_area_latitude_bands": len(partition_latitude_band)
        == 2 * EQUAL_AREA_LATITUDE_BAND_COUNT,
        "both_partitions_cover_all_ecliptic_latitude_bands": len(partition_ecliptic_band)
        == 2 * (len(ECLIPTIC_LATITUDE_BAND_EDGES_DEG) - 1),
        "field_circles_do_not_overlap": minimum_separation_deg > 2 * FIELD_RADIUS_DEG,
        "cross_partition_field_circles_do_not_overlap": minimum_cross_separation_deg
        > 2 * FIELD_RADIUS_DEG,
        "environment_intersections_are_flags_not_exclusions": len(fields) == 500
        and (~fields["eligible_for_scientific_background"].astype(bool)).all(),
        "no_gaia_count_or_selector_columns_used": forbidden_columns.isdisjoint(fields.columns)
        and forbidden_columns.isdisjoint(hosts.columns)
        and forbidden_columns.isdisjoint(environments.columns),
        "input_host_and_environment_rows_preserved": len(hosts) == 2155
        and len(environments) == 2155,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    LARGE_SKY_FIELD_GRID.parent.mkdir(parents=True, exist_ok=True)
    fields.to_csv(LARGE_SKY_FIELD_GRID, index=False)
    partition_counts = fields["experiment_partition"].value_counts().sort_index().to_dict()
    environment_flag_counts = fields["environment_flag_state"].value_counts().to_dict()
    manifest = {
        "grid_version": GRID_VERSION,
        "grid_id": fields.iloc[0]["grid_id"],
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "count_blind_field_identities_and_partition_frozen",
        "plain_language_definition": {
            "fixed_sky_grid": (
                "A reproducible set of sky positions used to measure how the frozen selector "
                "behaves away from target-centered measurements."
            ),
            "sky_block": (
                "A broad fixed part of the sky used only to keep nearby grid fields on the "
                "same side of development and validation."
            ),
            "development": "fields allowed for measuring and choosing the large-sky model",
            "validation": "fields held back until the large-sky model is fixed",
            "environment_flag": (
                "A warning that a field overlaps a represented catalog group, association, "
                "or project-host center; it is not an automatic deletion or a settled halo "
                "boundary."
            ),
        },
        "selection_contract": (
            "deterministic_spherical_geometry_and_catalog_environment_flags_only_no_gaia_counts"
        ),
        "inputs": [{"path": path, "sha256": sha256} for path, sha256 in input_hashes.items()],
        "field_generation": {
            "field_count": len(fields),
            "field_count_per_hemisphere": FIELD_COUNT_PER_HEMISPHERE,
            "minimum_absolute_galactic_latitude_deg": (MINIMUM_ABSOLUTE_GALACTIC_LATITUDE_DEG),
            "maximum_absolute_galactic_latitude_deg_measured": float(
                fields["absolute_galactic_latitude_deg"].max()
            ),
            "minimum_absolute_galactic_latitude_deg_measured": float(
                fields["absolute_galactic_latitude_deg"].min()
            ),
            "golden_angle_deg": 180.0 * (3.0 - np.sqrt(5.0)),
            "field_radius_deg": FIELD_RADIUS_DEG,
            "exact_spherical_field_area_square_deg": float(
                fields.iloc[0]["requested_area_square_deg"]
            ),
            "inherited_field_count_and_radius": True,
            "field_count_is_not_a_new_power_calculation": True,
        },
        "partition": {
            "galactic_longitude_block_width_deg": GALACTIC_LONGITUDE_BLOCK_WIDTH_DEG,
            "equal_area_latitude_band_edges_deg": equal_area_latitude_edges_deg(),
            "ecliptic_latitude_diagnostic_band_edges_deg": list(ECLIPTIC_LATITUDE_BAND_EDGES_DEG),
            "base_validation_blocks_per_hemisphere_latitude_band": (
                BASE_VALIDATION_BLOCKS_PER_HEMISPHERE_LATITUDE_BAND
            ),
            "hemisphere_latitude_bands_with_third_validation_block": (
                HEMISPHERE_LATITUDE_BANDS_WITH_THIRD_VALIDATION_BLOCK
            ),
            "field_counts": partition_counts,
            "sky_block_counts": fields.groupby("experiment_partition")["sky_block_id"]
            .nunique()
            .sort_index()
            .to_dict(),
            "validation_selector_results_must_remain_unopened": True,
        },
        "spatial_separation": {
            "minimum_distinct_field_center_separation_deg": minimum_separation_deg,
            "minimum_development_to_validation_center_separation_deg": (
                minimum_cross_separation_deg
            ),
            "required_non_overlap_center_separation_deg": 2 * FIELD_RADIUS_DEG,
        },
        "environment_sensitivity_flags": {
            **catalog_counts,
            "group_radius": "two_times_catalog_second_turnaround_radius",
            "association_radius": "one_catalog_first_turnaround_radius",
            "universal_halo_exclusion_approved": False,
            "field_counts": environment_flag_counts,
            "fields_intersecting_represented_group_circle": int(
                fields["represented_group_circle_intersection_count"].gt(0).sum()
            ),
            "fields_intersecting_represented_association_circle": int(
                fields["represented_association_circle_intersection_count"].gt(0).sum()
            ),
            "fields_containing_project_host_center": int(
                fields["project_host_center_inside_field_count"].gt(0).sum()
            ),
            "flags_are_sensitivity_labels_not_field_rejections": True,
        },
        "scientific_background_approval": False,
        "output": {
            "path": str(LARGE_SKY_FIELD_GRID.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(LARGE_SKY_FIELD_GRID),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_FIELD_GRID_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Large sky-field grid validation failed: {checks}")


if __name__ == "__main__":
    main()
