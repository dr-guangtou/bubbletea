"""Create a labeled Legacy Survey appearance atlas for the frozen UCD references."""

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.image import imread

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    UCD_LEGACY_REFERENCE_ATLAS_INDEX,
    UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST,
    UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP,
    UCD_LEGACY_REFERENCE_TARGETS,
    UCD_LEGACY_REFERENCE_TRACTOR_MATCHES,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.retrieve_m60_known_ucd_cutouts import local_path
from scripts.utils.plotting import save_figure, set_style

SCRIPT_PATH = "scripts/phase4_search/plot_ucd_legacy_reference_atlas.py"
COMMAND = "uv run python scripts/phase4_search/plot_ucd_legacy_reference_atlas.py"
PANELS_PER_PAGE = 100


def display_name(value: object) -> str:
    """Return a compact literature name without changing the source record."""
    if pd.isna(value) or not str(value).strip():
        return "unnamed literature object"
    return str(value).split(";")[0][:22]


def build_index() -> pd.DataFrame:
    """Join image and catalog evidence into a source-by-source atlas index."""
    targets = pd.read_csv(UCD_LEGACY_REFERENCE_TARGETS, dtype={"gaia_dr3_ids": str})
    cutouts = pd.read_csv(UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST)
    gaia = pd.read_csv(UCD_LEGACY_REFERENCE_GAIA_MEMBERSHIP, dtype={"source_id": str})
    tractor = pd.read_csv(UCD_LEGACY_REFERENCE_TRACTOR_MATCHES)
    closest = tractor.loc[tractor["selected_closest_match"]].copy()
    closest = closest[
        [
            "canonical_object_id",
            "ls_id",
            "dist_arcsec",
            "type",
            "maskbits",
            "fitbits",
            "mag_g",
            "mag_r",
            "mag_i",
            "mag_z",
            "sersic",
            "shape_r",
            "shape_e1",
            "shape_e2",
        ]
    ].rename(
        columns={
            column: f"closest_tractor_{column}"
            for column in closest.columns
            if column != "canonical_object_id"
        }
    )
    index = targets.merge(
        cutouts[
            [
                "canonical_object_id",
                "retrieval_status",
                "image_content_status",
                "file_path",
                "visual_interpretation_status",
            ]
        ],
        on="canonical_object_id",
        how="left",
        validate="1:1",
    )
    index = index.merge(
        gaia[
            [
                "canonical_object_id",
                "gaia_membership_result_status",
                "in_qso_candidates",
                "in_galaxy_candidates",
                "non_single_star",
            ]
        ],
        on="canonical_object_id",
        how="left",
        validate="1:1",
    ).merge(closest, on="canonical_object_id", how="left", validate="1:1")
    index.insert(0, "atlas_id", [f"UCD-REF-{number:04d}" for number in range(1, len(index) + 1)])
    index["atlas_inclusion_status"] = "not_shown_no_nonuniform_image"
    usable = index["image_content_status"].eq("nonuniform_image_content")
    index.loc[usable, "atlas_inclusion_status"] = "shown_in_atlas"
    index["atlas_page"] = pd.NA
    index["atlas_panel"] = pd.NA
    for cohort in index["reference_cohort"].drop_duplicates():
        cohort_rows = index.index[usable & index["reference_cohort"].eq(cohort)]
        for position, row_index in enumerate(cohort_rows):
            index.loc[row_index, "atlas_page"] = position // PANELS_PER_PAGE + 1
            index.loc[row_index, "atlas_panel"] = position % PANELS_PER_PAGE + 1
    return index


def render_pages(index: pd.DataFrame) -> None:
    """Render every nonuniform image without assigning a physical classification."""
    set_style()
    plt.rcParams.update(
        {"axes.grid": False, "font.family": "sans-serif", "font.size": 6, "axes.titlesize": 4.5}
    )
    for cohort, cohort_rows in index.loc[
        index["atlas_inclusion_status"].eq("shown_in_atlas")
    ].groupby("reference_cohort", sort=False):
        page_count = math.ceil(len(cohort_rows) / PANELS_PER_PAGE)
        for page_number in range(1, page_count + 1):
            rows = cohort_rows.loc[cohort_rows["atlas_page"].eq(page_number)]
            figure, axes = plt.subplots(10, 10, figsize=(12, 12))
            for axis in axes.flat:
                axis.set_axis_off()
            for axis, (_, row) in zip(axes.flat, rows.iterrows(), strict=False):
                axis.imshow(imread(local_path(row["file_path"])), origin="upper")
                axis.set_title(f"{row['atlas_id']}\n{display_name(row['original_names'])}", pad=1.0)
                axis.set_axis_off()
            readable_cohort = cohort.replace("_", " ")
            figure.suptitle(
                f"Legacy Survey UCD reference: {readable_cohort} — page {page_number} of {page_count}",
                fontsize=12,
            )
            figure.subplots_adjust(
                left=0.02, right=0.98, bottom=0.02, top=0.95, wspace=0.05, hspace=0.26
            )
            name = f"ucd_legacy_reference_{cohort}_page_{page_number:02d}_v1"
            save_figure(
                figure,
                name=name,
                phase=4,
                script_path=SCRIPT_PATH,
                command=COMMAND,
                data_source=(
                    "data/literature/catalogs/ucd_legacy_reference_atlas_index_v1.csv; "
                    "Legacy Survey DR10 three-color JPEG cutouts"
                ),
                title=f"UCD Legacy Survey appearance atlas: {readable_cohort}, page {page_number}",
                description=(
                    f"Page {page_number} of {page_count} for the {readable_cohort} cohort. "
                    "Each 16.768-arcsecond-wide image is centered on the literature coordinate "
                    "and labeled with a stable atlas identifier and a compact source name. "
                    "Only nonuniform JPEGs are shown. The images remain visually unclassified; "
                    "catalog membership and Legacy Survey model measurements are lookup evidence "
                    "in the atlas index, not automatic acceptance or rejection rules."
                ),
            )
            plt.close(figure)


def main() -> None:
    """Validate complete inputs, save the lookup index, and render the atlas."""
    summary_path = UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST.with_suffix(".json")
    summary = json.loads(summary_path.read_text())
    if summary["passed_count"] != summary["check_count"]:
        raise RuntimeError("UCD reference cutout checks did not pass")
    if calculate_sha256(UCD_LEGACY_REFERENCE_CUTOUT_MANIFEST) != summary["manifest_sha256"]:
        raise RuntimeError("UCD reference cutout manifest differs from its recorded digest")
    index = build_index()
    if len(index) != 724 or not index["atlas_id"].is_unique:
        raise RuntimeError("UCD Legacy reference atlas index is incomplete")
    index.to_csv(UCD_LEGACY_REFERENCE_ATLAS_INDEX, index=False)
    render_pages(index)


if __name__ == "__main__":
    main()
