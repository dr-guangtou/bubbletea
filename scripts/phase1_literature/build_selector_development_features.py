"""Build a Gaia DR3 feature matrix for benchmark development rows only.

The validation partition is selected out before any remote query. The script
retrieves additional Gaia-native selector inputs by exact source identifier and
writes a provenance manifest without changing the released benchmark.
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import pandas as pd
from pyvo.dal import tap

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    SELECTOR_DEVELOPMENT_FEATURES,
    SELECTOR_DEVELOPMENT_FEATURES_MANIFEST,
    VALIDATION_BENCHMARK,
    VALIDATION_BENCHMARK_MANIFEST,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import serialize_path
from scripts.phase1_literature.synchronize_crossmatch_products import (
    DATALAB_TAP_URL,
    GAIA_IDENTIFIER_BATCH_SIZE,
    MAX_QUERY_ATTEMPTS,
    chunked_rows,
    run_query,
)

logger = logging.getLogger(__name__)

GAIA_RELEASE = "Gaia DR3"
DEVELOPMENT_FEATURE_VERSION = "gaia_selector_development_features_v3"
ADDITIONAL_GAIA_COLUMNS = [
    "source_id",
    "pmra_pmdec_corr",
    "phot_g_mean_flux_over_error",
    "phot_bp_mean_flux_over_error",
    "phot_rp_mean_flux_over_error",
    "phot_bp_rp_excess_factor",
    "classprob_dsc_combmod_quasar",
    "classprob_dsc_combmod_galaxy",
    "classprob_dsc_combmod_star",
    "in_qso_candidates",
    "in_galaxy_candidates",
    "non_single_star",
]


def parse_arguments() -> argparse.Namespace:
    """Parse input, output, and smoke-run arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--benchmark-manifest", type=Path, default=VALIDATION_BENCHMARK_MANIFEST)
    parser.add_argument("--output", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES)
    parser.add_argument("--manifest", type=Path, default=SELECTOR_DEVELOPMENT_FEATURES_MANIFEST)
    parser.add_argument(
        "--limit",
        type=int,
        help="Query only the first N development identifiers for a measured smoke run.",
    )
    return parser.parse_args()


def build_query(source_ids: list[str]) -> str:
    """Build one deterministic exact-identifier Gaia query."""
    identifiers = ",".join(sorted(source_ids, key=int))
    return (
        f"SELECT {', '.join(ADDITIONAL_GAIA_COLUMNS)} FROM gaia_dr3.gaia_source "
        f"WHERE source_id IN ({identifiers}) ORDER BY source_id"
    )


def retrieve_features(source_ids: list[str]) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Retrieve selector features in measured, deterministic identifier batches."""
    service = tap.TAPService(DATALAB_TAP_URL)
    identifier_frame = pd.DataFrame({"source_id": sorted(set(source_ids), key=int)})
    frames = []
    query_records = []
    for batch_number, batch in enumerate(
        chunked_rows(identifier_frame, GAIA_IDENTIFIER_BATCH_SIZE), start=1
    ):
        identifiers = batch["source_id"].tolist()
        query = build_query(identifiers)
        started = perf_counter()
        result = run_query(service, query, len(identifiers) + 10)
        elapsed_seconds = perf_counter() - started
        frames.append(result)
        query_records.append(
            {
                "batch_number": batch_number,
                "requested_identifier_count": len(identifiers),
                "returned_row_count": len(result),
                "elapsed_seconds": elapsed_seconds,
                "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
                "maximum_query_attempts": MAX_QUERY_ATTEMPTS,
            }
        )
        logger.info(
            "Gaia exact-identifier batch %d: requested %d, returned %d",
            batch_number,
            len(identifiers),
            len(result),
        )
    features = pd.concat(frames, ignore_index=True)
    features["source_id"] = features["source_id"].map(lambda value: str(int(value)))
    if features["source_id"].duplicated().any():
        raise RuntimeError("Gaia returned duplicate development source identifiers")
    return features, query_records


def main() -> None:
    """Build and validate the development-only feature matrix."""
    arguments = parse_arguments()
    if arguments.limit is not None and arguments.limit <= 0:
        raise ValueError("--limit must be positive")

    benchmark = pd.read_csv(arguments.benchmark, dtype={"gaia_dr3_id": str})
    development = benchmark.loc[benchmark["partition"].eq("development")].copy()
    validation_ids = set(
        benchmark.loc[benchmark["partition"].eq("validation"), "gaia_dr3_id"].astype(str)
    )
    development = development.sort_values("gaia_dr3_id")
    if arguments.limit is not None:
        development = development.head(arguments.limit).copy()
    requested_ids = development["gaia_dr3_id"].astype(str).tolist()
    queried_validation_ids = set(requested_ids).intersection(validation_ids)
    if queried_validation_ids:
        raise RuntimeError("Validation identifiers entered the development query set")

    features, query_records = retrieve_features(requested_ids)
    requested_set = set(requested_ids)
    returned_set = set(features["source_id"])
    if returned_set != requested_set:
        missing = sorted(requested_set - returned_set, key=int)
        unexpected = sorted(returned_set - requested_set, key=int)
        raise RuntimeError(
            f"Gaia exact-identifier mismatch: missing={len(missing)}, unexpected={len(unexpected)}"
        )

    output = development.merge(
        features,
        left_on="gaia_dr3_id",
        right_on="source_id",
        how="left",
        validate="1:1",
    ).drop(columns="source_id")
    if set(output["partition"]) != {"development"}:
        raise RuntimeError("Development feature output contains another partition")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(arguments.output, index=False)
    with arguments.benchmark_manifest.open(encoding="utf-8") as input_file:
        benchmark_manifest = json.load(input_file)
    manifest = {
        "feature_version": DEVELOPMENT_FEATURE_VERSION,
        "generated_utc": datetime.now(UTC).isoformat(),
        "gaia_release": GAIA_RELEASE,
        "endpoint": DATALAB_TAP_URL,
        "partition": "development",
        "smoke_limit": arguments.limit,
        "inputs": {
            "benchmark": serialize_path(arguments.benchmark),
            "benchmark_sha256": calculate_sha256(arguments.benchmark),
            "benchmark_manifest": serialize_path(arguments.benchmark_manifest),
            "benchmark_manifest_sha256": calculate_sha256(arguments.benchmark_manifest),
            "benchmark_output_sha256": benchmark_manifest["output_sha256"],
        },
        "additional_gaia_columns": ADDITIONAL_GAIA_COLUMNS[1:],
        "query_batches": query_records,
        "counts": {
            "benchmark_rows": len(benchmark),
            "development_rows": int(benchmark["partition"].eq("development").sum()),
            "validation_rows": int(benchmark["partition"].eq("validation").sum()),
            "queried_development_rows": len(requested_ids),
            "queried_validation_rows": len(queried_validation_ids),
            "output_rows": len(output),
            "unique_output_gaia_sources": output["gaia_dr3_id"].nunique(),
        },
        "output": serialize_path(arguments.output),
        "output_sha256": calculate_sha256(arguments.output),
    }
    arguments.manifest.parent.mkdir(parents=True, exist_ok=True)
    arguments.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %d development feature rows to %s", len(output), arguments.output)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
