"""Retrieve compact Legacy Survey DR10 cutouts for the two known M60 UCD controls."""

import argparse
import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.image import imread

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    M60_KNOWN_UCD_CUTOUT_DIR,
    M60_KNOWN_UCD_CUTOUT_MANIFEST,
    M60_KNOWN_UCD_CUTOUT_SUMMARY,
    M60_POSITIVE_CONTROL_CONTRACT,
    M60_POSITIVE_CONTROL_KNOWN_OBJECTS,
    PROJECT_ROOT,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.freeze_m60_positive_control import CONTRACT_VERSION
from scripts.utils.plotting import save_figure, set_style

logger = logging.getLogger(__name__)

SCRIPT_PATH = "scripts/phase4_search/retrieve_m60_known_ucd_cutouts.py"
COMMAND = (
    "BUBBLETEA_EXTERNAL_DATA=~/Dropbox/work/data uv run python "
    "scripts/phase4_search/retrieve_m60_known_ucd_cutouts.py --execute"
)


def parse_arguments() -> argparse.Namespace:
    """Require explicit permission for image retrieval."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def output_path_text(path: Path) -> str:
    """Return a repository-relative path or an absolute external path."""
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def cutout_url(
    endpoint: str,
    ra: float,
    dec: float,
    pixel_scale_arcsec: float,
    size_pixels: int,
    layer: str,
) -> str:
    """Build one exact three-color Legacy Survey cutout URL."""
    parameters = urlencode(
        {
            "ra": f"{ra:.12f}",
            "dec": f"{dec:.12f}",
            "pixscale": f"{pixel_scale_arcsec:.3f}",
            "width": size_pixels,
            "height": size_pixels,
            "layer": layer,
        }
    )
    return f"{endpoint}?{parameters}"


def render_montage(rows: pd.DataFrame) -> None:
    """Create a two-panel visual check of the known-UCD cutouts."""
    set_style()
    plt.rcParams.update({"axes.grid": False, "font.family": "sans-serif"})
    figure, axes = plt.subplots(1, len(rows), figsize=(5.6, 3.0), squeeze=False)
    for axis, (_, row) in zip(axes[0], rows.iterrows(), strict=True):
        image = imread(row["file_path"])
        axis.imshow(image, origin="upper")
        axis.set_title(
            f"{row['original_names']}\n{row['projected_radius_kpc']:.1f} kpc",
            fontsize=9,
        )
        axis.set_xticks([])
        axis.set_yticks([])
        for spine in axis.spines.values():
            spine.set_visible(False)
    figure.suptitle("M60 reliable-UCD controls: Legacy Survey DR10", fontsize=11)
    figure.tight_layout()
    save_figure(
        figure,
        name="m60_known_ucd_legacy_cutouts_v1",
        phase=4,
        script_path=SCRIPT_PATH,
        command=COMMAND,
        data_source=(
            "data/results/radial_search/m60_positive_control_known_objects_v1.csv; "
            "Legacy Survey DR10 Viewer JPEG cutout service"
        ),
        title="M60 known-UCD Legacy Survey cutout pilot",
        description=(
            "Compact three-color Legacy Survey DR10 cutouts centered on the two reliable "
            "M60 UCD controls. Each field is 64 by 64 pixels at 0.262 arcseconds per "
            "pixel, or 16.768 arcseconds wide. These development controls test cutout "
            "scale and coverage; they are not independent selector validation. Visual "
            "appearance is review evidence only and does not change the Gaia radial "
            "profile, coverage, or area accounting."
        ),
    )
    plt.close(figure)


def main() -> None:
    """Retrieve, verify, record, and plot the two frozen image controls."""
    if not parse_arguments().execute:
        raise RuntimeError("Legacy Survey retrieval requires --execute")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    contract = json.loads(M60_POSITIVE_CONTROL_CONTRACT.read_text())
    if contract["contract_version"] != CONTRACT_VERSION:
        raise RuntimeError("M60 positive-control contract is not expected")
    known_digest = contract["known_objects"]["artifact_sha256"]
    if calculate_sha256(M60_POSITIVE_CONTROL_KNOWN_OBJECTS) != known_digest:
        raise RuntimeError("M60 known-object table differs from its frozen digest")
    review = contract["visual_review"]
    known = pd.read_csv(
        M60_POSITIVE_CONTROL_KNOWN_OBJECTS,
        dtype={"gaia_dr3_ids": str},
    )
    controls = known.loc[
        known["positive_control_role"].eq("reliable_confirmed_ucd")
        & known["gaia_identifier_count"].eq(1)
    ].copy()
    if len(controls) != 2:
        raise RuntimeError("Expected exactly two frozen M60 UCD image controls")

    M60_KNOWN_UCD_CUTOUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    for _, row in controls.iterrows():
        source_id = row["gaia_dr3_ids"]
        url = cutout_url(
            review["endpoint"],
            row["adopted_ra"],
            row["adopted_dec"],
            review["pixel_scale_arcsec"],
            review["size_pixels"],
            review["layer"],
        )
        request = Request(url, headers={"User-Agent": "BubbleTea-M60-positive-control/1.0"})
        with urlopen(request, timeout=120) as response:  # noqa: S310
            content = response.read()
            content_type = response.headers.get("Content-Type", "")
        if not content.startswith(b"\xff\xd8"):
            raise RuntimeError(f"Legacy Survey did not return JPEG data for {source_id}")
        path = M60_KNOWN_UCD_CUTOUT_DIR / f"{source_id}_ls_dr10.jpg"
        path.write_bytes(content)
        image = imread(path)
        if image.shape[:2] != (review["size_pixels"], review["size_pixels"]):
            raise RuntimeError(f"Unexpected cutout dimensions for {source_id}: {image.shape}")
        manifest_rows.append(
            {
                "canonical_object_id": row["canonical_object_id"],
                "original_names": row["original_names"],
                "gaia_dr3_id": source_id,
                "ra_deg": row["adopted_ra"],
                "dec_deg": row["adopted_dec"],
                "projected_radius_kpc": row["projected_radius_kpc"],
                "survey": review["survey"],
                "layer": review["layer"],
                "pixel_scale_arcsec": review["pixel_scale_arcsec"],
                "width_pixels": review["size_pixels"],
                "height_pixels": review["size_pixels"],
                "field_width_arcsec": review["field_width_arcsec"],
                "url": url,
                "content_type": content_type,
                "byte_count": len(content),
                "file_path": output_path_text(path),
                "sha256": hashlib.sha256(content).hexdigest(),
                "interpretation_status": "visual_review_control_not_physical_classification",
            }
        )
    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(M60_KNOWN_UCD_CUTOUT_MANIFEST, index=False)
    render_montage(manifest)
    summary = {
        "cutout_version": "m60_known_ucd_legacy_cutouts_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "known_ucd_cutout_pilot_complete",
        "target_count": len(manifest),
        "file_count": len(manifest),
        "survey": review["survey"],
        "layer": review["layer"],
        "three_color_image": review["three_color_image"],
        "pixel_scale_arcsec": review["pixel_scale_arcsec"],
        "size_pixels": review["size_pixels"],
        "field_width_arcsec": review["field_width_arcsec"],
        "scientific_limits": [
            "known_ucds_are_development_controls_not_independent_validation",
            "jpeg_cutouts_do_not_establish_catalog_mask_or_fit_quality",
            "visual_review_flags_do_not_remove_sources_from_gaia_profile",
            "legacy_imaging_does_not_change_gaia_area_accounting",
        ],
        "inputs": {
            "m60_contract_sha256": calculate_sha256(M60_POSITIVE_CONTROL_CONTRACT),
            "known_objects_sha256": calculate_sha256(M60_POSITIVE_CONTROL_KNOWN_OBJECTS),
            "manifest_sha256": calculate_sha256(M60_KNOWN_UCD_CUTOUT_MANIFEST),
        },
        "files": manifest[["gaia_dr3_id", "file_path", "sha256"]].to_dict("records"),
    }
    M60_KNOWN_UCD_CUTOUT_SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    logger.info("Retrieved %d compact DR10 cutouts", len(manifest))


if __name__ == "__main__":
    main()
