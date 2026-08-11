"""Measure pre-selector Gaia conditions for frozen large-sky development fields."""

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS,
    LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS_MANIFEST,
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST,
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST,
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY,
    LARGE_SKY_FIELD_GRID,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import file_sha256, query_sha256
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.query_partition import cone_predicate
from scripts.utils.point_source_selector import MAXIMUM_G_MAGNITUDE, MINIMUM_G_MAGNITUDE

LOGGER = logging.getLogger(__name__)
MEASUREMENT_VERSION = "large_sky_development_field_conditions_v1"


def measure_field_condition(service: tap.TAPService, field: pd.Series) -> dict[str, object]:
    """Measure counts, observation frequency, and M10 without applying the selector."""
    predicate = cone_predicate(
        float(field["ra_deg"]),
        float(field["dec_deg"]),
        float(field["field_radius_deg"]),
    )
    magnitude_domain = f"phot_g_mean_mag BETWEEN {MINIMUM_G_MAGNITUDE} AND {MAXIMUM_G_MAGNITUDE}"
    magnitude_domain_count_query = (
        "SELECT COUNT(*) AS source_count FROM gaia_dr3.gaia_source WHERE "
        f"{predicate} AND {magnitude_domain}"
    )
    started = perf_counter()
    source_count = int(
        service.run_sync(magnitude_domain_count_query, maxrec=10)
        .to_table()
        .to_pandas()
        .iloc[0]["source_count"]
    )
    magnitude_domain_count_seconds = perf_counter() - started
    observation_query = (
        "SELECT source_id, visibility_periods_used, astrometric_matched_transits "
        "FROM gaia_dr3.gaia_source WHERE "
        f"{predicate} AND {magnitude_domain}"
    )
    started = perf_counter()
    observations = (
        service.run_sync(observation_query, maxrec=source_count + 1).to_table().to_pandas()
    )
    observation_retrieval_seconds = perf_counter() - started
    low_transit_count_query = (
        "SELECT COUNT(*) AS source_count FROM gaia_dr3.gaia_source WHERE "
        f"{predicate} AND astrometric_matched_transits <= 10 "
        "AND phot_g_mean_mag IS NOT NULL"
    )
    started = perf_counter()
    low_transit_source_count = int(
        service.run_sync(low_transit_count_query, maxrec=10)
        .to_table()
        .to_pandas()
        .iloc[0]["source_count"]
    )
    low_transit_count_seconds = perf_counter() - started
    low_transit_query = (
        "SELECT phot_g_mean_mag FROM gaia_dr3.gaia_source WHERE "
        f"{predicate} AND astrometric_matched_transits <= 10 "
        "AND phot_g_mean_mag IS NOT NULL"
    )
    started = perf_counter()
    low_transit = (
        service.run_sync(low_transit_query, maxrec=low_transit_source_count + 1)
        .to_table()
        .to_pandas()
    )
    low_transit_seconds = perf_counter() - started
    valid_low_transit_magnitudes = low_transit["phot_g_mean_mag"].dropna().astype(float)
    visibility_period_count = int(observations["visibility_periods_used"].notna().sum())
    matched_transit_count = int(observations["astrometric_matched_transits"].notna().sum())
    query_text = " ".join(
        (
            magnitude_domain_count_query,
            observation_query,
            low_transit_count_query,
            low_transit_query,
        )
    ).lower()
    return {
        "measurement_version": MEASUREMENT_VERSION,
        "pilot_id": field["pilot_id"],
        "grid_id": field["grid_id"],
        "field_id": field["field_id"],
        "experiment_partition": field["experiment_partition"],
        "hemisphere": field["hemisphere"],
        "equal_area_latitude_band_index": int(field["equal_area_latitude_band_index"]),
        "absolute_ecliptic_latitude_band": field["absolute_ecliptic_latitude_band"],
        "environment_flag_state": field["environment_flag_state"],
        "ra_deg": float(field["ra_deg"]),
        "dec_deg": float(field["dec_deg"]),
        "galactic_longitude_deg": float(field["galactic_longitude_deg"]),
        "galactic_latitude_deg": float(field["galactic_latitude_deg"]),
        "ecliptic_latitude_deg": float(field["ecliptic_latitude_deg"]),
        "field_radius_deg": float(field["field_radius_deg"]),
        "usable_area_square_deg": float(field["requested_area_square_deg"]),
        "source_count_in_frozen_magnitude_domain": source_count,
        "source_density_per_square_deg": source_count / float(field["requested_area_square_deg"]),
        "retrieved_observation_source_count": len(observations),
        "observation_source_identifiers_unique": observations["source_id"].is_unique,
        "visibility_period_non_null_count": visibility_period_count,
        "mean_visibility_periods_used": float(observations["visibility_periods_used"].mean()),
        "matched_transit_non_null_count": matched_transit_count,
        "mean_astrometric_matched_transits": float(
            observations["astrometric_matched_transits"].mean()
        ),
        "low_transit_source_count": low_transit_source_count,
        "retrieved_low_transit_source_count": len(low_transit),
        "m10_median_g_magnitude": float(valid_low_transit_magnitudes.median()),
        "magnitude_domain_count_query_seconds": magnitude_domain_count_seconds,
        "observation_retrieval_seconds": observation_retrieval_seconds,
        "low_transit_count_query_seconds": low_transit_count_seconds,
        "low_transit_retrieval_seconds": low_transit_seconds,
        "magnitude_domain_count_query_sha256": query_sha256(magnitude_domain_count_query),
        "observation_query_sha256": query_sha256(observation_query),
        "low_transit_count_query_sha256": query_sha256(low_transit_count_query),
        "low_transit_query_sha256": query_sha256(low_transit_query),
        "query_contract_uses_selector_output": any(
            term in query_text
            for term in (
                "point_source",
                "selector",
                "astrometric_excess_noise_sig",
                "ipd_frac_multi_peak",
                "ipd_gof_harmonic_amplitude",
            )
        ),
    }


