"""Detailed audit and summary of the target galaxy sample.

This script performs a deep dive into the properties of the ranked galaxy
sample, focusing on distance provenance, data completeness, and
spatial distribution.
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scripts.config import GALAXY_SAMPLE_CSV, FIGURES_DIR
from scripts.utils.plotting import set_style, save_figure

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def perform_audit():
    """Load and audit the target galaxy sample."""
    if not GALAXY_SAMPLE_CSV.exists():
        logger.error(f"Galaxy sample file not found: {GALAXY_SAMPLE_CSV}")
        return

    df = pd.read_csv(GALAXY_SAMPLE_CSV)
    n_total = len(df)
    logger.info(f"Auditing {n_total} galaxies from {GALAXY_SAMPLE_CSV}")

    # 1. Distance Provenance
    logger.info("\n[1] Distance Provenance Summary:")
    if 'dist_source' in df.columns:
        source_counts = df['dist_source'].value_counts()
        for src, count in source_counts.items():
            logger.info(f"  {src:<10}: {count:>5} ({count/n_total*100:.1f}%)")

    # 2. Morphological Completeness
    logger.info("\n[2] Morphological Completeness (T-Type):")
    if 'ttype_lvg' in df.columns:
        unknown_mask = df['ttype_lvg'].isna()
        n_unknown = unknown_mask.sum()
        logger.info(f"  Classified: {n_total - n_unknown:>5} ({(n_total - n_unknown)/n_total*100:.1f}%)")
        logger.info(f"  Unknown:    {n_unknown:>5} ({n_unknown/n_total*100:.1f}%)")

        # Distribution of types among those known
        valid_t = df.loc[~unknown_mask, 'ttype_lvg']
        logger.info(f"  Early-type (T < 0):  {(valid_t < 0).sum()}")
        logger.info(f"  Intermediate (T=0): {(valid_t == 0).sum()}")
        logger.info(f"  Late-type (T > 0):   {(valid_t > 0).sum()}")

    # 3. Spatial Distribution (Galactic Latitude)
    logger.info("\n[3] Galactic Latitude Distribution:")
    if 'glat' in df.columns:
        logger.info(df['glat'].describe())
        low_b = (df['glat'].abs() < 20).sum()
        logger.info(f"  Low latitude (|b| < 20 deg): {low_b} ({(low_b/n_total)*100:.1f}%)")

    # 4. Luminosity Check
    logger.info("\n[4] Luminosity Check (log L_K):")
    if 'log_L_K' in df.columns:
        missing_l = df['log_L_K'].isna().sum()
        logger.info(f"  Missing log_L_K: {missing_l}")

    # Generate Audit Figures
    set_style()

    # Figure: Distance vs Luminosity
    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(df['dist_best'], df['log_L_K'],
                         c=df['glat'].abs(), cmap='magma',
                         alpha=0.5, s=30)
    cbar = plt.colorbar(scatter)
    cbar.set_label('|Galactic Latitude| (deg)')

    ax.set_xlabel('Best Distance (Mpc)')
    ax.set_ylabel('$\log_{10}(L_K / L_\odot)$')
    ax.set_title('Galaxy Sample: Luminosity vs Distance')
    ax.grid(True, alpha=0.3)

    save_figure(
        fig, "sample_dist_vs_lum", phase=2,
        script_path="scripts/phase2_galaxy_sample/compile_sample.py",
        command="PYTHONPATH=. uv run python scripts/phase2_galaxy_sample/compile_sample.py",
        data_source="galaxy_sample_ranked.csv",
        description="Distribution of target galaxies in distance-luminosity space. "
                    "The sample is restricted to D < 25 Mpc and is color-coded by "
                    "galactic latitude to highlight objects near the plane."
    )
    plt.close(fig)

if __name__ == "__main__":
    perform_audit()
