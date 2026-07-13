"""Consistent plotting utilities for the BubbleTea project.

Includes matplotlib style defaults and a helper to save figures with
companion markdown metadata.
"""

import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

def set_style():
    """Set global matplotlib style for publication-quality figures."""
    plt.rcParams.update({
        "figure.figsize": (8, 6),
        "font.size": 12,
        "axes.labelsize": 14,
        "axes.titlesize": 14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 12,
        "figure.titlesize": 16,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "savefig.bbox": "tight",
        "savefig.dpi": 300,
        "font.family": "serif",
    })

def save_figure(
    fig: plt.Figure,
    name: str,
    phase: int,
    script_path: str,
    command: str,
    data_source: str,
    description: str,
    title: Optional[str] = None
):
    """Save figure as PNG and create companion markdown file.

    Args:
        fig: The matplotlib figure object.
        name: Descriptive name for the figure (e.g., 'aen_distribution').
        phase: Research phase number (e.g., 1).
        script_path: Relative path to the script that generated the figure.
        command: The full command used to run the script.
        data_source: Description of data used (e.g., 'Gaia DR3', 'ucd_collection.db').
        description: Detailed explanation of what the figure shows.
        title: Optional title for the figure in the markdown file.
    """
    from scripts.config import FIGURES_DIR

    # Ensure directory exists
    phase_dir = FIGURES_DIR / f"phase{phase}"
    phase_dir.mkdir(parents=True, exist_ok=True)

    # Filenames
    png_path = phase_dir / f"{name}.png"
    md_path = phase_dir / f"{name}.md"

    # Save PNG
    fig.savefig(png_path)
    logger.info(f"Saved figure to {png_path}")

    # Prepare Markdown content
    date_str = datetime.now().strftime("%Y-%m-%d")
    title_str = title or name.replace("_", " ").title()

    md_content = f"""# Figure: {title_str}

**Script:** `{script_path}`
**Command:** `{command}`
**Data:** `{data_source}`
**Date:** {date_str}

**Description:**
{description}
"""

    # Save MD
    with open(md_path, "w") as f:
        f.write(md_content)
    logger.info(f"Saved metadata to {md_path}")
