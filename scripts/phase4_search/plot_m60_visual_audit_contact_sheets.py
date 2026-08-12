"""Create blinded contact sheets for the frozen M60 visual-audit sample."""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.image import imread

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.config import (
    M60_POSITIVE_CONTROL_AUDIT_CUTOUT_MANIFEST,
    M60_POSITIVE_CONTROL_AUDIT_CUTOUT_SUMMARY,
)
from scripts.phase1_literature.audit_reference_data import calculate_sha256
from scripts.phase4_search.retrieve_m60_known_ucd_cutouts import local_path
from scripts.utils.plotting import save_figure, set_style

SCRIPT_PATH = "scripts/phase4_search/plot_m60_visual_audit_contact_sheets.py"
COMMAND = "uv run python scripts/phase4_search/plot_m60_visual_audit_contact_sheets.py"
ZONE_LABELS = {
    "central_diagnostic_0_50_kpc": "0--50 kpc diagnostic region",
    "near_host_50_150_kpc": "50--150 kpc",
    "intermediate_150_300_kpc": "150--300 kpc",
    "far_300_600_kpc": "300--600 kpc",
}


def main() -> None:
    """Render one 10-by-10 sheet per zone without assigning interpretations."""
    summary = json.loads(M60_POSITIVE_CONTROL_AUDIT_CUTOUT_SUMMARY.read_text())
    if summary["passed_count"] != summary["check_count"]:
        raise RuntimeError("M60 audit cutout checks did not pass")
    if calculate_sha256(M60_POSITIVE_CONTROL_AUDIT_CUTOUT_MANIFEST) != summary["manifest_sha256"]:
        raise RuntimeError("M60 audit cutout manifest differs from its recorded digest")
    manifest = pd.read_csv(
        M60_POSITIVE_CONTROL_AUDIT_CUTOUT_MANIFEST,
        dtype={"source_id": str},
    )
    set_style()
    plt.rcParams.update(
        {
            "axes.grid": False,
            "font.family": "sans-serif",
            "font.size": 7,
            "axes.titlesize": 5,
        }
    )
    for zone_name, zone_label in ZONE_LABELS.items():
        rows = manifest.loc[manifest["audit_radial_zone"].eq(zone_name)].sort_values(
            "audit_sample_id"
        )
        if len(rows) != 100:
            raise RuntimeError(f"Expected 100 cutouts for {zone_name}")
        figure, axes = plt.subplots(10, 10, figsize=(12, 12))
        for axis, (_, row) in zip(axes.flat, rows.iterrows(), strict=True):
            axis.imshow(imread(local_path(row["file_path"])), origin="upper")
            axis.set_title(row["audit_sample_id"], pad=1.0)
            axis.set_xticks([])
            axis.set_yticks([])
            for spine in axis.spines.values():
                spine.set_visible(False)
        figure.suptitle(f"M60 representative visual audit: {zone_label}", fontsize=13)
        figure.subplots_adjust(
            left=0.02, right=0.98, bottom=0.02, top=0.95, wspace=0.06, hspace=0.22
        )
        name = f"m60_visual_audit_{zone_name}_v1"
        save_figure(
            figure,
            name=name,
            phase=4,
            script_path=SCRIPT_PATH,
            command=COMMAND,
            data_source=(
                "data/results/radial_search/"
                "m60_positive_control_visual_audit_cutouts_v1.csv; "
                "Legacy Survey DR10 Viewer JPEG cutout service"
            ),
            title=f"M60 visual audit contact sheet: {zone_label}",
            description=(
                f"Blinded contact sheet for the 100 randomly selected M60 sources in "
                f"the {zone_label} radial zone. Each three-color Legacy Survey DR10 "
                "cutout is 16.768 arcseconds wide and is labeled only by its permanent "
                "audit identifier. The sheet omits Gaia score, magnitude, and candidate "
                "priority to limit review bias. Images remain unreviewed when this "
                "figure is generated; the contact sheet neither assigns contamination "
                "flags nor changes the Gaia radial profile."
            ),
        )
        plt.close(figure)


if __name__ == "__main__":
    main()
