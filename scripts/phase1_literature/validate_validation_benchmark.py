"""Validate benchmark provenance, label roles, and fixed partition invariants."""

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    DWARF_HII_GAIA_ASSOCIATION_CALIBRATION,
    DWARF_HII_GAIA_ASSOCIATION_CANDIDATES,
    HII_GAIA_ASSOCIATION_CALIBRATION,
    HII_GAIA_ASSOCIATION_CANDIDATES,
    LITERATURE_REFERENCE_DB_V2,
    VALIDATION_BENCHMARK,
    VALIDATION_BENCHMARK_MANIFEST,
    VALIDATION_BENCHMARK_SOURCES,
    VALIDATION_BENCHMARK_VALIDATION,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.build_validation_benchmark import (
    BENCHMARK_VERSION,
    PARTITION_RULESET,
    fixed_partition,
    partition_group,
)


def parse_arguments() -> argparse.Namespace:
    """Parse benchmark validation paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--manifest", type=Path, default=VALIDATION_BENCHMARK_MANIFEST)
    parser.add_argument("--source-registry", type=Path, default=VALIDATION_BENCHMARK_SOURCES)
    parser.add_argument("--reference-database", type=Path, default=LITERATURE_REFERENCE_DB_V2)
    parser.add_argument("--output", type=Path, default=VALIDATION_BENCHMARK_VALIDATION)
    return parser.parse_args()


def database_counts(path: Path) -> dict[str, int]:
    """Return Gaia-linked canonical and source counts from the read-only database."""
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        row = connection.execute(
            """
            SELECT COUNT(DISTINCT a.canonical_object_id), COUNT(DISTINCT r.gaia_dr3_id)
            FROM object_record_associations a
            JOIN literature_records r USING (record_id)
            WHERE r.gaia_dr3_id IS NOT NULL
            """
        ).fetchone()
    finally:
        connection.close()
    return {"canonical_objects": int(row[0]), "gaia_sources": int(row[1])}


def main() -> None:
    """Run deterministic checks and write a machine-readable validation report."""
    arguments = parse_arguments()
    with arguments.manifest.open(encoding="utf-8") as input_file:
        manifest = json.load(input_file)
    with arguments.source_registry.open(encoding="utf-8") as input_file:
        source_registry = json.load(input_file)
    benchmark = pd.read_csv(arguments.benchmark, dtype={"gaia_dr3_id": str})
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check(
        "benchmark_version",
        set(benchmark["benchmark_version"]) == {BENCHMARK_VERSION},
        sorted(benchmark["benchmark_version"].unique()),
    )
    check(
        "partition_ruleset",
        set(benchmark["partition_ruleset"]) == {PARTITION_RULESET},
        sorted(benchmark["partition_ruleset"].unique()),
    )
    check("unique_benchmark_ids", benchmark["benchmark_id"].is_unique, len(benchmark))
    check("unique_gaia_sources", benchmark["gaia_dr3_id"].is_unique, len(benchmark))
    check(
        "output_digest",
        calculate_sha256(arguments.benchmark) == manifest["output_sha256"],
        manifest["output_sha256"],
    )
    check(
        "reference_database_digest",
        calculate_sha256(arguments.reference_database)
        == manifest["inputs"]["reference_database_sha256"],
        manifest["inputs"]["reference_database_sha256"],
    )
    check(
        "source_registry_digest",
        calculate_sha256(arguments.source_registry) == manifest["inputs"]["source_registry_sha256"],
        manifest["inputs"]["source_registry_sha256"],
    )
    association_inputs = {
        "hii_association_candidates": HII_GAIA_ASSOCIATION_CANDIDATES,
        "hii_association_calibration": HII_GAIA_ASSOCIATION_CALIBRATION,
        "dwarf_hii_association_candidates": DWARF_HII_GAIA_ASSOCIATION_CANDIDATES,
        "dwarf_hii_association_calibration": DWARF_HII_GAIA_ASSOCIATION_CALIBRATION,
    }
    for input_name, input_path in association_inputs.items():
        expected_digest = manifest["inputs"][f"{input_name}_sha256"]
        check(
            f"{input_name}_digest",
            calculate_sha256(input_path) == expected_digest,
            expected_digest,
        )

    expected_groups = benchmark["gaia_dr3_id"].map(partition_group)
    expected_partitions = expected_groups.map(fixed_partition)
    check(
        "partition_groups_recomputed",
        expected_groups.equals(benchmark["partition_group"]),
        int((expected_groups != benchmark["partition_group"]).sum()),
    )
    check(
        "partitions_recomputed",
        expected_partitions.equals(benchmark["partition"]),
        int((expected_partitions != benchmark["partition"]).sum()),
    )
    group_partition_counts = benchmark.groupby("partition_group")["partition"].nunique()
    check(
        "no_spatial_group_partition_leakage",
        bool((group_partition_counts == 1).all()),
        int((group_partition_counts != 1).sum()),
    )

    uncertain = benchmark["label"].eq("uncertain") | benchmark["confidence_tier"].isin(
        ["uncertain", "conflict"]
    )
    check(
        "uncertain_labels_not_primary",
        not benchmark.loc[uncertain, "primary_label_eligible"].any(),
        int(benchmark.loc[uncertain, "primary_label_eligible"].sum()),
    )
    check(
        "uncertain_labels_retained_for_sensitivity",
        benchmark.loc[uncertain, "sensitivity_label_eligible"].all(),
        int(uncertain.sum()),
    )
    shared = benchmark["label_subtype"].eq("ambiguous_shared_gaia_distinct_objects")
    check("one_shared_gaia_sensitivity_row", int(shared.sum()) == 1, int(shared.sum()))

    literature = benchmark["source_cohort"].eq("literature_ucd")
    represented_canonical_ids = set()
    for value in benchmark.loc[literature, "canonical_object_id"].dropna().astype(str):
        represented_canonical_ids.update(value.split(";"))
    expected_literature = database_counts(arguments.reference_database)
    check(
        "all_gaia_linked_canonical_objects_represented",
        len(represented_canonical_ids) == expected_literature["canonical_objects"],
        len(represented_canonical_ids),
    )
    check(
        "all_literature_gaia_sources_represented_once",
        int(literature.sum()) == expected_literature["gaia_sources"],
        int(literature.sum()),
    )

    minimum_g = manifest["applicability_domain"]["minimum_phot_g_mean_mag"]
    maximum_g = manifest["applicability_domain"]["maximum_phot_g_mean_mag"]
    check(
        "magnitude_domain",
        benchmark["phot_g_mean_mag"].between(minimum_g, maximum_g, inclusive="both").all(),
        [float(benchmark["phot_g_mean_mag"].min()), float(benchmark["phot_g_mean_mag"].max())],
    )
    subtype_partitions = benchmark.groupby("label_subtype")["partition"].nunique()
    subtype_counts = benchmark["label_subtype"].value_counts()
    multirow_subtypes = subtype_counts[subtype_counts > 1].index
    check(
        "every_multirow_label_role_in_both_partitions",
        bool((subtype_partitions.loc[multirow_subtypes] == 2).all()),
        subtype_partitions.to_dict(),
    )
    sdss = benchmark["source_cohort"].str.startswith("sdss_dr16")
    check(
        "sdss_associations_within_published_crossmatch_radius",
        benchmark.loc[sdss, "gaia_association_distance_arcsec"].le(1.5).all(),
        1.5,
    )
    registry_status = {source["cohort"]: source["status"] for source in source_registry["sources"]}
    association_cohorts = {
        "phangs_muse_hii": {
            "expected_count": 175,
            "maximum_distance_arcsec": 0.3,
            "label_subtype": "compact_hii_region",
            "registry_status": "approved_moderate_confidence_0p3_arcsec",
        },
        "van_zee_dwarf_hii": {
            "expected_count": 12,
            "maximum_distance_arcsec": 3.0,
            "label_subtype": "dwarf_galaxy_hii_region",
            "registry_status": "approved_moderate_confidence_3p0_arcsec",
        },
    }
    for cohort_name, expected in association_cohorts.items():
        cohort = benchmark.loc[benchmark["source_cohort"].eq(cohort_name)]
        check(
            f"{cohort_name}_count",
            len(cohort) == expected["expected_count"],
            len(cohort),
        )
        check(
            f"{cohort_name}_association_radius",
            cohort["gaia_association_distance_arcsec"]
            .le(expected["maximum_distance_arcsec"])
            .all(),
            float(cohort["gaia_association_distance_arcsec"].max()),
        )
        check(
            f"{cohort_name}_label_contract",
            set(cohort["label"]) == {"contaminant"}
            and set(cohort["label_subtype"]) == {expected["label_subtype"]}
            and set(cohort["confidence_tier"]) == {"moderate"}
            and cohort["primary_label_eligible"].all()
            and cohort["sensitivity_label_eligible"].all(),
            {
                "labels": sorted(cohort["label"].unique()),
                "label_subtypes": sorted(cohort["label_subtype"].unique()),
                "confidence_tiers": sorted(cohort["confidence_tier"].unique()),
            },
        )
        check(
            f"{cohort_name}_registry_status",
            registry_status.get(cohort_name) == expected["registry_status"],
            registry_status.get(cohort_name),
        )
    check(
        "association_cohorts_do_not_duplicate_prior_gaia_sources",
        manifest["sampling"]["hii_rows_excluded_for_existing_gaia_source"] == 0
        and manifest["sampling"]["dwarf_hii_rows_excluded_for_existing_gaia_source"] == 0,
        {
            "phangs_muse_hii": manifest["sampling"]["hii_rows_excluded_for_existing_gaia_source"],
            "van_zee_dwarf_hii": manifest["sampling"][
                "dwarf_hii_rows_excluded_for_existing_gaia_source"
            ],
        },
    )
    check(
        "manifest_total",
        len(benchmark) == manifest["counts"]["total_rows"],
        len(benchmark),
    )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "benchmark_version": BENCHMARK_VERSION,
        "benchmark_sha256": calculate_sha256(arguments.benchmark),
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "counts": {
            "rows": len(benchmark),
            "gaia_sources": benchmark["gaia_dr3_id"].nunique(),
            "partitions": dict(sorted(Counter(benchmark["partition"]).items())),
            "label_subtypes": dict(sorted(Counter(benchmark["label_subtype"]).items())),
        },
        "checks": checks,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failed:
        failed_names = ", ".join(str(item["name"]) for item in failed)
        raise RuntimeError(f"Benchmark validation failed: {failed_names}")


if __name__ == "__main__":
    main()
