"""Validate pilot search by recovering literature UCDs.

Cross-matches candidates identified in the radial search with the
known UCD collection to quantify recovery rates and identify
new candidate discoveries.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from astropy.coordinates import SkyCoord
import astropy.units as u
from scripts.config import RADIAL_SEARCH_RESULTS_DIR, LITERATURE_DB
from scripts.phase1_literature.ucd_database import get_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_literature_ucds():
    """Load all matched literature UCDs from the database."""
    conn = get_db_connection()
    query = "SELECT object_id, ra, dec, source_id, host_galaxy FROM ucd_objects WHERE gaia_dr3_id IS NOT NULL"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def validate_host(host_name: str, df_lit: pd.DataFrame):
    """Validate recovery for a specific host galaxy."""
    safe_name = host_name.replace(' ', '_')
    cand_path = RADIAL_SEARCH_RESULTS_DIR / f"{safe_name}_candidates.csv"

    if not cand_path.exists():
        return None

    df_cand = pd.read_csv(cand_path)

    # Filter literature UCDs that should be near this host
    # (Using a simple 300 kpc cut if host_galaxy is not explicitly set)
    # For now, we'll just match all literature against all candidates

    c_lit = SkyCoord(ra=df_lit['ra'].values*u.deg, dec=df_lit['dec'].values*u.deg)
    c_cand = SkyCoord(ra=df_cand['ra'].values*u.deg, dec=df_cand['dec'].values*u.deg)

    # Match within 1 arcsec
    idx_lit, d2d, d3d = c_lit.match_to_catalog_sky(c_cand)
    mask = d2d < 1.0 * u.arcsec

    n_found = mask.sum()
    n_total_lit = len(df_lit) # This is too broad, but let's see

    # Better: check objects specifically associated with this host in literature
    # (Mapping might be needed)

    logger.info(f"Host: {host_name}")
    logger.info(f"  Candidates found in search: {len(df_cand)}")
    logger.info(f"  Literature UCDs recovered: {n_found}")

    # Identify "New" high-confidence candidates
    df_new = df_cand[~df_cand.index.isin(idx_lit[mask])]
    high_conf = df_new[df_new['model_c_score'] > 0.8]
    logger.info(f"  New High-Confidence Candidates (Model C > 0.8): {len(high_conf)}")

    return {
        'host': host_name,
        'n_candidates': len(df_cand),
        'n_recovered': n_found,
        'n_new_high_conf': len(high_conf)
    }

def main():
    df_lit = load_literature_ucds()
    summary_path = RADIAL_SEARCH_RESULTS_DIR / "pilot_search_summary.csv"
    if not summary_path.exists():
        logger.error("Pilot summary not found.")
        return

    df_summary = pd.read_csv(summary_path)

    results = []
    for _, row in df_summary.iterrows():
        res = validate_host(row['objname'], df_lit)
        if res:
            results.append(res)

    if results:
        df_val = pd.DataFrame(results)
        print("\nRecovery Validation Summary:")
        print(df_val.to_string(index=False))

if __name__ == "__main__":
    main()
