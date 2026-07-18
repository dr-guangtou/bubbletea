"""Select five real hosts for count-blind background-design review."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    BACKGROUND_REVIEW_HOSTS,
    BACKGROUND_REVIEW_HOSTS_MANIFEST,
    GALAXY_SAMPLE_CSV,
    KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES,
    PROJECT_ROOT,
)


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a local input file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def first_ranked(rows: pd.DataFrame) -> pd.Series:
    """Return the lowest-rank row from a non-empty set."""
    if rows.empty:
        raise RuntimeError("A required background-review category is empty")
    return rows.sort_values("rank").iloc[0]


def main() -> None:
    """Write a deterministic review set without Gaia source-count information."""
    environments = pd.read_csv(KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES)
    hosts = pd.read_csv(GALAXY_SAMPLE_CSV)[["rank", "glat", "glon"]]
    rows = environments.merge(hosts, on="rank", how="left", validate="one_to_one")
    accepted = rows["association_state"].eq("accepted_unique_spherical_5arcsec_v1")
    one_galaxy = rows["catalog_environment_role"].eq("catalog_isolated_principal")
    group_main = rows["catalog_environment_role"].eq("catalog_group_principal")
    group_member = rows["catalog_environment_role"].eq("catalog_group_member")
    selections = [
        (
            "highest_ranked_one_galaxy_catalog_case",
            first_ranked(rows.loc[accepted & one_galaxy]),
        ),
        (
            "nearest_one_galaxy_catalog_case",
            rows.loc[accepted & one_galaxy].sort_values(["dist_best", "rank"]).iloc[0],
        ),
        ("highest_ranked_group_main_galaxy", first_ranked(rows.loc[accepted & group_main])),
        ("highest_ranked_group_member", first_ranked(rows.loc[accepted & group_member])),
        ("highest_ranked_unresolved_environment", first_ranked(rows.loc[~accepted])),
    ]
    review = pd.DataFrame([row for _, row in selections])
    review.insert(0, "review_case", [name for name, _ in selections])
    review["review_use"] = "geometry_and_field_condition_review_only"
    BACKGROUND_REVIEW_HOSTS.parent.mkdir(parents=True, exist_ok=True)
    review.to_csv(BACKGROUND_REVIEW_HOSTS, index=False)
    manifest = {
        "review_version": "background_review_hosts_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "selection_contract": "deterministic_host_and_environment_fields_only_no_gaia_counts",
        "inputs": [
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "sha256": file_sha256(path),
            }
            for path in (GALAXY_SAMPLE_CSV, KOURKCHI_TULLY_ENVIRONMENT_CANDIDATES)
        ],
        "row_count": len(review),
        "review_cases": review["review_case"].tolist(),
    }
    BACKGROUND_REVIEW_HOSTS_MANIFEST.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
