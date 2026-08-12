"""Validate the bounded M60 count and Legacy Survey cutout pilot artifacts."""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from matplotlib.image import imread

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    EXTERNAL_DATA_DIR,
    FIGURES_DIR,
    M60_KNOWN_UCD_CUTOUT_MANIFEST,
    M60_KNOWN_UCD_CUTOUT_SUMMARY,
    M60_POSITIVE_CONTROL_COUNT_BENCHMARK,
    M60_POSITIVE_CONTROL_KNOWN_OBJECTS,
)


def resolve_external_path(path_text: str) -> Path:
    """Resolve a portable external-data locator."""
    prefix = "$BUBBLETEA_EXTERNAL_DATA/"
    if not path_text.startswith(prefix):
        raise RuntimeError(f"Expected an external-data locator, received {path_text}")
    return EXTERNAL_DATA_DIR / path_text.removeprefix(prefix)


def sha256(path: Path) -> str:
    """Calculate a file digest without changing the file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    """Check count scope, cutout identity, dimensions, and figure pairing."""
    count = json.loads(M60_POSITIVE_CONTROL_COUNT_BENCHMARK.read_text())
    summary = json.loads(M60_KNOWN_UCD_CUTOUT_SUMMARY.read_text())
    manifest = pd.read_csv(M60_KNOWN_UCD_CUTOUT_MANIFEST, dtype={"gaia_dr3_id": str})
    known = pd.read_csv(M60_POSITIVE_CONTROL_KNOWN_OBJECTS, dtype={"gaia_dr3_ids": str})
    reliable_ids = set(
        known.loc[
            known["positive_control_role"].eq("reliable_confirmed_ucd"),
            "gaia_dr3_ids",
        ]
    )
    file_checks = []
    for _, row in manifest.iterrows():
        path = resolve_external_path(row["file_path"])
        file_checks.append(
            path.is_file()
            and sha256(path) == row["sha256"]
            and imread(path).shape[:2] == (int(row["height_pixels"]), int(row["width_pixels"]))
        )

    figure_base = FIGURES_DIR / "phase4" / "m60_known_ucd_legacy_cutouts_v1"
    checks = {
        "count_query_safeguards_passed": count["passed_count"] == count["check_count"],
        "count_is_raw_not_selector_passing": not count["selector_applied"],
        "count_downloaded_no_source_rows": count["source_rows_downloaded"] == 0,
        "exactly_two_cutouts_recorded": len(manifest) == summary["target_count"] == 2,
        "cutouts_are_the_two_reliable_controls": set(manifest["gaia_dr3_id"]) == reliable_ids,
        "cutout_files_match_digests_and_dimensions": all(file_checks),
        "cutout_scale_matches_frozen_pilot": manifest["field_width_arcsec"].eq(16.768).all(),
        "visual_review_does_not_remove_sources": (
            "visual_review_flags_do_not_remove_sources_from_gaia_profile"
            in summary["scientific_limits"]
        ),
        "figure_and_caption_exist": figure_base.with_suffix(".png").is_file()
        and figure_base.with_suffix(".md").is_file(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    if not all(checks.values()):
        raise RuntimeError(f"M60 bounded-pilot validation failed: {checks}")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
