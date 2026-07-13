"""Check survey coverage for target galaxies.

Uses NOIRLab Data Lab TAP service to check if target galaxies fall within
the Legacy Survey DR10 footprint.
"""

import logging
import time
import pandas as pd
from pyvo.dal import tap
from scripts.config import GALAXY_SAMPLE_CSV, GALAXY_SAMPLE_DIR, DATA_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NOIRLab Data Lab TAP service
DATALAB_TAP_URL = "https://datalab.noirlab.edu/tap"

def check_ls_dr10_coverage(ra, dec, service, radius_deg=0.1):
    """Check if any LS DR10 objects exist within a radius of the coordinates."""
    # Box search for existence in tractor table
    adql = f"""
    SELECT TOP 1 ls_id
    FROM ls_dr10.tractor
    WHERE ra BETWEEN {ra - radius_deg} AND {ra + radius_deg}
      AND dec BETWEEN {dec - radius_deg} AND {dec + radius_deg}
    """
    try:
        job = service.run_sync(adql)
        return len(job.to_table()) > 0
    except Exception as e:
        logger.error(f"Error checking coverage at ({ra}, {dec}): {e}")
        return False

def main(n_test=None):
    """Check coverage for sample galaxies."""
    if not GALAXY_SAMPLE_CSV.exists():
        logger.error(f"File not found: {GALAXY_SAMPLE_CSV}")
        return

    df = pd.read_csv(GALAXY_SAMPLE_CSV)
    if n_test:
        logger.info(f"Testing coverage for top {n_test} galaxies...")
        df = df.head(n_test).copy()
    else:
        logger.info(f"Checking coverage for all {len(df)} galaxies...")

    service = tap.TAPService(DATALAB_TAP_URL)

    ls_coverage = []
    start_time = time.time()

    for i, row in df.iterrows():
        if i % 10 == 0 and i > 0:
            elapsed = time.time() - start_time
            rate = i / elapsed
            eta = (len(df) - i) / rate / 60
            logger.info(f"Progress: {i}/{len(df)} ({(i/len(df))*100:.1f}%) - ETA: {eta:.1f} min")

        covered = check_ls_dr10_coverage(row['ra'], row['dec'], service)
        ls_coverage.append(covered)
        time.sleep(0.2) # Rate limit respect

    df['has_ls_dr10'] = ls_coverage

    # Save results
    output_path = GALAXY_SAMPLE_DIR / "galaxy_sample_with_coverage.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"Coverage check complete. Results saved to {output_path}")
    logger.info(f"Summary: {df['has_ls_dr10'].sum()} / {len(df)} galaxies covered by LS DR10")

if __name__ == "__main__":
    # Check top 500 for a good pool
    main(n_test=500)
