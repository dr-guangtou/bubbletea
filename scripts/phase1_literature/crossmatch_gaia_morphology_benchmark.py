"""Cross-match the blind-safe benchmark development partition to Gaia morphology.

The match uses exact Gaia DR3 source identifiers and never evaluates validation-
partition identifiers. The Gaia morphology catalog remains a candidate and
failure-mode catalog; membership is not interpreted as an astrophysical truth label.
"""

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from astropy.table import Table

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    EXTRAGALACTIC_REFERENCE_DIR,
    EXTRAGALACTIC_REFERENCE_SOURCES,
    GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH,
    GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH_MANIFEST,
    VALIDATION_BENCHMARK,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import serialize_path

logger = logging.getLogger(__name__)

CROSSMATCH_VERSION = "gaia_morphology_benchmark_crossmatch_v1"
MORPHOLOGY_CATALOG_ID = "gaia_dr3_morphology_galaxies"
MORPHOLOGY_COLUMNS = [
    "source_id",
    "classprob_dsc_combmod_galaxy",
    "classprob_dsc_combmod_quasar",
    "classlabel_dsc",
    "classlabel_dsc_joint",
    "vari_best_class_name",
    "redshift_ugc",
    "n_transits",
    "radius_sersic",
    "radius_sersic_error",
    "n_sersic",
    "n_sersic_error",
    "flags_sersic",
    "radius_de_vaucouleurs",
    "radius_de_vaucouleurs_error",
    "flags_de_vaucouleurs",
]
BENCHMARK_OUTPUT_COLUMNS = [
    "benchmark_id",
    "source_cohort",
    "source_object_id",
    "canonical_object_id",
    "gaia_dr3_id",
    "label",
    "label_subtype",
    "confidence_tier",
    "primary_label_eligible",
    "sensitivity_label_eligible",
    "label_basis",
    "classification_state",
    "partition",
    "publication_bibcode",
    "catalog_id",
    "source_row_locator",
    "source_detail",
    "phot_g_mean_mag",
]


