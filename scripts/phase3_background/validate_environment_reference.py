"""Validate provenance and accepted Kourkchi-Tully environment associations."""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    KOURKCHI_TULLY_2017_DIR,
    KOURKCHI_TULLY_2017_PROVENANCE,
    KOURKCHI_TULLY_ENVIRONMENT_AUDIT,
    KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES,
    KOURKCHI_TULLY_ENVIRONMENT_VALIDATION,
)


def sha256(path: Path) -> str:
    """Return a file's SHA-256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    """Require source, identity-rule, ambiguity, and output invariants."""
    provenance = json.loads(KOURKCHI_TULLY_2017_PROVENANCE.read_text(encoding="utf-8"))
    audit = json.loads(KOURKCHI_TULLY_ENVIRONMENT_AUDIT.read_text(encoding="utf-8"))
    rows = pd.read_csv(KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES)
    accepted = rows["association_state"].eq("accepted_unique_spherical_5arcsec_v1")
    ambiguous = rows["association_state"].eq("manual_ambiguous_multiple_within_5arcsec")
    unmatched = rows["association_state"].eq("unmatched_beyond_5_arcsec")
    source_digests = {
        name: sha256(KOURKCHI_TULLY_2017_DIR / name)
        for name in ["ReadMe", "table2.dat.gz", "table3.dat.gz"]
    }
    checks = {
        "source_digests": all(
            source_digests[name] == provenance["files"][name]["sha256"] for name in source_digests
        ),
        "host_count": len(rows) == 2_155 == audit["host_count"],
        "association_partition": int(accepted.sum()) == 1_792
        and int(ambiguous.sum()) == 2
        and int(unmatched.sum()) == 361,
        "accepted_radius": rows.loc[accepted, "nearest_separation_arcsec"].le(5).all(),
        "accepted_unique_neighbor": rows.loc[accepted, "catalog_neighbors_within_5_arcsec"]
        .eq(1)
        .all(),
        "accepted_unique_pgc": not rows.loc[accepted, "catalog_pgc"].duplicated().any(),
        "accepted_group_properties": rows.loc[
            accepted,
            ["group_principal_pgc", "group_member_count", "catalog_environment_role"],
        ]
        .notna()
        .all()
        .all(),
        "ambiguities_preserved": rows.loc[ambiguous, "catalog_neighbors_within_5_arcsec"]
        .gt(1)
        .all(),
        "shifted_control_zero_matches": audit["shifted_control_calibration"][
            "shifted_position_count"
        ]
        == 17_240
        and audit["shifted_control_calibration"]["total_match_count"] == 0,
        "no_inference_claim": "no automatic inferential background assignment"
        in provenance["use_policy"],
    }
    checks = {name: bool(value) for name, value in checks.items()}
    report = {
        "validation_version": "kourkchi_tully_environment_validation_v1",
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "failed_count": len(checks) - sum(checks.values()),
        "source_digests": source_digests,
        "checks": checks,
    }
    KOURKCHI_TULLY_ENVIRONMENT_VALIDATION.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"Environment-reference validation failed: {checks}")


if __name__ == "__main__":
    main()
