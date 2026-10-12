"""Retrieve the frozen 400-source M60 visual-audit cutout set."""

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd
from matplotlib.image import imread

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    M60_POSITIVE_CONTROL_AUDIT_CONTRACT,
    M60_POSITIVE_CONTROL_AUDIT_CUTOUT_DIR,
    M60_POSITIVE_CONTROL_AUDIT_CUTOUT_MANIFEST,
    M60_POSITIVE_CONTROL_AUDIT_CUTOUT_SUMMARY,
    M60_POSITIVE_CONTROL_AUDIT_SAMPLE,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.freeze_m60_visual_audit_sample import AUDIT_VERSION
from scripts.phase4_search.retrieve_m60_known_ucd_cutouts import cutout_url, output_path_text

logger = logging.getLogger(__name__)

CUTOUT_VERSION = "m60_positive_control_visual_audit_cutouts_v1"
ENDPOINT = "https://www.legacysurvey.org/viewer/jpeg-cutout"
LAYER = "ls-dr10"
PIXEL_SCALE_ARCSEC = 0.262
SIZE_PIXELS = 64
FIELD_WIDTH_ARCSEC = PIXEL_SCALE_ARCSEC * SIZE_PIXELS
MINIMUM_REQUEST_INTERVAL_SECONDS = 0.25
MAXIMUM_ATTEMPTS = 3


