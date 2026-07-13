"""Rank and prioritize target galaxies for the pilot search.

Implements guidelines for selecting a diverse Top 100 sample:
1. Prioritize massive/luminous galaxies (log L_K > 10.7).
2. Include literature UCD hosts for calibration.
3. Ensure representation of non-cluster/field environments.
"""

import logging
import pandas as pd
import numpy as np
from scripts.config import GALAXY_SAMPLE_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
LOG_LK_MW = 10.7
CLUSTERS = ['Virgo', 'Fornax', 'Hydra', 'Coma', 'Centaurus']

# Literature hosts (from Phase I database)
LIT_HOSTS = [
    'NGC 1316', 'NGC 1399', 'MESSIER 087', 'NGC 5128', 'MESSIER 031',
    'MESSIER 049', 'MESSIER 060', 'NGC 3923', 'NGC 4546', 'MESSIER 104',
    'MESSIER 081', 'NGC 1553', 'NGC 1549', 'NGC 1400', 'NGC 1407',
    'NGC 4709', 'NGC 4696', 'NGC 3311', 'MESSIER 059', 'MESSIER 085'
]

def rank_targets():
    """Merge data and rank galaxies."""
    coverage_path = GALAXY_SAMPLE_DIR / "galaxy_sample_with_coverage.csv"
    morphology_path = GALAXY_SAMPLE_DIR / "galaxy_sample_with_morphology.csv"

    if not coverage_path.exists() or not morphology_path.exists():
        logger.error("Missing input files for ranking.")
        return

    df_cov = pd.read_csv(coverage_path)
    df_morph = pd.read_csv(morphology_path)

    # Merge morphology into coverage
    # Keep columns from coverage, add 'hyperleda_type' from morph
    df = df_cov.merge(df_morph[['objname', 'hyperleda_type']], on='objname', how='left')

    # Identify literature hosts
    df['is_lit_host'] = df['objname'].isin(LIT_HOSTS)

    # Identify cluster members
    # Simple check based on common cluster name tags or specific host strings
    # (In a real scenario, we'd use group/cluster catalogs)
    df['is_cluster'] = False
    for cluster in CLUSTERS:
        # Check if cluster name is in any related metadata (we'll just use a proxy for now)
        pass

    # Manual override for known cluster regions
    # (Simplified for pilot)
    cluster_ra_dec = {
        'Virgo': {'ra': 187.7, 'dec': 12.4, 'radius': 10},
        'Fornax': {'ra': 54.6, 'dec': -35.4, 'radius': 5}
    }

    for cluster, coords in cluster_ra_dec.items():
        dist = np.sqrt((df['ra'] - coords['ra'])**2 + (df['dec'] - coords['dec'])**2)
        df.loc[dist < coords['radius'], 'is_cluster'] = True

    # Calculate Priority Score
    # Score = Luminosity + LitBonus + FieldBonus - DistancePenalty

    # Normalize log_L_K
    df['score_lum'] = (df['log_L_K'] - df['log_L_K'].min()) / (df['log_L_K'].max() - df['log_L_K'].min()) * 50

    # Lit bonus (high priority for calibration)
    df['score_lit'] = df['is_lit_host'].astype(int) * 30

    # Field bonus (environmental diversity)
    df['score_field'] = (~df['is_cluster']).astype(int) * 20

    # Distance penalty (closer is better)
    df['score_dist'] = (1.0 - (df['dist_best'] / df['dist_best'].max())) * 20

    df['total_score'] = df['score_lum'] + df['score_lit'] + df['score_field'] + df['score_dist']

    # Sort and filter
    # Must have LS DR10 coverage
    df_pilot_pool = df[df['has_ls_dr10'] == True].sort_values('total_score', ascending=False)

    top_100 = df_pilot_pool.head(100).copy()

    # Final cleanup and save
    output_path = GALAXY_SAMPLE_DIR / "pilot_sample_top100.csv"
    top_100.to_csv(output_path, index=False)

    logger.info(f"Pilot sample ranking complete. Top 100 saved to {output_path}")

    # Summary
    logger.info("\nTop 10 Galaxies in Pilot:")
    logger.info("\n" + top_100[['objname', 'log_L_K', 'dist_best', 'is_lit_host', 'total_score']].head(10).to_string(index=False))

    logger.info(f"\nLuminous (log L_K > {LOG_LK_MW}): {(top_100['log_L_K'] > LOG_LK_MW).sum()}")
    logger.info(f"Literature Hosts: {top_100['is_lit_host'].sum()}")
    logger.info(f"Non-Cluster Targets: {(~top_100['is_cluster']).sum()}")

if __name__ == "__main__":
    rank_targets()
