"""Analyze Gaia properties of the literature UCD collection.

Generates diagnostic plots to characterize UCD properties (AEN, color,
magnitude, excess noise significance, and BR excess factor) as a function
of distance, establishing the baseline for new UCD candidate selection.
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scripts.config import LITERATURE_DB
from scripts.phase1_literature.ucd_database import get_db_connection
from scripts.utils.plotting import set_style, save_figure

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Command used to run this script (for figure metadata)
COMMAND = "PYTHONPATH=. uv run python scripts/phase1_literature/analyze_gaia_properties.py"

def load_data():
    """Load UCD objects with Gaia data from the database."""
    conn = get_db_connection()
    query = """
        SELECT
            o.object_id, o.source_id, o.ra, o.dec, o.distance_mpc,
            o.gaia_g_mag, o.gaia_bp_rp, o.gaia_aen, o.gaia_aen_sig,
            o.gaia_ruwe, o.gaia_br_excess, o.gaia_prob_galaxy,
            o.gaia_prob_star, o.gaia_dr3_id, s.year
        FROM ucd_objects o
        JOIN ucd_sources s ON o.source_id = s.source_id
        WHERE o.gaia_dr3_id IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    logger.info(f"Loaded {len(df)} UCDs with Gaia data")
    return df

def plot_aen_vs_distance(df: pd.DataFrame):
    """Plot Astrometric Excess Noise (AEN) distribution vs distance."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Filter out sources with no distance info (or set to 0/NaN)
    df_dist = df[df['distance_mpc'].notnull() & (df['distance_mpc'] > 0)]

    if df_dist.empty:
        logger.warning("No distance data for AEN vs Distance plot")
        plt.close(fig)
        return

    distances = sorted(df_dist['distance_mpc'].unique())
    data_to_plot = [df_dist[df_dist['distance_mpc'] == d]['gaia_aen'].dropna() for d in distances]

    ax.boxplot(data_to_plot, tick_labels=[f"{d:.1f}" for d in distances])
    ax.set_yscale('log')
    ax.set_xlabel('Distance (Mpc)')
    ax.set_ylabel('Gaia AEN (mas)')
    ax.set_title('UCD Gaia Astrometric Excess Noise vs Distance')

    ax.axhline(0.5, color='r', linestyle='--', alpha=0.5, label='Common threshold (0.5 mas)')
    ax.legend()

    save_figure(
        fig, "aen_vs_distance", phase=1,
        script_path="scripts/phase1_literature/analyze_gaia_properties.py",
        command=COMMAND,
        data_source="ucd_collection.db (Gaia DR3)",
        description="Gaia AEN vs distance. UCDs at >50 Mpc (like Coma) tend to have AEN closer to 0.5 mas."
    )
    plt.close(fig)

def plot_selection_criteria_stats(df: pd.DataFrame):
    """Plot histograms of potential selection criteria: AEN_sig and BR_excess."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # AEN Significance
    axes[0].hist(df['gaia_aen_sig'].dropna(), bins=30, alpha=0.7, color='C0')
    axes[0].set_xlabel('AEN Significance ($D$)')
    axes[0].set_ylabel('Count')
    axes[0].set_title('Astrometric Excess Noise Significance')
    axes[0].axvline(2.0, color='r', linestyle='--', label='D=2 threshold')
    axes[0].legend()

    # BP-RP Excess Factor
    axes[1].hist(df['gaia_br_excess'].dropna(), bins=30, alpha=0.7, color='C1')
    axes[1].set_xlabel('Phot. BP-RP Excess Factor')
    axes[1].set_ylabel('Count')
    axes[1].set_title('BP-RP Excess Factor')
    # Typically 1.0 + 0.015*color^2 is expected for stars
    axes[1].axvline(1.5, color='r', linestyle='--', label='Likely extended (>1.5)')
    axes[1].legend()

    plt.tight_layout()
    save_figure(
        fig, "selection_criteria_qa", phase=1,
        script_path="scripts/phase1_literature/analyze_gaia_properties.py",
        command=COMMAND,
        data_source="ucd_collection.db (Gaia DR3)",
        description="QA of additional Gaia selection criteria: AEN significance and BP-RP excess factor. "
                    "Most UCDs show highly significant excess noise (D > 2) and elevated BR excess factors."
    )
    plt.close(fig)

def plot_negative_test(df: pd.DataFrame):
    """Plot AEN for the z=0.034 sample as a negative test."""
    blakeslee_id = "2008AJ....136.2295B"
    df_neg = df[df['source_id'] == blakeslee_id]

    if df_neg.empty:
        logger.info("No data for Blakeslee 2008 negative test")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.hist(df_neg['gaia_aen'].dropna(), bins=10, alpha=0.7, color='gray', label='Abell S0740 (z=0.034)')
    ax.axvline(0.5, color='r', linestyle='--', label='Threshold (0.5 mas)')
    ax.set_xlabel('Gaia AEN (mas)')
    ax.set_ylabel('Count')
    ax.set_title('Negative Test: UCDs at High Redshift (z=0.034)')
    ax.legend()

    save_figure(
        fig, "negative_test_aen", phase=1,
        script_path="scripts/phase1_literature/analyze_gaia_properties.py",
        command=COMMAND,
        data_source="ucd_collection.db (Gaia DR3)",
        description="AEN distribution for UCD candidates at z=0.034. These should be mostly undetected "
                    "or have very low AEN as they are beyond Gaia's resolution limit."
    )
    plt.close(fig)

def main():
    set_style()
    df = load_data()

    if df.empty:
        logger.error("No data available for analysis.")
        return

    plot_aen_vs_distance(df)
    plot_selection_criteria_stats(df)
    plot_negative_test(df)

    # Also generate the standard distributions
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    axes[0].hist(df['gaia_aen'].dropna(), bins=np.logspace(-1, 2, 30), alpha=0.7)
    axes[0].set_xscale('log')
    axes[0].set_xlabel('AEN (mas)')
    axes[1].hist(df['gaia_bp_rp'].dropna(), bins=30, alpha=0.7)
    axes[1].set_xlabel('BP - RP (mag)')
    axes[2].hist(df['gaia_g_mag'].dropna(), bins=30, alpha=0.7)
    axes[2].set_xlabel('G (mag)')
    axes[3].hist(df['gaia_ruwe'].dropna(), bins=30, range=(0, 5), alpha=0.7)
    axes[3].set_xlabel('RUWE')
    plt.tight_layout()
    save_figure(fig, "property_distributions_v2", phase=1, script_path="scripts/phase1_literature/analyze_gaia_properties.py", command=COMMAND, data_source="ucd_collection.db (Gaia DR3)", description="Updated distributions with expanded sample.")
    plt.close(fig)

    logger.info("Analysis complete. Expanded figures saved.")

if __name__ == "__main__":
    main()