def main() -> None:
    """Measure all 12 frozen development pilot fields and validate completeness."""
    pilot = pd.read_csv(LARGE_SKY_DEVELOPMENT_PILOT_FIELDS)
    pilot_manifest = json.loads(
        LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST.read_text(encoding="utf-8")
    )
    retrieval_summary = pd.read_csv(LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY)
    retrieval_manifest = json.loads(
        LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST.read_text(encoding="utf-8")
    )
    grid = pd.read_csv(LARGE_SKY_FIELD_GRID)
    validation_field_ids = set(
        grid.loc[grid["experiment_partition"].eq("validation"), "field_id"].astype(str)
    )
    service = tap.TAPService(DATA_LAB_TAP_URL)
    started = perf_counter()
    records = []
    for index, (_, field) in enumerate(pilot.sort_values("field_id").iterrows(), start=1):
        field_id = str(field["field_id"])
        if field_id in validation_field_ids or field["experiment_partition"] != "development":
            raise RuntimeError(f"Refusing to measure non-development field {field_id}")
        LOGGER.info("Measuring development field %d/%d: %s", index, len(pilot), field_id)
        records.append(measure_field_condition(service, field))
    results = pd.DataFrame(records)
    total_seconds = perf_counter() - started
    conditions_by_field = results.set_index("field_id").sort_index()
    retrieval_by_field = retrieval_summary.set_index("field_id").sort_index()
    output_field_ids = set(results["field_id"].astype(str))
    query_hash_columns = [
        "magnitude_domain_count_query_sha256",
        "observation_query_sha256",
        "low_transit_count_query_sha256",
        "low_transit_query_sha256",
    ]
    checks = {
        "all_twelve_frozen_development_fields_measured": len(results) == len(pilot) == 12
        and output_field_ids == set(pilot["field_id"].astype(str)),
        "no_validation_field_measured": validation_field_ids.isdisjoint(output_field_ids),
        "aggregate_counts_match_full_column_retrieval": conditions_by_field[
            "source_count_in_frozen_magnitude_domain"
        ].equals(retrieval_by_field["retrieved_source_count"]),
        "observation_retrievals_complete": results["retrieved_observation_source_count"]
        .eq(results["source_count_in_frozen_magnitude_domain"])
        .all(),
        "observation_source_identifiers_unique": results[
            "observation_source_identifiers_unique"
        ].all(),
        "low_transit_retrievals_complete": results["low_transit_source_count"]
        .eq(results["retrieved_low_transit_source_count"])
        .all(),
        "observation_counts_complete": results["visibility_period_non_null_count"]
        .eq(results["source_count_in_frozen_magnitude_domain"])
        .all()
        and results["matched_transit_non_null_count"]
        .eq(results["source_count_in_frozen_magnitude_domain"])
        .all(),
        "all_m10_values_finite": np.isfinite(results["m10_median_g_magnitude"]).all(),
        "all_areas_match_retrieval": conditions_by_field["usable_area_square_deg"].equals(
            retrieval_by_field["usable_area_square_deg"]
        ),
        "query_hashes_unique_per_field_and_query_type": all(
            results[column].is_unique for column in query_hash_columns
        ),
        "no_selector_output_used": ~results["query_contract_uses_selector_output"].any(),
        "input_manifests_passed": pilot_manifest["passed_count"] == pilot_manifest["check_count"]
        and retrieval_manifest["passed_count"] == retrieval_manifest["check_count"],
    }
    checks = {name: bool(value) for name, value in checks.items()}
    LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS, index=False)
    manifest = {
        "measurement_version": MEASUREMENT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "measurement_scope": "twelve_frozen_development_fields_pre_selector_only",
        "data_source": {
            "catalog_release": "Gaia DR3",
            "table": "gaia_dr3.gaia_source",
            "query_service": DATA_LAB_TAP_URL,
            "publication_bibcode": "2023A&A...674A...1G",
            "publication_doi": "10.1051/0004-6361/202243940",
        },
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
                LARGE_SKY_DEVELOPMENT_PILOT_FIELDS_MANIFEST,
                LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY,
                LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST,
            )
        ],
        "plain_language_definitions": {
            "m10": (
                "The median Gaia G magnitude among sources with at most ten matched "
                "astrometric transits; it is a local depth indicator, not a selector cut."
            ),
            "visibility_periods": (
                "Groups of Gaia observations separated in time; the field mean describes "
                "how often sources were observed on distinct occasions."
            ),
            "matched_transits": (
                "Gaia focal-plane crossings matched to a source; the field mean is another "
                "measure of observation frequency."
            ),
            "total_source_density": (
                "All Gaia sources in the frozen G range divided by exact usable area before "
                "the UCD selector is applied."
            ),
        },
        "minimum_g_magnitude": MINIMUM_G_MAGNITUDE,
        "maximum_g_magnitude": MAXIMUM_G_MAGNITUDE,
        "field_count": len(results),
        "held_back_validation_field_count": len(validation_field_ids),
        "validation_selector_results_opened": False,
        "total_elapsed_seconds": total_seconds,
        "measured_ranges": {
            column: {
                "minimum": float(results[column].min()),
                "maximum": float(results[column].max()),
            }
            for column in (
                "source_density_per_square_deg",
                "mean_visibility_periods_used",
                "mean_astrometric_matched_transits",
                "m10_median_g_magnitude",
            )
        },
        "output": {
            "path": str(LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DEVELOPMENT_FIELD_CONDITIONS_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Large-sky field-condition measurement failed: {checks}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
