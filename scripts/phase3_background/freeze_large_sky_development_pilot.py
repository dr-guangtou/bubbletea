"""Freeze development fields for the large-sky retrieval benchmark and pilot."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_FIELD_GRID_MANIFEST,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256

PILOT_VERSION = "large_sky_development_pilot_fields_v1"


def stable_hash_integer(field_id: str) -> int:
    """Return the stable pilot-selection hash for one field identifier."""
    value = f"{PILOT_VERSION}:{field_id}"
    return int(hashlib.sha256(value.encode()).hexdigest()[:16], 16)


def select_pilot_fields(grid: pd.DataFrame) -> pd.DataFrame:
    """Select the benchmark and a count-blind position-coverage pilot."""
    development = grid.loc[grid["experiment_partition"].eq("development")].copy()
    development["hemisphere_latitude_band_id"] = (
        development["hemisphere"] + ":" + development["equal_area_latitude_band_index"].astype(str)
    )
    development["pilot_selection_hash"] = development["field_id"].map(stable_hash_integer)
    benchmark = development.sort_values(["absolute_galactic_latitude_deg", "field_id"]).iloc[0]
    benchmark_cell = str(benchmark["hemisphere_latitude_band_id"])
    selected_records = []
    for cell_id, cell_fields in development.groupby("hemisphere_latitude_band_id", sort=True):
        if cell_id == benchmark_cell:
            selected = benchmark.copy()
            selected["pilot_selection_reason"] = "benchmark_smallest_absolute_galactic_latitude"
        else:
            selected = cell_fields.nsmallest(1, "pilot_selection_hash").iloc[0].copy()
            selected["pilot_selection_reason"] = (
                "stable_hash_hemisphere_galactic_latitude_band_representative"
            )
        selected_records.append(selected)
    selected = pd.DataFrame(selected_records)
    represented_ecliptic_bands = set(selected["absolute_ecliptic_latitude_band"])
    all_ecliptic_bands = set(development["absolute_ecliptic_latitude_band"])
    for ecliptic_band in sorted(all_ecliptic_bands - represented_ecliptic_bands):
        supplement = (
            development.loc[development["absolute_ecliptic_latitude_band"].eq(ecliptic_band)]
            .nsmallest(1, "pilot_selection_hash")
            .iloc[0]
            .copy()
        )
        supplement["pilot_selection_reason"] = (
            "stable_hash_missing_ecliptic_latitude_band_supplement"
        )
        selected = pd.concat([selected, supplement.to_frame().T], ignore_index=True)
    selected["is_single_field_performance_benchmark"] = selected["field_id"].eq(
        benchmark["field_id"]
    )
    return selected.sort_values("field_id").reset_index(drop=True)


def pilot_identifier(grid_id: str, grid_sha256: str) -> str:
    """Return a stable identifier for the pilot-selection contract."""
    contract = {
        "pilot_version": PILOT_VERSION,
        "grid_id": grid_id,
        "grid_sha256": grid_sha256,
        "benchmark_rule": "minimum_absolute_galactic_latitude_then_field_id",
        "coverage_rule": (
            "one_per_hemisphere_latitude_band_then_missing_ecliptic_band_supplements"
        ),
    }
    encoded = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    return f"development_pilot_{hashlib.sha256(encoded).hexdigest()[:20]}"


def main() -> None:
    """Write the count-blind development pilot before any large-field query."""
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    grid_manifest = json.loads(LARGE_SKY_FIELD_GRID_MANIFEST.read_text(encoding="utf-8"))
    grid_sha256 = file_sha256(LARGE_SKY_FIELD_GRID)
    pilot = select_pilot_fields(grid)
    pilot.insert(0, "pilot_id", pilot_identifier(grid_manifest["grid_id"], grid_sha256))
    validation_ids = set(
        grid.loc[grid["experiment_partition"].eq("validation"), "field_id"].astype(str)
    )
    pilot_ids = set(pilot["field_id"].astype(str))
    expected_cells = set(
        grid.loc[grid["experiment_partition"].eq("development")].assign(
            cell=lambda frame: (
                frame["hemisphere"] + ":" + frame["equal_area_latitude_band_index"].astype(str)
            )
        )["cell"]
    )
    forbidden_columns = {
        "measured_source_count",
        "retrieved_source_count",
        "selected_source_count",
        "selected_source_density_per_square_deg",
        "point_source_logistic_probability",
        "point_source_logistic_selected",
    }
    checks = {
        "twelve_development_fields": len(pilot) == 12,
        "pilot_field_identifiers_unique": pilot["field_id"].is_unique,
        "all_pilot_fields_are_development": pilot["experiment_partition"].eq("development").all(),
        "no_validation_field_selected": validation_ids.isdisjoint(pilot_ids),
        "one_benchmark_field": pilot["is_single_field_performance_benchmark"].sum() == 1,
        "benchmark_is_minimum_absolute_latitude_development_field": pilot.loc[
            pilot["is_single_field_performance_benchmark"], "field_id"
        ].iloc[0]
        == grid.loc[grid["experiment_partition"].eq("development")]
        .sort_values(["absolute_galactic_latitude_deg", "field_id"])
        .iloc[0]["field_id"],
        "all_hemisphere_latitude_bands_represented": set(pilot["hemisphere_latitude_band_id"])
        == expected_cells,
        "all_ecliptic_latitude_bands_represented": set(pilot["absolute_ecliptic_latitude_band"])
        == set(grid["absolute_ecliptic_latitude_band"]),
        "both_environment_flag_states_represented": pilot["environment_flag_state"].nunique() == 2,
        "selection_uses_no_gaia_counts_or_selector_outputs": forbidden_columns.isdisjoint(
            pilot.columns
        ),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS.parent.mkdir(parents=True, exist_ok=True)
    pilot.to_csv(LARGE_SKY_DEVELOPMENT_PILOT_FIELDS, index=False)
    manifest = {
        "pilot_version": PILOT_VERSION,
        "pilot_id": pilot.iloc[0]["pilot_id"],
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "development_field_identities_frozen_before_gaia_retrieval",
        "selection_contract": (
            "grid_positions_and_stable_hashes_only_no_gaia_counts_no_selector_outputs"
        ),
        "input": {
            "path": str(LARGE_SKY_FIELD_GRID.relative_to(PROJECT_ROOT)),
            "sha256": grid_sha256,
            "grid_id": grid_manifest["grid_id"],
        },
        "benchmark_rule": "smallest_absolute_galactic_latitude_then_field_id",
        "coverage_rule": (
            "benchmark_plus_one_development_field_per_hemisphere_latitude_band_then_"
            "stable_hash_supplements_for_missing_ecliptic_bands"
        ),
        "pilot_field_count": len(pilot),
        "benchmark_field_id": pilot.loc[
            pilot["is_single_field_performance_benchmark"], "field_id"
        ].iloc[0],
        "pilot_field_ids": pilot["field_id"].tolist(),
        "held_back_validation_field_count": len(validation_ids),
        "held_back_validation_field_ids_sha256": hashlib.sha256(
            "\n".join(sorted(validation_ids)).encode()
        ).hexdigest(),
        "output": {
            "path": str(LARGE_SKY_DEVELOPMENT_PILOT_FIELDS.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(LARGE_SKY_DEVELOPMENT_PILOT_FIELDS),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Large-sky development pilot freeze failed: {checks}")


if __name__ == "__main__":
    main()