def parse_arguments() -> argparse.Namespace:
    """Parse benchmark, registry, external-catalog, and output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--source-registry", type=Path, default=EXTRAGALACTIC_REFERENCE_SOURCES)
    parser.add_argument("--external-directory", type=Path, default=EXTRAGALACTIC_REFERENCE_DIR)
    parser.add_argument("--output", type=Path, default=GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH_MANIFEST,
    )
    return parser.parse_args()


def morphology_registry_entry(source_registry: Path) -> dict[str, object]:
    """Return the registered Gaia morphology catalog entry."""
    registry = json.loads(source_registry.read_text(encoding="utf-8"))
    entries = [
        catalog
        for catalog in registry["catalogs"]
        if catalog["catalog_id"] == MORPHOLOGY_CATALOG_ID
    ]
    if len(entries) != 1:
        raise RuntimeError("Expected one registered Gaia morphology catalog")
    return entries[0]


def grouped_counts(frame: pd.DataFrame, matched_ids: set[str]) -> list[dict[str, object]]:
    """Summarize exact-match coverage without pooling benchmark subtypes."""
    group_columns = ["source_cohort", "label", "label_subtype", "confidence_tier"]
    records = []
    for keys, group in frame.groupby(group_columns, dropna=False, sort=True):
        matched_count = int(group["gaia_dr3_id"].isin(matched_ids).sum())
        records.append(
            {
                **dict(zip(group_columns, keys, strict=True)),
                "development_row_count": len(group),
                "morphology_match_count": matched_count,
                "morphology_match_fraction": matched_count / len(group),
            }
        )
    return records


def main() -> None:
    """Write exact development matches and a provenance-rich summary manifest."""
    arguments = parse_arguments()
    benchmark = pd.read_csv(arguments.benchmark, dtype={"gaia_dr3_id": str})
    development = benchmark.loc[benchmark["partition"].eq("development")].copy()
    validation = benchmark.loc[benchmark["partition"].eq("validation")].copy()
    if development.empty or validation.empty:
        raise RuntimeError("Benchmark must contain development and validation partitions")

    catalog = morphology_registry_entry(arguments.source_registry)
    morphology_path = arguments.external_directory / str(catalog["external_relative_path"])
    if calculate_sha256(morphology_path) != catalog["sha256"]:
        raise RuntimeError("Gaia morphology catalog hash differs from its source registry")
    morphology = Table.read(morphology_path, memmap=True)[MORPHOLOGY_COLUMNS].to_pandas()
    morphology["source_id"] = morphology["source_id"].map(lambda value: str(int(value)))
    if morphology["source_id"].duplicated().any():
        raise RuntimeError("Gaia morphology catalog contains duplicate source identifiers")

    development_ids = set(development["gaia_dr3_id"])
    morphology_matches = morphology.loc[morphology["source_id"].isin(development_ids)].copy()
    output = development[BENCHMARK_OUTPUT_COLUMNS].merge(
        morphology_matches,
        left_on="gaia_dr3_id",
        right_on="source_id",
        how="inner",
        validate="1:1",
    )
    output = output.drop(columns="source_id").sort_values(["label", "label_subtype", "gaia_dr3_id"])
    if not output["partition"].eq("development").all():
        raise RuntimeError("Validation row entered the Gaia morphology cross-match")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(arguments.output, index=False)
    matched_ids = set(output["gaia_dr3_id"])
    confirmed_development = development.loc[
        development["label_subtype"].eq("ucd_confirmed")
        & development["primary_label_eligible"].eq(True)  # noqa: E712
    ]
    candidate_development = development.loc[development["label_subtype"].eq("ucd_candidate")]
    hii_development = development.loc[
        development["label_subtype"].isin(["compact_hii_region", "dwarf_galaxy_hii_region"])
    ]
    manifest = {
        "crossmatch_version": CROSSMATCH_VERSION,
        "generated_utc": datetime.now(UTC).isoformat(),
        "match_method": "exact_gaia_dr3_source_id",
        "interpretation": "candidate_catalog_membership_not_astrophysical_truth",
        "selector_use": "supplementary_morphology_evidence_not_parent_sample_requirement",
        "validation_partition_inspected": False,
        "inputs": {
            "benchmark": serialize_path(arguments.benchmark),
            "benchmark_sha256": calculate_sha256(arguments.benchmark),
            "source_registry": serialize_path(arguments.source_registry),
            "source_registry_sha256": calculate_sha256(arguments.source_registry),
            "external_relative_path": catalog["external_relative_path"],
            "external_catalog_sha256": catalog["sha256"],
            "external_catalog_row_count": catalog["row_count"],
        },
        "counts": {
            "benchmark_rows": len(benchmark),
            "development_rows": len(development),
            "validation_rows_withheld": len(validation),
            "morphology_catalog_rows": len(morphology),
            "development_matches": len(output),
            "confirmed_development_ucds": len(confirmed_development),
            "confirmed_development_ucd_matches": int(
                confirmed_development["gaia_dr3_id"].isin(matched_ids).sum()
            ),
            "candidate_development_ucds": len(candidate_development),
            "candidate_development_ucd_matches": int(
                candidate_development["gaia_dr3_id"].isin(matched_ids).sum()
            ),
            "development_hii_regions": len(hii_development),
            "development_hii_region_matches": int(
                hii_development["gaia_dr3_id"].isin(matched_ids).sum()
            ),
        },
        "grouped_counts": grouped_counts(development, matched_ids),
        "output": serialize_path(arguments.output),
        "output_sha256": calculate_sha256(arguments.output),
        "deferred_test": (
            "Repeat exact matching for the withheld validation partition only after "
            "the Gaia-only selector and morphology-use policy are frozen."
        ),
    }
    arguments.manifest.parent.mkdir(parents=True, exist_ok=True)
    arguments.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %d development morphology matches", len(output))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
