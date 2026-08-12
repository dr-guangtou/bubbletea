"""Retrieve compact three-color Legacy Survey cutouts for the frozen UCD references."""

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
    UCD_LEGACY_REFERENCE_CONTRACT,
    UCD_LEGACY_REFERENCE_CUTOUT_DIR,
    UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST,
    UCD_LEGACY_REFERENCE_TARGETS,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.freeze_ucd_legacy_reference import CONTRACT_VERSION
from scripts.phase4_search.retrieve_m60_known_ucd_cutouts import cutout_url, output_path_text

logger = logging.getLogger(__name__)

CUTOUT_VERSION = "ucd_legacy_reference_cutouts_v1"
ENDPOINT = "https://www.legacysurvey.org/viewer/jpeg-cutout"
LAYER = "ls-dr10"
PIXEL_SCALE_ARCSEC = 0.262
SIZE_PIXELS = 64
FIELD_WIDTH_ARCSEC = PIXEL_SCALE_ARCSEC * SIZE_PIXELS
MINIMUM_REQUEST_INTERVAL_SECONDS = 0.25
MAXIMUM_ATTEMPTS = 3


def parse_arguments() -> argparse.Namespace:
    """Require explicit permission for image retrieval."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def valid_image(path: Path) -> bool:
    """Return whether an existing checkpoint is a readable 64-by-64 JPEG."""
    try:
        return path.read_bytes().startswith(b"\xff\xd8") and imread(path).shape[:2] == (
            SIZE_PIXELS,
            SIZE_PIXELS,
        )
    except (OSError, ValueError):
        return False


def request_image(url: str, object_id: str) -> tuple[bytes | None, str, str]:
    """Return image content or a preserved unavailable outcome after retries."""
    request = Request(url, headers={"User-Agent": "BubbleTea-UCD-Legacy-reference/1.0"})
    last_error = ""
    for attempt in range(1, MAXIMUM_ATTEMPTS + 1):
        try:
            with urlopen(request, timeout=120) as response:  # noqa: S310
                content = response.read()
                content_type = response.headers.get("Content-Type", "")
            if content.startswith(b"\xff\xd8"):
                return content, content_type, ""
            return None, content_type, "response_was_not_jpeg"
        except HTTPError as error:
            last_error = f"http_{error.code}"
            if error.code in {400, 404}:
                return None, "", last_error
        except (URLError, TimeoutError) as error:
            last_error = type(error).__name__
        if attempt < MAXIMUM_ATTEMPTS:
            time.sleep(2 ** (attempt - 1))
    logger.warning("Cutout unavailable for %s: %s", object_id, last_error)
    return None, "", last_error


def write_manifest(rows: list[dict[str, object]]) -> None:
    """Checkpoint every completed coordinate atomically."""
    temporary = UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST.with_suffix(".csv.tmp")
    pd.DataFrame(rows).to_csv(temporary, index=False)
    temporary.replace(UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST)


def main() -> None:
    """Retrieve or reuse every image and preserve unavailable outcomes."""
    if not parse_arguments().execute:
        raise RuntimeError("Legacy Survey image access requires --execute")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    contract = json.loads(UCD_LEGACY_REFERENCE_CONTRACT.read_text())
    if contract["contract_version"] != CONTRACT_VERSION:
        raise RuntimeError("UCD Legacy reference contract is not expected")
    if calculate_sha256(UCD_LEGACY_REFERENCE_TARGETS) != contract["target_output"]["sha256"]:
        raise RuntimeError("UCD Legacy reference targets differ from their frozen digest")
    targets = pd.read_csv(UCD_LEGACY_REFERENCE_TARGETS, dtype={"gaia_dr3_ids": str})
    UCD_LEGACY_REFERENCE_CUTOUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, row in targets.iterrows():
        object_id = row["canonical_object_id"]
        path = UCD_LEGACY_REFERENCE_CUTOUT_DIR / f"{object_id}_ls_dr10.jpg"
        url = cutout_url(
            ENDPOINT,
            float(row["adopted_ra"]),
            float(row["adopted_dec"]),
            PIXEL_SCALE_ARCSEC,
            SIZE_PIXELS,
            LAYER,
        )
        if valid_image(path):
            content = path.read_bytes()
            content_type = "image/jpeg"
            status = "reused_verified_checkpoint"
            error = ""
        else:
            if index:
                time.sleep(MINIMUM_REQUEST_INTERVAL_SECONDS)
            content, content_type, error = request_image(url, object_id)
            if content is None:
                status = "unavailable_or_non_jpeg"
            else:
                temporary = path.with_suffix(".jpg.tmp")
                temporary.write_bytes(content)
                if imread(temporary).shape[:2] != (SIZE_PIXELS, SIZE_PIXELS):
                    temporary.unlink(missing_ok=True)
                    content = None
                    status = "unusable_wrong_dimensions"
                    error = "unexpected_image_dimensions"
                else:
                    temporary.replace(path)
                    status = "downloaded_and_verified"
        rows.append(
            {
                "canonical_object_id": object_id,
                "reference_cohort": row["reference_cohort"],
                "classification_state": row["classification_state"],
                "original_names": row["original_names"],
                "host_galaxies": row["host_galaxies"],
                "ra_deg": row["adopted_ra"],
                "dec_deg": row["adopted_dec"],
                "survey": "Legacy Survey DR10",
                "layer": LAYER,
                "pixel_scale_arcsec": PIXEL_SCALE_ARCSEC,
                "size_pixels": SIZE_PIXELS,
                "field_width_arcsec": FIELD_WIDTH_ARCSEC,
                "url": url,
                "retrieval_status": status,
                "error_or_unavailable_reason": error,
                "content_type": content_type,
                "byte_count": len(content) if content is not None else 0,
                "file_path": output_path_text(path) if content is not None else "",
                "sha256": hashlib.sha256(content).hexdigest() if content is not None else "",
                "visual_interpretation_status": "not_reviewed",
            }
        )
        write_manifest(rows)
        if (index + 1) % 50 == 0:
            logger.info("Completed %d of %d UCD reference cutouts", index + 1, len(targets))

    manifest = pd.DataFrame(rows)
    available = manifest["retrieval_status"].isin(
        ["downloaded_and_verified", "reused_verified_checkpoint"]
    )
    checks = {
        "all_724_targets_have_outcomes": len(manifest) == len(targets) == 724,
        "target_identifiers_are_unique": manifest["canonical_object_id"].is_unique,
        "available_files_are_verified": all(
            valid_image(UCD_LEGACY_REFERENCE_CUTOUT_DIR / f"{object_id}_ls_dr10.jpg")
            for object_id in manifest.loc[available, "canonical_object_id"]
        ),
        "unavailable_outcomes_are_explicit": manifest.loc[~available, "retrieval_status"]
        .ne("")
        .all(),
        "all_images_remain_unreviewed": manifest["visual_interpretation_status"]
        .eq("not_reviewed")
        .all(),
        "image_absence_does_not_change_ucd_status": True,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    summary = {
        "cutout_version": CUTOUT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "complete_with_explicit_unavailable_outcomes",
        "target_count": len(manifest),
        "available_verified_count": int(available.sum()),
        "unavailable_or_unusable_count": int((~available).sum()),
        "counts_by_cohort_and_status": [
            {
                "reference_cohort": cohort,
                "retrieval_status": status,
                "count": int(count),
            }
            for (cohort, status), count in manifest.groupby(
                ["reference_cohort", "retrieval_status"]
            )
            .size()
            .items()
        ],
        "manifest_sha256": calculate_sha256(UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST),
        "check_count": len(checks),
        "passed_count": sum(checks.values()),
        "checks": checks,
    }
    summary_path = UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST.with_suffix(".json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not all(checks.values()):
        raise RuntimeError(f"UCD Legacy cutout retrieval failed: {checks}")


if __name__ == "__main__":
    main()