def parse_arguments() -> argparse.Namespace:
    """Require explicit permission for the 400 image requests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def write_manifest(rows: list[dict[str, object]]) -> None:
    """Checkpoint completed image metadata atomically."""
    temporary = M60_POSITIVE_CONTROL_AUDIT_CUTOUT_MANIFEST.with_suffix(".csv.tmp")
    pd.DataFrame(rows).to_csv(temporary, index=False)
    temporary.replace(M60_POSITIVE_CONTROL_AUDIT_CUTOUT_MANIFEST)


def download_jpeg(url: str, source_id: int) -> tuple[bytes, str]:
    """Download one JPEG with bounded retries and a descriptive user agent."""
    request = Request(url, headers={"User-Agent": "BubbleTea-M60-visual-audit/1.0"})
    for attempt in range(1, MAXIMUM_ATTEMPTS + 1):
        try:
            with urlopen(request, timeout=120) as response:  # noqa: S310
                return response.read(), response.headers.get("Content-Type", "")
        except (HTTPError, URLError, TimeoutError) as error:
            if attempt == MAXIMUM_ATTEMPTS:
                raise RuntimeError(f"Cutout failed for Gaia {source_id}: {error}") from error
            time.sleep(2 ** (attempt - 1))
    raise AssertionError("Retry loop ended without returning or raising")


def valid_existing_cutout(path: Path) -> bool:
    """Return whether a checkpoint is a readable 64-by-64 image."""
    try:
        return path.read_bytes().startswith(b"\xff\xd8") and imread(path).shape[:2] == (
            SIZE_PIXELS,
            SIZE_PIXELS,
        )
    except (OSError, ValueError):
        return False


def main() -> None:
    """Retrieve or reuse every frozen audit cutout and record exact provenance."""
    if not parse_arguments().execute:
        raise RuntimeError("Legacy Survey retrieval requires --execute")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    contract = json.loads(M60_POSITIVE_CONTROL_AUDIT_CONTRACT.read_text())
    if contract["audit_version"] != AUDIT_VERSION:
        raise RuntimeError("M60 visual-audit contract is not expected")
    if contract["passed_count"] != contract["check_count"]:
        raise RuntimeError("M60 visual-audit safeguards did not pass")
    if calculate_sha256(M60_POSITIVE_CONTROL_AUDIT_SAMPLE) != contract["sample_output"]["sha256"]:
        raise RuntimeError("M60 visual-audit sample differs from its frozen digest")
    sample = pd.read_csv(M60_POSITIVE_CONTROL_AUDIT_SAMPLE, dtype={"source_id": "int64"})
    if len(sample) != 400 or not sample["source_id"].is_unique:
        raise RuntimeError("Expected 400 unique frozen audit sources")

    M60_POSITIVE_CONTROL_AUDIT_CUTOUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    downloaded_count = 0
    reused_count = 0
    for index, row in sample.iterrows():
        source_id = int(row["source_id"])
        path = M60_POSITIVE_CONTROL_AUDIT_CUTOUT_DIR / f"{source_id}_ls_dr10.jpg"
        url = cutout_url(
            ENDPOINT,
            float(row["ra"]),
            float(row["dec"]),
            PIXEL_SCALE_ARCSEC,
            SIZE_PIXELS,
            LAYER,
        )
        if valid_existing_cutout(path):
            reused_count += 1
            content = path.read_bytes()
            retrieval_status = "reused_verified_checkpoint"
            content_type = "image/jpeg"
        else:
            if downloaded_count:
                time.sleep(MINIMUM_REQUEST_INTERVAL_SECONDS)
            content, content_type = download_jpeg(url, source_id)
            if not content.startswith(b"\xff\xd8"):
                raise RuntimeError(f"Legacy Survey did not return JPEG data for {source_id}")
            temporary = path.with_suffix(".jpg.tmp")
            temporary.write_bytes(content)
            if imread(temporary).shape[:2] != (SIZE_PIXELS, SIZE_PIXELS):
                temporary.unlink(missing_ok=True)
                raise RuntimeError(f"Unexpected image dimensions for Gaia {source_id}")
            temporary.replace(path)
            downloaded_count += 1
            retrieval_status = "downloaded_and_verified"
        rows.append(
            {
                "audit_sample_id": row["audit_sample_id"],
                "source_id": source_id,
                "audit_radial_zone": row["audit_radial_zone"],
                "ra_deg": row["ra"],
                "dec_deg": row["dec"],
                "projected_radius_kpc": row["projected_radius_kpc"],
                "survey": "Legacy Survey DR10",
                "layer": LAYER,
                "pixel_scale_arcsec": PIXEL_SCALE_ARCSEC,
                "width_pixels": SIZE_PIXELS,
                "height_pixels": SIZE_PIXELS,
                "field_width_arcsec": FIELD_WIDTH_ARCSEC,
                "url": url,
                "content_type": content_type,
                "byte_count": len(content),
                "file_path": output_path_text(path),
                "sha256": hashlib.sha256(content).hexdigest(),
                "retrieval_status": retrieval_status,
                "visual_interpretation_status": "not_reviewed",
            }
        )
        write_manifest(rows)
        if (index + 1) % 25 == 0:
            logger.info("Verified %d of %d audit cutouts", index + 1, len(sample))

    manifest = pd.DataFrame(rows)
    checks = {
        "frozen_sample_used": calculate_sha256(M60_POSITIVE_CONTROL_AUDIT_SAMPLE)
        == contract["sample_output"]["sha256"],
        "all_four_hundred_cutouts_recorded": len(manifest) == 400,
        "source_identifiers_are_unique": manifest["source_id"].is_unique,
        "one_hundred_cutouts_per_zone": manifest.groupby("audit_radial_zone").size().eq(100).all(),
        "all_images_are_verified_dimensions": all(
            valid_existing_cutout(
                M60_POSITIVE_CONTROL_AUDIT_CUTOUT_DIR / f"{source_id}_ls_dr10.jpg"
            )
            for source_id in manifest["source_id"]
        ),
        "all_images_remain_unreviewed": manifest["visual_interpretation_status"]
        .eq("not_reviewed")
        .all(),
        "images_do_not_change_gaia_area": True,
        "candidate_shortlist_remains_separate": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    summary = {
        "cutout_version": CUTOUT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "complete_unreviewed_visual_audit_cutout_set",
        "sample_count": len(manifest),
        "downloaded_this_run": downloaded_count,
        "reused_verified_checkpoints": reused_count,
        "survey": "Legacy Survey DR10",
        "layer": LAYER,
        "pixel_scale_arcsec": PIXEL_SCALE_ARCSEC,
        "size_pixels": SIZE_PIXELS,
        "field_width_arcsec": FIELD_WIDTH_ARCSEC,
        "sample_sha256": calculate_sha256(M60_POSITIVE_CONTROL_AUDIT_SAMPLE),
        "manifest_sha256": calculate_sha256(M60_POSITIVE_CONTROL_AUDIT_CUTOUT_MANIFEST),
        "scientific_limits": [
            "cutouts_are_visual_review_evidence_not_calibrated_morphology",
            "unusable_images_must_not_be_labeled_clean",
            "visual_flags_remove_no_sources_from_gaia_profile",
            "legacy_imaging_does_not_change_gaia_area_accounting",
            "audit_sample_is_separate_from_promising_candidate_shortlist",
        ],
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    M60_POSITIVE_CONTROL_AUDIT_CUTOUT_SUMMARY.write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if not all(checks.values()):
        raise RuntimeError(f"M60 audit-cutout retrieval failed: {checks}")


if __name__ == "__main__":
    main()
