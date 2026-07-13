"""Execute background density queries on Gaia DR3 using astroquery.

Implements a robust pipeline for querying Gaia. Applies Model C selection
locally on results. Handles concurrency and retries.
"""

import logging
import time
import pandas as pd
import numpy as np
import argparse
from scipy.stats import norm
from astroquery.gaia import Gaia
from concurrent.futures import ThreadPoolExecutor, as_completed
from scripts.config import BACKGROUND_RESULTS_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_CONCURRENT = 3 # Slightly more conservative
MAX_RETRIES = 3
SEARCH_RADIUS_DEG = 0.8 # ~2 sq deg area

def apply_model_c(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the preliminary Model C selection criteria locally."""
    if df.empty:
        return df

    # AEN Score (D=2 is 50%)
    prob_aen = norm.cdf(df['astrometric_excess_noise_sig'] - 2.0)

    # BR Excess Score (1.2-1.7 range)
    prob_br = (df['phot_bp_rp_excess_factor'] - 1.2) / 0.5
    prob_br = np.clip(prob_br, 0, 1)

    df['model_c_score'] = (prob_aen * 0.7 + prob_br * 0.3)
    return df[df['model_c_score'] > 0.5].copy()

def query_field(ra, dec, field_id):
    """Query a single field using astroquery."""
    adql = f"""
    SELECT
        source_id, ra, dec, phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag,
        astrometric_excess_noise, astrometric_excess_noise_sig,
        phot_bp_rp_excess_factor, classprob_dsc_combmod_galaxy
    FROM gaiadr3.gaia_source
    WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {SEARCH_RADIUS_DEG}))
      AND phot_g_mean_mag BETWEEN 16 AND 21
      AND astrometric_excess_noise > 0.3
      AND astrometric_excess_noise_sig > 1.0
    """

    for attempt in range(MAX_RETRIES):
        try:
            job = Gaia.launch_job_async(adql)
            table = job.get_results()
            df = table.to_pandas()

            # Apply Model C
            df_ucd = apply_model_c(df)

            return {
                'field_id': field_id,
                'ra': ra,
                'dec': dec,
                'n_total_candidates': len(df),
                'n_model_c': len(df_ucd),
                'density': len(df_ucd) / 2.0,
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed for field {field_id}: {e}")
            time.sleep(5 * (attempt + 1))

    return {'field_id': field_id, 'status': 'failed'}

import os

def main():
    parser = argparse.ArgumentParser(description="Run background Gaia queries.")
    parser.add_argument("--n", type=int, default=500, help="Number of fields to process")
    args = parser.parse_args()

    # Gaia Login (optional, from env vars)
    gaia_user = os.environ.get("GAIA_USER")
    gaia_pwd = os.environ.get("GAIA_PASSWORD")
    if gaia_user and gaia_pwd:
        logger.info(f"Logging in to Gaia as {gaia_user}...")
        Gaia.login(user=gaia_user, password=gaia_pwd)
    else:
        logger.warning("Running as anonymous user. For better performance, set GAIA_USER and GAIA_PASSWORD.")

    coords_path = BACKGROUND_RESULTS_DIR / "background_fields_500.csv"
    if not coords_path.exists():
        logger.error(f"Coordinates file not found: {coords_path}")
        return

    df_coords = pd.read_csv(coords_path).head(args.n)

    results = []
    logger.info(f"Starting background queries for {len(df_coords)} fields...")

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        futures = {executor.submit(query_field, row['ra'], row['dec'], i): i
                   for i, row in df_coords.iterrows()}

        for i, future in enumerate(as_completed(futures)):
            res = future.result()
            results.append(res)

            if (i + 1) % 5 == 0:
                logger.info(f"Progress: {i+1}/{len(df_coords)} completed.")

    # Save results
    df_res = pd.DataFrame(results)
    # Merge back original galactic coordinates
    df_final = df_res.merge(df_coords[['glon', 'glat']], left_on='field_id', right_index=True)

    output_path = BACKGROUND_RESULTS_DIR / f"background_density_results_{args.n}.csv"
    df_final.to_csv(output_path, index=False)
    logger.info(f"Background characterization complete. Results saved to {output_path}")

if __name__ == "__main__":
    main()
