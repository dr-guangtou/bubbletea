"""Fetch morphological information for target galaxies from HyperLEDA via VizieR.

Retrieves morphological types (Hubble) and T-types from the HyperLEDA
database using coordinate-based regional queries.
"""

import logging
import time
import pandas as pd
import numpy as np
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u
from scripts.config import GALAXY_SAMPLE_CSV, GALAXY_SAMPLE_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HyperLEDA on VizieR: VII/237
# Note: Using small radius for precise identification
vizier = Vizier(columns=["*"], row_limit=1)

def fetch_hyperleda_morphology(ra, dec):
    """Fetch morphology for a single object using coordinates."""
    try:
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        result = vizier.query_region(coord, radius=30*u.arcsec, catalog="VII/237")
        if result and len(result) > 0:
            logger.info(f"Match found at ({ra}, {dec})")
            table = result[0]
            # MType seems to be the Hubble type column in this version
            morph_type = str(table['MType'][0]) if 'MType' in table.colnames and table['MType'][0] else None
            t_type = None # T-Type code not directly in this simplified VizieR table
            logger.info(f"Extracted: Type={morph_type}")
            return morph_type, t_type
        else:
            logger.debug(f"No match for ({ra}, {dec})")
        return None, None
    except Exception as e:
        logger.warning(f"Error fetching HyperLEDA data at ({ra}, {dec}): {e}")
        return None, None

def main(n_limit=50):
    """Fetch morphology for the top N galaxies."""
    if not GALAXY_SAMPLE_CSV.exists():
        logger.error(f"File not found: {GALAXY_SAMPLE_CSV}")
        return

    df = pd.read_csv(GALAXY_SAMPLE_CSV)

    # Target those with unknown T-Type
    mask_to_fetch = df['ttype_lvg'].isna()
    fetch_idx = df[mask_to_fetch].head(n_limit).index

    logger.info(f"Fetching HyperLEDA morphology for {len(fetch_idx)} galaxies by coordinates...")

    start_time = time.time()
    n_success = 0

    # Initialize columns if they don't exist
    if 'hyperleda_type' not in df.columns:
        df['hyperleda_type'] = None
    if 'hyperleda_t' not in df.columns:
        df['hyperleda_t'] = np.nan

    for i, idx in enumerate(fetch_idx):
        ra, dec = df.loc[idx, 'ra'], df.loc[idx, 'dec']
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            eta = (len(fetch_idx) - (i+1)) / rate / 60
            logger.info(f"Progress: {i+1}/{len(fetch_idx)} - ETA: {eta:.1f} min")

        morph, t_type = fetch_hyperleda_morphology(ra, dec)
        if morph is not None or t_type is not None:
            df.loc[idx, 'hyperleda_type'] = str(morph) if morph is not None else None
            df.loc[idx, 'hyperleda_t'] = float(t_type) if t_type is not None else np.nan
            n_success += 1
            logger.info(f"  -> {df.loc[idx, 'objname']}: Type={morph}, T={t_type}")

        # Respect rate limits
        time.sleep(0.2)

    # Save results
    output_path = GALAXY_SAMPLE_DIR / "galaxy_sample_with_morphology.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"Morphology fetch complete. Results saved to {output_path}")
    logger.info(f"Successfully retrieved morphology for {n_success} galaxies.")

if __name__ == "__main__":
    main(n_limit=500)
