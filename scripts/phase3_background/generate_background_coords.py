"""Generate random background coordinates for Phase III.

Generates a uniform distribution of coordinates across the sky, filtered
to restrict results to galactic latitudes |b| > 20 deg. Designed to be
scalable for larger sample sizes.
"""

import logging
import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from scripts.config import BACKGROUND_RESULTS_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_random_coords(n_fields: int, b_min: float = 20.0):
    """Generate N random coordinates with |b| > b_min.

    Uses uniform distribution on a sphere.
    """
    logger.info(f"Generating {n_fields} random coordinates with |b| > {b_min} deg...")

    # We generate more than needed to account for the latitude filter
    # Area of |b| < b_min is sin(b_min) * total_area
    # So we need roughly n_fields / (1 - sin(b_min))
    n_oversample = int(n_fields / (1 - np.sin(np.deg2rad(b_min))) * 1.5)

    # Random RA (0 to 360)
    ra = np.random.uniform(0, 360, n_oversample)

    # Random Dec (uniform in sin(dec) from -1 to 1)
    sin_dec = np.random.uniform(-1, 1, n_oversample)
    dec = np.rad2deg(np.arcsin(sin_dec))

    # Convert to Galactic to filter
    coords = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
    b = coords.galactic.b.deg

    mask = np.abs(b) > b_min

    df = pd.DataFrame({
        'ra': ra[mask],
        'dec': dec[mask],
        'glon': coords.galactic.l.deg[mask],
        'glat': b[mask]
    })

    # Take only the requested number
    if len(df) < n_fields:
        logger.warning(f"Only generated {len(df)} coordinates. Try a larger oversample.")
        return df

    return df.head(n_fields).reset_index(drop=True)

def main(n_fields: int = 500):
    """Main execution."""
    df = generate_random_coords(n_fields)

    # Ensure results directory exists
    BACKGROUND_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = BACKGROUND_RESULTS_DIR / f"background_fields_{n_fields}.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"Successfully saved {len(df)} background fields to {output_path}")

if __name__ == "__main__":
    main()
