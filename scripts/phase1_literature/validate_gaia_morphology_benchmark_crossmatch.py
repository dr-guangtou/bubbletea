"""Validate the blind-safe Gaia morphology benchmark cross-match artifacts."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH,
    GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH_MANIFEST,
    GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH_VALIDATION,
    VALIDATION_BENCHMARK,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase1_literature.crossmatch_gaia_morphology_benchmark import CROSSMATCH_VERSION


def parse_arguments() -> argparse.Namespace:
    """Parse benchmark, cross-match, manifest, and validation paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=VALIDATION_BENCHMARK)
    parser.add_argument("--crossmatch", type=Path, default=GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH_MANIFEST,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=GAIA_MORPHOLOGY_BENCHMARK_CROSSMATCH_VALIDATION,
    )
    return parser.parse_args()


def main() -> None:
    """Run structural, partition, count, and provenance checks."""
    arguments = parse_arguments()
    benchmark = pd.read_csv(arguments.benchmark, dtype={"gaia_dr3_id": str})
    crossmatch = pd.read_csv(arguments.crossmatch, dtype={"gaia_dr3_id": str})
    manifest = json.loads(arguments.manifest.read_text(encoding="utf-8"))
    development = benchmark.loc[benchmark["partition"].eq("development")]
    validation_ids = set(benchmark.loc[benchmark["partition"].eq("validation"), "gaia_dr3_id"])
    checks = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check(
        "crossmatch_version",
        manifest["crossmatch_version"] == CROSSMATCH_VERSION,
        manifest["crossmatch_version"],
    )
    check(
        "output_hash",
        manifest["output_sha256"] == calculate_sha256(arguments.crossmatch),
        manifest["output_sha256"],
    )
    check(
        "benchmark_hash",
        manifest["inputs"]["benchmark_sha256"] == calculate_sha256(arguments.benchmark),
        manifest["inputs"]["benchmark_sha256"],
    )
    check(
        "development_only",
        crossmatch["partition"].eq("development").all(),
        sorted(crossmatch["partition"].unique()),
    )
    check(
        "no_validation_identifiers",
        set(crossmatch["gaia_dr3_id"]).isdisjoint(validation_ids),
        len(set(crossmatch["gaia_dr3_id"]).intersection(validation_ids)),
    )
    check(
        "unique_gaia_identifiers",
        not crossmatch["gaia_dr3_id"].duplicated().any(),
        int(crossmatch["gaia_dr3_id"].duplicated().sum()),
    )
    check(
        "all_matches_are_development_rows",
        set(crossmatch["gaia_dr3_id"]).issubset(set(development["gaia_dr3_id"])),
        len(crossmatch),
    )
    check(
        "manifest_match_count",
        manifest["counts"]["development_matches"] == len(crossmatch),
        manifest["counts"]["development_matches"],
    )
    confirmed_matches = int(crossmatch["label_subtype"].eq("ucd_confirmed").sum())
    candidate_matches = int(crossmatch["label_subtype"].eq("ucd_candidate").sum())
    hii_matches = int(
        crossmatch["label_subtype"].isin(["compact_hii_region", "dwarf_galaxy_hii_region"]).sum()
    )
    check(
        "confirmed_match_count",
        manifest["counts"]["confirmed_development_ucd_matches"] == confirmed_matches,
        confirmed_matches,
    )
    check(
        "candidate_match_count",
        manifest["counts"]["candidate_development_ucd_matches"] == candidate_matches,
        candidate_matches,
    )
    check(
        "hii_match_count",
        manifest["counts"]["development_hii_region_matches"] == hii_matches,
        hii_matches,
    )
    check(
        "all_matches_have_sersic_radius",
        crossmatch["radius_sersic"].notna().all(),
        int(crossmatch["radius_sersic"].isna().sum()),
    )
    check(
        "candidate_catalog_interpretation",
        manifest["interpretation"] == "candidate_catalog_membership_not_astrophysical_truth",
        manifest["interpretation"],
    )
    check(
        "not_parent_sample",
        manifest["selector_use"]
        == "supplementary_morphology_evidence_not_parent_sample_requirement",
        manifest["selector_use"],
    )
    check(
        "validation_partition_blind",
        manifest["validation_partition_inspected"] is False,
        manifest["validation_partition_inspected"],
    )

    failed = [item for item in checks if not item["passed"]]
    report = {
        "crossmatch_version": CROSSMATCH_VERSION,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "checks": checks,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failed:
        names = ", ".join(item["name"] for item in failed)
        raise RuntimeError(f"Gaia morphology benchmark cross-match validation failed: {names}")


if __name__ == "__main__":
    main()
