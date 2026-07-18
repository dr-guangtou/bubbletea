"""Derive fixed G-magnitude summaries from verified development checkpoints."""

import json
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
    LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES,
    LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES_MANIFEST,
    LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST,
    LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY,
    LARGE_SKY_FIELD_GRID,
    LARGE_SKY_GAIA_RETRIEVAL_DIR,
    PROJECT_ROOT,
)
from scripts.phase3_background.adaptive_gaia_retrieval import (
    AdaptiveGaiaRetriever,
    file_sha256,
    load_leaf_plan,
)
from scripts.phase3_background.benchmark_full_selector_retrieval import (
    source_identifier_sha256,
)
from scripts.phase3_background.benchmark_gaia_field_conditions import DATA_LAB_TAP_URL
from scripts.phase3_background.benchmark_large_sky_development_retrieval import (
    field_base_where,
    require_external_checkpoint_root,
)
from scripts.utils.point_source_selector import RAW_GAIA_COLUMNS

SUMMARY_VERSION = "large_sky_development_g_magnitude_summaries_v1"
QUANTILES = (0.1, 0.5, 0.9)


def main() -> None:
    """Write fixed G-magnitude summaries without making an archive request."""
    require_external_checkpoint_root()
    pilot = pd.read_csv(LARGE_SKY_DEVELOPMENT_PILOT_FIELDS)
    retrieval = pd.read_csv(LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY)
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
    external_receipts = []
    for _, field in pilot.sort_values("field_id").iterrows():
        field_id = str(field["field_id"])
        if field_id in validation_field_ids or field["experiment_partition"] != "development":
            raise RuntimeError(f"Refusing to read non-development field {field_id}")
        field_directory = (
            LARGE_SKY_GAIA_RETRIEVAL_DIR / str(field["grid_id"]) / str(field["pilot_id"]) / field_id
        )
        plan_path = field_directory / "measured_plan.csv"
        receipt_path = field_directory / "field_receipt.json"
        leaf_strips = load_leaf_plan(plan_path)
        retriever = AdaptiveGaiaRetriever(
            service,
            field_base_where(field),
            field_directory,
            tuple(RAW_GAIA_COLUMNS),
        )
        if not all(retriever.checkpoint_valid(strip) for strip in leaf_strips):
            raise RuntimeError(f"Field {field_id} has an invalid raw checkpoint")
        combined = retriever.combine(leaf_strips)
        field_retrieval = retrieval.loc[retrieval["field_id"].eq(field_id)].iloc[0]
        identifier_hash = source_identifier_sha256(combined)
        magnitudes = combined["phot_g_mean_mag"].dropna().astype(float)
        quantiles = magnitudes.quantile(QUANTILES)
        records.append(
            {
                "summary_version": SUMMARY_VERSION,
                "grid_id": field["grid_id"],
                "field_id": field_id,
                "experiment_partition": field["experiment_partition"],
                "source_count": len(combined),
                "non_null_g_magnitude_count": len(magnitudes),
                "phot_g_mean_mag_10th_percentile": float(quantiles.loc[0.1]),
                "median_phot_g_mean_mag": float(quantiles.loc[0.5]),
                "phot_g_mean_mag_90th_percentile": float(quantiles.loc[0.9]),
                "combined_source_identifier_sha256": identifier_hash,
                "source_count_matches_retrieval": len(combined)
                == int(field_retrieval["retrieved_source_count"]),
                "identifier_hash_matches_retrieval": identifier_hash
                == field_retrieval["combined_source_identifier_sha256"],
            }
        )
        external_receipts.append(
            {
                "field_id": field_id,
                "path": str(receipt_path.resolve()),
                "sha256": file_sha256(receipt_path),
                "measured_plan_path": str(plan_path.resolve()),
                "measured_plan_sha256": file_sha256(plan_path),
            }
        )
    summaries = pd.DataFrame(records)
    output_field_ids = set(summaries["field_id"].astype(str))
    checks = {
        "all_twelve_development_pilot_fields_summarized": len(summaries) == len(pilot) == 12,
        "no_validation_field_read": validation_field_ids.isdisjoint(output_field_ids),
        "all_source_counts_match_retrieval": summaries["source_count_matches_retrieval"].all(),
        "all_identifier_hashes_match_retrieval": summaries[
            "identifier_hash_matches_retrieval"
        ].all(),
        "all_g_magnitudes_present": summaries["non_null_g_magnitude_count"]
        .eq(summaries["source_count"])
        .all(),
        "all_summaries_finite": np.isfinite(
            summaries[
                [
                    "phot_g_mean_mag_10th_percentile",
                    "median_phot_g_mean_mag",
                    "phot_g_mean_mag_90th_percentile",
                ]
            ]
        )
        .all()
        .all(),
        "all_quantiles_ordered": (
            summaries["phot_g_mean_mag_10th_percentile"]
            .le(summaries["median_phot_g_mean_mag"])
            .all()
            and summaries["median_phot_g_mean_mag"]
            .le(summaries["phot_g_mean_mag_90th_percentile"])
            .all()
        ),
        "retrieval_manifest_passed": retrieval_manifest["passed_count"]
        == retrieval_manifest["check_count"],
        "no_archive_query_executed": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES.parent.mkdir(parents=True, exist_ok=True)
    summaries.to_csv(LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES, index=False)
    manifest = {
        "summary_version": SUMMARY_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "scope": "twelve_completed_development_fields_local_checkpoint_calculation",
        "plain_language_definition": (
            "For each field, sort the already downloaded Gaia G magnitudes and record "
            "the values below 10 percent, 50 percent, and 90 percent of sources."
        ),
        "quantile_method": "pandas_linear_interpolation",
        "quantiles": list(QUANTILES),
        "archive_queries_executed": 0,
        "field_count": len(summaries),
        "held_back_validation_field_count": len(validation_field_ids),
        "validation_selector_results_opened": False,
        "elapsed_seconds": perf_counter() - started,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": file_sha256(path)}
            for path in (
                LARGE_SKY_DEVELOPMENT_PILOT_FIELDS,
                LARGE_SKY_DEVELOPMENT_RETRIEVAL_SUMMARY,
                LARGE_SKY_DEVELOPMENT_RETRIEVAL_MANIFEST,
                LARGE_SKY_FIELD_GRID,
            )
        ],
        "external_field_receipts": external_receipts,
        "output": {
            "path": str(LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES),
        },
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    LARGE_SKY_DEVELOPMENT_G_MAGNITUDE_SUMMARIES_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"G-magnitude summary derivation failed: {checks}")


if __name__ == "__main__":
    main()
