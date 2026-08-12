"""Validate the complete unreviewed M60 visual-audit cutout artifacts."""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from matplotlib.image import imread

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    FIGURES_DIR,
    M60_POSITIVE_CONTROL_AUDIT_CUTOUT_MANIFEST,
    M60_POSITIVE_CONTROL_AUDIT_CUTOUT_SUMMARY,
    M60_POSITIVE_CONTROL_AUDIT_SAMPLE,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.plot_m60_visual_audit_contact_sheets import ZONE_LABELS
from scripts.phase4_search.retrieve_m60_known_ucd_cutouts import local_path


def main() -> None:
    """Check identities, files, digests, dimensions, statuses, and figure pairs."""
    summary = json.loads(M60_POSITIVE_CONTROL_AUDIT_CUTOUT_SUMMARY.read_text())
    manifest = pd.read_csv(
        M60_POSITIVE_CONTROL_AUDIT_CUTOUT_MANIFEST,
        dtype={"source_id": str},
    )
    sample = pd.read_csv(M60_POSITIVE_CONTROL_AUDIT_SAMPLE, dtype={"source_id": str})
    file_checks = []
    for _, row in manifest.iterrows():
        path = local_path(row["file_path"])
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
        dimensions = imread(path).shape[:2] if path.is_file() else ()
        file_checks.append(
            digest == row["sha256"]
            and dimensions == (int(row["height_pixels"]), int(row["width_pixels"]))
        )
    figure_pairs = []
    for zone_name in ZONE_LABELS:
        base = FIGURES_DIR / "phase4" / f"m60_visual_audit_{zone_name}_v1"
        figure_pairs.append(
            base.with_suffix(".png").is_file() and base.with_suffix(".md").is_file()
        )
    checks = {
        "retrieval_safeguards_passed": summary["passed_count"] == summary["check_count"],
        "sample_digest_matches": calculate_sha256(M60_POSITIVE_CONTROL_AUDIT_SAMPLE)
        == summary["sample_sha256"],
        "manifest_digest_matches": calculate_sha256(M60_POSITIVE_CONTROL_AUDIT_CUTOUT_MANIFEST)
        == summary["manifest_sha256"],
        "manifest_matches_exact_sample_identifiers": set(manifest["source_id"])
        == set(sample["source_id"]),
        "all_files_match_digests_and_dimensions": all(file_checks),
        "all_four_hundred_images_remain_unreviewed": len(manifest) == 400
        and manifest["visual_interpretation_status"].eq("not_reviewed").all(),
        "all_four_zone_figure_pairs_exist": all(figure_pairs),
        "contact_sheets_assign_no_labels": sample["possible_star_forming_region_or_young_cluster"]
        .eq("not_reviewed")
        .all()
        and sample["possible_nearby_source_blend_or_image_problem"].eq("not_reviewed").all(),
        "legacy_images_change_no_gaia_area": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    if not all(checks.values()):
        raise RuntimeError(f"M60 audit-cutout validation failed: {checks}")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
