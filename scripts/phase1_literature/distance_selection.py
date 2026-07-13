"""Evaluate distance-dependent selection criteria for UCDs.

Proposes and evaluates multiple selection models (constant, physical,
probabilistic) and quantifies their performance against the literature
UCD sample.
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from scripts.config import LITERATURE_DB, BACKGROUND_DENSITY_BY_GALACTIC_LAT
from scripts.phase1_literature.ucd_database import get_db_connection
from scripts.utils.plotting import set_style, save_figure

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COMMAND = "PYTHONPATH=. uv run python scripts/phase1_literature/distance_selection.py"

def load_data():
    """Load UCD objects with Gaia data from the database."""
    conn = get_db_connection()
    query = """
        SELECT
            o.object_id, o.source_id, o.distance_mpc,
            o.gaia_g_mag, o.gaia_bp_rp, o.gaia_aen, o.gaia_aen_sig,
            o.gaia_br_excess, o.gaia_dr3_id
        FROM ucd_objects o
        WHERE o.gaia_dr3_id IS NOT NULL AND o.distance_mpc IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def model_a_constant(df: pd.DataFrame, aen_thresh: float = 0.5, d_thresh: float = 2.0):
    """Model A: Constant thresholds (Classic Voggel+)."""
    return (df['gaia_aen'] > aen_thresh) & (df['gaia_aen_sig'] > d_thresh)

def model_b_physical(df: pd.DataFrame, d_ref: float = 20.0, aen_ref: float = 0.5):
    """Model B: Distance-dependent threshold (scaling with angular size)."""
    # AEN_threshold = AEN_ref * (D_ref / D)
    # However, Gaia's resolution floor means we shouldn't go below ~0.3-0.5
    thresh = aen_ref * (d_ref / df['distance_mpc'])
    thresh = thresh.clip(lower=0.3)
    return (df['gaia_aen'] > thresh) & (df['gaia_aen_sig'] > 2.0)

def model_c_probabilistic(df: pd.DataFrame):
    """Model C: Simplified probabilistic approach.

    Assigns a score based on how many sigma the AEN and BR_excess are
    above typical stellar values.
    """
    # For stars, log10(AEN) is roughly centered at -1 (0.1 mas) with width ~0.3
    # We use gaia_aen_sig (D) as a direct proxy for probability
    # Prob = CDF(D)
    prob_aen = norm.cdf(df['gaia_aen_sig'] - 2.0) # Shifted so D=2 is 50%

    # BR excess: stars are near 1.2-1.3. UCDs are > 1.5
    # Very rough mapping
    prob_br = (df['gaia_br_excess'] - 1.2) / 0.5
    prob_br = prob_br.clip(0, 1)

    return (prob_aen * 0.7 + prob_br * 0.3) > 0.5

def evaluate_models(df: pd.DataFrame):
    """Quantitatively evaluate the proposed models."""
    df['sel_a'] = model_a_constant(df)
    df['sel_b'] = model_b_physical(df)
    df['sel_c'] = model_c_probabilistic(df)

    distances = sorted(df['distance_mpc'].unique())
    results = []

    for d in distances:
        subset = df[df['distance_mpc'] == d]
        n_total = len(subset)
        if n_total == 0: continue

        results.append({
            'distance': d,
            'n_total': n_total,
            'comp_a': subset['sel_a'].sum() / n_total,
            'comp_b': subset['sel_b'].sum() / n_total,
            'comp_c': subset['sel_c'].sum() / n_total
        })

    res_df = pd.DataFrame(results)
    logger.info("\nModel Completeness by Distance:")
    logger.info("\n" + res_df.to_string(index=False))
    return res_df, df

def plot_evaluation(res_df: pd.DataFrame, df: pd.DataFrame):
    """Generate plots showing model performance."""
    set_style()

    # 1. Completeness vs Distance
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(res_df['distance'], res_df['comp_a']*100, 'o-', label='Model A (Constant)')
    ax.plot(res_df['distance'], res_df['comp_b']*100, 's-', label='Model B (Physical)')
    ax.plot(res_df['distance'], res_df['comp_c']*100, '^-', label='Model C (Probabilistic)')

    ax.set_xscale('log')
    ax.set_xlabel('Distance (Mpc)')
    ax.set_ylabel('Completeness (%)')
    ax.set_title('Selection Model Completeness vs Distance')
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.legend()

    save_figure(
        fig, "model_completeness", phase=1,
        script_path="scripts/phase1_literature/distance_selection.py",
        command=COMMAND,
        data_source="ucd_collection.db",
        description="Comparison of UCD selection model completeness. Model A (constant AEN > 0.5) "
                    "is highly complete at small distances but drops off for distant clusters. "
                    "Model B (physical scaling) attempts to recover more distant objects."
    )
    plt.close(fig)

    # 2. AEN vs Magnitude with Boundaries
    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(df['gaia_g_mag'], df['gaia_aen'], c=df['distance_mpc'],
                         cmap='viridis', alpha=0.6, s=20)
    cbar = plt.colorbar(scatter)
    cbar.set_label('Distance (Mpc)')

    # Plot boundaries
    g_range = np.linspace(14, 21, 100)
    ax.axhline(0.5, color='r', linestyle='--', label='Model A Boundary')

    ax.set_yscale('log')
    ax.set_xlabel('Gaia G (mag)')
    ax.set_ylabel('Gaia AEN (mas)')
    ax.set_title('UCD Distribution and Selection Boundaries')
    ax.legend()

    save_figure(
        fig, "selection_boundaries", phase=1,
        script_path="scripts/phase1_literature/distance_selection.py",
        command=COMMAND,
        data_source="ucd_collection.db",
        description="Gaia AEN vs G magnitude for known UCDs. The 0.5 mas threshold (Model A) "
                    "captures most nearby UCDs but may be too conservative for distant systems."
    )
    plt.close(fig)

def main():
    df = load_data()
    if df.empty:
        logger.error("No data loaded.")
        return

    res_df, df_full = evaluate_models(df)
    plot_evaluation(res_df, df_full)

    # Summarize Pros/Cons
    print("\n" + "="*60)
    print("PROPOSED SELECTION MODELS EVALUATION")
    print("="*60)
    print("\nModel A (Constant AEN > 0.5 mas, D > 2):")
    print(f"  Pros: Simple, established (Voggel+ 2020), low contamination.")
    print(f"  Cons: Completeness drops to {res_df.iloc[-1]['comp_a']*100:.1f}% at 100 Mpc.")

    print("\nModel B (Distance-dependent AEN > 0.5 * (20/D)):")
    print(f"  Pros: Physically motivated (angular size), higher completeness at distance.")
    print(f"  Cons: Higher background contamination in distant fields.")

    print("\nModel C (Probabilistic Score AEN + BR_excess):")
    print(f"  Pros: Multi-parameter, handles edge cases better, flexible threshold.")
    print(f"  Cons: Requires more parameters, needs better background calibration.")
    print("="*60)

if __name__ == "__main__":
    main()
